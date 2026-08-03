from __future__ import annotations

# ruff: noqa: E501
import ast
import copy
import json
from pathlib import Path

import pytest

from scripts.runtime import verify_rf17_acceptance as verifier


def _representative_evidence() -> dict[str, object]:
    evidence: dict[str, object] = {
        "technical_id": verifier.TECHNICAL_ID,
        "identity": {"candidate_sha": "a" * 40},
    }
    for path in {path for item in verifier.registry() for path in item.required_raw_paths}:
        current = evidence
        parts = path.split(".")
        for part in parts[:-1]:
            current = current.setdefault(part, {})  # type: ignore[assignment]
        current[parts[-1]] = True
    return evidence


def test_canonical_registry_and_raw_paths_are_immutable_shape() -> None:
    registry = verifier.registry()
    assert len(registry) == 48
    assert tuple(item.requirement_id for item in registry) == verifier.EXPECTED_RF17_REQUIREMENT_IDS
    assert tuple(item.tamper_strategy_id for item in registry) == verifier.EXPECTED_RF17_TAMPER_STRATEGY_IDS
    assert all(item.required_raw_paths for item in registry)
    assert all("observations" not in path and "verdict" not in path for item in registry for path in item.required_raw_paths)


def test_each_checker_passes_valid_raw_evidence_and_missing_path_fails_closed() -> None:
    evidence = _representative_evidence()
    for item in verifier.registry():
        assert item.check(evidence), item.requirement_id
        missing = copy.deepcopy(evidence)
        current = missing
        parts = item.required_raw_paths[0].split(".")
        for part in parts[:-1]:
            current = current[part]
        del current[parts[-1]]
        assert not item.check(missing), item.requirement_id


def test_every_tamper_changes_raw_evidence_and_rejects_target() -> None:
    evidence = _representative_evidence()
    for item in verifier.registry():
        mutated = copy.deepcopy(evidence)
        before = json.dumps(mutated, sort_keys=True)
        item.tamper(mutated)
        assert json.dumps(mutated, sort_keys=True) != before
        assert not item.check(mutated), item.requirement_id


def test_producer_has_no_verifier_dependency_or_acceptance_map() -> None:
    producer = Path("scripts/runtime/run_rf17_postgres_acceptance.py")
    tree = ast.parse(producer.read_text(encoding="utf-8"))
    source = producer.read_text(encoding="utf-8")
    forbidden = ("verify_rf17_acceptance", "importlib", "SimpleNamespace", "EXPECTED_RF17", "observations", "passes", "verdicts", "acceptance_results")
    assert not any(token in source for token in forbidden)
    assert not any(isinstance(node, ast.ImportFrom) and node.module and "verify_rf17" in node.module for node in ast.walk(tree))


def test_no_generic_fact_checker_or_default_success_path() -> None:
    source = Path("scripts/runtime/verify_rf17_acceptance.py").read_text(encoding="utf-8")
    assert "def _fact" not in source
    assert "data.get(\"observations\")" not in source
    assert "default=True" not in source


@pytest.mark.parametrize("bad", [{"requirement_ids": []}, {"tamper_strategy_ids": []}])
def test_registry_diagnostics_do_not_define_the_registry(bad: dict[str, object]) -> None:
    assert bad != {"requirement_ids": list(verifier.EXPECTED_RF17_REQUIREMENT_IDS)}
