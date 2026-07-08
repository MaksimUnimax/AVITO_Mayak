from __future__ import annotations

from importlib import import_module

from mayak.modules import entitlements_and_billing
from mayak.platform import boundaries


def test_entitlements_and_billing_package_imports_with_expected_module_id() -> None:
    module = import_module("mayak.modules.entitlements_and_billing")
    provider_boundary_module = import_module("mayak.modules.entitlements_and_billing.payment_provider_boundary")
    admin_tariff_module = import_module("mayak.modules.entitlements_and_billing.admin_tariff_management")

    assert module.MODULE_ID == boundaries.ENTITLEMENTS_AND_BILLING_MODULE_ID
    assert entitlements_and_billing.MODULE_ID == boundaries.ENTITLEMENTS_AND_BILLING_MODULE_ID
    assert module.FREE_TARIFF_POLICY.tariff_name.value == "FREE"
    assert module.BASIC_TARIFF_POLICY.tariff_name.value == "BASIC"
    assert admin_tariff_module.AdminTariffOutcome.DRAFT_CREATED.value == "DRAFT_CREATED"
    assert admin_tariff_module.AdminTariffCommandFamily.CREATE_TARIFF_DRAFT.value == "CreateTariffDraftCommand"
    assert provider_boundary_module.PaymentProviderCandidate.YOOKASSA.value == "YOOKASSA"
    assert provider_boundary_module.PaymentProviderBoundaryOutcome.ACCEPTED_AS_EVIDENCE.value == (
        "ACCEPTED_AS_EVIDENCE"
    )


def test_entitlements_and_billing_package_exports_synthetic_fixture_registry() -> None:
    assert entitlements_and_billing.FIXTURE_IDS[0] == "FX-EB-OWN-ACCOUNT-DECISION-001"
    assert "FX-EB-REDACTION-001" in entitlements_and_billing.FIXTURE_IDS
    assert entitlements_and_billing.SYNTHETIC_FIXTURE_BY_ID["FX-EB-MANUAL-GRANT-AUTHORIZED-001"].fixture_id == (
        "FX-EB-MANUAL-GRANT-AUTHORIZED-001"
    )


def test_entitlements_and_billing_package_exports_payment_provider_boundary_semantics() -> None:
    assert entitlements_and_billing.PaymentProviderCandidate.TELEGRAM_STARS.value == "TELEGRAM_STARS"
    assert entitlements_and_billing.PaymentProviderBoundaryAction.CAPTURE_EVIDENCE_ONLY.value == (
        "CAPTURE_EVIDENCE_ONLY"
    )
    assert entitlements_and_billing.PaymentProviderBoundaryOutcome.PAYMENT_IS_NOT_AUTHORITY.value == (
        "PAYMENT_IS_NOT_AUTHORITY"
    )


def test_entitlements_and_billing_package_exports_admin_tariff_semantics() -> None:
    assert entitlements_and_billing.AdminTariffCommandFamily.PUBLISH_TARIFF_DEFINITION.value == (
        "PublishTariffDefinitionCommand"
    )
    assert entitlements_and_billing.AdminTariffOutcome.MANUAL_ACCESS_ASSIGNED.value == (
        "MANUAL_ACCESS_ASSIGNED"
    )
    assert entitlements_and_billing.ENTITLEMENTS_TARIFF_ADMIN == "ENTITLEMENTS_TARIFF_ADMIN"
    assert entitlements_and_billing.ENTITLEMENTS_TARIFF_ASSIGN_ADMIN == "ENTITLEMENTS_TARIFF_ASSIGN_ADMIN"
