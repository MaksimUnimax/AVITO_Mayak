"""Transport-neutral Admin & Support anchor action boundary."""

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
from mayak.platform.boundaries import SCAN_ORCHESTRATION_AND_LISTING_STATE_MODULE_ID


class _AdminAnchorContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


_NonEmptyReferenceId = Annotated[str, Field(min_length=1)]


class AdminAnchorActionKind(str, Enum):
    RESET = "RESET"
    REBASE_FROM_CURRENT_TOP_WINDOW = "REBASE_FROM_CURRENT_TOP_WINDOW"
    REVIEW_LOST_ANCHORS_RECOVERY = "REVIEW_LOST_ANCHORS_RECOVERY"


class AdminAnchorActionOutcomeState(str, Enum):
    ANCHOR_STATE_RESET = "ANCHOR_STATE_RESET"
    ANCHOR_STATE_REBASED = "ANCHOR_STATE_REBASED"
    LOST_ANCHORS_RECOVERY_REVIEW_RECORDED = "LOST_ANCHORS_RECOVERY_REVIEW_RECORDED"
    UNCHANGED = "UNCHANGED"
    BLOCKED = "BLOCKED"
    REJECTED = "REJECTED"
    CONFLICT = "CONFLICT"
    AMBIGUOUS = "AMBIGUOUS"


_ACTION_FAMILY_BY_KIND = {
    AdminAnchorActionKind.RESET: "SCAN_RESET_ANCHOR_STATE",
    AdminAnchorActionKind.REBASE_FROM_CURRENT_TOP_WINDOW: (
        "SCAN_REBASE_ANCHOR_STATE_FROM_CURRENT_TOP_WINDOW"
    ),
    AdminAnchorActionKind.REVIEW_LOST_ANCHORS_RECOVERY: (
        "SCAN_MARK_LOST_ANCHORS_RECOVERY_REVIEWED"
    ),
}

_SUCCESSFUL_OUTCOME_BY_KIND = {
    AdminAnchorActionKind.RESET: AdminAnchorActionOutcomeState.ANCHOR_STATE_RESET,
    AdminAnchorActionKind.REBASE_FROM_CURRENT_TOP_WINDOW: (
        AdminAnchorActionOutcomeState.ANCHOR_STATE_REBASED
    ),
    AdminAnchorActionKind.REVIEW_LOST_ANCHORS_RECOVERY: (
        AdminAnchorActionOutcomeState.LOST_ANCHORS_RECOVERY_REVIEW_RECORDED
    ),
}

_AUDIT_STATE_BY_OUTCOME = {
    AdminAnchorActionOutcomeState.ANCHOR_STATE_RESET: SupportActionAuditState.RECORDED,
    AdminAnchorActionOutcomeState.ANCHOR_STATE_REBASED: SupportActionAuditState.RECORDED,
    AdminAnchorActionOutcomeState.LOST_ANCHORS_RECOVERY_REVIEW_RECORDED: (
        SupportActionAuditState.RECORDED
    ),
    AdminAnchorActionOutcomeState.UNCHANGED: SupportActionAuditState.REPLAYED,
    AdminAnchorActionOutcomeState.BLOCKED: SupportActionAuditState.REJECTED,
    AdminAnchorActionOutcomeState.REJECTED: SupportActionAuditState.REJECTED,
    AdminAnchorActionOutcomeState.CONFLICT: SupportActionAuditState.CONFLICT,
    AdminAnchorActionOutcomeState.AMBIGUOUS: SupportActionAuditState.MANUAL_REVIEW_REQUIRED,
}


def _reject_duplicate_references(values: tuple[str, ...], label: str) -> None:
    if any(not value for value in values):
        raise ValueError(f"{label} references must be non-empty")
    if len(values) != len(set(values)):
        raise ValueError(f"duplicate {label} references are not allowed")


def _reject_duplicate_evidence(evidence: tuple[SupportEvidenceReference, ...]) -> None:
    identifiers = tuple(item.support_evidence_reference_id for item in evidence)
    if not identifiers:
        raise ValueError("evidence references must be non-empty")
    _reject_duplicate_references(identifiers, "evidence")


