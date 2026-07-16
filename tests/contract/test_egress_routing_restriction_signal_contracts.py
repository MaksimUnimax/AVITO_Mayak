from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

import mayak.modules.egress_routing as egress_routing
import mayak.modules.egress_routing.restriction_signal as restriction_signal_module
import tests.contract.test_egress_routing_outcome_response_failure_contracts as failure_contracts
from mayak.modules.egress_routing import (
    ER08A_TASK_ID,
    DispatchAttempt,
    RouteReconciliationStatus,
    TransportAssignment,
    TransportAssignmentCommitmentBoundary,
    TransportDispatchAttemptBoundary,
    TransportOutcomeStatus,
    TransportResponseFailureOutcomeBoundary,
    TransportRestrictionSignalAuthority,
    TransportRestrictionSignalBoundary,
    TransportRestrictionSignalKind,
)

EXPECTED_TASK_ID = "ER-08A-TRANSPORT-RESTRICTION-SIGNAL-BOUNDARY-20260715-031"

EXPECTED_MODULE_EXPORTS = (
    "ER08A_TASK_ID",
    "TransportRestrictionSignalAuthority",
    "TransportRestrictionSignalKind",
    "TransportRestrictionSignalBoundary",
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
    "signal_kind",
    "source_failure_boundary",
    "signal_recorded",
    "restriction_evaluation_required",
    "quarantine_evaluation_required",
    "route_state_mutation_authorized",
    "fallback_effect_authorized",
    "captcha_solving_authorized",
    "captcha_bypass_authorized",
    "parser_success_inferred",
    "scan_success_inferred",
    "notification_delivery_inferred",
    "reason_codes",
    "evidence_reference_ids",
)

EXPECTED_AUTHORITY_MATRIX = (("EGRESS_ROUTING_SERVER", "EGRESS_ROUTING_SERVER"),)
EXPECTED_KIND_MATRIX = (
    ("EXPLICIT_RESTRICTION", "EXPLICIT_RESTRICTION"),
    ("EXPLICIT_CHALLENGE", "EXPLICIT_CHALLENGE"),
)
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


class TextLike(str):
    pass


class TupleLike(tuple):
    pass


class BoolLike(int):
    pass


def _mutate(record: object, **changes: object) -> None:
    for field_name, value in changes.items():
        object.__setattr__(record, field_name, value)


def _snapshot(record: object) -> tuple[object, ...]:
    return tuple(getattr(record, field.name) for field in fields(cast(Any, record)))


def _build_source_boundary(
    *,
    outcome_status: TransportOutcomeStatus = TransportOutcomeStatus.RATE_OR_ACCESS_RESTRICTED,
) -> TransportResponseFailureOutcomeBoundary:
    boundary = failure_contracts._build_boundary(
        outcome_status=TransportOutcomeStatus.RATE_OR_ACCESS_RESTRICTED,
        safe_response_reference=None,
        reconciliation_status=RouteReconciliationStatus.NOT_REQUIRED,
    )
    if outcome_status is not TransportOutcomeStatus.RATE_OR_ACCESS_RESTRICTED:
        _mutate(boundary.outcome, status=outcome_status)
    return boundary


def _boundary_kwargs(
    source_boundary: TransportResponseFailureOutcomeBoundary,
    signal_kind: TransportRestrictionSignalKind,
) -> dict[str, object]:
    return {
        "boundary_id": "restriction-signal-boundary-01",
        "authority": TransportRestrictionSignalAuthority.EGRESS_ROUTING_SERVER,
        "signal_kind": signal_kind,
        "source_failure_boundary": source_boundary,
        "signal_recorded": True,
        "restriction_evaluation_required": True,
        "quarantine_evaluation_required": True,
        "route_state_mutation_authorized": False,
        "fallback_effect_authorized": False,
        "captcha_solving_authorized": False,
        "captcha_bypass_authorized": False,
        "parser_success_inferred": False,
        "scan_success_inferred": False,
        "notification_delivery_inferred": False,
        "reason_codes": ("restriction-signal-recorded",),
        "evidence_reference_ids": ("evidence-restriction-signal-01",),
    }


