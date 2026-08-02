"""Independent fail-closed verifier for RF-13 PostgreSQL evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
from pathlib import Path

MARKER = "RF13_ACCEPTANCE_VERIFIED"
TECHNICAL_ID = "RF-13-BEACON-MANAGEMENT-RUNTIME-POSTGRES-20260802-01"
EXPECTED_BASE = "39c750198cddc385ae3909b8fd63ff0e8e1a4a95"
EXPECTED_HEAD = "RF13_BEACON_RUNTIME"
EXPECTED_GATES = frozenset({
    "migration_empty_to_head", "migration_rf12_to_head", "version_table",
    "metadata_parity", "physical_constraints", "preparation", "source_preservation",
    "snapshot_positive", "snapshot_negative_matrix", "revision_immutability",
    "override_provenance", "stale_patch_race", "idempotency_replay",
    "idempotency_mismatch", "idempotency_concurrency", "rollback_retry",
    "ownership_isolation", "lifecycle_transition_matrix", "entitlement_activation",
    "active_slot_race", "paid_expiry_system_freeze", "archive_restore_delete_history",
    "revision_reads", "synthetic_cleanup", "credential_exposure",
})
REQUIRED_TABLES = frozenset({
    "beacon_beacons", "beacon_configuration_revisions",
    "beacon_filter_overrides", "beacon_lifecycle_events",
})


def _git(root: Path, *args: str) -> str:
    return subprocess.check_output(("git", *args), cwd=root, text=True).strip()


def verify(root: Path, evidence: Path, candidate_sha: str) -> None:
    item = json.loads(evidence.read_text(encoding="utf-8"))
    actual_sha = _git(root, "rev-parse", "HEAD")
    actual_tree = _git(root, "rev-parse", "HEAD^{tree}")
    parent = _git(root, "rev-parse", "HEAD^")
    if item.get("technical_id") != TECHNICAL_ID:
        raise SystemExit("technical id mismatch")
    if candidate_sha != actual_sha or item.get("candidate_sha") != actual_sha:
        raise SystemExit("candidate SHA mismatch")
    if item.get("candidate_tree") != actual_tree:
        raise SystemExit("candidate tree mismatch")
    if parent != EXPECTED_BASE or item.get("parent") != EXPECTED_BASE:
        raise SystemExit("candidate is not one direct child of Expected Base")
    if item.get("alembic_head") != EXPECTED_HEAD:
        raise SystemExit("Alembic head mismatch")
    if item.get("python") != "3.14.6" or platform.python_version() != item.get("python"):
        raise SystemExit("Python toolchain mismatch")
    uv_output = subprocess.check_output(("uv", "--version"), text=True).strip().split()
    uv = next((token for token in uv_output if token[:1].isdigit()), "")
    if item.get("uv") != "0.11.31" or uv != item.get("uv"):
        raise SystemExit(
            f"uv toolchain mismatch: observed={uv!r} evidence={item.get('uv')!r}"
        )
    if item.get("postgres_major") != 18:
        raise SystemExit("PostgreSQL major evidence mismatch")
    if item.get("lock_identity") != hashlib.sha256((root / "uv.lock").read_bytes()).hexdigest():
        raise SystemExit("uv.lock identity mismatch")
    schema = item.get("schema")
    if not isinstance(schema, dict) or set(schema.get("tables", [])) != REQUIRED_TABLES:
        raise SystemExit("physical table evidence incomplete")
    runtime = item.get("runtime")
    if not isinstance(runtime, dict):
        raise SystemExit("runtime witness missing")
    if runtime.get("cleanup_verified") is not True:
        raise SystemExit("cleanup was not observed")
    if item.get("raw_provider_payload_persisted") is not False:
        raise SystemExit("raw provider payload persistence evidence failed")
    if item.get("production_data_marker") is not False:
        raise SystemExit("production data marker detected")
    gates = item.get("gates")
    if not isinstance(gates, dict) or set(gates) != EXPECTED_GATES:
        raise SystemExit("RF13 gate registry is not exact")
    if any(value is not True for value in gates.values()):
        raise SystemExit("RF13 gate failed")
    negative = runtime.get("negative_zero_effect")
    if not isinstance(negative, list) or len(negative) != 7:
        raise SystemExit("negative snapshot cardinality failed")
    if not all(row.get("revision_count") == 2 for row in negative):
        raise SystemExit("negative snapshot changed persistence")
    if runtime.get("old_revision") != json.dumps(
        runtime.get("old_revision_after"), sort_keys=True
    ):
        raise SystemExit("revision immutability witness failed")
    if runtime.get("override_count") != 1:
        raise SystemExit("override cardinality failed")
    if runtime.get("terminal_state") != "PERMANENTLY_DELETED":
        raise SystemExit("terminal lifecycle witness failed")
    print(MARKER)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("evidence", type=Path)
    parser.add_argument("candidate_sha")
    args = parser.parse_args()
    verify(args.root, args.evidence, args.candidate_sha)