class AdminAnchorStateSummary(_AdminAnchorContract):
    admin_anchor_state_summary_id: str = Field(min_length=1)
    metadata: ContractMetadata
    actor_context: SupportActorContext
    subject: SupportSubjectReference
    beacon_reference_id: str = Field(min_length=1)
    listing_state_scope_reference_id: str = Field(min_length=1)
    anchor_state_reference_id: str | None = Field(default=None, min_length=1)
    baseline_reference_id: str | None = Field(default=None, min_length=1)
    configuration_revision_reference_id: str = Field(min_length=1)
    scan_state_reference_id: str | None = Field(default=None, min_length=1)
    anchor_window_policy_reference_id: str = Field(min_length=1)
    lost_anchors_recovery_reference_id: str | None = Field(default=None, min_length=1)
    latest_fresh_state_reference_id: str | None = Field(default=None, min_length=1)
    state: SupportSafeSummaryState
    freshness: SupportFreshnessState
    provenance_reference_ids: tuple[_NonEmptyReferenceId, ...]
    evidence_references: tuple[SupportEvidenceReference, ...]
    redacted: Literal[True] = True
    safe_reference_only: Literal[True] = True
    contains_secret_material: Literal[False] = False
    raw_avito_payload_retained: Literal[False] = False
    full_listing_archive_retained: Literal[False] = False
    confirmed_new_listing_authority: Literal[False] = False
    clean_no_new_authority: Literal[False] = False
    window_overflow_resolution_authority: Literal[False] = False
    mutation_authority: Literal[False] = False

    @model_validator(mode="after")
    def _validate_summary_matrix(self) -> "AdminAnchorStateSummary":
        if self.subject.owning_module_id != SCAN_ORCHESTRATION_AND_LISTING_STATE_MODULE_ID:
            raise ValueError("subject owner must be Scan Orchestration")
        if self.subject.subject_kind is not SupportSubjectKind.LISTING_STATE:
            raise ValueError("anchor summary subject must be listing state")
        if self.subject.safe_subject_reference_id != self.listing_state_scope_reference_id:
            raise ValueError("listing-state scope must match subject")
        if self.state in {
            SupportSafeSummaryState.AVAILABLE,
            SupportSafeSummaryState.REDACTED,
            SupportSafeSummaryState.STALE,
        }:
            if self.state in {
                SupportSafeSummaryState.AVAILABLE,
                SupportSafeSummaryState.REDACTED,
            } and self.freshness is not SupportFreshnessState.FRESH:
                raise ValueError("available or redacted summary requires fresh freshness")
            if (
                self.state is SupportSafeSummaryState.STALE
                and self.freshness is not SupportFreshnessState.STALE
            ):
                raise ValueError("stale summary requires stale freshness")
            if not self.anchor_state_reference_id or not self.scan_state_reference_id:
                raise ValueError("usable summary requires anchor and scan references")
            if not self.provenance_reference_ids or not self.evidence_references:
                raise ValueError("usable summary requires provenance and evidence")
        if (
            self.state is SupportSafeSummaryState.UNKNOWN
            and self.freshness is not SupportFreshnessState.UNKNOWN
        ):
            raise ValueError("unknown summary requires unknown freshness")
        if (
            self.state is SupportSafeSummaryState.AMBIGUOUS
            and self.freshness is not SupportFreshnessState.AMBIGUOUS
        ):
            raise ValueError("ambiguous summary requires ambiguous freshness")
        if self.state in {
            SupportSafeSummaryState.FORBIDDEN,
            SupportSafeSummaryState.NOT_FOUND_SAFE,
            SupportSafeSummaryState.UNKNOWN,
            SupportSafeSummaryState.AMBIGUOUS,
            SupportSafeSummaryState.UNSUPPORTED,
        } and any(
            reference is not None
            for reference in (
                self.anchor_state_reference_id,
                self.baseline_reference_id,
                self.scan_state_reference_id,
                self.lost_anchors_recovery_reference_id,
                self.latest_fresh_state_reference_id,
            )
        ):
            raise ValueError("non-usable summary cannot carry authoritative references")
        if self.latest_fresh_state_reference_id and not self.lost_anchors_recovery_reference_id:
            raise ValueError("latest-fresh reference requires recovery reference")
        if self.lost_anchors_recovery_reference_id and self.state not in {
            SupportSafeSummaryState.AVAILABLE,
            SupportSafeSummaryState.REDACTED,
            SupportSafeSummaryState.STALE,
        }:
            raise ValueError("recovery references require a usable summary")
        _reject_duplicate_references(self.provenance_reference_ids, "provenance")
        _reject_duplicate_evidence(self.evidence_references)
        return self


