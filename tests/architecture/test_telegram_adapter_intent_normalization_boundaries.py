from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "src/mayak/modules/telegram_adapter"
FORBIDDEN_ROOTS = {"os", "pathlib", "subprocess", "shutil", "hashlib", "base64", "requests", "httpx", "aiohttp", "urllib", "aiogram", "telebot", "telethon", "pyrogram", "sqlalchemy", "psycopg", "alembic", "celery", "redis", "kombu", "pika"}  # noqa: E501
ALLOWED_MAYAK = {"mayak.contracts", "mayak.modules.telegram_adapter.contracts", "mayak.platform.boundaries"}  # noqa: E501
FORBIDDEN_CALLS = {"urlparse", "urlsplit", "urljoin", "get", "post", "request", "create_engine", "sessionmaker", "getUpdates", "get_updates", "setWebhook", "set_webhook", "dispatch", "handle", "create_beacon", "pause_beacon", "delete_beacon", "send_notification", "setattr"}  # noqa: E501
FORBIDDEN_FIELDS = {"raw_payload", "provider_payload", "raw_update", "raw_text", "message_text", "url", "callback_data", "deep_link", "token", "secret", "credential", "password", "private_key"}  # noqa: E501
FORBIDDEN_DECLARATION_PARTS = ("handler", "service", "repository", "worker", "client", "runtime")


def violations(source: str) -> list[str]:
    tree = ast.parse(source)
    out: list[str] = []
    for top_node in tree.body:
        if isinstance(top_node, ast.Assign) and isinstance(top_node.value, ast.Call):
            out.append("top-level instance")
    stdlib: set[str] = set(getattr(sys, "stdlib_module_names", set()))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".", 1)[0]
                if root in FORBIDDEN_ROOTS or (root == "mayak" and alias.name not in ALLOWED_MAYAK):
                    out.append("import")
                elif root not in stdlib and root not in {"pydantic"}:
                    out.append("unknown import")
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            root = module.split(".", 1)[0]
            if root in FORBIDDEN_ROOTS or (root == "mayak" and module not in ALLOWED_MAYAK):
                out.append("from import")
        elif isinstance(node, ast.Call) and isinstance(node.func, (ast.Name, ast.Attribute)):
            name = node.func.id if isinstance(node.func, ast.Name) else node.func.attr
            if name in FORBIDDEN_CALLS:
                out.append("call")
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id in FORBIDDEN_FIELDS:
                out.append("field")
            if isinstance(node.annotation, ast.Subscript) and isinstance(node.annotation.value, ast.Name) and node.annotation.value.id == "Annotated":  # noqa: E501
                out.append("annotated evasion")
        elif isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Subscript):
            target_subscript = node.targets[0]
            if isinstance(target_subscript, ast.Subscript) and isinstance(target_subscript.value, ast.Name) and target_subscript.value.id == "__annotations__":  # noqa: E501
                out.append("dynamic annotations")
        elif isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            target_node = node.targets[0] if isinstance(node, ast.Assign) else node.target
            if isinstance(target_node, ast.Name) and target_node.id == "__annotations__":
                out.append("dynamic annotations")
        elif isinstance(node, ast.ClassDef) and any(part in node.name.lower() for part in FORBIDDEN_DECLARATION_PARTS):  # noqa: E501
            out.append("runtime declaration")
    return out


def test_production_files_pass_boundary_guard() -> None:
    for path in ROOT.glob("*.py"):
        assert violations(path.read_text()) == [], path


def test_guard_catches_alias_positions_foreign_imports_runtime_and_mutation() -> None:
    unsafe = (
        "import os, enum, pathlib",
        "import enum, httpx, typing",
        "import typing, shutil",
        "from mayak.modules.identity_and_access import Account",
        "from pathlib import Path",
        "def f():\n    return get_updates()",
        "class Handler: pass",
        "class X:\n    raw_payload: str",
        "__annotations__['x'] = str",
        "top = object()",
        "setattr(X, 'field', str)",
        "from typing import Annotated\nclass X:\n    safe: Annotated[bool, 'false'] = False",
    )
    for source in unsafe:
        assert violations(source), source


def test_safe_semantic_snippets_pass() -> None:
    for source in (
        "from mayak.contracts import ContractMetadata",
        "from mayak.platform.boundaries import TELEGRAM_ADAPTER_MODULE_ID",
        "from mayak.modules.telegram_adapter.contracts import TelegramProviderIdentity",
        "from typing import Literal\nclass X:\n    allowed: Literal[False] = False",
    ):
        assert violations(source) == [], source
