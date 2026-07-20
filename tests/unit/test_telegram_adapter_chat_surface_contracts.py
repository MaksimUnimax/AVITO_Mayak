from __future__ import annotations

from copy import deepcopy
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
    TelegramChatSurfaceAdmissionOutcome,
    TelegramChatSurfaceAdmissionRequest,
    TelegramChatSurfaceAdmissionState,
    TelegramChatSurfaceClass,
    TelegramChatSurfaceReasonCode,
    TelegramProviderIdentity,
    TelegramProviderUpdateIdentity,
    TelegramUntrustedChatSurfaceReference,
    TelegramUpdateAdmissionState,
    TelegramUpdateIntakeRecord,
    TelegramUpdateIntakeState,
    TelegramUpdateStructuralClass,
    VerifiedTelegramIdentityEvidence,
)


def metadata() -> ContractMetadata:
    return ContractMetadata(
        contract_name="telegram.chat-surface",
        contract_version="1",
        message_id=uuid4(),
        correlation_id=uuid4(),
        producer="telegram-adapter",
    )


def intake(bot: str = "bot-ref", record_id: str = "intake-ref") -> TelegramUpdateIntakeRecord:
    return TelegramUpdateIntakeRecord(
        telegram_update_intake_record_id=record_id,
        metadata=metadata(),
        provider_update_identity=TelegramProviderUpdateIdentity(
            telegram_provider_update_ref="update-ref",
            telegram_bot_ref=bot,
            telegram_update_id="update-42",
            provider_update_type_ref="private-chat-candidate",
        ),
        idempotency_key=IdempotencyKey(value="key-ref"),
        idempotency_scope=IdempotencyScope(value="telegram-update"),
        fingerprint=IdempotencyFingerprint(value="fingerprint-ref"),
        admission_state=TelegramUpdateAdmissionState.VERIFIED,
        structural_classification=TelegramUpdateStructuralClass.SUPPORTED_CANDIDATE,
        intake_state=TelegramUpdateIntakeState.ACCEPTED_FOR_NORMALIZATION,
        provider_admission_evidence_ref="admission-ref",
        normalization_reference_id="normalization-ref",
        reason_code="accepted",
    )


def surface(
    kind: TelegramChatSurfaceClass,
    *,
    bot: str = "bot-ref",
    record_id: str = "intake-ref",
    **refs: object,
) -> TelegramUntrustedChatSurfaceReference:
    refs.setdefault(
        "private_participant_provider_identity_reference",
        "provider-identity-ref" if kind is TelegramChatSurfaceClass.PRIVATE_CHAT else None,
    )
    refs.setdefault(
        "forum_topic_provider_reference",
        "topic-ref" if kind is TelegramChatSurfaceClass.FORUM_TOPIC else None,
    )
    refs.setdefault(
        "business_connection_provider_reference",
        "business-ref" if kind is TelegramChatSurfaceClass.BUSINESS_CONNECTION else None,
    )
    refs.setdefault(
        "shared_chat_provider_reference",
        "shared-ref" if kind is TelegramChatSurfaceClass.SHARED_CHAT else None,
    )
    values: dict[str, object] = {
        "telegram_chat_surface_reference_id": "surface-ref",
        "telegram_bot_ref": bot,
        "telegram_update_intake_record_id": record_id,
        "telegram_chat_provider_reference": "chat-ref",
        "surface_class": kind,
        **refs,
    }
    return TelegramUntrustedChatSurfaceReference.model_validate(values)


def evidence(
    bot: str = "bot-ref", identity_ref: str = "provider-identity-ref"
) -> VerifiedTelegramIdentityEvidence:
    return VerifiedTelegramIdentityEvidence(
        verified_identity_evidence_ref="evidence-ref",
        provider_identity=TelegramProviderIdentity(
            telegram_provider_identity_ref=identity_ref,
            telegram_bot_ref=bot,
            telegram_user_id="user-ref",
        ),
        verification_method_ref="method-ref",
        verification_result_ref="result-ref",
    )


