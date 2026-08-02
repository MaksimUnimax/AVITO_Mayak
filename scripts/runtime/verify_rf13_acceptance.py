"""Fail-closed RF-13 v5 acceptance verifier and semantic coverage registry."""

# ruff: noqa

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import platform
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

MARKER = "RF13_ACCEPTANCE_VERIFIED"
TECHNICAL_ID = "RF-13-BEACON-MANAGEMENT-RUNTIME-POSTGRES-20260802-01"
EXPECTED_BASE = "df517b397c6f4bc665ee760e173489a4a08ee196"
SCHEMA_VERSION = "rf13-postgres-acceptance-v5"

REQUIRED_SECTIONS = (
    "identity", "toolchain", "migration_setup_identity", "physical_schema",
    "preparation", "positive_snapshot", "negative_snapshot_matrix",
    "patch_lww_concurrency", "different_field_concurrency_applicability",
    "idempotency_concurrency", "rollback", "ownership", "active_slot_concurrency",
    "lifecycle_history", "system_freeze_positive", "system_authority_mismatch_negative",
    "revision_immutability", "cleanup", "security_witness",
)

_CASE_LINES = """
identity_candidate_sha identity_candidate_tree identity_parent identity_technical_id identity_schema_version
toolchain_python toolchain_uv toolchain_lock_digest postgres_major
migration_empty_head migration_version_table migration_head
preparation_state preparation_current_revision preparation_source_url preparation_event_count
snapshot_positive_delta snapshot_positive_current_revision snapshot_negative_revision snapshot_negative_current_revision snapshot_source_url
patch_sessions patch_barrier patch_worker_count patch_committed_count patch_revision_count patch_duplicate_revision patch_current_not_max patch_value_not_max patch_final_revision patch_orphan_revision patch_orphan_override
idempotency_sessions idempotency_barrier idempotency_two_effects idempotency_two_terminals idempotency_resource_ids idempotency_missing_replay idempotency_fake_replay
active_sessions active_barrier active_worker_missing active_counts active_both_allowed active_denial_reason active_final_count active_event_count
rollback_post_counts rollback_baseline_copy rollback_retry_failure rollback_duplicate_business rollback_duplicate_idempotency
ownership_read_accept ownership_state_change ownership_unverified_accept ownership_accept
lifecycle_active_count restore_entitlement_missing restore_stale_entitlement source_url_change revision_reference_change permanent_delete_restorable restore_after_delete event_sequence lifecycle_event_sequence
freeze_class freeze_actor_account freeze_persisted_class freeze_causation freeze_policy freeze_event_count freeze_state auto_free resolved_class_mismatch
old_revision current_revision_wrong
schema_revision_unique schema_current_fk schema_revision_positive schema_revision_pair schema_source_url schema_actor_causation metadata_parity
cleanup_residue cleanup_preexisting
security_secret_count security_raw_payload security_production_data
"""
REQUIRED_TAMPER_CASES = tuple(_CASE_LINES.split())


def _path(item: dict[str, Any], dotted: str) -> Any:
    node: Any = item
    for part in dotted.split("."):
        if isinstance(node, dict) and part in node:
            node = node[part]
        elif isinstance(node, list) and part.isdigit() and int(part) < len(node):
            node = node[int(part)]
        else:
            raise SystemExit(f"raw observation missing: {dotted}")
    return node


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def _count(value: Any, name: str) -> int:
    _require(type(value) is int and value >= 0, f"malformed count: {name}")
    return value


def _same(a: Any, b: Any, message: str) -> None:
    _require(a == b, message)


@dataclass(frozen=True)
class Requirement:
    checker: Callable[[dict[str, Any]], None]
    raw_paths: tuple[str, ...]
    tamper_cases: tuple[str, ...]


@dataclass(frozen=True)
class TamperMutation:
    requirement_ids: tuple[str, ...]
    changed_paths: tuple[str, ...]
    mutate: Callable[[dict[str, Any]], None]


