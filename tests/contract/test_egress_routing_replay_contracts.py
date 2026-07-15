from __future__ import annotations

from dataclasses import fields, is_dataclass
from pathlib import Path
from typing import cast

import pytest

from mayak.contracts.idempotency import IdempotencyDecision
from mayak.modules import egress_routing
from mayak.modules.egress_routing import (
    ER06D_TASK_ID,
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
    TransportDispatchReplayAuthority,
    TransportDispatchReplayBoundary,
)
from mayak.modules.egress_routing import replay as replay_module
from mayak.platform.idempotency import (
    IdempotencyFingerprint,
    IdempotencyKey,
    IdempotencyScope,
)

EXPECTED_TASK_ID = (
    "ER-06D-"
    "DISPATCH-REPLAY-DECISION-BOUNDARY-20260715-013"
)

EXPECTED_REPLAY_EXPORTS = (
    "ER06D_TASK_ID",
    "TransportDispatchReplayAuthority",
    "TransportDispatchReplayBoundary",
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
    "ER02_TASK_ID",
    "EGRESS_SYNTHETIC_FIXTURE_IDS",
    "EGRESS_SYNTHETIC_FIXTURES",
    "EgressSyntheticFixture",
)

EXPECTED_REPLAY_FIELD_NAMES = (
    "boundary_id",
    "authority",
    "dispatch_attempt",
    "original_scope",
    "original_key",
    "original_fingerprint",
    "replay_scope",
    "replay_key",
    "replay_fingerprint",
    "decision",
    "original_attempt_reference",
    "replay_dispatch_effect_authorized",
    "reconciliation_required",
    "reason_codes",
    "evidence_reference_ids",
)

EXPECTED_REPLAY_AUTHORITY_MATRIX = (
    ("EGRESS_ROUTING_SERVER", "EGRESS_ROUTING_SERVER"),
)

EXPECTED_DECISION_VALUES = (
    "NEW",
    "REPLAY_TERMINAL",
    "PENDING",
    "MISMATCH",
    "RECONCILE_REQUIRED",
)

EXPECTED_DISPATCH_STATUS_TO_DECISION = (
    (DispatchStatus.PENDING, IdempotencyDecision.PENDING, False),
    (DispatchStatus.ATTEMPTED, IdempotencyDecision.PENDING, False),
    (DispatchStatus.ACKNOWLEDGED, IdempotencyDecision.PENDING, False),
    (DispatchStatus.UNKNOWN, IdempotencyDecision.RECONCILE_REQUIRED, True),
    (DispatchStatus.REJECTED, IdempotencyDecision.REPLAY_TERMINAL, False),
    (DispatchStatus.NOT_SENT, IdempotencyDecision.REPLAY_TERMINAL, False),
    (DispatchStatus.SENT, IdempotencyDecision.REPLAY_TERMINAL, False),
)


def _mutate(record: object, **changes: object) -> None:
    for field_name, value in changes.items():
        object.__setattr__(record, field_name, value)


