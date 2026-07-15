# ruff: noqa: I001

from __future__ import annotations

from dataclasses import fields, is_dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

import mayak.modules.egress_routing as egress_routing
import mayak.modules.egress_routing.fixtures as fixtures_module
import mayak.modules.egress_routing.outcome_availability as outcome_availability_module
import tests.contract.test_egress_routing_outcome_contracts as outcome_contracts
from mayak.modules.egress_routing import (
    DispatchStatus,
    ER07B_TASK_ID,
    EGRESS_SYNTHETIC_FIXTURES,
    EGRESS_SYNTHETIC_FIXTURE_IDS,
    RouteReconciliationStatus,
    TransportAssignmentOutcome,
    TransportAvailabilityOutcomeAuthority,
    TransportAvailabilityOutcomeBoundary,
    TransportDispatchAttemptBoundary,
    TransportDispatchAuthority,
    TransportOutcomeStatus,
)

EXPECTED_TASK_ID = "ER-07B-TRANSPORT-AVAILABILITY-OUTCOME-BOUNDARY-20260715-017"

EXPECTED_MODULE_EXPORTS = (
    "ER07B_TASK_ID",
    "TransportAvailabilityOutcomeAuthority",
    "TransportAvailabilityOutcomeBoundary",
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

EXPECTED_FIELD_NAMES = (
    "boundary_id",
    "authority",
    "dispatch_attempt",
    "outcome",
    "outcome_committed",
    "new_dispatch_effect_authorized",
    "assignment_terminal",
    "parser_success_inferred",
    "scan_success_inferred",
    "notification_delivery_inferred",
    "reason_codes",
    "evidence_reference_ids",
)

EXPECTED_AUTHORITY_MATRIX = (("EGRESS_ROUTING_SERVER", "EGRESS_ROUTING_SERVER"),)

EXPECTED_DISPATCH_OUTCOME_MATRIX = {
    DispatchStatus.NOT_SENT: TransportOutcomeStatus.TRANSPORT_UNAVAILABLE,
    DispatchStatus.SENT: TransportOutcomeStatus.TRANSPORT_TIMEOUT,
    DispatchStatus.UNKNOWN: TransportOutcomeStatus.TRANSPORT_AMBIGUOUS,
}

EXPECTED_RECONCILIATION_MATRIX = {
    TransportOutcomeStatus.TRANSPORT_UNAVAILABLE: (
        RouteReconciliationStatus.NOT_REQUIRED,
        RouteReconciliationStatus.RESOLVED_NOT_SENT,
        RouteReconciliationStatus.RESOLVED_TERMINAL,
    ),
    TransportOutcomeStatus.TRANSPORT_TIMEOUT: (
        RouteReconciliationStatus.NOT_REQUIRED,
        RouteReconciliationStatus.RESOLVED_SENT,
        RouteReconciliationStatus.RESOLVED_TERMINAL,
    ),
    TransportOutcomeStatus.TRANSPORT_AMBIGUOUS: (
        RouteReconciliationStatus.REQUIRED,
        RouteReconciliationStatus.PENDING,
        RouteReconciliationStatus.REMAINS_AMBIGUOUS,
        RouteReconciliationStatus.MANUAL_REVIEW_REQUIRED,
    ),
}

EXPECTED_VALID_CASES = (
    (
        DispatchStatus.NOT_SENT,
        TransportOutcomeStatus.TRANSPORT_UNAVAILABLE,
        RouteReconciliationStatus.NOT_REQUIRED,
        True,
    ),
    (
        DispatchStatus.NOT_SENT,
        TransportOutcomeStatus.TRANSPORT_UNAVAILABLE,
        RouteReconciliationStatus.RESOLVED_NOT_SENT,
        True,
    ),
    (
        DispatchStatus.NOT_SENT,
        TransportOutcomeStatus.TRANSPORT_UNAVAILABLE,
        RouteReconciliationStatus.RESOLVED_TERMINAL,
        True,
    ),
    (
        DispatchStatus.SENT,
        TransportOutcomeStatus.TRANSPORT_TIMEOUT,
        RouteReconciliationStatus.NOT_REQUIRED,
        True,
    ),
    (
        DispatchStatus.SENT,
        TransportOutcomeStatus.TRANSPORT_TIMEOUT,
        RouteReconciliationStatus.RESOLVED_SENT,
        True,
    ),
    (
        DispatchStatus.SENT,
        TransportOutcomeStatus.TRANSPORT_TIMEOUT,
        RouteReconciliationStatus.RESOLVED_TERMINAL,
        True,
    ),
    (
        DispatchStatus.UNKNOWN,
        TransportOutcomeStatus.TRANSPORT_AMBIGUOUS,
        RouteReconciliationStatus.REQUIRED,
        False,
    ),
    (
        DispatchStatus.UNKNOWN,
        TransportOutcomeStatus.TRANSPORT_AMBIGUOUS,
        RouteReconciliationStatus.PENDING,
        False,
    ),
    (
        DispatchStatus.UNKNOWN,
        TransportOutcomeStatus.TRANSPORT_AMBIGUOUS,
        RouteReconciliationStatus.REMAINS_AMBIGUOUS,
        False,
    ),
    (
        DispatchStatus.UNKNOWN,
        TransportOutcomeStatus.TRANSPORT_AMBIGUOUS,
        RouteReconciliationStatus.MANUAL_REVIEW_REQUIRED,
        False,
    ),
)

EXPECTED_FORBIDDEN_OUTCOMES = (
    TransportOutcomeStatus.NOT_SENT,
    TransportOutcomeStatus.DISPATCH_REJECTED,
    TransportOutcomeStatus.DISPATCH_UNKNOWN,
    TransportOutcomeStatus.SENT_NO_RESPONSE,
    TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
    TransportOutcomeStatus.USABLE_RESPONSE_TRANSPORT_ONLY,
    TransportOutcomeStatus.RATE_OR_ACCESS_RESTRICTED,
    TransportOutcomeStatus.CAPTCHA_OR_CHALLENGE,
    TransportOutcomeStatus.PROVIDER_REJECTED,
    TransportOutcomeStatus.MALFORMED_RESPONSE_TRANSPORT_LAYER,
    TransportOutcomeStatus.ROUTE_QUARANTINED,
    TransportOutcomeStatus.ROUTE_DEGRADED,
    TransportOutcomeStatus.NO_APPROVED_ROUTE_AVAILABLE,
    TransportOutcomeStatus.POLICY_FALLBACK_ATTEMPTED,
    TransportOutcomeStatus.POLICY_FALLBACK_EXHAUSTED,
    TransportOutcomeStatus.RECONCILIATION_REQUIRED,
)

EXPECTED_PRIOR_DISPATCH_OUTCOME_MATRIX = {
    DispatchStatus.NOT_SENT: (TransportOutcomeStatus.NOT_SENT,),
    DispatchStatus.REJECTED: (TransportOutcomeStatus.DISPATCH_REJECTED,),
    DispatchStatus.UNKNOWN: (
        TransportOutcomeStatus.DISPATCH_UNKNOWN,
        TransportOutcomeStatus.RECONCILIATION_REQUIRED,
    ),
    DispatchStatus.SENT: (
        TransportOutcomeStatus.SENT_NO_RESPONSE,
        TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
        TransportOutcomeStatus.USABLE_RESPONSE_TRANSPORT_ONLY,
        TransportOutcomeStatus.RATE_OR_ACCESS_RESTRICTED,
        TransportOutcomeStatus.CAPTCHA_OR_CHALLENGE,
        TransportOutcomeStatus.PROVIDER_REJECTED,
        TransportOutcomeStatus.MALFORMED_RESPONSE_TRANSPORT_LAYER,
    ),
}

EXPECTED_PRIOR_RECONCILIATION_MATRIX = {
    DispatchStatus.NOT_SENT: (
        RouteReconciliationStatus.NOT_REQUIRED,
        RouteReconciliationStatus.RESOLVED_NOT_SENT,
        RouteReconciliationStatus.RESOLVED_TERMINAL,
    ),
    DispatchStatus.REJECTED: (
        RouteReconciliationStatus.NOT_REQUIRED,
        RouteReconciliationStatus.RESOLVED_NOT_SENT,
        RouteReconciliationStatus.RESOLVED_TERMINAL,
    ),
    DispatchStatus.UNKNOWN: (
        RouteReconciliationStatus.REQUIRED,
        RouteReconciliationStatus.PENDING,
        RouteReconciliationStatus.REMAINS_AMBIGUOUS,
        RouteReconciliationStatus.MANUAL_REVIEW_REQUIRED,
    ),
    DispatchStatus.SENT: (
        RouteReconciliationStatus.NOT_REQUIRED,
        RouteReconciliationStatus.RESOLVED_SENT,
        RouteReconciliationStatus.RESOLVED_TERMINAL,
    ),
}

EXPECTED_PRIOR_DEFERRED_STATUSES = (
    TransportOutcomeStatus.TRANSPORT_UNAVAILABLE,
    TransportOutcomeStatus.TRANSPORT_TIMEOUT,
    TransportOutcomeStatus.TRANSPORT_AMBIGUOUS,
    TransportOutcomeStatus.ROUTE_QUARANTINED,
    TransportOutcomeStatus.ROUTE_DEGRADED,
    TransportOutcomeStatus.NO_APPROVED_ROUTE_AVAILABLE,
    TransportOutcomeStatus.POLICY_FALLBACK_ATTEMPTED,
    TransportOutcomeStatus.POLICY_FALLBACK_EXHAUSTED,
)

UNSET = object()


class TextLike(str):
    pass


class TupleLike(tuple):
    pass


def _mutate(record: object, **changes: object) -> None:
    for field_name, value in changes.items():
        object.__setattr__(record, field_name, value)


def _build_state(
    *,
    dispatch_status: DispatchStatus,
    outcome_status: TransportOutcomeStatus,
    **kwargs: object,
) -> dict[str, object]:
    state = outcome_contracts._build_state(
        dispatch_status=dispatch_status,
        outcome_status=outcome_status,
        **kwargs,
    )
    state["authority"] = TransportAvailabilityOutcomeAuthority.EGRESS_ROUTING_SERVER
    return state


def _build_boundary(
    *,
    dispatch_status: DispatchStatus,
    outcome_status: TransportOutcomeStatus,
    **kwargs: object,
) -> TransportAvailabilityOutcomeBoundary:
    state = _build_state(dispatch_status=dispatch_status, outcome_status=outcome_status, **kwargs)
    boundary = TransportAvailabilityOutcomeBoundary(**_boundary_kwargs(state))  # type: ignore[arg-type]
    assert isinstance(boundary, TransportAvailabilityOutcomeBoundary)
    return boundary


def _boundary_kwargs(state: dict[str, object]) -> dict[str, object]:
    return {
        "boundary_id": state["boundary_id"],
        "authority": state["authority"],
        "dispatch_attempt": state["dispatch_boundary"],
        "outcome": state["outcome"],
        "outcome_committed": state["outcome_committed"],
        "new_dispatch_effect_authorized": state["new_dispatch_effect_authorized"],
        "assignment_terminal": state["assignment_terminal"],
        "parser_success_inferred": state["parser_success_inferred"],
        "scan_success_inferred": state["scan_success_inferred"],
        "notification_delivery_inferred": state["notification_delivery_inferred"],
        "reason_codes": state["reason_codes"],
        "evidence_reference_ids": state["evidence_reference_ids"],
    }


def _field_names(*records: object) -> set[str]:
    names: set[str] = set()
    for record in records:
        names.update(field.name for field in fields(cast(Any, record)))
    return names


def _snapshot(record: object) -> tuple[object, ...]:
    dataclass_record = cast(Any, record)
    return tuple(getattr(dataclass_record, field.name) for field in fields(dataclass_record))


def test_task_id_is_bound_to_the_module_exactly_once() -> None:
    source = Path(outcome_availability_module.__file__).read_text()
    assert ER07B_TASK_ID == EXPECTED_TASK_ID
    assert source.count(EXPECTED_TASK_ID) == 1


def test_module_exports_are_exact() -> None:
    assert outcome_availability_module.__all__ == EXPECTED_MODULE_EXPORTS
    assert tuple(outcome_availability_module.__all__) == EXPECTED_MODULE_EXPORTS
    assert type(outcome_availability_module.__all__) is tuple
    assert len(set(outcome_availability_module.__all__)) == len(EXPECTED_MODULE_EXPORTS)
    assert all(hasattr(outcome_availability_module, name) for name in EXPECTED_MODULE_EXPORTS)


def test_package_exports_are_exact() -> None:
    assert type(egress_routing.__all__) is tuple
    assert egress_routing.__all__ == EXPECTED_PACKAGE_EXPORTS
    assert tuple(egress_routing.__all__) == EXPECTED_PACKAGE_EXPORTS
    assert len(set(egress_routing.__all__)) == len(EXPECTED_PACKAGE_EXPORTS)
    assert all(hasattr(egress_routing, name) for name in EXPECTED_PACKAGE_EXPORTS)


def test_authority_matrix_is_exact() -> None:
    assert (
        tuple((member.name, member.value) for member in TransportAvailabilityOutcomeAuthority)
        == (EXPECTED_AUTHORITY_MATRIX[0],)
    )
    assert len(TransportAvailabilityOutcomeAuthority) == 1


def test_boundary_shape_is_exact() -> None:
    assert is_dataclass(TransportAvailabilityOutcomeBoundary)
    assert (
        TransportAvailabilityOutcomeBoundary.__dataclass_params__.frozen is True  # type: ignore[attr-defined]
    )
    assert (
        TransportAvailabilityOutcomeBoundary.__dataclass_params__.slots is True  # type: ignore[attr-defined]
    )
    assert tuple(field.name for field in fields(TransportAvailabilityOutcomeBoundary)) == (
        EXPECTED_FIELD_NAMES
    )


@pytest.mark.parametrize(
    ("dispatch_status", "outcome_status", "reconciliation_status", "assignment_terminal"),
    EXPECTED_VALID_CASES,
)
def test_valid_dispatch_and_outcome_matrices_are_accepted(
    dispatch_status: DispatchStatus,
    outcome_status: TransportOutcomeStatus,
    reconciliation_status: RouteReconciliationStatus,
    assignment_terminal: bool,
) -> None:
    boundary = _build_boundary(
        dispatch_status=dispatch_status,
        outcome_status=outcome_status,
        reconciliation_status=reconciliation_status,
        assignment_terminal=assignment_terminal,
    )
    assert boundary.authority is TransportAvailabilityOutcomeAuthority.EGRESS_ROUTING_SERVER
    assert boundary.dispatch_attempt.authority is TransportDispatchAuthority.EGRESS_ROUTING_SERVER
    assert boundary.dispatch_attempt.dispatch_state_committed is True
    assert boundary.dispatch_attempt.new_dispatch_effect_authorized is False
    assert boundary.dispatch_attempt.assignment_commitment.assignment_committed is True
    assert boundary.dispatch_attempt.attempt.attempt_ordinal == 1
    assert boundary.dispatch_attempt.attempt.outcome_reference is None
    assert boundary.outcome.status is outcome_status
    assert boundary.outcome.safe_response_reference is None
    assert boundary.outcome.reconciliation_status is reconciliation_status
    assert boundary.assignment_terminal is assignment_terminal
    assert boundary.outcome_committed is True
    assert boundary.new_dispatch_effect_authorized is False
    assert boundary.parser_success_inferred is False
    assert boundary.scan_success_inferred is False
    assert boundary.notification_delivery_inferred is False


def test_text_fields_reject_blank_values() -> None:
    kwargs = _boundary_kwargs(
        _build_state(
            dispatch_status=DispatchStatus.NOT_SENT,
            outcome_status=TransportOutcomeStatus.TRANSPORT_UNAVAILABLE,
        )
    )
    kwargs["boundary_id"] = " "
    with pytest.raises(ValueError):
        TransportAvailabilityOutcomeBoundary(**kwargs)  # type: ignore[arg-type]

    state = _build_state(
        dispatch_status=DispatchStatus.NOT_SENT,
        outcome_status=TransportOutcomeStatus.TRANSPORT_UNAVAILABLE,
    )
    outcome = cast(object, state["outcome"])
    _mutate(outcome, outcome_id=" ")
    kwargs = _boundary_kwargs(state)
    with pytest.raises(ValueError):
        TransportAvailabilityOutcomeBoundary(**kwargs)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("target", "field_name"),
    (
        ("attempt", "attempt_id"),
        ("attempt", "assignment_id"),
        ("attempt", "lease_id"),
        ("attempt", "route_id"),
        ("attempt", "agent_id"),
        ("attempt", "correlation_id"),
        ("attempt", "causation_id"),
        ("assignment", "assignment_id"),
        ("assignment", "lease_id"),
        ("assignment", "route_id"),
        ("assignment", "agent_id"),
        ("assignment", "correlation_id"),
        ("assignment", "causation_id"),
        ("outcome", "outcome_id"),
        ("outcome", "assignment_id"),
        ("outcome", "attempt_id"),
        ("outcome", "correlation_id"),
        ("outcome", "causation_id"),
    ),
)
def test_nested_identity_text_fields_reject_blank_values(
    target: str, field_name: str
) -> None:
    state = _build_state(
        dispatch_status=DispatchStatus.NOT_SENT,
        outcome_status=TransportOutcomeStatus.TRANSPORT_UNAVAILABLE,
    )
    dispatch_boundary = cast(TransportDispatchAttemptBoundary, state["dispatch_boundary"])
    target_record = {
        "attempt": dispatch_boundary.attempt,
        "assignment": dispatch_boundary.assignment_commitment.assignment,
        "outcome": state["outcome"],
    }[target]
    _mutate(target_record, **{field_name: " "})
    kwargs = _boundary_kwargs(state)
    with pytest.raises(ValueError):
        TransportAvailabilityOutcomeBoundary(**kwargs)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("boundary_id", TextLike("boundary-01")),
        ("dispatch_attempt", SimpleNamespace()),
        ("outcome", SimpleNamespace()),
        ("authority", SimpleNamespace()),
    ],
)
def test_wrong_authority_and_type_are_rejected(field_name: str, value: object) -> None:
    kwargs = _boundary_kwargs(
        _build_state(
            dispatch_status=DispatchStatus.NOT_SENT,
            outcome_status=TransportOutcomeStatus.TRANSPORT_UNAVAILABLE,
        )
    )
    kwargs[field_name] = value
    with pytest.raises(ValueError):
        TransportAvailabilityOutcomeBoundary(**kwargs)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("outcome_committed", False),
        ("outcome_committed", 1),
        ("new_dispatch_effect_authorized", True),
        ("new_dispatch_effect_authorized", 1),
        ("parser_success_inferred", True),
        ("scan_success_inferred", True),
        ("notification_delivery_inferred", True),
    ],
)
def test_top_level_bool_fields_reject_wrong_values(
    field_name: str, value: object
) -> None:
    kwargs = _boundary_kwargs(
        _build_state(
            dispatch_status=DispatchStatus.NOT_SENT,
            outcome_status=TransportOutcomeStatus.TRANSPORT_UNAVAILABLE,
        )
    )
    kwargs[field_name] = value
    with pytest.raises(ValueError):
        TransportAvailabilityOutcomeBoundary(**kwargs)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("dispatch_state_committed", False),
        ("dispatch_state_committed", 1),
        ("new_dispatch_effect_authorized", True),
        ("new_dispatch_effect_authorized", 1),
        ("assignment_committed", False),
        ("assignment_committed", 1),
    ],
)
def test_nested_dispatch_bool_fields_reject_wrong_values(
    field_name: str, value: object
) -> None:
    state = _build_state(
        dispatch_status=DispatchStatus.NOT_SENT,
        outcome_status=TransportOutcomeStatus.TRANSPORT_UNAVAILABLE,
    )
    dispatch_boundary = cast(TransportDispatchAttemptBoundary, state["dispatch_boundary"])
    if field_name == "assignment_committed":
        _mutate(dispatch_boundary.assignment_commitment, assignment_committed=value)
    else:
        _mutate(dispatch_boundary, **{field_name: value})
    kwargs = _boundary_kwargs(state)
    with pytest.raises(ValueError):
        TransportAvailabilityOutcomeBoundary(**kwargs)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("reason_codes", ()),
        ("reason_codes", ["reason-code-01"]),
        ("reason_codes", {"reason-code-01"}),
        ("reason_codes", (item for item in ("reason-code-01",))),
        ("reason_codes", TupleLike(("reason-code-01",))),
        ("reason_codes", (" ",)),
        ("evidence_reference_ids", ()),
        ("evidence_reference_ids", ["evidence-01"]),
        ("evidence_reference_ids", {"evidence-01"}),
        ("evidence_reference_ids", (item for item in ("evidence-01",))),
        ("evidence_reference_ids", TupleLike(("evidence-01",))),
        ("evidence_reference_ids", (" ",)),
    ],
)
def test_top_level_tuple_fields_reject_invalid_values(
    field_name: str, value: object
) -> None:
    kwargs = _boundary_kwargs(
        _build_state(
            dispatch_status=DispatchStatus.NOT_SENT,
            outcome_status=TransportOutcomeStatus.TRANSPORT_UNAVAILABLE,
        )
    )
    kwargs[field_name] = value
    with pytest.raises(ValueError):
        TransportAvailabilityOutcomeBoundary(**kwargs)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("reason_codes", ()),
        ("reason_codes", ["reason-code-01"]),
        ("reason_codes", {"reason-code-01"}),
        ("reason_codes", (item for item in ("reason-code-01",))),
        ("reason_codes", TupleLike(("reason-code-01",))),
        ("reason_codes", (" ",)),
        ("evidence_reference_ids", ()),
        ("evidence_reference_ids", ["evidence-01"]),
        ("evidence_reference_ids", {"evidence-01"}),
        ("evidence_reference_ids", (item for item in ("evidence-01",))),
        ("evidence_reference_ids", TupleLike(("evidence-01",))),
        ("evidence_reference_ids", (" ",)),
    ],
)
def test_outcome_tuple_fields_reject_invalid_values(field_name: str, value: object) -> None:
    state = _build_state(
        dispatch_status=DispatchStatus.NOT_SENT,
        outcome_status=TransportOutcomeStatus.TRANSPORT_UNAVAILABLE,
    )
    outcome = cast(object, state["outcome"])
    _mutate(outcome, **{field_name: value})
    kwargs = _boundary_kwargs(state)
    with pytest.raises(ValueError):
        TransportAvailabilityOutcomeBoundary(**kwargs)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("authority", SimpleNamespace()),
        ("dispatch_state_committed", False),
        ("new_dispatch_effect_authorized", True),
    ],
)
def test_nested_dispatch_gate_rejects_invalid_state(
    field_name: str, value: object
) -> None:
    state = _build_state(
        dispatch_status=DispatchStatus.NOT_SENT,
        outcome_status=TransportOutcomeStatus.TRANSPORT_UNAVAILABLE,
    )
    dispatch_boundary = cast(TransportDispatchAttemptBoundary, state["dispatch_boundary"])
    _mutate(dispatch_boundary, **{field_name: value})
    kwargs = _boundary_kwargs(state)
    with pytest.raises(ValueError):
        TransportAvailabilityOutcomeBoundary(**kwargs)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "dispatch_status",
    (
        DispatchStatus.PENDING,
        DispatchStatus.ATTEMPTED,
        DispatchStatus.ACKNOWLEDGED,
        DispatchStatus.REJECTED,
    ),
)
def test_rejected_dispatch_statuses_are_not_accepted(dispatch_status: DispatchStatus) -> None:
    state = _build_state(
        dispatch_status=DispatchStatus.NOT_SENT,
        outcome_status=TransportOutcomeStatus.TRANSPORT_UNAVAILABLE,
    )
    dispatch_boundary = cast(TransportDispatchAttemptBoundary, state["dispatch_boundary"])
    _mutate(dispatch_boundary.attempt, dispatch_status=dispatch_status)
    kwargs = _boundary_kwargs(state)
    with pytest.raises(ValueError):
        TransportAvailabilityOutcomeBoundary(**kwargs)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("dispatch_status", "allowed_outcome"),
    tuple(EXPECTED_DISPATCH_OUTCOME_MATRIX.items()),
)
def test_dispatch_outcome_matrix_is_exact(
    dispatch_status: DispatchStatus,
    allowed_outcome: TransportOutcomeStatus,
) -> None:
    for outcome_status in TransportOutcomeStatus:
        state = _build_state(
            dispatch_status=dispatch_status,
            outcome_status=allowed_outcome,
            assignment_terminal=allowed_outcome is not TransportOutcomeStatus.TRANSPORT_AMBIGUOUS,
        )
        outcome = cast(TransportAssignmentOutcome, state["outcome"])
        _mutate(outcome, status=outcome_status)
        kwargs = _boundary_kwargs(state)
        if outcome_status is allowed_outcome:
            boundary = TransportAvailabilityOutcomeBoundary(**kwargs)  # type: ignore[arg-type]
            assert boundary.outcome.status is allowed_outcome
            assert boundary.dispatch_attempt.attempt.dispatch_status is dispatch_status
        else:
            with pytest.raises(ValueError):
                TransportAvailabilityOutcomeBoundary(**kwargs)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("outcome_status", "allowed_reconciliations"),
    tuple(EXPECTED_RECONCILIATION_MATRIX.items()),
)
def test_reconciliation_matrix_is_exact(
    outcome_status: TransportOutcomeStatus,
    allowed_reconciliations: tuple[RouteReconciliationStatus, ...],
) -> None:
    for reconciliation_status in RouteReconciliationStatus:
        base_reconciliation_status = (
            reconciliation_status
            if reconciliation_status in allowed_reconciliations
            else allowed_reconciliations[0]
        )
        state = _build_state(
            dispatch_status={
                TransportOutcomeStatus.TRANSPORT_UNAVAILABLE: DispatchStatus.NOT_SENT,
                TransportOutcomeStatus.TRANSPORT_TIMEOUT: DispatchStatus.SENT,
                TransportOutcomeStatus.TRANSPORT_AMBIGUOUS: DispatchStatus.UNKNOWN,
            }[outcome_status],
            outcome_status=outcome_status,
            reconciliation_status=base_reconciliation_status,
            assignment_terminal=outcome_status is not TransportOutcomeStatus.TRANSPORT_AMBIGUOUS,
        )
        if reconciliation_status is not base_reconciliation_status:
            outcome = cast(object, state["outcome"])
            _mutate(outcome, reconciliation_status=reconciliation_status)
        kwargs = _boundary_kwargs(state)
        if reconciliation_status in allowed_reconciliations:
            boundary = TransportAvailabilityOutcomeBoundary(**kwargs)  # type: ignore[arg-type]
            assert boundary.outcome.reconciliation_status is reconciliation_status
        else:
            with pytest.raises(ValueError):
                TransportAvailabilityOutcomeBoundary(**kwargs)  # type: ignore[arg-type]


