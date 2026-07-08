from __future__ import annotations

import ast
from pathlib import Path


ALLOWED_IMPORT_ROOTS = {
    "__future__",
    "datetime",
    "enum",
    "contracts",
    "mayak",
    "pydantic",
    "policies",
    "typing",
}

MODULE_FILE = Path("src/mayak/modules/entitlements_and_billing/usage_consumption.py")


def _import_roots(source: str) -> set[str]:
    tree = ast.parse(source)
    roots: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".", 1)[0])
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            roots.add(node.module.split(".", 1)[0])

    return roots


def test_eb06_no_runtime_db_provider_imports_001() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    source = (repo_root / MODULE_FILE).read_text()
    forbidden_imports = _import_roots(source) - ALLOWED_IMPORT_ROOTS

    assert forbidden_imports == set(), sorted(forbidden_imports)
