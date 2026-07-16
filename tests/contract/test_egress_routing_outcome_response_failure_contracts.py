from __future__ import annotations

from dataclasses import fields, is_dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

import mayak.modules.egress_routing as egress_routing
import mayak.modules.egress_routing.fixtures as fixtures_module
import mayak.modules.egress_routing.outcome_response_failure as failure_module
import tests.contract.test_egress_routing_outcome_availability_contracts as oavail_contracts
import tests.contract.test_egress_routing_outcome_contracts as outcome_contracts
import tests.contract.test_egress_routing_outcome_response_contracts as response_contracts
from mayak.modules.egress_routing import (
    ER07D_TASK_ID,
    DispatchAttempt,
    DispatchStatus,
    RouteReconciliationStatus,
    TransportAssignment,
    TransportAssignmentCommitmentBoundary,
    TransportAssignmentOutcome,
    TransportDispatchAttemptBoundary,
    TransportDispatchAuthority,
    TransportOutcomeStatus,
    TransportResponseFailureOutcomeAuthority,
    TransportResponseFailureOutcomeBoundary,
)

EXPECTED_TASK_ID = "ER-07D-TRANSPORT-RESPONSE-FAILURE-OUTCOME-BOUNDARY-20260715-021"

EXPECTED_MODULE_EXPORTS = (
    "ER07D_TASK_ID",
    "TransportResponseFailureOutcomeAuthority",
    "TransportResponseFailureOutcomeBoundary",
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
    "ER11A_TASK_ID",
    "DevelopmentBridgeAuthority",
    "DevelopmentBridgeGateBoundary",
    "ER07E_TASK_ID",
    "PolicyFallbackTransportOutcomeAuthority",
    "PolicyFallbackTransportOutcomeBoundary",
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

EXPECTED_OUTCOME_STATUSES = (
    TransportOutcomeStatus.RATE_OR_ACCESS_RESTRICTED,
    TransportOutcomeStatus.CAPTCHA_OR_CHALLENGE,
    TransportOutcomeStatus.PROVIDER_REJECTED,
    TransportOutcomeStatus.MALFORMED_RESPONSE_TRANSPORT_LAYER,
)

EXPECTED_RECONCILIATION_STATUSES = (
    RouteReconciliationStatus.NOT_REQUIRED,
    RouteReconciliationStatus.RESOLVED_SENT,
    RouteReconciliationStatus.RESOLVED_TERMINAL,
)

SAFE_RESPONSE_REFERENCE_BY_STATUS = {
    TransportOutcomeStatus.RATE_OR_ACCESS_RESTRICTED: "opaque-safe-response-01",
    TransportOutcomeStatus.CAPTCHA_OR_CHALLENGE: "opaque-safe-response-02",
    TransportOutcomeStatus.PROVIDER_REJECTED: "opaque-safe-response-03",
    TransportOutcomeStatus.MALFORMED_RESPONSE_TRANSPORT_LAYER: "opaque-safe-response-04",
}

RECONCILIATION_LOOKALIKE = SimpleNamespace(name="NOT_REQUIRED", value="NOT_REQUIRED")
AUTHORITY_LOOKALIKE = SimpleNamespace(name="EGRESS_ROUTING_SERVER", value="EGRESS_ROUTING_SERVER")
OUTCOME_STATUS_LOOKALIKE = SimpleNamespace(
    name="RATE_OR_ACCESS_RESTRICTED",
    value="RATE_OR_ACCESS_RESTRICTED",
)
RECONCILIATION_STATUS_LOOKALIKE = SimpleNamespace(
    name="NOT_REQUIRED",
    value="NOT_REQUIRED",
)


class TextLike(str):
    pass


class TupleLike(tuple):
    pass


INVALID_SAFE_RESPONSE_REFERENCE_VARIANTS = (
    " ",
    TextLike("opaque-safe-response"),
    b"opaque-safe-response",
    ["opaque-safe-response"],
    {"safe_response_reference": "opaque-safe-response"},
    SimpleNamespace(safe_response_reference="opaque-safe-response"),
)

EXPECTED_SAFE_RESPONSE_REFERENCE_NEGATIVE_COMBINATIONS = 24


def _mutate(record: object, **changes: object) -> None:
    for field_name, value in changes.items():
        object.__setattr__(record, field_name, value)


def _build_state(
    *,
    outcome_status: TransportOutcomeStatus,
    safe_response_reference: object,
    reconciliation_status: object,
    dispatch_status: DispatchStatus = DispatchStatus.SENT,
) -> dict[str, object]:
    state = outcome_contracts._build_state(
        dispatch_status=dispatch_status,
        outcome_status=outcome_status,
        safe_response_reference=safe_response_reference,
        reconciliation_status=reconciliation_status,
    )
    state["authority"] = TransportResponseFailureOutcomeAuthority.EGRESS_ROUTING_SERVER
    return state


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


def _build_boundary(
    *,
    outcome_status: TransportOutcomeStatus,
    safe_response_reference: object,
    reconciliation_status: object,
    dispatch_status: DispatchStatus = DispatchStatus.SENT,
) -> TransportResponseFailureOutcomeBoundary:
    state = _build_state(
        outcome_status=outcome_status,
        safe_response_reference=safe_response_reference,
        reconciliation_status=reconciliation_status,
        dispatch_status=dispatch_status,
    )
    boundary = TransportResponseFailureOutcomeBoundary(**_boundary_kwargs(state))  # type: ignore[arg-type]
    assert type(boundary) is TransportResponseFailureOutcomeBoundary
    return boundary


def _dispatch_boundary(state: dict[str, object]) -> TransportDispatchAttemptBoundary:
    dispatch_boundary = state["dispatch_boundary"]
    assert type(dispatch_boundary) is TransportDispatchAttemptBoundary
    return dispatch_boundary


def _outcome(state: dict[str, object]) -> TransportAssignmentOutcome:
    outcome = state["outcome"]
    assert type(outcome) is TransportAssignmentOutcome
    return outcome


def _field_names(*records: object) -> set[str]:
    names: set[str] = set()
    for record in records:
        names.update(field.name for field in fields(cast(Any, record)))
    return names


def _as_lookalike(record: object) -> SimpleNamespace:
    payload = {field.name: getattr(record, field.name) for field in fields(cast(Any, record))}
    return SimpleNamespace(**payload)


def test_task_id_is_bound_to_the_module_exactly_once() -> None:
    source = Path(failure_module.__file__).read_text()
    assert ER07D_TASK_ID == EXPECTED_TASK_ID
    assert source.count(EXPECTED_TASK_ID) == 1


def test_module_exports_are_exact() -> None:
    assert failure_module.__all__ == EXPECTED_MODULE_EXPORTS
    assert tuple(failure_module.__all__) == EXPECTED_MODULE_EXPORTS
    assert type(failure_module.__all__) is tuple
    assert len(set(failure_module.__all__)) == len(EXPECTED_MODULE_EXPORTS)
    assert all(hasattr(failure_module, name) for name in EXPECTED_MODULE_EXPORTS)


def test_package_exports_are_exact() -> None:
    assert type(egress_routing.__all__) is tuple
    assert egress_routing.__all__ == EXPECTED_PACKAGE_EXPORTS
    assert tuple(egress_routing.__all__) == EXPECTED_PACKAGE_EXPORTS
    assert len(set(egress_routing.__all__)) == len(EXPECTED_PACKAGE_EXPORTS)
    assert all(hasattr(egress_routing, name) for name in EXPECTED_PACKAGE_EXPORTS)


def test_authority_matrix_is_exact() -> None:
    assert (
        tuple((member.name, member.value) for member in TransportResponseFailureOutcomeAuthority)
        == EXPECTED_AUTHORITY_MATRIX
    )
    assert len(TransportResponseFailureOutcomeAuthority) == 1


def test_boundary_shape_is_exact() -> None:
    assert is_dataclass(TransportResponseFailureOutcomeBoundary)
    assert (
        TransportResponseFailureOutcomeBoundary.__dataclass_params__.frozen is True  # type: ignore[attr-defined]
    )
    assert (
        TransportResponseFailureOutcomeBoundary.__dataclass_params__.slots is True  # type: ignore[attr-defined]
    )
    assert tuple(field.name for field in fields(TransportResponseFailureOutcomeBoundary)) == (
        EXPECTED_FIELD_NAMES
    )


@pytest.mark.parametrize(
    ("outcome_status", "reconciliation_status", "safe_response_reference"),
    tuple(
        (outcome_status, reconciliation_status, safe_response_reference)
        for outcome_status in EXPECTED_OUTCOME_STATUSES
        for reconciliation_status in EXPECTED_RECONCILIATION_STATUSES
        for safe_response_reference in (None, SAFE_RESPONSE_REFERENCE_BY_STATUS[outcome_status])
    ),
)
def test_twenty_four_positive_transport_failure_combinations_are_accepted(
    outcome_status: TransportOutcomeStatus,
    reconciliation_status: RouteReconciliationStatus,
    safe_response_reference: str | None,
) -> None:
    boundary = _build_boundary(
        outcome_status=outcome_status,
        safe_response_reference=safe_response_reference,
        reconciliation_status=reconciliation_status,
    )

    assert type(boundary) is TransportResponseFailureOutcomeBoundary
    assert type(boundary.dispatch_attempt) is TransportDispatchAttemptBoundary
    assert (
        type(boundary.dispatch_attempt.assignment_commitment)
        is TransportAssignmentCommitmentBoundary
    )
    assert type(boundary.dispatch_attempt.attempt) is DispatchAttempt
    assert type(boundary.dispatch_attempt.assignment_commitment.assignment) is TransportAssignment
    assert type(boundary.outcome) is TransportAssignmentOutcome
    assert boundary.authority is TransportResponseFailureOutcomeAuthority.EGRESS_ROUTING_SERVER
    assert boundary.outcome_committed is True
    assert boundary.new_dispatch_effect_authorized is False
    assert boundary.assignment_terminal is True
    assert boundary.parser_success_inferred is False
    assert boundary.scan_success_inferred is False
    assert boundary.notification_delivery_inferred is False
    assert boundary.dispatch_attempt.authority is TransportDispatchAuthority.EGRESS_ROUTING_SERVER
    assert boundary.dispatch_attempt.dispatch_state_committed is True
    assert boundary.dispatch_attempt.new_dispatch_effect_authorized is False
    assert boundary.dispatch_attempt.assignment_commitment.assignment_committed is True
    assert boundary.dispatch_attempt.attempt.dispatch_status is DispatchStatus.SENT
    assert boundary.dispatch_attempt.attempt.attempt_ordinal == 1
    assert boundary.dispatch_attempt.attempt.outcome_reference is None
    assert boundary.outcome.status is outcome_status
    assert boundary.outcome.reconciliation_status is reconciliation_status
    assert boundary.outcome.safe_response_reference is safe_response_reference
    assert type(boundary.reason_codes) is tuple
    assert type(boundary.evidence_reference_ids) is tuple
    assert type(boundary.outcome.reason_codes) is tuple
    assert type(boundary.outcome.evidence_reference_ids) is tuple
    assignment = boundary.dispatch_attempt.assignment_commitment.assignment
    attempt = boundary.dispatch_attempt.attempt
    assert boundary.dispatch_attempt.attempt.assignment_id == assignment.assignment_id
    assert boundary.dispatch_attempt.attempt.lease_id == assignment.lease_id
    assert boundary.dispatch_attempt.attempt.route_id == assignment.route_id
    assert boundary.dispatch_attempt.attempt.agent_id == assignment.agent_id
    assert boundary.dispatch_attempt.attempt.correlation_id == assignment.correlation_id
    assert boundary.dispatch_attempt.attempt.causation_id == assignment.causation_id
    assert boundary.outcome.assignment_id == assignment.assignment_id
    assert boundary.outcome.attempt_id == attempt.attempt_id
    assert boundary.outcome.correlation_id == assignment.correlation_id
    assert boundary.outcome.causation_id == assignment.causation_id


@pytest.mark.parametrize(
    "dispatch_status",
    tuple(status for status in DispatchStatus if status is not DispatchStatus.SENT),
)
def test_all_other_dispatch_statuses_are_rejected(dispatch_status: DispatchStatus) -> None:
    state = _build_state(
        outcome_status=TransportOutcomeStatus.RATE_OR_ACCESS_RESTRICTED,
        safe_response_reference="opaque-safe-response-01",
        reconciliation_status=RouteReconciliationStatus.NOT_REQUIRED,
    )
    _mutate(_dispatch_boundary(state).attempt, dispatch_status=dispatch_status)
    with pytest.raises(ValueError):
        TransportResponseFailureOutcomeBoundary(**_boundary_kwargs(state))  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "outcome_status",
    tuple(status for status in TransportOutcomeStatus if status not in EXPECTED_OUTCOME_STATUSES),
)
def test_all_other_outcome_statuses_are_rejected(outcome_status: TransportOutcomeStatus) -> None:
    state = _build_state(
        outcome_status=TransportOutcomeStatus.RATE_OR_ACCESS_RESTRICTED,
        safe_response_reference="opaque-safe-response-01",
        reconciliation_status=RouteReconciliationStatus.NOT_REQUIRED,
    )
    _mutate(_outcome(state), status=outcome_status)
    with pytest.raises(ValueError):
        TransportResponseFailureOutcomeBoundary(**_boundary_kwargs(state))  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "reconciliation_status",
    tuple(
        status
        for status in RouteReconciliationStatus
        if status not in EXPECTED_RECONCILIATION_STATUSES
    ),
)
def test_all_other_reconciliation_statuses_are_rejected(
    reconciliation_status: RouteReconciliationStatus,
) -> None:
    state = _build_state(
        outcome_status=TransportOutcomeStatus.RATE_OR_ACCESS_RESTRICTED,
        safe_response_reference="opaque-safe-response-01",
        reconciliation_status=RouteReconciliationStatus.NOT_REQUIRED,
    )
    _mutate(_outcome(state), reconciliation_status=reconciliation_status)
    with pytest.raises(ValueError):
        TransportResponseFailureOutcomeBoundary(**_boundary_kwargs(state))  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("field_path", "bad_value"),
    (
        ("authority", "EGRESS_ROUTING_SERVER"),
        ("authority", TextLike("EGRESS_ROUTING_SERVER")),
        ("authority", AUTHORITY_LOOKALIKE),
        ("dispatch_boundary.attempt.dispatch_status", "SENT"),
        ("dispatch_boundary.attempt.dispatch_status", TextLike("SENT")),
        ("dispatch_boundary.attempt.dispatch_status", SimpleNamespace(name="SENT", value="SENT")),
        ("outcome.status", "RATE_OR_ACCESS_RESTRICTED"),
        ("outcome.status", TextLike("RATE_OR_ACCESS_RESTRICTED")),
        ("outcome.status", OUTCOME_STATUS_LOOKALIKE),
        ("outcome.reconciliation_status", "NOT_REQUIRED"),
        ("outcome.reconciliation_status", TextLike("NOT_REQUIRED")),
        ("outcome.reconciliation_status", RECONCILIATION_STATUS_LOOKALIKE),
    ),
)
def test_exact_enum_values_reject_plain_strings_subclasses_and_lookalikes(
    field_path: str,
    bad_value: object,
) -> None:
    state = _build_state(
        outcome_status=TransportOutcomeStatus.RATE_OR_ACCESS_RESTRICTED,
        safe_response_reference="opaque-safe-response-01",
        reconciliation_status=RouteReconciliationStatus.NOT_REQUIRED,
    )
    if field_path == "authority":
        state["authority"] = bad_value
    elif field_path == "dispatch_boundary.attempt.dispatch_status":
        _mutate(_dispatch_boundary(state).attempt, dispatch_status=bad_value)
    elif field_path == "outcome.status":
        _mutate(_outcome(state), status=bad_value)
    else:
        _mutate(_outcome(state), reconciliation_status=bad_value)
    with pytest.raises(ValueError):
        TransportResponseFailureOutcomeBoundary(**_boundary_kwargs(state))  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "field_name",
    ("dispatch_attempt", "outcome", "assignment_commitment", "attempt", "assignment"),
)
def test_nested_records_require_exact_dataclass_types(field_name: str) -> None:
    state = _build_state(
        outcome_status=TransportOutcomeStatus.PROVIDER_REJECTED,
        safe_response_reference="opaque-safe-response-03",
        reconciliation_status=RouteReconciliationStatus.RESOLVED_TERMINAL,
    )
    dispatch_boundary = _dispatch_boundary(state)
    if field_name == "dispatch_attempt":
        state["dispatch_boundary"] = _as_lookalike(dispatch_boundary)
    elif field_name == "outcome":
        state["outcome"] = _as_lookalike(_outcome(state))
    elif field_name == "assignment_commitment":
        _mutate(
            dispatch_boundary,
            assignment_commitment=_as_lookalike(dispatch_boundary.assignment_commitment),
        )
    elif field_name == "attempt":
        _mutate(dispatch_boundary, attempt=_as_lookalike(dispatch_boundary.attempt))
    else:
        _mutate(
            dispatch_boundary.assignment_commitment,
            assignment=_as_lookalike(dispatch_boundary.assignment_commitment.assignment),
        )
    with pytest.raises(ValueError):
        TransportResponseFailureOutcomeBoundary(**_boundary_kwargs(state))  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("field_name", "bad_value"),
    (
        ("dispatch_boundary.attempt.attempt_id", TextLike("attempt-01")),
        ("dispatch_boundary.attempt.attempt_id", " "),
        ("dispatch_boundary.attempt.attempt_id", b"attempt-01"),
        ("dispatch_boundary.attempt.attempt_id", SimpleNamespace(attempt_id="attempt-01")),
        ("outcome.outcome_id", TextLike("outcome-01")),
        ("outcome.outcome_id", " "),
        ("outcome.outcome_id", b"outcome-01"),
        ("outcome.outcome_id", SimpleNamespace(outcome_id="outcome-01")),
        ("outcome.outcome_id", TextLike("outcome-01")),
    ),
)
def test_exact_ids_and_primitives_require_builtin_types(
    field_name: str,
    bad_value: object,
) -> None:
    state = _build_state(
        outcome_status=TransportOutcomeStatus.MALFORMED_RESPONSE_TRANSPORT_LAYER,
        safe_response_reference=None,
        reconciliation_status=RouteReconciliationStatus.RESOLVED_SENT,
    )
    if field_name.startswith("dispatch_boundary.attempt."):
        _mutate(_dispatch_boundary(state).attempt, **{field_name.rsplit(".", 1)[-1]: bad_value})
    else:
        _mutate(_outcome(state), outcome_id=bad_value)
    with pytest.raises(ValueError):
        TransportResponseFailureOutcomeBoundary(**_boundary_kwargs(state))  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("field_name", "bad_value"),
    (
        ("outcome_committed", 1),
        ("new_dispatch_effect_authorized", 1),
        ("assignment_terminal", 0),
        ("parser_success_inferred", 1),
        ("scan_success_inferred", 0),
        ("notification_delivery_inferred", 1),
    ),
)
def test_bool_fields_require_exact_builtin_bools(field_name: str, bad_value: object) -> None:
    state = _build_state(
        outcome_status=TransportOutcomeStatus.CAPTCHA_OR_CHALLENGE,
        safe_response_reference=None,
        reconciliation_status=RouteReconciliationStatus.RESOLVED_SENT,
    )
    state[field_name] = bad_value
    with pytest.raises(ValueError):
        TransportResponseFailureOutcomeBoundary(**_boundary_kwargs(state))  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("field_path", "bad_value"),
    (
        ("reason_codes", ["reason-01"]),
        ("reason_codes", {"reason-01"}),
        ("reason_codes", iter(("reason-01",))),
        ("reason_codes", TupleLike(("reason-01",))),
        ("reason_codes", ("reason-01", " ")),
        ("evidence_reference_ids", ["evidence-01"]),
        ("evidence_reference_ids", {"evidence-01"}),
        ("evidence_reference_ids", iter(("evidence-01",))),
        ("evidence_reference_ids", TupleLike(("evidence-01",))),
        ("evidence_reference_ids", ("evidence-01", " ")),
        ("outcome.reason_codes", ["reason-01"]),
        ("outcome.reason_codes", {"reason-01"}),
        ("outcome.reason_codes", iter(("reason-01",))),
        ("outcome.reason_codes", TupleLike(("reason-01",))),
        ("outcome.reason_codes", ("reason-01", " ")),
        ("outcome.evidence_reference_ids", ["evidence-01"]),
        ("outcome.evidence_reference_ids", {"evidence-01"}),
        ("outcome.evidence_reference_ids", iter(("evidence-01",))),
        ("outcome.evidence_reference_ids", TupleLike(("evidence-01",))),
        ("outcome.evidence_reference_ids", ("evidence-01", " ")),
    ),
)
def test_tuple_fields_require_exact_nonblank_tuples(
    field_path: str,
    bad_value: object,
) -> None:
    state = _build_state(
        outcome_status=TransportOutcomeStatus.PROVIDER_REJECTED,
        safe_response_reference="opaque-safe-response-03",
        reconciliation_status=RouteReconciliationStatus.RESOLVED_TERMINAL,
    )
    if field_path.startswith("outcome."):
        _mutate(_outcome(state), **{field_path.split(".", 1)[1]: bad_value})
    else:
        state[field_path] = bad_value
    with pytest.raises(ValueError):
        TransportResponseFailureOutcomeBoundary(**_boundary_kwargs(state))  # type: ignore[arg-type]


