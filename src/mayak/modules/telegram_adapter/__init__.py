"""Telegram Adapter module package."""

from mayak.modules.telegram_adapter.contracts import (
    TelegramAccountLinkReference,
    TelegramIdentityResolutionOutcome,
    TelegramIdentityResolutionRequest,
    TelegramIdentityResolutionState,
    TelegramProviderIdentity,
    TelegramProviderUpdateIdentity,
    TelegramUpdateAdmissionState,
    TelegramUpdateDeduplicationRecord,
    TelegramUpdateDeduplicationState,
    TelegramUpdateIntakeRecord,
    TelegramUpdateIntakeState,
    TelegramUpdateStructuralClass,
    VerifiedTelegramIdentityEvidence,
)
from mayak.platform.boundaries import TELEGRAM_ADAPTER_MODULE_ID

MODULE_ID = TELEGRAM_ADAPTER_MODULE_ID

__all__ = [
    "MODULE_ID",
    "TelegramAccountLinkReference",
    "TelegramIdentityResolutionOutcome",
    "TelegramIdentityResolutionRequest",
    "TelegramIdentityResolutionState",
    "TelegramProviderIdentity",
    "TelegramProviderUpdateIdentity",
    "TelegramUpdateAdmissionState",
    "TelegramUpdateStructuralClass",
    "TelegramUpdateIntakeState",
    "TelegramUpdateDeduplicationState",
    "TelegramUpdateIntakeRecord",
    "TelegramUpdateDeduplicationRecord",
    "VerifiedTelegramIdentityEvidence",
]
