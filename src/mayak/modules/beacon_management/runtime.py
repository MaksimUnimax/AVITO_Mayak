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

from .contracts import (
    BeaconActionCausation,
    BeaconLifecycleState,
    BeaconParserOutcomeStatus,
    BeaconSystemActorClass,
    ExtractedSearchConfigurationSnapshot,
)

_BEACONS = metadata.tables["mayak.beacon_beacons"]
_ACCOUNTS = metadata.tables["mayak.identity_accounts"]
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


class SystemAuthorityPort(Protocol):
    def resolve_system(
        self, session: Session, *, actor_reference: str
    ) -> "ResolvedSystemActor": ...


@dataclass(frozen=True, slots=True)
class ResolvedActor:
    """Server-established authority; never a caller-supplied authorization flag."""

    actor_id: UUID
    account_id: UUID
    verified: bool
    reference: str


@dataclass(frozen=True, slots=True)
class VerifiedSupportAuthority:
    """Verified operator authority and explicit target-account scope."""

    operator_account_id: UUID
    target_account_id: UUID
    reference: str
    verified: bool = True

    def __post_init__(self) -> None:
        if not self.verified or self.operator_account_id == self.target_account_id:
            raise BeaconRuntimeError("distinct verified support authority required")


@dataclass(frozen=True, slots=True)
class ResolvedSystemActor:
    """Service authority; it is never an account owner."""

    actor_id: UUID
    verified: bool
    reference: str
    system_actor_class: str


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
        except (TypeError, ValueError, json.JSONDecodeError):
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


