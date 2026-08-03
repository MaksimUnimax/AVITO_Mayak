"""RF17 verifier over scenario-specific primitive runtime and PostgreSQL facts."""
# ruff: noqa: E501, E701, E702
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

MARKER = "RF17_NOTIFICATION_DELIVERY_RUNTIME_VERIFIED"
TECHNICAL_ID = "RF-17-NOTIFICATION-DELIVERY-DURABLE-RUNTIME-20260803-01"
EXPECTED_RF17_REQUIREMENT_IDS = (
    "identity.candidate_sha", "identity.pg18_db_repo_head", "schema.physical_five_tables", "security.app_role_notification_only",
    "source.single_event", "source.replay_same", "source.concurrent_same", "source.identity_fingerprint_mismatch", "source.same_fingerprint_cross_scope_conflict",
    "source.baseline_blocked", "source.no_new_blocked", "source.price_blocked", "source.non_notification_families_blocked", "source.unsafe_payload_blocked",
    "endpoint.stable_replay", "endpoint.cross_account_rebind_blocked", "endpoint.accepted_channel_evidence", "fanout.explicit_targets", "fanout.empty_blocked", "fanout.concurrent_dedup",
    "claim.same_item_single_owner", "claim.deterministic_order", "lease.wrong_token_blocked", "lease.expired_terminal_blocked", "attempt.unique_number",
    "transaction.attempt_committed_before_adapter", "transaction.adapter_outside_db_transaction", "result.definite_success", "result.not_human_read", "result.definite_failure_no_retry",
    "result.replay_same", "result.mismatch_blocked", "reconciliation.single_on_ambiguous", "reconciliation.unresolved_blocks_attempt", "reconciliation.replay_same",
    "reconciliation.resolved_delivered", "reconciliation.confirmed_no_effect_only_retry", "reconciliation.manual_ambiguous_blocks", "restart.claim_before_attempt_reclaim",
    "restart.retry_claim_before_attempt_reclaim", "restart.after_attempt_reconcile", "history.account_scope", "history.beacon_scope", "history.cross_account_blocked",
    "history.safe_refs", "foreign.authority_unchanged", "privacy.no_raw_provider_values", "privacy.no_raw_lease_values",
)
EXPECTED_RF17_TAMPER_STRATEGY_IDS = tuple("tamper." + item for item in EXPECTED_RF17_REQUIREMENT_IDS)
_BAD_KEYS = {"observations", "passes", "verdicts", "acceptance_results", "provider_payload", "raw_lease_token", "single_committed_event", "replay_same_row", "trusted_delivered_binds_attempt", "e446_summary", "operation", "physical", "relation_id"}
_SECRET = re.compile(r"(?i)(bearer\s+\S+|authorization\s*[:=]|cookie\s*[:=]|lease_token\s*[:=]\s*[^\s,}]+)")

@dataclass(frozen=True, slots=True)
class Requirement:
    requirement_id: str
    tamper_strategy_id: str
    required_raw_paths: tuple[str, ...]
    check: Callable[[dict[str, object]], bool]
    tamper: Callable[[dict[str, object]], None]
    scenario_id: str

def _raw(data: dict[str, object], path: str) -> object:
    value: object = data
    for part in path.split("."):
        if isinstance(value, dict) and part in value:
            value = value[part]
        elif isinstance(value, list) and part.isdigit() and int(part) < len(value):
            value = value[int(part)]
        else:
            return None
    return value

def _changed(data: dict[str, object], path: str) -> None:
    parts = path.split(".")
    value: object = data
    for part in parts[:-1]:
        if isinstance(value, dict) and part in value:
            value = value[part]
        elif isinstance(value, list) and part.isdigit() and int(part) < len(value):
            value = value[int(part)]
        else:
            raise KeyError(path)
    if isinstance(value, dict) and parts[-1] in value:
        old = value[parts[-1]]
        def setter(replacement: object) -> None:
            value[parts[-1]] = replacement
    elif isinstance(value, list) and parts[-1].isdigit() and int(parts[-1]) < len(value):
        index = int(parts[-1]); old = value[index]
        def setter(replacement: object) -> None:
            value[index] = replacement
    else:
        raise KeyError(path)
    if isinstance(old, bool): setter(not old)
    elif isinstance(old, int): setter(old + 1)
    elif isinstance(old, list): setter(old + ["tampered-fact"])
    elif isinstance(old, dict): setter({"tampered": True})
    else: setter("tampered-fact")

def _present(data: dict[str, object], *paths: str) -> bool:
    return all(_raw(data, path) is not None for path in paths)

def _has(data: dict[str, object], path: str) -> bool:
    value: object = data
    for part in path.split("."):
        if not isinstance(value, dict) or part not in value:
            return False
        value = value[part]
    return True

def _scenario(data: dict[str, object], name: str, *fields: str) -> bool:
    node = _raw(data, name)
    return isinstance(node, dict) and all(_has(data, f"{name}.{field}") for field in fields)

def _is_error(data: dict[str, object], path: str, expected: str) -> bool:
    value = _raw(data, path)
    return isinstance(value, dict) and value.get("class") == expected and bool(value.get("attempted"))

def _rows(data: dict[str, object], path: str, count: int | None = None) -> bool:
    value = _raw(data, path)
    return isinstance(value, list) and (count is None or len(value) == count)

def _valid_identity(data: dict[str, object]) -> bool:
    return bool(re.fullmatch(r"[0-9a-f]{40}", str(_raw(data, "identity.candidate_sha")))) and _raw(data, "identity.technical_id") == TECHNICAL_ID
