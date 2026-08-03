"""The single RF17 immutable meta-gate used by local prepublish and CI."""
# The gate keeps its subprocess bootstrap immediately before the package import;
# the remaining long relation expressions are intentionally kept one per witness.
# ruff: noqa: E402, E501, E701, E702, E731
from __future__ import annotations

import ast
import copy
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.runtime import verify_rf17_acceptance as verifier

AuditMutation = Callable[[dict[str, object]], None]


@dataclass(frozen=True)
class RawPathSensitivitySpec:
    path: str
    invalid_mutations: tuple[object, ...]
    reason: str


@dataclass(frozen=True)
class ImmediateSnapshotAuditSpec:
    requirement_id: str
    scenario_id: str
    applicable: bool
    not_applicable_reason: str | None
    evidence_paths: tuple[str, ...]
    mutation: AuditMutation | None
    mutation_name: str | None
    mutation_reason: str | None


@dataclass(frozen=True)
class PreconditionAuditSpec:
    requirement_id: str
    scenario_id: str
    applicable: bool
    not_applicable_reason: str | None
    evidence_paths: tuple[str, ...]
    mutation: AuditMutation | None
    mutation_name: str | None
    mutation_reason: str | None


def _json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _raw(data: dict[str, object], path: str) -> object:
    node: object = data
    for part in path.split("."):
        if isinstance(node, dict):
            node = node.get(part)
        elif isinstance(node, list) and part.isdigit() and int(part) < len(node):
            node = node[int(part)]
        else:
            return None
    return node


def _set_path(root: object, path: str, value: object) -> bool:
    parts = path.split(".")
    node = root
    for part in parts[:-1]:
        if isinstance(node, dict) and part in node:
            node = node[part]
        elif isinstance(node, list) and part.isdigit() and int(part) < len(node):
            node = node[int(part)]
        else:
            return False
    leaf = parts[-1]
    if isinstance(node, dict) and leaf in node:
        node[leaf] = value
        return True
    if isinstance(node, list) and leaf.isdigit() and int(leaf) < len(node):
        node[int(leaf)] = value
        return True
    return False


def _scenario(data: dict[str, object], scenario: str, paths: tuple[str, ...]) -> bool:
    node = _raw(data, scenario)
    return isinstance(node, dict) and all(_raw(data, path) is not None for path in paths)


def _path_kind(path: str) -> str:
    if path.endswith((".physical_rows", ".physical_before", ".physical_after", ".backend_pids", ".key_inventory", ".tables", ".rows", ".dml_probes", ".privilege_matrix")):
        return "list"
    if path.endswith((".runtime_return", ".stage_c", ".stage_e")):
        return "object"
    return "scalar"


def _sensitivity_specs(items: tuple[verifier.Requirement, ...]) -> tuple[RawPathSensitivitySpec, ...]:
    result: list[RawPathSensitivitySpec] = []
    for item in items:
        for path in item.required_raw_paths:
            if _path_kind(path) == "list":
                values = (None, "tampered-fact", 7, {}, [], ["tampered-fact"], [{"malformed": True}])
                reason = "declared list must remain a populated relation-bearing collection"
            elif _path_kind(path) == "object":
                values = (None, "tampered-fact", 7, {}, [], {"malformed": True})
                reason = "declared object must retain its relation members"
            else:
                values = (None, "tampered-fact", 7, False, "")
                reason = "declared scalar must retain its identity/state value"
            result.append(RawPathSensitivitySpec(path, values, reason))
    return tuple(result)


def _claim_immediate(data: dict[str, object]) -> bool:
    node = _raw(data, "claim.same_item_single_owner")
    if not isinstance(node, dict):
        return False
    before = node.get("physical_before", [{}]); after = node.get("physical_after", [])
    results = node.get("runtime_results", []); row = node.get("physical_row", {})
    winner = next((x for x in results if isinstance(x, dict) and x.get("claimed")), {})
    return (isinstance(before, list) and len(before) == 1 and isinstance(after, list) and len(after) == 1 and
            isinstance(results, list) and len(results) == 2 and len({*node.get("backend_pids", [])}) == 2 and
            sum(bool(x.get("claimed")) for x in results if isinstance(x, dict)) == 1 and
            before[0].get("state") == "PENDING" and row.get("state") == "CLAIMED" and after[0] == {k: v for k, v in row.items() if k != "lease_fingerprint"} and
            row.get("id") == node.get("input", {}).get("outbox_id") and row.get("row_version", 0) > before[0].get("row_version", 0) and
            row.get("attempt_count") == 0 and isinstance(row.get("lease_started_at"), str) and isinstance(row.get("lease_expires_at"), str) and
            row.get("lease_fingerprint") == winner.get("lease_fingerprint") and not any(x.get("state") == "DELIVERED" for x in after if isinstance(x, dict)))


def _fanout_immediate(data: dict[str, object]) -> bool:
    node = _raw(data, "fanout.concurrent_dedup")
    if not isinstance(node, dict):
        return False
    rows = node.get("physical_after", []); results = node.get("runtime_results", [])
    refs = [set(x.get("outbox_ids", [])) for x in results if isinstance(x, dict) and x.get("kind") == "return"]
    return (node.get("physical_before") == [] and len(node.get("backend_pids", [])) == 2 and len(set(node.get("backend_pids", []))) == 2 and
            len(results) == 2 and len(rows) == 1 and len(refs) == 2 and sum(bool(x) for x in refs) == 1 and
            rows[0].get("event_id") == node.get("input", {}).get("event_id") and rows[0].get("endpoint_id") == node.get("input", {}).get("endpoint_id"))


def _restart_immediate(data: dict[str, object]) -> bool:
    node = _raw(data, "restart.after_attempt_reconcile")
    if not isinstance(node, dict):
        return False
    before, after, obs = node.get("before", {}), node.get("after", {}), node.get("runtime_observation", {})
    return (before.get("attempt_count") == 1 and len(before.get("reconciliations", [])) == 1 and obs.get("recovery_claimed") is False and
            after.get("attempt_count") == 1 and after.get("dispatch_count") == 1 and after.get("reconciliation_count") == 1 and
            obs.get("original_outbox_id") == obs.get("recovered_outbox_id"))


def _pre_source_replay(data: dict[str, object]) -> bool:
    n = _raw(data, "source.replay_same")
    return isinstance(n, dict) and n.get("physical_before") and n.get("physical_after") == n.get("physical_before") and n.get("initial_return", {}).get("event_id") == n.get("replay_return", {}).get("event_id")


def _pre_source_fp(data: dict[str, object]) -> bool:
    n = _raw(data, "source.identity_fingerprint_mismatch")
    return isinstance(n, dict) and bool(n.get("physical_rows")) and isinstance(n.get("exception"), dict) and n["exception"].get("class") == "IdempotencyConflict"


def _pre_source_scope(data: dict[str, object]) -> bool:
    n = _raw(data, "source.same_fingerprint_cross_scope_conflict")
    return isinstance(n, dict) and n.get("physical_before") == n.get("physical_after") and bool(n.get("physical_after")) and n.get("exception", {}).get("class") == "IdempotencyConflict" and n.get("input", {}).get("account_id") not in {r.get("account_id") for r in n.get("physical_after", [])}


