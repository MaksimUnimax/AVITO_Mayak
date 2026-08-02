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
    # Every case mutates the named evidence boundary.  This is deliberately
    # explicit: a case that accidentally falls through to a generic schema
    # mutation would create false coverage.
    def obj(name: str) -> dict[str, Any]:
        value = item.setdefault(name, {})
        return value if isinstance(value, dict) else {}

    def outcome(name: str, index: int = 0) -> dict[str, Any]:
        rows = obj(name).setdefault("outcomes", [])
        while len(rows) <= index:
            rows.append({})
        return rows[index]

    if case == "technical-id": item["technical_id"] = "tampered"
    elif case == "schema-version": item["schema_version"] = "tampered"
    elif case == "evidence-phase": item["evidence_phase"] = "RUNTIME_COMPLETE_PENDING_HOST_FINALIZATION"
    elif case in {"candidate-sha", "image-revision-altered"}: item["candidate_source_sha"] = "0" * 40
    elif case == "candidate-tree": item["candidate_tree_identity"] = "0" * 40
    elif case == "historical-rf12-migration-digest": item["historical_rf12_manual_grant_sha256"] = "0" * 64
    elif case == "rf09-digest":
        key = next(iter(item.get("rf09_digests", {"alembic/versions/20260701_x.py": ""})))
        obj("rf09_digests")[key] = "0" * 64
    elif case == "postgres-major": obj("postgres")["major"] = 17
    elif case == "final-alembic-head": item["alembic_head"] = "tampered"
    elif case == "missing-migration-observation": obj("migration_ladders").pop("empty_to_head", None)
    elif case == "metadata-parity-mismatch": obj("metadata_parity")["mismatches"] = ["tampered"]
    elif case == "positive-physical-case-absent": obj("physical_constraints")["positive_cases"] = []
    elif case == "negative-constraint-changed-to-accepted": obj("physical_constraints")["negative_cases"][0]["rejected"] = False
    elif case == "command-production-method-removed": obj("production_command_matrix")["rows"][0]["production_method"] = "test.fake"
    elif case == "replay-changed-to-second-effect": obj("replay")["counts"]["business_effect_second"] = 1
    elif case == "sequential-mismatch-changed-to-success": outcome("fingerprint_mismatch")["state"] = "RECORDED"
    elif case.startswith("manual-concurrency-"):
        obj("manual_access_same_key_concurrency")["sessions"] = 1
        if case.endswith("duplicate-effect"): obj("manual_access_same_key_concurrency")["counts"]["business_effect"] = 2
        if case.endswith("both-recorded"):
            outcome("manual_access_same_key_concurrency")["state"] = "RECORDED"
            outcome("manual_access_same_key_concurrency", 1)["state"] = "RECORDED"
    elif case.startswith("tariff-concurrency-"):
        if case.endswith("sessions-one"): obj("tariff_assignment_same_key_concurrency")["sessions"] = 1
        elif case.endswith("duplicate-effect"): obj("tariff_assignment_same_key_concurrency")["counts"]["business_effect"] = 2
        else:
            obj("tariff_assignment_same_key_concurrency")["outcomes"] = [{}]
    elif case == "concurrent-mismatch-two-successes":
        outcome("concurrent_same_key_different_fingerprint_conflict")["state"] = "RECORDED"
        outcome("concurrent_same_key_different_fingerprint_conflict", 1)["state"] = "RECORDED"
    elif case == "concurrent-mismatch-two-mismatches-zero-effect": obj("concurrent_same_key_different_fingerprint_conflict")["counts"]["business_effect"] = 0
    elif case == "concurrent-mismatch-terminal-count": obj("concurrent_same_key_different_fingerprint_conflict")["counts"]["terminal_records"] = 2
    elif case.startswith("same-account-payment-"):
        obj("payment_same_provider_same_account_duplicate")["counts"]["business_effect"] = 2
    elif case == "cross-account-provider-conflict-removed": outcome("payment_same_provider_cross_account_conflict", 1)["reason_code"] = "OTHER"
    elif case == "cross-account-committed-payment-count": obj("payment_same_provider_cross_account_conflict")["counts"]["business_effect"] = 2
    elif case in {"manual-rollback-observation-removed", "second-rollback-observation-removed"}: obj("manual_grant_rollback_retry" if case.startswith("manual") else "second_rollback_retry")["retry_committed"] = False
    elif case in {"manual-rollback-residual-effect", "second-rollback-residual-effect"}: obj("manual_grant_rollback_retry" if case.startswith("manual") else "second_rollback_retry")["counts"]["post_rollback_business"] = 1
    elif case == "manual-active-exact-match-false": obj("manual_entitlement_semantics")["cases"]["active_exact_match"]["allowed"] = False
    elif case == "wrong-capability-allowed": obj("manual_entitlement_semantics")["cases"]["wrong_capability"]["allowed"] = True
    elif case == "wrong-scope-allowed": obj("manual_entitlement_semantics")["cases"]["wrong_scope"]["allowed"] = True
    elif case == "expired-manual-allowed": obj("manual_entitlement_semantics")["cases"]["expired"]["allowed"] = True
    elif case == "revoked-manual-allowed": obj("manual_entitlement_semantics")["cases"]["revoked"]["allowed"] = True
    elif case == "manual-kind-collapsed-to-tariff": obj("manual_entitlement_semantics")["manual_kind_distinct"] = False
    elif case == "payment-only-entitlement-allowed": obj("payment_evidence_non_authority")["entitlement_effective"] = True
    elif case == "free-active-beacon-first-denied": obj("usage_policy_semantics")["free"]["active_beacon"]["first"]["state"] = "DENIED"
    elif case == "free-active-beacon-second-allowed": obj("usage_policy_semantics")["free"]["active_beacon"]["second"]["state"] = "ALLOWED"
    elif case == "free-active-beacon-count-over-one": obj("usage_policy_semantics")["free"]["active_beacon"]["observed_count"] = 2
    elif case in {"free-minimum-altered", "free-step-altered", "free-179-allowed", "free-181-allowed"}: obj("usage_policy_semantics")["free"]["minimum" if case.endswith("minimum-altered") else "step" if case.endswith("step-altered") else "interval_179_allowed" if case.endswith("179-allowed") else "interval_181_allowed"] = 1
    elif case in {"basic-minimum-altered", "basic-step-altered", "basic-4-allowed", "basic-6-allowed"}: obj("usage_policy_semantics")["basic"]["minimum" if case.endswith("minimum-altered") else "step" if case.endswith("step-altered") else "interval_4_allowed" if case.endswith("4-allowed") else "interval_6_allowed"] = 1
    elif case == "invented-basic-active-beacon-limit": obj("usage_policy_semantics")["basic"]["active_beacon_limit"] = 1
    elif case == "paid-expired-basic-allowed": obj("usage_policy_semantics")["paid_expiry"]["effective_allowed"] = True
    elif case == "basic-price-altered": obj("usage_policy_semantics")["tariff_definitions"]["BASIC"]["price_minor"] = 1
    elif case == "synthetic-cleanup-residual": obj("synthetic_database_cleanup")["counts"]["remaining_synthetic_accounts"] = 1
    elif case.startswith("docker-") or case == "candidate-image-absence-false": obj("docker_task_resource_cleanup")["task_resources_absent"] = False
    elif case == "post-cleanup-raw-snapshot-absent": obj("post_cleanup_foreign_resource_equality")["raw_after_observed"] = False
    elif case == "foreign-snapshots-differ": obj("post_cleanup_foreign_resource_equality")["after"] = {"tampered": True}
    elif case == "foreign-equal-flag-false": obj("post_cleanup_foreign_resource_equality")["equal"] = False
    elif case == "credential-exposure": item["credential_exposure"] = True
    elif case == "lock-identity-altered": item["lock_identity"] = "0" * 64
    elif case == "build-input-identity-altered": item["build_input_identity"] = "0" * 64
    else: raise AssertionError(f"unmapped RF12 tamper case: {case}")
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
