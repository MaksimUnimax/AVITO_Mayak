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


class MaxUpdateAdmissionState(Enum):
    VERIFIED = "VERIFIED"
    NOT_VERIFIED = "NOT_VERIFIED"
    REJECTED = "REJECTED"
    AMBIGUOUS = "AMBIGUOUS"
    BLOCKED = "BLOCKED"


class MaxUpdateSourceKind(Enum):
    WEBHOOK = "WEBHOOK"
    LONG_POLLING_DEV_TEST = "LONG_POLLING_DEV_TEST"


class MaxUpdateStructuralClass(Enum):
    SUPPORTED_CANDIDATE = "SUPPORTED_CANDIDATE"
    UNSUPPORTED = "UNSUPPORTED"
    MALFORMED = "MALFORMED"
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


class MaxCommandSurfaceKind(Enum):
    PERSONAL_CHAT = "PERSONAL_CHAT"
    GROUP = "GROUP"
    CHANNEL = "CHANNEL"
    UNKNOWN = "UNKNOWN"


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
    source_kind: MaxUpdateSourceKind
    admission_state: MaxUpdateAdmissionState
    structural_classification: MaxUpdateStructuralClass
    approved_dev_test_context_reference_id: str | None = Field(default=None, min_length=1)
    long_polling_marker_reference_id: str | None = Field(default=None, min_length=1)
    production_fallback_authority: Literal[False] = False
    marker_business_identity_authority: Literal[False] = False
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

    @model_validator(mode="after")
    def _validate_intake_matrix(self) -> "MaxUpdateIntakeRecord":
        if self.source_kind is MaxUpdateSourceKind.WEBHOOK:
            if self.approved_dev_test_context_reference_id is not None:
                raise ValueError("WEBHOOK cannot carry development/test context")
            if self.long_polling_marker_reference_id is not None:
                raise ValueError("WEBHOOK cannot carry Long Polling marker")
        if self.source_kind is MaxUpdateSourceKind.LONG_POLLING_DEV_TEST:
            if self.approved_dev_test_context_reference_id is None:
                raise ValueError("Long Polling requires approved development/test context")
        if self.provider_identity is not None and self.provider_identity.max_bot_ref != self.max_bot_ref:
            raise ValueError("provider identity bot reference must match intake bot reference")
        if self.state is MaxUpdateIntakeState.ACCEPTED:
            if self.admission_state is not MaxUpdateAdmissionState.VERIFIED:
                raise ValueError("ACCEPTED intake requires verified admission")
            if self.structural_classification is not MaxUpdateStructuralClass.SUPPORTED_CANDIDATE:
                raise ValueError("ACCEPTED intake requires supported structure")
            if self.authenticity_evidence_reference_id is None:
                raise ValueError("ACCEPTED intake requires authenticity evidence")
            if self.normalization_reference_id is None:
                raise ValueError("ACCEPTED intake requires normalization reference")
        elif self.normalization_reference_id is not None:
            raise ValueError("only ACCEPTED intake may carry normalization reference")
        if self.state is MaxUpdateIntakeState.IGNORED_UNSUPPORTED:
            if self.structural_classification is not MaxUpdateStructuralClass.UNSUPPORTED:
                raise ValueError("IGNORED_UNSUPPORTED requires unsupported structure")
        elif self.state is MaxUpdateIntakeState.REJECTED_UNTRUSTED:
            if self.admission_state not in {
                MaxUpdateAdmissionState.NOT_VERIFIED,
                MaxUpdateAdmissionState.REJECTED,
            }:
                raise ValueError("REJECTED_UNTRUSTED requires unverified or rejected admission")
        elif self.state is MaxUpdateIntakeState.REJECTED_MALFORMED:
            if self.structural_classification is not MaxUpdateStructuralClass.MALFORMED:
                raise ValueError("REJECTED_MALFORMED requires malformed structure")
        elif self.state is MaxUpdateIntakeState.AMBIGUOUS:
            if (
                self.admission_state is not MaxUpdateAdmissionState.AMBIGUOUS
                and self.structural_classification is not MaxUpdateStructuralClass.AMBIGUOUS
            ):
                raise ValueError("AMBIGUOUS intake requires ambiguous admission or structure")
        elif self.state is MaxUpdateIntakeState.BLOCKED:
            if (
                self.admission_state is not MaxUpdateAdmissionState.BLOCKED
                and self.structural_classification is not MaxUpdateStructuralClass.BLOCKED
            ):
                raise ValueError("BLOCKED intake requires blocked admission or structure")
        return self


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
    adapter_processing_authorized: bool
    provider_marker_advance_authority: Literal[False] = False
    marker_business_identity_authority: Literal[False] = False

    @model_validator(mode="after")
    def _validate_deduplication_matrix(self) -> "MaxUpdateDeduplicationRecord":
        if self.state is MaxUpdateDeduplicationState.NEW_UPDATE:
            if self.existing_intake_record_id is not None or self.existing_fingerprint is not None:
                raise ValueError("NEW_UPDATE cannot carry existing intake or fingerprint")
            if self.replayed_adapter_outcome_reference_id is not None:
                raise ValueError("NEW_UPDATE cannot carry replayed outcome")
            if not self.adapter_processing_authorized:
                raise ValueError("NEW_UPDATE requires adapter processing authorization")
        elif self.state is MaxUpdateDeduplicationState.DUPLICATE_REPLAY:
            if self.existing_intake_record_id is None or self.existing_fingerprint is None:
                raise ValueError("DUPLICATE_REPLAY requires existing intake and fingerprint")
            if self.existing_fingerprint != self.fingerprint:
                raise ValueError("DUPLICATE_REPLAY requires matching fingerprint")
            if self.replayed_adapter_outcome_reference_id is None:
                raise ValueError("DUPLICATE_REPLAY requires replayed outcome")
            if self.adapter_processing_authorized:
                raise ValueError("DUPLICATE_REPLAY forbids adapter processing")
        elif self.state is MaxUpdateDeduplicationState.FINGERPRINT_CONFLICT:
            if self.existing_intake_record_id is None or self.existing_fingerprint is None:
                raise ValueError("FINGERPRINT_CONFLICT requires existing intake and fingerprint")
            if self.existing_fingerprint == self.fingerprint:
                raise ValueError("FINGERPRINT_CONFLICT requires different fingerprint")
            if self.replayed_adapter_outcome_reference_id is not None:
                raise ValueError("FINGERPRINT_CONFLICT cannot carry replayed outcome")
            if self.adapter_processing_authorized:
                raise ValueError("FINGERPRINT_CONFLICT forbids adapter processing")
        elif self.state is MaxUpdateDeduplicationState.IDENTITY_AMBIGUOUS:
            if self.existing_intake_record_id is None or self.existing_fingerprint is None:
                raise ValueError("IDENTITY_AMBIGUOUS requires existing intake and fingerprint")
            if self.replayed_adapter_outcome_reference_id is not None:
                raise ValueError("IDENTITY_AMBIGUOUS cannot carry replayed outcome")
            if self.adapter_processing_authorized:
                raise ValueError("IDENTITY_AMBIGUOUS forbids adapter processing")
        elif self.state is MaxUpdateDeduplicationState.BLOCKED:
            if self.replayed_adapter_outcome_reference_id is not None:
                raise ValueError("BLOCKED cannot carry replayed outcome")
            if self.adapter_processing_authorized:
                raise ValueError("BLOCKED forbids adapter processing")
            if (self.existing_intake_record_id is None) != (self.existing_fingerprint is None):
                raise ValueError("BLOCKED requires paired existing intake and fingerprint")
        return self


