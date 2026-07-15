from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .contracts import DispatchStatus, RouteReconciliationState, RouteReconciliationStatus
from .dispatch import TransportDispatchAttemptBoundary, TransportDispatchAuthority

ER06E_TASK_ID = "ER-06E-UNKNOWN-DISPATCH-RECONCILIATION-BOUNDARY-20260715-014"

__all__ = (
    "ER06E_TASK_ID",
    "TransportDispatchReconciliationAuthority",
    "TransportDispatchReconciliationBoundary",
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


_UNRESOLVED_RECONCILIATION_STATUSES = frozenset(
    {
        RouteReconciliationStatus.REQUIRED,
        RouteReconciliationStatus.PENDING,
        RouteReconciliationStatus.REMAINS_AMBIGUOUS,
        RouteReconciliationStatus.MANUAL_REVIEW_REQUIRED,
    }
)


class TransportDispatchReconciliationAuthority(str, Enum):
    EGRESS_ROUTING_SERVER = "EGRESS_ROUTING_SERVER"


@dataclass(frozen=True, slots=True)
class TransportDispatchReconciliationBoundary:
    boundary_id: str
    authority: TransportDispatchReconciliationAuthority
    dispatch_attempt: TransportDispatchAttemptBoundary
    reconciliation_state: RouteReconciliationState
    reconciliation_state_committed: bool
    new_dispatch_effect_authorized: bool
    assignment_terminal: bool
    reason_codes: tuple[str, ...]
    evidence_reference_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        boundary_id = _require_text(self.boundary_id, "boundary_id")
        authority = _require_exact_enum(
            self.authority,
            TransportDispatchReconciliationAuthority,
            "authority",
        )
        dispatch_attempt = _require_exact_record(
            self.dispatch_attempt,
            TransportDispatchAttemptBoundary,
            "dispatch_attempt",
        )
        reconciliation_state = _require_exact_record(
            self.reconciliation_state,
            RouteReconciliationState,
            "reconciliation_state",
        )
        reconciliation_state_committed = _require_bool(
            self.reconciliation_state_committed,
            "reconciliation_state_committed",
        )
        new_dispatch_effect_authorized = _require_bool(
            self.new_dispatch_effect_authorized,
            "new_dispatch_effect_authorized",
        )
        assignment_terminal = _require_bool(self.assignment_terminal, "assignment_terminal")
        reason_codes = _require_non_empty_text_tuple(self.reason_codes, "reason_codes")
        evidence_reference_ids = _require_non_empty_text_tuple(
            self.evidence_reference_ids,
            "evidence_reference_ids",
        )

        assert isinstance(authority, TransportDispatchReconciliationAuthority)
        assert isinstance(dispatch_attempt, TransportDispatchAttemptBoundary)
        assert isinstance(reconciliation_state, RouteReconciliationState)

        object.__setattr__(self, "boundary_id", boundary_id)
        object.__setattr__(self, "authority", authority)
        object.__setattr__(self, "dispatch_attempt", dispatch_attempt)
        object.__setattr__(self, "reconciliation_state", reconciliation_state)
        object.__setattr__(
            self,
            "reconciliation_state_committed",
            reconciliation_state_committed,
        )
        object.__setattr__(
            self,
            "new_dispatch_effect_authorized",
            new_dispatch_effect_authorized,
        )
        object.__setattr__(self, "assignment_terminal", assignment_terminal)
        object.__setattr__(self, "reason_codes", reason_codes)
        object.__setattr__(self, "evidence_reference_ids", evidence_reference_ids)

        if authority is not TransportDispatchReconciliationAuthority.EGRESS_ROUTING_SERVER:
            raise ValueError("authority must be EGRESS_ROUTING_SERVER")
        if dispatch_attempt.authority is not TransportDispatchAuthority.EGRESS_ROUTING_SERVER:
            raise ValueError("dispatch_attempt.authority must be EGRESS_ROUTING_SERVER")
        if dispatch_attempt.dispatch_state_committed is not True:
            raise ValueError("dispatch_attempt.dispatch_state_committed must be True")
        if dispatch_attempt.new_dispatch_effect_authorized is not False:
            raise ValueError("dispatch_attempt.new_dispatch_effect_authorized must be False")

        attempt = dispatch_attempt.attempt
        dispatch_status = _require_exact_enum(
            attempt.dispatch_status,
            DispatchStatus,
            "dispatch_status",
        )
        if dispatch_status is not DispatchStatus.UNKNOWN:
            raise ValueError("dispatch_attempt.attempt.dispatch_status must be UNKNOWN")
        if attempt.attempt_ordinal != 1:
            raise ValueError("dispatch_attempt.attempt.attempt_ordinal must be 1")
        if attempt.outcome_reference is not None:
            raise ValueError("dispatch_attempt.attempt.outcome_reference must be None")
        if attempt.reconciliation_required is not True:
            raise ValueError("dispatch_attempt.attempt.reconciliation_required must be True")

        reconciliation_id = _require_text(
            reconciliation_state.reconciliation_id,
            "reconciliation_state.reconciliation_id",
        )
        assignment_id = _require_text(reconciliation_state.assignment_id, "assignment_id")
        attempt_id = _require_text(reconciliation_state.attempt_id, "attempt_id")
        status = _require_exact_enum(
            reconciliation_state.status,
            RouteReconciliationStatus,
            "reconciliation_state.status",
        )
        reconciliation_reason_codes = _require_non_empty_text_tuple(
            reconciliation_state.reason_codes,
            "reconciliation_state.reason_codes",
        )
        reconciliation_evidence_reference_ids = _require_non_empty_text_tuple(
            reconciliation_state.evidence_reference_ids,
            "reconciliation_state.evidence_reference_ids",
        )

        if status not in _UNRESOLVED_RECONCILIATION_STATUSES:
            raise ValueError("reconciliation_state.status must be unresolved")
        if reconciliation_state.resolved_outcome_reference is not None:
            raise ValueError("reconciliation_state.resolved_outcome_reference must be None")
        if reconciliation_state_committed is not True:
            raise ValueError("reconciliation_state_committed must be True")
        if new_dispatch_effect_authorized is not False:
            raise ValueError("new_dispatch_effect_authorized must be False")
        if assignment_terminal is not False:
            raise ValueError("assignment_terminal must be False")

        if assignment_id != attempt.assignment_id:
            raise ValueError("reconciliation_state.assignment_id must match dispatch attempt")
        if attempt_id != attempt.attempt_id:
            raise ValueError("reconciliation_state.attempt_id must match dispatch attempt")

        object.__setattr__(self, "reconciliation_state", reconciliation_state)
        object.__setattr__(self, "reason_codes", reason_codes)
        object.__setattr__(self, "evidence_reference_ids", evidence_reference_ids)
        object.__setattr__(self, "boundary_id", boundary_id)

        assert isinstance(reconciliation_id, str)
        assert isinstance(assignment_id, str)
        assert isinstance(attempt_id, str)
        assert isinstance(reconciliation_reason_codes, tuple)
        assert isinstance(reconciliation_evidence_reference_ids, tuple)