def _build_state(
    *,
    dispatch_status: DispatchStatus = DispatchStatus.PENDING,
    attempt_ordinal: int = 1,
    outcome_reference: str | None = None,
    dispatch_state_committed: bool = True,
    dispatch_authority: TransportDispatchAuthority = (
        TransportDispatchAuthority.EGRESS_ROUTING_SERVER
    ),
    assignment_authority: TransportAssignmentAuthority = (
        TransportAssignmentAuthority.EGRESS_ROUTING_SERVER
    ),
    lease_status: RouteLeaseStatus = RouteLeaseStatus.GRANTED,
    restriction_snapshot: RouteRestrictionStatus = RouteRestrictionStatus.NONE,
    reconciliation_status: RouteReconciliationStatus = RouteReconciliationStatus.NOT_REQUIRED,
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
        reconciliation_status=reconciliation_status,
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
        authority=assignment_authority,
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
    attempt = DispatchAttempt(
        attempt_id="attempt-01",
        assignment_id=assignment.assignment_id,
        lease_id=assignment.lease_id,
        route_id=assignment.route_id,
        agent_id=assignment.agent_id,
        dispatch_status=dispatch_status,
        attempt_ordinal=attempt_ordinal,
        outcome_reference=outcome_reference,
        reconciliation_required=dispatch_status is DispatchStatus.UNKNOWN,
        correlation_id=assignment.correlation_id,
        causation_id=assignment.causation_id,
    )
    dispatch_attempt = TransportDispatchAttemptBoundary(
        boundary_id="dispatch-boundary-01",
        authority=dispatch_authority,
        assignment_commitment=commitment,
        attempt=attempt,
        dispatch_state_committed=dispatch_state_committed,
        new_dispatch_effect_authorized=dispatch_status is DispatchStatus.PENDING,
        reason_codes=("dispatch-committed",),
        evidence_reference_ids=("evidence-dispatch-01",),
    )
    return {
        "dispatch_attempt": dispatch_attempt,
        "scope": IdempotencyScope(value="scope-01"),
        "key": IdempotencyKey(value="key-01"),
        "fingerprint": IdempotencyFingerprint(value="fingerprint-01"),
    }


def _build_replay_boundary(
    *,
    boundary_id: str = "replay-boundary-01",
    authority: TransportDispatchReplayAuthority = (
        TransportDispatchReplayAuthority.EGRESS_ROUTING_SERVER
    ),
    dispatch_attempt: TransportDispatchAttemptBoundary | None = None,
    dispatch_status: DispatchStatus = DispatchStatus.PENDING,
    dispatch_state_committed: bool = True,
    attempt_ordinal: int = 1,
    outcome_reference: str | None = None,
    dispatch_authority: TransportDispatchAuthority = (
        TransportDispatchAuthority.EGRESS_ROUTING_SERVER
    ),
    assignment_authority: TransportAssignmentAuthority = (
        TransportAssignmentAuthority.EGRESS_ROUTING_SERVER
    ),
    lease_status: RouteLeaseStatus = RouteLeaseStatus.GRANTED,
    restriction_snapshot: RouteRestrictionStatus = RouteRestrictionStatus.NONE,
    reconciliation_status: RouteReconciliationStatus = RouteReconciliationStatus.NOT_REQUIRED,
    original_scope: IdempotencyScope | None = None,
    original_key: IdempotencyKey | None = None,
    original_fingerprint: IdempotencyFingerprint | None = None,
    replay_scope: IdempotencyScope | None = None,
    replay_key: IdempotencyKey | None = None,
    replay_fingerprint: IdempotencyFingerprint | None = None,
    decision: IdempotencyDecision | None = None,
    original_attempt_reference: str = "attempt-01",
    replay_dispatch_effect_authorized: bool = False,
    reconciliation_required: bool | None = None,
    reason_codes: tuple[str, ...] = ("replay-decision",),
    evidence_reference_ids: tuple[str, ...] = ("evidence-replay-01",),
) -> TransportDispatchReplayBoundary:
    state = _build_state(
        dispatch_status=dispatch_status,
        attempt_ordinal=attempt_ordinal,
        outcome_reference=outcome_reference,
        dispatch_state_committed=dispatch_state_committed,
        dispatch_authority=dispatch_authority,
        assignment_authority=assignment_authority,
        lease_status=lease_status,
        restriction_snapshot=restriction_snapshot,
        reconciliation_status=reconciliation_status,
    )
    if dispatch_attempt is None:
        dispatch_attempt = cast(TransportDispatchAttemptBoundary, state["dispatch_attempt"])
    scope = state["scope"]
    key = state["key"]
    fingerprint = state["fingerprint"]
    assert isinstance(scope, IdempotencyScope)
    assert isinstance(key, IdempotencyKey)
    assert isinstance(fingerprint, IdempotencyFingerprint)

    return TransportDispatchReplayBoundary(
        boundary_id=boundary_id,
        authority=authority,
        dispatch_attempt=dispatch_attempt,
        original_scope=original_scope or scope,
        original_key=original_key or key,
        original_fingerprint=original_fingerprint or fingerprint,
        replay_scope=replay_scope or scope,
        replay_key=replay_key or key,
        replay_fingerprint=replay_fingerprint or fingerprint,
        decision=decision or (
            IdempotencyDecision.PENDING
            if dispatch_status in (
                DispatchStatus.PENDING,
                DispatchStatus.ATTEMPTED,
                DispatchStatus.ACKNOWLEDGED,
            )
            else (
                IdempotencyDecision.RECONCILE_REQUIRED
                if dispatch_status is DispatchStatus.UNKNOWN
                else IdempotencyDecision.REPLAY_TERMINAL
            )
        ),
        original_attempt_reference=original_attempt_reference,
        replay_dispatch_effect_authorized=replay_dispatch_effect_authorized,
        reconciliation_required=(
            dispatch_status is DispatchStatus.UNKNOWN
            if reconciliation_required is None
            else reconciliation_required
        ),
        reason_codes=reason_codes,
        evidence_reference_ids=evidence_reference_ids,
    )


def test_task_id_appears_in_changed_scope_exactly_once() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    replay_source = (repo_root / "src/mayak/modules/egress_routing/replay.py").read_text()
    assert ER06D_TASK_ID == EXPECTED_TASK_ID
    assert replay_source.count(ER06D_TASK_ID) == 1


def test_replay_module_public_exports() -> None:
    assert replay_module.__all__ == EXPECTED_REPLAY_EXPORTS
    assert type(replay_module.__all__) is tuple
    assert len(replay_module.__all__) == len(EXPECTED_REPLAY_EXPORTS)
    assert len(set(replay_module.__all__)) == len(EXPECTED_REPLAY_EXPORTS)
    assert all(hasattr(replay_module, name) for name in EXPECTED_REPLAY_EXPORTS)


def test_package_module_id_and_public_exports() -> None:
    assert egress_routing.MODULE_ID == "07-egress-routing"
    assert type(egress_routing.__all__) is tuple
    assert egress_routing.__all__ == EXPECTED_PACKAGE_EXPORTS
    assert tuple(egress_routing.__all__) == EXPECTED_PACKAGE_EXPORTS
    assert len(egress_routing.__all__) == len(EXPECTED_PACKAGE_EXPORTS)
    assert len(set(egress_routing.__all__)) == len(EXPECTED_PACKAGE_EXPORTS)
    assert all(hasattr(egress_routing, name) for name in EXPECTED_PACKAGE_EXPORTS)


def test_replay_boundary_record_shape_is_exact() -> None:
    assert is_dataclass(TransportDispatchReplayBoundary)
    assert getattr(TransportDispatchReplayBoundary, "__dataclass_params__").frozen is True
    assert hasattr(TransportDispatchReplayBoundary, "__slots__")
    boundary = _build_replay_boundary()
    assert not hasattr(boundary, "__dict__")
    assert tuple(field.name for field in fields(TransportDispatchReplayBoundary)) == (
        EXPECTED_REPLAY_FIELD_NAMES
    )


def test_replay_authority_matrix_is_exact() -> None:
    assert [member.value for member in TransportDispatchReplayAuthority] == [
        item[0] for item in EXPECTED_REPLAY_AUTHORITY_MATRIX
    ]
    assert TransportDispatchReplayAuthority.EGRESS_ROUTING_SERVER.value == "EGRESS_ROUTING_SERVER"


def test_shared_idempotency_primitives_are_unchanged() -> None:
    assert IdempotencyDecision.__module__ == "mayak.contracts.idempotency"
    assert tuple(member.value for member in IdempotencyDecision) == EXPECTED_DECISION_VALUES
    assert set(IdempotencyDecision.__members__.keys()) == set(EXPECTED_DECISION_VALUES)
    assert IdempotencyScope.__module__ == "mayak.platform.idempotency"
    assert IdempotencyKey.__module__ == "mayak.platform.idempotency"
    assert IdempotencyFingerprint.__module__ == "mayak.platform.idempotency"
    assert type(IdempotencyScope(value="scope-x")) is IdempotencyScope
    assert type(IdempotencyKey(value="key-x")) is IdempotencyKey
    assert type(IdempotencyFingerprint(value="fingerprint-x")) is IdempotencyFingerprint


@pytest.mark.parametrize(
    ("dispatch_status", "expected_decision", "expected_reconciliation_required"),
    EXPECTED_DISPATCH_STATUS_TO_DECISION,
)
def test_exact_match_status_matrix_is_unchanged(
    dispatch_status: DispatchStatus,
    expected_decision: IdempotencyDecision,
    expected_reconciliation_required: bool,
) -> None:
    boundary = _build_replay_boundary(dispatch_status=dispatch_status)
    assert boundary.decision is expected_decision
    assert boundary.replay_dispatch_effect_authorized is False
    assert boundary.reconciliation_required is expected_reconciliation_required
    assert boundary.original_scope == boundary.replay_scope
    assert boundary.original_key == boundary.replay_key
    assert boundary.original_fingerprint == boundary.replay_fingerprint
    assert boundary.original_attempt_reference == boundary.dispatch_attempt.attempt.attempt_id


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("replay_scope", IdempotencyScope(value="scope-02")),
        ("replay_key", IdempotencyKey(value="key-02")),
        ("replay_fingerprint", IdempotencyFingerprint(value="fingerprint-02")),
    ],
)
def test_mismatch_matrix_is_exact(field_name: str, value: object) -> None:
    boundary = _build_replay_boundary(
        decision=IdempotencyDecision.MISMATCH,
        **{field_name: value},  # type: ignore[arg-type]
    )
    assert boundary.decision is IdempotencyDecision.MISMATCH
    assert boundary.replay_dispatch_effect_authorized is False
    assert boundary.reconciliation_required is False


