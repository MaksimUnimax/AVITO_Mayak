"""Transport-neutral safe status display projections for Web Cabinet."""

from __future__ import annotations

from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from mayak.contracts import ContractMetadata
from mayak.modules.web_cabinet.read_models import WebReadFreshness, WebViewAudience
from mayak.platform.boundaries import (
    ADMIN_AND_SUPPORT_MODULE_ID,
    BEACON_MANAGEMENT_MODULE_ID,
    ENTITLEMENTS_AND_BILLING_MODULE_ID,
    IDENTITY_AND_ACCESS_MODULE_ID,
    MAX_ADAPTER_MODULE_ID,
    NOTIFICATION_DELIVERY_MODULE_ID,
    SCAN_ORCHESTRATION_AND_LISTING_STATE_MODULE_ID,
    TELEGRAM_ADAPTER_MODULE_ID,
    WEB_CABINET_MODULE_ID,
)


class _WebStatusDisplayContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


_NonEmptyReferenceId = Annotated[str, Field(min_length=1)]


def _validate_references(values: tuple[str, ...], label: str, *, allow_empty: bool = True) -> None:
    if not allow_empty and not values:
        raise ValueError(f"{label} must be non-empty")
    if any(not value.strip() for value in values):
        raise ValueError(f"{label} references must be non-blank")
    if len(values) != len(set(values)):
        raise ValueError(f"duplicate {label} references are not allowed")


class WebStatusSourceFamily(str, Enum):
    SCAN_ORCHESTRATION = "SCAN_ORCHESTRATION"
    NOTIFICATION_DELIVERY = "NOTIFICATION_DELIVERY"
    ENTITLEMENTS = "ENTITLEMENTS"
    CHANNEL_ADAPTER = "CHANNEL_ADAPTER"
    WEB_READ_MODEL = "WEB_READ_MODEL"


class WebStatusEvidenceClass(str, Enum):
    SCAN_NO_NEW_PROVEN = "SCAN_NO_NEW_PROVEN"
    SCAN_EXTERNAL_UNAVAILABLE = "SCAN_EXTERNAL_UNAVAILABLE"
    SCAN_RECOVERY_COMPLETED = "SCAN_RECOVERY_COMPLETED"
    SCAN_LOST_ANCHORS_RECOVERED = "SCAN_LOST_ANCHORS_RECOVERED"
    ENTITLEMENT_ACCESS_RESTRICTED = "ENTITLEMENT_ACCESS_RESTRICTED"
    ENTITLEMENT_FREE_COMPLIANCE_REQUIRED = "ENTITLEMENT_FREE_COMPLIANCE_REQUIRED"
    CHANNEL_NOT_CONNECTED = "CHANNEL_NOT_CONNECTED"
    CHANNEL_NOT_VERIFIED = "CHANNEL_NOT_VERIFIED"
    CHANNEL_DISABLED_BY_USER = "CHANNEL_DISABLED_BY_USER"
    NOTIFICATION_DELIVERY_FAILED = "NOTIFICATION_DELIVERY_FAILED"
    NOTIFICATION_DELIVERY_UNKNOWN = "NOTIFICATION_DELIVERY_UNKNOWN"
    NOTIFICATION_RECONCILIATION_REQUIRED = "NOTIFICATION_RECONCILIATION_REQUIRED"
    WEB_READ_MODEL_STALE = "WEB_READ_MODEL_STALE"
    SAFE_NOT_AUTHORIZED_OR_NOT_FOUND = "SAFE_NOT_AUTHORIZED_OR_NOT_FOUND"
    AMBIGUOUS = "AMBIGUOUS"
    UNSUPPORTED = "UNSUPPORTED"


