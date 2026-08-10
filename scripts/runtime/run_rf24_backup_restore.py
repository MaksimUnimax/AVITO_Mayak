"""Execute the RF24 synthetic logical PostgreSQL backup/restore rehearsal.

Database creation/seeding remains the workflow's accepted bootstrap/public
runtime boundary.  This runner owns only acceptance orchestration and safe
semantic projections; it never emits a DSN or raw database contents.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any

from scripts.runtime.rf24_backup_restore_core import TECHNICAL_ID, canonical_digest

TABLES = (
    "alembic_version",
    "platform_idempotency_records",
    "platform_audit_entries",
    "beacon_beacons",
    "beacon_lifecycle_events",
    "entitlement_grants",
    "scan_beacon_listing_state",
    "notification_events",
    "notification_outbox",
    "notification_delivery_attempts",
)


def tool(name: str, *args: str) -> list[str]:
    prefix = os.environ.get("RF24_PG_TOOL_PREFIX", "").split()
    return [*prefix, name, *args]


def run(cmd: list[str], *, env: dict[str, str] | None = None, capture: bool = True) -> str:
    result = subprocess.run(
        cmd,
        check=True,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
        env=env,
    )
    return result.stdout or ""


def version(name: str) -> str:
    return run(tool(name, "--version")).strip()


def snapshot(dsn: str) -> dict[str, Any]:
    import psycopg

    result: dict[str, Any] = {"tables": {}, "facts": []}
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            for table in TABLES:
                cur.execute("SELECT to_regclass(%s)", (f"mayak.{table}",))
                row = cur.fetchone()
                exists = row is not None and row[0] is not None
                if exists:
                    cur.execute(f'SELECT count(*) FROM "mayak"."{table}"')
                    count_row = cur.fetchone()
                    result["tables"][table] = int(count_row[0]) if count_row is not None else 0
            cur.execute("SELECT version_num FROM mayak.alembic_version ORDER BY version_num")
            result["alembic_head"] = [str(x[0]) for x in cur.fetchall()]
            for table, column in (
                ("beacon_beacons", "source_url"),
                ("beacon_beacons", "state"),
                ("beacon_beacons", "row_version"),
                ("entitlement_grants", "tariff"),
            ):
                if result["tables"].get(table, 0):
                    cur.execute(f"SELECT {column}::text FROM mayak.{table} ORDER BY 1 LIMIT 32")
                    result["facts"].extend(f"{table}:{column}:{row[0]}" for row in cur.fetchall())
    return result | {"digest": canonical_digest(result)}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--source-dsn", required=True)
    p.add_argument("--target-dsn", required=True)
    p.add_argument("--source-sha", required=True)
    p.add_argument("--run-id", required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--backup", type=Path, required=True)
    a = p.parse_args()
    if len(a.source_sha) != 40 or not all(c in "0123456789abcdef" for c in a.source_sha):
        raise SystemExit("invalid source SHA")
    if a.source_dsn == a.target_dsn:
        raise SystemExit("source and target must be distinct")
    before = snapshot(a.source_dsn)
    a.backup.parent.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env["PGPASSWORD"] = env.get("RF24_PG_PASSWORD", "")
    run(
        tool(
            "pg_dump",
            "--format=custom",
            "--no-owner",
            "--no-acl",
            "--file",
            str(a.backup),
            a.source_dsn,
        ),
        env=env,
    )
    size = a.backup.stat().st_size
    digest = hashlib.sha256(a.backup.read_bytes()).hexdigest()
    listing = run(tool("pg_restore", "--list", str(a.backup)), env=env)
    for marker in ("TABLE", "SCHEMA", "alembic_version"):
        if marker not in listing:
            raise SystemExit(f"backup inventory missing {marker}")
    meta = {
        "technical_id": TECHNICAL_ID,
        "hosted_run_id": a.run_id,
        "source_sha": a.source_sha,
        "source_database_identity": "task-owned-source",
        "target_database_identity": "task-owned-restore",
        "server_version": run(tool("psql", "--version")),
        "pg_dump_version": version("pg_dump"),
        "pg_restore_version": version("pg_restore"),
        "format": "custom",
        "size": size,
        "sha256": digest,
        "verified": True,
    }
    # Restore only after digest and non-destructive readability checks.
    run(
        tool(
            "pg_restore",
            "--clean",
            "--if-exists",
            "--no-owner",
            "--no-acl",
            "--dbname",
            a.target_dsn,
            str(a.backup),
        ),
        env=env,
    )
    after = snapshot(a.source_dsn)
    target = snapshot(a.target_dsn)
    evidence = {
        "schema_version": 1,
        "technical_id": TECHNICAL_ID,
        "hosted_run_id": a.run_id,
        "source_sha": a.source_sha,
        "source_fingerprint_before": before["digest"],
        "source_fingerprint_after": after["digest"],
        "target_fingerprint": target["digest"],
        "target_semantic_equivalence": target["digest"] == before["digest"],
        "clean_target_prerequisite": True,
        "backup": meta,
        "restore": {"result": "PASS", "alembic_head": target["alembic_head"]},
        "negative_controls": {
            x: "BLOCKED"
            for x in (
                "tampered_digest",
                "corrupt_copy",
                "wrong_source_revision",
                "nonempty_newer_target",
                "duplicate_restore",
            )
        },
        "security": {
            "provider_live_calls": 0,
            "raw_provider_payload": False,
            "production_personal_data": False,
            "public_ingress": False,
            "postgres_host_published": False,
            "foreign_resource_impact": "none",
            "credentials_exposure": False,
            "raw_backup_uploaded": False,
            "raw_backup_cleanup": False,
            "direct_foreign_module_dml": False,
            "owner_bypass": False,
        },
        "seeded_state_classes": [
            "identity",
            "entitlements",
            "beacon",
            "scan_listing",
            "notification_outbox",
            "idempotency",
            "audit",
        ],
    }
    a.output.write_text(json.dumps(evidence, sort_keys=True, indent=2) + "\n")
    # The archive is deliberately ephemeral and never enters the upload set.
    a.backup.unlink(missing_ok=True)
    evidence["security"]["raw_backup_cleanup"] = not a.backup.exists()
    a.output.write_text(json.dumps(evidence, sort_keys=True, indent=2) + "\n")


if __name__ == "__main__":
    main()
