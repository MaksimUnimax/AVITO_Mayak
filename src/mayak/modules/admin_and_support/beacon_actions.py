"""Transport-neutral Admin & Support Beacon support action boundary."""

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
from mayak.platform.boundaries import BEACON_MANAGEMENT_MODULE_ID


class _AdminBeaconSupportContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


_NonEmptyReferenceId = Annotated[str, Field(min_length=1)]


class AdminBeaconSupportActionKind(str, Enum):
    PATCH_CURRENT_CONFIGURATION = "PATCH_CURRENT_CONFIGURATION"


class AdminBeaconPatchFieldSupportState(str, Enum):
    SUPPORTED = "SUPPORTED"
    UNSUPPORTED = "UNSUPPORTED"
    UNCERTAIN = "UNCERTAIN"
    AMBIGUOUS = "AMBIGUOUS"


class AdminBeaconSupportOutcomeState(str, Enum):
    CURRENT_CONFIGURATION_UPDATED = "CURRENT_CONFIGURATION_UPDATED"
    UNCHANGED = "UNCHANGED"
    BLOCKED = "BLOCKED"
    REJECTED = "REJECTED"
    CONFLICT = "CONFLICT"
    AMBIGUOUS = "AMBIGUOUS"


_ACTION_FAMILY_BY_ACTION = {
    AdminBeaconSupportActionKind.PATCH_CURRENT_CONFIGURATION: "BEACON_PATCH_CURRENT_CONFIGURATION",
}
_SUCCESS_STATE_BY_ACTION = {
    AdminBeaconSupportActionKind.PATCH_CURRENT_CONFIGURATION: (
        AdminBeaconSupportOutcomeState.CURRENT_CONFIGURATION_UPDATED
    ),
}
_AUDIT_STATE_BY_OUTCOME = {
    AdminBeaconSupportOutcomeState.CURRENT_CONFIGURATION_UPDATED: SupportActionAuditState.RECORDED,
    AdminBeaconSupportOutcomeState.UNCHANGED: SupportActionAuditState.REPLAYED,
    AdminBeaconSupportOutcomeState.BLOCKED: SupportActionAuditState.REJECTED,
    AdminBeaconSupportOutcomeState.REJECTED: SupportActionAuditState.REJECTED,
    AdminBeaconSupportOutcomeState.CONFLICT: SupportActionAuditState.CONFLICT,
    AdminBeaconSupportOutcomeState.AMBIGUOUS: SupportActionAuditState.MANUAL_REVIEW_REQUIRED,
}


def _reject_duplicate_ids(values: tuple[str, ...], label: str) -> None:
    if any(not value for value in values):
        raise ValueError(f"{label} identifiers must be non-empty")
    if len(values) != len(set(values)):
        raise ValueError(f"duplicate {label} identifiers are not allowed")


def _require_current_references(model: object, label: str) -> None:
    if any(
        getattr(model, name) is None
        for name in (
            "current_configuration_reference_id",
            "current_revision_reference_id",
            "current_authoritative_state_reference_id",
        )
    ):
        raise ValueError(f"{label} requires all current authoritative references")


