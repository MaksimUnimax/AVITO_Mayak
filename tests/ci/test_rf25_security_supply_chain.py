from __future__ import annotations

import httpx
import pytest

from mayak.modules.max_adapter.contracts import MaxRetryRecommendation
from mayak.modules.max_adapter.runtime import map_transport_result
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


def _response(status: int, content: bytes) -> httpx.MockTransport:
    return httpx.MockTransport(lambda request: httpx.Response(status, content=content))


def _raising(exception_type):
    def handler(request: httpx.Request) -> httpx.Response:
        raise exception_type("synthetic transport failure", request=request)

    return httpx.MockTransport(handler)


@pytest.mark.parametrize(
    "transport",
    [
        _response(200, b"x" * 33),
        _raising(httpx.ReadTimeout),
        _raising(httpx.NetworkError),
        _response(503, b"provider may have processed this"),
        _response(200, b"{"),
        _response(200, b"[]"),
    ],
    ids=["oversized", "timeout", "network", "http-5xx", "malformed-json", "unusable-json"],
)
def test_max_effectful_unknown_results_reconcile_first(transport: httpx.MockTransport) -> None:
    client = httpx.Client(transport=transport)
    result = HttpxMaxTransport(
        "synthetic-token", max_response_bytes=32, client=client
    ).send_message("42", "hello")
    assert result.outcome is MaxTransportClass.AMBIGUOUS
    assert result.request_sent is True
    assert result.reconciliation_required is True
    assert result.provider_ref is None
    mapped = map_transport_result(result)
    assert mapped.outcome_class == "DELIVERY_AMBIGUOUS"
    assert mapped.reconciliation_required is True
    assert mapped.retry_recommendation is MaxRetryRecommendation.RECONCILE_FIRST


def test_max_effectful_definite_rejection_is_not_ambiguity() -> None:
    client = httpx.Client(transport=_response(400, b"not-json"))
    result = HttpxMaxTransport("synthetic-token", client=client).send_message("42", "hello")
    assert result.outcome is MaxTransportClass.REJECTED
    assert result.reconciliation_required is False
    assert map_transport_result(result).outcome_class == "PROVIDER_REJECTED"


def test_max_effectful_definite_acceptance_is_accepted() -> None:
    client = httpx.Client(transport=_response(200, b'{"message_id":"m-1"}'))
    result = HttpxMaxTransport("synthetic-token", client=client).send_message("42", "hello")
    assert result.outcome is MaxTransportClass.ACCEPTED
    assert result.provider_ref == "m-1"
    assert result.reconciliation_required is False
    mapped = map_transport_result(result)
    assert mapped.outcome_class == "PROVIDER_ACCEPTED"
    assert mapped.provider_safe_delivery_reference == "m-1"