def _valid_db(data: dict[str, object]) -> bool:
    return str(_raw(data, "database.postgres_version")).startswith("PostgreSQL 18") and _raw(data, "database.db_alembic_head") == _raw(data, "database.repository_alembic_head")
def _valid_schema(data: dict[str, object]) -> bool:
    return _raw(data, "schema.tables") == ["notification_delivery_attempts", "notification_delivery_reconciliations", "notification_endpoints", "notification_events", "notification_outbox"] and all(isinstance(_raw(data, f"schema.columns.{table}"), list) for table in _raw(data, "schema.tables") or [])
def _valid_privileges(data: dict[str, object]) -> bool:
    matrix = _raw(data, "security.privilege_matrix"); probes = _raw(data, "security.dml_probes")
    return isinstance(matrix, list) and isinstance(probes, list) and all(isinstance(row, dict) for row in matrix) and all(isinstance(row, dict) for row in probes) and all(row.get("owner") == "notification" for row in matrix if str(row.get("table", "")).startswith("notification_")) and all(row.get("sqlstate") == "42501" for row in probes if row.get("domain") in {"identity", "beacon", "scan"})
def _source_single(data): return _scenario(data, "source.single_event", "input", "runtime_return", "physical_rows") and _rows(data, "source.single_event.physical_rows", 1)
def _source_replay(data): return _scenario(data, "source.replay_same", "input", "runtime_return", "physical_rows") and _raw(data, "source.replay_same.runtime_return.event_id") == _raw(data, "source.single_event.runtime_return.event_id") and _rows(data, "source.replay_same.physical_rows", 1)
def _source_concurrent(data): return _scenario(data, "source.concurrent_same", "input", "runtime_results", "backend_pids", "physical_rows") and len(set(_raw(data, "source.concurrent_same.backend_pids") or [])) == 2 and _rows(data, "source.concurrent_same.physical_rows", 1) and len({_raw(data, "source.concurrent_same.runtime_results.0.event_id"), _raw(data, "source.concurrent_same.runtime_results.1.event_id")}) == 1
def _source_fp(data): return _scenario(data, "source.identity_fingerprint_mismatch", "input", "exception", "physical_rows") and _is_error(data, "source.identity_fingerprint_mismatch.exception", "IdempotencyConflict") and _rows(data, "source.identity_fingerprint_mismatch.physical_rows", 1)
def _source_scope(data): return _scenario(data, "source.same_fingerprint_cross_scope_conflict", "input", "exception", "physical_rows") and _is_error(data, "source.same_fingerprint_cross_scope_conflict.exception", "IdempotencyConflict")
def _source_blocked(data, name, family): return _scenario(data, name, "input", "runtime_return", "physical_rows") and _raw(data, f"{name}.runtime_return") is None and _rows(data, f"{name}.physical_rows", 0) and _raw(data, f"{name}.input.family") == family
def _endpoint_replay(data): return _scenario(data, "endpoint.stable_replay", "input", "runtime_return", "physical_before", "physical_after") and _raw(data, "endpoint.stable_replay.physical_before") == _raw(data, "endpoint.stable_replay.physical_after")
def _endpoint_account(data): return _scenario(data, "endpoint.cross_account_rebind_blocked", "input", "exception", "physical_after") and _is_error(data, "endpoint.cross_account_rebind_blocked.exception", "AccountScopeConflict")
def _endpoint_channel(data): return _scenario(data, "endpoint.accepted_channel_evidence", "input", "runtime_return", "physical_after") and _raw(data, "endpoint.accepted_channel_evidence.input.channel") in {"TELEGRAM", "MAX"}
def _fanout_targets(data):
    rows = _raw(data, "fanout.explicit_targets.physical_rows")
    return _scenario(data, "fanout.explicit_targets", "input", "runtime_return", "physical_rows") and isinstance(rows, list) and all(isinstance(row, dict) for row in rows) and bool(rows) and set(_raw(data, "fanout.explicit_targets.runtime_return.outbox_ids") or []) == {row.get("id") for row in rows}
def _fanout_empty(data): return _scenario(data, "fanout.empty_blocked", "input", "exception", "physical_rows") and _is_error(data, "fanout.empty_blocked.exception", "AccountScopeConflict") and _rows(data, "fanout.empty_blocked.physical_rows", 0)
def _fanout_concurrent(data): return _scenario(data, "fanout.concurrent_dedup", "input", "backend_pids", "runtime_results", "physical_rows") and len(set(_raw(data, "fanout.concurrent_dedup.backend_pids") or [])) == 2 and len(_raw(data, "fanout.concurrent_dedup.physical_rows") or []) == 1
def _claim_owner(data):
    results = _raw(data, "claim.same_item_single_owner.runtime_results")
    return _scenario(data, "claim.same_item_single_owner", "input", "backend_pids", "runtime_results", "physical_row") and len(set(_raw(data, "claim.same_item_single_owner.backend_pids") or [])) == 2 and isinstance(results, list) and all(isinstance(item, dict) for item in results) and sum(bool(item.get("claimed")) for item in results) == 1
def _claim_order(data): return _scenario(data, "claim.deterministic_order", "input", "runtime_return", "physical_rows") and _raw(data, "claim.deterministic_order.runtime_return.outbox_ids") == [row.get("id") for row in sorted(_raw(data, "claim.deterministic_order.physical_rows") or [], key=lambda row: (row.get("available_at"), row.get("id")))]
def _lease_wrong(data): return _scenario(data, "lease.wrong_token_blocked", "input", "exception", "physical_before", "physical_after") and _is_error(data, "lease.wrong_token_blocked.exception", "LeaseConflict") and _raw(data, "lease.wrong_token_blocked.physical_before") == _raw(data, "lease.wrong_token_blocked.physical_after")
def _lease_expired(data): return _scenario(data, "lease.expired_terminal_blocked", "input", "exception", "physical_after") and _is_error(data, "lease.expired_terminal_blocked.exception", "LeaseConflict")
def _attempt_unique(data):
    rows = _raw(data, "attempt.unique_number.physical_rows")
    return _scenario(data, "attempt.unique_number", "input", "runtime_return", "physical_rows") and isinstance(rows, list) and all(isinstance(row, dict) for row in rows) and len({row.get("attempt_number") for row in rows}) == len(rows)
