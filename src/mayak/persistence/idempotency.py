"""PostgreSQL persistence for terminal idempotency outcomes."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from mayak.contracts.idempotency import IdempotencyDecision, IdempotencyDecisionOutcome
from mayak.contracts.results import CommonOutcome
from mayak.persistence.metadata import metadata
from mayak.platform.idempotency import IdempotencyFingerprint, IdempotencyKey, IdempotencyScope

__all__ = ["TerminalIdempotencyResolution", "PostgresTerminalIdempotencyRepository"]

_FINGERPRINT = re.compile(r"[0-9a-f]{64}\Z")
_MAX_RESULT_BYTES = 65_536
_TABLE = metadata.tables["mayak.platform_idempotency_records"]


@dataclass(frozen=True, slots=True)
class TerminalIdempotencyResolution:
    decision: IdempotencyDecisionOutcome
    outcome: CommonOutcome | None

    def __post_init__(self) -> None:
        if self.decision.decision is IdempotencyDecision.REPLAY_TERMINAL:
            if not isinstance(self.outcome, CommonOutcome):
                raise ValueError("terminal replay requires a validated outcome")
        elif self.decision.decision not in (
            IdempotencyDecision.NEW,
            IdempotencyDecision.MISMATCH,
            IdempotencyDecision.RECONCILE_REQUIRED,
        ) or self.outcome is not None:
            raise ValueError("non-replay terminal resolutions cannot contain an outcome")


class PostgresTerminalIdempotencyRepository:
    """Read and atomically write terminal records in the registered table."""

    def evaluate(
        self,
        session: Session,
        *,
        scope: IdempotencyScope,
        key: IdempotencyKey,
        fingerprint: IdempotencyFingerprint,
        now: datetime,
    ) -> TerminalIdempotencyResolution:
        self._validate_lookup(scope, key, fingerprint, now)
        row = session.execute(
            select(_TABLE.c.expires_at, _TABLE.c.request_fingerprint, _TABLE.c.result).where(
                _TABLE.c.scope == scope.value,
                _TABLE.c.idempotency_key == key.value,
            )
        ).mappings().one_or_none()
        return self._resolve_row(row, fingerprint.value, now)

    def record_terminal(
        self,
        session: Session,
        *,
        record_id: UUID,
        scope: IdempotencyScope,
        key: IdempotencyKey,
        fingerprint: IdempotencyFingerprint,
        outcome: CommonOutcome,
        created_at: datetime,
        expires_at: datetime,
        now: datetime,
    ) -> TerminalIdempotencyResolution:
        self._validate_record(
            record_id, scope, key, fingerprint, outcome, created_at, expires_at, now
        )
        payload = outcome.model_dump(mode="json")
        statement: Any = insert(_TABLE).values(
            id=record_id,
            scope=scope.value,
            idempotency_key=key.value,
            request_fingerprint=fingerprint.value,
            result=payload,
            created_at=created_at,
            expires_at=expires_at,
        )
        statement = statement.on_conflict_do_update(
            constraint="uq_platform_idempotency_records_scope_key",
            set_={
                "id": statement.excluded.id,
                "scope": statement.excluded.scope,
                "idempotency_key": statement.excluded.idempotency_key,
                "request_fingerprint": statement.excluded.request_fingerprint,
                "result": statement.excluded.result,
                "created_at": statement.excluded.created_at,
                "expires_at": statement.excluded.expires_at,
            },
            where=_TABLE.c.expires_at <= now,
        ).returning(_TABLE.c.id)
        inserted = session.execute(statement).scalar_one_or_none()
        if inserted is not None:
            return self._new("IDEMPOTENCY_TERMINAL_RECORDED")
        self._validate_lookup(scope, key, fingerprint, now)
        row = session.execute(
            select(_TABLE.c.expires_at, _TABLE.c.request_fingerprint, _TABLE.c.result).where(
                _TABLE.c.scope == scope.value,
                _TABLE.c.idempotency_key == key.value,
            )
        ).mappings().one_or_none()
        if row is None:
            return self._reconcile("IDEMPOTENCY_CONFLICT_STATE_UNKNOWN")
        return self._resolve_row(row, fingerprint.value, now)

    @staticmethod
    def _validate_lookup(
        scope: IdempotencyScope,
        key: IdempotencyKey,
        fingerprint: IdempotencyFingerprint,
        now: datetime,
    ) -> None:
        if not scope.value:
            raise ValueError("scope must be non-empty")
        if not key.value or len(key.value) > 200:
            raise ValueError("idempotency key has invalid length")
        if _FINGERPRINT.fullmatch(fingerprint.value) is None:
            raise ValueError("request fingerprint has invalid format")
        PostgresTerminalIdempotencyRepository._aware(now, "now")

    @classmethod
    def _validate_record(
        cls, record_id: UUID, scope: IdempotencyScope, key: IdempotencyKey,
        fingerprint: IdempotencyFingerprint, outcome: CommonOutcome,
        created_at: datetime, expires_at: datetime, now: datetime,
    ) -> None:
        if not isinstance(record_id, UUID):
            raise ValueError("record id must be a UUID")
        cls._validate_lookup(scope, key, fingerprint, now)
        if not isinstance(outcome, CommonOutcome):
            raise ValueError("outcome must be a CommonOutcome")
        cls._aware(created_at, "created_at")
        cls._aware(expires_at, "expires_at")
        if expires_at <= created_at:
            raise ValueError("expires_at must be after created_at")
        encoded = json.dumps(
            outcome.model_dump(mode="json"), sort_keys=True, ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        if len(encoded) > _MAX_RESULT_BYTES:
            raise ValueError("serialized terminal outcome exceeds persistence limit")

    @staticmethod
    def _aware(value: datetime, name: str) -> None:
        if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{name} must be timezone-aware")

    @classmethod
    def _resolve_row(
        cls, row: Any, fingerprint: str, now: datetime
    ) -> TerminalIdempotencyResolution:
        if row is None:
            return cls._new("IDEMPOTENCY_KEY_AVAILABLE")
        if row["expires_at"] <= now:
            return cls._new("IDEMPOTENCY_RECORD_EXPIRED")
        if row["request_fingerprint"] != fingerprint:
            return cls._mismatch("IDEMPOTENCY_FINGERPRINT_MISMATCH")
        try:
            outcome = CommonOutcome.model_validate(row["result"])
        except Exception:
            return cls._reconcile("IDEMPOTENCY_STORED_RESULT_INVALID")
        return TerminalIdempotencyResolution(
            IdempotencyDecisionOutcome.replay_terminal(reason_code="IDEMPOTENCY_REPLAY_TERMINAL"),
            outcome,
        )

    @staticmethod
    def _new(reason: str) -> TerminalIdempotencyResolution:
        return TerminalIdempotencyResolution(
            IdempotencyDecisionOutcome.new(reason_code=reason), None
        )

    @staticmethod
    def _mismatch(reason: str) -> TerminalIdempotencyResolution:
        return TerminalIdempotencyResolution(
            IdempotencyDecisionOutcome.mismatch(reason_code=reason), None
        )

    @staticmethod
    def _reconcile(reason: str) -> TerminalIdempotencyResolution:
        return TerminalIdempotencyResolution(
            IdempotencyDecisionOutcome.reconcile_required(reason_code=reason), None
        )
