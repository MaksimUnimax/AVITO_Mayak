from __future__ import annotations

import ast
from pathlib import Path

import mayak.modules.telegram_adapter as package
from mayak.modules.telegram_adapter import contracts

EXPECTED_NEW = (
    "TelegramCallbackActionScope",
    "TelegramCallbackRiskClass",
    "TelegramCallbackPayloadValidationMode",
    "TelegramCallbackReplayState",
    "TelegramCallbackExpiryState",
    "TelegramCallbackConfirmationState",
    "TelegramCallbackValidationState",
    "TelegramUntrustedCallbackReference",
    "TelegramCallbackAuthorizationEvidence",
    "TelegramCallbackValidationRequest",
    "TelegramCallbackValidationOutcome",
)
EXPECTED_PRIOR = (
    "MODULE_ID",
    "TelegramInboundInputKind",
    "TelegramIntentFamily",
    "TelegramIntentNormalizationState",
    "TelegramIntentOwnerBoundary",
    "TelegramUntrustedInputReference",
    "TelegramIntentNormalizationRequest",
    "TelegramCommandEnvelope",
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
    "TelegramProviderMode",
    "TelegramProviderModeBoundaryState",
    "TelegramWebhookModeRequirements",
    "TelegramGetUpdatesModeRequirements",
    "TelegramProviderModeBoundary",
    "TelegramExistingBotEvidenceState",
    "TelegramExistingBotMetadata",
    "TelegramProtectedSecretPresenceEvidence",
    "TelegramPublicBotMetadataPresenceEvidence",
    "TelegramExistingBotOperationalGate",
)


def test_exact_new_root_exports_and_identity() -> None:
    assert tuple(name for name in package.__all__ if name in EXPECTED_NEW) == EXPECTED_NEW
    assert all(getattr(package, name) is getattr(contracts, name) for name in EXPECTED_NEW)
    assert all(name in package.__all__ for name in EXPECTED_PRIOR)
    assert not any(
        name.startswith("TelegramCallback") and name not in EXPECTED_NEW for name in package.__all__
    )


def test_production_has_no_runtime_instance_and_legacy_guard_survives() -> None:
    source = Path(contracts.__file__).read_text()
    tree = ast.parse(source)
    assert not any(
        isinstance(node, ast.Assign) and isinstance(node.value, ast.Call) for node in tree.body
    )
    assert "TelegramCallbackValidationOutcome" in source
