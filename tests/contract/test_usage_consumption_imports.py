from __future__ import annotations

from importlib import import_module

from mayak.modules import entitlements_and_billing


def test_usage_consumption_module_imports_with_expected_exports() -> None:
    module = import_module("mayak.modules.entitlements_and_billing.usage_consumption")

    assert module.APPROVED_USAGE_COUNTER_FAMILIES[0].value == "ACTIVE_BEACON_SLOT"
    assert module.BLOCKED_USAGE_COUNTER_FAMILIES[-1].value == "MONETARY_PAYMENT_CONSUMPTION"
    assert module.BEACON_MANAGEMENT_MODULE_LABEL == "Beacon Management"
    assert module.SCAN_ORCHESTRATION_MODULE_LABEL == "Scan Orchestration"


def test_entitlements_and_billing_package_exports_usage_consumption_contracts() -> None:
    assert entitlements_and_billing.UsageCounterFamily.ACTIVE_BEACON_SLOT.value == "ACTIVE_BEACON_SLOT"
    assert entitlements_and_billing.UsageConsumptionOutcome.ACCEPTED.value == "ACCEPTED"
    assert entitlements_and_billing.APPROVED_USAGE_COUNTER_FAMILIES[1].value == "SCAN_INTERVAL_WINDOW"
    assert entitlements_and_billing.ActiveBeaconSlotEvidence.__name__ == "ActiveBeaconSlotEvidence"

