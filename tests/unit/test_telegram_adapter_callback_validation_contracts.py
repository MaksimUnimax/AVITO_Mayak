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
    TelegramCallbackActionScope,
    TelegramCallbackAuthorizationEvidence,
    TelegramCallbackConfirmationState,
    TelegramCallbackExpiryState,
    TelegramCallbackPayloadValidationMode,
    TelegramCallbackReplayState,
    TelegramCallbackRiskClass,
    TelegramCallbackValidationOutcome,
    TelegramCallbackValidationRequest,
    TelegramCallbackValidationState,
    TelegramIdentityResolutionOutcome,
    TelegramIdentityResolutionState,
    TelegramIntentOwnerBoundary,
    TelegramProviderIdentity,
    TelegramProviderUpdateIdentity,
    TelegramUntrustedCallbackReference,
    TelegramUpdateAdmissionState,
    TelegramUpdateDeduplicationRecord,
    TelegramUpdateDeduplicationState,
    TelegramUpdateIntakeRecord,
    TelegramUpdateIntakeState,
    TelegramUpdateStructuralClass,
)


def meta() -> ContractMetadata:
    return ContractMetadata(
        contract_name="telegram.callback",
        contract_version="1",
        message_id=uuid4(),
        correlation_id=uuid4(),
        producer="telegram-adapter",
    )


def provider_identity() -> TelegramProviderIdentity:
    return TelegramProviderIdentity(
        telegram_provider_identity_ref="provider-ref",
        telegram_bot_ref="bot-ref",
        telegram_user_id="user-ref",
    )


def update_identity() -> TelegramProviderUpdateIdentity:
    return TelegramProviderUpdateIdentity(
        telegram_provider_update_ref="update-ref",
        telegram_bot_ref="bot-ref",
        telegram_update_id="42",
        provider_update_type_ref="callback",
    )


def intake() -> TelegramUpdateIntakeRecord:
    return TelegramUpdateIntakeRecord(
        telegram_update_intake_record_id="intake-ref",
        metadata=meta(),
        provider_update_identity=update_identity(),
        provider_identity=provider_identity(),
        idempotency_key=IdempotencyKey(value="key"),
        idempotency_scope=IdempotencyScope(value="scope"),
        fingerprint=IdempotencyFingerprint(value="fingerprint"),
        admission_state=TelegramUpdateAdmissionState.VERIFIED,
        structural_classification=TelegramUpdateStructuralClass.SUPPORTED_CANDIDATE,
        intake_state=TelegramUpdateIntakeState.ACCEPTED_FOR_NORMALIZATION,
        provider_admission_evidence_ref="admission-ref",
        normalization_reference_id="normalization-ref",
        reason_code="accepted",
    )


def dedup() -> TelegramUpdateDeduplicationRecord:
    return TelegramUpdateDeduplicationRecord(
        telegram_update_deduplication_record_id="dedup-ref",
        metadata=meta(),
        provider_update_identity=update_identity(),
        idempotency_key=IdempotencyKey(value="key"),
        idempotency_scope=IdempotencyScope(value="scope"),
        fingerprint=IdempotencyFingerprint(value="fingerprint"),
        state=TelegramUpdateDeduplicationState.NEW_UPDATE,
        current_intake_record_id="intake-ref",
        adapter_processing_authorized=True,
        reason_code="new",
    )


def callback(**changes: object) -> TelegramUntrustedCallbackReference:
    values: dict[str, object] = {
        "telegram_untrusted_callback_reference_id": "callback-ref",
        "provider_update_identity": update_identity(),
        "callback_query_reference_id": "query-ref",
        "opaque_callback_payload_reference_id": "opaque-ref",
        "payload_validation_mode": TelegramCallbackPayloadValidationMode.OPAQUE_SERVER_RESOLVED,
        "callback_action_idempotency_key": IdempotencyKey(value="key"),
        "callback_action_idempotency_scope": IdempotencyScope(value="scope"),
        "callback_payload_fingerprint": IdempotencyFingerprint(value="fingerprint"),
        "server_resolution_or_signature_evidence_reference_id": "validation-ref",
    }
    values.update(changes)
    return TelegramUntrustedCallbackReference.model_validate(values)


