from __future__ import annotations

import pytest

from mayak.runtime.rf21_observers import (
    PROVIDER_GUARDED_BOUNDARIES,
    ProviderTransportGuardViolation,
    ProviderTransportObserver,
    check_notification_isolation,
    observe_support_projection,
    production_provider_transport_guard,
    provider_guard_negative_canary,
    scan_source_semantics,
)


def test_provider_observer_zero_is_measured_and_canary_increments() -> None:
    observer = ProviderTransportObserver("telegram.transport.TelegramBotApiTransport")
    assert observer.observation().measured == 0
    observer.call(lambda: "synthetic response")
    assert observer.observation().measured == 1


def test_production_guard_intercepts_exact_boundaries_and_restores_methods() -> None:
    from mayak.modules.max_adapter.transport import HttpxMaxTransport
    from mayak.modules.telegram_adapter.transport import HttpxTelegramTransport

    originals = tuple(getattr(owner, name) for owner, name in (
        (HttpxTelegramTransport, "_request"),
        (HttpxMaxTransport, "_request"),
        (HttpxMaxTransport, "get_updates"),
    ))
    with production_provider_transport_guard() as observed:
        for operation in (
            lambda: HttpxTelegramTransport("synthetic")._request("getMe", {}),
            lambda: HttpxMaxTransport("synthetic")._request("GET", "/me"),
            lambda: HttpxMaxTransport("synthetic").get_updates(marker=None, limit=1, timeout=0),
        ):
            with pytest.raises(ProviderTransportGuardViolation):
                operation()
        result = observed.observation().as_dict()
        assert result["guarded_boundaries"] == list(PROVIDER_GUARDED_BOUNDARIES)
        assert result["total_calls"] == 3
    assert tuple(getattr(owner, name) for owner, name in (
        (HttpxTelegramTransport, "_request"),
        (HttpxMaxTransport, "_request"),
        (HttpxMaxTransport, "get_updates"),
    )) == originals


def test_negative_canary_uses_same_guard_for_telegram_and_max() -> None:
    result = provider_guard_negative_canary()
    assert result == {"caught": ["telegram", "max_request", "max_get_updates"], "counts": 3}


def test_support_observer_requires_seeded_public_and_rejects_private_marker() -> None:
    projection = {"cases": ({"subject": "PUBLIC-CANARY"},)}
    result = observe_support_projection(projection, public_marker="PUBLIC-CANARY",
                                        private_marker="PRIVATE-CANARY")
    assert result == {"ready": True, "public_marker_visible": True,
                      "private_marker_visible": False}
    leaked = observe_support_projection({"subject": "PRIVATE-CANARY"},
                                        public_marker="PUBLIC-CANARY",
                                        private_marker="PRIVATE-CANARY")
    assert leaked["private_marker_visible"] is True


def test_notification_checker_detects_cross_tenant_projection() -> None:
    assert check_notification_isolation({"account_id": "A", "items": ["a"]},
                                        own_account="A", foreign_account="B").measured is True
    assert check_notification_isolation({"account_id": "A", "items": ["B"]},
                                        own_account="A", foreign_account="B").measured is False


@pytest.mark.parametrize("source, key", [
    ("import sqlalchemy\nvalue = 1", "direct_web_dml"),
    ("def f():\n return read_token()", "token_access"),
    ("def f(response):\n return response.text", "raw_provider_payload"),
])
def test_semantic_observer_negative_canaries(source: str, key: str) -> None:
    assert scan_source_semantics(source, subject="negative-canary")[key] is False
