"""Transport-neutral Admin & Support boundary for Notification Delivery requests."""

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


_NonEmptyReferenceId = Annotated[str, Field(min_length=1)]


class AdminNotificationActionKind(str, Enum):
    REQUEST_RECONCILIATION = "REQUEST_RECONCILIATION"
    REQUEST_RESEND = "REQUEST_RESEND"
    REQUEST_SUPPRESSION = "REQUEST_SUPPRESSION"
    REQUEST_CANCELLATION = "REQUEST_CANCELLATION"


class AdminNotificationActionOutcomeState(str, Enum):
    RECONCILIATION_REQUESTED = "RECONCILIATION_REQUESTED"
    UNCHANGED = "UNCHANGED"
    BLOCKED = "BLOCKED"
    REJECTED = "REJECTED"
    CONFLICT = "CONFLICT"
    AMBIGUOUS = "AMBIGUOUS"


_ACTION_FAMILY_BY_KIND = {
    AdminNotificationActionKind.REQUEST_RECONCILIATION: "NOTIFICATION_REQUEST_RECONCILIATION",
    AdminNotificationActionKind.REQUEST_RESEND: "NOTIFICATION_REQUEST_RESEND",
    AdminNotificationActionKind.REQUEST_SUPPRESSION: "NOTIFICATION_REQUEST_SUPPRESSION",
    AdminNotificationActionKind.REQUEST_CANCELLATION: "NOTIFICATION_REQUEST_CANCELLATION",
}

_AUDIT_STATE_BY_OUTCOME = {
    AdminNotificationActionOutcomeState.RECONCILIATION_REQUESTED: SupportActionAuditState.RECORDED,
    AdminNotificationActionOutcomeState.UNCHANGED: SupportActionAuditState.REPLAYED,
    AdminNotificationActionOutcomeState.BLOCKED: SupportActionAuditState.REJECTED,
    AdminNotificationActionOutcomeState.REJECTED: SupportActionAuditState.REJECTED,
    AdminNotificationActionOutcomeState.CONFLICT: SupportActionAuditState.CONFLICT,
    AdminNotificationActionOutcomeState.AMBIGUOUS: SupportActionAuditState.MANUAL_REVIEW_REQUIRED,
}


def _reject_duplicate_ids(values: tuple[str, ...], label: str) -> None:
    if any(not value for value in values):
        raise ValueError(f"{label} identifiers must be non-empty")
    if len(values) != len(set(values)):
        raise ValueError(f"duplicate {label} identifiers are not allowed")


class AdminNotificationDeliveryStateSummary(_AdminNotificationContract):
    admin_notification_delivery_state_summary_id: str = Field(min_length=1)
    metadata: ContractMetadata
    actor_context: SupportActorContext
    subject: SupportSubjectReference
    target_account_reference_id: str = Field(min_length=1)
    notification_outbox_item_reference_id: str | None = Field(default=None, min_length=1)
    notification_attempt_reference_id: str | None = Field(default=None, min_length=1)
    notification_delivery_history_reference_id: str | None = Field(default=None, min_length=1)
    reconciliation_reference_id: str | None = Field(default=None, min_length=1)
    state: SupportSafeSummaryState
    freshness: SupportFreshnessState
    provenance_reference_ids: tuple[_NonEmptyReferenceId, ...] = ()
    evidence_references: tuple[SupportEvidenceReference, ...] = ()
    redacted: Literal[True] = True
    safe_reference_only: Literal[True] = True
    contains_secret_material: Literal[False] = False
    raw_provider_payload_retained: Literal[False] = False
    provider_mapping_authority: Literal[False] = False
    delivery_execution_authority: Literal[False] = False
    retry_authority: Literal[False] = False
    mutation_authority: Literal[False] = False

    @model_validator(mode="after")
    def _validate_summary_boundary(self) -> "AdminNotificationDeliveryStateSummary":
        if self.subject.owning_module_id != NOTIFICATION_DELIVERY_MODULE_ID:
            raise ValueError("notification summary must be owned by Notification Delivery")
        if self.subject.subject_kind not in {
            SupportSubjectKind.NOTIFICATION_OUTBOX_ITEM,
            SupportSubjectKind.NOTIFICATION_ATTEMPT,
        }:
            raise ValueError("notification summary subject must be an outbox item or attempt")
        if self.subject.target_account_reference_id != self.target_account_reference_id:
            raise ValueError("summary subject account reference must match target")
        if self.state in {
            SupportSafeSummaryState.AVAILABLE,
            SupportSafeSummaryState.REDACTED,
            SupportSafeSummaryState.STALE,
        }:
            expected_freshness = (
                SupportFreshnessState.STALE
                if self.state is SupportSafeSummaryState.STALE
                else SupportFreshnessState.FRESH
            )
            if self.freshness is not expected_freshness:
                raise ValueError("notification summary freshness does not match state")
            if not self.provenance_reference_ids or not self.evidence_references:
                raise ValueError("usable notification summary requires provenance and evidence")
        elif self.freshness not in {
            SupportFreshnessState.UNKNOWN,
            SupportFreshnessState.AMBIGUOUS,
        }:
            raise ValueError(
                "non-usable notification summary requires unknown or ambiguous freshness"
            )
        if self.state is SupportSafeSummaryState.UNKNOWN and (
            self.freshness is not SupportFreshnessState.UNKNOWN
        ):
            raise ValueError("unknown notification summary requires unknown freshness")
        if self.state is SupportSafeSummaryState.AMBIGUOUS and (
            self.freshness is not SupportFreshnessState.AMBIGUOUS
        ):
            raise ValueError("ambiguous notification summary requires ambiguous freshness")
        if self.state in {
            SupportSafeSummaryState.FORBIDDEN,
            SupportSafeSummaryState.NOT_FOUND_SAFE,
            SupportSafeSummaryState.UNKNOWN,
            SupportSafeSummaryState.AMBIGUOUS,
            SupportSafeSummaryState.UNSUPPORTED,
        } and any(
            reference is not None
            for reference in (
                self.notification_outbox_item_reference_id,
                self.notification_attempt_reference_id,
                self.notification_delivery_history_reference_id,
                self.reconciliation_reference_id,
            )
        ):
            raise ValueError("non-usable notification summary cannot carry delivery references")
        _reject_duplicate_ids(self.provenance_reference_ids, "provenance")
        _reject_duplicate_ids(
            tuple(item.support_evidence_reference_id for item in self.evidence_references),
            "evidence-reference",
        )
        if not self.evidence_references:
            raise ValueError("notification summary requires evidence")
        return self


