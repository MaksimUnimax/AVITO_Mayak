from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

import mayak.modules.egress_routing as egress_routing
import mayak.modules.egress_routing.restriction_evaluation as restriction_evaluation_module
import tests.contract.test_egress_routing_restriction_signal_contracts as signal_contracts
from mayak.modules.egress_routing import (
    ER08A_TASK_ID,
    ER08B_TASK_ID,
    DispatchAttempt,
    DispatchStatus,
    TransportAssignment,
    TransportAssignmentAuthority,
    TransportAssignmentCommitmentBoundary,
    TransportAssignmentOutcome,
    TransportDispatchAttemptBoundary,
    TransportDispatchAuthority,
    TransportOutcomeStatus,
    TransportResponseFailureOutcomeAuthority,
    TransportResponseFailureOutcomeBoundary,
    TransportRestrictionEvaluationAuthority,
    TransportRestrictionEvaluationGateBoundary,
    TransportRestrictionSignalAuthority,
    TransportRestrictionSignalBoundary,
    TransportRestrictionSignalKind,
)

EXPECTED_TASK_ID = "ER-08B-RESTRICTION-QUARANTINE-EVALUATION-GATE-20260716-041"

EXPECTED_MODULE_EXPORTS = (
    "ER08B_TASK_ID",
    "TransportRestrictionEvaluationAuthority",
    "TransportRestrictionEvaluationGateBoundary",
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
    "source_signal",
    "route_id",
    "evaluation_recorded",
    "restriction_policy_gate_satisfied",
    "quarantine_policy_gate_satisfied",
    "protected_review_required",
    "new_affected_lease_authorized",
    "new_affected_assignment_authorized",
    "restriction_state_commit_authorized",
    "quarantine_decision_commit_authorized",
    "fallback_effect_authorized",
    "automatic_unquarantine_authorized",
    "captcha_solving_authorized",
    "captcha_bypass_authorized",
    "parser_success_inferred",
    "scan_success_inferred",
    "notification_delivery_inferred",
    "reason_codes",
    "evidence_reference_ids",
)

EXPECTED_AUTHORITY_MATRIX = (("EGRESS_ROUTING_SERVER", "EGRESS_ROUTING_SERVER"),)

EXPECTED_ALLOWED_OUTCOME_STATUS_MATRIX = (
    (
        TransportOutcomeStatus.RATE_OR_ACCESS_RESTRICTED,
        TransportRestrictionSignalKind.EXPLICIT_RESTRICTION,
    ),
    (
        TransportOutcomeStatus.CAPTCHA_OR_CHALLENGE,
        TransportRestrictionSignalKind.EXPLICIT_CHALLENGE,
    ),
)

EXPECTED_REASON_CODES = (
    "restriction-evaluation-recorded",
    "quarantine-evaluation-recorded",
)

EXPECTED_EVIDENCE_REFERENCE_IDS = (
    "evidence-restriction-evaluation-01",
    "evidence-quarantine-evaluation-01",
)

class TextLike(str):
    pass


class TupleLike(tuple):
    pass


class BoolLike(int):
    pass


SOURCE_SIGNAL_PREFIX = "source_signal."
SOURCE_FAILURE_PREFIX = f"{SOURCE_SIGNAL_PREFIX}source_failure_boundary."
DISPATCH_PREFIX = f"{SOURCE_FAILURE_PREFIX}dispatch_attempt."
ASSIGNMENT_COMMITMENT_PREFIX = f"{DISPATCH_PREFIX}assignment_commitment."
ASSIGNMENT_PREFIX = f"{ASSIGNMENT_COMMITMENT_PREFIX}assignment."
ATTEMPT_PREFIX = f"{DISPATCH_PREFIX}attempt."
OUTCOME_PREFIX = f"{SOURCE_FAILURE_PREFIX}outcome."
OUTCOME_STATUS_FIELD = f"{OUTCOME_PREFIX}status"
DISPATCH_AUTHORITY_FIELD = f"{DISPATCH_PREFIX}authority"
ATTEMPT_DISPATCH_STATUS_FIELD = f"{ATTEMPT_PREFIX}dispatch_status"
ASSIGNMENT_COMMITMENT_AUTHORITY_FIELD = f"{ASSIGNMENT_COMMITMENT_PREFIX}authority"

