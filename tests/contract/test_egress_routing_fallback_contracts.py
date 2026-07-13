from __future__ import annotations

from dataclasses import fields, is_dataclass
from pathlib import Path
from typing import Any, cast

import pytest

import mayak.modules.egress_routing.fallback as fallback_module
from mayak.modules import egress_routing
from mayak.modules.egress_routing import (
    ER02_TASK_ID,
    ER03_TASK_ID,
    ER05A_TASK_ID,
    ER05B_TASK_ID,
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
)

EXPECTED_TASK_ID = "".join(("ER-05B-", "POLICY-BASED-FALLBACK-BOUNDARY-", "20260713-008"))

EXPECTED_MODULE_EXPORTS = (
    "ER05B_TASK_ID",
    "PolicyBasedFallbackBoundary",
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
    "ER02_TASK_ID",
    "EGRESS_SYNTHETIC_FIXTURE_IDS",
    "EGRESS_SYNTHETIC_FIXTURES",
    "EgressSyntheticFixture",
)

EXPECTED_FIELD_NAMES = {
    PolicyBasedFallbackBoundary: (
        "boundary_id",
        "authority",
        "request_reference",
        "requester_module",
        "environment_id",
        "purpose",
        "capability_scope",
        "fallback_policy_reference",
        "original_selection",
        "original_failure_reference",
        "fallback_candidate_evaluations",
        "decision",
    ),
}


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


def _selection_decision(
    selected_route_id: str,
    candidate_route_ids: tuple[str, ...],
    *,
    policy_reference: str = "selection-policy-01",
) -> RouteSelectionDecision:
    rejected_route_ids = tuple(
        route_id for route_id in candidate_route_ids if route_id != selected_route_id
    )
    return RouteSelectionDecision(
        decision_id="selection-decision-01",
        request_reference="request-01",
        status=RouteSelectionStatus.SELECTED,
        selected_route_id=selected_route_id,
        candidate_route_ids=candidate_route_ids,
        rejected_route_ids=rejected_route_ids,
        reason_codes=("selected",),
        evidence_reference_ids=("evidence-selection-01",),
        policy_reference=policy_reference,
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
        decision=_selection_decision("route-source-01", ("route-source-01", "route-source-02")),
    )


def _fallback_decision(
    status: PolicyBasedFallbackStatus,
    *,
    policy_reference: str | None,
    from_route_id: str,
    to_route_id: str | None,
    bounded_attempt_reference: str | None,
    original_failure_reference: str,
    reconciliation_status: RouteReconciliationStatus,
    reason_codes: tuple[str, ...] = ("fallback-policy",),
    evidence_reference_ids: tuple[str, ...] = ("evidence-fallback-01",),
) -> PolicyBasedFallbackDecision:
    return PolicyBasedFallbackDecision(
        decision_id="fallback-decision-01",
        request_reference="request-01",
        status=status,
        policy_reference=policy_reference,
        from_route_id=from_route_id,
        to_route_id=to_route_id,
        reason_codes=reason_codes,
        evidence_reference_ids=evidence_reference_ids,
        bounded_attempt_reference=bounded_attempt_reference,
        original_failure_reference=original_failure_reference,
        reconciliation_status=reconciliation_status,
    )


def _boundary(
    candidates: tuple[RouteCandidateEvaluation, ...],
    decision: PolicyBasedFallbackDecision,
    *,
    fallback_policy_reference: str | None,
    original_selection: ServerRouteSelectionBoundary | None = None,
    request_reference: str = "request-01",
    requester_module: str = "07-egress-routing",
    environment_id: str = "env-01",
    purpose: str = "search",
    capability_scope: tuple[str, ...] = ("search",),
    original_failure_reference: str = "failure-01",
    authority: RouteSelectionAuthority = RouteSelectionAuthority.EGRESS_ROUTING_SERVER,
) -> PolicyBasedFallbackBoundary:
    return PolicyBasedFallbackBoundary(
        boundary_id="fallback-boundary-01",
        authority=authority,
        request_reference=request_reference,
        requester_module=requester_module,
        environment_id=environment_id,
        purpose=purpose,
        capability_scope=capability_scope,
        fallback_policy_reference=fallback_policy_reference,
        original_selection=original_selection or _original_selection(),
        original_failure_reference=original_failure_reference,
        fallback_candidate_evaluations=candidates,
        decision=decision,
    )


