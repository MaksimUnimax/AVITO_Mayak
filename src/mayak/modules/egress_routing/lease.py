from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .contracts import (
    RouteLease,
    RouteLeaseStatus,
    RouteReconciliationStatus,
    RouteRestrictionStatus,
    RouteSelectionStatus,
)
from .selection import (
    RouteCandidateEligibilityStatus,
    RouteCandidateEvaluation,
    RouteSelectionAuthority,
    ServerRouteSelectionBoundary,
)

ER06A_TASK_ID = "ER-06A-ROUTE-LEASE-AUTHORIZATION-BOUNDARY-20260713-009"

__all__ = (
    "ER06A_TASK_ID",
    "RouteLeaseAuthority",
    "RouteLeaseAuthorizationBoundary",
)


def _require_text(value: object, field_name: str) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-blank string")
    return value


def _require_tuple(value: object, field_name: str) -> tuple[object, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    return value


def _require_non_empty_tuple(value: object, field_name: str) -> tuple[object, ...]:
    items = _require_tuple(value, field_name)
    if not items:
        raise ValueError(f"{field_name} must not be empty")
    return items


def _require_text_tuple(value: object, field_name: str) -> tuple[str, ...]:
    items = _require_non_empty_tuple(value, field_name)
    for item in items:
        _require_text(item, field_name)
    return items  # type: ignore[return-value]


def _require_bool(value: object, field_name: str) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


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

_UNRESOLVED_RECONCILIATION_STATUSES: frozenset[RouteReconciliationStatus] = frozenset(
    {
        RouteReconciliationStatus.REQUIRED,
        RouteReconciliationStatus.PENDING,
        RouteReconciliationStatus.REMAINS_AMBIGUOUS,
        RouteReconciliationStatus.MANUAL_REVIEW_REQUIRED,
    }
)

_RESTRICTION_STATUSES_BLOCKING_DISPATCH: frozenset[RouteRestrictionStatus] = frozenset(
    {
        RouteRestrictionStatus.DEGRADED,
        RouteRestrictionStatus.RESTRICTED,
        RouteRestrictionStatus.QUARANTINED,
        RouteRestrictionStatus.SUSPENDED,
        RouteRestrictionStatus.RETIRED,
    }
)


class RouteLeaseAuthority(str, Enum):
    EGRESS_ROUTING_SERVER = "EGRESS_ROUTING_SERVER"


@dataclass(frozen=True, slots=True)
class RouteLeaseAuthorizationBoundary:
    boundary_id: str
    authority: RouteLeaseAuthority
    request_reference: str
    requester_module: str
    environment_id: str
    purpose: str
    capability_scope: tuple[str, ...]
    selection: ServerRouteSelectionBoundary
    selected_candidate: RouteCandidateEvaluation
    lease: RouteLease
    reconciliation_status: RouteReconciliationStatus
    new_dispatch_authorized: bool
    reason_codes: tuple[str, ...]
    evidence_reference_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "boundary_id", _require_text(self.boundary_id, "boundary_id"))
        object.__setattr__(
            self,
            "authority",
            _require_exact_enum(self.authority, RouteLeaseAuthority, "authority"),
        )
        object.__setattr__(
            self,
            "request_reference",
            _require_text(self.request_reference, "request_reference"),
        )
        object.__setattr__(
            self,
            "requester_module",
            _require_text(self.requester_module, "requester_module"),
        )
        object.__setattr__(
            self,
            "environment_id",
            _require_text(self.environment_id, "environment_id"),
        )
        object.__setattr__(self, "purpose", _require_text(self.purpose, "purpose"))
        capability_scope = _require_text_tuple(self.capability_scope, "capability_scope")
        object.__setattr__(
            self,
            "selection",
            _require_exact_record(self.selection, ServerRouteSelectionBoundary, "selection"),
        )
        object.__setattr__(
            self,
            "selected_candidate",
            _require_exact_record(
                self.selected_candidate, RouteCandidateEvaluation, "selected_candidate"
            ),
        )
        object.__setattr__(
            self,
            "lease",
            _require_exact_record(self.lease, RouteLease, "lease"),
        )
        object.__setattr__(
            self,
            "reconciliation_status",
            _require_exact_enum(
                self.reconciliation_status, RouteReconciliationStatus, "reconciliation_status"
            ),
        )
        object.__setattr__(
            self,
            "new_dispatch_authorized",
            _require_bool(self.new_dispatch_authorized, "new_dispatch_authorized"),
        )
        _require_text_tuple(self.reason_codes, "reason_codes")
        _require_text_tuple(self.evidence_reference_ids, "evidence_reference_ids")

        if self.authority is not RouteLeaseAuthority.EGRESS_ROUTING_SERVER:
            raise ValueError("authority must be EGRESS_ROUTING_SERVER")

        selection = self.selection
        if selection.authority is not RouteSelectionAuthority.EGRESS_ROUTING_SERVER:
            raise ValueError("selection.authority must be EGRESS_ROUTING_SERVER")
        if selection.decision.status is not RouteSelectionStatus.SELECTED:
            raise ValueError("selection.decision.status must be SELECTED")
        if selection.decision.selected_route_id is None:
            raise ValueError("selection.decision.selected_route_id must not be None")
        if selection.request_reference != self.request_reference:
            raise ValueError("selection.request_reference must match boundary request_reference")
        if selection.requester_module != self.requester_module:
            raise ValueError("selection.requester_module must match boundary requester_module")
        if selection.environment_id != self.environment_id:
            raise ValueError("selection.environment_id must match boundary environment_id")
        if selection.purpose != self.purpose:
            raise ValueError("selection.purpose must match boundary purpose")
        if selection.capability_scope != capability_scope:
            raise ValueError("selection.capability_scope must match boundary capability_scope")

        selected_candidate = self.selected_candidate
        candidate_in_selection = False
        for candidate in selection.candidate_evaluations:
            if candidate is selected_candidate:
                candidate_in_selection = True
                break
        if not candidate_in_selection:
            raise ValueError("selected_candidate must be in selection.candidate_evaluations")
        if selected_candidate.status is not RouteCandidateEligibilityStatus.ELIGIBLE:
            raise ValueError("selected_candidate.status must be ELIGIBLE")
        if selected_candidate.route_id != selection.decision.selected_route_id:
            raise ValueError(
                "selected_candidate.route_id must match"
                " selection.decision.selected_route_id"
            )
        if selected_candidate.request_reference != self.request_reference:
            raise ValueError(
                "selected_candidate.request_reference must match"
                " boundary request_reference"
            )
        if selected_candidate.requester_module != self.requester_module:
            raise ValueError(
                "selected_candidate.requester_module must match"
                " boundary requester_module"
            )
        if selected_candidate.environment_id != self.environment_id:
            raise ValueError(
                "selected_candidate.environment_id must match"
                " boundary environment_id"
            )
        if selected_candidate.purpose != self.purpose:
            raise ValueError("selected_candidate.purpose must match boundary purpose")
        if selected_candidate.capability_scope != capability_scope:
            raise ValueError(
                "selected_candidate.capability_scope must match"
                " boundary capability_scope"
            )

        eligible_count = sum(
            1
            for candidate in selection.candidate_evaluations
            if candidate.status is RouteCandidateEligibilityStatus.ELIGIBLE
        )
        if eligible_count != 1:
            raise ValueError("selection must have exactly one ELIGIBLE candidate")

        lease = self.lease
        if lease.route_id != selection.decision.selected_route_id:
            raise ValueError("lease.route_id must match selection.decision.selected_route_id")
        if lease.route_id != selected_candidate.route_id:
            raise ValueError("lease.route_id must match selected_candidate.route_id")
        if lease.agent_id != selected_candidate.agent_id:
            raise ValueError("lease.agent_id must match selected_candidate.agent_id")
        if lease.requester_module != self.requester_module:
            raise ValueError("lease.requester_module must match boundary requester_module")
        if lease.purpose != self.purpose:
            raise ValueError("lease.purpose must match boundary purpose")
        if lease.capability_scope != capability_scope:
            raise ValueError("lease.capability_scope must match boundary capability_scope")

        self._validate_lifecycle_authorization()

    def _validate_lifecycle_authorization(self) -> None:
        lease = self.lease
        reconciliation = self.reconciliation_status
        restriction = lease.restriction_snapshot

        if lease.status is RouteLeaseStatus.REQUESTED:
            if self.new_dispatch_authorized is not False:
                raise ValueError("REQUESTED must not authorize dispatch")
            return

        if lease.status is RouteLeaseStatus.REJECTED:
            if self.new_dispatch_authorized is not False:
                raise ValueError("REJECTED must not authorize dispatch")
            return

        if lease.status is RouteLeaseStatus.GRANTED:
            if self.new_dispatch_authorized is not True:
                raise ValueError("GRANTED must authorize dispatch")
            if restriction is not RouteRestrictionStatus.NONE:
                raise ValueError("GRANTED requires NONE restriction")
            if reconciliation not in _RESOLVED_RECONCILIATION_STATUSES:
                raise ValueError("GRANTED requires resolved reconciliation")
            return

        if lease.status is RouteLeaseStatus.DISPATCHED:
            if self.new_dispatch_authorized is not False:
                raise ValueError("DISPATCHED must not authorize new dispatch")
            if restriction is not RouteRestrictionStatus.NONE:
                raise ValueError("DISPATCHED requires NONE restriction")
            if reconciliation not in _RESOLVED_RECONCILIATION_STATUSES:
                raise ValueError("DISPATCHED requires resolved reconciliation")
            return

        if lease.status is RouteLeaseStatus.IN_USE:
            if self.new_dispatch_authorized is not False:
                raise ValueError("IN_USE must not authorize new dispatch")
            if restriction is not RouteRestrictionStatus.NONE:
                raise ValueError("IN_USE requires NONE restriction")
            if reconciliation not in _RESOLVED_RECONCILIATION_STATUSES:
                raise ValueError("IN_USE requires resolved reconciliation")
            return

        if lease.status is RouteLeaseStatus.COMPLETED:
            if self.new_dispatch_authorized is not False:
                raise ValueError("COMPLETED must not authorize new dispatch")
            if restriction is not RouteRestrictionStatus.NONE:
                raise ValueError("COMPLETED requires NONE restriction")
            if reconciliation not in _RESOLVED_RECONCILIATION_STATUSES:
                raise ValueError("COMPLETED requires resolved reconciliation")
            return

        if lease.status is RouteLeaseStatus.EXPIRED:
            if self.new_dispatch_authorized is not False:
                raise ValueError("EXPIRED must not authorize dispatch")
            return

        if lease.status is RouteLeaseStatus.REVOKED:
            if self.new_dispatch_authorized is not False:
                raise ValueError("REVOKED must not authorize dispatch")
            return

        if lease.status is RouteLeaseStatus.AMBIGUOUS:
            if self.new_dispatch_authorized is not False:
                raise ValueError("AMBIGUOUS must not authorize dispatch")
            if reconciliation not in _UNRESOLVED_RECONCILIATION_STATUSES:
                raise ValueError("AMBIGUOUS requires unresolved reconciliation")
            return

        if lease.status is RouteLeaseStatus.RECONCILIATION_REQUIRED:
            if self.new_dispatch_authorized is not False:
                raise ValueError("RECONCILIATION_REQUIRED must not authorize dispatch")
            if reconciliation not in _UNRESOLVED_RECONCILIATION_STATUSES:
                raise ValueError("RECONCILIATION_REQUIRED requires unresolved reconciliation")
            return

        if lease.status is RouteLeaseStatus.FAILED:
            if self.new_dispatch_authorized is not False:
                raise ValueError("FAILED must not authorize dispatch")
            return