class WebStatusDisplayFamily(str, Enum):
    NO_NEW_LISTINGS = "NO_NEW_LISTINGS"
    EXTERNAL_UNAVAILABLE_CONTINUING_SCAN = "EXTERNAL_UNAVAILABLE_CONTINUING_SCAN"
    RECOVERY_COMPLETED = "RECOVERY_COMPLETED"
    LOST_ANCHORS_STATE_RESTORED = "LOST_ANCHORS_STATE_RESTORED"
    ACCESS_RESTRICTED = "ACCESS_RESTRICTED"
    FREE_COMPLIANCE_REQUIRED = "FREE_COMPLIANCE_REQUIRED"
    CHANNEL_NOT_CONNECTED = "CHANNEL_NOT_CONNECTED"
    CHANNEL_NOT_VERIFIED = "CHANNEL_NOT_VERIFIED"
    CHANNEL_DISABLED_BY_USER = "CHANNEL_DISABLED_BY_USER"
    NOTIFICATION_NOT_DELIVERED = "NOTIFICATION_NOT_DELIVERED"
    NOTIFICATION_STATUS_UNKNOWN = "NOTIFICATION_STATUS_UNKNOWN"
    RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"
    READ_MODEL_STALE = "READ_MODEL_STALE"
    NOT_AUTHORIZED_OR_NOT_FOUND_SAFE = "NOT_AUTHORIZED_OR_NOT_FOUND_SAFE"
    AMBIGUOUS = "AMBIGUOUS"
    UNSUPPORTED = "UNSUPPORTED"


class WebStatusDisplayResultState(str, Enum):
    AVAILABLE = "AVAILABLE"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND_SAFE = "NOT_FOUND_SAFE"
    STALE = "STALE"
    AMBIGUOUS = "AMBIGUOUS"
    UNSUPPORTED = "UNSUPPORTED"


class RequestWebStatusDisplayQuery(_WebStatusDisplayContract):
    web_status_display_query_id: _NonEmptyReferenceId
    metadata: ContractMetadata
    account_id: _NonEmptyReferenceId
    actor_context_reference_id: _NonEmptyReferenceId
    authorization_decision_reference_id: _NonEmptyReferenceId
    tenant_scope_reference_id: _NonEmptyReferenceId
    requested_audience: WebViewAudience
    beacon_scope_ids: tuple[_NonEmptyReferenceId, ...]
    requested_status_reference_ids: tuple[_NonEmptyReferenceId, ...]
    status_mapping_policy_reference_id: _NonEmptyReferenceId
    freshness_policy_reference_id: _NonEmptyReferenceId
    reason_code: _NonEmptyReferenceId
    verified_actor_required: Literal[True] = True
    account_scope_required: Literal[True] = True
    read_only: Literal[True] = True
    owning_module_status_authority_required: Literal[True] = True
    client_status_authority: Literal[False] = False
    browser_state_authority: Literal[False] = False
    web_business_outcome_evaluator: Literal[False] = False
    direct_foreign_state_write_authority: Literal[False] = False
    delivery_execution_authority: Literal[False] = False
    retry_execution_authority: Literal[False] = False
    reconciliation_execution_authority: Literal[False] = False
    provider_call_authority: Literal[False] = False
    raw_error_requested: Literal[False] = False
    stack_trace_requested: Literal[False] = False
    raw_provider_payload_requested: Literal[False] = False
    actual_message_text_requested: Literal[False] = False
    retention_policy_defined: Literal[False] = False

    @model_validator(mode="after")
    def _validate_query(self) -> "RequestWebStatusDisplayQuery":
        _validate_references(self.beacon_scope_ids, "Beacon scope")
        _validate_references(
            self.requested_status_reference_ids, "requested status", allow_empty=False
        )
        return self


