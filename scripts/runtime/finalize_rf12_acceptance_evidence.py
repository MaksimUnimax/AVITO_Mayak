"""Finalize RF-12 evidence with raw snapshots captured after Docker teardown.

The finalizer owns only host-resource observations.  It does not import or
reproduce verifier predicates and it never changes PostgreSQL runtime facts.
"""

# Evidence records are intentionally explicit and readable.
# ruff: noqa: E501

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

RUNTIME_PRODUCER_GATES = frozenset({
    "migration_ladders", "metadata_parity", "physical_constraints",
    "production_command_matrix", "replay", "fingerprint_mismatch",
    "manual_access_same_key_concurrency", "tariff_assignment_same_key_concurrency",
    "concurrent_same_key_different_fingerprint_conflict",
    "payment_same_provider_same_account_duplicate", "payment_same_provider_cross_account_conflict",
    "manual_grant_rollback_retry", "second_rollback_retry", "manual_entitlement_semantics",
    "usage_policy_semantics", "payment_evidence_non_authority", "synthetic_database_cleanup",
    "credential_exposure",
})
HOST_FINALIZER_GATES = frozenset({"docker_task_resource_cleanup", "post_cleanup_foreign_resource_equality"})


def _raw(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def finalize(runtime_path: Path, before_path: Path, after_path: Path, absence_path: Path, output_path: Path) -> None:
    evidence = _raw(runtime_path)
    before = _raw(before_path)
    after = _raw(after_path)
    absence = _raw(absence_path)
    if not isinstance(before, dict) or not isinstance(after, dict) or not isinstance(absence, dict):
        raise SystemExit("RF12 raw Docker observations are invalid")
    if evidence.get("evidence_phase") != "RUNTIME_COMPLETE_PENDING_HOST_FINALIZATION":
        raise SystemExit("RF12 finalizer requires runtime-complete pending evidence")
    gates = evidence.get("gates")
    if not isinstance(gates, dict) or set(gates) != RUNTIME_PRODUCER_GATES | HOST_FINALIZER_GATES:
        raise SystemExit("RF12 finalizer received an invalid closed-world gate set")
    if any(gates[name] is not True for name in RUNTIME_PRODUCER_GATES):
        raise SystemExit("RF12 finalizer refuses failed producer evidence")
    task_absent = (
        absence.get("task_resources_absent") is True
        and absence.get("container_absent") is True
        and absence.get("network_absent") is True
        and absence.get("volume_absent") is True
        and absence.get("image_tag_absent") is True
        and absence.get("image_id_not_retained") is True
    )
    equality = before == after
    evidence["foreign_before_raw"] = before
    evidence["foreign_after_raw"] = after
    evidence["docker_task_resource_cleanup"] = {
        "observation_source": "raw Docker inspect after teardown",
        "scenario_id": "rf12-docker-task-resource-removal-post-cleanup",
        "production_method": "Docker CLI resource removal",
        "sessions": 0,
        "before": absence.get("task_resources_before", {}),
        "after": absence,
        "outcomes": [{"task_resources_absent": task_absent}],
        "counts": {"remaining_task_resources": int(absence.get("remaining_task_resources", 1))},
        "bounded": True,
        "task_resources_absent": task_absent,
    }
    evidence["post_cleanup_foreign_resource_equality"] = {
        "observation_source": "raw normalized Docker snapshots",
        "scenario_id": "rf12-foreign-resource-equality-after-teardown",
        "production_method": "Docker CLI inventory",
        "sessions": 0,
        "before": before,
        "after": after,
        "outcomes": [{"equal": equality}],
        "counts": {"before_resources": sum(len(v) for v in before.values() if isinstance(v, list)), "after_resources": sum(len(v) for v in after.values() if isinstance(v, list))},
        "bounded": True,
        "raw_after_observed": True,
        "equal": equality,
    }
    evidence["gates"]["docker_task_resource_cleanup"] = task_absent
    evidence["gates"]["post_cleanup_foreign_resource_equality"] = task_absent and equality
    evidence["evidence_phase"] = "FINALIZED"
    output_path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if not (task_absent and equality):
        raise SystemExit("RF12 Docker post-cleanup observations failed")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--before", type=Path, required=True)
    parser.add_argument("--after", type=Path, required=True)
    parser.add_argument("--absence", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    finalize(args.runtime, args.before, args.after, args.absence, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
