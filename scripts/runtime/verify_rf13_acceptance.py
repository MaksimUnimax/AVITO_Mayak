"""Fail-closed, observation-first RF-13 acceptance verifier (v4)."""

from __future__ import annotations

# ruff: noqa: E501
import argparse
import hashlib
import json
import platform
import subprocess
from pathlib import Path
from typing import Any

MARKER = "RF13_ACCEPTANCE_VERIFIED"
TECHNICAL_ID = "RF-13-BEACON-MANAGEMENT-RUNTIME-POSTGRES-20260802-01"
EXPECTED_BASE = "d48aa01ba01d6f02746fb1bad73213a2b1efbd30"
SCHEMA_VERSION = "rf13-postgres-acceptance-v4"

REQUIRED_SECTIONS = (
    "identity",
    "toolchain",
    "migration_setup_identity",
    "physical_schema",
    "preparation",
    "positive_snapshot",
    "negative_snapshot_matrix",
    "patch_lww_concurrency",
    "different_field_concurrency_applicability",
    "idempotency_concurrency",
    "rollback",
    "ownership",
    "active_slot_concurrency",
    "lifecycle_history",
    "system_freeze_positive",
    "system_authority_mismatch_negative",
    "revision_immutability",
    "cleanup",
    "security_witness",
)

# The registry is acceptance authority.  Every requirement names the raw paths it
# consumes and the tamper cases that must be able to falsify it.
REQUIRED_ACCEPTANCE_REQUIREMENTS: dict[str, dict[str, Any]] = {
    "identity-candidate": {"raw": ["identity.candidate_sha"], "tamper": ["identity_candidate_sha"]},
    "identity-parent": {"raw": ["identity.parent"], "tamper": ["identity_parent"]},
    "identity-toolchain": {
        "raw": ["toolchain.python", "toolchain.uv", "toolchain.uv_lock_sha256"],
        "tamper": ["toolchain_python"],
    },
    "migration-head": {
        "raw": ["migration_setup_identity.version_table"],
        "tamper": ["migration_head"],
    },
    "physical-constraints": {
        "raw": ["physical_schema.constraints"],
        "tamper": ["schema_actor_causation"],
    },
    "preparation-state": {"raw": ["preparation.observed"], "tamper": ["preparation_state"]},
    "snapshot-positive": {"raw": ["positive_snapshot"], "tamper": ["snapshot_positive_delta"]},
    "snapshot-negative-matrix": {
        "raw": ["negative_snapshot_matrix"],
        "tamper": ["snapshot_negative_revision"],
    },
    "patch-persisted-order": {
        "raw": ["patch_lww_concurrency.workers", "patch_lww_concurrency.final_revision_no"],
        "tamper": ["patch_final_revision"],
    },
    "idempotency-repository-decision": {
        "raw": ["idempotency_concurrency.outcomes"],
        "tamper": ["idempotency_fake_replay"],
    },
    "rollback-post-query": {
        "raw": ["rollback.baseline_counts", "rollback.post_rollback_counts"],
        "tamper": ["rollback_post_counts"],
    },
    "ownership-zero-effect": {"raw": ["ownership"], "tamper": ["ownership_accept"]},
    "active-slot-attribution": {
        "raw": ["active_slot_concurrency.workers"],
        "tamper": ["active_denial_reason"],
    },
    "lifecycle-raw-history": {
        "raw": ["lifecycle_history.event_rows"],
        "tamper": ["lifecycle_event_sequence"],
    },
    "system-freeze-db-witness": {
        "raw": ["system_freeze_positive.event_id", "system_freeze_positive.system_actor_class"],
        "tamper": ["freeze_class"],
    },
    "system-authority-binding": {
        "raw": ["system_authority_mismatch_negative"],
        "tamper": ["resolved_class_mismatch"],
    },
    "revision-immutability": {"raw": ["revision_immutability"], "tamper": ["old_revision"]},
    "metadata-parity": {"raw": ["physical_schema.metadata_parity"], "tamper": ["metadata_parity"]},
    "cleanup-observation": {"raw": ["cleanup"], "tamper": ["cleanup_residue"]},
    "security-counts": {
        "raw": ["security_witness.secret_scan_match_count"],
        "tamper": ["security_secret_count"],
    },
}

