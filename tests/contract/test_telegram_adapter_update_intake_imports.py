from __future__ import annotations

import ast
from pathlib import Path

from mayak.modules import telegram_adapter

TG02 = {
    "TelegramAccountLinkReference",
    "TelegramIdentityResolutionOutcome",
    "TelegramIdentityResolutionRequest",
    "TelegramIdentityResolutionState",
    "TelegramProviderIdentity",
    "VerifiedTelegramIdentityEvidence",
}
TG03 = {
    "TelegramProviderUpdateIdentity",
    "TelegramUpdateAdmissionState",
    "TelegramUpdateStructuralClass",
    "TelegramUpdateIntakeState",
    "TelegramUpdateDeduplicationState",
    "TelegramUpdateIntakeRecord",
    "TelegramUpdateDeduplicationRecord",
}


def test_package_root_preserves_tg02_and_exports_tg03() -> None:
    assert telegram_adapter.MODULE_ID == "09-telegram-adapter"
    assert TG02 | TG03 <= set(telegram_adapter.__all__)
    assert {name for name in TG02 | TG03 if not hasattr(telegram_adapter, name)} == set()


def test_update_contracts_reuse_shared_primitives_and_have_no_runtime_types() -> None:
    source = (
        Path(__file__).parents[2] / "src/mayak/modules/telegram_adapter/contracts.py"
    ).read_text()
    tree = ast.parse(source)
    imports = {node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
    assert "mayak.contracts" in imports
    assert not any(
        name.startswith("mayak.modules.") and name != "mayak.modules.telegram_adapter.contracts"
        for name in imports
    )
    assert not any(
        token in source.lower()
        for token in ("client", "handler", "http", "queue", "runtime", "persistence")
    )
