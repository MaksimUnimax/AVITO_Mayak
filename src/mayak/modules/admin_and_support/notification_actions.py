"""Transport-neutral Admin & Support Notification Delivery request boundary."""

from __future__ import annotations

from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from mayak.contracts.metadata import ContractMetadata
from mayak.modules.admin_and_support.contracts import (
    SupportActionAuditRecord,
    SupportActionAuditState,
    SupportActorContext,
    SupportCommandEnvelope,
    SupportCommandPreparationState,
    SupportEvidenceReference,
    SupportFreshnessState,
    SupportSubjectKind,
    SupportSubjectReference,
)
from mayak.modules.admin_and_support.safe_reads import SupportSafeSummaryState
from mayak.platform.boundaries import NOTIFICATION_DELIVERY_MODULE_ID


class _AdminNotificationContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


_Reference = Annotated[str, Field(min_length=1)]


class AdminNotificationSupportActionKind(str, Enum):
    REQUEST_RECONCILIATION = "REQUEST_RECONCILIATION"
    REQUEST_BOUNDED_RETRY_AFTER_POLICY = "REQUEST_BOUNDED_RETRY_AFTER_POLICY"
    REQUEST_SUPPRESSION = "REQUEST_SUPPRESSION"
    REQUEST_CANCELLATION = "REQUEST_CANCELLATION"


class AdminNotificationDeliveryStateClass(str, Enum):
    PLANNED = "PLANNED"
    REPLAYED = "REPLAYED"
    SUPPRESSED = "SUPPRESSED"
    BLOCKED = "BLOCKED"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"
    RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"
    AMBIGUOUS = "AMBIGUOUS"


class AdminNotificationSupportOutcomeState(str, Enum):
    RECONCILIATION_REQUEST_ACCEPTED = "RECONCILIATION_REQUEST_ACCEPTED"
    BOUNDED_RETRY_REQUEST_ACCEPTED = "BOUNDED_RETRY_REQUEST_ACCEPTED"
    SUPPRESSION_REQUEST_ACCEPTED = "SUPPRESSION_REQUEST_ACCEPTED"
    CANCELLATION_REQUEST_ACCEPTED = "CANCELLATION_REQUEST_ACCEPTED"
    UNCHANGED = "UNCHANGED"
    BLOCKED = "BLOCKED"
    REJECTED = "REJECTED"
    CONFLICT = "CONFLICT"
    AMBIGUOUS = "AMBIGUOUS"


