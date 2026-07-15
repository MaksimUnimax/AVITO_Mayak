from __future__ import annotations

from dataclasses import fields
from typing import Any, cast

import pytest

import tests.contract.test_egress_routing_dispatch_contracts as dispatch_contracts
from mayak.modules.egress_routing import (
    DispatchAttempt,
    DispatchStatus,
    RouteReconciliationState,
    RouteReconciliationStatus,
    TransportDispatchAttemptBoundary,
    TransportDispatchAuthority,
    TransportDispatchReconciliationAuthority,
    TransportDispatchReconciliationBoundary,
)


def _build_dispatch_state() -> dict[str, object]:
    return dispatch_contracts._build_valid_state(
        dispatch_status=DispatchStatus.UNKNOWN,
        new_dispatch_effect_authorized=False,
        reconciliation_required=True,
        attempt_ordinal=1,
        outcome_reference=None,
    )


def _build_reconciliation_state(
    *,
    status: RouteReconciliationStatus = RouteReconciliationStatus.REQUIRED,
    resolved_outcome_reference: str | None = None,
) -> RouteReconciliationState:
    dispatch_state = _build_dispatch_state()
    attempt = dispatch_state["attempt"]
    assert isinstance(attempt, DispatchAttempt)
    return RouteReconciliationState(
        reconciliation_id="reconciliation-01",
        assignment_id=attempt.assignment_id,
        attempt_id=attempt.attempt_id,
        status=status,
        reason_codes=("reconciliation-required",),
        evidence_reference_ids=("evidence-reconciliation-state-01",),
        resolved_outcome_reference=resolved_outcome_reference,
    )


def _mutate(record: object, **changes: object) -> None:
    for field_name, value in changes.items():
        object.__setattr__(record, field_name, value)


def _build_boundary(
    *,
    status: RouteReconciliationStatus = RouteReconciliationStatus.REQUIRED,
    resolved_outcome_reference: str | None = None,
) -> TransportDispatchReconciliationBoundary:
    dispatch_state = _build_dispatch_state()
    dispatch_boundary = dispatch_state["boundary"]
    attempt = dispatch_state["attempt"]
    assert isinstance(dispatch_boundary, TransportDispatchAttemptBoundary)
    assert isinstance(attempt, DispatchAttempt)
    reconciliation_state = _build_reconciliation_state(
        status=status,
        resolved_outcome_reference=resolved_outcome_reference,
    )
    return TransportDispatchReconciliationBoundary(
        boundary_id="reconciliation-boundary-01",
        authority=TransportDispatchReconciliationAuthority.EGRESS_ROUTING_SERVER,
        dispatch_attempt=dispatch_boundary,
        reconciliation_state=reconciliation_state,
        reconciliation_state_committed=True,
        new_dispatch_effect_authorized=False,
        assignment_terminal=False,
        reason_codes=("reconciliation-committed",),
        evidence_reference_ids=("evidence-reconciliation-boundary-01",),
    )


def _field_names(*records: object) -> set[str]:
    names: set[str] = set()
    for record in records:
        names.update(field.name for field in fields(cast(Any, record)))
    return names


def _snapshot(record: object) -> tuple[object, ...]:
    return tuple(getattr(record, field.name) for field in fields(cast(Any, record)))


def test_only_egress_server_commits_reconciliation_state() -> None:
    boundary = _build_boundary()
    assert boundary.authority is TransportDispatchReconciliationAuthority.EGRESS_ROUTING_SERVER
    assert boundary.reconciliation_state_committed is True


def test_only_unknown_dispatch_enters_er06e() -> None:
    boundary = _build_boundary()
    assert boundary.dispatch_attempt.authority is TransportDispatchAuthority.EGRESS_ROUTING_SERVER
    assert boundary.dispatch_attempt.attempt.dispatch_status is DispatchStatus.UNKNOWN
    assert boundary.dispatch_attempt.attempt.reconciliation_required is True


def test_exact_assignment_identity_preserved() -> None:
    boundary = _build_boundary()
    assert (
        boundary.reconciliation_state.assignment_id
        == boundary.dispatch_attempt.attempt.assignment_id
    )


def test_exact_attempt_identity_preserved() -> None:
    boundary = _build_boundary()
    assert boundary.reconciliation_state.attempt_id == boundary.dispatch_attempt.attempt.attempt_id


def test_no_second_attempt_created() -> None:
    boundary = _build_boundary()
    assert boundary.dispatch_attempt.attempt.attempt_ordinal == 1
    assert boundary.dispatch_attempt.attempt.outcome_reference is None
    assert "second_attempt" not in _field_names(
        boundary,
        boundary.dispatch_attempt,
        boundary.reconciliation_state,
    )


def test_new_dispatch_effect_is_always_blocked() -> None:
    boundary = _build_boundary()
    assert boundary.new_dispatch_effect_authorized is False
    assert boundary.dispatch_attempt.new_dispatch_effect_authorized is False