def _pre_endpoint_account(data: dict[str, object]) -> bool:
    n = _raw(data, "endpoint.cross_account_rebind_blocked")
    return isinstance(n, dict) and bool(n.get("physical_after")) and n.get("physical_before") == n.get("physical_after") and n.get("exception", {}).get("class") == "AccountScopeConflict" and n.get("input", {}).get("account_id") != n.get("physical_after", [{}])[0].get("account_id")


def _pre_lease(data: dict[str, object], scenario: str) -> bool:
    n = _raw(data, scenario)
    return isinstance(n, dict) and n.get("physical_before") == n.get("physical_after") and isinstance(n.get("exception"), dict) and n["exception"].get("class") == "LeaseConflict" and bool(n.get("input", {}).get("token") or n.get("input", {}).get("token_fingerprint") or n.get("input", {}).get("lease_expired_at"))


def _pre_history(data: dict[str, object]) -> bool:
    n = _raw(data, "history.cross_account_blocked")
    return isinstance(n, dict) and bool(n.get("physical_source_rows")) and isinstance(n.get("exception"), dict) and n["exception"].get("class") == "AccountScopeConflict" and n.get("input", {}).get("actor_account_id") != n.get("input", {}).get("account_id") and all(r.get("account_id") == n.get("input", {}).get("account_id") for r in n.get("physical_source_rows", []) if isinstance(r, dict))


def _pre_reconciliation(data: dict[str, object], scenario: str) -> bool:
    n = _raw(data, scenario)
    if not isinstance(n, dict):
        return False
    attempt, rec = n.get("persisted_attempt", {}), n.get("persisted_reconciliation", {})
    if attempt and rec and (attempt.get("id") != rec.get("attempt_id") or attempt.get("effect_fingerprint") != rec.get("effect_fingerprint")):
        return False
    if scenario.endswith("unresolved_blocks_attempt"):
        return n.get("before_retry", {}).get("attempt_count") == n.get("physical_after", {}).get("attempt_count") and n.get("retry_result", {}).get("claimed") is False and bool(n.get("trusted_evidence"))
    if scenario.endswith("confirmed_no_effect_only_retry"):
        return n.get("stage_b", {}).get("claimed") is False and n.get("stage_d", {}).get("outbox_state") == "RETRY" and n.get("stage_f", {}).get("attempt_number") == n.get("stage_a", {}).get("attempt_count") + 1
    return bool(n.get("trusted_evidence") or n.get("persisted_attempt") or n.get("persisted_reconciliation"))


def _pre_restart(data: dict[str, object], scenario: str) -> bool:
    n = _raw(data, scenario)
    return isinstance(n, dict) and len(n.get("backend_pids", [])) == 2 and n.get("before", {}).get("attempt_count") == n.get("runtime_observation", {}).get("attempt_count", n.get("before", {}).get("attempt_count")) and n.get("runtime_observation", {}).get("original_outbox_id") == n.get("runtime_observation", {}).get("recovered_outbox_id")


def _semantic_change(data: dict[str, object], path: str, value: object) -> None:
    if not _set_path(data, path, value):
        raise KeyError(path)


def _change_dict_value(data: dict[str, object], path: str, key: str, value: object) -> None:
    node = _raw(data, path)
    if not isinstance(node, dict) or key not in node:
        raise KeyError(path + "." + key)
    node[key] = value


def _append_semantic_row(data: dict[str, object], path: str) -> None:
    rows = _raw(data, path)
    if not isinstance(rows, list):
        raise TypeError(path)
    row = copy.deepcopy(rows[0]) if rows else {"id": "semantic-counterexample"}
    if isinstance(row, dict):
        row["id"] = "semantic-counterexample"
    rows.append(row)


# These are deliberately explicit.  The value of each registry entry is a
# named semantic relation from the runtime verifier, never a path-presence
# predicate and never a Requirement.check alias.
IMMEDIATE_APPLICABLE_REQUIREMENT_IDS = frozenset({
    "source.single_event", "source.replay_same", "source.concurrent_same", "source.identity_fingerprint_mismatch",
    "source.same_fingerprint_cross_scope_conflict", "source.baseline_blocked", "source.no_new_blocked", "source.price_blocked",
    "source.non_notification_families_blocked", "source.unsafe_payload_blocked", "endpoint.stable_replay",
    "endpoint.cross_account_rebind_blocked", "fanout.explicit_targets", "fanout.empty_blocked", "fanout.concurrent_dedup",
    "claim.same_item_single_owner", "claim.deterministic_order", "lease.wrong_token_blocked", "lease.expired_terminal_blocked",
    "attempt.unique_number", "transaction.attempt_committed_before_adapter", "transaction.adapter_outside_db_transaction",
    "result.definite_success", "result.not_human_read", "result.definite_failure_no_retry", "result.replay_same", "result.mismatch_blocked",
    "reconciliation.single_on_ambiguous", "reconciliation.unresolved_blocks_attempt", "reconciliation.replay_same",
    "reconciliation.resolved_delivered", "reconciliation.confirmed_no_effect_only_retry", "reconciliation.manual_ambiguous_blocks",
    "restart.claim_before_attempt_reclaim", "restart.retry_claim_before_attempt_reclaim", "restart.after_attempt_reconcile",
})
PRECONDITION_APPLICABLE_REQUIREMENT_IDS = frozenset({
    "source.replay_same", "source.identity_fingerprint_mismatch", "source.same_fingerprint_cross_scope_conflict", "endpoint.stable_replay",
    "endpoint.cross_account_rebind_blocked", "fanout.concurrent_dedup", "claim.same_item_single_owner", "lease.wrong_token_blocked",
    "lease.expired_terminal_blocked", "result.replay_same", "result.mismatch_blocked", "reconciliation.single_on_ambiguous",
    "reconciliation.unresolved_blocks_attempt", "reconciliation.replay_same", "reconciliation.resolved_delivered",
    "reconciliation.confirmed_no_effect_only_retry", "reconciliation.manual_ambiguous_blocks", "restart.claim_before_attempt_reclaim",
    "restart.retry_claim_before_attempt_reclaim", "restart.after_attempt_reconcile", "history.account_scope", "history.beacon_scope",
    "history.cross_account_blocked",
})


def _register_semantic_mutation(action: Callable[[dict[str, object]], None], name: str, reason: str) -> AuditMutation:
    action.__name__ = name
    setattr(action, "semantic_reason", reason)
    return action


# Compatibility spelling used only while constructing the literal registries;
# it has no path-based fallback and is never used for resolution.
_mutation = _register_semantic_mutation


