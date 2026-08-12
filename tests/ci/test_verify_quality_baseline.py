from __future__ import annotations

import importlib.util
from collections import Counter
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).parents[2] / "scripts/ci/verify_quality_baseline.py"
SPEC = importlib.util.spec_from_file_location("quality_verifier", MODULE_PATH)
assert SPEC and SPEC.loader
verifier = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verifier)


def test_collection_and_governed_skip_accounting() -> None:
    execution = {
        "executed_collected_count": 7,
        "passed_count": 5,
        "failed_count": 0,
        "error_count": 0,
        "skipped_count": 2,
        "xfailed_count": 0,
        "xpassed_count": 0,
    }
    verifier.validate_suite_observations(7, 7, execution, 1)
    with pytest.raises(RuntimeError, match="account"):
        verifier.validate_suite_observations(7, 7, {**execution, "skipped_count": 3}, 1)
    with pytest.raises(RuntimeError, match="outcome"):
        verifier.validate_suite_observations(7, 7, {**execution, "failed_count": 1}, 1)
    with pytest.raises(RuntimeError, match="xfail"):
        verifier.validate_suite_observations(7, 7, {**execution, "xpassed_count": 1}, 1)


def test_explicit_collection_floor_is_successor_safe() -> None:
    execution = {
        "executed_collected_count": 8,
        "passed_count": 8,
        "failed_count": 0,
        "error_count": 0,
        "skipped_count": 0,
        "xfailed_count": 0,
        "xpassed_count": 0,
    }
    verifier.validate_suite_observations(8, 8, execution, 1, minimum_count=7)
    with pytest.raises(RuntimeError, match="comparison-base"):
        verifier.validate_suite_observations(
            6,
            6,
            {**execution, "executed_collected_count": 6, "passed_count": 6},
            1,
            minimum_count=7,
        )


def test_parsers_remain_fail_closed() -> None:
    assert verifier.parse_collection_count("collected 9 items\n") == 9
    assert (
        verifier.parse_execution_summary("collected 9 items\n7 passed, 2 skipped in 1.00s\n")[
            "skipped_count"
        ]
        == 2
    )
    with pytest.raises(RuntimeError):
        verifier.parse_collection_count("collected -1 items\n")
    with pytest.raises(RuntimeError):
        verifier.parse_coverage_percent("TOTAL 10 2 85%\nTOTAL 10 2 86%\n")


def test_diagnostic_delta_is_global_multiset_identity() -> None:
    base = Counter({("a.py", "E1"): 1, ("b.py", "E2"): 1})
    assert verifier.multiset_regressions(base, Counter({("a.py", "E1"): 1})) == Counter()
    assert verifier.multiset_regressions(
        base, Counter({("a.py", "E9"): 1, ("b.py", "E2"): 1})
    ) == Counter({("a.py", "E9"): 1})
    assert verifier.multiset_regressions(
        base, Counter({("a.py", "E1"): 2, ("b.py", "E2"): 1})
    ) == Counter({("a.py", "E1"): 1})
