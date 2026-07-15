# ruff: noqa: I001

from __future__ import annotations

from dataclasses import fields, is_dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest

import mayak.modules.egress_routing.outcome as outcome_module
import tests.contract.test_egress_routing_dispatch_contracts as dispatch_contracts
from mayak.modules import egress_routing
from mayak.modules.egress_routing import (
    DispatchStatus,
    ER07A_TASK_ID,
    RouteReconciliationStatus,
    TransportAssignmentOutcome,
    TransportDispatchAttemptBoundary,
    TransportDispatchAuthority,
    TransportOutcomeCommitmentAuthority,
    TransportOutcomeCommitmentBoundary,
    TransportOutcomeStatus,
)

EXPECTED_TASK_ID = "ER-07A-TRANSPORT-OUTCOME-COMMITMENT-BOUNDARY-20260715-016"

EXPECTED_MODULE_EXPORTS = (
    "ER07A_TASK_ID",
    "TransportOutcomeCommitmentAuthority",
    "TransportOutcomeCommitmentBoundary",
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

EXPECTED_DISPATCH_TO_OUTCOME_MATRIX = {
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

EXPECTED_RECONCILIATION_MATRIX = {
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

EXPECTED_NO_RESPONSE_STATUSES = (
    TransportOutcomeStatus.NOT_SENT,
    TransportOutcomeStatus.DISPATCH_REJECTED,
    TransportOutcomeStatus.DISPATCH_UNKNOWN,
    TransportOutcomeStatus.SENT_NO_RESPONSE,
    TransportOutcomeStatus.RECONCILIATION_REQUIRED,
)

EXPECTED_REQUIRED_REFERENCE_STATUSES = (
    TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
    TransportOutcomeStatus.USABLE_RESPONSE_TRANSPORT_ONLY,
)

EXPECTED_OPTIONAL_REFERENCE_STATUSES = (
    TransportOutcomeStatus.RATE_OR_ACCESS_RESTRICTED,
    TransportOutcomeStatus.CAPTCHA_OR_CHALLENGE,
    TransportOutcomeStatus.PROVIDER_REJECTED,
    TransportOutcomeStatus.MALFORMED_RESPONSE_TRANSPORT_LAYER,
)

EXPECTED_DEFERRED_STATUSES = (
    TransportOutcomeStatus.TRANSPORT_UNAVAILABLE,
    TransportOutcomeStatus.TRANSPORT_TIMEOUT,
    TransportOutcomeStatus.TRANSPORT_AMBIGUOUS,
    TransportOutcomeStatus.ROUTE_QUARANTINED,
    TransportOutcomeStatus.ROUTE_DEGRADED,
    TransportOutcomeStatus.NO_APPROVED_ROUTE_AVAILABLE,
    TransportOutcomeStatus.POLICY_FALLBACK_ATTEMPTED,
    TransportOutcomeStatus.POLICY_FALLBACK_EXHAUSTED,
)

VALID_CASES = (
    (
        DispatchStatus.NOT_SENT,
        TransportOutcomeStatus.NOT_SENT,
        None,
        RouteReconciliationStatus.NOT_REQUIRED,
        True,
    ),
    (
        DispatchStatus.REJECTED,
        TransportOutcomeStatus.DISPATCH_REJECTED,
        None,
        RouteReconciliationStatus.RESOLVED_NOT_SENT,
        True,
    ),
    (
        DispatchStatus.UNKNOWN,
        TransportOutcomeStatus.DISPATCH_UNKNOWN,
        None,
        RouteReconciliationStatus.REQUIRED,
        False,
    ),
    (
        DispatchStatus.UNKNOWN,
        TransportOutcomeStatus.RECONCILIATION_REQUIRED,
        None,
        RouteReconciliationStatus.MANUAL_REVIEW_REQUIRED,
        False,
    ),
    (
        DispatchStatus.SENT,
        TransportOutcomeStatus.SENT_NO_RESPONSE,
        None,
        RouteReconciliationStatus.NOT_REQUIRED,
        True,
    ),
    (
        DispatchStatus.SENT,
        TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
        "safe-response-01",
        RouteReconciliationStatus.RESOLVED_SENT,
        True,
    ),
    (
        DispatchStatus.SENT,
        TransportOutcomeStatus.USABLE_RESPONSE_TRANSPORT_ONLY,
        "safe-response-02",
        RouteReconciliationStatus.RESOLVED_TERMINAL,
        True,
    ),
    (
        DispatchStatus.SENT,
        TransportOutcomeStatus.RATE_OR_ACCESS_RESTRICTED,
        "safe-response-03",
        RouteReconciliationStatus.NOT_REQUIRED,
        True,
    ),
    (
        DispatchStatus.SENT,
        TransportOutcomeStatus.CAPTCHA_OR_CHALLENGE,
        None,
        RouteReconciliationStatus.RESOLVED_SENT,
        True,
    ),
    (
        DispatchStatus.SENT,
        TransportOutcomeStatus.PROVIDER_REJECTED,
        "safe-response-04",
        RouteReconciliationStatus.RESOLVED_TERMINAL,
        True,
    ),
    (
        DispatchStatus.SENT,
        TransportOutcomeStatus.MALFORMED_RESPONSE_TRANSPORT_LAYER,
        None,
        RouteReconciliationStatus.RESOLVED_SENT,
        True,
    ),
)

_UNSET = object()


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
    boundary_id: object = "outcome-boundary-01",
    authority: object = TransportOutcomeCommitmentAuthority.EGRESS_ROUTING_SERVER,
    outcome_committed: object = True,
    new_dispatch_effect_authorized: object = False,
    assignment_terminal: object = _UNSET,
    parser_success_inferred: object = False,
    scan_success_inferred: object = False,
    notification_delivery_inferred: object = False,
    reason_codes: object = ("transport-outcome-committed",),
    evidence_reference_ids: object = ("evidence-outcome-commitment-01",),
    safe_response_reference: object = _UNSET,
    reconciliation_status: object = _UNSET,
) -> dict[str, object]:
    state = dispatch_contracts._build_valid_state(
        dispatch_status=dispatch_status,
        new_dispatch_effect_authorized=False,
        reconciliation_required=dispatch_status is DispatchStatus.UNKNOWN,
        attempt_ordinal=1,
        outcome_reference=None,
    )
    dispatch_boundary = state["boundary"]
    attempt = state["attempt"]
    assignment = state["assignment"]
    assert isinstance(dispatch_boundary, TransportDispatchAttemptBoundary)

    if safe_response_reference is _UNSET:
        safe_response_reference = {
            TransportOutcomeStatus.NOT_SENT: None,
            TransportOutcomeStatus.DISPATCH_REJECTED: None,
            TransportOutcomeStatus.DISPATCH_UNKNOWN: None,
            TransportOutcomeStatus.RECONCILIATION_REQUIRED: None,
            TransportOutcomeStatus.SENT_NO_RESPONSE: None,
            TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED: "safe-response-01",
            TransportOutcomeStatus.USABLE_RESPONSE_TRANSPORT_ONLY: "safe-response-02",
            TransportOutcomeStatus.RATE_OR_ACCESS_RESTRICTED: "safe-response-03",
            TransportOutcomeStatus.CAPTCHA_OR_CHALLENGE: None,
            TransportOutcomeStatus.PROVIDER_REJECTED: "safe-response-04",
            TransportOutcomeStatus.MALFORMED_RESPONSE_TRANSPORT_LAYER: None,
            TransportOutcomeStatus.TRANSPORT_UNAVAILABLE: None,
            TransportOutcomeStatus.TRANSPORT_TIMEOUT: None,
            TransportOutcomeStatus.TRANSPORT_AMBIGUOUS: None,
            TransportOutcomeStatus.ROUTE_QUARANTINED: None,
            TransportOutcomeStatus.ROUTE_DEGRADED: None,
            TransportOutcomeStatus.NO_APPROVED_ROUTE_AVAILABLE: None,
            TransportOutcomeStatus.POLICY_FALLBACK_ATTEMPTED: None,
            TransportOutcomeStatus.POLICY_FALLBACK_EXHAUSTED: None,
        }[outcome_status]
    if reconciliation_status is _UNSET:
        reconciliation_status = {
            TransportOutcomeStatus.NOT_SENT: RouteReconciliationStatus.NOT_REQUIRED,
            TransportOutcomeStatus.DISPATCH_REJECTED: RouteReconciliationStatus.RESOLVED_NOT_SENT,
            TransportOutcomeStatus.DISPATCH_UNKNOWN: RouteReconciliationStatus.REQUIRED,
            TransportOutcomeStatus.RECONCILIATION_REQUIRED: RouteReconciliationStatus.MANUAL_REVIEW_REQUIRED,  # noqa: E501
            TransportOutcomeStatus.SENT_NO_RESPONSE: RouteReconciliationStatus.NOT_REQUIRED,
            TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED: RouteReconciliationStatus.RESOLVED_SENT,  # noqa: E501
            TransportOutcomeStatus.USABLE_RESPONSE_TRANSPORT_ONLY: RouteReconciliationStatus.RESOLVED_TERMINAL,  # noqa: E501
            TransportOutcomeStatus.RATE_OR_ACCESS_RESTRICTED: RouteReconciliationStatus.NOT_REQUIRED,  # noqa: E501
            TransportOutcomeStatus.CAPTCHA_OR_CHALLENGE: RouteReconciliationStatus.RESOLVED_SENT,
            TransportOutcomeStatus.PROVIDER_REJECTED: RouteReconciliationStatus.RESOLVED_TERMINAL,  # noqa: E501
            TransportOutcomeStatus.MALFORMED_RESPONSE_TRANSPORT_LAYER: RouteReconciliationStatus.RESOLVED_SENT,  # noqa: E501
            TransportOutcomeStatus.TRANSPORT_UNAVAILABLE: RouteReconciliationStatus.NOT_REQUIRED,
            TransportOutcomeStatus.TRANSPORT_TIMEOUT: RouteReconciliationStatus.NOT_REQUIRED,
            TransportOutcomeStatus.TRANSPORT_AMBIGUOUS: RouteReconciliationStatus.REQUIRED,
            TransportOutcomeStatus.ROUTE_QUARANTINED: RouteReconciliationStatus.NOT_REQUIRED,
            TransportOutcomeStatus.ROUTE_DEGRADED: RouteReconciliationStatus.NOT_REQUIRED,
            TransportOutcomeStatus.NO_APPROVED_ROUTE_AVAILABLE: RouteReconciliationStatus.NOT_REQUIRED,  # noqa: E501
            TransportOutcomeStatus.POLICY_FALLBACK_ATTEMPTED: RouteReconciliationStatus.NOT_REQUIRED,  # noqa: E501
            TransportOutcomeStatus.POLICY_FALLBACK_EXHAUSTED: RouteReconciliationStatus.NOT_REQUIRED,  # noqa: E501
        }[outcome_status]
    if assignment_terminal is _UNSET:
        assignment_terminal = outcome_status not in {
            TransportOutcomeStatus.DISPATCH_UNKNOWN,
            TransportOutcomeStatus.RECONCILIATION_REQUIRED,
        }

    outcome = TransportAssignmentOutcome(
        outcome_id="outcome-01",
        assignment_id=cast(str, assignment.assignment_id),
        attempt_id=cast(str, attempt.attempt_id),
        status=outcome_status,
        safe_response_reference=cast(str | None, safe_response_reference),
        reason_codes=("transport-outcome-committed",),
        evidence_reference_ids=("evidence-outcome-01",),
        reconciliation_status=cast(RouteReconciliationStatus, reconciliation_status),
        correlation_id=cast(str, assignment.correlation_id),
        causation_id=cast(str, assignment.causation_id),
    )
    return {
        "boundary_id": cast(str, boundary_id),
        "authority": cast(TransportOutcomeCommitmentAuthority, authority),
        "dispatch_boundary": dispatch_boundary,
        "attempt": attempt,
        "assignment": assignment,
        "outcome": outcome,
        "outcome_committed": cast(bool, outcome_committed),
        "new_dispatch_effect_authorized": cast(bool, new_dispatch_effect_authorized),
        "assignment_terminal": cast(bool, assignment_terminal),
        "parser_success_inferred": cast(bool, parser_success_inferred),
        "scan_success_inferred": cast(bool, scan_success_inferred),
        "notification_delivery_inferred": cast(bool, notification_delivery_inferred),
        "reason_codes": cast(tuple[str, ...], reason_codes),
        "evidence_reference_ids": cast(tuple[str, ...], evidence_reference_ids),
    }


def _build_boundary(
    *,
    dispatch_status: DispatchStatus,
    outcome_status: TransportOutcomeStatus,
    **kwargs: object,
) -> TransportOutcomeCommitmentBoundary:
    state = _build_state(dispatch_status=dispatch_status, outcome_status=outcome_status, **kwargs)
    boundary = TransportOutcomeCommitmentBoundary(**_boundary_kwargs(state))  # type: ignore[arg-type]
    assert isinstance(boundary, TransportOutcomeCommitmentBoundary)
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


def test_task_id_appears_in_changed_scope_exactly_once() -> None:
    assert ER07A_TASK_ID == EXPECTED_TASK_ID
    source = Path(outcome_module.__file__).read_text()
    assert source.count(EXPECTED_TASK_ID) == 1


def test_module_exports_are_exact() -> None:
    assert outcome_module.__all__ == EXPECTED_MODULE_EXPORTS
    assert tuple(outcome_module.__all__) == EXPECTED_MODULE_EXPORTS
    assert type(outcome_module.__all__) is tuple
    assert len(set(outcome_module.__all__)) == len(EXPECTED_MODULE_EXPORTS)
    assert all(hasattr(outcome_module, name) for name in EXPECTED_MODULE_EXPORTS)


def test_package_exports_are_exact() -> None:
    assert type(egress_routing.__all__) is tuple
    assert egress_routing.__all__ == EXPECTED_PACKAGE_EXPORTS
    assert tuple(egress_routing.__all__) == EXPECTED_PACKAGE_EXPORTS
    assert len(set(egress_routing.__all__)) == len(EXPECTED_PACKAGE_EXPORTS)
    assert all(hasattr(egress_routing, name) for name in EXPECTED_PACKAGE_EXPORTS)


def test_authority_matrix_is_exact() -> None:
    assert tuple((member.name, member.value) for member in TransportOutcomeCommitmentAuthority) == (
        EXPECTED_AUTHORITY_MATRIX[0],
    )
    assert len(TransportOutcomeCommitmentAuthority) == 1


def test_boundary_shape_is_exact() -> None:
    assert is_dataclass(TransportOutcomeCommitmentBoundary)
    assert TransportOutcomeCommitmentBoundary.__dataclass_params__.frozen is True  # type: ignore[attr-defined]
    assert TransportOutcomeCommitmentBoundary.__dataclass_params__.slots is True  # type: ignore[attr-defined]
    assert tuple(field.name for field in fields(TransportOutcomeCommitmentBoundary)) == (
        EXPECTED_FIELD_NAMES
    )


@pytest.mark.parametrize(
    (
        "dispatch_status",
        "outcome_status",
        "safe_response_reference",
        "reconciliation_status",
        "assignment_terminal",
    ),
    VALID_CASES,
)
def test_valid_dispatch_and_outcome_matrices_are_accepted(
    dispatch_status: DispatchStatus,
    outcome_status: TransportOutcomeStatus,
    safe_response_reference: object,
    reconciliation_status: RouteReconciliationStatus,
    assignment_terminal: bool,
) -> None:
    boundary = _build_boundary(
        dispatch_status=dispatch_status,
        outcome_status=outcome_status,
        safe_response_reference=safe_response_reference,
        reconciliation_status=reconciliation_status,
        assignment_terminal=assignment_terminal,
    )
    assert boundary.authority is TransportOutcomeCommitmentAuthority.EGRESS_ROUTING_SERVER
    assert boundary.outcome.status is outcome_status
    assert boundary.outcome.safe_response_reference == safe_response_reference
    assert boundary.outcome.reconciliation_status is reconciliation_status
    assert boundary.assignment_terminal is assignment_terminal
    assert boundary.outcome_committed is True
    assert boundary.new_dispatch_effect_authorized is False
    assert boundary.parser_success_inferred is False
    assert boundary.scan_success_inferred is False
    assert boundary.notification_delivery_inferred is False


def test_er02_status_matrix_and_outcome_shape_remain_unchanged() -> None:
    assert tuple(member.name for member in TransportOutcomeStatus) == (
        "NOT_SENT",
        "DISPATCH_REJECTED",
        "DISPATCH_UNKNOWN",
        "SENT_NO_RESPONSE",
        "TRANSPORT_UNAVAILABLE",
        "TRANSPORT_TIMEOUT",
        "TRANSPORT_AMBIGUOUS",
        "RESPONSE_RECEIVED_UNCLASSIFIED",
        "USABLE_RESPONSE_TRANSPORT_ONLY",
        "RATE_OR_ACCESS_RESTRICTED",
        "CAPTCHA_OR_CHALLENGE",
        "PROVIDER_REJECTED",
        "MALFORMED_RESPONSE_TRANSPORT_LAYER",
        "ROUTE_QUARANTINED",
        "ROUTE_DEGRADED",
        "NO_APPROVED_ROUTE_AVAILABLE",
        "POLICY_FALLBACK_ATTEMPTED",
        "POLICY_FALLBACK_EXHAUSTED",
        "RECONCILIATION_REQUIRED",
    )
    assert tuple(field.name for field in fields(TransportAssignmentOutcome)) == (
        "outcome_id",
        "assignment_id",
        "attempt_id",
        "status",
        "safe_response_reference",
        "reason_codes",
        "evidence_reference_ids",
        "reconciliation_status",
        "correlation_id",
        "causation_id",
    )


@pytest.mark.parametrize("field_name", ("boundary_id",))
def test_text_fields_reject_blank_values(field_name: str) -> None:
    kwargs = _boundary_kwargs(
        _build_state(
            dispatch_status=DispatchStatus.SENT,
            outcome_status=TransportOutcomeStatus.SENT_NO_RESPONSE,
        )
    )
    kwargs[field_name] = " "
    with pytest.raises(ValueError):
        TransportOutcomeCommitmentBoundary(**kwargs)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("boundary_id", TextLike("boundary-01")),
        ("reason_codes", TupleLike(("transport-outcome-committed",))),
        ("evidence_reference_ids", TupleLike(("evidence-outcome-commitment-01",))),
        ("dispatch_attempt", SimpleNamespace()),
        ("outcome", SimpleNamespace()),
    ],
)
def test_subclass_and_lookalike_types_are_rejected(field_name: str, value: object) -> None:
    state = _build_state(
        dispatch_status=DispatchStatus.SENT,
        outcome_status=TransportOutcomeStatus.SENT_NO_RESPONSE,
    )
    kwargs = _boundary_kwargs(state)
    kwargs[field_name] = value
    with pytest.raises(ValueError):
        TransportOutcomeCommitmentBoundary(**kwargs)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "field_name",
    (
        "outcome_committed",
        "new_dispatch_effect_authorized",
        "assignment_terminal",
        "parser_success_inferred",
        "scan_success_inferred",
        "notification_delivery_inferred",
    ),
)
def test_bool_fields_reject_non_bool_types(field_name: str) -> None:
    kwargs = _boundary_kwargs(
        _build_state(
            dispatch_status=DispatchStatus.SENT,
            outcome_status=TransportOutcomeStatus.SENT_NO_RESPONSE,
        )
    )
    kwargs[field_name] = 1
    with pytest.raises(ValueError):
        TransportOutcomeCommitmentBoundary(**kwargs)  # type: ignore[arg-type]


