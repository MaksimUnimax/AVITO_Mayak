from __future__ import annotations

from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from mayak.contracts import ContractMetadata
from mayak.modules.admin_and_support.contracts import (
    SupportActorContext,
    SupportEvidenceReference,
    SupportExplanationRecord,
    SupportExplanationState,
    SupportFreshnessState,
    SupportReadModel,
    SupportReadState,
    SupportSubjectReference,
)
from mayak.platform.boundaries import (
    BEACON_MANAGEMENT_MODULE_ID,
    EGRESS_ROUTING_MODULE_ID,
    ENTITLEMENTS_AND_BILLING_MODULE_ID,
    IDENTITY_AND_ACCESS_MODULE_ID,
    MAX_ADAPTER_MODULE_ID,
    NOTIFICATION_DELIVERY_MODULE_ID,
    SCAN_ORCHESTRATION_AND_LISTING_STATE_MODULE_ID,
    TELEGRAM_ADAPTER_MODULE_ID,
)


class _AdminSupportSafeReadContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


_NonEmptyReferenceId = Annotated[str, Field(min_length=1)]


class SupportSummaryFamily(str, Enum):
    ACCOUNT_ROLE = "ACCOUNT_ROLE"
    TARIFF_ACCESS_LIMIT = "TARIFF_ACCESS_LIMIT"
    BEACON = "BEACON"
    SCAN_ANCHOR = "SCAN_ANCHOR"
    NOTIFICATION = "NOTIFICATION"
    EGRESS_ROUTE = "EGRESS_ROUTE"
    TELEGRAM_ADAPTER = "TELEGRAM_ADAPTER"
    MAX_ADAPTER = "MAX_ADAPTER"


class SupportSafeSummaryState(str, Enum):
    AVAILABLE = "AVAILABLE"
    REDACTED = "REDACTED"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND_SAFE = "NOT_FOUND_SAFE"
    STALE = "STALE"
    UNKNOWN = "UNKNOWN"
    AMBIGUOUS = "AMBIGUOUS"
    UNSUPPORTED = "UNSUPPORTED"


_SUMMARY_FAMILY_OWNERS = {
    SupportSummaryFamily.ACCOUNT_ROLE: IDENTITY_AND_ACCESS_MODULE_ID,
    SupportSummaryFamily.TARIFF_ACCESS_LIMIT: ENTITLEMENTS_AND_BILLING_MODULE_ID,
    SupportSummaryFamily.BEACON: BEACON_MANAGEMENT_MODULE_ID,
    SupportSummaryFamily.SCAN_ANCHOR: SCAN_ORCHESTRATION_AND_LISTING_STATE_MODULE_ID,
    SupportSummaryFamily.NOTIFICATION: NOTIFICATION_DELIVERY_MODULE_ID,
    SupportSummaryFamily.EGRESS_ROUTE: EGRESS_ROUTING_MODULE_ID,
    SupportSummaryFamily.TELEGRAM_ADAPTER: TELEGRAM_ADAPTER_MODULE_ID,
    SupportSummaryFamily.MAX_ADAPTER: MAX_ADAPTER_MODULE_ID,
}


def _reject_duplicate_ids(values: tuple[str, ...], label: str) -> None:
    if any(not value for value in values):
        raise ValueError(f"{label} identifiers must be non-empty")
    if len(values) != len(set(values)):
        raise ValueError(f"duplicate {label} identifiers are not allowed")


def _reject_duplicate_families(values: tuple[SupportSummaryFamily, ...]) -> None:
    if len(values) != len(set(values)):
        raise ValueError("duplicate summary families are not allowed")


def _owner_for(family: SupportSummaryFamily) -> str:
    return _SUMMARY_FAMILY_OWNERS[family]