_ACTION_FAMILY_BY_KIND = {
    AdminNotificationSupportActionKind.REQUEST_RECONCILIATION: (
        "NOTIFICATION_SUPPORT_REQUEST_RECONCILIATION"
    ),
    AdminNotificationSupportActionKind.REQUEST_BOUNDED_RETRY_AFTER_POLICY: (
        "NOTIFICATION_SUPPORT_REQUEST_BOUNDED_RETRY"
    ),
    AdminNotificationSupportActionKind.REQUEST_SUPPRESSION: (
        "NOTIFICATION_SUPPORT_REQUEST_SUPPRESSION"
    ),
    AdminNotificationSupportActionKind.REQUEST_CANCELLATION: (
        "NOTIFICATION_SUPPORT_REQUEST_CANCELLATION"
    ),
}
_SUCCESS_OUTCOME_BY_KIND = {
    AdminNotificationSupportActionKind.REQUEST_RECONCILIATION: (
        AdminNotificationSupportOutcomeState.RECONCILIATION_REQUEST_ACCEPTED
    ),
    AdminNotificationSupportActionKind.REQUEST_BOUNDED_RETRY_AFTER_POLICY: (
        AdminNotificationSupportOutcomeState.BOUNDED_RETRY_REQUEST_ACCEPTED
    ),
    AdminNotificationSupportActionKind.REQUEST_SUPPRESSION: (
        AdminNotificationSupportOutcomeState.SUPPRESSION_REQUEST_ACCEPTED
    ),
    AdminNotificationSupportActionKind.REQUEST_CANCELLATION: (
        AdminNotificationSupportOutcomeState.CANCELLATION_REQUEST_ACCEPTED
    ),
}
_AUDIT_STATE_BY_OUTCOME = {
    AdminNotificationSupportOutcomeState.RECONCILIATION_REQUEST_ACCEPTED: (
        SupportActionAuditState.RECORDED
    ),
    AdminNotificationSupportOutcomeState.BOUNDED_RETRY_REQUEST_ACCEPTED: (
        SupportActionAuditState.RECORDED
    ),
    AdminNotificationSupportOutcomeState.SUPPRESSION_REQUEST_ACCEPTED: (
        SupportActionAuditState.RECORDED
    ),
    AdminNotificationSupportOutcomeState.CANCELLATION_REQUEST_ACCEPTED: (
        SupportActionAuditState.RECORDED
    ),
    AdminNotificationSupportOutcomeState.UNCHANGED: SupportActionAuditState.REPLAYED,
    AdminNotificationSupportOutcomeState.BLOCKED: SupportActionAuditState.REJECTED,
    AdminNotificationSupportOutcomeState.REJECTED: SupportActionAuditState.REJECTED,
    AdminNotificationSupportOutcomeState.CONFLICT: SupportActionAuditState.CONFLICT,
    AdminNotificationSupportOutcomeState.AMBIGUOUS: SupportActionAuditState.MANUAL_REVIEW_REQUIRED,
}


def _unique(values: tuple[str, ...], label: str, required: bool = False) -> None:
    if any(not value for value in values) or len(values) != len(set(values)):
        raise ValueError(f"invalid {label} identifiers")
    if required and not values:
        raise ValueError(f"{label} is required")


def _current_reference_values(summary: AdminNotificationCurrentStateSummary) -> tuple[object, ...]:
    return (
        summary.notification_read_model_reference_id,
        summary.notification_history_entry_reference_id,
        summary.notification_security_decision_reference_id,
        summary.notification_deduplication_reference_id,
        summary.delivery_state_class,
    )


def _all_current_reference_values(
    summary: AdminNotificationCurrentStateSummary,
) -> tuple[object, ...]:
    return (
        *_current_reference_values(summary),
        summary.provider_outcome_acceptance_reference_id,
    )


