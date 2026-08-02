from __future__ import annotations

import importlib.util
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "rf15_verifier", Path(__file__).parents[2] / "scripts/runtime/verify_rf15_acceptance.py"
)
assert SPEC is not None and SPEC.loader is not None
VERIFIER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFIER)


def _timeline() -> dict[str, str]:
    base = datetime(2026, 8, 2, tzinfo=UTC)
    return {
        "start_a": base.isoformat(),
        "start_b": (base + timedelta(seconds=1)).isoformat(),
        "end_a": (base + timedelta(seconds=4)).isoformat(),
        "end_b": (base + timedelta(seconds=5)).isoformat(),
    }


def _evidence() -> dict:
    c = {
        "cadence_policy": {
            "basic_minimum": 300,
            "basic_step": 300,
            "free_minimum": 10800,
            "free_step": 10800,
            "invalid_rejected": True,
            "caller_override_rejected": True,
        },
        "schedule_uniqueness": {
            "physical_rows": 1,
            "beacon_ids": ["a"],
            "distinct_beacon_ids": ["a"],
        },
        "due_work_current_slot": {
            "work_due_at": "2026-08-01T00:00:00+00:00",
            "now": "2026-08-02T00:00:00+00:00",
            "next_due_at": "2026-08-02T01:00:00+00:00",
        },
        "due_work_coalescing": {
            "missed_periods": 3,
            "created_rows": 1,
            "now": "2026-08-02T00:00:00+00:00",
            "next_due_at": "2026-08-02T01:00:00+00:00",
        },
        "recovery_blocks_backlog": {
            "unresolved_state": "PENDING_RECONCILIATION",
            "created_rows": 0,
        },
        "due_materialization_concurrency": {
            **_timeline(),
            "backend_pid_a": 10,
            "backend_pid_b": 11,
            "physical_work_rows": 1,
        },
        "claim_exclusivity": {
            **_timeline(),
            "backend_pid_a": 12,
            "backend_pid_b": 13,
            "successful_claims": 1,
            "physical_claimed_rows": 1,
        },
        "expired_claim_reconciliation": {
            "state_after": "PENDING_RECONCILIATION",
            "ordinary_claim_rows": 0,
        },
        "lease_guard": {
            "wrong_token_committed": False,
            "expired_token_committed": False,
            "lost_token_committed": False,
        },
        "run_revision_pin": {
            "revision_before": 1,
            "revision_pinned": 1,
            "substitution_committed": False,
        },
        "run_replay": {"physical_run_rows": 1, "first_run_id": "r1", "replayed_run_id": "r1"},
        "baseline_no_event": {"baseline_recorded": True, "event_delta": 0},
        "empty_baseline_durable": {
            "durable_baseline": True,
            "listing_rows": 0,
            "event_delta": 0,
            "fake_listing_rows": 0,
        },
        "parser_failure_no_advance": {
            "statuses": sorted(VERIFIER.PARSER_FAILURES),
            "baseline_before": "b",
            "baseline_after": "b",
            "anchor_before": "a",
            "anchor_after": "a",
            "listing_before": ["x"],
            "listing_after": ["x"],
            "event_delta": 0,
        },
        "new_listing_exactly_once": {
            "unseen_keys": ["l1"],
            "listing_key": "l1",
            "event_physical_rows": 1,
            "returned_event_ids": ["e1"],
            "persisted_event_ids": ["e1"],
        },
        "price_change_no_event": {
            "event_delta": 0,
            "price_event_delta": 0,
            "snapshot_updated": True,
        },
        "duplicate_within_run_exactly_once": {
            "candidate_keys": ["l1", "l1"],
            "physical_listing_rows": 1,
            "semantic_effects": 1,
        },
        "beacon_isolation": {
            "beacon_a_keys": ["a"],
            "beacon_b_keys": [],
            "cross_beacon_substitution_committed": False,
        },
        "absence_no_removal": {
            "prior_listing_present": True,
            "post_listing_present": True,
            "removal_inferred": False,
        },
        "authority_recheck": {
            "lifecycle_denied_committed": False,
            "entitlement_denied_committed": False,
            "revision_denied_committed": False,
            "parser_denied_committed": False,
        },
        "idempotency_replay_and_mismatch": {
            "same_fingerprint_effects": 1,
            "replay_returns_original": True,
            "mismatch_new_effects": 0,
            "retention_days": 14,
        },
        "concurrent_idempotency": {
            **_timeline(),
            "backend_pid_a": 20,
            "backend_pid_b": 21,
            "physical_terminal_rows": 1,
            "physical_effects": 1,
            "returned_ids": ["e1"],
            "persisted_ids": ["e1"],
        },
        "concurrent_baseline_serialization": {
            **_timeline(),
            "backend_pid_a": 22,
            "backend_pid_b": 23,
            "physical_effects": 1,
        },
        "concurrent_new_listing_serialization": {
            **_timeline(),
            "backend_pid_a": 24,
            "backend_pid_b": 25,
            "physical_effects": 1,
        },
        "restart_durability": {
            "before_identity": "b1",
            "after_identity": "b1",
            "after_state": "SUCCEEDED_DIFFERENCE",
        },
        "foreign_state_witness": {
            "before": {"identity": ["i"]},
            "after": {"identity": ["i"]},
            "before_digest": "same",
            "after_digest": "same",
            "capture_a": "FOREIGN_BASELINE_AFTER_FIXTURES_BEFORE_SCAN",
            "capture_b": "FOREIGN_AFTER_SCAN",
            "platform_effects": {"allowed_only": True},
        },
        "raw_payload_snapshot_boundary": {
            "persisted_raw_payload": False,
            "rejected_fields": ["raw", "headers"],
            "max_utf8_bytes": 32768,
            "recursive_rejection": True,
        },
        "platform_event_identity": {
            "returned_event_id": "e1",
            "persisted_event_id": "e1",
            "notification_delta": 0,
            "egress_delta": 0,
        },
        "no_foreign_domain_effect": {
            "foreign_before_digest": "same",
            "foreign_after_digest": "same",
            "notification_writes": 0,
            "egress_writes": 0,
        },
    }
    return {
        "identity": {"technical_id": VERIFIER.TECHNICAL_ID},
        "migration": {"table_count": 51, "global_index_count": 73, "scan_index_count": 8},
        "behavioral_cases": c,
    }


