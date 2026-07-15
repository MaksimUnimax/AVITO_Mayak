from __future__ import annotations

from dataclasses import fields, is_dataclass
from pathlib import Path
from typing import Any

import pytest

import mayak.modules.egress_routing.assignment as assignment_module
from mayak.modules import egress_routing
from mayak.modules.egress_routing import (
    ER06B_TASK_ID,
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
)

EXPECTED_TASK_ID = "ER-06B-TRANSPORT-ASSIGNMENT-COMMITMENT-BOUNDARY-20260715-010"

EXPECTED_ASSIGNMENT_EXPORTS = (
    "ER06B_TASK_ID",
    "TransportAssignmentAuthority",
    "TransportAssignmentCommitmentBoundary",
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
    "ER02_TASK_ID",
    "EGRESS_SYNTHETIC_FIXTURE_IDS",
    "EGRESS_SYNTHETIC_FIXTURES",
    "EgressSyntheticFixture",
)

EXPECTED_ENUM_PAIRS = {
    TransportAssignmentAuthority: (("EGRESS_ROUTING_SERVER", "EGRESS_ROUTING_SERVER"),),
}

EXPECTED_BOUNDARY_FIELD_NAMES = (
    "boundary_id",
    "authority",
    "request_reference",
    "requester_module",
    "environment_id",
    "purpose",
    "capability_scope",
    "lease_authorization",
    "assignment",
    "assignment_committed",
    "reason_codes",
    "evidence_reference_ids",
)

EXPECTED_ASSIGNMENT_FIELD_NAMES = (
    "assignment_id",
    "lease_id",
    "route_id",
    "agent_id",
    "purpose",
    "safe_request_reference",
    "expected_response_class",
    "deadline_reference",
    "route_policy_reference",
    "profile_reference",
    "redacted_config_reference",
    "correlation_id",
    "causation_id",
)

EXPECTED_LEASE_BOUNDARY_FIELD_NAMES = (
    "boundary_id",
    "authority",
    "request_reference",
    "requester_module",
    "environment_id",
    "purpose",
    "capability_scope",
    "selection",
    "selected_candidate",
    "lease",
    "reconciliation_status",
    "new_dispatch_authorized",
    "reason_codes",
    "evidence_reference_ids",
)


def _mutate(record: object, **changes: object) -> None:
    for field_name, value in changes.items():
        object.__setattr__(record, field_name, value)


