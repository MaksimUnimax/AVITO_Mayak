from __future__ import annotations

from dataclasses import fields, is_dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

import mayak.modules.egress_routing as egress_routing
import mayak.modules.egress_routing.outcome_fallback as outcome_fallback_module
from mayak.modules.egress_routing import (
    ER07E_TASK_ID,
    AgentLifecycleStatus,
    AgentRegistration,
    AgentRegistrationStatus,
    AgentRouteAssociation,
    AgentRouteAssociationStatus,
    AgentRouteRegistrationBoundary,
    EgressAgent,
    EgressRoute,
    PolicyBasedFallbackBoundary,
    PolicyBasedFallbackDecision,
    PolicyBasedFallbackStatus,
    PolicyFallbackTransportOutcomeAuthority,
    PolicyFallbackTransportOutcomeBoundary,
    RouteCandidateEligibilityStatus,
    RouteCandidateEvaluation,
    RouteCapability,
    RouteEvidenceStatus,
    RouteFamily,
    RouteHealthState,
    RouteHealthStatus,
    RouteLifecycleStatus,
    RouteReadinessDecision,
    RouteReadinessStatus,
    RouteReconciliationStatus,
    RouteRegistration,
    RouteRegistrationStatus,
    RouteRestrictionState,
    RouteRestrictionStatus,
    RouteSelectionAuthority,
    RouteSelectionDecision,
    RouteSelectionStatus,
    ServerRouteSelectionBoundary,
    SessionPolicyStatus,
    TransportOutcomeStatus,
)

EXPECTED_TASK_ID = "ER-07E-POLICY-FALLBACK-TRANSPORT-OUTCOME-BOUNDARY-20260715-023"

EXPECTED_MODULE_EXPORTS = (
    "ER07E_TASK_ID",
    "PolicyFallbackTransportOutcomeAuthority",
    "PolicyFallbackTransportOutcomeBoundary",
)

EXPECTED_PACKAGE_EXPORTS = (
    "MODULE_ID",
    "AgentLifecycleStatus",
    "DiagnosticEvidenceKind",
    "DispatchAttempt",
    "DispatchStatus",
    "EgressAgent",
    "EgressRoute",
    "PolicyBasedFallbackDecision",
    "PolicyBasedFallbackStatus",
    "RouteCapability",
    "RouteEvidenceReference",
    "RouteEvidenceStatus",
    "RouteFamily",
    "RouteHealthState",
    "RouteHealthStatus",
    "RouteLease",
    "RouteLeaseStatus",
    "RouteLifecycleStatus",
    "RouteQuarantineDecision",
    "RouteQuarantineStatus",
    "RouteReadinessDecision",
    "RouteReadinessStatus",
    "RouteReconciliationState",
    "RouteReconciliationStatus",
    "RouteRestrictionState",
    "RouteRestrictionStatus",
    "RouteSelectionDecision",
    "RouteSelectionStatus",
    "SafeOperationalDiagnostic",
    "SessionPolicyStatus",
    "TransportAssignment",
    "TransportAssignmentOutcome",
    "TransportOutcomeStatus",
    "ER03_TASK_ID",
    "AgentRegistrationStatus",
    "RouteRegistrationStatus",
    "AgentRouteAssociationStatus",
    "AgentRegistration",
    "RouteRegistration",
    "AgentRouteAssociation",
    "AgentRouteRegistrationBoundary",
    "ER05A_TASK_ID",
    "RouteSelectionAuthority",
    "RouteCandidateEligibilityStatus",
    "RouteCandidateEvaluation",
    "ServerRouteSelectionBoundary",
    "ER05B_TASK_ID",
    "PolicyBasedFallbackBoundary",
    "ER06A_TASK_ID",
    "RouteLeaseAuthority",
    "RouteLeaseAuthorizationBoundary",
    "ER06B_TASK_ID",
    "TransportAssignmentAuthority",
    "TransportAssignmentCommitmentBoundary",
    "ER06C_TASK_ID",
    "TransportDispatchAuthority",
    "TransportDispatchAttemptBoundary",
    "ER06D_TASK_ID",
    "TransportDispatchReplayAuthority",
    "TransportDispatchReplayBoundary",
    "ER06E_TASK_ID",
    "TransportDispatchReconciliationAuthority",
    "TransportDispatchReconciliationBoundary",
    "ER06F_TASK_ID",
    "TransportDispatchReconciliationResolutionAuthority",
    "TransportDispatchReconciliationResolutionBoundary",
    "ER07A_TASK_ID",
    "TransportOutcomeCommitmentAuthority",
    "TransportOutcomeCommitmentBoundary",
    "ER07B_TASK_ID",
    "TransportAvailabilityOutcomeAuthority",
    "TransportAvailabilityOutcomeBoundary",
    "ER07C_TASK_ID",
    "TransportResponsePresenceOutcomeAuthority",
    "TransportResponsePresenceOutcomeBoundary",
    "ER07D_TASK_ID",
    "TransportResponseFailureOutcomeAuthority",
    "TransportResponseFailureOutcomeBoundary",
    "ER08A_TASK_ID",
    "TransportRestrictionSignalAuthority",
    "TransportRestrictionSignalKind",
    "TransportRestrictionSignalBoundary",
    "ER08B_TASK_ID",
    "TransportRestrictionEvaluationAuthority",
    "TransportRestrictionEvaluationGateBoundary",
    "ER09A_TASK_ID",
    "EgressSessionSecretAuthority",
    "EgressSessionSecretGateBoundary",
    "ER10A_TASK_ID",
    "FutureBrowserFallbackAuthority",
    "FutureBrowserFallbackGateBoundary",
    "ER07E_TASK_ID",
    "PolicyFallbackTransportOutcomeAuthority",
    "PolicyFallbackTransportOutcomeBoundary",
    "ER02_TASK_ID",
    "EGRESS_SYNTHETIC_FIXTURE_IDS",
    "EGRESS_SYNTHETIC_FIXTURES",
    "EgressSyntheticFixture",
)

EXPECTED_FIELD_NAMES = (
    "boundary_id",
    "authority",
    "fallback",
    "outcome_status",
    "outcome_committed",
    "new_fallback_effect_authorized",
    "transport_terminal",
    "parser_success_inferred",
    "scan_success_inferred",
    "notification_delivery_inferred",
    "reason_codes",
    "evidence_reference_ids",
)

EXPECTED_FALLBACK_STATUSES = (
    PolicyBasedFallbackStatus.ATTEMPTED,
    PolicyBasedFallbackStatus.EXHAUSTED,
    PolicyBasedFallbackStatus.NO_APPROVED_ROUTE,
)

