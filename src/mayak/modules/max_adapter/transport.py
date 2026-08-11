"""Small, redacting MAX provider transports."""

# ruff: noqa: E501

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Mapping

import httpx


class MaxTransportClass(StrEnum):
    ACCEPTED = "PROVIDER_ACCEPTED"
    REJECTED = "PROVIDER_REJECTED"
    AUTH_FAILED = "AUTH_FAILED"
    RATE_LIMITED = "RATE_LIMITED"
    UNAVAILABLE = "UNAVAILABLE"
    MALFORMED = "MALFORMED"
    AMBIGUOUS = "AMBIGUOUS"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True, slots=True)
class MaxTransportResult:
    outcome: MaxTransportClass
    provider_ref: str | None = None
    reason_code: str = ""
    http_status: int | None = None
    request_sent: bool = False
    reconciliation_required: bool = False
    bot_ref: str | None = None


@dataclass(frozen=True, slots=True)
class MaxUpdateBatch:
    outcome: MaxTransportClass
    updates: tuple[Mapping[str, Any], ...] = ()
    next_marker: int | None = None
    reason_code: str = ""


def _safe_ref(value: object) -> str | None:
    if isinstance(value, (str, int)) and str(value).strip():
        return str(value)[:255]
    return None


class FakeMaxTransport:
    """Scripted, deterministic transport; it never performs network I/O."""

    def __init__(self, outcomes: list[MaxTransportResult | MaxUpdateBatch] | None = None) -> None:
        self._outcomes = list(outcomes or [])
        self.calls: list[tuple[str, Mapping[str, Any]]] = []

    def _next(self, method: str, params: Mapping[str, Any]) -> Any:
        self.calls.append((method, dict(params)))
        return (
            self._outcomes.pop(0)
            if self._outcomes
            else MaxTransportResult(
                MaxTransportClass.UNAVAILABLE, reason_code="fake_script_exhausted"
            )
        )

    def get_me(self) -> MaxTransportResult:
        return self._next("GET /me", {})

    def send_message(self, chat_id: str, text: str) -> MaxTransportResult:
        if not chat_id or not text or len(text.encode()) > 4096:
            return MaxTransportResult(MaxTransportClass.REJECTED, reason_code="invalid_request")
        return self._next("POST /messages", {"chat_id": chat_id, "text_length": len(text)})

    def get_updates(self, *, marker: int | None, limit: int, timeout: int) -> MaxUpdateBatch:
        return self._next("GET /updates", {"marker": marker, "limit": limit, "timeout": timeout})


