from __future__ import annotations

from dataclasses import fields, is_dataclass
from pathlib import Path
from typing import Any, cast

import pytest

import mayak.modules.egress_routing.reconciliation_resolution as resolution_module
import tests.contract.test_egress_routing_reconciliation_contracts as reconciliation_contracts
from mayak.modules import egress_routing
from mayak.modules.egress_routing import (
    ER06F_TASK_ID,
    RouteReconciliationState,
    RouteReconciliationStatus,
    TransportDispatchReconciliationAuthority,
    TransportDispatchReconciliationBoundary,
    TransportDispatchReconciliationResolutionAuthority,
    TransportDispatchReconciliationResolutionBoundary,
)

EXPECTED_TASK_ID = "ER-06F-RESOLVED-DISPATCH-RECONCILIATION-BOUNDARY-20260715-015"

EXPECTED_MODULE_EXPORTS = (
    "ER06F_TASK_ID",
    "TransportDispatchReconciliationResolutionAuthority",
    "TransportDispatchReconciliationResolutionBoundary",
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
    "ER02_TASK_ID",
    "EGRESS_SYNTHETIC_FIXTURE_IDS",
    "EGRESS_SYNTHETIC_FIXTURES",
    "EgressSyntheticFixture",
)

EXPECTED_BOUNDARY_FIELD_NAMES = (
    "boundary_id",
    "authority",
    "unresolved_reconciliation",
    "resolved_reconciliation_state",
    "resolution_committed",
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

EXPECTED_AUTHORITY_MATRIX = (("EGRESS_ROUTING_SERVER", "EGRESS_ROUTING_SERVER"),)

EXPECTED_SOURCE_STATUSES = (
    RouteReconciliationStatus.REQUIRED,
    RouteReconciliationStatus.PENDING,
    RouteReconciliationStatus.REMAINS_AMBIGUOUS,
    RouteReconciliationStatus.MANUAL_REVIEW_REQUIRED,
)

EXPECTED_TARGET_STATUSES = (
    RouteReconciliationStatus.RESOLVED_NOT_SENT,
    RouteReconciliationStatus.RESOLVED_SENT,
    RouteReconciliationStatus.RESOLVED_TERMINAL,
)

EXPECTED_INVALID_SOURCE_STATUSES = (
    RouteReconciliationStatus.NOT_REQUIRED,
    RouteReconciliationStatus.RESOLVED_NOT_SENT,
    RouteReconciliationStatus.RESOLVED_SENT,
    RouteReconciliationStatus.RESOLVED_TERMINAL,
)

EXPECTED_INVALID_TARGET_STATUSES = (
    RouteReconciliationStatus.NOT_REQUIRED,
    RouteReconciliationStatus.REQUIRED,
    RouteReconciliationStatus.PENDING,
    RouteReconciliationStatus.REMAINS_AMBIGUOUS,
    RouteReconciliationStatus.MANUAL_REVIEW_REQUIRED,
)

EXPECTED_INVALID_TUPLE_VALUES = (
    (),
    (" ",),
    ["reason-code-01"],
)


def _mutate(record: object, **changes: object) -> None:
    for field_name, value in changes.items():
        object.__setattr__(record, field_name, value)


def _build_unresolved_boundary(
    *,
    status: RouteReconciliationStatus = RouteReconciliationStatus.REQUIRED,
) -> TransportDispatchReconciliationBoundary:
    boundary = reconciliation_contracts._build_boundary(reconciliation_status=status)
    assert isinstance(boundary, TransportDispatchReconciliationBoundary)
    return boundary


def _build_resolved_state(
    source_boundary: TransportDispatchReconciliationBoundary,
    *,
    target_status: RouteReconciliationStatus,
    resolved_outcome_reference: str | None,
) -> RouteReconciliationState:
    source_state = source_boundary.reconciliation_state
    assert isinstance(source_state, RouteReconciliationState)
    return RouteReconciliationState(
        reconciliation_id=source_state.reconciliation_id,
        assignment_id=source_state.assignment_id,
        attempt_id=source_state.attempt_id,
        status=target_status,
        reason_codes=("resolved-reconciliation",),
        evidence_reference_ids=("evidence-resolution-state-01",),
        resolved_outcome_reference=resolved_outcome_reference,
    )


def _build_boundary(
    *,
    source_status: RouteReconciliationStatus = RouteReconciliationStatus.REQUIRED,
    target_status: RouteReconciliationStatus = RouteReconciliationStatus.RESOLVED_NOT_SENT,
    boundary_id: str = "resolution-boundary-01",
    authority: object = TransportDispatchReconciliationResolutionAuthority.EGRESS_ROUTING_SERVER,
    unresolved_reconciliation: object | None = None,
    resolved_reconciliation_state: object | None = None,
    resolution_committed: object = True,
    new_dispatch_effect_authorized: object = False,
    assignment_terminal: object = True,
    reason_codes: object = ("resolution-committed",),
    evidence_reference_ids: object = ("evidence-resolution-boundary-01",),
    resolved_outcome_reference: str | None = None,
) -> TransportDispatchReconciliationResolutionBoundary:
    if unresolved_reconciliation is None:
        unresolved_reconciliation = _build_unresolved_boundary(status=source_status)
    if resolved_reconciliation_state is None:
        source_boundary = unresolved_reconciliation
        assert isinstance(source_boundary, TransportDispatchReconciliationBoundary)
        if resolved_outcome_reference is None and target_status in EXPECTED_TARGET_STATUSES:
            resolved_outcome_reference = (
                f"resolved-outcome-{source_status.name.lower()}-{target_status.name.lower()}"
            )
        resolved_reconciliation_state = _build_resolved_state(
            source_boundary,
            target_status=target_status,
            resolved_outcome_reference=resolved_outcome_reference,
        )
    boundary = TransportDispatchReconciliationResolutionBoundary(
        boundary_id=boundary_id,
        authority=authority,  # type: ignore[arg-type]
        unresolved_reconciliation=unresolved_reconciliation,  # type: ignore[arg-type]
        resolved_reconciliation_state=resolved_reconciliation_state,  # type: ignore[arg-type]
        resolution_committed=resolution_committed,  # type: ignore[arg-type]
        new_dispatch_effect_authorized=new_dispatch_effect_authorized,  # type: ignore[arg-type]
        assignment_terminal=assignment_terminal,  # type: ignore[arg-type]
        reason_codes=reason_codes,  # type: ignore[arg-type]
        evidence_reference_ids=evidence_reference_ids,  # type: ignore[arg-type]
    )
    assert isinstance(boundary, TransportDispatchReconciliationResolutionBoundary)
    return boundary


def _field_names(*records: object) -> set[str]:
    names: set[str] = set()
    for record in records:
        names.update(field.name for field in fields(cast(Any, record)))
    return names


def _snapshot(record: object) -> tuple[object, ...]:
    dataclass_record = cast(Any, record)
    return tuple(getattr(dataclass_record, field.name) for field in fields(dataclass_record))


def test_task_id_appears_in_changed_scope_exactly_once() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    source = (
        repo_root / "src/mayak/modules/egress_routing/reconciliation_resolution.py"
    ).read_text()
    assert ER06F_TASK_ID == EXPECTED_TASK_ID
    assert source.count(ER06F_TASK_ID) == 1


def test_resolution_module_public_exports() -> None:
    assert resolution_module.__all__ == EXPECTED_MODULE_EXPORTS
    assert type(resolution_module.__all__) is tuple
    assert tuple(resolution_module.__all__) == EXPECTED_MODULE_EXPORTS
    assert len(resolution_module.__all__) == len(EXPECTED_MODULE_EXPORTS)
    assert len(set(resolution_module.__all__)) == len(EXPECTED_MODULE_EXPORTS)
    assert all(hasattr(resolution_module, name) for name in EXPECTED_MODULE_EXPORTS)


def test_package_module_id_and_public_exports() -> None:
    assert egress_routing.MODULE_ID == "07-egress-routing"
    assert type(egress_routing.__all__) is tuple
    assert egress_routing.__all__ == EXPECTED_PACKAGE_EXPORTS
    assert tuple(egress_routing.__all__) == EXPECTED_PACKAGE_EXPORTS
    assert len(egress_routing.__all__) == len(EXPECTED_PACKAGE_EXPORTS)
    assert len(set(egress_routing.__all__)) == len(EXPECTED_PACKAGE_EXPORTS)
    assert all(hasattr(egress_routing, name) for name in EXPECTED_PACKAGE_EXPORTS)


def test_resolution_boundary_record_shape_is_exact() -> None:
    assert is_dataclass(TransportDispatchReconciliationResolutionBoundary)
    assert (
        getattr(TransportDispatchReconciliationResolutionBoundary, "__dataclass_params__").frozen
        is True
    )
    assert hasattr(TransportDispatchReconciliationResolutionBoundary, "__slots__")
    boundary = _build_boundary()
    assert not hasattr(boundary, "__dict__")
    assert tuple(
        field.name for field in fields(TransportDispatchReconciliationResolutionBoundary)
    ) == (EXPECTED_BOUNDARY_FIELD_NAMES)


def test_reconciliation_state_record_fields_are_unchanged() -> None:
    assert tuple(field.name for field in fields(RouteReconciliationState)) == (
        EXPECTED_RECONCILIATION_STATE_FIELD_NAMES
    )


def test_resolution_authority_matrix_is_exact() -> None:
    assert tuple(member.name for member in TransportDispatchReconciliationResolutionAuthority) == (
        "EGRESS_ROUTING_SERVER",
    )
    assert tuple(member.value for member in TransportDispatchReconciliationResolutionAuthority) == (
        "EGRESS_ROUTING_SERVER",
    )
    assert EXPECTED_AUTHORITY_MATRIX == (("EGRESS_ROUTING_SERVER", "EGRESS_ROUTING_SERVER"),)


@pytest.mark.parametrize("source_status", EXPECTED_SOURCE_STATUSES)
@pytest.mark.parametrize("target_status", EXPECTED_TARGET_STATUSES)
def test_valid_resolution_matrix(
    source_status: RouteReconciliationStatus,
    target_status: RouteReconciliationStatus,
) -> None:
    boundary = _build_boundary(source_status=source_status, target_status=target_status)
    source_state = boundary.unresolved_reconciliation.reconciliation_state
    resolved_state = boundary.resolved_reconciliation_state

    assert (
        boundary.authority
        is TransportDispatchReconciliationResolutionAuthority.EGRESS_ROUTING_SERVER
    )
    assert boundary.unresolved_reconciliation.authority is (
        TransportDispatchReconciliationAuthority.EGRESS_ROUTING_SERVER
    )
    assert source_state.status is source_status
    assert resolved_state.status is target_status
    assert boundary.resolution_committed is True
    assert boundary.new_dispatch_effect_authorized is False
    assert boundary.assignment_terminal is True
    assert resolved_state.reconciliation_id == source_state.reconciliation_id
    assert resolved_state.assignment_id == source_state.assignment_id
    assert resolved_state.attempt_id == source_state.attempt_id
    assert resolved_state.resolved_outcome_reference is not None
    assert resolved_state.resolved_outcome_reference.strip()
    assert source_state.resolved_outcome_reference is None
    assert boundary.unresolved_reconciliation.reconciliation_state_committed is True
    assert boundary.unresolved_reconciliation.new_dispatch_effect_authorized is False
    assert boundary.unresolved_reconciliation.assignment_terminal is False


def test_wrong_authority_is_rejected() -> None:
    with pytest.raises(
        ValueError, match="authority must be TransportDispatchReconciliationResolutionAuthority"
    ):
        _build_boundary(authority="EGRESS_ROUTING_SERVER")


def test_blank_boundary_id_is_rejected() -> None:
    with pytest.raises(ValueError, match="boundary_id must be a non-blank string"):
        _build_boundary(boundary_id="   ")


def test_wrong_unresolved_type_is_rejected() -> None:
    unresolved_boundary = _build_unresolved_boundary(status=RouteReconciliationStatus.REQUIRED)
    resolved_state = _build_resolved_state(
        unresolved_boundary,
        target_status=RouteReconciliationStatus.RESOLVED_NOT_SENT,
        resolved_outcome_reference="resolved-outcome-01",
    )
    with pytest.raises(
        ValueError,
        match="unresolved_reconciliation must be TransportDispatchReconciliationBoundary",
    ):
        _build_boundary(
            unresolved_reconciliation=object(),
            resolved_reconciliation_state=resolved_state,
        )


def test_wrong_resolved_state_type_is_rejected() -> None:
    with pytest.raises(
        ValueError, match="resolved_reconciliation_state must be RouteReconciliationState"
    ):
        _build_boundary(resolved_reconciliation_state=object())


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("resolution_committed", 1),
        ("new_dispatch_effect_authorized", 1),
        ("assignment_terminal", 1),
    ],
)
def test_invalid_bool_types_are_rejected(field_name: str, value: object) -> None:
    with pytest.raises(ValueError, match="must be a bool"):
        if field_name == "resolution_committed":
            _build_boundary(resolution_committed=value)
        elif field_name == "new_dispatch_effect_authorized":
            _build_boundary(new_dispatch_effect_authorized=value)
        else:
            _build_boundary(assignment_terminal=value)


