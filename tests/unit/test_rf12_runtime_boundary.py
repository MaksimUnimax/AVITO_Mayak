from __future__ import annotations

from pathlib import Path

import pytest

from mayak.modules.entitlements_and_billing.runtime import (
    FakeYooKassaProvider,
    PaymentState,
    ProviderResponse,
    YooKassaSandboxAdapter,
)


def test_provider_is_disabled_without_optional_secret() -> None:
    result = YooKassaSandboxAdapter(
        enabled=True, secret_file=Path("/definitely/missing")
    ).create_payment(idempotency_key="synthetic-idem", amount_minor=99_000, currency="RUB")
    assert result.state is PaymentState.REJECTED
    assert result.safe_reference == "PROVIDER_DISABLED_CONTINUE"


def test_provider_refund_api_is_not_available() -> None:
    with pytest.raises(RuntimeError, match="refund API is blocked"):
        FakeYooKassaProvider().refund_payment("payment")


def test_fake_provider_has_normalized_outcomes_only() -> None:
    fake = FakeYooKassaProvider({"idem": ProviderResponse(PaymentState.CONFIRMED, "p-1", "ref")})
    result = fake.create_payment("idem", 99_000, "RUB")
    assert result == ProviderResponse(PaymentState.CONFIRMED, "p-1", "ref")
    assert fake.calls == [("create", "idem")]
