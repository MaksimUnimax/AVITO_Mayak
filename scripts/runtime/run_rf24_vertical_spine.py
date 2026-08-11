# ruff: noqa: E501
"""Process-driven RF24 acceptance producer with a credential-safe evidence boundary."""
from __future__ import annotations

import argparse
import json
import os
import re
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from collections import deque
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast
from urllib.parse import urlsplit
from uuid import uuid4

from mayak.runtime.settings import RuntimeConfigurationError, compose_runtime_settings

APPLICATION_SECRET_FILENAME = "mayak_database_application_password"


def validate_acceptance_secrets_directory(value: str | Path) -> Path:
    """Validate the one explicit, file-backed synthetic secret boundary."""
    directory = Path(value)
    if not directory.is_absolute():
        raise RuntimeError("acceptance secrets directory must be absolute")
    if directory.is_symlink() or not directory.is_dir():
        raise RuntimeError("acceptance secrets directory must be a real directory")
    if directory.stat().st_mode & 0o077:
        raise RuntimeError("acceptance secrets directory permissions are too broad")
    secret = directory / APPLICATION_SECRET_FILENAME
    if secret.is_symlink() or not secret.is_file():
        raise RuntimeError(f"required acceptance secret missing: {APPLICATION_SECRET_FILENAME}")
    if secret.stat().st_mode & 0o077:
        raise RuntimeError("acceptance application secret permissions are too broad")
    if secret.stat().st_size == 0:
        raise RuntimeError(f"required acceptance secret empty: {APPLICATION_SECRET_FILENAME}")
    return directory


@dataclass(frozen=True, slots=True)
class SafeResponse:
    status: int
    payload: object
    _session_cookie: str | None = None

    def __repr__(self) -> str:
        return f"SafeResponse(status={self.status}, payload=<safe>, session_cookie=<redacted>)"

    def evidence(self) -> dict[str, object]:
        return {"status": self.status, "payload": _safe_payload(self.payload)}


_RF26_TECHNICAL_ID = "RF26-OBSERVABILITY-BACKUP-RECOVERY-01"
_RF26_SCHEMA_VERSION = 1
_RF26_BOUNDARIES = (
    "SEED_A_ENVIRONMENT", "SEED_B_API_PROCESS_START", "SEED_C_WORKER_PROCESS_START",
    "SEED_D_SCHEDULER_PROCESS_START", "SEED_E_API_LIVENESS", "SEED_F_OPERATOR_LOGIN",
    "SEED_G_ADMIN_BOOTSTRAP", "SEED_H_TARGET_LOGIN", "SEED_I_ENTITLEMENT",
    "SEED_J_BEACON_CREATE", "SEED_K_BEACON_CONFIGURATION", "SEED_L_BEACON_ACTIVATION",
    "SEED_M_BASELINE_SCHEDULE", "SEED_N_BASELINE_COMPLETION", "SEED_O_DIFFERENCE_SCHEDULE",
    "SEED_P_DIFFERENCE_COMPLETION", "SEED_Q_NOTIFICATION_READ_MODEL", "SEED_R_WEB_CABINET",
    "SEED_S_ADMIN_DIAGNOSTICS", "SEED_T_PROCESS_PROVENANCE", "SEED_U_DURABLE_STATE_PROOF",
)
_RF26_RUNTIME_PORT_MIN = 18080
_RF26_RUNTIME_PORT_MAX = 18099


class SeedLifecycleReporter:
    """Single diagnostic boundary for the real RF24 producer."""

    def __init__(self, *, source_sha: str, run_id: str) -> None:
        self.source_sha = source_sha
        self.run_id = run_id
        self.completed: list[str] = []
        self.current: dict[str, object] | None = None
        self.trace: deque[dict[str, object]] = deque(maxlen=5)

    def begin(self, boundary: str, *, input: object, derived: object,
              function: str, environment: object, evidence: object) -> None:
        process_kind = environment.get("process_kind") if isinstance(environment, dict) else None
        self.current = {"boundary": boundary, "process_kind": _safe_payload(process_kind), "exit_code": None}
        self.trace.append({
            "input": _safe_payload(input), "derived": _safe_payload(derived),
            "function": function, "environment": _safe_payload(environment),
            "source_runtime_evidence": _safe_payload(evidence),
        })

    def passed(self, evidence: object) -> None:
        if self.current is None:
            return
        boundary = str(self.current["boundary"])
        self.completed.append(boundary)
        self.current = None

    def publish_failure(self, error: BaseException) -> None:
        current = self.current or {"boundary": "SEED_A_ENVIRONMENT", "process_kind": None, "exit_code": None}
        reason = _redact_text(str(error))
        diagnostic = {
            "schema_version": _RF26_SCHEMA_VERSION,
            "technical_id": _RF26_TECHNICAL_ID,
            "source_sha": self.source_sha,
            "run_id": self.run_id,
            "failed_boundary": current["boundary"],
            "completed_boundaries": self.completed[-64:],
            "exception_class": type(error).__name__,
            "redacted_reason": reason[:400],
            "affected_process_kind": current.get("process_kind"),
            "process_exit_code": current.get("exit_code"),
            "five_transition_trace": list(self.trace),
        }
        if isinstance(error, RuntimeConfigurationError):
            diagnostic["reason_code"] = error.reason_code
            diagnostic["canonical_fields"] = list(error.fields)
        encoded = json.dumps(diagnostic, sort_keys=True, separators=(",", ":"))
        print(f"::error title=RF26 runtime seed {diagnostic['failed_boundary']}::{encoded}", flush=True)
        summary = os.environ.get("GITHUB_STEP_SUMMARY")
        if summary:
            with Path(summary).open("a", encoding="utf-8") as stream:
                stream.write("## RF26 runtime seed diagnostic\n\n```json\n")
                stream.write(json.dumps(diagnostic, sort_keys=True, indent=2)[:12000])
                stream.write("\n```\n")
        print(f"RF26 runtime seed diagnostic: {encoded}", flush=True)


