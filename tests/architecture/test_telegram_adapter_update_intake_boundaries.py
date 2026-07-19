from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "src/mayak/modules/telegram_adapter"
FORBIDDEN_IMPORT_PREFIXES = {
    "aiogram", "telebot", "telethon", "pyrogram", "httpx", "requests", "aiohttp",
    "urllib3", "fastapi", "starlette", "flask", "django", "sqlalchemy", "psycopg",
    "alembic", "celery", "redis", "kombu", "pika",
}
FORBIDDEN_CALL_NAMES = {
    "getUpdates", "get_updates", "setWebhook", "set_webhook", "deleteWebhook",
    "delete_webhook", "getWebhookInfo", "get_webhook_info", "start_polling",
    "run_polling", "poll_forever", "serve_forever", "create_engine", "sessionmaker",
}
FORBIDDEN_VALUE_FIELDS = {
    "raw_payload", "provider_payload", "raw_update", "bot_token", "token_value",
    "secret_value", "secret_token", "webhook_secret", "private_key", "private_key_value",
    "message_archive", "private_message_archive",
}
FORBIDDEN_DECLARATIONS = {
    "TelegramClient", "TelegramBotClient", "TelegramWebhookEndpoint", "TelegramPollingLoop",
    "TelegramWorker", "TelegramRuntimeService", "TelegramRepository",
}
ALLOWED_MAYAK_IMPORTS = {
    "mayak.contracts", "mayak.modules.telegram_adapter.contracts", "mayak.platform.boundaries",
}


def _import_names(node: ast.Import | ast.ImportFrom) -> list[str]:
    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names]
    return [node.module] if node.module else []


def _terminal_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""


def _assigned_names(node: ast.AST) -> list[str]:
    if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        return [target.id for target in targets if isinstance(target, ast.Name)]
    return []


def _guard_violations(source: str) -> list[str]:
    tree = ast.parse(source)
    violations: list[str] = []
    stdlib: set[str] = getattr(sys, "stdlib_module_names", set())
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for name in _import_names(node):
                root = name.split(".", 1)[0]
                if root in FORBIDDEN_IMPORT_PREFIXES:
                    violations.append(f"forbidden import: {name}")
                elif root == "mayak":
                    if name not in ALLOWED_MAYAK_IMPORTS:
                        violations.append(f"foreign mayak import: {name}")
                elif root not in stdlib and root not in {"pydantic"}:
                    violations.append(f"non-whitelisted import: {name}")
        elif isinstance(node, ast.Call):
            name = _terminal_name(node.func)
            if name in FORBIDDEN_CALL_NAMES:
                violations.append(f"forbidden call: {name}")
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            if "api.telegram.org" in node.value:
                violations.append("provider URL literal")
        for name in _assigned_names(node):
            if name in FORBIDDEN_VALUE_FIELDS:
                violations.append(f"unsafe value field: {name}")
        if (
            isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
            and node in tree.body
        ):
            if node.name in FORBIDDEN_DECLARATIONS:
                violations.append(f"forbidden declaration: {node.name}")
    return violations


def test_production_imports_are_transport_neutral_and_module_local() -> None:
    for path in ROOT.glob("*.py"):
        violations = _guard_violations(path.read_text())
        assert not violations, f"{path}: {violations}"


def test_production_has_no_provider_runtime_storage_or_weak_input_boundary() -> None:
    for path in ROOT.glob("*.py"):
        violations = _guard_violations(path.read_text())
        assert not violations, f"{path}: {violations}"


def test_ast_guard_rejects_calls_urls_unsafe_fields_and_runtime_declarations() -> None:
    unsafe_sources = (
        "def intake():\n    return get_updates()",
        "client.set_webhook('policy-ref')",
        "PROVIDER = 'https://api.telegram.org/bot/placeholder'",
        "class Record:\n    raw_payload: str",
        "class Record:\n    bot_token: str",
        "class TelegramWebhookEndpoint:\n    pass",
    )
    for source in unsafe_sources:
        assert _guard_violations(source), source


def test_ast_guard_rejects_every_forbidden_multi_alias_import() -> None:
    unsafe_sources = (
        "import os, httpx",
        "import httpx, os",
        "import pathlib, sqlalchemy",
        "import enum, aiogram",
        "import typing, telethon",
        "import sys, mayak.modules.identity_and_access",
        "import pydantic, requests",
        "import os, sys, httpx, pathlib",
    )
    for source in unsafe_sources:
        assert _guard_violations(source), source


def test_ast_guard_allows_safe_and_contract_imports() -> None:
    safe_sources = (
        "import os, sys",
        "import pathlib, enum, typing",
        "import pydantic",
        "from mayak.contracts import ContractMetadata",
        "from mayak.platform.boundaries import TELEGRAM_ADAPTER_MODULE_ID",
        "from mayak.modules.telegram_adapter.contracts import TelegramProviderIdentity",
    )
    for source in safe_sources:
        assert _guard_violations(source) == [], source


def test_ast_guard_allows_semantic_names_references_and_documentation() -> None:
    source = '''
from enum import Enum

class ProviderMode(str, Enum):
    WEBHOOK = "WEBHOOK"
    GET_UPDATES = "GET_UPDATES"

class SemanticContract:
    webhook_authenticity_policy_ref: str
    get_updates_offset_advancement_policy_ref: str
    callback_payload_fingerprint: str
    private_chat_surface_ref: str
    token_secret_reference_id: str

"mutually exclusive modes; group/channel unsupported boundary"
'''
    assert _guard_violations(source) == []
