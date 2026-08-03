# ruff: noqa: E501, I001

from mayak.modules.telegram_adapter import (
    FakeTelegramTransport,
    HttpxTelegramTransport,
    TelegramAdapterRuntime,
    TelegramDeliveryMappingResult,
    TelegramIdentityMappingResult,
    TelegramIntakeResult,
    TelegramReadiness,
    TelegramTransportResult,
)


def test_rf18_runtime_exports_are_public() -> None:
    for value in (TelegramAdapterRuntime, TelegramIntakeResult, TelegramIdentityMappingResult, TelegramDeliveryMappingResult, TelegramReadiness, FakeTelegramTransport, HttpxTelegramTransport, TelegramTransportResult):
        assert value is not None