def _safe_payload(value: object, *, depth: int = 0) -> object:
    """Bound JSON observations and drop transport/auth metadata by construction."""
    if depth > 5:
        return "bounded"
    if isinstance(value, dict):
        result: dict[str, object] = {}
        for key, item in list(value.items())[:64]:
            normalized = str(key).lower().replace("-", "_")
            if normalized in {
                "set_cookie", "cookie", "authorization", "proxy_authorization",
                "access_token", "refresh_token", "session_token", "password",
            }:
                continue
            result[str(key)[:128]] = _safe_payload(item, depth=depth + 1)
        return result
    if isinstance(value, (list, tuple)):
        return [_safe_payload(item, depth=depth + 1) for item in list(value)[:64]]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value if not isinstance(value, str) or len(value) <= 512 else value[:512]
    return str(value)[:256]


def _port_is_bindable(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        try:
            probe.bind(("127.0.0.1", port))
        except OSError:
            return False
    return True


def select_runtime_api_port(raw: str | None = None) -> int:
    """Select one task-local API port from the finite RF26 acceptance range."""
    supplied = raw if raw is not None else os.environ.get("MAYAK_API_INTERNAL_PORT")
    if supplied is not None:
        try:
            port = int(supplied, 10)
        except (TypeError, ValueError) as error:
            raise ValueError("MAYAK_API_INTERNAL_PORT must be an integer") from error
        if not _RF26_RUNTIME_PORT_MIN <= port <= _RF26_RUNTIME_PORT_MAX:
            raise ValueError("MAYAK_API_INTERNAL_PORT is outside 18080-18099")
        if not _port_is_bindable(port):
            raise OSError(f"MAYAK_API_INTERNAL_PORT {port} is unavailable")
        return port
    for port in range(_RF26_RUNTIME_PORT_MIN, _RF26_RUNTIME_PORT_MAX + 1):
        if _port_is_bindable(port):
            return port
    raise OSError("no bindable RF26 runtime API port in 18080-18099")


def _decode_body(raw: bytes) -> object:
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        text = raw[:2048].decode("utf-8", "replace")
        markers = tuple(sorted(set(re.findall(r"Web Cabinet|Admin|DELIVERED|SUCCEEDED_[A-Z]+", text))))
        references = tuple(sorted(set(re.findall(r"[0-9a-f]{8}-[0-9a-f-]{27,36}", text, re.I))))
        return {"bytes": len(raw), "markers": markers, "opaque_references": references[:32]}


def request(
    url: str, *, method: str = "GET", body: object | None = None,
    session_cookie: str | None = None, idempotency_key: str | None = None,
) -> SafeResponse:
    data = None if body is None else json.dumps(body).encode()
    headers = {"Content-Type": "application/json"}
    if session_cookie is not None:
        headers["Cookie"] = f"mayak_session={session_cookie}"
    if idempotency_key is not None:
        headers["Idempotency-Key"] = idempotency_key
    if method != "GET":
        parsed = urlsplit(url)
        headers["Origin"] = f"{parsed.scheme}://{parsed.netloc}"
    try:
        with urllib.request.urlopen(
            urllib.request.Request(url, data=data, method=method, headers=headers), timeout=20
        ) as response:
            raw_cookie = response.headers.get("set-cookie")
            raw = response.read(32768)
            return SafeResponse(response.status, _decode_body(raw), _cookie_value(raw_cookie))
    except urllib.error.HTTPError as exc:
        return SafeResponse(exc.code, _decode_body(exc.read(32768)))
    except urllib.error.URLError:
        return SafeResponse(0, {"error": "unreachable"})


def _cookie_value(header: str | None) -> str | None:
    if not header:
        return None
    first = header.split(";", 1)[0]
    name, separator, value = first.partition("=")
    if separator and name.strip() == "mayak_session" and value:
        return value
    return None


def _json_payload(payload: object) -> dict[str, Any]:
    return cast(dict[str, Any], payload) if isinstance(payload, dict) else {}


def _db_provenance(beacon_id: str) -> list[dict[str, object]]:
    """Read-only durable cross-check; it is never used as process provenance."""
    try:
        import psycopg
        host = os.environ.get("MAYAK_DATABASE_HOST", "mayak-postgres")
        port = os.environ.get("MAYAK_DATABASE_PORT", "5432")
        user = os.environ.get("MAYAK_DATABASE_APPLICATION_USER", "mayak_application")
        database = os.environ.get("MAYAK_DATABASE_NAME", "mayak")
        secret_dir = Path(os.environ.get("MAYAK_SECRETS_DIR", "/run/secrets"))
        password_path = secret_dir / "mayak_database_application_password"
        password = password_path.read_text(encoding="utf-8").strip() if password_path.exists() else None
        with psycopg.connect(host=host, port=int(port), user=user, dbname=database, password=password) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """SELECT s.id, w.id, w.state, r.id, r.state
                       FROM mayak.scan_schedules s
                       JOIN mayak.scan_work_items w ON w.schedule_id = s.id
                       JOIN mayak.scan_runs r ON r.work_item_id = w.id
                       WHERE s.beacon_id = %s
                       ORDER BY w.created_at, w.id""",
                    (beacon_id,),
                )
                return [
                    {"schedule_id": str(a), "work_item_id": str(b), "work_state": c,
                     "run_id": str(d), "run_state": e}
                    for a, b, c, d, e in cursor.fetchall()
                ]
    except Exception:
        return []


_RF24_BACKUP_RESTORE_TECHNICAL_ID = "RF24-BACKUP-RESTORE-SCENARIO-01"
_RF24_MAX_OBSERVATION_RECORDS = 128


def _read_jsonl(path: Path, *, process_kind: str, run_id: str) -> list[dict[str, Any]]:
    if not path.is_file() or path.is_symlink():
        raise RuntimeError(f"missing {process_kind} observation file")
    rows: list[dict[str, Any]] = []
    lines = path.read_text(encoding="utf-8").splitlines()
    if len(lines) > _RF24_MAX_OBSERVATION_RECORDS:
        raise RuntimeError(f"{process_kind} observation record limit exceeded")
    for line in lines:
        item = json.loads(line)
        if (
            not isinstance(item, dict)
            or item.get("technical_id") != _RF24_BACKUP_RESTORE_TECHNICAL_ID
            or item.get("process_kind") != process_kind
            or item.get("acceptance_run_id") != run_id
        ):
            raise RuntimeError(f"invalid {process_kind} observation identity")
        rows.append(item)
    return rows