def _build_boundary(
    *,
    outcome_status: TransportOutcomeStatus = TransportOutcomeStatus.RATE_OR_ACCESS_RESTRICTED,
) -> TransportRestrictionSignalBoundary:
    source_boundary = _build_source_boundary(outcome_status=outcome_status)
    signal_kind = {
        TransportOutcomeStatus.RATE_OR_ACCESS_RESTRICTED: (
            TransportRestrictionSignalKind.EXPLICIT_RESTRICTION
        ),
        TransportOutcomeStatus.CAPTCHA_OR_CHALLENGE: (
            TransportRestrictionSignalKind.EXPLICIT_CHALLENGE
        ),
    }.get(outcome_status, TransportRestrictionSignalKind.EXPLICIT_RESTRICTION)
    boundary = TransportRestrictionSignalBoundary(
        **_boundary_kwargs(source_boundary, signal_kind)  # type: ignore[arg-type]
    )
    assert type(boundary) is TransportRestrictionSignalBoundary
    return boundary


def _source_failure_boundary(
    boundary: TransportRestrictionSignalBoundary,
) -> TransportResponseFailureOutcomeBoundary:
    source_boundary = boundary.source_failure_boundary
    assert type(source_boundary) is TransportResponseFailureOutcomeBoundary
    return source_boundary


def _dispatch_boundary(
    boundary: TransportRestrictionSignalBoundary,
) -> TransportDispatchAttemptBoundary:
    dispatch_boundary = _source_failure_boundary(boundary).dispatch_attempt
    assert type(dispatch_boundary) is TransportDispatchAttemptBoundary
    return dispatch_boundary


def _assignment_commitment(
    boundary: TransportRestrictionSignalBoundary,
) -> TransportAssignmentCommitmentBoundary:
    assignment_commitment = _dispatch_boundary(boundary).assignment_commitment
    assert type(assignment_commitment) is TransportAssignmentCommitmentBoundary
    return assignment_commitment


def _attempt(boundary: TransportRestrictionSignalBoundary) -> DispatchAttempt:
    attempt = _dispatch_boundary(boundary).attempt
    assert type(attempt) is DispatchAttempt
    return attempt


def _assignment(boundary: TransportRestrictionSignalBoundary) -> TransportAssignment:
    assignment = _assignment_commitment(boundary).assignment
    assert type(assignment) is TransportAssignment
    return assignment


def test_task_id_is_bound_to_the_module_exactly_once() -> None:
    source = Path(restriction_signal_module.__file__).read_text()
    assert ER08A_TASK_ID == EXPECTED_TASK_ID
    assert source.count(EXPECTED_TASK_ID) == 1


def test_module_exports_are_exact() -> None:
    assert restriction_signal_module.__all__ == EXPECTED_MODULE_EXPORTS
    assert tuple(restriction_signal_module.__all__) == EXPECTED_MODULE_EXPORTS
    assert type(restriction_signal_module.__all__) is tuple
    assert len(set(restriction_signal_module.__all__)) == len(EXPECTED_MODULE_EXPORTS)
    assert all(hasattr(restriction_signal_module, name) for name in EXPECTED_MODULE_EXPORTS)


def test_package_exports_are_exact() -> None:
    assert type(egress_routing.__all__) is tuple
    assert egress_routing.__all__ == EXPECTED_PACKAGE_EXPORTS
    assert tuple(egress_routing.__all__) == EXPECTED_PACKAGE_EXPORTS
    assert len(set(egress_routing.__all__)) == len(EXPECTED_PACKAGE_EXPORTS)
    assert all(hasattr(egress_routing, name) for name in EXPECTED_PACKAGE_EXPORTS)


