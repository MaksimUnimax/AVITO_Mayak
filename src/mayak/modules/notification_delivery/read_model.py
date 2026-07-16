from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .batch import (
    NotificationBatchDecision,
    NotificationBatchDisposition,
    NotificationBatchItemResult,
    NotificationBatchSafeErrorCategory,
)
from .eligibility import NotificationChannelClass

ND12_TASK_ID = "MAYAK-ND-12-READ-MODEL-HISTORY-20260716-003"


class NotificationReadAudience(str, Enum):
    USER = "USER"
    ADMIN = "ADMIN"
    SUPPORT = "SUPPORT"


class NotificationDeliveryReadStatus(str, Enum):
    PLANNED = "PLANNED"
    REPLAYED = "REPLAYED"
    SUPPRESSED = "SUPPRESSED"
    BLOCKED = "BLOCKED"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"
    RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"


class NotificationDeliveryHistoryClassification(str, Enum):
    PLANNED = "PLANNED"
    REPLAYED = "REPLAYED"
    SUPPRESSED = "SUPPRESSED"
    BLOCKED = "BLOCKED"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"
    RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"


class NotificationReadProjectionStatus(str, Enum):
    PROJECTED = "PROJECTED"
    RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"


_READ_REASON_BY_STATUS = {
    NotificationReadProjectionStatus.PROJECTED: ("read-model-projected",),
    NotificationReadProjectionStatus.RECONCILIATION_REQUIRED: (
        "read-model-reconciliation-required",
    ),
}

_READ_STATUS_BY_DISPOSITION = {
    NotificationBatchDisposition.CREATED: NotificationDeliveryReadStatus.PLANNED,
    NotificationBatchDisposition.REPLAYED: NotificationDeliveryReadStatus.REPLAYED,
    NotificationBatchDisposition.SUPPRESSED: NotificationDeliveryReadStatus.SUPPRESSED,
    NotificationBatchDisposition.BLOCKED: NotificationDeliveryReadStatus.BLOCKED,
    NotificationBatchDisposition.DELIVERED: NotificationDeliveryReadStatus.DELIVERED,
    NotificationBatchDisposition.FAILED: NotificationDeliveryReadStatus.FAILED,
    NotificationBatchDisposition.RECONCILIATION_REQUIRED: (
        NotificationDeliveryReadStatus.RECONCILIATION_REQUIRED
    ),
}

_HISTORY_CLASSIFICATION_BY_DISPOSITION = {
    NotificationBatchDisposition.CREATED: NotificationDeliveryHistoryClassification.PLANNED,
    NotificationBatchDisposition.REPLAYED: NotificationDeliveryHistoryClassification.REPLAYED,
    NotificationBatchDisposition.SUPPRESSED: NotificationDeliveryHistoryClassification.SUPPRESSED,
    NotificationBatchDisposition.BLOCKED: NotificationDeliveryHistoryClassification.BLOCKED,
    NotificationBatchDisposition.DELIVERED: NotificationDeliveryHistoryClassification.DELIVERED,
    NotificationBatchDisposition.FAILED: NotificationDeliveryHistoryClassification.FAILED,
    NotificationBatchDisposition.RECONCILIATION_REQUIRED: (
        NotificationDeliveryHistoryClassification.RECONCILIATION_REQUIRED
    ),
}


def _require_text(value: object, field_name: str) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-blank string")
    return value


def _require_optional_text(value: object, field_name: str) -> str | None:
    if value is None:
        return None
    return _require_text(value, field_name)


def _require_bool(value: object, field_name: str) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _require_exact_enum(value: object, enum_type: type[Enum], field_name: str) -> Enum:
    if type(value) is not enum_type:
        raise ValueError(f"{field_name} must be {enum_type.__name__}")
    return value


