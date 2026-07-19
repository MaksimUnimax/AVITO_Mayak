from __future__ import annotations

import importlib

import mayak.modules.telegram_adapter as package
from mayak.modules.telegram_adapter import contracts

NEW = (
    "TelegramExistingBotEvidenceState",
    "TelegramExistingBotMetadata",
    "TelegramProtectedSecretPresenceEvidence",
    "TelegramPublicBotMetadataPresenceEvidence",
    "TelegramExistingBotOperationalGate",
)


def test_new_symbols_are_root_exports_and_identity_preserves_prior_exports() -> None:
    for name in NEW:
        assert name in package.__all__
        assert getattr(package, name) is getattr(contracts, name)
    assert package.MODULE_ID == "09-telegram-adapter"
    for name in (
        "TelegramIdentityResolutionState", "VerifiedTelegramIdentityEvidence",
        "TelegramProviderMode", "TelegramProviderModeBoundary", "TelegramUpdateIntakeRecord",
        "TelegramUpdateDeduplicationRecord", "TelegramWebhookModeRequirements",
        "TelegramGetUpdatesModeRequirements",
    ):
        assert name in package.__all__ and hasattr(package, name)


def test_import_has_no_runtime_side_effect() -> None:
    assert importlib.import_module("mayak.modules.telegram_adapter") is package
