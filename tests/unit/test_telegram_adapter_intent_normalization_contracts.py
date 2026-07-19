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
    TelegramCommandEnvelope,
    TelegramInboundInputKind,
    TelegramIntentFamily,
    TelegramIntentNormalizationRequest,
    TelegramIntentNormalizationState,
    TelegramIntentOwnerBoundary,
    TelegramProviderIdentity,
    TelegramProviderUpdateIdentity,
    TelegramUntrustedInputReference,
    TelegramUpdateAdmissionState,
    TelegramUpdateDeduplicationRecord,
    TelegramUpdateDeduplicationState,
    TelegramUpdateIntakeRecord,
    TelegramUpdateIntakeState,
    TelegramUpdateStructuralClass,
)


def meta() -> ContractMetadata:
    return ContractMetadata(contract_name="telegram.intent", contract_version="1", message_id=uuid4(), correlation_id=uuid4(), producer="telegram-adapter")  # noqa: E501


def update() -> TelegramProviderUpdateIdentity:
    return TelegramProviderUpdateIdentity(telegram_provider_update_ref="update-ref", telegram_bot_ref="bot-ref", telegram_update_id="42", provider_update_type_ref="type-ref")  # noqa: E501


def identity() -> TelegramProviderIdentity:
    return TelegramProviderIdentity(telegram_provider_identity_ref="identity-ref", telegram_bot_ref="bot-ref", telegram_user_id="user-ref")  # noqa: E501


def intake(**changes: object) -> TelegramUpdateIntakeRecord:
    values: dict[str, object] = {
        "telegram_update_intake_record_id": "intake-ref", "metadata": meta(), "provider_update_identity": update(), "provider_identity": identity(),  # noqa: E501
        "idempotency_key": IdempotencyKey(value="key"), "idempotency_scope": IdempotencyScope(value="scope"), "fingerprint": IdempotencyFingerprint(value="fingerprint"),  # noqa: E501
        "admission_state": TelegramUpdateAdmissionState.VERIFIED, "structural_classification": TelegramUpdateStructuralClass.SUPPORTED_CANDIDATE,  # noqa: E501
        "intake_state": TelegramUpdateIntakeState.ACCEPTED_FOR_NORMALIZATION, "provider_admission_evidence_ref": "admission-ref", "normalization_reference_id": "request-ref", "reason_code": "accepted",  # noqa: E501
    }
    values.update(changes)
    return TelegramUpdateIntakeRecord.model_validate(values)


def dedup(**changes: object) -> TelegramUpdateDeduplicationRecord:
    values: dict[str, object] = {
        "telegram_update_deduplication_record_id": "dedup-ref", "metadata": meta(), "provider_update_identity": update(),  # noqa: E501
        "idempotency_key": IdempotencyKey(value="key"), "idempotency_scope": IdempotencyScope(value="scope"), "fingerprint": IdempotencyFingerprint(value="fingerprint"),  # noqa: E501
        "state": TelegramUpdateDeduplicationState.NEW_UPDATE, "current_intake_record_id": "intake-ref", "adapter_processing_authorized": True, "reason_code": "new",  # noqa: E501
    }
    values.update(changes)
    return TelegramUpdateDeduplicationRecord.model_validate(values)


def untrusted(kind: TelegramInboundInputKind = TelegramInboundInputKind.COMMAND_CANDIDATE, **changes: object) -> TelegramUntrustedInputReference:  # noqa: E501
    values: dict[str, object] = {"telegram_untrusted_input_reference_id": "input-ref", "provider_update_identity": update(), "input_kind": kind, "input_evidence_reference_id": "evidence-ref"}  # noqa: E501
    values.update(changes)
    return TelegramUntrustedInputReference.model_validate(values)


def request(**changes: object) -> TelegramIntentNormalizationRequest:
    values: dict[str, object] = {"telegram_intent_normalization_request_id": "request-ref", "metadata": meta(), "intake_record": intake(), "deduplication_record": dedup(), "untrusted_input": untrusted(), "normalization_policy_reference_id": "policy-ref"}  # noqa: E501
    values.update(changes)
    return TelegramIntentNormalizationRequest.model_validate(values)


