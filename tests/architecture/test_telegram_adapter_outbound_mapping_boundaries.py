from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).parents[2]
PRODUCTION = ROOT / "src" / "mayak" / "modules" / "telegram_adapter"
ALLOWED = {PRODUCTION / "contracts.py", PRODUCTION / "__init__.py"}


def _tree(path: Path) -> ast.AST:
    return ast.parse(path.read_text(encoding="utf-8"))


def test_production_entries_and_no_new_file() -> None:
    assert set(PRODUCTION.glob("*.py")) == ALLOWED


def test_forbidden_runtime_provider_and_rendering_terms_absent() -> None:
    path = PRODUCTION / "contracts.py"
    tree = _tree(path)
    tg11_names = {
        "TelegramOutboundTargetReference",
        "TelegramOutboundMappingRequest",
        "TelegramOutboundRequestIntent",
        "TelegramOutboundMappingOutcome",
    }
    source = "\n".join(
        ast.get_source_segment(path.read_text(encoding="utf-8"), node) or ""
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef) and node.name in tg11_names
    ).lower()
    forbidden = (
        "requests",
        "httpx",
        "aiohttp",
        "webhook",
        "getupdates",
        "botfather",
        "mini app",
        "template",
        "button",
        "pagination",
        "provider result",
        "subprocess",
        "filesystem",
        "message text",
        "ok=true",
    )
    assert not [term for term in forbidden if term in source]


def test_ast_has_no_execution_calls_or_dynamic_imports() -> None:
    for path in ALLOWED:
        tree = _tree(path)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in {"exec", "eval", "__import__"}
