from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[2]
SPEC = importlib.util.spec_from_file_location(
    "coverage_verifier", ROOT / "scripts/ci/verify_coverage_baseline.py"
)
assert SPEC and SPEC.loader
verifier = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verifier)


def baseline() -> dict:
    return json.loads((ROOT / "scripts/ci/coverage_baseline.json").read_text())


def candidate(percent: str = "78.90499971077647") -> dict:
    return {
        "meta": {"version": "7.15.0", "branch_coverage": True},
        "files": {str(i): {} for i in range(566)},
        "totals": {
            "covered_lines": 61000,
            "num_statements": 82870,
            "missing_lines": 21870,
            "covered_branches": 20845,
            "num_branches": 20856,
            "missing_branches": 11,
            "percent_covered": percent,
        },
    }


def run(tmp_path: Path, document: dict, report: dict | None = None) -> None:
    baseline_path = tmp_path / "baseline.json"
    candidate_path = tmp_path / "coverage.json"
    baseline_path.write_text(json.dumps(document))
    candidate_path.write_text(json.dumps(report or candidate()))
    verifier.compare(candidate_path, baseline_path, comparison_base=verifier.BASELINE_SHA)


def test_equality_and_higher_candidate_pass(tmp_path: Path) -> None:
    run(tmp_path, baseline(), candidate("78.26377069472382"))
    run(tmp_path, baseline(), candidate())


@pytest.mark.parametrize(
    "change",
    [
        {
            "measurement": {
                "branch": True,
                "source": None,
                "include": None,
                "omit": None,
                "pytest_authority": "full-repository-unfiltered",
                "exact_percent": "78.26377069472381",
                "reference_statements": 82672,
                "reference_branches": 20802,
                "reference_measured_files": 566,
                "reference_covered_opportunities": 81734,
            }
        },
        {"reference_sha": "0" * 40},
        {"toolchain": {"python": "3.13", "uv": "0.11.31", "coverage_py": "7.15.0"}},
        {
            "measurement": {
                "branch": False,
                "source": None,
                "include": None,
                "omit": None,
                "pytest_authority": "full-repository-unfiltered",
                "exact_percent": "78.26377069472382",
                "reference_statements": 82672,
                "reference_branches": 20802,
                "reference_measured_files": 566,
                "reference_covered_opportunities": 81734,
            }
        },
    ],
)
def test_baseline_edits_fail_closed(tmp_path: Path, change: dict) -> None:
    document = baseline()
    document.update(change)
    with pytest.raises(verifier.CoverageContractError):
        run(tmp_path, document)


@pytest.mark.parametrize("percent", ["78.26377069472381", "NaN", "Infinity"])
def test_exact_regression_and_nonfinite_values_fail(tmp_path: Path, percent: str) -> None:
    with pytest.raises(verifier.CoverageContractError):
        run(tmp_path, baseline(), candidate(percent))


def test_wrong_comparison_base_and_narrowing_fail(tmp_path: Path) -> None:
    with pytest.raises(verifier.CoverageContractError):
        verifier.compare(
            tmp_path / "missing.json",
            ROOT / "scripts/ci/coverage_baseline.json",
            comparison_base="1" * 40,
        )
    bad = candidate()
    bad["meta"]["branch_coverage"] = False
    with pytest.raises(verifier.CoverageContractError):
        run(tmp_path, baseline(), bad)


def test_governed_skips_and_collection_accounting(tmp_path: Path) -> None:
    log = tmp_path / "pytest.log"
    log.write_text("7000 passed, 35 skipped in 1.00s\n")
    result = verifier.validate_pytest_log(log, baseline())
    assert result["collected"] == 7035
    log.write_text("7000 passed, 36 skipped in 1.00s\n")
    assert verifier.validate_pytest_log(log, baseline())["skipped"] == 36