EXPECTED_RECONCILIATION_STATUSES = (
    RouteReconciliationStatus.NOT_REQUIRED,
    RouteReconciliationStatus.RESOLVED_NOT_SENT,
    RouteReconciliationStatus.RESOLVED_SENT,
    RouteReconciliationStatus.RESOLVED_TERMINAL,
)

EXPECTED_STATUS_TO_OUTCOME = {
    PolicyBasedFallbackStatus.ATTEMPTED: TransportOutcomeStatus.POLICY_FALLBACK_ATTEMPTED,
    PolicyBasedFallbackStatus.EXHAUSTED: TransportOutcomeStatus.POLICY_FALLBACK_EXHAUSTED,
    PolicyBasedFallbackStatus.NO_APPROVED_ROUTE: TransportOutcomeStatus.NO_APPROVED_ROUTE_AVAILABLE,
}

EXPECTED_TERMINAL_BY_FALLBACK_STATUS = {
    PolicyBasedFallbackStatus.ATTEMPTED: False,
    PolicyBasedFallbackStatus.EXHAUSTED: True,
    PolicyBasedFallbackStatus.NO_APPROVED_ROUTE: True,
}

EXPECTED_POSITIVE_COMBINATIONS = 12


class TextLike(str):
    pass


class TupleLike(tuple):
    pass


_LOOKALIKE = SimpleNamespace(name="EGRESS_ROUTING_SERVER", value="EGRESS_ROUTING_SERVER")


def _mutate(record: object, **changes: object) -> None:
    for field_name, value in changes.items():
        object.__setattr__(record, field_name, value)


def _enum_lookalike(name: str) -> SimpleNamespace:
    return SimpleNamespace(name=name, value=name)


def _set_path(root: object, path: tuple[str | int, ...], value: object) -> None:
    target: Any = root
    for field_name in path[:-1]:
        target = target[field_name] if isinstance(field_name, int) else getattr(target, field_name)
    leaf = cast(str, path[-1])
    object.__setattr__(target, leaf, value)


def _namespace_copy(record: object, **changes: object) -> SimpleNamespace:
    record_instance = cast(Any, record)
    payload = {
        field.name: getattr(record_instance, field.name) for field in fields(record_instance)
    }
    payload.update(changes)
    return SimpleNamespace(**payload)


def _field_names(record_cls: Any) -> tuple[str, ...]:
    return tuple(field.name for field in fields(record_cls))


def _candidate(
    route_id: str = "route-target-01",
    agent_id: str = "agent-target-01",
    *,
    request_reference: str = "request-01",
    requester_module: str = "07-egress-routing",
    environment_id: str = "env-01",
    purpose: str = "search",
    capability_scope: tuple[str, ...] = ("search",),
    policy_reference: str = "fallback-policy-01",
    route_family: RouteFamily = RouteFamily.LINUX_REFERENCE_STYLE_ROUTE,
    route_lifecycle_status: RouteLifecycleStatus = RouteLifecycleStatus.READY,
    agent_lifecycle_status: AgentLifecycleStatus = AgentLifecycleStatus.READY,
    capability_evidence_status: RouteEvidenceStatus = RouteEvidenceStatus.CURRENT,
    readiness_status: RouteReadinessStatus = RouteReadinessStatus.READY,
    health_status: RouteHealthStatus = RouteHealthStatus.READY,
    restriction_status: RouteRestrictionStatus = RouteRestrictionStatus.NONE,
    blocks_new_assignments: bool = False,
    reconciliation_status: RouteReconciliationStatus = RouteReconciliationStatus.NOT_REQUIRED,
    status: RouteCandidateEligibilityStatus = RouteCandidateEligibilityStatus.ELIGIBLE,
    reason_codes: tuple[str, ...] = (),
    evidence_reference_ids: tuple[str, ...] = ("evidence-candidate-01",),
) -> RouteCandidateEvaluation:
    agent = EgressAgent(
        agent_id=agent_id,
        agent_class="LinuxReferenceStyleAgent",
        environment_id=environment_id,
        lifecycle_status=agent_lifecycle_status,
        trust_scope=("egress", "safe-routing"),
        source_release_reference="release-20260712",
        credential_reference="opaque-credential-ref",
        evidence_reference_ids=("evidence-agent-01",),
    )
    route = EgressRoute(
        route_id=route_id,
        route_family=route_family,
        environment_id=environment_id,
        agent_id=agent_id,
        purpose_scope=("search", "dispatch"),
        capability_ids=("cap-01",),
        lifecycle_status=route_lifecycle_status,
        evidence_reference_ids=("evidence-route-01",),
    )
    agent_registration = AgentRegistration(
        registration_id=f"{agent_id}-registration",
        agent_id=agent_id,
        environment_id=environment_id,
        agent_class="LinuxReferenceStyleAgent",
        accountable_owner_reference="owner-01",
        purpose_scope=("egress", "safe-routing"),
        trust_scope=("egress", "safe-routing"),
        source_release_reference="release-20260712",
        credential_reference="opaque-credential-ref",
        connectivity_boundary_reference="connectivity-boundary-01",
        isolation_boundary_reference="isolation-boundary-01",
        privacy_boundary_reference="privacy-boundary-01",
        replaceable_execution_dependency=True,
        primary_database_access_allowed=False,
        business_state_ownership_allowed=False,
        public_unauthenticated_inbound_allowed=False,
        foreign_resource_reuse_allowed=False,
        arbitrary_command_execution_allowed=False,
        status=AgentRegistrationStatus.REGISTERED,
        reason_codes=(),
        evidence_reference_ids=("evidence-agent-registration-01",),
    )
    route_registration = RouteRegistration(
        registration_id=f"{route_id}-registration",
        route_id=route_id,
        agent_id=agent_id,
        agent_registration_id=agent_registration.registration_id,
        environment_id=environment_id,
        source_release_reference="release-20260712",
        route_family=route_family,
        purpose_scope=("search", "dispatch"),
        capability_ids=("cap-01",),
        unsupported_classes=(),
        evidence_status=RouteEvidenceStatus.CURRENT,
        session_policy_status=SessionPolicyStatus.APPROVED_REFERENCE_ONLY,
        restriction_reference=None,
        selection_policy_reference="selection-policy-01",
        privacy_boundary_reference="privacy-boundary-01",
        status=RouteRegistrationStatus.REGISTERED,
        reason_codes=(),
        evidence_reference_ids=("evidence-route-registration-01",),
    )
    association = AgentRouteAssociation(
        association_id=f"{route_id}-association",
        agent_id=agent_id,
        route_id=route_id,
        environment_id=environment_id,
        agent_registration_id=agent_registration.registration_id,
        route_registration_id=route_registration.registration_id,
        purpose_scope=("search", "dispatch"),
        status=AgentRouteAssociationStatus.ACTIVE,
        reason_codes=(),
        evidence_reference_ids=("evidence-association-01",),
    )
    boundary = AgentRouteRegistrationBoundary(
        boundary_id=f"{route_id}-boundary",
        agent=agent,
        agent_registration=agent_registration,
        route=route,
        route_registration=route_registration,
        association=association,
    )
    capability = RouteCapability(
        capability_id="cap-01",
        route_id=route_id,
        destination_scope=("destination-01",),
        operation_classes=("search", "dispatch"),
        unsupported_classes=("billing",),
        evidence_reference_ids=("evidence-capability-01",),
        evidence_status=capability_evidence_status,
        session_policy_status=SessionPolicyStatus.APPROVED_REFERENCE_ONLY,
    )
    readiness = RouteReadinessDecision(
        decision_id=f"{route_id}-readiness",
        route_id=route_id,
        readiness_status=readiness_status,
        reason_codes=("ready",),
        evidence_reference_ids=("evidence-readiness-01",),
        policy_reference="policy-01",
    )
    health = RouteHealthState(
        route_id=route_id,
        health_status=health_status,
        reason_codes=("healthy",),
        evidence_reference_ids=("evidence-health-01",),
        observed_at_reference="ts-01",
    )
    restriction = RouteRestrictionState(
        restriction_id=f"{route_id}-restriction",
        route_id=route_id,
        status=restriction_status,
        reason_codes=("restriction",),
        evidence_reference_ids=("evidence-restriction-01",),
        blocks_new_assignments=blocks_new_assignments,
        review_reference=None,
    )
    return RouteCandidateEvaluation(
        evaluation_id=f"{route_id}-evaluation",
        request_reference=request_reference,
        requester_module=requester_module,
        environment_id=environment_id,
        purpose=purpose,
        capability_scope=capability_scope,
        policy_reference=policy_reference,
        route_id=route_id,
        agent_id=agent_id,
        registration_boundary=boundary,
        capability=capability,
        readiness=readiness,
        health=health,
        restriction=restriction,
        reconciliation_status=reconciliation_status,
        status=status,
        reason_codes=reason_codes,
        evidence_reference_ids=evidence_reference_ids,
    )