@pytest.mark.parametrize(
    ("dispatch_status", "wrong_decision"),
    [
        (DispatchStatus.PENDING, IdempotencyDecision.MISMATCH),
        (DispatchStatus.ATTEMPTED, IdempotencyDecision.REPLAY_TERMINAL),
        (DispatchStatus.ACKNOWLEDGED, IdempotencyDecision.RECONCILE_REQUIRED),
        (DispatchStatus.UNKNOWN, IdempotencyDecision.PENDING),
        (DispatchStatus.REJECTED, IdempotencyDecision.PENDING),
        (DispatchStatus.NOT_SENT, IdempotencyDecision.PENDING),
        (DispatchStatus.SENT, IdempotencyDecision.PENDING),
    ],
)
def test_exact_match_rejects_wrong_decision(
    dispatch_status: DispatchStatus,
    wrong_decision: IdempotencyDecision,
) -> None:
    with pytest.raises(ValueError, match="decision does not match replay semantics"):
        _build_replay_boundary(dispatch_status=dispatch_status, decision=wrong_decision)


def test_mismatch_rejects_non_mismatch_decision() -> None:
    with pytest.raises(ValueError, match="decision does not match replay semantics"):
        _build_replay_boundary(
            decision=IdempotencyDecision.PENDING,
            replay_scope=IdempotencyScope(value="scope-02"),
        )


