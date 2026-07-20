"""Transport-neutral Admin & Support case, note and audit semantics."""

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
from mayak.modules.admin_and_support.contracts import (
    SupportActionAuditRecord,
    SupportActionAuditState,
    SupportActorContext,
    SupportCase,
    SupportCaseState,
    SupportCommandPreparationState,
    SupportEvidenceReference,
    SupportSubjectReference,
)
from mayak.platform.boundaries import ADMIN_AND_SUPPORT_MODULE_ID


class _CaseRecordContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


def _ids(values: tuple[SupportEvidenceReference, ...], label: str) -> set[str]:
    result = tuple(item.support_evidence_reference_id for item in values)
    if not result:
        raise ValueError(f"{label} evidence must be non-empty")
    if len(result) != len(set(result)):
        raise ValueError(f"duplicate {label} evidence identifiers are not allowed")
    return set(result)


class SupportCaseActionKind(str, Enum):
    OPEN_CASE = "OPEN_CASE"
    START_WORK = "START_WORK"
    REQUEST_EVIDENCE = "REQUEST_EVIDENCE"
    ESCALATE_CASE = "ESCALATE_CASE"
    RESOLVE_CASE = "RESOLVE_CASE"
    CLOSE_CASE = "CLOSE_CASE"
    REJECT_CASE = "REJECT_CASE"
    RECORD_AMBIGUITY = "RECORD_AMBIGUITY"
    RECORD_INTERNAL_NOTE = "RECORD_INTERNAL_NOTE"


class SupportCaseActionOutcomeState(str, Enum):
    CASE_OPENED = "CASE_OPENED"
    CASE_UPDATED = "CASE_UPDATED"
    CASE_ESCALATED = "CASE_ESCALATED"
    CASE_RESOLVED = "CASE_RESOLVED"
    CASE_CLOSED = "CASE_CLOSED"
    CASE_REJECTED = "CASE_REJECTED"
    CASE_AMBIGUITY_RECORDED = "CASE_AMBIGUITY_RECORDED"
    INTERNAL_NOTE_RECORDED = "INTERNAL_NOTE_RECORDED"
    UNCHANGED = "UNCHANGED"
    BLOCKED = "BLOCKED"
    ACTION_REJECTED = "ACTION_REJECTED"
    CONFLICT = "CONFLICT"
    AMBIGUOUS = "AMBIGUOUS"


class SupportCaseAuditLinkState(str, Enum):
    INITIAL = "INITIAL"
    APPENDED = "APPENDED"


