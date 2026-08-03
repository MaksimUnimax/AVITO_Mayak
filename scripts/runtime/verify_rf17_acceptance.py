"""Independent RF17 verifier.

The producer is intentionally only a PostgreSQL/domain recorder.  This file
owns the canonical registry and derives each result from a distinct raw path.
"""
from __future__ import annotations

# ruff: noqa: E501
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
    "identity.candidate_sha", "identity.pg18_db_repo_head", "schema.physical_five_tables",
    "security.app_role_notification_only", "source.single_event", "source.replay_same",
    "source.concurrent_same", "source.identity_fingerprint_mismatch", "source.same_fingerprint_cross_scope_conflict",
    "source.baseline_blocked", "source.no_new_blocked", "source.price_blocked", "source.non_notification_families_blocked",
    "source.unsafe_payload_blocked", "endpoint.stable_replay", "endpoint.cross_account_rebind_blocked",
    "endpoint.accepted_channel_evidence", "fanout.explicit_targets", "fanout.empty_blocked", "fanout.concurrent_dedup",
    "claim.same_item_single_owner", "claim.deterministic_order", "lease.wrong_token_blocked", "lease.expired_terminal_blocked",
    "attempt.unique_number", "transaction.attempt_committed_before_adapter", "transaction.adapter_outside_db_transaction",
    "result.definite_success", "result.not_human_read", "result.definite_failure_no_retry", "result.replay_same",
    "result.mismatch_blocked", "reconciliation.single_on_ambiguous", "reconciliation.unresolved_blocks_attempt",
    "reconciliation.replay_same", "reconciliation.resolved_delivered", "reconciliation.confirmed_no_effect_only_retry",
    "reconciliation.manual_ambiguous_blocks", "restart.claim_before_attempt_reclaim", "restart.retry_claim_before_attempt_reclaim",
    "restart.after_attempt_reconcile", "history.account_scope", "history.beacon_scope", "history.cross_account_blocked",
    "history.safe_refs", "foreign.authority_unchanged", "privacy.no_raw_provider_values", "privacy.no_raw_lease_values",
)
EXPECTED_RF17_TAMPER_STRATEGY_IDS = tuple("tamper." + item for item in EXPECTED_RF17_REQUIREMENT_IDS)
_SECRET = re.compile(r"(?i)(bearer\s+\S+|authorization\s*[:=]|cookie\s*[:=]|lease_token\s*[:=]\s*[0-9a-f-]{20,})")


@dataclass(frozen=True, slots=True)
class Requirement:
    requirement_id: str
    tamper_strategy_id: str
    required_raw_paths: tuple[str, ...]
    check: Callable[[dict[str, object]], bool]
    tamper: Callable[[dict[str, object]], None]


def _raw(data: dict[str, object], path: str) -> object:
    current: object = data
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def _present(data: dict[str, object], path: str) -> bool:
    return _raw(data, path) is True


def _flip(data: dict[str, object], path: str) -> None:
    current: object = data
    parts = path.split(".")
    for part in parts[:-1]:
        if not isinstance(current, dict) or part not in current:
            raise KeyError(path)
        current = current[part]
    if not isinstance(current, dict) or parts[-1] not in current:
        raise KeyError(path)
    value = current[parts[-1]]
    if type(value) is bool:
        current[parts[-1]] = not value
    elif isinstance(value, int):
        current[parts[-1]] = value + 1
    elif isinstance(value, list):
        current[parts[-1]] = value + ["tampered-raw-fact"]
    else:
        current[parts[-1]] = "tampered-raw-fact"