def test_unknown_mismatch_preserves_reconciliation_requirement() -> None:
    boundary = _build_replay_boundary(
        dispatch_status=DispatchStatus.UNKNOWN,
        decision=IdempotencyDecision.MISMATCH,
        replay_scope=IdempotencyScope(value="scope-02"),
    )
    assert boundary.decision is IdempotencyDecision.MISMATCH
    assert boundary.replay_dispatch_effect_authorized is False
    assert boundary.reconciliation_required is True


@pytest.mark.parametrize(
    ("dispatch_status", "reconciliation_required"),
    [
        (DispatchStatus.UNKNOWN, False),
        (DispatchStatus.PENDING, True),
        (DispatchStatus.ATTEMPTED, True),
        (DispatchStatus.ACKNOWLEDGED, True),
        (DispatchStatus.REJECTED, True),
        (DispatchStatus.NOT_SENT, True),
        (DispatchStatus.SENT, True),
    ],
)
def test_reconciliation_invariant_is_enforced(
    dispatch_status: DispatchStatus,
    reconciliation_required: bool,
) -> None:
    with pytest.raises(
        ValueError,
        match="reconciliation_required must be True only when dispatch_status is UNKNOWN",
    ):
        _build_replay_boundary(
            dispatch_status=dispatch_status,
            reconciliation_required=reconciliation_required,
        )


def test_dispatch_state_committed_false_is_rejected() -> None:
    state = _build_state()
    dispatch_attempt = state["dispatch_attempt"]
    scope = state["scope"]
    key = state["key"]
    fingerprint = state["fingerprint"]
    assert isinstance(dispatch_attempt, TransportDispatchAttemptBoundary)
    assert isinstance(scope, IdempotencyScope)
    assert isinstance(key, IdempotencyKey)
    assert isinstance(fingerprint, IdempotencyFingerprint)
    _mutate(dispatch_attempt, dispatch_state_committed=False)
    with pytest.raises(ValueError, match="dispatch_state_committed must be True"):
        TransportDispatchReplayBoundary(
            boundary_id="replay-boundary-01",
            authority=TransportDispatchReplayAuthority.EGRESS_ROUTING_SERVER,
            dispatch_attempt=dispatch_attempt,
            original_scope=scope,
            original_key=key,
            original_fingerprint=fingerprint,
            replay_scope=scope,
            replay_key=key,
            replay_fingerprint=fingerprint,
            decision=IdempotencyDecision.PENDING,
            original_attempt_reference="attempt-01",
            replay_dispatch_effect_authorized=False,
            reconciliation_required=False,
            reason_codes=("replay-decision",),
            evidence_reference_ids=("evidence-replay-01",),
        )


