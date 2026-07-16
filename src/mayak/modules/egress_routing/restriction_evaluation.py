from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TypeVar, cast

from .assignment import TransportAssignmentAuthority, TransportAssignmentCommitmentBoundary
from .contracts import (
    DispatchAttempt,
    DispatchStatus,
    TransportAssignment,
    TransportAssignmentOutcome,
    TransportOutcomeStatus,
)
from .dispatch import TransportDispatchAttemptBoundary, TransportDispatchAuthority
from .outcome_response_failure import (
    TransportResponseFailureOutcomeAuthority,
    TransportResponseFailureOutcomeBoundary,
)
from .restriction_signal import (
    TransportRestrictionSignalAuthority,
    TransportRestrictionSignalBoundary,
    TransportRestrictionSignalKind,
)

ER08B_TASK_ID = "ER-08B-RESTRICTION-QUARANTINE-EVALUATION-GATE-20260716-041"

__all__ = (
    "ER08B_TASK_ID",
    "TransportRestrictionEvaluationAuthority",
    "TransportRestrictionEvaluationGateBoundary",
)


def _require_text(value: object, field_name: str) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-blank string")
    return value


def _require_bool(value: object, field_name: str) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _require_tuple(value: object, field_name: str) -> tuple[object, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    return value


def _require_non_empty_text_tuple(value: object, field_name: str) -> tuple[str, ...]:
    items = _require_tuple(value, field_name)
    if not items:
        raise ValueError(f"{field_name} must not be empty")
    for item in items:
        _require_text(item, field_name)
    return items  # type: ignore[return-value]


E = TypeVar("E", bound=Enum)
T = TypeVar("T")


def _require_exact_enum(value: object, enum_cls: type[E], field_name: str) -> E:
    if type(value) is not enum_cls:
        raise ValueError(f"{field_name} must be {enum_cls.__name__}")
    return cast(E, value)


def _require_exact_record(value: object, record_cls: type[T], field_name: str) -> T:
    if type(value) is not record_cls:
        raise ValueError(f"{field_name} must be {record_cls.__name__}")
    return cast(T, value)


_ALLOWED_OUTCOME_KIND_BY_STATUS = {
    TransportOutcomeStatus.RATE_OR_ACCESS_RESTRICTED: (
        TransportRestrictionSignalKind.EXPLICIT_RESTRICTION
    ),
    TransportOutcomeStatus.CAPTCHA_OR_CHALLENGE: (
        TransportRestrictionSignalKind.EXPLICIT_CHALLENGE
    ),
}


class TransportRestrictionEvaluationAuthority(str, Enum):
    EGRESS_ROUTING_SERVER = "EGRESS_ROUTING_SERVER"


@dataclass(frozen=True, slots=True)
class TransportRestrictionEvaluationGateBoundary:
    boundary_id: str
    authority: TransportRestrictionEvaluationAuthority
    source_signal: TransportRestrictionSignalBoundary
    route_id: str
    evaluation_recorded: bool
    restriction_policy_gate_satisfied: bool
    quarantine_policy_gate_satisfied: bool
    protected_review_required: bool
    new_affected_lease_authorized: bool
    new_affected_assignment_authorized: bool
    restriction_state_commit_authorized: bool
    quarantine_decision_commit_authorized: bool
    fallback_effect_authorized: bool
    automatic_unquarantine_authorized: bool
    captcha_solving_authorized: bool
    captcha_bypass_authorized: bool
    parser_success_inferred: bool
    scan_success_inferred: bool
    notification_delivery_inferred: bool
    reason_codes: tuple[str, ...]
    evidence_reference_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        boundary_id = _require_text(self.boundary_id, "boundary_id")
        authority = _require_exact_enum(
            self.authority,
            TransportRestrictionEvaluationAuthority,
            "authority",
        )
        source_signal = _require_exact_record(
            self.source_signal,
            TransportRestrictionSignalBoundary,
            "source_signal",
        )
        route_id = _require_text(self.route_id, "route_id")
        evaluation_recorded = _require_bool(self.evaluation_recorded, "evaluation_recorded")
        restriction_policy_gate_satisfied = _require_bool(
            self.restriction_policy_gate_satisfied,
            "restriction_policy_gate_satisfied",
        )
        quarantine_policy_gate_satisfied = _require_bool(
            self.quarantine_policy_gate_satisfied,
            "quarantine_policy_gate_satisfied",
        )
        protected_review_required = _require_bool(
            self.protected_review_required,
            "protected_review_required",
        )
        new_affected_lease_authorized = _require_bool(
            self.new_affected_lease_authorized,
            "new_affected_lease_authorized",
        )
        new_affected_assignment_authorized = _require_bool(
            self.new_affected_assignment_authorized,
            "new_affected_assignment_authorized",
        )
        restriction_state_commit_authorized = _require_bool(
            self.restriction_state_commit_authorized,
            "restriction_state_commit_authorized",
        )
        quarantine_decision_commit_authorized = _require_bool(
            self.quarantine_decision_commit_authorized,
            "quarantine_decision_commit_authorized",
        )
        fallback_effect_authorized = _require_bool(
            self.fallback_effect_authorized,
            "fallback_effect_authorized",
        )
        automatic_unquarantine_authorized = _require_bool(
            self.automatic_unquarantine_authorized,
            "automatic_unquarantine_authorized",
        )
        captcha_solving_authorized = _require_bool(
            self.captcha_solving_authorized,
            "captcha_solving_authorized",
        )
        captcha_bypass_authorized = _require_bool(
            self.captcha_bypass_authorized,
            "captcha_bypass_authorized",
        )
        parser_success_inferred = _require_bool(
            self.parser_success_inferred,
            "parser_success_inferred",
        )
        scan_success_inferred = _require_bool(self.scan_success_inferred, "scan_success_inferred")
        notification_delivery_inferred = _require_bool(
            self.notification_delivery_inferred,
            "notification_delivery_inferred",
        )
        reason_codes = _require_non_empty_text_tuple(self.reason_codes, "reason_codes")
        evidence_reference_ids = _require_non_empty_text_tuple(
            self.evidence_reference_ids,
            "evidence_reference_ids",
        )

        object.__setattr__(self, "boundary_id", boundary_id)
        object.__setattr__(self, "authority", authority)
        object.__setattr__(self, "source_signal", source_signal)
        object.__setattr__(self, "route_id", route_id)
        object.__setattr__(self, "evaluation_recorded", evaluation_recorded)
        object.__setattr__(
            self,
            "restriction_policy_gate_satisfied",
            restriction_policy_gate_satisfied,
        )
        object.__setattr__(
            self,
            "quarantine_policy_gate_satisfied",
            quarantine_policy_gate_satisfied,
        )
        object.__setattr__(self, "protected_review_required", protected_review_required)
        object.__setattr__(
            self,
            "new_affected_lease_authorized",
            new_affected_lease_authorized,
        )
        object.__setattr__(
            self,
            "new_affected_assignment_authorized",
            new_affected_assignment_authorized,
        )
        object.__setattr__(
            self,
            "restriction_state_commit_authorized",
            restriction_state_commit_authorized,
        )
        object.__setattr__(
            self,
            "quarantine_decision_commit_authorized",
            quarantine_decision_commit_authorized,
        )
        object.__setattr__(self, "fallback_effect_authorized", fallback_effect_authorized)
        object.__setattr__(
            self,
            "automatic_unquarantine_authorized",
            automatic_unquarantine_authorized,
        )
        object.__setattr__(self, "captcha_solving_authorized", captcha_solving_authorized)
        object.__setattr__(self, "captcha_bypass_authorized", captcha_bypass_authorized)
        object.__setattr__(self, "parser_success_inferred", parser_success_inferred)
        object.__setattr__(self, "scan_success_inferred", scan_success_inferred)
        object.__setattr__(
            self,
            "notification_delivery_inferred",
            notification_delivery_inferred,
        )
        object.__setattr__(self, "reason_codes", reason_codes)
        object.__setattr__(self, "evidence_reference_ids", evidence_reference_ids)

        if authority is not TransportRestrictionEvaluationAuthority.EGRESS_ROUTING_SERVER:
            raise ValueError("authority must be EGRESS_ROUTING_SERVER")
        if evaluation_recorded is not True:
            raise ValueError("evaluation_recorded must be True")
        if restriction_policy_gate_satisfied is not False:
            raise ValueError("restriction_policy_gate_satisfied must be False")
        if quarantine_policy_gate_satisfied is not False:
            raise ValueError("quarantine_policy_gate_satisfied must be False")
        if protected_review_required is not True:
            raise ValueError("protected_review_required must be True")
        if new_affected_lease_authorized is not False:
            raise ValueError("new_affected_lease_authorized must be False")
        if new_affected_assignment_authorized is not False:
            raise ValueError("new_affected_assignment_authorized must be False")
        if restriction_state_commit_authorized is not False:
            raise ValueError("restriction_state_commit_authorized must be False")
        if quarantine_decision_commit_authorized is not False:
            raise ValueError("quarantine_decision_commit_authorized must be False")
        if fallback_effect_authorized is not False:
            raise ValueError("fallback_effect_authorized must be False")
        if automatic_unquarantine_authorized is not False:
            raise ValueError("automatic_unquarantine_authorized must be False")
        if captcha_solving_authorized is not False:
            raise ValueError("captcha_solving_authorized must be False")
        if captcha_bypass_authorized is not False:
            raise ValueError("captcha_bypass_authorized must be False")
        if parser_success_inferred is not False:
            raise ValueError("parser_success_inferred must be False")
        if scan_success_inferred is not False:
            raise ValueError("scan_success_inferred must be False")
        if notification_delivery_inferred is not False:
            raise ValueError("notification_delivery_inferred must be False")

        signal_authority = _require_exact_enum(
            source_signal.authority,
            TransportRestrictionSignalAuthority,
            "source_signal.authority",
        )
        signal_kind = _require_exact_enum(
            source_signal.signal_kind,
            TransportRestrictionSignalKind,
            "source_signal.signal_kind",
        )
        source_failure_boundary = _require_exact_record(
            source_signal.source_failure_boundary,
            TransportResponseFailureOutcomeBoundary,
            "source_signal.source_failure_boundary",
        )

        if signal_authority is not TransportRestrictionSignalAuthority.EGRESS_ROUTING_SERVER:
            raise ValueError("source_signal.authority must be EGRESS_ROUTING_SERVER")
        if (
            _require_bool(
                source_signal.signal_recorded,
                "source_signal.signal_recorded",
            )
            is not True
        ):
            raise ValueError("source_signal.signal_recorded must be True")
        if (
            _require_bool(
                source_signal.restriction_evaluation_required,
                "source_signal.restriction_evaluation_required",
            )
            is not True
        ):
            raise ValueError("source_signal.restriction_evaluation_required must be True")
        if (
            _require_bool(
                source_signal.quarantine_evaluation_required,
                "source_signal.quarantine_evaluation_required",
            )
            is not True
        ):
            raise ValueError("source_signal.quarantine_evaluation_required must be True")
        if (
            _require_bool(
                source_signal.route_state_mutation_authorized,
                "source_signal.route_state_mutation_authorized",
            )
            is not False
        ):
            raise ValueError("source_signal.route_state_mutation_authorized must be False")
        if (
            _require_bool(
                source_signal.fallback_effect_authorized,
                "source_signal.fallback_effect_authorized",
            )
            is not False
        ):
            raise ValueError("source_signal.fallback_effect_authorized must be False")
        if (
            _require_bool(
                source_signal.captcha_solving_authorized,
                "source_signal.captcha_solving_authorized",
            )
            is not False
        ):
            raise ValueError("source_signal.captcha_solving_authorized must be False")
        if (
            _require_bool(
                source_signal.captcha_bypass_authorized,
                "source_signal.captcha_bypass_authorized",
            )
            is not False
        ):
            raise ValueError("source_signal.captcha_bypass_authorized must be False")
        if (
            _require_bool(
                source_signal.parser_success_inferred,
                "source_signal.parser_success_inferred",
            )
            is not False
        ):
            raise ValueError("source_signal.parser_success_inferred must be False")
        if (
            _require_bool(
                source_signal.scan_success_inferred,
                "source_signal.scan_success_inferred",
            )
            is not False
        ):
            raise ValueError("source_signal.scan_success_inferred must be False")
        if (
            _require_bool(
                source_signal.notification_delivery_inferred,
                "source_signal.notification_delivery_inferred",
            )
            is not False
        ):
            raise ValueError("source_signal.notification_delivery_inferred must be False")
        _require_non_empty_text_tuple(source_signal.reason_codes, "source_signal.reason_codes")
        _require_non_empty_text_tuple(
            source_signal.evidence_reference_ids,
            "source_signal.evidence_reference_ids",
        )

        source_failure_authority = _require_exact_enum(
            source_failure_boundary.authority,
            TransportResponseFailureOutcomeAuthority,
            "source_signal.source_failure_boundary.authority",
        )
        if (
            source_failure_authority
            is not TransportResponseFailureOutcomeAuthority.EGRESS_ROUTING_SERVER
        ):
            raise ValueError(
                "source_signal.source_failure_boundary.authority must be EGRESS_ROUTING_SERVER"
            )
        if (
            _require_bool(
                source_failure_boundary.outcome_committed,
                "source_signal.source_failure_boundary.outcome_committed",
            )
            is not True
        ):
            raise ValueError(
                "source_signal.source_failure_boundary.outcome_committed must be True"
            )
        if (
            _require_bool(
                source_failure_boundary.new_dispatch_effect_authorized,
                "source_signal.source_failure_boundary.new_dispatch_effect_authorized",
            )
            is not False
        ):
            raise ValueError(
                "source_signal.source_failure_boundary.new_dispatch_effect_authorized must be False"
            )
        if (
            _require_bool(
                source_failure_boundary.assignment_terminal,
                "source_signal.source_failure_boundary.assignment_terminal",
            )
            is not True
        ):
            raise ValueError(
                "source_signal.source_failure_boundary.assignment_terminal must be True"
            )
        if (
            _require_bool(
                source_failure_boundary.parser_success_inferred,
                "source_signal.source_failure_boundary.parser_success_inferred",
            )
            is not False
        ):
            raise ValueError(
                "source_signal.source_failure_boundary.parser_success_inferred must be False"
            )
        if (
            _require_bool(
                source_failure_boundary.scan_success_inferred,
                "source_signal.source_failure_boundary.scan_success_inferred",
            )
            is not False
        ):
            raise ValueError(
                "source_signal.source_failure_boundary.scan_success_inferred must be False"
            )
        if (
            _require_bool(
                source_failure_boundary.notification_delivery_inferred,
                "source_signal.source_failure_boundary.notification_delivery_inferred",
            )
            is not False
        ):
            raise ValueError(
                "source_signal.source_failure_boundary.notification_delivery_inferred must be False"
            )
        _require_non_empty_text_tuple(
            source_failure_boundary.reason_codes,
            "source_signal.source_failure_boundary.reason_codes",
        )
        _require_non_empty_text_tuple(
            source_failure_boundary.evidence_reference_ids,
            "source_signal.source_failure_boundary.evidence_reference_ids",
        )

        dispatch_boundary = _require_exact_record(
            source_failure_boundary.dispatch_attempt,
            TransportDispatchAttemptBoundary,
            "source_signal.source_failure_boundary.dispatch_attempt",
        )
        outcome = _require_exact_record(
            source_failure_boundary.outcome,
            TransportAssignmentOutcome,
            "source_signal.source_failure_boundary.outcome",
        )

        dispatch_authority = _require_exact_enum(
            dispatch_boundary.authority,
            TransportDispatchAuthority,
            "source_signal.source_failure_boundary.dispatch_attempt.authority",
        )
        if dispatch_authority is not TransportDispatchAuthority.EGRESS_ROUTING_SERVER:
            raise ValueError(
                "source_signal.source_failure_boundary.dispatch_attempt.authority must be "
                "EGRESS_ROUTING_SERVER"
            )
        if (
            _require_bool(
                dispatch_boundary.dispatch_state_committed,
                "source_signal.source_failure_boundary.dispatch_attempt.dispatch_state_committed",
            )
            is not True
        ):
            raise ValueError(
                "source_signal.source_failure_boundary.dispatch_attempt.dispatch_state_committed "
                "must be True"
            )
        if (
            _require_bool(
                dispatch_boundary.new_dispatch_effect_authorized,
                "source_signal.source_failure_boundary.dispatch_attempt.new_dispatch_effect_authorized",
            )
            is not False
        ):
            raise ValueError(
                "source_signal.source_failure_boundary.dispatch_attempt."
                "new_dispatch_effect_authorized must be False"
            )
        _require_non_empty_text_tuple(
            dispatch_boundary.reason_codes,
            "source_signal.source_failure_boundary.dispatch_attempt.reason_codes",
        )
        _require_non_empty_text_tuple(
            dispatch_boundary.evidence_reference_ids,
            "source_signal.source_failure_boundary.dispatch_attempt.evidence_reference_ids",
        )

        assignment_commitment = _require_exact_record(
            dispatch_boundary.assignment_commitment,
            TransportAssignmentCommitmentBoundary,
            "source_signal.source_failure_boundary.dispatch_attempt.assignment_commitment",
        )
        assignment = _require_exact_record(
            assignment_commitment.assignment,
            TransportAssignment,
            "source_signal.source_failure_boundary.dispatch_attempt.assignment_commitment.assignment",
        )
        attempt = _require_exact_record(
            dispatch_boundary.attempt,
            DispatchAttempt,
            "source_signal.source_failure_boundary.dispatch_attempt.attempt",
        )

        assignment_commitment_authority = _require_exact_enum(
            assignment_commitment.authority,
            TransportAssignmentAuthority,
            "source_signal.source_failure_boundary.dispatch_attempt.assignment_commitment.authority",
        )
        if (
            assignment_commitment_authority
            is not TransportAssignmentAuthority.EGRESS_ROUTING_SERVER
        ):
            raise ValueError(
                "source_signal.source_failure_boundary.dispatch_attempt."
                "assignment_commitment.authority must be EGRESS_ROUTING_SERVER"
            )
        if (
            _require_bool(
                assignment_commitment.assignment_committed,
                "source_signal.source_failure_boundary.dispatch_attempt.assignment_commitment.assignment_committed",
            )
            is not True
        ):
            raise ValueError(
                "source_signal.source_failure_boundary.dispatch_attempt."
                "assignment_commitment.assignment_committed must be True"
            )
        _require_non_empty_text_tuple(
            assignment_commitment.reason_codes,
            "source_signal.source_failure_boundary.dispatch_attempt.assignment_commitment.reason_codes",
        )
        _require_non_empty_text_tuple(
            assignment_commitment.evidence_reference_ids,
            "source_signal.source_failure_boundary.dispatch_attempt.assignment_commitment.evidence_reference_ids",
        )

        attempt_status = _require_exact_enum(
            attempt.dispatch_status,
            DispatchStatus,
            "source_signal.source_failure_boundary.dispatch_attempt.attempt.dispatch_status",
        )
        if attempt_status is not DispatchStatus.SENT:
            raise ValueError(
                "source_signal.source_failure_boundary.dispatch_attempt.attempt.dispatch_status "
                "must be SENT"
            )
        if type(attempt.attempt_ordinal) is not int or attempt.attempt_ordinal != 1:
            raise ValueError(
                "source_signal.source_failure_boundary.dispatch_attempt.attempt.attempt_ordinal "
                "must be 1"
            )
        if attempt.outcome_reference is not None:
            raise ValueError(
                "source_signal.source_failure_boundary.dispatch_attempt.attempt.outcome_reference "
                "must be None"
            )
        if (
            _require_bool(
                attempt.reconciliation_required,
                "source_signal.source_failure_boundary.dispatch_attempt.attempt.reconciliation_required",
            )
            is not False
        ):
            raise ValueError(
                "source_signal.source_failure_boundary.dispatch_attempt.attempt."
                "reconciliation_required must be False"
            )

        outcome_status = _require_exact_enum(
            outcome.status,
            TransportOutcomeStatus,
            "source_signal.source_failure_boundary.outcome.status",
        )
        expected_signal_kind = _ALLOWED_OUTCOME_KIND_BY_STATUS.get(outcome_status)
        if expected_signal_kind is None:
            raise ValueError(
                "source_signal.source_failure_boundary.outcome.status must be "
                "RATE_OR_ACCESS_RESTRICTED or CAPTCHA_OR_CHALLENGE"
            )
        if signal_kind is not expected_signal_kind:
            raise ValueError("source_signal.signal_kind must match source outcome status")
        _require_non_empty_text_tuple(
            outcome.reason_codes,
            "source_signal.source_failure_boundary.outcome.reason_codes",
        )
        _require_non_empty_text_tuple(
            outcome.evidence_reference_ids,
            "source_signal.source_failure_boundary.outcome.evidence_reference_ids",
        )

        assignment_id = _require_text(
            assignment.assignment_id,
            "source_signal.source_failure_boundary.dispatch_attempt.assignment_commitment.assignment.assignment_id",
        )
        lease_id = _require_text(
            assignment.lease_id,
            "source_signal.source_failure_boundary.dispatch_attempt.assignment_commitment.assignment.lease_id",
        )
        assignment_route_id = _require_text(
            assignment.route_id,
            "source_signal.source_failure_boundary.dispatch_attempt.assignment_commitment.assignment.route_id",
        )
        agent_id = _require_text(
            assignment.agent_id,
            "source_signal.source_failure_boundary.dispatch_attempt.assignment_commitment.assignment.agent_id",
        )
        assignment_correlation_id = _require_text(
            assignment.correlation_id,
            "source_signal.source_failure_boundary.dispatch_attempt.assignment_commitment.assignment.correlation_id",
        )
        assignment_causation_id = _require_text(
            assignment.causation_id,
            "source_signal.source_failure_boundary.dispatch_attempt.assignment_commitment.assignment.causation_id",
        )
        attempt_assignment_id = _require_text(
            attempt.assignment_id,
            "source_signal.source_failure_boundary.dispatch_attempt.attempt.assignment_id",
        )
        attempt_lease_id = _require_text(
            attempt.lease_id,
            "source_signal.source_failure_boundary.dispatch_attempt.attempt.lease_id",
        )
        attempt_route_id = _require_text(
            attempt.route_id,
            "source_signal.source_failure_boundary.dispatch_attempt.attempt.route_id",
        )
        attempt_agent_id = _require_text(
            attempt.agent_id,
            "source_signal.source_failure_boundary.dispatch_attempt.attempt.agent_id",
        )
        attempt_correlation_id = _require_text(
            attempt.correlation_id,
            "source_signal.source_failure_boundary.dispatch_attempt.attempt.correlation_id",
        )
        attempt_causation_id = _require_text(
            attempt.causation_id,
            "source_signal.source_failure_boundary.dispatch_attempt.attempt.causation_id",
        )
        outcome_assignment_id = _require_text(
            outcome.assignment_id,
            "source_signal.source_failure_boundary.outcome.assignment_id",
        )
        outcome_attempt_id = _require_text(
            outcome.attempt_id,
            "source_signal.source_failure_boundary.outcome.attempt_id",
        )
        outcome_correlation_id = _require_text(
            outcome.correlation_id,
            "source_signal.source_failure_boundary.outcome.correlation_id",
        )
        outcome_causation_id = _require_text(
            outcome.causation_id,
            "source_signal.source_failure_boundary.outcome.causation_id",
        )
        if route_id != assignment_route_id:
            raise ValueError("route_id must match assignment.route_id")
        if attempt_route_id != assignment_route_id:
            raise ValueError("attempt.route_id must match assignment.route_id")
        if attempt_assignment_id != assignment_id:
            raise ValueError("attempt.assignment_id must match assignment.assignment_id")
        if attempt_lease_id != lease_id:
            raise ValueError("attempt.lease_id must match assignment.lease_id")
        if attempt_agent_id != agent_id:
            raise ValueError("attempt.agent_id must match assignment.agent_id")
        if attempt_correlation_id != assignment_correlation_id:
            raise ValueError("attempt.correlation_id must match assignment.correlation_id")
        if attempt_causation_id != assignment_causation_id:
            raise ValueError("attempt.causation_id must match assignment.causation_id")
        if outcome_assignment_id != assignment_id:
            raise ValueError("outcome.assignment_id must match assignment.assignment_id")
        if outcome_attempt_id != attempt.attempt_id:
            raise ValueError("outcome.attempt_id must match attempt.attempt_id")
        if outcome_correlation_id != assignment_correlation_id:
            raise ValueError("outcome.correlation_id must match assignment.correlation_id")
        if outcome_causation_id != assignment_causation_id:
            raise ValueError("outcome.causation_id must match assignment.causation_id")
