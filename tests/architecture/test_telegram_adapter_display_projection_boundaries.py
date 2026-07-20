from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).parents[2]
PRODUCTION = ROOT / "src" / "mayak" / "modules" / "telegram_adapter"


def test_only_expected_production_entries_exist() -> None:
    assert {path.name for path in PRODUCTION.glob("*.py")} == {"contracts.py", "__init__.py"}


def test_production_has_no_foreign_module_imports() -> None:
    for path in PRODUCTION.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                assert (node.module or "") == "mayak.modules.telegram_adapter.contracts" or not (
                    node.module or ""
                ).startswith("mayak.modules.")
            if isinstance(node, ast.Import):
                assert all(not alias.name.startswith("mayak.modules.") for alias in node.names)


def test_display_boundary_has_no_runtime_or_final_rendering_surface() -> None:
    path = PRODUCTION / "contracts.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    source = "\n".join(
        ast.get_source_segment(path.read_text(encoding="utf-8"), node) or ""
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef) and node.name.startswith("TelegramDisplay")
    ).lower()
    for forbidden in (
        "httpx",
        "aiohttp",
        "webhook",
        "getupdates",
        "mini app",
        "callback payload",
        "button label",
        "pagination size",
        "provider call",
    ):
        assert forbidden not in source