_FAMILY = {
    SupportCaseActionKind.OPEN_CASE: "ADMIN_SUPPORT_OPEN_CASE",
    SupportCaseActionKind.START_WORK: "ADMIN_SUPPORT_START_CASE_WORK",
    SupportCaseActionKind.REQUEST_EVIDENCE: "ADMIN_SUPPORT_REQUEST_CASE_EVIDENCE",
    SupportCaseActionKind.ESCALATE_CASE: "ADMIN_SUPPORT_ESCALATE_CASE",
    SupportCaseActionKind.RESOLVE_CASE: "ADMIN_SUPPORT_RESOLVE_CASE",
    SupportCaseActionKind.CLOSE_CASE: "ADMIN_SUPPORT_CLOSE_CASE",
    SupportCaseActionKind.REJECT_CASE: "ADMIN_SUPPORT_REJECT_CASE",
    SupportCaseActionKind.RECORD_AMBIGUITY: "ADMIN_SUPPORT_RECORD_CASE_AMBIGUITY",
    SupportCaseActionKind.RECORD_INTERNAL_NOTE: "ADMIN_SUPPORT_RECORD_INTERNAL_NOTE",
}
_TARGET = {
    SupportCaseActionKind.OPEN_CASE: SupportCaseState.OPEN,
    SupportCaseActionKind.START_WORK: SupportCaseState.IN_PROGRESS,
    SupportCaseActionKind.REQUEST_EVIDENCE: SupportCaseState.WAITING_FOR_EVIDENCE,
    SupportCaseActionKind.ESCALATE_CASE: SupportCaseState.ESCALATED,
    SupportCaseActionKind.RESOLVE_CASE: SupportCaseState.RESOLVED,
    SupportCaseActionKind.CLOSE_CASE: SupportCaseState.CLOSED,
    SupportCaseActionKind.REJECT_CASE: SupportCaseState.REJECTED,
    SupportCaseActionKind.RECORD_AMBIGUITY: SupportCaseState.AMBIGUOUS,
}
_SUCCESS = {
    SupportCaseActionKind.OPEN_CASE: SupportCaseActionOutcomeState.CASE_OPENED,
    SupportCaseActionKind.START_WORK: SupportCaseActionOutcomeState.CASE_UPDATED,
    SupportCaseActionKind.REQUEST_EVIDENCE: SupportCaseActionOutcomeState.CASE_UPDATED,
    SupportCaseActionKind.ESCALATE_CASE: SupportCaseActionOutcomeState.CASE_ESCALATED,
    SupportCaseActionKind.RESOLVE_CASE: SupportCaseActionOutcomeState.CASE_RESOLVED,
    SupportCaseActionKind.CLOSE_CASE: SupportCaseActionOutcomeState.CASE_CLOSED,
    SupportCaseActionKind.REJECT_CASE: SupportCaseActionOutcomeState.CASE_REJECTED,
    SupportCaseActionKind.RECORD_AMBIGUITY: SupportCaseActionOutcomeState.CASE_AMBIGUITY_RECORDED,
    SupportCaseActionKind.RECORD_INTERNAL_NOTE: (
        SupportCaseActionOutcomeState.INTERNAL_NOTE_RECORDED
    ),
}
_AUDIT = {
    **{state: SupportActionAuditState.RECORDED for state in _SUCCESS.values()},
    SupportCaseActionOutcomeState.UNCHANGED: SupportActionAuditState.REPLAYED,
    SupportCaseActionOutcomeState.BLOCKED: SupportActionAuditState.REJECTED,
    SupportCaseActionOutcomeState.ACTION_REJECTED: SupportActionAuditState.REJECTED,
    SupportCaseActionOutcomeState.CONFLICT: SupportActionAuditState.CONFLICT,
    SupportCaseActionOutcomeState.AMBIGUOUS: SupportActionAuditState.MANUAL_REVIEW_REQUIRED,
}
_NOTE_FIELDS = (
    "safe_note_draft_reference_id",
    "note_redaction_policy_reference_id",
    "note_classification_reference_id",
    "corrects_internal_note_reference_id",
)


class SupportInternalNoteRecord(_CaseRecordContract):
    support_internal_note_record_id: str = Field(min_length=1)
    metadata: ContractMetadata
    support_case_id: str = Field(min_length=1)
    support_work_item_id: str | None = Field(default=None, min_length=1)
    actor_context: SupportActorContext
    subject: SupportSubjectReference
    source_note_draft_reference_id: str = Field(min_length=1)
    safe_note_reference_id: str = Field(min_length=1)
    redaction_policy_reference_id: str = Field(min_length=1)
    classification_reference_id: str = Field(min_length=1)
    reason_code: str = Field(min_length=1)
    corrects_internal_note_reference_id: str | None = Field(default=None, min_length=1)
    evidence_references: tuple[SupportEvidenceReference, ...]
    admin_support_note_record_authority: Literal[True] = True
    internal_only: Literal[True] = True
    customer_visible: Literal[False] = False
    customer_visible_explanation_separate: Literal[True] = True
    redacted: Literal[True] = True
    append_style: Literal[True] = True
    edit_in_place_authority: Literal[False] = False
    delete_authority: Literal[False] = False
    contains_secret_material: Literal[False] = False
    raw_note_text_retained: Literal[False] = False
    raw_payload_retained: Literal[False] = False
    full_private_message_retained: Literal[False] = False
    business_state_authority: Literal[False] = False
    foreign_mutation_authority: Literal[False] = False

    @model_validator(mode="after")
    def _validate_note(self) -> "SupportInternalNoteRecord":
        if self.metadata.causation_id is None:
            raise ValueError("note metadata requires causation id")
        _ids(self.evidence_references, "note")
        if self.source_note_draft_reference_id == self.safe_note_reference_id:
            raise ValueError("source draft and safe note references must differ")
        if self.corrects_internal_note_reference_id in {
            self.support_internal_note_record_id,
            self.source_note_draft_reference_id,
            self.safe_note_reference_id,
        }:
            raise ValueError("correction reference must identify another internal note")
        return self