def identity_outcome() -> TelegramIdentityResolutionOutcome:
    return TelegramIdentityResolutionOutcome(
        telegram_identity_resolution_reference_id="resolution-ref",
        telegram_identity_resolution_request_id="resolution-request-ref",
        identity_decision_reference_id="decision-ref",
        state=TelegramIdentityResolutionState.RESOLVED_ACCOUNT,
        provider_identity=provider_identity(),
        reason_code="resolved",
        account_link=TelegramAccountLinkReference(
            telegram_account_link_reference_id="link-ref",
            provider_identity=provider_identity(),
            account_id="account-ref",
            identity_account_reference_id="identity-account-ref",
            identity_provider_identity_id="user-ref",
        ),
    )


def evidence(
    action: TelegramCallbackActionScope, granted: bool = True
) -> TelegramCallbackAuthorizationEvidence:
    owner = {
        TelegramCallbackActionScope.READ_BEACON: TelegramIntentOwnerBoundary.BEACON_MANAGEMENT,
        TelegramCallbackActionScope.DELETE_BEACON: TelegramIntentOwnerBoundary.BEACON_MANAGEMENT,
        TelegramCallbackActionScope.UNLINK_TELEGRAM_IDENTITY: TelegramIntentOwnerBoundary.IDENTITY_AND_ACCESS,  # noqa: E501
    }[action]
    return TelegramCallbackAuthorizationEvidence(
        telegram_callback_authorization_evidence_id="authorization-ref",
        action_scope=action,
        owner_boundary=owner,
        owning_module_contract_reference_id="module-contract-ref",
        owning_module_decision_reference_id="module-decision-ref",
        identity_resolution_outcome=identity_outcome(),
        server_side_ownership_check_performed=granted,
        authorization_granted=granted,
        action_scope_matches_decision=granted,
        actor_account_matches_owner=granted,
    )


def request(
    action: TelegramCallbackActionScope = TelegramCallbackActionScope.READ_BEACON, **changes: object
) -> TelegramCallbackValidationRequest:
    owners = {
        TelegramCallbackActionScope.OPEN_CONTEXT: TelegramIntentOwnerBoundary.TELEGRAM_ADAPTER,
        TelegramCallbackActionScope.READ_BEACON: TelegramIntentOwnerBoundary.BEACON_MANAGEMENT,
        TelegramCallbackActionScope.DELETE_BEACON: TelegramIntentOwnerBoundary.BEACON_MANAGEMENT,
        TelegramCallbackActionScope.UNLINK_TELEGRAM_IDENTITY: TelegramIntentOwnerBoundary.IDENTITY_AND_ACCESS,  # noqa: E501
        TelegramCallbackActionScope.UNSUPPORTED_ACTION: TelegramIntentOwnerBoundary.NONE,
        TelegramCallbackActionScope.AMBIGUOUS_ACTION: TelegramIntentOwnerBoundary.NONE,
    }
    risks = {
        TelegramCallbackActionScope.OPEN_CONTEXT: TelegramCallbackRiskClass.NON_DESTRUCTIVE,
        TelegramCallbackActionScope.READ_BEACON: TelegramCallbackRiskClass.NON_DESTRUCTIVE,
        TelegramCallbackActionScope.DELETE_BEACON: TelegramCallbackRiskClass.DESTRUCTIVE,
        TelegramCallbackActionScope.UNLINK_TELEGRAM_IDENTITY: TelegramCallbackRiskClass.IDENTITY_SENSITIVE,  # noqa: E501
        TelegramCallbackActionScope.UNSUPPORTED_ACTION: TelegramCallbackRiskClass.UNSUPPORTED_OR_AMBIGUOUS,  # noqa: E501
        TelegramCallbackActionScope.AMBIGUOUS_ACTION: TelegramCallbackRiskClass.UNSUPPORTED_OR_AMBIGUOUS,  # noqa: E501
    }
    values: dict[str, object] = {
        "telegram_callback_validation_request_id": "request-ref",
        "metadata": meta(),
        "intake_record": intake(),
        "deduplication_record": dedup(),
        "callback_reference": callback(),
        "action_scope": action,
        "risk_class": risks[action],
        "owner_boundary": owners[action],
        "replay_state": TelegramCallbackReplayState.NEW_ACTION,
        "expiry_state": TelegramCallbackExpiryState.NOT_REQUIRED,
        "confirmation_state": TelegramCallbackConfirmationState.NOT_REQUIRED,
        "authorization_evidence": None
        if owners[action]
        in {TelegramIntentOwnerBoundary.TELEGRAM_ADAPTER, TelegramIntentOwnerBoundary.NONE}
        else evidence(action),
        "callback_policy_reference_id": "policy-ref",
        "reason_code": "validated",
    }
    values.update(changes)
    return TelegramCallbackValidationRequest.model_validate(values)


