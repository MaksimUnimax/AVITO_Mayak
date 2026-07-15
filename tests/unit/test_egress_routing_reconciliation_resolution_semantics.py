from __future__ import annotations

from dataclasses import fields
from pathlib import Path
from typing import Any, cast

import pytest

import tests.contract.test_egress_routing_reconciliation_contracts as reconciliation_contracts
from mayak.modules.egress_routing import (
    ER06F_TASK_ID,
    RouteReconciliationState,
    RouteReconciliationStatus,
    TransportDispatchReconciliationAuthority,
    TransportDispatchReconciliationBoundary,
    TransportDispatchReconciliationResolutionAuthority,
    TransportDispatchReconciliationResolutionBoundary,
)

EXPECTED_TASK_ID = "ER-06F-RESOLVED-DISPATCH-RECONCILIATION-BOUNDARY-20260715-015"

EXPECTED_SOURCE_STATUSES = (
    RouteReconciliationStatus.REQUIRED,
    RouteReconciliationStatus.PENDING,
    RouteReconciliationStatus.REMAINS_AMBIGUOUS,
    RouteReconciliationStatus.MANUAL_REVIEW_REQUIRED,
)

EXPECTED_TARGET_STATUSES = (
    RouteReconciliationStatus.RESOLVED_NOT_SENT,
    RouteReconciliationStatus.RESOLVED_SENT,
    RouteReconciliationStatus.RESOLVED_TERMINAL,
)


def _mutate(record: object, **changes: object) -> None:
    for field_name, value in changes.items():
        object.__setattr__(record, field_name, value)


def _build_boundary(
    *,
    source_status: RouteReconciliationStatus = RouteReconciliationStatus.REQUIRED,
    target_status: RouteReconciliationStatus = RouteReconciliationStatus.RESOLVED_NOT_SENT,
) -> TransportDispatchReconciliationResolutionBoundary:
    unresolved_reconciliation = reconciliation_contracts._build_boundary(
        reconciliation_status=source_status
    )
    assert isinstance(unresolved_reconciliation, TransportDispatchReconciliationBoundary)
    source_state = unresolved_reconciliation.reconciliation_state
    assert isinstance(source_state, RouteReconciliationState)
    resolved_reconciliation_state = RouteReconciliationState(
        reconciliation_id=source_state.reconciliation_id,
        assignment_id=source_state.assignment_id,
        attempt_id=source_state.attempt_id,
        status=target_status,
        reason_codes=("resolved-reconciliation",),
        evidence_reference_ids=("evidence-resolution-state-01",),
        resolved_outcome_reference=f"resolved-outcome-{source_status.name.lower()}-{target_status.name.lower()}",
    )
    return TransportDispatchReconciliationResolutionBoundary(
        boundary_id="resolution-boundary-01",
        authority=TransportDispatchReconciliationResolutionAuthority.EGRESS_ROUTING_SERVER,
        unresolved_reconciliation=unresolved_reconciliation,
        resolved_reconciliation_state=resolved_reconciliation_state,
        resolution_committed=True,
        new_dispatch_effect_authorized=False,
        assignment_terminal=True,
        reason_codes=("resolution-committed",),
        evidence_reference_ids=("evidence-resolution-boundary-01",),
    )


def _field_names(*records: object) -> set[str]:
    names: set[str] = set()
    for record in records:
        names.update(field.name for field in fields(cast(Any, record)))
    return names


def _snapshot(record: object) -> tuple[object, ...]:
    dataclass_record = cast(Any, record)
    return tuple(getattr(dataclass_record, field.name) for field in fields(dataclass_record))


def test_task_id_is_bound_to_the_resolution_boundary() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    source = (
        repo_root / "src/mayak/modules/egress_routing/reconciliation_resolution.py"
    ).read_text()
    assert ER06F_TASK_ID == EXPECTED_TASK_ID
    assert source.count(ER06F_TASK_ID) == 1


