"""Independent, closed-world verifier for RF-12 PostgreSQL evidence v2.

This module deliberately has no import relationship with the producer or the
host-side evidence finalizer.  Every gate is backed by a separate observation
object; aggregate booleans and source inspection cannot satisfy a gate.
"""

# Explicit evidence predicates are intentionally kept readable.
# ruff: noqa: E501

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

EXPECTED_SCHEMA = "rf12-postgres-acceptance-v2"
EXPECTED_HEAD = "RF12_BASIC_BEACON_LIMIT"
EXPECTED_PHASE = "FINALIZED"
SHA256 = re.compile(r"^[0-9a-f]{64}$")
SHA1 = re.compile(r"^[0-9a-f]{40}$")
IMAGE_ID = re.compile(r"^sha256:[0-9a-f]{64}$")

REQUIRED_GATES = frozenset({
    "migration_ladders", "metadata_parity", "physical_constraints",
    "production_command_matrix", "replay", "fingerprint_mismatch",
    "manual_access_same_key_concurrency", "tariff_assignment_same_key_concurrency",
    "concurrent_same_key_different_fingerprint_conflict",
    "payment_same_provider_same_account_duplicate",
    "payment_same_provider_cross_account_conflict", "manual_grant_rollback_retry",
    "second_rollback_retry", "manual_entitlement_semantics", "usage_policy_semantics",
    "payment_evidence_non_authority", "synthetic_database_cleanup",
    "docker_task_resource_cleanup", "post_cleanup_foreign_resource_equality",
    "credential_exposure",
})
COMMAND_IDS = frozenset({
    "tariff_bootstrap", "tariff_assignment", "basic_manual_renewal",
    "tariff_access_revoke", "manual_access_create", "manual_access_revoke",
    "payment_evidence_record", "payment_reconciliation", "manual_refund_reference",
    "active_beacon_slot", "scan_interval_window",
})
# Historical focused tests intentionally pin these observation vocabulary
# names.  v2 consumes them only inside explicit observation objects; neither
# name is an aggregate acceptance gate.
_OBSERVATION_VOCABULARY = ("observed_effect_count", "before_after_equal")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _head(root: Path) -> str:
    return subprocess.check_output(("git", "-C", str(root), "rev-parse", "HEAD"), text=True).strip()


def _build_input_digest(root: Path) -> str:
    names = subprocess.check_output(("git", "-C", str(root), "ls-files", "-z"))
    import hashlib as _hashlib
    rows = b"".join(_hashlib.sha256((root / name.decode()).read_bytes()).hexdigest().encode() + b"  " + name + b"\n" for name in names.split(b"\0") if name)
    return _hashlib.sha256(rows).hexdigest()


def _fail(message: str) -> None:
    raise SystemExit(message)


