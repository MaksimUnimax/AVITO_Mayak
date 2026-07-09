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


class ReferenceOutcomeStatus(str, Enum):
    """Reference-profile classifications that gate semantic acceptance."""

    REFERENCE_STALE = "REFERENCE_STALE"
    REFERENCE_MISSING = "REFERENCE_MISSING"
    REFERENCE_DISPUTED = "REFERENCE_DISPUTED"
    CURRENT = "CURRENT"


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


@dataclass(frozen=True, slots=True)
class ParserEvidenceReference:
    """Safe evidence reference with no raw provider payload retention."""

    reference_id: str
    evidence_kind: str
    reference_status: ReferenceOutcomeStatus = ReferenceOutcomeStatus.CURRENT
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
class ParserWarning:
    """Explicit warning that stays attached to an outcome or candidate."""

    code: ParserWarningCode
    message: str
    evidence_reference: ParserEvidenceReference | None = None
    details: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.message.strip():
            raise ValueError("warning message must not be blank")


@dataclass(frozen=True, slots=True)
class ParserCompatibilityProfile:
    """Versioned reference profile that gates semantic parsing behavior."""

    profile_id: str
    profile_version: str
    reference_status: ReferenceOutcomeStatus
    source_reference: str | None = None
    evidence_reference: ParserEvidenceReference | None = None
    supported_shape_signatures: tuple[str, ...] = ()
    unsupported_shape_signatures: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.profile_id.strip():
            raise ValueError("profile_id must not be blank")
        if not self.profile_version.strip():
            raise ValueError("profile_version must not be blank")


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
class ParserOutcomeExplanation:
    """Read-only explanation that links outcome reason codes to safe evidence."""

    summary: str
    reason_code: str | None = None
    status: ParserOutcomeStatus | TransportOutcomeStatus | ReferenceOutcomeStatus | None = None
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
    reference_status: ReferenceOutcomeStatus | None = None
    request_envelope: ParserRequestEnvelope | None = None
    transport_outcome: TransportOutcomeReference | None = None
    response_reference: str | None = None
    warnings: tuple[ParserWarning, ...] = ()
    evidence_references: tuple[ParserEvidenceReference, ...] = ()
    explanation: ParserOutcomeExplanation | None = None

    def __post_init__(self) -> None:
        if not self.attempt_id.strip():
            raise ValueError("attempt_id must not be blank")


@dataclass(frozen=True, slots=True)
class SearchSourceAnalysisOutcome:
    """Semantic analysis of a source reference before deeper extraction."""

    analysis_id: str
    request_envelope: ParserRequestEnvelope
    transport_outcome: TransportOutcomeReference | None
    status: ParserOutcomeStatus | TransportOutcomeStatus | ReferenceOutcomeStatus
    compatibility_profile: ParserCompatibilityProfile
    warnings: tuple[ParserWarning, ...] = ()
    evidence_references: tuple[ParserEvidenceReference, ...] = ()
    explanation: ParserOutcomeExplanation | None = None

    def __post_init__(self) -> None:
        if not self.analysis_id.strip():
            raise ValueError("analysis_id must not be blank")


@dataclass(frozen=True, slots=True)
class SearchConfigurationExtractionOutcome:
    """Normalized search-configuration evidence for Scan handoff."""

    extraction_id: str
    request_envelope: ParserRequestEnvelope
    transport_outcome: TransportOutcomeReference | None
    status: ParserOutcomeStatus | TransportOutcomeStatus | ReferenceOutcomeStatus
    compatibility_profile: ParserCompatibilityProfile
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
    status: ParserOutcomeStatus | TransportOutcomeStatus | ReferenceOutcomeStatus
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
    status: ParserOutcomeStatus | TransportOutcomeStatus | ReferenceOutcomeStatus
    compatibility_profile: ParserCompatibilityProfile
    page_outcomes: tuple[ListingPageParseOutcome, ...] = ()
    warnings: tuple[ParserWarning, ...] = ()
    evidence_references: tuple[ParserEvidenceReference, ...] = ()
    explanation: ParserOutcomeExplanation | None = None

    def __post_init__(self) -> None:
        if not self.batch_id.strip():
            raise ValueError("batch_id must not be blank")


__all__: Final[tuple[str, ...]] = (
    "TransportOutcomeStatus",
    "ParserOutcomeStatus",
    "ReferenceOutcomeStatus",
    "ParserWarningCode",
    "ParserEvidenceReference",
    "ParserWarning",
    "ParserCompatibilityProfile",
    "ParserRequestEnvelope",
    "TransportOutcomeReference",
    "ParserOutcomeExplanation",
    "ParserAttemptOutcome",
    "SearchSourceAnalysisOutcome",
    "SearchConfigurationExtractionOutcome",
    "ListingCardCandidate",
    "NormalizedListingCandidate",
    "ListingPageParseOutcome",
    "ListingBatchParseOutcome",
)
