# ruff: noqa: I001

from __future__ import annotations

from dataclasses import fields, is_dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

import mayak.modules.egress_routing as egress_routing
import mayak.modules.egress_routing.fixtures as fixtures_module
import mayak.modules.egress_routing.outcome_response as outcome_response_module
import tests.contract.test_egress_routing_outcome_availability_contracts as oavail_contracts
import tests.contract.test_egress_routing_outcome_contracts as outcome_contracts
from mayak.modules.egress_routing import (
    DispatchAttempt,
    DispatchStatus,
    ER07C_TASK_ID,
    RouteReconciliationStatus,
    TransportAssignment,
    TransportAssignmentCommitmentBoundary,
    TransportAssignmentOutcome,
    TransportDispatchAttemptBoundary,
    TransportDispatchAuthority,
    TransportOutcomeStatus,
    TransportResponsePresenceOutcomeAuthority,
    TransportResponsePresenceOutcomeBoundary,
)

EXPECTED_TASK_ID = "ER-07C-TRANSPORT-RESPONSE-PRESENCE-OUTCOME-BOUNDARY-20260715-019"

EXPECTED_MODULE_EXPORTS = (
    "ER07C_TASK_ID",
    "TransportResponsePresenceOutcomeAuthority",
    "TransportResponsePresenceOutcomeBoundary",
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

EXPECTED_OUTCOME_STATUS_MATRIX = (
    TransportOutcomeStatus.SENT_NO_RESPONSE,
    TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
    TransportOutcomeStatus.USABLE_RESPONSE_TRANSPORT_ONLY,
)

EXPECTED_RECONCILIATION_STATUSES = (
    RouteReconciliationStatus.NOT_REQUIRED,
    RouteReconciliationStatus.RESOLVED_SENT,
    RouteReconciliationStatus.RESOLVED_TERMINAL,
)

SAFE_RESPONSE_REFERENCE_BY_OUTCOME_STATUS = {
    TransportOutcomeStatus.SENT_NO_RESPONSE: None,
    TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED: "opaque-safe-response-01",
    TransportOutcomeStatus.USABLE_RESPONSE_TRANSPORT_ONLY: "opaque-safe-response-02",
}

RECONCILIATION_LOOKALIKE = SimpleNamespace(
    name="NOT_REQUIRED",
    value="NOT_REQUIRED",
)


class TextLike(str):
    pass


class TupleLike(tuple):
    pass


def _mutate(record: object, **changes: object) -> None:
    for field_name, value in changes.items():
        object.__setattr__(record, field_name, value)


def _build_state(
    *,
    dispatch_status: DispatchStatus = DispatchStatus.SENT,
    outcome_status: TransportOutcomeStatus,
    boundary_id: object = "outcome-response-boundary-01",
    authority: object = TransportResponsePresenceOutcomeAuthority.EGRESS_ROUTING_SERVER,
    outcome_committed: object = True,
    new_dispatch_effect_authorized: object = False,
    assignment_terminal: object = True,
    parser_success_inferred: object = False,
    scan_success_inferred: object = False,
    notification_delivery_inferred: object = False,
    reason_codes: object = ("transport-response-presence",),
    evidence_reference_ids: object = ("evidence-transport-response-presence-01",),
    safe_response_reference: object = None,
    reconciliation_status: object = RouteReconciliationStatus.NOT_REQUIRED,
) -> dict[str, object]:
    state = outcome_contracts._build_state(
        dispatch_status=dispatch_status,
        outcome_status=outcome_status,
        boundary_id=boundary_id,
        authority=authority,
        outcome_committed=outcome_committed,
        new_dispatch_effect_authorized=new_dispatch_effect_authorized,
        assignment_terminal=assignment_terminal,
        parser_success_inferred=parser_success_inferred,
        scan_success_inferred=scan_success_inferred,
        notification_delivery_inferred=notification_delivery_inferred,
        reason_codes=reason_codes,
        evidence_reference_ids=evidence_reference_ids,
        safe_response_reference=safe_response_reference,
        reconciliation_status=reconciliation_status,
    )
    state["authority"] = TransportResponsePresenceOutcomeAuthority.EGRESS_ROUTING_SERVER
    return state


def _build_boundary(
    *,
    dispatch_status: DispatchStatus,
    outcome_status: TransportOutcomeStatus,
    **kwargs: object,
) -> TransportResponsePresenceOutcomeBoundary:
    state = _build_state(dispatch_status=dispatch_status, outcome_status=outcome_status, **kwargs)
    boundary = TransportResponsePresenceOutcomeBoundary(**_boundary_kwargs(state))  # type: ignore[arg-type]
    assert type(boundary) is TransportResponsePresenceOutcomeBoundary
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


def _snapshot(record: object) -> tuple[object, ...]:
    dataclass_record = cast(Any, record)
    return tuple(getattr(dataclass_record, field.name) for field in fields(dataclass_record))


def _as_lookalike(record: object) -> SimpleNamespace:
    payload = {field.name: getattr(record, field.name) for field in fields(cast(Any, record))}
    return SimpleNamespace(**payload)


def test_task_id_is_bound_to_the_module_exactly_once() -> None:
    source = Path(outcome_response_module.__file__).read_text()
    assert ER07C_TASK_ID == EXPECTED_TASK_ID
    assert source.count(EXPECTED_TASK_ID) == 1


def test_module_exports_are_exact() -> None:
    assert outcome_response_module.__all__ == EXPECTED_MODULE_EXPORTS
    assert tuple(outcome_response_module.__all__) == EXPECTED_MODULE_EXPORTS
    assert type(outcome_response_module.__all__) is tuple
    assert len(set(outcome_response_module.__all__)) == len(EXPECTED_MODULE_EXPORTS)
    assert all(hasattr(outcome_response_module, name) for name in EXPECTED_MODULE_EXPORTS)


def test_package_exports_are_exact() -> None:
    assert type(egress_routing.__all__) is tuple
    assert egress_routing.__all__ == EXPECTED_PACKAGE_EXPORTS
    assert tuple(egress_routing.__all__) == EXPECTED_PACKAGE_EXPORTS
    assert len(set(egress_routing.__all__)) == len(EXPECTED_PACKAGE_EXPORTS)
    assert all(hasattr(egress_routing, name) for name in EXPECTED_PACKAGE_EXPORTS)


def test_authority_matrix_is_exact() -> None:
    assert (
        tuple((member.name, member.value) for member in TransportResponsePresenceOutcomeAuthority)
        == EXPECTED_AUTHORITY_MATRIX
    )
    assert len(TransportResponsePresenceOutcomeAuthority) == 1


def test_boundary_shape_is_exact() -> None:
    assert is_dataclass(TransportResponsePresenceOutcomeBoundary)
    assert (
        TransportResponsePresenceOutcomeBoundary.__dataclass_params__.frozen is True  # type: ignore[attr-defined]
    )
    assert (
        TransportResponsePresenceOutcomeBoundary.__dataclass_params__.slots is True  # type: ignore[attr-defined]
    )
    assert tuple(field.name for field in fields(TransportResponsePresenceOutcomeBoundary)) == (
        EXPECTED_FIELD_NAMES
    )


@pytest.mark.parametrize(
    ("outcome_status", "reconciliation_status"),
    tuple(
        (outcome_status, reconciliation_status)
        for outcome_status in EXPECTED_OUTCOME_STATUS_MATRIX
        for reconciliation_status in EXPECTED_RECONCILIATION_STATUSES
    ),
)
def test_nine_positive_outcome_and_reconciliation_combinations_are_accepted(
    outcome_status: TransportOutcomeStatus,
    reconciliation_status: RouteReconciliationStatus,
) -> None:
    boundary = _build_boundary(
        dispatch_status=DispatchStatus.SENT,
        outcome_status=outcome_status,
        safe_response_reference=SAFE_RESPONSE_REFERENCE_BY_OUTCOME_STATUS[outcome_status],
        reconciliation_status=reconciliation_status,
    )

    assert type(boundary) is TransportResponsePresenceOutcomeBoundary
    assert type(boundary.dispatch_attempt) is TransportDispatchAttemptBoundary
    assert (
        type(boundary.dispatch_attempt.assignment_commitment)
        is TransportAssignmentCommitmentBoundary
    )
    assert type(boundary.dispatch_attempt.attempt) is DispatchAttempt
    assert type(boundary.dispatch_attempt.assignment_commitment.assignment) is TransportAssignment
    assert type(boundary.outcome) is TransportAssignmentOutcome
    assert boundary.authority is TransportResponsePresenceOutcomeAuthority.EGRESS_ROUTING_SERVER
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
    assert type(boundary.dispatch_attempt.attempt.attempt_id) is str
    assert boundary.outcome.status is outcome_status
    assert boundary.outcome.reconciliation_status is reconciliation_status
    if outcome_status is TransportOutcomeStatus.SENT_NO_RESPONSE:
        assert boundary.outcome.safe_response_reference is None
    else:
        assert type(boundary.outcome.safe_response_reference) is str
        expected_safe_reference = SAFE_RESPONSE_REFERENCE_BY_OUTCOME_STATUS[outcome_status]
        assert boundary.outcome.safe_response_reference == expected_safe_reference
    assert type(boundary.reason_codes) is tuple
    assert type(boundary.evidence_reference_ids) is tuple
    assert type(boundary.outcome.reason_codes) is tuple
    assert type(boundary.outcome.evidence_reference_ids) is tuple


@pytest.mark.parametrize(
    "dispatch_status",
    tuple(status for status in DispatchStatus if status is not DispatchStatus.SENT),
)
def test_all_other_dispatch_statuses_are_rejected(dispatch_status: DispatchStatus) -> None:
    state = _build_state(
        dispatch_status=DispatchStatus.SENT,
        outcome_status=TransportOutcomeStatus.SENT_NO_RESPONSE,
    )
    _mutate(_dispatch_boundary(state).attempt, dispatch_status=dispatch_status)
    with pytest.raises(ValueError):
        TransportResponsePresenceOutcomeBoundary(**_boundary_kwargs(state))  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "outcome_status",
    tuple(
        status
        for status in TransportOutcomeStatus
        if status not in EXPECTED_OUTCOME_STATUS_MATRIX
    ),
)
def test_all_other_outcome_statuses_are_rejected(outcome_status: TransportOutcomeStatus) -> None:
    state = _build_state(outcome_status=TransportOutcomeStatus.SENT_NO_RESPONSE)
    _mutate(_outcome(state), status=outcome_status)
    with pytest.raises(ValueError):
        TransportResponsePresenceOutcomeBoundary(**_boundary_kwargs(state))  # type: ignore[arg-type]


