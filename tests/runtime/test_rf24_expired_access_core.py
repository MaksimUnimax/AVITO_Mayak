from datetime import UTC, datetime
from typing import Any, cast
from uuid import UUID

import pytest

from mayak.modules.entitlements_and_billing.contracts import (
    EntitlementDecisionStatus,
    TariffName,
)
from mayak.modules.entitlements_and_billing.runtime import EffectiveEntitlement
from mayak.runtime.rf23_composition import CustomerEntitlementPort
from mayak.runtime.rf24_composition import ScanEntitlementAdapter

ACCOUNT = UUID("00000000-0000-0000-0000-000000000024")


class Owner:
    def __init__(self, projection: object = None, error: Exception | None = None) -> None:
        self.projection = projection
        self.error = error

    def evaluate_effective(self, session: object, account_id: UUID, *, at: datetime) -> object:
        if self.error is not None:
            raise self.error
        return self.projection


def projection(status: EntitlementDecisionStatus) -> EffectiveEntitlement:
    return EffectiveEntitlement(
        status=status,
        account_id=ACCOUNT,
        tariff=TariffName.BASIC if status is EntitlementDecisionStatus.ALLOWED else None,
    )


@pytest.mark.parametrize(
    ("status", "allowed"),
    [
        (EntitlementDecisionStatus.ALLOWED, True),
        (EntitlementDecisionStatus.DENIED, False),
        (EntitlementDecisionStatus.USER_CHOICE_REQUIRED, False),
        (EntitlementDecisionStatus.FREE_COMPLIANCE_REQUIRED, False),
    ],
)
def test_customer_entitlement_port_interprets_owner_status_fail_closed(
    status: EntitlementDecisionStatus, allowed: bool
) -> None:
    decision = CustomerEntitlementPort(cast(Any, Owner(projection(status)))).decide(
        cast(Any, object()), account_id=ACCOUNT, action="activate", active_count=0
    )
    assert decision.allowed is allowed


def test_customer_entitlement_port_rejects_missing_or_malformed_status() -> None:
    for malformed in (object(), type("Projection", (), {"status": "ALLOWED"})()):
        decision = CustomerEntitlementPort(cast(Any, Owner(malformed))).decide(
            cast(Any, object()), account_id=ACCOUNT, action="activate", active_count=0
        )
        assert decision.allowed is False


def test_customer_entitlement_port_rejects_owner_exception() -> None:
    decision = CustomerEntitlementPort(
        cast(Any, Owner(error=RuntimeError("owner unavailable")))
    ).decide(
        cast(Any, object()), account_id=ACCOUNT, action="activate", active_count=0
    )
    assert decision.allowed is False


def test_scan_entitlement_adapter_uses_explicit_moment() -> None:
    expected = datetime(2030, 1, 1, tzinfo=UTC)
    owner = Owner(projection(EntitlementDecisionStatus.ALLOWED))
    adapter = ScanEntitlementAdapter(cast(Any, owner), lambda: datetime(2040, 1, 1, tzinfo=UTC))
    adapter.bind(cast(Any, object()), at=expected)
    result = adapter.current(UUID("00000000-0000-0000-0000-000000000025"), ACCOUNT)
    assert result.status.value == "ALLOWED"