def envelope(state: TelegramIntentNormalizationState, family: TelegramIntentFamily, **changes: object) -> TelegramCommandEnvelope:  # noqa: E501
    boundaries = {
        TelegramIntentFamily.START_OR_LINK_TELEGRAM: (TelegramIntentOwnerBoundary.IDENTITY_AND_ACCESS,),  # noqa: E501
        TelegramIntentFamily.HELP_REQUESTED: (TelegramIntentOwnerBoundary.TELEGRAM_ADAPTER,),
        TelegramIntentFamily.LIST_MY_BEACONS_REQUESTED: (TelegramIntentOwnerBoundary.BEACON_MANAGEMENT,),  # noqa: E501
        TelegramIntentFamily.BEACON_STATUS_REQUESTED: (TelegramIntentOwnerBoundary.BEACON_MANAGEMENT,),  # noqa: E501
        TelegramIntentFamily.CREATE_BEACON_FROM_SOURCE_URL_REQUESTED: (TelegramIntentOwnerBoundary.BEACON_MANAGEMENT,),  # noqa: E501
        TelegramIntentFamily.BEACON_SETTINGS_REQUESTED: (TelegramIntentOwnerBoundary.BEACON_MANAGEMENT,),  # noqa: E501
        TelegramIntentFamily.UPDATE_BEACON_INTERVAL_OR_STATUS_PREF_REQUESTED: (TelegramIntentOwnerBoundary.BEACON_MANAGEMENT, TelegramIntentOwnerBoundary.NOTIFICATION_DELIVERY),  # noqa: E501
        TelegramIntentFamily.PAUSE_BEACON_REQUESTED: (TelegramIntentOwnerBoundary.BEACON_MANAGEMENT,),  # noqa: E501
        TelegramIntentFamily.RESUME_BEACON_REQUESTED: (TelegramIntentOwnerBoundary.BEACON_MANAGEMENT,),  # noqa: E501
        TelegramIntentFamily.DELETE_BEACON_REQUESTED_WITH_CONFIRMATION: (TelegramIntentOwnerBoundary.BEACON_MANAGEMENT,),  # noqa: E501
        TelegramIntentFamily.TARIFF_OR_LIMITS_REQUESTED: (TelegramIntentOwnerBoundary.ENTITLEMENTS_AND_BILLING,),  # noqa: E501
        TelegramIntentFamily.OPEN_FULL_LISTING_RESULT_REQUESTED: (TelegramIntentOwnerBoundary.NOTIFICATION_DELIVERY,),  # noqa: E501
        TelegramIntentFamily.TOGGLE_NO_NEW_STATUS_NOTIFICATION_REQUESTED: (TelegramIntentOwnerBoundary.NOTIFICATION_DELIVERY,),  # noqa: E501
    }.get(family, (TelegramIntentOwnerBoundary.BEACON_MANAGEMENT,))
    normalization_request = request()
    candidate_ref = None
    if family is TelegramIntentFamily.CREATE_BEACON_FROM_SOURCE_URL_REQUESTED:
        normalization_request = request(untrusted_input=untrusted(TelegramInboundInputKind.SOURCE_URL_CANDIDATE, candidate_source_url_reference_id="candidate-ref"))  # noqa: E501
        candidate_ref = "candidate-ref"
    values: dict[str, object] = {"telegram_command_envelope_id": "envelope-ref", "metadata": meta(), "normalization_request": normalization_request, "state": state, "intent_family": family, "owner_boundaries": boundaries, "owner_contract_reference_ids": tuple("owner-ref" for _ in boundaries), "candidate_source_url_reference_id": candidate_ref, "dangerous_action_confirmation_required": family is TelegramIntentFamily.DELETE_BEACON_REQUESTED_WITH_CONFIRMATION, "reason_code": "normalized"}  # noqa: E501
    values.update(changes)
    return TelegramCommandEnvelope.model_validate(values)


def test_exact_enums_and_safe_models() -> None:
    assert [x.value for x in TelegramInboundInputKind] == ["COMMAND_CANDIDATE", "MESSAGE_TEXT_CANDIDATE", "SOURCE_URL_CANDIDATE", "UNSUPPORTED_INPUT", "AMBIGUOUS_INPUT"]  # noqa: E501
    assert [x.value for x in TelegramIntentNormalizationState] == ["NORMALIZED", "UNSUPPORTED", "AMBIGUOUS", "BLOCKED"]  # noqa: E501
    assert [x.value for x in TelegramIntentOwnerBoundary] == ["TELEGRAM_ADAPTER", "IDENTITY_AND_ACCESS", "BEACON_MANAGEMENT", "NOTIFICATION_DELIVERY", "ENTITLEMENTS_AND_BILLING", "NONE"]  # noqa: E501
    assert TelegramIntentFamily.UNSUPPORTED_OR_AMBIGUOUS_INPUT.value == "UNSUPPORTED_OR_AMBIGUOUS_INPUT"  # noqa: E501
    for model in (TelegramUntrustedInputReference, TelegramIntentNormalizationRequest, TelegramCommandEnvelope):  # noqa: E501
        assert model.model_config["frozen"] and model.model_config["extra"] == "forbid"


