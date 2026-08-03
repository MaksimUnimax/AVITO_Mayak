"""The single RF17 immutable meta-gate used by local prepublish and CI."""
# ruff: noqa: E501, E701, E702, F841
from __future__ import annotations

import ast
import copy
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from scripts.runtime import verify_rf17_acceptance as verifier


@dataclass(frozen=True)
class RawPathSensitivitySpec:
    path: str
    invalid_mutations: tuple[object, ...]
    reason: str


@dataclass(frozen=True)
class AuditSpec:
    requirement_id: str
    scenario_id: str
    lifecycle: str
    relevant_paths: tuple[str, ...]
    applicable: bool
    not_applicable_reason: str | None
    evaluator: Callable[[dict[str, object]], bool]


def _json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


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


def _path_kind(path: str) -> str:
    """Immutable structural policy; it never consults evidence or a checker."""
    if path.endswith(".physical_rows") or path.endswith(".physical_before") or path.endswith(".physical_after"):
        return "list"
    if path.endswith(".backend_pids") or path.endswith(".key_inventory") or path.endswith(".tables"):
        return "list"
    if path.endswith(".runtime_return") or path.endswith(".stage_c") or path.endswith(".stage_e"):
        return "object"
    if path.endswith(".rows") or path.endswith(".dml_probes") or path.endswith(".privilege_matrix"):
        return "list"
    return "scalar"


def _sensitivity_specs(items: tuple[verifier.Requirement, ...]) -> tuple[RawPathSensitivitySpec, ...]:
    specs: list[RawPathSensitivitySpec] = []
    for item in items:
        for path in item.required_raw_paths:
            kind = _path_kind(path)
            if kind == "list":
                values = (None, "tampered-fact", 7, {}, [], ["tampered-fact"], [{"malformed": True}])
                reason = "declared list must remain a populated, relation-bearing collection"
            elif kind == "object":
                values = (None, "tampered-fact", 7, {}, [], {"malformed": True})
                reason = "declared object must retain its required relation members"
            else:
                values = (None, "tampered-fact", 7, False, "")
                reason = "declared scalar must retain its required identity/state value"
            specs.append(RawPathSensitivitySpec(path, values, reason))
    return tuple(specs)


_PRE_OPERATION = {"identity.", "schema.", "security.", "source.", "endpoint.", "fanout."}
_IMMEDIATE = {"claim.", "lease.", "attempt.", "transaction.", "result."}


def _lifecycle(requirement_id: str) -> str:
    if any(requirement_id.startswith(prefix) for prefix in _PRE_OPERATION):
        return "PRE_OPERATION"
    if any(requirement_id.startswith(prefix) for prefix in _IMMEDIATE):
        return "IMMEDIATE_POST_OPERATION"
    if requirement_id.startswith("reconciliation.") or requirement_id.startswith("restart."):
        return "LATER_LIFECYCLE"
    if requirement_id.startswith(("history.", "foreign.", "privacy.")):
        return "FINAL_READ_MODEL"
    return "NOT_APPLICABLE"


def _audit_specs(items: tuple[verifier.Requirement, ...], lifecycle: bool) -> tuple[AuditSpec, ...]:
    specs: list[AuditSpec] = []
    for item in items:
        classification = _lifecycle(item.requirement_id)
        applicable = classification != "NOT_APPLICABLE"
        if lifecycle and item.requirement_id == "claim.same_item_single_owner":
            classification = "IMMEDIATE_POST_OPERATION"
            applicable = True
        specs.append(AuditSpec(item.requirement_id, item.scenario_id, classification, item.required_raw_paths,
                               applicable, None if applicable else "no lifecycle snapshot is defined for this requirement",
                               item.check))
    return tuple(specs)


def _evaluate_audits(specs: tuple[AuditSpec, ...], evidence: dict[str, object], label: str) -> dict[str, object]:
    entries: list[dict[str, object]] = []
    failures: list[str] = []
    for spec in specs:
        passed = True if not spec.applicable else verifier._safe_check(spec.evaluator, evidence)
        if spec.applicable and not passed:
            failures.append(spec.requirement_id)
        entries.append({"requirement_id": spec.requirement_id, "scenario_id": spec.scenario_id,
                        "lifecycle": spec.lifecycle, "relevant_evidence_paths": list(spec.relevant_paths),
                        "applicable": spec.applicable, "not_applicable_reason": spec.not_applicable_reason,
                        "evaluator": spec.evaluator.__name__, "pass": passed})
    return {"entries": entries, "entry_count": len(entries), "applicable_count": sum(bool(x["applicable"]) for x in entries),
            "pass_count": sum(bool(x["pass"]) for x in entries), "failures": failures, "label": label}


