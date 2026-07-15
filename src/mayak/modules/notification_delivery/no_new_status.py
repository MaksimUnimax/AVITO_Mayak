from __future__ import annotations

from dataclasses import dataclass as _dataclass
from enum import Enum as _Enum

from .delivery_plan import (
    NotificationDeliveryPlanDecision as _NotificationDeliveryPlanDecision,
)
from .delivery_plan import (
    NotificationDeliveryPlanDecisionStatus as _NotificationDeliveryPlanDecisionStatus,
)
from .eligibility import (
    NO_NEW_MINIMUM_FREQUENCY_MINUTES as _NO_NEW_MINIMUM_FREQUENCY_MINUTES,
)
from .eligibility import (
    NotificationEligibilityDecision as _NotificationEligibilityDecision,
)
from .eligibility import (
    NotificationEligibilityStatus as _NotificationEligibilityStatus,
)
from .source_intake import (
    NotificationSourceFamily as _NotificationSourceFamily,
)
from .source_intake import (
    NotificationSourceIntakeStatus as _NotificationSourceIntakeStatus,
)
from .source_intake import (
    NotificationSourceProducer as _NotificationSourceProducer,
)

ND08_TASK_ID = "ND-08-NO-NEW-STATUS-POLICY-SEMANTICS-20260716-012"

_ALLOWED_REASON_CODES = {
    "no-new-status-push-eligible",
    "no-new-status-preference-disabled",
    "no-new-status-frequency-below-minimum",
    "no-new-status-minimum-frequency-not-elapsed",
    "no-new-status-no-eligible-push-channel",
    "no-new-status-eligibility-blocked",
    "no-new-status-minimum-frequency-ambiguous",
    "no-new-status-channel-plan-blocked",
}

_SOURCE_ACCEPTED_STATUS_ONLY_REASON_CODES = ("source-accepted-status-only-no-new",)
_ELIGIBILITY_NO_NEW_PREFERENCE_DISABLED_REASON_CODES = (
    "eligibility-no-new-preference-disabled",
)
_ELIGIBILITY_NO_NEW_FREQUENCY_BELOW_MINIMUM_REASON_CODES = (
    "eligibility-no-new-frequency-below-minimum",
)
_ELIGIBILITY_ELIGIBLE_REASON_CODES = ("eligibility-eligible",)
_ELIGIBILITY_NO_ELIGIBLE_PUSH_CHANNEL_REASON_CODES = (
    "eligibility-no-eligible-push-channel",
)


class NotificationNoNewStatusAuthority(str, _Enum):
    NOTIFICATION_DELIVERY_SERVER = "NOTIFICATION_DELIVERY_SERVER"


class NotificationNoNewMinimumFrequencyGateStatus(str, _Enum):
    NOT_APPLICABLE = "NOT_APPLICABLE"
    NO_PRIOR_NOTIFICATION = "NO_PRIOR_NOTIFICATION"
    MINIMUM_FREQUENCY_ELAPSED = "MINIMUM_FREQUENCY_ELAPSED"
    MINIMUM_FREQUENCY_NOT_ELAPSED = "MINIMUM_FREQUENCY_NOT_ELAPSED"
    AMBIGUOUS = "AMBIGUOUS"


class NotificationNoNewStatusDecisionStatus(str, _Enum):
    PUSH_STATUS_ELIGIBLE = "PUSH_STATUS_ELIGIBLE"
    READ_MODEL_ONLY_PREFERENCE_DISABLED = "READ_MODEL_ONLY_PREFERENCE_DISABLED"
    READ_MODEL_ONLY_FREQUENCY_BELOW_MINIMUM = "READ_MODEL_ONLY_FREQUENCY_BELOW_MINIMUM"
    READ_MODEL_ONLY_MINIMUM_FREQUENCY_NOT_ELAPSED = "READ_MODEL_ONLY_MINIMUM_FREQUENCY_NOT_ELAPSED"
    READ_MODEL_ONLY_NO_ELIGIBLE_PUSH_CHANNEL = "READ_MODEL_ONLY_NO_ELIGIBLE_PUSH_CHANNEL"
    BLOCKED_ELIGIBILITY = "BLOCKED_ELIGIBILITY"
    BLOCKED_MINIMUM_FREQUENCY_AMBIGUOUS = "BLOCKED_MINIMUM_FREQUENCY_AMBIGUOUS"
    BLOCKED_CHANNEL_PLAN = "BLOCKED_CHANNEL_PLAN"


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


