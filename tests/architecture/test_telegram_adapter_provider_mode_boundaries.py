from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).parents[2]
SOURCE = ROOT / "src/mayak/modules/telegram_adapter/contracts.py"
INIT = ROOT / "src/mayak/modules/telegram_adapter/__init__.py"


def trees() -> list[ast.AST]:
    return [ast.parse(path.read_text()) for path in (SOURCE, INIT)]


def test_provider_mode_source_has_no_provider_or_transport_imports() -> None:
    forbidden = {
        "httpx",
        "requests",
        "fastapi",
        "flask",
        "aiohttp",
        "aiogram",
        "telethon",
        "telegram",
    }
    for tree in trees():
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert all(alias.name.split(".")[0] not in forbidden for alias in node.names)
            if isinstance(node, ast.ImportFrom):
                assert (node.module or "").split(".")[0] not in forbidden


def test_each_provider_operation_alias_and_url_is_absent() -> None:
    tree = ast.parse(SOURCE.read_text())
    forbidden_calls = {
        "getUpdates",
        "get_updates",
        "setWebhook",
        "set_webhook",
        "deleteWebhook",
        "delete_webhook",
        "getWebhookInfo",
        "get_webhook_info",
        "poll",
        "serve",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in forbidden_calls
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            assert "api.telegram.org" not in node.value


def test_production_module_contains_only_contract_declarations() -> None:
    tree = ast.parse(SOURCE.read_text())
    forbidden_names = {
        "TelegramProvider",
        "TelegramClient",
        "HTTPClient",
        "PollingWorker",
        "Scheduler",
        "Repository",
        "endpoint",
        "polling_loop",
    }
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            assert node.name not in forbidden_names
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    assert target.id not in {
                        "provider",
                        "client",
                        "worker",
                        "scheduler",
                        "repository",
                        "endpoint",
                    }


def test_no_unsafe_payload_or_concrete_operation_fields() -> None:
    unsafe = {
        "token_value",
        "secret_value",
        "secret_header",
        "raw_request",
        "raw_update",
        "endpoint_url",
        "hostname",
        "domain",
        "port_number",
        "certificate",
        "cursor_value",
        "provider_client",
    }
    tree = ast.parse(SOURCE.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            assert node.target.id not in unsafe


def test_no_top_level_runtime_instances_or_business_dispatch() -> None:
    tree = ast.parse(SOURCE.read_text())
    for node in tree.body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            raise AssertionError("production module must not instantiate runtime objects")
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
            raise AssertionError("production module must not create top-level runtime objects")
