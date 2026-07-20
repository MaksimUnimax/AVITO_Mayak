"""Literal, ordered export contracts for Admin & Support."""

import importlib

import mayak.modules.admin_and_support as package
from mayak.modules.admin_and_support import (
    access_actions,
    anchor_actions,
    beacon_actions,
    case_records,
    contracts,
    notification_actions,
    role_actions,
    safe_reads,
    tariff_actions,
)

EXPECTED = {
    contracts: [
        "SupportCaseState",
        "SupportWorkItemState",
        "SupportSubjectKind",
        "SupportEvidenceKind",
        "SupportFreshnessState",
        "SupportReadState",
        "SupportExplanationState",
        "SupportCommandPreparationState",
        "SupportActionAuditState",
        "SupportEscalationState",
        "SupportActorContext",
        "SupportSubjectReference",
        "SupportEvidenceReference",
        "SupportCase",
        "SupportWorkItem",
        "SupportReadModel",
        "SupportExplanationRecord",
        "SupportCommandEnvelope",
        "SupportActionAuditRecord",
        "SupportEscalationRecord",
    ],
    safe_reads: [
        "SupportSummaryFamily",
        "SupportSafeSummaryState",
        "SupportSafeSummaryReference",
        "SupportSafeReadRequest",
        "SupportSafeReadProjection",
        "SupportSafeExplanationRequest",
        "SupportSafeExplanationOutcome",
    ],
    role_actions: [
        "AdminRoleActionKind",
        "AdminRoleActionOutcomeState",
        "AdminRoleActionRequest",
        "AdminRoleActionOutcome",
    ],
    tariff_actions: [
        "AdminTariffCatalogActionKind",
        "AdminTariffPopulationEffect",
        "AdminTariffCatalogOutcomeState",
        "AdminTariffCatalogActionRequest",
        "AdminTariffCatalogActionOutcome",
    ],
    access_actions: [
        "AdminUserAccessActionKind",
        "AdminUserAccessOutcomeState",
        "AdminUserAccessActionRequest",
        "AdminUserAccessActionOutcome",
    ],
    anchor_actions: [
        "AdminAnchorActionKind",
        "AdminAnchorActionOutcomeState",
        "AdminAnchorStateSummary",
        "AdminAnchorActionRequest",
        "AdminAnchorActionOutcome",
    ],
    beacon_actions: [
        "AdminBeaconSupportActionKind",
        "AdminBeaconPatchFieldSupportState",
        "AdminBeaconSupportOutcomeState",
        "AdminBeaconCurrentStateSummary",
        "AdminBeaconPatchFieldReference",
        "AdminBeaconSupportActionRequest",
        "AdminBeaconSupportActionOutcome",
    ],
    case_records: [
        "SupportCaseActionKind",
        "SupportCaseActionOutcomeState",
        "SupportCaseAuditLinkState",
        "SupportInternalNoteRecord",
        "SupportCaseActionRequest",
        "SupportCaseActionOutcome",
        "SupportCaseAuditTrailEntry",
    ],
    notification_actions: [
        "AdminNotificationSupportActionKind",
        "AdminNotificationDeliveryStateClass",
        "AdminNotificationSupportOutcomeState",
        "AdminNotificationCurrentStateSummary",
        "AdminNotificationInterventionPolicyReference",
        "AdminNotificationSupportActionRequest",
        "AdminNotificationSupportActionOutcome",
    ],
}
EXPECTED_PACKAGE = [
    "MODULE_ID",
    "SupportActionAuditRecord",
    "SupportActionAuditState",
    "SupportActorContext",
    "SupportCase",
    "SupportCaseState",
    "SupportCommandEnvelope",
    "SupportCommandPreparationState",
    "SupportEscalationRecord",
    "SupportEscalationState",
    "SupportEvidenceKind",
    "SupportEvidenceReference",
    "SupportExplanationRecord",
    "SupportExplanationState",
    "SupportFreshnessState",
    "SupportReadModel",
    "SupportReadState",
    "SupportSubjectKind",
    "SupportSubjectReference",
    "SupportWorkItem",
    "SupportWorkItemState",
    "SupportSafeExplanationOutcome",
    "SupportSafeExplanationRequest",
    "SupportSafeReadProjection",
    "SupportSafeReadRequest",
    "SupportSafeSummaryReference",
    "SupportSafeSummaryState",
    "SupportSummaryFamily",
    "AdminRoleActionKind",
    "AdminRoleActionOutcomeState",
    "AdminRoleActionRequest",
    "AdminRoleActionOutcome",
    "AdminTariffCatalogActionKind",
    "AdminTariffPopulationEffect",
    "AdminTariffCatalogOutcomeState",
    "AdminTariffCatalogActionRequest",
    "AdminTariffCatalogActionOutcome",
    "AdminUserAccessActionKind",
    "AdminUserAccessOutcomeState",
    "AdminUserAccessActionRequest",
    "AdminUserAccessActionOutcome",
    "AdminAnchorActionKind",
    "AdminAnchorActionOutcomeState",
    "AdminAnchorStateSummary",
    "AdminAnchorActionRequest",
    "AdminAnchorActionOutcome",
    "AdminBeaconSupportActionKind",
    "AdminBeaconPatchFieldSupportState",
    "AdminBeaconSupportOutcomeState",
    "AdminBeaconCurrentStateSummary",
    "AdminBeaconPatchFieldReference",
    "AdminBeaconSupportActionRequest",
    "AdminBeaconSupportActionOutcome",
    "SupportCaseActionKind",
    "SupportCaseActionOutcomeState",
    "SupportCaseAuditLinkState",
    "SupportInternalNoteRecord",
    "SupportCaseActionRequest",
    "SupportCaseActionOutcome",
    "SupportCaseAuditTrailEntry",
    "AdminNotificationSupportActionKind",
    "AdminNotificationDeliveryStateClass",
    "AdminNotificationSupportOutcomeState",
    "AdminNotificationCurrentStateSummary",
    "AdminNotificationInterventionPolicyReference",
    "AdminNotificationSupportActionRequest",
    "AdminNotificationSupportActionOutcome",
]
ALIASES = {
    "AdminNotificationActionKind",
    "AdminNotificationActionOutcomeState",
    "AdminNotificationDeliveryStateSummary",
}