class AdminNotificationSupportActionRequest(_AdminNotificationContract):
    admin_notification_support_action_request_id: str = Field(min_length=1)
    metadata: ContractMetadata
    command_envelope: SupportCommandEnvelope
    current_state_summary: AdminNotificationDeliveryStateSummary
    action_kind: AdminNotificationActionKind
    target_account_reference_id: str = Field(min_length=1)
    target_outbox_item_reference_id: str | None = Field(default=None, min_length=1)
    target_attempt_reference_id: str | None = Field(default=None, min_length=1)
    expected_reconciliation_reference_id: str | None = Field(default=None, min_length=1)
    timestamp_policy_reference_id: str = Field(min_length=1)
    server_authorization_required: Literal[True] = True
    notification_delivery_authority: Literal[True] = True
    reconciliation_first_for_ambiguous_effect: Literal[True] = True
    idempotency_required: Literal[True] = True
    duplicate_protection_required: Literal[True] = True
    direct_outbox_mutation_authority: Literal[False] = False
    direct_attempt_mutation_authority: Literal[False] = False
    direct_provider_call_authority: Literal[False] = False
    provider_mapping_authority: Literal[False] = False
    retry_policy_authority: Literal[False] = False
    blind_resend_authority: Literal[False] = False
    suppression_policy_authority: Literal[False] = False
    cancellation_policy_authority: Literal[False] = False
    runtime_execution_authority: Literal[False] = False
    persistence_implementation_authority: Literal[False] = False

    @model_validator(mode="after")
    def _validate_request_boundary(self) -> "AdminNotificationSupportActionRequest":
        envelope = self.command_envelope
        summary = self.current_state_summary
        if self.metadata != envelope.metadata or self.metadata.causation_id is None:
            raise ValueError("request metadata must match envelope and have causation")
        if envelope.owning_module_id != NOTIFICATION_DELIVERY_MODULE_ID:
            raise ValueError("notification envelope must be owned by Notification Delivery")
        if envelope.subject.owning_module_id != NOTIFICATION_DELIVERY_MODULE_ID:
            raise ValueError("notification envelope subject must be owned by Notification Delivery")
        if envelope.subject.subject_kind not in {
            SupportSubjectKind.NOTIFICATION_OUTBOX_ITEM,
            SupportSubjectKind.NOTIFICATION_ATTEMPT,
        }:
            raise ValueError("notification envelope subject must be an outbox item or attempt")
        if envelope.actor_context != summary.actor_context or envelope.subject != summary.subject:
            raise ValueError("envelope actor and subject must match summary")
        if self.target_account_reference_id != summary.target_account_reference_id:
            raise ValueError("request account must match summary")
        if self.target_outbox_item_reference_id != summary.notification_outbox_item_reference_id:
            raise ValueError("request outbox reference must match summary")
        if self.target_attempt_reference_id != summary.notification_attempt_reference_id:
            raise ValueError("request attempt reference must match summary")
        if envelope.action_family_reference_id != _ACTION_FAMILY_BY_KIND[self.action_kind]:
            raise ValueError("notification action family does not match action kind")
        if not envelope.evidence_references:
            raise ValueError("notification envelope requires evidence")
        _reject_duplicate_ids(
            tuple(item.support_evidence_reference_id for item in envelope.evidence_references),
            "evidence-reference",
        )
        if self.action_kind is AdminNotificationActionKind.REQUEST_RECONCILIATION:
            if summary.state is not SupportSafeSummaryState.AMBIGUOUS:
                raise ValueError("reconciliation request requires ambiguous notification state")
            if envelope.state is SupportCommandPreparationState.PREPARED and (
                not self.expected_reconciliation_reference_id
            ):
                raise ValueError(
                    "prepared reconciliation requires expected reconciliation reference"
                )
        elif envelope.state is SupportCommandPreparationState.PREPARED:
            raise ValueError("resend, suppression and cancellation require explicit policy")
        if envelope.state is SupportCommandPreparationState.PREPARED:
            if summary.state not in {
                SupportSafeSummaryState.AVAILABLE,
                SupportSafeSummaryState.REDACTED,
                SupportSafeSummaryState.STALE,
                SupportSafeSummaryState.AMBIGUOUS,
            }:
                raise ValueError("prepared notification request requires a meaningful summary")
            if not summary.provenance_reference_ids or not summary.evidence_references:
                raise ValueError("prepared notification request requires summary evidence")
        return self


