"""Fail-closed semantic verifier for raw RF15 runtime transcripts.

The input is an observation transcript.  It contains no producer verdicts;
every decision below is derived from operation records and independent
physical observations.  This module intentionally has no Mayak imports.
"""

from __future__ import annotations

import argparse
import copy
import json
from collections.abc import Callable, Mapping
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


def _case(data: Mapping[str, Any], name: str) -> Mapping[str, Any]:
    cases = data.get("behavioral_cases")
    if not isinstance(cases, Mapping) or set(cases) != set(REQUIREMENT_IDS):
        raise ValueError("behavioral case registry mismatch")
    value = cases.get(name)
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


def _operation(c: Mapping[str, Any]) -> Mapping[str, Any]:
    operation = c.get("operation")
    if not isinstance(operation, Mapping):
        raise ValueError("operation observation missing")
    if not isinstance(operation.get("callable"), str) or not operation["callable"]:
        raise ValueError("operation identity missing")
    if not isinstance(operation.get("input"), Mapping):
        raise ValueError("operation input missing")
    if ("result" in operation) == ("exception" in operation):
        raise ValueError("operation must have exactly one result or exception")
    if "exception" in operation and not isinstance(operation["exception"], Mapping):
        raise ValueError("exception observation malformed")
    _time(operation.get("started_at"))
    _time(operation.get("finished_at"))
    if _time(operation["started_at"]) >= _time(operation["finished_at"]):
        raise ValueError("operation interval is impossible")
    if not isinstance(operation.get("backend_pid"), int):
        raise ValueError("backend identity missing")
    return operation


def _physical(c: Mapping[str, Any]) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    before, after = c.get("physical_before"), c.get("physical_after")
    if not isinstance(before, Mapping) or not isinstance(after, Mapping):
        raise ValueError("physical before/after observations missing")
    return before, after


def _ids(value: Any) -> list[Any]:
    if not isinstance(value, list) or len(value) != len(set(map(str, value))):
        raise ValueError("physical identity list is malformed")
    return value


def _overlap(c: Mapping[str, Any]) -> bool:
    a, b = c.get("operation_a"), c.get("operation_b")
    if not isinstance(a, Mapping) or not isinstance(b, Mapping):
        return False
    sa, ea = _time(a.get("started_at")), _time(a.get("finished_at"))
    sb, eb = _time(b.get("started_at")), _time(b.get("finished_at"))
    if sa >= ea or sb >= eb:
        raise ValueError("impossible concurrency interval")
    return max(sa, sb) < min(ea, eb) and a.get("backend_pid") != b.get("backend_pid")


def _result(c: Mapping[str, Any]) -> Any:
    return _operation(c).get("result")


def _changed(c: Mapping[str, Any], key: str) -> bool:
    before, after = _physical(c)
    return before.get(key) != after.get(key)


def check_cadence_policy(d: Mapping[str, Any]) -> bool:
    c = _case(d, "cadence_policy")
    op = _operation(c)
    results = c.get("attempts")
    return (
        isinstance(results, list)
        and len(results) == 6
        and all(
            isinstance(x, Mapping)
            and isinstance(x.get("operation"), Mapping)
            and isinstance(x["operation"].get("exception"), Mapping)
            and x["operation"]["exception"].get("class") == "CadenceRejected"
            for x in results
        )
        and op.get("result", {}).get("basic") == [300, 300]
        and op.get("result", {}).get("free") == [10800, 10800]
    )


def check_schedule_uniqueness(d: Mapping[str, Any]) -> bool:
    c = _case(d, "schedule_uniqueness")
    _operation(c)
    before, after = _physical(c)
    return len(_ids(after.get("schedule_ids"))) == 1 and set(before.get("beacon_ids", [])) <= set(
        after.get("beacon_ids", [])
    )


def check_due_work_current_slot(d: Mapping[str, Any]) -> bool:
    c = _case(d, "due_work_current_slot")
    _operation(c)
    _, after = _physical(c)
    return bool(_time(after["due_at"]) <= _time(after["now"]) < _time(after["next_due_at"]))


def check_due_work_coalescing(d: Mapping[str, Any]) -> bool:
    c = _case(d, "due_work_coalescing")
    _operation(c)
    before, after = _physical(c)
    return bool(
        after.get("work_ids")
        and len(after["work_ids"]) - len(before.get("work_ids", [])) == 1
        and after.get("missed_intervals", 0) > 1
    )


def check_recovery_blocks_backlog(d: Mapping[str, Any]) -> bool:
    c = _case(d, "recovery_blocks_backlog")
    _operation(c)
    before, after = _physical(c)
    return bool(
        after.get("state") == "PENDING_RECONCILIATION"
        and after.get("work_ids") == before.get("work_ids")
    )


