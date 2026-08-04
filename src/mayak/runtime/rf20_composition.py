"""RF20 production composition adapters.

Only this composition boundary translates the persisted Identity session into
the internal SupportRuntime actor context.  HTTP form values are intentionally
not accepted by this adapter.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from mayak.contracts.idempotency import IdempotencyKey
from mayak.modules.admin_and_support.runtime import (
    AuthorizationDenied,
    OutcomeClass,
    OwningOutcome,
    VerifiedActor,
)
from mayak.modules.beacon_management.runtime import (
    BeaconManagementRuntime,
    BeaconRuntimeError,
    ConflictError,
    ResolvedActor,
    VerifiedSupportAuthority,
)
from mayak.modules.entitlements_and_billing.contracts import TariffName
from mayak.modules.entitlements_and_billing.runtime import (
    AuthorityFacts,
    EntitlementsBillingRuntime,
    RuntimeState,
)
from mayak.modules.identity_and_access.contracts import RoleMutationRequest
from mayak.modules.identity_and_access.runtime import IdentityRuntime
from mayak.modules.notification_delivery.runtime import read_history
from mayak.persistence.metadata import metadata
from mayak.platform.correlation import CorrelationContext, CorrelationId

if TYPE_CHECKING:
    from mayak.modules.admin_and_support.runtime import SupportRuntime

_ACCOUNTS = metadata.tables["mayak.identity_accounts"]
_ROLES = metadata.tables["mayak.identity_role_assignments"]


class IdentityAuthorityAdapter:
    """Resolve RF20 authority from an active persisted Identity session."""

    def __init__(self, identity: IdentityRuntime) -> None:
        self.identity = identity
        self.calls = 0
        self.foreign_denials = 0

    def verify_operator(self, session: Session, session_reference: Any) -> VerifiedActor:
        self.calls += 1
        validation = self.identity.validate_session(session, session_reference)
        account_id = validation.account_id
        if account_id is None:
            raise AuthorizationDenied("active Identity session required")
        roles = self._roles(session, account_id)
        role = "ADMIN" if "ADMIN" in roles else "SUPPORT" if "SUPPORT" in roles else None
        if role is None:
            raise AuthorizationDenied("operator role required")
        if validation.metadata is None:
            raise AuthorizationDenied("session metadata unavailable")
        return VerifiedActor(
            actor_account_id=account_id,
            role=role,
            authorization_scope=f"identity:{role.lower()}",
            authorization_reference=f"identity-session:{validation.metadata.session_id}",
            identity_session_reference=session_reference,
        )

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
    ) -> Any:
        self.calls += 1
        token = actor.identity_session_reference
        if token is None:
            raise AuthorizationDenied("production Identity session reference required")
        role = {
            "ASSIGN_SUPPORT": "SUPPORT",
            "ASSIGN_ADMIN": "ADMIN",
            "REVOKE_SUPPORT": "SUPPORT",
            "REVOKE_ADMIN": "ADMIN",
        }.get(action)
        if role is None:
            raise AuthorizationDenied("unsupported Identity role action")
        state = self.identity.mutate_role(
            session,
            RoleMutationRequest(
                session_id=UUID(actor.authorization_reference.split(":", 1)[1]),
                target_account_id=target,
                role_code=role,
                reason=reason,
                idempotency_key=IdempotencyKey(value=idempotency_key),
                correlation=CorrelationContext(
                    correlation_id=CorrelationId(value=correlation_id or str(uuid4()))
                ),
            ),
            token,
            revoke=action.startswith("REVOKE_"),
        )
        state_name = getattr(state, "value", str(state))
        terminal = (
            OutcomeClass.SUCCEEDED
            if state_name in {"ASSIGNED", "REVOKED", "UNCHANGED"}
            else OutcomeClass.REJECTED
        )
        return OwningOutcome(
            "identity_and_access", f"identity-role:{target}:{role}", terminal, state_name
        )

    def authority(self, session: Session, actor_reference: Any, target: UUID) -> AuthorityFacts:
        actor = self.verify_operator(session, actor_reference)
        target_state = session.execute(
            select(_ACCOUNTS.c.state).where(_ACCOUNTS.c.id == target)
        ).scalar_one_or_none()
        if target_state != "ACTIVE":
            raise PermissionError("target account unavailable")
        capabilities = (
            frozenset({
                "ENTITLEMENTS_TARIFF_ADMIN",
                "ENTITLEMENTS_TARIFF_ASSIGN_ADMIN",
                "ENTITLEMENTS_MANUAL_ACCESS_ADMIN",
            }) if actor.role == "ADMIN" else frozenset()
        )
        return AuthorityFacts(
            actor_id=actor.actor_account_id,
            account_id=target,
            capabilities=capabilities,
            scope=actor.authorization_scope,
            authorization_reference=actor.authorization_reference,
            audit_reference=actor.authorization_reference,
        )

    def resolve(
        self, session: Session, *, actor_reference: Any, requested_account_id: UUID | None
    ) -> ResolvedActor:
        actor = self.verify_operator(session, actor_reference)
        if requested_account_id is not None and requested_account_id != actor.actor_account_id:
            raise AuthorizationDenied("identity account scope mismatch")
        return ResolvedActor(
            actor_id=actor.actor_account_id,
            account_id=actor.actor_account_id,
            verified=True,
            reference=actor.authorization_reference,
        )

    def operator_exists(
        self, session: Session, *, actor: VerifiedActor, target: UUID
    ) -> bool:
        self.calls += 1
        return bool(self._roles(session, target) & {"ADMIN", "SUPPORT"})

    def account_summary(
        self, session: Session, *, actor: VerifiedActor, target: UUID
    ) -> dict[str, Any]:
        self.calls += 1
        row = session.execute(
            select(_ACCOUNTS.c.id, _ACCOUNTS.c.state).where(_ACCOUNTS.c.id == target)
        ).mappings().one_or_none()
        if row is None:
            raise AuthorizationDenied("account unavailable")
        return {
            "account_id": str(row["id"]),
            "state": row["state"],
            "roles": sorted(self._roles(session, target)),
            "redacted": True,
        }

    @staticmethod
    def _roles(session: Session, account_id: UUID) -> set[str]:
        return set(
            session.execute(
                select(_ROLES.c.role_code).where(
                    _ROLES.c.account_id == account_id,
                    _ROLES.c.revoked_at.is_(None),
                )
            ).scalars()
        )


class BeaconSupportAdapter:
    """Typed RF20 bridge to the actual Beacon owner runtime."""

    owner = "beacon_management"

    def __init__(self, runtime: BeaconManagementRuntime) -> None:
        self.runtime = runtime
        self.calls = 0
        self.foreign_denials = 0

    def execute_support_patch(
        self, session: Session, *, actor: VerifiedActor, target: UUID,
        target_account_id: UUID, patch: dict[str, Any], expected_row_version: int,
        reason: str, idempotency_key: str, correlation_id: str,
    ) -> OwningOutcome:
        if not patch or "source_url" in patch:
            return OwningOutcome(self.owner, "beacon-policy", OutcomeClass.POLICY_BLOCKED)
        self.calls += 1
        try:
            result = self.runtime.patch_current_configuration_for_support(
                session,
                authority=VerifiedSupportAuthority(
                    operator_account_id=actor.actor_account_id,
                    target_account_id=target_account_id,
                    reference=actor.authorization_reference,
                ),
                beacon_id=target, patch=patch, expected_row_version=expected_row_version,
                idempotency_key=idempotency_key, reason=reason,
                correlation=CorrelationContext(correlation_id=CorrelationId(value=correlation_id)),
            )
        except ConflictError:
            return OwningOutcome(self.owner, "stale-beacon", OutcomeClass.CONFLICT)
        except BeaconRuntimeError:
            self.foreign_denials += 1
            return OwningOutcome(self.owner, "beacon-policy", OutcomeClass.POLICY_BLOCKED)
        return OwningOutcome(self.owner, str(result.beacon_id), OutcomeClass.SUCCEEDED)

    def safe_summary(
        self, session: Session, *, actor: VerifiedActor, target: UUID
    ) -> dict[str, Any]:
        self.calls += 1
        return self.runtime.safe_summary_for_support(
            session,
            authority=VerifiedSupportAuthority(
                operator_account_id=actor.actor_account_id,
                target_account_id=target,
                reference=actor.authorization_reference,
            ),
        )


class EntitlementsSupportAdapter:
    """RF20 mapping to the current Entitlements public runtime commands."""

    def __init__(self, owner: EntitlementsBillingRuntime) -> None:
        self.owner = owner
        self.calls = 0

    def execute_tariff_action(
        self, session: Session, *, actor: VerifiedActor, target: UUID, action: str,
        reason: str, idempotency_key: str, target_account_id: UUID,
    ) -> OwningOutcome:
        self.calls += 1
        token = actor.identity_session_reference
        if action != "ASSIGN_BASIC" or token is None:
            return OwningOutcome(
                "entitlements_and_billing", "tariff-policy", OutcomeClass.POLICY_BLOCKED
            )
        now = datetime.now(UTC)
        result = self.owner.assign_access(
            session, token, tariff=TariffName.BASIC, starts_at=now,
            ends_at=now + timedelta(days=30), reason=reason,
            idempotency_key=idempotency_key, target_account_id=target_account_id,
        )
        return self._outcome(result.state, result.resource_id)

    def execute_access_action(
        self, session: Session, *, actor: VerifiedActor, target: UUID, action: str,
        reason: str, idempotency_key: str,
    ) -> OwningOutcome:
        self.calls += 1
        token = actor.identity_session_reference
        if action != "GRANT_ACCESS" or token is None:
            return OwningOutcome(
                "entitlements_and_billing", "access-policy", OutcomeClass.POLICY_BLOCKED
            )
        now = datetime.now(UTC)
        result = self.owner.manual_access_create(
            session, token, starts_at=now, ends_at=now + timedelta(days=30),
            idempotency_key=idempotency_key, reason=reason,
            target_account_id=target,
        )
        return self._outcome(result.state, result.resource_id)

    def safe_summary(
        self, session: Session, *, actor: VerifiedActor, target: UUID
    ) -> dict[str, Any]:
        self.calls += 1
        result = self.owner.evaluate_effective(session, target, at=datetime.now(UTC))
        return {
            "owner": "entitlements_and_billing",
            "status": result.status.value,
            "redacted": True,
        }

    @staticmethod
    def _outcome(state: RuntimeState, reference: UUID | None) -> OwningOutcome:
        mapping = {
            RuntimeState.RECORDED: OutcomeClass.SUCCEEDED,
            RuntimeState.REPLAYED: OutcomeClass.SUCCEEDED,
            RuntimeState.BLOCKED: OutcomeClass.POLICY_BLOCKED,
            RuntimeState.UNAUTHORIZED: OutcomeClass.REJECTED,
            RuntimeState.CONFLICT: OutcomeClass.CONFLICT,
            RuntimeState.MISMATCH: OutcomeClass.CONFLICT,
            RuntimeState.RECONCILE_REQUIRED: OutcomeClass.RECONCILIATION_REQUIRED,
        }
        return OwningOutcome(
            "entitlements_and_billing", str(reference or "owner-outcome"),
            mapping.get(state, OutcomeClass.REJECTED), state.value,
        )


class NotificationDiagnosticsAdapter:
    """Read-only RF20 façade over Notification history."""

    def __init__(self) -> None:
        self.calls = 0

    def safe_diagnostics(
        self, session: Session, *, actor: VerifiedActor, target: UUID
    ) -> dict[str, Any]:
        self.calls += 1
        history = read_history(session, account_id=target, actor_account_id=actor.actor_account_id)
        return {"owner": "notification_delivery", "history_count": len(history), "redacted": True}


class ScanPolicyAdapter:
    """Current Scan public runtime has no destructive RF20 command."""

    def __init__(self) -> None:
        self.calls = 0

    def execute_anchor_action(
        self, session: Session, *, actor: VerifiedActor, target: UUID, action: str,
        reason: str, idempotency_key: str,
    ) -> OwningOutcome:
        self.calls += 1
        return OwningOutcome(
            "scan_orchestration", "scan-anchor-policy", OutcomeClass.POLICY_BLOCKED,
            "safe review/preparation only",
        )

    def safe_summary(
        self, session: Session, *, actor: VerifiedActor, target: UUID
    ) -> dict[str, Any]:
        self.calls += 1
        return {"owner": "scan_orchestration", "state": "SAFE_REVIEW_ONLY", "redacted": True}


@dataclass(frozen=True, slots=True)
class RF20Composition:
    """Production-shaped RF20 owner wiring used by both HTTP and acceptance."""

    identity: IdentityAuthorityAdapter
    entitlements: EntitlementsSupportAdapter
    beacon: BeaconSupportAdapter
    scan: ScanPolicyAdapter
    notification: NotificationDiagnosticsAdapter

    def runtime(self) -> "SupportRuntime":
        from mayak.modules.admin_and_support.runtime import SupportRuntime

        return SupportRuntime(
            identity=self.identity, entitlements=self.entitlements, beacon=self.beacon,
            scan=self.scan, notification=self.notification,
        )


def build_rf20_composition(
    *, identity: IdentityRuntime, entitlements: EntitlementsBillingRuntime,
    beacon: BeaconManagementRuntime,
) -> RF20Composition:
    identity_adapter = IdentityAuthorityAdapter(identity)
    return RF20Composition(
        identity=identity_adapter,
        entitlements=EntitlementsSupportAdapter(entitlements),
        beacon=BeaconSupportAdapter(beacon),
        scan=ScanPolicyAdapter(),
        notification=NotificationDiagnosticsAdapter(),
    )


__all__ = [
    "BeaconSupportAdapter",
    "RF20Composition",
    "build_rf20_composition",
    "EntitlementsSupportAdapter",
    "IdentityAuthorityAdapter",
    "NotificationDiagnosticsAdapter",
    "ScanPolicyAdapter",
]