@pytest.mark.parametrize("outcome_status", EXPECTED_OUTCOME_STATUSES)
@pytest.mark.parametrize("bad_value", INVALID_SAFE_RESPONSE_REFERENCE_VARIANTS)
def test_safe_response_reference_requires_optional_builtin_text(
    outcome_status: TransportOutcomeStatus,
    bad_value: object,
) -> None:
    assert (
        len(EXPECTED_OUTCOME_STATUSES) * len(INVALID_SAFE_RESPONSE_REFERENCE_VARIANTS)
        == EXPECTED_SAFE_RESPONSE_REFERENCE_NEGATIVE_COMBINATIONS
    )
    state = _build_state(
        outcome_status=outcome_status,
        safe_response_reference="opaque-safe-response-01",
        reconciliation_status=RouteReconciliationStatus.NOT_REQUIRED,
    )
    _mutate(_outcome(state), safe_response_reference=bad_value)
    with pytest.raises(ValueError):
        TransportResponseFailureOutcomeBoundary(**_boundary_kwargs(state))  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "outcome_status",
    EXPECTED_OUTCOME_STATUSES,
)
@pytest.mark.parametrize("safe_response_reference", (None, "opaque-safe-response"))
def test_safe_response_reference_is_preserved_exactly(
    outcome_status: TransportOutcomeStatus,
    safe_response_reference: str | None,
) -> None:
    boundary = _build_boundary(
        outcome_status=outcome_status,
        safe_response_reference=safe_response_reference,
        reconciliation_status=RouteReconciliationStatus.RESOLVED_SENT,
    )
    assert boundary.outcome.safe_response_reference is safe_response_reference