def _assert_common_boundary_state(
    boundary: PolicyBasedFallbackBoundary,
    *,
    fallback_policy_reference: str | None,
    expected_status: PolicyBasedFallbackStatus,
    expected_to_route_id: str | None,
    expected_bounded_attempt_reference: str | None,
    expected_candidate_route_ids: tuple[str, ...],
    expected_eligible_count: int,
) -> None:
    assert boundary.authority is RouteSelectionAuthority.EGRESS_ROUTING_SERVER
    assert boundary.request_reference == "request-01"
    assert boundary.requester_module == "07-egress-routing"
    assert boundary.environment_id == "env-01"
    assert boundary.purpose == "search"
    assert boundary.capability_scope == ("search",)
    assert boundary.fallback_policy_reference == fallback_policy_reference
    assert boundary.original_selection.authority is RouteSelectionAuthority.EGRESS_ROUTING_SERVER
    assert boundary.original_selection.decision.status is RouteSelectionStatus.SELECTED
    assert boundary.original_selection.decision.selected_route_id == "route-source-01"
    assert boundary.original_selection.request_reference == boundary.request_reference
    assert boundary.original_selection.requester_module == boundary.requester_module
    assert boundary.original_selection.environment_id == boundary.environment_id
    assert boundary.original_selection.purpose == boundary.purpose
    assert boundary.original_selection.capability_scope == boundary.capability_scope
    assert boundary.original_failure_reference == "failure-01"
    assert boundary.decision.request_reference == boundary.request_reference
    assert boundary.decision.original_failure_reference == boundary.original_failure_reference
    assert boundary.decision.from_route_id == boundary.original_selection.decision.selected_route_id
    assert boundary.decision.policy_reference == fallback_policy_reference
    assert boundary.decision.status is expected_status
    assert boundary.decision.to_route_id == expected_to_route_id
    assert boundary.decision.bounded_attempt_reference == expected_bounded_attempt_reference
    assert boundary.decision.reason_codes == ("fallback-policy",)
    assert boundary.decision.evidence_reference_ids == ("evidence-fallback-01",)
    assert tuple(candidate.route_id for candidate in boundary.fallback_candidate_evaluations) == (
        expected_candidate_route_ids
    )
    assert (
        sum(
            candidate.status is RouteCandidateEligibilityStatus.ELIGIBLE
            for candidate in boundary.fallback_candidate_evaluations
        )
        == expected_eligible_count
    )
    assert all(
        candidate.request_reference == boundary.request_reference
        and candidate.requester_module == boundary.requester_module
        and candidate.environment_id == boundary.environment_id
        and candidate.purpose == boundary.purpose
        and candidate.capability_scope == boundary.capability_scope
        for candidate in boundary.fallback_candidate_evaluations
    )


def test_fallback_module_public_surface_is_exact() -> None:
    assert fallback_module.ER05B_TASK_ID == EXPECTED_TASK_ID
    assert fallback_module.PolicyBasedFallbackBoundary is PolicyBasedFallbackBoundary
    assert type(fallback_module.__all__) is tuple
    assert fallback_module.__all__ == EXPECTED_MODULE_EXPORTS
    assert tuple(fallback_module.__all__) == EXPECTED_MODULE_EXPORTS
    assert len(fallback_module.__all__) == len(EXPECTED_MODULE_EXPORTS)
    assert len(set(fallback_module.__all__)) == len(EXPECTED_MODULE_EXPORTS)
    assert all(hasattr(fallback_module, name) for name in EXPECTED_MODULE_EXPORTS)


