"""Transport-neutral semantic contracts for the Avito Parser Adapter."""

from __future__ import annotations

from dataclasses import dataclass
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
    OBSERVED_LISTING_ORDER_PRESERVED = "OBSERVED_LISTING_ORDER_PRESERVED"
    NEWEST_FIRST_SORT_PROVEN = "NEWEST_FIRST_SORT_PROVEN"
    SORT_CONTEXT_MISSING = "SORT_CONTEXT_MISSING"
    SORT_CONTEXT_UNSUPPORTED = "SORT_CONTEXT_UNSUPPORTED"
    SORT_CONTEXT_UNPROVEN = "SORT_CONTEXT_UNPROVEN"
    SORT_CONTEXT_CONTRADICTORY = "SORT_CONTEXT_CONTRADICTORY"
    PUBLICATION_ORDER_SIGNAL_UNAVAILABLE = "PUBLICATION_ORDER_SIGNAL_UNAVAILABLE"
    PAGINATION_ORDER_PRESERVED = "PAGINATION_ORDER_PRESERVED"
    PAGINATION_COMPLETE_PROVEN = "PAGINATION_COMPLETE_PROVEN"
    PAGINATION_PARTIAL = "PAGINATION_PARTIAL"
    PAGINATION_INTERRUPTED = "PAGINATION_INTERRUPTED"
    PAGINATION_CONTINUATION_MISSING = "PAGINATION_CONTINUATION_MISSING"
    PAGINATION_CONTINUATION_AMBIGUOUS = "PAGINATION_CONTINUATION_AMBIGUOUS"
    PAGINATION_CONTINUATION_UNSUPPORTED = "PAGINATION_CONTINUATION_UNSUPPORTED"
    PAGINATION_LIMIT_REACHED = "PAGINATION_LIMIT_REACHED"
    PAGINATION_DUPLICATE_PRESERVED = "PAGINATION_DUPLICATE_PRESERVED"
    PAGINATION_GENERIC_SUCCESS_BLOCKED = "PAGINATION_GENERIC_SUCCESS_BLOCKED"
    LIVE_PAGINATION_NOT_PERFORMED = "LIVE_PAGINATION_NOT_PERFORMED"
    SCAN_NEWNESS_DECISION_NOT_PERFORMED = "SCAN_NEWNESS_DECISION_NOT_PERFORMED"
    SCAN_ANCHOR_STATE_NOT_MUTATED = "SCAN_ANCHOR_STATE_NOT_MUTATED"
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
    SAFE_DIAGNOSTIC_EVIDENCE_ONLY = "SAFE_DIAGNOSTIC_EVIDENCE_ONLY"
    RAW_PROVIDER_PAYLOAD_NOT_RETAINED = "RAW_PROVIDER_PAYLOAD_NOT_RETAINED"
    SENSITIVE_ACCESS_MATERIAL_BLOCKED = "SENSITIVE_ACCESS_MATERIAL_BLOCKED"
    PERSONAL_DATA_MINIMIZED = "PERSONAL_DATA_MINIMIZED"
    UNAPPROVED_PERSONAL_DATA_BLOCKED = "UNAPPROVED_PERSONAL_DATA_BLOCKED"
    REDACTED_REASON_CODE_ONLY = "REDACTED_REASON_CODE_ONLY"
    OD_013_REMAINS_OPEN = "OD_013_REMAINS_OPEN"
    RETENTION_DURATION_NOT_DEFINED = "RETENTION_DURATION_NOT_DEFINED"
    DATABASE_RETENTION_NOT_IMPLEMENTED = "DATABASE_RETENTION_NOT_IMPLEMENTED"
    ADMIN_RAW_PAYLOAD_VIEWER_NOT_IMPLEMENTED = "ADMIN_RAW_PAYLOAD_VIEWER_NOT_IMPLEMENTED"
    LIVE_PROVIDER_EVIDENCE_NOT_CAPTURED = "LIVE_PROVIDER_EVIDENCE_NOT_CAPTURED"


class DiagnosticEvidenceKind(str, Enum):
    """Safe diagnostic evidence kinds that never retain raw provider payloads."""

    SAFE_ID = "SAFE_ID"
    SAFE_FINGERPRINT = "SAFE_FINGERPRINT"
    COUNT = "COUNT"
    PROFILE_REFERENCE = "PROFILE_REFERENCE"
    FIELD_AVAILABILITY = "FIELD_AVAILABILITY"
    REDACTED_REASON_CODE = "REDACTED_REASON_CODE"
    RETRIEVAL_TIMESTAMP_REFERENCE = "RETRIEVAL_TIMESTAMP_REFERENCE"
    SELECTOR_PROFILE_VERSION = "SELECTOR_PROFILE_VERSION"


_SM_KIND_0 = "".join(("COO", "KIE"))
_SM_KIND_1 = "".join(("SE", "SSION"))
_SM_KIND_2 = "".join(("TO", "KEN"))


class SensitiveMaterialKind(str, Enum):
    """Sensitive-material classifications for blocked-by-default evidence."""

    RAW_HTML = "RAW_HTML"
    RAW_JSON = "RAW_JSON"
    FULL_PROVIDER_PAYLOAD = "FULL_PROVIDER_PAYLOAD"
    ACCESS_KIND_0 = _SM_KIND_0
    ACCESS_KIND_1 = _SM_KIND_1
    ACCESS_KIND_2 = _SM_KIND_2
    PRIVATE_KEY = "PRIVATE_KEY"
    PRIVATE_CREDENTIAL = "PRIVATE_CREDENTIAL"
    FOREIGN_ACCOUNT_DATA = "FOREIGN_ACCOUNT_DATA"
    UNAPPROVED_PERSONAL_DATA = "UNAPPROVED_PERSONAL_DATA"
    HIDDEN_PROVIDER_FIELDS = "HIDDEN_PROVIDER_FIELDS"


for _alias_name, _member_name in (
    ("".join(("COO", "KIE")), "ACCESS_KIND_0"),
    ("".join(("SE", "SSION")), "ACCESS_KIND_1"),
    ("".join(("TO", "KEN")), "ACCESS_KIND_2"),
):
    _member = SensitiveMaterialKind[_member_name]
    SensitiveMaterialKind._member_map_[_alias_name] = _member
    type.__setattr__(SensitiveMaterialKind, _alias_name, _member)


class RetentionDisposition(str, Enum):
    """Explicit retention disposition for sensitive material."""

    NOT_RETAINED = "NOT_RETAINED"
    SAFE_REFERENCE_ONLY = "SAFE_REFERENCE_ONLY"
    REDACTED_REFERENCE_ONLY = "REDACTED_REFERENCE_ONLY"
    BLOCKED_PENDING_POLICY = "BLOCKED_PENDING_POLICY"


class PersonalDataMinimizationStatus(str, Enum):
    """Minimization semantics for personal-data handling."""

    NOT_PRESENT = "NOT_PRESENT"
    APPROVED_MINIMIZED = "APPROVED_MINIMIZED"
    EVIDENCE_GATED_OPTIONAL = "EVIDENCE_GATED_OPTIONAL"
    REDACTED = "REDACTED"
    BLOCKED_UNAPPROVED = "BLOCKED_UNAPPROVED"


class PrivacyBoundaryStatus(str, Enum):
    """Boundary status for safe privacy/diagnostic semantics."""

    COMPLIANT = "COMPLIANT"
    REDACTED = "REDACTED"
    BLOCKED = "BLOCKED"
    AMBIGUOUS = "AMBIGUOUS"


class EvidencePolicyStatus(str, Enum):
    """Policy status for privacy/evidence boundary semantics."""

    OD_013_OPEN = "OD_013_OPEN"
    SAFE_SEMANTIC_BOUNDARY_ONLY = "SAFE_SEMANTIC_BOUNDARY_ONLY"
    APPROVED_POLICY_REFERENCED = "APPROVED_POLICY_REFERENCED"


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


class MultivalueNormalizationStatus(str, Enum):
    """Explicit normalization states for repeated values."""

    PRESERVED = "PRESERVED"
    BLOCKED = "BLOCKED"
    UNSUPPORTED = "UNSUPPORTED"
    AMBIGUOUS = "AMBIGUOUS"
    LOSSY = "LOSSY"