class AdminNotificationSupportActionOutcome(_AdminNotificationContract):
    admin_notification_support_action_outcome_id: str = Field(min_length=1)
    metadata: ContractMetadata
    request: AdminNotificationSupportActionRequest
    state: AdminNotificationActionOutcomeState
    notification_delivery_decision_reference_id: str = Field(min_length=1)
    authoritative_reconciliation_reference_id: str | None = Field(default=None, min_length=1)
    audit_record: SupportActionAuditRecord
    evidence_references: tuple[SupportEvidenceReference, ...]
    notification_delivery_outcome_authority: Literal[True] = True
    admin_support_notification_state_authority: Literal[False] = False
    direct_outbox_mutation_authority: Literal[False] = False
    direct_provider_call_authority: Literal[False] = False
    provider_mapping_authority: Literal[False] = False
    retry_authority: Literal[False] = False
    blind_resend_authority: Literal[False] = False
    suppression_policy_authority: Literal[False] = False
    cancellation_policy_authority: Literal[False] = False

    @model_validator(mode="after")
    def _validate_outcome_boundary(self) -> "AdminNotificationSupportActionOutcome":
        request = self.request
        envelope = request.command_envelope
        if envelope.state is not SupportCommandPreparationState.PREPARED:
            raise ValueError("outcome requires prepared request")
        if envelope.owning_command_reference_id is None:
            raise ValueError("outcome requires owning command reference")
        if self.metadata.correlation_id != request.metadata.correlation_id:
            raise ValueError("outcome correlation must match request")
        if self.metadata.causation_id != request.metadata.message_id:
            raise ValueError("outcome causation must match request message")
        if self.state is AdminNotificationActionOutcomeState.RECONCILIATION_REQUESTED:
            if request.action_kind is not AdminNotificationActionKind.REQUEST_RECONCILIATION:
                raise ValueError("reconciliation outcome does not match action kind")
            if self.authoritative_reconciliation_reference_id is None:
                raise ValueError("reconciliation outcome requires authoritative reference")
        elif self.authoritative_reconciliation_reference_id is not None:
            raise ValueError("non-reconciliation outcome cannot carry reconciliation reference")
        if not self.evidence_references:
            raise ValueError("notification outcome requires evidence")
        evidence_ids = tuple(
            item.support_evidence_reference_id for item in self.evidence_references
        )
        _reject_duplicate_ids(evidence_ids, "evidence-reference")
        audit = self.audit_record
        if (
            tuple(item.support_evidence_reference_id for item in audit.evidence_references)
            != evidence_ids
            or audit.support_action_id != envelope.support_action_id
            or audit.support_case_id != envelope.support_case_id
            or audit.actor_context != envelope.actor_context
            or audit.subject != envelope.subject
            or audit.action_family_reference_id != envelope.action_family_reference_id
            or audit.reason_code != envelope.reason_code
            or audit.requested_command_reference_id != envelope.owning_command_reference_id
            or audit.owning_module_id != NOTIFICATION_DELIVERY_MODULE_ID
            or audit.owning_module_outcome_reference_id
            != self.notification_delivery_decision_reference_id
            or audit.state is not _AUDIT_STATE_BY_OUTCOME[self.state]
            or audit.metadata.correlation_id != self.metadata.correlation_id
            or audit.metadata.causation_id != self.metadata.message_id
        ):
            raise ValueError("audit record does not align with notification outcome and envelope")
        return self


__all__ = [
    "AdminNotificationActionKind",
    "AdminNotificationActionOutcomeState",
    "AdminNotificationDeliveryStateSummary",
    "AdminNotificationSupportActionRequest",
    "AdminNotificationSupportActionOutcome",
]
