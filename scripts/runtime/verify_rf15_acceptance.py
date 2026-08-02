"""Independent fail-closed verifier for RF15 raw evidence and causal registries."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

TECHNICAL_ID = "RF-15-SCAN-ORCHESTRATION-DURABLE-RUNTIME-20260802-01"
REQUIREMENTS = (
    "cadence_policy",
    "due_work_uniqueness",
    "due_work_coalescing",
    "claim_exclusivity",
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
    "concurrent_comparison_serialization",
    "restart_durability",
    "foreign_state_witness",
    "raw_payload_snapshot_boundary",
    "platform_ownership_boundary",
)
FAMILIES = (
    "identity",
    "migration",
    "cadence",
    "schedule",
    "due_materialization",
    "claims",
    "runs",
    "baseline",
    "difference",
    "failure_matrix",
    "reconciliation",
    "idempotency",
    "concurrency",
    "restart",
    "foreign_state",
    "raw_payload_boundary",
    "platform_effects",
)


def load(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise SystemExit(f"invalid object: {path}")
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence", type=Path)
    args = parser.parse_args()
    data = load(args.evidence)
    root = args.evidence.parent
    requirement_map = load(root / "rf15-requirement-map.json")
    tamper_matrix = load(root / "rf15-tamper-matrix.json")
    identity = data.get("identity", {})
    migration = data.get("migration", {})
    if (
        identity.get("technical_id") != TECHNICAL_ID
        or identity.get("candidate_sha")
        != subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    ):
        raise SystemExit("identity mismatch")
    if not str(identity.get("parent_sha", "")) or not str(identity.get("tree_sha", "")):
        raise SystemExit("incomplete git identity")
    if (
        migration.get("table_count") != 51
        or migration.get("global_index_count") != 73
        or migration.get("scan_index_count") != 8
    ):
        raise SystemExit("accepted schema counts are not proven")
    if set(migration.get("tables", ())) != {
        "scan_schedules",
        "scan_work_items",
        "scan_runs",
        "scan_listing_observations",
        "scan_beacon_listing_state",
        "scan_anchors",
        "alembic_version",
    } and not set(migration.get("tables", ())).issuperset(
        {
            "scan_schedules",
            "scan_work_items",
            "scan_runs",
            "scan_listing_observations",
            "scan_beacon_listing_state",
            "scan_anchors",
        }
    ):
        raise SystemExit("scan schema evidence incomplete")
    families = data.get("families", {})
    if set(families) != set(FAMILIES):
        raise SystemExit("evidence families incomplete")
    if data.get("raw_payload_boundary", {}).get("payload_material_present") is not False:
        raise SystemExit("raw payload boundary violated")
    raw_cases = data.get("raw_cases", [])
    raw_ids = {item.get("case_id") for item in raw_cases if isinstance(item, dict)}
    if raw_ids != set(REQUIREMENTS) or any(
        item.get("observed") is not True for item in raw_cases if isinstance(item, dict)
    ):
        raise SystemExit("behavioral raw evidence incomplete")
    map_items = requirement_map.get("requirements", [])
    tamper_items = tamper_matrix.get("tampers", [])
    map_ids = {item.get("requirement_id") for item in map_items if isinstance(item, dict)}
    tamper_ids = {item.get("requirement_id") for item in tamper_items if isinstance(item, dict)}
    if (
        map_ids != set(REQUIREMENTS)
        or tamper_ids != set(REQUIREMENTS)
        or len(map_items) != len(REQUIREMENTS)
        or len(tamper_items) != len(REQUIREMENTS)
    ):
        raise SystemExit("registry mismatch")
    if any(
        item.get("producer_derived_field_consumed") is not False
        for item in map_items
        if isinstance(item, dict)
    ):
        raise SystemExit("producer-derived acceptance field used")
    if any(
        item.get("checker_before") is not True
        or item.get("checker_after") is not False
        or item.get("expected_causal_failure") is not True
        for item in tamper_items
        if isinstance(item, dict)
    ):
        raise SystemExit("tamper matrix incomplete")
    print("RF15_ACCEPTANCE_VERIFIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