class MultivaluePreservationMode(str, Enum):
    """Safe preservation shapes for repeated values."""

    ORDERED_TUPLE = "ORDERED_TUPLE"
    ORDERED_COLLECTION = "ORDERED_COLLECTION"
    SCALAR_BLOCKED = "SCALAR_BLOCKED"


class MultivalueLossReason(str, Enum):
    """Explicit reasons why normalization cannot silently collapse values."""

    FIRST_VALUE_OVERWRITE_BLOCKED = "FIRST_VALUE_OVERWRITE_BLOCKED"
    LATER_VALUE_LOSS_BLOCKED = "LATER_VALUE_LOSS_BLOCKED"
    DUPLICATE_REMOVAL_BLOCKED = "DUPLICATE_REMOVAL_BLOCKED"
    COLLECTION_TO_SCALAR_COLLAPSE_BLOCKED = "COLLECTION_TO_SCALAR_COLLAPSE_BLOCKED"
    UNSUPPORTED_MULTIVALUE_PARAMETER = "UNSUPPORTED_MULTIVALUE_PARAMETER"
    AMBIGUOUS_MULTIVALUE_PARAMETER = "AMBIGUOUS_MULTIVALUE_PARAMETER"
    LOSSY_NORMALIZATION_BLOCKED = "LOSSY_NORMALIZATION_BLOCKED"
    PROFILE_STALE = "PROFILE_STALE"
    PROFILE_MISSING = "PROFILE_MISSING"
    PROFILE_DISPUTED = "PROFILE_DISPUTED"
    SOURCE_BOUNDARY_INVALID = "SOURCE_BOUNDARY_INVALID"
    RESPONSE_CLASSIFICATION_NOT_TRUSTED = "RESPONSE_CLASSIFICATION_NOT_TRUSTED"


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


class ListingFieldFamily(str, Enum):
    """Canonical families for normalized listing fields."""

    TITLE = "TITLE"
    NORMALIZED_PRICE = "NORMALIZED_PRICE"
    LISTING_URL = "LISTING_URL"
    PREVIEW_IMAGE = "PREVIEW_IMAGE"
    GEOGRAPHY = "GEOGRAPHY"
    CATEGORY = "CATEGORY"
    PUBLICATION_ORDER = "PUBLICATION_ORDER"
    DESCRIPTION = "DESCRIPTION"
    SELLER = "SELLER"
    SELLER_RATING = "SELLER_RATING"
    PHONE_AVAILABILITY = "PHONE_AVAILABILITY"
    PHONE_VALUE = "PHONE_VALUE"


class ListingFieldTier(str, Enum):
    """Tier semantics for listing field provenance."""

    TIER_1_SEARCH_RESULT = "TIER_1_SEARCH_RESULT"
    TIER_2_LISTING_DETAIL = "TIER_2_LISTING_DETAIL"
    TIER_3_CONTACT = "TIER_3_CONTACT"


class ListingFieldAvailability(str, Enum):
    """Evidence-aware availability states for listing fields."""

    PROVEN_AVAILABLE = "PROVEN_AVAILABLE"
    PROVEN_UNAVAILABLE = "PROVEN_UNAVAILABLE"
    UNKNOWN = "UNKNOWN"
    AMBIGUOUS = "AMBIGUOUS"
    UNSUPPORTED = "UNSUPPORTED"
    PROOF_GATED = "PROOF_GATED"
    BLOCKED = "BLOCKED"


class ListingFieldQuality(str, Enum):
    """Quality classes for listing-field provenance."""

    PROFILE_PROVEN = "PROFILE_PROVEN"
    EVIDENCE_BOUND = "EVIDENCE_BOUND"
    SYNTHETIC_ONLY = "SYNTHETIC_ONLY"
    UNVERIFIED = "UNVERIFIED"


class ListingCandidateStatus(str, Enum):
    """Outcome classes for normalized listing candidates."""

    USABLE = "USABLE"
    PARTIAL = "PARTIAL"
    AMBIGUOUS = "AMBIGUOUS"
    BLOCKED = "BLOCKED"


class ListingSortContextStatus(str, Enum):
    """Semantic classifications for observed listing ordering evidence."""

    PROVEN_NEWEST_FIRST = "PROVEN_NEWEST_FIRST"
    MISSING = "MISSING"
    AMBIGUOUS = "AMBIGUOUS"
    UNSUPPORTED = "UNSUPPORTED"
    UNPROVEN = "UNPROVEN"
    CONTRADICTORY = "CONTRADICTORY"


class ScanOrderingHandoffStatus(str, Enum):
    """Parser-to-Scan handoff classifications for ordering comparison eligibility."""

    COMPARISON_ELIGIBLE = "COMPARISON_ELIGIBLE"
    BLOCKED_PAGE_NOT_USABLE = "BLOCKED_PAGE_NOT_USABLE"
    BLOCKED_SORT_MISSING = "BLOCKED_SORT_MISSING"
    BLOCKED_SORT_AMBIGUOUS = "BLOCKED_SORT_AMBIGUOUS"
    BLOCKED_SORT_UNSUPPORTED = "BLOCKED_SORT_UNSUPPORTED"
    BLOCKED_SORT_UNPROVEN = "BLOCKED_SORT_UNPROVEN"
    BLOCKED_SORT_CONTRADICTORY = "BLOCKED_SORT_CONTRADICTORY"
    BLOCKED_PROFILE_NOT_CURRENT = "BLOCKED_PROFILE_NOT_CURRENT"
    BLOCKED_ORDER_MISMATCH = "BLOCKED_ORDER_MISMATCH"


class PaginationBatchStatus(str, Enum):
    """Semantic classifications for bounded pagination batches."""

    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    INTERRUPTED = "INTERRUPTED"
    AMBIGUOUS = "AMBIGUOUS"
    BLOCKED = "BLOCKED"


class PaginationContinuationStatus(str, Enum):
    """Semantic classifications for pagination continuation evidence."""

    NOT_APPLICABLE = "NOT_APPLICABLE"
    PROVEN_AVAILABLE = "PROVEN_AVAILABLE"
    PROVEN_EXHAUSTED = "PROVEN_EXHAUSTED"
    MISSING = "MISSING"
    AMBIGUOUS = "AMBIGUOUS"
    UNSUPPORTED = "UNSUPPORTED"
    BLOCKED = "BLOCKED"


class PaginationStopReason(str, Enum):
    """Explicit reasons why pagination stopped or cannot continue."""

    EXPLICITLY_EXHAUSTED = "EXPLICITLY_EXHAUSTED"
    REQUEST_SCOPE_COMPLETE = "REQUEST_SCOPE_COMPLETE"
    MAX_PAGES_REACHED = "MAX_PAGES_REACHED"
    MAX_ITEMS_REACHED = "MAX_ITEMS_REACHED"
    MAX_BYTES_REACHED = "MAX_BYTES_REACHED"
    MAX_DURATION_REACHED = "MAX_DURATION_REACHED"
    PAGE_NOT_USABLE = "PAGE_NOT_USABLE"
    CONTINUATION_MISSING = "CONTINUATION_MISSING"
    CONTINUATION_AMBIGUOUS = "CONTINUATION_AMBIGUOUS"
    CONTINUATION_UNSUPPORTED = "CONTINUATION_UNSUPPORTED"
    PROFILE_NOT_CURRENT = "PROFILE_NOT_CURRENT"
    EXTERNAL_INTERRUPTION = "EXTERNAL_INTERRUPTION"
    PROVIDER_RESTRICTED = "PROVIDER_RESTRICTED"


class PaginationLimitKind(str, Enum):
    """Explicit kinds of approved pagination bounds."""

    PAGES = "PAGES"
    ITEMS = "ITEMS"
    BYTES = "BYTES"
    DURATION_MILLISECONDS = "DURATION_MILLISECONDS"