class MaxCommandEnvelope(_MaxContract):
    max_command_envelope_id: str = Field(min_length=1)
    metadata: ContractMetadata
    provider_identity: MaxProviderIdentity
    source_kind: MaxCommandSourceKind
    provider_payload_reference_id: str = Field(min_length=1)
    normalized_product_intent_reference_id: str | None = Field(default=None, min_length=1)
    state: MaxCommandNormalizationState
    reason_code: str = Field(min_length=1)
    intake_record: MaxUpdateIntakeRecord
    deduplication_record: MaxUpdateDeduplicationRecord
    surface_kind: MaxCommandSurfaceKind
    normalization_policy_reference_id: str = Field(min_length=1)
    owner_contract_reference_id: str | None = Field(default=None, min_length=1)
    ambiguity_evidence_reference_id: str | None = Field(default=None, min_length=1)
    blocking_decision_reference_id: str | None = Field(default=None, min_length=1)
    provider_payload_retained: Literal[False] = False
    provider_payload_trusted: Literal[False] = False
    telegram_payload_authority: Literal[False] = False
    internal_authorization_authority: Literal[False] = False
    account_merge_authority: Literal[False] = False
    beacon_mutation_authority: Literal[False] = False
    notification_eligibility_authority: Literal[False] = False
    destructive_action_authority: Literal[False] = False
    conversation_state_machine_authority: Literal[False] = False
    provider_runtime_authority: Literal[False] = False
    exact_command_catalog_selected: Literal[False] = False
    exact_callback_payload_format_selected: Literal[False] = False
    exact_deep_link_format_selected: Literal[False] = False
    client_payload_authority: Literal[False] = False
    business_execution_authority: Literal[False] = False

    @model_validator(mode="after")
    def _validate_normalization_prerequisites(self) -> "MaxCommandEnvelope":
        if self.intake_record.state is not MaxUpdateIntakeState.ACCEPTED:
            raise ValueError("command normalization requires accepted intake")
        if self.intake_record.admission_state is not MaxUpdateAdmissionState.VERIFIED:
            raise ValueError("command normalization requires verified intake admission")
        if self.intake_record.structural_classification is not MaxUpdateStructuralClass.SUPPORTED_CANDIDATE:
            raise ValueError("command normalization requires supported candidate intake")
        if self.intake_record.normalization_reference_id != self.max_command_envelope_id:
            raise ValueError("intake normalization reference must match command envelope")
        if self.intake_record.provider_identity is None:
            raise ValueError("accepted intake requires provider identity for command normalization")
        if self.intake_record.provider_identity != self.provider_identity:
            raise ValueError("intake provider identity must match command provider identity")

        dedup = self.deduplication_record
        if dedup.state is not MaxUpdateDeduplicationState.NEW_UPDATE:
            raise ValueError("only NEW_UPDATE deduplication may enter command normalization")
        if not dedup.adapter_processing_authorized:
            raise ValueError("NEW_UPDATE must authorize adapter processing")
        if dedup.current_intake_record_id != self.intake_record.max_update_intake_record_id:
            raise ValueError("dedup current intake reference must match intake record")
        if dedup.max_update_reference != self.intake_record.max_update_reference:
            raise ValueError("dedup update reference must match intake record")
        if dedup.idempotency_key != self.intake_record.idempotency_key:
            raise ValueError("dedup idempotency key must match intake record")
        if dedup.idempotency_scope != self.intake_record.idempotency_scope:
            raise ValueError("dedup idempotency scope must match intake record")
        if dedup.fingerprint != self.intake_record.fingerprint:
            raise ValueError("dedup fingerprint must match intake record")

        if self.surface_kind is MaxCommandSurfaceKind.PERSONAL_CHAT:
            if self.state is MaxCommandNormalizationState.NORMALIZED and self.provider_identity.max_chat_id is None:
                raise ValueError("normalized personal chat requires MAX chat identity")
        elif self.surface_kind in {MaxCommandSurfaceKind.GROUP, MaxCommandSurfaceKind.CHANNEL}:
            if self.state is not MaxCommandNormalizationState.BLOCKED:
                raise ValueError("group and channel normalization is blocked")
            if self.blocking_decision_reference_id is None:
                raise ValueError("blocked group or channel requires blocking decision")
            if self.normalized_product_intent_reference_id is not None or self.owner_contract_reference_id is not None:
                raise ValueError("blocked group or channel cannot carry intent or owner reference")
        elif self.surface_kind is MaxCommandSurfaceKind.UNKNOWN:
            if self.state not in {
                MaxCommandNormalizationState.AMBIGUOUS,
                MaxCommandNormalizationState.BLOCKED,
            }:
                raise ValueError("unknown command surface must be ambiguous or blocked")

        if self.state is MaxCommandNormalizationState.NORMALIZED:
            if self.surface_kind is not MaxCommandSurfaceKind.PERSONAL_CHAT:
                raise ValueError("normalized command requires personal chat")
            if self.normalized_product_intent_reference_id is None:
                raise ValueError("normalized command requires opaque intent reference")
            if self.owner_contract_reference_id is None:
                raise ValueError("normalized command requires owner contract reference")
            if self.ambiguity_evidence_reference_id is not None or self.blocking_decision_reference_id is not None:
                raise ValueError("normalized command cannot carry ambiguity or blocking evidence")
        elif self.state in {
            MaxCommandNormalizationState.IGNORED,
            MaxCommandNormalizationState.UNSUPPORTED,
            MaxCommandNormalizationState.INVALID,
        }:
            if self.normalized_product_intent_reference_id is not None or self.owner_contract_reference_id is not None:
                raise ValueError("non-normalized command cannot carry intent or owner reference")
            if self.ambiguity_evidence_reference_id is not None or self.blocking_decision_reference_id is not None:
                raise ValueError("ignored, unsupported or invalid command cannot carry ambiguity or blocking evidence")
        elif self.state is MaxCommandNormalizationState.AMBIGUOUS:
            if self.normalized_product_intent_reference_id is not None or self.owner_contract_reference_id is not None:
                raise ValueError("ambiguous command cannot carry intent or owner reference")
            if self.ambiguity_evidence_reference_id is None:
                raise ValueError("ambiguous command requires ambiguity evidence")
            if self.blocking_decision_reference_id is not None:
                raise ValueError("ambiguous command cannot carry blocking decision")
        elif self.state is MaxCommandNormalizationState.BLOCKED:
            if self.normalized_product_intent_reference_id is not None or self.owner_contract_reference_id is not None:
                raise ValueError("blocked command cannot carry intent or owner reference")
            if self.ambiguity_evidence_reference_id is not None:
                raise ValueError("blocked command cannot carry ambiguity evidence")
            if self.blocking_decision_reference_id is None:
                raise ValueError("blocked command requires blocking decision")
        return self


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
    max_bot_ref: str = Field(min_length=1)
    launch_context_reference_id: str = Field(min_length=1)
    validation_policy_reference_id: str = Field(min_length=1)
    state: MaxMiniAppValidationState
    provider_identity: MaxProviderIdentity | None = None
    validation_evidence_reference_id: str | None = Field(default=None, min_length=1)
    auth_date_policy_reference_id: str | None = Field(default=None, min_length=1)
    canonicalization_evidence_reference_id: str | None = Field(default=None, min_length=1)
    hash_validation_evidence_reference_id: str | None = Field(default=None, min_length=1)
    auth_date_evidence_reference_id: str | None = Field(default=None, min_length=1)
    blocking_decision_reference_id: str | None = Field(default=None, min_length=1)
    reason_code: str = Field(min_length=1)
    server_side_validation_performed: bool
    client_launch_data_trusted: Literal[False] = False
    authorization_authority: Literal[False] = False
    raw_web_app_data_retained: Literal[False] = False
    raw_web_app_data_trusted: Literal[False] = False
    client_side_validation_authority: Literal[False] = False
    internal_account_authority: Literal[False] = False
    identity_link_authority: Literal[False] = False
    web_cabinet_screen_authority: Literal[False] = False
    mini_app_frontend_authority: Literal[False] = False
    runtime_endpoint_authority: Literal[False] = False
    provider_configuration_authority: Literal[False] = False
    token_material_present: Literal[False] = False
    auth_date_threshold_defined_here: Literal[False] = False
    validated_external_identity_only: Literal[True] = True
    server_side_authorization_still_required: Literal[True] = True

    @model_validator(mode="after")
    def _validate_server_evidence(self) -> "MaxMiniAppValidationResult":
        if self.state is MaxMiniAppValidationState.BLOCKED:
            if self.server_side_validation_performed:
                raise ValueError("BLOCKED Mini App result cannot claim server validation")
            if self.validation_evidence_reference_id is not None:
                raise ValueError("BLOCKED Mini App result cannot carry validation evidence")
            if self.blocking_decision_reference_id is None:
                raise ValueError("BLOCKED Mini App result requires blocking decision reference")
        else:
            if not self.server_side_validation_performed:
                raise ValueError("non-BLOCKED Mini App result requires server validation")
            if self.validation_evidence_reference_id is None:
                raise ValueError("non-BLOCKED Mini App result requires validation evidence")
            if self.blocking_decision_reference_id is not None:
                raise ValueError("non-BLOCKED Mini App result cannot carry blocking decision reference")

        if self.state is MaxMiniAppValidationState.VERIFIED:
            if self.provider_identity is None:
                raise ValueError("VERIFIED Mini App result requires provider identity")
            if self.provider_identity.max_bot_ref != self.max_bot_ref:
                raise ValueError("provider identity bot reference must match Mini App bot reference")
            if self.auth_date_policy_reference_id is None:
                raise ValueError("VERIFIED Mini App result requires auth-date policy reference")
            if self.canonicalization_evidence_reference_id is None:
                raise ValueError("VERIFIED Mini App result requires canonicalization evidence")
            if self.hash_validation_evidence_reference_id is None:
                raise ValueError("VERIFIED Mini App result requires hash validation evidence")
            if self.auth_date_evidence_reference_id is None:
                raise ValueError("VERIFIED Mini App result requires auth-date evidence")
        elif self.provider_identity is not None:
            raise ValueError("non-VERIFIED Mini App result cannot carry provider identity")

        if self.state is MaxMiniAppValidationState.REJECTED:
            if self.canonicalization_evidence_reference_id is None:
                raise ValueError("REJECTED Mini App result requires canonicalization evidence")
            if self.hash_validation_evidence_reference_id is None:
                raise ValueError("REJECTED Mini App result requires hash validation evidence")
            if self.auth_date_policy_reference_id is not None:
                raise ValueError("REJECTED Mini App result cannot carry auth-date policy reference")
            if self.auth_date_evidence_reference_id is not None:
                raise ValueError("REJECTED Mini App result cannot carry auth-date evidence")
        elif self.state is MaxMiniAppValidationState.STALE:
            if self.auth_date_policy_reference_id is None:
                raise ValueError("STALE Mini App result requires auth-date policy reference")
            if self.canonicalization_evidence_reference_id is None:
                raise ValueError("STALE Mini App result requires canonicalization evidence")
            if self.hash_validation_evidence_reference_id is None:
                raise ValueError("STALE Mini App result requires hash validation evidence")
            if self.auth_date_evidence_reference_id is None:
                raise ValueError("STALE Mini App result requires auth-date evidence")
        elif self.state in {
            MaxMiniAppValidationState.MALFORMED,
            MaxMiniAppValidationState.MISSING_HASH,
        }:
            if self.auth_date_policy_reference_id is not None:
                raise ValueError(f"{self.state.value} Mini App result cannot carry auth-date policy reference")
            if self.canonicalization_evidence_reference_id is not None:
                raise ValueError(f"{self.state.value} Mini App result cannot carry canonicalization evidence")
            if self.hash_validation_evidence_reference_id is not None:
                raise ValueError(f"{self.state.value} Mini App result cannot carry hash validation evidence")
            if self.auth_date_evidence_reference_id is not None:
                raise ValueError(f"{self.state.value} Mini App result cannot carry auth-date evidence")
        elif self.state is MaxMiniAppValidationState.BLOCKED:
            if self.auth_date_policy_reference_id is not None:
                raise ValueError("BLOCKED Mini App result cannot carry auth-date policy reference")
            if self.canonicalization_evidence_reference_id is not None:
                raise ValueError("BLOCKED Mini App result cannot carry canonicalization evidence")
            if self.hash_validation_evidence_reference_id is not None:
                raise ValueError("BLOCKED Mini App result cannot carry hash validation evidence")
            if self.auth_date_evidence_reference_id is not None:
                raise ValueError("BLOCKED Mini App result cannot carry auth-date evidence")
        return self


