from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).parents[2]
PRODUCTION = ROOT / "src/mayak/modules/telegram_adapter"
ALLOWED_IMPORTS = {
    "mayak.contracts",
    "mayak.modules.telegram_adapter.contracts",
    "mayak.platform.boundaries",
}
FORBIDDEN_WORDS = (
    "telegram_api",
    "httpx",
    "cryptography",
    "hashlib",
    "base64",
    "subprocess",
    "callback_parser",
    "callback_handler",
    "button_handler",
)
FORBIDDEN_CALLS = {
    "parse",
    "decode",
    "encode",
    "verify",
    "sign",
    "request",
    "get_updates",
    "send_message",
    "answer_callback_query",
}


def _terminal(node: ast.expr) -> str:
    while isinstance(node, ast.Attribute):
        node = node.value
    return node.id if isinstance(node, ast.Name) else ""


def test_all_production_telegram_files_have_safe_imports_and_no_runtime() -> None:
    for path in PRODUCTION.glob("*.py"):
        source = path.read_text()
        lower = source.lower()
        assert not any(word in lower for word in FORBIDDEN_WORDS)
        tree = ast.parse(source)
        assert not any(isinstance(node, ast.Import) for node in ast.walk(tree))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and node.module.startswith("mayak."):
                    assert node.module in ALLOWED_IMPORTS
                assert all(alias.asname is None for alias in node.names)
            if isinstance(node, ast.Call):
                assert _terminal(node.func) not in FORBIDDEN_CALLS
        assert not any(isinstance(node, (ast.Global, ast.Nonlocal)) for node in ast.walk(tree))


def test_safe_semantic_snippets_pass_independently() -> None:
    snippets = (
        "from mayak.modules.telegram_adapter.contracts import TelegramCallbackActionScope\nvalue = TelegramCallbackActionScope.OPEN_CONTEXT",  # noqa: E501
        "from mayak.contracts import ContractMetadata\nvalue = ContractMetadata",
        "from mayak.platform.boundaries import TELEGRAM_ADAPTER_MODULE_ID\nvalue = TELEGRAM_ADAPTER_MODULE_ID",  # noqa: E501
    )
    for snippet in snippets:
        tree = ast.parse(snippet)
        assert all(not isinstance(node, ast.Import) for node in ast.walk(tree))
        assert all(not isinstance(node, ast.Call) for node in ast.walk(tree))