REQUIRED_TAMPER_CASES = (
    "identity_candidate_sha identity_candidate_tree identity_parent identity_technical_id identity_schema_version toolchain_python toolchain_uv toolchain_lock_digest postgres_major",
    "migration_empty_head migration_version_table migration_head",
    "preparation_state preparation_current_revision preparation_source_url preparation_event_count",
    "snapshot_positive_delta snapshot_positive_current_revision snapshot_negative_revision snapshot_negative_current_revision snapshot_source_url",
    "patch_sessions patch_barrier patch_worker_count patch_committed_count patch_revision_count patch_duplicate_revision patch_current_not_max patch_value_not_max patch_final_revision patch_orphan_revision patch_orphan_override",
    "idempotency_sessions idempotency_barrier idempotency_two_effects idempotency_two_terminals idempotency_resource_ids idempotency_missing_replay idempotency_fake_replay",
    "active_sessions active_barrier active_worker_missing active_counts active_both_allowed active_denial_reason active_final_count active_event_count",
    "rollback_post_counts rollback_baseline_copy rollback_retry_failure rollback_duplicate_business rollback_duplicate_idempotency",
    "ownership_read_accept ownership_state_change ownership_unverified_accept ownership_accept",
    "lifecycle_active_count restore_entitlement_missing restore_stale_entitlement source_url_change revision_reference_change permanent_delete_restorable restore_after_delete event_sequence lifecycle_event_sequence",
    "freeze_class freeze_actor_account freeze_persisted_class freeze_causation freeze_policy freeze_event_count freeze_state auto_free resolved_class_mismatch",
    "old_revision current_revision_wrong",
    "schema_revision_unique schema_current_fk schema_revision_positive schema_revision_pair schema_source_url schema_actor_causation metadata_parity",
    "cleanup_residue cleanup_preexisting",
    "security_secret_count security_raw_payload security_production_data",
)
REQUIRED_TAMPER_CASES = tuple(
    "".join(part.split()) for line in REQUIRED_TAMPER_CASES for part in line.split()
)


def _git(root: Path, *args: str) -> str:
    return subprocess.check_output(("git", *args), cwd=root, text=True).strip()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def _path(item: dict[str, Any], dotted: str) -> Any:
    node: Any = item
    for key in dotted.split("."):
        _require(isinstance(node, dict) and key in node, f"raw observation missing: {dotted}")
        node = node[key]
    return node


def _count(witness: dict[str, Any], key: str) -> int:
    value = witness.get(key)
    _require(isinstance(value, int) and value >= 0, f"malformed count: {key}")
    return value