class AdminNotificationCurrentStateSummary(_AdminNotificationContract):
    admin_notification_current_state_summary_id: str = Field(min_length=1)
    metadata: ContractMetadata
    actor_context: SupportActorContext
    subject: SupportSubjectReference
    target_account_reference_id: str = Field(min_length=1)
    target_beacon_reference_id: str | None = Field(default=None, min_length=1)
    notification_outbox_item_reference_id: str = Field(min_length=1)
    notification_attempt_reference_id: str | None = Field(default=None, min_length=1)
    notification_read_model_reference_id: str | None = Field(default=None, min_length=1)
    notification_history_entry_reference_id: str | None = Field(default=None, min_length=1)
    notification_security_decision_reference_id: str | None = Field(default=None, min_length=1)
    notification_deduplication_reference_id: str | None = Field(default=None, min_length=1)
    provider_outcome_acceptance_reference_id: str | None = Field(default=None, min_length=1)
    delivery_state_class: AdminNotificationDeliveryStateClass | None = None
    reconciliation_required: bool
    retry_policy_required: bool
    state: SupportSafeSummaryState
    freshness: SupportFreshnessState
    provenance_reference_ids: tuple[_Reference, ...]
    evidence_references: tuple[SupportEvidenceReference, ...]
    redacted: Literal[True] = True
    safe_reference_only: Literal[True] = True
    notification_delivery_authority_preserved: Literal[True] = True
    contains_secret_material: Literal[False] = False
    raw_provider_payload_retained: Literal[False] = False
    raw_recipient_identity_retained: Literal[False] = False
    direct_outbox_mutation_authority: Literal[False] = False
    direct_attempt_mutation_authority: Literal[False] = False
    provider_send_authority: Literal[False] = False
    provider_mapping_authority: Literal[False] = False
    blind_retry_authority: Literal[False] = False
    ambiguous_provider_effect_hidden: Literal[False] = False
    mutation_authority: Literal[False] = False

    @model_validator(mode="after")
    def _validate_summary(self) -> AdminNotificationCurrentStateSummary:
        if self.subject.owning_module_id != NOTIFICATION_DELIVERY_MODULE_ID:
            raise ValueError("subject owner mismatch")
        if self.subject.subject_kind not in {
            SupportSubjectKind.NOTIFICATION_OUTBOX_ITEM,
            SupportSubjectKind.NOTIFICATION_ATTEMPT,
        }:
            raise ValueError("subject kind mismatch")
        if self.subject.target_account_reference_id != self.target_account_reference_id:
            raise ValueError("account mismatch")
        if self.subject.subject_kind is SupportSubjectKind.NOTIFICATION_OUTBOX_ITEM:
            if self.subject.safe_subject_reference_id != self.notification_outbox_item_reference_id:
                raise ValueError("outbox reference mismatch")
        elif (
            self.notification_attempt_reference_id is None
            or self.subject.safe_subject_reference_id != self.notification_attempt_reference_id
        ):
            raise ValueError("attempt reference mismatch")
        usable = self.state in {
            SupportSafeSummaryState.AVAILABLE,
            SupportSafeSummaryState.REDACTED,
        }
        stale = self.state is SupportSafeSummaryState.STALE
        if usable and self.freshness is not SupportFreshnessState.FRESH:
            raise ValueError("usable summary must be fresh")
        if stale and self.freshness is not SupportFreshnessState.STALE:
            raise ValueError("stale summary must be stale")
        if (usable or stale) and (
            self.delivery_state_class is None
            or any(value is None for value in _current_reference_values(self))
            or not self.provenance_reference_ids
        ):
            raise ValueError("authoritative summary references are incomplete")
        if (
            self.state is SupportSafeSummaryState.UNKNOWN
            and self.freshness is not SupportFreshnessState.UNKNOWN
        ):
            raise ValueError("unknown summary must be unknown")
        if (
            self.state is SupportSafeSummaryState.AMBIGUOUS
            and self.freshness is not SupportFreshnessState.AMBIGUOUS
        ):
            raise ValueError("ambiguous summary must be ambiguous")
        if self.state in {
            SupportSafeSummaryState.FORBIDDEN,
            SupportSafeSummaryState.NOT_FOUND_SAFE,
            SupportSafeSummaryState.UNKNOWN,
            SupportSafeSummaryState.AMBIGUOUS,
            SupportSafeSummaryState.UNSUPPORTED,
        } and any(value is not None for value in _all_current_reference_values(self)):
            raise ValueError("non-authoritative summary carries current references")
        if (
            self.delivery_state_class
            in {
                AdminNotificationDeliveryStateClass.RECONCILIATION_REQUIRED,
                AdminNotificationDeliveryStateClass.AMBIGUOUS,
            }
            and not self.reconciliation_required
        ):
            raise ValueError("reconciliation flag is required")
        if (
            self.retry_policy_required
            and self.delivery_state_class is not AdminNotificationDeliveryStateClass.FAILED
        ):
            raise ValueError("retry policy is only valid for failed state")
        if self.delivery_state_class is AdminNotificationDeliveryStateClass.DELIVERED and (
            self.reconciliation_required or self.retry_policy_required
        ):
            raise ValueError("delivered state cannot require retry or reconciliation")
        _unique(self.provenance_reference_ids, "provenance", required=False)
        _unique(
            tuple(item.support_evidence_reference_id for item in self.evidence_references),
            "evidence",
            required=True,
        )
        return self