def _build_valid_state(
    *,
    request_reference: str = "request-01",
    safe_request_reference: str = "safe-request-envelope-01",
    requester_module: str = "07-egress-routing",
    environment_id: str = "env-01",
    purpose: str = "search",
    capability_scope: tuple[str, ...] = ("search",),
    lease_status: RouteLeaseStatus = RouteLeaseStatus.GRANTED,
    restriction_snapshot: RouteRestrictionStatus = RouteRestrictionStatus.NONE,
    reconciliation_status: RouteReconciliationStatus = RouteReconciliationStatus.NOT_REQUIRED,
    new_dispatch_authorized: bool = True,
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
        reconciliation_status=reconciliation_status,
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
        reconciliation_status=reconciliation_status,
        new_dispatch_authorized=new_dispatch_authorized,
        reason_codes=("lease-granted",),
        evidence_reference_ids=("evidence-lease-authorization-01",),
    )
    assignment = TransportAssignment(
        assignment_id="assignment-01",
        lease_id=lease.lease_id,
        route_id=route_id,
        agent_id=agent_id,
        purpose=purpose,
        safe_request_reference=safe_request_reference,
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
        "safe_request_reference": safe_request_reference,
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


def _boundary_kwargs_from_state(state: dict[str, Any]) -> dict[str, Any]:
    boundary = state["boundary"]
    assert isinstance(boundary, TransportAssignmentCommitmentBoundary)
    return {
        "boundary_id": boundary.boundary_id,
        "authority": boundary.authority,
        "request_reference": state["request_reference"],
        "requester_module": state["requester_module"],
        "environment_id": state["environment_id"],
        "purpose": state["purpose"],
        "capability_scope": state["capability_scope"],
        "lease_authorization": state["lease_authorization"],
        "assignment": state["assignment"],
        "assignment_committed": boundary.assignment_committed,
        "reason_codes": boundary.reason_codes,
        "evidence_reference_ids": boundary.evidence_reference_ids,
    }


def _assignment_kwargs_from_state(state: dict[str, Any]) -> dict[str, Any]:
    assignment = state["assignment"]
    assert isinstance(assignment, TransportAssignment)
    return {
        "assignment_id": assignment.assignment_id,
        "lease_id": assignment.lease_id,
        "route_id": assignment.route_id,
        "agent_id": assignment.agent_id,
        "purpose": assignment.purpose,
        "safe_request_reference": assignment.safe_request_reference,
        "expected_response_class": assignment.expected_response_class,
        "deadline_reference": assignment.deadline_reference,
        "route_policy_reference": assignment.route_policy_reference,
        "profile_reference": assignment.profile_reference,
        "redacted_config_reference": assignment.redacted_config_reference,
        "correlation_id": assignment.correlation_id,
        "causation_id": assignment.causation_id,
    }


def _lease_authorization_kwargs_from_state(state: dict[str, Any]) -> dict[str, Any]:
    lease_authorization = state["lease_authorization"]
    assert isinstance(lease_authorization, RouteLeaseAuthorizationBoundary)
    return {
        "boundary_id": lease_authorization.boundary_id,
        "authority": lease_authorization.authority,
        "request_reference": lease_authorization.request_reference,
        "requester_module": lease_authorization.requester_module,
        "environment_id": lease_authorization.environment_id,
        "purpose": lease_authorization.purpose,
        "capability_scope": lease_authorization.capability_scope,
        "selection": lease_authorization.selection,
        "selected_candidate": lease_authorization.selected_candidate,
        "lease": lease_authorization.lease,
        "reconciliation_status": lease_authorization.reconciliation_status,
        "new_dispatch_authorized": lease_authorization.new_dispatch_authorized,
        "reason_codes": lease_authorization.reason_codes,
        "evidence_reference_ids": lease_authorization.evidence_reference_ids,
    }


class TestTaskId:
    def test_exact_task_id(self) -> None:
        assert ER06B_TASK_ID == EXPECTED_TASK_ID

    def test_task_id_count_in_assignment_module(self) -> None:
        source = Path(assignment_module.__file__).read_text()
        assert source.count(ER06B_TASK_ID) == 1


class TestAssignmentModuleExports:
    def test_exact_exports(self) -> None:
        assert assignment_module.__all__ == EXPECTED_ASSIGNMENT_EXPORTS

    def test_exports_are_builtin_tuple(self) -> None:
        assert type(assignment_module.__all__) is tuple

    def test_exports_are_unique_and_indexable(self) -> None:
        assert tuple(assignment_module.__all__) == EXPECTED_ASSIGNMENT_EXPORTS
        assert len(assignment_module.__all__) == len(EXPECTED_ASSIGNMENT_EXPORTS)
        assert len(set(assignment_module.__all__)) == len(EXPECTED_ASSIGNMENT_EXPORTS)

    def test_exports_exist(self) -> None:
        for name in EXPECTED_ASSIGNMENT_EXPORTS:
            assert hasattr(assignment_module, name), f"{name} missing from assignment module"


class TestPackageExports:
    def test_package_all_is_builtin_tuple(self) -> None:
        assert type(egress_routing.__all__) is tuple

    def test_package_all_exact_order(self) -> None:
        assert egress_routing.__all__ == EXPECTED_PACKAGE_EXPORTS

    def test_package_all_iteration_and_indexing(self) -> None:
        observed = tuple(egress_routing.__all__)
        assert observed == EXPECTED_PACKAGE_EXPORTS
        assert observed[0] == "MODULE_ID"
        assert observed[-1] == "EgressSyntheticFixture"
        assert observed[49] == "RouteLeaseAuthority"
        assert observed[50] == "RouteLeaseAuthorizationBoundary"
        assert observed[51] == "ER06B_TASK_ID"
        assert observed[52] == "TransportAssignmentAuthority"
        assert observed[53] == "TransportAssignmentCommitmentBoundary"

    def test_package_all_length_and_uniqueness(self) -> None:
        assert len(egress_routing.__all__) == len(EXPECTED_PACKAGE_EXPORTS)
        assert len(set(egress_routing.__all__)) == len(EXPECTED_PACKAGE_EXPORTS)

    def test_package_all_names_exist(self) -> None:
        for name in EXPECTED_PACKAGE_EXPORTS:
            assert hasattr(egress_routing, name), f"{name} missing from package"


class TestAuthorityMatrix:
    def test_exact_enum_matrix(self) -> None:
        for enum_cls, expected_pairs in EXPECTED_ENUM_PAIRS.items():
            actual_pairs = tuple((member.name, member.value) for member in enum_cls)
            assert actual_pairs == expected_pairs

    def test_only_egress_server_authority(self) -> None:
        assert len(TransportAssignmentAuthority) == 1
        assert TransportAssignmentAuthority.EGRESS_ROUTING_SERVER.value == "EGRESS_ROUTING_SERVER"


class TestBoundaryShape:
    def test_is_frozen_and_slotted_dataclass(self) -> None:
        assert is_dataclass(TransportAssignmentCommitmentBoundary)
        assert TransportAssignmentCommitmentBoundary.__dataclass_params__.frozen is True  # type: ignore[attr-defined]
        assert TransportAssignmentCommitmentBoundary.__dataclass_params__.slots is True  # type: ignore[attr-defined]

    def test_exact_field_order(self) -> None:
        assert (
            tuple(field.name for field in fields(TransportAssignmentCommitmentBoundary))
            == EXPECTED_BOUNDARY_FIELD_NAMES
        )

    def test_boundary_field_count(self) -> None:
        assert len(fields(TransportAssignmentCommitmentBoundary)) == len(
            EXPECTED_BOUNDARY_FIELD_NAMES
        )

    def test_assignment_field_order_is_unchanged(self) -> None:
        assert (
            tuple(field.name for field in fields(TransportAssignment))
            == EXPECTED_ASSIGNMENT_FIELD_NAMES
        )

    def test_lease_authorization_field_order_is_unchanged(self) -> None:
        assert (
            tuple(field.name for field in fields(RouteLeaseAuthorizationBoundary))
            == EXPECTED_LEASE_BOUNDARY_FIELD_NAMES
        )

    def test_boundary_does_not_expose_forbidden_state(self) -> None:
        field_names = {field.name for field in fields(TransportAssignmentCommitmentBoundary)}
        forbidden = {
            "attempt_id",
            "attempt_ordinal",
            "dispatch_status",
            "receipt_status",
            "send_status",
            "outcome_id",
            "transport_outcome",
            "safe_response_reference",
            "reconciliation_result",
            "retry_count",
            "retry_delay",
            "backoff",
            "duration",
            "timeout_seconds",
            "expires_at",
            "renewal",
            "provider",
            "protocol",
            "hostname",
            "host",
            "ip",
            "port",
            "proxy",
            "vpn",
            "tunnel",
            "cookie_value",
            "session_value",
            "credential_value",
            "account",
            "beacon",
            "tariff",
            "payment",
            "listing",
            "notification",
        }
        assert field_names.isdisjoint(forbidden)


class TestMandatoryValidation:
    def test_wrong_authority_rejected(self) -> None:
        kwargs = _boundary_kwargs_from_state(_build_valid_state())
        kwargs["authority"] = RouteLeaseAuthority.EGRESS_ROUTING_SERVER
        with pytest.raises(ValueError):
            TransportAssignmentCommitmentBoundary(**kwargs)  # type: ignore[arg-type]

    @pytest.mark.parametrize(
        "field_name",
        (
            "boundary_id",
            "request_reference",
            "requester_module",
            "environment_id",
            "purpose",
        ),
    )
    def test_mandatory_text_fields_must_be_non_blank(self, field_name: str) -> None:
        kwargs = _boundary_kwargs_from_state(_build_valid_state())
        kwargs[field_name] = " "
        with pytest.raises(ValueError):
            TransportAssignmentCommitmentBoundary(**kwargs)  # type: ignore[arg-type]

    def test_assignment_committed_must_be_true(self) -> None:
        kwargs = _boundary_kwargs_from_state(_build_valid_state())
        kwargs["assignment_committed"] = False
        with pytest.raises(ValueError):
            TransportAssignmentCommitmentBoundary(**kwargs)  # type: ignore[arg-type]


class TestTupleValidation:
    @pytest.mark.parametrize(
        ("field_name", "value"),
        (
            ("capability_scope", ["search"]),
            ("capability_scope", ()),
            ("capability_scope", ("search", 1)),
            ("reason_codes", ["reason"]),
            ("reason_codes", ()),
            ("evidence_reference_ids", ["evidence"]),
            ("evidence_reference_ids", ()),
        ),
    )
    def test_exact_tuple_validation(self, field_name: str, value: object) -> None:
        kwargs = _boundary_kwargs_from_state(_build_valid_state())
        kwargs[field_name] = value
        with pytest.raises(ValueError):
            TransportAssignmentCommitmentBoundary(**kwargs)  # type: ignore[arg-type]


class TestBoolValidation:
    def test_assignment_committed_must_be_builtin_bool(self) -> None:
        kwargs = _boundary_kwargs_from_state(_build_valid_state())
        kwargs["assignment_committed"] = 1
        with pytest.raises(ValueError):
            TransportAssignmentCommitmentBoundary(**kwargs)  # type: ignore[arg-type]


class TestNestedTypeValidation:
    def test_wrong_lease_authorization_type_rejected(self) -> None:
        kwargs = _boundary_kwargs_from_state(_build_valid_state())
        kwargs["lease_authorization"] = "invalid"
        with pytest.raises(ValueError):
            TransportAssignmentCommitmentBoundary(**kwargs)  # type: ignore[arg-type]

    def test_wrong_assignment_type_rejected(self) -> None:
        kwargs = _boundary_kwargs_from_state(_build_valid_state())
        kwargs["assignment"] = "invalid"
        with pytest.raises(ValueError):
            TransportAssignmentCommitmentBoundary(**kwargs)  # type: ignore[arg-type]


class TestLeaseAuthorizationLinkage:
    def test_valid_context_accepts_exact_lease_authorization(self) -> None:
        boundary = _build_boundary()
        assert boundary.authority is TransportAssignmentAuthority.EGRESS_ROUTING_SERVER
        assert boundary.assignment_committed is True
        assert boundary.lease_authorization.authority is RouteLeaseAuthority.EGRESS_ROUTING_SERVER
        assert boundary.lease_authorization.lease.status is RouteLeaseStatus.GRANTED
        assert (
            boundary.lease_authorization.lease.restriction_snapshot is RouteRestrictionStatus.NONE
        )
        assert boundary.lease_authorization.reconciliation_status in {
            RouteReconciliationStatus.NOT_REQUIRED,
            RouteReconciliationStatus.RESOLVED_NOT_SENT,
            RouteReconciliationStatus.RESOLVED_SENT,
            RouteReconciliationStatus.RESOLVED_TERMINAL,
        }

    @pytest.mark.parametrize(
        ("field_name", "value"),
        (
            ("request_reference", "wrong-request"),
            ("requester_module", "wrong-module"),
            ("environment_id", "wrong-environment"),
            ("purpose", "wrong-purpose"),
            ("capability_scope", ("wrong-capability",)),
        ),
    )
    def test_lease_authorization_context_mismatch_rejected(
        self, field_name: str, value: object
    ) -> None:
        state = _build_valid_state()
        lease_authorization = state["lease_authorization"]
        assert isinstance(lease_authorization, RouteLeaseAuthorizationBoundary)
        _mutate(lease_authorization, **{field_name: value})
        kwargs = _boundary_kwargs_from_state(state)
        with pytest.raises(ValueError):
            TransportAssignmentCommitmentBoundary(**kwargs)  # type: ignore[arg-type]

    def test_wrong_lease_authority_rejected(self) -> None:
        state = _build_valid_state()
        lease_authorization = state["lease_authorization"]
        assert isinstance(lease_authorization, RouteLeaseAuthorizationBoundary)
        _mutate(lease_authorization, authority="wrong-authority")
        kwargs = _boundary_kwargs_from_state(state)
        with pytest.raises(ValueError):
            TransportAssignmentCommitmentBoundary(**kwargs)  # type: ignore[arg-type]


class TestLeaseAuthorizationGates:
    @pytest.mark.parametrize(
        ("mutation", "value"),
        (
            ("lease_status", RouteLeaseStatus.REQUESTED),
            ("lease_status", RouteLeaseStatus.REJECTED),
            ("lease_status", RouteLeaseStatus.DISPATCHED),
            ("lease_status", RouteLeaseStatus.IN_USE),
            ("lease_status", RouteLeaseStatus.COMPLETED),
            ("lease_status", RouteLeaseStatus.EXPIRED),
            ("lease_status", RouteLeaseStatus.REVOKED),
            ("lease_status", RouteLeaseStatus.AMBIGUOUS),
            ("lease_status", RouteLeaseStatus.RECONCILIATION_REQUIRED),
            ("lease_status", RouteLeaseStatus.FAILED),
            ("restriction_snapshot", RouteRestrictionStatus.RESTRICTED),
            ("restriction_snapshot", RouteRestrictionStatus.DEGRADED),
            ("restriction_snapshot", RouteRestrictionStatus.QUARANTINED),
            ("restriction_snapshot", RouteRestrictionStatus.SUSPENDED),
            ("restriction_snapshot", RouteRestrictionStatus.RETIRED),
            ("reconciliation_status", RouteReconciliationStatus.REQUIRED),
            ("reconciliation_status", RouteReconciliationStatus.PENDING),
            ("reconciliation_status", RouteReconciliationStatus.REMAINS_AMBIGUOUS),
            ("reconciliation_status", RouteReconciliationStatus.MANUAL_REVIEW_REQUIRED),
            ("new_dispatch_authorized", False),
        ),
    )
    def test_lease_authorization_not_permitting_dispatch_is_rejected(
        self,
        mutation: str,
        value: object,
    ) -> None:
        state = _build_valid_state()
        lease_authorization = state["lease_authorization"]
        assert isinstance(lease_authorization, RouteLeaseAuthorizationBoundary)
        if mutation == "lease_status":
            _mutate(lease_authorization.lease, status=value)
        elif mutation == "restriction_snapshot":
            _mutate(lease_authorization.lease, restriction_snapshot=value)
        elif mutation == "reconciliation_status":
            _mutate(lease_authorization, reconciliation_status=value)
        else:
            _mutate(lease_authorization, new_dispatch_authorized=value)
        kwargs = _boundary_kwargs_from_state(state)
        with pytest.raises(ValueError):
            TransportAssignmentCommitmentBoundary(**kwargs)  # type: ignore[arg-type]


class TestAssignmentLinkage:
    def test_valid_assignment_linkage_is_accepted(self) -> None:
        boundary = _build_boundary()
        assert boundary.assignment.lease_id == boundary.lease_authorization.lease.lease_id
        assert boundary.assignment.route_id == boundary.lease_authorization.lease.route_id
        assert boundary.assignment.agent_id == boundary.lease_authorization.lease.agent_id
        assert boundary.assignment.purpose == boundary.purpose
        assert boundary.assignment.safe_request_reference == "safe-request-envelope-01"
        assert boundary.assignment.safe_request_reference != boundary.request_reference
        assert boundary.assignment.expected_response_class == "safe-response-class"
        assert boundary.assignment.deadline_reference == "deadline-reference-01"
        assert (
            boundary.assignment.route_policy_reference
            == boundary.lease_authorization.selection.decision.policy_reference
        )
        assert boundary.assignment.profile_reference == "profile-reference-01"
        assert boundary.assignment.redacted_config_reference == "redacted-config-01"

    def test_distinct_non_blank_request_and_safe_request_references_are_accepted(self) -> None:
        state = _build_valid_state()
        boundary = state["boundary"]
        assignment = state["assignment"]
        assert isinstance(boundary, TransportAssignmentCommitmentBoundary)
        assert isinstance(assignment, TransportAssignment)
        assert state["request_reference"] == "request-01"
        assert state["safe_request_reference"] == "safe-request-envelope-01"
        assert boundary.request_reference == state["request_reference"]
        assert assignment.safe_request_reference == state["safe_request_reference"]
        assert boundary.request_reference != assignment.safe_request_reference
        assert boundary.request_reference.strip()
        assert assignment.safe_request_reference.strip()

    @pytest.mark.parametrize(
        ("field_name", "value"),
        (
            ("lease_id", "wrong-lease"),
            ("route_id", "wrong-route"),
            ("agent_id", "wrong-agent"),
            ("purpose", "wrong-purpose"),
            ("correlation_id", "wrong-correlation"),
            ("causation_id", "wrong-causation"),
            ("route_policy_reference", "wrong-policy"),
        ),
    )
    def test_assignment_linkage_mismatch_is_rejected(self, field_name: str, value: object) -> None:
        state = _build_valid_state()
        assignment = state["assignment"]
        assert isinstance(assignment, TransportAssignment)
        _mutate(assignment, **{field_name: value})
        kwargs = _boundary_kwargs_from_state(state)
        with pytest.raises(ValueError):
            TransportAssignmentCommitmentBoundary(**kwargs)  # type: ignore[arg-type]


class TestCommitmentSemantics:
    def test_valid_commitment_boundary_is_accepted(self) -> None:
        boundary = _build_boundary()
        assert boundary.assignment_committed is True
        assert boundary.authority is TransportAssignmentAuthority.EGRESS_ROUTING_SERVER
        assert boundary.reason_codes == ("assignment-committed",)
        assert boundary.evidence_reference_ids == ("evidence-assignment-commitment-01",)

    def test_commitment_does_not_create_dispatch_attempt_or_outcome_state(self) -> None:
        boundary_field_names = {
            field.name for field in fields(TransportAssignmentCommitmentBoundary)
        }
        assignment_field_names = {field.name for field in fields(TransportAssignment)}
        assert "attempt_id" not in boundary_field_names
        assert "dispatch_status" not in boundary_field_names
        assert "safe_response_reference" not in boundary_field_names
        assert "outcome_id" not in boundary_field_names
        assert "attempt_id" not in assignment_field_names
        assert "dispatch_status" not in assignment_field_names
        assert "safe_response_reference" not in assignment_field_names

    def test_commitment_does_not_prove_dispatch_or_response(self) -> None:
        boundary = _build_boundary()
        assert boundary.assignment_committed is True
        assert boundary.lease_authorization.lease.status is RouteLeaseStatus.GRANTED
        assert boundary.lease_authorization.new_dispatch_authorized is True
        assert (
            boundary.lease_authorization.reconciliation_status
            is RouteReconciliationStatus.NOT_REQUIRED
        )

    def test_commitment_preserves_minimal_data(self) -> None:
        boundary = _build_boundary()
        assignment_field_names = {field.name for field in fields(boundary.assignment)}
        forbidden = {
            "account",
            "beacon",
            "tariff",
            "payment",
            "listing",
            "notification",
            "provider",
            "proxy",
            "vpn",
            "tunnel",
            "browser",
            "windows",
            "cookie_value",
            "session_value",
            "credential_value",
        }
        assert assignment_field_names.isdisjoint(forbidden)

    def test_commitment_does_not_mutate_inputs(self) -> None:
        state = _build_valid_state()
        lease_authorization = state["lease_authorization"]
        assignment = state["assignment"]
        assert isinstance(lease_authorization, RouteLeaseAuthorizationBoundary)
        assert isinstance(assignment, TransportAssignment)
        lease_before = _lease_authorization_kwargs_from_state(state)
        assignment_before = _assignment_kwargs_from_state(state)
        TransportAssignmentCommitmentBoundary(**_boundary_kwargs_from_state(state))
        lease_after = _lease_authorization_kwargs_from_state(state)
        assignment_after = _assignment_kwargs_from_state(state)
        assert lease_before == lease_after
        assert assignment_before == assignment_after


class TestRegressionPreservation:
    def test_task_marker_occurs_exactly_once_in_assignment_module(self) -> None:
        source = Path(assignment_module.__file__).read_text()
        assert source.count(ER06B_TASK_ID) == 1