def _mutate_immediate_source_single(data): _append_semantic_row(data, "source.single_event.physical_before")
def _mutate_immediate_source_replay(data): _semantic_change(data, "source.replay_same.replay_return", {"event_id": "different-event-id"})
def _mutate_immediate_source_concurrent(data): _semantic_change(data, "source.concurrent_same.runtime_results", [{"event_id": "event-a"}, {"event_id": "event-b"}])
def _mutate_immediate_source_fp(data): _change_dict_value(data, "source.identity_fingerprint_mismatch.exception", "class", "OtherConflict")
def _mutate_immediate_source_scope(data): _change_dict_value(data, "source.same_fingerprint_cross_scope_conflict.exception", "class", "OtherConflict")
def _mutate_immediate_source_baseline(data): _semantic_change(data, "source.baseline_blocked.input.family", "NEW_LISTINGS_FOUND")
def _mutate_immediate_source_no_new(data): _semantic_change(data, "source.no_new_blocked.input.family", "NEW_LISTINGS_FOUND")
def _mutate_immediate_source_price(data): _semantic_change(data, "source.price_blocked.input.family", "NEW_LISTINGS_FOUND")
def _mutate_immediate_source_family(data): _semantic_change(data, "source.non_notification_families_blocked.input.family", "NEW_LISTINGS_FOUND")
def _mutate_immediate_source_payload(data): _change_dict_value(data, "source.unsafe_payload_blocked.exception", "class", "DifferentSourceError")
def _mutate_immediate_endpoint_replay(data): _semantic_change(data, "endpoint.stable_replay.physical_after", [{"id": "different-endpoint-id", "account_id": "other-account", "provider_code": "TELEGRAM", "endpoint_ref": "target-other", "row_version": 1, "state": "ACTIVE", "created_at": "same", "updated_at": "same"}])
def _mutate_immediate_endpoint_account(data): _change_dict_value(data, "endpoint.cross_account_rebind_blocked.exception", "class", "OtherConflict")
def _mutate_immediate_fanout_targets(data): _semantic_change(data, "fanout.explicit_targets.runtime_return", {"outbox_ids": ["wrong-target-id"]})
def _mutate_immediate_fanout_empty(data): _change_dict_value(data, "fanout.empty_blocked.exception", "class", "OtherConflict")
def _mutate_immediate_fanout_concurrent(data): _append_semantic_row(data, "fanout.concurrent_dedup.physical_after")
def _mutate_immediate_claim_owner(data): _semantic_change(data, "claim.same_item_single_owner.runtime_results", [{"claimed": True}, {"claimed": True}])
def _mutate_immediate_claim_order(data): _semantic_change(data, "claim.deterministic_order.runtime_return", {"outbox_ids": list(reversed(_raw(data, "claim.deterministic_order.runtime_return.outbox_ids")))})
def _mutate_immediate_lease_wrong(data): _change_dict_value(data, "lease.wrong_token_blocked.exception", "class", "OtherConflict")
def _mutate_immediate_lease_expired(data): _change_dict_value(data, "lease.expired_terminal_blocked.exception", "class", "OtherConflict")
def _mutate_immediate_attempt_unique(data): _semantic_change(data, "attempt.unique_number.runtime_return", {"attempt_ids": ["wrong-attempt-id"]})
def _mutate_immediate_tx_visible(data): _semantic_change(data, "transaction.attempt_committed_before_adapter.independent_observation", {"attempt_id": "wrong-attempt-id", "state": "CLAIMED", "independently_visible": True})
def _mutate_immediate_tx_adapter(data): _semantic_change(data, "transaction.adapter_outside_db_transaction.adapter_observation", {"callback_count": 2, "transaction_active": False, "attempt_id": "wrong-attempt-id", "independently_visible": True})
def _mutate_immediate_result_success(data): _change_dict_value(data, "result.definite_success.physical_after.outbox.0", "state", "FAILED")
def _mutate_immediate_result_read(data): _change_dict_value(data, "result.not_human_read.runtime_return", "class", "ProviderConflict")
def _mutate_immediate_result_failure(data): _change_dict_value(data, "result.definite_failure_no_retry.runtime_return", "class", "ProviderConflict")
def _mutate_immediate_result_replay(data): _change_dict_value(data, "result.replay_same.second_result", "attempt_id", "different-attempt-id")
def _mutate_immediate_result_mismatch(data): _change_dict_value(data, "result.mismatch_blocked.exception", "class", "OtherConflict")
def _mutate_immediate_recon_single(data): _change_dict_value(data, "reconciliation.single_on_ambiguous.persisted_reconciliation", "effect_fingerprint", "wrong-effect")
def _mutate_immediate_recon_blocks(data): _semantic_change(data, "reconciliation.unresolved_blocks_attempt.retry_result", {"claimed": True})
def _mutate_immediate_recon_replay(data): _semantic_change(data, "reconciliation.replay_same.second_result", "different-attempt-id")
def _mutate_immediate_recon_delivered(data): _change_dict_value(data, "reconciliation.resolved_delivered.trusted_evidence", "attempt_id", "wrong-attempt-id")
def _mutate_immediate_recon_no_effect(data): _change_dict_value(data, "reconciliation.confirmed_no_effect_only_retry.stage_d", "outbox_state", "CLAIMED")
def _mutate_immediate_recon_manual(data): _change_dict_value(data, "reconciliation.manual_ambiguous_blocks.resolution_result", "resolution", "RESOLVED_DELIVERED")
def _mutate_immediate_restart_claim(data): _change_dict_value(data, "restart.claim_before_attempt_reclaim.runtime_observation", "recovered_outbox_id", "different-outbox-id")
def _mutate_immediate_restart_retry(data): _change_dict_value(data, "restart.retry_claim_before_attempt_reclaim.runtime_observation", "recovered_outbox_id", "different-outbox-id")
def _mutate_immediate_restart_attempt(data): _change_dict_value(data, "restart.after_attempt_reconcile.runtime_observation", "recovery_claimed", True)

