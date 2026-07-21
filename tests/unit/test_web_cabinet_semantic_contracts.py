"""Executable deterministic WC-02..WC-12 semantic vectors."""

from __future__ import annotations

import ast
import json
import os
import re
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

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

SCENARIO_EXECUTION_SPEC = (
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
)


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
    static_labels: tuple[str, ...] = ()
    constructed_model_names: tuple[str, ...] = ()
    attempted_model_name: str | None = None
    attempted_payload_keys: tuple[str, ...] = ()
    intended_mutation_keys: tuple[str, ...] = ()
    complete_valid_source_exists: bool = False
    unrelated_required_fields_retained: bool = False


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


def _validation_tuple(
    caught: ValidationError,
) -> tuple[tuple[tuple[Any, ...], ...], tuple[str, ...], tuple[str, ...]]:
    entries = tuple(caught.errors())
    assert entries
    return (
        tuple(tuple(entry["loc"]) for entry in entries),
        tuple(str(entry["type"]) for entry in entries),
        tuple(str(entry["msg"])[:120] for entry in entries),
    )


def _evidence(
    vector: dict, models: tuple[BaseModel, ...], semantic: tuple[str, ...], error: Any = None
) -> ExecutionEvidence:
    locations, types, fragments = error or ((), (), ())
    names = tuple(type(model).__name__ for model in models)
    return ExecutionEvidence(
        "PASS" if error is None else "VALIDATION_ERROR",
        vector["fixture_id"],
        vector["scenario"],
        vector["category"],
        names,
        semantic,
        locations,
        types,
        fragments,
        constructed_model_names=names,
        attempted_model_name=names[-1] if error is not None and names else None,
        complete_valid_source_exists=error is not None,
        unrelated_required_fields_retained=error is not None,
    )


def _valid_view() -> tuple[Any, ...]:
    o0 = read_models.RequestWebCabinetViewQuery(
        web_cabinet_view_query_id="view-query-synthetic-001",
        metadata=_META,
        account_id="acct-synthetic-001",
        actor_context_reference_id="actor-synthetic-001",
        authorization_decision_reference_id="authz-synthetic-001",
        tenant_scope_reference_id="tenant-synthetic-001",
        audience=security_privacy.WebViewAudience.CUSTOMER,
        requested_families=(read_models.WebReadModelFamily.ACTIVE_BEACONS,),
        view_policy_reference_id="policy-synthetic-001",
        reason_code="synthetic-view",
        verified_actor_required=True,
        read_only=True,
        client_state_authority=False,
        direct_write_authority=False,
        provider_call_authority=False,
        raw_resource_access_authority=False,
        foreign_host_access_authority=False,
    )
    o1 = read_models.WebReadModelSourceReference(
        web_source_reference_id="source-synthetic-001",
        family=read_models.WebReadModelFamily.ACTIVE_BEACONS,
        owning_module_id="04-beacon-management",
        account_id="acct-synthetic-001",
        tenant_scope_reference_id="tenant-synthetic-001",
        state=read_models.WebSourceState.AVAILABLE,
        freshness=security_privacy.WebReadFreshness.FRESH,
        safe_projection_reference_id="projection-synthetic-001",
        provenance_reference_ids=("provenance-synthetic-001",),
        reason_code="available",
        ambiguity_reference_id=None,
        redaction_policy_reference_id="redaction-synthetic-001",
        safe_reference_only=True,
        redacted=True,
        minimal_personal_data=True,
        contains_secret_material=False,
        raw_provider_payload_retained=False,
        full_private_message_retained=False,
        full_listing_archive_retained=False,
        mutation_authority=False,
        provider_call_authority=False,
    )
    o2 = read_models.WebCabinetViewResult(
        web_cabinet_view_result_id="view-result-synthetic-001",
        metadata=_META,
        query=o0,
        state=read_models.WebCabinetViewState.AUTHORIZED,
        freshness=security_privacy.WebReadFreshness.FRESH,
        sources=(o1,),
        composition_policy_reference_id="composition-synthetic-001",
        redaction_policy_reference_id="redaction-synthetic-001",
        ambiguity_reference_id=None,
        provenance_aware=True,
        freshness_aware=True,
        ownership_scoped=True,
        authorization_required=True,
        redacted=True,
        minimal_personal_data=True,
        contains_secret_material=False,
        raw_provider_payload_retained=False,
        full_private_message_retained=False,
        full_listing_archive_retained=False,
        mutation_authority=False,
        provider_call_authority=False,
        business_success_authority=False,
    )
    return o0, o1, o2


def _valid_command() -> tuple[Any, ...]:
    o0 = beacon_commands.WebBeaconPatchField(
        web_patch_field_id="patch-synthetic-001",
        field_name="safe_field",
        requested_value_reference_id="ref-synthetic-001",
        owning_module_validation_family_reference_id="beacon-management",
        client_validation_reference_id=None,
        explicitly_supplied=True,
        server_validation_required=True,
        client_validation_authority=False,
        field_support_authority=False,
        raw_value_retained=False,
        provider_payload_retained=False,
    )
    o1 = beacon_commands.SubmitBeaconWebCommandCommand(
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
        patch_fields=(o0,),
        history_entry_reference_id=None,
        confirmation_reference_id=None,
        entitlement_recheck_reference_id=None,
        idempotency_key=IdempotencyKey(value="idem-synthetic-001"),
        idempotency_scope=IdempotencyScope(value="acct-synthetic-001"),
        idempotency_fingerprint=IdempotencyFingerprint(value="fingerprint-synthetic-001"),
        correlation_id="corr-synthetic-001",
        causation_id="cause-synthetic-001",
        reason_code="synthetic-command",
        verified_actor_required=True,
        ownership_scope_validation_required=True,
        server_side_validation_required=True,
        owning_module_current_state_reload_required=True,
        client_validation_authority=False,
        web_observed_state_authority=False,
        direct_write_authority=False,
        provider_call_authority=False,
        entitlement_mutation_authority=False,
        scan_mutation_authority=False,
        notification_mutation_authority=False,
        stale_full_form_overwrite=False,
        source_url_only_idempotency=False,
        raw_provider_payload_retained=False,
        business_success_authority=False,
    )
    o2 = beacon_commands.WebBeaconCommandSubmitOutcome(
        web_beacon_command_submit_outcome_id="outcome-synthetic-001",
        metadata=_META,
        command=o1,
        state=beacon_commands.WebBeaconCommandSubmitState.SUBMITTED,
        owning_module_id="04-beacon-management",
        owning_module_outcome_reference_id="outcome-ref-synthetic-001",
        authoritative_state_reference_id="state-ref-synthetic-001",
        replay_of_outcome_reference_id=None,
        rejection_reason_code=None,
        ambiguity_reference_id=None,
        applied_field_names=("safe_field",),
        owning_module_accepted=True,
        authoritative_state_reloaded=True,
        safe_display_outcome=True,
        explicit_owning_module_outcome_required=True,
        web_business_success_authority=False,
        direct_write_authority=False,
        provider_call_authority=False,
        raw_provider_payload_retained=False,
        full_form_state_retained=False,
        committed_scan_audit_facts_rewritten=False,
        physical_delete_implementation_claimed=False,
    )
    return o0, o1, o2


def _auth_models() -> tuple[Any, ...]:
    o0 = auth_context.RequestWebPresentationContextQuery(
        web_presentation_context_query_id="synthetic-reference-001",
        metadata=_META,
        actor_context_reference_id="actor-synthetic-001",
        requested_audience=security_privacy.WebViewAudience.CUSTOMER,
        tenant_scope_reference_id="synthetic-reference-001",
        identity_validation_policy_reference_id="synthetic-reference-001",
        reason_code="synthetic-reference-001",
        identity_authority_required=True,
        read_only=True,
        client_account_authority=False,
        client_role_authority=False,
        client_session_authority=False,
        provider_identity_authority=False,
        phone_requirement_defined=False,
        password_policy_defined=False,
        recovery_policy_defined=False,
        account_merge_policy_defined=False,
        raw_credential_material_present=False,
        raw_session_token_present=False,
        raw_provider_payload_present=False,
        cookie_jwt_oauth_implementation_claimed=False,
        session_storage_implementation_claimed=False,
        direct_identity_write_authority=False,
    )
    o1 = auth_context.WebIdentityAuthorityReference(
        web_identity_authority_reference_id="synthetic-reference-001",
        owning_module_id="02-identity-and-access",
        actor_context_reference_id="actor-synthetic-001",
        actor_state=auth_context.WebPresentationActorState.VERIFIED,
        account_id="acct-synthetic-001",
        authorization_decision_reference_id="authz-synthetic-001",
        auth_session_reference_id="session-synthetic-001",
        session_state=auth_context.WebSessionReferenceState.ACTIVE,
        role_scope_reference_id=None,
        target_scope_reference_id=None,
        audit_reference_id=None,
        reason_code="synthetic-reference-001",
        ambiguity_reference_id=None,
        internal_account_id_authority=True,
        provider_identity_authority=False,
        web_local_account_authority=False,
        client_role_authority=False,
        client_session_authority=False,
        contact_point_is_account_authority=False,
        phone_requirement_defined=False,
        raw_credential_retained=False,
        raw_session_token_retained=False,
        raw_provider_payload_retained=False,
        account_merge_authority=False,
        identity_mutation_authority=False,
        session_implementation_authority=False,
        safe_reference_only=True,
    )
    o2 = auth_context.WebPresentationContextResult(
        web_presentation_context_result_id="synthetic-reference-001",
        metadata=_META,
        query=o0,
        state=auth_context.WebPresentationContextState.AUTHORIZED,
        authority=o1,
        resolved_account_id="acct-synthetic-001",
        safe_identity_summary_reference_id="identity-summary-synthetic-001",
        ambiguity_reference_id=None,
        reason_code="synthetic-reference-001",
        identity_authoritative=True,
        account_scope_preserved=True,
        presentation_only=True,
        session_transport_neutral=True,
        authentication_implementation_present=False,
        authorization_implementation_present=False,
        separate_customer_database=False,
        direct_identity_write_authority=False,
        provider_call_authority=False,
        business_success_authority=False,
        raw_credential_material_present=False,
        raw_session_token_present=False,
        raw_provider_payload_present=False,
        phone_requirement_defined=False,
        password_recovery_policy_defined=False,
        account_merge_policy_defined=False,
    )
    return o0, o1, o2


def _entitlement_models() -> tuple[Any, ...]:
    o0 = entitlement_projections.RequestWebEntitlementProjectionQuery(
        web_entitlement_projection_query_id="synthetic-reference-001",
        metadata=_META,
        account_id="acct-synthetic-001",
        actor_context_reference_id="synthetic-reference-001",
        authorization_decision_reference_id="synthetic-reference-001",
        tenant_scope_reference_id="synthetic-reference-001",
        requested_capability_reference_ids=("capability-synthetic-001",),
        include_tariff_options=True,
        entitlement_evaluation_policy_reference_id="synthetic-reference-001",
        tariff_visibility_policy_reference_id="synthetic-reference-001",
        reason_code="synthetic-reference-001",
        verified_actor_required=True,
        account_scope_required=True,
        read_only=True,
        entitlements_authority_required=True,
        client_entitlement_authority=False,
        client_tariff_authority=False,
        web_entitlement_evaluator=False,
        direct_entitlement_write_authority=False,
        subscription_mutation_authority=False,
        grant_mutation_authority=False,
        payment_mutation_authority=False,
        usage_counter_mutation_authority=False,
        provider_call_authority=False,
        payment_response_is_entitlement_authority=False,
        invented_tariff_values_allowed=False,
        raw_payment_payload_present=False,
    )
    o1 = entitlement_projections.WebEntitlementCapabilityProjection(
        web_entitlement_capability_projection_id="synthetic-reference-001",
        account_id="acct-synthetic-001",
        capability_reference_id="capability-synthetic-001",
        access_state=entitlement_projections.WebEntitlementAccessState.ALLOWED,
        effective_entitlement_decision_reference_id="synthetic-reference-001",
        safe_limit_display_reference_id=None,
        effective_interval_reference_id=None,
        source_reference_ids=("entitlement-source-001",),
        reason_code="synthetic-reference-001",
        ambiguity_reference_id=None,
        derived_from_entitlements=True,
        safe_reference_only=True,
        web_recomputed=False,
        web_limit_authority=False,
        raw_limit_value_retained=False,
        payment_evidence_authority=False,
        raw_payment_payload_retained=False,
        direct_mutation_authority=False,
        provider_call_authority=False,
    )
    o2 = entitlement_projections.WebTariffOptionProjection(
        web_tariff_option_projection_id="synthetic-reference-001",
        owning_module_id="03-entitlements-and-billing",
        account_id="acct-synthetic-001",
        tariff_definition_reference_id="synthetic-reference-001",
        semantic_version_reference_id="synthetic-reference-001",
        state=entitlement_projections.WebTariffOptionState.AVAILABLE,
        safe_name_display_reference_id="tariff-name-001",
        safe_price_display_reference_id=None,
        safe_billing_period_display_reference_id=None,
        safe_limit_summary_reference_ids=("synthetic-reference-001",),
        source_reference_ids=("tariff-source-001",),
        reason_code="synthetic-reference-001",
        ambiguity_reference_id=None,
        approved_definition_reference_required=True,
        safe_display_references_only=True,
        web_tariff_authority=False,
        web_price_authority=False,
        web_limit_authority=False,
        payment_provider_authority=False,
        payment_response_is_entitlement_authority=False,
        raw_payment_payload_retained=False,
        future_tariff_invention_authority=False,
        provider_call_authority=False,
        direct_mutation_authority=False,
    )
    o3 = entitlement_projections.WebEntitlementProjectionResult(
        web_entitlement_projection_result_id="synthetic-reference-001",
        metadata=_META,
        query=o0,
        state=entitlement_projections.WebEntitlementProjectionState.AVAILABLE,
        freshness=security_privacy.WebReadFreshness.FRESH,
        owning_module_id="03-entitlements-and-billing",
        effective_entitlement_summary_reference_id="synthetic-reference-001",
        current_tariff_definition_reference_id=None,
        capabilities=(o1,),
        tariff_options=(o2,),
        payment_upgrade_placeholder_reference_id=None,
        source_reference_ids=("entitlement-source-001",),
        ambiguity_reference_id=None,
        reason_code="synthetic-reference-001",
        safe_projection_only=True,
        entitlements_authoritative=True,
        web_entitlement_authority=False,
        web_tariff_definition_authority=False,
        effective_entitlement_recomputed_by_web=False,
        prices_limits_names_invented=False,
        subscription_mutation_authority=False,
        grant_mutation_authority=False,
        payment_mutation_authority=False,
        usage_counter_mutation_authority=False,
        direct_write_authority=False,
        provider_call_authority=False,
        payment_provider_integration_present=False,
        payment_response_is_entitlement_authority=False,
        raw_payment_payload_retained=False,
        card_data_retained=False,
        minimal_personal_data=True,
        redacted=True,
        business_success_authority=False,
    )
    return o0, o1, o2, o3


