from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .assignment import (
    TransportAssignmentAuthority,
    TransportAssignmentCommitmentBoundary,
)
from .contracts import (
    DispatchAttempt,
    DispatchStatus,
    RouteLeaseStatus,
    RouteReconciliationStatus,
    RouteRestrictionStatus,
)

ER06C_TASK_ID = "ER-06C-FIRST-DISPATCH-ATTEMPT-BOUNDARY-20260715-012"

__all__ = (
    "ER06C_TASK_ID",
    "TransportDispatchAuthority",
    "TransportDispatchAttemptBoundary",
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


_RESOLVED_RECONCILIATION_STATUSES: frozenset[RouteReconciliationStatus] = frozenset(
    {
        RouteReconciliationStatus.NOT_REQUIRED,
        RouteReconciliationStatus.RESOLVED_NOT_SENT,
        RouteReconciliationStatus.RESOLVED_SENT,
        RouteReconciliationStatus.RESOLVED_TERMINAL,
    }
)


class TransportDispatchAuthority(str, Enum):
    EGRESS_ROUTING_SERVER = "EGRESS_ROUTING_SERVER"


@dataclass(frozen=True, slots=True)
class TransportDispatchAttemptBoundary:
    boundary_id: str
    authority: TransportDispatchAuthority
    assignment_commitment: TransportAssignmentCommitmentBoundary
    attempt: DispatchAttempt
    dispatch_state_committed: bool
    new_dispatch_effect_authorized: bool
    reason_codes: tuple[str, ...]
    evidence_reference_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        boundary_id = _require_text(self.boundary_id, "boundary_id")
        authority = _require_exact_enum(self.authority, TransportDispatchAuthority, "authority")
        assignment_commitment = _require_exact_record(
            self.assignment_commitment,
            TransportAssignmentCommitmentBoundary,
            "assignment_commitment",
        )
        attempt = _require_exact_record(self.attempt, DispatchAttempt, "attempt")
        dispatch_state_committed = _require_bool(
            self.dispatch_state_committed, "dispatch_state_committed"
        )
        new_dispatch_effect_authorized = _require_bool(
            self.new_dispatch_effect_authorized, "new_dispatch_effect_authorized"
        )
        reason_codes = _require_non_empty_text_tuple(self.reason_codes, "reason_codes")
        evidence_reference_ids = _require_non_empty_text_tuple(
            self.evidence_reference_ids, "evidence_reference_ids"
        )

        assert isinstance(authority, TransportDispatchAuthority)
        assert isinstance(assignment_commitment, TransportAssignmentCommitmentBoundary)
        assert isinstance(attempt, DispatchAttempt)

        object.__setattr__(self, "boundary_id", boundary_id)
        object.__setattr__(self, "authority", authority)
        object.__setattr__(self, "assignment_commitment", assignment_commitment)
        object.__setattr__(self, "attempt", attempt)
        object.__setattr__(self, "dispatch_state_committed", dispatch_state_committed)
        object.__setattr__(
            self, "new_dispatch_effect_authorized", new_dispatch_effect_authorized
        )
        object.__setattr__(self, "reason_codes", reason_codes)
        object.__setattr__(self, "evidence_reference_ids", evidence_reference_ids)

        if authority is not TransportDispatchAuthority.EGRESS_ROUTING_SERVER:
            raise ValueError("authority must be EGRESS_ROUTING_SERVER")
        if dispatch_state_committed is not True:
            raise ValueError("dispatch_state_committed must be True")

        if (
            assignment_commitment.authority
            is not TransportAssignmentAuthority.EGRESS_ROUTING_SERVER
        ):
            raise ValueError(
                "assignment_commitment.authority must be EGRESS_ROUTING_SERVER"
            )
        if assignment_commitment.assignment_committed is not True:
            raise ValueError(
                "assignment_commitment.assignment_committed must be True"
            )
        if assignment_commitment.lease_authorization.new_dispatch_authorized is not True:
            raise ValueError(
                "assignment_commitment.lease_authorization.new_dispatch_authorized "
                "must be True"
            )
        if assignment_commitment.lease_authorization.lease.status is not RouteLeaseStatus.GRANTED:
            raise ValueError(
                "assignment_commitment.lease_authorization.lease.status must be GRANTED"
            )
        if (
            assignment_commitment.lease_authorization.lease.restriction_snapshot
            is not RouteRestrictionStatus.NONE
        ):
            raise ValueError(
                "assignment_commitment.lease_authorization.lease.restriction_snapshot must be NONE"
            )
        if (
            assignment_commitment.lease_authorization.reconciliation_status
            not in _RESOLVED_RECONCILIATION_STATUSES
        ):
            raise ValueError(
                "assignment_commitment.lease_authorization.reconciliation_status must be resolved"
            )

        assignment = assignment_commitment.assignment
        _require_text(attempt.attempt_id, "attempt.attempt_id")
        _require_text(attempt.assignment_id, "attempt.assignment_id")
        _require_text(attempt.lease_id, "attempt.lease_id")
        _require_text(attempt.route_id, "attempt.route_id")
        _require_text(attempt.agent_id, "attempt.agent_id")
        attempt_dispatch_status = _require_exact_enum(
            attempt.dispatch_status, DispatchStatus, "attempt.dispatch_status"
        )
        attempt_ordinal = attempt.attempt_ordinal
        if type(attempt_ordinal) is not int or attempt_ordinal != 1:
            raise ValueError("attempt.attempt_ordinal must be 1")
        attempt_outcome_reference = attempt.outcome_reference
        if attempt_outcome_reference is not None:
            raise ValueError("attempt.outcome_reference must be None")
        attempt_reconciliation_required = _require_bool(
            attempt.reconciliation_required, "attempt.reconciliation_required"
        )
        _require_text(attempt.correlation_id, "attempt.correlation_id")
        _require_text(attempt.causation_id, "attempt.causation_id")

        assignment_id = _require_text(assignment.assignment_id, "assignment.assignment_id")
        assignment_lease_id = _require_text(assignment.lease_id, "assignment.lease_id")
        assignment_route_id = _require_text(assignment.route_id, "assignment.route_id")
        assignment_agent_id = _require_text(assignment.agent_id, "assignment.agent_id")
        assignment_correlation_id = _require_text(
            assignment.correlation_id, "assignment.correlation_id"
        )
        assignment_causation_id = _require_text(assignment.causation_id, "assignment.causation_id")

        if attempt.assignment_id != assignment_id:
            raise ValueError(
                "attempt.assignment_id must match "
                "assignment_commitment.assignment.assignment_id"
            )
        if attempt.lease_id != assignment_lease_id:
            raise ValueError(
                "attempt.lease_id must match assignment_commitment.assignment.lease_id"
            )
        if attempt.route_id != assignment_route_id:
            raise ValueError(
                "attempt.route_id must match assignment_commitment.assignment.route_id"
            )
        if attempt.agent_id != assignment_agent_id:
            raise ValueError(
                "attempt.agent_id must match assignment_commitment.assignment.agent_id"
            )
        if attempt.correlation_id != assignment_correlation_id:
            raise ValueError(
                "attempt.correlation_id must match assignment_commitment.assignment.correlation_id"
            )
        if attempt.causation_id != assignment_causation_id:
            raise ValueError(
                "attempt.causation_id must match assignment_commitment.assignment.causation_id"
            )

        if attempt_dispatch_status is DispatchStatus.UNKNOWN:
            if attempt_reconciliation_required is not True:
                raise ValueError(
                    "attempt.reconciliation_required must be True when "
                    "dispatch_status is UNKNOWN"
                )
            expected_authorization = False
        else:
            if attempt_reconciliation_required is not False:
                raise ValueError(
                    "attempt.reconciliation_required must be False unless "
                    "dispatch_status is UNKNOWN"
                )
            expected_authorization = attempt_dispatch_status is DispatchStatus.PENDING

        if attempt_dispatch_status is DispatchStatus.PENDING:
            if new_dispatch_effect_authorized is not True:
                raise ValueError("new_dispatch_effect_authorized must be True for PENDING")
        else:
            if new_dispatch_effect_authorized is not False:
                raise ValueError(
                    "new_dispatch_effect_authorized must be False unless "
                    "dispatch_status is PENDING"
                )

        if new_dispatch_effect_authorized is not expected_authorization:
            raise ValueError(
                "new_dispatch_effect_authorized does not match dispatch_status semantics"
            )
