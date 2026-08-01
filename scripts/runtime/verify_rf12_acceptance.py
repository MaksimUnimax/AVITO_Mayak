"""Independent consumer for the RF-12 real-PostgreSQL evidence document."""

# Explicit evidence fields are intentionally kept readable.
# ruff: noqa: E501

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

EXPECTED_HEAD = "RF12_RUNTIME_HARDEN"
EXPECTED_SCHEMA = "rf12-postgres-acceptance-v1"
EXPECTED_TECHNICAL_ID = "RF-12-CORRECTIVE-TRANSACTION-SERIALIZATION-SCHEMA-INVARIANTS-AND-REAL-POSTGRES-CLOSURE-20260801-03"
REQUIRED = {
    "empty_to_head", "rf09_to_manual_to_head", "manual_to_head", "metadata_parity",
    "physical_constraints", "command_matrix", "rollback", "concurrency", "payment_race",
    "cleanup", "foreign_equality",
}
COMMAND_IDS = {
    "tariff_bootstrap", "tariff_assignment", "basic_manual_renewal", "tariff_access_revoke",
    "manual_access_create", "manual_access_revoke", "payment_evidence_record",
    "payment_reconciliation", "manual_refund_reference", "active_beacon_slot",
    "scan_interval_window",
}
SHA = re.compile(r"^[0-9a-f]{40}$")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _head(root: Path) -> str:
    return subprocess.check_output(("git", "-C", str(root), "rev-parse", "HEAD"), text=True).strip()


def _fail(message: str) -> None:
    raise SystemExit(message)


def _observed_matrix(value: Any) -> bool:
    if not isinstance(value, dict) or not isinstance(value.get("rows"), list):
        return False
    rows = value["rows"]
    command_rows = [row for row in rows if row.get("command_id") in COMMAND_IDS]
    replay = next((row for row in rows if row.get("command_id") == "replay_mismatch"), None)
    if {row.get("command_id") for row in command_rows} != COMMAND_IDS or not isinstance(replay, dict):
        return False
    return (
        all(
        isinstance(row.get("production_method"), str)
        and row["production_method"].startswith("EntitlementsBillingRuntime.")
        and isinstance(row.get("post_state"), dict)
        and isinstance(row.get("business_effect_count"), int)
        and isinstance(row.get("audit_effect_count"), int)
        and isinstance(row.get("idempotency_effect_count"), int)
        for row in command_rows
        )
        and isinstance(replay.get("replay"), dict)
        and isinstance(replay.get("mismatch"), dict)
    )


