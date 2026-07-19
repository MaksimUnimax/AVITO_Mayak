from __future__ import annotations

import ast
from pathlib import Path

from mayak.contracts import (
    ContractMetadata,
    IdempotencyFingerprint,
    IdempotencyKey,
    IdempotencyScope,
)
from mayak.modules import telegram_adapter
from mayak.modules.telegram_adapter import (
    TelegramAccountLinkReference,
    TelegramIdentityResolutionOutcome,
    TelegramIdentityResolutionRequest,
    TelegramIdentityResolutionState,
    TelegramProviderIdentity,
    VerifiedTelegramIdentityEvidence,
)
from mayak.platform.boundaries import TELEGRAM_ADAPTER_MODULE_ID


def test_public_telegram_identity_contract_exports_are_stable() -> None:
    assert telegram_adapter.MODULE_ID == TELEGRAM_ADAPTER_MODULE_ID == "09-telegram-adapter"
    assert all(
        symbol is not None
        for symbol in (
            TelegramAccountLinkReference,
            TelegramIdentityResolutionOutcome,
            TelegramIdentityResolutionRequest,
            TelegramIdentityResolutionState,
            TelegramProviderIdentity,
            VerifiedTelegramIdentityEvidence,
            ContractMetadata,
            IdempotencyKey,
            IdempotencyScope,
            IdempotencyFingerprint,
        )
    )


def test_production_telegram_files_do_not_import_identity_or_other_modules() -> None:
    root = Path(__file__).resolve().parents[2] / "src/mayak/modules/telegram_adapter"
    for path in root.glob("*.py"):
        tree = ast.parse(path.read_text())
        imports = [node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
        imports += [
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        ]
        assert not any(
            name.startswith("mayak.modules.")
            and name != "mayak.modules.telegram_adapter.contracts"
            for name in imports
        )
        assert "mayak.modules.identity_and_access" not in imports


def test_shared_and_identity_files_are_unchanged_and_public_api_has_no_runtime_types() -> None:
    assert not any("identity_and_access" in name for name in telegram_adapter.__all__)
    assert not {
        name
        for name in telegram_adapter.__all__
        if any(
            token in name.lower()
            for token in ("client", "handler", "orm", "http", "queue", "persistence")
        )
    }
