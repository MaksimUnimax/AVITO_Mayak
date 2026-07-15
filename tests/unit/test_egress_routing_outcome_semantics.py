from __future__ import annotations

from dataclasses import fields
from typing import cast

import pytest

import tests.contract.test_egress_routing_outcome_contracts as outcome_contracts
from mayak.modules.egress_routing import (
    DispatchAttempt,
    DispatchStatus,
    RouteReconciliationStatus,
    TransportAssignment,
    TransportAssignmentOutcome,
    TransportOutcomeCommitmentAuthority,
    TransportOutcomeCommitmentBoundary,
    TransportOutcomeStatus,
)


def _build_case(
    *,
    dispatch_status: DispatchStatus = DispatchStatus.SENT,
    outcome_status: TransportOutcomeStatus = TransportOutcomeStatus.SENT_NO_RESPONSE,
    **kwargs: object,
) -> dict[str, object]:
    state = outcome_contracts._build_state(
        dispatch_status=dispatch_status,
        outcome_status=outcome_status,
        **kwargs,
    )
    state["boundary"] = outcome_contracts._build_boundary(
        dispatch_status=dispatch_status,
        outcome_status=outcome_status,
        **kwargs,
    )
    return state


def _boundary(record: dict[str, object]) -> TransportOutcomeCommitmentBoundary:
    boundary = record["boundary"]
    assert isinstance(boundary, TransportOutcomeCommitmentBoundary)
    return boundary


def test_only_egress_server_commits_transport_outcome() -> None:
    boundary = _boundary(
        _build_case(
            dispatch_status=DispatchStatus.SENT,
            outcome_status=TransportOutcomeStatus.SENT_NO_RESPONSE,
        )
    )
    assert boundary.authority is TransportOutcomeCommitmentAuthority.EGRESS_ROUTING_SERVER
    assert boundary.outcome_committed is True
    assert boundary.new_dispatch_effect_authorized is False


def test_one_outcome_belongs_to_one_exact_assignment_and_attempt() -> None:
    record = _build_case(
        dispatch_status=DispatchStatus.SENT,
        outcome_status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
        safe_response_reference="safe-response-01",
    )
    boundary = _boundary(record)
    assignment = cast(TransportAssignment, record["assignment"])
    attempt = cast(DispatchAttempt, record["attempt"])
    outcome = cast(TransportAssignmentOutcome, record["outcome"])
    assert boundary.outcome.assignment_id == assignment.assignment_id
    assert boundary.outcome.attempt_id == attempt.attempt_id
    assert boundary.outcome.correlation_id == assignment.correlation_id == attempt.correlation_id
    assert boundary.outcome.causation_id == assignment.causation_id == attempt.causation_id
    assert isinstance(outcome, TransportAssignmentOutcome)


@pytest.mark.parametrize(
    "outcome_status",
    (
        TransportOutcomeStatus.NOT_SENT,
        TransportOutcomeStatus.DISPATCH_REJECTED,
    ),
)
def test_known_not_sent_outcomes_are_terminal(outcome_status: TransportOutcomeStatus) -> None:
    dispatch_status = (
        DispatchStatus.NOT_SENT
        if outcome_status is TransportOutcomeStatus.NOT_SENT
        else DispatchStatus.REJECTED
    )
    boundary = _boundary(
        _build_case(dispatch_status=dispatch_status, outcome_status=outcome_status)
    )
    assert boundary.assignment_terminal is True
    assert boundary.outcome.reconciliation_status in {
        RouteReconciliationStatus.NOT_REQUIRED,
        RouteReconciliationStatus.RESOLVED_NOT_SENT,
        RouteReconciliationStatus.RESOLVED_TERMINAL,
    }


@pytest.mark.parametrize(
    "outcome_status",
    (
        TransportOutcomeStatus.SENT_NO_RESPONSE,
        TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
        TransportOutcomeStatus.USABLE_RESPONSE_TRANSPORT_ONLY,
        TransportOutcomeStatus.RATE_OR_ACCESS_RESTRICTED,
        TransportOutcomeStatus.CAPTCHA_OR_CHALLENGE,
        TransportOutcomeStatus.PROVIDER_REJECTED,
        TransportOutcomeStatus.MALFORMED_RESPONSE_TRANSPORT_LAYER,
    ),
)
def test_known_sent_outcomes_are_terminal(outcome_status: TransportOutcomeStatus) -> None:
    boundary = _boundary(
        _build_case(
            dispatch_status=DispatchStatus.SENT,
            outcome_status=outcome_status,
        )
    )
    assert boundary.assignment_terminal is True
    assert boundary.outcome.reconciliation_status in {
        RouteReconciliationStatus.NOT_REQUIRED,
        RouteReconciliationStatus.RESOLVED_SENT,
        RouteReconciliationStatus.RESOLVED_TERMINAL,
    }


@pytest.mark.parametrize(
    "outcome_status",
    (
        TransportOutcomeStatus.DISPATCH_UNKNOWN,
        TransportOutcomeStatus.RECONCILIATION_REQUIRED,
    ),
)
def test_unknown_outcomes_are_non_terminal_and_reconcile_first(
    outcome_status: TransportOutcomeStatus,
) -> None:
    boundary = _boundary(
        _build_case(
            dispatch_status=DispatchStatus.UNKNOWN,
            outcome_status=outcome_status,
        )
    )
    assert boundary.assignment_terminal is False
    assert boundary.outcome.reconciliation_status in {
        RouteReconciliationStatus.REQUIRED,
        RouteReconciliationStatus.PENDING,
        RouteReconciliationStatus.REMAINS_AMBIGUOUS,
        RouteReconciliationStatus.MANUAL_REVIEW_REQUIRED,
    }


