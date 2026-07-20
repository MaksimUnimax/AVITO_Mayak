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
    TelegramDeepLinkContextOwnerBoundary,
    TelegramDeepLinkContextResolutionEvidence,
    TelegramDeepLinkExpiryState,
    TelegramDeepLinkPayloadValidationMode,
    TelegramDeepLinkPurpose,
    TelegramDeepLinkReplayState,
    TelegramDeepLinkValidationOutcome,
    TelegramDeepLinkValidationRequest,
    TelegramDeepLinkValidationState,
    TelegramProviderIdentity,
    TelegramProviderUpdateIdentity,
    TelegramUntrustedDeepLinkReference,
    TelegramUpdateAdmissionState,
    TelegramUpdateDeduplicationRecord,
    TelegramUpdateDeduplicationState,
    TelegramUpdateIntakeRecord,
    TelegramUpdateIntakeState,
    TelegramUpdateStructuralClass,
    VerifiedTelegramIdentityEvidence,
)


def _meta() -> ContractMetadata:
    return ContractMetadata(
        contract_name="telegram.deep-link",
        contract_version="1",
        message_id=uuid4(),
        correlation_id=uuid4(),
        producer="telegram-adapter",
    )


def _identities() -> tuple[TelegramProviderIdentity, TelegramProviderUpdateIdentity]:
    return (
        TelegramProviderIdentity(
            telegram_provider_identity_ref="provider-ref",
            telegram_bot_ref="bot-ref",
            telegram_user_id="external-user-ref",
        ),
        TelegramProviderUpdateIdentity(
            telegram_provider_update_ref="update-ref",
            telegram_bot_ref="bot-ref",
            telegram_update_id="update-ref-id",
            provider_update_type_ref="message",
        ),
    )