class SupportSafeSummaryReference(_AdminSupportSafeReadContract):
    support_safe_summary_reference_id: str = Field(min_length=1)
    summary_family: SupportSummaryFamily
    owning_module_id: str = Field(min_length=1)
    subject: SupportSubjectReference
    state: SupportSafeSummaryState
    freshness: SupportFreshnessState
    safe_summary_reference_id: str | None = Field(default=None, min_length=1)
    provenance_reference_ids: tuple[_NonEmptyReferenceId, ...] = ()
    evidence_references: tuple[SupportEvidenceReference, ...] = ()
    redaction_policy_reference_id: str = Field(min_length=1)
    reason_code: str = Field(min_length=1)
    ambiguity_reference_id: str | None = Field(default=None, min_length=1)
    safe_reference_only: Literal[True] = True
    redacted: Literal[True] = True
    minimal_personal_data: Literal[True] = True
    contains_secret_material: Literal[False] = False
    raw_provider_payload_retained: Literal[False] = False
    full_personal_data_retained: Literal[False] = False
    foreign_host_resource_accessed: Literal[False] = False
    mutation_authority: Literal[False] = False

    @model_validator(mode="after")
    def _validate_summary_matrix(self) -> "SupportSafeSummaryReference":
        if self.owning_module_id != _owner_for(self.summary_family):
            raise ValueError("summary family owning module does not match")
        if self.state in {
            SupportSafeSummaryState.AVAILABLE,
            SupportSafeSummaryState.REDACTED,
            SupportSafeSummaryState.STALE,
        } and (self.safe_summary_reference_id is None or not self.provenance_reference_ids):
            raise ValueError(
                "available, redacted and stale summaries require safe reference and provenance"
            )
        if self.state in {
            SupportSafeSummaryState.FORBIDDEN,
            SupportSafeSummaryState.NOT_FOUND_SAFE,
            SupportSafeSummaryState.UNKNOWN,
            SupportSafeSummaryState.UNSUPPORTED,
        } and self.safe_summary_reference_id is not None:
            raise ValueError("this summary state cannot carry a safe summary reference")
        if self.safe_summary_reference_id is not None and not self.provenance_reference_ids:
            raise ValueError("safe summary reference requires provenance")
        if (
            self.state is SupportSafeSummaryState.STALE
            and self.freshness is not SupportFreshnessState.STALE
        ):
            raise ValueError("stale summary requires stale freshness")
        if (
            self.state is SupportSafeSummaryState.UNKNOWN
            and self.freshness is not SupportFreshnessState.UNKNOWN
        ):
            raise ValueError("unknown summary requires unknown freshness")
        if self.state is SupportSafeSummaryState.AMBIGUOUS:
            if self.ambiguity_reference_id is None:
                raise ValueError("ambiguous summary requires ambiguity reference")
        elif self.ambiguity_reference_id is not None:
            raise ValueError("non-ambiguous summary cannot carry ambiguity reference")
        _reject_duplicate_ids(self.provenance_reference_ids, "provenance")
        _reject_duplicate_ids(
            tuple(item.support_evidence_reference_id for item in self.evidence_references),
            "evidence-reference",
        )
        return self


class SupportSafeReadRequest(_AdminSupportSafeReadContract):
    support_safe_read_request_id: str = Field(min_length=1)
    metadata: ContractMetadata
    actor_context: SupportActorContext
    primary_subject: SupportSubjectReference
    requested_families: tuple[SupportSummaryFamily, ...]
    tenant_scope_reference_id: str = Field(min_length=1)
    authorization_policy_reference_id: str = Field(min_length=1)
    reason_code: str = Field(min_length=1)
    support_case_id: str | None = Field(default=None, min_length=1)
    evidence_references: tuple[SupportEvidenceReference, ...] = ()
    read_only: Literal[True] = True
    direct_write_authority: Literal[False] = False
    provider_call_authority: Literal[False] = False
    raw_resource_access_authority: Literal[False] = False
    foreign_host_access_authority: Literal[False] = False

    @model_validator(mode="after")
    def _validate_request(self) -> "SupportSafeReadRequest":
        if not self.requested_families:
            raise ValueError("requested families must be non-empty")
        _reject_duplicate_families(self.requested_families)
        if self.primary_subject.tenant_scope_reference_id != self.tenant_scope_reference_id:
            raise ValueError("primary subject tenant scope must match request")
        _reject_duplicate_ids(
            tuple(item.support_evidence_reference_id for item in self.evidence_references),
            "evidence-reference",
        )
        return self


