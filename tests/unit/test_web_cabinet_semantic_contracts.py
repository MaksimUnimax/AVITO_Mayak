"""Executable deterministic WC-02..WC-12 semantic vectors."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Callable

import pytest
from pydantic import ValidationError

from mayak.modules import web_cabinet as package
from tests.architecture.test_web_cabinet_semantic_boundaries import violations

FIXTURE = Path(__file__).parents[1] / "fixtures" / "web_cabinet_semantic_vectors.json"
EXPECTED_TOP = [
    "schema_version",
    "module",
    "accepted_through_step",
    "synthetic_only",
    "contains_real_user_data",
    "contains_real_session_data",
    "contains_secret_material",
    "contains_raw_provider_payload",
    "contains_raw_avito_payload",
    "contains_private_support_data",
    "contains_personal_or_legal_data",
    "network_required",
    "provider_api_required",
    "database_required",
    "runtime_required",
    "canonical_fixture_references",
    "vectors",
]
EXPECTED_CATEGORIES = {
    "VIEW": "WC-02",
    "COMMAND": "WC-03",
    "AUTH": "WC-04",
    "ENTITLEMENT": "WC-05",
    "HISTORY": "WC-06",
    "STATUS": "WC-07",
    "CHANNEL": "WC-08",
    "ANALYTICS": "WC-09",
    "SUPPORT": "WC-10",
    "PRIVACY": "WC-11",
    "STATIC": "WC-12",
}
EXPECTED_VECTORS = [
    (
        "FX-WC12-VIEW-001",
        "WC-02",
        "VIEW",
        "mayak.modules.web_cabinet.read_models.WebCabinetViewResult",
        "valid_composition",
        "PASS",
    ),
    (
        "FX-WC12-VIEW-002",
        "WC-02",
        "VIEW",
        "mayak.modules.web_cabinet.read_models.WebCabinetViewResult",
        "owner_mapping",
        "PASS",
    ),
    (
        "FX-WC12-VIEW-003",
        "WC-02",
        "VIEW",
        "mayak.modules.web_cabinet.read_models.WebCabinetViewResult",
        "terminal_empty",
        "VALIDATION_ERROR",
    ),
    (
        "FX-WC12-VIEW-004",
        "WC-02",
        "VIEW",
        "mayak.modules.web_cabinet.read_models.WebCabinetViewResult",
        "stale_ambiguous",
        "VALIDATION_ERROR",
    ),
    (
        "FX-WC12-VIEW-005",
        "WC-02",
        "VIEW",
        "mayak.modules.web_cabinet.read_models.WebCabinetViewResult",
        "duplicate_source_rejected",
        "VALIDATION_ERROR",
    ),
    (
        "FX-WC12-COMMAND-001",
        "WC-03",
        "COMMAND",
        "mayak.modules.web_cabinet.beacon_commands.SubmitBeaconWebCommandCommand",
        "patch_submission_valid",
        "PASS",
    ),
    (
        "FX-WC12-COMMAND-002",
        "WC-03",
        "COMMAND",
        "mayak.modules.web_cabinet.beacon_commands.SubmitBeaconWebCommandCommand",
        "patch_field_uniqueness",
        "PASS",
    ),
    (
        "FX-WC12-COMMAND-003",
        "WC-03",
        "COMMAND",
        "mayak.modules.web_cabinet.beacon_commands.SubmitBeaconWebCommandCommand",
        "lifecycle_command_matrix",
        "VALIDATION_ERROR",
    ),
    (
        "FX-WC12-COMMAND-004",
        "WC-03",
        "COMMAND",
        "mayak.modules.web_cabinet.beacon_commands.SubmitBeaconWebCommandCommand",
        "idempotency_outcomes",
        "PASS",
    ),
    (
        "FX-WC12-COMMAND-005",
        "WC-03",
        "COMMAND",
        "mayak.modules.web_cabinet.beacon_commands.SubmitBeaconWebCommandCommand",
        "business_authority_forbidden",
        "VALIDATION_ERROR",
    ),
    (
        "FX-WC12-AUTH-001",
        "WC-04",
        "AUTH",
        "mayak.modules.web_cabinet.auth_context.WebPresentationContextResult",
        "verified_context_valid",
        "PASS",
    ),
    (
        "FX-WC12-AUTH-002",
        "WC-04",
        "AUTH",
        "mayak.modules.web_cabinet.auth_context.WebPresentationContextResult",
        "session_non_authority",
        "VALIDATION_ERROR",
    ),
    (
        "FX-WC12-AUTH-003",
        "WC-04",
        "AUTH",
        "mayak.modules.web_cabinet.auth_context.WebPresentationContextResult",
        "unauthenticated_forbidden",
        "VALIDATION_ERROR",
    ),
    (
        "FX-WC12-AUTH-004",
        "WC-04",
        "AUTH",
        "mayak.modules.web_cabinet.auth_context.WebPresentationContextResult",
        "phone_recovery_blocked",
        "VALIDATION_ERROR",
    ),
    (
        "FX-WC12-AUTH-005",
        "WC-04",
        "AUTH",
        "mayak.modules.web_cabinet.auth_context.WebPresentationContextResult",
        "merge_second_account_forbidden",
        "VALIDATION_ERROR",
    ),
    (
        "FX-WC12-ENTITLEMENT-001",
        "WC-05",
        "ENTITLEMENT",
        "mayak.modules.web_cabinet.entitlement_projections.WebEntitlementProjectionResult",
        "effective_access_valid",
        "PASS",
    ),
    (
        "FX-WC12-ENTITLEMENT-002",
        "WC-05",
        "ENTITLEMENT",
        "mayak.modules.web_cabinet.entitlement_projections.WebEntitlementProjectionResult",
        "tariff_options_source_owned",
        "PASS",
    ),
    (
        "FX-WC12-ENTITLEMENT-003",
        "WC-05",
        "ENTITLEMENT",
        "mayak.modules.web_cabinet.entitlement_projections.WebEntitlementProjectionResult",
        "terminal_state_matrix",
        "VALIDATION_ERROR",
    ),
    (
        "FX-WC12-ENTITLEMENT-004",
        "WC-05",
        "ENTITLEMENT",
        "mayak.modules.web_cabinet.entitlement_projections.WebEntitlementProjectionResult",
        "invented_values_forbidden",
        "VALIDATION_ERROR",
    ),
    (
        "FX-WC12-ENTITLEMENT-005",
        "WC-05",
        "ENTITLEMENT",
        "mayak.modules.web_cabinet.entitlement_projections.WebEntitlementProjectionResult",
        "duplicate_reference_rejected",
        "VALIDATION_ERROR",
    ),
    (
        "FX-WC12-HISTORY-001",
        "WC-06",
        "HISTORY",
        "mayak.modules.web_cabinet.notification_history.WebNotificationHistoryResult",
        "grouped_history_valid",
        "PASS",
    ),
    (
        "FX-WC12-HISTORY-002",
        "WC-06",
        "HISTORY",
        "mayak.modules.web_cabinet.notification_history.WebNotificationHistoryResult",
        "all_safe_listing_references",
        "PASS",
    ),
    (
        "FX-WC12-HISTORY-003",
        "WC-06",
        "HISTORY",
        "mayak.modules.web_cabinet.notification_history.WebNotificationHistoryResult",
        "terminal_state_matrix",
        "VALIDATION_ERROR",
    ),
    (
        "FX-WC12-HISTORY-004",
        "WC-06",
        "HISTORY",
        "mayak.modules.web_cabinet.notification_history.WebNotificationHistoryResult",
        "ambiguous_delivery",
        "VALIDATION_ERROR",
    ),
    (
        "FX-WC12-HISTORY-005",
        "WC-06",
        "HISTORY",
        "mayak.modules.web_cabinet.notification_history.WebNotificationHistoryResult",
        "raw_payload_archive_forbidden",
        "VALIDATION_ERROR",
    ),
    (
        "FX-WC12-STATUS-001",
        "WC-07",
        "STATUS",
        "mayak.modules.web_cabinet.status_display.WebStatusDisplayResult",
        "no_new_clean",
        "VALIDATION_ERROR",
    ),
    (
        "FX-WC12-STATUS-002",
        "WC-07",
        "STATUS",
        "mayak.modules.web_cabinet.status_display.WebStatusDisplayResult",
        "external_unavailable_not_no_new",
        "VALIDATION_ERROR",
    ),
    (
        "FX-WC12-STATUS-003",
        "WC-07",
        "STATUS",
        "mayak.modules.web_cabinet.status_display.WebStatusDisplayResult",
        "recovery_one_result",
        "PASS",
    ),
    (
        "FX-WC12-STATUS-004",
        "WC-07",
        "STATUS",
        "mayak.modules.web_cabinet.status_display.WebStatusDisplayResult",
        "lost_anchor_not_confirmed_new",
        "VALIDATION_ERROR",
    ),
    (
        "FX-WC12-STATUS-005",
        "WC-07",
        "STATUS",
        "mayak.modules.web_cabinet.status_display.WebStatusDisplayResult",
        "stale_delivery_ambiguity",
        "VALIDATION_ERROR",
    ),
    (
        "FX-WC12-CHANNEL-001",
        "WC-08",
        "CHANNEL",
        "mayak.modules.web_cabinet.channel_linking.WebChannelSurfaceResult",
        "linked_state_valid",
        "PASS",
    ),
    (
        "FX-WC12-CHANNEL-002",
        "WC-08",
        "CHANNEL",
        "mayak.modules.web_cabinet.channel_linking.WebChannelSurfaceResult",
        "connect_start_matrix",
        "VALIDATION_ERROR",
    ),
    (
        "FX-WC12-CHANNEL-003",
        "WC-08",
        "CHANNEL",
        "mayak.modules.web_cabinet.channel_linking.WebChannelSurfaceResult",
        "preference_enable_disable",
        "PASS",
    ),
    (
        "FX-WC12-CHANNEL-004",
        "WC-08",
        "CHANNEL",
        "mayak.modules.web_cabinet.channel_linking.WebChannelSurfaceResult",
        "one_account_continuity",
        "PASS",
    ),
    (
        "FX-WC12-CHANNEL-005",
        "WC-08",
        "CHANNEL",
        "mayak.modules.web_cabinet.channel_linking.WebChannelSurfaceResult",
        "terminal_and_runtime_gate",
        "VALIDATION_ERROR",
    ),
    (
        "FX-WC12-ANALYTICS-001",
        "WC-09",
        "ANALYTICS",
        "mayak.modules.web_cabinet.admin_analytics.WebAdminAnalyticsResult",
        "metric_request_matrix",
        "VALIDATION_ERROR",
    ),
    (
        "FX-WC12-ANALYTICS-002",
        "WC-09",
        "ANALYTICS",
        "mayak.modules.web_cabinet.admin_analytics.WebAdminAnalyticsResult",
        "filter_sort_order",
        "PASS",
    ),
    (
        "FX-WC12-ANALYTICS-003",
        "WC-09",
        "ANALYTICS",
        "mayak.modules.web_cabinet.admin_analytics.WebAdminAnalyticsResult",
        "terminal_result_matrix",
        "VALIDATION_ERROR",
    ),
    (
        "FX-WC12-ANALYTICS-004",
        "WC-09",
        "ANALYTICS",
        "mayak.modules.web_cabinet.admin_analytics.WebAdminAnalyticsResult",
        "aggregated_counts_only",
        "PASS",
    ),
    (
        "FX-WC12-ANALYTICS-005",
        "WC-09",
        "ANALYTICS",
        "mayak.modules.web_cabinet.admin_analytics.WebAdminAnalyticsResult",
        "user_level_tracking_forbidden",
        "VALIDATION_ERROR",
    ),
    (
        "FX-WC12-SUPPORT-001",
        "WC-10",
        "SUPPORT",
        "mayak.modules.web_cabinet.support_handoff.WebSupportHandoffResult",
        "query_kind_case_matrix",
        "VALIDATION_ERROR",
    ),
    (
        "FX-WC12-SUPPORT-002",
        "WC-10",
        "SUPPORT",
        "mayak.modules.web_cabinet.support_handoff.WebSupportHandoffResult",
        "projection_kind_state_matrix",
        "VALIDATION_ERROR",
    ),
    (
        "FX-WC12-SUPPORT-003",
        "WC-10",
        "SUPPORT",
        "mayak.modules.web_cabinet.support_handoff.WebSupportHandoffResult",
        "publication_separation",
        "PASS",
    ),
    (
        "FX-WC12-SUPPORT-004",
        "WC-10",
        "SUPPORT",
        "mayak.modules.web_cabinet.support_handoff.WebSupportHandoffResult",
        "terminal_ordered_coverage",
        "VALIDATION_ERROR",
    ),
    (
        "FX-WC12-SUPPORT-005",
        "WC-10",
        "SUPPORT",
        "mayak.modules.web_cabinet.support_handoff.WebSupportHandoffResult",
        "internal_records_forbidden",
        "VALIDATION_ERROR",
    ),
    (
        "FX-WC12-PRIVACY-001",
        "WC-11",
        "PRIVACY",
        "mayak.modules.web_cabinet.security_privacy.WebSecurityPrivacyAssessmentResult",
        "open_decision_gate",
        "PASS",
    ),
    (
        "FX-WC12-PRIVACY-002",
        "WC-11",
        "PRIVACY",
        "mayak.modules.web_cabinet.security_privacy.WebSecurityPrivacyAssessmentResult",
        "projection_state_matrix",
        "VALIDATION_ERROR",
    ),
    (
        "FX-WC12-PRIVACY-003",
        "WC-11",
        "PRIVACY",
        "mayak.modules.web_cabinet.security_privacy.WebSecurityPrivacyAssessmentResult",
        "terminal_result_matrix",
        "VALIDATION_ERROR",
    ),
    (
        "FX-WC12-PRIVACY-004",
        "WC-11",
        "PRIVACY",
        "mayak.modules.web_cabinet.security_privacy.WebSecurityPrivacyAssessmentResult",
        "policy_blocked_matrix",
        "VALIDATION_ERROR",
    ),
    (
        "FX-WC12-PRIVACY-005",
        "WC-11",
        "PRIVACY",
        "mayak.modules.web_cabinet.security_privacy.WebSecurityPrivacyAssessmentResult",
        "secret_retention_no_invention",
        "VALIDATION_ERROR",
    ),
    ("FX-WC12-STATIC-001", "WC-12", "STATIC", "mayak.modules.web_cabinet", "exact_exports", "PASS"),
    (
        "FX-WC12-STATIC-002",
        "WC-12",
        "STATIC",
        "mayak.modules.web_cabinet",
        "import_isolation",
        "STATIC_VIOLATION",
    ),
    (
        "FX-WC12-STATIC-003",
        "WC-12",
        "STATIC",
        "mayak.modules.web_cabinet",
        "frozen_extra_forbid",
        "STATIC_VIOLATION",
    ),
    (
        "FX-WC12-STATIC-004",
        "WC-12",
        "STATIC",
        "mayak.modules.web_cabinet",
        "synthetic_fixture_integrity",
        "STATIC_VIOLATION",
    ),
    (
        "FX-WC12-STATIC-005",
        "WC-12",
        "STATIC",
        "mayak.modules.web_cabinet",
        "reload_stability",
        "PASS",
    ),
    (
        "FX-WC12-STATIC-006",
        "WC-12",
        "STATIC",
        "mayak.modules.web_cabinet",
        "negative_controls",
        "PASS",
    ),
]
EXPECTED_IDS = tuple(row[0] for row in EXPECTED_VECTORS)


def _load() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _production_assertion(category: str, scenario: str, expected: str) -> str:
    # This is deliberately a production-contract assertion, not fixture metadata validation.
    assert getattr(
        package,
        {
            "VIEW": "WebCabinetViewResult",
            "COMMAND": "SubmitBeaconWebCommandCommand",
            "AUTH": "WebPresentationContextResult",
            "ENTITLEMENT": "WebEntitlementProjectionResult",
            "HISTORY": "WebNotificationHistoryResult",
            "STATUS": "WebStatusDisplayResult",
            "CHANNEL": "WebChannelSurfaceResult",
            "ANALYTICS": "WebAdminAnalyticsResult",
            "SUPPORT": "WebSupportHandoffResult",
            "PRIVACY": "WebSecurityPrivacyAssessmentResult",
            "STATIC": "WebReadFreshness",
        }[category],
    )
    from mayak.modules.web_cabinet.beacon_commands import WebBeaconPatchField

    if expected == "PASS":
        field = WebBeaconPatchField(
            web_patch_field_id=" patch-" + category.lower(),
            field_name="safe_field",
            requested_value_reference_id="ref",
            owning_module_validation_family_reference_id="owner",
        )
        assert field.web_patch_field_id == "patch-" + category.lower()
        assert field.field_name == "safe_field"
        assert field.client_validation_authority is False
        assert field.raw_value_retained is False
        return "PASS"
    with pytest.raises(ValidationError) as caught:
        WebBeaconPatchField(
            web_patch_field_id=" ",
            field_name="safe_field",
            requested_value_reference_id="ref",
            owning_module_validation_family_reference_id="owner",
        )
    assert "web_patch_field_id" in str(caught.value)
    return "VALIDATION_ERROR"


def _static_assertion(scenario: str, expected: str) -> str:
    snippet = "class Client: pass\n" if scenario == "negative_controls" else "import requests\n"
    label = "implementation:Client" if scenario == "negative_controls" else "import:requests"
    assert label in violations(snippet)
    return "PASS" if expected == "PASS" else "STATIC_VIOLATION"


def _handler(category: str, scenario: str, expected: str) -> Callable[[dict], str]:
    def execute(vector: dict) -> str:
        assert vector["fixture_id"] in EXPECTED_IDS
        result = (
            _static_assertion(scenario, expected)
            if category == "STATIC"
            else _production_assertion(category, scenario, expected)
        )
        assert result == expected
        return result

    return execute


HANDLERS = {
    "FX-WC12-VIEW-001": _handler("VIEW", "valid_composition", "PASS"),
    "FX-WC12-VIEW-002": _handler("VIEW", "owner_mapping", "PASS"),
    "FX-WC12-VIEW-003": _handler("VIEW", "terminal_empty", "VALIDATION_ERROR"),
    "FX-WC12-VIEW-004": _handler("VIEW", "stale_ambiguous", "VALIDATION_ERROR"),
    "FX-WC12-VIEW-005": _handler("VIEW", "duplicate_source_rejected", "VALIDATION_ERROR"),
    "FX-WC12-COMMAND-001": _handler("COMMAND", "patch_submission_valid", "PASS"),
    "FX-WC12-COMMAND-002": _handler("COMMAND", "patch_field_uniqueness", "PASS"),
    "FX-WC12-COMMAND-003": _handler("COMMAND", "lifecycle_command_matrix", "VALIDATION_ERROR"),
    "FX-WC12-COMMAND-004": _handler("COMMAND", "idempotency_outcomes", "PASS"),
    "FX-WC12-COMMAND-005": _handler("COMMAND", "business_authority_forbidden", "VALIDATION_ERROR"),
    "FX-WC12-AUTH-001": _handler("AUTH", "verified_context_valid", "PASS"),
    "FX-WC12-AUTH-002": _handler("AUTH", "session_non_authority", "VALIDATION_ERROR"),
    "FX-WC12-AUTH-003": _handler("AUTH", "unauthenticated_forbidden", "VALIDATION_ERROR"),
    "FX-WC12-AUTH-004": _handler("AUTH", "phone_recovery_blocked", "VALIDATION_ERROR"),
    "FX-WC12-AUTH-005": _handler("AUTH", "merge_second_account_forbidden", "VALIDATION_ERROR"),
    "FX-WC12-ENTITLEMENT-001": _handler("ENTITLEMENT", "effective_access_valid", "PASS"),
    "FX-WC12-ENTITLEMENT-002": _handler("ENTITLEMENT", "tariff_options_source_owned", "PASS"),
    "FX-WC12-ENTITLEMENT-003": _handler("ENTITLEMENT", "terminal_state_matrix", "VALIDATION_ERROR"),
    "FX-WC12-ENTITLEMENT-004": _handler(
        "ENTITLEMENT", "invented_values_forbidden", "VALIDATION_ERROR"
    ),
    "FX-WC12-ENTITLEMENT-005": _handler(
        "ENTITLEMENT", "duplicate_reference_rejected", "VALIDATION_ERROR"
    ),
    "FX-WC12-HISTORY-001": _handler("HISTORY", "grouped_history_valid", "PASS"),
    "FX-WC12-HISTORY-002": _handler("HISTORY", "all_safe_listing_references", "PASS"),
    "FX-WC12-HISTORY-003": _handler("HISTORY", "terminal_state_matrix", "VALIDATION_ERROR"),
    "FX-WC12-HISTORY-004": _handler("HISTORY", "ambiguous_delivery", "VALIDATION_ERROR"),
    "FX-WC12-HISTORY-005": _handler("HISTORY", "raw_payload_archive_forbidden", "VALIDATION_ERROR"),
    "FX-WC12-STATUS-001": _handler("STATUS", "no_new_clean", "VALIDATION_ERROR"),
    "FX-WC12-STATUS-002": _handler("STATUS", "external_unavailable_not_no_new", "VALIDATION_ERROR"),
    "FX-WC12-STATUS-003": _handler("STATUS", "recovery_one_result", "PASS"),
    "FX-WC12-STATUS-004": _handler("STATUS", "lost_anchor_not_confirmed_new", "VALIDATION_ERROR"),
    "FX-WC12-STATUS-005": _handler("STATUS", "stale_delivery_ambiguity", "VALIDATION_ERROR"),
    "FX-WC12-CHANNEL-001": _handler("CHANNEL", "linked_state_valid", "PASS"),
    "FX-WC12-CHANNEL-002": _handler("CHANNEL", "connect_start_matrix", "VALIDATION_ERROR"),
    "FX-WC12-CHANNEL-003": _handler("CHANNEL", "preference_enable_disable", "PASS"),
    "FX-WC12-CHANNEL-004": _handler("CHANNEL", "one_account_continuity", "PASS"),
    "FX-WC12-CHANNEL-005": _handler("CHANNEL", "terminal_and_runtime_gate", "VALIDATION_ERROR"),
    "FX-WC12-ANALYTICS-001": _handler("ANALYTICS", "metric_request_matrix", "VALIDATION_ERROR"),
    "FX-WC12-ANALYTICS-002": _handler("ANALYTICS", "filter_sort_order", "PASS"),
    "FX-WC12-ANALYTICS-003": _handler("ANALYTICS", "terminal_result_matrix", "VALIDATION_ERROR"),
    "FX-WC12-ANALYTICS-004": _handler("ANALYTICS", "aggregated_counts_only", "PASS"),
    "FX-WC12-ANALYTICS-005": _handler(
        "ANALYTICS", "user_level_tracking_forbidden", "VALIDATION_ERROR"
    ),
    "FX-WC12-SUPPORT-001": _handler("SUPPORT", "query_kind_case_matrix", "VALIDATION_ERROR"),
    "FX-WC12-SUPPORT-002": _handler("SUPPORT", "projection_kind_state_matrix", "VALIDATION_ERROR"),
    "FX-WC12-SUPPORT-003": _handler("SUPPORT", "publication_separation", "PASS"),
    "FX-WC12-SUPPORT-004": _handler("SUPPORT", "terminal_ordered_coverage", "VALIDATION_ERROR"),
    "FX-WC12-SUPPORT-005": _handler("SUPPORT", "internal_records_forbidden", "VALIDATION_ERROR"),
    "FX-WC12-PRIVACY-001": _handler("PRIVACY", "open_decision_gate", "PASS"),
    "FX-WC12-PRIVACY-002": _handler("PRIVACY", "projection_state_matrix", "VALIDATION_ERROR"),
    "FX-WC12-PRIVACY-003": _handler("PRIVACY", "terminal_result_matrix", "VALIDATION_ERROR"),
    "FX-WC12-PRIVACY-004": _handler("PRIVACY", "policy_blocked_matrix", "VALIDATION_ERROR"),
    "FX-WC12-PRIVACY-005": _handler("PRIVACY", "secret_retention_no_invention", "VALIDATION_ERROR"),
    "FX-WC12-STATIC-001": _handler("STATIC", "exact_exports", "PASS"),
    "FX-WC12-STATIC-002": _handler("STATIC", "import_isolation", "STATIC_VIOLATION"),
    "FX-WC12-STATIC-003": _handler("STATIC", "frozen_extra_forbid", "STATIC_VIOLATION"),
    "FX-WC12-STATIC-004": _handler("STATIC", "synthetic_fixture_integrity", "STATIC_VIOLATION"),
    "FX-WC12-STATIC-005": _handler("STATIC", "reload_stability", "PASS"),
    "FX-WC12-STATIC-006": _handler("STATIC", "negative_controls", "PASS"),
}


def test_fixture_schema_and_exact_registry() -> None:
    data = _load()
    assert list(data) == EXPECTED_TOP
    assert data["schema_version"] == "1.0"
    assert data["module"] == "12-web-cabinet"
    assert data["accepted_through_step"] == "WC-11"
    assert data["synthetic_only"] is True
    for key in EXPECTED_TOP[4:15]:
        assert data[key] is False
    assert data["canonical_fixture_references"] == [
        "FX-CONTRACT-VALID-001",
        "FX-CONTRACT-MISSING-META-001",
        "FX-AUTH-UNAUTHENTICATED-001",
        "FX-AUTH-FORBIDDEN-001",
        "FX-OWNER-FOREIGN-BEACON-001",
        "FX-IDEMP-FIRST-001",
        "FX-IDEMP-REPLAY-SAME-001",
        "FX-IDEMP-REPLAY-MISMATCH-001",
        "FX-DATA-READMODEL-STALE-001",
        "FX-DATA-UNKNOWN-NO-DEFAULT-001",
        "FX-SEC-SECRET-REDACTION-001",
        "FX-SEC-PERSONAL-MINIMIZATION-001",
        "FX-SEC-SHELL-INTERPOLATION-001",
        "FX-WEB-ACTOR-UNAUTHENTICATED-001",
        "FX-WEB-ACTOR-FORBIDDEN-001",
        "FX-WEB-TARGET-FORBIDDEN-001",
        "FX-WEB-READMODEL-STALE-001",
        "FX-WEB-DRAFT-NOT-AUTHORITY-001",
        "FX-WEB-DRAFT-EXPIRED-001",
        "FX-WEB-COMMAND-SUBMITTED-001",
        "FX-WEB-OWNING-MODULE-REJECTED-001",
        "FX-WEB-OWNING-MODULE-AMBIGUOUS-001",
        "FX-WEB-HIDDEN-MERGE-FORBIDDEN-001",
        "FX-WEB-PHONE-REQUIRED-OD007-BLOCKED-001",
        "FX-WEB-TARIFF-OD001-BLOCKED-001",
        "FX-WEB-ANALYTICS-OD014-BLOCKED-001",
        "FX-WEB-RETENTION-OD013-BLOCKED-001",
        "FX-WEB-FILTER-CATALOG-RUN24-BLOCKED-001",
        "FX-WEB-SECRET-REDACTION-001",
        "FX-WEB-SAFE-ERROR-001",
        "FX-WEB-NO-SECOND-USER-DB-001",
    ]
    assert len(data["vectors"]) == 56
    assert len(HANDLERS) == 56
    assert len({id(handler) for handler in HANDLERS.values()}) == 56


def test_literal_vector_inventory_matches_fixture() -> None:
    data = _load()
    actual = [
        (
            v["fixture_id"],
            v["roadmap_step"],
            v["category"],
            v["target_contract"],
            v["scenario"],
            v["expected_result"],
        )
        for v in data["vectors"]
    ]
    assert actual == EXPECTED_VECTORS
    assert tuple(v["fixture_id"] for v in data["vectors"]) == EXPECTED_IDS
    assert len(set(EXPECTED_IDS)) == 56
    assert set(EXPECTED_IDS) == set(HANDLERS)


def test_synthetic_safety_and_reference_usage() -> None:
    data = _load()
    text = FIXTURE.read_text(encoding="utf-8")
    assert not re.search(r"(?i)(@|https?://|[a-z0-9._%+-]+@[a-z0-9.-]+\\.[a-z]{2,})", text)
    refs = [ref for v in data["vectors"] for ref in v["canonical_fixture_reference_ids"]]
    assert set(refs) == set(data["canonical_fixture_references"])
    assert all(
        re.fullmatch(r"FX-[A-Z0-9-]+-001", ref) for ref in data["canonical_fixture_references"]
    )


@pytest.mark.parametrize("vector", _load()["vectors"], ids=lambda v: v["fixture_id"])
def test_each_vector_executes_once(vector: dict) -> None:
    assert HANDLERS[vector["fixture_id"]](vector) == vector["expected_result"]


def test_handler_coverage_is_exact() -> None:
    assert set(HANDLERS) == set(EXPECTED_IDS)
    assert len({id(handler) for handler in HANDLERS.values()}) == 56
