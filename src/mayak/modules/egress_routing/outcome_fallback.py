from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .contracts import (
    PolicyBasedFallbackDecision,
    PolicyBasedFallbackStatus,
    RouteReconciliationStatus,
    RouteSelectionDecision,
    RouteSelectionStatus,
    TransportOutcomeStatus,
)
from .fallback import PolicyBasedFallbackBoundary
from .selection import (
    RouteCandidateEligibilityStatus,
    RouteCandidateEvaluation,
    RouteSelectionAuthority,
    ServerRouteSelectionBoundary,
)

ER07E_TASK_ID = "ER-07E-POLICY-FALLBACK-TRANSPORT-OUTCOME-BOUNDARY-20260715-023"

__all__ = (
    "ER07E_TASK_ID",
    "PolicyFallbackTransportOutcomeAuthority",
    "PolicyFallbackTransportOutcomeBoundary",
)


def _require_text(value: object, field_name: str) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-blank string")
    return value  # type: ignore[return-value]


def _require_non_empty_text_tuple(value: object, field_name: str) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    for item in value:
        _require_text(item, field_name)
    return value  # type: ignore[return-value]


def _require_bool(value: object, field_name: str) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value  # type: ignore[return-value]


def _require_exact_enum(value: object, enum_cls: type[Enum], field_name: str) -> None:
    if type(value) is not enum_cls:
        raise ValueError(f"{field_name} must be {enum_cls.__name__}")


def _require_exact_record(value: object, record_cls: type[object], field_name: str) -> None:
    if type(value) is not record_cls:
        raise ValueError(f"{field_name} must be {record_cls.__name__}")


_STATUS_TO_OUTCOME = {
    PolicyBasedFallbackStatus.ATTEMPTED: TransportOutcomeStatus.POLICY_FALLBACK_ATTEMPTED,
    PolicyBasedFallbackStatus.EXHAUSTED: TransportOutcomeStatus.POLICY_FALLBACK_EXHAUSTED,
    PolicyBasedFallbackStatus.NO_APPROVED_ROUTE: TransportOutcomeStatus.NO_APPROVED_ROUTE_AVAILABLE,
}

_TERMINAL_BY_FALLBACK_STATUS = {
    PolicyBasedFallbackStatus.ATTEMPTED: False,
    PolicyBasedFallbackStatus.EXHAUSTED: True,
    PolicyBasedFallbackStatus.NO_APPROVED_ROUTE: True,
}

_ALLOWED_RECONCILIATION_STATUSES = frozenset(
    {
        RouteReconciliationStatus.NOT_REQUIRED,
        RouteReconciliationStatus.RESOLVED_NOT_SENT,
        RouteReconciliationStatus.RESOLVED_SENT,
        RouteReconciliationStatus.RESOLVED_TERMINAL,
    }
)


class PolicyFallbackTransportOutcomeAuthority(str, Enum):
    EGRESS_ROUTING_SERVER = "EGRESS_ROUTING_SERVER"