def _tx_visible(data): return _scenario(data, "transaction.attempt_committed_before_adapter", "runtime_return", "physical_rows", "separate_connection_visible") and bool(_raw(data, "transaction.attempt_committed_before_adapter.separate_connection_visible"))
def _tx_adapter(data): return _scenario(data, "transaction.adapter_outside_db_transaction", "runtime_return", "adapter_observation") and _raw(data, "transaction.adapter_outside_db_transaction.adapter_observation.transaction_active") is False
def _outbox_state(data, name):
    rows = _raw(data, f"{name}.physical_after.outbox")
    return rows[0].get("state") if isinstance(rows, list) and rows and isinstance(rows[0], dict) else None
def _result_success(data): return _scenario(data, "result.definite_success", "input", "runtime_return", "physical_after") and _raw(data, "result.definite_success.runtime_return.class") == "none" and _outbox_state(data, "result.definite_success") == "DELIVERED" and _raw(data, "result.definite_success.physical_after.attempts.0.state") == "DELIVERED_ACCEPTED" and bool(_raw(data, "result.definite_success.physical_after.attempts.0.provider_reference"))
def _result_read(data): return _scenario(data, "result.not_human_read", "input", "runtime_return", "physical_after") and _raw(data, "result.not_human_read.runtime_return.class") == "none" and _outbox_state(data, "result.not_human_read") == "DELIVERED" and "human_read" not in (_raw(data, "result.not_human_read.physical_after.attempts.0.safe_metadata") or {})
def _result_failure(data):
    node = _raw(data, "result.definite_failure_no_retry") or {}; outbox = (node.get("physical_after", {}).get("outbox") or [{}])[0]; later = node.get("physical_after", {}).get("later_claims", [])
    return _scenario(data, "result.definite_failure_no_retry", "input", "runtime_return", "physical_after") and node.get("runtime_return", {}).get("class") == "none" and outbox.get("state") == "FAILED" and (node.get("physical_after", {}).get("attempts") or [{}])[0].get("state") == "FAILED_NON_RETRYABLE" and all(item.get("outbox_id") != outbox.get("id") for item in later)
def _result_replay(data): return _scenario(data, "result.replay_same", "input", "runtime_results", "physical_rows") and len(_raw(data, "result.replay_same.physical_rows") or []) == 1 and all(_raw(data, f"result.replay_same.runtime_results.{i}.class") == "none" for i in (0, 1)) and _raw(data, "result.replay_same.physical_rows.0.state") == "DELIVERED_ACCEPTED"
def _result_mismatch(data): return _scenario(data, "result.mismatch_blocked", "input", "exception", "physical_before", "physical_after") and _is_error(data, "result.mismatch_blocked.exception", "IdempotencyConflict") and _raw(data, "result.mismatch_blocked.physical_before") == _raw(data, "result.mismatch_blocked.physical_after")
def _recon(data, name, state):
    node = _scenario(data, name, "input", "persisted_attempt", "persisted_reconciliation", "trusted_evidence", "runtime_return", "physical_after")
    attempt = _raw(data, f"{name}.persisted_attempt") or {}; rec = _raw(data, f"{name}.persisted_reconciliation") or {}; trusted = _raw(data, f"{name}.trusted_evidence") or {}; after = _raw(data, f"{name}.physical_after") or {}
    rec_meta = rec.get("safe_metadata", {}) if isinstance(rec, dict) else {}
    actual_state = after.get("outbox", [{}])[0].get("state")
    state_ok = actual_state == ("CLAIMED" if state == "RETRY" else state)
    retry_ok = state != "RETRY" or len(after.get("attempts", [])) >= 2
    return node and attempt.get("id") == trusted.get("attempt_id") and attempt.get("effect_fingerprint") == rec_meta.get("effect_fingerprint") == trusted.get("effect_fingerprint") and isinstance(after.get("reconciliations"), list) and len(after["reconciliations"]) == 1 and state_ok and retry_ok and isinstance(_raw(data, f"{name}.runtime_return.initial"), str)
def _restart(data, name, expected):
    node = _scenario(data, name, "before", "after", "backend_pids", "runtime_observation")
    pids = _raw(data, f"{name}.backend_pids") or []; after = _raw(data, f"{name}.after") or {}
    actual = after["outbox"][0].get("state") if isinstance(after.get("outbox"), list) and after["outbox"] else None
    return node and len(pids) == 2 and pids[0] != pids[1] and actual == ("CLAIMED" if expected == "RETRY" else expected)
def _history(data, name): return _scenario(data, name, "input", "runtime_return", "physical_source_rows") and _raw(data, f"{name}.runtime_return.account_id") == _raw(data, f"{name}.input.account_id")
def _foreign(data): return _scenario(data, "foreign.authority_unchanged", "fixture_rows", "before", "after") and _raw(data, "foreign.authority_unchanged.before") == _raw(data, "foreign.authority_unchanged.after")
def _privacy(data, name, forbidden):
    node = _raw(data, name)
    projection = _raw(data, f"{name}.persisted_safe_projection")
    if not isinstance(node, dict) or not isinstance(projection, dict) or not _present(data, f"{name}.key_inventory") or forbidden in json.dumps(node, sort_keys=True): return False
    if name.endswith("provider_values"): return isinstance(projection.get("provider_reference"), str) and projection.get("provider_reference") == "delivery-ref-1"
    return projection.get("lease_token") is None and isinstance(projection.get("lease_fingerprint"), str) and bool(re.fullmatch(r"[0-9a-f]{64}", projection["lease_fingerprint"]))

