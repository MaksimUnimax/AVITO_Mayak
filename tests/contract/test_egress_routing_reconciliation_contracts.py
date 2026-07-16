from __future__ import annotations

from dataclasses import fields, is_dataclass
from pathlib import Path
from typing import cast

import pytest

import mayak.modules.egress_routing.reconciliation as reconciliation_module
import tests.contract.test_egress_routing_dispatch_contracts as dispatch_contracts
from mayak.modules import egress_routing
from mayak.modules.egress_routing import (
    ER06E_TASK_ID,
    DispatchAttempt,
    DispatchStatus,
    RouteReconciliationState,
    RouteReconciliationStatus,
    TransportDispatchAttemptBoundary,
    TransportDispatchAuthority,
    TransportDispatchReconciliationAuthority,
    TransportDispatchReconciliationBoundary,
)

EXPECTED_TASK_ID = "ER-06E-UNKNOWN-DISPATCH-RECONCILIATION-BOUNDARY-20260715-014"

EXPECTED_RECONCILIATION_EXPORTS = (
    "ER06E_TASK_ID",
    "TransportDispatchReconciliationAuthority",
    "TransportDispatchReconciliationBoundary",
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
    "ER07C_TASK_ID",
    "TransportResponsePresenceOutcomeAuthority",
    "TransportResponsePresenceOutcomeBoundary",
    "ER07D_TASK_ID",
    "TransportResponseFailureOutcomeAuthority",
    "TransportResponseFailureOutcomeBoundary",
    "ER08A_TASK_ID",
    "TransportRestrictionSignalAuthority",
    "TransportRestrictionSignalKind",
    "TransportRestrictionSignalBoundary",
    "ER08B_TASK_ID",
    "TransportRestrictionEvaluationAuthority",
    "TransportRestrictionEvaluationGateBoundary",
    "ER09A_TASK_ID",
    "EgressSessionSecretAuthority",
    "EgressSessionSecretGateBoundary",
    "ER10A_TASK_ID",
    "FutureBrowserFallbackAuthority",
    "FutureBrowserFallbackGateBoundary",
    "ER07E_TASK_ID",
    "PolicyFallbackTransportOutcomeAuthority",
    "PolicyFallbackTransportOutcomeBoundary",
    "ER02_TASK_ID",
    "EGRESS_SYNTHETIC_FIXTURE_IDS",
    "EGRESS_SYNTHETIC_FIXTURES",
    "EgressSyntheticFixture",
)

EXPECTED_RECONCILIATION_FIELD_NAMES = (
    "boundary_id",
    "authority",
    "dispatch_attempt",
    "reconciliation_state",
    "reconciliation_state_committed",
    "new_dispatch_effect_authorized",
    "assignment_terminal",
    "reason_codes",
    "evidence_reference_ids",
)

EXPECTED_RECONCILIATION_STATE_FIELD_NAMES = (
    "reconciliation_id",
    "assignment_id",
    "attempt_id",
    "status",
    "reason_codes",
    "evidence_reference_ids",
    "resolved_outcome_reference",
)

EXPECTED_RECONCILIATION_AUTHORITY_MATRIX = (("EGRESS_ROUTING_SERVER", "EGRESS_ROUTING_SERVER"),)

EXPECTED_RECONCILIATION_STATUS_MATRIX = (
    ("NOT_REQUIRED", "NOT_REQUIRED"),
    ("REQUIRED", "REQUIRED"),
    ("PENDING", "PENDING"),
    ("RESOLVED_NOT_SENT", "RESOLVED_NOT_SENT"),
    ("RESOLVED_SENT", "RESOLVED_SENT"),
    ("RESOLVED_TERMINAL", "RESOLVED_TERMINAL"),
    ("REMAINS_AMBIGUOUS", "REMAINS_AMBIGUOUS"),
    ("MANUAL_REVIEW_REQUIRED", "MANUAL_REVIEW_REQUIRED"),
)


def _mutate(record: object, **changes: object) -> None:
    for field_name, value in changes.items():
        object.__setattr__(record, field_name, value)