def _concurrent(d: Mapping[str, Any], name: str) -> bool:
    c = _case(d, name)
    _operation(c)
    before, after = _physical(c)
    return _overlap(c) and len(after.get("work_ids", [])) - len(before.get("work_ids", [])) == 1


def check_due_materialization_concurrency(d: Mapping[str, Any]) -> bool:
    return _concurrent(d, "due_materialization_concurrency")


def check_claim_exclusivity(d: Mapping[str, Any]) -> bool:
    c = _case(d, "claim_exclusivity")
    _operation(c)
    before, after = _physical(c)
    results = c.get("results")
    return (
        _overlap(c)
        and isinstance(results, list)
        and len(results) == 2
        and sum(bool(x) for x in results) == 1
        and after.get("state") == "CLAIMED"
        and before.get("work_id") == after.get("work_id")
    )


def check_expired_claim_reconciliation(d: Mapping[str, Any]) -> bool:
    c = _case(d, "expired_claim_reconciliation")
    _operation(c)
    _, after = _physical(c)
    return bool(after.get("state") == "PENDING_RECONCILIATION" and after.get("claimable") is False)


def check_lease_guard(d: Mapping[str, Any]) -> bool:
    c = _case(d, "lease_guard")
    _operation(c)
    before, after = _physical(c)
    attempts = c.get("attempts")
    return (
        isinstance(attempts, list)
        and len(attempts) == 3
        and before == after
        and all(isinstance(x, Mapping) and x.get("exception") for x in attempts)
    )


def check_run_revision_pin(d: Mapping[str, Any]) -> bool:
    c = _case(d, "run_revision_pin")
    op = _operation(c)
    before, after = _physical(c)
    return op.get("result", {}).get("revision_no") == before.get("revision_no") == after.get(
        "revision_no"
    ) and bool(op.get("result", {}).get("run_id"))


def check_run_replay(d: Mapping[str, Any]) -> bool:
    c = _case(d, "run_replay")
    _operation(c)
    _, after = _physical(c)
    ids = c.get("returned_run_ids")
    return (
        isinstance(ids, list)
        and len(ids) == 2
        and ids[0] == ids[1]
        and len(after.get("run_ids", [])) == 1
    )


def check_baseline_no_event(d: Mapping[str, Any]) -> bool:
    c = _case(d, "baseline_no_event")
    _operation(c)
    before, after = _physical(c)
    return bool(
        after.get("baseline_id")
        and before.get("baseline_id") is None
        and after.get("event_ids", []) == before.get("event_ids", [])
    )


def check_empty_baseline_durable(d: Mapping[str, Any]) -> bool:
    c = _case(d, "empty_baseline_durable")
    _operation(c)
    before, after = _physical(c)
    return bool(
        after.get("anchor_id")
        and after.get("listing_ids", []) == []
        and after.get("event_ids", []) == before.get("event_ids", [])
    )


def check_parser_failure_no_advance(d: Mapping[str, Any]) -> bool:
    c = _case(d, "parser_failure_no_advance")
    _operation(c)
    before, after = _physical(c)
    return set(c.get("statuses", [])) == PARSER_FAILURES and before == after


def check_new_listing_exactly_once(d: Mapping[str, Any]) -> bool:
    c = _case(d, "new_listing_exactly_once")
    op = _operation(c)
    _, after = _physical(c)
    returned = op.get("result", {}).get("event_ids", [])
    persisted = after.get("event_ids", [])
    return len(returned) == 1 and returned == persisted and len(after.get("listing_ids", [])) == 1


def check_price_change_no_event(d: Mapping[str, Any]) -> bool:
    c = _case(d, "price_change_no_event")
    _operation(c)
    before, after = _physical(c)
    return before.get("snapshot") != after.get("snapshot") and after.get(
        "event_ids", []
    ) == before.get("event_ids", [])


def check_duplicate_within_run_exactly_once(d: Mapping[str, Any]) -> bool:
    c = _case(d, "duplicate_within_run_exactly_once")
    _operation(c)
    _, after = _physical(c)
    return (
        c.get("input", {}).get("candidate_keys", [])
        == [after.get("listing_key"), after.get("listing_key")]
        and len(after.get("listing_ids", [])) == 1
    )


def check_beacon_isolation(d: Mapping[str, Any]) -> bool:
    c = _case(d, "beacon_isolation")
    _operation(c)
    _, after = _physical(c)
    return (
        after.get("beacon_a") != after.get("beacon_b")
        and after.get("beacon_b_foreign_rows", []) == []
    )