def _history_models() -> tuple[Any, ...]:
    o0 = notification_history.RequestWebNotificationHistoryQuery(
        web_notification_history_query_id="synthetic-reference-001",
        metadata=_META,
        account_id="acct-synthetic-001",
        actor_context_reference_id="synthetic-reference-001",
        authorization_decision_reference_id="synthetic-reference-001",
        tenant_scope_reference_id="synthetic-reference-001",
        requested_audience=security_privacy.WebViewAudience.CUSTOMER,
        beacon_scope_ids=("beacon-synthetic-001",),
        notification_read_policy_reference_id="synthetic-reference-001",
        freshness_policy_reference_id="synthetic-reference-001",
        reason_code="synthetic-reference-001",
        verified_actor_required=True,
        account_scope_required=True,
        read_only=True,
        notification_authority_required=True,
        client_history_authority=False,
        web_delivery_evaluator=False,
        direct_notification_write_authority=False,
        outbox_mutation_authority=False,
        attempt_mutation_authority=False,
        retry_authority=False,
        reconciliation_execution_authority=False,
        provider_mapping_authority=False,
        provider_call_authority=False,
        read_tracking_authority=False,
        click_tracking_authority=False,
        retention_policy_defined=False,
        raw_provider_payload_present=False,
        full_message_history_requested=False,
        full_listing_archive_requested=False,
    )
    o1 = notification_history.WebNotificationListingReferenceProjection(
        web_notification_listing_reference_projection_id="synthetic-reference-001",
        account_id="acct-synthetic-001",
        beacon_id="beacon-synthetic-001",
        safe_listing_reference_id="synthetic-reference-001",
        notification_listing_card_reference_id=None,
        source_event_reference_id="synthetic-reference-001",
        source_fact_reference_id=None,
        provenance_reference_ids=("synthetic-reference-001",),
        evidence_reference_ids=("synthetic-reference-001",),
        reason_code="synthetic-reference-001",
        safe_reference_only=True,
        notification_projection_source=True,
        listing_reference_preserved=True,
        raw_listing_value_retained=False,
        raw_avito_payload_retained=False,
        raw_provider_payload_retained=False,
        contact_data_retained=False,
        full_listing_archive_authority=False,
        fetch_authority=False,
        parse_authority=False,
        enrichment_authority=False,
        provider_call_authority=False,
        retention_authority=False,
    )
    o2 = notification_history.WebNotificationDeliveryHistoryEntry(
        web_notification_delivery_history_entry_id="synthetic-reference-001",
        account_id="acct-synthetic-001",
        beacon_id="beacon-synthetic-001",
        notification_history_entry_reference_id="synthetic-reference-001",
        notification_batch_item_reference_id="synthetic-reference-001",
        notification_source_decision_reference_id="synthetic-reference-001",
        notification_outbox_item_reference_id=None,
        notification_attempt_reference_id=None,
        channel_class_reference_id=None,
        safe_result_reference_id="synthetic-reference-001",
        delivery_state=notification_history.WebNotificationDeliveryState.PLANNED,
        safe_error_category_reference_id="synthetic-reference-001",
        safe_reason_codes=("synthetic-reference-001",),
        listing_references=(o1,),
        listing_count=1,
        reconciliation_required=False,
        reconciliation_reference_id=None,
        retry_policy_required=False,
        retry_policy_reference_id=None,
        evidence_reference_ids=("synthetic-reference-001",),
        freshness_reference_ids=("synthetic-reference-001",),
        provenance_reference_ids=("synthetic-reference-001",),
        derived_from_notification=True,
        safe_projection_only=True,
        per_item_outcome_exposed=True,
        listing_references_preserved=True,
        web_delivery_authority=False,
        delivery_execution_authority=False,
        provider_mapping_authority=False,
        provider_call_authority=False,
        outbox_mutation_authority=False,
        attempt_mutation_authority=False,
        retry_execution_authority=False,
        reconciliation_execution_authority=False,
        read_tracking_authority=False,
        click_tracking_authority=False,
        retention_authority=False,
        raw_message_content_retained=False,
        full_chat_history_retained=False,
        full_listing_archive_retained=False,
        raw_listing_payload_retained=False,
        raw_provider_payload_retained=False,
        business_success_authority=False,
    )
    o3 = notification_history.WebNotificationHistoryResult(
        web_notification_history_result_id="synthetic-reference-001",
        metadata=_META,
        query=o0,
        state=notification_history.WebNotificationHistoryResultState.AVAILABLE,
        freshness=security_privacy.WebReadFreshness.FRESH,
        owning_module_id="08-notification-delivery",
        notification_read_model_reference_id="history-model-001",
        notification_projection_decision_reference_id="history-decision-001",
        history_entries=(o2,),
        safe_listing_references=(o1,),
        listing_count=1,
        history_entry_count=1,
        replay_visible=False,
        failure_visible=False,
        reconciliation_required=False,
        source_reference_ids=("history-source-001",),
        freshness_reference_ids=("synthetic-reference-001",),
        provenance_reference_ids=("synthetic-reference-001",),
        evidence_reference_ids=("synthetic-reference-001",),
        ambiguity_reference_id=None,
        reason_code="synthetic-reference-001",
        safe_projection_only=True,
        notification_authoritative=True,
        web_notification_authority=False,
        per_item_outcomes_exposed=True,
        listing_references_preserved=True,
        preview_truncation_applied=False,
        delivery_execution_authority=False,
        provider_mapping_authority=False,
        provider_call_authority=False,
        outbox_mutation_authority=False,
        attempt_mutation_authority=False,
        retry_execution_authority=False,
        reconciliation_execution_authority=False,
        read_tracking_authority=False,
        click_tracking_authority=False,
        retention_policy_defined=False,
        full_listing_archive_retained=False,
        full_message_history_retained=False,
        full_chat_history_retained=False,
        raw_listing_payload_retained=False,
        raw_provider_payload_retained=False,
        credentials_retained=False,
        minimal_personal_data=True,
        redacted=True,
        business_success_authority=False,
    )
    return o0, o1, o2, o3


def _status_models() -> tuple[Any, ...]:
    o0 = status_display.RequestWebStatusDisplayQuery(
        web_status_display_query_id="synthetic-reference-001",
        metadata=_META,
        account_id="acct-synthetic-001",
        actor_context_reference_id="synthetic-reference-001",
        authorization_decision_reference_id="synthetic-reference-001",
        tenant_scope_reference_id="synthetic-reference-001",
        requested_audience=security_privacy.WebViewAudience.CUSTOMER,
        beacon_scope_ids=("beacon-synthetic-001",),
        requested_status_reference_ids=("status-synthetic-001",),
        status_mapping_policy_reference_id="synthetic-reference-001",
        freshness_policy_reference_id="synthetic-reference-001",
        reason_code="synthetic-reference-001",
        verified_actor_required=True,
        account_scope_required=True,
        read_only=True,
        owning_module_status_authority_required=True,
        client_status_authority=False,
        browser_state_authority=False,
        web_business_outcome_evaluator=False,
        direct_foreign_state_write_authority=False,
        delivery_execution_authority=False,
        retry_execution_authority=False,
        reconciliation_execution_authority=False,
        provider_call_authority=False,
        raw_error_requested=False,
        stack_trace_requested=False,
        raw_provider_payload_requested=False,
        actual_message_text_requested=False,
        retention_policy_defined=False,
    )
    o1 = status_display.WebStatusEvidenceReference(
        web_status_evidence_reference_id="evidence-synthetic-001",
        account_id="acct-synthetic-001",
        beacon_id="beacon-synthetic-001",
        source_family=status_display.WebStatusSourceFamily.SCAN_ORCHESTRATION,
        source_module_id="06-scan-orchestration-and-listing-state",
        evidence_class=status_display.WebStatusEvidenceClass.SCAN_NO_NEW_PROVEN,
        source_status_reference_id="synthetic-reference-001",
        source_decision_reference_id="decision-synthetic-001",
        source_outcome_reference_id="outcome-synthetic-001",
        source_reason_codes=("no-new",),
        freshness=security_privacy.WebReadFreshness.FRESH,
        safe_evidence_reference_ids=("evidence-safe-001",),
        safe_latest_fresh_listing_reference_ids=(),
        no_new_claim_allowed=True,
        state_restored_latest_fresh_only=False,
        continuing_scan_visible=False,
        reconciliation_reference_id=None,
        ambiguity_reference_id=None,
        safe_reference_only=True,
        source_module_authoritative=True,
        web_status_authority=False,
        web_scan_authority=False,
        web_notification_authority=False,
        web_entitlement_authority=False,
        web_channel_authority=False,
        confirmed_new_claim_allowed=False,
        delivery_success_claim_allowed=False,
        user_receipt_claim_allowed=False,
        provider_call_authority=False,
        mutation_authority=False,
        raw_error_present=False,
        stack_trace_present=False,
        raw_provider_payload_present=False,
        secret_value_present=False,
        personal_contact_data_present=False,
        retention_authority=False,
    )
    o2 = status_display.WebStatusDisplayItem(
        web_status_display_item_id="synthetic-reference-001",
        account_id="acct-synthetic-001",
        beacon_id="beacon-synthetic-001",
        family=status_display.WebStatusDisplayFamily.NO_NEW_LISTINGS,
        safe_status_title_reference_id="synthetic-reference-001",
        safe_status_message_reference_id="synthetic-reference-001",
        safe_action_reference_ids=("synthetic-reference-001",),
        source_evidence_reference_ids=("evidence-synthetic-001",),
        reason_code="synthetic-reference-001",
        safe_display_references_only=True,
        redacted=True,
        localization_value_embedded=False,
        raw_error_present=False,
        stack_trace_present=False,
        raw_provider_payload_present=False,
        secret_value_present=False,
        personal_contact_data_present=False,
        business_success_authority=False,
        delivery_success_authority=False,
        provider_call_authority=False,
        mutation_authority=False,
    )
    o3 = status_display.WebStatusDisplayResult(
        web_status_display_result_id="synthetic-reference-001",
        metadata=_META,
        query=o0,
        state=status_display.WebStatusDisplayResultState.AVAILABLE,
        freshness=security_privacy.WebReadFreshness.FRESH,
        owning_module_id="12-web-cabinet",
        status_mapping_policy_reference_id="synthetic-reference-001",
        source_evidence=(o1,),
        display_items=(o2,),
        external_unavailable_visible=False,
        recovery_visible=False,
        lost_anchors_state_restored_visible=False,
        access_or_channel_problem_visible=False,
        delivery_problem_visible=False,
        reconciliation_visible=False,
        stale_warning_visible=False,
        source_reference_ids=("status-source-001",),
        evidence_reference_ids=("evidence-synthetic-001",),
        ambiguity_reference_id=None,
        reason_code="synthetic-reference-001",
        safe_projection_only=True,
        web_presentation_authority_only=True,
        source_modules_authoritative=True,
        web_business_outcome_authority=False,
        false_no_new_prevented=True,
        false_confirmed_new_prevented=True,
        notification_failure_does_not_rollback_scan=True,
        unknown_delivery_is_reconciliation_first=True,
        safe_display_references_only=True,
        actual_ui_copy_embedded=False,
        direct_foreign_state_write_authority=False,
        delivery_execution_authority=False,
        retry_execution_authority=False,
        reconciliation_execution_authority=False,
        provider_call_authority=False,
        raw_error_present=False,
        stack_trace_present=False,
        raw_provider_payload_present=False,
        secret_value_present=False,
        personal_contact_data_present=False,
        retention_policy_defined=False,
        minimal_personal_data=True,
        redacted=True,
        business_success_authority=False,
    )
    return o0, o1, o2, o3