def _selection_decision(selected_route_id: str) -> RouteSelectionDecision:
    return RouteSelectionDecision(
        decision_id="selection-decision-01",
        request_reference="request-01",
        status=RouteSelectionStatus.SELECTED,
        selected_route_id=selected_route_id,
        candidate_route_ids=("route-source-01", "route-source-02"),
        rejected_route_ids=("route-source-02",),
        reason_codes=("selected",),
        evidence_reference_ids=("evidence-selection-01",),
        policy_reference="selection-policy-01",
    )


def _original_selection() -> ServerRouteSelectionBoundary:
    selected = _candidate(
        route_id="route-source-01",
        agent_id="agent-source-01",
        policy_reference="selection-policy-01",
        status=RouteCandidateEligibilityStatus.ELIGIBLE,
    )
    policy_rejected = _candidate(
        route_id="route-source-02",
        agent_id="agent-source-02",
        policy_reference="selection-policy-01",
        status=RouteCandidateEligibilityStatus.POLICY_REJECTED,
        reason_codes=("policy-rejected",),
    )
    return ServerRouteSelectionBoundary(
        boundary_id="selection-boundary-01",
        authority=RouteSelectionAuthority.EGRESS_ROUTING_SERVER,
        request_reference="request-01",
        requester_module="07-egress-routing",
        environment_id="env-01",
        purpose="search",
        capability_scope=("search",),
        policy_reference="selection-policy-01",
        candidate_evaluations=(selected, policy_rejected),
        decision=_selection_decision("route-source-01"),
    )


def _fallback_candidates(
    status: PolicyBasedFallbackStatus,
) -> tuple[RouteCandidateEvaluation, ...]:
    if status is PolicyBasedFallbackStatus.ATTEMPTED:
        return (
            _candidate(
                route_id="route-target-01",
                agent_id="agent-target-01",
                policy_reference="fallback-policy-01",
                status=RouteCandidateEligibilityStatus.ELIGIBLE,
            ),
            _candidate(
                route_id="route-target-02",
                agent_id="agent-target-02",
                policy_reference="fallback-policy-01",
                status=RouteCandidateEligibilityStatus.POLICY_REJECTED,
                reason_codes=("policy-rejected",),
            ),
        )
    if status is PolicyBasedFallbackStatus.EXHAUSTED:
        return (
            _candidate(
                route_id="route-target-03",
                agent_id="agent-target-03",
                policy_reference="fallback-policy-01",
                status=RouteCandidateEligibilityStatus.POLICY_REJECTED,
                reason_codes=("policy-rejected",),
            ),
            _candidate(
                route_id="route-target-04",
                agent_id="agent-target-04",
                policy_reference="fallback-policy-01",
                status=RouteCandidateEligibilityStatus.POLICY_REJECTED,
                reason_codes=("policy-rejected",),
            ),
        )
    return (
        _candidate(
            route_id="route-target-05",
            agent_id="agent-target-05",
            policy_reference="fallback-policy-01",
            status=RouteCandidateEligibilityStatus.POLICY_REJECTED,
            reason_codes=("policy-rejected",),
        ),
    )


def _fallback_decision(
    status: PolicyBasedFallbackStatus,
    reconciliation_status: RouteReconciliationStatus,
) -> PolicyBasedFallbackDecision:
    if status is PolicyBasedFallbackStatus.ATTEMPTED:
        to_route_id = "route-target-01"
        bounded_attempt_reference = "bounded-attempt-01"
    elif status is PolicyBasedFallbackStatus.EXHAUSTED:
        to_route_id = None
        bounded_attempt_reference = "bounded-attempt-01"
    else:
        to_route_id = None
        bounded_attempt_reference = None

    return PolicyBasedFallbackDecision(
        decision_id="fallback-decision-01",
        request_reference="request-01",
        status=status,
        policy_reference="fallback-policy-01",
        from_route_id="route-source-01",
        to_route_id=to_route_id,
        reason_codes=("fallback-policy",),
        evidence_reference_ids=("evidence-fallback-01",),
        bounded_attempt_reference=bounded_attempt_reference,
        original_failure_reference="failure-01",
        reconciliation_status=reconciliation_status,
    )