def _db_snapshot(account_id: str, beacon_id: str) -> dict[str, object]:
    """Bounded read-only snapshot used to calculate observed acceptance deltas."""
    import psycopg
    host = os.environ.get("MAYAK_DATABASE_HOST", "mayak-postgres")
    port = os.environ.get("MAYAK_DATABASE_PORT", "5432")
    user = os.environ.get("MAYAK_DATABASE_APPLICATION_USER", "mayak_application")
    database = os.environ.get("MAYAK_DATABASE_NAME", "mayak")
    secret_dir = Path(os.environ.get("MAYAK_SECRETS_DIR", "/run/secrets"))
    password_path = secret_dir / "mayak_database_application_password"
    password = password_path.read_text(encoding="utf-8").strip() if password_path.exists() else None
    with psycopg.connect(host=host, port=int(port), user=user, dbname=database, password=password) as conn:
        from scripts.runtime.rf24_backup_restore_core import validate_projection_schema
        validate_projection_schema(conn)
        with conn.cursor() as cursor:
            result: dict[str, object] = {}
            queries = {
                "listing_identities": ("SELECT external_listing_key FROM mayak.scan_beacon_listing_state WHERE beacon_id=%s ORDER BY external_listing_key", (beacon_id,)),
                "scan_new_listing_events": ("SELECT id FROM mayak.notification_events WHERE account_id=%s AND beacon_id=%s AND event_code='NEW_LISTINGS_FOUND' ORDER BY id", (account_id, beacon_id)),
                "notification_events": ("SELECT id, payload->>'source_event_id' FROM mayak.notification_events WHERE account_id=%s AND beacon_id=%s ORDER BY id", (account_id, beacon_id)),
                "outbox_records": ("SELECT id, event_id FROM mayak.notification_outbox WHERE event_id IN (SELECT id FROM mayak.notification_events WHERE account_id=%s AND beacon_id=%s) ORDER BY id", (account_id, beacon_id)),
                "delivery_attempts": ("SELECT a.id, a.outbox_id, a.state, e.provider_code FROM mayak.notification_delivery_attempts a JOIN mayak.notification_outbox o ON o.id=a.outbox_id JOIN mayak.notification_endpoints e ON e.id=o.endpoint_id WHERE o.event_id IN (SELECT id FROM mayak.notification_events WHERE account_id=%s AND beacon_id=%s) ORDER BY a.id", (account_id, beacon_id)),
            }
            for name, (query, params) in queries.items():
                cursor.execute(query, params)
                result[name] = [tuple(str(value) for value in row) for row in cursor.fetchall()]
            return result


def _observed_seed_state(account_id: str, beacon_id: str) -> dict[str, object]:
    """Project only bounded counts/digests of state created by public runtime calls."""
    import psycopg

    host = os.environ.get("MAYAK_DATABASE_HOST", "mayak-postgres")
    port = os.environ.get("MAYAK_DATABASE_PORT", "5432")
    user = os.environ.get("MAYAK_DATABASE_APPLICATION_USER", "mayak_application")
    database = os.environ.get("MAYAK_DATABASE_NAME", "mayak")
    secret_dir = Path(os.environ.get("MAYAK_SECRETS_DIR", "/run/secrets"))
    password_path = secret_dir / "mayak_database_application_password"
    password = password_path.read_text(encoding="utf-8").strip() if password_path.exists() else None
    queries = {
        "account": ("SELECT id::text, state FROM mayak.identity_accounts WHERE id=%s", (account_id,)),
        "entitlement": ("SELECT id::text, state, source_code FROM mayak.entitlement_access_grants WHERE account_id=%s", (account_id,)),
        "beacon": ("SELECT id::text, state, current_revision_no, row_version FROM mayak.beacon_beacons WHERE id=%s AND account_id=%s", (beacon_id, account_id)),
        "beacon_configuration_history": ("SELECT beacon_id::text, revision_no, source_url, accepted_filter::text, created_by_account_id::text, created_at::text FROM mayak.beacon_configuration_revisions WHERE beacon_id=%s ORDER BY revision_no", (beacon_id,)),
        "beacon_history": ("SELECT id::text, beacon_id::text, from_state, to_state, actor_account_id::text, reason, created_at::text, system_actor_class, causation_reference, policy_source_reference FROM mayak.beacon_lifecycle_events WHERE beacon_id=%s ORDER BY created_at, id", (beacon_id,)),
        "scan_listing": ("SELECT external_listing_key, last_seen_at::text FROM mayak.scan_beacon_listing_state WHERE beacon_id=%s ORDER BY external_listing_key", (beacon_id,)),
        "notification_outbox": ("SELECT e.id::text, o.id::text, a.id::text, a.state FROM mayak.notification_events e JOIN mayak.notification_outbox o ON o.event_id=e.id JOIN mayak.notification_delivery_attempts a ON a.outbox_id=o.id WHERE e.account_id=%s AND e.beacon_id=%s ORDER BY e.id", (account_id, beacon_id)),
        "idempotency": ("SELECT scope, idempotency_key, request_fingerprint FROM mayak.platform_idempotency_records ORDER BY id LIMIT 32", ()),
        "audit": ("SELECT action_code, target_type, target_id, correlation_id FROM mayak.platform_audit_entries ORDER BY id LIMIT 32", ()),
    }
    state: dict[str, object] = {}
    with psycopg.connect(host=host, port=int(port), user=user, dbname=database, password=password) as conn:
        from scripts.runtime.rf24_backup_restore_core import validate_projection_schema
        validate_projection_schema(conn)
        with conn.cursor() as cursor:
            for name, (query, params) in queries.items():
                cursor.execute(query, params)
                rows = [[str(value) for value in row] for row in cursor.fetchall()]
                state[name] = {"count": len(rows), "projection_digest": __import__("hashlib").sha256(json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()).hexdigest()}
    return state


def _run_records(scan_payload: object) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    if not isinstance(scan_payload, list):
        return result
    for view in scan_payload:
        if isinstance(view, dict) and isinstance(view.get("recent_runs"), list):
            result.extend(item for item in view["recent_runs"] if isinstance(item, dict))
    return result


def _checkout_head(root: Path) -> str:
    """Read checkout identity with ownership trust scoped to this invocation."""
    repository_root = root.resolve()
    return subprocess.check_output(
        (
            "git",
            "-c",
            f"safe.directory={repository_root}",
            "-C",
            str(repository_root),
            "rev-parse",
            "HEAD",
        ),
        text=True,
        shell=False,
    ).strip()