def test_authority_and_kind_matrices_are_exact() -> None:
    assert (
        tuple((member.name, member.value) for member in TransportRestrictionSignalAuthority)
        == EXPECTED_AUTHORITY_MATRIX
    )
    assert (
        tuple((member.name, member.value) for member in TransportRestrictionSignalKind)
        == EXPECTED_KIND_MATRIX
    )
    assert len(TransportRestrictionSignalAuthority) == 1
    assert len(TransportRestrictionSignalKind) == 2


def test_boundary_shape_is_exact() -> None:
    assert is_dataclass(TransportRestrictionSignalBoundary)
    assert (
        TransportRestrictionSignalBoundary.__dataclass_params__.frozen is True  # type: ignore[attr-defined]
    )
    assert (
        TransportRestrictionSignalBoundary.__dataclass_params__.slots is True  # type: ignore[attr-defined]
    )
    assert tuple(field.name for field in fields(TransportRestrictionSignalBoundary)) == (
        EXPECTED_FIELD_NAMES
    )


@pytest.mark.parametrize(
    ("outcome_status", "signal_kind"),
    EXPECTED_ALLOWED_OUTCOME_STATUS_MATRIX,
)
def test_positive_outcome_to_signal_mappings_are_accepted(
    outcome_status: TransportOutcomeStatus,
    signal_kind: TransportRestrictionSignalKind,
) -> None:
    boundary = TransportRestrictionSignalBoundary(
        **_boundary_kwargs(_build_source_boundary(outcome_status=outcome_status), signal_kind)  # type: ignore[arg-type]
    )

    assert type(boundary) is TransportRestrictionSignalBoundary
    assert boundary.authority is TransportRestrictionSignalAuthority.EGRESS_ROUTING_SERVER
    assert boundary.signal_kind is signal_kind
    assert boundary.signal_recorded is True
    assert boundary.restriction_evaluation_required is True
    assert boundary.quarantine_evaluation_required is True
    assert boundary.route_state_mutation_authorized is False
    assert boundary.fallback_effect_authorized is False
    assert boundary.captcha_solving_authorized is False
    assert boundary.captcha_bypass_authorized is False
    assert boundary.parser_success_inferred is False
    assert boundary.scan_success_inferred is False
    assert boundary.notification_delivery_inferred is False
    assert boundary.source_failure_boundary is not None
    assert boundary.source_failure_boundary is _source_failure_boundary(boundary)
    assert boundary.source_failure_boundary.outcome.status is outcome_status
    assert boundary.reason_codes == ("restriction-signal-recorded",)
    assert boundary.evidence_reference_ids == ("evidence-restriction-signal-01",)
    assert boundary == _build_boundary(outcome_status=outcome_status)
    assert hash(boundary) == hash(_build_boundary(outcome_status=outcome_status))


