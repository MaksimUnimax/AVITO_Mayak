"""Produce raw RF15 PostgreSQL evidence; acceptance decisions belong to the verifier."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import create_engine, inspect, text


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    url = os.environ["MAYAK_DATABASE_URL"]
    engine = create_engine(url, future=True)
    with engine.connect() as connection:
        version = connection.execute(text("select version()")).scalar_one()
        head = connection.execute(
            text("select version_num from mayak.alembic_version")
        ).scalar_one()
        tables = sorted(inspect(connection).get_table_names(schema="mayak"))
        scan_tables = [name for name in tables if name.startswith("scan_")]
        rows = {
            name: connection.execute(text(f"select count(*) from mayak.{name}")).scalar_one()
            for name in scan_tables
        }
    candidate = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    evidence = {
        "identity": {
            "technical_id": "RF-15-SCAN-ORCHESTRATION-DURABLE-RUNTIME-20260802-01",
            "candidate_sha": candidate,
        },
        "migration": {
            "head": head,
            "postgresql_version": version,
            "scan_tables": scan_tables,
            "row_counts": rows,
        },
        "raw_cases": [
            {
                "case_id": "schema_current_head",
                "head": head,
                "required_tables": [
                    "scan_schedules",
                    "scan_work_items",
                    "scan_runs",
                    "scan_listing_observations",
                    "scan_beacon_listing_state",
                    "scan_anchors",
                ],
            }
        ],
        "captured_at": datetime.now(UTC).isoformat(),
    }
    args.output.write_text(json.dumps(evidence, sort_keys=True, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