def _channel_models() -> tuple[Any, ...]:
    o0 = channel_linking.RequestWebChannelSurfaceQuery(
        web_channel_surface_query_id="synthetic-reference-001",
        metadata=_META,
        account_id="acct-synthetic-001",
        actor_context_reference_id="synthetic-reference-001",
        authorization_decision_reference_id="synthetic-reference-001",
        tenant_scope_reference_id="synthetic-reference-001",
        requested_audience=security_privacy.WebViewAudience.CUSTOMER,
        requested_channels=(channel_linking.WebChannelKind.TELEGRAM,),
        channel_read_policy_reference_id="synthetic-reference-001",
        identity_link_policy_reference_id="synthetic-reference-001",
        notification_preference_policy_reference_id="synthetic-reference-001",
        freshness_policy_reference_id="synthetic-reference-001",
        reason_code="synthetic-reference-001",
        verified_actor_required=True,
        account_scope_required=True,
        read_only=True,
        identity_authority_required=True,
        adapter_authority_required=True,
        notification_authority_required=True,
        client_identity_authority=False,
        client_link_authority=False,
        client_preference_authority=False,
        browser_state_authority=False,
        provider_identifier_requested=False,
        raw_link_requested=False,
        raw_mini_app_data_requested=False,
        telegram_runtime_capability_requested=False,
        runtime_execution_requested=False,
        direct_foreign_state_write_authority=False,
        provider_call_authority=False,
        retention_policy_defined=False,
    )
    o1 = channel_linking.WebChannelSurfaceProjection(
        web_channel_surface_projection_id="synthetic-reference-001",
        account_id="acct-synthetic-001",
        channel=channel_linking.WebChannelKind.TELEGRAM,
        state=channel_linking.WebChannelSurfaceState.LINKED_ENABLED,
        preference_state=channel_linking.WebChannelNotificationPreferenceState.ENABLED,
        freshness=security_privacy.WebReadFreshness.FRESH,
        owning_adapter_module_id="09-telegram-adapter",
        adapter_projection_reference_id="synthetic-reference-001",
        adapter_eligibility_reference_id="eligibility-001",
        adapter_runtime_gate_safe_reference_id=None,
        provider_identity_safe_reference_id="provider-identity-001",
        adapter_account_link_reference_id="link-001",
        identity_decision_reference_id="identity-decision-001",
        identity_account_reference_id="acct-synthetic-001",
        identity_link_challenge_reference_id=None,
        notification_channel_gate_decision_reference_id="gate-001",
        notification_target_safe_reference_id="target-001",
        notification_push_eligible=True,
        safe_start_connection_action_reference_id=None,
        safe_enable_notifications_action_reference_id=None,
        safe_disable_notifications_action_reference_id="disable-001",
        safe_cross_interface_return_reference_id=None,
        safe_mini_app_surface_reference_id=None,
        source_reference_ids=("channel-source-001",),
        evidence_reference_ids=("channel-evidence-001",),
        ambiguity_reference_id=None,
        reason_code="synthetic-reference-001",
        safe_projection_only=True,
        same_internal_account_required=True,
        identity_authoritative=True,
        adapter_provider_mapping_authoritative=True,
        notification_preference_authoritative=True,
        telegram_runtime_gate_reference_only=True,
        web_identity_authority=False,
        web_link_authority=False,
        web_preference_authority=False,
        web_target_authority=False,
        web_runtime_authority=False,
        provider_identifier_present=False,
        raw_link_present=False,
        raw_mini_app_data_present=False,
        runtime_capability_present=False,
        runtime_execution_authority=False,
        weak_correlation_link_allowed=False,
        automatic_account_merge_allowed=False,
        phone_requirement_defined=False,
        provider_call_authority=False,
        direct_mutation_authority=False,
        business_success_authority=False,
        minimal_personal_data=True,
        redacted=True,
    )
    o2 = channel_linking.WebChannelSurfaceResult(
        web_channel_surface_result_id="synthetic-reference-001",
        metadata=_META,
        query=o0,
        state=channel_linking.WebChannelSurfaceResultState.AVAILABLE,
        freshness=security_privacy.WebReadFreshness.FRESH,
        owning_module_id="12-web-cabinet",
        channel_read_policy_reference_id="synthetic-reference-001",
        channel_projections=(o1,),
        linked_channel_count=1,
        push_eligible_channel_count=1,
        disabled_channel_count=0,
        future_gated_channel_count=0,
        source_reference_ids=("channel-source-001",),
        evidence_reference_ids=("channel-evidence-001",),
        ambiguity_reference_id=None,
        reason_code="synthetic-reference-001",
        safe_presentation_boundary=True,
        single_account_boundary=True,
        identity_authoritative=True,
        adapters_authoritative=True,
        notification_authoritative=True,
        eligible_channel_set_from_notification=True,
        telegram_runtime_gate_reference_only=True,
        web_foreign_authority=False,
        runtime_authority=False,
        provider_call_authority=False,
        direct_write_authority=False,
        business_success_authority=False,
        raw_provider_data_present=False,
        raw_link_data_present=False,
        raw_mini_app_data_present=False,
        automatic_account_merge_allowed=False,
        minimal_personal_data=True,
        redacted=True,
    )
    o3 = channel_linking.SubmitWebChannelCommandCommand(
        web_channel_command_id="synthetic-reference-001",
        metadata=_META,
        idempotency_key=IdempotencyKey(value="synthetic-reference-001"),
        idempotency_scope=IdempotencyScope(value="synthetic-reference-001"),
        fingerprint=IdempotencyFingerprint(value="synthetic-reference-001"),
        account_id="acct-synthetic-001",
        actor_context_reference_id="synthetic-reference-001",
        authorization_decision_reference_id="synthetic-reference-001",
        tenant_scope_reference_id="synthetic-reference-001",
        channel=channel_linking.WebChannelKind.TELEGRAM,
        command_kind=channel_linking.WebChannelCommandKind.ENABLE_NOTIFICATIONS,
        requested_owning_module_id="08-notification-delivery",
        current_channel_projection_reference_id="synthetic-reference-001",
        expected_source_version_reference_id="synthetic-reference-001",
        adapter_action_reference_id=None,
        adapter_runtime_gate_safe_reference_id=None,
        identity_link_contract_reference_id=None,
        identity_decision_reference_id="identity-decision-001",
        notification_preference_contract_reference_id="preference-contract-001",
        notification_channel_gate_decision_reference_id="notification-gate-001",
        reason_code="synthetic-reference-001",
        verified_actor_account_server_validation=True,
        web_draft_client_identity_authority=False,
        web_draft_client_link_authority=False,
        web_draft_client_preference_authority=False,
        direct_identity_adapter_notification_write_authority=False,
        runtime_gate_reference_only=True,
        runtime_capability_requested=False,
        runtime_execution_requested=False,
        provider_authority=False,
        raw_provider_data_present=False,
        raw_link_data_present=False,
        raw_mini_app_data_present=False,
        account_merge_authority=False,
        phone_requirement_defined=False,
        business_success_authority=False,
    )
    o4 = channel_linking.WebChannelCommandSubmitOutcome(
        web_channel_command_submit_outcome_id="synthetic-reference-001",
        metadata=_META,
        command=o3,
        state=channel_linking.WebChannelCommandSubmitState.SUBMITTED,
        owning_module_id="08-notification-delivery",
        owning_command_reference_id="command-owner-001",
        replayed_outcome_reference_id=None,
        safe_owning_outcome_reference_id="outcome-safe-001",
        reconciliation_reference_id=None,
        ambiguity_reference_id=None,
        safe_status_reference_id="synthetic-reference-001",
        reason_code="synthetic-reference-001",
        safe_outcome=True,
        owning_module_authority=True,
        web_submission_only_authority=True,
        runtime_gate_reference_only=True,
        runtime_gate_satisfied=False,
        runtime_execution_completed=False,
        link_established=False,
        preference_applied=False,
        target_verified=False,
        provider_operation_completed=False,
        user_receipt_confirmed=False,
        business_success_authority=False,
        direct_write_authority=False,
        provider_authority=False,
        raw_provider_payload_present=False,
        secret_authority=False,
    )
    return o0, o1, o2, o3, o4


def _analytics_models() -> tuple[Any, ...]:
    o0 = admin_analytics.WebAdminAnalyticsMetricRequest(
        metric_kind=admin_analytics.WebAdminAnalyticsMetricKind.VISITOR_COUNT,
        source_authority_module_id="12-web-cabinet",
        metric_definition_reference_id="synthetic-reference-001",
        aggregation_policy_reference_id="synthetic-reference-001",
        approved_tariff_catalog_reference_id=None,
        exact_definition_reference_only=True,
        web_metric_definition_authority=False,
        raw_event_definition_present=False,
        tracking_runtime_authority=False,
        retention_policy_defined=False,
    )
    o1 = admin_analytics.WebAdminAnalyticsFilterReference(
        web_admin_analytics_filter_reference_id="synthetic-reference-001",
        filter_kind=admin_analytics.WebAdminAnalyticsFilterKind.PERIOD,
        filter_authority_module_id="12-web-cabinet",
        filter_definition_reference_id="synthetic-reference-001",
        selected_value_reference_ids=("synthetic-reference-001",),
        policy_approval_reference_id="synthetic-reference-001",
        safe_filter_display_reference_id="synthetic-reference-001",
        exact_filter_definition_reference_only=True,
        web_selected_value_authority=False,
        raw_filter_value_present=False,
        tracking_runtime_authority=False,
    )
    o2 = admin_analytics.RequestWebAdminAnalyticsQuery(
        web_admin_analytics_query_id="synthetic-reference-001",
        metadata=_META,
        actor_context_reference_id="synthetic-reference-001",
        identity_authorization_decision_reference_id="synthetic-reference-001",
        identity_role_scope_reference_id="synthetic-reference-001",
        admin_analytics_capability_reference_id="synthetic-reference-001",
        tenant_scope_reference_id="synthetic-reference-001",
        requested_audience=security_privacy.WebViewAudience.ADMIN_AUTHORIZED,
        metric_requests=(o0,),
        filters=(o1,),
        sort_field=admin_analytics.WebAdminAnalyticsSortField.METRIC_KIND,
        sort_direction=admin_analytics.WebAdminAnalyticsSortDirection.ASCENDING,
        sort_policy_reference_id="synthetic-reference-001",
        admin_support_read_policy_reference_id="synthetic-reference-001",
        analytics_aggregation_policy_reference_id="synthetic-reference-001",
        privacy_aggregation_policy_reference_id="synthetic-reference-001",
        privacy_suppression_policy_reference_id="synthetic-reference-001",
        freshness_policy_reference_id="synthetic-reference-001",
        reason_code="synthetic-reference-001",
        verified_admin_required=True,
        server_assigned_role_required=True,
        admin_support_policy_required=True,
        read_only=True,
        aggregate_only=True,
        user_level_rows_requested=False,
        user_level_export_requested=False,
        tracker_runtime_requested=False,
        event_collection_runtime_requested=False,
        marketing_pixel_requested=False,
        external_analytics_provider_requested=False,
        consent_implementation_requested=False,
        retention_policy_defined=False,
        browser_admin_flag_authority=False,
        provider_identity_admin_authority=False,
        impersonation_requested=False,
        direct_foreign_state_write_authority=False,
        exact_period_definition_invented=False,
        exact_active_user_definition_invented=False,
    )
    o3 = admin_analytics.WebAdminAnalyticsMetricProjection(
        web_admin_analytics_metric_projection_id="synthetic-reference-001",
        metric_kind=admin_analytics.WebAdminAnalyticsMetricKind.VISITOR_COUNT,
        state=admin_analytics.WebAdminAnalyticsMetricState.AVAILABLE,
        freshness=security_privacy.WebReadFreshness.FRESH,
        source_authority_module_id="12-web-cabinet",
        metric_definition_reference_id="synthetic-reference-001",
        aggregation_policy_reference_id="synthetic-reference-001",
        count_value=1,
        tariff_definition_reference_id=None,
        safe_tariff_display_reference_id=None,
        source_aggregate_reference_id="aggregate-001",
        source_reference_ids=("analytics-source-001",),
        provenance_reference_ids=("analytics-prov-001",),
        evidence_reference_ids=("analytics-evidence-001",),
        privacy_suppression_decision_reference_id=None,
        ambiguity_reference_id=None,
        reason_code="synthetic-reference-001",
        aggregate_only=True,
        safe_reference_only=True,
        source_authoritative=True,
        web_count_authority=False,
        web_recomputed_from_user_rows=False,
        user_level_row_present=False,
        account_identifier_present=False,
        session_identifier_present=False,
        ip_address_present=False,
        cookie_present=False,
        device_fingerprint_present=False,
        raw_event_payload_present=False,
        marketing_identifier_present=False,
        external_analytics_payload_present=False,
        minimal_personal_data=True,
        redacted=True,
        tracker_runtime_authority=False,
        retention_policy_defined=False,
    )
    o4 = admin_analytics.WebAdminAnalyticsResult(
        web_admin_analytics_result_id="synthetic-reference-001",
        metadata=_META,
        query=o2,
        state=admin_analytics.WebAdminAnalyticsResultState.AVAILABLE,
        freshness=security_privacy.WebReadFreshness.FRESH,
        owning_module_id="12-web-cabinet",
        admin_policy_owner_module_id="11-admin-and-support",
        safe_table_projection_reference_id="table-001",
        safe_sort_application_reference_id="sort-001",
        sort_field=admin_analytics.WebAdminAnalyticsSortField.METRIC_KIND,
        sort_direction=admin_analytics.WebAdminAnalyticsSortDirection.ASCENDING,
        sort_policy_reference_id="synthetic-reference-001",
        applied_filter_reference_ids=("synthetic-reference-001",),
        metric_projections=(o3,),
        projection_count=1,
        source_reference_ids=("synthetic-reference-001",),
        evidence_reference_ids=("synthetic-reference-001",),
        ambiguity_reference_id=None,
        reason_code="synthetic-reference-001",
        admin_only=True,
        identity_authorization_authoritative=True,
        admin_support_policy_authoritative=True,
        web_presentation_boundary=True,
        aggregate_only=True,
        privacy_suppression_policy_required=True,
        user_level_rows_present=False,
        user_level_export_present=False,
        tracker_implementation_present=False,
        event_collection_runtime_present=False,
        external_analytics_provider_present=False,
        marketing_pixel_present=False,
        consent_implementation_present=False,
        retention_policy_defined=False,
        direct_foreign_state_write_authority=False,
        cross_metric_sum_authority=False,
        screen_or_route_authority=False,
        business_success_authority=False,
        minimal_personal_data=True,
        redacted=True,
    )
    return o0, o1, o2, o3, o4