def _build_state(
    *,
    reconciliation_status: RouteReconciliationStatus = RouteReconciliationStatus.REQUIRED,
) -> dict[str, object]:
    base = dispatch_contracts._build_valid_state(
        dispatch_status=DispatchStatus.UNKNOWN,
        new_dispatch_effect_authorized=False,
        reconciliation_required=True,
        attempt_ordinal=1,
        outcome_reference=None,
    )
    dispatch_boundary = base["boundary"]
    dispatch_attempt = base["attempt"]
    assert isinstance(dispatch_boundary, TransportDispatchAttemptBoundary)
    assert isinstance(dispatch_attempt, DispatchAttempt)

    reconciliation_state = RouteReconciliationState(
        reconciliation_id="reconciliation-01",
        assignment_id=dispatch_attempt.assignment_id,
        attempt_id=dispatch_attempt.attempt_id,
        status=reconciliation_status,
        reason_codes=("reconciliation-required",),
        evidence_reference_ids=("evidence-reconciliation-state-01",),
        resolved_outcome_reference=None,
    )
    boundary = TransportDispatchReconciliationBoundary(
        boundary_id="reconciliation-boundary-01",
        authority=TransportDispatchReconciliationAuthority.EGRESS_ROUTING_SERVER,
        dispatch_attempt=dispatch_boundary,
        reconciliation_state=reconciliation_state,
        reconciliation_state_committed=True,
        new_dispatch_effect_authorized=False,
        assignment_terminal=False,
        reason_codes=("reconciliation-committed",),
        evidence_reference_ids=("evidence-reconciliation-boundary-01",),
    )
    return {
        "boundary": boundary,
        "dispatch_boundary": dispatch_boundary,
        "dispatch_attempt": dispatch_attempt,
        "reconciliation_state": reconciliation_state,
    }


def _build_boundary(
    *,
    reconciliation_status: RouteReconciliationStatus = RouteReconciliationStatus.REQUIRED,
) -> TransportDispatchReconciliationBoundary:
    state = _build_state(reconciliation_status=reconciliation_status)
    boundary = state["boundary"]
    assert isinstance(boundary, TransportDispatchReconciliationBoundary)
    return boundary


def _construct_boundary_from_state(
    state: dict[str, object],
) -> TransportDispatchReconciliationBoundary:
    boundary = TransportDispatchReconciliationBoundary(
        boundary_id="reconciliation-boundary-01",
        authority=TransportDispatchReconciliationAuthority.EGRESS_ROUTING_SERVER,
        dispatch_attempt=state["dispatch_boundary"],  # type: ignore[arg-type]
        reconciliation_state=state["reconciliation_state"],  # type: ignore[arg-type]
        reconciliation_state_committed=True,
        new_dispatch_effect_authorized=False,
        assignment_terminal=False,
        reason_codes=("reconciliation-committed",),
        evidence_reference_ids=("evidence-reconciliation-boundary-01",),
    )
    assert isinstance(boundary, TransportDispatchReconciliationBoundary)
    return boundary


def test_task_id_appears_in_changed_scope_exactly_once() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    source = (repo_root / "src/mayak/modules/egress_routing/reconciliation.py").read_text()
    assert ER06E_TASK_ID == EXPECTED_TASK_ID
    assert source.count(ER06E_TASK_ID) == 1


def test_reconciliation_module_public_exports() -> None:
    assert reconciliation_module.__all__ == EXPECTED_RECONCILIATION_EXPORTS
    assert type(reconciliation_module.__all__) is tuple
    assert tuple(reconciliation_module.__all__) == EXPECTED_RECONCILIATION_EXPORTS
    assert len(reconciliation_module.__all__) == len(EXPECTED_RECONCILIATION_EXPORTS)
    assert len(set(reconciliation_module.__all__)) == len(EXPECTED_RECONCILIATION_EXPORTS)
    assert all(hasattr(reconciliation_module, name) for name in EXPECTED_RECONCILIATION_EXPORTS)


def test_package_module_id_and_public_exports() -> None:
    assert egress_routing.MODULE_ID == "07-egress-routing"
    assert type(egress_routing.__all__) is tuple
    assert egress_routing.__all__ == EXPECTED_PACKAGE_EXPORTS
    assert tuple(egress_routing.__all__) == EXPECTED_PACKAGE_EXPORTS
    assert len(egress_routing.__all__) == len(EXPECTED_PACKAGE_EXPORTS)
    assert len(set(egress_routing.__all__)) == len(EXPECTED_PACKAGE_EXPORTS)
    assert all(hasattr(egress_routing, name) for name in EXPECTED_PACKAGE_EXPORTS)


def test_reconciliation_boundary_record_shape_is_exact() -> None:
    assert is_dataclass(TransportDispatchReconciliationBoundary)
    assert getattr(TransportDispatchReconciliationBoundary, "__dataclass_params__").frozen is True
    assert hasattr(TransportDispatchReconciliationBoundary, "__slots__")
    boundary = _build_boundary()
    assert not hasattr(boundary, "__dict__")
    assert tuple(field.name for field in fields(TransportDispatchReconciliationBoundary)) == (
        EXPECTED_RECONCILIATION_FIELD_NAMES
    )