class HttpxMaxTransport:
    """Verified HTTPS MAX transport with bounded, redacted observations."""

    def __init__(
        self,
        token: str,
        *,
        base_url: str = "https://platform-api2.max.ru",
        max_response_bytes: int = 2_097_152,
        connect_timeout: float = 5,
        read_timeout: float = 30,
        write_timeout: float = 30,
        pool_timeout: float = 5,
        client: httpx.Client | None = None,
    ) -> None:
        if not token or any(ch.isspace() for ch in token):
            raise ValueError("MAX credential is invalid")
        if not base_url.startswith("https://") or "?" in base_url:
            raise ValueError("MAX API base must be verified HTTPS")
        self._token, self._base_url, self._limit = token, base_url.rstrip("/"), max_response_bytes
        self._timeout = httpx.Timeout(
            read_timeout, connect=connect_timeout, write=write_timeout, pool=pool_timeout
        )
        self._client = client

    def _request(
        self,
        method: str,
        path: str,
        *,
        effectful: bool = False,
        json_body: Mapping[str, Any] | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> MaxTransportResult:
        owned = self._client is None
        client = self._client or httpx.Client(timeout=self._timeout)
        try:
            with client.stream(method, f"{self._base_url}{path}", headers={"Authorization": self._token}, json=json_body, params=params) as response:
                body = bytearray()
                for chunk in response.iter_bytes():
                    remaining = self._limit - len(body)
                    body.extend(chunk[: remaining + 1])
                    if len(body) > self._limit:
                        return self._unknown_or_read_failure(
                            effectful,
                            reason_code="response_too_large",
                            http_status=response.status_code,
                        )
                status = response.status_code
        except (httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError):
            return self._unknown_or_read_failure(effectful, reason_code="transport_failure")
        except httpx.HTTPError:
            return self._unknown_or_read_failure(effectful, reason_code="protocol_failure")
        finally:
            if owned:
                client.close()
        if status == 401:
            return MaxTransportResult(
                MaxTransportClass.AUTH_FAILED,
                reason_code="http_401",
                http_status=status,
                request_sent=True,
            )
        if status == 429:
            return MaxTransportResult(
                MaxTransportClass.RATE_LIMITED,
                reason_code="http_429",
                http_status=status,
                request_sent=True,
            )
        if 400 <= status < 500:
            return MaxTransportResult(
                MaxTransportClass.REJECTED,
                reason_code=f"http_{status}",
                http_status=status,
                request_sent=True,
            )
        if status >= 500:
            if effectful:
                return MaxTransportResult(
                    MaxTransportClass.AMBIGUOUS,
                    reason_code=f"http_{status}_effect_unknown",
                    http_status=status,
                    request_sent=True,
                    reconciliation_required=True,
                )
            return MaxTransportResult(
                MaxTransportClass.UNAVAILABLE,
                reason_code=f"http_{status}",
                http_status=status,
                request_sent=True,
            )
        try:
            payload = json.loads(bytes(body))
        except (UnicodeDecodeError, json.JSONDecodeError):
            if effectful:
                return MaxTransportResult(
                    MaxTransportClass.AMBIGUOUS,
                    reason_code="malformed_json_effect_unknown",
                    http_status=status,
                    request_sent=True,
                    reconciliation_required=True,
                )
            return MaxTransportResult(
                MaxTransportClass.MALFORMED,
                reason_code="malformed_json",
                http_status=status,
                request_sent=True,
            )
        if not isinstance(payload, Mapping):
            if effectful:
                return MaxTransportResult(
                    MaxTransportClass.AMBIGUOUS,
                    reason_code="unusable_response_effect_unknown",
                    http_status=status,
                    request_sent=True,
                    reconciliation_required=True,
                )
            return MaxTransportResult(
                MaxTransportClass.MALFORMED,
                reason_code="unusable_response",
                http_status=status,
                request_sent=True,
            )
        ref = _safe_ref(payload.get("message_id") or payload.get("user_id") or payload.get("id"))
        if effectful and not _safe_ref(payload.get("message_id")):
            return MaxTransportResult(
                MaxTransportClass.AMBIGUOUS,
                reason_code="missing_message_reference_effect_unknown",
                http_status=status,
                request_sent=True,
                reconciliation_required=True,
            )
        return MaxTransportResult(
            MaxTransportClass.ACCEPTED,
            ref,
            "ok",
            status,
            True,
            False,
            _safe_ref(payload.get("user_id")),
        )

    def get_me(self) -> MaxTransportResult:
        return self._request("GET", "/me")

    def send_message(self, chat_id: str, text: str) -> MaxTransportResult:
        if not chat_id or not text or len(text.encode()) > 4096:
            return MaxTransportResult(MaxTransportClass.REJECTED, reason_code="invalid_request")
        return self._request(
            "POST",
            "/messages",
            effectful=True,
            json_body={"text": text, "recipient": {"chat_id": chat_id}},
        )

    @staticmethod
    def _unknown_or_read_failure(
        effectful: bool, *, reason_code: str, http_status: int | None = None
    ) -> MaxTransportResult:
        if effectful:
            return MaxTransportResult(
                MaxTransportClass.AMBIGUOUS,
                reason_code=f"{reason_code}_effect_unknown",
                http_status=http_status,
                request_sent=True,
                reconciliation_required=True,
            )
        return MaxTransportResult(
            MaxTransportClass.MALFORMED,
            reason_code=reason_code,
            http_status=http_status,
            request_sent=True,
        )

    def get_updates(self, *, marker: int | None, limit: int, timeout: int) -> MaxUpdateBatch:
        owned = self._client is None
        client = self._client or httpx.Client(timeout=self._timeout)
        try:
            with client.stream("GET", f"{self._base_url}/updates", headers={"Authorization": self._token}, params={"marker": marker, "limit": limit, "timeout": timeout}) as response:
                body = bytearray()
                for chunk in response.iter_bytes():
                    remaining = self._limit - len(body)
                    body.extend(chunk[: remaining + 1])
                    if len(body) > self._limit:
                        return MaxUpdateBatch(MaxTransportClass.MALFORMED, reason_code="response_too_large")
                status = response.status_code
        except (httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError, httpx.HTTPError):
            return MaxUpdateBatch(MaxTransportClass.AMBIGUOUS, reason_code="transport_failure")
        finally:
            if owned:
                client.close()
        if status == 401:
            return MaxUpdateBatch(MaxTransportClass.AUTH_FAILED, reason_code="http_401")
        if status == 429:
            return MaxUpdateBatch(MaxTransportClass.RATE_LIMITED, reason_code="http_429")
        if status >= 500:
            return MaxUpdateBatch(
                MaxTransportClass.UNAVAILABLE, reason_code=f"http_{status}"
            )
        try:
            payload = json.loads(bytes(body))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return MaxUpdateBatch(MaxTransportClass.MALFORMED, reason_code="malformed_json")
        updates = payload.get("updates") if isinstance(payload, Mapping) else None
        if not isinstance(updates, list) or any(not isinstance(item, Mapping) for item in updates):
            return MaxUpdateBatch(MaxTransportClass.MALFORMED, reason_code="updates_result_invalid")
        next_marker = payload.get("marker")
        if next_marker is not None and type(next_marker) is not int:
            return MaxUpdateBatch(MaxTransportClass.MALFORMED, reason_code="marker_invalid")
        return MaxUpdateBatch(MaxTransportClass.ACCEPTED, tuple(updates), next_marker, "ok")


__all__ = [
    "FakeMaxTransport",
    "HttpxMaxTransport",
    "MaxTransportClass",
    "MaxTransportResult",
    "MaxUpdateBatch",
]
