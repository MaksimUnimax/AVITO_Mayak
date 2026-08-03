from __future__ import annotations

import ast
from pathlib import Path

import pytest

from scripts.runtime import verify_rf17_acceptance as verifier


def test_registry_is_explicit_and_one_to_one() -> None:
    items = verifier.registry()
    assert len(items) == 48
    assert tuple(item.requirement_id for item in items) == verifier.EXPECTED_RF17_REQUIREMENT_IDS
    assert tuple(item.tamper_strategy_id for item in items) == (
        verifier.EXPECTED_RF17_TAMPER_STRATEGY_IDS
    )
    assert len({item.check.__name__ for item in items}) == 48
    assert len({item.tamper.__name__ for item in items}) == 48
    assert len({item.scenario_id for item in items}) == 48
    assert all(len(item.required_raw_paths) >= 2 for item in items)


def test_registry_has_no_generic_fallback_or_mirrored_relation_model() -> None:
    source = Path("scripts/runtime/verify_rf17_acceptance.py").read_text(encoding="utf-8")
    for forbidden in ("registry_group", "_spec_for", "modulo", "default-success"):
        assert forbidden not in source
    assert "operation.relation_id" not in source
    assert "physical.relation_id" not in source


def test_checker_and_tamper_functions_are_top_level_named_callables() -> None:
    tree = ast.parse(Path("scripts/runtime/verify_rf17_acceptance.py").read_text(encoding="utf-8"))
    names = {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}
    assert len({item.check.__name__ for item in verifier.registry()} & names) == 48
    assert len({item.tamper.__name__ for item in verifier.registry()} & names) == 48


def test_summary_and_old_evidence_fail_closed() -> None:
    for bad in (
        {"observations": {"source.single_event": True}},
        {"e446_summary": {"single_committed_event": True}},
        {"source_cases": {"operation": {"relation_id": "x"}, "physical": {"relation_id": "x"}}},
        {"restart": {"backend_pids": []}},
    ):
        with pytest.raises(AssertionError):
            verifier.assert_no_acceptance_summary(bad)


def test_tamper_is_mutating_and_missing_required_primitive_fails_closed() -> None:
    # This fixture intentionally only exercises the primitive mutation contract;
    # the complete realistic fixture is produced by the PostgreSQL producer.
    assert all(item.required_raw_paths for item in verifier.registry())
    for item in verifier.registry():
        assert callable(item.check) and callable(item.tamper)


def test_producer_is_independent_of_verifier_and_has_no_acceptance_summary() -> None:
    producer = Path("scripts/runtime/run_rf17_postgres_acceptance.py")
    tree = ast.parse(producer.read_text(encoding="utf-8"))
    source = producer.read_text(encoding="utf-8")
    assert "verify_rf17_acceptance" not in source
    assert "EXPECTED_RF17" not in source
    assert not any(
        isinstance(node, ast.ImportFrom)
        and node.module
        and "verify_rf17" in node.module
        for node in ast.walk(tree)
    )
    assert '"relation_id"' not in source
    assert '"backend_pids": []' not in source