def _set(item: dict[str, Any], path: str, value: Any) -> None:
    parts = path.split(".")
    node = item
    for part in parts[:-1]:
        node = node[int(part)] if isinstance(node, list) else node[part]
    if isinstance(node, list):
        node[int(parts[-1])] = value
    else:
        node[parts[-1]] = value


def _toggle(item: dict[str, Any], path: str) -> None:
    old = _path(item, path)
    if isinstance(old, bool):
        _set(item, path, not old)
    elif isinstance(old, int):
        _set(item, path, old + 1)
    elif isinstance(old, str):
        _set(item, path, old + "-tampered")
    elif isinstance(old, list):
        _set(item, path, old + ["tampered"])
    else:
        _set(item, path, "tampered")


def _mut(path: str, requirement: str, value: Any = None) -> Callable[[dict[str, Any]], None]:
    def apply(item: dict[str, Any]) -> None:
        old = _path(item, path)
        _set(item, path, value if value is not None else (not old if isinstance(old, bool) else old + "-tampered" if isinstance(old, str) else old + 1))
    return apply


def _check_identity(item: dict[str, Any]) -> None:
    identity = _path(item, "identity")
    _require(identity["technical_id"] == TECHNICAL_ID, "technical id mismatch")
    _require(identity["candidate_sha"] == item["_expected_candidate_sha"], "candidate SHA mismatch")
    _require(identity["candidate_tree"] == item["_actual_candidate_tree"], "candidate tree mismatch")
    _require(identity["parent"] == EXPECTED_BASE, "parent mismatch")
    _require(identity["schema_version"] == SCHEMA_VERSION, "identity schema mismatch")


def _check_toolchain(item: dict[str, Any]) -> None:
    tool = _path(item, "toolchain")
    _require(tool["python"] == "3.14.6" and platform.python_version() == "3.14.6", "Python mismatch")
    uv = next((x for x in subprocess.check_output(("uv", "--version"), text=True).split() if x[:1].isdigit()), "")
    _require(tool["uv"] == "0.11.31" and uv == "0.11.31", "uv mismatch")
    _require(tool["uv_lock_sha256"] == hashlib.sha256(Path(item["_root"] + "/uv.lock").read_bytes()).hexdigest(), "uv.lock mismatch")
    _require(tool["postgres_major"] == 18, "PostgreSQL major mismatch")


def _check_migration(item: dict[str, Any]) -> None:
    m = _path(item, "migration_setup_identity")
    _require(m["empty_to_head"]["before"] == "empty", "migration empty state")
    _require(m["empty_to_head"]["after"] == "RF13_BEACON_RUNTIME_HARDEN", "migration upgrade")
    _require(m["version_table"] == "RF13_BEACON_RUNTIME_HARDEN" and m["head"] == m["version_table"], "migration head")


def _check_schema(item: dict[str, Any]) -> None:
    schema = _path(item, "physical_schema")
    _require(schema["metadata_parity"] is True, "metadata parity")
    constraints = schema["constraints"]
    _require(isinstance(constraints, list) and constraints, "physical constraints missing")
    by_name = {row["name"]: row for row in constraints}
    _require(any(row["type"] == "u" and row["columns"] == ["revision_id"] for row in constraints), "revision uniqueness")
    _require(any(row["type"] == "f" and row["columns"] == ["current_revision_id"] and row["referenced_table"] == "beacon_configuration_revisions" and row["referenced_columns"] == ["revision_id"] for row in constraints), "current revision FK")
    unique = next(row for row in constraints if row["type"] == "u" and row["columns"] == ["revision_id"])
    current_fk = next(row for row in constraints if row["type"] == "f" and row["columns"] == ["current_revision_id"])
    _require("unique" in unique["definition"].lower() and "revision_id" in unique["definition"].lower(), "revision id definition")
    _require("beacon_configuration_revisions" in current_fk["definition"] and "revision_id" in current_fk["definition"], "current revision definition")
    required = ("current_revision_no", "source_url", "actor_account_id", "causation_reference")
    definitions = " ".join(str(expression).lower() for expression in schema["exact_constraint_definitions"])
    normalized = definitions.replace("(", "").replace(")", "").replace("::text", "")
    _require("current_revision_no is null or current_revision_no > 0" in normalized, "revision positivity")
    _require("source_url is null or btrimsource_url <> ''" in normalized.replace("btrim(source_url)", "btrimsource_url"), "source URL invariant")
    _require("current_revision_no is null and current_revision_id is null" in normalized and "current_revision_no is not null and current_revision_id is not null" in normalized, "revision pair invariant")
    _require("actor_account_id is not null and system_actor_class is null" in normalized and "actor_account_id is null and system_actor_class is not null" in normalized, "actor causation invariant")
    _require("check (true)" not in definitions, "weak physical constraint")