def _parts(
    *,
    purpose: TelegramDeepLinkPurpose = TelegramDeepLinkPurpose.OPEN_BEACON_CONTEXT,
    mode: TelegramDeepLinkPayloadValidationMode = (
        TelegramDeepLinkPayloadValidationMode.OPAQUE_SERVER_RESOLVED
    ),
    replay: TelegramDeepLinkReplayState = TelegramDeepLinkReplayState.NEW_LINK,
    expiry: TelegramDeepLinkExpiryState = TelegramDeepLinkExpiryState.VALID,
    context_decision: str | None = None,
    context_ref: str | None = "context-ref",
    handoff_ref: str | None = "handoff-ref",
) -> tuple[
    TelegramUntrustedDeepLinkReference,
    TelegramDeepLinkContextResolutionEvidence,
    TelegramDeepLinkValidationRequest,
]:
    identity, update = _identities()
    deep_link = TelegramUntrustedDeepLinkReference(
        telegram_untrusted_deep_link_reference_id="deep-link-ref",
        telegram_bot_ref="bot-ref",
        telegram_update_intake_reference_id="intake-ref",
        provider_update_identity=update,
        deep_link_payload_fingerprint=IdempotencyFingerprint(value="payload-fp"),
        purpose_candidate=purpose,
    )
    decision_required = purpose in {
        TelegramDeepLinkPurpose.RETURN_FROM_WEB_CABINET,
        TelegramDeepLinkPurpose.OPEN_FUTURE_MINI_APP_CONTEXT,
    }
    eligible = (
        mode
        in {
            TelegramDeepLinkPayloadValidationMode.OPAQUE_SERVER_RESOLVED,
            TelegramDeepLinkPayloadValidationMode.SIGNED_VALIDATED,
        }
        and replay is TelegramDeepLinkReplayState.NEW_LINK
        and expiry is TelegramDeepLinkExpiryState.VALID
        and purpose
        not in {TelegramDeepLinkPurpose.UNSUPPORTED, TelegramDeepLinkPurpose.AMBIGUOUS}
        and (not decision_required or context_decision is not None)
    )
    effective_handoff = handoff_ref if eligible else None
    effective_context = context_ref if eligible else None
    evidence = TelegramDeepLinkContextResolutionEvidence(
        telegram_deep_link_context_resolution_evidence_id="evidence-ref",
        purpose=purpose,
        owner_boundary={
            TelegramDeepLinkPurpose.LINK_EXISTING_ACCOUNT: (
                TelegramDeepLinkContextOwnerBoundary.IDENTITY_AND_ACCESS
            ),
            TelegramDeepLinkPurpose.BOT_ONBOARDING: (
                TelegramDeepLinkContextOwnerBoundary.TELEGRAM_ADAPTER
            ),
            TelegramDeepLinkPurpose.OPEN_BEACON_CONTEXT: (
                TelegramDeepLinkContextOwnerBoundary.BEACON_MANAGEMENT
            ),
            TelegramDeepLinkPurpose.OPEN_RESULT_OR_LISTING_CONTEXT: (
                TelegramDeepLinkContextOwnerBoundary.NOTIFICATION_DELIVERY
            ),
            TelegramDeepLinkPurpose.RETURN_FROM_WEB_CABINET: (
                TelegramDeepLinkContextOwnerBoundary.WEB_CABINET
            ),
            TelegramDeepLinkPurpose.OPEN_FUTURE_MINI_APP_CONTEXT: (
                TelegramDeepLinkContextOwnerBoundary.FUTURE_MINI_APP_GATE
            ),
            TelegramDeepLinkPurpose.UNSUPPORTED: TelegramDeepLinkContextOwnerBoundary.NONE,
            TelegramDeepLinkPurpose.AMBIGUOUS: TelegramDeepLinkContextOwnerBoundary.NONE,
        }[purpose],
        validation_mode=mode,
        replay_state=replay,
        expiry_state=expiry,
        matching_payload_fingerprint=IdempotencyFingerprint(value="payload-fp"),
        external_validation_policy_reference="validation-policy-ref",
        external_signing_policy_reference="signing-policy-ref"
        if mode is TelegramDeepLinkPayloadValidationMode.SIGNED_VALIDATED
        else None,
        server_side_context_resolution_reference=effective_context,
        owner_contract_handoff_reference=effective_handoff,
        external_context_decision_reference=context_decision,
    )
    intake = TelegramUpdateIntakeRecord(
        telegram_update_intake_record_id="intake-ref",
        metadata=_meta(),
        provider_update_identity=update,
        provider_identity=identity,
        idempotency_key=IdempotencyKey(value="intake-key"),
        idempotency_scope=IdempotencyScope(value="telegram-scope"),
        fingerprint=IdempotencyFingerprint(value="update-fp"),
        admission_state=TelegramUpdateAdmissionState.VERIFIED,
        structural_classification=TelegramUpdateStructuralClass.SUPPORTED_CANDIDATE,
        intake_state=TelegramUpdateIntakeState.ACCEPTED_FOR_NORMALIZATION,
        provider_admission_evidence_ref="admission-ref",
        normalization_reference_id="normalization-ref",
        reason_code="accepted",
    )
    state_by_replay = {
        TelegramDeepLinkReplayState.NEW_LINK: TelegramUpdateDeduplicationState.NEW_UPDATE,
        TelegramDeepLinkReplayState.DUPLICATE_REPLAY: (
            TelegramUpdateDeduplicationState.DUPLICATE_REPLAY
        ),
        TelegramDeepLinkReplayState.FINGERPRINT_CONFLICT: (
            TelegramUpdateDeduplicationState.FINGERPRINT_CONFLICT
        ),
        TelegramDeepLinkReplayState.AMBIGUOUS: TelegramUpdateDeduplicationState.AMBIGUOUS,
    }
    state = state_by_replay[replay]
    is_duplicate = replay is TelegramDeepLinkReplayState.DUPLICATE_REPLAY
    dedup = TelegramUpdateDeduplicationRecord(
        telegram_update_deduplication_record_id="dedup-ref",
        metadata=_meta(),
        provider_update_identity=update,
        idempotency_key=IdempotencyKey(value="intake-key"),
        idempotency_scope=IdempotencyScope(value="telegram-scope"),
        fingerprint=IdempotencyFingerprint(value="update-fp"),
        state=state,
        current_intake_record_id="intake-ref",
        existing_intake_record_id=None
        if state is TelegramUpdateDeduplicationState.NEW_UPDATE
        else "old-intake",
        existing_fingerprint=None
        if state is TelegramUpdateDeduplicationState.NEW_UPDATE
        else IdempotencyFingerprint(
            value=(
                "old-fp"
                if replay is TelegramDeepLinkReplayState.FINGERPRINT_CONFLICT
                else "update-fp"
            )
        ),
        replayed_adapter_outcome_ref="old-outcome" if is_duplicate else None,
        adapter_processing_authorized=state is TelegramUpdateDeduplicationState.NEW_UPDATE,
        reason_code="dedup",
    )
    request = TelegramDeepLinkValidationRequest(
        telegram_deep_link_validation_request_id="request-ref",
        untrusted_deep_link_reference=deep_link,
        accepted_telegram_update_intake=intake,
        deduplication_evidence=dedup,
        verified_telegram_provider_identity_evidence=VerifiedTelegramIdentityEvidence(
            verified_identity_evidence_ref="verified-ref",
            provider_identity=identity,
            verification_method_ref="provider-policy-ref",
            verification_result_ref="provider-result-ref",
        ),
        context_resolution_evidence=evidence,
        deduplication_allows_new_processing=state is TelegramUpdateDeduplicationState.NEW_UPDATE,
    )
    return deep_link, evidence, request