def _require_positive_int(value: object, field_name: str) -> int:
    if type(value) is not int or value <= 0:
        raise ValueError(f"{field_name} must be a positive int")
    return value


def _require_exact_enum(value: object, enum_type: type[_Enum], field_name: str) -> _Enum:
    if type(value) is not enum_type:
        raise ValueError(f"{field_name} must be {enum_type.__name__}")
    return value


def _require_text_tuple(
    value: object,
    field_name: str,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not allow_empty and not value:
        raise ValueError(f"{field_name} must not be empty")
    return tuple(_require_text(item, field_name) for item in value)


def _first_occurrence_union(*tuples: tuple[str, ...]) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []
    for items in tuples:
        for item in items:
            if item not in seen:
                seen.add(item)
                ordered.append(item)
    return tuple(ordered)


def _reason_code_for_status(status: NotificationNoNewStatusDecisionStatus) -> str:
    return {
        NotificationNoNewStatusDecisionStatus.PUSH_STATUS_ELIGIBLE: "no-new-status-push-eligible",
        NotificationNoNewStatusDecisionStatus.READ_MODEL_ONLY_PREFERENCE_DISABLED: (
            "no-new-status-preference-disabled"
        ),
        NotificationNoNewStatusDecisionStatus.READ_MODEL_ONLY_FREQUENCY_BELOW_MINIMUM: (
            "no-new-status-frequency-below-minimum"
        ),
        NotificationNoNewStatusDecisionStatus.READ_MODEL_ONLY_MINIMUM_FREQUENCY_NOT_ELAPSED: (
            "no-new-status-minimum-frequency-not-elapsed"
        ),
        NotificationNoNewStatusDecisionStatus.READ_MODEL_ONLY_NO_ELIGIBLE_PUSH_CHANNEL: (
            "no-new-status-no-eligible-push-channel"
        ),
        NotificationNoNewStatusDecisionStatus.BLOCKED_ELIGIBILITY: (
            "no-new-status-eligibility-blocked"
        ),
        NotificationNoNewStatusDecisionStatus.BLOCKED_MINIMUM_FREQUENCY_AMBIGUOUS: (
            "no-new-status-minimum-frequency-ambiguous"
        ),
        NotificationNoNewStatusDecisionStatus.BLOCKED_CHANNEL_PLAN: (
            "no-new-status-channel-plan-blocked"
        ),
    }[status]


def _require_reason_codes(value: object, field_name: str) -> tuple[str, ...]:
    reason_codes = _require_text_tuple(value, field_name, allow_empty=False)
    if len(reason_codes) != 1 or reason_codes[0] not in _ALLOWED_REASON_CODES:
        raise ValueError(f"{field_name} contains unsupported reason codes")
    return reason_codes


def _require_evidence_reference_ids(value: object, field_name: str) -> tuple[str, ...]:
    return _require_text_tuple(value, field_name, allow_empty=True)


def _validate_context_gate_consistency(
    *,
    status_preference_enabled: bool,
    configured_status_frequency_minutes: int | None,
    minimum_frequency_gate_status: NotificationNoNewMinimumFrequencyGateStatus,
    last_no_new_status_notification_reference_id: str | None,
) -> None:
    if not status_preference_enabled:
        if configured_status_frequency_minutes is not None:
            raise ValueError("disabled no-new preference must not carry a frequency")
        if (
            minimum_frequency_gate_status
            is not NotificationNoNewMinimumFrequencyGateStatus.NOT_APPLICABLE
        ):
            raise ValueError("disabled no-new preference must use NOT_APPLICABLE gate evidence")
        return

    if configured_status_frequency_minutes is None:
        raise ValueError("enabled no-new preference requires a supplied frequency")

    if configured_status_frequency_minutes < _NO_NEW_MINIMUM_FREQUENCY_MINUTES:
        if (
            minimum_frequency_gate_status
            is not NotificationNoNewMinimumFrequencyGateStatus.NOT_APPLICABLE
        ):
            raise ValueError("below-minimum frequency must use NOT_APPLICABLE gate evidence")
        return

    if minimum_frequency_gate_status is NotificationNoNewMinimumFrequencyGateStatus.NOT_APPLICABLE:
        raise ValueError("enabled minimum-frequency evidence must not be NOT_APPLICABLE")

    if (
        minimum_frequency_gate_status
        is NotificationNoNewMinimumFrequencyGateStatus.NO_PRIOR_NOTIFICATION
    ):
        if last_no_new_status_notification_reference_id is not None:
            raise ValueError(
                "no-prior-notification evidence must not carry a last notification ref"
            )
        return

    if minimum_frequency_gate_status in (
        NotificationNoNewMinimumFrequencyGateStatus.MINIMUM_FREQUENCY_ELAPSED,
        NotificationNoNewMinimumFrequencyGateStatus.MINIMUM_FREQUENCY_NOT_ELAPSED,
        NotificationNoNewMinimumFrequencyGateStatus.AMBIGUOUS,
    ):
        if last_no_new_status_notification_reference_id is None:
            raise ValueError("frequency evidence requires a last notification ref")
        return

    raise ValueError("unsupported minimum frequency gate evidence")


@_dataclass(frozen=True, slots=True)
class NotificationNoNewStatusPolicyContext:
    account_id: str
    beacon_id: str
    last_successful_scan_reference_id: str
    no_new_status_fact_reference_id: str
    configured_scan_interval_reference_id: str
    status_preference_enabled: bool
    configured_status_frequency_minutes: int | None
    last_no_new_status_notification_reference_id: str | None
    minimum_frequency_gate_status: NotificationNoNewMinimumFrequencyGateStatus
    evidence_reference_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_text(self.account_id, "account_id")
        _require_text(self.beacon_id, "beacon_id")
        _require_text(self.last_successful_scan_reference_id, "last_successful_scan_reference_id")
        _require_text(self.no_new_status_fact_reference_id, "no_new_status_fact_reference_id")
        _require_text(
            self.configured_scan_interval_reference_id,
            "configured_scan_interval_reference_id",
        )
        _require_bool(self.status_preference_enabled, "status_preference_enabled")
        if self.configured_status_frequency_minutes is not None:
            _require_positive_int(
                self.configured_status_frequency_minutes,
                "configured_status_frequency_minutes",
            )
        _require_exact_enum(
            self.minimum_frequency_gate_status,
            NotificationNoNewMinimumFrequencyGateStatus,
            "minimum_frequency_gate_status",
        )
        _require_optional_text(
            self.last_no_new_status_notification_reference_id,
            "last_no_new_status_notification_reference_id",
        )
        _require_evidence_reference_ids(self.evidence_reference_ids, "evidence_reference_ids")
        _validate_context_gate_consistency(
            status_preference_enabled=self.status_preference_enabled,
            configured_status_frequency_minutes=self.configured_status_frequency_minutes,
            minimum_frequency_gate_status=self.minimum_frequency_gate_status,
            last_no_new_status_notification_reference_id=self.last_no_new_status_notification_reference_id,
        )


@_dataclass(frozen=True, slots=True)
class NotificationNoNewStatusPolicyDecision:
    decision_id: str
    authority: NotificationNoNewStatusAuthority
    eligibility_decision: _NotificationEligibilityDecision
    delivery_plan_decision: _NotificationDeliveryPlanDecision | None
    context: NotificationNoNewStatusPolicyContext
    status: NotificationNoNewStatusDecisionStatus
    status_read_model_eligible: bool
    push_status_work_eligible: bool
    delivery_attempt_authorized: bool
    provider_mapping_authorized: bool
    reason_codes: tuple[str, ...]
    evidence_reference_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_text(self.decision_id, "decision_id")
        _require_exact_enum(self.authority, NotificationNoNewStatusAuthority, "authority")
        if type(self.eligibility_decision) is not _NotificationEligibilityDecision:
            raise ValueError("eligibility_decision must be _NotificationEligibilityDecision")
        if self.delivery_plan_decision is not None and (
            type(self.delivery_plan_decision) is not _NotificationDeliveryPlanDecision
        ):
            raise ValueError(
                "delivery_plan_decision must be _NotificationDeliveryPlanDecision | None"
            )
        if type(self.context) is not NotificationNoNewStatusPolicyContext:
            raise ValueError("context must be NotificationNoNewStatusPolicyContext")
        _require_exact_enum(self.status, NotificationNoNewStatusDecisionStatus, "status")
        _require_bool(self.status_read_model_eligible, "status_read_model_eligible")
        _require_bool(self.push_status_work_eligible, "push_status_work_eligible")
        _require_bool(self.delivery_attempt_authorized, "delivery_attempt_authorized")
        _require_bool(self.provider_mapping_authorized, "provider_mapping_authorized")
        _require_reason_codes(self.reason_codes, "reason_codes")
        _require_evidence_reference_ids(self.evidence_reference_ids, "evidence_reference_ids")

        if self.delivery_attempt_authorized or self.provider_mapping_authorized:
            raise ValueError("no-new status decisions must not authorize execution")

        expected_reason_code = _reason_code_for_status(self.status)
        if self.reason_codes != (expected_reason_code,):
            raise ValueError("reason_codes must match the decision status")

        if self.status is NotificationNoNewStatusDecisionStatus.PUSH_STATUS_ELIGIBLE:
            if not self.status_read_model_eligible or not self.push_status_work_eligible:
                raise ValueError(
                    "push-eligible decisions must keep the read model and push work eligible"
                )
            if self.delivery_plan_decision is None:
                raise ValueError("push-eligible decisions require a planned delivery decision")
            if (
                self.delivery_plan_decision.status
                is not _NotificationDeliveryPlanDecisionStatus.PLANNED
            ):
                raise ValueError("push-eligible decisions require a planned delivery decision")
            return

        if (
            self.status
            is NotificationNoNewStatusDecisionStatus.READ_MODEL_ONLY_MINIMUM_FREQUENCY_NOT_ELAPSED
        ):
            if not self.status_read_model_eligible or self.push_status_work_eligible:
                raise ValueError("not-elapsed decisions must remain read-model-only")
            if self.delivery_plan_decision is None:
                raise ValueError("not-elapsed decisions require a planned delivery decision")
            if (
                self.delivery_plan_decision.status
                is not _NotificationDeliveryPlanDecisionStatus.PLANNED
            ):
                raise ValueError("not-elapsed decisions require a planned delivery decision")
            return

        if self.status is NotificationNoNewStatusDecisionStatus.BLOCKED_MINIMUM_FREQUENCY_AMBIGUOUS:
            if not self.status_read_model_eligible or self.push_status_work_eligible:
                raise ValueError("ambiguous decisions must remain read-model-safe")
            if self.delivery_plan_decision is None:
                raise ValueError("ambiguous decisions require a planned delivery decision")
            if (
                self.delivery_plan_decision.status
                is not _NotificationDeliveryPlanDecisionStatus.PLANNED
            ):
                raise ValueError("ambiguous decisions require a planned delivery decision")
            return

        if self.status is NotificationNoNewStatusDecisionStatus.BLOCKED_ELIGIBILITY:
            if self.push_status_work_eligible:
                raise ValueError("blocked eligibility decisions must not authorize push work")
            return

        if self.status is NotificationNoNewStatusDecisionStatus.BLOCKED_CHANNEL_PLAN:
            if self.push_status_work_eligible or not self.status_read_model_eligible:
                raise ValueError("channel-plan blocked decisions must remain read-model safe")
            if (
                self.delivery_plan_decision is not None
                and self.delivery_plan_decision.status
                is _NotificationDeliveryPlanDecisionStatus.PLANNED
            ):
                raise ValueError(
                    "channel-plan blocked decisions must not carry a planned delivery decision"
                )
            return

        if not self.status_read_model_eligible or self.push_status_work_eligible:
            raise ValueError("read-model-only decisions must remain read-model-only")
        if self.delivery_plan_decision is not None:
            raise ValueError("read-model-only decisions must not carry a delivery plan decision")


def _validate_no_new_source(
    eligibility_decision: _NotificationEligibilityDecision,
) -> _NotificationEligibilityDecision:
    if type(eligibility_decision) is not _NotificationEligibilityDecision:
        raise ValueError("eligibility_decision must be _NotificationEligibilityDecision")

    source_intake_decision = eligibility_decision.source_intake_decision
    source_event = source_intake_decision.source_event
    if source_event.source_family is not _NotificationSourceFamily.NO_NEW_LISTINGS_STATUS:
        raise ValueError("no-new status policy requires NO_NEW_LISTINGS_STATUS source family")
    if source_event.source_producer is not _NotificationSourceProducer.SCAN_ORCHESTRATION:
        raise ValueError("no-new status policy requires SCAN_ORCHESTRATION source producer")
    if source_event.source_committed is not True:
        raise ValueError("no-new status policy requires a committed source event")
    if (
        type(source_event.source_commit_reference) is not str
        or not source_event.source_commit_reference.strip()
    ):
        raise ValueError("no-new status policy requires a committed source reference")
    if source_event.source_identity_ambiguous is not False:
        raise ValueError("no-new status policy requires an unambiguous source event")
    if getattr(source_event, "contains_raw_" "provider_" "p" "ay" "load") is not False:
        raise ValueError("no-new status policy requires a sanitized source event")
    if source_intake_decision.status is not _NotificationSourceIntakeStatus.ACCEPTED_STATUS_ONLY:
        raise ValueError("no-new status policy requires an accepted status-only intake decision")
    if source_intake_decision.source_accepted is not True:
        raise ValueError("no-new status policy requires accepted source evidence")
    if source_intake_decision.notification_candidate is not False:
        raise ValueError(
            "no-new status policy must not treat the source as a notification candidate"
        )
    if source_intake_decision.status_read_model_candidate is not True:
        raise ValueError("no-new status policy requires read-model candidate source evidence")
    if source_intake_decision.outbox_effect_authorized is not False:
        raise ValueError("no-new status policy must not authorize outbox effects")
    if source_intake_decision.delivery_attempt_authorized is not False:
        raise ValueError("no-new status policy must not authorize delivery attempts")
    if source_intake_decision.reason_codes != _SOURCE_ACCEPTED_STATUS_ONLY_REASON_CODES:
        raise ValueError("no-new status policy requires canonical accepted-status reason codes")

    return eligibility_decision


def _validate_no_new_eligibility_reason_codes(
    *,
    eligibility_decision: _NotificationEligibilityDecision,
    context: NotificationNoNewStatusPolicyContext,
) -> None:
    if eligibility_decision.status is _NotificationEligibilityStatus.SUPPRESSED_BY_PREFERENCE:
        if not context.status_preference_enabled:
            expected_reason_codes = _ELIGIBILITY_NO_NEW_PREFERENCE_DISABLED_REASON_CODES
        elif (
            context.configured_status_frequency_minutes is not None
            and context.configured_status_frequency_minutes < _NO_NEW_MINIMUM_FREQUENCY_MINUTES
        ):
            expected_reason_codes = _ELIGIBILITY_NO_NEW_FREQUENCY_BELOW_MINIMUM_REASON_CODES
        else:
            raise ValueError(
                "suppressed no-new decisions require disabled preference or below-minimum frequency"
            )
        if eligibility_decision.reason_codes != expected_reason_codes:
            raise ValueError("suppressed no-new eligibility reason codes must match context")
        return

    if eligibility_decision.status is _NotificationEligibilityStatus.ELIGIBLE:
        if eligibility_decision.reason_codes != _ELIGIBILITY_ELIGIBLE_REASON_CODES:
            raise ValueError("eligible no-new decisions require canonical eligibility reason codes")
        return

    if (
        eligibility_decision.status
        is _NotificationEligibilityStatus.BLOCKED_NO_ELIGIBLE_PUSH_CHANNEL
    ):
        if eligibility_decision.reason_codes != _ELIGIBILITY_NO_ELIGIBLE_PUSH_CHANNEL_REASON_CODES:
            raise ValueError(
                "blocked push-channel decisions require canonical no-channel reason codes"
            )



def _validate_mirrored_context(
    *,
    eligibility_decision: _NotificationEligibilityDecision,
    context: NotificationNoNewStatusPolicyContext,
) -> None:
    source_event = eligibility_decision.source_intake_decision.source_event
    if context.account_id != source_event.account_id:
        raise ValueError("account_id must mirror the source eligibility decision")
    if context.beacon_id != source_event.beacon_id:
        raise ValueError("beacon_id must mirror the source eligibility decision")
    if context.no_new_status_fact_reference_id != source_event.source_fact_id:
        raise ValueError("no_new_status_fact_reference_id must mirror the source fact id")
    if (
        context.status_preference_enabled
        != eligibility_decision.context.no_new_status_preference_enabled
    ):
        raise ValueError("no-new preference flag must mirror the eligibility context")
    if (
        context.configured_status_frequency_minutes
        != eligibility_decision.context.no_new_status_frequency_minutes
    ):
        raise ValueError("no-new frequency must mirror the eligibility context")


def _validate_planned_delivery_plan(
    *,
    eligibility_decision: _NotificationEligibilityDecision,
    context: NotificationNoNewStatusPolicyContext,
    delivery_plan_decision: _NotificationDeliveryPlanDecision,
) -> None:
    if type(delivery_plan_decision) is not _NotificationDeliveryPlanDecision:
        raise ValueError("delivery_plan_decision must be _NotificationDeliveryPlanDecision")

    outbox_creation_decision = delivery_plan_decision.outbox_creation_decision
    if outbox_creation_decision.eligibility_decision is not eligibility_decision:
        raise ValueError("delivery plan must belong to the supplied eligibility decision")

    if delivery_plan_decision.status is not _NotificationDeliveryPlanDecisionStatus.PLANNED:
        if delivery_plan_decision.status in (
            _NotificationDeliveryPlanDecisionStatus.BLOCKED_OUTBOX,
            _NotificationDeliveryPlanDecisionStatus.BLOCKED_CHANNEL_PLAN_AMBIGUOUS,
            _NotificationDeliveryPlanDecisionStatus.BLOCKED_NO_PUSH_CHANNEL,
        ):
            return
        raise ValueError("delivery plan decision must be planned or blocked")

    delivery_plan = delivery_plan_decision.delivery_plan
    if delivery_plan is None:
        raise ValueError("planned delivery decisions require a delivery plan")

    if delivery_plan.outbox_item.account_id != context.account_id:
        raise ValueError("delivery plan account_id must mirror the policy context")
    if delivery_plan.outbox_item.beacon_id != context.beacon_id:
        raise ValueError("delivery plan beacon_id must mirror the policy context")
    if delivery_plan.outbox_item.source_fact_id != context.no_new_status_fact_reference_id:
        raise ValueError("delivery plan source_fact_id must mirror the policy context")
    if (
        delivery_plan.outbox_item.event_reason
        is not _NotificationSourceFamily.NO_NEW_LISTINGS_STATUS
    ):
        raise ValueError("delivery plan must use NO_NEW_LISTINGS_STATUS as the event reason")
    if delivery_plan.push_channel_classes != eligibility_decision.eligible_push_channels:
        raise ValueError("delivery plan push channel projection must mirror eligibility")
    if not delivery_plan.web_status_read_model_planned:
        raise ValueError("delivery plan must keep the web read model planned")


def _build_policy_decision(
    *,
    decision_id: str,
    eligibility_decision: _NotificationEligibilityDecision,
    delivery_plan_decision: _NotificationDeliveryPlanDecision | None,
    context: NotificationNoNewStatusPolicyContext,
    status: NotificationNoNewStatusDecisionStatus,
    status_read_model_eligible: bool,
    push_status_work_eligible: bool,
    evidence_reference_ids: tuple[str, ...],
) -> NotificationNoNewStatusPolicyDecision:
    return NotificationNoNewStatusPolicyDecision(
        decision_id=decision_id,
        authority=NotificationNoNewStatusAuthority.NOTIFICATION_DELIVERY_SERVER,
        eligibility_decision=eligibility_decision,
        delivery_plan_decision=delivery_plan_decision,
        context=context,
        status=status,
        status_read_model_eligible=status_read_model_eligible,
        push_status_work_eligible=push_status_work_eligible,
        delivery_attempt_authorized=False,
        provider_mapping_authorized=False,
        reason_codes=(_reason_code_for_status(status),),
        evidence_reference_ids=evidence_reference_ids,
    )


def evaluate_no_new_status_policy(
    *,
    decision_id: str,
    eligibility_decision: _NotificationEligibilityDecision,
    delivery_plan_decision: _NotificationDeliveryPlanDecision | None,
    context: NotificationNoNewStatusPolicyContext,
    evidence_reference_ids: tuple[str, ...],
) -> NotificationNoNewStatusPolicyDecision:
    _require_text(decision_id, "decision_id")
    _require_evidence_reference_ids(evidence_reference_ids, "evidence_reference_ids")
    if type(context) is not NotificationNoNewStatusPolicyContext:
        raise ValueError("context must be NotificationNoNewStatusPolicyContext")

    validated_eligibility_decision = _validate_no_new_source(eligibility_decision)
    _validate_mirrored_context(
        eligibility_decision=validated_eligibility_decision,
        context=context,
    )
    _validate_no_new_eligibility_reason_codes(
        eligibility_decision=validated_eligibility_decision,
        context=context,
    )

    combined_evidence_reference_ids = _first_occurrence_union(
        validated_eligibility_decision.evidence_reference_ids,
        delivery_plan_decision.evidence_reference_ids if delivery_plan_decision is not None else (),
        context.evidence_reference_ids,
        evidence_reference_ids,
    )

    if (
        validated_eligibility_decision.status
        is _NotificationEligibilityStatus.SUPPRESSED_BY_PREFERENCE
    ):
        if delivery_plan_decision is not None:
            raise ValueError("suppressed no-new decisions must not carry a delivery plan decision")
        if not context.status_preference_enabled:
            return _build_policy_decision(
                decision_id=decision_id,
                eligibility_decision=validated_eligibility_decision,
                delivery_plan_decision=None,
                context=context,
                status=NotificationNoNewStatusDecisionStatus.READ_MODEL_ONLY_PREFERENCE_DISABLED,
                status_read_model_eligible=True,
                push_status_work_eligible=False,
                evidence_reference_ids=combined_evidence_reference_ids,
            )
        if (
            context.configured_status_frequency_minutes is not None
            and context.configured_status_frequency_minutes < _NO_NEW_MINIMUM_FREQUENCY_MINUTES
        ):
            return _build_policy_decision(
                decision_id=decision_id,
                eligibility_decision=validated_eligibility_decision,
                delivery_plan_decision=None,
                context=context,
                status=NotificationNoNewStatusDecisionStatus.READ_MODEL_ONLY_FREQUENCY_BELOW_MINIMUM,
                status_read_model_eligible=True,
                push_status_work_eligible=False,
                evidence_reference_ids=combined_evidence_reference_ids,
            )
        raise ValueError(
            "suppressed no-new decisions must reflect disabled preference "
            "or below-minimum frequency"
        )

    if (
        validated_eligibility_decision.status
        is _NotificationEligibilityStatus.BLOCKED_NO_ELIGIBLE_PUSH_CHANNEL
    ):
        if delivery_plan_decision is not None:
            raise ValueError(
                "no-eligible-channel decisions must not carry a delivery plan decision"
            )
        if validated_eligibility_decision.eligible_push_channels:
            raise ValueError("blocked no-eligible-channel decisions must not expose push channels")
        return _build_policy_decision(
            decision_id=decision_id,
            eligibility_decision=validated_eligibility_decision,
            delivery_plan_decision=None,
            context=context,
            status=NotificationNoNewStatusDecisionStatus.READ_MODEL_ONLY_NO_ELIGIBLE_PUSH_CHANNEL,
            status_read_model_eligible=True,
            push_status_work_eligible=False,
            evidence_reference_ids=combined_evidence_reference_ids,
        )

    if validated_eligibility_decision.status is _NotificationEligibilityStatus.ELIGIBLE:
        if not validated_eligibility_decision.eligible_push_channels:
            raise ValueError("eligible no-new decisions require at least one push channel")
        if not context.status_preference_enabled:
            raise ValueError("eligible no-new decisions require enabled preference")
        if context.configured_status_frequency_minutes is None:
            raise ValueError("eligible no-new decisions require a configured frequency")
        if context.configured_status_frequency_minutes < _NO_NEW_MINIMUM_FREQUENCY_MINUTES:
            raise ValueError("eligible no-new decisions require a minimum configured frequency")

        if delivery_plan_decision is None:
            return _build_policy_decision(
                decision_id=decision_id,
                eligibility_decision=validated_eligibility_decision,
                delivery_plan_decision=None,
                context=context,
                status=NotificationNoNewStatusDecisionStatus.BLOCKED_CHANNEL_PLAN,
                status_read_model_eligible=True,
                push_status_work_eligible=False,
                evidence_reference_ids=combined_evidence_reference_ids,
            )

        _validate_planned_delivery_plan(
            eligibility_decision=validated_eligibility_decision,
            context=context,
            delivery_plan_decision=delivery_plan_decision,
        )

        if delivery_plan_decision.status is not _NotificationDeliveryPlanDecisionStatus.PLANNED:
            return _build_policy_decision(
                decision_id=decision_id,
                eligibility_decision=validated_eligibility_decision,
                delivery_plan_decision=delivery_plan_decision,
                context=context,
                status=NotificationNoNewStatusDecisionStatus.BLOCKED_CHANNEL_PLAN,
                status_read_model_eligible=True,
                push_status_work_eligible=False,
                evidence_reference_ids=combined_evidence_reference_ids,
            )

        if (
            context.minimum_frequency_gate_status
            is NotificationNoNewMinimumFrequencyGateStatus.NO_PRIOR_NOTIFICATION
        ):
            return _build_policy_decision(
                decision_id=decision_id,
                eligibility_decision=validated_eligibility_decision,
                delivery_plan_decision=delivery_plan_decision,
                context=context,
                status=NotificationNoNewStatusDecisionStatus.PUSH_STATUS_ELIGIBLE,
                status_read_model_eligible=True,
                push_status_work_eligible=True,
                evidence_reference_ids=combined_evidence_reference_ids,
            )

        if (
            context.minimum_frequency_gate_status
            is NotificationNoNewMinimumFrequencyGateStatus.MINIMUM_FREQUENCY_ELAPSED
        ):
            return _build_policy_decision(
                decision_id=decision_id,
                eligibility_decision=validated_eligibility_decision,
                delivery_plan_decision=delivery_plan_decision,
                context=context,
                status=NotificationNoNewStatusDecisionStatus.PUSH_STATUS_ELIGIBLE,
                status_read_model_eligible=True,
                push_status_work_eligible=True,
                evidence_reference_ids=combined_evidence_reference_ids,
            )

        if (
            context.minimum_frequency_gate_status
            is NotificationNoNewMinimumFrequencyGateStatus.MINIMUM_FREQUENCY_NOT_ELAPSED
        ):
            return _build_policy_decision(
                decision_id=decision_id,
                eligibility_decision=validated_eligibility_decision,
                delivery_plan_decision=delivery_plan_decision,
                context=context,
                status=NotificationNoNewStatusDecisionStatus.READ_MODEL_ONLY_MINIMUM_FREQUENCY_NOT_ELAPSED,
                status_read_model_eligible=True,
                push_status_work_eligible=False,
                evidence_reference_ids=combined_evidence_reference_ids,
            )

        if (
            context.minimum_frequency_gate_status
            is NotificationNoNewMinimumFrequencyGateStatus.AMBIGUOUS
        ):
            return _build_policy_decision(
                decision_id=decision_id,
                eligibility_decision=validated_eligibility_decision,
                delivery_plan_decision=delivery_plan_decision,
                context=context,
                status=NotificationNoNewStatusDecisionStatus.BLOCKED_MINIMUM_FREQUENCY_AMBIGUOUS,
                status_read_model_eligible=True,
                push_status_work_eligible=False,
                evidence_reference_ids=combined_evidence_reference_ids,
            )

        raise ValueError("eligible no-new decisions require supported minimum frequency evidence")

    if delivery_plan_decision is not None:
        raise ValueError("non-eligible no-new decisions must not carry a delivery plan decision")

    return _build_policy_decision(
        decision_id=decision_id,
        eligibility_decision=validated_eligibility_decision,
        delivery_plan_decision=None,
        context=context,
        status=NotificationNoNewStatusDecisionStatus.BLOCKED_ELIGIBILITY,
        status_read_model_eligible=validated_eligibility_decision.status_read_model_eligible,
        push_status_work_eligible=False,
        evidence_reference_ids=combined_evidence_reference_ids,
    )


__all__ = (
    "ND08_TASK_ID",
    "NotificationNoNewStatusAuthority",
    "NotificationNoNewMinimumFrequencyGateStatus",
    "NotificationNoNewStatusDecisionStatus",
    "NotificationNoNewStatusPolicyContext",
    "NotificationNoNewStatusPolicyDecision",
    "evaluate_no_new_status_policy",
)
