"""Fail-closed verifier for the RF15 raw PostgreSQL transcript.

The producer records observations only.  This module derives every result
from the recorded operation, interval, and physical row facts.
"""

from __future__ import annotations

import argparse
import copy
import json
from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

TECHNICAL_ID = "RF-15-SCAN-ORCHESTRATION-DURABLE-RUNTIME-20260802-01"
PARSER_FAILURES = {
    "NOT_SENT",
    "TRANSPORT_UNAVAILABLE",
    "TRANSPORT_AMBIGUOUS",
    "EXPLICIT_REJECTION",
    "RATE_OR_ACCESS_RESTRICTED",
    "CAPTCHA_OR_CHALLENGE",
    "MALFORMED_RESPONSE",
    "INCOMPLETE_RESPONSE",
    "UNSUPPORTED_STRUCTURE",
    "REFERENCE_STALE",
    "REFERENCE_MISSING",
    "REFERENCE_DISPUTED",
    "PARTIAL",
    "RESULT_AMBIGUOUS",
}
REQUIREMENT_IDS = (
    "cadence_policy",
    "schedule_uniqueness",
    "due_work_current_slot",
    "due_work_coalescing",
    "recovery_blocks_backlog",
    "due_materialization_concurrency",
    "claim_exclusivity",
    "expired_claim_reconciliation",
    "lease_guard",
    "run_revision_pin",
    "run_replay",
    "baseline_no_event",
    "empty_baseline_durable",
    "parser_failure_no_advance",
    "new_listing_exactly_once",
    "price_change_no_event",
    "duplicate_within_run_exactly_once",
    "beacon_isolation",
    "absence_no_removal",
    "authority_recheck",
    "idempotency_replay_and_mismatch",
    "concurrent_idempotency",
    "concurrent_baseline_serialization",
    "concurrent_new_listing_serialization",
    "restart_durability",
    "foreign_state_witness",
    "raw_payload_snapshot_boundary",
    "platform_event_identity",
    "no_foreign_domain_effect",
)


def _time(value: Any) -> datetime:
    if not isinstance(value, str):
        raise ValueError("timestamp is not a string")
    result = datetime.fromisoformat(value)
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError("timestamp is not timezone-aware")
    return result


def _op(value: Any) -> Mapping[str, Any]:
    if (
        not isinstance(value, Mapping)
        or not isinstance(value.get("callable"), str)
        or not isinstance(value.get("input"), Mapping)
    ):
        raise ValueError("raw operation missing")
    if ("result" in value) == ("exception" in value):
        raise ValueError("raw operation must contain result xor exception")
    if _time(value.get("started_at")) >= _time(value.get("finished_at")):
        raise ValueError("invalid raw operation interval")
    if not isinstance(value.get("backend_pid"), int) or isinstance(value.get("backend_pid"), bool):
        raise ValueError("invalid backend identity")
    return value