def test_original_attempt_reference_mismatch_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="original_attempt_reference must match dispatch_attempt.attempt.attempt_id",
    ):
        _build_replay_boundary(original_attempt_reference="attempt-02")


@pytest.mark.parametrize(
    (
        "kwargs",
        "expected_message",
    ),
    [
        ({"authority": object()}, "authority must be TransportDispatchReplayAuthority"),
        ({"boundary_id": "   "}, "boundary_id must be a non-blank string"),
        (
            {"dispatch_attempt": object()},
            "dispatch_attempt must be TransportDispatchAttemptBoundary",
        ),
        ({"original_scope": "scope-raw"}, "original_scope must be IdempotencyScope"),
        ({"original_key": "key-raw"}, "original_key must be IdempotencyKey"),
        (
            {"original_fingerprint": "fingerprint-raw"},
            "original_fingerprint must be IdempotencyFingerprint",
        ),
        ({"replay_scope": "scope-raw"}, "replay_scope must be IdempotencyScope"),
        ({"replay_key": "key-raw"}, "replay_key must be IdempotencyKey"),
        (
            {"replay_fingerprint": "fingerprint-raw"},
            "replay_fingerprint must be IdempotencyFingerprint",
        ),
        ({"decision": "PENDING"}, "decision must be IdempotencyDecision"),
        ({"decision": IdempotencyDecision.NEW}, "decision NEW is forbidden"),
        (
            {"original_attempt_reference": "   "},
            "original_attempt_reference must be a non-blank string",
        ),
        (
            {"replay_dispatch_effect_authorized": "false"},
            "replay_dispatch_effect_authorized must be a bool",
        ),
        (
            {"replay_dispatch_effect_authorized": True},
            "replay_dispatch_effect_authorized must be False",
        ),
        ({"reconciliation_required": "false"}, "reconciliation_required must be a bool"),
        (
            {"reason_codes": ("replay-decision",), "evidence_reference_ids": []},
            "evidence_reference_ids must be a tuple",
        ),
        (
            {"reason_codes": [], "evidence_reference_ids": ("evidence-replay-01",)},
            "reason_codes must be a tuple",
        ),
        (
            {"reason_codes": (), "evidence_reference_ids": ("evidence-replay-01",)},
            "reason_codes must not be empty",
        ),
        (
            {"reason_codes": ("replay-decision",), "evidence_reference_ids": ()},
            "evidence_reference_ids must not be empty",
        ),
    ],
)
def test_exact_validation_rejects_invalid_values(
    kwargs: dict[str, object],
    expected_message: str,
) -> None:
    base_kwargs: dict[str, object] = {
        "dispatch_status": DispatchStatus.PENDING,
    }
    base_kwargs.update(kwargs)
    with pytest.raises(ValueError, match=expected_message):
        _build_replay_boundary(**base_kwargs)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("field_name", "value", "expected_message"),
    [
        ("reason_codes", ["replay-decision"], "reason_codes must be a tuple"),
        ("reason_codes", (item for item in ("replay-decision",)), "reason_codes must be a tuple"),
        ("reason_codes", {"replay-decision"}, "reason_codes must be a tuple"),
        (
            "reason_codes",
            ("replay-decision", " "),
            "reason_codes must be a non-blank string",
        ),
        (
            "evidence_reference_ids",
            ["evidence-replay-01"],
            "evidence_reference_ids must be a tuple",
        ),
        (
            "evidence_reference_ids",
            (item for item in ("evidence-replay-01",)),
            "evidence_reference_ids must be a tuple",
        ),
        (
            "evidence_reference_ids",
            {"evidence-replay-01"},
            "evidence_reference_ids must be a tuple",
        ),
        (
            "evidence_reference_ids",
            ("evidence-replay-01", " "),
            "evidence_reference_ids must be a non-blank string",
        ),
    ],
)
def test_exact_tuple_validation_rejects_lists_generators_sets_and_blank_items(
    field_name: str,
    value: object,
    expected_message: str,
) -> None:
    kwargs: dict[str, object] = {
        "reason_codes": ("replay-decision",),
        "evidence_reference_ids": ("evidence-replay-01",),
    }
    kwargs[field_name] = value
    with pytest.raises(ValueError, match=expected_message):
        _build_replay_boundary(**kwargs)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("field_name", "value", "expected_message"),
    [
        (
            "replay_dispatch_effect_authorized",
            1,
            "replay_dispatch_effect_authorized must be a bool",
        ),
        (
            "replay_dispatch_effect_authorized",
            "false",
            "replay_dispatch_effect_authorized must be a bool",
        ),
        ("reconciliation_required", 1, "reconciliation_required must be a bool"),
        ("reconciliation_required", "false", "reconciliation_required must be a bool"),
    ],
)
def test_exact_bool_validation_rejects_non_bool_values(
    field_name: str,
    value: object,
    expected_message: str,
) -> None:
    kwargs: dict[str, object] = {
        "dispatch_status": DispatchStatus.UNKNOWN,
        "replay_dispatch_effect_authorized": False,
        "reconciliation_required": True,
    }
    kwargs[field_name] = value
    with pytest.raises(ValueError, match=expected_message):
        _build_replay_boundary(**kwargs)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("field_name", "value", "expected_message"),
    [
        (
            "dispatch_attempt",
            "attempt-01",
            "dispatch_attempt must be TransportDispatchAttemptBoundary",
        ),
        ("original_scope", "scope-raw", "original_scope must be IdempotencyScope"),
        ("original_key", "key-raw", "original_key must be IdempotencyKey"),
        (
            "original_fingerprint",
            "fingerprint-raw",
            "original_fingerprint must be IdempotencyFingerprint",
        ),
        ("replay_scope", "scope-raw", "replay_scope must be IdempotencyScope"),
        ("replay_key", "key-raw", "replay_key must be IdempotencyKey"),
        (
            "replay_fingerprint",
            "fingerprint-raw",
            "replay_fingerprint must be IdempotencyFingerprint",
        ),
    ],
)
def test_exact_idempotency_types_reject_raw_strings(
    field_name: str,
    value: object,
    expected_message: str,
) -> None:
    kwargs: dict[str, object] = {field_name: value}
    with pytest.raises(ValueError, match=expected_message):
        _build_replay_boundary(**kwargs)  # type: ignore[arg-type]


