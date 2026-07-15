from __future__ import annotations

from dataclasses import fields, is_dataclass
from pathlib import Path
from typing import Any

import pytest

import mayak.modules.egress_routing.selection as selection_module
from mayak.modules import egress_routing
from mayak.modules.egress_routing import (
    ER05A_TASK_ID,
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

EXPECTED_TASK_ID = "".join(("ER-05A-", "SERVER-ROUTE-SELECTION-BOUNDARY-", "20260712-007"))

EXPECTED_SELECTION_EXPORTS = (
    "ER05A_TASK_ID",
    "RouteSelectionAuthority",
    "RouteCandidateEligibilityStatus",
    "RouteCandidateEvaluation",
    "ServerRouteSelectionBoundary",
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
    "ER02_TASK_ID",
    "EGRESS_SYNTHETIC_FIXTURE_IDS",
    "EGRESS_SYNTHETIC_FIXTURES",
    "EgressSyntheticFixture",
)

EXPECTED_ENUM_PAIRS = {
    RouteSelectionAuthority: (("EGRESS_ROUTING_SERVER", "EGRESS_ROUTING_SERVER"),),
    RouteCandidateEligibilityStatus: (
        ("ELIGIBLE", "ELIGIBLE"),
        ("REGISTRATION_BLOCKED", "REGISTRATION_BLOCKED"),
        ("PURPOSE_MISMATCH", "PURPOSE_MISMATCH"),
        ("CAPABILITY_MISMATCH", "CAPABILITY_MISMATCH"),
        ("READINESS_BLOCKED", "READINESS_BLOCKED"),
        ("HEALTH_BLOCKED", "HEALTH_BLOCKED"),
        ("RESTRICTED", "RESTRICTED"),
        ("EVIDENCE_STALE", "EVIDENCE_STALE"),
        ("RECONCILIATION_BLOCKED", "RECONCILIATION_BLOCKED"),
        ("POLICY_REJECTED", "POLICY_REJECTED"),
        ("CONFLICT", "CONFLICT"),
        ("AMBIGUOUS", "AMBIGUOUS"),
    ),
}

EXPECTED_FIELD_NAMES = {
    RouteCandidateEvaluation: (
        "evaluation_id",
        "request_reference",
        "requester_module",
        "environment_id",
        "purpose",
        "capability_scope",
        "policy_reference",
        "route_id",
        "agent_id",
        "registration_boundary",
        "capability",
        "readiness",
        "health",
        "restriction",
        "reconciliation_status",
        "status",
        "reason_codes",
        "evidence_reference_ids",
    ),
    ServerRouteSelectionBoundary: (
        "boundary_id",
        "authority",
        "request_reference",
        "requester_module",
        "environment_id",
        "purpose",
        "capability_scope",
        "policy_reference",
        "candidate_evaluations",
        "decision",
    ),
}


def _mutate(record: object, **changes: object) -> None:
    for field_name, value in changes.items():
        object.__setattr__(record, field_name, value)


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
    status: RouteCandidateEligibilityStatus = RouteCandidateEligibilityStatus.ELIGIBLE,
    reason_codes: tuple[str, ...] = (),
    evidence_reference_ids: tuple[str, ...] = ("evidence-candidate-01",),
) -> dict[str, Any]:
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
        purpose_scope=route_purpose_scope,
        capability_ids=route_capability_ids,
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
    boundary = AgentRouteRegistrationBoundary(
        boundary_id=f"{route_id}-boundary",
        agent=agent,
        agent_registration=agent_registration,
        route=route,
        route_registration=route_registration,
        association=association,
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


def _boundary_kwargs(
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


def _candidate_for_route(
    route_id: str,
    agent_id: str,
    *,
    status: RouteCandidateEligibilityStatus = RouteCandidateEligibilityStatus.ELIGIBLE,
    reason_codes: tuple[str, ...] = (),
    evidence_reference_ids: tuple[str, ...] = ("evidence-candidate-01",),
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
    route_family: RouteFamily = RouteFamily.LINUX_REFERENCE_STYLE_ROUTE,
    capability_scope: tuple[str, ...] = ("search",),
    route_purpose_scope: tuple[str, ...] = ("search", "dispatch"),
    route_capability_ids: tuple[str, ...] = ("cap-01",),
    capability_id: str = "cap-01",
    purpose: str = "search",
    request_reference: str = "request-01",
    requester_module: str = "07-egress-routing",
    environment_id: str = "env-01",
    policy_reference: str = "policy-01",
) -> RouteCandidateEvaluation:
    return RouteCandidateEvaluation(
        **_candidate_kwargs(
            evaluation_id=f"{route_id}-evaluation",
            request_reference=request_reference,
            requester_module=requester_module,
            environment_id=environment_id,
            purpose=purpose,
            capability_scope=capability_scope,
            policy_reference=policy_reference,
            route_id=route_id,
            agent_id=agent_id,
            route_family=route_family,
            route_purpose_scope=route_purpose_scope,
            route_capability_ids=route_capability_ids,
            capability_id=capability_id,
            capability_evidence_status=capability_evidence_status,
            agent_lifecycle_status=agent_lifecycle_status,
            route_lifecycle_status=route_lifecycle_status,
            agent_registration_status=agent_registration_status,
            route_registration_status=route_registration_status,
            association_status=association_status,
            readiness_status=readiness_status,
            health_status=health_status,
            restriction_status=restriction_status,
            blocks_new_assignments=blocks_new_assignments,
            reconciliation_status=reconciliation_status,
            status=status,
            reason_codes=reason_codes,
            evidence_reference_ids=evidence_reference_ids,
        )
    )


def _selected_boundary() -> ServerRouteSelectionBoundary:
    candidate_a = _candidate_for_route(
        "route-01",
        "agent-01",
        status=RouteCandidateEligibilityStatus.ELIGIBLE,
        reason_codes=(),
        evidence_reference_ids=("evidence-candidate-01",),
        capability_id="cap-01",
        route_capability_ids=("cap-01",),
    )
    candidate_b = _candidate_for_route(
        "route-02",
        "agent-02",
        status=RouteCandidateEligibilityStatus.POLICY_REJECTED,
        reason_codes=("policy-blocked",),
        evidence_reference_ids=("evidence-candidate-02",),
        capability_id="cap-02",
        route_capability_ids=("cap-02",),
    )
    decision = RouteSelectionDecision(
        **_decision_kwargs(
            status=RouteSelectionStatus.SELECTED,
            selected_route_id="route-01",
            candidate_route_ids=("route-01", "route-02"),
            rejected_route_ids=("route-02",),
        )
    )
    return ServerRouteSelectionBoundary(
        **_boundary_kwargs(
            candidate_evaluations=(candidate_a, candidate_b),
            decision=decision,
        )
    )


def _non_selected_boundary_kwargs() -> dict[str, Any]:
    candidate = _candidate_for_route(
        "route-01",
        "agent-01",
        status=RouteCandidateEligibilityStatus.POLICY_REJECTED,
        reason_codes=("policy-blocked",),
        evidence_reference_ids=("evidence-candidate-01",),
    )
    decision = RouteSelectionDecision(
        **_decision_kwargs(
            status=RouteSelectionStatus.NO_ELIGIBLE_ROUTE,
            selected_route_id=None,
            candidate_route_ids=("route-01",),
            rejected_route_ids=("route-01",),
            reason_codes=("no-route",),
            evidence_reference_ids=("evidence-decision-01",),
        )
    )
    return _boundary_kwargs(candidate_evaluations=(candidate,), decision=decision)


def test_selection_task_id_and_package_exports_are_exact() -> None:
    assert ER05A_TASK_ID == EXPECTED_TASK_ID
    assert selection_module.ER05A_TASK_ID == EXPECTED_TASK_ID
    assert type(selection_module.__all__) is tuple
    assert selection_module.__all__ == EXPECTED_SELECTION_EXPORTS
    assert tuple(selection_module.__all__) == EXPECTED_SELECTION_EXPORTS
    assert len(selection_module.__all__) == len(EXPECTED_SELECTION_EXPORTS)
    assert len(set(selection_module.__all__)) == len(EXPECTED_SELECTION_EXPORTS)
    assert egress_routing.__all__ == EXPECTED_PACKAGE_EXPORTS
    assert tuple(egress_routing.__all__) == EXPECTED_PACKAGE_EXPORTS
    assert type(egress_routing.__all__) is tuple
    assert len(egress_routing.__all__) == len(EXPECTED_PACKAGE_EXPORTS)
    assert len(set(egress_routing.__all__)) == len(EXPECTED_PACKAGE_EXPORTS)
    assert all(hasattr(selection_module, name) for name in EXPECTED_SELECTION_EXPORTS)
    assert all(hasattr(egress_routing, name) for name in EXPECTED_PACKAGE_EXPORTS)

    repo_root = Path(__file__).resolve().parents[2]
    changed_files = (
        repo_root / "src/mayak/modules/egress_routing/__init__.py",
        repo_root / "src/mayak/modules/egress_routing/selection.py",
        repo_root / "tests/contract/test_egress_routing_contracts.py",
        repo_root / "tests/contract/test_egress_routing_registration_contracts.py",
        repo_root / "tests/contract/test_egress_routing_selection_contracts.py",
        repo_root / "tests/unit/test_egress_routing_selection_semantics.py",
        repo_root / "tests/architecture/test_egress_routing_boundaries.py",
    )
    task_id_count = sum(path.read_text().count(EXPECTED_TASK_ID) for path in changed_files)
    assert task_id_count == 1


@pytest.mark.parametrize(
    ("enum_cls", "expected_pairs"),
    list(EXPECTED_ENUM_PAIRS.items()),
)
def test_public_enum_member_value_pairs(
    enum_cls: Any, expected_pairs: tuple[tuple[str, str], ...]
) -> None:
    observed_pairs = tuple((member.name, member.value) for member in enum_cls)
    assert observed_pairs == expected_pairs


@pytest.mark.parametrize(
    ("record_cls", "expected_field_names"),
    list(EXPECTED_FIELD_NAMES.items()),
)
def test_required_records_are_frozen_and_slotted_dataclasses(
    record_cls: Any, expected_field_names: tuple[str, ...]
) -> None:
    assert is_dataclass(record_cls)
    assert record_cls.__dataclass_params__.frozen is True  # type: ignore[union-attr]
    assert tuple(field.name for field in fields(record_cls)) == expected_field_names
    assert tuple(record_cls.__slots__) == expected_field_names  # type: ignore[union-attr]


@pytest.mark.parametrize(
    ("record_cls", "kwargs", "blank_field"),
    [
        (RouteCandidateEvaluation, _candidate_kwargs(), "evaluation_id"),
        (RouteCandidateEvaluation, _candidate_kwargs(), "request_reference"),
        (RouteCandidateEvaluation, _candidate_kwargs(), "requester_module"),
        (RouteCandidateEvaluation, _candidate_kwargs(), "environment_id"),
        (RouteCandidateEvaluation, _candidate_kwargs(), "purpose"),
        (RouteCandidateEvaluation, _candidate_kwargs(), "policy_reference"),
        (RouteCandidateEvaluation, _candidate_kwargs(), "route_id"),
        (RouteCandidateEvaluation, _candidate_kwargs(), "agent_id"),
        (
            ServerRouteSelectionBoundary,
            _non_selected_boundary_kwargs(),
            "boundary_id",
        ),
        (
            ServerRouteSelectionBoundary,
            _non_selected_boundary_kwargs(),
            "request_reference",
        ),
        (
            ServerRouteSelectionBoundary,
            _non_selected_boundary_kwargs(),
            "requester_module",
        ),
        (
            ServerRouteSelectionBoundary,
            _non_selected_boundary_kwargs(),
            "environment_id",
        ),
        (
            ServerRouteSelectionBoundary,
            _non_selected_boundary_kwargs(),
            "purpose",
        ),
        (
            ServerRouteSelectionBoundary,
            _non_selected_boundary_kwargs(),
            "policy_reference",
        ),
    ],
)
def test_blank_mandatory_text_fields_are_rejected(
    record_cls: type[object],
    kwargs: dict[str, Any],
    blank_field: str,
) -> None:
    kwargs = dict(kwargs)
    kwargs[blank_field] = " "
    with pytest.raises(ValueError):
        record_cls(**kwargs)


@pytest.mark.parametrize(
    ("record_cls", "kwargs", "field_name"),
    [
        (RouteCandidateEvaluation, _candidate_kwargs(), "capability_scope"),
        (RouteCandidateEvaluation, _candidate_kwargs(), "reason_codes"),
        (RouteCandidateEvaluation, _candidate_kwargs(), "evidence_reference_ids"),
        (
            ServerRouteSelectionBoundary,
            _non_selected_boundary_kwargs(),
            "capability_scope",
        ),
        (
            ServerRouteSelectionBoundary,
            _non_selected_boundary_kwargs(),
            "candidate_evaluations",
        ),
    ],
)
def test_non_tuple_collections_are_rejected(
    record_cls: type[object],
    kwargs: dict[str, Any],
    field_name: str,
) -> None:
    kwargs = dict(kwargs)
    if field_name == "candidate_evaluations":
        kwargs[field_name] = [_candidate_for_route("route-01", "agent-01")]
    else:
        kwargs[field_name] = ["search"]
    with pytest.raises(ValueError):
        record_cls(**kwargs)


@pytest.mark.parametrize(
    ("record_cls", "kwargs", "field_name"),
    [
        (RouteCandidateEvaluation, _candidate_kwargs(), "capability_scope"),
        (RouteCandidateEvaluation, _candidate_kwargs(), "reason_codes"),
        (RouteCandidateEvaluation, _candidate_kwargs(), "evidence_reference_ids"),
        (
            ServerRouteSelectionBoundary,
            _boundary_kwargs(
                candidate_evaluations=(_candidate_for_route("route-01", "agent-01"),),
                decision=RouteSelectionDecision(
                    **_decision_kwargs(
                        status=RouteSelectionStatus.NO_ELIGIBLE_ROUTE,
                        selected_route_id=None,
                        candidate_route_ids=("route-01",),
                        rejected_route_ids=("route-01",),
                        reason_codes=("no-route",),
                        evidence_reference_ids=("evidence-decision-01",),
                    )
                ),
            ),
            "capability_scope",
        ),
    ],
)
def test_blank_tuple_entries_are_rejected(
    record_cls: type[object],
    kwargs: dict[str, Any],
    field_name: str,
) -> None:
    kwargs = dict(kwargs)
    kwargs[field_name] = ("safe", " ")
    with pytest.raises(ValueError):
        record_cls(**kwargs)


@pytest.mark.parametrize(
    ("record_cls", "kwargs", "field_name"),
    [
        (RouteCandidateEvaluation, _candidate_kwargs(), "registration_boundary"),
        (RouteCandidateEvaluation, _candidate_kwargs(), "capability"),
        (RouteCandidateEvaluation, _candidate_kwargs(), "readiness"),
        (RouteCandidateEvaluation, _candidate_kwargs(), "health"),
        (RouteCandidateEvaluation, _candidate_kwargs(), "restriction"),
        (RouteCandidateEvaluation, _candidate_kwargs(), "reconciliation_status"),
        (RouteCandidateEvaluation, _candidate_kwargs(), "status"),
        (
            ServerRouteSelectionBoundary,
            _non_selected_boundary_kwargs(),
            "authority",
        ),
        (
            ServerRouteSelectionBoundary,
            _non_selected_boundary_kwargs(),
            "decision",
        ),
    ],
)
def test_wrong_nested_record_types_are_rejected(
    record_cls: type[object],
    kwargs: dict[str, Any],
    field_name: str,
) -> None:
    kwargs = dict(kwargs)
    kwargs[field_name] = object()
    with pytest.raises(ValueError):
        record_cls(**kwargs)


@pytest.mark.parametrize(
    ("field_name", "mutator"),
    [
        ("route_id", lambda boundary: _mutate(boundary.route, route_id="foreign-route")),
        ("agent_id", lambda boundary: _mutate(boundary.agent, agent_id="foreign-agent")),
        (
            "environment_id",
            lambda boundary: _mutate(boundary.agent, environment_id="foreign-env"),
        ),
        (
            "environment_id",
            lambda boundary: _mutate(boundary.route, environment_id="foreign-env"),
        ),
        (
            "route_id",
            lambda boundary: _mutate(boundary.association, route_id="foreign-route"),
        ),
        (
            "agent_id",
            lambda boundary: _mutate(boundary.association, agent_id="foreign-agent"),
        ),
    ],
)
def test_candidate_cross_record_mismatches_are_rejected(
    field_name: str,
    mutator: Any,
) -> None:
    kwargs = _candidate_kwargs()
    mutator(kwargs["registration_boundary"])
    with pytest.raises(ValueError):
        RouteCandidateEvaluation(**kwargs)


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("route_id", "foreign-route"),
        ("agent_id", "foreign-agent"),
        ("environment_id", "foreign-env"),
    ],
)
def test_candidate_rejects_boundary_route_agent_environment_mismatches(
    field_name: str,
    value: str,
) -> None:
    kwargs = _candidate_kwargs()
    if field_name == "route_id":
        _mutate(kwargs["registration_boundary"].route, route_id=value)
    elif field_name == "agent_id":
        _mutate(kwargs["registration_boundary"].agent, agent_id=value)
    elif field_name == "environment_id":
        _mutate(kwargs["registration_boundary"].route, environment_id=value)
        _mutate(kwargs["registration_boundary"].agent, environment_id=value)
    else:
        raise AssertionError(field_name)
    with pytest.raises(ValueError):
        RouteCandidateEvaluation(**kwargs)