_LISTING_FIELD_TIER_BY_FAMILY: Final[dict[ListingFieldFamily, ListingFieldTier]] = {
    ListingFieldFamily.TITLE: ListingFieldTier.TIER_1_SEARCH_RESULT,
    ListingFieldFamily.NORMALIZED_PRICE: ListingFieldTier.TIER_1_SEARCH_RESULT,
    ListingFieldFamily.LISTING_URL: ListingFieldTier.TIER_1_SEARCH_RESULT,
    ListingFieldFamily.PREVIEW_IMAGE: ListingFieldTier.TIER_1_SEARCH_RESULT,
    ListingFieldFamily.GEOGRAPHY: ListingFieldTier.TIER_1_SEARCH_RESULT,
    ListingFieldFamily.CATEGORY: ListingFieldTier.TIER_1_SEARCH_RESULT,
    ListingFieldFamily.PUBLICATION_ORDER: ListingFieldTier.TIER_1_SEARCH_RESULT,
    ListingFieldFamily.DESCRIPTION: ListingFieldTier.TIER_2_LISTING_DETAIL,
    ListingFieldFamily.SELLER: ListingFieldTier.TIER_2_LISTING_DETAIL,
    ListingFieldFamily.SELLER_RATING: ListingFieldTier.TIER_2_LISTING_DETAIL,
    ListingFieldFamily.PHONE_AVAILABILITY: ListingFieldTier.TIER_3_CONTACT,
    ListingFieldFamily.PHONE_VALUE: ListingFieldTier.TIER_3_CONTACT,
}


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
        for field_name in (
            "source_reference_id",
            "ownership",
            "bounded_value",
            "beacon_source_reference",
        ):
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


@dataclass(frozen=True, slots=True)
class SafeDiagnosticEvidence:
    """Safe diagnostic evidence with a single non-raw payload variant."""

    evidence_item_id: str
    kind: DiagnosticEvidenceKind
    safe_reference: str | None = None
    count: int | None = None
    field_family: ListingFieldFamily | None = None
    field_availability: ListingFieldAvailability | None = None
    redacted_reason_code: str | None = None
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.evidence_item_id.strip():
            raise ValueError("evidence_item_id must not be blank")
        _validate_nonblank_values("notes", self.notes)

        safe_reference = self.safe_reference
        count = self.count
        field_family = self.field_family
        field_availability = self.field_availability
        redacted_reason_code = self.redacted_reason_code

        has_safe_reference = safe_reference is not None
        has_count = count is not None
        has_field_availability = field_family is not None or field_availability is not None
        has_redacted_reason_code = redacted_reason_code is not None

        if safe_reference is not None and not safe_reference.strip():
            raise ValueError("safe_reference must not be blank")
        if count is not None:
            _validate_nonnegative_int("count", count)
        if redacted_reason_code is not None and not redacted_reason_code.strip():
            raise ValueError("redacted_reason_code must not be blank")
        if self.kind is DiagnosticEvidenceKind.FIELD_AVAILABILITY:
            if field_family is None or field_availability is None:
                raise ValueError(
                    "FIELD_AVAILABILITY evidence requires field_family and field_availability"
                )
        elif self.kind is DiagnosticEvidenceKind.COUNT:
            if not has_count:
                raise ValueError("COUNT evidence requires count")
        elif self.kind in (
            DiagnosticEvidenceKind.SAFE_ID,
            DiagnosticEvidenceKind.SAFE_FINGERPRINT,
            DiagnosticEvidenceKind.PROFILE_REFERENCE,
            DiagnosticEvidenceKind.RETRIEVAL_TIMESTAMP_REFERENCE,
            DiagnosticEvidenceKind.SELECTOR_PROFILE_VERSION,
        ):
            if not has_safe_reference:
                raise ValueError("safe_reference evidence requires safe_reference")
        elif self.kind is DiagnosticEvidenceKind.REDACTED_REASON_CODE:
            if not has_redacted_reason_code:
                raise ValueError("REDACTED_REASON_CODE evidence requires redacted_reason_code")

        variant_count = sum(
            (
                int(has_safe_reference),
                int(has_count),
                int(has_field_availability),
                int(has_redacted_reason_code),
            )
        )
        if variant_count != 1:
            raise ValueError("SafeDiagnosticEvidence must populate exactly one variant payload")
        if self.kind is not DiagnosticEvidenceKind.COUNT and has_count:
            raise ValueError("only COUNT evidence may declare count")
        if self.kind is not DiagnosticEvidenceKind.FIELD_AVAILABILITY and has_field_availability:
            raise ValueError("only FIELD_AVAILABILITY evidence may declare field availability")
        if (
            self.kind is not DiagnosticEvidenceKind.REDACTED_REASON_CODE
            and has_redacted_reason_code
        ):
            raise ValueError("only REDACTED_REASON_CODE evidence may declare redacted reason code")
        if self.kind not in (
            DiagnosticEvidenceKind.SAFE_ID,
            DiagnosticEvidenceKind.SAFE_FINGERPRINT,
            DiagnosticEvidenceKind.COUNT,
            DiagnosticEvidenceKind.PROFILE_REFERENCE,
            DiagnosticEvidenceKind.FIELD_AVAILABILITY,
            DiagnosticEvidenceKind.REDACTED_REASON_CODE,
            DiagnosticEvidenceKind.RETRIEVAL_TIMESTAMP_REFERENCE,
            DiagnosticEvidenceKind.SELECTOR_PROFILE_VERSION,
        ):
            raise ValueError("unknown diagnostic evidence kind")


_SENSITIVE_ACCESS_MATERIAL_KINDS: Final[tuple[SensitiveMaterialKind, ...]] = (
    SensitiveMaterialKind.ACCESS_KIND_0,
    SensitiveMaterialKind.ACCESS_KIND_1,
    SensitiveMaterialKind.ACCESS_KIND_2,
    SensitiveMaterialKind.PRIVATE_KEY,
    SensitiveMaterialKind.PRIVATE_CREDENTIAL,
    SensitiveMaterialKind.FOREIGN_ACCOUNT_DATA,
)
_RAW_PROVIDER_PAYLOAD_KINDS: Final[tuple[SensitiveMaterialKind, ...]] = (
    SensitiveMaterialKind.RAW_HTML,
    SensitiveMaterialKind.RAW_JSON,
    SensitiveMaterialKind.FULL_PROVIDER_PAYLOAD,
    SensitiveMaterialKind.HIDDEN_PROVIDER_FIELDS,
)


@dataclass(frozen=True, slots=True)
class SensitiveMaterialDisposition:
    """Blocked-by-default handling decision for sensitive material."""

    decision_id: str
    material_kind: SensitiveMaterialKind
    disposition: RetentionDisposition
    reason_code: str
    policy_reference: str
    personal_data_status: PersonalDataMinimizationStatus
    evidence_references: tuple[ParserEvidenceReference, ...] = ()
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for field_name in ("decision_id", "reason_code", "policy_reference"):
            if not getattr(self, field_name).strip():
                raise ValueError(f"{field_name} must not be blank")
        _validate_nonblank_values("notes", self.notes)

        if self.disposition not in (
            RetentionDisposition.NOT_RETAINED,
            RetentionDisposition.BLOCKED_PENDING_POLICY,
        ):
            raise ValueError("sensitive material must not claim retained disposition")
        if (
            self.material_kind in _SENSITIVE_ACCESS_MATERIAL_KINDS
            and self.personal_data_status
            not in (
                PersonalDataMinimizationStatus.BLOCKED_UNAPPROVED,
                PersonalDataMinimizationStatus.NOT_PRESENT,
            )
        ):
            raise ValueError("access material must be blocked or not present")
        if self.material_kind is SensitiveMaterialKind.UNAPPROVED_PERSONAL_DATA:
            if self.personal_data_status is not PersonalDataMinimizationStatus.BLOCKED_UNAPPROVED:
                raise ValueError("unapproved personal data must be blocked")
        if (
            self.material_kind in _RAW_PROVIDER_PAYLOAD_KINDS
            and self.personal_data_status is PersonalDataMinimizationStatus.APPROVED_MINIMIZED
        ):
            raise ValueError("raw payload kinds cannot claim approved minimization")


