from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .contracts import (
    RouteLeaseStatus,
    RouteReconciliationStatus,
    RouteRestrictionStatus,
    TransportAssignment,
)
from .lease import RouteLeaseAuthority, RouteLeaseAuthorizationBoundary

ER06B_TASK_ID = "ER-06B-TRANSPORT-ASSIGNMENT-COMMITMENT-BOUNDARY-20260715-010"

__all__ = (
    "ER06B_TASK_ID",
    "TransportAssignmentAuthority",
    "TransportAssignmentCommitmentBoundary",
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


class TransportAssignmentAuthority(str, Enum):
    EGRESS_ROUTING_SERVER = "EGRESS_ROUTING_SERVER"


@dataclass(frozen=True, slots=True)
class TransportAssignmentCommitmentBoundary:
    boundary_id: str
    authority: TransportAssignmentAuthority
    request_reference: str
    requester_module: str
    environment_id: str
    purpose: str
    capability_scope: tuple[str, ...]
    lease_authorization: RouteLeaseAuthorizationBoundary
    assignment: TransportAssignment
    assignment_committed: bool
    reason_codes: tuple[str, ...]
    evidence_reference_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        boundary_id = _require_text(self.boundary_id, "boundary_id")
        authority = _require_exact_enum(self.authority, TransportAssignmentAuthority, "authority")
        request_reference = _require_text(self.request_reference, "request_reference")
        requester_module = _require_text(self.requester_module, "requester_module")
        environment_id = _require_text(self.environment_id, "environment_id")
        purpose = _require_text(self.purpose, "purpose")
        capability_scope = _require_text_tuple(self.capability_scope, "capability_scope")
        lease_authorization = _require_exact_record(
            self.lease_authorization,
            RouteLeaseAuthorizationBoundary,
            "lease_authorization",
        )
        assignment = _require_exact_record(self.assignment, TransportAssignment, "assignment")
        assert isinstance(lease_authorization, RouteLeaseAuthorizationBoundary)
        assert isinstance(assignment, TransportAssignment)
        assignment_committed = self.assignment_committed
        if type(assignment_committed) is not bool:
            raise ValueError("assignment_committed must be a bool")
        if assignment_committed is not True:
            raise ValueError("assignment_committed must be True")
        reason_codes = _require_text_tuple(self.reason_codes, "reason_codes")
        evidence_reference_ids = _require_text_tuple(
            self.evidence_reference_ids, "evidence_reference_ids"
        )

        object.__setattr__(self, "boundary_id", boundary_id)
        object.__setattr__(self, "authority", authority)
        object.__setattr__(self, "request_reference", request_reference)
        object.__setattr__(self, "requester_module", requester_module)
        object.__setattr__(self, "environment_id", environment_id)
        object.__setattr__(self, "purpose", purpose)
        object.__setattr__(self, "capability_scope", capability_scope)
        object.__setattr__(self, "lease_authorization", lease_authorization)
        object.__setattr__(self, "assignment", assignment)
        object.__setattr__(self, "assignment_committed", assignment_committed)
        object.__setattr__(self, "reason_codes", reason_codes)
        object.__setattr__(self, "evidence_reference_ids", evidence_reference_ids)

        if authority is not TransportAssignmentAuthority.EGRESS_ROUTING_SERVER:
            raise ValueError("authority must be EGRESS_ROUTING_SERVER")

        if lease_authorization.authority is not RouteLeaseAuthority.EGRESS_ROUTING_SERVER:
            raise ValueError("lease_authorization.authority must be EGRESS_ROUTING_SERVER")
        if lease_authorization.request_reference != request_reference:
            raise ValueError("lease_authorization.request_reference must match request_reference")
        if lease_authorization.requester_module != requester_module:
            raise ValueError("lease_authorization.requester_module must match requester_module")
        if lease_authorization.environment_id != environment_id:
            raise ValueError("lease_authorization.environment_id must match environment_id")
        if lease_authorization.purpose != purpose:
            raise ValueError("lease_authorization.purpose must match purpose")
        if lease_authorization.capability_scope != capability_scope:
            raise ValueError("lease_authorization.capability_scope must match capability_scope")
        if lease_authorization.new_dispatch_authorized is not True:
            raise ValueError("lease_authorization.new_dispatch_authorized must be True")
        if lease_authorization.lease.status is not RouteLeaseStatus.GRANTED:
            raise ValueError("lease_authorization.lease.status must be GRANTED")
        if lease_authorization.lease.restriction_snapshot is not RouteRestrictionStatus.NONE:
            raise ValueError("lease_authorization.lease.restriction_snapshot must be NONE")
        if lease_authorization.reconciliation_status not in _RESOLVED_RECONCILIATION_STATUSES:
            raise ValueError("lease_authorization.reconciliation_status must be resolved")

        assignment_context = assignment
        if assignment_context.lease_id != lease_authorization.lease.lease_id:
            raise ValueError("assignment.lease_id must match lease_authorization.lease.lease_id")
        if assignment_context.route_id != lease_authorization.lease.route_id:
            raise ValueError("assignment.route_id must match lease_authorization.lease.route_id")
        if assignment_context.agent_id != lease_authorization.lease.agent_id:
            raise ValueError("assignment.agent_id must match lease_authorization.lease.agent_id")
        if assignment_context.purpose != purpose:
            raise ValueError("assignment.purpose must match purpose")
        if assignment_context.safe_request_reference != request_reference:
            raise ValueError(
                "assignment.safe_request_reference must match request_reference"
            )
        if assignment_context.correlation_id != lease_authorization.lease.correlation_id:
            raise ValueError(
                "assignment.correlation_id must match lease_authorization.lease.correlation_id"
            )
        if assignment_context.causation_id != lease_authorization.lease.causation_id:
            raise ValueError(
                "assignment.causation_id must match lease_authorization.lease.causation_id"
            )
        if (
            assignment_context.route_policy_reference
            != lease_authorization.selection.decision.policy_reference
        ):
            raise ValueError(
                "assignment.route_policy_reference must match "
                "lease_authorization.selection.decision.policy_reference"
            )
