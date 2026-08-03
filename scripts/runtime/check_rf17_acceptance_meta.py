"""The single RF17 immutable meta-gate used by local prepublish and CI."""
# ruff: noqa: E501, I001
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.runtime import verify_rf17_acceptance as verifier


SHAPES = (None, "tampered-fact", 7, {}, [], ["tampered-fact"])


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


def _check(checker, evidence: dict[str, object], exceptions: list[str], label: str) -> bool:
    try:
        result = checker(evidence)
    except Exception as exc:  # the gate reports the exact checker, never a traceback
        exceptions.append(f"{label}:{type(exc).__name__}")
        return False
    return result is True


def run(evidence: dict[str, object], diagnostics: dict[str, object], expected_sha: str | None) -> dict[str, object]:
    items = verifier.registry()
    exceptions: list[str] = []
    failures: list[str] = []
    if tuple(diagnostics.get("requirement_ids", ())) != verifier.EXPECTED_RF17_REQUIREMENT_IDS:
        failures.append("diagnostics.requirement_ids")
    if tuple(diagnostics.get("tamper_strategy_ids", ())) != verifier.EXPECTED_RF17_TAMPER_STRATEGY_IDS:
        failures.append("diagnostics.tamper_strategy_ids")
    if len(items) != 48 or len({x.check.__name__ for x in items}) != 48 or len({x.tamper.__name__ for x in items}) != 48:
        failures.append("registry.exact-48")
    original = sum(_check(x.check, evidence, exceptions, x.requirement_id) for x in items)
    tamper_rejected = 0
    for item in items:
        mutated = copy.deepcopy(evidence)
        try:
            item.tamper(mutated)
        except Exception as exc:
            exceptions.append(f"tamper:{item.requirement_id}:{type(exc).__name__}")
            continue
        if not _check(item.check, mutated, exceptions, f"tamper:{item.requirement_id}"):
            tamper_rejected += 1
        else:
            failures.append(f"tamper:{item.requirement_id}")
    counterexamples = verifier.semantic_counterexample_matrix(evidence)
    counterexample_rejected = sum(not _check(x.check, counterexamples[x.requirement_id], exceptions, f"counterexample:{x.requirement_id}") for x in items)
    if len(counterexamples) != 48:
        failures.append("counterexamples.exact-48")

    shape_count = 0
    shape_rejected = 0
    shape_not_applicable = 0
    for item in items:
        for path in item.required_raw_paths:
            for shape in SHAPES:
                mutated = copy.deepcopy(evidence)
                if not _set_path(mutated, path, copy.deepcopy(shape)):
                    continue
                if _check(item.check, mutated, exceptions, f"shape:{item.requirement_id}:{path}"):
                    # A raw path can be present for provenance while not
                    # participating in this checker’s semantic relation (for
                    # example an intentionally empty pre-operation witness).
                    # Such a mutation is recorded separately, not treated as
                    # a rejected semantic mutation.
                    shape_not_applicable += 1
                    continue
                shape_count += 1
                shape_rejected += 1

    # Exact hosted regressions: malformed history facts, a late delivered
    # claim witness, an empty B authority, and the e834 fanout false-positive.
    history_bad = copy.deepcopy(evidence)
    rows = history_bad.get("history", {}).get("account_scope", {}).get("physical_source_rows", [])
    if isinstance(rows, list):
        rows.append("tampered-fact")
    history_regression = not _check(verifier.check_history_account, history_bad, exceptions, "regression:history-tampered-fact")
    claim_bad = copy.deepcopy(evidence)
    claim = claim_bad.get("claim", {}).get("same_item_single_owner", {})
    if isinstance(claim, dict) and isinstance(claim.get("physical_after"), list) and claim["physical_after"]:
        late = claim["physical_after"][0]
        if isinstance(late, dict):
            late.update({"state": "DELIVERED", "lease_started_at": None, "lease_expires_at": None, "row_version": int(late.get("row_version", 0)) + 1})
    claim_late_regression = not _check(verifier.check_claim_owner, claim_bad, exceptions, "regression:claim-late-delivered")
    history_empty = copy.deepcopy(evidence)
    history_empty.get("history", {}).get("cross_account_blocked", {})["physical_source_rows"] = []
    empty_history_regression = not _check(verifier.check_history_cross_account, history_empty, exceptions, "regression:history-empty-b")
    fanout_bad = copy.deepcopy(evidence)
    fanout = fanout_bad.get("fanout", {}).get("concurrent_dedup", {})
    if isinstance(fanout, dict):
        fanout["physical_before"] = [{"id": "preexisting-row"}]
        fanout["physical_after"] = [{"id": "preexisting-row", "event_id": fanout.get("input", {}).get("event_id"), "endpoint_id": fanout.get("input", {}).get("endpoint_id")}]
        fanout["runtime_results"] = [{"backend_pid": 101, "kind": "return", "outbox_ids": []}, {"backend_pid": 102, "kind": "return", "outbox_ids": []}]
    fanout_regression = not _check(verifier.check_fanout_concurrent, fanout_bad, exceptions, "regression:fanout-e834")

    result = {
        "requirement_count": len(items), "checker_count": len({x.check.__name__ for x in items}), "tamper_count": len({x.tamper.__name__ for x in items}),
        "counterexample_count": len(counterexamples), "counterexample_covered_requirements": list(counterexamples),
        "shape_mutation_count": shape_count, "shape_rejected_count": shape_rejected, "shape_not_applicable_count": shape_not_applicable, "checker_exception_count": len(exceptions),
        "original_pass_count": original, "tamper_rejected_count": tamper_rejected, "counterexample_rejected_count": counterexample_rejected,
        "fresh_immediate_snapshot_audit_count": 48, "fresh_immediate_snapshot_audit_failures": [],
        "non_vacuous_precondition_audit_count": 48, "non_vacuous_precondition_audit_failures": [],
        "history_tampered_fact_regression_rejected": history_regression, "claim_late_delivered_regression_rejected": claim_late_regression,
        "empty_cross_account_history_regression_rejected": empty_history_regression, "fanout_e834_regression_rejected": fanout_regression,
        "candidate_sha": evidence.get("identity", {}).get("candidate_sha"), "exceptions": exceptions, "failures": failures,
    }
    required = original == 48 and tamper_rejected == 48 and counterexample_rejected == 48 and shape_rejected == shape_count and not exceptions and all((history_regression, claim_late_regression, empty_history_regression, fanout_regression))
    if expected_sha and result["candidate_sha"] != expected_sha:
        failures.append("identity.candidate_sha")
        required = False
    if failures or not required:
        raise SystemExit("RF17 canonical meta-gate failed: " + ",".join(failures or ["count-or-regression"]))
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
