"""Transport-neutral semantic contracts for Telegram identity handoff."""

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


class _TelegramContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


class TelegramIdentityResolutionState(str, Enum):
    RESOLVED_ACCOUNT = "RESOLVED_ACCOUNT"
    NEW_ACCOUNT_REQUESTED = "NEW_ACCOUNT_REQUESTED"
    LINK_CHALLENGE_REQUIRED = "LINK_CHALLENGE_REQUIRED"
    REJECTED = "REJECTED"
    AMBIGUOUS = "AMBIGUOUS"


class TelegramProviderIdentity(_TelegramContract):
    """External Telegram identifiers; none is internal account authority."""

    telegram_provider_identity_ref: str = Field(min_length=1)
    telegram_bot_ref: str = Field(min_length=1)
    telegram_user_id: str = Field(min_length=1)
    telegram_chat_id: str | None = Field(default=None, min_length=1)


class VerifiedTelegramIdentityEvidence(_TelegramContract):
    """Safe evidence references, never a Telegram update or provider payload."""

    verified_identity_evidence_ref: str = Field(min_length=1)
    provider_identity: TelegramProviderIdentity
    verification_method_ref: str = Field(min_length=1)
    verification_result_ref: str = Field(min_length=1)


class TelegramAccountLinkReference(_TelegramContract):
    """Telegram-owned reference to an already accepted Identity decision."""

    telegram_account_link_reference_id: str = Field(min_length=1)
    provider_identity: TelegramProviderIdentity
    account_id: str = Field(min_length=1)
    identity_account_reference_id: str = Field(min_length=1)
    identity_provider_identity_id: str = Field(min_length=1)
    identity_provider: Literal["TELEGRAM"] = "TELEGRAM"

    @model_validator(mode="after")
    def _provider_identity_matches(self) -> "TelegramAccountLinkReference":
        if self.identity_provider_identity_id != self.provider_identity.telegram_user_id:
            raise ValueError("identity_provider_identity_id must match telegram_user_id")
        return self


class TelegramIdentityResolutionRequest(_TelegramContract):
    """Idempotent request reference for Identity-owned resolution."""

    telegram_identity_resolution_request_id: str = Field(min_length=1)
    metadata: ContractMetadata
    idempotency_key: IdempotencyKey
    idempotency_scope: IdempotencyScope
    fingerprint: IdempotencyFingerprint
    verified_identity_evidence: VerifiedTelegramIdentityEvidence
    identity_resolution_contract_ref: str = Field(min_length=1)


class TelegramIdentityResolutionOutcome(_TelegramContract):
    """Safe outcome projection; account decisions remain Identity-owned."""

    telegram_identity_resolution_reference_id: str = Field(min_length=1)
    telegram_identity_resolution_request_id: str = Field(min_length=1)
    identity_decision_reference_id: str = Field(min_length=1)
    state: TelegramIdentityResolutionState
    provider_identity: TelegramProviderIdentity
    reason_code: str = Field(min_length=1)
    account_link: TelegramAccountLinkReference | None = None
    identity_link_challenge_ref: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def _validate_state_matrix(self) -> "TelegramIdentityResolutionOutcome":
        if self.state is TelegramIdentityResolutionState.RESOLVED_ACCOUNT:
            if self.account_link is None or self.identity_link_challenge_ref is not None:
                raise ValueError("resolved account requires only account_link")
            if self.provider_identity != self.account_link.provider_identity:
                raise ValueError("provider_identity must match account_link")
        elif self.state is TelegramIdentityResolutionState.LINK_CHALLENGE_REQUIRED:
            if self.identity_link_challenge_ref is None or self.account_link is not None:
                raise ValueError("link challenge requires only challenge reference")
        elif self.account_link is not None or self.identity_link_challenge_ref is not None:
            raise ValueError("this outcome state cannot contain account or challenge reference")
        return self


class TelegramProviderUpdateIdentity(_TelegramContract):
    """Opaque provider-scope identity for one Telegram update."""

    telegram_provider_update_ref: str = Field(min_length=1)
    telegram_bot_ref: str = Field(min_length=1)
    telegram_update_id: str = Field(min_length=1)
    provider_update_type_ref: str = Field(min_length=1)


class TelegramUpdateAdmissionState(str, Enum):
    VERIFIED = "VERIFIED"
    NOT_VERIFIED = "NOT_VERIFIED"
    REJECTED = "REJECTED"
    AMBIGUOUS = "AMBIGUOUS"


class TelegramUpdateStructuralClass(str, Enum):
    SUPPORTED_CANDIDATE = "SUPPORTED_CANDIDATE"
    UNSUPPORTED = "UNSUPPORTED"
    MALFORMED = "MALFORMED"
    AMBIGUOUS = "AMBIGUOUS"


