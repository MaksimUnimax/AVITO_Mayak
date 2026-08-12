#!/usr/bin/env python3
"""Fail-closed bootstrap or exact explicit-base coverage comparator."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

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
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise CoverageContractError("invalid exact coverage percentage")
    try:
        result = Decimal(str(value))
    except InvalidOperation as exc:
        raise CoverageContractError("invalid exact coverage percentage") from exc
    if not result.is_finite() or not 0 <= result <= 100:
        raise CoverageContractError("impossible exact coverage percentage")
    return result


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CoverageContractError("JSON evidence is unreadable") from exc
    if not isinstance(value, dict):
        raise CoverageContractError("JSON evidence must be an object")
    return value


def _metrics(totals: dict[str, Any]) -> dict[str, Any]:
    if any(key not in totals for key in REQUIRED):
        raise CoverageContractError("coverage totals are incomplete")
    result: dict[str, Any] = {key: _number(totals[key], key) for key in REQUIRED[:-1]}
    result["percent_covered"] = _percent(totals["percent_covered"])
    if result["covered_lines"] + result["missing_lines"] != result["num_statements"]:
        raise CoverageContractError("statement accounting mismatch")
    if result["covered_branches"] + result["missing_branches"] != result["num_branches"]:
        raise CoverageContractError("branch accounting mismatch")
    if (
        result["covered_lines"] > result["num_statements"]
        or result["covered_branches"] > result["num_branches"]
    ):
        raise CoverageContractError("impossible coverage totals")
    result["opportunities"] = result["num_statements"] + result["num_branches"]
    result["covered_opportunities"] = result["covered_lines"] + result["covered_branches"]
    return result


def validate_baseline(
    document: dict[str, Any], *, comparison_base: str | None = None
) -> dict[str, Any]:
    if document.get("schema_version") != 1 or document.get("reference_sha") != BASELINE_SHA:
        raise CoverageContractError("bootstrap artifact identity/schema mismatch")
    measurement = document.get("measurement")
    if document.get("toolchain") != {"python": "3.14.6", "uv": "0.11.31", "coverage_py": "7.15.0"}:
        raise CoverageContractError("bootstrap toolchain mismatch")
    if (
        not isinstance(measurement, dict)
        or measurement.get("branch") is not True
        or any(measurement.get(k) is not None for k in ("source", "include", "omit"))
    ):
        raise CoverageContractError("bootstrap narrows coverage measurement")
    if comparison_base is not None and comparison_base != BASELINE_SHA:
        raise CoverageContractError("bootstrap artifact is not valid for dynamic comparison")
    if _percent(measurement.get("exact_percent")) != Decimal("78.26377069472382"):
        raise CoverageContractError("bootstrap exact floor was edited")
    if measurement.get("pytest_authority") != "full-repository-unfiltered":
        raise CoverageContractError("pytest authority is not broad")
    for key in (
        "reference_statements",
        "reference_branches",
        "reference_measured_files",
        "reference_covered_opportunities",
    ):
        _number(measurement.get(key), key)
    identities = measurement.get("governed_skipped_nodeids")
    if (
        not isinstance(identities, list)
        or len(identities) != 35
        or any(not isinstance(x, str) for x in identities)
    ):
        raise CoverageContractError("bootstrap skip identities are incomplete")
    expected_digest = hashlib.sha256(("\n".join(sorted(identities)) + "\n").encode()).hexdigest()
    if measurement.get("governed_skipped_nodeids_sha256") != expected_digest:
        raise CoverageContractError("bootstrap skip identity digest mismatch")
    return document


def _coverage(document: dict[str, Any]) -> tuple[dict[str, Any], int]:
    meta = document.get("meta")
    if (
        not isinstance(meta, dict)
        or meta.get("branch_coverage") is not True
        or meta.get("version") != "7.15.0"
    ):
        raise CoverageContractError("coverage toolchain/branch metadata mismatch")
    totals = _metrics(document.get("totals", {}))
    files = document.get("files")
    if not isinstance(files, dict):
        raise CoverageContractError("coverage file accounting missing")
    return totals, len(files)


def _skip_evidence(path: Path) -> dict[str, Any]:
    try:
        root = ET.parse(path).getroot()
    except (OSError, ET.ParseError) as exc:
        raise CoverageContractError("pytest JUnit evidence is unreadable") from exc
    skipped: Counter[str] = Counter()
    failed = errors = xfail = xpass = passed = 0
    collected = 0
    for case in root.iter("testcase"):
        collected += 1
        nodeid = str(case.attrib.get("classname", "")) + "::" + str(case.attrib.get("name", ""))
        if case.find("failure") is not None:
            failed += 1
        elif case.find("error") is not None:
            errors += 1
        elif case.find("skipped") is not None:
            skipped[nodeid] += 1
        else:
            passed += 1
    return {
        "collected": collected,
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "skipped": skipped,
        "xfail": xfail,
        "xpass": xpass,
    }


def validate_pytest_evidence(
    candidate: Path, base: dict[str, Any], *, base_collected: int
) -> dict[str, Any]:
    observed = _skip_evidence(candidate)
    base_skips = set(base.get("governed_skipped_nodeids", []))
    if not base_skips:
        raise CoverageContractError("governed skip identities are missing")
    candidate_skips = set(observed["skipped"])
    if not candidate_skips <= base_skips:
        raise CoverageContractError("candidate introduced a skipped test identity")
    if observed["failed"] or observed["errors"] or observed["xfail"] or observed["xpass"]:
        raise CoverageContractError("pytest failure, error, or unauthorized xfail/xpass")
    if observed["collected"] < base_collected:
        raise CoverageContractError("candidate test collection regressed")
    observed["skipped_count"] = len(candidate_skips)
    observed["skipped_digest"] = (
        __import__("hashlib").sha256("\n".join(sorted(candidate_skips)).encode()).hexdigest()
    )
    return observed


def compare(
    candidate_json: Path,
    baseline_json: Path,
    *,
    comparison_base: str | None = None,
    base_junit: Path | None = None,
    candidate_junit: Path | None = None,
) -> dict[str, Any]:
    candidate = _load_json(candidate_json)
    candidate_totals, candidate_files = _coverage(candidate)
    if comparison_base == BASELINE_SHA:
        base_doc = validate_baseline(_load_json(baseline_json), comparison_base=comparison_base)
        floor = _percent(base_doc["measurement"]["exact_percent"])
        base_collected = sum(base_doc["measurement"]["reference_test_counts"].values())
        base_skips = base_doc["measurement"].get("governed_skipped_nodeids", [])
        base_opportunities = base_doc["measurement"].get("reference_covered_opportunities")
        base_files = base_doc["measurement"].get("reference_measured_files", 0)
        mode = "BOOTSTRAP"
    else:
        if not comparison_base or not SHA.fullmatch(comparison_base):
            raise CoverageContractError("dynamic comparison base SHA is required")
        if baseline_json == Path(__file__).with_name("coverage_baseline.json"):
            raise CoverageContractError("bootstrap artifact cannot be used for dynamic comparison")
        base_doc = _load_json(baseline_json)
        if base_doc.get("reference_sha") != comparison_base:
            raise CoverageContractError("dynamic base SHA receipt mismatch")
        base_totals, base_files = _coverage(base_doc)
        floor = base_totals["percent_covered"]
        base_collected = int(base_doc.get("pytest", {}).get("collected", 0))
        base_skips = base_doc.get("pytest", {}).get("skipped_nodeids", [])
        base_opportunities = base_totals["covered_opportunities"]
        mode = "DYNAMIC"
        if base_junit is None:
            raise CoverageContractError("dynamic base pytest evidence is required")
        base_run = _skip_evidence(base_junit)
        base_collected = base_run["collected"]
        base_skips = sorted(base_run["skipped"])
    if not base_skips:
        raise CoverageContractError("governed skip identities are missing")
    if candidate_totals["percent_covered"] < floor:
        raise CoverageContractError("candidate coverage regressed")
    if mode == "BOOTSTRAP":
        if candidate_totals["covered_opportunities"] < int(base_opportunities):
            raise CoverageContractError("covered opportunities regressed")
        if candidate_files < int(base_files):
            raise CoverageContractError("measured-file disappearance")
    result: dict[str, Any] = {
        "status": "PASS",
        "mode": mode,
        "comparison_base": comparison_base,
        "base_exact_percent": str(floor),
        "candidate_exact_percent": str(candidate_totals["percent_covered"]),
        "base_measured_files": base_files,
        "candidate_measured_files": candidate_files,
    }
    if candidate_junit:
        result["pytest"] = validate_pytest_evidence(
            candidate_junit, {"governed_skipped_nodeids": base_skips}, base_collected=base_collected
        )
    return result


def validate_pytest_log(path: Path, baseline: dict[str, Any]) -> dict[str, int]:
    """Compatibility parser; it is intentionally not used as CI skip authority."""
    text = path.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"(\d+) passed, (\d+) skipped", text)
    if not match:
        raise CoverageContractError("pytest execution accounting is missing")
    passed, skipped = map(int, match.groups())
    return {
        "collected": passed + skipped,
        "passed": passed,
        "failed": 0,
        "errors": 0,
        "skipped": skipped,
        "xfailed": 0,
        "xpassed": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("candidate_json", type=Path)
    parser.add_argument(
        "--baseline", type=Path, default=Path(__file__).with_name("coverage_baseline.json")
    )
    parser.add_argument("--comparison-base", required=True)
    parser.add_argument("--base-junit", type=Path)
    parser.add_argument("--candidate-junit", type=Path)
    parser.add_argument("--pytest-log", type=Path)
    args = parser.parse_args()
    try:
        result = compare(
            args.candidate_json,
            args.baseline,
            comparison_base=args.comparison_base,
            base_junit=args.base_junit,
            candidate_junit=args.candidate_junit,
        )
        print(json.dumps(result, sort_keys=True, default=str))
    except CoverageContractError as exc:
        print(f"COVERAGE_NO_REGRESSION: FAIL: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
