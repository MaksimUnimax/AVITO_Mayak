"""Provider-neutral semantic contracts for Filter Catalog & Builder."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, StringConstraints, model_validator


OpaqueReferenceId = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=128, pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
]
SafeCode = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=96, pattern=r"^[A-Z0-9_]+$")
]
Sha256Hex = Annotated[str, StringConstraints(min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$")]
SafeLabel = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=160, pattern=r"^[^\x00-\x1f\x7f]*$")
]


class CatalogPublicationState(StrEnum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    SUPERSEDED = "SUPERSEDED"


class FilterDefinitionState(StrEnum):
    PROPOSED = "PROPOSED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    DEPRECATED = "DEPRECATED"
    SUPERSEDED = "SUPERSEDED"
    BLOCKED = "BLOCKED"


class FilterValueKind(StrEnum):
    SCALAR = "SCALAR"
    TEXT = "TEXT"
    MULTIVALUE = "MULTIVALUE"
    RANGE = "RANGE"
    REFERENCE = "REFERENCE"


class FilterEvidenceState(StrEnum):
    CURRENT = "CURRENT"
    STALE = "STALE"
    MISSING = "MISSING"
    CONTRADICTORY = "CONTRADICTORY"
    UNSUPPORTED = "UNSUPPORTED"
    AMBIGUOUS = "AMBIGUOUS"
    RESTRICTED = "RESTRICTED"


class FilterCapabilityState(StrEnum):
    EDITABLE = "EDITABLE"
    FOUND_NOT_EDITABLE = "FOUND_NOT_EDITABLE"
    UNSUPPORTED = "UNSUPPORTED"
    STALE = "STALE"
    AMBIGUOUS = "AMBIGUOUS"
    CATEGORY_INCOMPATIBLE = "CATEGORY_INCOMPATIBLE"
    PROVIDER_CHANGED = "PROVIDER_CHANGED"
    EVIDENCE_REFRESH_REQUIRED = "EVIDENCE_REFRESH_REQUIRED"


class FilterDependencyKind(StrEnum):
    REQUIRES = "REQUIRES"
    EXCLUDES = "EXCLUDES"
    CONSTRAINS = "CONSTRAINS"


class BuilderDraftValidationState(StrEnum):
    VALID = "VALID"
    INVALID = "INVALID"
    UNSUPPORTED = "UNSUPPORTED"
    STALE = "STALE"
    CONFLICT = "CONFLICT"
    AMBIGUOUS = "AMBIGUOUS"
    BLOCKED = "BLOCKED"


class BeaconOverrideCandidateState(StrEnum):
    PREPARED = "PREPARED"
    REJECTED = "REJECTED"
    UNSUPPORTED = "UNSUPPORTED"
    STALE = "STALE"
    CONFLICT = "CONFLICT"
    AMBIGUOUS = "AMBIGUOUS"
    BLOCKED = "BLOCKED"


class CatalogCompatibilityState(StrEnum):
    COMPATIBLE = "COMPATIBLE"
    CHANGED_COMPATIBLE = "CHANGED_COMPATIBLE"
    CHANGED_BREAKING = "CHANGED_BREAKING"
    UNSUPPORTED = "UNSUPPORTED"
    STALE = "STALE"
    AMBIGUOUS = "AMBIGUOUS"
    UNKNOWN = "UNKNOWN"


class _FilterCatalogContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


def _unique(values: tuple[str, ...], name: str, *, required: bool = False) -> None:
    if required and not values:
        raise ValueError(f"{name} must not be empty")
    if len(values) != len(set(values)):
        raise ValueError(f"{name} must contain unique references")


def _aware(value: datetime, name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")


def _range_rules(lower: Decimal | None, upper: Decimal | None, step: Decimal | None) -> None:
    if lower is None and upper is None:
        raise ValueError("at least one range boundary is required")
    if lower is not None and upper is not None and lower > upper:
        raise ValueError("lower_bound must not exceed upper_bound")
    if step is not None and step <= 0:
        raise ValueError("step must be strictly positive")


class FilterEvidenceReference(_FilterCatalogContract):
    evidence_reference_id: OpaqueReferenceId
    evidence_state: FilterEvidenceState
    evidence_kind_code: SafeCode
    scope_reference_ids: tuple[OpaqueReferenceId, ...]
    source_fingerprint: Sha256Hex
    observed_at: datetime
    limitations: tuple[SafeCode, ...] = ()
    refresh_required: bool
    parser_observation_reference_id: OpaqueReferenceId | None = None

    @model_validator(mode="after")
    def validate_semantics(self) -> "FilterEvidenceReference":
        _unique(self.scope_reference_ids, "scope_reference_ids", required=True)
        _unique(self.limitations, "limitations")
        _aware(self.observed_at, "observed_at")
        return self


class FilterCatalogVersion(_FilterCatalogContract):
    filter_catalog_version_id: OpaqueReferenceId
    publication_state: CatalogPublicationState
    created_at: datetime
    published_at: datetime | None = None
    supersedes_catalog_version_id: OpaqueReferenceId | None = None
    evidence_reference_ids: tuple[OpaqueReferenceId, ...]
    filter_definition_ids: tuple[OpaqueReferenceId, ...] = ()

    @model_validator(mode="after")
    def validate_semantics(self) -> "FilterCatalogVersion":
        _aware(self.created_at, "created_at")
        if self.published_at is not None:
            _aware(self.published_at, "published_at")
        if self.publication_state in (CatalogPublicationState.PUBLISHED, CatalogPublicationState.SUPERSEDED) and self.published_at is None:
            raise ValueError("published and superseded versions require published_at")
        if self.publication_state is CatalogPublicationState.DRAFT and self.published_at is not None:
            raise ValueError("draft versions must not have published_at")
        if self.supersedes_catalog_version_id == self.filter_catalog_version_id:
            raise ValueError("a catalog version must not supersede itself")
        _unique(self.evidence_reference_ids, "evidence_reference_ids")
        _unique(self.filter_definition_ids, "filter_definition_ids")
        return self


class FilterOptionDefinition(_FilterCatalogContract):
    filter_option_id: OpaqueReferenceId
    filter_definition_id: OpaqueReferenceId
    canonical_value_code: SafeCode
    safe_label: SafeLabel
    definition_state: FilterDefinitionState
    evidence_reference_ids: tuple[OpaqueReferenceId, ...]

    @model_validator(mode="after")
    def validate_semantics(self) -> "FilterOptionDefinition":
        _unique(self.evidence_reference_ids, "evidence_reference_ids", required=True)
        return self


class FilterRangeDefinition(_FilterCatalogContract):
    filter_range_definition_id: OpaqueReferenceId
    filter_definition_id: OpaqueReferenceId
    unit_code: SafeCode
    lower_bound: Decimal | None = None
    upper_bound: Decimal | None = None
    lower_inclusive: bool
    upper_inclusive: bool
    step: Decimal | None = None
    evidence_reference_ids: tuple[OpaqueReferenceId, ...]

    @model_validator(mode="after")
    def validate_semantics(self) -> "FilterRangeDefinition":
        _range_rules(self.lower_bound, self.upper_bound, self.step)
        _unique(self.evidence_reference_ids, "evidence_reference_ids", required=True)
        return self


class FilterDependencyRule(_FilterCatalogContract):
    filter_dependency_rule_id: OpaqueReferenceId
    source_filter_definition_id: OpaqueReferenceId
    target_filter_definition_id: OpaqueReferenceId
    dependency_kind: FilterDependencyKind
    condition_code: SafeCode
    outcome_code: SafeCode
    evidence_reference_ids: tuple[OpaqueReferenceId, ...]

    @model_validator(mode="after")
    def validate_semantics(self) -> "FilterDependencyRule":
        if self.source_filter_definition_id == self.target_filter_definition_id:
            raise ValueError("source and target filter definitions must differ")
        _unique(self.evidence_reference_ids, "evidence_reference_ids", required=True)
        return self


class FilterCapabilityProfile(_FilterCatalogContract):
    filter_capability_profile_id: OpaqueReferenceId
    filter_catalog_version_id: OpaqueReferenceId
    provider_surface_reference_id: OpaqueReferenceId
    category_scope_reference_id: OpaqueReferenceId | None = None
    geography_scope_reference_id: OpaqueReferenceId | None = None
    capability_state: FilterCapabilityState
    evidence_reference_ids: tuple[OpaqueReferenceId, ...]
    warning_ids: tuple[OpaqueReferenceId, ...] = ()

    @model_validator(mode="after")
    def validate_semantics(self) -> "FilterCapabilityProfile":
        _unique(self.evidence_reference_ids, "evidence_reference_ids", required=True)
        _unique(self.warning_ids, "warning_ids")
        return self


class FilterDefinition(_FilterCatalogContract):
    filter_definition_id: OpaqueReferenceId
    filter_catalog_version_id: OpaqueReferenceId
    normalized_key: SafeCode
    safe_label: SafeLabel
    value_kind: FilterValueKind
    definition_state: FilterDefinitionState
    evidence_reference_ids: tuple[OpaqueReferenceId, ...]
    capability_profile_ids: tuple[OpaqueReferenceId, ...]
    filter_option_ids: tuple[OpaqueReferenceId, ...] = ()
    filter_range_definition_id: OpaqueReferenceId | None = None
    dependency_rule_ids: tuple[OpaqueReferenceId, ...] = ()
    supersedes_filter_definition_id: OpaqueReferenceId | None = None

    @model_validator(mode="after")
    def validate_semantics(self) -> "FilterDefinition":
        _unique(self.evidence_reference_ids, "evidence_reference_ids", required=True)
        _unique(self.capability_profile_ids, "capability_profile_ids", required=True)
        _unique(self.filter_option_ids, "filter_option_ids")
        _unique(self.dependency_rule_ids, "dependency_rule_ids")
        if self.supersedes_filter_definition_id == self.filter_definition_id:
            raise ValueError("a filter definition must not supersede itself")
        if self.value_kind is FilterValueKind.RANGE and self.filter_range_definition_id is None:
            raise ValueError("range filters require a range definition")
        if self.value_kind is not FilterValueKind.RANGE and self.filter_range_definition_id is not None:
            raise ValueError("non-range filters must not have a range definition")
        if self.value_kind is FilterValueKind.RANGE and self.filter_option_ids:
            raise ValueError("range filters must not contain option IDs")
        return self


class BuilderFieldDefinition(_FilterCatalogContract):
    builder_field_id: OpaqueReferenceId
    filter_catalog_version_id: OpaqueReferenceId
    filter_definition_id: OpaqueReferenceId
    filter_capability_profile_id: OpaqueReferenceId
    value_kind: FilterValueKind
    capability_state: FilterCapabilityState
    required: bool
    filter_option_ids: tuple[OpaqueReferenceId, ...] = ()
    filter_range_definition_id: OpaqueReferenceId | None = None
    warning_ids: tuple[OpaqueReferenceId, ...] = ()

    @model_validator(mode="after")
    def validate_semantics(self) -> "BuilderFieldDefinition":
        _unique(self.filter_option_ids, "filter_option_ids")
        _unique(self.warning_ids, "warning_ids")
        if self.value_kind is FilterValueKind.RANGE and self.filter_range_definition_id is None:
            raise ValueError("range fields require a range definition")
        if self.value_kind is FilterValueKind.RANGE and self.filter_option_ids:
            raise ValueError("range fields must not contain option IDs")
        if self.value_kind is not FilterValueKind.RANGE and self.filter_range_definition_id is not None:
            raise ValueError("non-range fields must not have a range definition")
        return self


class BuilderDraftValidationResult(_FilterCatalogContract):
    builder_draft_validation_result_id: OpaqueReferenceId
    filter_catalog_version_id: OpaqueReferenceId
    beacon_revision_id: OpaqueReferenceId
    validation_state: BuilderDraftValidationState
    accepted_builder_field_ids: tuple[OpaqueReferenceId, ...] = ()
    rejected_builder_field_ids: tuple[OpaqueReferenceId, ...] = ()
    warning_ids: tuple[OpaqueReferenceId, ...] = ()
    is_authoritative_for_beacon: Literal[False] = False

    @model_validator(mode="after")
    def validate_semantics(self) -> "BuilderDraftValidationResult":
        _unique(self.accepted_builder_field_ids, "accepted_builder_field_ids")
        _unique(self.rejected_builder_field_ids, "rejected_builder_field_ids")
        _unique(self.warning_ids, "warning_ids")
        if set(self.accepted_builder_field_ids) & set(self.rejected_builder_field_ids):
            raise ValueError("accepted and rejected builder field IDs must not overlap")
        if self.validation_state is BuilderDraftValidationState.VALID and self.rejected_builder_field_ids:
            raise ValueError("valid validation results must have no rejected field IDs")
        return self


class BeaconOverrideCandidateOutcome(_FilterCatalogContract):
    beacon_override_candidate_outcome_id: OpaqueReferenceId
    override_candidate_reference_id: OpaqueReferenceId
    beacon_id: OpaqueReferenceId
    beacon_revision_id: OpaqueReferenceId
    filter_catalog_version_id: OpaqueReferenceId
    candidate_state: BeaconOverrideCandidateState
    validated_builder_field_ids: tuple[OpaqueReferenceId, ...] = ()
    warning_ids: tuple[OpaqueReferenceId, ...] = ()
    beacon_acceptance_required: Literal[True] = True

    @model_validator(mode="after")
    def validate_semantics(self) -> "BeaconOverrideCandidateOutcome":
        _unique(self.validated_builder_field_ids, "validated_builder_field_ids")
        _unique(self.warning_ids, "warning_ids")
        return self


class CatalogCompatibilityWarning(_FilterCatalogContract):
    catalog_compatibility_warning_id: OpaqueReferenceId
    compatibility_state: CatalogCompatibilityState
    subject_reference_id: OpaqueReferenceId
    safe_code: SafeCode
    evidence_reference_ids: tuple[OpaqueReferenceId, ...]
    blocks_editability: bool

    @model_validator(mode="after")
    def validate_semantics(self) -> "CatalogCompatibilityWarning":
        _unique(self.evidence_reference_ids, "evidence_reference_ids", required=True)
        return self


class CatalogReadModel(_FilterCatalogContract):
    filter_catalog_version_id: OpaqueReferenceId
    generated_at: datetime
    filter_definitions: tuple[FilterDefinition, ...] = ()
    filter_option_definitions: tuple[FilterOptionDefinition, ...] = ()
    filter_range_definitions: tuple[FilterRangeDefinition, ...] = ()
    filter_dependency_rules: tuple[FilterDependencyRule, ...] = ()
    filter_capability_profiles: tuple[FilterCapabilityProfile, ...] = ()
    builder_field_definitions: tuple[BuilderFieldDefinition, ...] = ()
    compatibility_warnings: tuple[CatalogCompatibilityWarning, ...] = ()
    evidence_reference_ids: tuple[OpaqueReferenceId, ...]
    provenance_reference_ids: tuple[OpaqueReferenceId, ...]

    @model_validator(mode="after")
    def validate_semantics(self) -> "CatalogReadModel":
        _aware(self.generated_at, "generated_at")
        _unique(self.evidence_reference_ids, "evidence_reference_ids", required=True)
        _unique(self.provenance_reference_ids, "provenance_reference_ids", required=True)
        families = (
            (self.filter_definitions, "filter_definition_id"),
            (self.filter_option_definitions, "filter_option_id"),
            (self.filter_range_definitions, "filter_range_definition_id"),
            (self.filter_dependency_rules, "filter_dependency_rule_id"),
            (self.filter_capability_profiles, "filter_capability_profile_id"),
            (self.builder_field_definitions, "builder_field_id"),
            (self.compatibility_warnings, "catalog_compatibility_warning_id"),
        )
        for records, id_field in families:
            _unique(tuple(getattr(record, id_field) for record in records), id_field)
        for records in (
            self.filter_definitions,
            self.filter_range_definitions,
            self.filter_dependency_rules,
            self.filter_capability_profiles,
            self.builder_field_definitions,
        ):
            for record in records:
                if record.filter_catalog_version_id != self.filter_catalog_version_id:
                    raise ValueError("embedded record has a mismatched catalog version")
        return self


__all__ = (
    "OpaqueReferenceId", "SafeCode", "Sha256Hex", "SafeLabel",
    "CatalogPublicationState", "FilterDefinitionState", "FilterValueKind",
    "FilterEvidenceState", "FilterCapabilityState", "FilterDependencyKind",
    "BuilderDraftValidationState", "BeaconOverrideCandidateState", "CatalogCompatibilityState",
    "FilterEvidenceReference", "FilterCatalogVersion", "FilterOptionDefinition",
    "FilterRangeDefinition", "FilterDependencyRule", "FilterCapabilityProfile",
    "FilterDefinition", "BuilderFieldDefinition", "BuilderDraftValidationResult",
    "BeaconOverrideCandidateOutcome", "CatalogCompatibilityWarning", "CatalogReadModel",
)