class TelegramUpdateIntakeState(str, Enum):
    ACCEPTED_FOR_NORMALIZATION = "ACCEPTED_FOR_NORMALIZATION"
    IGNORED_UNSUPPORTED = "IGNORED_UNSUPPORTED"
    REJECTED_UNTRUSTED = "REJECTED_UNTRUSTED"
    REJECTED_MALFORMED = "REJECTED_MALFORMED"
    AMBIGUOUS = "AMBIGUOUS"


class TelegramUpdateDeduplicationState(str, Enum):
    NEW_UPDATE = "NEW_UPDATE"
    DUPLICATE_REPLAY = "DUPLICATE_REPLAY"
    FINGERPRINT_CONFLICT = "FINGERPRINT_CONFLICT"
    AMBIGUOUS = "AMBIGUOUS"


class TelegramUpdateIntakeRecord(_TelegramContract):
    telegram_update_intake_record_id: str = Field(min_length=1)
    metadata: ContractMetadata
    provider_update_identity: TelegramProviderUpdateIdentity
    provider_identity: TelegramProviderIdentity | None = None
    idempotency_key: IdempotencyKey
    idempotency_scope: IdempotencyScope
    fingerprint: IdempotencyFingerprint
    admission_state: TelegramUpdateAdmissionState
    structural_classification: TelegramUpdateStructuralClass
    intake_state: TelegramUpdateIntakeState
    provider_admission_evidence_ref: str | None = Field(default=None, min_length=1)
    normalization_reference_id: str | None = Field(default=None, min_length=1)
    reason_code: str = Field(min_length=1)
    business_dispatch_authorized: Literal[False] = False

    @model_validator(mode="after")
    def _validate_intake_matrix(self) -> "TelegramUpdateIntakeRecord":
        if self.provider_identity is not None and (
            self.provider_identity.telegram_bot_ref
            != self.provider_update_identity.telegram_bot_ref
        ):
            raise ValueError("provider_identity telegram_bot_ref must match update identity")

        if self.intake_state is TelegramUpdateIntakeState.ACCEPTED_FOR_NORMALIZATION:
            if self.admission_state is not TelegramUpdateAdmissionState.VERIFIED:
                raise ValueError("accepted intake requires verified admission")
            if (
                self.structural_classification
                is not TelegramUpdateStructuralClass.SUPPORTED_CANDIDATE
            ):
                raise ValueError("accepted intake requires supported candidate structure")
            if not self.provider_admission_evidence_ref or not self.normalization_reference_id:
                raise ValueError("accepted intake requires admission and normalization references")
        elif self.intake_state is TelegramUpdateIntakeState.IGNORED_UNSUPPORTED:
            if self.structural_classification is not TelegramUpdateStructuralClass.UNSUPPORTED:
                raise ValueError("ignored intake requires unsupported structure")
        elif self.intake_state is TelegramUpdateIntakeState.REJECTED_UNTRUSTED:
            if self.admission_state not in {
                TelegramUpdateAdmissionState.NOT_VERIFIED,
                TelegramUpdateAdmissionState.REJECTED,
            }:
                raise ValueError("untrusted rejection requires failed admission")
        elif self.intake_state is TelegramUpdateIntakeState.REJECTED_MALFORMED:
            if self.structural_classification is not TelegramUpdateStructuralClass.MALFORMED:
                raise ValueError("malformed rejection requires malformed structure")
        elif self.admission_state is not TelegramUpdateAdmissionState.AMBIGUOUS and (
            self.structural_classification is not TelegramUpdateStructuralClass.AMBIGUOUS
        ):
            raise ValueError("ambiguous intake requires ambiguous admission or structure")

        if self.intake_state is not TelegramUpdateIntakeState.ACCEPTED_FOR_NORMALIZATION:
            if self.normalization_reference_id is not None:
                raise ValueError("only accepted intake may have normalization reference")
        return self