_SOURCE_MODULES = {
    WebStatusSourceFamily.SCAN_ORCHESTRATION: {SCAN_ORCHESTRATION_AND_LISTING_STATE_MODULE_ID},
    WebStatusSourceFamily.NOTIFICATION_DELIVERY: {NOTIFICATION_DELIVERY_MODULE_ID},
    WebStatusSourceFamily.ENTITLEMENTS: {ENTITLEMENTS_AND_BILLING_MODULE_ID},
    WebStatusSourceFamily.CHANNEL_ADAPTER: {TELEGRAM_ADAPTER_MODULE_ID, MAX_ADAPTER_MODULE_ID},
    WebStatusSourceFamily.WEB_READ_MODEL: {
        IDENTITY_AND_ACCESS_MODULE_ID,
        ENTITLEMENTS_AND_BILLING_MODULE_ID,
        BEACON_MANAGEMENT_MODULE_ID,
        SCAN_ORCHESTRATION_AND_LISTING_STATE_MODULE_ID,
        NOTIFICATION_DELIVERY_MODULE_ID,
        TELEGRAM_ADAPTER_MODULE_ID,
        MAX_ADAPTER_MODULE_ID,
        ADMIN_AND_SUPPORT_MODULE_ID,
        WEB_CABINET_MODULE_ID,
    },
}

_EVIDENCE_SOURCES = {
    **{
        item: WebStatusSourceFamily.SCAN_ORCHESTRATION
        for item in (
            WebStatusEvidenceClass.SCAN_NO_NEW_PROVEN,
            WebStatusEvidenceClass.SCAN_EXTERNAL_UNAVAILABLE,
            WebStatusEvidenceClass.SCAN_RECOVERY_COMPLETED,
            WebStatusEvidenceClass.SCAN_LOST_ANCHORS_RECOVERED,
        )
    },
    **{
        item: WebStatusSourceFamily.ENTITLEMENTS
        for item in (
            WebStatusEvidenceClass.ENTITLEMENT_ACCESS_RESTRICTED,
            WebStatusEvidenceClass.ENTITLEMENT_FREE_COMPLIANCE_REQUIRED,
        )
    },
    **{
        item: WebStatusSourceFamily.CHANNEL_ADAPTER
        for item in (
            WebStatusEvidenceClass.CHANNEL_NOT_CONNECTED,
            WebStatusEvidenceClass.CHANNEL_NOT_VERIFIED,
            WebStatusEvidenceClass.CHANNEL_DISABLED_BY_USER,
        )
    },
    **{
        item: WebStatusSourceFamily.NOTIFICATION_DELIVERY
        for item in (
            WebStatusEvidenceClass.NOTIFICATION_DELIVERY_FAILED,
            WebStatusEvidenceClass.NOTIFICATION_DELIVERY_UNKNOWN,
            WebStatusEvidenceClass.NOTIFICATION_RECONCILIATION_REQUIRED,
        )
    },
    WebStatusEvidenceClass.WEB_READ_MODEL_STALE: WebStatusSourceFamily.WEB_READ_MODEL,
    WebStatusEvidenceClass.SAFE_NOT_AUTHORIZED_OR_NOT_FOUND: WebStatusSourceFamily.WEB_READ_MODEL,
}