def request(
    kind: TelegramChatSurfaceClass = TelegramChatSurfaceClass.PRIVATE_CHAT, **changes: object
) -> TelegramChatSurfaceAdmissionRequest:
    values: dict[str, object] = {
        "telegram_chat_surface_admission_request_id": "request-ref",
        "metadata": metadata(),
        "update_intake_record": intake(),
        "chat_surface": surface(
            kind,
            private_participant_provider_identity_reference="provider-identity-ref"
            if kind is TelegramChatSurfaceClass.PRIVATE_CHAT
            else None,
            forum_topic_provider_reference="topic-ref"
            if kind is TelegramChatSurfaceClass.FORUM_TOPIC
            else None,
            business_connection_provider_reference="business-ref"
            if kind is TelegramChatSurfaceClass.BUSINESS_CONNECTION
            else None,
            shared_chat_provider_reference="shared-ref"
            if kind is TelegramChatSurfaceClass.SHARED_CHAT
            else None,
        ),
        "verified_telegram_provider_identity_evidence": evidence()
        if kind is TelegramChatSurfaceClass.PRIVATE_CHAT
        else None,
        "surface_policy_reference_id": "surface-policy",
    }
    values.update(changes)
    return TelegramChatSurfaceAdmissionRequest.model_validate(values)


def outcome(
    kind: TelegramChatSurfaceClass, **changes: object
) -> TelegramChatSurfaceAdmissionOutcome:
    req = request(kind)
    unsupported = {
        TelegramChatSurfaceClass.GROUP: (
            TelegramChatSurfaceAdmissionState.UNSUPPORTED_SURFACE_IGNORED,
            TelegramChatSurfaceReasonCode.GROUP_NOT_SUPPORTED,
        ),
        TelegramChatSurfaceClass.SUPERGROUP: (
            TelegramChatSurfaceAdmissionState.UNSUPPORTED_SURFACE_IGNORED,
            TelegramChatSurfaceReasonCode.SUPERGROUP_NOT_SUPPORTED,
        ),
        TelegramChatSurfaceClass.CHANNEL: (
            TelegramChatSurfaceAdmissionState.UNSUPPORTED_SURFACE_IGNORED,
            TelegramChatSurfaceReasonCode.CHANNEL_NOT_SUPPORTED,
        ),
        TelegramChatSurfaceClass.FORUM_TOPIC: (
            TelegramChatSurfaceAdmissionState.UNSUPPORTED_SURFACE_IGNORED,
            TelegramChatSurfaceReasonCode.FORUM_TOPIC_NOT_SUPPORTED,
        ),
        TelegramChatSurfaceClass.BUSINESS_CONNECTION: (
            TelegramChatSurfaceAdmissionState.UNSUPPORTED_SURFACE_IGNORED,
            TelegramChatSurfaceReasonCode.BUSINESS_CONNECTION_NOT_SUPPORTED,
        ),
        TelegramChatSurfaceClass.SHARED_CHAT: (
            TelegramChatSurfaceAdmissionState.UNSUPPORTED_SURFACE_IGNORED,
            TelegramChatSurfaceReasonCode.SHARED_CHAT_NOT_SUPPORTED,
        ),
        TelegramChatSurfaceClass.UNKNOWN: (
            TelegramChatSurfaceAdmissionState.AMBIGUOUS_SURFACE_REJECTED,
            TelegramChatSurfaceReasonCode.UNKNOWN_SURFACE,
        ),
    }
    state, reason = (
        (
            TelegramChatSurfaceAdmissionState.PRIVATE_CHAT_ADMITTED,
            TelegramChatSurfaceReasonCode.PRIVATE_CHAT_V1_SUPPORTED,
        )
        if kind is TelegramChatSurfaceClass.PRIVATE_CHAT
        else unsupported[kind]
    )
    values: dict[str, object] = {
        "telegram_chat_surface_admission_outcome_id": "outcome-ref",
        "metadata": metadata(),
        "request": req,
        "admission_state": state,
        "reason_code": reason,
        "admitted_update_intake_record_id": "intake-ref"
        if kind is TelegramChatSurfaceClass.PRIVATE_CHAT
        else None,
        "verified_provider_identity_reference": "provider-identity-ref"
        if kind is TelegramChatSurfaceClass.PRIVATE_CHAT
        else None,
        "safe_diagnostic_reference_id": None
        if kind is TelegramChatSurfaceClass.PRIVATE_CHAT
        else "diagnostic-ref",
    }
    values.update(changes)
    return TelegramChatSurfaceAdmissionOutcome.model_validate(values)