def _fallback_boundary(
    status: PolicyBasedFallbackStatus,
    reconciliation_status: RouteReconciliationStatus,
    *,
    candidates: tuple[RouteCandidateEvaluation, ...] | None = None,
) -> PolicyBasedFallbackBoundary:
    return PolicyBasedFallbackBoundary(
        boundary_id="fallback-boundary-01",
        authority=RouteSelectionAuthority.EGRESS_ROUTING_SERVER,
        request_reference="request-01",
        requester_module="07-egress-routing",
        environment_id="env-01",
        purpose="search",
        capability_scope=("search",),
        fallback_policy_reference="fallback-policy-01",
        original_selection=_original_selection(),
        original_failure_reference="failure-01",
        fallback_candidate_evaluations=_fallback_candidates(status)
        if candidates is None
        else candidates,
        decision=_fallback_decision(status, reconciliation_status),
    )


def _construct(
    *,
    fallback_status: PolicyBasedFallbackStatus,
    reconciliation_status: RouteReconciliationStatus,
    candidates: tuple[RouteCandidateEvaluation, ...] | None = None,
    outcome_status: TransportOutcomeStatus | None = None,
    transport_terminal: bool | None = None,
    outcome_committed: bool = True,
    new_fallback_effect_authorized: bool = False,
    parser_success_inferred: bool = False,
    scan_success_inferred: bool = False,
    notification_delivery_inferred: bool = False,
    authority: PolicyFallbackTransportOutcomeAuthority = (
        PolicyFallbackTransportOutcomeAuthority.EGRESS_ROUTING_SERVER
    ),
) -> PolicyFallbackTransportOutcomeBoundary:
    fallback = _fallback_boundary(fallback_status, reconciliation_status, candidates=candidates)
    return PolicyFallbackTransportOutcomeBoundary(
        boundary_id="outcome-fallback-boundary-01",
        authority=authority,
        fallback=fallback,
        outcome_status=outcome_status or EXPECTED_STATUS_TO_OUTCOME[fallback_status],
        outcome_committed=outcome_committed,
        new_fallback_effect_authorized=new_fallback_effect_authorized,
        transport_terminal=EXPECTED_TERMINAL_BY_FALLBACK_STATUS[fallback_status]
        if transport_terminal is None
        else transport_terminal,
        parser_success_inferred=parser_success_inferred,
        scan_success_inferred=scan_success_inferred,
        notification_delivery_inferred=notification_delivery_inferred,
        reason_codes=("policy-fallback-transport",),
        evidence_reference_ids=("evidence-outcome-fallback-01",),
    )


def _rebuild_boundary(
    boundary: PolicyFallbackTransportOutcomeBoundary,
) -> PolicyFallbackTransportOutcomeBoundary:
    return PolicyFallbackTransportOutcomeBoundary(
        boundary_id=boundary.boundary_id,
        authority=boundary.authority,
        fallback=boundary.fallback,
        outcome_status=boundary.outcome_status,
        outcome_committed=boundary.outcome_committed,
        new_fallback_effect_authorized=boundary.new_fallback_effect_authorized,
        transport_terminal=boundary.transport_terminal,
        parser_success_inferred=boundary.parser_success_inferred,
        scan_success_inferred=boundary.scan_success_inferred,
        notification_delivery_inferred=boundary.notification_delivery_inferred,
        reason_codes=boundary.reason_codes,
        evidence_reference_ids=boundary.evidence_reference_ids,
    )


def _base_boundary(
    fallback_status: PolicyBasedFallbackStatus = PolicyBasedFallbackStatus.ATTEMPTED,
    reconciliation_status: RouteReconciliationStatus = RouteReconciliationStatus.NOT_REQUIRED,
) -> PolicyFallbackTransportOutcomeBoundary:
    return _construct(
        fallback_status=fallback_status,
        reconciliation_status=reconciliation_status,
    )


def test_public_surface_and_exports_are_exact() -> None:
    source = Path("src/mayak/modules/egress_routing/outcome_fallback.py").read_text(
        encoding="utf-8"
    )

    assert source.count(EXPECTED_TASK_ID) == 1
    assert ER07E_TASK_ID == EXPECTED_TASK_ID
    assert outcome_fallback_module.__all__ == EXPECTED_MODULE_EXPORTS
    assert type(outcome_fallback_module.__all__) is tuple
    assert egress_routing.__all__ == EXPECTED_PACKAGE_EXPORTS
    assert type(egress_routing.__all__) is tuple
    assert tuple(member.name for member in PolicyFallbackTransportOutcomeAuthority) == (
        "EGRESS_ROUTING_SERVER",
    )
    assert (
        PolicyFallbackTransportOutcomeAuthority.EGRESS_ROUTING_SERVER.value
        == "EGRESS_ROUTING_SERVER"
    )
    assert is_dataclass(PolicyFallbackTransportOutcomeBoundary)
    assert cast(Any, PolicyFallbackTransportOutcomeBoundary).__dataclass_params__.frozen is True
    assert hasattr(PolicyFallbackTransportOutcomeBoundary, "__slots__")
    assert _field_names(PolicyFallbackTransportOutcomeBoundary) == EXPECTED_FIELD_NAMES
    assert len(egress_routing.EGRESS_SYNTHETIC_FIXTURE_IDS) == 34