def _require_text_tuple(
    value: object,
    field_name: str,
    *,
    allow_empty: bool,
    unique: bool,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value and not allow_empty:
        raise ValueError(f"{field_name} must not be empty")
    validated = tuple(_require_text(item, field_name) for item in value)
    if unique and len(set(validated)) != len(validated):
        raise ValueError(f"{field_name} must not contain duplicate values")
    return validated


def _first_occurrence_union(*tuples: tuple[str, ...]) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []
    for items in tuples:
        for item in items:
            if item not in seen:
                seen.add(item)
                ordered.append(item)
    return tuple(ordered)


def _audience_reason_code(audience: NotificationReadAudience) -> tuple[str, ...]:
    return {
        NotificationReadAudience.USER: ("read-model-user",),
        NotificationReadAudience.ADMIN: ("read-model-admin",),
        NotificationReadAudience.SUPPORT: ("read-model-support",),
    }[audience]


def _status_reason_codes(status: NotificationReadProjectionStatus) -> tuple[str, ...]:
    return _READ_REASON_BY_STATUS[status]


@dataclass(frozen=True, slots=True)
class NotificationReadAuthorizationScope:
    scope_id: str
    audience: NotificationReadAudience
    authorized: bool
    account_id: str
    beacon_scope_ids: tuple[str, ...]
    authorization_reference_id: str
    evidence_reference_ids: tuple[str, ...]
    freshness_reference_ids: tuple[str, ...]
    provenance_reference_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_text(self.scope_id, "scope_id")
        _require_exact_enum(self.audience, NotificationReadAudience, "audience")
        _require_bool(self.authorized, "authorized")
        _require_text(self.account_id, "account_id")
        _require_text_tuple(
            self.beacon_scope_ids,
            "beacon_scope_ids",
            allow_empty=True,
            unique=True,
        )
        _require_text(self.authorization_reference_id, "authorization_reference_id")
        _require_text_tuple(
            self.evidence_reference_ids,
            "evidence_reference_ids",
            allow_empty=True,
            unique=True,
        )
        _require_text_tuple(
            self.freshness_reference_ids,
            "freshness_reference_ids",
            allow_empty=True,
            unique=True,
        )
        _require_text_tuple(
            self.provenance_reference_ids,
            "provenance_reference_ids",
            allow_empty=True,
            unique=True,
        )


@dataclass(frozen=True, slots=True)
class NotificationDeliveryHistoryEntry:
    history_entry_id: str
    batch_item_id: str
    account_id: str
    beacon_id: str | None
    source_decision_id: str
    outbox_item_id: str | None
    attempt_id: str | None
    channel_class: NotificationChannelClass | None
    delivery_status: NotificationDeliveryReadStatus
    history_classification: NotificationDeliveryHistoryClassification
    reconciliation_required: bool
    retry_policy_required: bool
    provider_safe_error_category: NotificationBatchSafeErrorCategory
    safe_reason_codes: tuple[str, ...]
    safe_listing_reference_ids: tuple[str, ...]
    listing_count: int
    evidence_reference_ids: tuple[str, ...]
    freshness_reference_ids: tuple[str, ...]
    provenance_reference_ids: tuple[str, ...]
    audience: NotificationReadAudience
    mutation_authorized: bool
    execution_authorized: bool
    provider_mapping_authorized: bool
    read_tracking_authorized: bool
    click_tracking_authorized: bool
    retention_authorized: bool

    def __post_init__(self) -> None:
        _require_text(self.history_entry_id, "history_entry_id")
        _require_text(self.batch_item_id, "batch_item_id")
        _require_text(self.account_id, "account_id")
        _require_optional_text(self.beacon_id, "beacon_id")
        _require_text(self.source_decision_id, "source_decision_id")
        _require_optional_text(self.outbox_item_id, "outbox_item_id")
        _require_optional_text(self.attempt_id, "attempt_id")
        if self.channel_class is not None:
            _require_exact_enum(self.channel_class, NotificationChannelClass, "channel_class")
        _require_exact_enum(
            self.delivery_status,
            NotificationDeliveryReadStatus,
            "delivery_status",
        )
        _require_exact_enum(
            self.history_classification,
            NotificationDeliveryHistoryClassification,
            "history_classification",
        )
        if self.delivery_status.value != self.history_classification.value:
            raise ValueError("history classification must match the delivery status")
        _require_bool(self.reconciliation_required, "reconciliation_required")
        _require_bool(self.retry_policy_required, "retry_policy_required")
        _require_exact_enum(
            self.provider_safe_error_category,
            NotificationBatchSafeErrorCategory,
            "provider_safe_error_category",
        )
        _require_text_tuple(
            self.safe_reason_codes,
            "safe_reason_codes",
            allow_empty=False,
            unique=True,
        )
        _require_text_tuple(
            self.safe_listing_reference_ids,
            "safe_listing_reference_ids",
            allow_empty=True,
            unique=True,
        )
        if type(self.listing_count) is not int or self.listing_count < 0:
            raise ValueError("listing_count must be a non-negative int")
        if self.listing_count != len(self.safe_listing_reference_ids):
            raise ValueError("listing_count must match safe_listing_reference_ids")
        _require_text_tuple(
            self.evidence_reference_ids,
            "evidence_reference_ids",
            allow_empty=True,
            unique=True,
        )
        _require_text_tuple(
            self.freshness_reference_ids,
            "freshness_reference_ids",
            allow_empty=True,
            unique=True,
        )
        _require_text_tuple(
            self.provenance_reference_ids,
            "provenance_reference_ids",
            allow_empty=True,
            unique=True,
        )
        _require_exact_enum(self.audience, NotificationReadAudience, "audience")
        _require_bool(self.mutation_authorized, "mutation_authorized")
        _require_bool(self.execution_authorized, "execution_authorized")
        _require_bool(self.provider_mapping_authorized, "provider_mapping_authorized")
        _require_bool(self.read_tracking_authorized, "read_tracking_authorized")
        _require_bool(self.click_tracking_authorized, "click_tracking_authorized")
        _require_bool(self.retention_authorized, "retention_authorized")


@dataclass(frozen=True, slots=True)
class NotificationReadModel:
    read_model_id: str
    audience: NotificationReadAudience
    account_id: str
    beacon_scope_ids: tuple[str, ...]
    batch_decision_id: str
    history_entries: tuple[NotificationDeliveryHistoryEntry, ...]
    safe_listing_reference_ids: tuple[str, ...]
    listing_count: int
    history_entry_count: int
    listing_references_preserved: bool
    per_item_outcomes_exposed: bool
    execution_authorized: bool
    provider_mapping_authorized: bool
    mutation_authorized: bool
    read_tracking_authorized: bool
    click_tracking_authorized: bool
    retention_authorized: bool
    replay_visible: bool
    failure_visible: bool
    ambiguous_visible: bool
    reconciliation_required: bool
    freshness_reference_ids: tuple[str, ...]
    provenance_reference_ids: tuple[str, ...]
    evidence_reference_ids: tuple[str, ...]
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_text(self.read_model_id, "read_model_id")
        _require_exact_enum(self.audience, NotificationReadAudience, "audience")
        _require_text(self.account_id, "account_id")
        _require_text_tuple(
            self.beacon_scope_ids,
            "beacon_scope_ids",
            allow_empty=True,
            unique=True,
        )
        _require_text(self.batch_decision_id, "batch_decision_id")
        if type(self.history_entries) is not tuple or not self.history_entries:
            raise ValueError("history_entries must be a non-empty tuple")
        for history_entry in self.history_entries:
            if type(history_entry) is not NotificationDeliveryHistoryEntry:
                raise ValueError("history_entries must contain NotificationDeliveryHistoryEntry")
            if history_entry.audience is not self.audience:
                raise ValueError("history_entries must share the read audience")
            if history_entry.account_id != self.account_id:
                raise ValueError("history_entries must share the account")
        _require_text_tuple(
            self.safe_listing_reference_ids,
            "safe_listing_reference_ids",
            allow_empty=True,
            unique=True,
        )
        if type(self.listing_count) is not int or self.listing_count < 0:
            raise ValueError("listing_count must be a non-negative int")
        if self.listing_count != len(self.safe_listing_reference_ids):
            raise ValueError("listing_count must match safe_listing_reference_ids")
        if type(self.history_entry_count) is not int or self.history_entry_count < 0:
            raise ValueError("history_entry_count must be a non-negative int")
        if self.history_entry_count != len(self.history_entries):
            raise ValueError("history_entry_count must match history_entries")
        _require_bool(self.listing_references_preserved, "listing_references_preserved")
        _require_bool(self.per_item_outcomes_exposed, "per_item_outcomes_exposed")
        _require_bool(self.execution_authorized, "execution_authorized")
        _require_bool(self.provider_mapping_authorized, "provider_mapping_authorized")
        _require_bool(self.mutation_authorized, "mutation_authorized")
        _require_bool(self.read_tracking_authorized, "read_tracking_authorized")
        _require_bool(self.click_tracking_authorized, "click_tracking_authorized")
        _require_bool(self.retention_authorized, "retention_authorized")
        _require_bool(self.replay_visible, "replay_visible")
        _require_bool(self.failure_visible, "failure_visible")
        _require_bool(self.ambiguous_visible, "ambiguous_visible")
        _require_bool(self.reconciliation_required, "reconciliation_required")
        _require_text_tuple(
            self.freshness_reference_ids,
            "freshness_reference_ids",
            allow_empty=True,
            unique=True,
        )
        _require_text_tuple(
            self.provenance_reference_ids,
            "provenance_reference_ids",
            allow_empty=True,
            unique=True,
        )
        _require_text_tuple(
            self.evidence_reference_ids,
            "evidence_reference_ids",
            allow_empty=True,
            unique=True,
        )
        _require_text_tuple(self.reason_codes, "reason_codes", allow_empty=False, unique=True)
        if self.reconciliation_required and self.reason_codes != _READ_REASON_BY_STATUS[
            NotificationReadProjectionStatus.RECONCILIATION_REQUIRED
        ]:
            raise ValueError("reconciliation-required read models need the reconciliation reason")
        if not self.reconciliation_required and self.reason_codes != _READ_REASON_BY_STATUS[
            NotificationReadProjectionStatus.PROJECTED
        ]:
            raise ValueError("projected read models need the projected reason")


@dataclass(frozen=True, slots=True)
class NotificationReadModelProjectionDecision:
    decision_id: str
    authorization_scope: NotificationReadAuthorizationScope
    source_batch_decision: NotificationBatchDecision
    read_model: NotificationReadModel
    status: NotificationReadProjectionStatus
    listing_references_preserved: bool
    per_item_outcomes_exposed: bool
    execution_authorized: bool
    provider_mapping_authorized: bool
    mutation_authorized: bool
    read_tracking_authorized: bool
    click_tracking_authorized: bool
    retention_authorized: bool
    reason_codes: tuple[str, ...]
    evidence_reference_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_text(self.decision_id, "decision_id")
        if type(self.authorization_scope) is not NotificationReadAuthorizationScope:
            raise ValueError("authorization_scope must be NotificationReadAuthorizationScope")
        if type(self.source_batch_decision) is not NotificationBatchDecision:
            raise ValueError("source_batch_decision must be NotificationBatchDecision")
        if type(self.read_model) is not NotificationReadModel:
            raise ValueError("read_model must be NotificationReadModel")
        _require_exact_enum(self.status, NotificationReadProjectionStatus, "status")
        _require_bool(self.listing_references_preserved, "listing_references_preserved")
        _require_bool(self.per_item_outcomes_exposed, "per_item_outcomes_exposed")
        _require_bool(self.execution_authorized, "execution_authorized")
        _require_bool(self.provider_mapping_authorized, "provider_mapping_authorized")
        _require_bool(self.mutation_authorized, "mutation_authorized")
        _require_bool(self.read_tracking_authorized, "read_tracking_authorized")
        _require_bool(self.click_tracking_authorized, "click_tracking_authorized")
        _require_bool(self.retention_authorized, "retention_authorized")
        _require_text_tuple(self.reason_codes, "reason_codes", allow_empty=False, unique=True)
        _require_text_tuple(
            self.evidence_reference_ids,
            "evidence_reference_ids",
            allow_empty=True,
            unique=True,
        )

        expected_projection = _project_notification_read_model(
            decision_id=self.decision_id,
            authorization_scope=self.authorization_scope,
            source_batch_decision=self.source_batch_decision,
            evidence_reference_ids=self.evidence_reference_ids,
        )
        if _read_model_values(self.read_model) != expected_projection.read_model_values:
            raise ValueError("notification read models must be canonically projected")
        if _projection_decision_values(self) != expected_projection:
            raise ValueError("notification read model projection decisions must be canonical")


@dataclass(frozen=True, slots=True)
class _HistoryEntryValues:
    history_entry_id: str
    batch_item_id: str
    account_id: str
    beacon_id: str | None
    source_decision_id: str
    outbox_item_id: str | None
    attempt_id: str | None
    channel_class: NotificationChannelClass | None
    delivery_status: NotificationDeliveryReadStatus
    history_classification: NotificationDeliveryHistoryClassification
    reconciliation_required: bool
    retry_policy_required: bool
    provider_safe_error_category: NotificationBatchSafeErrorCategory
    safe_reason_codes: tuple[str, ...]
    safe_listing_reference_ids: tuple[str, ...]
    listing_count: int
    evidence_reference_ids: tuple[str, ...]
    freshness_reference_ids: tuple[str, ...]
    provenance_reference_ids: tuple[str, ...]
    audience: NotificationReadAudience
    mutation_authorized: bool
    execution_authorized: bool
    provider_mapping_authorized: bool
    read_tracking_authorized: bool
    click_tracking_authorized: bool
    retention_authorized: bool


@dataclass(frozen=True, slots=True)
class _ReadModelValues:
    read_model_id: str
    audience: NotificationReadAudience
    account_id: str
    beacon_scope_ids: tuple[str, ...]
    batch_decision_id: str
    history_entries: tuple[_HistoryEntryValues, ...]
    safe_listing_reference_ids: tuple[str, ...]
    listing_count: int
    history_entry_count: int
    listing_references_preserved: bool
    per_item_outcomes_exposed: bool
    execution_authorized: bool
    provider_mapping_authorized: bool
    mutation_authorized: bool
    read_tracking_authorized: bool
    click_tracking_authorized: bool
    retention_authorized: bool
    replay_visible: bool
    failure_visible: bool
    ambiguous_visible: bool
    reconciliation_required: bool
    freshness_reference_ids: tuple[str, ...]
    provenance_reference_ids: tuple[str, ...]
    evidence_reference_ids: tuple[str, ...]
    reason_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class _ProjectionDecisionValues:
    decision_id: str
    authorization_scope: NotificationReadAuthorizationScope
    source_batch_decision_id: str
    read_model_values: _ReadModelValues
    status: NotificationReadProjectionStatus
    listing_references_preserved: bool
    per_item_outcomes_exposed: bool
    execution_authorized: bool
    provider_mapping_authorized: bool
    mutation_authorized: bool
    read_tracking_authorized: bool
    click_tracking_authorized: bool
    retention_authorized: bool
    reason_codes: tuple[str, ...]
    evidence_reference_ids: tuple[str, ...]


def _history_entry_values(history_entry: NotificationDeliveryHistoryEntry) -> _HistoryEntryValues:
    return _HistoryEntryValues(
        history_entry.history_entry_id,
        history_entry.batch_item_id,
        history_entry.account_id,
        history_entry.beacon_id,
        history_entry.source_decision_id,
        history_entry.outbox_item_id,
        history_entry.attempt_id,
        history_entry.channel_class,
        history_entry.delivery_status,
        history_entry.history_classification,
        history_entry.reconciliation_required,
        history_entry.retry_policy_required,
        history_entry.provider_safe_error_category,
        history_entry.safe_reason_codes,
        history_entry.safe_listing_reference_ids,
        history_entry.listing_count,
        history_entry.evidence_reference_ids,
        history_entry.freshness_reference_ids,
        history_entry.provenance_reference_ids,
        history_entry.audience,
        history_entry.mutation_authorized,
        history_entry.execution_authorized,
        history_entry.provider_mapping_authorized,
        history_entry.read_tracking_authorized,
        history_entry.click_tracking_authorized,
        history_entry.retention_authorized,
    )


def _read_model_values(read_model: NotificationReadModel) -> _ReadModelValues:
    return _ReadModelValues(
        read_model.read_model_id,
        read_model.audience,
        read_model.account_id,
        read_model.beacon_scope_ids,
        read_model.batch_decision_id,
        tuple(_history_entry_values(history_entry) for history_entry in read_model.history_entries),
        read_model.safe_listing_reference_ids,
        read_model.listing_count,
        read_model.history_entry_count,
        read_model.listing_references_preserved,
        read_model.per_item_outcomes_exposed,
        read_model.execution_authorized,
        read_model.provider_mapping_authorized,
        read_model.mutation_authorized,
        read_model.read_tracking_authorized,
        read_model.click_tracking_authorized,
        read_model.retention_authorized,
        read_model.replay_visible,
        read_model.failure_visible,
        read_model.ambiguous_visible,
        read_model.reconciliation_required,
        read_model.freshness_reference_ids,
        read_model.provenance_reference_ids,
        read_model.evidence_reference_ids,
        read_model.reason_codes,
    )


def _project_history_entry(
    *,
    item_result: NotificationBatchItemResult,
    audience: NotificationReadAudience,
    evidence_reference_ids: tuple[str, ...],
    freshness_reference_ids: tuple[str, ...],
    provenance_reference_ids: tuple[str, ...],
) -> NotificationDeliveryHistoryEntry:
    if type(item_result) is not NotificationBatchItemResult:
        raise ValueError("item_results must contain NotificationBatchItemResult")
    if _require_exact_enum(
        item_result.disposition,
        NotificationBatchDisposition,
        "disposition",
    ) is None:
        raise AssertionError("unreachable")

    delivery_status = _READ_STATUS_BY_DISPOSITION[item_result.disposition]
    history_classification = _HISTORY_CLASSIFICATION_BY_DISPOSITION[item_result.disposition]
    return NotificationDeliveryHistoryEntry(
        history_entry_id=item_result.batch_item_id,
        batch_item_id=item_result.batch_item_id,
        account_id=item_result.account_id,
        beacon_id=item_result.beacon_id,
        source_decision_id=item_result.source_decision_id,
        outbox_item_id=item_result.outbox_item_id,
        attempt_id=item_result.attempt_id,
        channel_class=item_result.channel_class,
        delivery_status=delivery_status,
        history_classification=history_classification,
        reconciliation_required=item_result.reconciliation_required,
        retry_policy_required=item_result.retry_policy_required,
        provider_safe_error_category=item_result.safe_error_category,
        safe_reason_codes=item_result.reason_codes,
        safe_listing_reference_ids=item_result.safe_listing_reference_ids,
        listing_count=len(item_result.safe_listing_reference_ids),
        evidence_reference_ids=evidence_reference_ids,
        freshness_reference_ids=freshness_reference_ids,
        provenance_reference_ids=provenance_reference_ids,
        audience=audience,
        mutation_authorized=False,
        execution_authorized=False,
        provider_mapping_authorized=False,
        read_tracking_authorized=False,
        click_tracking_authorized=False,
        retention_authorized=False,
    )


def _project_notification_read_model(
    *,
    decision_id: str,
    authorization_scope: NotificationReadAuthorizationScope,
    source_batch_decision: NotificationBatchDecision,
    evidence_reference_ids: tuple[str, ...],
) -> _ProjectionDecisionValues:
    _require_text(decision_id, "decision_id")
    if type(authorization_scope) is not NotificationReadAuthorizationScope:
        raise ValueError("authorization_scope must be NotificationReadAuthorizationScope")
    if type(source_batch_decision) is not NotificationBatchDecision:
        raise ValueError("source_batch_decision must be NotificationBatchDecision")
    _require_text_tuple(
        evidence_reference_ids,
        "evidence_reference_ids",
        allow_empty=True,
        unique=True,
    )

    if authorization_scope.authorized is not True:
        raise ValueError("authorization scope must be authorized")
    if authorization_scope.account_id != source_batch_decision.account_id:
        raise ValueError("authorization scope does not match the batch decision")

    item_results = source_batch_decision.item_results
    if type(item_results) is not tuple or not item_results:
        raise ValueError("source batch decision must expose item results")
    if source_batch_decision.item_count != len(item_results):
        raise ValueError("source batch decision must stay aligned with item results")

    seen_batch_item_ids: set[str] = set()
    seen_source_decision_ids: set[str] = set()
    history_entries: list[NotificationDeliveryHistoryEntry] = []
    for item_result in item_results:
        if type(item_result) is not NotificationBatchItemResult:
            raise ValueError("source batch decision must contain NotificationBatchItemResult")
        if item_result.account_id != source_batch_decision.account_id:
            raise ValueError("authorization scope does not match the batch decision")
        if item_result.batch_item_id in seen_batch_item_ids:
            raise ValueError("duplicate batch item identities are not allowed")
        seen_batch_item_ids.add(item_result.batch_item_id)
        if item_result.source_decision_id in seen_source_decision_ids:
            raise ValueError("duplicate source decision identities are not allowed")
        seen_source_decision_ids.add(item_result.source_decision_id)
        if item_result.beacon_id is not None and item_result.beacon_id not in (
            authorization_scope.beacon_scope_ids
        ):
            raise ValueError("authorization scope does not cover the batch beacons")

        combined_evidence_reference_ids = _first_occurrence_union(
            authorization_scope.evidence_reference_ids,
            source_batch_decision.evidence_reference_ids,
            item_result.evidence_reference_ids,
            evidence_reference_ids,
        )
        combined_freshness_reference_ids = _first_occurrence_union(
            authorization_scope.freshness_reference_ids,
            source_batch_decision.evidence_reference_ids,
            item_result.evidence_reference_ids,
        )
        combined_provenance_reference_ids = _first_occurrence_union(
            authorization_scope.provenance_reference_ids,
            source_batch_decision.evidence_reference_ids,
            item_result.evidence_reference_ids,
        )
        history_entries.append(
            _project_history_entry(
                item_result=item_result,
                audience=authorization_scope.audience,
                evidence_reference_ids=combined_evidence_reference_ids,
                freshness_reference_ids=combined_freshness_reference_ids,
                provenance_reference_ids=combined_provenance_reference_ids,
            )
        )

    safe_listing_reference_ids = _first_occurrence_union(
        *(history_entry.safe_listing_reference_ids for history_entry in history_entries),
    )
    listing_count = len(safe_listing_reference_ids)
    replay_visible = any(
        history_entry.history_classification is NotificationDeliveryHistoryClassification.REPLAYED
        for history_entry in history_entries
    )
    failure_visible = any(
        history_entry.delivery_status is NotificationDeliveryReadStatus.FAILED
        for history_entry in history_entries
    )
    ambiguous_visible = any(
        history_entry.delivery_status
        is NotificationDeliveryReadStatus.RECONCILIATION_REQUIRED
        for history_entry in history_entries
    )
    reconciliation_required = any(
        history_entry.reconciliation_required for history_entry in history_entries
    ) or ambiguous_visible
    status = (
        NotificationReadProjectionStatus.RECONCILIATION_REQUIRED
        if reconciliation_required
        else NotificationReadProjectionStatus.PROJECTED
    )
    reason_codes = _status_reason_codes(status)
    combined_evidence_reference_ids = _first_occurrence_union(
        authorization_scope.evidence_reference_ids,
        source_batch_decision.evidence_reference_ids,
        evidence_reference_ids,
        *(history_entry.evidence_reference_ids for history_entry in history_entries),
    )
    combined_freshness_reference_ids = _first_occurrence_union(
        authorization_scope.freshness_reference_ids,
        source_batch_decision.evidence_reference_ids,
        *(history_entry.freshness_reference_ids for history_entry in history_entries),
    )
    combined_provenance_reference_ids = _first_occurrence_union(
        authorization_scope.provenance_reference_ids,
        source_batch_decision.evidence_reference_ids,
        *(history_entry.provenance_reference_ids for history_entry in history_entries),
    )

    read_model = NotificationReadModel(
        read_model_id=decision_id,
        audience=authorization_scope.audience,
        account_id=source_batch_decision.account_id,
        beacon_scope_ids=authorization_scope.beacon_scope_ids,
        batch_decision_id=source_batch_decision.batch_id,
        history_entries=tuple(history_entries),
        safe_listing_reference_ids=safe_listing_reference_ids,
        listing_count=listing_count,
        history_entry_count=len(history_entries),
        listing_references_preserved=True,
        per_item_outcomes_exposed=True,
        execution_authorized=False,
        provider_mapping_authorized=False,
        mutation_authorized=False,
        read_tracking_authorized=False,
        click_tracking_authorized=False,
        retention_authorized=False,
        replay_visible=replay_visible,
        failure_visible=failure_visible,
        ambiguous_visible=ambiguous_visible,
        reconciliation_required=reconciliation_required,
        freshness_reference_ids=combined_freshness_reference_ids,
        provenance_reference_ids=combined_provenance_reference_ids,
        evidence_reference_ids=combined_evidence_reference_ids,
        reason_codes=reason_codes,
    )

    return _ProjectionDecisionValues(
        decision_id=decision_id,
        authorization_scope=authorization_scope,
        source_batch_decision_id=source_batch_decision.batch_id,
        read_model_values=_read_model_values(read_model),
        status=status,
        listing_references_preserved=True,
        per_item_outcomes_exposed=True,
        execution_authorized=False,
        provider_mapping_authorized=False,
        mutation_authorized=False,
        read_tracking_authorized=False,
        click_tracking_authorized=False,
        retention_authorized=False,
        reason_codes=reason_codes,
        evidence_reference_ids=combined_evidence_reference_ids,
    )


def project_notification_read_model(
    *,
    decision_id: str,
    authorization_scope: NotificationReadAuthorizationScope,
    source_batch_decision: NotificationBatchDecision,
    evidence_reference_ids: tuple[str, ...],
) -> NotificationReadModelProjectionDecision:
    projection = _project_notification_read_model(
        decision_id=decision_id,
        authorization_scope=authorization_scope,
        source_batch_decision=source_batch_decision,
        evidence_reference_ids=evidence_reference_ids,
    )
    read_model = NotificationReadModel(
        read_model_id=projection.decision_id,
        audience=projection.authorization_scope.audience,
        account_id=source_batch_decision.account_id,
        beacon_scope_ids=authorization_scope.beacon_scope_ids,
        batch_decision_id=source_batch_decision.batch_id,
        history_entries=tuple(
            _project_history_entry(
                item_result=item_result,
                audience=authorization_scope.audience,
                evidence_reference_ids=_first_occurrence_union(
                    authorization_scope.evidence_reference_ids,
                    source_batch_decision.evidence_reference_ids,
                    item_result.evidence_reference_ids,
                    evidence_reference_ids,
                ),
                freshness_reference_ids=_first_occurrence_union(
                    authorization_scope.freshness_reference_ids,
                    source_batch_decision.evidence_reference_ids,
                    item_result.evidence_reference_ids,
                ),
                provenance_reference_ids=_first_occurrence_union(
                    authorization_scope.provenance_reference_ids,
                    source_batch_decision.evidence_reference_ids,
                    item_result.evidence_reference_ids,
                ),
            )
            for item_result in source_batch_decision.item_results
        ),
        safe_listing_reference_ids=_first_occurrence_union(
            *(
                item_result.safe_listing_reference_ids
                for item_result in source_batch_decision.item_results
            ),
        ),
        listing_count=len(
            _first_occurrence_union(
                *(
                    item_result.safe_listing_reference_ids
                    for item_result in source_batch_decision.item_results
                ),
            )
        ),
        history_entry_count=len(source_batch_decision.item_results),
        listing_references_preserved=True,
        per_item_outcomes_exposed=True,
        execution_authorized=False,
        provider_mapping_authorized=False,
        mutation_authorized=False,
        read_tracking_authorized=False,
        click_tracking_authorized=False,
        retention_authorized=False,
        replay_visible=any(
            item_result.disposition is NotificationBatchDisposition.REPLAYED
            for item_result in source_batch_decision.item_results
        ),
        failure_visible=any(
            item_result.disposition is NotificationBatchDisposition.FAILED
            for item_result in source_batch_decision.item_results
        ),
        ambiguous_visible=any(
            item_result.disposition is NotificationBatchDisposition.RECONCILIATION_REQUIRED
            for item_result in source_batch_decision.item_results
        ),
        reconciliation_required=projection.status
        is NotificationReadProjectionStatus.RECONCILIATION_REQUIRED,
        freshness_reference_ids=projection.read_model_values.freshness_reference_ids,
        provenance_reference_ids=projection.read_model_values.provenance_reference_ids,
        evidence_reference_ids=projection.read_model_values.evidence_reference_ids,
        reason_codes=projection.reason_codes,
    )
    return NotificationReadModelProjectionDecision(
        decision_id=projection.decision_id,
        authorization_scope=projection.authorization_scope,
        source_batch_decision=source_batch_decision,
        read_model=read_model,
        status=projection.status,
        listing_references_preserved=projection.listing_references_preserved,
        per_item_outcomes_exposed=projection.per_item_outcomes_exposed,
        execution_authorized=projection.execution_authorized,
        provider_mapping_authorized=projection.provider_mapping_authorized,
        mutation_authorized=projection.mutation_authorized,
        read_tracking_authorized=projection.read_tracking_authorized,
        click_tracking_authorized=projection.click_tracking_authorized,
        retention_authorized=projection.retention_authorized,
        reason_codes=projection.reason_codes,
        evidence_reference_ids=projection.evidence_reference_ids,
    )


def _projection_decision_values(
    projection_decision: NotificationReadModelProjectionDecision,
) -> _ProjectionDecisionValues:
    return _ProjectionDecisionValues(
        projection_decision.decision_id,
        projection_decision.authorization_scope,
        projection_decision.source_batch_decision.batch_id,
        _read_model_values(projection_decision.read_model),
        projection_decision.status,
        projection_decision.listing_references_preserved,
        projection_decision.per_item_outcomes_exposed,
        projection_decision.execution_authorized,
        projection_decision.provider_mapping_authorized,
        projection_decision.mutation_authorized,
        projection_decision.read_tracking_authorized,
        projection_decision.click_tracking_authorized,
        projection_decision.retention_authorized,
        projection_decision.reason_codes,
        projection_decision.evidence_reference_ids,
    )


__all__ = (
    "ND12_TASK_ID",
    "NotificationReadAudience",
    "NotificationDeliveryReadStatus",
    "NotificationDeliveryHistoryClassification",
    "NotificationReadProjectionStatus",
    "NotificationReadAuthorizationScope",
    "NotificationDeliveryHistoryEntry",
    "NotificationReadModel",
    "NotificationReadModelProjectionDecision",
    "project_notification_read_model",
)