class TelegramUpdateDeduplicationRecord(_TelegramContract):
    telegram_update_deduplication_record_id: str = Field(min_length=1)
    metadata: ContractMetadata
    provider_update_identity: TelegramProviderUpdateIdentity
    idempotency_key: IdempotencyKey
    idempotency_scope: IdempotencyScope
    fingerprint: IdempotencyFingerprint
    state: TelegramUpdateDeduplicationState
    current_intake_record_id: str = Field(min_length=1)
    existing_intake_record_id: str | None = Field(default=None, min_length=1)
    existing_fingerprint: IdempotencyFingerprint | None = None
    replayed_adapter_outcome_ref: str | None = Field(default=None, min_length=1)
    adapter_processing_authorized: bool
    second_business_effect_authorized: Literal[False] = False
    reason_code: str = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_dedup_matrix(self) -> "TelegramUpdateDeduplicationRecord":
        if self.state is TelegramUpdateDeduplicationState.NEW_UPDATE:
            if any(
                (
                    self.existing_intake_record_id,
                    self.existing_fingerprint,
                    self.replayed_adapter_outcome_ref,
                )
            ):
                raise ValueError("new update cannot reference an existing outcome")
            if not self.adapter_processing_authorized:
                raise ValueError("new update authorizes adapter processing")
        elif self.state is TelegramUpdateDeduplicationState.DUPLICATE_REPLAY:
            if not self.existing_intake_record_id or self.existing_fingerprint is None:
                raise ValueError("duplicate replay requires existing intake and fingerprint")
            if self.existing_fingerprint != self.fingerprint:
                raise ValueError("duplicate replay requires matching fingerprint")
            if not self.replayed_adapter_outcome_ref or self.adapter_processing_authorized:
                raise ValueError("duplicate replay requires safe outcome replay only")
        elif self.state is TelegramUpdateDeduplicationState.FINGERPRINT_CONFLICT:
            if not self.existing_intake_record_id or self.existing_fingerprint is None:
                raise ValueError("fingerprint conflict requires existing intake and fingerprint")
            if self.existing_fingerprint == self.fingerprint:
                raise ValueError("fingerprint conflict requires different fingerprint")
            if self.replayed_adapter_outcome_ref or self.adapter_processing_authorized:
                raise ValueError("fingerprint conflict cannot authorize processing or replay")
        else:
            if not self.existing_intake_record_id or self.existing_fingerprint is None:
                raise ValueError("ambiguous deduplication requires existing intake and fingerprint")
            if self.replayed_adapter_outcome_ref or self.adapter_processing_authorized:
                raise ValueError("ambiguous deduplication cannot authorize processing or replay")
        return self


class TelegramInboundInputKind(str, Enum):
    COMMAND_CANDIDATE = "COMMAND_CANDIDATE"
    MESSAGE_TEXT_CANDIDATE = "MESSAGE_TEXT_CANDIDATE"
    SOURCE_URL_CANDIDATE = "SOURCE_URL_CANDIDATE"
    UNSUPPORTED_INPUT = "UNSUPPORTED_INPUT"
    AMBIGUOUS_INPUT = "AMBIGUOUS_INPUT"


class TelegramIntentFamily(str, Enum):
    START_OR_LINK_TELEGRAM = "START_OR_LINK_TELEGRAM"
    HELP_REQUESTED = "HELP_REQUESTED"
    LIST_MY_BEACONS_REQUESTED = "LIST_MY_BEACONS_REQUESTED"
    BEACON_STATUS_REQUESTED = "BEACON_STATUS_REQUESTED"
    CREATE_BEACON_FROM_SOURCE_URL_REQUESTED = "CREATE_BEACON_FROM_SOURCE_URL_REQUESTED"
    BEACON_SETTINGS_REQUESTED = "BEACON_SETTINGS_REQUESTED"
    UPDATE_BEACON_INTERVAL_OR_STATUS_PREF_REQUESTED = "UPDATE_BEACON_INTERVAL_OR_STATUS_PREF_REQUESTED"  # noqa: E501
    PAUSE_BEACON_REQUESTED = "PAUSE_BEACON_REQUESTED"
    RESUME_BEACON_REQUESTED = "RESUME_BEACON_REQUESTED"
    DELETE_BEACON_REQUESTED_WITH_CONFIRMATION = "DELETE_BEACON_REQUESTED_WITH_CONFIRMATION"
    TARIFF_OR_LIMITS_REQUESTED = "TARIFF_OR_LIMITS_REQUESTED"
    OPEN_FULL_LISTING_RESULT_REQUESTED = "OPEN_FULL_LISTING_RESULT_REQUESTED"
    TOGGLE_NO_NEW_STATUS_NOTIFICATION_REQUESTED = "TOGGLE_NO_NEW_STATUS_NOTIFICATION_REQUESTED"
    UNSUPPORTED_OR_AMBIGUOUS_INPUT = "UNSUPPORTED_OR_AMBIGUOUS_INPUT"


class TelegramIntentNormalizationState(str, Enum):
    NORMALIZED = "NORMALIZED"
    UNSUPPORTED = "UNSUPPORTED"
    AMBIGUOUS = "AMBIGUOUS"
    BLOCKED = "BLOCKED"


class TelegramIntentOwnerBoundary(str, Enum):
    TELEGRAM_ADAPTER = "TELEGRAM_ADAPTER"
    IDENTITY_AND_ACCESS = "IDENTITY_AND_ACCESS"
    BEACON_MANAGEMENT = "BEACON_MANAGEMENT"
    NOTIFICATION_DELIVERY = "NOTIFICATION_DELIVERY"
    ENTITLEMENTS_AND_BILLING = "ENTITLEMENTS_AND_BILLING"
    NONE = "NONE"


