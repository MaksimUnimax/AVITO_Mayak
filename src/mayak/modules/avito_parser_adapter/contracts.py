"""Transport-neutral semantic contracts for the Avito Parser Adapter."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Final


class TransportOutcomeStatus(str, Enum):
    """Transport-level classifications for adapter attempts."""

    NOT_SENT = "NOT_SENT"
    TRANSPORT_UNAVAILABLE = "TRANSPORT_UNAVAILABLE"
    TRANSPORT_AMBIGUOUS = "TRANSPORT_AMBIGUOUS"
    RESPONSE_RECEIVED_UNCLASSIFIED = "RESPONSE_RECEIVED_UNCLASSIFIED"


class ParserOutcomeStatus(str, Enum):
    """Parser-level classifications for transport-neutral outcomes."""

    USABLE_RESPONSE = "USABLE_RESPONSE"
    EXPLICIT_REJECTION = "EXPLICIT_REJECTION"
    RATE_OR_ACCESS_RESTRICTED = "RATE_OR_ACCESS_RESTRICTED"
    CAPTCHA_OR_CHALLENGE = "CAPTCHA_OR_CHALLENGE"
    MALFORMED_RESPONSE = "MALFORMED_RESPONSE"
    INCOMPLETE_RESPONSE = "INCOMPLETE_RESPONSE"
    UNSUPPORTED_STRUCTURE = "UNSUPPORTED_STRUCTURE"
    PARTIAL = "PARTIAL"
    RESULT_AMBIGUOUS = "RESULT_AMBIGUOUS"


class ProviderResponseEvidenceClass(str, Enum):
    """Provider-response evidence classes used by semantic classification."""

    UNCLASSIFIED = "UNCLASSIFIED"
    BODY_PRESENT_UNCLASSIFIED = "BODY_PRESENT_UNCLASSIFIED"
    USABLE_RESPONSE = "USABLE_RESPONSE"
    EXPLICIT_REJECTION = "EXPLICIT_REJECTION"
    RATE_OR_ACCESS_RESTRICTED = "RATE_OR_ACCESS_RESTRICTED"
    CAPTCHA_OR_CHALLENGE = "CAPTCHA_OR_CHALLENGE"
    MALFORMED_RESPONSE = "MALFORMED_RESPONSE"
    INCOMPLETE_RESPONSE = "INCOMPLETE_RESPONSE"
    UNSUPPORTED_STRUCTURE = "UNSUPPORTED_STRUCTURE"
    PARTIAL = "PARTIAL"
    RESULT_AMBIGUOUS = "RESULT_AMBIGUOUS"
    EMPTY_WITH_PROOF = "EMPTY_WITH_PROOF"
    EMPTY_WITHOUT_PROOF = "EMPTY_WITHOUT_PROOF"


class ResponseCompletenessStatus(str, Enum):
    """Completeness classifications for response semantics."""

    UNVERIFIED = "UNVERIFIED"
    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    INCOMPLETE = "INCOMPLETE"
    EMPTY_PROVEN = "EMPTY_PROVEN"
    EMPTY_BLOCKED = "EMPTY_BLOCKED"
    AMBIGUOUS = "AMBIGUOUS"


class ResponseRestrictionSignal(str, Enum):
    """Explicit restriction signals that must not be hidden as empty."""

    NONE = "NONE"
    RATE_LIMIT = "RATE_LIMIT"
    ACCESS_RESTRICTED = "ACCESS_RESTRICTED"
    CAPTCHA = "CAPTCHA"
    CHALLENGE = "CHALLENGE"


class ReferenceOutcomeStatus(str, Enum):
    """Reference-profile classifications that gate semantic acceptance."""

    REFERENCE_STALE = "REFERENCE_STALE"
    REFERENCE_MISSING = "REFERENCE_MISSING"
    REFERENCE_DISPUTED = "REFERENCE_DISPUTED"
    CURRENT = "CURRENT"


class CompatibilityProfileLifecycleStatus(str, Enum):
    """Compatibility-profile lifecycle states."""

    CURRENT = "CURRENT"
    STALE = "STALE"
    SUPERSEDED = "SUPERSEDED"
    WITHDRAWN = "WITHDRAWN"
    UNAVAILABLE = "UNAVAILABLE"
    DISPUTED = "DISPUTED"


class CompatibilityProfileAuthorityClass(str, Enum):
    """Authority class for a profile or observation set."""

    OBSERVATION_ONLY = "OBSERVATION_ONLY"
    OWNER_CAPTURED = "OWNER_CAPTURED"
    SYNTHETIC = "SYNTHETIC"
    PROOF_GATED = "PROOF_GATED"
    OFFICIAL_PRIMARY_ONLY = "OFFICIAL_PRIMARY_ONLY"


class CompatibilityChangeClass(str, Enum):
    """Semantic classification for compatibility changes."""

    COMPATIBLE = "COMPATIBLE"
    WARNING = "WARNING"
    BREAKING = "BREAKING"
    UNKNOWN = "UNKNOWN"
    DISPUTED = "DISPUTED"
    UNAVAILABLE = "UNAVAILABLE"


class CompatibilityRevalidationTrigger(str, Enum):
    """Triggers that require compatibility revalidation."""

    REFERENCE_CHANGED = "REFERENCE_CHANGED"
    EXTRACTION_CLAIM_CHANGED = "EXTRACTION_CLAIM_CHANGED"
    PARSER_WARNING_MAPPING_CHANGED = "PARSER_WARNING_MAPPING_CHANGED"
    FIXTURE_MATRIX_CHANGED = "FIXTURE_MATRIX_CHANGED"
    PROVIDER_STRUCTURE_UNPROVEN_OR_STALE = "PROVIDER_STRUCTURE_UNPROVEN_OR_STALE"
    OWNER_DECISION_CHANGED = "OWNER_DECISION_CHANGED"


class ParserWarningCode(str, Enum):
    """Semantic warning codes for safe adapter evidence."""

    PHONE_UNAVAILABLE = "PHONE_UNAVAILABLE"
    SELLER_UNAVAILABLE = "SELLER_UNAVAILABLE"
    RATING_UNAVAILABLE = "RATING_UNAVAILABLE"
    DESCRIPTION_UNAVAILABLE = "DESCRIPTION_UNAVAILABLE"
    MULTIVALUE_FILTER_PRESERVED = "MULTIVALUE_FILTER_PRESERVED"
    SORT_CONTEXT_AMBIGUOUS = "SORT_CONTEXT_AMBIGUOUS"
    PARTIAL_PAGE = "PARTIAL_PAGE"
    STALE_COMPATIBILITY_PROFILE = "STALE_COMPATIBILITY_PROFILE"
    EMPTY_RESULT_PROVEN = "EMPTY_RESULT_PROVEN"
    FIELD_CANDIDATE_OPTIONAL = "FIELD_CANDIDATE_OPTIONAL"
    REFERENCE_CHANGED = "REFERENCE_CHANGED"
    REFERENCE_SUPERSEDED = "REFERENCE_SUPERSEDED"
    REFERENCE_WITHDRAWN = "REFERENCE_WITHDRAWN"
    REFERENCE_UNAVAILABLE = "REFERENCE_UNAVAILABLE"
    REFERENCE_DISPUTED = "REFERENCE_DISPUTED"
    UNSUPPORTED_EXTRACTION_CLAIM = "UNSUPPORTED_EXTRACTION_CLAIM"
    COMPATIBILITY_REVALIDATION_REQUIRED = "COMPATIBILITY_REVALIDATION_REQUIRED"
    INTERNAL_ENDPOINT_OBSERVATION_ONLY = "INTERNAL_ENDPOINT_OBSERVATION_ONLY"
    STALE_PROFILE_BLOCKED = "STALE_PROFILE_BLOCKED"
    WITHDRAWN_PROFILE_BLOCKED = "WITHDRAWN_PROFILE_BLOCKED"
    DISPUTED_PROFILE_WARNING = "DISPUTED_PROFILE_WARNING"
    UNAVAILABLE_PROFILE_WARNING = "UNAVAILABLE_PROFILE_WARNING"
    SOURCE_URL_UNTRUSTED = "SOURCE_URL_UNTRUSTED"
    SOURCE_URL_POLICY_MISSING = "SOURCE_URL_POLICY_MISSING"
    SOURCE_URL_MALFORMED = "SOURCE_URL_MALFORMED"
    SOURCE_URL_UNSUPPORTED = "SOURCE_URL_UNSUPPORTED"
    SOURCE_URL_CANONICALIZATION_UNPROVEN = "SOURCE_URL_CANONICALIZATION_UNPROVEN"
    SOURCE_URL_REDIRECT_POLICY_BLOCKED = "SOURCE_URL_REDIRECT_POLICY_BLOCKED"
    SOURCE_URL_DNS_POLICY_BLOCKED = "SOURCE_URL_DNS_POLICY_BLOCKED"
    SOURCE_VALUE_SHELL_TARGET_BLOCKED = "SOURCE_VALUE_SHELL_TARGET_BLOCKED"
    SOURCE_VALUE_FILESYSTEM_TARGET_BLOCKED = "SOURCE_VALUE_FILESYSTEM_TARGET_BLOCKED"
    SOURCE_VALUE_NETWORK_TARGET_BLOCKED = "SOURCE_VALUE_NETWORK_TARGET_BLOCKED"


class SearchConfigurationWarningCode(str, Enum):
    """Search-configuration warning codes for evidence-bound extraction."""

    GEOGRAPHY_CANDIDATE_EVIDENCE_BOUND = "GEOGRAPHY_CANDIDATE_EVIDENCE_BOUND"
    CATEGORY_CANDIDATE_EVIDENCE_BOUND = "CATEGORY_CANDIDATE_EVIDENCE_BOUND"
    PRICE_BOUNDS_CANDIDATE_EVIDENCE_BOUND = "PRICE_BOUNDS_CANDIDATE_EVIDENCE_BOUND"
    STRUCTURED_FILTER_CANDIDATE_EVIDENCE_BOUND = "STRUCTURED_FILTER_CANDIDATE_EVIDENCE_BOUND"
    MULTIVALUE_PARAMETER_PRESERVED = "MULTIVALUE_PARAMETER_PRESERVED"
    UNSUPPORTED_PARAMETER_EXPLICIT = "UNSUPPORTED_PARAMETER_EXPLICIT"
    AMBIGUOUS_PARAMETER_EXPLICIT = "AMBIGUOUS_PARAMETER_EXPLICIT"
    LOSSY_NORMALIZATION_BLOCKED = "LOSSY_NORMALIZATION_BLOCKED"
    SORT_CONTEXT_UNPROVEN = "SORT_CONTEXT_UNPROVEN"
    PAGINATION_CONTEXT_BLOCKED = "PAGINATION_CONTEXT_BLOCKED"
    COUNTRY_WIDE_POLICY_GATED = "COUNTRY_WIDE_POLICY_GATED"
    FILTER_EDITABILITY_NOT_DECLARED = "FILTER_EDITABILITY_NOT_DECLARED"
    BEACON_SNAPSHOT_ACCEPTANCE_NOT_PERFORMED = "BEACON_SNAPSHOT_ACCEPTANCE_NOT_PERFORMED"


class SearchConfigurationExtractionField(str, Enum):
    """Search-configuration field families extracted from evidence."""

    GEOGRAPHY_CONTEXT = "GEOGRAPHY_CONTEXT"
    CATEGORY_CONTEXT = "CATEGORY_CONTEXT"
    PRICE_LOWER_BOUND = "PRICE_LOWER_BOUND"
    PRICE_UPPER_BOUND = "PRICE_UPPER_BOUND"
    STRUCTURED_FILTER = "STRUCTURED_FILTER"
    REPEATED_PARAMETER = "REPEATED_PARAMETER"
    SORT_CONTEXT = "SORT_CONTEXT"
    PAGINATION_CONTEXT = "PAGINATION_CONTEXT"
    UNSUPPORTED_PARAMETER = "UNSUPPORTED_PARAMETER"
    AMBIGUOUS_PARAMETER = "AMBIGUOUS_PARAMETER"
    COUNTRY_WIDE_CONTEXT = "COUNTRY_WIDE_CONTEXT"
    FILTER_EDITABILITY_CONTEXT = "FILTER_EDITABILITY_CONTEXT"
    BEACON_SNAPSHOT_CONTEXT = "BEACON_SNAPSHOT_CONTEXT"


class SearchConfigurationFieldStatus(str, Enum):
    """Confidence and policy status for search-configuration candidates."""

    EVIDENCE_BOUND = "EVIDENCE_BOUND"
    PRESERVED = "PRESERVED"
    UNPROVEN = "UNPROVEN"
    UNSUPPORTED = "UNSUPPORTED"
    AMBIGUOUS = "AMBIGUOUS"
    POLICY_GATED = "POLICY_GATED"
    LOSSY_NORMALIZATION_BLOCKED = "LOSSY_NORMALIZATION_BLOCKED"


class SearchConfigurationValueKind(str, Enum):
    """Value-shape kinds for search-configuration candidates."""

    SCALAR = "SCALAR"
    RANGE_BOUND = "RANGE_BOUND"
    KEY_VALUE_PAIR = "KEY_VALUE_PAIR"
    COLLECTION = "COLLECTION"
    CONTEXT = "CONTEXT"
    PROVENANCE = "PROVENANCE"
    UNSUPPORTED = "UNSUPPORTED"
    AMBIGUOUS = "AMBIGUOUS"


class SourceReferenceKind(str, Enum):
    """Semantic kinds for bounded source references consumed by the parser."""

    BEACON_OWNED_SUBMISSION = "BEACON_OWNED_SUBMISSION"
    SAFE_REFERENCE = "SAFE_REFERENCE"
    BOUNDED_VALUE = "BOUNDED_VALUE"
    EXTERNAL_UNTRUSTED_INPUT = "EXTERNAL_UNTRUSTED_INPUT"
    BLOCKED_BOUNDARY = "BLOCKED_BOUNDARY"


class SourceBoundaryStatus(str, Enum):
    """Explicit source-boundary analysis statuses."""

    SOURCE_URL_UNTRUSTED = "SOURCE_URL_UNTRUSTED"
    SOURCE_URL_POLICY_MISSING = "SOURCE_URL_POLICY_MISSING"
    SOURCE_URL_MALFORMED = "SOURCE_URL_MALFORMED"
    SOURCE_URL_UNSUPPORTED = "SOURCE_URL_UNSUPPORTED"
    SOURCE_URL_CANONICALIZATION_UNPROVEN = "SOURCE_URL_CANONICALIZATION_UNPROVEN"
    SOURCE_URL_REDIRECT_POLICY_BLOCKED = "SOURCE_URL_REDIRECT_POLICY_BLOCKED"
    SOURCE_URL_DNS_POLICY_BLOCKED = "SOURCE_URL_DNS_POLICY_BLOCKED"
    SOURCE_VALUE_SHELL_TARGET_BLOCKED = "SOURCE_VALUE_SHELL_TARGET_BLOCKED"
    SOURCE_VALUE_FILESYSTEM_TARGET_BLOCKED = "SOURCE_VALUE_FILESYSTEM_TARGET_BLOCKED"
    SOURCE_VALUE_NETWORK_TARGET_BLOCKED = "SOURCE_VALUE_NETWORK_TARGET_BLOCKED"


class SourceBoundaryRiskCode(str, Enum):
    """Risk codes that describe blocked or unproven source-boundary conditions."""

    SOURCE_URL_UNTRUSTED = "SOURCE_URL_UNTRUSTED"
    SOURCE_URL_POLICY_MISSING = "SOURCE_URL_POLICY_MISSING"
    SOURCE_URL_MALFORMED = "SOURCE_URL_MALFORMED"
    SOURCE_URL_UNSUPPORTED = "SOURCE_URL_UNSUPPORTED"
    SOURCE_URL_CANONICALIZATION_UNPROVEN = "SOURCE_URL_CANONICALIZATION_UNPROVEN"
    SOURCE_URL_REDIRECT_POLICY_BLOCKED = "SOURCE_URL_REDIRECT_POLICY_BLOCKED"
    SOURCE_URL_DNS_POLICY_BLOCKED = "SOURCE_URL_DNS_POLICY_BLOCKED"
    SOURCE_VALUE_SHELL_TARGET_BLOCKED = "SOURCE_VALUE_SHELL_TARGET_BLOCKED"
    SOURCE_VALUE_FILESYSTEM_TARGET_BLOCKED = "SOURCE_VALUE_FILESYSTEM_TARGET_BLOCKED"
    SOURCE_VALUE_NETWORK_TARGET_BLOCKED = "SOURCE_VALUE_NETWORK_TARGET_BLOCKED"


class SourceBoundaryPolicyRequirement(str, Enum):
    """Required policy gates for source-boundary validation."""

    HOST_POLICY_REQUIRED = "HOST_POLICY_REQUIRED"
    PATH_POLICY_REQUIRED = "PATH_POLICY_REQUIRED"
    QUERY_POLICY_REQUIRED = "QUERY_POLICY_REQUIRED"
    REDIRECT_POLICY_REQUIRED = "REDIRECT_POLICY_REQUIRED"
    DNS_POLICY_REQUIRED = "DNS_POLICY_REQUIRED"
    CANONICALIZATION_PROOF_REQUIRED = "CANONICALIZATION_PROOF_REQUIRED"
    SHELL_INTERPOLATION_BLOCK_REQUIRED = "SHELL_INTERPOLATION_BLOCK_REQUIRED"
    FILESYSTEM_TARGET_BLOCK_REQUIRED = "FILESYSTEM_TARGET_BLOCK_REQUIRED"
    NETWORK_TARGET_BLOCK_REQUIRED = "NETWORK_TARGET_BLOCK_REQUIRED"


@dataclass(frozen=True, slots=True)
class ParserSourceReference:
    """Beacon-owned bounded source reference with no live URL authority."""

    source_reference_id: str
    source_reference_kind: SourceReferenceKind
    beacon_source_reference: str
    bounded_value: str
    ownership: str = "Beacon Management"
    untrusted_input: bool = True
    host_reference: str | None = None
    path_reference: str | None = None
    query_reference: str | None = None
    header_references: tuple[str, ...] = ()
    extracted_value_references: tuple[str, ...] = ()
    policy_requirements: tuple[SourceBoundaryPolicyRequirement, ...] = ()
    risk_codes: tuple[SourceBoundaryRiskCode, ...] = ()
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for field_name in ("source_reference_id", "ownership", "bounded_value", "beacon_source_reference"):
            if not getattr(self, field_name).strip():
                raise ValueError(f"{field_name} must not be blank")
        _validate_nonblank_values("header_references", self.header_references)
        _validate_nonblank_values("extracted_value_references", self.extracted_value_references)
        _validate_nonblank_values("notes", self.notes)


@dataclass(frozen=True, slots=True)
class SourceBoundaryOutcome:
    """Explicit source-boundary analysis outcome for safe parser metadata."""

    boundary_id: str
    source_reference: ParserSourceReference
    status: SourceBoundaryStatus
    policy_requirements: tuple[SourceBoundaryPolicyRequirement, ...] = ()
    risk_codes: tuple[SourceBoundaryRiskCode, ...] = ()
    warnings: tuple[ParserWarning, ...] = ()
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.boundary_id.strip():
            raise ValueError("boundary_id must not be blank")
        _validate_nonblank_values("notes", self.notes)


@dataclass(frozen=True, slots=True)
class ParserEvidenceReference:
    """Safe evidence reference with no raw provider payload retention."""

    reference_id: str
    evidence_kind: str
    reference_status: ReferenceOutcomeStatus = ReferenceOutcomeStatus.CURRENT
    lifecycle_status: CompatibilityProfileLifecycleStatus | None = None
    fingerprint: str | None = None
    version: str | None = None
    sample_count: int | None = None
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.reference_id.strip():
            raise ValueError("reference_id must not be blank")
        if not self.evidence_kind.strip():
            raise ValueError("evidence_kind must not be blank")


def _lifecycle_status_from_reference_status(
    reference_status: ReferenceOutcomeStatus,
) -> CompatibilityProfileLifecycleStatus:
    if reference_status is ReferenceOutcomeStatus.CURRENT:
        return CompatibilityProfileLifecycleStatus.CURRENT
    if reference_status is ReferenceOutcomeStatus.REFERENCE_STALE:
        return CompatibilityProfileLifecycleStatus.STALE
    if reference_status is ReferenceOutcomeStatus.REFERENCE_DISPUTED:
        return CompatibilityProfileLifecycleStatus.DISPUTED
    return CompatibilityProfileLifecycleStatus.UNAVAILABLE


def _reference_status_from_lifecycle_status(
    lifecycle_status: CompatibilityProfileLifecycleStatus,
) -> ReferenceOutcomeStatus:
    if lifecycle_status is CompatibilityProfileLifecycleStatus.CURRENT:
        return ReferenceOutcomeStatus.CURRENT
    if lifecycle_status in (
        CompatibilityProfileLifecycleStatus.STALE,
        CompatibilityProfileLifecycleStatus.SUPERSEDED,
    ):
        return ReferenceOutcomeStatus.REFERENCE_STALE
    if lifecycle_status is CompatibilityProfileLifecycleStatus.DISPUTED:
        return ReferenceOutcomeStatus.REFERENCE_DISPUTED
    return ReferenceOutcomeStatus.REFERENCE_MISSING


def _validate_nonblank_values(field_name: str, values: tuple[str, ...]) -> None:
    for value in values:
        if not value.strip():
            raise ValueError(f"{field_name} must not contain blank values")


@dataclass(frozen=True, slots=True)
class ParserWarning:
    """Explicit warning that stays attached to an outcome or candidate."""

    code: ParserWarningCode | SearchConfigurationWarningCode
    message: str
    evidence_reference: ParserEvidenceReference | None = None
    details: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.message.strip():
            raise ValueError("warning message must not be blank")


@dataclass(frozen=True, slots=True)
class ParserResponseClassificationRule:
    """Semantic rule that explains how a response classification is derived."""

    rule_id: str
    summary: str
    required_transport_statuses: tuple[TransportOutcomeStatus, ...] = ()
    required_parser_statuses: tuple[ParserOutcomeStatus, ...] = ()
    required_reference_statuses: tuple[
        ReferenceOutcomeStatus | CompatibilityProfileLifecycleStatus,
        ...,
    ] = ()
    required_provider_evidence_classes: tuple[ProviderResponseEvidenceClass, ...] = ()
    required_response_completeness_statuses: tuple[ResponseCompletenessStatus, ...] = ()
    required_response_restriction_signals: tuple[ResponseRestrictionSignal, ...] = ()
    requires_current_profile_proof: bool = False
    requires_required_structure: bool = True
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.rule_id.strip():
            raise ValueError("rule_id must not be blank")
        if not self.summary.strip():
            raise ValueError("summary must not be blank")
        _validate_nonblank_values("notes", self.notes)


@dataclass(frozen=True, slots=True)
class ParserCompatibilityProfile:
    """Versioned reference profile that gates semantic parsing behavior."""

    profile_id: str
    semantic_version: str | None = None
    profile_version: str | None = None
    lifecycle_status: CompatibilityProfileLifecycleStatus | None = None
    authority_class: CompatibilityProfileAuthorityClass = CompatibilityProfileAuthorityClass.OBSERVATION_ONLY
    authority_scope: tuple[str, ...] = ()
    reference_ids: tuple[str, ...] = ()
    primary_reference_repository: str | None = None
    primary_reference_commit: str | None = None
    retrieval_date: str | None = None
    effective_date: str | None = None
    reference_status: ReferenceOutcomeStatus | None = None
    source_reference: str | None = None
    evidence_reference: ParserEvidenceReference | None = None
    supported_extraction_claims: tuple[str, ...] = ()
    supported_shape_signatures: tuple[str, ...] = ()
    unsupported_extraction_claims: tuple[str, ...] = ()
    unsupported_shape_signatures: tuple[str, ...] = ()
    required_fields: tuple[str, ...] = ()
    completeness_rules: tuple[str, ...] = ()
    warning_mappings: tuple[str, ...] = ()
    error_mappings: tuple[str, ...] = ()
    fixture_ids: tuple[str, ...] = ()
    acceptance_matrix_rows: tuple[str, ...] = ()
    revalidation_triggers: tuple[CompatibilityRevalidationTrigger, ...] = ()
    compatibility_change_classes: tuple[CompatibilityChangeClass, ...] = ()
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.profile_id.strip():
            raise ValueError("profile_id must not be blank")

        if self.semantic_version is None and self.profile_version is None:
            raise ValueError("semantic_version must not be blank")
        if self.semantic_version is None:
            object.__setattr__(self, "semantic_version", self.profile_version)
        if self.profile_version is None:
            object.__setattr__(self, "profile_version", self.semantic_version)
        if self.semantic_version is not None and not self.semantic_version.strip():
            raise ValueError("semantic_version must not be blank")
        if self.profile_version is not None and not self.profile_version.strip():
            raise ValueError("profile_version must not be blank")
        if self.semantic_version != self.profile_version:
            raise ValueError("semantic_version and profile_version must match")

        if self.lifecycle_status is None and self.reference_status is None:
            object.__setattr__(self, "lifecycle_status", CompatibilityProfileLifecycleStatus.CURRENT)
            object.__setattr__(self, "reference_status", ReferenceOutcomeStatus.CURRENT)
        elif self.lifecycle_status is None:
            object.__setattr__(
                self,
                "lifecycle_status",
                _lifecycle_status_from_reference_status(self.reference_status),
            )
        elif self.reference_status is None:
            object.__setattr__(
                self,
                "reference_status",
                _reference_status_from_lifecycle_status(self.lifecycle_status),
            )
        else:
            expected_reference_status = _reference_status_from_lifecycle_status(self.lifecycle_status)
            if self.reference_status is not expected_reference_status:
                raise ValueError("reference_status must match lifecycle_status")

        if self.primary_reference_repository is not None and not self.primary_reference_repository.strip():
            raise ValueError("primary_reference_repository must not be blank")
        if self.primary_reference_commit is not None and not self.primary_reference_commit.strip():
            raise ValueError("primary_reference_commit must not be blank")
        if (self.primary_reference_repository is None) != (self.primary_reference_commit is None):
            raise ValueError("primary_reference_repository and primary_reference_commit must be provided together")

        if self.supported_extraction_claims and not self.supported_shape_signatures:
            object.__setattr__(self, "supported_shape_signatures", self.supported_extraction_claims)
        if self.supported_shape_signatures and not self.supported_extraction_claims:
            object.__setattr__(self, "supported_extraction_claims", self.supported_shape_signatures)

        if self.unsupported_extraction_claims and not self.unsupported_shape_signatures:
            object.__setattr__(self, "unsupported_shape_signatures", self.unsupported_extraction_claims)
        if self.unsupported_shape_signatures and not self.unsupported_extraction_claims:
            object.__setattr__(self, "unsupported_extraction_claims", self.unsupported_shape_signatures)

        for field_name, values in (
            ("authority_scope", self.authority_scope),
            ("reference_ids", self.reference_ids),
            ("supported_extraction_claims", self.supported_extraction_claims),
            ("unsupported_extraction_claims", self.unsupported_extraction_claims),
            ("supported_shape_signatures", self.supported_shape_signatures),
            ("unsupported_shape_signatures", self.unsupported_shape_signatures),
            ("required_fields", self.required_fields),
            ("completeness_rules", self.completeness_rules),
            ("warning_mappings", self.warning_mappings),
            ("error_mappings", self.error_mappings),
            ("fixture_ids", self.fixture_ids),
            ("acceptance_matrix_rows", self.acceptance_matrix_rows),
            ("notes", self.notes),
        ):
            _validate_nonblank_values(field_name, values)


@dataclass(frozen=True, slots=True)
class ParserRequestEnvelope:
    """Normalized adapter request metadata with safe source references only."""

    request_id: str
    contract_name: str
    contract_version: str
    producer: str
    purpose: str
    compatibility_profile: ParserCompatibilityProfile
    safe_source_reference: str | None = None
    source_reference: ParserSourceReference | None = None
    source_boundary_outcome: SourceBoundaryOutcome | None = None
    configuration_revision_id: str | None = None
    safe_transport_reference: str | None = None
    message_id: str | None = None
    correlation_id: str | None = None
    causation_id: str | None = None
    idempotency_key: str | None = None
    requested_page_numbers: tuple[int, ...] = ()
    requested_unit_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for field_name in ("request_id", "contract_name", "contract_version", "producer", "purpose"):
            if not getattr(self, field_name).strip():
                raise ValueError(f"{field_name} must not be blank")
        if self.source_reference is not None and self.safe_source_reference is not None:
            if self.source_reference.bounded_value != self.safe_source_reference:
                raise ValueError("safe_source_reference must match source_reference.bounded_value")
        if self.source_boundary_outcome is not None and self.source_reference is not None:
            if self.source_boundary_outcome.source_reference != self.source_reference:
                raise ValueError("source_boundary_outcome.source_reference must match source_reference")


@dataclass(frozen=True, slots=True)
class TransportOutcomeReference:
    """Explicit transport outcome reference consumed by parser semantics."""

    transport_reference_id: str
    transport_status: TransportOutcomeStatus
    request_reference: str | None = None
    response_reference: str | None = None
    route_reference: str | None = None
    notes: tuple[str, ...] = ()
    evidence_references: tuple[ParserEvidenceReference, ...] = ()

    def __post_init__(self) -> None:
        if not self.transport_reference_id.strip():
            raise ValueError("transport_reference_id must not be blank")


@dataclass(frozen=True, slots=True)
class TransportResponseClassificationOutcome:
    """Semantic transport/provider/response classification for one adapter attempt."""

    classification_id: str
    status: (
        TransportOutcomeStatus
        | ParserOutcomeStatus
        | ReferenceOutcomeStatus
        | CompatibilityProfileLifecycleStatus
        | CompatibilityChangeClass
        | SourceBoundaryStatus
    )
    transport_status: TransportOutcomeStatus | None = None
    parser_status: ParserOutcomeStatus | None = None
    reference_status: ReferenceOutcomeStatus | CompatibilityProfileLifecycleStatus | None = None
    provider_response_evidence_class: ProviderResponseEvidenceClass = ProviderResponseEvidenceClass.UNCLASSIFIED
    response_completeness_status: ResponseCompletenessStatus = ResponseCompletenessStatus.UNVERIFIED
    response_restriction_signal: ResponseRestrictionSignal = ResponseRestrictionSignal.NONE
    classification_rule: ParserResponseClassificationRule | None = None
    transport_outcome: TransportOutcomeReference | None = None
    request_envelope: ParserRequestEnvelope | None = None
    warnings: tuple[ParserWarning, ...] = ()
    evidence_references: tuple[ParserEvidenceReference, ...] = ()
    explanation: ParserOutcomeExplanation | None = None
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.classification_id.strip():
            raise ValueError("classification_id must not be blank")
        _validate_nonblank_values("notes", self.notes)


@dataclass(frozen=True, slots=True)
class ParserOutcomeExplanation:
    """Read-only explanation that links outcome reason codes to safe evidence."""

    summary: str
    reason_code: str | None = None
    status: (
        ParserOutcomeStatus
        | TransportOutcomeStatus
        | ReferenceOutcomeStatus
        | CompatibilityProfileLifecycleStatus
        | CompatibilityChangeClass
        | SourceBoundaryStatus
        | None
    ) = None
    details: tuple[str, ...] = ()
    evidence_references: tuple[ParserEvidenceReference, ...] = ()
    warnings: tuple[ParserWarning, ...] = ()

    def __post_init__(self) -> None:
        if not self.summary.strip():
            raise ValueError("summary must not be blank")


@dataclass(frozen=True, slots=True)
class ParserAttemptOutcome:
    """Adapter-attempt classification separating transport and parser success."""

    attempt_id: str
    transport_status: TransportOutcomeStatus
    parser_status: ParserOutcomeStatus | None = None
    reference_status: ReferenceOutcomeStatus | CompatibilityProfileLifecycleStatus | None = None
    request_envelope: ParserRequestEnvelope | None = None
    transport_outcome: TransportOutcomeReference | None = None
    response_reference: str | None = None
    transport_response_classification: TransportResponseClassificationOutcome | None = None
    warnings: tuple[ParserWarning, ...] = ()
    evidence_references: tuple[ParserEvidenceReference, ...] = ()
    explanation: ParserOutcomeExplanation | None = None

    def __post_init__(self) -> None:
        if not self.attempt_id.strip():
            raise ValueError("attempt_id must not be blank")
        if self.transport_response_classification is not None:
            classification = self.transport_response_classification
            if classification.transport_outcome is not None and self.transport_outcome is not None:
                if classification.transport_outcome != self.transport_outcome:
                    raise ValueError("transport_response_classification.transport_outcome must match transport_outcome")
            if classification.transport_status is not None and classification.transport_status != self.transport_status:
                raise ValueError("transport_response_classification.transport_status must match transport_status")
            if classification.parser_status is not None and self.parser_status is not None:
                if classification.parser_status != self.parser_status:
                    raise ValueError("transport_response_classification.parser_status must match parser_status")
            if classification.reference_status is not None and self.reference_status is not None:
                if classification.reference_status != self.reference_status:
                    raise ValueError("transport_response_classification.reference_status must match reference_status")


@dataclass(frozen=True, slots=True)
class SearchSourceAnalysisOutcome:
    """Semantic analysis of a source reference before deeper extraction."""

    analysis_id: str
    request_envelope: ParserRequestEnvelope
    transport_outcome: TransportOutcomeReference | None
    status: (
        ParserOutcomeStatus
        | TransportOutcomeStatus
        | ReferenceOutcomeStatus
        | CompatibilityProfileLifecycleStatus
        | CompatibilityChangeClass
        | SourceBoundaryStatus
    )
    compatibility_profile: ParserCompatibilityProfile
    warnings: tuple[ParserWarning, ...] = ()
    evidence_references: tuple[ParserEvidenceReference, ...] = ()
    explanation: ParserOutcomeExplanation | None = None

    def __post_init__(self) -> None:
        if not self.analysis_id.strip():
            raise ValueError("analysis_id must not be blank")


@dataclass(frozen=True, slots=True)
class SearchConfigurationEvidence:
    """Safe provenance bundle for search-configuration extraction."""

    evidence_id: str
    request_envelope: ParserRequestEnvelope
    compatibility_profile: ParserCompatibilityProfile
    source_reference: ParserSourceReference | None = None
    source_boundary_outcome: SourceBoundaryOutcome | None = None
    transport_outcome: TransportOutcomeReference | None = None
    evidence_references: tuple[ParserEvidenceReference, ...] = ()
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.evidence_id.strip():
            raise ValueError("evidence_id must not be blank")
        _validate_nonblank_values("notes", self.notes)


@dataclass(frozen=True, slots=True)
class SearchConfigurationParameterCandidate:
    """Evidence-bound search parameter candidate with preserved values."""

    parameter_key: str
    parameter_value: str | None = None
    field_status: SearchConfigurationFieldStatus = SearchConfigurationFieldStatus.EVIDENCE_BOUND
    value_kind: SearchConfigurationValueKind = SearchConfigurationValueKind.KEY_VALUE_PAIR
    repeated_values: tuple[str, ...] = ()
    evidence_references: tuple[ParserEvidenceReference, ...] = ()
    warnings: tuple[ParserWarning, ...] = ()
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.parameter_key.strip():
            raise ValueError("parameter_key must not be blank")
        _validate_nonblank_values("repeated_values", self.repeated_values)
        _validate_nonblank_values("notes", self.notes)


@dataclass(frozen=True, slots=True)
class SearchConfigurationCandidate:
    """Evidence-bound search-configuration candidate."""

    candidate_id: str
    extraction_field: SearchConfigurationExtractionField
    field_status: SearchConfigurationFieldStatus
    value_kind: SearchConfigurationValueKind
    parameter_candidates: tuple[SearchConfigurationParameterCandidate, ...] = ()
    evidence_references: tuple[ParserEvidenceReference, ...] = ()
    warnings: tuple[ParserWarning, ...] = ()
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.candidate_id.strip():
            raise ValueError("candidate_id must not be blank")
        _validate_nonblank_values("notes", self.notes)


@dataclass(frozen=True, slots=True)
class SearchConfigurationExtractionOutcome:
    """Normalized search-configuration evidence for Scan handoff."""

    extraction_id: str
    request_envelope: ParserRequestEnvelope
    transport_outcome: TransportOutcomeReference | None
    status: (
        ParserOutcomeStatus
        | TransportOutcomeStatus
        | ReferenceOutcomeStatus
        | CompatibilityProfileLifecycleStatus
        | CompatibilityChangeClass
        | SourceBoundaryStatus
    )
    compatibility_profile: ParserCompatibilityProfile
    search_configuration_evidence: SearchConfigurationEvidence | None = None
    search_configuration_candidates: tuple[SearchConfigurationCandidate, ...] = ()
    parameter_candidates: tuple[SearchConfigurationParameterCandidate, ...] = ()
    normalized_geography_candidates: tuple[str, ...] = ()
    normalized_category_candidates: tuple[str, ...] = ()
    normalized_filter_candidates: tuple[str, ...] = ()
    observed_sort_context_reference: str | None = None
    warnings: tuple[ParserWarning, ...] = ()
    evidence_references: tuple[ParserEvidenceReference, ...] = ()
    explanation: ParserOutcomeExplanation | None = None

    def __post_init__(self) -> None:
        if not self.extraction_id.strip():
            raise ValueError("extraction_id must not be blank")
        if self.search_configuration_evidence is not None:
            if self.search_configuration_evidence.request_envelope != self.request_envelope:
                raise ValueError("search_configuration_evidence.request_envelope must match request_envelope")
            if self.search_configuration_evidence.compatibility_profile != self.compatibility_profile:
                raise ValueError("search_configuration_evidence.compatibility_profile must match compatibility_profile")


@dataclass(frozen=True, slots=True)
class ListingCardCandidate:
    """Listing-card candidate with evidence-gated optional fields."""

    listing_card_id: str
    title: str | None = None
    price_text: str | None = None
    listing_url_reference: str | None = None
    preview_image_reference: str | None = None
    phone: str | None = None
    seller: str | None = None
    seller_rating: str | None = None
    description: str | None = None
    warnings: tuple[ParserWarning, ...] = ()
    evidence_references: tuple[ParserEvidenceReference, ...] = ()

    def __post_init__(self) -> None:
        if not self.listing_card_id.strip():
            raise ValueError("listing_card_id must not be blank")


@dataclass(frozen=True, slots=True)
class NormalizedListingCandidate:
    """Normalized listing candidate whose card fields remain optional."""

    listing_candidate_id: str
    card_candidate: ListingCardCandidate
    geography: str | None = None
    category: str | None = None
    publication_order_reference: str | None = None
    sort_context_reference: str | None = None
    warnings: tuple[ParserWarning, ...] = ()
    evidence_references: tuple[ParserEvidenceReference, ...] = ()

    def __post_init__(self) -> None:
        if not self.listing_candidate_id.strip():
            raise ValueError("listing_candidate_id must not be blank")


@dataclass(frozen=True, slots=True)
class ListingPageParseOutcome:
    """Semantic parsing outcome for one page of listing candidates."""

    page_id: str
    request_envelope: ParserRequestEnvelope
    transport_outcome: TransportOutcomeReference | None
    status: (
        ParserOutcomeStatus
        | TransportOutcomeStatus
        | ReferenceOutcomeStatus
        | CompatibilityProfileLifecycleStatus
        | CompatibilityChangeClass
        | SourceBoundaryStatus
    )
    compatibility_profile: ParserCompatibilityProfile
    normalized_listing_candidates: tuple[NormalizedListingCandidate, ...] = ()
    card_candidates: tuple[ListingCardCandidate, ...] = ()
    warnings: tuple[ParserWarning, ...] = ()
    evidence_references: tuple[ParserEvidenceReference, ...] = ()
    explanation: ParserOutcomeExplanation | None = None

    def __post_init__(self) -> None:
        if not self.page_id.strip():
            raise ValueError("page_id must not be blank")


@dataclass(frozen=True, slots=True)
class ListingBatchParseOutcome:
    """Batch-level parsing outcome for independently classified pages."""

    batch_id: str
    request_envelope: ParserRequestEnvelope
    transport_outcome: TransportOutcomeReference | None
    status: (
        ParserOutcomeStatus
        | TransportOutcomeStatus
        | ReferenceOutcomeStatus
        | CompatibilityProfileLifecycleStatus
        | CompatibilityChangeClass
        | SourceBoundaryStatus
    )
    compatibility_profile: ParserCompatibilityProfile
    page_outcomes: tuple[ListingPageParseOutcome, ...] = ()
    warnings: tuple[ParserWarning, ...] = ()
    evidence_references: tuple[ParserEvidenceReference, ...] = ()
    explanation: ParserOutcomeExplanation | None = None

    def __post_init__(self) -> None:
        if not self.batch_id.strip():
            raise ValueError("batch_id must not be blank")


@dataclass(frozen=True, slots=True)
class ParserCompatibilityOutcome:
    """Read-only compatibility decision for a bounded evidence/profile set."""

    outcome_id: str
    compatibility_profile: ParserCompatibilityProfile
    lifecycle_status: CompatibilityProfileLifecycleStatus
    change_class: CompatibilityChangeClass
    status: (
        ParserOutcomeStatus
        | TransportOutcomeStatus
        | ReferenceOutcomeStatus
        | CompatibilityProfileLifecycleStatus
        | CompatibilityChangeClass
        | None
    ) = None
    warnings: tuple[ParserWarning, ...] = ()
    error_messages: tuple[str, ...] = ()
    revalidation_triggers: tuple[CompatibilityRevalidationTrigger, ...] = ()
    evidence_references: tuple[ParserEvidenceReference, ...] = ()
    explanation: ParserOutcomeExplanation | None = None

    def __post_init__(self) -> None:
        if not self.outcome_id.strip():
            raise ValueError("outcome_id must not be blank")


__all__: Final[tuple[str, ...]] = (
    "TransportOutcomeStatus",
    "ParserOutcomeStatus",
    "ProviderResponseEvidenceClass",
    "ResponseCompletenessStatus",
    "ResponseRestrictionSignal",
    "ReferenceOutcomeStatus",
    "CompatibilityProfileLifecycleStatus",
    "CompatibilityProfileAuthorityClass",
    "CompatibilityChangeClass",
    "CompatibilityRevalidationTrigger",
    "ParserWarningCode",
    "SearchConfigurationWarningCode",
    "SearchConfigurationExtractionField",
    "SearchConfigurationFieldStatus",
    "SearchConfigurationValueKind",
    "SourceReferenceKind",
    "SourceBoundaryStatus",
    "SourceBoundaryRiskCode",
    "SourceBoundaryPolicyRequirement",
    "ParserSourceReference",
    "SourceBoundaryOutcome",
    "ParserEvidenceReference",
    "ParserWarning",
    "ParserResponseClassificationRule",
    "ParserCompatibilityProfile",
    "ParserCompatibilityOutcome",
    "ParserRequestEnvelope",
    "TransportOutcomeReference",
    "TransportResponseClassificationOutcome",
    "ParserOutcomeExplanation",
    "ParserAttemptOutcome",
    "SearchSourceAnalysisOutcome",
    "SearchConfigurationEvidence",
    "SearchConfigurationParameterCandidate",
    "SearchConfigurationCandidate",
    "SearchConfigurationExtractionOutcome",
    "ListingCardCandidate",
    "NormalizedListingCandidate",
    "ListingPageParseOutcome",
    "ListingBatchParseOutcome",
)
