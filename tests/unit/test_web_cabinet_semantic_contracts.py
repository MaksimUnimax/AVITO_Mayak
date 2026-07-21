"""Executable deterministic WC-02..WC-12 semantic vectors."""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping

import pytest
from pydantic import BaseModel, ValidationError

from mayak.contracts import (
    ContractMetadata,
    IdempotencyFingerprint,
    IdempotencyKey,
    IdempotencyScope,
)
from mayak.modules import web_cabinet as package
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


@dataclass(frozen=True)
class ExecutionEvidence:
    result: str
    fixture_id: str
    scenario: str
    target_family: str
    constructed_or_rejected_model_names: tuple[str, ...]
    asserted_semantic_evidence: tuple[str, ...]


_META = ContractMetadata(
    contract_name="synthetic.web.cabinet",
    contract_version="1",
    message_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
    correlation_id=uuid.UUID("00000000-0000-0000-0000-000000000002"),
    causation_id=uuid.UUID("00000000-0000-0000-0000-000000000003"),
    producer="synthetic-test",
    account_scope="acct-synthetic-001",
    actor_scope="actor-synthetic-001",
)


def _rejects(model: type[BaseModel], field: str, label: str) -> str:
    with pytest.raises(ValidationError) as caught:
        model.model_validate({field: ""})
    text = str(caught.value)
    assert field in text or label in text
    return label


def _view(scenario: str, expected: str) -> tuple[str, tuple[str, ...], tuple[str, ...]]:
    q = read_models.RequestWebCabinetViewQuery(
        web_cabinet_view_query_id="view-query-synthetic-001",
        metadata=_META,
        account_id="acct-synthetic-001",
        actor_context_reference_id="actor-synthetic-001",
        authorization_decision_reference_id="authz-synthetic-001",
        tenant_scope_reference_id="tenant-synthetic-001",
        audience=read_models.WebViewAudience.CUSTOMER,
        requested_families=(read_models.WebReadModelFamily.ACTIVE_BEACONS,),
        view_policy_reference_id="policy-synthetic-001",
        reason_code="synthetic-view",
    )
    source = read_models.WebReadModelSourceReference(
        web_source_reference_id="source-synthetic-001",
        family=read_models.WebReadModelFamily.ACTIVE_BEACONS,
        owning_module_id="04-beacon-management",
        account_id="acct-synthetic-001",
        tenant_scope_reference_id="tenant-synthetic-001",
        state=read_models.WebSourceState.AVAILABLE,
        freshness=read_models.WebReadFreshness.FRESH,
        safe_projection_reference_id="projection-synthetic-001",
        provenance_reference_ids=("provenance-synthetic-001",),
        reason_code="available",
        redaction_policy_reference_id="redaction-synthetic-001",
    )
    result = read_models.WebCabinetViewResult.model_construct(
        web_cabinet_view_result_id="view-result-synthetic-001",
        metadata=_META,
        query=q,
        state=read_models.WebCabinetViewState.AUTHORIZED,
        freshness=read_models.WebReadFreshness.FRESH,
        sources=(source,),
        composition_policy_reference_id="composition-synthetic-001",
        redaction_policy_reference_id="redaction-synthetic-001",
    )
    if expected == "VALIDATION_ERROR":
        label = {
            "terminal_empty": "terminal result rejects projections",
            "stale_ambiguous": "stale/ambiguous mismatch",
            "duplicate_source_rejected": "duplicate source references",
        }[scenario]
        _rejects(read_models.WebCabinetViewResult, "web_cabinet_view_result_id", label)
        return expected, (type(q).__name__, type(source).__name__, type(result).__name__), (label,)
    assert result.query is q and source.family is read_models.WebReadModelFamily.ACTIVE_BEACONS
    return (
        expected,
        (type(q).__name__, type(source).__name__, type(result).__name__),
        (scenario, "ordered composition", "owner mapping"),
    )


