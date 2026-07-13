from __future__ import annotations

from dataclasses import fields
from typing import Any

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


def _candidate(
    route_id: str = "route-01",
    agent_id: str = "agent-01",
    *,
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
    purpose: str = "search",
    capability_scope: tuple[str, ...] = ("search",),
    reason_codes: tuple[str, ...] = (),
    evidence_reference_ids: tuple[str, ...] = ("evidence-candidate-01",),
) -> RouteCandidateEvaluation:
    agent = EgressAgent(
        agent_id=agent_id,
        agent_class="LinuxReferenceStyleAgent",
        environment_id="env-01",
        lifecycle_status=agent_lifecycle_status,
        trust_scope=("egress", "safe-routing"),
        source_release_reference="release-20260712",
        credential_reference="opaque-credential-ref",
        evidence_reference_ids=("evidence-agent-01",),
    )
    route = EgressRoute(
        route_id=route_id,
        route_family=route_family,
        environment_id="env-01",
        agent_id=agent_id,
        purpose_scope=("search", "dispatch"),
        capability_ids=("cap-01",),
        lifecycle_status=route_lifecycle_status,
        evidence_reference_ids=("evidence-route-01",),
    )
    agent_registration = AgentRegistration(
        registration_id=f"{agent_id}-registration",
        agent_id=agent_id,
        environment_id="env-01",
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
        environment_id="env-01",
        source_release_reference="release-20260712",
        route_family=route_family,
        purpose_scope=("search", "dispatch"),
        capability_ids=("cap-01",),
        unsupported_classes=(),
        evidence_status=RouteEvidenceStatus.CURRENT,
        session_policy_status=SessionPolicyStatus.APPROVED_REFERENCE_ONLY,
        restriction_reference=None,
        selection_policy_reference=None,
        privacy_boundary_reference="privacy-boundary-01",
        status=RouteRegistrationStatus.REGISTERED,
        reason_codes=(),
        evidence_reference_ids=("evidence-route-registration-01",),
    )
    association = AgentRouteAssociation(
        association_id=f"{route_id}-association",
        agent_id=agent_id,
        route_id=route_id,
        environment_id="env-01",
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
        request_reference="request-01",
        requester_module="07-egress-routing",
        environment_id="env-01",
        purpose=purpose,
        capability_scope=capability_scope,
        policy_reference="policy-01",
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


def _decision(
    status: RouteSelectionStatus,
    *,
    selected_route_id: str | None,
    candidate_route_ids: tuple[str, ...],
    rejected_route_ids: tuple[str, ...],
    reason_codes: tuple[str, ...] = ("selection-approved",),
    evidence_reference_ids: tuple[str, ...] = ("evidence-decision-01",),
) -> RouteSelectionDecision:
    return RouteSelectionDecision(
        decision_id="decision-01",
        request_reference="request-01",
        status=status,
        selected_route_id=selected_route_id,
        candidate_route_ids=candidate_route_ids,
        rejected_route_ids=rejected_route_ids,
        reason_codes=reason_codes,
        evidence_reference_ids=evidence_reference_ids,
        policy_reference="policy-01",
    )


def _boundary(
    candidates: tuple[RouteCandidateEvaluation, ...],
    decision: RouteSelectionDecision,
    *,
    request_reference: str = "request-01",
    requester_module: str = "07-egress-routing",
    environment_id: str = "env-01",
    purpose: str = "search",
    capability_scope: tuple[str, ...] = ("search",),
    policy_reference: str = "policy-01",
    authority: RouteSelectionAuthority = RouteSelectionAuthority.EGRESS_ROUTING_SERVER,
) -> ServerRouteSelectionBoundary:
    return ServerRouteSelectionBoundary(
        boundary_id="boundary-01",
        authority=authority,
        request_reference=request_reference,
        requester_module=requester_module,
        environment_id=environment_id,
        purpose=purpose,
        capability_scope=capability_scope,
        policy_reference=policy_reference,
        candidate_evaluations=candidates,
        decision=decision,
    )


def _field_names(record_cls: Any) -> tuple[str, ...]:
    return tuple(field.name for field in fields(record_cls))


def test_only_egress_routing_server_is_the_selection_authority() -> None:
    assert tuple(member.name for member in RouteSelectionAuthority) == ("EGRESS_ROUTING_SERVER",)
    assert RouteSelectionAuthority.EGRESS_ROUTING_SERVER.value == "EGRESS_ROUTING_SERVER"
    assert "PARSER" not in RouteSelectionAuthority.__members__
    assert "SCAN" not in RouteSelectionAuthority.__members__
    assert "AGENT" not in RouteSelectionAuthority.__members__
    assert "CLIENT_UI" not in RouteSelectionAuthority.__members__


@pytest.mark.parametrize(
    "route_lifecycle_status",
    (
        RouteLifecycleStatus.REGISTERED,
        RouteLifecycleStatus.QUARANTINED,
        RouteLifecycleStatus.RESTRICTED,
    ),
)
def test_registration_alone_and_non_ready_routes_are_not_selectable(
    route_lifecycle_status: RouteLifecycleStatus,
) -> None:
    candidate = _candidate(
        route_lifecycle_status=route_lifecycle_status,
        agent_lifecycle_status=AgentLifecycleStatus.ONLINE_UNREADY,
        status=RouteCandidateEligibilityStatus.READINESS_BLOCKED,
        reason_codes=("not-ready",),
    )
    assert candidate.status is RouteCandidateEligibilityStatus.READINESS_BLOCKED
    assert (
        candidate.registration_boundary.agent_registration.status
        is AgentRegistrationStatus.REGISTERED
    )
    assert (
        candidate.registration_boundary.route_registration.status
        is RouteRegistrationStatus.REGISTERED
    )


@pytest.mark.parametrize(
    "evidence_status",
    (
        RouteEvidenceStatus.STALE,
        RouteEvidenceStatus.MISSING,
        RouteEvidenceStatus.DISPUTED,
        RouteEvidenceStatus.UNPROVEN,
        RouteEvidenceStatus.WITHDRAWN,
    ),
)
def test_non_current_evidence_is_not_eligible(
    evidence_status: RouteEvidenceStatus,
) -> None:
    candidate = _candidate(
        capability_evidence_status=evidence_status,
        status=RouteCandidateEligibilityStatus.EVIDENCE_STALE,
        reason_codes=("evidence-stale",),
    )
    assert candidate.status is RouteCandidateEligibilityStatus.EVIDENCE_STALE
    assert candidate.capability.evidence_status is evidence_status


@pytest.mark.parametrize(
    "route_family",
    (
        RouteFamily.LINUX_REFERENCE_STYLE_ROUTE,
        RouteFamily.BROWSER_EXTENSION_ROUTE,
        RouteFamily.OWNER_DEVELOPMENT_BRIDGE_ROUTE,
        RouteFamily.WINDOWS_VM_BROWSER_WORKER_ROUTE,
        RouteFamily.RUSSIAN_RESIDENTIAL_ROUTE,
    ),
)
def test_route_family_labels_do_not_select_by_themselves(route_family: RouteFamily) -> None:
    candidate = _candidate(
        route_family=route_family,
        route_lifecycle_status=RouteLifecycleStatus.REGISTERED,
        agent_lifecycle_status=AgentLifecycleStatus.ONLINE_UNREADY,
        status=RouteCandidateEligibilityStatus.READINESS_BLOCKED,
        reason_codes=("not-ready",),
    )
    assert candidate.status is RouteCandidateEligibilityStatus.READINESS_BLOCKED
    assert candidate.registration_boundary.route.route_family is route_family


@pytest.mark.parametrize(
    ("status", "candidate_kwargs"),
    [
        (
            RouteCandidateEligibilityStatus.PURPOSE_MISMATCH,
            {"purpose": "other-purpose", "reason_codes": ("blocked",)},
        ),
        (
            RouteCandidateEligibilityStatus.CAPABILITY_MISMATCH,
            {"capability_scope": ("other",), "reason_codes": ("blocked",)},
        ),
        (
            RouteCandidateEligibilityStatus.HEALTH_BLOCKED,
            {"health_status": RouteHealthStatus.DEGRADED, "reason_codes": ("blocked",)},
        ),
        (
            RouteCandidateEligibilityStatus.RESTRICTED,
            {
                "restriction_status": RouteRestrictionStatus.RESTRICTED,
                "blocks_new_assignments": True,
                "reason_codes": ("blocked",),
            },
        ),
        (
            RouteCandidateEligibilityStatus.RECONCILIATION_BLOCKED,
            {
                "reconciliation_status": RouteReconciliationStatus.REQUIRED,
                "reason_codes": ("blocked",),
            },
        ),
    ],
)
def test_explicit_failure_statuses_remain_distinct(
    status: RouteCandidateEligibilityStatus,
    candidate_kwargs: dict[str, Any],
) -> None:
    candidate = _candidate(status=status, **candidate_kwargs)
    assert candidate.status is status


def test_policy_rejection_is_distinct_from_technical_failure() -> None:
    policy_rejected = _candidate(
        status=RouteCandidateEligibilityStatus.POLICY_REJECTED,
        reason_codes=("policy-blocked",),
    )
    assert policy_rejected.status is RouteCandidateEligibilityStatus.POLICY_REJECTED

    with pytest.raises(ValueError):
        _candidate(
            capability_evidence_status=RouteEvidenceStatus.STALE,
            status=RouteCandidateEligibilityStatus.POLICY_REJECTED,
            reason_codes=("policy-blocked",),
        )


def test_selected_route_is_unique_and_rejected_routes_stay_explicit() -> None:
    eligible = _candidate(route_id="route-01", agent_id="agent-01")
    policy_rejected = _candidate(
        route_id="route-02",
        agent_id="agent-02",
        status=RouteCandidateEligibilityStatus.POLICY_REJECTED,
        reason_codes=("policy-blocked",),
    )
    decision = _decision(
        RouteSelectionStatus.SELECTED,
        selected_route_id="route-01",
        candidate_route_ids=("route-01", "route-02"),
        rejected_route_ids=("route-02",),
    )
    boundary = _boundary((eligible, policy_rejected), decision)
    assert boundary.decision.selected_route_id == "route-01"
    assert boundary.decision.rejected_route_ids == ("route-02",)
    assert boundary.candidate_evaluations[0].status is RouteCandidateEligibilityStatus.ELIGIBLE
    assert (
        boundary.candidate_evaluations[1].status is RouteCandidateEligibilityStatus.POLICY_REJECTED
    )

    with pytest.raises(ValueError):
        _boundary(
            (
                _candidate(route_id="route-01", agent_id="agent-01"),
                _candidate(route_id="route-02", agent_id="agent-02"),
            ),
            _decision(
                RouteSelectionStatus.SELECTED,
                selected_route_id="route-01",
                candidate_route_ids=("route-01", "route-02"),
                rejected_route_ids=("route-02",),
            ),
        )


def test_no_eligible_route_is_explicit() -> None:
    candidate_a = _candidate(
        route_id="route-01",
        agent_id="agent-01",
        status=RouteCandidateEligibilityStatus.READINESS_BLOCKED,
        reason_codes=("readiness",),
        route_lifecycle_status=RouteLifecycleStatus.REGISTERED,
        agent_lifecycle_status=AgentLifecycleStatus.ONLINE_UNREADY,
    )
    candidate_b = _candidate(
        route_id="route-02",
        agent_id="agent-02",
        status=RouteCandidateEligibilityStatus.HEALTH_BLOCKED,
        reason_codes=("health",),
        health_status=RouteHealthStatus.DEGRADED,
    )
    boundary = _boundary(
        (candidate_a, candidate_b),
        _decision(
            RouteSelectionStatus.NO_ELIGIBLE_ROUTE,
            selected_route_id=None,
            candidate_route_ids=("route-01", "route-02"),
            rejected_route_ids=("route-01", "route-02"),
            reason_codes=("no-route",),
        ),
    )
    assert boundary.decision.status is RouteSelectionStatus.NO_ELIGIBLE_ROUTE
    assert boundary.decision.selected_route_id is None
    assert boundary.decision.rejected_route_ids == ("route-01", "route-02")

    with pytest.raises(ValueError):
        _boundary(
            (_candidate(route_id="route-01", agent_id="agent-01"),),
            _decision(
                RouteSelectionStatus.NO_ELIGIBLE_ROUTE,
                selected_route_id=None,
                candidate_route_ids=("route-01",),
                rejected_route_ids=("route-01",),
                reason_codes=("no-route",),
            ),
        )


def test_selection_does_not_create_lease_assignment_or_transport_attempt() -> None:
    field_names = {field.name for field in fields(RouteCandidateEvaluation)} | {
        field.name for field in fields(ServerRouteSelectionBoundary)
    }
    banned_tokens = {
        "lease_id",
        "assignment_id",
        "priority",
        "score",
        "weight",
        "round_robin",
        "fallback_order",
        "provider",
        "proxy",
        "vpn",
        "tunnel",
        "host",
        "hostname",
        "ip",
        "port",
    }
    assert field_names.isdisjoint(banned_tokens)


def test_selection_contains_no_parser_scan_agent_provider_runtime_fields() -> None:
    field_names = _field_names(RouteCandidateEvaluation) + _field_names(
        ServerRouteSelectionBoundary
    )
    forbidden_tokens = {
        "selected_by_parser",
        "selected_by_scan",
        "selected_by_agent",
        "protocol",
        "cookie",
        "session_value",
        "credential_value",
    }
    assert all(token not in field_names for token in forbidden_tokens)