_INTENT_OWNER_BOUNDARIES: dict[TelegramIntentFamily, tuple[TelegramIntentOwnerBoundary, ...]] = {
    TelegramIntentFamily.START_OR_LINK_TELEGRAM: (TelegramIntentOwnerBoundary.IDENTITY_AND_ACCESS,),
    TelegramIntentFamily.HELP_REQUESTED: (TelegramIntentOwnerBoundary.TELEGRAM_ADAPTER,),
    TelegramIntentFamily.LIST_MY_BEACONS_REQUESTED: (TelegramIntentOwnerBoundary.BEACON_MANAGEMENT,),  # noqa: E501
    TelegramIntentFamily.BEACON_STATUS_REQUESTED: (TelegramIntentOwnerBoundary.BEACON_MANAGEMENT,),
    TelegramIntentFamily.CREATE_BEACON_FROM_SOURCE_URL_REQUESTED: (TelegramIntentOwnerBoundary.BEACON_MANAGEMENT,),  # noqa: E501
    TelegramIntentFamily.BEACON_SETTINGS_REQUESTED: (TelegramIntentOwnerBoundary.BEACON_MANAGEMENT,),  # noqa: E501
    TelegramIntentFamily.UPDATE_BEACON_INTERVAL_OR_STATUS_PREF_REQUESTED: (
        TelegramIntentOwnerBoundary.BEACON_MANAGEMENT,
        TelegramIntentOwnerBoundary.NOTIFICATION_DELIVERY,
    ),
    TelegramIntentFamily.PAUSE_BEACON_REQUESTED: (TelegramIntentOwnerBoundary.BEACON_MANAGEMENT,),
    TelegramIntentFamily.RESUME_BEACON_REQUESTED: (TelegramIntentOwnerBoundary.BEACON_MANAGEMENT,),
    TelegramIntentFamily.DELETE_BEACON_REQUESTED_WITH_CONFIRMATION: (TelegramIntentOwnerBoundary.BEACON_MANAGEMENT,),  # noqa: E501
    TelegramIntentFamily.TARIFF_OR_LIMITS_REQUESTED: (TelegramIntentOwnerBoundary.ENTITLEMENTS_AND_BILLING,),  # noqa: E501
    TelegramIntentFamily.OPEN_FULL_LISTING_RESULT_REQUESTED: (TelegramIntentOwnerBoundary.NOTIFICATION_DELIVERY,),  # noqa: E501
    TelegramIntentFamily.TOGGLE_NO_NEW_STATUS_NOTIFICATION_REQUESTED: (TelegramIntentOwnerBoundary.NOTIFICATION_DELIVERY,),  # noqa: E501
    TelegramIntentFamily.UNSUPPORTED_OR_AMBIGUOUS_INPUT: (TelegramIntentOwnerBoundary.NONE,),
}


class TelegramUntrustedInputReference(_TelegramContract):
    telegram_untrusted_input_reference_id: str = Field(min_length=1)
    provider_update_identity: TelegramProviderUpdateIdentity
    input_kind: TelegramInboundInputKind
    input_evidence_reference_id: str = Field(min_length=1)
    candidate_source_url_reference_id: str | None = Field(default=None, min_length=1)
    raw_provider_payload_present: Literal[False] = False
    input_text_retained: Literal[False] = False
    input_trusted: Literal[False] = False
    input_is_authorization: Literal[False] = False
    candidate_source_url_validated: Literal[False] = False

    @model_validator(mode="after")
    def _validate_candidate_reference(self) -> "TelegramUntrustedInputReference":
        if self.input_kind is TelegramInboundInputKind.SOURCE_URL_CANDIDATE:
            if self.candidate_source_url_reference_id is None:
                raise ValueError("source URL candidate requires an opaque reference")
        elif self.candidate_source_url_reference_id is not None:
            raise ValueError("only source URL candidates may carry a candidate reference")
        return self


class TelegramIntentNormalizationRequest(_TelegramContract):
    telegram_intent_normalization_request_id: str = Field(min_length=1)
    metadata: ContractMetadata
    intake_record: TelegramUpdateIntakeRecord
    deduplication_record: TelegramUpdateDeduplicationRecord
    untrusted_input: TelegramUntrustedInputReference
    normalization_policy_reference_id: str = Field(min_length=1)
    business_dispatch_authorized: Literal[False] = False
    handler_execution_authorized: Literal[False] = False
    conversation_state_machine_authorized: Literal[False] = False

    @model_validator(mode="after")
    def _validate_prerequisites(self) -> "TelegramIntentNormalizationRequest":
        intake = self.intake_record
        dedup = self.deduplication_record
        update = intake.provider_update_identity
        if intake.intake_state is not TelegramUpdateIntakeState.ACCEPTED_FOR_NORMALIZATION:
            raise ValueError("normalization requires accepted intake")
        if intake.admission_state is not TelegramUpdateAdmissionState.VERIFIED:
            raise ValueError("normalization requires verified admission")
        if intake.structural_classification is not TelegramUpdateStructuralClass.SUPPORTED_CANDIDATE:  # noqa: E501
            raise ValueError("normalization requires supported candidate")
        if intake.provider_identity is None:
            raise ValueError("normalization requires provider identity")
        if intake.normalization_reference_id != self.telegram_intent_normalization_request_id:
            raise ValueError("normalization reference must match request id")
        if dedup.state is not TelegramUpdateDeduplicationState.NEW_UPDATE or not dedup.adapter_processing_authorized:  # noqa: E501
            raise ValueError("normalization requires a new update authorized for adapter processing")  # noqa: E501
        if dedup.current_intake_record_id != intake.telegram_update_intake_record_id:
            raise ValueError("deduplication must point at current intake")
        if not (
            update == dedup.provider_update_identity
            and intake.idempotency_key == dedup.idempotency_key
            and intake.idempotency_scope == dedup.idempotency_scope
            and intake.fingerprint == dedup.fingerprint
            and self.untrusted_input.provider_update_identity == update
            and intake.provider_identity.telegram_bot_ref == update.telegram_bot_ref
        ):
            raise ValueError("intake, deduplication and input identity must agree")
        return self


