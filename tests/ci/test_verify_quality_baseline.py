from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).parents[2] / "scripts/ci/verify_quality_baseline.py"
SPEC = importlib.util.spec_from_file_location("quality_verifier", MODULE_PATH)
assert SPEC and SPEC.loader
verifier = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verifier)


def output(errors: list[str], notes: int = 29, summary: int | None = None) -> str:
    rows = [f"src/example.py:{i}: error: diagnostic {i} [TEST]" for i in errors]
    rows.extend(f"src/example.py:{i}: note: note {i}" for i in range(notes))
    total = len(errors) if summary is None else summary
    return "\n".join(rows + [f"Found {total} errors in 1 file"]) + "\n"


def canonical_output() -> str:
    return output([str(i) for i in range(249)])


def test_observes_counts_from_supplied_stdout() -> None:
    observed = verifier.observe_mypy_output(output(["1", "2"], notes=3), 1)
    assert observed["error_count"] == 2
    assert observed["note_count"] == 3
    assert observed["summary_count"] == 2
    assert observed["exit_code"] == 1
    assert verifier.parse_collection_count("collected 4636 items\r\n") == 4636
    assert verifier.parse_collection_count("4637 tests collected\n") == 4637
    with pytest.raises(RuntimeError, match="missing"):
        verifier.parse_collection_count("pytest output without a summary\n")
    with pytest.raises(RuntimeError, match="ambiguous"):
        verifier.parse_collection_count("collected 4636 items\ncollected 4637 items\n")


def test_observed_digest_uses_sorted_normalized_error_rows() -> None:
    observed = verifier.observe_mypy_output(output(["2", "1"], notes=0), 1)
    normalized = (
        "src/example.py:1: error: diagnostic 1 [TEST]\n"
        "src/example.py:2: error: diagnostic 2 [TEST]\n"
    )
    assert observed["normalized_error_text"] == normalized
    assert observed["observed_normalized_error_sha256"] == verifier.digest(normalized)
    execution = verifier.parse_execution_summary("collected 4637 items\n4637 passed in 1.00s\n")
    verifier.validate_suite_observations(4637, 4637, execution, 86)


def test_diagnostic_input_order_does_not_change_observed_digest() -> None:
    first = verifier.observe_mypy_output(output(["1", "2", "3"]), 1)
    second = verifier.observe_mypy_output(output(["3", "1", "2"]), 1)
    assert first["observed_normalized_error_sha256"] == second["observed_normalized_error_sha256"]
    execution = {
        "executed_collected_count": 4636,
        "passed_count": 4636,
        "failed_count": 0,
        "error_count": 0,
        "skipped_count": 0,
        "xfailed_count": 0,
        "xpassed_count": 0,
    }
    with pytest.raises(RuntimeError, match="below"):
        verifier.validate_suite_observations(
            4635,
            4635,
            {**execution, "executed_collected_count": 4635, "passed_count": 4635},
            85,
        )
    with pytest.raises(RuntimeError, match="collection"):
        verifier.validate_suite_observations(4636, 4637, execution, 85)


def test_changing_one_error_changes_observed_digest() -> None:
    first = verifier.observe_mypy_output(output(["1", "2", "3"]), 1)
    second = verifier.observe_mypy_output(output(["1", "2", "changed"]), 1)
    assert first["observed_normalized_error_sha256"] != second["observed_normalized_error_sha256"]
    with pytest.raises(RuntimeError, match="execution"):
        verifier.validate_suite_observations(
            4636,
            4636,
            {
                "executed_collected_count": 4635,
                "passed_count": 4636,
                "failed_count": 0,
                "error_count": 0,
                "skipped_count": 0,
                "xfailed_count": 0,
                "xpassed_count": 0,
            },
            85,
        )


