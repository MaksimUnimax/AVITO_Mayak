"""Pure, fail-closed verifier for the RF15 raw runtime transcript."""

from __future__ import annotations

import argparse
import copy
import json
from collections.abc import Mapping
from datetime import datetime
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
    if _time(value.get("started_at")) >= _time(value.get("finished_at")) or not isinstance(
        value.get("backend_pid"), int
    ):
        raise ValueError("invalid raw operation interval or backend identity")
    return value


def _ops(case: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    result: list[Mapping[str, Any]] = []
    for key, value in case.items():
        if key == "operation" or key.startswith("operation_"):
            if isinstance(value, Mapping):
                result.append(_op(value))
        elif key == "attempts" and isinstance(value, list):
            for item in value:
                if isinstance(item, Mapping) and isinstance(item.get("operation"), Mapping):
                    result.append(_op(item["operation"]))
    return result


def _physical(case: Mapping[str, Any]) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    before, after = case.get("physical_before"), case.get("physical_after")
    if not isinstance(before, Mapping) or not isinstance(after, Mapping):
        raise ValueError("physical observations missing")
    for observation in (before, after):
        for key in ("schedule_rows", "work_rows", "run_rows", "listing_rows", "event_ids"):
            if not isinstance(observation.get(key), list):
                raise ValueError(f"missing physical leaf: {key}")
    return before, after


def _case(data: Mapping[str, Any], name: str) -> Mapping[str, Any]:
    cases = data.get("behavioral_cases")
    if (
        not isinstance(cases, Mapping)
        or set(cases) != set(REQUIREMENT_IDS)
        or not isinstance(cases.get(name), Mapping)
    ):
        raise ValueError("behavioral case registry mismatch")
    return cases[name]


def _success(case: Mapping[str, Any], needle: str) -> bool:
    return any(needle in str(op["callable"]) and "result" in op for op in _ops(case))


def _rejects(case: Mapping[str, Any], count: int, classes: set[str]) -> bool:
    attempts = case.get("attempts")
    return (
        isinstance(attempts, list)
        and len(attempts) == count
        and all(
            isinstance(item, Mapping)
            and isinstance(item.get("operation"), Mapping)
            and item["operation"].get("exception", {}).get("class") in classes
            and item.get("physical_before") == item.get("physical_after")
            for item in attempts
        )
    )


def _terminal(case: Mapping[str, Any]) -> bool:
    return _success(case, "commit_comparison") and case["physical_before"] != case["physical_after"]


def _concurrent(case: Mapping[str, Any], needle: str) -> bool:
    a, b = case.get("operation_a"), case.get("operation_b")
    return (
        isinstance(a, Mapping)
        and isinstance(b, Mapping)
        and needle in str(a.get("callable"))
        and needle in str(b.get("callable"))
        and isinstance(a.get("backend_pid"), int)
        and isinstance(b.get("backend_pid"), int)
        and a["backend_pid"] != b["backend_pid"]
        and _time(a["started_at"]) < _time(b["finished_at"])
        and _time(b["started_at"]) < _time(a["finished_at"])
    )


def _check(name: str, case: Mapping[str, Any]) -> bool:
    """Every requirement has an independent semantic branch. Missing leaves reject."""
    try:
        if name == "cadence_policy":
            result = case["operation"]["result"]
            return (
                _success(case, "validate_cadence")
                and result["basic"] == [300, 600]
                and result["free"] == [10800, 21600]
                and _rejects(case, 6, {"CadenceRejected"})
            )
        before, after = _physical(case)
        if name == "schedule_uniqueness":
            return (
                _success(case, "create_or_update")
                and len(after["schedule_rows"]) == 1
                and after["schedule_rows"][0]["interval_seconds"] in (300, 600)
            )
        if name == "due_work_current_slot":
            return (
                _success(case, "materialize_due_work")
                and after["work_rows"]
                and all(
                    row["due_at"] <= case["operation"]["input"]["now"] for row in after["work_rows"]
                )
            )
        if name == "due_work_coalescing":
            return (
                _success(case, "materialize_due_work")
                and len(after["work_rows"]) == 1
                and after["schedule_rows"][0]["next_due_at"] > case["operation"]["input"]["now"]
            )
        if name == "recovery_blocks_backlog":
            return (
                _success(case, "record_parser_outcome")
                and _success(case, "materialize_due_work")
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
            return _rejects(case, 1, {"DependencyBlocked", "LeaseConflict"}) and any(
                row["state"] == "RECONCILIATION" for row in after["work_rows"]
            )
        if name == "lease_guard":
            return _rejects(case, 3, {"LeaseConflict"}) and before == after
        if name == "run_revision_pin":
            return (
                _success(case, "start_run")
                and after["run_rows"]
                and all(
                    row["revision_no"] == case["operation"]["result"]["revision_no"]
                    for row in after["run_rows"]
                )
            )
        if name == "run_replay":
            return (
                _success(case, "start_run")
                and len(after["run_rows"]) == len(before["run_rows"])
                and case["operation"]["result"].get("replayed") is True
            )
        if name == "baseline_no_event":
            return (
                _terminal(case)
                and after["listing_rows"]
                and len(after["event_ids"]) == len(before["event_ids"])
            )
        if name == "empty_baseline_durable":
            return (
                _terminal(case)
                and len(after["run_rows"]) > len(before["run_rows"])
                and not after["listing_rows"]
                and not after["event_ids"]
            )
        if name == "parser_failure_no_advance":
            return set(case["statuses"]) == PARSER_FAILURES and _rejects(
                case, len(PARSER_FAILURES), {"DependencyBlocked", "ParserRejected"}
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
                and len(after["event_ids"]) == len(before["event_ids"])
            )
        if name == "duplicate_within_run_exactly_once":
            return (
                _terminal(case) and len(after["listing_rows"]) == 1 and len(after["event_ids"]) <= 1
            )
        if name == "beacon_isolation":
            return (
                _terminal(case)
                and case["scope"]["a"]["beacon_id"] != case["scope"]["b"]["beacon_id"]
                and case["physical_before"].get("beacon_id")
                == case["physical_after"].get("beacon_id")
            )
        if name == "absence_no_removal":
            return (
                _terminal(case)
                and bool(before["listing_rows"])
                and before["listing_rows"] == after["listing_rows"]
            )
        if name == "authority_recheck":
            return (
                _rejects(case, 4, {"DependencyBlocked", "RevisionConflict", "CadenceRejected"})
                and before == after
            )
        if name == "idempotency_replay_and_mismatch":
            return (
                _terminal(case)
                and case.get("operation_replay", {}).get("result") is not None
                and case.get("operation_mismatch", {}).get("exception", {}).get("class")
                == "IdempotencyMismatch"
            )
        if name in {
            "concurrent_idempotency",
            "concurrent_baseline_serialization",
            "concurrent_new_listing_serialization",
        }:
            return (
                _concurrent(case, "commit_comparison")
                and len(after["listing_rows"]) == 1
                and len(after["event_ids"]) <= 1
            )
        if name == "restart_durability":
            second = after["second_lifetime"]
            return (
                _terminal(case)
                and isinstance(second["backend_pid"], int)
                and second["run_rows"] == after["run_rows"]
            )
        if name in {"foreign_state_witness", "no_foreign_domain_effect"}:
            return (
                _terminal(case["rf15_physical"])
                and case["physical_before"]["semantic"] == case["physical_after"]["semantic"]
            )
        if name == "raw_payload_snapshot_boundary":
            return _rejects(case, 15, {"ValidationError"}) and not after.get(
                "unsafe_persisted_values"
            )
        if name == "platform_event_identity":
            return (
                _terminal(case)
                and case.get("returned_event_id") == case.get("persisted_event_id")
                and case["returned_event_id"] in after["event_ids"]
            )
    except (KeyError, IndexError, TypeError, ValueError, OverflowError):
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

TAMPER_PATHS = {name: ("physical_after", "event_ids") for name in REQUIREMENT_IDS}
TAMPER_PATHS.update(
    {
        "cadence_policy": ("operation", "result", "basic"),
        "schedule_uniqueness": ("physical_after", "schedule_rows"),
        "due_work_current_slot": ("operation", "input", "now"),
        "due_work_coalescing": ("physical_after", "work_rows"),
        "recovery_blocks_backlog": ("physical_after", "work_rows"),
        "claim_exclusivity": ("physical_after", "work_rows"),
        "expired_claim_reconciliation": ("physical_after", "work_rows"),
        "lease_guard": ("attempts", 0, "physical_after"),
        "run_revision_pin": ("operation", "result", "revision_no"),
        "run_replay": ("operation", "result", "replayed"),
        "empty_baseline_durable": ("physical_after", "listing_rows"),
        "duplicate_within_run_exactly_once": ("physical_after", "listing_rows"),
        "beacon_isolation": ("physical_after", "beacon_id"),
        "absence_no_removal": ("physical_after", "listing_rows"),
        "authority_recheck": ("attempts", 0, "operation", "exception"),
        "idempotency_replay_and_mismatch": ("operation_mismatch", "exception", "class"),
        "concurrent_baseline_serialization": ("physical_after", "listing_rows"),
        "parser_failure_no_advance": ("attempts", 0, "physical_after"),
        "raw_payload_snapshot_boundary": ("attempts", 0, "operation", "exception"),
        "foreign_state_witness": ("physical_after", "semantic"),
        "no_foreign_domain_effect": ("physical_after", "semantic"),
        "restart_durability": ("physical_after", "second_lifetime", "run_rows"),
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
    if isinstance(value, list):
        parent[leaf] = value + [{"tampered": True}]
    elif isinstance(value, bool):
        parent[leaf] = not value
    elif isinstance(value, int):
        parent[leaf] = value + 1
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


def verify(data: dict[str, Any], output_dir: Path) -> None:
    if data.get("identity", {}).get("technical_id") != TECHNICAL_ID or set(
        data.get("behavioral_cases", {})
    ) != set(REQUIREMENT_IDS):
        raise ValueError("identity or requirement registry mismatch")
    rows = []
    original = {name: bool(CHECKERS[name](data)) for name in REQUIREMENT_IDS}
    if not all(original.values()):
        failed = [name for name, value in original.items() if not value]
        raise ValueError(f"original evidence is false: {failed}")
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
    payload = {"requirements": rows}
    output_dir.joinpath("rf15-requirement-map.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n"
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