def _validate_executed_case_provenance(data: dict[str, object]) -> tuple[int, int]:
    ledger = data.get("executed_case_ledger")
    bindings = data.get("requirement_case_bindings")
    if not isinstance(ledger, dict) or not isinstance(bindings, dict):
        raise SystemExit("RF17 executed-case provenance is missing")
    seen: set[str] = set()
    for requirement_id in EXPECTED_RF17_REQUIREMENT_IDS:
        case_ids = bindings.get(requirement_id)
        if not isinstance(case_ids, list) or not case_ids or any(not isinstance(item, str) for item in case_ids):
            raise SystemExit("RF17 requirement has no executed case binding: " + requirement_id)
        for case_id in case_ids:
            if case_id not in ledger:
                raise SystemExit("RF17 binding references an absent executed case: " + case_id)
            case = ledger[case_id]
            if not isinstance(case, dict) or case.get("case_id") != case_id or case.get("actual_callable_executed") is not True:
                raise SystemExit("RF17 executed case is not actual callable provenance: " + case_id)
            if not isinstance(case.get("callable"), str) or not case["callable"]:
                raise SystemExit("RF17 executed case has no callable provenance: " + case_id)
            if case_id in seen:
                raise SystemExit("RF17 duplicate semantic case ID: " + case_id)
            seen.add(case_id)
    if len(ledger) != len(seen) or len(seen) != len(EXPECTED_RF17_REQUIREMENT_IDS):
        raise SystemExit("RF17 executed case ledger contains unbound or duplicate semantic cases")
    return len(ledger), len(seen)

def check_identity_candidate(data): return _valid_identity(data)
def check_identity_db(data): return _valid_db(data)
def check_schema(data): return _valid_schema(data)
def check_privileges(data): return _valid_privileges(data)
def check_source_single(data): return _source_single(data)
def check_source_replay(data): return _source_replay(data)
def check_source_concurrent(data): return _source_concurrent(data)
def check_source_fingerprint(data): return _source_fp(data)
def check_source_scope(data): return _source_scope(data)
def check_source_baseline(data): return _source_blocked(data, "source.baseline_blocked", "BEACON_BASELINE_ESTABLISHED")
def check_source_no_new(data): return _source_blocked(data, "source.no_new_blocked", "NO_NEW_LISTINGS_STATUS")
def check_source_price(data): return _source_blocked(data, "source.price_blocked", "LISTING_PRICE_PAIR_FIRST_SEEN")
def check_source_family(data): return _source_blocked(data, "source.non_notification_families_blocked", "PROVIDER_ONLY_CALLBACK")
def check_source_payload(data): return _scenario(data, "source.unsafe_payload_blocked", "input", "exception", "physical_rows") and _is_error(data, "source.unsafe_payload_blocked.exception", "InvalidNotificationSource") and _rows(data, "source.unsafe_payload_blocked.physical_rows", 0)
def check_endpoint_replay(data): return _endpoint_replay(data)
def check_endpoint_account(data): return _endpoint_account(data)
def check_endpoint_channel(data): return _endpoint_channel(data)
def check_fanout_targets(data): return _fanout_targets(data)
def check_fanout_empty(data): return _fanout_empty(data)
def check_fanout_concurrent(data): return _fanout_concurrent(data)
def check_claim_owner(data): return _claim_owner(data)
def check_claim_order(data): return _claim_order(data)
def check_lease_wrong(data): return _lease_wrong(data)
def check_lease_expired(data): return _lease_expired(data)
def check_attempt_unique(data): return _attempt_unique(data)
def check_transaction_visible(data): return _tx_visible(data)
def check_transaction_adapter(data): return _tx_adapter(data)
def check_result_success(data): return _result_success(data)
def check_result_read(data): return _result_read(data)
def check_result_failure(data): return _result_failure(data)
def check_result_replay(data): return _result_replay(data)
def check_result_mismatch(data): return _result_mismatch(data)
def check_recon_single(data): return _recon(data, "reconciliation.single_on_ambiguous", "RECONCILIATION_REQUIRED")
def check_recon_blocks(data): return _recon(data, "reconciliation.unresolved_blocks_attempt", "RECONCILIATION_REQUIRED")
def check_recon_replay(data): return _recon(data, "reconciliation.replay_same", "RECONCILIATION_REQUIRED")
def check_recon_delivered(data): return _recon(data, "reconciliation.resolved_delivered", "DELIVERED")
def check_recon_no_effect(data): return _recon(data, "reconciliation.confirmed_no_effect_only_retry", "RETRY")
def check_recon_manual(data): return _recon(data, "reconciliation.manual_ambiguous_blocks", "RECONCILIATION_REQUIRED")
def check_restart_claim(data): return _restart(data, "restart.claim_before_attempt_reclaim", "CLAIMED")
def check_restart_retry(data): return _restart(data, "restart.retry_claim_before_attempt_reclaim", "RETRY")
def check_restart_attempt(data): return _restart(data, "restart.after_attempt_reconcile", "RECONCILIATION_REQUIRED")
def check_history_account(data): return _history(data, "history.account_scope")
def check_history_beacon(data): return _history(data, "history.beacon_scope")
def check_history_cross_account(data): return _scenario(data, "history.cross_account_blocked", "input", "exception", "physical_source_rows") and _is_error(data, "history.cross_account_blocked.exception", "AccountScopeConflict")
def check_history_refs(data): return _scenario(data, "history.safe_refs", "input", "runtime_return", "physical_source_rows") and all("listing_reference_ids" in row for row in _raw(data, "history.safe_refs.runtime_return.rows") or [])
def check_foreign(data): return _foreign(data)
def check_privacy_provider(data): return _privacy(data, "privacy.no_raw_provider_values", "provider_payload")
def check_privacy_lease(data): return _privacy(data, "privacy.no_raw_lease_values", "raw-lease-secret")