def test_false_success_flags_must_remain_false() -> None:
    for field_name in (
        "parser_success_inferred",
        "scan_success_inferred",
        "notification_delivery_inferred",
    ):
        kwargs = _boundary_kwargs(
            _build_state(
                dispatch_status=DispatchStatus.SENT,
                outcome_status=TransportOutcomeStatus.SENT_NO_RESPONSE,
            )
        )
        kwargs[field_name] = True
        with pytest.raises(ValueError):
            TransportOutcomeCommitmentBoundary(**kwargs)  # type: ignore[arg-type]


def test_outcome_committed_and_new_dispatch_authorized_invariants() -> None:
    kwargs = _boundary_kwargs(
        _build_state(
            dispatch_status=DispatchStatus.SENT,
            outcome_status=TransportOutcomeStatus.SENT_NO_RESPONSE,
        )
    )
    kwargs["outcome_committed"] = False
    with pytest.raises(ValueError):
        TransportOutcomeCommitmentBoundary(**kwargs)  # type: ignore[arg-type]

    kwargs = _boundary_kwargs(
        _build_state(
            dispatch_status=DispatchStatus.SENT,
            outcome_status=TransportOutcomeStatus.SENT_NO_RESPONSE,
        )
    )
    kwargs["new_dispatch_effect_authorized"] = True
    with pytest.raises(ValueError):
        TransportOutcomeCommitmentBoundary(**kwargs)  # type: ignore[arg-type]