def check_absence_no_removal(d: Mapping[str, Any]) -> bool:
    c = _case(d, "absence_no_removal")
    _operation(c)
    before, after = _physical(c)
    return before.get("listing_ids") == after.get("listing_ids") and after.get(
        "event_ids"
    ) == before.get("event_ids")


def check_authority_recheck(d: Mapping[str, Any]) -> bool:
    c = _case(d, "authority_recheck")
    _operation(c)
    before, after = _physical(c)
    attempts = c.get("attempts")
    return (
        isinstance(attempts, list)
        and len(attempts) == 4
        and before == after
        and all(x.get("exception") for x in attempts if isinstance(x, Mapping))
    )


def check_idempotency_replay_and_mismatch(d: Mapping[str, Any]) -> bool:
    c = _case(d, "idempotency_replay_and_mismatch")
    _operation(c)
    before, after = _physical(c)
    return (
        c.get("returned_results", [None, None])[0] == c.get("returned_results", [None, None])[1]
        and after.get("effect_ids") == before.get("effect_ids")
        and len(after.get("terminal_ids", [])) == 1
    )


def check_concurrent_idempotency(d: Mapping[str, Any]) -> bool:
    c = _case(d, "concurrent_idempotency")
    _operation(c)
    before, after = _physical(c)
    return (
        _overlap(c)
        and len(after.get("terminal_ids", [])) - len(before.get("terminal_ids", [])) == 1
        and len(after.get("effect_ids", [])) - len(before.get("effect_ids", [])) == 1
    )


def check_concurrent_baseline_serialization(d: Mapping[str, Any]) -> bool:
    return _concurrent_baseline(d, "concurrent_baseline_serialization")


def check_concurrent_new_listing_serialization(d: Mapping[str, Any]) -> bool:
    return _concurrent_baseline(d, "concurrent_new_listing_serialization")


def _concurrent_baseline(d: Mapping[str, Any], name: str) -> bool:
    c = _case(d, name)
    _operation(c)
    before, after = _physical(c)
    return _overlap(c) and len(after.get("effect_ids", [])) - len(before.get("effect_ids", [])) == 1


def check_restart_durability(d: Mapping[str, Any]) -> bool:
    c = _case(d, "restart_durability")
    _operation(c)
    before, after = _physical(c)
    return before.get("identity") == after.get("identity") and after.get("state") in {
        "SUCCEEDED_BASELINE",
        "SUCCEEDED_DIFFERENCE",
    }


def check_foreign_state_witness(d: Mapping[str, Any]) -> bool:
    c = _case(d, "foreign_state_witness")
    _operation(c)
    before, after = _physical(c)
    return (
        before.get("capture_id") != after.get("capture_id")
        and before.get("digest") == after.get("digest")
        and before.get("semantic") == after.get("semantic")
    )


def check_raw_payload_snapshot_boundary(d: Mapping[str, Any]) -> bool:
    c = _case(d, "raw_payload_snapshot_boundary")
    _operation(c)
    _, after = _physical(c)
    max_bytes = after.get("max_utf8_bytes")
    return bool(
        set(c.get("input", {}).get("descriptors", []))
        >= {"raw", "headers", "cookies", "token", "phone"}
        and after.get("unsafe_fields", []) == []
        and isinstance(max_bytes, int)
        and max_bytes <= 32768
    )


def check_platform_event_identity(d: Mapping[str, Any]) -> bool:
    c = _case(d, "platform_event_identity")
    op = _operation(c)
    _, after = _physical(c)
    return (
        op.get("result", {}).get("event_ids", []) == after.get("event_ids", [])
        and after.get("notification_ids", []) == []
        and after.get("egress_ids", []) == []
    )


def check_no_foreign_domain_effect(d: Mapping[str, Any]) -> bool:
    c = _case(d, "no_foreign_domain_effect")
    _operation(c)
    before, after = _physical(c)
    return (
        before.get("digest") == after.get("digest")
        and after.get("notification_ids", []) == []
        and after.get("egress_ids", []) == []
    )


BEHAVIORAL_CHECKERS: dict[str, Callable[[Mapping[str, Any]], bool]] = {
    name: globals()[f"check_{name}"] for name in REQUIREMENT_IDS
}
CHECKERS = BEHAVIORAL_CHECKERS