EGRESS_AUTHORITY_LOOKALIKE = SimpleNamespace(
    name="EGRESS_ROUTING_SERVER",
    value="EGRESS_ROUTING_SERVER",
)
EXPLICIT_RESTRICTION_LOOKALIKE = SimpleNamespace(
    name="EXPLICIT_RESTRICTION",
    value="EXPLICIT_RESTRICTION",
)
SENT_LOOKALIKE = SimpleNamespace(name="SENT", value="SENT")
RATE_OR_ACCESS_RESTRICTED_LOOKALIKE = SimpleNamespace(
    name="RATE_OR_ACCESS_RESTRICTED",
    value="RATE_OR_ACCESS_RESTRICTED",
)
EGRESS_AUTHORITY_TEXT = TextLike("EGRESS_ROUTING_SERVER")
EXPLICIT_RESTRICTION_TEXT = TextLike("EXPLICIT_RESTRICTION")
RATE_OR_ACCESS_RESTRICTED_TEXT = TextLike("RATE_OR_ACCESS_RESTRICTED")
SENT_TEXT = TextLike("SENT")
OTHER_ROUTE_TEXT = TextLike("other-route")
OTHER_ASSIGNMENT_TEXT = TextLike("other-assignment")
OTHER_LEASE_TEXT = TextLike("other-lease")
OTHER_AGENT_TEXT = TextLike("other-agent")
OTHER_ATTEMPT_TEXT = TextLike("other-attempt")
OTHER_CORRELATION_TEXT = TextLike("other-correlation")
OTHER_CAUSATION_TEXT = TextLike("other-causation")

ALLOWED_OUTCOME_STATUSES = {
    TransportOutcomeStatus.RATE_OR_ACCESS_RESTRICTED,
    TransportOutcomeStatus.CAPTCHA_OR_CHALLENGE,
}


def _mutate(record: object, **changes: object) -> None:
    for field_name, value in changes.items():
        object.__setattr__(record, field_name, value)


def _snapshot(record: object) -> tuple[object, ...]:
    return tuple(getattr(record, field.name) for field in fields(cast(Any, record)))


def _build_source_signal(
    *,
    outcome_status: TransportOutcomeStatus = TransportOutcomeStatus.RATE_OR_ACCESS_RESTRICTED,
) -> TransportRestrictionSignalBoundary:
    return signal_contracts._build_boundary(outcome_status=outcome_status)


def _source_failure_boundary(
    source_signal: TransportRestrictionSignalBoundary,
) -> TransportResponseFailureOutcomeBoundary:
    boundary = source_signal.source_failure_boundary
    assert type(boundary) is TransportResponseFailureOutcomeBoundary
    return boundary


def _dispatch_boundary(
    source_signal: TransportRestrictionSignalBoundary,
) -> TransportDispatchAttemptBoundary:
    boundary = _source_failure_boundary(source_signal).dispatch_attempt
    assert type(boundary) is TransportDispatchAttemptBoundary
    return boundary


def _assignment_commitment(
    source_signal: TransportRestrictionSignalBoundary,
) -> TransportAssignmentCommitmentBoundary:
    boundary = _dispatch_boundary(source_signal).assignment_commitment
    assert type(boundary) is TransportAssignmentCommitmentBoundary
    return boundary


def _attempt(source_signal: TransportRestrictionSignalBoundary) -> DispatchAttempt:
    attempt = _dispatch_boundary(source_signal).attempt
    assert type(attempt) is DispatchAttempt
    return attempt


def _assignment(source_signal: TransportRestrictionSignalBoundary) -> TransportAssignment:
    assignment = _assignment_commitment(source_signal).assignment
    assert type(assignment) is TransportAssignment
    return assignment


def _outcome(source_signal: TransportRestrictionSignalBoundary) -> TransportAssignmentOutcome:
    outcome = _source_failure_boundary(source_signal).outcome
    assert type(outcome) is TransportAssignmentOutcome
    return outcome


def _boundary_kwargs(
    source_signal: TransportRestrictionSignalBoundary,
    *,
    route_id: str | None = None,
) -> dict[str, object]:
    assignment = _assignment(source_signal)
    return {
        "boundary_id": "restriction-evaluation-gate-01",
        "authority": TransportRestrictionEvaluationAuthority.EGRESS_ROUTING_SERVER,
        "source_signal": source_signal,
        "route_id": assignment.route_id if route_id is None else route_id,
        "evaluation_recorded": True,
        "restriction_policy_gate_satisfied": False,
        "quarantine_policy_gate_satisfied": False,
        "protected_review_required": True,
        "new_affected_lease_authorized": False,
        "new_affected_assignment_authorized": False,
        "restriction_state_commit_authorized": False,
        "quarantine_decision_commit_authorized": False,
        "fallback_effect_authorized": False,
        "automatic_unquarantine_authorized": False,
        "captcha_solving_authorized": False,
        "captcha_bypass_authorized": False,
        "parser_success_inferred": False,
        "scan_success_inferred": False,
        "notification_delivery_inferred": False,
        "reason_codes": EXPECTED_REASON_CODES,
        "evidence_reference_ids": EXPECTED_EVIDENCE_REFERENCE_IDS,
    }