def test_literal_source_inventories_and_order() -> None:
    for module, expected in EXPECTED.items():
        assert module.__all__ == expected
        assert len(module.__all__) == len(set(module.__all__))


def test_literal_package_inventory_order_and_count() -> None:
    assert package.__all__ == EXPECTED_PACKAGE
    assert len(EXPECTED_PACKAGE) == 67
    assert len(EXPECTED_PACKAGE) == len(set(EXPECTED_PACKAGE))


def test_reexport_identity_and_no_historical_aliases() -> None:
    for module, names in EXPECTED.items():
        for name in names:
            assert getattr(package, name) is getattr(module, name)
        public_contracts = {
            name
            for name, value in vars(module).items()
            if not name.startswith("_")
            and isinstance(value, type)
            and value.__module__ == module.__name__
            and (hasattr(value, "model_fields") or hasattr(value, "__members__"))
        }
        assert public_contracts == set(names)
    assert not ALIASES & set(vars(notification_actions))
    assert not any(
        name.lower() in {"send", "resend", "send_notification", "resend_notification"}
        for name in vars(notification_actions)
    )


def test_export_mutation_controls_are_strict() -> None:
    original = list(package.__all__)
    swapped = list(original)
    swapped[1], swapped[2] = swapped[2], swapped[1]
    assert swapped != EXPECTED_PACKAGE
    assert original + ["synthetic-extra"] != EXPECTED_PACKAGE
    assert EXPECTED[contracts][:-1] != EXPECTED[contracts]
    assert "AdminNotificationActionKind" not in EXPECTED_PACKAGE


def test_reload_export_identity_is_deterministic() -> None:
    before = tuple(package.__all__)
    importlib.reload(package)
    assert tuple(package.__all__) == before