def test_wrong_authority_is_rejected() -> None:
    kwargs = _boundary_kwargs(
        _build_state(
            dispatch_status=DispatchStatus.SENT,
            outcome_status=TransportOutcomeStatus.SENT_NO_RESPONSE,
        )
    )
    kwargs["authority"] = TransportDispatchAuthority.EGRESS_ROUTING_SERVER
    with pytest.raises(ValueError):
        TransportOutcomeCommitmentBoundary(**kwargs)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("reason_codes", ()),
        ("reason_codes", ["reason-code-01"]),
        ("reason_codes", (" ",)),
        ("evidence_reference_ids", ()),
        ("evidence_reference_ids", ["evidence-01"]),
        ("evidence_reference_ids", (" ",)),
    ],
)
def test_top_level_tuple_fields_reject_invalid_values(field_name: str, value: object) -> None:
    kwargs = _boundary_kwargs(
        _build_state(
            dispatch_status=DispatchStatus.SENT,
            outcome_status=TransportOutcomeStatus.SENT_NO_RESPONSE,
        )
    )
    kwargs[field_name] = value
    with pytest.raises(ValueError):
        TransportOutcomeCommitmentBoundary(**kwargs)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "dispatch_status",
    (
        DispatchStatus.PENDING,
        DispatchStatus.ATTEMPTED,
        DispatchStatus.ACKNOWLEDGED,
    ),
)
def test_pending_attempted_acknowledged_dispatch_statuses_are_rejected(
    dispatch_status: DispatchStatus,
) -> None:
    state = _build_state(
        dispatch_status=DispatchStatus.SENT,
        outcome_status=TransportOutcomeStatus.SENT_NO_RESPONSE,
    )
    _mutate(state["attempt"], dispatch_status=dispatch_status)
    kwargs = _boundary_kwargs(state)
    with pytest.raises(ValueError):
        TransportOutcomeCommitmentBoundary(**kwargs)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("dispatch_field", "value"),
    [
        ("authority", TransportOutcomeCommitmentAuthority.EGRESS_ROUTING_SERVER),
        ("dispatch_state_committed", False),
        ("new_dispatch_effect_authorized", True),
        ("assignment_commitment", SimpleNamespace(assignment_committed=False)),
    ],
)
def test_nested_dispatch_gate_rejects_invalid_state(dispatch_field: str, value: object) -> None:
    state = _build_state(
        dispatch_status=DispatchStatus.SENT,
        outcome_status=TransportOutcomeStatus.SENT_NO_RESPONSE,
    )
    dispatch_boundary = cast(TransportDispatchAttemptBoundary, state["dispatch_boundary"])
    _mutate(dispatch_boundary, **{dispatch_field: value})
    kwargs = _boundary_kwargs(state)
    with pytest.raises(ValueError):
        TransportOutcomeCommitmentBoundary(**kwargs)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("attempt_ordinal", 0),
        ("attempt_ordinal", 2),
        ("outcome_reference", "outcome-01"),
    ],
)
def test_attempt_gate_rejects_non_terminal_state(field_name: str, value: object) -> None:
    state = _build_state(
        dispatch_status=DispatchStatus.SENT,
        outcome_status=TransportOutcomeStatus.SENT_NO_RESPONSE,
    )
    attempt = cast(object, state["attempt"])
    _mutate(attempt, **{field_name: value})
    kwargs = _boundary_kwargs(state)
    with pytest.raises(ValueError):
        TransportOutcomeCommitmentBoundary(**kwargs)  # type: ignore[arg-type]


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
def test_attempt_assignment_identity_mismatches_are_rejected(field_name: str) -> None:
    state = _build_state(
        dispatch_status=DispatchStatus.SENT,
        outcome_status=TransportOutcomeStatus.SENT_NO_RESPONSE,
    )
    attempt = cast(object, state["attempt"])
    _mutate(attempt, **{field_name: "mismatch"})
    kwargs = _boundary_kwargs(state)
    with pytest.raises(ValueError):
        TransportOutcomeCommitmentBoundary(**kwargs)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("outcome_id", " "),
        ("assignment_id", " "),
        ("attempt_id", " "),
        ("correlation_id", " "),
        ("causation_id", " "),
    ],
)
def test_outcome_identity_fields_reject_blank_values(field_name: str, value: object) -> None:
    state = _build_state(
        dispatch_status=DispatchStatus.SENT,
        outcome_status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
        safe_response_reference="safe-response-01",
    )
    outcome = cast(object, state["outcome"])
    _mutate(outcome, **{field_name: value})
    kwargs = _boundary_kwargs(state)
    with pytest.raises(ValueError):
        TransportOutcomeCommitmentBoundary(**kwargs)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("field_name",),
    (
        ("assignment_id",),
        ("attempt_id",),
    ),
)
def test_outcome_identity_mismatches_are_rejected(field_name: str) -> None:
    state = _build_state(
        dispatch_status=DispatchStatus.SENT,
        outcome_status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
        safe_response_reference="safe-response-01",
    )
    outcome = cast(object, state["outcome"])
    _mutate(outcome, **{field_name: "mismatch"})
    kwargs = _boundary_kwargs(state)
    with pytest.raises(ValueError):
        TransportOutcomeCommitmentBoundary(**kwargs)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("field_name",),
    (
        ("correlation_id",),
        ("causation_id",),
    ),
)
def test_outcome_correlation_and_causation_identity_mismatches_are_rejected(
    field_name: str,
) -> None:
    state = _build_state(
        dispatch_status=DispatchStatus.SENT,
        outcome_status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
        safe_response_reference="safe-response-01",
    )
    outcome = cast(object, state["outcome"])
    _mutate(outcome, **{field_name: "mismatch"})
    kwargs = _boundary_kwargs(state)
    with pytest.raises(ValueError):
        TransportOutcomeCommitmentBoundary(**kwargs)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("reason_codes", ()),
        ("reason_codes", ["reason-code-01"]),
        ("reason_codes", (" ",)),
        ("evidence_reference_ids", ()),
        ("evidence_reference_ids", ["evidence-01"]),
        ("evidence_reference_ids", (" ",)),
    ],
)
def test_outcome_tuple_fields_reject_invalid_values(field_name: str, value: object) -> None:
    state = _build_state(
        dispatch_status=DispatchStatus.SENT,
        outcome_status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
        safe_response_reference="safe-response-01",
    )
    outcome = cast(object, state["outcome"])
    _mutate(outcome, **{field_name: value})
    kwargs = _boundary_kwargs(state)
    with pytest.raises(ValueError):
        TransportOutcomeCommitmentBoundary(**kwargs)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("dispatch_status", "outcome_status"),
    (
        (DispatchStatus.NOT_SENT, TransportOutcomeStatus.DISPATCH_REJECTED),
        (DispatchStatus.NOT_SENT, TransportOutcomeStatus.DISPATCH_UNKNOWN),
        (DispatchStatus.REJECTED, TransportOutcomeStatus.NOT_SENT),
        (DispatchStatus.UNKNOWN, TransportOutcomeStatus.NOT_SENT),
        (DispatchStatus.SENT, TransportOutcomeStatus.NOT_SENT),
        (DispatchStatus.SENT, TransportOutcomeStatus.DISPATCH_UNKNOWN),
        (DispatchStatus.SENT, TransportOutcomeStatus.RECONCILIATION_REQUIRED),
    ),
)
def test_forbidden_dispatch_outcome_combinations_are_rejected(
    dispatch_status: DispatchStatus,
    outcome_status: TransportOutcomeStatus,
) -> None:
    state = _build_state(
        dispatch_status=dispatch_status,
        outcome_status=outcome_status,
    )
    kwargs = _boundary_kwargs(state)
    with pytest.raises(ValueError):
        TransportOutcomeCommitmentBoundary(**kwargs)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("dispatch_status", "outcome_status", "reconciliation_status"),
    (
        (DispatchStatus.NOT_SENT, TransportOutcomeStatus.NOT_SENT, RouteReconciliationStatus.REQUIRED),  # noqa: E501
        (DispatchStatus.NOT_SENT, TransportOutcomeStatus.NOT_SENT, RouteReconciliationStatus.PENDING),  # noqa: E501
        (DispatchStatus.REJECTED, TransportOutcomeStatus.DISPATCH_REJECTED, RouteReconciliationStatus.PENDING),  # noqa: E501
        (DispatchStatus.UNKNOWN, TransportOutcomeStatus.DISPATCH_UNKNOWN, RouteReconciliationStatus.NOT_REQUIRED),  # noqa: E501
        (DispatchStatus.SENT, TransportOutcomeStatus.SENT_NO_RESPONSE, RouteReconciliationStatus.REQUIRED),  # noqa: E501
        (
            DispatchStatus.SENT,
            TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,  # noqa: E501
            RouteReconciliationStatus.REMAINS_AMBIGUOUS,
        ),
    ),
)
def test_forbidden_reconciliation_combinations_are_rejected(
    dispatch_status: DispatchStatus,
    outcome_status: TransportOutcomeStatus,
    reconciliation_status: RouteReconciliationStatus,
) -> None:
    state = _build_state(
        dispatch_status=dispatch_status,
        outcome_status=outcome_status,
        safe_response_reference=(
            "safe-response-01"
            if outcome_status is TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED
            else _UNSET
        ),
    )
    _mutate(state["outcome"], reconciliation_status=reconciliation_status)
    kwargs = _boundary_kwargs(state)
    with pytest.raises(ValueError):
        TransportOutcomeCommitmentBoundary(**kwargs)  # type: ignore[arg-type]


