from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .attempt import (
    NotificationAttempt,
    NotificationAttemptPlanningDecision,
    NotificationAttemptPlanningStatus,
    NotificationProviderOutcomeAcceptanceDecision,
    NotificationProviderOutcomeAcceptanceStatus,
)
from .deduplication import (
    NotificationDeduplicationDecision,
    NotificationDeduplicationDecisionStatus,
)
from .delivery_plan import (
    NotificationDeliveryPlanDecision,
    NotificationDeliveryPlanDecisionStatus,
)
from .eligibility import NotificationChannelClass
from .outbox import (
    NotificationOutboxChannelIntent,
    NotificationOutboxCreationDecision,
    NotificationOutboxCreationStatus,
    NotificationOutboxItem,
)

ND11_TASK_ID = "ND-11-BATCH-PARTIAL-OUTCOME-SEMANTICS-20260716-019"

_REPLAYED_REQUEST_STAGES = {
    "ATTEMPT_CREATION",
    "PROVIDER_OUTCOME_RECORDING",
}

_ACCEPTED_DISPOSITIONS = {
    "CREATED",
    "REPLAYED",
    "DELIVERED",
}

_GENERIC_REASON_BY_DISPOSITION = {
    "CREATED": ("batch-item-created",),
    "REPLAYED": ("batch-item-replayed",),
    "SUPPRESSED": ("batch-item-suppressed",),
    "BLOCKED": ("batch-item-blocked",),
    "DELIVERED": ("batch-item-delivered",),
    "FAILED": ("batch-item-failed",),
    "RECONCILIATION_REQUIRED": ("batch-item-reconciliation-required",),
}

_BATCH_REASON_BY_STATUS = {
    "ALL_ACCEPTED": ("batch-all-accepted",),
    "PARTIAL_OUTCOME": ("batch-partial-outcome",),
    "ALL_BLOCKED_OR_FAILED": ("batch-all-blocked-or-failed",),
    "RECONCILIATION_REQUIRED": ("batch-reconciliation-required",),
}

_DEDUP_SAFE_ERROR_BY_STATUS = {
    "NEW_EFFECT": "NONE",
    "REPLAY_TERMINAL": "NONE",
    "REPLAY_PENDING": "NONE",
    "RECONCILIATION_REQUIRED": "AMBIGUOUS_RECONCILIATION",
    "IDEMPOTENCY_MISMATCH": "IDEMPOTENCY_BLOCKED",
    "MISSING_REQUIRED_IDEMPOTENCY": "IDEMPOTENCY_BLOCKED",
}

_DELIVERY_PLAN_SAFE_ERROR_BY_STATUS = {
    "PLANNED": "NONE",
    "BLOCKED_OUTBOX": "DELIVERY_PLAN_BLOCKED",
    "BLOCKED_CHANNEL_PLAN_AMBIGUOUS": "CHANNEL_PLAN_BLOCKED",
    "BLOCKED_NO_PUSH_CHANNEL": "CHANNEL_PLAN_BLOCKED",
}

_ATTEMPT_SAFE_ERROR_BY_STATUS = {
    "PLANNED": "NONE",
    "BLOCKED_DELIVERY_PLAN": "DELIVERY_PLAN_BLOCKED",
    "BLOCKED_CHANNEL_PLAN": "CHANNEL_PLAN_BLOCKED",
}

_PROVIDER_FAILURE_LIFECYCLE_STATUSES = {
    "PROVIDER_REJECTED",
    "PROVIDER_UNAVAILABLE",
    "RATE_OR_ACCESS_RESTRICTED",
    "MALFORMED_OR_UNUSABLE_PROVIDER_RESPONSE",
    "DELIVERY_FAILURE",
    "SUPPRESSED_OR_CANCELLED",
    "TARGET_UNAVAILABLE_OR_UNVERIFIED",
    "FAILED_RETRYABLE_AFTER_POLICY",
    "FAILED_NON_RETRYABLE",
}


def _require_text(value: object, field_name: str) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-blank string")
    return value


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


def _batch_item_result_values(result: "NotificationBatchItemResult") -> tuple[object, ...]:
    return (
        result.batch_item_id,
        result.authority,
        result.item_input,
        result.stage,
        result.source_decision_id,
        result.account_id,
        result.beacon_id,
        result.channel_class,
        result.outbox_item_id,
        result.attempt_id,
        result.safe_result_reference_id,
        result.safe_listing_reference_ids,
        result.disposition,
        result.safe_error_category,
        result.replayed,
        result.delivery_accepted,
        result.reconciliation_required,
        result.retry_policy_required,
        result.execution_authorized,
        result.provider_mapping_authorized,
        result.reason_codes,
        result.evidence_reference_ids,
    )


def _batch_decision_values(decision: "NotificationBatchDecision") -> tuple[object, ...]:
    return (
        decision.batch_id,
        decision.authority,
        decision.account_id,
        decision.item_inputs,
        decision.item_results,
        decision.status,
        decision.item_count,
        decision.accepted_count,
        decision.created_count,
        decision.replayed_count,
        decision.suppressed_count,
        decision.blocked_count,
        decision.delivered_count,
        decision.failed_count,
        decision.reconciliation_count,
        decision.retry_policy_required_count,
        decision.listing_references_preserved,
        decision.per_item_outcomes_exposed,
        decision.execution_authorized,
        decision.provider_mapping_authorized,
        decision.reason_codes,
        decision.evidence_reference_ids,
    )