class SupportCaseActionRequest(_CaseRecordContract):
    support_case_action_request_id: str = Field(min_length=1)
    metadata: ContractMetadata
    support_action_id: str = Field(min_length=1)
    support_case_id: str = Field(min_length=1)
    current_case: SupportCase | None = None
    actor_context: SupportActorContext
    subject: SupportSubjectReference
    action_kind: SupportCaseActionKind
    target_state: SupportCaseState | None = None
    action_family_reference_id: str = Field(min_length=1)
    policy_reference_id: str = Field(min_length=1)
    policy_decision_reference_id: str = Field(min_length=1)
    admin_support_command_reference_id: str | None = Field(default=None, min_length=1)
    state: SupportCommandPreparationState
    reason_code: str = Field(min_length=1)
    idempotency_key: IdempotencyKey
    idempotency_scope: IdempotencyScope
    fingerprint: IdempotencyFingerprint
    support_work_item_id: str | None = Field(default=None, min_length=1)
    safe_note_draft_reference_id: str | None = Field(default=None, min_length=1)
    note_redaction_policy_reference_id: str | None = Field(default=None, min_length=1)
    note_classification_reference_id: str | None = Field(default=None, min_length=1)
    corrects_internal_note_reference_id: str | None = Field(default=None, min_length=1)
    evidence_references: tuple[SupportEvidenceReference, ...]
    admin_support_case_record_authority: Literal[True] = True
    server_authorization_required: Literal[True] = True
    append_style_required: Literal[True] = True
    customer_visible_explanation_separate: Literal[True] = True
    direct_domain_write_authority: Literal[False] = False
    foreign_business_state_authority: Literal[False] = False
    raw_note_text_retained: Literal[False] = False
    contains_secret_material: Literal[False] = False
    provider_call_authority: Literal[False] = False
    persistence_authority: Literal[False] = False
    business_execution_authority: Literal[False] = False

    @model_validator(mode="after")
    def _validate_request(self) -> "SupportCaseActionRequest":
        if self.metadata.causation_id is None:
            raise ValueError("request metadata requires causation id")
        if self.action_family_reference_id != _FAMILY[self.action_kind]:
            raise ValueError("action family does not match action kind")
        _ids(self.evidence_references, "request")
        if (
            self.state is SupportCommandPreparationState.PREPARED
            and self.admin_support_command_reference_id is None
        ):
            raise ValueError("prepared request requires command reference")
        if (
            self.state is not SupportCommandPreparationState.PREPARED
            and self.admin_support_command_reference_id is not None
        ):
            raise ValueError("non-prepared request cannot carry command reference")
        if self.action_kind is SupportCaseActionKind.OPEN_CASE:
            if self.current_case is not None or self.target_state is not SupportCaseState.OPEN:
                raise ValueError("open case requires no current case and OPEN target")
        elif self.action_kind is SupportCaseActionKind.RECORD_INTERNAL_NOTE:
            if (
                self.current_case is None
                or self.target_state is not None
                or any(getattr(self, f) is None for f in _NOTE_FIELDS[:3])
            ):
                raise ValueError(
                    "internal note requires current case, no target, and note references"
                )
        else:
            if (
                self.current_case is None
                or self.current_case.support_case_id != self.support_case_id
                or self.current_case.primary_subject != self.subject
            ):
                raise ValueError("non-open action requires matching current case")
            if self.target_state is not _TARGET[self.action_kind]:
                raise ValueError("target state does not match action kind")
        if self.action_kind is not SupportCaseActionKind.RECORD_INTERNAL_NOTE and any(
            getattr(self, f) is not None for f in _NOTE_FIELDS
        ):
            raise ValueError("non-note action cannot carry note references")
        if (
            self.corrects_internal_note_reference_id is not None
            and self.corrects_internal_note_reference_id == self.safe_note_draft_reference_id
        ):
            raise ValueError("correction reference cannot equal note draft reference")
        return self


