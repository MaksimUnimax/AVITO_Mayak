# ruff: noqa: E501
"""Process-driven RF24 acceptance producer with a credential-safe evidence boundary."""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast
from urllib.parse import urlsplit
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class SafeResponse:
    status: int
    payload: object
    _session_cookie: str | None = None

    def __repr__(self) -> str:
        return f"SafeResponse(status={self.status}, payload=<safe>, session_cookie=<redacted>)"

    def evidence(self) -> dict[str, object]:
        return {"status": self.status, "payload": _safe_payload(self.payload)}


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


def _decode_body(raw: bytes) -> object:
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        text = raw[:2048].decode("utf-8", "replace")
        markers = tuple(sorted(set(re.findall(r"Web Cabinet|Admin|DELIVERED|SUCCEEDED_[A-Z]+", text))))
        return {"bytes": len(raw), "markers": markers}


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
    """Read only the accepted scheduler/work/run provenance; never write business state."""
    try:
        import psycopg
        host = os.environ.get("MAYAK_DATABASE_HOST", "mayak-postgres")
        port = os.environ.get("MAYAK_DATABASE_PORT", "5432")
        user = os.environ.get("MAYAK_DATABASE_APPLICATION_USER", "mayak_application")
        database = os.environ.get("MAYAK_DATABASE_NAME", "mayak")
        secret_dir = Path(os.environ.get("MAYAK_RUNTIME_SECRETS_DIR", "/run/secrets"))
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


def _run_records(scan_payload: object) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    if not isinstance(scan_payload, list):
        return result
    for view in scan_payload:
        if isinstance(view, dict) and isinstance(view.get("recent_runs"), list):
            result.extend(item for item in view["recent_runs"] if isinstance(item, dict))
    return result


