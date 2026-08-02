from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "rf15_verifier", Path(__file__).parents[2] / "scripts/runtime/verify_rf15_acceptance.py"
)
assert SPEC and SPEC.loader
V = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(V)


def test_registry_has_exactly_29_requirements_and_raw_dependencies() -> None:
    assert len(V.REQUIREMENT_IDS) == 29
    assert set(V.REQUIREMENT_IDS) == set(V.CHECKERS)
    assert set(V.REQUIREMENT_IDS) == set(V.RAW_DEPENDENCY_PATHS)
    assert all(
        any("physical_before" in path for path in paths)
        for paths in V.RAW_DEPENDENCY_PATHS.values()
    )


def test_verifier_does_not_depend_on_conclusion_fields() -> None:
    forbidden = {
        "due_at",
        "now",
        "next_due_at",
        "missed_intervals",
        "claimable",
        "baseline_id",
        "anchor_id",
        "returned_run_ids",
        "returned_results",
        "effect_ids",
        "terminal_ids",
        "snapshot",
        "listing_key",
        "beacon_a",
        "beacon_b",
    }
    assert not any(
        any(token in path.rsplit(".", 1)[-1] for token in forbidden)
        for paths in V.RAW_DEPENDENCY_PATHS.values()
        for path in paths
    )


def test_raw_operation_requires_result_or_exception() -> None:
    with pytest.raises(ValueError):
        V._op(
            {
                "callable": "x",
                "input": {},
                "started_at": "2026-08-02T00:00:00+00:00",
                "finished_at": "2026-08-02T00:00:01+00:00",
                "backend_pid": 1,
            }
        )


def test_cadence_contract_is_actual_policy() -> None:
    assert V._check(
        "cadence_policy",
        {
            "operation": {
                "callable": "validate_cadence",
                "input": {},
                "result": {"basic": [300, 600], "free": [10800, 21600]},
                "started_at": "2026-08-02T00:00:00+00:00",
                "finished_at": "2026-08-02T00:00:01+00:00",
                "backend_pid": 1,
            },
            "attempts": [
                {
                    "operation": {
                        "callable": "validate_cadence",
                        "input": {},
                        "exception": {},
                        "started_at": "2026-08-02T00:00:00+00:00",
                        "finished_at": "2026-08-02T00:00:01+00:00",
                        "backend_pid": i,
                    }
                }
                for i in range(6)
            ],
        },
    )