@pytest.mark.parametrize(
    "field_name",
    (
        "attempt.assignment_id",
        "attempt.lease_id",
        "attempt.route_id",
        "attempt.agent_id",
        "attempt.correlation_id",
        "attempt.causation_id",
        "outcome.assignment_id",
        "outcome.attempt_id",
        "outcome.correlation_id",
        "outcome.causation_id",
    ),
)
def test_linkage_mutations_are_rejected(field_name: str) -> None:
    state = _build_state(
        outcome_status=TransportOutcomeStatus.PROVIDER_REJECTED,
        safe_response_reference="opaque-safe-response-03",
        reconciliation_status=RouteReconciliationStatus.RESOLVED_TERMINAL,
    )
    if field_name.startswith("attempt."):
        _mutate(_dispatch_boundary(state).attempt, **{field_name.split(".", 1)[1]: "mismatch"})
    else:
        _mutate(_outcome(state), **{field_name.split(".", 1)[1]: "mismatch"})
    with pytest.raises(ValueError):
        TransportResponseFailureOutcomeBoundary(**_boundary_kwargs(state))  # type: ignore[arg-type]


def test_no_forbidden_semantics_are_present() -> None:
    boundary = _build_boundary(
        outcome_status=TransportOutcomeStatus.MALFORMED_RESPONSE_TRANSPORT_LAYER,
        safe_response_reference=None,
        reconciliation_status=RouteReconciliationStatus.RESOLVED_SENT,
    )
    field_names = _field_names(boundary, boundary.dispatch_attempt, boundary.outcome)
    forbidden = {
        "Parser",
        "Scan",
        "Notification",
        "response_payload",
        "response_body",
        "receipt_payload",
        "send_payload",
        "content",
        "listing",
        "baseline",
        "anchor",
        "route_health",
        "health",
        "quarantine",
        "fallback",
        "second_attempt",
        "retry_attempt",
        "retry",
        "backoff",
        "captcha_solver",
        "captcha_bypass",
        "provider",
        "proxy",
        "vpn",
        "tunnel",
        "runtime",
        "storage",
        "network",
    }
    assert forbidden.isdisjoint(field_names)


