"""Safe, provider-neutral projections for catalog consumers."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator

from .contracts import (
    BeaconOverrideCandidateOutcome,
    BeaconOverrideCandidateState,
    BuilderFieldDefinition,
    CatalogCompatibilityWarning,
    FilterCapabilityProfile,
    FilterCapabilityState,
    FilterDefinition,
    FilterDefinitionState,
    FilterEvidenceReference,
    FilterEvidenceState,
    OpaqueReferenceId,
    SafeLabel,
)


class CatalogSafeReadAudience(StrEnum):
    WEB_CUSTOMER = "WEB_CUSTOMER"
    ADMIN_AUTHORIZED = "ADMIN_AUTHORIZED"


class CatalogSafeReadSurfaceState(StrEnum):
    AVAILABLE = "AVAILABLE"
    REDACTED = "REDACTED"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND_SAFE = "NOT_FOUND_SAFE"


class CatalogSafeReadFreshnessState(StrEnum):
    CURRENT = "CURRENT"
    STALE = "STALE"
    UNKNOWN = "UNKNOWN"
    AMBIGUOUS = "AMBIGUOUS"


class CatalogSafeExplanationCode(StrEnum):
    EDITABLE = "EDITABLE"
    FOUND_NOT_EDITABLE = "FOUND_NOT_EDITABLE"
    UNSUPPORTED = "UNSUPPORTED"
    STALE = "STALE"
    AMBIGUOUS = "AMBIGUOUS"
    CATEGORY_INCOMPATIBLE = "CATEGORY_INCOMPATIBLE"
    PROVIDER_CHANGED = "PROVIDER_CHANGED"
    EVIDENCE_REFRESH_REQUIRED = "EVIDENCE_REFRESH_REQUIRED"
    BEACON_ACCEPTANCE_REQUIRED = "BEACON_ACCEPTANCE_REQUIRED"
    REDACTED = "REDACTED"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND_SAFE = "NOT_FOUND_SAFE"


class _SafeReadModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


class CatalogSafeReadAccessContext(_SafeReadModel):
    audience: CatalogSafeReadAudience
    surface_state: CatalogSafeReadSurfaceState
    access_decision_reference_id: OpaqueReferenceId
    scope_reference_id: OpaqueReferenceId
    identity_authorization_evaluated_elsewhere: Literal[True] = True
    filter_catalog_authorizes_identity: Literal[False] = False


class CatalogSafeFilterReadRequest(_SafeReadModel):
    catalog_safe_filter_read_model_id: OpaqueReferenceId
    access_context: CatalogSafeReadAccessContext
    filter_catalog_version_id: OpaqueReferenceId
    filter_definition: FilterDefinition | None = None
    capability_profile: FilterCapabilityProfile | None = None
    builder_field_definition: BuilderFieldDefinition | None = None
    evidence_references: tuple[FilterEvidenceReference, ...] = ()
    compatibility_warnings: tuple[CatalogCompatibilityWarning, ...] = ()
    beacon_override_candidate_outcome: BeaconOverrideCandidateOutcome | None = None
    provenance_reference_ids: tuple[OpaqueReferenceId, ...]

    @model_validator(mode="after")
    def validate_semantics(self) -> "CatalogSafeFilterReadRequest":
        if not self.provenance_reference_ids or len(self.provenance_reference_ids) != len(set(self.provenance_reference_ids)):
            raise ValueError("provenance_reference_ids must be non-empty and unique")

        state = self.access_context.surface_state
        if state is not CatalogSafeReadSurfaceState.AVAILABLE:
            if any((self.filter_definition, self.capability_profile, self.builder_field_definition, self.beacon_override_candidate_outcome)):
                raise ValueError("non-available reads must not contain subject records")
            if self.evidence_references or self.compatibility_warnings:
                raise ValueError("non-available reads must not contain evidence or warnings")
            return self

        definition = self.filter_definition
        profile = self.capability_profile
        if definition is None or profile is None:
            raise ValueError("available reads require definition and capability profile")
        if definition.definition_state is not FilterDefinitionState.APPROVED:
            raise ValueError("available reads require an approved definition")
        if definition.filter_catalog_version_id != self.filter_catalog_version_id or profile.filter_catalog_version_id != self.filter_catalog_version_id:
            raise ValueError("definition and profile catalog versions must match")
        if profile.filter_capability_profile_id not in definition.capability_profile_ids:
            raise ValueError("capability profile is not referenced by the definition")

        evidence_ids = tuple(evidence.evidence_reference_id for evidence in self.evidence_references)
        if len(evidence_ids) != len(set(evidence_ids)):
            raise ValueError("evidence reference IDs must be unique")
        expected_evidence_ids = set(definition.evidence_reference_ids) | set(profile.evidence_reference_ids)
        if set(evidence_ids) != expected_evidence_ids:
            raise ValueError("supplied evidence IDs must exactly cover definition and profile evidence")

        warning_ids = tuple(warning.catalog_compatibility_warning_id for warning in self.compatibility_warnings)
        if len(warning_ids) != len(set(warning_ids)):
            raise ValueError("warning IDs must be unique")
        expected_warning_ids = list(profile.warning_ids)
        if self.builder_field_definition is not None:
            expected_warning_ids.extend(self.builder_field_definition.warning_ids)
        if set(warning_ids) != set(expected_warning_ids) or len(expected_warning_ids) != len(set(expected_warning_ids)):
            raise ValueError("supplied warning IDs must exactly cover expected warnings")
        subjects = {definition.filter_definition_id, profile.filter_capability_profile_id}
        builder = self.builder_field_definition
        if builder is not None:
            subjects.add(builder.builder_field_id)
        for warning in self.compatibility_warnings:
            if warning.subject_reference_id not in subjects:
                raise ValueError("warning subject is outside the request")
            if not set(warning.evidence_reference_ids).issubset(set(evidence_ids)):
                raise ValueError("warning evidence must be supplied")

        if builder is not None:
            if (
                builder.filter_catalog_version_id != self.filter_catalog_version_id
                or builder.filter_definition_id != definition.filter_definition_id
                or builder.filter_capability_profile_id != profile.filter_capability_profile_id
                or builder.capability_state is not profile.capability_state
            ):
                raise ValueError("builder field does not exactly match the definition and profile")
        candidate = self.beacon_override_candidate_outcome
        if candidate is not None:
            if builder is None:
                raise ValueError("candidate outcome requires a builder field")
            if candidate.candidate_state is not BeaconOverrideCandidateState.PREPARED:
                raise ValueError("candidate outcome must be prepared")
            if candidate.filter_catalog_version_id != self.filter_catalog_version_id:
                raise ValueError("candidate catalog version must match")
            if builder.builder_field_id not in candidate.validated_builder_field_ids:
                raise ValueError("candidate must contain the builder field")
            if not candidate.beacon_acceptance_required:
                raise ValueError("candidate must require Beacon acceptance")
            if profile.capability_state is not FilterCapabilityState.EDITABLE:
                raise ValueError("candidate is forbidden for a non-editable capability")
        return self


class CatalogSafeFilterReadModel(_SafeReadModel):
    catalog_safe_filter_read_model_id: OpaqueReferenceId
    audience: CatalogSafeReadAudience
    surface_state: CatalogSafeReadSurfaceState
    freshness_state: CatalogSafeReadFreshnessState
    filter_catalog_version_id: OpaqueReferenceId
    filter_definition_id: OpaqueReferenceId | None = None
    builder_field_id: OpaqueReferenceId | None = None
    filter_capability_profile_id: OpaqueReferenceId | None = None
    safe_label: SafeLabel | None = None
    capability_state: FilterCapabilityState | None = None
    explanation_codes: tuple[CatalogSafeExplanationCode, ...]
    warning_ids: tuple[OpaqueReferenceId, ...] = ()
    evidence_reference_ids: tuple[OpaqueReferenceId, ...] = ()
    provenance_reference_ids: tuple[OpaqueReferenceId, ...]
    beacon_override_candidate_outcome_reference_id: OpaqueReferenceId | None = None
    beacon_acceptance_required: bool = False
    details_redacted: bool
    identity_authorization_performed_by_filter_catalog: Literal[False] = False
    authoritative_business_state: Literal[False] = False
    beacon_acceptance_performed: Literal[False] = False
    contains_raw_provider_payload: Literal[False] = False
    contains_stack_trace: Literal[False] = False
    contains_secret_or_personal_data: Literal[False] = False
    contains_admin_private_notes: Literal[False] = False
    runtime_or_persistence_performed: Literal[False] = False

    @model_validator(mode="after")
    def validate_semantics(self) -> "CatalogSafeFilterReadModel":
        if not self.explanation_codes or len(self.explanation_codes) != len(set(self.explanation_codes)):
            raise ValueError("explanation_codes must be non-empty and unique")
        if not self.provenance_reference_ids or len(self.provenance_reference_ids) != len(set(self.provenance_reference_ids)):
            raise ValueError("provenance_reference_ids must be non-empty and unique")
        if self.surface_state is not CatalogSafeReadSurfaceState.AVAILABLE:
            expected = {
                CatalogSafeReadSurfaceState.REDACTED: CatalogSafeExplanationCode.REDACTED,
                CatalogSafeReadSurfaceState.FORBIDDEN: CatalogSafeExplanationCode.FORBIDDEN,
                CatalogSafeReadSurfaceState.NOT_FOUND_SAFE: CatalogSafeExplanationCode.NOT_FOUND_SAFE,
            }[self.surface_state]
            if any((self.filter_definition_id, self.builder_field_id, self.filter_capability_profile_id, self.safe_label, self.capability_state)):
                raise ValueError("non-available model must not contain subject details")
            if self.warning_ids or self.evidence_reference_ids or self.beacon_override_candidate_outcome_reference_id:
                raise ValueError("non-available model must not contain safe subject references")
            if self.beacon_acceptance_required or not self.details_redacted or self.freshness_state is not CatalogSafeReadFreshnessState.UNKNOWN:
                raise ValueError("non-available model invariant failed")
            if self.explanation_codes != (expected,):
                raise ValueError("non-available model requires one exact explanation")
        else:
            if any(value is None for value in (self.filter_definition_id, self.filter_capability_profile_id, self.safe_label, self.capability_state)):
                raise ValueError("available model requires definition, profile, label and capability")
            if self.explanation_codes[0].value != self.capability_state.value:
                raise ValueError("first explanation must map capability state")
            if len(self.explanation_codes) > 2 or (len(self.explanation_codes) == 2 and self.explanation_codes[1] is not CatalogSafeExplanationCode.BEACON_ACCEPTANCE_REQUIRED):
                raise ValueError("available model explanation sequence is invalid")
            if self.beacon_acceptance_required != (len(self.explanation_codes) == 2):
                raise ValueError("Beacon acceptance flag must match explanation")
            if self.audience is CatalogSafeReadAudience.WEB_CUSTOMER and (
                self.warning_ids or self.evidence_reference_ids or self.beacon_override_candidate_outcome_reference_id or not self.details_redacted
            ):
                raise ValueError("customer model must redact safe details")
            if self.audience is CatalogSafeReadAudience.ADMIN_AUTHORIZED and self.details_redacted:
                raise ValueError("authorized admin model must preserve safe details")
        return self


def _derive_freshness(evidence_references: tuple[FilterEvidenceReference, ...]) -> CatalogSafeReadFreshnessState:
    states = {evidence.evidence_state for evidence in evidence_references}
    if FilterEvidenceState.AMBIGUOUS in states or FilterEvidenceState.CONTRADICTORY in states:
        return CatalogSafeReadFreshnessState.AMBIGUOUS
    if FilterEvidenceState.STALE in states:
        return CatalogSafeReadFreshnessState.STALE
    if states & {FilterEvidenceState.MISSING, FilterEvidenceState.UNSUPPORTED, FilterEvidenceState.RESTRICTED}:
        return CatalogSafeReadFreshnessState.UNKNOWN
    if states and states == {FilterEvidenceState.CURRENT}:
        return CatalogSafeReadFreshnessState.CURRENT
    return CatalogSafeReadFreshnessState.UNKNOWN


def project_catalog_safe_filter_read(request: CatalogSafeFilterReadRequest) -> CatalogSafeFilterReadModel:
    """Project one validated request into a deterministic safe read model."""
    context = request.access_context
    if context.surface_state is not CatalogSafeReadSurfaceState.AVAILABLE:
        return CatalogSafeFilterReadModel(
            catalog_safe_filter_read_model_id=request.catalog_safe_filter_read_model_id,
            audience=context.audience,
            surface_state=context.surface_state,
            freshness_state=CatalogSafeReadFreshnessState.UNKNOWN,
            filter_catalog_version_id=request.filter_catalog_version_id,
            explanation_codes=(CatalogSafeExplanationCode(context.surface_state.value),),
            provenance_reference_ids=request.provenance_reference_ids,
            details_redacted=True,
        )

    definition = request.filter_definition
    profile = request.capability_profile
    builder = request.builder_field_definition
    candidate = request.beacon_override_candidate_outcome
    explanations = [CatalogSafeExplanationCode(profile.capability_state.value)]
    if candidate is not None:
        explanations.append(CatalogSafeExplanationCode.BEACON_ACCEPTANCE_REQUIRED)
    customer = context.audience is CatalogSafeReadAudience.WEB_CUSTOMER
    return CatalogSafeFilterReadModel(
        catalog_safe_filter_read_model_id=request.catalog_safe_filter_read_model_id,
        audience=context.audience,
        surface_state=context.surface_state,
        freshness_state=_derive_freshness(request.evidence_references),
        filter_catalog_version_id=request.filter_catalog_version_id,
        filter_definition_id=definition.filter_definition_id,
        builder_field_id=builder.builder_field_id if builder is not None else None,
        filter_capability_profile_id=profile.filter_capability_profile_id,
        safe_label=definition.safe_label,
        capability_state=profile.capability_state,
        explanation_codes=tuple(explanations),
        warning_ids=() if customer else tuple(warning.catalog_compatibility_warning_id for warning in request.compatibility_warnings),
        evidence_reference_ids=() if customer else tuple(evidence.evidence_reference_id for evidence in request.evidence_references),
        provenance_reference_ids=request.provenance_reference_ids,
        beacon_override_candidate_outcome_reference_id=None if customer or candidate is None else candidate.beacon_override_candidate_outcome_id,
        beacon_acceptance_required=candidate is not None,
        details_redacted=customer,
    )


__all__ = (
    "CatalogSafeReadAudience",
    "CatalogSafeReadSurfaceState",
    "CatalogSafeReadFreshnessState",
    "CatalogSafeExplanationCode",
    "CatalogSafeReadAccessContext",
    "CatalogSafeFilterReadRequest",
    "CatalogSafeFilterReadModel",
    "project_catalog_safe_filter_read",
)