def _outcome(
    request: TelegramDeepLinkValidationRequest, state: TelegramDeepLinkValidationState
) -> TelegramDeepLinkValidationOutcome:
    return TelegramDeepLinkValidationOutcome(
        telegram_deep_link_validation_outcome_id="outcome-ref",
        request=request,
        validation_state=state,
        owner_boundary=request.context_resolution_evidence.owner_boundary,
        owner_handoff_reference=request.context_resolution_evidence.owner_contract_handoff_reference
        if state
        in {
            TelegramDeepLinkValidationState.IDENTITY_HANDOFF_REQUIRED,
            TelegramDeepLinkValidationState.VALIDATED_FOR_OWNER_HANDOFF,
        }
        else None,
        blocking_reason_reference="block-ref"
        if state is TelegramDeepLinkValidationState.BLOCKED_PENDING_CONTEXT_DECISION
        else None,
    )


def test_exact_enums_and_owner_mapping() -> None:
    assert tuple(TelegramDeepLinkPurpose) == tuple(
        TelegramDeepLinkPurpose(value)
        for value in (
            "LINK_EXISTING_ACCOUNT",
            "BOT_ONBOARDING",
            "OPEN_BEACON_CONTEXT",
            "OPEN_RESULT_OR_LISTING_CONTEXT",
            "RETURN_FROM_WEB_CABINET",
            "OPEN_FUTURE_MINI_APP_CONTEXT",
            "UNSUPPORTED",
            "AMBIGUOUS",
        )
    )
    owners = [
        TelegramDeepLinkContextOwnerBoundary.IDENTITY_AND_ACCESS,
        TelegramDeepLinkContextOwnerBoundary.TELEGRAM_ADAPTER,
        TelegramDeepLinkContextOwnerBoundary.BEACON_MANAGEMENT,
        TelegramDeepLinkContextOwnerBoundary.NOTIFICATION_DELIVERY,
        TelegramDeepLinkContextOwnerBoundary.WEB_CABINET,
        TelegramDeepLinkContextOwnerBoundary.FUTURE_MINI_APP_GATE,
    ]
    for purpose, owner in zip(tuple(TelegramDeepLinkPurpose)[:6], owners, strict=True):
        assert _parts(purpose=purpose)[1].owner_boundary is owner


@pytest.mark.parametrize("purpose", tuple(TelegramDeepLinkPurpose)[:6])
def test_six_supported_purposes_validate_without_business_effect(
    purpose: TelegramDeepLinkPurpose,
) -> None:
    decision = (
        "decision-ref"
        if purpose
        in {
            TelegramDeepLinkPurpose.RETURN_FROM_WEB_CABINET,
            TelegramDeepLinkPurpose.OPEN_FUTURE_MINI_APP_CONTEXT,
        }
        else None
    )
    request = _parts(purpose=purpose, context_decision=decision)[2]
    state = (
        TelegramDeepLinkValidationState.IDENTITY_HANDOFF_REQUIRED
        if purpose is TelegramDeepLinkPurpose.LINK_EXISTING_ACCOUNT
        else TelegramDeepLinkValidationState.VALIDATED_FOR_OWNER_HANDOFF
    )
    outcome = _outcome(request, state)
    assert outcome.business_effect_authorized is False
    assert outcome.account_link_performed is False
    assert outcome.provider_runtime_performed is False


