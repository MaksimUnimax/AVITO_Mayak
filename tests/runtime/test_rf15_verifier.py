from __future__ import annotations

import importlib.util
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "rf15_verifier", Path(__file__).parents[2] / "scripts/runtime/verify_rf15_acceptance.py"
)
assert SPEC and SPEC.loader
V = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(V)


def _op(
    pid: int, result: object = None, *, exception: object | None = None, offset: int = 0
) -> dict:
    base = datetime(2026, 8, 2, tzinfo=UTC) + timedelta(seconds=offset)
    value = {
        "callable": "mayak.synthetic.target",
        "input": {"scenario": "rf15-test"},
        "started_at": base.isoformat(),
        "finished_at": (base + timedelta(seconds=2)).isoformat(),
        "backend_pid": pid,
    }
    value["exception" if exception is not None else "result"] = (
        exception if exception is not None else result
    )
    return value


def _case() -> dict:
    op = _op(10, {})
    c = {
        name: {
            "operation": deepcopy(op),
            "physical_before": {"ids": []},
            "physical_after": {"ids": []},
        }
        for name in V.REQUIREMENT_IDS
    }
    c["cadence_policy"].update(
        {
            "operation": _op(10, {"basic": [300, 300], "free": [10800, 10800]}),
            "attempts": [
                {"operation": _op(11, exception={"class": "CadenceRejected"}, offset=i)}
                for i in range(6)
            ],
        }
    )
    c["schedule_uniqueness"]["physical_after"] = {"schedule_ids": ["s1"], "beacon_ids": ["b1"]}
    c["due_work_current_slot"]["physical_after"] = {
        "due_at": "2026-08-01T00:00:00+00:00",
        "now": "2026-08-02T00:00:00+00:00",
        "next_due_at": "2026-08-02T01:00:00+00:00",
    }
    c["due_work_coalescing"].update(
        {
            "physical_before": {"work_ids": []},
            "physical_after": {"work_ids": ["w1"], "missed_intervals": 3},
        }
    )
    c["recovery_blocks_backlog"].update(
        {
            "physical_before": {"work_ids": ["w1"]},
            "physical_after": {"work_ids": ["w1"], "state": "PENDING_RECONCILIATION"},
        }
    )
    for name in (
        "due_materialization_concurrency",
        "concurrent_baseline_serialization",
        "concurrent_new_listing_serialization",
    ):
        c[name].update(
            {
                "operation_a": _op(20, {}, offset=0),
                "operation_b": _op(21, {}, offset=1),
                "physical_before": {"work_ids": [], "effect_ids": []},
                "physical_after": {"work_ids": ["w1"], "effect_ids": ["e1"]},
            }
        )
    c["claim_exclusivity"].update(
        {
            "operation_a": _op(22, {"claim": True}),
            "operation_b": _op(23, {"claim": False}, offset=1),
            "results": [True, False],
            "physical_before": {"work_id": "w1"},
            "physical_after": {"work_id": "w1", "state": "CLAIMED"},
        }
    )
    c["expired_claim_reconciliation"]["physical_after"] = {
        "state": "PENDING_RECONCILIATION",
        "claimable": False,
    }
    c["lease_guard"].update(
        {"attempts": [{"exception": {"class": "LeaseConflict"}} for _ in range(3)]}
    )
    c["run_revision_pin"].update(
        {
            "operation": _op(30, {"run_id": "r1", "revision_no": 2}),
            "physical_before": {"revision_no": 2},
            "physical_after": {"revision_no": 2},
        }
    )
    c["run_replay"].update(
        {"returned_run_ids": ["r1", "r1"], "physical_after": {"run_ids": ["r1"]}}
    )
    c["baseline_no_event"].update(
        {
            "physical_before": {"baseline_id": None, "event_ids": []},
            "physical_after": {"baseline_id": "a1", "event_ids": []},
        }
    )
    c["empty_baseline_durable"].update(
        {
            "physical_before": {"event_ids": []},
            "physical_after": {"anchor_id": "a1", "listing_ids": [], "event_ids": []},
        }
    )
    c["parser_failure_no_advance"].update(
        {
            "statuses": sorted(V.PARSER_FAILURES),
            "physical_before": {"state": "b", "listing_ids": [], "event_ids": []},
            "physical_after": {"state": "b", "listing_ids": [], "event_ids": []},
        }
    )
    c["new_listing_exactly_once"].update(
        {
            "operation": _op(40, {"event_ids": ["e1"]}),
            "physical_after": {"listing_ids": ["l1"], "event_ids": ["e1"]},
        }
    )
    c["price_change_no_event"].update(
        {
            "physical_before": {"snapshot": {"price": 1}, "event_ids": []},
            "physical_after": {"snapshot": {"price": 2}, "event_ids": []},
        }
    )
    c["duplicate_within_run_exactly_once"].update(
        {
            "input": {"candidate_keys": ["l1", "l1"]},
            "physical_after": {"listing_key": "l1", "listing_ids": ["l1"]},
        }
    )
    c["beacon_isolation"]["physical_after"] = {
        "beacon_a": ["l1"],
        "beacon_b": ["l2"],
        "beacon_b_foreign_rows": [],
    }
    c["absence_no_removal"].update(
        {
            "physical_before": {"listing_ids": ["l1"], "event_ids": []},
            "physical_after": {"listing_ids": ["l1"], "event_ids": []},
        }
    )
    c["authority_recheck"].update(
        {"attempts": [{"exception": {"class": "DependencyBlocked"}} for _ in range(4)]}
    )
    c["idempotency_replay_and_mismatch"].update(
        {
            "returned_results": ["r1", "r1"],
            "physical_before": {"effect_ids": [], "terminal_ids": []},
            "physical_after": {"effect_ids": [], "terminal_ids": ["t1"]},
        }
    )
    c["concurrent_idempotency"].update(
        {
            "operation_a": _op(50, {}),
            "operation_b": _op(51, {}, offset=1),
            "physical_before": {"effect_ids": [], "terminal_ids": []},
            "physical_after": {"effect_ids": ["e1"], "terminal_ids": ["t1"]},
        }
    )
    c["restart_durability"].update(
        {
            "physical_before": {"identity": "r1"},
            "physical_after": {"identity": "r1", "state": "SUCCEEDED_DIFFERENCE"},
        }
    )
    c["foreign_state_witness"].update(
        {
            "physical_before": {"capture_id": "a", "digest": "d", "semantic": {"x": 1}},
            "physical_after": {"capture_id": "b", "digest": "d", "semantic": {"x": 1}},
        }
    )
    c["raw_payload_snapshot_boundary"].update(
        {
            "input": {"descriptors": ["raw", "headers", "cookies", "token", "phone"]},
            "attempts": [
                {"operation": _op(61 + i, exception={"class": "ValueError"}, offset=i)}
                for i in range(15)
            ],
            "physical_after": {"listing_ids": []},
        }
    )
    c["platform_event_identity"].update(
        {
            "operation": _op(60, {"event_ids": ["e1"]}),
            "physical_after": {"event_ids": ["e1"], "notification_ids": [], "egress_ids": []},
        }
    )
    c["no_foreign_domain_effect"].update(
        {
            "physical_before": {"digest": "d"},
            "physical_after": {"digest": "d", "notification_ids": [], "egress_ids": []},
        }
    )
    return c