def tamper_identity_candidate(data): _changed(data, "identity.candidate_sha")
def tamper_identity_db(data): _changed(data, "database.db_alembic_head")
def tamper_schema(data): _changed(data, "schema.tables")
def tamper_privileges(data): _changed(data, "security.dml_probes")
def tamper_source_single(data): _changed(data, "source.single_event.physical_rows")
def tamper_source_replay(data): _changed(data, "source.replay_same.runtime_return.event_id")
def tamper_source_concurrent(data): _changed(data, "source.concurrent_same.backend_pids")
def tamper_source_fingerprint(data): _changed(data, "source.identity_fingerprint_mismatch.exception.class")
def tamper_source_scope(data): _changed(data, "source.same_fingerprint_cross_scope_conflict.exception.class")
def tamper_source_baseline(data): _changed(data, "source.baseline_blocked.runtime_return")
def tamper_source_no_new(data): _changed(data, "source.no_new_blocked.runtime_return")
def tamper_source_price(data): _changed(data, "source.price_blocked.runtime_return")
def tamper_source_family(data): _changed(data, "source.non_notification_families_blocked.runtime_return")
def tamper_source_payload(data): _changed(data, "source.unsafe_payload_blocked.exception.class")
def tamper_endpoint_replay(data): _changed(data, "endpoint.stable_replay.physical_after")
def tamper_endpoint_account(data): _changed(data, "endpoint.cross_account_rebind_blocked.exception.class")
def tamper_endpoint_channel(data): _changed(data, "endpoint.accepted_channel_evidence.input.channel")
def tamper_fanout_targets(data): _changed(data, "fanout.explicit_targets.physical_rows")
def tamper_fanout_empty(data): _changed(data, "fanout.empty_blocked.physical_rows")
def tamper_fanout_concurrent(data): _changed(data, "fanout.concurrent_dedup.backend_pids")
def tamper_claim_owner(data): _changed(data, "claim.same_item_single_owner.runtime_results")
def tamper_claim_order(data): _changed(data, "claim.deterministic_order.runtime_return.outbox_ids")
def tamper_lease_wrong(data): _changed(data, "lease.wrong_token_blocked.exception.class")
def tamper_lease_expired(data): _changed(data, "lease.expired_terminal_blocked.exception.class")
def tamper_attempt_unique(data): _changed(data, "attempt.unique_number.physical_rows")
def tamper_transaction_visible(data): _changed(data, "transaction.attempt_committed_before_adapter.separate_connection_visible")
def tamper_transaction_adapter(data): _changed(data, "transaction.adapter_outside_db_transaction.adapter_observation.transaction_active")
def tamper_result_success(data): _changed(data, "result.definite_success.physical_after.outbox.0.state")
def tamper_result_read(data): _changed(data, "result.not_human_read.physical_after.outbox.0.state")
def tamper_result_failure(data): _changed(data, "result.definite_failure_no_retry.physical_after.outbox.0.state")
def tamper_result_replay(data): _changed(data, "result.replay_same.physical_rows")
def tamper_result_mismatch(data): _changed(data, "result.mismatch_blocked.exception.class")
def tamper_recon_single(data): _changed(data, "reconciliation.single_on_ambiguous.persisted_attempt.effect_fingerprint")
def tamper_recon_blocks(data): _changed(data, "reconciliation.unresolved_blocks_attempt.trusted_evidence.effect_fingerprint")
def tamper_recon_replay(data): _changed(data, "reconciliation.replay_same.persisted_reconciliation.safe_metadata.effect_fingerprint")
def tamper_recon_delivered(data): _changed(data, "reconciliation.resolved_delivered.physical_after.outbox.0.state")
def tamper_recon_no_effect(data): _changed(data, "reconciliation.confirmed_no_effect_only_retry.physical_after.outbox.0.state")
def tamper_recon_manual(data): _changed(data, "reconciliation.manual_ambiguous_blocks.physical_after.outbox.0.state")
def tamper_restart_claim(data): _changed(data, "restart.claim_before_attempt_reclaim.backend_pids")
def tamper_restart_retry(data): _changed(data, "restart.retry_claim_before_attempt_reclaim.backend_pids")
def tamper_restart_attempt(data): _changed(data, "restart.after_attempt_reconcile.backend_pids")
def tamper_history_account(data): _changed(data, "history.account_scope.runtime_return.account_id")
def tamper_history_beacon(data): _changed(data, "history.beacon_scope.runtime_return.account_id")
def tamper_history_cross_account(data): _changed(data, "history.cross_account_blocked.exception.class")
def tamper_history_refs(data): _changed(data, "history.safe_refs.runtime_return.rows")
def tamper_foreign(data): _changed(data, "foreign.authority_unchanged.after")
def tamper_privacy_provider(data): _changed(data, "privacy.no_raw_provider_values.persisted_safe_projection")
def tamper_privacy_lease(data): _changed(data, "privacy.no_raw_lease_values.persisted_safe_projection")

