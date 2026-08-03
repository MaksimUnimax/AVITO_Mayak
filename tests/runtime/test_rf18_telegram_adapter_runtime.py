from __future__ import annotations

# ruff: noqa: E501, I001

import httpx
import pytest

from mayak.modules.telegram_adapter.runtime import webhook_authenticity
from mayak.modules.telegram_adapter.transport import (
    FakeTelegramTransport,
    HttpxTelegramTransport,
    TelegramTransportClass,
    TelegramTransportResult,
)


def private_update(update_id: int = 1, text: str = "/help") -> dict[str, object]:
    return {"update_id": update_id, "message": {"message_id": 5, "from": {"id": 42, "username": "must-not-persist"}, "chat": {"id": 42, "type": "private"}, "text": text}}


def test_webhook_authenticity_fails_closed() -> None:
    assert webhook_authenticity("synthetic-secret", "synthetic-secret") == "VERIFIED"
    assert webhook_authenticity("wrong", "synthetic-secret") == "REJECTED_MISMATCH"
    assert webhook_authenticity(None, "synthetic-secret") == "REJECTED_MISSING_SECRET"
    assert webhook_authenticity("synthetic-secret", None) == "BLOCKED_EXPECTED_SECRET_UNAVAILABLE"


def test_fake_transport_is_scripted_and_observable() -> None:
    fake = FakeTelegramTransport([TelegramTransportResult(TelegramTransportClass.ACCEPTED, "77", "ok")])
    result = fake.send_message("42", "safe text")
    assert result.message_ref == "77"
    assert fake.calls == [("sendMessage", {"chat_id": "42", "text": "safe text"})]


@pytest.mark.parametrize("status, payload, expected", [(200, {"ok": True, "result": {"message_id": 9}}, TelegramTransportClass.ACCEPTED), (200, {"ok": False, "error_code": 400}, TelegramTransportClass.REJECTED), (429, {"ok": False}, TelegramTransportClass.RATE_LIMITED)])
def test_httpx_transport_normalizes_provider_result(status: int, payload: object, expected: TelegramTransportClass) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.host == "api.telegram.org"
        assert "/botSYNTHETIC_ONLY_TOKEN/" in str(request.url)
        return httpx.Response(status, json=payload)

    transport = HttpxTelegramTransport("SYNTHETIC_ONLY_TOKEN", client=httpx.Client(transport=httpx.MockTransport(handler)))
    result = transport.send_message("42", "safe")
    assert result.outcome is expected
    assert "SYNTHETIC_ONLY_TOKEN" not in result.reason_code


def test_unsupported_surface_does_not_normalize() -> None:
    # The durable DB test is isolated in the PostgreSQL suite; this vector
    # documents the provider boundary without requiring a local database.
    from mayak.modules.telegram_adapter.runtime import _normalized

    normalized, accepted, reason = _normalized({"update_id": 1, "channel_post": {"chat": {"id": 1, "type": "channel"}}}, "synthetic-bot", 1)
    assert not accepted and reason == "unsupported_top_level"
    assert normalized["update_class"] == "UNSUPPORTED"