def _check_preparation(item: dict[str, Any]) -> None:
    p = _path(item, "preparation")
    _require(p["state"] == "DRAFT" and p["current_revision_no"] is None and p["current_revision_id"] is None, "preparation state")
    _require(p["lifecycle_event_count"] == 1 and len(p["lifecycle_events"]) == 1, "preparation event")
    event = p["lifecycle_events"][0]
    _require(event["from_state"] is None and event["to_state"] == "DRAFT", "preparation transition")
    _require(p["revision_count"] == 0 and p["override_count"] == 0 and p["source_url"] == p["submitted_source_url"], "preparation observation")


def _check_positive(item: dict[str, Any]) -> None:
    p = _path(item, "positive_snapshot")
    _require(p["post_revision_count"] == p["pre_revision_count"] + 1 and p["state_after"] == "READY", "positive revision/state")
    _require(p["parser_outcome"] == "CLEAN" and p["accepted_as_clean"] is True and p["parser_evidence_reference"], "positive parser")
    _require(p["current_revision_id"] == p["persisted_revision_id"] and p["current_revision_no"] == p["persisted_revision_no"], "positive current pointer")
    _require(p["source_url_before"] == p["source_url_after"] and p["override_count"] == 0, "positive source")


def _check_negative(item: dict[str, Any]) -> None:
    rows = _path(item, "negative_snapshot_matrix")
    _require(len(rows) == 7, "seven negative outcomes required")
    statuses = {"MALFORMED", "INCOMPLETE", "CAPTCHA_AFFECTED", "BLOCKED", "ROUTE_FAILED", "AMBIGUOUS", "UNSUPPORTED"}
    _require({row["status"] for row in rows} == statuses, "negative statuses")
    for row in rows:
        for name in ("exception_or_result", "pre_revision_count", "post_revision_count", "pre_override_count", "post_override_count", "current_revision_before", "current_revision_after", "row_version_before", "row_version_after"):
            _require(name in row, f"negative field missing: {name}")
        _require(row["pre_revision_count"] == row["post_revision_count"] and row["pre_override_count"] == row["post_override_count"] and row["current_revision_before"] == row["current_revision_after"] and row["row_version_before"] == row["row_version_after"], "negative mutation")


def _check_patch(item: dict[str, Any]) -> None:
    p = _path(item, "patch_lww_concurrency")
    workers = p["workers"]
    _require(p["sessions"] == 2 and p["barrier"] is True and len(workers) == 2 and all(w["outcome"] == "SUCCEEDED" for w in workers), "patch sessions")
    _require(len({w["idempotency_key"] for w in workers}) == 2 and len({w["revision_no"] for w in workers}) == 2, "patch workers")
    _require(p["committed_count"] == p["revision_count"] == 2 and p["final_revision_no"] == max(w["revision_no"] for w in workers), "patch revisions")
    winner = max(workers, key=lambda w: w["revision_no"])
    _require(p["final_value"] == winner["value"] and p["final_row_version_delta"] == 2 and p["orphan_revision_count"] == p["orphan_override_count"] == 0, "patch LWW")


def _check_idem(item: dict[str, Any]) -> None:
    p = _path(item, "idempotency_concurrency")
    _require(p["sessions"] == 2 and p["barrier"] is True and p["attempt_count"] == 2, "idempotency sessions")
    _require(len({o["idempotency_key"] for o in p["outcomes"]}) == 1 and len({o["fingerprint"] for o in p["outcomes"]}) == 1, "idempotency key")
    _require(sorted(o["repository_decision"] for o in p["outcomes"]) == ["NEW", "REPLAY_TERMINAL"], "repository decisions")
    _require(p["business_effect_count"] == p["terminal_record_count"] == 1 and len({o["resource_id"] for o in p["outcomes"]}) == 1, "idempotency effects")


