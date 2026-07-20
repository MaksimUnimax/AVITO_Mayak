from __future__ import annotations

# ruff: noqa: E501
import ast
from pathlib import Path

ROOT = Path(__file__).parents[2]
PRODUCTION = ROOT / "src" / "mayak" / "modules" / "telegram_adapter"


def test_provider_outcome_keeps_the_two_file_production_surface() -> None:
    assert {p.name for p in PRODUCTION.glob("*.py")} == {"contracts.py", "__init__.py"}


def test_provider_outcome_has_no_foreign_import_or_dynamic_runtime() -> None:
    for path in PRODUCTION.glob("*.py"):
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                assert not (node.module or "").startswith("mayak.modules.") or node.module == (
                    "mayak.modules.telegram_adapter.contracts"
                )
            if isinstance(node, ast.Import):
                assert all(not a.name.startswith("mayak.modules.") for a in node.names)
        lowered = "\n".join(
            ast.get_source_segment(source, node) or ""
            for node in ast.walk(tree)
            if isinstance(node, ast.ClassDef)
            and (
                node.name.startswith("TelegramProvider")
                or node.name.startswith("TelegramTransport")
                or node.name.startswith("TelegramNotificationProvider")
            )
        ).lower()
        for forbidden in (
            "httpx",
            "aiohttp",
            "importlib",
            "sqlalchemy",
            "psycopg",
            "alembic",
            "telegram api",
            "requests.get",
            "client.post",
        ):
            assert forbidden not in lowered


def test_provider_outcome_is_semantic_only() -> None:
    source = (PRODUCTION / "contracts.py").read_text(encoding="utf-8").lower()
    for forbidden in (
        "provider_call_performed: literal[true]",
        "notification_delivery_accepted: literal[true]",
        "human_read_or_click_proven: literal[true]",
        "business_success_proven: literal[true]",
    ):
        assert forbidden not in source
