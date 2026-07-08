from __future__ import annotations

import ast
from pathlib import Path

ALLOWED_IMPORT_ROOTS = {
    "__future__",
    "enum",
    "mayak",
    "pydantic",
    "typing",
    "uuid",
}

PUBLIC_PRIMITIVE_FILES = (
    Path("src/mayak/contracts/configuration.py"),
    Path("src/mayak/contracts/__init__.py"),
    Path("src/mayak/contracts/errors.py"),
    Path("src/mayak/contracts/idempotency.py"),
    Path("src/mayak/contracts/metadata.py"),
    Path("src/mayak/contracts/results.py"),
    Path("src/mayak/platform/config.py"),
    Path("src/mayak/platform/__init__.py"),
    Path("src/mayak/platform/errors.py"),
    Path("src/mayak/platform/idempotency.py"),
    Path("src/mayak/platform/redaction.py"),
)


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


def test_public_contract_primitives_do_not_import_forbidden_frameworks_or_sdks() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    for relative_path in PUBLIC_PRIMITIVE_FILES:
        source = (repo_root / relative_path).read_text()
        forbidden_imports = _import_roots(source) - ALLOWED_IMPORT_ROOTS
        assert forbidden_imports == set(), f"{relative_path}: {sorted(forbidden_imports)}"