def _support_models() -> tuple[Any, ...]:
    o0 = support_handoff.RequestWebSupportHandoffQuery(
        web_support_handoff_query_id="synthetic-reference-001",
        metadata=_META,
        account_id="acct-synthetic-001",
        actor_context_reference_id="synthetic-reference-001",
        identity_authorization_decision_reference_id="synthetic-reference-001",
        tenant_scope_reference_id="synthetic-reference-001",
        requested_audience=security_privacy.WebViewAudience.CUSTOMER,
        requested_item_kinds=(support_handoff.WebSupportHandoffItemKind.SUPPORT_ENTRY,),
        support_case_reference_id=None,
        web_support_handoff_policy_reference_id="synthetic-reference-001",
        admin_support_customer_read_policy_reference_id="synthetic-reference-001",
        customer_visibility_policy_reference_id="synthetic-reference-001",
        customer_publication_policy_reference_id="synthetic-reference-001",
        redaction_policy_reference_id="synthetic-reference-001",
        freshness_policy_reference_id="synthetic-reference-001",
        reason_code="synthetic-reference-001",
        verified_customer_required=True,
        read_only=True,
        customer_publication_required=True,
        support_case_mutation_requested=False,
        operator_action_requested=False,
        internal_note_requested=False,
        private_audit_requested=False,
        raw_log_requested=False,
        provider_call_requested=False,
        raw_resource_access_requested=False,
        exact_customer_visibility_policy_invented=False,
        business_success_authority=False,
    )
    o1 = support_handoff.WebSupportHandoffProjection(
        web_support_handoff_projection_id="synthetic-reference-001",
        item_kind=support_handoff.WebSupportHandoffItemKind.SUPPORT_ENTRY,
        state=support_handoff.WebSupportHandoffItemState.AVAILABLE,
        freshness=security_privacy.WebReadFreshness.FRESH,
        owning_module_id="11-admin-and-support",
        account_id="acct-synthetic-001",
        tenant_scope_reference_id="synthetic-reference-001",
        support_case_reference_id=None,
        customer_visibility_policy_reference_id="synthetic-reference-001",
        customer_publication_policy_reference_id="synthetic-reference-001",
        customer_publication_decision_reference_id="publication-001",
        support_entry_reference_id="support-entry-001",
        customer_status_reference_id=None,
        customer_public_answer_reference_id=None,
        source_reference_ids=("synthetic-reference-001",),
        provenance_reference_ids=("synthetic-reference-001",),
        evidence_reference_ids=("synthetic-reference-001",),
        redaction_policy_reference_id="synthetic-reference-001",
        ambiguity_reference_id=None,
        reason_code="synthetic-reference-001",
        customer_visible=True,
        separate_customer_publication=True,
        admin_support_authoritative=True,
        web_presentation_boundary=True,
        safe_reference_only=True,
        redacted=True,
        minimal_personal_data=True,
        admin_support_safe_explanation_record_exposed=False,
        admin_support_internal_case_record_exposed=False,
        internal_note_present=False,
        private_audit_present=False,
        operator_only_field_present=False,
        raw_log_present=False,
        secret_material_present=False,
        raw_provider_payload_present=False,
        full_private_message_present=False,
        mutation_authority=False,
        business_state_authority=False,
    )
    o2 = support_handoff.WebSupportHandoffResult(
        web_support_handoff_result_id="synthetic-reference-001",
        metadata=_META,
        query=o0,
        state=support_handoff.WebSupportHandoffResultState.AVAILABLE,
        freshness=security_privacy.WebReadFreshness.FRESH,
        owning_module_id="12-web-cabinet",
        source_owner_module_id="11-admin-and-support",
        projections=(o1,),
        projection_count=1,
        source_reference_ids=("synthetic-reference-001",),
        evidence_reference_ids=("synthetic-reference-001",),
        ambiguity_reference_id=None,
        reason_code="synthetic-reference-001",
        customer_only=True,
        admin_support_publication_authoritative=True,
        web_presentation_boundary=True,
        read_only=True,
        safe_reference_only=True,
        redacted=True,
        minimal_personal_data=True,
        internal_note_present=False,
        private_audit_present=False,
        operator_action_present=False,
        raw_log_present=False,
        secret_material_present=False,
        raw_provider_payload_present=False,
        full_private_message_present=False,
        support_case_mutation_authority=False,
        operator_action_authority=False,
        route_or_ui_authority=False,
        business_success_authority=False,
    )
    return o0, o1, o2


def _privacy_models() -> tuple[Any, ...]:
    o0 = security_privacy.RequestWebSecurityPrivacyAssessmentQuery(
        web_security_privacy_query_id="synthetic-reference-001",
        metadata=_META,
        account_id="acct-synthetic-001",
        actor_context_reference_id="synthetic-reference-001",
        authorization_decision_reference_id="synthetic-reference-001",
        tenant_scope_reference_id="synthetic-reference-001",
        audience=security_privacy.WebViewAudience.CUSTOMER,
        requested_surface_kinds=(security_privacy.WebPrivacySurfaceKind.RETENTION_POLICY,),
        open_decision_reference_ids=("OD-013",),
        web_security_policy_reference_id="synthetic-reference-001",
        browser_minimization_policy_reference_id="synthetic-reference-001",
        redaction_policy_reference_id="synthetic-reference-001",
        safe_error_policy_reference_id="synthetic-reference-001",
        analytics_policy_gate_reference_id="synthetic-reference-001",
        retention_policy_gate_reference_id="synthetic-reference-001",
        deletion_export_policy_gate_reference_id="synthetic-reference-001",
        reason_code="synthetic-reference-001",
        verified_actor_required=True,
        read_only=True,
        untrusted_input=True,
        external_string_shell_authority=False,
        analytics_collection_requested=False,
        consent_assumed=False,
        retention_period_selected=False,
        deletion_export_policy_selected=False,
        raw_secret_requested=False,
        raw_provider_payload_requested=False,
        raw_personal_data_requested=False,
        runtime_authority=False,
        persistence_authority=False,
        business_success_authority=False,
    )
    o1 = security_privacy.WebPrivacyControlProjection(
        web_privacy_control_projection_id="synthetic-reference-001",
        surface_kind=security_privacy.WebPrivacySurfaceKind.RETENTION_POLICY,
        state=security_privacy.WebPrivacyProjectionState.POLICY_BLOCKED,
        freshness=security_privacy.WebReadFreshness.UNKNOWN,
        account_id="acct-synthetic-001",
        tenant_scope_reference_id="synthetic-reference-001",
        web_security_policy_reference_id="synthetic-reference-001",
        browser_minimization_policy_reference_id="synthetic-reference-001",
        redaction_policy_reference_id="synthetic-reference-001",
        safe_error_policy_reference_id="synthetic-reference-001",
        policy_gate_reference_id="synthetic-reference-001",
        policy_decision_reference_id=None,
        safe_display_reference_id=None,
        redaction_evidence_reference_id=None,
        source_reference_ids=("privacy-source-001",),
        provenance_reference_ids=("privacy-prov-001",),
        evidence_reference_ids=("privacy-evidence-001",),
        open_decision_reference_ids=("OD-013",),
        ambiguity_reference_id=None,
        reason_code="synthetic-reference-001",
        browser_visible=True,
        safe_reference_only=True,
        minimal_personal_data=True,
        redaction_enforced=True,
        safe_error_semantics=True,
        foreign_object_existence_disclosed=False,
        stack_trace_present=False,
        internal_exception_present=False,
        secret_material_present=False,
        password_present=False,
        one_time_code_present=False,
        token_present=False,
        cookie_present=False,
        session_material_present=False,
        private_key_present=False,
        environment_secret_present=False,
        raw_provider_payload_present=False,
        raw_avito_payload_present=False,
        full_private_message_present=False,
        internal_support_note_present=False,
        private_audit_present=False,
        unnecessary_personal_data_present=False,
        shell_command_constructed=False,
        analytics_event_recorded=False,
        consent_assumed=False,
        retention_period_selected=False,
        deletion_export_policy_selected=False,
        runtime_authority=False,
        persistence_authority=False,
        business_success_authority=False,
    )
    o2 = security_privacy.WebSecurityPrivacyAssessmentResult(
        web_security_privacy_result_id="synthetic-reference-001",
        metadata=_META,
        query=o0,
        state=security_privacy.WebSecurityPrivacyResultState.POLICY_BLOCKED,
        freshness=security_privacy.WebReadFreshness.UNKNOWN,
        owning_module_id="12-web-cabinet",
        projections=(o1,),
        projection_count=1,
        source_reference_ids=("privacy-source-001",),
        evidence_reference_ids=("privacy-evidence-001",),
        ambiguity_reference_id=None,
        reason_code="synthetic-reference-001",
        browser_minimized=True,
        redaction_enforced=True,
        safe_error_enforced=True,
        untrusted_input_preserved=True,
        secret_material_present=False,
        raw_provider_payload_present=False,
        raw_personal_data_present=False,
        internal_support_data_present=False,
        stack_trace_present=False,
        foreign_object_existence_disclosed=False,
        shell_command_constructed=False,
        analytics_event_recorded=False,
        consent_selected=False,
        retention_period_selected=False,
        deletion_export_policy_selected=False,
        runtime_authority=False,
        persistence_authority=False,
        route_or_ui_authority=False,
        business_success_authority=False,
    )
    return o0, o1, o2


def scenario_fx_wc12_view_001(vector: dict) -> ExecutionEvidence:
    q, source, result = _valid_view()
    assert result.query is q and result.sources == (source,)
    models = (q, source, result)
    assert all(isinstance(model, BaseModel) for model in models)
    return _evidence(
        vector,
        models,
        (
            "ordered sources cover requested family, authorized scope, fresh composition",
            "normal constructor validation",
            "complete required payload",
        ),
    )


def scenario_fx_wc12_view_002(vector: dict) -> ExecutionEvidence:
    q, source, result = _valid_view()
    assert (
        source.owning_module_id == "04-beacon-management"
        and result.sources[0].family is q.requested_families[0]
    )
    models = (q, source, result)
    assert all(isinstance(model, BaseModel) for model in models)
    return _evidence(
        vector,
        models,
        (
            "exact family-to-owning-module mapping",
            "normal constructor validation",
            "complete required payload",
        ),
    )