@pytest.mark.parametrize("fallback_status", EXPECTED_FALLBACK_STATUSES)
@pytest.mark.parametrize("reconciliation_status", EXPECTED_RECONCILIATION_STATUSES)
def test_all_positive_combinations_are_accepted(
    fallback_status: PolicyBasedFallbackStatus,
    reconciliation_status: RouteReconciliationStatus,
) -> None:
    boundary = _construct(
        fallback_status=fallback_status,
        reconciliation_status=reconciliation_status,
    )

    assert type(boundary) is PolicyFallbackTransportOutcomeBoundary
    assert type(boundary.fallback) is PolicyBasedFallbackBoundary
    assert type(boundary.fallback.decision) is PolicyBasedFallbackDecision
    assert type(boundary.fallback.original_selection) is ServerRouteSelectionBoundary
    assert type(boundary.fallback.original_selection.decision) is RouteSelectionDecision
    assert type(boundary.fallback.fallback_candidate_evaluations) is tuple
    assert boundary.authority is PolicyFallbackTransportOutcomeAuthority.EGRESS_ROUTING_SERVER
    assert boundary.fallback.authority is RouteSelectionAuthority.EGRESS_ROUTING_SERVER
    assert (
        boundary.fallback.original_selection.authority
        is RouteSelectionAuthority.EGRESS_ROUTING_SERVER
    )
    assert boundary.fallback.original_selection.decision.status is RouteSelectionStatus.SELECTED
    assert boundary.outcome_status is EXPECTED_STATUS_TO_OUTCOME[fallback_status]
    assert boundary.transport_terminal is EXPECTED_TERMINAL_BY_FALLBACK_STATUS[fallback_status]
    assert boundary.outcome_committed is True
    assert boundary.new_fallback_effect_authorized is False
    assert boundary.parser_success_inferred is False
    assert boundary.scan_success_inferred is False
    assert boundary.notification_delivery_inferred is False
    assert boundary.reason_codes == ("policy-fallback-transport",)
    assert boundary.evidence_reference_ids == ("evidence-outcome-fallback-01",)
    assert boundary.fallback.decision.reason_codes == ("fallback-policy",)
    assert boundary.fallback.decision.evidence_reference_ids == ("evidence-fallback-01",)
    assert (
        boundary.fallback.original_selection.request_reference
        == boundary.fallback.request_reference
    )
    assert (
        boundary.fallback.original_selection.requester_module == boundary.fallback.requester_module
    )
    assert boundary.fallback.original_selection.environment_id == boundary.fallback.environment_id
    assert boundary.fallback.original_selection.purpose == boundary.fallback.purpose
    assert (
        boundary.fallback.original_selection.capability_scope == boundary.fallback.capability_scope
    )
    assert boundary.fallback.decision.request_reference == boundary.fallback.request_reference
    assert (
        boundary.fallback.decision.original_failure_reference
        == boundary.fallback.original_failure_reference
    )
    assert (
        boundary.fallback.decision.from_route_id
        == boundary.fallback.original_selection.decision.selected_route_id
    )
    assert (
        boundary.fallback.decision.policy_reference == boundary.fallback.fallback_policy_reference
    )
    assert (
        boundary.fallback.original_selection.decision.request_reference
        == boundary.fallback.request_reference
    )
    assert (
        boundary.fallback.original_selection.decision.policy_reference
        == boundary.fallback.original_selection.policy_reference
    )

    candidates = boundary.fallback.fallback_candidate_evaluations
    assert all(type(candidate) is RouteCandidateEvaluation for candidate in candidates)
    assert all(
        type(candidate.status) is RouteCandidateEligibilityStatus for candidate in candidates
    )
    assert len({candidate.evaluation_id for candidate in candidates}) == len(candidates)
    assert len({candidate.route_id for candidate in candidates}) == len(candidates)
    assert all(
        candidate.request_reference == boundary.fallback.request_reference
        for candidate in candidates
    )
    assert all(
        candidate.requester_module == boundary.fallback.requester_module for candidate in candidates
    )
    assert all(
        candidate.environment_id == boundary.fallback.environment_id for candidate in candidates
    )
    assert all(candidate.purpose == boundary.fallback.purpose for candidate in candidates)
    assert all(
        candidate.capability_scope == boundary.fallback.capability_scope for candidate in candidates
    )
    assert all(
        candidate.policy_reference == boundary.fallback.fallback_policy_reference
        for candidate in candidates
    )

    if fallback_status is PolicyBasedFallbackStatus.ATTEMPTED:
        eligible_candidates = tuple(
            candidate
            for candidate in candidates
            if candidate.status is RouteCandidateEligibilityStatus.ELIGIBLE
        )
        assert len(candidates) == 2
        assert len(eligible_candidates) == 1
        assert eligible_candidates[0].route_id == boundary.fallback.decision.to_route_id
        assert boundary.fallback.decision.to_route_id is not None
        assert boundary.fallback.decision.bounded_attempt_reference == "bounded-attempt-01"
    elif fallback_status is PolicyBasedFallbackStatus.EXHAUSTED:
        assert len(candidates) == 2
        assert not any(
            candidate.status is RouteCandidateEligibilityStatus.ELIGIBLE for candidate in candidates
        )
        assert boundary.fallback.decision.to_route_id is None
        assert boundary.fallback.decision.bounded_attempt_reference == "bounded-attempt-01"
    else:
        assert len(candidates) == 1
        assert not any(
            candidate.status is RouteCandidateEligibilityStatus.ELIGIBLE for candidate in candidates
        )
        assert boundary.fallback.decision.to_route_id is None
        assert boundary.fallback.decision.bounded_attempt_reference is None


def test_no_approved_route_accepts_empty_candidate_tuple() -> None:
    boundary = _construct(
        fallback_status=PolicyBasedFallbackStatus.NO_APPROVED_ROUTE,
        reconciliation_status=RouteReconciliationStatus.NOT_REQUIRED,
        candidates=(),
    )

    assert boundary.outcome_status is TransportOutcomeStatus.NO_APPROVED_ROUTE_AVAILABLE
    assert boundary.transport_terminal is True
    assert boundary.fallback.fallback_candidate_evaluations == ()
    assert boundary.fallback.decision.to_route_id is None
    assert boundary.fallback.decision.bounded_attempt_reference is None


@pytest.mark.parametrize(
    "fallback_status",
    (
        PolicyBasedFallbackStatus.NOT_EVALUATED,
        PolicyBasedFallbackStatus.NOT_ALLOWED,
        PolicyBasedFallbackStatus.ALLOWED,
        PolicyBasedFallbackStatus.BLOCKED_RECONCILIATION_REQUIRED,
    ),
)
def test_other_fallback_statuses_are_rejected(
    fallback_status: PolicyBasedFallbackStatus,
) -> None:
    boundary = _base_boundary()
    _set_path(boundary, ("fallback", "decision", "status"), fallback_status)

    with pytest.raises(ValueError):
        _rebuild_boundary(boundary)


@pytest.mark.parametrize(
    "outcome_status",
    tuple(
        status
        for status in TransportOutcomeStatus
        if status
        not in {
            TransportOutcomeStatus.POLICY_FALLBACK_ATTEMPTED,
            TransportOutcomeStatus.POLICY_FALLBACK_EXHAUSTED,
            TransportOutcomeStatus.NO_APPROVED_ROUTE_AVAILABLE,
        }
    ),
)
def test_other_transport_outcomes_are_rejected(outcome_status: TransportOutcomeStatus) -> None:
    boundary = _base_boundary()
    _set_path(boundary, ("outcome_status",), outcome_status)

    with pytest.raises(ValueError):
        _rebuild_boundary(boundary)