def test_blind_replay_remains_blocked() -> None:
    boundary = _build_boundary()
    assert boundary.dispatch_attempt.attempt.dispatch_status is DispatchStatus.UNKNOWN
    assert boundary.new_dispatch_effect_authorized is False
    assert boundary.assignment_terminal is False


def test_required_remains_unresolved() -> None:
    boundary = _build_boundary(status=RouteReconciliationStatus.REQUIRED)
    assert boundary.reconciliation_state.status is RouteReconciliationStatus.REQUIRED
    assert boundary.reconciliation_state.resolved_outcome_reference is None


def test_pending_does_not_choose_worker_runtime() -> None:
    boundary = _build_boundary(status=RouteReconciliationStatus.PENDING)
    field_names = _field_names(boundary, boundary.dispatch_attempt, boundary.reconciliation_state)
    banned = {
        "worker_id",
        "runtime",
        "timeout_seconds",
        "deadline",
        "source_endpoint",
        "source_priority",
    }
    assert banned.isdisjoint(field_names)
    assert boundary.reconciliation_state.status is RouteReconciliationStatus.PENDING


def test_remains_ambiguous_produces_no_outcome() -> None:
    boundary = _build_boundary(status=RouteReconciliationStatus.REMAINS_AMBIGUOUS)
    field_names = _field_names(boundary, boundary.dispatch_attempt, boundary.reconciliation_state)
    banned = {
        "outcome_id",
        "transport_outcome",
        "safe_response_reference",
        "response_status",
        "response_body",
        "receipt_payload",
        "send_payload",
    }
    assert banned.isdisjoint(field_names)
    assert boundary.reconciliation_state.resolved_outcome_reference is None


def test_manual_review_required_does_not_grant_admin_direct_mutation() -> None:
    boundary = _build_boundary(status=RouteReconciliationStatus.MANUAL_REVIEW_REQUIRED)
    field_names = _field_names(boundary, boundary.dispatch_attempt, boundary.reconciliation_state)
    banned = {"admin", "mutation", "worker", "runtime"}
    assert banned.isdisjoint(field_names)
    assert boundary.assignment_terminal is False


@pytest.mark.parametrize(
    "status",
    [
        RouteReconciliationStatus.REQUIRED,
        RouteReconciliationStatus.PENDING,
        RouteReconciliationStatus.REMAINS_AMBIGUOUS,
        RouteReconciliationStatus.MANUAL_REVIEW_REQUIRED,
    ],
)
def test_no_unresolved_status_is_assignment_terminal(status: RouteReconciliationStatus) -> None:
    boundary = _build_boundary(status=status)
    assert boundary.assignment_terminal is False


@pytest.mark.parametrize(
    "status",
    [
        RouteReconciliationStatus.NOT_REQUIRED,
        RouteReconciliationStatus.RESOLVED_NOT_SENT,
        RouteReconciliationStatus.RESOLVED_SENT,
        RouteReconciliationStatus.RESOLVED_TERMINAL,
    ],
)
def test_no_resolved_status_is_accepted(status: RouteReconciliationStatus) -> None:
    if status is RouteReconciliationStatus.NOT_REQUIRED:
        reconciliation_state = _build_reconciliation_state(status=status)
    else:
        reconciliation_state = _build_reconciliation_state(
            status=status,
            resolved_outcome_reference="resolved-outcome-01",
        )
    dispatch_state = _build_dispatch_state()
    dispatch_boundary = dispatch_state["boundary"]
    assert isinstance(dispatch_boundary, TransportDispatchAttemptBoundary)
    with pytest.raises(ValueError):
        TransportDispatchReconciliationBoundary(
            boundary_id="reconciliation-boundary-01",
            authority=TransportDispatchReconciliationAuthority.EGRESS_ROUTING_SERVER,
            dispatch_attempt=dispatch_boundary,
            reconciliation_state=reconciliation_state,
            reconciliation_state_committed=True,
            new_dispatch_effect_authorized=False,
            assignment_terminal=False,
            reason_codes=("reconciliation-committed",),
            evidence_reference_ids=("evidence-reconciliation-boundary-01",),
        )


@pytest.mark.parametrize(
    "status",
    [
        RouteReconciliationStatus.REQUIRED,
        RouteReconciliationStatus.PENDING,
        RouteReconciliationStatus.REMAINS_AMBIGUOUS,
        RouteReconciliationStatus.MANUAL_REVIEW_REQUIRED,
    ],
)
def test_no_resolved_outcome_reference_is_accepted(status: RouteReconciliationStatus) -> None:
    reconciliation_state = _build_reconciliation_state(status=status)
    if status is RouteReconciliationStatus.REMAINS_AMBIGUOUS:
        _mutate(reconciliation_state, resolved_outcome_reference="outcome-01")
    else:
        _mutate(reconciliation_state, resolved_outcome_reference="outcome-01")
    dispatch_state = _build_dispatch_state()
    dispatch_boundary = dispatch_state["boundary"]
    assert isinstance(dispatch_boundary, TransportDispatchAttemptBoundary)
    with pytest.raises(ValueError):
        TransportDispatchReconciliationBoundary(
            boundary_id="reconciliation-boundary-01",
            authority=TransportDispatchReconciliationAuthority.EGRESS_ROUTING_SERVER,
            dispatch_attempt=dispatch_boundary,
            reconciliation_state=reconciliation_state,
            reconciliation_state_committed=True,
            new_dispatch_effect_authorized=False,
            assignment_terminal=False,
            reason_codes=("reconciliation-committed",),
            evidence_reference_ids=("evidence-reconciliation-boundary-01",),
        )