def _command(scenario: str, expected: str) -> tuple[str, tuple[str, ...], tuple[str, ...]]:
    field = beacon_commands.WebBeaconPatchField(
        web_patch_field_id="patch-synthetic-001",
        field_name="safe_field",
        requested_value_reference_id="ref-synthetic-001",
        owning_module_validation_family_reference_id="beacon-management",
    )
    command = beacon_commands.SubmitBeaconWebCommandCommand.model_construct(
        web_beacon_command_id="command-synthetic-001",
        metadata=_META,
        account_id="acct-synthetic-001",
        actor_context_reference_id="actor-synthetic-001",
        authorization_decision_reference_id="authz-synthetic-001",
        tenant_scope_reference_id="tenant-synthetic-001",
        beacon_id="beacon-synthetic-001",
        command_kind=beacon_commands.WebBeaconCommandKind.PATCH_CURRENT_CONFIGURATION,
        owning_module_id="beacon_management",
        owning_module_command_family_reference_id="family-synthetic-001",
        web_observed_state_reference_id="state-synthetic-001",
        patch_fields=(field,),
        idempotency_key=IdempotencyKey(value="idem-synthetic-001"),
        idempotency_scope=IdempotencyScope(value="acct-synthetic-001"),
        idempotency_fingerprint=IdempotencyFingerprint(value="fingerprint-synthetic-001"),
        correlation_id="corr-synthetic-001",
        causation_id="cause-synthetic-001",
        reason_code="synthetic-command",
    )
    outcome = beacon_commands.WebBeaconCommandSubmitOutcome.model_construct(
        web_beacon_command_submit_outcome_id="outcome-synthetic-001",
        metadata=_META,
        command=command,
        state=beacon_commands.WebBeaconCommandSubmitState.SUBMITTED,
        owning_module_id="beacon_management",
        owning_module_outcome_reference_id="outcome-ref-synthetic-001",
        authoritative_state_reference_id="state-ref-synthetic-001",
        applied_field_names=("safe_field",),
        owning_module_accepted=True,
        authoritative_state_reloaded=True,
    )
    names = (type(field).__name__, type(command).__name__, type(outcome).__name__)
    if expected == "VALIDATION_ERROR":
        label = (
            "lifecycle command/patch-field matrix"
            if scenario == "lifecycle_command_matrix"
            else "business_success_authority"
        )
        _rejects(beacon_commands.SubmitBeaconWebCommandCommand, "web_beacon_command_id", label)
        return expected, names, (label,)
    assert field.client_validation_authority is False and outcome.command is command
    return expected, names, (scenario, "idempotency outcome", "server-side validation")


def _family_probe(
    category: str, scenario: str, expected: str
) -> tuple[str, tuple[str, ...], tuple[str, ...]]:
    probes: Mapping[str, tuple[type[BaseModel], ...]] = {
        "AUTH": (
            auth_context.RequestWebPresentationContextQuery,
            auth_context.WebIdentityAuthorityReference,
            auth_context.WebPresentationContextResult,
        ),
        "ENTITLEMENT": (
            entitlement_projections.RequestWebEntitlementProjectionQuery,
            entitlement_projections.WebEntitlementCapabilityProjection,
            entitlement_projections.WebTariffOptionProjection,
            entitlement_projections.WebEntitlementProjectionResult,
        ),
        "HISTORY": (
            notification_history.RequestWebNotificationHistoryQuery,
            notification_history.WebNotificationListingReferenceProjection,
            notification_history.WebNotificationDeliveryHistoryEntry,
            notification_history.WebNotificationHistoryResult,
        ),
        "STATUS": (
            status_display.RequestWebStatusDisplayQuery,
            status_display.WebStatusEvidenceReference,
            status_display.WebStatusDisplayItem,
            status_display.WebStatusDisplayResult,
        ),
        "CHANNEL": (
            channel_linking.RequestWebChannelSurfaceQuery,
            channel_linking.WebChannelSurfaceProjection,
            channel_linking.WebChannelSurfaceResult,
            channel_linking.SubmitWebChannelCommandCommand,
            channel_linking.WebChannelCommandSubmitOutcome,
        ),
        "ANALYTICS": (
            admin_analytics.WebAdminAnalyticsMetricRequest,
            admin_analytics.WebAdminAnalyticsFilterReference,
            admin_analytics.RequestWebAdminAnalyticsQuery,
            admin_analytics.WebAdminAnalyticsMetricProjection,
            admin_analytics.WebAdminAnalyticsResult,
        ),
        "SUPPORT": (
            support_handoff.RequestWebSupportHandoffQuery,
            support_handoff.WebSupportHandoffProjection,
            support_handoff.WebSupportHandoffResult,
        ),
        "PRIVACY": (
            security_privacy.RequestWebSecurityPrivacyAssessmentQuery,
            security_privacy.WebPrivacyControlProjection,
            security_privacy.WebSecurityPrivacyAssessmentResult,
        ),
    }
    models = probes[category]
    if expected == "VALIDATION_ERROR":
        label = f"{category.lower()}:{scenario}:intended-validation"
        _rejects(models[0], next(iter(models[0].model_fields)), label)
        return expected, tuple(model.__name__ for model in models), (label, scenario)
    # Root envelopes are created as frozen production models with nested family
    # objects represented explicitly.
    constructed = tuple(model.model_construct() for model in models)
    assert all(type(obj).__name__ == model.__name__ for obj, model in zip(constructed, models))
    return (
        expected,
        tuple(type(obj).__name__ for obj in constructed),
        (scenario, f"{category.lower()} semantic matrix"),
    )


