"""Pure preparation semantics for Beacon override candidates."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator

from .builder_validation import (
    BuilderDraftValidationOutcome,
    BuilderDraftValidationRequest,
    BuilderServerValueValidationState,
)
from .contracts import (
    BeaconOverrideCandidateOutcome,
    BeaconOverrideCandidateState,
    BuilderDraftValidationState,
    FilterCapabilityState,
    OpaqueReferenceId,
)


class BeaconOverrideCandidatePreparationReason(StrEnum):
    CANDIDATE_PREPARED = "CANDIDATE_PREPARED"
    VALIDATION_RESULT_REFERENCE_MISMATCH = "VALIDATION_RESULT_REFERENCE_MISMATCH"
    CATALOG_VERSION_MISMATCH = "CATALOG_VERSION_MISMATCH"
    BEACON_REVISION_MISMATCH = "BEACON_REVISION_MISMATCH"
    ACCEPTED_FIELD_SET_MISMATCH = "ACCEPTED_FIELD_SET_MISMATCH"
    ACCEPTED_FIELD_INPUT_MISSING = "ACCEPTED_FIELD_INPUT_MISSING"
    ACCEPTED_FIELD_CONTEXT_MISSING = "ACCEPTED_FIELD_CONTEXT_MISSING"
    ACCEPTED_FIELD_CATALOG_VERSION_MISMATCH = "ACCEPTED_FIELD_CATALOG_VERSION_MISMATCH"
    ACCEPTED_FIELD_NOT_VISIBLE = "ACCEPTED_FIELD_NOT_VISIBLE"
    ACCEPTED_FIELD_NOT_ENABLED = "ACCEPTED_FIELD_NOT_ENABLED"
    ACCEPTED_FIELD_NOT_EDITABLE = "ACCEPTED_FIELD_NOT_EDITABLE"
    ACCEPTED_FIELD_SERVER_VALUE_NOT_VALID = "ACCEPTED_FIELD_SERVER_VALUE_NOT_VALID"
    DRAFT_INVALID = "DRAFT_INVALID"
    DRAFT_UNSUPPORTED = "DRAFT_UNSUPPORTED"
    DRAFT_STALE = "DRAFT_STALE"
    DRAFT_CONFLICT = "DRAFT_CONFLICT"
    DRAFT_AMBIGUOUS = "DRAFT_AMBIGUOUS"
    DRAFT_BLOCKED = "DRAFT_BLOCKED"


class _CandidateModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


class BeaconOverrideFieldCandidate(_CandidateModel):
    builder_field_id: OpaqueReferenceId
    filter_definition_id: OpaqueReferenceId
    filter_capability_profile_id: OpaqueReferenceId
    builder_field_projection_outcome_reference_id: OpaqueReferenceId
    server_value_validation_reference_id: OpaqueReferenceId
    value_reference_ids: tuple[OpaqueReferenceId, ...] = ()
    value_sequence_preserved: Literal[True] = True
    beacon_applied: Literal[False] = False
    beacon_authoritative: Literal[False] = False


class BeaconOverrideCandidatePreparationRequest(_CandidateModel):
    beacon_override_candidate_outcome_id: OpaqueReferenceId
    override_candidate_reference_id: OpaqueReferenceId
    beacon_id: OpaqueReferenceId
    filter_catalog_version_id: OpaqueReferenceId
    beacon_revision_id: OpaqueReferenceId
    builder_validation_request: BuilderDraftValidationRequest
    builder_validation_outcome: BuilderDraftValidationOutcome
    catalog_evidence_reference_ids: tuple[OpaqueReferenceId, ...]
    beacon_acceptance_boundary_reference_id: OpaqueReferenceId
    beacon_acceptance_requested: Literal[False] = False
    beacon_mutation_requested: Literal[False] = False
    beacon_revision_creation_requested: Literal[False] = False
    snapshot_acceptance_requested: Literal[False] = False
    lifecycle_transition_requested: Literal[False] = False
    direct_table_write_requested: Literal[False] = False

    @model_validator(mode="after")
    def validate_semantics(self) -> "BeaconOverrideCandidatePreparationRequest":
        if not self.catalog_evidence_reference_ids:
            raise ValueError("catalog_evidence_reference_ids must not be empty")
        if len(self.catalog_evidence_reference_ids) != len(set(self.catalog_evidence_reference_ids)):
            raise ValueError("catalog_evidence_reference_ids must be unique")
        return self


class BeaconOverrideCandidatePreparationResult(_CandidateModel):
    candidate_outcome: BeaconOverrideCandidateOutcome
    builder_draft_id: OpaqueReferenceId
    beacon_acceptance_boundary_reference_id: OpaqueReferenceId
    catalog_evidence_reference_ids: tuple[OpaqueReferenceId, ...]
    field_candidates: tuple[BeaconOverrideFieldCandidate, ...] = ()
    reason_codes: tuple[BeaconOverrideCandidatePreparationReason, ...]
    beacon_acceptance_performed: Literal[False] = False
    beacon_mutation_performed: Literal[False] = False
    beacon_revision_created: Literal[False] = False
    extracted_snapshot_accepted: Literal[False] = False
    source_url_changed: Literal[False] = False
    lifecycle_changed: Literal[False] = False
    historical_revision_rewritten: Literal[False] = False
    direct_table_write_performed: Literal[False] = False
    runtime_or_persistence_performed: Literal[False] = False

    @model_validator(mode="after")
    def validate_semantics(self) -> "BeaconOverrideCandidatePreparationResult":
        if not self.catalog_evidence_reference_ids or len(self.catalog_evidence_reference_ids) != len(set(self.catalog_evidence_reference_ids)):
            raise ValueError("catalog evidence references must be non-empty and unique")
        if not self.reason_codes or len(self.reason_codes) != len(set(self.reason_codes)):
            raise ValueError("reason codes must be non-empty and unique")
        field_ids = tuple(field.builder_field_id for field in self.field_candidates)
        if len(field_ids) != len(set(field_ids)):
            raise ValueError("field candidate IDs must be unique")
        if field_ids != self.candidate_outcome.validated_builder_field_ids:
            raise ValueError("field IDs must equal validated builder field IDs")
        if self.candidate_outcome.candidate_state is BeaconOverrideCandidateState.PREPARED:
            if self.reason_codes != (BeaconOverrideCandidatePreparationReason.CANDIDATE_PREPARED,):
                raise ValueError("prepared result requires CANDIDATE_PREPARED")
        else:
            if self.field_candidates or self.candidate_outcome.validated_builder_field_ids:
                raise ValueError("non-prepared result must not contain field candidates")
            if BeaconOverrideCandidatePreparationReason.CANDIDATE_PREPARED in self.reason_codes:
                raise ValueError("non-prepared result must not contain CANDIDATE_PREPARED")
        return self


_NONVALID_REASONS = {
    BuilderDraftValidationState.INVALID: BeaconOverrideCandidatePreparationReason.DRAFT_INVALID,
    BuilderDraftValidationState.UNSUPPORTED: BeaconOverrideCandidatePreparationReason.DRAFT_UNSUPPORTED,
    BuilderDraftValidationState.STALE: BeaconOverrideCandidatePreparationReason.DRAFT_STALE,
    BuilderDraftValidationState.CONFLICT: BeaconOverrideCandidatePreparationReason.DRAFT_CONFLICT,
    BuilderDraftValidationState.AMBIGUOUS: BeaconOverrideCandidatePreparationReason.DRAFT_AMBIGUOUS,
    BuilderDraftValidationState.BLOCKED: BeaconOverrideCandidatePreparationReason.DRAFT_BLOCKED,
}


def _ordered_reasons(reasons: set[BeaconOverrideCandidatePreparationReason]) -> tuple[BeaconOverrideCandidatePreparationReason, ...]:
    return tuple(reason for reason in BeaconOverrideCandidatePreparationReason if reason in reasons)


def _result(
    request: BeaconOverrideCandidatePreparationRequest,
    state: BeaconOverrideCandidateState,
    reasons: tuple[BeaconOverrideCandidatePreparationReason, ...],
    field_candidates: tuple[BeaconOverrideFieldCandidate, ...] = (),
) -> BeaconOverrideCandidatePreparationResult:
    validation_request = request.builder_validation_request
    validation_result = request.builder_validation_outcome.validation_result
    outcome = BeaconOverrideCandidateOutcome(
        beacon_override_candidate_outcome_id=request.beacon_override_candidate_outcome_id,
        override_candidate_reference_id=request.override_candidate_reference_id,
        beacon_id=request.beacon_id,
        beacon_revision_id=request.beacon_revision_id,
        filter_catalog_version_id=request.filter_catalog_version_id,
        candidate_state=state,
        validated_builder_field_ids=tuple(field.builder_field_id for field in field_candidates),
        warning_ids=validation_result.warning_ids,
    )
    return BeaconOverrideCandidatePreparationResult(
        candidate_outcome=outcome,
        builder_draft_id=validation_request.builder_draft_id,
        beacon_acceptance_boundary_reference_id=request.beacon_acceptance_boundary_reference_id,
        catalog_evidence_reference_ids=request.catalog_evidence_reference_ids,
        field_candidates=field_candidates,
        reason_codes=reasons,
    )


def prepare_beacon_override_candidate(
    request: BeaconOverrideCandidatePreparationRequest,
) -> BeaconOverrideCandidatePreparationResult:
    validation_request = request.builder_validation_request
    validation_outcome = request.builder_validation_outcome
    validation_result = validation_outcome.validation_result
    context = validation_request.server_context
    reference_reasons: set[BeaconOverrideCandidatePreparationReason] = set()
    if validation_result.builder_draft_validation_result_id != validation_request.builder_draft_validation_result_id:
        reference_reasons.add(BeaconOverrideCandidatePreparationReason.VALIDATION_RESULT_REFERENCE_MISMATCH)
    if any(version != request.filter_catalog_version_id for version in (
        validation_request.filter_catalog_version_id,
        context.filter_catalog_version_id,
        validation_result.filter_catalog_version_id,
    )):
        reference_reasons.add(BeaconOverrideCandidatePreparationReason.CATALOG_VERSION_MISMATCH)
    if any(revision != request.beacon_revision_id for revision in (
        validation_request.beacon_revision_id,
        context.beacon_revision_id,
        validation_result.beacon_revision_id,
    )):
        reference_reasons.add(BeaconOverrideCandidatePreparationReason.BEACON_REVISION_MISMATCH)
    if reference_reasons:
        return _result(request, BeaconOverrideCandidateState.CONFLICT, _ordered_reasons(reference_reasons))

    state = validation_result.validation_state
    if state is not BuilderDraftValidationState.VALID:
        return _result(request, {
            BuilderDraftValidationState.INVALID: BeaconOverrideCandidateState.REJECTED,
            BuilderDraftValidationState.UNSUPPORTED: BeaconOverrideCandidateState.UNSUPPORTED,
            BuilderDraftValidationState.STALE: BeaconOverrideCandidateState.STALE,
            BuilderDraftValidationState.CONFLICT: BeaconOverrideCandidateState.CONFLICT,
            BuilderDraftValidationState.AMBIGUOUS: BeaconOverrideCandidateState.AMBIGUOUS,
            BuilderDraftValidationState.BLOCKED: BeaconOverrideCandidateState.BLOCKED,
        }[state], (_NONVALID_REASONS[state],))

    submitted_ids = tuple(field.builder_field_id for field in validation_request.draft_fields)
    accepted_ids = validation_result.accepted_builder_field_ids
    defects: set[BeaconOverrideCandidatePreparationReason] = set()
    if accepted_ids != submitted_ids:
        defects.add(BeaconOverrideCandidatePreparationReason.ACCEPTED_FIELD_SET_MISMATCH)
    inputs = {field.builder_field_id: field for field in validation_request.draft_fields}
    entries = {entry.field_definition.builder_field_id: entry for entry in context.field_entries}
    for field_id in accepted_ids:
        draft_field = inputs.get(field_id)
        entry = entries.get(field_id)
        if draft_field is None:
            defects.add(BeaconOverrideCandidatePreparationReason.ACCEPTED_FIELD_INPUT_MISSING)
        if entry is None:
            defects.add(BeaconOverrideCandidatePreparationReason.ACCEPTED_FIELD_CONTEXT_MISSING)
            continue
        if entry.field_definition.filter_catalog_version_id != request.filter_catalog_version_id:
            defects.add(BeaconOverrideCandidatePreparationReason.ACCEPTED_FIELD_CATALOG_VERSION_MISMATCH)
        if not entry.visible:
            defects.add(BeaconOverrideCandidatePreparationReason.ACCEPTED_FIELD_NOT_VISIBLE)
        if not entry.enabled:
            defects.add(BeaconOverrideCandidatePreparationReason.ACCEPTED_FIELD_NOT_ENABLED)
        if entry.field_definition.capability_state is not FilterCapabilityState.EDITABLE:
            defects.add(BeaconOverrideCandidatePreparationReason.ACCEPTED_FIELD_NOT_EDITABLE)
        if draft_field is None or draft_field.server_value_validation_state is not BuilderServerValueValidationState.VALID or draft_field.server_value_validation_reference_id is None:
            defects.add(BeaconOverrideCandidatePreparationReason.ACCEPTED_FIELD_SERVER_VALUE_NOT_VALID)
    if defects:
        return _result(request, BeaconOverrideCandidateState.CONFLICT, _ordered_reasons(defects))

    fields = tuple(
        BeaconOverrideFieldCandidate(
            builder_field_id=field_id,
            filter_definition_id=entries[field_id].field_definition.filter_definition_id,
            filter_capability_profile_id=entries[field_id].field_definition.filter_capability_profile_id,
            builder_field_projection_outcome_reference_id=entries[field_id].projection_outcome_reference_id,
            server_value_validation_reference_id=inputs[field_id].server_value_validation_reference_id,
            value_reference_ids=inputs[field_id].value_reference_ids,
        )
        for field_id in accepted_ids
    )
    return _result(request, BeaconOverrideCandidateState.PREPARED, (BeaconOverrideCandidatePreparationReason.CANDIDATE_PREPARED,), fields)


__all__ = (
    "BeaconOverrideCandidatePreparationReason",
    "BeaconOverrideFieldCandidate",
    "BeaconOverrideCandidatePreparationRequest",
    "BeaconOverrideCandidatePreparationResult",
    "prepare_beacon_override_candidate",
)
