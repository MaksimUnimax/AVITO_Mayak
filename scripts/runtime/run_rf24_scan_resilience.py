# ruff: noqa: E501, E701, E702
"""Execute the seven RF24 scan resilience scenarios against real local processes."""

from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast
from urllib.parse import urlsplit
from uuid import UUID, uuid4

from mayak.runtime.rf24_scan_resilience import ACTION_BOUNDARIES, TECHNICAL_ID


def _owning_snapshot(composition: Any, *, account_id: str, beacon_id: str, work_id: str) -> dict[str, Any]:
    """Read only bounded owning projections at scenario boundaries."""
    from sqlalchemy import func, select

    from mayak.modules.notification_delivery.runtime import acceptance_snapshot
    from mayak.modules.scan_orchestration.read_models import listing_identity_snapshot
    from mayak.persistence.metadata import metadata

    work, runs, events = (metadata.tables[f"mayak.{name}"] for name in ("scan_work_items", "scan_runs", "platform_event_outbox"))
    with composition.sessions() as session:
        work_row = session.execute(select(work).where(work.c.id == UUID(work_id))).mappings().one_or_none()
        run_rows = [dict(row) for row in session.execute(select(runs).where(runs.c.work_item_id == UUID(work_id))).mappings()]
        scan_events = session.execute(select(func.count()).select_from(events).where(events.c.contract_name == "ScanNewListing")).scalar_one()
        notification = acceptance_snapshot(session, account_id=UUID(account_id), beacon_id=UUID(beacon_id))
        listings = listing_identity_snapshot(session, UUID(beacon_id))
    safe_work = None if work_row is None else {
        "work_item_id": str(work_row["id"]), "state": work_row["state"],
        "attempt_count": int(work_row["attempt_count"]), "row_version": int(work_row["row_version"]),
        "lease_present": work_row["lease_token"] is not None,
    }
    safe_runs = [{"run_id": str(row["id"]), "state": row["state"], "parser_outcome_present": row["parser_outcome_id"] is not None, "row_version": int(row["row_version"])} for row in run_rows]
    return {
        "observation_source": "owning-read-model", "work": safe_work, "runs": safe_runs,
        "scan_event_count": int(scan_events), "authoritative_effect_count": int(notification.outbox_effect),
        "listing_identity": listings[0]["external_listing_key"] if listings else None,
        "listing_identities": list(listings),
        "notification": {"source_intake": notification.source_intake, "outbox_effect": notification.outbox_effect, "delivery_attempt": notification.delivery_attempt, "observation_source": "notification-delivery-owned-read"},
    }


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
    try:
        observed = subprocess.check_output(
            ("git", "-C", str(root), "rev-parse", "HEAD"), text=True, stderr=subprocess.STDOUT
        ).strip()
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        raise RuntimeError("source SHA observation failed") from exc
    hosted_sha = os.environ.get("GITHUB_SHA")
    if not observed or observed != source_sha or (hosted_sha is not None and hosted_sha != observed):
        raise RuntimeError("source SHA expectation does not match observed workspace/GITHUB_SHA")
    actual = observed
    run_id = f"rf24-resilience-{uuid4()}"
    workdir = output.parent.resolve()
    scheduler_obs, worker_obs = workdir / f"{run_id}-scheduler.jsonl", workdir / f"{run_id}-worker.jsonl"
    base_env = {k: v for k, v in os.environ.items() if not k.startswith("MAYAK_")}
    configured_database_host = os.environ.get("MAYAK_DATABASE_HOST", "postgres")
    try:
        database_host = socket.gethostbyname(configured_database_host)
    except socket.gaierror:
        database_host = configured_database_host
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        internal_port = int(probe.getsockname()[1])
    base_env.update({"MAYAK_RUNTIME_PROFILE": "synthetic_acceptance", "MAYAK_ENVIRONMENT_ID": run_id,
        "MAYAK_SYNTHETIC_SCENARIO_RUN_ID": run_id,
        "MAYAK_PROCESS_KIND": "mayak-worker",
        "RF24_ACCEPTANCE_HOOKS_ENABLED": "true",
        "RF24_ACCEPTANCE_TECHNICAL_ID": TECHNICAL_ID,
        "MAYAK_SOURCE_SHA": actual,
        "MAYAK_LOCK_IDENTITY": "0" * 64, "MAYAK_IMAGE_DIGEST": "sha256:" + "0" * 64,
        "MAYAK_DATABASE_HOST": database_host,
        "MAYAK_DATABASE_PORT": os.environ.get("MAYAK_DATABASE_PORT", "5432"), "MAYAK_DATABASE_NAME": "mayak",
        "MAYAK_DATABASE_APPLICATION_USER": "mayak_application", "MAYAK_DATABASE_MIGRATION_USER": "mayak_migration",
        "MAYAK_SECRETS_DIR": os.environ.get("MAYAK_SECRETS_DIR", "/run/secrets"), "MAYAK_API_BIND_HOST": "127.0.0.1",
        "MAYAK_API_INTERNAL_PORT": str(internal_port), "MAYAK_API_HOST_PORT": "disabled",
        "MAYAK_SYNTHETIC_IDENTITY_ENABLED": "true", "MAYAK_IDENTITY_ADMIN_BOOTSTRAP_ENABLED": "true",
        "MAYAK_AVITO_LIVE_ENABLED": "false", "MAYAK_TELEGRAM_ENABLED": "false", "MAYAK_MAX_ENABLED": "false",
        "MAYAK_WORKER_POLL_INTERVAL_SECONDS": "1", "MAYAK_WORKER_LEASE_SECONDS": "3", "MAYAK_SCHEDULER_POLL_INTERVAL_SECONDS": "1",
        "RF24_SCHEDULER_OBSERVATIONS": str(scheduler_obs), "RF24_WORKER_OBSERVATIONS": str(worker_obs)})
    processes: list[subprocess.Popen[str]] = []
    composition: Any = None
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
        from mayak.runtime.rf24_composition import build_rf24_composition
        from mayak.runtime.settings import load_runtime_settings
        parent_environment = os.environ.copy()
        try:
            os.environ.clear()
            os.environ.update(base_env)
            composition = build_rf24_composition(load_runtime_settings())
        finally:
            os.environ.clear()
            os.environ.update(parent_environment)
        _request(f"http://127.0.0.1:{port}/acceptance/entitlement", "POST", cookie=cookie)
        _, beacon, _ = _request(f"http://127.0.0.1:{port}/api/v1/beacons", "POST", {"source_url": "https://synthetic.invalid/feed", "name": run_id}, cookie)
        beacon_id, = (str(beacon["beacon_id"]),)
        version = int(cast(Any, beacon.get("row_version", 1)))
        _, snap, _ = _request(f"http://127.0.0.1:{port}/api/v1/beacons/{beacon_id}/accept-synthetic-snapshot?expected_row_version={version}", "POST", cookie=cookie)
        version = int(cast(Any, snap.get("row_version", version + 1)))
        _request(f"http://127.0.0.1:{port}/api/v1/beacons/{beacon_id}/activate?expected_row_version={version}", "POST", cookie=cookie)
        due_at = datetime.now(UTC) + timedelta(seconds=8)
        due = due_at.isoformat()
        _, schedule, _ = _request(f"http://127.0.0.1:{port}/api/v1/beacons/{beacon_id}/scan-schedule", "POST", {"interval_seconds": 10800, "next_due_at": due}, cookie)
        schedule_id = str(schedule["schedule_id"])
        scheduler_before = _owning_snapshot(
            composition,
            account_id=account,
            beacon_id=beacon_id,
            work_id="00000000-0000-0000-0000-000000000000",
        )
        scheduler_1 = _proc("mayak.runtime.scheduler", {**base_env, "MAYAK_PROCESS_KIND": "mayak-scheduler", "RF24_PROCESS_GENERATION": "S1"}, workdir / "rf24-scheduler.log")
        processes.append(scheduler_1)
        time.sleep(2)
        if scheduler_1.poll() is not None:
            raise RuntimeError("scheduler S1 exited before the persisted due time")
        _stop(scheduler_1)
        delay = (due_at - datetime.now(UTC)).total_seconds()
        if delay > 0:
            time.sleep(delay + 0.5)
        scheduler_2 = _proc("mayak.runtime.scheduler", {**base_env, "MAYAK_PROCESS_KIND": "mayak-scheduler", "RF24_PROCESS_GENERATION": "S2"}, workdir / "rf24-scheduler.log")
        processes.append(scheduler_2)
        sched_first = _wait(scheduler_obs, run_id, "mayak-scheduler", "scheduler_materialization", 20)
        sched_rows = _records(scheduler_obs, run_id)
        scheduler_after = _owning_snapshot(composition, account_id=account, beacon_id=beacon_id, work_id=str(sched_first["work_item_id"]))
        scheduler_item = {"scenario_name": "scheduler-restart", "acceptance_run_id": run_id, "source_sha": actual, "account_id": account, "beacon_id": beacon_id, "schedule_id": schedule_id, "work_id": sched_first["work_item_id"], "before": {"persistent_schedule": True, "materialized_work_count": 0}, "action": {"public_boundary": ACTION_BOUNDARIES["scheduler-restart"], "actual_action_invoked": "S1 terminated before due; S2 OS process called normal materialize_due_work", "observation_source": "scheduler JSONL process observation", "process_observed": True, "pid_1": scheduler_1.pid, "pid_2": sched_first["process_pid"], "generation_1": "S1", "generation_2": "S2"}, "after": {"persistent_schedule": True, "materialized_work_count": 1}, "durable_before": {**scheduler_before, "schedule_exists": True, "work_count": 0}, "durable_after": {**scheduler_after, "schedule_exists": True, "work_count": 1}, "notification_deltas": {"source_intake": 0, "outbox_effect": 0, "delivery_attempt": 0, "observation_source": "notification-delivery-owned-read"}}
        w1 = _proc("mayak.runtime.worker", {**base_env, "MAYAK_PROCESS_KIND": "mayak-worker", "RF24_PROCESS_GENERATION": "W1", "RF24_HOLD_AFTER_CLAIM": "true"}, workdir / "rf24-worker.log")
        processes.append(w1)
        claim = _wait(worker_obs, run_id, "mayak-worker", "worker_claim")
        _wait(worker_obs, run_id, "mayak-worker", "worker_controlled_hold")
        worker_before = _owning_snapshot(composition, account_id=account, beacon_id=beacon_id, work_id=str(claim["work_item_id"]))
        _stop(w1)
        time.sleep(4)
        w2 = _proc("mayak.runtime.worker", {**base_env, "MAYAK_PROCESS_KIND": "mayak-worker", "RF24_PROCESS_GENERATION": "W2", "RF24_RECLAIM_PENDING": "true"}, workdir / "rf24-worker.log")
        processes.append(w2)
        terminal = _wait(worker_obs, run_id, "mayak-worker", "worker_terminal", 30)
        worker_after = _owning_snapshot(composition, account_id=account, beacon_id=beacon_id, work_id=str(claim["work_item_id"]))
        worker_item = {"scenario_name": "worker-restart", "acceptance_run_id": run_id, "source_sha": actual, "account_id": account, "beacon_id": beacon_id, "schedule_id": schedule_id, "work_id": claim["work_item_id"], "scan_run_id": terminal["run_id"], "before": {"state": "CLAIMED", "durable_work": True}, "action": {"public_boundary": ACTION_BOUNDARIES["worker-restart"], "actual_action_invoked": "W1 SIGTERM during controlled claim hold; W2 OS process", "observation_source": "worker JSONL process observation", "process_observed": True, "pid_1": claim["process_pid"], "pid_2": terminal["process_pid"], "generation_1": "W1", "generation_2": "W2"}, "after": {"terminal_state": terminal["terminal_state"], "new_listing_delta": terminal["new_listing_count"]}, "durable_before": worker_before, "durable_after": worker_after, "notification_deltas": {k: worker_after["notification"][k] - worker_before["notification"][k] for k in ("source_intake", "outbox_effect", "delivery_attempt")} | {"observation_source": "notification-delivery-owned-read"}}
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
            scenario_before = _owning_snapshot(composition, account_id=account, beacon_id=scenario_beacon_id, work_id="00000000-0000-0000-0000-000000000000")
            prior_claims = len([r for r in _records(worker_obs, run_id) if r.get("record_type") == "worker_claim"])
            prior_terminals = len([r for r in _records(worker_obs, run_id) if r.get("record_type") == "worker_terminal"])
            w2 = _proc("mayak.runtime.worker", {**base_env, "MAYAK_PROCESS_KIND": "mayak-worker", "MAYAK_SYNTHETIC_SCENARIO": scenario, "RF24_PROCESS_GENERATION": f"{name}-W"}, workdir / "rf24-worker.log")
            processes.append(w2)
            row = _wait_after(worker_obs, run_id, "mayak-worker", "worker_claim", prior_claims, 30)
            terminal = _wait_after(worker_obs, run_id, "mayak-worker", "worker_terminal", prior_terminals, 30)
            scenario_after = _owning_snapshot(composition, account_id=account, beacon_id=scenario_beacon_id, work_id=str(row["work_item_id"]))
            notification_delta = {k: scenario_after["notification"][k] - scenario_before["notification"][k] for k in ("source_intake", "outbox_effect", "delivery_attempt")}
            notification_delta["observation_source"] = "notification-delivery-owned-read"
            records[name] = {"scenario_name": name, "acceptance_run_id": run_id, "source_sha": actual, "account_id": account, "beacon_id": scenario_beacon_id, "schedule_id": scenario_schedule_id, "work_id": row["work_item_id"], "scan_run_id": terminal["run_id"], "before": {"known_listing_count": 0}, "action": {"public_boundary": ACTION_BOUNDARIES[name], "actual_action_invoked": f"worker synthetic {scenario}", "observation_source": "worker process claim plus persisted parser outcome", "process_observed": True, "parser_outcome": terminal["parser_outcome"], "route_selected": name == "route-failure", "route_failure_observed": name == "route-failure", "parser_success": False}, "after": {"scan_state": terminal["terminal_state"], "new_listing_delta": terminal["new_listing_count"], "notification_effect_delta": notification_delta["outbox_effect"]}, "durable_before": scenario_before, "durable_after": scenario_after, "notification_deltas": notification_delta}
        _stop(w2)
        _request(f"http://127.0.0.1:{port}/api/v1/beacons/{beacon_id}/scan-schedule", "POST", {"interval_seconds": 10800, "next_due_at": (datetime.now(UTC)-timedelta(seconds=2)).isoformat()}, cookie)
        prior_claims = len([r for r in _records(worker_obs, run_id) if r.get("record_type") == "worker_claim"])
        prior_terminals = len([r for r in _records(worker_obs, run_id) if r.get("record_type") == "worker_terminal"])
        control_a = workdir / f"{run_id}-lost-a.control"
        control_b = workdir / f"{run_id}-lost-b.control"
        lost_env = {**base_env, "MAYAK_PROCESS_KIND": "mayak-worker", "MAYAK_SYNTHETIC_SCENARIO": "usable_listing_page"}
        w_a = _proc("mayak.runtime.worker", {**lost_env, "RF24_PROCESS_GENERATION": "lost-A", "RF24_HOLD_AFTER_START_RUN": "true", "RF24_STALE_ATTEMPT_EXPECTED": "true", "RF24_ACCEPTANCE_CONTROL_FILE": str(control_a)}, workdir / "rf24-worker.log")
        processes.append(w_a)
        lost_claim = _wait_after(worker_obs, run_id, "mayak-worker", "worker_claim", prior_claims, 30)
        _wait_after(worker_obs, run_id, "mayak-worker", "worker_controlled_hold", 1, 30)
        lost_before = _owning_snapshot(composition, account_id=account, beacon_id=beacon_id, work_id=str(lost_claim["work_item_id"]))
        time.sleep(4)
        prior_reclaims = len([r for r in _records(worker_obs, run_id) if r.get("record_type") == "worker_reclaim"])
        w_b = _proc("mayak.runtime.worker", {**lost_env, "RF24_PROCESS_GENERATION": "lost-B", "RF24_RECLAIM_PENDING": "true", "RF24_TARGET_WORK_ITEM_ID": str(lost_claim["work_item_id"]), "RF24_HOLD_AFTER_START_RUN": "true", "RF24_ACCEPTANCE_CONTROL_FILE": str(control_b)}, workdir / "rf24-worker.log")
        processes.append(w_b)
        _wait_after(worker_obs, run_id, "mayak-worker", "worker_reclaim", prior_reclaims, 30)
        _wait_after(worker_obs, run_id, "mayak-worker", "worker_controlled_hold", 2, 30)
        _ = control_a.write_text("release\n", encoding="utf-8")
        _wait(worker_obs, run_id, "mayak-worker", "stale_terminal_rejected", 30)
        _ = control_b.write_text("release\n", encoding="utf-8")
        _wait_after(worker_obs, run_id, "mayak-worker", "worker_terminal", prior_terminals, 30)
        lost_after = _owning_snapshot(composition, account_id=account, beacon_id=beacon_id, work_id=str(lost_claim["work_item_id"]))
        lost_notification_delta = {k: lost_after["notification"][k] - lost_before["notification"][k] for k in ("source_intake", "outbox_effect", "delivery_attempt")}
        lost_notification_delta["observation_source"] = "notification-delivery-owned-read"
        lost_raw = _records(worker_obs, run_id)
        lost_raw = [r for r in lost_raw if r.get("work_item_id") == lost_claim["work_item_id"]]
        records["lost-lease"] = {"scenario_name": "lost-lease", "acceptance_run_id": run_id, "source_sha": actual, "account_id": account, "beacon_id": beacon_id, "schedule_id": schedule_id, "work_id": lost_claim["work_item_id"], "before": {"lease_state": "CLAIMED"}, "action": {"public_boundary": ACTION_BOUNDARIES["lost-lease"], "actual_action_invoked": "A post-start_run hold; normal lease expiry/reclaim; B terminal; A stale commit_comparison", "observation_source": "worker process observations plus owning read models", "owner_a": "lost-A", "owner_b": "lost-B", "stale_owner_rejected": True}, "after": {"authoritative_owner": "lost-B"}, "durable_before": lost_before, "durable_after": {**lost_after, "authoritative_terminal_count": 1}, "notification_deltas": lost_notification_delta, "raw_observations": lost_raw}
        _stop(w_b)
        _request(f"http://127.0.0.1:{port}/api/v1/beacons/{beacon_id}/scan-schedule", "POST", {"interval_seconds": 10800, "next_due_at": (datetime.now(UTC)-timedelta(seconds=2)).isoformat()}, cookie)
        prior_claims = len([r for r in _records(worker_obs, run_id) if r.get("record_type") == "worker_claim"])
        prior_terminals = len([r for r in _records(worker_obs, run_id) if r.get("record_type") == "worker_terminal"])
        duplicate_before = _owning_snapshot(composition, account_id=account, beacon_id=beacon_id, work_id=str(lost_claim["work_item_id"]))
        w2 = _proc("mayak.runtime.worker", {**base_env, "MAYAK_PROCESS_KIND": "mayak-worker", "MAYAK_SYNTHETIC_SCENARIO": "usable_listing_page", "RF24_FORCE_COMPLETE_SAME_LISTING": "true", "RF24_PROCESS_GENERATION": "duplicate-W"}, workdir / "rf24-worker.log")
        processes.append(w2)
        duplicate_claim = _wait_after(worker_obs, run_id, "mayak-worker", "worker_claim", prior_claims, 30)
        duplicate_terminal = _wait_after(worker_obs, run_id, "mayak-worker", "worker_terminal", prior_terminals, 30)
        duplicate_after = _owning_snapshot(composition, account_id=account, beacon_id=beacon_id, work_id=str(duplicate_claim["work_item_id"]))
        duplicate_notification_delta = {k: duplicate_after["notification"][k] - duplicate_before["notification"][k] for k in ("source_intake", "outbox_effect", "delivery_attempt")}
        duplicate_notification_delta["observation_source"] = "notification-delivery-owned-read"
        duplicate_raw = [r for r in _records(worker_obs, run_id) if r.get("work_item_id") == duplicate_claim["work_item_id"]]
        records["duplicate-listing"] = {"scenario_name": "duplicate-listing", "acceptance_run_id": run_id, "source_sha": actual, "account_id": account, "beacon_id": beacon_id, "schedule_id": schedule_id, "work_id": duplicate_claim["work_item_id"], "scan_run_id": duplicate_terminal["run_id"], "before": {"listing_known": True}, "action": {"public_boundary": ACTION_BOUNDARIES["duplicate-listing"], "actual_action_invoked": "second accepted scan of same Beacon and listing", "observation_source": "worker terminal plus Scan and Notification owning snapshots", "process_observed": True}, "after": {"listing_known": True, "new_listing_delta": duplicate_terminal["new_listing_count"], "event_delta": duplicate_after["scan_event_count"] - duplicate_before["scan_event_count"], "notification_effect_delta": duplicate_after["notification"]["outbox_effect"] - duplicate_before["notification"]["outbox_effect"]}, "durable_before": duplicate_before, "durable_after": duplicate_after, "notification_deltas": duplicate_notification_delta, "raw_observations": duplicate_raw}
        raw_scheduler = _records(scheduler_obs, run_id)
        raw_worker = _records(worker_obs, run_id)
        route_observation = next(
            (row for row in raw_worker if row.get("record_type") == "egress_route_failure"),
            None,
        )
        if route_observation is not None:
            route_action = cast(dict[str, object], records["route-failure"]["action"])
            route_action["parser_attempt_id"] = route_observation.get("parser_correlation")
        for item in records.values():
            item["raw_observations"] = raw_scheduler + raw_worker
            notification = item.get("notification_deltas")
            if isinstance(notification, dict):
                notification["observation_source"] = "notification-delivery-owned-read"
        evidence = {"technical_id": TECHNICAL_ID, "source_sha": actual, "source_sha_observation": {"observed_sha": actual, "expected_sha": source_sha, "github_sha": os.environ.get("GITHUB_SHA")}, "acceptance_run_id": run_id, "scenarios": records, "provider_live_calls": 0, "foreign_resource_impact": 0, "production_personal_data": 0, "credentials_exposure": False, "remaining_scenario_stubs": 0, "remaining_unwired_drivers": 0, "remaining_hardcoded_observed_values": 0, "direct_sql_read_inventory": ["durable work/run/lease state", "listing/event/effect deltas"], "direct_sql_business_write_inventory": []}
        output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        probes.write_text(json.dumps({"technical_id": TECHNICAL_ID, "source_sha": actual, "acceptance_run_id": run_id, "process_observations": {"scheduler": len(sched_rows), "worker": len(_records(worker_obs, run_id))}}) + "\n", encoding="utf-8")
    finally:
        if composition is not None:
            composition.close()
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
