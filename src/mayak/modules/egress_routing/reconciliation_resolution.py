from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .contracts import RouteReconciliationState, RouteReconciliationStatus
from .reconciliation import (
    TransportDispatchReconciliationAuthority,
    TransportDispatchReconciliationBoundary,
)

ER06F_TASK_ID = "ER-06F-RESOLVED-DISPATCH-RECONCILIATION-BOUNDARY-20260715-015"

__all__ = (
    "ER06F_TASK_ID",
    "TransportDispatchReconciliationResolutionAuthority",
    "TransportDispatchReconciliationResolutionBoundary",
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
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    return value


def _require_non_empty_text_tuple(value: object, field_name: str) -> tuple[str, ...]:
    items = _require_tuple(value, field_name)
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

_RESOLVED_RECONCILIATION_STATUSES = frozenset(
    {
        RouteReconciliationStatus.RESOLVED_NOT_SENT,
        RouteReconciliationStatus.RESOLVED_SENT,
        RouteReconciliationStatus.RESOLVED_TERMINAL,
    }
)


class TransportDispatchReconciliationResolutionAuthority(str, Enum):
    EGRESS_ROUTING_SERVER = "EGRESS_ROUTING_SERVER"


@dataclass(frozen=True, slots=True)
class TransportDispatchReconciliationResolutionBoundary:
    boundary_id: str
    authority: TransportDispatchReconciliationResolutionAuthority
    unresolved_reconciliation: TransportDispatchReconciliationBoundary
    resolved_reconciliation_state: RouteReconciliationState
    resolution_committed: bool
    new_dispatch_effect_authorized: bool
    assignment_terminal: bool
    reason_codes: tuple[str, ...]
    evidence_reference_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        boundary_id = _require_text(self.boundary_id, "boundary_id")
        authority = _require_exact_enum(
            self.authority,
            TransportDispatchReconciliationResolutionAuthority,
            "authority",
        )
        unresolved_reconciliation = _require_exact_record(
            self.unresolved_reconciliation,
            TransportDispatchReconciliationBoundary,
            "unresolved_reconciliation",
        )
        resolved_reconciliation_state = _require_exact_record(
            self.resolved_reconciliation_state,
            RouteReconciliationState,
            "resolved_reconciliation_state",
        )
        resolution_committed = _require_bool(self.resolution_committed, "resolution_committed")
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

        assert isinstance(authority, TransportDispatchReconciliationResolutionAuthority)
        assert isinstance(unresolved_reconciliation, TransportDispatchReconciliationBoundary)
        assert isinstance(resolved_reconciliation_state, RouteReconciliationState)

        object.__setattr__(self, "boundary_id", boundary_id)
        object.__setattr__(self, "authority", authority)
        object.__setattr__(self, "unresolved_reconciliation", unresolved_reconciliation)
        object.__setattr__(
            self,
            "resolved_reconciliation_state",
            resolved_reconciliation_state,
        )
        object.__setattr__(self, "resolution_committed", resolution_committed)
        object.__setattr__(
            self,
            "new_dispatch_effect_authorized",
            new_dispatch_effect_authorized,
        )
        object.__setattr__(self, "assignment_terminal", assignment_terminal)
        object.__setattr__(self, "reason_codes", reason_codes)
        object.__setattr__(self, "evidence_reference_ids", evidence_reference_ids)

        if (
            authority
            is not TransportDispatchReconciliationResolutionAuthority.EGRESS_ROUTING_SERVER
        ):
            raise ValueError("authority must be EGRESS_ROUTING_SERVER")
        if (
            unresolved_reconciliation.authority
            is not TransportDispatchReconciliationAuthority.EGRESS_ROUTING_SERVER
        ):
            raise ValueError("unresolved_reconciliation.authority must be EGRESS_ROUTING_SERVER")
        if unresolved_reconciliation.reconciliation_state_committed is not True:
            raise ValueError(
                "unresolved_reconciliation.reconciliation_state_committed must be True"
            )
        if unresolved_reconciliation.new_dispatch_effect_authorized is not False:
            raise ValueError(
                "unresolved_reconciliation.new_dispatch_effect_authorized must be False"
            )
        if unresolved_reconciliation.assignment_terminal is not False:
            raise ValueError("unresolved_reconciliation.assignment_terminal must be False")

        unresolved_state = _require_exact_record(
            unresolved_reconciliation.reconciliation_state,
            RouteReconciliationState,
            "unresolved_reconciliation.reconciliation_state",
        )
        assert isinstance(unresolved_state, RouteReconciliationState)
        unresolved_status = _require_exact_enum(
            unresolved_state.status,
            RouteReconciliationStatus,
            "unresolved_reconciliation.reconciliation_state.status",
        )
        _require_text(
            unresolved_state.reconciliation_id,
            "unresolved_reconciliation.reconciliation_state.reconciliation_id",
        )
        _require_text(
            unresolved_state.assignment_id,
            "unresolved_reconciliation.reconciliation_state.assignment_id",
        )
        _require_text(
            unresolved_state.attempt_id,
            "unresolved_reconciliation.reconciliation_state.attempt_id",
        )
        _require_non_empty_text_tuple(
            unresolved_state.reason_codes,
            "unresolved_reconciliation.reconciliation_state.reason_codes",
        )
        _require_non_empty_text_tuple(
            unresolved_state.evidence_reference_ids,
            "unresolved_reconciliation.reconciliation_state.evidence_reference_ids",
        )
        if unresolved_status not in _UNRESOLVED_RECONCILIATION_STATUSES:
            raise ValueError(
                "unresolved_reconciliation.reconciliation_state.status must be unresolved"
            )
        if unresolved_state.resolved_outcome_reference is not None:
            raise ValueError(
                "unresolved_reconciliation.reconciliation_state."
                "resolved_outcome_reference must be None"
            )

        resolved_state = resolved_reconciliation_state
        resolved_status = _require_exact_enum(
            resolved_state.status,
            RouteReconciliationStatus,
            "resolved_reconciliation_state.status",
        )
        assert isinstance(resolved_state, RouteReconciliationState)
        if resolved_status not in _RESOLVED_RECONCILIATION_STATUSES:
            raise ValueError("resolved_reconciliation_state.status must be resolved")

        resolved_reconciliation_id = _require_text(
            resolved_state.reconciliation_id,
            "resolved_reconciliation_state.reconciliation_id",
        )
        resolved_assignment_id = _require_text(
            resolved_state.assignment_id,
            "resolved_reconciliation_state.assignment_id",
        )
        resolved_attempt_id = _require_text(
            resolved_state.attempt_id,
            "resolved_reconciliation_state.attempt_id",
        )
        resolved_outcome_reference = _require_text(
            resolved_state.resolved_outcome_reference,
            "resolved_reconciliation_state.resolved_outcome_reference",
        )
        _require_non_empty_text_tuple(
            resolved_state.reason_codes,
            "resolved_reconciliation_state.reason_codes",
        )
        _require_non_empty_text_tuple(
            resolved_state.evidence_reference_ids,
            "resolved_reconciliation_state.evidence_reference_ids",
        )

        if resolved_reconciliation_id != unresolved_state.reconciliation_id:
            raise ValueError(
                "resolved_reconciliation_state.reconciliation_id must match "
                "unresolved_reconciliation.reconciliation_state.reconciliation_id"
            )
        if resolved_assignment_id != unresolved_state.assignment_id:
            raise ValueError(
                "resolved_reconciliation_state.assignment_id must match "
                "unresolved_reconciliation.reconciliation_state.assignment_id"
            )
        if resolved_attempt_id != unresolved_state.attempt_id:
            raise ValueError(
                "resolved_reconciliation_state.attempt_id must match "
                "unresolved_reconciliation.reconciliation_state.attempt_id"
            )

        if resolution_committed is not True:
            raise ValueError("resolution_committed must be True")
        if new_dispatch_effect_authorized is not False:
            raise ValueError("new_dispatch_effect_authorized must be False")
        if assignment_terminal is not True:
            raise ValueError("assignment_terminal must be True")

        assert isinstance(resolved_outcome_reference, str)