class MaxOutboundRequest(_MaxContract):
    max_outbound_request_id: str = Field(min_length=1)
    metadata: ContractMetadata
    notification_outbox_item_id: str = Field(min_length=1)
    notification_attempt_id: str = Field(min_length=1)
    notification_channel: Literal["MAX"] = "MAX"
    notification_attempt_lifecycle: Literal["ATTEMPT_PLANNED"] = "ATTEMPT_PLANNED"
    target_reference_id: str = Field(min_length=1)
    target_kind: Literal["PERSONAL_CHAT", "GROUP", "CHANNEL", "UNKNOWN"]
    max_bot_ref: str = Field(min_length=1)
    max_chat_id: str | None = Field(default=None, min_length=1)
    safe_message_reference_id: str = Field(min_length=1)
    safe_card_reference_id: str | None = Field(default=None, min_length=1)
    delivery_purpose_reference_id: str = Field(min_length=1)
    idempotency_key: IdempotencyKey
    idempotency_scope: IdempotencyScope
    fingerprint: IdempotencyFingerprint
    adapter_policy_reference_id: str = Field(min_length=1)
    provider_request_intent_reference_id: str | None = Field(default=None, min_length=1)
    mapping_evidence_reference_id: str = Field(min_length=1)
    ambiguity_evidence_reference_id: str | None = Field(default=None, min_length=1)
    blocking_decision_reference_id: str | None = Field(default=None, min_length=1)
    correlation_id: str = Field(min_length=1)
    causation_id: str = Field(min_length=1)
    state: MaxOutboundRequestState
    reason_code: str = Field(min_length=1)
    generic_outbox_authority: Literal[False] = False
    generic_delivery_success_authority: Literal[False] = False
    notification_attempt_mutation_authority: Literal[False] = False
    notification_retry_authority: Literal[False] = False
    notification_reconciliation_authority: Literal[False] = False
    notification_eligibility_authority: Literal[False] = False
    provider_call_authority: Literal[False] = False
    live_provider_request_sent: Literal[False] = False
    provider_payload_retained: Literal[False] = False
    secret_material_present: Literal[False] = False
    final_message_rendering_authority: Literal[False] = False

    @model_validator(mode="after")
    def _validate_outbound_mapping(self) -> "MaxOutboundRequest":
        if self.state is not MaxOutboundRequestState.REQUEST_PREPARED and self.provider_request_intent_reference_id is not None:
            raise ValueError("only REQUEST_PREPARED may carry provider request intent")
        if self.state is not MaxOutboundRequestState.AMBIGUOUS and self.ambiguity_evidence_reference_id is not None:
            raise ValueError("only AMBIGUOUS may carry ambiguity evidence")
        if self.state is not MaxOutboundRequestState.BLOCKED and self.blocking_decision_reference_id is not None:
            raise ValueError("only BLOCKED may carry blocking decision")

        if self.state is MaxOutboundRequestState.REQUEST_PREPARED:
            if self.target_kind != "PERSONAL_CHAT" or self.max_chat_id is None:
                raise ValueError("REQUEST_PREPARED requires a personal chat and MAX chat reference")
            if self.provider_request_intent_reference_id is None:
                raise ValueError("REQUEST_PREPARED requires provider request intent")
        elif self.state is MaxOutboundRequestState.BLOCKED:
            if self.blocking_decision_reference_id is None:
                raise ValueError("BLOCKED requires blocking decision")
            if self.max_chat_id is not None or self.provider_request_intent_reference_id is not None or self.ambiguity_evidence_reference_id is not None:
                raise ValueError("BLOCKED forbids MAX chat, request intent, and ambiguity evidence")
        elif self.state is MaxOutboundRequestState.UNSUPPORTED_TARGET:
            if self.target_kind not in {"GROUP", "CHANNEL"} or self.max_chat_id is not None or self.provider_request_intent_reference_id is not None or self.ambiguity_evidence_reference_id is not None or self.blocking_decision_reference_id is not None:
                raise ValueError("UNSUPPORTED_TARGET requires GROUP or CHANNEL without dispatch references")
        elif self.state is MaxOutboundRequestState.INVALID_CONTENT:
            if self.target_kind != "PERSONAL_CHAT" or self.max_chat_id is None or self.provider_request_intent_reference_id is not None or self.ambiguity_evidence_reference_id is not None or self.blocking_decision_reference_id is not None:
                raise ValueError("INVALID_CONTENT requires personal chat without dispatch references")
        elif self.state is MaxOutboundRequestState.AMBIGUOUS:
            if self.target_kind != "UNKNOWN" or self.ambiguity_evidence_reference_id is None or self.max_chat_id is not None or self.provider_request_intent_reference_id is not None or self.blocking_decision_reference_id is not None:
                raise ValueError("AMBIGUOUS requires UNKNOWN target and ambiguity evidence only")
        return self


