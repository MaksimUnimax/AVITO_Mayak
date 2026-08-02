from __future__ import annotations

# ruff: noqa

import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))

from scripts.runtime.verify_rf13_acceptance import (
    REQUIRED_SECTIONS,
    REQUIRED_TAMPER_CASES,
    REQUIREMENT_REGISTRY,
    TAMPER_MUTATIONS,
)


def test_one_executable_requirement_registry_and_exact_case_set() -> None:
    assert REQUIREMENT_REGISTRY
    assert set(REQUIREMENT_REGISTRY) == {"identity", "toolchain", "migration", "physical_schema", "preparation", "positive_snapshot", "negative_snapshot_matrix", "patch_lww", "idempotency", "active_slot", "rollback", "ownership", "lifecycle", "freeze", "revision", "schema_integrity", "cleanup", "security", "system_authority_mismatch", "different_field_applicability"}
    assert all(callable(spec.checker) and spec.raw_paths and spec.tamper_cases for spec in REQUIREMENT_REGISTRY.values())
    assert set(REQUIRED_TAMPER_CASES) == set(TAMPER_MUTATIONS)
    assert all(mutation.requirement_ids and mutation.changed_paths and callable(mutation.mutate) for mutation in TAMPER_MUTATIONS.values())


def test_requirement_case_and_raw_path_coverage_is_machine_declared() -> None:
    mapped = {case for spec in REQUIREMENT_REGISTRY.values() for case in spec.tamper_cases}
    assert mapped == set(REQUIRED_TAMPER_CASES)
    covered_requirements = {requirement for mutation in TAMPER_MUTATIONS.values() for requirement in mutation.requirement_ids}
    assert covered_requirements == set(REQUIREMENT_REGISTRY)
    for case, mutation in TAMPER_MUTATIONS.items():
        assert set(mutation.requirement_ids) <= set(REQUIREMENT_REGISTRY), case
        declared = [path for requirement in mutation.requirement_ids for path in REQUIREMENT_REGISTRY[requirement].raw_paths]
        assert any(path == raw or path.startswith(raw + ".") or raw.startswith(path + ".") for path in mutation.changed_paths for raw in declared), case


def test_required_sections_are_not_diagnostic_or_presence_authority() -> None:
    assert "diagnostic_gates" not in REQUIRED_SECTIONS
    source = Path("scripts/runtime/verify_rf13_acceptance.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    assert not any(isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "get" and any(isinstance(arg, ast.Constant) and "pre_revision_count" in str(arg.value) for arg in node.args) for node in ast.walk(tree))
    assert "tamper_" + "probe" not in source


def test_schema_checker_is_not_word_presence_or_check_true() -> None:
    source = Path("scripts/runtime/verify_rf13_acceptance.py").read_text(encoding="utf-8")
    assert "CHECK (TRUE)" in source
    assert "pg_get_constraintdef" not in source
    assert "len(constraints) >=" not in source


def test_tamper_runner_has_no_universal_rejection_or_noop_sentinel() -> None:
    source = Path("scripts/runtime/run_rf13_tamper_matrix.py").read_text(encoding="utf-8")
    assert "tamper_" + "probe" not in source
    assert "item[" not in source
    assert "mutation.mutate" in source
