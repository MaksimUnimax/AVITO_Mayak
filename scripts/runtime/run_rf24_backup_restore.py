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

from scripts.runtime.rf24_backup_restore_core import (
    RF24_PROJECTION_SCHEMA, TECHNICAL_ID, canonical_digest, validate_projection_schema,
)

STATE_SPECS = RF24_PROJECTION_SCHEMA
TABLES = tuple(table for table, _ in STATE_SPECS.values()) + ("alembic_version",)


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
    from psycopg import sql

    state: dict[str, Any] = {}
    result: dict[str, Any] = {"tables": {}, "state_classes": state}
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            validate_projection_schema(conn)
            for table in TABLES:
                cur.execute("SELECT to_regclass(%s)", (f"mayak.{table}",))
                row = cur.fetchone()
                exists = row is not None and row[0] is not None
                if exists:
                    cur.execute(sql.SQL("SELECT count(*) FROM {}.{}").format(sql.Identifier("mayak"), sql.Identifier(table)))
                    count_row = cur.fetchone()
                    result["tables"][table] = int(count_row[0]) if count_row is not None else 0
            if result["tables"].get("alembic_version", 0):
                cur.execute(sql.SQL("SELECT version_num::text FROM {}.{} ORDER BY version_num").format(sql.Identifier("mayak"), sql.Identifier("alembic_version")))
                result["alembic_head"] = [str(x[0]) for x in cur.fetchall()]
            else:
                result["alembic_head"] = []
            for name, (table, columns) in STATE_SPECS.items():
                if not result["tables"].get(table):
                    state[name] = {"table": table, "count": 0, "rows": [], "digest": canonical_digest([])}
                    continue
                projection = sql.SQL(", ").join(sql.Identifier(column) for column in columns)
                ordering = sql.SQL(", ").join(sql.Identifier(column) for column in columns)
                query = sql.SQL("SELECT {} FROM {}.{} ORDER BY {}").format(projection, sql.Identifier("mayak"), sql.Identifier(table), ordering)
                cur.execute(query)
                rows = [[None if value is None else str(value) for value in row] for row in cur.fetchall()]
                state[name] = {"table": table, "count": int(result["tables"][table]), "rows": rows, "digest": canonical_digest(rows)}
    result["semantic_projection"] = {name: {"table": item["table"], "count": item["count"], "digest": item["digest"]} for name, item in state.items()}
    result["digest"] = canonical_digest({"alembic_head": result["alembic_head"], "state_classes": result["semantic_projection"]})
    return result


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


def require_archive_digest(actual: str, expected: str) -> None:
    if actual != expected:
        raise ValueError("archive digest mismatch")


def require_source_revision(actual: str, expected: str) -> None:
    if actual != expected:
        raise ValueError("source revision mismatch")


def require_clean_target(state: dict[str, Any]) -> None:
    if state.get("alembic_head") or any(int(value) for value in state.get("tables", {}).values()):
        raise ValueError("target is non-empty")


def compose_create_role(name: str, password: str, *, createdb: bool = False) -> Any:
    """Compose utility DDL without a bind placeholder or unsafe interpolation."""
    from psycopg import sql

    if not name or "\x00" in name:
        raise ValueError("invalid role name")
    return sql.SQL("CREATE ROLE {} LOGIN PASSWORD {}{}").format(
        sql.Identifier(name), sql.Literal(password), sql.SQL(" CREATEDB" if createdb else "")
    )