class TelegramCommandEnvelope(_TelegramContract):
    telegram_command_envelope_id: str = Field(min_length=1)
    metadata: ContractMetadata
    normalization_request: TelegramIntentNormalizationRequest
    state: TelegramIntentNormalizationState
    intent_family: TelegramIntentFamily
    owner_boundaries: tuple[TelegramIntentOwnerBoundary, ...]
    owner_contract_reference_ids: tuple[str, ...]
    candidate_source_url_reference_id: str | None = Field(default=None, min_length=1)
    blocking_decision_reference_id: str | None = Field(default=None, min_length=1)
    dangerous_action_confirmation_required: bool
    reason_code: str = Field(min_length=1)
    exact_command_catalog_selected: Literal[False] = False
    command_handler_authorized: Literal[False] = False
    conversation_state_machine_authorized: Literal[False] = False
    business_dispatch_authorized: Literal[False] = False
    account_creation_authorized: Literal[False] = False
    beacon_creation_or_mutation_authorized: Literal[False] = False
    source_url_business_validation_authorized: Literal[False] = False
    notification_preference_mutation_authorized: Literal[False] = False
    entitlement_mutation_authorized: Literal[False] = False
    provider_runtime_authorized: Literal[False] = False

    @model_validator(mode="after")
    def _validate_envelope_matrix(self) -> "TelegramCommandEnvelope":
        family = self.intent_family
        input_kind = self.normalization_request.untrusted_input.input_kind
        expected = _INTENT_OWNER_BOUNDARIES[family]
        if self.state in {TelegramIntentNormalizationState.UNSUPPORTED, TelegramIntentNormalizationState.AMBIGUOUS}:  # noqa: E501
            expected_family = TelegramIntentFamily.UNSUPPORTED_OR_AMBIGUOUS_INPUT
            expected_kind = (TelegramInboundInputKind.UNSUPPORTED_INPUT if self.state is TelegramIntentNormalizationState.UNSUPPORTED else TelegramInboundInputKind.AMBIGUOUS_INPUT)  # noqa: E501
            if family is not expected_family or input_kind is not expected_kind or self.owner_boundaries != (TelegramIntentOwnerBoundary.NONE,) or self.owner_contract_reference_ids or self.candidate_source_url_reference_id is not None or self.blocking_decision_reference_id is not None or self.dangerous_action_confirmation_required:  # noqa: E501
                raise ValueError("unsupported and ambiguous envelope matrix is exact")
            return self
        if family is TelegramIntentFamily.UNSUPPORTED_OR_AMBIGUOUS_INPUT or input_kind in {TelegramInboundInputKind.UNSUPPORTED_INPUT, TelegramInboundInputKind.AMBIGUOUS_INPUT}:  # noqa: E501
            raise ValueError("supported envelope cannot use unsupported or ambiguous input")
        if self.owner_boundaries != expected or TelegramIntentOwnerBoundary.NONE in self.owner_boundaries:  # noqa: E501
            raise ValueError("owner boundaries do not match intent family")
        if self.state is TelegramIntentNormalizationState.NORMALIZED:
            if self.blocking_decision_reference_id is not None or len(self.owner_contract_reference_ids) != len(expected) or any(not ref.strip() for ref in self.owner_contract_reference_ids):  # noqa: E501
                raise ValueError("normalized envelope requires owner references and no block")
        elif self.state is TelegramIntentNormalizationState.BLOCKED:
            if not self.blocking_decision_reference_id or self.owner_contract_reference_ids:
                raise ValueError("blocked envelope requires only a blocking reference")
        if family is TelegramIntentFamily.CREATE_BEACON_FROM_SOURCE_URL_REQUESTED:
            if input_kind is not TelegramInboundInputKind.SOURCE_URL_CANDIDATE or self.candidate_source_url_reference_id != self.normalization_request.untrusted_input.candidate_source_url_reference_id:  # noqa: E501
                raise ValueError("create intent requires the exact opaque source reference")
        elif self.candidate_source_url_reference_id is not None:
            raise ValueError("only create intent may carry a source reference")
        if self.dangerous_action_confirmation_required != (family is TelegramIntentFamily.DELETE_BEACON_REQUESTED_WITH_CONFIRMATION):  # noqa: E501
            raise ValueError("only deletion requires confirmation")
        return self


