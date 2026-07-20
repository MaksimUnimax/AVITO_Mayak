from __future__ import annotations

import ast
from pathlib import Path

import pytest

REPO = Path(__file__).parents[2]
PRODUCTION = (
    REPO / "src/mayak/modules/telegram_adapter/contracts.py",
    REPO / "src/mayak/modules/telegram_adapter/__init__.py",
)
ALLOWED = {path.name for path in PRODUCTION}


def _guard(text: str) -> list[str]:
    violations: list[str] = []
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [alias.name for alias in node.names]
            module = getattr(node, "module", "") or ""
            joined = " ".join(names + [module])
            if any(
                term in joined for term in ("http", "requests", "urllib", "cryptography", "hashlib")
            ):
                violations.append("provider/network/crypto import")
            if module.startswith("mayak.modules.") and not module.startswith(
                "mayak.modules.telegram_adapter"
            ):
                violations.append("foreign module import")
            if "import_module" in names:
                violations.append("forbidden dynamic import")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in {"open", "eval", "exec", "__import__"}:
                violations.append(f"forbidden call {node.func.id}")
        if isinstance(node, ast.Attribute) and node.attr in {"import_module", "sha256", "new"}:
            violations.append(f"forbidden dynamic/crypto attribute {node.attr}")
    forbidden_fragments = (
        "requests.",
        "urllib.",
        "httpx",
        "webview",
        "javascript",
        "hmac.",
        "ed25519",
        "sqlalchemy",
        "psycopg",
        "alembic",
        "subprocess",
        "socket",
        "datetime.now",
        "timedelta",
        "time.time",
        ".get(",
    )
    violations.extend(fragment for fragment in forbidden_fragments if fragment in text.lower())
    return violations


def test_production_files_are_only_contracts_and_package_exports() -> None:
    module = REPO / "src/mayak/modules/telegram_adapter"
    direct = {path.name for path in module.iterdir() if path.name != "__pycache__"}
    assert direct == ALLOWED
    assert all(path in PRODUCTION for path in PRODUCTION)


def test_reusable_tg09_architecture_guard_passes_production() -> None:
    for path in PRODUCTION:
        assert _guard(path.read_text()) == [], path


@pytest.mark.parametrize(
    "negative_control",
    (
        "import hashlib\nhashlib.sha256(b'x')\n",
        "import requests\nrequests.get('x')\n",
        "from mayak.modules.beacon_management import contracts\n",
        "open('x')\n",
        "from importlib import import_module\nimport_module('x')\n",
        "from datetime import datetime, timedelta\ndatetime.now()\n",
    ),
)
def test_reusable_guard_rejects_real_negative_controls(negative_control: str) -> None:
    assert _guard(negative_control)


def test_tg09_has_no_forbidden_runtime_or_ownership_artifacts() -> None:
    text = "\n".join(path.read_text().lower() for path in PRODUCTION)
    assert "__import__" not in text
    assert "business_effect_authorized: literal[false]" in text
    assert "internal_account_authority" not in text