def _source_event_from_outbox_creation(
    outbox_creation_decision: NotificationOutboxCreationDecision,
) -> object:
    eligibility_decision = outbox_creation_decision.eligibility_decision
    return eligibility_decision.source_intake_decision.source_event


def _source_event_from_delivery_plan(
    delivery_plan_decision: NotificationDeliveryPlanDecision,
) -> object:
    outbox_creation_decision = delivery_plan_decision.outbox_creation_decision
    eligibility_decision = outbox_creation_decision.eligibility_decision
    return eligibility_decision.source_intake_decision.source_event


def _source_event_from_attempt(
    attempt_planning_decision: NotificationAttemptPlanningDecision,
) -> object:
    delivery_plan_decision = attempt_planning_decision.delivery_plan_decision
    outbox_creation_decision = delivery_plan_decision.outbox_creation_decision
    eligibility_decision = outbox_creation_decision.eligibility_decision
    return eligibility_decision.source_intake_decision.source_event


def _listing_references_from_outbox_creation(
    outbox_creation_decision: NotificationOutboxCreationDecision,
) -> tuple[str, ...]:
    if outbox_creation_decision.outbox_item is not None:
        return outbox_creation_decision.outbox_item.safe_listing_reference_ids
    source_event = _source_event_from_outbox_creation(outbox_creation_decision)
    return source_event.safe_listing_reference_ids


def _listing_references_from_delivery_plan(
    delivery_plan_decision: NotificationDeliveryPlanDecision,
) -> tuple[str, ...]:
    if delivery_plan_decision.delivery_plan is not None:
        delivery_plan = delivery_plan_decision.delivery_plan
        return delivery_plan.outbox_item.safe_listing_reference_ids
    source_event = _source_event_from_delivery_plan(delivery_plan_decision)
    return source_event.safe_listing_reference_ids


def _listing_references_from_attempt(
    attempt_planning_decision: NotificationAttemptPlanningDecision,
) -> tuple[str, ...]:
    if attempt_planning_decision.attempt is not None:
        delivery_plan = attempt_planning_decision.delivery_plan_decision.delivery_plan
        return delivery_plan.outbox_item.safe_listing_reference_ids
    source_event = _source_event_from_attempt(attempt_planning_decision)
    return source_event.safe_listing_reference_ids


def _validate_provider_outbox_context(
    *,
    provider_outcome_decision: NotificationProviderOutcomeAcceptanceDecision,
    outbox_item_context: NotificationOutboxItem,
) -> NotificationAttempt:
    previous_attempt = provider_outcome_decision.previous_attempt
    resulting_attempt = provider_outcome_decision.resulting_attempt

    if type(outbox_item_context) is not NotificationOutboxItem:
        raise ValueError("outbox_item_context must be NotificationOutboxItem")

    if provider_outcome_decision.status is NotificationProviderOutcomeAcceptanceStatus.REPLAYED:
        if resulting_attempt is not previous_attempt:
            raise ValueError("replayed provider outcomes must preserve the original attempt")
    elif provider_outcome_decision.status in {
        NotificationProviderOutcomeAcceptanceStatus.ACCEPTED_DELIVERED,
        NotificationProviderOutcomeAcceptanceStatus.ACCEPTED_FAILURE,
        NotificationProviderOutcomeAcceptanceStatus.ACCEPTED_AMBIGUOUS,
    }:
        if resulting_attempt is None:
            raise ValueError("accepted provider outcomes must carry a resulting attempt")
        if resulting_attempt.attempt_id != previous_attempt.attempt_id:
            raise ValueError("accepted provider outcomes must preserve the attempt identity")
        if resulting_attempt.outbox_item_id != previous_attempt.outbox_item_id:
            raise ValueError("accepted provider outcomes must preserve the outbox identity")
        if resulting_attempt.account_id != previous_attempt.account_id:
            raise ValueError("accepted provider outcomes must preserve the account identity")
        if resulting_attempt.beacon_id != previous_attempt.beacon_id:
            raise ValueError("accepted provider outcomes must preserve the beacon identity")
        if resulting_attempt.channel_class is not previous_attempt.channel_class:
            raise ValueError("accepted provider outcomes must preserve the channel identity")
        if resulting_attempt.target_reference_id != previous_attempt.target_reference_id:
            raise ValueError("accepted provider outcomes must preserve the target identity")
        if resulting_attempt.correlation_id != previous_attempt.correlation_id:
            raise ValueError("accepted provider outcomes must preserve the correlation id")
        if resulting_attempt.causation_id != previous_attempt.causation_id:
            raise ValueError("accepted provider outcomes must preserve the causation id")
    elif resulting_attempt is not None:
        if resulting_attempt.attempt_id != previous_attempt.attempt_id:
            raise ValueError("rejected provider outcomes must preserve the attempt identity")

    if outbox_item_context.outbox_item_id != previous_attempt.outbox_item_id:
        raise ValueError("provider outcome context must match the attempt outbox id")
    if outbox_item_context.account_id != previous_attempt.account_id:
        raise ValueError("provider outcome context must match the attempt account")
    if outbox_item_context.beacon_id != previous_attempt.beacon_id:
        raise ValueError("provider outcome context must match the attempt beacon")
    if outbox_item_context.correlation_id != previous_attempt.correlation_id:
        raise ValueError("provider outcome context must match the attempt correlation")
    if outbox_item_context.causation_id != previous_attempt.causation_id:
        raise ValueError("provider outcome context must match the attempt causation")

    matched_intent = None
    for intent in outbox_item_context.channel_intents:
        if type(intent) is not NotificationOutboxChannelIntent:
            raise ValueError(
                "provider outcome context must contain NotificationOutboxChannelIntent"
            )
        if intent.channel_class is previous_attempt.channel_class:
            matched_intent = intent
    if matched_intent is None:
        raise ValueError("provider outcome attempt channel must exist in the outbox intents")
    if matched_intent.target_reference_id != previous_attempt.target_reference_id:
        raise ValueError("provider outcome target reference must match the outbox intent")

    return resulting_attempt or previous_attempt