def _build_boundary(
    *,
    outcome_status: TransportOutcomeStatus = TransportOutcomeStatus.RATE_OR_ACCESS_RESTRICTED,
    route_id: str | None = None,
) -> TransportRestrictionEvaluationGateBoundary:
    source_signal = _build_source_signal(outcome_status=outcome_status)
    boundary = TransportRestrictionEvaluationGateBoundary(
        **_boundary_kwargs(source_signal, route_id=route_id)  # type: ignore[arg-type]
    )
    assert type(boundary) is TransportRestrictionEvaluationGateBoundary
    return boundary


def _field_names(*records: object) -> set[str]:
    names: set[str] = set()
    for record in records:
        names.update(field.name for field in fields(cast(Any, record)))
    return names


def _clone_as_lookalike(record: object) -> SimpleNamespace:
    payload = {
        field.name: getattr(record, field.name)
        for field in fields(cast(Any, record))
    }
    return SimpleNamespace(**payload)


def _clone_as_subclass(record: object) -> object:
    record_type = type(record)
    subclass = type(f"{record_type.__name__}Subclass", (record_type,), {})
    payload = {
        field.name: getattr(record, field.name)
        for field in fields(cast(Any, record))
    }
    return subclass(**payload)


def test_task_id_is_bound_to_the_module_exactly_once() -> None:
    source = Path(restriction_evaluation_module.__file__).read_text()
    assert ER08B_TASK_ID == EXPECTED_TASK_ID
    assert source.count(EXPECTED_TASK_ID) == 1


def test_module_exports_are_exact() -> None:
    assert restriction_evaluation_module.__all__ == EXPECTED_MODULE_EXPORTS
    assert tuple(restriction_evaluation_module.__all__) == EXPECTED_MODULE_EXPORTS
    assert type(restriction_evaluation_module.__all__) is tuple
    assert len(set(restriction_evaluation_module.__all__)) == len(EXPECTED_MODULE_EXPORTS)
    assert all(hasattr(restriction_evaluation_module, name) for name in EXPECTED_MODULE_EXPORTS)


def test_package_exports_are_exact() -> None:
    assert type(egress_routing.__all__) is tuple
    assert egress_routing.__all__ == EXPECTED_PACKAGE_EXPORTS
    assert tuple(egress_routing.__all__) == EXPECTED_PACKAGE_EXPORTS
    assert len(set(egress_routing.__all__)) == len(EXPECTED_PACKAGE_EXPORTS)
    assert all(hasattr(egress_routing, name) for name in EXPECTED_PACKAGE_EXPORTS)


def test_authority_matrix_is_exact() -> None:
    assert (
        tuple((member.name, member.value) for member in TransportRestrictionEvaluationAuthority)
        == EXPECTED_AUTHORITY_MATRIX
    )
    assert len(TransportRestrictionEvaluationAuthority) == 1


def test_boundary_shape_is_exact() -> None:
    assert is_dataclass(TransportRestrictionEvaluationGateBoundary)
    assert (
        TransportRestrictionEvaluationGateBoundary.__dataclass_params__.frozen is True  # type: ignore[attr-defined]
    )
    assert (
        TransportRestrictionEvaluationGateBoundary.__dataclass_params__.slots is True  # type: ignore[attr-defined]
    )
    assert tuple(field.name for field in fields(TransportRestrictionEvaluationGateBoundary)) == (
        EXPECTED_FIELD_NAMES
    )


