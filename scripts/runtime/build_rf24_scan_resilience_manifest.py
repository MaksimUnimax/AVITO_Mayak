# ruff: noqa: E501
"""Create the hash-bound, credential-safe package manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def build(output: Path, payloads: list[Path], *, source_sha: str, run_id: str, scanner_result: Path) -> None:
    try:
        scan = json.loads(scanner_result.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("scanner result is missing or malformed") from exc
    if (
        not isinstance(scan, dict)
        or scan.get("scanner") != "rf24-scan-resilience-artifact-safety"
        or scan.get("schema_version") != 1
        or not isinstance(scan.get("finding_count"), int)
        or not isinstance(scan.get("findings"), list)
        or scan["finding_count"] != len(scan["findings"])
        or scan["finding_count"] != 0
    ):
        raise ValueError("scanner result is not a zero-finding machine-readable PASS")
    entries = []
    for path in payloads:
        if not path.is_file() or path.stat().st_size == 0:
            raise ValueError(f"empty or missing payload: {path}")
        entries.append({"basename": path.name, "size": path.stat().st_size,
                        "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    output.write_text(json.dumps({
        "artifact_name": "rf24-scan-runtime-resilience", "technical_id": "RF24-SCAN-RUNTIME-RESILIENCE-SCENARIOS-01-CORRECTIVE-02",
        "source_sha": source_sha, "acceptance_run_id": run_id,
        "finding_count": scan["finding_count"],
        "scanner_result": {"basename": scanner_result.name, "sha256": hashlib.sha256(scanner_result.read_bytes()).hexdigest()},
        "payloads": entries,
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--source-sha", required=True)
    p.add_argument("--run-id", required=True)
    p.add_argument("--scanner-result", type=Path, required=True)
    p.add_argument("payloads", type=Path, nargs="+")
    a = p.parse_args()
    build(a.output, a.payloads, source_sha=a.source_sha, run_id=a.run_id, scanner_result=a.scanner_result)