@dataclass(frozen=True, slots=True)
class PolicyFallbackTransportOutcomeBoundary:
    boundary_id: str
    authority: PolicyFallbackTransportOutcomeAuthority
    fallback: PolicyBasedFallbackBoundary
    outcome_status: TransportOutcomeStatus
    outcome_committed: bool
    new_fallback_effect_authorized: bool
    transport_terminal: bool
    parser_success_inferred: bool
    scan_success_inferred: bool
    notification_delivery_inferred: bool
    reason_codes: tuple[str, ...]
    evidence_reference_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "boundary_id", _require_text(self.boundary_id, "boundary_id"))
        _require_exact_enum(
            self.authority, PolicyFallbackTransportOutcomeAuthority, "authority"
        )
        if self.authority is not PolicyFallbackTransportOutcomeAuthority.EGRESS_ROUTING_SERVER:
            raise ValueError("authority must be EGRESS_ROUTING_SERVER")
        _require_exact_record(self.fallback, PolicyBasedFallbackBoundary, "fallback")
        _require_exact_enum(self.outcome_status, TransportOutcomeStatus, "outcome_status")
        _require_bool(self.outcome_committed, "outcome_committed")
        _require_bool(self.new_fallback_effect_authorized, "new_fallback_effect_authorized")
        _require_bool(self.transport_terminal, "transport_terminal")
        _require_bool(self.parser_success_inferred, "parser_success_inferred")
        _require_bool(self.scan_success_inferred, "scan_success_inferred")
        _require_bool(self.notification_delivery_inferred, "notification_delivery_inferred")
        reason_codes = _require_non_empty_text_tuple(self.reason_codes, "reason_codes")
        evidence_reference_ids = _require_non_empty_text_tuple(
            self.evidence_reference_ids, "evidence_reference_ids"
        )

        fallback = self.fallback
        _require_exact_enum(fallback.authority, RouteSelectionAuthority, "fallback.authority")
        if fallback.authority is not RouteSelectionAuthority.EGRESS_ROUTING_SERVER:
            raise ValueError("fallback.authority must be EGRESS_ROUTING_SERVER")
        _require_exact_record(
            fallback.original_selection,
            ServerRouteSelectionBoundary,
            "fallback.original_selection",
        )
        _require_exact_record(
            fallback.original_selection.decision,
            RouteSelectionDecision,
            "fallback.original_selection.decision",
        )
        _require_exact_record(fallback.decision, PolicyBasedFallbackDecision, "fallback.decision")

        fallback_status = fallback.decision.status
        _require_exact_enum(
            fallback_status, PolicyBasedFallbackStatus, "fallback.decision.status"
        )
        _require_exact_enum(
            fallback.decision.reconciliation_status,
            RouteReconciliationStatus,
            "fallback.decision.reconciliation_status",
        )
        _require_exact_enum(
            fallback.original_selection.authority,
            RouteSelectionAuthority,
            "fallback.original_selection.authority",
        )
        if fallback.original_selection.authority is not RouteSelectionAuthority.EGRESS_ROUTING_SERVER:
            raise ValueError("fallback.original_selection.authority must be EGRESS_ROUTING_SERVER")
        _require_exact_enum(
            fallback.original_selection.decision.status,
            RouteSelectionStatus,
            "fallback.original_selection.decision.status",
        )
        if fallback.original_selection.decision.status is not RouteSelectionStatus.SELECTED:
            raise ValueError("fallback.original_selection.decision.status must be SELECTED")

        _require_text(fallback.boundary_id, "fallback.boundary_id")
        fallback_request_reference = _require_text(
            fallback.request_reference, "fallback.request_reference"
        )
        fallback_requester_module = _require_text(
            fallback.requester_module, "fallback.requester_module"
        )
        fallback_environment_id = _require_text(fallback.environment_id, "fallback.environment_id")
        fallback_purpose = _require_text(fallback.purpose, "fallback.purpose")
        fallback_capability_scope = _require_non_empty_text_tuple(
            fallback.capability_scope, "fallback.capability_scope"
        )
        fallback_policy_reference = _require_text(
            fallback.fallback_policy_reference, "fallback.fallback_policy_reference"
        )
        fallback_original_failure_reference = _require_text(
            fallback.original_failure_reference, "fallback.original_failure_reference"
        )
        fallback_original_selection = fallback.original_selection
        _require_text(
            fallback_original_selection.boundary_id,
            "fallback.original_selection.boundary_id",
        )
        _require_text(
            fallback_original_selection.request_reference,
            "fallback.original_selection.request_reference",
        )
        _require_text(
            fallback_original_selection.requester_module,
            "fallback.original_selection.requester_module",
        )
        _require_text(
            fallback_original_selection.environment_id,
            "fallback.original_selection.environment_id",
        )
        _require_text(fallback_original_selection.purpose, "fallback.original_selection.purpose")
        fallback_original_selection_capability_scope = _require_non_empty_text_tuple(
            fallback_original_selection.capability_scope,
            "fallback.original_selection.capability_scope",
        )
        _require_text(
            fallback_original_selection.policy_reference,
            "fallback.original_selection.policy_reference",
        )
        fallback_original_selection_decision = fallback_original_selection.decision
        _require_text(
            fallback_original_selection_decision.decision_id,
            "fallback.original_selection.decision.decision_id",
        )
        _require_text(
            fallback_original_selection_decision.request_reference,
            "fallback.original_selection.decision.request_reference",
        )
        _require_text(
            fallback_original_selection_decision.policy_reference,
            "fallback.original_selection.decision.policy_reference",
        )
        fallback_original_selection_selected_route_id = _require_text(
            fallback_original_selection_decision.selected_route_id,
            "fallback.original_selection.decision.selected_route_id",
        )
        fallback_decision = fallback.decision
        _require_text(fallback_decision.decision_id, "fallback.decision.decision_id")
        fallback_decision_request_reference = _require_text(
            fallback_decision.request_reference, "fallback.decision.request_reference"
        )
        fallback_decision_policy_reference = _require_text(
            fallback_decision.policy_reference, "fallback.decision.policy_reference"
        )
        fallback_decision_from_route_id = _require_text(
            fallback_decision.from_route_id, "fallback.decision.from_route_id"
        )
        fallback_decision_original_failure_reference = _require_text(
            fallback_decision.original_failure_reference,
            "fallback.decision.original_failure_reference",
        )
        _require_non_empty_text_tuple(
            fallback_decision.reason_codes, "fallback.decision.reason_codes"
        )
        _require_non_empty_text_tuple(
            fallback_decision.evidence_reference_ids,
            "fallback.decision.evidence_reference_ids",
        )
        fallback_candidates = fallback.fallback_candidate_evaluations
        if type(fallback_candidates) is not tuple:
            raise ValueError("fallback.fallback_candidate_evaluations must be a tuple")

        candidate_route_ids: list[str] = []
        candidate_evaluation_ids: list[str] = []
        eligible_candidates: list[RouteCandidateEvaluation] = []
        for candidate in fallback_candidates:
            _require_exact_record(candidate, RouteCandidateEvaluation, "fallback candidate")
            _require_exact_enum(
                candidate.status,
                RouteCandidateEligibilityStatus,
                "fallback candidate.status",
            )
            candidate_evaluation_id = _require_text(
                candidate.evaluation_id, "candidate.evaluation_id"
            )
            candidate_request_reference = _require_text(
                candidate.request_reference, "candidate.request_reference"
            )
            candidate_requester_module = _require_text(
                candidate.requester_module, "candidate.requester_module"
            )
            candidate_environment_id = _require_text(
                candidate.environment_id, "candidate.environment_id"
            )
            candidate_purpose = _require_text(candidate.purpose, "candidate.purpose")
            candidate_capability_scope = _require_non_empty_text_tuple(
                candidate.capability_scope, "candidate.capability_scope"
            )
            candidate_policy_reference = _require_text(
                candidate.policy_reference, "candidate.policy_reference"
            )
            candidate_route_id = _require_text(candidate.route_id, "candidate.route_id")
            _require_text(candidate.agent_id, "candidate.agent_id")

            if candidate_request_reference != fallback_request_reference:
                raise ValueError("candidate request_reference must match fallback request_reference")
            if candidate_requester_module != fallback_requester_module:
                raise ValueError("candidate requester_module must match fallback requester_module")
            if candidate_environment_id != fallback_environment_id:
                raise ValueError("candidate environment_id must match fallback environment_id")
            if candidate_purpose != fallback_purpose:
                raise ValueError("candidate purpose must match fallback purpose")
            if candidate_capability_scope != fallback_capability_scope:
                raise ValueError("candidate capability_scope must match fallback capability_scope")
            if candidate_policy_reference != fallback_policy_reference:
                raise ValueError("candidate policy_reference must match fallback policy_reference")
            if candidate_route_id == fallback_original_selection_selected_route_id:
                raise ValueError("candidate route_id must differ from the originally selected route")

            candidate_evaluation_ids.append(candidate_evaluation_id)
            candidate_route_ids.append(candidate_route_id)
            if candidate.status is RouteCandidateEligibilityStatus.ELIGIBLE:
                eligible_candidates.append(candidate)

        if len(candidate_evaluation_ids) != len(set(candidate_evaluation_ids)):
            raise ValueError("fallback candidate evaluation ids must be unique")
        if len(candidate_route_ids) != len(set(candidate_route_ids)):
            raise ValueError("fallback candidate route ids must be unique")
        if fallback.original_selection.request_reference != fallback_request_reference:
            raise ValueError("fallback.original_selection.request_reference must match fallback")
        if fallback.original_selection.requester_module != fallback_requester_module:
            raise ValueError("fallback.original_selection.requester_module must match fallback")
        if fallback.original_selection.environment_id != fallback_environment_id:
            raise ValueError("fallback.original_selection.environment_id must match fallback")
        if fallback.original_selection.purpose != fallback_purpose:
            raise ValueError("fallback.original_selection.purpose must match fallback")
        if fallback_original_selection_capability_scope != fallback_capability_scope:
            raise ValueError("fallback.original_selection.capability_scope must match fallback")

        if fallback_decision_request_reference != fallback_request_reference:
            raise ValueError("fallback.decision.request_reference must match fallback")
        if fallback_decision_original_failure_reference != fallback_original_failure_reference:
            raise ValueError("fallback.decision.original_failure_reference must match fallback")
        if fallback_decision_from_route_id != fallback_original_selection_selected_route_id:
            raise ValueError("fallback.decision.from_route_id must match selected route")
        if fallback_decision_policy_reference != fallback_policy_reference:
            raise ValueError("fallback.decision.policy_reference must match fallback policy")
        if fallback.decision.reconciliation_status not in _ALLOWED_RECONCILIATION_STATUSES:
            raise ValueError("unsupported fallback reconciliation status")

        fallback_status = fallback.decision.status
        if fallback_status not in _STATUS_TO_OUTCOME:
            raise ValueError("unsupported policy fallback status")
        if self.outcome_status is not _STATUS_TO_OUTCOME[fallback_status]:
            raise ValueError("outcome_status must match fallback status")
        if self.transport_terminal is not _TERMINAL_BY_FALLBACK_STATUS[fallback_status]:
            raise ValueError("transport_terminal must match fallback status")
        if self.outcome_committed is not True:
            raise ValueError("outcome_committed must be True")
        if self.new_fallback_effect_authorized is not False:
            raise ValueError("new_fallback_effect_authorized must be False")
        if self.parser_success_inferred is not False:
            raise ValueError("parser_success_inferred must be False")
        if self.scan_success_inferred is not False:
            raise ValueError("scan_success_inferred must be False")
        if self.notification_delivery_inferred is not False:
            raise ValueError("notification_delivery_inferred must be False")

        if fallback_status is PolicyBasedFallbackStatus.ATTEMPTED:
            if fallback_decision.to_route_id is None:
                raise ValueError("attempted fallback must have to_route_id")
            fallback_decision_to_route_id = _require_text(
                fallback_decision.to_route_id, "fallback.decision.to_route_id"
            )
            if fallback_decision.bounded_attempt_reference is None:
                raise ValueError("attempted fallback must have bounded_attempt_reference")
            _require_text(
                fallback_decision.bounded_attempt_reference,
                "fallback.decision.bounded_attempt_reference",
            )
            if len(eligible_candidates) != 1:
                raise ValueError("attempted fallback requires exactly one eligible candidate")
            if eligible_candidates[0].route_id != fallback_decision_to_route_id:
                raise ValueError("attempted fallback target must match the eligible candidate")
        elif fallback_status is PolicyBasedFallbackStatus.EXHAUSTED:
            if fallback_decision.to_route_id is not None:
                raise ValueError("exhausted fallback must not have to_route_id")
            if fallback_decision.bounded_attempt_reference is None:
                raise ValueError("exhausted fallback must have bounded_attempt_reference")
            _require_text(
                fallback_decision.bounded_attempt_reference,
                "fallback.decision.bounded_attempt_reference",
            )
            if not fallback_candidates:
                raise ValueError("exhausted fallback requires candidates")
            if eligible_candidates:
                raise ValueError("exhausted fallback cannot expose eligible candidates")
        elif fallback_status is PolicyBasedFallbackStatus.NO_APPROVED_ROUTE:
            if fallback_decision.to_route_id is not None:
                raise ValueError("no approved route fallback must not have to_route_id")
            if fallback_decision.bounded_attempt_reference is not None:
                raise ValueError(
                    "no approved route fallback must not have bounded_attempt_reference"
                )
            if eligible_candidates:
                raise ValueError("no approved route fallback cannot expose eligible candidates")
        else:  # pragma: no cover - defensive rejection of exact matrix gaps
            raise ValueError("unsupported policy fallback status")

        object.__setattr__(self, "reason_codes", reason_codes)
        object.__setattr__(self, "evidence_reference_ids", evidence_reference_ids)
        object.__setattr__(self, "fallback", fallback)
