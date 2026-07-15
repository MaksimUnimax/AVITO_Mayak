from __future__ import annotations

import importlib
from dataclasses import fields
from typing import Any, cast

import pytest

from mayak.contracts.idempotency import IdempotencyDecision
from mayak.modules.egress_routing import (
    DispatchStatus,
    RouteLease,
    TransportDispatchReplayAuthority,
    TransportDispatchReplayBoundary,
)
from mayak.platform.idempotency import (
    IdempotencyFingerprint,
    IdempotencyKey,
    IdempotencyScope,
)

replay_contracts = cast(
    Any, importlib.import_module("tests.contract.test_egress_routing_replay_contracts")
)


def _snapshot(record: object) -> tuple[object, ...]:
    return tuple(getattr(record, field.name) for field in fields(cast(Any, record)))


def _build_boundary(
    *,
    dispatch_status: DispatchStatus = DispatchStatus.PENDING,
    **kwargs: object,
) -> TransportDispatchReplayBoundary:
    return replay_contracts._build_replay_boundary(dispatch_status=dispatch_status, **kwargs)


def test_only_egress_server_commits_replay_decision() -> None:
    boundary = _build_boundary()
    assert boundary.authority is TransportDispatchReplayAuthority.EGRESS_ROUTING_SERVER


def test_replay_references_exact_existing_attempt_and_creates_no_second_attempt() -> None:
    boundary = _build_boundary()
    field_names = {field.name for field in fields(TransportDispatchReplayBoundary)}
    assert boundary.original_attempt_reference == boundary.dispatch_attempt.attempt.attempt_id
    assert boundary.dispatch_attempt.attempt.attempt_ordinal == 1
    assert boundary.dispatch_attempt.attempt.outcome_reference is None
    assert "new_attempt" not in field_names
    assert "retry_attempt" not in field_names
    assert "next_attempt" not in field_names
    assert "attempt_ordinal" not in field_names


def test_replay_authorizes_no_second_effect_and_preserves_existing_state() -> None:
    boundary = _build_boundary()
    assert boundary.decision is IdempotencyDecision.PENDING
    assert boundary.replay_dispatch_effect_authorized is False
    assert boundary.original_scope == boundary.replay_scope
    assert boundary.original_key == boundary.replay_key
    assert boundary.original_fingerprint == boundary.replay_fingerprint


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("replay_scope", IdempotencyScope(value="scope-02")),
        ("replay_key", IdempotencyKey(value="key-02")),
        ("replay_fingerprint", IdempotencyFingerprint(value="fingerprint-02")),
    ],
)
def test_scope_key_fingerprint_mismatch_blocks_effect(field_name: str, value: object) -> None:
    boundary = _build_boundary(
        decision=IdempotencyDecision.MISMATCH,
        **{field_name: value},  # type: ignore[arg-type]
    )
    assert boundary.decision is IdempotencyDecision.MISMATCH
    assert boundary.replay_dispatch_effect_authorized is False
    assert boundary.reconciliation_required is False


@pytest.mark.parametrize(
    ("dispatch_status", "expected_decision"),
    [
        (DispatchStatus.PENDING, IdempotencyDecision.PENDING),
        (DispatchStatus.ATTEMPTED, IdempotencyDecision.PENDING),
        (DispatchStatus.ACKNOWLEDGED, IdempotencyDecision.PENDING),
    ],
)
def test_pending_replay_returns_original_pending_state(
    dispatch_status: DispatchStatus,
    expected_decision: IdempotencyDecision,
) -> None:
    boundary = _build_boundary(dispatch_status=dispatch_status)
    assert boundary.decision is expected_decision
    assert boundary.replay_dispatch_effect_authorized is False
    assert boundary.reconciliation_required is False


def test_unknown_replay_is_reconcile_first() -> None:
    boundary = _build_boundary(dispatch_status=DispatchStatus.UNKNOWN)
    assert boundary.decision is IdempotencyDecision.RECONCILE_REQUIRED
    assert boundary.replay_dispatch_effect_authorized is False
    assert boundary.reconciliation_required is True


