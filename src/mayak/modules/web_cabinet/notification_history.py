"""Transport-neutral Web Cabinet notification history projections."""

from __future__ import annotations

from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from mayak.contracts import ContractMetadata
from mayak.modules.web_cabinet.read_models import WebReadFreshness, WebViewAudience
from mayak.platform.boundaries import NOTIFICATION_DELIVERY_MODULE_ID


class _WebNotificationHistoryContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


_NonEmptyReferenceId = Annotated[str, Field(min_length=1)]


def _validate_reference_tuple(
    values: tuple[str, ...], label: str, *, allow_empty: bool = True
) -> None:
    if not allow_empty and not values:
        raise ValueError(f"{label} must be non-empty")
    if any(not value.strip() for value in values):
        raise ValueError(f"{label} references must be non-blank")
    if len(values) != len(set(values)):
        raise ValueError(f"duplicate {label} references are not allowed")


def _first_occurrence_union(*tuples: tuple[str, ...]) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []
    for values in tuples:
        for value in values:
            if value not in seen:
                seen.add(value)
                ordered.append(value)
    return tuple(ordered)


class WebNotificationDeliveryState(str, Enum):
    PLANNED = "PLANNED"
    REPLAYED = "REPLAYED"
    SUPPRESSED = "SUPPRESSED"
    BLOCKED = "BLOCKED"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"
    RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"


class WebNotificationHistoryResultState(str, Enum):
    AVAILABLE = "AVAILABLE"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND_SAFE = "NOT_FOUND_SAFE"
    STALE = "STALE"
    AMBIGUOUS = "AMBIGUOUS"
    RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"


class RequestWebNotificationHistoryQuery(_WebNotificationHistoryContract):
    web_notification_history_query_id: _NonEmptyReferenceId
    metadata: ContractMetadata
    account_id: _NonEmptyReferenceId
    actor_context_reference_id: _NonEmptyReferenceId
    authorization_decision_reference_id: _NonEmptyReferenceId
    tenant_scope_reference_id: _NonEmptyReferenceId
    requested_audience: WebViewAudience
    beacon_scope_ids: tuple[_NonEmptyReferenceId, ...]
    notification_read_policy_reference_id: _NonEmptyReferenceId
    freshness_policy_reference_id: _NonEmptyReferenceId
    reason_code: _NonEmptyReferenceId
    verified_actor_required: Literal[True] = True
    account_scope_required: Literal[True] = True
    read_only: Literal[True] = True
    notification_authority_required: Literal[True] = True
    client_history_authority: Literal[False] = False
    web_delivery_evaluator: Literal[False] = False
    direct_notification_write_authority: Literal[False] = False
    outbox_mutation_authority: Literal[False] = False
    attempt_mutation_authority: Literal[False] = False
    retry_authority: Literal[False] = False
    reconciliation_execution_authority: Literal[False] = False
    provider_mapping_authority: Literal[False] = False
    provider_call_authority: Literal[False] = False
    read_tracking_authority: Literal[False] = False
    click_tracking_authority: Literal[False] = False
    retention_policy_defined: Literal[False] = False
    raw_provider_payload_present: Literal[False] = False
    full_message_history_requested: Literal[False] = False
    full_listing_archive_requested: Literal[False] = False

    @model_validator(mode="after")
    def _validate_query(self) -> "RequestWebNotificationHistoryQuery":
        _validate_reference_tuple(self.beacon_scope_ids, "Beacon scope")
        return self


class WebNotificationListingReferenceProjection(_WebNotificationHistoryContract):
    web_notification_listing_reference_projection_id: _NonEmptyReferenceId
    account_id: _NonEmptyReferenceId
    beacon_id: _NonEmptyReferenceId | None = None
    safe_listing_reference_id: _NonEmptyReferenceId
    notification_listing_card_reference_id: _NonEmptyReferenceId | None = None
    source_event_reference_id: _NonEmptyReferenceId
    source_fact_reference_id: _NonEmptyReferenceId | None = None
    provenance_reference_ids: tuple[_NonEmptyReferenceId, ...]
    evidence_reference_ids: tuple[_NonEmptyReferenceId, ...]
    reason_code: _NonEmptyReferenceId
    safe_reference_only: Literal[True] = True
    notification_projection_source: Literal[True] = True
    listing_reference_preserved: Literal[True] = True
    raw_listing_value_retained: Literal[False] = False
    raw_avito_payload_retained: Literal[False] = False
    raw_provider_payload_retained: Literal[False] = False
    contact_data_retained: Literal[False] = False
    full_listing_archive_authority: Literal[False] = False
    fetch_authority: Literal[False] = False
    parse_authority: Literal[False] = False
    enrichment_authority: Literal[False] = False
    provider_call_authority: Literal[False] = False
    retention_authority: Literal[False] = False

    @model_validator(mode="after")
    def _validate_listing_reference(self) -> "WebNotificationListingReferenceProjection":
        _validate_reference_tuple(self.provenance_reference_ids, "provenance", allow_empty=False)
        _validate_reference_tuple(self.evidence_reference_ids, "evidence")
        return self


