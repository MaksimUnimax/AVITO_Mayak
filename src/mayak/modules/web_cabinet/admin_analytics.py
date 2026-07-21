"""Transport-neutral, aggregate-only Web Cabinet admin analytics projections."""

from __future__ import annotations

from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from mayak.contracts import ContractMetadata
from mayak.modules.web_cabinet.read_models import WebReadFreshness, WebViewAudience
from mayak.platform.boundaries import (
    ADMIN_AND_SUPPORT_MODULE_ID,
    ENTITLEMENTS_AND_BILLING_MODULE_ID,
    IDENTITY_AND_ACCESS_MODULE_ID,
    WEB_CABINET_MODULE_ID,
)


class _WebAdminAnalyticsContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


_NonEmptyReferenceId = Annotated[str, Field(min_length=1)]


class WebAdminAnalyticsMetricKind(str, Enum):
    VISITOR_COUNT = "VISITOR_COUNT"
    REGISTERED_LINKED_USER_COUNT = "REGISTERED_LINKED_USER_COUNT"
    ACTIVE_USING_USER_COUNT = "ACTIVE_USING_USER_COUNT"
    FREE_TARIFF_ACCOUNT_COUNT = "FREE_TARIFF_ACCOUNT_COUNT"
    PAID_TARIFF_ACCOUNT_COUNT = "PAID_TARIFF_ACCOUNT_COUNT"


class WebAdminAnalyticsMetricState(str, Enum):
    AVAILABLE = "AVAILABLE"
    PRIVACY_SUPPRESSED = "PRIVACY_SUPPRESSED"
    STALE = "STALE"
    AMBIGUOUS = "AMBIGUOUS"


class WebAdminAnalyticsResultState(str, Enum):
    AVAILABLE = "AVAILABLE"
    REDACTED = "REDACTED"
    FORBIDDEN = "FORBIDDEN"
    POLICY_BLOCKED = "POLICY_BLOCKED"
    STALE = "STALE"
    AMBIGUOUS = "AMBIGUOUS"
    UNSUPPORTED = "UNSUPPORTED"


class WebAdminAnalyticsSortField(str, Enum):
    METRIC_KIND = "METRIC_KIND"
    TARIFF = "TARIFF"
    COUNT = "COUNT"


class WebAdminAnalyticsSortDirection(str, Enum):
    ASCENDING = "ASCENDING"
    DESCENDING = "DESCENDING"


class WebAdminAnalyticsFilterKind(str, Enum):
    PERIOD = "PERIOD"
    TARIFF = "TARIFF"
    ACCOUNT_USE_STATUS = "ACCOUNT_USE_STATUS"


_METRIC_OWNERS = {
    WebAdminAnalyticsMetricKind.VISITOR_COUNT: WEB_CABINET_MODULE_ID,
    WebAdminAnalyticsMetricKind.REGISTERED_LINKED_USER_COUNT: IDENTITY_AND_ACCESS_MODULE_ID,
    WebAdminAnalyticsMetricKind.ACTIVE_USING_USER_COUNT: WEB_CABINET_MODULE_ID,
    WebAdminAnalyticsMetricKind.FREE_TARIFF_ACCOUNT_COUNT: ENTITLEMENTS_AND_BILLING_MODULE_ID,
    WebAdminAnalyticsMetricKind.PAID_TARIFF_ACCOUNT_COUNT: ENTITLEMENTS_AND_BILLING_MODULE_ID,
}
_FILTER_OWNERS = {
    WebAdminAnalyticsFilterKind.PERIOD: WEB_CABINET_MODULE_ID,
    WebAdminAnalyticsFilterKind.TARIFF: ENTITLEMENTS_AND_BILLING_MODULE_ID,
    WebAdminAnalyticsFilterKind.ACCOUNT_USE_STATUS: WEB_CABINET_MODULE_ID,
}
_TARIFF_METRICS = {
    WebAdminAnalyticsMetricKind.FREE_TARIFF_ACCOUNT_COUNT,
    WebAdminAnalyticsMetricKind.PAID_TARIFF_ACCOUNT_COUNT,
}