def test_eligible_status_requires_failed_registration_gate() -> None:
    kwargs = _candidate_kwargs()
    _mutate(
        kwargs["registration_boundary"].agent_registration,
        status=AgentRegistrationStatus.REGISTRATION_BLOCKED,
    )
    with pytest.raises(ValueError):
        RouteCandidateEvaluation(**kwargs)


@pytest.mark.parametrize(
    ("field_name", "value", "status"),
    [
        (
            "agent_registration",
            AgentRegistrationStatus.REGISTRATION_BLOCKED,
            RouteCandidateEligibilityStatus.REGISTRATION_BLOCKED,
        ),
        ("purpose", "other-purpose", RouteCandidateEligibilityStatus.PURPOSE_MISMATCH),
        ("capability_scope", ("other",), RouteCandidateEligibilityStatus.CAPABILITY_MISMATCH),
        (
            "agent_lifecycle",
            AgentLifecycleStatus.ONLINE_UNREADY,
            RouteCandidateEligibilityStatus.READINESS_BLOCKED,
        ),
        (
            "health_status",
            RouteHealthStatus.DEGRADED,
            RouteCandidateEligibilityStatus.HEALTH_BLOCKED,
        ),
        (
            "restriction_status",
            RouteRestrictionStatus.RESTRICTED,
            RouteCandidateEligibilityStatus.RESTRICTED,
        ),
        (
            "capability_evidence",
            RouteEvidenceStatus.STALE,
            RouteCandidateEligibilityStatus.EVIDENCE_STALE,
        ),
        (
            "reconciliation_status",
            RouteReconciliationStatus.REQUIRED,
            RouteCandidateEligibilityStatus.RECONCILIATION_BLOCKED,
        ),
    ],
)
def test_candidate_specific_ineligibility_statuses(
    field_name: str,
    value: object,
    status: RouteCandidateEligibilityStatus,
) -> None:
    kwargs = _candidate_kwargs(status=status, reason_codes=("blocked",))
    if field_name == "agent_registration":
        _mutate(kwargs["registration_boundary"].agent_registration, status=value)
    elif field_name == "purpose":
        kwargs["purpose"] = value
    elif field_name == "capability_scope":
        kwargs["capability_scope"] = value
    elif field_name == "agent_lifecycle":
        _mutate(kwargs["registration_boundary"].agent, lifecycle_status=value)
    elif field_name == "health_status":
        _mutate(kwargs["health"], health_status=value)
    elif field_name == "restriction_status":
        _mutate(kwargs["restriction"], status=value, blocks_new_assignments=True)
    elif field_name == "capability_evidence":
        _mutate(kwargs["capability"], evidence_status=value)
    elif field_name == "reconciliation_status":
        kwargs["reconciliation_status"] = value
    else:
        raise AssertionError(field_name)
    candidate = RouteCandidateEvaluation(**kwargs)
    assert candidate.status is status