@pytest.mark.parametrize(
    ("outcome_status", "signal_kind"),
    EXPECTED_ALLOWED_OUTCOME_STATUS_MATRIX,
)
def test_positive_signal_mappings_are_accepted(
    outcome_status: TransportOutcomeStatus,
    signal_kind: TransportRestrictionSignalKind,
) -> None:
    source_signal = _build_source_signal(outcome_status=outcome_status)
    boundary = TransportRestrictionEvaluationGateBoundary(
        **_boundary_kwargs(source_signal)  # type: ignore[arg-type]
    )

    failure = source_signal.source_failure_boundary
    dispatch = failure.dispatch_attempt
    commitment = dispatch.assignment_commitment
    attempt = dispatch.attempt
    assignment = commitment.assignment
    outcome = failure.outcome
    source_failure = _source_failure_boundary(source_signal)
    dispatch_boundary = _dispatch_boundary(source_signal)
    commitment_boundary = _assignment_commitment(source_signal)

    assert type(boundary) is TransportRestrictionEvaluationGateBoundary
    assert type(boundary.source_signal) is TransportRestrictionSignalBoundary
    assert type(source_failure) is TransportResponseFailureOutcomeBoundary
    assert type(dispatch_boundary) is TransportDispatchAttemptBoundary
    assert type(commitment_boundary) is TransportAssignmentCommitmentBoundary
    assert type(attempt) is DispatchAttempt
    assert type(assignment) is TransportAssignment
    assert type(outcome) is TransportAssignmentOutcome
    assert boundary.authority is TransportRestrictionEvaluationAuthority.EGRESS_ROUTING_SERVER
    assert boundary.source_signal is source_signal
    assert (
        boundary.source_signal.authority
        is TransportRestrictionSignalAuthority.EGRESS_ROUTING_SERVER
    )
    assert boundary.source_signal.signal_kind is signal_kind
    assert boundary.source_signal.signal_recorded is True
    assert boundary.source_signal.restriction_evaluation_required is True
    assert boundary.source_signal.quarantine_evaluation_required is True
    assert boundary.source_signal.route_state_mutation_authorized is False
    assert boundary.source_signal.fallback_effect_authorized is False
    assert boundary.source_signal.captcha_solving_authorized is False
    assert boundary.source_signal.captcha_bypass_authorized is False
    assert boundary.source_signal.parser_success_inferred is False
    assert boundary.source_signal.scan_success_inferred is False
    assert boundary.source_signal.notification_delivery_inferred is False
    assert boundary.source_signal.source_failure_boundary.authority is (
        TransportResponseFailureOutcomeAuthority.EGRESS_ROUTING_SERVER
    )
    assert boundary.source_signal.source_failure_boundary.outcome.status is outcome_status
    assert boundary.source_signal.source_failure_boundary.outcome_committed is True
    assert (
        boundary.source_signal.source_failure_boundary.new_dispatch_effect_authorized is False
    )
    assert boundary.source_signal.source_failure_boundary.assignment_terminal is True
    assert boundary.source_signal.source_failure_boundary.parser_success_inferred is False
    assert boundary.source_signal.source_failure_boundary.scan_success_inferred is False
    assert boundary.source_signal.source_failure_boundary.notification_delivery_inferred is False
    assert boundary.source_signal.source_failure_boundary.dispatch_attempt.authority is (
        TransportDispatchAuthority.EGRESS_ROUTING_SERVER
    )
    assert dispatch_boundary.dispatch_state_committed is True
    assert dispatch_boundary.new_dispatch_effect_authorized is False
    assert attempt.dispatch_status is DispatchStatus.SENT
    assert attempt.attempt_ordinal == 1
    assert attempt.outcome_reference is None
    assert attempt.reconciliation_required is False
    assert commitment.authority is TransportAssignmentAuthority.EGRESS_ROUTING_SERVER
    assert commitment_boundary.assignment_committed is True
    assert boundary.route_id == assignment.route_id
    assert boundary.route_id == attempt.route_id
    assert assignment.route_id == attempt.route_id
    assert assignment.lease_id == attempt.lease_id
    assert assignment.agent_id == attempt.agent_id
    assert attempt.assignment_id == assignment.assignment_id
    assert attempt.lease_id == assignment.lease_id
    assert attempt.route_id == assignment.route_id
    assert attempt.agent_id == assignment.agent_id
    assert attempt.correlation_id == assignment.correlation_id
    assert attempt.causation_id == assignment.causation_id
    assert outcome.assignment_id == assignment.assignment_id
    assert outcome.attempt_id == attempt.attempt_id
    assert outcome.correlation_id == assignment.correlation_id
    assert outcome.causation_id == assignment.causation_id
    assert boundary.evaluation_recorded is True
    assert boundary.restriction_policy_gate_satisfied is False
    assert boundary.quarantine_policy_gate_satisfied is False
    assert boundary.protected_review_required is True
    assert boundary.new_affected_lease_authorized is False
    assert boundary.new_affected_assignment_authorized is False
    assert boundary.restriction_state_commit_authorized is False
    assert boundary.quarantine_decision_commit_authorized is False
    assert boundary.fallback_effect_authorized is False
    assert boundary.automatic_unquarantine_authorized is False
    assert boundary.captcha_solving_authorized is False
    assert boundary.captcha_bypass_authorized is False
    assert boundary.parser_success_inferred is False
    assert boundary.scan_success_inferred is False
    assert boundary.notification_delivery_inferred is False
    assert boundary.reason_codes == EXPECTED_REASON_CODES
    assert boundary.evidence_reference_ids == EXPECTED_EVIDENCE_REFERENCE_IDS
    assert boundary == _build_boundary(outcome_status=outcome_status)
    assert hash(boundary) == hash(_build_boundary(outcome_status=outcome_status))


@pytest.mark.parametrize(
    "outcome_status",
    tuple(
        status
        for status in TransportOutcomeStatus
        if status not in ALLOWED_OUTCOME_STATUSES
    ),
)
def test_all_other_outcomes_are_rejected(outcome_status: TransportOutcomeStatus) -> None:
    source_signal = _build_source_signal()
    _mutate(_outcome(source_signal), status=outcome_status)
    with pytest.raises(ValueError):
        TransportRestrictionEvaluationGateBoundary(
            **_boundary_kwargs(source_signal)  # type: ignore[arg-type]
        )


