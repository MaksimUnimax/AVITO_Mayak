"""Architecture boundary tests for Filter Catalog FC-08 synthetic fixtures and tests."""

from __future__ import annotations

import ast
import json
import os
import re
import subprocess
from pathlib import Path

import pytest

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
        result = subprocess.run(
            ["git", "diff", "--name-only", f"{FC08_BASE_SHA}...HEAD"],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        committed_paths = sorted(result.stdout.strip().split("\n")) if result.stdout.strip() else []
        result2 = subprocess.run(
            ["git", "diff", "--name-only", "--cached"],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        result3 = subprocess.run(
            ["git", "diff", "--name-only"],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        working_paths = result2.stdout.strip().split("\n") if result2.stdout.strip() else []
        working_paths += result3.stdout.strip().split("\n") if result3.stdout.strip() else []
        all_paths = sorted(set(committed_paths + [p for p in working_paths if p]))
        assert all_paths == EXPECTED_FC08_PATHS, (
            f"FC-08 path set mismatch: expected {EXPECTED_FC08_PATHS}, got {all_paths}"
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
            test_src = ast.get_source_segment(source, test_func)
            assert test_src is not None, f"Cannot extract source for {test_name}"
            assert f'"{v["vector_id"]}"' in test_src or f"'{v['vector_id']}'" in test_src, (
                f"{test_name} must contain exact literal vector ID {v['vector_id']}"
            )
            assert test_src.count("_run_handler_twice") == 1, f"{test_name} must call _run_handler_twice exactly once"
            assert f"{v['handler']}(" not in test_src.replace("_run_handler_twice(", ""), (
                f"{test_name} must not call {v['handler']} directly outside _run_handler_twice"
            )
            assert "actual = _run_handler_twice" in test_src, f"{test_name} must assign result to actual"
            test_lines = test_src.split("\n")
            assert_lines = []
            for l in test_lines:
                s = l.strip()
                if s.startswith("assert ") and "norm1" not in s and "original_" not in s:
                    assert_lines.append(s)
            semantic_assertions = [
                l for l in assert_lines
                if ("actual[" in l or "actual." in l)
                and "actual is not None" not in l
                and l.strip() != "assert actual"
            ]
            non_trivial_assertions = [
                l for l in assert_lines
                if "is not None" not in l
                and l.strip() != "assert actual"
            ]
            assert len(semantic_assertions) > 0 or len(non_trivial_assertions) > 0, (
                f"{test_name} must have at least one semantic assertion on actual; "
                f"found only existence/type assertions"
            )
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("handle_fc08_"):
                has_return = any(
                    isinstance(n, ast.Return) and n.value is not None
                    for n in ast.walk(node)
                )
                assert has_return, f"{node.name} must return normalized result evidence"
                handler_src = ast.get_source_segment(source, node)
                assert handler_src is not None, f"Cannot extract source for {node.name}"
                for child in ast.walk(node):
                    if isinstance(child, ast.Return) and child.value is not None:
                        ret_src = ast.get_source_segment(source, child)
                        assert ret_src is not None or "vector_expected" not in handler_src.split("return")[1] if "return" in handler_src else True, (
                            f"{node.name} return must not reference vector_expected"
                        )
                return_section = handler_src[handler_src.rfind("return"):]
                assert "vector_expected" not in return_section, (
                    f"{node.name} return value must not reference vector_expected"
                )
        assert "norm1 == norm2" in source, "Normalized result equality check must exist"
        assert "original_input" in source, "Input immutability check must exist"
        assert "original_expected" in source, "Expected immutability check must exist"
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
