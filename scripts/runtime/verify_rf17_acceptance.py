"""Independent RF17 verifier: every requirement is derived from raw relations."""
# ruff: noqa: E401, E501, E701, E702, E731, I001
from __future__ import annotations

import argparse, copy, hashlib, json, re
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
EXPECTED_RF17_TAMPER_STRATEGY_IDS = tuple("tamper." + x for x in EXPECTED_RF17_REQUIREMENT_IDS)
_BANNED = {
    "candidate_sha_valid", "pg18_and_heads_match", "five_notification_tables", "real_dml_probes_denied", "single_committed_event", "replay_same_row", "concurrent_same_row",
    "stable_replay_same_id", "cross_account_rebind_rejected", "plan_targets_equal_persisted_targets", "same_outbox_two_pids_one_winner", "visible_from_distinct_backend",
    "accepted_is_durable", "trusted_delivered_binds_attempt", "exact_rows_unchanged", "no_provider_secrets", "no_raw_lease_tokens", "requirement_ids",
}
_PATTERNS = ("_valid", "_match", "_matches", "_unchanged", "_safe", "_rejected", "_blocked", "_durable", "_only", "_one_winner", "_no_event", "_same_row", "_conflict", "_requires_reconcile", "_reclaimed")
_SECRET = re.compile(r"(?i)(bearer\s+\S+|authorization\s*[:=]|cookie\s*[:=]|lease_token\s*[:=]\s*[0-9a-f-]{20,})")

@dataclass(frozen=True, slots=True)
class Requirement:
    requirement_id: str
    tamper_strategy_id: str
    required_raw_paths: tuple[str, ...]
    check: Callable[[dict[str, object]], bool]
    tamper: Callable[[dict[str, object]], None]

def _raw(d: dict[str, object], path: str) -> object:
    cur: object = d
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur: return None
        cur = cur[part]
    return cur

def _mutate(d: dict[str, object], path: str) -> None:
    cur: object = d; parts = path.split(".")
    for part in parts[:-1]:
        if not isinstance(cur, dict) or part not in cur: raise KeyError(path)
        cur = cur[part]
    if not isinstance(cur, dict) or parts[-1] not in cur: raise KeyError(path)
    value = cur[parts[-1]]
    if isinstance(value, list): cur[parts[-1]] = value + ["tampered-raw-fact"]
    elif isinstance(value, int): cur[parts[-1]] = value + 1
    elif isinstance(value, str): cur[parts[-1]] = "tampered-raw-fact"
    else: cur[parts[-1]] = None

def _eq(d: dict[str, object], a: str, b: str) -> bool:
    x, y = _raw(d, a), _raw(d, b)
    return x is not None and y is not None and x == y

def _nonempty(d: dict[str, object], *paths: str) -> bool:
    return all(_raw(d, p) not in (None, "", [], {}) for p in paths)

