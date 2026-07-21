from mayak.modules import telegram_adapter
from mayak.modules.telegram_adapter import contracts

NAMES = (
    "TelegramPrivacyDataClass",
    "TelegramDiagnosticPurpose",
    "TelegramPrivacyProjectionState",
    "TelegramPrivacyReasonCode",
    "TelegramUntrustedPrivacyReference",
    "TelegramSafeDiagnosticFact",
    "TelegramRetentionGateReference",
    "TelegramPrivacyBoundaryRequest",
    "TelegramSafeDiagnosticProjection",
    "TelegramPrivacyBoundaryOutcome",
)


def test_all_tg14_symbols_export_from_contracts_and_package_root() -> None:
    for name in NAMES:
        assert getattr(contracts, name) is getattr(telegram_adapter, name)
        assert name in contracts.__all__
        assert telegram_adapter.__all__.count(name) == 1


def test_schema_is_reference_only_and_forbids_raw_material_fields() -> None:
    forbidden = {
        "token",
        "secret",
        "message",
        "phone",
        "payload",
        "update",
        "response",
        "body",
        "raw_text",
    }
    for name in NAMES:
        model = getattr(contracts, name)
        fields = (
            set(model.model_json_schema().get("properties", {}))
            if hasattr(model, "model_json_schema")
            else set()
        )
        assert not fields & forbidden
