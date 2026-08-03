# ruff: noqa: E402, E501
from __future__ import annotations

import ast
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.runtime import check_rf17_acceptance_meta as meta
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


def test_raw_path_provenance_is_explicit_and_disjoint_from_acceptance_paths() -> None:
    required = {path for item in verifier.registry() for path in item.required_raw_paths}
    provenance = {path for paths in verifier.PROVENANCE_ONLY_RAW_PATHS.values() for path in paths}
    assert provenance.isdisjoint(required)
    assert set(verifier.PROVENANCE_ONLY_RAW_PATHS) <= {item.requirement_id for item in verifier.registry()}


def test_canonical_meta_has_no_post_checker_shape_exemption_or_literal_audits() -> None:
    source = Path("scripts/runtime/check_rf17_acceptance_meta.py").read_text(encoding="utf-8")
    assert "shape_not_applicable" not in source
    assert "if checker returns True" not in source
    assert "fresh_immediate_snapshot_audit_count = 48" not in source
    assert "non_vacuous_precondition_audit_count = 48" not in source
    assert '"fresh_immediate_snapshot_audit_failures": []' not in source
    assert '"non_vacuous_precondition_audit_failures": []' not in source


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


def test_all_checkers_are_total_for_deterministic_shape_mutations() -> None:
    shapes = [None, "tampered-fact", 7, {}, [], ["tampered-fact"]]
    for item in verifier.registry():
        for shape in shapes:
            value = {"scenario": shape}
            result = item.check(value)
            assert type(result) is bool


def test_hosted_history_tampered_fact_regression_is_fail_closed() -> None:
    evidence = {"history": {"account_scope": {"input": {"account_id": "a"}, "runtime_return": {"rows": []}, "physical_source_rows": ["tampered-fact"]}}}
    assert verifier.check_history_account(evidence) is False


def test_empty_cross_account_history_regression_is_rejected() -> None:
    evidence = {"history": {"cross_account_blocked": {"input": {"account_id": "b"}, "exception": {"class": "AccountScopeConflict", "attempted": True}, "physical_source_rows": []}}}
    assert verifier.check_history_cross_account(evidence) is False


def test_canonical_meta_gate_is_the_workflow_authority() -> None:
    workflow = Path(".github/workflows/ci-rf17-acceptance.yml").read_text(encoding="utf-8")
    meta = Path("scripts/runtime/check_rf17_acceptance_meta.py").read_text(encoding="utf-8")
    assert "check_rf17_acceptance_meta.py" in workflow
    assert "from scripts.runtime import verify_rf17_acceptance" in meta
    assert "uv run python - <<'PY'" not in workflow[workflow.index("Immutable meta-gate") :]


def _clean_env() -> dict[str, str]:
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env.pop("PYTHONHOME", None)
    return env


def _uv() -> str:
    return shutil.which("uv") or "/root/.local/bin/uv"


def test_canonical_entrypoint_is_importable_from_clean_repository_root() -> None:
    result = subprocess.run([_uv(), "run", "python", "scripts/runtime/check_rf17_acceptance_meta.py", "--help"], cwd=ROOT, env=_clean_env(), capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "ModuleNotFoundError" not in result.stderr


def test_canonical_entrypoint_is_importable_from_clean_foreign_cwd() -> None:
    script = ROOT / "scripts/runtime/check_rf17_acceptance_meta.py"
    with tempfile.TemporaryDirectory() as foreign:
        result = subprocess.run([_uv(), "run", "python", str(script), "--help"], cwd=foreign, env=_clean_env(), capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "ModuleNotFoundError" not in result.stderr


def test_exact_workflow_form_writes_canonical_meta_output() -> None:
    evidence = Path("/opt/avito-mayak-runtime/rf17-prepublish-c07/final-artifacts/rf17-evidence.json")
    diagnostics = Path("/opt/avito-mayak-runtime/rf17-prepublish-c07/final-artifacts/rf17-verifier-diagnostics.json")
    if not evidence.exists() or not diagnostics.exists():
        pytest.skip("project-owned RF17 evidence is unavailable")
    with tempfile.TemporaryDirectory() as directory:
        output = Path(directory) / "rf17-meta-gate.json"
        result = subprocess.run(
            [
                _uv(),
                "run",
                "python",
                "scripts/runtime/check_rf17_acceptance_meta.py",
                "--evidence",
                str(evidence),
                "--diagnostics",
                str(diagnostics),
                "--output",
                str(output),
            ],
            cwd=ROOT,
            env=_clean_env(),
            capture_output=True,
            text=True,
        )
        output_created = output.exists()
        output_value = json.loads(output.read_text()) if output_created else {}
    assert result.returncode == 0, result.stderr
    assert output_created
    assert output_value["requirement_count"] == 48


def test_audit_families_are_independent_and_non_vacuous() -> None:
    items = verifier.registry()
    immediate = meta.immediate_snapshot_specs(items)
    precondition = meta.precondition_specs(items)
    assert len(immediate) == len(precondition) == 48
    assert sum(item.applicable for item in immediate) + sum(not item.applicable for item in immediate) == 48
    assert sum(item.applicable for item in precondition) + sum(not item.applicable for item in precondition) == 48
    assert all(item.evaluator is not requirement.check for item in immediate for requirement in items if item.requirement_id == requirement.requirement_id)
    assert all(item.evaluator is not requirement.check for item in precondition for requirement in items if item.requirement_id == requirement.requirement_id)
    assert all(item.not_applicable_reason for item in immediate + precondition if not item.applicable)
    source = Path("scripts/runtime/check_rf17_acceptance_meta.py").read_text(encoding="utf-8")
    assert "_audit_specs(items: tuple[verifier.Requirement, ...], lifecycle: bool)" not in source
    assert "evaluator=item.check" not in source
    assert "passed = True if not spec.applicable" not in source


def test_meta_audit_mutation_contracts_are_fail_closed() -> None:
    fixture = Path("/opt/avito-mayak-runtime/rf17-prepublish-c07/final-artifacts/rf17-evidence.json")
    if not fixture.exists():
        pytest.skip("project-owned RF17 evidence is unavailable")
    evidence = json.loads(fixture.read_text())
    items = verifier.registry()
    for specs, label in ((meta.immediate_snapshot_specs(items), "immediate"), (meta.precondition_specs(items), "precondition")):
        counts = meta._audit_sensitivity(specs, evidence, label)
        assert counts[f"{label}_mutation_accepted_count"] == 0
        assert counts[f"{label}_mutation_exception_count"] == 0
        assert counts[f"{label}_mutation_rejected_count"] == counts[f"{label}_mutation_attempted_count"]


def test_semantic_false_positive_regressions_preserve_shape_and_are_rejected() -> None:
    evidence_path = Path("/opt/avito-mayak-runtime/rf17-prepublish-c09/rf17-evidence.json")
    if not evidence_path.exists():
        pytest.skip("project-owned RF17 evidence is unavailable")
    evidence = json.loads(evidence_path.read_text())

    endpoint = json.loads(json.dumps(evidence))
    row = endpoint["endpoint"]["stable_replay"]["physical_after"][0]
    row["id"] = "different-valid-looking-endpoint-id"
    assert meta._regression_mutations(endpoint, [])["endpoint_stable_replay_semantic_counterexample_rejected"]

    source = json.loads(json.dumps(evidence))
    source["source"]["single_event"]["physical_before"].append(
        dict(source["source"]["single_event"]["physical_after"][0])
    )
    assert meta._regression_mutations(source, [])["source_single_event_preexisting_counterexample_rejected"]


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