class NotificationBatchAuthority(str, Enum):
    NOTIFICATION_DELIVERY_SERVER = "NOTIFICATION_DELIVERY_SERVER"


class NotificationBatchStage(str, Enum):
    DEDUPLICATION = "DEDUPLICATION"
    OUTBOX_CREATION = "OUTBOX_CREATION"
    DELIVERY_PLAN = "DELIVERY_PLAN"
    ATTEMPT_PLANNING = "ATTEMPT_PLANNING"
    PROVIDER_OUTCOME = "PROVIDER_OUTCOME"


class NotificationBatchDisposition(str, Enum):
    CREATED = "CREATED"
    REPLAYED = "REPLAYED"
    SUPPRESSED = "SUPPRESSED"
    BLOCKED = "BLOCKED"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"
    RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"


class NotificationBatchSafeErrorCategory(str, Enum):
    NONE = "NONE"
    ELIGIBILITY_BLOCKED = "ELIGIBILITY_BLOCKED"
    IDEMPOTENCY_BLOCKED = "IDEMPOTENCY_BLOCKED"
    DELIVERY_PLAN_BLOCKED = "DELIVERY_PLAN_BLOCKED"
    CHANNEL_PLAN_BLOCKED = "CHANNEL_PLAN_BLOCKED"
    PROVIDER_FAILURE = "PROVIDER_FAILURE"
    PROVIDER_OUTCOME_REJECTED = "PROVIDER_OUTCOME_REJECTED"
    AMBIGUOUS_RECONCILIATION = "AMBIGUOUS_RECONCILIATION"


class NotificationBatchDecisionStatus(str, Enum):
    ALL_ACCEPTED = "ALL_ACCEPTED"
    PARTIAL_OUTCOME = "PARTIAL_OUTCOME"
    ALL_BLOCKED_OR_FAILED = "ALL_BLOCKED_OR_FAILED"
    RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"


@dataclass(frozen=True, slots=True)
class NotificationBatchItemInput:
    batch_item_id: str
    source_decision: (
        NotificationDeduplicationDecision
        | NotificationOutboxCreationDecision
        | NotificationDeliveryPlanDecision
        | NotificationAttemptPlanningDecision
        | NotificationProviderOutcomeAcceptanceDecision
    )
    outbox_item_context: NotificationOutboxItem | None
    evidence_reference_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_text(self.batch_item_id, "batch_item_id")
        if type(self.source_decision) not in {
            NotificationDeduplicationDecision,
            NotificationOutboxCreationDecision,
            NotificationDeliveryPlanDecision,
            NotificationAttemptPlanningDecision,
            NotificationProviderOutcomeAcceptanceDecision,
        }:
            raise ValueError(
                "source_decision must be one of the approved Notification Delivery decisions"
            )
        if (
            self.outbox_item_context is not None
            and type(self.outbox_item_context) is not NotificationOutboxItem
        ):
            raise ValueError("outbox_item_context must be NotificationOutboxItem | None")
        _require_text_tuple(
            self.evidence_reference_ids, "evidence_reference_ids", allow_empty=True, unique=True
        )
        if type(self.source_decision) is NotificationProviderOutcomeAcceptanceDecision:
            if self.outbox_item_context is None:
                raise ValueError("provider outcome inputs require outbox_item_context")
        elif self.outbox_item_context is not None:
            raise ValueError("outbox_item_context is only allowed for provider outcome inputs")


def _dedup_item_result_fields(
    item_input: NotificationBatchItemInput,
    decision: NotificationDeduplicationDecision,
) -> tuple[object, ...]:
    request = decision.request
    if request.stage.value == "OUTBOX_CREATION":
        outbox_item_id = request.proposed_result_reference_id
        attempt_id = None
    elif request.stage.value in _REPLAYED_REQUEST_STAGES:
        outbox_item_id = None
        attempt_id = request.proposed_result_reference_id
    else:
        outbox_item_id = None
        attempt_id = None

    if decision.status is NotificationDeduplicationDecisionStatus.NEW_EFFECT:
        disposition = NotificationBatchDisposition.CREATED
        safe_result_reference_id = decision.resulting_record.protected_result_reference_id
        replayed = False
        reconciliation_required = decision.reconciliation_required
    elif decision.status in (
        NotificationDeduplicationDecisionStatus.REPLAY_TERMINAL,
        NotificationDeduplicationDecisionStatus.REPLAY_PENDING,
    ):
        disposition = NotificationBatchDisposition.REPLAYED
        safe_result_reference_id = decision.resulting_record.protected_result_reference_id
        replayed = True
        reconciliation_required = False
    elif decision.status is NotificationDeduplicationDecisionStatus.RECONCILIATION_REQUIRED:
        disposition = NotificationBatchDisposition.RECONCILIATION_REQUIRED
        safe_result_reference_id = decision.resulting_record.protected_result_reference_id
        replayed = True
        reconciliation_required = True
    elif decision.status is NotificationDeduplicationDecisionStatus.IDEMPOTENCY_MISMATCH:
        disposition = NotificationBatchDisposition.BLOCKED
        safe_result_reference_id = (
            decision.existing_record.protected_result_reference_id
            if decision.existing_record is not None
            else request.proposed_result_reference_id
        )
        replayed = False
        reconciliation_required = False
    else:
        disposition = NotificationBatchDisposition.BLOCKED
        safe_result_reference_id = request.proposed_result_reference_id
        replayed = False
        reconciliation_required = False

    return (
        item_input.batch_item_id,
        NotificationBatchAuthority.NOTIFICATION_DELIVERY_SERVER,
        item_input,
        NotificationBatchStage.DEDUPLICATION,
        decision.decision_id,
        request.account_id,
        request.beacon_id,
        request.channel_class,
        outbox_item_id,
        attempt_id,
        safe_result_reference_id,
        (),
        disposition,
        NotificationBatchSafeErrorCategory(_DEDUP_SAFE_ERROR_BY_STATUS[decision.status.name]),
        replayed,
        False,
        reconciliation_required,
        False,
        False,
        False,
        _GENERIC_REASON_BY_DISPOSITION[disposition.name],
        _first_occurrence_union(decision.evidence_reference_ids, item_input.evidence_reference_ids),
    )


