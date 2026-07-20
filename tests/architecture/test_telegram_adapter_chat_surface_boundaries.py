from __future__ import annotations

import ast
from pathlib import Path

import pytest

REPO = Path(__file__).parents[2]
PRODUCTION_DIR = REPO / "src/mayak/modules/telegram_adapter"
PRODUCTION = (PRODUCTION_DIR / "contracts.py", PRODUCTION_DIR / "__init__.py")
EXPECTED_DIRECT_ENTRIES = {"contracts.py", "__init__.py"}
TG10_SYMBOLS = (
    "TelegramChatSurfaceClass",
    "TelegramChatSurfaceAdmissionState",
    "TelegramChatSurfaceReasonCode",
    "TelegramUntrustedChatSurfaceReference",
    "TelegramChatSurfaceAdmissionRequest",
    "TelegramChatSurfaceAdmissionOutcome",
)


def _tg10_source(text: str) -> str:
    start = text.find("class TelegramChatSurfaceClass")
    end = text.find("class TelegramUpdateDeduplicationRecord")
    return text[start:end] if start >= 0 and end > start else ""


def _guard(text: str) -> list[str]:
    """Cache-safe guard for TG-10 production entries, with no filesystem reads."""
    violations: list[str] = []
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return ["invalid Python source"]
    forbidden_imports = {
        "telegram",
        "aiogram",
        "telethon",
        "pyrogram",
        "httpx",
        "requests",
        "aiohttp",
        "fastapi",
        "flask",
        "sqlalchemy",
        "psycopg",
        "alembic",
        "celery",
        "redis",
        "importlib",
        "subprocess",
        "socket",
        "pathlib",
    }
    forbidden_calls = {
        "getUpdates",
        "get_updates",
        "setWebhook",
        "set_webhook",
        "webhook",
        "send",
        "render",
        "open",
        "exec",
        "eval",
        "__import__",
        "import_module",
        "system",
    }
    forbidden_words = {
        "botfather",
        "mini_app",
        "frontend",
        "raw_payload",
        "raw_update",
        "raw_message",
        "message_text",
        "profile",
        "contact",
        "account_ownership",
        "ownership_inference",
        "router",
        "handler",
        "state_machine",
        "database",
        "migration",
        "queue",
        "worker",
        "service",
        "deploy",
        "outbound",
        "template",
        "tg11",
    }
    positive_unsupported = {
        "group_supported",
        "supergroup_supported",
        "channel_supported",
        "forum_topic_supported",
        "business_connection_supported",
        "shared_chat_supported",
        "group_business_effect",
    }
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            module = (getattr(node, "module", "") or "").split(".", 1)[0].lower()
            imported_names = {alias.name.split(".", 1)[0].lower() for alias in node.names}
            if module in forbidden_imports:
                violations.append(f"forbidden import: {module}")
            if forbidden_imports.intersection(imported_names):
                violations.append("forbidden import")
            module_name = getattr(node, "module", "") or ""
            if module_name.startswith("mayak.modules.") and module_name != (
                "mayak.modules.telegram_adapter.contracts"
            ):
                violations.append("foreign module import")
        if isinstance(node, ast.Call):
            name = (
                node.func.id if isinstance(node.func, ast.Name) else getattr(node.func, "attr", "")
            )
            if name in forbidden_calls:
                violations.append(f"forbidden call: {name}")
        if (
            isinstance(node, ast.Name)
            and node.id.casefold() in forbidden_words | positive_unsupported
        ):
            violations.append(f"forbidden name: {node.id}")
        if isinstance(node, ast.ClassDef):
            class_name = node.name.casefold()
            if any(word in class_name for word in forbidden_words):
                violations.append("forbidden runtime artifact")
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            lowered = node.value.casefold()
            if any(word in lowered for word in forbidden_words):
                violations.append("forbidden runtime artifact")
            if "api.telegram.org" in lowered:
                violations.append("provider API")
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id.casefold() in positive_unsupported:
                violations.append("positive unsupported-surface flag")
            if isinstance(node.value, ast.Constant) and node.value.value is True:
                if "unsupported" not in node.target.id.casefold() and any(
                    token in node.target.id.casefold()
                    for token in ("group", "channel", "topic", "business", "shared")
                ):
                    violations.append("positive unsupported-surface value")
    return violations


def test_exact_production_entries_no_new_production_file_and_cache_safe() -> None:
    entries = {entry.name for entry in PRODUCTION_DIR.iterdir() if entry.name != "__pycache__"}
    assert entries == EXPECTED_DIRECT_ENTRIES
    assert all(path.is_file() for path in PRODUCTION)
    assert _guard(_tg10_source((PRODUCTION_DIR / "contracts.py").read_text())) == []
    init_tree = ast.parse((PRODUCTION_DIR / "__init__.py").read_text())
    assert not any(
        isinstance(node, (ast.Import, ast.ImportFrom))
        and (getattr(node, "module", "") or "").startswith(
            ("telegram", "httpx", "requests", "mayak.modules.identity_and_access")
        )
        for node in ast.walk(init_tree)
    )


def test_tg10_exports_are_exact_and_surface_gate_is_negative() -> None:
    from mayak.modules import telegram_adapter
    from mayak.modules.telegram_adapter import contracts

    for exports in (contracts.__all__, telegram_adapter.__all__):
        assert tuple(name for name in exports if name in TG10_SYMBOLS) == TG10_SYMBOLS
        assert len(exports) == len(set(exports))


@pytest.mark.parametrize(
    ("negative", "expected"),
    (
        ("import httpx\nhttpx.post('x')", "forbidden import"),
        ("from mayak.modules.identity_and_access import Identity", "foreign module import"),
        ("client.getUpdates()", "forbidden call"),
        ("client.send('x')", "forbidden call"),
        ("class TelegramWebhookHandler: pass", "forbidden runtime artifact"),
        ("class Model:\n    raw_payload: str", "forbidden name"),
        ("class Model:\n    group_supported: bool = True", "positive unsupported-surface"),
        ("import importlib\nimportlib.import_module('x')", "forbidden import"),
        ("open('secret')", "forbidden call"),
        ("class Worker: pass", "forbidden runtime artifact"),
    ),
)
def test_guard_rejects_real_negative_controls(negative: str, expected: str) -> None:
    assert any(expected in violation for violation in _guard(negative))


def test_guard_accepts_transport_neutral_private_only_contract_shape() -> None:
    safe = """
from typing import Literal
from pydantic import BaseModel
class Model(BaseModel):
    private_chat_only_v1: Literal[True] = True
    unsupported_surface_business_effect: Literal[False] = False
    chat_surface_establishes_internal_account_ownership: Literal[False] = False
    provider_call_authority: Literal[False] = False
"""
    assert _guard(safe) == []
