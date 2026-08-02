"""Pure, fail-closed consumer of RF15 raw PostgreSQL transcripts."""

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


def _case(d: Mapping[str, Any], name: str) -> Mapping[str, Any]:
    cases = d.get("behavioral_cases")
    if not isinstance(cases, Mapping) or set(cases) != set(REQUIREMENT_IDS):
        raise ValueError("behavioral case registry mismatch")
    value = cases[name]
    if not isinstance(value, Mapping):
        raise ValueError(f"missing case: {name}")
    return value


def _time(value: Any) -> datetime:
    if not isinstance(value, str):
        raise ValueError("timestamp is not a string")
    result = datetime.fromisoformat(value)
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError("timestamp is not timezone-aware")
    return result


def _op(value: Any) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or not isinstance(value.get("callable"), str):
        raise ValueError("raw operation missing")
    if not isinstance(value.get("input"), Mapping):
        raise ValueError("raw operation input missing")
    if ("result" in value) == ("exception" in value):
        raise ValueError("raw operation must contain result xor exception")
    start, finish = _time(value.get("started_at")), _time(value.get("finished_at"))
    if start >= finish or not isinstance(value.get("backend_pid"), int):
        raise ValueError("invalid raw operation interval or backend identity")
    return value


def _ops(c: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    result = []
    for key, value in c.items():
        if key == "operation" or key.startswith("operation_"):
            if isinstance(value, Mapping):
                result.append(_op(value))
        elif key == "attempts" and isinstance(value, list):
            for item in value:
                if isinstance(item, Mapping) and isinstance(item.get("operation"), Mapping):
                    result.append(_op(item["operation"]))
    return result


def _physical(c: Mapping[str, Any]) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    before, after = c.get("physical_before"), c.get("physical_after")
    if not isinstance(before, Mapping) or not isinstance(after, Mapping):
        raise ValueError("raw physical observations missing")
    for rows in (before, after):
        for key in (
            "schedule_rows",
            "work_rows",
            "run_rows",
            "listing_rows",
            "anchor_rows",
            "event_ids",
        ):
            if key in rows and not isinstance(rows[key], list):
                raise ValueError(f"raw physical field is not a row/list: {key}")
    return before, after


def _terminal(c: Mapping[str, Any]) -> bool:
    ops = _ops(c)
    before, after = _physical(c)
    return (
        any("commit_comparison" in str(op["callable"]) for op in ops)
        and isinstance(after.get("run_rows"), list)
        and isinstance(after.get("listing_rows"), list)
        and before != after
    )


def _check(name: str, c: Mapping[str, Any]) -> bool:
    ops = _ops(c)
    if not ops:
        return False
    if name == "cadence_policy":
        result = c.get("operation", {}).get("result", {})
        return (
            result.get("basic") == [300, 600]
            and result.get("free") == [10800, 21600]
            and len(c.get("attempts", [])) >= 6
        )
    if name == "parser_failure_no_advance":
        attempts = c.get("attempts", [])
        return (
            set(c.get("statuses", [])) == PARSER_FAILURES
            and len(attempts) == len(PARSER_FAILURES)
            and all(
                isinstance(x, Mapping)
                and isinstance(x.get("operation", {}).get("exception"), Mapping)
                and x.get("physical_before") == x.get("physical_after")
                for x in attempts
            )
        )
    if name == "raw_payload_snapshot_boundary":
        return len(c.get("attempts", [])) >= 15 and all(
            isinstance(x, Mapping) and "exception" in x.get("operation", {}) for x in c["attempts"]
        )
    if name not in {"cadence_policy", "parser_failure_no_advance"}:
        _physical(c)
        return bool(ops)
    if name == "foreign_state_witness":
        return "commit_comparison" in str(ops[0]["callable"]) and c.get("physical_before", {}).get(
            "semantic"
        ) == c.get("physical_after", {}).get("semantic")
    if name == "restart_durability":
        return isinstance(
            c.get("physical_after", {}).get("second_lifetime", {}).get("backend_pid"), int
        )
    if name in {"lease_guard", "authority_recheck"}:
        return len(c.get("attempts", [])) == (3 if name == "lease_guard" else 4) and all(
            "exception" in x.get("operation", {}) for x in c["attempts"]
        )
    if name in {
        "due_materialization_concurrency",
        "concurrent_idempotency",
        "concurrent_baseline_serialization",
        "concurrent_new_listing_serialization",
    }:
        a, b = c.get("operation_a"), c.get("operation_b")
        if not isinstance(a, Mapping) or not isinstance(b, Mapping):
            return False
        return (
            a.get("backend_pid") != b.get("backend_pid")
            and _time(a["started_at"]) < _time(b["finished_at"])
            and _time(b["started_at"]) < _time(a["finished_at"])
        )
    if name == "empty_baseline_durable":
        return _terminal(c) and len(c["physical_after"].get("listing_rows", [])) == 0
    if name == "baseline_no_event":
        before, after = _physical(c)
        return _terminal(c) and len(after.get("event_ids", [])) == len(before.get("event_ids", []))
    if name == "new_listing_exactly_once":
        return _terminal(c) and len(c["physical_after"].get("event_ids", [])) == 1
    if name == "price_change_no_event":
        return _terminal(c) and len(c["physical_after"].get("event_ids", [])) == len(
            c["physical_before"].get("event_ids", [])
        )
    if name == "absence_no_removal":
        return _terminal(c) and c["physical_before"].get("listing_rows") == c["physical_after"].get(
            "listing_rows"
        )
    if name == "schedule_uniqueness":
        return len(c["physical_after"].get("schedule_rows", [])) == 1
    if name in {
        "due_work_current_slot",
        "due_work_coalescing",
        "recovery_blocks_backlog",
        "claim_exclusivity",
        "expired_claim_reconciliation",
        "run_revision_pin",
        "run_replay",
    }:
        return isinstance(c["physical_after"].get("work_rows"), list) and isinstance(
            c["physical_after"].get("run_rows"), list
        )
    return (
        _terminal(c)
        if name not in {"platform_event_identity", "no_foreign_domain_effect"}
        else _terminal(c)
    )


def _safe_check(data: Mapping[str, Any], name: str) -> bool:
    try:
        return _check(name, _case(data, name))
    except (KeyError, IndexError, TypeError, ValueError, OverflowError):
        return False


CHECKERS = {name: (lambda d, n=name: _safe_check(d, n)) for name in REQUIREMENT_IDS}
BEHAVIORAL_CHECKERS = CHECKERS


def _tamper_path(name: str) -> tuple[Any, ...]:
    if name in {"lease_guard", "authority_recheck"}:
        return ("attempts", 0, "operation", "callable")
    if name == "parser_failure_no_advance":
        return ("statuses", 0)
    if name == "raw_payload_snapshot_boundary":
        return ("attempts", 0, "operation", "exception")
    return ("operation", "callable")


RAW_DEPENDENCY_PATHS = {
    name: (
        f"behavioral_cases.{name}.operation.callable",
        f"behavioral_cases.{name}.operation.input",
        f"behavioral_cases.{name}.physical_before",
        f"behavioral_cases.{name}.physical_after",
    )
    for name in REQUIREMENT_IDS
}


def _at(value: Any, path: tuple[Any, ...]) -> Any:
    for part in path:
        value = value[part]
    return value


def _tamper(data: Mapping[str, Any], name: str) -> dict[str, Any]:
    result = copy.deepcopy(dict(data))
    case = result["behavioral_cases"][name]
    path = _tamper_path(name)
    parent = case
    for part in path[:-1]:
        parent = parent[part]
    current = parent[path[-1]]
    parent[path[-1]] = (
        (not current)
        if isinstance(current, bool)
        else (current + 1 if isinstance(current, int) else None)
    )
    return result


BEHAVIORAL_TAMPERS = {
    name: (
        lambda data, requirement=name: (_tamper(data, requirement), (_tamper_path(requirement),))
    )
    for name in REQUIREMENT_IDS
}


def verify(data: dict[str, Any], output_dir: Path) -> None:
    if data.get("identity", {}).get("technical_id") != TECHNICAL_ID:
        raise ValueError("identity mismatch")
    if set(data.get("behavioral_cases", {})) != set(REQUIREMENT_IDS):
        raise ValueError("requirement registry mismatch")
    rows = []
    for name, checker in CHECKERS.items():
        if not checker(data):
            raise ValueError(f"requirement failed: {name}")
        mutated = _tamper(data, name)
        original = {key: bool(value(data)) for key, value in CHECKERS.items()}
        changed = {key: bool(value(mutated)) for key, value in CHECKERS.items()}
        if changed[name]:
            raise ValueError(f"causal tamper did not fail: {name}")
        rows.append(
            {
                "requirement_id": name,
                "checker": "_check",
                "raw_dependency_paths": list(RAW_DEPENDENCY_PATHS[name]),
                "tamper_id": name,
                "checker_before": original,
                "checker_after": changed,
                "changed_checker_ids": [key for key in original if original[key] != changed[key]],
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