@pytest.mark.parametrize(
    ("field_name", "value", "status"),
    [
        (
            "agent_registration",
            AgentRegistrationStatus.REGISTRATION_BLOCKED,
            RouteCandidateEligibilityStatus.ELIGIBLE,
        ),
        ("purpose", "other-purpose", RouteCandidateEligibilityStatus.ELIGIBLE),
        ("capability_scope", ("other",), RouteCandidateEligibilityStatus.ELIGIBLE),
        (
            "agent_lifecycle",
            AgentLifecycleStatus.ONLINE_UNREADY,
            RouteCandidateEligibilityStatus.ELIGIBLE,
        ),
        ("health_status", RouteHealthStatus.DEGRADED, RouteCandidateEligibilityStatus.ELIGIBLE),
        (
            "restriction_status",
            RouteRestrictionStatus.RESTRICTED,
            RouteCandidateEligibilityStatus.ELIGIBLE,
        ),
        (
            "capability_evidence",
            RouteEvidenceStatus.STALE,
            RouteCandidateEligibilityStatus.ELIGIBLE,
        ),
        (
            "reconciliation_status",
            RouteReconciliationStatus.REQUIRED,
            RouteCandidateEligibilityStatus.ELIGIBLE,
        ),
    ],
)
def test_eligible_candidates_reject_individual_technical_gate_failures(
    field_name: str,
    value: object,
    status: RouteCandidateEligibilityStatus,
) -> None:
    kwargs = _candidate_kwargs(status=status)
    if field_name == "agent_registration":
        _mutate(kwargs["registration_boundary"].agent_registration, status=value)
    elif field_name == "purpose":
        kwargs["purpose"] = value
    elif field_name == "capability_scope":
        kwargs["capability_scope"] = value
    elif field_name == "agent_lifecycle":
        _mutate(kwargs["registration_boundary"].agent, lifecycle_status=value)
    elif field_name == "health_status":
        _mutate(kwargs["health"], health_status=value)
    elif field_name == "restriction_status":
        _mutate(kwargs["restriction"], status=value, blocks_new_assignments=True)
    elif field_name == "capability_evidence":
        _mutate(kwargs["capability"], evidence_status=value)
    elif field_name == "reconciliation_status":
        kwargs["reconciliation_status"] = value
    else:
        raise AssertionError(field_name)
    with pytest.raises(ValueError):
        RouteCandidateEvaluation(**kwargs)


