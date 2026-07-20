from __future__ import annotations

import inspect

from mayak.modules import telegram_adapter
from mayak.modules.telegram_adapter import contracts

TG11 = (
    "TelegramOutboundRequestClass",
    "TelegramOutboundMappingState",
    "TelegramOutboundMappingReasonCode",
    "TelegramNotificationAttemptHandoff",
    "TelegramListingCardProjectionHandoff",
    "TelegramOutboundTargetReference",
    "TelegramOutboundMappingRequest",
    "TelegramOutboundRequestIntent",
    "TelegramOutboundMappingOutcome",
)


def test_exact_nine_surface_and_identity() -> None:
    assert tuple(contracts.__all__[:9]) == TG11
    assert sum(name in contracts.__all__ for name in TG11) == 9
    assert tuple(telegram_adapter.__all__[1:10]) == TG11
    for name in TG11:
        assert getattr(contracts, name) is getattr(telegram_adapter, name)


def test_no_accidental_public_tg11_helpers() -> None:
    assert not any(
        name.startswith("_") is False and name.startswith("_outbound")
        for name in contracts.__dict__
    )
    assert inspect.isclass(telegram_adapter.TelegramOutboundMappingOutcome)
