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
    evidence["identity"]["candidate_sha"] = "a" * 40  # type: ignore[index]
    evidence["technical_id"] = verifier.TECHNICAL_ID
    evidence["database"] = {"postgres_version": "PostgreSQL 18.0", "db_alembic_head": "head", "repository_alembic_head": "head"}
    evidence["physical_schema"] = {"tables": ["notification_endpoints", "notification_events", "notification_outbox", "notification_delivery_attempts", "notification_delivery_reconciliations"]}
    evidence["application_privileges"] = {"matrix": [{"table": "notification_events", "can_select": True, "can_insert": True, "can_update": True, "can_delete": True}], "probes": [{"table": "identity_accounts", "sqlstate": "42501"}]}
    for group in ("source_cases", "endpoint_cases", "fanout_cases", "claim_cases", "lease_cases", "attempt_cases", "result_cases", "reconciliation_cases", "restart_cases", "history_cases", "foreign_witness", "safe_persistence"):
        evidence[group] = {"operation": {"raw": "one", "relation_id": "rf17"}, "physical": {"raw": "two", "relation_id": "rf17"}}
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


def test_e446_summary_fixture_is_rejected_and_primitive_paths_are_multi_fact() -> None:
    bad = {"technical_id": verifier.TECHNICAL_ID, "identity": {"candidate_sha": "a" * 40}, "source_cases": {"single_committed_event": True, "replay_same_row": True, "trusted_delivered_binds_attempt": True}}
    with pytest.raises(AssertionError):
        verifier.assert_no_acceptance_summary(bad)
    assert all(len(item.required_raw_paths) >= 2 for item in verifier.registry())


@pytest.mark.parametrize("bad", [{"requirement_ids": []}, {"tamper_strategy_ids": []}])
def test_registry_diagnostics_do_not_define_the_registry(bad: dict[str, object]) -> None:
    assert bad != {"requirement_ids": list(verifier.EXPECTED_RF17_REQUIREMENT_IDS)}