class AdminNotificationInterventionPolicyReference(_AdminNotificationContract):
    admin_notification_intervention_policy_reference_id: str = Field(min_length=1)
    action_kind: AdminNotificationSupportActionKind
    notification_intervention_policy_decision_reference_id: str = Field(min_length=1)
    notification_security_decision_reference_id: str = Field(min_length=1)
    notification_deduplication_reference_id: str = Field(min_length=1)
    reconciliation_obligation_reference_id: str | None = Field(default=None, min_length=1)
    reconciliation_clearance_reference_id: str | None = Field(default=None, min_length=1)
    retry_policy_reference_id: str | None = Field(default=None, min_length=1)
    suppression_policy_reference_id: str | None = Field(default=None, min_length=1)
    cancellation_policy_reference_id: str | None = Field(default=None, min_length=1)
    safe_reference_only: Literal[True] = True
    notification_delivery_policy_authority_preserved: Literal[True] = True
    duplicate_protection_required: Literal[True] = True
    ambiguous_provider_effect_must_remain_explicit: Literal[True] = True
    direct_send_authority: Literal[False] = False
    blind_retry_authority: Literal[False] = False
    direct_outbox_mutation_authority: Literal[False] = False
    provider_mapping_authority: Literal[False] = False
    provider_execution_authority: Literal[False] = False

    @model_validator(mode="after")
    def _validate_policy(self) -> AdminNotificationInterventionPolicyReference:
        if self.action_kind is AdminNotificationSupportActionKind.REQUEST_RECONCILIATION:
            if self.reconciliation_obligation_reference_id is None or any(
                value is not None
                for value in (
                    self.reconciliation_clearance_reference_id,
                    self.retry_policy_reference_id,
                    self.suppression_policy_reference_id,
                    self.cancellation_policy_reference_id,
                )
            ):
                raise ValueError("policy references do not match action matrix")
        elif (
            self.action_kind
            is AdminNotificationSupportActionKind.REQUEST_BOUNDED_RETRY_AFTER_POLICY
        ):
            if (
                self.reconciliation_clearance_reference_id is None
                or self.retry_policy_reference_id is None
                or any(
                    value is not None
                    for value in (
                        self.reconciliation_obligation_reference_id,
                        self.suppression_policy_reference_id,
                        self.cancellation_policy_reference_id,
                    )
                )
            ):
                raise ValueError("policy references do not match action matrix")
        elif self.action_kind is AdminNotificationSupportActionKind.REQUEST_SUPPRESSION:
            if self.suppression_policy_reference_id is None or any(
                value is not None
                for value in (
                    self.reconciliation_obligation_reference_id,
                    self.reconciliation_clearance_reference_id,
                    self.retry_policy_reference_id,
                    self.cancellation_policy_reference_id,
                )
            ):
                raise ValueError("policy references do not match action matrix")
        elif self.cancellation_policy_reference_id is None or any(
            value is not None
            for value in (
                self.reconciliation_obligation_reference_id,
                self.reconciliation_clearance_reference_id,
                self.retry_policy_reference_id,
                self.suppression_policy_reference_id,
            )
        ):
            raise ValueError("policy references do not match action matrix")
        return self


