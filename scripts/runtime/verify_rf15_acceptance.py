"""Fail-closed verifier for the RF15 raw PostgreSQL transcript.

The producer records facts only.  This module owns all acceptance conclusions,
and each requirement declares the exact raw leaves consumed by its checker.
"""

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
    if not isinstance(value, Mapping) or not isinstance(value.get("callable"), str):
        raise ValueError("raw operation missing")
    if not isinstance(value.get("input"), Mapping):
        raise ValueError("raw operation input missing")
    if ("result" in value) == ("exception" in value):
        raise ValueError("raw operation must contain result xor exception")
    if _time(value.get("started_at")) >= _time(value.get("finished_at")):
        raise ValueError("invalid raw operation interval")
    if not isinstance(value.get("backend_pid"), int) or isinstance(value.get("backend_pid"), bool):
        raise ValueError("invalid backend identity")
    exception = value.get("exception")
    if exception is not None and not isinstance(exception, Mapping):
        raise ValueError("malformed exception")
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


def _case(data: Mapping[str, Any], name: str) -> Mapping[str, Any]:
    cases = data.get("behavioral_cases")
    if not isinstance(cases, Mapping) or set(cases) != set(REQUIREMENT_IDS):
        raise ValueError("behavioral case registry mismatch")
    case = cases.get(name)
    if not isinstance(case, Mapping):
        raise ValueError("behavioral case is not an object")
    return case


def _success(case: Mapping[str, Any], needle: str) -> bool:
    return any(needle in str(op["callable"]) and "result" in op for op in _ops(case))


def _physical(case: Mapping[str, Any]) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    before, after = case.get("physical_before"), case.get("physical_after")
    if not isinstance(before, Mapping) or not isinstance(after, Mapping):
        raise ValueError("physical observations missing")
    for observation in (before, after):
        for key in ("schedule_rows", "work_rows", "run_rows", "listing_rows", "event_ids"):
            if not isinstance(observation.get(key), list):
                raise ValueError(f"missing physical leaf: {key}")
    return before, after


def _rejects(case: Mapping[str, Any], count: int | None, classes: set[str]) -> bool:
    attempts = case.get("attempts")
    if not isinstance(attempts, list) or (count is not None and len(attempts) < count):
        return False
    for item in attempts:
        if not isinstance(item, Mapping) or not isinstance(item.get("operation"), Mapping):
            return False
        operation = item["operation"]
        if operation.get("exception", {}).get("class") not in classes:
            return False
        if "physical_before" in item or "physical_after" in item:
            if item.get("physical_before") != item.get("physical_after"):
                return False
    return True


def _terminal(case: Mapping[str, Any]) -> bool:
    before, after = _physical(case)
    return _success(case, "commit_comparison") and before != after


def _concurrent(case: Mapping[str, Any], needle: str) -> bool:
    a, b = case.get("operation_a"), case.get("operation_b")
    if not isinstance(a, Mapping) or not isinstance(b, Mapping):
        return False
    try:
        return (
            needle in str(a["callable"])
            and needle in str(b["callable"])
            and isinstance(a["backend_pid"], int)
            and isinstance(b["backend_pid"], int)
            and a["backend_pid"] != b["backend_pid"]
            and _time(a["started_at"]) < _time(b["finished_at"])
            and _time(b["started_at"]) < _time(a["finished_at"])
            and _time(case["race_started_at"])
            <= min(_time(a["started_at"]), _time(b["started_at"]))
            and max(_time(a["finished_at"]), _time(b["finished_at"]))
            <= _time(case["race_finished_at"])
        )
    except (KeyError, TypeError, ValueError):
        return False