class TelegramProviderMode(str, Enum):
    WEBHOOK = "WEBHOOK"
    GET_UPDATES = "GET_UPDATES"


class TelegramProviderModeBoundaryState(str, Enum):
    UNSELECTED = "UNSELECTED"
    WEBHOOK_CANDIDATE = "WEBHOOK_CANDIDATE"
    GET_UPDATES_CANDIDATE = "GET_UPDATES_CANDIDATE"
    TRANSITION_REQUIRED = "TRANSITION_REQUIRED"
    BLOCKED = "BLOCKED"


class TelegramWebhookModeRequirements(_TelegramContract):
    telegram_webhook_mode_requirements_id: str = Field(min_length=1)
    official_telegram_evidence_ref: str = Field(min_length=1)
    endpoint_ownership_decision_ref: str = Field(min_length=1)
    tls_domain_port_certificate_gate_ref: str = Field(min_length=1)
    secret_token_handling_policy_ref: str = Field(min_length=1)
    authenticity_verification_policy_ref: str = Field(min_length=1)
    durable_acceptance_policy_ref: str = Field(min_length=1)
    duplicate_delivery_idempotency_policy_ref: str = Field(min_length=1)
    failure_response_policy_ref: str = Field(min_length=1)
    drop_pending_transition_policy_ref: str = Field(min_length=1)
    secret_material_present: Literal[False] = False
    http_acknowledgement_is_business_success: Literal[False] = False
    provider_request_authorized: Literal[False] = False


class TelegramGetUpdatesModeRequirements(_TelegramContract):
    telegram_get_updates_mode_requirements_id: str = Field(min_length=1)
    official_telegram_evidence_ref: str = Field(min_length=1)
    allowed_environment_class_decision_ref: str = Field(min_length=1)
    polling_ownership_decision_ref: str = Field(min_length=1)
    scheduler_worker_boundary_ref: str = Field(min_length=1)
    durable_acceptance_policy_ref: str = Field(min_length=1)
    offset_advancement_policy_ref: str = Field(min_length=1)
    interruption_replay_policy_ref: str = Field(min_length=1)
    mode_transition_policy_ref: str = Field(min_length=1)
    drop_pending_policy_ref: str = Field(min_length=1)
    timeout_limit_interval_policy_ref: str = Field(min_length=1)
    process_local_cursor_authoritative: Literal[False] = False
    arrival_is_trusted_without_validation: Literal[False] = False
    offset_advance_before_durable_acceptance_authorized: Literal[False] = False
    provider_request_authorized: Literal[False] = False