_SECRET_LOG_PATTERNS = (
    re.compile(r"(?i)(postgres(?:ql)?(?:\+[^:/\s]+)?://[^\s:@/]+:)[^\s@]+(@)"),
    re.compile(r"(?i)(\b(?:authorization|proxy-authorization)\s*[:=]\s*(?:bearer\s+)?)[^\s,]+"),
    re.compile(r"(?i)(\b(?:cookie|set-cookie)\s*[:=]\s*)[^\s]+"),
    re.compile(r"(?i)(\b(?:password|passwd|token|secret|session[_-]?token|access[_-]?token)\s*[:=]\s*)[^\s,]+"),
    re.compile(r"-----BEGIN [A-Z ]+PRIVATE KEY-----.*", re.I),
)


def _sanitized_log_tail(path: Path, *, limit: int = 4096) -> str:
    """Return a bounded diagnostic tail with credential-shaped values redacted."""
    raw = path.read_text(encoding="utf-8", errors="replace")[-limit:]
    sanitized = raw
    for pattern in _SECRET_LOG_PATTERNS:
        sanitized = pattern.sub(lambda match: match.group(1) + "<redacted>" if match.lastindex else "<redacted>", sanitized)
    return sanitized[-limit:]


def _redact_text(value: object) -> str:
    text = str(value).replace("\n", " ")[:800]
    for pattern in _SECRET_LOG_PATTERNS:
        text = pattern.sub(lambda match: match.group(1) + "<redacted>" if match.lastindex else "<redacted>", text)
    return text


def _child_environment(
    base: dict[str, str], *, source_sha: str, run_id: str, kind: str,
    database_host: str, database_name: str, port: int,
    scheduler_observations: Path, worker_observations: Path,
) -> dict[str, str]:
    """Build and prove the exact acceptance environment before subprocess spawn."""
    if "MAYAK_SECRETS_DIR" not in base:
        raise RuntimeError("MAYAK_SECRETS_DIR is required before acceptance process spawn")
    secret_dir = validate_acceptance_secrets_directory(base["MAYAK_SECRETS_DIR"])
    values = {
        "MAYAK_RUNTIME_PROFILE": "synthetic_acceptance",
        "MAYAK_SOURCE_SHA": source_sha,
        "MAYAK_ENVIRONMENT_ID": run_id,
        "MAYAK_SYNTHETIC_SCENARIO_RUN_ID": run_id,
        "MAYAK_LOCK_IDENTITY": "0" * 64,
        "MAYAK_IMAGE_DIGEST": "sha256:" + "0" * 64,
        "MAYAK_PROCESS_KIND": f"mayak-{kind}",
        "MAYAK_DATABASE_HOST": database_host,
        "MAYAK_DATABASE_PORT": "5432",
        "MAYAK_DATABASE_NAME": database_name,
        "MAYAK_DATABASE_APPLICATION_USER": "mayak_application",
        "MAYAK_DATABASE_MIGRATION_USER": "mayak_migration",
        "MAYAK_SECRETS_DIR": str(secret_dir),
        "MAYAK_API_BIND_HOST": "127.0.0.1",
        "MAYAK_API_INTERNAL_PORT": str(port),
        "MAYAK_API_HOST_PORT": "disabled",
        "MAYAK_SYNTHETIC_IDENTITY_ENABLED": "true",
        "MAYAK_IDENTITY_ADMIN_BOOTSTRAP_ENABLED": "true",
        "MAYAK_AVITO_LIVE_ENABLED": "false",
        "MAYAK_TELEGRAM_ENABLED": "false",
        "MAYAK_TELEGRAM_UPDATE_MODE": "disabled",
        "MAYAK_MAX_ENABLED": "false",
        "MAYAK_MAX_UPDATE_MODE": "disabled",
        "MAYAK_YOOKASSA_ENABLED": "false",
        "MAYAK_EGRESS_AGENT_ENABLED": "false",
        "MAYAK_WORKER_POLL_INTERVAL_SECONDS": "1",
        "MAYAK_WORKER_LEASE_SECONDS": "30",
        "MAYAK_SCHEDULER_POLL_INTERVAL_SECONDS": "1",
        "MAYAK_SYNTHETIC_SCENARIO": "usable_listing_page",
        "RF24_SCHEDULER_OBSERVATIONS": str(scheduler_observations),
        "RF24_WORKER_OBSERVATIONS": str(worker_observations),
    }
    if kind in {"worker", "scheduler"}:
        values.update(
            {
                "RF24_ACCEPTANCE_HOOKS_ENABLED": "true",
                "RF24_ACCEPTANCE_TECHNICAL_ID": "RF24-BACKUP-RESTORE-SCENARIO-01",
            }
        )
    settings = compose_runtime_settings(values)
    if (
        settings.build.source_sha != source_sha
        or settings.build.environment_id != run_id
        or settings.database.host != database_host
        or settings.database.name != database_name
        or settings.runtime.process_kind.value != f"mayak-{kind}"
        or settings.api.bind_host != "127.0.0.1"
        or settings.api.internal_port != port
        or any((settings.providers.avito_live_enabled, settings.providers.telegram_enabled, settings.providers.max_enabled, settings.providers.yookassa_enabled, settings.providers.egress_agent_enabled))
    ):
        raise RuntimeError(f"runtime settings preflight failed for mayak-{kind}")
    acceptance_only = {
        "RF24_ACCEPTANCE_HOOKS_ENABLED",
        "RF24_ACCEPTANCE_TECHNICAL_ID",
    }
    inherited = {
        key: value
        for key, value in base.items()
        if not key.startswith("MAYAK_") and key not in acceptance_only
    }
    child_environment = inherited | values
    if not all(isinstance(value, str) for value in child_environment.values()):
        raise RuntimeError("runtime child environment must contain strings only")
    return child_environment


def _startup_failure(kind: str, process: subprocess.Popen[str], log: Path, phase: str) -> RuntimeError:
    return RuntimeError(
        f"{kind} exited during {phase}: exit_code={process.poll()} "
        f"reason=child_process_exit log_tail={_sanitized_log_tail(log)!r}"
    )