def test_exact_enum_order_and_mapping() -> None:
    assert [x.value for x in TelegramCallbackActionScope] == [
        "OPEN_CONTEXT",
        "READ_BEACON",
        "UPDATE_BEACON",
        "PAUSE_BEACON",
        "RESUME_BEACON",
        "DELETE_BEACON",
        "CHANGE_BEACON_SOURCE_URL",
        "UNLINK_TELEGRAM_IDENTITY",
        "DISABLE_NOTIFICATION_CHANNEL",
        "TARIFF_OR_PAYMENT_SENSITIVE_ACTION",
        "UNSUPPORTED_ACTION",
        "AMBIGUOUS_ACTION",
    ]
    assert [x.value for x in TelegramCallbackRiskClass] == [
        "NON_DESTRUCTIVE",
        "STATE_CHANGING",
        "DESTRUCTIVE",
        "IDENTITY_SENSITIVE",
        "NOTIFICATION_SENSITIVE",
        "PAYMENT_OR_TARIFF_SENSITIVE",
        "UNSUPPORTED_OR_AMBIGUOUS",
    ]
    assert [x.value for x in TelegramCallbackPayloadValidationMode] == [
        "OPAQUE_SERVER_RESOLVED",
        "SIGNED_VALIDATED",
        "UNVALIDATED",
        "AMBIGUOUS",
    ]
    assert [x.value for x in TelegramCallbackReplayState] == [
        "NEW_ACTION",
        "DUPLICATE_REPLAY",
        "FINGERPRINT_CONFLICT",
        "AMBIGUOUS",
    ]
    assert [x.value for x in TelegramCallbackExpiryState] == [
        "NOT_REQUIRED",
        "VALID",
        "EXPIRED",
        "MISSING",
        "AMBIGUOUS",
    ]
    assert [x.value for x in TelegramCallbackConfirmationState] == [
        "NOT_REQUIRED",
        "REQUIRED",
        "VERIFIED",
        "REJECTED",
        "EXPIRED",
    ]
    assert [x.value for x in TelegramCallbackValidationState] == [
        "VALIDATED_FOR_OWNER_HANDOFF",
        "CONFIRMATION_REQUIRED",
        "REJECTED_UNTRUSTED",
        "REJECTED_EXPIRED",
        "REJECTED_UNAUTHORIZED",
        "DUPLICATE_REPLAY",
        "FINGERPRINT_CONFLICT",
        "UNSUPPORTED",
        "AMBIGUOUS",
        "BLOCKED",
    ]


def test_safe_models_and_untrusted_evidence() -> None:
    models = (
        TelegramUntrustedCallbackReference,
        TelegramCallbackAuthorizationEvidence,
        TelegramCallbackValidationRequest,
        TelegramCallbackValidationOutcome,
    )
    assert all(
        model.model_config["frozen"]
        and model.model_config["extra"] == "forbid"
        and model.model_config["str_strip_whitespace"]
        for model in models
    )
    with pytest.raises(ValidationError):
        callback(raw_callback_data_present=True)
    with pytest.raises(ValidationError):
        callback(
            payload_validation_mode=TelegramCallbackPayloadValidationMode.UNVALIDATED,
            server_resolution_or_signature_evidence_reference_id="bad",
        )
    with pytest.raises(ValidationError):
        callback(callback_data_trusted=True)