def test_resolution_committed_false_is_rejected() -> None:
    with pytest.raises(ValueError, match="resolution_committed must be True"):
        _build_boundary(resolution_committed=False)


def test_new_dispatch_effect_authorized_true_is_rejected() -> None:
    with pytest.raises(ValueError, match="new_dispatch_effect_authorized must be False"):
        _build_boundary(new_dispatch_effect_authorized=True)


def test_assignment_terminal_false_is_rejected() -> None:
    with pytest.raises(ValueError, match="assignment_terminal must be True"):
        _build_boundary(assignment_terminal=False)


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("reason_codes", tuple()),
        ("reason_codes", ["reason-code-01"]),
        ("reason_codes", (" ",)),
        ("evidence_reference_ids", tuple()),
        ("evidence_reference_ids", ["evidence-01"]),
        ("evidence_reference_ids", (" ",)),
    ],
)
def test_invalid_or_empty_top_level_tuples_are_rejected(
    field_name: str,
    value: object,
) -> None:
    with pytest.raises(ValueError):
        if field_name == "reason_codes":
            _build_boundary(reason_codes=value)
        else:
            _build_boundary(evidence_reference_ids=value)


@pytest.mark.parametrize("invalid_status", EXPECTED_INVALID_SOURCE_STATUSES)
def test_invalid_source_statuses_are_rejected(
    invalid_status: RouteReconciliationStatus,
) -> None:
    boundary = _build_unresolved_boundary(status=RouteReconciliationStatus.REQUIRED)
    _mutate(boundary.reconciliation_state, status=invalid_status)
    with pytest.raises(
        ValueError, match="unresolved_reconciliation.reconciliation_state.status must be unresolved"
    ):
        _build_boundary(unresolved_reconciliation=boundary)


