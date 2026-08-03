"""Provider transports for the Telegram Adapter.

The transport is intentionally small: it returns redacted observations and
never owns Notification lifecycle or retry policy.
"""

# ruff: noqa: E501, E701, I001

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Mapping

import httpx


class TelegramTransportClass(StrEnum):
    ACCEPTED = "PROVIDER_ACCEPTED"
    REJECTED = "PROVIDER_REJECTED"
    UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    RATE_LIMITED = "RATE_LIMITED_OR_RESTRICTED"
    MALFORMED = "MALFORMED_OR_UNUSABLE_RESPONSE"
    AMBIGUOUS = "PROVIDER_EFFECT_AMBIGUOUS"


@dataclass(frozen=True, slots=True)
class TelegramTransportResult:
    outcome: TelegramTransportClass
    message_ref: str | None = None
    reason_code: str = ""
    http_status: int | None = None
    request_sent: bool = False
    reconciliation_required: bool = False


@dataclass(frozen=True, slots=True)
class TelegramUpdateBatchResult:
    outcome: TelegramTransportClass
    updates: tuple[Mapping[str, Any], ...] = ()
    next_offset_candidate: int | None = None
    reason_code: str = ""


class TelegramTransportError(RuntimeError):
    """Safe transport error; token and provider bodies are never retained."""


def _message_ref(payload: Mapping[str, Any]) -> str | None:
    result = payload.get("result")
    if not isinstance(result, Mapping):
        return None
    message_id = result.get("message_id")
    if type(message_id) is not int or message_id < 0:
        return None
    return str(message_id)


class FakeTelegramTransport:
    """Deterministic scripted provider with observable calls and no network."""

    def __init__(self, outcomes: list[TelegramTransportResult | TelegramUpdateBatchResult] | None = None) -> None:
        self._outcomes = list(outcomes or [])
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def _next(self, method: str, params: dict[str, Any]) -> Any:
        self.calls.append((method, dict(params)))
        if not self._outcomes:
            return TelegramTransportResult(TelegramTransportClass.UNAVAILABLE, reason_code="fake_script_exhausted")
        return self._outcomes.pop(0)

    def get_me(self) -> TelegramTransportResult:
        return self._next("getMe", {})

    def send_message(self, chat_id: str, text: str) -> TelegramTransportResult:
        if not chat_id or not text or len(text.encode()) > 4096:
            return TelegramTransportResult(TelegramTransportClass.REJECTED, reason_code="invalid_request")
        return self._next("sendMessage", {"chat_id": chat_id, "text": text})

    def get_updates(self, *, offset: int | None, limit: int, timeout: int) -> TelegramUpdateBatchResult:
        return self._next("getUpdates", {"offset": offset, "limit": limit, "timeout": timeout})


class HttpxTelegramTransport:
    """Production-shaped Bot API transport; callers must explicitly inject a token."""

    def __init__(self, token: str, *, max_response_bytes: int = 2_097_152,
                 connect_timeout: float = 5, read_timeout: float = 30,
                 write_timeout: float = 30, pool_timeout: float = 5,
                 client: httpx.Client | None = None) -> None:
        if not token or any(ch.isspace() for ch in token):
            raise ValueError("telegram token is invalid")
        self._token = token
        self._max_response_bytes = max_response_bytes
        self._timeout = httpx.Timeout(read_timeout, connect=connect_timeout, write=write_timeout, pool=pool_timeout)
        self._client = client
        self.calls: list[str] = []
        self._last_payload: Mapping[str, Any] = {}

    def _request(self, method: str, params: Mapping[str, Any]) -> TelegramTransportResult:
        self.calls.append(method)
        url = f"https://api.telegram.org/bot{self._token}/{method}"
        try:
            response = (self._client or httpx.Client(timeout=self._timeout)).post(url, data=dict(params))
            body = response.content
        except (httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError):
            return TelegramTransportResult(TelegramTransportClass.UNAVAILABLE, reason_code="transport_failure", request_sent=True, reconciliation_required=True)
        except httpx.HTTPError:
            return TelegramTransportResult(TelegramTransportClass.AMBIGUOUS, reason_code="protocol_failure", request_sent=True, reconciliation_required=True)
        if len(body) > self._max_response_bytes:
            return TelegramTransportResult(TelegramTransportClass.AMBIGUOUS, reason_code="response_too_large", http_status=response.status_code, request_sent=True, reconciliation_required=True)
        if response.status_code == 429:
            return TelegramTransportResult(TelegramTransportClass.RATE_LIMITED, reason_code="http_429", http_status=429, request_sent=True)
        try:
            payload = json.loads(body)
        except (UnicodeDecodeError, json.JSONDecodeError):
            return TelegramTransportResult(TelegramTransportClass.AMBIGUOUS, reason_code="malformed_json", http_status=response.status_code, request_sent=True, reconciliation_required=True)
        if not isinstance(payload, Mapping) or type(payload.get("ok")) is not bool:
            return TelegramTransportResult(TelegramTransportClass.AMBIGUOUS, reason_code="unusable_response", http_status=response.status_code, request_sent=True, reconciliation_required=True)
        self._last_payload = payload
        if payload["ok"] is True:
            ref = _message_ref(payload) if method == "sendMessage" else None
            if method == "sendMessage" and ref is None:
                return TelegramTransportResult(TelegramTransportClass.AMBIGUOUS, reason_code="message_result_invalid", http_status=response.status_code, request_sent=True, reconciliation_required=True)
            return TelegramTransportResult(TelegramTransportClass.ACCEPTED, message_ref=ref, reason_code="ok_true", http_status=response.status_code, request_sent=True)
        return TelegramTransportResult(TelegramTransportClass.REJECTED, reason_code="provider_rejected", http_status=response.status_code, request_sent=True)

    def get_me(self) -> TelegramTransportResult:
        return self._request("getMe", {})

    def send_message(self, chat_id: str, text: str) -> TelegramTransportResult:
        return self._request("sendMessage", {"chat_id": chat_id, "text": text})

    def get_updates(self, *, offset: int | None, limit: int, timeout: int) -> TelegramUpdateBatchResult:
        result = self._request("getUpdates", {"offset": offset, "limit": limit, "timeout": timeout})
        if result.outcome is not TelegramTransportClass.ACCEPTED:
            return TelegramUpdateBatchResult(result.outcome, reason_code=result.reason_code)
        raw_updates = self._last_payload.get("result")
        if not isinstance(raw_updates, list) or any(not isinstance(item, Mapping) for item in raw_updates):
            return TelegramUpdateBatchResult(TelegramTransportClass.AMBIGUOUS, reason_code="updates_result_invalid")
        updates = tuple(item for item in raw_updates if isinstance(item, Mapping))
        return TelegramUpdateBatchResult(TelegramTransportClass.ACCEPTED, updates, reason_code="ok_true")


__all__ = ["FakeTelegramTransport", "HttpxTelegramTransport", "TelegramTransportClass", "TelegramTransportResult", "TelegramUpdateBatchResult"]