@pytest.mark.parametrize(
    "outcome_status",
    tuple(
        status
        for status in TransportOutcomeStatus
        if status
        not in {
            TransportOutcomeStatus.RATE_OR_ACCESS_RESTRICTED,
            TransportOutcomeStatus.CAPTCHA_OR_CHALLENGE,
        }
    ),
)
def test_all_other_outcome_statuses_are_rejected(outcome_status: TransportOutcomeStatus) -> None:
    source_boundary = _build_source_boundary(outcome_status=outcome_status)
    with pytest.raises(ValueError):
        TransportRestrictionSignalBoundary(
            **_boundary_kwargs(source_boundary, TransportRestrictionSignalKind.EXPLICIT_RESTRICTION)  # type: ignore[arg-type]
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
def test_signal_kind_mismatch_is_rejected(
    outcome_status: TransportOutcomeStatus,
    bad_signal_kind: TransportRestrictionSignalKind,
) -> None:
    source_boundary = _build_source_boundary(outcome_status=outcome_status)
    with pytest.raises(ValueError):
        TransportRestrictionSignalBoundary(
            **_boundary_kwargs(source_boundary, bad_signal_kind)  # type: ignore[arg-type]
        )


def test_invalid_authority_is_rejected() -> None:
    source_boundary = _build_source_boundary()
    kwargs = _boundary_kwargs(source_boundary, TransportRestrictionSignalKind.EXPLICIT_RESTRICTION)
    kwargs["authority"] = TextLike("EGRESS_ROUTING_SERVER")
    with pytest.raises(ValueError):
        TransportRestrictionSignalBoundary(**kwargs)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("field_name", "bad_value"),
    (
        ("boundary_id", " "),
        ("boundary_id", TextLike(" ")),
        ("authority", "EGRESS_ROUTING_SERVER"),
        ("authority", TextLike("EGRESS_ROUTING_SERVER")),
        ("authority", SimpleNamespace(name="EGRESS_ROUTING_SERVER", value="EGRESS_ROUTING_SERVER")),
        ("signal_kind", "EXPLICIT_RESTRICTION"),
        ("signal_kind", TextLike("EXPLICIT_RESTRICTION")),
        ("signal_kind", SimpleNamespace(name="EXPLICIT_RESTRICTION", value="EXPLICIT_RESTRICTION")),
        ("signal_recorded", 1),
        ("signal_recorded", BoolLike(1)),
        ("restriction_evaluation_required", 1),
        ("restriction_evaluation_required", BoolLike(1)),
        ("quarantine_evaluation_required", 1),
        ("quarantine_evaluation_required", BoolLike(1)),
        ("route_state_mutation_authorized", 0),
        ("route_state_mutation_authorized", BoolLike(0)),
        ("fallback_effect_authorized", 0),
        ("fallback_effect_authorized", BoolLike(0)),
        ("captcha_solving_authorized", 0),
        ("captcha_solving_authorized", BoolLike(0)),
        ("captcha_bypass_authorized", 0),
        ("captcha_bypass_authorized", BoolLike(0)),
        ("parser_success_inferred", 0),
        ("parser_success_inferred", BoolLike(0)),
        ("scan_success_inferred", 0),
        ("scan_success_inferred", BoolLike(0)),
        ("notification_delivery_inferred", 0),
        ("notification_delivery_inferred", BoolLike(0)),
        ("reason_codes", TupleLike(("reason",))),
        ("reason_codes", ()),
        ("reason_codes", TupleLike(())),
        ("evidence_reference_ids", TupleLike(("evidence",))),
        ("evidence_reference_ids", ()),
        ("evidence_reference_ids", TupleLike(())),
    ),
)
def test_exact_enum_and_bool_and_tuple_values_reject_lookalikes(
    field_name: str,
    bad_value: object,
) -> None:
    boundary = _build_boundary()
    kwargs = _boundary_kwargs(_source_failure_boundary(boundary), boundary.signal_kind)
    kwargs[field_name] = bad_value
    with pytest.raises(ValueError):
        TransportRestrictionSignalBoundary(**kwargs)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("field_name", "replacement_factory"),
    (
        ("source_failure_boundary", lambda boundary: SimpleNamespace(**{
            "boundary_id": boundary.boundary_id,
        })),
        (
            "source_failure_boundary",
            lambda boundary: type(
                "SourceFailureBoundarySubclass",
                (TransportResponseFailureOutcomeBoundary,),
                {},
            )(**{field.name: getattr(boundary, field.name) for field in fields(boundary)}),
        ),
        (
            "source_failure_boundary.dispatch_attempt",
            lambda boundary: SimpleNamespace(**{
                field.name: getattr(_dispatch_boundary(boundary), field.name)
                for field in fields(_dispatch_boundary(boundary))
            }),
        ),
        (
            "source_failure_boundary.outcome",
            lambda boundary: SimpleNamespace(**{
                field.name: getattr(_source_failure_boundary(boundary).outcome, field.name)
                for field in fields(_source_failure_boundary(boundary).outcome)
            }),
        ),
        (
            "source_failure_boundary.dispatch_attempt.assignment_commitment",
            lambda boundary: SimpleNamespace(**{
                field.name: getattr(_assignment_commitment(boundary), field.name)
                for field in fields(_assignment_commitment(boundary))
            }),
        ),
        (
            "source_failure_boundary.dispatch_attempt.attempt",
            lambda boundary: SimpleNamespace(
                **{
                    field.name: getattr(_attempt(boundary), field.name)
                    for field in fields(_attempt(boundary))
                }
            ),
        ),
        (
            "source_failure_boundary.dispatch_attempt.assignment_commitment.assignment",
            lambda boundary: SimpleNamespace(
                **{
                    field.name: getattr(_assignment(boundary), field.name)
                    for field in fields(_assignment(boundary))
                }
            ),
        ),
    ),
)
def test_exact_record_levels_reject_subclasses_and_foreign_records(
    field_name: str,
    replacement_factory: Any,
) -> None:
    boundary = _build_boundary()
    source_boundary = _source_failure_boundary(boundary)
    if field_name == "source_failure_boundary":
        kwargs = _boundary_kwargs(replacement_factory(source_boundary), boundary.signal_kind)
    elif field_name == "source_failure_boundary.dispatch_attempt":
        _mutate(source_boundary, dispatch_attempt=replacement_factory(boundary))
        kwargs = _boundary_kwargs(source_boundary, boundary.signal_kind)
    elif field_name == "source_failure_boundary.outcome":
        _mutate(source_boundary, outcome=replacement_factory(boundary))
        kwargs = _boundary_kwargs(source_boundary, boundary.signal_kind)
    elif field_name == "source_failure_boundary.dispatch_attempt.assignment_commitment":
        _mutate(_dispatch_boundary(boundary), assignment_commitment=replacement_factory(boundary))
        kwargs = _boundary_kwargs(source_boundary, boundary.signal_kind)
    elif field_name == "source_failure_boundary.dispatch_attempt.attempt":
        _mutate(_dispatch_boundary(boundary), attempt=replacement_factory(boundary))
        kwargs = _boundary_kwargs(source_boundary, boundary.signal_kind)
    else:
        _mutate(_assignment_commitment(boundary), assignment=replacement_factory(boundary))
        kwargs = _boundary_kwargs(source_boundary, boundary.signal_kind)
    with pytest.raises(ValueError):
        TransportRestrictionSignalBoundary(**kwargs)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("mutate_path", "field_name", "bad_value"),
    (
        ("assignment", "assignment_id", "assignment-02"),
        ("assignment", "lease_id", "lease-02"),
        ("assignment", "route_id", "route-02"),
        ("assignment", "agent_id", "agent-02"),
        ("attempt", "attempt_id", "attempt-02"),
        ("attempt", "assignment_id", "assignment-02"),
        ("attempt", "lease_id", "lease-02"),
        ("attempt", "route_id", "route-02"),
        ("attempt", "agent_id", "agent-02"),
        ("attempt", "outcome_reference", "outcome-ref-02"),
        ("outcome", "assignment_id", "assignment-02"),
        ("outcome", "attempt_id", "attempt-02"),
        ("outcome", "correlation_id", "correlation-02"),
        ("outcome", "causation_id", "causation-02"),
    ),
)
def test_identity_mismatches_are_rejected(
    mutate_path: str,
    field_name: str,
    bad_value: object,
) -> None:
    boundary = _build_boundary()
    source_boundary = _source_failure_boundary(boundary)
    if mutate_path == "assignment":
        _mutate(_assignment(boundary), **{field_name: bad_value})
    elif mutate_path == "attempt":
        _mutate(_attempt(boundary), **{field_name: bad_value})
    else:
        _mutate(_source_failure_boundary(boundary).outcome, **{field_name: bad_value})
    with pytest.raises(ValueError):
        TransportRestrictionSignalBoundary(
            **_boundary_kwargs(source_boundary, boundary.signal_kind)  # type: ignore[arg-type]
        )


