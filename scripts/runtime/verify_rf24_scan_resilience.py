# ruff: noqa: E501
"""Independent fail-closed verifier for the seven-scenario RF24 package."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, cast

from mayak.runtime.rf24_scan_resilience import ACTION_BOUNDARIES, SCENARIO_NAMES, TECHNICAL_ID

SECRET_KEY = re.compile(r"(?:cookie|set-cookie|authorization|bearer|access[_-]?token|refresh[_-]?token|session[_-]?token|password)", re.I)
SECRET_VALUE = re.compile(r"(?:bearer\s+\S+|mayak_session=\S+|postgres(?:ql)?://[^\s:@/]+:[^\s@/]+@|-----BEGIN [A-Z ]+PRIVATE KEY-----)", re.I)


def _unsafe(value: object) -> bool:
    if isinstance(value, dict):
        return any((SECRET_KEY.search(str(k)) and v not in (None, "", False, True, "<redacted>", "removed")) or _unsafe(v) for k, v in value.items())
    if isinstance(value, list):
        return any(_unsafe(v) for v in value)
    return isinstance(value, str) and bool(SECRET_VALUE.search(value))


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _scenario(name: str, item: dict[str, Any], run_id: str) -> None:
    _require(item.get("scenario_name") == name, f"{name}: identity mismatch")
    for key in ("acceptance_run_id", "source_sha", "account_id", "beacon_id", "schedule_id"):
        _require(bool(item.get(key)) and (key != "acceptance_run_id" or item.get(key) == run_id), f"{name}: missing {key}")
    before, action, after = item.get("before"), item.get("action"), item.get("after")
    _require(isinstance(before, dict) and isinstance(action, dict) and isinstance(after, dict), f"{name}: before/action/after missing")
    before = cast(dict[str, Any], before)
    action = cast(dict[str, Any], action)
    after = cast(dict[str, Any], after)
    _require(action.get("public_boundary") == ACTION_BOUNDARIES[name], f"{name}: wrong boundary")
    _require(action.get("actual_action_invoked") not in (None, "", "stub", "TODO"), f"{name}: unwired action")
    _require(action.get("observation_source") not in (None, "hard-coded", "constant"), f"{name}: hard-coded observation")
    _require(action.get("process_observed") is True if name in {"worker-restart", "scheduler-restart"} else True, f"{name}: process observation missing")
    if name == "worker-restart":
        _require(action.get("pid_1") != action.get("pid_2") and action.get("generation_1") != action.get("generation_2"), "worker restart identity reused")
        _require(after.get("terminal_state") in {"SUCCEEDED_BASELINE", "SUCCEEDED_DIFFERENCE"} and after.get("duplicate_effect") is False, "worker restart terminal proof missing")
    elif name == "scheduler-restart":
        _require(action.get("pid_1") != action.get("pid_2") and action.get("generation_1") != action.get("generation_2"), "scheduler restart identity reused")
        _require(after.get("materialized_work_count") == 1 and after.get("persistent_schedule") is True, "scheduler duplicate materialization")
    elif name == "partial-parser":
        _require(action.get("parser_outcome") == "PARTIAL" and after.get("scan_state") not in {"SUCCEEDED_BASELINE", "SUCCEEDED_DIFFERENCE"}, "partial became success")
        _require(after.get("new_listing_delta") == 0 and after.get("notification_effect_delta") == 0, "partial false effect")
    elif name == "captcha-restriction":
        _require(action.get("parser_outcome") in {"CAPTCHA_OR_CHALLENGE", "RATE_OR_ACCESS_RESTRICTED"} and after.get("scan_state") not in {"SUCCEEDED_BASELINE", "SUCCEEDED_DIFFERENCE"}, "restriction became empty success")
        _require(after.get("new_listing_delta") == 0 and after.get("notification_effect_delta") == 0, "restriction false effect")
    elif name == "route-failure":
        _require(action.get("route_selected") is True and action.get("route_failure_observed") is True and action.get("parser_success") is False, "route failure was not propagated")
        _require(after.get("new_listing_delta") == 0 and after.get("notification_effect_delta") == 0, "route false effect")
    elif name == "lost-lease":
        _require(action.get("owner_a") != action.get("owner_b") and action.get("stale_owner_rejected") is True, "stale owner was not rejected")
        _require(after.get("authoritative_owner") == action.get("owner_b"), "wrong lease owner")
    elif name == "duplicate-listing":
        _require(after.get("listing_known") is True and after.get("new_listing_delta") == 0 and after.get("event_delta") == 0 and after.get("notification_effect_delta") == 0, "duplicate listing emitted an effect")


def verify(path: Path, source_sha: str) -> None:
    data = cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))
    _require(bool(isinstance(data, dict) and data.get("technical_id") == TECHNICAL_ID), "technical ID mismatch")
    _require(data.get("source_sha") == source_sha, "source SHA mismatch")
    run_id = data.get("acceptance_run_id")
    _require(bool(isinstance(run_id, str) and run_id), "run ID missing")
    run_id = cast(str, run_id)
    _require(data.get("provider_live_calls") == 0 and data.get("foreign_resource_impact") == 0 and data.get("production_personal_data") == 0, "unsafe runtime impact")
    _require(bool(data.get("credentials_exposure") is False and not _unsafe(data)), "credential exposure")
    scenarios = data.get("scenarios")
    _require(isinstance(scenarios, dict) and set(scenarios) == set(SCENARIO_NAMES), "scenario set is not exact")
    scenarios = cast(dict[str, Any], scenarios)
    for name in SCENARIO_NAMES:
        item = scenarios[name]
        _require(isinstance(item, dict), f"{name}: not an object")
        _scenario(name, item, run_id)
    _require(data.get("remaining_scenario_stubs") == 0 and data.get("remaining_unwired_drivers") == 0 and data.get("remaining_hardcoded_observed_values") == 0, "implementation inventory incomplete")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--evidence", type=Path, required=True)
    p.add_argument("--source-sha", required=True)
    a = p.parse_args()
    verify(a.evidence, a.source_sha)
    print("RF24_SCAN_RESILIENCE_VERIFIER=PASS")