def _unique(values: tuple[str, ...], label: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{label} must be unique")


class WebAdminAnalyticsMetricRequest(_WebAdminAnalyticsContract):
    metric_kind: WebAdminAnalyticsMetricKind
    source_authority_module_id: _NonEmptyReferenceId
    metric_definition_reference_id: _NonEmptyReferenceId
    aggregation_policy_reference_id: _NonEmptyReferenceId
    approved_tariff_catalog_reference_id: _NonEmptyReferenceId | None = None
    exact_definition_reference_only: Literal[True] = True
    web_metric_definition_authority: Literal[False] = False
    raw_event_definition_present: Literal[False] = False
    tracking_runtime_authority: Literal[False] = False
    retention_policy_defined: Literal[False] = False

    @model_validator(mode="after")
    def validate_authority(self) -> "WebAdminAnalyticsMetricRequest":
        if self.source_authority_module_id != _METRIC_OWNERS[self.metric_kind]:
            raise ValueError("metric source authority does not match metric owner")
        if (
            self.metric_kind in _TARIFF_METRICS
            and self.approved_tariff_catalog_reference_id is None
        ):
            raise ValueError("tariff metrics require an approved tariff catalog reference")
        if (
            self.metric_kind not in _TARIFF_METRICS
            and self.approved_tariff_catalog_reference_id is not None
        ):
            raise ValueError("non-tariff metrics forbid a tariff catalog reference")
        return self


class WebAdminAnalyticsFilterReference(_WebAdminAnalyticsContract):
    web_admin_analytics_filter_reference_id: _NonEmptyReferenceId
    filter_kind: WebAdminAnalyticsFilterKind
    filter_authority_module_id: _NonEmptyReferenceId
    filter_definition_reference_id: _NonEmptyReferenceId
    selected_value_reference_ids: tuple[_NonEmptyReferenceId, ...]
    policy_approval_reference_id: _NonEmptyReferenceId
    safe_filter_display_reference_id: _NonEmptyReferenceId
    exact_filter_definition_reference_only: Literal[True] = True
    web_selected_value_authority: Literal[False] = False
    raw_filter_value_present: Literal[False] = False
    tracking_runtime_authority: Literal[False] = False

    @model_validator(mode="after")
    def validate_filter(self) -> "WebAdminAnalyticsFilterReference":
        if self.filter_authority_module_id != _FILTER_OWNERS[self.filter_kind]:
            raise ValueError("filter authority does not match filter owner")
        if not self.selected_value_reference_ids:
            raise ValueError("selected filter values must be non-empty")
        _unique(self.selected_value_reference_ids, "selected filter values")
        return self


class RequestWebAdminAnalyticsQuery(_WebAdminAnalyticsContract):
    web_admin_analytics_query_id: _NonEmptyReferenceId
    metadata: ContractMetadata
    actor_context_reference_id: _NonEmptyReferenceId
    identity_authorization_decision_reference_id: _NonEmptyReferenceId
    identity_role_scope_reference_id: _NonEmptyReferenceId
    admin_analytics_capability_reference_id: _NonEmptyReferenceId
    tenant_scope_reference_id: _NonEmptyReferenceId
    requested_audience: Literal[WebViewAudience.ADMIN_AUTHORIZED] = WebViewAudience.ADMIN_AUTHORIZED
    metric_requests: tuple[WebAdminAnalyticsMetricRequest, ...]
    filters: tuple[WebAdminAnalyticsFilterReference, ...] = ()
    sort_field: WebAdminAnalyticsSortField
    sort_direction: WebAdminAnalyticsSortDirection
    sort_policy_reference_id: _NonEmptyReferenceId
    admin_support_read_policy_reference_id: _NonEmptyReferenceId
    analytics_aggregation_policy_reference_id: _NonEmptyReferenceId
    privacy_aggregation_policy_reference_id: _NonEmptyReferenceId
    privacy_suppression_policy_reference_id: _NonEmptyReferenceId
    freshness_policy_reference_id: _NonEmptyReferenceId
    reason_code: _NonEmptyReferenceId
    verified_admin_required: Literal[True] = True
    server_assigned_role_required: Literal[True] = True
    admin_support_policy_required: Literal[True] = True
    read_only: Literal[True] = True
    aggregate_only: Literal[True] = True
    user_level_rows_requested: Literal[False] = False
    user_level_export_requested: Literal[False] = False
    tracker_runtime_requested: Literal[False] = False
    event_collection_runtime_requested: Literal[False] = False
    marketing_pixel_requested: Literal[False] = False
    external_analytics_provider_requested: Literal[False] = False
    consent_implementation_requested: Literal[False] = False
    retention_policy_defined: Literal[False] = False
    browser_admin_flag_authority: Literal[False] = False
    provider_identity_admin_authority: Literal[False] = False
    impersonation_requested: Literal[False] = False
    direct_foreign_state_write_authority: Literal[False] = False
    exact_period_definition_invented: Literal[False] = False
    exact_active_user_definition_invented: Literal[False] = False

    @model_validator(mode="after")
    def validate_query(self) -> "RequestWebAdminAnalyticsQuery":
        if not self.metric_requests:
            raise ValueError("metric requests must be non-empty")
        kinds = tuple(request.metric_kind for request in self.metric_requests)
        if len(kinds) != len(set(kinds)):
            raise ValueError("metric kinds must be unique")
        if any(
            request.aggregation_policy_reference_id
            != self.analytics_aggregation_policy_reference_id
            for request in self.metric_requests
        ):
            raise ValueError("metric aggregation policy must match query policy")
        filter_ids = tuple(item.web_admin_analytics_filter_reference_id for item in self.filters)
        filter_kinds = tuple(item.filter_kind for item in self.filters)
        _unique(filter_ids, "filter IDs")
        if len(filter_kinds) != len(set(filter_kinds)):
            raise ValueError("filter kinds must be unique")
        return self


class WebAdminAnalyticsMetricProjection(_WebAdminAnalyticsContract):
    web_admin_analytics_metric_projection_id: _NonEmptyReferenceId
    metric_kind: WebAdminAnalyticsMetricKind
    state: WebAdminAnalyticsMetricState
    freshness: WebReadFreshness
    source_authority_module_id: _NonEmptyReferenceId
    metric_definition_reference_id: _NonEmptyReferenceId
    aggregation_policy_reference_id: _NonEmptyReferenceId
    count_value: int | None = Field(default=None, ge=0)
    tariff_definition_reference_id: _NonEmptyReferenceId | None = None
    safe_tariff_display_reference_id: _NonEmptyReferenceId | None = None
    source_aggregate_reference_id: _NonEmptyReferenceId | None = None
    source_reference_ids: tuple[_NonEmptyReferenceId, ...]
    provenance_reference_ids: tuple[_NonEmptyReferenceId, ...]
    evidence_reference_ids: tuple[_NonEmptyReferenceId, ...]
    privacy_suppression_decision_reference_id: _NonEmptyReferenceId | None = None
    ambiguity_reference_id: _NonEmptyReferenceId | None = None
    reason_code: _NonEmptyReferenceId
    aggregate_only: Literal[True] = True
    safe_reference_only: Literal[True] = True
    source_authoritative: Literal[True] = True
    web_count_authority: Literal[False] = False
    web_recomputed_from_user_rows: Literal[False] = False
    user_level_row_present: Literal[False] = False
    account_identifier_present: Literal[False] = False
    session_identifier_present: Literal[False] = False
    ip_address_present: Literal[False] = False
    cookie_present: Literal[False] = False
    device_fingerprint_present: Literal[False] = False
    raw_event_payload_present: Literal[False] = False
    marketing_identifier_present: Literal[False] = False
    external_analytics_payload_present: Literal[False] = False
    minimal_personal_data: Literal[True] = True
    redacted: Literal[True] = True
    tracker_runtime_authority: Literal[False] = False
    retention_policy_defined: Literal[False] = False

    @model_validator(mode="after")
    def validate_projection(self) -> "WebAdminAnalyticsMetricProjection":
        if self.source_authority_module_id != _METRIC_OWNERS[self.metric_kind]:
            raise ValueError("metric source authority does not match metric owner")
        _unique(self.source_reference_ids, "source references")
        _unique(self.provenance_reference_ids, "provenance references")
        _unique(self.evidence_reference_ids, "evidence references")
        tariff = self.metric_kind in _TARIFF_METRICS
        if tariff != (
            self.tariff_definition_reference_id is not None
            and self.safe_tariff_display_reference_id is not None
        ):
            raise ValueError(
                "tariff projections require tariff definition and safe display references"
            )
        if not tariff and (
            self.tariff_definition_reference_id is not None
            or self.safe_tariff_display_reference_id is not None
        ):
            raise ValueError("non-tariff projections forbid tariff references")
        if self.state is WebAdminAnalyticsMetricState.AVAILABLE:
            if (
                self.freshness is not WebReadFreshness.FRESH
                or self.count_value is None
                or self.source_aggregate_reference_id is None
                or not self.source_reference_ids
                or not self.provenance_reference_ids
                or not self.evidence_reference_ids
                or self.privacy_suppression_decision_reference_id is not None
                or self.ambiguity_reference_id is not None
            ):
                raise ValueError("invalid available metric projection")
        elif self.state is WebAdminAnalyticsMetricState.PRIVACY_SUPPRESSED:
            if (
                self.freshness is not WebReadFreshness.FRESH
                or self.count_value is not None
                or self.source_aggregate_reference_id is None
                or not self.source_reference_ids
                or not self.provenance_reference_ids
                or not self.evidence_reference_ids
                or self.privacy_suppression_decision_reference_id is None
                or self.ambiguity_reference_id is not None
            ):
                raise ValueError("invalid privacy-suppressed metric projection")
        elif self.state is WebAdminAnalyticsMetricState.STALE:
            if (
                self.freshness is not WebReadFreshness.STALE
                or self.count_value is None
                or self.source_aggregate_reference_id is None
                or not self.source_reference_ids
                or not self.provenance_reference_ids
                or not self.evidence_reference_ids
                or self.privacy_suppression_decision_reference_id is not None
                or self.ambiguity_reference_id is not None
            ):
                raise ValueError("invalid stale metric projection")
        else:
            if (
                self.freshness is not WebReadFreshness.AMBIGUOUS
                or self.count_value is not None
                or self.source_aggregate_reference_id is not None
                or not self.source_reference_ids
                or not self.evidence_reference_ids
                or self.ambiguity_reference_id is None
                or self.privacy_suppression_decision_reference_id is not None
            ):
                raise ValueError("invalid ambiguous metric projection")
        return self


class WebAdminAnalyticsResult(_WebAdminAnalyticsContract):
    web_admin_analytics_result_id: _NonEmptyReferenceId
    metadata: ContractMetadata
    query: RequestWebAdminAnalyticsQuery
    state: WebAdminAnalyticsResultState
    freshness: WebReadFreshness
    owning_module_id: _NonEmptyReferenceId
    admin_policy_owner_module_id: _NonEmptyReferenceId
    safe_table_projection_reference_id: _NonEmptyReferenceId | None = None
    safe_sort_application_reference_id: _NonEmptyReferenceId | None = None
    sort_field: WebAdminAnalyticsSortField
    sort_direction: WebAdminAnalyticsSortDirection
    sort_policy_reference_id: _NonEmptyReferenceId
    applied_filter_reference_ids: tuple[_NonEmptyReferenceId, ...]
    metric_projections: tuple[WebAdminAnalyticsMetricProjection, ...]
    projection_count: int = Field(ge=0)
    source_reference_ids: tuple[_NonEmptyReferenceId, ...]
    evidence_reference_ids: tuple[_NonEmptyReferenceId, ...]
    ambiguity_reference_id: _NonEmptyReferenceId | None = None
    reason_code: _NonEmptyReferenceId
    admin_only: Literal[True] = True
    identity_authorization_authoritative: Literal[True] = True
    admin_support_policy_authoritative: Literal[True] = True
    web_presentation_boundary: Literal[True] = True
    aggregate_only: Literal[True] = True
    privacy_suppression_policy_required: Literal[True] = True
    user_level_rows_present: Literal[False] = False
    user_level_export_present: Literal[False] = False
    tracker_implementation_present: Literal[False] = False
    event_collection_runtime_present: Literal[False] = False
    external_analytics_provider_present: Literal[False] = False
    marketing_pixel_present: Literal[False] = False
    consent_implementation_present: Literal[False] = False
    retention_policy_defined: Literal[False] = False
    direct_foreign_state_write_authority: Literal[False] = False
    cross_metric_sum_authority: Literal[False] = False
    screen_or_route_authority: Literal[False] = False
    business_success_authority: Literal[False] = False
    minimal_personal_data: Literal[True] = True
    redacted: Literal[True] = True

    @model_validator(mode="after")
    def validate_result(self) -> "WebAdminAnalyticsResult":
        if (
            self.owning_module_id != WEB_CABINET_MODULE_ID
            or self.admin_policy_owner_module_id != ADMIN_AND_SUPPORT_MODULE_ID
        ):
            raise ValueError("result ownership boundary is invalid")
        if (
            self.sort_field is not self.query.sort_field
            or self.sort_direction is not self.query.sort_direction
            or self.sort_policy_reference_id != self.query.sort_policy_reference_id
        ):
            raise ValueError("result sort does not match query")
        _unique(self.source_reference_ids, "result source references")
        _unique(self.evidence_reference_ids, "result evidence references")
        if not self.source_reference_ids:
            raise ValueError("result source references must be non-empty")
        if not self.evidence_reference_ids:
            raise ValueError("result evidence references must be non-empty")
        projection_ids = tuple(
            item.web_admin_analytics_metric_projection_id for item in self.metric_projections
        )
        _unique(projection_ids, "projection IDs")
        if self.projection_count != len(self.metric_projections):
            raise ValueError("projection count does not match projections")
        query_filter_ids = tuple(
            item.web_admin_analytics_filter_reference_id for item in self.query.filters
        )
        if self.state in {
            WebAdminAnalyticsResultState.FORBIDDEN,
            WebAdminAnalyticsResultState.POLICY_BLOCKED,
            WebAdminAnalyticsResultState.UNSUPPORTED,
        }:
            if (
                self.metric_projections
                or self.projection_count
                or self.safe_table_projection_reference_id is not None
                or self.safe_sort_application_reference_id is not None
                or self.applied_filter_reference_ids
                or self.ambiguity_reference_id is not None
            ):
                raise ValueError("terminal result must not expose projections or filters")
            expected = (
                WebReadFreshness.FRESH
                if self.state is WebAdminAnalyticsResultState.FORBIDDEN
                else WebReadFreshness.UNKNOWN
            )
            if self.freshness is not expected:
                raise ValueError("invalid terminal freshness")
            return self
        if self.applied_filter_reference_ids != query_filter_ids:
            raise ValueError("applied filters do not match query")
        if len(self.applied_filter_reference_ids) != len(set(self.applied_filter_reference_ids)):
            raise ValueError("applied filters must be unique")
        if (
            self.safe_table_projection_reference_id is None
            or self.safe_sort_application_reference_id is None
        ):
            raise ValueError("non-terminal result requires table and sort references")
        requests = {item.metric_kind: item for item in self.query.metric_requests}
        grouped = {
            kind: tuple(item for item in self.metric_projections if item.metric_kind is kind)
            for kind in requests
        }
        if any(item.metric_kind not in requests for item in self.metric_projections):
            raise ValueError("unrequested metric projection")
        for kind, request in requests.items():
            items = grouped[kind]
            required = 1 if kind is not WebAdminAnalyticsMetricKind.PAID_TARIFF_ACCOUNT_COUNT else 1
            if (
                kind is WebAdminAnalyticsMetricKind.PAID_TARIFF_ACCOUNT_COUNT
                and len(items) < required
            ) or (
                kind is not WebAdminAnalyticsMetricKind.PAID_TARIFF_ACCOUNT_COUNT
                and len(items) != required
            ):
                raise ValueError("metric coverage is incomplete")
            if any(
                item.source_authority_module_id != request.source_authority_module_id
                or item.metric_definition_reference_id != request.metric_definition_reference_id
                or item.aggregation_policy_reference_id != request.aggregation_policy_reference_id
                for item in items
            ):
                raise ValueError("projection provenance does not match request")
            if kind is WebAdminAnalyticsMetricKind.PAID_TARIFF_ACCOUNT_COUNT:
                tariff_ids = tuple(item.tariff_definition_reference_id for item in items)
                if len(tariff_ids) != len(set(tariff_ids)):
                    raise ValueError("paid tariff definitions must be unique")
        states = tuple(item.state for item in self.metric_projections)
        if self.state is WebAdminAnalyticsResultState.AVAILABLE:
            if (
                self.freshness is not WebReadFreshness.FRESH
                or any(state is not WebAdminAnalyticsMetricState.AVAILABLE for state in states)
                or self.ambiguity_reference_id is not None
            ):
                raise ValueError("invalid available result")
        elif self.state is WebAdminAnalyticsResultState.REDACTED:
            if (
                self.freshness is not WebReadFreshness.FRESH
                or not any(
                    state is WebAdminAnalyticsMetricState.PRIVACY_SUPPRESSED for state in states
                )
                or any(
                    state
                    not in {
                        WebAdminAnalyticsMetricState.AVAILABLE,
                        WebAdminAnalyticsMetricState.PRIVACY_SUPPRESSED,
                    }
                    for state in states
                )
                or self.ambiguity_reference_id is not None
            ):
                raise ValueError("invalid redacted result")
        elif self.state is WebAdminAnalyticsResultState.STALE:
            if (
                self.freshness is not WebReadFreshness.STALE
                or not any(state is WebAdminAnalyticsMetricState.STALE for state in states)
                or any(state is WebAdminAnalyticsMetricState.AMBIGUOUS for state in states)
                or self.ambiguity_reference_id is not None
            ):
                raise ValueError("invalid stale result")
        elif self.state is WebAdminAnalyticsResultState.AMBIGUOUS:
            if (
                self.freshness is not WebReadFreshness.AMBIGUOUS
                or not any(state is WebAdminAnalyticsMetricState.AMBIGUOUS for state in states)
                or self.ambiguity_reference_id is None
            ):
                raise ValueError("invalid ambiguous result")
        else:
            raise ValueError("unsupported result state")
        return self


__all__ = [
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
]