class SupportSafeReadProjection(_AdminSupportSafeReadContract):
    support_safe_read_projection_id: str = Field(min_length=1)
    metadata: ContractMetadata
    request: SupportSafeReadRequest
    read_model: SupportReadModel
    summaries: tuple[SupportSafeSummaryReference, ...] = ()
    evidence_references: tuple[SupportEvidenceReference, ...] = ()
    projection_policy_reference_id: str = Field(min_length=1)
    redacted: Literal[True] = True
    provenance_aware: Literal[True] = True
    unknown_ambiguity_preserved: Literal[True] = True
    mutation_authority: Literal[False] = False
    provider_call_authority: Literal[False] = False

    @model_validator(mode="after")
    def _validate_projection(self) -> "SupportSafeReadProjection":
        if self.read_model.actor_context != self.request.actor_context:
            raise ValueError("read model actor must match request actor")
        if self.read_model.subject != self.request.primary_subject:
            raise ValueError("read model subject must match request subject")
        _reject_duplicate_families(tuple(summary.summary_family for summary in self.summaries))
        _reject_duplicate_ids(
            tuple(summary.support_safe_summary_reference_id for summary in self.summaries),
            "safe-summary-reference",
        )
        for summary in self.summaries:
            if summary.summary_family not in self.request.requested_families:
                raise ValueError("summary family was not requested")
            if summary.subject.tenant_scope_reference_id != self.request.tenant_scope_reference_id:
                raise ValueError("summary subject tenant scope must match request")
        if self.summaries:
            if self.read_model.summary_reference_id != self.support_safe_read_projection_id:
                raise ValueError("summary projection reference must match projection")
            if not all(
                summary.support_safe_summary_reference_id
                in self.read_model.provenance_reference_ids
                for summary in self.summaries
            ):
                raise ValueError("read model must link every summary provenance reference")
        elif self.read_model.summary_reference_id is not None:
            raise ValueError(
                "projection without summaries cannot carry read-model summary reference"
            )
        if self.read_model.state in {
            SupportReadState.AUTHORIZED,
            SupportReadState.REDACTED,
            SupportReadState.STALE,
        } and not self.summaries:
            raise ValueError("authorized, redacted and stale projections require summaries")
        if (
            self.read_model.state
            in {SupportReadState.FORBIDDEN, SupportReadState.NOT_FOUND_SAFE}
            and self.summaries
        ):
            raise ValueError("forbidden or not-found-safe projection cannot carry summaries")
        if (
            self.read_model.state is SupportReadState.STALE
            and self.read_model.freshness is not SupportFreshnessState.STALE
        ):
            raise ValueError("stale projection requires stale freshness")
        if self.read_model.freshness is SupportFreshnessState.FRESH and any(
            summary.freshness is not SupportFreshnessState.FRESH for summary in self.summaries
        ):
            raise ValueError("fresh projection requires fresh summaries")
        if self.read_model.freshness is SupportFreshnessState.STALE and not any(
            summary.freshness is SupportFreshnessState.STALE for summary in self.summaries
        ):
            raise ValueError("stale projection requires a stale summary")
        if self.read_model.freshness is SupportFreshnessState.UNKNOWN and not any(
            summary.freshness is SupportFreshnessState.UNKNOWN for summary in self.summaries
        ):
            raise ValueError("unknown projection requires an unknown summary")
        if self.read_model.freshness is SupportFreshnessState.AMBIGUOUS and not any(
            summary.state is SupportSafeSummaryState.AMBIGUOUS for summary in self.summaries
        ):
            raise ValueError("ambiguous freshness requires an ambiguous summary")
        if self.read_model.state is SupportReadState.AMBIGUOUS and not (
            any(
                summary.state
                in {SupportSafeSummaryState.AMBIGUOUS, SupportSafeSummaryState.UNKNOWN}
                for summary in self.summaries
            )
            or self.evidence_references
        ):
            raise ValueError("ambiguous projection requires ambiguous/unknown summary or evidence")
        _reject_duplicate_ids(
            tuple(item.support_evidence_reference_id for item in self.evidence_references),
            "evidence-reference",
        )
        return self


class SupportSafeExplanationRequest(_AdminSupportSafeReadContract):
    support_safe_explanation_request_id: str = Field(min_length=1)
    metadata: ContractMetadata
    support_case_id: str = Field(min_length=1)
    actor_context: SupportActorContext
    primary_subject: SupportSubjectReference
    read_projection_reference_id: str = Field(min_length=1)
    requested_families: tuple[SupportSummaryFamily, ...]
    reason_code: str = Field(min_length=1)
    evidence_references: tuple[SupportEvidenceReference, ...] = ()
    customer_visible_requested: Literal[False] = False
    mutation_authority: Literal[False] = False

    @model_validator(mode="after")
    def _validate_explanation_request(self) -> "SupportSafeExplanationRequest":
        if not self.requested_families:
            raise ValueError("requested explanation families must be non-empty")
        _reject_duplicate_families(self.requested_families)
        _reject_duplicate_ids(
            tuple(item.support_evidence_reference_id for item in self.evidence_references),
            "evidence-reference",
        )
        return self


