"""Safe synthetic fixture identifiers for Avito Parser Adapter semantics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from .contracts import (
    CompatibilityChangeClass,
    CompatibilityProfileAuthorityClass,
    CompatibilityProfileLifecycleStatus,
    CompatibilityRevalidationTrigger,
    ListingBatchParseOutcome,
    ListingCardCandidate,
    ListingPageParseOutcome,
    NormalizedListingCandidate,
    ParserCompatibilityOutcome,
    ParserAttemptOutcome,
    ParserCompatibilityProfile,
    ParserEvidenceReference,
    ParserOutcomeExplanation,
    ParserOutcomeStatus,
    ParserSourceReference,
    ParserRequestEnvelope,
    ParserWarning,
    ParserWarningCode,
    _lifecycle_status_from_reference_status,
    ReferenceOutcomeStatus,
    SearchConfigurationExtractionOutcome,
    SearchSourceAnalysisOutcome,
    SourceBoundaryOutcome,
    SourceBoundaryPolicyRequirement,
    SourceBoundaryRiskCode,
    SourceBoundaryStatus,
    SourceReferenceKind,
    TransportOutcomeReference,
    TransportOutcomeStatus,
    _reference_status_from_lifecycle_status,
)


@dataclass(frozen=True, slots=True)
class SyntheticFixtureCase:
    """Synthetic semantic case with no real provider payloads."""

    fixture_id: str
    summary: str
    request_envelope: ParserRequestEnvelope
    transport_outcome: TransportOutcomeReference
    attempt_outcome: ParserAttemptOutcome
    source_boundary_outcome: SourceBoundaryOutcome | None = None
    compatibility_profile: ParserCompatibilityProfile | None = None
    compatibility_outcome: ParserCompatibilityOutcome | None = None
    search_source_analysis_outcome: SearchSourceAnalysisOutcome | None = None
    search_configuration_extraction_outcome: SearchConfigurationExtractionOutcome | None = None
    listing_page_parse_outcome: ListingPageParseOutcome | None = None
    listing_batch_parse_outcome: ListingBatchParseOutcome | None = None

    def __post_init__(self) -> None:
        if not self.fixture_id.strip():
            raise ValueError("fixture_id must not be blank")
        if not self.summary.strip():
            raise ValueError("summary must not be blank")
        if self.source_boundary_outcome is None:
            object.__setattr__(self, "source_boundary_outcome", self.request_envelope.source_boundary_outcome)
        if self.compatibility_profile is None:
            object.__setattr__(self, "compatibility_profile", self.request_envelope.compatibility_profile)


def _profile(
    profile_id: str,
    *,
    lifecycle_status: CompatibilityProfileLifecycleStatus | None = None,
    authority_class: CompatibilityProfileAuthorityClass = CompatibilityProfileAuthorityClass.OBSERVATION_ONLY,
    reference_status: ReferenceOutcomeStatus = ReferenceOutcomeStatus.CURRENT,
    evidence_suffix: str,
    reference_ids: tuple[str, ...] = ("AVITO-PRIMARY-PARSER-001",),
    primary_reference_repository: str = "Duff89/parser_avito",
    primary_reference_commit: str = "48441c352e36919abef13c436f41a3a62636da17",
    retrieval_date: str = "2026-07-09",
    effective_date: str = "2026-07-09",
    supported_extraction_claims: tuple[str, ...] = (),
    unsupported_extraction_claims: tuple[str, ...] = (
        "official/public contract",
        "internal endpoint stability",
        "phone extraction permission",
        "production suitability",
    ),
    required_fields: tuple[str, ...] = ("profile_id", "semantic_version", "reference_ids"),
    completeness_rules: tuple[str, ...] = (
        "supported extraction claims are explicit",
        "unsupported claims remain explicit",
    ),
    warning_mappings: tuple[str, ...] = (
        "REFERENCE_CHANGED->COMPATIBILITY_REVALIDATION_REQUIRED",
        "REFERENCE_DISPUTED->DISPUTED_PROFILE_WARNING",
    ),
    error_mappings: tuple[str, ...] = (
        "REFERENCE_WITHDRAWN->WITHDRAWN_PROFILE_BLOCKED",
        "REFERENCE_UNAVAILABLE->UNAVAILABLE_PROFILE_WARNING",
    ),
    fixture_ids: tuple[str, ...] = (),
    acceptance_matrix_rows: tuple[str, ...] = (),
    revalidation_triggers: tuple[CompatibilityRevalidationTrigger, ...] = (
        CompatibilityRevalidationTrigger.REFERENCE_CHANGED,
        CompatibilityRevalidationTrigger.EXTRACTION_CLAIM_CHANGED,
        CompatibilityRevalidationTrigger.PARSER_WARNING_MAPPING_CHANGED,
        CompatibilityRevalidationTrigger.FIXTURE_MATRIX_CHANGED,
        CompatibilityRevalidationTrigger.PROVIDER_STRUCTURE_UNPROVEN_OR_STALE,
        CompatibilityRevalidationTrigger.OWNER_DECISION_CHANGED,
    ),
    compatibility_change_classes: tuple[CompatibilityChangeClass, ...] = (
        CompatibilityChangeClass.COMPATIBLE,
        CompatibilityChangeClass.WARNING,
        CompatibilityChangeClass.BREAKING,
        CompatibilityChangeClass.UNKNOWN,
        CompatibilityChangeClass.DISPUTED,
        CompatibilityChangeClass.UNAVAILABLE,
    ),
) -> ParserCompatibilityProfile:
    effective_lifecycle_status = (
        lifecycle_status if lifecycle_status is not None else _lifecycle_status_from_reference_status(reference_status)
    )
    evidence_reference = ParserEvidenceReference(
        reference_id=f"fx::{evidence_suffix}::profile",
        evidence_kind="compatibility-profile",
        reference_status=reference_status,
        lifecycle_status=effective_lifecycle_status,
        fingerprint=f"fingerprint::{evidence_suffix}",
        version="2026.07.09",
        notes=(f"synthetic compatibility profile {profile_id}",),
    )
    return ParserCompatibilityProfile(
        profile_id=profile_id,
        semantic_version="2026.07.09",
        profile_version="2026.07.09",
        lifecycle_status=effective_lifecycle_status,
        authority_class=authority_class,
        authority_scope=("observation-only", "synthetic"),
        reference_ids=reference_ids,
        primary_reference_repository=primary_reference_repository,
        primary_reference_commit=primary_reference_commit,
        retrieval_date=retrieval_date,
        effective_date=effective_date,
        reference_status=reference_status,
        source_reference=f"safe-source::{evidence_suffix}",
        evidence_reference=evidence_reference,
        supported_extraction_claims=supported_extraction_claims,
        supported_shape_signatures=supported_extraction_claims or (f"shape::{evidence_suffix}::tier1",),
        unsupported_extraction_claims=unsupported_extraction_claims,
        unsupported_shape_signatures=unsupported_extraction_claims,
        required_fields=required_fields,
        completeness_rules=completeness_rules,
        warning_mappings=warning_mappings,
        error_mappings=error_mappings,
        fixture_ids=fixture_ids,
        acceptance_matrix_rows=acceptance_matrix_rows,
        revalidation_triggers=revalidation_triggers,
        compatibility_change_classes=compatibility_change_classes,
        notes=(f"synthetic profile {profile_id}",),
    )


def _request(
    request_id: str,
    profile: ParserCompatibilityProfile,
    *,
    purpose: str,
    safe_source_reference: str,
    source_reference: ParserSourceReference | None = None,
    source_boundary_outcome: SourceBoundaryOutcome | None = None,
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
        source_reference=source_reference,
        source_boundary_outcome=source_boundary_outcome,
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


def _source_reference(
    source_reference_id: str,
    *,
    kind: SourceReferenceKind,
    bounded_value: str = "source-ref:beacon-revision-001",
    owner: str = "Beacon Management",
    notes: tuple[str, ...] = (),
) -> ParserSourceReference:
    return ParserSourceReference(
        source_reference_id=source_reference_id,
        source_reference_kind=kind,
        bounded_value=bounded_value,
        owner=owner,
        notes=notes,
    )


def _source_boundary(
    source_boundary_id: str,
    source_reference: ParserSourceReference,
    *,
    status: SourceBoundaryStatus,
    evidence_suffix: str,
    policy_requirements: tuple[SourceBoundaryPolicyRequirement, ...] = (),
    risk_codes: tuple[SourceBoundaryRiskCode, ...] = (),
    warning_codes: tuple[ParserWarningCode, ...] = (),
    warning_message: str | None = None,
) -> SourceBoundaryOutcome:
    warnings = tuple(
        ParserWarning(
            code=code,
            message=warning_message or f"source boundary {code.value.lower()} in synthetic case",
        )
        for code in warning_codes
    )
    return SourceBoundaryOutcome(
        source_boundary_id=source_boundary_id,
        source_reference=source_reference,
        status=status,
        policy_requirements=policy_requirements,
        risk_codes=risk_codes,
        warnings=warnings,
        evidence_references=(
            ParserEvidenceReference(
                reference_id=f"fx::{evidence_suffix}::source-boundary",
                evidence_kind="source-boundary",
            ),
        ),
        explanation=ParserOutcomeExplanation(
            summary="synthetic source boundary decision",
            reason_code=f"FX::{evidence_suffix}",
            status=status,
            warnings=warnings,
        ),
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


def _source_boundary_attempt(
    attempt_id: str,
    request: ParserRequestEnvelope,
    *,
    parser_status: ParserOutcomeStatus,
    evidence_suffix: str,
    warnings: tuple[ParserWarning, ...] = (),
) -> ParserAttemptOutcome:
    transport = _transport(
        transport_reference_id=f"fx::{evidence_suffix}::transport",
        status=TransportOutcomeStatus.NOT_SENT,
        request_reference=request.request_id,
        response_reference=None,
        route_reference=None,
        evidence_reference_suffix=evidence_suffix,
    )
    return ParserAttemptOutcome(
        attempt_id=attempt_id,
        transport_status=TransportOutcomeStatus.NOT_SENT,
        parser_status=parser_status,
        request_envelope=request,
        transport_outcome=transport,
        warnings=warnings,
        evidence_references=transport.evidence_references,
        explanation=ParserOutcomeExplanation(
            summary="synthetic source boundary attempt",
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
    source_boundary_outcome: SourceBoundaryOutcome | None = None,
    compatibility_profile: ParserCompatibilityProfile | None = None,
    compatibility_outcome: ParserCompatibilityOutcome | None = None,
    search_source_analysis_outcome: SearchSourceAnalysisOutcome | None = None,
    search_configuration_extraction_outcome: SearchConfigurationExtractionOutcome | None = None,
    listing_page_parse_outcome: ListingPageParseOutcome | None = None,
    listing_batch_parse_outcome: ListingBatchParseOutcome | None = None,
) -> SyntheticFixtureCase:
    return SyntheticFixtureCase(
        fixture_id=fixture_id,
        summary=summary,
        source_boundary_outcome=source_boundary_outcome or request_envelope.source_boundary_outcome,
        compatibility_profile=compatibility_profile or request_envelope.compatibility_profile,
        request_envelope=request_envelope,
        transport_outcome=transport_outcome,
        attempt_outcome=attempt_outcome,
        compatibility_outcome=compatibility_outcome,
        search_source_analysis_outcome=search_source_analysis_outcome,
        search_configuration_extraction_outcome=search_configuration_extraction_outcome,
        listing_page_parse_outcome=listing_page_parse_outcome,
        listing_batch_parse_outcome=listing_batch_parse_outcome,
    )


def _compatibility_outcome(
    outcome_id: str,
    profile: ParserCompatibilityProfile,
    *,
    lifecycle_status: CompatibilityProfileLifecycleStatus,
    change_class: CompatibilityChangeClass,
    status: (
        ParserOutcomeStatus
        | TransportOutcomeStatus
        | ReferenceOutcomeStatus
        | CompatibilityProfileLifecycleStatus
        | CompatibilityChangeClass
        | None
    ) = None,
    evidence_suffix: str,
    warnings: tuple[ParserWarning, ...] = (),
    error_messages: tuple[str, ...] = (),
    revalidation_triggers: tuple[CompatibilityRevalidationTrigger, ...] = (),
) -> ParserCompatibilityOutcome:
    return ParserCompatibilityOutcome(
        outcome_id=outcome_id,
        compatibility_profile=profile,
        lifecycle_status=lifecycle_status,
        change_class=change_class,
        status=status,
        warnings=warnings,
        error_messages=error_messages,
        revalidation_triggers=revalidation_triggers,
        evidence_references=(
            ParserEvidenceReference(
                reference_id=f"fx::{evidence_suffix}::compatibility",
                evidence_kind="compatibility-outcome",
                reference_status=_reference_status_from_lifecycle_status(lifecycle_status),
                lifecycle_status=lifecycle_status,
                notes=(f"synthetic compatibility outcome {outcome_id}",),
            ),
        ),
        explanation=ParserOutcomeExplanation(
            summary="synthetic compatibility revalidation",
            reason_code=f"FX::{evidence_suffix}",
            status=lifecycle_status,
            warnings=warnings,
        ),
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

_PROFILE_CURRENT_REFERENCE = _profile(
    "fx-apa03-profile-current-reference",
    evidence_suffix="apa03-current-reference",
    supported_extraction_claims=(
        "tier-1 semantic claims",
        "current clean-empty proof only when explicitly evidenced",
    ),
    unsupported_extraction_claims=(
        "official/public contract",
        "internal endpoint stability",
    ),
    required_fields=("profile_id", "semantic_version", "reference_ids"),
    completeness_rules=(
        "current profile requires explicit evidence metadata",
        "clean empty remains blocked without current proof",
    ),
    warning_mappings=(
        "REFERENCE_CHANGED->COMPATIBILITY_REVALIDATION_REQUIRED",
        "REFERENCE_DISPUTED->DISPUTED_PROFILE_WARNING",
    ),
    error_mappings=(
        "REFERENCE_WITHDRAWN->WITHDRAWN_PROFILE_BLOCKED",
        "REFERENCE_UNAVAILABLE->UNAVAILABLE_PROFILE_WARNING",
    ),
    fixture_ids=("FX-APA03-CURRENT-REFERENCE-PROFILE-001",),
    acceptance_matrix_rows=("APA03::CURRENT::TIER1::ACCEPT",),
)
_PROFILE_STALE_REFERENCE = _profile(
    "fx-apa03-profile-stale-reference",
    lifecycle_status=CompatibilityProfileLifecycleStatus.STALE,
    reference_status=ReferenceOutcomeStatus.REFERENCE_STALE,
    evidence_suffix="apa03-stale-reference",
    supported_extraction_claims=(
        "stale profile blocks clean empty without current proof",
    ),
    unsupported_extraction_claims=(
        "clean empty current proof",
    ),
    required_fields=("profile_id", "semantic_version", "reference_ids"),
    completeness_rules=("stale profiles cannot be treated as current",),
    warning_mappings=("REFERENCE_CHANGED->STALE_PROFILE_BLOCKED",),
    error_mappings=("REFERENCE_STALE->BLOCK_CURRENT_ACCEPTANCE",),
    fixture_ids=("FX-APA03-STALE-REFERENCE-PROFILE-BLOCKS-CLEAN-EMPTY-001",),
    acceptance_matrix_rows=("APA03::STALE::EMPTY::BLOCK",),
)
_PROFILE_DISPUTED_REFERENCE = _profile(
    "fx-apa03-profile-disputed-reference",
    lifecycle_status=CompatibilityProfileLifecycleStatus.DISPUTED,
    reference_status=ReferenceOutcomeStatus.REFERENCE_DISPUTED,
    evidence_suffix="apa03-disputed-reference",
    supported_extraction_claims=("disputed evidence stays warning-only",),
    unsupported_extraction_claims=("current acceptance",),
    required_fields=("profile_id", "semantic_version", "reference_ids"),
    completeness_rules=("disputed evidence cannot become current",),
    warning_mappings=("REFERENCE_DISPUTED->DISPUTED_PROFILE_WARNING",),
    error_mappings=("REFERENCE_DISPUTED->DISPUTED_PROFILE_WARNING",),
    fixture_ids=("FX-APA03-DISPUTED-REFERENCE-PROFILE-WARNING-001",),
    acceptance_matrix_rows=("APA03::DISPUTED::WARN",),
)
_PROFILE_SUPERSEDED_REFERENCE = _profile(
    "fx-apa03-profile-superseded-reference",
    lifecycle_status=CompatibilityProfileLifecycleStatus.SUPERSEDED,
    reference_status=ReferenceOutcomeStatus.REFERENCE_STALE,
    evidence_suffix="apa03-superseded-reference",
    supported_extraction_claims=("superseded evidence is revalidation-only",),
    unsupported_extraction_claims=("current acceptance",),
    required_fields=("profile_id", "semantic_version", "reference_ids"),
    completeness_rules=("superseded evidence requires replacement profile",),
    warning_mappings=("REFERENCE_SUPERSEDED->COMPATIBILITY_REVALIDATION_REQUIRED",),
    error_mappings=("REFERENCE_SUPERSEDED->BREAK_CURRENT_ACCEPTANCE",),
    fixture_ids=("FX-APA03-SUPERSEDED-REFERENCE-PROFILE-001",),
    acceptance_matrix_rows=("APA03::SUPERSEDED::REVALIDATE",),
)
_PROFILE_WITHDRAWN_REFERENCE = _profile(
    "fx-apa03-profile-withdrawn-reference",
    lifecycle_status=CompatibilityProfileLifecycleStatus.WITHDRAWN,
    reference_status=ReferenceOutcomeStatus.REFERENCE_MISSING,
    evidence_suffix="apa03-withdrawn-reference",
    supported_extraction_claims=("withdrawn evidence blocks success",),
    unsupported_extraction_claims=("parser success",),
    required_fields=("profile_id", "semantic_version", "reference_ids"),
    completeness_rules=("withdrawn evidence cannot be accepted as current",),
    warning_mappings=("REFERENCE_WITHDRAWN->WITHDRAWN_PROFILE_BLOCKED",),
    error_mappings=("REFERENCE_WITHDRAWN->WITHDRAWN_PROFILE_BLOCKED",),
    fixture_ids=("FX-APA03-WITHDRAWN-REFERENCE-PROFILE-BLOCKS-SUCCESS-001",),
    acceptance_matrix_rows=("APA03::WITHDRAWN::BLOCK",),
)
_PROFILE_UNAVAILABLE_REFERENCE = _profile(
    "fx-apa03-profile-unavailable-reference",
    lifecycle_status=CompatibilityProfileLifecycleStatus.UNAVAILABLE,
    reference_status=ReferenceOutcomeStatus.REFERENCE_MISSING,
    evidence_suffix="apa03-unavailable-reference",
    supported_extraction_claims=("unavailable evidence remains unavailable",),
    unsupported_extraction_claims=("current acceptance",),
    required_fields=("profile_id", "semantic_version", "reference_ids"),
    completeness_rules=("unavailable evidence cannot be treated as current",),
    warning_mappings=("REFERENCE_UNAVAILABLE->UNAVAILABLE_PROFILE_WARNING",),
    error_mappings=("REFERENCE_UNAVAILABLE->UNAVAILABLE_PROFILE_WARNING",),
    fixture_ids=("FX-APA03-UNAVAILABLE-REFERENCE-PROFILE-001",),
    acceptance_matrix_rows=("APA03::UNAVAILABLE::BLOCK",),
)
_PROFILE_UNSUPPORTED_CLAIM = _profile(
    "fx-apa03-profile-unsupported-claim",
    evidence_suffix="apa03-unsupported-claim",
    supported_extraction_claims=("search configuration extraction only",),
    unsupported_extraction_claims=("phone extraction", "listing-detail enrichment"),
    required_fields=("profile_id", "semantic_version", "reference_ids"),
    completeness_rules=("unsupported claims remain unavailable",),
    warning_mappings=("UNSUPPORTED_EXTRACTION_CLAIM->UNAVAILABLE",),
    error_mappings=("UNSUPPORTED_EXTRACTION_CLAIM->UNAVAILABLE",),
    fixture_ids=("FX-APA03-UNSUPPORTED-EXTRACTION-CLAIM-001",),
    acceptance_matrix_rows=("APA03::CLAIM::UNSUPPORTED",),
)
_PROFILE_CHANGED_REFERENCE = _profile(
    "fx-apa03-profile-changed-reference",
    evidence_suffix="apa03-changed-reference",
    supported_extraction_claims=("reference change triggers revalidation",),
    unsupported_extraction_claims=("stable acceptance without revalidation",),
    required_fields=("profile_id", "semantic_version", "reference_ids"),
    completeness_rules=("changed references must revalidate before acceptance",),
    warning_mappings=("REFERENCE_CHANGED->COMPATIBILITY_REVALIDATION_REQUIRED",),
    error_mappings=("REFERENCE_CHANGED->COMPATIBILITY_REVALIDATION_REQUIRED",),
    fixture_ids=("FX-APA03-REFERENCE-COMMIT-REVALIDATION-001",),
    acceptance_matrix_rows=("APA03::REFERENCE_CHANGED::REVALIDATE",),
    revalidation_triggers=(CompatibilityRevalidationTrigger.REFERENCE_CHANGED,),
)
_PROFILE_INTERNAL_OBSERVATION = _profile(
    "fx-apa03-profile-internal-observation",
    authority_class=CompatibilityProfileAuthorityClass.OBSERVATION_ONLY,
    evidence_suffix="apa03-internal-observation",
    supported_extraction_claims=("internal endpoint observation only",),
    unsupported_extraction_claims=("official/public contract", "stable provider contract"),
    required_fields=("profile_id", "semantic_version", "reference_ids"),
    completeness_rules=("observation-only evidence cannot become the official contract",),
    warning_mappings=("INTERNAL_ENDPOINT_OBSERVATION_ONLY->OBSERVATION_ONLY",),
    error_mappings=("INTERNAL_ENDPOINT_OBSERVATION_ONLY->NOT_STABLE_CONTRACT",),
    fixture_ids=("FX-APA03-INTERNAL-ENDPOINT-OBSERVATION-NOT-STABLE-001",),
    acceptance_matrix_rows=("APA03::OBSERVATION::NOT_STABLE",),
)

_PROFILE_SOURCE_BOUNDARY = _profile(
    "fx-apa04-profile-source-boundary",
    evidence_suffix="apa04-source-boundary",
    supported_extraction_claims=(
        "Beacon-owned source reference is carried as bounded metadata",
        "malformed and unsupported source boundaries remain explicit",
    ),
    unsupported_extraction_claims=(
        "live URL open",
        "redirect following",
        "DNS probing",
        "canonicalization guessing",
        "shell target interpolation",
        "filesystem target interpolation",
        "network target interpolation",
    ),
    required_fields=("profile_id", "semantic_version", "reference_ids"),
    completeness_rules=(
        "source boundary decisions remain explicit",
        "parser output must not overwrite Beacon source URL",
    ),
    warning_mappings=(
        "SOURCE_URL_UNTRUSTED->SOURCE_URL_UNTRUSTED",
        "SOURCE_URL_POLICY_MISSING->SOURCE_URL_POLICY_MISSING",
        "SOURCE_URL_MALFORMED->SOURCE_URL_MALFORMED",
        "SOURCE_URL_UNSUPPORTED->SOURCE_URL_UNSUPPORTED",
        "SOURCE_URL_CANONICALIZATION_UNPROVEN->SOURCE_URL_CANONICALIZATION_UNPROVEN",
        "SOURCE_URL_REDIRECT_POLICY_BLOCKED->SOURCE_URL_REDIRECT_POLICY_BLOCKED",
        "SOURCE_URL_DNS_POLICY_BLOCKED->SOURCE_URL_DNS_POLICY_BLOCKED",
        "SOURCE_VALUE_SHELL_TARGET_BLOCKED->SOURCE_VALUE_SHELL_TARGET_BLOCKED",
        "SOURCE_VALUE_FILESYSTEM_TARGET_BLOCKED->SOURCE_VALUE_FILESYSTEM_TARGET_BLOCKED",
        "SOURCE_VALUE_NETWORK_TARGET_BLOCKED->SOURCE_VALUE_NETWORK_TARGET_BLOCKED",
    ),
    error_mappings=(
        "SOURCE_URL_MALFORMED->MALFORMED",
        "SOURCE_URL_UNSUPPORTED->UNSUPPORTED",
        "SOURCE_URL_POLICY_MISSING->POLICY_MISSING",
    ),
    fixture_ids=(
        "FX-APA04-SOURCE-REFERENCE-BOUNDED-INPUT-ACCEPTED-001",
        "FX-APA04-SOURCE-BOUNDARY-MALFORMED-REJECTED-001",
        "FX-APA04-SOURCE-BOUNDARY-UNSUPPORTED-BLOCKED-001",
        "FX-APA04-SOURCE-BOUNDARY-POLICY-MISSING-001",
        "FX-APA04-SOURCE-BOUNDARY-REDIRECT-POLICY-MISSING-001",
        "FX-APA04-SOURCE-BOUNDARY-DNS-POLICY-MISSING-001",
        "FX-APA04-SOURCE-BOUNDARY-CANONICALIZATION-UNPROVEN-001",
        "FX-APA04-SOURCE-BOUNDARY-SHELL-TARGET-BLOCKED-001",
        "FX-APA04-SOURCE-BOUNDARY-FILESYSTEM-TARGET-BLOCKED-001",
        "FX-APA04-SOURCE-BOUNDARY-NETWORK-TARGET-BLOCKED-001",
        "FX-APA04-SOURCE-BOUNDARY-PARSER-OUTPUT-PRESERVES-BEACON-SOURCE-001",
    ),
    acceptance_matrix_rows=(
        "APA04::SOURCE::ACCEPT",
        "APA04::SOURCE::MALFORMED",
        "APA04::SOURCE::UNSUPPORTED",
        "APA04::SOURCE::POLICY_MISSING",
        "APA04::SOURCE::REDIRECT_POLICY_MISSING",
        "APA04::SOURCE::DNS_POLICY_MISSING",
        "APA04::SOURCE::CANONICALIZATION_UNPROVEN",
        "APA04::SOURCE::SHELL_TARGET_BLOCKED",
        "APA04::SOURCE::FILESYSTEM_TARGET_BLOCKED",
        "APA04::SOURCE::NETWORK_TARGET_BLOCKED",
        "APA04::SOURCE::OUTPUT_PRESERVED",
    ),
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

_REQUEST_CURRENT_REFERENCE = _request(
    "fx-apa03-request-current-reference",
    _PROFILE_CURRENT_REFERENCE,
    purpose="page-parse",
    safe_source_reference="source::current-reference",
    requested_page_numbers=(1,),
)
_REQUEST_STALE_REFERENCE = _request(
    "fx-apa03-request-stale-reference",
    _PROFILE_STALE_REFERENCE,
    purpose="page-parse",
    safe_source_reference="source::stale-reference",
    requested_page_numbers=(1,),
)
_REQUEST_DISPUTED_REFERENCE = _request(
    "fx-apa03-request-disputed-reference",
    _PROFILE_DISPUTED_REFERENCE,
    purpose="source-analysis",
    safe_source_reference="source::disputed-reference",
)
_REQUEST_SUPERSEDED_REFERENCE = _request(
    "fx-apa03-request-superseded-reference",
    _PROFILE_SUPERSEDED_REFERENCE,
    purpose="source-analysis",
    safe_source_reference="source::superseded-reference",
)
_REQUEST_WITHDRAWN_REFERENCE = _request(
    "fx-apa03-request-withdrawn-reference",
    _PROFILE_WITHDRAWN_REFERENCE,
    purpose="page-parse",
    safe_source_reference="source::withdrawn-reference",
    requested_page_numbers=(1,),
)
_REQUEST_UNAVAILABLE_REFERENCE = _request(
    "fx-apa03-request-unavailable-reference",
    _PROFILE_UNAVAILABLE_REFERENCE,
    purpose="source-analysis",
    safe_source_reference="source::unavailable-reference",
)
_REQUEST_UNSUPPORTED_CLAIM = _request(
    "fx-apa03-request-unsupported-claim",
    _PROFILE_UNSUPPORTED_CLAIM,
    purpose="configuration-extraction",
    safe_source_reference="source::unsupported-claim",
)
_REQUEST_CHANGED_REFERENCE = _request(
    "fx-apa03-request-changed-reference",
    _PROFILE_CHANGED_REFERENCE,
    purpose="page-parse",
    safe_source_reference="source::changed-reference",
    requested_page_numbers=(1,),
)
_REQUEST_INTERNAL_OBSERVATION = _request(
    "fx-apa03-request-internal-observation",
    _PROFILE_INTERNAL_OBSERVATION,
    purpose="source-analysis",
    safe_source_reference="source::internal-observation",
)

_TRANSPORT_CURRENT_REFERENCE = _transport(
    "fx-apa03-transport-current-reference",
    status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
    request_reference=_REQUEST_CURRENT_REFERENCE.request_id,
    response_reference="response::current-reference",
    route_reference="route::synthetic",
    evidence_reference_suffix="apa03-current-reference",
)
_TRANSPORT_STALE_REFERENCE = _transport(
    "fx-apa03-transport-stale-reference",
    status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
    request_reference=_REQUEST_STALE_REFERENCE.request_id,
    response_reference="response::stale-reference",
    route_reference="route::synthetic",
    evidence_reference_suffix="apa03-stale-reference",
)
_TRANSPORT_DISPUTED_REFERENCE = _transport(
    "fx-apa03-transport-disputed-reference",
    status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
    request_reference=_REQUEST_DISPUTED_REFERENCE.request_id,
    response_reference="response::disputed-reference",
    route_reference="route::synthetic",
    evidence_reference_suffix="apa03-disputed-reference",
)
_TRANSPORT_SUPERSEDED_REFERENCE = _transport(
    "fx-apa03-transport-superseded-reference",
    status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
    request_reference=_REQUEST_SUPERSEDED_REFERENCE.request_id,
    response_reference="response::superseded-reference",
    route_reference="route::synthetic",
    evidence_reference_suffix="apa03-superseded-reference",
)
_TRANSPORT_WITHDRAWN_REFERENCE = _transport(
    "fx-apa03-transport-withdrawn-reference",
    status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
    request_reference=_REQUEST_WITHDRAWN_REFERENCE.request_id,
    response_reference="response::withdrawn-reference",
    route_reference="route::synthetic",
    evidence_reference_suffix="apa03-withdrawn-reference",
)
_TRANSPORT_UNAVAILABLE_REFERENCE = _transport(
    "fx-apa03-transport-unavailable-reference",
    status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
    request_reference=_REQUEST_UNAVAILABLE_REFERENCE.request_id,
    response_reference="response::unavailable-reference",
    route_reference="route::synthetic",
    evidence_reference_suffix="apa03-unavailable-reference",
)
_TRANSPORT_UNSUPPORTED_CLAIM = _transport(
    "fx-apa03-transport-unsupported-claim",
    status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
    request_reference=_REQUEST_UNSUPPORTED_CLAIM.request_id,
    response_reference="response::unsupported-claim",
    route_reference="route::synthetic",
    evidence_reference_suffix="apa03-unsupported-claim",
)
_TRANSPORT_CHANGED_REFERENCE = _transport(
    "fx-apa03-transport-changed-reference",
    status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
    request_reference=_REQUEST_CHANGED_REFERENCE.request_id,
    response_reference="response::changed-reference",
    route_reference="route::synthetic",
    evidence_reference_suffix="apa03-changed-reference",
)
_TRANSPORT_INTERNAL_OBSERVATION = _transport(
    "fx-apa03-transport-internal-observation",
    status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
    request_reference=_REQUEST_INTERNAL_OBSERVATION.request_id,
    response_reference="response::internal-observation",
    route_reference="route::synthetic",
    evidence_reference_suffix="apa03-internal-observation",
)

_SOURCE_REFERENCE_ACCEPTED = _source_reference(
    "fx-apa04-source-reference-accepted",
    kind=SourceReferenceKind.BEACON_SUBMITTED_URL,
)
_SOURCE_REFERENCE_MALFORMED = _source_reference(
    "fx-apa04-source-reference-malformed",
    kind=SourceReferenceKind.BEACON_SUBMITTED_URL,
)
_SOURCE_REFERENCE_UNSUPPORTED = _source_reference(
    "fx-apa04-source-reference-unsupported",
    kind=SourceReferenceKind.BEACON_SUBMITTED_URL,
)
_SOURCE_REFERENCE_POLICY_MISSING = _source_reference(
    "fx-apa04-source-reference-policy-missing",
    kind=SourceReferenceKind.BEACON_SUBMITTED_URL,
)
_SOURCE_REFERENCE_REDIRECT = _source_reference(
    "fx-apa04-source-reference-redirect",
    kind=SourceReferenceKind.BEACON_SUBMITTED_URL,
)
_SOURCE_REFERENCE_DNS = _source_reference(
    "fx-apa04-source-reference-dns",
    kind=SourceReferenceKind.BEACON_SUBMITTED_URL,
)
_SOURCE_REFERENCE_CANONICALIZATION = _source_reference(
    "fx-apa04-source-reference-canonicalization",
    kind=SourceReferenceKind.BEACON_SUBMITTED_URL,
)
_SOURCE_REFERENCE_SHELL = _source_reference(
    "fx-apa04-source-reference-shell",
    kind=SourceReferenceKind.BEACON_SUBMITTED_URL,
    bounded_value="bounded-source-value",
)
_SOURCE_REFERENCE_FILESYSTEM = _source_reference(
    "fx-apa04-source-reference-filesystem",
    kind=SourceReferenceKind.BEACON_SUBMITTED_URL,
    bounded_value="bounded-source-value",
)
_SOURCE_REFERENCE_NETWORK = _source_reference(
    "fx-apa04-source-reference-network",
    kind=SourceReferenceKind.BEACON_SUBMITTED_URL,
    bounded_value="bounded-source-value",
)
_SOURCE_REFERENCE_PRESERVED = _source_reference(
    "fx-apa04-source-reference-preserved",
    kind=SourceReferenceKind.BEACON_PERSISTED_REFERENCE,
)

_BOUNDARY_ACCEPTED = _source_boundary(
    "fx-apa04-boundary-accepted",
    _SOURCE_REFERENCE_ACCEPTED,
    status=SourceBoundaryStatus.ACCEPTED,
    evidence_suffix="apa04-source-reference-accepted",
    policy_requirements=(
        SourceBoundaryPolicyRequirement.BEACON_OWNERSHIP_PRESERVED,
        SourceBoundaryPolicyRequirement.SAFE_REFERENCE_ONLY,
    ),
    risk_codes=(SourceBoundaryRiskCode.SOURCE_URL_UNTRUSTED,),
    warning_codes=(ParserWarningCode.SOURCE_URL_UNTRUSTED,),
    warning_message="Beacon-owned source reference is accepted only as bounded metadata",
)
_BOUNDARY_MALFORMED = _source_boundary(
    "fx-apa04-boundary-malformed",
    _SOURCE_REFERENCE_MALFORMED,
    status=SourceBoundaryStatus.MALFORMED,
    evidence_suffix="apa04-source-boundary-malformed",
    policy_requirements=(SourceBoundaryPolicyRequirement.SAFE_REFERENCE_ONLY,),
    risk_codes=(SourceBoundaryRiskCode.SOURCE_URL_MALFORMED,),
    warning_codes=(ParserWarningCode.SOURCE_URL_MALFORMED,),
    warning_message="malformed source boundary is rejected",
)
_BOUNDARY_UNSUPPORTED = _source_boundary(
    "fx-apa04-boundary-unsupported",
    _SOURCE_REFERENCE_UNSUPPORTED,
    status=SourceBoundaryStatus.UNSUPPORTED,
    evidence_suffix="apa04-source-boundary-unsupported",
    policy_requirements=(SourceBoundaryPolicyRequirement.SAFE_REFERENCE_ONLY,),
    risk_codes=(SourceBoundaryRiskCode.SOURCE_URL_UNSUPPORTED,),
    warning_codes=(ParserWarningCode.SOURCE_URL_UNSUPPORTED,),
    warning_message="unsupported source boundary is blocked",
)
_BOUNDARY_POLICY_MISSING = _source_boundary(
    "fx-apa04-boundary-policy-missing",
    _SOURCE_REFERENCE_POLICY_MISSING,
    status=SourceBoundaryStatus.POLICY_MISSING,
    evidence_suffix="apa04-source-boundary-policy-missing",
    policy_requirements=(SourceBoundaryPolicyRequirement.HOST_PATH_QUERY_POLICY,),
    risk_codes=(SourceBoundaryRiskCode.SOURCE_URL_POLICY_MISSING,),
    warning_codes=(ParserWarningCode.SOURCE_URL_POLICY_MISSING,),
    warning_message="host/path/query validation policy is missing",
)
_BOUNDARY_REDIRECT_POLICY_MISSING = _source_boundary(
    "fx-apa04-boundary-redirect-policy-missing",
    _SOURCE_REFERENCE_REDIRECT,
    status=SourceBoundaryStatus.POLICY_MISSING,
    evidence_suffix="apa04-source-boundary-redirect-policy-missing",
    policy_requirements=(SourceBoundaryPolicyRequirement.REDIRECT_POLICY,),
    risk_codes=(SourceBoundaryRiskCode.SOURCE_URL_REDIRECT_POLICY_BLOCKED,),
    warning_codes=(ParserWarningCode.SOURCE_URL_REDIRECT_POLICY_BLOCKED,),
    warning_message="redirect policy is missing so live follow stays blocked",
)
_BOUNDARY_DNS_POLICY_MISSING = _source_boundary(
    "fx-apa04-boundary-dns-policy-missing",
    _SOURCE_REFERENCE_DNS,
    status=SourceBoundaryStatus.POLICY_MISSING,
    evidence_suffix="apa04-source-boundary-dns-policy-missing",
    policy_requirements=(SourceBoundaryPolicyRequirement.DNS_POLICY,),
    risk_codes=(SourceBoundaryRiskCode.SOURCE_URL_DNS_POLICY_BLOCKED,),
    warning_codes=(ParserWarningCode.SOURCE_URL_DNS_POLICY_BLOCKED,),
    warning_message="DNS policy is missing so probing stays blocked",
)
_BOUNDARY_CANONICALIZATION_UNPROVEN = _source_boundary(
    "fx-apa04-boundary-canonicalization-unproven",
    _SOURCE_REFERENCE_CANONICALIZATION,
    status=SourceBoundaryStatus.UNPROVEN,
    evidence_suffix="apa04-source-boundary-canonicalization-unproven",
    policy_requirements=(SourceBoundaryPolicyRequirement.CANONICALIZATION_POLICY,),
    risk_codes=(SourceBoundaryRiskCode.SOURCE_URL_CANONICALIZATION_UNPROVEN,),
    warning_codes=(ParserWarningCode.SOURCE_URL_CANONICALIZATION_UNPROVEN,),
    warning_message="canonicalization/equivalence remains unproven",
)
_BOUNDARY_SHELL_BLOCKED = _source_boundary(
    "fx-apa04-boundary-shell-blocked",
    _SOURCE_REFERENCE_SHELL,
    status=SourceBoundaryStatus.BLOCKED,
    evidence_suffix="apa04-source-boundary-shell-blocked",
    policy_requirements=(SourceBoundaryPolicyRequirement.NO_SHELL_TARGETS,),
    risk_codes=(SourceBoundaryRiskCode.SOURCE_VALUE_SHELL_TARGET_BLOCKED,),
    warning_codes=(ParserWarningCode.SOURCE_VALUE_SHELL_TARGET_BLOCKED,),
    warning_message="shell interpolation target remains blocked",
)
_BOUNDARY_FILESYSTEM_BLOCKED = _source_boundary(
    "fx-apa04-boundary-filesystem-blocked",
    _SOURCE_REFERENCE_FILESYSTEM,
    status=SourceBoundaryStatus.BLOCKED,
    evidence_suffix="apa04-source-boundary-filesystem-blocked",
    policy_requirements=(SourceBoundaryPolicyRequirement.NO_FILESYSTEM_TARGETS,),
    risk_codes=(SourceBoundaryRiskCode.SOURCE_VALUE_FILESYSTEM_TARGET_BLOCKED,),
    warning_codes=(ParserWarningCode.SOURCE_VALUE_FILESYSTEM_TARGET_BLOCKED,),
    warning_message="filesystem target remains blocked",
)
_BOUNDARY_NETWORK_BLOCKED = _source_boundary(
    "fx-apa04-boundary-network-blocked",
    _SOURCE_REFERENCE_NETWORK,
    status=SourceBoundaryStatus.BLOCKED,
    evidence_suffix="apa04-source-boundary-network-blocked",
    policy_requirements=(SourceBoundaryPolicyRequirement.NO_NETWORK_TARGETS,),
    risk_codes=(SourceBoundaryRiskCode.SOURCE_VALUE_NETWORK_TARGET_BLOCKED,),
    warning_codes=(ParserWarningCode.SOURCE_VALUE_NETWORK_TARGET_BLOCKED,),
    warning_message="arbitrary network target remains blocked",
)
_BOUNDARY_OUTPUT_PRESERVED = _source_boundary(
    "fx-apa04-boundary-output-preserved",
    _SOURCE_REFERENCE_PRESERVED,
    status=SourceBoundaryStatus.ACCEPTED,
    evidence_suffix="apa04-source-boundary-output-preserved",
    policy_requirements=(
        SourceBoundaryPolicyRequirement.BEACON_OWNERSHIP_PRESERVED,
        SourceBoundaryPolicyRequirement.SAFE_REFERENCE_ONLY,
    ),
    risk_codes=(SourceBoundaryRiskCode.SOURCE_URL_UNTRUSTED,),
    warning_codes=(ParserWarningCode.SOURCE_URL_UNTRUSTED,),
    warning_message="parser output preserves Beacon source URL ownership",
)

_REQUEST_SOURCE_BOUNDARY_ACCEPTED = _request(
    "fx-apa04-request-source-boundary-accepted",
    _PROFILE_SOURCE_BOUNDARY,
    purpose="source-boundary-analysis",
    safe_source_reference=_SOURCE_REFERENCE_ACCEPTED.bounded_value,
    source_reference=_SOURCE_REFERENCE_ACCEPTED,
    source_boundary_outcome=_BOUNDARY_ACCEPTED,
)
_REQUEST_SOURCE_BOUNDARY_MALFORMED = _request(
    "fx-apa04-request-source-boundary-malformed",
    _PROFILE_SOURCE_BOUNDARY,
    purpose="source-boundary-analysis",
    safe_source_reference=_SOURCE_REFERENCE_MALFORMED.bounded_value,
    source_reference=_SOURCE_REFERENCE_MALFORMED,
    source_boundary_outcome=_BOUNDARY_MALFORMED,
)
_REQUEST_SOURCE_BOUNDARY_UNSUPPORTED = _request(
    "fx-apa04-request-source-boundary-unsupported",
    _PROFILE_SOURCE_BOUNDARY,
    purpose="source-boundary-analysis",
    safe_source_reference=_SOURCE_REFERENCE_UNSUPPORTED.bounded_value,
    source_reference=_SOURCE_REFERENCE_UNSUPPORTED,
    source_boundary_outcome=_BOUNDARY_UNSUPPORTED,
)
_REQUEST_SOURCE_BOUNDARY_POLICY_MISSING = _request(
    "fx-apa04-request-source-boundary-policy-missing",
    _PROFILE_SOURCE_BOUNDARY,
    purpose="source-boundary-analysis",
    safe_source_reference=_SOURCE_REFERENCE_POLICY_MISSING.bounded_value,
    source_reference=_SOURCE_REFERENCE_POLICY_MISSING,
    source_boundary_outcome=_BOUNDARY_POLICY_MISSING,
)
_REQUEST_SOURCE_BOUNDARY_REDIRECT = _request(
    "fx-apa04-request-source-boundary-redirect",
    _PROFILE_SOURCE_BOUNDARY,
    purpose="source-boundary-analysis",
    safe_source_reference=_SOURCE_REFERENCE_REDIRECT.bounded_value,
    source_reference=_SOURCE_REFERENCE_REDIRECT,
    source_boundary_outcome=_BOUNDARY_REDIRECT_POLICY_MISSING,
)
_REQUEST_SOURCE_BOUNDARY_DNS = _request(
    "fx-apa04-request-source-boundary-dns",
    _PROFILE_SOURCE_BOUNDARY,
    purpose="source-boundary-analysis",
    safe_source_reference=_SOURCE_REFERENCE_DNS.bounded_value,
    source_reference=_SOURCE_REFERENCE_DNS,
    source_boundary_outcome=_BOUNDARY_DNS_POLICY_MISSING,
)
_REQUEST_SOURCE_BOUNDARY_CANONICALIZATION = _request(
    "fx-apa04-request-source-boundary-canonicalization",
    _PROFILE_SOURCE_BOUNDARY,
    purpose="source-boundary-analysis",
    safe_source_reference=_SOURCE_REFERENCE_CANONICALIZATION.bounded_value,
    source_reference=_SOURCE_REFERENCE_CANONICALIZATION,
    source_boundary_outcome=_BOUNDARY_CANONICALIZATION_UNPROVEN,
)
_REQUEST_SOURCE_BOUNDARY_SHELL = _request(
    "fx-apa04-request-source-boundary-shell",
    _PROFILE_SOURCE_BOUNDARY,
    purpose="source-boundary-analysis",
    safe_source_reference=_SOURCE_REFERENCE_SHELL.bounded_value,
    source_reference=_SOURCE_REFERENCE_SHELL,
    source_boundary_outcome=_BOUNDARY_SHELL_BLOCKED,
)
_REQUEST_SOURCE_BOUNDARY_FILESYSTEM = _request(
    "fx-apa04-request-source-boundary-filesystem",
    _PROFILE_SOURCE_BOUNDARY,
    purpose="source-boundary-analysis",
    safe_source_reference=_SOURCE_REFERENCE_FILESYSTEM.bounded_value,
    source_reference=_SOURCE_REFERENCE_FILESYSTEM,
    source_boundary_outcome=_BOUNDARY_FILESYSTEM_BLOCKED,
)
_REQUEST_SOURCE_BOUNDARY_NETWORK = _request(
    "fx-apa04-request-source-boundary-network",
    _PROFILE_SOURCE_BOUNDARY,
    purpose="source-boundary-analysis",
    safe_source_reference=_SOURCE_REFERENCE_NETWORK.bounded_value,
    source_reference=_SOURCE_REFERENCE_NETWORK,
    source_boundary_outcome=_BOUNDARY_NETWORK_BLOCKED,
)
_REQUEST_SOURCE_BOUNDARY_PRESERVED = _request(
    "fx-apa04-request-source-boundary-preserved",
    _PROFILE_SOURCE_BOUNDARY,
    purpose="source-boundary-analysis",
    safe_source_reference=_SOURCE_REFERENCE_PRESERVED.bounded_value,
    source_reference=_SOURCE_REFERENCE_PRESERVED,
    source_boundary_outcome=_BOUNDARY_OUTPUT_PRESERVED,
)

_TRANSPORT_SOURCE_BOUNDARY_ACCEPTED = _transport(
    "fx-apa04-transport-source-boundary-accepted",
    status=TransportOutcomeStatus.NOT_SENT,
    request_reference=_REQUEST_SOURCE_BOUNDARY_ACCEPTED.request_id,
    response_reference=None,
    route_reference=None,
    evidence_reference_suffix="apa04-source-boundary-accepted",
)
_TRANSPORT_SOURCE_BOUNDARY_MALFORMED = _transport(
    "fx-apa04-transport-source-boundary-malformed",
    status=TransportOutcomeStatus.NOT_SENT,
    request_reference=_REQUEST_SOURCE_BOUNDARY_MALFORMED.request_id,
    response_reference=None,
    route_reference=None,
    evidence_reference_suffix="apa04-source-boundary-malformed",
)
_TRANSPORT_SOURCE_BOUNDARY_UNSUPPORTED = _transport(
    "fx-apa04-transport-source-boundary-unsupported",
    status=TransportOutcomeStatus.NOT_SENT,
    request_reference=_REQUEST_SOURCE_BOUNDARY_UNSUPPORTED.request_id,
    response_reference=None,
    route_reference=None,
    evidence_reference_suffix="apa04-source-boundary-unsupported",
)
_TRANSPORT_SOURCE_BOUNDARY_POLICY_MISSING = _transport(
    "fx-apa04-transport-source-boundary-policy-missing",
    status=TransportOutcomeStatus.NOT_SENT,
    request_reference=_REQUEST_SOURCE_BOUNDARY_POLICY_MISSING.request_id,
    response_reference=None,
    route_reference=None,
    evidence_reference_suffix="apa04-source-boundary-policy-missing",
)
_TRANSPORT_SOURCE_BOUNDARY_REDIRECT = _transport(
    "fx-apa04-transport-source-boundary-redirect",
    status=TransportOutcomeStatus.NOT_SENT,
    request_reference=_REQUEST_SOURCE_BOUNDARY_REDIRECT.request_id,
    response_reference=None,
    route_reference=None,
    evidence_reference_suffix="apa04-source-boundary-redirect",
)
_TRANSPORT_SOURCE_BOUNDARY_DNS = _transport(
    "fx-apa04-transport-source-boundary-dns",
    status=TransportOutcomeStatus.NOT_SENT,
    request_reference=_REQUEST_SOURCE_BOUNDARY_DNS.request_id,
    response_reference=None,
    route_reference=None,
    evidence_reference_suffix="apa04-source-boundary-dns",
)
_TRANSPORT_SOURCE_BOUNDARY_CANONICALIZATION = _transport(
    "fx-apa04-transport-source-boundary-canonicalization",
    status=TransportOutcomeStatus.NOT_SENT,
    request_reference=_REQUEST_SOURCE_BOUNDARY_CANONICALIZATION.request_id,
    response_reference=None,
    route_reference=None,
    evidence_reference_suffix="apa04-source-boundary-canonicalization",
)
_TRANSPORT_SOURCE_BOUNDARY_SHELL = _transport(
    "fx-apa04-transport-source-boundary-shell",
    status=TransportOutcomeStatus.NOT_SENT,
    request_reference=_REQUEST_SOURCE_BOUNDARY_SHELL.request_id,
    response_reference=None,
    route_reference=None,
    evidence_reference_suffix="apa04-source-boundary-shell",
)
_TRANSPORT_SOURCE_BOUNDARY_FILESYSTEM = _transport(
    "fx-apa04-transport-source-boundary-filesystem",
    status=TransportOutcomeStatus.NOT_SENT,
    request_reference=_REQUEST_SOURCE_BOUNDARY_FILESYSTEM.request_id,
    response_reference=None,
    route_reference=None,
    evidence_reference_suffix="apa04-source-boundary-filesystem",
)
_TRANSPORT_SOURCE_BOUNDARY_NETWORK = _transport(
    "fx-apa04-transport-source-boundary-network",
    status=TransportOutcomeStatus.NOT_SENT,
    request_reference=_REQUEST_SOURCE_BOUNDARY_NETWORK.request_id,
    response_reference=None,
    route_reference=None,
    evidence_reference_suffix="apa04-source-boundary-network",
)
_TRANSPORT_SOURCE_BOUNDARY_PRESERVED = _transport(
    "fx-apa04-transport-source-boundary-preserved",
    status=TransportOutcomeStatus.NOT_SENT,
    request_reference=_REQUEST_SOURCE_BOUNDARY_PRESERVED.request_id,
    response_reference=None,
    route_reference=None,
    evidence_reference_suffix="apa04-source-boundary-preserved",
)

_ATTEMPT_SOURCE_BOUNDARY_ACCEPTED = _source_boundary_attempt(
    "fx-apa04-attempt-source-boundary-accepted",
    _REQUEST_SOURCE_BOUNDARY_ACCEPTED,
    parser_status=ParserOutcomeStatus.USABLE_RESPONSE,
    evidence_suffix="apa04-source-boundary-accepted",
    warnings=_BOUNDARY_ACCEPTED.warnings,
)
_ATTEMPT_SOURCE_BOUNDARY_MALFORMED = _source_boundary_attempt(
    "fx-apa04-attempt-source-boundary-malformed",
    _REQUEST_SOURCE_BOUNDARY_MALFORMED,
    parser_status=ParserOutcomeStatus.MALFORMED_RESPONSE,
    evidence_suffix="apa04-source-boundary-malformed",
    warnings=_BOUNDARY_MALFORMED.warnings,
)
_ATTEMPT_SOURCE_BOUNDARY_UNSUPPORTED = _source_boundary_attempt(
    "fx-apa04-attempt-source-boundary-unsupported",
    _REQUEST_SOURCE_BOUNDARY_UNSUPPORTED,
    parser_status=ParserOutcomeStatus.UNSUPPORTED_STRUCTURE,
    evidence_suffix="apa04-source-boundary-unsupported",
    warnings=_BOUNDARY_UNSUPPORTED.warnings,
)
_ATTEMPT_SOURCE_BOUNDARY_POLICY_MISSING = _source_boundary_attempt(
    "fx-apa04-attempt-source-boundary-policy-missing",
    _REQUEST_SOURCE_BOUNDARY_POLICY_MISSING,
    parser_status=ParserOutcomeStatus.EXPLICIT_REJECTION,
    evidence_suffix="apa04-source-boundary-policy-missing",
    warnings=_BOUNDARY_POLICY_MISSING.warnings,
)
_ATTEMPT_SOURCE_BOUNDARY_REDIRECT = _source_boundary_attempt(
    "fx-apa04-attempt-source-boundary-redirect",
    _REQUEST_SOURCE_BOUNDARY_REDIRECT,
    parser_status=ParserOutcomeStatus.EXPLICIT_REJECTION,
    evidence_suffix="apa04-source-boundary-redirect",
    warnings=_BOUNDARY_REDIRECT_POLICY_MISSING.warnings,
)
_ATTEMPT_SOURCE_BOUNDARY_DNS = _source_boundary_attempt(
    "fx-apa04-attempt-source-boundary-dns",
    _REQUEST_SOURCE_BOUNDARY_DNS,
    parser_status=ParserOutcomeStatus.EXPLICIT_REJECTION,
    evidence_suffix="apa04-source-boundary-dns",
    warnings=_BOUNDARY_DNS_POLICY_MISSING.warnings,
)
_ATTEMPT_SOURCE_BOUNDARY_CANONICALIZATION = _source_boundary_attempt(
    "fx-apa04-attempt-source-boundary-canonicalization",
    _REQUEST_SOURCE_BOUNDARY_CANONICALIZATION,
    parser_status=ParserOutcomeStatus.RESULT_AMBIGUOUS,
    evidence_suffix="apa04-source-boundary-canonicalization",
    warnings=_BOUNDARY_CANONICALIZATION_UNPROVEN.warnings,
)
_ATTEMPT_SOURCE_BOUNDARY_SHELL = _source_boundary_attempt(
    "fx-apa04-attempt-source-boundary-shell",
    _REQUEST_SOURCE_BOUNDARY_SHELL,
    parser_status=ParserOutcomeStatus.EXPLICIT_REJECTION,
    evidence_suffix="apa04-source-boundary-shell",
    warnings=_BOUNDARY_SHELL_BLOCKED.warnings,
)
_ATTEMPT_SOURCE_BOUNDARY_FILESYSTEM = _source_boundary_attempt(
    "fx-apa04-attempt-source-boundary-filesystem",
    _REQUEST_SOURCE_BOUNDARY_FILESYSTEM,
    parser_status=ParserOutcomeStatus.EXPLICIT_REJECTION,
    evidence_suffix="apa04-source-boundary-filesystem",
    warnings=_BOUNDARY_FILESYSTEM_BLOCKED.warnings,
)
_ATTEMPT_SOURCE_BOUNDARY_NETWORK = _source_boundary_attempt(
    "fx-apa04-attempt-source-boundary-network",
    _REQUEST_SOURCE_BOUNDARY_NETWORK,
    parser_status=ParserOutcomeStatus.EXPLICIT_REJECTION,
    evidence_suffix="apa04-source-boundary-network",
    warnings=_BOUNDARY_NETWORK_BLOCKED.warnings,
)
_ATTEMPT_SOURCE_BOUNDARY_PRESERVED = _source_boundary_attempt(
    "fx-apa04-attempt-source-boundary-preserved",
    _REQUEST_SOURCE_BOUNDARY_PRESERVED,
    parser_status=ParserOutcomeStatus.USABLE_RESPONSE,
    evidence_suffix="apa04-source-boundary-preserved",
    warnings=_BOUNDARY_OUTPUT_PRESERVED.warnings,
)

_CARD_TIER1 = _usable_listing_card("fx-apa02-card-tier1", evidence_suffix="tier1")
_CARD_CURRENT_REFERENCE = _usable_listing_card(
    "fx-apa03-card-current-reference",
    evidence_suffix="apa03-current-reference",
)
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
_LISTING_CURRENT_REFERENCE = _listing_candidate(
    "fx-apa03-listing-current-reference",
    _CARD_CURRENT_REFERENCE,
    evidence_suffix="apa03-current-reference",
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

_PAGE_STALE_BLOCKED = _listing_page(
    "fx-apa03-page-stale-blocked",
    _REQUEST_STALE_REFERENCE,
    _TRANSPORT_STALE_REFERENCE,
    _PROFILE_STALE_REFERENCE,
    status=CompatibilityProfileLifecycleStatus.STALE,
    evidence_suffix="apa03-stale-reference",
    warnings=(
        ParserWarning(
            code=ParserWarningCode.STALE_PROFILE_BLOCKED,
            message="stale compatibility profile blocks clean empty",
        ),
    ),
)
_PAGE_WITHDRAWN_BLOCKED = _listing_page(
    "fx-apa03-page-withdrawn-blocked",
    _REQUEST_WITHDRAWN_REFERENCE,
    _TRANSPORT_WITHDRAWN_REFERENCE,
    _PROFILE_WITHDRAWN_REFERENCE,
    status=CompatibilityProfileLifecycleStatus.WITHDRAWN,
    evidence_suffix="apa03-withdrawn-reference",
    warnings=(
        ParserWarning(
            code=ParserWarningCode.WITHDRAWN_PROFILE_BLOCKED,
            message="withdrawn compatibility profile blocks parser success",
        ),
    ),
)
_PAGE_CURRENT_REFERENCE = _listing_page(
    "fx-apa03-page-current-reference",
    _REQUEST_CURRENT_REFERENCE,
    _TRANSPORT_CURRENT_REFERENCE,
    _PROFILE_CURRENT_REFERENCE,
    status=ParserOutcomeStatus.USABLE_RESPONSE,
    candidate=_LISTING_CURRENT_REFERENCE,
    card=_CARD_CURRENT_REFERENCE,
    evidence_suffix="apa03-current-reference",
)

_COMPATIBILITY_CURRENT_REFERENCE = _compatibility_outcome(
    "fx-apa03-compatibility-current-reference",
    _PROFILE_CURRENT_REFERENCE,
    lifecycle_status=CompatibilityProfileLifecycleStatus.CURRENT,
    change_class=CompatibilityChangeClass.COMPATIBLE,
    status=CompatibilityProfileLifecycleStatus.CURRENT,
    evidence_suffix="apa03-current-reference",
)
_COMPATIBILITY_STALE_REFERENCE = _compatibility_outcome(
    "fx-apa03-compatibility-stale-reference",
    _PROFILE_STALE_REFERENCE,
    lifecycle_status=CompatibilityProfileLifecycleStatus.STALE,
    change_class=CompatibilityChangeClass.BREAKING,
    status=CompatibilityProfileLifecycleStatus.STALE,
    evidence_suffix="apa03-stale-reference",
    warnings=(
        ParserWarning(
            code=ParserWarningCode.STALE_PROFILE_BLOCKED,
            message="stale compatibility profile cannot be treated as current",
        ),
    ),
    revalidation_triggers=(CompatibilityRevalidationTrigger.REFERENCE_CHANGED,),
)
_COMPATIBILITY_DISPUTED_REFERENCE = _compatibility_outcome(
    "fx-apa03-compatibility-disputed-reference",
    _PROFILE_DISPUTED_REFERENCE,
    lifecycle_status=CompatibilityProfileLifecycleStatus.DISPUTED,
    change_class=CompatibilityChangeClass.DISPUTED,
    status=CompatibilityProfileLifecycleStatus.DISPUTED,
    evidence_suffix="apa03-disputed-reference",
    warnings=(
        ParserWarning(
            code=ParserWarningCode.DISPUTED_PROFILE_WARNING,
            message="disputed profile returns warning-only outcome",
        ),
    ),
    revalidation_triggers=(CompatibilityRevalidationTrigger.OWNER_DECISION_CHANGED,),
)
_COMPATIBILITY_SUPERSEDED_REFERENCE = _compatibility_outcome(
    "fx-apa03-compatibility-superseded-reference",
    _PROFILE_SUPERSEDED_REFERENCE,
    lifecycle_status=CompatibilityProfileLifecycleStatus.SUPERSEDED,
    change_class=CompatibilityChangeClass.WARNING,
    status=CompatibilityProfileLifecycleStatus.SUPERSEDED,
    evidence_suffix="apa03-superseded-reference",
    warnings=(
        ParserWarning(
            code=ParserWarningCode.REFERENCE_SUPERSEDED,
            message="superseded profile requires revalidation",
        ),
    ),
    revalidation_triggers=(CompatibilityRevalidationTrigger.REFERENCE_CHANGED,),
)
_COMPATIBILITY_WITHDRAWN_REFERENCE = _compatibility_outcome(
    "fx-apa03-compatibility-withdrawn-reference",
    _PROFILE_WITHDRAWN_REFERENCE,
    lifecycle_status=CompatibilityProfileLifecycleStatus.WITHDRAWN,
    change_class=CompatibilityChangeClass.BREAKING,
    status=CompatibilityProfileLifecycleStatus.WITHDRAWN,
    evidence_suffix="apa03-withdrawn-reference",
    warnings=(
        ParserWarning(
            code=ParserWarningCode.WITHDRAWN_PROFILE_BLOCKED,
            message="withdrawn profile blocks parser success",
        ),
    ),
    revalidation_triggers=(CompatibilityRevalidationTrigger.OWNER_DECISION_CHANGED,),
)
_COMPATIBILITY_UNAVAILABLE_REFERENCE = _compatibility_outcome(
    "fx-apa03-compatibility-unavailable-reference",
    _PROFILE_UNAVAILABLE_REFERENCE,
    lifecycle_status=CompatibilityProfileLifecycleStatus.UNAVAILABLE,
    change_class=CompatibilityChangeClass.UNAVAILABLE,
    status=CompatibilityProfileLifecycleStatus.UNAVAILABLE,
    evidence_suffix="apa03-unavailable-reference",
    warnings=(
        ParserWarning(
            code=ParserWarningCode.UNAVAILABLE_PROFILE_WARNING,
            message="unavailable profile cannot be treated as current",
        ),
    ),
)
_COMPATIBILITY_CHANGED_REFERENCE = _compatibility_outcome(
    "fx-apa03-compatibility-changed-reference",
    _PROFILE_CHANGED_REFERENCE,
    lifecycle_status=CompatibilityProfileLifecycleStatus.CURRENT,
    change_class=CompatibilityChangeClass.WARNING,
    status=CompatibilityProfileLifecycleStatus.CURRENT,
    evidence_suffix="apa03-changed-reference",
    warnings=(
        ParserWarning(
            code=ParserWarningCode.REFERENCE_CHANGED,
            message="changed reference commit requires revalidation",
        ),
    ),
    revalidation_triggers=(CompatibilityRevalidationTrigger.REFERENCE_CHANGED,),
)
_COMPATIBILITY_INTERNAL_OBSERVATION = _compatibility_outcome(
    "fx-apa03-compatibility-internal-observation",
    _PROFILE_INTERNAL_OBSERVATION,
    lifecycle_status=CompatibilityProfileLifecycleStatus.CURRENT,
    change_class=CompatibilityChangeClass.UNKNOWN,
    status=CompatibilityProfileLifecycleStatus.CURRENT,
    evidence_suffix="apa03-internal-observation",
    warnings=(
        ParserWarning(
            code=ParserWarningCode.INTERNAL_ENDPOINT_OBSERVATION_ONLY,
            message="internal endpoint observation does not become a stable contract",
        ),
    ),
    revalidation_triggers=(CompatibilityRevalidationTrigger.PROVIDER_STRUCTURE_UNPROVEN_OR_STALE,),
)
_COMPATIBILITY_UNSUPPORTED_CLAIM = _compatibility_outcome(
    "fx-apa03-compatibility-unsupported-claim",
    _PROFILE_UNSUPPORTED_CLAIM,
    lifecycle_status=CompatibilityProfileLifecycleStatus.CURRENT,
    change_class=CompatibilityChangeClass.UNAVAILABLE,
    status=ParserOutcomeStatus.UNSUPPORTED_STRUCTURE,
    evidence_suffix="apa03-unsupported-claim",
    warnings=(
        ParserWarning(
            code=ParserWarningCode.UNSUPPORTED_EXTRACTION_CLAIM,
            message="unsupported extraction claim stays unavailable or unknown",
        ),
    ),
)

_SEARCH_SOURCE_DISPUTED_REFERENCE = _search_source_analysis(
    "fx-apa03-analysis-disputed-reference",
    _REQUEST_DISPUTED_REFERENCE,
    _TRANSPORT_DISPUTED_REFERENCE,
    _PROFILE_DISPUTED_REFERENCE,
    status=CompatibilityProfileLifecycleStatus.DISPUTED,
    evidence_suffix="apa03-disputed-reference",
    warnings=(
        ParserWarning(
            code=ParserWarningCode.DISPUTED_PROFILE_WARNING,
            message="disputed profile returns warning/disputed outcome",
        ),
    ),
)
_SEARCH_SOURCE_SUPERSEDED_REFERENCE = _search_source_analysis(
    "fx-apa03-analysis-superseded-reference",
    _REQUEST_SUPERSEDED_REFERENCE,
    _TRANSPORT_SUPERSEDED_REFERENCE,
    _PROFILE_SUPERSEDED_REFERENCE,
    status=CompatibilityProfileLifecycleStatus.SUPERSEDED,
    evidence_suffix="apa03-superseded-reference",
    warnings=(
        ParserWarning(
            code=ParserWarningCode.REFERENCE_SUPERSEDED,
            message="superseded profile requires revalidation",
        ),
    ),
)
_SEARCH_SOURCE_UNAVAILABLE_REFERENCE = _search_source_analysis(
    "fx-apa03-analysis-unavailable-reference",
    _REQUEST_UNAVAILABLE_REFERENCE,
    _TRANSPORT_UNAVAILABLE_REFERENCE,
    _PROFILE_UNAVAILABLE_REFERENCE,
    status=CompatibilityProfileLifecycleStatus.UNAVAILABLE,
    evidence_suffix="apa03-unavailable-reference",
    warnings=(
        ParserWarning(
            code=ParserWarningCode.UNAVAILABLE_PROFILE_WARNING,
            message="unavailable profile cannot be treated as current",
        ),
    ),
)
_SEARCH_SOURCE_INTERNAL_OBSERVATION = _search_source_analysis(
    "fx-apa03-analysis-internal-observation",
    _REQUEST_INTERNAL_OBSERVATION,
    _TRANSPORT_INTERNAL_OBSERVATION,
    _PROFILE_INTERNAL_OBSERVATION,
    status=CompatibilityProfileLifecycleStatus.CURRENT,
    evidence_suffix="apa03-internal-observation",
    warnings=(
        ParserWarning(
            code=ParserWarningCode.INTERNAL_ENDPOINT_OBSERVATION_ONLY,
            message="internal endpoint observation does not become a stable contract",
        ),
    ),
)
_SEARCH_SOURCE_CURRENT_REFERENCE = _search_source_analysis(
    "fx-apa03-analysis-current-reference",
    _REQUEST_CURRENT_REFERENCE,
    _TRANSPORT_CURRENT_REFERENCE,
    _PROFILE_CURRENT_REFERENCE,
    status=ParserOutcomeStatus.USABLE_RESPONSE,
    evidence_suffix="apa03-current-reference",
)

_SEARCH_CONFIGURATION_UNSUPPORTED_CLAIM = _search_configuration(
    "fx-apa03-extraction-unsupported-claim",
    _REQUEST_UNSUPPORTED_CLAIM,
    _TRANSPORT_UNSUPPORTED_CLAIM,
    _PROFILE_UNSUPPORTED_CLAIM,
    status=ParserOutcomeStatus.UNSUPPORTED_STRUCTURE,
    evidence_suffix="apa03-unsupported-claim",
    warnings=(
        ParserWarning(
            code=ParserWarningCode.UNSUPPORTED_EXTRACTION_CLAIM,
            message="unsupported extraction claim stays unavailable or unknown",
        ),
    ),
)

_SEARCH_CONFIGURATION_CHANGED_REFERENCE = _search_configuration(
    "fx-apa03-extraction-changed-reference",
    _REQUEST_CHANGED_REFERENCE,
    _TRANSPORT_CHANGED_REFERENCE,
    _PROFILE_CHANGED_REFERENCE,
    status=CompatibilityProfileLifecycleStatus.CURRENT,
    evidence_suffix="apa03-changed-reference",
    warnings=(
        ParserWarning(
            code=ParserWarningCode.REFERENCE_CHANGED,
            message="changed reference commit requires revalidation",
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
    _fixture(
        "FX-APA03-CURRENT-REFERENCE-PROFILE-001",
        "current reference profile accepted for semantic Tier 1 claims",
        _REQUEST_CURRENT_REFERENCE,
        _TRANSPORT_CURRENT_REFERENCE,
        _usable_attempt(
            "fx-apa03-attempt-current-reference",
            _PROFILE_CURRENT_REFERENCE,
            _REQUEST_CURRENT_REFERENCE,
            _TRANSPORT_CURRENT_REFERENCE,
            evidence_suffix="apa03-current-reference",
        ),
        compatibility_profile=_PROFILE_CURRENT_REFERENCE,
        compatibility_outcome=_COMPATIBILITY_CURRENT_REFERENCE,
        search_source_analysis_outcome=_SEARCH_SOURCE_CURRENT_REFERENCE,
        listing_page_parse_outcome=_PAGE_CURRENT_REFERENCE,
    ),
    _fixture(
        "FX-APA03-STALE-REFERENCE-PROFILE-BLOCKS-CLEAN-EMPTY-001",
        "stale reference profile blocks clean empty",
        _REQUEST_STALE_REFERENCE,
        _TRANSPORT_STALE_REFERENCE,
        _usable_attempt(
            "fx-apa03-attempt-stale-reference",
            _PROFILE_STALE_REFERENCE,
            _REQUEST_STALE_REFERENCE,
            _TRANSPORT_STALE_REFERENCE,
            parser_status=ParserOutcomeStatus.UNSUPPORTED_STRUCTURE,
            reference_status=ReferenceOutcomeStatus.REFERENCE_STALE,
            evidence_suffix="apa03-stale-reference",
            warnings=(
                ParserWarning(
                    code=ParserWarningCode.STALE_PROFILE_BLOCKED,
                    message="stale reference profile blocks clean empty",
                ),
            ),
        ),
        compatibility_profile=_PROFILE_STALE_REFERENCE,
        compatibility_outcome=_COMPATIBILITY_STALE_REFERENCE,
        listing_page_parse_outcome=_PAGE_STALE_BLOCKED,
    ),
    _fixture(
        "FX-APA03-DISPUTED-REFERENCE-PROFILE-WARNING-001",
        "disputed reference profile returns warning/disputed outcome",
        _REQUEST_DISPUTED_REFERENCE,
        _TRANSPORT_DISPUTED_REFERENCE,
        _usable_attempt(
            "fx-apa03-attempt-disputed-reference",
            _PROFILE_DISPUTED_REFERENCE,
            _REQUEST_DISPUTED_REFERENCE,
            _TRANSPORT_DISPUTED_REFERENCE,
            parser_status=ParserOutcomeStatus.RESULT_AMBIGUOUS,
            reference_status=ReferenceOutcomeStatus.REFERENCE_DISPUTED,
            evidence_suffix="apa03-disputed-reference",
            warnings=(
                ParserWarning(
                    code=ParserWarningCode.DISPUTED_PROFILE_WARNING,
                    message="disputed profile returns warning/disputed outcome",
                ),
            ),
        ),
        compatibility_profile=_PROFILE_DISPUTED_REFERENCE,
        compatibility_outcome=_COMPATIBILITY_DISPUTED_REFERENCE,
        search_source_analysis_outcome=_SEARCH_SOURCE_DISPUTED_REFERENCE,
    ),
    _fixture(
        "FX-APA03-SUPERSEDED-REFERENCE-PROFILE-001",
        "superseded reference profile requires revalidation",
        _REQUEST_SUPERSEDED_REFERENCE,
        _TRANSPORT_SUPERSEDED_REFERENCE,
        _usable_attempt(
            "fx-apa03-attempt-superseded-reference",
            _PROFILE_SUPERSEDED_REFERENCE,
            _REQUEST_SUPERSEDED_REFERENCE,
            _TRANSPORT_SUPERSEDED_REFERENCE,
            parser_status=ParserOutcomeStatus.UNSUPPORTED_STRUCTURE,
            reference_status=ReferenceOutcomeStatus.REFERENCE_STALE,
            evidence_suffix="apa03-superseded-reference",
            warnings=(
                ParserWarning(
                    code=ParserWarningCode.REFERENCE_SUPERSEDED,
                    message="superseded profile requires revalidation",
                ),
            ),
        ),
        compatibility_profile=_PROFILE_SUPERSEDED_REFERENCE,
        compatibility_outcome=_COMPATIBILITY_SUPERSEDED_REFERENCE,
        search_source_analysis_outcome=_SEARCH_SOURCE_SUPERSEDED_REFERENCE,
    ),
    _fixture(
        "FX-APA03-WITHDRAWN-REFERENCE-PROFILE-BLOCKS-SUCCESS-001",
        "withdrawn reference profile blocks parser success",
        _REQUEST_WITHDRAWN_REFERENCE,
        _TRANSPORT_WITHDRAWN_REFERENCE,
        _usable_attempt(
            "fx-apa03-attempt-withdrawn-reference",
            _PROFILE_WITHDRAWN_REFERENCE,
            _REQUEST_WITHDRAWN_REFERENCE,
            _TRANSPORT_WITHDRAWN_REFERENCE,
            parser_status=ParserOutcomeStatus.EXPLICIT_REJECTION,
            reference_status=ReferenceOutcomeStatus.REFERENCE_MISSING,
            evidence_suffix="apa03-withdrawn-reference",
            warnings=(
                ParserWarning(
                    code=ParserWarningCode.WITHDRAWN_PROFILE_BLOCKED,
                    message="withdrawn profile blocks parser success",
                ),
            ),
        ),
        compatibility_profile=_PROFILE_WITHDRAWN_REFERENCE,
        compatibility_outcome=_COMPATIBILITY_WITHDRAWN_REFERENCE,
        listing_page_parse_outcome=_PAGE_WITHDRAWN_BLOCKED,
    ),
    _fixture(
        "FX-APA03-UNAVAILABLE-REFERENCE-PROFILE-001",
        "unavailable reference profile remains unavailable",
        _REQUEST_UNAVAILABLE_REFERENCE,
        _TRANSPORT_UNAVAILABLE_REFERENCE,
        _usable_attempt(
            "fx-apa03-attempt-unavailable-reference",
            _PROFILE_UNAVAILABLE_REFERENCE,
            _REQUEST_UNAVAILABLE_REFERENCE,
            _TRANSPORT_UNAVAILABLE_REFERENCE,
            parser_status=ParserOutcomeStatus.UNSUPPORTED_STRUCTURE,
            reference_status=ReferenceOutcomeStatus.REFERENCE_MISSING,
            evidence_suffix="apa03-unavailable-reference",
            warnings=(
                ParserWarning(
                    code=ParserWarningCode.UNAVAILABLE_PROFILE_WARNING,
                    message="unavailable profile remains unavailable",
                ),
            ),
        ),
        compatibility_profile=_PROFILE_UNAVAILABLE_REFERENCE,
        compatibility_outcome=_COMPATIBILITY_UNAVAILABLE_REFERENCE,
        search_source_analysis_outcome=_SEARCH_SOURCE_UNAVAILABLE_REFERENCE,
    ),
    _fixture(
        "FX-APA03-UNSUPPORTED-EXTRACTION-CLAIM-001",
        "unsupported extraction claim stays unavailable or unknown",
        _REQUEST_UNSUPPORTED_CLAIM,
        _TRANSPORT_UNSUPPORTED_CLAIM,
        _usable_attempt(
            "fx-apa03-attempt-unsupported-claim",
            _PROFILE_UNSUPPORTED_CLAIM,
            _REQUEST_UNSUPPORTED_CLAIM,
            _TRANSPORT_UNSUPPORTED_CLAIM,
            parser_status=ParserOutcomeStatus.UNSUPPORTED_STRUCTURE,
            evidence_suffix="apa03-unsupported-claim",
            warnings=(
                ParserWarning(
                    code=ParserWarningCode.UNSUPPORTED_EXTRACTION_CLAIM,
                    message="unsupported extraction claim stays unavailable or unknown",
                ),
            ),
        ),
        compatibility_profile=_PROFILE_UNSUPPORTED_CLAIM,
        compatibility_outcome=_COMPATIBILITY_UNSUPPORTED_CLAIM,
        search_configuration_extraction_outcome=_SEARCH_CONFIGURATION_UNSUPPORTED_CLAIM,
    ),
    _fixture(
        "FX-APA03-REFERENCE-COMMIT-REVALIDATION-001",
        "changed reference commit requires revalidation",
        _REQUEST_CHANGED_REFERENCE,
        _TRANSPORT_CHANGED_REFERENCE,
        _usable_attempt(
            "fx-apa03-attempt-changed-reference",
            _PROFILE_CHANGED_REFERENCE,
            _REQUEST_CHANGED_REFERENCE,
            _TRANSPORT_CHANGED_REFERENCE,
            evidence_suffix="apa03-changed-reference",
            warnings=(
                ParserWarning(
                    code=ParserWarningCode.REFERENCE_CHANGED,
                    message="changed reference commit requires revalidation",
                ),
            ),
        ),
        compatibility_profile=_PROFILE_CHANGED_REFERENCE,
        compatibility_outcome=_COMPATIBILITY_CHANGED_REFERENCE,
        search_configuration_extraction_outcome=_SEARCH_CONFIGURATION_CHANGED_REFERENCE,
    ),
    _fixture(
        "FX-APA03-INTERNAL-ENDPOINT-OBSERVATION-NOT-STABLE-001",
        "internal endpoint observation does not become a stable contract",
        _REQUEST_INTERNAL_OBSERVATION,
        _TRANSPORT_INTERNAL_OBSERVATION,
        _usable_attempt(
            "fx-apa03-attempt-internal-observation",
            _PROFILE_INTERNAL_OBSERVATION,
            _REQUEST_INTERNAL_OBSERVATION,
            _TRANSPORT_INTERNAL_OBSERVATION,
            evidence_suffix="apa03-internal-observation",
            warnings=(
                ParserWarning(
                    code=ParserWarningCode.INTERNAL_ENDPOINT_OBSERVATION_ONLY,
                    message="internal endpoint observation does not become a stable contract",
                ),
            ),
        ),
        compatibility_profile=_PROFILE_INTERNAL_OBSERVATION,
        compatibility_outcome=_COMPATIBILITY_INTERNAL_OBSERVATION,
        search_source_analysis_outcome=_SEARCH_SOURCE_INTERNAL_OBSERVATION,
    ),
    _fixture(
        "FX-APA04-SOURCE-REFERENCE-BOUNDED-INPUT-ACCEPTED-001",
        "Beacon-owned source reference is accepted as untrusted bounded input",
        _REQUEST_SOURCE_BOUNDARY_ACCEPTED,
        _TRANSPORT_SOURCE_BOUNDARY_ACCEPTED,
        _ATTEMPT_SOURCE_BOUNDARY_ACCEPTED,
        source_boundary_outcome=_BOUNDARY_ACCEPTED,
        compatibility_profile=_PROFILE_SOURCE_BOUNDARY,
    ),
    _fixture(
        "FX-APA04-SOURCE-BOUNDARY-MALFORMED-REJECTED-001",
        "malformed source boundary is rejected",
        _REQUEST_SOURCE_BOUNDARY_MALFORMED,
        _TRANSPORT_SOURCE_BOUNDARY_MALFORMED,
        _ATTEMPT_SOURCE_BOUNDARY_MALFORMED,
        source_boundary_outcome=_BOUNDARY_MALFORMED,
        compatibility_profile=_PROFILE_SOURCE_BOUNDARY,
    ),
    _fixture(
        "FX-APA04-SOURCE-BOUNDARY-UNSUPPORTED-BLOCKED-001",
        "unsupported source boundary is blocked",
        _REQUEST_SOURCE_BOUNDARY_UNSUPPORTED,
        _TRANSPORT_SOURCE_BOUNDARY_UNSUPPORTED,
        _ATTEMPT_SOURCE_BOUNDARY_UNSUPPORTED,
        source_boundary_outcome=_BOUNDARY_UNSUPPORTED,
        compatibility_profile=_PROFILE_SOURCE_BOUNDARY,
    ),
    _fixture(
        "FX-APA04-SOURCE-BOUNDARY-POLICY-MISSING-001",
        "missing host/path/query policy blocks validation",
        _REQUEST_SOURCE_BOUNDARY_POLICY_MISSING,
        _TRANSPORT_SOURCE_BOUNDARY_POLICY_MISSING,
        _ATTEMPT_SOURCE_BOUNDARY_POLICY_MISSING,
        source_boundary_outcome=_BOUNDARY_POLICY_MISSING,
        compatibility_profile=_PROFILE_SOURCE_BOUNDARY,
    ),
    _fixture(
        "FX-APA04-SOURCE-BOUNDARY-REDIRECT-POLICY-MISSING-001",
        "missing redirect policy blocks live follow",
        _REQUEST_SOURCE_BOUNDARY_REDIRECT,
        _TRANSPORT_SOURCE_BOUNDARY_REDIRECT,
        _ATTEMPT_SOURCE_BOUNDARY_REDIRECT,
        source_boundary_outcome=_BOUNDARY_REDIRECT_POLICY_MISSING,
        compatibility_profile=_PROFILE_SOURCE_BOUNDARY,
    ),
    _fixture(
        "FX-APA04-SOURCE-BOUNDARY-DNS-POLICY-MISSING-001",
        "missing DNS policy blocks probing",
        _REQUEST_SOURCE_BOUNDARY_DNS,
        _TRANSPORT_SOURCE_BOUNDARY_DNS,
        _ATTEMPT_SOURCE_BOUNDARY_DNS,
        source_boundary_outcome=_BOUNDARY_DNS_POLICY_MISSING,
        compatibility_profile=_PROFILE_SOURCE_BOUNDARY,
    ),
    _fixture(
        "FX-APA04-SOURCE-BOUNDARY-CANONICALIZATION-UNPROVEN-001",
        "canonicalization and equivalence remain unproven",
        _REQUEST_SOURCE_BOUNDARY_CANONICALIZATION,
        _TRANSPORT_SOURCE_BOUNDARY_CANONICALIZATION,
        _ATTEMPT_SOURCE_BOUNDARY_CANONICALIZATION,
        source_boundary_outcome=_BOUNDARY_CANONICALIZATION_UNPROVEN,
        compatibility_profile=_PROFILE_SOURCE_BOUNDARY,
    ),
    _fixture(
        "FX-APA04-SOURCE-BOUNDARY-SHELL-TARGET-BLOCKED-001",
        "shell interpolation target is blocked",
        _REQUEST_SOURCE_BOUNDARY_SHELL,
        _TRANSPORT_SOURCE_BOUNDARY_SHELL,
        _ATTEMPT_SOURCE_BOUNDARY_SHELL,
        source_boundary_outcome=_BOUNDARY_SHELL_BLOCKED,
        compatibility_profile=_PROFILE_SOURCE_BOUNDARY,
    ),
    _fixture(
        "FX-APA04-SOURCE-BOUNDARY-FILESYSTEM-TARGET-BLOCKED-001",
        "filesystem target interpolation is blocked",
        _REQUEST_SOURCE_BOUNDARY_FILESYSTEM,
        _TRANSPORT_SOURCE_BOUNDARY_FILESYSTEM,
        _ATTEMPT_SOURCE_BOUNDARY_FILESYSTEM,
        source_boundary_outcome=_BOUNDARY_FILESYSTEM_BLOCKED,
        compatibility_profile=_PROFILE_SOURCE_BOUNDARY,
    ),
    _fixture(
        "FX-APA04-SOURCE-BOUNDARY-NETWORK-TARGET-BLOCKED-001",
        "arbitrary network target is blocked",
        _REQUEST_SOURCE_BOUNDARY_NETWORK,
        _TRANSPORT_SOURCE_BOUNDARY_NETWORK,
        _ATTEMPT_SOURCE_BOUNDARY_NETWORK,
        source_boundary_outcome=_BOUNDARY_NETWORK_BLOCKED,
        compatibility_profile=_PROFILE_SOURCE_BOUNDARY,
    ),
    _fixture(
        "FX-APA04-SOURCE-BOUNDARY-PARSER-OUTPUT-PRESERVES-BEACON-SOURCE-001",
        "parser output preserves Beacon-owned source ownership",
        _REQUEST_SOURCE_BOUNDARY_PRESERVED,
        _TRANSPORT_SOURCE_BOUNDARY_PRESERVED,
        _ATTEMPT_SOURCE_BOUNDARY_PRESERVED,
        source_boundary_outcome=_BOUNDARY_OUTPUT_PRESERVED,
        compatibility_profile=_PROFILE_SOURCE_BOUNDARY,
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
