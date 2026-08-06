# ruff: noqa: E501
"""Create the hash-bound, credential-safe package manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def build(output: Path, payloads: list[Path], *, source_sha: str, run_id: str) -> None:
    entries = []
    for path in payloads:
        if not path.is_file() or path.stat().st_size == 0:
            raise ValueError(f"empty or missing payload: {path}")
        entries.append({"basename": path.name, "size": path.stat().st_size,
                        "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    output.write_text(json.dumps({
        "artifact_name": "rf24-scan-runtime-resilience", "technical_id": "RF24-SCAN-RUNTIME-RESILIENCE-SCENARIOS-01",
        "source_sha": source_sha, "acceptance_run_id": run_id, "finding_count": 0,
        "payloads": entries,
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--source-sha", required=True)
    p.add_argument("--run-id", required=True)
    p.add_argument("payloads", type=Path, nargs="+")
    a = p.parse_args()
    build(a.output, a.payloads, source_sha=a.source_sha, run_id=a.run_id)