class AdminNotificationSupportActionRequest(_AdminNotificationContract):
    admin_notification_support_action_request_id: str = Field(min_length=1)
    metadata: ContractMetadata
    command_envelope: SupportCommandEnvelope
    current_state_summary: AdminNotificationCurrentStateSummary
    intervention_policy_reference: AdminNotificationInterventionPolicyReference
    action_kind: AdminNotificationSupportActionKind
    target_account_reference_id: str = Field(min_length=1)
    target_beacon_reference_id: str | None = Field(default=None, min_length=1)
    target_outbox_item_reference_id: str = Field(min_length=1)
    target_attempt_reference_id: str | None = Field(default=None, min_length=1)
    timestamp_policy_reference_id: str = Field(min_length=1)
    server_authorization_required: Literal[True] = True
    notification_delivery_authority_preserved: Literal[True] = True
    idempotency_required: Literal[True] = True
    duplicate_protection_required: Literal[True] = True
    reconciliation_first_for_ambiguous_effect: Literal[True] = True
    direct_notification_send_authority: Literal[False] = False
    blind_resend_authority: Literal[False] = False
    direct_outbox_mutation_authority: Literal[False] = False
    direct_attempt_mutation_authority: Literal[False] = False
    telegram_send_authority: Literal[False] = False
    max_send_authority: Literal[False] = False
    provider_mapping_authority: Literal[False] = False
    provider_execution_authority: Literal[False] = False
    business_execution_authority: Literal[False] = False
    runtime_authority: Literal[False] = False

    @model_validator(mode="after")
    def _validate_request(self) -> AdminNotificationSupportActionRequest:
        envelope = self.command_envelope
        summary = self.current_state_summary
        policy = self.intervention_policy_reference
        if self.metadata != envelope.metadata or self.metadata.causation_id is None:
            raise ValueError("metadata mismatch or missing causation")
        if (
            envelope.owning_module_id != NOTIFICATION_DELIVERY_MODULE_ID
            or envelope.subject.owning_module_id != NOTIFICATION_DELIVERY_MODULE_ID
        ):
            raise ValueError("envelope owner mismatch")
        if envelope.subject.subject_kind not in {
            SupportSubjectKind.NOTIFICATION_OUTBOX_ITEM,
            SupportSubjectKind.NOTIFICATION_ATTEMPT,
        }:
            raise ValueError("envelope subject kind mismatch")
        if envelope.actor_context != summary.actor_context or envelope.subject != summary.subject:
            raise ValueError("envelope context mismatch")
        if (
            self.target_account_reference_id,
            self.target_beacon_reference_id,
            self.target_outbox_item_reference_id,
            self.target_attempt_reference_id,
        ) != (
            summary.target_account_reference_id,
            summary.target_beacon_reference_id,
            summary.notification_outbox_item_reference_id,
            summary.notification_attempt_reference_id,
        ):
            raise ValueError("request targets mismatch")
        selected = (
            self.target_attempt_reference_id
            if envelope.subject.subject_kind is SupportSubjectKind.NOTIFICATION_ATTEMPT
            else self.target_outbox_item_reference_id
        )
        if envelope.subject.safe_subject_reference_id != selected:
            raise ValueError("envelope safe subject mismatch")
        if action_kind := policy.action_kind:
            if (
                self.action_kind is not action_kind
                or envelope.action_family_reference_id != _ACTION_FAMILY_BY_KIND[self.action_kind]
            ):
                raise ValueError("action or action family mismatch")
        if (
            envelope.policy_reference_id
            != policy.admin_notification_intervention_policy_reference_id
        ):
            raise ValueError("envelope policy reference mismatch")
        if (
            policy.notification_security_decision_reference_id
            != summary.notification_security_decision_reference_id
            or policy.notification_deduplication_reference_id
            != summary.notification_deduplication_reference_id
        ):
            raise ValueError("policy safe references mismatch")
        _unique(
            tuple(item.support_evidence_reference_id for item in envelope.evidence_references),
            "evidence",
            required=True,
        )
        if envelope.state is SupportCommandPreparationState.PREPARED:
            if (
                summary.state
                not in {SupportSafeSummaryState.AVAILABLE, SupportSafeSummaryState.REDACTED}
                or summary.freshness is not SupportFreshnessState.FRESH
            ):
                raise ValueError("prepared request requires fresh usable summary")
            if (
                any(value is None for value in _current_reference_values(summary))
                or not summary.provenance_reference_ids
                or not summary.evidence_references
            ):
                raise ValueError("prepared request requires complete summary")
            if summary.reconciliation_required or summary.delivery_state_class in {
                AdminNotificationDeliveryStateClass.RECONCILIATION_REQUIRED,
                AdminNotificationDeliveryStateClass.AMBIGUOUS,
            }:
                if (
                    self.action_kind
                    is not AdminNotificationSupportActionKind.REQUEST_RECONCILIATION
                ):
                    raise ValueError("ambiguous effect requires reconciliation first")
            if (
                self.action_kind is AdminNotificationSupportActionKind.REQUEST_RECONCILIATION
                and not (
                    summary.reconciliation_required
                    or summary.delivery_state_class
                    in {
                        AdminNotificationDeliveryStateClass.RECONCILIATION_REQUIRED,
                        AdminNotificationDeliveryStateClass.AMBIGUOUS,
                    }
                )
            ):
                raise ValueError("reconciliation request requires reconciliation flag or state")
            if (
                self.action_kind
                is AdminNotificationSupportActionKind.REQUEST_BOUNDED_RETRY_AFTER_POLICY
            ):
                if (
                    summary.delivery_state_class is not AdminNotificationDeliveryStateClass.FAILED
                    or summary.reconciliation_required
                    or policy.retry_policy_reference_id is None
                    or policy.reconciliation_clearance_reference_id is None
                ):
                    raise ValueError("bounded retry gates are incomplete")
            if (
                self.action_kind is AdminNotificationSupportActionKind.REQUEST_SUPPRESSION
                and policy.suppression_policy_reference_id is None
            ):
                raise ValueError("suppression policy is required")
            if (
                self.action_kind is AdminNotificationSupportActionKind.REQUEST_CANCELLATION
                and policy.cancellation_policy_reference_id is None
            ):
                raise ValueError("cancellation policy is required")
        return self