def test_policy_rejected_requires_all_technical_gates_to_pass() -> None:
    candidate = RouteCandidateEvaluation(
        **_candidate_kwargs(
            status=RouteCandidateEligibilityStatus.POLICY_REJECTED,
            reason_codes=("policy-blocked",),
        )
    )
    assert candidate.status is RouteCandidateEligibilityStatus.POLICY_REJECTED

    kwargs = _candidate_kwargs(
        status=RouteCandidateEligibilityStatus.POLICY_REJECTED,
        reason_codes=("policy-blocked",),
    )
    _mutate(kwargs["capability"], evidence_status=RouteEvidenceStatus.STALE)
    with pytest.raises(ValueError):
        RouteCandidateEvaluation(**kwargs)


def test_selection_boundary_selected_requires_single_eligible_candidate() -> None:
    boundary = _selected_boundary()
    assert boundary.authority is RouteSelectionAuthority.EGRESS_ROUTING_SERVER
    assert boundary.decision.status is RouteSelectionStatus.SELECTED
    assert boundary.decision.selected_route_id == "route-01"
    assert boundary.decision.rejected_route_ids == ("route-02",)
    assert boundary.candidate_evaluations[0].status is RouteCandidateEligibilityStatus.ELIGIBLE
    assert (
        boundary.candidate_evaluations[1].status is RouteCandidateEligibilityStatus.POLICY_REJECTED
    )

    duplicate_eligible = _selected_boundary()
    _mutate(
        duplicate_eligible.candidate_evaluations[1], status=RouteCandidateEligibilityStatus.ELIGIBLE
    )
    with pytest.raises(ValueError):
        ServerRouteSelectionBoundary(
            **_boundary_kwargs(
                candidate_evaluations=duplicate_eligible.candidate_evaluations,
                decision=duplicate_eligible.decision,
            )
        )