def test_sentinel_dispatch_status_requires_exact_sent() -> None:
    state = _build_state(
        dispatch_status=DispatchStatus.SENT,
        outcome_status=TransportOutcomeStatus.SENT_NO_RESPONSE,
    )
    _mutate(_dispatch_boundary(state).attempt, dispatch_status=DispatchStatus.NOT_SENT)
    with pytest.raises(ValueError):
        TransportResponsePresenceOutcomeBoundary(**_boundary_kwargs(state))  # type: ignore[arg-type]


def test_plain_reconciliation_string_is_rejected() -> None:
    state = _build_state(outcome_status=TransportOutcomeStatus.SENT_NO_RESPONSE)
    _mutate(_outcome(state), reconciliation_status="NOT_REQUIRED")
    with pytest.raises(ValueError):
        TransportResponsePresenceOutcomeBoundary(**_boundary_kwargs(state))  # type: ignore[arg-type]


def test_reconciliation_str_subclass_is_rejected() -> None:
    state = _build_state(outcome_status=TransportOutcomeStatus.SENT_NO_RESPONSE)
    _mutate(_outcome(state), reconciliation_status=TextLike("NOT_REQUIRED"))
    with pytest.raises(ValueError):
        TransportResponsePresenceOutcomeBoundary(**_boundary_kwargs(state))  # type: ignore[arg-type]


