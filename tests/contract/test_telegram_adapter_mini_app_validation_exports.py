from __future__ import annotations

import json
from hashlib import sha1
from pathlib import Path

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
    "raw_user",
    "raw_chat",
    "raw_profile",
    "internal_account",
    "business_authorization",
    "provider_token",
    "bot_token_value",
    "webhook_secret",
}


def test_exact_ten_tg09_exports_and_public_identity() -> None:
    def filtered(exports: list[str]) -> tuple[str, ...]:
        return tuple(
            name
            for name in exports
            if name.startswith("TelegramMiniApp")
            or name == "TelegramUntrustedMiniAppLaunchReference"
        )

    assert filtered(contracts.__all__) == TG09_SYMBOLS
    assert filtered(telegram_adapter.__all__) == TG09_SYMBOLS
    assert contracts.__all__.count("TelegramUntrustedMiniAppLaunchReference") == 1
    assert telegram_adapter.__all__.count("TelegramUntrustedMiniAppLaunchReference") == 1
    assert all(getattr(contracts, name) is getattr(telegram_adapter, name) for name in TG09_SYMBOLS)
    package_bytes = Path(telegram_adapter.__file__).read_bytes()
    assert (
        sha1(b"blob " + str(len(package_bytes)).encode() + b"\0" + package_bytes).hexdigest()
        == "704e5fb27be12af3d6bf961db96b55279da7b06e"
    )


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
                    if (
                        key.lower() in {"properties", "$defs", "definitions"}
                        and isinstance(value, dict)
                    ):
                        seen.update(name.lower() for name in value)
                        for nested in value.values():
                            scan(nested)
                    else:
                        scan(value)
            elif isinstance(node, list):
                for value in node:
                    scan(value)

        scan(schema)
        assert not seen & FORBIDDEN_SCHEMA_NAMES, (name, seen & FORBIDDEN_SCHEMA_NAMES)