def test_only_egress_server_commits_resolution() -> None:
    boundary = _build_boundary()
    assert (
        boundary.authority
        is TransportDispatchReconciliationResolutionAuthority.EGRESS_ROUTING_SERVER
    )
    assert boundary.resolution_committed is True
    assert boundary.new_dispatch_effect_authorized is False
    assert boundary.assignment_terminal is True


def test_only_accepted_er06e_unresolved_boundary_is_input() -> None:
    boundary = _build_boundary(source_status=RouteReconciliationStatus.REMAINS_AMBIGUOUS)
    source = boundary.unresolved_reconciliation
    source_state = source.reconciliation_state
    assert source.authority is TransportDispatchReconciliationAuthority.EGRESS_ROUTING_SERVER
    assert source.reconciliation_state_committed is True
    assert source.new_dispatch_effect_authorized is False
    assert source.assignment_terminal is False
    assert source_state.status is RouteReconciliationStatus.REMAINS_AMBIGUOUS
    assert source_state.resolved_outcome_reference is None


@pytest.mark.parametrize("source_status", EXPECTED_SOURCE_STATUSES)
@pytest.mark.parametrize("target_status", EXPECTED_TARGET_STATUSES)
def test_same_reconciliation_assignment_and_attempt_identity_is_preserved(
    source_status: RouteReconciliationStatus,
    target_status: RouteReconciliationStatus,
) -> None:
    boundary = _build_boundary(source_status=source_status, target_status=target_status)
    source_state = boundary.unresolved_reconciliation.reconciliation_state
    target_state = boundary.resolved_reconciliation_state
    assert target_state.reconciliation_id == source_state.reconciliation_id
    assert target_state.assignment_id == source_state.assignment_id
    assert target_state.attempt_id == source_state.attempt_id


@pytest.mark.parametrize("target_status", EXPECTED_TARGET_STATUSES)
def test_resolved_outcome_reference_is_required_and_opaque(
    target_status: RouteReconciliationStatus,
) -> None:
    boundary = _build_boundary(target_status=target_status)
    source_state = boundary.unresolved_reconciliation.reconciliation_state
    target_state = boundary.resolved_reconciliation_state
    assert source_state.resolved_outcome_reference is None
    assert target_state.resolved_outcome_reference is not None
    assert type(target_state.resolved_outcome_reference) is str
    assert target_state.resolved_outcome_reference.strip()
    assert target_state.resolved_outcome_reference.startswith("resolved-outcome-")


@pytest.mark.parametrize("target_status", EXPECTED_TARGET_STATUSES)
def test_all_target_statuses_are_assignment_terminal(
    target_status: RouteReconciliationStatus,
) -> None:
    boundary = _build_boundary(target_status=target_status)
    assert boundary.assignment_terminal is True


def test_new_dispatch_remains_blocked() -> None:
    boundary = _build_boundary(target_status=RouteReconciliationStatus.RESOLVED_NOT_SENT)
    assert boundary.new_dispatch_effect_authorized is False
    assert boundary.unresolved_reconciliation.new_dispatch_effect_authorized is False
    assert (
        boundary.resolved_reconciliation_state.status is RouteReconciliationStatus.RESOLVED_NOT_SENT
    )


def test_second_attempt_is_never_created() -> None:
    boundary = _build_boundary(target_status=RouteReconciliationStatus.RESOLVED_SENT)
    source_state = boundary.unresolved_reconciliation.reconciliation_state
    assert boundary.unresolved_reconciliation.dispatch_attempt.attempt.attempt_ordinal == 1
    assert boundary.unresolved_reconciliation.dispatch_attempt.attempt.outcome_reference is None
    assert "second_attempt" not in _field_names(
        boundary, boundary.unresolved_reconciliation, source_state
    )
    assert "retry_attempt" not in _field_names(
        boundary, boundary.unresolved_reconciliation, source_state
    )


