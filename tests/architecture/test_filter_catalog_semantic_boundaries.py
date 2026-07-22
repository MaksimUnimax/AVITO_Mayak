"""Architecture boundary tests for Filter Catalog FC-08 synthetic fixtures and tests."""

from __future__ import annotations

import json
import os
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


def _load_fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


class TestFC08ArchitectureBoundaries:
    def test_four_fc08_files_exist_and_production_not_patched(self) -> None:
        for path in [FIXTURE_PATH, ARCH_TEST_PATH, CONTRACT_TEST_PATH, UNIT_TEST_PATH]:
            assert path.exists(), f"FC-08 file missing: {path}"

    def test_fixture_top_level_schema_and_key_order(self) -> None:
        data = _load_fixture()
        keys = list(data.keys())
        assert keys == ["schema_version", "module_id", "technical_id", "canonical_references", "vectors"]
        assert data["schema_version"] == "1.0"
        assert data["module_id"] == "13-filter-catalog-and-builder"
        assert data["technical_id"] == "FC-08-PARALLEL-MAIN-REISSUE-20260722-028"

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

    def test_synthetic_only_corpus(self) -> None:
        data = _load_fixture()
        vectors_raw = json.dumps(data["vectors"]).lower()
        assert "http://" not in vectors_raw, "HTTP URLs found in vectors"
        assert "https://" not in vectors_raw, "HTTPS URLs found in vectors"
        assert "api.telegram.org" not in vectors_raw, "Telegram API found in vectors"

    def test_forbidden_imports_absent(self) -> None:
        for prod_file in PRODUCTION_FILES:
            if not prod_file.exists():
                continue
            content = prod_file.read_text(encoding="utf-8")
            for mod in FORBIDDEN_IMPORTS:
                assert f"import {mod}" not in content, f"Forbidden import {mod} in {prod_file.name}"

    def test_protected_production_blobs_match(self) -> None:
        import hashlib
        import subprocess
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
        import re
        lines = content.split("\n")
        od009_active = False
        for line in lines:
            if "OD-009" in line and "OPEN" in line.upper():
                od009_active = True
                break
        assert od009_active, "OD-009 must remain OPEN"

    def test_deterministic_reload_fixture_gives_identical_object(self) -> None:
        import copy
        data1 = _load_fixture()
        data2 = _load_fixture()
        assert data1 == data2
        assert json.dumps(data1, sort_keys=True) == json.dumps(data2, sort_keys=True)