def test_package_public_surface_is_exact() -> None:
    assert egress_routing.MODULE_ID == "07-egress-routing"
    assert type(egress_routing.__all__) is tuple
    assert egress_routing.__all__ == EXPECTED_PACKAGE_EXPORTS
    assert tuple(egress_routing.__all__) == EXPECTED_PACKAGE_EXPORTS
    assert len(egress_routing.__all__) == len(EXPECTED_PACKAGE_EXPORTS)
    assert len(set(egress_routing.__all__)) == len(EXPECTED_PACKAGE_EXPORTS)
    assert all(hasattr(egress_routing, name) for name in EXPECTED_PACKAGE_EXPORTS)


def test_fallback_boundary_is_frozen_and_slotted_dataclass_with_exact_fields() -> None:
    assert is_dataclass(PolicyBasedFallbackBoundary)
    assert cast(Any, PolicyBasedFallbackBoundary).__dataclass_params__.frozen is True
    assert (
        tuple(field.name for field in fields(PolicyBasedFallbackBoundary))
        == (EXPECTED_FIELD_NAMES[PolicyBasedFallbackBoundary])
    )
    assert tuple(field.name for field in fields(PolicyBasedFallbackBoundary)) == (
        PolicyBasedFallbackBoundary.__slots__
    )