def test_safe_response_reference_is_always_none() -> None:
    state = _build_state(
        dispatch_status=DispatchStatus.NOT_SENT,
        outcome_status=TransportOutcomeStatus.TRANSPORT_UNAVAILABLE,
    )
    outcome = cast(object, state["outcome"])
    _mutate(outcome, safe_response_reference="safe-response-01")
    kwargs = _boundary_kwargs(state)
    with pytest.raises(ValueError):
        TransportAvailabilityOutcomeBoundary(**kwargs)  # type: ignore[arg-type]


def test_wrong_assignment_terminal_is_rejected() -> None:
    for (
        dispatch_status,
        outcome_status,
        reconciliation_status,
        assignment_terminal,
    ) in EXPECTED_VALID_CASES:
        state = _build_state(
            dispatch_status=dispatch_status,
            outcome_status=outcome_status,
            reconciliation_status=reconciliation_status,
            assignment_terminal=assignment_terminal,
        )
        kwargs = _boundary_kwargs(state)
        kwargs["assignment_terminal"] = not assignment_terminal
        with pytest.raises(ValueError):
            TransportAvailabilityOutcomeBoundary(**kwargs)  # type: ignore[arg-type]


def test_false_success_flags_remain_false() -> None:
    state = _build_state(
        dispatch_status=DispatchStatus.NOT_SENT,
        outcome_status=TransportOutcomeStatus.TRANSPORT_UNAVAILABLE,
    )
    kwargs = _boundary_kwargs(state)
    for field_name in (
        "parser_success_inferred",
        "scan_success_inferred",
        "notification_delivery_inferred",
    ):
        mutated = dict(kwargs)
        mutated[field_name] = True
        with pytest.raises(ValueError):
            TransportAvailabilityOutcomeBoundary(**mutated)  # type: ignore[arg-type]


