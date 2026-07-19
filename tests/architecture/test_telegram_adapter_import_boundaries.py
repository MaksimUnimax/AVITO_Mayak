from __future__ import annotations

import ast
from pathlib import Path

ALLOWED_ROOTS = {"__future__", "enum", "typing", "pydantic", "mayak"}
FORBIDDEN_SUBSTRINGS = {
    "mayak.modules.identity_and_access",
    "aiogram",
    "telebot",
    "telethon",
    "httpx",
    "requests",
    "fastapi",
    "starlette",
    "sqlalchemy",
    "psycopg",
    "alembic",
    "queue",
    "broker",
    "entrypoint",
    "infra",
    "runtime",
    "getme",
    "getupdates",
    "webhook",
    "polling",
    "deep-link",
    "mini app",
    "database",
    "worker",
    "scheduler",
    "account creation",
    "account merge",
    "token",
    "secret",
    "raw payload",
}


def test_telegram_production_imports_stay_within_transport_neutral_boundary() -> None:
    root = Path(__file__).resolve().parents[2] / "src/mayak/modules/telegram_adapter"
    for path in root.glob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots = [alias.name.split(".", 1)[0] for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                roots = [node.module.split(".", 1)[0]]
            else:
                continue
            assert set(roots) <= ALLOWED_ROOTS, f"{path}: {set(roots) - ALLOWED_ROOTS}"
            if isinstance(node, ast.ImportFrom) and node.module and node.module != "__future__":
                assert node.module in {
                    "enum",
                    "typing",
                    "pydantic",
                    "mayak.modules.telegram_adapter.contracts",
                    "mayak.platform.boundaries",
                    "mayak.contracts",
                }


def test_telegram_production_files_have_no_provider_runtime_storage_or_secret_implementation() -> (
    None
):
    root = Path(__file__).resolve().parents[2] / "src/mayak/modules/telegram_adapter"
    for path in root.glob("*.py"):
        source = path.read_text().lower()
        found = [term for term in FORBIDDEN_SUBSTRINGS if term.lower() in source]
        assert not found, f"{path}: forbidden implementation terms {sorted(found)}"