@pytest.mark.parametrize(
    ("field_name", "bad_value"),
    (
        ("boundary_id", " "),
        ("outcome_committed", False),
        ("new_dispatch_effect_authorized", True),
        ("assignment_terminal", False),
        ("parser_success_inferred", True),
        ("scan_success_inferred", True),
        ("notification_delivery_inferred", True),
        ("signal_recorded", False),
        ("restriction_evaluation_required", False),
        ("quarantine_evaluation_required", False),
        ("route_state_mutation_authorized", True),
        ("fallback_effect_authorized", True),
        ("captcha_solving_authorized", True),
        ("captcha_bypass_authorized", True),
        ("reason_codes", ()),
        ("evidence_reference_ids", ()),
    ),
)
def test_source_er07d_invariants_and_mandatory_flags_are_enforced(
    field_name: str,
    bad_value: object,
) -> None:
    boundary = _build_boundary()
    source_boundary = _source_failure_boundary(boundary)
    if field_name in {
        "outcome_committed",
        "new_dispatch_effect_authorized",
        "assignment_terminal",
        "parser_success_inferred",
        "scan_success_inferred",
        "notification_delivery_inferred",
        "boundary_id",
        "reason_codes",
        "evidence_reference_ids",
    }:
        _mutate(source_boundary, **{field_name: bad_value})
        kwargs = _boundary_kwargs(source_boundary, boundary.signal_kind)
    else:
        kwargs = _boundary_kwargs(source_boundary, boundary.signal_kind)
        kwargs[field_name] = bad_value
    with pytest.raises(ValueError):
        TransportRestrictionSignalBoundary(**kwargs)  # type: ignore[arg-type]