@pytest.mark.parametrize("status", EXPECTED_FORBIDDEN_OUTCOMES)
def test_all_other_transport_outcomes_are_rejected(status: TransportOutcomeStatus) -> None:
    state = _build_state(
        dispatch_status=DispatchStatus.NOT_SENT,
        outcome_status=TransportOutcomeStatus.TRANSPORT_UNAVAILABLE,
    )
    outcome = cast(object, state["outcome"])
    _mutate(outcome, status=status)
    kwargs = _boundary_kwargs(state)
    with pytest.raises(ValueError):
        TransportAvailabilityOutcomeBoundary(**kwargs)  # type: ignore[arg-type]


def test_identity_linkage_is_preserved() -> None:
    boundary = _build_boundary(
        dispatch_status=DispatchStatus.NOT_SENT,
        outcome_status=TransportOutcomeStatus.TRANSPORT_UNAVAILABLE,
    )
    assignment = boundary.dispatch_attempt.assignment_commitment.assignment
    attempt = boundary.dispatch_attempt.attempt
    outcome = boundary.outcome

    assert outcome.outcome_id == "outcome-01"
    assert outcome.assignment_id == assignment.assignment_id
    assert outcome.attempt_id == attempt.attempt_id
    assert outcome.correlation_id == assignment.correlation_id == attempt.correlation_id
    assert outcome.causation_id == assignment.causation_id == attempt.causation_id
    assert (
        boundary.dispatch_attempt.assignment_commitment.assignment.assignment_id
        == attempt.assignment_id
    )
    assert boundary.dispatch_attempt.assignment_commitment.assignment.lease_id == attempt.lease_id
    assert boundary.dispatch_attempt.assignment_commitment.assignment.route_id == attempt.route_id
    assert boundary.dispatch_attempt.assignment_commitment.assignment.agent_id == attempt.agent_id


