from __future__ import annotations

from dataclasses import fields
from typing import cast

import pytest

import tests.contract.test_egress_routing_outcome_contracts as outcome_contracts
from mayak.modules.egress_routing import (
    DispatchStatus,
    RouteReconciliationStatus,
    TransportAssignmentOutcome,
    TransportDispatchAttemptBoundary,
    TransportOutcomeStatus,
    TransportResponsePresenceOutcomeAuthority,
    TransportResponsePresenceOutcomeBoundary,
)


def _build_state(
    *,
    outcome_status: TransportOutcomeStatus,
    safe_response_reference: object,
    reconciliation_status: RouteReconciliationStatus,
) -> dict[str, object]:
    state = outcome_contracts._build_state(
        dispatch_status=DispatchStatus.SENT,
        outcome_status=outcome_status,
        safe_response_reference=safe_response_reference,
        reconciliation_status=reconciliation_status,
    )
    state["authority"] = TransportResponsePresenceOutcomeAuthority.EGRESS_ROUTING_SERVER
    return state


def _build_boundary(
    *,
    outcome_status: TransportOutcomeStatus,
    safe_response_reference: object,
    reconciliation_status: RouteReconciliationStatus,
) -> TransportResponsePresenceOutcomeBoundary:
    state = _build_state(
        outcome_status=outcome_status,
        safe_response_reference=safe_response_reference,
        reconciliation_status=reconciliation_status,
    )
    boundary = TransportResponsePresenceOutcomeBoundary(
        boundary_id=cast(str, state["boundary_id"]),
        authority=cast(
            TransportResponsePresenceOutcomeAuthority,
            state["authority"],
        ),
        dispatch_attempt=cast(TransportDispatchAttemptBoundary, state["dispatch_boundary"]),
        outcome=cast(TransportAssignmentOutcome, state["outcome"]),
        outcome_committed=cast(bool, state["outcome_committed"]),
        new_dispatch_effect_authorized=cast(bool, state["new_dispatch_effect_authorized"]),
        assignment_terminal=cast(bool, state["assignment_terminal"]),
        parser_success_inferred=cast(bool, state["parser_success_inferred"]),
        scan_success_inferred=cast(bool, state["scan_success_inferred"]),
        notification_delivery_inferred=cast(
            bool,
            state["notification_delivery_inferred"],
        ),
        reason_codes=cast(tuple[str, ...], state["reason_codes"]),
        evidence_reference_ids=cast(tuple[str, ...], state["evidence_reference_ids"]),
    )
    assert type(boundary) is TransportResponsePresenceOutcomeBoundary
    return boundary


def test_sent_no_response_fixes_absence_of_safe_response_reference() -> None:
    boundary = _build_boundary(
        outcome_status=TransportOutcomeStatus.SENT_NO_RESPONSE,
        safe_response_reference=None,
        reconciliation_status=RouteReconciliationStatus.NOT_REQUIRED,
    )
    assert boundary.outcome.safe_response_reference is None
    assert boundary.outcome.status is TransportOutcomeStatus.SENT_NO_RESPONSE
    assert boundary.assignment_terminal is True
    assert boundary.new_dispatch_effect_authorized is False


def test_response_received_unclassified_is_transport_only() -> None:
    boundary = _build_boundary(
        outcome_status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
        safe_response_reference="opaque-safe-response-01",
        reconciliation_status=RouteReconciliationStatus.RESOLVED_SENT,
    )
    assert type(boundary.outcome.safe_response_reference) is str
    assert boundary.outcome.safe_response_reference == "opaque-safe-response-01"
    assert boundary.parser_success_inferred is False
    assert boundary.scan_success_inferred is False
    assert boundary.notification_delivery_inferred is False


def test_usable_response_transport_only_remains_transport_only() -> None:
    boundary = _build_boundary(
        outcome_status=TransportOutcomeStatus.USABLE_RESPONSE_TRANSPORT_ONLY,
        safe_response_reference="opaque-safe-response-02",
        reconciliation_status=RouteReconciliationStatus.RESOLVED_TERMINAL,
    )
    assert boundary.outcome.status is TransportOutcomeStatus.USABLE_RESPONSE_TRANSPORT_ONLY
    assert boundary.outcome.safe_response_reference == "opaque-safe-response-02"
    assert boundary.parser_success_inferred is False
    assert boundary.scan_success_inferred is False
    assert boundary.notification_delivery_inferred is False
    assert boundary.assignment_terminal is True


@pytest.mark.parametrize(
    "outcome_status",
    (
        TransportOutcomeStatus.SENT_NO_RESPONSE,
        TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
        TransportOutcomeStatus.USABLE_RESPONSE_TRANSPORT_ONLY,
    ),
)
def test_all_allowed_outcomes_are_terminal_and_block_new_dispatch_effect(
    outcome_status: TransportOutcomeStatus,
) -> None:
    safe_response_reference = {
        TransportOutcomeStatus.SENT_NO_RESPONSE: None,
        TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED: "opaque-safe-response-01",
        TransportOutcomeStatus.USABLE_RESPONSE_TRANSPORT_ONLY: "opaque-safe-response-02",
    }[outcome_status]
    reconciliation_status = {
        TransportOutcomeStatus.SENT_NO_RESPONSE: RouteReconciliationStatus.NOT_REQUIRED,
        TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED: (
            RouteReconciliationStatus.RESOLVED_SENT
        ),
        TransportOutcomeStatus.USABLE_RESPONSE_TRANSPORT_ONLY: (
            RouteReconciliationStatus.RESOLVED_TERMINAL
        ),
    }[outcome_status]
    boundary = _build_boundary(
        outcome_status=outcome_status,
        safe_response_reference=safe_response_reference,
        reconciliation_status=reconciliation_status,
    )
    assert boundary.assignment_terminal is True
    assert boundary.new_dispatch_effect_authorized is False
    assert boundary.outcome_committed is True
    assert boundary.dispatch_attempt.attempt.attempt_ordinal == 1
    assert boundary.dispatch_attempt.attempt.outcome_reference is None


def test_identity_and_causation_are_preserved() -> None:
    boundary = _build_boundary(
        outcome_status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
        safe_response_reference="opaque-safe-response-01",
        reconciliation_status=RouteReconciliationStatus.RESOLVED_SENT,
    )
    assignment = boundary.dispatch_attempt.assignment_commitment.assignment
    attempt = boundary.dispatch_attempt.attempt
    outcome = boundary.outcome
    assert outcome.assignment_id == assignment.assignment_id
    assert outcome.attempt_id == attempt.attempt_id
    assert outcome.correlation_id == assignment.correlation_id
    assert outcome.causation_id == assignment.causation_id
    assert attempt.assignment_id == assignment.assignment_id
    assert attempt.lease_id == assignment.lease_id
    assert attempt.route_id == assignment.route_id
    assert attempt.agent_id == assignment.agent_id
    assert attempt.correlation_id == assignment.correlation_id
    assert attempt.causation_id == assignment.causation_id


def test_no_second_attempt_or_parser_scan_notification_state_is_created() -> None:
    boundary = _build_boundary(
        outcome_status=TransportOutcomeStatus.SENT_NO_RESPONSE,
        safe_response_reference=None,
        reconciliation_status=RouteReconciliationStatus.NOT_REQUIRED,
    )
    field_names = {
        field.name
        for record in (boundary, boundary.dispatch_attempt, boundary.outcome)
        for field in fields(record)
    }
    assert {"second_attempt", "retry_attempt", "retry", "fallback"}.isdisjoint(field_names)
    assert {"Parser", "Scan", "Notification"}.isdisjoint(field_names)
