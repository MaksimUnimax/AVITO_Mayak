from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
from typing import Any, cast

import pytest

import tests.contract.test_egress_routing_outcome_availability_contracts as contracts
from mayak.modules.egress_routing import (
    DispatchStatus,
    RouteReconciliationStatus,
    TransportAvailabilityOutcomeBoundary,
    TransportOutcomeStatus,
)


def _boundary(
    dispatch_status: DispatchStatus,
    outcome_status: TransportOutcomeStatus,
    **kwargs: object,
) -> TransportAvailabilityOutcomeBoundary:
    return contracts._build_boundary(
        dispatch_status=dispatch_status,
        outcome_status=outcome_status,
        **kwargs,
    )


def _field_names(*records: object) -> set[str]:
    names: set[str] = set()
    for record in records:
        names.update(field.name for field in fields(cast(Any, record)))
    return names


def _snapshot(record: object) -> tuple[object, ...]:
    return tuple(getattr(record, field.name) for field in fields(cast(Any, record)))


def test_unavailable_is_known_not_sent_terminal() -> None:
    boundary = _boundary(
        DispatchStatus.NOT_SENT,
        TransportOutcomeStatus.TRANSPORT_UNAVAILABLE,
    )
    assert boundary.assignment_terminal is True
    assert boundary.outcome.reconciliation_status in {
        RouteReconciliationStatus.NOT_REQUIRED,
        RouteReconciliationStatus.RESOLVED_NOT_SENT,
        RouteReconciliationStatus.RESOLVED_TERMINAL,
    }
    assert boundary.dispatch_attempt.attempt.dispatch_status is DispatchStatus.NOT_SENT
    assert boundary.dispatch_attempt.attempt.attempt_ordinal == 1
    assert boundary.dispatch_attempt.attempt.outcome_reference is None


def test_timeout_is_known_sent_terminal() -> None:
    boundary = _boundary(
        DispatchStatus.SENT,
        TransportOutcomeStatus.TRANSPORT_TIMEOUT,
    )
    assert boundary.assignment_terminal is True
    assert boundary.outcome.reconciliation_status in {
        RouteReconciliationStatus.NOT_REQUIRED,
        RouteReconciliationStatus.RESOLVED_SENT,
        RouteReconciliationStatus.RESOLVED_TERMINAL,
    }
    assert boundary.dispatch_attempt.attempt.dispatch_status is DispatchStatus.SENT


def test_ambiguous_is_unresolved_non_terminal() -> None:
    boundary = _boundary(
        DispatchStatus.UNKNOWN,
        TransportOutcomeStatus.TRANSPORT_AMBIGUOUS,
        reconciliation_status=RouteReconciliationStatus.REQUIRED,
        assignment_terminal=False,
    )
    assert boundary.assignment_terminal is False
    assert boundary.outcome.reconciliation_status in {
        RouteReconciliationStatus.REQUIRED,
        RouteReconciliationStatus.PENDING,
        RouteReconciliationStatus.REMAINS_AMBIGUOUS,
        RouteReconciliationStatus.MANUAL_REVIEW_REQUIRED,
    }
    assert boundary.dispatch_attempt.attempt.dispatch_status is DispatchStatus.UNKNOWN


def test_no_blind_retry_and_no_second_attempt() -> None:
    boundary = _boundary(
        DispatchStatus.UNKNOWN,
        TransportOutcomeStatus.TRANSPORT_AMBIGUOUS,
        reconciliation_status=RouteReconciliationStatus.REQUIRED,
        assignment_terminal=False,
    )
    field_names = _field_names(boundary, boundary.dispatch_attempt, boundary.outcome)
    assert boundary.dispatch_attempt.attempt.attempt_ordinal == 1
    assert boundary.dispatch_attempt.attempt.outcome_reference is None
    assert {"retry", "second_attempt", "replay", "fallback"}.isdisjoint(field_names)


def test_no_false_success_and_no_parser_scan_notification_objects() -> None:
    boundary = _boundary(
        DispatchStatus.NOT_SENT,
        TransportOutcomeStatus.TRANSPORT_UNAVAILABLE,
    )
    assert boundary.outcome_committed is True
    assert boundary.new_dispatch_effect_authorized is False
    assert boundary.parser_success_inferred is False
    assert boundary.scan_success_inferred is False
    assert boundary.notification_delivery_inferred is False
    field_names = _field_names(boundary, boundary.dispatch_attempt, boundary.outcome)
    assert {"parser", "scan", "notification"}.isdisjoint({name.lower() for name in field_names})


def test_no_route_health_quarantine_fallback_mutation_and_no_runtime_behavior() -> None:
    boundary = _boundary(
        DispatchStatus.SENT,
        TransportOutcomeStatus.TRANSPORT_TIMEOUT,
    )
    field_names = _field_names(boundary, boundary.dispatch_attempt, boundary.outcome)
    banned = {
        "route_health",
        "health",
        "quarantine",
        "fallback",
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


def test_boundary_is_immutable() -> None:
    boundary = _boundary(
        DispatchStatus.NOT_SENT,
        TransportOutcomeStatus.TRANSPORT_UNAVAILABLE,
    )
    snapshot = _snapshot(boundary)
    dispatch_snapshot = _snapshot(boundary.dispatch_attempt)
    outcome_snapshot = _snapshot(boundary.outcome)

    with pytest.raises(FrozenInstanceError):
        boundary.boundary_id = "changed"  # type: ignore[misc]

    assert _snapshot(boundary) == snapshot
    assert _snapshot(boundary.dispatch_attempt) == dispatch_snapshot
    assert _snapshot(boundary.outcome) == outcome_snapshot