def test_no_eligible_route_allows_empty_candidates_but_rejects_hidden_eligibles() -> None:
    empty_boundary = ServerRouteSelectionBoundary(
        **_boundary_kwargs(
            candidate_evaluations=(),
            decision=RouteSelectionDecision(
                **_decision_kwargs(
                    status=RouteSelectionStatus.NO_ELIGIBLE_ROUTE,
                    selected_route_id=None,
                    candidate_route_ids=(),
                    rejected_route_ids=(),
                    reason_codes=("no-route",),
                    evidence_reference_ids=("evidence-decision-01",),
                )
            ),
        )
    )
    assert empty_boundary.decision.selected_route_id is None
    assert empty_boundary.decision.rejected_route_ids == ()

    hidden_eligible = _selected_boundary()
    _mutate(
        hidden_eligible.decision,
        status=RouteSelectionStatus.NO_ELIGIBLE_ROUTE,
        selected_route_id=None,
        rejected_route_ids=("route-01", "route-02"),
    )
    with pytest.raises(ValueError):
        ServerRouteSelectionBoundary(
            **_boundary_kwargs(
                candidate_evaluations=hidden_eligible.candidate_evaluations,
                decision=hidden_eligible.decision,
            )
        )


@pytest.mark.parametrize(
    ("status", "candidate_status", "selected_route_id", "candidate_ids", "rejected_ids"),
    [
        (
            RouteSelectionStatus.BLOCKED,
            RouteCandidateEligibilityStatus.POLICY_REJECTED,
            None,
            ("route-01",),
            ("route-01",),
        ),
        (
            RouteSelectionStatus.RESTRICTED,
            RouteCandidateEligibilityStatus.RESTRICTED,
            None,
            ("route-01",),
            ("route-01",),
        ),
        (
            RouteSelectionStatus.CONFLICT,
            RouteCandidateEligibilityStatus.CONFLICT,
            None,
            ("route-01",),
            ("route-01",),
        ),
        (
            RouteSelectionStatus.AMBIGUOUS,
            RouteCandidateEligibilityStatus.AMBIGUOUS,
            None,
            ("route-01",),
            ("route-01",),
        ),
    ],
)
def test_blocked_and_unresolved_decisions_validate_explicit_candidate_statuses(
    status: RouteSelectionStatus,
    candidate_status: RouteCandidateEligibilityStatus,
    selected_route_id: str | None,
    candidate_ids: tuple[str, ...],
    rejected_ids: tuple[str, ...],
) -> None:
    candidate_kwargs: dict[str, Any] = {
        "status": candidate_status,
        "reason_codes": ("blocked",),
    }
    if candidate_status is RouteCandidateEligibilityStatus.RESTRICTED:
        candidate_kwargs["restriction_status"] = RouteRestrictionStatus.RESTRICTED
        candidate_kwargs["blocks_new_assignments"] = True
    candidates = (_candidate_for_route("route-01", "agent-01", **candidate_kwargs),)
    decision = RouteSelectionDecision(
        **_decision_kwargs(
            status=status,
            selected_route_id=selected_route_id,
            candidate_route_ids=candidate_ids,
            rejected_route_ids=rejected_ids,
            reason_codes=("blocked",),
            evidence_reference_ids=("evidence-decision-01",),
        )
    )
    boundary = ServerRouteSelectionBoundary(
        **_boundary_kwargs(candidate_evaluations=candidates, decision=decision)
    )
    assert boundary.decision.status is status
    assert boundary.decision.selected_route_id is None
    assert boundary.decision.rejected_route_ids == rejected_ids