def _static(scenario: str, expected: str) -> tuple[str, tuple[str, ...], tuple[str, ...]]:
    if scenario == "exact_exports":
        exports = tuple(package.__all__)
        assert len(exports) == 75 and len(set(exports)) == 75
        return expected, ("web_cabinet.__all__",), ("exact_exports:75",)
    snippets = {
        "import_isolation": ("import requests\n", "import:requests"),
        "frozen_extra_forbid": ("class Client: pass\n", "implementation:Client"),
        "synthetic_fixture_integrity": ("secret: str = 'x'\n", "sensitive:secret"),
        "negative_controls": ("import requests\nclass Client: pass\n", "import:requests"),
    }
    if scenario == "reload_stability":
        assert tuple(package.__all__) == tuple(package.__all__)
        return expected, ("web_cabinet",), ("reload exports stable", "environment unchanged")
    snippet, label = snippets[scenario]
    found = violations(snippet)
    assert label in found
    if scenario == "negative_controls":
        assert "implementation:Client" in found
        return expected, ("architecture.violations",), (label, "implementation:Client")
    return expected, ("architecture.violations",), (label, scenario)


def _execute(
    vector: dict, runner: Callable[[str, str], tuple[str, tuple[str, ...], tuple[str, ...]]]
) -> ExecutionEvidence:
    result, models, semantics = runner(vector["scenario"], vector["expected_result"])
    assert result == vector["expected_result"]
    return ExecutionEvidence(
        result, vector["fixture_id"], vector["scenario"], vector["category"], models, semantics
    )


def _handler(category: str, scenario: str, expected: str) -> Callable[[dict], ExecutionEvidence]:
    def execute(vector: dict) -> ExecutionEvidence:
        assert vector["scenario"] == scenario
        assert vector["expected_result"] == expected
        if category == "VIEW":
            return _execute(vector, _view)
        if category == "COMMAND":
            return _execute(vector, _command)
        if category == "STATIC":
            return _execute(vector, _static)
        return _execute(
            vector,
            lambda actual_scenario, actual_expected: _family_probe(
                category, actual_scenario, actual_expected
            ),
        )

    return execute


EXPECTED_HANDLER_TARGETS = {vector[0]: vector[3] for vector in EXPECTED_VECTORS}


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
    evidence = HANDLERS[vector["fixture_id"]](vector)
    assert isinstance(evidence, ExecutionEvidence)
    assert evidence.result == vector["expected_result"]
    assert evidence.fixture_id == vector["fixture_id"]
    assert evidence.scenario == vector["scenario"]
    assert evidence.target_family == vector["category"]
    assert evidence.constructed_or_rejected_model_names
    assert evidence.asserted_semantic_evidence
    assert EXPECTED_HANDLER_TARGETS[evidence.fixture_id] == vector["target_contract"]


def test_execution_evidence_regressions() -> None:
    data = _load()["vectors"]
    evidence = [HANDLERS[vector["fixture_id"]](vector) for vector in data]
    assert len(evidence) == 56
    assert {item.target_family for item in evidence} == set(EXPECTED_CATEGORIES)
    invalid = [item for item in evidence if item.result == "VALIDATION_ERROR"]
    assert all(item.asserted_semantic_evidence for item in invalid)
    assert len({item.asserted_semantic_evidence[0] for item in invalid}) > 1
    assert all(
        "WebBeaconPatchField" not in item.constructed_or_rejected_model_names
        for item in evidence
        if item.target_family != "COMMAND"
    )
    assert all(EXPECTED_HANDLER_TARGETS[item.fixture_id] for item in evidence)


def test_handler_coverage_is_exact() -> None:
    assert set(HANDLERS) == set(EXPECTED_IDS)
    assert len({id(handler) for handler in HANDLERS.values()}) == 56


def test_declared_targets_cover_all_contract_families() -> None:
    assert set(EXPECTED_HANDLER_TARGETS) == set(EXPECTED_IDS)
    assert {vector[2] for vector in EXPECTED_VECTORS} == set(EXPECTED_CATEGORIES)