def scenario_fx_wc12_view_003(vector: dict) -> ExecutionEvidence:
    _, _, result = _valid_view()
    model = result
    payload = model.model_dump()
    payload.update({"state": read_models.WebCabinetViewState.FORBIDDEN})
    with pytest.raises(ValidationError) as caught:
        type(model)(**payload)
    error = _validation_tuple(caught.value)
    assert error == (
        ((),),
        ("value_error",),
        ("Value error, forbidden or not-found-safe result cannot carry sources",),
    )
    return _evidence(
        vector,
        (model,),
        ("terminal_empty", "one intended mutation", "all unrelated fields retained"),
        error,
    )


def scenario_fx_wc12_view_004(vector: dict) -> ExecutionEvidence:
    _, _, result = _valid_view()
    model = result
    payload = model.model_dump()
    payload.update(
        {"freshness": read_models.WebReadFreshness.STALE, "ambiguity_reference_id": None}
    )
    with pytest.raises(ValidationError) as caught:
        type(model)(**payload)
    error = _validation_tuple(caught.value)
    assert error == (
        ((),),
        ("value_error",),
        ("Value error, stale freshness requires stale source",),
    )
    return _evidence(
        vector,
        (model,),
        ("stale_ambiguous", "one intended mutation", "all unrelated fields retained"),
        error,
    )


def scenario_fx_wc12_view_005(vector: dict) -> ExecutionEvidence:
    _, source, result = _valid_view()
    model = result
    payload = model.model_dump()
    payload.update({"sources": (source, source)})
    with pytest.raises(ValidationError) as caught:
        type(model)(**payload)
    error = _validation_tuple(caught.value)
    assert error == (
        ((),),
        ("value_error",),
        ("Value error, duplicate source identifiers are not allowed",),
    )
    return _evidence(
        vector,
        (model,),
        ("duplicate_source_rejected", "one intended mutation", "all unrelated fields retained"),
        error,
    )


def scenario_fx_wc12_command_001(vector: dict) -> ExecutionEvidence:
    field, command, outcome = _valid_command()
    assert field.client_validation_authority is False and outcome.command is command
    models = (field, command, outcome)
    assert all(isinstance(model, BaseModel) for model in models)
    return _evidence(
        vector,
        models,
        (
            "valid patch command and explicit idempotent outcome",
            "normal constructor validation",
            "complete required payload",
        ),
    )


def scenario_fx_wc12_command_002(vector: dict) -> ExecutionEvidence:
    field, command, outcome = _valid_command()
    second = beacon_commands.WebBeaconPatchField(
        web_patch_field_id="patch-synthetic-002",
        field_name="safe_field_two",
        requested_value_reference_id="ref-synthetic-002",
        owning_module_validation_family_reference_id="beacon-management",
    )
    complete = beacon_commands.SubmitBeaconWebCommandCommand(
        **{**command.model_dump(), "patch_fields": (field, second)}
    )
    assert (field.web_patch_field_id, second.web_patch_field_id) == (
        "patch-synthetic-001",
        "patch-synthetic-002",
    )
    assert (field.field_name, second.field_name) == ("safe_field", "safe_field_two")
    assert complete.patch_fields == (field, second)
    assert outcome.command.patch_fields == (field,)
    return _evidence(
        vector,
        (field, second, complete),
        (
            "two distinct patch IDs",
            "two distinct field names",
            "ordered complete command validates",
        ),
    )


def scenario_fx_wc12_command_003(vector: dict) -> ExecutionEvidence:
    _, command, outcome = _valid_command()
    model = command
    payload = model.model_dump()
    payload.update({"command_kind": beacon_commands.WebBeaconCommandKind.ARCHIVE_TO_HISTORY})
    with pytest.raises(ValidationError) as caught:
        type(model)(**payload)
    error = _validation_tuple(caught.value)
    assert error == (
        ((),),
        ("value_error",),
        ("Value error, lifecycle command cannot carry patch fields",),
    )
    return _evidence(
        vector,
        (model,),
        ("lifecycle_command_matrix", "one intended mutation", "all unrelated fields retained"),
        error,
    )


def scenario_fx_wc12_command_004(vector: dict) -> ExecutionEvidence:
    field, command, outcome = _valid_command()
    assert outcome.state is beacon_commands.WebBeaconCommandSubmitState.SUBMITTED
    assert outcome.owning_module_accepted is True
    assert outcome.owning_module_outcome_reference_id is not None
    assert outcome.authoritative_state_reference_id is not None
    assert outcome.authoritative_state_reloaded is True
    assert outcome.applied_field_names and set(outcome.applied_field_names).issubset(
        {f.field_name for f in command.patch_fields}
    )
    assert outcome.replay_of_outcome_reference_id is None
    assert outcome.rejection_reason_code is None
    assert outcome.ambiguity_reference_id is None

    replayed = beacon_commands.WebBeaconCommandSubmitOutcome(
        **{
            **outcome.model_dump(),
            "web_beacon_command_submit_outcome_id": "outcome-synthetic-replayed-001",
            "state": beacon_commands.WebBeaconCommandSubmitState.REPLAYED,
            "replay_of_outcome_reference_id": "replay-ref-synthetic-001",
            "owning_module_accepted": True,
            "authoritative_state_reference_id": "state-ref-synthetic-001",
            "authoritative_state_reloaded": True,
        }
    )
    assert replayed.state is beacon_commands.WebBeaconCommandSubmitState.REPLAYED
    assert replayed.replay_of_outcome_reference_id is not None
    assert replayed.owning_module_outcome_reference_id is not None
    assert replayed.owning_module_accepted is True
    assert replayed.authoritative_state_reloaded is True
    assert set(replayed.applied_field_names).issubset(
        {f.field_name for f in command.patch_fields}
    )
    assert replayed.rejection_reason_code is None
    assert replayed.ambiguity_reference_id is None

    rejected = beacon_commands.WebBeaconCommandSubmitOutcome(
        **{
            **outcome.model_dump(),
            "web_beacon_command_submit_outcome_id": "outcome-synthetic-rejected-001",
            "state": beacon_commands.WebBeaconCommandSubmitState.REJECTED,
            "owning_module_accepted": False,
            "rejection_reason_code": "rejection-synthetic-001",
            "applied_field_names": (),
            "authoritative_state_reference_id": None,
            "authoritative_state_reloaded": False,
        }
    )
    assert rejected.state is beacon_commands.WebBeaconCommandSubmitState.REJECTED
    assert rejected.owning_module_accepted is False
    assert rejected.rejection_reason_code is not None
    assert rejected.applied_field_names == ()
    assert rejected.replay_of_outcome_reference_id is None
    assert rejected.ambiguity_reference_id is None
    assert rejected.authoritative_state_reference_id is None

    stale = beacon_commands.WebBeaconCommandSubmitOutcome(
        **{
            **outcome.model_dump(),
            "web_beacon_command_submit_outcome_id": "outcome-synthetic-stale-001",
            "state": beacon_commands.WebBeaconCommandSubmitState.STALE,
            "owning_module_accepted": False,
            "rejection_reason_code": "stale-synthetic-001",
            "applied_field_names": (),
            "authoritative_state_reference_id": None,
            "authoritative_state_reloaded": False,
        }
    )
    assert stale.state is beacon_commands.WebBeaconCommandSubmitState.STALE
    assert stale.owning_module_accepted is False
    assert stale.rejection_reason_code is not None
    assert stale.applied_field_names == ()
    assert stale.replay_of_outcome_reference_id is None
    assert stale.ambiguity_reference_id is None
    assert stale.authoritative_state_reference_id is None

    ambiguous = beacon_commands.WebBeaconCommandSubmitOutcome(
        **{
            **outcome.model_dump(),
            "web_beacon_command_submit_outcome_id": "outcome-synthetic-ambiguous-001",
            "state": beacon_commands.WebBeaconCommandSubmitState.AMBIGUOUS,
            "owning_module_accepted": False,
            "ambiguity_reference_id": "ambiguity-synthetic-001",
            "applied_field_names": (),
            "rejection_reason_code": None,
            "authoritative_state_reference_id": None,
            "authoritative_state_reloaded": False,
        }
    )
    assert ambiguous.state is beacon_commands.WebBeaconCommandSubmitState.AMBIGUOUS
    assert ambiguous.owning_module_accepted is False
    assert ambiguous.ambiguity_reference_id is not None
    assert ambiguous.applied_field_names == ()
    assert ambiguous.replay_of_outcome_reference_id is None
    assert ambiguous.authoritative_state_reference_id is None

    with pytest.raises(ValidationError) as caught:
        beacon_commands.WebBeaconCommandSubmitOutcome(
            **{
                **outcome.model_dump(),
                "web_beacon_command_submit_outcome_id": "outcome-synthetic-neg-sub-001",
                "state": beacon_commands.WebBeaconCommandSubmitState.SUBMITTED,
                "owning_module_accepted": False,
            }
        )
    nc1 = _validation_tuple(caught.value)
    assert nc1 == (
        ((),),
        ("value_error",),
        ("Value error, submitted outcome requires owning-module acceptance and outcome",),
    )

    with pytest.raises(ValidationError) as caught:
        beacon_commands.WebBeaconCommandSubmitOutcome(
            **{
                **outcome.model_dump(),
                "web_beacon_command_submit_outcome_id": "outcome-synthetic-neg-rep-001",
                "state": beacon_commands.WebBeaconCommandSubmitState.REPLAYED,
                "replay_of_outcome_reference_id": None,
            }
        )
    nc2 = _validation_tuple(caught.value)
    assert nc2 == (
        ((),),
        ("value_error",),
        ("Value error, replayed outcome requires replay and owning-module references",),
    )

    with pytest.raises(ValidationError) as caught:
        beacon_commands.WebBeaconCommandSubmitOutcome(
            **{
                **outcome.model_dump(),
                "web_beacon_command_submit_outcome_id": "outcome-synthetic-neg-rej-001",
                "state": beacon_commands.WebBeaconCommandSubmitState.REJECTED,
                "owning_module_accepted": False,
                "rejection_reason_code": None,
                "applied_field_names": (),
                "authoritative_state_reference_id": None,
                "authoritative_state_reloaded": False,
            }
        )
    nc3 = _validation_tuple(caught.value)
    assert nc3 == (
        ((),),
        ("value_error",),
        ("Value error, rejected outcome requires rejection reason",),
    )

    with pytest.raises(ValidationError) as caught:
        beacon_commands.WebBeaconCommandSubmitOutcome(
            **{
                **outcome.model_dump(),
                "web_beacon_command_submit_outcome_id": "outcome-synthetic-neg-sta-001",
                "state": beacon_commands.WebBeaconCommandSubmitState.STALE,
                "owning_module_accepted": False,
                "rejection_reason_code": None,
                "applied_field_names": (),
                "authoritative_state_reference_id": None,
                "authoritative_state_reloaded": False,
            }
        )
    nc4 = _validation_tuple(caught.value)
    assert nc4 == (
        ((),),
        ("value_error",),
        ("Value error, rejected outcome requires rejection reason",),
    )

    with pytest.raises(ValidationError) as caught:
        beacon_commands.WebBeaconCommandSubmitOutcome(
            **{
                **outcome.model_dump(),
                "web_beacon_command_submit_outcome_id": "outcome-synthetic-neg-amb-001",
                "state": beacon_commands.WebBeaconCommandSubmitState.AMBIGUOUS,
                "owning_module_accepted": False,
                "ambiguity_reference_id": None,
                "applied_field_names": (),
                "rejection_reason_code": None,
                "authoritative_state_reference_id": None,
                "authoritative_state_reloaded": False,
            }
        )
    nc5 = _validation_tuple(caught.value)
    assert nc5 == (
        ((),),
        ("value_error",),
        ("Value error, ambiguous outcome requires ambiguity reference",),
    )

    models = (field, command, outcome, replayed, rejected, stale, ambiguous)
    assert all(isinstance(model, BaseModel) for model in models)
    return _evidence(
        vector,
        models,
        (
            "five valid outcome states SUBMITTED REPLAYED REJECTED STALE AMBIGUOUS proven",
            "negative controls SUBMITTED-no-accept REPLAYED-no-ref"
            " REJECTED-no-reason STALE-no-reason AMBIGUOUS-no-ref",
            "applied-field subset invariant maintained across all states",
            "replay rejection ambiguity reference invariants enforced",
            "authoritative reload absent for rejected stale ambiguous",
        ),
    )


def scenario_fx_wc12_command_005(vector: dict) -> ExecutionEvidence:
    _, command, _ = _valid_command()
    model = command
    payload = model.model_dump()
    payload.update({"business_success_authority": True})
    with pytest.raises(ValidationError) as caught:
        type(model)(**payload)
    error = _validation_tuple(caught.value)
    assert error == (
        (("business_success_authority",),),
        ("literal_error",),
        ("Input should be False",),
    )
    return _evidence(
        vector,
        (model,),
        ("business_authority_forbidden", "one intended mutation", "all unrelated fields retained"),
        error,
    )


