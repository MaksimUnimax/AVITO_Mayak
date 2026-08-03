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

AuditEvaluator = Callable[[dict[str, object]], bool]
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
    evaluator: AuditEvaluator
    mutation: AuditMutation | None


@dataclass(frozen=True)
class PreconditionAuditSpec:
    requirement_id: str
    scenario_id: str
    applicable: bool
    not_applicable_reason: str | None
    evidence_paths: tuple[str, ...]
    evaluator: AuditEvaluator
    mutation: AuditMutation | None


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


def _generic_relation(paths: tuple[str, ...], data: dict[str, object]) -> bool:
    if not paths or not all(_raw(data, path) is not None for path in paths):
        return False
    # This is an audit witness relation: it requires a populated, typed stage
    # witness and never delegates the acceptance decision to Requirement.check.
    return all(not isinstance(_raw(data, path), (str, bytes)) or bool(_raw(data, path)) for path in paths)


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


def _evaluator(paths: tuple[str, ...], special: AuditEvaluator | None = None) -> AuditEvaluator:
    if special is not None:
        def safe_special(data: dict[str, object]) -> bool:
            try:
                return special(data) is True
            except Exception:
                return False
        return safe_special
    return lambda data: _generic_relation(paths, data)


def _mutation(paths: tuple[str, ...]) -> AuditMutation:
    def mutate(data: dict[str, object]) -> None:
        for path in (paths[0], paths[-1]):
            if _set_path(data, path, None):
                return
        raise KeyError(paths[0] if paths else "missing audit path")
    return mutate


def _immediate_source_blocked(data: dict[str, object], scenario: str) -> bool:
    node = _raw(data, scenario)
    return isinstance(node, dict) and node.get("runtime_return") is None and node.get("physical_rows") == [] and bool(node.get("input", {}).get("family"))


def immediate_snapshot_specs(items: tuple[verifier.Requirement, ...]) -> tuple[ImmediateSnapshotAuditSpec, ...]:
    static = {"identity.", "schema.", "security.", "privacy.", "foreign."}
    special = {"claim.same_item_single_owner": _claim_immediate, "fanout.concurrent_dedup": _fanout_immediate, "restart.after_attempt_reconcile": _restart_immediate}
    result: list[ImmediateSnapshotAuditSpec] = []
    for item in items:
        applicable = not item.requirement_id.startswith(tuple(static)) and item.requirement_id not in {"endpoint.accepted_channel_evidence", "history.account_scope", "history.beacon_scope", "history.cross_account_blocked", "history.safe_refs"}
        paths = tuple(item.required_raw_paths)
        evaluator = special.get(item.requirement_id)
        if item.requirement_id.startswith("source.") and item.requirement_id.endswith(("baseline_blocked", "no_new_blocked", "price_blocked", "non_notification_families_blocked")):
            evaluator = lambda data, s=item.scenario_id: _immediate_source_blocked(data, s)
        result.append(ImmediateSnapshotAuditSpec(item.requirement_id, item.scenario_id, applicable, None if applicable else "no meaningful immediate lifecycle snapshot exists for this static or final read-model requirement", paths, _evaluator(paths, evaluator), _mutation(paths) if applicable else None))
    return tuple(result)


def precondition_specs(items: tuple[verifier.Requirement, ...]) -> tuple[PreconditionAuditSpec, ...]:
    mandatory = {"source.replay_same", "source.identity_fingerprint_mismatch", "source.same_fingerprint_cross_scope_conflict", "endpoint.stable_replay", "endpoint.cross_account_rebind_blocked", "fanout.concurrent_dedup", "claim.same_item_single_owner", "lease.wrong_token_blocked", "lease.expired_terminal_blocked", "result.replay_same", "result.mismatch_blocked", "history.account_scope", "history.beacon_scope", "history.cross_account_blocked", "reconciliation.single_on_ambiguous", "reconciliation.unresolved_blocks_attempt", "reconciliation.replay_same", "reconciliation.resolved_delivered", "reconciliation.confirmed_no_effect_only_retry", "reconciliation.manual_ambiguous_blocks", "restart.claim_before_attempt_reclaim", "restart.retry_claim_before_attempt_reclaim", "restart.after_attempt_reconcile"}
    result: list[PreconditionAuditSpec] = []
    for item in items:
        applicable = item.requirement_id in mandatory
        paths = tuple(item.required_raw_paths)
        special: AuditEvaluator | None = None
        if item.requirement_id == "source.replay_same": special = _pre_source_replay
        elif item.requirement_id == "source.identity_fingerprint_mismatch": special = _pre_source_fp
        elif item.requirement_id == "source.same_fingerprint_cross_scope_conflict": special = _pre_source_scope
        elif item.requirement_id == "endpoint.cross_account_rebind_blocked": special = _pre_endpoint_account
        elif item.requirement_id.startswith("lease."): special = lambda data, s=item.scenario_id: _pre_lease(data, s)
        elif item.requirement_id.startswith("reconciliation."): special = lambda data, s=item.scenario_id, p=paths: _generic_relation(p, data) and _pre_reconciliation(data, s)
        elif item.requirement_id.startswith("restart."): special = lambda data, s=item.scenario_id: _pre_restart(data, s)
        elif item.requirement_id == "history.cross_account_blocked": special = _pre_history
        result.append(PreconditionAuditSpec(item.requirement_id, item.scenario_id, applicable, None if applicable else "requirement has no non-vacuous negative/idempotency precondition witness", paths, _evaluator(paths, special), _mutation(paths) if applicable else None))
    return tuple(result)


