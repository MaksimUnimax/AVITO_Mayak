from __future__ import annotations

import json

from mayak.modules import telegram_adapter
from mayak.modules.telegram_adapter import contracts

TG09_SYMBOLS = (
    "TelegramMiniAppPurpose",
    "TelegramMiniAppContextOwnerBoundary",
    "TelegramMiniAppInitDataValidationState",
    "TelegramMiniAppFreshnessState",
    "TelegramMiniAppFrontendDecisionState",
    "TelegramMiniAppValidationState",
    "TelegramUntrustedMiniAppLaunchReference",
    "TelegramMiniAppOfficialValidationEvidence",
    "TelegramMiniAppValidationRequest",
    "TelegramMiniAppValidationOutcome",
)

FORBIDDEN_SCHEMA_NAMES = {
    "init_data",
    "raw_init_data",
    "init_data_unsafe",
    "auth_date",
    "hash",
    "signature",
    "user",
    "chat",
    "account_id",
    "beacon_id",
    "listing_id",
    "result_id",
    "email",
    "phone",
    "payment_id",
    "token",
    "secret",
    "credential",
    "url",
    "algorithm",
    "key",
    "key_id",
    "ttl",
    "duration",
    "threshold",
    "freshness_threshold",
}


def test_exact_ten_tg09_exports_and_public_identity() -> None:
    assert all(name in contracts.__all__ for name in TG09_SYMBOLS)
    assert all(name in telegram_adapter.__all__ for name in TG09_SYMBOLS)
    assert all(getattr(contracts, name) is getattr(telegram_adapter, name) for name in TG09_SYMBOLS)


def test_enum_serialization_is_stable() -> None:
    for name in TG09_SYMBOLS[:6]:
        enum_type = getattr(contracts, name)
        assert all(json.loads(json.dumps(member.value)) == member.value for member in enum_type)


def test_recursive_tg09_schema_has_no_forbidden_property_or_definition_name() -> None:
    for name in TG09_SYMBOLS[6:]:
        schema = getattr(contracts, name).model_json_schema()
        seen: set[str] = set()

        def scan(node: object) -> None:
            if isinstance(node, dict):
                for key, value in node.items():
                    if key in {"properties", "$defs", "definitions"} and isinstance(value, dict):
                        seen.update(value)
                        for nested in value.values():
                            scan(nested)
                    else:
                        scan(value)
            elif isinstance(node, list):
                for value in node:
                    scan(value)

        scan(schema)
        assert not seen & FORBIDDEN_SCHEMA_NAMES, (name, seen & FORBIDDEN_SCHEMA_NAMES)