class WebStatusEvidenceReference(_WebStatusDisplayContract):
    web_status_evidence_reference_id: _NonEmptyReferenceId
    account_id: _NonEmptyReferenceId
    beacon_id: _NonEmptyReferenceId | None = None
    source_family: WebStatusSourceFamily
    source_module_id: _NonEmptyReferenceId
    evidence_class: WebStatusEvidenceClass
    source_status_reference_id: _NonEmptyReferenceId
    source_decision_reference_id: _NonEmptyReferenceId | None = None
    source_outcome_reference_id: _NonEmptyReferenceId | None = None
    source_reason_codes: tuple[_NonEmptyReferenceId, ...]
    freshness: WebReadFreshness
    safe_evidence_reference_ids: tuple[_NonEmptyReferenceId, ...]
    safe_latest_fresh_listing_reference_ids: tuple[_NonEmptyReferenceId, ...]
    no_new_claim_allowed: Literal[True, False]
    state_restored_latest_fresh_only: Literal[True, False]
    continuing_scan_visible: Literal[True, False]
    reconciliation_reference_id: _NonEmptyReferenceId | None = None
    ambiguity_reference_id: _NonEmptyReferenceId | None = None
    safe_reference_only: Literal[True] = True
    source_module_authoritative: Literal[True] = True
    web_status_authority: Literal[False] = False
    web_scan_authority: Literal[False] = False
    web_notification_authority: Literal[False] = False
    web_entitlement_authority: Literal[False] = False
    web_channel_authority: Literal[False] = False
    confirmed_new_claim_allowed: Literal[False] = False
    delivery_success_claim_allowed: Literal[False] = False
    user_receipt_claim_allowed: Literal[False] = False
    provider_call_authority: Literal[False] = False
    mutation_authority: Literal[False] = False
    raw_error_present: Literal[False] = False
    stack_trace_present: Literal[False] = False
    raw_provider_payload_present: Literal[False] = False
    secret_value_present: Literal[False] = False
    personal_contact_data_present: Literal[False] = False
    retention_authority: Literal[False] = False

    @model_validator(mode="after")
    def _validate_evidence(self) -> "WebStatusEvidenceReference":
        _validate_references(self.source_reason_codes, "source reason", allow_empty=False)
        _validate_references(self.safe_evidence_reference_ids, "safe evidence", allow_empty=False)
        _validate_references(self.safe_latest_fresh_listing_reference_ids, "latest-fresh listing")
        expected_source = _EVIDENCE_SOURCES.get(self.evidence_class)
        if expected_source is not None and self.source_family is not expected_source:
            raise ValueError("evidence class is not owned by source family")
        if self.source_module_id not in _SOURCE_MODULES[self.source_family]:
            raise ValueError("source module does not belong to source family")
        if self.evidence_class is WebStatusEvidenceClass.SCAN_NO_NEW_PROVEN:
            if (
                self.freshness is not WebReadFreshness.FRESH
                or not self.source_decision_reference_id
                or not self.source_outcome_reference_id
            ):
                raise ValueError("proven no-new requires fresh decision and outcome evidence")
            if (
                not self.no_new_claim_allowed
                or self.safe_latest_fresh_listing_reference_ids
                or self.state_restored_latest_fresh_only
                or self.continuing_scan_visible
            ):
                raise ValueError("invalid proven no-new boundary")
        elif self.no_new_claim_allowed:
            raise ValueError("only proven comparison may claim no-new")
        if self.evidence_class is WebStatusEvidenceClass.SCAN_EXTERNAL_UNAVAILABLE:
            if (
                self.freshness is not WebReadFreshness.FRESH
                or not self.continuing_scan_visible
                or self.safe_latest_fresh_listing_reference_ids
            ):
                raise ValueError("external-unavailable requires continuing scan")
        elif self.continuing_scan_visible:
            raise ValueError("continuing scan is limited to external-unavailable")
        if self.evidence_class in (
            WebStatusEvidenceClass.SCAN_RECOVERY_COMPLETED,
            WebStatusEvidenceClass.SCAN_LOST_ANCHORS_RECOVERED,
        ) and (not self.source_decision_reference_id or not self.source_outcome_reference_id):
            raise ValueError("recovery requires decision and outcome references")
        if self.evidence_class is WebStatusEvidenceClass.SCAN_LOST_ANCHORS_RECOVERED:
            if (
                self.freshness is not WebReadFreshness.FRESH
                or not 1 <= len(self.safe_latest_fresh_listing_reference_ids) <= 3
                or not self.state_restored_latest_fresh_only
            ):
                raise ValueError("lost anchors requires latest-fresh state restoration")
        elif self.safe_latest_fresh_listing_reference_ids or self.state_restored_latest_fresh_only:
            raise ValueError("latest-fresh references are limited to lost anchors")
        if self.evidence_class is WebStatusEvidenceClass.NOTIFICATION_RECONCILIATION_REQUIRED:
            if not self.reconciliation_reference_id:
                raise ValueError("reconciliation reference is required")
        elif self.reconciliation_reference_id is not None:
            raise ValueError("reconciliation reference is not allowed")
        if self.evidence_class is WebStatusEvidenceClass.WEB_READ_MODEL_STALE:
            if self.freshness is not WebReadFreshness.STALE:
                raise ValueError("stale read model requires stale freshness")
        elif self.freshness is WebReadFreshness.STALE:
            raise ValueError("only stale read model may use stale freshness")
        if self.evidence_class is WebStatusEvidenceClass.AMBIGUOUS:
            if self.freshness is not WebReadFreshness.AMBIGUOUS or not self.ambiguity_reference_id:
                raise ValueError("ambiguity requires ambiguous freshness and reference")
        elif (
            self.freshness is WebReadFreshness.AMBIGUOUS or self.ambiguity_reference_id is not None
        ):
            raise ValueError("ambiguity evidence is limited to ambiguous class")
        if (
            self.evidence_class is not WebStatusEvidenceClass.SCAN_NO_NEW_PROVEN
            and self.evidence_class
            in {
                WebStatusEvidenceClass.SCAN_EXTERNAL_UNAVAILABLE,
                WebStatusEvidenceClass.SCAN_LOST_ANCHORS_RECOVERED,
                WebStatusEvidenceClass.NOTIFICATION_DELIVERY_FAILED,
                WebStatusEvidenceClass.NOTIFICATION_DELIVERY_UNKNOWN,
                WebStatusEvidenceClass.NOTIFICATION_RECONCILIATION_REQUIRED,
                WebStatusEvidenceClass.WEB_READ_MODEL_STALE,
                WebStatusEvidenceClass.AMBIGUOUS,
            }
            and self.no_new_claim_allowed
        ):
            raise ValueError("unsafe evidence cannot claim no-new")
        return self


