"""UI-neutral builder field projection and draft validation semantics."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator

from .contracts import (
    BuilderDraftValidationResult,
    BuilderDraftValidationState,
    BuilderFieldDefinition,
    FilterCapabilityProfile,
    FilterCapabilityState,
    FilterDefinition,
    FilterDefinitionState,
    OpaqueReferenceId,
)


class BuilderFieldProjectionDecision(StrEnum):
    PRODUCED = "PRODUCED"
    BLOCKED = "BLOCKED"


class BuilderFieldProjectionReason(StrEnum):
    FIELD_PRODUCED = "FIELD_PRODUCED"
    DEFINITION_NOT_APPROVED = "DEFINITION_NOT_APPROVED"
    CATALOG_VERSION_MISMATCH = "CATALOG_VERSION_MISMATCH"
    CAPABILITY_PROFILE_NOT_LINKED = "CAPABILITY_PROFILE_NOT_LINKED"


class BuilderServerValueValidationState(StrEnum):
    VALID = "VALID"
    INVALID = "INVALID"
    NOT_EVALUATED = "NOT_EVALUATED"


class BuilderClientValidationState(StrEnum):
    NOT_RUN = "NOT_RUN"
    PASSED = "PASSED"
    FAILED = "FAILED"


class BuilderDraftValidationReason(StrEnum):
    DRAFT_VALID = "DRAFT_VALID"
    CATALOG_VERSION_MISMATCH = "CATALOG_VERSION_MISMATCH"
    BEACON_REVISION_MISMATCH = "BEACON_REVISION_MISMATCH"
    UNKNOWN_FIELD = "UNKNOWN_FIELD"
    FIELD_NOT_VISIBLE = "FIELD_NOT_VISIBLE"
    FIELD_NOT_ENABLED = "FIELD_NOT_ENABLED"
    FIELD_FOUND_NOT_EDITABLE = "FIELD_FOUND_NOT_EDITABLE"
    FIELD_UNSUPPORTED = "FIELD_UNSUPPORTED"
    FIELD_STALE = "FIELD_STALE"
    FIELD_AMBIGUOUS = "FIELD_AMBIGUOUS"
    FIELD_CATEGORY_INCOMPATIBLE = "FIELD_CATEGORY_INCOMPATIBLE"
    FIELD_PROVIDER_CHANGED = "FIELD_PROVIDER_CHANGED"
    FIELD_EVIDENCE_REFRESH_REQUIRED = "FIELD_EVIDENCE_REFRESH_REQUIRED"
    REQUIRED_FIELD_MISSING = "REQUIRED_FIELD_MISSING"
    SERVER_VALUE_INVALID = "SERVER_VALUE_INVALID"
    SERVER_VALUE_NOT_EVALUATED = "SERVER_VALUE_NOT_EVALUATED"
    CLIENT_VALIDATION_ADVISORY_ONLY = "CLIENT_VALIDATION_ADVISORY_ONLY"


class _BuilderValidationModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


class BuilderFieldProjectionRequest(_BuilderValidationModel):
    builder_field_projection_outcome_id: OpaqueReferenceId
    builder_field_id: OpaqueReferenceId
    filter_catalog_version_id: OpaqueReferenceId
    filter_definition: FilterDefinition
    capability_profile: FilterCapabilityProfile
    required: bool


class BuilderFieldProjectionOutcome(_BuilderValidationModel):
    builder_field_projection_outcome_id: OpaqueReferenceId
    decision: BuilderFieldProjectionDecision
    reason_codes: tuple[BuilderFieldProjectionReason, ...]
    field_definition: BuilderFieldDefinition | None = None
    display_grants_editability: Literal[False] = False

    @model_validator(mode="after")
    def validate_semantics(self) -> "BuilderFieldProjectionOutcome":
        if not self.reason_codes or len(self.reason_codes) != len(set(self.reason_codes)):
            raise ValueError("reason_codes must be non-empty and unique")
        if self.decision is BuilderFieldProjectionDecision.PRODUCED:
            if self.field_definition is None or BuilderFieldProjectionReason.FIELD_PRODUCED not in self.reason_codes:
                raise ValueError("produced outcomes require a field and FIELD_PRODUCED")
        else:
            if self.field_definition is not None or BuilderFieldProjectionReason.FIELD_PRODUCED in self.reason_codes:
                raise ValueError("blocked outcomes require no field and no FIELD_PRODUCED")
        return self


class BuilderFieldServerEntry(_BuilderValidationModel):
    field_definition: BuilderFieldDefinition
    projection_outcome_reference_id: OpaqueReferenceId
    visible: bool
    enabled: bool
    server_owned: Literal[True] = True
    client_visibility_authority: Literal[False] = False
    client_enablement_authority: Literal[False] = False

    @model_validator(mode="after")
    def validate_semantics(self) -> "BuilderFieldServerEntry":
        if self.enabled and (not self.visible or self.field_definition.capability_state is not FilterCapabilityState.EDITABLE):
            raise ValueError("enabled fields must be visible and editable")
        return self


class BuilderFieldServerContext(_BuilderValidationModel):
    builder_field_server_context_id: OpaqueReferenceId
    filter_catalog_version_id: OpaqueReferenceId
    beacon_revision_id: OpaqueReferenceId
    field_entries: tuple[BuilderFieldServerEntry, ...] = ()

    @model_validator(mode="after")
    def validate_semantics(self) -> "BuilderFieldServerContext":
        field_ids = tuple(entry.field_definition.builder_field_id for entry in self.field_entries)
        outcome_ids = tuple(entry.projection_outcome_reference_id for entry in self.field_entries)
        if len(field_ids) != len(set(field_ids)):
            raise ValueError("builder field IDs must be unique")
        if len(outcome_ids) != len(set(outcome_ids)):
            raise ValueError("projection outcome references must be unique")
        if any(entry.field_definition.filter_catalog_version_id != self.filter_catalog_version_id for entry in self.field_entries):
            raise ValueError("field catalog version must match context")
        return self


class BuilderDraftFieldInput(_BuilderValidationModel):
    builder_field_id: OpaqueReferenceId
    value_reference_ids: tuple[OpaqueReferenceId, ...] = ()
    server_value_validation_state: BuilderServerValueValidationState
    server_value_validation_reference_id: OpaqueReferenceId | None = None
    client_validation_state: BuilderClientValidationState = BuilderClientValidationState.NOT_RUN
    client_reported_visible: bool | None = None
    client_reported_enabled: bool | None = None

    @model_validator(mode="after")
    def validate_semantics(self) -> "BuilderDraftFieldInput":
        if self.server_value_validation_state in (BuilderServerValueValidationState.VALID, BuilderServerValueValidationState.INVALID):
            if self.server_value_validation_reference_id is None:
                raise ValueError("evaluated server values require a reference")
        elif self.server_value_validation_reference_id is not None:
            raise ValueError("not-evaluated server values must not have a reference")
        return self


class BuilderDraftValidationRequest(_BuilderValidationModel):
    builder_draft_validation_result_id: OpaqueReferenceId
    builder_draft_id: OpaqueReferenceId
    filter_catalog_version_id: OpaqueReferenceId
    beacon_revision_id: OpaqueReferenceId
    server_context: BuilderFieldServerContext
    draft_fields: tuple[BuilderDraftFieldInput, ...] = ()

    @model_validator(mode="after")
    def validate_semantics(self) -> "BuilderDraftValidationRequest":
        ids = tuple(field.builder_field_id for field in self.draft_fields)
        if len(ids) != len(set(ids)):
            raise ValueError("submitted builder field IDs must be unique")
        return self


class BuilderDraftValidationOutcome(_BuilderValidationModel):
    validation_result: BuilderDraftValidationResult
    reason_codes: tuple[BuilderDraftValidationReason, ...]
    client_validation_authoritative: Literal[False] = False
    draft_authoritative_for_beacon: Literal[False] = False
    beacon_mutation_performed: Literal[False] = False
    override_candidate_prepared: Literal[False] = False

    @model_validator(mode="after")
    def validate_semantics(self) -> "BuilderDraftValidationOutcome":
        if not self.reason_codes or len(self.reason_codes) != len(set(self.reason_codes)):
            raise ValueError("reason_codes must be non-empty and unique")
        valid = self.validation_result.validation_state is BuilderDraftValidationState.VALID
        if valid and (BuilderDraftValidationReason.DRAFT_VALID not in self.reason_codes or self.validation_result.rejected_builder_field_ids):
            raise ValueError("valid outcomes require DRAFT_VALID and no rejected fields")
        if not valid and BuilderDraftValidationReason.DRAFT_VALID in self.reason_codes:
            raise ValueError("non-valid outcomes must not contain DRAFT_VALID")
        return self


_CAPABILITY_REASONS = {
    FilterCapabilityState.FOUND_NOT_EDITABLE: BuilderDraftValidationReason.FIELD_FOUND_NOT_EDITABLE,
    FilterCapabilityState.UNSUPPORTED: BuilderDraftValidationReason.FIELD_UNSUPPORTED,
    FilterCapabilityState.STALE: BuilderDraftValidationReason.FIELD_STALE,
    FilterCapabilityState.AMBIGUOUS: BuilderDraftValidationReason.FIELD_AMBIGUOUS,
    FilterCapabilityState.CATEGORY_INCOMPATIBLE: BuilderDraftValidationReason.FIELD_CATEGORY_INCOMPATIBLE,
    FilterCapabilityState.PROVIDER_CHANGED: BuilderDraftValidationReason.FIELD_PROVIDER_CHANGED,
    FilterCapabilityState.EVIDENCE_REFRESH_REQUIRED: BuilderDraftValidationReason.FIELD_EVIDENCE_REFRESH_REQUIRED,
}


def _ordered(values: set[BuilderDraftValidationReason]) -> tuple[BuilderDraftValidationReason, ...]:
    return tuple(reason for reason in BuilderDraftValidationReason if reason in values)


def project_builder_field_definition(request: BuilderFieldProjectionRequest) -> BuilderFieldProjectionOutcome:
    reasons: set[BuilderFieldProjectionReason] = set()
    definition = request.filter_definition
    profile = request.capability_profile
    if definition.definition_state is not FilterDefinitionState.APPROVED:
        reasons.add(BuilderFieldProjectionReason.DEFINITION_NOT_APPROVED)
    if request.filter_catalog_version_id != definition.filter_catalog_version_id or request.filter_catalog_version_id != profile.filter_catalog_version_id:
        reasons.add(BuilderFieldProjectionReason.CATALOG_VERSION_MISMATCH)
    if profile.filter_capability_profile_id not in definition.capability_profile_ids:
        reasons.add(BuilderFieldProjectionReason.CAPABILITY_PROFILE_NOT_LINKED)
    if reasons:
        return BuilderFieldProjectionOutcome(
            builder_field_projection_outcome_id=request.builder_field_projection_outcome_id,
            decision=BuilderFieldProjectionDecision.BLOCKED,
            reason_codes=tuple(reason for reason in BuilderFieldProjectionReason if reason in reasons),
        )
    field = BuilderFieldDefinition(
        builder_field_id=request.builder_field_id,
        filter_catalog_version_id=request.filter_catalog_version_id,
        filter_definition_id=definition.filter_definition_id,
        filter_capability_profile_id=profile.filter_capability_profile_id,
        value_kind=definition.value_kind,
        capability_state=profile.capability_state,
        required=request.required,
        filter_option_ids=definition.filter_option_ids,
        filter_range_definition_id=definition.filter_range_definition_id,
        warning_ids=profile.warning_ids,
    )
    return BuilderFieldProjectionOutcome(
        builder_field_projection_outcome_id=request.builder_field_projection_outcome_id,
        decision=BuilderFieldProjectionDecision.PRODUCED,
        reason_codes=(BuilderFieldProjectionReason.FIELD_PRODUCED,),
        field_definition=field,
    )


def validate_builder_draft(request: BuilderDraftValidationRequest) -> BuilderDraftValidationOutcome:
    context = request.server_context
    entries = {entry.field_definition.builder_field_id: entry for entry in context.field_entries}
    reasons: set[BuilderDraftValidationReason] = set()
    accepted: list[OpaqueReferenceId] = []
    rejected: list[OpaqueReferenceId] = []
    submitted = {field.builder_field_id for field in request.draft_fields}
    version_conflict = request.filter_catalog_version_id != context.filter_catalog_version_id
    beacon_conflict = request.beacon_revision_id != context.beacon_revision_id
    if version_conflict:
        reasons.add(BuilderDraftValidationReason.CATALOG_VERSION_MISMATCH)
    if beacon_conflict:
        reasons.add(BuilderDraftValidationReason.BEACON_REVISION_MISMATCH)
    if version_conflict or beacon_conflict:
        rejected.extend(field.builder_field_id for field in request.draft_fields)
        rejected.extend(entry.field_definition.builder_field_id for entry in context.field_entries if entry.field_definition.required and entry.field_definition.builder_field_id not in submitted)
    else:
        for field in request.draft_fields:
            entry = entries.get(field.builder_field_id)
            field_reasons: set[BuilderDraftValidationReason] = set()
            if entry is None:
                field_reasons.add(BuilderDraftValidationReason.UNKNOWN_FIELD)
            else:
                if not entry.visible:
                    field_reasons.add(BuilderDraftValidationReason.FIELD_NOT_VISIBLE)
                if not entry.enabled:
                    field_reasons.add(BuilderDraftValidationReason.FIELD_NOT_ENABLED)
                capability_reason = _CAPABILITY_REASONS.get(entry.field_definition.capability_state)
                if capability_reason is not None:
                    field_reasons.add(capability_reason)
                if entry.field_definition.required and not field.value_reference_ids:
                    field_reasons.add(BuilderDraftValidationReason.REQUIRED_FIELD_MISSING)
                if field.server_value_validation_state is BuilderServerValueValidationState.INVALID:
                    field_reasons.add(BuilderDraftValidationReason.SERVER_VALUE_INVALID)
                elif field.server_value_validation_state is BuilderServerValueValidationState.NOT_EVALUATED:
                    field_reasons.add(BuilderDraftValidationReason.SERVER_VALUE_NOT_EVALUATED)
            if field.client_validation_state is not BuilderClientValidationState.NOT_RUN:
                reasons.add(BuilderDraftValidationReason.CLIENT_VALIDATION_ADVISORY_ONLY)
            reasons.update(field_reasons)
            (accepted if not field_reasons else rejected).append(field.builder_field_id)
        for entry in context.field_entries:
            if entry.field_definition.required and entry.field_definition.builder_field_id not in submitted:
                rejected.append(entry.field_definition.builder_field_id)
                reasons.add(BuilderDraftValidationReason.REQUIRED_FIELD_MISSING)
    accepted = list(dict.fromkeys(accepted))
    rejected = list(dict.fromkeys(rejected))
    warning_ids: list[OpaqueReferenceId] = []
    warning_subjects = set(submitted) | {
        entry.field_definition.builder_field_id
        for entry in context.field_entries
        if entry.field_definition.required and entry.field_definition.builder_field_id not in submitted
    }
    for entry in context.field_entries:
        if entry.field_definition.builder_field_id in warning_subjects:
            warning_ids.extend(entry.field_definition.warning_ids)
    warning_ids = list(dict.fromkeys(warning_ids))
    if not reasons - {BuilderDraftValidationReason.CLIENT_VALIDATION_ADVISORY_ONLY}:
        state = BuilderDraftValidationState.VALID
        reasons.add(BuilderDraftValidationReason.DRAFT_VALID)
    else:
        if BuilderDraftValidationReason.CATALOG_VERSION_MISMATCH in reasons or BuilderDraftValidationReason.BEACON_REVISION_MISMATCH in reasons:
            state = BuilderDraftValidationState.CONFLICT
        elif BuilderDraftValidationReason.FIELD_STALE in reasons or BuilderDraftValidationReason.FIELD_PROVIDER_CHANGED in reasons or BuilderDraftValidationReason.FIELD_EVIDENCE_REFRESH_REQUIRED in reasons:
            state = BuilderDraftValidationState.STALE
        elif BuilderDraftValidationReason.FIELD_AMBIGUOUS in reasons:
            state = BuilderDraftValidationState.AMBIGUOUS
        elif BuilderDraftValidationReason.FIELD_UNSUPPORTED in reasons or BuilderDraftValidationReason.FIELD_CATEGORY_INCOMPATIBLE in reasons:
            state = BuilderDraftValidationState.UNSUPPORTED
        elif any(reason in reasons for reason in (BuilderDraftValidationReason.FIELD_NOT_VISIBLE, BuilderDraftValidationReason.FIELD_NOT_ENABLED, BuilderDraftValidationReason.FIELD_FOUND_NOT_EDITABLE, BuilderDraftValidationReason.SERVER_VALUE_NOT_EVALUATED)):
            state = BuilderDraftValidationState.BLOCKED
        else:
            state = BuilderDraftValidationState.INVALID
    result = BuilderDraftValidationResult(
        builder_draft_validation_result_id=request.builder_draft_validation_result_id,
        filter_catalog_version_id=context.filter_catalog_version_id,
        beacon_revision_id=context.beacon_revision_id,
        validation_state=state,
        accepted_builder_field_ids=tuple(accepted) if state is not BuilderDraftValidationState.CONFLICT else (),
        rejected_builder_field_ids=tuple(rejected),
        warning_ids=tuple(warning_ids),
        is_authoritative_for_beacon=False,
    )
    return BuilderDraftValidationOutcome(validation_result=result, reason_codes=_ordered(reasons))


__all__ = (
    "BuilderFieldProjectionDecision", "BuilderFieldProjectionReason", "BuilderServerValueValidationState",
    "BuilderClientValidationState", "BuilderDraftValidationReason", "BuilderFieldProjectionRequest",
    "BuilderFieldProjectionOutcome", "BuilderFieldServerEntry", "BuilderFieldServerContext",
    "BuilderDraftFieldInput", "BuilderDraftValidationRequest", "BuilderDraftValidationOutcome",
    "project_builder_field_definition", "validate_builder_draft",
)