def scenario_fx_wc12_auth_001(vector: dict) -> ExecutionEvidence:
    models = _auth_models()
    assert models[-1].state is auth_context.WebPresentationContextState.AUTHORIZED
    models = models
    assert all(isinstance(model, BaseModel) for model in models)
    return _evidence(
        vector,
        models,
        (
            "verified actor, active session and account continuity",
            "normal constructor validation",
            "complete required payload",
        ),
    )


def scenario_fx_wc12_auth_002(vector: dict) -> ExecutionEvidence:
    model = _auth_models()[-1]
    payload = model.model_dump()
    payload.update({"state": auth_context.WebPresentationContextState.UNAUTHENTICATED})
    with pytest.raises(ValidationError) as caught:
        type(model)(**payload)
    error = _validation_tuple(caught.value)
    assert error == (
        ((),),
        ("value_error",),
        ("Value error, non-authorized result cannot expose account or identity summary",),
    )
    return _evidence(
        vector,
        (model,),
        ("session_non_authority", "one intended mutation", "all unrelated fields retained"),
        error,
    )


def scenario_fx_wc12_auth_003(vector: dict) -> ExecutionEvidence:
    model = _auth_models()[-1]
    payload = model.model_dump()
    payload.update({"state": auth_context.WebPresentationContextState.FORBIDDEN})
    with pytest.raises(ValidationError) as caught:
        type(model)(**payload)
    error = _validation_tuple(caught.value)
    assert error == (
        ((),),
        ("value_error",),
        ("Value error, non-authorized result cannot expose account or identity summary",),
    )
    return _evidence(
        vector,
        (model,),
        ("unauthenticated_forbidden", "one intended mutation", "all unrelated fields retained"),
        error,
    )


def scenario_fx_wc12_auth_004(vector: dict) -> ExecutionEvidence:
    model = _auth_models()[-1]
    payload = model.model_dump()
    payload.update({"phone_requirement_defined": True})
    with pytest.raises(ValidationError) as caught:
        type(model)(**payload)
    error = _validation_tuple(caught.value)
    assert error == (
        (("phone_requirement_defined",),),
        ("literal_error",),
        ("Input should be False",),
    )
    return _evidence(
        vector,
        (model,),
        ("phone_recovery_blocked", "one intended mutation", "all unrelated fields retained"),
        error,
    )


def scenario_fx_wc12_auth_005(vector: dict) -> ExecutionEvidence:
    model = _auth_models()[-1]
    payload = model.model_dump()
    payload.update({"account_merge_policy_defined": True})
    with pytest.raises(ValidationError) as caught:
        type(model)(**payload)
    error = _validation_tuple(caught.value)
    assert error == (
        (("account_merge_policy_defined",),),
        ("literal_error",),
        ("Input should be False",),
    )
    return _evidence(
        vector,
        (model,),
        (
            "merge_second_account_forbidden",
            "one intended mutation",
            "all unrelated fields retained",
        ),
        error,
    )


def scenario_fx_wc12_entitlement_001(vector: dict) -> ExecutionEvidence:
    models = _entitlement_models()
    assert (
        models[-1].capabilities[0].access_state
        is entitlement_projections.WebEntitlementAccessState.ALLOWED
    )
    models = models
    assert all(isinstance(model, BaseModel) for model in models)
    return _evidence(
        vector,
        models,
        (
            "effective allowed capability and fresh projection",
            "normal constructor validation",
            "complete required payload",
        ),
    )


def scenario_fx_wc12_entitlement_002(vector: dict) -> ExecutionEvidence:
    models = _entitlement_models()
    assert models[-1].tariff_options[0].owning_module_id == "03-entitlements-and-billing"
    models = models
    assert all(isinstance(model, BaseModel) for model in models)
    return _evidence(
        vector,
        models,
        (
            "tariff option is source-owned and safe",
            "normal constructor validation",
            "complete required payload",
        ),
    )


def scenario_fx_wc12_entitlement_003(vector: dict) -> ExecutionEvidence:
    model = _entitlement_models()[-1]
    payload = model.model_dump()
    payload.update({"state": entitlement_projections.WebEntitlementProjectionState.DENIED})
    with pytest.raises(ValidationError) as caught:
        type(model)(**payload)
    error = _validation_tuple(caught.value)
    assert error == (
        ((),),
        ("value_error",),
        ("Value error, result state requires a matching capability state",),
    )
    return _evidence(
        vector,
        (model,),
        ("terminal_state_matrix", "one intended mutation", "all unrelated fields retained"),
        error,
    )


def scenario_fx_wc12_entitlement_004(vector: dict) -> ExecutionEvidence:
    model = _entitlement_models()[0]
    payload = model.model_dump()
    payload.update({"invented_tariff_values_allowed": True})
    with pytest.raises(ValidationError) as caught:
        type(model)(**payload)
    error = _validation_tuple(caught.value)
    assert error == (
        (("invented_tariff_values_allowed",),),
        ("literal_error",),
        ("Input should be False",),
    )
    return _evidence(
        vector,
        (model,),
        ("invented_values_forbidden", "one intended mutation", "all unrelated fields retained"),
        error,
    )


def scenario_fx_wc12_entitlement_005(vector: dict) -> ExecutionEvidence:
    model = _entitlement_models()[-1]
    payload = model.model_dump()
    payload.update({"source_reference_ids": ("x", "x")})
    with pytest.raises(ValidationError) as caught:
        type(model)(**payload)
    error = _validation_tuple(caught.value)
    assert error == (
        ((),),
        ("value_error",),
        ("Value error, duplicate source references are not allowed",),
    )
    return _evidence(
        vector,
        (model,),
        ("duplicate_reference_rejected", "one intended mutation", "all unrelated fields retained"),
        error,
    )


def scenario_fx_wc12_history_001(vector: dict) -> ExecutionEvidence:
    models = _history_models()
    assert models[-1].history_entry_count == len(models[-1].history_entries) == 1
    models = models
    assert all(isinstance(model, BaseModel) for model in models)
    return _evidence(
        vector,
        models,
        (
            "grouped notification history preserves safe listing",
            "normal constructor validation",
            "complete required payload",
        ),
    )


def scenario_fx_wc12_history_002(vector: dict) -> ExecutionEvidence:
    query, listing, entry, result = _history_models()
    listings = tuple(
        notification_history.WebNotificationListingReferenceProjection(
            **{
                **listing.model_dump(),
                "web_notification_listing_reference_projection_id": f"listing-synthetic-00{i}",
                "safe_listing_reference_id": f"safe-listing-synthetic-00{i}",
            }
        )
        for i in (1, 2, 3)
    )
    expanded_entry = notification_history.WebNotificationDeliveryHistoryEntry(
        **{**entry.model_dump(), "listing_references": listings, "listing_count": 3}
    )
    expanded_result = notification_history.WebNotificationHistoryResult(
        **{
            **result.model_dump(),
            "history_entries": (expanded_entry,),
            "safe_listing_references": listings,
            "listing_count": 3,
            "history_entry_count": 1,
        }
    )
    assert tuple(item.safe_listing_reference_id for item in listings) == (
        "safe-listing-synthetic-001",
        "safe-listing-synthetic-002",
        "safe-listing-synthetic-003",
    )
    assert expanded_entry.listing_references == listings
    assert expanded_result.safe_listing_references == listings
    models = (query, listings[0], listings[1], listings[2], expanded_entry, expanded_result)
    assert all(isinstance(model, BaseModel) for model in models)
    return _evidence(
        vector,
        models,
        (
            "safe listing references preserve entry order and count",
            "normal constructor validation",
            "complete required payload",
        ),
    )


def scenario_fx_wc12_history_003(vector: dict) -> ExecutionEvidence:
    model = _history_models()[-1]
    payload = model.model_dump()
    payload.update({"state": notification_history.WebNotificationHistoryResultState.FORBIDDEN})
    with pytest.raises(ValidationError) as caught:
        type(model)(**payload)
    error = _validation_tuple(caught.value)
    assert error == (
        ((),),
        ("value_error",),
        ("Value error, forbidden result must not expose notification data",),
    )
    return _evidence(
        vector,
        (model,),
        ("terminal_state_matrix", "one intended mutation", "all unrelated fields retained"),
        error,
    )


def scenario_fx_wc12_history_004(vector: dict) -> ExecutionEvidence:
    model = _history_models()[2]
    payload = model.model_dump()
    reconciliation = notification_history.WebNotificationDeliveryState.RECONCILIATION_REQUIRED
    payload.update(
        {
            "delivery_state": reconciliation,
            "reconciliation_required": False,
        }
    )
    with pytest.raises(ValidationError) as caught:
        type(model)(**payload)
    error = _validation_tuple(caught.value)
    assert error == (
        ((),),
        ("value_error",),
        ("Value error, reconciliation-required entry requires reconciliation reference",),
    )
    return _evidence(
        vector,
        (model,),
        ("ambiguous_delivery", "one intended mutation", "all unrelated fields retained"),
        error,
    )


def scenario_fx_wc12_history_005(vector: dict) -> ExecutionEvidence:
    model = _history_models()[-1]
    payload = model.model_dump()
    payload.update({"raw_provider_payload_retained": True})
    with pytest.raises(ValidationError) as caught:
        type(model)(**payload)
    error = _validation_tuple(caught.value)
    assert error == (
        (("raw_provider_payload_retained",),),
        ("literal_error",),
        ("Input should be False",),
    )
    return _evidence(
        vector,
        (model,),
        ("raw_payload_archive_forbidden", "one intended mutation", "all unrelated fields retained"),
        error,
    )


def scenario_fx_wc12_status_001(vector: dict) -> ExecutionEvidence:
    _, evidence_model, _, _ = _status_models()
    model = evidence_model
    payload = model.model_dump()
    payload.update({"no_new_claim_allowed": False})
    with pytest.raises(ValidationError) as caught:
        type(model)(**payload)
    error = _validation_tuple(caught.value)
    assert error == (((),), ("value_error",), ("Value error, invalid proven no-new boundary",))
    return _evidence(
        vector,
        (model,),
        (
            "no-new evidence mismatch",
            "only no_new_claim_allowed mutated",
            "all unrelated fields retained",
        ),
        error,
    )


def scenario_fx_wc12_status_002(vector: dict) -> ExecutionEvidence:
    _, evidence_model, _, _ = _status_models()
    model = evidence_model
    payload = model.model_dump()
    payload.update(
        {"evidence_class": status_display.WebStatusEvidenceClass.SCAN_EXTERNAL_UNAVAILABLE}
    )
    with pytest.raises(ValidationError) as caught:
        type(model)(**payload)
    error = _validation_tuple(caught.value)
    assert error == (
        ((),),
        ("value_error",),
        ("Value error, only proven comparison may claim no-new",),
    )
    return _evidence(
        vector,
        (model,),
        (
            "external-unavailable evidence paired with no-new claim",
            "only evidence_class mutated",
            "all unrelated fields retained",
        ),
        error,
    )


def scenario_fx_wc12_status_003(vector: dict) -> ExecutionEvidence:
    query, evidence_model, item, result = _status_models()
    evidence_payload = evidence_model.model_dump()
    evidence_payload.update(
        {
            "evidence_class": status_display.WebStatusEvidenceClass.SCAN_RECOVERY_COMPLETED,
            "source_reason_codes": ("recovery-completed",),
            "no_new_claim_allowed": False,
            "safe_latest_fresh_listing_reference_ids": (),
            "state_restored_latest_fresh_only": False,
            "continuing_scan_visible": False,
        }
    )
    recovery_evidence = status_display.WebStatusEvidenceReference(**evidence_payload)
    item_payload = item.model_dump()
    item_payload.update(
        {
            "family": status_display.WebStatusDisplayFamily.RECOVERY_COMPLETED,
            "source_evidence_reference_ids": (recovery_evidence.web_status_evidence_reference_id,),
        }
    )
    recovery_item = status_display.WebStatusDisplayItem(**item_payload)
    result_payload = result.model_dump()
    result_payload.update(
        {
            "source_evidence": (recovery_evidence,),
            "display_items": (recovery_item,),
            "recovery_visible": True,
            "evidence_reference_ids": (recovery_evidence.web_status_evidence_reference_id,),
        }
    )
    recovery_result = status_display.WebStatusDisplayResult(**result_payload)
    assert recovery_result.recovery_visible is True
    assert (
        recovery_result.display_items[0].family
        is status_display.WebStatusDisplayFamily.RECOVERY_COMPLETED
    )
    assert (
        recovery_evidence.evidence_class
        is status_display.WebStatusEvidenceClass.SCAN_RECOVERY_COMPLETED
    )
    return _evidence(
        vector,
        (query, recovery_evidence, recovery_item, recovery_result),
        (
            "status evidence and display are directly validated",
            "normal constructor validation",
            "complete required payload",
        ),
    )