class AdminAnchorActionRequest(_AdminAnchorContract):
    admin_anchor_action_request_id: str = Field(min_length=1)
    metadata: ContractMetadata
    command_envelope: SupportCommandEnvelope
    current_state_summary: AdminAnchorStateSummary
    action_kind: AdminAnchorActionKind
    target_beacon_reference_id: str = Field(min_length=1)
    expected_anchor_state_reference_id: str | None = Field(default=None, min_length=1)
    anchor_window_policy_reference_id: str = Field(min_length=1)
    rebase_source_scan_state_reference_id: str | None = Field(default=None, min_length=1)
    lost_anchors_recovery_reference_id: str | None = Field(default=None, min_length=1)
    timestamp_policy_reference_id: str = Field(min_length=1)
    server_authorization_required: Literal[True] = True
    scan_anchor_authority: Literal[True] = True
    fresh_current_state_required: Literal[True] = True
    confirmed_new_listing_authority: Literal[False] = False
    clean_no_new_authority: Literal[False] = False
    window_overflow_resolution_authority: Literal[False] = False
    anchor_window_value_authority: Literal[False] = False
    direct_scan_write_authority: Literal[False] = False
    raw_avito_payload_authority: Literal[False] = False
    full_listing_archive_authority: Literal[False] = False
    business_execution_authority: Literal[False] = False

    @model_validator(mode="after")
    def _validate_request_matrix(self) -> "AdminAnchorActionRequest":
        summary = self.current_state_summary
        envelope = self.command_envelope
        if self.metadata != envelope.metadata or self.metadata.causation_id is None:
            raise ValueError("request metadata must equal envelope metadata and have causation")
        if envelope.owning_module_id != SCAN_ORCHESTRATION_AND_LISTING_STATE_MODULE_ID:
            raise ValueError("anchor envelope must be owned by Scan Orchestration")
        if envelope.subject.owning_module_id != SCAN_ORCHESTRATION_AND_LISTING_STATE_MODULE_ID:
            raise ValueError("anchor subject must be owned by Scan Orchestration")
        if envelope.subject.subject_kind is not SupportSubjectKind.LISTING_STATE:
            raise ValueError("anchor envelope subject must be listing state")
        if envelope.actor_context != summary.actor_context or envelope.subject != summary.subject:
            raise ValueError("envelope actor and subject must match summary")
        if self.target_beacon_reference_id != summary.beacon_reference_id:
            raise ValueError("target Beacon must match summary")
        if envelope.action_family_reference_id != _ACTION_FAMILY_BY_KIND[self.action_kind]:
            raise ValueError("action family does not match action kind")
        _reject_duplicate_evidence(envelope.evidence_references)
        if self.anchor_window_policy_reference_id != summary.anchor_window_policy_reference_id:
            raise ValueError("anchor-window policy must match summary")
        if (summary.anchor_state_reference_id is None) != (
            self.expected_anchor_state_reference_id is None
        ):
            raise ValueError("absent current and expected anchors must align")
        if self.expected_anchor_state_reference_id != summary.anchor_state_reference_id:
            raise ValueError("expected anchor must match current anchor")
        prepared = envelope.state is SupportCommandPreparationState.PREPARED
        if prepared:
            if summary.state not in {
                SupportSafeSummaryState.AVAILABLE,
                SupportSafeSummaryState.REDACTED,
            } or summary.freshness is not SupportFreshnessState.FRESH:
                raise ValueError("prepared action requires fresh available or redacted summary")
            if not summary.anchor_state_reference_id or not self.expected_anchor_state_reference_id:
                raise ValueError("prepared action requires current and expected anchor")
            if not summary.provenance_reference_ids or not summary.evidence_references:
                raise ValueError("prepared action requires summary provenance and evidence")
        if self.action_kind is AdminAnchorActionKind.RESET:
            if (
                self.rebase_source_scan_state_reference_id
                or self.lost_anchors_recovery_reference_id
            ):
                raise ValueError("reset cannot carry rebase or recovery references")
        if self.action_kind is AdminAnchorActionKind.REBASE_FROM_CURRENT_TOP_WINDOW:
            if prepared and (
                self.rebase_source_scan_state_reference_id != summary.scan_state_reference_id
            ):
                raise ValueError("prepared rebase must use current Scan state")
            if self.lost_anchors_recovery_reference_id:
                raise ValueError("rebase cannot carry recovery reference")
        if self.action_kind is AdminAnchorActionKind.REVIEW_LOST_ANCHORS_RECOVERY:
            if prepared and (
                summary.lost_anchors_recovery_reference_id is None
                or self.lost_anchors_recovery_reference_id is None
            ):
                raise ValueError(
                    "prepared recovery review requires current and request recovery references"
                )
            if prepared and (
                self.lost_anchors_recovery_reference_id
                != summary.lost_anchors_recovery_reference_id
            ):
                raise ValueError("prepared recovery review must use current recovery reference")
            if self.rebase_source_scan_state_reference_id:
                raise ValueError("recovery review cannot carry rebase source")
        if not prepared:
            if self.rebase_source_scan_state_reference_id and (
                self.rebase_source_scan_state_reference_id != summary.scan_state_reference_id
            ):
                raise ValueError("rebase source must match summary Scan state")
            if self.lost_anchors_recovery_reference_id and (
                self.lost_anchors_recovery_reference_id
                != summary.lost_anchors_recovery_reference_id
            ):
                raise ValueError("recovery reference must match summary")
        return self