_DISPLAY_EVIDENCE = {
    WebStatusDisplayFamily.NO_NEW_LISTINGS: WebStatusEvidenceClass.SCAN_NO_NEW_PROVEN,
    WebStatusDisplayFamily.EXTERNAL_UNAVAILABLE_CONTINUING_SCAN: (
        WebStatusEvidenceClass.SCAN_EXTERNAL_UNAVAILABLE
    ),
    WebStatusDisplayFamily.RECOVERY_COMPLETED: WebStatusEvidenceClass.SCAN_RECOVERY_COMPLETED,
    WebStatusDisplayFamily.LOST_ANCHORS_STATE_RESTORED: (
        WebStatusEvidenceClass.SCAN_LOST_ANCHORS_RECOVERED
    ),
    WebStatusDisplayFamily.ACCESS_RESTRICTED: WebStatusEvidenceClass.ENTITLEMENT_ACCESS_RESTRICTED,
    WebStatusDisplayFamily.FREE_COMPLIANCE_REQUIRED: (
        WebStatusEvidenceClass.ENTITLEMENT_FREE_COMPLIANCE_REQUIRED
    ),
    WebStatusDisplayFamily.CHANNEL_NOT_CONNECTED: WebStatusEvidenceClass.CHANNEL_NOT_CONNECTED,
    WebStatusDisplayFamily.CHANNEL_NOT_VERIFIED: WebStatusEvidenceClass.CHANNEL_NOT_VERIFIED,
    WebStatusDisplayFamily.CHANNEL_DISABLED_BY_USER: (
        WebStatusEvidenceClass.CHANNEL_DISABLED_BY_USER
    ),
    WebStatusDisplayFamily.NOTIFICATION_NOT_DELIVERED: (
        WebStatusEvidenceClass.NOTIFICATION_DELIVERY_FAILED
    ),
    WebStatusDisplayFamily.NOTIFICATION_STATUS_UNKNOWN: (
        WebStatusEvidenceClass.NOTIFICATION_DELIVERY_UNKNOWN
    ),
    WebStatusDisplayFamily.RECONCILIATION_REQUIRED: (
        WebStatusEvidenceClass.NOTIFICATION_RECONCILIATION_REQUIRED
    ),
    WebStatusDisplayFamily.READ_MODEL_STALE: WebStatusEvidenceClass.WEB_READ_MODEL_STALE,
    WebStatusDisplayFamily.NOT_AUTHORIZED_OR_NOT_FOUND_SAFE: (
        WebStatusEvidenceClass.SAFE_NOT_AUTHORIZED_OR_NOT_FOUND
    ),
    WebStatusDisplayFamily.AMBIGUOUS: WebStatusEvidenceClass.AMBIGUOUS,
    WebStatusDisplayFamily.UNSUPPORTED: WebStatusEvidenceClass.UNSUPPORTED,
}


