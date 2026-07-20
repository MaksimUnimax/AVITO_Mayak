from __future__ import annotations

import ast
from pathlib import Path

import pytest

import mayak.modules.telegram_adapter as package

ROOT = Path(__file__).parents[2]
PRODUCTION = ROOT / "src/mayak/modules/telegram_adapter"
ALLOWED = {"__init__.py", "contracts.py"}
FORBIDDEN = (
    "telegram_api",
    "httpx",
    "cryptography",
    "hashlib",
    "sqlalchemy",
    "psycopg",
    "alembic",
    "getupdates",
    "webhook",
    "hmac",
    "ttl",
    "duration",
    "raw_payload:", "account_id:", "beacon_id:", "token:", "secret:",
)


def tg08_architecture_guard(source_override: str | None = None) -> None:
    assert {path.name for path in PRODUCTION.glob("*.py")} == ALLOWED
    source = source_override or (PRODUCTION / "contracts.py").read_text()
    tg08_source = source[
        source.index("class TelegramDeepLinkPurpose") : source.index("__all__ = [")
    ].lower()
    assert not any(word in tg08_source for word in FORBIDDEN)
    for path in PRODUCTION.glob("*.py"):
        tree = ast.parse(path.read_text())
        assert not any(
            isinstance(node, (ast.Import, ast.Call))
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
        )
        assert not any(isinstance(node, (ast.Global, ast.Nonlocal)) for node in ast.walk(tree))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.ImportFrom)
                and node.module
                and node.module.startswith("mayak.")
            ):
                assert node.module in {
                    "mayak.contracts",
                    "mayak.modules.telegram_adapter.contracts",
                    "mayak.platform.boundaries",
                }
    assert tuple(
        name
        for name in package.__all__
        if name.startswith("TelegramDeepLink") or name == "TelegramUntrustedDeepLinkReference"
    ) == (
        "TelegramDeepLinkPurpose",
        "TelegramDeepLinkContextOwnerBoundary",
        "TelegramDeepLinkPayloadValidationMode",
        "TelegramDeepLinkReplayState",
        "TelegramDeepLinkExpiryState",
        "TelegramDeepLinkValidationState",
        "TelegramUntrustedDeepLinkReference",
        "TelegramDeepLinkContextResolutionEvidence",
        "TelegramDeepLinkValidationRequest",
        "TelegramDeepLinkValidationOutcome",
    )


def test_tg08_architecture_guard() -> None:
    tg08_architecture_guard()

@pytest.mark.parametrize("negative", ("telegram_api", "account_id:", "raw_payload:", "ttl"))
def test_real_negative_controls_use_same_guard(negative: str) -> None:
    with pytest.raises(AssertionError):
        source = (PRODUCTION / "contracts.py").read_text()
        end = source.index("__all__ = [")
        tg08_architecture_guard(source[:end] + negative + source[end:])