def test_reconciliation_state_record_fields_are_unchanged() -> None:
    assert tuple(field.name for field in fields(RouteReconciliationState)) == (
        EXPECTED_RECONCILIATION_STATE_FIELD_NAMES
    )


def test_reconciliation_authority_matrix_is_exact() -> None:
    assert [member.value for member in TransportDispatchReconciliationAuthority] == [
        item[0] for item in EXPECTED_RECONCILIATION_AUTHORITY_MATRIX
    ]
    assert (
        TransportDispatchReconciliationAuthority.EGRESS_ROUTING_SERVER.value
        == "EGRESS_ROUTING_SERVER"
    )


def test_reconciliation_status_matrix_is_exact() -> None:
    assert [member.value for member in RouteReconciliationStatus] == [
        item[0] for item in EXPECTED_RECONCILIATION_STATUS_MATRIX
    ]
    assert set(RouteReconciliationStatus.__members__.keys()) == {
        item[0] for item in EXPECTED_RECONCILIATION_STATUS_MATRIX
    }


def test_only_egress_server_authority_commits_reconciliation_state() -> None:
    boundary = _build_boundary()
    assert boundary.authority is TransportDispatchReconciliationAuthority.EGRESS_ROUTING_SERVER


def test_unknown_dispatch_gate_and_identity_linkage_are_exact() -> None:
    boundary = _build_boundary()
    assert boundary.dispatch_attempt.authority is TransportDispatchAuthority.EGRESS_ROUTING_SERVER
    assert boundary.dispatch_attempt.dispatch_state_committed is True
    assert boundary.dispatch_attempt.new_dispatch_effect_authorized is False
    assert boundary.dispatch_attempt.attempt.dispatch_status is DispatchStatus.UNKNOWN
    assert boundary.dispatch_attempt.attempt.attempt_ordinal == 1
    assert boundary.dispatch_attempt.attempt.outcome_reference is None
    assert boundary.dispatch_attempt.attempt.reconciliation_required is True
    assert (
        boundary.reconciliation_state.assignment_id
        == boundary.dispatch_attempt.attempt.assignment_id
    )
    assert boundary.reconciliation_state.attempt_id == boundary.dispatch_attempt.attempt.attempt_id


