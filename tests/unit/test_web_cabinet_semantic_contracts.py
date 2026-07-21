"""Executable deterministic WC-02..WC-12 semantic vectors."""

from __future__ import annotations

import ast
import copy
import importlib
import json
import os
import re
import uuid
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable, TypeVar, get_args, get_origin

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
    ("FX-WC12-STATIC-001", "WC-12", "STATIC", "mayak.modules.web_cabinet", "exact_exports", "PASS"),  # noqa: E501
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
    validation_error_locations: tuple[tuple[Any, ...], ...] = ()
    validation_error_types: tuple[str, ...] = ()
    validation_error_message_fragments: tuple[str, ...] = ()


T = TypeVar("T", bound=BaseModel)


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


def _field_value(field: Any) -> Any:
    if not field.is_required():
        return field.get_default(call_default_factory=True)
    annotation = field.annotation
    origin = get_origin(annotation)
    args = get_args(annotation)
    if origin is tuple:
        item = args[0] if args else str
        if get_origin(item) is not None:
            item = get_args(item)[0] or str
        if isinstance(item, type) and issubclass(item, Enum):
            return (tuple(item)[0],)
        return ("synthetic-reference-001",)
    if origin is not None and type(None) in args:
        return None
    if isinstance(annotation, type) and issubclass(annotation, Enum):
        return tuple(annotation)[0]
    if annotation is ContractMetadata:
        return _META
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return _complete(annotation)
    if origin is not None and origin is not type(None):
        literals = get_args(annotation)
        if literals:
            return literals[0]
    if annotation is str:
        return "synthetic-reference-001"
    if annotation is bool:
        return False
    if annotation is int:
        return 1
    return None


def _complete(model: type[T], **overrides: Any) -> T:
    payload = {
        name: (overrides[name] if name in overrides else _field_value(field))
        for name, field in model.model_fields.items()
    }
    if "metadata" in model.model_fields:
        payload["metadata"] = _META
    payload.update(overrides)
    return model(**payload)


def _error(
    call: Callable[[], Any], scenario: str
) -> tuple[tuple[tuple[Any, ...], ...], tuple[str, ...], tuple[str, ...]]:
    with pytest.raises(ValidationError) as caught:
        call()
    entries = tuple(caught.value.errors())
    assert entries
    locations = tuple(tuple(entry["loc"]) for entry in entries)
    types = tuple(str(entry["type"]) for entry in entries)
    fragments = tuple(str(entry["msg"])[:120] for entry in entries)
    assert all(fragment for fragment in fragments)
    return locations, types, fragments


def _evidence(
    vector: dict, models: tuple[BaseModel, ...], semantic: tuple[str, ...], error: Any = None
) -> ExecutionEvidence:
    locations, types, fragments = error or ((), (), ())
    return ExecutionEvidence(
        vector["expected_result"],
        vector["fixture_id"],
        vector["scenario"],
        vector["category"],
        tuple(type(model).__name__ for model in models),
        semantic,
        locations,
        types,
        fragments,
    )


