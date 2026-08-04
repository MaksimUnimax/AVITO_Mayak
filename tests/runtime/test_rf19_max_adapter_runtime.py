from __future__ import annotations

# ruff: noqa: E501
import hashlib
import hmac
import json

import httpx
import respx

from mayak.modules.max_adapter.mini_app import validate_webapp_data
from mayak.modules.max_adapter.transport import (
    FakeMaxTransport,
    HttpxMaxTransport,
    MaxTransportClass,
    MaxTransportResult,
)


def test_fake_transport_is_deterministic_and_supports_safe_outcomes() -> None:
    fake = FakeMaxTransport([MaxTransportResult(MaxTransportClass.ACCEPTED, "m-1")])
    assert fake.send_message("42", "hello").provider_ref == "m-1"
    assert fake.calls == [("POST /messages", {"chat_id": "42", "text_length": 5})]


@respx.mock
def test_httpx_uses_current_base_authorization_and_json() -> None:
    route = respx.post("https://platform-api2.max.ru/messages").mock(
        return_value=httpx.Response(200, json={"message_id": 7})
    )
    result = HttpxMaxTransport("synthetic-token").send_message("42", "hello")
    assert result.outcome is MaxTransportClass.ACCEPTED
    assert route.calls[0].request.headers["Authorization"] == "synthetic-token"
    assert "token" not in str(route.calls[0].request.url)
    assert json.loads(route.calls[0].request.content)["recipient"] == {"chat_id": "42"}


def test_mini_app_signature_and_policy_boundary() -> None:
    token = "synthetic-token"
    user = json.dumps({"id": 42}, separators=(",", ":"))
    values = {"auth_date": "1000", "user": user}
    canonical = "\n".join(f"{key}={value}" for key, value in sorted(values.items()))
    secret = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
    digest = hmac.new(secret, canonical.encode(), hashlib.sha256).hexdigest()
    data = f"auth_date=1000&user={user}&hash={digest}"
    assert (
        validate_webapp_data(
            data, bot_token=token, now=1001, max_age_seconds=10, policy_reference="test-policy"
        ).state
        == "VERIFIED"
    )
    assert (
        validate_webapp_data(
            data, bot_token=token, now=2000, max_age_seconds=10, policy_reference="test-policy"
        ).state
        == "STALE"
    )
    assert (
        validate_webapp_data(
            data + "&auth_date=1000",
            bot_token=token,
            now=1001,
            max_age_seconds=10,
            policy_reference="test-policy",
        ).reason_code
        == "duplicate_parameter"
    )