def _check_identity_candidate_sha(d: dict[str, object]) -> bool: return _present(d, "identity.candidate_sha_valid")
def _check_identity_heads(d: dict[str, object]) -> bool: return _present(d, "database.pg18_and_heads_match")
def _check_schema_tables(d: dict[str, object]) -> bool: return _present(d, "physical_schema.five_notification_tables")
def _check_security_privileges(d: dict[str, object]) -> bool: return _present(d, "application_privileges.real_dml_probes_denied")
def _check_source_single(d: dict[str, object]) -> bool: return _present(d, "source_cases.single_committed_event")
def _check_source_replay(d: dict[str, object]) -> bool: return _present(d, "source_cases.replay_same_row")
def _check_source_concurrent(d: dict[str, object]) -> bool: return _present(d, "source_cases.concurrent_same_row")
def _check_source_fingerprint(d: dict[str, object]) -> bool: return _present(d, "source_cases.fingerprint_conflict_sqlstate")
def _check_source_scope(d: dict[str, object]) -> bool: return _present(d, "source_cases.same_fingerprint_scope_conflict")
def _check_baseline(d: dict[str, object]) -> bool: return _present(d, "source_cases.baseline_no_event")
def _check_no_new(d: dict[str, object]) -> bool: return _present(d, "source_cases.no_new_no_event")
def _check_price(d: dict[str, object]) -> bool: return _present(d, "source_cases.price_no_event")
def _check_families(d: dict[str, object]) -> bool: return _present(d, "source_cases.non_notification_no_event")
def _check_payload(d: dict[str, object]) -> bool: return _present(d, "source_cases.unsafe_payload_rejected")
def _check_endpoint_replay(d: dict[str, object]) -> bool: return _present(d, "endpoint_cases.stable_replay_same_id")
def _check_endpoint_scope(d: dict[str, object]) -> bool: return _present(d, "endpoint_cases.cross_account_rebind_rejected")
def _check_endpoint_semantics(d: dict[str, object]) -> bool: return _present(d, "endpoint_cases.accepted_channel_class")
def _check_fanout_targets(d: dict[str, object]) -> bool: return _present(d, "fanout_cases.plan_targets_equal_persisted_targets")
def _check_fanout_empty(d: dict[str, object]) -> bool: return _present(d, "fanout_cases.empty_rejected")
def _check_fanout_dedup(d: dict[str, object]) -> bool: return _present(d, "fanout_cases.concurrent_unique_rows")
def _check_claim_owner(d: dict[str, object]) -> bool: return _present(d, "claim_cases.same_outbox_two_pids_one_winner")
def _check_claim_order(d: dict[str, object]) -> bool: return _present(d, "claim_cases.order_matches_available_at_id")
def _check_lease_token(d: dict[str, object]) -> bool: return _present(d, "lease_cases.wrong_fingerprint_sqlstate")
def _check_lease_expired(d: dict[str, object]) -> bool: return _present(d, "lease_cases.expired_with_attempt_reconcile")
def _check_attempt_unique(d: dict[str, object]) -> bool: return _present(d, "attempt_cases.unique_numbers")
def _check_tx_visible(d: dict[str, object]) -> bool: return _present(d, "attempt_cases.visible_from_distinct_backend")
def _check_tx_separate(d: dict[str, object]) -> bool: return _present(d, "attempt_cases.adapter_backend_distinct")
def _check_result_success(d: dict[str, object]) -> bool: return _present(d, "result_cases.accepted_is_durable")
def _check_result_read(d: dict[str, object]) -> bool: return _present(d, "result_cases.accepted_not_human_read")
def _check_result_failure(d: dict[str, object]) -> bool: return _present(d, "result_cases.failure_no_second_attempt")
def _check_result_replay(d: dict[str, object]) -> bool: return _present(d, "result_cases.same_outcome_replay")
def _check_result_mismatch(d: dict[str, object]) -> bool: return _present(d, "result_cases.changed_outcome_conflict")
def _check_rec_single(d: dict[str, object]) -> bool: return _present(d, "reconciliation_cases.one_unresolved_for_ambiguity")
def _check_rec_block(d: dict[str, object]) -> bool: return _present(d, "reconciliation_cases.unresolved_blocks_new_attempt")
def _check_rec_replay(d: dict[str, object]) -> bool: return _present(d, "reconciliation_cases.same_ambiguity_replay_one_row")
def _check_rec_delivered(d: dict[str, object]) -> bool: return _present(d, "reconciliation_cases.trusted_delivered_binds_attempt")
def _check_rec_retry(d: dict[str, object]) -> bool: return _present(d, "reconciliation_cases.confirmed_no_effect_retry_only")
def _check_rec_manual(d: dict[str, object]) -> bool: return _present(d, "reconciliation_cases.manual_still_ambiguous_blocks")
def _check_restart_claim(d: dict[str, object]) -> bool: return _present(d, "restart_cases.first_claim_reclaimed_by_new_backend")
def _check_restart_retry(d: dict[str, object]) -> bool: return _present(d, "restart_cases.retry_claim_reclaimed_after_history")
def _check_restart_attempt(d: dict[str, object]) -> bool: return _present(d, "restart_cases.current_attempt_requires_reconcile")
def _check_history_account(d: dict[str, object]) -> bool: return _present(d, "history_cases.actor_equals_account")
def _check_history_beacon(d: dict[str, object]) -> bool: return _present(d, "history_cases.beacon_filter_authorized_rows_only")
def _check_history_foreign(d: dict[str, object]) -> bool: return _present(d, "history_cases.foreign_beacon_empty")
def _check_history_refs(d: dict[str, object]) -> bool: return _present(d, "history_cases.safe_listing_refs_only")
def _check_foreign(d: dict[str, object]) -> bool: return _present(d, "foreign_witness.exact_rows_unchanged")
def _check_provider_privacy(d: dict[str, object]) -> bool: return _present(d, "safe_persistence.no_provider_secrets")
def _check_lease_privacy(d: dict[str, object]) -> bool: return _present(d, "safe_persistence.no_raw_lease_tokens")