def test_only_egress_server_authority_is_permitted() -> None:
    boundary = _build_replay_boundary()
    assert boundary.authority is TransportDispatchReplayAuthority.EGRESS_ROUTING_SERVER
    with pytest.raises(
        ValueError,
        match="authority must be TransportDispatchReplayAuthority",
    ):
        _build_replay_boundary(authority=object())  # type: ignore[arg-type]


def test_existing_dispatch_gate_is_enforced() -> None:
    state = _build_state()
    dispatch_attempt = state["dispatch_attempt"]
    scope = state["scope"]
    key = state["key"]
    fingerprint = state["fingerprint"]
    assert isinstance(dispatch_attempt, TransportDispatchAttemptBoundary)
    assert isinstance(scope, IdempotencyScope)
    assert isinstance(key, IdempotencyKey)
    assert isinstance(fingerprint, IdempotencyFingerprint)
    _mutate(dispatch_attempt, authority=object())
    with pytest.raises(
        ValueError,
        match="dispatch_attempt.authority must be EGRESS_ROUTING_SERVER",
    ):
        TransportDispatchReplayBoundary(
            boundary_id="replay-boundary-01",
            authority=TransportDispatchReplayAuthority.EGRESS_ROUTING_SERVER,
            dispatch_attempt=dispatch_attempt,
            original_scope=scope,
            original_key=key,
            original_fingerprint=fingerprint,
            replay_scope=scope,
            replay_key=key,
            replay_fingerprint=fingerprint,
            decision=IdempotencyDecision.PENDING,
            original_attempt_reference="attempt-01",
            replay_dispatch_effect_authorized=False,
            reconciliation_required=False,
            reason_codes=("replay-decision",),
            evidence_reference_ids=("evidence-replay-01",),
        )
