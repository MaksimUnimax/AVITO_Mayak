from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import cast

from .contracts import (
    PolicyBasedFallbackDecision,
    PolicyBasedFallbackStatus,
    RouteReconciliationStatus,
    RouteSelectionStatus,
)
from .selection import (
    RouteCandidateEligibilityStatus,
    RouteCandidateEvaluation,
    RouteSelectionAuthority,
    ServerRouteSelectionBoundary,
)

ER05B_TASK_ID = "ER-05B-POLICY-BASED-FALLBACK-BOUNDARY-20260713-008"

__all__ = (
    "ER05B_TASK_ID",
    "PolicyBasedFallbackBoundary",
)


def _require_text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-blank string")
    return value


def _require_optional_text(value: object, field_name: str) -> str | None:
    if value is None:
        return None
    return _require_text(value, field_name)


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


def _require_candidate_evaluations(
    value: object, field_name: str
) -> tuple[RouteCandidateEvaluation, ...]:
    items = _require_tuple(value, field_name)
    for item in items:
        _require_exact_record(item, RouteCandidateEvaluation, field_name)
    return items  # type: ignore[return-value]


_RESOLVED_RECONCILIATION_STATUSES = frozenset(
    {
        RouteReconciliationStatus.NOT_REQUIRED,
        RouteReconciliationStatus.RESOLVED_NOT_SENT,
        RouteReconciliationStatus.RESOLVED_SENT,
        RouteReconciliationStatus.RESOLVED_TERMINAL,
    }
)

_UNRESOLVED_RECONCILIATION_STATUSES = frozenset(
    {
        RouteReconciliationStatus.REQUIRED,
        RouteReconciliationStatus.PENDING,
        RouteReconciliationStatus.REMAINS_AMBIGUOUS,
        RouteReconciliationStatus.MANUAL_REVIEW_REQUIRED,
    }
)