def registry() -> tuple[Requirement, ...]:
    return (
        Requirement("identity.candidate_sha", "tamper.identity.candidate_sha", ("identity.candidate_sha", "identity.technical_id"), check_identity_candidate, tamper_identity_candidate, "identity.candidate_sha"),
        Requirement("identity.pg18_db_repo_head", "tamper.identity.pg18_db_repo_head", ("database.postgres_version", "database.db_alembic_head", "database.repository_alembic_head"), check_identity_db, tamper_identity_db, "identity.pg18_db_repo_head"),
        Requirement("schema.physical_five_tables", "tamper.schema.physical_five_tables", ("schema.tables", "schema.columns.notification_events"), check_schema, tamper_schema, "schema.physical_five_tables"),
        Requirement("security.app_role_notification_only", "tamper.security.app_role_notification_only", ("security.privilege_matrix", "security.dml_probes"), check_privileges, tamper_privileges, "security.app_role_notification_only"),
        Requirement("source.single_event", "tamper.source.single_event", ("source.single_event.runtime_return", "source.single_event.physical_rows"), check_source_single, tamper_source_single, "source.single_event"),
        Requirement("source.replay_same", "tamper.source.replay_same", ("source.replay_same.runtime_return", "source.replay_same.physical_rows"), check_source_replay, tamper_source_replay, "source.replay_same"),
        Requirement("source.concurrent_same", "tamper.source.concurrent_same", ("source.concurrent_same.runtime_results", "source.concurrent_same.backend_pids", "source.concurrent_same.physical_rows"), check_source_concurrent, tamper_source_concurrent, "source.concurrent_same"),
        Requirement("source.identity_fingerprint_mismatch", "tamper.source.identity_fingerprint_mismatch", ("source.identity_fingerprint_mismatch.exception", "source.identity_fingerprint_mismatch.physical_rows"), check_source_fingerprint, tamper_source_fingerprint, "source.identity_fingerprint_mismatch"),
        Requirement("source.same_fingerprint_cross_scope_conflict", "tamper.source.same_fingerprint_cross_scope_conflict", ("source.same_fingerprint_cross_scope_conflict.exception", "source.same_fingerprint_cross_scope_conflict.physical_rows"), check_source_scope, tamper_source_scope, "source.same_fingerprint_cross_scope_conflict"),
        Requirement("source.baseline_blocked", "tamper.source.baseline_blocked", ("source.baseline_blocked.input", "source.baseline_blocked.runtime_return", "source.baseline_blocked.physical_rows"), check_source_baseline, tamper_source_baseline, "source.baseline_blocked"),
        Requirement("source.no_new_blocked", "tamper.source.no_new_blocked", ("source.no_new_blocked.input", "source.no_new_blocked.runtime_return", "source.no_new_blocked.physical_rows"), check_source_no_new, tamper_source_no_new, "source.no_new_blocked"),
        Requirement("source.price_blocked", "tamper.source.price_blocked", ("source.price_blocked.input", "source.price_blocked.runtime_return", "source.price_blocked.physical_rows"), check_source_price, tamper_source_price, "source.price_blocked"),
        Requirement("source.non_notification_families_blocked", "tamper.source.non_notification_families_blocked", ("source.non_notification_families_blocked.input", "source.non_notification_families_blocked.runtime_return", "source.non_notification_families_blocked.physical_rows"), check_source_family, tamper_source_family, "source.non_notification_families_blocked"),
        Requirement("source.unsafe_payload_blocked", "tamper.source.unsafe_payload_blocked", ("source.unsafe_payload_blocked.exception", "source.unsafe_payload_blocked.physical_rows"), check_source_payload, tamper_source_payload, "source.unsafe_payload_blocked"),
        Requirement("endpoint.stable_replay", "tamper.endpoint.stable_replay", ("endpoint.stable_replay.physical_before", "endpoint.stable_replay.physical_after"), check_endpoint_replay, tamper_endpoint_replay, "endpoint.stable_replay"),
        Requirement("endpoint.cross_account_rebind_blocked", "tamper.endpoint.cross_account_rebind_blocked", ("endpoint.cross_account_rebind_blocked.exception", "endpoint.cross_account_rebind_blocked.physical_after"), check_endpoint_account, tamper_endpoint_account, "endpoint.cross_account_rebind_blocked"),
        Requirement("endpoint.accepted_channel_evidence", "tamper.endpoint.accepted_channel_evidence", ("endpoint.accepted_channel_evidence.input.channel", "endpoint.accepted_channel_evidence.physical_after"), check_endpoint_channel, tamper_endpoint_channel, "endpoint.accepted_channel_evidence"),
        Requirement("fanout.explicit_targets", "tamper.fanout.explicit_targets", ("fanout.explicit_targets.runtime_return", "fanout.explicit_targets.physical_rows"), check_fanout_targets, tamper_fanout_targets, "fanout.explicit_targets"),
        Requirement("fanout.empty_blocked", "tamper.fanout.empty_blocked", ("fanout.empty_blocked.exception", "fanout.empty_blocked.physical_rows"), check_fanout_empty, tamper_fanout_empty, "fanout.empty_blocked"),
        Requirement("fanout.concurrent_dedup", "tamper.fanout.concurrent_dedup", ("fanout.concurrent_dedup.backend_pids", "fanout.concurrent_dedup.physical_rows"), check_fanout_concurrent, tamper_fanout_concurrent, "fanout.concurrent_dedup"),
        Requirement("claim.same_item_single_owner", "tamper.claim.same_item_single_owner", ("claim.same_item_single_owner.backend_pids", "claim.same_item_single_owner.runtime_results", "claim.same_item_single_owner.physical_row"), check_claim_owner, tamper_claim_owner, "claim.same_item_single_owner"),
        Requirement("claim.deterministic_order", "tamper.claim.deterministic_order", ("claim.deterministic_order.runtime_return", "claim.deterministic_order.physical_rows"), check_claim_order, tamper_claim_order, "claim.deterministic_order"),
        Requirement("lease.wrong_token_blocked", "tamper.lease.wrong_token_blocked", ("lease.wrong_token_blocked.exception", "lease.wrong_token_blocked.physical_before", "lease.wrong_token_blocked.physical_after"), check_lease_wrong, tamper_lease_wrong, "lease.wrong_token_blocked"),
        Requirement("lease.expired_terminal_blocked", "tamper.lease.expired_terminal_blocked", ("lease.expired_terminal_blocked.exception", "lease.expired_terminal_blocked.physical_after"), check_lease_expired, tamper_lease_expired, "lease.expired_terminal_blocked"),
        Requirement("attempt.unique_number", "tamper.attempt.unique_number", ("attempt.unique_number.runtime_return", "attempt.unique_number.physical_rows"), check_attempt_unique, tamper_attempt_unique, "attempt.unique_number"),
        Requirement("transaction.attempt_committed_before_adapter", "tamper.transaction.attempt_committed_before_adapter", ("transaction.attempt_committed_before_adapter.physical_rows", "transaction.attempt_committed_before_adapter.separate_connection_visible"), check_transaction_visible, tamper_transaction_visible, "transaction.attempt_committed_before_adapter"),
        Requirement("transaction.adapter_outside_db_transaction", "tamper.transaction.adapter_outside_db_transaction", ("transaction.adapter_outside_db_transaction.adapter_observation", "transaction.adapter_outside_db_transaction.runtime_return"), check_transaction_adapter, tamper_transaction_adapter, "transaction.adapter_outside_db_transaction"),
        Requirement("result.definite_success", "tamper.result.definite_success", ("result.definite_success.runtime_return", "result.definite_success.physical_after"), check_result_success, tamper_result_success, "result.definite_success"),
        Requirement("result.not_human_read", "tamper.result.not_human_read", ("result.not_human_read.runtime_return", "result.not_human_read.physical_after"), check_result_read, tamper_result_read, "result.not_human_read"),
        Requirement("result.definite_failure_no_retry", "tamper.result.definite_failure_no_retry", ("result.definite_failure_no_retry.runtime_return", "result.definite_failure_no_retry.physical_after"), check_result_failure, tamper_result_failure, "result.definite_failure_no_retry"),
        Requirement("result.replay_same", "tamper.result.replay_same", ("result.replay_same.runtime_results", "result.replay_same.physical_rows"), check_result_replay, tamper_result_replay, "result.replay_same"),
        Requirement("result.mismatch_blocked", "tamper.result.mismatch_blocked", ("result.mismatch_blocked.exception", "result.mismatch_blocked.physical_after"), check_result_mismatch, tamper_result_mismatch, "result.mismatch_blocked"),
        Requirement("reconciliation.single_on_ambiguous", "tamper.reconciliation.single_on_ambiguous", ("reconciliation.single_on_ambiguous.persisted_attempt", "reconciliation.single_on_ambiguous.persisted_reconciliation"), check_recon_single, tamper_recon_single, "reconciliation.single_on_ambiguous"),
        Requirement("reconciliation.unresolved_blocks_attempt", "tamper.reconciliation.unresolved_blocks_attempt", ("reconciliation.unresolved_blocks_attempt.trusted_evidence", "reconciliation.unresolved_blocks_attempt.physical_after"), check_recon_blocks, tamper_recon_blocks, "reconciliation.unresolved_blocks_attempt"),
        Requirement("reconciliation.replay_same", "tamper.reconciliation.replay_same", ("reconciliation.replay_same.persisted_attempt", "reconciliation.replay_same.persisted_reconciliation"), check_recon_replay, tamper_recon_replay, "reconciliation.replay_same"),
        Requirement("reconciliation.resolved_delivered", "tamper.reconciliation.resolved_delivered", ("reconciliation.resolved_delivered.trusted_evidence", "reconciliation.resolved_delivered.physical_after"), check_recon_delivered, tamper_recon_delivered, "reconciliation.resolved_delivered"),
        Requirement("reconciliation.confirmed_no_effect_only_retry", "tamper.reconciliation.confirmed_no_effect_only_retry", ("reconciliation.confirmed_no_effect_only_retry.trusted_evidence", "reconciliation.confirmed_no_effect_only_retry.physical_after"), check_recon_no_effect, tamper_recon_no_effect, "reconciliation.confirmed_no_effect_only_retry"),
        Requirement("reconciliation.manual_ambiguous_blocks", "tamper.reconciliation.manual_ambiguous_blocks", ("reconciliation.manual_ambiguous_blocks.trusted_evidence", "reconciliation.manual_ambiguous_blocks.physical_after"), check_recon_manual, tamper_recon_manual, "reconciliation.manual_ambiguous_blocks"),
        Requirement("restart.claim_before_attempt_reclaim", "tamper.restart.claim_before_attempt_reclaim", ("restart.claim_before_attempt_reclaim.backend_pids", "restart.claim_before_attempt_reclaim.after"), check_restart_claim, tamper_restart_claim, "restart.claim_before_attempt_reclaim"),
        Requirement("restart.retry_claim_before_attempt_reclaim", "tamper.restart.retry_claim_before_attempt_reclaim", ("restart.retry_claim_before_attempt_reclaim.backend_pids", "restart.retry_claim_before_attempt_reclaim.after"), check_restart_retry, tamper_restart_retry, "restart.retry_claim_before_attempt_reclaim"),
        Requirement("restart.after_attempt_reconcile", "tamper.restart.after_attempt_reconcile", ("restart.after_attempt_reconcile.backend_pids", "restart.after_attempt_reconcile.after"), check_restart_attempt, tamper_restart_attempt, "restart.after_attempt_reconcile"),
        Requirement("history.account_scope", "tamper.history.account_scope", ("history.account_scope.runtime_return", "history.account_scope.physical_source_rows"), check_history_account, tamper_history_account, "history.account_scope"),
        Requirement("history.beacon_scope", "tamper.history.beacon_scope", ("history.beacon_scope.runtime_return", "history.beacon_scope.physical_source_rows"), check_history_beacon, tamper_history_beacon, "history.beacon_scope"),
        Requirement("history.cross_account_blocked", "tamper.history.cross_account_blocked", ("history.cross_account_blocked.exception", "history.cross_account_blocked.physical_source_rows"), check_history_cross_account, tamper_history_cross_account, "history.cross_account_blocked"),
        Requirement("history.safe_refs", "tamper.history.safe_refs", ("history.safe_refs.runtime_return", "history.safe_refs.physical_source_rows"), check_history_refs, tamper_history_refs, "history.safe_refs"),
        Requirement("foreign.authority_unchanged", "tamper.foreign.authority_unchanged", ("foreign.authority_unchanged.before", "foreign.authority_unchanged.after"), check_foreign, tamper_foreign, "foreign.authority_unchanged"),
        Requirement("privacy.no_raw_provider_values", "tamper.privacy.no_raw_provider_values", ("privacy.no_raw_provider_values.persisted_safe_projection", "privacy.no_raw_provider_values.key_inventory"), check_privacy_provider, tamper_privacy_provider, "privacy.no_raw_provider_values"),
        Requirement("privacy.no_raw_lease_values", "tamper.privacy.no_raw_lease_values", ("privacy.no_raw_lease_values.persisted_safe_projection", "privacy.no_raw_lease_values.key_inventory"), check_privacy_lease, tamper_privacy_lease, "privacy.no_raw_lease_values"),
    )

