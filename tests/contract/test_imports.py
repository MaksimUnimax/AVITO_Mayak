from __future__ import annotations

from importlib import import_module

from mayak.contracts import (
    AuditActorCategory,
    AuditConfigurationReference,
    AuditContext,
    AuditContractReference,
    AuditErrorReference,
    AuditModuleIdentifier,
    AuditOperation,
    AuditReadinessReference,
    AuditReason,
    AuditResultReference,
    AuditTargetScope,
    CommonErrorOutcome,
    CommonOutcome,
    ConfigurationComponent,
    ConfigurationEnvironment,
    ConfigurationMetadata,
    ConfigurationPresence,
    ConfigurationProvenance,
    ConfigurationSchemaVersion,
    ConfigurationSourceCategory,
    ConfigurationValidationOutcome,
    ConfigurationValidationStatus,
    ContractMetadata,
    CorrelationContext,
    CorrelationId,
    ErrorCategory,
    IdempotencyDecision,
    IdempotencyDecisionOutcome,
    IdempotencyFingerprint,
    IdempotencyKey,
    IdempotencyScope,
    MessageId,
    ProcessCompositionMetadata,
    ProcessReadinessOutcome,
    ProcessReadinessStatus,
    ProcessRole,
    RequestId,
    Result,
    RetryClass,
    RunId,
    WorkId,
)
from mayak.modules import beacon_management
from mayak.modules.beacon_management import (
    BeaconConfigurationEvidenceRetentionDecision,
    BeaconConfigurationRetentionBoundary,
    BeaconConfigurationStoragePolicyOutcome,
    BeaconConfigurationStoragePolicyRejectionReason,
    BeaconCurrentConfigurationAuthorityStatus,
    BeaconCurrentConfigurationDecision,
    BeaconEffectiveEntitlementSnapshot,
    BeaconEntitlementEvidenceFreshnessStatus,
    BeaconEntitlementEvidenceReference,
    BeaconLifecycleActionKind,
    BeaconLifecycleEntitlementDecision,
    BeaconLifecycleEntitlementOutcome,
    BeaconLifecycleEntitlementRejectionReason,
    BeaconTariffPolicyBand,
)
from mayak.modules.beacon_management import contracts as beacon_management_contracts
from mayak.platform import (
    AuditContext as PlatformAuditContext,
)
from mayak.platform import (
    CorrelationContext as PlatformCorrelationContext,
)
from mayak.platform import (
    DependencyReadiness,
    DependencyReadinessStatus,
    boundaries,
)
from mayak.platform import (
    ProcessCompositionMetadata as PlatformProcessCompositionMetadata,
)
from mayak.platform import (
    ProcessRole as PlatformProcessRole,
)


def test_platform_and_contracts_import() -> None:
    platform = import_module("mayak.platform")
    contracts = import_module("mayak.contracts")

    assert platform.MODULE_ID == boundaries.PLATFORM_AND_CONTRACTS_MODULE_ID
    assert contracts.MODULE_ID == boundaries.PLATFORM_AND_CONTRACTS_MODULE_ID