class AdminBeaconCurrentStateSummary(_AdminBeaconSupportContract):
    admin_beacon_current_state_summary_id: str = Field(min_length=1)
    metadata: ContractMetadata
    actor_context: SupportActorContext
    subject: SupportSubjectReference
    target_beacon_reference_id: str = Field(min_length=1)
    target_account_reference_id: str = Field(min_length=1)
    current_configuration_reference_id: str | None = Field(default=None, min_length=1)
    current_revision_reference_id: str | None = Field(default=None, min_length=1)
    current_authoritative_state_reference_id: str | None = Field(default=None, min_length=1)
    state: SupportSafeSummaryState
    freshness: SupportFreshnessState
    provenance_reference_ids: tuple[_NonEmptyReferenceId, ...] = ()
    evidence_references: tuple[SupportEvidenceReference, ...] = ()
    redacted: Literal[True] = True
    safe_reference_only: Literal[True] = True
    contains_secret_material: Literal[False] = False
    raw_source_url_retained: Literal[False] = False
    raw_parser_payload_retained: Literal[False] = False
    full_revision_history_retained: Literal[False] = False
    mutation_authority: Literal[False] = False

    @model_validator(mode="after")
    def _validate_summary_matrix(self) -> "AdminBeaconCurrentStateSummary":
        if self.subject.owning_module_id != BEACON_MANAGEMENT_MODULE_ID:
            raise ValueError("Beacon summary subject must be owned by Beacon Management")
        if self.subject.subject_kind is not SupportSubjectKind.BEACON:
            raise ValueError("Beacon summary subject must be a Beacon")
        if self.subject.safe_subject_reference_id != self.target_beacon_reference_id:
            raise ValueError("summary subject Beacon reference must match target")
        if self.subject.target_account_reference_id != self.target_account_reference_id:
            raise ValueError("summary subject account reference must match target")
        if self.state in {SupportSafeSummaryState.AVAILABLE, SupportSafeSummaryState.REDACTED}:
            if self.freshness is not SupportFreshnessState.FRESH:
                raise ValueError("usable summary requires fresh state")
            _require_current_references(self, "usable summary")
            if not self.provenance_reference_ids or not self.evidence_references:
                raise ValueError("usable summary requires provenance and evidence")
        elif self.state is SupportSafeSummaryState.STALE:
            if self.freshness is not SupportFreshnessState.STALE:
                raise ValueError("stale summary requires stale freshness")
            _require_current_references(self, "stale summary")
            if not self.provenance_reference_ids or not self.evidence_references:
                raise ValueError("stale summary requires provenance and evidence")
        elif self.state is SupportSafeSummaryState.UNKNOWN:
            if self.freshness is not SupportFreshnessState.UNKNOWN:
                raise ValueError("unknown summary requires unknown freshness")
        elif self.state is SupportSafeSummaryState.AMBIGUOUS:
            if self.freshness is not SupportFreshnessState.AMBIGUOUS:
                raise ValueError("ambiguous summary requires ambiguous freshness")
        if self.state in {
            SupportSafeSummaryState.FORBIDDEN,
            SupportSafeSummaryState.NOT_FOUND_SAFE,
            SupportSafeSummaryState.UNKNOWN,
            SupportSafeSummaryState.AMBIGUOUS,
            SupportSafeSummaryState.UNSUPPORTED,
        } and any(
            ref is not None
            for ref in (
                self.current_configuration_reference_id,
                self.current_revision_reference_id,
                self.current_authoritative_state_reference_id,
            )
        ):
            raise ValueError("non-authoritative summary state cannot carry current references")
        _reject_duplicate_ids(self.provenance_reference_ids, "provenance")
        _reject_duplicate_ids(
            tuple(item.support_evidence_reference_id for item in self.evidence_references),
            "evidence-reference",
        )
        if not self.evidence_references:
            raise ValueError("summary requires evidence")
        return self


class AdminBeaconPatchFieldReference(_AdminBeaconSupportContract):
    admin_beacon_patch_field_reference_id: str = Field(min_length=1)
    field_reference_id: str = Field(min_length=1)
    support_state: AdminBeaconPatchFieldSupportState
    requested_value_reference_id: str = Field(min_length=1)
    parser_filter_evidence_reference_id: str = Field(min_length=1)
    override_evidence_reference_id: str = Field(min_length=1)
    safe_reference_only: Literal[True] = True
    source_url_field: Literal[False] = False
    multivalue_semantics_preserved: Literal[True] = True
    raw_value_retained: Literal[False] = False
    live_validation_performed: Literal[False] = False


