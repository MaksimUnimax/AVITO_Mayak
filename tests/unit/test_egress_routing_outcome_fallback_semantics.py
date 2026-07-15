from __future__ import annotations

from dataclasses import fields

import pytest

from mayak.modules.egress_routing import (
    PolicyBasedFallbackStatus,
    RouteReconciliationStatus,
    TransportOutcomeStatus,
)
import tests.contract.test_egress_routing_outcome_fallback_contracts as outcome_fallback_contracts


def _boundary(
    fallback_status: PolicyBasedFallbackStatus,
    reconciliation_status: RouteReconciliationStatus,
    *,
    outcome_status: TransportOutcomeStatus | None = None,
) -> object:
    return outcome_fallback_contracts._construct(
        fallback_status=fallback_status,
        reconciliation_status=reconciliation_status,
        outcome_status=outcome_status,
    )


@pytest.mark.parametrize(
    "fallback_status, expected_terminal, expected_outcome_status",
    (
        (
            PolicyBasedFallbackStatus.ATTEMPTED,
            False,
            TransportOutcomeStatus.POLICY_FALLBACK_ATTEMPTED,
        ),
        (
            PolicyBasedFallbackStatus.EXHAUSTED,
            True,
            TransportOutcomeStatus.POLICY_FALLBACK_EXHAUSTED,
        ),
        (
            PolicyBasedFallbackStatus.NO_APPROVED_ROUTE,
            True,
            TransportOutcomeStatus.NO_APPROVED_ROUTE_AVAILABLE,
        ),
    ),
)
def test_supported_statuses_are_transport_facts(
    fallback_status: PolicyBasedFallbackStatus,
    expected_terminal: bool,
    expected_outcome_status: TransportOutcomeStatus,
) -> None:
    boundary = _boundary(fallback_status, RouteReconciliationStatus.NOT_REQUIRED)

    assert boundary.transport_terminal is expected_terminal
    assert boundary.outcome_status is expected_outcome_status
    assert boundary.outcome_committed is True
    assert boundary.new_fallback_effect_authorized is False
    assert boundary.parser_success_inferred is False
    assert boundary.scan_success_inferred is False
    assert boundary.notification_delivery_inferred is False


@pytest.mark.parametrize(
    "fallback_status",
    (
        PolicyBasedFallbackStatus.ATTEMPTED,
        PolicyBasedFallbackStatus.EXHAUSTED,
        PolicyBasedFallbackStatus.NO_APPROVED_ROUTE,
    ),
)
def test_supported_statuses_do_not_imply_parser_scan_or_notification(
    fallback_status: PolicyBasedFallbackStatus,
) -> None:
    boundary = _boundary(fallback_status, RouteReconciliationStatus.RESOLVED_SENT)
    boundary_fields = {field.name for field in fields(boundary)}
    nested_fields = {field.name for field in fields(boundary.fallback)}
    nested_fields.update(field.name for field in fields(boundary.fallback.decision))
    nested_fields.update(field.name for field in fields(boundary.fallback.original_selection))
    nested_fields.update(field.name for field in fields(boundary.fallback.original_selection.decision))
    nested_fields.update(field.name for field in fields(boundary.fallback.fallback_candidate_evaluations[0]))

    banned = {
        "listing",
        "baseline",
        "anchor",
        "parser",
        "scan",
        "notification",
        "assignment",
        "dispatch",
        "response",
        "retry",
        "replay",
        "backoff",
        "captcha_solver",
        "captcha_bypass",
        "route_health",
        "quarantine",
    }
    assert banned.isdisjoint(boundary_fields)
    assert banned.isdisjoint(nested_fields)


def test_route_degraded_and_quarantined_remain_unsupported_here() -> None:
    with pytest.raises(ValueError):
        _boundary(
            PolicyBasedFallbackStatus.ATTEMPTED,
            RouteReconciliationStatus.NOT_REQUIRED,
            outcome_status=TransportOutcomeStatus.ROUTE_DEGRADED,
        )

    with pytest.raises(ValueError):
        _boundary(
            PolicyBasedFallbackStatus.ATTEMPTED,
            RouteReconciliationStatus.NOT_REQUIRED,
            outcome_status=TransportOutcomeStatus.ROUTE_QUARANTINED,
        )


def test_no_empty_listing_or_assignment_dispatch_is_created() -> None:
    boundary = _boundary(
        PolicyBasedFallbackStatus.NO_APPROVED_ROUTE,
        RouteReconciliationStatus.NOT_REQUIRED,
    )

    assert boundary.fallback.fallback_candidate_evaluations
    assert "listing" not in {field.name for field in fields(boundary)}
    assert "assignment" not in {field.name for field in fields(boundary)}
    assert "dispatch" not in {field.name for field in fields(boundary)}
