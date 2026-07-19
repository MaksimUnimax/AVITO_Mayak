from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).parents[2]
SOURCE = ROOT / "src/mayak/modules/telegram_adapter/contracts.py"
INIT = ROOT / "src/mayak/modules/telegram_adapter/__init__.py"
NEW_CLASSES = {
    "TelegramExistingBotEvidenceState", "TelegramExistingBotMetadata",
    "TelegramProtectedSecretPresenceEvidence", "TelegramPublicBotMetadataPresenceEvidence",
    "TelegramExistingBotOperationalGate",
}


def trees() -> list[ast.AST]:
    return [ast.parse(path.read_text()) for path in (SOURCE, INIT)]


def test_all_import_aliases_and_import_from_modules_are_safe() -> None:
    forbidden = {
        "os", "pathlib", "subprocess", "shutil", "hashlib", "base64", "httpx", "requests",
        "aiohttp", "fastapi", "flask", "telegram", "aiogram", "telethon",
    }
    for tree in trees():
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert all(alias.name.split(".")[0] not in forbidden for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                assert (node.module or "").split(".")[0] not in forbidden


def test_no_io_hash_provider_or_mutation_calls_and_no_urls() -> None:
    forbidden_calls = {
        "open", "read", "read_text", "read_bytes", "stat", "lstat", "getsize", "sha1",
        "sha256", "sha512", "md5", "b64encode", "getMe", "getUpdates", "setWebhook",
        "deleteWebhook", "poll", "serve", "setattr",
    }
    tree = ast.parse(SOURCE.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id not in forbidden_calls
            if isinstance(node.func, ast.Attribute):
                assert node.func.attr not in forbidden_calls
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            assert "api.telegram.org" not in node.value


def test_production_has_only_contract_declarations_and_direct_safety_annotations() -> None:
    tree = ast.parse(SOURCE.read_text())
    classes = {node.name: node for node in tree.body if isinstance(node, ast.ClassDef)}
    assert NEW_CLASSES <= classes.keys()
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            assert not any(
                word in node.name.lower() for word in ("client", "worker", "service", "repository")
            )
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            assert node.target.id not in {
                "token_value", "secret_value", "raw_payload", "raw_update", "endpoint_url",
                "provider_client",
            }
    for node in tree.body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            raise AssertionError("no top-level model instances")
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
            raise AssertionError("no top-level runtime instances")
    for class_name in NEW_CLASSES - {"TelegramExistingBotEvidenceState"}:
        assert any(isinstance(item, ast.AnnAssign) for item in classes[class_name].body)


def test_unsafe_synthetic_snippets_are_rejected_by_same_ast_rules() -> None:
    forbidden = {"open", "sha256", "getUpdates", "setattr"}
    for source in (
        "import os", "from pathlib import Path", "open('x')", "sha256('x')",
        "client.getUpdates()", "setattr(Model, 'field', x)",
    ):
        tree = ast.parse(source)
        imports = [n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]
        calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)]
        unsafe_import = any(
            (isinstance(n, ast.Import) and n.names[0].name.split(".")[0] in {"os", "pathlib"})
            or (isinstance(n, ast.ImportFrom) and (n.module or "").split(".")[0] == "pathlib")
            for n in imports
        )
        unsafe_call = any(
            (isinstance(n.func, ast.Name) and n.func.id in forbidden)
            or (isinstance(n.func, ast.Attribute) and n.func.attr in forbidden)
            for n in calls
        )
        assert unsafe_import or unsafe_call
