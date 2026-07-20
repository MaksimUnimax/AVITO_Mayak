from __future__ import annotations

import ast
from pathlib import Path

import pytest

REPO = Path(__file__).parents[2]
PRODUCTION_DIR = REPO / "src/mayak/modules/telegram_adapter"
PRODUCTION = (
    PRODUCTION_DIR / "contracts.py",
    PRODUCTION_DIR / "__init__.py",
)
EXPECTED_DIRECT_ENTRIES = {"contracts.py", "__init__.py"}
TG09_SYMBOLS = (
    "TelegramMiniAppPurpose",
    "TelegramMiniAppContextOwnerBoundary",
    "TelegramMiniAppInitDataValidationState",
    "TelegramMiniAppFreshnessState",
    "TelegramMiniAppFrontendDecisionState",
    "TelegramMiniAppValidationState",
    "TelegramUntrustedMiniAppLaunchReference",
    "TelegramMiniAppOfficialValidationEvidence",
    "TelegramMiniAppValidationRequest",
    "TelegramMiniAppValidationOutcome",
)


def _tg09_source(text: str) -> str:
    start = text.find("class TelegramMiniAppPurpose")
    return text[start:] if start >= 0 else text


def _guard(text: str) -> list[str]:
    """Cache-safe AST/text boundary guard for TG-09 production code."""
    violations: list[str] = []
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return ["invalid Python source"]
    tg09 = _tg09_source(text).lower()
    forbidden_imports = (
        "requests",
        "urllib",
        "httpx",
        "cryptography",
        "hashlib",
        "hmac",
        "ed25519",
        "sqlalchemy",
        "psycopg",
        "alembic",
        "subprocess",
        "socket",
        "importlib",
    )
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            module = (getattr(node, "module", "") or "").lower()
            imported = " ".join(alias.name.lower() for alias in node.names)
            joined = f"{module} {imported}"
            if module == "telegram" or module.startswith("telegram."):
                violations.append("forbidden Telegram SDK import")
            if any(term in joined for term in forbidden_imports):
                violations.append("forbidden import")
            if module.startswith("mayak.modules.") and not module.startswith(
                "mayak.modules.telegram_adapter"
            ):
                violations.append("foreign module import")
            if module == "importlib" or "import_module" in imported:
                violations.append("dynamic import")
        if isinstance(node, ast.Call):
            name = (
                node.func.id
                if isinstance(node.func, ast.Name)
                else getattr(node.func, "attr", "")
            )
            if name in {
                "open",
                "eval",
                "exec",
                "__import__",
                "urlopen",
                "request",
                "send",
                "post",
                "put",
                "delete",
                "mutate",
                "execute",
            }:
                violations.append(f"forbidden call {name}")
        if isinstance(node, ast.Attribute) and node.attr in {"sha256", "hmac", "import_module"}:
            violations.append(f"forbidden attribute {node.attr}")
    if any(
        fragment in tg09
        for fragment in (
            "<script",
            "javascript:",
            "webview",
            "http://",
            "https://",
            "requests.",
            "urllib.",
            "httpx",
            "hmac.",
            "ed25519",
            "sqlalchemy",
            "psycopg",
            "alembic",
            "subprocess",
            "socket.",
            "datetime.",
            "timedelta",
            "time.time",
        )
    ):
        violations.append("forbidden runtime artifact")
    names: set[str] = set()
    for node in ast.walk(ast.parse(_tg09_source(text))):
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id.lower())
    if names & {
        "init_data",
        "raw_init_data",
        "init_data_unsafe",
        "raw_user",
        "raw_chat",
        "raw_profile",
        "account_id",
        "beacon_id",
        "listing_id",
        "result_id",
        "token",
        "secret",
        "credential",
        "key",
        "key_id",
        "ttl",
        "duration",
        "threshold",
        "freshness_threshold",
    }:
        violations.append("forbidden TG-09 field")
    if "class TelegramMiniAppPurpose" in text:
        if "validated_provider_identity_reference" not in tg09:
            violations.append("missing provider identity binding")
        if "telegram_provider_identity_ref" not in tg09:
            violations.append("missing provider identity reference equality")
        if "literal[false]" not in tg09:
            violations.append("missing semantic no-authority flags")
    return violations


def test_production_direct_entries_are_exact_and_cache_safe() -> None:
    entries = {
        entry.name
        for entry in PRODUCTION_DIR.iterdir()
        if not (entry.name == "__pycache__" and entry.is_dir())
    }
    assert entries == EXPECTED_DIRECT_ENTRIES
    assert all(path.is_file() for path in PRODUCTION)


def test_reusable_tg09_architecture_guard_passes_production() -> None:
    for path in PRODUCTION:
        assert _guard(path.read_text()) == [], path


def test_exact_tg09_exports_and_no_accidental_symbols() -> None:
    from mayak.modules import telegram_adapter
    from mayak.modules.telegram_adapter import contracts

    for exports in (contracts.__all__, telegram_adapter.__all__):
        filtered = tuple(
            name
            for name in exports
            if name.startswith("TelegramMiniApp")
            or name == "TelegramUntrustedMiniAppLaunchReference"
        )
        assert filtered == TG09_SYMBOLS
        assert exports.count("TelegramUntrustedMiniAppLaunchReference") == 1


@pytest.mark.parametrize(
    "negative_control",
    (
        "import hashlib\nhashlib.sha256(b'x')\n",
        "import requests\nrequests.get('x')\n",
        "from mayak.modules.beacon_management import contracts\n",
        "open('x')\n",
        "from importlib import import_module\nimport_module('x')\n",
        "from datetime import datetime, timedelta\ndatetime.now()\n",
        "<script>window.fetch('x')</script>\n",
        "class Model:\n    raw_init_data: str\n",
        "class Model:\n    token: str\n",
        "def mutate_account():\n    execute()\n",
        "import sqlalchemy\n",
        "import socket\n",
    ),
)
def test_reusable_guard_rejects_real_negative_controls(negative_control: str) -> None:
    assert _guard(negative_control)


def test_tg09_semantic_boundary_markers_are_present() -> None:
    text = _tg09_source((PRODUCTION_DIR / "contracts.py").read_text()).lower()
    assert "unsafe_context_used_for_authentication: literal[false]" in text
    assert "unsafe_context_used_for_authorization: literal[false]" in text
    assert "provider_identity_remains_external: literal[true]" in text
    assert "business_effect_authorized: literal[false]" in text
    assert "client_ui_state_authorization: literal[false]" in text
    assert "validated_provider_identity_reference" in text