def test_no_transport_assignment_outcome_is_created() -> None:
    boundary = _build_boundary()
    field_names = _field_names(boundary, boundary.dispatch_attempt, boundary.reconciliation_state)
    banned = {
        "outcome_id",
        "transport_outcome",
        "TransportAssignmentOutcome",
    }
    assert banned.isdisjoint(field_names)


def test_no_send_not_sent_or_response_inference() -> None:
    boundary = _build_boundary()
    field_names = _field_names(boundary, boundary.dispatch_attempt, boundary.reconciliation_state)
    banned = {
        "send_payload",
        "receipt_payload",
        "response_status",
        "response_body",
        "safe_response_reference",
        "not_sent",
    }
    assert banned.isdisjoint(field_names)


def test_no_transport_success_parser_success_or_scan_success_inference() -> None:
    boundary = _build_boundary()
    field_names = _field_names(boundary, boundary.dispatch_attempt, boundary.reconciliation_state)
    banned = {
        "transport_success",
        "parser_success",
        "scan_success",
        "parser",
        "scan",
    }
    assert banned.isdisjoint(field_names)


def test_no_reconciliation_source_priority_timeout_is_chosen() -> None:
    boundary = _build_boundary()
    field_names = _field_names(boundary, boundary.dispatch_attempt, boundary.reconciliation_state)
    banned = {
        "reconciliation_source",
        "source_priority",
        "source_endpoint",
        "timeout_seconds",
        "timeout",
        "deadline",
        "ttl",
    }
    assert banned.isdisjoint(field_names)


def test_no_storage_ttl_retry_backoff_is_chosen() -> None:
    boundary = _build_boundary()
    field_names = _field_names(boundary, boundary.dispatch_attempt, boundary.reconciliation_state)
    banned = {
        "storage_reference",
        "database_reference",
        "retry_count",
        "retry_delay",
        "backoff",
        "duration",
        "expires_at",
    }
    assert banned.isdisjoint(field_names)


def test_no_provider_proxy_vpn_tunnel_is_selected() -> None:
    boundary = _build_boundary()
    field_names = _field_names(boundary, boundary.dispatch_attempt, boundary.reconciliation_state)
    banned = {"provider", "proxy", "vpn", "tunnel", "protocol"}
    assert banned.isdisjoint(field_names)


def test_no_browser_or_windows_topology_is_modelled() -> None:
    boundary = _build_boundary()
    field_names = _field_names(boundary, boundary.dispatch_attempt, boundary.reconciliation_state)
    banned = {"browser", "windows", "host", "hostname", "ip", "port"}
    assert banned.isdisjoint(field_names)


def test_no_mutation_of_nested_dispatch_assignment_or_lease_records() -> None:
    state = dispatch_contracts._build_valid_state(
        dispatch_status=DispatchStatus.UNKNOWN,
        new_dispatch_effect_authorized=False,
        reconciliation_required=True,
        attempt_ordinal=1,
        outcome_reference=None,
    )
    boundary = state["boundary"]
    dispatch_attempt = state["attempt"]
    assignment_commitment = state["assignment_commitment"]
    lease_authorization = state["lease_authorization"]
    lease = state["lease"]
    assignment = state["assignment"]
    reconciliation_state = _build_reconciliation_state()
    snapshots_before = (
        _snapshot(dispatch_attempt),
        _snapshot(assignment_commitment),
        _snapshot(lease_authorization),
        _snapshot(lease),
        _snapshot(assignment),
    )
    constructed = TransportDispatchReconciliationBoundary(
        boundary_id="reconciliation-boundary-01",
        authority=TransportDispatchReconciliationAuthority.EGRESS_ROUTING_SERVER,
        dispatch_attempt=boundary,
        reconciliation_state=reconciliation_state,
        reconciliation_state_committed=True,
        new_dispatch_effect_authorized=False,
        assignment_terminal=False,
        reason_codes=("reconciliation-committed",),
        evidence_reference_ids=("evidence-reconciliation-boundary-01",),
    )
    assert constructed.assignment_terminal is False
    snapshots_after = (
        _snapshot(dispatch_attempt),
        _snapshot(assignment_commitment),
        _snapshot(lease_authorization),
        _snapshot(lease),
        _snapshot(assignment),
    )
    assert snapshots_after == snapshots_before
