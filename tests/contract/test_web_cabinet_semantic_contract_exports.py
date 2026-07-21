"""Literal Web Cabinet public exports, enum and reload contracts."""

from __future__ import annotations

import importlib
import os
import types
from enum import Enum

import pytest
from pydantic import BaseModel, ValidationError

import mayak.modules.web_cabinet as package
from mayak.modules.web_cabinet import (
    admin_analytics,
    auth_context,
    beacon_commands,
    channel_linking,
    entitlement_projections,
    notification_history,
    read_models,
    security_privacy,
    status_display,
    support_handoff,
)

MODULE_EXPORTS = {
    read_models: [
        "RequestWebCabinetViewQuery",
        "WebCabinetViewResult",
        "WebCabinetViewState",
        "WebReadFreshness",
        "WebReadModelFamily",
        "WebReadModelSourceReference",
        "WebSourceState",
        "WebViewAudience",
    ],
    beacon_commands: [
        "SubmitBeaconWebCommandCommand",
        "WebBeaconCommandKind",
        "WebBeaconCommandSubmitOutcome",
        "WebBeaconCommandSubmitState",
        "WebBeaconPatchField",
    ],
    auth_context: [
        "RequestWebPresentationContextQuery",
        "WebIdentityAuthorityReference",
        "WebPresentationActorState",
        "WebPresentationContextResult",
        "WebPresentationContextState",
        "WebSessionReferenceState",
    ],
    entitlement_projections: [
        "RequestWebEntitlementProjectionQuery",
        "WebEntitlementAccessState",
        "WebEntitlementCapabilityProjection",
        "WebEntitlementProjectionResult",
        "WebEntitlementProjectionState",
        "WebTariffOptionProjection",
        "WebTariffOptionState",
    ],
    notification_history: [
        "RequestWebNotificationHistoryQuery",
        "WebNotificationDeliveryHistoryEntry",
        "WebNotificationDeliveryState",
        "WebNotificationHistoryResult",
        "WebNotificationHistoryResultState",
        "WebNotificationListingReferenceProjection",
    ],
    status_display: [
        "RequestWebStatusDisplayQuery",
        "WebStatusDisplayFamily",
        "WebStatusDisplayItem",
        "WebStatusDisplayResult",
        "WebStatusDisplayResultState",
        "WebStatusEvidenceClass",
        "WebStatusEvidenceReference",
        "WebStatusSourceFamily",
    ],
    channel_linking: [
        "RequestWebChannelSurfaceQuery",
        "SubmitWebChannelCommandCommand",
        "WebChannelCommandKind",
        "WebChannelCommandSubmitOutcome",
        "WebChannelCommandSubmitState",
        "WebChannelKind",
        "WebChannelNotificationPreferenceState",
        "WebChannelSurfaceProjection",
        "WebChannelSurfaceResult",
        "WebChannelSurfaceResultState",
        "WebChannelSurfaceState",
    ],
    admin_analytics: [
        "RequestWebAdminAnalyticsQuery",
        "WebAdminAnalyticsFilterKind",
        "WebAdminAnalyticsFilterReference",
        "WebAdminAnalyticsMetricKind",
        "WebAdminAnalyticsMetricProjection",
        "WebAdminAnalyticsMetricRequest",
        "WebAdminAnalyticsMetricState",
        "WebAdminAnalyticsResult",
        "WebAdminAnalyticsResultState",
        "WebAdminAnalyticsSortDirection",
        "WebAdminAnalyticsSortField",
    ],
    support_handoff: [
        "RequestWebSupportHandoffQuery",
        "WebSupportHandoffItemKind",
        "WebSupportHandoffItemState",
        "WebSupportHandoffProjection",
        "WebSupportHandoffResult",
        "WebSupportHandoffResultState",
    ],
    security_privacy: [
        "RequestWebSecurityPrivacyAssessmentQuery",
        "WebPrivacyControlProjection",
        "WebPrivacyProjectionState",
        "WebPrivacySurfaceKind",
        "WebSecurityPrivacyAssessmentResult",
        "WebSecurityPrivacyResultState",
    ],
}
PACKAGE_EXPORTS = ["MODULE_ID"] + [name for module in MODULE_EXPORTS.values() for name in module]
ENUM_VALUES = {
    "WebBeaconCommandKind": (
        "PATCH_CURRENT_CONFIGURATION",
        "ARCHIVE_TO_HISTORY",
        "DELETE_TO_HISTORY",
        "RESTORE_FROM_HISTORY",
        "PERMANENT_DELETE",
    ),
    "WebReadModelFamily": (
        "ACCOUNT_SUMMARY",
        "ACTIVE_BEACONS",
        "BEACON_HISTORY",
        "TARIFF_ACCESS_LIMITS",
        "LAST_SCAN_STATUS",
        "MESSAGE_RESULT_HISTORY",
        "TELEGRAM_CHANNEL",
        "MAX_CHANNEL",
        "CUSTOMER_SUPPORT_STATUS",
        "ADMIN_ANALYTICS_PLACEHOLDER",
    ),
    "WebReadFreshness": ("FRESH", "STALE", "UNKNOWN", "AMBIGUOUS"),
    "WebViewAudience": ("CUSTOMER", "ADMIN_AUTHORIZED"),
    "WebPrivacySurfaceKind": (
        "BROWSER_VISIBLE_DATA",
        "SAFE_ERROR",
        "ANALYTICS_COLLECTION",
        "RETENTION_POLICY",
        "DELETION_EXPORT_POLICY",
    ),
    "WebPrivacyProjectionState": (
        "SAFE",
        "REDACTED",
        "STALE",
        "AMBIGUOUS",
        "POLICY_BLOCKED",
        "UNSUPPORTED",
    ),
    "WebSecurityPrivacyResultState": (
        "SAFE",
        "REDACTED",
        "FORBIDDEN",
        "STALE",
        "AMBIGUOUS",
        "POLICY_BLOCKED",
        "UNSUPPORTED",
    ),
}