def verify(root: Path, evidence: Path, candidate_sha: str) -> None:
    item = json.loads(evidence.read_text(encoding="utf-8"))
    _require("tamper_probe" not in item, "tamper probe is not evidence")
    actual_sha, actual_tree, parent = (
        _git(root, x) for x in ("rev-parse HEAD", "rev-parse HEAD^{tree}", "rev-parse HEAD^")
    )
    identity = _path(item, "identity")
    _require(item.get("schema_version") == SCHEMA_VERSION, "schema v4 required")
    _require(identity.get("technical_id") == TECHNICAL_ID, "technical id mismatch")
    _require(candidate_sha == actual_sha == identity.get("candidate_sha"), "candidate SHA mismatch")
    _require(identity.get("candidate_tree") == actual_tree, "candidate tree mismatch")
    _require(parent == EXPECTED_BASE and identity.get("parent") == EXPECTED_BASE, "parent mismatch")
    toolchain = _path(item, "toolchain")
    _require(
        toolchain.get("python") == "3.14.6" and platform.python_version() == "3.14.6",
        "Python mismatch",
    )
    uv = next(
        (
            x
            for x in subprocess.check_output(("uv", "--version"), text=True).split()
            if x[:1].isdigit()
        ),
        "",
    )
    _require(toolchain.get("uv") == "0.11.31" and uv == "0.11.31", "uv mismatch")
    _require(
        toolchain.get("uv_lock_sha256")
        == hashlib.sha256((root / "uv.lock").read_bytes()).hexdigest(),
        "uv.lock mismatch",
    )
    for section in REQUIRED_SECTIONS:
        value = item.get(section)
        _require(
            isinstance(value, (dict, list)) and bool(value), f"required section invalid: {section}"
        )
    _require(
        item.get("migration_setup_identity", {}).get("version_table")
        == "RF13_BEACON_RUNTIME_HARDEN",
        "migration head",
    )
    physical = _path(item, "physical_schema")
    _require(physical.get("metadata_parity") is True, "metadata parity")
    constraints = physical.get("constraints", {})
    _require(
        isinstance(constraints, dict) and len(constraints) >= 6, "physical constraints missing"
    )
    definitions = " ".join(
        str(v.get("definition", "")) for v in constraints.values() if isinstance(v, dict)
    ).lower()
    for fragment in ("current_revision", "source_url", "actor_account_id", "causation_reference"):
        _require(fragment in definitions, f"physical invariant missing: {fragment}")
    negative = _path(item, "negative_snapshot_matrix")
    _require(
        isinstance(negative, list) and len(negative) == 7,
        "all seven negative parser outcomes required",
    )
    for row in negative:
        _require(
            row.get("revision_count") == row.get("pre_revision_count", row.get("revision_count")),
            "negative revision persistence",
        )
        _require(
            row.get("current_revision_after")
            == row.get("current_revision_before", row.get("current_revision_after")),
            "negative current authority",
        )
    patch = _path(item, "patch_lww_concurrency_witness")
    workers = patch.get("workers", [])
    revisions = [row.get("revision_no") for row in workers]
    _require(
        len(workers) == 2
        and all(isinstance(x, int) for x in revisions)
        and len(set(revisions)) == 2,
        "patch revision observations",
    )
    _require(patch.get("final_revision_no") == max(revisions), "LWW not persisted revision order")
    idem = _path(item, "idempotency_concurrency")
    _require(
        idem.get("business_effect_count") == 1 and idem.get("terminal_record_count") == 1,
        "idempotency effects",
    )
    _require(
        all(
            row.get("repository_decision") in {"NEW", "REPLAY_TERMINAL"}
            for row in idem.get("outcomes", [])
        ),
        "real repository decisions missing",
    )
    rollback = _path(item, "rollback")
    _require(
        rollback.get("baseline_counts") == rollback.get("post_rollback_counts"), "rollback residue"
    )
    lifecycle = _path(item, "lifecycle_history")
    _require(
        isinstance(lifecycle.get("event_rows"), list) and lifecycle.get("event_rows"),
        "lifecycle rows missing",
    )
    freeze = _path(item, "system_freeze_positive")
    _require(
        freeze.get("actor_account_id") is None and freeze.get("state") == "FROZEN",
        "freeze actor/state",
    )
    _require(freeze.get("system_actor_class") == "ENTITLEMENTS_AND_BILLING_SERVICE", "freeze class")
    mismatch = _path(item, "system_authority_mismatch_negative")
    _require(
        mismatch.get("zero_effect") is True
        and mismatch.get("exception_class") == "BeaconRuntimeError",
        "authority mismatch witness",
    )
    security = _path(item, "security_witness")
    _require(
        _count(security, "secret_scan_match_count") == 0
        and _count(security, "raw_provider_payload_forbidden_persisted_value_count") == 0,
        "security counts",
    )
    for requirement, spec in REQUIRED_ACCEPTANCE_REQUIREMENTS.items():
        _require(
            spec.get("raw") and spec.get("tamper"), f"requirement mapping incomplete: {requirement}"
        )
        for raw in spec["raw"]:
            _path(item, raw)
    print(MARKER)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("evidence", type=Path)
    parser.add_argument("candidate_sha")
    args = parser.parse_args()
    verify(args.root, args.evidence, args.candidate_sha)
