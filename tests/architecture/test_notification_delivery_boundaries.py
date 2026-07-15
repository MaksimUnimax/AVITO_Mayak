from __future__ import annotations

import ast
from pathlib import Path

ALLOWED_IMPORT_ROOTS = {
    "__future__",
    "dataclasses",
    "enum",
    "mayak",
}

FORBIDDEN_IMPORT_ROOTS = {
    "aiohttp",
    "alembic",
    "aiogram",
    "fastapi",
    "httpx",
    "psycopg",
    "psycopg2",
    "queue",
    "requests",
    "socket",
    "sqlalchemy",
    "subprocess",
    "telethon",
}

FORBIDDEN_SOURCE_TOKENS = {
    "requests",
    "httpx",
    "aiohttp",
    "socket",
    "subprocess",
    "sqlalchemy",
    "psycopg",
    "alembic",
    "fastapi",
    "telethon",
    "aiogram",
    "datetime",
    "time",
    "queue",
    "worker",
    "broker",
    "cache",
    "filesystem",
    "network",
    "telegram",
    "max",
}

FORBIDDEN_FIELD_NAMES = {
    "raw_payload",
    "body",
    "html",
    "json",
    "cookie",
    "token",
    "secret",
    "credential",
    "provider_payload",
    "delivery_result",
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
            assert not node.module.startswith("mayak.modules"), node.module

    return roots


def _field_names(source: str) -> set[str]:
    tree = ast.parse(source)
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            for statement in node.body:
                if isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
                    names.add(statement.target.id)
    return names


def test_notification_delivery_source_intake_stays_within_allowed_import_boundary() -> None:
    source_path = Path("src/mayak/modules/notification_delivery/source_intake.py")
    source = source_path.read_text()
    roots = _import_roots(source)
    assert roots <= ALLOWED_IMPORT_ROOTS
    assert roots.isdisjoint(FORBIDDEN_IMPORT_ROOTS)


def test_notification_delivery_source_intake_avoids_forbidden_runtime_tokens_and_payload_fields(
    ) -> None:
    source_path = Path("src/mayak/modules/notification_delivery/source_intake.py")
    source = source_path.read_text().lower()
    for token in FORBIDDEN_SOURCE_TOKENS:
        assert token not in source, token

    field_names = _field_names(source_path.read_text())
    assert field_names.isdisjoint(FORBIDDEN_FIELD_NAMES)