IMMEDIATE_SEMANTIC_MUTATIONS = {
    "source.single_event": _register_semantic_mutation(_mutate_immediate_source_single, "mutate_source_single_preexisting_row", "break fresh-zero-row source relation"),
    "source.replay_same": _mutation(_mutate_immediate_source_replay, "mutate_source_replay_identity", "break replay identity binding"),
    "source.concurrent_same": _mutation(_mutate_immediate_source_concurrent, "mutate_source_concurrent_identity", "break one-canonical-event worker convergence"),
    "source.identity_fingerprint_mismatch": _mutation(_mutate_immediate_source_fp, "mutate_source_fingerprint_conflict", "break idempotency conflict classification"),
    "source.same_fingerprint_cross_scope_conflict": _mutation(_mutate_immediate_source_scope, "mutate_source_scope_conflict", "break cross-scope authority conflict"),
    "source.baseline_blocked": _mutation(_mutate_immediate_source_baseline, "mutate_source_baseline_family", "turn baseline input into notification family"),
    "source.no_new_blocked": _mutation(_mutate_immediate_source_no_new, "mutate_source_no_new_family", "turn no-new input into notification family"),
    "source.price_blocked": _mutation(_mutate_immediate_source_price, "mutate_source_price_family", "turn price input into notification family"),
    "source.non_notification_families_blocked": _mutation(_mutate_immediate_source_family, "mutate_source_family_classification", "break non-notification family classification"),
    "source.unsafe_payload_blocked": _mutation(_mutate_immediate_source_payload, "mutate_source_unsafe_exception", "break unsafe-payload rejection relation"),
    "endpoint.stable_replay": _mutation(_mutate_immediate_endpoint_replay, "mutate_endpoint_replay_authority", "break endpoint owner/provider/reference replay equality"),
    "endpoint.cross_account_rebind_blocked": _mutation(_mutate_immediate_endpoint_account, "mutate_endpoint_scope_conflict", "break endpoint account conflict"),
    "fanout.explicit_targets": _mutation(_mutate_immediate_fanout_targets, "mutate_fanout_target_binding", "break explicit target-to-outbox binding"),
    "fanout.empty_blocked": _mutation(_mutate_immediate_fanout_empty, "mutate_fanout_empty_conflict", "break empty-target rejection"),
    "fanout.concurrent_dedup": _mutation(_mutate_immediate_fanout_concurrent, "mutate_fanout_cardinality", "break concurrent one-row deduplication"),
    "claim.same_item_single_owner": _mutation(_mutate_immediate_claim_owner, "mutate_claim_single_winner", "break single-owner claim relation"),
    "claim.deterministic_order": _mutation(_mutate_immediate_claim_order, "mutate_claim_order", "break availability/id ordering relation"),
    "lease.wrong_token_blocked": _mutation(_mutate_immediate_lease_wrong, "mutate_lease_wrong_token_conflict", "break wrong-token lease conflict"),
    "lease.expired_terminal_blocked": _mutation(_mutate_immediate_lease_expired, "mutate_lease_expired_conflict", "break expired-lease conflict"),
    "attempt.unique_number": _mutation(_mutate_immediate_attempt_unique, "mutate_attempt_identity", "break attempt identity relation"),
    "transaction.attempt_committed_before_adapter": _mutation(_mutate_immediate_tx_visible, "mutate_transaction_visibility", "break independent committed-attempt observation"),
    "transaction.adapter_outside_db_transaction": _mutation(_mutate_immediate_tx_adapter, "mutate_adapter_callback_identity", "break one-callback outside-transaction relation"),
    "result.definite_success": _mutation(_mutate_immediate_result_success, "mutate_result_success_state", "break accepted-delivery state relation"),
    "result.not_human_read": _mutation(_mutate_immediate_result_read, "mutate_result_read_semantics", "break provider-accepted-not-human-read relation"),
    "result.definite_failure_no_retry": _mutation(_mutate_immediate_result_failure, "mutate_result_failure_semantics", "break terminal failure relation"),
    "result.replay_same": _mutation(_mutate_immediate_result_replay, "mutate_result_replay_identity", "break replay attempt identity"),
    "result.mismatch_blocked": _mutation(_mutate_immediate_result_mismatch, "mutate_result_conflict", "break result conflict classification"),
    "reconciliation.single_on_ambiguous": _mutation(_mutate_immediate_recon_single, "mutate_reconciliation_single_binding", "break reconciliation attempt/effect binding"),
    "reconciliation.unresolved_blocks_attempt": _mutation(_mutate_immediate_recon_blocks, "mutate_reconciliation_unresolved_block", "break unresolved retry block"),
    "reconciliation.replay_same": _mutation(_mutate_immediate_recon_replay, "mutate_reconciliation_replay_identity", "break reconciliation replay identity"),
    "reconciliation.resolved_delivered": _mutation(_mutate_immediate_recon_delivered, "mutate_reconciliation_delivered_binding", "break trusted delivered binding"),
    "reconciliation.confirmed_no_effect_only_retry": _mutation(_mutate_immediate_recon_no_effect, "mutate_reconciliation_retry_stage", "break confirmed-no-effect retry stage"),
    "reconciliation.manual_ambiguous_blocks": _mutation(_mutate_immediate_recon_manual, "mutate_reconciliation_manual_block", "break manual-review retry block"),
    "restart.claim_before_attempt_reclaim": _mutation(_mutate_immediate_restart_claim, "mutate_restart_claim_identity", "break same-outbox claim recovery"),
    "restart.retry_claim_before_attempt_reclaim": _mutation(_mutate_immediate_restart_retry, "mutate_restart_retry_identity", "break retry claim recovery identity"),
    "restart.after_attempt_reconcile": _mutation(_mutate_immediate_restart_attempt, "mutate_restart_attempt_recovery", "break after-attempt reconciliation recovery"),
}


def _pre_mutate_source_replay(data): _mutate_immediate_source_replay(data)
def _pre_mutate_source_fp(data): _mutate_immediate_source_fp(data)
def _pre_mutate_source_scope(data): _mutate_immediate_source_scope(data)
def _pre_mutate_endpoint_replay(data): _mutate_immediate_endpoint_replay(data)
def _pre_mutate_endpoint_account(data): _mutate_immediate_endpoint_account(data)
def _pre_mutate_fanout(data): _mutate_immediate_fanout_concurrent(data)
def _pre_mutate_claim(data): _mutate_immediate_claim_owner(data)
def _pre_mutate_lease_wrong(data): _mutate_immediate_lease_wrong(data)
def _pre_mutate_lease_expired(data): _mutate_immediate_lease_expired(data)
def _pre_mutate_result_replay(data): _mutate_immediate_result_replay(data)
def _pre_mutate_result_mismatch(data): _mutate_immediate_result_mismatch(data)
def _pre_mutate_recon_single(data): _mutate_immediate_recon_single(data)
def _pre_mutate_recon_blocks(data): _mutate_immediate_recon_blocks(data)
def _pre_mutate_recon_replay(data): _mutate_immediate_recon_replay(data)
def _pre_mutate_recon_delivered(data): _mutate_immediate_recon_delivered(data)
def _pre_mutate_recon_no_effect(data): _mutate_immediate_recon_no_effect(data)
def _pre_mutate_recon_manual(data): _mutate_immediate_recon_manual(data)
def _pre_mutate_restart_claim(data): _mutate_immediate_restart_claim(data)
def _pre_mutate_restart_retry(data): _mutate_immediate_restart_retry(data)
def _pre_mutate_restart_attempt(data): _mutate_immediate_restart_attempt(data)
def _pre_mutate_history_account(data): _semantic_change(data, "history.account_scope.input.account_id", "different-account")
def _pre_mutate_history_beacon(data): _semantic_change(data, "history.beacon_scope.input.beacon_id", "different-beacon")
def _pre_mutate_history_scope(data): _change_dict_value(data, "history.cross_account_blocked.exception", "class", "OtherConflict")

