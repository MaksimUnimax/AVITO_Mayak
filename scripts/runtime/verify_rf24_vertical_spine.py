# ruff: noqa: E501
"""Independent, fail-closed verifier for structured RF24 spine evidence."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, cast

_AUTH_KEY = re.compile(r"(?:authorization|proxy.?authorization|cookie|set.?cookie|session.?token|access.?token|refresh.?token|password)", re.I)
_AUTH_VALUE = re.compile(r"(?:bearer\s+\S+|mayak_session=\S+|postgres(?:ql)?://[^\s:@/]+:[^\s@/]+@|-----BEGIN [A-Z ]+PRIVATE KEY-----)", re.I)
_EMPTY = {None, "", False, "redacted", "removed", "none", "null"}


def _credential_in(value: object, *, key: str = "") -> bool:
    if isinstance(value, dict):
        for name, item in value.items():
            normalized = str(name).lower().replace("-", "_")
            if _AUTH_KEY.search(normalized) and item not in _EMPTY and item is not True:
                return True
            if _credential_in(item, key=normalized):
                return True
        return False
    if isinstance(value, list):
        return any(_credential_in(item, key=key) for item in value)
    if isinstance(value, str):
        return bool(_AUTH_VALUE.search(value))
    return False


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def verify(path: Path, source_sha: str) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    _require(isinstance(data, dict), "evidence is not an object")
    _require(data.get("source_sha") == source_sha, "evidence source SHA mismatch")
    _require(isinstance(data.get("run_id"), str) and bool(data["run_id"]), "missing run ID")
    _require(data.get("api_bind") == "127.0.0.1" and data.get("postgres_host_published") is False, "runtime boundary is not local-only")
    _require(data.get("provider_live_calls") == 0 and data.get("foreign_resource_impact") == 0 and data.get("production_personal_data") == 0, "unsafe runtime impact")
    _require(data.get("credentials_exposure") is False, "credentials_exposure must be false")
    security = data.get("security")
    _require(isinstance(security, dict) and security.get("credentials_exposure") is False and security.get("serialized_cookie_value_present") is False and security.get("authorization_material_present") is False, "security boundary is not proven")
    _require(not _credential_in(data), "credential-bearing evidence material")

    processes = data.get("processes")
    _require(isinstance(processes, list), "process identities missing")
    kinds = {item.get("kind") for item in processes if isinstance(item, dict)}
    valid_pids = all(
        isinstance(item.get("pid"), int) and int(item["pid"]) > 0
        for item in processes if isinstance(item, dict)
    )
    _require({"api", "worker", "scheduler"} <= kinds and valid_pids, "distinct process spine missing")

    processes = {item.get("kind"): item for item in data.get("processes", []) if isinstance(item, dict)}
    _require(all(kind in processes and isinstance(processes[kind].get("pid"), int) for kind in ("api", "worker", "scheduler")), "process identities missing")
    run_id = data["run_id"]
    scheduler = [item for item in data.get("scheduler_observations", []) if isinstance(item, dict)]
    scheduler = [item for item in scheduler if item.get("record_type") == "scheduler_materialization" and item.get("materialized_count", 0) >= 1]
    _require(len(scheduler) >= 2, "two positive scheduler observations missing")
    first, second = scheduler[0], scheduler[1]
    _require(all(item.get("acceptance_run_id") == run_id and item.get("process_kind") == "mayak-scheduler" and item.get("process_pid") == processes["scheduler"].get("pid") for item in (first, second)), "scheduler process identity mismatch")
    _require(bool(first.get("schedule_id") == second.get("schedule_id") and first.get("work_item_id") != second.get("work_item_id")), "scheduler work correlation missing")
    _require(bool(first.get("work_item_id") and second.get("work_item_id") and first.get("materialized_count", 0) >= 1 and second.get("materialized_count", 0) >= 1), "scheduler materialization is not observed")
    workers = [item for item in data.get("worker_observations", []) if isinstance(item, dict)]
    claims = {item.get("work_item_id"): item for item in workers if item.get("record_type") == "worker_claim"}
    terminals = {item.get("work_item_id"): item for item in workers if item.get("record_type") == "worker_terminal"}
    _require(all(work in claims and work in terminals for work in (first["work_item_id"], second["work_item_id"])), "worker process observations missing")
    for item in (claims[first["work_item_id"]], claims[second["work_item_id"]], terminals[first["work_item_id"]], terminals[second["work_item_id"]]):
        _require(item.get("acceptance_run_id") == run_id and item.get("process_kind") == "mayak-worker" and item.get("process_pid") == processes["worker"].get("pid"), "worker process identity mismatch")
    _require(terminals[first["work_item_id"]].get("terminal_state") == "SUCCEEDED_BASELINE" and terminals[second["work_item_id"]].get("terminal_state") == "SUCCEEDED_DIFFERENCE", "terminal states missing")
    durable = {item.get("work_item_id"): item for item in data.get("durable_provenance", []) if isinstance(item, dict)}
    first_work = str(first["work_item_id"])
    second_work = str(second["work_item_id"])
    _require(all(work in durable and durable[work].get("schedule_id") == first.get("schedule_id") for work in (first_work, second_work)), "durable work correlation missing")
    _require(all(durable[work].get("run_id") == terminals[work].get("run_id") for work in (first_work, second_work)), "durable terminal correlation missing")

    snapshots = cast(dict[str, Any], data.get("before_after"))
    _require(isinstance(snapshots, dict), "before/after snapshots missing")
    def delta(name: str, phase: str) -> int:
        section = snapshots.get(phase, {})
        before = section.get("before", {}).get(name, [])
        after = section.get("after", {}).get(name, [])
        return len(set(map(str, after)) - set(map(str, before)))
    _require(all(delta(name, "baseline") == 0 for name in ("scan_new_listing_events", "notification_events", "outbox_records", "delivery_attempts")), "baseline deltas were not observed as zero")
    _require(delta("listing_identities", "difference") == 1 and delta("scan_new_listing_events", "difference") == 1 and delta("notification_events", "difference") == 1 and delta("outbox_records", "difference") == 1 and delta("delivery_attempts", "difference") == 1, "difference deltas were not observed")
    scans = data.get("scan_cycles")
    _require(isinstance(scans, list) and len(scans) >= 2 and scans[0].get("state") == "SUCCEEDED_BASELINE" and scans[1].get("state") == "SUCCEEDED_DIFFERENCE", "scan terminal observations missing")
    _require(scans[0].get("new_listing_count") == 0 and scans[1].get("new_listing_count") == 1, "comparison result is not observed")
    event_ids = cast(Any, terminals[second["work_item_id"]].get("event_ids"))
    _require(isinstance(event_ids, list) and len(event_ids) == 1, "actual Scan event identity missing")
    scan_event_id = event_ids[0]
    notification = data.get("notification")
    event_id = notification.get("event_id") if isinstance(notification, dict) else None
    _require(isinstance(notification, dict) and notification.get("event_id") != scan_event_id and notification.get("source_event_id") == scan_event_id, "Notification source identity mismatch")
    telegram = data.get("telegram")
    _require(isinstance(telegram, dict) and telegram.get("live_provider_calls") == 0 and telegram.get("blind_retries") == 0 and telegram.get("delivery_status") == "DELIVERED" and telegram.get("channel_class") == "TELEGRAM", "Telegram durable outcome missing")
    web = data.get("web_status_read_model")
    _require(bool(isinstance(web, dict) and web.get("web_delivery_mode") == "WEB_STATUS_READ_MODEL" and web.get("web_event_id") == event_id and web.get("web_source_event_id") == scan_event_id and web.get("web_listing_reference") and web.get("web_visible") is True), "Web read-model proof missing")
    cabinet = data.get("web_cabinet")
    cabinet_response = cabinet.get("response") if isinstance(cabinet, dict) else None
    cabinet_refs = cabinet_response.get("opaque_references", []) if isinstance(cabinet_response, dict) else []
    _require(isinstance(cabinet, dict) and cabinet.get("status") == 200 and cabinet.get("target_state_visible") is True and cabinet.get("notification_event_id") == event_id and cabinet.get("account_id") == web.get("web_account_id") and cabinet.get("beacon_id") == web.get("web_beacon_id") and cabinet.get("account_id") in cabinet_refs and cabinet.get("beacon_id") in cabinet_refs, "Web Cabinet target binding missing")
    admin = data.get("admin_diagnostics")
    admin_response = admin.get("response") if isinstance(admin, dict) else None
    admin_refs = admin_response.get("opaque_references", []) if isinstance(admin_response, dict) else []
    target = admin.get("target_observation") if isinstance(admin, dict) else None
    _require(isinstance(admin, dict) and admin.get("status") == 200 and admin.get("authenticated") is True and admin.get("authorized") is True and admin.get("target_diagnostics_visible") is True and admin.get("notification_event_id") == event_id and admin.get("scan_event_id") == scan_event_id and admin.get("baseline_run_id") == terminals[first["work_item_id"]].get("run_id") and admin.get("difference_run_id") == terminals[second["work_item_id"]].get("run_id") and admin.get("target_account_id") in admin_refs and isinstance(target, dict) and target.get("beacon_id") == web.get("web_beacon_id") and target.get("scan_event_id") == scan_event_id, "authorized Admin diagnostics missing")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--source-sha", required=True)
    args = parser.parse_args()
    verify(args.evidence, args.source_sha)
    print("RF24_SPINE_VERIFIER=PASS")