def _check(name: str, case: Mapping[str, Any]) -> bool:
    """Select the requirement branch before reading any branch-specific leaf."""
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
            attempts = case["attempts"]
            safe = case["safe_persistence"]
            return (
                _rejects(case, 15, {"ValidationError", "ValueError"})
                and isinstance(safe, Mapping)
                and safe["successful_terminal"] is True
                and safe["serialized_size"] <= 32768
                and not safe["unsafe_persisted_values"]
                and not safe["raw_provider_body"]
                and len(attempts) >= 15
            )
        if name in {"foreign_state_witness", "no_foreign_domain_effect"}:
            branch = case["rf15_physical"]
            before, after = _physical(branch)
            return (
                _terminal(branch)
                and before["semantic"] == after["semantic"]
                and _time(before["observed_at"])
                < _time(branch["operation"]["started_at"])
                < _time(branch["operation"]["finished_at"])
                < _time(after["observed_at"])
            )
        before, after = _physical(case)
        if name == "schedule_uniqueness":
            return _success(case, "create_or_update") and len(after["schedule_rows"]) == 1
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
            operation = case["operation"]
            return (
                "start_run" in str(operation["callable"])
                and len(after["run_rows"]) == len(before["run_rows"])
                and (
                    operation.get("result", {}).get("replayed") is True
                    or operation.get("exception", {}).get("class")
                    in {"RunAlreadyStarted", "DependencyBlocked"}
                )
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
                and case["scope"]["a"]["beacon_id"] == after["beacon_id"]
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
                and case["operation_replay"].get("result") is not None
                and case["operation_mismatch"]["exception"]["class"] == "IdempotencyMismatch"
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
        if name == "platform_event_identity":
            return (
                _terminal(case)
                and case["returned_event_id"] == case["persisted_event_id"]
                and case["returned_event_id"] in after["event_ids"]
            )
    except (KeyError, IndexError, TypeError, ValueError, OverflowError, AttributeError):
        return False
    return False


CHECKERS = {
    name: (lambda data, requirement=name: _check(requirement, _case(data, requirement)))
    for name in REQUIREMENT_IDS
}
BEHAVIORAL_CHECKERS = CHECKERS

# Every requirement is intentionally listed.  There is no default/fallback.
RAW_DEPENDENCY_PATHS = {
    "cadence_policy": [
        "behavioral_cases.cadence_policy.operation.result",
        "behavioral_cases.cadence_policy.attempts[*].operation.exception.class",
    ],
    "schedule_uniqueness": [
        "behavioral_cases.schedule_uniqueness.operation.result",
        "behavioral_cases.schedule_uniqueness.physical_after.schedule_rows",
    ],
    "due_work_current_slot": [
        "behavioral_cases.due_work_current_slot.operation.input.now",
        "behavioral_cases.due_work_current_slot.physical_after.work_rows",
    ],
    "due_work_coalescing": [
        "behavioral_cases.due_work_coalescing.operation.input.now",
        "behavioral_cases.due_work_coalescing.physical_after.schedule_rows",
        "behavioral_cases.due_work_coalescing.physical_after.work_rows",
    ],
    "recovery_blocks_backlog": [
        "behavioral_cases.recovery_blocks_backlog.operation",
        "behavioral_cases.recovery_blocks_backlog.materialize_operation",
        "behavioral_cases.recovery_blocks_backlog.physical_before.work_rows",
        "behavioral_cases.recovery_blocks_backlog.physical_after.work_rows",
    ],
    "due_materialization_concurrency": [
        "behavioral_cases.due_materialization_concurrency.operation_a",
        "behavioral_cases.due_materialization_concurrency.operation_b",
        "behavioral_cases.due_materialization_concurrency.race_started_at",
        "behavioral_cases.due_materialization_concurrency.race_finished_at",
        "behavioral_cases.due_materialization_concurrency.physical_after.work_rows",
    ],
    "claim_exclusivity": [
        "behavioral_cases.claim_exclusivity.operation_a",
        "behavioral_cases.claim_exclusivity.operation_b",
        "behavioral_cases.claim_exclusivity.physical_after.work_rows",
    ],
    "expired_claim_reconciliation": [
        "behavioral_cases.expired_claim_reconciliation.attempts[*].operation.exception.class",
        "behavioral_cases.expired_claim_reconciliation.physical_after.work_rows",
    ],
    "lease_guard": [
        "behavioral_cases.lease_guard.attempts[*].operation.exception.class",
        "behavioral_cases.lease_guard.physical_before",
        "behavioral_cases.lease_guard.physical_after",
    ],
    "run_revision_pin": [
        "behavioral_cases.run_revision_pin.operation.result.revision_no",
        "behavioral_cases.run_revision_pin.physical_after.run_rows",
    ],
    "run_replay": [
        "behavioral_cases.run_replay.operation.result.replayed",
        "behavioral_cases.run_replay.physical_before.run_rows",
        "behavioral_cases.run_replay.physical_after.run_rows",
    ],
    "baseline_no_event": [
        "behavioral_cases.baseline_no_event.physical_before.event_ids",
        "behavioral_cases.baseline_no_event.physical_after.listing_rows",
    ],
    "empty_baseline_durable": [
        "behavioral_cases.empty_baseline_durable.physical_after.run_rows",
        "behavioral_cases.empty_baseline_durable.physical_after.event_ids",
    ],
    "parser_failure_no_advance": [
        "behavioral_cases.parser_failure_no_advance.statuses",
        "behavioral_cases.parser_failure_no_advance.attempts[*].operation.exception.class",
    ],
    "new_listing_exactly_once": [
        "behavioral_cases.new_listing_exactly_once.physical_before.listing_rows",
        "behavioral_cases.new_listing_exactly_once.physical_after.event_ids",
    ],
    "price_change_no_event": [
        "behavioral_cases.price_change_no_event.physical_before.listing_rows",
        "behavioral_cases.price_change_no_event.physical_after.event_ids",
    ],
    "duplicate_within_run_exactly_once": [
        "behavioral_cases.duplicate_within_run_exactly_once.physical_after.listing_rows",
        "behavioral_cases.duplicate_within_run_exactly_once.physical_after.event_ids",
    ],
    "beacon_isolation": [
        "behavioral_cases.beacon_isolation.scope.a.beacon_id",
        "behavioral_cases.beacon_isolation.scope.b.beacon_id",
        "behavioral_cases.beacon_isolation.physical_after.beacon_id",
    ],
    "absence_no_removal": [
        "behavioral_cases.absence_no_removal.physical_before.listing_rows",
        "behavioral_cases.absence_no_removal.physical_after.listing_rows",
    ],
    "authority_recheck": [
        "behavioral_cases.authority_recheck.attempts[*].operation.exception.class",
        "behavioral_cases.authority_recheck.physical_before",
        "behavioral_cases.authority_recheck.physical_after",
    ],
    "idempotency_replay_and_mismatch": [
        "behavioral_cases.idempotency_replay_and_mismatch.operation_replay.result",
        "behavioral_cases.idempotency_replay_and_mismatch.operation_mismatch.exception.class",
    ],
    "concurrent_idempotency": [
        "behavioral_cases.concurrent_idempotency.operation_a",
        "behavioral_cases.concurrent_idempotency.operation_b",
        "behavioral_cases.concurrent_idempotency.physical_after.event_ids",
    ],
    "concurrent_baseline_serialization": [
        "behavioral_cases.concurrent_baseline_serialization.operation_a",
        "behavioral_cases.concurrent_baseline_serialization.operation_b",
        "behavioral_cases.concurrent_baseline_serialization.physical_after.listing_rows",
    ],
    "concurrent_new_listing_serialization": [
        "behavioral_cases.concurrent_new_listing_serialization.operation_a",
        "behavioral_cases.concurrent_new_listing_serialization.operation_b",
        "behavioral_cases.concurrent_new_listing_serialization.physical_after.event_ids",
    ],
    "restart_durability": [
        "behavioral_cases.restart_durability.physical_after.second_lifetime.backend_pid",
        "behavioral_cases.restart_durability.physical_after.second_lifetime.run_rows",
    ],
    "foreign_state_witness": [
        "behavioral_cases.foreign_state_witness.rf15_physical.physical_before.semantic",
        "behavioral_cases.foreign_state_witness.rf15_physical.physical_after.semantic",
        "behavioral_cases.foreign_state_witness.rf15_physical.operation.started_at",
    ],
    "raw_payload_snapshot_boundary": [
        "behavioral_cases.raw_payload_snapshot_boundary.attempts[*].operation.exception.class",
        "behavioral_cases.raw_payload_snapshot_boundary.safe_persistence.serialized_size",
        "behavioral_cases.raw_payload_snapshot_boundary.safe_persistence.unsafe_persisted_values",
    ],
    "platform_event_identity": [
        "behavioral_cases.platform_event_identity.returned_event_id",
        "behavioral_cases.platform_event_identity.persisted_event_id",
        "behavioral_cases.platform_event_identity.physical_after.event_ids",
    ],
    "no_foreign_domain_effect": [
        "behavioral_cases.no_foreign_domain_effect.rf15_physical.physical_before.semantic",
        "behavioral_cases.no_foreign_domain_effect.rf15_physical.physical_after.semantic",
        "behavioral_cases.no_foreign_domain_effect.rf15_physical.operation.finished_at",
    ],
}

TAMPER_PATHS = {
    "cadence_policy": ("operation", "result", "basic"),
    "schedule_uniqueness": ("physical_after", "schedule_rows"),
    "due_work_current_slot": ("physical_after", "work_rows"),
    "due_work_coalescing": ("physical_after", "schedule_rows"),
    "recovery_blocks_backlog": ("materialize_operation", "result"),
    "due_materialization_concurrency": ("operation_a", "backend_pid"),
    "claim_exclusivity": ("physical_after", "work_rows"),
    "expired_claim_reconciliation": ("physical_after", "work_rows"),
    "lease_guard": ("attempts", 0, "operation", "exception", "class"),
    "run_revision_pin": ("operation", "result", "revision_no"),
    "run_replay": ("operation", "result", "replayed"),
    "baseline_no_event": ("physical_after", "event_ids"),
    "empty_baseline_durable": ("physical_after", "run_rows"),
    "parser_failure_no_advance": ("attempts", 0, "operation", "exception", "class"),
    "new_listing_exactly_once": ("physical_after", "listing_rows"),
    "price_change_no_event": ("physical_after", "listing_rows"),
    "duplicate_within_run_exactly_once": ("physical_after", "listing_rows"),
    "beacon_isolation": ("scope", "b", "beacon_id"),
    "absence_no_removal": ("physical_after", "listing_rows"),
    "authority_recheck": ("attempts", 0, "operation", "exception", "class"),
    "idempotency_replay_and_mismatch": ("operation_mismatch", "exception", "class"),
    "concurrent_idempotency": ("physical_after", "event_ids"),
    "concurrent_baseline_serialization": ("physical_after", "listing_rows"),
    "concurrent_new_listing_serialization": ("physical_after", "event_ids"),
    "restart_durability": ("physical_after", "second_lifetime", "run_rows"),
    "foreign_state_witness": ("rf15_physical", "physical_after", "semantic"),
    "raw_payload_snapshot_boundary": ("safe_persistence", "successful_terminal"),
    "platform_event_identity": ("persisted_event_id",),
    "no_foreign_domain_effect": ("rf15_physical", "physical_after", "semantic"),
}


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


def _diagnostics(data: Mapping[str, Any], original: Mapping[str, bool]) -> list[dict[str, Any]]:
    rows = []
    for name in REQUIREMENT_IDS:
        case = (
            data.get("behavioral_cases", {}).get(name, {})
            if isinstance(data.get("behavioral_cases"), Mapping)
            else {}
        )
        exceptions = (
            [
                str(item.get("operation", {}).get("exception", {}).get("class"))
                for item in case.get("attempts", [])
                if isinstance(item, Mapping)
            ]
            if isinstance(case, Mapping)
            else []
        )
        rows.append(
            {
                "requirement_id": name,
                "original_checker": bool(original.get(name, False)),
                "failure_reason_category": "checker_false"
                if not original.get(name, False)
                else "none",
                "required_dependency_paths": RAW_DEPENDENCY_PATHS[name],
                "encountered_operation_exception_classes": exceptions,
            }
        )
    return rows


def verify(data: dict[str, Any], output_dir: Path) -> None:
    original: dict[str, bool] = {}
    for name in REQUIREMENT_IDS:
        try:
            original[name] = bool(CHECKERS[name](data))
        except (KeyError, IndexError, TypeError, ValueError):
            original[name] = False
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