def test_frozen_slots_replace_and_input_stability_are_enforced() -> None:
    boundary = _build_boundary()
    source_boundary = _source_failure_boundary(boundary)
    before_source = _snapshot(source_boundary)
    before_dispatch = _snapshot(_dispatch_boundary(boundary))
    before_assignment_commitment = _snapshot(_assignment_commitment(boundary))
    before_attempt = _snapshot(_attempt(boundary))
    before_assignment = _snapshot(_assignment(boundary))

    with pytest.raises(FrozenInstanceError):
        boundary.signal_recorded = False  # type: ignore[misc]

    with pytest.raises(ValueError):
        replace(boundary, signal_recorded=False)
    with pytest.raises(ValueError):
        replace(boundary, route_state_mutation_authorized=True)

    assert boundary == _build_boundary()
    assert _snapshot(source_boundary) == before_source
    assert _snapshot(_dispatch_boundary(boundary)) == before_dispatch
    assert _snapshot(_assignment_commitment(boundary)) == before_assignment_commitment
    assert _snapshot(_attempt(boundary)) == before_attempt
    assert _snapshot(_assignment(boundary)) == before_assignment


def test_deterministic_equality_and_immutability_guards() -> None:
    first = _build_boundary()
    second = _build_boundary()

    assert first == second
    assert hash(first) == hash(second)
    assert first.source_failure_boundary is _source_failure_boundary(first)
    assert first.source_failure_boundary.dispatch_attempt is _dispatch_boundary(first)
    assert first.source_failure_boundary.outcome is _source_failure_boundary(first).outcome


def test_module_source_avoids_route_state_fallback_and_raw_response_terms() -> None:
    source = Path(restriction_signal_module.__file__).read_text()
    for forbidden in (
        "RouteHealthState",
        "RouteRestrictionState",
        "RouteQuarantineDecision",
        "PolicyBasedFallbackBoundary",
        "safe_response_reference",
        "response_body",
        "raw_response",
    ):
        assert forbidden not in source
