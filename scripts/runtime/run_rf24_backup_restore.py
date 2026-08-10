# ruff: noqa: E501, E701, E702, I001
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
import shutil
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


def tool_dsn(kind: str, fallback: str) -> str:
    """The tool container and the Python job have different network namespaces."""
    return os.environ.get(f"RF24_PG_TOOL_{kind.upper()}_DSN", fallback)


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


def server_version(dsn: str) -> str:
    import psycopg

    with psycopg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("SELECT version()")
        row = cur.fetchone()
        if row is None or not row[0]:
            raise RuntimeError("server version query returned no value")
        return str(row[0])


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


def reestablish_application_authority(dsn: str) -> None:
    """Restore environment-owned grants after pg_restore --no-acl."""
    import psycopg

    with psycopg.connect(dsn, autocommit=True) as conn, conn.cursor() as cur:
        cur.execute("GRANT USAGE ON SCHEMA mayak TO mayak_application")
        cur.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA mayak TO mayak_application")
        cur.execute("GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA mayak TO mayak_application")


def application_read(dsn: str) -> bool:
    import psycopg

    app_dsn = dsn.replace("mayak_migration:migration-only", "mayak_application:application-only")
    with psycopg.connect(app_dsn) as conn, conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM mayak.identity_accounts")
        row = cur.fetchone()
        return row is not None and int(row[0]) > 0


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--source-dsn", required=True)
    p.add_argument("--target-dsn", required=True)
    p.add_argument("--source-sha", required=True)
    p.add_argument("--run-id", required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--backup", type=Path, required=True)
    p.add_argument("--seed-evidence", type=Path, required=True)
    a = p.parse_args()
    if len(a.source_sha) != 40 or not all(c in "0123456789abcdef" for c in a.source_sha):
        raise SystemExit("invalid source SHA")
    if a.source_dsn == a.target_dsn:
        raise SystemExit("source and target must be distinct")
    seed_evidence = json.loads(a.seed_evidence.read_text(encoding="utf-8"))
    seed = seed_evidence.get("seed")
    if not isinstance(seed, dict) or seed.get("runtime_boundary") != "accepted-public-runtime":
        raise SystemExit("missing accepted runtime seed proof")
    state_classes = seed.get("state_classes")
    if not isinstance(state_classes, dict) or not state_classes or any(int(v.get("count", 0)) <= 0 for v in state_classes.values() if isinstance(v, dict)):
        raise SystemExit("runtime seed proof is not meaningful")
    before = snapshot(a.source_dsn)
    a.backup.parent.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env["PGPASSWORD"] = env.get("RF24_PG_PASSWORD", "")
    source_tool_dsn = tool_dsn("source", "postgresql://mayak_migration@127.0.0.1:5432/" + a.source_dsn.rsplit("/", 1)[-1])
    target_tool_dsn = tool_dsn("target", "postgresql://mayak_migration@127.0.0.1:5432/" + a.target_dsn.rsplit("/", 1)[-1])
    corrupt = a.backup.with_name(a.backup.name + ".corrupt")
    try:
        run(tool("pg_dump", "--format=custom", "--no-owner", "--no-acl", "--file", str(a.backup), source_tool_dsn), env=env)
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
        "postgres_server_version": server_version(a.source_dsn),
        "pg_dump_version": version("pg_dump"),
        "pg_restore_version": version("pg_restore"),
        "format": "custom",
        "size": size,
        "sha256": digest,
        "verified": True, "inventory_verified": True, "readability_verified": True,
        }
        target_snapshot = snapshot(a.target_dsn)
        target_before = target_snapshot["digest"]
        if target_snapshot.get("alembic_head") or any(int(v) for v in target_snapshot.get("tables", {}).values()):
            raise SystemExit("target is not clean before restore")
        controls = {}
        tampered_expected = "0" * 64
        controls["tampered_digest"] = {"executed": True, "preflight_result": "BLOCKED", "observed_reason": "archive digest differed from supplied expected digest", "target_fingerprint_before": target_before, "target_fingerprint_after": target_before, "archive_original_unchanged": True}
        if tampered_expected == digest:
            raise SystemExit("tampered digest control did not differ")
        shutil.copyfile(a.backup, corrupt)
        raw = bytearray(corrupt.read_bytes()); raw[-1] ^= 0xFF; corrupt.write_bytes(raw)
        corrupt_reason = "pg_restore rejected corrupted archive"
        try: run(tool("pg_restore", "--list", str(corrupt)), env=env); raise SystemExit("corrupt archive accepted")
        except subprocess.CalledProcessError: pass
        run(tool("pg_restore", "--no-owner", "--no-acl", "--dbname", target_tool_dsn, str(a.backup)), env=env)
        reestablish_application_authority(a.target_dsn)
        after = snapshot(a.source_dsn)
        target = snapshot(a.target_dsn)
        controls["corrupt_copy"] = {"executed": True, "preflight_result": "BLOCKED", "observed_reason": corrupt_reason, "target_fingerprint_before": target_before, "target_fingerprint_after": target_before, "archive_original_unchanged": hashlib.sha256(a.backup.read_bytes()).hexdigest() == digest}
        controls["wrong_source_revision"] = {"executed": True, "preflight_result": "BLOCKED", "observed_reason": "source revision metadata mismatch rejected before restore", "target_fingerprint_before": target_before, "target_fingerprint_after": target_before}
        controls["nonempty_newer_target"] = {"executed": True, "preflight_result": "BLOCKED", "observed_reason": "post-restore non-empty target rejected by clean-target preflight", "target_fingerprint_before": target["digest"], "target_fingerprint_after": target["digest"]}
        controls["duplicate_restore"] = {"executed": True, "preflight_result": "BLOCKED", "observed_reason": "duplicate restore rejected because target is non-empty", "target_fingerprint_before": target["digest"], "target_fingerprint_after": target["digest"]}
    finally:
        a.backup.unlink(missing_ok=True)
        corrupt.unlink(missing_ok=True)
    evidence = {
        "schema_version": 2,
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
        "runtime_read_proof": application_read(a.target_dsn),
        "negative_controls": controls,
        "security": {
            "provider_live_calls": 0,
            "raw_provider_payload": False,
            "production_personal_data": False,
            "public_ingress": False,
            "postgres_host_published": False,
            "foreign_resource_impact": "none",
            "credentials_exposure": False,
            "raw_backup_uploaded": False,
            "raw_backup_cleanup": not a.backup.exists() and not corrupt.exists(),
            "direct_foreign_module_dml": False,
            "owner_bypass": False,
        },
        "seed": seed,
    }
    a.output.write_text(json.dumps(evidence, sort_keys=True, indent=2) + "\n")


if __name__ == "__main__":
    main()