_CHECKS = (
    _check_identity_candidate_sha, _check_identity_heads, _check_schema_tables, _check_security_privileges,
    _check_source_single, _check_source_replay, _check_source_concurrent, _check_source_fingerprint,
    _check_source_scope, _check_baseline, _check_no_new, _check_price, _check_families, _check_payload,
    _check_endpoint_replay, _check_endpoint_scope, _check_endpoint_semantics, _check_fanout_targets,
    _check_fanout_empty, _check_fanout_dedup, _check_claim_owner, _check_claim_order, _check_lease_token,
    _check_lease_expired, _check_attempt_unique, _check_tx_visible, _check_tx_separate, _check_result_success,
    _check_result_read, _check_result_failure, _check_result_replay, _check_result_mismatch, _check_rec_single,
    _check_rec_block, _check_rec_replay, _check_rec_delivered, _check_rec_retry, _check_rec_manual,
    _check_restart_claim, _check_restart_retry, _check_restart_attempt, _check_history_account,
    _check_history_beacon, _check_history_foreign, _check_history_refs, _check_foreign, _check_provider_privacy,
    _check_lease_privacy,
)
_PATHS = (
    "identity.candidate_sha_valid", "database.pg18_and_heads_match", "physical_schema.five_notification_tables",
    "application_privileges.real_dml_probes_denied", "source_cases.single_committed_event", "source_cases.replay_same_row",
    "source_cases.concurrent_same_row", "source_cases.fingerprint_conflict_sqlstate", "source_cases.same_fingerprint_scope_conflict",
    "source_cases.baseline_no_event", "source_cases.no_new_no_event", "source_cases.price_no_event", "source_cases.non_notification_no_event",
    "source_cases.unsafe_payload_rejected", "endpoint_cases.stable_replay_same_id", "endpoint_cases.cross_account_rebind_rejected",
    "endpoint_cases.accepted_channel_class", "fanout_cases.plan_targets_equal_persisted_targets", "fanout_cases.empty_rejected",
    "fanout_cases.concurrent_unique_rows", "claim_cases.same_outbox_two_pids_one_winner", "claim_cases.order_matches_available_at_id",
    "lease_cases.wrong_fingerprint_sqlstate", "lease_cases.expired_with_attempt_reconcile", "attempt_cases.unique_numbers",
    "attempt_cases.visible_from_distinct_backend", "attempt_cases.adapter_backend_distinct", "result_cases.accepted_is_durable",
    "result_cases.accepted_not_human_read", "result_cases.failure_no_second_attempt", "result_cases.same_outcome_replay",
    "result_cases.changed_outcome_conflict", "reconciliation_cases.one_unresolved_for_ambiguity", "reconciliation_cases.unresolved_blocks_new_attempt",
    "reconciliation_cases.same_ambiguity_replay_one_row", "reconciliation_cases.trusted_delivered_binds_attempt",
    "reconciliation_cases.confirmed_no_effect_retry_only", "reconciliation_cases.manual_still_ambiguous_blocks",
    "restart_cases.first_claim_reclaimed_by_new_backend", "restart_cases.retry_claim_reclaimed_after_history",
    "restart_cases.current_attempt_requires_reconcile", "history_cases.actor_equals_account", "history_cases.beacon_filter_authorized_rows_only",
    "history_cases.foreign_beacon_empty", "history_cases.safe_listing_refs_only", "foreign_witness.exact_rows_unchanged",
    "safe_persistence.no_provider_secrets", "safe_persistence.no_raw_lease_tokens",
)


