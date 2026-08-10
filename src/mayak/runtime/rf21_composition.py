"""RF21 composition boundary for public owner runtimes.

Only this module imports owner runtimes.  Adapters intentionally return safe,
redacted values and never expose ORM rows or provider material to Web.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from mayak.modules.beacon_management.runtime import (
    BeaconManagementRuntime,
    BeaconRuntimeError,
    ConflictError,
    ResolvedActor,
)
from mayak.modules.entitlements_and_billing.runtime import EntitlementsBillingRuntime
from mayak.modules.identity_and_access.runtime import IdentityRuntime
from mayak.modules.max_adapter.runtime import max_readiness
from mayak.modules.notification_delivery.runtime import read_history
from mayak.modules.scan_orchestration.read_models import current_listing_state, recent_runs
from mayak.modules.telegram_adapter.runtime import telegram_readiness
from mayak.modules.web_cabinet.beacon_commands import WebBeaconCommandKind
from mayak.modules.web_cabinet.runtime import (
    VerifiedWebCustomer,
    WebConflictError,
    WebRuntimeState,
    WebSection,
)


class IdentityWebAdapter:
    owner = "identity_and_access"
    key = "account"

    def __init__(self, runtime: IdentityRuntime) -> None:
        self.runtime = runtime
        self.calls = 0

    def resolve_session(self, session: Any, session_reference: Any) -> VerifiedWebCustomer | None:
        self.calls += 1
        try:
            resolver = getattr(self.runtime, "validate_session_reference", None)
            if resolver is None:
                resolver = self.runtime.validate_session
            result = resolver(session, session_reference)
        except (TypeError, ValueError):
            return None
        if result.account_id is None or result.metadata is None:
            return None
        return VerifiedWebCustomer(
            result.account_id,
            result.metadata.session_id,
            f"identity-session:{result.metadata.session_id}",
            authority_context=session_reference,
        )

    def account_summary(self, session: Any, customer: VerifiedWebCustomer) -> dict[str, str]:
        self.calls += 1
        reader = getattr(self.runtime, "safe_account_summary", None)
        if reader is None:
            return {"account_id": str(customer.account_id), "state": "UNKNOWN", "owner": self.owner}
        return reader(session, customer.account_id)


class CustomerIdentityAuthorityAdapter:
    """Customer authority bridge retaining the opaque Identity credential."""

    def __init__(self, runtime: IdentityRuntime) -> None:
        self.runtime = runtime

    def resolve(
        self, session: Any, *, actor_reference: Any, requested_account_id: UUID | None
    ) -> ResolvedActor:
        resolver = getattr(self.runtime, "validate_session_reference", None)
        if resolver is None:
            resolver = self.runtime.validate_session
        validation = resolver(session, actor_reference)
        if validation.account_id is None or validation.metadata is None:
            raise PermissionError("active Identity session required")
        if requested_account_id is not None and requested_account_id != validation.account_id:
            raise PermissionError("Identity account scope mismatch")
        return ResolvedActor(
            actor_id=validation.account_id,
            account_id=validation.account_id,
            verified=True,
            reference=f"identity-session:{validation.metadata.session_id}",
        )


@dataclass(frozen=True, slots=True)
class WebBeaconProjection:
    """Owner-read Beacon view plus the safe current filter projection."""

    view: Any
    current_filter_values: tuple[str, ...]

    def __getattr__(self, name: str) -> Any:
        return getattr(self.view, name)


class BeaconWebAdapter:
    owner = "beacon_management"
    key = "beacons"

    def __init__(self, runtime: BeaconManagementRuntime) -> None:
        self.runtime = runtime
        self.calls = 0

    def read(self, session: Any, customer: VerifiedWebCustomer) -> tuple[Any, ...]:
        self.calls += 1
        authority = (
            customer.authority_context
            if customer.authority_context is not None
            else customer.authority_reference
        )
        views = self.runtime.list(session, actor_reference=authority)
        projected: list[Any] = []
        for view in views:
            get_revision = getattr(self.runtime, "get_revision", None)
            revision_no = getattr(view, "current_revision_no", None)
            if not callable(get_revision) or revision_no is None:
                projected.append(view)
                continue
            revision = get_revision(
                session,
                actor_reference=authority,
                beacon_id=view.beacon_id,
                revision_no=revision_no,
            )
            values = revision.accepted_filter.get("normalized_filter_values", ())
            projected.append(
                WebBeaconProjection(
                    view=view,
                    current_filter_values=tuple(str(value) for value in values),
                )
            )
        return tuple(projected)

    def detail(
        self, session: Any, customer: VerifiedWebCustomer, beacon_id: UUID
    ) -> dict[str, Any]:
        self.calls += 1
        authority = (
            customer.authority_context
            if customer.authority_context is not None
            else customer.authority_reference
        )
        try:
            view = self.runtime.get(session, actor_reference=authority, beacon_id=beacon_id)
            history = self.runtime.history(session, actor_reference=authority, beacon_id=beacon_id)
        except ConflictError as exc:
            raise WebConflictError("Beacon command conflict") from exc
        except BeaconRuntimeError as exc:
            raise PermissionError("Beacon is unavailable for this customer") from exc
        return {"beacon": view, "history": history, "owner": self.owner}

    def command(
        self,
        session: Any,
        customer: VerifiedWebCustomer,
        *,
        beacon_id: UUID,
        action: WebBeaconCommandKind,
        expected_row_version: int,
        idempotency_key: str,
        patch: dict[str, Any] | None = None,
    ) -> Any:
        self.calls += 1
        try:
            action = WebBeaconCommandKind(action)
        except ValueError as exc:
            raise ValueError("unsupported Web Beacon command") from exc
        args = dict(
            session=session,
            actor_reference=customer.authority_context,
            beacon_id=beacon_id,
            idempotency_key=idempotency_key,
            expected_row_version=expected_row_version,
        )
        if action is WebBeaconCommandKind.PATCH_CURRENT_CONFIGURATION:
            if not patch:
                raise ValueError("patch required")
            args.update(patch=patch, strict_expected_row_version=True)
            try:
                return self.runtime.patch(**args)
            except ConflictError as exc:
                raise WebConflictError("Beacon command conflict") from exc
            except BeaconRuntimeError as exc:
                raise PermissionError("Beacon command is unavailable for this customer") from exc
        methods = {
            WebBeaconCommandKind.ARCHIVE_TO_HISTORY: "archive",
            WebBeaconCommandKind.RESTORE_FROM_HISTORY: "restore",
            WebBeaconCommandKind.DELETE_TO_HISTORY: "user_delete",
            WebBeaconCommandKind.PERMANENT_DELETE: "permanent_delete",
        }
        method = methods.get(action)
        if method is None:
            raise ValueError("unsupported Web Beacon command")
        try:
            return getattr(self.runtime, method)(**args)
        except ConflictError as exc:
            raise WebConflictError("Beacon command conflict") from exc
        except BeaconRuntimeError as exc:
            raise PermissionError("Beacon command is unavailable for this customer") from exc


class EntitlementWebAdapter:
    owner = "entitlements_and_billing"
    key = "entitlements"

    def __init__(self, runtime: EntitlementsBillingRuntime) -> None:
        self.runtime = runtime
        self.calls = 0

    def read(self, session: Any, customer: VerifiedWebCustomer) -> Any:
        self.calls += 1
        return self.runtime.evaluate_effective(session, customer.account_id, at=datetime.now(UTC))


class NotificationWebAdapter:
    owner = "notification_delivery"
    key = "notifications"

    def __init__(self, runtime: Any = read_history) -> None:
        self.runtime = runtime
        self.calls = 0

    def read(self, session: Any, customer: VerifiedWebCustomer) -> Any:
        self.calls += 1
        return self.runtime(
            session, account_id=customer.account_id, actor_account_id=customer.account_id, limit=20
        )


class ScanWebAdapter:
    owner = "scan_orchestration"
    key = "scan"

    def __init__(self, beacon: BeaconWebAdapter) -> None:
        self.beacon = beacon
        self.calls = 0

    def read(self, session: Any, customer: VerifiedWebCustomer) -> dict[str, Any]:
        self.calls += 1
        return {
            "owner": self.owner,
            "beacons": [
                {
                    "beacon_id": str(view.beacon_id),
                    "recent_runs": recent_runs(session, view.beacon_id),
                    "listing_state": current_listing_state(session, view.beacon_id),
                }
                for view in self.beacon.read(session, customer)
            ],
        }


class TelegramWebAdapter:
    owner = "telegram_adapter"
    key = "telegram"

    def __init__(self, settings: Any) -> None:
        self.settings, self.calls = settings, 0

    def read(self, session: Any, customer: VerifiedWebCustomer) -> dict[str, Any]:
        self.calls += 1
        result = telegram_readiness(self.settings, credential_present=False)
        return {"owner": self.owner, "state": result.state, "enabled": result.enabled}


class MaxWebAdapter:
    owner = "max_adapter"
    key = "max"

    def __init__(self, settings: Any) -> None:
        self.settings, self.calls = settings, 0

    def read(self, session: Any, customer: VerifiedWebCustomer) -> dict[str, Any]:
        self.calls += 1
        result = max_readiness(self.settings, credential_present=False)
        return {"owner": self.owner, "state": result.state, "enabled": result.enabled}


class SupportWebAdapter:
    owner = "admin_and_support"
    key = "support"

    def __init__(self, runtime: Any) -> None:
        self.runtime, self.calls = runtime, 0

    def read(self, session: Any, customer: VerifiedWebCustomer) -> Any:
        self.calls += 1
        return self.runtime.customer_visible_summary(session, customer.account_id)


@dataclass(slots=True)
class SafeUnavailableAdapter:
    owner: str
    key: str
    reason: str = "provider disabled or projection unavailable"

    def read(self, session: Any, customer: VerifiedWebCustomer) -> WebSection:
        return WebSection(
            self.key,
            WebRuntimeState.UNKNOWN,
            self.owner,
            message=self.reason,
            provenance=(self.owner,),
        )


def build_rf21_runtime(
    *,
    identity: IdentityRuntime,
    beacon: BeaconManagementRuntime,
    entitlements: EntitlementsBillingRuntime,
    notification: Any = read_history,
    scan: Any | None = None,
    telegram: Any | None = None,
    max_adapter: Any | None = None,
    support: Any | None = None,
    settings: Any | None = None,
) -> Any:
    from mayak.modules.web_cabinet.runtime import WebCabinetRuntime

    identity_adapter = IdentityWebAdapter(identity)
    beacon_adapter = BeaconWebAdapter(beacon)
    effective_settings = settings or getattr(identity, "settings", None)
    projections: list[Any] = [
        EntitlementWebAdapter(entitlements),
        NotificationWebAdapter(notification),
        scan or ScanWebAdapter(beacon_adapter),
    ]
    if effective_settings is not None:
        projections.extend(
            (
                telegram or TelegramWebAdapter(effective_settings),
                max_adapter or MaxWebAdapter(effective_settings),
            )
        )
    else:
        projections.extend(
            (
                telegram or SafeUnavailableAdapter("telegram_adapter", "telegram"),
                max_adapter or SafeUnavailableAdapter("max_adapter", "max"),
            )
        )
    projections.append(
        SupportWebAdapter(support)
        if support is not None and not hasattr(support, "read")
        else support or SafeUnavailableAdapter("admin_and_support", "support")
    )
    return WebCabinetRuntime(
        identity=identity_adapter,
        account=identity_adapter,
        beacon=beacon_adapter,
        projections=tuple(projections),
    )


__all__ = [
    "IdentityWebAdapter",
    "BeaconWebAdapter",
    "EntitlementWebAdapter",
    "CustomerIdentityAuthorityAdapter",
    "WebBeaconProjection",
    "NotificationWebAdapter",
    "ScanWebAdapter",
    "TelegramWebAdapter",
    "MaxWebAdapter",
    "SupportWebAdapter",
    "SafeUnavailableAdapter",
    "build_rf21_runtime",
]