_TAMPER_PATHS = {
    "cadence_policy": ("attempts", 0, "operation", "exception"),
    "schedule_uniqueness": ("physical_after", "schedule_ids"),
    "due_work_current_slot": ("physical_after", "due_at"),
    "due_work_coalescing": ("physical_after", "work_ids"),
    "recovery_blocks_backlog": ("physical_after", "state"),
    "due_materialization_concurrency": ("operation_b", "backend_pid"),
    "claim_exclusivity": ("results", 0),
    "expired_claim_reconciliation": ("physical_after", "claimable"),
    "lease_guard": ("attempts", 0, "exception"),
    "run_revision_pin": ("physical_after", "revision_no"),
    "run_replay": ("returned_run_ids", 1),
    "baseline_no_event": ("physical_after", "event_ids"),
    "empty_baseline_durable": ("physical_after", "anchor_id"),
    "parser_failure_no_advance": ("physical_after", "listing_ids"),
    "new_listing_exactly_once": ("physical_after", "event_ids"),
    "price_change_no_event": ("physical_after", "event_ids"),
    "duplicate_within_run_exactly_once": ("physical_after", "listing_ids"),
    "beacon_isolation": ("physical_after", "beacon_b_foreign_rows"),
    "absence_no_removal": ("physical_after", "listing_ids"),
    "authority_recheck": ("attempts", 0, "exception"),
    "idempotency_replay_and_mismatch": ("physical_after", "terminal_ids"),
    "concurrent_idempotency": ("operation_b", "backend_pid"),
    "concurrent_baseline_serialization": ("operation_b", "backend_pid"),
    "concurrent_new_listing_serialization": ("operation_b", "backend_pid"),
    "restart_durability": ("physical_after", "identity"),
    "foreign_state_witness": ("physical_after", "digest"),
    "raw_payload_snapshot_boundary": ("physical_after", "unsafe_fields"),
    "platform_event_identity": ("physical_after", "event_ids"),
    "no_foreign_domain_effect": ("physical_after", "digest"),
}


def _at(value: Any, path: tuple[Any, ...]) -> Any:
    for part in path:
        value = value[part]
    return value


def _tamper(data: Mapping[str, Any], requirement: str) -> dict[str, Any]:
    result = copy.deepcopy(dict(data))
    case = result["behavioral_cases"][requirement]
    path = _TAMPER_PATHS[requirement]
    try:
        current = _at(case, path)
    except (KeyError, IndexError, TypeError):
        raise ValueError(f"tamper path missing: {requirement}") from None
    parent = case
    for part in path[:-1]:
        parent = parent[part]
    key = path[-1]
    if key == "backend_pid" and "operation_a" in case:
        parent[key] = case["operation_a"]["backend_pid"]
        return result
    if isinstance(current, bool):
        parent[key] = not current
    elif isinstance(current, int):
        parent[key] = current + 1
    elif isinstance(current, list):
        parent[key] = list(current) + ["tampered"]
    elif isinstance(current, str):
        parent[key] = None
    else:
        parent[key] = None
    return result


BEHAVIORAL_TAMPERS = {
    name: (
        lambda data, requirement=name: (
            _tamper(data, requirement),
            (f"behavioral_cases.{requirement}",),
        )
    )
    for name in REQUIREMENT_IDS
}


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("identity", {}).get("technical_id") != TECHNICAL_ID:
        raise ValueError("identity mismatch")
    return value


def verify(data: dict[str, Any], output_dir: Path) -> None:
    if set(REQUIREMENT_IDS) != set(BEHAVIORAL_CHECKERS) or set(REQUIREMENT_IDS) != set(
        BEHAVIORAL_TAMPERS
    ):
        raise ValueError("registry equality failed")
    migration = data.get("migration")
    if (
        not isinstance(migration, Mapping)
        or not migration.get("head")
        or not migration.get("independent_connection")
    ):
        raise ValueError("migration evidence missing")
    rows: list[dict[str, Any]] = []
    for requirement, checker in BEHAVIORAL_CHECKERS.items():
        try:
            if not checker(data):
                raise ValueError(f"requirement failed: {requirement}")
            mutated, _ = BEHAVIORAL_TAMPERS[requirement](data)
            if checker(mutated):
                raise ValueError(f"causal tamper did not fail: {requirement}")
            path = _TAMPER_PATHS[requirement]
            _at(_case(data, requirement), path)
        except (KeyError, IndexError, TypeError, ValueError, OverflowError) as exc:
            raise ValueError(str(exc)) from None
        rows.append(
            {
                "requirement_id": requirement,
                "checker": checker.__name__,
                "raw_dependency_paths": [f"behavioral_cases.{requirement}"]
                + [
                    f"behavioral_cases.{requirement}."
                    + ".".join(map(str, _TAMPER_PATHS[requirement]))
                ],
                "tamper_id": requirement,
                "checker_before": True,
                "checker_after": False,
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
        verify(_load(args.evidence), args.evidence.parent)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise SystemExit(f"RF15 evidence rejected: {exc}") from None
    print("RF15_ACCEPTANCE_VERIFIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