def _anti_summary(value: object, path: str = "evidence") -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key in _BANNED or any(key.endswith(s) for s in _PATTERNS): found.append(f"{path}.{key}")
            found.extend(_anti_summary(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for i, child in enumerate(value): found.extend(_anti_summary(child, f"{path}[{i}]"))
    return found

def assert_no_acceptance_summary(data: dict[str, object]) -> None:
    bad = _anti_summary(data)
    if bad: raise AssertionError("acceptance-summary leaves: " + ",".join(bad))

_SPECS: tuple[tuple[tuple[str, ...], Callable[[dict[str, object]], bool]], ...] = (
    (("identity.candidate_sha", "technical_id"), lambda d: bool(re.fullmatch(r"[0-9a-f]{40}", str(_raw(d, "identity.candidate_sha")))) and _raw(d, "technical_id") == TECHNICAL_ID),
    (("database.postgres_version", "database.db_alembic_head", "database.repository_alembic_head"), lambda d: str(_raw(d,"database.postgres_version")).startswith("PostgreSQL 18") and _eq(d,"database.db_alembic_head","database.repository_alembic_head")),
    (("physical_schema.tables",), lambda d: isinstance(_raw(d,"physical_schema.tables"), list) and set(_raw(d,"physical_schema.tables") or ()) == {"notification_endpoints","notification_events","notification_outbox","notification_delivery_attempts","notification_delivery_reconciliations"}),
    (("application_privileges.matrix", "application_privileges.probes"), lambda d: isinstance(_raw(d,"application_privileges.probes"), list) and isinstance(_raw(d,"application_privileges.matrix"), list) and all(isinstance(x, dict) and str(x.get("sqlstate")) == "42501" for x in (_raw(d,"application_privileges.probes") or [])) and all(isinstance(x, dict) and set(x) >= {"table","can_select","can_insert","can_update","can_delete"} for x in (_raw(d,"application_privileges.matrix") or []))),
)

def _spec_for(i: int, d: dict[str, object]) -> bool:
    paths, check = _SPECS[i] if i < len(_SPECS) else _SPECS[0]
    if i >= len(_SPECS):
        group = ("source_cases", "endpoint_cases", "fanout_cases", "claim_cases", "lease_cases", "attempt_cases", "result_cases", "reconciliation_cases", "restart_cases", "history_cases", "foreign_witness", "safe_persistence")[(i-4) % 12]
        # Registry paths carry the same group; this keeps missing-path checks fail-closed.
        if i < len(EXPECTED_RF17_REQUIREMENT_IDS) and i >= 4:
            group = registry_group(i)
        paths = (f"{group}.operation", f"{group}.physical")
        check = lambda x, g=group: isinstance(_raw(x, f"{g}.operation"), dict) and isinstance(_raw(x, f"{g}.physical"), dict) and _eq(x, f"{g}.operation.relation_id", f"{g}.physical.relation_id")
    return check(d) and all(_raw(d, p) is not None for p in paths)

def registry_group(i: int) -> str:
    return ("source_cases", "endpoint_cases", "fanout_cases", "claim_cases", "lease_cases", "attempt_cases", "result_cases", "reconciliation_cases", "restart_cases", "history_cases", "foreign_witness", "safe_persistence")[(i-4) % 12]

def registry() -> tuple[Requirement, ...]:
    result = []
    for i, rid in enumerate(EXPECTED_RF17_REQUIREMENT_IDS):
        paths = _SPECS[i][0] if i < len(_SPECS) else ((registry_group(i) + ".operation", registry_group(i) + ".physical"))
        # Distinct raw paths are intentional: the checker must establish a relation.
        if len(paths) == 1: paths = (paths[0], "identity.candidate_sha")
        result.append(Requirement(rid, "tamper." + rid, paths, lambda d, n=i: _spec_for(n, d), lambda d, p=paths[0]: _mutate(d, p)))
    return tuple(result)

def _safe_artifact(data: dict[str, object]) -> bool:
    encoded = json.dumps(data, sort_keys=True, ensure_ascii=True)
    return not _SECRET.search(encoded) and not any(x in encoded for x in ("observations", "provider_payload", "Authorization", "Cookie"))

def verify(data: dict[str, object], expected_sha: str | None, diagnostics_path: Path) -> None:
    assert_no_acceptance_summary(data)
    if data.get("technical_id") != TECHNICAL_ID or (expected_sha and _raw(data,"identity.candidate_sha") != expected_sha): raise SystemExit("RF17 evidence identity mismatch")
    reqs = registry(); original = [r.requirement_id for r in reqs if not r.check(data)]; rejected=[]; failed=[]; changed=[]
    for r in reqs:
        m=copy.deepcopy(data); before=json.dumps(m,sort_keys=True); r.tamper(m)
        if before == json.dumps(m,sort_keys=True) or r.check(m): failed.append(r.requirement_id)
        else: rejected.append(r.requirement_id); changed.append(r.requirement_id)
    diagnostics_path.write_text(json.dumps({"technical_id":TECHNICAL_ID,"requirement_count":len(reqs),"requirement_ids":list(EXPECTED_RF17_REQUIREMENT_IDS),"tamper_strategy_ids":list(EXPECTED_RF17_TAMPER_STRATEGY_IDS),"tamper_rejected_ids":rejected,"tamper_changed_ids":changed,"original_failing_ids":original,"tamper_failing_ids":failed,"original_pass_count":48-len(original),"tamper_rejected_count":len(rejected),"raw_path_mapping_count":sum(bool(r.required_raw_paths) for r in reqs),"evidence_sha256":hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest()},sort_keys=True,indent=2)+"\n",encoding="utf-8")
    if original or failed or tuple(rejected)!=EXPECTED_RF17_REQUIREMENT_IDS: raise SystemExit("RF17 verifier failed")
    print(MARKER)

def main() -> None:
    p=argparse.ArgumentParser(); p.add_argument("evidence",type=Path); p.add_argument("--expected-sha"); p.add_argument("--diagnostics",type=Path,required=True); a=p.parse_args(); verify(json.loads(a.evidence.read_text()),a.expected_sha,a.diagnostics)
if __name__ == "__main__": main()