@pytest.mark.parametrize(
    ("outcome_status", "bad_signal_kind"),
    (
        (
            TransportOutcomeStatus.RATE_OR_ACCESS_RESTRICTED,
            TransportRestrictionSignalKind.EXPLICIT_CHALLENGE,
        ),
        (
            TransportOutcomeStatus.CAPTCHA_OR_CHALLENGE,
            TransportRestrictionSignalKind.EXPLICIT_RESTRICTION,
        ),
    ),
)
def test_signal_outcome_mismatch_is_rejected(
    outcome_status: TransportOutcomeStatus,
    bad_signal_kind: TransportRestrictionSignalKind,
) -> None:
    source_signal = _build_source_signal(outcome_status=outcome_status)
    _mutate(source_signal, signal_kind=bad_signal_kind)
    with pytest.raises(ValueError):
        TransportRestrictionEvaluationGateBoundary(
            **_boundary_kwargs(source_signal)  # type: ignore[arg-type]
        )


@pytest.mark.parametrize(
    "bad_value",
    (
        "EGRESS_ROUTING_SERVER",
        TextLike("EGRESS_ROUTING_SERVER"),
        SimpleNamespace(name="EGRESS_ROUTING_SERVER", value="EGRESS_ROUTING_SERVER"),
    ),
)
def test_invalid_authority_is_rejected(bad_value: object) -> None:
    source_signal = _build_source_signal()
    kwargs = _boundary_kwargs(source_signal)
    kwargs["authority"] = bad_value
    with pytest.raises(ValueError):
        TransportRestrictionEvaluationGateBoundary(**kwargs)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("field_name", "bad_value"),
    (
        ("evaluation_recorded", 1),
        ("evaluation_recorded", BoolLike(1)),
        ("restriction_policy_gate_satisfied", 1),
        ("restriction_policy_gate_satisfied", BoolLike(1)),
        ("quarantine_policy_gate_satisfied", 1),
        ("quarantine_policy_gate_satisfied", BoolLike(1)),
        ("protected_review_required", 0),
        ("protected_review_required", BoolLike(0)),
        ("new_affected_lease_authorized", 1),
        ("new_affected_lease_authorized", BoolLike(1)),
        ("new_affected_assignment_authorized", 1),
        ("new_affected_assignment_authorized", BoolLike(1)),
        ("restriction_state_commit_authorized", 1),
        ("restriction_state_commit_authorized", BoolLike(1)),
        ("quarantine_decision_commit_authorized", 1),
        ("quarantine_decision_commit_authorized", BoolLike(1)),
        ("fallback_effect_authorized", 1),
        ("fallback_effect_authorized", BoolLike(1)),
        ("automatic_unquarantine_authorized", 1),
        ("automatic_unquarantine_authorized", BoolLike(1)),
        ("captcha_solving_authorized", 1),
        ("captcha_solving_authorized", BoolLike(1)),
        ("captcha_bypass_authorized", 1),
        ("captcha_bypass_authorized", BoolLike(1)),
        ("parser_success_inferred", 1),
        ("parser_success_inferred", BoolLike(1)),
        ("scan_success_inferred", 1),
        ("scan_success_inferred", BoolLike(1)),
        ("notification_delivery_inferred", 1),
        ("notification_delivery_inferred", BoolLike(1)),
        ("source_signal.signal_recorded", 1),
        ("source_signal.restriction_evaluation_required", 1),
        ("source_signal.quarantine_evaluation_required", 1),
        ("source_signal.route_state_mutation_authorized", 1),
        ("source_signal.fallback_effect_authorized", 1),
        ("source_signal.captcha_solving_authorized", 1),
        ("source_signal.captcha_bypass_authorized", 1),
        ("source_signal.parser_success_inferred", 1),
        ("source_signal.scan_success_inferred", 1),
        ("source_signal.notification_delivery_inferred", 1),
        ("source_signal.source_failure_boundary.outcome_committed", 1),
        ("source_signal.source_failure_boundary.new_dispatch_effect_authorized", 1),
        ("source_signal.source_failure_boundary.assignment_terminal", 0),
        ("source_signal.source_failure_boundary.parser_success_inferred", 1),
        ("source_signal.source_failure_boundary.scan_success_inferred", 1),
        ("source_signal.source_failure_boundary.notification_delivery_inferred", 1),
        (DISPATCH_PREFIX + "dispatch_state_committed", 1),
        (DISPATCH_PREFIX + "new_dispatch_effect_authorized", 1),
        (ATTEMPT_PREFIX + "reconciliation_required", 1),
        (ASSIGNMENT_COMMITMENT_PREFIX + "assignment_committed", 0),
    ),
)
def test_exact_bool_values_reject_bool_like_and_wrong_values(
    field_name: str,
    bad_value: object,
) -> None:
    source_signal = _build_source_signal()
    kwargs = _boundary_kwargs(source_signal)
    if field_name.startswith(ASSIGNMENT_PREFIX):
        target: Any = _assignment(source_signal)
        subfield = field_name.removeprefix(ASSIGNMENT_PREFIX)
    elif field_name.startswith(ASSIGNMENT_COMMITMENT_PREFIX + "attempt."):
        target = _attempt(source_signal)
        subfield = field_name.removeprefix(ASSIGNMENT_COMMITMENT_PREFIX + "attempt.")
    elif field_name.startswith(ASSIGNMENT_COMMITMENT_PREFIX):
        target = _assignment_commitment(source_signal)
        subfield = field_name.removeprefix(ASSIGNMENT_COMMITMENT_PREFIX)
    elif field_name.startswith(ATTEMPT_PREFIX):
        target = _attempt(source_signal)
        subfield = field_name.removeprefix(ATTEMPT_PREFIX)
    elif field_name.startswith(DISPATCH_PREFIX):
        target = _dispatch_boundary(source_signal)
        subfield = field_name.removeprefix(DISPATCH_PREFIX)
    elif field_name.startswith(SOURCE_FAILURE_PREFIX):
        target = _source_failure_boundary(source_signal)
        subfield = field_name.removeprefix(SOURCE_FAILURE_PREFIX)
    elif field_name.startswith(SOURCE_SIGNAL_PREFIX):
        target = source_signal
        subfield = field_name.removeprefix(SOURCE_SIGNAL_PREFIX)
    else:
        kwargs[field_name] = bad_value
        target = None
        subfield = ""
    if target is not None:
        _mutate(target, **{subfield: bad_value})
    with pytest.raises(ValueError):
        TransportRestrictionEvaluationGateBoundary(**kwargs)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("field_path", "replacement_factory"),
    (
        ("source_signal", _clone_as_lookalike),
        ("source_signal", _clone_as_subclass),
        ("source_signal.source_failure_boundary", _clone_as_lookalike),
        ("source_signal.source_failure_boundary", _clone_as_subclass),
        ("source_signal.source_failure_boundary.dispatch_attempt", _clone_as_lookalike),
        ("source_signal.source_failure_boundary.dispatch_attempt", _clone_as_subclass),
        ("source_signal.source_failure_boundary.outcome", _clone_as_lookalike),
        ("source_signal.source_failure_boundary.outcome", _clone_as_subclass),
        (
            "source_signal.source_failure_boundary.dispatch_attempt.assignment_commitment",
            _clone_as_lookalike,
        ),
        (
            "source_signal.source_failure_boundary.dispatch_attempt.assignment_commitment",
            _clone_as_subclass,
        ),
        ("source_signal.source_failure_boundary.dispatch_attempt.attempt", _clone_as_lookalike),
        ("source_signal.source_failure_boundary.dispatch_attempt.attempt", _clone_as_subclass),
        (
            "source_signal.source_failure_boundary.dispatch_attempt.assignment_commitment.assignment",
            _clone_as_lookalike,
        ),
        (
            "source_signal.source_failure_boundary.dispatch_attempt.assignment_commitment.assignment",
            _clone_as_subclass,
        ),
    ),
)
def test_exact_record_levels_reject_subclasses_and_foreign_records(
    field_path: str,
    replacement_factory: Any,
) -> None:
    source_signal = _build_source_signal(outcome_status=TransportOutcomeStatus.CAPTCHA_OR_CHALLENGE)
    kwargs = _boundary_kwargs(source_signal)
    replacement = replacement_factory(
        {
            "source_signal": source_signal,
            SOURCE_FAILURE_PREFIX.rstrip("."): _source_failure_boundary(source_signal),
            DISPATCH_PREFIX.rstrip("."): _dispatch_boundary(source_signal),
            OUTCOME_PREFIX.rstrip("."): _outcome(source_signal),
            ASSIGNMENT_COMMITMENT_PREFIX.rstrip("."): _assignment_commitment(source_signal),
            ATTEMPT_PREFIX.rstrip("."): _attempt(source_signal),
            ASSIGNMENT_PREFIX.rstrip("."): _assignment(source_signal),
        }[field_path]
    )
    if field_path == "source_signal":
        kwargs["source_signal"] = replacement
    elif field_path == SOURCE_FAILURE_PREFIX.rstrip("."):
        _mutate(source_signal, source_failure_boundary=replacement)
    elif field_path == DISPATCH_PREFIX.rstrip("."):
        _mutate(_source_failure_boundary(source_signal), dispatch_attempt=replacement)
    elif field_path == OUTCOME_PREFIX.rstrip("."):
        _mutate(_source_failure_boundary(source_signal), outcome=replacement)
    elif field_path == ASSIGNMENT_COMMITMENT_PREFIX.rstrip("."):
        _mutate(_dispatch_boundary(source_signal), assignment_commitment=replacement)
    elif field_path == ATTEMPT_PREFIX.rstrip("."):
        _mutate(_dispatch_boundary(source_signal), attempt=replacement)
    else:
        _mutate(_assignment_commitment(source_signal), assignment=replacement)
    with pytest.raises(ValueError):
        TransportRestrictionEvaluationGateBoundary(**kwargs)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("field_name", "bad_value"),
    (
        ("authority", EGRESS_AUTHORITY_TEXT),
        ("authority", EGRESS_AUTHORITY_TEXT),
        ("authority", EGRESS_AUTHORITY_LOOKALIKE),
        ("source_signal.authority", EGRESS_AUTHORITY_TEXT),
        ("source_signal.authority", EGRESS_AUTHORITY_TEXT),
        ("source_signal.authority", EGRESS_AUTHORITY_LOOKALIKE),
        ("source_signal.signal_kind", EXPLICIT_RESTRICTION_TEXT),
        ("source_signal.signal_kind", EXPLICIT_RESTRICTION_TEXT),
        ("source_signal.signal_kind", EXPLICIT_RESTRICTION_LOOKALIKE),
        ("source_signal.source_failure_boundary.authority", EGRESS_AUTHORITY_TEXT),
        ("source_signal.source_failure_boundary.authority", EGRESS_AUTHORITY_TEXT),
        ("source_signal.source_failure_boundary.authority", EGRESS_AUTHORITY_LOOKALIKE),
        (OUTCOME_STATUS_FIELD, RATE_OR_ACCESS_RESTRICTED_TEXT),
        (OUTCOME_STATUS_FIELD, RATE_OR_ACCESS_RESTRICTED_TEXT),
        (OUTCOME_STATUS_FIELD, RATE_OR_ACCESS_RESTRICTED_LOOKALIKE),
        (DISPATCH_AUTHORITY_FIELD, EGRESS_AUTHORITY_TEXT),
        (DISPATCH_AUTHORITY_FIELD, EGRESS_AUTHORITY_TEXT),
        (DISPATCH_AUTHORITY_FIELD, EGRESS_AUTHORITY_LOOKALIKE),
        (ATTEMPT_DISPATCH_STATUS_FIELD, SENT_TEXT),
        (ATTEMPT_DISPATCH_STATUS_FIELD, SENT_TEXT),
        (ATTEMPT_DISPATCH_STATUS_FIELD, SENT_LOOKALIKE),
        (ASSIGNMENT_COMMITMENT_AUTHORITY_FIELD, EGRESS_AUTHORITY_TEXT),
        (ASSIGNMENT_COMMITMENT_AUTHORITY_FIELD, EGRESS_AUTHORITY_TEXT),
        (ASSIGNMENT_COMMITMENT_AUTHORITY_FIELD, EGRESS_AUTHORITY_LOOKALIKE),
    ),
)
def test_exact_enum_values_reject_plain_strings_subclasses_and_lookalikes(
    field_name: str,
    bad_value: object,
) -> None:
    source_signal = _build_source_signal()
    kwargs = _boundary_kwargs(source_signal)
    if field_name == "authority":
        kwargs["authority"] = bad_value
    elif field_name == "source_signal.authority":
        _mutate(source_signal, authority=bad_value)
    elif field_name == "source_signal.signal_kind":
        _mutate(source_signal, signal_kind=bad_value)
    elif field_name == "source_signal.source_failure_boundary.authority":
        _mutate(_source_failure_boundary(source_signal), authority=bad_value)
    elif field_name == "source_signal.source_failure_boundary.outcome.status":
        _mutate(_outcome(source_signal), status=bad_value)
    elif field_name == DISPATCH_AUTHORITY_FIELD:
        _mutate(_dispatch_boundary(source_signal), authority=bad_value)
    elif field_name == ATTEMPT_DISPATCH_STATUS_FIELD:
        _mutate(_attempt(source_signal), dispatch_status=bad_value)
    else:
        _mutate(_assignment_commitment(source_signal), authority=bad_value)
    with pytest.raises(ValueError):
        TransportRestrictionEvaluationGateBoundary(**kwargs)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("field_name", "bad_value"),
    (
        ("route_id", "other-route"),
        ("route_id", TextLike("other-route")),
        (ASSIGNMENT_PREFIX + "route_id", "other-route"),
        (ATTEMPT_PREFIX + "route_id", "other-route"),
        (ASSIGNMENT_PREFIX + "assignment_id", "other-assignment"),
        (ATTEMPT_PREFIX + "assignment_id", "other-assignment"),
        (ASSIGNMENT_PREFIX + "lease_id", "other-lease"),
        (ATTEMPT_PREFIX + "lease_id", "other-lease"),
        (ASSIGNMENT_PREFIX + "agent_id", "other-agent"),
        (ATTEMPT_PREFIX + "agent_id", "other-agent"),
        (ATTEMPT_PREFIX + "attempt_id", "other-attempt"),
        (OUTCOME_PREFIX + "assignment_id", "other-assignment"),
        (OUTCOME_PREFIX + "attempt_id", "other-attempt"),
        (ATTEMPT_PREFIX + "correlation_id", "other-correlation"),
        (ATTEMPT_PREFIX + "causation_id", "other-causation"),
        (OUTCOME_PREFIX + "correlation_id", "other-correlation"),
        (OUTCOME_PREFIX + "causation_id", "other-causation"),
    ),
)
def test_linkage_mutations_are_rejected(field_name: str, bad_value: object) -> None:
    source_signal = _build_source_signal(outcome_status=TransportOutcomeStatus.CAPTCHA_OR_CHALLENGE)
    kwargs = _boundary_kwargs(source_signal)
    if field_name == "route_id":
        kwargs["route_id"] = bad_value
    elif field_name.startswith(ASSIGNMENT_PREFIX):
        _mutate(_assignment(source_signal), **{field_name.rsplit(".", 1)[-1]: bad_value})
    elif field_name.startswith(ATTEMPT_PREFIX):
        _mutate(_attempt(source_signal), **{field_name.rsplit(".", 1)[-1]: bad_value})
    elif field_name.startswith(OUTCOME_PREFIX):
        _mutate(_outcome(source_signal), **{field_name.rsplit(".", 1)[-1]: bad_value})
    else:
        _mutate(_assignment_commitment(source_signal), **{field_name.rsplit(".", 1)[-1]: bad_value})
    with pytest.raises(ValueError):
        TransportRestrictionEvaluationGateBoundary(**kwargs)  # type: ignore[arg-type]


