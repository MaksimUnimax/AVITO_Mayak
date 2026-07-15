from __future__ import annotations

from dataclasses import fields, is_dataclass
from pathlib import Path
from typing import Any

import pytest

import mayak.modules.egress_routing.lease as lease_module
from mayak.modules import egress_routing
from mayak.modules.egress_routing import (
    ER06A_TASK_ID,
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
)

EXPECTED_TASK_ID = "".join(("ER-06A-", "ROUTE-LEASE-AUTHORIZATION-BOUNDARY-", "20260713-009"))

EXPECTED_LEASE_EXPORTS = (
    "ER06A_TASK_ID",
    "RouteLeaseAuthority",
    "RouteLeaseAuthorizationBoundary",
)

EXPECTED_ENUM_PAIRS = {
    RouteLeaseAuthority: (("EGRESS_ROUTING_SERVER", "EGRESS_ROUTING_SERVER"),),
}

EXPECTED_BOUNDARY_FIELD_NAMES = (
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


def _agent_kwargs(
    *,
    agent_id: str = "agent-01",
    environment_id: str = "env-01",
    lifecycle_status: AgentLifecycleStatus = AgentLifecycleStatus.READY,
) -> dict[str, Any]:
    return {
        "agent_id": agent_id,
        "agent_class": "LinuxReferenceStyleAgent",
        "environment_id": environment_id,
        "lifecycle_status": lifecycle_status,
        "trust_scope": ("egress", "safe-routing"),
        "source_release_reference": "release-20260712",
        "credential_reference": "opaque-credential-ref",
        "evidence_reference_ids": ("evidence-agent-01",),
    }


def _route_kwargs(
    *,
    route_id: str = "route-01",
    agent_id: str = "agent-01",
    environment_id: str = "env-01",
    route_family: RouteFamily = RouteFamily.LINUX_REFERENCE_STYLE_ROUTE,
    route_purpose_scope: tuple[str, ...] = ("search", "dispatch"),
    route_capability_ids: tuple[str, ...] = ("cap-01",),
    lifecycle_status: RouteLifecycleStatus = RouteLifecycleStatus.READY,
) -> dict[str, Any]:
    return {
        "route_id": route_id,
        "route_family": route_family,
        "environment_id": environment_id,
        "agent_id": agent_id,
        "purpose_scope": route_purpose_scope,
        "capability_ids": route_capability_ids,
        "lifecycle_status": lifecycle_status,
        "evidence_reference_ids": ("evidence-route-01",),
    }


def _registration_boundary_kwargs(
    *,
    agent_id: str = "agent-01",
    route_id: str = "route-01",
    environment_id: str = "env-01",
    route_purpose_scope: tuple[str, ...] = ("search", "dispatch"),
    route_capability_ids: tuple[str, ...] = ("cap-01",),
    route_family: RouteFamily = RouteFamily.LINUX_REFERENCE_STYLE_ROUTE,
    agent_lifecycle_status: AgentLifecycleStatus = AgentLifecycleStatus.READY,
    route_lifecycle_status: RouteLifecycleStatus = RouteLifecycleStatus.READY,
    agent_registration_status: AgentRegistrationStatus = AgentRegistrationStatus.REGISTERED,
    route_registration_status: RouteRegistrationStatus = RouteRegistrationStatus.REGISTERED,
    association_status: AgentRouteAssociationStatus = AgentRouteAssociationStatus.ACTIVE,
) -> dict[str, Any]:
    agent = EgressAgent(
        **_agent_kwargs(
            agent_id=agent_id,
            environment_id=environment_id,
            lifecycle_status=agent_lifecycle_status,
        )
    )
    route = EgressRoute(
        **_route_kwargs(
            route_id=route_id,
            agent_id=agent_id,
            environment_id=environment_id,
            route_family=route_family,
            route_purpose_scope=route_purpose_scope,
            route_capability_ids=route_capability_ids,
            lifecycle_status=route_lifecycle_status,
        )
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
        status=agent_registration_status,
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
        purpose_scope=route_purpose_scope,
        capability_ids=route_capability_ids,
        unsupported_classes=(),
        evidence_status=RouteEvidenceStatus.CURRENT,
        session_policy_status=SessionPolicyStatus.APPROVED_REFERENCE_ONLY,
        restriction_reference=None,
        selection_policy_reference=None,
        privacy_boundary_reference="privacy-boundary-01",
        status=route_registration_status,
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
        purpose_scope=route_purpose_scope,
        status=association_status,
        reason_codes=(),
        evidence_reference_ids=("evidence-association-01",),
    )
    return {
        "boundary_id": f"{route_id}-boundary",
        "agent": agent,
        "agent_registration": agent_registration,
        "route": route,
        "route_registration": route_registration,
        "association": association,
    }


def _candidate_kwargs(
    *,
    evaluation_id: str = "evaluation-01",
    request_reference: str = "request-01",
    requester_module: str = "07-egress-routing",
    environment_id: str = "env-01",
    purpose: str = "search",
    capability_scope: tuple[str, ...] = ("search",),
    policy_reference: str = "policy-01",
    route_id: str = "route-01",
    agent_id: str = "agent-01",
    status: RouteCandidateEligibilityStatus = RouteCandidateEligibilityStatus.ELIGIBLE,
    route_family: RouteFamily = RouteFamily.LINUX_REFERENCE_STYLE_ROUTE,
    route_purpose_scope: tuple[str, ...] = ("search", "dispatch"),
    route_capability_ids: tuple[str, ...] = ("cap-01",),
    capability_id: str = "cap-01",
    capability_operation_classes: tuple[str, ...] = ("search", "dispatch"),
    capability_evidence_status: RouteEvidenceStatus = RouteEvidenceStatus.CURRENT,
    agent_lifecycle_status: AgentLifecycleStatus = AgentLifecycleStatus.READY,
    route_lifecycle_status: RouteLifecycleStatus = RouteLifecycleStatus.READY,
    agent_registration_status: AgentRegistrationStatus = AgentRegistrationStatus.REGISTERED,
    route_registration_status: RouteRegistrationStatus = RouteRegistrationStatus.REGISTERED,
    association_status: AgentRouteAssociationStatus = AgentRouteAssociationStatus.ACTIVE,
    readiness_status: RouteReadinessStatus = RouteReadinessStatus.READY,
    health_status: RouteHealthStatus = RouteHealthStatus.READY,
    restriction_status: RouteRestrictionStatus = RouteRestrictionStatus.NONE,
    blocks_new_assignments: bool = False,
    reconciliation_status: RouteReconciliationStatus = RouteReconciliationStatus.NOT_REQUIRED,
    reason_codes: tuple[str, ...] = (),
    evidence_reference_ids: tuple[str, ...] = ("evidence-candidate-01",),
) -> dict[str, Any]:
    boundary = AgentRouteRegistrationBoundary(
        **_registration_boundary_kwargs(
            agent_id=agent_id,
            route_id=route_id,
            environment_id=environment_id,
            route_purpose_scope=route_purpose_scope,
            route_capability_ids=route_capability_ids,
            route_family=route_family,
            agent_lifecycle_status=agent_lifecycle_status,
            route_lifecycle_status=route_lifecycle_status,
            agent_registration_status=agent_registration_status,
            route_registration_status=route_registration_status,
            association_status=association_status,
        )
    )
    capability = RouteCapability(
        capability_id=capability_id,
        route_id=route_id,
        destination_scope=("destination-01",),
        operation_classes=capability_operation_classes,
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
        policy_reference=policy_reference,
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
    return {
        "evaluation_id": evaluation_id,
        "request_reference": request_reference,
        "requester_module": requester_module,
        "environment_id": environment_id,
        "purpose": purpose,
        "capability_scope": capability_scope,
        "policy_reference": policy_reference,
        "route_id": route_id,
        "agent_id": agent_id,
        "registration_boundary": boundary,
        "capability": capability,
        "readiness": readiness,
        "health": health,
        "restriction": restriction,
        "reconciliation_status": reconciliation_status,
        "status": status,
        "reason_codes": reason_codes,
        "evidence_reference_ids": evidence_reference_ids,
    }


def _decision_kwargs(
    *,
    status: RouteSelectionStatus,
    selected_route_id: str | None,
    candidate_route_ids: tuple[str, ...],
    rejected_route_ids: tuple[str, ...],
    request_reference: str = "request-01",
    reason_codes: tuple[str, ...] = ("selection-approved",),
    evidence_reference_ids: tuple[str, ...] = ("evidence-decision-01",),
    policy_reference: str = "policy-01",
) -> dict[str, Any]:
    return {
        "decision_id": "decision-01",
        "request_reference": request_reference,
        "status": status,
        "selected_route_id": selected_route_id,
        "candidate_route_ids": candidate_route_ids,
        "rejected_route_ids": rejected_route_ids,
        "reason_codes": reason_codes,
        "evidence_reference_ids": evidence_reference_ids,
        "policy_reference": policy_reference,
    }


def _selection_boundary_kwargs(
    *,
    candidate_evaluations: tuple[RouteCandidateEvaluation, ...],
    decision: RouteSelectionDecision,
    boundary_id: str = "boundary-01",
    authority: RouteSelectionAuthority = RouteSelectionAuthority.EGRESS_ROUTING_SERVER,
    request_reference: str = "request-01",
    requester_module: str = "07-egress-routing",
    environment_id: str = "env-01",
    purpose: str = "search",
    capability_scope: tuple[str, ...] = ("search",),
    policy_reference: str = "policy-01",
) -> dict[str, Any]:
    return {
        "boundary_id": boundary_id,
        "authority": authority,
        "request_reference": request_reference,
        "requester_module": requester_module,
        "environment_id": environment_id,
        "purpose": purpose,
        "capability_scope": capability_scope,
        "policy_reference": policy_reference,
        "candidate_evaluations": candidate_evaluations,
        "decision": decision,
    }


def _lease_kwargs(
    *,
    lease_id: str = "lease-01",
    route_id: str = "route-01",
    agent_id: str = "agent-01",
    requester_module: str = "07-egress-routing",
    purpose: str = "search",
    capability_scope: tuple[str, ...] = ("search",),
    status: RouteLeaseStatus = RouteLeaseStatus.GRANTED,
    restriction_snapshot: RouteRestrictionStatus = RouteRestrictionStatus.NONE,
    idempotency_key: str = "idempotency-01",
    semantic_fingerprint: str = "fingerprint-01",
    validity_reference: str = "validity-01",
    correlation_id: str = "correlation-01",
    causation_id: str = "causation-01",
) -> dict[str, Any]:
    return {
        "lease_id": lease_id,
        "route_id": route_id,
        "agent_id": agent_id,
        "requester_module": requester_module,
        "purpose": purpose,
        "capability_scope": capability_scope,
        "status": status,
        "idempotency_key": idempotency_key,
        "semantic_fingerprint": semantic_fingerprint,
        "validity_reference": validity_reference,
        "restriction_snapshot": restriction_snapshot,
        "correlation_id": correlation_id,
        "causation_id": causation_id,
    }


def _boundary_kwargs(
    *,
    selection: ServerRouteSelectionBoundary,
    selected_candidate: RouteCandidateEvaluation,
    lease: RouteLease,
    reconciliation_status: RouteReconciliationStatus = RouteReconciliationStatus.NOT_REQUIRED,
    new_dispatch_authorized: bool = True,
    boundary_id: str = "lease-boundary-01",
    authority: RouteLeaseAuthority = RouteLeaseAuthority.EGRESS_ROUTING_SERVER,
    request_reference: str = "request-01",
    requester_module: str = "07-egress-routing",
    environment_id: str = "env-01",
    purpose: str = "search",
    capability_scope: tuple[str, ...] = ("search",),
    reason_codes: tuple[str, ...] = ("lease-granted",),
    evidence_reference_ids: tuple[str, ...] = ("evidence-lease-01",),
) -> dict[str, Any]:
    return {
        "boundary_id": boundary_id,
        "authority": authority,
        "request_reference": request_reference,
        "requester_module": requester_module,
        "environment_id": environment_id,
        "purpose": purpose,
        "capability_scope": capability_scope,
        "selection": selection,
        "selected_candidate": selected_candidate,
        "lease": lease,
        "reconciliation_status": reconciliation_status,
        "new_dispatch_authorized": new_dispatch_authorized,
        "reason_codes": reason_codes,
        "evidence_reference_ids": evidence_reference_ids,
    }


def _build_valid_boundary(
    *,
    lease_status: RouteLeaseStatus = RouteLeaseStatus.GRANTED,
    restriction_snapshot: RouteRestrictionStatus = RouteRestrictionStatus.NONE,
    reconciliation_status: RouteReconciliationStatus = RouteReconciliationStatus.NOT_REQUIRED,
    new_dispatch_authorized: bool = True,
    route_id: str = "route-01",
    agent_id: str = "agent-01",
    request_reference: str = "request-01",
    requester_module: str = "07-egress-routing",
    environment_id: str = "env-01",
    purpose: str = "search",
    capability_scope: tuple[str, ...] = ("search",),
) -> RouteLeaseAuthorizationBoundary:
    candidate = RouteCandidateEvaluation(
        **_candidate_kwargs(
            request_reference=request_reference,
            requester_module=requester_module,
            environment_id=environment_id,
            purpose=purpose,
            capability_scope=capability_scope,
            route_id=route_id,
            agent_id=agent_id,
            status=RouteCandidateEligibilityStatus.ELIGIBLE,
        )
    )
    decision = RouteSelectionDecision(
        **_decision_kwargs(
            status=RouteSelectionStatus.SELECTED,
            selected_route_id=route_id,
            candidate_route_ids=(route_id,),
            rejected_route_ids=(),
            request_reference=request_reference,
        )
    )
    selection = ServerRouteSelectionBoundary(
        **_selection_boundary_kwargs(
            candidate_evaluations=(candidate,),
            decision=decision,
            request_reference=request_reference,
            requester_module=requester_module,
            environment_id=environment_id,
            purpose=purpose,
            capability_scope=capability_scope,
        )
    )
    lease = RouteLease(
        **_lease_kwargs(
            route_id=route_id,
            agent_id=agent_id,
            requester_module=requester_module,
            purpose=purpose,
            capability_scope=capability_scope,
            status=lease_status,
            restriction_snapshot=restriction_snapshot,
        )
    )
    return RouteLeaseAuthorizationBoundary(
        **_boundary_kwargs(
            selection=selection,
            selected_candidate=candidate,
            lease=lease,
            reconciliation_status=reconciliation_status,
            new_dispatch_authorized=new_dispatch_authorized,
            request_reference=request_reference,
            requester_module=requester_module,
            environment_id=environment_id,
            purpose=purpose,
            capability_scope=capability_scope,
        )
    )


class TestTaskId:
    def test_exact_task_id(self) -> None:
        assert ER06A_TASK_ID == EXPECTED_TASK_ID

    def test_task_id_count_in_lease_module(self) -> None:
        source = Path(lease_module.__file__).read_text()
        assert source.count(ER06A_TASK_ID) == 1


class TestLeaseModuleExports:
    def test_exact_exports(self) -> None:
        assert lease_module.__all__ == EXPECTED_LEASE_EXPORTS

    def test_all_names_exist(self) -> None:
        for name in EXPECTED_LEASE_EXPORTS:
            assert hasattr(lease_module, name), f"{name} not found in lease module"

    def test_task_id_is_in_exports(self) -> None:
        assert "ER06A_TASK_ID" in EXPECTED_LEASE_EXPORTS


class TestPackageExports:
    def test_package_all_is_tuple(self) -> None:
        assert type(egress_routing.__all__) is tuple

    def test_lease_exports_present(self) -> None:
        for name in EXPECTED_LEASE_EXPORTS:
            assert name in egress_routing.__all__, f"{name} not in package __all__"

    def test_package_all_exact_order(self) -> None:
        expected = (
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
    "ER02_TASK_ID",
    "EGRESS_SYNTHETIC_FIXTURE_IDS",
    "EGRESS_SYNTHETIC_FIXTURES",
    "EgressSyntheticFixture",
)
        assert egress_routing.__all__ == expected


class TestLeaseAuthorityMatrix:
    def test_exact_enum_pairs(self) -> None:
        for enum_cls, expected_pairs in EXPECTED_ENUM_PAIRS.items():
            actual_pairs = tuple((member.name, member.value) for member in enum_cls)
            assert actual_pairs == expected_pairs, f"{enum_cls.__name__} mismatch"

    def test_only_egress_server_authority(self) -> None:
        assert len(RouteLeaseAuthority) == 1
        assert RouteLeaseAuthority.EGRESS_ROUTING_SERVER.value == "EGRESS_ROUTING_SERVER"


class TestBoundaryRecord:
    def test_is_dataclass(self) -> None:
        assert is_dataclass(RouteLeaseAuthorizationBoundary)

    def test_frozen(self) -> None:
        assert RouteLeaseAuthorizationBoundary.__dataclass_params__.frozen is True  # type: ignore[attr-defined]

    def test_slots(self) -> None:
        assert RouteLeaseAuthorizationBoundary.__dataclass_params__.slots is True  # type: ignore[attr-defined]

    def test_exact_field_order(self) -> None:
        field_names = tuple(f.name for f in fields(RouteLeaseAuthorizationBoundary))
        assert field_names == EXPECTED_BOUNDARY_FIELD_NAMES

    def test_field_count(self) -> None:
        assert len(fields(RouteLeaseAuthorizationBoundary)) == 14


class TestMandatoryValidation:
    def test_boundary_id_must_be_non_blank(self) -> None:
        with pytest.raises(ValueError, match="boundary_id"):
            RouteLeaseAuthorizationBoundary(
                **_boundary_kwargs(
                    selection=_build_valid_boundary().selection,
                    selected_candidate=_build_valid_boundary().selected_candidate,
                    lease=_build_valid_boundary().lease,
                    boundary_id="",
                )
            )

    def test_request_reference_must_be_non_blank(self) -> None:
        with pytest.raises(ValueError, match="request_reference"):
            RouteLeaseAuthorizationBoundary(
                **_boundary_kwargs(
                    selection=_build_valid_boundary().selection,
                    selected_candidate=_build_valid_boundary().selected_candidate,
                    lease=_build_valid_boundary().lease,
                    request_reference="",
                )
            )

    def test_requester_module_must_be_non_blank(self) -> None:
        with pytest.raises(ValueError, match="requester_module"):
            RouteLeaseAuthorizationBoundary(
                **_boundary_kwargs(
                    selection=_build_valid_boundary().selection,
                    selected_candidate=_build_valid_boundary().selected_candidate,
                    lease=_build_valid_boundary().lease,
                    requester_module="",
                )
            )

    def test_environment_id_must_be_non_blank(self) -> None:
        with pytest.raises(ValueError, match="environment_id"):
            RouteLeaseAuthorizationBoundary(
                **_boundary_kwargs(
                    selection=_build_valid_boundary().selection,
                    selected_candidate=_build_valid_boundary().selected_candidate,
                    lease=_build_valid_boundary().lease,
                    environment_id="",
                )
            )

    def test_purpose_must_be_non_blank(self) -> None:
        with pytest.raises(ValueError, match="purpose"):
            RouteLeaseAuthorizationBoundary(
                **_boundary_kwargs(
                    selection=_build_valid_boundary().selection,
                    selected_candidate=_build_valid_boundary().selected_candidate,
                    lease=_build_valid_boundary().lease,
                    purpose="",
                )
            )

    def test_reason_codes_must_be_non_empty_tuple(self) -> None:
        with pytest.raises(ValueError, match="reason_codes"):
            RouteLeaseAuthorizationBoundary(
                **_boundary_kwargs(
                    selection=_build_valid_boundary().selection,
                    selected_candidate=_build_valid_boundary().selected_candidate,
                    lease=_build_valid_boundary().lease,
                    reason_codes=(),
                )
            )

    def test_evidence_reference_ids_must_be_non_empty_tuple(self) -> None:
        with pytest.raises(ValueError, match="evidence_reference_ids"):
            RouteLeaseAuthorizationBoundary(
                **_boundary_kwargs(
                    selection=_build_valid_boundary().selection,
                    selected_candidate=_build_valid_boundary().selected_candidate,
                    lease=_build_valid_boundary().lease,
                    evidence_reference_ids=(),
                )
            )


class TestTupleValidation:
    def test_non_tuple_capability_scope_rejected(self) -> None:
        with pytest.raises(ValueError, match="capability_scope"):
            RouteLeaseAuthorizationBoundary(
                **_boundary_kwargs(
                    selection=_build_valid_boundary().selection,
                    selected_candidate=_build_valid_boundary().selected_candidate,
                    lease=_build_valid_boundary().lease,
                    capability_scope=["search"],  # type: ignore[arg-type]
                )
            )

    def test_non_tuple_reason_codes_rejected(self) -> None:
        with pytest.raises(ValueError, match="reason_codes"):
            RouteLeaseAuthorizationBoundary(
                **_boundary_kwargs(
                    selection=_build_valid_boundary().selection,
                    selected_candidate=_build_valid_boundary().selected_candidate,
                    lease=_build_valid_boundary().lease,
                    reason_codes=["reason"],  # type: ignore[arg-type]
                )
            )

    def test_non_tuple_evidence_references_rejected(self) -> None:
        with pytest.raises(ValueError, match="evidence_reference_ids"):
            RouteLeaseAuthorizationBoundary(
                **_boundary_kwargs(
                    selection=_build_valid_boundary().selection,
                    selected_candidate=_build_valid_boundary().selected_candidate,
                    lease=_build_valid_boundary().lease,
                    evidence_reference_ids=["ev"],  # type: ignore[arg-type]
                )
            )


class TestBoolValidation:
    def test_non_bool_dispatch_authorization_rejected(self) -> None:
        with pytest.raises(ValueError, match="new_dispatch_authorized"):
            RouteLeaseAuthorizationBoundary(
                **_boundary_kwargs(
                    selection=_build_valid_boundary().selection,
                    selected_candidate=_build_valid_boundary().selected_candidate,
                    lease=_build_valid_boundary().lease,
                    new_dispatch_authorized="yes",  # type: ignore[arg-type]
                )
            )


class TestSelectionLinkage:
    def test_selection_must_be_server_route_selection_boundary(self) -> None:
        with pytest.raises(ValueError):
            RouteLeaseAuthorizationBoundary(
                **_boundary_kwargs(
                    selection="invalid",  # type: ignore[arg-type]
                    selected_candidate=_build_valid_boundary().selected_candidate,
                    lease=_build_valid_boundary().lease,
                )
            )

    def test_selection_status_must_be_selected(self) -> None:
        with pytest.raises(ValueError):
            valid = _build_valid_boundary()
            candidate = RouteCandidateEvaluation(
                **_candidate_kwargs(
                    request_reference=valid.request_reference,
                    requester_module=valid.requester_module,
                    environment_id=valid.environment_id,
                    purpose=valid.purpose,
                    capability_scope=valid.capability_scope,
                    route_id=valid.lease.route_id,
                    agent_id=valid.lease.agent_id,
                    status=RouteCandidateEligibilityStatus.ELIGIBLE,
                )
            )
            decision = RouteSelectionDecision(
                **_decision_kwargs(
                    status=RouteSelectionStatus.NO_ELIGIBLE_ROUTE,
                    selected_route_id=None,
                    candidate_route_ids=(valid.lease.route_id,),
                    rejected_route_ids=(valid.lease.route_id,),
                    request_reference=valid.request_reference,
                )
            )
            selection = ServerRouteSelectionBoundary(
                **_selection_boundary_kwargs(
                    candidate_evaluations=(candidate,),
                    decision=decision,
                    request_reference=valid.request_reference,
                    requester_module=valid.requester_module,
                    environment_id=valid.environment_id,
                    purpose=valid.purpose,
                    capability_scope=valid.capability_scope,
                )
            )
            RouteLeaseAuthorizationBoundary(
                **_boundary_kwargs(
                    selection=selection,
                    selected_candidate=candidate,
                    lease=valid.lease,
                )
            )

    def test_selection_request_mismatch(self) -> None:
        with pytest.raises(ValueError):
            valid = _build_valid_boundary()
            other_request = "wrong-request"
            candidate = RouteCandidateEvaluation(
                **_candidate_kwargs(
                    request_reference=other_request,
                    requester_module=valid.requester_module,
                    environment_id=valid.environment_id,
                    purpose=valid.purpose,
                    capability_scope=valid.capability_scope,
                    route_id=valid.lease.route_id,
                    agent_id=valid.lease.agent_id,
                )
            )
            decision = RouteSelectionDecision(
                **_decision_kwargs(
                    status=RouteSelectionStatus.SELECTED,
                    selected_route_id=valid.lease.route_id,
                    candidate_route_ids=(valid.lease.route_id,),
                    rejected_route_ids=(),
                    request_reference=other_request,
                )
            )
            selection = ServerRouteSelectionBoundary(
                **_selection_boundary_kwargs(
                    candidate_evaluations=(candidate,),
                    decision=decision,
                    request_reference=other_request,
                    requester_module=valid.requester_module,
                    environment_id=valid.environment_id,
                    purpose=valid.purpose,
                    capability_scope=valid.capability_scope,
                )
            )
            RouteLeaseAuthorizationBoundary(
                **_boundary_kwargs(
                    selection=selection,
                    selected_candidate=candidate,
                    lease=valid.lease,
                    request_reference=valid.request_reference,
                )
            )

    def test_selection_requester_mismatch(self) -> None:
        with pytest.raises(ValueError):
            valid = _build_valid_boundary()
            other_requester = "wrong-module"
            candidate = RouteCandidateEvaluation(
                **_candidate_kwargs(
                    request_reference=valid.request_reference,
                    requester_module=other_requester,
                    environment_id=valid.environment_id,
                    purpose=valid.purpose,
                    capability_scope=valid.capability_scope,
                    route_id=valid.lease.route_id,
                    agent_id=valid.lease.agent_id,
                )
            )
            decision = RouteSelectionDecision(
                **_decision_kwargs(
                    status=RouteSelectionStatus.SELECTED,
                    selected_route_id=valid.lease.route_id,
                    candidate_route_ids=(valid.lease.route_id,),
                    rejected_route_ids=(),
                    request_reference=valid.request_reference,
                )
            )
            selection = ServerRouteSelectionBoundary(
                **_selection_boundary_kwargs(
                    candidate_evaluations=(candidate,),
                    decision=decision,
                    request_reference=valid.request_reference,
                    requester_module=other_requester,
                    environment_id=valid.environment_id,
                    purpose=valid.purpose,
                    capability_scope=valid.capability_scope,
                )
            )
            RouteLeaseAuthorizationBoundary(
                **_boundary_kwargs(
                    selection=selection,
                    selected_candidate=candidate,
                    lease=valid.lease,
                    requester_module=valid.requester_module,
                )
            )

    def test_selection_environment_mismatch(self) -> None:
        with pytest.raises(ValueError):
            valid = _build_valid_boundary()
            other_env = "wrong-env"
            candidate = RouteCandidateEvaluation(
                **_candidate_kwargs(
                    request_reference=valid.request_reference,
                    requester_module=valid.requester_module,
                    environment_id=other_env,
                    purpose=valid.purpose,
                    capability_scope=valid.capability_scope,
                    route_id=valid.lease.route_id,
                    agent_id=valid.lease.agent_id,
                )
            )
            decision = RouteSelectionDecision(
                **_decision_kwargs(
                    status=RouteSelectionStatus.SELECTED,
                    selected_route_id=valid.lease.route_id,
                    candidate_route_ids=(valid.lease.route_id,),
                    rejected_route_ids=(),
                    request_reference=valid.request_reference,
                )
            )
            selection = ServerRouteSelectionBoundary(
                **_selection_boundary_kwargs(
                    candidate_evaluations=(candidate,),
                    decision=decision,
                    request_reference=valid.request_reference,
                    requester_module=valid.requester_module,
                    environment_id=other_env,
                    purpose=valid.purpose,
                    capability_scope=valid.capability_scope,
                )
            )
            RouteLeaseAuthorizationBoundary(
                **_boundary_kwargs(
                    selection=selection,
                    selected_candidate=candidate,
                    lease=valid.lease,
                    environment_id=valid.environment_id,
                )
            )

    def test_selection_purpose_mismatch(self) -> None:
        with pytest.raises(ValueError):
            valid = _build_valid_boundary()
            other_purpose = "wrong-purpose"
            candidate = RouteCandidateEvaluation(
                **_candidate_kwargs(
                    request_reference=valid.request_reference,
                    requester_module=valid.requester_module,
                    environment_id=valid.environment_id,
                    purpose=other_purpose,
                    capability_scope=valid.capability_scope,
                    route_id=valid.lease.route_id,
                    agent_id=valid.lease.agent_id,
                )
            )
            decision = RouteSelectionDecision(
                **_decision_kwargs(
                    status=RouteSelectionStatus.SELECTED,
                    selected_route_id=valid.lease.route_id,
                    candidate_route_ids=(valid.lease.route_id,),
                    rejected_route_ids=(),
                    request_reference=valid.request_reference,
                )
            )
            selection = ServerRouteSelectionBoundary(
                **_selection_boundary_kwargs(
                    candidate_evaluations=(candidate,),
                    decision=decision,
                    request_reference=valid.request_reference,
                    requester_module=valid.requester_module,
                    environment_id=valid.environment_id,
                    purpose=other_purpose,
                    capability_scope=valid.capability_scope,
                )
            )
            RouteLeaseAuthorizationBoundary(
                **_boundary_kwargs(
                    selection=selection,
                    selected_candidate=candidate,
                    lease=valid.lease,
                    purpose=valid.purpose,
                )
            )

    def test_selection_capability_mismatch(self) -> None:
        with pytest.raises(ValueError):
            valid = _build_valid_boundary()
            other_cap = ("wrong-cap",)
            candidate = RouteCandidateEvaluation(
                **_candidate_kwargs(
                    request_reference=valid.request_reference,
                    requester_module=valid.requester_module,
                    environment_id=valid.environment_id,
                    purpose=valid.purpose,
                    capability_scope=other_cap,
                    route_id=valid.lease.route_id,
                    agent_id=valid.lease.agent_id,
                )
            )
            decision = RouteSelectionDecision(
                **_decision_kwargs(
                    status=RouteSelectionStatus.SELECTED,
                    selected_route_id=valid.lease.route_id,
                    candidate_route_ids=(valid.lease.route_id,),
                    rejected_route_ids=(),
                    request_reference=valid.request_reference,
                )
            )
            selection = ServerRouteSelectionBoundary(
                **_selection_boundary_kwargs(
                    candidate_evaluations=(candidate,),
                    decision=decision,
                    request_reference=valid.request_reference,
                    requester_module=valid.requester_module,
                    environment_id=valid.environment_id,
                    purpose=valid.purpose,
                    capability_scope=other_cap,
                )
            )
            RouteLeaseAuthorizationBoundary(
                **_boundary_kwargs(
                    selection=selection,
                    selected_candidate=candidate,
                    lease=valid.lease,
                    capability_scope=valid.capability_scope,
                )
            )


class TestSelectedCandidateLinkage:
    def test_selected_candidate_must_be_in_selection(self) -> None:
        with pytest.raises(ValueError):
            valid = _build_valid_boundary()
            other_candidate = RouteCandidateEvaluation(
                **_candidate_kwargs(
                    evaluation_id="other-evaluation",
                    request_reference=valid.request_reference,
                    requester_module=valid.requester_module,
                    environment_id=valid.environment_id,
                    purpose=valid.purpose,
                    capability_scope=valid.capability_scope,
                    route_id=valid.lease.route_id,
                    agent_id=valid.lease.agent_id,
                )
            )
            RouteLeaseAuthorizationBoundary(
                **_boundary_kwargs(
                    selection=valid.selection,
                    selected_candidate=other_candidate,
                    lease=valid.lease,
                )
            )

    def test_selected_candidate_must_be_eligible(self) -> None:
        with pytest.raises(ValueError):
            valid = _build_valid_boundary()
            candidate = valid.selection.candidate_evaluations[0]
            _mutate(candidate, status=RouteCandidateEligibilityStatus.POLICY_REJECTED)
            _mutate(candidate, reason_codes=("policy-rejected",))
            RouteLeaseAuthorizationBoundary(
                **_boundary_kwargs(
                    selection=valid.selection,
                    selected_candidate=candidate,
                    lease=valid.lease,
                )
            )

    def test_selected_candidate_route_mismatch(self) -> None:
        with pytest.raises(ValueError):
            valid = _build_valid_boundary()
            candidate = valid.selection.candidate_evaluations[0]
            _mutate(candidate, route_id="other-route")
            RouteLeaseAuthorizationBoundary(
                **_boundary_kwargs(
                    selection=valid.selection,
                    selected_candidate=candidate,
                    lease=valid.lease,
                )
            )

    def test_two_eligible_candidates_rejected(self) -> None:
        with pytest.raises(ValueError):
            valid = _build_valid_boundary()
            candidate1 = valid.selection.candidate_evaluations[0]
            candidate2 = RouteCandidateEvaluation(
                **_candidate_kwargs(
                    evaluation_id="eval-02",
                    request_reference=valid.request_reference,
                    requester_module=valid.requester_module,
                    environment_id=valid.environment_id,
                    purpose=valid.purpose,
                    capability_scope=valid.capability_scope,
                    route_id="route-02",
                    agent_id="agent-02",
                )
            )
            decision = RouteSelectionDecision(
                **_decision_kwargs(
                    status=RouteSelectionStatus.SELECTED,
                    selected_route_id=valid.lease.route_id,
                    candidate_route_ids=(valid.lease.route_id, "route-02"),
                    rejected_route_ids=(),
                    request_reference=valid.request_reference,
                )
            )
            selection = ServerRouteSelectionBoundary(
                **_selection_boundary_kwargs(
                    candidate_evaluations=(candidate1, candidate2),
                    decision=decision,
                    request_reference=valid.request_reference,
                    requester_module=valid.requester_module,
                    environment_id=valid.environment_id,
                    purpose=valid.purpose,
                    capability_scope=valid.capability_scope,
                )
            )
            RouteLeaseAuthorizationBoundary(
                **_boundary_kwargs(
                    selection=selection,
                    selected_candidate=candidate1,
                    lease=valid.lease,
                )
            )


class TestLeaseLinkage:
    def test_lease_route_mismatch(self) -> None:
        with pytest.raises(ValueError):
            valid = _build_valid_boundary()
            lease = RouteLease(
                **_lease_kwargs(
                    route_id="wrong-route",
                    agent_id=valid.lease.agent_id,
                    requester_module=valid.requester_module,
                    purpose=valid.purpose,
                    capability_scope=valid.capability_scope,
                )
            )
            RouteLeaseAuthorizationBoundary(
                **_boundary_kwargs(
                    selection=valid.selection,
                    selected_candidate=valid.selected_candidate,
                    lease=lease,
                )
            )

    def test_lease_agent_mismatch(self) -> None:
        with pytest.raises(ValueError):
            valid = _build_valid_boundary()
            lease = RouteLease(
                **_lease_kwargs(
                    route_id=valid.lease.route_id,
                    agent_id="wrong-agent",
                    requester_module=valid.requester_module,
                    purpose=valid.purpose,
                    capability_scope=valid.capability_scope,
                )
            )
            RouteLeaseAuthorizationBoundary(
                **_boundary_kwargs(
                    selection=valid.selection,
                    selected_candidate=valid.selected_candidate,
                    lease=lease,
                )
            )

    def test_lease_requester_mismatch(self) -> None:
        with pytest.raises(ValueError):
            valid = _build_valid_boundary()
            lease = RouteLease(
                **_lease_kwargs(
                    route_id=valid.lease.route_id,
                    agent_id=valid.lease.agent_id,
                    requester_module="wrong-module",
                    purpose=valid.purpose,
                    capability_scope=valid.capability_scope,
                )
            )
            RouteLeaseAuthorizationBoundary(
                **_boundary_kwargs(
                    selection=valid.selection,
                    selected_candidate=valid.selected_candidate,
                    lease=lease,
                )
            )

    def test_lease_purpose_mismatch(self) -> None:
        with pytest.raises(ValueError):
            valid = _build_valid_boundary()
            lease = RouteLease(
                **_lease_kwargs(
                    route_id=valid.lease.route_id,
                    agent_id=valid.lease.agent_id,
                    requester_module=valid.requester_module,
                    purpose="wrong-purpose",
                    capability_scope=valid.capability_scope,
                )
            )
            RouteLeaseAuthorizationBoundary(
                **_boundary_kwargs(
                    selection=valid.selection,
                    selected_candidate=valid.selected_candidate,
                    lease=lease,
                )
            )

    def test_lease_capability_mismatch(self) -> None:
        with pytest.raises(ValueError):
            valid = _build_valid_boundary()
            lease = RouteLease(
                **_lease_kwargs(
                    route_id=valid.lease.route_id,
                    agent_id=valid.lease.agent_id,
                    requester_module=valid.requester_module,
                    purpose=valid.purpose,
                    capability_scope=("wrong-cap",),
                )
            )
            RouteLeaseAuthorizationBoundary(
                **_boundary_kwargs(
                    selection=valid.selection,
                    selected_candidate=valid.selected_candidate,
                    lease=lease,
                )
            )


class TestLifecycleSemantics:
    def test_requested_no_authorization(self) -> None:
        boundary = _build_valid_boundary(
            lease_status=RouteLeaseStatus.REQUESTED,
            new_dispatch_authorized=False,
        )
        assert boundary.new_dispatch_authorized is False

    def test_rejected_no_authorization(self) -> None:
        boundary = _build_valid_boundary(
            lease_status=RouteLeaseStatus.REJECTED,
            new_dispatch_authorized=False,
        )
        assert boundary.new_dispatch_authorized is False

    def test_granted_authorizes_dispatch(self) -> None:
        boundary = _build_valid_boundary(
            lease_status=RouteLeaseStatus.GRANTED,
            new_dispatch_authorized=True,
        )
        assert boundary.new_dispatch_authorized is True

    def test_dispatched_no_new_dispatch(self) -> None:
        boundary = _build_valid_boundary(
            lease_status=RouteLeaseStatus.DISPATCHED,
            new_dispatch_authorized=False,
        )
        assert boundary.new_dispatch_authorized is False

    def test_in_use_no_new_dispatch(self) -> None:
        boundary = _build_valid_boundary(
            lease_status=RouteLeaseStatus.IN_USE,
            new_dispatch_authorized=False,
        )
        assert boundary.new_dispatch_authorized is False

    def test_completed_no_new_dispatch(self) -> None:
        boundary = _build_valid_boundary(
            lease_status=RouteLeaseStatus.COMPLETED,
            new_dispatch_authorized=False,
        )
        assert boundary.new_dispatch_authorized is False

    def test_expired_blocks_dispatch(self) -> None:
        boundary = _build_valid_boundary(
            lease_status=RouteLeaseStatus.EXPIRED,
            new_dispatch_authorized=False,
        )
        assert boundary.new_dispatch_authorized is False

    def test_revoked_blocks_dispatch(self) -> None:
        boundary = _build_valid_boundary(
            lease_status=RouteLeaseStatus.REVOKED,
            new_dispatch_authorized=False,
        )
        assert boundary.new_dispatch_authorized is False

    def test_ambiguous_blocks_dispatch(self) -> None:
        boundary = _build_valid_boundary(
            lease_status=RouteLeaseStatus.AMBIGUOUS,
            new_dispatch_authorized=False,
            reconciliation_status=RouteReconciliationStatus.REQUIRED,
        )
        assert boundary.new_dispatch_authorized is False

    def test_reconciliation_required_blocks_dispatch(self) -> None:
        boundary = _build_valid_boundary(
            lease_status=RouteLeaseStatus.RECONCILIATION_REQUIRED,
            new_dispatch_authorized=False,
            reconciliation_status=RouteReconciliationStatus.PENDING,
        )
        assert boundary.new_dispatch_authorized is False

    def test_failed_blocks_dispatch(self) -> None:
        boundary = _build_valid_boundary(
            lease_status=RouteLeaseStatus.FAILED,
            new_dispatch_authorized=False,
        )
        assert boundary.new_dispatch_authorized is False


class TestAuthorizationEquivalence:
    def test_granted_authorization_false_rejected(self) -> None:
        with pytest.raises(ValueError, match="GRANTED must authorize dispatch"):
            _build_valid_boundary(
                lease_status=RouteLeaseStatus.GRANTED,
                new_dispatch_authorized=False,
            )

    def test_granted_with_unresolved_reconciliation_rejected(self) -> None:
        with pytest.raises(ValueError, match="GRANTED requires resolved reconciliation"):
            _build_valid_boundary(
                lease_status=RouteLeaseStatus.GRANTED,
                new_dispatch_authorized=True,
                reconciliation_status=RouteReconciliationStatus.REQUIRED,
            )

    def test_granted_with_restricted_snapshot_rejected(self) -> None:
        with pytest.raises(ValueError, match="GRANTED requires NONE restriction"):
            _build_valid_boundary(
                lease_status=RouteLeaseStatus.GRANTED,
                new_dispatch_authorized=True,
                restriction_snapshot=RouteRestrictionStatus.RESTRICTED,
            )

    def test_non_granted_authorization_true_rejected(self) -> None:
        with pytest.raises(ValueError, match="DISPATCHED must not authorize new dispatch"):
            _build_valid_boundary(
                lease_status=RouteLeaseStatus.DISPATCHED,
                new_dispatch_authorized=True,
            )

    def test_dispatched_with_restricted_snapshot_rejected(self) -> None:
        with pytest.raises(ValueError, match="DISPATCHED requires NONE restriction"):
            _build_valid_boundary(
                lease_status=RouteLeaseStatus.DISPATCHED,
                new_dispatch_authorized=False,
                restriction_snapshot=RouteRestrictionStatus.RESTRICTED,
            )

    def test_in_use_with_restricted_snapshot_rejected(self) -> None:
        with pytest.raises(ValueError, match="IN_USE requires NONE restriction"):
            _build_valid_boundary(
                lease_status=RouteLeaseStatus.IN_USE,
                new_dispatch_authorized=False,
                restriction_snapshot=RouteRestrictionStatus.QUARANTINED,
            )

    def test_completed_with_restricted_snapshot_rejected(self) -> None:
        with pytest.raises(ValueError, match="COMPLETED requires NONE restriction"):
            _build_valid_boundary(
                lease_status=RouteLeaseStatus.COMPLETED,
                new_dispatch_authorized=False,
                restriction_snapshot=RouteRestrictionStatus.SUSPENDED,
            )

    def test_ambiguous_with_resolved_reconciliation_rejected(self) -> None:
        with pytest.raises(ValueError, match="AMBIGUOUS requires unresolved reconciliation"):
            _build_valid_boundary(
                lease_status=RouteLeaseStatus.AMBIGUOUS,
                new_dispatch_authorized=False,
                reconciliation_status=RouteReconciliationStatus.NOT_REQUIRED,
            )

    def test_reconciliation_required_with_resolved_reconciliation_rejected(self) -> None:
        with pytest.raises(ValueError, match="RECONCILIATION_REQUIRED requires unresolved"):
            _build_valid_boundary(
                lease_status=RouteLeaseStatus.RECONCILIATION_REQUIRED,
                new_dispatch_authorized=False,
                reconciliation_status=RouteReconciliationStatus.RESOLVED_SENT,
            )


class TestRouteLeaseStatusMatrix:
    def test_route_lease_status_unchanged(self) -> None:
        expected = (
            ("REQUESTED", "REQUESTED"),
            ("REJECTED", "REJECTED"),
            ("GRANTED", "GRANTED"),
            ("DISPATCHED", "DISPATCHED"),
            ("IN_USE", "IN_USE"),
            ("COMPLETED", "COMPLETED"),
            ("EXPIRED", "EXPIRED"),
            ("REVOKED", "REVOKED"),
            ("AMBIGUOUS", "AMBIGUOUS"),
            ("RECONCILIATION_REQUIRED", "RECONCILIATION_REQUIRED"),
            ("FAILED", "FAILED"),
        )
        actual = tuple((m.name, m.value) for m in RouteLeaseStatus)
        assert actual == expected


class TestRouteLeaseFields:
    def test_route_lease_fields_unchanged(self) -> None:
        expected = (
            "lease_id",
            "route_id",
            "agent_id",
            "requester_module",
            "purpose",
            "capability_scope",
            "status",
            "idempotency_key",
            "semantic_fingerprint",
            "validity_reference",
            "restriction_snapshot",
            "correlation_id",
            "causation_id",
        )
        actual = tuple(f.name for f in fields(RouteLease))
        assert actual == expected


class TestRegressionPreservation:
    def test_er02_task_id_in_fixtures(self) -> None:
        source = Path(egress_routing.fixtures.__file__).read_text()
        assert "ER-02-" in source

    def test_er03_task_id_in_registration(self) -> None:
        source = Path(egress_routing.registration.__file__).read_text()
        assert "ER-03-" in source

    def test_er05a_task_id_in_selection(self) -> None:
        source = Path(egress_routing.selection.__file__).read_text()
        assert "ER-05A-" in source

    def test_er05b_task_id_in_fallback(self) -> None:
        source = Path(egress_routing.fallback.__file__).read_text()
        assert "ER-05B-" in source

    def test_er06a_task_id_in_lease(self) -> None:
        source = Path(egress_routing.lease.__file__).read_text()
        assert "ER-06A-" in source

    def test_fixture_count(self) -> None:
        from mayak.modules.egress_routing import EGRESS_SYNTHETIC_FIXTURES

        assert len(EGRESS_SYNTHETIC_FIXTURES) == 34