class MaxProviderOutcome(_MaxContract):
    max_provider_outcome_id: str = Field(min_length=1)
    metadata: ContractMetadata
    outbound_request: MaxOutboundRequest
    max_outbound_request_id: str = Field(min_length=1)
    notification_attempt_id: str = Field(min_length=1)
    notification_outbox_item_id: str = Field(min_length=1)
    target_reference_id: str = Field(min_length=1)
    notification_channel: Literal["MAX"] = "MAX"
    notification_outcome_class: Literal["DISPATCH_AMBIGUOUS", "PROVIDER_ACCEPTED", "PROVIDER_REJECTED", "PROVIDER_UNAVAILABLE", "RATE_OR_ACCESS_RESTRICTED", "MALFORMED_OR_UNUSABLE_PROVIDER_RESPONSE", "DELIVERY_AMBIGUOUS", "SUPPRESSED_OR_CANCELLED", "TARGET_UNAVAILABLE_OR_UNVERIFIED"]
    state: MaxProviderOutcomeState
    provider_response_reference_id: str | None = Field(default=None, min_length=1)
    max_message_id: str | None = Field(default=None, min_length=1)
    max_callback_reference_id: str | None = Field(default=None, min_length=1)
    provider_safe_delivery_reference_id: str | None = Field(default=None, min_length=1)
    egress_correlation_reference_id: str | None = Field(default=None, min_length=1)
    retry_recommendation: MaxRetryRecommendation
    reconciliation_required: bool
    failure_policy_reference_id: str | None = Field(default=None, min_length=1)
    ambiguity_evidence_reference_id: str | None = Field(default=None, min_length=1)
    blocking_decision_reference_id: str | None = Field(default=None, min_length=1)
    outcome_evidence_reference_id: str = Field(min_length=1)
    adapter_contract_reference_id: str = Field(min_length=1)
    adapter_contract_version_reference_id: str = Field(min_length=1)
    correlation_id: str = Field(min_length=1)
    causation_id: str = Field(min_length=1)
    reason_code: str = Field(min_length=1)
    human_read_proven: Literal[False] = False
    generic_delivery_success_authority: Literal[False] = False
    blind_retry_authority: Literal[False] = False
    adapter_outcome_committed: Literal[True] = True
    contains_raw_provider_payload: Literal[False] = False
    provider_payload_retained: Literal[False] = False
    secret_material_present: Literal[False] = False
    provider_call_authority: Literal[False] = False
    notification_outbox_authority: Literal[False] = False
    notification_attempt_mutation_authority: Literal[False] = False
    notification_delivery_lifecycle_authority: Literal[False] = False
    retry_execution_authority: Literal[False] = False
    business_success_proven: Literal[False] = False
    user_visible_delivery_proven: Literal[False] = False

    @model_validator(mode="after")
    def _validate_ambiguity(self) -> "MaxProviderOutcome":
        if self.outbound_request.state is not MaxOutboundRequestState.REQUEST_PREPARED:
            raise ValueError("outcome requires REQUEST_PREPARED outbound request")
        for field in ("max_outbound_request_id", "notification_attempt_id", "notification_outbox_item_id", "target_reference_id", "correlation_id", "causation_id"):
            if getattr(self, field) != getattr(self.outbound_request, field):
                raise ValueError(f"{field} must match outbound request")
        if self.retry_recommendation is MaxRetryRecommendation.RETRY_ONLY_UNDER_NOTIFICATION_POLICY:
            if self.failure_policy_reference_id is None:
                raise ValueError("policy retry requires failure policy reference")
        elif self.failure_policy_reference_id is not None:
            raise ValueError("failure policy reference is only for policy retry")
        if self.state is not MaxProviderOutcomeState.AMBIGUOUS and self.ambiguity_evidence_reference_id is not None:
            raise ValueError("only AMBIGUOUS may carry ambiguity evidence")
        if self.state is not MaxProviderOutcomeState.BLOCKED and self.blocking_decision_reference_id is not None:
            raise ValueError("only BLOCKED may carry blocking decision")
        if self.state is not MaxProviderOutcomeState.PROVIDER_ACCEPTED and any((self.max_message_id, self.max_callback_reference_id, self.provider_safe_delivery_reference_id)):
            raise ValueError("delivery references require PROVIDER_ACCEPTED")

        if self.state is MaxProviderOutcomeState.PROVIDER_ACCEPTED:
            if self.notification_outcome_class != "PROVIDER_ACCEPTED" or self.provider_response_reference_id is None or self.provider_safe_delivery_reference_id is None or self.retry_recommendation is not MaxRetryRecommendation.NOT_APPLICABLE or self.reconciliation_required or self.failure_policy_reference_id is not None or self.ambiguity_evidence_reference_id is not None or self.blocking_decision_reference_id is not None:
                raise ValueError("invalid PROVIDER_ACCEPTED outcome mapping")
        elif self.state is MaxProviderOutcomeState.PROVIDER_REJECTED:
            if self.notification_outcome_class != "PROVIDER_REJECTED" or self.provider_response_reference_id is None or self.reconciliation_required or self.ambiguity_evidence_reference_id is not None or self.blocking_decision_reference_id is not None or self.max_message_id is not None or self.max_callback_reference_id is not None or self.provider_safe_delivery_reference_id is not None or self.retry_recommendation not in {MaxRetryRecommendation.DO_NOT_RETRY, MaxRetryRecommendation.RETRY_ONLY_UNDER_NOTIFICATION_POLICY}:
                raise ValueError("invalid PROVIDER_REJECTED outcome mapping")
        elif self.state is MaxProviderOutcomeState.AUTH_FAILED:
            if self.notification_outcome_class != "RATE_OR_ACCESS_RESTRICTED" or self.provider_response_reference_id is None or self.retry_recommendation is not MaxRetryRecommendation.DO_NOT_RETRY or self.reconciliation_required or any((self.failure_policy_reference_id, self.max_message_id, self.max_callback_reference_id, self.provider_safe_delivery_reference_id, self.ambiguity_evidence_reference_id, self.blocking_decision_reference_id)):
                raise ValueError("invalid AUTH_FAILED outcome mapping")
        elif self.state is MaxProviderOutcomeState.UNAVAILABLE:
            if self.notification_outcome_class != "PROVIDER_UNAVAILABLE" or self.retry_recommendation is not MaxRetryRecommendation.RETRY_ONLY_UNDER_NOTIFICATION_POLICY or self.failure_policy_reference_id is None or self.reconciliation_required or any((self.max_message_id, self.max_callback_reference_id, self.provider_safe_delivery_reference_id, self.ambiguity_evidence_reference_id, self.blocking_decision_reference_id)):
                raise ValueError("invalid UNAVAILABLE outcome mapping")
        elif self.state is MaxProviderOutcomeState.RATE_LIMITED:
            if self.notification_outcome_class != "RATE_OR_ACCESS_RESTRICTED" or self.provider_response_reference_id is None or self.retry_recommendation is not MaxRetryRecommendation.RETRY_ONLY_UNDER_NOTIFICATION_POLICY or self.failure_policy_reference_id is None or self.reconciliation_required or any((self.max_message_id, self.max_callback_reference_id, self.provider_safe_delivery_reference_id, self.ambiguity_evidence_reference_id, self.blocking_decision_reference_id)):
                raise ValueError("invalid RATE_LIMITED outcome mapping")
        elif self.state is MaxProviderOutcomeState.MALFORMED:
            if self.notification_outcome_class != "MALFORMED_OR_UNUSABLE_PROVIDER_RESPONSE" or self.provider_response_reference_id is None or self.retry_recommendation is not MaxRetryRecommendation.DO_NOT_RETRY or self.reconciliation_required or any((self.failure_policy_reference_id, self.max_message_id, self.max_callback_reference_id, self.provider_safe_delivery_reference_id, self.ambiguity_evidence_reference_id, self.blocking_decision_reference_id)):
                raise ValueError("invalid MALFORMED outcome mapping")
        elif self.state is MaxProviderOutcomeState.AMBIGUOUS:
            if self.notification_outcome_class not in {"DISPATCH_AMBIGUOUS", "DELIVERY_AMBIGUOUS"} or self.retry_recommendation is not MaxRetryRecommendation.RECONCILE_FIRST or not self.reconciliation_required or self.ambiguity_evidence_reference_id is None or any((self.failure_policy_reference_id, self.max_message_id, self.max_callback_reference_id, self.provider_safe_delivery_reference_id, self.blocking_decision_reference_id)):
                raise ValueError("invalid AMBIGUOUS outcome mapping")
        elif self.state is MaxProviderOutcomeState.BLOCKED:
            if self.notification_outcome_class != "SUPPRESSED_OR_CANCELLED" or self.retry_recommendation is not MaxRetryRecommendation.NOT_APPLICABLE or self.reconciliation_required or self.blocking_decision_reference_id is None or any((self.provider_response_reference_id, self.failure_policy_reference_id, self.max_message_id, self.max_callback_reference_id, self.provider_safe_delivery_reference_id, self.ambiguity_evidence_reference_id)):
                raise ValueError("invalid BLOCKED outcome mapping")
        return self


