from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .contracts import (
    DispatchStatus,
    RouteReconciliationStatus,
    TransportAssignmentOutcome,
    TransportOutcomeStatus,
)
from .dispatch import TransportDispatchAttemptBoundary, TransportDispatchAuthority

ER07B_TASK_ID = "ER-07B-TRANSPORT-AVAILABILITY-OUTCOME-BOUNDARY-20260715-017"

__all__ = (
    "ER07B_TASK_ID",
    "TransportAvailabilityOutcomeAuthority",
    "TransportAvailabilityOutcomeBoundary",
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


def _require_exact_enum(value: object, enum_cls: type[Enum], field_name: str) -> Enum:
    if type(value) is not enum_cls:
        raise ValueError(f"{field_name} must be {enum_cls.__name__}")
    return value


def _require_exact_record(value: object, record_cls: type[object], field_name: str) -> object:
    if type(value) is not record_cls:
        raise ValueError(f"{field_name} must be {record_cls.__name__}")
    return value


_DISPATCH_OUTCOME_MATRIX: dict[DispatchStatus, TransportOutcomeStatus] = {
    DispatchStatus.NOT_SENT: TransportOutcomeStatus.TRANSPORT_UNAVAILABLE,
    DispatchStatus.SENT: TransportOutcomeStatus.TRANSPORT_TIMEOUT,
    DispatchStatus.UNKNOWN: TransportOutcomeStatus.TRANSPORT_AMBIGUOUS,
}

_OUTCOME_RECONCILIATION_MATRIX: dict[
    TransportOutcomeStatus, frozenset[RouteReconciliationStatus]
] = {
    TransportOutcomeStatus.TRANSPORT_UNAVAILABLE: frozenset(
        {
            RouteReconciliationStatus.NOT_REQUIRED,
            RouteReconciliationStatus.RESOLVED_NOT_SENT,
            RouteReconciliationStatus.RESOLVED_TERMINAL,
        }
    ),
    TransportOutcomeStatus.TRANSPORT_TIMEOUT: frozenset(
        {
            RouteReconciliationStatus.NOT_REQUIRED,
            RouteReconciliationStatus.RESOLVED_SENT,
            RouteReconciliationStatus.RESOLVED_TERMINAL,
        }
    ),
    TransportOutcomeStatus.TRANSPORT_AMBIGUOUS: frozenset(
        {
            RouteReconciliationStatus.REQUIRED,
            RouteReconciliationStatus.PENDING,
            RouteReconciliationStatus.REMAINS_AMBIGUOUS,
            RouteReconciliationStatus.MANUAL_REVIEW_REQUIRED,
        }
    ),
}


class TransportAvailabilityOutcomeAuthority(str, Enum):
    EGRESS_ROUTING_SERVER = "EGRESS_ROUTING_SERVER"


@dataclass(frozen=True, slots=True)
class TransportAvailabilityOutcomeBoundary:
    boundary_id: str
    authority: TransportAvailabilityOutcomeAuthority
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
        authority = _require_exact_enum(
            self.authority, TransportAvailabilityOutcomeAuthority, "authority"
        )
        dispatch_attempt = _require_exact_record(
            self.dispatch_attempt, TransportDispatchAttemptBoundary, "dispatch_attempt"
        )
        outcome = _require_exact_record(self.outcome, TransportAssignmentOutcome, "outcome")
        outcome_committed = _require_bool(self.outcome_committed, "outcome_committed")
        new_dispatch_effect_authorized = _require_bool(
            self.new_dispatch_effect_authorized, "new_dispatch_effect_authorized"
        )
        assignment_terminal = _require_bool(self.assignment_terminal, "assignment_terminal")
        parser_success_inferred = _require_bool(
            self.parser_success_inferred, "parser_success_inferred"
        )
        scan_success_inferred = _require_bool(self.scan_success_inferred, "scan_success_inferred")
        notification_delivery_inferred = _require_bool(
            self.notification_delivery_inferred, "notification_delivery_inferred"
        )
        reason_codes = _require_non_empty_text_tuple(self.reason_codes, "reason_codes")
        evidence_reference_ids = _require_non_empty_text_tuple(
            self.evidence_reference_ids, "evidence_reference_ids"
        )

        assert isinstance(authority, TransportAvailabilityOutcomeAuthority)
        assert isinstance(dispatch_attempt, TransportDispatchAttemptBoundary)
        assert isinstance(outcome, TransportAssignmentOutcome)

        object.__setattr__(self, "boundary_id", boundary_id)
        object.__setattr__(self, "authority", authority)
        object.__setattr__(self, "dispatch_attempt", dispatch_attempt)
        object.__setattr__(self, "outcome", outcome)
        object.__setattr__(self, "outcome_committed", outcome_committed)
        object.__setattr__(
            self, "new_dispatch_effect_authorized", new_dispatch_effect_authorized
        )
        object.__setattr__(self, "assignment_terminal", assignment_terminal)
        object.__setattr__(self, "parser_success_inferred", parser_success_inferred)
        object.__setattr__(self, "scan_success_inferred", scan_success_inferred)
        object.__setattr__(
            self, "notification_delivery_inferred", notification_delivery_inferred
        )
        object.__setattr__(self, "reason_codes", reason_codes)
        object.__setattr__(self, "evidence_reference_ids", evidence_reference_ids)

        if authority is not TransportAvailabilityOutcomeAuthority.EGRESS_ROUTING_SERVER:
            raise ValueError("authority must be EGRESS_ROUTING_SERVER")
        if outcome_committed is not True:
            raise ValueError("outcome_committed must be True")
        if new_dispatch_effect_authorized is not False:
            raise ValueError("new_dispatch_effect_authorized must be False")
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

        assignment_commitment = dispatch_attempt.assignment_commitment
        attempt = dispatch_attempt.attempt
        assignment = assignment_commitment.assignment

        if assignment_commitment.assignment_committed is not True:
            raise ValueError(
                "dispatch_attempt.assignment_commitment.assignment_committed must be True"
            )
        attempt_id = _require_text(attempt.attempt_id, "dispatch_attempt.attempt.attempt_id")
        attempt_assignment_id = _require_text(
            attempt.assignment_id, "dispatch_attempt.attempt.assignment_id"
        )
        attempt_lease_id = _require_text(attempt.lease_id, "dispatch_attempt.attempt.lease_id")
        attempt_route_id = _require_text(attempt.route_id, "dispatch_attempt.attempt.route_id")
        attempt_agent_id = _require_text(attempt.agent_id, "dispatch_attempt.attempt.agent_id")
        attempt_correlation_id = _require_text(
            attempt.correlation_id, "dispatch_attempt.attempt.correlation_id"
        )
        attempt_causation_id = _require_text(
            attempt.causation_id, "dispatch_attempt.attempt.causation_id"
        )
        if type(attempt.attempt_ordinal) is not int or attempt.attempt_ordinal != 1:
            raise ValueError("dispatch_attempt.attempt.attempt_ordinal must be 1")
        if attempt.outcome_reference is not None:
            raise ValueError("dispatch_attempt.attempt.outcome_reference must be None")

        assignment_id = _require_text(assignment.assignment_id, "assignment.assignment_id")
        lease_id = _require_text(assignment.lease_id, "assignment.lease_id")
        route_id = _require_text(assignment.route_id, "assignment.route_id")
        agent_id = _require_text(assignment.agent_id, "assignment.agent_id")
        correlation_id = _require_text(assignment.correlation_id, "assignment.correlation_id")
        causation_id = _require_text(assignment.causation_id, "assignment.causation_id")

        if attempt_assignment_id != assignment_id:
            raise ValueError("dispatch_attempt.attempt.assignment_id must match assignment_id")
        if attempt_lease_id != lease_id:
            raise ValueError("dispatch_attempt.attempt.lease_id must match lease_id")
        if attempt_route_id != route_id:
            raise ValueError("dispatch_attempt.attempt.route_id must match route_id")
        if attempt_agent_id != agent_id:
            raise ValueError("dispatch_attempt.attempt.agent_id must match agent_id")
        if attempt_correlation_id != correlation_id:
            raise ValueError("dispatch_attempt.attempt.correlation_id must match correlation_id")
        if attempt_causation_id != causation_id:
            raise ValueError("dispatch_attempt.attempt.causation_id must match causation_id")

        _require_text(outcome.outcome_id, "outcome.outcome_id")
        outcome_assignment_id = _require_text(outcome.assignment_id, "outcome.assignment_id")
        outcome_attempt_id = _require_text(outcome.attempt_id, "outcome.attempt_id")
        outcome_correlation_id = _require_text(outcome.correlation_id, "outcome.correlation_id")
        outcome_causation_id = _require_text(outcome.causation_id, "outcome.causation_id")
        outcome_reason_codes = _require_non_empty_text_tuple(
            outcome.reason_codes, "outcome.reason_codes"
        )
        outcome_evidence_reference_ids = _require_non_empty_text_tuple(
            outcome.evidence_reference_ids, "outcome.evidence_reference_ids"
        )
        if outcome_assignment_id != assignment_id:
            raise ValueError("outcome.assignment_id must match assignment.assignment_id")
        if outcome_attempt_id != attempt_id:
            raise ValueError("outcome.attempt_id must match dispatch_attempt.attempt.attempt_id")
        if outcome_correlation_id != correlation_id:
            raise ValueError("outcome.correlation_id must match assignment.correlation_id")
        if outcome_causation_id != causation_id:
            raise ValueError("outcome.causation_id must match assignment.causation_id")
        if outcome.safe_response_reference is not None:
            raise ValueError("outcome.safe_response_reference must be None")

        dispatch_status = _require_exact_enum(
            attempt.dispatch_status, DispatchStatus, "dispatch_attempt.attempt.dispatch_status"
        )
        outcome_status = _require_exact_enum(
            outcome.status,
            TransportOutcomeStatus,
            "outcome.status",
        )
        if dispatch_status not in _DISPATCH_OUTCOME_MATRIX:
            raise ValueError("dispatch_attempt.attempt.dispatch_status is not allowed")
        if _DISPATCH_OUTCOME_MATRIX[dispatch_status] is not outcome_status:
            raise ValueError("dispatch_attempt.attempt.dispatch_status and outcome.status mismatch")

        if outcome_status not in _OUTCOME_RECONCILIATION_MATRIX:
            raise ValueError("outcome.status is not allowed")
        if outcome.reconciliation_status not in _OUTCOME_RECONCILIATION_MATRIX[outcome_status]:
            raise ValueError("outcome.reconciliation_status is incompatible with outcome.status")
        if not outcome_reason_codes:
            raise ValueError("outcome.reason_codes must not be empty")
        if not outcome_evidence_reference_ids:
            raise ValueError("outcome.evidence_reference_ids must not be empty")
        if outcome_status is TransportOutcomeStatus.TRANSPORT_AMBIGUOUS:
            if assignment_terminal is not False:
                raise ValueError("assignment_terminal must be False for TRANSPORT_AMBIGUOUS")
        else:
            if assignment_terminal is not True:
                raise ValueError("assignment_terminal must be True for terminal transport outcomes")

        object.__setattr__(self, "outcome", outcome)
