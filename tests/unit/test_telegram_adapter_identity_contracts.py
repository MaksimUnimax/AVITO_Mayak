from __future__ import annotations

from uuid import uuid4

import pytest
from pydantic import ValidationError

from mayak.contracts import (
    ContractMetadata,
    IdempotencyFingerprint,
    IdempotencyKey,
    IdempotencyScope,
)
from mayak.modules.telegram_adapter import (
    TelegramAccountLinkReference,
    TelegramIdentityResolutionOutcome,
    TelegramIdentityResolutionRequest,
    TelegramIdentityResolutionState,
    TelegramProviderIdentity,
    VerifiedTelegramIdentityEvidence,
)

MODELS = (
    TelegramProviderIdentity,
    VerifiedTelegramIdentityEvidence,
    TelegramAccountLinkReference,
    TelegramIdentityResolutionRequest,
    TelegramIdentityResolutionOutcome,
)


def provider() -> TelegramProviderIdentity:
    return TelegramProviderIdentity(
        telegram_provider_identity_ref="tg-identity-ref",
        telegram_bot_ref="tg-bot-ref",
        telegram_user_id="tg-user-42",
        telegram_chat_id="tg-chat-42",
    )


def evidence() -> VerifiedTelegramIdentityEvidence:
    return VerifiedTelegramIdentityEvidence(
        verified_identity_evidence_ref="evidence-ref",
        provider_identity=provider(),
        verification_method_ref="method-ref",
        verification_result_ref="result-ref",
    )


def metadata() -> ContractMetadata:
    return ContractMetadata(
        contract_name="telegram.identity-resolution",
        contract_version="1",
        message_id=uuid4(),
        correlation_id=uuid4(),
        producer="telegram-adapter",
    )


def request() -> TelegramIdentityResolutionRequest:
    return TelegramIdentityResolutionRequest(
        telegram_identity_resolution_request_id="request-ref",
        metadata=metadata(),
        idempotency_key=IdempotencyKey(value="key-ref"),
        idempotency_scope=IdempotencyScope(value="telegram-identity"),
        fingerprint=IdempotencyFingerprint(value="fingerprint-ref"),
        verified_identity_evidence=evidence(),
        identity_resolution_contract_ref="identity-resolution-boundary",
    )


def account_link(p: TelegramProviderIdentity | None = None) -> TelegramAccountLinkReference:
    p = p or provider()
    return TelegramAccountLinkReference(
        telegram_account_link_reference_id="link-ref",
        provider_identity=p,
        account_id="account-42",
        identity_account_reference_id="identity-account-ref",
        identity_provider_identity_id=p.telegram_user_id,
    )


def outcome(
    state: TelegramIdentityResolutionState,
    **extra: object,
) -> TelegramIdentityResolutionOutcome:
    return TelegramIdentityResolutionOutcome(
        telegram_identity_resolution_reference_id="outcome-ref",
        telegram_identity_resolution_request_id="request-ref",
        identity_decision_reference_id="decision-ref",
        state=state,
        provider_identity=provider(),
        reason_code="decision-reference",
        **extra,
    )


def test_models_are_frozen_and_forbid_unknown_fields() -> None:
    for model in MODELS:
        assert model.model_config["frozen"] is True
        assert model.model_config["extra"] == "forbid"
    with pytest.raises((TypeError, ValidationError)):
        provider().telegram_user_id = "changed"  # type: ignore[misc]
    with pytest.raises(ValidationError):
        TelegramProviderIdentity.model_validate({**provider().model_dump(), "unexpected": "x"})


def test_external_identity_has_no_account_authority_and_rejects_blank_ids() -> None:
    assert "account_id" not in TelegramProviderIdentity.model_fields
    assert provider().telegram_user_id == "tg-user-42"
    assert provider().telegram_chat_id == "tg-chat-42"
    with pytest.raises(ValidationError):
        TelegramProviderIdentity.model_validate(
            {**provider().model_dump(), "telegram_user_id": "   "}
        )


def test_request_requires_metadata_and_all_idempotency_primitives() -> None:
    assert request().metadata.contract_name == "telegram.identity-resolution"
    assert request().metadata.producer == "telegram-adapter"
    for field in ("metadata", "idempotency_key", "idempotency_scope", "fingerprint"):
        payload = request().model_dump()
        payload.pop(field)
        with pytest.raises(ValidationError):
            TelegramIdentityResolutionRequest.model_validate(payload)
    assert "account_id" not in request().model_dump()
    assert "merge_key" not in TelegramIdentityResolutionRequest.model_fields


def test_link_reference_is_identity_decision_projection() -> None:
    assert account_link().identity_provider == "TELEGRAM"
    with pytest.raises(ValidationError):
        TelegramAccountLinkReference.model_validate(
            {**account_link().model_dump(), "identity_provider": "MAX"}
        )
    with pytest.raises(ValidationError, match="must match"):
        TelegramAccountLinkReference.model_validate(
            {**account_link().model_dump(), "identity_provider_identity_id": "other"}
        )


def test_outcome_matrix() -> None:
    assert outcome(
        TelegramIdentityResolutionState.RESOLVED_ACCOUNT, account_link=account_link()
    ).account_link
    assert outcome(
        TelegramIdentityResolutionState.LINK_CHALLENGE_REQUIRED,
        identity_link_challenge_ref="challenge-ref",
    )
    for state in (
        TelegramIdentityResolutionState.NEW_ACCOUNT_REQUESTED,
        TelegramIdentityResolutionState.REJECTED,
        TelegramIdentityResolutionState.AMBIGUOUS,
    ):
        assert outcome(state).account_link is None
        with pytest.raises(ValidationError):
            outcome(state, account_link=account_link())
    with pytest.raises(ValidationError):
        outcome(TelegramIdentityResolutionState.RESOLVED_ACCOUNT)
    with pytest.raises(ValidationError):
        outcome(TelegramIdentityResolutionState.LINK_CHALLENGE_REQUIRED)
    with pytest.raises(ValidationError):
        outcome(
            TelegramIdentityResolutionState.AMBIGUOUS,
            identity_link_challenge_ref="challenge",
        )
    with pytest.raises(ValidationError):
        outcome(
            TelegramIdentityResolutionState.RESOLVED_ACCOUNT,
            account_link=account_link(),
            identity_link_challenge_ref="challenge",
        )


def test_states_and_safe_serialization() -> None:
    assert [s.value for s in TelegramIdentityResolutionState] == [
        "RESOLVED_ACCOUNT",
        "NEW_ACCOUNT_REQUESTED",
        "LINK_CHALLENGE_REQUIRED",
        "REJECTED",
        "AMBIGUOUS",
    ]
    assert (
        "account_id"
        not in outcome(TelegramIdentityResolutionState.NEW_ACCOUNT_REQUESTED).model_dump()
    )
    serialized = str(evidence().model_dump())
    for forbidden in (
        "username",
        "display_name",
        "avatar",
        "phone",
        "email",
        "chat_title",
        "payload",
        "token",
        "secret",
    ):
        assert forbidden not in serialized
    assert evidence().model_dump()["provider_identity"]["telegram_chat_id"] != "account-42"


@pytest.mark.parametrize(
    "field",
    [
        "username",
        "display_name",
        "avatar",
        "phone",
        "email",
        "chat_title",
        "raw_payload",
        "token",
        "secret",
    ],
)
def test_provider_payload_and_weak_identity_fields_are_extra(field: str) -> None:
    with pytest.raises(ValidationError):
        TelegramProviderIdentity.model_validate({**provider().model_dump(), field: "synthetic"})
