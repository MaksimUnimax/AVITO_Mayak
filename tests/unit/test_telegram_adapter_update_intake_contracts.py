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
    TelegramProviderIdentity,
    TelegramProviderUpdateIdentity,
    TelegramUpdateAdmissionState,
    TelegramUpdateDeduplicationRecord,
    TelegramUpdateDeduplicationState,
    TelegramUpdateIntakeRecord,
    TelegramUpdateIntakeState,
    TelegramUpdateStructuralClass,
)


def meta() -> ContractMetadata:
    return ContractMetadata(
        contract_name="telegram.update",
        contract_version="1",
        message_id=uuid4(),
        correlation_id=uuid4(),
        producer="telegram-adapter",
    )


def update_identity(bot: str = "bot-ref") -> TelegramProviderUpdateIdentity:
    return TelegramProviderUpdateIdentity(
        telegram_provider_update_ref="update-ref",
        telegram_bot_ref=bot,
        telegram_update_id="update-42",
        provider_update_type_ref="opaque-type",
    )


def identity(bot: str = "bot-ref") -> TelegramProviderIdentity:
    return TelegramProviderIdentity(
        telegram_provider_identity_ref="identity-ref",
        telegram_bot_ref=bot,
        telegram_user_id="user-42",
    )


def common() -> dict[str, object]:
    return dict(
        metadata=meta(),
        provider_update_identity=update_identity(),
        idempotency_key=IdempotencyKey(value="key"),
        idempotency_scope=IdempotencyScope(value="telegram-update"),
        fingerprint=IdempotencyFingerprint(value="fp"),
        reason_code="reason",
    )


def intake(state: TelegramUpdateIntakeState, **changes: object) -> TelegramUpdateIntakeRecord:
    values = dict(
        telegram_update_intake_record_id="intake-ref",
        **common(),
        admission_state=TelegramUpdateAdmissionState.VERIFIED,
        structural_classification=TelegramUpdateStructuralClass.SUPPORTED_CANDIDATE,
        intake_state=state,
    )
    values.update(changes)
    return TelegramUpdateIntakeRecord.model_validate(values)


def dedup(
    state: TelegramUpdateDeduplicationState, **changes: object
) -> TelegramUpdateDeduplicationRecord:
    values = dict(
        telegram_update_deduplication_record_id="dedup-ref",
        current_intake_record_id="current",
        state=state,
        adapter_processing_authorized=state is TelegramUpdateDeduplicationState.NEW_UPDATE,
        **common(),
    )
    values.update(changes)
    return TelegramUpdateDeduplicationRecord.model_validate(values)


def test_exact_states_and_provider_identity_are_opaque() -> None:
    assert [x.value for x in TelegramUpdateAdmissionState] == [
        "VERIFIED",
        "NOT_VERIFIED",
        "REJECTED",
        "AMBIGUOUS",
    ]
    assert [x.value for x in TelegramUpdateStructuralClass] == [
        "SUPPORTED_CANDIDATE",
        "UNSUPPORTED",
        "MALFORMED",
        "AMBIGUOUS",
    ]
    assert [x.value for x in TelegramUpdateIntakeState] == [
        "ACCEPTED_FOR_NORMALIZATION",
        "IGNORED_UNSUPPORTED",
        "REJECTED_UNTRUSTED",
        "REJECTED_MALFORMED",
        "AMBIGUOUS",
    ]
    assert [x.value for x in TelegramUpdateDeduplicationState] == [
        "NEW_UPDATE",
        "DUPLICATE_REPLAY",
        "FINGERPRINT_CONFLICT",
        "AMBIGUOUS",
    ]
    assert set(TelegramProviderUpdateIdentity.model_fields) == {
        "telegram_provider_update_ref",
        "telegram_bot_ref",
        "telegram_update_id",
        "provider_update_type_ref",
    }
    with pytest.raises(ValidationError):
        TelegramProviderUpdateIdentity(
            telegram_provider_update_ref=" ",
            telegram_bot_ref="bot",
            telegram_update_id="id",
            provider_update_type_ref="type",
        )
    with pytest.raises(ValidationError):
        TelegramProviderUpdateIdentity.model_validate(
            {**update_identity().model_dump(), "raw_payload": "x"}
        )


def test_models_are_frozen_and_forbid_profile_authority_and_secret_fields() -> None:
    record = intake(
        TelegramUpdateIntakeState.ACCEPTED_FOR_NORMALIZATION,
        provider_admission_evidence_ref="evidence",
        normalization_reference_id="normalization",
    )
    assert record.business_dispatch_authorized is False
    assert record.model_config["frozen"] is True and record.model_config["extra"] == "forbid"
    with pytest.raises((TypeError, ValidationError)):
        record.reason_code = "changed"  # type: ignore[misc]
    for field in (
        "account_id",
        "raw_payload",
        "message_text",
        "username",
        "display_name",
        "avatar",
        "phone",
        "chat_title",
        "token",
        "secret",
    ):
        assert field not in TelegramUpdateIntakeRecord.model_fields
        with pytest.raises(ValidationError):
            TelegramUpdateIntakeRecord.model_validate({**record.model_dump(), field: "x"})