def _outbox_item_result_fields(
    item_input: NotificationBatchItemInput,
    decision: NotificationOutboxCreationDecision,
) -> tuple[object, ...]:
    source_event = _source_event_from_outbox_creation(decision)
    if decision.status is NotificationOutboxCreationStatus.REPLAYED:
        if decision.outbox_item is None:
            raise ValueError("replayed outbox decisions must carry the original outbox item")
        outbox_item_id = decision.outbox_item.outbox_item_id
        safe_result_reference_id = decision.outbox_item.outbox_item_id
        safe_listing_reference_ids = decision.outbox_item.safe_listing_reference_ids
        account_id = decision.outbox_item.account_id
        beacon_id = decision.outbox_item.beacon_id
        disposition = NotificationBatchDisposition.REPLAYED
        replayed = True
        safe_error_category = NotificationBatchSafeErrorCategory.NONE
    elif decision.outbox_item is not None:
        outbox_item_id = decision.outbox_item.outbox_item_id
        safe_result_reference_id = decision.outbox_item.outbox_item_id
        safe_listing_reference_ids = decision.outbox_item.safe_listing_reference_ids
        account_id = decision.outbox_item.account_id
        beacon_id = decision.outbox_item.beacon_id
        disposition = NotificationBatchDisposition.CREATED
        replayed = decision.replayed
        safe_error_category = NotificationBatchSafeErrorCategory.NONE
    elif decision.status is NotificationOutboxCreationStatus.BLOCKED_ELIGIBILITY:
        outbox_item_id = None
        safe_result_reference_id = decision.decision_id
        safe_listing_reference_ids = source_event.safe_listing_reference_ids
        account_id = source_event.account_id
        beacon_id = source_event.beacon_id
        disposition = NotificationBatchDisposition.SUPPRESSED
        replayed = False
        safe_error_category = NotificationBatchSafeErrorCategory.ELIGIBILITY_BLOCKED
    else:
        outbox_item_id = None
        safe_result_reference_id = decision.decision_id
        safe_listing_reference_ids = source_event.safe_listing_reference_ids
        account_id = source_event.account_id
        beacon_id = source_event.beacon_id
        disposition = NotificationBatchDisposition.BLOCKED
        replayed = False
        safe_error_category = NotificationBatchSafeErrorCategory.IDEMPOTENCY_BLOCKED

    return (
        item_input.batch_item_id,
        NotificationBatchAuthority.NOTIFICATION_DELIVERY_SERVER,
        item_input,
        NotificationBatchStage.OUTBOX_CREATION,
        decision.decision_id,
        account_id,
        beacon_id,
        None,
        outbox_item_id,
        None,
        safe_result_reference_id,
        safe_listing_reference_ids,
        disposition,
        safe_error_category,
        replayed,
        False,
        False,
        False,
        False,
        False,
        _GENERIC_REASON_BY_DISPOSITION[disposition.name],
        _first_occurrence_union(decision.evidence_reference_ids, item_input.evidence_reference_ids),
    )