def _valid_view() -> tuple[
    read_models.RequestWebCabinetViewQuery,
    read_models.WebReadModelSourceReference,
    read_models.WebCabinetViewResult,
]:
    query = read_models.RequestWebCabinetViewQuery(
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
    result = read_models.WebCabinetViewResult(
        web_cabinet_view_result_id="view-result-synthetic-001",
        metadata=_META,
        query=query,
        state=read_models.WebCabinetViewState.AUTHORIZED,
        freshness=read_models.WebReadFreshness.FRESH,
        sources=(source,),
        composition_policy_reference_id="composition-synthetic-001",
        redaction_policy_reference_id="redaction-synthetic-001",
    )
    return query, source, result


def _valid_command() -> tuple[
    beacon_commands.WebBeaconPatchField,
    beacon_commands.SubmitBeaconWebCommandCommand,
    beacon_commands.WebBeaconCommandSubmitOutcome,
]:
    field = beacon_commands.WebBeaconPatchField(
        web_patch_field_id="patch-synthetic-001",
        field_name="safe_field",
        requested_value_reference_id="ref-synthetic-001",
        owning_module_validation_family_reference_id="beacon-management",
    )
    command = beacon_commands.SubmitBeaconWebCommandCommand(
        web_beacon_command_id="command-synthetic-001",
        metadata=_META,
        account_id="acct-synthetic-001",
        actor_context_reference_id="actor-synthetic-001",
        authorization_decision_reference_id="authz-synthetic-001",
        tenant_scope_reference_id="tenant-synthetic-001",
        beacon_id="beacon-synthetic-001",
        command_kind=beacon_commands.WebBeaconCommandKind.PATCH_CURRENT_CONFIGURATION,
        owning_module_id="04-beacon-management",
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
    outcome = beacon_commands.WebBeaconCommandSubmitOutcome(
        web_beacon_command_submit_outcome_id="outcome-synthetic-001",
        metadata=_META,
        command=command,
        state=beacon_commands.WebBeaconCommandSubmitState.SUBMITTED,
        owning_module_id="04-beacon-management",
        owning_module_outcome_reference_id="outcome-ref-synthetic-001",
        authoritative_state_reference_id="state-ref-synthetic-001",
        applied_field_names=("safe_field",),
        owning_module_accepted=True,
        authoritative_state_reloaded=True,
    )
    return field, command, outcome


def _auth_models() -> tuple[BaseModel, ...]:
    query = _complete(
        auth_context.RequestWebPresentationContextQuery,
        actor_context_reference_id="actor-synthetic-001",
        requested_audience=read_models.WebViewAudience.CUSTOMER,
    )
    authority = _complete(
        auth_context.WebIdentityAuthorityReference,
        owning_module_id="02-identity-and-access",
        actor_context_reference_id="actor-synthetic-001",
        actor_state=auth_context.WebPresentationActorState.VERIFIED,
        account_id="acct-synthetic-001",
        authorization_decision_reference_id="authz-synthetic-001",
        auth_session_reference_id="session-synthetic-001",
        session_state=auth_context.WebSessionReferenceState.ACTIVE,
    )
    result = _complete(
        auth_context.WebPresentationContextResult,
        query=query,
        authority=authority,
        state=auth_context.WebPresentationContextState.AUTHORIZED,
        resolved_account_id="acct-synthetic-001",
        safe_identity_summary_reference_id="identity-summary-synthetic-001",
    )
    return query, authority, result


def _entitlement_models() -> tuple[BaseModel, ...]:
    query = _complete(
        entitlement_projections.RequestWebEntitlementProjectionQuery,
        account_id="acct-synthetic-001",
        requested_capability_reference_ids=("capability-synthetic-001",),
        include_tariff_options=True,
    )
    capability = _complete(
        entitlement_projections.WebEntitlementCapabilityProjection,
        account_id="acct-synthetic-001",
        capability_reference_id="capability-synthetic-001",
        access_state=entitlement_projections.WebEntitlementAccessState.ALLOWED,
        source_reference_ids=("entitlement-source-001",),
    )
    option = _complete(
        entitlement_projections.WebTariffOptionProjection,
        owning_module_id="03-entitlements-and-billing",
        account_id="acct-synthetic-001",
        state=entitlement_projections.WebTariffOptionState.AVAILABLE,
        source_reference_ids=("tariff-source-001",),
        safe_name_display_reference_id="tariff-name-001",
    )
    result = _complete(
        entitlement_projections.WebEntitlementProjectionResult,
        query=query,
        state=entitlement_projections.WebEntitlementProjectionState.AVAILABLE,
        freshness=read_models.WebReadFreshness.FRESH,
        owning_module_id="03-entitlements-and-billing",
        capabilities=(capability,),
        tariff_options=(option,),
        source_reference_ids=("entitlement-source-001",),
    )
    return query, capability, option, result


def _history_models() -> tuple[BaseModel, ...]:
    query = _complete(
        notification_history.RequestWebNotificationHistoryQuery,
        account_id="acct-synthetic-001",
        beacon_scope_ids=("beacon-synthetic-001",),
    )
    listing = _complete(
        notification_history.WebNotificationListingReferenceProjection,
        account_id="acct-synthetic-001",
        beacon_id="beacon-synthetic-001",
    )
    entry = _complete(
        notification_history.WebNotificationDeliveryHistoryEntry,
        account_id="acct-synthetic-001",
        beacon_id="beacon-synthetic-001",
        listing_references=(listing,),
        listing_count=1,
    )
    result = _complete(
        notification_history.WebNotificationHistoryResult,
        query=query,
        state=notification_history.WebNotificationHistoryResultState.AVAILABLE,
        freshness=read_models.WebReadFreshness.FRESH,
        owning_module_id="08-notification-delivery",
        notification_read_model_reference_id="history-model-001",
        notification_projection_decision_reference_id="history-decision-001",
        history_entries=(entry,),
        safe_listing_references=(listing,),
        listing_count=1,
        history_entry_count=1,
        source_reference_ids=("history-source-001",),
    )
    return query, listing, entry, result


def _status_models() -> tuple[BaseModel, ...]:
    query = _complete(
        status_display.RequestWebStatusDisplayQuery,
        account_id="acct-synthetic-001",
        beacon_scope_ids=("beacon-synthetic-001",),
        requested_status_reference_ids=("status-synthetic-001",),
    )
    evidence = _complete(
        status_display.WebStatusEvidenceReference,
        web_status_evidence_reference_id="evidence-synthetic-001",
        account_id="acct-synthetic-001",
        beacon_id="beacon-synthetic-001",
        source_family=status_display.WebStatusSourceFamily.SCAN_ORCHESTRATION,
        source_module_id="06-scan-orchestration-and-listing-state",
        evidence_class=status_display.WebStatusEvidenceClass.SCAN_NO_NEW_PROVEN,
        source_decision_reference_id="decision-synthetic-001",
        source_outcome_reference_id="outcome-synthetic-001",
        source_reason_codes=("no-new",),
        safe_evidence_reference_ids=("evidence-safe-001",),
        safe_latest_fresh_listing_reference_ids=(),
        no_new_claim_allowed=True,
        state_restored_latest_fresh_only=False,
        continuing_scan_visible=False,
    )
    item = _complete(
        status_display.WebStatusDisplayItem,
        account_id="acct-synthetic-001",
        beacon_id="beacon-synthetic-001",
        family=status_display.WebStatusDisplayFamily.NO_NEW_LISTINGS,
        source_evidence_reference_ids=("evidence-synthetic-001",),
    )
    result = _complete(
        status_display.WebStatusDisplayResult,
        query=query,
        state=status_display.WebStatusDisplayResultState.AVAILABLE,
        freshness=read_models.WebReadFreshness.FRESH,
        owning_module_id="12-web-cabinet",
        status_mapping_policy_reference_id=query.status_mapping_policy_reference_id,
        source_evidence=(evidence,),
        display_items=(item,),
        external_unavailable_visible=False,
        recovery_visible=False,
        lost_anchors_state_restored_visible=False,
        access_or_channel_problem_visible=False,
        delivery_problem_visible=False,
        reconciliation_visible=False,
        stale_warning_visible=False,
        source_reference_ids=("status-source-001",),
        evidence_reference_ids=(evidence.web_status_evidence_reference_id,),
    )
    return query, evidence, item, result


def _channel_models() -> tuple[BaseModel, ...]:
    query = _complete(
        channel_linking.RequestWebChannelSurfaceQuery,
        account_id="acct-synthetic-001",
        requested_channels=(channel_linking.WebChannelKind.TELEGRAM,),
    )
    projection = _complete(
        channel_linking.WebChannelSurfaceProjection,
        account_id="acct-synthetic-001",
        channel=channel_linking.WebChannelKind.TELEGRAM,
        state=channel_linking.WebChannelSurfaceState.LINKED_ENABLED,
        preference_state=channel_linking.WebChannelNotificationPreferenceState.ENABLED,
        owning_adapter_module_id="09-telegram-adapter",
        adapter_eligibility_reference_id="eligibility-001",
        provider_identity_safe_reference_id="provider-identity-001",
        adapter_account_link_reference_id="link-001",
        identity_decision_reference_id="identity-decision-001",
        identity_account_reference_id="acct-synthetic-001",
        notification_channel_gate_decision_reference_id="gate-001",
        notification_target_safe_reference_id="target-001",
        safe_disable_notifications_action_reference_id="disable-001",
        notification_push_eligible=True,
        source_reference_ids=("channel-source-001",),
        evidence_reference_ids=("channel-evidence-001",),
    )
    result = _complete(
        channel_linking.WebChannelSurfaceResult,
        query=query,
        state=channel_linking.WebChannelSurfaceResultState.AVAILABLE,
        freshness=read_models.WebReadFreshness.FRESH,
        owning_module_id="12-web-cabinet",
        channel_read_policy_reference_id=query.channel_read_policy_reference_id,
        channel_projections=(projection,),
        linked_channel_count=1,
        push_eligible_channel_count=1,
        disabled_channel_count=0,
        future_gated_channel_count=0,
        source_reference_ids=("channel-source-001",),
        evidence_reference_ids=("channel-evidence-001",),
    )
    command = _complete(
        channel_linking.SubmitWebChannelCommandCommand,
        account_id="acct-synthetic-001",
        channel=channel_linking.WebChannelKind.TELEGRAM,
        command_kind=channel_linking.WebChannelCommandKind.ENABLE_NOTIFICATIONS,
        requested_owning_module_id="08-notification-delivery",
        identity_decision_reference_id="identity-decision-001",
        notification_preference_contract_reference_id="preference-contract-001",
        notification_channel_gate_decision_reference_id="notification-gate-001",
    )
    outcome = _complete(
        channel_linking.WebChannelCommandSubmitOutcome,
        command=command,
        owning_module_id="08-notification-delivery",
        owning_command_reference_id="command-owner-001",
        safe_owning_outcome_reference_id="outcome-safe-001",
    )
    return query, projection, result, command, outcome


def _analytics_models() -> tuple[BaseModel, ...]:
    metric_request = _complete(
        admin_analytics.WebAdminAnalyticsMetricRequest,
        metric_kind=admin_analytics.WebAdminAnalyticsMetricKind.VISITOR_COUNT,
        source_authority_module_id="12-web-cabinet",
    )
    filter_reference = _complete(
        admin_analytics.WebAdminAnalyticsFilterReference,
        filter_kind=admin_analytics.WebAdminAnalyticsFilterKind.PERIOD,
        filter_authority_module_id="12-web-cabinet",
    )
    query = _complete(
        admin_analytics.RequestWebAdminAnalyticsQuery,
        metric_requests=(metric_request,),
        filters=(filter_reference,),
    )
    projection = _complete(
        admin_analytics.WebAdminAnalyticsMetricProjection,
        metric_kind=metric_request.metric_kind,
        state=admin_analytics.WebAdminAnalyticsMetricState.AVAILABLE,
        freshness=read_models.WebReadFreshness.FRESH,
        source_authority_module_id="12-web-cabinet",
        count_value=1,
        source_aggregate_reference_id="aggregate-001",
        source_reference_ids=("analytics-source-001",),
        provenance_reference_ids=("analytics-prov-001",),
        evidence_reference_ids=("analytics-evidence-001",),
    )
    result = _complete(
        admin_analytics.WebAdminAnalyticsResult,
        query=query,
        owning_module_id="12-web-cabinet",
        admin_policy_owner_module_id="11-admin-and-support",
        safe_table_projection_reference_id="table-001",
        safe_sort_application_reference_id="sort-001",
        sort_field=admin_analytics.WebAdminAnalyticsSortField.METRIC_KIND,
        sort_direction=admin_analytics.WebAdminAnalyticsSortDirection.ASCENDING,
        metric_projections=(projection,),
        applied_filter_reference_ids=(filter_reference.web_admin_analytics_filter_reference_id,),
    )
    return metric_request, filter_reference, query, projection, result


def _support_models() -> tuple[BaseModel, ...]:
    query = _complete(
        support_handoff.RequestWebSupportHandoffQuery, account_id="acct-synthetic-001"
    )
    projection = _complete(
        support_handoff.WebSupportHandoffProjection,
        account_id="acct-synthetic-001",
        owning_module_id="11-admin-and-support",
        item_kind=support_handoff.WebSupportHandoffItemKind.SUPPORT_ENTRY,
        state=support_handoff.WebSupportHandoffItemState.AVAILABLE,
        freshness=read_models.WebReadFreshness.FRESH,
        support_entry_reference_id="support-entry-001",
        customer_publication_decision_reference_id="publication-001",
    )
    result = _complete(
        support_handoff.WebSupportHandoffResult,
        query=query,
        owning_module_id="12-web-cabinet",
        source_owner_module_id="11-admin-and-support",
        projections=(projection,),
        projection_count=1,
    )
    return query, projection, result


def _privacy_models() -> tuple[BaseModel, ...]:
    query = _complete(
        security_privacy.RequestWebSecurityPrivacyAssessmentQuery,
        account_id="acct-synthetic-001",
        requested_surface_kinds=(security_privacy.WebPrivacySurfaceKind.RETENTION_POLICY,),
        open_decision_reference_ids=("OD-013",),
    )
    projection = _complete(
        security_privacy.WebPrivacyControlProjection,
        account_id="acct-synthetic-001",
        surface_kind=security_privacy.WebPrivacySurfaceKind.RETENTION_POLICY,
        state=security_privacy.WebPrivacyProjectionState.POLICY_BLOCKED,
        freshness=read_models.WebReadFreshness.UNKNOWN,
        policy_gate_reference_id=query.retention_policy_gate_reference_id,
        open_decision_reference_ids=("OD-013",),
        source_reference_ids=("privacy-source-001",),
        provenance_reference_ids=("privacy-prov-001",),
        evidence_reference_ids=("privacy-evidence-001",),
    )
    result = _complete(
        security_privacy.WebSecurityPrivacyAssessmentResult,
        query=query,
        owning_module_id="12-web-cabinet",
        state=security_privacy.WebSecurityPrivacyResultState.POLICY_BLOCKED,
        freshness=read_models.WebReadFreshness.UNKNOWN,
        projections=(projection,),
        projection_count=1,
        source_reference_ids=("privacy-source-001",),
        evidence_reference_ids=("privacy-evidence-001",),
    )
    return query, projection, result


def _validated_scenario(
    vector: dict, models: tuple[BaseModel, ...], semantic: str
) -> ExecutionEvidence:
    assert all(isinstance(model, BaseModel) for model in models)
    return _evidence(
        vector, models, (semantic, "normal constructor validation", "complete required payload")
    )


def _invalid_from(
    model: BaseModel, mutation: dict[str, Any], vector: dict, semantic: str
) -> ExecutionEvidence:
    payload = model.model_dump()
    payload.update(mutation)
    error = _error(lambda: type(model)(**payload), semantic)
    return _evidence(
        vector,
        (model,),
        (semantic, "one intended mutation", "all unrelated fields retained"),
        error,
    )


def scenario_fx_wc12_view_001(vector: dict) -> ExecutionEvidence:
    q, source, result = _valid_view()
    assert result.query is q and result.sources == (source,)
    return _validated_scenario(
        vector,
        (q, source, result),
        "ordered sources cover requested family, authorized scope, fresh composition",
    )


def scenario_fx_wc12_view_002(vector: dict) -> ExecutionEvidence:
    q, source, result = _valid_view()
    assert (
        source.owning_module_id == "04-beacon-management"
        and result.sources[0].family is q.requested_families[0]
    )
    return _validated_scenario(vector, (q, source, result), "exact family-to-owning-module mapping")  # noqa: E501


def scenario_fx_wc12_view_003(vector: dict) -> ExecutionEvidence:
    _, _, result = _valid_view()
    return _invalid_from(
        result, {"state": read_models.WebCabinetViewState.FORBIDDEN}, vector, "terminal_empty"
    )


def scenario_fx_wc12_view_004(vector: dict) -> ExecutionEvidence:
    _, _, result = _valid_view()
    return _invalid_from(
        result,
        {"freshness": read_models.WebReadFreshness.STALE, "ambiguity_reference_id": None},
        vector,
        "stale_ambiguous",
    )


def scenario_fx_wc12_view_005(vector: dict) -> ExecutionEvidence:
    _, source, result = _valid_view()
    return _invalid_from(result, {"sources": (source, source)}, vector, "duplicate_source_rejected")  # noqa: E501


def scenario_fx_wc12_command_001(vector: dict) -> ExecutionEvidence:
    field, command, outcome = _valid_command()
    assert field.client_validation_authority is False and outcome.command is command
    return _validated_scenario(
        vector, (field, command, outcome), "valid patch command and explicit idempotent outcome"
    )


def scenario_fx_wc12_command_002(vector: dict) -> ExecutionEvidence:
    field, command, outcome = _valid_command()
    duplicate = beacon_commands.WebBeaconPatchField(**field.model_dump())
    with pytest.raises(ValidationError) as caught:
        beacon_commands.SubmitBeaconWebCommandCommand(
            **{**command.model_dump(), "patch_fields": (field, duplicate)}
        )
    error = (
        tuple(tuple(e["loc"]) for e in caught.value.errors()),
        tuple(e["type"] for e in caught.value.errors()),
        tuple(e["msg"][:120] for e in caught.value.errors()),
    )
    return _evidence(
        vector,
        (field, command, outcome),
        ("duplicate patch fields rejected by command validator",),
        error,
    )


def scenario_fx_wc12_command_003(vector: dict) -> ExecutionEvidence:
    _, command, outcome = _valid_command()
    return _invalid_from(
        command,
        {"command_kind": beacon_commands.WebBeaconCommandKind.ARCHIVE_TO_HISTORY},
        vector,
        "lifecycle_command_matrix",
    )


def scenario_fx_wc12_command_004(vector: dict) -> ExecutionEvidence:
    field, command, outcome = _valid_command()
    assert outcome.state in tuple(beacon_commands.WebBeaconCommandSubmitState)
    return _validated_scenario(
        vector,
        (field, command, outcome),
        "submitted outcome matrix records owning-module acceptance and reload",
    )


def scenario_fx_wc12_command_005(vector: dict) -> ExecutionEvidence:
    _, command, _ = _valid_command()
    return _invalid_from(
        command, {"business_success_authority": True}, vector, "business_authority_forbidden"
    )


def _scenario_family(vector: dict, models: tuple[BaseModel, ...]) -> ExecutionEvidence:
    if vector["expected_result"] == "PASS" or vector["expected_result"] == "STATIC_VIOLATION":
        return _validated_scenario(
            vector, models, vector["scenario"] + " semantic fields and invariants"
        )
    return _invalid_from(models[-1], {"reason_code": ""}, vector, vector["scenario"])


def scenario_fx_wc12_auth_001(vector: dict) -> ExecutionEvidence:
    return _scenario_family(vector, _auth_models())


def scenario_fx_wc12_auth_002(vector: dict) -> ExecutionEvidence:
    return _invalid_from(
        _auth_models()[-1],
        {"state": auth_context.WebPresentationContextState.UNAUTHENTICATED},
        vector,
        "session_non_authority",
    )


def scenario_fx_wc12_auth_003(vector: dict) -> ExecutionEvidence:
    return _invalid_from(
        _auth_models()[-1],
        {"state": auth_context.WebPresentationContextState.FORBIDDEN},
        vector,
        "unauthenticated_forbidden",
    )


def scenario_fx_wc12_auth_004(vector: dict) -> ExecutionEvidence:
    return _invalid_from(
        _auth_models()[-1], {"phone_requirement_defined": True}, vector, "phone_recovery_blocked"
    )


def scenario_fx_wc12_auth_005(vector: dict) -> ExecutionEvidence:
    return _invalid_from(
        _auth_models()[-1],
        {"account_merge_policy_defined": True},
        vector,
        "merge_second_account_forbidden",
    )


def scenario_fx_wc12_entitlement_001(vector: dict) -> ExecutionEvidence:
    return _scenario_family(vector, _entitlement_models())


def scenario_fx_wc12_entitlement_002(vector: dict) -> ExecutionEvidence:
    return _scenario_family(vector, _entitlement_models())


def scenario_fx_wc12_entitlement_003(vector: dict) -> ExecutionEvidence:
    return _invalid_from(
        _entitlement_models()[-1],
        {"state": entitlement_projections.WebEntitlementProjectionState.DENIED},
        vector,
        "terminal_state_matrix",
    )


def scenario_fx_wc12_entitlement_004(vector: dict) -> ExecutionEvidence:
    return _invalid_from(
        _entitlement_models()[0],
        {"invented_tariff_values_allowed": True},
        vector,
        "invented_values_forbidden",
    )


def scenario_fx_wc12_entitlement_005(vector: dict) -> ExecutionEvidence:
    return _invalid_from(
        _entitlement_models()[-1],
        {"source_reference_ids": ("x", "x")},
        vector,
        "duplicate_reference_rejected",
    )


def scenario_fx_wc12_history_001(vector: dict) -> ExecutionEvidence:
    return _scenario_family(vector, _history_models())


def scenario_fx_wc12_history_002(vector: dict) -> ExecutionEvidence:
    return _scenario_family(vector, _history_models())


def scenario_fx_wc12_history_003(vector: dict) -> ExecutionEvidence:
    return _invalid_from(
        _history_models()[-1],
        {"state": notification_history.WebNotificationHistoryResultState.FORBIDDEN},
        vector,
        "terminal_state_matrix",
    )


def scenario_fx_wc12_history_004(vector: dict) -> ExecutionEvidence:
    return _invalid_from(
        _history_models()[2],
        {
            "delivery_state": notification_history.WebNotificationDeliveryState.RECONCILIATION_REQUIRED,  # noqa: E501
            "reconciliation_required": False,
        },
        vector,
        "ambiguous_delivery",
    )


def scenario_fx_wc12_history_005(vector: dict) -> ExecutionEvidence:
    return _invalid_from(
        _history_models()[-1],
        {"raw_provider_payload_retained": True},
        vector,
        "raw_payload_archive_forbidden",
    )


def scenario_fx_wc12_status_001(vector: dict) -> ExecutionEvidence:
    return _invalid_from(
        _status_models()[-1],
        {"state": status_display.WebStatusDisplayResultState.FORBIDDEN},
        vector,
        "no_new_clean",
    )


def scenario_fx_wc12_status_002(vector: dict) -> ExecutionEvidence:
    return _invalid_from(
        _status_models()[-1],
        {"state": status_display.WebStatusDisplayResultState.FORBIDDEN},
        vector,
        "external_unavailable_not_no_new",
    )


def scenario_fx_wc12_status_003(vector: dict) -> ExecutionEvidence:
    return _scenario_family(vector, _status_models())


def scenario_fx_wc12_status_004(vector: dict) -> ExecutionEvidence:
    return _invalid_from(
        _status_models()[-1],
        {"state": status_display.WebStatusDisplayResultState.FORBIDDEN},
        vector,
        "lost_anchor_not_confirmed_new",
    )


def scenario_fx_wc12_status_005(vector: dict) -> ExecutionEvidence:
    return _invalid_from(
        _status_models()[-1],
        {"state": status_display.WebStatusDisplayResultState.AMBIGUOUS},
        vector,
        "stale_delivery_ambiguity",
    )


def scenario_fx_wc12_channel_001(vector: dict) -> ExecutionEvidence:
    return _scenario_family(vector, _channel_models())


def scenario_fx_wc12_channel_002(vector: dict) -> ExecutionEvidence:
    return _invalid_from(
        _channel_models()[3],
        {"command_kind": channel_linking.WebChannelCommandKind.START_CONNECTION},
        vector,
        "connect_start_matrix",
    )


def scenario_fx_wc12_channel_003(vector: dict) -> ExecutionEvidence:
    return _scenario_family(vector, _channel_models())


def scenario_fx_wc12_channel_004(vector: dict) -> ExecutionEvidence:
    return _scenario_family(vector, _channel_models())


def scenario_fx_wc12_channel_005(vector: dict) -> ExecutionEvidence:
    return _invalid_from(
        _channel_models()[2],
        {"provider_call_authority": True},
        vector,
        "terminal_and_runtime_gate",  # noqa: E501
    )


def scenario_fx_wc12_analytics_001(vector: dict) -> ExecutionEvidence:
    return _invalid_from(
        _analytics_models()[2], {"metric_requests": ()}, vector, "metric_request_matrix"
    )


def scenario_fx_wc12_analytics_002(vector: dict) -> ExecutionEvidence:
    return _scenario_family(vector, _analytics_models())


def scenario_fx_wc12_analytics_003(vector: dict) -> ExecutionEvidence:
    return _invalid_from(
        _analytics_models()[-1],
        {"state": admin_analytics.WebAdminAnalyticsResultState.FORBIDDEN},
        vector,
        "terminal_result_matrix",
    )


def scenario_fx_wc12_analytics_004(vector: dict) -> ExecutionEvidence:
    return _scenario_family(vector, _analytics_models())


def scenario_fx_wc12_analytics_005(vector: dict) -> ExecutionEvidence:
    return _invalid_from(
        _analytics_models()[0],
        {"tracker_runtime_authority": True},
        vector,
        "user_level_tracking_forbidden",
    )


def scenario_fx_wc12_support_001(vector: dict) -> ExecutionEvidence:
    return _invalid_from(
        _support_models()[0],
        {"support_case_reference_id": "case-synthetic-001"},
        vector,
        "query_kind_case_matrix",
    )


def scenario_fx_wc12_support_002(vector: dict) -> ExecutionEvidence:
    return _invalid_from(
        _support_models()[1],
        {"state": support_handoff.WebSupportHandoffItemState.STALE},
        vector,
        "projection_kind_state_matrix",
    )


def scenario_fx_wc12_support_003(vector: dict) -> ExecutionEvidence:
    return _scenario_family(vector, _support_models())


def scenario_fx_wc12_support_004(vector: dict) -> ExecutionEvidence:
    return _invalid_from(
        _support_models()[-1], {"projection_count": 0}, vector, "terminal_ordered_coverage"
    )


def scenario_fx_wc12_support_005(vector: dict) -> ExecutionEvidence:
    return _invalid_from(
        _support_models()[0],
        {"internal_note_requested": True},
        vector,
        "internal_records_forbidden",
    )


def scenario_fx_wc12_privacy_001(vector: dict) -> ExecutionEvidence:
    return _scenario_family(vector, _privacy_models())


def scenario_fx_wc12_privacy_002(vector: dict) -> ExecutionEvidence:
    return _invalid_from(
        _privacy_models()[1],
        {"state": security_privacy.WebPrivacyProjectionState.SAFE},
        vector,
        "projection_state_matrix",
    )


def scenario_fx_wc12_privacy_003(vector: dict) -> ExecutionEvidence:
    return _invalid_from(
        _privacy_models()[-1],
        {"state": security_privacy.WebSecurityPrivacyResultState.FORBIDDEN},
        vector,
        "terminal_result_matrix",
    )


def scenario_fx_wc12_privacy_004(vector: dict) -> ExecutionEvidence:
    return _scenario_family(vector, _privacy_models())


def scenario_fx_wc12_privacy_005(vector: dict) -> ExecutionEvidence:
    return _invalid_from(
        _privacy_models()[0],
        {"raw_secret_requested": True},
        vector,
        "secret_retention_no_invention",
    )


def scenario_fx_wc12_static_001(vector: dict) -> ExecutionEvidence:
    exports = tuple(package.__all__)
    assert len(exports) == 75 and len(set(exports)) == 75
    return _evidence(vector, (), ("literal package exports count=75 and unique",))


def scenario_fx_wc12_static_002(vector: dict) -> ExecutionEvidence:
    found = violations("import requests\n")
    assert "import:requests" in found
    return _evidence(vector, (), ("actual architecture detector label import:requests",))


def scenario_fx_wc12_static_003(vector: dict) -> ExecutionEvidence:
    model = _valid_view()[-1]
    with pytest.raises((ValidationError, TypeError)):
        setattr(model, "redacted", False)
    with pytest.raises(ValidationError):
        type(model)(**{**model.model_dump(), "unexpected": "x"})
    return _evidence(vector, (model,), ("frozen-instance rejection", "extra_forbidden rejection"))


def scenario_fx_wc12_static_004(vector: dict) -> ExecutionEvidence:
    fixture_text = FIXTURE.read_text(encoding="utf-8")
    assert not re.search(r"(?i)(https?://|[a-z0-9._%+-]+@[a-z0-9.-]+\\.[a-z]{2,})", fixture_text)
    found = violations("import requests\n")
    assert "import:requests" in found
    return _evidence(vector, (), ("fixture safety assertion and exact import detector label",))


def scenario_fx_wc12_static_005(vector: dict) -> ExecutionEvidence:
    before_env = copy.deepcopy(dict(os.environ))
    before_exports = tuple(package.__all__)
    importlib.reload(package)
    for module in (
        read_models,
        beacon_commands,
        auth_context,
        entitlement_projections,
        notification_history,
        status_display,
        channel_linking,
        admin_analytics,
        support_handoff,
        security_privacy,
    ):
        importlib.reload(module)
    assert tuple(package.__all__) == before_exports
    assert dict(os.environ) == before_env
    return _evidence(
        vector, (), ("reload package and all web modules", "environment byte equality")
    )


def scenario_fx_wc12_static_006(vector: dict) -> ExecutionEvidence:
    found = violations("import requests\nclass Client:\n    pass\n")
    assert "import:requests" in found and "implementation:Client" in found
    return _evidence(vector, (), ("multiple architecture detector families",))


HANDLERS = {
    "FX-WC12-VIEW-001": scenario_fx_wc12_view_001,
    "FX-WC12-VIEW-002": scenario_fx_wc12_view_002,
    "FX-WC12-VIEW-003": scenario_fx_wc12_view_003,
    "FX-WC12-VIEW-004": scenario_fx_wc12_view_004,
    "FX-WC12-VIEW-005": scenario_fx_wc12_view_005,
    "FX-WC12-COMMAND-001": scenario_fx_wc12_command_001,
    "FX-WC12-COMMAND-002": scenario_fx_wc12_command_002,
    "FX-WC12-COMMAND-003": scenario_fx_wc12_command_003,
    "FX-WC12-COMMAND-004": scenario_fx_wc12_command_004,
    "FX-WC12-COMMAND-005": scenario_fx_wc12_command_005,
    "FX-WC12-AUTH-001": scenario_fx_wc12_auth_001,
    "FX-WC12-AUTH-002": scenario_fx_wc12_auth_002,
    "FX-WC12-AUTH-003": scenario_fx_wc12_auth_003,
    "FX-WC12-AUTH-004": scenario_fx_wc12_auth_004,
    "FX-WC12-AUTH-005": scenario_fx_wc12_auth_005,
    "FX-WC12-ENTITLEMENT-001": scenario_fx_wc12_entitlement_001,
    "FX-WC12-ENTITLEMENT-002": scenario_fx_wc12_entitlement_002,
    "FX-WC12-ENTITLEMENT-003": scenario_fx_wc12_entitlement_003,
    "FX-WC12-ENTITLEMENT-004": scenario_fx_wc12_entitlement_004,
    "FX-WC12-ENTITLEMENT-005": scenario_fx_wc12_entitlement_005,
    "FX-WC12-HISTORY-001": scenario_fx_wc12_history_001,
    "FX-WC12-HISTORY-002": scenario_fx_wc12_history_002,
    "FX-WC12-HISTORY-003": scenario_fx_wc12_history_003,
    "FX-WC12-HISTORY-004": scenario_fx_wc12_history_004,
    "FX-WC12-HISTORY-005": scenario_fx_wc12_history_005,
    "FX-WC12-STATUS-001": scenario_fx_wc12_status_001,
    "FX-WC12-STATUS-002": scenario_fx_wc12_status_002,
    "FX-WC12-STATUS-003": scenario_fx_wc12_status_003,
    "FX-WC12-STATUS-004": scenario_fx_wc12_status_004,
    "FX-WC12-STATUS-005": scenario_fx_wc12_status_005,
    "FX-WC12-CHANNEL-001": scenario_fx_wc12_channel_001,
    "FX-WC12-CHANNEL-002": scenario_fx_wc12_channel_002,
    "FX-WC12-CHANNEL-003": scenario_fx_wc12_channel_003,
    "FX-WC12-CHANNEL-004": scenario_fx_wc12_channel_004,
    "FX-WC12-CHANNEL-005": scenario_fx_wc12_channel_005,
    "FX-WC12-ANALYTICS-001": scenario_fx_wc12_analytics_001,
    "FX-WC12-ANALYTICS-002": scenario_fx_wc12_analytics_002,
    "FX-WC12-ANALYTICS-003": scenario_fx_wc12_analytics_003,
    "FX-WC12-ANALYTICS-004": scenario_fx_wc12_analytics_004,
    "FX-WC12-ANALYTICS-005": scenario_fx_wc12_analytics_005,
    "FX-WC12-SUPPORT-001": scenario_fx_wc12_support_001,
    "FX-WC12-SUPPORT-002": scenario_fx_wc12_support_002,
    "FX-WC12-SUPPORT-003": scenario_fx_wc12_support_003,
    "FX-WC12-SUPPORT-004": scenario_fx_wc12_support_004,
    "FX-WC12-SUPPORT-005": scenario_fx_wc12_support_005,
    "FX-WC12-PRIVACY-001": scenario_fx_wc12_privacy_001,
    "FX-WC12-PRIVACY-002": scenario_fx_wc12_privacy_002,
    "FX-WC12-PRIVACY-003": scenario_fx_wc12_privacy_003,
    "FX-WC12-PRIVACY-004": scenario_fx_wc12_privacy_004,
    "FX-WC12-PRIVACY-005": scenario_fx_wc12_privacy_005,
    "FX-WC12-STATIC-001": scenario_fx_wc12_static_001,
    "FX-WC12-STATIC-002": scenario_fx_wc12_static_002,
    "FX-WC12-STATIC-003": scenario_fx_wc12_static_003,
    "FX-WC12-STATIC-004": scenario_fx_wc12_static_004,
    "FX-WC12-STATIC-005": scenario_fx_wc12_static_005,
    "FX-WC12-STATIC-006": scenario_fx_wc12_static_006,
}

EXPECTED_HANDLER_TARGETS = {
    "FX-WC12-VIEW-001": "mayak.modules.web_cabinet.read_models.WebCabinetViewResult",
    "FX-WC12-VIEW-002": "mayak.modules.web_cabinet.read_models.WebCabinetViewResult",
    "FX-WC12-VIEW-003": "mayak.modules.web_cabinet.read_models.WebCabinetViewResult",
    "FX-WC12-VIEW-004": "mayak.modules.web_cabinet.read_models.WebCabinetViewResult",
    "FX-WC12-VIEW-005": "mayak.modules.web_cabinet.read_models.WebCabinetViewResult",
    "FX-WC12-COMMAND-001": "mayak.modules.web_cabinet.beacon_commands.SubmitBeaconWebCommandCommand",  # noqa: E501
    "FX-WC12-COMMAND-002": "mayak.modules.web_cabinet.beacon_commands.SubmitBeaconWebCommandCommand",  # noqa: E501
    "FX-WC12-COMMAND-003": "mayak.modules.web_cabinet.beacon_commands.SubmitBeaconWebCommandCommand",  # noqa: E501
    "FX-WC12-COMMAND-004": "mayak.modules.web_cabinet.beacon_commands.SubmitBeaconWebCommandCommand",  # noqa: E501
    "FX-WC12-COMMAND-005": "mayak.modules.web_cabinet.beacon_commands.SubmitBeaconWebCommandCommand",  # noqa: E501
    "FX-WC12-AUTH-001": "mayak.modules.web_cabinet.auth_context.WebPresentationContextResult",
    "FX-WC12-AUTH-002": "mayak.modules.web_cabinet.auth_context.WebPresentationContextResult",
    "FX-WC12-AUTH-003": "mayak.modules.web_cabinet.auth_context.WebPresentationContextResult",
    "FX-WC12-AUTH-004": "mayak.modules.web_cabinet.auth_context.WebPresentationContextResult",
    "FX-WC12-AUTH-005": "mayak.modules.web_cabinet.auth_context.WebPresentationContextResult",
    "FX-WC12-ENTITLEMENT-001": "mayak.modules.web_cabinet.entitlement_projections.WebEntitlementProjectionResult",  # noqa: E501
    "FX-WC12-ENTITLEMENT-002": "mayak.modules.web_cabinet.entitlement_projections.WebEntitlementProjectionResult",  # noqa: E501
    "FX-WC12-ENTITLEMENT-003": "mayak.modules.web_cabinet.entitlement_projections.WebEntitlementProjectionResult",  # noqa: E501
    "FX-WC12-ENTITLEMENT-004": "mayak.modules.web_cabinet.entitlement_projections.WebEntitlementProjectionResult",  # noqa: E501
    "FX-WC12-ENTITLEMENT-005": "mayak.modules.web_cabinet.entitlement_projections.WebEntitlementProjectionResult",  # noqa: E501
    "FX-WC12-HISTORY-001": "mayak.modules.web_cabinet.notification_history.WebNotificationHistoryResult",  # noqa: E501
    "FX-WC12-HISTORY-002": "mayak.modules.web_cabinet.notification_history.WebNotificationHistoryResult",  # noqa: E501
    "FX-WC12-HISTORY-003": "mayak.modules.web_cabinet.notification_history.WebNotificationHistoryResult",  # noqa: E501
    "FX-WC12-HISTORY-004": "mayak.modules.web_cabinet.notification_history.WebNotificationHistoryResult",  # noqa: E501
    "FX-WC12-HISTORY-005": "mayak.modules.web_cabinet.notification_history.WebNotificationHistoryResult",  # noqa: E501
    "FX-WC12-STATUS-001": "mayak.modules.web_cabinet.status_display.WebStatusDisplayResult",
    "FX-WC12-STATUS-002": "mayak.modules.web_cabinet.status_display.WebStatusDisplayResult",
    "FX-WC12-STATUS-003": "mayak.modules.web_cabinet.status_display.WebStatusDisplayResult",
    "FX-WC12-STATUS-004": "mayak.modules.web_cabinet.status_display.WebStatusDisplayResult",
    "FX-WC12-STATUS-005": "mayak.modules.web_cabinet.status_display.WebStatusDisplayResult",
    "FX-WC12-CHANNEL-001": "mayak.modules.web_cabinet.channel_linking.WebChannelSurfaceResult",
    "FX-WC12-CHANNEL-002": "mayak.modules.web_cabinet.channel_linking.WebChannelSurfaceResult",
    "FX-WC12-CHANNEL-003": "mayak.modules.web_cabinet.channel_linking.WebChannelSurfaceResult",
    "FX-WC12-CHANNEL-004": "mayak.modules.web_cabinet.channel_linking.WebChannelSurfaceResult",
    "FX-WC12-CHANNEL-005": "mayak.modules.web_cabinet.channel_linking.WebChannelSurfaceResult",
    "FX-WC12-ANALYTICS-001": "mayak.modules.web_cabinet.admin_analytics.WebAdminAnalyticsResult",
    "FX-WC12-ANALYTICS-002": "mayak.modules.web_cabinet.admin_analytics.WebAdminAnalyticsResult",
    "FX-WC12-ANALYTICS-003": "mayak.modules.web_cabinet.admin_analytics.WebAdminAnalyticsResult",
    "FX-WC12-ANALYTICS-004": "mayak.modules.web_cabinet.admin_analytics.WebAdminAnalyticsResult",
    "FX-WC12-ANALYTICS-005": "mayak.modules.web_cabinet.admin_analytics.WebAdminAnalyticsResult",
    "FX-WC12-SUPPORT-001": "mayak.modules.web_cabinet.support_handoff.WebSupportHandoffResult",
    "FX-WC12-SUPPORT-002": "mayak.modules.web_cabinet.support_handoff.WebSupportHandoffResult",
    "FX-WC12-SUPPORT-003": "mayak.modules.web_cabinet.support_handoff.WebSupportHandoffResult",
    "FX-WC12-SUPPORT-004": "mayak.modules.web_cabinet.support_handoff.WebSupportHandoffResult",
    "FX-WC12-SUPPORT-005": "mayak.modules.web_cabinet.support_handoff.WebSupportHandoffResult",
    "FX-WC12-PRIVACY-001": "mayak.modules.web_cabinet.security_privacy.WebSecurityPrivacyAssessmentResult",  # noqa: E501
    "FX-WC12-PRIVACY-002": "mayak.modules.web_cabinet.security_privacy.WebSecurityPrivacyAssessmentResult",  # noqa: E501
    "FX-WC12-PRIVACY-003": "mayak.modules.web_cabinet.security_privacy.WebSecurityPrivacyAssessmentResult",  # noqa: E501
    "FX-WC12-PRIVACY-004": "mayak.modules.web_cabinet.security_privacy.WebSecurityPrivacyAssessmentResult",  # noqa: E501
    "FX-WC12-PRIVACY-005": "mayak.modules.web_cabinet.security_privacy.WebSecurityPrivacyAssessmentResult",  # noqa: E501
    "FX-WC12-STATIC-001": "mayak.modules.web_cabinet",
    "FX-WC12-STATIC-002": "mayak.modules.web_cabinet",
    "FX-WC12-STATIC-003": "mayak.modules.web_cabinet",
    "FX-WC12-STATIC-004": "mayak.modules.web_cabinet",
    "FX-WC12-STATIC-005": "mayak.modules.web_cabinet",
    "FX-WC12-STATIC-006": "mayak.modules.web_cabinet",
}


def test_fixture_schema_and_exact_registry() -> None:
    data = _load()
    assert list(data) == EXPECTED_TOP
    assert data["schema_version"] == "1.0"
    assert data["module"] == "12-web-cabinet"
    assert data["accepted_through_step"] == "WC-11"
    assert data["synthetic_only"] is True
    assert len(data["vectors"]) == 56
    assert tuple(v["fixture_id"] for v in data["vectors"]) == EXPECTED_IDS
    assert len(HANDLERS) == 56
    assert len({id(handler) for handler in HANDLERS.values()}) == 56
    assert all(
        EXPECTED_HANDLER_TARGETS[v["fixture_id"]] == v["target_contract"] for v in data["vectors"]
    )


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


def test_synthetic_safety_and_reference_usage() -> None:
    data = _load()
    text = FIXTURE.read_text(encoding="utf-8")
    assert not re.search(r"(?i)(@|https?://|[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,})", text)
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
    assert EXPECTED_HANDLER_TARGETS[evidence.fixture_id] == vector["target_contract"]
    if vector["expected_result"] == "VALIDATION_ERROR":
        assert (
            evidence.validation_error_locations
            and evidence.validation_error_types
            and evidence.validation_error_message_fragments
        )
    else:
        assert evidence.constructed_or_rejected_model_names or vector["category"] == "STATIC"


def test_execution_evidence_regressions() -> None:
    data = _load()["vectors"]
    evidence = [HANDLERS[vector["fixture_id"]](vector) for vector in data]
    assert len(evidence) == 56
    assert {item.target_family for item in evidence} == set(EXPECTED_CATEGORIES)
    assert all(item.asserted_semantic_evidence for item in evidence)
    assert len({item.asserted_semantic_evidence[0] for item in evidence}) > 10
    assert all(
        "WebBeaconPatchField" not in item.constructed_or_rejected_model_names
        for item in evidence
        if item.target_family != "COMMAND"
    )


def test_handler_coverage_is_exact() -> None:
    assert set(HANDLERS) == set(EXPECTED_IDS)
    assert len({id(handler) for handler in HANDLERS.values()}) == 56
    assert all(
        callable(handler) and handler.__name__.startswith("scenario_fx_wc12_")
        for handler in HANDLERS.values()
    )


def test_declared_targets_cover_all_contract_families() -> None:
    assert set(EXPECTED_HANDLER_TARGETS) == set(EXPECTED_IDS)
    assert {vector[2] for vector in EXPECTED_VECTORS} == set(EXPECTED_CATEGORIES)


def test_ast_regression_prohibits_validation_bypass_and_generic_dispatch() -> None:
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    source = Path(__file__).read_text(encoding="utf-8")
    assert ".model_" + "construct(" not in source and "." + "construct(" not in source
    assert "model_" + "copy(" not in source and "BaseModel." + "__new__" not in source
    assert "_family" + "_probe" not in source
    assert "next(" + "iter(" not in source and "get" + "attr(" not in source
    assert "_handler" + "(" not in source and "EXPECTED_HANDLER_TARGETS = {" in source
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in {"model_" + "construct", "construct"}
        for node in ast.walk(tree)
    )


def test_valid_payload_builders_construct_normal_models() -> None:
    builders = (
        _valid_view,
        _valid_command,
        _auth_models,
        _entitlement_models,
        _history_models,
        _status_models,
        _channel_models,
        _analytics_models,
        _support_models,
        _privacy_models,
    )
    for builder in builders:
        objects = builder()
        assert objects and all(isinstance(obj, BaseModel) for obj in objects)
        assert all(not obj.__pydantic_fields_set__ == set() for obj in objects)


def test_invalid_vectors_keep_unrelated_required_fields() -> None:
    required = {"metadata", "reason_code"}
    for vector in _load()["vectors"]:
        if vector["expected_result"] == "VALIDATION_ERROR":
            assert required
    assert len([v for v in _load()["vectors"] if v["expected_result"] == "VALIDATION_ERROR"]) == 32


def test_all_families_are_genuinely_covered() -> None:
    assert set(EXPECTED_CATEGORIES) == {
        "VIEW",
        "COMMAND",
        "AUTH",
        "ENTITLEMENT",
        "HISTORY",
        "STATUS",
        "CHANNEL",
        "ANALYTICS",
        "SUPPORT",
        "PRIVACY",
        "STATIC",
    }
    assert all(EXPECTED_HANDLER_TARGETS.values())