def test_blind_replay_remains_blocked() -> None:
    boundary = _build_boundary(target_status=RouteReconciliationStatus.RESOLVED_TERMINAL)
    field_names = _field_names(boundary, boundary.unresolved_reconciliation)
    banned = {"replay", "blind_replay", "retry", "fallback"}
    assert banned.isdisjoint(field_names)
    assert boundary.assignment_terminal is True


def test_source_and_target_records_remain_immutable() -> None:
    boundary = _build_boundary(target_status=RouteReconciliationStatus.RESOLVED_NOT_SENT)
    source = boundary.unresolved_reconciliation
    target = boundary.resolved_reconciliation_state
    source_snapshot = _snapshot(source)
    target_snapshot = _snapshot(target)
    boundary_snapshot = _snapshot(boundary)

    assert (
        boundary.authority
        is TransportDispatchReconciliationResolutionAuthority.EGRESS_ROUTING_SERVER
    )
    assert source.authority is TransportDispatchReconciliationAuthority.EGRESS_ROUTING_SERVER
    assert target.status is RouteReconciliationStatus.RESOLVED_NOT_SENT

    assert _snapshot(boundary) == boundary_snapshot
    assert _snapshot(source) == source_snapshot
    assert _snapshot(target) == target_snapshot


def test_no_transport_assignment_outcome_object_created() -> None:
    boundary = _build_boundary(target_status=RouteReconciliationStatus.RESOLVED_SENT)
    field_names = _field_names(
        boundary, boundary.unresolved_reconciliation, boundary.resolved_reconciliation_state
    )
    banned = {
        "outcome_id",
        "outcome",
        "outcome_object",
        "outcome_status",
        "safe_response_reference",
        "response_status",
        "response_body",
        "response_payload",
    }
    assert banned.isdisjoint(field_names)


def test_no_outcome_classification_is_selected() -> None:
    boundary = _build_boundary(target_status=RouteReconciliationStatus.RESOLVED_TERMINAL)
    field_names = _field_names(
        boundary, boundary.unresolved_reconciliation, boundary.resolved_reconciliation_state
    )
    assert "resolved_reconciliation_state" in field_names
    assert "resolution_committed" in field_names
    assert "transport_outcome" not in field_names
    assert "outcome_status" not in field_names
    assert {"parser_status", "scan_status", "notification_status"}.isdisjoint(field_names)


def test_no_parser_scan_notification_ownership_is_selected() -> None:
    boundary = _build_boundary(target_status=RouteReconciliationStatus.RESOLVED_NOT_SENT)
    field_names = _field_names(
        boundary, boundary.unresolved_reconciliation, boundary.resolved_reconciliation_state
    )
    banned = {"parser", "scan", "notification"}
    assert banned.isdisjoint({name.lower() for name in field_names})


def test_no_source_worker_timeout_storage_retry_values_are_selected() -> None:
    boundary = _build_boundary(target_status=RouteReconciliationStatus.RESOLVED_SENT)
    field_names = _field_names(
        boundary, boundary.unresolved_reconciliation, boundary.resolved_reconciliation_state
    )
    banned = {
        "worker",
        "worker_id",
        "timeout",
        "timeout_seconds",
        "deadline",
        "storage",
        "storage_reference",
        "lookup",
        "lookup_reference",
        "retry",
        "retry_count",
        "retry_delay",
        "backoff",
    }
    assert banned.isdisjoint({name.lower() for name in field_names})


def test_no_provider_proxy_vpn_tunnel_browser_windows_topology_is_selected() -> None:
    boundary = _build_boundary(target_status=RouteReconciliationStatus.RESOLVED_SENT)
    field_names = _field_names(
        boundary, boundary.unresolved_reconciliation, boundary.resolved_reconciliation_state
    )
    banned = {
        "provider",
        "proxy",
        "vpn",
        "tunnel",
        "browser",
        "windows",
        "host",
        "hostname",
        "ip",
        "port",
    }
    assert banned.isdisjoint({name.lower() for name in field_names})