def _check_rollback(item: dict[str, Any]) -> None:
    p = _path(item, "rollback")
    _require(p["in_transaction"] != p["baseline"] and p["post_rollback"] == p["baseline"], "rollback observation")
    _require(p["post_rollback"] == p["post_independent_query"] and p["retry_business_effect_count"] == 1 and p["retry_terminal_effect_count"] == 1 and p["rollback_resource_absent"] is True and p["retry_resource_persisted"] is True, "rollback retry")


def _check_ownership(item: dict[str, Any]) -> None:
    ownership = _path(item, "ownership")
    for name, p in ownership.items():
        expected_reason = "actor does not own Beacon" if name == "foreign_read" else "actor verification required"
        _require(p["exception_class"] == "BeaconRuntimeError" and p["safe_reason"] and p["row_version_before"] == p["row_version_after"] and p["revision_count_before"] == p["revision_count_after"] and p["event_count_before"] == p["event_count_after"] and p["audit_count_before"] == p["audit_count_after"] and p["idempotency_count_before"] == p["idempotency_count_after"], "ownership zero effect")
        _require(p["safe_reason"] == expected_reason, "ownership denial reason")


def _check_active(item: dict[str, Any]) -> None:
    p = _path(item, "active_slot_concurrency")
    _require(p["sessions"] == 2 and p["barrier"] is True and p["capacity"] == 1 and p["baseline_active_count"] == 0, "active setup")
    _require(sorted(x["active_count"] for x in p["entitlement_observations"]) == [0, 1], "active entitlement counts")
    _require(sum(w["decision"] == "ALLOWED" for w in p["workers"]) == 1 and sum(w["decision"] == "DENIED" for w in p["workers"]) == 1, "active decisions")
    denied = next(w for w in p["workers"] if w["decision"] == "DENIED")
    _require(denied["exception_class"] == "BeaconRuntimeError" and denied["reason"] == "current entitlement does not allow lifecycle action" and p["final_active_count"] == 1 and p["activation_event_count"] == 1, "active attribution")


def _check_lifecycle(item: dict[str, Any]) -> None:
    p = _path(item, "lifecycle_history")
    _require(p["event_rows"] == sorted(p["event_rows"], key=lambda row: row["sequence"]), "event order")
    _require(p["active_count_after_archive"] == 0 and p["restore_entitlement"]["action"] == "restore" and p["restore_entitlement"]["fresh"] is True and p["restore_entitlement"]["allowed"] is True, "lifecycle restore")
    expected_to_states = {"DRAFT", "READY", "ACTIVE", "PAUSED", "ARCHIVED", "PERMANENTLY_DELETED"}
    observed_to_states = {row["to_state"] for row in p["event_rows"]}
    _require(expected_to_states <= observed_to_states, "lifecycle event semantics")
    _require(p["source_url_before_archive"] == p["source_url_after_restore"] and p["revision_id_before_archive"] == p["revision_id_after_restore"] and p["permanent_delete_state"] == "PERMANENTLY_DELETED" and p["rejected_restore"]["exception_class"] == "BeaconRuntimeError" and p["rejected_restore"]["reason"] == "permanent delete is terminal", "lifecycle history")


def _check_freeze(item: dict[str, Any]) -> None:
    p = _path(item, "system_freeze_positive")
    _require(p["resolved_class"] == p["requested_service_class"] == p["persisted_system_actor_class"] == "ENTITLEMENTS_AND_BILLING_SERVICE", "freeze authority")
    _require(p["event"]["actor_account_id"] is None and p["event"]["to_state"] == "FROZEN" and p["event"]["causation_reference"] == "rf13-expiry-causation" and p["event"]["policy_source_reference"] == "rf13-paid-expiry-policy" and p["freeze_event_count"] == 1 and not p["auto_free_observations"], "freeze event")