class MaxReconciliationRecord(_MaxContract):
    max_reconciliation_record_id: str = Field(min_length=1)
    metadata: ContractMetadata
    provider_outcome: MaxProviderOutcome
    max_provider_outcome_id: str = Field(min_length=1)
    max_outbound_request_id: str = Field(min_length=1)
    notification_attempt_id: str = Field(min_length=1)
    notification_outbox_item_id: str = Field(min_length=1)
    target_reference_id: str = Field(min_length=1)
    source_ambiguity_evidence_reference_id: str = Field(min_length=1)
    idempotency_key: IdempotencyKey
    idempotency_scope: IdempotencyScope
    fingerprint: IdempotencyFingerprint
    duplicate_effect_guard_reference_id: str = Field(min_length=1)
    reconciliation_policy_reference_id: str = Field(min_length=1)
    state: MaxReconciliationState
    reconciliation_still_required: bool
    reconciliation_evidence_reference_id: str | None = Field(default=None, min_length=1)
    resolved_provider_effect_reference_id: str | None = Field(default=None, min_length=1)
    resolved_no_effect_reference_id: str | None = Field(default=None, min_length=1)
    remaining_ambiguity_evidence_reference_id: str | None = Field(default=None, min_length=1)
    subscription_degradation_reference_id: str | None = Field(default=None, min_length=1)
    manual_review_reference_id: str | None = Field(default=None, min_length=1)
    retry_recommendation: MaxRetryRecommendation
    notification_retry_policy_reference_id: str | None = Field(default=None, min_length=1)
    correlation_id: str = Field(min_length=1)
    causation_id: str = Field(min_length=1)
    reason_code: str = Field(min_length=1)
    blind_retry_authority: Literal[False] = False
    duplicate_user_visible_effect_authority: Literal[False] = False
    reconciliation_record_committed: Literal[True] = True
    unknown_effect_success_authority: Literal[False] = False
    unknown_effect_failure_authority: Literal[False] = False
    generic_delivery_success_authority: Literal[False] = False
    generic_delivery_failure_authority: Literal[False] = False
    notification_outbox_authority: Literal[False] = False
    notification_attempt_mutation_authority: Literal[False] = False
    notification_delivery_lifecycle_authority: Literal[False] = False
    notification_retry_authority: Literal[False] = False
    retry_execution_authority: Literal[False] = False
    reconciliation_execution_authority: Literal[False] = False
    provider_call_authority: Literal[False] = False
    provider_payload_retained: Literal[False] = False
    secret_material_present: Literal[False] = False
    human_read_proven: Literal[False] = False
    business_success_proven: Literal[False] = False

    @model_validator(mode="after")
    def _validate_reconciliation(self) -> "MaxReconciliationRecord":
        outcome = self.provider_outcome
        if outcome.state is not MaxProviderOutcomeState.AMBIGUOUS:
            raise ValueError("reconciliation requires AMBIGUOUS provider outcome")
        if outcome.notification_outcome_class not in {"DISPATCH_AMBIGUOUS", "DELIVERY_AMBIGUOUS"}:
            raise ValueError("reconciliation requires an ambiguous notification outcome class")
        if not outcome.reconciliation_required:
            raise ValueError("reconciliation requires reconciliation-required provider outcome")
        if outcome.retry_recommendation is not MaxRetryRecommendation.RECONCILE_FIRST:
            raise ValueError("reconciliation requires reconcile-first provider recommendation")
        if outcome.ambiguity_evidence_reference_id is None:
            raise ValueError("reconciliation requires source ambiguity evidence")
        if not outcome.adapter_outcome_committed:
            raise ValueError("reconciliation requires committed provider outcome")

        references = {
            "max_provider_outcome_id": (self.max_provider_outcome_id, outcome.max_provider_outcome_id),
            "max_outbound_request_id": (self.max_outbound_request_id, outcome.max_outbound_request_id),
            "notification_attempt_id": (self.notification_attempt_id, outcome.notification_attempt_id),
            "notification_outbox_item_id": (self.notification_outbox_item_id, outcome.notification_outbox_item_id),
            "target_reference_id": (self.target_reference_id, outcome.target_reference_id),
            "source_ambiguity_evidence_reference_id": (self.source_ambiguity_evidence_reference_id, outcome.ambiguity_evidence_reference_id),
            "idempotency_key": (self.idempotency_key, outcome.outbound_request.idempotency_key),
            "idempotency_scope": (self.idempotency_scope, outcome.outbound_request.idempotency_scope),
            "fingerprint": (self.fingerprint, outcome.outbound_request.fingerprint),
            "correlation_id": (self.correlation_id, outcome.correlation_id),
            "causation_id": (self.causation_id, outcome.causation_id),
        }
        for field, (value, expected) in references.items():
            if value != expected:
                raise ValueError(f"{field} must match provider outcome")

        if self.reconciliation_evidence_reference_id is None:
            raise ValueError("reconciliation requires evidence reference")
        state_references = {
            "resolved_provider_effect_reference_id": self.resolved_provider_effect_reference_id,
            "resolved_no_effect_reference_id": self.resolved_no_effect_reference_id,
            "remaining_ambiguity_evidence_reference_id": self.remaining_ambiguity_evidence_reference_id,
            "subscription_degradation_reference_id": self.subscription_degradation_reference_id,
            "manual_review_reference_id": self.manual_review_reference_id,
        }
        allowed = {
            MaxReconciliationState.RESOLVED_NO_EFFECT: {"resolved_no_effect_reference_id"},
            MaxReconciliationState.RESOLVED_EFFECT: {"resolved_provider_effect_reference_id"},
            MaxReconciliationState.REMAINS_AMBIGUOUS: {"remaining_ambiguity_evidence_reference_id"},
            MaxReconciliationState.SUBSCRIPTION_DEGRADED: {"remaining_ambiguity_evidence_reference_id", "subscription_degradation_reference_id"},
            MaxReconciliationState.MANUAL_REVIEW_REQUIRED: {"remaining_ambiguity_evidence_reference_id", "manual_review_reference_id"},
        }[self.state]
        present = {name for name, value in state_references.items() if value is not None}
        if present != allowed:
            raise ValueError("state-specific reconciliation evidence is invalid")

        if self.retry_recommendation is MaxRetryRecommendation.RETRY_ONLY_UNDER_NOTIFICATION_POLICY:
            if self.notification_retry_policy_reference_id is None:
                raise ValueError("policy retry requires Notification retry policy reference")
        elif self.notification_retry_policy_reference_id is not None:
            raise ValueError("Notification retry policy reference requires policy retry")

        if self.state is MaxReconciliationState.RESOLVED_NO_EFFECT:
            if self.reconciliation_still_required or self.retry_recommendation is not MaxRetryRecommendation.RETRY_ONLY_UNDER_NOTIFICATION_POLICY:
                raise ValueError("invalid RESOLVED_NO_EFFECT reconciliation matrix")
        elif self.state is MaxReconciliationState.RESOLVED_EFFECT:
            if self.reconciliation_still_required or self.retry_recommendation is not MaxRetryRecommendation.DO_NOT_RETRY:
                raise ValueError("invalid RESOLVED_EFFECT reconciliation matrix")
        elif self.state is MaxReconciliationState.REMAINS_AMBIGUOUS:
            if not self.reconciliation_still_required or self.retry_recommendation is not MaxRetryRecommendation.RECONCILE_FIRST:
                raise ValueError("invalid REMAINS_AMBIGUOUS reconciliation matrix")
        elif self.state is MaxReconciliationState.SUBSCRIPTION_DEGRADED:
            if not self.reconciliation_still_required or self.retry_recommendation is not MaxRetryRecommendation.RECONCILE_FIRST:
                raise ValueError("invalid SUBSCRIPTION_DEGRADED reconciliation matrix")
        elif self.state is MaxReconciliationState.MANUAL_REVIEW_REQUIRED:
            if not self.reconciliation_still_required or self.retry_recommendation is not MaxRetryRecommendation.DO_NOT_RETRY:
                raise ValueError("invalid MANUAL_REVIEW_REQUIRED reconciliation matrix")
        return self