def _delivery_plan_item_result_fields(
    item_input: NotificationBatchItemInput,
    decision: NotificationDeliveryPlanDecision,
) -> tuple[object, ...]:
    source_event = _source_event_from_delivery_plan(decision)
    if decision.delivery_plan is not None:
        outbox_item_id = decision.delivery_plan.outbox_item.outbox_item_id
        safe_result_reference_id = decision.delivery_plan.delivery_plan_id
        safe_listing_reference_ids = decision.delivery_plan.outbox_item.safe_listing_reference_ids
        account_id = decision.delivery_plan.account_id
        beacon_id = decision.delivery_plan.beacon_id
        disposition = NotificationBatchDisposition.CREATED
        safe_error_category = NotificationBatchSafeErrorCategory.NONE
    elif decision.status is NotificationDeliveryPlanDecisionStatus.BLOCKED_OUTBOX:
        outbox_item_id = (
            decision.outbox_creation_decision.outbox_item.outbox_item_id
            if decision.outbox_creation_decision.outbox_item is not None
            else None
        )
        safe_result_reference_id = decision.decision_id
        safe_listing_reference_ids = _listing_references_from_delivery_plan(decision)
        account_id = source_event.account_id
        beacon_id = source_event.beacon_id
        disposition = NotificationBatchDisposition.BLOCKED
        safe_error_category = NotificationBatchSafeErrorCategory.DELIVERY_PLAN_BLOCKED
    else:
        outbox_item_id = (
            decision.outbox_creation_decision.outbox_item.outbox_item_id
            if decision.outbox_creation_decision.outbox_item is not None
            else None
        )
        safe_result_reference_id = decision.decision_id
        safe_listing_reference_ids = _listing_references_from_delivery_plan(decision)
        account_id = source_event.account_id
        beacon_id = source_event.beacon_id
        disposition = NotificationBatchDisposition.BLOCKED
        safe_error_category = NotificationBatchSafeErrorCategory.CHANNEL_PLAN_BLOCKED

    return (
        item_input.batch_item_id,
        NotificationBatchAuthority.NOTIFICATION_DELIVERY_SERVER,
        item_input,
        NotificationBatchStage.DELIVERY_PLAN,
        decision.decision_id,
        account_id,
        beacon_id,
        None,
        outbox_item_id,
        None,
        safe_result_reference_id,
        safe_listing_reference_ids,
        disposition,
        safe_error_category,
        False,
        False,
        False,
        False,
        False,
        False,
        _GENERIC_REASON_BY_DISPOSITION[disposition.name],
        _first_occurrence_union(decision.evidence_reference_ids, item_input.evidence_reference_ids),
    )


def _attempt_item_result_fields(
    item_input: NotificationBatchItemInput,
    decision: NotificationAttemptPlanningDecision,
) -> tuple[object, ...]:
    source_event = _source_event_from_attempt(decision)
    if decision.attempt is not None:
        attempt = decision.attempt
        outbox_item_id = attempt.outbox_item_id
        safe_result_reference_id = attempt.attempt_id
        safe_listing_reference_ids = _listing_references_from_attempt(decision)
        account_id = attempt.account_id
        beacon_id = attempt.beacon_id
        channel_class = attempt.channel_class
        attempt_id = attempt.attempt_id
        disposition = NotificationBatchDisposition.CREATED
        safe_error_category = NotificationBatchSafeErrorCategory.NONE
    elif decision.status is NotificationAttemptPlanningStatus.BLOCKED_DELIVERY_PLAN:
        outbox_item_id = (
            decision.delivery_plan_decision.delivery_plan.outbox_item.outbox_item_id
            if decision.delivery_plan_decision.delivery_plan is not None
            else None
        )
        safe_result_reference_id = decision.decision_id
        safe_listing_reference_ids = _listing_references_from_attempt(decision)
        account_id = source_event.account_id
        beacon_id = source_event.beacon_id
        channel_class = decision.channel_class
        attempt_id = None
        disposition = NotificationBatchDisposition.BLOCKED
        safe_error_category = NotificationBatchSafeErrorCategory.DELIVERY_PLAN_BLOCKED
    else:
        outbox_item_id = (
            decision.delivery_plan_decision.delivery_plan.outbox_item.outbox_item_id
            if decision.delivery_plan_decision.delivery_plan is not None
            else None
        )
        safe_result_reference_id = decision.decision_id
        safe_listing_reference_ids = _listing_references_from_attempt(decision)
        account_id = source_event.account_id
        beacon_id = source_event.beacon_id
        channel_class = decision.channel_class
        attempt_id = None
        disposition = NotificationBatchDisposition.BLOCKED
        safe_error_category = NotificationBatchSafeErrorCategory.CHANNEL_PLAN_BLOCKED

    return (
        item_input.batch_item_id,
        NotificationBatchAuthority.NOTIFICATION_DELIVERY_SERVER,
        item_input,
        NotificationBatchStage.ATTEMPT_PLANNING,
        decision.decision_id,
        account_id,
        beacon_id,
        channel_class,
        outbox_item_id,
        attempt_id,
        safe_result_reference_id,
        safe_listing_reference_ids,
        disposition,
        safe_error_category,
        False,
        False,
        False,
        False,
        False,
        False,
        _GENERIC_REASON_BY_DISPOSITION[disposition.name],
        _first_occurrence_union(decision.evidence_reference_ids, item_input.evidence_reference_ids),
    )


