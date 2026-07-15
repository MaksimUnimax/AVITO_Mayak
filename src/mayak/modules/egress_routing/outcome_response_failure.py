from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .assignment import TransportAssignmentCommitmentBoundary
from .contracts import (
    DispatchAttempt,
    DispatchStatus,
    RouteReconciliationStatus,
    TransportAssignment,
    TransportAssignmentOutcome,
    TransportOutcomeStatus,
)
from .dispatch import (
    TransportDispatchAttemptBoundary,
    TransportDispatchAuthority,
)

ER07D_TASK_ID = "ER-07D-TRANSPORT-RESPONSE-FAILURE-OUTCOME-BOUNDARY-20260715-021"

__all__ = (
    "ER07D_TASK_ID",
    "TransportResponseFailureOutcomeAuthority",
    "TransportResponseFailureOutcomeBoundary",
)


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


def _require_exact_enum(value: object, enum_cls: type[Enum], field_name: str) -> Enum:
    if type(value) is not enum_cls:
        raise ValueError(f"{field_name} must be {enum_cls.__name__}")
    return value


def _require_exact_record(value: object, record_cls: type[object], field_name: str) -> object:
    if type(value) is not record_cls:
        raise ValueError(f"{field_name} must be {record_cls.__name__}")
    return value


_ALLOWED_OUTCOME_STATUSES = frozenset(
    {
        TransportOutcomeStatus.RATE_OR_ACCESS_RESTRICTED,
        TransportOutcomeStatus.CAPTCHA_OR_CHALLENGE,
        TransportOutcomeStatus.PROVIDER_REJECTED,
        TransportOutcomeStatus.MALFORMED_RESPONSE_TRANSPORT_LAYER,
    }
)

_ALLOWED_RECONCILIATION_STATUSES = frozenset(
    {
        RouteReconciliationStatus.NOT_REQUIRED,
        RouteReconciliationStatus.RESOLVED_SENT,
        RouteReconciliationStatus.RESOLVED_TERMINAL,
    }
)


class TransportResponseFailureOutcomeAuthority(str, Enum):
    EGRESS_ROUTING_SERVER = "EGRESS_ROUTING_SERVER"


