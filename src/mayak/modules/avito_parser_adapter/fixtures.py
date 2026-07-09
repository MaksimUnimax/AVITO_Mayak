"""Safe synthetic fixture identifiers for Avito Parser Adapter semantics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from .contracts import (
    ListingBatchParseOutcome,
    ListingCardCandidate,
    ListingPageParseOutcome,
    NormalizedListingCandidate,
    ParserAttemptOutcome,
    ParserCompatibilityProfile,
    ParserEvidenceReference,
    ParserOutcomeExplanation,
    ParserOutcomeStatus,
    ParserRequestEnvelope,
    ParserWarning,
    ParserWarningCode,
    ReferenceOutcomeStatus,
    SearchConfigurationExtractionOutcome,
    SearchSourceAnalysisOutcome,
    TransportOutcomeReference,
    TransportOutcomeStatus,
)


@dataclass(frozen=True, slots=True)
class SyntheticFixtureCase:
    """Synthetic semantic case with no real provider payloads."""

    fixture_id: str
    summary: str
    request_envelope: ParserRequestEnvelope
    transport_outcome: TransportOutcomeReference
    attempt_outcome: ParserAttemptOutcome
    search_source_analysis_outcome: SearchSourceAnalysisOutcome | None = None
    search_configuration_extraction_outcome: SearchConfigurationExtractionOutcome | None = None
    listing_page_parse_outcome: ListingPageParseOutcome | None = None
    listing_batch_parse_outcome: ListingBatchParseOutcome | None = None

    def __post_init__(self) -> None:
        if not self.fixture_id.strip():
            raise ValueError("fixture_id must not be blank")
        if not self.summary.strip():
            raise ValueError("summary must not be blank")


def _profile(
    profile_id: str,
    *,
    reference_status: ReferenceOutcomeStatus = ReferenceOutcomeStatus.CURRENT,
    evidence_suffix: str,
) -> ParserCompatibilityProfile:
    return ParserCompatibilityProfile(
        profile_id=profile_id,
        profile_version="2026.07.09",
        reference_status=reference_status,
        source_reference=f"safe-source::{evidence_suffix}",
        evidence_reference=ParserEvidenceReference(
            reference_id=f"fx::{evidence_suffix}::profile",
            evidence_kind="compatibility-profile",
            reference_status=reference_status,
            fingerprint=f"fingerprint::{evidence_suffix}",
            version="2026.07.09",
            notes=(f"synthetic compatibility profile {profile_id}",),
        ),
        supported_shape_signatures=(f"shape::{evidence_suffix}::tier1",),
        unsupported_shape_signatures=(),
        notes=(f"synthetic profile {profile_id}",),
    )


def _request(
    request_id: str,
    profile: ParserCompatibilityProfile,
    *,
    purpose: str,
    safe_source_reference: str,
    requested_page_numbers: tuple[int, ...] = (),
    requested_unit_ids: tuple[str, ...] = (),
) -> ParserRequestEnvelope:
    return ParserRequestEnvelope(
        request_id=request_id,
        contract_name="mayak.avito.parser.request",
        contract_version="1.0",
        producer="mayak.tests.synthetic",
        purpose=purpose,
        compatibility_profile=profile,
        safe_source_reference=safe_source_reference,
        configuration_revision_id="cfg::synthetic::001",
        safe_transport_reference=f"transport::{request_id}",
        message_id=f"msg::{request_id}",
        correlation_id=f"corr::{request_id}",
        causation_id=f"cause::{request_id}",
        idempotency_key=f"idempotency::{request_id}",
        requested_page_numbers=requested_page_numbers,
        requested_unit_ids=requested_unit_ids,
    )


def _transport(
    transport_reference_id: str,
    *,
    status: TransportOutcomeStatus,
    request_reference: str,
    response_reference: str | None = None,
    route_reference: str | None = None,
    evidence_reference_suffix: str,
) -> TransportOutcomeReference:
    return TransportOutcomeReference(
        transport_reference_id=transport_reference_id,
        transport_status=status,
        request_reference=request_reference,
        response_reference=response_reference,
        route_reference=route_reference,
        notes=(f"synthetic transport outcome {transport_reference_id}",),
        evidence_references=(
            ParserEvidenceReference(
                reference_id=f"fx::{evidence_reference_suffix}::transport",
                evidence_kind="transport-outcome",
                notes=(f"transport status {status.value}",),
            ),
        ),
    )


def _usable_listing_card(
    card_id: str,
    *,
    evidence_suffix: str,
    phone: str | None = None,
    seller: str | None = None,
    seller_rating: str | None = None,
    description: str | None = None,
) -> ListingCardCandidate:
    return ListingCardCandidate(
        listing_card_id=card_id,
        title="Synthetic Tier 1 title",
        price_text="123 456 ₽",
        listing_url_reference=f"listing::{evidence_suffix}::url",
        preview_image_reference=f"image::{evidence_suffix}::preview",
        phone=phone,
        seller=seller,
        seller_rating=seller_rating,
        description=description,
        warnings=(),
        evidence_references=(
            ParserEvidenceReference(
                reference_id=f"fx::{evidence_suffix}::card",
                evidence_kind="listing-card",
                notes=("synthetic tier 1 listing card",),
            ),
        ),
    )


def _listing_candidate(
    candidate_id: str,
    card: ListingCardCandidate,
    *,
    evidence_suffix: str,
    geography: str = "synthetic-city",
    category: str = "synthetic-category",
    publication_order_reference: str | None = "publication-order::synthetic",
    sort_context_reference: str | None = "sort-context::synthetic",
    warnings: tuple[ParserWarning, ...] = (),
) -> NormalizedListingCandidate:
    return NormalizedListingCandidate(
        listing_candidate_id=candidate_id,
        card_candidate=card,
        geography=geography,
        category=category,
        publication_order_reference=publication_order_reference,
        sort_context_reference=sort_context_reference,
        warnings=warnings,
        evidence_references=(
            ParserEvidenceReference(
                reference_id=f"fx::{evidence_suffix}::listing",
                evidence_kind="normalized-listing",
            ),
        ),
    )


def _usable_attempt(
    attempt_id: str,
    profile: ParserCompatibilityProfile,
    request: ParserRequestEnvelope,
    transport: TransportOutcomeReference,
    *,
    parser_status: ParserOutcomeStatus = ParserOutcomeStatus.USABLE_RESPONSE,
    reference_status: ReferenceOutcomeStatus | None = None,
    warnings: tuple[ParserWarning, ...] = (),
    evidence_suffix: str,
) -> ParserAttemptOutcome:
    return ParserAttemptOutcome(
        attempt_id=attempt_id,
        transport_status=transport.transport_status,
        parser_status=parser_status,
        reference_status=reference_status,
        request_envelope=request,
        transport_outcome=transport,
        response_reference=f"response::{evidence_suffix}",
        warnings=warnings,
        evidence_references=transport.evidence_references,
        explanation=ParserOutcomeExplanation(
            summary="synthetic parser attempt",
            reason_code=f"FX::{evidence_suffix}",
            status=parser_status,
            evidence_references=transport.evidence_references,
            warnings=warnings,
        ),
    )


def _search_source_analysis(
    analysis_id: str,
    request: ParserRequestEnvelope,
    transport: TransportOutcomeReference,
    profile: ParserCompatibilityProfile,
    *,
    status: ParserOutcomeStatus | TransportOutcomeStatus | ReferenceOutcomeStatus,
    evidence_suffix: str,
    warnings: tuple[ParserWarning, ...] = (),
) -> SearchSourceAnalysisOutcome:
    return SearchSourceAnalysisOutcome(
        analysis_id=analysis_id,
        request_envelope=request,
        transport_outcome=transport,
        status=status,
        compatibility_profile=profile,
        warnings=warnings,
        evidence_references=(
            ParserEvidenceReference(
                reference_id=f"fx::{evidence_suffix}::analysis",
                evidence_kind="search-source-analysis",
            ),
        ),
        explanation=ParserOutcomeExplanation(
            summary="synthetic search source analysis",
            reason_code=f"FX::{evidence_suffix}",
            status=status,
            warnings=warnings,
        ),
    )


def _search_configuration(
    extraction_id: str,
    request: ParserRequestEnvelope,
    transport: TransportOutcomeReference,
    profile: ParserCompatibilityProfile,
    *,
    status: ParserOutcomeStatus | TransportOutcomeStatus | ReferenceOutcomeStatus,
    evidence_suffix: str,
    normalized_filters: tuple[str, ...] = (),
    sort_context_reference: str | None = None,
    warnings: tuple[ParserWarning, ...] = (),
) -> SearchConfigurationExtractionOutcome:
    return SearchConfigurationExtractionOutcome(
        extraction_id=extraction_id,
        request_envelope=request,
        transport_outcome=transport,
        status=status,
        compatibility_profile=profile,
        normalized_geography_candidates=("synthetic-city",),
        normalized_category_candidates=("synthetic-category",),
        normalized_filter_candidates=normalized_filters,
        observed_sort_context_reference=sort_context_reference,
        warnings=warnings,
        evidence_references=(
            ParserEvidenceReference(
                reference_id=f"fx::{evidence_suffix}::configuration",
                evidence_kind="search-configuration",
            ),
        ),
        explanation=ParserOutcomeExplanation(
            summary="synthetic search configuration extraction",
            reason_code=f"FX::{evidence_suffix}",
            status=status,
            warnings=warnings,
        ),
    )


def _listing_page(
    page_id: str,
    request: ParserRequestEnvelope,
    transport: TransportOutcomeReference,
    profile: ParserCompatibilityProfile,
    *,
    status: ParserOutcomeStatus | TransportOutcomeStatus | ReferenceOutcomeStatus,
    candidate: NormalizedListingCandidate | None = None,
    card: ListingCardCandidate | None = None,
    evidence_suffix: str,
    warnings: tuple[ParserWarning, ...] = (),
) -> ListingPageParseOutcome:
    normalized_candidates = () if candidate is None else (candidate,)
    card_candidates = () if card is None else (card,)
    return ListingPageParseOutcome(
        page_id=page_id,
        request_envelope=request,
        transport_outcome=transport,
        status=status,
        compatibility_profile=profile,
        normalized_listing_candidates=normalized_candidates,
        card_candidates=card_candidates,
        warnings=warnings,
        evidence_references=(
            ParserEvidenceReference(
                reference_id=f"fx::{evidence_suffix}::page",
                evidence_kind="listing-page",
            ),
        ),
        explanation=ParserOutcomeExplanation(
            summary="synthetic listing page parse",
            reason_code=f"FX::{evidence_suffix}",
            status=status,
            warnings=warnings,
        ),
    )


def _listing_batch(
    batch_id: str,
    request: ParserRequestEnvelope,
    transport: TransportOutcomeReference,
    profile: ParserCompatibilityProfile,
    *,
    status: ParserOutcomeStatus | TransportOutcomeStatus | ReferenceOutcomeStatus,
    page_outcomes: tuple[ListingPageParseOutcome, ...],
    evidence_suffix: str,
    warnings: tuple[ParserWarning, ...] = (),
) -> ListingBatchParseOutcome:
    return ListingBatchParseOutcome(
        batch_id=batch_id,
        request_envelope=request,
        transport_outcome=transport,
        status=status,
        compatibility_profile=profile,
        page_outcomes=page_outcomes,
        warnings=warnings,
        evidence_references=(
            ParserEvidenceReference(
                reference_id=f"fx::{evidence_suffix}::batch",
                evidence_kind="listing-batch",
            ),
        ),
        explanation=ParserOutcomeExplanation(
            summary="synthetic listing batch parse",
            reason_code=f"FX::{evidence_suffix}",
            status=status,
            warnings=warnings,
        ),
    )


def _fixture(
    fixture_id: str,
    summary: str,
    request_envelope: ParserRequestEnvelope,
    transport_outcome: TransportOutcomeReference,
    attempt_outcome: ParserAttemptOutcome,
    *,
    search_source_analysis_outcome: SearchSourceAnalysisOutcome | None = None,
    search_configuration_extraction_outcome: SearchConfigurationExtractionOutcome | None = None,
    listing_page_parse_outcome: ListingPageParseOutcome | None = None,
    listing_batch_parse_outcome: ListingBatchParseOutcome | None = None,
) -> SyntheticFixtureCase:
    return SyntheticFixtureCase(
        fixture_id=fixture_id,
        summary=summary,
        request_envelope=request_envelope,
        transport_outcome=transport_outcome,
        attempt_outcome=attempt_outcome,
        search_source_analysis_outcome=search_source_analysis_outcome,
        search_configuration_extraction_outcome=search_configuration_extraction_outcome,
        listing_page_parse_outcome=listing_page_parse_outcome,
        listing_batch_parse_outcome=listing_batch_parse_outcome,
    )


_PROFILE_TIER1 = _profile("fx-apa02-profile-tier1", evidence_suffix="tier1")
_PROFILE_EMPTY = _profile("fx-apa02-profile-empty", evidence_suffix="empty")
_PROFILE_RESTRICTED = _profile("fx-apa02-profile-restricted", evidence_suffix="restricted")
_PROFILE_MALFORMED = _profile("fx-apa02-profile-malformed", evidence_suffix="malformed")
_PROFILE_AMBIGUOUS = _profile("fx-apa02-profile-ambiguous", evidence_suffix="ambiguous")
_PROFILE_OPTIONAL = _profile("fx-apa02-profile-optional", evidence_suffix="optional")
_PROFILE_MULTIVALUE = _profile("fx-apa02-profile-multivalue", evidence_suffix="multivalue")
_PROFILE_SORT = _profile("fx-apa02-profile-sort", evidence_suffix="sort")
_PROFILE_PARTIAL = _profile("fx-apa02-profile-partial", evidence_suffix="partial")
_PROFILE_STALE = _profile(
    "fx-apa02-profile-stale",
    reference_status=ReferenceOutcomeStatus.REFERENCE_STALE,
    evidence_suffix="stale",
)

_REQUEST_TIER1 = _request(
    "fx-apa02-request-tier1",
    _PROFILE_TIER1,
    purpose="search-page-parse",
    safe_source_reference="source::tier1",
    requested_page_numbers=(1,),
)
_REQUEST_EMPTY = _request(
    "fx-apa02-request-empty",
    _PROFILE_EMPTY,
    purpose="source-analysis",
    safe_source_reference="source::empty",
)
_REQUEST_RESTRICTED = _request(
    "fx-apa02-request-restricted",
    _PROFILE_RESTRICTED,
    purpose="page-parse",
    safe_source_reference="source::restricted",
)
_REQUEST_MALFORMED = _request(
    "fx-apa02-request-malformed",
    _PROFILE_MALFORMED,
    purpose="page-parse",
    safe_source_reference="source::malformed",
)
_REQUEST_AMBIGUOUS = _request(
    "fx-apa02-request-ambiguous",
    _PROFILE_AMBIGUOUS,
    purpose="page-parse",
    safe_source_reference="source::ambiguous",
)
_REQUEST_OPTIONAL = _request(
    "fx-apa02-request-optional",
    _PROFILE_OPTIONAL,
    purpose="page-parse",
    safe_source_reference="source::optional",
)
_REQUEST_MULTIVALUE = _request(
    "fx-apa02-request-multivalue",
    _PROFILE_MULTIVALUE,
    purpose="configuration-extraction",
    safe_source_reference="source::multivalue",
)
_REQUEST_SORT = _request(
    "fx-apa02-request-sort",
    _PROFILE_SORT,
    purpose="configuration-extraction",
    safe_source_reference="source::sort",
)
_REQUEST_PARTIAL = _request(
    "fx-apa02-request-partial",
    _PROFILE_PARTIAL,
    purpose="batch-parse",
    safe_source_reference="source::partial",
    requested_page_numbers=(1, 2),
)
_REQUEST_STALE = _request(
    "fx-apa02-request-stale",
    _PROFILE_STALE,
    purpose="source-analysis",
    safe_source_reference="source::stale",
)

_TRANSPORT_TIER1 = _transport(
    "fx-apa02-transport-tier1",
    status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
    request_reference=_REQUEST_TIER1.request_id,
    response_reference="response::tier1",
    route_reference="route::synthetic",
    evidence_reference_suffix="tier1",
)
_TRANSPORT_EMPTY = _transport(
    "fx-apa02-transport-empty",
    status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
    request_reference=_REQUEST_EMPTY.request_id,
    response_reference="response::empty",
    route_reference="route::synthetic",
    evidence_reference_suffix="empty",
)
_TRANSPORT_RESTRICTED = _transport(
    "fx-apa02-transport-restricted",
    status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
    request_reference=_REQUEST_RESTRICTED.request_id,
    response_reference="response::restricted",
    route_reference="route::synthetic",
    evidence_reference_suffix="restricted",
)
_TRANSPORT_MALFORMED = _transport(
    "fx-apa02-transport-malformed",
    status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
    request_reference=_REQUEST_MALFORMED.request_id,
    response_reference="response::malformed",
    route_reference="route::synthetic",
    evidence_reference_suffix="malformed",
)
_TRANSPORT_AMBIGUOUS = _transport(
    "fx-apa02-transport-ambiguous",
    status=TransportOutcomeStatus.TRANSPORT_AMBIGUOUS,
    request_reference=_REQUEST_AMBIGUOUS.request_id,
    response_reference="response::ambiguous",
    route_reference="route::synthetic",
    evidence_reference_suffix="ambiguous",
)
_TRANSPORT_OPTIONAL = _transport(
    "fx-apa02-transport-optional",
    status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
    request_reference=_REQUEST_OPTIONAL.request_id,
    response_reference="response::optional",
    route_reference="route::synthetic",
    evidence_reference_suffix="optional",
)
_TRANSPORT_MULTIVALUE = _transport(
    "fx-apa02-transport-multivalue",
    status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
    request_reference=_REQUEST_MULTIVALUE.request_id,
    response_reference="response::multivalue",
    route_reference="route::synthetic",
    evidence_reference_suffix="multivalue",
)
_TRANSPORT_SORT = _transport(
    "fx-apa02-transport-sort",
    status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
    request_reference=_REQUEST_SORT.request_id,
    response_reference="response::sort",
    route_reference="route::synthetic",
    evidence_reference_suffix="sort",
)
_TRANSPORT_PARTIAL = _transport(
    "fx-apa02-transport-partial",
    status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
    request_reference=_REQUEST_PARTIAL.request_id,
    response_reference="response::partial",
    route_reference="route::synthetic",
    evidence_reference_suffix="partial",
)
_TRANSPORT_STALE = _transport(
    "fx-apa02-transport-stale",
    status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
    request_reference=_REQUEST_STALE.request_id,
    response_reference="response::stale",
    route_reference="route::synthetic",
    evidence_reference_suffix="stale",
)

_CARD_TIER1 = _usable_listing_card("fx-apa02-card-tier1", evidence_suffix="tier1")
_CARD_OPTIONAL_PHONE = _usable_listing_card(
    "fx-apa02-card-optional-phone",
    evidence_suffix="optional-phone",
    phone=None,
)
_CARD_OPTIONAL_UNAVAILABLE = _usable_listing_card(
    "fx-apa02-card-optional-unavailable",
    evidence_suffix="optional-unavailable",
    seller=None,
    seller_rating=None,
    description=None,
)

_LISTING_TIER1 = _listing_candidate(
    "fx-apa02-listing-tier1",
    _CARD_TIER1,
    evidence_suffix="tier1",
)
_LISTING_OPTIONAL_PHONE = _listing_candidate(
    "fx-apa02-listing-optional-phone",
    _CARD_OPTIONAL_PHONE,
    evidence_suffix="optional-phone",
)
_LISTING_OPTIONAL_UNAVAILABLE = _listing_candidate(
    "fx-apa02-listing-optional-unavailable",
    _CARD_OPTIONAL_UNAVAILABLE,
    evidence_suffix="optional-unavailable",
    warnings=(
        ParserWarning(
            code=ParserWarningCode.SELLER_UNAVAILABLE,
            message="seller evidence unavailable in synthetic case",
        ),
        ParserWarning(
            code=ParserWarningCode.RATING_UNAVAILABLE,
            message="rating evidence unavailable in synthetic case",
        ),
        ParserWarning(
            code=ParserWarningCode.DESCRIPTION_UNAVAILABLE,
            message="description evidence unavailable in synthetic case",
        ),
    ),
)

_PAGE_TIER1 = _listing_page(
    "fx-apa02-page-tier1",
    _REQUEST_TIER1,
    _TRANSPORT_TIER1,
    _PROFILE_TIER1,
    status=ParserOutcomeStatus.USABLE_RESPONSE,
    candidate=_LISTING_TIER1,
    card=_CARD_TIER1,
    evidence_suffix="tier1",
)
_PAGE_EMPTY = _listing_page(
    "fx-apa02-page-empty",
    _REQUEST_EMPTY,
    _TRANSPORT_EMPTY,
    _PROFILE_EMPTY,
    status=ParserOutcomeStatus.USABLE_RESPONSE,
    evidence_suffix="empty",
    warnings=(
        ParserWarning(
            code=ParserWarningCode.EMPTY_RESULT_PROVEN,
            message="clean empty result is proven by compatibility profile",
        ),
    ),
)
_PAGE_RESTRICTED = _listing_page(
    "fx-apa02-page-restricted",
    _REQUEST_RESTRICTED,
    _TRANSPORT_RESTRICTED,
    _PROFILE_RESTRICTED,
    status=ParserOutcomeStatus.RATE_OR_ACCESS_RESTRICTED,
    evidence_suffix="restricted",
)
_PAGE_MALFORMED = _listing_page(
    "fx-apa02-page-malformed",
    _REQUEST_MALFORMED,
    _TRANSPORT_MALFORMED,
    _PROFILE_MALFORMED,
    status=ParserOutcomeStatus.MALFORMED_RESPONSE,
    evidence_suffix="malformed",
)
_PAGE_AMBIGUOUS = _listing_page(
    "fx-apa02-page-ambiguous",
    _REQUEST_AMBIGUOUS,
    _TRANSPORT_AMBIGUOUS,
    _PROFILE_AMBIGUOUS,
    status=ParserOutcomeStatus.RESULT_AMBIGUOUS,
    evidence_suffix="ambiguous",
)
_PAGE_OPTIONAL = _listing_page(
    "fx-apa02-page-optional",
    _REQUEST_OPTIONAL,
    _TRANSPORT_OPTIONAL,
    _PROFILE_OPTIONAL,
    status=ParserOutcomeStatus.USABLE_RESPONSE,
    candidate=_LISTING_OPTIONAL_PHONE,
    card=_CARD_OPTIONAL_PHONE,
    evidence_suffix="optional",
    warnings=(
        ParserWarning(
            code=ParserWarningCode.PHONE_UNAVAILABLE,
            message="phone is evidence-gated and unavailable",
        ),
    ),
)
_PAGE_OPTIONAL_UNAVAILABLE = _listing_page(
    "fx-apa02-page-optional-unavailable",
    _REQUEST_OPTIONAL,
    _TRANSPORT_OPTIONAL,
    _PROFILE_OPTIONAL,
    status=ParserOutcomeStatus.USABLE_RESPONSE,
    candidate=_LISTING_OPTIONAL_UNAVAILABLE,
    card=_CARD_OPTIONAL_UNAVAILABLE,
    evidence_suffix="optional-unavailable",
    warnings=_LISTING_OPTIONAL_UNAVAILABLE.warnings,
)
_PAGE_SORT = _listing_page(
    "fx-apa02-page-sort",
    _REQUEST_SORT,
    _TRANSPORT_SORT,
    _PROFILE_SORT,
    status=ParserOutcomeStatus.USABLE_RESPONSE,
    evidence_suffix="sort",
    warnings=(
        ParserWarning(
            code=ParserWarningCode.SORT_CONTEXT_AMBIGUOUS,
            message="observed sort context is handoff evidence only",
        ),
    ),
)
_PAGE_PARTIAL = _listing_page(
    "fx-apa02-page-partial",
    _REQUEST_PARTIAL,
    _TRANSPORT_PARTIAL,
    _PROFILE_PARTIAL,
    status=ParserOutcomeStatus.PARTIAL,
    candidate=_LISTING_TIER1,
    card=_CARD_TIER1,
    evidence_suffix="partial",
    warnings=(
        ParserWarning(
            code=ParserWarningCode.PARTIAL_PAGE,
            message="page outcome is partial in synthetic case",
        ),
    ),
)
_BATCH_PARTIAL = _listing_batch(
    "fx-apa02-batch-partial",
    _REQUEST_PARTIAL,
    _TRANSPORT_PARTIAL,
    _PROFILE_PARTIAL,
    status=ParserOutcomeStatus.PARTIAL,
    page_outcomes=(_PAGE_PARTIAL,),
    evidence_suffix="partial",
    warnings=(
        ParserWarning(
            code=ParserWarningCode.PARTIAL_PAGE,
            message="batch outcome is partial in synthetic case",
        ),
    ),
)

SYNTHETIC_FIXTURE_CASES: Final[tuple[SyntheticFixtureCase, ...]] = (
    _fixture(
        "FX-APA02-USABLE-SEARCH-TIER1-001",
        "usable search result with Tier 1 fields",
        _REQUEST_TIER1,
        _TRANSPORT_TIER1,
        _usable_attempt(
            "fx-apa02-attempt-tier1",
            _PROFILE_TIER1,
            _REQUEST_TIER1,
            _TRANSPORT_TIER1,
            evidence_suffix="tier1",
        ),
        search_source_analysis_outcome=_search_source_analysis(
            "fx-apa02-analysis-tier1",
            _REQUEST_TIER1,
            _TRANSPORT_TIER1,
            _PROFILE_TIER1,
            status=ParserOutcomeStatus.USABLE_RESPONSE,
            evidence_suffix="tier1",
        ),
        search_configuration_extraction_outcome=_search_configuration(
            "fx-apa02-extraction-tier1",
            _REQUEST_TIER1,
            _TRANSPORT_TIER1,
            _PROFILE_TIER1,
            status=ParserOutcomeStatus.USABLE_RESPONSE,
            evidence_suffix="tier1",
            normalized_filters=("city=synthetic", "category=synthetic"),
            sort_context_reference="sort-context::tier1",
        ),
        listing_page_parse_outcome=_PAGE_TIER1,
    ),
    _fixture(
        "FX-APA02-CLEAN-EMPTY-COMPATIBILITY-PROOF-001",
        "clean empty result with compatibility-profile proof",
        _REQUEST_EMPTY,
        _TRANSPORT_EMPTY,
        _usable_attempt(
            "fx-apa02-attempt-empty",
            _PROFILE_EMPTY,
            _REQUEST_EMPTY,
            _TRANSPORT_EMPTY,
            evidence_suffix="empty",
            warnings=(
                ParserWarning(
                    code=ParserWarningCode.EMPTY_RESULT_PROVEN,
                    message="empty result is explicitly proven",
                ),
            ),
        ),
        search_source_analysis_outcome=_search_source_analysis(
            "fx-apa02-analysis-empty",
            _REQUEST_EMPTY,
            _TRANSPORT_EMPTY,
            _PROFILE_EMPTY,
            status=ParserOutcomeStatus.USABLE_RESPONSE,
            evidence_suffix="empty",
        ),
        listing_page_parse_outcome=_PAGE_EMPTY,
    ),
    _fixture(
        "FX-APA02-FALSE-EMPTY-RESTRICTED-001",
        "false-empty prevention for restricted response",
        _REQUEST_RESTRICTED,
        _TRANSPORT_RESTRICTED,
        _usable_attempt(
            "fx-apa02-attempt-restricted",
            _PROFILE_RESTRICTED,
            _REQUEST_RESTRICTED,
            _TRANSPORT_RESTRICTED,
            parser_status=ParserOutcomeStatus.RATE_OR_ACCESS_RESTRICTED,
            evidence_suffix="restricted",
        ),
        listing_page_parse_outcome=_PAGE_RESTRICTED,
    ),
    _fixture(
        "FX-APA02-FALSE-EMPTY-MALFORMED-001",
        "false-empty prevention for malformed response",
        _REQUEST_MALFORMED,
        _TRANSPORT_MALFORMED,
        _usable_attempt(
            "fx-apa02-attempt-malformed",
            _PROFILE_MALFORMED,
            _REQUEST_MALFORMED,
            _TRANSPORT_MALFORMED,
            parser_status=ParserOutcomeStatus.MALFORMED_RESPONSE,
            evidence_suffix="malformed",
        ),
        listing_page_parse_outcome=_PAGE_MALFORMED,
    ),
    _fixture(
        "FX-APA02-FALSE-EMPTY-AMBIGUOUS-001",
        "false-empty prevention for ambiguous response",
        _REQUEST_AMBIGUOUS,
        _TRANSPORT_AMBIGUOUS,
        _usable_attempt(
            "fx-apa02-attempt-ambiguous",
            _PROFILE_AMBIGUOUS,
            _REQUEST_AMBIGUOUS,
            _TRANSPORT_AMBIGUOUS,
            parser_status=ParserOutcomeStatus.RESULT_AMBIGUOUS,
            evidence_suffix="ambiguous",
        ),
        listing_page_parse_outcome=_PAGE_AMBIGUOUS,
    ),
    _fixture(
        "FX-APA02-OPTIONAL-PHONE-UNAVAILABLE-001",
        "optional phone unavailable without listing failure",
        _REQUEST_OPTIONAL,
        _TRANSPORT_OPTIONAL,
        _usable_attempt(
            "fx-apa02-attempt-optional",
            _PROFILE_OPTIONAL,
            _REQUEST_OPTIONAL,
            _TRANSPORT_OPTIONAL,
            warnings=(
                ParserWarning(
                    code=ParserWarningCode.PHONE_UNAVAILABLE,
                    message="phone is unavailable in synthetic case",
                ),
            ),
            evidence_suffix="optional",
        ),
        listing_page_parse_outcome=_PAGE_OPTIONAL,
    ),
    _fixture(
        "FX-APA02-SELLER-RATING-DESCRIPTION-UNAVAILABLE-001",
        "seller/rating/description unavailable warnings",
        _REQUEST_OPTIONAL,
        _TRANSPORT_OPTIONAL,
        _usable_attempt(
            "fx-apa02-attempt-optional-unavailable",
            _PROFILE_OPTIONAL,
            _REQUEST_OPTIONAL,
            _TRANSPORT_OPTIONAL,
            warnings=_LISTING_OPTIONAL_UNAVAILABLE.warnings,
            evidence_suffix="optional-unavailable",
        ),
        listing_page_parse_outcome=_PAGE_OPTIONAL_UNAVAILABLE,
    ),
    _fixture(
        "FX-APA02-REPEATED-MULTIVALUE-FILTER-PRESERVATION-001",
        "repeated/multivalue filter preservation",
        _REQUEST_MULTIVALUE,
        _TRANSPORT_MULTIVALUE,
        _usable_attempt(
            "fx-apa02-attempt-multivalue",
            _PROFILE_MULTIVALUE,
            _REQUEST_MULTIVALUE,
            _TRANSPORT_MULTIVALUE,
            evidence_suffix="multivalue",
        ),
        search_configuration_extraction_outcome=_search_configuration(
            "fx-apa02-extraction-multivalue",
            _REQUEST_MULTIVALUE,
            _TRANSPORT_MULTIVALUE,
            _PROFILE_MULTIVALUE,
            status=ParserOutcomeStatus.USABLE_RESPONSE,
            evidence_suffix="multivalue",
            normalized_filters=("city=synthetic", "city=synthetic", "metro=synthetic"),
            warnings=(
                ParserWarning(
                    code=ParserWarningCode.MULTIVALUE_FILTER_PRESERVED,
                    message="repeated filter values are preserved",
                ),
            ),
        ),
    ),
    _fixture(
        "FX-APA02-AMBIGUOUS-SORT-NEWEST-EVIDENCE-001",
        "ambiguous sort/newest evidence handoff",
        _REQUEST_SORT,
        _TRANSPORT_SORT,
        _usable_attempt(
            "fx-apa02-attempt-sort",
            _PROFILE_SORT,
            _REQUEST_SORT,
            _TRANSPORT_SORT,
            evidence_suffix="sort",
            warnings=(
                ParserWarning(
                    code=ParserWarningCode.SORT_CONTEXT_AMBIGUOUS,
                    message="sort/newest evidence is ambiguous and handed off to Scan",
                ),
            ),
        ),
        search_configuration_extraction_outcome=_search_configuration(
            "fx-apa02-extraction-sort",
            _REQUEST_SORT,
            _TRANSPORT_SORT,
            _PROFILE_SORT,
            status=ParserOutcomeStatus.USABLE_RESPONSE,
            evidence_suffix="sort",
            sort_context_reference="sort-context::newest-vs-ambiguous",
            warnings=(
                ParserWarning(
                    code=ParserWarningCode.SORT_CONTEXT_AMBIGUOUS,
                    message="observed sort context is a scan handoff only",
                ),
            ),
        ),
        listing_page_parse_outcome=_PAGE_SORT,
    ),
    _fixture(
        "FX-APA02-PARTIAL-PAGE-BATCH-001",
        "partial page and batch outcome",
        _REQUEST_PARTIAL,
        _TRANSPORT_PARTIAL,
        _usable_attempt(
            "fx-apa02-attempt-partial",
            _PROFILE_PARTIAL,
            _REQUEST_PARTIAL,
            _TRANSPORT_PARTIAL,
            parser_status=ParserOutcomeStatus.PARTIAL,
            evidence_suffix="partial",
            warnings=(
                ParserWarning(
                    code=ParserWarningCode.PARTIAL_PAGE,
                    message="partial parser result in synthetic case",
                ),
            ),
        ),
        listing_page_parse_outcome=_PAGE_PARTIAL,
        listing_batch_parse_outcome=_BATCH_PARTIAL,
    ),
    _fixture(
        "FX-APA02-STALE-COMPATIBILITY-PROFILE-001",
        "stale compatibility profile",
        _REQUEST_STALE,
        _TRANSPORT_STALE,
        _usable_attempt(
            "fx-apa02-attempt-stale",
            _PROFILE_STALE,
            _REQUEST_STALE,
            _TRANSPORT_STALE,
            reference_status=ReferenceOutcomeStatus.REFERENCE_STALE,
            evidence_suffix="stale",
            warnings=(
                ParserWarning(
                    code=ParserWarningCode.STALE_COMPATIBILITY_PROFILE,
                    message="compatibility profile is stale in synthetic case",
                ),
            ),
        ),
        search_source_analysis_outcome=_search_source_analysis(
            "fx-apa02-analysis-stale",
            _REQUEST_STALE,
            _TRANSPORT_STALE,
            _PROFILE_STALE,
            status=ReferenceOutcomeStatus.REFERENCE_STALE,
            evidence_suffix="stale",
            warnings=(
                ParserWarning(
                    code=ParserWarningCode.STALE_COMPATIBILITY_PROFILE,
                    message="compatibility profile is stale in synthetic case",
                ),
            ),
        ),
    ),
)

SYNTHETIC_FIXTURE_BY_ID: Final[dict[str, SyntheticFixtureCase]] = {
    fixture.fixture_id: fixture for fixture in SYNTHETIC_FIXTURE_CASES
}

FIXTURE_IDS: Final[tuple[str, ...]] = tuple(fixture.fixture_id for fixture in SYNTHETIC_FIXTURE_CASES)

__all__: Final[tuple[str, ...]] = (
    "SyntheticFixtureCase",
    "SYNTHETIC_FIXTURE_CASES",
    "SYNTHETIC_FIXTURE_BY_ID",
    "FIXTURE_IDS",
)
