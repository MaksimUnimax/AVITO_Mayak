"""Create a bounded, fail-closed diagnostic from one RF26 H19 JUnit report."""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
TECHNICAL_ID = "RF26-OBSERVABILITY-BACKUP-RECOVERY-01"
MAX_FAILURES = 20
MAX_TEXT = 160
SENSITIVE = re.compile(
    r"(?ix)"
    r"(?:postgres(?:ql)?(?:\+[^:/\s]+)?://[^\s]+|https?://[^\s/@]+:[^\s/@]+@[^\s]+)"
    r"|(?:password|passwd|token|secret|api[_ -]?key)\s*[=:]\s*[^\s,;]+"
    r"|(?:authorization|proxy-authorization)\s*:\s*(?:bearer|basic)\s*[^\s]+"
    r"|(?:cookie|set-cookie|session(?:[_ -]?id)?)\s*[=:]\s*[^\s,;]+"
    r"|-----begin[^\n]*(?:private key|encrypted private key)-----"
    r"|(?:mayak|provider)[_-](?:secret|token|password|credential)[^\s=:]*\s*[=:]"
)


@dataclass(frozen=True)
class Counts:
    total: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    errors: int = 0
    duration: str = "0"


def _safe(value: object, *, fallback: str = "[REDACTED]") -> str:
    text = str(value or "")
    if SENSITIVE.search(text):
        return fallback
    text = "".join(char if char.isprintable() and char not in "\r\n\t" else " " for char in text)
    return text[:MAX_TEXT] if text else fallback


def _identity(
    source_sha: str | None, run_id: str | None, job: str | None, attempt: str | None
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "technical_id": TECHNICAL_ID,
        "source_sha": _safe(source_sha or os.getenv("GITHUB_SHA", ""), fallback="unknown"),
        "github_run_id": _safe(run_id or os.getenv("GITHUB_RUN_ID", ""), fallback="unknown"),
        "job": _safe(job or os.getenv("GITHUB_JOB", ""), fallback="unknown"),
        "attempt": _safe(attempt or os.getenv("GITHUB_RUN_ATTEMPT", ""), fallback="unknown"),
        "python_version": _safe(sys.version.split()[0]),
        "uv_version": _safe(os.getenv("UV_VERSION", ""), fallback="unknown"),
    }


def _suite_nodes(root: ET.Element) -> list[ET.Element]:
    return [root] if root.tag == "testsuite" else list(root.findall(".//testsuite"))


def _counts(root: ET.Element) -> Counts:
    suites = _suite_nodes(root)
    total = sum(int(s.attrib.get("tests", "0")) for s in suites)
    skipped = sum(int(s.attrib.get("skipped", "0")) for s in suites)
    errors = sum(int(s.attrib.get("errors", "0")) for s in suites)
    failed = sum(int(s.attrib.get("failures", "0")) for s in suites)
    passed = max(0, total - skipped - errors - failed)
    duration = sum(float(s.attrib.get("time", "0") or 0) for s in suites)
    return Counts(total, passed, failed, skipped, errors, f"{duration:.3f}")


def _node_id(case: ET.Element) -> str:
    classname = case.attrib.get("classname", "")
    name = case.attrib.get("name", "")
    raw = f"{classname}::{name}" if classname else name
    return _safe(raw, fallback="[REDACTED_NODE_ID]")


def _failures(root: ET.Element) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    for case in root.findall(".//testcase"):
        failure = case.find("failure")
        error = case.find("error")
        marker = failure if failure is not None else error
        if marker is None:
            continue
        category = "pytest_failure" if failure is not None else "pytest_collection_or_error"
        result.append({
            "node_id": _node_id(case),
            "category": category,
            "reason": _safe(marker.attrib.get("message", "") or marker.text or "failure"),
        })
        if len(result) >= MAX_FAILURES:
            break
    return result


def parse_junit(path: Path, *, source_sha: str | None = None, run_id: str | None = None,
                job: str | None = None, attempt: str | None = None) -> dict[str, Any]:
    base = _identity(source_sha, run_id, job, attempt)
    try:
        root = ET.parse(path).getroot()
        counts = _counts(root)
    except (OSError, ET.ParseError, ValueError, TypeError):
        base.update({
            "total_tests": 0, "passed": 0, "failed": 0, "skipped": 0, "error_count": 0,
            "duration": "0",
            "failing_tests": [],
            "exception_categories": ["diagnostic_input_invalid"],
            "redacted_reasons": ["diagnostic input unavailable or malformed"],
            "diagnostic_generation_status": "fail_closed_input_error",
        })
        return base
    failures = _failures(root)
    base.update({
        "total_tests": counts.total, "passed": counts.passed, "failed": counts.failed,
        "skipped": counts.skipped, "error_count": counts.errors, "duration": counts.duration,
        "failing_tests": [item["node_id"] for item in failures],
        "exception_categories": sorted({item["category"] for item in failures}),
        "redacted_reasons": [item["reason"] for item in failures],
        "diagnostic_generation_status": "ok",
    })
    return base


def write_diagnostic(path: Path, output: Path, **identity: str | None) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    data = parse_junit(path, **identity)
    serialized = json.dumps(data, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    output.write_text(serialized + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("junit", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--source-sha")
    parser.add_argument("--run-id")
    parser.add_argument("--job")
    parser.add_argument("--attempt")
    args = parser.parse_args()
    write_diagnostic(args.junit, args.output, source_sha=args.source_sha, run_id=args.run_id,
                     job=args.job, attempt=args.attempt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