def _provider_outcome_item_result_fields(
    item_input: NotificationBatchItemInput,
    decision: NotificationProviderOutcomeAcceptanceDecision,
) -> tuple[object, ...]:
    outbox_item_context = item_input.outbox_item_context
    if outbox_item_context is None:
        raise ValueError("provider outcome inputs require outbox_item_context")
    effective_attempt = _validate_provider_outbox_context(
        provider_outcome_decision=decision,
        outbox_item_context=outbox_item_context,
    )

    if decision.status is NotificationProviderOutcomeAcceptanceStatus.REPLAYED:
        disposition = NotificationBatchDisposition.REPLAYED
        replayed = True
        delivery_accepted = decision.delivery_accepted
        reconciliation_required = decision.reconciliation_required
    elif decision.status is NotificationProviderOutcomeAcceptanceStatus.ACCEPTED_DELIVERED:
        disposition = NotificationBatchDisposition.DELIVERED
        replayed = False
        delivery_accepted = True
        reconciliation_required = False
    elif decision.status is NotificationProviderOutcomeAcceptanceStatus.ACCEPTED_FAILURE:
        disposition = NotificationBatchDisposition.FAILED
        replayed = False
        delivery_accepted = False
        reconciliation_required = False
    elif decision.status is NotificationProviderOutcomeAcceptanceStatus.ACCEPTED_AMBIGUOUS:
        disposition = NotificationBatchDisposition.RECONCILIATION_REQUIRED
        replayed = False
        delivery_accepted = False
        reconciliation_required = True
    else:
        disposition = NotificationBatchDisposition.BLOCKED
        replayed = False
        delivery_accepted = False
        reconciliation_required = False

    if disposition is NotificationBatchDisposition.DELIVERED:
        safe_error_category = NotificationBatchSafeErrorCategory.NONE
    elif disposition is NotificationBatchDisposition.FAILED:
        safe_error_category = NotificationBatchSafeErrorCategory.PROVIDER_FAILURE
    elif disposition is NotificationBatchDisposition.RECONCILIATION_REQUIRED:
        safe_error_category = NotificationBatchSafeErrorCategory.AMBIGUOUS_RECONCILIATION
    elif disposition is NotificationBatchDisposition.REPLAYED:
        replayed_failure = (
            decision.provider_outcome.outcome_class.value
            in _PROVIDER_FAILURE_LIFECYCLE_STATUSES
        )
        if delivery_accepted:
            safe_error_category = NotificationBatchSafeErrorCategory.NONE
        elif reconciliation_required:
            safe_error_category = NotificationBatchSafeErrorCategory.AMBIGUOUS_RECONCILIATION
        elif replayed_failure:
            safe_error_category = NotificationBatchSafeErrorCategory.PROVIDER_FAILURE
        elif effective_attempt.lifecycle_status.value in _PROVIDER_FAILURE_LIFECYCLE_STATUSES:
            safe_error_category = NotificationBatchSafeErrorCategory.PROVIDER_FAILURE
        elif effective_attempt.lifecycle_status.value in {
            "DISPATCH_AMBIGUOUS",
            "DELIVERY_AMBIGUOUS",
            "RECONCILIATION_REQUIRED",
        }:
            safe_error_category = NotificationBatchSafeErrorCategory.AMBIGUOUS_RECONCILIATION
        else:
            safe_error_category = NotificationBatchSafeErrorCategory.NONE
    else:
        safe_error_category = NotificationBatchSafeErrorCategory.PROVIDER_OUTCOME_REJECTED

    retry_policy_required = (
        disposition
        in {
            NotificationBatchDisposition.FAILED,
            NotificationBatchDisposition.REPLAYED,
        }
        and delivery_accepted is False
        and reconciliation_required is False
        and (
            effective_attempt.lifecycle_status.value
            in _PROVIDER_FAILURE_LIFECYCLE_STATUSES
            or (
                disposition is NotificationBatchDisposition.REPLAYED
                and decision.provider_outcome.outcome_class.value
                in _PROVIDER_FAILURE_LIFECYCLE_STATUSES
            )
        )
    )

    return (
        item_input.batch_item_id,
        NotificationBatchAuthority.NOTIFICATION_DELIVERY_SERVER,
        item_input,
        NotificationBatchStage.PROVIDER_OUTCOME,
        decision.decision_id,
        effective_attempt.account_id,
        effective_attempt.beacon_id,
        effective_attempt.channel_class,
        effective_attempt.outbox_item_id,
        effective_attempt.attempt_id,
        effective_attempt.attempt_id,
        outbox_item_context.safe_listing_reference_ids,
        disposition,
        safe_error_category,
        replayed,
        delivery_accepted,
        reconciliation_required,
        retry_policy_required,
        False,
        False,
        _GENERIC_REASON_BY_DISPOSITION[disposition.name],
        _first_occurrence_union(
            decision.evidence_reference_ids,
            outbox_item_context.evidence_reference_ids,
            item_input.evidence_reference_ids,
        ),
    )


def _project_notification_batch_item_result_fields(
    item_input: NotificationBatchItemInput,
) -> tuple[object, ...]:
    source_decision = item_input.source_decision
    if type(source_decision) is NotificationDeduplicationDecision:
        return _dedup_item_result_fields(item_input, source_decision)
    if type(source_decision) is NotificationOutboxCreationDecision:
        return _outbox_item_result_fields(item_input, source_decision)
    if type(source_decision) is NotificationDeliveryPlanDecision:
        return _delivery_plan_item_result_fields(item_input, source_decision)
    if type(source_decision) is NotificationAttemptPlanningDecision:
        return _attempt_item_result_fields(item_input, source_decision)
    return _provider_outcome_item_result_fields(item_input, source_decision)


@dataclass(frozen=True, slots=True)
class NotificationBatchItemResult:
    batch_item_id: str
    authority: NotificationBatchAuthority
    item_input: NotificationBatchItemInput
    stage: NotificationBatchStage
    source_decision_id: str
    account_id: str
    beacon_id: str | None
    channel_class: NotificationChannelClass | None
    outbox_item_id: str | None
    attempt_id: str | None
    safe_result_reference_id: str
    safe_listing_reference_ids: tuple[str, ...]
    disposition: NotificationBatchDisposition
    safe_error_category: NotificationBatchSafeErrorCategory
    replayed: bool
    delivery_accepted: bool
    reconciliation_required: bool
    retry_policy_required: bool
    execution_authorized: bool
    provider_mapping_authorized: bool
    reason_codes: tuple[str, ...]
    evidence_reference_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if type(self.item_input) is not NotificationBatchItemInput:
            raise ValueError("item_input must be NotificationBatchItemInput")
        expected = _project_notification_batch_item_result_fields(self.item_input)
        actual = _batch_item_result_values(self)
        if actual != expected:
            raise ValueError(
                "notification batch item results must be canonically derived from the input"
            )