class SupportCaseActionOutcome(_CaseRecordContract):
    support_case_action_outcome_id: str = Field(min_length=1)
    metadata: ContractMetadata
    request: SupportCaseActionRequest
    state: SupportCaseActionOutcomeState
    case_action_decision_reference_id: str = Field(min_length=1)
    resulting_case: SupportCase | None = None
    internal_note_record: SupportInternalNoteRecord | None = None
    audit_record: SupportActionAuditRecord
    evidence_references: tuple[SupportEvidenceReference, ...]
    admin_support_case_outcome_authority: Literal[True] = True
    foreign_business_state_authority: Literal[False] = False
    append_style: Literal[True] = True
    customer_visible_explanation_separate: Literal[True] = True
    contains_secret_material: Literal[False] = False
    raw_note_text_retained: Literal[False] = False
    raw_payload_retained: Literal[False] = False
    direct_foreign_write_authority: Literal[False] = False
    persistence_authority: Literal[False] = False

    @model_validator(mode="after")
    def _validate_outcome(self) -> "SupportCaseActionOutcome":
        request = self.request
        if (
            request.state is not SupportCommandPreparationState.PREPARED
            or request.admin_support_command_reference_id is None
        ):
            raise ValueError("outcome requires prepared request and command reference")
        if (
            self.metadata.correlation_id != request.metadata.correlation_id
            or self.metadata.causation_id != request.metadata.message_id
        ):
            raise ValueError("outcome correlation/causation does not link to request")
        outcome_ids = _ids(self.evidence_references, "outcome")
        if outcome_ids != _ids(request.evidence_references, "request"):
            raise ValueError("outcome evidence must equal request evidence")
        if outcome_ids != _ids(self.audit_record.evidence_references, "audit"):
            raise ValueError("audit evidence must equal outcome evidence")
        expected = _SUCCESS[request.action_kind]
        if self.state in set(_SUCCESS.values()) and self.state is not expected:
            raise ValueError("successful outcome does not match action kind")
        successful = self.state in {expected, SupportCaseActionOutcomeState.UNCHANGED}
        if not successful and (
            self.resulting_case is not None or self.internal_note_record is not None
        ):
            raise ValueError("failed outcome cannot carry case or note")
        if successful and self.resulting_case is None:
            raise ValueError("successful or unchanged outcome requires resulting case")
        is_note = request.action_kind is SupportCaseActionKind.RECORD_INTERNAL_NOTE
        if is_note and successful:
            if (
                request.current_case is None
                or self.resulting_case != request.current_case
                or self.internal_note_record is None
            ):
                raise ValueError(
                    "successful internal note must preserve current case and carry note"
                )
            note = self.internal_note_record
            if (
                note.support_case_id,
                note.support_work_item_id,
                note.actor_context,
                note.subject,
                note.reason_code,
            ) != (
                request.support_case_id,
                request.support_work_item_id,
                request.actor_context,
                request.subject,
                request.reason_code,
            ):
                raise ValueError("note identity does not match request")
            if (
                note.source_note_draft_reference_id,
                note.redaction_policy_reference_id,
                note.classification_reference_id,
                note.corrects_internal_note_reference_id,
            ) != (
                request.safe_note_draft_reference_id,
                request.note_redaction_policy_reference_id,
                request.note_classification_reference_id,
                request.corrects_internal_note_reference_id,
            ):
                raise ValueError("note references do not match request")
            if (
                note.metadata.correlation_id != request.metadata.correlation_id
                or note.metadata.causation_id != request.metadata.message_id
                or _ids(note.evidence_references, "note") != outcome_ids
            ):
                raise ValueError("note causation or evidence does not match")
        elif self.internal_note_record is not None:
            raise ValueError("non-note outcome cannot carry internal note")
        if self.resulting_case is not None and not is_note:
            if (
                self.resulting_case.support_case_id != request.support_case_id
                or self.resulting_case.primary_subject != request.subject
            ):
                raise ValueError("resulting case identity must match request")
            if request.action_kind is SupportCaseActionKind.OPEN_CASE:
                if (
                    self.state is not SupportCaseActionOutcomeState.CASE_OPENED
                    or self.resulting_case.state is not SupportCaseState.OPEN
                    or self.resulting_case.opened_by != request.actor_context
                    or _ids(self.resulting_case.evidence_references, "case") != outcome_ids
                ):
                    raise ValueError("open result does not match request")
            elif (
                request.current_case is None
                or self.resulting_case.opened_by != request.current_case.opened_by
            ):
                raise ValueError("lifecycle result must preserve opened-by")
            if (
                self.state is not SupportCaseActionOutcomeState.UNCHANGED
                and self.resulting_case.state is not request.target_state
            ):
                raise ValueError("lifecycle result state does not match request")
            if (
                self.state is not SupportCaseActionOutcomeState.UNCHANGED
                and not outcome_ids.issubset(_ids(self.resulting_case.evidence_references, "case"))
            ):
                raise ValueError("lifecycle result must include request evidence")
        if (
            self.state is SupportCaseActionOutcomeState.UNCHANGED
            and not is_note
            and self.resulting_case != request.current_case
        ):
            raise ValueError("unchanged non-note result must preserve current case")
        if self.audit_record.state is not _AUDIT.get(self.state):
            raise ValueError("audit state does not match outcome")
        audit = self.audit_record
        if (
            audit.support_action_id,
            audit.support_case_id,
            audit.actor_context,
            audit.subject,
            audit.action_family_reference_id,
            audit.reason_code,
            audit.requested_command_reference_id,
            audit.owning_module_id,
            audit.owning_module_outcome_reference_id,
        ) != (
            request.support_action_id,
            request.support_case_id,
            request.actor_context,
            request.subject,
            request.action_family_reference_id,
            request.reason_code,
            request.admin_support_command_reference_id,
            ADMIN_AND_SUPPORT_MODULE_ID,
            self.case_action_decision_reference_id,
        ):
            raise ValueError("audit does not align with outcome")
        if (
            audit.metadata.correlation_id != self.metadata.correlation_id
            or audit.metadata.causation_id != self.metadata.message_id
        ):
            raise ValueError("audit causation does not link to outcome")
        return self


