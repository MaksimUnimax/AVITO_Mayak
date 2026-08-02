"""Independent fail-closed verifier for the RF15 raw evidence envelope."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence", type=Path)
    args = parser.parse_args()
    data = json.loads(args.evidence.read_text())
    required = {"identity", "migration", "raw_cases"}
    if set(data) < required:
        raise SystemExit("missing raw evidence")
    if (
        data["identity"].get("technical_id")
        != "RF-15-SCAN-ORCHESTRATION-DURABLE-RUNTIME-20260802-01"
    ):
        raise SystemExit("wrong technical id")
    expected = {
        "scan_schedules",
        "scan_work_items",
        "scan_runs",
        "scan_listing_observations",
        "scan_beacon_listing_state",
        "scan_anchors",
    }
    if set(data["migration"].get("scan_tables", ())) != expected:
        raise SystemExit("scan schema evidence is incomplete")
    if not data["migration"].get("head"):
        raise SystemExit("missing Alembic head")
    if (
        data["identity"].get("candidate_sha")
        != subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    ):
        raise SystemExit("candidate SHA mismatch")
    print("RF15_ACCEPTANCE_VERIFIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
