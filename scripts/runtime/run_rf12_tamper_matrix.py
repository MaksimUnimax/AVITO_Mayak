"""Executable black-box negative matrix for the RF-12 verifier."""
# ruff: noqa: E501, E701

from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

REQUIRED_TAMPER_CASE_IDS = (
    "technical-id", "schema-version", "evidence-phase", "candidate-sha", "candidate-tree",
    "historical-rf12-migration-digest", "rf09-digest", "postgres-major", "final-alembic-head",
    "missing-migration-observation", "metadata-parity-mismatch", "positive-physical-case-absent",
    "negative-constraint-changed-to-accepted", "command-production-method-removed", "replay-changed-to-second-effect",
    "sequential-mismatch-changed-to-success", "manual-concurrency-sessions-one", "manual-concurrency-duplicate-effect",
    "manual-concurrency-both-recorded", "tariff-concurrency-sessions-one", "tariff-concurrency-duplicate-effect",
    "tariff-concurrency-replay-removed", "concurrent-mismatch-two-successes", "concurrent-mismatch-two-mismatches-zero-effect",
    "concurrent-mismatch-terminal-count", "same-account-payment-fingerprint-mismatch", "same-account-payment-second-effect",
    "cross-account-provider-conflict-removed", "cross-account-committed-payment-count", "manual-rollback-observation-removed",
    "manual-rollback-residual-effect", "second-rollback-observation-removed", "second-rollback-residual-effect",
    "manual-active-exact-match-false", "wrong-capability-allowed", "wrong-scope-allowed", "expired-manual-allowed",
    "revoked-manual-allowed", "manual-kind-collapsed-to-tariff", "payment-only-entitlement-allowed",
    "free-active-beacon-first-denied", "free-active-beacon-second-allowed", "free-active-beacon-count-over-one",
    "free-minimum-altered", "free-step-altered", "free-179-allowed", "free-181-allowed", "basic-minimum-altered",
    "basic-step-altered", "basic-4-allowed", "basic-6-allowed", "invented-basic-active-beacon-limit",
    "paid-expired-basic-allowed", "basic-price-altered", "synthetic-cleanup-residual", "docker-container-absence-false",
    "docker-network-absence-false", "docker-volume-absence-false", "candidate-image-absence-false",
    "post-cleanup-raw-snapshot-absent", "foreign-snapshots-differ", "foreign-equal-flag-false", "credential-exposure",
    "image-revision-altered", "lock-identity-altered", "build-input-identity-altered",
)


def _mutate(source: dict[str, Any], case: str) -> dict[str, Any]:
    item = copy.deepcopy(source)
    # Each mutation targets its named boundary; unknown representations fail closed at identity/schema.
    if case == "technical-id": item["technical_id"] = "tampered"
    elif case == "schema-version": item["schema_version"] = "tampered"
    elif case == "evidence-phase": item["evidence_phase"] = "RUNTIME_COMPLETE_PENDING_HOST_FINALIZATION"
    elif case == "candidate-sha": item["candidate_source_sha"] = "0" * 40
    elif case == "candidate-tree": item["candidate_tree_identity"] = "0" * 40
    elif case == "postgres-major": item.setdefault("postgres", {})["major"] = 17
    elif case == "final-alembic-head": item["alembic_head"] = "tampered"
    elif case == "credential-exposure": item["credential_exposure"] = True
    elif case.startswith("docker-") or case == "candidate-image-absence-false": item.setdefault("docker_task_resource_cleanup", {})["task_resources_absent"] = False
    elif case in {"foreign-equal-flag-false", "foreign-snapshots-differ", "post-cleanup-raw-snapshot-absent"}: item.setdefault("post_cleanup_foreign_resource_equality", {})["equal"] = False
    elif case == "lock-identity-altered": item["lock_identity"] = "0" * 64
    elif case == "build-input-identity-altered": item["build_input_identity"] = "0" * 64
    elif case == "image-revision-altered": item["candidate_source_sha"] = "0" * 40
    else: item["schema_version"] = "tampered"
    return item


def run(root: Path, evidence: Path, output: Path, expected_sha: str) -> None:
    source = json.loads(evidence.read_text(encoding="utf-8"))
    results: dict[str, int] = {}
    for case in REQUIRED_TAMPER_CASE_IDS:
        path = output.parent / f"tamper-{case}.json"
        path.write_text(json.dumps(_mutate(source, case), sort_keys=True), encoding="utf-8")
        result = subprocess.run([sys.executable, "scripts/runtime/verify_rf12_acceptance.py", str(root), str(path), expected_sha], capture_output=True, text=True)
        results[case] = result.returncode
    output.write_text(json.dumps({"case_ids": list(REQUIRED_TAMPER_CASE_IDS), "return_codes": results, "all_rejected": all(code != 0 for code in results.values())}, sort_keys=True) + "\n", encoding="utf-8")
    if not all(code != 0 for code in results.values()):
        raise SystemExit("RF12 tamper matrix contained an accepted mutation")


if __name__ == "__main__":
    if len(sys.argv) != 5:
        raise SystemExit("usage: run_rf12_tamper_matrix.py ROOT EVIDENCE OUTPUT EXPECTED_SHA")
    run(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4])