def test_reconciliation_lookalike_object_is_rejected() -> None:
    state = _build_state(outcome_status=TransportOutcomeStatus.SENT_NO_RESPONSE)
    _mutate(_outcome(state), reconciliation_status=RECONCILIATION_LOOKALIKE)
    with pytest.raises(ValueError):
        TransportResponsePresenceOutcomeBoundary(**_boundary_kwargs(state))  # type: ignore[arg-type]


def test_safe_response_str_subclass_is_rejected() -> None:
    state = _build_state(
        outcome_status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
        safe_response_reference="opaque-safe-response",
        reconciliation_status=RouteReconciliationStatus.RESOLVED_SENT,
    )
    _mutate(_outcome(state), safe_response_reference=TextLike("opaque-safe-response"))
    with pytest.raises(ValueError):
        TransportResponsePresenceOutcomeBoundary(**_boundary_kwargs(state))  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("field_name", "bad_value"),
    (
        ("boundary_id", TextLike("boundary-01")),
        ("outcome.outcome_id", TextLike("outcome-01")),
        ("outcome_committed", 1),
    ),
)
def test_text_and_bool_fields_require_builtin_types(
    field_name: str,
    bad_value: object,
) -> None:
    state = _build_state(outcome_status=TransportOutcomeStatus.SENT_NO_RESPONSE)
    if field_name == "boundary_id":
        state["boundary_id"] = bad_value
    elif field_name == "outcome.outcome_id":
        _mutate(_outcome(state), outcome_id=bad_value)
    else:
        state[field_name] = bad_value
    with pytest.raises(ValueError):
        TransportResponsePresenceOutcomeBoundary(**_boundary_kwargs(state))  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("field_path", "bad_value"),
    (
        ("reason_codes", ["code-01"]),
        ("reason_codes", {"code-01"}),
        ("reason_codes", iter(("code-01",))),
        ("reason_codes", TupleLike(("code-01",))),
        ("reason_codes", ("code-01", " ")),
        ("outcome.reason_codes", ["code-01"]),
        ("outcome.reason_codes", {"code-01"}),
        ("outcome.reason_codes", iter(("code-01",))),
        ("outcome.reason_codes", TupleLike(("code-01",))),
        ("outcome.reason_codes", ("code-01", " ")),
        ("evidence_reference_ids", ["evidence-01"]),
        ("evidence_reference_ids", {"evidence-01"}),
        ("evidence_reference_ids", iter(("evidence-01",))),
        ("evidence_reference_ids", TupleLike(("evidence-01",))),
        ("evidence_reference_ids", ("evidence-01", " ")),
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
    state = _build_state(outcome_status=TransportOutcomeStatus.SENT_NO_RESPONSE)
    if field_path.startswith("outcome."):
        _mutate(_outcome(state), **{field_path.split(".", 1)[1]: bad_value})
    else:
        state[field_path] = bad_value
    with pytest.raises(ValueError):
        TransportResponsePresenceOutcomeBoundary(**_boundary_kwargs(state))  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "field_name",
    ("dispatch_attempt", "outcome", "assignment_commitment", "attempt", "assignment"),
)
def test_nested_records_require_exact_dataclass_types(field_name: str) -> None:
    state = _build_state(outcome_status=TransportOutcomeStatus.SENT_NO_RESPONSE)
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
        TransportResponsePresenceOutcomeBoundary(**_boundary_kwargs(state))  # type: ignore[arg-type]