class WebStatusDisplayItem(_WebStatusDisplayContract):
    web_status_display_item_id: _NonEmptyReferenceId
    account_id: _NonEmptyReferenceId
    beacon_id: _NonEmptyReferenceId | None = None
    family: WebStatusDisplayFamily
    safe_status_title_reference_id: _NonEmptyReferenceId
    safe_status_message_reference_id: _NonEmptyReferenceId
    safe_action_reference_ids: tuple[_NonEmptyReferenceId, ...]
    source_evidence_reference_ids: tuple[_NonEmptyReferenceId, ...]
    reason_code: _NonEmptyReferenceId
    safe_display_references_only: Literal[True] = True
    redacted: Literal[True] = True
    localization_value_embedded: Literal[False] = False
    raw_error_present: Literal[False] = False
    stack_trace_present: Literal[False] = False
    raw_provider_payload_present: Literal[False] = False
    secret_value_present: Literal[False] = False
    personal_contact_data_present: Literal[False] = False
    business_success_authority: Literal[False] = False
    delivery_success_authority: Literal[False] = False
    provider_call_authority: Literal[False] = False
    mutation_authority: Literal[False] = False

    @model_validator(mode="after")
    def _validate_item(self) -> "WebStatusDisplayItem":
        _validate_references(self.safe_action_reference_ids, "safe action")
        _validate_references(
            self.source_evidence_reference_ids, "source evidence", allow_empty=False
        )
        return self