@pytest.mark.parametrize("action", list(TelegramCallbackActionScope))
def test_owner_risk_mapping_and_confirmation(action: TelegramCallbackActionScope) -> None:
    owners = {
        "OPEN_CONTEXT": "TELEGRAM_ADAPTER",
        "READ_BEACON": "BEACON_MANAGEMENT",
        "UPDATE_BEACON": "BEACON_MANAGEMENT",
        "PAUSE_BEACON": "BEACON_MANAGEMENT",
        "RESUME_BEACON": "BEACON_MANAGEMENT",
        "DELETE_BEACON": "BEACON_MANAGEMENT",
        "CHANGE_BEACON_SOURCE_URL": "BEACON_MANAGEMENT",
        "UNLINK_TELEGRAM_IDENTITY": "IDENTITY_AND_ACCESS",
        "DISABLE_NOTIFICATION_CHANNEL": "NOTIFICATION_DELIVERY",
        "TARIFF_OR_PAYMENT_SENSITIVE_ACTION": "ENTITLEMENTS_AND_BILLING",
        "UNSUPPORTED_ACTION": "NONE",
        "AMBIGUOUS_ACTION": "NONE",
    }
    risks = {
        "OPEN_CONTEXT": "NON_DESTRUCTIVE",
        "READ_BEACON": "NON_DESTRUCTIVE",
        "UPDATE_BEACON": "STATE_CHANGING",
        "PAUSE_BEACON": "STATE_CHANGING",
        "RESUME_BEACON": "STATE_CHANGING",
        "DELETE_BEACON": "DESTRUCTIVE",
        "CHANGE_BEACON_SOURCE_URL": "DESTRUCTIVE",
        "UNLINK_TELEGRAM_IDENTITY": "IDENTITY_SENSITIVE",
        "DISABLE_NOTIFICATION_CHANNEL": "NOTIFICATION_SENSITIVE",
        "TARIFF_OR_PAYMENT_SENSITIVE_ACTION": "PAYMENT_OR_TARIFF_SENSITIVE",
        "UNSUPPORTED_ACTION": "UNSUPPORTED_OR_AMBIGUOUS",
        "AMBIGUOUS_ACTION": "UNSUPPORTED_OR_AMBIGUOUS",
    }
    assert owners[action.value] in {x.value for x in TelegramIntentOwnerBoundary}
    assert risks[action.value] in {x.value for x in TelegramCallbackRiskClass}


def test_request_prerequisites_and_outcome_matrices() -> None:
    assert request().action_scope is TelegramCallbackActionScope.READ_BEACON
    assert request(TelegramCallbackActionScope.OPEN_CONTEXT).authorization_evidence is None
    with pytest.raises(ValidationError):
        request(
            callback_reference=callback(
                payload_validation_mode=TelegramCallbackPayloadValidationMode.UNVALIDATED
            )
        )
    with pytest.raises(ValidationError):
        request(TelegramCallbackActionScope.DELETE_BEACON)
    dangerous = request(
        TelegramCallbackActionScope.DELETE_BEACON,
        confirmation_state=TelegramCallbackConfirmationState.REQUIRED,
    )
    assert dangerous.confirmation_state is TelegramCallbackConfirmationState.REQUIRED
    with pytest.raises(ValidationError):
        request(existing_callback_outcome_reference_id="old")


def test_safety_literals_and_handoff_only() -> None:
    valid = request(TelegramCallbackActionScope.OPEN_CONTEXT)
    outcome = TelegramCallbackValidationOutcome(
        telegram_callback_validation_outcome_id="outcome-ref",
        metadata=meta(),
        validation_request=valid,
        state=TelegramCallbackValidationState.VALIDATED_FOR_OWNER_HANDOFF,
        owner_handoff_reference_id="handoff-ref",
        reason_code="handoff",
        owner_handoff_authorized=True,
    )
    assert outcome.owner_handoff_authorized is True
    assert outcome.business_execution_authorized is False
    with pytest.raises(ValidationError):
        TelegramCallbackValidationOutcome.model_validate(
            {**outcome.model_dump(), "business_execution_authorized": True}
        )
    with pytest.raises(ValidationError):
        TelegramCallbackValidationOutcome(
            telegram_callback_validation_outcome_id="outcome-ref",
            metadata=meta(),
            validation_request=valid,
            state=TelegramCallbackValidationState.BLOCKED,
            reason_code="blocked",
            owner_handoff_authorized=False,
        )


def test_identity_and_authorization_are_server_side() -> None:
    with pytest.raises(ValidationError):
        TelegramCallbackAuthorizationEvidence.model_validate(
            {
                **evidence(TelegramCallbackActionScope.READ_BEACON, granted=False).model_dump(),
                "identity_resolution_outcome": {
                    **identity_outcome().model_dump(),
                    "state": TelegramIdentityResolutionState.AMBIGUOUS,
                    "account_link": None,
                },
            }
        )
    with pytest.raises(ValidationError):
        request(
            TelegramCallbackActionScope.READ_BEACON,
            authorization_evidence=evidence(TelegramCallbackActionScope.READ_BEACON).model_copy(
                update={
                    "identity_resolution_outcome": identity_outcome().model_copy(
                        update={
                            "provider_identity": TelegramProviderIdentity(
                                telegram_provider_identity_ref="other",
                                telegram_bot_ref="bot-ref",
                                telegram_user_id="other-user",
                            )
                        }
                    )
                }
            ),
        )