def test_source_resolved_outcome_reference_non_none_is_rejected() -> None:
    boundary = _build_unresolved_boundary(status=RouteReconciliationStatus.REQUIRED)
    _mutate(boundary.reconciliation_state, resolved_outcome_reference="opaque-outcome-01")
    with pytest.raises(ValueError, match="resolved_outcome_reference must be None"):
        _build_boundary(unresolved_reconciliation=boundary)


@pytest.mark.parametrize("invalid_status", EXPECTED_INVALID_TARGET_STATUSES)
def test_invalid_target_statuses_are_rejected(
    invalid_status: RouteReconciliationStatus,
) -> None:
    boundary = _build_unresolved_boundary(status=RouteReconciliationStatus.REQUIRED)
    resolved_state = _build_resolved_state(
        boundary,
        target_status=invalid_status,
        resolved_outcome_reference=None,
    )
    with pytest.raises(ValueError, match="resolved_reconciliation_state.status must be resolved"):
        _build_boundary(
            unresolved_reconciliation=boundary,
            resolved_reconciliation_state=resolved_state,
            resolved_outcome_reference=None,
        )


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("reconciliation_id", " "),
        ("assignment_id", " "),
        ("attempt_id", " "),
    ],
)
def test_blank_target_identities_are_rejected(field_name: str, value: str) -> None:
    boundary = _build_unresolved_boundary(status=RouteReconciliationStatus.REQUIRED)
    resolved_state = _build_resolved_state(
        boundary,
        target_status=RouteReconciliationStatus.RESOLVED_NOT_SENT,
        resolved_outcome_reference="resolved-outcome-01",
    )
    _mutate(resolved_state, **{field_name: value})
    with pytest.raises(
        ValueError, match=f"resolved_reconciliation_state.{field_name} must be a non-blank string"
    ):
        if field_name == "reconciliation_id":
            _build_boundary(
                unresolved_reconciliation=boundary,
                resolved_reconciliation_state=resolved_state,
            )
        elif field_name == "assignment_id":
            _build_boundary(
                unresolved_reconciliation=boundary,
                resolved_reconciliation_state=resolved_state,
            )
        else:
            _build_boundary(
                unresolved_reconciliation=boundary,
                resolved_reconciliation_state=resolved_state,
            )