def registry() -> tuple[Requirement, ...]:
    return tuple(Requirement(rid, "tamper." + rid, (path,), check, lambda d, p=path: _flip(d, p)) for rid, path, check in zip(EXPECTED_RF17_REQUIREMENT_IDS, _PATHS, _CHECKS, strict=True))


def _safe_artifact(data: dict[str, object]) -> bool:
    encoded = json.dumps(data, sort_keys=True, ensure_ascii=True)
    return _SECRET.search(encoded) is None and not any(token in encoded for token in ("observations", "provider_payload", "Authorization", "Cookie"))


def verify(data: dict[str, object], expected_sha: str | None, diagnostics_path: Path) -> None:
    if data.get("technical_id") != TECHNICAL_ID or (expected_sha is not None and data.get("identity", {}).get("candidate_sha") != expected_sha):
        raise SystemExit("RF17 evidence identity mismatch")
    requirements = registry()
    original_failures = [item.requirement_id for item in requirements if not item.check(data)]
    tamper_rejected: list[str] = []
    tamper_failures: list[str] = []
    tamper_changed: list[str] = []
    for item in requirements:
        mutated = copy.deepcopy(data)
        before = json.dumps(mutated, sort_keys=True)
        try:
            item.tamper(mutated)
            if before == json.dumps(mutated, sort_keys=True):
                tamper_failures.append(item.requirement_id)
            elif not item.check(mutated):
                tamper_rejected.append(item.requirement_id)
                tamper_changed.append(item.requirement_id)
            else:
                tamper_failures.append(item.requirement_id)
        except Exception:
            tamper_failures.append(item.requirement_id)
    diagnostics = {
        "technical_id": TECHNICAL_ID, "requirement_count": len(requirements),
        "requirement_ids": list(EXPECTED_RF17_REQUIREMENT_IDS), "tamper_strategy_ids": list(EXPECTED_RF17_TAMPER_STRATEGY_IDS),
        "tamper_rejected_ids": tamper_rejected, "tamper_changed_ids": tamper_changed,
        "original_failing_ids": original_failures, "tamper_failing_ids": tamper_failures,
        "original_pass_count": len(requirements) - len(original_failures), "tamper_rejected_count": len(tamper_rejected),
        "raw_path_mapping_count": sum(bool(item.required_raw_paths) for item in requirements),
        "evidence_sha256": hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest(),
    }
    diagnostics_path.write_text(json.dumps(diagnostics, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    if original_failures or tamper_failures or tuple(tamper_rejected) != EXPECTED_RF17_REQUIREMENT_IDS or len(requirements) != 48:
        raise SystemExit("RF17 verifier failed")
    print(MARKER)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence", type=Path)
    parser.add_argument("--expected-sha")
    parser.add_argument("--diagnostics", type=Path, required=True)
    args = parser.parse_args()
    verify(json.loads(args.evidence.read_text(encoding="utf-8")), args.expected_sha, args.diagnostics)


if __name__ == "__main__":
    main()
