from __future__ import annotations

from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from mayak.contracts import (
    ContractMetadata,
    IdempotencyFingerprint,
    IdempotencyKey,
    IdempotencyScope,
)


class _AdminSupportContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


_NonEmptyReferenceId = Annotated[str, Field(min_length=1)]


class SupportCaseState(str, Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    WAITING_FOR_EVIDENCE = "WAITING_FOR_EVIDENCE"
    ESCALATED = "ESCALATED"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    REJECTED = "REJECTED"
    AMBIGUOUS = "AMBIGUOUS"


class SupportWorkItemState(str, Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    BLOCKED = "BLOCKED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    AMBIGUOUS = "AMBIGUOUS"


class SupportSubjectKind(str, Enum):
    ACCOUNT = "ACCOUNT"
    BEACON = "BEACON"
    TARIFF_DEFINITION = "TARIFF_DEFINITION"
    SUBSCRIPTION = "SUBSCRIPTION"
    ENTITLEMENT_GRANT = "ENTITLEMENT_GRANT"
    MANUAL_ACCESS_GRANT = "MANUAL_ACCESS_GRANT"
    SCAN_RUN = "SCAN_RUN"
    LISTING_STATE = "LISTING_STATE"
    EGRESS_ROUTE = "EGRESS_ROUTE"
    NOTIFICATION_OUTBOX_ITEM = "NOTIFICATION_OUTBOX_ITEM"
    NOTIFICATION_ATTEMPT = "NOTIFICATION_ATTEMPT"
    TELEGRAM_ADAPTER_OUTCOME = "TELEGRAM_ADAPTER_OUTCOME"
    MAX_ADAPTER_OUTCOME = "MAX_ADAPTER_OUTCOME"
    GENERIC_SAFE_REFERENCE = "GENERIC_SAFE_REFERENCE"


class SupportEvidenceKind(str, Enum):
    SAFE_RECORD_REFERENCE = "SAFE_RECORD_REFERENCE"
    REDACTED_SUMMARY_REFERENCE = "REDACTED_SUMMARY_REFERENCE"
    HASH_REFERENCE = "HASH_REFERENCE"
    CLASSIFICATION_REFERENCE = "CLASSIFICATION_REFERENCE"
    REPORT_REFERENCE = "REPORT_REFERENCE"


class SupportFreshnessState(str, Enum):
    FRESH = "FRESH"
    STALE = "STALE"
    UNKNOWN = "UNKNOWN"
    AMBIGUOUS = "AMBIGUOUS"


class SupportReadState(str, Enum):
    AUTHORIZED = "AUTHORIZED"
    REDACTED = "REDACTED"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND_SAFE = "NOT_FOUND_SAFE"
    STALE = "STALE"
    AMBIGUOUS = "AMBIGUOUS"


class SupportExplanationState(str, Enum):
    EXPLAINED = "EXPLAINED"
    PARTIALLY_EXPLAINED = "PARTIALLY_EXPLAINED"
    BLOCKED = "BLOCKED"
    STALE = "STALE"
    AMBIGUOUS = "AMBIGUOUS"
    UNSUPPORTED = "UNSUPPORTED"


class SupportCommandPreparationState(str, Enum):
    PREPARED = "PREPARED"
    POLICY_BLOCKED = "POLICY_BLOCKED"
    UNAUTHORIZED = "UNAUTHORIZED"
    TARGET_FORBIDDEN = "TARGET_FORBIDDEN"
    UNSUPPORTED = "UNSUPPORTED"
    AMBIGUOUS = "AMBIGUOUS"


class SupportActionAuditState(str, Enum):
    RECORDED = "RECORDED"
    REPLAYED = "REPLAYED"
    CONFLICT = "CONFLICT"
    REJECTED = "REJECTED"
    MANUAL_REVIEW_REQUIRED = "MANUAL_REVIEW_REQUIRED"


class SupportEscalationState(str, Enum):
    ESCALATED = "ESCALATED"
    ALREADY_ESCALATED = "ALREADY_ESCALATED"
    BLOCKED = "BLOCKED"
    RESOLVED = "RESOLVED"
    AMBIGUOUS = "AMBIGUOUS"


def _reject_duplicate_ids(values: tuple[str, ...], label: str) -> None:
    if any(not value for value in values):
        raise ValueError(f"{label} identifiers must be non-empty")
    if len(values) != len(set(values)):
        raise ValueError(f"duplicate {label} identifiers are not allowed")


class SupportActorContext(_AdminSupportContract):
    support_actor_context_id: str = Field(min_length=1)
    actor_account_id: str = Field(min_length=1)
    identity_actor_reference_id: str = Field(min_length=1)
    role_reference_id: str = Field(min_length=1)
    authorization_scope_reference_id: str = Field(min_length=1)
    authorization_decision_reference_id: str = Field(min_length=1)
    verified: Literal[True] = True
    client_supplied_authority: Literal[False] = False
    provider_identity_authority: Literal[False] = False


class SupportSubjectReference(_AdminSupportContract):
    support_subject_reference_id: str = Field(min_length=1)
    subject_kind: SupportSubjectKind
    owning_module_id: str = Field(min_length=1)
    safe_subject_reference_id: str = Field(min_length=1)
    tenant_scope_reference_id: str = Field(min_length=1)
    target_account_reference_id: str | None = Field(default=None, min_length=1)
    safe_reference_only: Literal[True] = True
    raw_personal_data_retained: Literal[False] = False
    raw_provider_payload_retained: Literal[False] = False


class SupportEvidenceReference(_AdminSupportContract):
    support_evidence_reference_id: str = Field(min_length=1)
    evidence_kind: SupportEvidenceKind
    owning_module_id: str = Field(min_length=1)
    evidence_reference_id: str = Field(min_length=1)
    provenance_reference_id: str = Field(min_length=1)
    freshness: SupportFreshnessState
    classification_code: str = Field(min_length=1)
    safe_reference_only: Literal[True] = True
    contains_secret_material: Literal[False] = False
    raw_provider_payload_retained: Literal[False] = False
    full_private_message_retained: Literal[False] = False


class SupportCase(_AdminSupportContract):
    support_case_id: str = Field(min_length=1)
    metadata: ContractMetadata
    opened_by: SupportActorContext
    primary_subject: SupportSubjectReference
    state: SupportCaseState
    reason_code: str = Field(min_length=1)
    work_item_ids: tuple[_NonEmptyReferenceId, ...] = ()
    evidence_references: tuple[SupportEvidenceReference, ...] = ()
    internal_record: Literal[True] = True
    business_state_authority: Literal[False] = False

    @model_validator(mode="after")
    def _validate_references(self) -> "SupportCase":
        if (
            self.state in {SupportCaseState.RESOLVED, SupportCaseState.CLOSED}
            and not self.evidence_references
        ):
            raise ValueError("resolved or closed case requires evidence")
        _reject_duplicate_ids(self.work_item_ids, "work-item")
        _reject_duplicate_ids(
            tuple(item.support_evidence_reference_id for item in self.evidence_references),
            "evidence-reference",
        )
        return self


class SupportWorkItem(_AdminSupportContract):
    support_work_item_id: str = Field(min_length=1)
    metadata: ContractMetadata
    support_case_id: str = Field(min_length=1)
    assigned_actor: SupportActorContext
    subject: SupportSubjectReference
    state: SupportWorkItemState
    action_family_reference_id: str = Field(min_length=1)
    reason_code: str = Field(min_length=1)
    evidence_references: tuple[SupportEvidenceReference, ...] = ()
    direct_domain_write_authority: Literal[False] = False

    @model_validator(mode="after")
    def _validate_references(self) -> "SupportWorkItem":
        if self.state is SupportWorkItemState.COMPLETED and not self.evidence_references:
            raise ValueError("completed work item requires evidence")
        _reject_duplicate_ids(
            tuple(item.support_evidence_reference_id for item in self.evidence_references),
            "evidence-reference",
        )
        return self


class SupportReadModel(_AdminSupportContract):
    support_read_model_id: str = Field(min_length=1)
    metadata: ContractMetadata
    actor_context: SupportActorContext
    subject: SupportSubjectReference
    state: SupportReadState
    freshness: SupportFreshnessState
    summary_reference_id: str | None = Field(default=None, min_length=1)
    provenance_reference_ids: tuple[_NonEmptyReferenceId, ...] = ()
    evidence_references: tuple[SupportEvidenceReference, ...] = ()
    redacted: Literal[True] = True
    contains_secret_material: Literal[False] = False
    raw_payload_retained: Literal[False] = False
    mutation_authority: Literal[False] = False

    @model_validator(mode="after")
    def _validate_read_matrix(self) -> "SupportReadModel":
        if self.state in {SupportReadState.AUTHORIZED, SupportReadState.REDACTED} and (
            self.summary_reference_id is None or not self.provenance_reference_ids
        ):
            raise ValueError("authorized or redacted read requires summary and provenance")
        if (
            self.state in {SupportReadState.FORBIDDEN, SupportReadState.NOT_FOUND_SAFE}
            and self.summary_reference_id is not None
        ):
            raise ValueError("forbidden or not-found-safe read cannot carry summary")
        if (
            self.state is SupportReadState.STALE
            and self.freshness is not SupportFreshnessState.STALE
        ):
            raise ValueError("stale read requires stale freshness")
        _reject_duplicate_ids(self.provenance_reference_ids, "provenance")
        _reject_duplicate_ids(
            tuple(item.support_evidence_reference_id for item in self.evidence_references),
            "evidence-reference",
        )
        return self


class SupportExplanationRecord(_AdminSupportContract):
    support_explanation_record_id: str = Field(min_length=1)
    metadata: ContractMetadata
    support_case_id: str = Field(min_length=1)
    actor_context: SupportActorContext
    subject: SupportSubjectReference
    read_model_reference_id: str | None = Field(default=None, min_length=1)
    evidence_references: tuple[SupportEvidenceReference, ...] = ()
    state: SupportExplanationState
    safe_explanation_reference_id: str | None = Field(default=None, min_length=1)
    reason_code: str = Field(min_length=1)
    customer_visible: Literal[False] = False
    mutation_authority: Literal[False] = False

    @model_validator(mode="after")
    def _validate_explanation_matrix(self) -> "SupportExplanationRecord":
        if self.state is SupportExplanationState.EXPLAINED and (
            self.read_model_reference_id is None or self.safe_explanation_reference_id is None
        ):
            raise ValueError("explained record requires read-model and safe-explanation references")
        if (
            self.state is SupportExplanationState.PARTIALLY_EXPLAINED
            and self.safe_explanation_reference_id is None
        ):
            raise ValueError("partially explained record requires safe-explanation reference")
        _reject_duplicate_ids(
            tuple(item.support_evidence_reference_id for item in self.evidence_references),
            "evidence-reference",
        )
        return self


class SupportCommandEnvelope(_AdminSupportContract):
    support_command_envelope_id: str = Field(min_length=1)
    metadata: ContractMetadata
    support_case_id: str = Field(min_length=1)
    support_action_id: str = Field(min_length=1)
    actor_context: SupportActorContext
    subject: SupportSubjectReference
    action_family_reference_id: str = Field(min_length=1)
    policy_reference_id: str = Field(min_length=1)
    owning_module_id: str = Field(min_length=1)
    owning_command_reference_id: str | None = Field(default=None, min_length=1)
    idempotency_key: IdempotencyKey
    idempotency_scope: IdempotencyScope
    fingerprint: IdempotencyFingerprint
    evidence_references: tuple[SupportEvidenceReference, ...] = ()
    state: SupportCommandPreparationState
    reason_code: str = Field(min_length=1)
    direct_write_authority: Literal[False] = False
    provider_call_authority: Literal[False] = False
    business_execution_authority: Literal[False] = False

    @model_validator(mode="after")
    def _validate_command_matrix(self) -> "SupportCommandEnvelope":
        if self.state is SupportCommandPreparationState.PREPARED:
            if self.owning_command_reference_id is None or not self.evidence_references:
                raise ValueError("prepared command requires command reference and evidence")
        elif self.owning_command_reference_id is not None:
            raise ValueError("non-prepared command cannot carry command reference")
        _reject_duplicate_ids(
            tuple(item.support_evidence_reference_id for item in self.evidence_references),
            "evidence-reference",
        )
        return self


class SupportActionAuditRecord(_AdminSupportContract):
    support_action_audit_record_id: str = Field(min_length=1)
    metadata: ContractMetadata
    support_action_id: str = Field(min_length=1)
    support_case_id: str | None = Field(default=None, min_length=1)
    actor_context: SupportActorContext
    subject: SupportSubjectReference
    action_family_reference_id: str = Field(min_length=1)
    reason_code: str = Field(min_length=1)
    requested_command_reference_id: str = Field(min_length=1)
    owning_module_id: str = Field(min_length=1)
    owning_module_outcome_reference_id: str | None = Field(default=None, min_length=1)
    state: SupportActionAuditState
    evidence_references: tuple[SupportEvidenceReference, ...] = ()
    append_style: Literal[True] = True
    contains_secret_material: Literal[False] = False
    raw_payload_retained: Literal[False] = False
    business_state_authority: Literal[False] = False

    @model_validator(mode="after")
    def _validate_evidence(self) -> "SupportActionAuditRecord":
        _reject_duplicate_ids(
            tuple(item.support_evidence_reference_id for item in self.evidence_references),
            "evidence-reference",
        )
        return self


class SupportEscalationRecord(_AdminSupportContract):
    support_escalation_record_id: str = Field(min_length=1)
    metadata: ContractMetadata
    support_case_id: str = Field(min_length=1)
    support_work_item_id: str | None = Field(default=None, min_length=1)
    actor_context: SupportActorContext
    subject: SupportSubjectReference
    evidence_references: tuple[SupportEvidenceReference, ...] = ()
    state: SupportEscalationState
    reason_code: str = Field(min_length=1)
    resolution_reference_id: str | None = Field(default=None, min_length=1)
    fabricated_resolution_authority: Literal[False] = False

    @model_validator(mode="after")
    def _validate_escalation_matrix(self) -> "SupportEscalationRecord":
        if self.state is SupportEscalationState.RESOLVED and self.resolution_reference_id is None:
            raise ValueError("resolved escalation requires resolution reference")
        if (
            self.state is not SupportEscalationState.RESOLVED
            and self.resolution_reference_id is not None
        ):
            raise ValueError("non-resolved escalation cannot carry resolution reference")
        _reject_duplicate_ids(
            tuple(item.support_evidence_reference_id for item in self.evidence_references),
            "evidence-reference",
        )
        return self


__all__ = [
    "SupportCaseState",
    "SupportWorkItemState",
    "SupportSubjectKind",
    "SupportEvidenceKind",
    "SupportFreshnessState",
    "SupportReadState",
    "SupportExplanationState",
    "SupportCommandPreparationState",
    "SupportActionAuditState",
    "SupportEscalationState",
    "SupportActorContext",
    "SupportSubjectReference",
    "SupportEvidenceReference",
    "SupportCase",
    "SupportWorkItem",
    "SupportReadModel",
    "SupportExplanationRecord",
    "SupportCommandEnvelope",
    "SupportActionAuditRecord",
    "SupportEscalationRecord",
]