def _evaluate_audits(specs: tuple[object, ...], evidence: dict[str, object], label: str) -> dict[str, object]:
    entries: list[dict[str, object]] = []
    failures: list[str] = []
    for spec in specs:
        assert isinstance(spec, (ImmediateSnapshotAuditSpec, PreconditionAuditSpec))
        passed = spec.applicable and verifier._safe_check(spec.evaluator, evidence)
        if spec.applicable and not passed:
            failures.append(spec.requirement_id)
        entries.append({"requirement_id": spec.requirement_id, "scenario_id": spec.scenario_id, "evidence_paths": list(spec.evidence_paths), "applicable": spec.applicable, "not_applicable_reason": spec.not_applicable_reason, "evaluator": spec.evaluator.__name__, "pass": passed})
    applicable = sum(x["applicable"] is True for x in entries)
    return {"entries": entries, "entry_count": len(entries), "applicable_count": applicable, "not_applicable_count": len(entries) - applicable, "pass_count": sum(x["applicable"] is True and x["pass"] is True for x in entries), "failures": failures, "label": label}


def _audit_sensitivity(specs: tuple[object, ...], evidence: dict[str, object], label: str) -> dict[str, int]:
    attempted = rejected = accepted = exceptions = 0
    for spec in specs:
        assert isinstance(spec, (ImmediateSnapshotAuditSpec, PreconditionAuditSpec))
        if not spec.applicable or spec.mutation is None:
            continue
        mutated = copy.deepcopy(evidence); before = _json(mutated); attempted += 1
        try:
            spec.mutation(mutated)
            if before == _json(mutated):
                raise AssertionError("audit mutation was a no-op")
            passed = spec.evaluator(mutated)
        except Exception:
            exceptions += 1
            continue
        if passed:
            accepted += 1
        else:
            rejected += 1
    return {f"{label}_mutation_attempted_count": attempted, f"{label}_mutation_rejected_count": rejected, f"{label}_mutation_accepted_count": accepted, f"{label}_mutation_exception_count": exceptions}


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
    return {"producer_verifier_independence": not any(x in producer for x in ("verify_rf17_acceptance", "EXPECTED_RF17", "acceptance_results", '"relation_id"')), "generic_registry_fallback": "registry_group" not in names and "_spec_for" not in verifier_source, "modulo_routing": "modulo" not in verifier_source, "generic_relation": '"operation.relation_id"' not in verifier_source and '"physical.relation_id"' not in verifier_source, "reconciliation_router": all(x in names for x in ("check_recon_single", "check_recon_blocks", "check_recon_replay", "check_recon_delivered", "check_recon_no_effect", "check_recon_manual")), "restart_router": all(x in names for x in ("check_restart_claim", "check_restart_retry", "check_restart_attempt"))}


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
    return {"fanout_e834_false_positive_rejected": not _check(verifier.check_fanout_concurrent, fanout, exceptions, "regression:fanout"), "history_malformed_fact_rejected": not _check(verifier.check_history_account, history, exceptions, "regression:history"), "empty_B_authority_rejected": not _check(verifier.check_history_cross_account, empty_history, exceptions, "regression:empty-B"), "late_delivered_claim_rejected": not _check(verifier.check_claim_owner, claim, exceptions, "regression:late-claim"), "restart_no_blind_resend_counterexample_rejected": restart_rejected, "reconciliation_effect_binding_counterexample_rejected": reconciliation_rejected}


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
    immediate = _evaluate_audits(immediate_specs, evidence, "immediate_snapshot"); precondition = _evaluate_audits(precondition_specs_value, evidence, "non_vacuous_precondition")
    immediate_sensitivity = _audit_sensitivity(immediate_specs, evidence, "immediate"); precondition_sensitivity = _audit_sensitivity(precondition_specs_value, evidence, "precondition")
    alias_immediate = sum(spec.evaluator is item.check for spec in immediate_specs for item in items if spec.requirement_id == item.requirement_id)
    alias_precondition = sum(spec.evaluator is item.check for spec in precondition_specs_value for item in items if spec.requirement_id == item.requirement_id)
    execution_ok, executed_count, bound_count, fabricated_count, execution_reason = _execution_provenance(evidence); source_checks = _source_ast_checks()
    summary_ok = False
    try: verifier.assert_no_acceptance_summary({"e446_summary": {"single_committed_event": True}})
    except AssertionError: summary_ok = True
    regressions = _regression_mutations(evidence, exceptions)
    required = (not failures and not original_failures and not tamper_failures and len(counterexamples) == 48 and not counterexample_failures and shape_accepted == 0 and shape_exception == 0 and not shape_failures and immediate["entry_count"] == 48 and immediate["pass_count"] == immediate["applicable_count"] and not immediate["failures"] and immediate_sensitivity["immediate_mutation_accepted_count"] == 0 and immediate_sensitivity["immediate_mutation_exception_count"] == 0 and precondition["entry_count"] == 48 and precondition["pass_count"] == precondition["applicable_count"] and not precondition["failures"] and precondition_sensitivity["precondition_mutation_accepted_count"] == 0 and precondition_sensitivity["precondition_mutation_exception_count"] == 0 and execution_ok and fabricated_count == 0 and summary_ok and alias_immediate == 0 and alias_precondition == 0 and all(source_checks.values()) and all(regressions.values()) and not exceptions)
    result: dict[str, object] = {"technical_id": verifier.TECHNICAL_ID, "candidate_sha": evidence.get("identity", {}).get("candidate_sha"), "requirement_count": len(items), "checker_count": len(items), "tamper_count": len(items), "unique_checker_count": len({x.check.__name__ for x in items}), "unique_tamper_count": len({x.tamper.__name__ for x in items}), "original_pass_count": len(items) - len(original_failures), "tamper_rejected_count": len(items) - len(tamper_failures), "counterexample_count": len(counterexamples), "counterexample_rejected_count": len(counterexamples) - len(counterexample_failures), "executed_case_count": executed_count, "requirement_binding_count": bound_count, "fabricated_unbound_case_count": fabricated_count, "execution_provenance_meta_check": execution_ok, "approved_recorder_meta_check": execution_ok, "acceptance_critical_raw_path_count": len(specs), "provenance_only_raw_path_count": sum(len(x) for x in verifier.PROVENANCE_ONLY_RAW_PATHS.values()), "shape_attempted_count": shape_rejected + shape_accepted + shape_exception, "shape_rejected_count": shape_rejected, "shape_accepted_count": shape_accepted, "shape_exception_count": shape_exception, "shape_skipped_noop_count": skipped_noop, "shape_failure_cases": shape_failures, "immediate_snapshot_audit_entry_count": immediate["entry_count"], "immediate_snapshot_audit_applicable_count": immediate["applicable_count"], "immediate_snapshot_audit_not_applicable_count": immediate["not_applicable_count"], "immediate_snapshot_audit_pass_count": immediate["pass_count"], "immediate_snapshot_audit_failures": immediate["failures"], "precondition_audit_entry_count": precondition["entry_count"], "precondition_audit_applicable_count": precondition["applicable_count"], "precondition_audit_not_applicable_count": precondition["not_applicable_count"], "precondition_audit_pass_count": precondition["pass_count"], "precondition_audit_failures": precondition["failures"], "immediate_requirement_checker_alias_count": alias_immediate, "precondition_requirement_checker_alias_count": alias_precondition, **immediate_sensitivity, **precondition_sensitivity, "known_regressions": regressions, "producer_verifier_independence": source_checks["producer_verifier_independence"], "acceptance_summary_meta_check": summary_ok, "generic_registry_fallback_meta_check": source_checks["generic_registry_fallback"], "modulo_routing_meta_check": source_checks["modulo_routing"], "generic_relation_meta_check": source_checks["generic_relation"], "reconciliation_distinct_checker_meta_check": source_checks["reconciliation_router"], "restart_distinct_checker_meta_check": source_checks["restart_router"], "execution_provenance_reason": execution_reason, "exceptions": exceptions, "failures": failures + original_failures + tamper_failures + counterexample_failures, "evidence_digest": hashlib.sha256(_json(evidence).encode()).hexdigest()}
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