def test_mode_policy_replay_expiry_and_gates() -> None:
    signed = _parts(mode=TelegramDeepLinkPayloadValidationMode.SIGNED_VALIDATED)[1]
    assert signed.external_signing_policy_reference == "signing-policy-ref"
    with pytest.raises(ValidationError):
        TelegramDeepLinkContextResolutionEvidence.model_validate(
            signed.model_dump(exclude={"external_signing_policy_reference"})
        )
    duplicate_request = _parts(replay=TelegramDeepLinkReplayState.DUPLICATE_REPLAY)[2]
    assert (
        _outcome(
            duplicate_request, TelegramDeepLinkValidationState.DUPLICATE_REPLAY
        ).second_business_effect_authorized
        is False
    )
    for expiry in (TelegramDeepLinkExpiryState.EXPIRED, TelegramDeepLinkExpiryState.MISSING):
        request = _parts(expiry=expiry, handoff_ref=None, context_ref=None)[2]
        assert (
            _outcome(
                request, TelegramDeepLinkValidationState.REJECTED_EXPIRED
            ).owner_handoff_reference
            is None
        )


def test_untrusted_and_ambiguous_are_rejected_and_forbidden_fields_are_extra() -> None:
    request = _parts(
        mode=TelegramDeepLinkPayloadValidationMode.UNVALIDATED, context_ref=None, handoff_ref=None
    )[2]
    assert (
        _outcome(
            request, TelegramDeepLinkValidationState.REJECTED_UNTRUSTED
        ).deep_link_authorization_granted
        is False
    )
    with pytest.raises(ValidationError):
        TelegramUntrustedDeepLinkReference.model_validate(
            {**request.untrusted_deep_link_reference.model_dump(), "account_id": "internal"}
        )
    with pytest.raises(ValidationError):
        TelegramUntrustedDeepLinkReference.model_validate(
            {**request.untrusted_deep_link_reference.model_dump(), "raw_payload": "payload"}
        )


def test_context_decision_gate_and_identity_only_handoff() -> None:
    purpose = TelegramDeepLinkPurpose.RETURN_FROM_WEB_CABINET
    request = _parts(purpose=purpose, context_decision=None, context_ref=None, handoff_ref=None)[2]
    assert (
        _outcome(
            request, TelegramDeepLinkValidationState.BLOCKED_PENDING_CONTEXT_DECISION
        ).blocking_reason_reference
        == "block-ref"
    )
    identity_request = _parts(
        purpose=TelegramDeepLinkPurpose.LINK_EXISTING_ACCOUNT, context_ref=None
    )[2]
    outcome = _outcome(identity_request, TelegramDeepLinkValidationState.IDENTITY_HANDOFF_REQUIRED)
    assert outcome.account_link_performed is False


def test_ineligible_evidence_rejects_any_context_references() -> None:
    cases = (
        {"mode": TelegramDeepLinkPayloadValidationMode.UNVALIDATED},
        {"mode": TelegramDeepLinkPayloadValidationMode.AMBIGUOUS},
        {"replay": TelegramDeepLinkReplayState.DUPLICATE_REPLAY},
        {"replay": TelegramDeepLinkReplayState.FINGERPRINT_CONFLICT},
        {"replay": TelegramDeepLinkReplayState.AMBIGUOUS},
        {"expiry": TelegramDeepLinkExpiryState.EXPIRED},
        {"expiry": TelegramDeepLinkExpiryState.MISSING},
        {"expiry": TelegramDeepLinkExpiryState.AMBIGUOUS},
        {"purpose": TelegramDeepLinkPurpose.UNSUPPORTED},
        {"purpose": TelegramDeepLinkPurpose.AMBIGUOUS},
        {"purpose": TelegramDeepLinkPurpose.RETURN_FROM_WEB_CABINET},
        {"purpose": TelegramDeepLinkPurpose.OPEN_FUTURE_MINI_APP_CONTEXT},
    )
    for overrides in cases:
        evidence = _parts(**overrides)[1].model_dump()
        evidence["server_side_context_resolution_reference"] = "context-ref"
        evidence["owner_contract_handoff_reference"] = "handoff-ref"
        with pytest.raises(ValidationError):
            TelegramDeepLinkContextResolutionEvidence.model_validate(evidence)