def _check_mismatch(item: dict[str, Any]) -> None:
    p = _path(item, "system_authority_mismatch_negative")
    _require(p["resolved_class"] == "MAINTENANCE_SERVICE" and p["requested_causation_class"] == "ENTITLEMENTS_AND_BILLING_SERVICE" and p["exception_class"] == "BeaconRuntimeError" and p["reason"] == "system authority class does not match causation", "authority mismatch")
    _require(p["before"] == p["after"], "authority side effect")


def _check_revision(item: dict[str, Any]) -> None:
    p = _path(item, "revision_immutability")
    _require(p["revision_1_hash_before"] == p["revision_1_hash_after"] and p["revision_1_id"] != p["revision_2_id"] and p["current_revision_id"] == p["revision_2_id"] and p["current_revision_no"] == p["revision_2_no"], "revision immutability")


def _check_cleanup(item: dict[str, Any]) -> None:
    p = _path(item, "cleanup")
    _require(all(v == 0 for v in p["synthetic_post_counts"].values()) and p["preexisting_preserved"] is True and p["preexisting_baseline"] == p["preexisting_after"], "cleanup")


def _check_security(item: dict[str, Any]) -> None:
    p = _path(item, "security_witness")
    for key in ("secret_scan_match_count", "raw_provider_payload_forbidden_schema_field_count", "raw_provider_payload_forbidden_persisted_value_count", "production_personal_data_marker_count", "non_synthetic_source_count"):
        _require(_count(p[key], key) == 0, "security exposure")


def _check_applicability(item: dict[str, Any]) -> None:
    p = _path(item, "different_field_concurrency_applicability")
    _require(p["applicable"] is False and p["reason"], "different-field applicability")


def _spec(checker: Callable[[dict[str, Any]], None], paths: tuple[str, ...], cases: tuple[str, ...]) -> Requirement:
    return Requirement(checker, paths, cases)


REQUIREMENT_REGISTRY: dict[str, Requirement] = {
    "identity": _spec(_check_identity, ("identity",), tuple(REQUIRED_TAMPER_CASES[0:5])),
    "toolchain": _spec(_check_toolchain, ("toolchain",), tuple(REQUIRED_TAMPER_CASES[5:9])),
    "migration": _spec(_check_migration, ("migration_setup_identity",), tuple(REQUIRED_TAMPER_CASES[9:12])),
    "physical_schema": _spec(_check_schema, ("physical_schema",), tuple(REQUIRED_TAMPER_CASES[76:83])),
    "preparation": _spec(_check_preparation, ("preparation",), tuple(REQUIRED_TAMPER_CASES[12:16])),
    "positive_snapshot": _spec(_check_positive, ("positive_snapshot",), tuple(REQUIRED_TAMPER_CASES[16:21])),
    "negative_snapshot_matrix": _spec(_check_negative, ("negative_snapshot_matrix",), ("snapshot_negative_revision", "snapshot_negative_current_revision")),
    "patch_lww": _spec(_check_patch, ("patch_lww_concurrency",), tuple(REQUIRED_TAMPER_CASES[21:32])),
    "idempotency": _spec(_check_idem, ("idempotency_concurrency",), tuple(REQUIRED_TAMPER_CASES[32:39])),
    "active_slot": _spec(_check_active, ("active_slot_concurrency",), tuple(REQUIRED_TAMPER_CASES[39:47])),
    "rollback": _spec(_check_rollback, ("rollback",), tuple(REQUIRED_TAMPER_CASES[47:52])),
    "ownership": _spec(_check_ownership, ("ownership",), tuple(REQUIRED_TAMPER_CASES[52:56])),
    "lifecycle": _spec(_check_lifecycle, ("lifecycle_history",), tuple(REQUIRED_TAMPER_CASES[56:65])),
    "freeze": _spec(_check_freeze, ("system_freeze_positive",), tuple(REQUIRED_TAMPER_CASES[65:73])),
    "revision": _spec(_check_revision, ("revision_immutability",), tuple(REQUIRED_TAMPER_CASES[74:76])),
    "schema_integrity": _spec(_check_schema, ("physical_schema",), tuple(REQUIRED_TAMPER_CASES[76:83])),
    "cleanup": _spec(_check_cleanup, ("cleanup",), tuple(REQUIRED_TAMPER_CASES[83:85])),
    "security": _spec(_check_security, ("security_witness",), tuple(REQUIRED_TAMPER_CASES[85:88])),
    "system_authority_mismatch": _spec(_check_mismatch, ("system_authority_mismatch_negative",), ("resolved_class_mismatch",)),
    "different_field_applicability": _spec(_check_applicability, ("patch_lww_concurrency",), ("patch_sessions",)),
}
# Compatibility name for older integrity callers; this is the same
# executable registry, not a second metadata registry.
REQUIRED_ACCEPTANCE_REQUIREMENTS = REQUIREMENT_REGISTRY