def evidence() -> dict:
    return {
        "identity": {"technical_id": V.TECHNICAL_ID},
        "migration": {"head": "current", "independent_connection": True},
        "behavioral_cases": _case(),
    }


def test_all_raw_checkers_and_causal_tampers() -> None:
    data = evidence()
    assert set(V.REQUIREMENT_IDS) == set(V.BEHAVIORAL_CHECKERS) == set(V.BEHAVIORAL_TAMPERS)
    for name, checker in V.BEHAVIORAL_CHECKERS.items():
        assert checker(data), name
        mutated, paths = V.BEHAVIORAL_TAMPERS[name](data)
        assert paths
        try:
            assert not checker(mutated), name
        except (KeyError, TypeError, ValueError, IndexError):
            pass


def test_missing_malformed_and_impossible_evidence_fail_closed(tmp_path: Path) -> None:
    data = evidence()
    data["behavioral_cases"].pop("run_replay")
    with pytest.raises(ValueError):
        V.verify(data, tmp_path)
    data = evidence()
    data["behavioral_cases"]["due_work_current_slot"]["physical_after"]["now"] = "bad"
    with pytest.raises(ValueError):
        V.verify(data, tmp_path)


def test_verifier_does_not_accept_fake_conclusions_or_schema_witness() -> None:
    data = evidence()
    data["behavioral_cases"]["baseline_no_event"]["baseline_recorded"] = True
    data["behavioral_cases"]["baseline_no_event"]["physical_after"] = {"event_ids": []}
    assert not V.check_baseline_no_event(data)
    data = evidence()
    data["behavioral_cases"]["foreign_state_witness"]["physical_before"] = {"columns": ["id"]}
    assert not V.check_foreign_state_witness(data)


def test_producer_static_false_green_guard() -> None:
    source = (
        Path(__file__).parents[2] / "scripts/runtime/run_rf15_postgres_acceptance.py"
    ).read_text()
    forbidden = (
        "invalid_rejected",
        "successful_claims",
        "event_delta",
        "semantic_effects",
        "no-run-fixture",
        "recorded-id",
        "information_schema",
        "read_session",
        "max(",
        "min(",
    )
    assert not [token for token in forbidden if token in source]
