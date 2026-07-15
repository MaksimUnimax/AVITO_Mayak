from __future__ import annotations

from dataclasses import fields
from typing import Any

from mayak.modules.egress_routing import (
    AgentLifecycleStatus,
    AgentRegistration,
    AgentRegistrationStatus,
    AgentRouteAssociation,
    AgentRouteAssociationStatus,
    AgentRouteRegistrationBoundary,
    DispatchAttempt,
    DispatchStatus,
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
    TransportDispatchAttemptBoundary,
    TransportDispatchAuthority,
)


def _mutate(record: object, **changes: object) -> None:
    for field_name, value in changes.items():
        object.__setattr__(record, field_name, value)


def _snapshot(record: Any) -> tuple[object, ...]:
    return tuple(getattr(record, field.name) for field in fields(record))


def _build_state(
    *,
    dispatch_status: DispatchStatus = DispatchStatus.PENDING,
    new_dispatch_effect_authorized: bool | None = None,
    reconciliation_required: bool | None = None,
    attempt_ordinal: int = 1,
    outcome_reference: str | None = None,
    lease_status: RouteLeaseStatus = RouteLeaseStatus.GRANTED,
    restriction_snapshot: RouteRestrictionStatus = RouteRestrictionStatus.NONE,
    lease_reconciliation_status: RouteReconciliationStatus = RouteReconciliationStatus.NOT_REQUIRED,
) -> dict[str, object]:
    request_reference = "request-01"
    requester_module = "07-egress-routing"
    environment_id = "env-01"
    purpose = "search"
    capability_scope = ("search",)
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
        status=lease_status,
        idempotency_key="idempotency-01",
        semantic_fingerprint="fingerprint-01",
        validity_reference="validity-01",
        restriction_snapshot=restriction_snapshot,
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
        reconciliation_status=lease_reconciliation_status,
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
        safe_request_reference="safe-request-envelope-01",
        expected_response_class="safe-response-class",
        deadline_reference="deadline-reference-01",
        route_policy_reference=policy_reference,
        profile_reference="profile-reference-01",
        redacted_config_reference="redacted-config-01",
        correlation_id=lease.correlation_id,
        causation_id=lease.causation_id,
    )
    commitment = TransportAssignmentCommitmentBoundary(
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

    if new_dispatch_effect_authorized is None:
        new_dispatch_effect_authorized = dispatch_status is DispatchStatus.PENDING
    if reconciliation_required is None:
        reconciliation_required = dispatch_status is DispatchStatus.UNKNOWN
    attempt = DispatchAttempt(
        attempt_id="attempt-01",
        assignment_id=assignment.assignment_id,
        lease_id=assignment.lease_id,
        route_id=assignment.route_id,
        agent_id=assignment.agent_id,
        dispatch_status=dispatch_status,
        attempt_ordinal=attempt_ordinal,
        outcome_reference=outcome_reference,
        reconciliation_required=reconciliation_required,
        correlation_id=assignment.correlation_id,
        causation_id=assignment.causation_id,
    )
    boundary = TransportDispatchAttemptBoundary(
        boundary_id="dispatch-boundary-01",
        authority=TransportDispatchAuthority.EGRESS_ROUTING_SERVER,
        assignment_commitment=commitment,
        attempt=attempt,
        dispatch_state_committed=True,
        new_dispatch_effect_authorized=new_dispatch_effect_authorized,
        reason_codes=("dispatch-committed",),
        evidence_reference_ids=("evidence-dispatch-01",),
    )
    return {
        "agent": agent,
        "route": route,
        "registration_boundary": registration_boundary,
        "candidate": candidate,
        "selection": selection,
        "lease": lease,
        "lease_authorization": lease_authorization,
        "assignment": assignment,
        "assignment_commitment": commitment,
        "attempt": attempt,
        "boundary": boundary,
    }


def _build_boundary(**kwargs: Any) -> TransportDispatchAttemptBoundary:
    state = _build_state(**kwargs)
    boundary = state["boundary"]
    assert isinstance(boundary, TransportDispatchAttemptBoundary)
    return boundary


def test_only_egress_server_commits_dispatch_state() -> None:
    assert len(TransportDispatchAuthority) == 1
    assert TransportDispatchAuthority.EGRESS_ROUTING_SERVER.value == "EGRESS_ROUTING_SERVER"
    boundary = _build_boundary()
    assert boundary.authority is TransportDispatchAuthority.EGRESS_ROUTING_SERVER


def test_pending_permits_exact_first_dispatch_effect_semantically() -> None:
    boundary = _build_boundary(dispatch_status=DispatchStatus.PENDING)
    assert boundary.new_dispatch_effect_authorized is True
    assert boundary.attempt.dispatch_status is DispatchStatus.PENDING
    assert boundary.attempt.attempt_ordinal == 1
    assert boundary.attempt.outcome_reference is None
    assert boundary.attempt.reconciliation_required is False


def test_pending_does_not_prove_dispatch_happened() -> None:
    boundary = _build_boundary(dispatch_status=DispatchStatus.PENDING)
    assert boundary.attempt.dispatch_status is DispatchStatus.PENDING
    assert boundary.dispatch_state_committed is True
    assert boundary.attempt.outcome_reference is None


def test_attempted_blocks_a_second_dispatch() -> None:
    boundary = _build_boundary(dispatch_status=DispatchStatus.ATTEMPTED)
    assert boundary.attempt.dispatch_status is DispatchStatus.ATTEMPTED
    assert boundary.new_dispatch_effect_authorized is False
    assert boundary.attempt.outcome_reference is None


def test_attempted_does_not_prove_receipt() -> None:
    boundary = _build_boundary(dispatch_status=DispatchStatus.ATTEMPTED)
    assert boundary.attempt.dispatch_status is DispatchStatus.ATTEMPTED
    assert boundary.attempt.reconciliation_required is False


def test_acknowledged_proves_only_receipt_level_state() -> None:
    boundary = _build_boundary(dispatch_status=DispatchStatus.ACKNOWLEDGED)
    assert boundary.attempt.dispatch_status is DispatchStatus.ACKNOWLEDGED
    assert boundary.new_dispatch_effect_authorized is False
    assert boundary.attempt.outcome_reference is None


def test_acknowledged_does_not_prove_send() -> None:
    boundary = _build_boundary(dispatch_status=DispatchStatus.ACKNOWLEDGED)
    assert boundary.attempt.dispatch_status is DispatchStatus.ACKNOWLEDGED
    assert boundary.attempt.reconciliation_required is False


def test_rejected_does_not_prove_send() -> None:
    boundary = _build_boundary(dispatch_status=DispatchStatus.REJECTED)
    assert boundary.attempt.dispatch_status is DispatchStatus.REJECTED
    assert boundary.new_dispatch_effect_authorized is False
    assert boundary.attempt.outcome_reference is None


def test_rejected_does_not_authorize_retry() -> None:
    boundary = _build_boundary(dispatch_status=DispatchStatus.REJECTED)
    assert boundary.attempt.dispatch_status is DispatchStatus.REJECTED
    assert boundary.attempt.reconciliation_required is False


def test_unknown_is_reconcile_first() -> None:
    boundary = _build_boundary(
        dispatch_status=DispatchStatus.UNKNOWN,
        reconciliation_required=True,
        new_dispatch_effect_authorized=False,
    )
    assert boundary.attempt.dispatch_status is DispatchStatus.UNKNOWN
    assert boundary.attempt.reconciliation_required is True
    assert boundary.new_dispatch_effect_authorized is False


def test_unknown_blocks_blind_replay() -> None:
    boundary = _build_boundary(
        dispatch_status=DispatchStatus.UNKNOWN,
        reconciliation_required=True,
        new_dispatch_effect_authorized=False,
    )
    assert boundary.attempt.outcome_reference is None
    assert boundary.dispatch_state_committed is True


def test_not_sent_does_not_automatically_authorize_retry() -> None:
    boundary = _build_boundary(dispatch_status=DispatchStatus.NOT_SENT)
    assert boundary.attempt.dispatch_status is DispatchStatus.NOT_SENT
    assert boundary.new_dispatch_effect_authorized is False
    assert boundary.attempt.reconciliation_required is False


def test_sent_blocks_another_dispatch() -> None:
    boundary = _build_boundary(dispatch_status=DispatchStatus.SENT)
    assert boundary.attempt.dispatch_status is DispatchStatus.SENT
    assert boundary.new_dispatch_effect_authorized is False
    assert boundary.attempt.outcome_reference is None


def test_sent_does_not_prove_response() -> None:
    boundary = _build_boundary(dispatch_status=DispatchStatus.SENT)
    assert boundary.attempt.dispatch_status is DispatchStatus.SENT
    assert boundary.attempt.reconciliation_required is False


def test_sent_does_not_prove_transport_success() -> None:
    boundary = _build_boundary(dispatch_status=DispatchStatus.SENT)
    field_names = {field.name for field in fields(TransportDispatchAttemptBoundary)}
    assert boundary.attempt.dispatch_status is DispatchStatus.SENT
    assert "transport_outcome" not in field_names


def test_sent_does_not_prove_parser_success() -> None:
    boundary = _build_boundary(dispatch_status=DispatchStatus.SENT)
    assert boundary.attempt.dispatch_status is DispatchStatus.SENT
    assert "parser_success" not in {field.name for field in fields(DispatchAttempt)}


def test_sent_does_not_prove_scan_success() -> None:
    boundary = _build_boundary(dispatch_status=DispatchStatus.SENT)
    assert boundary.attempt.dispatch_status is DispatchStatus.SENT
    assert "scan_success" not in {field.name for field in fields(DispatchAttempt)}


def test_attempt_is_linked_to_exact_committed_assignment() -> None:
    boundary = _build_boundary()
    assert boundary.assignment_commitment.assignment.assignment_id == boundary.attempt.assignment_id
    assert boundary.assignment_commitment.assignment.lease_id == boundary.attempt.lease_id
    assert boundary.assignment_commitment.assignment.route_id == boundary.attempt.route_id
    assert boundary.assignment_commitment.assignment.agent_id == boundary.attempt.agent_id


def test_attempt_is_linked_to_exact_lease() -> None:
    boundary = _build_boundary()
    lease = boundary.assignment_commitment.lease_authorization.lease
    assert lease.lease_id == boundary.attempt.lease_id
    assert lease.route_id == boundary.attempt.route_id
    assert lease.agent_id == boundary.attempt.agent_id


def test_attempt_is_linked_to_exact_route() -> None:
    boundary = _build_boundary()
    lease = boundary.assignment_commitment.lease_authorization.lease
    assert boundary.assignment_commitment.assignment.route_id == boundary.attempt.route_id
    assert lease.route_id == boundary.attempt.route_id


def test_attempt_is_linked_to_exact_agent() -> None:
    boundary = _build_boundary()
    lease = boundary.assignment_commitment.lease_authorization.lease
    assert boundary.assignment_commitment.assignment.agent_id == boundary.attempt.agent_id
    assert lease.agent_id == boundary.attempt.agent_id


def test_correlation_and_causation_are_preserved() -> None:
    boundary = _build_boundary()
    assignment = boundary.assignment_commitment.assignment
    assert assignment.correlation_id == boundary.attempt.correlation_id
    assert assignment.causation_id == boundary.attempt.causation_id


def test_only_first_attempt_ordinal_is_accepted() -> None:
    boundary = _build_boundary()
    assert boundary.attempt.attempt_ordinal == 1


def test_outcome_remains_separate() -> None:
    boundary = _build_boundary()
    boundary_field_names = {field.name for field in fields(TransportDispatchAttemptBoundary)}
    attempt_field_names = {field.name for field in fields(DispatchAttempt)}
    assert "outcome_id" not in boundary_field_names
    assert "transport_outcome" not in boundary_field_names
    assert "safe_response_reference" not in boundary_field_names
    assert "response_status" not in boundary_field_names
    assert "safe_response_reference" not in attempt_field_names
    assert boundary.attempt.outcome_reference is None


def test_no_transport_assignment_outcome_created() -> None:
    _build_boundary()
    field_names = {field.name for field in fields(TransportDispatchAttemptBoundary)}
    assert "outcome_id" not in field_names
    assert "transport_outcome" not in field_names


def test_no_response_payload_stored() -> None:
    _build_boundary()
    field_names = {field.name for field in fields(TransportDispatchAttemptBoundary)}
    assert field_names.isdisjoint(
        {"response_payload", "response_body", "receipt_payload", "send_payload"}
    )


def test_no_account_beacon_tariff_payment_listing_notification_state() -> None:
    _build_boundary()
    field_names = {field.name for field in fields(TransportDispatchAttemptBoundary)}
    assert field_names.isdisjoint(
        {"account", "beacon", "tariff", "payment", "listing", "notification"}
    )


def test_no_provider_proxy_vpn_tunnel_selection() -> None:
    _build_boundary()
    field_names = {field.name for field in fields(TransportDispatchAttemptBoundary)}
    assert field_names.isdisjoint({"provider", "proxy", "vpn", "tunnel"})


def test_no_browser_windows_topology() -> None:
    _build_boundary()
    field_names = {field.name for field in fields(TransportDispatchAttemptBoundary)}
    assert field_names.isdisjoint({"browser", "windows", "host", "hostname", "ip", "port"})


def test_no_duration_retry_backoff_capacity_values() -> None:
    _build_boundary()
    field_names = {field.name for field in fields(TransportDispatchAttemptBoundary)}
    assert field_names.isdisjoint({"duration", "retry_count", "retry_delay", "backoff", "capacity"})


def test_no_mutation_of_assignment_commitment_or_nested_records() -> None:
    state = _build_state()
    assignment_before = _snapshot(state["assignment"])
    commitment_before = _snapshot(state["assignment_commitment"])
    lease_before = _snapshot(state["lease"])
    attempt_before = _snapshot(state["attempt"])
    TransportDispatchAttemptBoundary(
        boundary_id="dispatch-boundary-01",
        authority=TransportDispatchAuthority.EGRESS_ROUTING_SERVER,
        assignment_commitment=state["assignment_commitment"],  # type: ignore[arg-type]
        attempt=state["attempt"],  # type: ignore[arg-type]
        dispatch_state_committed=True,
        new_dispatch_effect_authorized=True,
        reason_codes=("dispatch-committed",),
        evidence_reference_ids=("evidence-dispatch-01",),
    )
    assert assignment_before == _snapshot(state["assignment"])
    assert commitment_before == _snapshot(state["assignment_commitment"])
    assert lease_before == _snapshot(state["lease"])
    assert attempt_before == _snapshot(state["attempt"])
