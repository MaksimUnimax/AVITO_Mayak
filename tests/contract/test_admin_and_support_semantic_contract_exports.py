"""Deterministic public export checks for Admin & Support semantic contracts."""

import importlib
import sys

import mayak.modules.admin_and_support as package
import mayak.modules.admin_and_support.access_actions as access_actions
import mayak.modules.admin_and_support.anchor_actions as anchor_actions
import mayak.modules.admin_and_support.beacon_actions as beacon_actions
import mayak.modules.admin_and_support.case_records as case_records
import mayak.modules.admin_and_support.contracts as contracts
import mayak.modules.admin_and_support.notification_actions as notification_actions
import mayak.modules.admin_and_support.role_actions as role_actions
import mayak.modules.admin_and_support.safe_reads as safe_reads
import mayak.modules.admin_and_support.tariff_actions as tariff_actions

INVENTORIES = {
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
PACKAGE_EXPORTS = list(package.__all__)


def test_exact_ordered_module_inventories() -> None:
    for module, expected in INVENTORIES.items():
        assert module.__all__ == expected
        assert len(expected) == len(set(expected))


def test_package_has_exactly_67_exports() -> None:
    assert len(PACKAGE_EXPORTS) == 67
    assert len(PACKAGE_EXPORTS) == len(set(PACKAGE_EXPORTS))
    assert PACKAGE_EXPORTS[0] == "MODULE_ID"


def test_module_id_is_stable() -> None:
    assert package.MODULE_ID == "11-admin-and-support"


def test_package_reexport_identity() -> None:
    for module, names in INVENTORIES.items():
        for name in names:
            assert getattr(package, name) is getattr(module, name)


def test_no_extra_public_symbol_or_historical_notification_alias() -> None:
    for module, expected in INVENTORIES.items():
        public = {name for name in vars(module) if not name.startswith("_")}
        assert public >= set(expected)
        assert set(module.__all__) == set(expected)
    assert not any(
        name.lower() in {"send", "resend", "send_notification", "resend_notification"}
        for name in vars(notification_actions)
    )


def test_repeated_import_reload_is_deterministic() -> None:
    first = importlib.import_module("mayak.modules.admin_and_support")
    names = tuple(first.__all__)
    second = importlib.reload(first)
    assert tuple(second.__all__) == names
    assert all(getattr(second, name) is getattr(package, name) for name in names)


def test_import_has_no_environment_network_provider_or_persistence_side_effect() -> None:
    before = set(sys.modules)
    for module in (*INVENTORIES, package):
        importlib.reload(module)
    added = {name.split(".")[0] for name in set(sys.modules) - before}
    assert not added & {"requests", "httpx", "aiohttp", "sqlalchemy", "redis", "boto3"}