def test_external_context_decision_allows_only_semantic_handoff() -> None:
    for purpose in (
        TelegramDeepLinkPurpose.RETURN_FROM_WEB_CABINET,
        TelegramDeepLinkPurpose.OPEN_FUTURE_MINI_APP_CONTEXT,
    ):
        request = _parts(purpose=purpose, context_decision="decision-ref")[2]
        evidence = request.context_resolution_evidence
        assert evidence.server_side_context_resolution_reference == "context-ref"
        assert evidence.owner_contract_handoff_reference == "handoff-ref"
        assert request.account_created is False
        assert request.account_linked is False
        assert request.business_effect_authorized is False


@pytest.mark.parametrize(
    ("replay", "dedup"),
    (
        (TelegramDeepLinkReplayState.NEW_LINK, TelegramUpdateDeduplicationState.NEW_UPDATE),
        (
            TelegramDeepLinkReplayState.DUPLICATE_REPLAY,
            TelegramUpdateDeduplicationState.DUPLICATE_REPLAY,
        ),
        (
            TelegramDeepLinkReplayState.FINGERPRINT_CONFLICT,
            TelegramUpdateDeduplicationState.FINGERPRINT_CONFLICT,
        ),
        (TelegramDeepLinkReplayState.AMBIGUOUS, TelegramUpdateDeduplicationState.AMBIGUOUS),
    ),
)
def test_replay_and_deduplication_mapping_is_exact(
    replay: TelegramDeepLinkReplayState, dedup: TelegramUpdateDeduplicationState
) -> None:
    request = _parts(replay=replay)[2]
    assert request.deduplication_evidence.state is dedup
    assert request.deduplication_evidence.adapter_processing_authorized is (
        dedup is TelegramUpdateDeduplicationState.NEW_UPDATE
    )


def test_replay_dedup_mismatch_and_identity_mismatches_are_rejected() -> None:
    request = _parts()[2]
    base = request.model_dump()
    for field, value in (
        ("deduplication_evidence.state", TelegramUpdateDeduplicationState.DUPLICATE_REPLAY),
        ("deduplication_evidence.adapter_processing_authorized", False),
        ("deduplication_evidence.provider_update_identity.telegram_bot_ref", "other-bot"),
        (
            "accepted_telegram_update_intake.provider_update_identity.telegram_update_id",
            "other-update",
        ),
        ("accepted_telegram_update_intake.telegram_update_intake_record_id", "other-intake"),
        ("deduplication_evidence.fingerprint.value", "other-fp"),
        ("untrusted_deep_link_reference.purpose_candidate", TelegramDeepLinkPurpose.BOT_ONBOARDING),
        ("context_resolution_evidence.owner_boundary", TelegramDeepLinkContextOwnerBoundary.NONE),
    ):
        mutated = base
        target = mutated
        parts = field.split(".")
        for part in parts[:-1]:
            target = target[part]
        target[parts[-1]] = value
        with pytest.raises(ValidationError):
            TelegramDeepLinkValidationRequest.model_validate(mutated)


def test_outcome_requires_exact_evidence_handoff_reference() -> None:
    request = _parts()[2]
    with pytest.raises(ValidationError):
        TelegramDeepLinkValidationOutcome(
            telegram_deep_link_validation_outcome_id="outcome-ref",
            request=request,
            validation_state=TelegramDeepLinkValidationState.VALIDATED_FOR_OWNER_HANDOFF,
            owner_boundary=request.context_resolution_evidence.owner_boundary,
            owner_handoff_reference="different-handoff",
            blocking_reason_reference=None,
        )


@pytest.mark.parametrize(
    "field",
    (
        "account_id", "beacon_id", "result_id", "listing_id", "email", "phone",
        "payment_id", "token", "secret", "raw_payload", "url",
    ),
)
def test_forbidden_fields_are_rejected_individually(field: str) -> None:
    reference = _parts()[0].model_dump()
    with pytest.raises(ValidationError):
        TelegramUntrustedDeepLinkReference.model_validate({**reference, field: "forbidden"})