# A compact, explicit path registry keeps every mutation semantic.  Values are
# selected by path shape, and are deliberately not accepted by the verifier.
_CASE_PATHS = {
    **{c: ("identity." + c.removeprefix("identity_"), "identity") for c in REQUIRED_TAMPER_CASES[:5]},
    "toolchain_python": ("toolchain.python", "toolchain"), "toolchain_uv": ("toolchain.uv", "toolchain"), "toolchain_lock_digest": ("toolchain.uv_lock_sha256", "toolchain"), "postgres_major": ("toolchain.postgres_major", "toolchain"),
    "migration_empty_head": ("migration_setup_identity.empty_to_head.after", "migration"), "migration_version_table": ("migration_setup_identity.version_table", "migration"), "migration_head": ("migration_setup_identity.head", "migration"),
}
for case, field in {"preparation_state": "state", "preparation_current_revision": "current_revision_id", "preparation_source_url": "source_url", "preparation_event_count": "lifecycle_event_count"}.items(): _CASE_PATHS[case] = (f"preparation.{field}", "preparation")
for case, path in {
    "snapshot_positive_delta":"positive_snapshot.post_revision_count", "snapshot_positive_current_revision":"positive_snapshot.current_revision_id", "snapshot_negative_revision":"negative_snapshot_matrix.0.post_revision_count", "snapshot_negative_current_revision":"negative_snapshot_matrix.0.current_revision_after", "snapshot_source_url":"positive_snapshot.source_url_after",
}.items(): _CASE_PATHS[case] = (path, "positive_snapshot" if "positive" in case or case == "snapshot_source_url" else "negative_snapshot_matrix")
for case in REQUIRED_TAMPER_CASES[21:32]: _CASE_PATHS[case] = ("patch_lww_concurrency." + {"patch_sessions":"sessions", "patch_barrier":"barrier", "patch_worker_count":"workers", "patch_committed_count":"committed_count", "patch_revision_count":"revision_count", "patch_duplicate_revision":"workers.0.revision_no", "patch_current_not_max":"final_revision_no", "patch_value_not_max":"final_value", "patch_final_revision":"final_revision_no", "patch_orphan_revision":"orphan_revision_count", "patch_orphan_override":"orphan_override_count"}[case], "patch_lww")
for case in REQUIRED_TAMPER_CASES[32:39]: _CASE_PATHS[case] = ("idempotency_concurrency." + {"idempotency_sessions":"sessions", "idempotency_barrier":"barrier", "idempotency_two_effects":"business_effect_count", "idempotency_two_terminals":"terminal_record_count", "idempotency_resource_ids":"outcomes.0.resource_id", "idempotency_missing_replay":"outcomes.1.repository_decision", "idempotency_fake_replay":"outcomes.1.repository_decision"}[case], "idempotency")
for case in REQUIRED_TAMPER_CASES[39:47]: _CASE_PATHS[case] = ("active_slot_concurrency." + {"active_sessions":"sessions", "active_barrier":"barrier", "active_worker_missing":"workers", "active_counts":"entitlement_observations.0.active_count", "active_both_allowed":"workers.0.decision", "active_denial_reason":"workers.1.reason", "active_final_count":"final_active_count", "active_event_count":"activation_event_count"}[case], "active_slot")
for case in REQUIRED_TAMPER_CASES[47:52]: _CASE_PATHS[case] = ("rollback." + {"rollback_post_counts":"post_rollback", "rollback_baseline_copy":"baseline", "rollback_retry_failure":"retry_business_effect_count", "rollback_duplicate_business":"retry_business_effect_count", "rollback_duplicate_idempotency":"retry_terminal_effect_count"}[case], "rollback")
for case in REQUIRED_TAMPER_CASES[52:56]: _CASE_PATHS[case] = ("ownership.foreign_read." + {"ownership_read_accept":"safe_reason", "ownership_state_change":"row_version_after", "ownership_unverified_accept":"revision_count_after", "ownership_accept":"audit_count_after"}[case], "ownership")
for case in REQUIRED_TAMPER_CASES[56:65]: _CASE_PATHS[case] = ("lifecycle_history." + {"lifecycle_active_count":"active_count_after_archive", "restore_entitlement_missing":"restore_entitlement", "restore_stale_entitlement":"restore_entitlement.fresh", "source_url_change":"source_url_after_restore", "revision_reference_change":"revision_id_after_restore", "permanent_delete_restorable":"permanent_delete_state", "restore_after_delete":"rejected_restore.reason", "event_sequence":"event_rows", "lifecycle_event_sequence":"event_rows"}[case], "lifecycle")
for case in REQUIRED_TAMPER_CASES[65:74]: _CASE_PATHS[case] = ("system_freeze_positive." + {"freeze_class":"resolved_class", "freeze_actor_account":"event.actor_account_id", "freeze_persisted_class":"persisted_system_actor_class", "freeze_causation":"event.causation_reference", "freeze_policy":"event.policy_source_reference", "freeze_event_count":"freeze_event_count", "freeze_state":"event.to_state", "auto_free":"auto_free_observations", "resolved_class_mismatch":"resolved_class"}[case], "freeze")
_CASE_PATHS.update({"old_revision": ("revision_immutability.revision_1_hash_after", "revision"), "current_revision_wrong": ("revision_immutability.current_revision_id", "revision"), "schema_revision_unique": ("physical_schema.constraints", "schema_integrity"), "schema_current_fk": ("physical_schema.constraints", "schema_integrity"), "schema_revision_positive": ("physical_schema.exact_constraint_definitions", "schema_integrity"), "schema_revision_pair": ("physical_schema.exact_constraint_definitions", "schema_integrity"), "schema_source_url": ("physical_schema.exact_constraint_definitions", "schema_integrity"), "schema_actor_causation": ("physical_schema.exact_constraint_definitions", "schema_integrity"), "metadata_parity": ("physical_schema.metadata_parity", "schema_integrity"), "cleanup_residue": ("cleanup.synthetic_post_counts.beacon_beacons", "cleanup"), "cleanup_preexisting": ("cleanup.preexisting_preserved", "cleanup"), "security_secret_count": ("security_witness.secret_scan_match_count", "security"), "security_raw_payload": ("security_witness.raw_provider_payload_forbidden_persisted_value_count", "security"), "security_production_data": ("security_witness.production_personal_data_marker_count", "security"), "resolved_class_mismatch": ("system_authority_mismatch_negative.resolved_class", "system_authority_mismatch")})

