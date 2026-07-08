from __future__ import annotations

import ast
from pathlib import Path

MODULE_PATH = Path("src/mayak/modules/entitlements_and_billing/subscription_lifecycle.py")

ALLOWED_IMPORT_ROOTS = {
    "__future__",
    "contracts",
    "datetime",
    "enum",
    "mayak",
    "pydantic",
    "policies",
    "typing",
}


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


def test_subscription_lifecycle_contract_file_does_not_import_forbidden_frameworks_or_sdks() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    source = (repo_root / MODULE_PATH).read_text()
    forbidden_imports = _import_roots(source) - ALLOWED_IMPORT_ROOTS
    assert forbidden_imports == set(), f"{MODULE_PATH}: {sorted(forbidden_imports)}"