class AdminBeaconSupportActionRequest(_AdminBeaconSupportContract):
    admin_beacon_support_action_request_id: str = Field(min_length=1)
    metadata: ContractMetadata
    command_envelope: SupportCommandEnvelope
    current_state_summary: AdminBeaconCurrentStateSummary
    action_kind: AdminBeaconSupportActionKind
    target_beacon_reference_id: str = Field(min_length=1)
    target_account_reference_id: str = Field(min_length=1)
    expected_current_configuration_reference_id: str | None = Field(default=None, min_length=1)
    expected_current_revision_reference_id: str | None = Field(default=None, min_length=1)
    patch_field_references: tuple[AdminBeaconPatchFieldReference, ...]
    timestamp_policy_reference_id: str = Field(min_length=1)
    server_authorization_required: Literal[True] = True
    beacon_configuration_authority: Literal[True] = True
    patch_based_save_required: Literal[True] = True
    authoritative_state_reload_required: Literal[True] = True
    stale_full_form_overwrite_authority: Literal[False] = False
    source_url_live_validation_authority: Literal[False] = False
    parser_implementation_authority: Literal[False] = False
    unsupported_field_mutation_authority: Literal[False] = False
    historical_scan_audit_reinterpretation_authority: Literal[False] = False
    direct_beacon_write_authority: Literal[False] = False
    business_execution_authority: Literal[False] = False

    @model_validator(mode="after")
    def _validate_request_boundary(self) -> "AdminBeaconSupportActionRequest":
        envelope = self.command_envelope
        summary = self.current_state_summary
        if self.metadata != envelope.metadata:
            raise ValueError("request metadata must match envelope metadata")
        if self.metadata.causation_id is None:
            raise ValueError("request metadata requires causation id")
        if envelope.owning_module_id != BEACON_MANAGEMENT_MODULE_ID:
            raise ValueError("envelope must be owned by Beacon Management")
        if envelope.subject.owning_module_id != BEACON_MANAGEMENT_MODULE_ID:
            raise ValueError("envelope subject must be owned by Beacon Management")
        if envelope.subject.subject_kind is not SupportSubjectKind.BEACON:
            raise ValueError("envelope subject must be a Beacon")
        if envelope.subject.safe_subject_reference_id != self.target_beacon_reference_id:
            raise ValueError("envelope subject Beacon reference must match target")
        if envelope.subject.target_account_reference_id != self.target_account_reference_id:
            raise ValueError("envelope subject account reference must match target")
        if envelope.actor_context != summary.actor_context or envelope.subject != summary.subject:
            raise ValueError("envelope actor and subject must match current summary")
        if (self.target_beacon_reference_id, self.target_account_reference_id) != (
            summary.target_beacon_reference_id,
            summary.target_account_reference_id,
        ):
            raise ValueError("request targets must match current summary")
        if envelope.action_family_reference_id != _ACTION_FAMILY_BY_ACTION[self.action_kind]:
            raise ValueError("action family reference does not match action kind")
        if not envelope.evidence_references:
            raise ValueError("envelope requires evidence")
        _reject_duplicate_ids(
            tuple(item.support_evidence_reference_id for item in envelope.evidence_references),
            "evidence-reference",
        )
        if not self.patch_field_references:
            raise ValueError("patch must be non-empty")
        _reject_duplicate_ids(
            tuple(
                item.admin_beacon_patch_field_reference_id for item in self.patch_field_references
            ),
            "patch-reference",
        )
        _reject_duplicate_ids(
            tuple(item.field_reference_id for item in self.patch_field_references),
            "field-reference",
        )
        if any(
            field.support_state is not AdminBeaconPatchFieldSupportState.SUPPORTED
            for field in self.patch_field_references
        ) and envelope.state is not SupportCommandPreparationState.POLICY_BLOCKED:
            raise ValueError("non-supported patch requires policy-blocked envelope")
        if (
            self.expected_current_configuration_reference_id
            != summary.current_configuration_reference_id
        ):
            raise ValueError("expected configuration reference must match summary")
        if self.expected_current_revision_reference_id != summary.current_revision_reference_id:
            raise ValueError("expected revision reference must match summary")
        if envelope.state is SupportCommandPreparationState.PREPARED:
            if summary.state not in {
                SupportSafeSummaryState.AVAILABLE,
                SupportSafeSummaryState.REDACTED,
            }:
                raise ValueError("prepared request requires usable summary")
            if summary.freshness is not SupportFreshnessState.FRESH:
                raise ValueError("prepared request requires fresh summary")
            _require_current_references(summary, "prepared request")
            if (
                not self.expected_current_configuration_reference_id
                or not self.expected_current_revision_reference_id
            ):
                raise ValueError("prepared request requires expected current references")
            if not summary.provenance_reference_ids or not summary.evidence_references:
                raise ValueError("prepared request requires summary provenance and evidence")
        return self