_REQUIREMENT_BY_CASE = {case: requirement for requirement, spec in REQUIREMENT_REGISTRY.items() for case in spec.tamper_cases}
for case in REQUIRED_TAMPER_CASES:
    _REQUIREMENT_BY_CASE.setdefault(case, _CASE_PATHS.get(case, ("identity", "identity"))[1])


def _make_mutation(case: str, path: str, requirement: str) -> Callable[[dict[str, Any]], None]:
    def mutate(item: dict[str, Any]) -> None:
        if case in {"patch_worker_count", "active_worker_missing"}:
            _path(item, path).pop()
        elif case in {"event_sequence", "lifecycle_event_sequence"}:
            rows = _path(item, path)
            if case == "event_sequence": rows.reverse()
            else: rows[0]["to_state"] = "BROKEN"
        elif case in {"rollback_baseline_copy"}:
            _set(item, path + ".beacon_beacons", _path(item, path + ".beacon_beacons") + 1)
        elif case == "idempotency_resource_ids": _toggle(item, path)
        elif case == "schema_revision_unique":
            next(row for row in _path(item, "physical_schema.constraints") if row["type"] == "u" and row["columns"] == ["revision_id"])["definition"] = "UNIQUE (wrong_column)"
        elif case == "schema_current_fk":
            next(row for row in _path(item, "physical_schema.constraints") if row["type"] == "f" and row["columns"] == ["current_revision_id"])["definition"] = "FOREIGN KEY (current_revision_id) REFERENCES wrong(id)"
        elif case in {"schema_revision_positive", "schema_source_url", "schema_actor_causation"}:
            marker = {"schema_revision_positive": "current_revision_no", "schema_source_url": "source_url", "schema_actor_causation": "actor_account_id"}[case]
            index = next(i for i, value in enumerate(_path(item, "physical_schema.exact_constraint_definitions")) if marker in value)
            _path(item, "physical_schema.exact_constraint_definitions")[index] = "CHECK (TRUE)"
        elif case == "schema_revision_pair":
            index = next(i for i, value in enumerate(_path(item, "physical_schema.exact_constraint_definitions")) if "current_revision_no" in value and "current_revision_id" in value)
            _path(item, "physical_schema.exact_constraint_definitions")[index] = "CHECK (current_revision_no IS NOT NULL)"
        elif case == "identity_schema_version": _set(item, path, "rf13-postgres-acceptance-invalid")
        else: _toggle(item, path)
    return mutate


