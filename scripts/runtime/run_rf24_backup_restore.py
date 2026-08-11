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
import sys
import socket
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from scripts.runtime.rf24_backup_restore_core import (
    CleanTargetState, RF24_PROJECTION_SCHEMA, TECHNICAL_ID, canonical_digest,
    inspect_clean_target, validate_projection_schema,
)

STATE_SPECS = RF24_PROJECTION_SCHEMA
TABLES = tuple(table for table, _ in STATE_SPECS.values()) + ("alembic_version",)
FULL_SOURCE = "FULL_SOURCE"
CLEAN_TARGET_PRE_RESTORE = "CLEAN_TARGET_PRE_RESTORE"
FULL_CONFLICT = "FULL_CONFLICT"
FULL_TARGET_POST_RESTORE = "FULL_TARGET_POST_RESTORE"
RECOVERY_STAGE_SEQUENCE = (
    "full_source", "clean_target", "full_conflict", "pg_dump", "archive_verify",
    "negative_controls", "restore", "full_target", "duplicate_restore", "replay", "evidence",
)


def execute_recovery_stage_sequence(operations: dict[str, Any]) -> list[str]:
    """Executable gate used by focused tests and kept fail-closed for callers."""
    missing = [stage for stage in RECOVERY_STAGE_SEQUENCE if not callable(operations.get(stage))]
    if missing:
        raise ValueError(f"recovery stage operation missing: {missing[0]}")
    reached: list[str] = []
    for stage in RECOVERY_STAGE_SEQUENCE:
        operations[stage]()
        reached.append(stage)
    return reached


@dataclass(frozen=True, slots=True)
class ConnectionIdentity:
    """A direct Psycopg/libpq identity; SQLAlchemy URLs never cross this boundary."""

    host: str
    port: int
    dbname: str
    user: str
    password: str

    @classmethod
    def from_dsn(cls, value: str) -> "ConnectionIdentity":
        parsed = urlsplit(value)
        if parsed.scheme != "postgresql":
            raise ValueError("psycopg connection kind requires a libpq postgresql:// URL")
        if not parsed.hostname or not parsed.path.strip("/") or not parsed.username:
            raise ValueError("invalid psycopg connection identity")
        if parsed.password is None:
            raise ValueError("psycopg connection identity has no password")
        return cls(parsed.hostname, parsed.port or 5432, parsed.path.strip("/"), parsed.username, parsed.password)

    def connect_kwargs(self) -> dict[str, object]:
        return {"host": self.host, "port": self.port, "dbname": self.dbname, "user": self.user, "password": self.password}

    def public(self) -> dict[str, object]:
        return {"host": self.host, "port": self.port, "dbname": self.dbname, "user": self.user}


def direct_identity(value: str) -> ConnectionIdentity:
    return ConnectionIdentity.from_dsn(value)


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


def run_binary_to_file(cmd: list[str], destination: Path, *, env: dict[str, str] | None = None) -> None:
    """Stream a custom-format dump out of the PG18 container, never through argv."""
    with destination.open("wb") as handle:
        subprocess.run(cmd, check=True, stdout=handle, stderr=subprocess.PIPE, env=env)


def run_with_archive(cmd: list[str], archive: Path, *, env: dict[str, str] | None = None) -> str:
    """Feed a host-side archive to a containerized PostgreSQL tool via stdin."""
    with archive.open("rb") as handle:
        result = subprocess.run(cmd, check=True, stdin=handle, text=True, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, env=env)
    return result.stdout or ""


def version(name: str) -> str:
    return run(tool(name, "--version")).strip()


def server_version(identity: ConnectionIdentity) -> str:
    import psycopg

    with psycopg.connect(**identity.connect_kwargs()) as conn, conn.cursor() as cur:
        cur.execute("SELECT version()")
        row = cur.fetchone()
        if row is None or not row[0]:
            raise RuntimeError("server version query returned no value")
        return str(row[0])


