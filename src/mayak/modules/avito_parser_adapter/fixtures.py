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
    ListingCandidateStatus,
    ListingCardCandidate,
    ListingFieldAvailability,
    ListingFieldCandidate,
    ListingFieldFamily,
    ListingFieldQuality,
    ListingFieldTier,
    ListingPageParseOutcome,
    MultivalueLossReason,
    MultivalueNormalizationOutcome,
    MultivalueNormalizationRule,
    MultivalueNormalizationStatus,
    MultivaluePreservationMode,
    NormalizedListingCandidate,
    ParserAttemptOutcome,
    ParserCompatibilityOutcome,
    ParserCompatibilityProfile,
    ParserEvidenceReference,
    ParserOutcomeExplanation,
    ParserOutcomeStatus,
    ParserRequestEnvelope,
    ParserResponseClassificationRule,
    ParserSourceReference,
    ParserWarning,
    ParserWarningCode,
    ProviderResponseEvidenceClass,
    ReferenceOutcomeStatus,
    ResponseCompletenessStatus,
    ResponseRestrictionSignal,
    SearchConfigurationCandidate,
    SearchConfigurationEvidence,
    SearchConfigurationExtractionField,
    SearchConfigurationExtractionOutcome,
    SearchConfigurationFieldStatus,
    SearchConfigurationParameterCandidate,
    SearchConfigurationValueKind,
    SearchConfigurationWarningCode,
    SearchSourceAnalysisOutcome,
    SourceBoundaryOutcome,
    SourceBoundaryPolicyRequirement,
    SourceBoundaryRiskCode,
    SourceBoundaryStatus,
    SourceReferenceKind,
    TransportOutcomeReference,
    TransportOutcomeStatus,
    TransportResponseClassificationOutcome,
    _lifecycle_status_from_reference_status,
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
        if self.compatibility_profile is None:
            object.__setattr__(
                self, "compatibility_profile", self.request_envelope.compatibility_profile
            )


def _profile(
    profile_id: str,
    *,
    lifecycle_status: CompatibilityProfileLifecycleStatus | None = None,
    authority_class: CompatibilityProfileAuthorityClass = (
        CompatibilityProfileAuthorityClass.OBSERVATION_ONLY
    ),
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
        lifecycle_status
        if lifecycle_status is not None
        else _lifecycle_status_from_reference_status(reference_status)
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
        supported_shape_signatures=supported_extraction_claims
        or (f"shape::{evidence_suffix}::tier1",),
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
        safe_source_reference=safe_source_reference,
        source_reference=source_reference,
        source_boundary_outcome=source_boundary_outcome,
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
    beacon_source_reference: str,
    bounded_value: str,
    host_reference: str | None = None,
    path_reference: str | None = None,
    query_reference: str | None = None,
    header_references: tuple[str, ...] = (),
    extracted_value_references: tuple[str, ...] = (),
    policy_requirements: tuple[SourceBoundaryPolicyRequirement, ...] = (),
    risk_codes: tuple[SourceBoundaryRiskCode, ...] = (),
    notes: tuple[str, ...] = (),
) -> ParserSourceReference:
    return ParserSourceReference(
        source_reference_id=source_reference_id,
        source_reference_kind=kind,
        beacon_source_reference=beacon_source_reference,
        bounded_value=bounded_value,
        host_reference=host_reference,
        path_reference=path_reference,
        query_reference=query_reference,
        header_references=header_references,
        extracted_value_references=extracted_value_references,
        policy_requirements=policy_requirements,
        risk_codes=risk_codes,
        notes=notes,
    )