class SupportCaseAuditTrailEntry(_CaseRecordContract):
    support_case_audit_trail_entry_id: str = Field(min_length=1)
    metadata: ContractMetadata
    support_case_id: str = Field(min_length=1)
    actor_context: SupportActorContext
    subject: SupportSubjectReference
    link_state: SupportCaseAuditLinkState
    previous_entry_reference_id: str | None = Field(default=None, min_length=1)
    action_audit_record: SupportActionAuditRecord
    action_outcome_reference_id: str = Field(min_length=1)
    evidence_references: tuple[SupportEvidenceReference, ...]
    append_style: Literal[True] = True
    historical_rewrite_authority: Literal[False] = False
    delete_authority: Literal[False] = False
    customer_visible: Literal[False] = False
    contains_secret_material: Literal[False] = False
    raw_payload_retained: Literal[False] = False
    full_private_message_retained: Literal[False] = False
    business_state_authority: Literal[False] = False

    @model_validator(mode="after")
    def _validate_trail(self) -> "SupportCaseAuditTrailEntry":
        audit = self.action_audit_record
        if (
            self.metadata.correlation_id != audit.metadata.correlation_id
            or self.metadata.causation_id != audit.metadata.message_id
        ):
            raise ValueError("trail metadata must link to audit")
        if (
            audit.support_case_id,
            audit.actor_context,
            audit.subject,
            audit.owning_module_outcome_reference_id,
        ) != (
            self.support_case_id,
            self.actor_context,
            self.subject,
            self.action_outcome_reference_id,
        ):
            raise ValueError("trail entry does not align with audit")
        if _ids(self.evidence_references, "trail") != _ids(audit.evidence_references, "audit"):
            raise ValueError("trail evidence must equal audit evidence")
        if self.link_state is SupportCaseAuditLinkState.INITIAL and (
            self.previous_entry_reference_id is not None
            or audit.action_family_reference_id != "ADMIN_SUPPORT_OPEN_CASE"
            or audit.owning_module_id != ADMIN_AND_SUPPORT_MODULE_ID
        ):
            raise ValueError("initial trail entry must be an Admin & Support opening audit")
        if (
            self.link_state is SupportCaseAuditLinkState.APPENDED
            and self.previous_entry_reference_id is None
        ):
            raise ValueError("appended trail entry requires previous entry reference")
        return self


__all__ = [
    "SupportCaseActionKind",
    "SupportCaseActionOutcomeState",
    "SupportCaseAuditLinkState",
    "SupportInternalNoteRecord",
    "SupportCaseActionRequest",
    "SupportCaseActionOutcome",
    "SupportCaseAuditTrailEntry",
]