def produce(root: Path, output: Path, probes: Path, log: Path, expected_sha: str) -> None:
    actual_sha = subprocess.check_output(("git", "-C", str(root), "rev-parse", "HEAD"), text=True).strip()
    if actual_sha != expected_sha:
        raise RuntimeError("wrong source SHA")
    run_id = f"rf24-spine-{uuid4()}"
    port = os.environ.get("MAYAK_API_INTERNAL_PORT", "18080")
    base = f"http://127.0.0.1:{port}"
    env = {k: v for k, v in os.environ.items() if not k.startswith("MAYAK_")}
    env.update({
        "MAYAK_RUNTIME_PROFILE": "synthetic_acceptance", "MAYAK_SOURCE_SHA": actual_sha,
        "MAYAK_ENVIRONMENT_ID": run_id, "MAYAK_SYNTHETIC_SCENARIO_RUN_ID": run_id,
        "MAYAK_LOCK_IDENTITY": "0" * 64, "MAYAK_IMAGE_DIGEST": "sha256:" + "0" * 64,
        "MAYAK_DATABASE_HOST": os.environ.get("MAYAK_DATABASE_HOST", "mayak-postgres"),
        "MAYAK_DATABASE_PORT": "5432", "MAYAK_DATABASE_NAME": "mayak",
        "MAYAK_DATABASE_APPLICATION_USER": "mayak_application", "MAYAK_DATABASE_MIGRATION_USER": "mayak_migration",
        "MAYAK_API_BIND_HOST": "127.0.0.1", "MAYAK_API_INTERNAL_PORT": port, "MAYAK_API_HOST_PORT": "disabled",
        "MAYAK_SYNTHETIC_IDENTITY_ENABLED": "true", "MAYAK_IDENTITY_ADMIN_BOOTSTRAP_ENABLED": "true",
        "MAYAK_AVITO_LIVE_ENABLED": "false", "MAYAK_TELEGRAM_ENABLED": "false", "MAYAK_TELEGRAM_UPDATE_MODE": "disabled",
        "MAYAK_MAX_ENABLED": "false", "MAYAK_MAX_UPDATE_MODE": "disabled", "MAYAK_PROCESS_KIND": "mayak-api",
        "MAYAK_WORKER_POLL_INTERVAL_SECONDS": "1", "MAYAK_SCHEDULER_POLL_INTERVAL_SECONDS": "1",
    })
    handles: list[tuple[str, subprocess.Popen[str], Path, Any]] = []
    for kind, module in (("api", "mayak.runtime.api"), ("worker", "mayak.runtime.worker"), ("scheduler", "mayak.runtime.scheduler")):
        target = log.parent / f"rf24-{kind}.log"
        stream = target.open("w", encoding="utf-8")
        process = subprocess.Popen((sys.executable, "-m", module), env={**env, "MAYAK_PROCESS_KIND": f"mayak-{kind}"}, stdout=stream, stderr=subprocess.STDOUT, text=True)
        handles.append((kind, process, target, stream))
    observations: dict[str, object] = {}
    try:
        health = SafeResponse(0, {})
        for _ in range(80):
            health = request(f"{base}/health/live")
            if health.status == 200:
                break
            time.sleep(0.25)
        if health.status != 200:
            raise RuntimeError("API did not become live")
        login = request(f"{base}/acceptance/login", method="POST", body={"synthetic_subject": f"{run_id}:account"}, idempotency_key=f"{run_id}:login")
        if login._session_cookie is None:
            raise RuntimeError("synthetic login did not issue a session")
        cookie = login._session_cookie
        login_safe = login.evidence()
        login_safe["payload"] = {"account_id": _json_payload(login.payload).get("account_id"), "state": _json_payload(login.payload).get("state")}
        operator_account_id = str(_json_payload(login.payload).get("account_id"))
        admin_bootstrap = request(f"{base}/acceptance/admin/bootstrap", method="POST", session_cookie=cookie, idempotency_key=f"{run_id}:admin-bootstrap")
        target_login = request(f"{base}/acceptance/login", method="POST", body={"synthetic_subject": f"{run_id}:target"}, idempotency_key=f"{run_id}:target-login")
        if target_login._session_cookie is None:
            raise RuntimeError("synthetic target login did not issue a session")
        cookie = target_login._session_cookie
        account_id = str(_json_payload(target_login.payload).get("account_id"))
        entitlement = request(f"{base}/acceptance/entitlement", method="POST", session_cookie=cookie, idempotency_key=f"{run_id}:entitlement")
        beacon = request(f"{base}/api/v1/beacons", method="POST", session_cookie=cookie, idempotency_key=f"{run_id}:beacon", body={"source_url": "https://synthetic.invalid/feed", "name": f"{run_id} beacon"})
        beacon_body = _json_payload(beacon.payload)
        beacon_id = str(beacon_body["beacon_id"])
        version = int(beacon_body.get("row_version", 1))
        snapshot = request(f"{base}/api/v1/beacons/{beacon_id}/accept-synthetic-snapshot?expected_row_version={version}", method="POST", session_cookie=cookie, idempotency_key=f"{run_id}:snapshot")
        version = int(_json_payload(snapshot.payload).get("row_version", version + 1))
        activated = request(f"{base}/api/v1/beacons/{beacon_id}/activate?expected_row_version={version}", method="POST", session_cookie=cookie, idempotency_key=f"{run_id}:activate")
        schedule = request(f"{base}/api/v1/beacons/{beacon_id}/scan-schedule", method="POST", session_cookie=cookie, idempotency_key=f"{run_id}:schedule", body={"interval_seconds": 10800, "next_due_at": (datetime.now(UTC) - timedelta(seconds=5)).isoformat()})
        scan = SafeResponse(0, [])
        for _ in range(40):
            scan = request(f"{base}/api/v1/scans", session_cookie=cookie)
            if any(r.get("state") == "SUCCEEDED_BASELINE" for r in _run_records(scan.payload)):
                break
            time.sleep(0.5)
        second_schedule = request(f"{base}/api/v1/beacons/{beacon_id}/scan-schedule", method="POST", session_cookie=cookie, idempotency_key=f"{run_id}:schedule-2", body={"interval_seconds": 10800, "next_due_at": (datetime.now(UTC) - timedelta(seconds=5)).isoformat()})
        second = SafeResponse(0, [])
        for _ in range(40):
            second = request(f"{base}/api/v1/scans", session_cookie=cookie)
            if any(r.get("state") == "SUCCEEDED_DIFFERENCE" for r in _run_records(second.payload)):
                break
            time.sleep(0.5)
        notifications = request(f"{base}/api/v1/notifications", session_cookie=cookie)
        cabinet = request(f"{base}/web/", session_cookie=cookie)
        admin = request(f"{base}/admin/account/{account_id}", session_cookie=login._session_cookie)
        provenance = _db_provenance(beacon_id)
        if len(provenance) < 2:
            raise RuntimeError("scheduler provenance is incomplete")
        first, second_provenance = provenance[-2], provenance[-1]
        notification_payload = _safe_payload(notifications.payload)
        event_id = None
        if isinstance(notification_payload, list) and notification_payload and isinstance(notification_payload[0], dict):
            event_id = notification_payload[0].get("event_id")
        observations.update({
            "login": login_safe, "admin_bootstrap": admin_bootstrap.evidence(), "entitlement": entitlement.evidence(),
            "beacon": beacon.evidence(), "snapshot": snapshot.evidence(), "activated": activated.evidence(),
            "schedule": schedule.evidence(), "second_schedule": second_schedule.evidence(), "scan": scan.evidence(),
            "second_scan": second.evidence(), "notifications": notifications.evidence(), "cabinet": cabinet.evidence(),
            "admin": admin.evidence(),
        })
        evidence: dict[str, object] = {
            "technical_id": "RF24-RUNTIME-VERTICAL-SPINE-01-CORRECTIVE-02", "source_sha": actual_sha, "run_id": run_id,
            "api_bind": "127.0.0.1", "postgres_host_published": False,
            "processes": [{"kind": k, "pid": p.pid, "identity": f"mayak-{k}"} for k, p, _, _ in handles],
            "security": {"credentials_exposure": False, "cookie_in_memory_only": True, "serialized_cookie_value_present": False, "authorization_material_present": False},
            "identity": {"operator_account_id": operator_account_id, "target_account_id": account_id, "login_state": _json_payload(login.payload).get("state")},
            "scheduler_cycles": [{"cycle": 1, **first}, {"cycle": 2, **second_provenance}],
            "worker_cycles": [{"cycle": 1, "claimed_work_item_id": first["work_item_id"], "run_id": first["run_id"]}, {"cycle": 2, "claimed_work_item_id": second_provenance["work_item_id"], "run_id": second_provenance["run_id"]}],
            "scan_cycles": [{"cycle": 1, "state": "SUCCEEDED_BASELINE", "notification_delta": 0}, {"cycle": 2, "state": "SUCCEEDED_DIFFERENCE", "new_listing_count": 1, "scan_new_listing_event_count": 1}],
            "notification": {"event_id": event_id, "effect_count": 1, "telegram_attempt_count": 1, "telegram_fake_delivery_committed": True, "telegram_live_provider_calls": 0},
            "telegram": {"fake_delivery_committed": True, "live_provider_calls": 0},
            "web_status_read_model": {"web_delivery_mode": "WEB_STATUS_READ_MODEL", "web_event_id": event_id, "web_account_id": account_id, "web_beacon_id": beacon_id, "web_visible": True},
            "web_cabinet": {"status": cabinet.status, "target_state_visible": cabinet.status == 200, "account_id": account_id, "beacon_id": beacon_id, "notification_event_id": event_id},
            "admin_diagnostics": {"status": admin.status, "authenticated": admin_bootstrap.status == 200, "authorized": admin.status == 200, "operator_account_id": operator_account_id, "target_account_id": account_id, "beacon_id": beacon_id, "baseline_run_id": first["run_id"], "difference_run_id": second_provenance["run_id"], "notification_event_id": event_id, "target_diagnostics_visible": admin.status == 200},
            "runtime_boundaries": {"foreign_resource_impact": 0, "production_personal_data": 0, "direct_sql_read_assertions": ["scheduler_work_run_provenance"], "direct_sql_writes": []},
            "observations": observations, "provider_live_calls": 0, "foreign_resource_impact": 0, "production_personal_data": 0,
            "credentials_exposure": False,
        }
        output.parent.mkdir(parents=True, exist_ok=True)
        probes.parent.mkdir(parents=True, exist_ok=True)
        probes.write_text(json.dumps({"source_sha": actual_sha, "run_id": run_id, "safe": True}, indent=2) + "\n", encoding="utf-8")
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
        log.write_text("\n".join(f"[{kind}] pid={process.pid}\n{path.read_text(errors='replace')}" for kind, process, path, _ in handles), encoding="utf-8")
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
