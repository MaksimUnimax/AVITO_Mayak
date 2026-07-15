from __future__ import annotations

from dataclasses import fields, is_dataclass
from pathlib import Path
from typing import Any

import pytest

import mayak.modules.egress_routing.dispatch as dispatch_module
from mayak.modules import egress_routing
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

EXPECTED_TASK_ID = "ER-06C-FIRST-DISPATCH-ATTEMPT-BOUNDARY-20260715-012"

EXPECTED_DISPATCH_EXPORTS = (
    "ER06C_TASK_ID",
    "TransportDispatchAuthority",
    "TransportDispatchAttemptBoundary",
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
    "ER02_TASK_ID",
    "EGRESS_SYNTHETIC_FIXTURE_IDS",
    "EGRESS_SYNTHETIC_FIXTURES",
    "EgressSyntheticFixture",
)

EXPECTED_ENUM_PAIRS = {
    TransportDispatchAuthority: (("EGRESS_ROUTING_SERVER", "EGRESS_ROUTING_SERVER"),),
    DispatchStatus: (
        ("PENDING", "PENDING"),
        ("ATTEMPTED", "ATTEMPTED"),
        ("ACKNOWLEDGED", "ACKNOWLEDGED"),
        ("REJECTED", "REJECTED"),
        ("UNKNOWN", "UNKNOWN"),
        ("NOT_SENT", "NOT_SENT"),
        ("SENT", "SENT"),
    ),
}

EXPECTED_BOUNDARY_FIELD_NAMES = (
    "boundary_id",
    "authority",
    "assignment_commitment",
    "attempt",
    "dispatch_state_committed",
    "new_dispatch_effect_authorized",
    "reason_codes",
    "evidence_reference_ids",
)

EXPECTED_DISPATCH_ATTEMPT_FIELD_NAMES = (
    "attempt_id",
    "assignment_id",
    "lease_id",
    "route_id",
    "agent_id",
    "dispatch_status",
    "attempt_ordinal",
    "outcome_reference",
    "reconciliation_required",
    "correlation_id",
    "causation_id",
)

EXPECTED_ASSIGNMENT_COMMITMENT_FIELD_NAMES = (
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

_RESOLVED_RECONCILIATION_STATUSES = (
    RouteReconciliationStatus.NOT_REQUIRED,
    RouteReconciliationStatus.RESOLVED_NOT_SENT,
    RouteReconciliationStatus.RESOLVED_SENT,
    RouteReconciliationStatus.RESOLVED_TERMINAL,
)


def _mutate(record: object, **changes: object) -> None:
    for field_name, value in changes.items():
        object.__setattr__(record, field_name, value)


def _build_valid_state(
    *,
    dispatch_status: DispatchStatus = DispatchStatus.PENDING,
    new_dispatch_effect_authorized: bool | None = None,
    reconciliation_required: bool | None = None,
    attempt_ordinal: int = 1,
    outcome_reference: str | None = None,
    lease_status: RouteLeaseStatus = RouteLeaseStatus.GRANTED,
    restriction_snapshot: RouteRestrictionStatus = RouteRestrictionStatus.NONE,
    reconciliation_status: RouteReconciliationStatus = RouteReconciliationStatus.NOT_REQUIRED,
    assignment_committed: bool = True,
    commitment_authority: TransportAssignmentAuthority = (
        TransportAssignmentAuthority.EGRESS_ROUTING_SERVER
    ),
) -> dict[str, Any]:
    request_reference = "request-01"
    requester_module = "07-egress-routing"
    environment_id = "env-01"
    purpose = "search"
    capability_scope = ("search",)
    agent_id = "agent-01"
    route_id = "route-01"
    policy_reference = "policy-01"
    lease_reconciliation_status = reconciliation_status

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
        authority=commitment_authority,
        request_reference=request_reference,
        requester_module=requester_module,
        environment_id=environment_id,
        purpose=purpose,
        capability_scope=capability_scope,
        lease_authorization=lease_authorization,
        assignment=assignment,
        assignment_committed=assignment_committed,
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
        "request_reference": request_reference,
        "requester_module": requester_module,
        "environment_id": environment_id,
        "purpose": purpose,
        "capability_scope": capability_scope,
    }