def _ops(case: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    found: list[Mapping[str, Any]] = []
    for key, value in case.items():
        if (key == "operation" or key.startswith("operation_")) and isinstance(value, Mapping):
            found.append(_op(value))
        if key.endswith("_operation") and isinstance(value, Mapping):
            found.append(_op(value))
        if key == "attempts" and isinstance(value, list):
            for attempt in value:
                if isinstance(attempt, Mapping) and isinstance(attempt.get("operation"), Mapping):
                    found.append(_op(attempt["operation"]))
    return found


def _case(data: Mapping[str, Any], name: str) -> Mapping[str, Any]:
    cases = data.get("behavioral_cases")
    if not isinstance(cases, Mapping) or set(cases) != set(REQUIREMENT_IDS):
        raise ValueError("behavioral case registry mismatch")
    case = cases.get(name)
    if not isinstance(case, Mapping):
        raise ValueError("behavioral case is not an object")
    return case


def _physical(case: Mapping[str, Any]) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    before, after = case.get("physical_before"), case.get("physical_after")
    if not isinstance(before, Mapping) or not isinstance(after, Mapping):
        raise ValueError("physical observations missing")
    for observation in (before, after):
        for leaf in ("schedule_rows", "work_rows", "run_rows", "listing_rows", "event_ids"):
            if not isinstance(observation.get(leaf), list):
                raise ValueError(f"missing physical leaf: {leaf}")
    return before, after


def _result(case: Mapping[str, Any], needle: str) -> Mapping[str, Any] | None:
    for operation in _ops(case):
        if (
            needle in str(operation.get("callable"))
            and "result" in operation
            and isinstance(operation["result"], Mapping)
        ):
            return operation["result"]
    return None


def _success(case: Mapping[str, Any], needle: str) -> bool:
    return _result(case, needle) is not None


def _rejects(case: Mapping[str, Any], count: int | None, classes: set[str]) -> bool:
    attempts = case.get("attempts")
    if not isinstance(attempts, list) or (count is not None and len(attempts) < count):
        return False
    for item in attempts:
        if not isinstance(item, Mapping) or not isinstance(item.get("operation"), Mapping):
            return False
        operation = _op(item["operation"])
        if operation.get("exception", {}).get("class") not in classes:
            return False
        if "physical_before" in item and item.get("physical_before") != item.get("physical_after"):
            return False
    return True


def _terminal(case: Mapping[str, Any]) -> bool:
    before, after = _physical(case)
    result = _result(case, "commit_comparison")
    return result is not None and before.get("run_rows") != after.get("run_rows")


def _concurrent(case: Mapping[str, Any], needle: str) -> bool:
    a, b = case.get("operation_a"), case.get("operation_b")
    if not isinstance(a, Mapping) or not isinstance(b, Mapping):
        return False
    try:
        a, b = _op(a), _op(b)
        return (
            needle in str(a["callable"])
            and needle in str(b["callable"])
            and a["backend_pid"] != b["backend_pid"]
            and _time(a["started_at"]) < _time(b["finished_at"])
            and _time(b["started_at"]) < _time(a["finished_at"])
        )
    except (KeyError, TypeError, ValueError):
        return False


def _same_rows(before: Mapping[str, Any], after: Mapping[str, Any]) -> bool:
    return before == after


def _check(name: str, case: Mapping[str, Any]) -> bool:
    """Select a requirement-specific shape before reading its leaves."""
    try:
        if name == "cadence_policy":
            result = case["operation"]["result"]
            return (
                result["basic"] == [300, 600]
                and result["free"] == [10800, 21600]
                and _rejects(case, 6, {"CadenceRejected"})
            )
        if name == "parser_failure_no_advance":
            return set(case["statuses"]) == PARSER_FAILURES and _rejects(
                case, 14, {"DependencyBlocked", "ParserRejected"}
            )
        if name == "raw_payload_snapshot_boundary":
            safe = case["safe_persistence"]
            return (
                _rejects(case, 15, {"ValidationError", "ValueError"})
                and safe.get("snapshot") == {"price": 1}
                and isinstance(safe.get("serialized_size"), int)
                and safe["serialized_size"] <= 32768
                and _terminal(safe)
            )
        if name in {"foreign_state_witness", "no_foreign_domain_effect"}:
            branch = case["rf15_physical"]
            before, after = _physical(branch)
            return (
                _terminal(branch)
                and before["semantic"] == after["semantic"]
                and _time(before["observation_finished_at"])
                < _time(branch["operation"]["started_at"])
                and _time(branch["operation"]["finished_at"])
                < _time(after["observation_started_at"])
            )
        before, after = _physical(case)
        if name == "schedule_uniqueness":
            return _success(case, "create_or_update") and len(after["schedule_rows"]) == 1
        if name == "due_work_current_slot":
            return (
                _success(case, "materialize_due_work")
                and bool(after["work_rows"])
                and all(
                    row["due_at"] <= case["operation"]["input"]["now"] for row in after["work_rows"]
                )
            )
        if name == "due_work_coalescing":
            return (
                _success(case, "materialize_due_work")
                and len(after["work_rows"]) == 1
                and _time(after["schedule_rows"][0]["next_due_at"])
                > _time(case["operation"]["input"]["now"])
            )
        if name == "recovery_blocks_backlog":
            return (
                _success(case, "record_parser_outcome")
                and _success(case, "materialize_due_work")
                and (
                    isinstance(case["materialize_operation"].get("result"), list)
                    or case["materialize_operation"].get("result") == {}
                )
                and len(after["work_rows"]) == len(before["work_rows"])
            )
        if name == "due_materialization_concurrency":
            return _concurrent(case, "materialize_due_work") and len(after["work_rows"]) == 1
        if name == "claim_exclusivity":
            return (
                _concurrent(case, "claim_work")
                and sum(row["state"] == "CLAIMED" for row in after["work_rows"]) == 1
            )
        if name == "expired_claim_reconciliation":
            return (
                _rejects(case, 1, {"LeaseConflict"})
                and len(after["work_rows"]) == 1
                and after["work_rows"][0]["state"] == "PENDING_RECONCILIATION"
            )
        if name == "lease_guard":
            return _rejects(case, 3, {"LeaseConflict"}) and _same_rows(before, after)
        if name == "run_revision_pin":
            return (
                _success(case, "start_run")
                and bool(after["run_rows"])
                and after["run_rows"][0]["revision_no"]
                == case["operation"]["result"]["revision_no"]
            )
        if name == "run_replay":
            return (
                _success(case, "start_run")
                and len(after["run_rows"]) == len(before["run_rows"])
                and (
                    case["operation"].get("result", {}).get("replayed") is True
                    or case["operation"].get("exception", {}).get("class")
                    in {"RunAlreadyStarted", "DependencyBlocked"}
                )
            )
        if name == "baseline_no_event":
            return (
                _terminal(case)
                and len(after["listing_rows"]) >= 1
                and after["event_ids"] == before["event_ids"]
            )
        if name == "empty_baseline_durable":
            return (
                _terminal(case)
                and after["run_rows"]
                and after["run_rows"][-1]["state"] == "SUCCEEDED_BASELINE"
                and not after["listing_rows"]
                and not after["event_ids"]
            )
        if name == "new_listing_exactly_once":
            return (
                _terminal(case)
                and len(after["listing_rows"]) == len(before["listing_rows"]) + 1
                and len(after["event_ids"]) == len(before["event_ids"]) + 1
            )
        if name == "price_change_no_event":
            return (
                _terminal(case)
                and len(after["listing_rows"]) == len(before["listing_rows"])
                and after["event_ids"] == before["event_ids"]
            )
        if name == "duplicate_within_run_exactly_once":
            return (
                _terminal(case) and len(after["listing_rows"]) == 1 and len(after["event_ids"]) <= 1
            )
        if name == "beacon_isolation":
            return (
                _terminal(case)
                and case["scope"]["a"]["beacon_id"] != case["scope"]["b"]["beacon_id"]
                and case["scope"]["a"]["beacon_id"] == after["beacon_id"]
            )
        if name == "absence_no_removal":
            return (
                _terminal(case)
                and bool(before["listing_rows"])
                and before["listing_rows"] == after["listing_rows"]
            )
        if name == "authority_recheck":
            return _rejects(
                case, 4, {"DependencyBlocked", "RevisionConflict", "CadenceRejected"}
            ) and _same_rows(before, after)
        if name == "idempotency_replay_and_mismatch":
            return (
                _terminal(case)
                and "result" in case["operation_replay"]
                and case["operation_mismatch"].get("exception", {}).get("class")
                == "IdempotencyMismatch"
            )
        if name == "concurrent_idempotency":
            return _concurrent(case, "commit_comparison") and len(after["event_ids"]) <= 1
        if name == "concurrent_baseline_serialization":
            return (
                _concurrent(case, "commit_comparison")
                and len(after["listing_rows"]) == 1
                and all(
                    op.get("result", {}).get("baseline_established") is True
                    for op in (case["operation_a"], case["operation_b"])
                )
            )
        if name == "concurrent_new_listing_serialization":
            return (
                _concurrent(case, "commit_comparison")
                and len(after["listing_rows"]) == 1
                and len(after["event_ids"]) == 1
            )
        if name == "restart_durability":
            return (
                _terminal(case)
                and case["physical_after"]["second_lifetime"]["run_rows"] == after["run_rows"]
                and case["physical_after"]["second_lifetime"]["backend_pid"]
                != case["operation"]["backend_pid"]
            )
        if name == "platform_event_identity":
            result = _result(case, "commit_comparison")
            return (
                _terminal(case)
                and isinstance(result.get("event_ids"), list)
                and result["event_ids"] == after["event_ids"]
            )
    except (KeyError, IndexError, TypeError, ValueError, OverflowError, AttributeError):
        return False
    return False


CHECKERS = {
    name: (lambda data, requirement=name: _check(requirement, _case(data, requirement)))
    for name in REQUIREMENT_IDS
}
BEHAVIORAL_CHECKERS = CHECKERS

RAW_DEPENDENCY_PATHS = {
    name: [
        f"behavioral_cases.{name}.operation",
        f"behavioral_cases.{name}.physical_before",
        f"behavioral_cases.{name}.physical_after",
    ]
    for name in REQUIREMENT_IDS
}
RAW_DEPENDENCY_PATHS.update(
    {
        "parser_failure_no_advance": [
            "behavioral_cases.parser_failure_no_advance.statuses",
            "behavioral_cases.parser_failure_no_advance.attempts[*].operation.exception.class",
        ],
        "raw_payload_snapshot_boundary": [
            "behavioral_cases.raw_payload_snapshot_boundary.attempts[*].operation.exception.class",
            "behavioral_cases.raw_payload_snapshot_boundary.safe_persistence.snapshot",
            "behavioral_cases.raw_payload_snapshot_boundary.safe_persistence.serialized_size",
        ],
        "foreign_state_witness": [
            "behavioral_cases.foreign_state_witness.rf15_physical.physical_before.semantic",
            "behavioral_cases.foreign_state_witness.rf15_physical.operation.started_at",
        ],
        "no_foreign_domain_effect": [
            "behavioral_cases.no_foreign_domain_effect.rf15_physical.physical_after.semantic",
            "behavioral_cases.no_foreign_domain_effect.rf15_physical.operation.finished_at",
        ],
    }
)
TAMPER_PATHS = {name: ("physical_after", "event_ids") for name in REQUIREMENT_IDS}
TAMPER_PATHS.update(
    {
        "schedule_uniqueness": ("physical_after", "schedule_rows"),
        "due_work_current_slot": ("physical_after", "work_rows"),
        "due_work_coalescing": ("physical_after", "schedule_rows", 0, "next_due_at"),
        "recovery_blocks_backlog": ("materialize_operation", "result"),
        "due_materialization_concurrency": ("operation_a", "backend_pid"),
        "claim_exclusivity": ("physical_after", "work_rows"),
        "new_listing_exactly_once": ("physical_after", "listing_rows"),
        "price_change_no_event": ("physical_after", "listing_rows"),
        "duplicate_within_run_exactly_once": ("physical_after", "listing_rows"),
        "absence_no_removal": ("physical_after", "listing_rows"),
        "concurrent_idempotency": ("operation_a", "backend_pid"),
        "concurrent_baseline_serialization": ("operation_a", "result", "baseline_established"),
        "concurrent_new_listing_serialization": ("physical_after", "event_ids"),
    }
)
TAMPER_PATHS.update(
    {
        "cadence_policy": ("operation", "result", "basic"),
        "parser_failure_no_advance": ("attempts", 0, "operation", "exception", "class"),
        "expired_claim_reconciliation": ("physical_after", "work_rows", 0, "state"),
        "lease_guard": ("attempts", 0, "operation", "exception", "class"),
        "run_revision_pin": ("operation", "result", "revision_no"),
        "run_replay": ("operation", "result", "replayed"),
        "beacon_isolation": ("scope", "a", "beacon_id"),
        "authority_recheck": ("attempts", 0, "operation", "exception", "class"),
        "idempotency_replay_and_mismatch": ("operation_mismatch", "exception", "class"),
        "restart_durability": ("physical_after", "second_lifetime", "run_rows"),
        "foreign_state_witness": ("rf15_physical", "physical_after", "semantic"),
        "no_foreign_domain_effect": ("rf15_physical", "physical_after", "semantic"),
        "raw_payload_snapshot_boundary": ("safe_persistence", "snapshot"),
        "platform_event_identity": ("operation", "result", "event_ids"),
    }
)


def _tamper(data: Mapping[str, Any], name: str) -> dict[str, Any]:
    result = copy.deepcopy(dict(data))
    parent: Any = result["behavioral_cases"][name]
    path = TAMPER_PATHS[name]
    for part in path[:-1]:
        parent = parent[part]
    leaf = path[-1]
    value = parent[leaf]
    if isinstance(value, bool):
        parent[leaf] = not value
    elif isinstance(value, int):
        parent[leaf] = value + 1
    elif isinstance(value, list):
        parent[leaf] = value + ["tampered"]
    elif isinstance(value, dict):
        parent[leaf] = {"tampered": True}
    else:
        parent[leaf] = "tampered"
    return result


BEHAVIORAL_TAMPERS = {
    name: (
        lambda data, requirement=name: (_tamper(data, requirement), (TAMPER_PATHS[requirement],))
    )
    for name in REQUIREMENT_IDS
}


def _stamp(seconds: int) -> tuple[str, str]:
    start = datetime(2026, 8, 2, tzinfo=timezone.utc) + timedelta(seconds=seconds)
    return start.isoformat(), (start + timedelta(seconds=1)).isoformat()


def _representative_operation(
    name: str, result: Any = None, exception: str | None = None, pid: int = 10, offset: int = 0
) -> dict[str, Any]:
    started, finished = _stamp(offset)
    value: dict[str, Any] = {
        "callable": name,
        "input": {"now": "2026-08-02T00:00:00+00:00"},
        "started_at": started,
        "finished_at": finished,
        "backend_pid": pid,
    }
    if exception is None:
        value["result"] = result if result is not None else {}
    else:
        value["exception"] = {"class": exception, "reason": "fixture"}
    return value


def _representative_physical(
    beacon: str = "a",
    *,
    runs: list[dict[str, Any]] | None = None,
    listings: list[dict[str, Any]] | None = None,
    events: list[str] | None = None,
    work: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "beacon_id": beacon,
        "schedule_ids": ["s"],
        "work_ids": ["w"],
        "run_ids": ["r"],
        "event_ids": events or [],
        "schedule_rows": [{"id": "s", "next_due_at": "2026-08-03T00:00:00+00:00"}],
        "work_rows": work
        or [{"id": "w", "state": "SUCCEEDED", "due_at": "2026-08-02T00:00:00+00:00"}],
        "run_rows": runs or [{"id": "r", "state": "SUCCEEDED_BASELINE", "revision_no": 1}],
        "listing_ids": [row["id"] for row in (listings or [])],
        "listing_rows": listings or [],
        "anchor_rows": [],
    }


def build_representative_evidence() -> dict[str, Any]:
    """Build deterministic raw-shaped evidence for the complete verifier proof."""
    cases: dict[str, dict[str, Any]] = {}
    for name in REQUIREMENT_IDS:
        before, after = _representative_physical(), _representative_physical()
        operation = _representative_operation(
            "commit_comparison", {"baseline_established": True, "event_ids": []}
        )
        cases[name] = {"operation": operation, "physical_before": before, "physical_after": after}
    cases["cadence_policy"] = {
        "operation": _representative_operation(
            "validate_cadence", {"basic": [300, 600], "free": [10800, 21600]}
        ),
        "attempts": [
            {
                "operation": _representative_operation(
                    "validate_cadence", exception="CadenceRejected", pid=i, offset=i
                )
            }
            for i in range(6)
        ],
        "physical_before": _representative_physical(),
        "physical_after": _representative_physical(),
    }
    for name in ("due_work_current_slot", "due_work_coalescing"):
        cases[name]["operation"] = _representative_operation("materialize_due_work", {})
    cases["due_work_coalescing"]["operation"]["input"]["now"] = "2026-08-02T00:00:00+00:00"
    cases["parser_failure_no_advance"] = {
        "statuses": sorted(PARSER_FAILURES),
        "attempts": [
            {
                "operation": _representative_operation(
                    "commit_comparison", exception="DependencyBlocked", pid=i, offset=i
                ),
                "physical_before": _representative_physical(),
                "physical_after": _representative_physical(),
            }
            for i in range(14)
        ],
        "physical_before": _representative_physical(),
        "physical_after": _representative_physical(),
    }
    cases["schedule_uniqueness"]["operation"] = _representative_operation("create_or_update", {})
    cases["due_work_current_slot"]["operation"]["input"]["now"] = "2026-08-02T00:00:00+00:00"
    cases["due_work_current_slot"]["physical_before"]["work_rows"] = []
    cases["due_work_current_slot"]["physical_after"]["work_rows"] = [
        {"id": "w", "state": "DUE", "due_at": "2026-08-02T00:00:00+00:00"}
    ]
    cases["due_work_current_slot"]["physical_after"]["schedule_rows"] = [
        {"id": "s", "next_due_at": "2026-08-03T00:00:00+00:00"}
    ]
    cases["due_work_coalescing"]["physical_before"]["work_rows"] = []
    cases["due_work_coalescing"]["physical_after"]["work_rows"] = [
        {"id": "w", "state": "DUE", "due_at": "2026-02-02T00:00:00+00:00"}
    ]
    cases["due_work_coalescing"]["physical_after"]["schedule_rows"] = [
        {"id": "s", "next_due_at": "2026-08-03T00:00:00+00:00"}
    ]
    cases["recovery_blocks_backlog"]["operation"] = _representative_operation(
        "record_parser_outcome", {}, exception=None
    )
    cases["recovery_blocks_backlog"]["materialize_operation"] = _representative_operation(
        "materialize_due_work", {}
    )
    for name in ("due_materialization_concurrency", "claim_exclusivity"):
        callable_name = "materialize_due_work" if name.startswith("due_") else "claim_work"
        cases[name].update(
            {
                "operation_a": _representative_operation(callable_name, {}, pid=11, offset=1),
                "operation_b": _representative_operation(callable_name, {}, pid=12, offset=1),
            }
        )
    cases["claim_exclusivity"]["physical_before"]["work_rows"] = []
    cases["claim_exclusivity"]["physical_after"]["work_rows"] = [{"id": "w", "state": "CLAIMED"}]
    cases["lease_guard"]["attempts"] = [
        {
            "operation": _representative_operation(
                "commit_comparison", exception="LeaseConflict", pid=i, offset=i
            ),
            "physical_before": _representative_physical(),
            "physical_after": _representative_physical(),
        }
        for i in range(3)
    ]
    cases["run_revision_pin"]["operation"] = _representative_operation(
        "start_run", {"revision_no": 1}
    )
    cases["run_replay"]["operation"] = _representative_operation("start_run", {"replayed": True})
    cases["baseline_no_event"]["physical_before"] = _representative_physical(
        runs=[{"id": "r", "state": "RUNNING", "revision_no": 1}]
    )
    cases["baseline_no_event"]["physical_after"] = _representative_physical(
        runs=[{"id": "r", "state": "SUCCEEDED_BASELINE", "revision_no": 1}], listings=[{"id": "l"}]
    )
    cases["empty_baseline_durable"]["physical_before"] = _representative_physical(
        runs=[{"id": "r", "state": "RUNNING", "revision_no": 1}]
    )
    cases["empty_baseline_durable"]["physical_after"] = _representative_physical(
        runs=[{"id": "r", "state": "SUCCEEDED_BASELINE", "revision_no": 1}]
    )
    cases["new_listing_exactly_once"]["physical_before"] = _representative_physical(
        runs=[{"id": "r", "state": "RUNNING", "revision_no": 1}]
    )
    cases["new_listing_exactly_once"]["physical_after"] = _representative_physical(
        runs=[{"id": "r", "state": "SUCCEEDED_DIFFERENCE", "revision_no": 1}],
        listings=[{"id": "l"}],
        events=["e"],
    )
    cases["price_change_no_event"]["physical_before"] = _representative_physical(
        runs=[{"id": "r", "state": "RUNNING", "revision_no": 1}], listings=[{"id": "l"}]
    )
    cases["price_change_no_event"]["physical_after"] = _representative_physical(
        runs=[{"id": "r", "state": "SUCCEEDED_DIFFERENCE", "revision_no": 1}],
        listings=[{"id": "l"}],
    )
    cases["duplicate_within_run_exactly_once"]["physical_before"] = _representative_physical(
        runs=[{"id": "r", "state": "RUNNING", "revision_no": 1}]
    )
    cases["duplicate_within_run_exactly_once"]["physical_after"] = _representative_physical(
        runs=[{"id": "r", "state": "SUCCEEDED_BASELINE", "revision_no": 1}],
        listings=[{"id": "l"}],
        events=[],
    )
    cases["beacon_isolation"].update(
        {
            "scope": {"a": {"beacon_id": "a"}, "b": {"beacon_id": "b"}},
            "operation": _representative_operation("commit_comparison", {}),
        }
    )
    cases["beacon_isolation"]["physical_before"] = _representative_physical(
        "a", runs=[{"id": "r", "state": "RUNNING", "revision_no": 1}]
    )
    cases["beacon_isolation"]["physical_after"] = _representative_physical(
        "a",
        runs=[{"id": "r", "state": "SUCCEEDED_BASELINE", "revision_no": 1}],
        listings=[{"id": "l"}],
    )
    cases["absence_no_removal"]["physical_before"] = _representative_physical(
        runs=[{"id": "r", "state": "RUNNING", "revision_no": 1}], listings=[{"id": "l"}]
    )
    cases["absence_no_removal"]["physical_after"] = _representative_physical(
        runs=[{"id": "r", "state": "SUCCEEDED_DIFFERENCE", "revision_no": 1}],
        listings=[{"id": "l"}],
    )
    cases["authority_recheck"]["attempts"] = [
        {
            "operation": _representative_operation(
                "commit_comparison", exception=exc, pid=i, offset=i
            ),
            "physical_before": _representative_physical(),
            "physical_after": _representative_physical(),
        }
        for i, exc in enumerate(
            ("DependencyBlocked", "RevisionConflict", "CadenceRejected", "DependencyBlocked")
        )
    ]
    cases["idempotency_replay_and_mismatch"].update(
        {
            "operation_replay": _representative_operation("commit_comparison", {}),
            "operation_mismatch": _representative_operation(
                "commit_comparison", exception="IdempotencyMismatch"
            ),
        }
    )
    cases["expired_claim_reconciliation"]["attempts"] = [
        {"operation": _representative_operation("claim_work", exception="LeaseConflict")}
    ]
    cases["expired_claim_reconciliation"]["physical_before"] = _representative_physical(
        work=[{"id": "w", "state": "CLAIMED"}]
    )
    cases["expired_claim_reconciliation"]["physical_after"] = _representative_physical(
        work=[{"id": "w", "state": "PENDING_RECONCILIATION"}]
    )
    cases["raw_payload_snapshot_boundary"] = {
        "attempts": [
            {
                "operation": _representative_operation(
                    "ListingCandidate", exception="ValueError", pid=i, offset=i
                )
            }
            for i in range(15)
        ],
        "safe_persistence": {
            "snapshot": {"price": 1},
            "serialized_size": 12,
            "physical_before": _representative_physical(
                runs=[{"id": "r", "state": "RUNNING", "revision_no": 1}]
            ),
            "physical_after": _representative_physical(
                runs=[{"id": "r", "state": "SUCCEEDED_BASELINE", "revision_no": 1}],
                listings=[{"id": "l"}],
            ),
        },
    }
    cases["raw_payload_snapshot_boundary"]["safe_persistence"]["operation"] = operation
    foreign_case = {
        "rf15_physical": {
            "operation": _representative_operation("commit_comparison", {}, offset=3),
            "physical_before": {
                **_representative_physical(
                    runs=[{"id": "r", "state": "RUNNING", "revision_no": 1}]
                ),
                "semantic": {"identity": [], "parser": []},
                "observation_finished_at": _stamp(1)[1],
            },
            "physical_after": {
                **_representative_physical(
                    runs=[{"id": "r", "state": "SUCCEEDED_BASELINE", "revision_no": 1}]
                ),
                "semantic": {"identity": [], "parser": []},
                "observation_started_at": _stamp(5)[0],
            },
        }
    }
    cases["foreign_state_witness"] = copy.deepcopy(foreign_case)
    cases["no_foreign_domain_effect"] = copy.deepcopy(foreign_case)
    for name in (
        "concurrent_idempotency",
        "concurrent_baseline_serialization",
        "concurrent_new_listing_serialization",
    ):
        cases[name].update(
            {
                "operation_a": _representative_operation(
                    "commit_comparison",
                    {
                        "baseline_established": name == "concurrent_baseline_serialization",
                        "event_ids": ["e"]
                        if name == "concurrent_new_listing_serialization"
                        else [],
                    },
                    pid=11,
                    offset=1,
                ),
                "operation_b": _representative_operation(
                    "commit_comparison",
                    {
                        "baseline_established": name == "concurrent_baseline_serialization",
                        "event_ids": [],
                    },
                    pid=12,
                    offset=1,
                ),
            }
        )
    cases["concurrent_idempotency"]["physical_after"] = _representative_physical(
        runs=[{"id": "r", "state": "SUCCEEDED_DIFFERENCE", "revision_no": 1}],
        listings=[{"id": "l"}],
        events=[],
    )
    cases["concurrent_baseline_serialization"]["physical_after"] = _representative_physical(
        runs=[{"id": "r", "state": "SUCCEEDED_BASELINE", "revision_no": 1}],
        listings=[{"id": "l"}],
        events=[],
    )
    cases["concurrent_new_listing_serialization"]["physical_after"] = _representative_physical(
        runs=[{"id": "r", "state": "SUCCEEDED_DIFFERENCE", "revision_no": 1}],
        listings=[{"id": "l"}],
        events=["e"],
    )
    for name in (
        "concurrent_idempotency",
        "concurrent_baseline_serialization",
        "concurrent_new_listing_serialization",
    ):
        cases[name]["physical_before"] = _representative_physical(
            runs=[{"id": "r", "state": "RUNNING", "revision_no": 1}]
        )
    cases["idempotency_replay_and_mismatch"]["physical_before"] = _representative_physical(
        runs=[{"id": "r", "state": "RUNNING", "revision_no": 1}]
    )
    cases["restart_durability"]["physical_before"] = _representative_physical(
        runs=[{"id": "r", "state": "RUNNING", "revision_no": 1}]
    )
    cases["restart_durability"]["physical_after"] = {
        **cases["restart_durability"]["physical_after"],
        "second_lifetime": {
            "backend_pid": 99,
            "run_rows": cases["restart_durability"]["physical_after"]["run_rows"],
        },
    }
    cases["platform_event_identity"]["operation"]["result"] = {
        "event_ids": ["e"],
        "baseline_established": False,
    }
    cases["platform_event_identity"]["physical_before"] = _representative_physical(
        runs=[{"id": "r", "state": "RUNNING", "revision_no": 1}]
    )
    cases["platform_event_identity"]["physical_after"]["event_ids"] = ["e"]
    return {"identity": {"technical_id": TECHNICAL_ID}, "behavioral_cases": cases}


def _diagnostics(data: Mapping[str, Any], original: Mapping[str, bool]) -> list[dict[str, Any]]:
    rows = []
    for name in REQUIREMENT_IDS:
        case = (
            data.get("behavioral_cases", {}).get(name, {})
            if isinstance(data.get("behavioral_cases"), Mapping)
            else {}
        )
        rows.append(
            {
                "requirement_id": name,
                "original_checker": bool(original.get(name, False)),
                "required_dependency_paths": RAW_DEPENDENCY_PATHS[name],
                "operation_exception_classes": [
                    str(item.get("operation", {}).get("exception", {}).get("class"))
                    for item in case.get("attempts", [])
                    if isinstance(item, Mapping)
                ]
                if isinstance(case, Mapping)
                else [],
            }
        )
    return rows


def verify(data: dict[str, Any], output_dir: Path) -> None:
    original = {
        name: bool(CHECKERS[name](data)) if name in CHECKERS else False for name in REQUIREMENT_IDS
    }
    output_dir.joinpath("rf15-verifier-diagnostics.json").write_text(
        json.dumps({"requirements": _diagnostics(data, original)}, indent=2, sort_keys=True) + "\n"
    )
    if data.get("identity", {}).get("technical_id") != TECHNICAL_ID or set(
        data.get("behavioral_cases", {})
    ) != set(REQUIREMENT_IDS):
        raise ValueError("identity or requirement registry mismatch")
    failed = [name for name, value in original.items() if not value]
    if failed:
        raise ValueError(f"original evidence is false: {failed}")
    rows = []
    for name in REQUIREMENT_IDS:
        mutated = _tamper(data, name)
        after = {other: bool(CHECKERS[other](mutated)) for other in REQUIREMENT_IDS}
        changed = [other for other in REQUIREMENT_IDS if original[other] != after[other]]
        if after[name] or name not in changed:
            raise ValueError(f"semantic tamper did not reject {name}")
        rows.append(
            {
                "requirement_id": name,
                "checker_before": original,
                "checker_after": after,
                "changed_checker_ids": changed,
                "tamper_id": name,
                "raw_dependency_paths": RAW_DEPENDENCY_PATHS[name],
            }
        )
    output_dir.joinpath("rf15-requirement-map.json").write_text(
        json.dumps({"requirements": rows}, indent=2, sort_keys=True) + "\n"
    )
    output_dir.joinpath("rf15-tamper-matrix.json").write_text(
        json.dumps({"tampers": rows}, indent=2, sort_keys=True) + "\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence", type=Path)
    args = parser.parse_args()
    try:
        verify(json.loads(args.evidence.read_text(encoding="utf-8")), args.evidence.parent)
    except (OSError, json.JSONDecodeError, ValueError, KeyError, IndexError, TypeError) as exc:
        raise SystemExit(f"RF15 evidence rejected: {exc}") from None
    print("RF15_ACCEPTANCE_VERIFIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