def verify(root: Path, evidence_path: Path, expected_candidate_sha: str | None = None) -> None:
    if not evidence_path.is_file():
        _fail("RF12 acceptance evidence is absent")
    try:
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        _fail(f"invalid RF12 evidence: {type(exc).__name__}")
    if evidence.get("schema_version") != EXPECTED_SCHEMA:
        _fail("RF12 evidence schema version is not exact")
    if evidence.get("technical_id") != EXPECTED_TECHNICAL_ID:
        _fail("RF12 evidence Technical ID is not exact")
    source_sha = evidence.get("candidate_source_sha")
    expected = expected_candidate_sha or _head(root)
    if not isinstance(source_sha, str) or not SHA.fullmatch(source_sha) or source_sha != expected:
        _fail("RF12 candidate source identity is not exact")
    if evidence.get("alembic_head") != EXPECTED_HEAD or evidence.get("alembic_version_schema") not in {"mayak", "public"}:
        _fail("current Alembic head is not RF12_RUNTIME_HARDEN")
    historical = root / "alembic/versions/20260801_RF12_manual_grant_semantics.py"
    if _sha(historical) != evidence.get("historical_rf12_manual_grant_sha256"):
        _fail("historical RF12 migration integrity evidence is invalid")
    if not isinstance(evidence.get("rf09_digests"), dict):
        _fail("RF09 migration identity evidence is absent")
    for path, digest in evidence["rf09_digests"].items():
        candidate = root / path
        if not candidate.is_file() or _sha(candidate) != digest:
            _fail(f"RF09 migration changed: {path}")
    gates = evidence.get("gates")
    if not isinstance(gates, dict) or set(gates) != REQUIRED or any(gates[name] is not True for name in REQUIRED):
        _fail("RF12 acceptance gate set is incomplete or failed")
    postgres = evidence.get("postgres")
    if not isinstance(postgres, dict) or postgres.get("major") != 18:
        _fail("PostgreSQL 18 evidence is absent")
    ladders = evidence.get("migration_ladders")
    if (
        not isinstance(ladders, dict)
        or set(ladders) != {"empty_to_head", "rf09_to_manual_to_head", "manual_to_head"}
        or any(
            not isinstance(ladders[name], dict)
            or ladders[name].get("observed") is not True
            or not isinstance(ladders[name].get("revisions"), list)
            for name in ladders
        )
    ):
        _fail("migration gate lacks real ladder observations")
    parity = evidence.get("metadata_parity")
    if not isinstance(parity, dict) or parity.get("observed") is not True or parity.get("mismatches"):
        _fail("metadata parity was not observed from PostgreSQL")
    constraints = evidence.get("constraint_matrix")
    if not isinstance(constraints, dict) or constraints.get("result") is not True or not constraints.get("cases") or not all(case.get("rejected") is True for case in constraints["cases"]):
        _fail("physical constraint matrix is incomplete")
    if not _observed_matrix(evidence.get("command_matrix")):
        _fail("real command matrix structure is incomplete")
    concurrency = evidence.get("concurrency")
    if not isinstance(concurrency, dict) or concurrency.get("sessions") != 2 or len(concurrency.get("outcomes", [])) != 2 or concurrency.get("observed_effect_count") != 1 or concurrency.get("observed_terminal_count") != 1 or concurrency.get("result") is not True:
        _fail("real concurrency observations are incomplete")
    rollback = evidence.get("rollback")
    if (
        not isinstance(rollback, dict)
        or not isinstance(rollback.get("before"), dict)
        or not isinstance(rollback.get("after"), dict)
        or rollback.get("before_after_equal") is not True
        or rollback.get("business_effect") != 0
        or rollback.get("audit_effect") != 0
        or rollback.get("terminal_effect") != 0
        or rollback.get("retry_success") is not True
    ):
        _fail("rollback observations are incomplete")
    payment = evidence.get("payment_race")
    if not isinstance(payment, dict) or payment.get("result") is not True:
        _fail("payment race observations are incomplete")
    for key in ("same_provider_same_account", "same_provider_different_account"):
        pair = payment.get(key)
        if not isinstance(pair, dict) or pair.get("sessions") != 2 or len(pair.get("outcomes", [])) != 2 or pair.get("bounded") is not True or pair.get("committed_payment_count") != 1:
            _fail("payment race session observations are incomplete")
    foreign = evidence.get("foreign_equality")
    if not isinstance(foreign, dict) or foreign.get("observed") is not True or foreign.get("equal") is not True or "before" not in foreign or "after" not in foreign:
        _fail("foreign equality is not observed from before/after snapshots")
    if evidence.get("cleanup", {}).get("task_resources_removed") is not True:
        _fail("cleanup or foreign equality is not proven")
    if evidence.get("credential_exposure") is not False:
        _fail("credential exposure gate failed")
    source = (root / "src/mayak/modules/entitlements_and_billing/runtime.py").read_text(encoding="utf-8")
    if "metadata.tables[\"mayak.platform_audit_entries\"]" in source or "_AUDIT.insert" in source:
        _fail("direct foreign audit write remains")


if __name__ == "__main__":
    if len(sys.argv) not in (3, 4):
        raise SystemExit("usage: verify_rf12_acceptance.py ROOT EVIDENCE [EXPECTED_CANDIDATE_SHA]")
    verify(Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3] if len(sys.argv) == 4 else None)