@pytest.mark.parametrize(
    ("field_name",),
    (
        ("assignment_id",),
        ("attempt_id",),
        ("correlation_id",),
        ("causation_id",),
    ),
)
def test_outcome_identity_mismatches_are_rejected(field_name: str) -> None:
    state = _build_state(
        dispatch_status=DispatchStatus.NOT_SENT,
        outcome_status=TransportOutcomeStatus.TRANSPORT_UNAVAILABLE,
    )
    outcome = cast(object, state["outcome"])
    _mutate(outcome, **{field_name: "mismatch"})
    kwargs = _boundary_kwargs(state)
    with pytest.raises(ValueError):
        TransportAvailabilityOutcomeBoundary(**kwargs)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("field_name",),
    (
        ("assignment_id",),
        ("lease_id",),
        ("route_id",),
        ("agent_id",),
        ("correlation_id",),
        ("causation_id",),
    ),
)
def test_attempt_identity_mismatches_are_rejected(field_name: str) -> None:
    state = _build_state(
        dispatch_status=DispatchStatus.NOT_SENT,
        outcome_status=TransportOutcomeStatus.TRANSPORT_UNAVAILABLE,
    )
    dispatch_boundary = cast(TransportDispatchAttemptBoundary, state["dispatch_boundary"])
    attempt = dispatch_boundary.attempt
    _mutate(attempt, **{field_name: "mismatch"})
    kwargs = _boundary_kwargs(state)
    with pytest.raises(ValueError):
        TransportAvailabilityOutcomeBoundary(**kwargs)  # type: ignore[arg-type]