class WebStatusDisplayResult(_WebStatusDisplayContract):
    web_status_display_result_id: _NonEmptyReferenceId
    metadata: ContractMetadata
    query: RequestWebStatusDisplayQuery
    state: WebStatusDisplayResultState
    freshness: WebReadFreshness
    owning_module_id: _NonEmptyReferenceId
    status_mapping_policy_reference_id: _NonEmptyReferenceId
    source_evidence: tuple[WebStatusEvidenceReference, ...]
    display_items: tuple[WebStatusDisplayItem, ...]
    external_unavailable_visible: bool
    recovery_visible: bool
    lost_anchors_state_restored_visible: bool
    access_or_channel_problem_visible: bool
    delivery_problem_visible: bool
    reconciliation_visible: bool
    stale_warning_visible: bool
    source_reference_ids: tuple[_NonEmptyReferenceId, ...]
    evidence_reference_ids: tuple[_NonEmptyReferenceId, ...]
    ambiguity_reference_id: _NonEmptyReferenceId | None = None
    reason_code: _NonEmptyReferenceId
    safe_projection_only: Literal[True] = True
    web_presentation_authority_only: Literal[True] = True
    source_modules_authoritative: Literal[True] = True
    web_business_outcome_authority: Literal[False] = False
    false_no_new_prevented: Literal[True] = True
    false_confirmed_new_prevented: Literal[True] = True
    notification_failure_does_not_rollback_scan: Literal[True] = True
    unknown_delivery_is_reconciliation_first: Literal[True] = True
    safe_display_references_only: Literal[True] = True
    actual_ui_copy_embedded: Literal[False] = False
    direct_foreign_state_write_authority: Literal[False] = False
    delivery_execution_authority: Literal[False] = False
    retry_execution_authority: Literal[False] = False
    reconciliation_execution_authority: Literal[False] = False
    provider_call_authority: Literal[False] = False
    raw_error_present: Literal[False] = False
    stack_trace_present: Literal[False] = False
    raw_provider_payload_present: Literal[False] = False
    secret_value_present: Literal[False] = False
    personal_contact_data_present: Literal[False] = False
    retention_policy_defined: Literal[False] = False
    minimal_personal_data: Literal[True] = True
    redacted: Literal[True] = True
    business_success_authority: Literal[False] = False

    @model_validator(mode="after")
    def _validate_result(self) -> "WebStatusDisplayResult":
        if self.owning_module_id != WEB_CABINET_MODULE_ID:
            raise ValueError("result must be owned by Web Cabinet")
        if self.status_mapping_policy_reference_id != self.query.status_mapping_policy_reference_id:
            raise ValueError("mapping policy must match query")
        _validate_references(
            self.source_reference_ids,
            "source",
            allow_empty=False if self.state is WebStatusDisplayResultState.AVAILABLE else True,
        )
        _validate_references(self.evidence_reference_ids, "evidence")
        evidence_ids = tuple(item.web_status_evidence_reference_id for item in self.source_evidence)
        _validate_references(evidence_ids, "evidence projection")
        if tuple(self.evidence_reference_ids) != evidence_ids:
            raise ValueError("evidence references must match evidence projections")
        item_ids = tuple(item.web_status_display_item_id for item in self.display_items)
        _validate_references(item_ids, "display item")
        status_refs = tuple(item.source_status_reference_id for item in self.source_evidence)
        _validate_references(status_refs, "source status")
        by_id = {item.web_status_evidence_reference_id: item for item in self.source_evidence}
        referenced: set[str] = set()
        for evidence in self.source_evidence:
            if evidence.account_id != self.query.account_id:
                raise ValueError("evidence account mismatch")
            if (
                self.query.beacon_scope_ids
                and evidence.beacon_id is not None
                and evidence.beacon_id not in self.query.beacon_scope_ids
            ):
                raise ValueError("evidence Beacon is outside query scope")
        for display in self.display_items:
            if display.account_id != self.query.account_id:
                raise ValueError("display account mismatch")
            if (
                self.query.beacon_scope_ids
                and display.beacon_id is not None
                and display.beacon_id not in self.query.beacon_scope_ids
            ):
                raise ValueError("display Beacon is outside query scope")
            refs = [by_id.get(ref) for ref in display.source_evidence_reference_ids]
            if any(ref is None for ref in refs):
                raise ValueError("display references unknown evidence")
            resolved_refs = tuple(ref for ref in refs if ref is not None)
            referenced.update(display.source_evidence_reference_ids)
            if any(
                ref.account_id != display.account_id or ref.beacon_id != display.beacon_id
                for ref in resolved_refs
            ):
                raise ValueError("display and evidence scope mismatch")
            expected = _DISPLAY_EVIDENCE[display.family]
            if any(ref.evidence_class is not expected for ref in resolved_refs):
                raise ValueError("display family does not match evidence class")
            if display.family is WebStatusDisplayFamily.NO_NEW_LISTINGS and any(
                not ref.no_new_claim_allowed for ref in resolved_refs
            ):
                raise ValueError("no-new display requires proven evidence")
            if display.family is WebStatusDisplayFamily.LOST_ANCHORS_STATE_RESTORED and any(
                not ref.state_restored_latest_fresh_only
                or ref.confirmed_new_claim_allowed
                or not ref.safe_latest_fresh_listing_reference_ids
                for ref in resolved_refs
            ):
                raise ValueError("lost anchors display must be state-restored/latest-fresh only")
        if referenced != set(evidence_ids):
            raise ValueError("every evidence projection must be displayed")
        families = {item.family for item in self.display_items}
        if self.external_unavailable_visible != (
            WebStatusDisplayFamily.EXTERNAL_UNAVAILABLE_CONTINUING_SCAN in families
        ):
            raise ValueError("external visibility mismatch")
        if self.recovery_visible != (WebStatusDisplayFamily.RECOVERY_COMPLETED in families):
            raise ValueError("recovery visibility mismatch")
        if self.lost_anchors_state_restored_visible != (
            WebStatusDisplayFamily.LOST_ANCHORS_STATE_RESTORED in families
        ):
            raise ValueError("lost anchors visibility mismatch")
        if self.access_or_channel_problem_visible != bool(
            families
            & {
                WebStatusDisplayFamily.ACCESS_RESTRICTED,
                WebStatusDisplayFamily.FREE_COMPLIANCE_REQUIRED,
                WebStatusDisplayFamily.CHANNEL_NOT_CONNECTED,
                WebStatusDisplayFamily.CHANNEL_NOT_VERIFIED,
                WebStatusDisplayFamily.CHANNEL_DISABLED_BY_USER,
            }
        ):
            raise ValueError("access/channel visibility mismatch")
        if self.delivery_problem_visible != bool(
            families
            & {
                WebStatusDisplayFamily.NOTIFICATION_NOT_DELIVERED,
                WebStatusDisplayFamily.NOTIFICATION_STATUS_UNKNOWN,
            }
        ):
            raise ValueError("delivery visibility mismatch")
        if self.reconciliation_visible != (
            WebStatusDisplayFamily.RECONCILIATION_REQUIRED in families
        ):
            raise ValueError("reconciliation visibility mismatch")
        if self.stale_warning_visible != (WebStatusDisplayFamily.READ_MODEL_STALE in families):
            raise ValueError("stale visibility mismatch")
        if self.state is WebStatusDisplayResultState.AVAILABLE:
            if (
                self.freshness is not WebReadFreshness.FRESH
                or not self.source_evidence
                or not self.display_items
                or families & {WebStatusDisplayFamily.AMBIGUOUS, WebStatusDisplayFamily.UNSUPPORTED}
            ):
                raise ValueError("invalid available result")
        elif self.state in (
            WebStatusDisplayResultState.FORBIDDEN,
            WebStatusDisplayResultState.NOT_FOUND_SAFE,
        ):
            if (
                self.source_evidence
                or self.display_items
                or any(
                    (
                        self.external_unavailable_visible,
                        self.recovery_visible,
                        self.lost_anchors_state_restored_visible,
                        self.access_or_channel_problem_visible,
                        self.delivery_problem_visible,
                        self.reconciliation_visible,
                        self.stale_warning_visible,
                    )
                )
            ):
                raise ValueError("empty safe result required")
            if (
                self.state is WebStatusDisplayResultState.NOT_FOUND_SAFE
                and self.freshness is not WebReadFreshness.FRESH
            ):
                raise ValueError("safe not-found requires fresh result")
        elif self.state is WebStatusDisplayResultState.STALE:
            if (
                self.freshness is not WebReadFreshness.STALE
                or WebStatusDisplayFamily.READ_MODEL_STALE not in families
                or not self.stale_warning_visible
            ):
                raise ValueError("stale result requires stale item")
        elif self.state is WebStatusDisplayResultState.AMBIGUOUS:
            if (
                self.freshness is not WebReadFreshness.AMBIGUOUS
                or not self.ambiguity_reference_id
                or WebStatusDisplayFamily.AMBIGUOUS not in families
            ):
                raise ValueError("ambiguous result requires ambiguity item")
        elif (
            self.state is WebStatusDisplayResultState.UNSUPPORTED
            and WebStatusDisplayFamily.UNSUPPORTED not in families
        ):
            raise ValueError("unsupported result requires unsupported item")
        if (
            self.state is not WebStatusDisplayResultState.STALE
            and self.freshness is WebReadFreshness.STALE
        ):
            raise ValueError("only stale result may use stale freshness")
        if (
            self.state is not WebStatusDisplayResultState.AMBIGUOUS
            and self.freshness is WebReadFreshness.AMBIGUOUS
        ):
            raise ValueError("only ambiguous result may use ambiguous freshness")
        if (
            self.state is not WebStatusDisplayResultState.AMBIGUOUS
            and self.ambiguity_reference_id is not None
        ):
            raise ValueError("non-ambiguous result cannot carry ambiguity reference")
        return self


__all__ = [
    "RequestWebStatusDisplayQuery",
    "WebStatusDisplayFamily",
    "WebStatusDisplayItem",
    "WebStatusDisplayResult",
    "WebStatusDisplayResultState",
    "WebStatusEvidenceClass",
    "WebStatusEvidenceReference",
    "WebStatusSourceFamily",
]