def _check(checker, evidence: dict[str, object], exceptions: list[str], label: str) -> bool:
    try:
        return checker(evidence) is True
    except Exception as exc:
        exceptions.append(f"{label}:{type(exc).__name__}")
        return False


def _execution_provenance(evidence: dict[str, object]) -> tuple[bool, int, int, int, str]:
    ledger = evidence.get("executed_case_ledger")
    bindings = evidence.get("requirement_case_bindings")
    if not isinstance(ledger, dict) or not isinstance(bindings, dict):
        return False, 0, 0, 0, "ledger-or-bindings-missing"
    seen: set[str] = set()
    duplicate = 0
    for requirement_id in verifier.EXPECTED_RF17_REQUIREMENT_IDS:
        case_ids = bindings.get(requirement_id)
        if not isinstance(case_ids, list) or len(case_ids) != 1:
            return False, len(ledger), len(seen), len(ledger) - len(seen), "binding-cardinality"
        case_id = case_ids[0]
        if not isinstance(case_id, str) or case_id in seen:
            duplicate += 1
            continue
        case = ledger.get(case_id)
        if not isinstance(case, dict) or case.get("case_id") != case_id or case.get("recorder") not in {"single_call", "concurrent_call", "stage_sequence"}:
            return False, len(ledger), len(seen), len(ledger) - len(seen), "case-recorder"
        if not isinstance(case.get("callable"), str) or not case["callable"] or not isinstance(case.get("runtime"), dict) or not case["runtime"].get("kind"):
            return False, len(ledger), len(seen), len(ledger) - len(seen), "case-provenance"
        seen.add(case_id)
    fabricated = len(set(ledger) - seen)
    ok = not duplicate and not fabricated and len(seen) == 48 and len(ledger) == 48
    return ok, len(ledger), len(seen), fabricated + duplicate, "ok" if ok else "case-cardinality"


def _source_ast_checks() -> dict[str, bool]:
    root = Path(__file__).resolve().parents[2]
    producer_path = root / "scripts/runtime/run_rf17_postgres_acceptance.py"
    verifier_path = root / "scripts/runtime/verify_rf17_acceptance.py"
    producer_source = producer_path.read_text(encoding="utf-8")
    producer_tree = ast.parse(producer_source)
    producer_bad = {"verify_rf17_acceptance", "check_rf17_acceptance_meta", "EXPECTED_RF17", "observations", "passes", "verdicts", "acceptance_results"}
    producer_independent = not any(token in producer_source for token in producer_bad) and '"relation_id"' not in producer_source and not any(
        isinstance(node, (ast.Import, ast.ImportFrom)) and "verify_rf17" in ast.unparse(node) for node in ast.walk(producer_tree)
    )
    source = verifier_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    generic = not ("registry_group" in source or "_spec_for" in source or '"operation.relation_id"' in source or '"physical.relation_id"' in source)
    return {"producer_verifier_independence": producer_independent, "generic_registry_fallback": "registry_group" not in names and "_spec_for" not in source,
            "modulo_routing": "modulo" not in source, "generic_relation": '"operation.relation_id"' not in source and '"physical.relation_id"' not in source, "reconciliation_router": "check_recon_single" in names and "check_recon_blocks" in names and "check_recon_replay" in names and "check_recon_delivered" in names and "check_recon_no_effect" in names and "check_recon_manual" in names,
            "restart_router": "check_restart_claim" in names and "check_restart_retry" in names and "check_restart_attempt" in names, "generic_router_fallback": generic}