def test_three_repeatable_accepted_observations_pass_validation() -> None:
    observations = [verifier.observe_mypy_output(canonical_output(), 1) for _ in range(3)]
    expected = observations[0]["observed_normalized_error_sha256"]
    assert isinstance(expected, str)
    setattr(verifier, "MYPY_SHA", expected)
    verifier.validate_mypy_observations(observations)
    assert observations[0]["observed_normalized_error_sha256"] == getattr(verifier, "MYPY_SHA")
    execution = {
        "executed_collected_count": 4636,
        "passed_count": 4636,
        "failed_count": 0,
        "error_count": 0,
        "skipped_count": 0,
        "xfailed_count": 0,
        "xpassed_count": 0,
    }
    verifier.validate_suite_observations(4636, 4636, execution, 85)
    verifier.validate_suite_observations(
        4637, 4637, {**execution, "executed_collected_count": 4637, "passed_count": 4637}, 86
    )
    assert verifier.parse_coverage_percent("TOTAL 10 2 85%\n") == 85
    assert verifier.parse_coverage_percent("TOTAL 10 2 86%\n") == 86


def test_matching_counts_with_wrong_observed_digest_fail_validation() -> None:
    observations = [verifier.observe_mypy_output(canonical_output(), 1) for _ in range(3)]
    for observation in observations:
        observation["observed_normalized_error_sha256"] = "0" * 64
    with pytest.raises(RuntimeError, match="derived|mismatch"):
        verifier.validate_mypy_observations(observations)
    for category in (
        "failed_count",
        "error_count",
        "skipped_count",
        "xfailed_count",
        "xpassed_count",
    ):
        execution = {
            "executed_collected_count": 4636,
            "passed_count": 4636,
            "failed_count": 0,
            "error_count": 0,
            "skipped_count": 0,
            "xfailed_count": 0,
            "xpassed_count": 0,
        }
        execution[category] = 1
        with pytest.raises(RuntimeError, match="outcome"):
            verifier.validate_suite_observations(4636, 4636, execution, 85)
    with pytest.raises(RuntimeError, match="below"):
        verifier.validate_suite_observations(4636, 4636, {
            "executed_collected_count": 4636, "passed_count": 4636,
            "failed_count": 0, "error_count": 0, "skipped_count": 0,
            "xfailed_count": 0, "xpassed_count": 0,
        }, 84)


def test_nonrepeatable_digests_or_zero_exit_fail_validation() -> None:
    observations = [verifier.observe_mypy_output(canonical_output(), 1) for _ in range(3)]
    expected = observations[0]["observed_normalized_error_sha256"]
    assert isinstance(expected, str)
    setattr(verifier, "MYPY_SHA", expected)
    observations[2]["observed_normalized_error_sha256"] = "0" * 64
    with pytest.raises(RuntimeError):
        verifier.validate_mypy_observations(observations)
    observations = [verifier.observe_mypy_output(canonical_output(), 1) for _ in range(3)]
    observations[1]["exit_code"] = 0
    with pytest.raises(RuntimeError):
        verifier.validate_mypy_observations(observations)


def test_mypy_gate_separates_expected_and_observed_digest(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    calls = 0

    def fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        nonlocal calls
        calls += 1
        return subprocess.CompletedProcess(["mypy"], 1, canonical_output(), "")

    monkeypatch.setattr(verifier, "run", fake_run)
    expected = verifier.observe_mypy_output(canonical_output(), 1)[
        "observed_normalized_error_sha256"
    ]
    assert isinstance(expected, str)
    monkeypatch.setattr(verifier, "MYPY_SHA", expected)
    verifier.mypy_gate(tmp_path, tmp_path)
    evidence = (tmp_path / "mypy-1.json").read_text(encoding="utf-8")
    assert calls == 3
    assert '"expected_normalized_error_sha256": "' + expected + '"' in evidence
    assert '"observed_normalized_error_sha256": "' + expected + '"' in evidence
    assert '"normalized_error_sha256"' not in evidence
    assert (
        verifier.MYPY_SHA
        not in verifier.observe_mypy_output(
            canonical_output().replace("diagnostic 248", "wrong"), 1
        )["normalized_error_text"]
    )
    assert not (tmp_path / ".coverage").exists()
    assert not (MODULE_PATH.parents[2] / ".coverage").exists()
    assert verifier.MINIMUM_ACCEPTED_TEST_COUNT == 4636
    assert verifier.MINIMUM_ACCEPTED_COVERAGE_PERCENT == 85
