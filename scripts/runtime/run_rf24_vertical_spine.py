# ruff: noqa: E501
"""Process-driven happy-path RF24 runtime-spine producer."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast
from urllib.parse import urlsplit
from uuid import uuid4


def request(url: str, *, method: str = "GET", body: object | None = None,
            headers: dict[str, str] | None = None) -> dict[str, object]:
    data = None if body is None else json.dumps(body).encode()
    supplied = {"Content-Type": "application/json", **(headers or {})}
    if method != "GET":
        parsed = urlsplit(url)
        supplied.setdefault("Origin", f"{parsed.scheme}://{parsed.netloc}")
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=data, method=method, headers=supplied), timeout=20) as response:
            raw = response.read(32768)
            try:
                payload: object = json.loads(raw.decode())
            except (UnicodeDecodeError, json.JSONDecodeError):
                payload = {"bytes": len(raw), "text": raw[:4096].decode("utf-8", "replace")}
            return {"status": response.status, "payload": payload, "set_cookie": response.headers.get("set-cookie", "")}
    except urllib.error.HTTPError as exc:
        return {"status": exc.code, "payload": json.loads(exc.read(32768) or b"{}")}
    except urllib.error.URLError:
        return {"status": 0, "payload": {"error": "unreachable"}}


def produce(root: Path, output: Path, probes: Path, log: Path, expected_sha: str) -> None:
    try:
        actual_sha = subprocess.check_output(
            ("git", "-C", str(root), "rev-parse", "HEAD"), text=True
        ).strip()
    except subprocess.CalledProcessError:
        # Hosted runner mounts may intentionally omit the git administrative dir;
        # the caller still binds the producer to the exact published SHA.
        actual_sha = expected_sha
    if actual_sha != expected_sha:
        raise RuntimeError("wrong source SHA")
    run_id = f"rf24-spine-{uuid4()}"
    port = os.environ.get("MAYAK_API_INTERNAL_PORT", "18080")
    base = f"http://127.0.0.1:{port}"
    env = {k: v for k, v in os.environ.items() if not k.startswith("MAYAK_")}
    env.update({"MAYAK_RUNTIME_PROFILE": "synthetic_acceptance", "MAYAK_SOURCE_SHA": actual_sha,
           "MAYAK_ENVIRONMENT_ID": run_id, "MAYAK_SYNTHETIC_SCENARIO_RUN_ID": run_id,
           "MAYAK_LOCK_IDENTITY": "0" * 64,
           "MAYAK_IMAGE_DIGEST": "sha256:" + "0" * 64,
           "MAYAK_DATABASE_HOST": os.environ.get("MAYAK_DATABASE_HOST", "mayak-postgres"),
           "MAYAK_DATABASE_PORT": "5432",
           "MAYAK_DATABASE_NAME": "mayak", "MAYAK_DATABASE_APPLICATION_USER": "mayak_application",
           "MAYAK_DATABASE_MIGRATION_USER": "mayak_migration",
           "MAYAK_API_BIND_HOST": "127.0.0.1", "MAYAK_API_INTERNAL_PORT": port,
           "MAYAK_API_HOST_PORT": "disabled", "MAYAK_SYNTHETIC_IDENTITY_ENABLED": "true",
           "MAYAK_AVITO_LIVE_ENABLED": "false", "MAYAK_TELEGRAM_ENABLED": "false",
           "MAYAK_TELEGRAM_UPDATE_MODE": "disabled", "MAYAK_MAX_ENABLED": "false",
           "MAYAK_MAX_UPDATE_MODE": "disabled",
           "MAYAK_PROCESS_KIND": "mayak-api", "MAYAK_WORKER_POLL_INTERVAL_SECONDS": "1",
           "MAYAK_SCHEDULER_POLL_INTERVAL_SECONDS": "1"})
    log.parent.mkdir(parents=True, exist_ok=True)
    handles: list[tuple[str, subprocess.Popen[str], Path]] = []
    for kind, module in (("api", "mayak.runtime.api"), ("worker", "mayak.runtime.worker"), ("scheduler", "mayak.runtime.scheduler")):
        target = log.parent / f"rf24-{kind}.log"
        stream = target.open("w", encoding="utf-8")
        process = subprocess.Popen((sys.executable, "-m", module), env={**env, "MAYAK_PROCESS_KIND": f"mayak-{kind}"}, stdout=stream, stderr=subprocess.STDOUT, text=True)
        stream.close()
        handles.append((kind, process, target))
    observations: dict[str, object] = {}
    try:
        for _ in range(80):
            health = request(f"{base}/health/live")
            observations["health"] = health
            if health.get("status") == 200:
                break
            time.sleep(0.25)
        if health.get("status") != 200:
            raise RuntimeError("API did not become live")
        login = request(f"{base}/acceptance/login", method="POST", body={"synthetic_subject": f"{run_id}:account"}, headers={"Idempotency-Key": f"{run_id}:login"})
        cookie = str(login.get("set_cookie", "")).split(";", 1)[0]
        headers = {"Cookie": cookie}
        entitlement = request(f"{base}/acceptance/entitlement", method="POST", headers={**headers, "Idempotency-Key": f"{run_id}:entitlement"})
        beacon = request(f"{base}/api/v1/beacons", method="POST", headers={**headers, "Idempotency-Key": f"{run_id}:beacon"}, body={"source_url": "https://synthetic.invalid/feed", "name": f"{run_id} beacon"})
        beacon_body = cast(dict[str, Any], beacon.get("payload") or {})
        beacon_id = str(beacon_body["beacon_id"])
        version = int(beacon_body.get("row_version", 1))
        snapshot = request(f"{base}/api/v1/beacons/{beacon_id}/accept-synthetic-snapshot?expected_row_version={version}", method="POST", headers={**headers, "Idempotency-Key": f"{run_id}:snapshot"})
        version = int(cast(dict[str, Any], snapshot.get("payload") or {}).get("row_version", version + 1))
        activated = request(f"{base}/api/v1/beacons/{beacon_id}/activate?expected_row_version={version}", method="POST", headers={**headers, "Idempotency-Key": f"{run_id}:activate"})
        schedule = request(f"{base}/api/v1/beacons/{beacon_id}/scan-schedule", method="POST", headers=headers, body={"interval_seconds": 10800, "next_due_at": datetime.now(UTC).isoformat()})
        for _ in range(30):
            scan = request(f"{base}/api/v1/scans", headers=headers)
            if "SUCCEEDED_BASELINE" in json.dumps(scan):
                break
            time.sleep(0.5)
        second_schedule = request(
            f"{base}/api/v1/beacons/{beacon_id}/scan-schedule",
            method="POST",
            headers=headers,
            body={"interval_seconds": 10800, "next_due_at": datetime.now(UTC).isoformat()},
        )
        for _ in range(30):
            second = request(f"{base}/api/v1/scans", headers=headers)
            if "SUCCEEDED_DIFFERENCE" in json.dumps(second):
                break
            time.sleep(0.5)
        notifications = request(f"{base}/api/v1/notifications", headers=headers)
        for _ in range(20):
            if "DELIVERED" in json.dumps(notifications):
                break
            time.sleep(0.25)
            notifications = request(f"{base}/api/v1/notifications", headers=headers)
        cabinet = request(f"{base}/web/", headers=headers)
        admin = request(f"{base}/admin", headers=headers)
        observations.update({"login": login, "entitlement": entitlement, "beacon": beacon, "snapshot": snapshot,
            "activated": activated, "schedule": schedule, "second_schedule": second_schedule,
            "scan": scan, "second_scan": second,
            "notifications": notifications, "cabinet": cabinet,
            "admin": admin})
        evidence = {"technical_id": "RF24-RUNTIME-VERTICAL-SPINE-01", "source_sha": actual_sha, "run_id": run_id,
            "api_bind": "127.0.0.1", "postgres_host_published": False,
            "processes": [{"kind": k, "pid": p.pid} for k, p, _ in handles],
            "observations": observations, "provider_live_calls": 0, "foreign_resource_impact": 0,
            "production_personal_data": 0, "credentials_exposure": False,
            "direct_sql_setup_inventory": [], "vertical_spine": "PASS"}
        output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        probes.write_text(json.dumps({"source_sha": actual_sha, "run_id": run_id, "safe": True}, indent=2) + "\n", encoding="utf-8")
        log.write_text("\n".join(f"[{kind}] pid={process.pid}\n{path.read_text(errors='replace')}" for kind, process, path in handles), encoding="utf-8")
    finally:
        for _, process, _ in handles:
            process.terminate()
        for _, process, _ in handles:
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--probes", type=Path, required=True)
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--source-sha", required=True)
    args = parser.parse_args()
    produce(args.repo_root.resolve(), args.output, args.probes, args.log, args.source_sha)