@pytest.mark.parametrize(
    "status",
    [
        RouteReconciliationStatus.REQUIRED,
        RouteReconciliationStatus.PENDING,
        RouteReconciliationStatus.REMAINS_AMBIGUOUS,
        RouteReconciliationStatus.MANUAL_REVIEW_REQUIRED,
    ],
)
def test_unresolved_reconciliation_statuses_are_accepted(
    status: RouteReconciliationStatus,
) -> None:
    boundary = _build_boundary(reconciliation_status=status)
    assert boundary.reconciliation_state.status is status
    assert boundary.reconciliation_state.resolved_outcome_reference is None
    assert boundary.reconciliation_state_committed is True
    assert boundary.new_dispatch_effect_authorized is False
    assert boundary.assignment_terminal is False


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("authority", "not-an-authority"),
        ("boundary_id", " "),
        ("dispatch_attempt", object()),
        ("reconciliation_state", object()),
        ("reconciliation_state_committed", 1),
        ("new_dispatch_effect_authorized", 0),
        ("assignment_terminal", 1),
        ("reason_codes", ["reason"]),
        ("reason_codes", ()),
        ("evidence_reference_ids", ["evidence"]),
        ("evidence_reference_ids", ()),
    ],
)
def test_boundary_validation_rejects_wrong_field_types(
    field_name: str,
    value: object,
) -> None:
    kwargs: dict[str, object] = {field_name: value}
    with pytest.raises(ValueError):
        state = _build_state()
        boundary_kwargs: dict[str, object] = {
            "boundary_id": "reconciliation-boundary-01",
            "authority": TransportDispatchReconciliationAuthority.EGRESS_ROUTING_SERVER,
            "dispatch_attempt": state["dispatch_boundary"],
            "reconciliation_state": state["reconciliation_state"],
            "reconciliation_state_committed": True,
            "new_dispatch_effect_authorized": False,
            "assignment_terminal": False,
            "reason_codes": ("reconciliation-committed",),
            "evidence_reference_ids": ("evidence-reconciliation-boundary-01",),
        }
        boundary_kwargs.update(kwargs)
        TransportDispatchReconciliationBoundary(**boundary_kwargs)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("authority", "bad-authority"),
        ("reconciliation_state_committed", False),
        ("new_dispatch_effect_authorized", True),
        ("assignment_terminal", True),
    ],
)
def test_boundary_validation_rejects_bool_and_authority_mismatches(
    field_name: str,
    value: object,
) -> None:
    with pytest.raises(ValueError):
        TransportDispatchReconciliationBoundary(  # type: ignore[arg-type]
            boundary_id="reconciliation-boundary-01",
            authority=(
                cast(TransportDispatchReconciliationAuthority, value)
                if field_name == "authority"
                else TransportDispatchReconciliationAuthority.EGRESS_ROUTING_SERVER
            ),
            dispatch_attempt=_build_state()["dispatch_boundary"],  # type: ignore[arg-type]
            reconciliation_state=_build_state()["reconciliation_state"],  # type: ignore[arg-type]
            reconciliation_state_committed=(
                cast(bool, value) if field_name == "reconciliation_state_committed" else True
            ),
            new_dispatch_effect_authorized=(
                cast(bool, value) if field_name == "new_dispatch_effect_authorized" else False
            ),
            assignment_terminal=(
                cast(bool, value) if field_name == "assignment_terminal" else False
            ),
            reason_codes=("reconciliation-committed",),
            evidence_reference_ids=("evidence-reconciliation-boundary-01",),
        )


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("dispatch_status", DispatchStatus.PENDING),
        ("dispatch_status", DispatchStatus.ATTEMPTED),
        ("dispatch_status", DispatchStatus.ACKNOWLEDGED),
        ("dispatch_status", DispatchStatus.REJECTED),
        ("dispatch_status", DispatchStatus.NOT_SENT),
        ("dispatch_status", DispatchStatus.SENT),
        ("attempt_ordinal", 2),
        ("outcome_reference", "outcome-01"),
        ("reconciliation_required", False),
    ],
)
def test_unknown_dispatch_gate_rejects_non_unknown_or_non_first_attempt(
    field_name: str,
    value: object,
) -> None:
    state = _build_state()
    dispatch_attempt = state["dispatch_attempt"]
    assert isinstance(dispatch_attempt, DispatchAttempt)
    _mutate(dispatch_attempt, **{field_name: value})
    with pytest.raises(ValueError):
        _construct_boundary_from_state(state)


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("reconciliation_id", " "),
        ("assignment_id", " "),
        ("attempt_id", " "),
        ("status", RouteReconciliationStatus.NOT_REQUIRED),
        ("status", RouteReconciliationStatus.RESOLVED_NOT_SENT),
        ("status", RouteReconciliationStatus.RESOLVED_SENT),
        ("status", RouteReconciliationStatus.RESOLVED_TERMINAL),
        ("resolved_outcome_reference", "outcome-01"),
    ],
)
def test_reconciliation_state_validation_rejects_wrong_identity_and_resolution(
    field_name: str,
    value: object,
) -> None:
    state = _build_state()
    reconciliation_state = state["reconciliation_state"]
    assert isinstance(reconciliation_state, RouteReconciliationState)
    _mutate(reconciliation_state, **{field_name: value})
    with pytest.raises(ValueError):
        _construct_boundary_from_state(state)


@pytest.mark.parametrize(
    "status",
    [
        RouteReconciliationStatus.REQUIRED,
        RouteReconciliationStatus.PENDING,
        RouteReconciliationStatus.REMAINS_AMBIGUOUS,
        RouteReconciliationStatus.MANUAL_REVIEW_REQUIRED,
    ],
)
def test_non_none_resolved_outcome_reference_is_rejected_for_all_allowed_statuses(
    status: RouteReconciliationStatus,
) -> None:
    state = _build_state(reconciliation_status=status)
    reconciliation_state = state["reconciliation_state"]
    assert isinstance(reconciliation_state, RouteReconciliationState)
    _mutate(reconciliation_state, resolved_outcome_reference="outcome-01")
    with pytest.raises(ValueError):
        _construct_boundary_from_state(state)


def test_nested_records_remain_immutable_under_valid_boundary_construction() -> None:
    state = _build_state()
    boundary = state["boundary"]
    dispatch_attempt = state["dispatch_attempt"]
    reconciliation_state = state["reconciliation_state"]
    assert isinstance(boundary, TransportDispatchReconciliationBoundary)
    assert isinstance(dispatch_attempt, DispatchAttempt)
    assert isinstance(reconciliation_state, RouteReconciliationState)

    before = (
        tuple(getattr(boundary, field.name) for field in fields(boundary)),
        tuple(getattr(dispatch_attempt, field.name) for field in fields(dispatch_attempt)),
        tuple(getattr(reconciliation_state, field.name) for field in fields(reconciliation_state)),
    )

    assert boundary.assignment_terminal is False

    after = (
        tuple(getattr(boundary, field.name) for field in fields(boundary)),
        tuple(getattr(dispatch_attempt, field.name) for field in fields(dispatch_attempt)),
        tuple(getattr(reconciliation_state, field.name) for field in fields(reconciliation_state)),
    )
    assert after == before