def test_untrusted_candidate_is_opaque_and_safety_literals_reject_true() -> None:
    source = untrusted(TelegramInboundInputKind.SOURCE_URL_CANDIDATE, candidate_source_url_reference_id="candidate-ref")  # noqa: E501
    assert source.candidate_source_url_validated is False
    with pytest.raises(ValidationError):
        untrusted(candidate_source_url_reference_id="wrong-kind")
    for field in ("raw_provider_payload_present", "input_text_retained", "input_trusted", "input_is_authorization", "candidate_source_url_validated"):  # noqa: E501
        with pytest.raises(ValidationError):
            TelegramUntrustedInputReference.model_validate({**untrusted().model_dump(), field: True})  # noqa: E501


def test_request_requires_accepted_new_consistent_intake() -> None:
    assert request().business_dispatch_authorized is False
    cases = (
        {"intake_record": intake(intake_state=TelegramUpdateIntakeState.REJECTED_UNTRUSTED, admission_state=TelegramUpdateAdmissionState.REJECTED, normalization_reference_id=None, provider_admission_evidence_ref=None)},  # noqa: E501
        {"deduplication_record": dedup(state=TelegramUpdateDeduplicationState.DUPLICATE_REPLAY, existing_intake_record_id="old", existing_fingerprint=IdempotencyFingerprint(value="fingerprint"), replayed_adapter_outcome_ref="outcome", adapter_processing_authorized=False)},  # noqa: E501
        {"intake_record": intake(normalization_reference_id="other")},
        {"deduplication_record": dedup(fingerprint=IdempotencyFingerprint(value="other"))},
        {"untrusted_input": untrusted(provider_update_identity=TelegramProviderUpdateIdentity(telegram_provider_update_ref="other", telegram_bot_ref="bot-ref", telegram_update_id="43", provider_update_type_ref="type-ref"))},  # noqa: E501
    )
    for change in cases:
        with pytest.raises(ValidationError):
            request(**change)


def test_state_source_and_confirmation_matrices() -> None:
    assert envelope(TelegramIntentNormalizationState.NORMALIZED, TelegramIntentFamily.HELP_REQUESTED).owner_contract_reference_ids == ("owner-ref",)  # noqa: E501
    assert envelope(TelegramIntentNormalizationState.BLOCKED, TelegramIntentFamily.HELP_REQUESTED, owner_contract_reference_ids=(), blocking_decision_reference_id="block-ref").business_dispatch_authorized is False  # noqa: E501
    assert envelope(TelegramIntentNormalizationState.UNSUPPORTED, TelegramIntentFamily.UNSUPPORTED_OR_AMBIGUOUS_INPUT, normalization_request=request(untrusted_input=untrusted(TelegramInboundInputKind.UNSUPPORTED_INPUT)), owner_boundaries=(TelegramIntentOwnerBoundary.NONE,), owner_contract_reference_ids=(), dangerous_action_confirmation_required=False).blocking_decision_reference_id is None  # noqa: E501
    assert envelope(TelegramIntentNormalizationState.AMBIGUOUS, TelegramIntentFamily.UNSUPPORTED_OR_AMBIGUOUS_INPUT, normalization_request=request(untrusted_input=untrusted(TelegramInboundInputKind.AMBIGUOUS_INPUT)), owner_boundaries=(TelegramIntentOwnerBoundary.NONE,), owner_contract_reference_ids=(), dangerous_action_confirmation_required=False).state is TelegramIntentNormalizationState.AMBIGUOUS  # noqa: E501
    create_request = request(untrusted_input=untrusted(TelegramInboundInputKind.SOURCE_URL_CANDIDATE, candidate_source_url_reference_id="candidate-ref"))  # noqa: E501
    assert envelope(TelegramIntentNormalizationState.NORMALIZED, TelegramIntentFamily.CREATE_BEACON_FROM_SOURCE_URL_REQUESTED, normalization_request=create_request, candidate_source_url_reference_id="candidate-ref").candidate_source_url_reference_id == "candidate-ref"  # noqa: E501
    assert envelope(TelegramIntentNormalizationState.NORMALIZED, TelegramIntentFamily.DELETE_BEACON_REQUESTED_WITH_CONFIRMATION).dangerous_action_confirmation_required is True  # noqa: E501
    with pytest.raises(ValidationError):
        envelope(TelegramIntentNormalizationState.NORMALIZED, TelegramIntentFamily.HELP_REQUESTED, dangerous_action_confirmation_required=True)  # noqa: E501


@pytest.mark.parametrize("family", list(TelegramIntentFamily))
def test_owner_mapping_is_exact_and_all_effect_flags_are_false(family: TelegramIntentFamily) -> None:  # noqa: E501
    if family is TelegramIntentFamily.UNSUPPORTED_OR_AMBIGUOUS_INPUT:
        return
    model = envelope(TelegramIntentNormalizationState.NORMALIZED, family)
    assert len(model.owner_contract_reference_ids) == len(model.owner_boundaries)
    assert all(value is False for name, value in model.model_dump().items() if name.endswith("authorized") or name.endswith("selected"))  # noqa: E501