def test_prior_state_regression_remains_unchanged() -> None:
    assert (
        Path(outcome_contracts.outcome_module.__file__)
        .read_text()
        .count(outcome_contracts.EXPECTED_TASK_ID)
        == 1
    )
    assert (
        Path(oavail_contracts.outcome_availability_module.__file__)
        .read_text()
        .count(oavail_contracts.EXPECTED_TASK_ID)
        == 1
    )
    assert (
        Path(response_contracts.outcome_response_module.__file__)
        .read_text()
        .count(response_contracts.EXPECTED_TASK_ID)
        == 1
    )
    assert outcome_contracts.EXPECTED_DISPATCH_TO_OUTCOME_MATRIX == {
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
    assert oavail_contracts.EXPECTED_DISPATCH_OUTCOME_MATRIX == {
        DispatchStatus.NOT_SENT: TransportOutcomeStatus.TRANSPORT_UNAVAILABLE,
        DispatchStatus.SENT: TransportOutcomeStatus.TRANSPORT_TIMEOUT,
        DispatchStatus.UNKNOWN: TransportOutcomeStatus.TRANSPORT_AMBIGUOUS,
    }
    assert oavail_contracts.EXPECTED_RECONCILIATION_MATRIX == {
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
    assert oavail_contracts.EXPECTED_VALID_CASES == (
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
    assert response_contracts.EXPECTED_OUTCOME_STATUS_MATRIX == (
        TransportOutcomeStatus.SENT_NO_RESPONSE,
        TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
        TransportOutcomeStatus.USABLE_RESPONSE_TRANSPORT_ONLY,
    )
    assert response_contracts.EXPECTED_RECONCILIATION_STATUSES == (
        RouteReconciliationStatus.NOT_REQUIRED,
        RouteReconciliationStatus.RESOLVED_SENT,
        RouteReconciliationStatus.RESOLVED_TERMINAL,
    )
    assert response_contracts.SAFE_RESPONSE_REFERENCE_BY_OUTCOME_STATUS == {
        TransportOutcomeStatus.SENT_NO_RESPONSE: None,
        TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED: "opaque-safe-response-01",
        TransportOutcomeStatus.USABLE_RESPONSE_TRANSPORT_ONLY: "opaque-safe-response-02",
    }
    assert len(fixtures_module.EGRESS_SYNTHETIC_FIXTURE_IDS) == 34
    assert tuple(fixtures_module.EGRESS_SYNTHETIC_FIXTURE_IDS) == tuple(
        egress_routing.EGRESS_SYNTHETIC_FIXTURE_IDS
    )
    assert (
        tuple(egress_routing.__all__[: egress_routing.__all__.index("ER07D_TASK_ID")])
        == tuple(
            response_contracts.EXPECTED_PACKAGE_EXPORTS[
                : response_contracts.EXPECTED_PACKAGE_EXPORTS.index("ER07D_TASK_ID")
            ]
        )
    )