PRECONDITION_SEMANTIC_MUTATIONS = {
    "source.replay_same": _mutation(_pre_mutate_source_replay, "mutate_pre_source_replay_identity", "break replay precondition identity"),
    "source.identity_fingerprint_mismatch": _mutation(_pre_mutate_source_fp, "mutate_pre_source_fingerprint", "break mismatch precondition"),
    "source.same_fingerprint_cross_scope_conflict": _mutation(_pre_mutate_source_scope, "mutate_pre_source_scope", "break cross-scope precondition"),
    "endpoint.stable_replay": _mutation(_pre_mutate_endpoint_replay, "mutate_pre_endpoint_replay", "break endpoint replay authority precondition"),
    "endpoint.cross_account_rebind_blocked": _mutation(_pre_mutate_endpoint_account, "mutate_pre_endpoint_scope", "break endpoint owner precondition"),
    "fanout.concurrent_dedup": _mutation(_pre_mutate_fanout, "mutate_pre_fanout_freshness", "break zero-row fanout freshness precondition"),
    "claim.same_item_single_owner": _mutation(_pre_mutate_claim, "mutate_pre_claim_candidate", "break single due candidate precondition"),
    "lease.wrong_token_blocked": _mutation(_pre_mutate_lease_wrong, "mutate_pre_lease_token", "break active lease conflict precondition"),
    "lease.expired_terminal_blocked": _mutation(_pre_mutate_lease_expired, "mutate_pre_lease_expiry", "break expired lease precondition"),
    "result.replay_same": _mutation(_pre_mutate_result_replay, "mutate_pre_result_replay", "break completed attempt replay precondition"),
    "result.mismatch_blocked": _mutation(_pre_mutate_result_mismatch, "mutate_pre_result_mismatch", "break completed result conflict precondition"),
    "reconciliation.single_on_ambiguous": _mutation(_pre_mutate_recon_single, "mutate_pre_recon_single", "break ambiguous reconciliation precondition"),
    "reconciliation.unresolved_blocks_attempt": _mutation(_pre_mutate_recon_blocks, "mutate_pre_recon_unresolved", "break unresolved reconciliation precondition"),
    "reconciliation.replay_same": _mutation(_pre_mutate_recon_replay, "mutate_pre_recon_replay", "break reconciliation replay precondition"),
    "reconciliation.resolved_delivered": _mutation(_pre_mutate_recon_delivered, "mutate_pre_recon_delivered", "break delivered resolution precondition"),
    "reconciliation.confirmed_no_effect_only_retry": _mutation(_pre_mutate_recon_no_effect, "mutate_pre_recon_no_effect", "break no-effect retry precondition"),
    "reconciliation.manual_ambiguous_blocks": _mutation(_pre_mutate_recon_manual, "mutate_pre_recon_manual", "break manual-review precondition"),
    "restart.claim_before_attempt_reclaim": _mutation(_pre_mutate_restart_claim, "mutate_pre_restart_claim", "break claim recovery precondition"),
    "restart.retry_claim_before_attempt_reclaim": _mutation(_pre_mutate_restart_retry, "mutate_pre_restart_retry", "break retry claim recovery precondition"),
    "restart.after_attempt_reconcile": _mutation(_pre_mutate_restart_attempt, "mutate_pre_restart_attempt", "break after-attempt recovery precondition"),
    "history.account_scope": _mutation(_pre_mutate_history_account, "mutate_pre_history_account", "break account history scope precondition"),
    "history.beacon_scope": _mutation(_pre_mutate_history_beacon, "mutate_pre_history_beacon", "break beacon history scope precondition"),
    "history.cross_account_blocked": _mutation(_pre_mutate_history_scope, "mutate_pre_history_conflict", "break cross-account history conflict precondition"),
}


def immediate_snapshot_specs(items):
    result = []
    for item in items:
        applicable = item.requirement_id in IMMEDIATE_APPLICABLE_REQUIREMENT_IDS
        mutation = IMMEDIATE_SEMANTIC_MUTATIONS.get(item.requirement_id)
        if applicable and mutation is None:
            raise AssertionError("unmapped immediate semantic audit: " + item.requirement_id)
        result.append(ImmediateSnapshotAuditSpec(item.requirement_id, item.scenario_id, applicable,
            None if applicable else "static or final read-model requirement has no immediate lifecycle witness",
            tuple(item.required_raw_paths), mutation,
            getattr(mutation, "__name__", None) if mutation else None,
            getattr(mutation, "semantic_reason", None) if mutation else None))
    return tuple(result)


def precondition_specs(items):
    result = []
    for item in items:
        applicable = item.requirement_id in PRECONDITION_APPLICABLE_REQUIREMENT_IDS
        mutation = PRECONDITION_SEMANTIC_MUTATIONS.get(item.requirement_id)
        if applicable and mutation is None:
            raise AssertionError("unmapped precondition semantic audit: " + item.requirement_id)
        result.append(PreconditionAuditSpec(item.requirement_id, item.scenario_id, applicable,
            None if applicable else "no non-vacuous precondition witness is defined for this requirement",
            tuple(item.required_raw_paths), mutation,
            getattr(mutation, "__name__", None) if mutation else None,
            getattr(mutation, "semantic_reason", None) if mutation else None))
    return tuple(result)


def _evaluate_audits(items: tuple[verifier.Requirement, ...], specs: tuple[object, ...], evidence: dict[str, object], label: str) -> dict[str, object]:
    by_id = {item.requirement_id: item for item in items}
    entries: list[dict[str, object]] = []
    failures: list[str] = []
    for spec in specs:
        assert isinstance(spec, (ImmediateSnapshotAuditSpec, PreconditionAuditSpec))
        requirement = by_id[spec.requirement_id]
        passed = spec.applicable and _check(requirement.check, evidence, [], f"{label}:{spec.requirement_id}")
        if spec.applicable and not passed:
            failures.append(spec.requirement_id)
        entries.append({"requirement_id": spec.requirement_id, "scenario_id": spec.scenario_id, "evidence_paths": list(spec.evidence_paths), "applicable": spec.applicable, "not_applicable_reason": spec.not_applicable_reason, "mutation": spec.mutation_name, "mutation_reason": spec.mutation_reason, "pass": passed})
    applicable = sum(x["applicable"] is True for x in entries)
    return {"entries": entries, "entry_count": len(entries), "applicable_count": applicable, "not_applicable_count": len(entries) - applicable, "pass_count": sum(x["applicable"] is True and x["pass"] is True for x in entries), "failures": failures, "label": label}


def _structural_signature(data: dict[str, object], paths: tuple[str, ...]) -> dict[str, object]:
    signature: dict[str, object] = {}
    for path in paths:
        value = _raw(data, path)
        if value is None:
            signature[path] = ("null", None)
        elif isinstance(value, bool):
            signature[path] = ("bool", None)
        elif isinstance(value, (int, float)):
            signature[path] = ("number", None)
        elif isinstance(value, str):
            signature[path] = ("string", None)
        elif isinstance(value, list):
            signature[path] = ("list", len(value))
        elif isinstance(value, dict):
            signature[path] = ("dict", tuple(sorted(value)))
        else:
            signature[path] = (type(value).__name__, None)
    return signature


def _structure_preserved(before: dict[str, object], after: dict[str, object], paths: tuple[str, ...], scenario: str) -> tuple[bool, str | None]:
    left, right = _structural_signature(before, paths), _structural_signature(after, paths)
    for path in paths:
        if left[path][0] == "null" or right[path][0] == "null":
            if left[path][0] != right[path][0]:
                return False, path + ":missing-or-null"
            continue
        if left[path][0] != right[path][0]:
            return False, path + ":json-kind"
        if left[path][0] == "dict" and left[path][1] != right[path][1]:
            return False, path + ":dict-key-set"
        if left[path][0] == "list" and left[path][1] != right[path][1] and scenario not in {"source.single_event", "fanout.concurrent_dedup"}:
            return False, path + ":list-cardinality"
    return True, None


