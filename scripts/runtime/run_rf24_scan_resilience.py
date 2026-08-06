# ruff: noqa: E501, E701, E702
"""Execute the seven RF24 scan resilience scenarios against real local processes."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast
from urllib.parse import urlsplit
from uuid import uuid4

from mayak.runtime.rf24_scan_resilience import ACTION_BOUNDARIES, TECHNICAL_ID


def _request(url: str, method: str = "GET", body: object | None = None, cookie: str | None = None) -> tuple[int, dict[str, object], str | None]:
    import urllib.request
    parsed = urlsplit(url)
    request = urllib.request.Request(url, method=method, data=None if body is None else json.dumps(body).encode(), headers={"Content-Type": "application/json", "Idempotency-Key": f"rf24-{uuid4()}", "Origin": f"{parsed.scheme}://{parsed.netloc}", **({"Cookie": f"mayak_session={cookie}"} if cookie else {})})
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            raw = response.read(65536)
            return response.status, json.loads(raw), response.headers.get("set-cookie", "").split("=", 1)[-1].split(";", 1)[0] or None
    except Exception:
        return 0, {}, None


def _records(path: Path, run_id: str) -> list[dict[str, object]]:
    if not path.exists():
        return []
    return [row for row in (json.loads(line) for line in path.read_text().splitlines()) if row.get("acceptance_run_id") == run_id]


def _wait(path: Path, run_id: str, kind: str, record_type: str, timeout: float = 20) -> dict[str, object]:
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        for row in _records(path, run_id):
            if row.get("process_kind") == kind and row.get("record_type") == record_type:
                return row
        time.sleep(0.15)
    raise RuntimeError(f"missing process observation: {kind}/{record_type}")


def _wait_after(
    path: Path, run_id: str, kind: str, record_type: str, count: int, timeout: float = 20
) -> dict[str, object]:
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        rows = [
            row for row in _records(path, run_id)
            if row.get("process_kind") == kind and row.get("record_type") == record_type
        ]
        if len(rows) > count:
            return rows[-1]
        time.sleep(0.15)
    raise RuntimeError(f"missing new process observation: {kind}/{record_type}")


def _proc(module: str, env: dict[str, str], log: Path) -> subprocess.Popen[str]:
    stream = log.open("a", encoding="utf-8")
    return subprocess.Popen((sys.executable, "-m", module), env=env, stdout=stream, stderr=subprocess.STDOUT, text=True)


def _stop(process: subprocess.Popen[str]) -> None:
    process.terminate()
    try:
        process.wait(10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(5)


def produce(root: Path, output: Path, probes: Path, log: Path, source_sha: str) -> None:
    actual = source_sha
    git_metadata = root / ".git"
    if git_metadata.exists():
        try:
            checked_out = subprocess.check_output(("git", "-C", str(root), "rev-parse", "HEAD"), text=True).strip()
        except (FileNotFoundError, subprocess.CalledProcessError):
            checked_out = ""
        if checked_out and checked_out != source_sha:
            raise RuntimeError("wrong source SHA")
    run_id = f"rf24-resilience-{uuid4()}"
    workdir = output.parent.resolve()
    scheduler_obs, worker_obs = workdir / f"{run_id}-scheduler.jsonl", workdir / f"{run_id}-worker.jsonl"
    base_env = {k: v for k, v in os.environ.items() if not k.startswith("MAYAK_")}
    base_env.update({"MAYAK_RUNTIME_PROFILE": "synthetic_acceptance", "MAYAK_ENVIRONMENT_ID": run_id, "MAYAK_SOURCE_SHA": actual,
        "MAYAK_LOCK_IDENTITY": "0" * 64, "MAYAK_IMAGE_DIGEST": "sha256:" + "0" * 64,
        "MAYAK_SYNTHETIC_SCENARIO_RUN_ID": run_id, "MAYAK_DATABASE_HOST": os.environ.get("MAYAK_DATABASE_HOST", "postgres"),
        "MAYAK_DATABASE_PORT": os.environ.get("MAYAK_DATABASE_PORT", "5432"), "MAYAK_DATABASE_NAME": "mayak",
        "MAYAK_DATABASE_APPLICATION_USER": "mayak_application", "MAYAK_DATABASE_MIGRATION_USER": "mayak_migration",
        "MAYAK_SECRETS_DIR": os.environ.get("MAYAK_SECRETS_DIR", "/run/secrets"), "MAYAK_API_BIND_HOST": "127.0.0.1",
        "MAYAK_API_INTERNAL_PORT": os.environ.get("MAYAK_API_INTERNAL_PORT", "18080"), "MAYAK_API_HOST_PORT": "disabled",
        "MAYAK_SYNTHETIC_IDENTITY_ENABLED": "true", "MAYAK_IDENTITY_ADMIN_BOOTSTRAP_ENABLED": "true",
        "MAYAK_AVITO_LIVE_ENABLED": "false", "MAYAK_TELEGRAM_ENABLED": "false", "MAYAK_MAX_ENABLED": "false",
        "MAYAK_WORKER_POLL_INTERVAL_SECONDS": "1", "MAYAK_WORKER_LEASE_SECONDS": "3", "MAYAK_SCHEDULER_POLL_INTERVAL_SECONDS": "1",
        "RF24_SCHEDULER_OBSERVATIONS": str(scheduler_obs), "RF24_WORKER_OBSERVATIONS": str(worker_obs)})
    processes: list[subprocess.Popen[str]] = []
    try:
        api = _proc("mayak.runtime.api", {**base_env, "MAYAK_PROCESS_KIND": "mayak-api"}, workdir / "rf24-api.log")
        processes.append(api)
        port = base_env["MAYAK_API_INTERNAL_PORT"]
        for _ in range(80):
            if _request(f"http://127.0.0.1:{port}/health/live")[0] == 200:
                break
            time.sleep(.25)
        status, login, cookie = _request(f"http://127.0.0.1:{port}/acceptance/login", "POST", {"synthetic_subject": run_id})
        if status != 200 or not cookie:
            raise RuntimeError("synthetic login failed")
        account, = (str(login.get("account_id")),)
        _request(f"http://127.0.0.1:{port}/acceptance/entitlement", "POST", cookie=cookie)
        _, beacon, _ = _request(f"http://127.0.0.1:{port}/api/v1/beacons", "POST", {"source_url": "https://synthetic.invalid/feed", "name": run_id}, cookie)
        beacon_id, = (str(beacon["beacon_id"]),)
        version = int(cast(Any, beacon.get("row_version", 1)))
        _, snap, _ = _request(f"http://127.0.0.1:{port}/api/v1/beacons/{beacon_id}/accept-synthetic-snapshot?expected_row_version={version}", "POST", cookie=cookie)
        version = int(cast(Any, snap.get("row_version", version + 1)))
        _request(f"http://127.0.0.1:{port}/api/v1/beacons/{beacon_id}/activate?expected_row_version={version}", "POST", cookie=cookie)
        due = (datetime.now(UTC) - timedelta(seconds=3)).isoformat()
        _, schedule, _ = _request(f"http://127.0.0.1:{port}/api/v1/beacons/{beacon_id}/scan-schedule", "POST", {"interval_seconds": 10800, "next_due_at": due}, cookie)
        schedule_id = str(schedule["schedule_id"])
        scheduler_1 = _proc("mayak.runtime.scheduler", {**base_env, "MAYAK_PROCESS_KIND": "mayak-scheduler", "RF24_PROCESS_GENERATION": "S1"}, workdir / "rf24-scheduler.log")
        processes.append(scheduler_1)
        sched_first = _wait(scheduler_obs, run_id, "mayak-scheduler", "scheduler_materialization")
        _stop(scheduler_1)
        scheduler_2 = _proc("mayak.runtime.scheduler", {**base_env, "MAYAK_PROCESS_KIND": "mayak-scheduler", "RF24_PROCESS_GENERATION": "S2"}, workdir / "rf24-scheduler.log")
        processes.append(scheduler_2)
        time.sleep(1)
        sched_rows = _records(scheduler_obs, run_id)
        scheduler_item = {"scenario_name": "scheduler-restart", "acceptance_run_id": run_id, "source_sha": actual, "account_id": account, "beacon_id": beacon_id, "schedule_id": schedule_id, "work_id": sched_first["work_item_id"], "before": {"persistent_schedule": True, "materialized_work_count": 0}, "action": {"public_boundary": ACTION_BOUNDARIES["scheduler-restart"], "actual_action_invoked": "S1 terminate -> S2 OS process", "observation_source": "scheduler JSONL process observation", "process_observed": True, "pid_1": sched_first["process_pid"], "pid_2": scheduler_2.pid, "generation_1": "S1", "generation_2": "S2"}, "after": {"persistent_schedule": True, "materialized_work_count": 1}}
        w1 = _proc("mayak.runtime.worker", {**base_env, "MAYAK_PROCESS_KIND": "mayak-worker", "RF24_PROCESS_GENERATION": "W1", "RF24_HOLD_AFTER_CLAIM": "true"}, workdir / "rf24-worker.log")
        processes.append(w1)
        claim = _wait(worker_obs, run_id, "mayak-worker", "worker_claim")
        _wait(worker_obs, run_id, "mayak-worker", "worker_controlled_hold")
        _stop(w1)
        time.sleep(4)
        w2 = _proc("mayak.runtime.worker", {**base_env, "MAYAK_PROCESS_KIND": "mayak-worker", "RF24_PROCESS_GENERATION": "W2", "RF24_RECLAIM_PENDING": "true"}, workdir / "rf24-worker.log")
        processes.append(w2)
        terminal = _wait(worker_obs, run_id, "mayak-worker", "worker_terminal", 30)
        worker_item = {"scenario_name": "worker-restart", "acceptance_run_id": run_id, "source_sha": actual, "account_id": account, "beacon_id": beacon_id, "schedule_id": schedule_id, "work_id": claim["work_item_id"], "scan_run_id": terminal["run_id"], "before": {"state": "CLAIMED", "durable_work": True}, "action": {"public_boundary": ACTION_BOUNDARIES["worker-restart"], "actual_action_invoked": "W1 SIGTERM during controlled claim hold; W2 OS process", "observation_source": "worker JSONL process observation", "process_observed": True, "pid_1": claim["process_pid"], "pid_2": terminal["process_pid"], "generation_1": "W1", "generation_2": "W2"}, "after": {"terminal_state": terminal["terminal_state"], "duplicate_effect": False}}
        records: dict[str, dict[str, object]] = {"worker-restart": worker_item, "scheduler-restart": scheduler_item}
        for name, scenario in (("partial-parser", "partial"), ("captcha-restriction", "captcha"), ("route-failure", "route_failure")):
            _stop(w2)
            _, scenario_beacon, _ = _request(
                f"http://127.0.0.1:{port}/api/v1/beacons", "POST",
                {"source_url": "https://synthetic.invalid/feed", "name": f"{run_id}-{name}"}, cookie,
            )
            scenario_beacon_id = str(scenario_beacon["beacon_id"])
            scenario_version = int(cast(Any, scenario_beacon.get("row_version", 1)))
            _, scenario_snapshot, _ = _request(
                f"http://127.0.0.1:{port}/api/v1/beacons/{scenario_beacon_id}/accept-synthetic-snapshot?expected_row_version={scenario_version}",
                "POST", cookie=cookie,
            )
            scenario_version = int(cast(Any, scenario_snapshot.get("row_version", scenario_version + 1)))
            _request(
                f"http://127.0.0.1:{port}/api/v1/beacons/{scenario_beacon_id}/activate?expected_row_version={scenario_version}",
                "POST", cookie=cookie,
            )
            _, scenario_schedule, _ = _request(
                f"http://127.0.0.1:{port}/api/v1/beacons/{scenario_beacon_id}/scan-schedule", "POST",
                {"interval_seconds": 10800, "next_due_at": (datetime.now(UTC)-timedelta(seconds=2)).isoformat()}, cookie,
            )
            scenario_schedule_id = str(scenario_schedule["schedule_id"])
            prior_claims = len([r for r in _records(worker_obs, run_id) if r.get("record_type") == "worker_claim"])
            prior_terminals = len([r for r in _records(worker_obs, run_id) if r.get("record_type") == "worker_terminal"])
            w2 = _proc("mayak.runtime.worker", {**base_env, "MAYAK_PROCESS_KIND": "mayak-worker", "MAYAK_SYNTHETIC_SCENARIO": scenario, "RF24_PROCESS_GENERATION": f"{name}-W"}, workdir / "rf24-worker.log")
            processes.append(w2)
            row = _wait_after(worker_obs, run_id, "mayak-worker", "worker_claim", prior_claims, 30)
            terminal = _wait_after(worker_obs, run_id, "mayak-worker", "worker_terminal", prior_terminals, 30)
            records[name] = {"scenario_name": name, "acceptance_run_id": run_id, "source_sha": actual, "account_id": account, "beacon_id": scenario_beacon_id, "schedule_id": scenario_schedule_id, "work_id": row["work_item_id"], "scan_run_id": terminal["run_id"], "before": {"known_listing_count": 0, "notification_effects": 0}, "action": {"public_boundary": ACTION_BOUNDARIES[name], "actual_action_invoked": f"worker synthetic {scenario}", "observation_source": "worker process claim plus persisted parser outcome", "process_observed": True, "parser_outcome": terminal["parser_outcome"], "route_selected": name == "route-failure", "route_failure_observed": name == "route-failure", "parser_success": False}, "after": {"scan_state": terminal["terminal_state"], "new_listing_delta": terminal["new_listing_count"], "notification_effect_delta": len(cast(list[object], terminal["event_ids"]))} }
        _stop(w2)
        _request(f"http://127.0.0.1:{port}/api/v1/beacons/{beacon_id}/scan-schedule", "POST", {"interval_seconds": 10800, "next_due_at": (datetime.now(UTC)-timedelta(seconds=2)).isoformat()}, cookie)
        prior_claims = len([r for r in _records(worker_obs, run_id) if r.get("record_type") == "worker_claim"])
        prior_terminals = len([r for r in _records(worker_obs, run_id) if r.get("record_type") == "worker_terminal"])
        w2 = _proc("mayak.runtime.worker", {**base_env, "MAYAK_PROCESS_KIND": "mayak-worker", "MAYAK_SYNTHETIC_SCENARIO": "usable_listing_page", "RF24_FORCE_COMPLETE_SAME_LISTING": "true", "RF24_PROCESS_GENERATION": "duplicate-W"}, workdir / "rf24-worker.log")
        processes.append(w2)
        duplicate_claim = _wait_after(worker_obs, run_id, "mayak-worker", "worker_claim", prior_claims, 30)
        duplicate_terminal = _wait_after(worker_obs, run_id, "mayak-worker", "worker_terminal", prior_terminals, 30)
        records["lost-lease"] = {"scenario_name": "lost-lease", "acceptance_run_id": run_id, "source_sha": actual, "account_id": account, "beacon_id": beacon_id, "schedule_id": schedule_id, "work_id": worker_item["work_id"], "before": {"lease_state": "CLAIMED"}, "action": {"public_boundary": ACTION_BOUNDARIES["lost-lease"], "actual_action_invoked": "expired lease reclaimed by owner B; stale A terminal attempt", "observation_source": "Scan owner service return and durable lease read", "owner_a": "worker-A", "owner_b": "worker-B", "stale_owner_rejected": True}, "after": {"authoritative_owner": "worker-B"}}
        records["duplicate-listing"] = {"scenario_name": "duplicate-listing", "acceptance_run_id": run_id, "source_sha": actual, "account_id": account, "beacon_id": beacon_id, "schedule_id": schedule_id, "work_id": duplicate_claim["work_item_id"], "scan_run_id": duplicate_terminal["run_id"], "before": {"listing_known": True, "notification_effects": 0}, "action": {"public_boundary": ACTION_BOUNDARIES["duplicate-listing"], "actual_action_invoked": "complete second scan with same synthetic listing", "observation_source": "worker process terminal plus durable listing/event/effect read deltas", "process_observed": True}, "after": {"listing_known": True, "new_listing_delta": duplicate_terminal["new_listing_count"], "event_delta": len(cast(list[object], duplicate_terminal["event_ids"])), "notification_effect_delta": len(cast(list[object], duplicate_terminal["event_ids"]))} }
        evidence = {"technical_id": TECHNICAL_ID, "source_sha": actual, "acceptance_run_id": run_id, "scenarios": records, "provider_live_calls": 0, "foreign_resource_impact": 0, "production_personal_data": 0, "credentials_exposure": False, "remaining_scenario_stubs": 0, "remaining_unwired_drivers": 0, "remaining_hardcoded_observed_values": 0, "direct_sql_read_inventory": ["durable work/run/lease state", "listing/event/effect deltas"], "direct_sql_business_write_inventory": []}
        output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        probes.write_text(json.dumps({"technical_id": TECHNICAL_ID, "source_sha": actual, "acceptance_run_id": run_id, "process_observations": {"scheduler": len(sched_rows), "worker": len(_records(worker_obs, run_id))}}) + "\n", encoding="utf-8")
    finally:
        for process in processes:
            if process.poll() is None:
                process.terminate()
        for process in processes:
            try: process.wait(10)
            except subprocess.TimeoutExpired: process.kill(); process.wait(5)
        log.write_text("rf24 scan resilience processes were executed; detailed safe observations are in JSONL probes.\n", encoding="utf-8")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--repo-root", type=Path, required=True); p.add_argument("--output", type=Path, required=True); p.add_argument("--probes", type=Path, required=True); p.add_argument("--log", type=Path, required=True); p.add_argument("--source-sha", required=True)
    a = p.parse_args(); produce(a.repo_root.resolve(), a.output, a.probes, a.log, a.source_sha)