def test_literal_module_exports() -> None:
    for module, expected in MODULE_EXPORTS.items():
        assert module.__all__ == expected
        assert len(module.__all__) == len(set(module.__all__))
        assert all(not name.startswith("_") for name in module.__all__)


def test_literal_package_exports_and_identity() -> None:
    assert package.__all__ == PACKAGE_EXPORTS
    assert len(package.__all__) == 75
    assert len(set(package.__all__)) == 75
    assert all(not name.startswith("_") for name in package.__all__)
    assert package.MODULE_ID == "12-web-cabinet"
    for module, names in MODULE_EXPORTS.items():
        for name in names:
            assert getattr(package, name) is getattr(module, name)


def test_enum_names_and_serialized_values_are_ordered_literals() -> None:
    modules = tuple(MODULE_EXPORTS)
    for module in modules:
        for name in MODULE_EXPORTS[module]:
            value = getattr(module, name)
            if isinstance(value, type) and issubclass(value, Enum):
                assert tuple(member.name for member in value) == tuple(
                    member.value for member in value
                )
    for name, values in ENUM_VALUES.items():
        enum = getattr(package, name)
        assert tuple(member.name for member in enum) == values
        assert tuple(member.value for member in enum) == values


def test_public_models_are_frozen_extra_forbid_and_whitespace_stripping() -> None:
    for module, names in MODULE_EXPORTS.items():
        for name in names:
            value = getattr(module, name)
            if isinstance(value, type) and issubclass(value, BaseModel):
                assert value.model_config["extra"] == "forbid"
                assert value.model_config["frozen"] is True
                assert value.model_config["str_strip_whitespace"] is True
                assert tuple(value.model_fields) == tuple(value.model_fields.keys())


def test_exports_are_exact_and_no_alias_or_private_names() -> None:
    owners = {name for names in MODULE_EXPORTS.values() for name in names}
    assert set(package.__all__) == owners | {"MODULE_ID"}
    assert not any(name.startswith("_") for name in owners)


@pytest.mark.parametrize("module", tuple(MODULE_EXPORTS))
def test_reload_preserves_order_without_environment_side_effect(
    module: types.ModuleType,
) -> None:
    before = os.environ.copy()
    expected = list(MODULE_EXPORTS[module])
    importlib.reload(module)
    assert module.__all__ == expected
    assert os.environ == before


@pytest.mark.parametrize("module", (package, *MODULE_EXPORTS))
def test_reload_package_and_modules_are_deterministic(
    module: types.ModuleType,
) -> None:
    before = os.environ.copy()
    expected = list(module.__all__)
    importlib.reload(module)
    assert module.__all__ == expected
    assert os.environ == before


def test_literal_field_order_controls_reject_obvious_contract_mutations() -> None:
    assert list(package.WebReadModelSourceReference.model_fields) == [
        "web_source_reference_id",
        "family",
        "owning_module_id",
        "account_id",
        "tenant_scope_reference_id",
        "state",
        "freshness",
        "safe_projection_reference_id",
        "provenance_reference_ids",
        "reason_code",
        "ambiguity_reference_id",
        "redaction_policy_reference_id",
        "safe_reference_only",
        "redacted",
        "minimal_personal_data",
        "contains_secret_material",
        "raw_provider_payload_retained",
        "full_private_message_retained",
        "full_listing_archive_retained",
        "mutation_authority",
        "provider_call_authority",
    ]
    assert list(package.WebBeaconPatchField.model_fields) == [
        "web_patch_field_id",
        "field_name",
        "requested_value_reference_id",
        "owning_module_validation_family_reference_id",
        "client_validation_reference_id",
        "explicitly_supplied",
        "server_validation_required",
        "client_validation_authority",
        "field_support_authority",
        "raw_value_retained",
        "provider_payload_retained",
    ]
    with pytest.raises(ValidationError):
        package.WebBeaconPatchField(
            web_patch_field_id=" ",
            field_name="x",
            requested_value_reference_id="v",
            owning_module_validation_family_reference_id="o",
        )
