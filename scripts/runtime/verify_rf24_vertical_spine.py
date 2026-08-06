# ruff: noqa: E501
"""Independent, fail-closed verifier for structured RF24 spine evidence."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

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

    schedules = data.get("scheduler_cycles")
    workers = data.get("worker_cycles")
    _require(isinstance(schedules, list) and len(schedules) >= 2, "two scheduler cycles missing")
    _require(isinstance(workers, list) and len(workers) >= 2, "two worker cycles missing")
    first, second = schedules[0], schedules[1]
    _require(all(isinstance(item, dict) for item in (first, second)), "malformed scheduler cycles")
    _require(first.get("cycle") == 1 and second.get("cycle") == 2, "scheduler cycle numbering missing")
    _require(first.get("work_state") and second.get("work_state"), "scheduler materialization state missing")
    _require(first.get("schedule_id") and first.get("schedule_id") == second.get("schedule_id"), "schedule provenance mismatch")
    _require(first.get("work_item_id") and second.get("work_item_id") and first.get("work_item_id") != second.get("work_item_id"), "distinct scheduler work IDs missing")
    _require(workers[0].get("claimed_work_item_id") == first.get("work_item_id") and workers[1].get("claimed_work_item_id") == second.get("work_item_id"), "worker claim provenance mismatch")
    _require(workers[0].get("run_id") == first.get("run_id") and workers[1].get("run_id") == second.get("run_id"), "worker run provenance mismatch")

    scans = data.get("scan_cycles")
    _require(isinstance(scans, list) and len(scans) >= 2, "scan cycles missing")
    _require(scans[0].get("state") == "SUCCEEDED_BASELINE" and scans[0].get("notification_delta") == 0, "baseline invariant missing")
    _require(scans[1].get("state") == "SUCCEEDED_DIFFERENCE" and scans[1].get("new_listing_count") == 1 and scans[1].get("scan_new_listing_event_count") == 1, "difference invariant missing")

    notification = data.get("notification")
    telegram = data.get("telegram")
    _require(bool(isinstance(notification, dict) and notification.get("event_id") and notification.get("effect_count") == 1), "generic notification effect missing")
    _require(isinstance(telegram, dict) and telegram.get("fake_delivery_committed") is True and telegram.get("live_provider_calls") == 0 and notification.get("telegram_attempt_count") == 1, "Telegram proof missing")
    web = data.get("web_status_read_model")
    cabinet = data.get("web_cabinet")
    _require(isinstance(web, dict) and web.get("web_delivery_mode") == "WEB_STATUS_READ_MODEL" and web.get("web_event_id") == notification.get("event_id") and web.get("web_visible") is True, "Web read-model proof missing")
    _require(isinstance(cabinet, dict) and cabinet.get("status") == 200 and cabinet.get("target_state_visible") is True and cabinet.get("notification_event_id") == notification.get("event_id") and cabinet.get("account_id") == web.get("web_account_id") and cabinet.get("beacon_id") == web.get("web_beacon_id"), "Web Cabinet target binding missing")
    admin = data.get("admin_diagnostics")
    _require(isinstance(admin, dict) and admin.get("authenticated") is True and admin.get("authorized") is True and admin.get("target_diagnostics_visible") is True, "authorized Admin diagnostics missing")
    _require(admin.get("operator_account_id") and admin.get("target_account_id") and admin.get("target_account_id") == web.get("web_account_id") and admin.get("beacon_id") == web.get("web_beacon_id") and admin.get("notification_event_id") == notification.get("event_id"), "Admin target binding missing")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--source-sha", required=True)
    args = parser.parse_args()
    verify(args.evidence, args.source_sha)
    print("RF24_SPINE_VERIFIER=PASS")