def test_boundary_rejects_duplicate_candidate_ids_and_context_mismatches() -> None:
    candidate_a = _candidate_for_route(
        "route-01",
        "agent-01",
        status=RouteCandidateEligibilityStatus.POLICY_REJECTED,
        reason_codes=("policy-blocked",),
        evidence_reference_ids=("evidence-candidate-01",),
    )
    candidate_b = _candidate_for_route(
        "route-01",
        "agent-02",
        status=RouteCandidateEligibilityStatus.POLICY_REJECTED,
        reason_codes=("policy-blocked",),
        evidence_reference_ids=("evidence-candidate-02",),
        capability_id="cap-02",
        route_capability_ids=("cap-02",),
    )
    decision = RouteSelectionDecision(
        **_decision_kwargs(
            status=RouteSelectionStatus.NO_ELIGIBLE_ROUTE,
            selected_route_id=None,
            candidate_route_ids=("route-01", "route-01"),
            rejected_route_ids=("route-01",),
            reason_codes=("duplicate",),
            evidence_reference_ids=("evidence-decision-01",),
        )
    )

    with pytest.raises(ValueError):
        ServerRouteSelectionBoundary(
            **_boundary_kwargs(
                candidate_evaluations=(candidate_a, candidate_b),
                decision=decision,
            )
        )


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("request_reference", "foreign-request"),
        ("requester_module", "foreign-module"),
        ("environment_id", "foreign-env"),
        ("purpose", "other-purpose"),
        ("capability_scope", ("other",)),
        ("policy_reference", "foreign-policy"),
    ],
)
def test_boundary_rejects_candidate_request_module_environment_purpose_policy_mismatches(
    field_name: str,
    value: object,
) -> None:
    kwargs = _boundary_kwargs(
        candidate_evaluations=(
            _candidate_for_route(
                "route-01",
                "agent-01",
                status=RouteCandidateEligibilityStatus.POLICY_REJECTED,
                reason_codes=("policy-blocked",),
                evidence_reference_ids=("evidence-candidate-01",),
            ),
        ),
        decision=RouteSelectionDecision(
            **_decision_kwargs(
                status=RouteSelectionStatus.NO_ELIGIBLE_ROUTE,
                selected_route_id=None,
                candidate_route_ids=("route-01",),
                rejected_route_ids=("route-01",),
                reason_codes=("no-route",),
                evidence_reference_ids=("evidence-decision-01",),
            )
        ),
    )
    kwargs[field_name] = value
    with pytest.raises(ValueError):
        ServerRouteSelectionBoundary(**kwargs)


def test_explicit_field_boundaries_do_not_include_provider_or_runtime_fields() -> None:
    field_names = {
        field.name for record_cls in EXPECTED_FIELD_NAMES for field in fields(record_cls)
    }
    banned_tokens = {
        "priority",
        "score",
        "weight",
        "rank",
        "round_robin",
        "fallback_order",
        "retry_count",
        "retry_delay",
        "provider",
        "protocol",
        "host",
        "hostname",
        "ip",
        "port",
        "proxy",
        "vpn",
        "tunnel",
        "cookie",
        "session_value",
        "credential_value",
        "selected_by_parser",
        "selected_by_scan",
        "selected_by_agent",
        "lease_id",
        "assignment_id",
    }
    assert field_names.isdisjoint(banned_tokens)
