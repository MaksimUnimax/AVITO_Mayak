from __future__ import annotations

import json

import mayak.modules.telegram_adapter as package
from mayak.modules.telegram_adapter import contracts

TG10_SYMBOLS = (
    "TelegramChatSurfaceClass",
    "TelegramChatSurfaceAdmissionState",
    "TelegramChatSurfaceReasonCode",
    "TelegramUntrustedChatSurfaceReference",
    "TelegramChatSurfaceAdmissionRequest",
    "TelegramChatSurfaceAdmissionOutcome",
)
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
TG02_SYMBOLS = {
    "TelegramAccountLinkReference",
    "TelegramIdentityResolutionOutcome",
    "TelegramIdentityResolutionRequest",
    "TelegramIdentityResolutionState",
    "TelegramProviderIdentity",
    "VerifiedTelegramIdentityEvidence",
}
TG03_SYMBOLS = {
    "TelegramProviderUpdateIdentity",
    "TelegramUpdateAdmissionState",
    "TelegramUpdateStructuralClass",
    "TelegramUpdateIntakeState",
    "TelegramUpdateDeduplicationState",
    "TelegramUpdateIntakeRecord",
    "TelegramUpdateDeduplicationRecord",
}
FORBIDDEN_SCHEMA_NAMES = {
    "account_id",
    "beacon_id",
    "listing_id",
    "notification_attempt_id",
    "email",
    "phone",
    "payment_id",
    "token",
    "secret",
    "credential",
    "raw_payload",
    "raw_update",
    "message",
    "profile",
    "contact",
    "ownership",
    "business_action",
    "provider_runtime",
    "outbound",
}


def _schema_names(schema: object) -> set[str]:
    found: set[str] = set()

    def walk(node: object) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if key.lower() in {"properties", "$defs", "definitions", "patternProperties"}:
                    if isinstance(value, dict):
                        found.update(str(name).casefold() for name in value)
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(schema)
    return found


def _filtered(exports: list[str], symbols: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(name for name in exports if name in symbols)


def test_exact_six_tg10_exports_order_uniqueness_identity_and_no_accidental_exports() -> None:
    for exports in (contracts.__all__, package.__all__):
        assert _filtered(exports, TG10_SYMBOLS) == TG10_SYMBOLS
        assert len(exports) == len(set(exports))
        assert not {
            name
            for name in exports
            if name.startswith("TelegramChatSurface")
            or name == "TelegramUntrustedChatSurfaceReference"
        } - set(TG10_SYMBOLS)
    assert all(getattr(contracts, name) is getattr(package, name) for name in TG10_SYMBOLS)


def test_tg09_tg02_tg03_exports_remain_intact() -> None:
    for exports in (contracts.__all__, package.__all__):
        assert _filtered(exports, TG09_SYMBOLS) == TG09_SYMBOLS
        assert TG02_SYMBOLS | TG03_SYMBOLS <= set(exports)


def test_enum_json_serialization_and_recursive_forbidden_schema_scan() -> None:
    for name in TG10_SYMBOLS[:3]:
        enum_type = getattr(contracts, name)
        assert [json.loads(json.dumps(member.value)) for member in enum_type] == [
            member.value for member in enum_type
        ]
    for name in TG10_SYMBOLS[3:]:
        assert not FORBIDDEN_SCHEMA_NAMES.intersection(
            _schema_names(getattr(contracts, name).model_json_schema())
        )


def test_schema_guard_has_real_negative_controls() -> None:
    safe = {"properties": {"diagnostic_reference": {"type": "string"}}}
    assert not FORBIDDEN_SCHEMA_NAMES.intersection(_schema_names(safe))
    for forbidden in ("account_id", "raw_payload", "provider_runtime", "business_action"):
        unsafe: dict[str, object] = {"$defs": {"nested": {"properties": {forbidden: {}}}}}
        assert forbidden in _schema_names(unsafe)