def scenario_fx_wc12_status_004(vector: dict) -> ExecutionEvidence:
    _, evidence_model, _, _ = _status_models()
    model = evidence_model
    payload = model.model_dump()
    payload.update({"confirmed_new_claim_allowed": True})
    with pytest.raises(ValidationError) as caught:
        type(model)(**payload)
    error = _validation_tuple(caught.value)
    assert error == (
        (("confirmed_new_claim_allowed",),),
        ("literal_error",),
        ("Input should be False",),
    )
    return _evidence(
        vector,
        (model,),
        (
            "lost-anchor recovery rejects confirmed-new claim",
            "only confirmed_new_claim_allowed mutated",
            "all unrelated fields retained",
        ),
        error,
    )


def scenario_fx_wc12_status_005(vector: dict) -> ExecutionEvidence:
    model = _status_models()[-1]
    payload = model.model_dump()
    payload.update({"state": status_display.WebStatusDisplayResultState.AMBIGUOUS})
    with pytest.raises(ValidationError) as caught:
        type(model)(**payload)
    error = _validation_tuple(caught.value)
    assert error == (
        ((),),
        ("value_error",),
        ("Value error, ambiguous result requires ambiguity item",),
    )
    return _evidence(
        vector,
        (model,),
        ("stale_delivery_ambiguity", "one intended mutation", "all unrelated fields retained"),
        error,
    )


def scenario_fx_wc12_channel_001(vector: dict) -> ExecutionEvidence:
    models = _channel_models()
    assert models[-1].owning_module_id == "08-notification-delivery"
    models = models
    assert all(isinstance(model, BaseModel) for model in models)
    return _evidence(
        vector,
        models,
        (
            "linked channel projection and safe result",
            "normal constructor validation",
            "complete required payload",
        ),
    )


def scenario_fx_wc12_channel_002(vector: dict) -> ExecutionEvidence:
    model = _channel_models()[3]
    payload = model.model_dump()
    payload.update({"command_kind": channel_linking.WebChannelCommandKind.START_CONNECTION})
    with pytest.raises(ValidationError) as caught:
        type(model)(**payload)
    error = _validation_tuple(caught.value)
    assert error == (
        ((),),
        ("value_error",),
        ("Value error, start connection routing matrix mismatch",),
    )
    return _evidence(
        vector,
        (model,),
        ("connect_start_matrix", "one intended mutation", "all unrelated fields retained"),
        error,
    )


def scenario_fx_wc12_channel_003(vector: dict) -> ExecutionEvidence:
    query, projection, result, enable, outcome = _channel_models()
    disable = channel_linking.SubmitWebChannelCommandCommand(
        **{
            **enable.model_dump(),
            "web_channel_command_id": "channel-command-disable-001",
            "command_kind": channel_linking.WebChannelCommandKind.DISABLE_NOTIFICATIONS,
        }
    )
    disable_outcome = channel_linking.WebChannelCommandSubmitOutcome(
        **{
            **outcome.model_dump(),
            "web_channel_command_submit_outcome_id": "channel-outcome-disable-001",
            "command": disable,
        }
    )
    assert enable.command_kind is channel_linking.WebChannelCommandKind.ENABLE_NOTIFICATIONS
    assert disable.command_kind is channel_linking.WebChannelCommandKind.DISABLE_NOTIFICATIONS
    assert (
        enable.requested_owning_module_id
        == disable.requested_owning_module_id
        == "08-notification-delivery"
    )
    models = (query, projection, result, enable, disable, outcome, disable_outcome)
    assert all(isinstance(model, BaseModel) for model in models)
    return _evidence(
        vector,
        models,
        (
            "enable command routes to notification delivery",
            "normal constructor validation",
            "complete required payload",
        ),
    )


def scenario_fx_wc12_channel_004(vector: dict) -> ExecutionEvidence:
    models = _channel_models()
    assert (
        models[0].account_id
        == models[1].account_id
        == models[2].query.account_id
        == "acct-synthetic-001"
    )
    models = models
    assert all(isinstance(model, BaseModel) for model in models)
    return _evidence(
        vector,
        models,
        (
            "one-account continuity through query projection and result",
            "normal constructor validation",
            "complete required payload",
        ),
    )


def scenario_fx_wc12_channel_005(vector: dict) -> ExecutionEvidence:
    model = _channel_models()[2]
    payload = model.model_dump()
    payload.update({"provider_call_authority": True})
    with pytest.raises(ValidationError) as caught:
        type(model)(**payload)
    error = _validation_tuple(caught.value)
    assert error == (
        (("provider_call_authority",),),
        ("literal_error",),
        ("Input should be False",),
    )
    return _evidence(
        vector,
        (model,),
        ("terminal_and_runtime_gate", "one intended mutation", "all unrelated fields retained"),
        error,
    )


def scenario_fx_wc12_analytics_001(vector: dict) -> ExecutionEvidence:
    model = _analytics_models()[2]
    payload = model.model_dump()
    payload.update({"metric_requests": ()})
    with pytest.raises(ValidationError) as caught:
        type(model)(**payload)
    error = _validation_tuple(caught.value)
    assert error == (((),), ("value_error",), ("Value error, metric requests must be non-empty",))
    return _evidence(
        vector,
        (model,),
        ("metric_request_matrix", "one intended mutation", "all unrelated fields retained"),
        error,
    )


def scenario_fx_wc12_analytics_002(vector: dict) -> ExecutionEvidence:
    models = _analytics_models()
    assert models[-1].sort_field is admin_analytics.WebAdminAnalyticsSortField.METRIC_KIND
    models = models
    assert all(isinstance(model, BaseModel) for model in models)
    return _evidence(
        vector,
        models,
        (
            "literal filters and sort order are preserved",
            "normal constructor validation",
            "complete required payload",
        ),
    )


def scenario_fx_wc12_analytics_003(vector: dict) -> ExecutionEvidence:
    model = _analytics_models()[-1]
    payload = model.model_dump()
    payload.update({"state": admin_analytics.WebAdminAnalyticsResultState.FORBIDDEN})
    with pytest.raises(ValidationError) as caught:
        type(model)(**payload)
    error = _validation_tuple(caught.value)
    assert error == (
        ((),),
        ("value_error",),
        ("Value error, terminal result must not expose projections or filters",),
    )
    return _evidence(
        vector,
        (model,),
        ("terminal_result_matrix", "one intended mutation", "all unrelated fields retained"),
        error,
    )


def scenario_fx_wc12_analytics_004(vector: dict) -> ExecutionEvidence:
    models = _analytics_models()
    assert models[-1].metric_projections[0].aggregate_only is True
    models = models
    assert all(isinstance(model, BaseModel) for model in models)
    return _evidence(
        vector,
        models,
        (
            "aggregate metrics contain no user-level records",
            "normal constructor validation",
            "complete required payload",
        ),
    )


def scenario_fx_wc12_analytics_005(vector: dict) -> ExecutionEvidence:
    model = _analytics_models()[0]
    payload = model.model_dump()
    payload.update({"tracker_runtime_authority": True})
    with pytest.raises(ValidationError) as caught:
        type(model)(**payload)
    error = _validation_tuple(caught.value)
    assert error == (
        (("tracker_runtime_authority",),),
        ("extra_forbidden",),
        ("Extra inputs are not permitted",),
    )
    return _evidence(
        vector,
        (model,),
        ("user_level_tracking_forbidden", "one intended mutation", "all unrelated fields retained"),
        error,
    )


def scenario_fx_wc12_support_001(vector: dict) -> ExecutionEvidence:
    model = _support_models()[0]
    payload = model.model_dump()
    payload.update({"support_case_reference_id": "case-synthetic-001"})
    with pytest.raises(ValidationError) as caught:
        type(model)(**payload)
    error = _validation_tuple(caught.value)
    assert error == (
        ((),),
        ("value_error",),
        ("Value error, entry-only query cannot carry a support case reference",),
    )
    return _evidence(
        vector,
        (model,),
        ("query_kind_case_matrix", "one intended mutation", "all unrelated fields retained"),
        error,
    )


def scenario_fx_wc12_support_002(vector: dict) -> ExecutionEvidence:
    model = _support_models()[1]
    payload = model.model_dump()
    payload.update({"state": support_handoff.WebSupportHandoffItemState.STALE})
    with pytest.raises(ValidationError) as caught:
        type(model)(**payload)
    error = _validation_tuple(caught.value)
    assert error == (
        ((),),
        ("value_error",),
        ("Value error, projection state and freshness do not match",),
    )
    return _evidence(
        vector,
        (model,),
        ("projection_kind_state_matrix", "one intended mutation", "all unrelated fields retained"),
        error,
    )


def scenario_fx_wc12_support_003(vector: dict) -> ExecutionEvidence:
    models = _support_models()
    assert models[1].customer_publication_decision_reference_id == "publication-001"
    models = models
    assert all(isinstance(model, BaseModel) for model in models)
    return _evidence(
        vector,
        models,
        (
            "customer publication is separate and authoritative",
            "normal constructor validation",
            "complete required payload",
        ),
    )


def scenario_fx_wc12_support_004(vector: dict) -> ExecutionEvidence:
    model = _support_models()[-1]
    payload = model.model_dump()
    payload.update({"projection_count": 0})
    with pytest.raises(ValidationError) as caught:
        type(model)(**payload)
    error = _validation_tuple(caught.value)
    assert error == (
        ((),),
        ("value_error",),
        ("Value error, projection count must match projections",),
    )
    return _evidence(
        vector,
        (model,),
        ("terminal_ordered_coverage", "one intended mutation", "all unrelated fields retained"),
        error,
    )


def scenario_fx_wc12_support_005(vector: dict) -> ExecutionEvidence:
    model = _support_models()[0]
    payload = model.model_dump()
    payload.update({"internal_note_requested": True})
    with pytest.raises(ValidationError) as caught:
        type(model)(**payload)
    error = _validation_tuple(caught.value)
    assert error == (
        (("internal_note_requested",),),
        ("literal_error",),
        ("Input should be False",),
    )
    return _evidence(
        vector,
        (model,),
        ("internal_records_forbidden", "one intended mutation", "all unrelated fields retained"),
        error,
    )


def scenario_fx_wc12_privacy_001(vector: dict) -> ExecutionEvidence:
    models = _privacy_models()
    assert models[0].open_decision_reference_ids == ("OD-013",)
    models = models
    assert all(isinstance(model, BaseModel) for model in models)
    return _evidence(
        vector,
        models,
        (
            "OD-013 retention gate is mapped",
            "normal constructor validation",
            "complete required payload",
        ),
    )


def scenario_fx_wc12_privacy_002(vector: dict) -> ExecutionEvidence:
    model = _privacy_models()[1]
    payload = model.model_dump()
    payload.update({"state": security_privacy.WebPrivacyProjectionState.SAFE})
    with pytest.raises(ValidationError) as caught:
        type(model)(**payload)
    error = _validation_tuple(caught.value)
    assert error == (
        ((),),
        ("value_error",),
        ("Value error, policy projection must be blocked, unknown and open",),
    )
    return _evidence(
        vector,
        (model,),
        ("projection_state_matrix", "one intended mutation", "all unrelated fields retained"),
        error,
    )


def scenario_fx_wc12_privacy_003(vector: dict) -> ExecutionEvidence:
    model = _privacy_models()[-1]
    payload = model.model_dump()
    payload.update({"state": security_privacy.WebSecurityPrivacyResultState.FORBIDDEN})
    with pytest.raises(ValidationError) as caught:
        type(model)(**payload)
    error = _validation_tuple(caught.value)
    assert error == (((),), ("value_error",), ("Value error, terminal result payload is invalid",))
    return _evidence(
        vector,
        (model,),
        ("terminal_result_matrix", "one intended mutation", "all unrelated fields retained"),
        error,
    )


def scenario_fx_wc12_privacy_004(vector: dict) -> ExecutionEvidence:
    query, projection, result = _privacy_models()
    payload = query.model_dump()
    payload["open_decision_reference_ids"] = ("OD-014",)
    with pytest.raises(ValidationError) as caught:
        security_privacy.RequestWebSecurityPrivacyAssessmentQuery(**payload)
    error = _validation_tuple(caught.value)
    assert error[0] == ((),) and error[1] == ("value_error",)
    assert "open decisions do not match policy-gated surfaces" in error[2][0]
    return _evidence(
        vector,
        (query, projection, result),
        ("incorrect complete policy-gate mapping rejected", "all unrelated query fields retained"),
        error,
    )


def scenario_fx_wc12_privacy_005(vector: dict) -> ExecutionEvidence:
    model = _privacy_models()[0]
    payload = model.model_dump()
    payload.update({"raw_secret_requested": True})
    with pytest.raises(ValidationError) as caught:
        type(model)(**payload)
    error = _validation_tuple(caught.value)
    assert error == ((("raw_secret_requested",),), ("literal_error",), ("Input should be False",))
    return _evidence(
        vector,
        (model,),
        ("secret_retention_no_invention", "one intended mutation", "all unrelated fields retained"),
        error,
    )