class AdminNotificationSupportActionOutcome(_AdminNotificationContract):
    admin_notification_support_action_outcome_id: str = Field(min_length=1)
    metadata: ContractMetadata
    request: AdminNotificationSupportActionRequest
    state: AdminNotificationSupportOutcomeState
    notification_support_decision_reference_id: str = Field(min_length=1)
    notification_deduplication_decision_reference_id: str | None = Field(default=None, min_length=1)
    notification_reconciliation_record_reference_id: str | None = Field(default=None, min_length=1)
    notification_attempt_plan_reference_id: str | None = Field(default=None, min_length=1)
    notification_suppression_record_reference_id: str | None = Field(default=None, min_length=1)
    notification_cancellation_record_reference_id: str | None = Field(default=None, min_length=1)
    post_action_read_model_reference_id: str | None = Field(default=None, min_length=1)
    post_action_history_entry_reference_id: str | None = Field(default=None, min_length=1)
    post_action_outbox_state_reference_id: str | None = Field(default=None, min_length=1)
    audit_record: SupportActionAuditRecord
    evidence_references: tuple[SupportEvidenceReference, ...]
    notification_delivery_outcome_authority_preserved: Literal[True] = True
    admin_support_delivery_state_authority: Literal[False] = False
    user_visible_delivery_success_claimed: Literal[False] = False
    provider_send_claimed: Literal[False] = False
    provider_acceptance_inferred: Literal[False] = False
    direct_outbox_mutation_authority: Literal[False] = False
    direct_attempt_mutation_authority: Literal[False] = False
    blind_resend_authority: Literal[False] = False
    ambiguous_provider_effect_hidden: Literal[False] = False
    runtime_authority: Literal[False] = False

    @model_validator(mode="after")
    def _validate_outcome(self) -> AdminNotificationSupportActionOutcome:
        request = self.request
        envelope = request.command_envelope
        if (
            envelope.state is not SupportCommandPreparationState.PREPARED
            or envelope.owning_command_reference_id is None
        ):
            raise ValueError("outcome requires prepared request")
        if (
            self.metadata.correlation_id != request.metadata.correlation_id
            or self.metadata.causation_id != request.metadata.message_id
        ):
            raise ValueError("outcome causation or correlation mismatch")
        evidence_ids = tuple(
            item.support_evidence_reference_id for item in self.evidence_references
        )
        _unique(evidence_ids, "evidence", required=True)
        audit = self.audit_record
        if (
            tuple(item.support_evidence_reference_id for item in audit.evidence_references)
            != evidence_ids
        ):
            raise ValueError("audit evidence mismatch")
        if (
            audit.support_action_id != envelope.support_action_id
            or audit.support_case_id != envelope.support_case_id
            or audit.actor_context != envelope.actor_context
            or audit.subject != envelope.subject
            or audit.action_family_reference_id != envelope.action_family_reference_id
            or audit.reason_code != envelope.reason_code
            or audit.requested_command_reference_id != envelope.owning_command_reference_id
            or audit.owning_module_id != NOTIFICATION_DELIVERY_MODULE_ID
            or audit.owning_module_outcome_reference_id
            != self.notification_support_decision_reference_id
            or audit.state is not _AUDIT_STATE_BY_OUTCOME[self.state]
            or audit.metadata.correlation_id != self.metadata.correlation_id
            or audit.metadata.causation_id != self.metadata.message_id
        ):
            raise ValueError("audit alignment mismatch")
        effects = (
            self.notification_reconciliation_record_reference_id,
            self.notification_attempt_plan_reference_id,
            self.notification_suppression_record_reference_id,
            self.notification_cancellation_record_reference_id,
        )
        post = (
            self.post_action_read_model_reference_id,
            self.post_action_history_entry_reference_id,
            self.post_action_outbox_state_reference_id,
        )
        accepted = self.state in set(_SUCCESS_OUTCOME_BY_KIND.values())
        if accepted:
            if self.state is not _SUCCESS_OUTCOME_BY_KIND[request.action_kind]:
                raise ValueError("accepted outcome does not match action")
            if (
                self.notification_deduplication_decision_reference_id is None
                or any(value is None for value in post)
                or len(set(post)) != 3
            ):
                raise ValueError("accepted outcome requires distinct post-action references")
            required_index = {
                AdminNotificationSupportOutcomeState.RECONCILIATION_REQUEST_ACCEPTED: 0,
                AdminNotificationSupportOutcomeState.BOUNDED_RETRY_REQUEST_ACCEPTED: 1,
                AdminNotificationSupportOutcomeState.SUPPRESSION_REQUEST_ACCEPTED: 2,
                AdminNotificationSupportOutcomeState.CANCELLATION_REQUEST_ACCEPTED: 3,
            }[self.state]
            if effects[required_index] is None or any(
                value is not None for i, value in enumerate(effects) if i != required_index
            ):
                raise ValueError("accepted action effects do not match action")
            if (
                self.state is AdminNotificationSupportOutcomeState.BOUNDED_RETRY_REQUEST_ACCEPTED
                and request.current_state_summary.delivery_state_class
                is not AdminNotificationDeliveryStateClass.FAILED
            ):
                raise ValueError("bounded retry cannot be accepted from this state")
        elif self.state is AdminNotificationSupportOutcomeState.UNCHANGED:
            if (
                self.notification_deduplication_decision_reference_id is None
                or any(value is None for value in post)
                or any(value is not None for value in effects)
                or len(set(post)) != 3
            ):
                raise ValueError("unchanged outcome matrix mismatch")
        elif self.notification_deduplication_decision_reference_id is not None or any(
            value is not None for value in effects + post
        ):
            raise ValueError("non-effect outcome cannot carry action references")
        return self


__all__ = [
    "AdminNotificationSupportActionKind",
    "AdminNotificationDeliveryStateClass",
    "AdminNotificationSupportOutcomeState",
    "AdminNotificationCurrentStateSummary",
    "AdminNotificationInterventionPolicyReference",
    "AdminNotificationSupportActionRequest",
    "AdminNotificationSupportActionOutcome",
]