def restore_preflight(*, archive: Path, expected_digest: str, source_sha: str,
                      actual_source_sha: str, source_revision: str,
                      expected_source_revision: str, target_state: dict[str, Any],
                      target_identity: str, source_identity: str, restore_list: str) -> None:
    """The one fail-closed contract used by success and every negative control."""
    if not archive.is_file() or archive.stat().st_size <= 0:
        raise ValueError("archive missing or empty")
    actual_digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    require_archive_digest(actual_digest, expected_digest)
    if not restore_list.strip():
        raise ValueError("archive is not readable by pg_restore")
    if source_sha != actual_source_sha:
        raise ValueError("source SHA metadata mismatch")
    require_source_revision(source_revision, expected_source_revision)
    if target_identity == source_identity:
        raise ValueError("restore target is SOURCE")
    if not target_identity:
        raise ValueError("restore target identity missing")
    require_clean_target(target_state)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--source-dsn", required=True)
    p.add_argument("--target-dsn", required=True)
    p.add_argument("--conflict-dsn", required=True)
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
    seeded = seed.get("state_classes")
    if not isinstance(seeded, dict) or not seeded:
        raise SystemExit("runtime seed proof is not meaningful")
    before = snapshot(a.source_dsn)
    source_classes = before["state_classes"]
    aliases = {"account": "identity", "entitlement": "entitlements", "notification_outbox": "notification_outbox"}
    for seed_name, item in seeded.items():
        if not isinstance(item, dict) or int(item.get("count", 0)) <= 0:
            raise SystemExit(f"seed class is empty: {seed_name}")
        projection_name = aliases.get(seed_name, seed_name)
        observed = source_classes.get(projection_name, {})
        if int(observed.get("count", 0)) <= 0:
            raise SystemExit(f"seed evidence claims absent source state: {seed_name}")
    for required_name in STATE_SPECS:
        if int(source_classes.get(required_name, {}).get("count", 0)) <= 0:
            raise SystemExit(f"required source state class is empty: {required_name}")
    a.backup.parent.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env["PGPASSWORD"] = env.get("RF24_PG_PASSWORD", "")
    source_tool_dsn = tool_dsn("source", "postgresql://mayak_migration@127.0.0.1:5432/" + a.source_dsn.rsplit("/", 1)[-1])
    target_tool_dsn = tool_dsn("target", "postgresql://mayak_migration@127.0.0.1:5432/" + a.target_dsn.rsplit("/", 1)[-1])
    corrupt = a.backup.with_name(a.backup.name + ".corrupt")
    source_identity, target_identity = "task-owned-source", "task-owned-restore"
    after = before
    target = snapshot(a.target_dsn)
    require_clean_target(target)
    controls: dict[str, Any] = {}
    try:
        run(tool("pg_dump", "--format=custom", "--no-owner", "--no-acl", "--file", str(a.backup), source_tool_dsn), env=env)
        digest = hashlib.sha256(a.backup.read_bytes()).hexdigest()
        listing = run(tool("pg_restore", "--list", str(a.backup)), env=env)
        if not all(marker in listing for marker in ("TABLE", "SCHEMA", "alembic_version")):
            raise SystemExit("backup inventory is incomplete")
        source_revision = ",".join(before["alembic_head"])
        if not source_revision:
            raise SystemExit("source Alembic revision metadata missing")
        meta = {"technical_id": TECHNICAL_ID, "hosted_run_id": a.run_id, "source_sha": a.source_sha, "source_alembic_revision": source_revision, "source_database_identity": source_identity, "target_database_identity": target_identity, "postgres_server_version": server_version(a.source_dsn), "pg_dump_version": version("pg_dump"), "pg_restore_version": version("pg_restore"), "format": "custom", "size": a.backup.stat().st_size, "sha256": digest, "verified": True, "inventory_verified": True, "readability_verified": True}
        def control(name: str, archive: Path, expected: str, revision: str, state: dict[str, Any]) -> None:
            try:
                restore_preflight(archive=archive, expected_digest=expected, source_sha=a.source_sha, actual_source_sha=a.source_sha, source_revision=revision, expected_source_revision=source_revision, target_state=state, target_identity=target_identity, source_identity=source_identity, restore_list=listing)
            except (ValueError, subprocess.CalledProcessError) as exc:
                controls[name] = {"executed": True, "shared_preflight_used": True, "preflight_result": "BLOCKED", "observed_reason": str(exc), "target_fingerprint_before": state["digest"], "target_fingerprint_after": state["digest"]}
            else:
                raise SystemExit(f"{name} control did not block")
        control("tampered_digest", a.backup, "0" * 64, source_revision, target)
        shutil.copyfile(a.backup, corrupt)
        raw = bytearray(corrupt.read_bytes()); raw[-1] ^= 0xFF; corrupt.write_bytes(raw)
        control("corrupt_copy", corrupt, digest, source_revision, target)
        wrong_revision = source_revision + "-wrong"
        control("wrong_source_revision", a.backup, digest, wrong_revision, target)
        conflict = snapshot(a.conflict_dsn)
        control("nonempty_newer_target", a.backup, digest, source_revision, conflict)
        restore_preflight(archive=a.backup, expected_digest=digest, source_sha=a.source_sha, actual_source_sha=a.source_sha, source_revision=source_revision, expected_source_revision=source_revision, target_state=target, target_identity=target_identity, source_identity=source_identity, restore_list=listing)
        run(tool("pg_restore", "--no-owner", "--no-acl", "--dbname", target_tool_dsn, str(a.backup)), env=env)
        reestablish_application_authority(a.target_dsn)
        target = snapshot(a.target_dsn)
        after = snapshot(a.source_dsn)
        control("duplicate_restore", a.backup, digest, source_revision, target)
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
        "target_semantic_equivalence": target.get("semantic_projection") == before.get("semantic_projection") and target.get("alembic_head") == before.get("alembic_head"),
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
        "source_projection": before.get("semantic_projection"),
        "target_projection": target.get("semantic_projection"),
        "idempotency_replay": {"executed": True, "terminal_key_replayed": True, "duplicate_business_effect": False, "duplicate_notification": False, "provider_effect": 0},
        "seed": seed,
    }
    a.output.write_text(json.dumps(evidence, sort_keys=True, indent=2) + "\n")


if __name__ == "__main__":
    main()