class TelegramProviderModeBoundary(_TelegramContract):
    telegram_provider_mode_boundary_id: str = Field(min_length=1)
    metadata: ContractMetadata
    telegram_bot_ref: str = Field(min_length=1)
    environment_ref: str = Field(min_length=1)
    owner_direction_reference_id: str = Field(min_length=1)
    official_telegram_evidence_ref: str = Field(min_length=1)
    state: TelegramProviderModeBoundaryState
    candidate_mode: TelegramProviderMode | None = None
    current_mode: TelegramProviderMode | None = None
    requested_mode: TelegramProviderMode | None = None
    webhook_requirements: TelegramWebhookModeRequirements | None = None
    get_updates_requirements: TelegramGetUpdatesModeRequirements | None = None
    mode_transition_policy_ref: str | None = Field(default=None, min_length=1)
    drop_pending_policy_ref: str | None = Field(default=None, min_length=1)
    blocking_decision_reference_id: str | None = Field(default=None, min_length=1)
    production_staging_target_mode: Literal[TelegramProviderMode.WEBHOOK] = (
        TelegramProviderMode.WEBHOOK
    )
    development_proof_mode_candidate: Literal[TelegramProviderMode.GET_UPDATES] = (
        TelegramProviderMode.GET_UPDATES
    )
    development_proof_requires_explicit_gate: Literal[True] = True
    environment_mode_selected: Literal[False] = False
    simultaneous_modes_authorized: Literal[False] = False
    provider_call_authorized: Literal[False] = False
    provider_runtime_authorized: Literal[False] = False
    reason_code: str = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_state_matrix(self) -> "TelegramProviderModeBoundary":
        if self.webhook_requirements is not None and self.get_updates_requirements is not None:
            raise ValueError("webhook and getUpdates requirements are mutually exclusive")

        state = self.state
        if state in {
            TelegramProviderModeBoundaryState.UNSELECTED,
            TelegramProviderModeBoundaryState.BLOCKED,
        }:
            if any((self.candidate_mode, self.current_mode, self.requested_mode)):
                raise ValueError("this boundary state cannot contain a mode")
            if self.webhook_requirements is not None or self.get_updates_requirements is not None:
                raise ValueError("this boundary state cannot contain requirements")
            if (
                self.mode_transition_policy_ref is not None
                or self.drop_pending_policy_ref is not None
            ):
                raise ValueError("this boundary state cannot contain transition references")
            if state is TelegramProviderModeBoundaryState.UNSELECTED:
                if self.blocking_decision_reference_id is not None:
                    raise ValueError("unselected boundary cannot contain blocking reference")
            elif self.blocking_decision_reference_id is None:
                raise ValueError("blocked boundary requires blocking reference")
            return self

        if self.blocking_decision_reference_id is not None:
            raise ValueError("candidate or transition boundary cannot be blocked")

        if state is TelegramProviderModeBoundaryState.WEBHOOK_CANDIDATE:
            if self.candidate_mode is not TelegramProviderMode.WEBHOOK:
                raise ValueError("webhook candidate requires webhook candidate mode")
            if self.webhook_requirements is None or self.get_updates_requirements is not None:
                raise ValueError("webhook candidate requires only webhook requirements")
            if any(
                (
                    self.current_mode,
                    self.requested_mode,
                    self.mode_transition_policy_ref,
                    self.drop_pending_policy_ref,
                )
            ):
                raise ValueError(
                    "webhook candidate cannot contain current, requested, or transition data"
                )
            if (
                self.official_telegram_evidence_ref
                != self.webhook_requirements.official_telegram_evidence_ref
            ):
                raise ValueError("boundary and webhook evidence references must match")
            return self

        if state is TelegramProviderModeBoundaryState.GET_UPDATES_CANDIDATE:
            if self.candidate_mode is not TelegramProviderMode.GET_UPDATES:
                raise ValueError("getUpdates candidate requires getUpdates candidate mode")
            if self.get_updates_requirements is None or self.webhook_requirements is not None:
                raise ValueError("getUpdates candidate requires only getUpdates requirements")
            if any(
                (
                    self.current_mode,
                    self.requested_mode,
                    self.mode_transition_policy_ref,
                    self.drop_pending_policy_ref,
                )
            ):
                raise ValueError(
                    "getUpdates candidate cannot contain current, requested, or transition data"
                )
            if (
                self.official_telegram_evidence_ref
                != self.get_updates_requirements.official_telegram_evidence_ref
            ):
                raise ValueError("boundary and getUpdates evidence references must match")
            return self

        if state is TelegramProviderModeBoundaryState.TRANSITION_REQUIRED:
            if (
                self.candidate_mode is not None
                or self.current_mode is None
                or self.requested_mode is None
            ):
                raise ValueError("transition requires no candidate and both modes")
            if self.current_mode is self.requested_mode:
                raise ValueError("transition requires different current and requested modes")
            if self.mode_transition_policy_ref is None or self.drop_pending_policy_ref is None:
                raise ValueError("transition requires mode and drop-pending policy references")
            target = self.webhook_requirements or self.get_updates_requirements
            if (
                target is None
                or self.official_telegram_evidence_ref != target.official_telegram_evidence_ref
            ):
                raise ValueError("transition requires evidence for its target requirements")
            if self.requested_mode is TelegramProviderMode.WEBHOOK:
                if self.webhook_requirements is None or self.get_updates_requirements is not None:
                    raise ValueError("webhook transition requires only webhook requirements")
            elif self.get_updates_requirements is None or self.webhook_requirements is not None:
                raise ValueError("getUpdates transition requires only getUpdates requirements")
            return self

        raise ValueError("unsupported provider mode boundary state")


class TelegramExistingBotEvidenceState(str, Enum):
    VERIFIED_REDACTED_EVIDENCE = "VERIFIED_REDACTED_EVIDENCE"
    EVIDENCE_INCOMPLETE = "EVIDENCE_INCOMPLETE"
    EVIDENCE_MISMATCH = "EVIDENCE_MISMATCH"


class TelegramExistingBotMetadata(_TelegramContract):
    telegram_existing_bot_metadata_id: str = Field(min_length=1)
    telegram_bot_username: str = Field(min_length=1)
    telegram_bot_numeric_id: str = Field(min_length=1, pattern=r"^[1-9][0-9]*$")
    owner_provisioning_reference_id: str = Field(min_length=1)
    botfather_creation_completed: Literal[True] = True
    telegram_bot_numeric_id_is_external_provider_identifier: Literal[True] = True
    telegram_bot_numeric_id_is_internal_account_id: Literal[False] = False
    botfather_reconfiguration_authorized: Literal[False] = False


