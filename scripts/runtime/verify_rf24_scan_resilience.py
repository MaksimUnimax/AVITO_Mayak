# ruff: noqa: E501
"""Independent, fail-closed verifier for scenario-local RF24 evidence."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, cast

from mayak.runtime.rf24_scan_resilience import ACTION_BOUNDARIES, SCENARIO_NAMES, TECHNICAL_ID

SECRET_KEY = re.compile(
    r"(?:cookie|set-cookie|authorization|bearer|access[_-]?token|refresh[_-]?token|session[_-]?token|password)",
    re.I,
)
SECRET_VALUE = re.compile(
    r"(?:bearer\s+\S+|mayak_session=\S+|postgres(?:ql)?://[^\s:@/]+:[^\s@/]+@|-----BEGIN [A-Z ]+PRIVATE KEY-----)",
    re.I,
)


def _unsafe(value: object) -> bool:
    if isinstance(value, dict):
        return any(
            (
                SECRET_KEY.search(str(k))
                and v not in (None, "", False, True, "<redacted>", "removed")
            )
            or _unsafe(v)
            for k, v in value.items()
        )
    if isinstance(value, list):
        return any(_unsafe(v) for v in value)
    return isinstance(value, str) and bool(SECRET_VALUE.search(value))


def _require(condition: object, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _rows(raw: list[dict[str, Any]], record_type: str, **match: object) -> list[dict[str, Any]]:
    return [
        r
        for r in raw
        if r.get("record_type") == record_type and all(r.get(k) == v for k, v in match.items())
    ]


def _base(
    name: str, item: dict[str, Any], run_id: str
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any], dict[str, Any]]:
    _require(item.get("scenario_name") == name, f"{name}: identity mismatch")
    keys = (
        "acceptance_run_id",
        "source_sha",
        "account_id",
        "beacon_id",
        "schedule_id",
        "work_id",
    ) + (() if name == "scheduler-restart" else ("scan_run_id",))
    for key in keys:
        _require(
            bool(item.get(key)) and (key != "acceptance_run_id" or item.get(key) == run_id),
            f"{name}: missing {key}",
        )
    _require(
        item.get("action", {}).get("public_boundary") == ACTION_BOUNDARIES[name],
        f"{name}: wrong boundary",
    )
    raw = item.get("raw_observations")
    before, after, notification = (
        item.get("durable_before"),
        item.get("durable_after"),
        item.get("notification_deltas"),
    )
    _require(isinstance(raw, list) and raw, f"{name}: scenario-local raw observations missing")
    _require(
        isinstance(before, dict) and isinstance(after, dict), f"{name}: owning snapshots missing"
    )
    _require(isinstance(notification, dict), f"{name}: notification authority missing")
    raw = cast(list[dict[str, Any]], raw)
    before = cast(dict[str, Any], before)
    after = cast(dict[str, Any], after)
    notification = cast(dict[str, Any], notification)
    _require(
        before.get("observation_source") == "owning-read-model"
        and after.get("observation_source") == "owning-read-model",
        f"{name}: non-owning durable snapshot",
    )
    _require(
        notification.get("observation_source") == "notification-delivery-owned-read",
        f"{name}: non-owning notification snapshot",
    )
    bn, an = before.get("notification", {}), after.get("notification", {})
    for key in ("source_intake", "outbox_effect", "delivery_attempt"):
        _require(
            notification.get(key) == an.get(key, -1) - bn.get(key, -1),
            f"{name}: notification delta not recomputed",
        )
    for row in raw:
        _require(
            row.get("technical_id") == TECHNICAL_ID and row.get("acceptance_run_id") == run_id,
            f"{name}: raw identity mismatch",
        )
        _require(
            isinstance(row.get("process_pid"), int) and row["process_pid"] > 0,
            f"{name}: process PID missing",
        )
        _require(
            isinstance(row.get("process_generation"), str)
            and row["process_generation"] not in {"", "unknown"},
            f"{name}: process generation missing",
        )
    return raw, before, after, notification


def _zero_effects(
    name: str, item: dict[str, Any], before: dict[str, Any], after: dict[str, Any]
) -> None:
    _require(
        after.get("scan_event_count", 0) - before.get("scan_event_count", 0) == 0,
        f"{name}: Scan event effect",
    )
    _require(
        item.get("notification_deltas", {}).get("source_intake") == 0
        and item.get("notification_deltas", {}).get("outbox_effect") == 0
        and item.get("notification_deltas", {}).get("delivery_attempt") == 0,
        f"{name}: notification effect",
    )


def _scenario(name: str, item: dict[str, Any], run_id: str) -> None:
    raw, before, after, _ = _base(name, item, run_id)
    work, scan_run = item["work_id"], item.get("scan_run_id")
    if name == "scheduler-restart":
        s1 = _rows(raw, "scheduler_process_started", process_generation="S1")
        s1_stop = _rows(raw, "scheduler_process_stopped", process_generation="S1")
        s2 = _rows(raw, "scheduler_process_started", process_generation="S2")
        s2_stop = _rows(raw, "scheduler_process_stopped", process_generation="S2")
        mats = [
            r
            for r in _rows(raw, "scheduler_materialization")
            if r.get("schedule_id") == item["schedule_id"]
            and r.get("work_item_id") == work
            and r.get("beacon_id") == item["beacon_id"]
        ]
        _require(
            len(s1) == len(s1_stop) == len(s2) == len(s2_stop) == 1 and len(mats) == 1,
            "scheduler lifecycle incomplete",
        )
        _require(
            s1[0]["process_pid"] != s2[0]["process_pid"]
            and s1[0]["process_generation"] != s2[0]["process_generation"],
            "scheduler identity reused",
        )
        _require(
            mats[0]["process_pid"] == s2[0]["process_pid"]
            and mats[0]["process_generation"] == "S2"
            and mats[0].get("materialized_count", 0) == 1,
            "scheduler materialization is not S2-correlated",
        )
        _require(
            not _rows(raw, "scheduler_materialization", process_generation="S1", work_item_id=work),
            "S1 materialized target work",
        )
        _require(
            before.get("schedule_exists") is True
            and before.get("work_count") == 0
            and after.get("work_count") == 1,
            "scheduler owning state mismatch",
        )
    elif name == "worker-restart":
        w1 = _rows(raw, "worker_process_started", process_generation="W1")
        w2 = _rows(raw, "worker_process_started", process_generation="W2")
        _require(
            len(w1) == len(w2) == 1 and w1[0]["process_pid"] != w2[0]["process_pid"],
            "worker process identities not raw-derived",
        )
        _require(
            _rows(raw, "worker_process_stopped", process_generation="W1")
            and _rows(raw, "worker_process_stopped", process_generation="W2"),
            "worker exit proof missing",
        )
        _require(
            _rows(raw, "worker_claim", process_generation="W1", work_item_id=work)
            and _rows(raw, "worker_controlled_hold", process_generation="W1", work_item_id=work),
            "W1 claim/hold missing",
        )
        _require(
            _rows(raw, "worker_claim", process_generation="W2", work_item_id=work)
            and _rows(raw, "worker_reclaim", process_generation="W2", work_item_id=work),
            "W2 reclaim missing",
        )
        terminals = _rows(
            raw, "worker_terminal", process_generation="W2", work_item_id=work, run_id=scan_run
        )
        _require(
            len(terminals) == 1
            and terminals[0].get("terminal_state")
            in {"SUCCEEDED_BASELINE", "SUCCEEDED_DIFFERENCE"},
            "W2 terminal missing",
        )
        _require(
            after.get("authoritative_effect_count") == before.get("authoritative_effect_count"),
            "worker restart notification effect",
        )
    elif name in {"partial-parser", "captcha-restriction"}:
        generation = f"{name}-W"
        terminal = _rows(
            raw,
            "worker_terminal",
            process_generation=generation,
            work_item_id=work,
            run_id=scan_run,
        )
        _require(
            len(_rows(raw, "worker_process_started", process_generation=generation)) == 1
            and len(_rows(raw, "worker_process_stopped", process_generation=generation)) == 1,
            f"{name}: lifecycle missing",
        )
        _require(
            _rows(raw, "worker_claim", process_generation=generation, work_item_id=work)
            and len(terminal) == 1,
            f"{name}: correlated terminal missing",
        )
        expected = "PARTIAL" if name == "partial-parser" else "CAPTCHA_OR_CHALLENGE"
        _require(
            terminal[0].get("parser_outcome") == expected and terminal[0].get("run_id") == scan_run,
            f"{name}: raw parser outcome mismatch",
        )
        _require(
            after.get("runs")
            and after["runs"][-1].get("state")
            not in {"SUCCEEDED_BASELINE", "SUCCEEDED_DIFFERENCE"},
            f"{name}: clean success",
        )
        _zero_effects(name, item, before, after)
    elif name == "route-failure":
        generation = "route-failure-W"
        terminal = _rows(
            raw,
            "worker_terminal",
            process_generation=generation,
            work_item_id=work,
            run_id=scan_run,
        )
        egress = [
            r
            for r in _rows(raw, "egress_route_failure", work_item_id=work, run_id=scan_run)
            if r.get("outcome") in {"FAILURE", "UNAVAILABLE", "TRANSPORT_UNAVAILABLE"}
        ]
        _require(
            egress
            and terminal
            and terminal[0].get("parser_outcome")
            in {"TRANSPORT_UNAVAILABLE", "EXPLICIT_REJECTION"},
            "route failure correlation incomplete",
        )
        _require(
            egress[0].get("parser_correlation") == terminal[0].get("parser_attempt_id"),
            "route/parser correlation mismatch",
        )
        _zero_effects(name, item, before, after)
    elif name == "lost-lease":
        a_claim = _rows(raw, "worker_claim", process_generation="lost-A", work_item_id=work)
        b_claim = _rows(raw, "worker_claim", process_generation="lost-B", work_item_id=work)
        _require(
            a_claim and b_claim and a_claim[0]["process_pid"] != b_claim[0]["process_pid"],
            "lost lease identities missing",
        )
        _require(
            _rows(
                raw,
                "worker_controlled_hold",
                process_generation="lost-A",
                work_item_id=work,
                run_id=scan_run,
            )
            and _rows(
                raw,
                "worker_controlled_hold",
                process_generation="lost-B",
                work_item_id=work,
                run_id=scan_run,
            ),
            "lost lease holds missing",
        )
        _require(
            _rows(
                raw,
                "stale_terminal_attempt",
                process_generation="lost-A",
                work_item_id=work,
                run_id=scan_run,
            ),
            "stale attempt missing",
        )
        _require(
            _rows(
                raw,
                "stale_terminal_rejected",
                process_generation="lost-A",
                work_item_id=work,
                run_id=scan_run,
            ),
            "stale rejection missing",
        )
        _require(
            _rows(
                raw,
                "worker_terminal",
                process_generation="lost-B",
                work_item_id=work,
                run_id=scan_run,
            ),
            "authoritative terminal missing",
        )
        _require(
            _rows(raw, "worker_process_stopped", process_generation="lost-A")
            and _rows(raw, "worker_process_stopped", process_generation="lost-B"),
            "lost worker exit missing",
        )
        _require(
            after.get("authoritative_terminal_run_count") == 1,
            "owning authoritative terminal recomputation mismatch",
        )
        _require("authoritative_terminal_count" not in after, "producer terminal count used")
    elif name == "duplicate-listing":
        _require(
            isinstance(before.get("listing_identity"), str) and before["listing_identity"],
            "duplicate before listing missing",
        )
        _require(
            after.get("listing_identity") == before.get("listing_identity"),
            "duplicate listing changed",
        )
        _require(
            _rows(raw, "worker_process_started", process_generation="duplicate-W")
            and _rows(raw, "worker_process_stopped", process_generation="duplicate-W"),
            "duplicate-W lifecycle missing",
        )
        _require(
            _rows(raw, "worker_claim", process_generation="duplicate-W", work_item_id=work)
            and _rows(
                raw,
                "worker_terminal",
                process_generation="duplicate-W",
                work_item_id=work,
                run_id=scan_run,
            ),
            "duplicate-W did not own exact work/run",
        )
        _zero_effects(name, item, before, after)


def verify(path: Path, source_sha: str) -> None:
    data = cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))
    _require(
        data.get("technical_id") == TECHNICAL_ID and data.get("source_sha") == source_sha,
        "identity or source SHA mismatch",
    )
    observed = data.get("source_sha_observation")
    _require(
        isinstance(observed, dict)
        and observed.get("observed_sha") == source_sha
        and observed.get("expected_sha") == source_sha
        and (observed.get("github_sha") is None or observed.get("github_sha") == source_sha),
        "source SHA was not independently observed",
    )
    run_id = data.get("acceptance_run_id")
    _require(isinstance(run_id, str) and run_id, "run ID missing")
    _require(
        data.get("provider_live_calls") == 0
        and data.get("foreign_resource_impact") == 0
        and data.get("production_personal_data") == 0
        and data.get("credentials_exposure") is False
        and not _unsafe(data),
        "unsafe runtime impact",
    )
    scenarios = data.get("scenarios")
    _require(
        isinstance(scenarios, dict) and set(scenarios) == set(SCENARIO_NAMES),
        "scenario set is not exact",
    )
    scenarios = cast(dict[str, Any], scenarios)
    for name in SCENARIO_NAMES:
        _require(isinstance(scenarios[name], dict), f"{name}: not an object")
        _scenario(name, cast(dict[str, Any], scenarios[name]), cast(str, run_id))
    _require(
        data.get("remaining_scenario_stubs") == 0
        and data.get("remaining_unwired_drivers") == 0
        and data.get("remaining_hardcoded_observed_values") == 0,
        "implementation inventory incomplete",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--source-sha", required=True)
    args = parser.parse_args()
    verify(args.evidence, args.source_sha)
    print("RF24_SCAN_RESILIENCE_VERIFIER=PASS")