TAMPER_MUTATIONS: dict[str, TamperMutation] = {
    case: TamperMutation((requirement,), (path,), _make_mutation(case, path, requirement))
    for case, (path, requirement) in _CASE_PATHS.items()
}
for _case, _requirements in {
    "patch_sessions": ("patch_lww", "different_field_applicability"),
    "schema_revision_unique": ("physical_schema", "schema_integrity"),
    "schema_current_fk": ("physical_schema", "schema_integrity"),
}.items():
    _mutation = TAMPER_MUTATIONS[_case]
    TAMPER_MUTATIONS[_case] = TamperMutation(_requirements, _mutation.changed_paths, _mutation.mutate)

def _git(root: Path, *args: str) -> str:
    return subprocess.check_output(("git", *args), cwd=root, text=True).strip()


def verify(root: Path, evidence: Path, candidate_sha: str) -> None:
    item = json.loads(evidence.read_text(encoding="utf-8"))
    actual_sha, actual_tree, parent = _git(root, "rev-parse", "HEAD"), _git(root, "rev-parse", "HEAD^{tree}"), _git(root, "rev-parse", "HEAD^")
    item["_expected_candidate_sha"], item["_actual_candidate_tree"], item["_root"] = candidate_sha, actual_tree, str(root)
    _require(actual_sha == candidate_sha and parent == EXPECTED_BASE, "candidate identity")
    _require(item.get("schema_version") == SCHEMA_VERSION, "schema v5 required")
    _require(set(item) - {"_expected_candidate_sha", "_actual_candidate_tree", "_root"} >= set(REQUIRED_SECTIONS), "required section envelope")
    _require(set(REQUIREMENT_REGISTRY) == {"identity", "toolchain", "migration", "physical_schema", "preparation", "positive_snapshot", "negative_snapshot_matrix", "patch_lww", "idempotency", "active_slot", "rollback", "ownership", "lifecycle", "freeze", "revision", "schema_integrity", "cleanup", "security", "system_authority_mismatch", "different_field_applicability"}, "registry incomplete")
    for requirement, spec in REQUIREMENT_REGISTRY.items():
        for path in spec.raw_paths: _path(item, path)
        spec.checker(item)
    print(MARKER)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path); parser.add_argument("evidence", type=Path); parser.add_argument("candidate_sha")
    args = parser.parse_args(); verify(args.root, args.evidence, args.candidate_sha)