def test_exact_enums_and_serialization() -> None:
    assert [x.value for x in TelegramChatSurfaceClass] == [x.name for x in TelegramChatSurfaceClass]
    assert list(TelegramChatSurfaceClass) == [
        TelegramChatSurfaceClass.PRIVATE_CHAT,
        TelegramChatSurfaceClass.GROUP,
        TelegramChatSurfaceClass.SUPERGROUP,
        TelegramChatSurfaceClass.CHANNEL,
        TelegramChatSurfaceClass.FORUM_TOPIC,
        TelegramChatSurfaceClass.BUSINESS_CONNECTION,
        TelegramChatSurfaceClass.SHARED_CHAT,
        TelegramChatSurfaceClass.UNKNOWN,
    ]
    assert [x.value for x in TelegramChatSurfaceAdmissionState] == [
        "PRIVATE_CHAT_ADMITTED",
        "UNSUPPORTED_SURFACE_IGNORED",
        "AMBIGUOUS_SURFACE_REJECTED",
    ]
    assert [x.value for x in TelegramChatSurfaceReasonCode] == [
        "PRIVATE_CHAT_V1_SUPPORTED",
        "GROUP_NOT_SUPPORTED",
        "SUPERGROUP_NOT_SUPPORTED",
        "CHANNEL_NOT_SUPPORTED",
        "FORUM_TOPIC_NOT_SUPPORTED",
        "BUSINESS_CONNECTION_NOT_SUPPORTED",
        "SHARED_CHAT_NOT_SUPPORTED",
        "UNKNOWN_SURFACE",
    ]


def test_records_are_frozen_extra_forbid_and_strip_strings() -> None:
    records = (
        surface(
            TelegramChatSurfaceClass.PRIVATE_CHAT,
            private_participant_provider_identity_reference=" identity-ref ",
        ),
        request(),
        outcome(TelegramChatSurfaceClass.PRIVATE_CHAT),
    )
    assert records[0].telegram_chat_surface_reference_id == "surface-ref"
    for record in records:
        string_field = next(
            name for name, value in record.model_dump().items() if isinstance(value, str)
        )
        with pytest.raises((ValidationError, TypeError)):
            setattr(record, string_field, "changed")
        data = deepcopy(record.model_dump())
        data["unexpected"] = "rejected"
        with pytest.raises(ValidationError):
            type(record).model_validate(data)


def test_all_literal_flags_reject_opposites() -> None:
    for record in (
        surface(
            TelegramChatSurfaceClass.PRIVATE_CHAT,
            private_participant_provider_identity_reference="identity-ref",
        ),
        request(),
        outcome(TelegramChatSurfaceClass.PRIVATE_CHAT),
    ):
        for field, value in record.model_dump().items():
            if isinstance(value, bool):
                data = record.model_dump()
                data[field] = not value
                with pytest.raises(ValidationError):
                    type(record).model_validate(data)


@pytest.mark.parametrize("kind", list(TelegramChatSurfaceClass))
def test_specialized_reference_matrix_and_outcome_matrix(kind: TelegramChatSurfaceClass) -> None:
    assert surface(kind)
    assert outcome(kind)


@pytest.mark.parametrize(
    "kind,field",
    [
        (TelegramChatSurfaceClass.PRIVATE_CHAT, "forum_topic_provider_reference"),
        (TelegramChatSurfaceClass.FORUM_TOPIC, "private_participant_provider_identity_reference"),
        (TelegramChatSurfaceClass.BUSINESS_CONNECTION, "shared_chat_provider_reference"),
        (TelegramChatSurfaceClass.SHARED_CHAT, "business_connection_provider_reference"),
    ],
)
def test_wrong_specialized_reference_fails(kind: TelegramChatSurfaceClass, field: str) -> None:
    with pytest.raises(ValidationError):
        surface(kind, **{field: "wrong-ref"})


