from __future__ import annotations

# ruff: noqa: E501
from mayak.modules import telegram_adapter
from mayak.modules.telegram_adapter import contracts

TG13 = (
    "TelegramProviderOutcomeClass",
    "TelegramProviderOutcomeMappingState",
    "TelegramProviderOutcomeReasonCode",
    "TelegramTransportOutcomeObservation",
    "TelegramProviderResponseObservation",
    "TelegramProviderReconciliationObservation",
    "TelegramProviderOutcomeMappingRequest",
    "TelegramNotificationProviderOutcomeHandoff",
    "TelegramProviderOutcome",
    "TelegramProviderOutcomeMappingDecision",
)


def test_exact_tg13_export_slice_and_identity() -> None:
    assert tuple(contracts.__all__[19:29]) == TG13
    assert tuple(telegram_adapter.__all__[20:30]) == TG13
    assert telegram_adapter.__all__[0] == "MODULE_ID"
    for name in TG13:
        assert contracts.__all__.count(name) == 1
        assert telegram_adapter.__all__.count(name) == 1
        assert getattr(contracts, name) is getattr(telegram_adapter, name)


def test_enum_orders_are_exact() -> None:
    assert [x.value for x in contracts.TelegramProviderOutcomeClass] == list(TG13[:0]) + [
        "PROVIDER_REQUEST_NOT_SENT",
        "PROVIDER_ACCEPTED",
        "PROVIDER_REJECTED",
        "PROVIDER_UNAVAILABLE",
        "RATE_LIMITED_OR_RESTRICTED",
        "MALFORMED_OR_UNUSABLE_RESPONSE",
        "PROVIDER_EFFECT_AMBIGUOUS",
        "RECONCILIATION_REQUIRED",
        "RECONCILED_NO_EFFECT",
        "RECONCILED_EFFECT",
    ]
    assert [x.value for x in contracts.TelegramProviderOutcomeMappingState] == [
        "OUTCOME_MAPPED",
        "OUTCOME_BLOCKED",
        "INVALID_EVIDENCE",
        "AMBIGUOUS",
    ]
    assert [x.value for x in contracts.TelegramProviderOutcomeReasonCode] == [
        "OUTBOUND_REQUEST_NOT_PREPARED",
        "OUTCOME_SCOPE_MISMATCH",
        "TRANSPORT_OUTCOME_NOT_COMMITTED",
        "UNSAFE_PROVIDER_EVIDENCE",
        "PROVIDER_REQUEST_NOT_SENT",
        "PROVIDER_ACCEPTED",
        "PROVIDER_REJECTED",
        "PROVIDER_UNAVAILABLE",
        "RATE_LIMITED_OR_RESTRICTED",
        "MALFORMED_OR_UNUSABLE_RESPONSE",
        "PROVIDER_EFFECT_AMBIGUOUS",
        "RECONCILIATION_REQUIRED",
        "RECONCILED_NO_EFFECT",
        "RECONCILED_EFFECT",
    ]