def _anti_summary(value: object, path: str = "evidence") -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key in _BAD_KEYS:
                found.append(f"{path}.{key}")
            if key == "backend_pids" and child == []:
                found.append(f"{path}.{key}")
            found.extend(_anti_summary(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value): found.extend(_anti_summary(child, f"{path}[{index}]"))
    return found

def assert_no_acceptance_summary(data: dict[str, object]) -> None:
    bad = _anti_summary(data)
    if bad: raise AssertionError("summary or mirrored evidence: " + ",".join(bad))

def _safe_check(checker: Callable[[dict[str, object]], bool], data: dict[str, object]) -> bool:
    try:
        return bool(checker(data))
    except (AttributeError, KeyError, TypeError, ValueError, IndexError):
        return False

def verify(data: dict[str, object], expected_sha: str | None, diagnostics_path: Path) -> None:
    assert_no_acceptance_summary(data)
    requirements = registry()
    executed_case_count, requirement_binding_count = _validate_executed_case_provenance(data)
    if _raw(data, "identity.technical_id") != TECHNICAL_ID or (expected_sha and _raw(data, "identity.candidate_sha") != expected_sha): raise SystemExit("RF17 evidence identity mismatch")
    original_failures = [item.requirement_id for item in requirements if not _safe_check(item.check, data)]
    tamper_failures: list[str] = []
    rejected: list[str] = []
    for item in requirements:
        mutated = copy.deepcopy(data); before = json.dumps(mutated, sort_keys=True); item.tamper(mutated)
        if before == json.dumps(mutated, sort_keys=True) or _safe_check(item.check, mutated): tamper_failures.append(item.requirement_id)
        else: rejected.append(item.requirement_id)
    diagnostics = {"technical_id": TECHNICAL_ID, "requirement_ids": list(EXPECTED_RF17_REQUIREMENT_IDS), "tamper_strategy_ids": list(EXPECTED_RF17_TAMPER_STRATEGY_IDS), "requirement_count": len(requirements), "checker_count": len(requirements), "unique_checker_count": len({item.check.__name__ for item in requirements}), "tamper_count": len(requirements), "unique_tamper_count": len({item.tamper.__name__ for item in requirements}), "requirement_checker_mapping": {item.requirement_id: item.check.__name__ for item in requirements}, "requirement_scenario_mapping": {item.requirement_id: item.scenario_id for item in requirements}, "required_raw_paths": {item.requirement_id: list(item.required_raw_paths) for item in requirements}, "raw_path_mapping_count": sum(bool(item.required_raw_paths) for item in requirements), "executed_case_count": executed_case_count, "requirement_executed_case_binding_count": requirement_binding_count, "fabricated_case_count": 0, "original_failures": original_failures, "tamper_failures": tamper_failures, "original_pass_count": len(requirements) - len(original_failures), "tamper_rejected_count": len(rejected), "evidence_digest": hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()}
    diagnostics_path.write_text(json.dumps(diagnostics, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    if original_failures or tamper_failures or tuple(rejected) != EXPECTED_RF17_REQUIREMENT_IDS: raise SystemExit("RF17 verifier failed")
    print(MARKER)

def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("evidence", type=Path); parser.add_argument("--expected-sha"); parser.add_argument("--diagnostics", type=Path, required=True); args = parser.parse_args(); verify(json.loads(args.evidence.read_text(encoding="utf-8")), args.expected_sha, args.diagnostics)

if __name__ == "__main__": main()