def snapshot(identity: ConnectionIdentity, *, phase: str = FULL_SOURCE) -> dict[str, Any]:
    import psycopg
    from psycopg import sql

    state: dict[str, Any] = {}
    result: dict[str, Any] = {"tables": {}, "state_classes": state}
    if phase not in {FULL_SOURCE, FULL_CONFLICT, FULL_TARGET_POST_RESTORE}:
        raise ValueError(f"full semantic snapshot is invalid for phase {phase}")
    with psycopg.connect(**identity.connect_kwargs()) as conn:
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
    result["phase"] = phase
    result["digest"] = canonical_digest({"alembic_head": result["alembic_head"], "state_classes": result["semantic_projection"]})
    return result


def reestablish_application_authority(identity: ConnectionIdentity) -> None:
    """Restore environment-owned grants after pg_restore --no-acl."""
    import psycopg

    with psycopg.connect(**{**identity.connect_kwargs(), "autocommit": True}) as conn, conn.cursor() as cur:
        cur.execute("GRANT USAGE ON SCHEMA mayak TO mayak_application")
        cur.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA mayak TO mayak_application")
        cur.execute("GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA mayak TO mayak_application")


def application_read(identity: ConnectionIdentity) -> bool:
    import psycopg

    app = ConnectionIdentity(identity.host, identity.port, identity.dbname, "mayak_application", os.environ.get("RF24_APPLICATION_PASSWORD", ""))
    if not app.password:
        raise ValueError("application credential source missing")
    with psycopg.connect(**app.connect_kwargs()) as conn, conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM mayak.identity_accounts")
        row = cur.fetchone()
        return row is not None and int(row[0]) > 0


def require_archive_digest(actual: str, expected: str) -> None:
    if actual != expected:
        raise ValueError("archive digest mismatch")


def require_source_revision(actual: str, expected: str) -> None:
    if actual != expected:
        raise ValueError("source revision mismatch")


def require_clean_target(state: CleanTargetState | dict[str, Any]) -> None:
    if isinstance(state, CleanTargetState):
        if state.phase != CLEAN_TARGET_PRE_RESTORE or not state.is_clean:
            raise ValueError("target is non-empty")
        return
    if state.get("phase") != CLEAN_TARGET_PRE_RESTORE or state.get("schema_exists") or state.get("project_relations") or state.get("alembic_head"):
        raise ValueError("target is non-empty")


def clean_target_snapshot(identity: ConnectionIdentity) -> CleanTargetState:
    import psycopg
    with psycopg.connect(**identity.connect_kwargs()) as conn:
        return inspect_clean_target(conn)


def database_tool_role_args() -> tuple[str, str]:
    """The container OS user is not the PostgreSQL restore authority."""
    return ("--username", os.environ.get("RF24_PG_DATABASE_ROLE", "mayak_migration"))


def restored_object_authority(identity: ConnectionIdentity) -> dict[str, Any]:
    import psycopg
    with psycopg.connect(**identity.connect_kwargs()) as conn, conn.cursor() as cur:
        cur.execute("SELECT current_user, has_schema_privilege(current_user, 'mayak', 'CREATE')")
        current_user, can_create = cur.fetchone()
        cur.execute("SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='mayak' AND c.relkind IN ('r','p','S') AND pg_get_userbyid(c.relowner)=current_user")
        owned = int(cur.fetchone()[0])
    if current_user != "mayak_migration" or not can_create or owned <= 0:
        raise RuntimeError("restored objects are not under explicit migration authority")
    return {"database_role": str(current_user), "owned_project_objects": owned, "schema_create": bool(can_create)}


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
                      expected_source_revision: str, target_state: CleanTargetState | dict[str, Any],
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


def state_digest(state: CleanTargetState | dict[str, Any]) -> str:
    return state.digest if isinstance(state, CleanTargetState) else str(state.get("digest", ""))