def test_contract_package_exports_common_primitives() -> None:
    assert AuditActorCategory.__name__ == "AuditActorCategory"
    assert AuditConfigurationReference.__name__ == "AuditConfigurationReference"
    assert AuditContext.__name__ == "AuditContext"
    assert AuditContractReference.__name__ == "AuditContractReference"
    assert AuditErrorReference.__name__ == "AuditErrorReference"
    assert AuditModuleIdentifier.__name__ == "AuditModuleIdentifier"
    assert AuditOperation.__name__ == "AuditOperation"
    assert AuditReadinessReference.__name__ == "AuditReadinessReference"
    assert AuditReason.__name__ == "AuditReason"
    assert AuditResultReference.__name__ == "AuditResultReference"
    assert AuditTargetScope.__name__ == "AuditTargetScope"
    assert ContractMetadata.__name__ == "ContractMetadata"
    assert CorrelationContext.__name__ == "CorrelationContext"
    assert CorrelationId.__name__ == "CorrelationId"
    assert Result.__name__ == "Result"
    assert ErrorCategory.__name__ == "ErrorCategory"
    assert ConfigurationComponent.__name__ == "ConfigurationComponent"
    assert ConfigurationEnvironment.__name__ == "ConfigurationEnvironment"
    assert ConfigurationMetadata.__name__ == "ConfigurationMetadata"
    assert ConfigurationPresence.__name__ == "ConfigurationPresence"
    assert ConfigurationProvenance.__name__ == "ConfigurationProvenance"
    assert ConfigurationSchemaVersion.__name__ == "ConfigurationSchemaVersion"
    assert ConfigurationSourceCategory.__name__ == "ConfigurationSourceCategory"
    assert ConfigurationValidationOutcome.__name__ == "ConfigurationValidationOutcome"
    assert ConfigurationValidationStatus.__name__ == "ConfigurationValidationStatus"
    assert IdempotencyDecision.__name__ == "IdempotencyDecision"
    assert IdempotencyDecisionOutcome.__name__ == "IdempotencyDecisionOutcome"
    assert IdempotencyFingerprint.__name__ == "IdempotencyFingerprint"
    assert IdempotencyKey.__name__ == "IdempotencyKey"
    assert IdempotencyScope.__name__ == "IdempotencyScope"
    assert ProcessCompositionMetadata.__name__ == "ProcessCompositionMetadata"
    assert ProcessReadinessOutcome.__name__ == "ProcessReadinessOutcome"
    assert ProcessReadinessStatus.__name__ == "ProcessReadinessStatus"
    assert ProcessRole.__name__ == "ProcessRole"
    assert CommonOutcome.__name__ == "CommonOutcome"
    assert CommonErrorOutcome.__name__ == "CommonErrorOutcome"
    assert RetryClass.__name__ == "RetryClass"
    assert MessageId.__name__ == "MessageId"
    assert RequestId.__name__ == "RequestId"
    assert RunId.__name__ == "RunId"
    assert WorkId.__name__ == "WorkId"


def test_platform_package_exports_process_primitives() -> None:
    assert PlatformAuditContext.__name__ == "AuditContext"
    assert PlatformCorrelationContext.__name__ == "CorrelationContext"
    assert DependencyReadiness.__name__ == "DependencyReadiness"
    assert DependencyReadinessStatus.__name__ == "DependencyReadinessStatus"
    assert PlatformProcessCompositionMetadata.__name__ == "ProcessCompositionMetadata"
    assert PlatformProcessRole.__name__ == "ProcessRole"


def test_all_module_packages_import() -> None:
    package_names_and_ids = [
        ("mayak.modules.identity_and_access", boundaries.IDENTITY_AND_ACCESS_MODULE_ID),
        ("mayak.modules.entitlements_and_billing", boundaries.ENTITLEMENTS_AND_BILLING_MODULE_ID),
        ("mayak.modules.beacon_management", boundaries.BEACON_MANAGEMENT_MODULE_ID),
        ("mayak.modules.avito_parser_adapter", boundaries.AVITO_PARSER_ADAPTER_MODULE_ID),
        (
            "mayak.modules.scan_orchestration",
            boundaries.SCAN_ORCHESTRATION_AND_LISTING_STATE_MODULE_ID,
        ),
        ("mayak.modules.egress_routing", boundaries.EGRESS_ROUTING_MODULE_ID),
        ("mayak.modules.notification_delivery", boundaries.NOTIFICATION_DELIVERY_MODULE_ID),
        ("mayak.modules.telegram_adapter", boundaries.TELEGRAM_ADAPTER_MODULE_ID),
        ("mayak.modules.max_adapter", boundaries.MAX_ADAPTER_MODULE_ID),
        ("mayak.modules.admin_and_support", boundaries.ADMIN_AND_SUPPORT_MODULE_ID),
        ("mayak.modules.web_cabinet", boundaries.WEB_CABINET_MODULE_ID),
        ("mayak.modules.filter_catalog", boundaries.FILTER_CATALOG_AND_BUILDER_MODULE_ID),
    ]

    for package_name, module_id in package_names_and_ids:
        module = import_module(package_name)
        assert module.MODULE_ID == module_id


