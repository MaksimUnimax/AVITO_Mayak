"""RF21 composition boundary for public owner runtimes.

Only this module imports owner runtimes.  Adapters intentionally return safe,
redacted values and never expose ORM rows or provider material to Web.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from mayak.modules.beacon_management.runtime import BeaconManagementRuntime
from mayak.modules.entitlements_and_billing.runtime import EntitlementsBillingRuntime
from mayak.modules.identity_and_access.runtime import IdentityRuntime
from mayak.modules.notification_delivery.runtime import read_history
from mayak.modules.web_cabinet.runtime import VerifiedWebCustomer, WebRuntimeState, WebSection


class IdentityWebAdapter:
    owner = "identity_and_access"
    key = "account"

    def __init__(self, runtime: IdentityRuntime) -> None:
        self.runtime = runtime
        self.calls = 0

    def resolve_session(self, session: Any, session_reference: Any) -> VerifiedWebCustomer | None:
        self.calls += 1
        try:
            result = self.runtime.validate_session(session, session_reference)
        except (TypeError, ValueError):
            return None
        if result.account_id is None or result.metadata is None:
            return None
        return VerifiedWebCustomer(result.account_id, result.metadata.session_id,
                                   f"identity-session:{result.metadata.session_id}")

    def account_summary(self, session: Any, customer: VerifiedWebCustomer) -> dict[str, str]:
        self.calls += 1
        # Identity is the only authority for this identifier; no contact/phone is projected.
        return {"account_id": str(customer.account_id), "state": "ACTIVE", "owner": self.owner}


class BeaconWebAdapter:
    owner = "beacon_management"
    key = "beacons"

    def __init__(self, runtime: BeaconManagementRuntime) -> None:
        self.runtime = runtime
        self.calls = 0

    def read(self, session: Any, customer: VerifiedWebCustomer) -> tuple[Any, ...]:
        self.calls += 1
        return self.runtime.list(session, actor_reference=customer.authority_reference)

    def detail(
        self, session: Any, customer: VerifiedWebCustomer, beacon_id: UUID
    ) -> dict[str, Any]:
        self.calls += 1
        view = self.runtime.get(session, actor_reference=customer.authority_reference,
                                beacon_id=beacon_id)
        history = self.runtime.history(session, actor_reference=customer.authority_reference,
                                       beacon_id=beacon_id)
        return {"beacon": view, "history": history, "owner": self.owner}

    def command(self, session: Any, customer: VerifiedWebCustomer, *, beacon_id: UUID,
                action: str, expected_row_version: int, idempotency_key: str,
                fingerprint: str, patch: dict[str, Any] | None = None) -> Any:
        self.calls += 1
        args = dict(session=session, actor_reference=customer.authority_reference,
                    beacon_id=beacon_id, idempotency_key=idempotency_key,
                    expected_row_version=expected_row_version)
        if action == "PATCH_CURRENT_CONFIGURATION":
            if not patch:
                raise ValueError("patch required")
            args.update(patch=patch)
            return self.runtime.patch(**args)
        methods = {"ARCHIVE_TO_HISTORY": "archive", "RESTORE_FROM_HISTORY": "restore",
                   "DELETE_TO_HISTORY": "user_delete", "PERMANENT_DELETE": "permanent_delete",
                   "PAUSE": "pause", "RESUME": "resume", "ACTIVATE": "activate"}
        method = methods.get(action)
        if method is None:
            raise ValueError("unsupported Beacon command")
        return getattr(self.runtime, method)(**args)


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
        return self.runtime(session, account_id=customer.account_id,
                            actor_account_id=customer.account_id, limit=20)


@dataclass(slots=True)
class SafeUnavailableAdapter:
    owner: str
    key: str
    reason: str = "provider disabled or projection unavailable"

    def read(self, session: Any, customer: VerifiedWebCustomer) -> WebSection:
        return WebSection(self.key, WebRuntimeState.UNKNOWN, self.owner,
                          message=self.reason, provenance=(self.owner,))


def build_rf21_runtime(*, identity: IdentityRuntime, beacon: BeaconManagementRuntime,
                       entitlements: EntitlementsBillingRuntime, notification: Any = read_history,
                       scan: Any | None = None, telegram: Any | None = None,
                       max_adapter: Any | None = None, support: Any | None = None) -> Any:
    from mayak.modules.web_cabinet.runtime import WebCabinetRuntime
    identity_adapter = IdentityWebAdapter(identity)
    return WebCabinetRuntime(
        identity=identity_adapter, account=identity_adapter,
        beacon=BeaconWebAdapter(beacon),
        projections=(EntitlementWebAdapter(entitlements), NotificationWebAdapter(notification),
                     scan or SafeUnavailableAdapter("scan_orchestration", "scan"),
                     telegram or SafeUnavailableAdapter("telegram_adapter", "telegram"),
                     max_adapter or SafeUnavailableAdapter("max_adapter", "max"),
                     support or SafeUnavailableAdapter("admin_and_support", "support")),
    )


__all__ = ["IdentityWebAdapter", "BeaconWebAdapter", "EntitlementWebAdapter",
           "NotificationWebAdapter", "SafeUnavailableAdapter", "build_rf21_runtime"]
