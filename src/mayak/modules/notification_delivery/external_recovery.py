 # ruff: noqa: E501
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .deduplication import (
    NotificationDeduplicationDecision,
    NotificationDeduplicationDecisionStatus,
    NotificationDeduplicationRecord,
    NotificationDeduplicationRecordState,
    NotificationDeduplicationRequest,
    NotificationDeduplicationStage,
)
from .delivery_plan import (
    NotificationDeliveryChannelPlanEntry,
    NotificationDeliveryPlan,
    NotificationDeliveryPlanAuthority,
    NotificationDeliveryPlanDecision,
    NotificationDeliveryPlanDecisionStatus,
)
from .eligibility import (
    NotificationChannelClass,
    NotificationChannelGateDecision,
    NotificationEligibilityDecision,
    NotificationEligibilityStatus,
    NotificationRecoveryGraceEvidence,
)
from .source_intake import (
    NotificationSourceEvent,
    NotificationSourceFamily,
    NotificationSourceIntakeDecision,
    NotificationSourceIntakeStatus,
    NotificationSourceProducer,
)

ND09_TASK_ID = "ND-09-EXTERNAL-RECOVERY-POLICY-SEMANTICS-20260716-015"

_ALLOWED_SOURCE_FAMILIES = (
    NotificationSourceFamily.EXTERNAL_UNAVAILABLE_STATUS,
    NotificationSourceFamily.RECOVERY_SCAN_COMPLETED,
    NotificationSourceFamily.LOST_ANCHORS_RECOVERED,
)

_SOURCE_REASON_BY_FAMILY = {
    NotificationSourceFamily.EXTERNAL_UNAVAILABLE_STATUS: ("source-accepted-external-status",),
    NotificationSourceFamily.RECOVERY_SCAN_COMPLETED: ("source-accepted-recovery-result",),
    NotificationSourceFamily.LOST_ANCHORS_RECOVERED: (
        "source-accepted-lost-anchors-state-restored",
    ),
}

_REASON_BY_STATUS = {
    "PUSH_WORK_ELIGIBLE": ("external-recovery-push-work-eligible",),
    "READ_MODEL_ONLY_SAME_PROBLEM": ("external-status-same-problem-read-model-only",),
    "READ_MODEL_ONLY_REPLAY_TERMINAL": ("external-recovery-replay-terminal",),
    "READ_MODEL_ONLY_REPLAY_PENDING": ("external-recovery-replay-pending",),
    "READ_MODEL_ONLY_NO_ELIGIBLE_PUSH_CHANNEL": ("external-recovery-no-eligible-push-channel",),
    "RECONCILIATION_REQUIRED": ("external-recovery-reconciliation-required",),
    "BLOCKED_ELIGIBILITY": ("external-recovery-eligibility-blocked",),
    "BLOCKED_PROBLEM_GATE_AMBIGUOUS": ("external-status-problem-gate-ambiguous",),
    "BLOCKED_IDEMPOTENCY": ("external-recovery-idempotency-blocked",),
    "BLOCKED_CHANNEL_PLAN": ("external-recovery-channel-plan-blocked",),
    "BLOCKED_RECOVERY_ALREADY_CONSUMED": ("recovery-result-already-consumed",),
}

_REPLAY_DECISION_TO_STATUS = {
    NotificationDeduplicationDecisionStatus.REPLAY_TERMINAL: ("READ_MODEL_ONLY_REPLAY_TERMINAL",),
    NotificationDeduplicationDecisionStatus.REPLAY_PENDING: ("READ_MODEL_ONLY_REPLAY_PENDING",),
}

_BLOCKED_ELIGIBILITY_STATUSES = {
    NotificationEligibilityStatus.BLOCKED_SOURCE_INTAKE,
    NotificationEligibilityStatus.BLOCKED_SCOPE_MISMATCH,
    NotificationEligibilityStatus.BLOCKED_BEACON_LIFECYCLE,
    NotificationEligibilityStatus.BLOCKED_ENTITLEMENT,
    NotificationEligibilityStatus.BLOCKED_AMBIGUOUS,
}

_BLOCKED_ELIGIBILITY_REASON_CODES = {
    ("eligibility-source-intake-blocked",),
    ("eligibility-account-scope-mismatch",),
    ("eligibility-beacon-scope-mismatch",),
    ("eligibility-beacon-lifecycle-ambiguous",),
    ("eligibility-entitlement-ambiguous",),
    ("eligibility-beacon-lifecycle-not-active",),
    ("eligibility-entitlement-not-allowed",),
}

