"""Durable Admin & Support runtime over the Module 11-owned tables.

The runtime deliberately knows only public ports for other modules.  Ports are
injected by the application composition root; this package never imports a
foreign repository, ORM model, provider adapter, or business table.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any, Protocol, cast
from uuid import UUID, uuid4

from sqlalchemy import Table, select, text, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.orm import Session

from mayak.contracts.idempotency import IdempotencyDecision
from mayak.contracts.results import CommonOutcome, Result
from mayak.persistence.idempotency import PostgresTerminalIdempotencyRepository
from mayak.persistence.metadata import metadata
from mayak.platform.correlation import CorrelationContext, CorrelationId
from mayak.platform.correlation_context import (
    correlation_context_scope,
    current_correlation_context,
)
from mayak.platform.idempotency import IdempotencyFingerprint, IdempotencyKey, IdempotencyScope

from .contracts import SupportCaseState


class SupportRuntimeError(RuntimeError):
    """Safe, operator-facing runtime failure."""


class AuthorizationDenied(SupportRuntimeError):
    pass


class TargetNotFound(SupportRuntimeError):
    pass


class StaleCase(SupportRuntimeError):
    pass


class IdempotencyConflict(SupportRuntimeError):
    pass


class ReconciliationRequired(SupportRuntimeError):
    pass


class OutcomeClass(StrEnum):
    SUCCEEDED = "SUCCEEDED"
    REJECTED = "REJECTED"
    CONFLICT = "CONFLICT"
    POLICY_BLOCKED = "POLICY_BLOCKED"
    AMBIGUOUS = "AMBIGUOUS"
    RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"
    REPLAYED = "REPLAYED"


ROLE_ACTIONS = frozenset({"ASSIGN_SUPPORT", "ASSIGN_ADMIN", "REVOKE_SUPPORT", "REVOKE_ADMIN"})
TARIFF_ACTIONS = frozenset({"ASSIGN_BASIC", "BOOTSTRAP_TARIFFS"})
ACCESS_ACTIONS = frozenset({"GRANT_ACCESS", "REVOKE_ACCESS"})
BEACON_ACTIONS = frozenset({"PATCH_CURRENT_CONFIGURATION"})
ANCHOR_ACTIONS = frozenset({"REVIEW", "PREPARE_CORRECTION"})


@dataclass(frozen=True, slots=True)
class VerifiedActor:
    """Identity-owned actor context; browser input cannot construct authority."""

    actor_account_id: UUID
    role: str
    authorization_scope: str
    authorization_reference: str
    verified: bool = True
    identity_session_reference: Any | None = None

    def __post_init__(self) -> None:
        if not self.verified or self.role not in {"ADMIN", "SUPPORT"}:
            raise AuthorizationDenied("verified operator authority required")


class IdentityPort(Protocol):
    def verify_operator(self, session: Session, actor_reference: str) -> VerifiedActor: ...

    def execute_role_action(
        self,
        session: Session,
        *,
        actor: VerifiedActor,
        target: UUID,
        action: str,
        reason: str,
        idempotency_key: str,
        correlation_id: str | None = None,
    ) -> "OwningOutcome": ...

    def account_summary(
        self, session: Session, *, actor: VerifiedActor, target: UUID
    ) -> dict[str, Any]: ...

    def operator_exists(self, session: Session, *, actor: VerifiedActor, target: UUID) -> bool: ...

class EntitlementsPort(Protocol):
    def execute_tariff_action(
        self, session: Session, *, actor: VerifiedActor, target: UUID, action: str,
        reason: str, idempotency_key: str, target_account_id: UUID
    ) -> "OwningOutcome": ...

    def execute_access_action(
        self,
        session: Session,
        *,
        actor: VerifiedActor,
        target: UUID,
        action: str,
        reason: str,
        idempotency_key: str,
        target_account_id: UUID,
    ) -> "OwningOutcome": ...

    def safe_summary(
        self, session: Session, *, actor: VerifiedActor, target: UUID
    ) -> dict[str, Any]: ...


class BeaconPort(Protocol):
    def execute_support_patch(
        self, session: Session, *, actor: VerifiedActor, target: UUID,
        target_account_id: UUID, patch: dict[str, Any], expected_row_version: int,
        reason: str, idempotency_key: str, correlation_id: str,
    ) -> "OwningOutcome": ...

    def safe_summary(
        self, session: Session, *, actor: VerifiedActor, target: UUID
    ) -> dict[str, Any]: ...


class ScanPort(Protocol):
    def execute_anchor_action(
        self,
        session: Session,
        *,
        actor: VerifiedActor,
        target: UUID,
        action: str,
        reason: str,
        idempotency_key: str,
    ) -> "OwningOutcome": ...

    def safe_summary(
        self, session: Session, *, actor: VerifiedActor, target: UUID
    ) -> dict[str, Any]: ...


class NotificationPort(Protocol):
    def safe_diagnostics(
        self, session: Session, *, actor: VerifiedActor, target: UUID
    ) -> dict[str, Any]: ...


@dataclass(frozen=True, slots=True)
class OwningOutcome:
    owner: str
    outcome_reference: str
    outcome_class: OutcomeClass
    message: str = ""


@dataclass(frozen=True, slots=True)
class SupportCaseView:
    case_id: UUID
    account_id: UUID
    opened_by_account_id: UUID
    assigned_to_account_id: UUID | None
    state: str
    subject: str
    row_version: int
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class MutationResult:
    action: str
    state: OutcomeClass
    target: str
    owning_module: str
    outcome_reference: str
    event_id: UUID | None = None
    replayed: bool = False


def _table(session: Session, name: str) -> Table:
    return metadata.tables[f"mayak.{name}"]


def _fingerprint(action: str, values: dict[str, Any]) -> IdempotencyFingerprint:
    canonical = json.dumps(
        {"action": action, **values}, sort_keys=True, separators=(",", ":"), default=str
    )
    return IdempotencyFingerprint(value=hashlib.sha256(canonical.encode()).hexdigest())


def _support_case_view(row: Any) -> SupportCaseView:
    """Project the physical support-case row into the public runtime view."""
    return SupportCaseView(
        case_id=row["id"],
        account_id=row["account_id"],
        opened_by_account_id=row["opened_by_account_id"],
        assigned_to_account_id=row["assigned_to_account_id"],
        state=row["state"],
        subject=row["subject"],
        row_version=row["row_version"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _command_correlation(correlation_id: str | None) -> str:
    context = current_correlation_context()
    if correlation_id and correlation_id != "rf20":
        return correlation_id
    return context.correlation_id.value if context is not None else f"rf20:{uuid4()}"


class SupportRuntime:
    """Support owner plus public-port orchestration facade."""

    IDEMPOTENCY_SCOPE = IdempotencyScope(value="admin_support.rf20")

    def __init__(
        self,
        *,
        identity: IdentityPort,
        entitlements: EntitlementsPort,
        beacon: BeaconPort,
        scan: ScanPort,
        notification: NotificationPort,
    ) -> None:
        self.identity = identity
        self.entitlements = entitlements
        self.beacon = beacon
        self.scan = scan
        self.notification = notification
        self._idempotency = PostgresTerminalIdempotencyRepository()

    @staticmethod
    def _now() -> datetime:
        return datetime.now(UTC)

    def _lock_idempotency(self, session: Session, key: str) -> None:
        """Serialize the complete RF20 command on PostgreSQL.

        The lock is transaction-scoped and deliberately precedes the first
        idempotency read.  SQLite/unit doubles do not expose PostgreSQL
        advisory locks, so they retain their existing deterministic behavior;
        PostgreSQL is the authority for RF20 acceptance.
        """
        bind = session.get_bind()
        if bind.dialect.name != "postgresql":
            return
        digest = hashlib.sha256(
            f"{self.IDEMPOTENCY_SCOPE.value}:{key.strip()}".encode("utf-8")
        ).digest()
        lock_key = int.from_bytes(digest[:8], "big", signed=True)
        session.execute(text("SELECT pg_advisory_xact_lock(:lock_key)"), {"lock_key": lock_key})

    def open_case(
        self,
        session: Session,
        *,
        actor: VerifiedActor,
        account_id: UUID,
        subject: str,
        reason: str,
        idempotency_key: str,
        correlation_id: str | None = None,
    ) -> MutationResult:
        self._require_operator(actor)
        if not reason.strip() or not subject.strip():
            raise ValueError("subject and reason are required")
        return self._case_mutation(
            session,
            actor=actor,
            account_id=account_id,
            action="OPEN_CASE",
            reason=reason,
            key=idempotency_key,
            values={"subject": subject},
            correlation_id=correlation_id,
            operation=lambda case_id, now: self._insert_case(
                session, case_id, actor, account_id, subject, now
            ),
        )

    def add_internal_note(
        self,
        session: Session,
        *,
        actor: VerifiedActor,
        case_id: UUID,
        body: str,
        reason: str,
        idempotency_key: str,
    ) -> MutationResult:
        self._require_operator(actor)
        clean = body.strip()
        if not clean or len(clean) > 65536:
            raise ValueError("note body must be non-empty and bounded")
        lowered = clean.lower()
        if any(
            word in lowered
            for word in (
                "authorization",
                "webappdata",
                "private_key",
                "raw_provider",
                "password",
                "token",
            )
        ):
            raise ValueError("note contains forbidden sensitive material")
        case = self.get_case(session, case_id)
        return self._case_mutation(
            session,
            actor=actor,
            account_id=case.account_id,
            action="RECORD_INTERNAL_NOTE",
            reason=reason,
            key=idempotency_key,
            values={"case_id": str(case_id), "body": clean},
            correlation_id=None,
            operation=lambda _case_id, now: self._insert_note(session, case_id, actor, clean, now),
        )

    def transition_case(
        self,
        session: Session,
        *,
        actor: VerifiedActor,
        case_id: UUID,
        target_state: SupportCaseState,
        expected_row_version: int,
        reason: str,
        idempotency_key: str,
        evidence_reference: str | None = None,
    ) -> MutationResult:
        self._require_operator(actor)
        if (
            target_state in {SupportCaseState.RESOLVED, SupportCaseState.CLOSED}
            and not evidence_reference
        ):
            raise ValueError("resolution/close requires safe evidence")
        case = self.get_case(session, case_id)
        allowed_transitions = {
            SupportCaseState.OPEN: {
                SupportCaseState.IN_PROGRESS,
                SupportCaseState.WAITING_FOR_EVIDENCE,
                SupportCaseState.ESCALATED,
                SupportCaseState.REJECTED,
            },
            SupportCaseState.IN_PROGRESS: {
                SupportCaseState.WAITING_FOR_EVIDENCE,
                SupportCaseState.ESCALATED,
                SupportCaseState.RESOLVED,
                SupportCaseState.CLOSED,
            },
            SupportCaseState.WAITING_FOR_EVIDENCE: {
                SupportCaseState.IN_PROGRESS,
                SupportCaseState.ESCALATED,
                SupportCaseState.RESOLVED,
                SupportCaseState.CLOSED,
            },
            SupportCaseState.ESCALATED: {
                SupportCaseState.IN_PROGRESS,
                SupportCaseState.RESOLVED,
                SupportCaseState.CLOSED,
            },
            SupportCaseState.RESOLVED: {SupportCaseState.CLOSED},
            SupportCaseState.CLOSED: set(),
            SupportCaseState.REJECTED: set(),
            SupportCaseState.AMBIGUOUS: set(),
        }
        if target_state not in allowed_transitions.get(SupportCaseState(case.state), set()):
            raise SupportRuntimeError("invalid support case transition")
        return self._case_mutation(
            session,
            actor=actor,
            account_id=case.account_id,
            action=f"CASE_{target_state.value}",
            reason=reason,
            key=idempotency_key,
            values={
                "case_id": str(case_id),
                "expected": expected_row_version,
                "state": target_state.value,
                "evidence": evidence_reference,
            },
            correlation_id=None,
            operation=lambda _case_id, now: self._update_case(
                session, case_id, target_state.value, expected_row_version, now
            ),
        )

    def assign_case(
        self,
        session: Session,
        *,
        actor: VerifiedActor,
        case_id: UUID,
        assignee_account_id: UUID,
        reason: str,
        idempotency_key: str,
    ) -> MutationResult:
        self._require_operator(actor)
        case = self.get_case(session, case_id)
        if not reason.strip() or not self.identity.operator_exists(
            session, actor=actor, target=assignee_account_id
        ):
            raise AuthorizationDenied("assignment target is not an active operator")
        return self._case_mutation(
            session,
            actor=actor,
            account_id=case.account_id,
            action="ASSIGN_CASE",
            reason=reason,
            key=idempotency_key,
            values={"case_id": str(case_id), "assignee": str(assignee_account_id)},
            correlation_id=None,
            operation=lambda _case_id, now: self._assign_case(
                session, case_id, assignee_account_id, now
            ),
        )

    def escalate_case(
        self,
        session: Session,
        *,
        actor: VerifiedActor,
        case_id: UUID,
        reason: str,
        idempotency_key: str,
    ) -> MutationResult:
        return self.transition_case(
            session,
            actor=actor,
            case_id=case_id,
            target_state=SupportCaseState.ESCALATED,
            expected_row_version=self.get_case(session, case_id).row_version,
            reason=reason,
            idempotency_key=idempotency_key,
        )

    def get_case(self, session: Session, case_id: UUID) -> SupportCaseView:
        cases = _table(session, "support_cases")
        row = session.execute(select(cases).where(cases.c.id == case_id)).mappings().one_or_none()
        if row is None:
            raise TargetNotFound("support case not found")
        return _support_case_view(row)

    def get_case_for_operator(
        self, session: Session, *, actor: VerifiedActor, case_id: UUID
    ) -> SupportCaseView:
        self._require_operator(actor)
        return self.get_case(session, case_id)

    def list_internal_notes(
        self, session: Session, *, actor: VerifiedActor, case_id: UUID
    ) -> tuple[dict[str, Any], ...]:
        self._require_operator(actor)
        notes = _table(session, "support_case_notes")
        return tuple(dict(row) for row in session.execute(
            select(notes).where(notes.c.case_id == case_id).order_by(notes.c.created_at)
        ).mappings())

    def list_events(
        self, session: Session, *, actor: VerifiedActor, case_id: UUID
    ) -> tuple[dict[str, Any], ...]:
        self._require_operator(actor)
        events = _table(session, "support_case_events")
        return tuple(dict(row) for row in session.execute(
            select(events).where(events.c.case_id == case_id).order_by(events.c.created_at)
        ).mappings())

    def list_cases(
        self, session: Session, *, actor: VerifiedActor, account_id: UUID | None = None,
        limit: int = 100
    ) -> tuple[SupportCaseView, ...]:
        self._require_operator(actor)
        cases = _table(session, "support_cases")
        statement = select(cases).order_by(cases.c.updated_at.desc()).limit(min(max(limit, 1), 100))
        if account_id is not None:
            statement = statement.where(cases.c.account_id == account_id)
        return tuple(_support_case_view(row) for row in session.execute(statement).mappings())

    @staticmethod
    def _require_operator(actor: VerifiedActor) -> None:
        if not actor.verified or actor.role not in {"ADMIN", "SUPPORT"}:
            raise AuthorizationDenied("verified operator authority required")

    def safe_account_summary(
        self, session: Session, *, actor: VerifiedActor, account_id: UUID
    ) -> dict[str, Any]:
        self._require_operator(actor)
        return {
            "account": self.identity.account_summary(session, actor=actor, target=account_id),
            "entitlements": self.entitlements.safe_summary(session, actor=actor, target=account_id),
            "beacons": self.beacon.safe_summary(session, actor=actor, target=account_id),
            "scan": self.scan.safe_summary(session, actor=actor, target=account_id),
            "notifications": self.notification.safe_diagnostics(
                session, actor=actor, target=account_id
            ),
            "redacted": True,
        }

    def execute_role_action(
        self,
        session: Session,
        *,
        actor: VerifiedActor,
        case_id: UUID,
        target: UUID,
        action: str,
        reason: str,
        idempotency_key: str,
    ) -> MutationResult:
        return self._delegated(
            session,
            actor=actor,
            case_id=case_id,
            target=target,
            action=action,
            reason=reason,
            key=idempotency_key,
            port=self.identity.execute_role_action,
            owner_kind="role",
        )

    def execute_access_action(
        self,
        session: Session,
        *,
        actor: VerifiedActor,
        case_id: UUID,
        target: UUID,
        action: str,
        reason: str,
        idempotency_key: str,
    ) -> MutationResult:
        return self._delegated(
            session,
            actor=actor,
            case_id=case_id,
            target=target,
            action=action,
            reason=reason,
            key=idempotency_key,
            port=self.entitlements.execute_access_action,
            owner_kind="access",
        )

    def execute_tariff_action(
        self, session: Session, *, actor: VerifiedActor, case_id: UUID, target: UUID,
        action: str, reason: str, idempotency_key: str
    ) -> MutationResult:
        return self._delegated(
            session, actor=actor, case_id=case_id, target=target, action=action,
            reason=reason, key=idempotency_key, port=self.entitlements.execute_tariff_action,
            owner_kind="tariff",
        )

    def execute_beacon_support_patch(
        self, session: Session, *, actor: VerifiedActor, case_id: UUID, target: UUID,
        target_account_id: UUID,
        patch: dict[str, Any], expected_row_version: int, reason: str,
        idempotency_key: str, correlation_id: str,
    ) -> MutationResult:
        """Typed RF20 command carrying Beacon owner preconditions."""
        self._require_operator(actor)
        case = self.get_case(session, case_id)
        if target_account_id != case.account_id:
            raise TargetNotFound("Beacon target must match support-case account")
        action = "PATCH_CURRENT_CONFIGURATION"
        fingerprint = _fingerprint(
            action,
            {"actor": str(actor.actor_account_id), "target": str(target),
             "account": str(target_account_id), "patch": patch,
             "expected_row_version": expected_row_version, "reason": reason.strip()},
        )
        now = self._now()
        correlation = _command_correlation(correlation_id)
        causation = f"{action}:{idempotency_key}"
        self._lock_idempotency(session, idempotency_key)
        decision = self._idempotency.evaluate(
            session, scope=self.IDEMPOTENCY_SCOPE, key=IdempotencyKey(value=idempotency_key),
            fingerprint=fingerprint, now=now,
        )
        if decision.decision is IdempotencyDecision.MISMATCH:
            raise IdempotencyConflict("idempotency fingerprint conflict")
        if decision.outcome is not None:
            return self._decode_replay(decision.outcome)
        outcome = self.beacon.execute_support_patch(
            session, actor=actor, target=target, target_account_id=target_account_id,
            patch=patch, expected_row_version=expected_row_version, reason=reason,
            idempotency_key=idempotency_key, correlation_id=correlation,
        )
        result = outcome if isinstance(outcome, MutationResult) else MutationResult(
            action="PATCH_CURRENT_CONFIGURATION", state=outcome.outcome_class,
            target=str(target), owning_module=outcome.owner,
            outcome_reference=outcome.outcome_reference,
        )
        self._record_event(
            session, case_id=case_id, actor=actor, action=action, reason=reason,
            key=idempotency_key, fingerprint=fingerprint.value, owner=outcome.owner,
            outcome=outcome,
            metadata={"domain_target": str(target), "target_account": str(target_account_id)},
            created_at=now, correlation_id=correlation, causation_id=causation,
        )
        self._idempotency.record_terminal(
            session, record_id=uuid4(), scope=self.IDEMPOTENCY_SCOPE,
            key=IdempotencyKey(value=idempotency_key), fingerprint=fingerprint,
            outcome=self._common(result), created_at=now,
            expires_at=now + timedelta(days=14), now=now,
        )
        return result

    def execute_anchor_action(
        self,
        session: Session,
        *,
        actor: VerifiedActor,
        case_id: UUID,
        target: UUID,
        action: str,
        reason: str,
        idempotency_key: str,
    ) -> MutationResult:
        return self._delegated(
            session,
            actor=actor,
            case_id=case_id,
            target=target,
            action=action,
            reason=reason,
            key=idempotency_key,
            port=self.scan.execute_anchor_action,
            owner_kind="anchor",
        )

    def notification_diagnostics(
        self, session: Session, *, actor: VerifiedActor, account_id: UUID
    ) -> dict[str, Any]:
        """Read notification history through the injected owner adapter."""
        self._require_operator(actor)
        return self.notification.safe_diagnostics(session, actor=actor, target=account_id)

    def _delegated(
        self,
        session: Session,
        *,
        actor: VerifiedActor,
        case_id: UUID,
        target: UUID,
        action: str,
        reason: str,
        key: str,
        port: Any,
        owner_kind: str,
        correlation_id: str | None = None,
    ) -> MutationResult:
        self._require_operator(actor)
        case = self.get_case(session, case_id)
        allowed = {
            "role": ROLE_ACTIONS, "tariff": TARIFF_ACTIONS, "access": ACCESS_ACTIONS,
            "beacon": BEACON_ACTIONS, "anchor": ANCHOR_ACTIONS,
        }.get(owner_kind)
        fingerprint = _fingerprint(
            action,
            {
                "actor": str(actor.actor_account_id),
                "target": str(target),
                "case": str(case_id),
                "reason": reason.strip(),
            },
        )
        now = self._now()
        correlation = _command_correlation(correlation_id)
        causation = f"{action}:{key}"
        self._lock_idempotency(session, key)
        decision = self._idempotency.evaluate(
            session,
            scope=self.IDEMPOTENCY_SCOPE,
            key=IdempotencyKey(value=key),
            fingerprint=fingerprint,
            now=now,
        )
        if decision.decision is IdempotencyDecision.MISMATCH:
            raise IdempotencyConflict("idempotency fingerprint conflict")
        if decision.outcome is not None:
            return self._decode_replay(decision.outcome)
        if allowed is None or action not in allowed:
            outcome = OwningOutcome(
                "admin_and_support", "unsupported-action", OutcomeClass.POLICY_BLOCKED,
            )
        elif (
            owner_kind in {"role", "tariff"}
            or (owner_kind == "access" and action == "GRANT_ACCESS")
        ) and target != case.account_id:
            outcome = OwningOutcome(
                "admin_and_support", "case-target-mismatch", OutcomeClass.POLICY_BLOCKED,
            )
        else:
            arguments = {
                "session": session, "actor": actor, "target": target, "action": action,
                "reason": reason, "idempotency_key": key,
            }
            if owner_kind == "role":
                arguments["correlation_id"] = correlation
            if owner_kind in {"tariff", "access"}:
                arguments["target_account_id"] = case.account_id
            with correlation_context_scope(
                CorrelationContext(correlation_id=CorrelationId(value=correlation))
            ):
                outcome = port(**arguments)
        result = self._record_event(
            session,
            case_id=case_id,
            actor=actor,
            action=action,
            reason=reason,
            key=key,
            fingerprint=fingerprint.value,
            owner=outcome.owner,
            outcome=outcome,
            metadata={"domain_target": str(target)},
            created_at=now,
            correlation_id=correlation,
            causation_id=causation,
        )
        self._idempotency.record_terminal(
            session,
            record_id=uuid4(),
            scope=self.IDEMPOTENCY_SCOPE,
            key=IdempotencyKey(value=key),
            fingerprint=fingerprint,
            outcome=self._common(result),
            created_at=now,
            expires_at=now + timedelta(days=14),
            now=now,
        )
        return result

    def _case_mutation(
        self,
        session: Session,
        *,
        actor: VerifiedActor,
        account_id: UUID,
        action: str,
        reason: str,
        key: str,
        values: dict[str, Any],
        operation: Any,
        correlation_id: str | None,
    ) -> MutationResult:
        fp = _fingerprint(
            action,
            {
                "actor": str(actor.actor_account_id),
                "target": str(account_id),
                "reason": reason.strip(),
                **values,
            },
        )
        now = self._now()
        correlation = _command_correlation(correlation_id)
        causation = f"{action}:{key}"
        self._lock_idempotency(session, key)
        decision = self._idempotency.evaluate(
            session,
            scope=self.IDEMPOTENCY_SCOPE,
            key=IdempotencyKey(value=key),
            fingerprint=fp,
            now=now,
        )
        if decision.decision is IdempotencyDecision.MISMATCH:
            raise IdempotencyConflict("idempotency fingerprint conflict")
        if decision.outcome is not None:
            return self._decode_replay(decision.outcome)
        case_id = operation(uuid4(), now)
        result = MutationResult(
            action=action,
            state=OutcomeClass.SUCCEEDED,
            target=str(account_id),
            owning_module="admin_and_support",
            outcome_reference=str(case_id),
        )
        self._record_event(
            session,
            case_id=case_id,
            actor=actor,
            action=action,
            reason=reason,
            key=key,
            fingerprint=fp.value,
            metadata=values,
            owner="admin_and_support",
            outcome=OwningOutcome("admin_and_support", str(case_id), OutcomeClass.SUCCEEDED),
            created_at=now,
            correlation_id=correlation,
            causation_id=causation,
        )
        self._idempotency.record_terminal(
            session,
            record_id=uuid4(),
            scope=self.IDEMPOTENCY_SCOPE,
            key=IdempotencyKey(value=key),
            fingerprint=fp,
            outcome=self._common(result),
            created_at=now,
            expires_at=now + timedelta(days=14),
            now=now,
        )
        return result

    def _insert_case(
        self,
        session: Session,
        case_id: UUID,
        actor: VerifiedActor,
        account_id: UUID,
        subject: str,
        now: datetime,
    ) -> UUID:
        cases = _table(session, "support_cases")
        session.execute(
            cases.insert().values(
                id=case_id,
                account_id=account_id,
                opened_by_account_id=actor.actor_account_id,
                assigned_to_account_id=None,
                state=SupportCaseState.OPEN.value,
                subject=subject.strip(),
                created_at=now,
                updated_at=now,
                row_version=1,
            )
        )
        return case_id

    def _update_case(
        self, session: Session, case_id: UUID, state: str, expected: int, now: datetime
    ) -> UUID:
        cases = _table(session, "support_cases")
        changed = cast(CursorResult[Any], session.execute(
            update(cases)
            .where(cases.c.id == case_id, cases.c.row_version == expected)
            .values(state=state, updated_at=now, row_version=expected + 1)
        )).rowcount
        if changed != 1:
            raise StaleCase("support case row version changed")
        return case_id

    def _assign_case(
        self, session: Session, case_id: UUID, assignee: UUID, now: datetime
    ) -> UUID:
        cases = _table(session, "support_cases")
        changed = cast(CursorResult[Any], session.execute(
            update(cases)
            .where(cases.c.id == case_id)
            .values(
                assigned_to_account_id=assignee,
                updated_at=now,
                row_version=cases.c.row_version + 1,
            )
        )).rowcount
        if changed != 1:
            raise TargetNotFound("support case not found")
        return case_id

    def _insert_note(
        self, session: Session, case_id: UUID, actor: VerifiedActor, body: str, now: datetime
    ) -> UUID:
        notes = _table(session, "support_case_notes")
        note_id = uuid4()
        session.execute(
            notes.insert().values(
                id=note_id,
                case_id=case_id,
                author_account_id=actor.actor_account_id,
                visibility="INTERNAL",
                body=body,
                created_at=now,
            )
        )
        return case_id

    def _record_event(
        self,
        session: Session,
        *,
        case_id: UUID,
        actor: VerifiedActor,
        action: str,
        reason: str,
        key: str,
        fingerprint: str,
        owner: str,
        outcome: OwningOutcome,
        metadata: dict[str, Any] | None = None,
        created_at: datetime | None = None,
        correlation_id: str | None = None,
        causation_id: str | None = None,
    ) -> MutationResult:
        events = _table(session, "support_case_events")
        event_id = uuid4()
        factual_created_at = created_at or self._now()
        if factual_created_at.tzinfo is None or factual_created_at.utcoffset() is None:
            raise ValueError("support event timestamp must be timezone-aware")
        session.execute(
            events.insert().values(
                id=event_id,
                case_id=case_id,
                actor_account_id=actor.actor_account_id,
                event_code=action,
                reason=reason.strip(),
                details={
                    "idempotency_key": key,
                    "fingerprint": fingerprint,
                    "owning_module": owner,
                    "outcome_reference": outcome.outcome_reference,
                    "outcome_class": outcome.outcome_class.value,
                    "correlation_id": correlation_id or _command_correlation(None),
                    "causation_id": causation_id or f"{action}:{key}",
                    "audit_result": "RECORDED",
                    **{
                        key: value for key, value in (metadata or {}).items()
                        if key not in {"body", "raw_provider_payload", "token", "password"}
                    },
                },
                created_at=factual_created_at,
            )
        )
        return MutationResult(
            action=action,
            state=outcome.outcome_class,
            target=str(case_id),
            owning_module=owner,
            outcome_reference=outcome.outcome_reference,
            event_id=event_id,
        )

    @staticmethod
    def _common(result: MutationResult) -> CommonOutcome:
        result_code = {
            OutcomeClass.SUCCEEDED: Result.SUCCEEDED,
            OutcomeClass.REPLAYED: Result.SUCCEEDED,
            OutcomeClass.REJECTED: Result.REJECTED,
            OutcomeClass.CONFLICT: Result.CONFLICT,
            OutcomeClass.POLICY_BLOCKED: Result.REJECTED,
            OutcomeClass.AMBIGUOUS: Result.AMBIGUOUS,
            OutcomeClass.RECONCILIATION_REQUIRED: Result.AMBIGUOUS,
        }.get(result.state, Result.REJECTED)
        return CommonOutcome(
            result=result_code,
            reason_code="RF20_SUPPORT_MUTATION",
            details=(
                json.dumps(
                    {
                        "action": result.action,
                        "state": result.state.value,
                        "target": result.target,
                        "owning_module": result.owning_module,
                        "outcome_reference": result.outcome_reference,
                    },
                    sort_keys=True,
                ),
            ),
        )

    @staticmethod
    def _decode_replay(outcome: CommonOutcome) -> MutationResult:
        if outcome.reason_code != "RF20_SUPPORT_MUTATION" or len(outcome.details) != 1:
            raise ReconciliationRequired("stored support outcome is invalid")
        data = json.loads(outcome.details[0])
        terminal = OutcomeClass(data["state"])
        return MutationResult(
            action=data["action"],
            state=terminal,
            target=data["target"],
            owning_module=data["owning_module"],
            outcome_reference=data["outcome_reference"],
            replayed=True,
        )


__all__ = [
    "AuthorizationDenied",
    "BeaconPort",
    "EntitlementsPort",
    "IdentityPort",
    "NotificationPort",
    "OutcomeClass",
    "OwningOutcome",
    "ReconciliationRequired",
    "ScanPort",
    "StaleCase",
    "SupportCaseView",
    "SupportRuntime",
    "TargetNotFound",
    "VerifiedActor",
]
