"""Independent, observation-first RF-13 PostgreSQL verifier."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
from pathlib import Path
from typing import Any

MARKER = "RF13_ACCEPTANCE_VERIFIED"
TECHNICAL_ID = "RF-13-BEACON-MANAGEMENT-RUNTIME-POSTGRES-20260802-01"
EXPECTED_BASE = "4c6cb905682c708aacf4f8199cabd064f6b8f63c"
EXPECTED_HEAD = "RF13_BEACON_RUNTIME_HARDEN"
SCHEMA_VERSION = "rf13-postgres-acceptance-v3"
REQUIRED_TABLES = {
    "beacon_beacons",
    "beacon_configuration_revisions",
    "beacon_filter_overrides",
    "beacon_lifecycle_events",
}
REQUIRED_SECTIONS = {
    "identity",
    "toolchain",
    "migration",
    "physical_schema",
    "preparation_witness",
    "snapshot_witness",
    "patch_lww_concurrency_witness",
    "different_field_concurrency_applicability",
    "idempotency_concurrency_witness",
    "rollback_witness",
    "ownership_witness",
    "active_slot_concurrency_witness",
    "lifecycle_witness",
    "system_freeze_witness",
    "revision_read_witness",
    "cleanup_witness",
    "security_witness",
}


def _git(root: Path, *args: str) -> str:
    return subprocess.check_output(("git", *args), cwd=root, text=True).strip()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def _count(witness: dict[str, Any], key: str) -> int:
    value = witness.get(key)
    _require(isinstance(value, int) and value >= 0, f"malformed count: {key}")
    return value


def verify(root: Path, evidence: Path, candidate_sha: str) -> None:
    item = json.loads(evidence.read_text(encoding="utf-8"))
    actual_sha = _git(root, "rev-parse", "HEAD")
    actual_tree = _git(root, "rev-parse", "HEAD^{tree}")
    parent = _git(root, "rev-parse", "HEAD^")
    identity = item.get("identity")
    _require(isinstance(identity, dict), "identity witness missing")
    _require(item.get("schema_version") == SCHEMA_VERSION, "schema v3 required")
    _require(identity.get("technical_id") == TECHNICAL_ID, "technical id mismatch")
    _require(candidate_sha == actual_sha == identity.get("candidate_sha"), "candidate SHA mismatch")
    _require(identity.get("candidate_tree") == actual_tree, "candidate tree mismatch")
    _require(parent == EXPECTED_BASE and identity.get("parent") == EXPECTED_BASE, "parent mismatch")
    _require(identity.get("alembic_head") == EXPECTED_HEAD, "Alembic head mismatch")
    toolchain = item.get("toolchain")
    _require(isinstance(toolchain, dict), "toolchain witness missing")
    _require(
        toolchain.get("python") == "3.14.6" and platform.python_version() == "3.14.6",
        "Python mismatch",
    )
    uv = next(
        (token for token in subprocess.check_output(("uv", "--version"), text=True).split()
         if token[:1].isdigit()),
        "",
    )
    _require(toolchain.get("uv") == "0.11.31" and uv == "0.11.31", "uv mismatch")
    _require(toolchain.get("postgres_major") == 18, "PostgreSQL 18 required")
    _require(
        toolchain.get("uv_lock_sha256")
        == hashlib.sha256((root / "uv.lock").read_bytes()).hexdigest(),
        "uv.lock mismatch",
    )
    _require(set(item) >= REQUIRED_SECTIONS, "required raw witness section missing")

    migration = item["migration"]
    _require(
        migration.get("empty_to_head", {}).get("after") == EXPECTED_HEAD,
        "empty migration ladder failed",
    )
    _require(
        migration.get("rf13_to_head", {}).get("before") == "RF13_BEACON_RUNTIME",
        "RF13 migration boundary missing",
    )
    _require(
        migration.get("rf13_to_head", {}).get("after") == EXPECTED_HEAD,
        "hardening migration failed",
    )
    _require(migration.get("version_table") == EXPECTED_HEAD, "version table mismatch")

    physical = item["physical_schema"]
    _require(set(physical.get("tables", [])) == REQUIRED_TABLES, "RF13 tables mismatch")
    constraints = physical.get("constraints")
    _require(isinstance(constraints, dict), "named physical constraints missing")
    required_constraints = {
        "uq_beacon_configuration_revisions_revision_id",
        "fk_beacon_beacons_current_revision_id",
        "ck_beacon_beacons_revision_positive",
        "current_revision_pair",
        "source_url_nonempty",
        "ck_beacon_lifecycle_events_actor_causation_pair",
    }
    missing_constraints = sorted(required_constraints - set(constraints))
    _require(
        not missing_constraints,
        f"required named constraint missing: {missing_constraints}",
    )
    _require(
        all(constraints[name] for name in required_constraints),
        "constraint definition/column signature missing",
    )

    patch = item["patch_lww_concurrency_witness"]
    _require(
        patch.get("sessions") == 2 and patch.get("barrier") is True,
        "patch concurrency not independent",
    )
    _require(len(patch.get("workers", [])) == 2, "patch worker cardinality")
    _require(
        patch.get("committed_count") == 2 and patch.get("revision_count") == 2,
        "patch commit/revision count",
    )
    _require(
        patch.get("first_committed_value") != patch.get("final_value"),
        "patch values did not overlap",
    )
    _require(
        patch.get("final_value") == patch.get("last_committed_value"),
        "patch final authority is not last commit",
    )
    _require(
        patch.get("orphan_revision_count") == 0 and patch.get("orphan_override_count") == 0,
        "patch residue",
    )
    _require(
        all(row.get("outcome") == "SUCCEEDED" for row in patch["workers"]), "patch worker failed"
    )

    applicability = item["different_field_concurrency_applicability"]
    _require(
        applicability.get("applicable") is False,
        "different-field proof must be N/A unless supported",
    )
    _require(
        applicability.get("reason")
        == "only one supported configuration patch field in accepted RF13 contract",
        "invalid N/A reason",
    )

    idem = item["idempotency_concurrency_witness"]
    _require(
        idem.get("sessions") == 2 and idem.get("barrier") is True,
        "idempotency concurrency not independent",
    )
    _require(
        idem.get("attempt_count") == 2 and idem.get("business_effect_count") == 1,
        "idempotency effects",
    )
    _require(
        idem.get("terminal_record_count") == 1 and idem.get("same_resource") is True,
        "idempotency terminal result",
    )
    _require(
        sorted(row.get("outcome") for row in idem["outcomes"]) == ["REPLAY", "SUCCEEDED"],
        "idempotency outcomes",
    )

    active = item["active_slot_concurrency_witness"]
    _require(
        active.get("sessions") == 2 and active.get("barrier") is True,
        "active-slot concurrency not independent",
    )
    _require(
        active.get("capacity") == 1 and active.get("before_active_count") == 0, "capacity witness"
    )
    active_outcomes = sorted(row.get("decision") for row in active["workers"])
    _require(
        active_outcomes == ["ALLOWED", "DENIED"],
        f"active-slot outcomes: {active_outcomes}; calls={active.get('observed_active_counts')}",
    )
    _require(
        active.get("final_active_count") == 1 and active.get("activation_event_count") == 1,
        "active-slot overcommit",
    )

    rollback = item["rollback_witness"]
    _require(
        rollback.get("baseline_counts") == rollback.get("post_rollback_counts"), "rollback residue"
    )
    _require(
        rollback.get("retry_outcome") == "SUCCEEDED"
        and rollback.get("retry_business_effect_count") == 1,
        "rollback retry",
    )

    lifecycle = item["lifecycle_witness"]
    _require(
        lifecycle.get("active_count_exclusion") is True
        and lifecycle.get("restore_entitlement_recheck") is True,
        "lifecycle exclusion/recheck",
    )
    _require(
        lifecycle.get("permanent_delete_terminal") is True
        and lifecycle.get("restore_after_permanent_delete") == "REJECTED",
        "terminal lifecycle",
    )
    _require(
        lifecycle.get("source_preserved") is True
        and lifecycle.get("revision_provenance_preserved") is True,
        "lifecycle provenance",
    )

    freeze = item["system_freeze_witness"]
    _require(
        freeze.get("actor_account_id") is None and freeze.get("state") == "FROZEN",
        "system actor/state",
    )
    _require(
        freeze.get("system_actor_class")
        and freeze.get("causation_reference")
        and freeze.get("policy_source_reference"),
        "system causation",
    )
    _require(
        freeze.get("auto_free_beacon_selected") is False and freeze.get("event_count") == 1,
        "system freeze event",
    )

    cleanup = item["cleanup_witness"]
    _require(cleanup.get("synthetic_counts_zero") is True, "synthetic cleanup")
    security = item["security_witness"]
    _require(
        security.get("credential_exposure") is False
        and security.get("raw_provider_payload_persisted") is False
        and security.get("production_data") is False,
        "security witness",
    )
    print(MARKER)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("evidence", type=Path)
    parser.add_argument("candidate_sha")
    args = parser.parse_args()
    verify(args.root, args.evidence, args.candidate_sha)
