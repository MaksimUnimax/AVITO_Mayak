from __future__ import annotations

from dataclasses import replace

import pytest

from mayak.modules.egress_routing import (
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


def _mutate(record: object, **changes: object) -> None:
    for field_name, value in changes.items():
        object.__setattr__(record, field_name, value)


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


def _base_boundary() -> PolicyBasedFallbackBoundary:
    candidate = _candidate(
        route_id="route-target-01",
        agent_id="agent-target-01",
        policy_reference="fallback-policy-01",
        status=RouteCandidateEligibilityStatus.ELIGIBLE,
    )
    decision = _fallback_decision(
        PolicyBasedFallbackStatus.ALLOWED,
        policy_reference="fallback-policy-01",
        from_route_id="route-source-01",
        to_route_id="route-target-01",
        bounded_attempt_reference="bounded-attempt-01",
        original_failure_reference="failure-01",
        reconciliation_status=RouteReconciliationStatus.RESOLVED_SENT,
    )
    return _boundary((candidate,), decision, fallback_policy_reference="fallback-policy-01")


def _candidate_statuses(
    boundary: PolicyBasedFallbackBoundary,
) -> tuple[RouteCandidateEligibilityStatus, ...]:
    return tuple(candidate.status for candidate in boundary.fallback_candidate_evaluations)


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

    assert boundary.authority is RouteSelectionAuthority.EGRESS_ROUTING_SERVER
    assert boundary.request_reference == "request-01"
    assert boundary.requester_module == "07-egress-routing"
    assert boundary.environment_id == "env-01"
    assert boundary.purpose == "search"
    assert boundary.capability_scope == ("search",)
    assert boundary.fallback_policy_reference == fallback_policy_reference
    assert boundary.original_selection.decision.status is RouteSelectionStatus.SELECTED
    assert boundary.original_selection.decision.selected_route_id == "route-source-01"
    assert boundary.original_failure_reference == "failure-01"
    assert boundary.decision.status is status
    assert boundary.decision.from_route_id == "route-source-01"
    assert boundary.decision.to_route_id == expected_to_route_id
    assert boundary.decision.bounded_attempt_reference == expected_bounded_attempt_reference
    assert (
        _candidate_statuses(boundary).count(RouteCandidateEligibilityStatus.ELIGIBLE)
        == expected_eligible_count
    )
    assert tuple(candidate.route_id for candidate in boundary.fallback_candidate_evaluations) == (
        expected_candidate_route_ids
    )


def test_fallback_rejects_authority_and_selection_linkage() -> None:
    boundary = _base_boundary()

    with pytest.raises(ValueError):
        replace(boundary, authority=object())  # type: ignore[arg-type]

    mutated_selection = _original_selection()
    _mutate(mutated_selection.decision, status=RouteSelectionStatus.NO_ELIGIBLE_ROUTE)
    with pytest.raises(ValueError):
        replace(boundary, original_selection=mutated_selection)

    mutated_selection = _original_selection()
    _mutate(mutated_selection.decision, selected_route_id=None)
    with pytest.raises(ValueError):
        replace(boundary, original_selection=mutated_selection)

    with pytest.raises(ValueError):
        replace(boundary, request_reference="request-02")

    with pytest.raises(ValueError):
        replace(boundary, requester_module="05-avito-parser-adapter")

    with pytest.raises(ValueError):
        replace(boundary, environment_id="env-02")

    with pytest.raises(ValueError):
        replace(boundary, purpose="dispatch")

    with pytest.raises(ValueError):
        replace(boundary, capability_scope=("dispatch",))


def test_fallback_rejects_decision_and_candidate_context() -> None:
    boundary = _base_boundary()

    with pytest.raises(ValueError):
        replace(boundary, decision=replace(boundary.decision, request_reference="request-02"))

    with pytest.raises(ValueError):
        replace(
            boundary,
            decision=replace(boundary.decision, original_failure_reference="failure-02"),
        )

    with pytest.raises(ValueError):
        replace(boundary, decision=replace(boundary.decision, from_route_id="route-source-02"))

    with pytest.raises(ValueError):
        replace(
            boundary,
            fallback_policy_reference="fallback-policy-02",
            decision=replace(boundary.decision, policy_reference="fallback-policy-02"),
        )

    with pytest.raises(ValueError):
        replace(boundary, decision=replace(boundary.decision, reason_codes=()))

    with pytest.raises(ValueError):
        replace(boundary, decision=replace(boundary.decision, evidence_reference_ids=()))

    candidate = _candidate(
        route_id="route-target-99",
        agent_id="agent-target-99",
        policy_reference="fallback-policy-01",
        status=RouteCandidateEligibilityStatus.ELIGIBLE,
    )
    _mutate(candidate, request_reference="request-02")
    with pytest.raises(ValueError):
        _boundary(
            (candidate,),
            _fallback_decision(
                PolicyBasedFallbackStatus.ALLOWED,
                policy_reference="fallback-policy-01",
                from_route_id="route-source-01",
                to_route_id="route-target-99",
                bounded_attempt_reference="bounded-attempt-01",
                original_failure_reference="failure-01",
                reconciliation_status=RouteReconciliationStatus.RESOLVED_SENT,
            ),
            fallback_policy_reference="fallback-policy-01",
        )


def test_fallback_rejects_duplicate_candidates_and_source_route() -> None:
    boundary = _base_boundary()
    first_candidate = _candidate(
        route_id="route-target-01",
        agent_id="agent-target-01",
        policy_reference="fallback-policy-01",
        status=RouteCandidateEligibilityStatus.ELIGIBLE,
    )
    second_candidate = _candidate(
        route_id="route-target-02",
        agent_id="agent-target-02",
        policy_reference="fallback-policy-01",
        status=RouteCandidateEligibilityStatus.POLICY_REJECTED,
        reason_codes=("policy-rejected",),
    )

    duplicate_evaluation_id = replace(second_candidate, evaluation_id=first_candidate.evaluation_id)
    with pytest.raises(ValueError):
        replace(
            boundary,
            fallback_candidate_evaluations=(first_candidate, duplicate_evaluation_id),
        )

    duplicate_route_id = _candidate(
        route_id=first_candidate.route_id,
        agent_id="agent-target-02",
        policy_reference="fallback-policy-01",
        status=RouteCandidateEligibilityStatus.POLICY_REJECTED,
        reason_codes=("policy-rejected",),
    )
    _mutate(duplicate_route_id, evaluation_id="route-target-02-evaluation")
    with pytest.raises(ValueError):
        replace(boundary, fallback_candidate_evaluations=(first_candidate, duplicate_route_id))

    candidate_same_as_from_route = _candidate(
        route_id="route-source-01",
        agent_id="agent-source-03",
        policy_reference="fallback-policy-01",
        status=RouteCandidateEligibilityStatus.POLICY_REJECTED,
        reason_codes=("policy-rejected",),
    )
    with pytest.raises(ValueError):
        _boundary(
            (candidate_same_as_from_route,),
            _fallback_decision(
                PolicyBasedFallbackStatus.ALLOWED,
                policy_reference="fallback-policy-01",
                from_route_id="route-source-01",
                to_route_id="route-target-01",
                bounded_attempt_reference="bounded-attempt-01",
                original_failure_reference="failure-01",
                reconciliation_status=RouteReconciliationStatus.RESOLVED_SENT,
            ),
            fallback_policy_reference="fallback-policy-01",
        )


def test_fallback_rejects_automatic_first_candidate_and_route_family() -> None:
    first_candidate = _candidate(
        route_id="route-target-01",
        agent_id="agent-target-01",
        policy_reference="fallback-policy-01",
        status=RouteCandidateEligibilityStatus.POLICY_REJECTED,
        reason_codes=("policy-rejected",),
    )
    eligible_candidate = _candidate(
        route_id="route-target-02",
        agent_id="agent-target-02",
        policy_reference="fallback-policy-01",
        route_family=RouteFamily.BROWSER_EXTENSION_ROUTE,
        status=RouteCandidateEligibilityStatus.ELIGIBLE,
    )
    with pytest.raises(ValueError):
        _boundary(
            (first_candidate, eligible_candidate),
            _fallback_decision(
                PolicyBasedFallbackStatus.ALLOWED,
                policy_reference="fallback-policy-01",
                from_route_id="route-source-01",
                to_route_id="route-target-01",
                bounded_attempt_reference="bounded-attempt-01",
                original_failure_reference="failure-01",
                reconciliation_status=RouteReconciliationStatus.RESOLVED_SENT,
            ),
            fallback_policy_reference="fallback-policy-01",
        )

    family_candidate = _candidate(
        route_id="route-target-03",
        agent_id="agent-target-03",
        policy_reference="fallback-policy-01",
        route_family=RouteFamily.BROWSER_EXTENSION_ROUTE,
        status=RouteCandidateEligibilityStatus.POLICY_REJECTED,
        reason_codes=("policy-rejected",),
    )
    linux_eligible_candidate = _candidate(
        route_id="route-target-04",
        agent_id="agent-target-04",
        policy_reference="fallback-policy-01",
        route_family=RouteFamily.LINUX_REFERENCE_STYLE_ROUTE,
        status=RouteCandidateEligibilityStatus.ELIGIBLE,
    )
    with pytest.raises(ValueError):
        _boundary(
            (family_candidate, linux_eligible_candidate),
            _fallback_decision(
                PolicyBasedFallbackStatus.ALLOWED,
                policy_reference="fallback-policy-01",
                from_route_id="route-source-01",
                to_route_id="route-target-03",
                bounded_attempt_reference="bounded-attempt-01",
                original_failure_reference="failure-01",
                reconciliation_status=RouteReconciliationStatus.RESOLVED_SENT,
            ),
            fallback_policy_reference="fallback-policy-01",
        )


def test_policy_based_fallback_boundary_rejects_status_and_reconciliation_mismatches() -> None:
    with pytest.raises(ValueError):
        _boundary(
            (),
            _fallback_decision(
                PolicyBasedFallbackStatus.NOT_EVALUATED,
                policy_reference="fallback-policy-01",
                from_route_id="route-source-01",
                to_route_id=None,
                bounded_attempt_reference=None,
                original_failure_reference="failure-01",
                reconciliation_status=RouteReconciliationStatus.NOT_REQUIRED,
            ),
            fallback_policy_reference="fallback-policy-01",
        )

    with pytest.raises(ValueError):
        _boundary(
            (
                _candidate(
                    route_id="route-target-01",
                    agent_id="agent-target-01",
                    policy_reference="fallback-policy-01",
                    status=RouteCandidateEligibilityStatus.POLICY_REJECTED,
                    reason_codes=("policy-rejected",),
                ),
            ),
            _fallback_decision(
                PolicyBasedFallbackStatus.NOT_ALLOWED,
                policy_reference="fallback-policy-01",
                from_route_id="route-source-01",
                to_route_id="route-target-01",
                bounded_attempt_reference=None,
                original_failure_reference="failure-01",
                reconciliation_status=RouteReconciliationStatus.NOT_REQUIRED,
            ),
            fallback_policy_reference="fallback-policy-01",
        )

    with pytest.raises(ValueError):
        _boundary(
            (
                _candidate(
                    route_id="route-target-01",
                    agent_id="agent-target-01",
                    policy_reference="fallback-policy-01",
                    status=RouteCandidateEligibilityStatus.POLICY_REJECTED,
                    reason_codes=("policy-rejected",),
                ),
            ),
            _fallback_decision(
                PolicyBasedFallbackStatus.ALLOWED,
                policy_reference="fallback-policy-01",
                from_route_id="route-source-01",
                to_route_id="route-target-01",
                bounded_attempt_reference="bounded-attempt-01",
                original_failure_reference="failure-01",
                reconciliation_status=RouteReconciliationStatus.RESOLVED_SENT,
            ),
            fallback_policy_reference="fallback-policy-01",
        )

    attempted_boundary = _base_boundary()
    _mutate(attempted_boundary.decision, status=PolicyBasedFallbackStatus.ATTEMPTED)
    _mutate(attempted_boundary.decision, reconciliation_status=RouteReconciliationStatus.REQUIRED)
    with pytest.raises(ValueError):
        _boundary(
            attempted_boundary.fallback_candidate_evaluations,
            attempted_boundary.decision,
            fallback_policy_reference="fallback-policy-01",
        )

    with pytest.raises(ValueError):
        _boundary(
            (
                _candidate(
                    route_id="route-target-01",
                    agent_id="agent-target-01",
                    policy_reference="fallback-policy-01",
                    status=RouteCandidateEligibilityStatus.ELIGIBLE,
                ),
            ),
            _fallback_decision(
                PolicyBasedFallbackStatus.EXHAUSTED,
                policy_reference="fallback-policy-01",
                from_route_id="route-source-01",
                to_route_id=None,
                bounded_attempt_reference="bounded-attempt-01",
                original_failure_reference="failure-01",
                reconciliation_status=RouteReconciliationStatus.RESOLVED_SENT,
            ),
            fallback_policy_reference="fallback-policy-01",
        )

    with pytest.raises(ValueError):
        _boundary(
            (
                _candidate(
                    route_id="route-target-01",
                    agent_id="agent-target-01",
                    policy_reference="fallback-policy-01",
                    status=RouteCandidateEligibilityStatus.POLICY_REJECTED,
                    reason_codes=("policy-rejected",),
                ),
            ),
            _fallback_decision(
                PolicyBasedFallbackStatus.EXHAUSTED,
                policy_reference="fallback-policy-01",
                from_route_id="route-source-01",
                to_route_id=None,
                bounded_attempt_reference=None,
                original_failure_reference="failure-01",
                reconciliation_status=RouteReconciliationStatus.RESOLVED_SENT,
            ),
            fallback_policy_reference="fallback-policy-01",
        )

    with pytest.raises(ValueError):
        _boundary(
            (),
            _fallback_decision(
                PolicyBasedFallbackStatus.BLOCKED_RECONCILIATION_REQUIRED,
                policy_reference="fallback-policy-01",
                from_route_id="route-source-01",
                to_route_id=None,
                bounded_attempt_reference=None,
                original_failure_reference="failure-01",
                reconciliation_status=RouteReconciliationStatus.RESOLVED_SENT,
            ),
            fallback_policy_reference="fallback-policy-01",
        )

    with pytest.raises(ValueError):
        _boundary(
            (
                _candidate(
                    route_id="route-target-01",
                    agent_id="agent-target-01",
                    policy_reference="fallback-policy-01",
                    status=RouteCandidateEligibilityStatus.ELIGIBLE,
                ),
            ),
            _fallback_decision(
                PolicyBasedFallbackStatus.NO_APPROVED_ROUTE,
                policy_reference="fallback-policy-01",
                from_route_id="route-source-01",
                to_route_id=None,
                bounded_attempt_reference=None,
                original_failure_reference="failure-01",
                reconciliation_status=RouteReconciliationStatus.RESOLVED_NOT_SENT,
            ),
            fallback_policy_reference="fallback-policy-01",
        )


def test_policy_based_fallback_boundary_rejects_non_blank_and_tuple_semantics() -> None:
    boundary = _base_boundary()

    with pytest.raises(ValueError):
        replace(boundary, boundary_id=" ")

    with pytest.raises(ValueError):
        replace(boundary, purpose=" ")

    with pytest.raises(ValueError):
        replace(boundary, capability_scope=())

    with pytest.raises(ValueError):
        replace(boundary, fallback_candidate_evaluations=[])  # type: ignore[arg-type]

    with pytest.raises(ValueError):
        replace(boundary, decision=replace(boundary.decision, reason_codes=(" ",)))

    with pytest.raises(ValueError):
        replace(boundary, decision=replace(boundary.decision, evidence_reference_ids=(" ",)))

    with pytest.raises(ValueError):
        replace(boundary, decision=replace(boundary.decision, policy_reference=None))


def test_policy_based_fallback_boundary_rejects_policy_and_candidate_role_confusion() -> None:
    boundary = _base_boundary()
    invalid_candidate = _candidate(
        route_id="route-target-99",
        agent_id="agent-target-99",
        policy_reference="fallback-policy-01",
        status=RouteCandidateEligibilityStatus.POLICY_REJECTED,
        reason_codes=("policy-rejected",),
    )
    _mutate(invalid_candidate, policy_reference="other-policy-01")
    with pytest.raises(ValueError):
        _boundary(
            (invalid_candidate,),
            _fallback_decision(
                PolicyBasedFallbackStatus.NOT_ALLOWED,
                policy_reference="fallback-policy-01",
                from_route_id="route-source-01",
                to_route_id=None,
                bounded_attempt_reference=None,
                original_failure_reference="failure-01",
                reconciliation_status=RouteReconciliationStatus.NOT_REQUIRED,
            ),
            fallback_policy_reference="fallback-policy-01",
        )

    invalid_decision = replace(boundary.decision, to_route_id="route-target-01")
    _mutate(invalid_decision, to_route_id="route-source-01")
    with pytest.raises(ValueError):
        _boundary(
            boundary.fallback_candidate_evaluations,
            invalid_decision,
            fallback_policy_reference="fallback-policy-01",
        )