class WebNotificationDeliveryHistoryEntry(_WebNotificationHistoryContract):
    web_notification_delivery_history_entry_id: _NonEmptyReferenceId
    account_id: _NonEmptyReferenceId
    beacon_id: _NonEmptyReferenceId | None = None
    notification_history_entry_reference_id: _NonEmptyReferenceId
    notification_batch_item_reference_id: _NonEmptyReferenceId
    notification_source_decision_reference_id: _NonEmptyReferenceId
    notification_outbox_item_reference_id: _NonEmptyReferenceId | None = None
    notification_attempt_reference_id: _NonEmptyReferenceId | None = None
    channel_class_reference_id: _NonEmptyReferenceId | None = None
    safe_result_reference_id: _NonEmptyReferenceId
    delivery_state: WebNotificationDeliveryState
    safe_error_category_reference_id: _NonEmptyReferenceId
    safe_reason_codes: tuple[_NonEmptyReferenceId, ...]
    listing_references: tuple[WebNotificationListingReferenceProjection, ...]
    listing_count: int
    reconciliation_required: bool
    reconciliation_reference_id: _NonEmptyReferenceId | None = None
    retry_policy_required: bool
    retry_policy_reference_id: _NonEmptyReferenceId | None = None
    evidence_reference_ids: tuple[_NonEmptyReferenceId, ...]
    freshness_reference_ids: tuple[_NonEmptyReferenceId, ...]
    provenance_reference_ids: tuple[_NonEmptyReferenceId, ...]
    derived_from_notification: Literal[True] = True
    safe_projection_only: Literal[True] = True
    per_item_outcome_exposed: Literal[True] = True
    listing_references_preserved: Literal[True] = True
    web_delivery_authority: Literal[False] = False
    delivery_execution_authority: Literal[False] = False
    provider_mapping_authority: Literal[False] = False
    provider_call_authority: Literal[False] = False
    outbox_mutation_authority: Literal[False] = False
    attempt_mutation_authority: Literal[False] = False
    retry_execution_authority: Literal[False] = False
    reconciliation_execution_authority: Literal[False] = False
    read_tracking_authority: Literal[False] = False
    click_tracking_authority: Literal[False] = False
    retention_authority: Literal[False] = False
    raw_message_content_retained: Literal[False] = False
    full_chat_history_retained: Literal[False] = False
    full_listing_archive_retained: Literal[False] = False
    raw_listing_payload_retained: Literal[False] = False
    raw_provider_payload_retained: Literal[False] = False
    business_success_authority: Literal[False] = False

    @model_validator(mode="after")
    def _validate_entry(self) -> "WebNotificationDeliveryHistoryEntry":
        _validate_reference_tuple(self.safe_reason_codes, "safe reason code", allow_empty=False)
        for label, values in (
            ("evidence", self.evidence_reference_ids),
            ("freshness", self.freshness_reference_ids),
            ("provenance", self.provenance_reference_ids),
        ):
            _validate_reference_tuple(values, label)
        if self.listing_count != len(self.listing_references) or self.listing_count < 0:
            raise ValueError("listing_count must match listing_references")
        projection_ids = tuple(
            item.web_notification_listing_reference_projection_id
            for item in self.listing_references
        )
        safe_ids = tuple(item.safe_listing_reference_id for item in self.listing_references)
        _validate_reference_tuple(projection_ids, "listing projection")
        _validate_reference_tuple(safe_ids, "safe listing")
        for item in self.listing_references:
            if item.account_id != self.account_id or item.beacon_id != self.beacon_id:
                raise ValueError("listing reference account and Beacon must match entry")
        if self.delivery_state is WebNotificationDeliveryState.DELIVERED:
            if (
                not self.notification_outbox_item_reference_id
                or not self.notification_attempt_reference_id
                or not self.channel_class_reference_id
            ):
                raise ValueError("delivered entry requires outbox, attempt and channel references")
            if self.reconciliation_required:
                raise ValueError("delivered entry cannot require reconciliation")
        if self.delivery_state is WebNotificationDeliveryState.FAILED:
            if (
                not self.notification_attempt_reference_id
                or not self.safe_error_category_reference_id
            ):
                raise ValueError("failed entry requires attempt and safe error category")
        if self.delivery_state is WebNotificationDeliveryState.RECONCILIATION_REQUIRED:
            if not self.reconciliation_required or not self.reconciliation_reference_id:
                raise ValueError("reconciliation-required entry requires reconciliation reference")
        elif self.reconciliation_required or self.reconciliation_reference_id is not None:
            raise ValueError("non-reconciliation entry cannot carry reconciliation state")
        if (
            self.retry_policy_required
            and self.delivery_state is not WebNotificationDeliveryState.FAILED
        ):
            raise ValueError("retry policy is only allowed for failed entries")
        if not self.retry_policy_required and self.retry_policy_reference_id is not None:
            raise ValueError("retry policy reference requires retry policy")
        if self.retry_policy_required and self.retry_policy_reference_id is None:
            raise ValueError("required retry policy needs a reference")
        return self


