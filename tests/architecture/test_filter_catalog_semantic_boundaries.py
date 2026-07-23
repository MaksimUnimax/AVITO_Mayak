"""Architecture boundary tests for Filter Catalog FC-08 synthetic fixtures and tests."""

from __future__ import annotations

import ast
import json
import os
import re
import subprocess
from pathlib import Path

import pytest
from tests.unit.test_filter_catalog_semantic_contracts import _find_generic_fc08_dispatch_evidence

FIXTURE_PATH = Path("tests/fixtures/filter_catalog_semantic_vectors.json")
ARCH_TEST_PATH = Path("tests/architecture/test_filter_catalog_semantic_boundaries.py")
CONTRACT_TEST_PATH = Path("tests/contract/test_filter_catalog_semantic_contract_exports.py")
UNIT_TEST_PATH = Path("tests/unit/test_filter_catalog_semantic_contracts.py")
REPO_ROOT = Path(__file__).resolve().parents[2]
PRODUCTION_FILES = [
    REPO_ROOT / "src" / "mayak" / "modules" / "filter_catalog" / "contracts.py",
    REPO_ROOT / "src" / "mayak" / "modules" / "filter_catalog" / "evidence_approval.py",
    REPO_ROOT / "src" / "mayak" / "modules" / "filter_catalog" / "builder_validation.py",
    REPO_ROOT / "src" / "mayak" / "modules" / "filter_catalog" / "value_dependency_semantics.py",
    REPO_ROOT / "src" / "mayak" / "modules" / "filter_catalog" / "beacon_override_candidate.py",
    REPO_ROOT / "src" / "mayak" / "modules" / "filter_catalog" / "safe_read_models.py",
    REPO_ROOT / "src" / "mayak" / "modules" / "filter_catalog" / "__init__.py",
]
EXPECTED_BLOBS = {
    "contracts.py": "30055bec462fd772d06f1dc12de1ea8fcba3da77",
    "evidence_approval.py": "9491ee2a90aa4f6cd580c4a9bf511942c92f2f0a",
    "builder_validation.py": "084ba9d7083b6ca6fab8b03c7be34e4d3f50c3fb",
    "value_dependency_semantics.py": "9cb0f1648a359ae86c5e699250111bbe62825d27",
    "beacon_override_candidate.py": "1a441afd4352fd56c295b6a656262c00f226b2c1",
    "safe_read_models.py": "239d79ab54e03838da2967d24b2ca3ee60da65fe",
    "__init__.py": "f880efde1ae75cb7357de15328e6685d8244d80d",
}
FORBIDDEN_IMPORTS = [
    "fastapi", "sqlalchemy", "alembic", "httpx", "respx",
    "opentelemetry", "aiogram", "telethon", "psycopg", "psycopg2",
]
FC08_BASE_SHA = "e6c716c759e4c04c9ef7cebf6a8fac48fbd7b001"
FC08_TERMINAL_SHA = "7d31c0e3d2a351df934f3797e02b3bc909d6ed34"
EXPECTED_FC08_PATHS = sorted([
    "tests/architecture/test_filter_catalog_semantic_boundaries.py",
    "tests/contract/test_filter_catalog_semantic_contract_exports.py",
    "tests/fixtures/filter_catalog_semantic_vectors.json",
    "tests/unit/test_filter_catalog_semantic_contracts.py",
])


def _load_fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


