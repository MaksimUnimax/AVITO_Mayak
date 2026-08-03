from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path("src/mayak/modules/notification_delivery")
RUNTIME = ROOT / "runtime.py"


def test_rf17_runtime_has_no_live_provider_or_broker_imports() -> None:
    tree = ast.parse(RUNTIME.read_text(encoding="utf-8"))
    roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0])
    assert roots.isdisjoint(
        {"httpx", "requests", "aiohttp", "aiogram", "telethon", "redis", "celery", "kombu", "pika"}
    )


def test_rf17_runtime_names_only_the_existing_notification_tables() -> None:
    source = RUNTIME.read_text(encoding="utf-8")
    assert "notification_events" in source
    assert "notification_outbox" in source
    assert "notification_delivery_attempts" in source
    assert "notification_delivery_reconciliations" in source
    assert "notification_endpoints" in source
    assert "rabbitmq" not in source.lower()
    assert "kafka" not in source.lower()
    assert "celery" not in source.lower()


def test_rf17_runtime_does_not_persist_raw_provider_material() -> None:
    source = RUNTIME.read_text(encoding="utf-8").lower()
    for forbidden in (
        "raw_provider_payload",
        "authorization",
        "cookies",
        "provider_token",
        "http://",
        "https://",
    ):
        assert forbidden not in source


def test_rf17_runtime_has_no_process_or_filesystem_execution() -> None:
    tree = ast.parse(RUNTIME.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = (
                node.func.id
                if isinstance(node.func, ast.Name)
                else node.func.attr
                if isinstance(node.func, ast.Attribute)
                else ""
            )
            assert name not in {"exec", "eval", "system", "popen", "run"}
