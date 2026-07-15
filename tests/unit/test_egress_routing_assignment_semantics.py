from __future__ import annotations

from dataclasses import fields
from pathlib import Path
from typing import Any

from mayak.modules.egress_routing import (
    ER06B_TASK_ID,
    AgentLifecycleStatus,
    AgentRegistration,
    AgentRegistrationStatus,
    AgentRouteAssociation,
    AgentRouteAssociationStatus,
    AgentRouteRegistrationBoundary,
    DispatchAttempt,
    EgressAgent,
    EgressRoute,
    RouteCandidateEligibilityStatus,
    RouteCandidateEvaluation,
    RouteCapability,
    RouteEvidenceStatus,
    RouteFamily,
    RouteHealthState,
    RouteHealthStatus,
    RouteLease,
    RouteLeaseAuthority,
    RouteLeaseAuthorizationBoundary,
    RouteLeaseStatus,
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
    TransportAssignment,
    TransportAssignmentAuthority,
    TransportAssignmentCommitmentBoundary,
    TransportAssignmentOutcome,
)


def _mutate(record: object, **changes: object) -> None:
    for field_name, value in changes.items():
        object.__setattr__(record, field_name, value)


def _build_valid_state(
    *,
    request_reference: str = "request-01",
    requester_module: str = "07-egress-routing",
    environment_id: str = "env-01",
    purpose: str = "search",
    capability_scope: tuple[str, ...] = ("search",),
) -> dict[str, Any]:
    agent_id = "agent-01"
    route_id = "route-01"
    policy_reference = "policy-01"

    agent = EgressAgent(
        agent_id=agent_id,
        agent_class="LinuxReferenceStyleAgent",
        environment_id=environment_id,
        lifecycle_status=AgentLifecycleStatus.READY,
        trust_scope=("egress", "safe-routing"),
        source_release_reference="release-20260712",
        credential_reference="opaque-credential-ref",
        evidence_reference_ids=("evidence-agent-01",),
    )
    route = EgressRoute(
        route_id=route_id,
        route_family=RouteFamily.LINUX_REFERENCE_STYLE_ROUTE,
        environment_id=environment_id,
        agent_id=agent_id,
        purpose_scope=("search", "dispatch"),
        capability_ids=("cap-01",),
        lifecycle_status=RouteLifecycleStatus.READY,
        evidence_reference_ids=("evidence-route-01",),
    )
    agent_registration = AgentRegistration(
        registration_id="agent-registration-01",
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
        registration_id="route-registration-01",
        route_id=route_id,
        agent_id=agent_id,
        agent_registration_id=agent_registration.registration_id,
        environment_id=environment_id,
        source_release_reference="release-20260712",
        route_family=RouteFamily.LINUX_REFERENCE_STYLE_ROUTE,
        purpose_scope=("search", "dispatch"),
        capability_ids=("cap-01",),
        unsupported_classes=(),
        evidence_status=RouteEvidenceStatus.CURRENT,
        session_policy_status=SessionPolicyStatus.APPROVED_REFERENCE_ONLY,
        restriction_reference=None,
        selection_policy_reference=policy_reference,
        privacy_boundary_reference="privacy-boundary-01",
        status=RouteRegistrationStatus.REGISTERED,
        reason_codes=(),
        evidence_reference_ids=("evidence-route-registration-01",),
    )
    association = AgentRouteAssociation(
        association_id="association-01",
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
    registration_boundary = AgentRouteRegistrationBoundary(
        boundary_id="registration-boundary-01",
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
        evidence_status=RouteEvidenceStatus.CURRENT,
        session_policy_status=SessionPolicyStatus.APPROVED_REFERENCE_ONLY,
    )
    readiness = RouteReadinessDecision(
        decision_id="readiness-decision-01",
        route_id=route_id,
        readiness_status=RouteReadinessStatus.READY,
        reason_codes=("ready",),
        evidence_reference_ids=("evidence-readiness-01",),
        policy_reference=policy_reference,
    )
    health = RouteHealthState(
        route_id=route_id,
        health_status=RouteHealthStatus.READY,
        reason_codes=("healthy",),
        evidence_reference_ids=("evidence-health-01",),
        observed_at_reference="timestamp-01",
    )
    restriction = RouteRestrictionState(
        restriction_id="restriction-01",
        route_id=route_id,
        status=RouteRestrictionStatus.NONE,
        reason_codes=("none",),
        evidence_reference_ids=("evidence-restriction-01",),
        blocks_new_assignments=False,
        review_reference=None,
    )
    candidate = RouteCandidateEvaluation(
        evaluation_id="candidate-evaluation-01",
        request_reference=request_reference,
        requester_module=requester_module,
        environment_id=environment_id,
        purpose=purpose,
        capability_scope=capability_scope,
        policy_reference=policy_reference,
        route_id=route_id,
        agent_id=agent_id,
        registration_boundary=registration_boundary,
        capability=capability,
        readiness=readiness,
        health=health,
        restriction=restriction,
        reconciliation_status=RouteReconciliationStatus.NOT_REQUIRED,
        status=RouteCandidateEligibilityStatus.ELIGIBLE,
        reason_codes=("eligible",),
        evidence_reference_ids=("evidence-candidate-01",),
    )
    decision = RouteSelectionDecision(
        decision_id="selection-decision-01",
        request_reference=request_reference,
        status=RouteSelectionStatus.SELECTED,
        selected_route_id=route_id,
        candidate_route_ids=(route_id,),
        rejected_route_ids=(),
        reason_codes=("selected",),
        evidence_reference_ids=("evidence-selection-01",),
        policy_reference=policy_reference,
    )
    selection = ServerRouteSelectionBoundary(
        boundary_id="selection-boundary-01",
        authority=RouteSelectionAuthority.EGRESS_ROUTING_SERVER,
        request_reference=request_reference,
        requester_module=requester_module,
        environment_id=environment_id,
        purpose=purpose,
        capability_scope=capability_scope,
        policy_reference=policy_reference,
        candidate_evaluations=(candidate,),
        decision=decision,
    )
    lease = RouteLease(
        lease_id="lease-01",
        route_id=route_id,
        agent_id=agent_id,
        requester_module=requester_module,
        purpose=purpose,
        capability_scope=capability_scope,
        status=RouteLeaseStatus.GRANTED,
        idempotency_key="idempotency-01",
        semantic_fingerprint="fingerprint-01",
        validity_reference="validity-01",
        restriction_snapshot=RouteRestrictionStatus.NONE,
        correlation_id="correlation-01",
        causation_id="causation-01",
    )
    lease_authorization = RouteLeaseAuthorizationBoundary(
        boundary_id="lease-boundary-01",
        authority=RouteLeaseAuthority.EGRESS_ROUTING_SERVER,
        request_reference=request_reference,
        requester_module=requester_module,
        environment_id=environment_id,
        purpose=purpose,
        capability_scope=capability_scope,
        selection=selection,
        selected_candidate=candidate,
        lease=lease,
        reconciliation_status=RouteReconciliationStatus.NOT_REQUIRED,
        new_dispatch_authorized=True,
        reason_codes=("lease-granted",),
        evidence_reference_ids=("evidence-lease-authorization-01",),
    )
    assignment = TransportAssignment(
        assignment_id="assignment-01",
        lease_id=lease.lease_id,
        route_id=route_id,
        agent_id=agent_id,
        purpose=purpose,
        safe_request_reference=request_reference,
        expected_response_class="safe-response-class",
        deadline_reference="deadline-reference-01",
        route_policy_reference=policy_reference,
        profile_reference="profile-reference-01",
        redacted_config_reference="redacted-config-01",
        correlation_id=lease.correlation_id,
        causation_id=lease.causation_id,
    )
    boundary = TransportAssignmentCommitmentBoundary(
        boundary_id="commitment-boundary-01",
        authority=TransportAssignmentAuthority.EGRESS_ROUTING_SERVER,
        request_reference=request_reference,
        requester_module=requester_module,
        environment_id=environment_id,
        purpose=purpose,
        capability_scope=capability_scope,
        lease_authorization=lease_authorization,
        assignment=assignment,
        assignment_committed=True,
        reason_codes=("assignment-committed",),
        evidence_reference_ids=("evidence-assignment-commitment-01",),
    )
    return {
        "request_reference": request_reference,
        "requester_module": requester_module,
        "environment_id": environment_id,
        "purpose": purpose,
        "capability_scope": capability_scope,
        "policy_reference": policy_reference,
        "agent": agent,
        "route": route,
        "registration_boundary": registration_boundary,
        "candidate": candidate,
        "selection": selection,
        "lease": lease,
        "lease_authorization": lease_authorization,
        "assignment": assignment,
        "boundary": boundary,
    }


def _build_boundary() -> TransportAssignmentCommitmentBoundary:
    state = _build_valid_state()
    boundary = state["boundary"]
    assert isinstance(boundary, TransportAssignmentCommitmentBoundary)
    return boundary


def _state_boundary(state: dict[str, Any]) -> TransportAssignmentCommitmentBoundary:
    boundary = state["boundary"]
    assert isinstance(boundary, TransportAssignmentCommitmentBoundary)
    return boundary


def _state_assignment(state: dict[str, Any]) -> TransportAssignment:
    assignment = state["assignment"]
    assert isinstance(assignment, TransportAssignment)
    return assignment


def _state_lease_authorization(state: dict[str, Any]) -> RouteLeaseAuthorizationBoundary:
    lease_authorization = state["lease_authorization"]
    assert isinstance(lease_authorization, RouteLeaseAuthorizationBoundary)
    return lease_authorization


def test_only_egress_server_commits_assignment() -> None:
    assert len(TransportAssignmentAuthority) == 1
    assert TransportAssignmentAuthority.EGRESS_ROUTING_SERVER.value == "EGRESS_ROUTING_SERVER"
    boundary = _build_boundary()
    assert boundary.authority is TransportAssignmentAuthority.EGRESS_ROUTING_SERVER


def test_valid_er06a_authorization_permits_one_assignment_commitment_semantically() -> None:
    boundary = _build_boundary()
    assert boundary.assignment_committed is True
    assert boundary.lease_authorization.authority is RouteLeaseAuthority.EGRESS_ROUTING_SERVER
    assert boundary.lease_authorization.lease.status is RouteLeaseStatus.GRANTED
    assert boundary.lease_authorization.lease.restriction_snapshot is RouteRestrictionStatus.NONE
    assert boundary.lease_authorization.new_dispatch_authorized is True


def test_assignment_is_linked_to_exact_lease_route_agent_and_purpose() -> None:
    boundary = _build_boundary()
    assignment = boundary.assignment
    lease = boundary.lease_authorization.lease

    assert assignment.lease_id == lease.lease_id
    assert assignment.route_id == lease.route_id
    assert assignment.agent_id == lease.agent_id
    assert assignment.purpose == boundary.purpose


def test_server_boundary_preserves_request_module_environment_and_capability_provenance() -> None:
    boundary = _build_boundary()
    assert boundary.request_reference == "request-01"
    assert boundary.requester_module == "07-egress-routing"
    assert boundary.environment_id == "env-01"
    assert boundary.purpose == "search"
    assert boundary.capability_scope == ("search",)
    assert boundary.lease_authorization.request_reference == boundary.request_reference
    assert boundary.lease_authorization.requester_module == boundary.requester_module
    assert boundary.lease_authorization.environment_id == boundary.environment_id
    assert boundary.lease_authorization.purpose == boundary.purpose
    assert boundary.lease_authorization.capability_scope == boundary.capability_scope


def test_assignment_carries_safe_request_reference_only() -> None:
    boundary = _build_boundary()
    assignment = boundary.assignment
    assert assignment.safe_request_reference == boundary.request_reference
    assert not hasattr(assignment, "request_reference")


def test_assignment_carries_expected_response_class_reference_only() -> None:
    boundary = _build_boundary()
    assignment = boundary.assignment
    assert assignment.expected_response_class == "safe-response-class"
    assert "response" not in {field.name for field in fields(TransportAssignment)}
    assert "safe_response_reference" not in {field.name for field in fields(TransportAssignment)}


def test_deadline_is_opaque_reference() -> None:
    boundary = _build_boundary()
    assert boundary.assignment.deadline_reference == "deadline-reference-01"
    assert boundary.assignment.deadline_reference != ""


def test_route_policy_is_exact_selection_policy_reference() -> None:
    boundary = _build_boundary()
    assert (
        boundary.assignment.route_policy_reference
        == boundary.lease_authorization.selection.decision.policy_reference
    )


def test_profile_is_optional_reference_only() -> None:
    boundary = _build_boundary()
    assert boundary.assignment.profile_reference == "profile-reference-01"
    assert boundary.assignment.profile_reference is not None


def test_redacted_config_is_optional_reference_only() -> None:
    boundary = _build_boundary()
    assert boundary.assignment.redacted_config_reference == "redacted-config-01"
    assert boundary.assignment.redacted_config_reference is not None


def test_assignment_commitment_does_not_create_dispatch_attempt() -> None:
    boundary = _build_boundary()
    boundary_field_names = {field.name for field in fields(TransportAssignmentCommitmentBoundary)}
    assert "attempt_id" not in boundary_field_names
    assert "dispatch_status" not in boundary_field_names
    assert boundary.assignment_committed is True
    assert TransportAssignmentCommitmentBoundary is not DispatchAttempt


def test_assignment_commitment_does_not_prove_dispatch_receipt_send_or_response() -> None:
    boundary = _build_boundary()
    boundary_field_names = {field.name for field in fields(TransportAssignmentCommitmentBoundary)}
    assert "receipt_status" not in boundary_field_names
    assert "send_status" not in boundary_field_names
    assert "safe_response_reference" not in boundary_field_names
    assert "transport_outcome" not in boundary_field_names
    assert TransportAssignmentCommitmentBoundary is not TransportAssignmentOutcome
    assert boundary.assignment_committed is True
    assert boundary.lease_authorization.new_dispatch_authorized is True
    assert boundary.lease_authorization.lease.status is RouteLeaseStatus.GRANTED


def test_assignment_commitment_does_not_prove_parser_or_scan_success() -> None:
    boundary_field_names = {field.name for field in fields(TransportAssignmentCommitmentBoundary)}
    assert "parser_success" not in boundary_field_names
    assert "scan_success" not in boundary_field_names


def test_assignment_contains_no_account_or_beacon_state() -> None:
    field_names = {field.name for field in fields(TransportAssignmentCommitmentBoundary)}
    assert field_names.isdisjoint({"account", "beacon"})


def test_assignment_contains_no_tariff_payment_listing_or_notification_state() -> None:
    field_names = {field.name for field in fields(TransportAssignmentCommitmentBoundary)}
    assert field_names.isdisjoint({"tariff", "payment", "listing", "notification"})


def test_assignment_contains_no_database_credentials() -> None:
    field_names = {field.name for field in fields(TransportAssignmentCommitmentBoundary)}
    assert field_names.isdisjoint({"db", "database", "credentials", "credential_value"})


def test_assignment_contains_no_raw_cookie_or_session_values() -> None:
    field_names = {field.name for field in fields(TransportAssignmentCommitmentBoundary)}
    assert field_names.isdisjoint({"cookie_value", "session_value"})


def test_assignment_does_not_choose_provider_proxy_vpn_or_tunnel() -> None:
    field_names = {field.name for field in fields(TransportAssignmentCommitmentBoundary)}
    assert field_names.isdisjoint({"provider", "proxy", "vpn", "tunnel"})


def test_assignment_does_not_select_browser_or_windows_topology() -> None:
    field_names = {field.name for field in fields(TransportAssignmentCommitmentBoundary)}
    assert field_names.isdisjoint({"browser", "windows", "host", "hostname", "ip", "port"})


def test_assignment_does_not_define_duration_retry_backoff_capacity_values() -> None:
    field_names = {field.name for field in fields(TransportAssignmentCommitmentBoundary)}
    assert field_names.isdisjoint({"duration", "retry_count", "retry_delay", "backoff", "capacity"})


def test_assignment_does_not_mutate_lease_authorization_selection_candidate_or_lease() -> None:
    state = _build_valid_state()
    lease_before = _state_lease_authorization(state).lease
    selection_before = _state_lease_authorization(state).selection
    candidate_before = _state_lease_authorization(state).selected_candidate
    assignment_before = _state_assignment(state)

    lease_snapshot = (
        lease_before.lease_id,
        lease_before.route_id,
        lease_before.agent_id,
        lease_before.requester_module,
        lease_before.purpose,
        lease_before.capability_scope,
        lease_before.status,
        lease_before.idempotency_key,
        lease_before.semantic_fingerprint,
        lease_before.validity_reference,
        lease_before.restriction_snapshot,
        lease_before.correlation_id,
        lease_before.causation_id,
    )
    selection_snapshot = (
        selection_before.boundary_id,
        selection_before.request_reference,
        selection_before.requester_module,
        selection_before.environment_id,
        selection_before.purpose,
        selection_before.capability_scope,
        selection_before.policy_reference,
        selection_before.decision.selected_route_id,
    )
    candidate_snapshot = (
        candidate_before.evaluation_id,
        candidate_before.request_reference,
        candidate_before.requester_module,
        candidate_before.environment_id,
        candidate_before.purpose,
        candidate_before.capability_scope,
        candidate_before.policy_reference,
        candidate_before.route_id,
        candidate_before.agent_id,
        candidate_before.reconciliation_status,
        candidate_before.status,
    )
    assignment_snapshot = (
        assignment_before.assignment_id,
        assignment_before.lease_id,
        assignment_before.route_id,
        assignment_before.agent_id,
        assignment_before.purpose,
        assignment_before.safe_request_reference,
        assignment_before.expected_response_class,
        assignment_before.deadline_reference,
        assignment_before.route_policy_reference,
        assignment_before.profile_reference,
        assignment_before.redacted_config_reference,
        assignment_before.correlation_id,
        assignment_before.causation_id,
    )

    boundary = TransportAssignmentCommitmentBoundary(
        boundary_id=_state_boundary(state).boundary_id,
        authority=_state_boundary(state).authority,
        request_reference=state["request_reference"],
        requester_module=state["requester_module"],
        environment_id=state["environment_id"],
        purpose=state["purpose"],
        capability_scope=state["capability_scope"],
        lease_authorization=_state_lease_authorization(state),
        assignment=assignment_before,
        assignment_committed=True,
        reason_codes=("assignment-committed",),
        evidence_reference_ids=("evidence-assignment-commitment-01",),
    )  # type: ignore[arg-type]
    assert boundary.assignment_committed is True

    assert lease_snapshot == (
        lease_before.lease_id,
        lease_before.route_id,
        lease_before.agent_id,
        lease_before.requester_module,
        lease_before.purpose,
        lease_before.capability_scope,
        lease_before.status,
        lease_before.idempotency_key,
        lease_before.semantic_fingerprint,
        lease_before.validity_reference,
        lease_before.restriction_snapshot,
        lease_before.correlation_id,
        lease_before.causation_id,
    )
    assert selection_snapshot == (
        selection_before.boundary_id,
        selection_before.request_reference,
        selection_before.requester_module,
        selection_before.environment_id,
        selection_before.purpose,
        selection_before.capability_scope,
        selection_before.policy_reference,
        selection_before.decision.selected_route_id,
    )
    assert candidate_snapshot == (
        candidate_before.evaluation_id,
        candidate_before.request_reference,
        candidate_before.requester_module,
        candidate_before.environment_id,
        candidate_before.purpose,
        candidate_before.capability_scope,
        candidate_before.policy_reference,
        candidate_before.route_id,
        candidate_before.agent_id,
        candidate_before.reconciliation_status,
        candidate_before.status,
    )
    assert assignment_snapshot == (
        assignment_before.assignment_id,
        assignment_before.lease_id,
        assignment_before.route_id,
        assignment_before.agent_id,
        assignment_before.purpose,
        assignment_before.safe_request_reference,
        assignment_before.expected_response_class,
        assignment_before.deadline_reference,
        assignment_before.route_policy_reference,
        assignment_before.profile_reference,
        assignment_before.redacted_config_reference,
        assignment_before.correlation_id,
        assignment_before.causation_id,
    )


def test_task_marker_occurs_exactly_once_in_assignment_module() -> None:
    source = Path(__file__).resolve().parents[2] / "src/mayak/modules/egress_routing/assignment.py"
    assert source.read_text().count(ER06B_TASK_ID) == 1