def test_blank_resolved_outcome_reference_is_rejected() -> None:
    boundary = _build_unresolved_boundary(status=RouteReconciliationStatus.REQUIRED)
    resolved_state = _build_resolved_state(
        boundary,
        target_status=RouteReconciliationStatus.RESOLVED_SENT,
        resolved_outcome_reference="resolved-outcome-01",
    )
    _mutate(resolved_state, resolved_outcome_reference="   ")
    with pytest.raises(
        ValueError,
        match="resolved_reconciliation_state.resolved_outcome_reference must be a non-blank string",
    ):
        _build_boundary(
            unresolved_reconciliation=boundary,
            resolved_reconciliation_state=resolved_state,
        )


def test_reconciliation_mismatch_is_rejected() -> None:
    boundary = _build_unresolved_boundary(status=RouteReconciliationStatus.REQUIRED)
    resolved_state = _build_resolved_state(
        boundary,
        target_status=RouteReconciliationStatus.RESOLVED_NOT_SENT,
        resolved_outcome_reference="resolved-outcome-01",
    )
    _mutate(resolved_state, reconciliation_id="reconciliation-02")
    with pytest.raises(
        ValueError, match="resolved_reconciliation_state.reconciliation_id must match"
    ):
        _build_boundary(
            unresolved_reconciliation=boundary,
            resolved_reconciliation_state=resolved_state,
        )