def test_boundary_remains_immutable() -> None:
    boundary = _build_boundary(
        dispatch_status=DispatchStatus.SENT,
        outcome_status=TransportOutcomeStatus.TRANSPORT_TIMEOUT,
    )
    boundary_snapshot = _snapshot(boundary)
    dispatch_snapshot = _snapshot(boundary.dispatch_attempt)
    outcome_snapshot = _snapshot(boundary.outcome)

    with pytest.raises(Exception):
        boundary.boundary_id = "changed"  # type: ignore[misc]

    assert _snapshot(boundary) == boundary_snapshot
    assert _snapshot(boundary.dispatch_attempt) == dispatch_snapshot
    assert _snapshot(boundary.outcome) == outcome_snapshot


def test_no_blind_retry_or_second_attempt_is_created() -> None:
    boundary = _build_boundary(
        dispatch_status=DispatchStatus.UNKNOWN,
        outcome_status=TransportOutcomeStatus.TRANSPORT_AMBIGUOUS,
        reconciliation_status=RouteReconciliationStatus.REQUIRED,
        assignment_terminal=False,
    )
    field_names = _field_names(boundary, boundary.dispatch_attempt, boundary.outcome)
    assert boundary.dispatch_attempt.attempt.attempt_ordinal == 1
    assert boundary.dispatch_attempt.attempt.outcome_reference is None
    assert {"retry", "second_attempt", "replay", "fallback"}.isdisjoint(field_names)