def test_boundary_is_frozen_and_slots() -> None:
    boundary = _build_boundary(outcome_status=TransportOutcomeStatus.CAPTCHA_OR_CHALLENGE)
    assert boundary.__class__.__dataclass_params__.frozen is True  # type: ignore[attr-defined]
    assert boundary.__class__.__dataclass_params__.slots is True  # type: ignore[attr-defined]
    assert not hasattr(boundary, "__dict__")
    with pytest.raises(FrozenInstanceError):
        boundary.route_id = "other-route"  # type: ignore[misc]


def test_inputs_are_not_mutated() -> None:
    source_signal = _build_source_signal(
        outcome_status=TransportOutcomeStatus.RATE_OR_ACCESS_RESTRICTED
    )
    before = (
        _snapshot(source_signal),
        _snapshot(_source_failure_boundary(source_signal)),
        _snapshot(_dispatch_boundary(source_signal)),
        _snapshot(_assignment_commitment(source_signal)),
        _snapshot(_attempt(source_signal)),
        _snapshot(_assignment(source_signal)),
        _snapshot(_outcome(source_signal)),
    )
    boundary = TransportRestrictionEvaluationGateBoundary(
        **_boundary_kwargs(source_signal)  # type: ignore[arg-type]
    )
    after = (
        _snapshot(source_signal),
        _snapshot(_source_failure_boundary(source_signal)),
        _snapshot(_dispatch_boundary(source_signal)),
        _snapshot(_assignment_commitment(source_signal)),
        _snapshot(_attempt(source_signal)),
        _snapshot(_assignment(source_signal)),
        _snapshot(_outcome(source_signal)),
    )
    assert before == after
    assert boundary.source_signal is source_signal