@pytest.mark.parametrize(
    "reconciliation_status",
    (
        RouteReconciliationStatus.REQUIRED,
        RouteReconciliationStatus.PENDING,
        RouteReconciliationStatus.REMAINS_AMBIGUOUS,
        RouteReconciliationStatus.MANUAL_REVIEW_REQUIRED,
    ),
)
def test_unresolved_reconciliation_statuses_are_rejected(
    reconciliation_status: RouteReconciliationStatus,
) -> None:
    boundary = _base_boundary()
    _set_path(boundary, ("fallback", "decision", "reconciliation_status"), reconciliation_status)

    with pytest.raises(ValueError):
        _rebuild_boundary(boundary)


@pytest.mark.parametrize(
    ("path", "invalid_value"),
    [
        (("authority",), "EGRESS_ROUTING_SERVER"),
        (("authority",), TextLike("EGRESS_ROUTING_SERVER")),
        (("authority",), _LOOKALIKE),
        (("fallback", "authority"), "EGRESS_ROUTING_SERVER"),
        (("fallback", "authority"), TextLike("EGRESS_ROUTING_SERVER")),
        (("fallback", "authority"), _LOOKALIKE),
        (("fallback", "decision", "status"), "ATTEMPTED"),
        (("fallback", "decision", "status"), TextLike("ATTEMPTED")),
        (("fallback", "decision", "status"), _enum_lookalike("ATTEMPTED")),
        (("fallback", "decision", "reconciliation_status"), "NOT_REQUIRED"),
        (("fallback", "decision", "reconciliation_status"), TextLike("NOT_REQUIRED")),
        (("fallback", "decision", "reconciliation_status"), _enum_lookalike("NOT_REQUIRED")),
        (("fallback", "original_selection", "authority"), "EGRESS_ROUTING_SERVER"),
        (("fallback", "original_selection", "authority"), TextLike("EGRESS_ROUTING_SERVER")),
        (("fallback", "original_selection", "authority"), _LOOKALIKE),
        (("fallback", "original_selection", "decision", "status"), "SELECTED"),
        (("fallback", "original_selection", "decision", "status"), TextLike("SELECTED")),
        (("fallback", "original_selection", "decision", "status"), _enum_lookalike("SELECTED")),
        (("fallback", "fallback_candidate_evaluations", 0, "status"), "ELIGIBLE"),
        (("fallback", "fallback_candidate_evaluations", 0, "status"), TextLike("ELIGIBLE")),
        (("fallback", "fallback_candidate_evaluations", 0, "status"), _enum_lookalike("ELIGIBLE")),
        (("outcome_status",), "POLICY_FALLBACK_ATTEMPTED"),
        (("outcome_status",), TextLike("POLICY_FALLBACK_ATTEMPTED")),
        (("outcome_status",), _enum_lookalike("POLICY_FALLBACK_ATTEMPTED")),
    ],
)
def test_exact_enum_validation_rejects_non_exact_members(
    path: tuple[str | int, ...],
    invalid_value: object,
) -> None:
    boundary = _base_boundary()
    _set_path(boundary, path, invalid_value)

    with pytest.raises(ValueError):
        _rebuild_boundary(boundary)


@pytest.mark.parametrize(
    ("path", "invalid_value"),
    [
        (("boundary_id",), " "),
        (("boundary_id",), TextLike("boundary-01")),
        (("boundary_id",), b"boundary-01"),
        (("fallback", "boundary_id"), " "),
        (("fallback", "request_reference"), TextLike("request-01")),
        (("fallback", "requester_module"), b"07-egress-routing"),
        (("fallback", "environment_id"), SimpleNamespace(value="env-01")),
        (("fallback", "purpose"), " "),
        (("fallback", "fallback_policy_reference"), TextLike("fallback-policy-01")),
        (("fallback", "original_failure_reference"), b"failure-01"),
        (("fallback", "decision", "decision_id"), " "),
        (("fallback", "decision", "request_reference"), TextLike("request-01")),
        (("fallback", "decision", "policy_reference"), b"fallback-policy-01"),
        (("fallback", "decision", "from_route_id"), " "),
        (("fallback", "decision", "original_failure_reference"), TextLike("failure-01")),
        (("fallback", "decision", "to_route_id"), " "),
        (("fallback", "decision", "to_route_id"), TextLike("route-target-01")),
        (("fallback", "decision", "to_route_id"), b"route-target-01"),
        (("fallback", "decision", "to_route_id"), SimpleNamespace(value="route-target-01")),
        (("fallback", "decision", "bounded_attempt_reference"), " "),
        (("fallback", "decision", "bounded_attempt_reference"), TextLike("bounded-attempt-01")),
        (("fallback", "decision", "bounded_attempt_reference"), b"bounded-attempt-01"),
        (
            ("fallback", "decision", "bounded_attempt_reference"),
            SimpleNamespace(value="bounded-attempt-01"),
        ),
        (("fallback", "original_selection", "boundary_id"), " "),
        (("fallback", "original_selection", "request_reference"), TextLike("request-01")),
        (("fallback", "original_selection", "requester_module"), b"07-egress-routing"),
        (("fallback", "original_selection", "environment_id"), SimpleNamespace(value="env-01")),
        (("fallback", "original_selection", "purpose"), " "),
        (("fallback", "original_selection", "policy_reference"), TextLike("selection-policy-01")),
        (("fallback", "original_selection", "decision", "decision_id"), " "),
        (
            ("fallback", "original_selection", "decision", "request_reference"),
            TextLike("request-01"),
        ),
        (
            ("fallback", "original_selection", "decision", "policy_reference"),
            b"selection-policy-01",
        ),
        (("fallback", "original_selection", "decision", "selected_route_id"), " "),
        (("fallback", "fallback_candidate_evaluations", 0, "evaluation_id"), " "),
        (("fallback", "fallback_candidate_evaluations", 0, "request_reference"), b"request-01"),
        (
            ("fallback", "fallback_candidate_evaluations", 0, "requester_module"),
            TextLike("07-egress-routing"),
        ),
        (
            ("fallback", "fallback_candidate_evaluations", 0, "environment_id"),
            SimpleNamespace(value="env-01"),
        ),
        (("fallback", "fallback_candidate_evaluations", 0, "purpose"), " "),
        (
            ("fallback", "fallback_candidate_evaluations", 0, "policy_reference"),
            b"fallback-policy-01",
        ),
        (
            ("fallback", "fallback_candidate_evaluations", 0, "route_id"),
            TextLike("route-target-01"),
        ),
        (("fallback", "fallback_candidate_evaluations", 0, "agent_id"), b"agent-target-01"),
    ],
)
def test_exact_text_validation_rejects_non_exact_strings(
    path: tuple[str | int, ...],
    invalid_value: object,
) -> None:
    boundary = _base_boundary()
    _set_path(boundary, path, invalid_value)

    with pytest.raises(ValueError):
        _rebuild_boundary(boundary)