@pytest.mark.parametrize(
    "state,changes",
    [
        (
            TelegramUpdateIntakeState.ACCEPTED_FOR_NORMALIZATION,
            {
                "provider_admission_evidence_ref": "evidence",
                "normalization_reference_id": "normalization",
            },
        ),
        (
            TelegramUpdateIntakeState.IGNORED_UNSUPPORTED,
            {"structural_classification": TelegramUpdateStructuralClass.UNSUPPORTED},
        ),
        (
            TelegramUpdateIntakeState.REJECTED_UNTRUSTED,
            {"admission_state": TelegramUpdateAdmissionState.REJECTED},
        ),
        (
            TelegramUpdateIntakeState.REJECTED_MALFORMED,
            {"structural_classification": TelegramUpdateStructuralClass.MALFORMED},
        ),
        (
            TelegramUpdateIntakeState.AMBIGUOUS,
            {"admission_state": TelegramUpdateAdmissionState.AMBIGUOUS},
        ),
    ],
)
def test_valid_intake_matrix(state: TelegramUpdateIntakeState, changes: dict[str, object]) -> None:
    record = intake(state, **changes)
    assert (record.normalization_reference_id is None) is (
        state is not TelegramUpdateIntakeState.ACCEPTED_FOR_NORMALIZATION
    )


def test_intake_rejects_mismatch_and_invalid_matrix() -> None:
    accepted = intake(
        TelegramUpdateIntakeState.ACCEPTED_FOR_NORMALIZATION,
        provider_admission_evidence_ref="evidence",
        normalization_reference_id="normalization",
    )
    for changes in (
        {"provider_identity": identity("other-bot")},
        {"admission_state": TelegramUpdateAdmissionState.REJECTED},
        {
            "normalization_reference_id": "normalization",
            "intake_state": TelegramUpdateIntakeState.REJECTED_MALFORMED,
            "structural_classification": TelegramUpdateStructuralClass.MALFORMED,
        },
        {"intake_state": TelegramUpdateIntakeState.IGNORED_UNSUPPORTED},
    ):
        with pytest.raises(ValidationError):
            TelegramUpdateIntakeRecord.model_validate({**accepted.model_dump(), **changes})


def test_dedup_matrix_proves_replay_and_conflict_semantics() -> None:
    new = dedup(TelegramUpdateDeduplicationState.NEW_UPDATE)
    replay = dedup(
        TelegramUpdateDeduplicationState.DUPLICATE_REPLAY,
        existing_intake_record_id="old",
        existing_fingerprint=new.fingerprint,
        replayed_adapter_outcome_ref="outcome",
        adapter_processing_authorized=False,
    )
    conflict = dedup(
        TelegramUpdateDeduplicationState.FINGERPRINT_CONFLICT,
        existing_intake_record_id="old",
        existing_fingerprint=IdempotencyFingerprint(value="different"),
        adapter_processing_authorized=False,
    )
    ambiguous = dedup(
        TelegramUpdateDeduplicationState.AMBIGUOUS,
        existing_intake_record_id="old",
        existing_fingerprint=new.fingerprint,
        adapter_processing_authorized=False,
    )
    assert new.adapter_processing_authorized and not replay.adapter_processing_authorized
    assert (
        replay.replayed_adapter_outcome_ref == "outcome"
        and conflict.replayed_adapter_outcome_ref is None
        and ambiguous.replayed_adapter_outcome_ref is None
    )
    assert all(
        record.second_business_effect_authorized is False
        for record in (new, replay, conflict, ambiguous)
    )
    for state, changes in (
        (
            TelegramUpdateDeduplicationState.DUPLICATE_REPLAY,
            {
                "existing_intake_record_id": "old",
                "existing_fingerprint": IdempotencyFingerprint(value="different"),
                "replayed_adapter_outcome_ref": "outcome",
                "adapter_processing_authorized": False,
            },
        ),
        (
            TelegramUpdateDeduplicationState.FINGERPRINT_CONFLICT,
            {
                "existing_intake_record_id": "old",
                "existing_fingerprint": new.fingerprint,
                "adapter_processing_authorized": False,
            },
        ),
        (TelegramUpdateDeduplicationState.NEW_UPDATE, {"adapter_processing_authorized": False}),
    ):
        with pytest.raises(ValidationError):
            dedup(state, **changes)
