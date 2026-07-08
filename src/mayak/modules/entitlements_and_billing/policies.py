"""Approved tariff policies for Entitlements & Billing."""

from __future__ import annotations

from typing import Final

from mayak.modules.entitlements_and_billing.contracts import TariffDefinition, TariffName

SEMANTIC_POLICY_VERSION: Final[str] = "v1"

FREE_TARIFF_POLICY: Final[TariffDefinition] = TariffDefinition(
    tariff_name=TariffName.FREE,
    semantic_version=SEMANTIC_POLICY_VERSION,
    price_rub=0,
    billing_period_label=None,
    scan_interval_floor_minutes=180,
    scan_interval_step_minutes=180,
    active_beacon_limit=1,
    feature_notes="reduced features",
    mechanism_notes="same entitlement mechanism as paid tariff, stricter limits",
)

BASIC_TARIFF_POLICY: Final[TariffDefinition] = TariffDefinition(
    tariff_name=TariffName.BASIC,
    semantic_version=SEMANTIC_POLICY_VERSION,
    price_rub=990,
    billing_period_label="1 month",
    scan_interval_floor_minutes=5,
    scan_interval_step_minutes=5,
    active_beacon_limit=None,
    feature_notes=None,
    mechanism_notes=None,
)

APPROVED_TARIFF_DEFINITIONS: Final[tuple[TariffDefinition, ...]] = (
    FREE_TARIFF_POLICY,
    BASIC_TARIFF_POLICY,
)

TARIFFS_BY_NAME: Final[dict[TariffName, TariffDefinition]] = {
    tariff_definition.tariff_name: tariff_definition
    for tariff_definition in APPROVED_TARIFF_DEFINITIONS
}

FUTURE_DECISION_GATES: Final[tuple[str, ...]] = ("OD-010", "OD-011", "OD-013")

__all__ = [
    "APPROVED_TARIFF_DEFINITIONS",
    "BASIC_TARIFF_POLICY",
    "FREE_TARIFF_POLICY",
    "FUTURE_DECISION_GATES",
    "SEMANTIC_POLICY_VERSION",
    "TARIFFS_BY_NAME",
]
