"""Read-only PostgreSQL runtime for the Module 13 Filter Catalog.

This module deliberately contains no catalog writer and no foreign-owner access.  The
JSONB envelopes are an RF22 wire format; after validation all decisions are delegated
to the accepted Module 13 semantic contracts.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Annotated, Any, Literal, Mapping, TypeVar, cast
from uuid import UUID

import sqlalchemy
import sqlalchemy.orm
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    ValidationError,
    model_validator,
)

from mayak.persistence.schema.filter_catalog import register_filter_catalog_tables

from .beacon_override_candidate import (
    BeaconOverrideCandidatePreparationRequest,
    prepare_beacon_override_candidate,
)
from .builder_validation import (
    BuilderClientValidationState,
    BuilderDraftFieldInput,
    BuilderDraftValidationRequest,
    BuilderFieldServerContext,
    BuilderFieldServerEntry,
    BuilderServerValueValidationState,
    validate_builder_draft,
)
from .contracts import (
    BuilderFieldDefinition,
    CatalogCompatibilityState,
    CatalogCompatibilityWarning,
    CatalogPublicationState,
    CatalogReadModel,
    FilterCapabilityProfile,
    FilterCapabilityState,
    FilterDefinition,
    FilterDefinitionState,
    FilterDependencyKind,
    FilterDependencyRule,
    FilterEvidenceReference,
    FilterEvidenceState,
    FilterOptionDefinition,
    FilterRangeDefinition,
    FilterValueKind,
    OpaqueReferenceId,
    SafeCode,
    SafeLabel,
)
from .safe_read_models import (
    CatalogSafeExplanationCode,
    CatalogSafeFilterReadModel,
    CatalogSafeReadAudience,
    CatalogSafeReadFreshnessState,
    CatalogSafeReadSurfaceState,
)
from .value_dependency_semantics import (
    MultivaluePreservationDecision,
    MultivaluePreservationRequest,
    RangeValueValidationDecision,
    RangeValueValidationRequest,
    evaluate_multivalue_preservation,
    validate_range_value,
)

_Code = StringConstraints(
    strip_whitespace=True,
    min_length=1,
    max_length=128,
    pattern=r"^[A-Z0-9_:-]+$",
)
_ModelT = TypeVar("_ModelT", bound=BaseModel)


class RuntimeBlocked(RuntimeError):
    """Raised when persisted catalog data cannot be reconstructed safely."""


class _Envelope(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


class EvidenceEnvelope(_Envelope):
    schema_version: Literal["rf22-filter-evidence/v1"]
    evidence_state: FilterEvidenceState
    evidence_kind_code: Annotated[str, _Code]
    scope_reference_ids: tuple[OpaqueReferenceId, ...] = Field(min_length=1, max_length=32)
    observed_at: datetime
    limitations: tuple[SafeCode, ...] = Field(default=(), max_length=32)
    refresh_required: bool
    parser_observation_reference_id: OpaqueReferenceId | None = None

    @model_validator(mode="after")
    def unique(self) -> "EvidenceEnvelope":
        if len(self.scope_reference_ids) != len(set(self.scope_reference_ids)) or len(
            self.limitations
        ) != len(set(self.limitations)):
            raise ValueError("duplicate evidence identifiers")
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise ValueError("observed_at must be timezone-aware")
        return self


class CapabilityOptionEnvelope(_Envelope):
    option_id: OpaqueReferenceId
    option_code: SafeCode
    safe_label: SafeLabel
    definition_state: FilterDefinitionState
    evidence_reference_ids: tuple[OpaqueReferenceId, ...] = Field(min_length=1, max_length=32)


class RangeEnvelope(_Envelope):
    range_definition_id: OpaqueReferenceId
    unit_code: SafeCode
    lower_bound: Decimal | None = None
    upper_bound: Decimal | None = None
    lower_inclusive: bool
    upper_inclusive: bool
    step: Decimal | None = None
    evidence_reference_ids: tuple[OpaqueReferenceId, ...] = Field(min_length=1, max_length=32)


class WarningEnvelope(_Envelope):
    warning_id: OpaqueReferenceId
    compatibility_state: CatalogCompatibilityState
    safe_code: SafeCode
    evidence_reference_ids: tuple[OpaqueReferenceId, ...] = Field(min_length=1, max_length=32)
    blocks_editability: bool


class CapabilityFieldEnvelope(_Envelope):
    definition_id: OpaqueReferenceId
    capability_state: FilterCapabilityState
    value_kind: FilterValueKind
    required: bool
    evidence_reference_ids: tuple[OpaqueReferenceId, ...] = Field(min_length=1, max_length=32)
    builder_field_id: OpaqueReferenceId | None = None
    options: tuple[CapabilityOptionEnvelope, ...] = Field(default=(), max_length=256)
    range_definition: RangeEnvelope | None = None
    warning_ids: tuple[OpaqueReferenceId, ...] = Field(default=(), max_length=32)
    compatibility_warnings: tuple[WarningEnvelope, ...] = Field(default=(), max_length=32)

    @model_validator(mode="after")
    def unique(self) -> "CapabilityFieldEnvelope":
        ids = tuple(option.option_id for option in self.options)
        if len(ids) != len(set(ids)) or len(self.warning_ids) != len(set(self.warning_ids)):
            raise ValueError("duplicate capability identifiers")
        warning_ids = tuple(item.warning_id for item in self.compatibility_warnings)
        if len(warning_ids) != len(set(warning_ids)) or set(warning_ids) != set(self.warning_ids):
            raise ValueError("warning metadata must exactly match warning_ids")
        if self.value_kind is FilterValueKind.RANGE and self.range_definition is None:
            raise ValueError("range capability requires range_definition")
        if self.value_kind is not FilterValueKind.RANGE and self.range_definition is not None:
            raise ValueError("non-range capability must not contain range_definition")
        return self


class CapabilityEnvelope(_Envelope):
    schema_version: Literal["rf22-filter-capability-profile/v1"]
    provider_surface_reference_id: OpaqueReferenceId
    category_scope_reference_id: OpaqueReferenceId | None = None
    geography_scope_reference_id: OpaqueReferenceId | None = None
    fields: dict[Annotated[str, _Code], CapabilityFieldEnvelope] = Field(
        min_length=1, max_length=256
    )

    @model_validator(mode="after")
    def keys_match(self) -> "CapabilityEnvelope":
        for code, field in self.fields.items():
            if code != code.upper() or field.definition_id == "":
                raise ValueError("invalid capability field map")
        return self


class DependencyEnvelope(_Envelope):
    schema_version: Literal["rf22-filter-dependency/v1"]
    dependency_kind: FilterDependencyKind
    condition_code: SafeCode
    outcome_code: SafeCode
    evidence_reference_ids: tuple[OpaqueReferenceId, ...] = Field(min_length=1, max_length=32)
    allowed_target_value_reference_ids: tuple[OpaqueReferenceId, ...] = Field(
        default=(), max_length=256
    )

    @model_validator(mode="after")
    def unique(self) -> "DependencyEnvelope":
        if len(self.evidence_reference_ids) != len(set(self.evidence_reference_ids)):
            raise ValueError("duplicate dependency evidence")
        if len(self.allowed_target_value_reference_ids) != len(
            set(self.allowed_target_value_reference_ids)
        ):
            raise ValueError("duplicate dependency target values")
        if (
            self.dependency_kind is FilterDependencyKind.CONSTRAINS
            and not self.allowed_target_value_reference_ids
        ):
            raise ValueError("constrains requires allowed target values")
        if (
            self.dependency_kind is not FilterDependencyKind.CONSTRAINS
            and self.allowed_target_value_reference_ids
        ):
            raise ValueError("only constrains may contain target values")
        return self


class DraftValueInput(_Envelope):
    """Untrusted, provider-neutral draft values; no client authority fields."""

    field_code: Annotated[str, _Code]
    value_reference_ids: tuple[OpaqueReferenceId, ...] = Field(default=(), max_length=256)
    unit_code: SafeCode | None = None
    lower_value: Decimal | None = None
    upper_value: Decimal | None = None
    lower_inclusive: bool = True
    upper_inclusive: bool = True
    step_origin: Decimal | None = None
    client_reported_visible: bool | None = None
    client_reported_enabled: bool | None = None
    client_validation_state: BuilderClientValidationState = BuilderClientValidationState.NOT_RUN


class CatalogLoadResult(_Envelope):
    catalog: CatalogReadModel
    version_code: str
    provenance_ref: str
    evidence_fingerprint: str


class RuntimeDraftResult(_Envelope):
    outcome: Any
    candidate: Any | None = None


class FilterCatalogRuntime:
    """Read-only catalog service around an application-role SQLAlchemy Session."""

    def __init__(self, session: sqlalchemy.orm.Session) -> None:
        self.session = session
        # A fresh registry avoids importing or touching any foreign owner table.
        tables = register_filter_catalog_tables(sqlalchemy.MetaData(schema="mayak"))
        (
            self.versions,
            self.definitions,
            self.options,
            self.dependencies,
            self.applicability,
            self.evidence,
            self.profiles,
        ) = tables
        self._evidence_by_catalog: dict[str, tuple[FilterEvidenceReference, ...]] = {}
        self._dependency_envelopes: dict[str, DependencyEnvelope] = {}
        self._catalog_states: dict[str, CatalogPublicationState] = {}

    @staticmethod
    def _uuid(value: object) -> UUID:
        if isinstance(value, UUID):
            return value
        return UUID(str(value))

    @staticmethod
    def _parse(model: type[_ModelT], value: object, label: str) -> _ModelT:
        try:
            return model.model_validate(value)
        except ValidationError as exc:
            raise RuntimeBlocked(f"invalid {label} envelope") from exc

    def load_catalog(
        self, version_code: str, *, customer_editable: bool = False
    ) -> CatalogLoadResult:
        row = (
            self.session.execute(
                sqlalchemy.select(self.versions).where(self.versions.c.version_code == version_code)
            )
            .mappings()
            .one_or_none()
        )
        if row is None or row["state"] not in (
            CatalogPublicationState.PUBLISHED.value,
            CatalogPublicationState.DRAFT.value,
        ):
            raise RuntimeBlocked("catalog version not found or has unknown state")
        if customer_editable and row["state"] != CatalogPublicationState.PUBLISHED.value:
            raise RuntimeBlocked("draft catalog is not customer editable")
        catalog_id = str(row["id"])
        self._catalog_states[catalog_id] = CatalogPublicationState(str(row["state"]))
        evidence_rows = (
            self.session.execute(
                sqlalchemy.select(self.evidence).where(
                    self.evidence.c.catalog_version_id == row["id"]
                )
            )
            .mappings()
            .all()
        )
        evidence_by_id: dict[str, FilterEvidenceReference] = {}
        for item in evidence_rows:
            evidence_env = self._parse(EvidenceEnvelope, item["safe_metadata"], "evidence")
            evidence_by_id[str(item["id"])] = FilterEvidenceReference(
                evidence_reference_id=str(item["id"]),
                evidence_state=evidence_env.evidence_state,
                evidence_kind_code=evidence_env.evidence_kind_code,
                scope_reference_ids=evidence_env.scope_reference_ids,
                source_fingerprint=str(item["evidence_fingerprint"]),
                observed_at=evidence_env.observed_at,
                limitations=evidence_env.limitations,
                refresh_required=evidence_env.refresh_required,
                parser_observation_reference_id=evidence_env.parser_observation_reference_id,
            )
        definition_rows = (
            self.session.execute(
                sqlalchemy.select(self.definitions).where(
                    self.definitions.c.catalog_version_id == row["id"]
                )
            )
            .mappings()
            .all()
        )
        option_rows = (
            self.session.execute(
                sqlalchemy.select(self.options)
                .join(self.definitions, self.options.c.definition_id == self.definitions.c.id)
                .where(self.definitions.c.catalog_version_id == row["id"])
                .order_by(self.options.c.definition_id, self.options.c.sort_order)
            )
            .mappings()
            .all()
        )
        options_by_definition: dict[str, list[Mapping[str, object]]] = {}
        for option in option_rows:
            options_by_definition.setdefault(str(option["definition_id"]), []).append(
                cast(Mapping[str, object], option)
            )
        profile_rows = (
            self.session.execute(
                sqlalchemy.select(self.profiles).where(
                    self.profiles.c.catalog_version_id == row["id"]
                )
            )
            .mappings()
            .all()
        )
        profiles_by_definition: dict[
            str, list[tuple[Mapping[str, object], CapabilityEnvelope, CapabilityFieldEnvelope]]
        ] = {}
        for profile in profile_rows:
            capability_env = self._parse(CapabilityEnvelope, profile["capabilities"], "capability")
            for code, field in capability_env.fields.items():
                profiles_by_definition.setdefault(field.definition_id, []).append(
                    (cast(Mapping[str, object], profile), capability_env, field)
                )
        definitions: list[FilterDefinition] = []
        profiles: list[FilterCapabilityProfile] = []
        option_defs: list[FilterOptionDefinition] = []
        ranges: list[FilterRangeDefinition] = []
        warnings: list[CatalogCompatibilityWarning] = []
        for definition in definition_rows:
            definition_id = str(definition["id"])
            evidence_id = str(definition["evidence_id"]) if definition["evidence_id"] else None
            if evidence_id is None or evidence_id not in evidence_by_id:
                raise RuntimeBlocked("definition references missing evidence")
            fields = profiles_by_definition.get(definition_id, [])
            if not fields:
                raise RuntimeBlocked("definition has no capability profile field")
            first_profile, first_env, first_field = fields[0]
            definition_code = str(definition["field_code"])
            if (
                definition_code not in first_env.fields
                or first_field.definition_id != definition_id
            ):
                raise RuntimeBlocked("capability field is not linked to its physical definition")
            if any(field != first_field for _, _, field in fields[1:]):
                raise RuntimeBlocked("ambiguous incompatible capability profiles")
            physical_options = options_by_definition.get(definition_id, [])
            physical_codes = tuple(str(item["option_code"]) for item in physical_options)
            metadata_codes = tuple(item.option_code for item in first_field.options)
            if physical_codes != metadata_codes:
                raise RuntimeBlocked("option inventory does not exactly match capability metadata")
            if not set(first_field.evidence_reference_ids) <= set(evidence_by_id):
                raise RuntimeBlocked("capability references missing evidence")
            for physical, meta in zip(physical_options, first_field.options):
                if str(physical["id"]) != meta.option_id:
                    raise RuntimeBlocked("option metadata ID does not match physical option")
                if not set(meta.evidence_reference_ids) <= set(evidence_by_id):
                    raise RuntimeBlocked("option references missing evidence")
                if str(physical["label"]) != meta.safe_label:
                    raise RuntimeBlocked("contradictory option metadata")
                option_defs.append(
                    FilterOptionDefinition(
                        filter_option_id=str(physical["id"]),
                        filter_definition_id=definition_id,
                        canonical_value_code=meta.option_code,
                        safe_label=meta.safe_label,
                        definition_state=meta.definition_state,
                        evidence_reference_ids=meta.evidence_reference_ids,
                    )
                )
            profile_id = str(first_profile["id"])
            profile_model = FilterCapabilityProfile(
                filter_capability_profile_id=profile_id,
                filter_catalog_version_id=catalog_id,
                provider_surface_reference_id=first_env.provider_surface_reference_id,
                category_scope_reference_id=first_env.category_scope_reference_id,
                geography_scope_reference_id=first_env.geography_scope_reference_id,
                capability_state=first_field.capability_state,
                evidence_reference_ids=first_field.evidence_reference_ids,
                warning_ids=first_field.warning_ids,
            )
            profiles.append(profile_model)
            for warning in first_field.compatibility_warnings:
                if not set(warning.evidence_reference_ids) <= set(evidence_by_id):
                    raise RuntimeBlocked("warning references missing evidence")
                warnings.append(
                    CatalogCompatibilityWarning(
                        catalog_compatibility_warning_id=warning.warning_id,
                        compatibility_state=warning.compatibility_state,
                        subject_reference_id=definition_id,
                        safe_code=warning.safe_code,
                        evidence_reference_ids=warning.evidence_reference_ids,
                        blocks_editability=warning.blocks_editability,
                    )
                )
            range_id = None
            if first_field.range_definition is not None:
                r = first_field.range_definition
                if not set(r.evidence_reference_ids) <= set(evidence_by_id):
                    raise RuntimeBlocked("range references missing evidence")
                range_id = r.range_definition_id
                ranges.append(
                    FilterRangeDefinition(
                        filter_range_definition_id=range_id,
                        filter_definition_id=definition_id,
                        unit_code=r.unit_code,
                        lower_bound=r.lower_bound,
                        upper_bound=r.upper_bound,
                        lower_inclusive=r.lower_inclusive,
                        upper_inclusive=r.upper_inclusive,
                        step=r.step,
                        evidence_reference_ids=r.evidence_reference_ids,
                    )
                )
            definitions.append(
                FilterDefinition(
                    filter_definition_id=definition_id,
                    filter_catalog_version_id=catalog_id,
                    normalized_key=str(definition["field_code"]),
                    safe_label=str(definition["label"]),
                    value_kind=FilterValueKind(str(first_field.value_kind)),
                    definition_state=FilterDefinitionState(str(definition["support_state"])),
                    evidence_reference_ids=(evidence_id,),
                    capability_profile_ids=(profile_id,),
                    filter_option_ids=tuple(str(item["id"]) for item in physical_options),
                    filter_range_definition_id=range_id,
                )
            )
        definition_ids = {item.filter_definition_id for item in definitions}
        dependencies: list[FilterDependencyRule] = []
        for item in (
            self.session.execute(
                sqlalchemy.select(self.dependencies).where(
                    self.dependencies.c.catalog_version_id == row["id"]
                )
            )
            .mappings()
            .all()
        ):
            source, target = (
                str(item["source_definition_id"]),
                str(item["depends_on_definition_id"]),
            )
            if source not in definition_ids or target not in definition_ids:
                raise RuntimeBlocked("dependency references missing or cross-version definition")
            dependency_env = self._parse(DependencyEnvelope, item["rule"], "dependency")
            if not set(dependency_env.evidence_reference_ids) <= set(evidence_by_id):
                raise RuntimeBlocked("dependency references missing evidence")
            self._dependency_envelopes[str(item["id"])] = dependency_env
            dependencies.append(
                FilterDependencyRule(
                    filter_dependency_rule_id=str(item["id"]),
                    source_filter_definition_id=source,
                    target_filter_definition_id=target,
                    dependency_kind=dependency_env.dependency_kind,
                    condition_code=dependency_env.condition_code,
                    outcome_code=dependency_env.outcome_code,
                    evidence_reference_ids=dependency_env.evidence_reference_ids,
                )
            )
        definitions = [
            item.model_copy(
                update={
                    "dependency_rule_ids": tuple(
                        rule.filter_dependency_rule_id
                        for rule in dependencies
                        if item.filter_definition_id
                        in (rule.source_filter_definition_id, rule.target_filter_definition_id)
                    )
                }
            )
            for item in definitions
        ]
        evidence_ids = tuple(evidence_by_id)
        self._evidence_by_catalog[catalog_id] = tuple(evidence_by_id.values())
        model = CatalogReadModel(
            filter_catalog_version_id=catalog_id,
            generated_at=datetime.now(timezone.utc),
            filter_definitions=tuple(definitions),
            filter_option_definitions=tuple(option_defs),
            filter_range_definitions=tuple(ranges),
            filter_dependency_rules=tuple(dependencies),
            filter_capability_profiles=tuple(profiles),
            compatibility_warnings=tuple(warnings),
            evidence_reference_ids=evidence_ids,
            provenance_reference_ids=(str(row["provenance_ref"]),),
        )
        return CatalogLoadResult(
            catalog=model,
            version_code=str(row["version_code"]),
            provenance_ref=str(row["provenance_ref"]),
            evidence_fingerprint=str(row["evidence_fingerprint"]),
        )

    def builder_context(
        self,
        catalog: CatalogReadModel,
        *,
        beacon_revision_id: str,
        provider_surface_reference_id: str,
        category_scope_reference_id: str | None,
        geography_scope_reference_id: str | None,
    ) -> BuilderFieldServerContext:
        entries: list[BuilderFieldServerEntry] = []
        profiles = {
            item.filter_capability_profile_id: item for item in catalog.filter_capability_profiles
        }
        for definition in catalog.filter_definitions:
            profile = next(
                (profiles[item] for item in definition.capability_profile_ids if item in profiles),
                None,
            )
            if profile is None:
                continue
            required_scope = (category_scope_reference_id, geography_scope_reference_id)
            scope_ok = (
                profile.provider_surface_reference_id == provider_surface_reference_id
                and profile.category_scope_reference_id == required_scope[0]
                and profile.geography_scope_reference_id == required_scope[1]
            )
            evidence_ok = all(
                item.evidence_state is FilterEvidenceState.CURRENT and not item.refresh_required
                for item in self._evidence_by_catalog.get(catalog.filter_catalog_version_id, ())
                if item.evidence_reference_id
                in set(definition.evidence_reference_ids) | set(profile.evidence_reference_ids)
            )
            category_ok = True
            if category_scope_reference_id is not None:
                category_rows = (
                    self.session.execute(
                        sqlalchemy.select(self.applicability).where(
                            self.applicability.c.catalog_version_id
                            == self._uuid(catalog.filter_catalog_version_id),
                            self.applicability.c.category_code == category_scope_reference_id,
                            self.applicability.c.definition_id
                            == self._uuid(definition.filter_definition_id),
                        )
                    )
                    .mappings()
                    .all()
                )
                category_ok = (
                    len(category_rows) == 1
                    and category_rows[0]["applicability_state"] == "APPLICABLE"
                )
            blocking_warning = any(
                warning.blocks_editability
                for warning in catalog.compatibility_warnings
                if warning.subject_reference_id == definition.filter_definition_id
            )
            editable = (
                self._catalog_states.get(catalog.filter_catalog_version_id)
                is CatalogPublicationState.PUBLISHED
                and definition.definition_state is FilterDefinitionState.APPROVED
                and profile.capability_state is FilterCapabilityState.EDITABLE
                and scope_ok
                and category_ok
                and evidence_ok
                and not blocking_warning
            )
            field = BuilderFieldDefinition(
                builder_field_id=f"RF22_FIELD_{definition.normalized_key}",
                filter_catalog_version_id=catalog.filter_catalog_version_id,
                filter_definition_id=definition.filter_definition_id,
                filter_capability_profile_id=profile.filter_capability_profile_id,
                value_kind=definition.value_kind,
                capability_state=profile.capability_state
                if scope_ok and category_ok and not blocking_warning
                else FilterCapabilityState.CATEGORY_INCOMPATIBLE,
                required=False,
                filter_option_ids=definition.filter_option_ids,
                filter_range_definition_id=definition.filter_range_definition_id,
                warning_ids=profile.warning_ids,
            )
            entries.append(
                BuilderFieldServerEntry(
                    field_definition=field,
                    projection_outcome_reference_id=f"RF22_PROJECTION_{definition.normalized_key}",
                    visible=True,
                    enabled=editable,
                )
            )
        return BuilderFieldServerContext(
            builder_field_server_context_id=f"RF22_CONTEXT_{catalog.filter_catalog_version_id}",
            filter_catalog_version_id=catalog.filter_catalog_version_id,
            beacon_revision_id=beacon_revision_id,
            field_entries=tuple(entries),
        )

    def validate_draft(
        self,
        catalog: CatalogReadModel,
        *,
        builder_draft_id: str,
        beacon_revision_id: str,
        provider_surface_reference_id: str,
        category_scope_reference_id: str | None,
        geography_scope_reference_id: str | None,
        fields: tuple[DraftValueInput, ...],
    ) -> RuntimeDraftResult:
        """Convert raw draft values into the accepted server-owned validation request."""
        context = self.builder_context(
            catalog,
            beacon_revision_id=beacon_revision_id,
            provider_surface_reference_id=provider_surface_reference_id,
            category_scope_reference_id=category_scope_reference_id,
            geography_scope_reference_id=geography_scope_reference_id,
        )
        by_code = {item.normalized_key: item for item in catalog.filter_definitions}
        by_field = {item.field_definition.builder_field_id: item for item in context.field_entries}
        option_codes = {
            item.filter_definition_id: {
                item.canonical_value_code: item.filter_option_id
                for item in catalog.filter_option_definitions
            }
            for item in catalog.filter_option_definitions
        }
        converted: list[BuilderDraftFieldInput] = []
        for raw in fields:
            definition = by_code.get(raw.field_code)
            if definition is None:
                converted.append(
                    BuilderDraftFieldInput(
                        builder_field_id=f"RF22_UNKNOWN_{raw.field_code}",
                        value_reference_ids=(),
                        server_value_validation_state=BuilderServerValueValidationState.INVALID,
                        server_value_validation_reference_id="RF22_UNKNOWN_FIELD",
                    )
                )
                continue
            field_id = f"RF22_FIELD_{definition.normalized_key}"
            entry = by_field.get(field_id)
            values = tuple(
                option_codes.get(definition.filter_definition_id, {}).get(value, value)
                for value in raw.value_reference_ids
            )
            valid = bool(entry and entry.enabled)
            if definition.value_kind in (
                FilterValueKind.SCALAR,
                FilterValueKind.REFERENCE,
                FilterValueKind.MULTIVALUE,
            ):
                valid = valid and all(
                    value in set(option_codes.get(definition.filter_definition_id, {}).values())
                    for value in values
                )
            if definition.value_kind is FilterValueKind.RANGE:
                range_definition = next(
                    (
                        item
                        for item in catalog.filter_range_definitions
                        if item.filter_definition_id == definition.filter_definition_id
                    ),
                    None,
                )
                if range_definition is None or raw.unit_code is None:
                    valid = False
                else:
                    outcome = validate_range_value(
                        RangeValueValidationRequest(
                            filter_definition_id=definition.filter_definition_id,
                            range_definition=range_definition,
                            candidate_unit_code=raw.unit_code,
                            lower_value=raw.lower_value,
                            upper_value=raw.upper_value,
                            lower_inclusive=raw.lower_inclusive,
                            upper_inclusive=raw.upper_inclusive,
                            step_origin=raw.step_origin,
                        )
                    )
                    valid = valid and outcome.decision is RangeValueValidationDecision.VALID
            if definition.value_kind is FilterValueKind.MULTIVALUE and valid:
                multivalue_outcome = evaluate_multivalue_preservation(
                    MultivaluePreservationRequest(
                        filter_definition_id=definition.filter_definition_id,
                        source_value_reference_ids=values,
                        candidate_value_reference_ids=values,
                    )
                )
                valid = multivalue_outcome.decision is MultivaluePreservationDecision.PRESERVED
            converted.append(
                BuilderDraftFieldInput(
                    builder_field_id=field_id,
                    value_reference_ids=values,
                    server_value_validation_state=BuilderServerValueValidationState.VALID
                    if valid
                    else BuilderServerValueValidationState.INVALID,
                    server_value_validation_reference_id=f"RF22_VALUE_{definition.normalized_key}",
                    client_validation_state=raw.client_validation_state,
                    client_reported_visible=raw.client_reported_visible,
                    client_reported_enabled=raw.client_reported_enabled,
                )
            )
        request = BuilderDraftValidationRequest(
            builder_draft_validation_result_id=f"RF22_VALIDATION_{builder_draft_id}",
            builder_draft_id=builder_draft_id,
            filter_catalog_version_id=catalog.filter_catalog_version_id,
            beacon_revision_id=beacon_revision_id,
            server_context=context,
            draft_fields=tuple(converted),
        )
        return RuntimeDraftResult(outcome=validate_builder_draft(request))

    def prepare_candidate(
        self,
        request: BuilderDraftValidationRequest,
        outcome: Any,
        *,
        beacon_id: str,
        beacon_acceptance_boundary_reference_id: str,
    ) -> Any:
        """Prepare, but never apply, a Beacon override candidate."""
        return prepare_beacon_override_candidate(
            BeaconOverrideCandidatePreparationRequest(
                beacon_override_candidate_outcome_id=f"RF22_CANDIDATE_{request.builder_draft_id}",
                override_candidate_reference_id=f"RF22_OVERRIDE_{request.builder_draft_id}",
                beacon_id=beacon_id,
                filter_catalog_version_id=request.filter_catalog_version_id,
                beacon_revision_id=request.beacon_revision_id,
                builder_validation_request=request,
                builder_validation_outcome=outcome,
                catalog_evidence_reference_ids=tuple(
                    item.evidence_reference_id
                    for item in self._evidence_by_catalog.get(request.filter_catalog_version_id, ())
                )
                or ("RF22_EVIDENCE_UNAVAILABLE",),
                beacon_acceptance_boundary_reference_id=beacon_acceptance_boundary_reference_id,
            )
        )

    def project_read_model(
        self,
        catalog: CatalogReadModel,
        field_code: str,
        *,
        audience: CatalogSafeReadAudience,
        surface_state: CatalogSafeReadSurfaceState = CatalogSafeReadSurfaceState.AVAILABLE,
    ) -> CatalogSafeFilterReadModel:
        """Return the accepted safe Web/Admin projection; authorization is external."""
        definition = next(
            (item for item in catalog.filter_definitions if item.normalized_key == field_code),
            None,
        )
        profile = next(
            (
                item
                for item in catalog.filter_capability_profiles
                if definition is not None
                and item.filter_capability_profile_id in definition.capability_profile_ids
            ),
            None,
        )
        if (
            surface_state is not CatalogSafeReadSurfaceState.AVAILABLE
            or definition is None
            or profile is None
        ):
            state = (
                surface_state
                if surface_state is not CatalogSafeReadSurfaceState.AVAILABLE
                else CatalogSafeReadSurfaceState.NOT_FOUND_SAFE
            )
            reason = {
                CatalogSafeReadSurfaceState.REDACTED: CatalogSafeExplanationCode.REDACTED,
                CatalogSafeReadSurfaceState.FORBIDDEN: CatalogSafeExplanationCode.FORBIDDEN,
                CatalogSafeReadSurfaceState.NOT_FOUND_SAFE: (
                    CatalogSafeExplanationCode.NOT_FOUND_SAFE
                ),
            }[state]
            return CatalogSafeFilterReadModel(
                catalog_safe_filter_read_model_id=f"RF22_READ_{field_code}",
                audience=audience,
                surface_state=state,
                freshness_state=CatalogSafeReadFreshnessState.UNKNOWN,
                filter_catalog_version_id=catalog.filter_catalog_version_id,
                explanation_codes=(reason,),
                provenance_reference_ids=catalog.provenance_reference_ids,
                details_redacted=True,
            )
        evidence = self._evidence_by_catalog.get(catalog.filter_catalog_version_id, ())
        current = all(
            item.evidence_state is FilterEvidenceState.CURRENT and not item.refresh_required
            for item in evidence
            if item.evidence_reference_id
            in set(definition.evidence_reference_ids) | set(profile.evidence_reference_ids)
        )
        warning_ids = tuple(
            warning.catalog_compatibility_warning_id
            for warning in catalog.compatibility_warnings
            if warning.subject_reference_id == definition.filter_definition_id
        )
        explanations: tuple[CatalogSafeExplanationCode, ...] = (
            CatalogSafeExplanationCode(profile.capability_state.value),
        )
        acceptance_required = profile.capability_state is FilterCapabilityState.EDITABLE
        if acceptance_required:
            explanations += (CatalogSafeExplanationCode.BEACON_ACCEPTANCE_REQUIRED,)
        return CatalogSafeFilterReadModel(
            catalog_safe_filter_read_model_id=f"RF22_READ_{field_code}",
            audience=audience,
            surface_state=CatalogSafeReadSurfaceState.AVAILABLE,
            freshness_state=CatalogSafeReadFreshnessState.CURRENT
            if current
            else CatalogSafeReadFreshnessState.STALE,
            filter_catalog_version_id=catalog.filter_catalog_version_id,
            filter_definition_id=definition.filter_definition_id,
            builder_field_id=f"RF22_FIELD_{definition.normalized_key}",
            filter_capability_profile_id=profile.filter_capability_profile_id,
            safe_label=definition.safe_label,
            capability_state=profile.capability_state,
            explanation_codes=explanations,
            warning_ids=warning_ids if audience is CatalogSafeReadAudience.ADMIN_AUTHORIZED else (),
            evidence_reference_ids=(
                tuple(
                    sorted(
                        set(definition.evidence_reference_ids) | set(profile.evidence_reference_ids)
                    )
                )
                if audience is CatalogSafeReadAudience.ADMIN_AUTHORIZED
                else ()
            ),
            provenance_reference_ids=catalog.provenance_reference_ids,
            beacon_acceptance_required=acceptance_required,
            details_redacted=audience is CatalogSafeReadAudience.WEB_CUSTOMER,
        )


__all__ = (
    "RuntimeBlocked",
    "EvidenceEnvelope",
    "CapabilityEnvelope",
    "DependencyEnvelope",
    "WarningEnvelope",
    "DraftValueInput",
    "CatalogLoadResult",
    "RuntimeDraftResult",
    "FilterCatalogRuntime",
)
