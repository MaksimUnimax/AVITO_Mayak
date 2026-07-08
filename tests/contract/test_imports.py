from __future__ import annotations

from importlib import import_module

from mayak.contracts import (
    CommonErrorOutcome,
    CommonOutcome,
    ContractMetadata,
    ErrorCategory,
    IdempotencyDecision,
    IdempotencyDecisionOutcome,
    IdempotencyFingerprint,
    IdempotencyKey,
    IdempotencyScope,
    Result,
    RetryClass,
)
from mayak.platform import boundaries


def test_platform_and_contracts_import() -> None:
    platform = import_module("mayak.platform")
    contracts = import_module("mayak.contracts")

    assert platform.MODULE_ID == boundaries.PLATFORM_AND_CONTRACTS_MODULE_ID
    assert contracts.MODULE_ID == boundaries.PLATFORM_AND_CONTRACTS_MODULE_ID


def test_contract_package_exports_common_primitives() -> None:
    assert ContractMetadata.__name__ == "ContractMetadata"
    assert Result.__name__ == "Result"
    assert ErrorCategory.__name__ == "ErrorCategory"
    assert IdempotencyDecision.__name__ == "IdempotencyDecision"
    assert IdempotencyDecisionOutcome.__name__ == "IdempotencyDecisionOutcome"
    assert IdempotencyFingerprint.__name__ == "IdempotencyFingerprint"
    assert IdempotencyKey.__name__ == "IdempotencyKey"
    assert IdempotencyScope.__name__ == "IdempotencyScope"
    assert CommonOutcome.__name__ == "CommonOutcome"
    assert CommonErrorOutcome.__name__ == "CommonErrorOutcome"
    assert RetryClass.__name__ == "RetryClass"


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