class TestFC08ArchitectureBoundaries:
    def test_four_fc08_files_exist_and_cumulative_patch_boundary(self) -> None:
        for path in [FIXTURE_PATH, ARCH_TEST_PATH, CONTRACT_TEST_PATH, UNIT_TEST_PATH]:
            assert path.exists(), f"FC-08 file missing: {path}"
        base_is_ancestor = subprocess.run(
            ["git", "merge-base", "--is-ancestor", FC08_BASE_SHA, FC08_TERMINAL_SHA],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        assert base_is_ancestor.returncode == 0, (
            f"FC08_BASE_SHA ({FC08_BASE_SHA}) must be ancestor of FC08_TERMINAL_SHA ({FC08_TERMINAL_SHA})"
        )
        terminal_is_ancestor = subprocess.run(
            ["git", "merge-base", "--is-ancestor", FC08_TERMINAL_SHA, "HEAD"],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        assert terminal_is_ancestor.returncode == 0, (
            f"FC08_TERMINAL_SHA ({FC08_TERMINAL_SHA}) must be ancestor of HEAD"
        )
        result = subprocess.run(
            ["git", "diff", "--name-only", f"{FC08_BASE_SHA}...{FC08_TERMINAL_SHA}"],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        assert result.returncode == 0, f"git diff failed: {result.stderr}"
        committed_paths = sorted(result.stdout.strip().split("\n")) if result.stdout.strip() else []
        # This test owns the immutable FC-08 historical commit range; the current
        # task worktree allowlist is checked by a separate task-specific gate.
        assert committed_paths == EXPECTED_FC08_PATHS, (
            f"FC-08 path set mismatch: expected {EXPECTED_FC08_PATHS}, got {committed_paths}"
        )
        for p in committed_paths:
            assert not p.startswith("src/"), f"Production file in FC-08 diff: {p}"
            assert not p.startswith("docs/"), f"Doc file in FC-08 diff: {p}"

    def test_fixture_top_level_schema_and_key_order(self) -> None:
        data = _load_fixture()
        keys = list(data.keys())
        assert keys == ["schema_version", "module_id", "technical_id", "canonical_references", "vectors"]
        assert data["schema_version"] == "1.0"
        assert data["module_id"] == "13-filter-catalog-and-builder"
        assert data["technical_id"] == "FC-08-PARALLEL-MAIN-REISSUE-20260722-028"
        data2 = _load_fixture()
        assert data == data2
        assert json.dumps(data, sort_keys=True) == json.dumps(data2, sort_keys=True)

    def test_category_counts_and_vector_order(self) -> None:
        data = _load_fixture()
        vectors = data["vectors"]
        assert len(vectors) == 56
        expected_prefixes = [
            ("FC08-CATALOG-", 8),
            ("FC08-EVIDENCE-", 8),
            ("FC08-BUILDER-", 8),
            ("FC08-VALUE-", 8),
            ("FC08-BEACON-", 8),
            ("FC08-SAFE-READ-", 12),
            ("FC08-STATIC-", 4),
        ]
        offset = 0
        for prefix, count in expected_prefixes:
            for i in range(count):
                assert vectors[offset + i]["vector_id"] == f"{prefix}{i + 1:03d}"
            offset += count
        categories = [v["category"] for v in vectors]
        assert categories == (
            ["CATALOG"] * 8 + ["EVIDENCE"] * 8 + ["BUILDER"] * 8
            + ["VALUE"] * 8 + ["BEACON"] * 8 + ["SAFE_READ"] * 12 + ["STATIC"] * 4
        )

    def test_synthetic_only_corpus_strict(self) -> None:
        data = _load_fixture()
        corpus = json.dumps(data)
        corpus_lower = corpus.lower()
        assert "http://" not in corpus_lower, "HTTP URLs found in vectors"
        assert "https://" not in corpus_lower, "HTTPS URLs found in vectors"
        assert "api.telegram.org" not in corpus_lower, "Telegram API found in vectors"
        assert re.search(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", corpus) is None, "IP addresses found"
        assert re.search(r"\b\d{10,}\b", corpus) is None, "Phone numbers found"
        assert "email" not in corpus_lower or "email" not in json.dumps(data["vectors"]), "Email found"
        for ref in data["canonical_references"]:
            assert ref["safe_label"].startswith("Synthetic"), f"Non-synthetic safe_label: {ref['safe_label']}"
        for vec in data["vectors"]:
            for rid in vec.get("canonical_reference_ids", []):
                assert rid.startswith("FC08-"), f"Non-FC08 reference: {rid}"

    def test_forbidden_imports_absent(self) -> None:
        for prod_file in PRODUCTION_FILES:
            if not prod_file.exists():
                continue
            content = prod_file.read_text(encoding="utf-8")
            for mod in FORBIDDEN_IMPORTS:
                assert f"import {mod}" not in content, f"Forbidden import {mod} in {prod_file.name}"

    def test_protected_production_blobs_match(self) -> None:
        for filename, expected_blob in EXPECTED_BLOBS.items():
            result = subprocess.run(
                ["git", "rev-parse", f"HEAD:src/mayak/modules/filter_catalog/{filename}"],
                capture_output=True, text=True, cwd=str(REPO_ROOT),
            )
            actual_blob = result.stdout.strip()
            assert actual_blob == expected_blob, (
                f"Blob mismatch for {filename}: expected {expected_blob}, got {actual_blob}"
            )

    def test_od009_remains_open(self) -> None:
        decisions_path = REPO_ROOT / "docs" / "00-governance" / "OPEN_DECISIONS.md"
        content = decisions_path.read_text(encoding="utf-8")
        assert "OD-009" in content
        lines = content.split("\n")
        od009_active = False
        for line in lines:
            if "OD-009" in line and "OPEN" in line.upper():
                od009_active = True
                break
        assert od009_active, "OD-009 must remain OPEN"

    def test_no_generic_dispatcher_and_public_only_guard(self) -> None:
        source = UNIT_TEST_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)
        assert not re.search(r"^HANDLER_MAP\s*=", source, re.MULTILINE), "Module-level HANDLER_MAP must not exist"
        assert not re.search(r"^def test_vector_handler\b", source, re.MULTILINE), "Generic test_vector_handler must not exist"
        assert not re.search(r"^@pytest\.mark\.parametrize", source, re.MULTILINE), "No parametrize decorators allowed"
        evidence = _find_generic_fc08_dispatch_evidence(tree)
        assert evidence == {
            "assignments": 0,
            "dictionary_literals": 0,
            "dictionary_entries": 0,
            "vector_id_lookups": 0,
            "selected_handler_assignments": 0,
            "selected_handler_calls": 0,
            "module_or_local_registries": 0,
        }
        mutation = ast.parse(
            """
handler_map = {\"FC08-CATALOG-001\": handle_fc08_catalog_001}
for v in vectors:
    handler = handler_map[v[\"vector_id\"]]
    handler(v[\"input\"], v[\"expected\"])
"""
        )
        mutation_evidence = _find_generic_fc08_dispatch_evidence(mutation)
        assert mutation_evidence["assignments"] == 1
        assert mutation_evidence["dictionary_literals"] == 1
        assert mutation_evidence["dictionary_entries"] == 1
        assert mutation_evidence["vector_id_lookups"] == 1
        assert mutation_evidence["selected_handler_assignments"] == 1
        assert mutation_evidence["selected_handler_calls"] == 1
        assert "_derive_freshness" not in source, "_derive_freshness must not be imported"
        lines = source.split("\n")
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith('"'):
                continue
            assert "pytest.raises(Exception" not in stripped, f"pytest.raises(Exception) found: {stripped}"
            assert "pytest.raises(BaseException" not in stripped, f"pytest.raises(BaseException) found: {stripped}"
        func_defs = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        for v in _load_fixture()["vectors"]:
            test_name = f"test_{v['vector_id'].lower().replace('-', '_')}"
            assert test_name in func_defs, f"Explicit test {test_name} not found"
            assert f"def {v['handler']}" in source, f"Handler {v['handler']} not in source"
            test_func = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == test_name)
            helper_calls = [n for n in ast.walk(test_func) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "_run_handler_twice"]
            assert len(helper_calls) == 1, f"{test_name} must call _run_handler_twice exactly once"
            helper_call = helper_calls[0]
            assert helper_call.args and isinstance(helper_call.args[0], ast.Name) and helper_call.args[0].id == v["handler"]
            assignments = [n for n in ast.walk(test_func) if isinstance(n, ast.Assign) and isinstance(n.value, ast.Call) and n.value is helper_call]
            assert len(assignments) == 1 and len(assignments[0].targets) == 1
            assert isinstance(assignments[0].targets[0], ast.Name) and assignments[0].targets[0].id == "actual"
            direct_calls = [n for n in ast.walk(test_func) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == v["handler"]]
            assert not direct_calls, f"{test_name} must not call {v['handler']} directly"
            vector_calls = [n for n in ast.walk(test_func) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "_get_vector"]
            assert len(vector_calls) == 1, f"{test_name} must call _get_vector exactly once"
            vector_call = vector_calls[0]
            assert len(vector_call.args) == 1 and not vector_call.keywords
            assert isinstance(vector_call.args[0], ast.Constant) and vector_call.args[0].value == v["vector_id"]
            vector_assignments = [n for n in ast.walk(test_func) if isinstance(n, ast.Assign) and n.value is vector_call]
            assert len(vector_assignments) == 1 and len(vector_assignments[0].targets) == 1
            assert isinstance(vector_assignments[0].targets[0], ast.Name) and vector_assignments[0].targets[0].id == "vector"
            def actual_content(node: ast.AST) -> bool:
                if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name) and node.value.id == "actual":
                    return True
                if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "actual":
                    return True
                return any(actual_content(child) for child in ast.iter_child_nodes(node))
            semantic_assertions = [n for n in ast.walk(test_func) if isinstance(n, ast.Assert) and actual_content(n.test)]
            assert semantic_assertions, f"{test_name} must assert actual content"
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("handle_fc08_"):
                has_return = any(
                    isinstance(n, ast.Return) and n.value is not None
                    for n in ast.walk(node)
                )
                assert has_return, f"{node.name} must return normalized result evidence"
                for child in ast.walk(node):
                    if isinstance(child, ast.Return) and child.value is not None:
                        assert not any(isinstance(name, ast.Name) and name.id == "vector_expected" for name in ast.walk(child.value)), (
                            f"{node.name} return value must not reference vector_expected"
                        )
        helper = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "_run_handler_twice")
        def assigned_call(name: str, call_name: str) -> list[ast.Assign]:
            return [
                n for n in ast.walk(helper)
                if isinstance(n, ast.Assign)
                and len(n.targets) == 1
                and isinstance(n.targets[0], ast.Name)
                and n.targets[0].id == name
                and isinstance(n.value, ast.Call)
                and isinstance(n.value.func, ast.Name)
                and n.value.func.id == call_name
            ]
        handler_calls = [
            n for n in ast.walk(helper)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "handler"
        ]
        assert len(handler_calls) == 2, "ALL_RUN_HELPER_HANDLER_CALL_COUNT must be 2"
        result_assignments = assigned_call("result1", "handler") + assigned_call("result2", "handler")
        assert len(result_assignments) == 2, "TWO_RUN_HANDLER_RESULT_ASSIGNMENT_COUNT must be 2"
        assert {n.targets[0].id for n in result_assignments} == {"result1", "result2"}
        for name, input_name, expected_name in (("result1", "input1", "expected1"), ("result2", "input2", "expected2")):
            assignment = assigned_call(name, "handler")
            assert len(assignment) == 1
            call = assignment[0].value
            assert len(call.args) == 2 and not call.keywords
            assert all(isinstance(arg, ast.Name) for arg in call.args)
            assert [arg.id for arg in call.args] == [input_name, expected_name]
        assert len(result_assignments) == len(handler_calls), "EXTRA_RUN_HELPER_HANDLER_CALL_COUNT must be 0"
        normalize_assignments = assigned_call("norm1", "_normalize_result") + assigned_call("norm2", "_normalize_result")
        normalize_calls = [
            n for n in ast.walk(helper)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "_normalize_result"
        ]
        assert len(normalize_calls) == 2, "ALL_NORMALIZE_RESULT_CALL_COUNT must be 2"
        assert len(normalize_assignments) == 2, "EXACT_NORMALIZE_ASSIGNMENT_COUNT must be 2"
        assert [n.targets[0].id for n in normalize_assignments] == ["norm1", "norm2"]
        assert all(len(n.value.args) == 1 and not n.value.keywords and isinstance(n.value.args[0], ast.Name) and n.value.args[0].id == n.targets[0].id.replace("norm", "result") for n in normalize_assignments)
        def exact_assert_count(left: str, right: str) -> int:
            return sum(
                isinstance(n, ast.Assert)
                and isinstance(n.test, ast.Compare)
                and len(n.test.ops) == 1
                and isinstance(n.test.ops[0], ast.Eq)
                and len(n.test.comparators) == 1
                and isinstance(n.test.left, ast.Name) and n.test.left.id == left
                and isinstance(n.test.comparators[0], ast.Name) and n.test.comparators[0].id == right
                for n in ast.walk(helper)
            )
        assert exact_assert_count("norm1", "norm2") == 1
        assert exact_assert_count("input1", "original_input") == 1
        assert exact_assert_count("input2", "original_input") == 1
        assert exact_assert_count("expected1", "original_expected") == 1
        assert exact_assert_count("expected2", "original_expected") == 1
        returns = [n for n in ast.walk(helper) if isinstance(n, ast.Return) and isinstance(n.value, ast.Name) and n.value.id == "norm1"]
        assert len(returns) == 1
        assert sum(isinstance(n, ast.Return) for n in ast.walk(helper)) == 1
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("handle_fc08_safe_read_"):
                src_handler = ast.get_source_segment(source, node)
                assert src_handler is not None, f"Cannot extract source for {node.name}"
                assert "project_catalog_safe_filter_read" in src_handler, (
                    f"{node.name} must call project_catalog_safe_filter_read"
                )
                assert "CatalogSafeFilterReadModel(" not in src_handler, (
                    f"{node.name} must not directly construct CatalogSafeFilterReadModel"
                )
        private_import_pattern = re.compile(
            r"from mayak\.modules\.filter_catalog\.\w+ import.*(?:"
            r"CatalogSafeFilterReadModel|FilterCatalogVersion|"
            r"CatalogPublicationState|FilterDefinitionState|FilterValueKind|"
            r"FilterCapabilityState|FilterCapabilityProfile|"
            r"BuilderDraftValidationResult|BuilderDraftValidationState|"
            r"BeaconOverrideCandidateOutcome|BeaconOverrideCandidateState|"
            r"BeaconOverrideCandidatePreparationResult|"
            r"EvidenceAuthorityReference|FilterEvidenceApprovalRequest|"
            r"MultivaluePreservationRequest|validate_range_value|"
            r"evaluate_filter_semantic_exposure|evaluate_filter_evidence_approval|"
            r"project_builder_field_definition|project_catalog_safe_filter_read|"
            r"evaluate_multivalue_preservation)"
        )
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("mayak.modules.filter_catalog."):
                for alias in node.names:
                    if alias.name.startswith("CatalogSafeFilterRead") and alias.name != "CatalogSafeFilterReadRequest" and alias.name != "CatalogSafeFilterReadAccessContext" and alias.name != "CatalogSafeReadSurfaceState" and alias.name != "CatalogSafeReadAudience" and alias.name != "CatalogSafeExplanationCode" and alias.name != "project_catalog_safe_filter_read":
                        assert False, f"Private production import {alias.name} found in {node.module}"
        dynamic_reflection = len(re.findall(r"getattr\(|importlib\.", source))
        assert dynamic_reflection == 0, f"Dynamic reflection/handler lookup found: {dynamic_reflection}"
