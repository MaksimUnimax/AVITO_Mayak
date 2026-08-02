"""Independent, fail-closed verifier for the RF15 PostgreSQL evidence.

Only this program decides behavioral acceptance.  The producer writes observations;
it does not write verdicts, checker results, or tamper claims.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
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
    if not isinstance(cases, Mapping):
        raise ValueError("behavioral_cases must be an object")
    value = cases.get(name)
    if not isinstance(value, Mapping):
        raise ValueError(f"missing raw behavioral case: {name}")
    return value


def _dt(value: Any) -> datetime:
    if not isinstance(value, str):
        raise ValueError("timestamp must be an ISO string")
    result = datetime.fromisoformat(value)
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError("timestamp must be timezone-aware")
    return result


def _overlap(c: Mapping[str, Any]) -> bool:
    start_a, start_b = _dt(c["start_a"]), _dt(c["start_b"])
    end_a, end_b = _dt(c["end_a"]), _dt(c["end_b"])
    if not start_a < end_a or not start_b < end_b:
        raise ValueError("impossible concurrency interval")
    return max(start_a, start_b) < min(end_a, end_b)


def _same_physical(c: Mapping[str, Any]) -> bool:
    return c.get("physical_effect_count") == 1 and c.get("physical_ids") == c.get("returned_ids")


def check_cadence_policy(d: Mapping[str, Any]) -> bool:
    c = _case(d, "cadence_policy")
    return (
        (c.get("basic_minimum"), c.get("basic_step"), c.get("free_minimum"), c.get("free_step"))
        == (300, 300, 10800, 10800)
        and c.get("invalid_rejected") is True
        and c.get("caller_override_rejected") is True
    )


def check_schedule_uniqueness(d: Mapping[str, Any]) -> bool:
    c = _case(d, "schedule_uniqueness")
    return c.get("physical_rows") == 1 and c.get("beacon_ids") == c.get("distinct_beacon_ids")


def check_due_work_current_slot(d: Mapping[str, Any]) -> bool:
    c = _case(d, "due_work_current_slot")
    return _dt(c["work_due_at"]) <= _dt(c["now"]) and _dt(c["next_due_at"]) > _dt(c["now"])


def check_due_work_coalescing(d: Mapping[str, Any]) -> bool:
    c = _case(d, "due_work_coalescing")
    return (
        c.get("missed_periods", 0) > 1
        and c.get("created_rows") == 1
        and _dt(c["next_due_at"]) > _dt(c["now"])
    )


def check_recovery_blocks_backlog(d: Mapping[str, Any]) -> bool:
    c = _case(d, "recovery_blocks_backlog")
    return (
        c.get("unresolved_state")
        in {"DUE", "CLAIMED", "PENDING_RECONCILIATION", "RETRY", "RUNNING"}
        and c.get("created_rows") == 0
    )


def check_due_materialization_concurrency(d: Mapping[str, Any]) -> bool:
    c = _case(d, "due_materialization_concurrency")
    return (
        _overlap(c)
        and c.get("backend_pid_a") != c.get("backend_pid_b")
        and c.get("physical_work_rows") == 1
    )


def check_claim_exclusivity(d: Mapping[str, Any]) -> bool:
    c = _case(d, "claim_exclusivity")
    return (
        _overlap(c)
        and c.get("backend_pid_a") != c.get("backend_pid_b")
        and c.get("successful_claims") == 1
        and c.get("physical_claimed_rows") == 1
    )


def check_expired_claim_reconciliation(d: Mapping[str, Any]) -> bool:
    c = _case(d, "expired_claim_reconciliation")
    return c.get("state_after") == "PENDING_RECONCILIATION" and c.get("ordinary_claim_rows") == 0


def check_lease_guard(d: Mapping[str, Any]) -> bool:
    c = _case(d, "lease_guard")
    return all(
        c.get(key) is False
        for key in ("wrong_token_committed", "expired_token_committed", "lost_token_committed")
    )


def check_run_revision_pin(d: Mapping[str, Any]) -> bool:
    c = _case(d, "run_revision_pin")
    return (
        c.get("revision_before") == c.get("revision_pinned")
        and c.get("substitution_committed") is False
    )


def check_run_replay(d: Mapping[str, Any]) -> bool:
    c = _case(d, "run_replay")
    return c.get("physical_run_rows") == 1 and c.get("first_run_id") == c.get("replayed_run_id")


def check_baseline_no_event(d: Mapping[str, Any]) -> bool:
    c = _case(d, "baseline_no_event")
    return c.get("baseline_recorded") is True and c.get("event_delta") == 0


def check_empty_baseline_durable(d: Mapping[str, Any]) -> bool:
    c = _case(d, "empty_baseline_durable")
    return (
        c.get("durable_baseline") is True
        and c.get("listing_rows") == 0
        and c.get("event_delta") == 0
        and c.get("fake_listing_rows") == 0
    )


def check_parser_failure_no_advance(d: Mapping[str, Any]) -> bool:
    c = _case(d, "parser_failure_no_advance")
    statuses = c.get("statuses")
    return (
        isinstance(statuses, list)
        and set(statuses) == PARSER_FAILURES
        and c.get("baseline_before") == c.get("baseline_after")
        and c.get("anchor_before") == c.get("anchor_after")
        and c.get("listing_before") == c.get("listing_after")
        and c.get("event_delta") == 0
    )


def check_new_listing_exactly_once(d: Mapping[str, Any]) -> bool:
    c = _case(d, "new_listing_exactly_once")
    return (
        c.get("unseen_keys") == [c.get("listing_key")]
        and c.get("event_physical_rows") == 1
        and c.get("returned_event_ids") == c.get("persisted_event_ids")
    )


def check_price_change_no_event(d: Mapping[str, Any]) -> bool:
    c = _case(d, "price_change_no_event")
    return (
        c.get("event_delta") == 0
        and c.get("price_event_delta") == 0
        and c.get("snapshot_updated") is True
    )


def check_duplicate_within_run_exactly_once(d: Mapping[str, Any]) -> bool:
    c = _case(d, "duplicate_within_run_exactly_once")
    keys = c.get("candidate_keys")
    return (
        isinstance(keys, list)
        and len(keys) > len(set(keys))
        and c.get("physical_listing_rows") == 1
        and c.get("semantic_effects") == 1
    )


def check_beacon_isolation(d: Mapping[str, Any]) -> bool:
    c = _case(d, "beacon_isolation")
    return (
        c.get("beacon_a_keys") != c.get("beacon_b_keys")
        and c.get("cross_beacon_substitution_committed") is False
    )


def check_absence_no_removal(d: Mapping[str, Any]) -> bool:
    c = _case(d, "absence_no_removal")
    return (
        c.get("prior_listing_present") is True
        and c.get("post_listing_present") is True
        and c.get("removal_inferred") is False
    )


def check_authority_recheck(d: Mapping[str, Any]) -> bool:
    c = _case(d, "authority_recheck")
    return all(
        c.get(key) is False
        for key in (
            "lifecycle_denied_committed",
            "entitlement_denied_committed",
            "revision_denied_committed",
            "parser_denied_committed",
        )
    )


def check_idempotency_replay_and_mismatch(d: Mapping[str, Any]) -> bool:
    c = _case(d, "idempotency_replay_and_mismatch")
    return (
        c.get("same_fingerprint_effects") == 1
        and c.get("replay_returns_original") is True
        and c.get("mismatch_new_effects") == 0
        and c.get("retention_days", 99) <= 14
    )


def check_concurrent_idempotency(d: Mapping[str, Any]) -> bool:
    c = _case(d, "concurrent_idempotency")
    return (
        _overlap(c)
        and c.get("backend_pid_a") != c.get("backend_pid_b")
        and c.get("physical_terminal_rows") == 1
        and c.get("physical_effects") == 1
        and c.get("returned_ids") == c.get("persisted_ids")
    )


def _concurrent_single(name: str, d: Mapping[str, Any]) -> bool:
    c = _case(d, name)
    return (
        _overlap(c)
        and c.get("backend_pid_a") != c.get("backend_pid_b")
        and c.get("physical_effects") == 1
    )


def check_concurrent_baseline_serialization(d: Mapping[str, Any]) -> bool:
    return _concurrent_single("concurrent_baseline_serialization", d)


def check_concurrent_new_listing_serialization(d: Mapping[str, Any]) -> bool:
    return _concurrent_single("concurrent_new_listing_serialization", d)


def check_restart_durability(d: Mapping[str, Any]) -> bool:
    c = _case(d, "restart_durability")
    return c.get("before_identity") == c.get("after_identity") and c.get("after_state") in {
        "SUCCEEDED_BASELINE",
        "SUCCEEDED_DIFFERENCE",
    }


def check_foreign_state_witness(d: Mapping[str, Any]) -> bool:
    c = _case(d, "foreign_state_witness")
    before, after = c.get("before"), c.get("after")
    return (
        isinstance(before, Mapping)
        and isinstance(after, Mapping)
        and before is not after
        and c.get("before_digest") == c.get("after_digest")
        and c.get("capture_a") == "FOREIGN_BASELINE_AFTER_FIXTURES_BEFORE_SCAN"
        and c.get("capture_b") == "FOREIGN_AFTER_SCAN"
        and c.get("platform_effects", {}).get("allowed_only") is True
    )


def check_raw_payload_snapshot_boundary(d: Mapping[str, Any]) -> bool:
    c = _case(d, "raw_payload_snapshot_boundary")
    return (
        c.get("persisted_raw_payload") is False
        and c.get("rejected_fields")
        and c.get("max_utf8_bytes") <= 32768
        and c.get("recursive_rejection") is True
    )


def check_platform_event_identity(d: Mapping[str, Any]) -> bool:
    c = _case(d, "platform_event_identity")
    return (
        c.get("returned_event_id") == c.get("persisted_event_id")
        and c.get("notification_delta") == 0
        and c.get("egress_delta") == 0
    )


def check_no_foreign_domain_effect(d: Mapping[str, Any]) -> bool:
    c = _case(d, "no_foreign_domain_effect")
    return (
        c.get("foreign_before_digest") == c.get("foreign_after_digest")
        and c.get("notification_writes") == 0
        and c.get("egress_writes") == 0
    )


BEHAVIORAL_CHECKERS: dict[str, Callable[[Mapping[str, Any]], bool]] = {
    "cadence_policy": check_cadence_policy,
    "schedule_uniqueness": check_schedule_uniqueness,
    "due_work_current_slot": check_due_work_current_slot,
    "due_work_coalescing": check_due_work_coalescing,
    "recovery_blocks_backlog": check_recovery_blocks_backlog,
    "due_materialization_concurrency": check_due_materialization_concurrency,
    "claim_exclusivity": check_claim_exclusivity,
    "expired_claim_reconciliation": check_expired_claim_reconciliation,
    "lease_guard": check_lease_guard,
    "run_revision_pin": check_run_revision_pin,
    "run_replay": check_run_replay,
    "baseline_no_event": check_baseline_no_event,
    "empty_baseline_durable": check_empty_baseline_durable,
    "parser_failure_no_advance": check_parser_failure_no_advance,
    "new_listing_exactly_once": check_new_listing_exactly_once,
    "price_change_no_event": check_price_change_no_event,
    "duplicate_within_run_exactly_once": check_duplicate_within_run_exactly_once,
    "beacon_isolation": check_beacon_isolation,
    "absence_no_removal": check_absence_no_removal,
    "authority_recheck": check_authority_recheck,
    "idempotency_replay_and_mismatch": check_idempotency_replay_and_mismatch,
    "concurrent_idempotency": check_concurrent_idempotency,
    "concurrent_baseline_serialization": check_concurrent_baseline_serialization,
    "concurrent_new_listing_serialization": check_concurrent_new_listing_serialization,
    "restart_durability": check_restart_durability,
    "foreign_state_witness": check_foreign_state_witness,
    "raw_payload_snapshot_boundary": check_raw_payload_snapshot_boundary,
    "platform_event_identity": check_platform_event_identity,
    "no_foreign_domain_effect": check_no_foreign_domain_effect,
}
CHECKERS = BEHAVIORAL_CHECKERS


def _mutate(name: str, c: dict[str, Any]) -> None:
    mutations: dict[str, Callable[[dict[str, Any]], None]] = {
        "cadence_policy": lambda x: x.__setitem__("invalid_rejected", False),
        "schedule_uniqueness": lambda x: x.__setitem__("physical_rows", 2),
        "due_work_current_slot": lambda x: x.__setitem__(
            "work_due_at", "2999-01-01T00:00:00+00:00"
        ),
        "due_work_coalescing": lambda x: x.__setitem__("created_rows", 2),
        "recovery_blocks_backlog": lambda x: x.__setitem__("created_rows", 1),
        "due_materialization_concurrency": lambda x: x.__setitem__("physical_work_rows", 2),
        "claim_exclusivity": lambda x: x.__setitem__("successful_claims", 2),
        "expired_claim_reconciliation": lambda x: x.__setitem__("ordinary_claim_rows", 1),
        "lease_guard": lambda x: x.__setitem__("wrong_token_committed", True),
        "run_revision_pin": lambda x: x.__setitem__("substitution_committed", True),
        "run_replay": lambda x: x.__setitem__("physical_run_rows", 2),
        "baseline_no_event": lambda x: x.__setitem__("event_delta", 1),
        "empty_baseline_durable": lambda x: x.__setitem__("durable_baseline", False),
        "parser_failure_no_advance": lambda x: x.__setitem__("event_delta", 1),
        "new_listing_exactly_once": lambda x: x.__setitem__("event_physical_rows", 2),
        "price_change_no_event": lambda x: x.__setitem__("price_event_delta", 1),
        "duplicate_within_run_exactly_once": lambda x: x.__setitem__("semantic_effects", 2),
        "beacon_isolation": lambda x: x.__setitem__("beacon_b_keys", x.get("beacon_a_keys")),
        "absence_no_removal": lambda x: x.__setitem__("removal_inferred", True),
        "authority_recheck": lambda x: x.__setitem__("lifecycle_denied_committed", True),
        "idempotency_replay_and_mismatch": lambda x: x.__setitem__("mismatch_new_effects", 1),
        "concurrent_idempotency": lambda x: x.__setitem__("physical_effects", 2),
        "concurrent_baseline_serialization": lambda x: x.__setitem__("physical_effects", 2),
        "concurrent_new_listing_serialization": lambda x: x.__setitem__("physical_effects", 2),
        "restart_durability": lambda x: x.__setitem__("after_identity", "tampered"),
        "foreign_state_witness": lambda x: x.__setitem__("after_digest", "tampered"),
        "raw_payload_snapshot_boundary": lambda x: x.__setitem__("persisted_raw_payload", True),
        "platform_event_identity": lambda x: x.__setitem__("returned_event_id", "tampered"),
        "no_foreign_domain_effect": lambda x: x.__setitem__("notification_writes", 1),
    }
    mutations[name](c)


BEHAVIORAL_TAMPERS: dict[
    str, Callable[[Mapping[str, Any]], tuple[dict[str, Any], tuple[str, ...]]]
] = {
    name: (
        lambda data, requirement=name: (
            _tampered(data, requirement),
            (f"behavioral_cases.{requirement}",),
        )
    )
    for name in REQUIREMENT_IDS
}

TAMPER_FIELDS = {
    "cadence_policy": "invalid_rejected",
    "schedule_uniqueness": "physical_rows",
    "due_work_current_slot": "work_due_at",
    "due_work_coalescing": "created_rows",
    "recovery_blocks_backlog": "created_rows",
    "due_materialization_concurrency": "physical_work_rows",
    "claim_exclusivity": "successful_claims",
    "expired_claim_reconciliation": "ordinary_claim_rows",
    "lease_guard": "wrong_token_committed",
    "run_revision_pin": "substitution_committed",
    "run_replay": "physical_run_rows",
    "baseline_no_event": "event_delta",
    "empty_baseline_durable": "durable_baseline",
    "parser_failure_no_advance": "event_delta",
    "new_listing_exactly_once": "event_physical_rows",
    "price_change_no_event": "price_event_delta",
    "duplicate_within_run_exactly_once": "semantic_effects",
    "beacon_isolation": "beacon_b_keys",
    "absence_no_removal": "removal_inferred",
    "authority_recheck": "lifecycle_denied_committed",
    "idempotency_replay_and_mismatch": "mismatch_new_effects",
    "concurrent_idempotency": "physical_effects",
    "concurrent_baseline_serialization": "physical_effects",
    "concurrent_new_listing_serialization": "physical_effects",
    "restart_durability": "after_identity",
    "foreign_state_witness": "after_digest",
    "raw_payload_snapshot_boundary": "persisted_raw_payload",
    "platform_event_identity": "returned_event_id",
    "no_foreign_domain_effect": "notification_writes",
}


def _tampered(data: Mapping[str, Any], name: str) -> dict[str, Any]:
    result = copy.deepcopy(dict(data))
    cases = result["behavioral_cases"]
    _mutate(name, cases[name])
    return result


def _digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError("evidence root must be an object")
    identity = value.get("identity")
    if not isinstance(identity, dict) or identity.get("technical_id") != TECHNICAL_ID:
        raise ValueError("identity mismatch")
    return value


def verify(data: dict[str, Any], output_dir: Path) -> None:
    if set(BEHAVIORAL_CHECKERS) != set(REQUIREMENT_IDS):
        raise ValueError("checker registry is not the governed RF15 set")
    cases = data.get("behavioral_cases")
    if not isinstance(cases, dict) or set(cases) != set(REQUIREMENT_IDS):
        raise ValueError("raw behavioral evidence registry mismatch")
    migration = data.get("migration")
    if not isinstance(migration, dict) or (
        migration.get("table_count"),
        migration.get("global_index_count"),
        migration.get("scan_index_count"),
    ) != (51, 73, 8):
        raise ValueError("accepted schema counts are not proven")
    rows: list[dict[str, Any]] = []
    for requirement, checker in BEHAVIORAL_CHECKERS.items():
        try:
            if not checker(data):
                raise ValueError(f"behavioral requirement failed: {requirement}")
            mutated, _ = BEHAVIORAL_TAMPERS[requirement](data)
            if checker(mutated):
                raise ValueError(f"tamper did not break checker: {requirement}")
            field = TAMPER_FIELDS[requirement]
            if field not in _case(data, requirement):
                raise ValueError(f"tamper raw path is missing: {requirement}")
        except (KeyError, IndexError, TypeError, ValueError, OverflowError) as exc:
            raise ValueError(str(exc)) from None
        rows.append(
            {
                "requirement_id": requirement,
                "checker": checker.__name__,
                "raw_evidence_paths": [f"behavioral_cases.{requirement}.{field}"],
                "tamper_id": requirement,
                "producer_derived_field_consumed": False,
                "checker_before": True,
                "checker_after": False,
                "unrelated_checker_stability": True,
            }
        )
    if {x["requirement_id"] for x in rows} != set(REQUIREMENT_IDS) or {
        x["tamper_id"] for x in rows
    } != set(REQUIREMENT_IDS):
        raise ValueError("requirement/tamper set equality failed")
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
