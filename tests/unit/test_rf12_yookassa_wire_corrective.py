from __future__ import annotations

import base64
import json
from pathlib import Path

import httpx

from mayak.modules.entitlements_and_billing.runtime import (
    PaymentState,
    YooKassaSandboxAdapter,
)


def _adapter(
    handler, tmp_path: Path, *, limit: int = 4096
) -> tuple[YooKassaSandboxAdapter, list[httpx.Request]]:
    secret = tmp_path / "secret"
    secret.write_text("synthetic-secret", encoding="utf-8")
    requests: list[httpx.Request] = []

    def wrapped(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return handler(request)

    client = httpx.Client(transport=httpx.MockTransport(wrapped))
    return YooKassaSandboxAdapter(
        enabled=True,
        shop_id="synthetic-shop",
        secret_file=secret,
        api_base="https://sandbox.invalid/v3",
        client=client,
        max_response_bytes=limit,
    ), requests


def test_create_wire_auth_payload_and_idempotence(tmp_path: Path) -> None:
    adapter, requests = _adapter(
        lambda request: httpx.Response(
            200,
            json={
                "id": "pay-1",
                "status": "succeeded",
                "confirmation": {"confirmation_url": "https://sandbox.invalid/c"},
            },
        ),
        tmp_path,
    )
    result = adapter.create_payment(
        idempotency_key="idem-1",
        amount_minor=99000,
        currency="RUB",
        return_url="https://mayak.invalid/return",
    )
    assert result.state is PaymentState.CONFIRMED
    request = requests[0]
    assert request.url.path == "/v3/payments"
    assert request.headers["Idempotence-Key"] == "idem-1"
    decoded = base64.b64decode(request.headers["Authorization"].split()[1]).decode()
    assert decoded == "synthetic-shop:synthetic-secret"
    body = json.loads(request.content)
    assert body["capture"] is True
    assert body["confirmation"] == {
        "type": "redirect",
        "return_url": "https://mayak.invalid/return",
    }


def test_retrieve_classifies_canceled_and_auth_not_found(tmp_path: Path) -> None:
    adapter, _ = _adapter(
        lambda request: httpx.Response(200, json={"id": "pay-1", "status": "canceled"}), tmp_path
    )
    assert adapter.retrieve_payment(external_payment_id="pay-1").state is PaymentState.REJECTED
    adapter.client.close()


def test_missing_redirect_is_rejected_before_network(tmp_path: Path) -> None:
    adapter, requests = _adapter(lambda request: httpx.Response(500), tmp_path)
    result = adapter.create_payment(idempotency_key="idem-1", amount_minor=99000, currency="RUB")
    assert result.safe_reference == "REDIRECT_RETURN_URL_REQUIRED"
    assert requests == []


def test_oversized_stream_is_fail_closed(tmp_path: Path) -> None:
    adapter, _ = _adapter(
        lambda request: httpx.Response(200, content=b"{" + b"x" * 5000 + b"}"), tmp_path, limit=32
    )
    result = adapter.retrieve_payment(external_payment_id="pay-1")
    assert result.state is PaymentState.AMBIGUOUS
    assert result.safe_reference in {"PROVIDER_RESPONSE_UNAVAILABLE", "RECONCILE_REQUIRED"}
    adapter.client.close()


def test_disabled_without_shop_id_or_secret(tmp_path: Path) -> None:
    adapter = YooKassaSandboxAdapter(enabled=True, shop_id=None, secret_file=tmp_path / "missing")
    assert (
        adapter.retrieve_payment(external_payment_id="pay-1").safe_reference
        == "PROVIDER_DISABLED_CONTINUE"
    )