def produce(root: Path, output: Path, probes: Path, log: Path, expected_sha: str) -> None:
    actual_sha = _checkout_head(root)
    if actual_sha != expected_sha:
        raise RuntimeError("wrong source SHA")
    run_id = f"rf24-spine-{uuid4()}"
    reporter = SeedLifecycleReporter(source_sha=actual_sha, run_id=run_id)
    reporter.begin(
        "SEED_A_ENVIRONMENT", input={"repo_root": str(root), "expected_sha": expected_sha},
        derived={"actual_sha": actual_sha, "run_id": run_id},
        function="scripts.runtime.run_rf24_vertical_spine:produce",
        environment={"profile": os.environ.get("MAYAK_RUNTIME_PROFILE"), "database_host": os.environ.get("MAYAK_DATABASE_HOST"), "database_name": os.environ.get("MAYAK_DATABASE_NAME")},
        evidence={"checkout_sha_proof": actual_sha == expected_sha},
    )
    try:
        port = select_runtime_api_port()
    except Exception as error:
        reporter.publish_failure(error)
        raise
    reporter.passed({"checkout_sha_proof": True, "selected_api_port": port})
    print(f"RF26 runtime API port selected: {port}", flush=True)
    base = f"http://127.0.0.1:{port}"
    log.parent.mkdir(parents=True, exist_ok=True)
    observation_dir = log.parent.resolve()
    scheduler_observations = observation_dir / f"rf24-{run_id}-scheduler-observations.jsonl"
    worker_observations = observation_dir / f"rf24-{run_id}-worker-observations.jsonl"
    base_env = dict(os.environ)
    database_host = base_env.get("MAYAK_DATABASE_HOST", "mayak-postgres")
    database_name = base_env.get("MAYAK_DATABASE_NAME", "mayak")
    handles: list[tuple[str, subprocess.Popen[str], Path, Any]] = []
    for kind, module in (("api", "mayak.runtime.api"), ("worker", "mayak.runtime.worker"), ("scheduler", "mayak.runtime.scheduler")):
        reporter.begin(
            {"api": "SEED_B_API_PROCESS_START", "worker": "SEED_C_WORKER_PROCESS_START", "scheduler": "SEED_D_SCHEDULER_PROCESS_START"}[kind],
            input={"kind": kind, "module": module, "selected_api_port": port}, derived={"process_kind": f"mayak-{kind}", "selected_api_port": port},
            function=f"subprocess.Popen:{module}", environment={"process_kind": f"mayak-{kind}", "database_host": database_host, "database_name": database_name, "secrets_dir": base_env.get("MAYAK_SECRETS_DIR")},
            evidence={"environment_contract": "canonical_child_environment", "selected_api_port": port},
        )
        target = log.parent / f"rf24-{kind}.log"
        try:
            child_env = _child_environment(base_env, source_sha=actual_sha, run_id=run_id, kind=kind,
                                           database_host=database_host, database_name=database_name, port=port,
                                           scheduler_observations=scheduler_observations, worker_observations=worker_observations)
            stream = target.open("w", encoding="utf-8")
            process = subprocess.Popen((sys.executable, "-m", module), env=child_env, stdout=stream, stderr=subprocess.STDOUT, text=True, shell=False)
        except Exception as error:
            reporter.publish_failure(error)
            raise
        handles.append((kind, process, target, stream))
        reporter.passed({"pid": process.pid, "module": module})
    observations: dict[str, object] = {}
    try:
        reporter.begin(
            "SEED_E_API_LIVENESS", input={"endpoint": f"{base}/health/live"}, derived={"polls": 80},
            function="scripts.runtime.run_rf24_vertical_spine:request", environment={"api_base": base},
            evidence={"child_modules": ["mayak.runtime.api", "mayak.runtime.worker", "mayak.runtime.scheduler"]},
        )
        health = SafeResponse(0, {})
        for _ in range(80):
            for kind, process, target, _ in handles:
                if process.poll() is not None:
                    reporter.current = {"boundary": {"api": "SEED_B_API_PROCESS_START", "worker": "SEED_C_WORKER_PROCESS_START", "scheduler": "SEED_D_SCHEDULER_PROCESS_START"}[kind], "process_kind": f"mayak-{kind}", "exit_code": process.poll()}
                    raise _startup_failure(kind, process, target, "readiness")
            health = request(f"{base}/health/live")
            if health.status == 200:
                break
            time.sleep(0.25)
        if health.status != 200:
            raise RuntimeError("API did not become live: reason=readiness_timeout")
        reporter.passed({"status": health.status})
        reporter.begin("SEED_F_OPERATOR_LOGIN", input={"subject": "operator"}, derived={"endpoint": "/acceptance/login"}, function="run_rf24_vertical_spine:request", environment={"api_base": base}, evidence={"status": "pending"})
        login = request(f"{base}/acceptance/login", method="POST", body={"synthetic_subject": f"{run_id}:account"}, idempotency_key=f"{run_id}:login")
        if login._session_cookie is None:
            raise RuntimeError("synthetic login did not issue a session")
        reporter.passed(login.evidence())
        cookie = login._session_cookie
        login_safe = login.evidence()
        login_safe["payload"] = {"account_id": _json_payload(login.payload).get("account_id"), "state": _json_payload(login.payload).get("state")}
        operator_account_id = str(_json_payload(login.payload).get("account_id"))
        reporter.begin("SEED_G_ADMIN_BOOTSTRAP", input={"operator_account_id": operator_account_id}, derived={"endpoint": "/acceptance/admin/bootstrap"}, function="run_rf24_vertical_spine:request", environment={"api_base": base}, evidence={"session": "in-memory-only"})
        admin_bootstrap = request(f"{base}/acceptance/admin/bootstrap", method="POST", session_cookie=cookie, idempotency_key=f"{run_id}:admin-bootstrap")
        if admin_bootstrap.status != 200:
            raise RuntimeError(f"admin bootstrap failed: status={admin_bootstrap.status}")
        reporter.passed(admin_bootstrap.evidence())
        reporter.begin("SEED_H_TARGET_LOGIN", input={"subject": "target"}, derived={"endpoint": "/acceptance/login"}, function="run_rf24_vertical_spine:request", environment={"api_base": base}, evidence={"status": "pending"})
        target_login = request(f"{base}/acceptance/login", method="POST", body={"synthetic_subject": f"{run_id}:target"}, idempotency_key=f"{run_id}:target-login")
        if target_login._session_cookie is None:
            raise RuntimeError("synthetic target login did not issue a session")
        reporter.passed(target_login.evidence())
        cookie = target_login._session_cookie
        account_id = str(_json_payload(target_login.payload).get("account_id"))
        reporter.begin("SEED_I_ENTITLEMENT", input={"account_id": account_id}, derived={"endpoint": "/acceptance/entitlement"}, function="run_rf24_vertical_spine:request", environment={"api_base": base}, evidence={"status": "pending"})
        entitlement = request(f"{base}/acceptance/entitlement", method="POST", session_cookie=cookie, idempotency_key=f"{run_id}:entitlement")
        if entitlement.status != 200:
            raise RuntimeError(f"entitlement setup failed: status={entitlement.status}")
        reporter.passed(entitlement.evidence())
        reporter.begin("SEED_J_BEACON_CREATE", input={"account_id": account_id}, derived={"endpoint": "/api/v1/beacons"}, function="run_rf24_vertical_spine:request", environment={"api_base": base}, evidence={"status": "pending"})
        beacon = request(f"{base}/api/v1/beacons", method="POST", session_cookie=cookie, idempotency_key=f"{run_id}:beacon", body={"source_url": "https://synthetic.invalid/feed", "name": f"{run_id} beacon"})
        if beacon.status != 200:
            raise RuntimeError(f"Beacon create failed: status={beacon.status}")
        reporter.passed(beacon.evidence())
        beacon_body = _json_payload(beacon.payload)
        beacon_id = str(beacon_body["beacon_id"])
        version = int(beacon_body.get("row_version", 1))
        reporter.begin("SEED_K_BEACON_CONFIGURATION", input={"beacon_id": beacon_id, "row_version": version}, derived={"endpoint": "accept-synthetic-snapshot"}, function="run_rf24_vertical_spine:request", environment={"api_base": base}, evidence={"status": "pending"})
        snapshot = request(f"{base}/api/v1/beacons/{beacon_id}/accept-synthetic-snapshot?expected_row_version={version}", method="POST", session_cookie=cookie, idempotency_key=f"{run_id}:snapshot")
        if snapshot.status != 200:
            raise RuntimeError(f"Beacon configuration failed: status={snapshot.status}")
        reporter.passed(snapshot.evidence())
        version = int(_json_payload(snapshot.payload).get("row_version", version + 1))
        reporter.begin("SEED_L_BEACON_ACTIVATION", input={"beacon_id": beacon_id, "row_version": version}, derived={"endpoint": "activate"}, function="run_rf24_vertical_spine:request", environment={"api_base": base}, evidence={"status": "pending"})
        activated = request(f"{base}/api/v1/beacons/{beacon_id}/activate?expected_row_version={version}", method="POST", session_cookie=cookie, idempotency_key=f"{run_id}:activate")
        if activated.status != 200:
            raise RuntimeError(f"Beacon activation failed: status={activated.status}")
        reporter.passed(activated.evidence())
        reporter.begin("SEED_M_BASELINE_SCHEDULE", input={"beacon_id": beacon_id}, derived={"next_due": "past"}, function="run_rf24_vertical_spine:request", environment={"api_base": base}, evidence={"status": "pending"})
        schedule = request(f"{base}/api/v1/beacons/{beacon_id}/scan-schedule", method="POST", session_cookie=cookie, idempotency_key=f"{run_id}:schedule", body={"interval_seconds": 10800, "next_due_at": (datetime.now(UTC) - timedelta(seconds=5)).isoformat()})
        if schedule.status != 200:
            raise RuntimeError(f"baseline schedule failed: status={schedule.status}")
        reporter.passed(schedule.evidence())
        baseline_before = _db_snapshot(account_id, beacon_id)
        scan = SafeResponse(0, [])
        for _ in range(40):
            scan = request(f"{base}/api/v1/scans", session_cookie=cookie)
            if any(r.get("state") == "SUCCEEDED_BASELINE" for r in _run_records(scan.payload)):
                break
            time.sleep(0.5)
        baseline_after = _db_snapshot(account_id, beacon_id)
        if not any(r.get("state") == "SUCCEEDED_BASELINE" for r in _run_records(scan.payload)):
            raise RuntimeError("baseline completion not observed")
        reporter.begin("SEED_N_BASELINE_COMPLETION", input={"beacon_id": beacon_id}, derived={"state": "SUCCEEDED_BASELINE"}, function="run_rf24_vertical_spine:_run_records", environment={"process_kind": "mayak-worker"}, evidence={"scan_status": scan.status})
        reporter.passed({"state": "SUCCEEDED_BASELINE"})
        reporter.begin("SEED_O_DIFFERENCE_SCHEDULE", input={"beacon_id": beacon_id}, derived={"next_due": "past"}, function="run_rf24_vertical_spine:request", environment={"api_base": base}, evidence={"status": "pending"})
        second_schedule = request(f"{base}/api/v1/beacons/{beacon_id}/scan-schedule", method="POST", session_cookie=cookie, idempotency_key=f"{run_id}:schedule-2", body={"interval_seconds": 10800, "next_due_at": (datetime.now(UTC) - timedelta(seconds=5)).isoformat()})
        if second_schedule.status != 200:
            raise RuntimeError(f"difference schedule failed: status={second_schedule.status}")
        reporter.passed(second_schedule.evidence())
        difference_before = _db_snapshot(account_id, beacon_id)
        second = SafeResponse(0, [])
        for _ in range(40):
            second = request(f"{base}/api/v1/scans", session_cookie=cookie)
            if any(r.get("state") == "SUCCEEDED_DIFFERENCE" for r in _run_records(second.payload)):
                break
            time.sleep(0.5)
        if not any(r.get("state") == "SUCCEEDED_DIFFERENCE" for r in _run_records(second.payload)):
            raise RuntimeError("difference completion not observed")
        reporter.begin("SEED_P_DIFFERENCE_COMPLETION", input={"beacon_id": beacon_id}, derived={"state": "SUCCEEDED_DIFFERENCE"}, function="run_rf24_vertical_spine:_run_records", environment={"process_kind": "mayak-worker"}, evidence={"scan_status": second.status})
        reporter.passed({"state": "SUCCEEDED_DIFFERENCE"})
        reporter.begin("SEED_Q_NOTIFICATION_READ_MODEL", input={"beacon_id": beacon_id}, derived={"endpoint": "/api/v1/notifications"}, function="run_rf24_vertical_spine:request", environment={"api_base": base}, evidence={"status": "pending"})
        notifications = request(f"{base}/api/v1/notifications", session_cookie=cookie)
        reporter.passed(notifications.evidence())
        reporter.begin("SEED_R_WEB_CABINET", input={"account_id": account_id}, derived={"endpoint": "/web/"}, function="run_rf24_vertical_spine:request", environment={"api_base": base}, evidence={"status": "pending"})
        cabinet = request(f"{base}/web/", session_cookie=cookie)
        reporter.passed(cabinet.evidence())
        reporter.begin("SEED_S_ADMIN_DIAGNOSTICS", input={"account_id": account_id}, derived={"endpoint": f"/admin/account/{account_id}"}, function="run_rf24_vertical_spine:request", environment={"api_base": base}, evidence={"status": "pending"})
        admin = request(
            f"{base}/admin/account/{account_id}",
            session_cookie=login._session_cookie,
        )
        reporter.passed(admin.evidence())
        scheduler_records = [r for r in _read_jsonl(scheduler_observations, process_kind="mayak-scheduler", run_id=run_id) if r.get("record_type") == "scheduler_materialization" and r.get("materialized_count", 0) >= 1]
        worker_records = _read_jsonl(worker_observations, process_kind="mayak-worker", run_id=run_id)
        claims = [r for r in worker_records if r.get("record_type") == "worker_claim"]
        terminals = [r for r in worker_records if r.get("record_type") == "worker_terminal"]
        if len(scheduler_records) < 2 or len(claims) < 2 or len(terminals) < 2:
            raise RuntimeError("process-originated RF24 provenance is incomplete")
        reporter.begin("SEED_T_PROCESS_PROVENANCE", input={"scheduler_records": len(scheduler_records), "worker_claims": len(claims), "worker_terminals": len(terminals)}, derived={"required": 2}, function="run_rf24_vertical_spine:_read_jsonl", environment={"process_kinds": ["mayak-worker", "mayak-scheduler"]}, evidence={"observation_identity": "technical_id+run_id+process_kind"})
        reporter.passed({"scheduler_records": len(scheduler_records), "worker_claims": len(claims), "worker_terminals": len(terminals)})
        first, second_provenance = scheduler_records[0], scheduler_records[1]
        claim_by_work = {r["work_item_id"]: r for r in claims}
        terminal_by_work = {r["work_item_id"]: r for r in terminals}
        if first["work_item_id"] == second_provenance["work_item_id"]:
            raise RuntimeError("scheduler did not emit two distinct work IDs")
        durable = _db_provenance(beacon_id)
        durable_by_work = {r["work_item_id"]: r for r in durable}
        for item in (first, second_provenance):
            if item["work_item_id"] not in claim_by_work or item["work_item_id"] not in terminal_by_work or item["work_item_id"] not in durable_by_work:
                raise RuntimeError("process and durable provenance do not correlate")
        reporter.begin("SEED_U_DURABLE_STATE_PROOF", input={"beacon_id": beacon_id}, derived={"correlated_work_items": 2}, function="run_rf24_vertical_spine:_db_provenance+_db_snapshot", environment={"database": database_name}, evidence={"foreign_resource_impact": 0})
        first_terminal, second_terminal = terminal_by_work[first["work_item_id"]], terminal_by_work[second_provenance["work_item_id"]]
        difference_after = _db_snapshot(account_id, beacon_id)
        seed_state = _observed_seed_state(account_id, beacon_id)
        if any(not isinstance(item, dict) or int(item.get("count", 0)) <= 0 for item in seed_state.values()):
            raise RuntimeError("runtime-owned synthetic state projection is incomplete")
        notification_payload = _safe_payload(notifications.payload)
        event_id = None
        if isinstance(notification_payload, list) and notification_payload and isinstance(notification_payload[0], dict):
            event_id = notification_payload[0].get("event_id")
        before_events = cast(list[tuple[str, ...]], difference_before.get("notification_events", []))
        after_events = cast(list[tuple[str, ...]], difference_after.get("notification_events", []))
        before_event_ids = {item[0] for item in before_events if isinstance(item, tuple)}
        difference_event_ids = [row[0] for row in after_events if isinstance(row, tuple) and row[0] not in before_event_ids]
        if len(difference_event_ids) != 1 or event_id != difference_event_ids[0]:
            raise RuntimeError("actual Notification event does not match durable delta")
        before_outbox = cast(list[tuple[str, ...]], difference_before.get("outbox_records", []))
        before_attempts = cast(list[tuple[str, ...]], difference_before.get("delivery_attempts", []))
        after_outbox = cast(list[tuple[str, ...]], difference_after.get("outbox_records", []))
        after_attempts = cast(list[tuple[str, ...]], difference_after.get("delivery_attempts", []))
        outbox_delta = [row for row in after_outbox if row not in before_outbox]
        attempt_delta = [row for row in after_attempts if row not in before_attempts]
        history_row = next((row for row in notification_payload if isinstance(row, dict) and row.get("event_id") == event_id), {}) if isinstance(notification_payload, list) else {}
        if len(outbox_delta) != 1 or len(attempt_delta) != 1:
            raise RuntimeError("actual outbox/Telegram deltas are not singular")
        before_listings = cast(list[tuple[str, ...]], difference_before.get("listing_identities", []))
        after_listings = cast(list[tuple[str, ...]], difference_after.get("listing_identities", []))
        listing_delta = [row[0] for row in after_listings if row not in before_listings]
        web_payload = _safe_payload(cabinet.payload)
        web_refs = cast(tuple[str, ...], web_payload.get("opaque_references", ())) if isinstance(web_payload, dict) else ()
        admin_payload = _safe_payload(admin.payload)
        admin_refs = cast(tuple[str, ...], admin_payload.get("opaque_references", ())) if isinstance(admin_payload, dict) else ()
        scan_event_id = str(second_terminal["event_ids"][0]) if second_terminal.get("event_ids") else None
        notification_source_event_id = next((row[1] for row in after_events if isinstance(row, tuple) and row[0] == event_id), None)
        if notification_source_event_id != scan_event_id:
            raise RuntimeError("Notification event source identity does not match ScanNewListing event")
        reporter.passed({"state_projection": "complete", "notification_delta": 1, "outbox_delta": len(outbox_delta), "delivery_delta": len(attempt_delta)})
        web_observed = cabinet.status == 200 and account_id in web_refs and beacon_id in web_refs and bool(listing_delta)
        admin_observed = admin.status == 200 and account_id in admin_refs
        observations.update({
            "login": login_safe, "admin_bootstrap": admin_bootstrap.evidence(), "entitlement": entitlement.evidence(),
            "beacon": beacon.evidence(), "snapshot": snapshot.evidence(), "activated": activated.evidence(),
            "schedule": schedule.evidence(), "second_schedule": second_schedule.evidence(), "scan": scan.evidence(),
            "second_scan": second.evidence(), "notifications": notifications.evidence(), "cabinet": cabinet.evidence(),
            "admin": admin.evidence(),
        })
        evidence: dict[str, object] = {
            "technical_id": "RF24-RUNTIME-VERTICAL-SPINE-01-CORRECTIVE-02", "source_sha": actual_sha, "run_id": run_id,
            "api_bind": "127.0.0.1", "selected_api_port": port, "postgres_host_published": False,
            "processes": [{"kind": k, "pid": p.pid, "identity": f"mayak-{k}"} for k, p, _, _ in handles],
            "security": {"credentials_exposure": False, "cookie_in_memory_only": True, "serialized_cookie_value_present": False, "authorization_material_present": False},
            "identity": {"operator_account_id": operator_account_id, "target_account_id": account_id, "login_state": _json_payload(login.payload).get("state")},
            "scheduler_observations": scheduler_records[:2],
            "worker_observations": worker_records,
            "scheduler_cycles": [{"cycle": 1, **first}, {"cycle": 2, **second_provenance}],
            "worker_cycles": [{"cycle": 1, **claim_by_work[first["work_item_id"]], "terminal": first_terminal}, {"cycle": 2, **claim_by_work[second_provenance["work_item_id"]], "terminal": second_terminal}],
            "durable_provenance": durable,
            "scan_cycles": [{"cycle": 1, "run_id": first_terminal["run_id"], "state": first_terminal["terminal_state"], "new_listing_count": first_terminal["new_listing_count"], "event_ids": first_terminal["event_ids"]}, {"cycle": 2, "run_id": second_terminal["run_id"], "state": second_terminal["terminal_state"], "new_listing_count": second_terminal["new_listing_count"], "event_ids": second_terminal["event_ids"]}],
            "before_after": {"baseline": {"before": baseline_before, "after": baseline_after}, "difference": {"before": difference_before, "after": difference_after}},
            "notification": {"event_id": event_id, "source_event_id": notification_source_event_id, "source_listing_reference_ids": history_row.get("listing_reference_ids"), "effect_count": len(outbox_delta), "outbox_id": outbox_delta[0][0]},
            "telegram": {"channel_class": attempt_delta[0][3], "attempt_id": attempt_delta[0][0], "outbox_id": attempt_delta[0][1], "delivery_status": history_row.get("delivery_status"), "provider_safe_delivery_reference": history_row.get("provider_safe_delivery_reference"), "live_provider_calls": 0, "blind_retries": 0},
            "web_status_read_model": {"web_delivery_mode": "WEB_STATUS_READ_MODEL", "web_event_id": event_id, "web_source_event_id": scan_event_id, "web_account_id": account_id, "web_beacon_id": beacon_id, "web_listing_reference": listing_delta[0] if listing_delta else None, "web_visible": web_observed},
            "web_cabinet": {"status": cabinet.status, "response": web_payload, "target_state_visible": web_observed, "account_id": account_id, "beacon_id": beacon_id, "notification_event_id": event_id},
            "admin_diagnostics": {"status": admin.status, "response": admin_payload, "authenticated": admin_bootstrap.status == 200 and admin_observed, "authorized": admin_observed, "operator_account_id": operator_account_id, "target_account_id": account_id, "beacon_id": beacon_id, "baseline_run_id": first_terminal["run_id"], "difference_run_id": second_terminal["run_id"], "scan_event_id": scan_event_id, "notification_event_id": event_id, "target_observation": {"account_id": account_id, "beacon_id": beacon_id, "baseline_run_id": first_terminal["run_id"], "difference_run_id": second_terminal["run_id"], "notification_event_id": event_id, "scan_event_id": scan_event_id}, "target_diagnostics_visible": admin_observed},
            "runtime_boundaries": {"foreign_resource_impact": 0, "production_personal_data": 0, "direct_sql_read_assertions": ["scheduler_work_run_durable_cross_check", "listing_identity_before_after", "scan_new_listing_event_before_after", "notification_event_before_after", "outbox_before_after", "delivery_attempt_before_after"], "direct_sql_writes": []},
            "observations": observations, "provider_live_calls": 0, "foreign_resource_impact": 0, "production_personal_data": 0,
            "seed": {"runtime_boundary": "accepted-public-runtime", "database": "task-owned-source", "run_id": run_id, "state_classes": seed_state,
                     "idempotent_command": {"boundary": "POST /api/v1/beacons", "scope": "beacon_management",
                                             "key": f"{run_id}:beacon", "payload": {"source_url": "https://synthetic.invalid/feed", "name": f"{run_id} beacon"},
                                             "account_id": account_id, "beacon_id": beacon_id}},
            "credentials_exposure": False,
        }
        output.parent.mkdir(parents=True, exist_ok=True)
        probes.parent.mkdir(parents=True, exist_ok=True)
        probes.write_text(json.dumps({"source_sha": actual_sha, "run_id": run_id, "safe": True}, indent=2) + "\n", encoding="utf-8")
    except Exception as error:
        reporter.publish_failure(error)
        raise
    finally:
        for _, process, _, _ in handles:
            process.terminate()
        for _, process, _, _ in handles:
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        for _, _, _, stream in handles:
            stream.flush()
            stream.close()
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text("\n".join(f"[{kind}] pid={process.pid}\n{_sanitized_log_tail(path)}" for kind, process, path, _ in handles), encoding="utf-8")
    output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--probes", type=Path, required=True)
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--source-sha", required=True)
    args = parser.parse_args()
    produce(args.repo_root.resolve(), args.output, args.probes, args.log, args.source_sha)