def _project_notification_batch_decision_fields(
    *,
    batch_id: str,
    item_inputs: tuple[NotificationBatchItemInput, ...],
    item_results: tuple[NotificationBatchItemResult, ...],
    evidence_reference_ids: tuple[str, ...],
) -> tuple[object, ...]:
    if not item_inputs:
        raise ValueError("batch must not be empty")
    if len(item_inputs) != len(item_results):
        raise ValueError("item_results must align with item_inputs")

    seen_batch_item_ids: set[str] = set()
    seen_source_decision_ids: set[str] = set()
    account_ids: set[str] = set()
    for item_input, item_result in zip(item_inputs, item_results):
        if type(item_input) is not NotificationBatchItemInput:
            raise ValueError("item_inputs must contain NotificationBatchItemInput")
        if type(item_result) is not NotificationBatchItemResult:
            raise ValueError("item_results must contain NotificationBatchItemResult")
        if item_input.batch_item_id in seen_batch_item_ids:
            raise ValueError("duplicate batch_item_id is not allowed")
        seen_batch_item_ids.add(item_input.batch_item_id)
        source_decision_id = item_input.source_decision.decision_id
        if source_decision_id in seen_source_decision_ids:
            raise ValueError("duplicate source decision identity is not allowed")
        seen_source_decision_ids.add(source_decision_id)
        if _batch_item_result_values(item_result) != _project_notification_batch_item_result_fields(
            item_input
        ):
            raise ValueError("item results must preserve canonical projection order and values")
        account_ids.add(item_result.account_id)

    if len(account_ids) != 1:
        raise ValueError("mixed accounts are not allowed")

    accepted_count = sum(
        item_result.disposition.name in _ACCEPTED_DISPOSITIONS for item_result in item_results
    )
    created_count = sum(
        item_result.disposition is NotificationBatchDisposition.CREATED
        for item_result in item_results
    )
    replayed_count = sum(
        item_result.disposition is NotificationBatchDisposition.REPLAYED
        for item_result in item_results
    )
    suppressed_count = sum(
        item_result.disposition is NotificationBatchDisposition.SUPPRESSED
        for item_result in item_results
    )
    blocked_count = sum(
        item_result.disposition is NotificationBatchDisposition.BLOCKED
        for item_result in item_results
    )
    delivered_count = sum(
        item_result.disposition is NotificationBatchDisposition.DELIVERED
        for item_result in item_results
    )
    failed_count = sum(
        item_result.disposition is NotificationBatchDisposition.FAILED
        for item_result in item_results
    )
    reconciliation_count = sum(
        item_result.disposition is NotificationBatchDisposition.RECONCILIATION_REQUIRED
        for item_result in item_results
    )
    retry_policy_required_count = sum(
        item_result.retry_policy_required for item_result in item_results
    )

    if reconciliation_count:
        status = NotificationBatchDecisionStatus.RECONCILIATION_REQUIRED
    elif accepted_count == len(item_inputs):
        status = NotificationBatchDecisionStatus.ALL_ACCEPTED
    elif accepted_count > 0:
        status = NotificationBatchDecisionStatus.PARTIAL_OUTCOME
    else:
        status = NotificationBatchDecisionStatus.ALL_BLOCKED_OR_FAILED

    return (
        batch_id,
        NotificationBatchAuthority.NOTIFICATION_DELIVERY_SERVER,
        item_results[0].account_id,
        item_inputs,
        item_results,
        status,
        len(item_inputs),
        accepted_count,
        created_count,
        replayed_count,
        suppressed_count,
        blocked_count,
        delivered_count,
        failed_count,
        reconciliation_count,
        retry_policy_required_count,
        True,
        True,
        False,
        False,
        _BATCH_REASON_BY_STATUS[status.name],
        _first_occurrence_union(
            *(item_result.evidence_reference_ids for item_result in item_results),
            evidence_reference_ids,
        ),
    )