def test_no_blind_retry_or_second_attempt_is_created() -> None:
    record = _build_case(
        dispatch_status=DispatchStatus.SENT,
        outcome_status=TransportOutcomeStatus.SENT_NO_RESPONSE,
    )
    boundary = _boundary(record)
    dispatch_attempt = boundary.dispatch_attempt
    attempt = cast(DispatchAttempt, record["attempt"])
    dispatch_attempt_attempt = cast(DispatchAttempt, dispatch_attempt.attempt)
    assert dispatch_attempt_attempt.attempt_ordinal == 1
    assert dispatch_attempt_attempt.outcome_reference is None
    assert "retry_attempt" not in {field.name for field in fields(boundary)}
    assert "second_attempt" not in {field.name for field in fields(dispatch_attempt)}
    assert attempt.attempt_ordinal == 1


def test_safe_response_reference_remains_opaque() -> None:
    record = _build_case(
        dispatch_status=DispatchStatus.SENT,
        outcome_status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
        safe_response_reference="opaque-safe-response",
    )
    boundary = _boundary(record)
    assert boundary.outcome.safe_response_reference == "opaque-safe-response"
    assert boundary.outcome.safe_response_reference.startswith("opaque")
    assert "payload" not in {field.name for field in fields(boundary.outcome)}


def test_transport_only_usability_is_not_parser_success() -> None:
    boundary = _boundary(
        _build_case(
            dispatch_status=DispatchStatus.SENT,
            outcome_status=TransportOutcomeStatus.USABLE_RESPONSE_TRANSPORT_ONLY,
            safe_response_reference="safe-response-02",
        )
    )
    assert boundary.parser_success_inferred is False
    assert boundary.scan_success_inferred is False
    assert boundary.notification_delivery_inferred is False


def test_captcha_and_restriction_are_not_empty_results() -> None:
    captcha_boundary = _boundary(
        _build_case(
            dispatch_status=DispatchStatus.SENT,
            outcome_status=TransportOutcomeStatus.CAPTCHA_OR_CHALLENGE,
        )
    )
    restriction_boundary = _boundary(
        _build_case(
            dispatch_status=DispatchStatus.SENT,
            outcome_status=TransportOutcomeStatus.RATE_OR_ACCESS_RESTRICTED,
            safe_response_reference="safe-response-03",
        )
    )
    assert captcha_boundary.notification_delivery_inferred is False
    assert restriction_boundary.parser_success_inferred is False
    assert restriction_boundary.scan_success_inferred is False


def test_malformed_response_is_not_clean_success() -> None:
    boundary = _boundary(
        _build_case(
            dispatch_status=DispatchStatus.SENT,
            outcome_status=TransportOutcomeStatus.MALFORMED_RESPONSE_TRANSPORT_LAYER,
        )
    )
    assert boundary.parser_success_inferred is False
    assert boundary.scan_success_inferred is False
    assert boundary.notification_delivery_inferred is False


def test_no_baseline_anchor_listing_mutation() -> None:
    boundary = _boundary(
        _build_case(
            dispatch_status=DispatchStatus.SENT,
            outcome_status=TransportOutcomeStatus.SENT_NO_RESPONSE,
        )
    )
    field_names = {field.name for field in fields(boundary)}
    assert {"baseline", "anchor", "listing"}.isdisjoint(field_names)
    assert {"baseline", "anchor", "listing"}.isdisjoint(
        {field.name for field in fields(boundary.outcome)}
    )


def test_no_notification_delivery_is_created() -> None:
    boundary = _boundary(
        _build_case(
            dispatch_status=DispatchStatus.SENT,
            outcome_status=TransportOutcomeStatus.SENT_NO_RESPONSE,
        )
    )
    assert boundary.notification_delivery_inferred is False
    field_names = {field.name for field in fields(boundary)}
    assert "notification" not in field_names


def test_no_route_health_quarantine_fallback_mutation() -> None:
    boundary = _boundary(
        _build_case(
            dispatch_status=DispatchStatus.SENT,
            outcome_status=TransportOutcomeStatus.SENT_NO_RESPONSE,
        )
    )
    field_names = {field.name for field in fields(boundary)}
    banned = {
        "route_health",
        "health",
        "quarantine",
        "fallback",
        "policy_fallback",
        "retry",
        "replay",
    }
    assert banned.isdisjoint(field_names)


def test_no_provider_network_browser_runtime_storage_implementation() -> None:
    boundary = _boundary(
        _build_case(
            dispatch_status=DispatchStatus.SENT,
            outcome_status=TransportOutcomeStatus.SENT_NO_RESPONSE,
        )
    )
    field_names = {field.name for field in fields(boundary)}
    field_names.update(field.name for field in fields(boundary.outcome))
    banned = {
        "provider",
        "proxy",
        "vpn",
        "tunnel",
        "browser",
        "runtime",
        "storage",
        "database",
        "db",
        "host",
        "hostname",
        "ip",
        "port",
    }
    assert banned.isdisjoint(field_names)


def test_records_are_immutable() -> None:
    boundary = _boundary(
        _build_case(
            dispatch_status=DispatchStatus.SENT,
            outcome_status=TransportOutcomeStatus.SENT_NO_RESPONSE,
        )
    )
    with pytest.raises(Exception):
        boundary.boundary_id = "changed"  # type: ignore[misc]
    with pytest.raises(Exception):
        boundary.outcome.status = TransportOutcomeStatus.NOT_SENT  # type: ignore[misc]
    with pytest.raises(Exception):
        boundary.dispatch_attempt.attempt.attempt_ordinal = 2  # type: ignore[misc]
