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
from mayak.modules.notification_delivery import NotificationSourceFamily
from mayak.modules.telegram_adapter import (
    TelegramOutboundMappingReasonCode,
    TelegramOutboundMappingState,
    TelegramOutboundRequestClass,
    TelegramOutboundRequestIntent,
    TelegramOutboundTargetReference,
)


def _metadata() -> ContractMetadata:
    return ContractMetadata(
        contract_name="telegram.outbound.mapping",
        contract_version="1",
        message_id=uuid4(),
        correlation_id=uuid4(),
        producer="telegram-adapter",
    )


def _target(**changes: object) -> TelegramOutboundTargetReference:
    values: dict[str, object] = {
        "telegram_outbound_target_reference_id": "telegram-target-ref",
        "notification_target_reference_id": "notification-target-ref",
        "telegram_bot_ref": "bot-ref",
        "telegram_chat_provider_reference": "private-chat-ref",
        "telegram_provider_identity_reference": "provider-identity-ref",
    }
    values.update(changes)
    return TelegramOutboundTargetReference(**values)  # type: ignore[arg-type]


def _intent(**changes: object) -> TelegramOutboundRequestIntent:
    values: dict[str, object] = {
        "telegram_outbound_request_intent_id": "intent-ref",
        "metadata": _metadata(),
        "request_class": TelegramOutboundRequestClass.PRIVATE_CHAT_MESSAGE_REQUEST,
        "notification_attempt_id": "attempt-ref",
        "notification_outbox_item_id": "outbox-ref",
        "notification_delivery_plan_id": "plan-ref",
        "notification_target_reference_id": "notification-target-ref",
        "telegram_bot_ref": "bot-ref",
        "telegram_chat_provider_reference": "private-chat-ref",
        "telegram_provider_identity_reference": "provider-identity-ref",
        "delivery_purpose": NotificationSourceFamily.NEW_LISTINGS_FOUND,
        "safe_listing_reference_ids": (),
        "safe_listing_card_reference_ids": (),
        "idempotency_key": IdempotencyKey(value="key-ref"),
        "idempotency_scope": IdempotencyScope(value="scope-ref"),
        "idempotency_fingerprint": IdempotencyFingerprint(value="fingerprint-ref"),
        "correlation_id": "correlation-ref",
        "causation_id": "causation-ref",
        "evidence_reference_ids": ("evidence-a", "evidence-b"),
    }
    values.update(changes)
    return TelegramOutboundRequestIntent(**values)  # type: ignore[arg-type]


def test_exact_enums_and_ordered_values() -> None:
    assert [item.value for item in TelegramOutboundRequestClass] == ["PRIVATE_CHAT_MESSAGE_REQUEST"]
    assert [item.value for item in TelegramOutboundMappingState] == [
        "REQUEST_PREPARED",
        "BLOCKED",
        "UNSUPPORTED_TARGET",
        "INVALID_CONTENT",
        "AMBIGUOUS",
    ]
    assert [item.value for item in TelegramOutboundMappingReasonCode] == [
        "TELEGRAM_PRIVATE_CHAT_REQUEST_PREPARED",
        "NOTIFICATION_ATTEMPT_NOT_READY",
        "NOTIFICATION_SCOPE_MISMATCH",
        "PRIVATE_CHAT_ADMISSION_REQUIRED",
        "TELEGRAM_TARGET_SCOPE_MISMATCH",
        "SAFE_CONTENT_REFERENCE_MISMATCH",
    ]


def test_target_is_frozen_forbid_extra_and_strips() -> None:
    target = _target(telegram_bot_ref=" bot-ref ")
    assert target.telegram_bot_ref == "bot-ref"
    with pytest.raises(ValidationError):
        _target(extra_field="forbidden")
    with pytest.raises(ValidationError):
        _target(internal_account_authority=True)
    with pytest.raises(ValidationError):
        _target(telegram_chat_provider_reference=" ")
    with pytest.raises(ValidationError):
        target.telegram_bot_ref = "other"  # type: ignore[misc]


def test_standalone_intent_intrinsic_validation_and_false_authority_flags() -> None:
    intent = _intent()
    assert intent.safe_listing_reference_ids == ()
    with pytest.raises(ValidationError):
        _intent(safe_listing_reference_ids=["listing-ref"])
    with pytest.raises(ValidationError):
        _intent(provider_call_authorized=True)
    with pytest.raises(ValidationError):
        _intent(correlation_id=" ")
    with pytest.raises(ValidationError):
        _intent(metadata={})


@pytest.mark.parametrize(
    ("state", "reason"),
    [
        (
            TelegramOutboundMappingState.REQUEST_PREPARED,
            TelegramOutboundMappingReasonCode.TELEGRAM_PRIVATE_CHAT_REQUEST_PREPARED,
        ),
        (
            TelegramOutboundMappingState.BLOCKED,
            TelegramOutboundMappingReasonCode.NOTIFICATION_ATTEMPT_NOT_READY,
        ),
        (
            TelegramOutboundMappingState.UNSUPPORTED_TARGET,
            TelegramOutboundMappingReasonCode.PRIVATE_CHAT_ADMISSION_REQUIRED,
        ),
        (
            TelegramOutboundMappingState.INVALID_CONTENT,
            TelegramOutboundMappingReasonCode.SAFE_CONTENT_REFERENCE_MISMATCH,
        ),
        (
            TelegramOutboundMappingState.AMBIGUOUS,
            TelegramOutboundMappingReasonCode.NOTIFICATION_SCOPE_MISMATCH,
        ),
    ],
)
def test_five_state_six_reason_matrix_is_closed(
    state: TelegramOutboundMappingState, reason: TelegramOutboundMappingReasonCode
) -> None:
    assert isinstance(state.value, str)
    assert isinstance(reason.value, str)


def test_target_public_fields_are_exact() -> None:
    assert tuple(TelegramOutboundTargetReference.model_fields) == (
        "telegram_outbound_target_reference_id",
        "notification_target_reference_id",
        "telegram_bot_ref",
        "telegram_chat_provider_reference",
        "telegram_provider_identity_reference",
        "private_chat_only_v1",
        "internal_account_authority",
        "group_or_channel_target_authority",
        "provider_call_authority",
    )