class WebNotificationHistoryResult(_WebNotificationHistoryContract):
    web_notification_history_result_id: _NonEmptyReferenceId
    metadata: ContractMetadata
    query: RequestWebNotificationHistoryQuery
    state: WebNotificationHistoryResultState
    freshness: WebReadFreshness
    owning_module_id: _NonEmptyReferenceId
    notification_read_model_reference_id: _NonEmptyReferenceId | None = None
    notification_projection_decision_reference_id: _NonEmptyReferenceId | None = None
    history_entries: tuple[WebNotificationDeliveryHistoryEntry, ...]
    safe_listing_references: tuple[WebNotificationListingReferenceProjection, ...]
    listing_count: int
    history_entry_count: int
    replay_visible: bool
    failure_visible: bool
    reconciliation_required: bool
    source_reference_ids: tuple[_NonEmptyReferenceId, ...]
    freshness_reference_ids: tuple[_NonEmptyReferenceId, ...]
    provenance_reference_ids: tuple[_NonEmptyReferenceId, ...]
    evidence_reference_ids: tuple[_NonEmptyReferenceId, ...]
    ambiguity_reference_id: _NonEmptyReferenceId | None = None
    reason_code: _NonEmptyReferenceId
    safe_projection_only: Literal[True] = True
    notification_authoritative: Literal[True] = True
    web_notification_authority: Literal[False] = False
    per_item_outcomes_exposed: Literal[True] = True
    listing_references_preserved: Literal[True] = True
    preview_truncation_applied: Literal[False] = False
    delivery_execution_authority: Literal[False] = False
    provider_mapping_authority: Literal[False] = False
    provider_call_authority: Literal[False] = False
    outbox_mutation_authority: Literal[False] = False
    attempt_mutation_authority: Literal[False] = False
    retry_execution_authority: Literal[False] = False
    reconciliation_execution_authority: Literal[False] = False
    read_tracking_authority: Literal[False] = False
    click_tracking_authority: Literal[False] = False
    retention_policy_defined: Literal[False] = False
    full_listing_archive_retained: Literal[False] = False
    full_message_history_retained: Literal[False] = False
    full_chat_history_retained: Literal[False] = False
    raw_listing_payload_retained: Literal[False] = False
    raw_provider_payload_retained: Literal[False] = False
    credentials_retained: Literal[False] = False
    minimal_personal_data: Literal[True] = True
    redacted: Literal[True] = True
    business_success_authority: Literal[False] = False

    @model_validator(mode="after")
    def _validate_result(self) -> "WebNotificationHistoryResult":
        if self.owning_module_id != NOTIFICATION_DELIVERY_MODULE_ID:
            raise ValueError("result must be owned by Notification Delivery")
        for label, values in (
            ("source", self.source_reference_ids),
            ("freshness", self.freshness_reference_ids),
            ("provenance", self.provenance_reference_ids),
            ("evidence", self.evidence_reference_ids),
        ):
            _validate_reference_tuple(values, label, allow_empty=False)
        if self.listing_count != len(self.safe_listing_references) or self.listing_count < 0:
            raise ValueError("listing_count must match safe_listing_references")
        if self.history_entry_count != len(self.history_entries) or self.history_entry_count < 0:
            raise ValueError("history_entry_count must match history_entries")
        entry_ids = tuple(
            item.web_notification_delivery_history_entry_id for item in self.history_entries
        )
        history_ids = tuple(
            item.notification_history_entry_reference_id for item in self.history_entries
        )
        batch_ids = tuple(
            item.notification_batch_item_reference_id for item in self.history_entries
        )
        for label, values in (
            ("history entry", entry_ids),
            ("notification history entry", history_ids),
            ("batch item", batch_ids),
        ):
            _validate_reference_tuple(values, label)
        if any(item.account_id != self.query.account_id for item in self.history_entries):
            raise ValueError("history entry account must match query")
        scope = set(self.query.beacon_scope_ids)
        if scope and any(
            item.beacon_id is not None and item.beacon_id not in scope
            for item in self.history_entries
        ):
            raise ValueError("history entry Beacon is outside query scope")
        global_projection_ids = tuple(
            item.web_notification_listing_reference_projection_id
            for item in self.safe_listing_references
        )
        global_safe_ids = tuple(
            item.safe_listing_reference_id for item in self.safe_listing_references
        )
        _validate_reference_tuple(global_projection_ids, "global listing projection")
        _validate_reference_tuple(global_safe_ids, "global safe listing")
        for item in self.safe_listing_references:
            if item.account_id != self.query.account_id:
                raise ValueError("global listing account must match query")
            if scope and item.beacon_id is not None and item.beacon_id not in scope:
                raise ValueError("global listing Beacon is outside query scope")
        expected_listings = _first_occurrence_union(
            *(
                tuple(item.safe_listing_reference_id for item in entry.listing_references)
                for entry in self.history_entries
            )
        )
        if (
            tuple(item.safe_listing_reference_id for item in self.safe_listing_references)
            != expected_listings
        ):
            raise ValueError(
                "safe listing references must preserve complete first-occurrence union"
            )
        if self.replay_visible != any(
            item.delivery_state is WebNotificationDeliveryState.REPLAYED
            for item in self.history_entries
        ):
            raise ValueError("replay visibility must reflect per-item outcomes")
        if self.failure_visible != any(
            item.delivery_state is WebNotificationDeliveryState.FAILED
            for item in self.history_entries
        ):
            raise ValueError("failure visibility must reflect per-item outcomes")
        if self.reconciliation_required != any(
            item.delivery_state is WebNotificationDeliveryState.RECONCILIATION_REQUIRED
            for item in self.history_entries
        ):
            raise ValueError("reconciliation visibility must reflect per-item outcomes")
        self._validate_state_requirements()
        return self

    def _validate_state_requirements(self) -> None:
        if self.state is WebNotificationHistoryResultState.AVAILABLE:
            if (
                self.freshness is not WebReadFreshness.FRESH
                or not self.history_entries
                or not self.notification_read_model_reference_id
                or not self.notification_projection_decision_reference_id
                or self.reconciliation_required
            ):
                raise ValueError("available result requirements are not met")
        elif self.state is WebNotificationHistoryResultState.NOT_FOUND_SAFE:
            if (
                self.freshness is not WebReadFreshness.FRESH
                or self.history_entries
                or self.safe_listing_references
                or self.listing_count
                or self.history_entry_count
                or self.replay_visible
                or self.failure_visible
                or self.reconciliation_required
            ):
                raise ValueError("not-found-safe result must be empty and fresh")
        elif self.state is WebNotificationHistoryResultState.FORBIDDEN:
            if (
                self.history_entries
                or self.safe_listing_references
                or self.listing_count
                or self.history_entry_count
                or self.notification_read_model_reference_id
                or self.notification_projection_decision_reference_id
                or self.replay_visible
                or self.failure_visible
                or self.reconciliation_required
            ):
                raise ValueError("forbidden result must not expose notification data")
        elif self.state is WebNotificationHistoryResultState.STALE:
            if (
                self.freshness is not WebReadFreshness.STALE
                or not self.notification_projection_decision_reference_id
            ):
                raise ValueError("stale result requirements are not met")
        elif self.state is WebNotificationHistoryResultState.AMBIGUOUS:
            if self.freshness is not WebReadFreshness.AMBIGUOUS or not self.ambiguity_reference_id:
                raise ValueError("ambiguous result requirements are not met")
        elif self.state is WebNotificationHistoryResultState.RECONCILIATION_REQUIRED:
            if (
                not self.reconciliation_required
                or not self.notification_read_model_reference_id
                or not self.notification_projection_decision_reference_id
            ):
                raise ValueError("reconciliation result requirements are not met")
        if (
            self.state is not WebNotificationHistoryResultState.STALE
            and self.freshness is WebReadFreshness.STALE
        ):
            raise ValueError("only stale state may use stale freshness")
        if (
            self.state is not WebNotificationHistoryResultState.AMBIGUOUS
            and self.freshness is WebReadFreshness.AMBIGUOUS
        ):
            raise ValueError("only ambiguous state may use ambiguous freshness")
        if (
            self.state is not WebNotificationHistoryResultState.AMBIGUOUS
            and self.ambiguity_reference_id is not None
        ):
            raise ValueError("non-ambiguous result cannot carry ambiguity reference")
        if self.state is not WebNotificationHistoryResultState.RECONCILIATION_REQUIRED and any(
            item.reconciliation_required for item in self.history_entries
        ):
            raise ValueError("only reconciliation result may expose reconciliation entries")


__all__ = [
    "RequestWebNotificationHistoryQuery",
    "WebNotificationDeliveryHistoryEntry",
    "WebNotificationDeliveryState",
    "WebNotificationHistoryResult",
    "WebNotificationHistoryResultState",
    "WebNotificationListingReferenceProjection",
]
