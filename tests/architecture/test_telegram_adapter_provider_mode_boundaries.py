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


def _has_annotations_mutation(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if (
                    isinstance(target, ast.Subscript)
                    and isinstance(target.value, ast.Name)
                    and target.value.id == "__annotations__"
                ):
                    return True
    return any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "setattr"
        for node in ast.walk(tree)
    )


def _has_built_safety_field_name(tree: ast.AST) -> bool:
    safety_fields = {
        "http_acknowledgement_is_business_success",
        "provider_runtime_authorized",
    }
    def joined_string(node: ast.AST) -> str | None:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            left = joined_string(node.left)
            right = joined_string(node.right)
            if left is not None and right is not None:
                return left + right
        return None

    for node in ast.walk(tree):
        if isinstance(node, ast.BinOp) and joined_string(node) in safety_fields:
            return True
    return False


def test_safety_fields_are_direct_annassign_declarations() -> None:
    tree = ast.parse(SOURCE.read_text())
    assert not _has_annotations_mutation(tree)
    assert not _has_built_safety_field_name(tree)
    expected = {
        "TelegramWebhookModeRequirements": "http_acknowledgement_is_business_success",
        "TelegramProviderModeBoundary": "provider_runtime_authorized",
    }
    classes = {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.ClassDef)
    }
    for class_name, field_name in expected.items():
        declarations = [
            node
            for node in classes[class_name].body
            if isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == field_name
        ]
        assert len(declarations) == 1


def test_safety_field_regression_rejects_dynamic_declarations() -> None:
    unsafe_snippets = (
        '__annotations__["field"] = Literal[False]',
        '__annotations__["provider_" + "runtime_authorized"] = Literal[False]',
        'setattr(Model, "provider_runtime_authorized", Literal[False])',
    )
    for snippet in unsafe_snippets:
        tree = ast.parse(snippet)
        assert _has_annotations_mutation(tree) or _has_built_safety_field_name(tree)


def test_safety_field_regression_allows_typed_declarations() -> None:
    tree = ast.parse(
        "class Model:\n"
        "    http_acknowledgement_is_business_success: Literal[False] = False\n"
        "    provider_runtime_authorized: Literal[False] = False\n"
    )
    assert not _has_annotations_mutation(tree)
    assert not _has_built_safety_field_name(tree)