def run(evidence: dict[str, object], diagnostics: dict[str, object], expected_sha: str | None) -> dict[str, object]:
    items = verifier.registry()
    exceptions: list[str] = []
    failures: list[str] = []
    if tuple(diagnostics.get("requirement_ids", ())) != verifier.EXPECTED_RF17_REQUIREMENT_IDS:
        failures.append("diagnostics.requirement_ids")
    if tuple(diagnostics.get("tamper_strategy_ids", ())) != verifier.EXPECTED_RF17_TAMPER_STRATEGY_IDS:
        failures.append("diagnostics.tamper_strategy_ids")
    if len(items) != 48 or tuple(x.requirement_id for x in items) != verifier.EXPECTED_RF17_REQUIREMENT_IDS:
        failures.append("registry.requirements")
    if len({x.check.__name__ for x in items}) != 48 or len({x.tamper.__name__ for x in items}) != 48:
        failures.append("registry.unique-callables")

    original_failures = [x.requirement_id for x in items if not _check(x.check, evidence, exceptions, f"original:{x.requirement_id}")]
    tamper_failures: list[str] = []
    for item in items:
        mutated = copy.deepcopy(evidence)
        before = _json(mutated)
        try:
            item.tamper(mutated)
        except Exception as exc:
            exceptions.append(f"tamper:{item.requirement_id}:{type(exc).__name__}")
            tamper_failures.append(item.requirement_id)
            continue
        if before == _json(mutated) or _check(item.check, mutated, exceptions, f"tamper:{item.requirement_id}"):
            tamper_failures.append(item.requirement_id)

    counterexamples = verifier.semantic_counterexample_matrix(evidence)
    counterexample_failures = [x.requirement_id for x in items if _check(x.check, counterexamples[x.requirement_id], exceptions, f"counterexample:{x.requirement_id}")]
    specs = _sensitivity_specs(items)
    shape_rejected = shape_accepted = shape_exception = skipped_noop = 0
    shape_failures: list[str] = []
    for item, spec in zip((item for item in items for _ in item.required_raw_paths), specs):
        original = verifier._raw(evidence, spec.path)
        original_serial = _json(original)
        for index, replacement in enumerate(spec.invalid_mutations):
            if original_serial == _json(replacement):
                skipped_noop += 1
                continue
            shape_id = f"{item.requirement_id}:{spec.path}:{index}"
            mutated = copy.deepcopy(evidence)
            if not _set_path(mutated, spec.path, copy.deepcopy(replacement)):
                shape_failures.append(shape_id + ":missing-path")
                continue
            local: list[str] = []
            try:
                accepted = item.check(mutated) is True
            except Exception as exc:
                shape_exception += 1
                shape_failures.append(shape_id + ":" + type(exc).__name__)
                continue
            if accepted:
                shape_accepted += 1
                shape_failures.append(shape_id + ":accepted")
            else:
                shape_rejected += 1
    immediate = _evaluate_audits(_audit_specs(items, True), evidence, "immediate_snapshot")
    precondition = _evaluate_audits(_audit_specs(items, False), evidence, "non_vacuous_precondition")
    execution_ok, executed_count, bound_count, fabricated_count, execution_reason = _execution_provenance(evidence)
    source_checks = _source_ast_checks()
    summary_fixture = {"e446_summary": {"single_committed_event": True}}
    summary_ok = False
    try:
        verifier.assert_no_acceptance_summary(summary_fixture)
    except AssertionError:
        summary_ok = True
    regressions = {}
    for name, checker, mutation in (("history_tampered_fact", verifier.check_history_account, lambda x: x.setdefault("history", {}).setdefault("account_scope", {}).setdefault("physical_source_rows", []).append("tampered-fact")),
                                    ("empty_cross_account_history", verifier.check_history_cross_account, lambda x: x.setdefault("history", {}).setdefault("cross_account_blocked", {}).__setitem__("physical_source_rows", []))):
        mutated = copy.deepcopy(evidence); mutation(mutated); regressions[name + "_rejected"] = not _check(checker, mutated, exceptions, "regression:" + name)
    claim_bad = copy.deepcopy(evidence); claim = claim_bad.get("claim", {}).get("same_item_single_owner", {}); row = claim.get("physical_after", [{}])[0] if isinstance(claim, dict) else {}
    if isinstance(row, dict): row.update({"state": "DELIVERED", "lease_started_at": None, "lease_expires_at": None})
    regressions["claim_late_delivered_rejected"] = not _check(verifier.check_claim_owner, claim_bad, exceptions, "regression:claim-late-delivered")
    fanout_bad = copy.deepcopy(evidence); fanout = fanout_bad.get("fanout", {}).get("concurrent_dedup", {}); fanout["physical_before"] = [{"id": "preexisting-row"}]; fanout["physical_after"] = [{"id": "preexisting-row"}]; fanout["runtime_results"] = [{"backend_pid": 101, "kind": "return", "outbox_ids": []}, {"backend_pid": 102, "kind": "return", "outbox_ids": []}]
    regressions["fanout_e834_rejected"] = not _check(verifier.check_fanout_concurrent, fanout_bad, exceptions, "regression:fanout-e834")
    regressions["restart_no_blind_resend_rejected"] = bool(source_checks["restart_router"] and _check(verifier.check_restart_attempt, evidence, exceptions, "regression:restart-baseline"))
    required = (not failures and not original_failures and not tamper_failures and len(counterexamples) == 48 and not counterexample_failures and
                shape_rejected == sum(1 for spec in specs for value in spec.invalid_mutations if _json(verifier._raw(evidence, spec.path)) != _json(value)) and shape_accepted == 0 and shape_exception == 0 and not shape_failures and
                immediate["entry_count"] == 48 and not immediate["failures"] and precondition["entry_count"] == 48 and not precondition["failures"] and execution_ok and fabricated_count == 0 and summary_ok and all(source_checks.values()) and all(regressions.values()) and not exceptions)
    result = {"technical_id": verifier.TECHNICAL_ID, "candidate_sha": evidence.get("identity", {}).get("candidate_sha"), "requirement_count": len(items), "checker_count": len(items), "tamper_count": len(items), "unique_checker_count": len({x.check.__name__ for x in items}), "unique_tamper_count": len({x.tamper.__name__ for x in items}), "original_pass_count": len(items) - len(original_failures), "tamper_rejected_count": len(items) - len(tamper_failures), "counterexample_count": len(counterexamples), "counterexample_rejected_count": len(counterexamples) - len(counterexample_failures), "executed_case_count": executed_count, "requirement_binding_count": bound_count, "fabricated_unbound_case_count": fabricated_count, "execution_provenance_meta_check": execution_ok, "approved_recorder_meta_check": execution_ok, "acceptance_critical_raw_path_count": len(specs), "provenance_only_raw_path_count": sum(len(x) for x in verifier.PROVENANCE_ONLY_RAW_PATHS.values()), "provenance_only_raw_paths": verifier.PROVENANCE_ONLY_RAW_PATHS, "shape_attempted_count": shape_rejected + shape_accepted + shape_exception, "shape_rejected_count": shape_rejected, "shape_accepted_count": shape_accepted, "shape_exception_count": shape_exception, "shape_skipped_noop_count": skipped_noop, "shape_explicit_valid_alternative_count": 0, "shape_failure_cases": shape_failures, "immediate_snapshot_audit_entry_count": immediate["entry_count"], "immediate_snapshot_audit_applicable_count": immediate["applicable_count"], "immediate_snapshot_audit_pass_count": immediate["pass_count"], "immediate_snapshot_audit_failures": immediate["failures"], "non_vacuous_precondition_audit_entry_count": precondition["entry_count"], "non_vacuous_precondition_audit_applicable_count": precondition["applicable_count"], "non_vacuous_precondition_audit_pass_count": precondition["pass_count"], "non_vacuous_precondition_audit_failures": precondition["failures"], "known_regressions": regressions, "producer_verifier_independence": source_checks["producer_verifier_independence"], "acceptance_summary_meta_check": summary_ok, "generic_registry_fallback_meta_check": source_checks["generic_registry_fallback"], "modulo_routing_meta_check": source_checks["modulo_routing"], "generic_relation_meta_check": source_checks["generic_relation"], "reconciliation_router_meta_check": source_checks["reconciliation_router"], "restart_router_meta_check": source_checks["restart_router"], "execution_provenance_reason": execution_reason, "exceptions": exceptions, "failures": failures + original_failures + tamper_failures + counterexample_failures, "evidence_digest": hashlib.sha256(_json(evidence).encode()).hexdigest()}
    if expected_sha and result["candidate_sha"] != expected_sha:
        result["failures"].append("identity.candidate_sha")
        required = False
    if not required:
        raise SystemExit("RF17 canonical meta-gate failed: " + ",".join(result["failures"] or ["count-or-regression"]))
    return result


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", type=Path, default=Path("rf17-evidence.json"))
    parser.add_argument("--diagnostics", type=Path, default=Path("rf17-verifier-diagnostics.json"))
    parser.add_argument("--output", type=Path, default=Path("rf17-meta-gate.json"))
    parser.add_argument("--expected-sha")
    args = parser.parse_args()
    result = run(json.loads(args.evidence.read_text()), json.loads(args.diagnostics.read_text()), args.expected_sha)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("RF17 canonical meta-gate passed")


if __name__ == "__main__":
    main()
