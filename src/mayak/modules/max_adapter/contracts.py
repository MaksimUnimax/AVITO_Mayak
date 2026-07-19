from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from mayak.contracts import (
    ContractMetadata,
    IdempotencyFingerprint,
    IdempotencyKey,
    IdempotencyScope,
)


class _MaxContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


class MaxEligibilityState(Enum):
    PROVEN = "PROVEN"
    UNPROVEN = "UNPROVEN"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    BLOCKED = "BLOCKED"
    UNSUPPORTED = "UNSUPPORTED"


class MaxUpdateIntakeState(Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED_UNTRUSTED = "REJECTED_UNTRUSTED"
    REJECTED_MALFORMED = "REJECTED_MALFORMED"
    IGNORED_UNSUPPORTED = "IGNORED_UNSUPPORTED"
    AMBIGUOUS = "AMBIGUOUS"
    BLOCKED = "BLOCKED"


class MaxUpdateDeduplicationState(Enum):
    NEW_UPDATE = "NEW_UPDATE"
    DUPLICATE_REPLAY = "DUPLICATE_REPLAY"
    FINGERPRINT_CONFLICT = "FINGERPRINT_CONFLICT"
    IDENTITY_AMBIGUOUS = "IDENTITY_AMBIGUOUS"
    BLOCKED = "BLOCKED"


class MaxCommandSourceKind(Enum):
    COMMAND = "COMMAND"
    CALLBACK = "CALLBACK"
    BUTTON = "BUTTON"
    DEEP_LINK = "DEEP_LINK"


class MaxCommandNormalizationState(Enum):
    NORMALIZED = "NORMALIZED"
    IGNORED = "IGNORED"
    UNSUPPORTED = "UNSUPPORTED"
    INVALID = "INVALID"
    AMBIGUOUS = "AMBIGUOUS"
    BLOCKED = "BLOCKED"


class MaxContactValidationState(Enum):
    POLICY_BLOCKED = "POLICY_BLOCKED"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    UNSUPPORTED = "UNSUPPORTED"
    AMBIGUOUS = "AMBIGUOUS"


class MaxMiniAppValidationState(Enum):
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    STALE = "STALE"
    MALFORMED = "MALFORMED"
    MISSING_HASH = "MISSING_HASH"
    BLOCKED = "BLOCKED"


class MaxOutboundRequestState(Enum):
    REQUEST_PREPARED = "REQUEST_PREPARED"
    BLOCKED = "BLOCKED"
    UNSUPPORTED_TARGET = "UNSUPPORTED_TARGET"
    INVALID_CONTENT = "INVALID_CONTENT"
    AMBIGUOUS = "AMBIGUOUS"


class MaxProviderOutcomeState(Enum):
    PROVIDER_ACCEPTED = "PROVIDER_ACCEPTED"
    PROVIDER_REJECTED = "PROVIDER_REJECTED"
    AUTH_FAILED = "AUTH_FAILED"
    UNAVAILABLE = "UNAVAILABLE"
    RATE_LIMITED = "RATE_LIMITED"
    MALFORMED = "MALFORMED"
    AMBIGUOUS = "AMBIGUOUS"
    BLOCKED = "BLOCKED"


class MaxRetryRecommendation(Enum):
    DO_NOT_RETRY = "DO_NOT_RETRY"
    RECONCILE_FIRST = "RECONCILE_FIRST"
    RETRY_ONLY_UNDER_NOTIFICATION_POLICY = "RETRY_ONLY_UNDER_NOTIFICATION_POLICY"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class MaxReconciliationState(Enum):
    RESOLVED_NO_EFFECT = "RESOLVED_NO_EFFECT"
    RESOLVED_EFFECT = "RESOLVED_EFFECT"
    REMAINS_AMBIGUOUS = "REMAINS_AMBIGUOUS"
    SUBSCRIPTION_DEGRADED = "SUBSCRIPTION_DEGRADED"
    MANUAL_REVIEW_REQUIRED = "MANUAL_REVIEW_REQUIRED"


class MaxProviderIdentity(_MaxContract):
    max_provider_identity_ref: str = Field(min_length=1)
    max_bot_ref: str = Field(min_length=1)
    max_user_id: str = Field(min_length=1)
    max_chat_id: str | None = Field(default=None, min_length=1)
    provider: Literal["MAX"] = "MAX"
    internal_account_authority: Literal[False] = False


class MaxAccountLinkReference(_MaxContract):
    max_account_link_reference_id: str = Field(min_length=1)
    provider_identity: MaxProviderIdentity
    account_id: str = Field(min_length=1)
    identity_account_reference_id: str = Field(min_length=1)
    identity_provider_identity_id: str = Field(min_length=1)
    identity_decision_reference_id: str = Field(min_length=1)
    identity_provider: Literal["MAX"] = "MAX"

    @model_validator(mode="after")
    def _validate_identity_reference(self) -> "MaxAccountLinkReference":
        if self.identity_provider_identity_id != self.provider_identity.max_user_id:
            raise ValueError("identity provider reference must match MAX user identity")
        return self


class MaxEligibilityEvidenceReference(_MaxContract):
    max_eligibility_evidence_reference_id: str = Field(min_length=1)
    state: MaxEligibilityState
    evidence_reference_id: str | None = Field(default=None, min_length=1)
    verified_profile_reference_id: str | None = Field(default=None, min_length=1)
    moderation_status_reference_id: str | None = Field(default=None, min_length=1)
    max_bot_ref: str | None = Field(default=None, min_length=1)
    safe_reference_only: Literal[True] = True
    contains_secret_material: Literal[False] = False

    @model_validator(mode="after")
    def _validate_proof_reference(self) -> "MaxEligibilityEvidenceReference":
        if self.state is MaxEligibilityState.PROVEN and self.evidence_reference_id is None:
            raise ValueError("PROVEN eligibility requires evidence reference")
        return self


class MaxUpdateIntakeRecord(_MaxContract):
    max_update_intake_record_id: str = Field(min_length=1)
    metadata: ContractMetadata
    max_update_reference: str = Field(min_length=1)
    max_bot_ref: str = Field(min_length=1)
    provider_update_family_ref: str = Field(min_length=1)
    provider_identity: MaxProviderIdentity | None = None
    idempotency_key: IdempotencyKey
    idempotency_scope: IdempotencyScope
    fingerprint: IdempotencyFingerprint
    state: MaxUpdateIntakeState
    authenticity_evidence_reference_id: str | None = Field(default=None, min_length=1)
    normalization_reference_id: str | None = Field(default=None, min_length=1)
    reason_code: str = Field(min_length=1)
    provider_payload_retained: Literal[False] = False
    business_dispatch_authority: Literal[False] = False


class MaxUpdateDeduplicationRecord(_MaxContract):
    max_update_deduplication_record_id: str = Field(min_length=1)
    metadata: ContractMetadata
    max_update_reference: str = Field(min_length=1)
    idempotency_key: IdempotencyKey
    idempotency_scope: IdempotencyScope
    fingerprint: IdempotencyFingerprint
    state: MaxUpdateDeduplicationState
    current_intake_record_id: str = Field(min_length=1)
    existing_intake_record_id: str | None = Field(default=None, min_length=1)
    existing_fingerprint: IdempotencyFingerprint | None = None
    replayed_adapter_outcome_reference_id: str | None = Field(default=None, min_length=1)
    reason_code: str = Field(min_length=1)
    second_business_effect_authority: Literal[False] = False


class MaxCommandEnvelope(_MaxContract):
    max_command_envelope_id: str = Field(min_length=1)
    metadata: ContractMetadata
    provider_identity: MaxProviderIdentity
    source_kind: MaxCommandSourceKind
    provider_payload_reference_id: str = Field(min_length=1)
    normalized_product_intent_reference_id: str | None = Field(default=None, min_length=1)
    state: MaxCommandNormalizationState
    reason_code: str = Field(min_length=1)
    client_payload_authority: Literal[False] = False
    business_execution_authority: Literal[False] = False


class MaxContactValidationResult(_MaxContract):
    max_contact_validation_result_id: str = Field(min_length=1)
    metadata: ContractMetadata
    provider_identity: MaxProviderIdentity | None = None
    state: MaxContactValidationState
    provider_contact_evidence_reference_id: str | None = Field(default=None, min_length=1)
    reason_code: str = Field(min_length=1)
    phone_required: Literal[False] = False
    account_merge_authority: Literal[False] = False
    contact_value_retained: Literal[False] = False


class MaxMiniAppValidationResult(_MaxContract):
    max_mini_app_validation_result_id: str = Field(min_length=1)
    metadata: ContractMetadata
    input_fingerprint: IdempotencyFingerprint
    state: MaxMiniAppValidationState
    provider_identity: MaxProviderIdentity | None = None
    validation_evidence_reference_id: str | None = Field(default=None, min_length=1)
    auth_date_policy_reference_id: str | None = Field(default=None, min_length=1)
    reason_code: str = Field(min_length=1)
    server_side_validation_performed: bool
    client_launch_data_trusted: Literal[False] = False
    authorization_authority: Literal[False] = False

    @model_validator(mode="after")
    def _validate_server_evidence(self) -> "MaxMiniAppValidationResult":
        if self.state is MaxMiniAppValidationState.VERIFIED:
            if not self.server_side_validation_performed:
                raise ValueError("VERIFIED Mini App result requires server validation")
            if self.provider_identity is None:
                raise ValueError("VERIFIED Mini App result requires provider identity")
            if self.validation_evidence_reference_id is None:
                raise ValueError("VERIFIED Mini App result requires validation evidence")
        elif self.provider_identity is not None:
            raise ValueError("non-VERIFIED Mini App result cannot carry provider identity")
        return self


class MaxOutboundRequest(_MaxContract):
    max_outbound_request_id: str = Field(min_length=1)
    metadata: ContractMetadata
    notification_outbox_item_id: str = Field(min_length=1)
    notification_attempt_id: str = Field(min_length=1)
    target_reference_id: str = Field(min_length=1)
    safe_message_reference_id: str = Field(min_length=1)
    safe_card_reference_id: str | None = Field(default=None, min_length=1)
    delivery_purpose_reference_id: str = Field(min_length=1)
    idempotency_key: IdempotencyKey
    idempotency_scope: IdempotencyScope
    fingerprint: IdempotencyFingerprint
    adapter_policy_reference_id: str = Field(min_length=1)
    state: MaxOutboundRequestState
    reason_code: str = Field(min_length=1)
    generic_outbox_authority: Literal[False] = False
    generic_delivery_success_authority: Literal[False] = False


class MaxProviderOutcome(_MaxContract):
    max_provider_outcome_id: str = Field(min_length=1)
    metadata: ContractMetadata
    max_outbound_request_id: str = Field(min_length=1)
    notification_attempt_id: str = Field(min_length=1)
    state: MaxProviderOutcomeState
    provider_response_reference_id: str | None = Field(default=None, min_length=1)
    max_message_id: str | None = Field(default=None, min_length=1)
    retry_recommendation: MaxRetryRecommendation
    reconciliation_required: bool
    reason_code: str = Field(min_length=1)
    human_read_proven: Literal[False] = False
    generic_delivery_success_authority: Literal[False] = False
    blind_retry_authority: Literal[False] = False

    @model_validator(mode="after")
    def _validate_ambiguity(self) -> "MaxProviderOutcome":
        if self.state is MaxProviderOutcomeState.AMBIGUOUS:
            if not self.reconciliation_required:
                raise ValueError("AMBIGUOUS outcome requires reconciliation")
            if self.retry_recommendation is not MaxRetryRecommendation.RECONCILE_FIRST:
                raise ValueError("AMBIGUOUS outcome requires reconcile-first recommendation")
        if self.retry_recommendation is MaxRetryRecommendation.RECONCILE_FIRST and not self.reconciliation_required:
            raise ValueError("reconcile-first recommendation requires reconciliation")
        return self


class MaxReconciliationRecord(_MaxContract):
    max_reconciliation_record_id: str = Field(min_length=1)
    metadata: ContractMetadata
    max_provider_outcome_id: str = Field(min_length=1)
    notification_attempt_id: str = Field(min_length=1)
    state: MaxReconciliationState
    reconciliation_evidence_reference_id: str | None = Field(default=None, min_length=1)
    reason_code: str = Field(min_length=1)
    blind_retry_authority: Literal[False] = False
    duplicate_user_visible_effect_authority: Literal[False] = False


class MaxAdapterReadModel(_MaxContract):
    max_adapter_read_model_id: str = Field(min_length=1)
    metadata: ContractMetadata
    max_provider_identity_ref: str | None = Field(default=None, min_length=1)
    max_eligibility_evidence_reference_id: str | None = Field(default=None, min_length=1)
    max_update_intake_record_id: str | None = Field(default=None, min_length=1)
    max_outbound_request_id: str | None = Field(default=None, min_length=1)
    max_provider_outcome_id: str | None = Field(default=None, min_length=1)
    safe_reason_codes: tuple[str, ...] = Field(default_factory=tuple)
    redacted_provider_reference_ids: tuple[str, ...] = Field(default_factory=tuple)
    raw_provider_payload_included: Literal[False] = False
    secret_material_included: Literal[False] = False
    phone_or_contact_included: Literal[False] = False
    mutation_authority: Literal[False] = False


__all__ = [
    "MaxAccountLinkReference",
    "MaxAdapterReadModel",
    "MaxCommandEnvelope",
    "MaxCommandNormalizationState",
    "MaxCommandSourceKind",
    "MaxContactValidationResult",
    "MaxContactValidationState",
    "MaxEligibilityEvidenceReference",
    "MaxEligibilityState",
    "MaxMiniAppValidationResult",
    "MaxMiniAppValidationState",
    "MaxOutboundRequest",
    "MaxOutboundRequestState",
    "MaxProviderIdentity",
    "MaxProviderOutcome",
    "MaxProviderOutcomeState",
    "MaxReconciliationRecord",
    "MaxReconciliationState",
    "MaxRetryRecommendation",
    "MaxUpdateDeduplicationRecord",
    "MaxUpdateDeduplicationState",
    "MaxUpdateIntakeRecord",
    "MaxUpdateIntakeState",
]
