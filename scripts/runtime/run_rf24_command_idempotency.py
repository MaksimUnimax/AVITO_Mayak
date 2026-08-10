# ruff: noqa: E501
"""Run RF24 public Beacon-create idempotency scenarios against PostgreSQL."""

from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any
from uuid import uuid4

from sqlalchemy import create_engine, text

TECHNICAL_ID = "RF24-COMMAND-IDEMPOTENCY-SCENARIOS-01"
SCOPE = "beacon_management"


def resolve_acceptance_database_host(host: str) -> str:
    """Resolve a service name for the API child without weakening settings policy."""
    try:
        addresses = {
            ipaddress.ip_address(item[4][0])
            for item in socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
        }
    except OSError as exc:
        raise RuntimeError("database host resolution failed") from exc
    if not addresses or any(not address.is_private for address in addresses):
        raise RuntimeError("database host did not resolve only to private addresses")
    return sorted(addresses, key=str)[0].compressed


def fingerprint(account: str, source_url: str, name: str) -> str:
    value = {
        "command": "create_preparation",
        "values": {"account": account, "name": name, "url": source_url},
    }
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def request(
    base: str,
    path: str,
    *,
    payload: object | None = None,
    key: str | None = None,
    cookie: str | None = None,
    method: str = "POST",
) -> tuple[int, dict[str, Any], str | None]:
    headers = {"Content-Type": "application/json", "Origin": base}
    if key is not None:
        headers["Idempotency-Key"] = key
    if cookie is not None:
        headers["Cookie"] = f"mayak_session={cookie}"
    req = urllib.request.Request(
        f"{base}{path}",
        method=method,
        headers=headers,
        data=None if payload is None else json.dumps(payload).encode(),
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            raw = response.read(65536)
            return response.status, json.loads(raw), response.headers.get("set-cookie")
    except urllib.error.HTTPError as exc:
        raw = exc.read(65536)
        try:
            body = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            body = {"error": "non-json response"}
        return exc.code, body, None


def safe_process_diagnostic(process: subprocess.Popen[str], log_path: Path) -> dict[str, Any]:
    """Return bounded process state and log metadata, never log contents."""
    return {
        "pid": process.pid,
        "poll": process.poll(),
        "log": {
            "path": log_path.name,
            "exists": log_path.exists(),
            "size": log_path.stat().st_size if log_path.exists() else 0,
        },
    }


def safe_http_diagnostic(status: int, body: dict[str, Any]) -> dict[str, Any]:
    """Keep only bounded, non-secret HTTP failure context."""
    allowed = {"detail", "error", "reason", "status", "state"}
    return {
        "status": status,
        "body": {key: str(value)[:160] for key, value in body.items() if key in allowed},
    }


def wait_for_api(
    process: subprocess.Popen[str], base: str, source_sha: str, log_path: Path
) -> dict[str, Any]:
    """Probe the safe readiness boundary before attempting synthetic login."""
    last_version: dict[str, Any] = {}
    for _ in range(80):
        state = process.poll()
        if state is not None:
            raise RuntimeError(f"api startup failed before readiness: {safe_process_diagnostic(process, log_path)}")
        try:
            status, body, _ = request(base, "/version", method="GET")
            last_version = body
            if status == 200:
                if body.get("source_sha") != source_sha:
                    raise RuntimeError("api /version source SHA mismatch")
                return body
        except (OSError, urllib.error.URLError):
            pass
        time.sleep(0.25)
    raise RuntimeError(
        f"api readiness timeout: {safe_process_diagnostic(process, log_path)} "
        f"version_status={last_version.get('status', 'unavailable')}"
    )


def snapshot(engine: Any, account: str, key: str, beacon_ids: list[str]) -> dict[str, Any]:
    beacon_id = beacon_ids[0] if beacon_ids else "00000000-0000-0000-0000-000000000000"
    with engine.connect() as c:
        beacons = [
            dict(r)
            for r in c.execute(
                text(
                    "SELECT id, account_id, name, source_url, state, row_version FROM mayak.beacon_beacons WHERE account_id=:account AND id=:beacon_id"
                ),
                {"account": account, "beacon_id": beacon_id},
            ).mappings()
        ]
        events = [
            dict(r)
            for r in c.execute(
                text(
                    "SELECT id, beacon_id, from_state, to_state, reason FROM mayak.beacon_lifecycle_events WHERE beacon_id=:beacon_id ORDER BY id"
                ),
                {"beacon_id": beacon_id},
            ).mappings()
        ]
        audit = [
            dict(r)
            for r in c.execute(
                text(
                    "SELECT id, action_code, target_type, target_id, reason FROM mayak.platform_audit_entries WHERE actor_account_id=:account AND action_code='BEACON_PREPARATION_CREATED' AND target_id=:beacon_id"
                ),
                {"account": account, "beacon_id": beacon_id},
            ).mappings()
        ]
        idem = [
            dict(r)
            for r in c.execute(
                text(
                    "SELECT id, scope, idempotency_key, request_fingerprint, result FROM mayak.platform_idempotency_records WHERE scope=:scope AND idempotency_key=:key ORDER BY id"
                ),
                {"scope": SCOPE, "key": key},
            ).mappings()
        ]

    def safe(row: dict[str, Any]) -> dict[str, Any]:
        return {
            k: (str(v) if k in {"id", "account_id", "beacon_id"} and v is not None else v)
            for k, v in row.items()
        }

    return {
        "beacons": [safe(r) for r in beacons],
        "lifecycle_events": [safe(r) for r in events],
        "audit": [safe(r) for r in audit],
        "idempotency": [safe(r) for r in idem],
        "observation_source": "owning-read-model",
    }


def one_scenario(
    engine: Any, base: str, account: str, cookie: str, *, name: str, key: str, changed: bool = False
) -> dict[str, Any]:
    url = "https://synthetic.invalid/rf24/command"
    payload = {"source_url": url, "name": name}
    candidate = {"source_url": url, "name": name + "-changed"} if changed else payload
    fp = fingerprint(account, url, name)
    candidate_fp = fingerprint(account, url, candidate["name"])
    b0 = snapshot(engine, account, key, [])
    first_status, first_body, _ = request(
        base, "/api/v1/beacons", payload=payload, key=key, cookie=cookie
    )
    first_id = str(first_body.get("beacon_id", ""))
    b1 = snapshot(engine, account, key, [first_id])
    second_status, second_body, _ = request(
        base, "/api/v1/beacons", payload=candidate if changed else payload, key=key, cookie=cookie
    )
    b2 = snapshot(engine, account, key, [first_id])
    return {
        "scenario_name": "same-key-different-fingerprint" if changed else "duplicate-command",
        "acceptance_run_id": os.environ["RF24_ACCEPTANCE_RUN_ID"],
        "source_sha": os.environ["MAYAK_SOURCE_SHA"],
        "account_id": account,
        "key": key,
        "scope": SCOPE,
        "payload": payload,
        "candidate_payload": candidate if changed else payload,
        "fingerprint": fp,
        "candidate_fingerprint": candidate_fp,
        "first_http": {"status": first_status, "body": first_body},
        "second_http": {"status": second_status, "body": second_body},
        "before": b0,
        "after_first": b1,
        "after_second": b2,
        "beacon_id": first_id,
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--repo-root", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--probes", type=Path, required=True)
    p.add_argument("--log", type=Path, required=True)
    p.add_argument("--source-sha", required=True)
    a = p.parse_args()
    observed = subprocess.check_output(
        ("git", "-C", str(a.repo_root), "rev-parse", "HEAD"), text=True
    ).strip()
    if observed != a.source_sha or os.environ.get("GITHUB_SHA", observed) != observed:
        raise SystemExit("source identity mismatch")
    run_id = f"rf24-command-{uuid4()}"
    os.environ["RF24_ACCEPTANCE_RUN_ID"] = run_id
    os.environ["MAYAK_SOURCE_SHA"] = observed
    dsn = os.environ.get("MAYAK_RF10_POSTGRES_DSN")
    if not dsn:
        raise SystemExit("MAYAK_RF10_POSTGRES_DSN is required")
    engine = create_engine(dsn)
    env = os.environ.copy()
    # The parent keeps RF10/RF11 DSNs for tests, but strict API settings reject
    # those test-only MAYAK_* names as unknown runtime configuration.
    for key in tuple(env):
        if key.startswith(("MAYAK_RF10_", "MAYAK_RF11_")):
            env.pop(key)
    env.update(
        {
            "MAYAK_RUNTIME_PROFILE": "synthetic_acceptance",
            "MAYAK_PROCESS_KIND": "mayak-api",
            "MAYAK_SOURCE_SHA": observed,
            "MAYAK_SYNTHETIC_IDENTITY_ENABLED": "true",
            "MAYAK_API_BIND_HOST": "127.0.0.1",
            "MAYAK_API_HOST_PORT": "disabled",
            "MAYAK_AVITO_LIVE_ENABLED": "false",
            "MAYAK_TELEGRAM_ENABLED": "false",
            "MAYAK_MAX_ENABLED": "false",
            "MAYAK_YOOKASSA_ENABLED": "false",
            "MAYAK_EGRESS_AGENT_ENABLED": "false",
        }
    )
    env["MAYAK_DATABASE_HOST"] = resolve_acceptance_database_host(
        env.get("MAYAK_DATABASE_HOST", "mayak-postgres")
    )
    port = None
    for candidate in range(18080, 18100):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            try:
                probe.bind(("127.0.0.1", candidate))
            except OSError:
                continue
            port = candidate
            break
    if port is None:
        raise SystemExit("no task-local API port available in 18080-18099")
    env["MAYAK_API_INTERNAL_PORT"] = str(port)
    log_handle = a.log.open("w", encoding="utf-8")
    process = subprocess.Popen(
        (sys.executable, "-m", "mayak.runtime.api"),
        cwd=a.repo_root,
        env=env,
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        base = f"http://127.0.0.1:{port}"
        wait_for_api(process, base, observed, a.log)
        login_cookie = None
        login: dict[str, Any] = {}
        login_status = 0
        for _ in range(80):
            if process.poll() is not None:
                raise RuntimeError(
                    f"api exited during synthetic login: {safe_process_diagnostic(process, a.log)}"
                )
            try:
                login_status, login, set_cookie = request(
                    base,
                    "/acceptance/login",
                    payload={"synthetic_subject": run_id},
                    key=f"login-{run_id}",
                )
                if login_status == 200 and set_cookie:
                    login_cookie = set_cookie
                    break
            except OSError:
                pass
            time.sleep(0.25)
        if not login_cookie:
            raise RuntimeError(
                f"synthetic login failed: {safe_http_diagnostic(login_status, login)} "
                f"process={safe_process_diagnostic(process, a.log)}"
            )
        cookie = login_cookie.split("=", 1)[1].split(";", 1)[0]
        account = str(login["account_id"])
        entitlement_status, entitlement_body, _ = request(
            base, "/acceptance/entitlement", key=f"entitlement-{run_id}", cookie=cookie
        )
        if entitlement_status != 200:
            raise RuntimeError(
                f"entitlement setup failed: {safe_http_diagnostic(entitlement_status, entitlement_body)} "
                f"process={safe_process_diagnostic(process, a.log)}"
            )
        a_item = one_scenario(
            engine, base, account, cookie, name=f"{run_id}-A", key=f"{run_id}-K-A"
        )
        b_item = one_scenario(
            engine, base, account, cookie, name=f"{run_id}-B", key=f"{run_id}-K-B", changed=True
        )
        evidence = {
            "schema_version": 1,
            "technical_id": TECHNICAL_ID,
            "acceptance_run_id": run_id,
            "source_sha": observed,
            "public_endpoint": "POST /api/v1/beacons",
            "source_trace": {
                "composition": "RF23Composition.beacon_create",
                "owner": "BeaconManagementRuntime.create_preparation",
                "repository": "PostgresTerminalIdempotencyRepository",
                "scope": SCOPE,
                "fingerprint_inputs": [
                    "command=create_preparation",
                    "account_id",
                    "source_url",
                    "name",
                ],
            },
            "scenarios": [a_item, b_item],
            "provider_live_calls": 0,
            "foreign_resource_impact": 0,
        }
        a.output.write_text(
            json.dumps(evidence, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8"
        )
        a.probes.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "technical_id": TECHNICAL_ID,
                    "acceptance_run_id": run_id,
                    "source_sha": observed,
                    "process_kind": "mayak-api",
                    "pid": process.pid,
                    "public_boundary": "127.0.0.1",
                    "session_material": "removed",
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
    finally:
        process.terminate()
        try:
            process.wait(10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(5)
        log_handle.close()


if __name__ == "__main__":
    main()
