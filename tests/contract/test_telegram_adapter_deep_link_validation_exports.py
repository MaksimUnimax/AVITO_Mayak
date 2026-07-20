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

FORBIDDEN_SCHEMA_NAMES = {
    "account_id",
    "beacon_id",
    "result_id",
    "listing_id",
    "email",
    "phone",
    "payment_id",
    "token",
    "secret",
    "credential",
    "raw_payload",
    "url",
    "algorithm",
    "signing_algorithm",
    "hash_algorithm",
    "key",
    "key_id",
    "key_length",
    "token_length",
    "ttl",
    "duration",
    "freshness",
    "freshness_threshold",
    "auth_date_threshold",
}


def _schema_field_names(schema: object) -> set[str]:
    names: set[str] = set()

    def walk(node: object) -> None:
        if isinstance(node, dict):
            for key in ("properties", "$defs", "definitions", "patternProperties"):
                value = node.get(key)
                if isinstance(value, dict):
                    names.update(str(name).casefold() for name in value)
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(schema)
    return names


def test_exact_ten_exports_and_identity() -> None:
    assert tuple(name for name in package.__all__ if name in EXPECTED) == EXPECTED
    assert tuple(name for name in contracts.__all__ if name in EXPECTED) == EXPECTED
    assert all(getattr(package, name) is getattr(contracts, name) for name in EXPECTED)
    assert not any(
        name.startswith("TelegramDeepLink") and name not in EXPECTED for name in package.__all__
    )


def test_enum_serialization_and_safe_schema() -> None:
    assert package.TelegramDeepLinkPurpose.OPEN_BEACON_CONTEXT.value == "OPEN_BEACON_CONTEXT"
    for name in EXPECTED[6:]:
        schema = package.__dict__[name].model_json_schema()
        assert not FORBIDDEN_SCHEMA_NAMES.intersection(_schema_field_names(schema))
    assert (
        json.dumps(package.TelegramDeepLinkPurpose.OPEN_BEACON_CONTEXT) == '"OPEN_BEACON_CONTEXT"'
    )


def test_recursive_schema_walk_covers_nested_defs_properties_arrays_and_unions() -> None:
    schema = {
        "properties": {
            "safe": {
                "items": {
                    "anyOf": [
                        {"properties": {"nested": {"type": "string"}}},
                        {"$defs": {"safe_definition": {"properties": {"deep": {}}}}},
                    ]
                }
            }
        },
        "oneOf": [{"allOf": [{"properties": {"deep_array": {"items": {}}}}]}],
    }
    assert _schema_field_names(schema) == {
        "safe",
        "nested",
        "safe_definition",
        "deep",
        "deep_array",
    }
    for forbidden in FORBIDDEN_SCHEMA_NAMES:
        forbidden_schema: dict[str, object] = {"$defs": {"Nested": {"properties": {forbidden: {}}}}}
        assert forbidden in _schema_field_names(forbidden_schema)
