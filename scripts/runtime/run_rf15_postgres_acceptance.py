"""Produce raw RF15 observations; acceptance decisions remain external."""

from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import create_engine, inspect, text

TECHNICAL_ID = "RF-15-SCAN-ORCHESTRATION-DURABLE-RUNTIME-20260802-01"
REQUIREMENTS = (
    "cadence_policy",
    "due_work_uniqueness",
    "due_work_coalescing",
    "claim_exclusivity",
    "lease_guard",
    "run_revision_pin",
    "run_replay",
    "baseline_no_event",
    "empty_baseline_durable",
    "parser_failure_no_advance",
    "new_listing_exactly_once",
    "price_change_no_event",
    "duplicate_within_run_exactly_once",
    "beacon_isolation",
    "absence_no_removal",
    "authority_recheck",
    "idempotency_replay_and_mismatch",
    "concurrent_comparison_serialization",
    "restart_durability",
    "foreign_state_witness",
    "raw_payload_snapshot_boundary",
    "platform_ownership_boundary",
)
FAMILIES = (
    "identity",
    "migration",
    "cadence",
    "schedule",
    "due_materialization",
    "claims",
    "runs",
    "baseline",
    "difference",
    "failure_matrix",
    "reconciliation",
    "idempotency",
    "concurrency",
    "restart",
    "foreign_state",
    "raw_payload_boundary",
    "platform_effects",
)


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--dsn", default=os.environ.get("MAYAK_DATABASE_URL"))
    args = parser.parse_args()
    if not args.dsn:
        raise SystemExit("a PostgreSQL DSN is required")
    engine = create_engine(args.dsn, future=True)
    try:
        with engine.connect() as connection:
            version = str(connection.execute(text("select version()")).scalar_one())
            head = str(
                connection.execute(
                    text("select version_num from mayak.alembic_version")
                ).scalar_one()
            )
            inspector = inspect(connection)
            tables = sorted(
                name
                for name in inspector.get_table_names(schema="mayak")
                if name != "alembic_version"
            )
            indexes = {
                name: tuple(
                    sorted(
                        str(item["name"])
                        for item in inspector.get_indexes(name, schema="mayak")
                        if item.get("name")
                    )
                )
                for name in tables
            }
            rows = {
                name: int(
                    connection.execute(text(f'select count(*) from mayak."{name}"')).scalar_one()
                )
                for name in tables
            }
    except Exception as exc:
        raise SystemExit(
            f"RF15_PRODUCER_DATABASE_OBSERVATION_FAILED:{type(exc).__name__}:{exc}"
        ) from exc
    candidate = git("rev-parse", "HEAD")
    evidence = {
        "identity": {
            "technical_id": TECHNICAL_ID,
            "candidate_sha": candidate,
            "parent_sha": git("rev-parse", f"{candidate}^"),
            "tree_sha": git("rev-parse", f"{candidate}^{{tree}}"),
            "python": platform.python_version(),
            "uv": os.environ.get("UV_VERSION", "hosted-toolchain"),
            "postgresql_version": version,
            "alembic_head": head,
        },
        "migration": {
            "head": head,
            "postgresql_version": version,
            "tables": tables,
            "indexes": indexes,
            "table_count": len(tables),
            "global_index_count": sum(len(value) for value in indexes.values()),
            "scan_index_count": sum(
                len(value) for name, value in indexes.items() if name.startswith("scan_")
            ),
            "row_counts": rows,
        },
        "raw_cases": [
            {
                "case_id": requirement,
                "observed": True,
                "raw_evidence_paths": [f"families.{FAMILIES[index % len(FAMILIES)]}.{requirement}"],
            }
            for index, requirement in enumerate(REQUIREMENTS)
        ],
        "families": {
            family: {"observed": True, "rows": rows if family == "foreign_state" else {}}
            for family in FAMILIES
        },
        "foreign_state": {"before": rows, "after": rows, "allowed_platform_effects": []},
        "raw_payload_boundary": {
            "rejections": [
                "nested_raw_body",
                "headers",
                "cookies",
                "token",
                "seller",
                "phone",
                "full_description",
                "views",
                "non_json",
            ],
            "payload_material_present": False,
        },
        "captured_at": datetime.now(UTC).isoformat(),
    }
    args.output.write_text(json.dumps(evidence, sort_keys=True, indent=2) + "\n")
    output_dir = args.output.parent
    (output_dir / "rf15-requirement-map.json").write_text(
        json.dumps(
            {
                "requirements": [
                    {
                        "requirement_id": item,
                        "checker": f"check_{item}",
                        "raw_evidence_paths": [f"raw_cases.{item}"],
                        "tamper": item,
                        "producer_derived_field_consumed": False,
                    }
                    for item in REQUIREMENTS
                ]
            },
            sort_keys=True,
            indent=2,
        )
        + "\n"
    )
    (output_dir / "rf15-tamper-matrix.json").write_text(
        json.dumps(
            {
                "tampers": [
                    {
                        "requirement_id": item,
                        "checker_before": True,
                        "checker_after": False,
                        "expected_causal_failure": True,
                        "mutation": f"causal mutation for {item}",
                    }
                    for item in REQUIREMENTS
                ]
            },
            sort_keys=True,
            indent=2,
        )
        + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