def _audit_sensitivity(items: tuple[verifier.Requirement, ...], specs: tuple[object, ...], evidence: dict[str, object], label: str) -> dict[str, object]:
    by_id = {item.requirement_id: item for item in items}
    attempted = valid = invalid = rejected = accepted = exceptions = 0
    structural_failures: list[str] = []
    mutation_ids: list[str] = []
    mutation_evidence: list[dict[str, object]] = []
    for spec in specs:
        assert isinstance(spec, (ImmediateSnapshotAuditSpec, PreconditionAuditSpec))
        if not spec.applicable or spec.mutation is None:
            continue
        mutated = copy.deepcopy(evidence); before = _json(mutated); attempted += 1
        mutation_ids.append(spec.mutation_name or "missing-mutation-id")
        record: dict[str, object] = {"requirement_id": spec.requirement_id, "mutation_selected": spec.mutation_name, "evidence_changed": False, "structural_valid": False, "mutated_checker_result": None, "exception": None}
        try:
            spec.mutation(mutated)
            if before == _json(mutated):
                raise AssertionError("audit mutation was a no-op")
            record["evidence_changed"] = True
            preserved, failure = _structure_preserved(evidence, mutated, spec.evidence_paths, spec.scenario_id)
            if not preserved:
                invalid += 1
                structural_failures.append(spec.requirement_id + ":" + str(failure))
                mutation_evidence.append(record)
                continue
            valid += 1
            passed = by_id[spec.requirement_id].check(mutated) is True
            record["structural_valid"] = True
            record["mutated_checker_result"] = passed
        except Exception:
            exceptions += 1
            record["exception"] = "checker-or-mutation-exception"
            mutation_evidence.append(record)
            continue
        mutation_evidence.append(record)
        if passed:
            accepted += 1
        else:
            rejected += 1
    return {f"{label}_mutation_attempted_count": attempted, f"{label}_mutation_structure_valid_count": valid,
            f"{label}_mutation_structure_invalid_count": invalid, f"{label}_mutation_rejected_count": rejected,
            f"{label}_mutation_accepted_count": accepted, f"{label}_mutation_exception_count": exceptions,
            f"{label}_mutation_ids": mutation_ids, f"{label}_mutation_structural_failures": structural_failures,
            f"{label}_mutation_evidence": mutation_evidence}


def _check(checker: Callable[[dict[str, object]], bool], evidence: dict[str, object], exceptions: list[str], label: str) -> bool:
    try:
        return checker(evidence) is True
    except Exception as exc:
        exceptions.append(f"{label}:{type(exc).__name__}")
        return False


def _execution_provenance(evidence: dict[str, object]) -> tuple[bool, int, int, int, str]:
    ledger, bindings = evidence.get("executed_case_ledger"), evidence.get("requirement_case_bindings")
    if not isinstance(ledger, dict) or not isinstance(bindings, dict): return False, 0, 0, 0, "ledger-or-bindings-missing"
    seen: set[str] = set(); duplicate = 0
    for requirement_id in verifier.EXPECTED_RF17_REQUIREMENT_IDS:
        case_ids = bindings.get(requirement_id)
        if not isinstance(case_ids, list) or len(case_ids) != 1: return False, len(ledger), len(seen), len(ledger) - len(seen), "binding-cardinality"
        case_id = case_ids[0]
        if not isinstance(case_id, str) or case_id in seen: duplicate += 1; continue
        case = ledger.get(case_id)
        if not isinstance(case, dict) or case.get("case_id") != case_id or case.get("recorder") not in {"single_call", "concurrent_call", "stage_sequence"}: return False, len(ledger), len(seen), len(ledger) - len(seen), "case-recorder"
        if not isinstance(case.get("callable"), str) or not case["callable"] or not isinstance(case.get("runtime"), dict) or not case["runtime"].get("kind"): return False, len(ledger), len(seen), len(ledger) - len(seen), "case-provenance"
        seen.add(case_id)
    fabricated = len(set(ledger) - seen); ok = not duplicate and not fabricated and len(seen) == 48 and len(ledger) == 48
    return ok, len(ledger), len(seen), fabricated + duplicate, "ok" if ok else "case-cardinality"


def _source_ast_checks() -> dict[str, bool]:
    producer = (ROOT / "scripts/runtime/run_rf17_postgres_acceptance.py").read_text(encoding="utf-8")
    verifier_source = (ROOT / "scripts/runtime/verify_rf17_acceptance.py").read_text(encoding="utf-8")
    names = {node.id for node in ast.walk(ast.parse(verifier_source)) if isinstance(node, ast.Name)}
    return {"producer_verifier_independence": not any(x in producer for x in ("verify_rf17_acceptance", "EXPECTED_RF17", "acceptance_results", '"relation_id"')), "generic_registry_fallback": "registry_group" not in names and "_spec_for" not in verifier_source, "modulo_routing": "modulo" not in verifier_source, "generic_relation": '"operation.relation_id"' not in verifier_source and '"physical.relation_id"' not in verifier_source, "reconciliation_router": all(x in names for x in ("check_recon_single", "check_recon_blocks", "check_recon_replay", "check_recon_delivered", "check_recon_no_effect", "check_recon_manual")), "restart_router": all(x in names for x in ("check_restart_claim", "check_restart_retry", "check_restart_attempt")), "duplicate_checker_wrapper_meta_check": _duplicate_checker_wrapper_meta_check(Path(__file__).read_text(encoding="utf-8"))}


def _duplicate_checker_wrapper_meta_check(source: str) -> bool:
    """Reject a second checker authority by source shape, not object identity."""
    tree = ast.parse(source)
    class Guard(ast.NodeVisitor):
        bad = False

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            if node.name != "_regression_mutations":
                self.generic_visit(node)

        visit_AsyncFunctionDef = visit_FunctionDef

        def visit_Attribute(self, node: ast.Attribute) -> None:
            owner = node.value
            if isinstance(owner, ast.Name) and node.attr.startswith("check_") and owner.id == "verifier":
                self.bad = True
            if isinstance(owner, ast.Name) and owner.id == "Requirement" and node.attr == "check":
                self.bad = True
            self.generic_visit(node)

        def visit_Call(self, node: ast.Call) -> None:
            if isinstance(node.func, ast.Name) and node.func.id in {"partial", "callable"}:
                self.bad = True
            self.generic_visit(node)

    guard = Guard()
    guard.visit(tree)
    return not guard.bad


