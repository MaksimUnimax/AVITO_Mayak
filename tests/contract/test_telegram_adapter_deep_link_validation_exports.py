from __future__ import annotations

import json

import mayak.modules.telegram_adapter as package
from mayak.modules.telegram_adapter import contracts

EXPECTED = (
    "TelegramDeepLinkPurpose",
    "TelegramDeepLinkContextOwnerBoundary",
    "TelegramDeepLinkPayloadValidationMode",
    "TelegramDeepLinkReplayState",
    "TelegramDeepLinkExpiryState",
    "TelegramDeepLinkValidationState",
    "TelegramUntrustedDeepLinkReference",
    "TelegramDeepLinkContextResolutionEvidence",
    "TelegramDeepLinkValidationRequest",
    "TelegramDeepLinkValidationOutcome",
)


def test_exact_ten_exports_and_identity() -> None:
    assert tuple(name for name in package.__all__ if name in EXPECTED) == EXPECTED
    assert tuple(name for name in contracts.__all__ if name in EXPECTED) == EXPECTED
    assert all(getattr(package, name) is getattr(contracts, name) for name in EXPECTED)
    assert not any(
        name.startswith("TelegramDeepLink") and name not in EXPECTED for name in package.__all__
    )


def test_enum_serialization_and_safe_schema() -> None:
    assert package.TelegramDeepLinkPurpose.OPEN_BEACON_CONTEXT.value == "OPEN_BEACON_CONTEXT"
    forbidden = {
        "account_id",
        "beacon_id",
        "email",
        "phone",
        "payment_id",
        "token",
        "secret",
        "raw_payload",
        "url",
    }
    for name in EXPECTED[6:]:
        properties = package.__dict__[name].model_json_schema().get("properties", {})
        assert not forbidden.intersection(properties)
    assert (
        json.dumps(package.TelegramDeepLinkPurpose.OPEN_BEACON_CONTEXT) == '"OPEN_BEACON_CONTEXT"'
    )