_BLOCKED_PLAN_REASON_CODES = {
    ("delivery-plan-outbox-blocked",),
    ("delivery-plan-channel-evidence-ambiguous",),
    ("delivery-plan-no-push-channel",),
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
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not allow_empty and not value:
        raise ValueError(f"{field_name} must not be empty")
    return tuple(_require_text(item, field_name) for item in value)


def _require_named_type(
    value: object,
    field_name: str,
    *,
    module_name: str,
    class_name: str,
) -> object:
    if value.__class__.__module__ != module_name or value.__class__.__name__ != class_name:
        raise ValueError(f"{field_name} must be {class_name}")
    return value


def _first_occurrence_union(*tuples: tuple[str, ...]) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []
    for items in tuples:
        for item in items:
            if item not in seen:
                seen.add(item)
                ordered.append(item)
    return tuple(ordered)


class NotificationExternalRecoveryAuthority(str, Enum):
    NOTIFICATION_DELIVERY_SERVER = "NOTIFICATION_DELIVERY_SERVER"


class NotificationExternalRecoveryEffectClass(str, Enum):
    AVITO_UNAVAILABLE_CONTINUING_SCAN = "AVITO_UNAVAILABLE_CONTINUING_SCAN"
    RECOVERY_RESULT_WITH_NEW_LISTINGS = "RECOVERY_RESULT_WITH_NEW_LISTINGS"
    RECOVERY_RESULT_NO_NEW_LISTINGS = "RECOVERY_RESULT_NO_NEW_LISTINGS"
    RECOVERY_RESULT_LOST_ANCHORS_RESTORED = "RECOVERY_RESULT_LOST_ANCHORS_RESTORED"
    RECOVERY_BLOCKED_OR_AMBIGUOUS = "RECOVERY_BLOCKED_OR_AMBIGUOUS"


class NotificationExternalProblemGateStatus(str, Enum):
    NOT_APPLICABLE = "NOT_APPLICABLE"
    PROBLEM_BEGAN = "PROBLEM_BEGAN"
    MATERIAL_CHANGE = "MATERIAL_CHANGE"
    SAME_PROBLEM_UNCHANGED = "SAME_PROBLEM_UNCHANGED"
    AMBIGUOUS = "AMBIGUOUS"


class NotificationExternalRecoveryDecisionStatus(str, Enum):
    PUSH_WORK_ELIGIBLE = "PUSH_WORK_ELIGIBLE"
    READ_MODEL_ONLY_SAME_PROBLEM = "READ_MODEL_ONLY_SAME_PROBLEM"
    READ_MODEL_ONLY_REPLAY_TERMINAL = "READ_MODEL_ONLY_REPLAY_TERMINAL"
    READ_MODEL_ONLY_REPLAY_PENDING = "READ_MODEL_ONLY_REPLAY_PENDING"
    READ_MODEL_ONLY_NO_ELIGIBLE_PUSH_CHANNEL = "READ_MODEL_ONLY_NO_ELIGIBLE_PUSH_CHANNEL"
    RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"
    BLOCKED_ELIGIBILITY = "BLOCKED_ELIGIBILITY"
    BLOCKED_PROBLEM_GATE_AMBIGUOUS = "BLOCKED_PROBLEM_GATE_AMBIGUOUS"
    BLOCKED_IDEMPOTENCY = "BLOCKED_IDEMPOTENCY"
    BLOCKED_CHANNEL_PLAN = "BLOCKED_CHANNEL_PLAN"
    BLOCKED_RECOVERY_ALREADY_CONSUMED = "BLOCKED_RECOVERY_ALREADY_CONSUMED"


_ALLOWED_EXTERNAL_GATE_STATUSES = (
    NotificationExternalProblemGateStatus.PROBLEM_BEGAN,
    NotificationExternalProblemGateStatus.MATERIAL_CHANGE,
    NotificationExternalProblemGateStatus.SAME_PROBLEM_UNCHANGED,
    NotificationExternalProblemGateStatus.AMBIGUOUS,
)


@dataclass(frozen=True, slots=True)
class NotificationExternalRecoveryPolicyContext:
    account_id: str
    beacon_id: str
    source_fact_reference_id: str
    external_problem_reference_id: str
    material_change_reference_id: str | None
    problem_gate_status: NotificationExternalProblemGateStatus
    recovery_obligation_reference_id: str | None
    recovery_result_already_consumed: bool
    evidence_reference_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_text(self.account_id, "account_id")
        _require_text(self.beacon_id, "beacon_id")
        _require_text(self.source_fact_reference_id, "source_fact_reference_id")
        _require_text(self.external_problem_reference_id, "external_problem_reference_id")
        _require_optional_text(self.material_change_reference_id, "material_change_reference_id")
        _require_exact_enum(
            self.problem_gate_status,
            NotificationExternalProblemGateStatus,
            "problem_gate_status",
        )
        _require_optional_text(
            self.recovery_obligation_reference_id,
            "recovery_obligation_reference_id",
        )
        _require_bool(self.recovery_result_already_consumed, "recovery_result_already_consumed")
        _require_text_tuple(self.evidence_reference_ids, "evidence_reference_ids", allow_empty=True)


@dataclass(frozen=True, slots=True)
class NotificationExternalRecoveryPolicyDecision:
    decision_id: str
    authority: NotificationExternalRecoveryAuthority
    eligibility_decision: NotificationEligibilityDecision
    deduplication_decision: NotificationDeduplicationDecision | None
    delivery_plan_decision: NotificationDeliveryPlanDecision | None
    context: NotificationExternalRecoveryPolicyContext
    effect_class: NotificationExternalRecoveryEffectClass
    status: NotificationExternalRecoveryDecisionStatus
    status_read_model_eligible: bool
    push_work_eligible: bool
    replayed: bool
    reconciliation_required: bool
    recovery_grace_applied: bool
    delivery_attempt_authorized: bool
    provider_mapping_authorized: bool
    reason_codes: tuple[str, ...]
    evidence_reference_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_text(self.decision_id, "decision_id")
        _require_exact_enum(self.authority, NotificationExternalRecoveryAuthority, "authority")
        if type(self.eligibility_decision) is not NotificationEligibilityDecision:
            raise ValueError("eligibility_decision must be NotificationEligibilityDecision")
        if self.deduplication_decision is not None and (
            type(self.deduplication_decision) is not NotificationDeduplicationDecision
        ):
            raise ValueError(
                "deduplication_decision must be NotificationDeduplicationDecision | None"
            )
        if self.delivery_plan_decision is not None and (
            type(self.delivery_plan_decision) is not NotificationDeliveryPlanDecision
        ):
            raise ValueError(
                "delivery_plan_decision must be NotificationDeliveryPlanDecision | None"
            )
        if type(self.context) is not NotificationExternalRecoveryPolicyContext:
            raise ValueError("context must be NotificationExternalRecoveryPolicyContext")
        _require_exact_enum(
            self.effect_class, NotificationExternalRecoveryEffectClass, "effect_class"
        )
        _require_exact_enum(self.status, NotificationExternalRecoveryDecisionStatus, "status")
        _require_bool(self.status_read_model_eligible, "status_read_model_eligible")
        _require_bool(self.push_work_eligible, "push_work_eligible")
        _require_bool(self.replayed, "replayed")
        _require_bool(self.reconciliation_required, "reconciliation_required")
        _require_bool(self.recovery_grace_applied, "recovery_grace_applied")
        _require_bool(self.delivery_attempt_authorized, "delivery_attempt_authorized")
        _require_bool(self.provider_mapping_authorized, "provider_mapping_authorized")
        _require_text_tuple(self.reason_codes, "reason_codes", allow_empty=False)
        _require_text_tuple(self.evidence_reference_ids, "evidence_reference_ids", allow_empty=True)

        if self.delivery_attempt_authorized or self.provider_mapping_authorized:
            raise ValueError("external recovery decisions must not authorize execution")

        expected_reason_codes = _REASON_BY_STATUS[self.status.name]
        if self.reason_codes != expected_reason_codes:
            raise ValueError("reason_codes must match the decision status")

        if self.status in {
            NotificationExternalRecoveryDecisionStatus.BLOCKED_ELIGIBILITY,
            NotificationExternalRecoveryDecisionStatus.BLOCKED_PROBLEM_GATE_AMBIGUOUS,
            NotificationExternalRecoveryDecisionStatus.BLOCKED_IDEMPOTENCY,
            NotificationExternalRecoveryDecisionStatus.BLOCKED_CHANNEL_PLAN,
            NotificationExternalRecoveryDecisionStatus.BLOCKED_RECOVERY_ALREADY_CONSUMED,
            NotificationExternalRecoveryDecisionStatus.RECONCILIATION_REQUIRED,
        }:
            if (
                self.effect_class
                is not NotificationExternalRecoveryEffectClass.RECOVERY_BLOCKED_OR_AMBIGUOUS
            ):
                raise ValueError("blocked decisions must use the blocked effect class")
        else:
            if (
                self.effect_class
                is NotificationExternalRecoveryEffectClass.RECOVERY_BLOCKED_OR_AMBIGUOUS
            ):
                raise ValueError("non-blocked decisions must preserve the source effect class")

        if self.status is NotificationExternalRecoveryDecisionStatus.PUSH_WORK_ELIGIBLE:
            if not self.status_read_model_eligible or not self.push_work_eligible:
                raise ValueError("push work decisions must keep read-model and push eligibility")
            if self.replayed or self.reconciliation_required:
                raise ValueError("push work decisions must not be replayed or reconciled")
            if self.deduplication_decision is None or self.delivery_plan_decision is None:
                raise ValueError(
                    "push work decisions require deduplication and delivery plan evidence"
                )
            if (
                self.deduplication_decision.status
                is not NotificationDeduplicationDecisionStatus.NEW_EFFECT
            ):
                raise ValueError("push work decisions require a NEW_EFFECT dedup decision")
            if (
                self.delivery_plan_decision.status
                is not NotificationDeliveryPlanDecisionStatus.PLANNED
            ):
                raise ValueError("push work decisions require a planned delivery decision")
            return

        if self.status is NotificationExternalRecoveryDecisionStatus.READ_MODEL_ONLY_SAME_PROBLEM:
            if not self.status_read_model_eligible or self.push_work_eligible:
                raise ValueError("same-problem decisions must remain read-model-only")
            if not self.replayed or self.reconciliation_required:
                raise ValueError("same-problem decisions must be replay-only")
            if self.delivery_plan_decision is not None:
                raise ValueError("same-problem decisions must not carry a delivery plan decision")
            if self.deduplication_decision is None:
                raise ValueError("same-problem decisions require deduplication evidence")
            if self.deduplication_decision.status not in (
                NotificationDeduplicationDecisionStatus.REPLAY_TERMINAL,
                NotificationDeduplicationDecisionStatus.REPLAY_PENDING,
            ):
                raise ValueError("same-problem decisions require replay evidence")
            return

        if (
            self.status
            is NotificationExternalRecoveryDecisionStatus.READ_MODEL_ONLY_REPLAY_TERMINAL
        ):
            if not self.status_read_model_eligible or self.push_work_eligible:
                raise ValueError("terminal replay decisions must remain read-model-only")
            if not self.replayed or self.reconciliation_required:
                raise ValueError("terminal replay decisions must be replay-only")
            if self.delivery_plan_decision is not None:
                raise ValueError(
                    "terminal replay decisions must not carry a delivery plan decision"
                )
            if self.deduplication_decision is None or (
                self.deduplication_decision.status
                is not NotificationDeduplicationDecisionStatus.REPLAY_TERMINAL
            ):
                raise ValueError("terminal replay decisions require replay-terminal evidence")
            return

        if self.status is NotificationExternalRecoveryDecisionStatus.READ_MODEL_ONLY_REPLAY_PENDING:
            if not self.status_read_model_eligible or self.push_work_eligible:
                raise ValueError("pending replay decisions must remain read-model-only")
            if not self.replayed or self.reconciliation_required:
                raise ValueError("pending replay decisions must be replay-only")
            if self.delivery_plan_decision is not None:
                raise ValueError("pending replay decisions must not carry a delivery plan decision")
            if self.deduplication_decision is None or (
                self.deduplication_decision.status
                is not NotificationDeduplicationDecisionStatus.REPLAY_PENDING
            ):
                raise ValueError("pending replay decisions require replay-pending evidence")
            return

        if (
            self.status
            is NotificationExternalRecoveryDecisionStatus.READ_MODEL_ONLY_NO_ELIGIBLE_PUSH_CHANNEL
        ):
            if not self.status_read_model_eligible or self.push_work_eligible:
                raise ValueError("no-channel decisions must remain read-model-only")
            if self.replayed or self.reconciliation_required:
                raise ValueError("no-channel decisions must not be replayed or reconciled")
            if self.deduplication_decision is not None or self.delivery_plan_decision is not None:
                raise ValueError(
                    "no-channel decisions must not carry deduplication or plan evidence"
                )
            return

        if self.status is NotificationExternalRecoveryDecisionStatus.RECONCILIATION_REQUIRED:
            if not self.status_read_model_eligible or self.push_work_eligible:
                raise ValueError("reconciliation decisions must remain read-model-safe")
            if not self.replayed or not self.reconciliation_required:
                raise ValueError("reconciliation decisions must mark reconciliation")
            if self.delivery_plan_decision is not None:
                raise ValueError("reconciliation decisions must not carry a delivery plan decision")
            if self.deduplication_decision is None or (
                self.deduplication_decision.status
                is not NotificationDeduplicationDecisionStatus.RECONCILIATION_REQUIRED
            ):
                raise ValueError("reconciliation decisions require reconciliation evidence")
            return

        if self.status is NotificationExternalRecoveryDecisionStatus.BLOCKED_ELIGIBILITY:
            if self.push_work_eligible or self.replayed or self.reconciliation_required:
                raise ValueError("blocked eligibility decisions must not authorize work")
            if self.deduplication_decision is not None or self.delivery_plan_decision is not None:
                raise ValueError("blocked eligibility decisions must not carry work evidence")
            return

        if self.status is NotificationExternalRecoveryDecisionStatus.BLOCKED_PROBLEM_GATE_AMBIGUOUS:
            if self.push_work_eligible or self.replayed or self.reconciliation_required:
                raise ValueError("ambiguous gate decisions must not authorize work")
            if self.deduplication_decision is not None or self.delivery_plan_decision is not None:
                raise ValueError("ambiguous gate decisions must not carry work evidence")
            return

        if self.status is NotificationExternalRecoveryDecisionStatus.BLOCKED_IDEMPOTENCY:
            if self.push_work_eligible or self.replayed or self.reconciliation_required:
                raise ValueError("idempotency-blocked decisions must not authorize work")
            if self.delivery_plan_decision is not None:
                raise ValueError(
                    "idempotency-blocked decisions must not carry a delivery plan decision"
                )
            if self.deduplication_decision is None or self.deduplication_decision.status not in (
                NotificationDeduplicationDecisionStatus.MISSING_REQUIRED_IDEMPOTENCY,
                NotificationDeduplicationDecisionStatus.IDEMPOTENCY_MISMATCH,
            ):
                raise ValueError("idempotency-blocked decisions require blocked dedup evidence")
            return

        if self.status is NotificationExternalRecoveryDecisionStatus.BLOCKED_CHANNEL_PLAN:
            if self.push_work_eligible or self.replayed or self.reconciliation_required:
                raise ValueError("blocked channel-plan decisions must not authorize work")
            if self.deduplication_decision is None:
                raise ValueError("blocked channel-plan decisions require dedup evidence")
            if (
                self.deduplication_decision.status
                is not NotificationDeduplicationDecisionStatus.NEW_EFFECT
            ):
                raise ValueError("blocked channel-plan decisions require NEW_EFFECT dedup evidence")
            if self.delivery_plan_decision is not None and (
                self.delivery_plan_decision.status is NotificationDeliveryPlanDecisionStatus.PLANNED
            ):
                raise ValueError(
                    "blocked channel-plan decisions must not carry a planned delivery decision"
                )
            return

        if (
            self.status
            is NotificationExternalRecoveryDecisionStatus.BLOCKED_RECOVERY_ALREADY_CONSUMED
        ):
            if self.push_work_eligible or self.replayed or self.reconciliation_required:
                raise ValueError("consumed-recovery decisions must not authorize work")
            if self.delivery_plan_decision is not None:
                raise ValueError(
                    "consumed-recovery decisions must not carry a delivery plan decision"
                )
            if (
                self.deduplication_decision is None
                or self.deduplication_decision.status
                is not NotificationDeduplicationDecisionStatus.NEW_EFFECT
            ):
                raise ValueError("consumed-recovery decisions require NEW_EFFECT dedup evidence")
            return

        raise ValueError("unsupported external recovery decision status")


def _validate_source_provenance(
    eligibility_decision: NotificationEligibilityDecision,
) -> tuple[NotificationSourceIntakeDecision, NotificationSourceEvent]:
    if type(eligibility_decision) is not NotificationEligibilityDecision:
        raise ValueError("eligibility_decision must be NotificationEligibilityDecision")

    source_intake_decision = eligibility_decision.source_intake_decision
    if type(source_intake_decision) is not NotificationSourceIntakeDecision:
        raise ValueError("source_intake_decision must be NotificationSourceIntakeDecision")

    source_event = source_intake_decision.source_event
    if type(source_event) is not NotificationSourceEvent:
        raise ValueError("source_event must be NotificationSourceEvent")
    if source_event.source_family not in _ALLOWED_SOURCE_FAMILIES:
        raise ValueError("external recovery policy requires an accepted external source family")
    if source_event.source_producer is not NotificationSourceProducer.SCAN_ORCHESTRATION:
        raise ValueError("external recovery policy requires SCAN_ORCHESTRATION provenance")
    if source_event.source_committed is not True:
        raise ValueError("external recovery policy requires a committed source event")
    if (
        type(source_event.source_commit_reference) is not str
        or not source_event.source_commit_reference.strip()
    ):
        raise ValueError("external recovery policy requires a committed source reference")
    if source_event.source_identity_ambiguous is not False:
        raise ValueError("external recovery policy requires an unambiguous source event")
    if source_event.contains_raw_provider_payload is not False:
        raise ValueError("external recovery policy requires sanitized source evidence")
    if source_event.beacon_id is None:
        raise ValueError("external recovery policy requires a beacon reference")
    if (
        source_intake_decision.status
        is not NotificationSourceIntakeStatus.ACCEPTED_NOTIFICATION_CANDIDATE
    ):
        raise ValueError("external recovery policy requires accepted notification intake")
    if source_intake_decision.source_accepted is not True:
        raise ValueError("external recovery policy requires accepted source evidence")
    if source_intake_decision.notification_candidate is not True:
        raise ValueError("external recovery policy requires a notification candidate")
    if source_intake_decision.status_read_model_candidate is not True:
        raise ValueError("external recovery policy requires a read-model candidate")
    if source_intake_decision.outbox_effect_authorized is not False:
        raise ValueError("external recovery policy must not authorize outbox effects")
    if source_intake_decision.delivery_attempt_authorized is not False:
        raise ValueError("external recovery policy must not authorize delivery attempts")
    if source_intake_decision.reason_codes != _SOURCE_REASON_BY_FAMILY[source_event.source_family]:
        raise ValueError("external recovery policy requires canonical source reasons")
    if eligibility_decision.source_intake_decision is not source_intake_decision:
        raise ValueError("eligibility decision must reference the supplied source intake decision")

    if any(code.startswith("eligibility-no-new-") for code in eligibility_decision.reason_codes):
        raise ValueError("external recovery policy forbids no-new preference evidence")
    if eligibility_decision.status in (
        NotificationEligibilityStatus.SUPPRESSED_BY_PREFERENCE,
        NotificationEligibilityStatus.STATUS_READ_MODEL_ONLY,
    ):
        raise ValueError("external recovery policy forbids no-new eligibility statuses")
    if eligibility_decision.outbox_effect_authorized is not False:
        raise ValueError("external recovery policy must not authorize outbox effects")
    if eligibility_decision.delivery_attempt_authorized is not False:
        raise ValueError("external recovery policy must not authorize delivery attempts")
    if type(eligibility_decision.context.recovery_grace_evidence) is not NotificationRecoveryGraceEvidence:
        raise ValueError("recovery_grace_evidence must be NotificationRecoveryGraceEvidence")

    eligible_push_channels = eligibility_decision.eligible_push_channels
    if type(eligible_push_channels) is not tuple:
        raise ValueError("eligible_push_channels must be a tuple")
    for gate in eligibility_decision.channel_gate_decisions:
        if type(gate) is not NotificationChannelGateDecision:
            raise ValueError("channel_gate_decisions must contain NotificationChannelGateDecision")
    if (
        tuple(
            gate.channel_class
            for gate in eligibility_decision.channel_gate_decisions
            if gate.push_eligible
        )
        != eligible_push_channels
    ):
        raise ValueError("eligible push channels must mirror the accepted gate decisions")

    if eligibility_decision.status is NotificationEligibilityStatus.ELIGIBLE:
        if (
            not eligibility_decision.source_eligible
            or not eligibility_decision.outbox_candidate_eligible
        ):
            raise ValueError("eligible decisions must authorize source and outbox work")
        if not eligibility_decision.status_read_model_eligible:
            raise ValueError("eligible decisions must keep the read model eligible")
        if eligibility_decision.recovery_grace_applied:
            raise ValueError("eligible decisions must not apply recovery grace")
        if not eligible_push_channels:
            raise ValueError("eligible decisions require at least one eligible push channel")
        if eligibility_decision.reason_codes != ("eligibility-eligible",):
            raise ValueError("eligible decisions require canonical eligibility reasons")
    elif eligibility_decision.status is NotificationEligibilityStatus.ELIGIBLE_RECOVERY_GRACE:
        if source_event.source_family is not NotificationSourceFamily.RECOVERY_SCAN_COMPLETED:
            raise ValueError("recovery grace is only valid for recovery scan results")
        if (
            not eligibility_decision.source_eligible
            or not eligibility_decision.outbox_candidate_eligible
        ):
            raise ValueError("recovery grace decisions must authorize source and outbox work")
        if not eligibility_decision.status_read_model_eligible:
            raise ValueError("recovery grace decisions must keep the read model eligible")
        if not eligibility_decision.recovery_grace_applied:
            raise ValueError("recovery grace decisions must mark grace as applied")
        if not eligible_push_channels:
            raise ValueError("recovery grace decisions require at least one eligible push channel")
        if eligibility_decision.reason_codes != ("eligibility-recovery-grace-applied",):
            raise ValueError("recovery grace decisions require canonical reasons")
        grace_evidence = eligibility_decision.context.recovery_grace_evidence
        if grace_evidence.problem_began_while_access_active is not True:
            raise ValueError("recovery grace requires an access-active beginning")
        if grace_evidence.recovery_result_already_consumed is not False:
            raise ValueError("recovery grace requires an unconsumed recovery result")
        if grace_evidence.recovery_obligation_reference_id is None:
            raise ValueError("recovery grace requires a recovery obligation reference")
    elif (
        eligibility_decision.status
        is NotificationEligibilityStatus.BLOCKED_NO_ELIGIBLE_PUSH_CHANNEL
    ):
        if (
            not eligibility_decision.source_eligible
            or eligibility_decision.outbox_candidate_eligible
        ):
            raise ValueError("no-channel decisions must keep source eligible and outbox blocked")
        if not eligibility_decision.status_read_model_eligible:
            raise ValueError("no-channel decisions must keep the read model eligible")
        if eligibility_decision.recovery_grace_applied:
            raise ValueError("no-channel decisions must not apply recovery grace")
        if eligible_push_channels:
            raise ValueError("no-channel decisions must not expose push channels")
        if eligibility_decision.reason_codes != ("eligibility-no-eligible-push-channel",):
            raise ValueError("no-channel decisions require canonical reasons")
    elif eligibility_decision.status in _BLOCKED_ELIGIBILITY_STATUSES:
        if eligibility_decision.source_eligible or eligibility_decision.outbox_candidate_eligible:
            raise ValueError("blocked eligibility decisions must not authorize source or outbox")
        if eligibility_decision.recovery_grace_applied:
            raise ValueError("blocked eligibility decisions must not apply recovery grace")
        if eligibility_decision.reason_codes not in _BLOCKED_ELIGIBILITY_REASON_CODES:
            raise ValueError("blocked eligibility decisions require canonical reasons")
    else:
        raise ValueError(
            "external recovery policy requires an accepted or blocked eligibility decision"
        )

    return source_intake_decision, source_event


def _validate_policy_context(
    *,
    context: NotificationExternalRecoveryPolicyContext,
    source_event: NotificationSourceEvent,
) -> None:
    if type(context) is not NotificationExternalRecoveryPolicyContext:
        raise ValueError("context must be NotificationExternalRecoveryPolicyContext")
    if context.account_id != source_event.account_id:
        raise ValueError("account_id must mirror the accepted source event")
    if context.beacon_id != source_event.beacon_id:
        raise ValueError("beacon_id must mirror the accepted source event")
    if context.source_fact_reference_id != source_event.source_fact_id:
        raise ValueError("source_fact_reference_id must mirror the accepted source event")
    _require_text(context.external_problem_reference_id, "external_problem_reference_id")


def _validate_external_problem_context(context: NotificationExternalRecoveryPolicyContext) -> None:
    if context.problem_gate_status not in _ALLOWED_EXTERNAL_GATE_STATUSES:
        raise ValueError("external recovery policy requires a supported external problem gate")
    if context.recovery_obligation_reference_id is not None:
        raise ValueError("external status decisions must not carry a recovery obligation reference")
    if context.recovery_result_already_consumed is not False:
        raise ValueError("external status decisions must not mark recovery as consumed")
    if context.problem_gate_status is NotificationExternalProblemGateStatus.MATERIAL_CHANGE:
        _require_text(context.material_change_reference_id, "material_change_reference_id")
    elif context.material_change_reference_id is not None:
        raise ValueError("only material change decisions may carry a material change reference")


def _validate_recovery_context(
    *,
    context: NotificationExternalRecoveryPolicyContext,
    eligibility_decision: NotificationEligibilityDecision,
    source_event: NotificationSourceEvent,
) -> None:
    if context.problem_gate_status is not NotificationExternalProblemGateStatus.NOT_APPLICABLE:
        raise ValueError("recovery decisions must use NOT_APPLICABLE as the problem gate")
    if context.material_change_reference_id is not None:
        raise ValueError("recovery decisions must not carry a material change reference")
    _require_text(context.recovery_obligation_reference_id, "recovery_obligation_reference_id")
    grace_evidence = eligibility_decision.context.recovery_grace_evidence
    if context.recovery_result_already_consumed != grace_evidence.recovery_result_already_consumed:
        raise ValueError("recovery result consumption must mirror the eligibility evidence")
    if eligibility_decision.recovery_grace_applied:
        if source_event.source_family is not NotificationSourceFamily.RECOVERY_SCAN_COMPLETED:
            raise ValueError("recovery grace decisions require a recovery scan result")
        if (
            context.recovery_obligation_reference_id
            != grace_evidence.recovery_obligation_reference_id
        ):
            raise ValueError("recovery grace obligation references must match")
        if grace_evidence.problem_began_while_access_active is not True:
            raise ValueError("recovery grace requires an access-active beginning")
        if grace_evidence.recovery_result_already_consumed is not False:
            raise ValueError("recovery grace requires an unconsumed recovery result")


def _validate_deduplication_decision(
    *,
    deduplication_decision: NotificationDeduplicationDecision,
    source_event: NotificationSourceEvent,
    semantic_effect_reference_id: str,
    strict_idempotency: bool,
) -> NotificationDeduplicationDecisionStatus:
    if type(deduplication_decision) is not NotificationDeduplicationDecision:
        raise ValueError("deduplication_decision must be NotificationDeduplicationDecision")

    request = deduplication_decision.request
    if type(request) is not NotificationDeduplicationRequest:
        raise ValueError("deduplication request must be NotificationDeduplicationRequest")
    if request.stage is not NotificationDeduplicationStage.OUTBOX_CREATION:
        raise ValueError("deduplication decisions must use OUTBOX_CREATION")
    if request.source_family is not source_event.source_family:
        raise ValueError("deduplication decisions must use the accepted source family")
    if request.account_id != source_event.account_id:
        raise ValueError("deduplication decisions must mirror the source account")
    if request.beacon_id != source_event.beacon_id:
        raise ValueError("deduplication decisions must mirror the source beacon")
    if request.channel_class is not None:
        raise ValueError("deduplication decisions must not carry a channel class")
    if request.semantic_effect_reference_id != semantic_effect_reference_id:
        raise ValueError("deduplication decisions must use the semantic effect reference")
    if request.proposed_record_state is not NotificationDeduplicationRecordState.PENDING:
        raise ValueError("deduplication decisions must propose the PENDING record state")
    if request.correlation_id != source_event.correlation_id:
        raise ValueError("deduplication decisions must mirror the source correlation id")
    if request.causation_id != source_event.causation_id:
        raise ValueError("deduplication decisions must mirror the source causation id")

    if request.idempotency_key is None:
        if strict_idempotency:
            raise ValueError("deduplication decisions require exact idempotency evidence")
    else:
        if type(request.idempotency_key) is not type(source_event.idempotency_key):
            raise ValueError("deduplication decisions must use exact idempotency types")
        if strict_idempotency and request.idempotency_key != source_event.idempotency_key:
            raise ValueError("deduplication decisions must use the source idempotency values")

    if request.idempotency_fingerprint is None:
        if strict_idempotency:
            raise ValueError("deduplication decisions require exact idempotency evidence")
    else:
        if type(request.idempotency_fingerprint) is not type(source_event.idempotency_fingerprint):
            raise ValueError("deduplication decisions must use exact idempotency types")
        if (
            strict_idempotency
            and request.idempotency_fingerprint != source_event.idempotency_fingerprint
        ):
            raise ValueError("deduplication decisions must use the source idempotency values")

    if request.idempotency_scope is None:
        if strict_idempotency:
            raise ValueError("deduplication decisions require exact idempotency evidence")
    else:
        if type(request.idempotency_scope) is not type(source_event.idempotency_scope):
            raise ValueError("deduplication decisions must use exact idempotency types")
        if strict_idempotency and request.idempotency_scope != source_event.idempotency_scope:
            raise ValueError("deduplication decisions must use the source idempotency values")

    status = deduplication_decision.status
    if status is NotificationDeduplicationDecisionStatus.NEW_EFFECT:
        if not deduplication_decision.effect_authorized:
            raise ValueError("new-effect dedup decisions must authorize the effect")
        if deduplication_decision.replayed or deduplication_decision.reconciliation_required:
            raise ValueError("new-effect dedup decisions must not replay or reconcile")
        if deduplication_decision.existing_record is not None:
            raise ValueError("new-effect dedup decisions must not carry an existing record")
        idempotency_decision = deduplication_decision.idempotency_decision
        assert idempotency_decision is not None
        if idempotency_decision.__class__.__module__ != "mayak.contracts.idempotency":
            raise ValueError("new-effect dedup decisions require the public idempotency contract")
        if idempotency_decision.__class__.__name__ != "IdempotencyDecision":
            raise ValueError("new-effect dedup decisions require the public idempotency contract")
        if idempotency_decision.value != "NEW":
            raise ValueError("new-effect dedup decisions require NEW idempotency")
        if deduplication_decision.reason_codes != ("dedup-new-effect",):
            raise ValueError("new-effect dedup decisions require canonical reasons")
        if (
            deduplication_decision.resulting_record is None
            or type(deduplication_decision.resulting_record) is not NotificationDeduplicationRecord
        ):
            raise ValueError("new-effect dedup decisions require a resulting record")
        resulting_record = deduplication_decision.resulting_record
        if resulting_record.record_state is not NotificationDeduplicationRecordState.PENDING:
            raise ValueError("new-effect dedup decisions require a PENDING resulting record")
        if resulting_record.semantic_effect_reference_id != request.semantic_effect_reference_id:
            raise ValueError(
                "new-effect dedup decisions must preserve the semantic effect reference"
            )
        if resulting_record.protected_result_reference_id != request.proposed_result_reference_id:
            raise ValueError("new-effect dedup decisions must preserve the result reference")
        if (
            resulting_record.correlation_id != request.correlation_id
            or resulting_record.causation_id != request.causation_id
        ):
            raise ValueError("new-effect dedup decisions must preserve correlation metadata")
        return status

    if status is NotificationDeduplicationDecisionStatus.REPLAY_TERMINAL:
        if (
            deduplication_decision.effect_authorized
            or deduplication_decision.reconciliation_required
        ):
            raise ValueError("terminal replays must not authorize new work")
        if not deduplication_decision.replayed:
            raise ValueError("terminal replays must be marked replayed")
        idempotency_decision = deduplication_decision.idempotency_decision
        assert idempotency_decision is not None
        if idempotency_decision.__class__.__module__ != "mayak.contracts.idempotency":
            raise ValueError("terminal replays require the public idempotency contract")
        if idempotency_decision.__class__.__name__ != "IdempotencyDecision":
            raise ValueError("terminal replays require the public idempotency contract")
        if idempotency_decision.value != "REPLAY_TERMINAL":
            raise ValueError("terminal replays require REPLAY_TERMINAL idempotency")
        if deduplication_decision.reason_codes != ("dedup-replay-terminal",):
            raise ValueError("terminal replays require canonical reasons")
        if deduplication_decision.existing_record is None or (
            deduplication_decision.resulting_record is not deduplication_decision.existing_record
        ):
            raise ValueError("terminal replays must reuse the existing record")
        if (
            deduplication_decision.existing_record.record_state
            is not NotificationDeduplicationRecordState.TERMINAL
        ):
            raise ValueError("terminal replays require a terminal existing record")
        return status

    if status is NotificationDeduplicationDecisionStatus.REPLAY_PENDING:
        if (
            deduplication_decision.effect_authorized
            or deduplication_decision.reconciliation_required
        ):
            raise ValueError("pending replays must not authorize new work")
        if not deduplication_decision.replayed:
            raise ValueError("pending replays must be marked replayed")
        idempotency_decision = deduplication_decision.idempotency_decision
        assert idempotency_decision is not None
        if idempotency_decision.__class__.__module__ != "mayak.contracts.idempotency":
            raise ValueError("pending replays require the public idempotency contract")
        if idempotency_decision.__class__.__name__ != "IdempotencyDecision":
            raise ValueError("pending replays require the public idempotency contract")
        if idempotency_decision.value != "PENDING":
            raise ValueError("pending replays require PENDING idempotency")
        if deduplication_decision.reason_codes != ("dedup-replay-pending",):
            raise ValueError("pending replays require canonical reasons")
        if deduplication_decision.existing_record is None or (
            deduplication_decision.resulting_record is not deduplication_decision.existing_record
        ):
            raise ValueError("pending replays must reuse the existing record")
        if (
            deduplication_decision.existing_record.record_state
            is not NotificationDeduplicationRecordState.PENDING
        ):
            raise ValueError("pending replays require a pending existing record")
        return status

    if status is NotificationDeduplicationDecisionStatus.RECONCILIATION_REQUIRED:
        if deduplication_decision.effect_authorized or not deduplication_decision.replayed:
            raise ValueError("reconciliation decisions must be replayed and unauthorized")
        if not deduplication_decision.reconciliation_required:
            raise ValueError("reconciliation decisions must mark reconciliation")
        idempotency_decision = deduplication_decision.idempotency_decision
        assert idempotency_decision is not None
        if idempotency_decision.__class__.__module__ != "mayak.contracts.idempotency":
            raise ValueError("reconciliation decisions require the public idempotency contract")
        if idempotency_decision.__class__.__name__ != "IdempotencyDecision":
            raise ValueError("reconciliation decisions require the public idempotency contract")
        if idempotency_decision.value != "RECONCILE_REQUIRED":
            raise ValueError("reconciliation decisions require RECONCILE_REQUIRED idempotency")
        if deduplication_decision.reason_codes != ("dedup-reconciliation-required",):
            raise ValueError("reconciliation decisions require canonical reasons")
        if deduplication_decision.existing_record is None or (
            deduplication_decision.resulting_record is not deduplication_decision.existing_record
        ):
            raise ValueError("reconciliation decisions must reuse the existing record")
        if (
            deduplication_decision.existing_record.record_state
            is not NotificationDeduplicationRecordState.AMBIGUOUS
        ):
            raise ValueError("reconciliation decisions require an ambiguous existing record")
        return status

    if status is NotificationDeduplicationDecisionStatus.MISSING_REQUIRED_IDEMPOTENCY:
        if (
            deduplication_decision.effect_authorized
            or deduplication_decision.replayed
            or deduplication_decision.reconciliation_required
        ):
            raise ValueError("missing-idempotency decisions must remain blocked")
        if deduplication_decision.idempotency_decision is not None:
            raise ValueError("missing-idempotency decisions must not carry an idempotency result")
        if deduplication_decision.reason_codes != ("dedup-missing-idempotency",):
            raise ValueError("missing-idempotency decisions require canonical reasons")
        if (
            request.idempotency_key is not None
            or request.idempotency_fingerprint is not None
            or request.idempotency_scope is not None
        ):
            raise ValueError("missing-idempotency decisions require empty idempotency evidence")
        if deduplication_decision.resulting_record is not None:
            raise ValueError("missing-idempotency decisions must not create a result record")
        return status

    if status is NotificationDeduplicationDecisionStatus.IDEMPOTENCY_MISMATCH:
        if (
            deduplication_decision.effect_authorized
            or deduplication_decision.replayed
            or deduplication_decision.reconciliation_required
        ):
            raise ValueError("idempotency mismatch decisions must remain blocked")
        idempotency_decision = deduplication_decision.idempotency_decision
        assert idempotency_decision is not None
        if idempotency_decision.__class__.__module__ != "mayak.contracts.idempotency":
            raise ValueError(
                "idempotency mismatch decisions require the public idempotency contract"
            )
        if idempotency_decision.__class__.__name__ != "IdempotencyDecision":
            raise ValueError(
                "idempotency mismatch decisions require the public idempotency contract"
            )
        if idempotency_decision.value != "MISMATCH":
            raise ValueError("idempotency mismatch decisions require MISMATCH idempotency")
        if deduplication_decision.reason_codes not in (
            ("dedup-idempotency-fingerprint-mismatch",),
            ("dedup-semantic-mismatch",),
        ):
            raise ValueError("idempotency mismatch decisions require canonical reasons")
        if deduplication_decision.resulting_record is not None:
            raise ValueError("idempotency mismatch decisions must not create a result record")
        if deduplication_decision.existing_record is None:
            raise ValueError("idempotency mismatch decisions require an existing record")
        return status

    raise ValueError("unsupported deduplication decision status")


def _validate_delivery_plan_decision(
    *,
    delivery_plan_decision: NotificationDeliveryPlanDecision,
    eligibility_decision: NotificationEligibilityDecision,
    source_event: NotificationSourceEvent,
) -> bool:
    if type(delivery_plan_decision) is not NotificationDeliveryPlanDecision:
        raise ValueError("delivery_plan_decision must be NotificationDeliveryPlanDecision")

    outbox_creation_decision = delivery_plan_decision.outbox_creation_decision
    outbox_creation_decision = _require_named_type(
        outbox_creation_decision,
        "outbox_creation_decision",
        module_name="mayak.modules.notification_delivery.outbox",
        class_name="NotificationOutboxCreationDecision",
    )  # type: ignore[assignment]
    outbox_item = outbox_creation_decision.outbox_item
    outbox_item = _require_named_type(
        outbox_item,
        "outbox_item",
        module_name="mayak.modules.notification_delivery.outbox",
        class_name="NotificationOutboxItem",
    )  # type: ignore[assignment]
    assert outbox_item is not None

    if outbox_creation_decision.eligibility_decision is not eligibility_decision:
        raise ValueError("delivery plan must belong to the supplied eligibility decision")
    if type(outbox_creation_decision.delivery_attempt_authorized) is not bool:
        raise ValueError(
            "delivery plan outbox creation must carry a bool delivery_attempt_authorized"
        )
    if type(outbox_creation_decision.outbox_item_created) is not bool:
        raise ValueError("delivery plan outbox creation must carry a bool outbox_item_created")
    if type(outbox_creation_decision.replayed) is not bool:
        raise ValueError("delivery plan outbox creation must carry a bool replay flag")
    if outbox_creation_decision.delivery_attempt_authorized is not False:
        raise ValueError("delivery plan outbox creation must not authorize delivery attempts")
    if outbox_creation_decision.outbox_item_created is not True:
        raise ValueError("delivery plan outbox creation must carry an accepted outbox item")
    if outbox_item.eligibility_decision_id != eligibility_decision.decision_id:
        raise ValueError("delivery plan outbox item must mirror the eligibility decision")
    if outbox_item.account_id != source_event.account_id:
        raise ValueError("delivery plan outbox item must mirror the source account")
    if outbox_item.beacon_id != source_event.beacon_id:
        raise ValueError("delivery plan outbox item must mirror the source beacon")
    if outbox_item.scan_run_id != source_event.scan_run_id:
        raise ValueError("delivery plan outbox item must mirror the source scan run")
    if outbox_item.source_event_id != source_event.source_event_id:
        raise ValueError("delivery plan outbox item must mirror the source event id")
    if outbox_item.source_fact_id != source_event.source_fact_id:
        raise ValueError("delivery plan outbox item must mirror the source fact id")
    if outbox_item.source_commit_reference != source_event.source_commit_reference:
        raise ValueError("delivery plan outbox item must mirror the source commit reference")
    if outbox_item.source_producer is not source_event.source_producer:
        raise ValueError("delivery plan outbox item must mirror the source producer")
    if outbox_item.source_contract != source_event.source_contract:
        raise ValueError("delivery plan outbox item must mirror the source contract")
    if outbox_item.source_contract_version != source_event.source_contract_version:
        raise ValueError("delivery plan outbox item must mirror the source contract version")
    if outbox_item.event_reason is not source_event.source_family:
        raise ValueError("delivery plan outbox item must mirror the source family")
    if outbox_item.listing_count != source_event.listing_count:
        raise ValueError("delivery plan outbox item must preserve the listing count")
    if outbox_item.safe_listing_reference_ids != source_event.safe_listing_reference_ids:
        raise ValueError("delivery plan outbox item must preserve all listing references")
    if outbox_item.correlation_id != source_event.correlation_id:
        raise ValueError("delivery plan outbox item must mirror the source correlation id")
    if outbox_item.causation_id != source_event.causation_id:
        raise ValueError("delivery plan outbox item must mirror the source causation id")
    if type(outbox_item.channel_intents) is not tuple or not outbox_item.channel_intents:
        raise ValueError("delivery plan outbox item must carry channel intents")
    if type(outbox_item.idempotency_key) is not type(source_event.idempotency_key):
        raise ValueError("delivery plan outbox item must preserve idempotency key types")
    if outbox_item.idempotency_key != source_event.idempotency_key:
        raise ValueError("delivery plan outbox item must preserve the idempotency key")
    if type(outbox_item.idempotency_fingerprint) is not type(source_event.idempotency_fingerprint):
        raise ValueError("delivery plan outbox item must preserve idempotency fingerprint types")
    if outbox_item.idempotency_fingerprint != source_event.idempotency_fingerprint:
        raise ValueError("delivery plan outbox item must preserve the idempotency fingerprint")
    if type(outbox_item.idempotency_scope) is not type(source_event.idempotency_scope):
        raise ValueError("delivery plan outbox item must preserve idempotency scope types")
    if outbox_item.idempotency_scope != source_event.idempotency_scope:
        raise ValueError("delivery plan outbox item must preserve the idempotency scope")
    if (
        outbox_item.channel_intents
        and tuple(intent.channel_class for intent in outbox_item.channel_intents)
        != eligibility_decision.eligible_push_channels
    ):
        raise ValueError("delivery plan outbox item channel intents must mirror the push channels")
    for intent in outbox_item.channel_intents:
        if intent.__class__.__module__ != "mayak.modules.notification_delivery.outbox":
            raise ValueError("delivery plan outbox item must use canonical channel intents")
        if intent.__class__.__name__ != "NotificationOutboxChannelIntent":
            raise ValueError("delivery plan outbox item must use canonical channel intents")

    if delivery_plan_decision.status is NotificationDeliveryPlanDecisionStatus.PLANNED:
        if (
            delivery_plan_decision.plan_created is not True
            or delivery_plan_decision.delivery_plan is None
        ):
            raise ValueError("planned delivery decisions require a delivery plan")
        if delivery_plan_decision.reason_codes != ("delivery-plan-created",):
            raise ValueError("planned delivery decisions require canonical reasons")
        delivery_plan = delivery_plan_decision.delivery_plan
        if type(delivery_plan) is not NotificationDeliveryPlan:
            raise ValueError("delivery plan must be NotificationDeliveryPlan")
        if (
            delivery_plan.authority
            is not NotificationDeliveryPlanAuthority.NOTIFICATION_DELIVERY_SERVER
        ):
            raise ValueError("delivery plan must use the notification-delivery authority")
        if delivery_plan.outbox_item is not outbox_item:
            raise ValueError("delivery plan must preserve the accepted outbox item")
        if delivery_plan.account_id != source_event.account_id:
            raise ValueError("delivery plan must mirror the source account")
        if delivery_plan.beacon_id != source_event.beacon_id:
            raise ValueError("delivery plan must mirror the source beacon")
        if delivery_plan.push_channel_classes != eligibility_decision.eligible_push_channels:
            raise ValueError("delivery plan push channels must mirror the eligibility decision")
        if not delivery_plan.web_status_read_model_planned:
            raise ValueError("delivery plan must keep the web read model planned")
        if delivery_plan.delivery_attempt_authorized is not False:
            raise ValueError("delivery plan must not authorize delivery attempts")
        if delivery_plan.provider_mapping_authorized is not False:
            raise ValueError("delivery plan must not authorize provider mapping")
        if type(delivery_plan.channel_entries) is not tuple or not delivery_plan.channel_entries:
            raise ValueError("delivery plan must carry channel entries")
        push_planned_channel_classes = tuple(
            entry.channel_class for entry in delivery_plan.channel_entries if entry.push_planned
        )
        if push_planned_channel_classes != eligibility_decision.eligible_push_channels:
            raise ValueError("delivery plan push projection must mirror eligibility")
        web_entries = [
            entry
            for entry in delivery_plan.channel_entries
            if entry.channel_class is NotificationChannelClass.WEB_STATUS_READ_MODEL
        ]
        if len(web_entries) != 1:
            raise ValueError("delivery plan must carry exactly one web read model entry")
        web_entry = web_entries[0]
        if web_entry.read_model_planned is not True or web_entry.push_planned:
            raise ValueError("web read model entries must remain read-model-only")
        for entry in delivery_plan.channel_entries:
            if type(entry) is not NotificationDeliveryChannelPlanEntry:
                raise ValueError("delivery plan must use canonical channel plan entries")
        return True

    if delivery_plan_decision.plan_created or delivery_plan_decision.delivery_plan is not None:
        raise ValueError("blocked delivery decisions must not carry a plan")
    if delivery_plan_decision.reason_codes not in _BLOCKED_PLAN_REASON_CODES:
        raise ValueError("blocked delivery decisions require canonical blocked reasons")
    if (
        delivery_plan_decision.status
        is NotificationDeliveryPlanDecisionStatus.BLOCKED_NO_PUSH_CHANNEL
    ):
        if eligibility_decision.eligible_push_channels:
            raise ValueError("blocked no-push-channel plans conflict with eligible push channels")
    if delivery_plan_decision.delivery_attempt_authorized is not False:
        raise ValueError("blocked delivery decisions must not authorize delivery attempts")
    if delivery_plan_decision.provider_mapping_authorized is not False:
        raise ValueError("blocked delivery decisions must not authorize provider mapping")
    return False


def _derived_effect_class(
    *,
    source_event: NotificationSourceEvent,
) -> NotificationExternalRecoveryEffectClass:
    if source_event.source_family is NotificationSourceFamily.EXTERNAL_UNAVAILABLE_STATUS:
        return NotificationExternalRecoveryEffectClass.AVITO_UNAVAILABLE_CONTINUING_SCAN
    if source_event.source_family is NotificationSourceFamily.LOST_ANCHORS_RECOVERED:
        return NotificationExternalRecoveryEffectClass.RECOVERY_RESULT_LOST_ANCHORS_RESTORED
    if source_event.listing_count > 0:
        return NotificationExternalRecoveryEffectClass.RECOVERY_RESULT_WITH_NEW_LISTINGS
    return NotificationExternalRecoveryEffectClass.RECOVERY_RESULT_NO_NEW_LISTINGS


def _build_decision(
    *,
    decision_id: str,
    eligibility_decision: NotificationEligibilityDecision,
    deduplication_decision: NotificationDeduplicationDecision | None,
    delivery_plan_decision: NotificationDeliveryPlanDecision | None,
    context: NotificationExternalRecoveryPolicyContext,
    effect_class: NotificationExternalRecoveryEffectClass,
    status: NotificationExternalRecoveryDecisionStatus,
    status_read_model_eligible: bool,
    push_work_eligible: bool,
    replayed: bool,
    reconciliation_required: bool,
    recovery_grace_applied: bool,
    evidence_reference_ids: tuple[str, ...],
) -> NotificationExternalRecoveryPolicyDecision:
    return NotificationExternalRecoveryPolicyDecision(
        decision_id=decision_id,
        authority=NotificationExternalRecoveryAuthority.NOTIFICATION_DELIVERY_SERVER,
        eligibility_decision=eligibility_decision,
        deduplication_decision=deduplication_decision,
        delivery_plan_decision=delivery_plan_decision,
        context=context,
        effect_class=effect_class,
        status=status,
        status_read_model_eligible=status_read_model_eligible,
        push_work_eligible=push_work_eligible,
        replayed=replayed,
        reconciliation_required=reconciliation_required,
        recovery_grace_applied=recovery_grace_applied,
        delivery_attempt_authorized=False,
        provider_mapping_authorized=False,
        reason_codes=_REASON_BY_STATUS[status.name],
        evidence_reference_ids=evidence_reference_ids,
    )


def evaluate_external_recovery_policy(
    *,
    decision_id: str,
    eligibility_decision: NotificationEligibilityDecision,
    deduplication_decision: NotificationDeduplicationDecision | None,
    delivery_plan_decision: NotificationDeliveryPlanDecision | None,
    context: NotificationExternalRecoveryPolicyContext,
    evidence_reference_ids: tuple[str, ...],
) -> NotificationExternalRecoveryPolicyDecision:
    _require_text(decision_id, "decision_id")
    _require_text_tuple(evidence_reference_ids, "evidence_reference_ids", allow_empty=True)

    _source_intake_decision, source_event = _validate_source_provenance(eligibility_decision)
    _validate_policy_context(context=context, source_event=source_event)

    if source_event.source_family is NotificationSourceFamily.EXTERNAL_UNAVAILABLE_STATUS:
        _validate_external_problem_context(context)
    else:
        _validate_recovery_context(
            context=context,
            eligibility_decision=eligibility_decision,
            source_event=source_event,
        )

    if context.problem_gate_status is NotificationExternalProblemGateStatus.AMBIGUOUS:
        if deduplication_decision is not None or delivery_plan_decision is not None:
            raise ValueError("ambiguous problem gate decisions must not carry downstream evidence")
        return _build_decision(
            decision_id=decision_id,
            eligibility_decision=eligibility_decision,
            deduplication_decision=None,
            delivery_plan_decision=None,
            context=context,
            effect_class=NotificationExternalRecoveryEffectClass.RECOVERY_BLOCKED_OR_AMBIGUOUS,
            status=NotificationExternalRecoveryDecisionStatus.BLOCKED_PROBLEM_GATE_AMBIGUOUS,
            status_read_model_eligible=eligibility_decision.status_read_model_eligible,
            push_work_eligible=False,
            replayed=False,
            reconciliation_required=False,
            recovery_grace_applied=eligibility_decision.recovery_grace_applied,
            evidence_reference_ids=_first_occurrence_union(
                eligibility_decision.evidence_reference_ids,
                context.evidence_reference_ids,
                evidence_reference_ids,
            ),
        )

    if (
        eligibility_decision.status
        is NotificationEligibilityStatus.BLOCKED_NO_ELIGIBLE_PUSH_CHANNEL
    ):
        if deduplication_decision is not None or delivery_plan_decision is not None:
            raise ValueError("no-channel decisions must not carry downstream work evidence")
        return _build_decision(
            decision_id=decision_id,
            eligibility_decision=eligibility_decision,
            deduplication_decision=None,
            delivery_plan_decision=None,
            context=context,
            effect_class=_derived_effect_class(source_event=source_event),
            status=NotificationExternalRecoveryDecisionStatus.READ_MODEL_ONLY_NO_ELIGIBLE_PUSH_CHANNEL,
            status_read_model_eligible=eligibility_decision.status_read_model_eligible,
            push_work_eligible=False,
            replayed=False,
            reconciliation_required=False,
            recovery_grace_applied=eligibility_decision.recovery_grace_applied,
            evidence_reference_ids=_first_occurrence_union(
                eligibility_decision.evidence_reference_ids,
                context.evidence_reference_ids,
                evidence_reference_ids,
            ),
        )

    if eligibility_decision.status in _BLOCKED_ELIGIBILITY_STATUSES:
        if deduplication_decision is not None or delivery_plan_decision is not None:
            raise ValueError(
                "blocked eligibility decisions must not carry downstream work evidence"
            )
        return _build_decision(
            decision_id=decision_id,
            eligibility_decision=eligibility_decision,
            deduplication_decision=None,
            delivery_plan_decision=None,
            context=context,
            effect_class=NotificationExternalRecoveryEffectClass.RECOVERY_BLOCKED_OR_AMBIGUOUS,
            status=NotificationExternalRecoveryDecisionStatus.BLOCKED_ELIGIBILITY,
            status_read_model_eligible=eligibility_decision.status_read_model_eligible,
            push_work_eligible=False,
            replayed=False,
            reconciliation_required=False,
            recovery_grace_applied=eligibility_decision.recovery_grace_applied,
            evidence_reference_ids=_first_occurrence_union(
                eligibility_decision.evidence_reference_ids,
                context.evidence_reference_ids,
                evidence_reference_ids,
            ),
        )

    if source_event.source_family is NotificationSourceFamily.EXTERNAL_UNAVAILABLE_STATUS:
        semantic_effect_reference_id = context.external_problem_reference_id
        if context.problem_gate_status is NotificationExternalProblemGateStatus.MATERIAL_CHANGE:
            semantic_effect_reference_id = (
                context.material_change_reference_id or semantic_effect_reference_id
            )

        if deduplication_decision is None:
            raise ValueError("external problem decisions require deduplication evidence")

        dedup_status = _validate_deduplication_decision(
            deduplication_decision=deduplication_decision,
            source_event=source_event,
            semantic_effect_reference_id=semantic_effect_reference_id,
            strict_idempotency=deduplication_decision.status
            not in (
                NotificationDeduplicationDecisionStatus.MISSING_REQUIRED_IDEMPOTENCY,
                NotificationDeduplicationDecisionStatus.IDEMPOTENCY_MISMATCH,
            ),
        )

        if dedup_status is NotificationDeduplicationDecisionStatus.NEW_EFFECT:
            if (
                context.problem_gate_status
                is NotificationExternalProblemGateStatus.SAME_PROBLEM_UNCHANGED
            ):
                raise ValueError("same-problem unchanged decisions must not create a new effect")
            if delivery_plan_decision is None:
                return _build_decision(
                    decision_id=decision_id,
                    eligibility_decision=eligibility_decision,
                    deduplication_decision=deduplication_decision,
                    delivery_plan_decision=None,
                    context=context,
                    effect_class=NotificationExternalRecoveryEffectClass.RECOVERY_BLOCKED_OR_AMBIGUOUS,
                    status=NotificationExternalRecoveryDecisionStatus.BLOCKED_CHANNEL_PLAN,
                    status_read_model_eligible=eligibility_decision.status_read_model_eligible,
                    push_work_eligible=False,
                    replayed=False,
                    reconciliation_required=False,
                    recovery_grace_applied=eligibility_decision.recovery_grace_applied,
                    evidence_reference_ids=_first_occurrence_union(
                        eligibility_decision.evidence_reference_ids,
                        deduplication_decision.evidence_reference_ids,
                        context.evidence_reference_ids,
                        evidence_reference_ids,
                    ),
                )
            if _validate_delivery_plan_decision(
                delivery_plan_decision=delivery_plan_decision,
                eligibility_decision=eligibility_decision,
                source_event=source_event,
            ):
                delivery_plan = delivery_plan_decision.delivery_plan
                assert delivery_plan is not None
                assert delivery_plan.outbox_item is not None
                if (
                    deduplication_decision.request.proposed_result_reference_id
                    != delivery_plan.outbox_item.outbox_item_id
                ):
                    raise ValueError(
                        "deduplication result references must match the planned outbox item"
                    )
                return _build_decision(
                    decision_id=decision_id,
                    eligibility_decision=eligibility_decision,
                    deduplication_decision=deduplication_decision,
                    delivery_plan_decision=delivery_plan_decision,
                    context=context,
                    effect_class=_derived_effect_class(source_event=source_event),
                    status=NotificationExternalRecoveryDecisionStatus.PUSH_WORK_ELIGIBLE,
                    status_read_model_eligible=eligibility_decision.status_read_model_eligible,
                    push_work_eligible=True,
                    replayed=False,
                    reconciliation_required=False,
                    recovery_grace_applied=eligibility_decision.recovery_grace_applied,
                    evidence_reference_ids=_first_occurrence_union(
                        eligibility_decision.evidence_reference_ids,
                        deduplication_decision.evidence_reference_ids,
                        delivery_plan_decision.evidence_reference_ids,
                        context.evidence_reference_ids,
                        evidence_reference_ids,
                    ),
                )
            return _build_decision(
                decision_id=decision_id,
                eligibility_decision=eligibility_decision,
                deduplication_decision=deduplication_decision,
                delivery_plan_decision=delivery_plan_decision,
                context=context,
                effect_class=NotificationExternalRecoveryEffectClass.RECOVERY_BLOCKED_OR_AMBIGUOUS,
                status=NotificationExternalRecoveryDecisionStatus.BLOCKED_CHANNEL_PLAN,
                status_read_model_eligible=eligibility_decision.status_read_model_eligible,
                push_work_eligible=False,
                replayed=False,
                reconciliation_required=False,
                recovery_grace_applied=eligibility_decision.recovery_grace_applied,
                evidence_reference_ids=_first_occurrence_union(
                    eligibility_decision.evidence_reference_ids,
                    deduplication_decision.evidence_reference_ids,
                    context.evidence_reference_ids,
                    evidence_reference_ids,
                ),
            )

        if dedup_status in _REPLAY_DECISION_TO_STATUS:
            if delivery_plan_decision is not None:
                raise ValueError("replay decisions must not carry a delivery plan decision")
            replay_status_name = _REPLAY_DECISION_TO_STATUS[dedup_status][0]
            return _build_decision(
                decision_id=decision_id,
                eligibility_decision=eligibility_decision,
                deduplication_decision=deduplication_decision,
                delivery_plan_decision=None,
                context=context,
                effect_class=_derived_effect_class(source_event=source_event),
                status=NotificationExternalRecoveryDecisionStatus[replay_status_name],
                status_read_model_eligible=eligibility_decision.status_read_model_eligible,
                push_work_eligible=False,
                replayed=True,
                reconciliation_required=False,
                recovery_grace_applied=eligibility_decision.recovery_grace_applied,
                evidence_reference_ids=_first_occurrence_union(
                    eligibility_decision.evidence_reference_ids,
                    deduplication_decision.evidence_reference_ids,
                    context.evidence_reference_ids,
                    evidence_reference_ids,
                ),
            )

        if dedup_status is NotificationDeduplicationDecisionStatus.RECONCILIATION_REQUIRED:
            if delivery_plan_decision is not None:
                raise ValueError("reconciliation decisions must not carry a delivery plan decision")
            return _build_decision(
                decision_id=decision_id,
                eligibility_decision=eligibility_decision,
                deduplication_decision=deduplication_decision,
                delivery_plan_decision=None,
                context=context,
                effect_class=NotificationExternalRecoveryEffectClass.RECOVERY_BLOCKED_OR_AMBIGUOUS,
                status=NotificationExternalRecoveryDecisionStatus.RECONCILIATION_REQUIRED,
                status_read_model_eligible=eligibility_decision.status_read_model_eligible,
                push_work_eligible=False,
                replayed=True,
                reconciliation_required=True,
                recovery_grace_applied=eligibility_decision.recovery_grace_applied,
                evidence_reference_ids=_first_occurrence_union(
                    eligibility_decision.evidence_reference_ids,
                    deduplication_decision.evidence_reference_ids,
                    context.evidence_reference_ids,
                    evidence_reference_ids,
                ),
            )

        if dedup_status in (
            NotificationDeduplicationDecisionStatus.MISSING_REQUIRED_IDEMPOTENCY,
            NotificationDeduplicationDecisionStatus.IDEMPOTENCY_MISMATCH,
        ):
            if delivery_plan_decision is not None:
                raise ValueError(
                    "idempotency-blocked decisions must not carry a delivery plan decision"
                )
            return _build_decision(
                decision_id=decision_id,
                eligibility_decision=eligibility_decision,
                deduplication_decision=deduplication_decision,
                delivery_plan_decision=None,
                context=context,
                effect_class=NotificationExternalRecoveryEffectClass.RECOVERY_BLOCKED_OR_AMBIGUOUS,
                status=NotificationExternalRecoveryDecisionStatus.BLOCKED_IDEMPOTENCY,
                status_read_model_eligible=eligibility_decision.status_read_model_eligible,
                push_work_eligible=False,
                replayed=False,
                reconciliation_required=False,
                recovery_grace_applied=eligibility_decision.recovery_grace_applied,
                evidence_reference_ids=_first_occurrence_union(
                    eligibility_decision.evidence_reference_ids,
                    deduplication_decision.evidence_reference_ids,
                    context.evidence_reference_ids,
                    evidence_reference_ids,
                ),
            )

        raise ValueError("external problem decisions require canonical deduplication evidence")

    if deduplication_decision is None:
        raise ValueError("recovery decisions require deduplication evidence")

    strict_idempotency = deduplication_decision.status not in (
        NotificationDeduplicationDecisionStatus.MISSING_REQUIRED_IDEMPOTENCY,
        NotificationDeduplicationDecisionStatus.IDEMPOTENCY_MISMATCH,
    )
    dedup_status = _validate_deduplication_decision(
        deduplication_decision=deduplication_decision,
        source_event=source_event,
        semantic_effect_reference_id=context.recovery_obligation_reference_id or "",
        strict_idempotency=strict_idempotency,
    )

    if dedup_status is NotificationDeduplicationDecisionStatus.NEW_EFFECT:
        if context.recovery_result_already_consumed:
            if delivery_plan_decision is not None:
                raise ValueError(
                    "consumed recovery decisions must not carry a delivery plan decision"
                )
            return _build_decision(
                decision_id=decision_id,
                eligibility_decision=eligibility_decision,
                deduplication_decision=deduplication_decision,
                delivery_plan_decision=None,
                context=context,
                effect_class=NotificationExternalRecoveryEffectClass.RECOVERY_BLOCKED_OR_AMBIGUOUS,
                status=NotificationExternalRecoveryDecisionStatus.BLOCKED_RECOVERY_ALREADY_CONSUMED,
                status_read_model_eligible=eligibility_decision.status_read_model_eligible,
                push_work_eligible=False,
                replayed=False,
                reconciliation_required=False,
                recovery_grace_applied=eligibility_decision.recovery_grace_applied,
                evidence_reference_ids=_first_occurrence_union(
                    eligibility_decision.evidence_reference_ids,
                    deduplication_decision.evidence_reference_ids,
                    context.evidence_reference_ids,
                    evidence_reference_ids,
                ),
            )
        if delivery_plan_decision is None:
            return _build_decision(
                decision_id=decision_id,
                eligibility_decision=eligibility_decision,
                deduplication_decision=deduplication_decision,
                delivery_plan_decision=None,
                context=context,
                effect_class=NotificationExternalRecoveryEffectClass.RECOVERY_BLOCKED_OR_AMBIGUOUS,
                status=NotificationExternalRecoveryDecisionStatus.BLOCKED_CHANNEL_PLAN,
                status_read_model_eligible=eligibility_decision.status_read_model_eligible,
                push_work_eligible=False,
                replayed=False,
                reconciliation_required=False,
                recovery_grace_applied=eligibility_decision.recovery_grace_applied,
                evidence_reference_ids=_first_occurrence_union(
                    eligibility_decision.evidence_reference_ids,
                    deduplication_decision.evidence_reference_ids,
                    context.evidence_reference_ids,
                    evidence_reference_ids,
                ),
            )
        if _validate_delivery_plan_decision(
            delivery_plan_decision=delivery_plan_decision,
            eligibility_decision=eligibility_decision,
            source_event=source_event,
        ):
            delivery_plan = delivery_plan_decision.delivery_plan
            assert delivery_plan is not None
            assert delivery_plan.outbox_item is not None
            if (
                deduplication_decision.request.proposed_result_reference_id
                != delivery_plan.outbox_item.outbox_item_id
            ):
                raise ValueError(
                    "deduplication result references must match the planned outbox item"
                )
            return _build_decision(
                decision_id=decision_id,
                eligibility_decision=eligibility_decision,
                deduplication_decision=deduplication_decision,
                delivery_plan_decision=delivery_plan_decision,
                context=context,
                effect_class=_derived_effect_class(source_event=source_event),
                status=NotificationExternalRecoveryDecisionStatus.PUSH_WORK_ELIGIBLE,
                status_read_model_eligible=eligibility_decision.status_read_model_eligible,
                push_work_eligible=True,
                replayed=False,
                reconciliation_required=False,
                recovery_grace_applied=eligibility_decision.recovery_grace_applied,
                evidence_reference_ids=_first_occurrence_union(
                    eligibility_decision.evidence_reference_ids,
                    deduplication_decision.evidence_reference_ids,
                    delivery_plan_decision.evidence_reference_ids,
                    context.evidence_reference_ids,
                    evidence_reference_ids,
                ),
            )
        return _build_decision(
            decision_id=decision_id,
            eligibility_decision=eligibility_decision,
            deduplication_decision=deduplication_decision,
            delivery_plan_decision=delivery_plan_decision,
            context=context,
            effect_class=NotificationExternalRecoveryEffectClass.RECOVERY_BLOCKED_OR_AMBIGUOUS,
            status=NotificationExternalRecoveryDecisionStatus.BLOCKED_CHANNEL_PLAN,
            status_read_model_eligible=eligibility_decision.status_read_model_eligible,
            push_work_eligible=False,
            replayed=False,
            reconciliation_required=False,
            recovery_grace_applied=eligibility_decision.recovery_grace_applied,
            evidence_reference_ids=_first_occurrence_union(
                eligibility_decision.evidence_reference_ids,
                deduplication_decision.evidence_reference_ids,
                context.evidence_reference_ids,
                evidence_reference_ids,
            ),
        )

    if dedup_status in _REPLAY_DECISION_TO_STATUS:
        if delivery_plan_decision is not None:
            raise ValueError("replay decisions must not carry a delivery plan decision")
        if (
            context.problem_gate_status.value
            == NotificationExternalProblemGateStatus.SAME_PROBLEM_UNCHANGED.value
        ):
            replay_status = NotificationExternalRecoveryDecisionStatus.PUSH_WORK_ELIGIBLE
        elif (
            source_event.source_family.value
            == NotificationSourceFamily.EXTERNAL_UNAVAILABLE_STATUS.value
        ):
            raise ValueError("same-problem replay evidence is inconsistent with problem gate")
        else:
            replay_status = NotificationExternalRecoveryDecisionStatus[
                _REPLAY_DECISION_TO_STATUS[dedup_status][0]
            ]
        return _build_decision(
            decision_id=decision_id,
            eligibility_decision=eligibility_decision,
            deduplication_decision=deduplication_decision,
            delivery_plan_decision=None,
            context=context,
            effect_class=_derived_effect_class(source_event=source_event),
            status=replay_status,
            status_read_model_eligible=eligibility_decision.status_read_model_eligible,
            push_work_eligible=False,
            replayed=True,
            reconciliation_required=False,
            recovery_grace_applied=eligibility_decision.recovery_grace_applied,
            evidence_reference_ids=_first_occurrence_union(
                eligibility_decision.evidence_reference_ids,
                deduplication_decision.evidence_reference_ids,
                context.evidence_reference_ids,
                evidence_reference_ids,
            ),
        )

    if dedup_status is NotificationDeduplicationDecisionStatus.RECONCILIATION_REQUIRED:
        if delivery_plan_decision is not None:
            raise ValueError("reconciliation decisions must not carry a delivery plan decision")
        return _build_decision(
            decision_id=decision_id,
            eligibility_decision=eligibility_decision,
            deduplication_decision=deduplication_decision,
            delivery_plan_decision=None,
            context=context,
            effect_class=NotificationExternalRecoveryEffectClass.RECOVERY_BLOCKED_OR_AMBIGUOUS,
            status=NotificationExternalRecoveryDecisionStatus.RECONCILIATION_REQUIRED,
            status_read_model_eligible=eligibility_decision.status_read_model_eligible,
            push_work_eligible=False,
            replayed=True,
            reconciliation_required=True,
            recovery_grace_applied=eligibility_decision.recovery_grace_applied,
            evidence_reference_ids=_first_occurrence_union(
                eligibility_decision.evidence_reference_ids,
                deduplication_decision.evidence_reference_ids,
                context.evidence_reference_ids,
                evidence_reference_ids,
            ),
        )

    if dedup_status in (
        NotificationDeduplicationDecisionStatus.MISSING_REQUIRED_IDEMPOTENCY,
        NotificationDeduplicationDecisionStatus.IDEMPOTENCY_MISMATCH,
    ):
        if delivery_plan_decision is not None:
            raise ValueError(
                "idempotency-blocked decisions must not carry a delivery plan decision"
            )
        return _build_decision(
            decision_id=decision_id,
            eligibility_decision=eligibility_decision,
            deduplication_decision=deduplication_decision,
            delivery_plan_decision=None,
            context=context,
            effect_class=NotificationExternalRecoveryEffectClass.RECOVERY_BLOCKED_OR_AMBIGUOUS,
            status=NotificationExternalRecoveryDecisionStatus.BLOCKED_IDEMPOTENCY,
            status_read_model_eligible=eligibility_decision.status_read_model_eligible,
            push_work_eligible=False,
            replayed=False,
            reconciliation_required=False,
            recovery_grace_applied=eligibility_decision.recovery_grace_applied,
            evidence_reference_ids=_first_occurrence_union(
                eligibility_decision.evidence_reference_ids,
                deduplication_decision.evidence_reference_ids,
                context.evidence_reference_ids,
                evidence_reference_ids,
            ),
        )

    raise ValueError("recovery decisions require canonical deduplication evidence")


__all__ = (
    "ND09_TASK_ID",
    "NotificationExternalRecoveryAuthority",
    "NotificationExternalRecoveryEffectClass",
    "NotificationExternalProblemGateStatus",
    "NotificationExternalRecoveryDecisionStatus",
    "NotificationExternalRecoveryPolicyContext",
    "NotificationExternalRecoveryPolicyDecision",
    "evaluate_external_recovery_policy",
)