def test_unknown_mismatch_still_preserves_reconciliation_requirement() -> None:
    boundary = _build_boundary(
        dispatch_status=DispatchStatus.UNKNOWN,
        decision=IdempotencyDecision.MISMATCH,
        replay_scope=IdempotencyScope(value="scope-02"),
    )
    assert boundary.decision is IdempotencyDecision.MISMATCH
    assert boundary.replay_dispatch_effect_authorized is False
    assert boundary.reconciliation_required is True


@pytest.mark.parametrize(
    "dispatch_status",
    [DispatchStatus.REJECTED, DispatchStatus.NOT_SENT, DispatchStatus.SENT],
)
def test_terminal_replay_returns_terminal_command_state(dispatch_status: DispatchStatus) -> None:
    boundary = _build_boundary(dispatch_status=dispatch_status)
    assert boundary.decision is IdempotencyDecision.REPLAY_TERMINAL
    assert boundary.replay_dispatch_effect_authorized is False
    assert boundary.reconciliation_required is False


def test_rejected_not_sent_and_sent_do_not_authorize_retry_or_response_inference() -> None:
    sent_boundary = _build_boundary(dispatch_status=DispatchStatus.SENT)
    field_names = {field.name for field in fields(TransportDispatchReplayBoundary)}
    assert "response_status" not in field_names
    assert "response_body" not in field_names
    assert "safe_response_reference" not in field_names
    assert "transport_outcome" not in field_names
    assert "parser_success" not in field_names
    assert "scan_success" not in field_names
    assert sent_boundary.decision is IdempotencyDecision.REPLAY_TERMINAL
    assert sent_boundary.replay_dispatch_effect_authorized is False
    assert sent_boundary.reconciliation_required is False


def test_new_decision_forbidden_for_existing_attempt() -> None:
    with pytest.raises(ValueError, match="decision NEW is forbidden"):
        _build_boundary(decision=IdempotencyDecision.NEW)


def test_dispatch_idempotency_is_not_lease_idempotency() -> None:
    replay_field_names = {field.name for field in fields(TransportDispatchReplayBoundary)}
    lease_field_names = {field.name for field in fields(RouteLease)}
    assert "idempotency_key" not in replay_field_names
    assert "semantic_fingerprint" not in replay_field_names
    assert {"idempotency_key", "semantic_fingerprint"}.issubset(lease_field_names)


def test_no_storage_ttl_retry_or_runtime_values_are_chosen() -> None:
    boundary = _build_boundary()
    field_names = {field.name for field in fields(TransportDispatchReplayBoundary)}
    banned_tokens = {
        "outcome_id",
        "transport_outcome",
        "response_status",
        "response_body",
        "receipt_payload",
        "send_payload",
        "storage_reference",
        "database_reference",
        "ttl",
        "expires_at",
        "retry_count",
        "retry_delay",
        "backoff",
        "duration",
        "timeout_seconds",
        "provider",
        "proxy",
        "vpn",
        "tunnel",
        "browser",
        "windows",
        "parser",
        "scan",
        "notification",
        "beacon",
        "admin",
    }
    assert banned_tokens.isdisjoint(field_names)
    assert boundary.replay_dispatch_effect_authorized is False


def test_no_mutation_of_nested_dispatch_assignment_or_lease_records() -> None:
    boundary = _build_boundary()
    dispatch_attempt = boundary.dispatch_attempt
    assignment_commitment = dispatch_attempt.assignment_commitment
    lease_authorization = assignment_commitment.lease_authorization
    lease = lease_authorization.lease
    assignment = assignment_commitment.assignment

    snapshots_before = (
        _snapshot(dispatch_attempt),
        _snapshot(assignment_commitment),
        _snapshot(lease_authorization),
        _snapshot(lease),
        _snapshot(assignment),
    )

    assert boundary.decision is IdempotencyDecision.PENDING
    assert boundary.replay_dispatch_effect_authorized is False

    snapshots_after = (
        _snapshot(dispatch_attempt),
        _snapshot(assignment_commitment),
        _snapshot(lease_authorization),
        _snapshot(lease),
        _snapshot(assignment),
    )
    assert snapshots_after == snapshots_before
