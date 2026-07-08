from __future__ import annotations

import ast
from pathlib import Path

ALLOWED_IMPORT_ROOTS = {
    "__future__",
    "enum",
    "mayak",
    "pydantic",
    "typing",
}

IDENTITY_AND_ACCESS_FILES = (
    Path("src/mayak/modules/identity_and_access/__init__.py"),
    Path("src/mayak/modules/identity_and_access/contracts.py"),
    Path("src/mayak/modules/identity_and_access/fixtures.py"),
)

FORBIDDEN_IMPORT_ROOTS = {
    "alembic",
    "asyncpg",
    "aiogram",
    "authlib",
    "bcrypt",
    "botocore",
    "boto3",
    "databases",
    "django",
    "fastapi",
    "httpx",
    "jwt",
    "max",
    "orjson",
    "passlib",
    "psycopg",
    "requests",
    "sqlalchemy",
    "sqlmodel",
    "starlette",
    "telegram",
    "telethon",
    "uvicorn",
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


def test_identity_and_access_files_do_not_import_runtime_frameworks_or_sdks() -> None:
    repo_root = Path(__file__).resolve().parents[2]

    for relative_path in IDENTITY_AND_ACCESS_FILES:
        source = (repo_root / relative_path).read_text()
        import_roots = _import_roots(source)
        forbidden = (import_roots - ALLOWED_IMPORT_ROOTS) & FORBIDDEN_IMPORT_ROOTS
        assert forbidden == set(), f"{relative_path}: {sorted(forbidden)}"