def test_exact_builtin_attempt_id_is_accepted() -> None:
    boundary = _build_boundary(
        dispatch_status=DispatchStatus.SENT,
        outcome_status=TransportOutcomeStatus.SENT_NO_RESPONSE,
    )
    assert type(boundary.outcome.attempt_id) is str
    assert boundary.outcome.attempt_id == boundary.dispatch_attempt.attempt.attempt_id


@pytest.mark.parametrize(
    "bad_kind",
    ("text_subclass", "blank", "bytes", "lookalike"),
)
def test_attempt_id_requires_exact_builtin_nonblank_string(bad_kind: str) -> None:
    state = _build_state(outcome_status=TransportOutcomeStatus.SENT_NO_RESPONSE)
    valid_attempt_id = _dispatch_boundary(state).attempt.attempt_id
    if bad_kind == "text_subclass":
        bad_value: object = TextLike(valid_attempt_id)
    elif bad_kind == "blank":
        bad_value = " "
    elif bad_kind == "bytes":
        bad_value = valid_attempt_id.encode("utf-8")
    else:
        bad_value = SimpleNamespace(attempt_id=valid_attempt_id)
    _mutate(_dispatch_boundary(state).attempt, attempt_id=bad_value)
    with pytest.raises(ValueError):
        TransportResponsePresenceOutcomeBoundary(**_boundary_kwargs(state))  # type: ignore[arg-type]
    assert type(valid_attempt_id) is str
    assert valid_attempt_id == "attempt-01"