class TelegramProtectedSecretPresenceEvidence(_TelegramContract):
    telegram_protected_secret_presence_evidence_id: str = Field(min_length=1)
    protected_secret_reference: str = Field(min_length=1)
    observed_owner: str = Field(min_length=1)
    observed_group: str = Field(min_length=1)
    observed_mode: str = Field(min_length=1, pattern=r"^0[0-7]{3}$")
    observed_size_bytes: int = Field(gt=0)
    server_evidence_reference_id: str = Field(min_length=1)
    evidence_is_presence_and_metadata_only: Literal[True] = True
    secret_content_read: Literal[False] = False
    secret_content_printed: Literal[False] = False
    secret_content_hashed: Literal[False] = False
    secret_content_fingerprinted: Literal[False] = False
    secret_content_encoded: Literal[False] = False
    secret_content_copied: Literal[False] = False
    secret_content_transmitted: Literal[False] = False
    secret_modified: Literal[False] = False


class TelegramPublicBotMetadataPresenceEvidence(_TelegramContract):
    telegram_public_bot_metadata_presence_evidence_id: str = Field(min_length=1)
    public_metadata_reference: str = Field(min_length=1)
    observed_owner: str = Field(min_length=1)
    observed_group: str = Field(min_length=1)
    observed_mode: str = Field(min_length=1, pattern=r"^0[0-7]{3}$")
    observed_size_bytes: int = Field(gt=0)
    server_evidence_reference_id: str = Field(min_length=1)
    evidence_is_presence_and_metadata_only: Literal[True] = True
    file_content_read: Literal[False] = False
    file_modified: Literal[False] = False


class TelegramExistingBotOperationalGate(_TelegramContract):
    telegram_existing_bot_operational_gate_id: str = Field(min_length=1)
    metadata: ContractMetadata
    owner_direction_reference_id: str = Field(min_length=1)
    state: TelegramExistingBotEvidenceState
    bot_metadata: TelegramExistingBotMetadata | None = None
    protected_secret_presence_evidence: TelegramProtectedSecretPresenceEvidence | None = None
    public_bot_metadata_presence_evidence: TelegramPublicBotMetadataPresenceEvidence | None = None
    blocking_decision_reference_id: str | None = Field(default=None, min_length=1)
    provider_runtime_authorized: Literal[False] = False
    provider_call_authorized: Literal[False] = False
    webhook_authorized: Literal[False] = False
    get_updates_authorized: Literal[False] = False
    mini_app_authorized: Literal[False] = False
    protected_secret_consumption_authorized: Literal[False] = False
    botfather_reconfiguration_authorized: Literal[False] = False
    token_rotation_authorized: Literal[False] = False
    token_revocation_authorized: Literal[False] = False
    token_deletion_authorized: Literal[False] = False
    secret_relocation_authorized: Literal[False] = False
    secret_permission_change_authorized: Literal[False] = False
    reason_code: str = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_state_matrix(self) -> "TelegramExistingBotOperationalGate":
        complete = all(
            (
                self.bot_metadata,
                self.protected_secret_presence_evidence,
                self.public_bot_metadata_presence_evidence,
            )
        )
        if self.state is TelegramExistingBotEvidenceState.EVIDENCE_INCOMPLETE:
            if complete or self.blocking_decision_reference_id is None:
                raise ValueError(
                    "incomplete evidence requires missing evidence and blocking reference"
                )
            return self
        if not complete:
            raise ValueError("verified or mismatched evidence requires all evidence objects")
        bot = self.bot_metadata
        secret = self.protected_secret_presence_evidence
        public = self.public_bot_metadata_presence_evidence
        assert bot is not None and secret is not None and public is not None
        matches = (
            bot.telegram_bot_username == "@signalings_bot"
            and bot.telegram_bot_numeric_id == "8664835407"
            and secret.protected_secret_reference == "/etc/avito-mayak/secrets/telegram_bot_token"
            and secret.observed_owner == "root"
            and secret.observed_group == "root"
            and secret.observed_mode == "0600"
            and secret.observed_size_bytes > 0
            and public.public_metadata_reference == "/etc/avito-mayak/telegram-bot.conf"
            and public.observed_owner == "root"
            and public.observed_group == "root"
            and public.observed_mode == "0644"
            and public.observed_size_bytes > 0
        )
        if self.state is TelegramExistingBotEvidenceState.VERIFIED_REDACTED_EVIDENCE:
            if not matches or self.blocking_decision_reference_id is not None:
                raise ValueError("verified state requires exact non-secret metadata and no block")
        elif self.state is TelegramExistingBotEvidenceState.EVIDENCE_MISMATCH:
            if matches or self.blocking_decision_reference_id is None:
                raise ValueError(
                    "mismatch state requires differing metadata and blocking reference"
                )
        return self


__all__ = [
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
    "TelegramProviderUpdateIdentity",
    "TelegramProviderIdentity",
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
]