@pytest.mark.parametrize("status", EXPECTED_REQUIRED_REFERENCE_STATUSES)
def test_missing_required_safe_response_reference_is_rejected(
    status: TransportOutcomeStatus,
) -> None:
    state = _build_state(
        dispatch_status=DispatchStatus.SENT,
        outcome_status=status,
        safe_response_reference=None,
    )
    kwargs = _boundary_kwargs(state)
    with pytest.raises(ValueError):
        TransportOutcomeCommitmentBoundary(**kwargs)  # type: ignore[arg-type]


@pytest.mark.parametrize("status", EXPECTED_NO_RESPONSE_STATUSES)
def test_unexpected_safe_response_reference_is_rejected_for_no_response_statuses(
    status: TransportOutcomeStatus,
) -> None:
    state = _build_state(
        dispatch_status=(
            DispatchStatus.UNKNOWN
            if status
            in {
                TransportOutcomeStatus.DISPATCH_UNKNOWN,
                TransportOutcomeStatus.RECONCILIATION_REQUIRED,
            }
            else DispatchStatus.SENT
        ),
        outcome_status=status,
        safe_response_reference="opaque-safe-response",
    )
    kwargs = _boundary_kwargs(state)
    with pytest.raises(ValueError):
        TransportOutcomeCommitmentBoundary(**kwargs)  # type: ignore[arg-type]


@pytest.mark.parametrize("status", EXPECTED_DEFERRED_STATUSES)
def test_deferred_outcome_statuses_are_rejected(status: TransportOutcomeStatus) -> None:
    state = _build_state(
        dispatch_status=DispatchStatus.SENT,
        outcome_status=status,
    )
    kwargs = _boundary_kwargs(state)
    with pytest.raises(ValueError):
        TransportOutcomeCommitmentBoundary(**kwargs)  # type: ignore[arg-type]
