from __future__ import annotations

import mayak.modules.telegram_adapter as package
from mayak.contracts import ContractMetadata
from mayak.modules.telegram_adapter import contracts

TG04 = (
    "TelegramProviderMode",
    "TelegramProviderModeBoundaryState",
    "TelegramWebhookModeRequirements",
    "TelegramGetUpdatesModeRequirements",
    "TelegramProviderModeBoundary",
)
TG02_TG03 = (
    "TelegramAccountLinkReference",
    "TelegramIdentityResolutionOutcome",
    "TelegramIdentityResolutionRequest",
    "TelegramIdentityResolutionState",
    "TelegramProviderIdentity",
    "TelegramProviderUpdateIdentity",
    "TelegramUpdateAdmissionState",
    "TelegramUpdateStructuralClass",
    "TelegramUpdateIntakeState",
    "TelegramUpdateDeduplicationState",
    "TelegramUpdateIntakeRecord",
    "TelegramUpdateDeduplicationRecord",
    "VerifiedTelegramIdentityEvidence",
)


def test_package_and_contract_exports_are_exactly_preserved_and_extended() -> None:
    assert package.MODULE_ID == "09-telegram-adapter"
    assert tuple(name for name in TG04 if name in package.__all__) == TG04
    assert tuple(name for name in TG04 if name in contracts.__all__) == TG04
    assert all(hasattr(package, name) and hasattr(contracts, name) for name in TG04)
    assert all(name in package.__all__ and name in contracts.__all__ for name in TG02_TG03)
    assert type(package.__all__) is list
    assert type(contracts.__all__) is list


def test_shared_metadata_is_reused_and_public_schemas_are_safe() -> None:
    assert (
        package.TelegramProviderModeBoundary.model_fields["metadata"].annotation is ContractMetadata
    )
    forbidden_fragments = (
        "token_value",
        "secret_value",
        "raw_payload",
        "endpoint_url",
        "cursor_value",
        "provider_client",
    )
    for model in (
        package.TelegramWebhookModeRequirements,
        package.TelegramGetUpdatesModeRequirements,
        package.TelegramProviderModeBoundary,
    ):
        names = set(model.model_fields)
        assert not any(any(fragment in name for fragment in forbidden_fragments) for name in names)