class MaxAdapterReadModel(_MaxContract):
    max_adapter_read_model_id: str = Field(min_length=1)
    metadata: ContractMetadata
    projection_audience: Literal["SUPPORT", "ADMIN", "USER"]
    projection_policy_reference_id: str = Field(min_length=1)
    authorization_evidence_reference_id: str = Field(min_length=1)
    provider_scope_reference_id: str = Field(min_length=1)
    max_bot_ref: str = Field(min_length=1)
    provenance_reference_ids: tuple[str, ...] = Field(min_length=1)
    safe_diagnostic_reference_ids: tuple[str, ...] = Field(min_length=1)
    correlation_id: str = Field(min_length=1)
    causation_id: str | None = Field(default=None, min_length=1)
    max_provider_identity_ref: str | None = Field(default=None, min_length=1)
    max_eligibility_evidence_reference_id: str | None = Field(default=None, min_length=1)
    eligibility_state: MaxEligibilityState | None = None
    max_update_intake_record_id: str | None = Field(default=None, min_length=1)
    update_intake_state: MaxUpdateIntakeState | None = None
    update_source_kind: MaxUpdateSourceKind | None = None
    update_structural_classification: MaxUpdateStructuralClass | None = None
    max_update_deduplication_record_id: str | None = Field(default=None, min_length=1)
    update_deduplication_state: MaxUpdateDeduplicationState | None = None
    max_command_envelope_id: str | None = Field(default=None, min_length=1)
    command_normalization_state: MaxCommandNormalizationState | None = None
    command_surface_kind: MaxCommandSurfaceKind | None = None
    max_contact_validation_result_id: str | None = Field(default=None, min_length=1)
    contact_validation_state: MaxContactValidationState | None = None
    max_mini_app_validation_result_id: str | None = Field(default=None, min_length=1)
    mini_app_validation_state: MaxMiniAppValidationState | None = None
    max_outbound_request_id: str | None = Field(default=None, min_length=1)
    outbound_request_state: MaxOutboundRequestState | None = None
    max_provider_outcome_id: str | None = Field(default=None, min_length=1)
    provider_outcome_state: MaxProviderOutcomeState | None = None
    max_reconciliation_record_id: str | None = Field(default=None, min_length=1)
    reconciliation_state: MaxReconciliationState | None = None
    latency_evidence_reference_id: str | None = Field(default=None, min_length=1)
    safe_reason_codes: tuple[str, ...] = Field(min_length=1)
    redacted_provider_reference_ids: tuple[str, ...] = Field(default_factory=tuple)
    raw_provider_payload_included: Literal[False] = False
    secret_material_included: Literal[False] = False
    phone_or_contact_included: Literal[False] = False
    mutation_authority: Literal[False] = False
    safe_projection_committed: Literal[True] = True
    references_are_opaque: Literal[True] = True
    provider_identifiers_redacted: Literal[True] = True
    authorization_decision_authority: Literal[False] = False
    identity_link_authority: Literal[False] = False
    account_merge_authority: Literal[False] = False
    generic_notification_state_authority: Literal[False] = False
    notification_retry_authority: Literal[False] = False
    provider_call_authority: Literal[False] = False
    retry_execution_authority: Literal[False] = False
    reconciliation_execution_authority: Literal[False] = False
    support_admin_work_authority: Literal[False] = False
    support_ui_authority: Literal[False] = False
    admin_ui_authority: Literal[False] = False
    web_ui_authority: Literal[False] = False
    raw_web_app_data_included: Literal[False] = False
    webhook_secret_included: Literal[False] = False
    private_key_included: Literal[False] = False
    legal_or_personal_document_included: Literal[False] = False
    unnecessary_personal_data_included: Literal[False] = False
    private_message_content_included: Literal[False] = False
    group_channel_member_inventory_included: Literal[False] = False
    provider_display_name_included: Literal[False] = False
    provider_username_included: Literal[False] = False
    provider_avatar_included: Literal[False] = False
    chat_title_included: Literal[False] = False
    retention_policy_defined_here: Literal[False] = False

    @model_validator(mode="after")
    def _validate_safe_projection(self) -> "MaxAdapterReadModel":
        tuples = {
            "provenance_reference_ids": self.provenance_reference_ids,
            "safe_diagnostic_reference_ids": self.safe_diagnostic_reference_ids,
            "safe_reason_codes": self.safe_reason_codes,
            "redacted_provider_reference_ids": self.redacted_provider_reference_ids,
        }
        for name, values in tuples.items():
            if any(not value.strip() for value in values):
                raise ValueError(f"{name} cannot contain blank values")
            if len(values) != len(set(values)):
                raise ValueError(f"{name} cannot contain duplicate values")

        pairs = {
            "eligibility": (self.max_eligibility_evidence_reference_id, self.eligibility_state),
            "deduplication": (self.max_update_deduplication_record_id, self.update_deduplication_state),
            "contact": (self.max_contact_validation_result_id, self.contact_validation_state),
            "mini_app": (self.max_mini_app_validation_result_id, self.mini_app_validation_state),
            "outbound": (self.max_outbound_request_id, self.outbound_request_state),
            "provider_outcome": (self.max_provider_outcome_id, self.provider_outcome_state),
            "reconciliation": (self.max_reconciliation_record_id, self.reconciliation_state),
        }
        for name, values in pairs.items():
            if (values[0] is None) != (values[1] is None):
                raise ValueError(f"{name} projection must be all-or-none")

        intake = (
            self.max_update_intake_record_id,
            self.update_intake_state,
            self.update_source_kind,
            self.update_structural_classification,
        )
        if any(value is not None for value in intake) and not all(value is not None for value in intake):
            raise ValueError("intake projection must be all-or-none")

        command = (self.max_command_envelope_id, self.command_normalization_state, self.command_surface_kind)
        if any(value is not None for value in command) and not all(value is not None for value in command):
            raise ValueError("command projection must be all-or-none")

        has_intake = all(value is not None for value in intake)
        has_dedup = all(value is not None for value in pairs["deduplication"])
        has_command = all(value is not None for value in command)
        has_outbound = all(value is not None for value in pairs["outbound"])
        has_outcome = all(value is not None for value in pairs["provider_outcome"])
        has_reconciliation = all(value is not None for value in pairs["reconciliation"])
        if has_dedup and not has_intake:
            raise ValueError("deduplication projection requires intake projection")
        if has_command and (not has_intake or not has_dedup):
            raise ValueError("command projection requires intake and deduplication projections")
        if has_outcome and not has_outbound:
            raise ValueError("provider outcome projection requires outbound projection")
        if has_reconciliation and not has_outcome:
            raise ValueError("reconciliation projection requires provider outcome projection")
        if has_reconciliation and not has_outbound:
            raise ValueError("reconciliation projection requires outbound projection")

        sources = (
            self.max_provider_identity_ref,
            self.max_eligibility_evidence_reference_id,
            self.max_update_intake_record_id,
            self.max_update_deduplication_record_id,
            self.max_command_envelope_id,
            self.max_contact_validation_result_id,
            self.max_mini_app_validation_result_id,
            self.max_outbound_request_id,
            self.max_provider_outcome_id,
            self.max_reconciliation_record_id,
        )
        if not any(source is not None for source in sources):
            raise ValueError("read projection requires at least one source reference")
        return self


__all__ = [
    "MaxAccountLinkReference",
    "MaxAdapterReadModel",
    "MaxCommandEnvelope",
    "MaxCommandNormalizationState",
    "MaxCommandSourceKind",
    "MaxCommandSurfaceKind",
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
    "MaxUpdateAdmissionState",
    "MaxUpdateSourceKind",
    "MaxUpdateStructuralClass",
]
