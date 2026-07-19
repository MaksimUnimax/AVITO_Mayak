from __future__ import annotations

import ast

from mayak.modules import telegram_adapter
from mayak.modules.telegram_adapter import contracts

TG06 = {
    "TelegramInboundInputKind", "TelegramIntentFamily", "TelegramIntentNormalizationState",
    "TelegramIntentOwnerBoundary", "TelegramUntrustedInputReference",
    "TelegramIntentNormalizationRequest", "TelegramCommandEnvelope",
}


def test_exact_tg06_root_exports_and_identity() -> None:
    assert telegram_adapter.MODULE_ID == "09-telegram-adapter"
    assert TG06 <= set(telegram_adapter.__all__)
    assert {name for name in TG06 if getattr(telegram_adapter, name) is not getattr(contracts, name)} == set()  # noqa: E501


def test_prior_exports_are_preserved_and_no_extra_tg06_symbols_exist() -> None:
    prior = {name for name in telegram_adapter.__all__ if name not in TG06 and name != "MODULE_ID"}
    assert prior <= set(vars(telegram_adapter))
    assert set(name for name in telegram_adapter.__all__ if name.startswith("TelegramIntent")) == {
        "TelegramIntentFamily", "TelegramIntentNormalizationState", "TelegramIntentOwnerBoundary", "TelegramIntentNormalizationRequest",  # noqa: E501
    }
    tree = ast.parse(open(contracts.__file__.replace(".pyc", ".py"), encoding="utf-8").read())
    assert not [node for node in tree.body if isinstance(node, ast.Call)]