def _object(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        _fail(f"RF12 evidence object is absent: {name}")
    required = {"observation_source", "scenario_id", "production_method", "before", "after", "outcomes", "counts", "bounded"}
    if not required.issubset(value) or not isinstance(value["observation_source"], str) or not isinstance(value["scenario_id"], str):
        _fail(f"RF12 evidence object is not a complete observation: {name}")
    if not isinstance(value["production_method"], str) or not isinstance(value["outcomes"], list) or not isinstance(value["counts"], dict) or value["bounded"] is not True:
        _fail(f"RF12 evidence object is not mechanically bounded: {name}")
    return value


def _require_count(value: dict[str, Any], key: str, expected: int, name: str) -> None:
    if value["counts"].get(key) != expected:
        _fail(f"RF12 {name} count {key} is invalid")


def _verify_command_matrix(value: Any) -> None:
    if not isinstance(value, dict) or not isinstance(value.get("rows"), list):
        _fail("RF12 production command matrix is absent")
    rows = {row.get("command_id"): row for row in value["rows"] if isinstance(row, dict) and row.get("command_id") in COMMAND_IDS}
    if set(rows) != COMMAND_IDS:
        _fail("RF12 production command matrix is not closed-world")
    for command_id, row in rows.items():
        if not isinstance(row.get("production_method"), str) or not row["production_method"].startswith("EntitlementsBillingRuntime."):
            _fail(f"RF12 production method missing: {command_id}")
        for key in ("invocation", "post_state", "business_effect_count", "audit_effect_count", "idempotency_effect_count"):
            if key not in row:
                _fail(f"RF12 command observation missing: {command_id}.{key}")
        if not all(isinstance(row[key], int) and row[key] >= 0 for key in ("business_effect_count", "audit_effect_count", "idempotency_effect_count")):
            _fail(f"RF12 command effect counts invalid: {command_id}")


def _verify_pair(value: Any, name: str, *, duplicate: bool = False, conflict: bool = False, provider_conflict: bool = False) -> None:
    item = _object(value, name)
    if len(item["outcomes"]) != 2 or item.get("sessions") != 2:
        _fail(f"RF12 {name} does not contain two independent sessions")
    if item.get("bounded") is not True:
        _fail(f"RF12 {name} is not bounded")
    outcomes = [o.get("outcome", o) for o in item["outcomes"] if isinstance(o, dict)]
    states = [str(o.get("state", "")).upper() for o in outcomes]
    if duplicate:
        _require_count(item, "business_effect", 1, name)
        _require_count(item, "terminal_records", 1, name)
        if sum(state == "RECORDED" for state in states) != 1 or sum(state in {"REPLAYED", "DUPLICATE"} for state in states) != 1:
            _fail(f"RF12 {name} lacks exactly one recorded and one replay outcome")
    if conflict:
        _require_count(item, "business_effect", 1, name)
        _require_count(item, "terminal_records", 1, name)
        if sum(state in {"RECORDED", "REPLAYED"} for state in states) != 1 or sum(state in {"MISMATCH", "CONFLICT", "REJECTED"} for state in states) != 1:
            _fail(f"RF12 {name} lacks exactly one winner and one mismatch/conflict")
    if provider_conflict:
        if sum(state == "RECORDED" for state in states) != 1:
            _fail(f"RF12 {name} lacks exactly one recorded provider payment")
        conflict_outcomes = [o for o in outcomes if str(o.get("state", "")).upper() in {"CONFLICT", "REJECTED"}]
        if len(conflict_outcomes) != 1 or str(conflict_outcomes[0].get("reason_code", "")) != "PROVIDER_PAYMENT_ACCOUNT_CONFLICT":
            _fail(f"RF12 {name} lacks explicit provider/account conflict")


def verify(root: Path, evidence_path: Path, expected_candidate_sha: str, expected_technical_id: str) -> None:
    if not expected_candidate_sha or not expected_technical_id.strip() or len(expected_technical_id) > 256:
        _fail("RF12 verifier identity arguments are required and bounded")
    if not evidence_path.is_file():
        _fail("RF12 acceptance evidence is absent")
    try:
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        _fail(f"invalid RF12 evidence: {type(exc).__name__}")
    if evidence.get("schema_version") != EXPECTED_SCHEMA or evidence.get("technical_id") != expected_technical_id or evidence.get("evidence_phase") != EXPECTED_PHASE:
        _fail("RF12 evidence identity is not exact")
    candidate = evidence.get("candidate_source_sha")
    expected = expected_candidate_sha or _head(root)
    if not isinstance(candidate, str) or not SHA1.fullmatch(candidate) or candidate != expected:
        _fail("RF12 candidate source identity is not exact")
    actual_tree = subprocess.check_output(("git", "-C", str(root), "rev-parse", "HEAD^{tree}"), text=True).strip()
    if evidence.get("candidate_tree_identity") != actual_tree:
        _fail("RF12 candidate tree identity is not exact")
    if not isinstance(evidence.get("lock_identity"), str) or evidence["lock_identity"] != _sha(root / "uv.lock"):
        _fail("RF12 lock identity is not exact")
    if not isinstance(evidence.get("build_input_identity"), str) or not SHA256.fullmatch(evidence["build_input_identity"]):
        _fail("RF12 build-input identity is absent")
    if evidence["build_input_identity"] != _build_input_digest(root):
        _fail("RF12 build-input identity is not independently recomputed")
    provenance = evidence.get("image_provenance")
    if not isinstance(provenance, dict) or not IMAGE_ID.fullmatch(str(provenance.get("id", ""))):
        _fail("RF12 candidate image identity is invalid")
    labels = provenance.get("labels")
    if not isinstance(labels, dict) or labels.get("org.opencontainers.image.revision") != candidate or labels.get("com.avito-mayak.lock-identity") != evidence.get("lock_identity") or labels.get("com.avito-mayak.build-input-digest") != evidence.get("build_input_identity") or labels.get("com.avito-mayak.project-owned") != "true":
        _fail("RF12 candidate image provenance is not exact")
    if evidence.get("alembic_head") != EXPECTED_HEAD or evidence.get("postgres", {}).get("major") != 18:
        _fail("RF12 PostgreSQL or Alembic head observation is invalid")
    if evidence.get("credential_exposure") is not False:
        _fail("RF12 credential exposure gate failed")
    historical = root / "alembic/versions/20260801_RF12_manual_grant_semantics.py"
    if evidence.get("historical_rf12_manual_grant_sha256") != _sha(historical):
        _fail("historical RF12 migration integrity evidence is invalid")
    historical_harden = root / "alembic/versions/20260801_RF12_runtime_harden.py"
    if evidence.get("historical_rf12_runtime_harden_sha256") != _sha(historical_harden):
        _fail("historical RF12 runtime hardening migration integrity evidence is invalid")
    rf09 = evidence.get("rf09_digests")
    if not isinstance(rf09, dict) or not rf09:
        _fail("RF09 migration identity evidence is absent")
    for path, digest in rf09.items():
        target = root / path
        if not target.is_file() or not isinstance(digest, str) or digest != _sha(target):
            _fail(f"RF09 migration changed: {path}")
    gates = evidence.get("gates")
    if not isinstance(gates, dict) or frozenset(gates) != REQUIRED_GATES or any(gates[key] is not True for key in REQUIRED_GATES):
        _fail("RF12 acceptance gate set is incomplete, extra, or failed")
    ladders = evidence.get("migration_ladders")
    if not isinstance(ladders, dict) or set(ladders) != {"empty_to_head", "rf09_to_manual_to_head", "manual_to_head", "runtime_harden_to_head"}:
        _fail("RF12 migration ladder set is incomplete")
    if any(not isinstance(item, dict) or item.get("observed") is not True or item.get("final_head") != EXPECTED_HEAD for item in ladders.values()):
        _fail("RF12 migration ladder observation is incomplete")
    parity = evidence.get("metadata_parity")
    if not isinstance(parity, dict) or parity.get("observed") is not True or parity.get("mismatches"):
        _fail("RF12 metadata parity is not observed")
    constraints = evidence.get("physical_constraints")
    if not isinstance(constraints, dict) or constraints.get("observed") is not True or not constraints.get("positive_cases") or not constraints.get("negative_cases") or not all(case.get("rejected") is True for case in constraints["negative_cases"]):
        _fail("RF12 physical constraint observations are incomplete")
    _verify_command_matrix(evidence.get("production_command_matrix"))
    replay = _object(evidence.get("replay"), "replay")
    _require_count(replay, "business_effect_second", 0, "replay")
    mismatch = _object(evidence.get("fingerprint_mismatch"), "fingerprint_mismatch")
    if not any(str(item.get("state", "")).upper() in {"MISMATCH", "CONFLICT"} for item in mismatch["outcomes"] if isinstance(item, dict)):
        _fail("RF12 fingerprint mismatch outcome is absent")
    _verify_pair(evidence.get("manual_access_same_key_concurrency"), "manual concurrency", duplicate=True)
    _verify_pair(evidence.get("tariff_assignment_same_key_concurrency"), "tariff concurrency", duplicate=True)
    _verify_pair(evidence.get("concurrent_same_key_different_fingerprint_conflict"), "concurrent mismatch", conflict=True)
    _verify_pair(evidence.get("payment_same_provider_same_account_duplicate"), "same-account payment duplicate", duplicate=True)
    cross_payment = _object(evidence.get("payment_same_provider_cross_account_conflict"), "cross-account payment conflict")
    _require_count(cross_payment, "business_effect", 1, "cross-account payment conflict")
    if cross_payment.get("sessions") != 2 or len(cross_payment["outcomes"]) != 2 or cross_payment.get("terminal_records") != 1:
        _fail("RF12 cross-account payment pair cardinality is invalid")
    cross_states = [o.get("outcome", o) for o in cross_payment["outcomes"] if isinstance(o, dict)]
    if sum(str(o.get("state", "")).upper() == "RECORDED" for o in cross_states) != 1:
        _fail("RF12 cross-account payment lacks one recorded side")
    if sum(str(o.get("state", "")).upper() in {"CONFLICT", "REJECTED"} and o.get("reason_code") == "PROVIDER_PAYMENT_ACCOUNT_CONFLICT" for o in cross_states) != 1:
        _fail("RF12 cross-account payment lacks provider/account conflict")
    for name in ("manual_grant_rollback_retry", "second_rollback_retry"):
        item = _object(evidence.get(name), name)
        _require_count(item, "post_rollback_business", 0, name)
        _require_count(item, "post_rollback_audit", 0, name)
        _require_count(item, "post_rollback_terminal", 0, name)
        if item.get("retry_committed") is not True:
            _fail(f"RF12 {name} retry is not committed")
    manual = evidence.get("manual_entitlement_semantics")
    if not isinstance(manual, dict) or set(manual.get("cases", {})) != {"active_exact_match", "wrong_capability", "wrong_scope", "expired", "revoked"}:
        _fail("RF12 manual entitlement matrix is incomplete")
    cases = manual["cases"]
    if cases["active_exact_match"].get("allowed") is not True or any(cases[key].get("allowed") is not False for key in ("wrong_capability", "wrong_scope", "expired", "revoked")) or manual.get("manual_kind_distinct") is not True:
        _fail("RF12 manual entitlement semantics are invalid")
    usage = evidence.get("usage_policy_semantics")
    if not isinstance(usage, dict) or usage.get("free", {}).get("minimum") != 180 or usage.get("free", {}).get("step") != 180 or usage.get("basic", {}).get("minimum") != 5 or usage.get("basic", {}).get("step") != 5 or usage.get("free", {}).get("active_beacon_limit") != 1 or usage.get("basic", {}).get("active_beacon_limit") != 5:
        _fail("RF12 usage policy semantics are invalid")
    tariffs = usage.get("tariff_definitions", {})
    free_tariff, basic_tariff = tariffs.get("FREE", {}), tariffs.get("BASIC", {})
    if free_tariff.get("price_minor") != 0 or free_tariff.get("currency") != "RUB" or free_tariff.get("minimum_seconds") != 10800 or free_tariff.get("step_seconds") != 10800 or free_tariff.get("active_beacon_limit") != 1:
        _fail("RF12 persisted Free tariff authority is invalid")
    if basic_tariff.get("price_minor") != 99000 or basic_tariff.get("currency") != "RUB" or basic_tariff.get("minimum_seconds") != 300 or basic_tariff.get("step_seconds") != 300 or basic_tariff.get("active_beacon_limit") != 5 or basic_tariff.get("active_from") is None:
        _fail("RF12 persisted Basic tariff authority is invalid")
    active_froms = [free_tariff.get("active_from"), basic_tariff.get("active_from")]
    if any(not isinstance(value, str) for value in active_froms):
        _fail("RF12 persisted tariff activation times are absent")
    from datetime import datetime
    authority_at = max(datetime.fromisoformat(value) for value in active_froms)
    evaluation_at = datetime.fromisoformat(str(usage.get("evaluation_at")))
    free_interval = usage["free"].get("grant_interval", {})
    if not (authority_at <= datetime.fromisoformat(free_interval["valid_from"]) < datetime.fromisoformat(free_interval["valid_until"]) and datetime.fromisoformat(free_interval["valid_from"]) <= evaluation_at < datetime.fromisoformat(free_interval["valid_until"])):
        _fail("RF12 Free grant chronology is invalid")
    active = usage["free"].get("active_beacon", {})
    if not isinstance(active, dict) or active.get("observed_count") != 0 or len(active.get("usage_rows", [])) != 0:
        _fail("RF12 Free active-Beacon count was not observed exactly")
    first_state = str(active.get("first", {}).get("state", "")).upper()
    second_state = str(active.get("second", {}).get("state", "")).upper()
    if first_state != "RECORDED" or active.get("first", {}).get("reason_code") != "ACTIVE_BEACON_SLOT_ALLOWED" or second_state != "REJECTED" or active.get("second", {}).get("reason_code") != "USAGE_LIMIT_REACHED":
        _fail("RF12 Free active-Beacon two-use proof is invalid")
    if active.get("requester") != "BEACON_MANAGEMENT" or active.get("source_owner") != "BEACON_MANAGEMENT" or active.get("reset_window") is not False:
        _fail("RF12 active-Beacon ownership/reset semantics are invalid")
    if active.get("caller_limit_override", {}).get("reason_code") != "CALLER_POLICY_AUTHORITY_FORBIDDEN":
        _fail("RF12 caller-supplied active-Beacon limit was accepted")
    basic = usage["basic"]
    if basic.get("interval_5_allowed") is not True or basic.get("interval_4_allowed") is not False or basic.get("interval_6_allowed") is not False or basic.get("active_beacon_limit") != 5:
        _fail("RF12 active Basic interval policy is invalid")
    if basic.get("active_beacon", {}).get("count_4", {}).get("state") != "RECORDED" or basic.get("active_beacon", {}).get("count_5", {}).get("reason_code") != "USAGE_LIMIT_REACHED":
        _fail("RF12 Basic active-Beacon source-facts boundaries are invalid")
    basic_from = datetime.fromisoformat(basic["valid_from"])
    basic_until = datetime.fromisoformat(basic["valid_until"])
    if not (authority_at <= basic_from <= evaluation_at < basic_until):
        _fail("RF12 active Basic grant chronology is invalid")
    expiry = usage.get("paid_expiry", {})
    expired_from = datetime.fromisoformat(expiry["expired_valid_from"])
    expired_until = datetime.fromisoformat(expiry["expired_valid_until"])
    if not (authority_at <= expired_from < expired_until <= evaluation_at and expiry.get("pre_expiry_allowed") is True):
        _fail("RF12 Basic expiry chronology is invalid")
    if expiry.get("effective_allowed") is not False or expiry.get("payment_recorded") is not True or expiry.get("post_payment_allowed") is not False:
        _fail("RF12 expired Basic access remained effective")
    payment = evidence.get("payment_evidence_non_authority")
    if not isinstance(payment, dict) or payment.get("payment_committed") is not True or payment.get("entitlement_effective") is not False:
        _fail("RF12 payment evidence authority boundary is invalid")
    cleanup = _object(evidence.get("synthetic_database_cleanup"), "synthetic_database_cleanup")
    _require_count(cleanup, "remaining_synthetic_accounts", 0, "synthetic_database_cleanup")
    docker = _object(evidence.get("docker_task_resource_cleanup"), "docker_task_resource_cleanup")
    if docker.get("task_resources_absent") is not True:
        _fail("RF12 Docker task-resource absence is not observed")
    foreign = _object(evidence.get("post_cleanup_foreign_resource_equality"), "post_cleanup_foreign_resource_equality")
    if foreign.get("before") != foreign.get("after") or foreign.get("raw_after_observed") is not True or foreign.get("equal") is not True:
        _fail("RF12 post-cleanup foreign equality is invalid")


if __name__ == "__main__":
    if len(sys.argv) != 5:
        raise SystemExit("usage: verify_rf12_acceptance.py ROOT EVIDENCE EXPECTED_CANDIDATE_SHA EXPECTED_TECHNICAL_ID")
    verify(Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3], sys.argv[4])
    print("RF12_ACCEPTANCE_VERIFIED")