def _build_boundary(**kwargs: Any) -> TransportDispatchAttemptBoundary:
    state = _build_valid_state(**kwargs)
    boundary = state["boundary"]
    assert isinstance(boundary, TransportDispatchAttemptBoundary)
    return boundary


def _boundary_kwargs_from_state(state: dict[str, Any]) -> dict[str, Any]:
    boundary = state["boundary"]
    assert isinstance(boundary, TransportDispatchAttemptBoundary)
    return {
        "boundary_id": boundary.boundary_id,
        "authority": boundary.authority,
        "assignment_commitment": state["assignment_commitment"],
        "attempt": state["attempt"],
        "dispatch_state_committed": boundary.dispatch_state_committed,
        "new_dispatch_effect_authorized": boundary.new_dispatch_effect_authorized,
        "reason_codes": boundary.reason_codes,
        "evidence_reference_ids": boundary.evidence_reference_ids,
    }


class TestTaskId:
    def test_exact_task_id(self) -> None:
        assert dispatch_module.ER06C_TASK_ID == EXPECTED_TASK_ID

    def test_task_id_count_in_dispatch_module(self) -> None:
        source = Path(dispatch_module.__file__).read_text()
        assert source.count(EXPECTED_TASK_ID) == 1


class TestModuleExports:
    def test_exact_exports(self) -> None:
        assert dispatch_module.__all__ == EXPECTED_DISPATCH_EXPORTS

    def test_exports_are_builtin_tuple(self) -> None:
        assert type(dispatch_module.__all__) is tuple

    def test_exports_are_unique_and_indexable(self) -> None:
        observed = tuple(dispatch_module.__all__)
        assert observed == EXPECTED_DISPATCH_EXPORTS
        assert observed[0] == "ER06C_TASK_ID"
        assert observed[1] == "TransportDispatchAuthority"
        assert observed[2] == "TransportDispatchAttemptBoundary"
        assert len(observed) == len(EXPECTED_DISPATCH_EXPORTS)
        assert len(set(observed)) == len(EXPECTED_DISPATCH_EXPORTS)

    def test_exports_exist(self) -> None:
        for name in EXPECTED_DISPATCH_EXPORTS:
            assert hasattr(dispatch_module, name), f"{name} missing from dispatch module"


class TestPackageExports:
    def test_package_all_is_builtin_tuple(self) -> None:
        assert type(egress_routing.__all__) is tuple

    def test_package_all_exact_order(self) -> None:
        assert egress_routing.__all__ == EXPECTED_PACKAGE_EXPORTS

    def test_package_all_iteration_and_indexing(self) -> None:
        observed = tuple(egress_routing.__all__)
        assert observed == EXPECTED_PACKAGE_EXPORTS
        assert observed[0] == "MODULE_ID"
        assert observed[51] == "ER06B_TASK_ID"
        assert observed[52] == "TransportAssignmentAuthority"
        assert observed[53] == "TransportAssignmentCommitmentBoundary"
        assert observed[54] == "ER06C_TASK_ID"
        assert observed[55] == "TransportDispatchAuthority"
        assert observed[56] == "TransportDispatchAttemptBoundary"
        assert observed[-1] == "EgressSyntheticFixture"

    def test_package_all_length_and_uniqueness(self) -> None:
        assert len(egress_routing.__all__) == len(EXPECTED_PACKAGE_EXPORTS)
        assert len(set(egress_routing.__all__)) == len(EXPECTED_PACKAGE_EXPORTS)

    def test_package_all_names_exist(self) -> None:
        for name in EXPECTED_PACKAGE_EXPORTS:
            assert hasattr(egress_routing, name), f"{name} missing from package"