def test_private_identity_binding_and_scope_checks() -> None:
    with pytest.raises(ValidationError):
        request(verified_telegram_provider_identity_evidence=None)
    with pytest.raises(ValidationError):
        request(
            chat_surface=surface(
                TelegramChatSurfaceClass.PRIVATE_CHAT,
                private_participant_provider_identity_reference="other",
            )
        )
    with pytest.raises(ValidationError):
        request(verified_telegram_provider_identity_evidence=evidence(identity_ref="other"))
    with pytest.raises(ValidationError):
        request(verified_telegram_provider_identity_evidence=evidence(bot="other-bot"))
    with pytest.raises(ValidationError):
        request(
            chat_surface=surface(
                TelegramChatSurfaceClass.PRIVATE_CHAT,
                record_id="other",
                private_participant_provider_identity_reference="provider-identity-ref",
            )
        )
    with pytest.raises(ValidationError):
        request(
            chat_surface=surface(
                TelegramChatSurfaceClass.PRIVATE_CHAT,
                bot="other-bot",
                private_participant_provider_identity_reference="provider-identity-ref",
            )
        )


@pytest.mark.parametrize("kind", list(TelegramChatSurfaceClass)[1:])
def test_non_private_surfaces_reject_identity_evidence(kind: TelegramChatSurfaceClass) -> None:
    s = surface(
        kind,
        **{"forum_topic_provider_reference": "topic-ref"}
        if kind is TelegramChatSurfaceClass.FORUM_TOPIC
        else {},
    )
    with pytest.raises(ValidationError):
        request(kind, chat_surface=s, verified_telegram_provider_identity_evidence=evidence())


def test_outcome_handoff_matrix() -> None:
    private = outcome(TelegramChatSurfaceClass.PRIVATE_CHAT)
    assert private.admitted_update_intake_record_id == "intake-ref"
    assert private.verified_provider_identity_reference == "provider-identity-ref"
    with pytest.raises(ValidationError):
        outcome(TelegramChatSurfaceClass.PRIVATE_CHAT, safe_diagnostic_reference_id="bad")
    for kind in list(TelegramChatSurfaceClass)[1:]:
        ignored = outcome(kind)
        assert ignored.admitted_update_intake_record_id is None
        assert ignored.verified_provider_identity_reference is None
        assert ignored.safe_diagnostic_reference_id == "diagnostic-ref"
        with pytest.raises(ValidationError):
            outcome(kind, verified_provider_identity_reference="handoff")
        with pytest.raises(ValidationError):
            outcome(kind, safe_diagnostic_reference_id=None)


@pytest.mark.parametrize(
    "field",
    [
        "account_id",
        "internal_user_id",
        "beacon_id",
        "listing_id",
        "notification_attempt_id",
        "raw_telegram_chat_id",
        "chat_title",
        "username",
        "display_name",
        "group_member_ids",
        "phone",
        "contact",
        "message_text",
        "raw_update",
        "raw_payload",
        "bot_token",
        "webhook_secret",
        "ownership_grant",
        "authorization_grant",
    ],
)
def test_forbidden_handoff_and_provider_fields_are_rejected(field: str) -> None:
    data = request().model_dump()
    data[field] = "forbidden"
    with pytest.raises(ValidationError):
        TelegramChatSurfaceAdmissionRequest.model_validate(data)


@pytest.mark.parametrize(
    "state,reason",
    [
        (
            TelegramChatSurfaceAdmissionState.PRIVATE_CHAT_ADMITTED,
            TelegramChatSurfaceReasonCode.GROUP_NOT_SUPPORTED,
        ),
        (
            TelegramChatSurfaceAdmissionState.UNSUPPORTED_SURFACE_IGNORED,
            TelegramChatSurfaceReasonCode.PRIVATE_CHAT_V1_SUPPORTED,
        ),
        (
            TelegramChatSurfaceAdmissionState.AMBIGUOUS_SURFACE_REJECTED,
            TelegramChatSurfaceReasonCode.GROUP_NOT_SUPPORTED,
        ),
    ],
)
def test_invalid_state_reason_combinations_fail(
    state: TelegramChatSurfaceAdmissionState, reason: TelegramChatSurfaceReasonCode
) -> None:
    with pytest.raises(ValidationError):
        outcome(TelegramChatSurfaceClass.PRIVATE_CHAT, admission_state=state, reason_code=reason)