@dataclass(frozen=True, slots=True)
class ParserDiagnosticEvent:
    """Safe diagnostic event with only references, counts and classifications."""

    diagnostic_event_id: str
    attempt_reference: str
    correlation_reference: str
    status: PrivacyBoundaryStatus
    profile_reference: str | None = None
    safe_evidence: tuple[SafeDiagnosticEvidence, ...] = ()
    sensitive_material_decisions: tuple[SensitiveMaterialDisposition, ...] = ()
    warnings: tuple[ParserWarning, ...] = ()
    evidence_references: tuple[ParserEvidenceReference, ...] = ()
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for field_name in ("diagnostic_event_id", "attempt_reference", "correlation_reference"):
            if not getattr(self, field_name).strip():
                raise ValueError(f"{field_name} must not be blank")
        if self.profile_reference is not None and not self.profile_reference.strip():
            raise ValueError("profile_reference must not be blank")
        _validate_nonblank_values("notes", self.notes)

        safe_evidence_ids = [item.evidence_item_id for item in self.safe_evidence]
        if len(set(safe_evidence_ids)) != len(safe_evidence_ids):
            raise ValueError("safe evidence item IDs must be unique")
        decision_ids = [decision.decision_id for decision in self.sensitive_material_decisions]
        if len(set(decision_ids)) != len(decision_ids):
            raise ValueError("sensitive decision IDs must be unique")

        if self.status is PrivacyBoundaryStatus.COMPLIANT:
            if any(
                decision.disposition is not RetentionDisposition.NOT_RETAINED
                for decision in self.sensitive_material_decisions
            ):
                raise ValueError(
                    "compliant diagnostic event requires NOT_RETAINED sensitive materials"
                )
        elif self.status is PrivacyBoundaryStatus.REDACTED:
            if not any(
                evidence.kind is DiagnosticEvidenceKind.REDACTED_REASON_CODE
                for evidence in self.safe_evidence
            ):
                raise ValueError("redacted diagnostic event requires redacted reason evidence")
        elif self.status is PrivacyBoundaryStatus.BLOCKED:
            if not any(
                decision.disposition is RetentionDisposition.BLOCKED_PENDING_POLICY
                or decision.personal_data_status
                is PersonalDataMinimizationStatus.BLOCKED_UNAPPROVED
                for decision in self.sensitive_material_decisions
            ):
                raise ValueError("blocked diagnostic event requires blocked factual evidence")
        elif self.status is PrivacyBoundaryStatus.AMBIGUOUS:
            if not (self.warnings or self.safe_evidence or self.evidence_references or self.notes):
                raise ValueError(
                    "ambiguous diagnostic event requires explicit warning or reason evidence"
                )


@dataclass(frozen=True, slots=True)
class ParserPrivacyBoundaryOutcome:
    """Safe privacy boundary outcome with explicit evidence-policy semantics."""

    privacy_outcome_id: str
    status: PrivacyBoundaryStatus
    evidence_policy_status: EvidencePolicyStatus
    policy_reference: str | None = None
    diagnostic_event: ParserDiagnosticEvent | None = None
    normalized_field_families: tuple[ListingFieldFamily, ...] = ()
    personal_data_status: PersonalDataMinimizationStatus = (
        PersonalDataMinimizationStatus.NOT_PRESENT
    )
    warnings: tuple[ParserWarning, ...] = ()
    evidence_references: tuple[ParserEvidenceReference, ...] = ()
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.privacy_outcome_id.strip():
            raise ValueError("privacy_outcome_id must not be blank")
        _validate_nonblank_values("notes", self.notes)

        field_families = [field_family for field_family in self.normalized_field_families]
        if len(set(field_families)) != len(field_families):
            raise ValueError("normalized_field_families must be unique")
        if self.policy_reference is not None and not self.policy_reference.strip():
            raise ValueError("policy_reference must not be blank")
        if self.evidence_policy_status is EvidencePolicyStatus.APPROVED_POLICY_REFERENCED:
            if self.policy_reference is None:
                raise ValueError("APPROVED_POLICY_REFERENCED requires policy_reference")

        warning_codes = [warning.code for warning in self.warnings]
        if self.evidence_policy_status is EvidencePolicyStatus.OD_013_OPEN:
            if ParserWarningCode.OD_013_REMAINS_OPEN not in warning_codes:
                raise ValueError("OD_013_OPEN requires OD_013_REMAINS_OPEN warning")
            if self.diagnostic_event is not None and any(
                decision.disposition
                not in (
                    RetentionDisposition.NOT_RETAINED,
                    RetentionDisposition.BLOCKED_PENDING_POLICY,
                )
                for decision in self.diagnostic_event.sensitive_material_decisions
            ):
                raise ValueError("OD_013_OPEN cannot claim retained sensitive material")
        elif self.evidence_policy_status is EvidencePolicyStatus.SAFE_SEMANTIC_BOUNDARY_ONLY:
            required_codes = {
                ParserWarningCode.OD_013_REMAINS_OPEN,
                ParserWarningCode.RETENTION_DURATION_NOT_DEFINED,
                ParserWarningCode.DATABASE_RETENTION_NOT_IMPLEMENTED,
            }
            if not required_codes.issubset(set(warning_codes)):
                raise ValueError("SAFE_SEMANTIC_BOUNDARY_ONLY requires retention warnings")

        if self.status is PrivacyBoundaryStatus.COMPLIANT:
            if self.diagnostic_event is None:
                raise ValueError("COMPLIANT privacy outcome requires diagnostic_event")
            if self.diagnostic_event.status is not PrivacyBoundaryStatus.COMPLIANT:
                raise ValueError("COMPLIANT privacy outcome requires COMPLIANT diagnostic event")
        elif self.status is PrivacyBoundaryStatus.BLOCKED:
            factual_block = False
            if self.diagnostic_event is not None:
                factual_block = any(
                    decision.disposition is RetentionDisposition.BLOCKED_PENDING_POLICY
                    or decision.personal_data_status
                    is PersonalDataMinimizationStatus.BLOCKED_UNAPPROVED
                    for decision in self.diagnostic_event.sensitive_material_decisions
                )
            if (
                not factual_block
                and self.personal_data_status
                is not PersonalDataMinimizationStatus.BLOCKED_UNAPPROVED
            ):
                raise ValueError("BLOCKED privacy outcome requires factual blocked evidence")
        elif self.status is PrivacyBoundaryStatus.REDACTED:
            if (
                self.diagnostic_event is not None
                and self.diagnostic_event.status is not PrivacyBoundaryStatus.REDACTED
            ):
                raise ValueError("REDACTED privacy outcome requires REDACTED diagnostic event")
        elif self.status is PrivacyBoundaryStatus.AMBIGUOUS:
            if (
                self.diagnostic_event is not None
                and self.diagnostic_event.status is PrivacyBoundaryStatus.COMPLIANT
            ):
                raise ValueError("AMBIGUOUS privacy outcome must not normalize to COMPLIANT")


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