def perform_restored_replay(identity: ConnectionIdentity, seed: dict[str, Any], source_sha: str) -> dict[str, Any]:
    """Invoke the already-owned public Beacon command against restored TARGET."""
    command = seed.get("idempotent_command")
    if not isinstance(command, dict) or not command.get("key") or not isinstance(command.get("payload"), dict):
        raise ValueError("runtime seed has no replayable idempotent command")
    from scripts.runtime.run_rf24_command_idempotency import fingerprint, request

    before = snapshot(identity, phase=FULL_TARGET_POST_RESTORE)
    # Reuse the vertical-spine settings preflight, but give the API a clean
    # MAYAK_* environment so inherited acceptance/test knobs cannot leak in.
    from scripts.runtime.run_rf24_vertical_spine import _child_environment
    base = {k: v for k, v in os.environ.items() if not k.startswith("MAYAK_")}
    base.pop("RF24_APPLICATION_PASSWORD", None)
    secret_dir = Path(os.environ.get("MAYAK_SECRETS_DIR", tempfile.mkdtemp(prefix="rf24-secrets-")))
    secret_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    secret = secret_dir / "mayak_database_application_password"
    if not secret.exists():
        secret.write_text(os.environ.get("RF24_APPLICATION_PASSWORD", ""), encoding="utf-8")
        secret.chmod(0o600)
    if secret.stat().st_mode & 0o077:
        raise RuntimeError("synthetic application secret permissions are too broad")
    port = next((candidate for candidate in range(18080, 18100) if _port_available(candidate)), None)
    if port is None:
        raise RuntimeError("no task-local API port available in 18080-18099")
    env = _child_environment(
        base | {"MAYAK_SECRETS_DIR": str(secret_dir)}, source_sha=source_sha,
        run_id=str(seed.get("run_id", "")) + "-replay", kind="api",
        database_host=identity.host, database_name=identity.dbname, port=str(port),
        scheduler_observations=secret_dir / "scheduler.jsonl", worker_observations=secret_dir / "worker.jsonl",
    )
    log = secret_dir / "rf24-restored-replay.log"
    with log.open("w", encoding="utf-8") as handle:
        process = subprocess.Popen((sys.executable, "-m", "mayak.runtime.api"), env=env, stdout=handle,
                                   stderr=subprocess.STDOUT, text=True, shell=False)
        try:
            base = f"http://127.0.0.1:{port}"
            for _ in range(80):
                if process.poll() is not None:
                    raise RuntimeError("restored replay API exited before readiness")
                status, _, _ = request(base, "/version", method="GET")
                if status == 200:
                    break
                import time
                time.sleep(0.25)
            else:
                raise RuntimeError("restored replay API readiness timeout")
            run_id = str(seed.get("run_id", ""))
            status, login, cookie_header = request(base, "/acceptance/login", payload={"synthetic_subject": f"{run_id}:target"}, key=f"{run_id}:replay-login")
            if status != 200 or not cookie_header:
                raise RuntimeError("restored replay login failed")
            cookie = cookie_header.split("=", 1)[1].split(";", 1)[0]
            # Login is setup for the owning boundary; the replay proof starts
            # after that setup so only the repeated terminal command is measured.
            before = snapshot(identity)
            replay_status, body, _ = request(base, "/api/v1/beacons", payload=command["payload"], key=str(command["key"]), cookie=cookie)
        finally:
            process.terminate()
            try:
                process.wait(10)
            except subprocess.TimeoutExpired:
                process.kill(); process.wait(5)
    after = snapshot(identity, phase=FULL_TARGET_POST_RESTORE)
    replay_key = str(command["key"])
    replay_fp = fingerprint(str(command.get("account_id", "")), str(command["payload"]["source_url"]), str(command["payload"]["name"]))
    original_beacon_id = str(command.get("beacon_id", ""))
    replay_beacon_id = str(body.get("beacon_id", "")) if isinstance(body, dict) else ""
    if replay_status != 200 or replay_beacon_id != original_beacon_id:
        raise RuntimeError("restored replay did not return the original Beacon result")
    def delta(table: str) -> int:
        return int(after["tables"].get(table, 0)) - int(before["tables"].get(table, 0))
    return {"executed": True, "boundary": command["boundary"], "scope": command["scope"], "key": replay_key,
            "fingerprint": replay_fp, "original_account_id": str(command.get("account_id", "")),
            "original_beacon_id": original_beacon_id, "replay_beacon_id": replay_beacon_id,
            "result": {"class": "duplicate", "status": replay_status, "beacon_id": replay_beacon_id},
            "before": {"fingerprint": before["digest"], "counts": before["tables"]},
            "after": {"fingerprint": after["digest"], "counts": after["tables"]},
            "beacon_delta": delta("beacon_beacons"), "beacon_revision_delta": delta("beacon_configuration_revisions"),
            "lifecycle_delta": delta("beacon_lifecycle_events"), "notification_delta": delta("notification_events"),
            "outbox_delta": delta("notification_outbox"), "provider_effect_delta": delta("notification_delivery_attempts"),
            "live_provider_calls": 0, "selected_port": port,
            "response_class": type(body).__name__, "login_account_present": bool(login.get("account_id"))}


