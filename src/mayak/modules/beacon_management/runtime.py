"""Authoritative, caller-transaction-owned Beacon Management runtime."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select, text, update
from sqlalchemy.orm import Session

from mayak.contracts.audit import AuditContext
from mayak.contracts.results import CommonOutcome, Result
from mayak.persistence.audit import PostgresAuditRepository
from mayak.persistence.idempotency import PostgresTerminalIdempotencyRepository
from mayak.persistence.metadata import metadata
from mayak.platform.audit import (
    AuditActorCategory,
    AuditModuleIdentifier,
    AuditOperation,
    AuditReason,
    AuditTargetScope,
)
from mayak.platform.correlation import CorrelationContext, CorrelationId
from mayak.platform.idempotency import IdempotencyFingerprint, IdempotencyKey, IdempotencyScope

from .contracts import BeaconLifecycleState

_BEACONS = metadata.tables["mayak.beacon_beacons"]
_REVISIONS = metadata.tables["mayak.beacon_configuration_revisions"]
_OVERRIDES = metadata.tables["mayak.beacon_filter_overrides"]
_EVENTS = metadata.tables["mayak.beacon_lifecycle_events"]
_SCOPE = IdempotencyScope(value="beacon_management")
_ACTIVE = {BeaconLifecycleState.ACTIVE.value}


class BeaconRuntimeError(RuntimeError):
    """Safe, bounded command failure."""


class ConflictError(BeaconRuntimeError):
    """Optimistic or idempotency conflict."""


class AuthorityPort(Protocol):
    def resolve(
        self, session: Session, *, actor_reference: str, requested_account_id: UUID | None
    ) -> "ResolvedActor": ...


class EntitlementPort(Protocol):
    def decide(
        self, session: Session, *, account_id: UUID, action: str, active_count: int
    ) -> "EntitlementDecision": ...


@dataclass(frozen=True, slots=True)
class ResolvedActor:
    """Server-established authority; never a caller-supplied authorization flag."""

    actor_id: UUID
    account_id: UUID
    verified: bool
    reference: str


@dataclass(frozen=True, slots=True)
class EntitlementDecision:
    allowed: bool
    fresh: bool = True
    expired: bool = False
    reference: str = ""


class BeaconCommandResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    result: Result
    reason_code: str = Field(min_length=1)
    beacon_id: UUID | None = None
    account_id: UUID | None = None
    state: str | None = None
    revision_no: int | None = None
    row_version: int | None = None
    source_url: str | None = None

    def terminal_outcome(self) -> CommonOutcome:
        payload = self.model_dump(mode="json")
        return CommonOutcome(
            result=self.result,
            reason_code=self.reason_code,
            details=(json.dumps(payload, sort_keys=True, separators=(",", ":")),),
        )

    @classmethod
    def from_terminal(cls, outcome: CommonOutcome) -> "BeaconCommandResult":
        if not outcome.details:
            return cls(result=outcome.result, reason_code=outcome.reason_code)
        try:
            payload = json.loads(outcome.details[0])
            return cls.model_validate(payload)
        except TypeError, ValueError, json.JSONDecodeError:
            return cls(result=outcome.result, reason_code=outcome.reason_code)


class BeaconView(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    beacon_id: UUID
    account_id: UUID
    name: str
    source_url: str | None
    state: str
    current_revision_no: int | None
    current_revision_id: UUID | None
    row_version: int


class BeaconManagementRuntime:
    """Module-04 commands and queries over Module-04-owned tables.

    The caller owns the SQLAlchemy transaction.  This class never commits or
    rolls back and never imports another domain runtime.
    """

    def __init__(
        self,
        authority: AuthorityPort,
        entitlement: EntitlementPort,
        *,
        idempotency: PostgresTerminalIdempotencyRepository | None = None,
        audit: PostgresAuditRepository | None = None,
    ) -> None:
        self.authority = authority
        self.entitlement = entitlement
        self.idempotency = idempotency or PostgresTerminalIdempotencyRepository()
        self.audit = audit or PostgresAuditRepository()

    @staticmethod
    def _now() -> datetime:
        return datetime.now(UTC)

    @staticmethod
    def _fingerprint(command: str, values: dict[str, Any]) -> IdempotencyFingerprint:
        encoded = json.dumps(
            {"command": command, "values": values},
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )
        return IdempotencyFingerprint(value=hashlib.sha256(encoded.encode()).hexdigest())

    @staticmethod
    def _key(value: str) -> IdempotencyKey:
        if not isinstance(value, str) or not value.strip():
            raise BeaconRuntimeError("missing idempotency key")
        return IdempotencyKey(value=value.strip())

    @staticmethod
    def _lock(session: Session, account_id: UUID) -> None:
        digest = hashlib.sha256(f"beacon-active:{account_id}".encode()).digest()
        session.execute(
            text("SELECT pg_advisory_xact_lock(:key)"),
            {"key": int.from_bytes(digest[:8], "big", signed=True)},
        )

    @staticmethod
    def _lock_idempotency(session: Session, key: str) -> None:
        digest = hashlib.sha256(f"beacon-idempotency:{key}".encode()).digest()
        session.execute(
            text("SELECT pg_advisory_xact_lock(:key)"),
            {"key": int.from_bytes(digest[:8], "big", signed=True)},
        )

    def _authority(
        self, session: Session, actor_reference: str, requested_account_id: UUID | None
    ) -> ResolvedActor:
        actor = self.authority.resolve(
            session, actor_reference=actor_reference, requested_account_id=requested_account_id
        )
        if not isinstance(actor, ResolvedActor) or not actor.verified:
            raise BeaconRuntimeError("verified authority required")
        return actor

    def _begin(
        self, session: Session, key: str, fingerprint: IdempotencyFingerprint
    ) -> BeaconCommandResult | None:
        self._lock_idempotency(session, key)
        resolution = self.idempotency.evaluate(
            session, scope=_SCOPE, key=self._key(key), fingerprint=fingerprint, now=self._now()
        )
        name = resolution.decision.decision.value
        if name == "REPLAY_TERMINAL":
            return BeaconCommandResult.from_terminal(resolution.outcome)  # type: ignore[arg-type]
        if name == "MISMATCH":
            raise ConflictError("idempotency fingerprint mismatch")
        if name == "RECONCILE_REQUIRED":
            raise ConflictError("idempotency reconciliation required")
        return None

    def _finish(
        self,
        session: Session,
        key: str,
        fingerprint: IdempotencyFingerprint,
        result: BeaconCommandResult,
    ) -> BeaconCommandResult:
        now = self._now()
        resolution = self.idempotency.record_terminal(
            session,
            record_id=uuid4(),
            scope=_SCOPE,
            key=self._key(key),
            fingerprint=fingerprint,
            outcome=result.terminal_outcome(),
            created_at=now,
            expires_at=now + timedelta(days=14),
            now=now,
        )
        if resolution.outcome is not None:
            return BeaconCommandResult.from_terminal(resolution.outcome)
        if resolution.decision.decision.value != "NEW":
            raise ConflictError("idempotency terminal state is not writable")
        return result

    def _audit(
        self, session: Session, actor: ResolvedActor, action: str, beacon_id: UUID, reason: str
    ) -> None:
        correlation = CorrelationContext(correlation_id=CorrelationId(value=str(uuid4())))
        context = AuditContext(
            actor_category=AuditActorCategory.OPERATOR,
            operation=AuditOperation(value=action),
            module_id=AuditModuleIdentifier(value="04-beacon-management"),
            target_scope=AuditTargetScope(value="beacon"),
            reason=AuditReason(value=reason[:200]),
            details=("actor_reference=" + actor.reference[:128],),
            correlation=correlation,
        )
        self.audit.append(
            session,
            entry_id=uuid4(),
            actor_account_id=actor.account_id,
            context=context,
            target_id=str(beacon_id),
            created_at=self._now(),
        )

    @staticmethod
    def _view(row: Any) -> BeaconView:
        return BeaconView(
            beacon_id=row["id"],
            account_id=row["account_id"],
            name=row["name"],
            source_url=row["source_url"],
            state=row["state"],
            current_revision_no=row["current_revision_no"],
            current_revision_id=row["current_revision_id"],
            row_version=row["row_version"],
        )

    def create_preparation(
        self,
        session: Session,
        *,
        actor_reference: str,
        account_id: UUID,
        source_url: str,
        name: str,
        idempotency_key: str,
    ) -> BeaconCommandResult:
        if not source_url.strip() or len(source_url) > 4096:
            raise BeaconRuntimeError("source URL is invalid")
        actor = self._authority(session, actor_reference, account_id)
        fp = self._fingerprint(
            "create_preparation", {"account": account_id, "url": source_url, "name": name}
        )
        replay = self._begin(session, idempotency_key, fp)
        if replay:
            return replay
        beacon_id = uuid4()
        now = self._now()
        session.execute(
            _BEACONS.insert().values(
                id=beacon_id,
                account_id=actor.account_id,
                name=name.strip(),
                source_url=source_url,
                current_revision_no=None,
                current_revision_id=None,
                state=BeaconLifecycleState.DRAFT.value,
                created_at=now,
                updated_at=now,
                row_version=1,
            )
        )
        session.execute(
            _EVENTS.insert().values(
                id=uuid4(),
                beacon_id=beacon_id,
                from_state=None,
                to_state=BeaconLifecycleState.DRAFT.value,
                actor_account_id=actor.account_id,
                reason="PREPARATION_CREATED",
                created_at=now,
            )
        )
        self._audit(session, actor, "BEACON_PREPARATION_CREATED", beacon_id, "PREPARATION_CREATED")
        return self._finish(
            session,
            idempotency_key,
            fp,
            BeaconCommandResult(
                result=Result.SUCCEEDED,
                reason_code="PREPARED",
                beacon_id=beacon_id,
                account_id=actor.account_id,
                state=BeaconLifecycleState.DRAFT.value,
                row_version=1,
                source_url=source_url,
            ),
        )

    def accept_snapshot(
        self,
        session: Session,
        *,
        actor_reference: str,
        beacon_id: UUID,
        snapshot: dict[str, Any],
        idempotency_key: str,
        expected_row_version: int | None = None,
    ) -> BeaconCommandResult:
        actor = self._authority(session, actor_reference, None)
        row = (
            session.execute(select(_BEACONS).where(_BEACONS.c.id == beacon_id))
            .mappings()
            .one_or_none()
        )
        if row is None or row["account_id"] != actor.account_id:
            raise BeaconRuntimeError("beacon unavailable")
        self._validate_snapshot(snapshot)
        if expected_row_version is not None and row["row_version"] != expected_row_version:
            raise ConflictError("stale beacon row version")
        fp = self._fingerprint(
            "accept_snapshot",
            {"beacon": beacon_id, "snapshot": snapshot, "expected": expected_row_version},
        )
        replay = self._begin(session, idempotency_key, fp)
        if replay:
            return replay
        revision_no = (row["current_revision_no"] or 0) + 1
        now = self._now()
        session.execute(
            _REVISIONS.insert().values(
                beacon_id=beacon_id,
                revision_no=revision_no,
                source_url=row["source_url"],
                filter_candidate=snapshot.get("candidate"),
                accepted_filter=snapshot["accepted_filter"],
                created_by_account_id=actor.account_id,
                created_at=now,
                catalog_version_id=snapshot.get("catalog_version_id"),
            )
        )
        version = row["row_version"] + 1
        session.execute(
            update(_BEACONS)
            .where(_BEACONS.c.id == beacon_id, _BEACONS.c.row_version == row["row_version"])
            .values(
                current_revision_no=revision_no,
                current_revision_id=beacon_id,
                state=BeaconLifecycleState.READY.value,
                updated_at=now,
                row_version=version,
            )
        )
        for field_code, value in snapshot.get("overrides", {}).items():
            session.execute(
                _OVERRIDES.insert().values(
                    id=uuid4(),
                    beacon_id=beacon_id,
                    revision_no=revision_no,
                    field_code=field_code,
                    value=value,
                    created_at=now,
                    row_version=1,
                )
            )
        self._audit(session, actor, "BEACON_SNAPSHOT_ACCEPTED", beacon_id, "SNAPSHOT_ACCEPTED")
        return self._finish(
            session,
            idempotency_key,
            fp,
            BeaconCommandResult(
                result=Result.SUCCEEDED,
                reason_code="SNAPSHOT_ACCEPTED",
                beacon_id=beacon_id,
                account_id=actor.account_id,
                state=BeaconLifecycleState.READY.value,
                revision_no=revision_no,
                row_version=version,
                source_url=row["source_url"],
            ),
        )

    @staticmethod
    def _validate_snapshot(snapshot: dict[str, Any]) -> None:
        if not isinstance(snapshot, dict) or not isinstance(snapshot.get("accepted_filter"), dict):
            raise BeaconRuntimeError("accepted snapshot is required")
        forbidden = ("html", "searchcore", "search_core", "context", "payload", "cookie", "token")
        blob = json.dumps(snapshot, ensure_ascii=False).lower()
        if any(word in blob for word in forbidden):
            raise BeaconRuntimeError("raw or provider-shaped evidence is forbidden")
        if (
            snapshot.get("status", "CLEAN") != "CLEAN"
            or snapshot.get("accepted_as_clean", True) is not True
        ):
            raise BeaconRuntimeError("snapshot is not clean")

    def patch(
        self,
        session: Session,
        *,
        actor_reference: str,
        beacon_id: UUID,
        patch: dict[str, Any],
        expected_row_version: int,
        idempotency_key: str,
    ) -> BeaconCommandResult:
        if "source_url" in patch:
            raise BeaconRuntimeError("source URL cannot be patched")
        actor = self._authority(session, actor_reference, None)
        row = (
            session.execute(select(_BEACONS).where(_BEACONS.c.id == beacon_id))
            .mappings()
            .one_or_none()
        )
        if row is None or row["account_id"] != actor.account_id:
            raise BeaconRuntimeError("beacon unavailable")
        fp = self._fingerprint(
            "patch", {"beacon": beacon_id, "patch": patch, "expected": expected_row_version}
        )
        replay = self._begin(session, idempotency_key, fp)
        if replay:
            return replay
        if row["row_version"] != expected_row_version:
            raise ConflictError("stale patch")
        current = (
            session.execute(
                select(_REVISIONS).where(
                    _REVISIONS.c.beacon_id == beacon_id,
                    _REVISIONS.c.revision_no == row["current_revision_no"],
                )
            )
            .mappings()
            .one_or_none()
        )
        if current is None:
            raise BeaconRuntimeError("beacon has no accepted configuration")
        accepted = dict(current["accepted_filter"])
        unknown = set(patch) - set(accepted)
        if unknown:
            raise BeaconRuntimeError("unsupported patch field")
        accepted.update(patch)
        revision_no = row["current_revision_no"] + 1
        now = self._now()
        session.execute(
            _REVISIONS.insert().values(
                beacon_id=beacon_id,
                revision_no=revision_no,
                source_url=row["source_url"],
                filter_candidate=current["filter_candidate"],
                accepted_filter=accepted,
                created_by_account_id=actor.account_id,
                created_at=now,
                catalog_version_id=current["catalog_version_id"],
            )
        )
        version = row["row_version"] + 1
        changed = session.execute(
            update(_BEACONS)
            .where(_BEACONS.c.id == beacon_id, _BEACONS.c.row_version == expected_row_version)
            .values(
                current_revision_no=revision_no,
                current_revision_id=beacon_id,
                updated_at=now,
                row_version=version,
            )
        )
        if getattr(changed, "rowcount", 0) != 1:
            raise ConflictError("stale patch")
        self._audit(session, actor, "BEACON_PATCHED", beacon_id, "CONFIGURATION_PATCHED")
        return self._finish(
            session,
            idempotency_key,
            fp,
            BeaconCommandResult(
                result=Result.SUCCEEDED,
                reason_code="PATCHED",
                beacon_id=beacon_id,
                account_id=actor.account_id,
                state=row["state"],
                revision_no=revision_no,
                row_version=version,
                source_url=row["source_url"],
            ),
        )

    def rename(
        self,
        session: Session,
        *,
        actor_reference: str,
        beacon_id: UUID,
        name: str,
        expected_row_version: int,
        idempotency_key: str,
    ) -> BeaconCommandResult:
        actor = self._authority(session, actor_reference, None)
        fp = self._fingerprint(
            "rename", {"beacon": beacon_id, "name": name, "expected": expected_row_version}
        )
        replay = self._begin(session, idempotency_key, fp)
        if replay:
            return replay
        result = session.execute(
            update(_BEACONS)
            .where(
                _BEACONS.c.id == beacon_id,
                _BEACONS.c.account_id == actor.account_id,
                _BEACONS.c.row_version == expected_row_version,
            )
            .values(name=name.strip(), updated_at=self._now(), row_version=expected_row_version + 1)
        )
        if getattr(result, "rowcount", 0) != 1:
            raise ConflictError("stale or unavailable beacon")
        self._audit(session, actor, "BEACON_RENAMED", beacon_id, "NAME_UPDATED")
        return self._finish(
            session,
            idempotency_key,
            fp,
            BeaconCommandResult(
                result=Result.SUCCEEDED,
                reason_code="RENAMED",
                beacon_id=beacon_id,
                account_id=actor.account_id,
                row_version=expected_row_version + 1,
            ),
        )

    def transition(
        self,
        session: Session,
        *,
        actor_reference: str,
        beacon_id: UUID,
        action: str,
        idempotency_key: str,
        expected_row_version: int | None = None,
        reason: str = "USER_REQUEST",
    ) -> BeaconCommandResult:
        actor = self._authority(session, actor_reference, None)
        self._lock(session, actor.account_id)
        row = (
            session.execute(select(_BEACONS).where(_BEACONS.c.id == beacon_id))
            .mappings()
            .one_or_none()
        )
        if row is None or row["account_id"] != actor.account_id:
            raise BeaconRuntimeError("beacon unavailable")
        if expected_row_version is not None and row["row_version"] != expected_row_version:
            raise ConflictError("stale beacon row version")
        fp = self._fingerprint(
            action, {"beacon": beacon_id, "reason": reason, "expected": expected_row_version}
        )
        replay = self._begin(session, idempotency_key, fp)
        if replay:
            return replay
        target = {
            "activate": BeaconLifecycleState.ACTIVE,
            "pause": BeaconLifecycleState.PAUSED,
            "resume": BeaconLifecycleState.ACTIVE,
            "freeze": BeaconLifecycleState.FROZEN,
            "archive": BeaconLifecycleState.ARCHIVED,
            "restore": BeaconLifecycleState.READY,
            "user_delete": BeaconLifecycleState.ARCHIVED,
            "permanent_delete": BeaconLifecycleState.PERMANENTLY_DELETED,
        }.get(action)
        if (
            target is None
            or target.value == row["state"]
            or row["state"] == BeaconLifecycleState.PERMANENTLY_DELETED.value
        ):
            raise BeaconRuntimeError("invalid lifecycle transition")
        if action in {"activate", "resume", "restore"}:
            count = session.execute(
                select(func.count())
                .select_from(_BEACONS)
                .where(_BEACONS.c.account_id == actor.account_id, _BEACONS.c.state.in_(_ACTIVE))
            ).scalar_one()
            decision = self.entitlement.decide(
                session, account_id=actor.account_id, action=action, active_count=count
            )
            if not decision.fresh or not decision.allowed:
                raise BeaconRuntimeError("current entitlement does not allow lifecycle action")
        now = self._now()
        version = row["row_version"] + 1
        result = session.execute(
            update(_BEACONS)
            .where(_BEACONS.c.id == beacon_id, _BEACONS.c.row_version == row["row_version"])
            .values(state=target.value, updated_at=now, row_version=version)
        )
        if getattr(result, "rowcount", 0) != 1:
            raise ConflictError("lifecycle race")
        session.execute(
            _EVENTS.insert().values(
                id=uuid4(),
                beacon_id=beacon_id,
                from_state=row["state"],
                to_state=target.value,
                actor_account_id=actor.account_id,
                reason=reason[:500],
                created_at=now,
            )
        )
        self._audit(session, actor, "BEACON_" + action.upper(), beacon_id, reason)
        return self._finish(
            session,
            idempotency_key,
            fp,
            BeaconCommandResult(
                result=Result.SUCCEEDED,
                reason_code="LIFECYCLE_TRANSITIONED",
                beacon_id=beacon_id,
                account_id=actor.account_id,
                state=target.value,
                revision_no=row["current_revision_no"],
                row_version=version,
                source_url=row["source_url"],
            ),
        )

    def get(self, session: Session, *, actor_reference: str, beacon_id: UUID) -> BeaconView:
        actor = self._authority(session, actor_reference, None)
        row = (
            session.execute(
                select(_BEACONS).where(
                    _BEACONS.c.id == beacon_id, _BEACONS.c.account_id == actor.account_id
                )
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            raise BeaconRuntimeError("beacon unavailable")
        return self._view(row)

    def list(self, session: Session, *, actor_reference: str) -> tuple[BeaconView, ...]:
        actor = self._authority(session, actor_reference, None)
        rows = (
            session.execute(
                select(_BEACONS)
                .where(_BEACONS.c.account_id == actor.account_id)
                .order_by(_BEACONS.c.created_at, _BEACONS.c.id)
            )
            .mappings()
            .all()
        )
        return tuple(self._view(row) for row in rows)

    def history(
        self, session: Session, *, actor_reference: str, beacon_id: UUID
    ) -> tuple[dict[str, Any], ...]:
        self.get(session, actor_reference=actor_reference, beacon_id=beacon_id)
        rows = (
            session.execute(
                select(_EVENTS)
                .where(_EVENTS.c.beacon_id == beacon_id)
                .order_by(_EVENTS.c.created_at, _EVENTS.c.id)
            )
            .mappings()
            .all()
        )
        return tuple(dict(row) for row in rows)

    create = create_preparation
    activate = transition
    pause = transition
    resume = transition
    freeze = transition
    archive = transition
    restore = transition
    user_delete = transition
    permanent_delete = transition


__all__ = [
    "AuthorityPort",
    "BeaconCommandResult",
    "BeaconManagementRuntime",
    "BeaconRuntimeError",
    "BeaconView",
    "ConflictError",
    "EntitlementDecision",
    "EntitlementPort",
    "ResolvedActor",
]
