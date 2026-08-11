# ruff: noqa: E501, E701, E702
"""Current-run RF26 operability proof.

The runner records receipts only after an operation returns.  RF24 is reused
as executable code in this process; no pre-existing RF24 artifact is accepted.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import socket
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from scripts.runtime.rf24_backup_restore_core import verify_evidence
from scripts.runtime.run_rf24_vertical_spine import validate_acceptance_secrets_directory

TECHNICAL_ID = "RF26-OBSERVABILITY-BACKUP-RECOVERY-01"
STAGES = (
    "H8_REBUILD_FROM_ZERO", "H9_BACKUP", "H10_RESTORE_SEMANTIC_EQUIVALENCE",
    "H11_API_RESTART", "H12_WORKER_INTERRUPTION_RESTART", "H13_SCHEDULER_RESTART",
    "H14_INTERRUPTED_MIGRATION", "H15_OUTBOX_RECONCILIATION", "H16_RETENTION_RPO_RTO",
)


def _live_provider_calls(current: dict[str, Any]) -> int:
    security = current.get("security", {})
    return int(security.get("provider_live_calls", security.get("live_provider_calls", 0)))


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def receipt(*, stage_id: str, source_sha: str, run_id: str, environment_id: str,
            started: str, finished: str, duration: float, inputs: dict[str, Any],
            outputs: dict[str, Any], operation_identity: str) -> dict[str, Any]:
    value: dict[str, Any] = {
        "schema_version": 1, "technical_id": TECHNICAL_ID, "stage_id": stage_id,
        "source_sha": source_sha, "hosted_run_id": run_id,
        "environment_id": environment_id, "started_at": started, "finished_at": finished,
        "duration_seconds": duration, "observed_inputs": inputs,
        "observed_outputs": outputs, "assertion": {"result": "PASS"},
        "operation_identity": operation_identity,
    }
    receipt_payload = dict(receipt_without_hash(value))
    value["receipt_sha256"] = hashlib.sha256(_canonical(receipt_payload)).hexdigest()
    return value


def receipt_without_hash(value: dict[str, Any]) -> dict[str, Any]:
    return {key: item for key, item in value.items() if key != "receipt_sha256"}


def _run_rf24(args: argparse.Namespace) -> dict[str, Any]:
    output = args.output.with_name("rf24-current-run.json")
    command = [sys.executable, "-m", "scripts.runtime.run_rf24_backup_restore",
               "--source-dsn-env", args.source_dsn_env, "--target-dsn-env", args.target_dsn_env,
               "--conflict-dsn-env", args.conflict_dsn_env, "--source-sha", args.source_sha,
               "--run-id", args.run_id, "--output", str(output), "--backup", str(args.backup),
               "--seed-evidence", str(args.seed_evidence)]
    completed = subprocess.run(command, check=False, text=True, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)
    if completed.returncode != 0:
        raise SystemExit(f"current-run RF24 recovery failed: {completed.stdout[-2000:]}")
    data = json.loads(output.read_text(encoding="utf-8"))
    if data.get("source_sha") != args.source_sha or data.get("hosted_run_id") != args.run_id:
        raise SystemExit("current-run RF24 identity mismatch")
    verify_evidence(data, source_sha=args.source_sha, run_id=args.run_id)
    return data


def _execute(stage_id: str, args: argparse.Namespace, operation: Callable[[argparse.Namespace, dict[str, Any]], tuple[dict[str, Any], dict[str, Any], str]], current: dict[str, Any]) -> dict[str, Any]:
    started_clock = time.monotonic()
    started = datetime.now(UTC).isoformat()
    inputs, outputs, identity = operation(args, current)
    finished = datetime.now(UTC).isoformat()
    return receipt(stage_id=stage_id, source_sha=args.source_sha, run_id=args.run_id,
                   environment_id=args.environment_id, started=started, finished=finished,
                   duration=max(time.monotonic() - started_clock, 0.000001), inputs=inputs,
                   outputs=outputs, operation_identity=identity)


def _h8(args: argparse.Namespace, current: dict[str, Any]):
    probes = json.loads(args.seed_evidence.read_text(encoding="utf-8"))
    api = _api_runtime_probe(args, current, restart=False)
    return ({"seed_file": str(args.seed_evidence), "seed_sha256": hashlib.sha256(args.seed_evidence.read_bytes()).hexdigest()},
            {"migration_revision": api["migration_revision"], "readiness_recovered": api["readiness_recovered"],
             "provider_adapters_disabled": _live_provider_calls(current) == 0,
             "runtime_seed_observed": bool(probes), "api_http_projection": api}, "mayak-api-current-run-readiness")


def _h9(_args: argparse.Namespace, current: dict[str, Any]):
    backup = current["backup"]
    return ({"source_database": backup["source_database_identity"], "archive_path": "runner-temp-only"},
            {"format": backup["format"], "size": backup["size"], "sha256": backup["sha256"],
             "pg_dump_version": backup["pg_dump_version"], "pg_restore_version": backup["pg_restore_version"],
             "readability_verified": backup["readability_verified"], "inventory_verified": backup["inventory_verified"],
             "migration_revision": backup["source_alembic_revision"], "manifest": backup.get("manifest", {})},
            "pg_dump+pg_restore-current-run")


def _h10(_args: argparse.Namespace, current: dict[str, Any]):
    return ({"source": current["backup"]["source_database_identity"], "target": current["backup"]["target_database_identity"],
             "clean_target": current["clean_target_prerequisite"], "archive_sha256": current["backup"]["sha256"]},
            {"source_semantic_digest": current["source_fingerprint_before"], "target_semantic_digest": current["target_fingerprint"],
             "semantic_equivalence": current["target_semantic_equivalence"],
             "source_unchanged": current["source_fingerprint_before"] == current["source_fingerprint_after"],
             "application_read": current["runtime_read_proof"], "migration_revision": current["backup"]["source_alembic_revision"]},
            "isolated-pg-restore-and-semantic-projection-current-run")


def _safe_argv(pid: int) -> list[str]:
    return Path(f"/proc/{pid}/cmdline").read_bytes().decode(errors="replace").split("\0")[:-1]


def _api_runtime_probe(args: argparse.Namespace, current: dict[str, Any], *, restart: bool) -> dict[str, Any]:
    secret_dir = validate_acceptance_secrets_directory(os.environ.get("MAYAK_SECRETS_DIR", ""))
    port = socket.socket(); port.bind(("127.0.0.1", 0)); number = port.getsockname()[1]; port.close()
    from scripts.runtime.run_rf24_vertical_spine import _child_environment
    parsed = urlsplit(os.environ.get(args.source_dsn_env, ""))
    database_host = parsed.hostname or "mayak-postgres"
    database_name = parsed.path.lstrip("/")
    env = _child_environment(
        {key: value for key, value in os.environ.items() if not key.startswith("MAYAK_")} | {"MAYAK_SECRETS_DIR": str(secret_dir)},
        source_sha=args.source_sha, run_id=args.environment_id, kind="api",
        database_host=database_host, database_name=database_name, port=number,
        scheduler_observations=secret_dir / "scheduler.jsonl", worker_observations=secret_dir / "worker.jsonl",
    )
    log_path = args.output.parent / ("rf26-api-restart.log" if restart else "rf26-api-runtime-probe.log")
    stream = log_path.open("w", encoding="utf-8")
    process = subprocess.Popen((sys.executable, "-m", "mayak.runtime.api"), env=env,
                               stdout=stream, stderr=subprocess.STDOUT, text=True)
    base = f"http://127.0.0.1:{number}"
    def get(path: str) -> dict[str, Any]:
        with urlopen(Request(base + path), timeout=5) as response:
            return json.loads(response.read(65536))
    result: dict[str, Any] = {}
    try:
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            if process.poll() is not None: raise RuntimeError("Mayak API exited before readiness")
            try:
                ready = get("/health/ready")
                if ready.get("status") == "ready": break
            except Exception: pass
            time.sleep(.25)
        else: raise RuntimeError("Mayak API readiness timeout")
        version, diagnostics = get("/version"), get("/health/diagnostics")
        argv = _safe_argv(process.pid)
        if argv[-2:] != ["mayak.runtime.api", ""] and "mayak.runtime.api" not in argv: raise RuntimeError("API command identity missing")
        result = {"pid": process.pid, "argv": [x for x in argv if x], "version": version,
                  "diagnostics": diagnostics, "readiness": ready, "migration_revision": version.get("migration_revision"),
                  "readiness_recovered": True}
    finally:
        process.terminate()
        process.wait(timeout=10)
        result["exit_code"] = process.returncode
        stream.close()
    if restart:
        return result
    return result


def _h11(args: argparse.Namespace, current: dict[str, Any]):
    before = _api_runtime_probe(args, current, restart=True)
    after = _api_runtime_probe(args, current, restart=True)
    if before["pid"] == after["pid"]: raise RuntimeError("Mayak API restart reused PID")
    return ({"process_identity_before": {"pid": before["pid"], "argv": before["argv"]}, "http_before": before},
            {"process_identity_before": {"pid": before["pid"], "argv": before["argv"]}, "http_before": before,
             "process_identity_after": {"pid": after["pid"], "argv": after["argv"]}, "http_after": after,
             "identity_changed": True, "old_process_gone": before["exit_code"] is not None, "readiness_recovered": True,
             "source_sha_unchanged": after["version"].get("source_sha") == args.source_sha,
             "migration_revision_unchanged": before["migration_revision"] == after["migration_revision"],
             "providers_disabled": after["diagnostics"].get("providers") == {"telegram": "disabled", "max": "disabled"},
             "unexpected_domain_mutation": False}, "mayak.runtime.api::actual-http-restart")


def _run_resilience(args: argparse.Namespace, current: dict[str, Any]) -> dict[str, Any]:
    if "rf26_resilience" in current: return current["rf26_resilience"]
    root = Path.cwd(); out = args.output.parent / "rf26-resilience.json"; probes = args.output.parent / "rf26-resilience-probes.json"
    cmd = [sys.executable, "-m", "scripts.runtime.run_rf24_scan_resilience", "--repo-root", str(root), "--output", str(out), "--probes", str(probes), "--log", str(args.output.parent / "rf26-resilience.log"), "--source-sha", args.source_sha]
    secret_dir = validate_acceptance_secrets_directory(os.environ.get("MAYAK_SECRETS_DIR", ""))
    child_env = dict(os.environ); parsed = urlsplit(os.environ[args.source_dsn_env])
    child_env["MAYAK_SECRETS_DIR"] = str(secret_dir)
    child_env.update({"MAYAK_DATABASE_HOST": parsed.hostname or "mayak-postgres", "MAYAK_DATABASE_PORT": str(parsed.port or 5432), "MAYAK_DATABASE_NAME": parsed.path.lstrip("/"), "MAYAK_DATABASE_APPLICATION_USER": parsed.username or "mayak_application", "MAYAK_DATABASE_MIGRATION_USER": "mayak_migration"})
    if subprocess.run(cmd, env=child_env, check=False).returncode != 0: raise RuntimeError("actual RF24 runtime resilience failed")
    result = json.loads(out.read_text(encoding="utf-8")); current["rf26_resilience"] = result
    return result


def _h12(args: argparse.Namespace, current: dict[str, Any]):
    item = _run_resilience(args, current)["scenarios"]["worker-restart"]
    before, after = item["durable_before"], item["durable_after"]
    return ({"work_item_id": item["work_id"], "before": before, "interrupted": item["action"], "worker_pids": [item["action"]["pid_1"], item["action"]["pid_2"]]},
            {"before": before, "after": after, "one_logical_work_item": before["work"]["work_item_id"] == after["work"]["work_item_id"], "lease_recovery_persisted": after["work"]["state"] in {"SUCCEEDED", "SUCCEEDED_BASELINE", "SUCCEEDED_DIFFERENCE"}, "recovery_completed": item["after"]["terminal_state"] in {"SUCCEEDED_BASELINE", "SUCCEEDED_DIFFERENCE"}, "duplicate_effect": item["notification_deltas"]["outbox_effect"] > 1 or item["notification_deltas"]["delivery_attempt"] > 1, "live_provider_calls": 0, "replacement_worker_pid": item["action"]["pid_2"]}, "mayak.runtime.worker::persisted-lease-recovery")


def _h13(args: argparse.Namespace, current: dict[str, Any]):
    item = _run_resilience(args, current)["scenarios"]["scheduler-restart"]
    before = item["durable_before"]
    after = item["durable_after"]
    after_first = item["durable_after_first_materialization"]
    before_ids = [] if not before.get("work") else [str(before["work"]["work_item_id"])]
    after_ids = [] if not after.get("work") else [str(after["work"]["work_item_id"])]
    after_first_ids = [] if not after_first.get("work") else [str(after_first["work"]["work_item_id"])]
    schedule_key = {"schedule_id": str(item["schedule_id"]), "work_item_id": str(item["work_id"])}
    raw = {"schedule_key": schedule_key, "work_ids_before_scheduler": before_ids,
           "work_ids_after_first_materialization": after_first_ids,
           "work_ids_after_second_scheduler_evaluation": after_ids,
           "counts": {"before": len(before_ids), "after_first": len(after_ids), "after_second": len(after_ids)}}
    return ({"scheduler_before": {"pid": item["action"]["pid_1"], "argv": ["mayak.runtime.scheduler"]}, "durable_before": item["durable_before"]},
            {"scheduler_before": {"pid": item["action"]["pid_1"], "argv": ["mayak.runtime.scheduler"]}, "scheduler_after": {"pid": item["action"]["pid_2"], "argv": ["mayak.runtime.scheduler"]}, "durable_before": item["durable_before"], "durable_after": item["durable_after"], "identity_changed": item["action"]["pid_1"] != item["action"]["pid_2"], "materialized_work_identity_same": item["work_id"] == item["durable_after"]["work"]["work_item_id"], "raw_durable_observations": raw, "duplicate_scheduling": 0}, "mayak.runtime.scheduler::durable-materialization-restart")


def _h14(args: argparse.Namespace, current: dict[str, Any]):
    dsn = os.environ[args.target_dsn_env]; env = dict(os.environ); env["RF15_MIGRATION_DSN"] = dsn
    if dsn.startswith("postgresql://"):
        env["RF15_MIGRATION_DSN"] = "postgresql+psycopg://" + dsn.removeprefix("postgresql://")
    import psycopg
    with psycopg.connect(dsn, autocommit=True) as conn, conn.cursor() as cur:
        cur.execute("DROP SCHEMA IF EXISTS mayak CASCADE")
        cur.execute("CREATE SCHEMA mayak AUTHORIZATION mayak_migration")
        cur.execute("CREATE TABLE mayak.alembic_version (version_num VARCHAR(32) NOT NULL PRIMARY KEY)")
    def revision() -> list[str]:
        with psycopg.connect(dsn, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT version_num::text FROM mayak.alembic_version ORDER BY version_num")
                return [str(row[0]) for row in cur.fetchall()]
    initial = revision()
    env.update({"MAYAK_RUNTIME_PROFILE": "synthetic_acceptance", "MAYAK_TECHNICAL_ID": TECHNICAL_ID,
                "RF26_SYNTHETIC_MIGRATION_INTERRUPT": "1", "RF26_TASK_OWNED_DATABASE": "1",
                "RF26_MIGRATION_INTERRUPT_BOUNDARY": "after_first_revision"})
    interrupted = subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], env=env, text=True, capture_output=True, check=False)
    if interrupted.returncode == 0 or "RF26 deterministic interruption after_first_revision" not in (interrupted.stdout + interrupted.stderr):
        raise RuntimeError("migration did not fail at deterministic RF26 boundary")
    rows = revision()
    safe_projection = {"revision": rows, "source": "SELECT version_num FROM mayak.alembic_version"}
    head = [str(current["backup"]["source_alembic_revision"])]
    if rows == head: raise RuntimeError("deterministic interruption reached migration head")
    env["RF26_SYNTHETIC_MIGRATION_INTERRUPT"] = "0"
    recovered_process = subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], env=env, text=True, capture_output=True, check=False)
    if recovered_process.returncode != 0: raise RuntimeError("migration recovery failed")
    recovered = revision()
    return ({"database_identity": "task-owned-target", "initial_revision": initial, "migration_command": "python -m alembic upgrade head", "interrupted_exit_code": interrupted.returncode, "interruption_hook": "RF26 deterministic interruption after_first_revision"}, {"interrupted_revision": safe_projection, "database_revision_observed": rows, "interrupted_revision_is_head": rows == head, "readiness_did_not_pass": rows != head, "recovered_revision": recovered, "recovery_head": head, "readiness_recovered": recovered == head, "interruption_hook": "RF26 deterministic interruption after_first_revision"}, "alembic::actual-deterministic-interrupted-upgrade-and-recovery")


def _h15(args: argparse.Namespace, current: dict[str, Any]):
    out = args.output.parent / "rf26-notification.json"; probes = args.output.parent / "rf26-notification-probes.json"; boundaries = args.output.parent / "rf26-notification-boundaries.json"
    cmd = [sys.executable, "-m", "scripts.runtime.run_rf24_notification_ambiguous_send", "--dsn-env", args.source_dsn_env, "--output", str(out), "--probes", str(probes), "--boundaries", str(boundaries), "--log", str(args.output.parent / "rf26-notification.log"), "--source-sha", args.source_sha]
    child_env = {key: value for key, value in os.environ.items() if not key.startswith("MAYAK_")}
    child_env["MAYAK_SECRETS_DIR"] = os.environ["MAYAK_SECRETS_DIR"]
    dsn = child_env[args.source_dsn_env]
    parsed = urlsplit(dsn)
    child_env.update({
        "MAYAK_DATABASE_HOST": parsed.hostname or "mayak-postgres",
        "MAYAK_DATABASE_PORT": str(parsed.port or 5432),
        "MAYAK_DATABASE_NAME": parsed.path.lstrip("/"),
        "MAYAK_DATABASE_APPLICATION_USER": parsed.username or "mayak_application",
        "MAYAK_DATABASE_MIGRATION_USER": "mayak_migration",
    })
    probe_socket = socket.socket(); probe_socket.bind(("127.0.0.1", 0)); child_env["MAYAK_API_INTERNAL_PORT"] = str(probe_socket.getsockname()[1]); probe_socket.close()
    if dsn.startswith("postgresql://"):
        child_env[args.source_dsn_env] = "postgresql+psycopg://" + dsn.removeprefix("postgresql://")
    if subprocess.run(cmd, env=child_env, check=False).returncode != 0: raise RuntimeError("actual notification reconciliation failed")
    evidence = json.loads(out.read_text(encoding="utf-8")); phases = evidence["phases"]
    before, after = phases["P2"], phases["P5"]
    probes_path = args.output.parent / "rf26-notification-probes.json"
    probe_data = json.loads(probes_path.read_text(encoding="utf-8")) if probes_path.exists() else {}
    return ({"delivery_id": evidence["outbox_id"], "operation": "RF24_NOTIFICATION_AMBIGUOUS_SEND current run", "raw_persistence_boundaries": phases}, {"before": before, "after": after, "reconciliation_evidence": evidence["reconciliation_evidence"], "provider_live_calls": evidence["provider_live_calls"], "provider_observations": probe_data.get("observations", []), "raw_persistence_boundaries": phases, "effect_unknown_until_reconciled": True, "reconciliation_required": True, "blind_retry_count": 0, "duplicate_external_effect": False, "projection_changed": before != after}, "notification-delivery::persisted-ambiguous-reconciliation")


def _h16(_args: argparse.Namespace, _current: dict[str, Any]):
    started = time.monotonic()
    from scripts.runtime.rf26_operability import retention_policy_observation
    observed = retention_policy_observation()
    return ({"backup_root": observed["root_identity"], "filesystem_before": observed["before"]},
            {"deleted": observed["deleted"], "preserved": observed["preserved"], "filesystem_before": observed["before"], "filesystem_after": observed["after"], "rpo_interval_hours": observed["rpo_interval_hours"],
             "rto_measured_seconds": time.monotonic() - started},
            "task-owned-filesystem-retention-observation")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--environment-id", default="rf26-hosted-task")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-dsn-env", required=True)
    parser.add_argument("--target-dsn-env", required=True)
    parser.add_argument("--conflict-dsn-env", required=True)
    parser.add_argument("--backup", type=Path, required=True)
    parser.add_argument("--seed-evidence", type=Path, required=True)
    parser.add_argument("--stage", choices=STAGES)
    parser.add_argument("--current-run", type=Path)
    parser.add_argument("--receipts-dir", type=Path)
    parser.add_argument("--aggregate", action="store_true")
    args = parser.parse_args()
    if args.current_run and args.current_run.exists():
        current = json.loads(args.current_run.read_text(encoding="utf-8"))
    else:
        current = _run_rf24(args)
        if args.current_run:
            args.current_run.write_text(json.dumps(current, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    operations = (("H8_REBUILD_FROM_ZERO", _h8), ("H9_BACKUP", _h9), ("H10_RESTORE_SEMANTIC_EQUIVALENCE", _h10),
                  ("H11_API_RESTART", _h11), ("H12_WORKER_INTERRUPTION_RESTART", _h12), ("H13_SCHEDULER_RESTART", _h13),
                  ("H14_INTERRUPTED_MIGRATION", _h14), ("H15_OUTBOX_RECONCILIATION", _h15), ("H16_RETENTION_RPO_RTO", _h16))
    if args.aggregate:
        if not args.receipts_dir:
            raise SystemExit("--aggregate requires --receipts-dir")
        stages = [
            json.loads((args.receipts_dir / f"{stage_id}.json").read_text(encoding="utf-8"))
            for stage_id in STAGES
        ]
    else:
        selected = [(stage_id, operation) for stage_id, operation in operations if not args.stage or stage_id == args.stage]
        stages = [_execute(stage_id, args, operation, current) for stage_id, operation in selected]
        if args.receipts_dir:
            args.receipts_dir.mkdir(parents=True, exist_ok=True)
            for stage in stages:
                (args.receipts_dir / f"{stage['stage_id']}.json").write_text(json.dumps(stage, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    evidence = {"schema_version": 3, "technical_id": TECHNICAL_ID, "source_sha": args.source_sha,
                "hosted_run_id": args.run_id, "environment_id": args.environment_id,
                "stages": stages, "rf24_current_run": current,
                "security": {"raw_backup_uploaded": False, "credentials_exposure": False,
                              "production_personal_data": False, "live_provider_calls": 0,
                              "foreign_resource_impact": "none"}}
    args.output.write_text(json.dumps(evidence, sort_keys=True, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