class TestAuthorityMatrix:
    def test_exact_enum_matrix(self) -> None:
        assert EXPECTED_ENUM_PAIRS[TransportDispatchAuthority] == (
            ("EGRESS_ROUTING_SERVER", "EGRESS_ROUTING_SERVER"),
        )
        assert EXPECTED_ENUM_PAIRS[DispatchStatus] == (
            ("PENDING", "PENDING"),
            ("ATTEMPTED", "ATTEMPTED"),
            ("ACKNOWLEDGED", "ACKNOWLEDGED"),
            ("REJECTED", "REJECTED"),
            ("UNKNOWN", "UNKNOWN"),
            ("NOT_SENT", "NOT_SENT"),
            ("SENT", "SENT"),
        )

    def test_only_egress_server_dispatch_authority(self) -> None:
        assert len(TransportDispatchAuthority) == 1
        assert TransportDispatchAuthority.EGRESS_ROUTING_SERVER.value == "EGRESS_ROUTING_SERVER"


class TestBoundaryShape:
    def test_is_frozen_and_slotted_dataclass(self) -> None:
        assert is_dataclass(TransportDispatchAttemptBoundary)
        assert TransportDispatchAttemptBoundary.__dataclass_params__.frozen is True  # type: ignore[attr-defined]
        assert TransportDispatchAttemptBoundary.__dataclass_params__.slots is True  # type: ignore[attr-defined]

    def test_exact_field_order(self) -> None:
        assert (
            tuple(field.name for field in fields(TransportDispatchAttemptBoundary))
            == EXPECTED_BOUNDARY_FIELD_NAMES
        )

    def test_boundary_field_count(self) -> None:
        assert len(fields(TransportDispatchAttemptBoundary)) == len(EXPECTED_BOUNDARY_FIELD_NAMES)

    def test_dispatch_attempt_field_order_is_unchanged(self) -> None:
        assert (
            tuple(field.name for field in fields(DispatchAttempt))
            == EXPECTED_DISPATCH_ATTEMPT_FIELD_NAMES
        )

    def test_assignment_commitment_field_order_is_unchanged(self) -> None:
        assert (
            tuple(field.name for field in fields(TransportAssignmentCommitmentBoundary))
            == EXPECTED_ASSIGNMENT_COMMITMENT_FIELD_NAMES
        )

    def test_boundary_does_not_expose_forbidden_state(self) -> None:
        field_names = {field.name for field in fields(TransportDispatchAttemptBoundary)}
        forbidden = {
            "outcome_id",
            "transport_outcome",
            "safe_response_reference",
            "response_status",
            "response_body",
            "receipt_payload",
            "send_payload",
            "reconciliation_result",
            "retry_count",
            "retry_delay",
            "backoff",
            "duration",
            "timeout_seconds",
            "expires_at",
            "provider",
            "protocol",
            "host",
            "hostname",
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
        kwargs["authority"] = TransportAssignmentAuthority.EGRESS_ROUTING_SERVER
        with pytest.raises(ValueError):
            TransportDispatchAttemptBoundary(**kwargs)  # type: ignore[arg-type]

    def test_blank_boundary_id_rejected(self) -> None:
        kwargs = _boundary_kwargs_from_state(_build_valid_state())
        kwargs["boundary_id"] = " "
        with pytest.raises(ValueError):
            TransportDispatchAttemptBoundary(**kwargs)  # type: ignore[arg-type]

    def test_wrong_assignment_commitment_type_rejected(self) -> None:
        kwargs = _boundary_kwargs_from_state(_build_valid_state())
        kwargs["assignment_commitment"] = "invalid"
        with pytest.raises(ValueError):
            TransportDispatchAttemptBoundary(**kwargs)  # type: ignore[arg-type]

    def test_wrong_attempt_type_rejected(self) -> None:
        kwargs = _boundary_kwargs_from_state(_build_valid_state())
        kwargs["attempt"] = "invalid"
        with pytest.raises(ValueError):
            TransportDispatchAttemptBoundary(**kwargs)  # type: ignore[arg-type]

    def test_non_bool_dispatch_state_committed_rejected(self) -> None:
        kwargs = _boundary_kwargs_from_state(_build_valid_state())
        kwargs["dispatch_state_committed"] = 1
        with pytest.raises(ValueError):
            TransportDispatchAttemptBoundary(**kwargs)  # type: ignore[arg-type]

    def test_dispatch_state_committed_false_rejected(self) -> None:
        kwargs = _boundary_kwargs_from_state(_build_valid_state())
        kwargs["dispatch_state_committed"] = False
        with pytest.raises(ValueError):
            TransportDispatchAttemptBoundary(**kwargs)  # type: ignore[arg-type]

    def test_non_bool_new_dispatch_effect_authorized_rejected(self) -> None:
        kwargs = _boundary_kwargs_from_state(_build_valid_state())
        kwargs["new_dispatch_effect_authorized"] = 1
        with pytest.raises(ValueError):
            TransportDispatchAttemptBoundary(**kwargs)  # type: ignore[arg-type]

    def test_non_tuple_reason_codes_rejected(self) -> None:
        kwargs = _boundary_kwargs_from_state(_build_valid_state())
        kwargs["reason_codes"] = ["dispatch"]
        with pytest.raises(ValueError):
            TransportDispatchAttemptBoundary(**kwargs)  # type: ignore[arg-type]

    def test_empty_reason_codes_rejected(self) -> None:
        kwargs = _boundary_kwargs_from_state(_build_valid_state())
        kwargs["reason_codes"] = ()
        with pytest.raises(ValueError):
            TransportDispatchAttemptBoundary(**kwargs)  # type: ignore[arg-type]

    def test_non_tuple_evidence_reference_ids_rejected(self) -> None:
        kwargs = _boundary_kwargs_from_state(_build_valid_state())
        kwargs["evidence_reference_ids"] = ["evidence"]
        with pytest.raises(ValueError):
            TransportDispatchAttemptBoundary(**kwargs)  # type: ignore[arg-type]

    def test_empty_evidence_reference_ids_rejected(self) -> None:
        kwargs = _boundary_kwargs_from_state(_build_valid_state())
        kwargs["evidence_reference_ids"] = ()
        with pytest.raises(ValueError):
            TransportDispatchAttemptBoundary(**kwargs)  # type: ignore[arg-type]


class TestNestedValidation:
    def test_wrong_assignment_commitment_authority_rejected(self) -> None:
        state = _build_valid_state()
        commitment = state["assignment_commitment"]
        assert isinstance(commitment, TransportAssignmentCommitmentBoundary)
        _mutate(commitment, authority=TransportDispatchAuthority.EGRESS_ROUTING_SERVER)
        kwargs = _boundary_kwargs_from_state(state)
        with pytest.raises(ValueError):
            TransportDispatchAttemptBoundary(**kwargs)  # type: ignore[arg-type]

    def test_assignment_committed_false_rejected(self) -> None:
        state = _build_valid_state()
        commitment = state["assignment_commitment"]
        assert isinstance(commitment, TransportAssignmentCommitmentBoundary)
        _mutate(commitment, assignment_committed=False)
        kwargs = _boundary_kwargs_from_state(state)
        with pytest.raises(ValueError):
            TransportDispatchAttemptBoundary(**kwargs)  # type: ignore[arg-type]

    def test_non_authorizing_lease_rejected(self) -> None:
        state = _build_valid_state()
        lease_authorization = state["lease_authorization"]
        assert isinstance(lease_authorization, RouteLeaseAuthorizationBoundary)
        _mutate(lease_authorization, new_dispatch_authorized=False)
        kwargs = _boundary_kwargs_from_state(state)
        with pytest.raises(ValueError):
            TransportDispatchAttemptBoundary(**kwargs)  # type: ignore[arg-type]

    @pytest.mark.parametrize(
        "lease_status",
        (
            RouteLeaseStatus.REQUESTED,
            RouteLeaseStatus.REJECTED,
            RouteLeaseStatus.DISPATCHED,
            RouteLeaseStatus.IN_USE,
            RouteLeaseStatus.COMPLETED,
            RouteLeaseStatus.EXPIRED,
            RouteLeaseStatus.REVOKED,
            RouteLeaseStatus.AMBIGUOUS,
            RouteLeaseStatus.RECONCILIATION_REQUIRED,
            RouteLeaseStatus.FAILED,
        ),
    )
    def test_non_granted_lease_rejected(self, lease_status: RouteLeaseStatus) -> None:
        state = _build_valid_state()
        lease_authorization = state["lease_authorization"]
        assert isinstance(lease_authorization, RouteLeaseAuthorizationBoundary)
        _mutate(lease_authorization.lease, status=lease_status)
        kwargs = _boundary_kwargs_from_state(state)
        with pytest.raises(ValueError):
            TransportDispatchAttemptBoundary(**kwargs)  # type: ignore[arg-type]

    def test_restricted_lease_rejected(self) -> None:
        state = _build_valid_state()
        lease_authorization = state["lease_authorization"]
        assert isinstance(lease_authorization, RouteLeaseAuthorizationBoundary)
        _mutate(lease_authorization.lease, restriction_snapshot=RouteRestrictionStatus.RESTRICTED)
        kwargs = _boundary_kwargs_from_state(state)
        with pytest.raises(ValueError):
            TransportDispatchAttemptBoundary(**kwargs)  # type: ignore[arg-type]

    @pytest.mark.parametrize(
        "reconciliation_status",
        (
            RouteReconciliationStatus.REQUIRED,
            RouteReconciliationStatus.PENDING,
            RouteReconciliationStatus.REMAINS_AMBIGUOUS,
            RouteReconciliationStatus.MANUAL_REVIEW_REQUIRED,
        ),
    )
    def test_unresolved_lease_reconciliation_rejected(
        self, reconciliation_status: RouteReconciliationStatus
    ) -> None:
        state = _build_valid_state()
        lease_authorization = state["lease_authorization"]
        assert isinstance(lease_authorization, RouteLeaseAuthorizationBoundary)
        _mutate(lease_authorization, reconciliation_status=reconciliation_status)
        kwargs = _boundary_kwargs_from_state(state)
        with pytest.raises(ValueError):
            TransportDispatchAttemptBoundary(**kwargs)  # type: ignore[arg-type]

    @pytest.mark.parametrize(
        ("field_name", "value"),
        (
            ("assignment_id", "wrong-assignment"),
            ("lease_id", "wrong-lease"),
            ("route_id", "wrong-route"),
            ("agent_id", "wrong-agent"),
            ("correlation_id", "wrong-correlation"),
            ("causation_id", "wrong-causation"),
        ),
    )
    def test_attempt_linkage_mismatch_rejected(self, field_name: str, value: object) -> None:
        state = _build_valid_state()
        attempt = state["attempt"]
        assert isinstance(attempt, DispatchAttempt)
        _mutate(attempt, **{field_name: value})
        kwargs = _boundary_kwargs_from_state(state)
        with pytest.raises(ValueError):
            TransportDispatchAttemptBoundary(**kwargs)  # type: ignore[arg-type]

    @pytest.mark.parametrize("attempt_ordinal", (0, 2))
    def test_attempt_ordinal_must_be_one(self, attempt_ordinal: int) -> None:
        state = _build_valid_state()
        attempt = state["attempt"]
        assert isinstance(attempt, DispatchAttempt)
        _mutate(attempt, attempt_ordinal=attempt_ordinal)
        kwargs = _boundary_kwargs_from_state(state)
        with pytest.raises(ValueError):
            TransportDispatchAttemptBoundary(**kwargs)  # type: ignore[arg-type]

    def test_outcome_reference_non_none_rejected(self) -> None:
        with pytest.raises(ValueError):
            _build_valid_state(outcome_reference="outcome-01")

    def test_pending_authorization_false_rejected(self) -> None:
        with pytest.raises(ValueError):
            _build_valid_state(
                dispatch_status=DispatchStatus.PENDING,
                new_dispatch_effect_authorized=False,
            )

    @pytest.mark.parametrize(
        "dispatch_status",
        (
            DispatchStatus.ATTEMPTED,
            DispatchStatus.ACKNOWLEDGED,
            DispatchStatus.REJECTED,
            DispatchStatus.UNKNOWN,
            DispatchStatus.NOT_SENT,
            DispatchStatus.SENT,
        ),
    )
    def test_non_pending_authorization_true_rejected(self, dispatch_status: DispatchStatus) -> None:
        with pytest.raises(ValueError):
            _build_valid_state(
                dispatch_status=dispatch_status,
                new_dispatch_effect_authorized=True,
                reconciliation_required=dispatch_status is DispatchStatus.UNKNOWN,
            )

    def test_unknown_reconciliation_false_rejected(self) -> None:
        with pytest.raises(ValueError):
            _build_valid_state(
                dispatch_status=DispatchStatus.UNKNOWN,
                reconciliation_required=False,
                new_dispatch_effect_authorized=False,
            )

    @pytest.mark.parametrize(
        "dispatch_status",
        (
            DispatchStatus.PENDING,
            DispatchStatus.ATTEMPTED,
            DispatchStatus.ACKNOWLEDGED,
            DispatchStatus.REJECTED,
            DispatchStatus.NOT_SENT,
            DispatchStatus.SENT,
        ),
    )
    def test_non_unknown_reconciliation_true_rejected(
        self, dispatch_status: DispatchStatus
    ) -> None:
        with pytest.raises(ValueError):
            _build_valid_state(
                dispatch_status=dispatch_status,
                reconciliation_required=True,
                new_dispatch_effect_authorized=dispatch_status is DispatchStatus.PENDING,
            )


class TestStatusSemantics:
    def test_pending_allows_exact_first_dispatch_effect(self) -> None:
        boundary = _build_boundary(
            dispatch_status=DispatchStatus.PENDING,
            new_dispatch_effect_authorized=True,
            reconciliation_required=False,
        )
        assert boundary.dispatch_state_committed is True
        assert boundary.new_dispatch_effect_authorized is True
        assert boundary.attempt.dispatch_status is DispatchStatus.PENDING
        assert boundary.attempt.attempt_ordinal == 1
        assert boundary.attempt.outcome_reference is None
        assert boundary.attempt.reconciliation_required is False

    def test_attempted_blocks_second_dispatch(self) -> None:
        boundary = _build_boundary(dispatch_status=DispatchStatus.ATTEMPTED)
        assert boundary.attempt.dispatch_status is DispatchStatus.ATTEMPTED
        assert boundary.new_dispatch_effect_authorized is False
        assert boundary.attempt.outcome_reference is None
        assert boundary.attempt.reconciliation_required is False

    def test_acknowledged_proves_only_receipt_level_state(self) -> None:
        boundary = _build_boundary(dispatch_status=DispatchStatus.ACKNOWLEDGED)
        assert boundary.attempt.dispatch_status is DispatchStatus.ACKNOWLEDGED
        assert boundary.new_dispatch_effect_authorized is False
        assert boundary.attempt.outcome_reference is None
        assert boundary.attempt.reconciliation_required is False

    def test_rejected_does_not_authorize_retry(self) -> None:
        boundary = _build_boundary(dispatch_status=DispatchStatus.REJECTED)
        assert boundary.attempt.dispatch_status is DispatchStatus.REJECTED
        assert boundary.new_dispatch_effect_authorized is False
        assert boundary.attempt.outcome_reference is None
        assert boundary.attempt.reconciliation_required is False

    def test_unknown_requires_reconciliation_first(self) -> None:
        boundary = _build_boundary(
            dispatch_status=DispatchStatus.UNKNOWN,
            reconciliation_required=True,
            new_dispatch_effect_authorized=False,
        )
        assert boundary.attempt.dispatch_status is DispatchStatus.UNKNOWN
        assert boundary.new_dispatch_effect_authorized is False
        assert boundary.attempt.reconciliation_required is True
        assert boundary.attempt.outcome_reference is None

    def test_not_sent_does_not_automatically_authorize_retry(self) -> None:
        boundary = _build_boundary(dispatch_status=DispatchStatus.NOT_SENT)
        assert boundary.attempt.dispatch_status is DispatchStatus.NOT_SENT
        assert boundary.new_dispatch_effect_authorized is False
        assert boundary.attempt.outcome_reference is None
        assert boundary.attempt.reconciliation_required is False

    def test_sent_blocks_another_dispatch_and_does_not_prove_transport_success(self) -> None:
        boundary = _build_boundary(dispatch_status=DispatchStatus.SENT)
        assert boundary.attempt.dispatch_status is DispatchStatus.SENT
        assert boundary.new_dispatch_effect_authorized is False
        assert boundary.attempt.outcome_reference is None
        assert boundary.attempt.reconciliation_required is False
        assert "parser_success" not in {field.name for field in fields(DispatchAttempt)}
        assert "scan_success" not in {field.name for field in fields(DispatchAttempt)}


class TestLinkageSemantics:
    def test_assignment_and_nested_records_remain_exact(self) -> None:
        boundary = _build_boundary()
        assignment_commitment = boundary.assignment_commitment
        attempt = boundary.attempt
        lease = assignment_commitment.lease_authorization.lease

        assert assignment_commitment.assignment.assignment_id == attempt.assignment_id
        assert assignment_commitment.assignment.lease_id == attempt.lease_id
        assert assignment_commitment.assignment.route_id == attempt.route_id
        assert assignment_commitment.assignment.agent_id == attempt.agent_id
        assert assignment_commitment.assignment.correlation_id == attempt.correlation_id
        assert assignment_commitment.assignment.causation_id == attempt.causation_id
        assert assignment_commitment.lease_authorization.lease.status is RouteLeaseStatus.GRANTED
        assert lease.restriction_snapshot is RouteRestrictionStatus.NONE
        assert (
            assignment_commitment.lease_authorization.reconciliation_status
            in _RESOLVED_RECONCILIATION_STATUSES
        )

    def test_dispatch_boundary_does_not_mutate_inputs(self) -> None:
        state = _build_valid_state()
        assignment_before = state["assignment"]
        commitment_before = state["assignment_commitment"]
        lease_before = state["lease"]
        attempt_before = state["attempt"]
        assignment_snapshot = tuple(
            getattr(assignment_before, field.name) for field in fields(assignment_before)
        )
        commitment_snapshot = tuple(
            getattr(commitment_before, field.name) for field in fields(commitment_before)
        )
        lease_snapshot = tuple(getattr(lease_before, field.name) for field in fields(lease_before))
        attempt_snapshot = tuple(
            getattr(attempt_before, field.name) for field in fields(attempt_before)
        )

        boundary = TransportDispatchAttemptBoundary(**_boundary_kwargs_from_state(state))
        assert boundary.dispatch_state_committed is True
        assert assignment_snapshot == tuple(
            getattr(boundary.assignment_commitment.assignment, field.name)
            for field in fields(boundary.assignment_commitment.assignment)
        )
        assert commitment_snapshot == tuple(
            getattr(boundary.assignment_commitment, field.name)
            for field in fields(boundary.assignment_commitment)
        )
        assert lease_snapshot == tuple(
            getattr(boundary.assignment_commitment.lease_authorization.lease, field.name)
            for field in fields(boundary.assignment_commitment.lease_authorization.lease)
        )
        assert attempt_snapshot == tuple(
            getattr(boundary.attempt, field.name) for field in fields(boundary.attempt)
        )

    def test_outcome_remains_separate(self) -> None:
        boundary = _build_boundary()
        boundary_field_names = {field.name for field in fields(TransportDispatchAttemptBoundary)}
        attempt_field_names = {field.name for field in fields(DispatchAttempt)}
        assert "outcome_id" not in boundary_field_names
        assert "transport_outcome" not in boundary_field_names
        assert "safe_response_reference" not in boundary_field_names
        assert "response_status" not in boundary_field_names
        assert "safe_response_reference" not in attempt_field_names
        assert "response_status" not in attempt_field_names
        assert boundary.attempt.outcome_reference is None


class TestRegressionPreservation:
    def test_dispatch_status_matrix_is_unchanged(self) -> None:
        actual_pairs: tuple[tuple[str, str], ...] = tuple(
            (member.name, member.value) for member in DispatchStatus
        )
        assert actual_pairs == EXPECTED_ENUM_PAIRS[DispatchStatus]

    def test_dispatch_attempt_fields_are_unchanged(self) -> None:
        assert tuple(field.name for field in fields(DispatchAttempt)) == (
            EXPECTED_DISPATCH_ATTEMPT_FIELD_NAMES
        )

    def test_assignment_commitment_fields_are_unchanged(self) -> None:
        assert tuple(field.name for field in fields(TransportAssignmentCommitmentBoundary)) == (
            EXPECTED_ASSIGNMENT_COMMITMENT_FIELD_NAMES
        )

    def test_task_marker_occurs_exactly_once_in_dispatch_module(self) -> None:
        source = Path(dispatch_module.__file__).read_text()
        assert source.count(EXPECTED_TASK_ID) == 1