def test_assignment_mismatch_is_rejected() -> None:
    boundary = _build_unresolved_boundary(status=RouteReconciliationStatus.REQUIRED)
    resolved_state = _build_resolved_state(
        boundary,
        target_status=RouteReconciliationStatus.RESOLVED_NOT_SENT,
        resolved_outcome_reference="resolved-outcome-01",
    )
    _mutate(resolved_state, assignment_id="assignment-02")
    with pytest.raises(ValueError, match="resolved_reconciliation_state.assignment_id must match"):
        _build_boundary(
            unresolved_reconciliation=boundary,
            resolved_reconciliation_state=resolved_state,
        )


def test_attempt_mismatch_is_rejected() -> None:
    boundary = _build_unresolved_boundary(status=RouteReconciliationStatus.REQUIRED)
    resolved_state = _build_resolved_state(
        boundary,
        target_status=RouteReconciliationStatus.RESOLVED_NOT_SENT,
        resolved_outcome_reference="resolved-outcome-01",
    )
    _mutate(resolved_state, attempt_id="attempt-02")
    with pytest.raises(ValueError, match="resolved_reconciliation_state.attempt_id must match"):
        _build_boundary(
            unresolved_reconciliation=boundary,
            resolved_reconciliation_state=resolved_state,
        )


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("reason_codes", tuple()),
        ("reason_codes", ["resolution-reason-01"]),
        ("reason_codes", (" ",)),
        ("evidence_reference_ids", tuple()),
        ("evidence_reference_ids", ["resolution-evidence-01"]),
        ("evidence_reference_ids", (" ",)),
    ],
)
def test_invalid_target_reason_and_evidence_tuples_are_rejected(
    field_name: str,
    value: object,
) -> None:
    boundary = _build_unresolved_boundary(status=RouteReconciliationStatus.REQUIRED)
    resolved_state = _build_resolved_state(
        boundary,
        target_status=RouteReconciliationStatus.RESOLVED_TERMINAL,
        resolved_outcome_reference="resolved-outcome-01",
    )
    _mutate(resolved_state, **{field_name: value})
    with pytest.raises(ValueError):
        if field_name == "reason_codes":
            _build_boundary(
                unresolved_reconciliation=boundary,
                resolved_reconciliation_state=resolved_state,
            )
        else:
            _build_boundary(
                unresolved_reconciliation=boundary,
                resolved_reconciliation_state=resolved_state,
            )
