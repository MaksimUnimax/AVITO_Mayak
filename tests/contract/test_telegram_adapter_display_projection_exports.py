from __future__ import annotations

from mayak.modules import telegram_adapter
from mayak.modules.telegram_adapter import contracts

TG11 = tuple(contracts.__all__[:9])
TG12 = (
    "TelegramDisplayClass",
    "TelegramDisplayProjectionState",
    "TelegramDisplayReasonCode",
    "TelegramSafeListingFieldFact",
    "TelegramListingCardDisplaySnapshot",
    "TelegramListingDisplayHandoff",
    "TelegramDisplayActionReference",
    "TelegramDisplayBoundaryRequest",
    "TelegramDisplayProjection",
    "TelegramDisplayBoundaryOutcome",
)


def test_exact_export_slices_and_identity() -> None:
    assert len(TG11) == 9
    assert tuple(contracts.__all__[9:19]) == TG12
    assert tuple(telegram_adapter.__all__[1:10]) == TG11
    assert tuple(telegram_adapter.__all__[10:20]) == TG12
    assert telegram_adapter.__all__[0] == "MODULE_ID"
    for name in TG12:
        assert contracts.__all__.count(name) == 1
        assert telegram_adapter.__all__.count(name) == 1
        assert getattr(contracts, name) is getattr(telegram_adapter, name)


def test_no_tg12_helper_exports() -> None:
    assert not any(
        name.startswith("_") is False and name.startswith("_display") for name in contracts.__dict__
    )
