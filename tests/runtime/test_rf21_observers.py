from __future__ import annotations

import pytest

from mayak.runtime.rf21_observers import (
    ProviderTransportObserver,
    check_notification_isolation,
    observe_support_projection,
    scan_source_semantics,
)


def test_provider_observer_zero_is_measured_and_canary_increments() -> None:
    observer = ProviderTransportObserver("telegram.transport.TelegramBotApiTransport")
    assert observer.observation().measured == 0
    observer.call(lambda: "synthetic response")
    assert observer.observation().measured == 1


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