def test_result_is_deterministic() -> None:
    boundary_a = _build_boundary(outcome_status=TransportOutcomeStatus.CAPTCHA_OR_CHALLENGE)
    boundary_b = _build_boundary(outcome_status=TransportOutcomeStatus.CAPTCHA_OR_CHALLENGE)
    assert boundary_a == boundary_b
    assert hash(boundary_a) == hash(boundary_b)


def test_no_forbidden_state_records_or_raw_payloads_are_present() -> None:
    source = Path(restriction_evaluation_module.__file__).read_text()
    forbidden = {
        "RouteHealthState",
        "RouteRestrictionState",
        "RouteQuarantineDecision",
        "RouteHealthStatus",
        "RouteRestrictionStatus",
        "RouteQuarantineStatus",
        "PolicyBasedFallbackDecision",
        "raw_response",
        "raw_json",
        "raw_html",
        "cookie",
        "cookies",
        "session",
        "sessions",
        "token",
        "private_key",
        "credentials",
        "subprocess",
        "socket",
        "httpx",
        "requests",
        "sqlalchemy",
        "alembic",
        "playwright",
        "selenium",
        "browser",
        "runtime",
        "storage",
    }
    assert all(item not in source for item in forbidden)


def test_er08a_semantics_remain_unchanged() -> None:
    assert ER08A_TASK_ID == signal_contracts.EXPECTED_TASK_ID
    assert signal_contracts.EXPECTED_ALLOWED_OUTCOME_STATUS_MATRIX == (
        (
            TransportOutcomeStatus.RATE_OR_ACCESS_RESTRICTED,
            TransportRestrictionSignalKind.EXPLICIT_RESTRICTION,
        ),
        (
            TransportOutcomeStatus.CAPTCHA_OR_CHALLENGE,
            TransportRestrictionSignalKind.EXPLICIT_CHALLENGE,
        ),
    )