@dataclass(frozen=True, slots=True)
class NotificationBatchDecision:
    batch_id: str
    authority: NotificationBatchAuthority
    account_id: str
    item_inputs: tuple[NotificationBatchItemInput, ...]
    item_results: tuple[NotificationBatchItemResult, ...]
    status: NotificationBatchDecisionStatus
    item_count: int
    accepted_count: int
    created_count: int
    replayed_count: int
    suppressed_count: int
    blocked_count: int
    delivered_count: int
    failed_count: int
    reconciliation_count: int
    retry_policy_required_count: int
    listing_references_preserved: bool
    per_item_outcomes_exposed: bool
    execution_authorized: bool
    provider_mapping_authorized: bool
    reason_codes: tuple[str, ...]
    evidence_reference_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_text(self.batch_id, "batch_id")
        _require_exact_enum(self.authority, NotificationBatchAuthority, "authority")
        _require_text(self.account_id, "account_id")
        if type(self.item_inputs) is not tuple or not self.item_inputs:
            raise ValueError("item_inputs must be a non-empty tuple")
        if type(self.item_results) is not tuple:
            raise ValueError("item_results must be a tuple")
        for item_input in self.item_inputs:
            if type(item_input) is not NotificationBatchItemInput:
                raise ValueError("item_inputs must contain NotificationBatchItemInput")
        for item_result in self.item_results:
            if type(item_result) is not NotificationBatchItemResult:
                raise ValueError("item_results must contain NotificationBatchItemResult")
        if type(self.status) is not NotificationBatchDecisionStatus:
            raise ValueError("status must be NotificationBatchDecisionStatus")
        if type(self.item_count) is not int or self.item_count < 0:
            raise ValueError("item_count must be a non-negative int")
        if type(self.accepted_count) is not int or self.accepted_count < 0:
            raise ValueError("accepted_count must be a non-negative int")
        if type(self.created_count) is not int or self.created_count < 0:
            raise ValueError("created_count must be a non-negative int")
        if type(self.replayed_count) is not int or self.replayed_count < 0:
            raise ValueError("replayed_count must be a non-negative int")
        if type(self.suppressed_count) is not int or self.suppressed_count < 0:
            raise ValueError("suppressed_count must be a non-negative int")
        if type(self.blocked_count) is not int or self.blocked_count < 0:
            raise ValueError("blocked_count must be a non-negative int")
        if type(self.delivered_count) is not int or self.delivered_count < 0:
            raise ValueError("delivered_count must be a non-negative int")
        if type(self.failed_count) is not int or self.failed_count < 0:
            raise ValueError("failed_count must be a non-negative int")
        if type(self.reconciliation_count) is not int or self.reconciliation_count < 0:
            raise ValueError("reconciliation_count must be a non-negative int")
        if (
            type(self.retry_policy_required_count) is not int
            or self.retry_policy_required_count < 0
        ):
            raise ValueError("retry_policy_required_count must be a non-negative int")
        _require_bool(self.listing_references_preserved, "listing_references_preserved")
        _require_bool(self.per_item_outcomes_exposed, "per_item_outcomes_exposed")
        _require_bool(self.execution_authorized, "execution_authorized")
        _require_bool(self.provider_mapping_authorized, "provider_mapping_authorized")
        _require_text_tuple(self.reason_codes, "reason_codes", allow_empty=False, unique=True)
        _require_text_tuple(
            self.evidence_reference_ids, "evidence_reference_ids", allow_empty=True, unique=True
        )
        if _batch_decision_values(self) != _project_notification_batch_decision_fields(
            batch_id=self.batch_id,
            item_inputs=self.item_inputs,
            item_results=self.item_results,
            evidence_reference_ids=self.evidence_reference_ids,
        ):
            raise ValueError("notification batch decisions must be canonically projected")


def project_notification_batch_outcomes(
    *,
    batch_id: str,
    item_inputs: tuple[NotificationBatchItemInput, ...],
    evidence_reference_ids: tuple[str, ...],
) -> NotificationBatchDecision:
    _require_text(batch_id, "batch_id")
    _require_text_tuple(
        evidence_reference_ids, "evidence_reference_ids", allow_empty=True, unique=True
    )
    if type(item_inputs) is not tuple or not item_inputs:
        raise ValueError("item_inputs must be a non-empty tuple")
    for item_input in item_inputs:
        if type(item_input) is not NotificationBatchItemInput:
            raise ValueError("item_inputs must contain NotificationBatchItemInput")

    item_results = tuple(
        NotificationBatchItemResult(**_item_result_kwargs(item_input)) for item_input in item_inputs
    )
    decision_fields = _project_notification_batch_decision_fields(
        batch_id=batch_id,
        item_inputs=item_inputs,
        item_results=item_results,
        evidence_reference_ids=evidence_reference_ids,
    )
    return NotificationBatchDecision(
        batch_id=decision_fields[0],
        authority=decision_fields[1],
        account_id=decision_fields[2],
        item_inputs=decision_fields[3],
        item_results=decision_fields[4],
        status=decision_fields[5],
        item_count=decision_fields[6],
        accepted_count=decision_fields[7],
        created_count=decision_fields[8],
        replayed_count=decision_fields[9],
        suppressed_count=decision_fields[10],
        blocked_count=decision_fields[11],
        delivered_count=decision_fields[12],
        failed_count=decision_fields[13],
        reconciliation_count=decision_fields[14],
        retry_policy_required_count=decision_fields[15],
        listing_references_preserved=decision_fields[16],
        per_item_outcomes_exposed=decision_fields[17],
        execution_authorized=decision_fields[18],
        provider_mapping_authorized=decision_fields[19],
        reason_codes=decision_fields[20],
        evidence_reference_ids=decision_fields[21],
    )


def _item_result_kwargs(item_input: NotificationBatchItemInput) -> dict[str, object]:
    values = _project_notification_batch_item_result_fields(item_input)
    return {
        "batch_item_id": values[0],
        "authority": values[1],
        "item_input": values[2],
        "stage": values[3],
        "source_decision_id": values[4],
        "account_id": values[5],
        "beacon_id": values[6],
        "channel_class": values[7],
        "outbox_item_id": values[8],
        "attempt_id": values[9],
        "safe_result_reference_id": values[10],
        "safe_listing_reference_ids": values[11],
        "disposition": values[12],
        "safe_error_category": values[13],
        "replayed": values[14],
        "delivery_accepted": values[15],
        "reconciliation_required": values[16],
        "retry_policy_required": values[17],
        "execution_authorized": values[18],
        "provider_mapping_authorized": values[19],
        "reason_codes": values[20],
        "evidence_reference_ids": values[21],
    }


__all__ = (
    "ND11_TASK_ID",
    "NotificationBatchAuthority",
    "NotificationBatchStage",
    "NotificationBatchDisposition",
    "NotificationBatchSafeErrorCategory",
    "NotificationBatchDecisionStatus",
    "NotificationBatchItemInput",
    "NotificationBatchItemResult",
    "NotificationBatchDecision",
    "project_notification_batch_outcomes",
)