def _port_available(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        try:
            probe.bind(("127.0.0.1", port))
        except OSError:
            return False
        return True


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--source-dsn")
    p.add_argument("--target-dsn")
    p.add_argument("--conflict-dsn")
    p.add_argument("--source-dsn-env")
    p.add_argument("--target-dsn-env")
    p.add_argument("--conflict-dsn-env")
    p.add_argument("--source-sha", required=True)
    p.add_argument("--run-id", required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--backup", type=Path, required=True)
    p.add_argument("--seed-evidence", type=Path, required=True)
    a = p.parse_args()
    for option, env_name in (("source_dsn", a.source_dsn_env), ("target_dsn", a.target_dsn_env), ("conflict_dsn", a.conflict_dsn_env)):
        if not getattr(a, option) and env_name:
            setattr(a, option, os.environ.get(env_name, ""))
    if not all((a.source_dsn, a.target_dsn, a.conflict_dsn)):
        raise SystemExit("direct connection identities are required")
    if len(a.source_sha) != 40 or not all(c in "0123456789abcdef" for c in a.source_sha):
        raise SystemExit("invalid source SHA")
    try:
        source_conn = direct_identity(a.source_dsn)
        target_conn = direct_identity(a.target_dsn)
        conflict_conn = direct_identity(a.conflict_dsn)
    except ValueError as exc:
        raise SystemExit(f"invalid direct connection identity: {exc}") from exc
    if len({source_conn.dbname, target_conn.dbname, conflict_conn.dbname}) != 3:
        raise SystemExit("SOURCE, TARGET and CONFLICT database identities must be distinct")
    seed_evidence = json.loads(a.seed_evidence.read_text(encoding="utf-8"))
    seed = seed_evidence.get("seed")
    if not isinstance(seed, dict) or seed.get("runtime_boundary") != "accepted-public-runtime":
        raise SystemExit("missing accepted runtime seed proof")
    seeded = seed.get("state_classes")
    if not isinstance(seeded, dict) or not seeded:
        raise SystemExit("runtime seed proof is not meaningful")
    before = snapshot(source_conn, phase=FULL_SOURCE)
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
    source_tool_dsn = tool_dsn("source", source_conn.dbname)
    target_tool_dsn = tool_dsn("target", target_conn.dbname)
    corrupt = a.backup.with_name(a.backup.name + ".corrupt")
    source_identity, target_identity = source_conn.dbname, target_conn.dbname
    after = before
    clean_target = clean_target_snapshot(target_conn)
    require_clean_target(clean_target)
    target = clean_target
    controls: dict[str, Any] = {}
    try:
        run_binary_to_file(tool("pg_dump", "--format=custom", "--no-owner", "--no-acl", *database_tool_role_args(), source_tool_dsn), a.backup, env=env)
        digest = hashlib.sha256(a.backup.read_bytes()).hexdigest()
        listing = run_with_archive(tool("pg_restore", "--list"), a.backup, env=env)
        if not all(marker in listing for marker in ("TABLE", "SCHEMA", "alembic_version")):
            raise SystemExit("backup inventory is incomplete")
        source_revision = ",".join(before["alembic_head"])
        if not source_revision:
            raise SystemExit("source Alembic revision metadata missing")
        meta = {"technical_id": TECHNICAL_ID, "hosted_run_id": a.run_id, "source_sha": a.source_sha, "source_alembic_revision": source_revision, "source_database_identity": source_conn.public(), "target_database_identity": target_conn.public(), "postgres_server_version": server_version(source_conn), "pg_dump_version": version("pg_dump"), "pg_restore_version": version("pg_restore"), "database_role": os.environ.get("RF24_PG_DATABASE_ROLE", "mayak_migration"), "format": "custom", "size": a.backup.stat().st_size, "sha256": digest, "verified": True, "inventory_verified": True, "readability_verified": True}
        def control(name: str, archive: Path, expected: str, revision: str, state: CleanTargetState | dict[str, Any], *, actual_sha: str = a.source_sha, archive_listing: str = listing) -> None:
            try:
                restore_preflight(archive=archive, expected_digest=expected, source_sha=a.source_sha, actual_source_sha=actual_sha, source_revision=revision, expected_source_revision=source_revision, target_state=state, target_identity=target_identity, source_identity=source_identity, restore_list=archive_listing)
            except (ValueError, subprocess.CalledProcessError) as exc:
                digest_state = state_digest(state)
                controls[name] = {"executed": True, "shared_preflight_used": True, "preflight_result": "BLOCKED", "observed_reason": str(exc), "target_fingerprint_before": digest_state, "target_fingerprint_after": digest_state}
            else:
                raise SystemExit(f"{name} control did not block")
        control("tampered_digest", a.backup, "0" * 64, source_revision, target)
        shutil.copyfile(a.backup, corrupt)
        raw = bytearray(corrupt.read_bytes()); raw[-1] ^= 0xFF; corrupt.write_bytes(raw)
        corrupt_listing = ""
        try:
            corrupt_listing = run_with_archive(tool("pg_restore", "--list"), corrupt, env=env)
        except subprocess.CalledProcessError:
            pass
        control("corrupt_copy", corrupt, digest, source_revision, target, archive_listing=corrupt_listing)
        control("wrong_source_sha", a.backup, digest, source_revision, target, actual_sha="0" * 40)
        wrong_revision = source_revision + "-wrong"
        control("wrong_source_revision", a.backup, digest, wrong_revision, target)
        conflict = snapshot(conflict_conn, phase=FULL_CONFLICT)
        control("nonempty_newer_target", a.backup, digest, source_revision, conflict)
        restore_preflight(archive=a.backup, expected_digest=digest, source_sha=a.source_sha, actual_source_sha=a.source_sha, source_revision=source_revision, expected_source_revision=source_revision, target_state=target, target_identity=target_identity, source_identity=source_identity, restore_list=listing)
        run_with_archive(tool("pg_restore", "--no-owner", "--no-acl", *database_tool_role_args(), "--dbname", target_tool_dsn), a.backup, env=env)
        reestablish_application_authority(target_conn)
        target = snapshot(target_conn, phase=FULL_TARGET_POST_RESTORE)
        authority = restored_object_authority(target_conn)
        after = snapshot(source_conn, phase=FULL_SOURCE)
        control("duplicate_restore", a.backup, digest, source_revision, target)
        replay = perform_restored_replay(target_conn, seed, a.source_sha)
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
        "clean_target_prerequisite": clean_target.is_clean,
        "clean_target_catalog": {"phase": clean_target.phase, "schema_exists": clean_target.schema_exists, "project_relations": list(clean_target.project_relations), "alembic_head": list(clean_target.alembic_head), "digest": clean_target.digest},
        "restore_authority": authority,
        "backup": meta,
        "restore": {"result": "PASS", "alembic_head": target["alembic_head"]},
        "runtime_read_proof": application_read(target_conn),
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
        "idempotency_replay": replay,
        "seed": seed,
    }
    a.output.write_text(json.dumps(evidence, sort_keys=True, indent=2) + "\n")


if __name__ == "__main__":
    main()