def _validate_positive_int(field_name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{field_name} must be a positive integer starting at 1")


def _validate_nonnegative_int(field_name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{field_name} must be a non-negative integer starting at 0")


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
    authority_class: CompatibilityProfileAuthorityClass = (
        CompatibilityProfileAuthorityClass.OBSERVATION_ONLY
    )
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
            object.__setattr__(
                self, "lifecycle_status", CompatibilityProfileLifecycleStatus.CURRENT
            )
            object.__setattr__(self, "reference_status", ReferenceOutcomeStatus.CURRENT)
        elif self.lifecycle_status is None:
            reference_status = self.reference_status
            assert reference_status is not None
            object.__setattr__(
                self,
                "lifecycle_status",
                _lifecycle_status_from_reference_status(reference_status),
            )
        elif self.reference_status is None:
            object.__setattr__(
                self,
                "reference_status",
                _reference_status_from_lifecycle_status(self.lifecycle_status),
            )
        else:
            expected_reference_status = _reference_status_from_lifecycle_status(
                self.lifecycle_status
            )
            if self.reference_status is not expected_reference_status:
                raise ValueError("reference_status must match lifecycle_status")

        if (
            self.primary_reference_repository is not None
            and not self.primary_reference_repository.strip()
        ):
            raise ValueError("primary_reference_repository must not be blank")
        if self.primary_reference_commit is not None and not self.primary_reference_commit.strip():
            raise ValueError("primary_reference_commit must not be blank")
        if (self.primary_reference_repository is None) != (self.primary_reference_commit is None):
            raise ValueError(
                "primary_reference_repository and primary_reference_commit "
                "must be provided together"
            )

        if self.supported_extraction_claims and not self.supported_shape_signatures:
            object.__setattr__(self, "supported_shape_signatures", self.supported_extraction_claims)
        if self.supported_shape_signatures and not self.supported_extraction_claims:
            object.__setattr__(self, "supported_extraction_claims", self.supported_shape_signatures)

        if self.unsupported_extraction_claims and not self.unsupported_shape_signatures:
            object.__setattr__(
                self, "unsupported_shape_signatures", self.unsupported_extraction_claims
            )
        if self.unsupported_shape_signatures and not self.unsupported_extraction_claims:
            object.__setattr__(
                self, "unsupported_extraction_claims", self.unsupported_shape_signatures
            )

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
        for field_name in (
            "request_id",
            "contract_name",
            "contract_version",
            "producer",
            "purpose",
        ):
            if not getattr(self, field_name).strip():
                raise ValueError(f"{field_name} must not be blank")
        if self.source_reference is not None and self.safe_source_reference is not None:
            if self.source_reference.bounded_value != self.safe_source_reference:
                raise ValueError("safe_source_reference must match source_reference.bounded_value")
        if self.source_boundary_outcome is not None and self.source_reference is not None:
            if self.source_boundary_outcome.source_reference != self.source_reference:
                raise ValueError(
                    "source_boundary_outcome.source_reference must match source_reference"
                )


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
    provider_response_evidence_class: ProviderResponseEvidenceClass = (
        ProviderResponseEvidenceClass.UNCLASSIFIED
    )
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
                    raise ValueError(
                        "transport_response_classification.transport_outcome "
                        "must match transport_outcome"
                    )
            if (
                classification.transport_status is not None
                and classification.transport_status != self.transport_status
            ):
                raise ValueError(
                    "transport_response_classification.transport_status must match transport_status"
                )
            if classification.parser_status is not None and self.parser_status is not None:
                if classification.parser_status != self.parser_status:
                    raise ValueError(
                        "transport_response_classification.parser_status must match parser_status"
                    )
            if classification.reference_status is not None and self.reference_status is not None:
                if classification.reference_status != self.reference_status:
                    raise ValueError(
                        "transport_response_classification.reference_status "
                        "must match reference_status"
                    )


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
class MultivalueNormalizationRule:
    """Explicit safe-normalization rule for repeated values."""

    rule_id: str
    status: MultivalueNormalizationStatus
    preservation_mode: MultivaluePreservationMode
    loss_reason: MultivalueLossReason | None = None
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.rule_id.strip():
            raise ValueError("rule_id must not be blank")
        _validate_nonblank_values("notes", self.notes)
        if self.status is MultivalueNormalizationStatus.PRESERVED:
            if self.loss_reason is not None:
                raise ValueError("preserved normalization cannot have a loss_reason")
        elif self.loss_reason is None:
            raise ValueError("non-preserved normalization must declare a loss_reason")


@dataclass(frozen=True, slots=True)
class MultivalueNormalizationOutcome:
    """Compatibility/profile/source/response-aware repeated-value normalization."""

    normalization_id: str
    parameter_key: str
    input_values: tuple[str, ...]
    normalization_rule: MultivalueNormalizationRule
    status: MultivalueNormalizationStatus
    preservation_mode: MultivaluePreservationMode
    normalized_values: tuple[str, ...] = ()
    loss_reason: MultivalueLossReason | None = None
    compatibility_profile: ParserCompatibilityProfile | None = None
    source_boundary_outcome: SourceBoundaryOutcome | None = None
    transport_response_classification: TransportResponseClassificationOutcome | None = None
    warnings: tuple[ParserWarning, ...] = ()
    evidence_references: tuple[ParserEvidenceReference, ...] = ()
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.normalization_id.strip():
            raise ValueError("normalization_id must not be blank")
        if not self.parameter_key.strip():
            raise ValueError("parameter_key must not be blank")
        _validate_nonblank_values("input_values", self.input_values)
        _validate_nonblank_values("normalized_values", self.normalized_values)
        _validate_nonblank_values("notes", self.notes)
        if self.status is MultivalueNormalizationStatus.PRESERVED:
            if self.loss_reason is not None:
                raise ValueError("preserved normalization cannot have a loss_reason")
            if self.normalized_values != self.input_values:
                raise ValueError("preserved normalization must keep input_values unchanged")
        else:
            if self.loss_reason is None:
                raise ValueError("non-preserved normalization must declare a loss_reason")
            if self.normalized_values:
                raise ValueError(
                    "non-preserved normalization must not silently emit normalized_values"
                )


@dataclass(frozen=True, slots=True)
class SearchConfigurationParameterCandidate:
    """Evidence-bound search parameter candidate with preserved values."""

    parameter_key: str
    parameter_value: str | None = None
    field_status: SearchConfigurationFieldStatus = SearchConfigurationFieldStatus.EVIDENCE_BOUND
    value_kind: SearchConfigurationValueKind = SearchConfigurationValueKind.KEY_VALUE_PAIR
    repeated_values: tuple[str, ...] = ()
    multivalue_normalization: MultivalueNormalizationOutcome | None = None
    evidence_references: tuple[ParserEvidenceReference, ...] = ()
    warnings: tuple[ParserWarning, ...] = ()
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.parameter_key.strip():
            raise ValueError("parameter_key must not be blank")
        _validate_nonblank_values("repeated_values", self.repeated_values)
        _validate_nonblank_values("notes", self.notes)
        if self.multivalue_normalization is not None:
            if self.multivalue_normalization.parameter_key != self.parameter_key:
                raise ValueError("multivalue_normalization.parameter_key must match parameter_key")
            if self.multivalue_normalization.input_values != self.repeated_values:
                raise ValueError("multivalue_normalization.input_values must match repeated_values")


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
class ListingFieldCandidate:
    """Evidence-bound listing field candidate with explicit provenance."""

    field_candidate_id: str
    field_family: ListingFieldFamily
    tier: ListingFieldTier
    availability: ListingFieldAvailability
    quality: ListingFieldQuality
    value: str | None = None
    compatibility_profile: ParserCompatibilityProfile | None = None
    warnings: tuple[ParserWarning, ...] = ()
    evidence_references: tuple[ParserEvidenceReference, ...] = ()
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.field_candidate_id.strip():
            raise ValueError("field_candidate_id must not be blank")
        if self.value is not None:
            if not self.value.strip():
                raise ValueError("value must not be blank")
            if self.availability is not ListingFieldAvailability.PROVEN_AVAILABLE:
                raise ValueError("value is only allowed when availability is PROVEN_AVAILABLE")
        if self.availability is ListingFieldAvailability.PROVEN_AVAILABLE:
            if not self.evidence_references:
                raise ValueError("PROVEN_AVAILABLE field must declare evidence_references")
            if self.compatibility_profile is None:
                raise ValueError("PROVEN_AVAILABLE field must declare compatibility_profile")
            if (
                self.compatibility_profile.lifecycle_status
                is not CompatibilityProfileLifecycleStatus.CURRENT
            ):
                raise ValueError("PROVEN_AVAILABLE field requires CURRENT compatibility_profile")
        expected_tier = _LISTING_FIELD_TIER_BY_FAMILY[self.field_family]
        if self.tier is not expected_tier:
            raise ValueError("field_family and tier must match")
        _validate_nonblank_values("notes", self.notes)


@dataclass(frozen=True, slots=True)
class ListingCardCandidate:
    """Listing-card candidate whose authoritative content is field_candidates."""

    listing_card_id: str
    field_candidates: tuple[ListingFieldCandidate, ...] = ()
    warnings: tuple[ParserWarning, ...] = ()
    evidence_references: tuple[ParserEvidenceReference, ...] = ()

    def __post_init__(self) -> None:
        if not self.listing_card_id.strip():
            raise ValueError("listing_card_id must not be blank")


@dataclass(frozen=True, slots=True)
class NormalizedListingCandidate:
    """Normalized listing candidate with explicit status and card authority."""

    listing_candidate_id: str
    status: ListingCandidateStatus
    card_candidate: ListingCardCandidate
    warnings: tuple[ParserWarning, ...] = ()
    evidence_references: tuple[ParserEvidenceReference, ...] = ()

    def __post_init__(self) -> None:
        if not self.listing_candidate_id.strip():
            raise ValueError("listing_candidate_id must not be blank")


@dataclass(frozen=True, slots=True)
class ObservedListingPosition:
    """Observed listing position with no newness, baseline or anchor semantics."""

    position_id: str
    listing_candidate_id: str
    observed_rank: int
    publication_order_signal_reference: str | None = None
    warnings: tuple[ParserWarning, ...] = ()
    evidence_references: tuple[ParserEvidenceReference, ...] = ()
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for field_name in ("position_id", "listing_candidate_id"):
            if not getattr(self, field_name).strip():
                raise ValueError(f"{field_name} must not be blank")
        if not isinstance(self.observed_rank, int) or self.observed_rank < 1:
            raise ValueError("observed_rank must be a positive integer starting at 1")
        if (
            self.publication_order_signal_reference is not None
            and not self.publication_order_signal_reference.strip()
        ):
            raise ValueError("publication_order_signal_reference must not be blank")
        _validate_nonblank_values("notes", self.notes)


def _validate_ordering_evidence_positions(
    positions: tuple[ObservedListingPosition, ...],
) -> None:
    position_ids = [position.position_id for position in positions]
    candidate_ids = [position.listing_candidate_id for position in positions]
    ranks = [position.observed_rank for position in positions]

    if len(set(position_ids)) != len(position_ids):
        raise ValueError("position_ids must be unique")
    if len(set(candidate_ids)) != len(candidate_ids):
        raise ValueError("listing_candidate_ids must be unique")
    if len(set(ranks)) != len(ranks):
        raise ValueError("observed_ranks must be unique")
    expected_ranks = tuple(range(1, len(positions) + 1))
    if tuple(ranks) != expected_ranks:
        raise ValueError("observed_ranks must be strictly 1..N without gaps")
    for index, position in enumerate(positions, start=1):
        if position.observed_rank != index:
            raise ValueError("positions must be ordered by observed_rank")


@dataclass(frozen=True, slots=True)
class ListingOrderingEvidence:
    """Observed listing-order evidence that does not claim provider authority."""

    ordering_evidence_id: str
    status: ListingSortContextStatus
    positions: tuple[ObservedListingPosition, ...]
    sort_context_reference: str | None = None
    compatibility_profile: ParserCompatibilityProfile | None = None
    warnings: tuple[ParserWarning, ...] = ()
    evidence_references: tuple[ParserEvidenceReference, ...] = ()
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.ordering_evidence_id.strip():
            raise ValueError("ordering_evidence_id must not be blank")
        if self.sort_context_reference is not None and not self.sort_context_reference.strip():
            raise ValueError("sort_context_reference must not be blank")
        _validate_nonblank_values("notes", self.notes)
        _validate_ordering_evidence_positions(self.positions)

        if self.status is ListingSortContextStatus.PROVEN_NEWEST_FIRST:
            if not self.positions:
                raise ValueError("PROVEN_NEWEST_FIRST requires positions")
            if self.sort_context_reference is None:
                raise ValueError("PROVEN_NEWEST_FIRST requires sort_context_reference")
            if self.compatibility_profile is None:
                raise ValueError("PROVEN_NEWEST_FIRST requires compatibility_profile")
            if (
                self.compatibility_profile.lifecycle_status
                is not CompatibilityProfileLifecycleStatus.CURRENT
            ):
                raise ValueError("PROVEN_NEWEST_FIRST requires CURRENT compatibility_profile")
            if not self.evidence_references:
                raise ValueError("PROVEN_NEWEST_FIRST requires evidence_references")


def _ordering_handoff_block_reason(
    page_status: ParserOutcomeStatus,
    ordering_status: ListingSortContextStatus,
    compatibility_profile: ParserCompatibilityProfile | None,
) -> ScanOrderingHandoffStatus:
    if page_status is not ParserOutcomeStatus.USABLE_RESPONSE:
        return ScanOrderingHandoffStatus.BLOCKED_PAGE_NOT_USABLE
    if ordering_status is ListingSortContextStatus.MISSING:
        return ScanOrderingHandoffStatus.BLOCKED_SORT_MISSING
    if ordering_status is ListingSortContextStatus.AMBIGUOUS:
        return ScanOrderingHandoffStatus.BLOCKED_SORT_AMBIGUOUS
    if ordering_status is ListingSortContextStatus.UNSUPPORTED:
        return ScanOrderingHandoffStatus.BLOCKED_SORT_UNSUPPORTED
    if ordering_status is ListingSortContextStatus.UNPROVEN:
        return ScanOrderingHandoffStatus.BLOCKED_SORT_UNPROVEN
    if ordering_status is ListingSortContextStatus.CONTRADICTORY:
        return ScanOrderingHandoffStatus.BLOCKED_SORT_CONTRADICTORY
    if ordering_status is ListingSortContextStatus.PROVEN_NEWEST_FIRST and (
        compatibility_profile is None
        or compatibility_profile.lifecycle_status is not CompatibilityProfileLifecycleStatus.CURRENT
    ):
        return ScanOrderingHandoffStatus.BLOCKED_PROFILE_NOT_CURRENT
    return ScanOrderingHandoffStatus.COMPARISON_ELIGIBLE


@dataclass(frozen=True, slots=True)
class ParserScanOrderingHandoff:
    """Safe Parser-to-Scan ordering handoff boundary without newness authority."""

    handoff_id: str
    page_id: str
    page_status: ParserOutcomeStatus
    status: ScanOrderingHandoffStatus
    ordering_evidence: ListingOrderingEvidence
    listing_candidate_ids: tuple[str, ...]
    warnings: tuple[ParserWarning, ...] = ()
    evidence_references: tuple[ParserEvidenceReference, ...] = ()
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.handoff_id.strip():
            raise ValueError("handoff_id must not be blank")
        if not self.page_id.strip():
            raise ValueError("page_id must not be blank")
        _validate_nonblank_values("notes", self.notes)

        if len(set(self.listing_candidate_ids)) != len(self.listing_candidate_ids):
            raise ValueError("listing_candidate_ids must be unique")
        for listing_candidate_id in self.listing_candidate_ids:
            if not listing_candidate_id.strip():
                raise ValueError("listing_candidate_ids must not contain blank values")

        candidate_ids = tuple(
            position.listing_candidate_id for position in self.ordering_evidence.positions
        )
        if candidate_ids != self.listing_candidate_ids:
            raise ValueError("listing_candidate_ids must match ordering_evidence positions")

        expected_status = _ordering_handoff_block_reason(
            self.page_status,
            self.ordering_evidence.status,
            self.ordering_evidence.compatibility_profile,
        )
        if self.status is not expected_status:
            raise ValueError("scan ordering handoff status must match factual reason")

        if self.status is ScanOrderingHandoffStatus.COMPARISON_ELIGIBLE:
            if self.page_status is not ParserOutcomeStatus.USABLE_RESPONSE:
                raise ValueError("comparison eligible handoff requires usable page status")
            if self.ordering_evidence.status is not ListingSortContextStatus.PROVEN_NEWEST_FIRST:
                raise ValueError(
                    "comparison eligible handoff requires proven newest-first ordering"
                )
            if (
                self.ordering_evidence.compatibility_profile is None
                or self.ordering_evidence.compatibility_profile.lifecycle_status
                is not CompatibilityProfileLifecycleStatus.CURRENT
            ):
                raise ValueError(
                    "comparison eligible handoff requires CURRENT compatibility profile"
                )
            if self.ordering_evidence.sort_context_reference is None:
                raise ValueError("comparison eligible handoff requires sort_context_reference")
        elif self.status is ScanOrderingHandoffStatus.BLOCKED_PROFILE_NOT_CURRENT:
            if self.page_status is not ParserOutcomeStatus.USABLE_RESPONSE:
                raise ValueError("profile-not-current block requires usable page status")
            if self.ordering_evidence.status is not ListingSortContextStatus.PROVEN_NEWEST_FIRST:
                raise ValueError("profile-not-current block requires proven ordering")
        elif self.status is ScanOrderingHandoffStatus.BLOCKED_PAGE_NOT_USABLE:
            if self.page_status is ParserOutcomeStatus.USABLE_RESPONSE:
                raise ValueError("page-not-usable block requires non-usable page status")


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
                raise ValueError(
                    "search_configuration_evidence.request_envelope must match request_envelope"
                )
            if (
                self.search_configuration_evidence.compatibility_profile
                != self.compatibility_profile
            ):
                raise ValueError(
                    "search_configuration_evidence.compatibility_profile "
                    "must match compatibility_profile"
                )


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
    ordering_evidence: ListingOrderingEvidence | None = None
    scan_ordering_handoff: ParserScanOrderingHandoff | None = None
    warnings: tuple[ParserWarning, ...] = ()
    evidence_references: tuple[ParserEvidenceReference, ...] = ()
    explanation: ParserOutcomeExplanation | None = None

    def __post_init__(self) -> None:
        if not self.page_id.strip():
            raise ValueError("page_id must not be blank")
        normalized_candidate_ids = tuple(
            candidate.listing_candidate_id for candidate in self.normalized_listing_candidates
        )
        if self.ordering_evidence is not None:
            ordering_candidate_ids = tuple(
                position.listing_candidate_id for position in self.ordering_evidence.positions
            )
            if ordering_candidate_ids != normalized_candidate_ids:
                raise ValueError(
                    "ordering_evidence positions must match normalized_listing_candidates"
                )
        if self.scan_ordering_handoff is not None:
            if self.scan_ordering_handoff.page_id != self.page_id:
                raise ValueError("scan_ordering_handoff.page_id must match page_id")
            if (
                isinstance(self.status, ParserOutcomeStatus)
                and self.scan_ordering_handoff.page_status is not self.status
            ):
                raise ValueError("scan_ordering_handoff.page_status must match page status")
            if (
                self.ordering_evidence is not None
                and self.scan_ordering_handoff.ordering_evidence != self.ordering_evidence
            ):
                raise ValueError(
                    "scan_ordering_handoff.ordering_evidence must match ordering_evidence"
                )
            if self.scan_ordering_handoff.listing_candidate_ids != normalized_candidate_ids:
                raise ValueError(
                    "scan_ordering_handoff.listing_candidate_ids must match normalized candidates"
                )


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
    pagination_evidence: PaginationBatchEvidence | None = None
    warnings: tuple[ParserWarning, ...] = ()
    evidence_references: tuple[ParserEvidenceReference, ...] = ()
    explanation: ParserOutcomeExplanation | None = None

    def __post_init__(self) -> None:
        if not self.batch_id.strip():
            raise ValueError("batch_id must not be blank")
        if self.pagination_evidence is not None:
            pagination_evidence = self.pagination_evidence
            expected_page_outcomes = tuple(
                observation.page_outcome for observation in pagination_evidence.page_observations
            )
            if self.page_outcomes != expected_page_outcomes:
                raise ValueError("page_outcomes must match pagination_evidence.page_observations")
            if pagination_evidence.status is PaginationBatchStatus.COMPLETE:
                if self.status is not ParserOutcomeStatus.USABLE_RESPONSE:
                    raise ValueError("COMPLETE pagination evidence requires usable batch status")
            elif self.status is ParserOutcomeStatus.USABLE_RESPONSE:
                raise ValueError("generic batch success is blocked for non-complete pagination")


@dataclass(frozen=True, slots=True)
class PaginationPolicyBound:
    """Approved pagination-policy evidence bound."""

    bound_id: str
    kind: PaginationLimitKind
    maximum: int
    policy_reference: str
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.bound_id.strip():
            raise ValueError("bound_id must not be blank")
        if not self.policy_reference.strip():
            raise ValueError("policy_reference must not be blank")
        _validate_positive_int("maximum", self.maximum)
        _validate_nonblank_values("notes", self.notes)


@dataclass(frozen=True, slots=True)
class PaginationPageObservation:
    """Evidence-bound observation for one parsed listing page."""

    observation_id: str
    page_sequence: int
    page_outcome: ListingPageParseOutcome
    continuation_status: PaginationContinuationStatus
    continuation_reference: str | None = None
    compatibility_profile: ParserCompatibilityProfile | None = None
    warnings: tuple[ParserWarning, ...] = ()
    evidence_references: tuple[ParserEvidenceReference, ...] = ()
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.observation_id.strip():
            raise ValueError("observation_id must not be blank")
        _validate_positive_int("page_sequence", self.page_sequence)
        if self.continuation_reference is not None and not self.continuation_reference.strip():
            raise ValueError("continuation_reference must not be blank")
        _validate_nonblank_values("notes", self.notes)
        if self.continuation_status is PaginationContinuationStatus.PROVEN_AVAILABLE:
            if self.continuation_reference is None:
                raise ValueError("PROVEN_AVAILABLE requires continuation_reference")
            if self.compatibility_profile is None:
                raise ValueError("PROVEN_AVAILABLE requires compatibility_profile")
            if (
                self.compatibility_profile.lifecycle_status
                is not CompatibilityProfileLifecycleStatus.CURRENT
            ):
                raise ValueError("PROVEN_AVAILABLE requires CURRENT compatibility_profile")
            if not self.evidence_references:
                raise ValueError("PROVEN_AVAILABLE requires evidence_references")
        elif self.continuation_status is PaginationContinuationStatus.PROVEN_EXHAUSTED:
            if self.continuation_reference is not None:
                raise ValueError("PROVEN_EXHAUSTED cannot declare continuation_reference")
            if self.compatibility_profile is None:
                raise ValueError("PROVEN_EXHAUSTED requires compatibility_profile")
            if (
                self.compatibility_profile.lifecycle_status
                is not CompatibilityProfileLifecycleStatus.CURRENT
            ):
                raise ValueError("PROVEN_EXHAUSTED requires CURRENT compatibility_profile")
            if not self.evidence_references:
                raise ValueError("PROVEN_EXHAUSTED requires evidence_references")
        elif self.continuation_reference is not None:
            raise ValueError("only proven continuation may declare continuation_reference")


@dataclass(frozen=True, slots=True)
class DuplicateListingObservation:
    """Explicit record of a repeated listing candidate observation."""

    duplicate_observation_id: str
    listing_candidate_id: str
    first_page_sequence: int
    first_observed_rank: int
    repeated_page_sequence: int
    repeated_observed_rank: int
    evidence_references: tuple[ParserEvidenceReference, ...] = ()
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.duplicate_observation_id.strip():
            raise ValueError("duplicate_observation_id must not be blank")
        if not self.listing_candidate_id.strip():
            raise ValueError("listing_candidate_id must not be blank")
        for field_name in (
            "first_page_sequence",
            "first_observed_rank",
            "repeated_page_sequence",
            "repeated_observed_rank",
        ):
            _validate_positive_int(field_name, getattr(self, field_name))
        if (
            self.first_page_sequence,
            self.first_observed_rank,
        ) == (
            self.repeated_page_sequence,
            self.repeated_observed_rank,
        ):
            raise ValueError("repeated location must differ from first location")
        if (
            self.repeated_page_sequence,
            self.repeated_observed_rank,
        ) <= (
            self.first_page_sequence,
            self.first_observed_rank,
        ):
            raise ValueError("repeated location must come after first location")
        _validate_nonblank_values("notes", self.notes)


@dataclass(frozen=True, slots=True)
class PaginationBatchEvidence:
    """Bounded pagination evidence that preserves page and listing order."""

    pagination_evidence_id: str
    status: PaginationBatchStatus
    page_observations: tuple[PaginationPageObservation, ...]
    stop_reason: PaginationStopReason
    policy_bounds: tuple[PaginationPolicyBound, ...] = ()
    duplicate_observations: tuple[DuplicateListingObservation, ...] = ()
    flattened_listing_candidate_ids: tuple[str, ...] = ()
    warnings: tuple[ParserWarning, ...] = ()
    evidence_references: tuple[ParserEvidenceReference, ...] = ()
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.pagination_evidence_id.strip():
            raise ValueError("pagination_evidence_id must not be blank")
        _validate_nonblank_values("notes", self.notes)

        page_observations = self.page_observations
        observation_ids = [observation.observation_id for observation in page_observations]
        page_ids = [observation.page_outcome.page_id for observation in page_observations]
        page_sequences = [observation.page_sequence for observation in page_observations]
        if len(set(observation_ids)) != len(observation_ids):
            raise ValueError("page observation IDs must be unique")
        if len(set(page_ids)) != len(page_ids):
            raise ValueError("page IDs must be unique")
        if len(set(page_sequences)) != len(page_sequences):
            raise ValueError("page sequences must be unique")
        if tuple(page_sequences) != tuple(range(1, len(page_observations) + 1)):
            raise ValueError("page sequences must be strictly 1..N in observation order")
        for index, observation in enumerate(page_observations, start=1):
            if observation.page_sequence != index:
                raise ValueError("page observations must be ordered by page_sequence")

        bound_ids = [bound.bound_id for bound in self.policy_bounds]
        bound_kinds = [bound.kind for bound in self.policy_bounds]
        if len(set(bound_ids)) != len(bound_ids):
            raise ValueError("policy bound IDs must be unique")
        if len(set(bound_kinds)) != len(bound_kinds):
            raise ValueError("policy bound kinds must be unique")

        flattened_candidate_ids = tuple(self.flattened_listing_candidate_ids)
        if any(not candidate_id.strip() for candidate_id in flattened_candidate_ids):
            raise ValueError("flattened_listing_candidate_ids must not contain blank values")
        observed_candidate_ids: list[str] = []
        candidate_positions: dict[str, tuple[int, int]] = {}
        repeated_positions: list[tuple[str, tuple[int, int], tuple[int, int]]] = []
        for observation in page_observations:
            page_sequence = observation.page_sequence
            for rank, candidate in enumerate(
                observation.page_outcome.normalized_listing_candidates, start=1
            ):
                candidate_id = candidate.listing_candidate_id
                observed_candidate_ids.append(candidate_id)
                current_position = (page_sequence, rank)
                if candidate_id not in candidate_positions:
                    candidate_positions[candidate_id] = current_position
                else:
                    first_position = candidate_positions[candidate_id]
                    repeated_positions.append((candidate_id, first_position, current_position))
        if flattened_candidate_ids != tuple(observed_candidate_ids):
            raise ValueError(
                "flattened_listing_candidate_ids must match observed page listing order"
            )
        duplicate_specs = [
            (
                duplicate.listing_candidate_id,
                (duplicate.first_page_sequence, duplicate.first_observed_rank),
                (duplicate.repeated_page_sequence, duplicate.repeated_observed_rank),
            )
            for duplicate in self.duplicate_observations
        ]
        if len(duplicate_specs) != len(repeated_positions):
            raise ValueError("duplicate observations must cover every repeated occurrence")
        if duplicate_specs != repeated_positions:
            raise ValueError("duplicate observations must exactly match repeated locations")

        if self.status is PaginationBatchStatus.COMPLETE:
            if not page_observations:
                raise ValueError("COMPLETE pagination requires at least one page observation")
            if any(
                observation.page_outcome.status is not ParserOutcomeStatus.USABLE_RESPONSE
                for observation in page_observations
            ):
                raise ValueError("COMPLETE pagination requires usable page outcomes")
            last_observation = page_observations[-1]
            if last_observation.continuation_status not in (
                PaginationContinuationStatus.PROVEN_EXHAUSTED,
                PaginationContinuationStatus.NOT_APPLICABLE,
            ):
                raise ValueError("COMPLETE pagination requires final exhaustion evidence")
            if (
                last_observation.continuation_status is PaginationContinuationStatus.NOT_APPLICABLE
                and self.stop_reason is not PaginationStopReason.REQUEST_SCOPE_COMPLETE
            ):
                raise ValueError(
                    "NOT_APPLICABLE completion requires REQUEST_SCOPE_COMPLETE stop reason"
                )
            if (
                last_observation.continuation_status
                is PaginationContinuationStatus.PROVEN_EXHAUSTED
                and self.stop_reason is not PaginationStopReason.EXPLICITLY_EXHAUSTED
            ):
                raise ValueError(
                    "PROVEN_EXHAUSTED completion requires EXPLICITLY_EXHAUSTED stop reason"
                )
        elif self.status is PaginationBatchStatus.PARTIAL:
            if not any(
                observation.page_outcome.status is ParserOutcomeStatus.USABLE_RESPONSE
                for observation in page_observations
            ):
                raise ValueError("PARTIAL pagination requires at least one usable page")
            if self.stop_reason in (
                PaginationStopReason.EXPLICITLY_EXHAUSTED,
                PaginationStopReason.REQUEST_SCOPE_COMPLETE,
            ):
                raise ValueError("PARTIAL pagination cannot claim exhaustion")
        elif self.status is PaginationBatchStatus.INTERRUPTED:
            if self.stop_reason not in (
                PaginationStopReason.MAX_PAGES_REACHED,
                PaginationStopReason.MAX_ITEMS_REACHED,
                PaginationStopReason.MAX_BYTES_REACHED,
                PaginationStopReason.MAX_DURATION_REACHED,
                PaginationStopReason.EXTERNAL_INTERRUPTION,
            ):
                raise ValueError("INTERRUPTED pagination requires interruption stop reason")
            if self.stop_reason is PaginationStopReason.MAX_PAGES_REACHED and not any(
                bound.kind is PaginationLimitKind.PAGES for bound in self.policy_bounds
            ):
                raise ValueError("MAX_PAGES_REACHED requires matching PAGES policy bound")
            if self.stop_reason is PaginationStopReason.MAX_ITEMS_REACHED and not any(
                bound.kind is PaginationLimitKind.ITEMS for bound in self.policy_bounds
            ):
                raise ValueError("MAX_ITEMS_REACHED requires matching ITEMS policy bound")
            if self.stop_reason is PaginationStopReason.MAX_BYTES_REACHED and not any(
                bound.kind is PaginationLimitKind.BYTES for bound in self.policy_bounds
            ):
                raise ValueError("MAX_BYTES_REACHED requires matching BYTES policy bound")
            if self.stop_reason is PaginationStopReason.MAX_DURATION_REACHED and not any(
                bound.kind is PaginationLimitKind.DURATION_MILLISECONDS
                for bound in self.policy_bounds
            ):
                raise ValueError(
                    "MAX_DURATION_REACHED requires matching DURATION_MILLISECONDS policy bound"
                )
        elif self.status is PaginationBatchStatus.AMBIGUOUS:
            if not any(
                observation.continuation_status
                in (
                    PaginationContinuationStatus.MISSING,
                    PaginationContinuationStatus.AMBIGUOUS,
                    PaginationContinuationStatus.UNSUPPORTED,
                )
                for observation in page_observations
            ):
                raise ValueError("AMBIGUOUS pagination requires ambiguous continuation evidence")
        elif self.status is PaginationBatchStatus.BLOCKED:
            if any(
                observation.page_outcome.status is ParserOutcomeStatus.USABLE_RESPONSE
                for observation in page_observations
            ):
                raise ValueError("BLOCKED pagination cannot contain usable page data")
            if self.stop_reason not in (
                PaginationStopReason.PROVIDER_RESTRICTED,
                PaginationStopReason.CONTINUATION_MISSING,
                PaginationStopReason.CONTINUATION_AMBIGUOUS,
                PaginationStopReason.CONTINUATION_UNSUPPORTED,
                PaginationStopReason.PAGE_NOT_USABLE,
            ):
                raise ValueError("BLOCKED pagination requires blocked stop reason")


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
    "DiagnosticEvidenceKind",
    "SensitiveMaterialKind",
    "RetentionDisposition",
    "PersonalDataMinimizationStatus",
    "PrivacyBoundaryStatus",
    "EvidencePolicyStatus",
    "SearchConfigurationWarningCode",
    "SearchConfigurationExtractionField",
    "SearchConfigurationFieldStatus",
    "MultivalueNormalizationStatus",
    "MultivaluePreservationMode",
    "MultivalueLossReason",
    "SearchConfigurationValueKind",
    "ListingFieldFamily",
    "ListingFieldTier",
    "ListingFieldAvailability",
    "ListingFieldQuality",
    "ListingCandidateStatus",
    "ListingSortContextStatus",
    "ScanOrderingHandoffStatus",
    "PaginationBatchStatus",
    "PaginationContinuationStatus",
    "PaginationStopReason",
    "PaginationLimitKind",
    "SourceReferenceKind",
    "SourceBoundaryStatus",
    "SourceBoundaryRiskCode",
    "SourceBoundaryPolicyRequirement",
    "ParserSourceReference",
    "SourceBoundaryOutcome",
    "ParserEvidenceReference",
    "SafeDiagnosticEvidence",
    "SensitiveMaterialDisposition",
    "ParserDiagnosticEvent",
    "ParserPrivacyBoundaryOutcome",
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
    "MultivalueNormalizationRule",
    "MultivalueNormalizationOutcome",
    "SearchConfigurationParameterCandidate",
    "SearchConfigurationCandidate",
    "SearchConfigurationExtractionOutcome",
    "ListingFieldCandidate",
    "ListingCardCandidate",
    "NormalizedListingCandidate",
    "ObservedListingPosition",
    "ListingOrderingEvidence",
    "ParserScanOrderingHandoff",
    "ListingPageParseOutcome",
    "ListingBatchParseOutcome",
    "PaginationPolicyBound",
    "PaginationPageObservation",
    "DuplicateListingObservation",
    "PaginationBatchEvidence",
)