def test_assignment_terminal_false_is_rejected() -> None:
    state = _build_state(outcome_status=TransportOutcomeStatus.SENT_NO_RESPONSE)
    state["assignment_terminal"] = False
    with pytest.raises(ValueError):
        TransportResponsePresenceOutcomeBoundary(**_boundary_kwargs(state))  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "flag_name",
    ("parser_success_inferred", "scan_success_inferred", "notification_delivery_inferred"),
)
def test_success_inference_flags_true_are_rejected(flag_name: str) -> None:
    state = _build_state(outcome_status=TransportOutcomeStatus.SENT_NO_RESPONSE)
    state[flag_name] = True
    with pytest.raises(ValueError):
        TransportResponsePresenceOutcomeBoundary(**_boundary_kwargs(state))  # type: ignore[arg-type]


def test_no_second_attempt_retry_or_fallback_state_is_created() -> None:
    boundary = _build_boundary(
        dispatch_status=DispatchStatus.SENT,
        outcome_status=TransportOutcomeStatus.SENT_NO_RESPONSE,
    )
    field_names = _field_names(boundary, boundary.dispatch_attempt, boundary.outcome)
    assert {"second_attempt", "retry_attempt", "retry", "fallback"}.isdisjoint(field_names)


def test_no_parser_scan_or_notification_state_is_created() -> None:
    boundary = _build_boundary(
        dispatch_status=DispatchStatus.SENT,
        outcome_status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
        safe_response_reference="opaque-safe-response",
        reconciliation_status=RouteReconciliationStatus.RESOLVED_SENT,
    )
    field_names = _field_names(boundary, boundary.dispatch_attempt, boundary.outcome)
    assert {"Parser", "Scan", "Notification"}.isdisjoint(field_names)
    assert {"parser", "scan", "notification"}.isdisjoint(field_names)


def test_no_route_health_quarantine_or_fallback_mutation() -> None:
    boundary = _build_boundary(
        dispatch_status=DispatchStatus.SENT,
        outcome_status=TransportOutcomeStatus.USABLE_RESPONSE_TRANSPORT_ONLY,
        safe_response_reference="opaque-safe-response",
        reconciliation_status=RouteReconciliationStatus.RESOLVED_TERMINAL,
    )
    field_names = _field_names(boundary, boundary.dispatch_attempt, boundary.outcome)
    banned = {
        "route_health",
        "health",
        "quarantine",
        "fallback",
        "listing",
        "baseline",
        "anchor",
        "content",
        "classification",
    }
    assert banned.isdisjoint(field_names)


def test_fixture_registry_is_unchanged() -> None:
    assert len(fixtures_module.EGRESS_SYNTHETIC_FIXTURE_IDS) == 34
    assert len(fixtures_module.EGRESS_SYNTHETIC_FIXTURES) == 34
    assert tuple(fixtures_module.EGRESS_SYNTHETIC_FIXTURE_IDS) == tuple(
        egress_routing.EGRESS_SYNTHETIC_FIXTURE_IDS
    )
    assert tuple(fixtures_module.EGRESS_SYNTHETIC_FIXTURES) == tuple(
        egress_routing.EGRESS_SYNTHETIC_FIXTURES
    )


def test_prior_er07a_and_er07b_task_markers_and_matrices_remain_unchanged() -> None:
    assert Path(outcome_contracts.outcome_module.__file__).read_text().count(
        outcome_contracts.EXPECTED_TASK_ID
    ) == 1
    assert (
        Path(oavail_contracts.outcome_availability_module.__file__)
        .read_text()
        .count(oavail_contracts.EXPECTED_TASK_ID)
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
    assert outcome_contracts.EXPECTED_RECONCILIATION_MATRIX == {
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
