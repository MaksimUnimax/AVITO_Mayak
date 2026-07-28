"""Append-only PostgreSQL persistence for safe audit entries."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import insert, select
from sqlalchemy.orm import Session

from mayak.contracts.audit import AuditContext
from mayak.contracts.serialization import ContractSerializationError, canonical_contract_bytes
from mayak.persistence.metadata import metadata

__all__ = ["AuditPersistenceError", "PersistedAuditEntry", "PostgresAuditRepository"]

_MAX_CONTEXT_BYTES = 65_536
_TABLE = metadata.tables["mayak.platform_audit_entries"]


class AuditPersistenceError(ValueError):
    """Safe validation or stored-row error for the audit repository."""


@dataclass(frozen=True, slots=True)
class PersistedAuditEntry:
    entry_id: UUID
    actor_account_id: UUID | None
    context: AuditContext
    target_id: str | None
    created_at: datetime


class PostgresAuditRepository:
    """Append and retrieve audit rows without owning the caller's session."""

    def append(
        self,
        session: Session,
        *,
        entry_id: UUID,
        actor_account_id: UUID | None,
        context: AuditContext,
        target_id: str | None,
        created_at: datetime,
    ) -> PersistedAuditEntry:
        self._validate_append(session, entry_id, actor_account_id, context, target_id, created_at)
        normalized_target_id = target_id.strip() if target_id is not None else None
        details = context.model_dump(mode="json")
        statement = (
            insert(_TABLE)
            .values(
                id=entry_id,
                actor_account_id=actor_account_id,
                action_code=context.operation.value,
                target_type=context.target_scope.value,
                target_id=normalized_target_id,
                reason=context.reason.value,
                correlation_id=context.correlation.correlation_id.value,  # type: ignore[union-attr]
                details=details,
                created_at=created_at,
            )
            .returning(*_TABLE.c)
        )
        row = session.execute(statement).mappings().one()
        return self._decode_row(row)

    def get(self, session: Session, *, entry_id: UUID) -> PersistedAuditEntry | None:
        self._validate_session(session)
        if not isinstance(entry_id, UUID):
            raise AuditPersistenceError("entry id must be a UUID")
        row = (
            session.execute(select(_TABLE).where(_TABLE.c.id == entry_id)).mappings().one_or_none()
        )
        if row is None:
            return None
        return self._decode_row(row)

    @classmethod
    def _validate_append(
        cls,
        session: Session,
        entry_id: UUID,
        actor_account_id: UUID | None,
        context: AuditContext,
        target_id: str | None,
        created_at: datetime,
    ) -> None:
        cls._validate_session(session)
        if not isinstance(entry_id, UUID):
            raise AuditPersistenceError("entry id must be a UUID")
        if actor_account_id is not None and not isinstance(actor_account_id, UUID):
            raise AuditPersistenceError("actor account id must be a UUID or None")
        if not isinstance(context, AuditContext):
            raise AuditPersistenceError("audit context must be an AuditContext")
        if context.correlation is None:
            raise AuditPersistenceError("audit context requires correlation")
        if len(context.operation.value) > 64:
            raise AuditPersistenceError("audit operation exceeds persistence limit")
        if len(context.target_scope.value) > 128:
            raise AuditPersistenceError("audit target scope exceeds persistence limit")
        if target_id is not None and (not isinstance(target_id, str) or not target_id.strip()):
            raise AuditPersistenceError("target id must be non-empty when provided")
        if (
            not isinstance(created_at, datetime)
            or created_at.tzinfo is None
            or created_at.utcoffset() is None
        ):
            raise AuditPersistenceError("created_at must be timezone-aware")
        try:
            encoded = canonical_contract_bytes(context)
        except ContractSerializationError:
            raise AuditPersistenceError(
                "serialized audit context exceeds persistence limit"
            ) from None
        if len(encoded) > _MAX_CONTEXT_BYTES:
            raise AuditPersistenceError("serialized audit context exceeds persistence limit")

    @staticmethod
    def _validate_session(session: Session) -> None:
        if not isinstance(session, Session):
            raise AuditPersistenceError("session must be a SQLAlchemy Session")

    @staticmethod
    def _decode_row(row: Any) -> PersistedAuditEntry:
        try:
            entry_id = row["id"]
            actor_account_id = row["actor_account_id"]
            action_code = row["action_code"]
            target_type = row["target_type"]
            target_id = row["target_id"]
            reason = row["reason"]
            correlation_id = row["correlation_id"]
            details = row["details"]
            created_at = row["created_at"]
            if not isinstance(entry_id, UUID):
                raise ValueError
            if actor_account_id is not None and not isinstance(actor_account_id, UUID):
                raise ValueError
            if target_id is not None and (not isinstance(target_id, str) or not target_id.strip()):
                raise ValueError
            if (
                not isinstance(created_at, datetime)
                or created_at.tzinfo is None
                or created_at.utcoffset() is None
            ):
                raise ValueError
            context = AuditContext.model_validate(details)
            if context.correlation is None:
                raise ValueError
            if action_code != context.operation.value:
                raise ValueError
            if target_type != context.target_scope.value:
                raise ValueError
            if reason != context.reason.value:
                raise ValueError
            if correlation_id != context.correlation.correlation_id.value:
                raise ValueError
            if len(canonical_contract_bytes(context)) > _MAX_CONTEXT_BYTES:
                raise ValueError
            return PersistedAuditEntry(entry_id, actor_account_id, context, target_id, created_at)
        except Exception:
            raise AuditPersistenceError("stored audit entry is invalid") from None
