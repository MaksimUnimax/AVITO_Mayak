from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).parents[2] / "src/mayak/modules/telegram_adapter"
FORBIDDEN = (
    "identity_and_access",
    "aiogram",
    "telethon",
    "httpx",
    "requests",
    "fastapi",
    "sqlalchemy",
    "psycopg",
    "alembic",
    "queue",
    "broker",
    "runtime",
    "webhook",
    "getupdates",
    "polling",
    "raw payload",
    "token",
    "secret",
    "database",
    "migration",
    "command",
    "callback",
    "deep-link",
    "mini app",
    "group",
    "channel",
    "persistence",
)


def test_production_imports_are_transport_neutral_and_module_local() -> None:
    for path in ROOT.glob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            else:
                continue
            assert all(
                name.split(".", 1)[0] in {"__future__", "enum", "typing", "pydantic", "mayak"}
                for name in names
            )
            assert not any(
                name.startswith("mayak.modules.")
                and name != "mayak.modules.telegram_adapter.contracts"
                for name in names
            )


def test_production_has_no_provider_runtime_storage_dispatch_or_weak_input_boundary() -> None:
    for path in ROOT.glob("*.py"):
        source = path.read_text().lower()
        assert not [term for term in FORBIDDEN if term in source], path