def test_registry_and_every_causal_tamper() -> None:
    evidence = _evidence()
    assert set(VERIFIER.BEHAVIORAL_CHECKERS) == set(VERIFIER.REQUIREMENT_IDS)
    for requirement, checker in VERIFIER.BEHAVIORAL_CHECKERS.items():
        assert checker(evidence), requirement
        tampered, paths = VERIFIER.BEHAVIORAL_TAMPERS[requirement](evidence)
        assert paths
        assert not checker(tampered), requirement
        assert tampered is not evidence


def test_missing_and_malformed_evidence_fail_closed(tmp_path: Path) -> None:
    evidence = _evidence()
    evidence["behavioral_cases"].pop("run_replay")
    with pytest.raises(ValueError):
        VERIFIER.verify(evidence, tmp_path)
    malformed = _evidence()
    malformed["behavioral_cases"]["due_work_current_slot"]["now"] = "not-a-time"
    with pytest.raises(ValueError):
        VERIFIER.verify(malformed, tmp_path)


def test_foreign_witness_is_two_captures() -> None:
    evidence = _evidence()
    assert VERIFIER.check_foreign_state_witness(evidence)
    evidence["behavioral_cases"]["foreign_state_witness"]["after"] = evidence["behavioral_cases"][
        "foreign_state_witness"
    ]["before"]
    assert not VERIFIER.check_foreign_state_witness(evidence)
