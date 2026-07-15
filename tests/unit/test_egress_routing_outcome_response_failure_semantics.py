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
    TransportResponseFailureOutcomeAuthority,
    TransportResponseFailureOutcomeBoundary,
)
from mayak.modules.egress_routing import outcome_response_failure as failure_module


def _build_boundary(
    *,
    outcome_status: TransportOutcomeStatus,
    safe_response_reference: object,
    reconciliation_status: RouteReconciliationStatus,
) -> TransportResponseFailureOutcomeBoundary:
    state = outcome_contracts._build_state(
        dispatch_status=DispatchStatus.SENT,
        outcome_status=outcome_status,
        safe_response_reference=safe_response_reference,
        reconciliation_status=reconciliation_status,
    )
    state["authority"] = (
        failure_module.TransportResponseFailureOutcomeAuthority.EGRESS_ROUTING_SERVER
    )
    boundary = TransportResponseFailureOutcomeBoundary(
        boundary_id=cast(str, state["boundary_id"]),
        authority=cast(TransportResponseFailureOutcomeAuthority, state["authority"]),
        dispatch_attempt=cast(TransportDispatchAttemptBoundary, state["dispatch_boundary"]),
        outcome=cast(TransportAssignmentOutcome, state["outcome"]),
        outcome_committed=cast(bool, state["outcome_committed"]),
        new_dispatch_effect_authorized=cast(bool, state["new_dispatch_effect_authorized"]),
        assignment_terminal=cast(bool, state["assignment_terminal"]),
        parser_success_inferred=cast(bool, state["parser_success_inferred"]),
        scan_success_inferred=cast(bool, state["scan_success_inferred"]),
        notification_delivery_inferred=cast(bool, state["notification_delivery_inferred"]),
        reason_codes=cast(tuple[str, ...], state["reason_codes"]),
        evidence_reference_ids=cast(tuple[str, ...], state["evidence_reference_ids"]),
    )
    assert type(boundary) is TransportResponseFailureOutcomeBoundary
    return boundary


@pytest.mark.parametrize(
    ("outcome_status", "safe_response_reference", "reconciliation_status"),
    (
        (
            TransportOutcomeStatus.RATE_OR_ACCESS_RESTRICTED,
            None,
            RouteReconciliationStatus.NOT_REQUIRED,
        ),
        (
            TransportOutcomeStatus.CAPTCHA_OR_CHALLENGE,
            "opaque-safe-response",
            RouteReconciliationStatus.RESOLVED_SENT,
        ),
        (
            TransportOutcomeStatus.PROVIDER_REJECTED,
            "opaque-safe-response",
            RouteReconciliationStatus.RESOLVED_TERMINAL,
        ),
        (
            TransportOutcomeStatus.MALFORMED_RESPONSE_TRANSPORT_LAYER,
            None,
            RouteReconciliationStatus.RESOLVED_SENT,
        ),
    ),
)
def test_transport_failure_outcomes_remain_terminal_transport_facts(
    outcome_status: TransportOutcomeStatus,
    safe_response_reference: object,
    reconciliation_status: RouteReconciliationStatus,
) -> None:
    boundary = _build_boundary(
        outcome_status=outcome_status,
        safe_response_reference=safe_response_reference,
        reconciliation_status=reconciliation_status,
    )
    assert boundary.assignment_terminal is True
    assert boundary.outcome_committed is True
    assert boundary.new_dispatch_effect_authorized is False
    assert boundary.dispatch_attempt.dispatch_state_committed is True
    assert boundary.dispatch_attempt.new_dispatch_effect_authorized is False
    assert boundary.dispatch_attempt.attempt.dispatch_status is DispatchStatus.SENT
    assert boundary.dispatch_attempt.attempt.attempt_ordinal == 1
    assert boundary.dispatch_attempt.attempt.outcome_reference is None
    assert boundary.parser_success_inferred is False
    assert boundary.scan_success_inferred is False
    assert boundary.notification_delivery_inferred is False
    assert boundary.outcome.status is outcome_status
    assert boundary.outcome.safe_response_reference is safe_response_reference


def test_captcha_outcome_does_not_solve_captcha_or_create_side_effects() -> None:
    boundary = _build_boundary(
        outcome_status=TransportOutcomeStatus.CAPTCHA_OR_CHALLENGE,
        safe_response_reference="opaque-safe-response",
        reconciliation_status=RouteReconciliationStatus.RESOLVED_SENT,
    )
    field_names = {field.name for field in fields(boundary)}
    assert {"captcha_solver", "captcha_bypass", "fallback", "retry", "backoff"}.isdisjoint(
        field_names
    )
    assert boundary.outcome.safe_response_reference == "opaque-safe-response"


def test_rate_or_access_restricted_is_transport_only_failure() -> None:
    boundary = _build_boundary(
        outcome_status=TransportOutcomeStatus.RATE_OR_ACCESS_RESTRICTED,
        safe_response_reference="opaque-safe-response",
        reconciliation_status=RouteReconciliationStatus.NOT_REQUIRED,
    )
    assert boundary.outcome.status is TransportOutcomeStatus.RATE_OR_ACCESS_RESTRICTED
    assert boundary.parser_success_inferred is False
    assert boundary.scan_success_inferred is False
    assert boundary.notification_delivery_inferred is False
    assert boundary.assignment_terminal is True


def test_provider_rejected_is_transport_only_rejection() -> None:
    boundary = _build_boundary(
        outcome_status=TransportOutcomeStatus.PROVIDER_REJECTED,
        safe_response_reference="opaque-safe-response",
        reconciliation_status=RouteReconciliationStatus.RESOLVED_TERMINAL,
    )
    assert boundary.outcome.status is TransportOutcomeStatus.PROVIDER_REJECTED
    assert boundary.outcome.safe_response_reference == "opaque-safe-response"


def test_malformed_transport_layer_response_is_not_empty_result() -> None:
    boundary = _build_boundary(
        outcome_status=TransportOutcomeStatus.MALFORMED_RESPONSE_TRANSPORT_LAYER,
        safe_response_reference=None,
        reconciliation_status=RouteReconciliationStatus.RESOLVED_SENT,
    )
    assert boundary.outcome.status is TransportOutcomeStatus.MALFORMED_RESPONSE_TRANSPORT_LAYER
    assert boundary.outcome.safe_response_reference is None
    assert boundary.parser_success_inferred is False
    assert boundary.scan_success_inferred is False
    assert boundary.notification_delivery_inferred is False


def test_no_route_health_quarantine_or_fallback_mutation_is_produced() -> None:
    boundary = _build_boundary(
        outcome_status=TransportOutcomeStatus.PROVIDER_REJECTED,
        safe_response_reference="opaque-safe-response",
        reconciliation_status=RouteReconciliationStatus.RESOLVED_TERMINAL,
    )
    field_names = {field.name for field in fields(boundary)}
    assert {"route_health", "health", "quarantine", "fallback", "listing", "baseline"}.isdisjoint(
        field_names
    )


def test_no_parser_scan_or_notification_result_is_produced() -> None:
    boundary = _build_boundary(
        outcome_status=TransportOutcomeStatus.RATE_OR_ACCESS_RESTRICTED,
        safe_response_reference="opaque-safe-response",
        reconciliation_status=RouteReconciliationStatus.NOT_REQUIRED,
    )
    field_names = {field.name for field in fields(boundary.outcome)}
    assert {"Parser", "Scan", "Notification"}.isdisjoint(field_names)
    assert {"response_payload", "response_body", "receipt_payload", "send_payload"}.isdisjoint(
        field_names
    )