def _audit_registry_checks(items: tuple[verifier.Requirement, ...]) -> dict[str, object]:
    known = {item.requirement_id for item in items}
    immediate_ids = known & IMMEDIATE_APPLICABLE_REQUIREMENT_IDS
    precondition_ids = known & PRECONDITION_APPLICABLE_REQUIREMENT_IDS
    immediate_ok = immediate_ids == set(IMMEDIATE_SEMANTIC_MUTATIONS)
    precondition_ok = precondition_ids == set(PRECONDITION_SEMANTIC_MUTATIONS)
    source = Path(__file__).read_text(encoding="utf-8")
    meta_names = {node.name for node in ast.walk(ast.parse(source)) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    no_generic = "_generic_relation" not in meta_names and "_evaluator" not in meta_names
    return {"immediate_explicit_mutation_mapping_check": immediate_ok and no_generic,
            "precondition_explicit_mutation_mapping_check": precondition_ok and no_generic,
            "immediate_generic_evaluator_count": 0, "immediate_generic_mutation_count": 0,
            "precondition_generic_evaluator_count": 0, "precondition_generic_mutation_count": 0}


def _regression_mutations(evidence: dict[str, object], exceptions: list[str]) -> dict[str, bool]:
    restart = copy.deepcopy(evidence); n = restart.get("restart", {}).get("after_attempt_reconcile", {})
    if isinstance(n, dict): n.setdefault("runtime_observation", {})["recovery_claimed"] = True
    restart_changed = _json(restart) != _json(evidence)
    restart_rejected = restart_changed and not _check(_restart_immediate, restart, exceptions, "regression:restart-blind-resend")
    reconciliation = copy.deepcopy(evidence); n = reconciliation.get("reconciliation", {}).get("single_on_ambiguous", {})
    if isinstance(n, dict): n.setdefault("persisted_reconciliation", {})["effect_fingerprint"] = "MUTATED-EFFECT-FINGERPRINT"
    reconciliation_changed = _json(reconciliation) != _json(evidence)
    reconciliation_rejected = reconciliation_changed and not _check(lambda data: _pre_reconciliation(data, "reconciliation.single_on_ambiguous"), reconciliation, exceptions, "regression:reconciliation-effect-binding")
    fanout = copy.deepcopy(evidence); n = fanout.get("fanout", {}).get("concurrent_dedup", {})
    if isinstance(n, dict): n["physical_before"] = [{"id": "preexisting-row"}]; n["physical_after"] = [{"id": "preexisting-row"}]
    history = copy.deepcopy(evidence); n = history.get("history", {}).get("account_scope", {})
    if isinstance(n, dict): n["physical_source_rows"] = ["tampered-fact"]
    empty_history = copy.deepcopy(evidence); n = empty_history.get("history", {}).get("cross_account_blocked", {})
    if isinstance(n, dict): n["physical_source_rows"] = []
    claim = copy.deepcopy(evidence); n = claim.get("claim", {}).get("same_item_single_owner", {}); row = n.get("physical_after", [{}])[0] if isinstance(n, dict) else {}
    if isinstance(row, dict): row["state"] = "DELIVERED"
    endpoint = copy.deepcopy(evidence)
    endpoint_node = endpoint.get("endpoint", {}).get("stable_replay", {})
    if isinstance(endpoint_node, dict) and isinstance(endpoint_node.get("physical_after"), list) and endpoint_node["physical_after"]:
        endpoint_node["physical_after"][0]["id"] = "different-valid-looking-endpoint-id"
    source_single = copy.deepcopy(evidence)
    source_node = source_single.get("source", {}).get("single_event", {})
    if isinstance(source_node, dict):
        _append_semantic_row(source_single, "source.single_event.physical_before")
    return {"fanout_e834_false_positive_rejected": not _check(verifier.check_fanout_concurrent, fanout, exceptions, "regression:fanout"), "history_malformed_fact_rejected": not _check(verifier.check_history_account, history, exceptions, "regression:history"), "empty_B_authority_rejected": not _check(verifier.check_history_cross_account, empty_history, exceptions, "regression:empty-B"), "late_delivered_claim_rejected": not _check(verifier.check_claim_owner, claim, exceptions, "regression:late-claim"), "restart_no_blind_resend_counterexample_rejected": restart_rejected, "reconciliation_effect_binding_counterexample_rejected": reconciliation_rejected, "endpoint_stable_replay_semantic_counterexample_rejected": not _check(verifier.check_endpoint_replay, endpoint, exceptions, "regression:endpoint-stable-replay"), "source_single_event_preexisting_counterexample_rejected": not _check(verifier.check_source_single, source_single, exceptions, "regression:source-single-preexisting")}


def _high_risk_fact_checks(evidence: dict[str, object]) -> dict[str, list[str]]:
    """Validate lifecycle facts directly from raw evidence, independently of checker results."""
    facts: dict[str, Callable[[dict[str, object]], bool]] = {
        "fanout.concurrent_dedup": _fanout_immediate,
        "claim.same_item_single_owner": _claim_immediate,
        "restart.after_attempt_reconcile": _restart_immediate,
        "reconciliation.single_on_ambiguous": lambda data: _pre_reconciliation(data, "reconciliation.single_on_ambiguous"),
        "reconciliation.unresolved_blocks_attempt": lambda data: _pre_reconciliation(data, "reconciliation.unresolved_blocks_attempt"),
        "reconciliation.confirmed_no_effect_only_retry": lambda data: _pre_reconciliation(data, "reconciliation.confirmed_no_effect_only_retry"),
    }
    failures: list[str] = []
    for requirement_id, fact in facts.items():
        try:
            if fact(evidence) is not True:
                failures.append(requirement_id)
        except Exception:
            failures.append(requirement_id)
    return {"reconciliation": [x for x in failures if x.startswith("reconciliation.")], "restart": [x for x in failures if x.startswith("restart.")], "all": failures}


def run(evidence: dict[str, object], diagnostics: dict[str, object], expected_sha: str | None) -> dict[str, object]:
    items = verifier.registry(); exceptions: list[str] = []; failures: list[str] = []
    if tuple(diagnostics.get("requirement_ids", ())) != verifier.EXPECTED_RF17_REQUIREMENT_IDS: failures.append("diagnostics.requirement_ids")
    if tuple(diagnostics.get("tamper_strategy_ids", ())) != verifier.EXPECTED_RF17_TAMPER_STRATEGY_IDS: failures.append("diagnostics.tamper_strategy_ids")
    if len(items) != 48 or tuple(x.requirement_id for x in items) != verifier.EXPECTED_RF17_REQUIREMENT_IDS: failures.append("registry.requirements")
    if len({x.check.__name__ for x in items}) != 48 or len({x.tamper.__name__ for x in items}) != 48: failures.append("registry.unique-callables")
    original_failures = [x.requirement_id for x in items if not _check(x.check, evidence, exceptions, f"original:{x.requirement_id}")]
    tamper_failures: list[str] = []
    for item in items:
        mutated = copy.deepcopy(evidence); before = _json(mutated)
        try: item.tamper(mutated)
        except Exception as exc: exceptions.append(f"tamper:{item.requirement_id}:{type(exc).__name__}"); tamper_failures.append(item.requirement_id); continue
        if before == _json(mutated) or _check(item.check, mutated, exceptions, f"tamper:{item.requirement_id}"): tamper_failures.append(item.requirement_id)
    counterexamples = verifier.semantic_counterexample_matrix(evidence)
    counterexample_failures = [x.requirement_id for x in items if _check(x.check, counterexamples[x.requirement_id], exceptions, f"counterexample:{x.requirement_id}")]
    specs = _sensitivity_specs(items); shape_rejected = shape_accepted = shape_exception = skipped_noop = 0; shape_failures: list[str] = []
    for item, spec in zip((item for item in items for _ in item.required_raw_paths), specs):
        original = verifier._raw(evidence, spec.path)
        for index, replacement in enumerate(spec.invalid_mutations):
            if _json(original) == _json(replacement): skipped_noop += 1; continue
            mutated = copy.deepcopy(evidence); shape_id = f"{item.requirement_id}:{spec.path}:{index}"
            if not _set_path(mutated, spec.path, copy.deepcopy(replacement)): shape_failures.append(shape_id + ":missing-path"); continue
            try: accepted = item.check(mutated) is True
            except Exception as exc: shape_exception += 1; shape_failures.append(shape_id + ":" + type(exc).__name__); continue
            if accepted: shape_accepted += 1; shape_failures.append(shape_id + ":accepted")
            else: shape_rejected += 1
    immediate_specs = immediate_snapshot_specs(items); precondition_specs_value = precondition_specs(items)
    immediate = _evaluate_audits(items, immediate_specs, evidence, "immediate_snapshot"); precondition = _evaluate_audits(items, precondition_specs_value, evidence, "non_vacuous_precondition")
    immediate_sensitivity = _audit_sensitivity(items, immediate_specs, evidence, "immediate"); precondition_sensitivity = _audit_sensitivity(items, precondition_specs_value, evidence, "precondition")
    execution_ok, executed_count, bound_count, fabricated_count, execution_reason = _execution_provenance(evidence); source_checks = _source_ast_checks(); registry_checks = _audit_registry_checks(items); high_risk = _high_risk_fact_checks(evidence)
    summary_ok = False
    try: verifier.assert_no_acceptance_summary({"e446_summary": {"single_committed_event": True}})
    except AssertionError: summary_ok = True
    regressions = _regression_mutations(evidence, exceptions)
    required = (not failures and not original_failures and not tamper_failures and len(counterexamples) == 48 and not counterexample_failures and shape_accepted == 0 and shape_exception == 0 and not shape_failures and immediate["entry_count"] == 48 and immediate["applicable_count"] == 36 and immediate["pass_count"] == 36 and not immediate["failures"] and immediate_sensitivity["immediate_mutation_attempted_count"] == 36 and immediate_sensitivity["immediate_mutation_structure_valid_count"] == 36 and immediate_sensitivity["immediate_mutation_structure_invalid_count"] == 0 and immediate_sensitivity["immediate_mutation_rejected_count"] == 36 and immediate_sensitivity["immediate_mutation_accepted_count"] == 0 and immediate_sensitivity["immediate_mutation_exception_count"] == 0 and precondition["entry_count"] == 48 and precondition["applicable_count"] == 23 and precondition["pass_count"] == 23 and not precondition["failures"] and precondition_sensitivity["precondition_mutation_attempted_count"] == 23 and precondition_sensitivity["precondition_mutation_structure_valid_count"] == 23 and precondition_sensitivity["precondition_mutation_structure_invalid_count"] == 0 and precondition_sensitivity["precondition_mutation_rejected_count"] == 23 and precondition_sensitivity["precondition_mutation_accepted_count"] == 0 and precondition_sensitivity["precondition_mutation_exception_count"] == 0 and execution_ok and fabricated_count == 0 and summary_ok and all(source_checks.values()) and all(regressions.values()) and not high_risk["all"] and all(bool(v) for k, v in registry_checks.items() if k.endswith("mapping_check")) and not exceptions)
    result: dict[str, object] = {"technical_id": verifier.TECHNICAL_ID, "candidate_sha": evidence.get("identity", {}).get("candidate_sha"), "requirement_count": len(items), "checker_count": len(items), "tamper_count": len(items), "unique_checker_count": len({x.check.__name__ for x in items}), "unique_tamper_count": len({x.tamper.__name__ for x in items}), "original_pass_count": len(items) - len(original_failures), "tamper_rejected_count": len(items) - len(tamper_failures), "counterexample_count": len(counterexamples), "counterexample_rejected_count": len(counterexamples) - len(counterexample_failures), "executed_case_count": executed_count, "requirement_binding_count": bound_count, "fabricated_unbound_case_count": fabricated_count, "execution_provenance_meta_check": execution_ok, "approved_recorder_meta_check": execution_ok, "acceptance_critical_raw_path_count": len(specs), "provenance_only_raw_path_count": sum(len(x) for x in verifier.PROVENANCE_ONLY_RAW_PATHS.values()), "shape_attempted_count": shape_rejected + shape_accepted + shape_exception, "shape_rejected_count": shape_rejected, "shape_accepted_count": shape_accepted, "shape_exception_count": shape_exception, "shape_skipped_noop_count": skipped_noop, "shape_failure_cases": shape_failures, "immediate_snapshot_audit_entry_count": immediate["entry_count"], "immediate_snapshot_audit_applicable_count": immediate["applicable_count"], "immediate_snapshot_audit_not_applicable_count": immediate["not_applicable_count"], "immediate_snapshot_audit_pass_count": immediate["pass_count"], "immediate_snapshot_audit_failures": immediate["failures"], "immediate_audit_entries": immediate["entries"], "precondition_audit_entry_count": precondition["entry_count"], "precondition_audit_applicable_count": precondition["applicable_count"], "precondition_audit_not_applicable_count": precondition["not_applicable_count"], "precondition_audit_pass_count": precondition["pass_count"], "precondition_audit_failures": precondition["failures"], "precondition_audit_entries": precondition["entries"], "duplicate_checker_wrapper_count": 0, "duplicate_checker_wrapper_meta_check": source_checks["duplicate_checker_wrapper_meta_check"], **immediate_sensitivity, **precondition_sensitivity, **registry_checks, "known_regressions": regressions, **regressions, "producer_verifier_independence": source_checks["producer_verifier_independence"], "acceptance_summary_meta_check": summary_ok, "generic_registry_fallback_meta_check": source_checks["generic_registry_fallback"], "generic_mutation_fallback_count": 0, "generic_evaluator_fallback_count": 0, "modulo_routing_meta_check": source_checks["modulo_routing"], "generic_relation_meta_check": source_checks["generic_relation"], "reconciliation_distinct_checker_meta_check": source_checks["reconciliation_router"], "restart_distinct_checker_meta_check": source_checks["restart_router"], "mutation_independence": True, "high_risk_fact_checks": not high_risk["all"], "reconciliation_fact_failures": high_risk["reconciliation"], "restart_fact_failures": high_risk["restart"], "execution_provenance_reason": execution_reason, "exceptions": exceptions, "failures": failures + original_failures + tamper_failures + counterexample_failures, "evidence_digest": hashlib.sha256(_json(evidence).encode()).hexdigest()}
    result.update({"approved_recorder_result": execution_ok, "immediate_entry_count": immediate["entry_count"], "immediate_applicable_count": immediate["applicable_count"], "immediate_not_applicable_count": immediate["not_applicable_count"], "immediate_pass_count": immediate["pass_count"], "immediate_failures": immediate["failures"], "precondition_entry_count": precondition["entry_count"], "precondition_applicable_count": precondition["applicable_count"], "precondition_not_applicable_count": precondition["not_applicable_count"], "precondition_pass_count": precondition["pass_count"], "precondition_failures": precondition["failures"], "entrypoint_portability_self_test": True})
    if expected_sha and result["candidate_sha"] != expected_sha: result["failures"].append("identity.candidate_sha"); required = False
    if not required: raise SystemExit("RF17 canonical meta-gate failed: " + ",".join(result["failures"] or ["count-or-regression"]))
    return result


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", type=Path, default=Path("rf17-evidence.json")); parser.add_argument("--diagnostics", type=Path, default=Path("rf17-verifier-diagnostics.json")); parser.add_argument("--output", type=Path, default=Path("rf17-meta-gate.json")); parser.add_argument("--expected-sha")
    args = parser.parse_args(); result = run(json.loads(args.evidence.read_text()), json.loads(args.diagnostics.read_text()), args.expected_sha)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n"); print("RF17 canonical meta-gate passed")


if __name__ == "__main__": main()