def _source_boundary(
    boundary_id: str,
    source_reference: ParserSourceReference,
    *,
    status: SourceBoundaryStatus,
    policy_requirements: tuple[SourceBoundaryPolicyRequirement, ...] = (),
    risk_codes: tuple[SourceBoundaryRiskCode, ...] = (),
    warnings: tuple[ParserWarning, ...] = (),
    notes: tuple[str, ...] = (),
) -> SourceBoundaryOutcome:
    return SourceBoundaryOutcome(
        boundary_id=boundary_id,
        source_reference=source_reference,
        status=status,
        policy_requirements=policy_requirements,
        risk_codes=risk_codes,
        warnings=warnings,
        notes=notes,
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


def _listing_field_candidate(
    field_candidate_id: str,
    field_family: ListingFieldFamily,
    tier: ListingFieldTier,
    availability: ListingFieldAvailability,
    quality: ListingFieldQuality,
    *,
    value: str | None = None,
    compatibility_profile: ParserCompatibilityProfile | None = None,
    evidence_suffix: str,
    warnings: tuple[ParserWarning, ...] = (),
    notes: tuple[str, ...] = (),
) -> ListingFieldCandidate:
    evidence_references = (
        ParserEvidenceReference(
            reference_id=f"fx::{evidence_suffix}::{field_candidate_id}",
            evidence_kind="listing-field",
            notes=(f"synthetic field candidate {field_candidate_id}",),
        ),
    )
    return ListingFieldCandidate(
        field_candidate_id=field_candidate_id,
        field_family=field_family,
        tier=tier,
        availability=availability,
        quality=quality,
        value=value,
        compatibility_profile=compatibility_profile,
        warnings=warnings,
        evidence_references=evidence_references,
        notes=notes,
    )


def _tier_1_listing_field_candidates(
    evidence_suffix: str,
    profile: ParserCompatibilityProfile,
) -> tuple[ListingFieldCandidate, ...]:
    return (
        _listing_field_candidate(
            f"fx-{evidence_suffix}-title",
            ListingFieldFamily.TITLE,
            ListingFieldTier.TIER_1_SEARCH_RESULT,
            ListingFieldAvailability.PROVEN_AVAILABLE,
            ListingFieldQuality.PROFILE_PROVEN,
            value="Synthetic Tier 1 title",
            compatibility_profile=profile,
            evidence_suffix=evidence_suffix,
        ),
        _listing_field_candidate(
            f"fx-{evidence_suffix}-price",
            ListingFieldFamily.NORMALIZED_PRICE,
            ListingFieldTier.TIER_1_SEARCH_RESULT,
            ListingFieldAvailability.PROVEN_AVAILABLE,
            ListingFieldQuality.PROFILE_PROVEN,
            value="123 456",
            compatibility_profile=profile,
            evidence_suffix=evidence_suffix,
        ),
        _listing_field_candidate(
            f"fx-{evidence_suffix}-listing-url",
            ListingFieldFamily.LISTING_URL,
            ListingFieldTier.TIER_1_SEARCH_RESULT,
            ListingFieldAvailability.PROVEN_AVAILABLE,
            ListingFieldQuality.PROFILE_PROVEN,
            value="listing::synthetic::url",
            compatibility_profile=profile,
            evidence_suffix=evidence_suffix,
        ),
        _listing_field_candidate(
            f"fx-{evidence_suffix}-preview-image",
            ListingFieldFamily.PREVIEW_IMAGE,
            ListingFieldTier.TIER_1_SEARCH_RESULT,
            ListingFieldAvailability.PROVEN_AVAILABLE,
            ListingFieldQuality.PROFILE_PROVEN,
            value="image::synthetic::preview",
            compatibility_profile=profile,
            evidence_suffix=evidence_suffix,
        ),
        _listing_field_candidate(
            f"fx-{evidence_suffix}-geography",
            ListingFieldFamily.GEOGRAPHY,
            ListingFieldTier.TIER_1_SEARCH_RESULT,
            ListingFieldAvailability.PROVEN_AVAILABLE,
            ListingFieldQuality.PROFILE_PROVEN,
            value="synthetic-city",
            compatibility_profile=profile,
            evidence_suffix=evidence_suffix,
        ),
        _listing_field_candidate(
            f"fx-{evidence_suffix}-category",
            ListingFieldFamily.CATEGORY,
            ListingFieldTier.TIER_1_SEARCH_RESULT,
            ListingFieldAvailability.PROVEN_AVAILABLE,
            ListingFieldQuality.PROFILE_PROVEN,
            value="synthetic-category",
            compatibility_profile=profile,
            evidence_suffix=evidence_suffix,
        ),
        _listing_field_candidate(
            f"fx-{evidence_suffix}-publication-order",
            ListingFieldFamily.PUBLICATION_ORDER,
            ListingFieldTier.TIER_1_SEARCH_RESULT,
            ListingFieldAvailability.PROVEN_AVAILABLE,
            ListingFieldQuality.PROFILE_PROVEN,
            value="1",
            compatibility_profile=profile,
            evidence_suffix=evidence_suffix,
        ),
    )


def _listing_card(
    card_id: str,
    *,
    field_candidates: tuple[ListingFieldCandidate, ...],
    evidence_suffix: str,
    warnings: tuple[ParserWarning, ...] = (),
) -> ListingCardCandidate:
    return ListingCardCandidate(
        listing_card_id=card_id,
        field_candidates=field_candidates,
        warnings=warnings,
        evidence_references=(
            ParserEvidenceReference(
                reference_id=f"fx::{evidence_suffix}::card",
                evidence_kind="listing-card",
                notes=("synthetic listing card",),
            ),
        ),
    )


def _listing_candidate(
    candidate_id: str,
    card: ListingCardCandidate,
    *,
    evidence_suffix: str,
    status: ListingCandidateStatus = ListingCandidateStatus.USABLE,
    warnings: tuple[ParserWarning, ...] = (),
) -> NormalizedListingCandidate:
    return NormalizedListingCandidate(
        listing_candidate_id=candidate_id,
        status=status,
        card_candidate=card,
        warnings=warnings,
        evidence_references=(
            ParserEvidenceReference(
                reference_id=f"fx::{evidence_suffix}::listing",
                evidence_kind="normalized-listing",
                notes=("synthetic normalized listing candidate",),
            ),
        ),
    )


def _tier_2_detail_field_candidates(
    evidence_suffix: str,
    profile: ParserCompatibilityProfile,
    *,
    availability: ListingFieldAvailability,
    warning_code: ParserWarningCode | None = None,
) -> tuple[ListingFieldCandidate, ...]:
    fields = []
    for family, label in (
        (ListingFieldFamily.DESCRIPTION, "description"),
        (ListingFieldFamily.SELLER, "seller"),
        (ListingFieldFamily.SELLER_RATING, "seller-rating"),
    ):
        field_warnings: tuple[ParserWarning, ...] = (
            (
                ParserWarning(
                    code=warning_code,
                    message=f"{label} evidence remains synthetic and explicit",
                ),
            )
            if warning_code is not None
            else ()
        )
        fields.append(
            _listing_field_candidate(
                f"fx-{evidence_suffix}-{label}",
                family,
                ListingFieldTier.TIER_2_LISTING_DETAIL,
                availability,
                ListingFieldQuality.EVIDENCE_BOUND
                if availability is ListingFieldAvailability.PROVEN_AVAILABLE
                else ListingFieldQuality.UNVERIFIED,
                value=(
                    "Synthetic listing detail"
                    if family is ListingFieldFamily.DESCRIPTION
                    else "Synthetic seller"
                    if family is ListingFieldFamily.SELLER
                    else "Synthetic seller rating"
                )
                if availability is ListingFieldAvailability.PROVEN_AVAILABLE
                else None,
                compatibility_profile=profile,
                evidence_suffix=evidence_suffix,
                warnings=field_warnings,
            )
        )
    return tuple(fields)


def _tier_3_phone_field_candidates(
    evidence_suffix: str,
    profile: ParserCompatibilityProfile,
    *,
    availability: ListingFieldAvailability,
    value_label: str | None = None,
) -> tuple[ListingFieldCandidate, ...]:
    phone_warnings: tuple[ParserWarning, ...] = (
        (
            ParserWarning(
                code=ParserWarningCode.PHONE_UNAVAILABLE,
                message="phone value remains proof-gated in synthetic case",
            ),
        )
        if availability is not ListingFieldAvailability.PROVEN_AVAILABLE
        else ()
    )
    return (
        _listing_field_candidate(
            f"fx-{evidence_suffix}-phone-availability",
            ListingFieldFamily.PHONE_AVAILABILITY,
            ListingFieldTier.TIER_3_CONTACT,
            availability,
            ListingFieldQuality.EVIDENCE_BOUND,
            value=value_label
            if availability is ListingFieldAvailability.PROVEN_AVAILABLE
            else None,
            compatibility_profile=profile,
            evidence_suffix=evidence_suffix,
            warnings=phone_warnings,
        ),
        _listing_field_candidate(
            f"fx-{evidence_suffix}-phone-value",
            ListingFieldFamily.PHONE_VALUE,
            ListingFieldTier.TIER_3_CONTACT,
            availability,
            ListingFieldQuality.EVIDENCE_BOUND,
            value=None,
            compatibility_profile=profile,
            evidence_suffix=evidence_suffix,
            warnings=phone_warnings,
        ),
    )


def _usable_attempt(
    attempt_id: str,
    profile: ParserCompatibilityProfile,
    request: ParserRequestEnvelope,
    transport: TransportOutcomeReference,
    *,
    parser_status: ParserOutcomeStatus | None = ParserOutcomeStatus.USABLE_RESPONSE,
    reference_status: ReferenceOutcomeStatus | CompatibilityProfileLifecycleStatus | None = None,
    transport_response_classification: TransportResponseClassificationOutcome | None = None,
    warnings: tuple[ParserWarning, ...] = (),
    evidence_suffix: str,
) -> ParserAttemptOutcome:
    evidence_references = transport.evidence_references
    if transport_response_classification is not None:
        evidence_references = (
            *evidence_references,
            *transport_response_classification.evidence_references,
        )
    return ParserAttemptOutcome(
        attempt_id=attempt_id,
        transport_status=transport.transport_status,
        parser_status=parser_status,
        reference_status=reference_status,
        request_envelope=request,
        transport_outcome=transport,
        response_reference=f"response::{evidence_suffix}",
        transport_response_classification=transport_response_classification,
        warnings=warnings,
        evidence_references=evidence_references,
        explanation=ParserOutcomeExplanation(
            summary="synthetic parser attempt",
            reason_code=f"FX::{evidence_suffix}",
            status=parser_status,
            evidence_references=evidence_references,
            warnings=warnings,
        ),
    )


def _classification_rule(
    rule_id: str,
    *,
    summary: str,
    required_transport_statuses: tuple[TransportOutcomeStatus, ...] = (),
    required_parser_statuses: tuple[ParserOutcomeStatus, ...] = (),
    required_reference_statuses: tuple[
        ReferenceOutcomeStatus | CompatibilityProfileLifecycleStatus, ...
    ] = (),
    required_provider_evidence_classes: tuple[ProviderResponseEvidenceClass, ...] = (),
    required_response_completeness_statuses: tuple[ResponseCompletenessStatus, ...] = (),
    required_response_restriction_signals: tuple[ResponseRestrictionSignal, ...] = (),
    requires_current_profile_proof: bool = False,
    requires_required_structure: bool = True,
    notes: tuple[str, ...] = (),
) -> ParserResponseClassificationRule:
    return ParserResponseClassificationRule(
        rule_id=rule_id,
        summary=summary,
        required_transport_statuses=required_transport_statuses,
        required_parser_statuses=required_parser_statuses,
        required_reference_statuses=required_reference_statuses,
        required_provider_evidence_classes=required_provider_evidence_classes,
        required_response_completeness_statuses=required_response_completeness_statuses,
        required_response_restriction_signals=required_response_restriction_signals,
        requires_current_profile_proof=requires_current_profile_proof,
        requires_required_structure=requires_required_structure,
        notes=notes,
    )


def _transport_response_classification(
    classification_id: str,
    request: ParserRequestEnvelope,
    transport: TransportOutcomeReference,
    *,
    status: TransportOutcomeStatus
    | ParserOutcomeStatus
    | ReferenceOutcomeStatus
    | CompatibilityProfileLifecycleStatus
    | CompatibilityChangeClass
    | SourceBoundaryStatus,
    provider_response_evidence_class: ProviderResponseEvidenceClass,
    response_completeness_status: ResponseCompletenessStatus,
    response_restriction_signal: ResponseRestrictionSignal = ResponseRestrictionSignal.NONE,
    parser_status: ParserOutcomeStatus | None = None,
    reference_status: ReferenceOutcomeStatus | CompatibilityProfileLifecycleStatus | None = None,
    classification_rule: ParserResponseClassificationRule | None = None,
    evidence_suffix: str,
    warnings: tuple[ParserWarning, ...] = (),
    notes: tuple[str, ...] = (),
) -> TransportResponseClassificationOutcome:
    return TransportResponseClassificationOutcome(
        classification_id=classification_id,
        status=status,
        transport_status=transport.transport_status,
        parser_status=parser_status,
        reference_status=reference_status,
        provider_response_evidence_class=provider_response_evidence_class,
        response_completeness_status=response_completeness_status,
        response_restriction_signal=response_restriction_signal,
        classification_rule=classification_rule,
        transport_outcome=transport,
        request_envelope=request,
        warnings=warnings,
        evidence_references=(
            ParserEvidenceReference(
                reference_id=f"fx::{evidence_suffix}::classification",
                evidence_kind="transport-response-classification",
                notes=(f"synthetic classification {classification_id}",),
            ),
        ),
        explanation=ParserOutcomeExplanation(
            summary="synthetic transport/response classification",
            reason_code=f"FX::{evidence_suffix}",
            status=status,
            warnings=warnings,
        ),
        notes=notes,
    )


def _transport_classification_fixture(
    fixture_id: str,
    summary: str,
    profile: ParserCompatibilityProfile,
    *,
    request_id: str,
    purpose: str,
    safe_source_reference: str,
    transport_reference_id: str,
    transport_status: TransportOutcomeStatus,
    response_reference: str | None,
    classification_id: str,
    classification_status: TransportOutcomeStatus
    | ParserOutcomeStatus
    | ReferenceOutcomeStatus
    | CompatibilityProfileLifecycleStatus
    | CompatibilityChangeClass
    | SourceBoundaryStatus,
    provider_response_evidence_class: ProviderResponseEvidenceClass,
    response_completeness_status: ResponseCompletenessStatus,
    classification_rule: ParserResponseClassificationRule,
    evidence_suffix: str,
    parser_status: ParserOutcomeStatus | None = None,
    reference_status: ReferenceOutcomeStatus | CompatibilityProfileLifecycleStatus | None = None,
    response_restriction_signal: ResponseRestrictionSignal = ResponseRestrictionSignal.NONE,
    warnings: tuple[ParserWarning, ...] = (),
    source_reference: ParserSourceReference | None = None,
    source_boundary_outcome: SourceBoundaryOutcome | None = None,
    search_source_analysis_outcome: SearchSourceAnalysisOutcome | None = None,
    search_configuration_extraction_outcome: SearchConfigurationExtractionOutcome | None = None,
    listing_page_parse_outcome: ListingPageParseOutcome | None = None,
    listing_batch_parse_outcome: ListingBatchParseOutcome | None = None,
) -> SyntheticFixtureCase:
    request = _request(
        request_id,
        profile,
        purpose=purpose,
        safe_source_reference=safe_source_reference,
        source_reference=source_reference,
        source_boundary_outcome=source_boundary_outcome,
    )
    transport = _transport(
        transport_reference_id,
        status=transport_status,
        request_reference=request.request_id,
        response_reference=response_reference,
        route_reference="route::synthetic",
        evidence_reference_suffix=evidence_suffix,
    )
    classification = _transport_response_classification(
        f"{classification_id}::classification",
        request,
        transport,
        status=classification_status,
        provider_response_evidence_class=provider_response_evidence_class,
        response_completeness_status=response_completeness_status,
        response_restriction_signal=response_restriction_signal,
        parser_status=parser_status,
        reference_status=reference_status,
        classification_rule=classification_rule,
        evidence_suffix=evidence_suffix,
        warnings=warnings,
        notes=(f"synthetic transport/response classification fixture {fixture_id}",),
    )
    attempt = _usable_attempt(
        f"{classification_id}::attempt",
        profile,
        request,
        transport,
        parser_status=parser_status,
        reference_status=reference_status,
        transport_response_classification=classification,
        warnings=warnings,
        evidence_suffix=evidence_suffix,
    )
    return _fixture(
        fixture_id,
        summary,
        request,
        transport,
        attempt,
        compatibility_profile=profile,
        search_source_analysis_outcome=search_source_analysis_outcome,
        search_configuration_extraction_outcome=search_configuration_extraction_outcome,
        listing_page_parse_outcome=listing_page_parse_outcome,
        listing_batch_parse_outcome=listing_batch_parse_outcome,
    )


def _search_source_analysis(
    analysis_id: str,
    request: ParserRequestEnvelope,
    transport: TransportOutcomeReference,
    profile: ParserCompatibilityProfile,
    *,
    status: (
        ParserOutcomeStatus
        | TransportOutcomeStatus
        | ReferenceOutcomeStatus
        | CompatibilityProfileLifecycleStatus
        | CompatibilityChangeClass
        | SourceBoundaryStatus
    ),
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
    status: (
        ParserOutcomeStatus
        | TransportOutcomeStatus
        | ReferenceOutcomeStatus
        | CompatibilityProfileLifecycleStatus
        | CompatibilityChangeClass
        | SourceBoundaryStatus
    ),
    evidence_suffix: str,
    normalized_geography_candidates: tuple[str, ...] = ("synthetic-city",),
    normalized_category_candidates: tuple[str, ...] = ("synthetic-category",),
    normalized_filters: tuple[str, ...] = (),
    sort_context_reference: str | None = None,
    search_configuration_evidence: SearchConfigurationEvidence | None = None,
    search_configuration_candidates: tuple[SearchConfigurationCandidate, ...] = (),
    parameter_candidates: tuple[SearchConfigurationParameterCandidate, ...] = (),
    warnings: tuple[ParserWarning, ...] = (),
) -> SearchConfigurationExtractionOutcome:
    return SearchConfigurationExtractionOutcome(
        extraction_id=extraction_id,
        request_envelope=request,
        transport_outcome=transport,
        status=status,
        compatibility_profile=profile,
        search_configuration_evidence=search_configuration_evidence,
        search_configuration_candidates=search_configuration_candidates,
        parameter_candidates=parameter_candidates,
        normalized_geography_candidates=normalized_geography_candidates,
        normalized_category_candidates=normalized_category_candidates,
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


def _search_configuration_evidence(
    evidence_id: str,
    request: ParserRequestEnvelope,
    transport: TransportOutcomeReference,
    profile: ParserCompatibilityProfile,
    *,
    source_reference: ParserSourceReference | None = None,
    source_boundary_outcome: SourceBoundaryOutcome | None = None,
    evidence_suffix: str,
    notes: tuple[str, ...] = (),
) -> SearchConfigurationEvidence:
    return SearchConfigurationEvidence(
        evidence_id=evidence_id,
        request_envelope=request,
        compatibility_profile=profile,
        source_reference=source_reference,
        source_boundary_outcome=source_boundary_outcome,
        transport_outcome=transport,
        evidence_references=(
            ParserEvidenceReference(
                reference_id=f"fx::{evidence_suffix}::search-configuration-provenance",
                evidence_kind="search-configuration-provenance",
            ),
        ),
        notes=notes,
    )


def _multivalue_normalization_rule(
    rule_id: str,
    *,
    status: MultivalueNormalizationStatus,
    preservation_mode: MultivaluePreservationMode,
    loss_reason: MultivalueLossReason | None = None,
    notes: tuple[str, ...] = (),
) -> MultivalueNormalizationRule:
    return MultivalueNormalizationRule(
        rule_id=rule_id,
        status=status,
        preservation_mode=preservation_mode,
        loss_reason=loss_reason,
        notes=notes,
    )


def _multivalue_normalization_outcome(
    normalization_id: str,
    parameter_key: str,
    input_values: tuple[str, ...],
    *,
    status: MultivalueNormalizationStatus,
    preservation_mode: MultivaluePreservationMode,
    normalized_values: tuple[str, ...] = (),
    loss_reason: MultivalueLossReason | None = None,
    compatibility_profile: ParserCompatibilityProfile | None = None,
    source_boundary_outcome: SourceBoundaryOutcome | None = None,
    transport_response_classification: TransportResponseClassificationOutcome | None = None,
    rule_notes: tuple[str, ...] = (),
    outcome_notes: tuple[str, ...] = (),
    warnings: tuple[ParserWarning, ...] = (),
    evidence_suffix: str,
) -> MultivalueNormalizationOutcome:
    rule = _multivalue_normalization_rule(
        f"{normalization_id}::rule",
        status=status,
        preservation_mode=preservation_mode,
        loss_reason=loss_reason,
        notes=rule_notes,
    )
    return MultivalueNormalizationOutcome(
        normalization_id=normalization_id,
        parameter_key=parameter_key,
        input_values=input_values,
        normalization_rule=rule,
        status=status,
        preservation_mode=preservation_mode,
        normalized_values=normalized_values,
        loss_reason=loss_reason,
        compatibility_profile=compatibility_profile,
        source_boundary_outcome=source_boundary_outcome,
        transport_response_classification=transport_response_classification,
        warnings=warnings,
        evidence_references=(
            ParserEvidenceReference(
                reference_id=f"fx::{evidence_suffix}::multivalue::{parameter_key}",
                evidence_kind="multivalue-normalization",
            ),
        ),
        notes=outcome_notes,
    )


def _multivalue_profile(
    profile_id: str,
    *,
    evidence_suffix: str,
    lifecycle_status: CompatibilityProfileLifecycleStatus = (
        CompatibilityProfileLifecycleStatus.CURRENT
    ),
    reference_status: ReferenceOutcomeStatus = ReferenceOutcomeStatus.CURRENT,
) -> ParserCompatibilityProfile:
    return _profile(
        profile_id,
        lifecycle_status=lifecycle_status,
        evidence_suffix=evidence_suffix,
        reference_status=reference_status,
        supported_extraction_claims=(
            "repeated source and query values remain ordered collections",
            "duplicate repeated values are preserved",
            "first-value overwrite stays blocked",
            "later-value loss stays blocked",
            "collection-to-scalar collapse stays blocked",
            "unsupported, ambiguous and lossy multivalue states stay explicit",
            "compatibility profile, source boundary and response classification gate normalization",
            "filter editability, Beacon mutation and Scan mutation stay outside Parser ownership",
        ),
        unsupported_extraction_claims=(
            "live avito traffic",
            "raw query rewrite",
            "url validation",
            "filter catalog implementation",
            "beacon mutation",
            "scan mutation",
        ),
        completeness_rules=(
            "repeated values stay ordered",
            "duplicate values stay explicit",
            "lossy or blocked states stay explicit",
        ),
    )


def _apa07_multivalue_fixture(
    fixture_id: str,
    summary: str,
    *,
    evidence_suffix: str,
    repeated_values: tuple[str, ...],
    multivalue_status: MultivalueNormalizationStatus,
    preservation_mode: MultivaluePreservationMode,
    loss_reason: MultivalueLossReason | None = None,
    normalized_values: tuple[str, ...] = (),
    parameter_key: str = "filter-key:synthetic-color",
    parameter_value: str | None = None,
    parameter_field_status: SearchConfigurationFieldStatus = (
        SearchConfigurationFieldStatus.PRESERVED
    ),
    parameter_value_kind: SearchConfigurationValueKind = (
        SearchConfigurationValueKind.COLLECTION
    ),
    candidate_id: str | None = None,
    extraction_field: SearchConfigurationExtractionField = (
        SearchConfigurationExtractionField.REPEATED_PARAMETER
    ),
    candidate_field_status: SearchConfigurationFieldStatus = (
        SearchConfigurationFieldStatus.PRESERVED
    ),
    candidate_value_kind: SearchConfigurationValueKind = (
        SearchConfigurationValueKind.COLLECTION
    ),
    warning_code: ParserWarningCode | SearchConfigurationWarningCode | None = None,
    warning_message: str | None = None,
    profile: ParserCompatibilityProfile | None = None,
    request: ParserRequestEnvelope | None = None,
    transport: TransportOutcomeReference | None = None,
    search_configuration_status: ParserOutcomeStatus
    | TransportOutcomeStatus
    | ReferenceOutcomeStatus
    | CompatibilityProfileLifecycleStatus
    | CompatibilityChangeClass
    | SourceBoundaryStatus = ParserOutcomeStatus.USABLE_RESPONSE,
    parser_status: ParserOutcomeStatus | None = ParserOutcomeStatus.USABLE_RESPONSE,
    reference_status: ReferenceOutcomeStatus | None = None,
    source_reference: ParserSourceReference | None = None,
    source_boundary_outcome: SourceBoundaryOutcome | None = None,
    transport_response_classification: TransportResponseClassificationOutcome | None = None,
    normalized_filters: tuple[str, ...] = (),
    normalized_geography_candidates: tuple[str, ...] = (),
    normalized_category_candidates: tuple[str, ...] = (),
    sort_context_reference: str | None = None,
    candidate_notes: tuple[str, ...] = (),
    parameter_notes: tuple[str, ...] = (),
    multivalue_rule_notes: tuple[str, ...] = (),
    multivalue_outcome_notes: tuple[str, ...] = (),
) -> SyntheticFixtureCase:
    effective_profile = profile if profile is not None else _PROFILE_SEARCH_CONFIGURATION
    effective_request = request if request is not None else _REQUEST_MULTIVALUE_SAFE_NORMALIZATION
    effective_transport = (
        transport if transport is not None else _TRANSPORT_MULTIVALUE_SAFE_NORMALIZATION
    )
    effective_source_reference = (
        source_reference
        if source_reference is not None
        else _MULTIVALUE_SAFE_NORMALIZATION_SOURCE_REFERENCE
    )
    effective_source_boundary_outcome = (
        source_boundary_outcome
        if source_boundary_outcome is not None
        else _MULTIVALUE_SAFE_NORMALIZATION_BOUNDARY
    )
    warnings: tuple[ParserWarning, ...] = (
        (
            ParserWarning(
                code=warning_code,
                message=warning_message,
            ),
        )
        if warning_code is not None and warning_message is not None
        else ()
    )
    normalization = _multivalue_normalization_outcome(
        f"{fixture_id}::normalization",
        parameter_key,
        repeated_values,
        status=multivalue_status,
        preservation_mode=preservation_mode,
        normalized_values=normalized_values,
        loss_reason=loss_reason,
        compatibility_profile=effective_profile,
        source_boundary_outcome=effective_source_boundary_outcome,
        transport_response_classification=transport_response_classification,
        rule_notes=multivalue_rule_notes,
        outcome_notes=multivalue_outcome_notes,
        warnings=warnings,
        evidence_suffix=evidence_suffix,
    )
    parameter = _search_configuration_parameter_candidate(
        parameter_key,
        parameter_value=parameter_value,
        field_status=parameter_field_status,
        value_kind=parameter_value_kind,
        repeated_values=repeated_values,
        multivalue_normalization=normalization,
        evidence_suffix=evidence_suffix,
        warnings=warnings,
        notes=parameter_notes,
    )
    candidate = _search_configuration_candidate(
        candidate_id if candidate_id is not None else f"{fixture_id.lower()}::candidate",
        extraction_field,
        field_status=candidate_field_status,
        value_kind=candidate_value_kind,
        parameter_candidates=(parameter,),
        evidence_suffix=evidence_suffix,
        warnings=warnings,
        notes=candidate_notes,
    )
    return _search_configuration_fixture(
        fixture_id,
        summary,
        status=search_configuration_status,
        evidence_suffix=evidence_suffix,
        profile=effective_profile,
        request=effective_request,
        transport=effective_transport,
        normalized_filters=normalized_filters,
        normalized_geography_candidates=normalized_geography_candidates,
        normalized_category_candidates=normalized_category_candidates,
        sort_context_reference=sort_context_reference,
        search_configuration_candidates=(candidate,),
        parameter_candidates=(parameter,),
        warnings=warnings,
        parser_status=parser_status,
        reference_status=reference_status,
        transport_response_classification=transport_response_classification,
        source_reference=effective_source_reference,
        source_boundary_outcome=effective_source_boundary_outcome,
    )


def _search_configuration_parameter_candidate(
    parameter_key: str,
    *,
    parameter_value: str | None = None,
    field_status: SearchConfigurationFieldStatus = SearchConfigurationFieldStatus.EVIDENCE_BOUND,
    value_kind: SearchConfigurationValueKind = SearchConfigurationValueKind.KEY_VALUE_PAIR,
    repeated_values: tuple[str, ...] = (),
    multivalue_normalization: MultivalueNormalizationOutcome | None = None,
    evidence_suffix: str,
    warnings: tuple[ParserWarning, ...] = (),
    notes: tuple[str, ...] = (),
) -> SearchConfigurationParameterCandidate:
    return SearchConfigurationParameterCandidate(
        parameter_key=parameter_key,
        parameter_value=parameter_value,
        field_status=field_status,
        value_kind=value_kind,
        repeated_values=repeated_values,
        multivalue_normalization=multivalue_normalization,
        evidence_references=(
            ParserEvidenceReference(
                reference_id=f"fx::{evidence_suffix}::parameter::{parameter_key}",
                evidence_kind="search-configuration-parameter",
            ),
        ),
        warnings=warnings,
        notes=notes,
    )


def _search_configuration_candidate(
    candidate_id: str,
    extraction_field: SearchConfigurationExtractionField,
    *,
    field_status: SearchConfigurationFieldStatus,
    value_kind: SearchConfigurationValueKind,
    parameter_candidates: tuple[SearchConfigurationParameterCandidate, ...] = (),
    evidence_suffix: str,
    warnings: tuple[ParserWarning, ...] = (),
    notes: tuple[str, ...] = (),
) -> SearchConfigurationCandidate:
    return SearchConfigurationCandidate(
        candidate_id=candidate_id,
        extraction_field=extraction_field,
        field_status=field_status,
        value_kind=value_kind,
        parameter_candidates=parameter_candidates,
        evidence_references=(
            ParserEvidenceReference(
                reference_id=f"fx::{evidence_suffix}::candidate::{candidate_id}",
                evidence_kind="search-configuration-candidate",
            ),
        ),
        warnings=warnings,
        notes=notes,
    )


def _search_configuration_fixture(
    fixture_id: str,
    summary: str,
    *,
    status: (
        ParserOutcomeStatus
        | TransportOutcomeStatus
        | ReferenceOutcomeStatus
        | CompatibilityProfileLifecycleStatus
        | CompatibilityChangeClass
        | SourceBoundaryStatus
    ) = ParserOutcomeStatus.USABLE_RESPONSE,
    evidence_suffix: str,
    profile: ParserCompatibilityProfile | None = None,
    request: ParserRequestEnvelope | None = None,
    transport: TransportOutcomeReference | None = None,
    normalized_geography_candidates: tuple[str, ...] = (),
    normalized_category_candidates: tuple[str, ...] = (),
    normalized_filters: tuple[str, ...] = (),
    sort_context_reference: str | None = None,
    search_configuration_candidates: tuple[SearchConfigurationCandidate, ...] = (),
    parameter_candidates: tuple[SearchConfigurationParameterCandidate, ...] = (),
    warnings: tuple[ParserWarning, ...] = (),
    parser_status: ParserOutcomeStatus | None = ParserOutcomeStatus.USABLE_RESPONSE,
    reference_status: ReferenceOutcomeStatus | None = None,
    transport_response_classification: TransportResponseClassificationOutcome | None = None,
    source_reference: ParserSourceReference | None = None,
    source_boundary_outcome: SourceBoundaryOutcome | None = None,
) -> SyntheticFixtureCase:
    effective_profile = profile if profile is not None else _PROFILE_SEARCH_CONFIGURATION
    effective_request = request if request is not None else _REQUEST_SEARCH_CONFIGURATION
    effective_transport = transport if transport is not None else _TRANSPORT_SEARCH_CONFIGURATION
    effective_source_reference = (
        source_reference if source_reference is not None else _SEARCH_CONFIG_SOURCE_REFERENCE
    )
    effective_source_boundary_outcome = (
        source_boundary_outcome
        if source_boundary_outcome is not None
        else _SEARCH_CONFIG_SOURCE_BOUNDARY
    )
    search_configuration_evidence = _search_configuration_evidence(
        f"fx-apa06-evidence-{evidence_suffix}",
        effective_request,
        effective_transport,
        effective_profile,
        source_reference=effective_source_reference,
        source_boundary_outcome=effective_source_boundary_outcome,
        evidence_suffix=evidence_suffix,
        notes=(f"synthetic search configuration fixture {fixture_id}",),
    )
    search_configuration_extraction_outcome = _search_configuration(
        f"fx-apa06-extraction-{evidence_suffix}",
        effective_request,
        effective_transport,
        effective_profile,
        status=status,
        evidence_suffix=evidence_suffix,
        normalized_geography_candidates=normalized_geography_candidates,
        normalized_category_candidates=normalized_category_candidates,
        normalized_filters=normalized_filters,
        sort_context_reference=sort_context_reference,
        search_configuration_evidence=search_configuration_evidence,
        search_configuration_candidates=search_configuration_candidates,
        parameter_candidates=parameter_candidates,
        warnings=warnings,
    )
    attempt = _usable_attempt(
        f"fx-apa06-attempt-{evidence_suffix}",
        effective_profile,
        effective_request,
        effective_transport,
        parser_status=parser_status,
        reference_status=reference_status,
        transport_response_classification=transport_response_classification,
        warnings=warnings,
        evidence_suffix=evidence_suffix,
    )
    return _fixture(
        fixture_id,
        summary,
        effective_request,
        effective_transport,
        attempt,
        compatibility_profile=effective_profile,
        search_configuration_extraction_outcome=search_configuration_extraction_outcome,
    )


def _listing_page(
    page_id: str,
    request: ParserRequestEnvelope,
    transport: TransportOutcomeReference,
    profile: ParserCompatibilityProfile,
    *,
    status: (
        ParserOutcomeStatus
        | TransportOutcomeStatus
        | ReferenceOutcomeStatus
        | CompatibilityProfileLifecycleStatus
        | CompatibilityChangeClass
        | SourceBoundaryStatus
    ),
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
    status: (
        ParserOutcomeStatus
        | TransportOutcomeStatus
        | ReferenceOutcomeStatus
        | CompatibilityProfileLifecycleStatus
        | CompatibilityChangeClass
        | SourceBoundaryStatus
    ),
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


def _boundary_fixture(
    fixture_id: str,
    summary: str,
    profile: ParserCompatibilityProfile,
    *,
    request_id: str,
    purpose: str,
    source_reference_id: str,
    source_reference_kind: SourceReferenceKind,
    beacon_source_reference: str,
    bounded_value: str,
    boundary_id: str,
    boundary_status: SourceBoundaryStatus,
    evidence_suffix: str,
    parser_status: ParserOutcomeStatus | None = None,
    host_reference: str | None = None,
    path_reference: str | None = None,
    query_reference: str | None = None,
    header_references: tuple[str, ...] = (),
    extracted_value_references: tuple[str, ...] = (),
    policy_requirements: tuple[SourceBoundaryPolicyRequirement, ...] = (),
    risk_codes: tuple[SourceBoundaryRiskCode, ...] = (),
    warnings: tuple[ParserWarning, ...] = (),
    configuration_extraction: bool = False,
    normalized_geography_candidates: tuple[str, ...] = ("synthetic-city",),
    normalized_category_candidates: tuple[str, ...] = ("synthetic-category",),
    normalized_filter_candidates: tuple[str, ...] = (),
    observed_sort_context_reference: str | None = None,
) -> SyntheticFixtureCase:
    source_reference = _source_reference(
        source_reference_id,
        kind=source_reference_kind,
        beacon_source_reference=beacon_source_reference,
        bounded_value=bounded_value,
        host_reference=host_reference,
        path_reference=path_reference,
        query_reference=query_reference,
        header_references=header_references,
        extracted_value_references=extracted_value_references,
        policy_requirements=policy_requirements,
        risk_codes=risk_codes,
        notes=(f"synthetic source reference {source_reference_id}",),
    )
    boundary_warnings = warnings or (
        ParserWarning(
            code=ParserWarningCode[boundary_status.name],
            message=f"synthetic source boundary {boundary_status.value.lower()}",
            evidence_reference=ParserEvidenceReference(
                reference_id=f"fx::{evidence_suffix}::boundary-warning",
                evidence_kind="source-boundary-warning",
            ),
        ),
    )
    boundary_outcome = _source_boundary(
        boundary_id,
        source_reference,
        status=boundary_status,
        policy_requirements=policy_requirements,
        risk_codes=risk_codes or (SourceBoundaryRiskCode[boundary_status.name],),
        warnings=boundary_warnings,
        notes=(f"synthetic source boundary {boundary_id}",),
    )
    request = _request(
        request_id,
        profile,
        purpose=purpose,
        safe_source_reference=bounded_value,
        source_reference=source_reference,
        source_boundary_outcome=boundary_outcome,
    )
    transport = _transport(
        f"{request_id}::transport",
        status=TransportOutcomeStatus.NOT_SENT,
        request_reference=request.request_id,
        response_reference=None,
        route_reference=None,
        evidence_reference_suffix=evidence_suffix,
    )
    effective_parser_status = parser_status
    if effective_parser_status is None:
        if boundary_status is SourceBoundaryStatus.SOURCE_URL_UNTRUSTED:
            effective_parser_status = ParserOutcomeStatus.USABLE_RESPONSE
        elif boundary_status is SourceBoundaryStatus.SOURCE_URL_CANONICALIZATION_UNPROVEN:
            effective_parser_status = ParserOutcomeStatus.RESULT_AMBIGUOUS
        else:
            effective_parser_status = ParserOutcomeStatus.EXPLICIT_REJECTION
    attempt = _usable_attempt(
        f"{request_id}::attempt",
        profile,
        request,
        transport,
        parser_status=effective_parser_status,
        warnings=boundary_warnings,
        evidence_suffix=evidence_suffix,
    )
    search_source_analysis_outcome = _search_source_analysis(
        f"{request_id}::analysis",
        request,
        transport,
        profile,
        status=boundary_status,
        warnings=boundary_warnings,
        evidence_suffix=evidence_suffix,
    )
    search_configuration_extraction_outcome = None
    if configuration_extraction:
        search_configuration_extraction_outcome = _search_configuration(
            f"{request_id}::configuration",
            request,
            transport,
            profile,
            status=boundary_status,
            normalized_geography_candidates=normalized_geography_candidates,
            normalized_category_candidates=normalized_category_candidates,
            normalized_filters=normalized_filter_candidates,
            sort_context_reference=observed_sort_context_reference,
            warnings=boundary_warnings,
            evidence_suffix=evidence_suffix,
        )
    return _fixture(
        fixture_id,
        summary,
        request,
        transport,
        attempt,
        compatibility_profile=profile,
        search_source_analysis_outcome=search_source_analysis_outcome,
        search_configuration_extraction_outcome=search_configuration_extraction_outcome,
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
    supported_extraction_claims=("stale profile blocks clean empty without current proof",),
    unsupported_extraction_claims=("clean empty current proof",),
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
        "beacon-owned source references are bounded metadata",
        "parser receives safe references only",
        "policy-missing source validation is blocked",
        "canonicalization equivalence is unproven until approved",
        "output does not overwrite beacon source ownership",
    ),
    unsupported_extraction_claims=(
        "live url validation",
        "redirect following",
        "dns probing",
        "shell interpolation from source values",
        "filesystem targeting from source values",
        "network targeting from source values",
    ),
    required_fields=("profile_id", "semantic_version", "reference_ids"),
    completeness_rules=(
        "source boundary outcomes stay explicit",
        "untrusted source values remain external input",
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
        "SOURCE_URL_MALFORMED->SOURCE_URL_MALFORMED",
        "SOURCE_URL_UNSUPPORTED->SOURCE_URL_UNSUPPORTED",
        "SOURCE_URL_POLICY_MISSING->SOURCE_URL_POLICY_MISSING",
        "SOURCE_URL_REDIRECT_POLICY_BLOCKED->SOURCE_URL_REDIRECT_POLICY_BLOCKED",
        "SOURCE_URL_DNS_POLICY_BLOCKED->SOURCE_URL_DNS_POLICY_BLOCKED",
    ),
    fixture_ids=(
        "FX-APA04-BEACON-OWNED-SOURCE-REFERENCE-001",
        "FX-APA04-MALFORMED-SOURCE-BLOCKED-001",
        "FX-APA04-UNSUPPORTED-SOURCE-BLOCKED-001",
        "FX-APA04-POLICY-MISSING-SOURCE-BLOCKED-001",
        "FX-APA04-REDIRECT-POLICY-BLOCKED-001",
        "FX-APA04-DNS-POLICY-BLOCKED-001",
        "FX-APA04-CANONICALIZATION-UNPROVEN-WARNING-001",
        "FX-APA04-SHELL-INTERPOLATION-BLOCKED-001",
        "FX-APA04-FILESYSTEM-TARGET-BLOCKED-001",
        "FX-APA04-NETWORK-TARGET-BLOCKED-001",
        "FX-APA04-PARSER-OUTPUT-NOT-OVERWRITING-BEACON-SOURCE-001",
    ),
    acceptance_matrix_rows=(
        "APA04::BEACON_OWNED::ACCEPTED_UNTRUSTED",
        "APA04::MALFORMED::BLOCK",
        "APA04::UNSUPPORTED::BLOCK",
        "APA04::POLICY_MISSING::BLOCK",
        "APA04::REDIRECT_POLICY::BLOCK",
        "APA04::DNS_POLICY::BLOCK",
        "APA04::CANONICALIZATION::WARN",
        "APA04::SHELL_TARGET::BLOCK",
        "APA04::FILESYSTEM_TARGET::BLOCK",
        "APA04::NETWORK_TARGET::BLOCK",
        "APA04::OUTPUT_OWNERSHIP::PRESERVED",
    ),
)

_PROFILE_SEARCH_CONFIGURATION = _profile(
    "fx-apa06-profile-search-configuration",
    evidence_suffix="apa06-search-configuration",
    supported_extraction_claims=(
        "evidence-bound geography candidate extraction",
        "evidence-bound category candidate extraction",
        "evidence-bound price bound candidate extraction",
        "structured filter key/value candidates are preserved",
        "repeated values are preserved as collections",
        "sort and pagination context remain evidence-bound candidates",
        "unsupported, ambiguous, lossy or policy-gated extraction stays explicit",
    ),
    unsupported_extraction_claims=(
        "user-editable filter authority",
        "country-wide activation policy",
        "beacon snapshot acceptance",
        "live pagination",
        "raw query rewrite",
        "filter catalog implementation",
        "live validation",
    ),
    required_fields=("profile_id", "semantic_version", "reference_ids"),
    completeness_rules=(
        "search configuration extraction stays evidence-bound",
        "compatibility profile and source boundary gate confidence",
        "unsupported and ambiguous parameters remain explicit",
    ),
    warning_mappings=(
        "GEOGRAPHY_CANDIDATE_EVIDENCE_BOUND->EVIDENCE_BOUND",
        "CATEGORY_CANDIDATE_EVIDENCE_BOUND->EVIDENCE_BOUND",
        "PRICE_BOUNDS_CANDIDATE_EVIDENCE_BOUND->EVIDENCE_BOUND",
        "STRUCTURED_FILTER_CANDIDATE_EVIDENCE_BOUND->EVIDENCE_BOUND",
        "MULTIVALUE_PARAMETER_PRESERVED->PRESERVED",
        "UNSUPPORTED_PARAMETER_EXPLICIT->UNSUPPORTED",
        "AMBIGUOUS_PARAMETER_EXPLICIT->AMBIGUOUS",
        "LOSSY_NORMALIZATION_BLOCKED->BLOCKED",
        "SORT_CONTEXT_UNPROVEN->UNPROVEN",
        "PAGINATION_CONTEXT_BLOCKED->BLOCKED",
        "COUNTRY_WIDE_POLICY_GATED->POLICY_GATED",
        "FILTER_EDITABILITY_NOT_DECLARED->POLICY_GATED",
        "BEACON_SNAPSHOT_ACCEPTANCE_NOT_PERFORMED->POLICY_GATED",
    ),
    error_mappings=(
        "UNSUPPORTED_PARAMETER_EXPLICIT->UNSUPPORTED",
        "AMBIGUOUS_PARAMETER_EXPLICIT->AMBIGUOUS",
        "LOSSY_NORMALIZATION_BLOCKED->BLOCKED",
        "PAGINATION_CONTEXT_BLOCKED->BLOCKED",
    ),
    fixture_ids=(
        "FX-APA06-GEOGRAPHY-CANDIDATE-001",
        "FX-APA06-CATEGORY-CANDIDATE-001",
        "FX-APA06-PRICE-BOUNDS-CANDIDATE-001",
        "FX-APA06-STRUCTURED-FILTER-KV-CANDIDATE-001",
        "FX-APA06-REPEATED-MULTIVALUE-PARAM-PRESERVED-001",
        "FX-APA06-UNSUPPORTED-PARAMETER-WARNING-001",
        "FX-APA06-AMBIGUOUS-PARAMETER-WARNING-001",
        "FX-APA06-LOSSY-NORMALIZATION-BLOCKED-001",
        "FX-APA06-SORT-CONTEXT-UNPROVEN-001",
        "FX-APA06-PAGINATION-CONTEXT-BLOCKED-001",
        "FX-APA06-COUNTRY-WIDE-CANDIDATE-POLICY-GATED-001",
        "FX-APA06-FILTER-EDITABILITY-NOT-DECLARED-001",
        "FX-APA06-BEACON-SNAPSHOT-ACCEPTANCE-NOT-PERFORMED-001",
    ),
    acceptance_matrix_rows=(
        "APA06::GEOGRAPHY::EVIDENCE_BOUND",
        "APA06::CATEGORY::EVIDENCE_BOUND",
        "APA06::PRICE_BOUNDS::EVIDENCE_BOUND",
        "APA06::STRUCTURED_FILTER::PRESERVED",
        "APA06::MULTIVALUE::PRESERVED",
        "APA06::UNSUPPORTED_PARAMETER::EXPLICIT",
        "APA06::AMBIGUOUS_PARAMETER::EXPLICIT",
        "APA06::LOSSY_NORMALIZATION::BLOCKED",
        "APA06::SORT_CONTEXT::UNPROVEN",
        "APA06::PAGINATION_CONTEXT::BLOCKED",
        "APA06::COUNTRY_WIDE::POLICY_GATED",
        "APA06::FILTER_EDITABILITY::NOT_DECLARED",
        "APA06::BEACON_SNAPSHOT_ACCEPTANCE::NOT_PERFORMED",
    ),
)


_RULE_TRANSPORT_GATE = _classification_rule(
    "fx-apa05-rule-transport-gate",
    summary="transport success alone is not parser success",
    required_transport_statuses=(
        TransportOutcomeStatus.NOT_SENT,
        TransportOutcomeStatus.TRANSPORT_UNAVAILABLE,
        TransportOutcomeStatus.TRANSPORT_AMBIGUOUS,
        TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
    ),
    required_response_completeness_statuses=(ResponseCompletenessStatus.UNVERIFIED,),
    notes=(
        "transport success alone is insufficient",
        "SENT_SUCCESS_RESPONSE is not parser success until content validation completes",
    ),
)
_RULE_USABLE_CURRENT_PROFILE = _classification_rule(
    "fx-apa05-rule-usable-current-profile",
    summary="usable response requires current profile proof and validated structure",
    required_transport_statuses=(TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,),
    required_parser_statuses=(ParserOutcomeStatus.USABLE_RESPONSE,),
    required_provider_evidence_classes=(ProviderResponseEvidenceClass.USABLE_RESPONSE,),
    required_response_completeness_statuses=(ResponseCompletenessStatus.COMPLETE,),
    requires_current_profile_proof=True,
    notes=(
        "clean empty is blocked without approved current profile proof",
        "parser success is not scan business success",
    ),
)
_RULE_PROVIDER_REJECTION = _classification_rule(
    "fx-apa05-rule-provider-rejection",
    summary="explicit provider rejection stays explicit",
    required_transport_statuses=(TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,),
    required_parser_statuses=(ParserOutcomeStatus.EXPLICIT_REJECTION,),
    required_provider_evidence_classes=(ProviderResponseEvidenceClass.EXPLICIT_REJECTION,),
    required_response_completeness_statuses=(ResponseCompletenessStatus.COMPLETE,),
    notes=("explicit rejection must not be normalized into empty success",),
)
_RULE_RESTRICTED = _classification_rule(
    "fx-apa05-rule-restricted",
    summary="rate or access restrictions stay explicit",
    required_transport_statuses=(TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,),
    required_parser_statuses=(ParserOutcomeStatus.RATE_OR_ACCESS_RESTRICTED,),
    required_provider_evidence_classes=(ProviderResponseEvidenceClass.RATE_OR_ACCESS_RESTRICTED,),
    required_response_completeness_statuses=(ResponseCompletenessStatus.COMPLETE,),
    required_response_restriction_signals=(
        ResponseRestrictionSignal.RATE_LIMIT,
        ResponseRestrictionSignal.ACCESS_RESTRICTED,
    ),
    notes=("restriction signals must not be hidden as empty",),
)
_RULE_CAPTCHA = _classification_rule(
    "fx-apa05-rule-captcha",
    summary="captcha or challenge stays explicit",
    required_transport_statuses=(TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,),
    required_parser_statuses=(ParserOutcomeStatus.CAPTCHA_OR_CHALLENGE,),
    required_provider_evidence_classes=(ProviderResponseEvidenceClass.CAPTCHA_OR_CHALLENGE,),
    required_response_completeness_statuses=(ResponseCompletenessStatus.COMPLETE,),
    required_response_restriction_signals=(
        ResponseRestrictionSignal.CAPTCHA,
        ResponseRestrictionSignal.CHALLENGE,
    ),
    notes=("captcha/challenge is an explicit restriction state",),
)
_RULE_STRUCTURE_FAILURE = _classification_rule(
    "fx-apa05-rule-structure-failure",
    summary="malformed, incomplete and unsupported structure remain explicit",
    required_transport_statuses=(TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,),
    required_parser_statuses=(
        ParserOutcomeStatus.MALFORMED_RESPONSE,
        ParserOutcomeStatus.INCOMPLETE_RESPONSE,
        ParserOutcomeStatus.UNSUPPORTED_STRUCTURE,
    ),
    required_provider_evidence_classes=(
        ProviderResponseEvidenceClass.MALFORMED_RESPONSE,
        ProviderResponseEvidenceClass.INCOMPLETE_RESPONSE,
        ProviderResponseEvidenceClass.UNSUPPORTED_STRUCTURE,
    ),
    required_response_completeness_statuses=(
        ResponseCompletenessStatus.UNVERIFIED,
        ResponseCompletenessStatus.INCOMPLETE,
        ResponseCompletenessStatus.PARTIAL,
    ),
    notes=("malformed, incomplete and unsupported responses are never clean empty",),
)
_RULE_REFERENCE_STATE = _classification_rule(
    "fx-apa05-rule-reference-state",
    summary="reference state remains explicit during response classification",
    required_reference_statuses=(
        ReferenceOutcomeStatus.REFERENCE_STALE,
        ReferenceOutcomeStatus.REFERENCE_MISSING,
        ReferenceOutcomeStatus.REFERENCE_DISPUTED,
    ),
    required_response_completeness_statuses=(ResponseCompletenessStatus.UNVERIFIED,),
    notes=("reference stale, missing and disputed states must not collapse into generic success",),
)
_RULE_PARTIAL = _classification_rule(
    "fx-apa05-rule-partial",
    summary="partial outcomes remain explicit",
    required_transport_statuses=(TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,),
    required_parser_statuses=(ParserOutcomeStatus.PARTIAL,),
    required_provider_evidence_classes=(ProviderResponseEvidenceClass.PARTIAL,),
    required_response_completeness_statuses=(ResponseCompletenessStatus.PARTIAL,),
    notes=("partial page or batch outcomes must not become generic success",),
)
_RULE_RESULT_AMBIGUOUS = _classification_rule(
    "fx-apa05-rule-result-ambiguous",
    summary="ambiguous result remains explicit",
    required_transport_statuses=(TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,),
    required_parser_statuses=(ParserOutcomeStatus.RESULT_AMBIGUOUS,),
    required_provider_evidence_classes=(ProviderResponseEvidenceClass.RESULT_AMBIGUOUS,),
    required_response_completeness_statuses=(ResponseCompletenessStatus.AMBIGUOUS,),
    notes=("recognized substring or non-empty body alone is insufficient",),
)
_RULE_CLEAN_EMPTY_BLOCKED = _classification_rule(
    "fx-apa05-rule-clean-empty-blocked",
    summary="clean empty is blocked without current profile proof",
    required_transport_statuses=(TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,),
    required_reference_statuses=(ReferenceOutcomeStatus.REFERENCE_MISSING,),
    required_provider_evidence_classes=(ProviderResponseEvidenceClass.EMPTY_WITHOUT_PROOF,),
    required_response_completeness_statuses=(ResponseCompletenessStatus.EMPTY_BLOCKED,),
    requires_current_profile_proof=True,
    notes=("clean empty cannot be produced without proof, structure and explicit usable response",),
)
_RULE_HTTP_200_NON_EMPTY_NOT_ENOUGH = _classification_rule(
    "fx-apa05-rule-http-200-non-empty-not-enough",
    summary="http 200 and non-empty body are not enough by themselves",
    required_transport_statuses=(TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,),
    required_provider_evidence_classes=(ProviderResponseEvidenceClass.BODY_PRESENT_UNCLASSIFIED,),
    required_response_completeness_statuses=(ResponseCompletenessStatus.UNVERIFIED,),
    notes=(
        "HTTP 200 / non-empty body / parseable body / recognized substring alone is insufficient",
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

_SEARCH_CONFIG_SOURCE_REFERENCE = _source_reference(
    "fx-apa06-source-reference-search-configuration",
    kind=SourceReferenceKind.SAFE_REFERENCE,
    beacon_source_reference="source-ref:beacon-revision-060",
    bounded_value="source-ref:beacon-revision-060",
    host_reference="provider.example",
    path_reference="/search",
    query_reference="q=synthetic-search-config",
    policy_requirements=(
        SourceBoundaryPolicyRequirement.HOST_POLICY_REQUIRED,
        SourceBoundaryPolicyRequirement.PATH_POLICY_REQUIRED,
        SourceBoundaryPolicyRequirement.QUERY_POLICY_REQUIRED,
    ),
    risk_codes=(SourceBoundaryRiskCode.SOURCE_URL_UNTRUSTED,),
    notes=("synthetic search configuration source reference",),
)
_SEARCH_CONFIG_SOURCE_BOUNDARY = _source_boundary(
    "fx-apa06-boundary-search-configuration",
    _SEARCH_CONFIG_SOURCE_REFERENCE,
    status=SourceBoundaryStatus.SOURCE_URL_UNTRUSTED,
    policy_requirements=(
        SourceBoundaryPolicyRequirement.HOST_POLICY_REQUIRED,
        SourceBoundaryPolicyRequirement.PATH_POLICY_REQUIRED,
        SourceBoundaryPolicyRequirement.QUERY_POLICY_REQUIRED,
    ),
    risk_codes=(SourceBoundaryRiskCode.SOURCE_URL_UNTRUSTED,),
)
_REQUEST_SEARCH_CONFIGURATION = _request(
    "fx-apa06-request-search-configuration",
    _PROFILE_SEARCH_CONFIGURATION,
    purpose="search-configuration-extraction",
    safe_source_reference="source-ref:beacon-revision-060",
    source_reference=_SEARCH_CONFIG_SOURCE_REFERENCE,
    source_boundary_outcome=_SEARCH_CONFIG_SOURCE_BOUNDARY,
    requested_page_numbers=(1,),
)
_TRANSPORT_SEARCH_CONFIGURATION = _transport(
    "fx-apa06-transport-search-configuration",
    status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
    request_reference=_REQUEST_SEARCH_CONFIGURATION.request_id,
    response_reference="response::synthetic::search-configuration",
    route_reference="route::synthetic",
    evidence_reference_suffix="apa06-search-configuration",
)

_MULTIVALUE_SAFE_NORMALIZATION_SOURCE_REFERENCE = _source_reference(
    "fx-apa07-source-reference-multivalue-safe-normalization",
    kind=SourceReferenceKind.SAFE_REFERENCE,
    beacon_source_reference="source-ref:beacon-revision-070",
    bounded_value="source-ref:beacon-revision-070",
    host_reference="provider.example",
    path_reference="/search",
    query_reference="q=synthetic-multivalue-safe-normalization",
    policy_requirements=(
        SourceBoundaryPolicyRequirement.HOST_POLICY_REQUIRED,
        SourceBoundaryPolicyRequirement.PATH_POLICY_REQUIRED,
        SourceBoundaryPolicyRequirement.QUERY_POLICY_REQUIRED,
    ),
    risk_codes=(SourceBoundaryRiskCode.SOURCE_URL_UNTRUSTED,),
    notes=("synthetic multivalue normalization source reference",),
)
_MULTIVALUE_SAFE_NORMALIZATION_BOUNDARY = _source_boundary(
    "fx-apa07-boundary-multivalue-safe-normalization",
    _MULTIVALUE_SAFE_NORMALIZATION_SOURCE_REFERENCE,
    status=SourceBoundaryStatus.SOURCE_URL_UNTRUSTED,
    policy_requirements=(
        SourceBoundaryPolicyRequirement.HOST_POLICY_REQUIRED,
        SourceBoundaryPolicyRequirement.PATH_POLICY_REQUIRED,
        SourceBoundaryPolicyRequirement.QUERY_POLICY_REQUIRED,
    ),
    risk_codes=(SourceBoundaryRiskCode.SOURCE_URL_UNTRUSTED,),
)
_REQUEST_MULTIVALUE_SAFE_NORMALIZATION = _request(
    "fx-apa07-request-multivalue-safe-normalization",
    _PROFILE_SEARCH_CONFIGURATION,
    purpose="search-configuration-extraction",
    safe_source_reference="source-ref:beacon-revision-070",
    source_reference=_MULTIVALUE_SAFE_NORMALIZATION_SOURCE_REFERENCE,
    source_boundary_outcome=_MULTIVALUE_SAFE_NORMALIZATION_BOUNDARY,
    requested_page_numbers=(1,),
)
_TRANSPORT_MULTIVALUE_SAFE_NORMALIZATION = _transport(
    "fx-apa07-transport-multivalue-safe-normalization",
    status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
    request_reference=_REQUEST_MULTIVALUE_SAFE_NORMALIZATION.request_id,
    response_reference="response::synthetic::multivalue-safe-normalization",
    route_reference="route::synthetic",
    evidence_reference_suffix="apa07-multivalue-safe-normalization",
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

_CARD_TIER1 = _listing_card(
    "fx-apa02-card-tier1",
    field_candidates=_tier_1_listing_field_candidates("tier1", _PROFILE_TIER1),
    evidence_suffix="tier1",
)
_CARD_CURRENT_REFERENCE = _listing_card(
    "fx-apa03-card-current-reference",
    field_candidates=_tier_1_listing_field_candidates(
        "apa03-current-reference", _PROFILE_CURRENT_REFERENCE
    ),
    evidence_suffix="apa03-current-reference",
)
_CARD_OPTIONAL_PHONE = _listing_card(
    "fx-apa02-card-optional-phone",
    field_candidates=(
        *_tier_1_listing_field_candidates("optional-phone", _PROFILE_OPTIONAL),
        *_tier_3_phone_field_candidates(
            "optional-phone",
            _PROFILE_OPTIONAL,
            availability=ListingFieldAvailability.PROOF_GATED,
        ),
    ),
    evidence_suffix="optional-phone",
)
_CARD_OPTIONAL_UNAVAILABLE = _listing_card(
    "fx-apa02-card-optional-unavailable",
    field_candidates=(
        *_tier_1_listing_field_candidates("optional-unavailable", _PROFILE_OPTIONAL),
        *_tier_2_detail_field_candidates(
            "optional-unavailable",
            _PROFILE_OPTIONAL,
            availability=ListingFieldAvailability.PROVEN_UNAVAILABLE,
        ),
    ),
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
    warnings=_CARD_OPTIONAL_UNAVAILABLE.warnings,
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

_CARD_APA08_TIER1_PROVEN = _listing_card(
    "fx-apa08-card-tier1-proven",
    field_candidates=_tier_1_listing_field_candidates(
        "apa08-tier1-proven", _PROFILE_CURRENT_REFERENCE
    ),
    evidence_suffix="apa08-tier1-proven",
)
_LISTING_APA08_TIER1_PROVEN = _listing_candidate(
    "fx-apa08-listing-tier1-proven",
    _CARD_APA08_TIER1_PROVEN,
    evidence_suffix="apa08-tier1-proven",
)

_CARD_APA08_OPTIONAL_DETAIL_UNAVAILABLE = _listing_card(
    "fx-apa08-card-optional-detail-fields-unavailable",
    field_candidates=(
        *_tier_1_listing_field_candidates(
            "apa08-optional-detail-fields-unavailable", _PROFILE_CURRENT_REFERENCE
        ),
        *_tier_2_detail_field_candidates(
            "apa08-optional-detail-fields-unavailable",
            _PROFILE_CURRENT_REFERENCE,
            availability=ListingFieldAvailability.PROVEN_UNAVAILABLE,
        ),
    ),
    evidence_suffix="apa08-optional-detail-fields-unavailable",
    warnings=(
        ParserWarning(
            code=ParserWarningCode.DESCRIPTION_UNAVAILABLE,
            message="description evidence unavailable in synthetic case",
        ),
        ParserWarning(
            code=ParserWarningCode.SELLER_UNAVAILABLE,
            message="seller evidence unavailable in synthetic case",
        ),
        ParserWarning(
            code=ParserWarningCode.RATING_UNAVAILABLE,
            message="rating evidence unavailable in synthetic case",
        ),
    ),
)
_LISTING_APA08_OPTIONAL_DETAIL_UNAVAILABLE = _listing_candidate(
    "fx-apa08-listing-optional-detail-fields-unavailable",
    _CARD_APA08_OPTIONAL_DETAIL_UNAVAILABLE,
    evidence_suffix="apa08-optional-detail-fields-unavailable",
    warnings=_CARD_APA08_OPTIONAL_DETAIL_UNAVAILABLE.warnings,
)

_CARD_APA08_PHONE_VALUE_PROOF_GATED = _listing_card(
    "fx-apa08-card-phone-value-proof-gated",
    field_candidates=(
        *_tier_1_listing_field_candidates(
            "apa08-phone-value-proof-gated", _PROFILE_CURRENT_REFERENCE
        ),
        *_tier_3_phone_field_candidates(
            "apa08-phone-value-proof-gated",
            _PROFILE_CURRENT_REFERENCE,
            availability=ListingFieldAvailability.PROOF_GATED,
        ),
    ),
    evidence_suffix="apa08-phone-value-proof-gated",
    warnings=(
        ParserWarning(
            code=ParserWarningCode.PHONE_UNAVAILABLE,
            message="phone value remains proof-gated and empty",
        ),
    ),
)
_LISTING_APA08_PHONE_VALUE_PROOF_GATED = _listing_candidate(
    "fx-apa08-listing-phone-value-proof-gated",
    _CARD_APA08_PHONE_VALUE_PROOF_GATED,
    evidence_suffix="apa08-phone-value-proof-gated",
    warnings=_CARD_APA08_PHONE_VALUE_PROOF_GATED.warnings,
)

_AMBIGUOUS_APA08_FIELD = _listing_field_candidate(
    "fx-apa08-ambiguous-seller-rating",
    ListingFieldFamily.SELLER_RATING,
    ListingFieldTier.TIER_2_LISTING_DETAIL,
    ListingFieldAvailability.AMBIGUOUS,
    ListingFieldQuality.UNVERIFIED,
    compatibility_profile=_PROFILE_CURRENT_REFERENCE,
    evidence_suffix="apa08-optional-field-ambiguous-warning",
    warnings=(
        ParserWarning(
            code=ParserWarningCode.FIELD_CANDIDATE_OPTIONAL,
            message="ambiguous field candidate remains explicit",
        ),
    ),
)
_CARD_APA08_OPTIONAL_FIELD_AMBIGUOUS = _listing_card(
    "fx-apa08-card-optional-field-ambiguous-warning",
    field_candidates=(
        *_tier_1_listing_field_candidates(
            "apa08-optional-field-ambiguous-warning", _PROFILE_CURRENT_REFERENCE
        ),
        _AMBIGUOUS_APA08_FIELD,
    ),
    evidence_suffix="apa08-optional-field-ambiguous-warning",
    warnings=_AMBIGUOUS_APA08_FIELD.warnings,
)
_LISTING_APA08_OPTIONAL_FIELD_AMBIGUOUS = _listing_candidate(
    "fx-apa08-listing-optional-field-ambiguous-warning",
    _CARD_APA08_OPTIONAL_FIELD_AMBIGUOUS,
    evidence_suffix="apa08-optional-field-ambiguous-warning",
    status=ListingCandidateStatus.AMBIGUOUS,
    warnings=_CARD_APA08_OPTIONAL_FIELD_AMBIGUOUS.warnings,
)

_FIELD_PROVENANCE_REQUIRED_FIELD = _listing_field_candidate(
    "fx-apa08-field-provenance-required-seller",
    ListingFieldFamily.SELLER,
    ListingFieldTier.TIER_2_LISTING_DETAIL,
    ListingFieldAvailability.PROVEN_AVAILABLE,
    ListingFieldQuality.PROFILE_PROVEN,
    value="Synthetic seller",
    compatibility_profile=_PROFILE_CURRENT_REFERENCE,
    evidence_suffix="apa08-field-provenance-required",
)
_CARD_APA08_FIELD_PROVENANCE_REQUIRED = _listing_card(
    "fx-apa08-card-field-provenance-required",
    field_candidates=(
        *_tier_1_listing_field_candidates(
            "apa08-field-provenance-required", _PROFILE_CURRENT_REFERENCE
        ),
        _FIELD_PROVENANCE_REQUIRED_FIELD,
    ),
    evidence_suffix="apa08-field-provenance-required",
)
_LISTING_APA08_FIELD_PROVENANCE_REQUIRED = _listing_candidate(
    "fx-apa08-listing-field-provenance-required",
    _CARD_APA08_FIELD_PROVENANCE_REQUIRED,
    evidence_suffix="apa08-field-provenance-required",
)

_CARD_APA08_NO_SCAN_NEWNESS_MUTATION = _listing_card(
    "fx-apa08-card-no-scan-newness-mutation",
    field_candidates=_tier_1_listing_field_candidates(
        "apa08-no-scan-newness-mutation", _PROFILE_CURRENT_REFERENCE
    ),
    evidence_suffix="apa08-no-scan-newness-mutation",
)
_LISTING_APA08_NO_SCAN_NEWNESS_MUTATION = _listing_candidate(
    "fx-apa08-listing-no-scan-newness-mutation",
    _CARD_APA08_NO_SCAN_NEWNESS_MUTATION,
    evidence_suffix="apa08-no-scan-newness-mutation",
)

_CARD_APA08_NO_RAW_PROVIDER_PAYLOAD = _listing_card(
    "fx-apa08-card-no-raw-provider-payload",
    field_candidates=_tier_1_listing_field_candidates(
        "apa08-no-raw-provider-payload", _PROFILE_CURRENT_REFERENCE
    ),
    evidence_suffix="apa08-no-raw-provider-payload",
)
_LISTING_APA08_NO_RAW_PROVIDER_PAYLOAD = _listing_candidate(
    "fx-apa08-listing-no-raw-provider-payload",
    _CARD_APA08_NO_RAW_PROVIDER_PAYLOAD,
    evidence_suffix="apa08-no-raw-provider-payload",
)

_REQUEST_APA08_TIER1_PROVEN = _request(
    "fx-apa08-request-tier1-proven",
    _PROFILE_CURRENT_REFERENCE,
    purpose="page-parse",
    safe_source_reference="source::apa08::tier1-proven",
    requested_page_numbers=(1,),
)
_TRANSPORT_APA08_TIER1_PROVEN = _transport(
    "fx-apa08-transport-tier1-proven",
    status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
    request_reference=_REQUEST_APA08_TIER1_PROVEN.request_id,
    response_reference="response::apa08::tier1-proven",
    route_reference="route::synthetic",
    evidence_reference_suffix="apa08-tier1-proven",
)
_ATTEMPT_APA08_TIER1_PROVEN = _usable_attempt(
    "fx-apa08-attempt-tier1-proven",
    _PROFILE_CURRENT_REFERENCE,
    _REQUEST_APA08_TIER1_PROVEN,
    _TRANSPORT_APA08_TIER1_PROVEN,
    evidence_suffix="apa08-tier1-proven",
)
_PAGE_APA08_TIER1_PROVEN = _listing_page(
    "fx-apa08-page-tier1-proven",
    _REQUEST_APA08_TIER1_PROVEN,
    _TRANSPORT_APA08_TIER1_PROVEN,
    _PROFILE_CURRENT_REFERENCE,
    status=ParserOutcomeStatus.USABLE_RESPONSE,
    candidate=_LISTING_APA08_TIER1_PROVEN,
    card=_CARD_APA08_TIER1_PROVEN,
    evidence_suffix="apa08-tier1-proven",
)

_REQUEST_APA08_OPTIONAL_DETAIL_UNAVAILABLE = _request(
    "fx-apa08-request-optional-detail-fields-unavailable",
    _PROFILE_CURRENT_REFERENCE,
    purpose="page-parse",
    safe_source_reference="source::apa08::optional-detail-fields-unavailable",
    requested_page_numbers=(1,),
)
_TRANSPORT_APA08_OPTIONAL_DETAIL_UNAVAILABLE = _transport(
    "fx-apa08-transport-optional-detail-fields-unavailable",
    status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
    request_reference=_REQUEST_APA08_OPTIONAL_DETAIL_UNAVAILABLE.request_id,
    response_reference="response::apa08::optional-detail-fields-unavailable",
    route_reference="route::synthetic",
    evidence_reference_suffix="apa08-optional-detail-fields-unavailable",
)
_ATTEMPT_APA08_OPTIONAL_DETAIL_UNAVAILABLE = _usable_attempt(
    "fx-apa08-attempt-optional-detail-fields-unavailable",
    _PROFILE_CURRENT_REFERENCE,
    _REQUEST_APA08_OPTIONAL_DETAIL_UNAVAILABLE,
    _TRANSPORT_APA08_OPTIONAL_DETAIL_UNAVAILABLE,
    evidence_suffix="apa08-optional-detail-fields-unavailable",
    warnings=_CARD_APA08_OPTIONAL_DETAIL_UNAVAILABLE.warnings,
)
_PAGE_APA08_OPTIONAL_DETAIL_UNAVAILABLE = _listing_page(
    "fx-apa08-page-optional-detail-fields-unavailable",
    _REQUEST_APA08_OPTIONAL_DETAIL_UNAVAILABLE,
    _TRANSPORT_APA08_OPTIONAL_DETAIL_UNAVAILABLE,
    _PROFILE_CURRENT_REFERENCE,
    status=ParserOutcomeStatus.USABLE_RESPONSE,
    candidate=_LISTING_APA08_OPTIONAL_DETAIL_UNAVAILABLE,
    card=_CARD_APA08_OPTIONAL_DETAIL_UNAVAILABLE,
    evidence_suffix="apa08-optional-detail-fields-unavailable",
    warnings=_CARD_APA08_OPTIONAL_DETAIL_UNAVAILABLE.warnings,
)

_REQUEST_APA08_PHONE_VALUE_PROOF_GATED = _request(
    "fx-apa08-request-phone-value-proof-gated",
    _PROFILE_CURRENT_REFERENCE,
    purpose="page-parse",
    safe_source_reference="source::apa08::phone-value-proof-gated",
    requested_page_numbers=(1,),
)
_TRANSPORT_APA08_PHONE_VALUE_PROOF_GATED = _transport(
    "fx-apa08-transport-phone-value-proof-gated",
    status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
    request_reference=_REQUEST_APA08_PHONE_VALUE_PROOF_GATED.request_id,
    response_reference="response::apa08::phone-value-proof-gated",
    route_reference="route::synthetic",
    evidence_reference_suffix="apa08-phone-value-proof-gated",
)
_ATTEMPT_APA08_PHONE_VALUE_PROOF_GATED = _usable_attempt(
    "fx-apa08-attempt-phone-value-proof-gated",
    _PROFILE_CURRENT_REFERENCE,
    _REQUEST_APA08_PHONE_VALUE_PROOF_GATED,
    _TRANSPORT_APA08_PHONE_VALUE_PROOF_GATED,
    evidence_suffix="apa08-phone-value-proof-gated",
    warnings=_CARD_APA08_PHONE_VALUE_PROOF_GATED.warnings,
)
_PAGE_APA08_PHONE_VALUE_PROOF_GATED = _listing_page(
    "fx-apa08-page-phone-value-proof-gated",
    _REQUEST_APA08_PHONE_VALUE_PROOF_GATED,
    _TRANSPORT_APA08_PHONE_VALUE_PROOF_GATED,
    _PROFILE_CURRENT_REFERENCE,
    status=ParserOutcomeStatus.USABLE_RESPONSE,
    candidate=_LISTING_APA08_PHONE_VALUE_PROOF_GATED,
    card=_CARD_APA08_PHONE_VALUE_PROOF_GATED,
    evidence_suffix="apa08-phone-value-proof-gated",
    warnings=_CARD_APA08_PHONE_VALUE_PROOF_GATED.warnings,
)

_REQUEST_APA08_OPTIONAL_FIELD_AMBIGUOUS = _request(
    "fx-apa08-request-optional-field-ambiguous-warning",
    _PROFILE_CURRENT_REFERENCE,
    purpose="page-parse",
    safe_source_reference="source::apa08::optional-field-ambiguous-warning",
    requested_page_numbers=(1,),
)
_TRANSPORT_APA08_OPTIONAL_FIELD_AMBIGUOUS = _transport(
    "fx-apa08-transport-optional-field-ambiguous-warning",
    status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
    request_reference=_REQUEST_APA08_OPTIONAL_FIELD_AMBIGUOUS.request_id,
    response_reference="response::apa08::optional-field-ambiguous-warning",
    route_reference="route::synthetic",
    evidence_reference_suffix="apa08-optional-field-ambiguous-warning",
)
_ATTEMPT_APA08_OPTIONAL_FIELD_AMBIGUOUS = _usable_attempt(
    "fx-apa08-attempt-optional-field-ambiguous-warning",
    _PROFILE_CURRENT_REFERENCE,
    _REQUEST_APA08_OPTIONAL_FIELD_AMBIGUOUS,
    _TRANSPORT_APA08_OPTIONAL_FIELD_AMBIGUOUS,
    parser_status=ParserOutcomeStatus.RESULT_AMBIGUOUS,
    evidence_suffix="apa08-optional-field-ambiguous-warning",
    warnings=_CARD_APA08_OPTIONAL_FIELD_AMBIGUOUS.warnings,
)
_PAGE_APA08_OPTIONAL_FIELD_AMBIGUOUS = _listing_page(
    "fx-apa08-page-optional-field-ambiguous-warning",
    _REQUEST_APA08_OPTIONAL_FIELD_AMBIGUOUS,
    _TRANSPORT_APA08_OPTIONAL_FIELD_AMBIGUOUS,
    _PROFILE_CURRENT_REFERENCE,
    status=ParserOutcomeStatus.RESULT_AMBIGUOUS,
    candidate=_LISTING_APA08_OPTIONAL_FIELD_AMBIGUOUS,
    card=_CARD_APA08_OPTIONAL_FIELD_AMBIGUOUS,
    evidence_suffix="apa08-optional-field-ambiguous-warning",
    warnings=_CARD_APA08_OPTIONAL_FIELD_AMBIGUOUS.warnings,
)

_REQUEST_APA08_FIELD_PROVENANCE_REQUIRED = _request(
    "fx-apa08-request-field-provenance-required",
    _PROFILE_CURRENT_REFERENCE,
    purpose="page-parse",
    safe_source_reference="source::apa08::field-provenance-required",
    requested_page_numbers=(1,),
)
_TRANSPORT_APA08_FIELD_PROVENANCE_REQUIRED = _transport(
    "fx-apa08-transport-field-provenance-required",
    status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
    request_reference=_REQUEST_APA08_FIELD_PROVENANCE_REQUIRED.request_id,
    response_reference="response::apa08::field-provenance-required",
    route_reference="route::synthetic",
    evidence_reference_suffix="apa08-field-provenance-required",
)
_ATTEMPT_APA08_FIELD_PROVENANCE_REQUIRED = _usable_attempt(
    "fx-apa08-attempt-field-provenance-required",
    _PROFILE_CURRENT_REFERENCE,
    _REQUEST_APA08_FIELD_PROVENANCE_REQUIRED,
    _TRANSPORT_APA08_FIELD_PROVENANCE_REQUIRED,
    evidence_suffix="apa08-field-provenance-required",
)
_PAGE_APA08_FIELD_PROVENANCE_REQUIRED = _listing_page(
    "fx-apa08-page-field-provenance-required",
    _REQUEST_APA08_FIELD_PROVENANCE_REQUIRED,
    _TRANSPORT_APA08_FIELD_PROVENANCE_REQUIRED,
    _PROFILE_CURRENT_REFERENCE,
    status=ParserOutcomeStatus.USABLE_RESPONSE,
    candidate=_LISTING_APA08_FIELD_PROVENANCE_REQUIRED,
    card=_CARD_APA08_FIELD_PROVENANCE_REQUIRED,
    evidence_suffix="apa08-field-provenance-required",
)

_REQUEST_APA08_NO_SCAN_NEWNESS_MUTATION = _request(
    "fx-apa08-request-no-scan-newness-mutation",
    _PROFILE_CURRENT_REFERENCE,
    purpose="page-parse",
    safe_source_reference="source::apa08::no-scan-newness-mutation",
    requested_page_numbers=(1,),
)
_TRANSPORT_APA08_NO_SCAN_NEWNESS_MUTATION = _transport(
    "fx-apa08-transport-no-scan-newness-mutation",
    status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
    request_reference=_REQUEST_APA08_NO_SCAN_NEWNESS_MUTATION.request_id,
    response_reference="response::apa08::no-scan-newness-mutation",
    route_reference="route::synthetic",
    evidence_reference_suffix="apa08-no-scan-newness-mutation",
)
_ATTEMPT_APA08_NO_SCAN_NEWNESS_MUTATION = _usable_attempt(
    "fx-apa08-attempt-no-scan-newness-mutation",
    _PROFILE_CURRENT_REFERENCE,
    _REQUEST_APA08_NO_SCAN_NEWNESS_MUTATION,
    _TRANSPORT_APA08_NO_SCAN_NEWNESS_MUTATION,
    evidence_suffix="apa08-no-scan-newness-mutation",
)
_PAGE_APA08_NO_SCAN_NEWNESS_MUTATION = _listing_page(
    "fx-apa08-page-no-scan-newness-mutation",
    _REQUEST_APA08_NO_SCAN_NEWNESS_MUTATION,
    _TRANSPORT_APA08_NO_SCAN_NEWNESS_MUTATION,
    _PROFILE_CURRENT_REFERENCE,
    status=ParserOutcomeStatus.USABLE_RESPONSE,
    candidate=_LISTING_APA08_NO_SCAN_NEWNESS_MUTATION,
    card=_CARD_APA08_NO_SCAN_NEWNESS_MUTATION,
    evidence_suffix="apa08-no-scan-newness-mutation",
)

_REQUEST_APA08_NO_RAW_PROVIDER_PAYLOAD = _request(
    "fx-apa08-request-no-raw-provider-payload",
    _PROFILE_CURRENT_REFERENCE,
    purpose="page-parse",
    safe_source_reference="source::apa08::no-raw-provider-payload",
    requested_page_numbers=(1,),
)
_TRANSPORT_APA08_NO_RAW_PROVIDER_PAYLOAD = _transport(
    "fx-apa08-transport-no-raw-provider-payload",
    status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
    request_reference=_REQUEST_APA08_NO_RAW_PROVIDER_PAYLOAD.request_id,
    response_reference="response::apa08::no-raw-provider-payload",
    route_reference="route::synthetic",
    evidence_reference_suffix="apa08-no-raw-provider-payload",
)
_ATTEMPT_APA08_NO_RAW_PROVIDER_PAYLOAD = _usable_attempt(
    "fx-apa08-attempt-no-raw-provider-payload",
    _PROFILE_CURRENT_REFERENCE,
    _REQUEST_APA08_NO_RAW_PROVIDER_PAYLOAD,
    _TRANSPORT_APA08_NO_RAW_PROVIDER_PAYLOAD,
    evidence_suffix="apa08-no-raw-provider-payload",
)
_PAGE_APA08_NO_RAW_PROVIDER_PAYLOAD = _listing_page(
    "fx-apa08-page-no-raw-provider-payload",
    _REQUEST_APA08_NO_RAW_PROVIDER_PAYLOAD,
    _TRANSPORT_APA08_NO_RAW_PROVIDER_PAYLOAD,
    _PROFILE_CURRENT_REFERENCE,
    status=ParserOutcomeStatus.USABLE_RESPONSE,
    candidate=_LISTING_APA08_NO_RAW_PROVIDER_PAYLOAD,
    card=_CARD_APA08_NO_RAW_PROVIDER_PAYLOAD,
    evidence_suffix="apa08-no-raw-provider-payload",
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
    _boundary_fixture(
        "FX-APA04-BEACON-OWNED-SOURCE-REFERENCE-001",
        "beacon-owned source reference accepted as untrusted bounded input",
        _PROFILE_SOURCE_BOUNDARY,
        request_id="fx-apa04-request-beacon-owned",
        purpose="source-boundary-analysis",
        source_reference_id="fx-apa04-source-reference-beacon-owned",
        source_reference_kind=SourceReferenceKind.BEACON_OWNED_SUBMISSION,
        beacon_source_reference="source-ref:beacon-revision-001",
        bounded_value="bounded-source-value",
        boundary_id="fx-apa04-boundary-beacon-owned",
        boundary_status=SourceBoundaryStatus.SOURCE_URL_UNTRUSTED,
        evidence_suffix="apa04-beacon-owned",
        parser_status=ParserOutcomeStatus.USABLE_RESPONSE,
        policy_requirements=(
            SourceBoundaryPolicyRequirement.HOST_POLICY_REQUIRED,
            SourceBoundaryPolicyRequirement.PATH_POLICY_REQUIRED,
            SourceBoundaryPolicyRequirement.QUERY_POLICY_REQUIRED,
        ),
        risk_codes=(SourceBoundaryRiskCode.SOURCE_URL_UNTRUSTED,),
    ),
    _boundary_fixture(
        "FX-APA04-MALFORMED-SOURCE-BLOCKED-001",
        "malformed source boundary is rejected explicitly",
        _PROFILE_SOURCE_BOUNDARY,
        request_id="fx-apa04-request-malformed",
        purpose="source-boundary-analysis",
        source_reference_id="fx-apa04-source-reference-malformed",
        source_reference_kind=SourceReferenceKind.EXTERNAL_UNTRUSTED_INPUT,
        beacon_source_reference="source-ref:beacon-revision-002",
        bounded_value="malformed-source-value",
        boundary_id="fx-apa04-boundary-malformed",
        boundary_status=SourceBoundaryStatus.SOURCE_URL_MALFORMED,
        evidence_suffix="apa04-malformed",
        policy_requirements=(
            SourceBoundaryPolicyRequirement.HOST_POLICY_REQUIRED,
            SourceBoundaryPolicyRequirement.PATH_POLICY_REQUIRED,
        ),
        risk_codes=(SourceBoundaryRiskCode.SOURCE_URL_MALFORMED,),
    ),
    _boundary_fixture(
        "FX-APA04-UNSUPPORTED-SOURCE-BLOCKED-001",
        "unsupported source boundary is blocked explicitly",
        _PROFILE_SOURCE_BOUNDARY,
        request_id="fx-apa04-request-unsupported",
        purpose="source-boundary-analysis",
        source_reference_id="fx-apa04-source-reference-unsupported",
        source_reference_kind=SourceReferenceKind.EXTERNAL_UNTRUSTED_INPUT,
        beacon_source_reference="source-ref:beacon-revision-003",
        bounded_value="unsupported-source-value",
        boundary_id="fx-apa04-boundary-unsupported",
        boundary_status=SourceBoundaryStatus.SOURCE_URL_UNSUPPORTED,
        evidence_suffix="apa04-unsupported",
        policy_requirements=(
            SourceBoundaryPolicyRequirement.HOST_POLICY_REQUIRED,
            SourceBoundaryPolicyRequirement.PATH_POLICY_REQUIRED,
            SourceBoundaryPolicyRequirement.QUERY_POLICY_REQUIRED,
        ),
        risk_codes=(SourceBoundaryRiskCode.SOURCE_URL_UNSUPPORTED,),
    ),
    _boundary_fixture(
        "FX-APA04-POLICY-MISSING-SOURCE-BLOCKED-001",
        "missing host path query policy blocks validation",
        _PROFILE_SOURCE_BOUNDARY,
        request_id="fx-apa04-request-policy-missing",
        purpose="source-boundary-analysis",
        source_reference_id="fx-apa04-source-reference-policy-missing",
        source_reference_kind=SourceReferenceKind.EXTERNAL_UNTRUSTED_INPUT,
        beacon_source_reference="source-ref:beacon-revision-004",
        bounded_value="bounded-source-value::policy-missing",
        boundary_id="fx-apa04-boundary-policy-missing",
        boundary_status=SourceBoundaryStatus.SOURCE_URL_POLICY_MISSING,
        evidence_suffix="apa04-policy-missing",
        host_reference="provider.example",
        path_reference="/search",
        query_reference="q=bounded-source-value",
        policy_requirements=(
            SourceBoundaryPolicyRequirement.HOST_POLICY_REQUIRED,
            SourceBoundaryPolicyRequirement.PATH_POLICY_REQUIRED,
            SourceBoundaryPolicyRequirement.QUERY_POLICY_REQUIRED,
        ),
        risk_codes=(SourceBoundaryRiskCode.SOURCE_URL_POLICY_MISSING,),
    ),
    _boundary_fixture(
        "FX-APA04-REDIRECT-POLICY-BLOCKED-001",
        "redirect policy missing blocks live follow",
        _PROFILE_SOURCE_BOUNDARY,
        request_id="fx-apa04-request-redirect-policy",
        purpose="source-boundary-analysis",
        source_reference_id="fx-apa04-source-reference-redirect-policy",
        source_reference_kind=SourceReferenceKind.EXTERNAL_UNTRUSTED_INPUT,
        beacon_source_reference="source-ref:beacon-revision-005",
        bounded_value="bounded-source-value::redirect-policy",
        boundary_id="fx-apa04-boundary-redirect-policy",
        boundary_status=SourceBoundaryStatus.SOURCE_URL_REDIRECT_POLICY_BLOCKED,
        evidence_suffix="apa04-redirect-policy",
        host_reference="provider.example",
        path_reference="/redirect-check",
        policy_requirements=(SourceBoundaryPolicyRequirement.REDIRECT_POLICY_REQUIRED,),
        risk_codes=(SourceBoundaryRiskCode.SOURCE_URL_REDIRECT_POLICY_BLOCKED,),
    ),
    _boundary_fixture(
        "FX-APA04-DNS-POLICY-BLOCKED-001",
        "dns policy missing blocks probing",
        _PROFILE_SOURCE_BOUNDARY,
        request_id="fx-apa04-request-dns-policy",
        purpose="source-boundary-analysis",
        source_reference_id="fx-apa04-source-reference-dns-policy",
        source_reference_kind=SourceReferenceKind.EXTERNAL_UNTRUSTED_INPUT,
        beacon_source_reference="source-ref:beacon-revision-006",
        bounded_value="bounded-source-value::dns-policy",
        boundary_id="fx-apa04-boundary-dns-policy",
        boundary_status=SourceBoundaryStatus.SOURCE_URL_DNS_POLICY_BLOCKED,
        evidence_suffix="apa04-dns-policy",
        host_reference="provider.example",
        policy_requirements=(SourceBoundaryPolicyRequirement.DNS_POLICY_REQUIRED,),
        risk_codes=(SourceBoundaryRiskCode.SOURCE_URL_DNS_POLICY_BLOCKED,),
    ),
    _boundary_fixture(
        "FX-APA04-CANONICALIZATION-UNPROVEN-WARNING-001",
        "canonicalization and equivalence remain unproven",
        _PROFILE_SOURCE_BOUNDARY,
        request_id="fx-apa04-request-canonicalization",
        purpose="source-boundary-analysis",
        source_reference_id="fx-apa04-source-reference-canonicalization",
        source_reference_kind=SourceReferenceKind.EXTERNAL_UNTRUSTED_INPUT,
        beacon_source_reference="source-ref:beacon-revision-007",
        bounded_value="bounded-source-value::canonicalization",
        boundary_id="fx-apa04-boundary-canonicalization",
        boundary_status=SourceBoundaryStatus.SOURCE_URL_CANONICALIZATION_UNPROVEN,
        evidence_suffix="apa04-canonicalization",
        host_reference="provider.example",
        path_reference="/search",
        query_reference="q=canonicalization",
        policy_requirements=(SourceBoundaryPolicyRequirement.CANONICALIZATION_PROOF_REQUIRED,),
        risk_codes=(SourceBoundaryRiskCode.SOURCE_URL_CANONICALIZATION_UNPROVEN,),
    ),
    _boundary_fixture(
        "FX-APA04-SHELL-INTERPOLATION-BLOCKED-001",
        "shell interpolation attempt is blocked explicitly",
        _PROFILE_SOURCE_BOUNDARY,
        request_id="fx-apa04-request-shell",
        purpose="source-boundary-analysis",
        source_reference_id="fx-apa04-source-reference-shell",
        source_reference_kind=SourceReferenceKind.EXTERNAL_UNTRUSTED_INPUT,
        beacon_source_reference="source-ref:beacon-revision-008",
        bounded_value="bounded-source-value::shell-target",
        boundary_id="fx-apa04-boundary-shell",
        boundary_status=SourceBoundaryStatus.SOURCE_VALUE_SHELL_TARGET_BLOCKED,
        evidence_suffix="apa04-shell",
        policy_requirements=(SourceBoundaryPolicyRequirement.SHELL_INTERPOLATION_BLOCK_REQUIRED,),
        risk_codes=(SourceBoundaryRiskCode.SOURCE_VALUE_SHELL_TARGET_BLOCKED,),
    ),
    _boundary_fixture(
        "FX-APA04-FILESYSTEM-TARGET-BLOCKED-001",
        "filesystem target attempt is blocked explicitly",
        _PROFILE_SOURCE_BOUNDARY,
        request_id="fx-apa04-request-filesystem",
        purpose="source-boundary-analysis",
        source_reference_id="fx-apa04-source-reference-filesystem",
        source_reference_kind=SourceReferenceKind.EXTERNAL_UNTRUSTED_INPUT,
        beacon_source_reference="source-ref:beacon-revision-009",
        bounded_value="bounded-source-value::filesystem-target",
        boundary_id="fx-apa04-boundary-filesystem",
        boundary_status=SourceBoundaryStatus.SOURCE_VALUE_FILESYSTEM_TARGET_BLOCKED,
        evidence_suffix="apa04-filesystem",
        policy_requirements=(SourceBoundaryPolicyRequirement.FILESYSTEM_TARGET_BLOCK_REQUIRED,),
        risk_codes=(SourceBoundaryRiskCode.SOURCE_VALUE_FILESYSTEM_TARGET_BLOCKED,),
    ),
    _boundary_fixture(
        "FX-APA04-NETWORK-TARGET-BLOCKED-001",
        "arbitrary network target attempt is blocked explicitly",
        _PROFILE_SOURCE_BOUNDARY,
        request_id="fx-apa04-request-network",
        purpose="source-boundary-analysis",
        source_reference_id="fx-apa04-source-reference-network",
        source_reference_kind=SourceReferenceKind.EXTERNAL_UNTRUSTED_INPUT,
        beacon_source_reference="source-ref:beacon-revision-010",
        bounded_value="bounded-source-value::network-target",
        boundary_id="fx-apa04-boundary-network",
        boundary_status=SourceBoundaryStatus.SOURCE_VALUE_NETWORK_TARGET_BLOCKED,
        evidence_suffix="apa04-network",
        policy_requirements=(SourceBoundaryPolicyRequirement.NETWORK_TARGET_BLOCK_REQUIRED,),
        risk_codes=(SourceBoundaryRiskCode.SOURCE_VALUE_NETWORK_TARGET_BLOCKED,),
    ),
    _boundary_fixture(
        "FX-APA04-PARSER-OUTPUT-NOT-OVERWRITING-BEACON-SOURCE-001",
        "parser output must not overwrite beacon source url ownership",
        _PROFILE_SOURCE_BOUNDARY,
        request_id="fx-apa04-request-output-preserved",
        purpose="source-boundary-analysis",
        source_reference_id="fx-apa04-source-reference-output-preserved",
        source_reference_kind=SourceReferenceKind.SAFE_REFERENCE,
        beacon_source_reference="source-ref:beacon-revision-011",
        bounded_value="bounded-source-value::output-preserved",
        boundary_id="fx-apa04-boundary-output-preserved",
        boundary_status=SourceBoundaryStatus.SOURCE_URL_UNTRUSTED,
        evidence_suffix="apa04-output-preserved",
        parser_status=ParserOutcomeStatus.USABLE_RESPONSE,
        configuration_extraction=True,
        normalized_geography_candidates=("safe-geography",),
        normalized_category_candidates=("safe-category",),
        normalized_filter_candidates=("ownership=beacon",),
        host_reference="provider.example",
        path_reference="/search",
        query_reference="q=ownership-preserved",
        policy_requirements=(
            SourceBoundaryPolicyRequirement.HOST_POLICY_REQUIRED,
            SourceBoundaryPolicyRequirement.PATH_POLICY_REQUIRED,
            SourceBoundaryPolicyRequirement.QUERY_POLICY_REQUIRED,
        ),
        risk_codes=(SourceBoundaryRiskCode.SOURCE_URL_UNTRUSTED,),
    ),
    _transport_classification_fixture(
        "FX-APA05-NOT-SENT-001",
        "transport not sent remains explicit",
        _PROFILE_CURRENT_REFERENCE,
        request_id="fx-apa05-request-not-sent",
        purpose="response-classification",
        safe_source_reference="source::not-sent",
        transport_reference_id="fx-apa05-transport-not-sent",
        transport_status=TransportOutcomeStatus.NOT_SENT,
        response_reference=None,
        classification_id="fx-apa05-classification-not-sent",
        classification_status=TransportOutcomeStatus.NOT_SENT,
        provider_response_evidence_class=ProviderResponseEvidenceClass.UNCLASSIFIED,
        response_completeness_status=ResponseCompletenessStatus.UNVERIFIED,
        classification_rule=_RULE_TRANSPORT_GATE,
        evidence_suffix="apa05-not-sent",
        parser_status=None,
    ),
    _transport_classification_fixture(
        "FX-APA05-TRANSPORT-UNAVAILABLE-001",
        "transport unavailable remains explicit",
        _PROFILE_CURRENT_REFERENCE,
        request_id="fx-apa05-request-transport-unavailable",
        purpose="response-classification",
        safe_source_reference="source::transport-unavailable",
        transport_reference_id="fx-apa05-transport-unavailable",
        transport_status=TransportOutcomeStatus.TRANSPORT_UNAVAILABLE,
        response_reference=None,
        classification_id="fx-apa05-classification-transport-unavailable",
        classification_status=TransportOutcomeStatus.TRANSPORT_UNAVAILABLE,
        provider_response_evidence_class=ProviderResponseEvidenceClass.UNCLASSIFIED,
        response_completeness_status=ResponseCompletenessStatus.UNVERIFIED,
        classification_rule=_RULE_TRANSPORT_GATE,
        evidence_suffix="apa05-transport-unavailable",
        parser_status=None,
    ),
    _transport_classification_fixture(
        "FX-APA05-TRANSPORT-AMBIGUOUS-001",
        "transport ambiguous remains explicit",
        _PROFILE_CURRENT_REFERENCE,
        request_id="fx-apa05-request-transport-ambiguous",
        purpose="response-classification",
        safe_source_reference="source::transport-ambiguous",
        transport_reference_id="fx-apa05-transport-ambiguous",
        transport_status=TransportOutcomeStatus.TRANSPORT_AMBIGUOUS,
        response_reference="response::synthetic::transport-ambiguous",
        classification_id="fx-apa05-classification-transport-ambiguous",
        classification_status=TransportOutcomeStatus.TRANSPORT_AMBIGUOUS,
        provider_response_evidence_class=ProviderResponseEvidenceClass.UNCLASSIFIED,
        response_completeness_status=ResponseCompletenessStatus.UNVERIFIED,
        classification_rule=_RULE_TRANSPORT_GATE,
        evidence_suffix="apa05-transport-ambiguous",
        parser_status=None,
    ),
    _transport_classification_fixture(
        "FX-APA05-SENT-SUCCESS-RESPONSE-UNCLASSIFIED-001",
        "sent success response stays unclassified until validated",
        _PROFILE_CURRENT_REFERENCE,
        request_id="fx-apa05-request-response-unclassified",
        purpose="response-classification",
        safe_source_reference="source::response-unclassified",
        transport_reference_id="fx-apa05-transport-response-unclassified",
        transport_status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
        response_reference="response::synthetic::response-unclassified",
        classification_id="fx-apa05-classification-response-unclassified",
        classification_status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
        provider_response_evidence_class=ProviderResponseEvidenceClass.UNCLASSIFIED,
        response_completeness_status=ResponseCompletenessStatus.UNVERIFIED,
        classification_rule=_RULE_TRANSPORT_GATE,
        evidence_suffix="apa05-response-unclassified",
        parser_status=None,
    ),
    _transport_classification_fixture(
        "FX-APA05-USABLE-RESPONSE-CURRENT-PROFILE-PROOF-001",
        "usable response with current profile and source boundary proof",
        _PROFILE_CURRENT_REFERENCE,
        request_id="fx-apa05-request-current-proof",
        purpose="response-classification",
        safe_source_reference="bounded-source-value::current-proof",
        transport_reference_id="fx-apa05-transport-current-proof",
        transport_status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
        response_reference="response::synthetic::current-proof",
        classification_id="fx-apa05-classification-current-proof",
        classification_status=ParserOutcomeStatus.USABLE_RESPONSE,
        provider_response_evidence_class=ProviderResponseEvidenceClass.USABLE_RESPONSE,
        response_completeness_status=ResponseCompletenessStatus.COMPLETE,
        classification_rule=_RULE_USABLE_CURRENT_PROFILE,
        evidence_suffix="apa05-current-proof",
        parser_status=ParserOutcomeStatus.USABLE_RESPONSE,
        reference_status=ReferenceOutcomeStatus.CURRENT,
        source_reference=_source_reference(
            "fx-apa05-source-reference-current-proof",
            kind=SourceReferenceKind.BEACON_OWNED_SUBMISSION,
            beacon_source_reference="source-ref:beacon-revision-050",
            bounded_value="bounded-source-value::current-proof",
            host_reference="provider.example",
            path_reference="/search",
            query_reference="q=bounded-source-value::current-proof",
            policy_requirements=(
                SourceBoundaryPolicyRequirement.HOST_POLICY_REQUIRED,
                SourceBoundaryPolicyRequirement.PATH_POLICY_REQUIRED,
                SourceBoundaryPolicyRequirement.QUERY_POLICY_REQUIRED,
            ),
            risk_codes=(SourceBoundaryRiskCode.SOURCE_URL_UNTRUSTED,),
            notes=("synthetic current-proof source reference",),
        ),
        source_boundary_outcome=_source_boundary(
            "fx-apa05-boundary-current-proof",
            _source_reference(
                "fx-apa05-source-reference-current-proof",
                kind=SourceReferenceKind.BEACON_OWNED_SUBMISSION,
                beacon_source_reference="source-ref:beacon-revision-050",
                bounded_value="bounded-source-value::current-proof",
                host_reference="provider.example",
                path_reference="/search",
                query_reference="q=bounded-source-value::current-proof",
                policy_requirements=(
                    SourceBoundaryPolicyRequirement.HOST_POLICY_REQUIRED,
                    SourceBoundaryPolicyRequirement.PATH_POLICY_REQUIRED,
                    SourceBoundaryPolicyRequirement.QUERY_POLICY_REQUIRED,
                ),
                risk_codes=(SourceBoundaryRiskCode.SOURCE_URL_UNTRUSTED,),
                notes=("synthetic current-proof source reference",),
            ),
            status=SourceBoundaryStatus.SOURCE_URL_UNTRUSTED,
            policy_requirements=(
                SourceBoundaryPolicyRequirement.HOST_POLICY_REQUIRED,
                SourceBoundaryPolicyRequirement.PATH_POLICY_REQUIRED,
                SourceBoundaryPolicyRequirement.QUERY_POLICY_REQUIRED,
            ),
            risk_codes=(SourceBoundaryRiskCode.SOURCE_URL_UNTRUSTED,),
        ),
        search_source_analysis_outcome=_search_source_analysis(
            "fx-apa05-analysis-current-proof",
            _request(
                "fx-apa05-request-current-proof",
                _PROFILE_CURRENT_REFERENCE,
                purpose="response-classification",
                safe_source_reference="bounded-source-value::current-proof",
                source_reference=_source_reference(
                    "fx-apa05-source-reference-current-proof",
                    kind=SourceReferenceKind.BEACON_OWNED_SUBMISSION,
                    beacon_source_reference="source-ref:beacon-revision-050",
                    bounded_value="bounded-source-value::current-proof",
                    host_reference="provider.example",
                    path_reference="/search",
                    query_reference="q=bounded-source-value::current-proof",
                    policy_requirements=(
                        SourceBoundaryPolicyRequirement.HOST_POLICY_REQUIRED,
                        SourceBoundaryPolicyRequirement.PATH_POLICY_REQUIRED,
                        SourceBoundaryPolicyRequirement.QUERY_POLICY_REQUIRED,
                    ),
                    risk_codes=(SourceBoundaryRiskCode.SOURCE_URL_UNTRUSTED,),
                    notes=("synthetic current-proof source reference",),
                ),
                source_boundary_outcome=_source_boundary(
                    "fx-apa05-boundary-current-proof",
                    _source_reference(
                        "fx-apa05-source-reference-current-proof",
                        kind=SourceReferenceKind.BEACON_OWNED_SUBMISSION,
                        beacon_source_reference="source-ref:beacon-revision-050",
                        bounded_value="bounded-source-value::current-proof",
                        host_reference="provider.example",
                        path_reference="/search",
                        query_reference="q=bounded-source-value::current-proof",
                        policy_requirements=(
                            SourceBoundaryPolicyRequirement.HOST_POLICY_REQUIRED,
                            SourceBoundaryPolicyRequirement.PATH_POLICY_REQUIRED,
                            SourceBoundaryPolicyRequirement.QUERY_POLICY_REQUIRED,
                        ),
                        risk_codes=(SourceBoundaryRiskCode.SOURCE_URL_UNTRUSTED,),
                        notes=("synthetic current-proof source reference",),
                    ),
                    status=SourceBoundaryStatus.SOURCE_URL_UNTRUSTED,
                    policy_requirements=(
                        SourceBoundaryPolicyRequirement.HOST_POLICY_REQUIRED,
                        SourceBoundaryPolicyRequirement.PATH_POLICY_REQUIRED,
                        SourceBoundaryPolicyRequirement.QUERY_POLICY_REQUIRED,
                    ),
                    risk_codes=(SourceBoundaryRiskCode.SOURCE_URL_UNTRUSTED,),
                ),
            ),
            _transport(
                "fx-apa05-transport-current-proof",
                status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
                request_reference="fx-apa05-request-current-proof",
                response_reference="response::synthetic::current-proof",
                route_reference="route::synthetic",
                evidence_reference_suffix="apa05-current-proof",
            ),
            _PROFILE_CURRENT_REFERENCE,
            status=ParserOutcomeStatus.USABLE_RESPONSE,
            evidence_suffix="apa05-current-proof",
        ),
        search_configuration_extraction_outcome=_search_configuration(
            "fx-apa05-extraction-current-proof",
            _request(
                "fx-apa05-request-current-proof",
                _PROFILE_CURRENT_REFERENCE,
                purpose="response-classification",
                safe_source_reference="bounded-source-value::current-proof",
                source_reference=_source_reference(
                    "fx-apa05-source-reference-current-proof",
                    kind=SourceReferenceKind.BEACON_OWNED_SUBMISSION,
                    beacon_source_reference="source-ref:beacon-revision-050",
                    bounded_value="bounded-source-value::current-proof",
                    host_reference="provider.example",
                    path_reference="/search",
                    query_reference="q=bounded-source-value::current-proof",
                    policy_requirements=(
                        SourceBoundaryPolicyRequirement.HOST_POLICY_REQUIRED,
                        SourceBoundaryPolicyRequirement.PATH_POLICY_REQUIRED,
                        SourceBoundaryPolicyRequirement.QUERY_POLICY_REQUIRED,
                    ),
                    risk_codes=(SourceBoundaryRiskCode.SOURCE_URL_UNTRUSTED,),
                    notes=("synthetic current-proof source reference",),
                ),
                source_boundary_outcome=_source_boundary(
                    "fx-apa05-boundary-current-proof",
                    _source_reference(
                        "fx-apa05-source-reference-current-proof",
                        kind=SourceReferenceKind.BEACON_OWNED_SUBMISSION,
                        beacon_source_reference="source-ref:beacon-revision-050",
                        bounded_value="bounded-source-value::current-proof",
                        host_reference="provider.example",
                        path_reference="/search",
                        query_reference="q=bounded-source-value::current-proof",
                        policy_requirements=(
                            SourceBoundaryPolicyRequirement.HOST_POLICY_REQUIRED,
                            SourceBoundaryPolicyRequirement.PATH_POLICY_REQUIRED,
                            SourceBoundaryPolicyRequirement.QUERY_POLICY_REQUIRED,
                        ),
                        risk_codes=(SourceBoundaryRiskCode.SOURCE_URL_UNTRUSTED,),
                        notes=("synthetic current-proof source reference",),
                    ),
                    status=SourceBoundaryStatus.SOURCE_URL_UNTRUSTED,
                    policy_requirements=(
                        SourceBoundaryPolicyRequirement.HOST_POLICY_REQUIRED,
                        SourceBoundaryPolicyRequirement.PATH_POLICY_REQUIRED,
                        SourceBoundaryPolicyRequirement.QUERY_POLICY_REQUIRED,
                    ),
                    risk_codes=(SourceBoundaryRiskCode.SOURCE_URL_UNTRUSTED,),
                ),
            ),
            _transport(
                "fx-apa05-transport-current-proof",
                status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
                request_reference="fx-apa05-request-current-proof",
                response_reference="response::synthetic::current-proof",
                route_reference="route::synthetic",
                evidence_reference_suffix="apa05-current-proof",
            ),
            _PROFILE_CURRENT_REFERENCE,
            status=ParserOutcomeStatus.USABLE_RESPONSE,
            evidence_suffix="apa05-current-proof",
            normalized_geography_candidates=("synthetic-city",),
            normalized_category_candidates=("synthetic-category",),
            normalized_filters=("proof=current",),
            sort_context_reference="sort-context::current-proof",
        ),
        listing_page_parse_outcome=_listing_page(
            "fx-apa05-page-current-proof",
            _request(
                "fx-apa05-request-current-proof",
                _PROFILE_CURRENT_REFERENCE,
                purpose="response-classification",
                safe_source_reference="bounded-source-value::current-proof",
                source_reference=_source_reference(
                    "fx-apa05-source-reference-current-proof",
                    kind=SourceReferenceKind.BEACON_OWNED_SUBMISSION,
                    beacon_source_reference="source-ref:beacon-revision-050",
                    bounded_value="bounded-source-value::current-proof",
                    host_reference="provider.example",
                    path_reference="/search",
                    query_reference="q=bounded-source-value::current-proof",
                    policy_requirements=(
                        SourceBoundaryPolicyRequirement.HOST_POLICY_REQUIRED,
                        SourceBoundaryPolicyRequirement.PATH_POLICY_REQUIRED,
                        SourceBoundaryPolicyRequirement.QUERY_POLICY_REQUIRED,
                    ),
                    risk_codes=(SourceBoundaryRiskCode.SOURCE_URL_UNTRUSTED,),
                    notes=("synthetic current-proof source reference",),
                ),
                source_boundary_outcome=_source_boundary(
                    "fx-apa05-boundary-current-proof",
                    _source_reference(
                        "fx-apa05-source-reference-current-proof",
                        kind=SourceReferenceKind.BEACON_OWNED_SUBMISSION,
                        beacon_source_reference="source-ref:beacon-revision-050",
                        bounded_value="bounded-source-value::current-proof",
                        host_reference="provider.example",
                        path_reference="/search",
                        query_reference="q=bounded-source-value::current-proof",
                        policy_requirements=(
                            SourceBoundaryPolicyRequirement.HOST_POLICY_REQUIRED,
                            SourceBoundaryPolicyRequirement.PATH_POLICY_REQUIRED,
                            SourceBoundaryPolicyRequirement.QUERY_POLICY_REQUIRED,
                        ),
                        risk_codes=(SourceBoundaryRiskCode.SOURCE_URL_UNTRUSTED,),
                        notes=("synthetic current-proof source reference",),
                    ),
                    status=SourceBoundaryStatus.SOURCE_URL_UNTRUSTED,
                    policy_requirements=(
                        SourceBoundaryPolicyRequirement.HOST_POLICY_REQUIRED,
                        SourceBoundaryPolicyRequirement.PATH_POLICY_REQUIRED,
                        SourceBoundaryPolicyRequirement.QUERY_POLICY_REQUIRED,
                    ),
                    risk_codes=(SourceBoundaryRiskCode.SOURCE_URL_UNTRUSTED,),
                ),
            ),
            _transport(
                "fx-apa05-transport-current-proof",
                status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
                request_reference="fx-apa05-request-current-proof",
                response_reference="response::synthetic::current-proof",
                route_reference="route::synthetic",
                evidence_reference_suffix="apa05-current-proof",
            ),
            _PROFILE_CURRENT_REFERENCE,
            status=ParserOutcomeStatus.USABLE_RESPONSE,
            candidate=_listing_candidate(
                "fx-apa05-listing-current-proof",
                _listing_card(
                    "fx-apa05-card-current-proof",
                    field_candidates=_tier_1_listing_field_candidates(
                        "apa05-current-proof", _PROFILE_CURRENT_REFERENCE
                    ),
                    evidence_suffix="apa05-current-proof",
                ),
                evidence_suffix="apa05-current-proof",
            ),
            card=_listing_card(
                "fx-apa05-card-current-proof",
                field_candidates=_tier_1_listing_field_candidates(
                    "apa05-current-proof", _PROFILE_CURRENT_REFERENCE
                ),
                evidence_suffix="apa05-current-proof",
            ),
            evidence_suffix="apa05-current-proof",
        ),
    ),
    _transport_classification_fixture(
        "FX-APA05-EXPLICIT-PROVIDER-REJECTION-001",
        "explicit provider rejection remains explicit",
        _PROFILE_CURRENT_REFERENCE,
        request_id="fx-apa05-request-provider-rejection",
        purpose="response-classification",
        safe_source_reference="source::provider-rejection",
        transport_reference_id="fx-apa05-transport-provider-rejection",
        transport_status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
        response_reference="response::synthetic::provider-rejection",
        classification_id="fx-apa05-classification-provider-rejection",
        classification_status=ParserOutcomeStatus.EXPLICIT_REJECTION,
        provider_response_evidence_class=ProviderResponseEvidenceClass.EXPLICIT_REJECTION,
        response_completeness_status=ResponseCompletenessStatus.COMPLETE,
        classification_rule=_RULE_PROVIDER_REJECTION,
        evidence_suffix="apa05-provider-rejection",
        parser_status=ParserOutcomeStatus.EXPLICIT_REJECTION,
    ),
    _transport_classification_fixture(
        "FX-APA05-RATE-ACCESS-RESTRICTED-001",
        "rate or access restriction remains explicit",
        _PROFILE_CURRENT_REFERENCE,
        request_id="fx-apa05-request-rate-access-restricted",
        purpose="response-classification",
        safe_source_reference="source::rate-access-restricted",
        transport_reference_id="fx-apa05-transport-rate-access-restricted",
        transport_status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
        response_reference="response::synthetic::rate-access-restricted",
        classification_id="fx-apa05-classification-rate-access-restricted",
        classification_status=ParserOutcomeStatus.RATE_OR_ACCESS_RESTRICTED,
        provider_response_evidence_class=ProviderResponseEvidenceClass.RATE_OR_ACCESS_RESTRICTED,
        response_completeness_status=ResponseCompletenessStatus.COMPLETE,
        classification_rule=_RULE_RESTRICTED,
        evidence_suffix="apa05-rate-access-restricted",
        parser_status=ParserOutcomeStatus.RATE_OR_ACCESS_RESTRICTED,
        response_restriction_signal=ResponseRestrictionSignal.RATE_LIMIT,
    ),
    _transport_classification_fixture(
        "FX-APA05-CAPTCHA-CHALLENGE-001",
        "captcha or challenge remains explicit",
        _PROFILE_CURRENT_REFERENCE,
        request_id="fx-apa05-request-captcha-challenge",
        purpose="response-classification",
        safe_source_reference="source::captcha-challenge",
        transport_reference_id="fx-apa05-transport-captcha-challenge",
        transport_status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
        response_reference="response::synthetic::captcha-challenge",
        classification_id="fx-apa05-classification-captcha-challenge",
        classification_status=ParserOutcomeStatus.CAPTCHA_OR_CHALLENGE,
        provider_response_evidence_class=ProviderResponseEvidenceClass.CAPTCHA_OR_CHALLENGE,
        response_completeness_status=ResponseCompletenessStatus.COMPLETE,
        classification_rule=_RULE_CAPTCHA,
        evidence_suffix="apa05-captcha-challenge",
        parser_status=ParserOutcomeStatus.CAPTCHA_OR_CHALLENGE,
        response_restriction_signal=ResponseRestrictionSignal.CAPTCHA,
    ),
    _transport_classification_fixture(
        "FX-APA05-MALFORMED-RESPONSE-001",
        "malformed response remains explicit",
        _PROFILE_CURRENT_REFERENCE,
        request_id="fx-apa05-request-malformed-response",
        purpose="response-classification",
        safe_source_reference="source::malformed-response",
        transport_reference_id="fx-apa05-transport-malformed-response",
        transport_status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
        response_reference="response::synthetic::malformed-response",
        classification_id="fx-apa05-classification-malformed-response",
        classification_status=ParserOutcomeStatus.MALFORMED_RESPONSE,
        provider_response_evidence_class=ProviderResponseEvidenceClass.MALFORMED_RESPONSE,
        response_completeness_status=ResponseCompletenessStatus.INCOMPLETE,
        classification_rule=_RULE_STRUCTURE_FAILURE,
        evidence_suffix="apa05-malformed-response",
        parser_status=ParserOutcomeStatus.MALFORMED_RESPONSE,
    ),
    _transport_classification_fixture(
        "FX-APA05-INCOMPLETE-RESPONSE-001",
        "incomplete response remains explicit",
        _PROFILE_CURRENT_REFERENCE,
        request_id="fx-apa05-request-incomplete-response",
        purpose="response-classification",
        safe_source_reference="source::incomplete-response",
        transport_reference_id="fx-apa05-transport-incomplete-response",
        transport_status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
        response_reference="response::synthetic::incomplete-response",
        classification_id="fx-apa05-classification-incomplete-response",
        classification_status=ParserOutcomeStatus.INCOMPLETE_RESPONSE,
        provider_response_evidence_class=ProviderResponseEvidenceClass.INCOMPLETE_RESPONSE,
        response_completeness_status=ResponseCompletenessStatus.INCOMPLETE,
        classification_rule=_RULE_STRUCTURE_FAILURE,
        evidence_suffix="apa05-incomplete-response",
        parser_status=ParserOutcomeStatus.INCOMPLETE_RESPONSE,
    ),
    _transport_classification_fixture(
        "FX-APA05-UNSUPPORTED-STRUCTURE-001",
        "unsupported structure remains explicit",
        _PROFILE_CURRENT_REFERENCE,
        request_id="fx-apa05-request-unsupported-structure",
        purpose="response-classification",
        safe_source_reference="source::unsupported-structure",
        transport_reference_id="fx-apa05-transport-unsupported-structure",
        transport_status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
        response_reference="response::synthetic::unsupported-structure",
        classification_id="fx-apa05-classification-unsupported-structure",
        classification_status=ParserOutcomeStatus.UNSUPPORTED_STRUCTURE,
        provider_response_evidence_class=ProviderResponseEvidenceClass.UNSUPPORTED_STRUCTURE,
        response_completeness_status=ResponseCompletenessStatus.UNVERIFIED,
        classification_rule=_RULE_STRUCTURE_FAILURE,
        evidence_suffix="apa05-unsupported-structure",
        parser_status=ParserOutcomeStatus.UNSUPPORTED_STRUCTURE,
    ),
    _transport_classification_fixture(
        "FX-APA05-STALE-REFERENCE-PROFILE-001",
        "stale reference profile remains explicit",
        _PROFILE_STALE_REFERENCE,
        request_id="fx-apa05-request-stale-reference",
        purpose="response-classification",
        safe_source_reference="source::stale-reference",
        transport_reference_id="fx-apa05-transport-stale-reference",
        transport_status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
        response_reference="response::synthetic::stale-reference",
        classification_id="fx-apa05-classification-stale-reference",
        classification_status=ReferenceOutcomeStatus.REFERENCE_STALE,
        provider_response_evidence_class=ProviderResponseEvidenceClass.UNCLASSIFIED,
        response_completeness_status=ResponseCompletenessStatus.UNVERIFIED,
        classification_rule=_RULE_REFERENCE_STATE,
        evidence_suffix="apa05-stale-reference",
        parser_status=None,
        reference_status=ReferenceOutcomeStatus.REFERENCE_STALE,
        warnings=(
            ParserWarning(
                code=ParserWarningCode.STALE_COMPATIBILITY_PROFILE,
                message="stale reference profile remains explicit",
            ),
        ),
        search_source_analysis_outcome=_search_source_analysis(
            "fx-apa05-analysis-stale-reference",
            _request(
                "fx-apa05-request-stale-reference",
                _PROFILE_STALE_REFERENCE,
                purpose="response-classification",
                safe_source_reference="source::stale-reference",
            ),
            _transport(
                "fx-apa05-transport-stale-reference",
                status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
                request_reference="fx-apa05-request-stale-reference",
                response_reference="response::synthetic::stale-reference",
                route_reference="route::synthetic",
                evidence_reference_suffix="apa05-stale-reference",
            ),
            _PROFILE_STALE_REFERENCE,
            status=ReferenceOutcomeStatus.REFERENCE_STALE,
            evidence_suffix="apa05-stale-reference",
            warnings=(
                ParserWarning(
                    code=ParserWarningCode.STALE_COMPATIBILITY_PROFILE,
                    message="stale reference profile remains explicit",
                ),
            ),
        ),
    ),
    _transport_classification_fixture(
        "FX-APA05-MISSING-REFERENCE-PROFILE-001",
        "missing reference profile remains explicit",
        _PROFILE_UNAVAILABLE_REFERENCE,
        request_id="fx-apa05-request-missing-reference",
        purpose="response-classification",
        safe_source_reference="source::missing-reference",
        transport_reference_id="fx-apa05-transport-missing-reference",
        transport_status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
        response_reference="response::synthetic::missing-reference",
        classification_id="fx-apa05-classification-missing-reference",
        classification_status=ReferenceOutcomeStatus.REFERENCE_MISSING,
        provider_response_evidence_class=ProviderResponseEvidenceClass.UNCLASSIFIED,
        response_completeness_status=ResponseCompletenessStatus.UNVERIFIED,
        classification_rule=_RULE_REFERENCE_STATE,
        evidence_suffix="apa05-missing-reference",
        parser_status=None,
        reference_status=ReferenceOutcomeStatus.REFERENCE_MISSING,
        warnings=(
            ParserWarning(
                code=ParserWarningCode.REFERENCE_UNAVAILABLE,
                message="missing reference profile remains explicit",
            ),
        ),
        search_source_analysis_outcome=_search_source_analysis(
            "fx-apa05-analysis-missing-reference",
            _request(
                "fx-apa05-request-missing-reference",
                _PROFILE_UNAVAILABLE_REFERENCE,
                purpose="response-classification",
                safe_source_reference="source::missing-reference",
            ),
            _transport(
                "fx-apa05-transport-missing-reference",
                status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
                request_reference="fx-apa05-request-missing-reference",
                response_reference="response::synthetic::missing-reference",
                route_reference="route::synthetic",
                evidence_reference_suffix="apa05-missing-reference",
            ),
            _PROFILE_UNAVAILABLE_REFERENCE,
            status=ReferenceOutcomeStatus.REFERENCE_MISSING,
            evidence_suffix="apa05-missing-reference",
            warnings=(
                ParserWarning(
                    code=ParserWarningCode.REFERENCE_UNAVAILABLE,
                    message="missing reference profile remains explicit",
                ),
            ),
        ),
    ),
    _transport_classification_fixture(
        "FX-APA05-DISPUTED-REFERENCE-PROFILE-001",
        "disputed reference profile remains explicit",
        _PROFILE_DISPUTED_REFERENCE,
        request_id="fx-apa05-request-disputed-reference",
        purpose="response-classification",
        safe_source_reference="source::disputed-reference",
        transport_reference_id="fx-apa05-transport-disputed-reference",
        transport_status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
        response_reference="response::synthetic::disputed-reference",
        classification_id="fx-apa05-classification-disputed-reference",
        classification_status=ReferenceOutcomeStatus.REFERENCE_DISPUTED,
        provider_response_evidence_class=ProviderResponseEvidenceClass.UNCLASSIFIED,
        response_completeness_status=ResponseCompletenessStatus.UNVERIFIED,
        classification_rule=_RULE_REFERENCE_STATE,
        evidence_suffix="apa05-disputed-reference",
        parser_status=None,
        reference_status=ReferenceOutcomeStatus.REFERENCE_DISPUTED,
        warnings=(
            ParserWarning(
                code=ParserWarningCode.REFERENCE_DISPUTED,
                message="disputed reference profile remains explicit",
            ),
        ),
        search_source_analysis_outcome=_search_source_analysis(
            "fx-apa05-analysis-disputed-reference",
            _request(
                "fx-apa05-request-disputed-reference",
                _PROFILE_DISPUTED_REFERENCE,
                purpose="response-classification",
                safe_source_reference="source::disputed-reference",
            ),
            _transport(
                "fx-apa05-transport-disputed-reference",
                status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
                request_reference="fx-apa05-request-disputed-reference",
                response_reference="response::synthetic::disputed-reference",
                route_reference="route::synthetic",
                evidence_reference_suffix="apa05-disputed-reference",
            ),
            _PROFILE_DISPUTED_REFERENCE,
            status=ReferenceOutcomeStatus.REFERENCE_DISPUTED,
            evidence_suffix="apa05-disputed-reference",
            warnings=(
                ParserWarning(
                    code=ParserWarningCode.REFERENCE_DISPUTED,
                    message="disputed reference profile remains explicit",
                ),
            ),
        ),
    ),
    _transport_classification_fixture(
        "FX-APA05-PARTIAL-RESPONSE-PAGE-001",
        "partial response page remains explicit",
        _PROFILE_PARTIAL,
        request_id="fx-apa05-request-partial-response",
        purpose="response-classification",
        safe_source_reference="source::partial-response",
        transport_reference_id="fx-apa05-transport-partial-response",
        transport_status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
        response_reference="response::synthetic::partial-response",
        classification_id="fx-apa05-classification-partial-response",
        classification_status=ParserOutcomeStatus.PARTIAL,
        provider_response_evidence_class=ProviderResponseEvidenceClass.PARTIAL,
        response_completeness_status=ResponseCompletenessStatus.PARTIAL,
        classification_rule=_RULE_PARTIAL,
        evidence_suffix="apa05-partial-response",
        parser_status=ParserOutcomeStatus.PARTIAL,
        warnings=(
            ParserWarning(
                code=ParserWarningCode.PARTIAL_PAGE,
                message="partial response page remains explicit",
            ),
        ),
        listing_page_parse_outcome=_listing_page(
            "fx-apa05-page-partial-response",
            _request(
                "fx-apa05-request-partial-response",
                _PROFILE_PARTIAL,
                purpose="response-classification",
                safe_source_reference="source::partial-response",
                requested_page_numbers=(1, 2),
            ),
            _transport(
                "fx-apa05-transport-partial-response",
                status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
                request_reference="fx-apa05-request-partial-response",
                response_reference="response::synthetic::partial-response",
                route_reference="route::synthetic",
                evidence_reference_suffix="apa05-partial-response",
            ),
            _PROFILE_PARTIAL,
            status=ParserOutcomeStatus.PARTIAL,
            candidate=_listing_candidate(
                "fx-apa05-listing-partial-response",
                _listing_card(
                    "fx-apa05-card-partial-response",
                    field_candidates=_tier_1_listing_field_candidates(
                        "apa05-partial-response", _PROFILE_PARTIAL
                    ),
                    evidence_suffix="apa05-partial-response",
                ),
                evidence_suffix="apa05-partial-response",
                status=ListingCandidateStatus.PARTIAL,
            ),
            card=_listing_card(
                "fx-apa05-card-partial-response",
                field_candidates=_tier_1_listing_field_candidates(
                    "apa05-partial-response", _PROFILE_PARTIAL
                ),
                evidence_suffix="apa05-partial-response",
            ),
            evidence_suffix="apa05-partial-response",
            warnings=(
                ParserWarning(
                    code=ParserWarningCode.PARTIAL_PAGE,
                    message="partial response page remains explicit",
                ),
            ),
        ),
        listing_batch_parse_outcome=_listing_batch(
            "fx-apa05-batch-partial-response",
            _request(
                "fx-apa05-request-partial-response",
                _PROFILE_PARTIAL,
                purpose="response-classification",
                safe_source_reference="source::partial-response",
                requested_page_numbers=(1, 2),
            ),
            _transport(
                "fx-apa05-transport-partial-response",
                status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
                request_reference="fx-apa05-request-partial-response",
                response_reference="response::synthetic::partial-response",
                route_reference="route::synthetic",
                evidence_reference_suffix="apa05-partial-response",
            ),
            _PROFILE_PARTIAL,
            status=ParserOutcomeStatus.PARTIAL,
            page_outcomes=(
                _listing_page(
                    "fx-apa05-page-partial-response",
                    _request(
                        "fx-apa05-request-partial-response",
                        _PROFILE_PARTIAL,
                        purpose="response-classification",
                        safe_source_reference="source::partial-response",
                        requested_page_numbers=(1, 2),
                    ),
                    _transport(
                        "fx-apa05-transport-partial-response",
                        status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
                        request_reference="fx-apa05-request-partial-response",
                        response_reference="response::synthetic::partial-response",
                        route_reference="route::synthetic",
                        evidence_reference_suffix="apa05-partial-response",
                    ),
                    _PROFILE_PARTIAL,
                    status=ParserOutcomeStatus.PARTIAL,
                    candidate=_listing_candidate(
                        "fx-apa05-listing-partial-response",
                        _listing_card(
                            "fx-apa05-card-partial-response",
                            field_candidates=_tier_1_listing_field_candidates(
                                "apa05-partial-response", _PROFILE_PARTIAL
                            ),
                            evidence_suffix="apa05-partial-response",
                        ),
                        evidence_suffix="apa05-partial-response",
                        status=ListingCandidateStatus.PARTIAL,
                    ),
                    card=_listing_card(
                        "fx-apa05-card-partial-response",
                        field_candidates=_tier_1_listing_field_candidates(
                            "apa05-partial-response", _PROFILE_PARTIAL
                        ),
                        evidence_suffix="apa05-partial-response",
                    ),
                    evidence_suffix="apa05-partial-response",
                    warnings=(
                        ParserWarning(
                            code=ParserWarningCode.PARTIAL_PAGE,
                            message="partial response page remains explicit",
                        ),
                    ),
                ),
            ),
            evidence_suffix="apa05-partial-response",
            warnings=(
                ParserWarning(
                    code=ParserWarningCode.PARTIAL_PAGE,
                    message="partial response page remains explicit",
                ),
            ),
        ),
    ),
    _transport_classification_fixture(
        "FX-APA05-AMBIGUOUS-RESULT-001",
        "ambiguous result remains explicit",
        _PROFILE_AMBIGUOUS,
        request_id="fx-apa05-request-ambiguous-result",
        purpose="response-classification",
        safe_source_reference="source::ambiguous-result",
        transport_reference_id="fx-apa05-transport-ambiguous-result",
        transport_status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
        response_reference="response::synthetic::ambiguous-result",
        classification_id="fx-apa05-classification-ambiguous-result",
        classification_status=ParserOutcomeStatus.RESULT_AMBIGUOUS,
        provider_response_evidence_class=ProviderResponseEvidenceClass.RESULT_AMBIGUOUS,
        response_completeness_status=ResponseCompletenessStatus.AMBIGUOUS,
        classification_rule=_RULE_RESULT_AMBIGUOUS,
        evidence_suffix="apa05-ambiguous-result",
        parser_status=ParserOutcomeStatus.RESULT_AMBIGUOUS,
        warnings=(
            ParserWarning(
                code=ParserWarningCode.SORT_CONTEXT_AMBIGUOUS,
                message="ambiguous result remains explicit",
            ),
        ),
        listing_page_parse_outcome=_listing_page(
            "fx-apa05-page-ambiguous-result",
            _request(
                "fx-apa05-request-ambiguous-result",
                _PROFILE_AMBIGUOUS,
                purpose="response-classification",
                safe_source_reference="source::ambiguous-result",
            ),
            _transport(
                "fx-apa05-transport-ambiguous-result",
                status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
                request_reference="fx-apa05-request-ambiguous-result",
                response_reference="response::synthetic::ambiguous-result",
                route_reference="route::synthetic",
                evidence_reference_suffix="apa05-ambiguous-result",
            ),
            _PROFILE_AMBIGUOUS,
            status=ParserOutcomeStatus.RESULT_AMBIGUOUS,
            evidence_suffix="apa05-ambiguous-result",
            warnings=(
                ParserWarning(
                    code=ParserWarningCode.SORT_CONTEXT_AMBIGUOUS,
                    message="ambiguous result remains explicit",
                ),
            ),
        ),
    ),
    _transport_classification_fixture(
        "FX-APA05-CLEAN-EMPTY-BLOCKED-WITHOUT-PROOF-001",
        "clean empty blocked without current profile proof",
        _PROFILE_CURRENT_REFERENCE,
        request_id="fx-apa05-request-clean-empty-blocked",
        purpose="response-classification",
        safe_source_reference="source::clean-empty-blocked",
        transport_reference_id="fx-apa05-transport-clean-empty-blocked",
        transport_status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
        response_reference="response::synthetic::clean-empty-blocked",
        classification_id="fx-apa05-classification-clean-empty-blocked",
        classification_status=ReferenceOutcomeStatus.REFERENCE_MISSING,
        provider_response_evidence_class=ProviderResponseEvidenceClass.EMPTY_WITHOUT_PROOF,
        response_completeness_status=ResponseCompletenessStatus.EMPTY_BLOCKED,
        classification_rule=_RULE_CLEAN_EMPTY_BLOCKED,
        evidence_suffix="apa05-clean-empty-blocked",
        parser_status=ParserOutcomeStatus.EXPLICIT_REJECTION,
        reference_status=ReferenceOutcomeStatus.REFERENCE_MISSING,
    ),
    _transport_classification_fixture(
        "FX-APA05-HTTP-200-NON-EMPTY-NOT-ENOUGH-001",
        "http 200 and non-empty body are not enough by themselves",
        _PROFILE_CURRENT_REFERENCE,
        request_id="fx-apa05-request-http-200-non-empty",
        purpose="response-classification",
        safe_source_reference="source::http-200-non-empty",
        transport_reference_id="fx-apa05-transport-http-200-non-empty",
        transport_status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
        response_reference="response::synthetic::http-200-non-empty",
        classification_id="fx-apa05-classification-http-200-non-empty",
        classification_status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
        provider_response_evidence_class=ProviderResponseEvidenceClass.BODY_PRESENT_UNCLASSIFIED,
        response_completeness_status=ResponseCompletenessStatus.UNVERIFIED,
        classification_rule=_RULE_HTTP_200_NON_EMPTY_NOT_ENOUGH,
        evidence_suffix="apa05-http-200-non-empty",
        parser_status=None,
    ),
    _search_configuration_fixture(
        "FX-APA06-GEOGRAPHY-CANDIDATE-001",
        "geography candidate from safe source evidence",
        evidence_suffix="apa06-geography",
        normalized_geography_candidates=("synthetic-city",),
        search_configuration_candidates=(
            _search_configuration_candidate(
                "fx-apa06-candidate-geography",
                SearchConfigurationExtractionField.GEOGRAPHY_CONTEXT,
                field_status=SearchConfigurationFieldStatus.EVIDENCE_BOUND,
                value_kind=SearchConfigurationValueKind.SCALAR,
                parameter_candidates=(
                    _search_configuration_parameter_candidate(
                        "geography",
                        parameter_value="synthetic-city",
                        field_status=SearchConfigurationFieldStatus.EVIDENCE_BOUND,
                        value_kind=SearchConfigurationValueKind.SCALAR,
                        evidence_suffix="apa06-geography",
                    ),
                ),
                evidence_suffix="apa06-geography",
                warnings=(
                    ParserWarning(
                        code=SearchConfigurationWarningCode.GEOGRAPHY_CANDIDATE_EVIDENCE_BOUND,
                        message="geography candidate remains evidence-bound",
                    ),
                ),
            ),
        ),
        parameter_candidates=(
            _search_configuration_parameter_candidate(
                "geography",
                parameter_value="synthetic-city",
                field_status=SearchConfigurationFieldStatus.EVIDENCE_BOUND,
                value_kind=SearchConfigurationValueKind.SCALAR,
                evidence_suffix="apa06-geography",
            ),
        ),
        warnings=(
            ParserWarning(
                code=SearchConfigurationWarningCode.GEOGRAPHY_CANDIDATE_EVIDENCE_BOUND,
                message="geography candidate remains evidence-bound",
            ),
        ),
    ),
    _search_configuration_fixture(
        "FX-APA06-CATEGORY-CANDIDATE-001",
        "category candidate from safe source evidence",
        evidence_suffix="apa06-category",
        normalized_category_candidates=("synthetic-category",),
        search_configuration_candidates=(
            _search_configuration_candidate(
                "fx-apa06-candidate-category",
                SearchConfigurationExtractionField.CATEGORY_CONTEXT,
                field_status=SearchConfigurationFieldStatus.EVIDENCE_BOUND,
                value_kind=SearchConfigurationValueKind.SCALAR,
                parameter_candidates=(
                    _search_configuration_parameter_candidate(
                        "category",
                        parameter_value="synthetic-category",
                        field_status=SearchConfigurationFieldStatus.EVIDENCE_BOUND,
                        value_kind=SearchConfigurationValueKind.SCALAR,
                        evidence_suffix="apa06-category",
                    ),
                ),
                evidence_suffix="apa06-category",
                warnings=(
                    ParserWarning(
                        code=SearchConfigurationWarningCode.CATEGORY_CANDIDATE_EVIDENCE_BOUND,
                        message="category candidate remains evidence-bound",
                    ),
                ),
            ),
        ),
        parameter_candidates=(
            _search_configuration_parameter_candidate(
                "category",
                parameter_value="synthetic-category",
                field_status=SearchConfigurationFieldStatus.EVIDENCE_BOUND,
                value_kind=SearchConfigurationValueKind.SCALAR,
                evidence_suffix="apa06-category",
            ),
        ),
        warnings=(
            ParserWarning(
                code=SearchConfigurationWarningCode.CATEGORY_CANDIDATE_EVIDENCE_BOUND,
                message="category candidate remains evidence-bound",
            ),
        ),
    ),
    _search_configuration_fixture(
        "FX-APA06-PRICE-BOUNDS-CANDIDATE-001",
        "price lower and upper bound candidates",
        evidence_suffix="apa06-price-bounds",
        search_configuration_candidates=(
            _search_configuration_candidate(
                "fx-apa06-candidate-price-lower",
                SearchConfigurationExtractionField.PRICE_LOWER_BOUND,
                field_status=SearchConfigurationFieldStatus.EVIDENCE_BOUND,
                value_kind=SearchConfigurationValueKind.RANGE_BOUND,
                parameter_candidates=(
                    _search_configuration_parameter_candidate(
                        "price_min",
                        parameter_value="1000",
                        field_status=SearchConfigurationFieldStatus.EVIDENCE_BOUND,
                        value_kind=SearchConfigurationValueKind.RANGE_BOUND,
                        evidence_suffix="apa06-price-bounds",
                    ),
                ),
                evidence_suffix="apa06-price-bounds",
                warnings=(
                    ParserWarning(
                        code=SearchConfigurationWarningCode.PRICE_BOUNDS_CANDIDATE_EVIDENCE_BOUND,
                        message="price lower bound remains evidence-bound",
                    ),
                ),
            ),
            _search_configuration_candidate(
                "fx-apa06-candidate-price-upper",
                SearchConfigurationExtractionField.PRICE_UPPER_BOUND,
                field_status=SearchConfigurationFieldStatus.EVIDENCE_BOUND,
                value_kind=SearchConfigurationValueKind.RANGE_BOUND,
                parameter_candidates=(
                    _search_configuration_parameter_candidate(
                        "price_max",
                        parameter_value="5000",
                        field_status=SearchConfigurationFieldStatus.EVIDENCE_BOUND,
                        value_kind=SearchConfigurationValueKind.RANGE_BOUND,
                        evidence_suffix="apa06-price-bounds",
                    ),
                ),
                evidence_suffix="apa06-price-bounds",
                warnings=(
                    ParserWarning(
                        code=SearchConfigurationWarningCode.PRICE_BOUNDS_CANDIDATE_EVIDENCE_BOUND,
                        message="price upper bound remains evidence-bound",
                    ),
                ),
            ),
        ),
        parameter_candidates=(
            _search_configuration_parameter_candidate(
                "price_min",
                parameter_value="1000",
                field_status=SearchConfigurationFieldStatus.EVIDENCE_BOUND,
                value_kind=SearchConfigurationValueKind.RANGE_BOUND,
                evidence_suffix="apa06-price-bounds",
            ),
            _search_configuration_parameter_candidate(
                "price_max",
                parameter_value="5000",
                field_status=SearchConfigurationFieldStatus.EVIDENCE_BOUND,
                value_kind=SearchConfigurationValueKind.RANGE_BOUND,
                evidence_suffix="apa06-price-bounds",
            ),
        ),
        warnings=(
            ParserWarning(
                code=SearchConfigurationWarningCode.PRICE_BOUNDS_CANDIDATE_EVIDENCE_BOUND,
                message="price bounds remain evidence-bound",
            ),
        ),
    ),
    _search_configuration_fixture(
        "FX-APA06-STRUCTURED-FILTER-KV-CANDIDATE-001",
        "structured filter key/value candidate from safe evidence",
        evidence_suffix="apa06-structured-filter",
        normalized_filters=("filter-key:synthetic-color=value:synthetic-red",),
        search_configuration_candidates=(
            _search_configuration_candidate(
                "fx-apa06-candidate-structured-filter",
                SearchConfigurationExtractionField.STRUCTURED_FILTER,
                field_status=SearchConfigurationFieldStatus.EVIDENCE_BOUND,
                value_kind=SearchConfigurationValueKind.KEY_VALUE_PAIR,
                parameter_candidates=(
                    _search_configuration_parameter_candidate(
                        "filter-key:synthetic-color",
                        parameter_value="value:synthetic-red",
                        field_status=SearchConfigurationFieldStatus.EVIDENCE_BOUND,
                        value_kind=SearchConfigurationValueKind.KEY_VALUE_PAIR,
                        evidence_suffix="apa06-structured-filter",
                    ),
                ),
                evidence_suffix="apa06-structured-filter",
                warnings=(
                    ParserWarning(
                        code=SearchConfigurationWarningCode.STRUCTURED_FILTER_CANDIDATE_EVIDENCE_BOUND,
                        message="structured filter candidate remains evidence-bound",
                    ),
                ),
            ),
        ),
        parameter_candidates=(
            _search_configuration_parameter_candidate(
                "filter-key:synthetic-color",
                parameter_value="value:synthetic-red",
                field_status=SearchConfigurationFieldStatus.EVIDENCE_BOUND,
                value_kind=SearchConfigurationValueKind.KEY_VALUE_PAIR,
                evidence_suffix="apa06-structured-filter",
            ),
        ),
        warnings=(
            ParserWarning(
                code=SearchConfigurationWarningCode.STRUCTURED_FILTER_CANDIDATE_EVIDENCE_BOUND,
                message="structured filter candidate remains evidence-bound",
            ),
        ),
    ),
    _search_configuration_fixture(
        "FX-APA06-REPEATED-MULTIVALUE-PARAM-PRESERVED-001",
        "repeated multivalue parameter preserved as collection",
        evidence_suffix="apa06-multivalue",
        normalized_filters=(
            "filter-key:synthetic-color=value:synthetic-red",
            "filter-key:synthetic-color=value:synthetic-blue",
        ),
        search_configuration_candidates=(
            _search_configuration_candidate(
                "fx-apa06-candidate-multivalue",
                SearchConfigurationExtractionField.REPEATED_PARAMETER,
                field_status=SearchConfigurationFieldStatus.PRESERVED,
                value_kind=SearchConfigurationValueKind.COLLECTION,
                parameter_candidates=(
                    _search_configuration_parameter_candidate(
                        "filter-key:synthetic-color",
                        parameter_value="value:synthetic-red",
                        field_status=SearchConfigurationFieldStatus.PRESERVED,
                        value_kind=SearchConfigurationValueKind.COLLECTION,
                        repeated_values=("value:synthetic-red", "value:synthetic-blue"),
                        evidence_suffix="apa06-multivalue",
                    ),
                ),
                evidence_suffix="apa06-multivalue",
                warnings=(
                    ParserWarning(
                        code=SearchConfigurationWarningCode.MULTIVALUE_PARAMETER_PRESERVED,
                        message="repeated parameter values are preserved",
                    ),
                ),
            ),
        ),
        parameter_candidates=(
            _search_configuration_parameter_candidate(
                "filter-key:synthetic-color",
                parameter_value="value:synthetic-red",
                field_status=SearchConfigurationFieldStatus.PRESERVED,
                value_kind=SearchConfigurationValueKind.COLLECTION,
                repeated_values=("value:synthetic-red", "value:synthetic-blue"),
                evidence_suffix="apa06-multivalue",
            ),
        ),
        warnings=(
            ParserWarning(
                code=SearchConfigurationWarningCode.MULTIVALUE_PARAMETER_PRESERVED,
                message="repeated parameter values are preserved",
            ),
        ),
    ),
    _search_configuration_fixture(
        "FX-APA06-UNSUPPORTED-PARAMETER-WARNING-001",
        "unsupported parameter remains explicit",
        evidence_suffix="apa06-unsupported-parameter",
        status=ParserOutcomeStatus.UNSUPPORTED_STRUCTURE,
        parser_status=ParserOutcomeStatus.UNSUPPORTED_STRUCTURE,
        search_configuration_candidates=(
            _search_configuration_candidate(
                "fx-apa06-candidate-unsupported",
                SearchConfigurationExtractionField.UNSUPPORTED_PARAMETER,
                field_status=SearchConfigurationFieldStatus.UNSUPPORTED,
                value_kind=SearchConfigurationValueKind.UNSUPPORTED,
                parameter_candidates=(
                    _search_configuration_parameter_candidate(
                        "unsupported:synthetic-mode",
                        parameter_value="value:legacy",
                        field_status=SearchConfigurationFieldStatus.UNSUPPORTED,
                        value_kind=SearchConfigurationValueKind.UNSUPPORTED,
                        evidence_suffix="apa06-unsupported-parameter",
                    ),
                ),
                evidence_suffix="apa06-unsupported-parameter",
                warnings=(
                    ParserWarning(
                        code=SearchConfigurationWarningCode.UNSUPPORTED_PARAMETER_EXPLICIT,
                        message="unsupported parameter remains explicit",
                    ),
                ),
            ),
        ),
        parameter_candidates=(
            _search_configuration_parameter_candidate(
                "unsupported:synthetic-mode",
                parameter_value="value:legacy",
                field_status=SearchConfigurationFieldStatus.UNSUPPORTED,
                value_kind=SearchConfigurationValueKind.UNSUPPORTED,
                evidence_suffix="apa06-unsupported-parameter",
            ),
        ),
        warnings=(
            ParserWarning(
                code=SearchConfigurationWarningCode.UNSUPPORTED_PARAMETER_EXPLICIT,
                message="unsupported parameter remains explicit",
            ),
        ),
    ),
    _search_configuration_fixture(
        "FX-APA06-AMBIGUOUS-PARAMETER-WARNING-001",
        "ambiguous parameter remains explicit",
        evidence_suffix="apa06-ambiguous-parameter",
        status=ParserOutcomeStatus.RESULT_AMBIGUOUS,
        parser_status=ParserOutcomeStatus.RESULT_AMBIGUOUS,
        search_configuration_candidates=(
            _search_configuration_candidate(
                "fx-apa06-candidate-ambiguous",
                SearchConfigurationExtractionField.AMBIGUOUS_PARAMETER,
                field_status=SearchConfigurationFieldStatus.AMBIGUOUS,
                value_kind=SearchConfigurationValueKind.AMBIGUOUS,
                parameter_candidates=(
                    _search_configuration_parameter_candidate(
                        "mode",
                        parameter_value="synthetic-ambiguous",
                        field_status=SearchConfigurationFieldStatus.AMBIGUOUS,
                        value_kind=SearchConfigurationValueKind.AMBIGUOUS,
                        evidence_suffix="apa06-ambiguous-parameter",
                    ),
                ),
                evidence_suffix="apa06-ambiguous-parameter",
                warnings=(
                    ParserWarning(
                        code=SearchConfigurationWarningCode.AMBIGUOUS_PARAMETER_EXPLICIT,
                        message="ambiguous parameter remains explicit",
                    ),
                ),
            ),
        ),
        parameter_candidates=(
            _search_configuration_parameter_candidate(
                "mode",
                parameter_value="synthetic-ambiguous",
                field_status=SearchConfigurationFieldStatus.AMBIGUOUS,
                value_kind=SearchConfigurationValueKind.AMBIGUOUS,
                evidence_suffix="apa06-ambiguous-parameter",
            ),
        ),
        warnings=(
            ParserWarning(
                code=SearchConfigurationWarningCode.AMBIGUOUS_PARAMETER_EXPLICIT,
                message="ambiguous parameter remains explicit",
            ),
        ),
    ),
    _search_configuration_fixture(
        "FX-APA06-LOSSY-NORMALIZATION-BLOCKED-001",
        "lossy normalization is blocked and warned",
        evidence_suffix="apa06-lossy-normalization",
        status=ParserOutcomeStatus.RESULT_AMBIGUOUS,
        parser_status=ParserOutcomeStatus.RESULT_AMBIGUOUS,
        search_configuration_candidates=(
            _search_configuration_candidate(
                "fx-apa06-candidate-lossy-normalization",
                SearchConfigurationExtractionField.STRUCTURED_FILTER,
                field_status=SearchConfigurationFieldStatus.LOSSY_NORMALIZATION_BLOCKED,
                value_kind=SearchConfigurationValueKind.COLLECTION,
                parameter_candidates=(
                    _search_configuration_parameter_candidate(
                        "filter-key:synthetic-size",
                        parameter_value="value:synthetic-large",
                        field_status=SearchConfigurationFieldStatus.LOSSY_NORMALIZATION_BLOCKED,
                        value_kind=SearchConfigurationValueKind.COLLECTION,
                        repeated_values=("value:synthetic-large", "value:synthetic-medium"),
                        evidence_suffix="apa06-lossy-normalization",
                    ),
                ),
                evidence_suffix="apa06-lossy-normalization",
                warnings=(
                    ParserWarning(
                        code=SearchConfigurationWarningCode.LOSSY_NORMALIZATION_BLOCKED,
                        message="lossy normalization is blocked",
                    ),
                ),
            ),
        ),
        parameter_candidates=(
            _search_configuration_parameter_candidate(
                "filter-key:synthetic-size",
                parameter_value="value:synthetic-large",
                field_status=SearchConfigurationFieldStatus.LOSSY_NORMALIZATION_BLOCKED,
                value_kind=SearchConfigurationValueKind.COLLECTION,
                repeated_values=("value:synthetic-large", "value:synthetic-medium"),
                evidence_suffix="apa06-lossy-normalization",
            ),
        ),
        warnings=(
            ParserWarning(
                code=SearchConfigurationWarningCode.LOSSY_NORMALIZATION_BLOCKED,
                message="lossy normalization is blocked",
            ),
        ),
    ),
    _search_configuration_fixture(
        "FX-APA06-SORT-CONTEXT-UNPROVEN-001",
        "sort context candidate is present but unproven",
        evidence_suffix="apa06-sort-context",
        sort_context_reference="sort-context::synthetic-newest",
        search_configuration_candidates=(
            _search_configuration_candidate(
                "fx-apa06-candidate-sort-context",
                SearchConfigurationExtractionField.SORT_CONTEXT,
                field_status=SearchConfigurationFieldStatus.UNPROVEN,
                value_kind=SearchConfigurationValueKind.CONTEXT,
                parameter_candidates=(
                    _search_configuration_parameter_candidate(
                        "sort",
                        parameter_value="newest",
                        field_status=SearchConfigurationFieldStatus.UNPROVEN,
                        value_kind=SearchConfigurationValueKind.CONTEXT,
                        evidence_suffix="apa06-sort-context",
                    ),
                ),
                evidence_suffix="apa06-sort-context",
                warnings=(
                    ParserWarning(
                        code=SearchConfigurationWarningCode.SORT_CONTEXT_UNPROVEN,
                        message="sort context is present but not proven",
                    ),
                ),
            ),
        ),
        parameter_candidates=(
            _search_configuration_parameter_candidate(
                "sort",
                parameter_value="newest",
                field_status=SearchConfigurationFieldStatus.UNPROVEN,
                value_kind=SearchConfigurationValueKind.CONTEXT,
                evidence_suffix="apa06-sort-context",
            ),
        ),
        warnings=(
            ParserWarning(
                code=SearchConfigurationWarningCode.SORT_CONTEXT_UNPROVEN,
                message="sort context is present but not proven",
            ),
        ),
    ),
    _search_configuration_fixture(
        "FX-APA06-PAGINATION-CONTEXT-BLOCKED-001",
        "pagination context candidate is blocked from live pagination",
        evidence_suffix="apa06-pagination-context",
        status=ParserOutcomeStatus.EXPLICIT_REJECTION,
        parser_status=ParserOutcomeStatus.EXPLICIT_REJECTION,
        search_configuration_candidates=(
            _search_configuration_candidate(
                "fx-apa06-candidate-pagination-context",
                SearchConfigurationExtractionField.PAGINATION_CONTEXT,
                field_status=SearchConfigurationFieldStatus.POLICY_GATED,
                value_kind=SearchConfigurationValueKind.CONTEXT,
                parameter_candidates=(
                    _search_configuration_parameter_candidate(
                        "page",
                        parameter_value="2",
                        field_status=SearchConfigurationFieldStatus.POLICY_GATED,
                        value_kind=SearchConfigurationValueKind.CONTEXT,
                        evidence_suffix="apa06-pagination-context",
                    ),
                ),
                evidence_suffix="apa06-pagination-context",
                warnings=(
                    ParserWarning(
                        code=SearchConfigurationWarningCode.PAGINATION_CONTEXT_BLOCKED,
                        message="pagination context is blocked from live pagination",
                    ),
                ),
            ),
        ),
        parameter_candidates=(
            _search_configuration_parameter_candidate(
                "page",
                parameter_value="2",
                field_status=SearchConfigurationFieldStatus.POLICY_GATED,
                value_kind=SearchConfigurationValueKind.CONTEXT,
                evidence_suffix="apa06-pagination-context",
            ),
        ),
        warnings=(
            ParserWarning(
                code=SearchConfigurationWarningCode.PAGINATION_CONTEXT_BLOCKED,
                message="pagination context is blocked from live pagination",
            ),
        ),
    ),
    _search_configuration_fixture(
        "FX-APA06-COUNTRY-WIDE-CANDIDATE-POLICY-GATED-001",
        "country-wide candidate evidence is policy gated",
        evidence_suffix="apa06-country-wide",
        search_configuration_candidates=(
            _search_configuration_candidate(
                "fx-apa06-candidate-country-wide",
                SearchConfigurationExtractionField.COUNTRY_WIDE_CONTEXT,
                field_status=SearchConfigurationFieldStatus.POLICY_GATED,
                value_kind=SearchConfigurationValueKind.CONTEXT,
                parameter_candidates=(
                    _search_configuration_parameter_candidate(
                        "country-wide",
                        parameter_value="synthetic-country-wide",
                        field_status=SearchConfigurationFieldStatus.POLICY_GATED,
                        value_kind=SearchConfigurationValueKind.CONTEXT,
                        evidence_suffix="apa06-country-wide",
                    ),
                ),
                evidence_suffix="apa06-country-wide",
                warnings=(
                    ParserWarning(
                        code=SearchConfigurationWarningCode.COUNTRY_WIDE_POLICY_GATED,
                        message="country-wide activation remains a policy decision outside Parser",
                    ),
                ),
            ),
        ),
        parameter_candidates=(
            _search_configuration_parameter_candidate(
                "country-wide",
                parameter_value="synthetic-country-wide",
                field_status=SearchConfigurationFieldStatus.POLICY_GATED,
                value_kind=SearchConfigurationValueKind.CONTEXT,
                evidence_suffix="apa06-country-wide",
            ),
        ),
        warnings=(
            ParserWarning(
                code=SearchConfigurationWarningCode.COUNTRY_WIDE_POLICY_GATED,
                message="country-wide activation remains a policy decision outside Parser",
            ),
        ),
    ),
    _search_configuration_fixture(
        "FX-APA06-FILTER-EDITABILITY-NOT-DECLARED-001",
        "filter editability is not declared by Parser",
        evidence_suffix="apa06-filter-editability",
        search_configuration_candidates=(
            _search_configuration_candidate(
                "fx-apa06-candidate-filter-editability",
                SearchConfigurationExtractionField.FILTER_EDITABILITY_CONTEXT,
                field_status=SearchConfigurationFieldStatus.POLICY_GATED,
                value_kind=SearchConfigurationValueKind.PROVENANCE,
                parameter_candidates=(
                    _search_configuration_parameter_candidate(
                        "filter-editability",
                        parameter_value="not-declared",
                        field_status=SearchConfigurationFieldStatus.POLICY_GATED,
                        value_kind=SearchConfigurationValueKind.PROVENANCE,
                        evidence_suffix="apa06-filter-editability",
                    ),
                ),
                evidence_suffix="apa06-filter-editability",
                warnings=(
                    ParserWarning(
                        code=SearchConfigurationWarningCode.FILTER_EDITABILITY_NOT_DECLARED,
                        message="filter editability is owned by Filter Catalog, not Parser",
                    ),
                ),
            ),
        ),
        parameter_candidates=(
            _search_configuration_parameter_candidate(
                "filter-editability",
                parameter_value="not-declared",
                field_status=SearchConfigurationFieldStatus.POLICY_GATED,
                value_kind=SearchConfigurationValueKind.PROVENANCE,
                evidence_suffix="apa06-filter-editability",
            ),
        ),
        warnings=(
            ParserWarning(
                code=SearchConfigurationWarningCode.FILTER_EDITABILITY_NOT_DECLARED,
                message="filter editability is owned by Filter Catalog, not Parser",
            ),
        ),
    ),
    _search_configuration_fixture(
        "FX-APA06-BEACON-SNAPSHOT-ACCEPTANCE-NOT-PERFORMED-001",
        "beacon snapshot acceptance is not performed by Parser",
        evidence_suffix="apa06-beacon-snapshot",
        search_configuration_candidates=(
            _search_configuration_candidate(
                "fx-apa06-candidate-beacon-snapshot",
                SearchConfigurationExtractionField.BEACON_SNAPSHOT_CONTEXT,
                field_status=SearchConfigurationFieldStatus.POLICY_GATED,
                value_kind=SearchConfigurationValueKind.PROVENANCE,
                parameter_candidates=(
                    _search_configuration_parameter_candidate(
                        "beacon-snapshot",
                        parameter_value="not-performed",
                        field_status=SearchConfigurationFieldStatus.POLICY_GATED,
                        value_kind=SearchConfigurationValueKind.PROVENANCE,
                        evidence_suffix="apa06-beacon-snapshot",
                    ),
                ),
                evidence_suffix="apa06-beacon-snapshot",
                warnings=(
                    ParserWarning(
                        code=SearchConfigurationWarningCode.BEACON_SNAPSHOT_ACCEPTANCE_NOT_PERFORMED,
                        message="beacon snapshot acceptance is not performed by Parser",
                    ),
                ),
            ),
        ),
        parameter_candidates=(
            _search_configuration_parameter_candidate(
                "beacon-snapshot",
                parameter_value="not-performed",
                field_status=SearchConfigurationFieldStatus.POLICY_GATED,
                value_kind=SearchConfigurationValueKind.PROVENANCE,
                evidence_suffix="apa06-beacon-snapshot",
            ),
        ),
        warnings=(
            ParserWarning(
                code=SearchConfigurationWarningCode.BEACON_SNAPSHOT_ACCEPTANCE_NOT_PERFORMED,
                message="beacon snapshot acceptance is not performed by Parser",
            ),
        ),
    ),
    _apa07_multivalue_fixture(
        "FX-APA07-REPEATED-VALUES-ORDER-PRESERVED-001",
        "repeated parameter values remain ordered",
        evidence_suffix="apa07-repeated-order",
        repeated_values=("value:synthetic-red", "value:synthetic-blue"),
        normalized_values=("value:synthetic-red", "value:synthetic-blue"),
        multivalue_status=MultivalueNormalizationStatus.PRESERVED,
        preservation_mode=MultivaluePreservationMode.ORDERED_COLLECTION,
        warning_code=SearchConfigurationWarningCode.MULTIVALUE_PARAMETER_PRESERVED,
        warning_message="repeated parameter values remain ordered and preserved",
        normalized_filters=(
            "filter-key:synthetic-color=value:synthetic-red",
            "filter-key:synthetic-color=value:synthetic-blue",
        ),
        candidate_id="fx-apa07-candidate-repeated-order",
    ),
    _apa07_multivalue_fixture(
        "FX-APA07-DUPLICATES-PRESERVED-001",
        "duplicate repeated values remain explicit",
        evidence_suffix="apa07-duplicates-preserved",
        repeated_values=("value:synthetic-red", "value:synthetic-red", "value:synthetic-blue"),
        normalized_values=("value:synthetic-red", "value:synthetic-red", "value:synthetic-blue"),
        multivalue_status=MultivalueNormalizationStatus.PRESERVED,
        preservation_mode=MultivaluePreservationMode.ORDERED_TUPLE,
        warning_code=SearchConfigurationWarningCode.MULTIVALUE_PARAMETER_PRESERVED,
        warning_message="duplicate repeated values remain explicit",
        normalized_filters=(
            "filter-key:synthetic-color=value:synthetic-red",
            "filter-key:synthetic-color=value:synthetic-red",
            "filter-key:synthetic-color=value:synthetic-blue",
        ),
        candidate_id="fx-apa07-candidate-duplicates-preserved",
    ),
    _apa07_multivalue_fixture(
        "FX-APA07-FIRST-VALUE-OVERWRITE-BLOCKED-001",
        "first value overwrite is blocked",
        evidence_suffix="apa07-first-value-blocked",
        repeated_values=("value:synthetic-red", "value:synthetic-blue"),
        multivalue_status=MultivalueNormalizationStatus.LOSSY,
        preservation_mode=MultivaluePreservationMode.SCALAR_BLOCKED,
        loss_reason=MultivalueLossReason.FIRST_VALUE_OVERWRITE_BLOCKED,
        warning_code=SearchConfigurationWarningCode.LOSSY_NORMALIZATION_BLOCKED,
        warning_message="first-value overwrite is blocked",
        search_configuration_status=ParserOutcomeStatus.RESULT_AMBIGUOUS,
        candidate_field_status=SearchConfigurationFieldStatus.LOSSY_NORMALIZATION_BLOCKED,
        parameter_field_status=SearchConfigurationFieldStatus.LOSSY_NORMALIZATION_BLOCKED,
        candidate_id="fx-apa07-candidate-first-value-blocked",
        normalized_filters=(),
    ),
    _apa07_multivalue_fixture(
        "FX-APA07-LATER-VALUE-LOSS-BLOCKED-001",
        "later value loss is blocked",
        evidence_suffix="apa07-later-value-blocked",
        repeated_values=("value:synthetic-red", "value:synthetic-blue"),
        multivalue_status=MultivalueNormalizationStatus.LOSSY,
        preservation_mode=MultivaluePreservationMode.SCALAR_BLOCKED,
        loss_reason=MultivalueLossReason.LATER_VALUE_LOSS_BLOCKED,
        warning_code=SearchConfigurationWarningCode.LOSSY_NORMALIZATION_BLOCKED,
        warning_message="later-value loss is blocked",
        search_configuration_status=ParserOutcomeStatus.RESULT_AMBIGUOUS,
        candidate_field_status=SearchConfigurationFieldStatus.LOSSY_NORMALIZATION_BLOCKED,
        parameter_field_status=SearchConfigurationFieldStatus.LOSSY_NORMALIZATION_BLOCKED,
        candidate_id="fx-apa07-candidate-later-value-blocked",
        normalized_filters=(),
    ),
    _apa07_multivalue_fixture(
        "FX-APA07-COLLECTION-TO-SCALAR-BLOCKED-001",
        "collection-to-scalar collapse is blocked",
        evidence_suffix="apa07-collection-to-scalar",
        repeated_values=("value:synthetic-red", "value:synthetic-blue"),
        multivalue_status=MultivalueNormalizationStatus.BLOCKED,
        preservation_mode=MultivaluePreservationMode.SCALAR_BLOCKED,
        loss_reason=MultivalueLossReason.COLLECTION_TO_SCALAR_COLLAPSE_BLOCKED,
        warning_code=SearchConfigurationWarningCode.LOSSY_NORMALIZATION_BLOCKED,
        warning_message="collection-to-scalar collapse is blocked",
        search_configuration_status=ParserOutcomeStatus.RESULT_AMBIGUOUS,
        candidate_field_status=SearchConfigurationFieldStatus.LOSSY_NORMALIZATION_BLOCKED,
        parameter_field_status=SearchConfigurationFieldStatus.LOSSY_NORMALIZATION_BLOCKED,
        candidate_id="fx-apa07-candidate-collection-to-scalar",
        normalized_filters=(),
    ),
    _apa07_multivalue_fixture(
        "FX-APA07-UNSUPPORTED-MULTIVALUE-EXPLICIT-001",
        "unsupported multivalue parameter remains explicit",
        evidence_suffix="apa07-unsupported-multivalue",
        repeated_values=("value:synthetic-legacy", "value:synthetic-modern"),
        multivalue_status=MultivalueNormalizationStatus.UNSUPPORTED,
        preservation_mode=MultivaluePreservationMode.SCALAR_BLOCKED,
        loss_reason=MultivalueLossReason.UNSUPPORTED_MULTIVALUE_PARAMETER,
        warning_code=SearchConfigurationWarningCode.UNSUPPORTED_PARAMETER_EXPLICIT,
        warning_message="unsupported multivalue parameter remains explicit",
        search_configuration_status=ParserOutcomeStatus.UNSUPPORTED_STRUCTURE,
        candidate_field_status=SearchConfigurationFieldStatus.UNSUPPORTED,
        parameter_field_status=SearchConfigurationFieldStatus.UNSUPPORTED,
        candidate_value_kind=SearchConfigurationValueKind.UNSUPPORTED,
        parameter_value_kind=SearchConfigurationValueKind.UNSUPPORTED,
        candidate_id="fx-apa07-candidate-unsupported-multivalue",
        normalized_filters=(),
    ),
    _apa07_multivalue_fixture(
        "FX-APA07-AMBIGUOUS-MULTIVALUE-EXPLICIT-001",
        "ambiguous multivalue parameter remains explicit",
        evidence_suffix="apa07-ambiguous-multivalue",
        repeated_values=("value:synthetic-red", "value:synthetic-blue"),
        multivalue_status=MultivalueNormalizationStatus.AMBIGUOUS,
        preservation_mode=MultivaluePreservationMode.SCALAR_BLOCKED,
        loss_reason=MultivalueLossReason.AMBIGUOUS_MULTIVALUE_PARAMETER,
        warning_code=SearchConfigurationWarningCode.AMBIGUOUS_PARAMETER_EXPLICIT,
        warning_message="ambiguous multivalue parameter remains explicit",
        search_configuration_status=ParserOutcomeStatus.RESULT_AMBIGUOUS,
        candidate_field_status=SearchConfigurationFieldStatus.AMBIGUOUS,
        parameter_field_status=SearchConfigurationFieldStatus.AMBIGUOUS,
        candidate_value_kind=SearchConfigurationValueKind.AMBIGUOUS,
        parameter_value_kind=SearchConfigurationValueKind.AMBIGUOUS,
        candidate_id="fx-apa07-candidate-ambiguous-multivalue",
        normalized_filters=(),
    ),
    _apa07_multivalue_fixture(
        "FX-APA07-LOSSY-NORMALIZATION-EXPLICIT-001",
        "lossy multivalue normalization remains explicit",
        evidence_suffix="apa07-lossy-explicit",
        repeated_values=("value:synthetic-red", "value:synthetic-red", "value:synthetic-blue"),
        multivalue_status=MultivalueNormalizationStatus.LOSSY,
        preservation_mode=MultivaluePreservationMode.SCALAR_BLOCKED,
        loss_reason=MultivalueLossReason.DUPLICATE_REMOVAL_BLOCKED,
        warning_code=SearchConfigurationWarningCode.LOSSY_NORMALIZATION_BLOCKED,
        warning_message="lossy multivalue normalization remains explicit",
        search_configuration_status=ParserOutcomeStatus.RESULT_AMBIGUOUS,
        candidate_field_status=SearchConfigurationFieldStatus.LOSSY_NORMALIZATION_BLOCKED,
        parameter_field_status=SearchConfigurationFieldStatus.LOSSY_NORMALIZATION_BLOCKED,
        candidate_id="fx-apa07-candidate-lossy-explicit",
        normalized_filters=(),
    ),
    _apa07_multivalue_fixture(
        "FX-APA07-PROFILE-BOUND-COLLECTION-PRESERVED-001",
        "approved current profile preserves the multivalue collection",
        evidence_suffix="apa07-profile-bound",
        repeated_values=("value:synthetic-red", "value:synthetic-blue"),
        normalized_values=("value:synthetic-red", "value:synthetic-blue"),
        multivalue_status=MultivalueNormalizationStatus.PRESERVED,
        preservation_mode=MultivaluePreservationMode.ORDERED_COLLECTION,
        warning_code=SearchConfigurationWarningCode.MULTIVALUE_PARAMETER_PRESERVED,
        warning_message="approved current profile preserves the multivalue collection",
        normalized_filters=(
            "filter-key:synthetic-color=value:synthetic-red",
            "filter-key:synthetic-color=value:synthetic-blue",
        ),
        candidate_id="fx-apa07-candidate-profile-bound",
    ),
    _apa07_multivalue_fixture(
        "FX-APA07-PROFILE-NOT-CURRENT-BLOCKS-001",
        "stale compatibility profile blocks profile-specific normalization",
        evidence_suffix="apa07-profile-stale",
        repeated_values=("value:synthetic-red", "value:synthetic-blue"),
        multivalue_status=MultivalueNormalizationStatus.BLOCKED,
        preservation_mode=MultivaluePreservationMode.SCALAR_BLOCKED,
        loss_reason=MultivalueLossReason.PROFILE_STALE,
        warning_code=ParserWarningCode.STALE_COMPATIBILITY_PROFILE,
        warning_message="stale compatibility profile blocks profile-specific normalization",
        profile=_multivalue_profile(
            "fx-apa07-profile-stale",
            evidence_suffix="apa07-profile-stale",
            lifecycle_status=CompatibilityProfileLifecycleStatus.STALE,
            reference_status=ReferenceOutcomeStatus.REFERENCE_STALE,
        ),
        request=_request(
            "fx-apa07-request-profile-stale",
            _multivalue_profile(
                "fx-apa07-profile-stale",
                evidence_suffix="apa07-profile-stale",
                lifecycle_status=CompatibilityProfileLifecycleStatus.STALE,
                reference_status=ReferenceOutcomeStatus.REFERENCE_STALE,
            ),
            purpose="search-configuration-extraction",
            safe_source_reference="source-ref:beacon-revision-070",
            source_reference=_MULTIVALUE_SAFE_NORMALIZATION_SOURCE_REFERENCE,
            source_boundary_outcome=_MULTIVALUE_SAFE_NORMALIZATION_BOUNDARY,
            requested_page_numbers=(1,),
        ),
        transport=_transport(
            "fx-apa07-transport-profile-stale",
            status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
            request_reference="fx-apa07-request-profile-stale",
            response_reference="response::synthetic::profile-stale",
            route_reference="route::synthetic",
            evidence_reference_suffix="apa07-profile-stale",
        ),
        search_configuration_status=CompatibilityProfileLifecycleStatus.STALE,
        parser_status=ParserOutcomeStatus.RESULT_AMBIGUOUS,
        candidate_field_status=SearchConfigurationFieldStatus.POLICY_GATED,
        parameter_field_status=SearchConfigurationFieldStatus.POLICY_GATED,
        candidate_id="fx-apa07-candidate-profile-stale",
        normalized_filters=(),
    ),
    _apa07_multivalue_fixture(
        "FX-APA07-PROFILE-MISSING-BLOCKS-001",
        "missing compatibility profile blocks profile-specific normalization",
        evidence_suffix="apa07-profile-missing",
        repeated_values=("value:synthetic-red", "value:synthetic-blue"),
        multivalue_status=MultivalueNormalizationStatus.BLOCKED,
        preservation_mode=MultivaluePreservationMode.SCALAR_BLOCKED,
        loss_reason=MultivalueLossReason.PROFILE_MISSING,
        warning_code=ParserWarningCode.UNAVAILABLE_PROFILE_WARNING,
        warning_message="missing compatibility profile blocks profile-specific normalization",
        profile=_multivalue_profile(
            "fx-apa07-profile-missing",
            evidence_suffix="apa07-profile-missing",
            lifecycle_status=CompatibilityProfileLifecycleStatus.UNAVAILABLE,
            reference_status=ReferenceOutcomeStatus.REFERENCE_MISSING,
        ),
        request=_request(
            "fx-apa07-request-profile-missing",
            _multivalue_profile(
                "fx-apa07-profile-missing",
                evidence_suffix="apa07-profile-missing",
                lifecycle_status=CompatibilityProfileLifecycleStatus.UNAVAILABLE,
                reference_status=ReferenceOutcomeStatus.REFERENCE_MISSING,
            ),
            purpose="search-configuration-extraction",
            safe_source_reference="source-ref:beacon-revision-070",
            source_reference=_MULTIVALUE_SAFE_NORMALIZATION_SOURCE_REFERENCE,
            source_boundary_outcome=_MULTIVALUE_SAFE_NORMALIZATION_BOUNDARY,
            requested_page_numbers=(1,),
        ),
        transport=_transport(
            "fx-apa07-transport-profile-missing",
            status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
            request_reference="fx-apa07-request-profile-missing",
            response_reference="response::synthetic::profile-missing",
            route_reference="route::synthetic",
            evidence_reference_suffix="apa07-profile-missing",
        ),
        search_configuration_status=ReferenceOutcomeStatus.REFERENCE_MISSING,
        parser_status=ParserOutcomeStatus.RESULT_AMBIGUOUS,
        reference_status=ReferenceOutcomeStatus.REFERENCE_MISSING,
        candidate_field_status=SearchConfigurationFieldStatus.POLICY_GATED,
        parameter_field_status=SearchConfigurationFieldStatus.POLICY_GATED,
        candidate_id="fx-apa07-candidate-profile-missing",
        normalized_filters=(),
    ),
    _apa07_multivalue_fixture(
        "FX-APA07-PROFILE-DISPUTED-BLOCKS-001",
        "disputed compatibility profile blocks profile-specific normalization",
        evidence_suffix="apa07-profile-disputed",
        repeated_values=("value:synthetic-red", "value:synthetic-blue"),
        multivalue_status=MultivalueNormalizationStatus.BLOCKED,
        preservation_mode=MultivaluePreservationMode.SCALAR_BLOCKED,
        loss_reason=MultivalueLossReason.PROFILE_DISPUTED,
        warning_code=ParserWarningCode.DISPUTED_PROFILE_WARNING,
        warning_message="disputed compatibility profile blocks profile-specific normalization",
        profile=_multivalue_profile(
            "fx-apa07-profile-disputed",
            evidence_suffix="apa07-profile-disputed",
            lifecycle_status=CompatibilityProfileLifecycleStatus.DISPUTED,
            reference_status=ReferenceOutcomeStatus.REFERENCE_DISPUTED,
        ),
        request=_request(
            "fx-apa07-request-profile-disputed",
            _multivalue_profile(
                "fx-apa07-profile-disputed",
                evidence_suffix="apa07-profile-disputed",
                lifecycle_status=CompatibilityProfileLifecycleStatus.DISPUTED,
                reference_status=ReferenceOutcomeStatus.REFERENCE_DISPUTED,
            ),
            purpose="search-configuration-extraction",
            safe_source_reference="source-ref:beacon-revision-070",
            source_reference=_MULTIVALUE_SAFE_NORMALIZATION_SOURCE_REFERENCE,
            source_boundary_outcome=_MULTIVALUE_SAFE_NORMALIZATION_BOUNDARY,
            requested_page_numbers=(1,),
        ),
        transport=_transport(
            "fx-apa07-transport-profile-disputed",
            status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
            request_reference="fx-apa07-request-profile-disputed",
            response_reference="response::synthetic::profile-disputed",
            route_reference="route::synthetic",
            evidence_reference_suffix="apa07-profile-disputed",
        ),
        search_configuration_status=ReferenceOutcomeStatus.REFERENCE_DISPUTED,
        parser_status=ParserOutcomeStatus.RESULT_AMBIGUOUS,
        reference_status=ReferenceOutcomeStatus.REFERENCE_DISPUTED,
        candidate_field_status=SearchConfigurationFieldStatus.POLICY_GATED,
        parameter_field_status=SearchConfigurationFieldStatus.POLICY_GATED,
        candidate_id="fx-apa07-candidate-profile-disputed",
        normalized_filters=(),
    ),
    _apa07_multivalue_fixture(
        "FX-APA07-SOURCE-BOUNDARY-BLOCKS-001",
        "invalid source boundary blocks multivalue normalization",
        evidence_suffix="apa07-source-boundary",
        repeated_values=("value:synthetic-red", "value:synthetic-blue"),
        multivalue_status=MultivalueNormalizationStatus.BLOCKED,
        preservation_mode=MultivaluePreservationMode.SCALAR_BLOCKED,
        loss_reason=MultivalueLossReason.SOURCE_BOUNDARY_INVALID,
        warning_code=ParserWarningCode.SOURCE_URL_MALFORMED,
        warning_message="invalid source boundary blocks multivalue normalization",
        source_boundary_outcome=_source_boundary(
            "fx-apa07-boundary-source-invalid",
            _MULTIVALUE_SAFE_NORMALIZATION_SOURCE_REFERENCE,
            status=SourceBoundaryStatus.SOURCE_URL_MALFORMED,
            policy_requirements=(
                SourceBoundaryPolicyRequirement.HOST_POLICY_REQUIRED,
                SourceBoundaryPolicyRequirement.PATH_POLICY_REQUIRED,
                SourceBoundaryPolicyRequirement.QUERY_POLICY_REQUIRED,
            ),
            risk_codes=(SourceBoundaryRiskCode.SOURCE_URL_MALFORMED,),
        ),
        search_configuration_status=SourceBoundaryStatus.SOURCE_URL_MALFORMED,
        parser_status=ParserOutcomeStatus.RESULT_AMBIGUOUS,
        candidate_field_status=SearchConfigurationFieldStatus.POLICY_GATED,
        parameter_field_status=SearchConfigurationFieldStatus.POLICY_GATED,
        candidate_id="fx-apa07-candidate-source-boundary-blocked",
        normalized_filters=(),
    ),
    _apa07_multivalue_fixture(
        "FX-APA07-RESPONSE-CLASSIFICATION-BLOCKS-001",
        "non-usable response classification blocks trusted normalization",
        evidence_suffix="apa07-response-classification",
        repeated_values=("value:synthetic-red", "value:synthetic-blue"),
        multivalue_status=MultivalueNormalizationStatus.BLOCKED,
        preservation_mode=MultivaluePreservationMode.SCALAR_BLOCKED,
        loss_reason=MultivalueLossReason.RESPONSE_CLASSIFICATION_NOT_TRUSTED,
        warning_code=SearchConfigurationWarningCode.LOSSY_NORMALIZATION_BLOCKED,
        warning_message="non-usable response classification blocks trusted normalization",
        transport_response_classification=_transport_response_classification(
            "fx-apa07-response-classification",
            _REQUEST_MULTIVALUE_SAFE_NORMALIZATION,
            _TRANSPORT_MULTIVALUE_SAFE_NORMALIZATION,
            status=ParserOutcomeStatus.RESULT_AMBIGUOUS,
            provider_response_evidence_class=ProviderResponseEvidenceClass.RESULT_AMBIGUOUS,
            response_completeness_status=ResponseCompletenessStatus.AMBIGUOUS,
            parser_status=ParserOutcomeStatus.RESULT_AMBIGUOUS,
            evidence_suffix="apa07-response-classification",
        ),
        search_configuration_status=ParserOutcomeStatus.RESULT_AMBIGUOUS,
        parser_status=ParserOutcomeStatus.RESULT_AMBIGUOUS,
        candidate_field_status=SearchConfigurationFieldStatus.LOSSY_NORMALIZATION_BLOCKED,
        parameter_field_status=SearchConfigurationFieldStatus.LOSSY_NORMALIZATION_BLOCKED,
        candidate_id="fx-apa07-candidate-response-classification-blocked",
        normalized_filters=(),
    ),
    _search_configuration_fixture(
        "FX-APA07-FILTER-EDITABILITY-NOT-DECLARED-001",
        "filter editability is not declared by Parser",
        evidence_suffix="apa07-filter-editability",
        search_configuration_candidates=(
            _search_configuration_candidate(
                "fx-apa07-candidate-filter-editability",
                SearchConfigurationExtractionField.FILTER_EDITABILITY_CONTEXT,
                field_status=SearchConfigurationFieldStatus.POLICY_GATED,
                value_kind=SearchConfigurationValueKind.PROVENANCE,
                parameter_candidates=(
                    _search_configuration_parameter_candidate(
                        "filter-editability",
                        parameter_value="not-declared",
                        field_status=SearchConfigurationFieldStatus.POLICY_GATED,
                        value_kind=SearchConfigurationValueKind.PROVENANCE,
                        evidence_suffix="apa07-filter-editability",
                    ),
                ),
                evidence_suffix="apa07-filter-editability",
                warnings=(
                    ParserWarning(
                        code=SearchConfigurationWarningCode.FILTER_EDITABILITY_NOT_DECLARED,
                        message="filter editability is owned by Filter Catalog, not Parser",
                    ),
                ),
            ),
        ),
        parameter_candidates=(
            _search_configuration_parameter_candidate(
                "filter-editability",
                parameter_value="not-declared",
                field_status=SearchConfigurationFieldStatus.POLICY_GATED,
                value_kind=SearchConfigurationValueKind.PROVENANCE,
                evidence_suffix="apa07-filter-editability",
            ),
        ),
        warnings=(
            ParserWarning(
                code=SearchConfigurationWarningCode.FILTER_EDITABILITY_NOT_DECLARED,
                message="filter editability is owned by Filter Catalog, not Parser",
            ),
        ),
    ),
    _search_configuration_fixture(
        "FX-APA07-BEACON-NO-MUTATION-001",
        "beacon snapshot acceptance is not performed by Parser",
        evidence_suffix="apa07-beacon-no-mutation",
        search_configuration_candidates=(
            _search_configuration_candidate(
                "fx-apa07-candidate-beacon-no-mutation",
                SearchConfigurationExtractionField.BEACON_SNAPSHOT_CONTEXT,
                field_status=SearchConfigurationFieldStatus.POLICY_GATED,
                value_kind=SearchConfigurationValueKind.PROVENANCE,
                parameter_candidates=(
                    _search_configuration_parameter_candidate(
                        "beacon-snapshot",
                        parameter_value="not-performed",
                        field_status=SearchConfigurationFieldStatus.POLICY_GATED,
                        value_kind=SearchConfigurationValueKind.PROVENANCE,
                        evidence_suffix="apa07-beacon-no-mutation",
                    ),
                ),
                evidence_suffix="apa07-beacon-no-mutation",
                warnings=(
                    ParserWarning(
                        code=SearchConfigurationWarningCode.BEACON_SNAPSHOT_ACCEPTANCE_NOT_PERFORMED,
                        message="beacon snapshot acceptance is not performed by Parser",
                    ),
                ),
            ),
        ),
        parameter_candidates=(
            _search_configuration_parameter_candidate(
                "beacon-snapshot",
                parameter_value="not-performed",
                field_status=SearchConfigurationFieldStatus.POLICY_GATED,
                value_kind=SearchConfigurationValueKind.PROVENANCE,
                evidence_suffix="apa07-beacon-no-mutation",
            ),
        ),
        warnings=(
            ParserWarning(
                code=SearchConfigurationWarningCode.BEACON_SNAPSHOT_ACCEPTANCE_NOT_PERFORMED,
                message="beacon snapshot acceptance is not performed by Parser",
            ),
        ),
    ),
    _search_configuration_fixture(
        "FX-APA07-SCAN-NO-MUTATION-001",
        "scan baseline and new-listing ownership remain outside Parser",
        evidence_suffix="apa07-scan-no-mutation",
        search_configuration_candidates=(
            _search_configuration_candidate(
                "fx-apa07-candidate-scan-no-mutation",
                SearchConfigurationExtractionField.PAGINATION_CONTEXT,
                field_status=SearchConfigurationFieldStatus.POLICY_GATED,
                value_kind=SearchConfigurationValueKind.CONTEXT,
                parameter_candidates=(
                    _search_configuration_parameter_candidate(
                        "scan-state",
                        parameter_value="not-performed",
                        field_status=SearchConfigurationFieldStatus.POLICY_GATED,
                        value_kind=SearchConfigurationValueKind.CONTEXT,
                        evidence_suffix="apa07-scan-no-mutation",
                    ),
                ),
                evidence_suffix="apa07-scan-no-mutation",
                warnings=(
                    ParserWarning(
                        code=SearchConfigurationWarningCode.PAGINATION_CONTEXT_BLOCKED,
                        message="scan baseline, anchors and new listings remain outside Parser",
                    ),
                ),
            ),
        ),
        parameter_candidates=(
            _search_configuration_parameter_candidate(
                "scan-state",
                parameter_value="not-performed",
                field_status=SearchConfigurationFieldStatus.POLICY_GATED,
                value_kind=SearchConfigurationValueKind.CONTEXT,
                evidence_suffix="apa07-scan-no-mutation",
            ),
        ),
        parser_status=ParserOutcomeStatus.EXPLICIT_REJECTION,
        warnings=(
            ParserWarning(
                code=SearchConfigurationWarningCode.PAGINATION_CONTEXT_BLOCKED,
                message="scan baseline, anchors and new listings remain outside Parser",
            ),
        ),
    ),
    _fixture(
        "FX-APA08-TIER1-LISTING-CARD-PROVEN-001",
        "tier 1 listing card is proven by current compatibility profile",
        _REQUEST_APA08_TIER1_PROVEN,
        _TRANSPORT_APA08_TIER1_PROVEN,
        _ATTEMPT_APA08_TIER1_PROVEN,
        listing_page_parse_outcome=_PAGE_APA08_TIER1_PROVEN,
    ),
    _fixture(
        "FX-APA08-OPTIONAL-DETAIL-FIELDS-UNAVAILABLE-001",
        "optional tier 2 fields remain unavailable without failing Tier 1 candidate",
        _REQUEST_APA08_OPTIONAL_DETAIL_UNAVAILABLE,
        _TRANSPORT_APA08_OPTIONAL_DETAIL_UNAVAILABLE,
        _ATTEMPT_APA08_OPTIONAL_DETAIL_UNAVAILABLE,
        listing_page_parse_outcome=_PAGE_APA08_OPTIONAL_DETAIL_UNAVAILABLE,
    ),
    _fixture(
        "FX-APA08-PHONE-VALUE-PROOF-GATED-001",
        "phone value remains proof-gated and empty",
        _REQUEST_APA08_PHONE_VALUE_PROOF_GATED,
        _TRANSPORT_APA08_PHONE_VALUE_PROOF_GATED,
        _ATTEMPT_APA08_PHONE_VALUE_PROOF_GATED,
        listing_page_parse_outcome=_PAGE_APA08_PHONE_VALUE_PROOF_GATED,
    ),
    _fixture(
        "FX-APA08-OPTIONAL-FIELD-AMBIGUOUS-WARNING-001",
        "ambiguous optional field emits an explicit warning",
        _REQUEST_APA08_OPTIONAL_FIELD_AMBIGUOUS,
        _TRANSPORT_APA08_OPTIONAL_FIELD_AMBIGUOUS,
        _ATTEMPT_APA08_OPTIONAL_FIELD_AMBIGUOUS,
        listing_page_parse_outcome=_PAGE_APA08_OPTIONAL_FIELD_AMBIGUOUS,
    ),
    _fixture(
        "FX-APA08-FIELD-PROVENANCE-REQUIRED-001",
        "proven field requires evidence and current profile",
        _REQUEST_APA08_FIELD_PROVENANCE_REQUIRED,
        _TRANSPORT_APA08_FIELD_PROVENANCE_REQUIRED,
        _ATTEMPT_APA08_FIELD_PROVENANCE_REQUIRED,
        listing_page_parse_outcome=_PAGE_APA08_FIELD_PROVENANCE_REQUIRED,
    ),
    _fixture(
        "FX-APA08-NO-SCAN-NEWNESS-MUTATION-001",
        "listing normalization does not own scan newness mutation",
        _REQUEST_APA08_NO_SCAN_NEWNESS_MUTATION,
        _TRANSPORT_APA08_NO_SCAN_NEWNESS_MUTATION,
        _ATTEMPT_APA08_NO_SCAN_NEWNESS_MUTATION,
        listing_page_parse_outcome=_PAGE_APA08_NO_SCAN_NEWNESS_MUTATION,
    ),
    _fixture(
        "FX-APA08-NO-RAW-PROVIDER-PAYLOAD-001",
        "listing normalization carries no raw provider payload",
        _REQUEST_APA08_NO_RAW_PROVIDER_PAYLOAD,
        _TRANSPORT_APA08_NO_RAW_PROVIDER_PAYLOAD,
        _ATTEMPT_APA08_NO_RAW_PROVIDER_PAYLOAD,
        listing_page_parse_outcome=_PAGE_APA08_NO_RAW_PROVIDER_PAYLOAD,
    ),
)

SYNTHETIC_FIXTURE_BY_ID: Final[dict[str, SyntheticFixtureCase]] = {
    fixture.fixture_id: fixture for fixture in SYNTHETIC_FIXTURE_CASES
}

FIXTURE_IDS: Final[tuple[str, ...]] = tuple(
    fixture.fixture_id for fixture in SYNTHETIC_FIXTURE_CASES
)

__all__: Final[tuple[str, ...]] = (
    "SyntheticFixtureCase",
    "SYNTHETIC_FIXTURE_CASES",
    "SYNTHETIC_FIXTURE_BY_ID",
    "FIXTURE_IDS",
)