class BeaconRevisionView(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    beacon_id: UUID
    revision_no: int
    revision_id: UUID
    source_url: str
    snapshot_id: str
    parser_outcome_status: str
    accepted_as_clean: bool
    parser_evidence_reference: str
    unsupported_parameters: tuple[str, ...]
    warning_codes: tuple[str, ...]
    accepted_filter: dict[str, Any]
    overrides: tuple[dict[str, Any], ...]


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
        system_authority: SystemAuthorityPort | None = None,
    ) -> None:
        self.authority = authority
        self.entitlement = entitlement
        self.idempotency = idempotency or PostgresTerminalIdempotencyRepository()
        self.audit = audit or PostgresAuditRepository()
        self.system_authority = system_authority

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
        try:
            actor = self.authority.resolve(
                session, actor_reference=actor_reference, requested_account_id=requested_account_id
            )
        except AttributeError as exc:
            raise BeaconRuntimeError("verified authority required") from exc
        if not isinstance(actor, ResolvedActor) or not actor.verified:
            raise BeaconRuntimeError("verified authority required")
        return actor

    def _system_authority(self, session: Session, actor_reference: str) -> ResolvedSystemActor:
        if self.system_authority is None:
            raise BeaconRuntimeError("system lifecycle authority required")
        actor = self.system_authority.resolve_system(session, actor_reference=actor_reference)
        if not isinstance(actor, ResolvedSystemActor) or not actor.verified:
            raise BeaconRuntimeError("verified system authority required")
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
        self,
        session: Session,
        actor: ResolvedActor | ResolvedSystemActor,
        action: str,
        beacon_id: UUID,
        reason: str,
        *,
        account_id: UUID | None = None,
        system_actor: bool = False,
        correlation: CorrelationContext | None = None,
    ) -> None:
        correlation = correlation or CorrelationContext(
            correlation_id=CorrelationId(value=str(uuid4()))
        )
        context = AuditContext(
            actor_category=(
                AuditActorCategory.SERVICE if system_actor else AuditActorCategory.OPERATOR
            ),
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
            actor_account_id=(
                None
                if system_actor
                else (getattr(actor, "account_id", None) if account_id is None else account_id)
            ),
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

    def create(self, session: Session, **kwargs: Any) -> BeaconCommandResult:
        """Explicit preparation command kept separate from lifecycle actions."""
        return self.create_preparation(session, **kwargs)

    def accept_snapshot(
        self,
        session: Session,
        *,
        actor_reference: str,
        beacon_id: UUID,
        snapshot: ExtractedSearchConfigurationSnapshot | dict[str, Any],
        idempotency_key: str,
        expected_row_version: int | None = None,
    ) -> BeaconCommandResult:
        if expected_row_version is None:
            raise ConflictError("expected row version is required")
        actor = self._authority(session, actor_reference, None)
        row = (
            session.execute(select(_BEACONS).where(_BEACONS.c.id == beacon_id).with_for_update())
            .mappings()
            .one_or_none()
        )
        if row is None or row["account_id"] != actor.account_id:
            raise BeaconRuntimeError("beacon unavailable")
        payload = self._validate_snapshot(snapshot)
        if row["row_version"] != expected_row_version:
            raise ConflictError("stale beacon row version")
        fp = self._fingerprint(
            "accept_snapshot",
            {"beacon": beacon_id, "snapshot": payload, "expected": expected_row_version},
        )
        replay = self._begin(session, idempotency_key, fp)
        if replay:
            return replay
        revision_no = (row["current_revision_no"] or 0) + 1
        revision_id = uuid4()
        now = self._now()
        session.execute(
            _REVISIONS.insert().values(
                beacon_id=beacon_id,
                revision_no=revision_no,
                revision_id=revision_id,
                source_url=row["source_url"],
                snapshot_id=payload["snapshot_id"],
                parser_outcome_status=payload["parser_outcome_status"],
                accepted_as_clean=payload["accepted_as_clean"],
                parser_evidence_reference=payload["parser_evidence_reference"],
                unsupported_parameters=payload["unsupported_parameters"],
                warning_codes=payload["warning_codes"],
                filter_candidate=None,
                accepted_filter=payload["accepted_filter"],
                created_by_account_id=actor.account_id,
                created_at=now,
                catalog_version_id=payload.get("catalog_version_id"),
            )
        )
        version = row["row_version"] + 1
        session.execute(
            update(_BEACONS)
            .where(_BEACONS.c.id == beacon_id, _BEACONS.c.row_version == row["row_version"])
            .values(
                current_revision_no=revision_no,
                current_revision_id=revision_id,
                state=BeaconLifecycleState.READY.value,
                updated_at=now,
                row_version=version,
            )
        )
        for field_code, value in payload.get("overrides", {}).items():
            session.execute(
                _OVERRIDES.insert().values(
                    id=uuid4(),
                    beacon_id=beacon_id,
                    revision_no=revision_no,
                    field_code=field_code,
                    value=value,
                    parser_evidence_reference=payload["parser_evidence_reference"],
                    override_evidence_reference=f"snapshot:{payload['snapshot_id']}:{field_code}",
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
    def _validate_snapshot(
        snapshot: ExtractedSearchConfigurationSnapshot | dict[str, Any],
    ) -> dict[str, Any]:
        if isinstance(snapshot, dict):
            blob = json.dumps(snapshot, ensure_ascii=False).lower()
            forbidden = (
                "html",
                "searchcore",
                "search_core",
                "context",
                "payload",
                "cookie",
                "token",
            )
            if any(word in blob for word in forbidden):
                raise BeaconRuntimeError("raw or provider-shaped evidence is forbidden")
            if snapshot.get("status") != "CLEAN" or snapshot.get("accepted_as_clean") is not True:
                raise BeaconRuntimeError("snapshot is not clean")
            raise BeaconRuntimeError("snapshot contract evidence is required")
        if not isinstance(snapshot, ExtractedSearchConfigurationSnapshot):
            raise BeaconRuntimeError("accepted snapshot contract is required")
        evidence = snapshot.parser_evidence_reference
        if (
            evidence is None
            or evidence.safety_class.name != "OPAQUE"
            or evidence.raw_provider_payload_authority
        ):
            raise BeaconRuntimeError("opaque parser evidence is required")
        if snapshot.parser_outcome_status is not BeaconParserOutcomeStatus.CLEAN:
            raise BeaconRuntimeError("snapshot is not clean")
        if snapshot.accepted_as_clean is not True or snapshot.unsupported_parameters:
            raise BeaconRuntimeError("snapshot is not safely accepted")
        accepted = {"normalized_filter_values": list(snapshot.normalized_filter_values)}
        return {
            "snapshot_id": snapshot.snapshot_id,
            "parser_outcome_status": snapshot.parser_outcome_status.value,
            "accepted_as_clean": snapshot.accepted_as_clean,
            "parser_evidence_reference": evidence.evidence_reference,
            "unsupported_parameters": list(snapshot.unsupported_parameters),
            "warning_codes": list(snapshot.warning_codes),
            "accepted_filter": accepted,
            "overrides": {},
        }

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
        actor = self._authority(session, actor_reference, None)
        return self._patch_as_actor(
            session, actor=actor, target_account_id=actor.account_id, beacon_id=beacon_id,
            patch=patch, expected_row_version=expected_row_version,
            idempotency_key=idempotency_key,
        )

    def patch_current_configuration_for_support(
        self,
        session: Session,
        *,
        authority: VerifiedSupportAuthority,
        beacon_id: UUID,
        patch: dict[str, Any],
        expected_row_version: int,
        idempotency_key: str,
        reason: str,
        correlation: CorrelationContext,
    ) -> BeaconCommandResult:
        """Cross-account support patch; owner DML stays in Beacon Management."""
        row_account = session.execute(
            select(_BEACONS.c.account_id).where(_BEACONS.c.id == beacon_id)
        ).scalar_one_or_none()
        if not authority.verified or row_account != authority.target_account_id:
            raise BeaconRuntimeError("beacon target account mismatch")
        actor = ResolvedActor(
            actor_id=authority.operator_account_id,
            account_id=authority.operator_account_id,
            verified=True,
            reference=authority.reference,
        )
        return self._patch_as_actor(
            session, actor=actor, target_account_id=authority.target_account_id,
            beacon_id=beacon_id, patch=patch, expected_row_version=expected_row_version,
            idempotency_key=idempotency_key, strict_expected_row_version=True,
            audit_reason=reason, correlation=correlation,
        )

    def _patch_as_actor(
        self,
        session: Session,
        *,
        actor: ResolvedActor,
        target_account_id: UUID,
        beacon_id: UUID,
        patch: dict[str, Any],
        expected_row_version: int,
        idempotency_key: str,
        strict_expected_row_version: bool = False,
        audit_reason: str = "CONFIGURATION_PATCHED",
        correlation: CorrelationContext | None = None,
    ) -> BeaconCommandResult:
        if "source_url" in patch:
            raise BeaconRuntimeError("source URL cannot be patched")
        # PATCH is field-scoped last-write-wins.  Serialize the owner account,
        # then reread authoritative state; expected_row_version is an
        # observation/precondition for callers, not a stale whole-form reject.
        self._lock(session, target_account_id)
        row = (
            session.execute(select(_BEACONS).where(_BEACONS.c.id == beacon_id).with_for_update())
            .mappings()
            .one_or_none()
        )
        if row is None or row["account_id"] != target_account_id:
            raise BeaconRuntimeError("beacon unavailable")
        if strict_expected_row_version and row["row_version"] != expected_row_version:
            raise ConflictError("stale patch")
        fp = self._fingerprint("patch", {"beacon": beacon_id, "patch": patch})
        replay = self._begin(session, idempotency_key, fp)
        if replay:
            return replay
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
        revision_id = uuid4()
        now = self._now()
        session.execute(
            _REVISIONS.insert().values(
                beacon_id=beacon_id,
                revision_no=revision_no,
                revision_id=revision_id,
                source_url=row["source_url"],
                snapshot_id=current["snapshot_id"],
                parser_outcome_status=current["parser_outcome_status"],
                accepted_as_clean=current["accepted_as_clean"],
                parser_evidence_reference=current["parser_evidence_reference"],
                unsupported_parameters=current["unsupported_parameters"],
                warning_codes=current["warning_codes"],
                filter_candidate=current["filter_candidate"],
                accepted_filter=accepted,
                created_by_account_id=target_account_id,
                created_at=now,
                catalog_version_id=current["catalog_version_id"],
            )
        )
        version = row["row_version"] + 1
        changed = session.execute(
            update(_BEACONS)
            .where(_BEACONS.c.id == beacon_id, _BEACONS.c.row_version == row["row_version"])
            .values(
                current_revision_no=revision_no,
                current_revision_id=revision_id,
                updated_at=now,
                row_version=version,
            )
        )
        if getattr(changed, "rowcount", 0) != 1:
            raise ConflictError("stale patch")
        for field_code, value in patch.items():
            session.execute(
                _OVERRIDES.insert().values(
                    id=uuid4(),
                    beacon_id=beacon_id,
                    revision_no=revision_no,
                    field_code=field_code,
                    value=value,
                    parser_evidence_reference=current["parser_evidence_reference"],
                    override_evidence_reference=f"patch:{revision_id}:{field_code}",
                    created_at=now,
                    row_version=1,
                )
            )
        self._audit(
            session, actor, "BEACON_PATCHED", beacon_id, audit_reason,
            account_id=actor.account_id, correlation=correlation,
        )
        return self._finish(
            session,
            idempotency_key,
            fp,
            BeaconCommandResult(
                result=Result.SUCCEEDED,
                reason_code="PATCHED",
                beacon_id=beacon_id,
                account_id=target_account_id,
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

    def _transition(
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
        return self._transition_as_actor(
            session,
            actor=actor,
            beacon_id=beacon_id,
            action=action,
            idempotency_key=idempotency_key,
            expected_row_version=expected_row_version,
            reason=reason,
            causation=None,
        )

    def _transition_as_actor(
        self,
        session: Session,
        *,
        actor: ResolvedActor | ResolvedSystemActor,
        beacon_id: UUID,
        action: str,
        idempotency_key: str,
        expected_row_version: int | None,
        reason: str,
        causation: BeaconActionCausation | None,
    ) -> BeaconCommandResult:
        if isinstance(actor, ResolvedActor):
            # Serialize all owner Beacon lifecycle decisions before taking a
            # per-Beacon row lock; otherwise distinct final-slot rows can both
            # observe the same active count.
            self._lock(session, actor.account_id)
            session.execute(
                select(_ACCOUNTS).where(_ACCOUNTS.c.id == actor.account_id).with_for_update()
            ).one()
        beacon_query = select(_BEACONS).where(_BEACONS.c.id == beacon_id)
        if isinstance(actor, ResolvedActor):
            beacon_query = beacon_query.with_for_update()
        row = session.execute(beacon_query).mappings().one_or_none()
        if row is None or (
            isinstance(actor, ResolvedActor) and row["account_id"] != actor.account_id
        ):
            raise BeaconRuntimeError("beacon unavailable")
        self._lock(session, row["account_id"])
        session.execute(
            select(_ACCOUNTS).where(_ACCOUNTS.c.id == row["account_id"]).with_for_update()
        ).one()
        row = (
            session.execute(select(_BEACONS).where(_BEACONS.c.id == beacon_id).with_for_update())
            .mappings()
            .one()
        )
        if expected_row_version is None:
            raise ConflictError("expected row version is required")
        if row["row_version"] != expected_row_version:
            raise ConflictError("stale beacon row version")
        fp = self._fingerprint(
            action, {"beacon": beacon_id, "reason": reason, "expected": expected_row_version}
        )
        replay = self._begin(session, idempotency_key, fp)
        if replay:
            return replay
        legal = {
            "activate": {BeaconLifecycleState.READY.value},
            "pause": {BeaconLifecycleState.ACTIVE.value},
            "resume": {BeaconLifecycleState.PAUSED.value, BeaconLifecycleState.FROZEN.value},
            "archive": {
                BeaconLifecycleState.READY.value,
                BeaconLifecycleState.PAUSED.value,
                BeaconLifecycleState.FROZEN.value,
            },
            "user_delete": {
                BeaconLifecycleState.DRAFT.value,
                BeaconLifecycleState.READY.value,
                BeaconLifecycleState.ACTIVE.value,
                BeaconLifecycleState.PAUSED.value,
                BeaconLifecycleState.FROZEN.value,
            },
            "permanent_delete": {BeaconLifecycleState.ARCHIVED.value},
        }
        if action == "freeze_after_expiry":
            legal[action] = {BeaconLifecycleState.ACTIVE.value}
        targets = {
            "activate": BeaconLifecycleState.ACTIVE,
            "pause": BeaconLifecycleState.PAUSED,
            "resume": BeaconLifecycleState.ACTIVE,
            "freeze_after_expiry": BeaconLifecycleState.FROZEN,
            "archive": BeaconLifecycleState.ARCHIVED,
            "user_delete": BeaconLifecycleState.ARCHIVED,
            "permanent_delete": BeaconLifecycleState.PERMANENTLY_DELETED,
            "restore": BeaconLifecycleState.READY,
        }
        if action == "restore":
            allowed_states = {
                BeaconLifecycleState.ARCHIVED.value,
                BeaconLifecycleState.FROZEN.value,
                BeaconLifecycleState.PAUSED.value,
            }
        else:
            allowed_states = legal.get(action, set())
        target = targets.get(action)
        if target is None or row["state"] not in allowed_states:
            raise BeaconRuntimeError("invalid lifecycle transition")
        account_id = row["account_id"]
        if action == "activate" and row["current_revision_no"] is None:
            raise BeaconRuntimeError("activation requires accepted current revision")
        if action in {"activate", "resume", "restore"}:
            # Lock the complete account-owned Beacon set before deriving the
            # active count.  This is the database fact used by Module 04's
            # capacity decision and prevents a final-slot snapshot race.
            session.execute(
                select(_BEACONS).where(_BEACONS.c.account_id == account_id).with_for_update()
            ).all()
            count = session.execute(
                select(func.count())
                .select_from(_BEACONS)
                .where(_BEACONS.c.account_id == account_id, _BEACONS.c.state.in_(_ACTIVE))
            ).scalar_one()
            decision = self.entitlement.decide(
                session, account_id=account_id, action=action, active_count=count
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
                actor_account_id=None if causation is not None else account_id,
                system_actor_class=(causation.service_actor_class.value if causation else None),
                causation_reference=(causation.causation_reference if causation else None),
                policy_source_reference=(causation.policy_source_reference if causation else None),
                reason=reason[:500],
                created_at=now,
            )
        )
        self._audit(
            session,
            actor,
            "BEACON_" + action.upper(),
            beacon_id,
            reason,
            account_id=None if causation is not None else account_id,
            system_actor=causation is not None,
        )
        return self._finish(
            session,
            idempotency_key,
            fp,
            BeaconCommandResult(
                result=Result.SUCCEEDED,
                reason_code="LIFECYCLE_TRANSITIONED",
                beacon_id=beacon_id,
                account_id=account_id,
                state=target.value,
                revision_no=row["current_revision_no"],
                row_version=version,
                source_url=row["source_url"],
            ),
        )

    def activate(
        self,
        session: Session,
        *,
        actor_reference: str,
        beacon_id: UUID,
        idempotency_key: str,
        expected_row_version: int,
    ) -> BeaconCommandResult:
        return self._transition(
            session,
            actor_reference=actor_reference,
            beacon_id=beacon_id,
            action="activate",
            idempotency_key=idempotency_key,
            expected_row_version=expected_row_version,
        )

    def pause(
        self,
        session: Session,
        *,
        actor_reference: str,
        beacon_id: UUID,
        idempotency_key: str,
        expected_row_version: int,
    ) -> BeaconCommandResult:
        return self._transition(
            session,
            actor_reference=actor_reference,
            beacon_id=beacon_id,
            action="pause",
            idempotency_key=idempotency_key,
            expected_row_version=expected_row_version,
        )

    def resume(
        self,
        session: Session,
        *,
        actor_reference: str,
        beacon_id: UUID,
        idempotency_key: str,
        expected_row_version: int,
    ) -> BeaconCommandResult:
        return self._transition(
            session,
            actor_reference=actor_reference,
            beacon_id=beacon_id,
            action="resume",
            idempotency_key=idempotency_key,
            expected_row_version=expected_row_version,
        )

    def archive(
        self,
        session: Session,
        *,
        actor_reference: str,
        beacon_id: UUID,
        idempotency_key: str,
        expected_row_version: int,
    ) -> BeaconCommandResult:
        return self._transition(
            session,
            actor_reference=actor_reference,
            beacon_id=beacon_id,
            action="archive",
            idempotency_key=idempotency_key,
            expected_row_version=expected_row_version,
        )

    def restore(
        self,
        session: Session,
        *,
        actor_reference: str,
        beacon_id: UUID,
        idempotency_key: str,
        expected_row_version: int,
    ) -> BeaconCommandResult:
        return self._transition(
            session,
            actor_reference=actor_reference,
            beacon_id=beacon_id,
            action="restore",
            idempotency_key=idempotency_key,
            expected_row_version=expected_row_version,
        )

    def user_delete(
        self,
        session: Session,
        *,
        actor_reference: str,
        beacon_id: UUID,
        idempotency_key: str,
        expected_row_version: int,
    ) -> BeaconCommandResult:
        return self._transition(
            session,
            actor_reference=actor_reference,
            beacon_id=beacon_id,
            action="user_delete",
            idempotency_key=idempotency_key,
            expected_row_version=expected_row_version,
        )

    def permanent_delete(
        self,
        session: Session,
        *,
        actor_reference: str,
        beacon_id: UUID,
        idempotency_key: str,
        expected_row_version: int,
    ) -> BeaconCommandResult:
        return self._transition(
            session,
            actor_reference=actor_reference,
            beacon_id=beacon_id,
            action="permanent_delete",
            idempotency_key=idempotency_key,
            expected_row_version=expected_row_version,
        )

    def freeze_after_expiry(
        self,
        session: Session,
        *,
        system_actor_reference: str,
        beacon_id: UUID,
        idempotency_key: str,
        expected_row_version: int,
        causation: BeaconActionCausation,
    ) -> BeaconCommandResult:
        if causation.service_actor_class.value == "":
            raise BeaconRuntimeError("system causation is required")
        actor = self._system_authority(session, system_actor_reference)
        if actor.system_actor_class != causation.service_actor_class.value:
            raise BeaconRuntimeError("system authority class does not match causation")
        if (
            causation.service_actor_class
            is not BeaconSystemActorClass.ENTITLEMENTS_AND_BILLING_SERVICE
        ):
            raise BeaconRuntimeError("paid expiry requires entitlements and billing authority")
        result = self._transition_as_actor(
            session,
            actor=actor,
            beacon_id=beacon_id,
            action="freeze_after_expiry",
            idempotency_key=idempotency_key,
            expected_row_version=expected_row_version,
            reason="PAID_ACCESS_EXPIRED:" + causation.causation_reference,
            causation=causation,
        )
        return result

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

    def get_revision(
        self, session: Session, *, actor_reference: str, beacon_id: UUID, revision_no: int
    ) -> BeaconRevisionView:
        self.get(session, actor_reference=actor_reference, beacon_id=beacon_id)
        row = (
            session.execute(
                select(_REVISIONS).where(
                    _REVISIONS.c.beacon_id == beacon_id, _REVISIONS.c.revision_no == revision_no
                )
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            raise BeaconRuntimeError("revision unavailable")
        overrides = (
            session.execute(
                select(_OVERRIDES)
                .where(_OVERRIDES.c.beacon_id == beacon_id, _OVERRIDES.c.revision_no == revision_no)
                .order_by(_OVERRIDES.c.field_code)
            )
            .mappings()
            .all()
        )
        return BeaconRevisionView(
            beacon_id=beacon_id,
            revision_no=revision_no,
            revision_id=row["revision_id"],
            source_url=row["source_url"],
            snapshot_id=row["snapshot_id"],
            parser_outcome_status=row["parser_outcome_status"],
            accepted_as_clean=row["accepted_as_clean"],
            parser_evidence_reference=row["parser_evidence_reference"],
            unsupported_parameters=tuple(row["unsupported_parameters"]),
            warning_codes=tuple(row["warning_codes"]),
            accepted_filter=dict(row["accepted_filter"]),
            overrides=tuple(dict(item) for item in overrides),
        )


__all__ = [
    "AuthorityPort",
    "BeaconCommandResult",
    "BeaconManagementRuntime",
    "BeaconRevisionView",
    "BeaconRuntimeError",
    "BeaconView",
    "ConflictError",
    "EntitlementDecision",
    "EntitlementPort",
    "ResolvedActor",
    "ResolvedSystemActor",
    "SystemAuthorityPort",
]