class SupportSafeExplanationOutcome(_AdminSupportSafeReadContract):
    support_safe_explanation_outcome_id: str = Field(min_length=1)
    metadata: ContractMetadata
    request: SupportSafeExplanationRequest
    read_projection: SupportSafeReadProjection
    explanation_record: SupportExplanationRecord
    source_summary_reference_ids: tuple[_NonEmptyReferenceId, ...] = ()
    uncertainty_reference_ids: tuple[_NonEmptyReferenceId, ...] = ()
    evidence_references: tuple[SupportEvidenceReference, ...] = ()
    customer_visible: Literal[False] = False
    guessed_value_authority: Literal[False] = False
    contains_secret_material: Literal[False] = False
    raw_provider_payload_retained: Literal[False] = False
    full_personal_data_retained: Literal[False] = False
    mutation_authority: Literal[False] = False

    @model_validator(mode="after")
    def _validate_explanation_outcome(self) -> "SupportSafeExplanationOutcome":
        if (
            self.request.read_projection_reference_id
            != self.read_projection.support_safe_read_projection_id
        ):
            raise ValueError("explanation request projection reference must match projection")
        if self.request.actor_context != self.read_projection.request.actor_context:
            raise ValueError("explanation request actor must match read request actor")
        if self.request.primary_subject != self.read_projection.request.primary_subject:
            raise ValueError("explanation request subject must match read request subject")
        if self.explanation_record.actor_context != self.request.actor_context:
            raise ValueError("explanation record actor must match request actor")
        if self.explanation_record.subject != self.request.primary_subject:
            raise ValueError("explanation record subject must match request subject")
        if self.explanation_record.support_case_id != self.request.support_case_id:
            raise ValueError("explanation record case must match request case")
        if self.explanation_record.read_model_reference_id is not None and (
            self.explanation_record.read_model_reference_id
            != self.read_projection.read_model.support_read_model_id
        ):
            raise ValueError("explanation record read-model reference must match projection")
        if self.explanation_record.state in {
            SupportExplanationState.EXPLAINED,
            SupportExplanationState.PARTIALLY_EXPLAINED,
            SupportExplanationState.STALE,
        } and (
            self.explanation_record.read_model_reference_id
            != self.read_projection.read_model.support_read_model_id
        ):
            raise ValueError("explanation state requires matching read-model reference")
        _reject_duplicate_ids(self.source_summary_reference_ids, "source summary")
        _reject_duplicate_ids(self.uncertainty_reference_ids, "uncertainty")
        summaries_by_id = {
            summary.support_safe_summary_reference_id: summary
            for summary in self.read_projection.summaries
        }
        if any(
            reference_id not in summaries_by_id
            for reference_id in self.source_summary_reference_ids
        ):
            raise ValueError("source summary must be contained in projection")
        if any(
            summaries_by_id[reference_id].summary_family not in self.request.requested_families
            for reference_id in self.source_summary_reference_ids
        ):
            raise ValueError("source summary family was not requested")
        if self.explanation_record.state is SupportExplanationState.EXPLAINED:
            if not self.source_summary_reference_ids or self.uncertainty_reference_ids:
                raise ValueError("explained outcome requires sources and no uncertainty")
        elif self.explanation_record.state is SupportExplanationState.PARTIALLY_EXPLAINED:
            if not self.source_summary_reference_ids or not self.uncertainty_reference_ids:
                raise ValueError("partially explained outcome requires sources and uncertainty")
        elif self.explanation_record.state is SupportExplanationState.STALE:
            if (
                self.read_projection.read_model.freshness is not SupportFreshnessState.STALE
                or not self.source_summary_reference_ids
                or not self.uncertainty_reference_ids
            ):
                raise ValueError("stale outcome requires stale projection, sources and uncertainty")
        elif (
            self.explanation_record.state is SupportExplanationState.AMBIGUOUS
            and not self.uncertainty_reference_ids
        ):
            raise ValueError("ambiguous outcome requires uncertainty")
        _reject_duplicate_ids(
            tuple(item.support_evidence_reference_id for item in self.evidence_references),
            "evidence-reference",
        )
        return self


__all__ = [
    "SupportSummaryFamily",
    "SupportSafeSummaryState",
    "SupportSafeSummaryReference",
    "SupportSafeReadRequest",
    "SupportSafeReadProjection",
    "SupportSafeExplanationRequest",
    "SupportSafeExplanationOutcome",
]