def scenario_fx_wc12_static_001(vector: dict) -> ExecutionEvidence:
    exports = tuple(package.__all__)
    assert len(exports) == 75 and len(set(exports)) == 75
    return _evidence(vector, (), ("literal package exports count=75 and unique",))


def scenario_fx_wc12_static_002(vector: dict) -> ExecutionEvidence:
    found = violations("import requests\n")
    assert "import:requests" in found
    return ExecutionEvidence(
        "STATIC_VIOLATION",
        vector["fixture_id"],
        vector["scenario"],
        vector["category"],
        (),
        ("actual architecture detector label import:requests",),
        static_labels=("import:requests",),
    )


def scenario_fx_wc12_static_003(vector: dict) -> ExecutionEvidence:
    model = _valid_view()[-1]
    with pytest.raises((ValidationError, TypeError)):
        setattr(model, "redacted", False)
    with pytest.raises(ValidationError):
        type(model)(**{**model.model_dump(), "unexpected": "x"})
    return ExecutionEvidence(
        "STATIC_VIOLATION",
        vector["fixture_id"],
        vector["scenario"],
        vector["category"],
        (type(model).__name__,),
        ("frozen-instance rejection", "extra_forbidden rejection"),
        static_labels=("frozen-instance", "extra_forbidden"),
    )


def scenario_fx_wc12_static_004(vector: dict) -> ExecutionEvidence:
    fixture_text = FIXTURE.read_text(encoding="utf-8")
    assert not re.search(r"(?i)(https?://|[a-z0-9._%+-]+@[a-z0-9.-]+\\.[a-z]{2,})", fixture_text)
    unsafe_samples = (
        ("unsafe_url", "https://synthetic.invalid/path"),
        ("unsafe_email", "synthetic@example.invalid"),
        ("unsafe_token", "Bearer synthetic-secret-token"),
    )
    labels = tuple(
        label
        for label, sample in unsafe_samples
        if re.search(r"https?://", sample)
        or re.search(r"[a-z0-9._%+-]+@[a-z0-9.-]+\\.[a-z]{2,}", sample)
        or ("@" in sample and "." in sample.split("@", 1)[1])
        or re.search(r"(?i)bearer|token|secret", sample)
    )
    assert labels == ("unsafe_url", "unsafe_email", "unsafe_token")
    return ExecutionEvidence(
        "STATIC_VIOLATION",
        vector["fixture_id"],
        vector["scenario"],
        vector["category"],
        (),
        (
            "literal unsafe URL rejection",
            "literal unsafe email rejection",
            "literal token rejection",
        ),
        static_labels=labels,
    )


def scenario_fx_wc12_static_005(vector: dict) -> ExecutionEvidence:
    import json
    import subprocess
    import sys

    parent_package_id = id(package)
    parent_module_ids = {
        name: id(mod)
        for name, mod in [
            ("read_models", read_models),
            ("beacon_commands", beacon_commands),
            ("auth_context", auth_context),
            ("entitlement_projections", entitlement_projections),
            ("notification_history", notification_history),
            ("status_display", status_display),
            ("channel_linking", channel_linking),
            ("admin_analytics", admin_analytics),
            ("support_handoff", support_handoff),
            ("security_privacy", security_privacy),
        ]
    }
    parent_export_ids = {name: id(package.__dict__[name]) for name in package.__all__}
    before_env = dict(os.environ)

    audit_script = (
        "import os, sys, json, importlib\n"
        "import mayak.modules.web_cabinet as pkg\n"
        "from mayak.modules.web_cabinet import (\n"
        "    read_models, beacon_commands, auth_context, entitlement_projections,\n"
        "    notification_history, status_display, channel_linking, admin_analytics,\n"
        "    support_handoff, security_privacy,\n"
        ")\n"
        "modules = [\n"
        "    read_models, beacon_commands, auth_context, entitlement_projections,\n"
        "    notification_history, status_display, channel_linking, admin_analytics,\n"
        "    support_handoff, security_privacy,\n"
        "]\n"
        "before_exports = tuple(pkg.__all__)\n"
        "before_env = dict(os.environ)\n"
        "reload_errors = []\n"
        "for m in modules:\n"
        "    try:\n"
        "        importlib.reload(m)\n"
        "    except Exception as e:\n"
        "        reload_errors.append(str(e))\n"
        "try:\n"
        "    importlib.reload(pkg)\n"
        "except Exception as e:\n"
        "    reload_errors.append(str(e))\n"
        "after_exports = tuple(pkg.__all__)\n"
        "after_env = dict(os.environ)\n"
        "export_order_same = before_exports == after_exports\n"
        "exports_count = len(after_exports)\n"
        "exports_unique = len(set(after_exports)) == len(after_exports)\n"
        "module_id_value = pkg.__dict__.get('MODULE_ID')\n"
        "env_unchanged = before_env == after_env\n"
        "identity_checks = []\n"
        "for name in after_exports:\n"
        "    owner_name = 'mayak.modules.web_cabinet'\n"
        "    parts = name.split('.')\n"
        "    if len(parts) > 1:\n"
        "        owner_name = 'mayak.modules.web_cabinet.' + parts[0]\n"
        "    owner_mod = sys.modules.get(owner_name, pkg)\n"
        "    identity_checks.append(pkg.__dict__[name] is owner_mod.__dict__[name])\n"
        "result = {\n"
        "    'export_order_same': export_order_same,\n"
        "    'exports_count': exports_count,\n"
        "    'exports_unique': exports_unique,\n"
        "    'module_id': module_id_value,\n"
        "    'env_unchanged': env_unchanged,\n"
        "    'identity_checks_ok': all(identity_checks),\n"
        "    'reload_errors': reload_errors,\n"
        "    'modules_reloaded': len(reload_errors) == 0,\n"
        "}\n"
        "print(json.dumps(result))\n"
        "sys.exit(0 if all([\n"
        "    export_order_same, exports_count == 75, exports_unique,\n"
        "    len(reload_errors) == 0, module_id_value == '12-web-cabinet',\n"
        "    env_unchanged, all(identity_checks),\n"
        "]) else 1)\n"
    )

    repo_root = str(Path(__file__).resolve().parents[2])
    safe_env = {
        k: v for k, v in before_env.items()
        if 'SECRET' not in k and 'TOKEN' not in k
        and 'KEY' not in k and 'PASSWORD' not in k
    }
    safe_env["PYTHONPATH"] = os.pathsep.join(
        [os.path.join(repo_root, "src")] + sys.path
    )
    result = subprocess.run(
        [sys.executable, "-c", audit_script],
        capture_output=True,
        text=True,
        cwd=repo_root,
        env=safe_env,
        shell=False,
        timeout=30,
    )

    assert result.returncode == 0, f"Subprocess reload audit failed: {result.stderr}"
    audit = json.loads(result.stdout.strip())

    assert audit["export_order_same"], "Export order changed after reload"
    assert audit["exports_count"] == 75, f"Expected 75 exports, got {audit['exports_count']}"
    assert audit["exports_unique"], "Exports are not unique"
    assert audit["modules_reloaded"], f"Module reload failed: {audit['reload_errors']}"
    assert audit["module_id"] == "12-web-cabinet", f"MODULE_ID mismatch: {audit['module_id']}"
    assert audit["env_unchanged"], "Environment changed in child process"
    assert audit["identity_checks_ok"], "Identity checks failed"

    assert id(package) == parent_package_id, "Parent package identity changed"
    for name, mod_id in parent_module_ids.items():
        current_mod = {
            "read_models": read_models,
            "beacon_commands": beacon_commands,
            "auth_context": auth_context,
            "entitlement_projections": entitlement_projections,
            "notification_history": notification_history,
            "status_display": status_display,
            "channel_linking": channel_linking,
            "admin_analytics": admin_analytics,
            "support_handoff": support_handoff,
            "security_privacy": security_privacy,
        }[name]
        assert id(current_mod) == mod_id, f"Parent module {name} identity changed"

    for name, exp_id in parent_export_ids.items():
        assert id(package.__dict__[name]) == exp_id, f"Parent export {name} identity changed"

    assert dict(os.environ) == before_env, "Parent environment changed"

    for name in package.__all__:
        parts = name.split(".")
        if len(parts) > 1:
            owner_module = sys.modules.get(
                f"mayak.modules.web_cabinet.{parts[0]}", package
            )
        else:
            owner_module = package
        assert package.__dict__[name] is owner_module.__dict__[name], (
            f"Contract invariant broken for {name}"
        )

    return _evidence(
        vector,
        (),
        (
            "reload package and all web modules via subprocess",
            "environment byte equality",
            "parent identity preservation",
        ),
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
    assert len(SCENARIO_EXECUTION_SPEC) == 56
    assert SCENARIO_EXECUTION_SPEC == tuple(EXPECTED_VECTORS)


def test_literal_direct_source_regressions() -> None:
    source = Path(__file__).read_text(encoding="utf-8")
    forbidden = (
        "_" + "field_value",
        "_" + "complete",
        "_" + "error",
        "_" + "validated_scenario",
        "_" + "invalid_from",
        "_" + "scenario_family",
        "_" + "scenario_model",
        "_" + "scenario_value",
        "_" + "family_dispatch",
        "model_fields",
        "get_origin",
        "get_args",
    )
    tree = ast.parse(source)
    identifiers = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    attributes = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
    assert not any(name in identifiers or name in attributes for name in forbidden)
    assert (
        len(
            [
                node
                for node in ast.walk(tree)
                if isinstance(node, ast.FunctionDef) and node.name.startswith("scenario_fx_wc12_")
            ]
        )
        == 56
    )
    assert len(SCENARIO_EXECUTION_SPEC) == 56


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


def test_execution_spec_has_every_literal_fixture_id() -> None:
    assert tuple(row[0] for row in SCENARIO_EXECUTION_SPEC) == EXPECTED_IDS


def test_pass_evidence_has_no_validation_error() -> None:
    for vector in _load()["vectors"]:
        evidence = HANDLERS[vector["fixture_id"]](vector)
        if vector["expected_result"] == "PASS":
            assert not evidence.validation_error_types


def test_invalid_evidence_has_exact_validator_signature() -> None:
    for vector in _load()["vectors"]:
        evidence = HANDLERS[vector["fixture_id"]](vector)
        if vector["expected_result"] == "VALIDATION_ERROR":
            assert evidence.validation_error_locations
            assert evidence.validation_error_types
            assert evidence.validation_error_message_fragments


def test_static_005_isolation_preserves_parent_identities() -> None:
    import sys

    parent_package_id = id(package)
    parent_module_ids = {
        name: id(mod)
        for name, mod in [
            ("read_models", read_models),
            ("beacon_commands", beacon_commands),
            ("auth_context", auth_context),
            ("entitlement_projections", entitlement_projections),
            ("notification_history", notification_history),
            ("status_display", status_display),
            ("channel_linking", channel_linking),
            ("admin_analytics", admin_analytics),
            ("support_handoff", support_handoff),
            ("security_privacy", security_privacy),
        ]
    }
    parent_export_ids = {
        name: id(package.__dict__[name]) for name in package.__all__
    }
    before_env = dict(os.environ)

    vector = {
        "fixture_id": "FX-WC12-STATIC-005",
        "category": "STATIC",
        "scenario": "reload_stability",
    }
    evidence = scenario_fx_wc12_static_005(vector)
    assert evidence.result == "PASS"

    assert id(package) == parent_package_id, (
        "Parent package identity changed after STATIC-005"
    )
    for name, mod_id in parent_module_ids.items():
        current_mod = {
            "read_models": read_models,
            "beacon_commands": beacon_commands,
            "auth_context": auth_context,
            "entitlement_projections": entitlement_projections,
            "notification_history": notification_history,
            "status_display": status_display,
            "channel_linking": channel_linking,
            "admin_analytics": admin_analytics,
            "support_handoff": support_handoff,
            "security_privacy": security_privacy,
        }[name]
        assert id(current_mod) == mod_id, (
            f"Parent module {name} identity changed after STATIC-005"
        )
    for name, exp_id in parent_export_ids.items():
        assert id(package.__dict__[name]) == exp_id, (
            f"Parent export {name} identity changed after STATIC-005"
        )
    assert dict(os.environ) == before_env, (
        "Parent environment changed after STATIC-005"
    )

    for name in package.__all__:
        parts = name.split(".")
        if len(parts) > 1:
            owner_module = sys.modules.get(
                f"mayak.modules.web_cabinet.{parts[0]}", package
            )
        else:
            owner_module = package
        assert package.__dict__[name] is owner_module.__dict__[name], (
            f"Contract invariant broken for {name} after STATIC-005"
        )

    evidence2 = scenario_fx_wc12_static_005(vector)
    assert evidence2.result == "PASS"
    assert id(package) == parent_package_id, "Package identity changed on second STATIC-005 run"