@dataclass(frozen=True, slots=True)
class PolicyBasedFallbackBoundary:
    boundary_id: str
    authority: RouteSelectionAuthority
    request_reference: str
    requester_module: str
    environment_id: str
    purpose: str
    capability_scope: tuple[str, ...]
    fallback_policy_reference: str | None
    original_selection: ServerRouteSelectionBoundary
    original_failure_reference: str
    fallback_candidate_evaluations: tuple[RouteCandidateEvaluation, ...]
    decision: PolicyBasedFallbackDecision

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
            "fallback_policy_reference",
            _require_optional_text(self.fallback_policy_reference, "fallback_policy_reference"),
        )
        authority = cast(
            RouteSelectionAuthority,
            _require_exact_enum(self.authority, RouteSelectionAuthority, "authority"),
        )
        original_selection = cast(
            ServerRouteSelectionBoundary,
            _require_exact_record(
                self.original_selection, ServerRouteSelectionBoundary, "original_selection"
            ),
        )
        object.__setattr__(
            self,
            "original_failure_reference",
            _require_text(self.original_failure_reference, "original_failure_reference"),
        )
        candidate_evaluations = _require_candidate_evaluations(
            self.fallback_candidate_evaluations, "fallback_candidate_evaluations"
        )
        decision = cast(
            PolicyBasedFallbackDecision,
            _require_exact_record(self.decision, PolicyBasedFallbackDecision, "decision"),
        )
        object.__setattr__(self, "capability_scope", capability_scope)
        object.__setattr__(self, "authority", authority)
        object.__setattr__(self, "original_selection", original_selection)
        object.__setattr__(self, "fallback_candidate_evaluations", candidate_evaluations)
        object.__setattr__(self, "decision", decision)

        if authority is not RouteSelectionAuthority.EGRESS_ROUTING_SERVER:
            raise ValueError("authority must be EGRESS_ROUTING_SERVER")

        if original_selection.authority is not RouteSelectionAuthority.EGRESS_ROUTING_SERVER:
            raise ValueError("original_selection.authority must be EGRESS_ROUTING_SERVER")
        if original_selection.decision.status is not RouteSelectionStatus.SELECTED:
            raise ValueError("original_selection must have a selected route decision")
        if original_selection.decision.selected_route_id is None:
            raise ValueError("original_selection must have selected_route_id")
        if original_selection.request_reference != self.request_reference:
            raise ValueError("original_selection request_reference must match boundary")
        if original_selection.requester_module != self.requester_module:
            raise ValueError("original_selection requester_module must match boundary")
        if original_selection.environment_id != self.environment_id:
            raise ValueError("original_selection environment_id must match boundary")
        if original_selection.purpose != self.purpose:
            raise ValueError("original_selection purpose must match boundary")
        if original_selection.capability_scope != capability_scope:
            raise ValueError("original_selection capability_scope must match boundary")

        candidate_evaluation_ids = tuple(
            candidate.evaluation_id for candidate in candidate_evaluations
        )
        if len(candidate_evaluation_ids) != len(set(candidate_evaluation_ids)):
            raise ValueError("fallback candidate evaluation ids must be unique")

        candidate_route_ids = tuple(candidate.route_id for candidate in candidate_evaluations)
        if len(candidate_route_ids) != len(set(candidate_route_ids)):
            raise ValueError("fallback candidate route ids must be unique")

        for candidate in candidate_evaluations:
            if candidate.request_reference != self.request_reference:
                raise ValueError("candidate request_reference must match boundary")
            if candidate.requester_module != self.requester_module:
                raise ValueError("candidate requester_module must match boundary")
            if candidate.environment_id != self.environment_id:
                raise ValueError("candidate environment_id must match boundary")
            if candidate.purpose != self.purpose:
                raise ValueError("candidate purpose must match boundary")
            if candidate.capability_scope != capability_scope:
                raise ValueError("candidate capability_scope must match boundary")
            if candidate.route_id == original_selection.decision.selected_route_id:
                raise ValueError("candidate route_id must differ from original selected route")
            if self.fallback_policy_reference is not None and (
                candidate.policy_reference != self.fallback_policy_reference
            ):
                raise ValueError("candidate policy_reference must match boundary")

        if decision.request_reference != self.request_reference:
            raise ValueError("decision.request_reference must match boundary")
        if decision.original_failure_reference != self.original_failure_reference:
            raise ValueError("decision.original_failure_reference must match boundary")
        if decision.from_route_id != original_selection.decision.selected_route_id:
            raise ValueError("decision.from_route_id must match original selected route")
        if decision.policy_reference != self.fallback_policy_reference:
            raise ValueError("decision.policy_reference must match boundary")
        if type(decision.reason_codes) is not tuple:
            raise ValueError("decision.reason_codes must be a tuple")
        if type(decision.evidence_reference_ids) is not tuple:
            raise ValueError("decision.evidence_reference_ids must be a tuple")
        _require_non_empty_text_tuple(decision.reason_codes, "decision.reason_codes")
        _require_non_empty_text_tuple(
            decision.evidence_reference_ids, "decision.evidence_reference_ids"
        )

        eligible_candidates = tuple(
            candidate
            for candidate in candidate_evaluations
            if candidate.status is RouteCandidateEligibilityStatus.ELIGIBLE
        )
        if self.fallback_policy_reference is None:
            if decision.status is not PolicyBasedFallbackStatus.NOT_EVALUATED:
                raise ValueError("policy-less fallback boundaries must remain not evaluated")
            if candidate_evaluations:
                raise ValueError("not evaluated fallback boundaries must not have candidates")
            if decision.to_route_id is not None:
                raise ValueError("not evaluated fallback boundaries must not have to_route_id")
            if decision.bounded_attempt_reference is not None:
                raise ValueError(
                    "not evaluated fallback boundaries must not have bounded_attempt_reference"
                )
            if decision.policy_reference is not None:
                raise ValueError("not evaluated fallback boundaries must not have policy_reference")
            if decision.reconciliation_status not in _RESOLVED_RECONCILIATION_STATUSES:
                raise ValueError(
                    "not evaluated fallback boundaries require resolved reconciliation"
                )
            return

        if decision.status is PolicyBasedFallbackStatus.NOT_EVALUATED:
            raise ValueError("policy-based fallback boundaries require a policy reference")
        if decision.policy_reference != self.fallback_policy_reference:
            raise ValueError("decision.policy_reference must match fallback_policy_reference")
        if decision.reconciliation_status in _UNRESOLVED_RECONCILIATION_STATUSES:
            if decision.status is not PolicyBasedFallbackStatus.BLOCKED_RECONCILIATION_REQUIRED:
                raise ValueError("unresolved reconciliation requires blocked fallback")
            if decision.to_route_id is not None:
                raise ValueError("blocked reconciliation fallback must not have to_route_id")
            if decision.bounded_attempt_reference is not None:
                raise ValueError(
                    "blocked reconciliation fallback must not have bounded_attempt_reference"
                )
            return

        if decision.status is PolicyBasedFallbackStatus.BLOCKED_RECONCILIATION_REQUIRED:
            raise ValueError("blocked fallback requires unresolved reconciliation")

        if decision.status is PolicyBasedFallbackStatus.NOT_ALLOWED:
            if decision.to_route_id is not None:
                raise ValueError("not allowed fallback must not have to_route_id")
            if decision.bounded_attempt_reference is not None:
                raise ValueError("not allowed fallback must not have bounded_attempt_reference")
            if any(
                candidate.status is RouteCandidateEligibilityStatus.ELIGIBLE
                for candidate in candidate_evaluations
            ):
                raise ValueError("not allowed fallback cannot expose eligible candidates")
        elif decision.status is PolicyBasedFallbackStatus.ALLOWED:
            if len(eligible_candidates) != 1:
                raise ValueError("allowed fallback requires exactly one eligible candidate")
            eligible_candidate = eligible_candidates[0]
            if decision.to_route_id is None:
                raise ValueError("allowed fallback must have to_route_id")
            if decision.to_route_id != eligible_candidate.route_id:
                raise ValueError("allowed fallback target must match eligible candidate")
            if decision.to_route_id not in candidate_route_ids:
                raise ValueError("fallback target route must be present among candidates")
            if decision.bounded_attempt_reference is None:
                raise ValueError("allowed fallback must have bounded_attempt_reference")
        elif decision.status is PolicyBasedFallbackStatus.ATTEMPTED:
            if len(eligible_candidates) != 1:
                raise ValueError("attempted fallback requires exactly one eligible candidate")
            eligible_candidate = eligible_candidates[0]
            if decision.to_route_id is None:
                raise ValueError("attempted fallback must have to_route_id")
            if decision.to_route_id != eligible_candidate.route_id:
                raise ValueError("attempted fallback target must match eligible candidate")
            if decision.to_route_id not in candidate_route_ids:
                raise ValueError("fallback target route must be present among candidates")
            if decision.bounded_attempt_reference is None:
                raise ValueError("attempted fallback must have bounded_attempt_reference")
        elif decision.status is PolicyBasedFallbackStatus.EXHAUSTED:
            if not candidate_evaluations:
                raise ValueError("exhausted fallback requires candidate evaluations")
            if eligible_candidates:
                raise ValueError("exhausted fallback cannot expose eligible candidates")
            if decision.to_route_id is not None:
                raise ValueError("exhausted fallback must not have to_route_id")
            if decision.bounded_attempt_reference is None:
                raise ValueError("exhausted fallback must have bounded_attempt_reference")
        elif decision.status is PolicyBasedFallbackStatus.NO_APPROVED_ROUTE:
            if eligible_candidates:
                raise ValueError("no approved route fallback cannot expose eligible candidates")
            if decision.to_route_id is not None:
                raise ValueError("no approved route fallback must not have to_route_id")
            if decision.bounded_attempt_reference is not None:
                raise ValueError(
                    "no approved route fallback must not have bounded_attempt_reference"
                )
        else:  # pragma: no cover - defensive exhaustion of enum values
            raise ValueError("unsupported fallback status")

        if (
            decision.status
            not in {
                PolicyBasedFallbackStatus.ALLOWED,
                PolicyBasedFallbackStatus.ATTEMPTED,
            }
            and decision.to_route_id is not None
        ):
            raise ValueError("non-target fallback statuses must not have to_route_id")
        if (
            decision.status
            not in {
                PolicyBasedFallbackStatus.ALLOWED,
                PolicyBasedFallbackStatus.ATTEMPTED,
                PolicyBasedFallbackStatus.EXHAUSTED,
            }
            and decision.bounded_attempt_reference is not None
        ):
            raise ValueError(
                "non-attempt fallback statuses must not have bounded_attempt_reference"
            )