@dataclass(frozen=True, slots=True)
class TransportResponseFailureOutcomeBoundary:
    boundary_id: str
    authority: TransportResponseFailureOutcomeAuthority
    dispatch_attempt: TransportDispatchAttemptBoundary
    outcome: TransportAssignmentOutcome
    outcome_committed: bool
    new_dispatch_effect_authorized: bool
    assignment_terminal: bool
    parser_success_inferred: bool
    scan_success_inferred: bool
    notification_delivery_inferred: bool
    reason_codes: tuple[str, ...]
    evidence_reference_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        boundary_id = _require_text(self.boundary_id, "boundary_id")
        authority: TransportResponseFailureOutcomeAuthority = _require_exact_enum(
            self.authority,
            TransportResponseFailureOutcomeAuthority,
            "authority",
        )  # type: ignore[assignment]
        dispatch_attempt: TransportDispatchAttemptBoundary = _require_exact_record(
            self.dispatch_attempt,
            TransportDispatchAttemptBoundary,
            "dispatch_attempt",
        )  # type: ignore[assignment]
        assert isinstance(dispatch_attempt, TransportDispatchAttemptBoundary)
        outcome: TransportAssignmentOutcome = _require_exact_record(
            self.outcome,
            TransportAssignmentOutcome,
            "outcome",
        )  # type: ignore[assignment]
        assert isinstance(outcome, TransportAssignmentOutcome)
        outcome_committed = _require_bool(self.outcome_committed, "outcome_committed")
        new_dispatch_effect_authorized = _require_bool(
            self.new_dispatch_effect_authorized,
            "new_dispatch_effect_authorized",
        )
        assignment_terminal = _require_bool(self.assignment_terminal, "assignment_terminal")
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
        object.__setattr__(self, "dispatch_attempt", dispatch_attempt)
        object.__setattr__(self, "outcome", outcome)
        object.__setattr__(self, "outcome_committed", outcome_committed)
        object.__setattr__(self, "new_dispatch_effect_authorized", new_dispatch_effect_authorized)
        object.__setattr__(self, "assignment_terminal", assignment_terminal)
        object.__setattr__(self, "parser_success_inferred", parser_success_inferred)
        object.__setattr__(self, "scan_success_inferred", scan_success_inferred)
        object.__setattr__(
            self,
            "notification_delivery_inferred",
            notification_delivery_inferred,
        )
        object.__setattr__(self, "reason_codes", reason_codes)
        object.__setattr__(self, "evidence_reference_ids", evidence_reference_ids)

        if authority is not TransportResponseFailureOutcomeAuthority.EGRESS_ROUTING_SERVER:
            raise ValueError("authority must be EGRESS_ROUTING_SERVER")
        if outcome_committed is not True:
            raise ValueError("outcome_committed must be True")
        if new_dispatch_effect_authorized is not False:
            raise ValueError("new_dispatch_effect_authorized must be False")
        if assignment_terminal is not True:
            raise ValueError("assignment_terminal must be True")
        if parser_success_inferred is not False:
            raise ValueError("parser_success_inferred must be False")
        if scan_success_inferred is not False:
            raise ValueError("scan_success_inferred must be False")
        if notification_delivery_inferred is not False:
            raise ValueError("notification_delivery_inferred must be False")

        if dispatch_attempt.authority is not TransportDispatchAuthority.EGRESS_ROUTING_SERVER:
            raise ValueError("dispatch_attempt.authority must be EGRESS_ROUTING_SERVER")
        if dispatch_attempt.dispatch_state_committed is not True:
            raise ValueError("dispatch_attempt.dispatch_state_committed must be True")
        if dispatch_attempt.new_dispatch_effect_authorized is not False:
            raise ValueError("dispatch_attempt.new_dispatch_effect_authorized must be False")

        assignment_commitment: TransportAssignmentCommitmentBoundary = _require_exact_record(
            dispatch_attempt.assignment_commitment,
            TransportAssignmentCommitmentBoundary,
            "dispatch_attempt.assignment_commitment",
        )  # type: ignore[assignment]
        assignment_committed = _require_bool(
            assignment_commitment.assignment_committed,
            "dispatch_attempt.assignment_commitment.assignment_committed",
        )
        if assignment_committed is not True:
            raise ValueError(
                "dispatch_attempt.assignment_commitment.assignment_committed must be True"
            )

        attempt: DispatchAttempt = _require_exact_record(
            dispatch_attempt.attempt,
            DispatchAttempt,
            "dispatch_attempt.attempt",
        )  # type: ignore[assignment]
        _require_text(attempt.attempt_id, "dispatch_attempt.attempt.attempt_id")
        dispatch_status: DispatchStatus = _require_exact_enum(
            attempt.dispatch_status,
            DispatchStatus,
            "dispatch_attempt.attempt.dispatch_status",
        )  # type: ignore[assignment]
        if dispatch_status is not DispatchStatus.SENT:
            raise ValueError("dispatch_attempt.attempt.dispatch_status must be SENT")
        attempt_ordinal = attempt.attempt_ordinal
        if type(attempt_ordinal) is not int or attempt_ordinal != 1:
            raise ValueError("dispatch_attempt.attempt.attempt_ordinal must be 1")
        if attempt.outcome_reference is not None:
            raise ValueError("dispatch_attempt.attempt.outcome_reference must be None")
        reconciliation_required = _require_bool(
            attempt.reconciliation_required,
            "dispatch_attempt.attempt.reconciliation_required",
        )
        if reconciliation_required is not False:
            raise ValueError("dispatch_attempt.attempt.reconciliation_required must be False")

        assignment: TransportAssignment = _require_exact_record(
            assignment_commitment.assignment,
            TransportAssignment,
            "dispatch_attempt.assignment_commitment.assignment",
        )  # type: ignore[assignment]
        attempt_assignment_id = _require_text(
            attempt.assignment_id,
            "dispatch_attempt.attempt.assignment_id",
        )
        attempt_lease_id = _require_text(
            attempt.lease_id,
            "dispatch_attempt.attempt.lease_id",
        )
        attempt_route_id = _require_text(
            attempt.route_id,
            "dispatch_attempt.attempt.route_id",
        )
        attempt_agent_id = _require_text(
            attempt.agent_id,
            "dispatch_attempt.attempt.agent_id",
        )
        attempt_correlation_id = _require_text(
            attempt.correlation_id,
            "dispatch_attempt.attempt.correlation_id",
        )
        attempt_causation_id = _require_text(
            attempt.causation_id,
            "dispatch_attempt.attempt.causation_id",
        )

        assignment_id = _require_text(
            assignment.assignment_id,
            "dispatch_attempt.assignment_commitment.assignment.assignment_id",
        )
        assignment_lease_id = _require_text(
            assignment.lease_id,
            "dispatch_attempt.assignment_commitment.assignment.lease_id",
        )
        assignment_route_id = _require_text(
            assignment.route_id,
            "dispatch_attempt.assignment_commitment.assignment.route_id",
        )
        assignment_agent_id = _require_text(
            assignment.agent_id,
            "dispatch_attempt.assignment_commitment.assignment.agent_id",
        )
        assignment_correlation_id = _require_text(
            assignment.correlation_id,
            "dispatch_attempt.assignment_commitment.assignment.correlation_id",
        )
        assignment_causation_id = _require_text(
            assignment.causation_id,
            "dispatch_attempt.assignment_commitment.assignment.causation_id",
        )

        if attempt_assignment_id != assignment_id:
            raise ValueError("attempt.assignment_id must match assignment.assignment_id")
        if attempt_lease_id != assignment_lease_id:
            raise ValueError("attempt.lease_id must match assignment.lease_id")
        if attempt_route_id != assignment_route_id:
            raise ValueError("attempt.route_id must match assignment.route_id")
        if attempt_agent_id != assignment_agent_id:
            raise ValueError("attempt.agent_id must match assignment.agent_id")
        if attempt_correlation_id != assignment_correlation_id:
            raise ValueError("attempt.correlation_id must match assignment.correlation_id")
        if attempt_causation_id != assignment_causation_id:
            raise ValueError("attempt.causation_id must match assignment.causation_id")

        _require_text(outcome.outcome_id, "outcome.outcome_id")
        outcome_assignment_id = _require_text(outcome.assignment_id, "outcome.assignment_id")
        outcome_attempt_id = _require_text(outcome.attempt_id, "outcome.attempt_id")
        outcome_status: TransportOutcomeStatus = _require_exact_enum(
            outcome.status,
            TransportOutcomeStatus,
            "outcome.status",
        )  # type: ignore[assignment]
        if outcome_status not in _ALLOWED_OUTCOME_STATUSES:
            raise ValueError("outcome.status must be a transport failure outcome")
        _require_optional_text(
            outcome.safe_response_reference,
            "outcome.safe_response_reference",
        )
        _require_non_empty_text_tuple(outcome.reason_codes, "outcome.reason_codes")
        _require_non_empty_text_tuple(
            outcome.evidence_reference_ids,
            "outcome.evidence_reference_ids",
        )
        reconciliation_status: RouteReconciliationStatus = _require_exact_enum(
            outcome.reconciliation_status,
            RouteReconciliationStatus,
            "outcome.reconciliation_status",
        )  # type: ignore[assignment]
        if reconciliation_status not in _ALLOWED_RECONCILIATION_STATUSES:
            raise ValueError("outcome.reconciliation_status must be resolved")
        outcome_correlation_id = _require_text(
            outcome.correlation_id,
            "outcome.correlation_id",
        )
        outcome_causation_id = _require_text(
            outcome.causation_id,
            "outcome.causation_id",
        )

        if outcome_assignment_id != assignment_id:
            raise ValueError("outcome.assignment_id must match assignment.assignment_id")
        if outcome_attempt_id != attempt.attempt_id:
            raise ValueError("outcome.attempt_id must match attempt.attempt_id")
        if outcome_correlation_id != assignment_correlation_id:
            raise ValueError("outcome.correlation_id must match assignment.correlation_id")
        if outcome_causation_id != assignment_causation_id:
            raise ValueError("outcome.causation_id must match assignment.causation_id")
