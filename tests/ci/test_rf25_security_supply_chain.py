from __future__ import annotations

import httpx

from mayak.modules.max_adapter.transport import HttpxMaxTransport, MaxTransportClass
from mayak.modules.telegram_adapter.transport import (
    HttpxTelegramTransport,
    TelegramTransportClass,
)
from scripts.ci.verify_security_supply_chain import self_test, valid_self_test_evidence


def _oversized(_: httpx.Request) -> httpx.Response:
    return httpx.Response(200, content=b"x" * 33)


def test_rf25_verifier_adversarial_self_test_is_complete(tmp_path) -> None:
    self_test(tmp_path)
    assert valid_self_test_evidence(tmp_path / "self-test-evidence.json")
    assert b"not-a-placeholder-value" not in (tmp_path / "self-test-evidence.json").read_bytes()


def test_telegram_rejects_oversized_response_before_retention() -> None:
    client = httpx.Client(transport=httpx.MockTransport(_oversized))
    result = HttpxTelegramTransport(
        "synthetic-token", max_response_bytes=32, client=client
    ).get_me()
    assert result.outcome is TelegramTransportClass.AMBIGUOUS
    assert result.reason_code == "response_too_large"
    assert result.reconciliation_required is True


def test_max_rejects_oversized_response_before_retention() -> None:
    client = httpx.Client(transport=httpx.MockTransport(_oversized))
    result = HttpxMaxTransport("synthetic-token", max_response_bytes=32, client=client).get_me()
    assert result.outcome is MaxTransportClass.MALFORMED
    assert result.reason_code == "response_too_large"