@pytest.mark.parametrize(
    ("path", "invalid_value"),
    [
        (("outcome_committed",), 0),
        (("outcome_committed",), 1),
        (("new_fallback_effect_authorized",), 0),
        (("transport_terminal",), 1),
        (("parser_success_inferred",), 0),
        (("scan_success_inferred",), 1),
        (("notification_delivery_inferred",), 0),
    ],
)
def test_exact_bool_validation_rejects_ints(
    path: tuple[str | int, ...],
    invalid_value: object,
) -> None:
    boundary = _base_boundary()
    _set_path(boundary, path, invalid_value)

    with pytest.raises(ValueError):
        _rebuild_boundary(boundary)


@pytest.mark.parametrize(
    ("path", "invalid_value"),
    [
        (("reason_codes",), ["policy-fallback-transport"]),
        (("reason_codes",), {"policy-fallback-transport"}),
        (("reason_codes",), iter(("policy-fallback-transport",))),
        (("reason_codes",), TupleLike(("policy-fallback-transport",))),
        (("reason_codes",), ("policy-fallback-transport", "")),
        (("evidence_reference_ids",), ["evidence-outcome-fallback-01"]),
        (("evidence_reference_ids",), {"evidence-outcome-fallback-01"}),
        (("evidence_reference_ids",), iter(("evidence-outcome-fallback-01",))),
        (("evidence_reference_ids",), TupleLike(("evidence-outcome-fallback-01",))),
        (("fallback", "capability_scope"), ["search"]),
        (("fallback", "capability_scope"), {"search"}),
        (("fallback", "capability_scope"), iter(("search",))),
        (("fallback", "capability_scope"), TupleLike(("search",))),
        (("fallback", "capability_scope"), ("search", "")),
        (("fallback", "decision", "reason_codes"), ["fallback-policy"]),
        (("fallback", "decision", "evidence_reference_ids"), {"evidence-fallback-01"}),
        (("fallback", "original_selection", "capability_scope"), ["search"]),
        (("fallback", "original_selection", "capability_scope"), TupleLike(("search",))),
        (("fallback", "fallback_candidate_evaluations"), []),
        (("fallback", "fallback_candidate_evaluations"), {1}),
        (("fallback", "fallback_candidate_evaluations"), iter(())),
    ],
)
def test_exact_tuple_validation_rejects_non_exact_tuples(
    path: tuple[str | int, ...],
    invalid_value: object,
) -> None:
    boundary = _base_boundary()
    _set_path(boundary, path, invalid_value)

    with pytest.raises(ValueError):
        _rebuild_boundary(boundary)


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("fallback", "decision", "to_route_id"), None),
        (("fallback", "decision", "bounded_attempt_reference"), None),
        (
            ("fallback", "fallback_candidate_evaluations", 0, "status"),
            RouteCandidateEligibilityStatus.RESTRICTED,
        ),
    ],
)
def test_status_specific_source_mutations_are_rejected(
    path: tuple[str | int, ...],
    value: object,
) -> None:
    boundary = _base_boundary()
    _set_path(boundary, path, value)

    with pytest.raises(ValueError):
        _rebuild_boundary(boundary)


def test_attempted_requires_exact_candidate_and_route_linkage() -> None:
    boundary = _base_boundary()
    assert boundary.fallback.decision.status is PolicyBasedFallbackStatus.ATTEMPTED
    assert (
        boundary.fallback.decision.to_route_id
        == boundary.fallback.fallback_candidate_evaluations[0].route_id
    )
    assert (
        boundary.fallback.fallback_candidate_evaluations[0].status
        is RouteCandidateEligibilityStatus.ELIGIBLE
    )


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("fallback", "decision", "to_route_id"), None),
        (("fallback", "decision", "bounded_attempt_reference"), None),
        (
            ("fallback", "fallback_candidate_evaluations", 0, "status"),
            RouteCandidateEligibilityStatus.RESTRICTED,
        ),
        (
            ("fallback", "fallback_candidate_evaluations", 1, "status"),
            RouteCandidateEligibilityStatus.ELIGIBLE,
        ),
        (("fallback", "decision", "to_route_id"), "route-target-02"),
    ],
)
def test_attempted_specific_source_mutations_are_rejected(
    path: tuple[str | int, ...],
    value: object,
) -> None:
    boundary = _base_boundary()
    _set_path(boundary, path, value)

    with pytest.raises(ValueError):
        _rebuild_boundary(boundary)


def test_exhausted_specific_source_mutations_are_rejected() -> None:
    boundary = _base_boundary(PolicyBasedFallbackStatus.EXHAUSTED)

    _set_path(boundary, ("fallback", "decision", "to_route_id"), "route-target-99")
    with pytest.raises(ValueError):
        _rebuild_boundary(boundary)

    boundary = _base_boundary(PolicyBasedFallbackStatus.EXHAUSTED)
    _set_path(boundary, ("fallback", "decision", "bounded_attempt_reference"), None)
    with pytest.raises(ValueError):
        _rebuild_boundary(boundary)

    boundary = _base_boundary(PolicyBasedFallbackStatus.EXHAUSTED)
    _set_path(
        boundary,
        ("fallback", "fallback_candidate_evaluations", 0, "status"),
        RouteCandidateEligibilityStatus.ELIGIBLE,
    )
    with pytest.raises(ValueError):
        _rebuild_boundary(boundary)

    boundary = _base_boundary(PolicyBasedFallbackStatus.EXHAUSTED)
    _set_path(boundary, ("fallback", "fallback_candidate_evaluations"), ())
    with pytest.raises(ValueError):
        _rebuild_boundary(boundary)


def test_no_approved_route_specific_source_mutations_are_rejected() -> None:
    boundary = _base_boundary(PolicyBasedFallbackStatus.NO_APPROVED_ROUTE)
    _set_path(boundary, ("fallback", "decision", "to_route_id"), "route-target-99")
    with pytest.raises(ValueError):
        _rebuild_boundary(boundary)

    boundary = _base_boundary(PolicyBasedFallbackStatus.NO_APPROVED_ROUTE)
    _set_path(boundary, ("fallback", "decision", "bounded_attempt_reference"), "bounded-attempt-99")
    with pytest.raises(ValueError):
        _rebuild_boundary(boundary)

    boundary = _base_boundary(PolicyBasedFallbackStatus.NO_APPROVED_ROUTE)
    _set_path(
        boundary,
        ("fallback", "fallback_candidate_evaluations", 0, "status"),
        RouteCandidateEligibilityStatus.ELIGIBLE,
    )
    with pytest.raises(ValueError):
        _rebuild_boundary(boundary)