def test_beacon_management_package_exports_bm07_current_configuration_storage_primitives() -> None:
    assert BeaconCurrentConfigurationAuthorityStatus.__name__ == (
        "BeaconCurrentConfigurationAuthorityStatus"
    )
    assert BeaconConfigurationStoragePolicyOutcome.__name__ == (
        "BeaconConfigurationStoragePolicyOutcome"
    )
    assert BeaconConfigurationRetentionBoundary.__name__ == "BeaconConfigurationRetentionBoundary"
    assert BeaconCurrentConfigurationDecision.__name__ == "BeaconCurrentConfigurationDecision"
    assert BeaconConfigurationEvidenceRetentionDecision.__name__ == (
        "BeaconConfigurationEvidenceRetentionDecision"
    )
    assert BeaconConfigurationStoragePolicyRejectionReason.__name__ == (
        "BeaconConfigurationStoragePolicyRejectionReason"
    )

    assert beacon_management.BeaconCurrentConfigurationAuthorityStatus is (
        beacon_management_contracts.BeaconCurrentConfigurationAuthorityStatus
    )
    assert beacon_management.BeaconConfigurationStoragePolicyOutcome is (
        beacon_management_contracts.BeaconConfigurationStoragePolicyOutcome
    )
    assert beacon_management.BeaconConfigurationRetentionBoundary is (
        beacon_management_contracts.BeaconConfigurationRetentionBoundary
    )
    assert beacon_management.BeaconCurrentConfigurationDecision is (
        beacon_management_contracts.BeaconCurrentConfigurationDecision
    )
    assert beacon_management.BeaconConfigurationEvidenceRetentionDecision is (
        beacon_management_contracts.BeaconConfigurationEvidenceRetentionDecision
    )
    assert beacon_management.BeaconConfigurationStoragePolicyRejectionReason is (
        beacon_management_contracts.BeaconConfigurationStoragePolicyRejectionReason
    )


def test_beacon_management_package_exports_bm08_lifecycle_entitlement_primitives() -> None:
    assert BeaconLifecycleActionKind.__name__ == "BeaconLifecycleActionKind"
    assert BeaconLifecycleEntitlementOutcome.__name__ == "BeaconLifecycleEntitlementOutcome"
    assert BeaconLifecycleEntitlementRejectionReason.__name__ == (
        "BeaconLifecycleEntitlementRejectionReason"
    )
    assert BeaconEntitlementEvidenceFreshnessStatus.__name__ == (
        "BeaconEntitlementEvidenceFreshnessStatus"
    )
    assert BeaconEntitlementEvidenceReference.__name__ == "BeaconEntitlementEvidenceReference"
    assert BeaconTariffPolicyBand.__name__ == "BeaconTariffPolicyBand"
    assert BeaconEffectiveEntitlementSnapshot.__name__ == "BeaconEffectiveEntitlementSnapshot"
    assert BeaconLifecycleEntitlementDecision.__name__ == "BeaconLifecycleEntitlementDecision"

    assert beacon_management.BeaconLifecycleActionKind is (
        beacon_management_contracts.BeaconLifecycleActionKind
    )
    assert beacon_management.BeaconLifecycleEntitlementOutcome is (
        beacon_management_contracts.BeaconLifecycleEntitlementOutcome
    )
    assert beacon_management.BeaconLifecycleEntitlementRejectionReason is (
        beacon_management_contracts.BeaconLifecycleEntitlementRejectionReason
    )
    assert beacon_management.BeaconEntitlementEvidenceFreshnessStatus is (
        beacon_management_contracts.BeaconEntitlementEvidenceFreshnessStatus
    )
    assert beacon_management.BeaconEntitlementEvidenceReference is (
        beacon_management_contracts.BeaconEntitlementEvidenceReference
    )
    assert beacon_management.BeaconTariffPolicyBand is (
        beacon_management_contracts.BeaconTariffPolicyBand
    )
    assert beacon_management.BeaconEffectiveEntitlementSnapshot is (
        beacon_management_contracts.BeaconEffectiveEntitlementSnapshot
    )
    assert beacon_management.BeaconLifecycleEntitlementDecision is (
        beacon_management_contracts.BeaconLifecycleEntitlementDecision
    )