class AdminBeaconSupportActionOutcome(_AdminBeaconSupportContract):
    admin_beacon_support_action_outcome_id: str = Field(min_length=1)
    metadata: ContractMetadata
    request: AdminBeaconSupportActionRequest
    state: AdminBeaconSupportOutcomeState
    beacon_patch_save_decision_reference_id: str = Field(min_length=1)
    authoritative_current_state_reload_reference_id: str | None = Field(default=None, min_length=1)
    authoritative_current_configuration_reference_id: str | None = Field(default=None, min_length=1)
    authoritative_current_revision_reference_id: str | None = Field(default=None, min_length=1)
    audit_record: SupportActionAuditRecord
    evidence_references: tuple[SupportEvidenceReference, ...]
    beacon_outcome_authority: Literal[True] = True
    admin_support_beacon_state_authority: Literal[False] = False
    authoritative_state_reload_required: Literal[True] = True
    stale_full_form_overwrite_authority: Literal[False] = False
    unsupported_field_mutation_authority: Literal[False] = False
    source_url_live_validation_authority: Literal[False] = False
    parser_implementation_authority: Literal[False] = False
    historical_scan_audit_reinterpretation_authority: Literal[False] = False
    direct_beacon_write_authority: Literal[False] = False
    business_execution_authority: Literal[False] = False

    @model_validator(mode="after")
    def _validate_outcome_boundary(self) -> "AdminBeaconSupportActionOutcome":
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
        if self.state is AdminBeaconSupportOutcomeState.CURRENT_CONFIGURATION_UPDATED and (
            self.state is not _SUCCESS_STATE_BY_ACTION[request.action_kind]
        ):
            raise ValueError("successful outcome does not match action kind")
        reload_refs = (
            self.authoritative_current_state_reload_reference_id,
            self.authoritative_current_configuration_reference_id,
            self.authoritative_current_revision_reference_id,
        )
        if self.state in {
            AdminBeaconSupportOutcomeState.CURRENT_CONFIGURATION_UPDATED,
            AdminBeaconSupportOutcomeState.UNCHANGED,
        }:
            if any(ref is None for ref in reload_refs):
                raise ValueError("successful outcome requires authoritative reload references")
            if len(set(reload_refs)) != 3:
                raise ValueError("authoritative reload references must be distinct")
        elif any(ref is not None for ref in reload_refs):
            raise ValueError("non-success outcome cannot carry authoritative reload references")
        if not self.evidence_references:
            raise ValueError("outcome requires evidence")
        evidence_ids = tuple(
            item.support_evidence_reference_id for item in self.evidence_references
        )
        _reject_duplicate_ids(evidence_ids, "evidence-reference")
        audit = self.audit_record
        if (
            tuple(item.support_evidence_reference_id for item in audit.evidence_references)
            != evidence_ids
        ):
            raise ValueError("audit evidence must equal outcome evidence")
        if (
            audit.support_action_id != envelope.support_action_id
            or audit.support_case_id != envelope.support_case_id
            or audit.actor_context != envelope.actor_context
            or audit.subject != envelope.subject
            or audit.action_family_reference_id != envelope.action_family_reference_id
            or audit.reason_code != envelope.reason_code
            or audit.requested_command_reference_id != envelope.owning_command_reference_id
            or audit.owning_module_id != BEACON_MANAGEMENT_MODULE_ID
            or audit.owning_module_outcome_reference_id
            != self.beacon_patch_save_decision_reference_id
            or audit.state is not _AUDIT_STATE_BY_OUTCOME[self.state]
            or audit.metadata.correlation_id != self.metadata.correlation_id
            or audit.metadata.causation_id != self.metadata.causation_id
        ):
            raise ValueError("audit record does not align with outcome and envelope")
        return self


__all__ = [
    "AdminBeaconSupportActionKind",
    "AdminBeaconPatchFieldSupportState",
    "AdminBeaconSupportOutcomeState",
    "AdminBeaconCurrentStateSummary",
    "AdminBeaconPatchFieldReference",
    "AdminBeaconSupportActionRequest",
    "AdminBeaconSupportActionOutcome",
]