def test_no_parser_scan_notification_object_is_created() -> None:
    boundary = _build_boundary(
        dispatch_status=DispatchStatus.NOT_SENT,
        outcome_status=TransportOutcomeStatus.TRANSPORT_UNAVAILABLE,
    )
    field_names = _field_names(boundary, boundary.dispatch_attempt, boundary.outcome)
    assert {"parser", "scan", "notification"}.isdisjoint({name.lower() for name in field_names})


def test_no_route_health_quarantine_fallback_mutation() -> None:
    boundary = _build_boundary(
        dispatch_status=DispatchStatus.SENT,
        outcome_status=TransportOutcomeStatus.TRANSPORT_TIMEOUT,
    )
    field_names = _field_names(boundary, boundary.dispatch_attempt, boundary.outcome)
    banned = {
        "route_health",
        "health",
        "quarantine",
        "fallback",
        "restriction",
        "degradation",
    }
    assert banned.isdisjoint({name.lower() for name in field_names})


def test_no_runtime_storage_provider_selection_behavior() -> None:
    boundary = _build_boundary(
        dispatch_status=DispatchStatus.NOT_SENT,
        outcome_status=TransportOutcomeStatus.TRANSPORT_UNAVAILABLE,
    )
    field_names = _field_names(boundary, boundary.dispatch_attempt, boundary.outcome)
    banned = {
        "runtime",
        "storage",
        "provider",
        "host",
        "hostname",
        "ip",
        "port",
        "timeout",
        "capacity",
    }
    assert banned.isdisjoint({name.lower() for name in field_names})


def test_prior_er07a_matrices_remain_unchanged() -> None:
    assert (
        outcome_contracts.EXPECTED_DISPATCH_TO_OUTCOME_MATRIX
        == EXPECTED_PRIOR_DISPATCH_OUTCOME_MATRIX
    )
    assert outcome_contracts.EXPECTED_RECONCILIATION_MATRIX == EXPECTED_PRIOR_RECONCILIATION_MATRIX
    assert outcome_contracts.EXPECTED_DEFERRED_STATUSES == EXPECTED_PRIOR_DEFERRED_STATUSES


def test_fixture_registry_remains_unchanged() -> None:
    assert len(EGRESS_SYNTHETIC_FIXTURES) == 34
    assert tuple(EGRESS_SYNTHETIC_FIXTURE_IDS) == tuple(
        fixture.fixture_id for fixture in fixtures_module.EGRESS_SYNTHETIC_FIXTURES
    )
    assert tuple(fixture.fixture_id for fixture in fixtures_module.EGRESS_SYNTHETIC_FIXTURES) == (
        EGRESS_SYNTHETIC_FIXTURE_IDS
    )
    assert Path(fixtures_module.__file__).read_text().count(fixtures_module.ER02_TASK_ID) == 1