@pytest.mark.parametrize(
    (
        "status, expected_to_route_id, expected_bounded_attempt_reference, "
        "expected_candidate_route_ids, expected_eligible_count, "
        "fallback_policy_reference, reconciliation_status, candidates"
    ),
    [
        (
            PolicyBasedFallbackStatus.NOT_EVALUATED,
            None,
            None,
            (),
            0,
            None,
            RouteReconciliationStatus.NOT_REQUIRED,
            (),
        ),
        (
            PolicyBasedFallbackStatus.NOT_ALLOWED,
            None,
            None,
            ("route-target-01",),
            0,
            "fallback-policy-01",
            RouteReconciliationStatus.NOT_REQUIRED,
            (
                _candidate(
                    route_id="route-target-01",
                    agent_id="agent-target-01",
                    policy_reference="fallback-policy-01",
                    status=RouteCandidateEligibilityStatus.POLICY_REJECTED,
                    reason_codes=("policy-rejected",),
                ),
            ),
        ),
        (
            PolicyBasedFallbackStatus.ALLOWED,
            "route-target-01",
            "bounded-attempt-01",
            ("route-target-01",),
            1,
            "fallback-policy-01",
            RouteReconciliationStatus.RESOLVED_SENT,
            (
                _candidate(
                    route_id="route-target-01",
                    agent_id="agent-target-01",
                    policy_reference="fallback-policy-01",
                    status=RouteCandidateEligibilityStatus.ELIGIBLE,
                ),
            ),
        ),
        (
            PolicyBasedFallbackStatus.ATTEMPTED,
            "route-target-01",
            "bounded-attempt-01",
            ("route-target-01",),
            1,
            "fallback-policy-01",
            RouteReconciliationStatus.RESOLVED_NOT_SENT,
            (
                _candidate(
                    route_id="route-target-01",
                    agent_id="agent-target-01",
                    policy_reference="fallback-policy-01",
                    status=RouteCandidateEligibilityStatus.ELIGIBLE,
                ),
            ),
        ),
        (
            PolicyBasedFallbackStatus.EXHAUSTED,
            None,
            "bounded-attempt-01",
            ("route-target-01", "route-target-02"),
            0,
            "fallback-policy-01",
            RouteReconciliationStatus.RESOLVED_TERMINAL,
            (
                _candidate(
                    route_id="route-target-01",
                    agent_id="agent-target-01",
                    policy_reference="fallback-policy-01",
                    status=RouteCandidateEligibilityStatus.POLICY_REJECTED,
                    reason_codes=("policy-rejected",),
                ),
                _candidate(
                    route_id="route-target-02",
                    agent_id="agent-target-02",
                    policy_reference="fallback-policy-01",
                    status=RouteCandidateEligibilityStatus.POLICY_REJECTED,
                    reason_codes=("policy-rejected",),
                ),
            ),
        ),
        (
            PolicyBasedFallbackStatus.BLOCKED_RECONCILIATION_REQUIRED,
            None,
            None,
            ("route-target-01",),
            1,
            "fallback-policy-01",
            RouteReconciliationStatus.REQUIRED,
            (
                _candidate(
                    route_id="route-target-01",
                    agent_id="agent-target-01",
                    policy_reference="fallback-policy-01",
                    status=RouteCandidateEligibilityStatus.ELIGIBLE,
                ),
            ),
        ),
        (
            PolicyBasedFallbackStatus.NO_APPROVED_ROUTE,
            None,
            None,
            ("route-target-01", "route-target-02"),
            0,
            "fallback-policy-01",
            RouteReconciliationStatus.RESOLVED_NOT_SENT,
            (
                _candidate(
                    route_id="route-target-01",
                    agent_id="agent-target-01",
                    policy_reference="fallback-policy-01",
                    status=RouteCandidateEligibilityStatus.POLICY_REJECTED,
                    reason_codes=("policy-rejected",),
                ),
                _candidate(
                    route_id="route-target-02",
                    agent_id="agent-target-02",
                    policy_reference="fallback-policy-01",
                    status=RouteCandidateEligibilityStatus.POLICY_REJECTED,
                    reason_codes=("policy-rejected",),
                ),
            ),
        ),
    ],
)
def test_policy_based_fallback_boundary_accepts_all_supported_statuses(
    status: PolicyBasedFallbackStatus,
    expected_to_route_id: str | None,
    expected_bounded_attempt_reference: str | None,
    expected_candidate_route_ids: tuple[str, ...],
    expected_eligible_count: int,
    fallback_policy_reference: str | None,
    reconciliation_status: RouteReconciliationStatus,
    candidates: tuple[RouteCandidateEvaluation, ...],
) -> None:
    boundary = _boundary(
        candidates,
        _fallback_decision(
            status,
            policy_reference=fallback_policy_reference,
            from_route_id="route-source-01",
            to_route_id=expected_to_route_id,
            bounded_attempt_reference=expected_bounded_attempt_reference,
            original_failure_reference="failure-01",
            reconciliation_status=reconciliation_status,
        ),
        fallback_policy_reference=fallback_policy_reference,
    )
    _assert_common_boundary_state(
        boundary,
        fallback_policy_reference=fallback_policy_reference,
        expected_status=status,
        expected_to_route_id=expected_to_route_id,
        expected_bounded_attempt_reference=expected_bounded_attempt_reference,
        expected_candidate_route_ids=expected_candidate_route_ids,
        expected_eligible_count=expected_eligible_count,
    )


def test_task_ids_remain_unique_in_source_files() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    source_files = (
        repo_root / "src/mayak/modules/egress_routing/fixtures.py",
        repo_root / "src/mayak/modules/egress_routing/registration.py",
        repo_root / "src/mayak/modules/egress_routing/selection.py",
        repo_root / "src/mayak/modules/egress_routing/fallback.py",
    )
    task_ids = (
        ER02_TASK_ID,
        ER03_TASK_ID,
        ER05A_TASK_ID,
        ER05B_TASK_ID,
    )
    counts = {
        task_id: sum(path.read_text().count(task_id) for path in source_files)
        for task_id in task_ids
    }
    assert counts == {
        ER02_TASK_ID: 1,
        ER03_TASK_ID: 1,
        ER05A_TASK_ID: 1,
        ER05B_TASK_ID: 1,
    }