class AdminAnchorActionOutcome(_AdminAnchorContract):
    admin_anchor_action_outcome_id: str = Field(min_length=1)
    metadata: ContractMetadata
    request: AdminAnchorActionRequest
    state: AdminAnchorActionOutcomeState
    scan_anchor_decision_reference_id: str = Field(min_length=1)
    authoritative_anchor_state_reference_id: str | None = Field(default=None, min_length=1)
    authoritative_recovery_reference_id: str | None = Field(default=None, min_length=1)
    audit_record: SupportActionAuditRecord
    evidence_references: tuple[SupportEvidenceReference, ...]
    scan_outcome_authority: Literal[True] = True
    admin_support_anchor_state_authority: Literal[False] = False
    confirmed_new_listing_authority: Literal[False] = False
    clean_no_new_authority: Literal[False] = False
    window_overflow_resolution_authority: Literal[False] = False
    raw_avito_payload_retained: Literal[False] = False
    full_listing_archive_retained: Literal[False] = False
    direct_scan_write_authority: Literal[False] = False
    business_execution_authority: Literal[False] = False

    @model_validator(mode="after")
    def _validate_outcome_matrix(self) -> "AdminAnchorActionOutcome":
        request = self.request
        envelope = request.command_envelope
        if envelope.state is not SupportCommandPreparationState.PREPARED:
            raise ValueError("outcome requires prepared request")
        if envelope.owning_command_reference_id is None:
            raise ValueError("outcome requires owning command reference")
        if self.metadata.correlation_id != request.metadata.correlation_id:
            raise ValueError("outcome correlation must match request")
        if self.metadata.causation_id != request.metadata.message_id:
            raise ValueError("outcome causation must match request message id")
        if self.state in _SUCCESSFUL_OUTCOME_BY_KIND.values() and self.state is not (
            _SUCCESSFUL_OUTCOME_BY_KIND[request.action_kind]
        ):
            raise ValueError("successful outcome does not match action kind")
        successful = self.state in _SUCCESSFUL_OUTCOME_BY_KIND.values()
        if successful or self.state is AdminAnchorActionOutcomeState.UNCHANGED:
            if request.action_kind is AdminAnchorActionKind.REVIEW_LOST_ANCHORS_RECOVERY:
                if (
                    self.authoritative_recovery_reference_id is None
                    or self.authoritative_anchor_state_reference_id is not None
                ):
                    raise ValueError("recovery review requires recovery reference only")
            elif (
                self.authoritative_anchor_state_reference_id is None
                or self.authoritative_recovery_reference_id is not None
            ):
                raise ValueError("reset/rebase requires anchor reference only")
        elif (
            self.authoritative_anchor_state_reference_id
            or self.authoritative_recovery_reference_id
        ):
            raise ValueError("non-success outcome cannot carry authoritative references")
        _reject_duplicate_evidence(self.evidence_references)
        _reject_duplicate_evidence(self.audit_record.evidence_references)
        outcome_ids = {item.support_evidence_reference_id for item in self.evidence_references}
        audit_ids = {
            item.support_evidence_reference_id
            for item in self.audit_record.evidence_references
        }
        if outcome_ids != audit_ids:
            raise ValueError("audit evidence must equal outcome evidence")
        if self.audit_record.support_action_id != envelope.support_action_id:
            raise ValueError("audit support action must match envelope")
        if self.audit_record.support_case_id != envelope.support_case_id:
            raise ValueError("audit support case must match envelope")
        if (
            self.audit_record.actor_context != envelope.actor_context
            or self.audit_record.subject != envelope.subject
        ):
            raise ValueError("audit actor and subject must match envelope")
        if self.audit_record.action_family_reference_id != envelope.action_family_reference_id:
            raise ValueError("audit action family must match envelope")
        if self.audit_record.reason_code != envelope.reason_code:
            raise ValueError("audit reason must match envelope")
        if self.audit_record.requested_command_reference_id != envelope.owning_command_reference_id:
            raise ValueError("audit command reference must match envelope")
        if self.audit_record.owning_module_id != SCAN_ORCHESTRATION_AND_LISTING_STATE_MODULE_ID:
            raise ValueError("audit owner must be Scan Orchestration")
        if (
            self.audit_record.owning_module_outcome_reference_id
            != self.scan_anchor_decision_reference_id
        ):
            raise ValueError("audit outcome must match Scan decision reference")
        if self.audit_record.state is not _AUDIT_STATE_BY_OUTCOME[self.state]:
            raise ValueError("audit state does not match outcome state")
        if self.audit_record.metadata.correlation_id != request.metadata.correlation_id:
            raise ValueError("audit correlation must match request")
        if self.audit_record.metadata.causation_id != self.metadata.message_id:
            raise ValueError("audit causation must match outcome message id")
        return self


__all__ = [
    "AdminAnchorActionKind",
    "AdminAnchorActionOutcomeState",
    "AdminAnchorStateSummary",
    "AdminAnchorActionRequest",
    "AdminAnchorActionOutcome",
]