@pytest.mark.parametrize(
    ("mutator", "expected_value"),
    [
        (("fallback", "request_reference"), "other-request"),
        (("fallback", "requester_module"), "other-module"),
        (("fallback", "environment_id"), "other-env"),
        (("fallback", "purpose"), "other-purpose"),
        (("fallback", "capability_scope"), ("other",)),
        (("fallback", "fallback_policy_reference"), "other-policy"),
        (("fallback", "original_failure_reference"), "other-failure"),
        (("fallback", "decision", "request_reference"), "other-request"),
        (("fallback", "decision", "policy_reference"), "other-policy"),
        (("fallback", "decision", "from_route_id"), "other-route"),
        (("fallback", "decision", "original_failure_reference"), "other-failure"),
        (("fallback", "original_selection", "request_reference"), "other-request"),
        (("fallback", "original_selection", "requester_module"), "other-module"),
        (("fallback", "original_selection", "environment_id"), "other-env"),
        (("fallback", "original_selection", "purpose"), "other-purpose"),
        (("fallback", "original_selection", "capability_scope"), ("other",)),
        (("fallback", "fallback_candidate_evaluations", 0, "request_reference"), "other-request"),
        (("fallback", "fallback_candidate_evaluations", 0, "requester_module"), "other-module"),
        (("fallback", "fallback_candidate_evaluations", 0, "environment_id"), "other-env"),
        (("fallback", "fallback_candidate_evaluations", 0, "purpose"), "other-purpose"),
        (("fallback", "fallback_candidate_evaluations", 0, "capability_scope"), ("other",)),
        (("fallback", "fallback_candidate_evaluations", 0, "policy_reference"), "other-policy"),
    ],
)
def test_linkage_mutations_are_rejected(mutator: tuple[str, ...], expected_value: object) -> None:
    boundary = _base_boundary()
    _set_path(boundary, tuple(mutator), expected_value)

    with pytest.raises(ValueError):
        _rebuild_boundary(boundary)


def test_duplicate_candidate_identifiers_are_rejected() -> None:
    boundary = _base_boundary()
    second_candidate = boundary.fallback.fallback_candidate_evaluations[1]
    object.__setattr__(
        second_candidate,
        "evaluation_id",
        boundary.fallback.fallback_candidate_evaluations[0].evaluation_id,
    )

    with pytest.raises(ValueError):
        _rebuild_boundary(boundary)

    boundary = _base_boundary()
    second_candidate = boundary.fallback.fallback_candidate_evaluations[1]
    object.__setattr__(
        second_candidate, "route_id", boundary.fallback.fallback_candidate_evaluations[0].route_id
    )

    with pytest.raises(ValueError):
        _rebuild_boundary(boundary)


def test_no_forbidden_semantics_are_exposed() -> None:
    boundary_fields = {field.name for field in fields(PolicyFallbackTransportOutcomeBoundary)}
    fallback_fields = {field.name for field in fields(PolicyBasedFallbackBoundary)}
    decision_fields = {field.name for field in fields(PolicyBasedFallbackDecision)}
    selection_fields = {field.name for field in fields(ServerRouteSelectionBoundary)}
    selection_decision_fields = {field.name for field in fields(RouteSelectionDecision)}
    banned = {
        "assignment",
        "dispatch",
        "response",
        "parser",
        "scan",
        "notification",
        "listing",
        "baseline",
        "anchor",
        "pending_recovery",
        "retry",
        "replay",
        "backoff",
        "content",
        "network",
        "runtime",
        "storage",
        "captcha_solver",
        "captcha_bypass",
        "provider",
        "proxy",
        "vpn",
        "tunnel",
        "browser",
        "windows",
        "route_health",
        "health",
        "quarantine",
    }
    assert banned.isdisjoint(boundary_fields)
    assert banned.isdisjoint(fallback_fields)
    assert banned.isdisjoint(decision_fields)
    assert banned.isdisjoint(selection_fields)
    assert banned.isdisjoint(selection_decision_fields)


def test_prior_state_regression_remains_unchanged() -> None:
    from tests.contract import test_egress_routing_fallback_contracts as fallback_contracts
    from tests.contract import (
        test_egress_routing_outcome_availability_contracts as outcome_availability_contracts,
    )
    from tests.contract import test_egress_routing_outcome_contracts as outcome_contracts
    from tests.contract import (
        test_egress_routing_outcome_response_contracts as outcome_response_contracts,
    )
    from tests.contract import (
        test_egress_routing_outcome_response_failure_contracts as response_failure_contracts,
    )
    from tests.contract import test_egress_routing_selection_contracts as selection_contracts

    assert (
        selection_contracts.EXPECTED_TASK_ID
        == "ER-05A-SERVER-ROUTE-SELECTION-BOUNDARY-20260712-007"
    )
    assert (
        fallback_contracts.EXPECTED_TASK_ID == "ER-05B-POLICY-BASED-FALLBACK-BOUNDARY-20260713-008"
    )
    assert (
        outcome_contracts.EXPECTED_TASK_ID
        == "ER-07A-TRANSPORT-OUTCOME-COMMITMENT-BOUNDARY-20260715-016"
    )
    assert (
        outcome_availability_contracts.EXPECTED_TASK_ID
        == "ER-07B-TRANSPORT-AVAILABILITY-OUTCOME-BOUNDARY-20260715-017"
    )
    assert (
        outcome_response_contracts.EXPECTED_TASK_ID
        == "ER-07C-TRANSPORT-RESPONSE-PRESENCE-OUTCOME-BOUNDARY-20260715-019"
    )
    assert (
        response_failure_contracts.EXPECTED_TASK_ID
        == "ER-07D-TRANSPORT-RESPONSE-FAILURE-OUTCOME-BOUNDARY-20260715-021"
    )
    assert len(egress_routing.EGRESS_SYNTHETIC_FIXTURE_IDS) == 34
    assert (
        tuple(egress_routing.EGRESS_SYNTHETIC_FIXTURE_IDS)
        == egress_routing.EGRESS_SYNTHETIC_FIXTURE_IDS
    )
