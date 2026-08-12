#!/usr/bin/env python3
"""Fail-closed exact current-main coverage comparison."""

from __future__ import annotations

import argparse
import json
import re
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
BASELINE_SHA = "5359921e2aedcc567363a9f2e9d47461459fef3b"
SHA = re.compile(r"^[0-9a-f]{40}$")
REQUIRED = (
    "covered_lines",
    "num_statements",
    "missing_lines",
    "num_branches",
    "covered_branches",
    "missing_branches",
    "percent_covered",
)


class CoverageContractError(RuntimeError):
    pass


def _number(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise CoverageContractError(f"invalid {name}")
    return value


def _percent(value: Any) -> Decimal:
    if not isinstance(value, (str, int, float)) or isinstance(value, bool):
        raise CoverageContractError("invalid exact coverage percentage")
    raw = str(value)
    try:
        result = Decimal(raw)
    except InvalidOperation as exc:
        raise CoverageContractError("invalid exact coverage percentage") from exc
    if not result.is_finite() or result < 0 or result > 100:
        raise CoverageContractError("impossible exact coverage percentage")
    return result


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CoverageContractError("coverage JSON is unreadable") from exc
    if not isinstance(value, dict):
        raise CoverageContractError("coverage JSON must be an object")
    return value


def _validate_metrics(totals: dict[str, Any]) -> dict[str, Any]:
    if any(key not in totals for key in REQUIRED):
        raise CoverageContractError("coverage totals are incomplete")
    result: dict[str, Any] = {key: _number(totals[key], key) for key in REQUIRED[:-1]}
    result["percent_covered"] = _percent(totals["percent_covered"])
    if (
        result["covered_lines"] > result["num_statements"]
        or result["missing_lines"] > result["num_statements"]
    ):
        raise CoverageContractError("impossible statement totals")
    if (
        result["covered_branches"] > result["num_branches"]
        or result["missing_branches"] > result["num_branches"]
    ):
        raise CoverageContractError("impossible branch totals")
    if result["covered_lines"] + result["missing_lines"] != result["num_statements"]:
        raise CoverageContractError("statement accounting mismatch")
    if result["covered_branches"] + result["missing_branches"] != result["num_branches"]:
        raise CoverageContractError("branch accounting mismatch")
    result["opportunities"] = result["num_statements"] + result["num_branches"]
    result["covered_opportunities"] = result["covered_lines"] + result["covered_branches"]
    return result


def validate_baseline(
    document: dict[str, Any], *, comparison_base: str | None = None
) -> dict[str, Any]:
    if document.get("schema_version") != 1 or document.get("reference_sha") != BASELINE_SHA:
        raise CoverageContractError("baseline identity/schema mismatch")
    if not SHA.fullmatch(str(document["reference_sha"])):
        raise CoverageContractError("baseline reference SHA is malformed")
    toolchain = document.get("toolchain")
    measurement = document.get("measurement")
    if toolchain != {"python": "3.14.6", "uv": "0.11.31", "coverage_py": "7.15.0"}:
        raise CoverageContractError("baseline toolchain mismatch")
    if (
        not isinstance(measurement, dict)
        or measurement.get("branch") is not True
        or any(measurement.get(k) is not None for k in ("source", "include", "omit"))
    ):
        raise CoverageContractError("baseline narrows coverage measurement")
    if comparison_base is not None and comparison_base != BASELINE_SHA:
        raise CoverageContractError("baseline reference is not the accepted comparison base")
    if _percent(measurement.get("exact_percent")) != Decimal("78.26377069472382"):
        raise CoverageContractError("baseline exact floor was edited")
    for key in (
        "reference_statements",
        "reference_branches",
        "reference_measured_files",
        "reference_covered_opportunities",
    ):
        _number(measurement.get(key), key)
    if (
        measurement["reference_statements"] != 82672
        or measurement["reference_branches"] != 20802
        or measurement["reference_measured_files"] != 566
        or measurement["reference_covered_opportunities"] != 81734
    ):
        raise CoverageContractError("baseline bootstrap metrics were edited")
    if measurement.get("pytest_authority") != "full-repository-unfiltered":
        raise CoverageContractError("pytest authority is not broad")
    return document


def compare(
    candidate_json: Path, baseline_json: Path, *, comparison_base: str | None = None
) -> dict[str, Any]:
    baseline = validate_baseline(_load_json(baseline_json), comparison_base=comparison_base)
    candidate = _load_json(candidate_json)
    meta = candidate.get("meta")
    if (
        not isinstance(meta, dict)
        or meta.get("branch_coverage") is not True
        or meta.get("version") != "7.15.0"
    ):
        raise CoverageContractError("candidate toolchain/branch metadata mismatch")
    totals = _validate_metrics(candidate.get("totals", {}))
    floor = _percent(baseline["measurement"]["exact_percent"])
    if totals["percent_covered"] < floor:
        raise CoverageContractError("candidate coverage is below current-main baseline")
    baseline_opportunities = baseline["measurement"].get("reference_covered_opportunities")
    if baseline_opportunities is not None and totals["covered_opportunities"] < _number(
        baseline_opportunities, "reference_covered_opportunities"
    ):
        raise CoverageContractError("candidate covered opportunities regressed")
    expected_files = baseline["measurement"].get("reference_measured_files", 0)
    if expected_files and len(candidate.get("files", {})) < expected_files:
        raise CoverageContractError("measured-file disappearance")
    return {
        "status": "PASS",
        "verdict": "COVERAGE_CURRENT_MAIN_NO_REGRESSION",
        "baseline_exact_percent": str(floor),
        "candidate_exact_percent": str(totals["percent_covered"]),
        "baseline_covered_opportunities": baseline_opportunities,
        "candidate_covered_opportunities": totals["covered_opportunities"],
        "candidate_measured_files": len(candidate.get("files", {})),
    }


def validate_pytest_log(path: Path, baseline: dict[str, Any]) -> dict[str, int]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        raise CoverageContractError("pytest execution log is unreadable") from exc
    summary_pattern = (
        r"(?m)^\s*(?:(\d+) passed)?(?:,?\s*(\d+) failed)?"
        r"(?:,?\s*(\d+) error(?:s)?)?(?:,?\s*(\d+) skipped)?"
        r"(?:,?\s*(\d+) xfailed)?(?:,?\s*(\d+) xpassed)?.*in [^\n]+$"
    )
    match = re.search(summary_pattern, text)
    if not match:
        raise CoverageContractError("pytest execution accounting is missing")
    values = [int(value or 0) for value in match.groups()]
    passed, failed, errors, skipped, xfailed, xpassed = values
    expected = baseline["measurement"]["reference_test_counts"]
    if failed or errors or xfailed or xpassed or skipped != expected["skipped"]:
        raise CoverageContractError("pytest execution outcome or skip governance mismatch")
    collected = passed + skipped
    if collected < expected["passed"] + expected["skipped"]:
        raise CoverageContractError("candidate test collection regressed")
    return {
        "collected": collected,
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "skipped": skipped,
        "xfailed": xfailed,
        "xpassed": xpassed,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("candidate_json", type=Path)
    parser.add_argument(
        "--baseline", type=Path, default=Path(__file__).with_name("coverage_baseline.json")
    )
    parser.add_argument("--comparison-base")
    parser.add_argument("--pytest-log", type=Path)
    args = parser.parse_args()
    try:
        result = compare(args.candidate_json, args.baseline, comparison_base=args.comparison_base)
        if args.pytest_log:
            result["pytest"] = validate_pytest_log(
                args.pytest_log,
                validate_baseline(_load_json(args.baseline), comparison_base=args.comparison_base),
            )
        print(json.dumps(result, sort_keys=True))
    except CoverageContractError as exc:
        print(f"COVERAGE_CURRENT_MAIN_NO_REGRESSION: FAIL: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
