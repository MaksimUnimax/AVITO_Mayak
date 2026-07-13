from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .contracts import (
    AgentLifecycleStatus,
    RouteCapability,
    RouteEvidenceStatus,
    RouteHealthState,
    RouteHealthStatus,
    RouteLifecycleStatus,
    RouteReadinessDecision,
    RouteReadinessStatus,
    RouteReconciliationStatus,
    RouteRestrictionState,
    RouteRestrictionStatus,
    RouteSelectionDecision,
    RouteSelectionStatus,
)
from .registration import (
    AgentRegistrationStatus,
    AgentRouteAssociationStatus,
    AgentRouteRegistrationBoundary,
    RouteRegistrationStatus,
)

ER05A_TASK_ID = "ER-05A-SERVER-ROUTE-SELECTION-BOUNDARY-20260712-007"

__all__ = (
    "ER05A_TASK_ID",
    "RouteSelectionAuthority",
    "RouteCandidateEligibilityStatus",
    "RouteCandidateEvaluation",
    "ServerRouteSelectionBoundary",
)


def _require_text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-blank string")
    return value


def _require_tuple(value: object, field_name: str) -> tuple[object, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    return value


def _require_text_tuple(value: object, field_name: str) -> tuple[str, ...]:
    items = _require_tuple(value, field_name)
    for item in items:
        _require_text(item, field_name)
    return items  # type: ignore[return-value]


def _require_non_empty_text_tuple(value: object, field_name: str) -> tuple[str, ...]:
    items = _require_text_tuple(value, field_name)
    if not items:
        raise ValueError(f"{field_name} must not be empty")
    return items


def _require_exact_enum(value: object, enum_cls: type[Enum], field_name: str) -> Enum:
    if type(value) is not enum_cls:
        raise ValueError(f"{field_name} must be {enum_cls.__name__}")
    return value


def _require_exact_record(value: object, record_cls: type[object], field_name: str) -> object:
    if type(value) is not record_cls:
        raise ValueError(f"{field_name} must be {record_cls.__name__}")
    return value


def _require_bool(value: object, field_name: str) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _require_candidate_evaluations(
    value: object, field_name: str
) -> tuple["RouteCandidateEvaluation", ...]:
    items = _require_tuple(value, field_name)
    for item in items:
        _require_exact_record(item, RouteCandidateEvaluation, field_name)
    return items  # type: ignore[return-value]


_ALLOWED_RECONCILIATION_STATUSES = frozenset(
    {
        RouteReconciliationStatus.NOT_REQUIRED,
        RouteReconciliationStatus.RESOLVED_NOT_SENT,
        RouteReconciliationStatus.RESOLVED_SENT,
        RouteReconciliationStatus.RESOLVED_TERMINAL,
    }
)


class RouteSelectionAuthority(str, Enum):
    EGRESS_ROUTING_SERVER = "EGRESS_ROUTING_SERVER"


class RouteCandidateEligibilityStatus(str, Enum):
    ELIGIBLE = "ELIGIBLE"
    REGISTRATION_BLOCKED = "REGISTRATION_BLOCKED"
    PURPOSE_MISMATCH = "PURPOSE_MISMATCH"
    CAPABILITY_MISMATCH = "CAPABILITY_MISMATCH"
    READINESS_BLOCKED = "READINESS_BLOCKED"
    HEALTH_BLOCKED = "HEALTH_BLOCKED"
    RESTRICTED = "RESTRICTED"
    EVIDENCE_STALE = "EVIDENCE_STALE"
    RECONCILIATION_BLOCKED = "RECONCILIATION_BLOCKED"
    POLICY_REJECTED = "POLICY_REJECTED"
    CONFLICT = "CONFLICT"
    AMBIGUOUS = "AMBIGUOUS"


@dataclass(frozen=True, slots=True)
class RouteCandidateEvaluation:
    evaluation_id: str
    request_reference: str
    requester_module: str
    environment_id: str
    purpose: str
    capability_scope: tuple[str, ...]
    policy_reference: str
    route_id: str
    agent_id: str
    registration_boundary: AgentRouteRegistrationBoundary
    capability: RouteCapability
    readiness: RouteReadinessDecision
    health: RouteHealthState
    restriction: RouteRestrictionState
    reconciliation_status: RouteReconciliationStatus
    status: RouteCandidateEligibilityStatus
    reason_codes: tuple[str, ...]
    evidence_reference_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "evaluation_id", _require_text(self.evaluation_id, "evaluation_id")
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
        object.__setattr__(
            self,
            "capability_scope",
            _require_text_tuple(self.capability_scope, "capability_scope"),
        )
        object.__setattr__(
            self,
            "policy_reference",
            _require_text(self.policy_reference, "policy_reference"),
        )
        object.__setattr__(self, "route_id", _require_text(self.route_id, "route_id"))
        object.__setattr__(self, "agent_id", _require_text(self.agent_id, "agent_id"))
        object.__setattr__(
            self,
            "registration_boundary",
            _require_exact_record(
                self.registration_boundary, AgentRouteRegistrationBoundary, "registration_boundary"
            ),
        )
        object.__setattr__(
            self,
            "capability",
            _require_exact_record(self.capability, RouteCapability, "capability"),
        )
        object.__setattr__(
            self,
            "readiness",
            _require_exact_record(self.readiness, RouteReadinessDecision, "readiness"),
        )
        object.__setattr__(
            self,
            "health",
            _require_exact_record(self.health, RouteHealthState, "health"),
        )
        object.__setattr__(
            self,
            "restriction",
            _require_exact_record(self.restriction, RouteRestrictionState, "restriction"),
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
            "status",
            _require_exact_enum(self.status, RouteCandidateEligibilityStatus, "status"),
        )
        reason_codes = _require_text_tuple(self.reason_codes, "reason_codes")
        evidence_reference_ids = _require_non_empty_text_tuple(
            self.evidence_reference_ids, "evidence_reference_ids"
        )

        boundary = self.registration_boundary
        if self.route_id != boundary.route.route_id:
            raise ValueError("route_id must match registration_boundary.route.route_id")
        if self.agent_id != boundary.agent.agent_id:
            raise ValueError("agent_id must match registration_boundary.agent.agent_id")
        if self.environment_id != boundary.agent.environment_id:
            raise ValueError("environment_id must match registration_boundary.agent.environment_id")
        if self.environment_id != boundary.route.environment_id:
            raise ValueError("environment_id must match registration_boundary.route.environment_id")
        if self.route_id != boundary.association.route_id:
            raise ValueError("route_id must match registration_boundary.association.route_id")
        if self.agent_id != boundary.association.agent_id:
            raise ValueError("agent_id must match registration_boundary.association.agent_id")
        if self.environment_id != boundary.association.environment_id:
            raise ValueError(
                "environment_id must match registration_boundary.association.environment_id"
            )
        if self.capability.route_id != self.route_id:
            raise ValueError("capability.route_id must match route_id")
        if self.capability.capability_id not in boundary.route.capability_ids:
            raise ValueError("capability.capability_id must be registered for the route")
        if self.readiness.route_id != self.route_id:
            raise ValueError("readiness.route_id must match route_id")
        if self.health.route_id != self.route_id:
            raise ValueError("health.route_id must match route_id")
        if self.restriction.route_id != self.route_id:
            raise ValueError("restriction.route_id must match route_id")

        registration_gate = (
            boundary.agent_registration.status is AgentRegistrationStatus.REGISTERED
            and boundary.route_registration.status is RouteRegistrationStatus.REGISTERED
            and boundary.association.status is AgentRouteAssociationStatus.ACTIVE
        )
        purpose_gate = self.purpose in boundary.route.purpose_scope
        capability_gate = (
            self.capability.capability_id in boundary.route.capability_ids
            and bool(self.capability_scope)
            and all(scope in self.capability.operation_classes for scope in self.capability_scope)
        )
        readiness_gate = (
            boundary.agent.lifecycle_status is AgentLifecycleStatus.READY
            and boundary.route.lifecycle_status is RouteLifecycleStatus.READY
            and self.readiness.readiness_status is RouteReadinessStatus.READY
        )
        health_gate = self.health.health_status is RouteHealthStatus.READY
        restriction_gate = (
            self.restriction.status is RouteRestrictionStatus.NONE
            and _require_bool(self.restriction.blocks_new_assignments, "blocks_new_assignments")
            is False
        )
        evidence_gate = self.capability.evidence_status is RouteEvidenceStatus.CURRENT and bool(
            evidence_reference_ids
        )
        reconciliation_gate = self.reconciliation_status in _ALLOWED_RECONCILIATION_STATUSES
        technical_gates = (
            registration_gate,
            purpose_gate,
            capability_gate,
            readiness_gate,
            health_gate,
            restriction_gate,
            evidence_gate,
            reconciliation_gate,
        )

        if self.status is RouteCandidateEligibilityStatus.ELIGIBLE:
            if not all(technical_gates):
                raise ValueError("eligible candidates require all technical gates to pass")
        else:
            if not reason_codes:
                raise ValueError("reason_codes are required for non-eligible candidate statuses")
            if (
                self.status is RouteCandidateEligibilityStatus.REGISTRATION_BLOCKED
                and registration_gate
            ):
                raise ValueError("registration_blocked requires a failed registration gate")
            if self.status is RouteCandidateEligibilityStatus.PURPOSE_MISMATCH and purpose_gate:
                raise ValueError("purpose_mismatch requires a failed purpose gate")
            if (
                self.status is RouteCandidateEligibilityStatus.CAPABILITY_MISMATCH
                and capability_gate
            ):
                raise ValueError("capability_mismatch requires a failed capability gate")
            if self.status is RouteCandidateEligibilityStatus.READINESS_BLOCKED and readiness_gate:
                raise ValueError("readiness_blocked requires a failed readiness gate")
            if self.status is RouteCandidateEligibilityStatus.HEALTH_BLOCKED and health_gate:
                raise ValueError("health_blocked requires a failed health gate")
            if self.status is RouteCandidateEligibilityStatus.RESTRICTED and restriction_gate:
                raise ValueError("restricted requires a failed restriction gate")
            if self.status is RouteCandidateEligibilityStatus.EVIDENCE_STALE and evidence_gate:
                raise ValueError("evidence_stale requires a failed evidence gate")
            if (
                self.status is RouteCandidateEligibilityStatus.RECONCILIATION_BLOCKED
                and reconciliation_gate
            ):
                raise ValueError("reconciliation_blocked requires a failed reconciliation gate")
            if self.status is RouteCandidateEligibilityStatus.POLICY_REJECTED and not all(
                technical_gates
            ):
                raise ValueError("policy_rejected requires all technical gates to pass")
            if (
                self.status
                in {
                    RouteCandidateEligibilityStatus.CONFLICT,
                    RouteCandidateEligibilityStatus.AMBIGUOUS,
                }
                and not evidence_reference_ids
            ):
                raise ValueError("evidence_reference_ids are required for conflict and ambiguous")

        object.__setattr__(self, "reason_codes", reason_codes)
        object.__setattr__(self, "evidence_reference_ids", evidence_reference_ids)


@dataclass(frozen=True, slots=True)
class ServerRouteSelectionBoundary:
    boundary_id: str
    authority: RouteSelectionAuthority
    request_reference: str
    requester_module: str
    environment_id: str
    purpose: str
    capability_scope: tuple[str, ...]
    policy_reference: str
    candidate_evaluations: tuple[RouteCandidateEvaluation, ...]
    decision: RouteSelectionDecision

    def __post_init__(self) -> None:
        object.__setattr__(self, "boundary_id", _require_text(self.boundary_id, "boundary_id"))
        object.__setattr__(
            self,
            "authority",
            _require_exact_enum(self.authority, RouteSelectionAuthority, "authority"),
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
        capability_scope = _require_non_empty_text_tuple(self.capability_scope, "capability_scope")
        object.__setattr__(
            self,
            "policy_reference",
            _require_text(self.policy_reference, "policy_reference"),
        )
        candidate_evaluations = _require_candidate_evaluations(
            self.candidate_evaluations, "candidate_evaluations"
        )
        decision = self.decision
        _require_exact_record(decision, RouteSelectionDecision, "decision")
        object.__setattr__(self, "candidate_evaluations", candidate_evaluations)
        object.__setattr__(self, "decision", decision)

        if self.authority is not RouteSelectionAuthority.EGRESS_ROUTING_SERVER:
            raise ValueError("authority must be EGRESS_ROUTING_SERVER")

        candidate_evaluation_ids = tuple(
            candidate.evaluation_id for candidate in candidate_evaluations
        )
        if len(candidate_evaluation_ids) != len(set(candidate_evaluation_ids)):
            raise ValueError("candidate evaluation ids must be unique")

        candidate_route_ids = tuple(candidate.route_id for candidate in candidate_evaluations)
        if len(candidate_route_ids) != len(set(candidate_route_ids)):
            raise ValueError("candidate route ids must be unique")

        for candidate in candidate_evaluations:
            if candidate.request_reference != self.request_reference:
                raise ValueError(
                    "candidate request_reference must match boundary request_reference"
                )
            if candidate.requester_module != self.requester_module:
                raise ValueError("candidate requester_module must match boundary requester_module")
            if candidate.environment_id != self.environment_id:
                raise ValueError("candidate environment_id must match boundary environment_id")
            if candidate.purpose != self.purpose:
                raise ValueError("candidate purpose must match boundary purpose")
            if candidate.capability_scope != capability_scope:
                raise ValueError("candidate capability_scope must match boundary capability_scope")
            if candidate.policy_reference != self.policy_reference:
                raise ValueError("candidate policy_reference must match boundary policy_reference")

        if decision.request_reference != self.request_reference:
            raise ValueError("decision.request_reference must match boundary request_reference")
        if decision.policy_reference != self.policy_reference:
            raise ValueError("decision.policy_reference must match boundary policy_reference")
        if type(decision.candidate_route_ids) is not tuple:
            raise ValueError("candidate_route_ids must be a tuple")
        if type(decision.rejected_route_ids) is not tuple:
            raise ValueError("rejected_route_ids must be a tuple")
        if not decision.reason_codes:
            raise ValueError("decision.reason_codes must not be empty")
        if not decision.evidence_reference_ids:
            raise ValueError("decision.evidence_reference_ids must not be empty")
        if any(not isinstance(item, str) or not item.strip() for item in decision.reason_codes):
            raise ValueError("decision.reason_codes must contain non-blank strings")
        if any(
            not isinstance(item, str) or not item.strip()
            for item in decision.evidence_reference_ids
        ):
            raise ValueError("decision.evidence_reference_ids must contain non-blank strings")
        if len(decision.rejected_route_ids) != len(set(decision.rejected_route_ids)):
            raise ValueError("decision.rejected_route_ids must be unique")
        if any(item not in candidate_route_ids for item in decision.rejected_route_ids):
            raise ValueError("decision.rejected_route_ids must be a subset of candidate route ids")

        expected_candidate_route_ids = candidate_route_ids
        if decision.candidate_route_ids != expected_candidate_route_ids:
            raise ValueError("decision.candidate_route_ids must match candidate route order")

        if self.decision.status is RouteSelectionStatus.SELECTED:
            if decision.selected_route_id is None:
                raise ValueError("selected decisions require selected_route_id")
            if decision.selected_route_id not in candidate_route_ids:
                raise ValueError("selected_route_id must be present in candidate route ids")
            if (
                sum(
                    candidate.status is RouteCandidateEligibilityStatus.ELIGIBLE
                    for candidate in candidate_evaluations
                )
                != 1
            ):
                raise ValueError("selected decisions require exactly one eligible candidate")
            eligible_candidate = next(
                candidate
                for candidate in candidate_evaluations
                if candidate.status is RouteCandidateEligibilityStatus.ELIGIBLE
            )
            if eligible_candidate.route_id != decision.selected_route_id:
                raise ValueError("selected_route_id must match the eligible candidate route id")
            expected_rejected_route_ids = tuple(
                candidate.route_id
                for candidate in candidate_evaluations
                if candidate.route_id != decision.selected_route_id
            )
            if decision.rejected_route_ids != expected_rejected_route_ids:
                raise ValueError(
                    "selected decisions must reject all non-selected candidates in order"
                )
        else:
            if decision.selected_route_id is not None:
                raise ValueError("non-selected decisions must not have selected_route_id")
            expected_rejected_route_ids = candidate_route_ids
            if decision.rejected_route_ids != expected_rejected_route_ids:
                raise ValueError(
                    "non-selected decisions must reject all candidate route ids in order"
                )
            if self.decision.status is RouteSelectionStatus.NO_ELIGIBLE_ROUTE:
                if any(
                    candidate.status is RouteCandidateEligibilityStatus.ELIGIBLE
                    for candidate in candidate_evaluations
                ):
                    raise ValueError("no eligible route decisions cannot hide eligible candidates")
            if self.decision.status is RouteSelectionStatus.RESTRICTED and not any(
                candidate.status is RouteCandidateEligibilityStatus.RESTRICTED
                for candidate in candidate_evaluations
            ):
                raise ValueError("restricted decisions require a restricted candidate")
            if self.decision.status is RouteSelectionStatus.CONFLICT and not any(
                candidate.status is RouteCandidateEligibilityStatus.CONFLICT
                for candidate in candidate_evaluations
            ):
                raise ValueError("conflict decisions require a conflicting candidate")
            if self.decision.status is RouteSelectionStatus.AMBIGUOUS and not any(
                candidate.status is RouteCandidateEligibilityStatus.AMBIGUOUS
                for candidate in candidate_evaluations
            ):
                raise ValueError("ambiguous decisions require an ambiguous candidate")

        if self.decision.status is RouteSelectionStatus.SELECTED and not candidate_evaluations:
            raise ValueError("selected decisions require at least one candidate")
