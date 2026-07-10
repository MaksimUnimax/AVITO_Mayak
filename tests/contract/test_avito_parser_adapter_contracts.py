from __future__ import annotations

from dataclasses import FrozenInstanceError, fields

import pytest

from mayak.modules import avito_parser_adapter
from mayak.modules.avito_parser_adapter import (
    MODULE_ID,
    SYNTHETIC_FIXTURE_BY_ID,
    CompatibilityChangeClass,
    CompatibilityProfileAuthorityClass,
    CompatibilityProfileLifecycleStatus,
    CompatibilityRevalidationTrigger,
    ListingCandidateStatus,
    ListingCardCandidate,
    ListingFieldAvailability,
    ListingFieldCandidate,
    ListingFieldFamily,
    ListingFieldQuality,
    ListingFieldTier,
    ListingOrderingEvidence,
    ListingPageParseOutcome,
    ListingSortContextStatus,
    MultivalueLossReason,
    MultivalueNormalizationOutcome,
    MultivalueNormalizationRule,
    MultivalueNormalizationStatus,
    MultivaluePreservationMode,
    NormalizedListingCandidate,
    ObservedListingPosition,
    ParserAttemptOutcome,
    ParserCompatibilityOutcome,
    ParserCompatibilityProfile,
    ParserEvidenceReference,
    ParserOutcomeExplanation,
    ParserOutcomeStatus,
    ParserRequestEnvelope,
    ParserResponseClassificationRule,
    ParserScanOrderingHandoff,
    ParserSourceReference,
    ParserWarning,
    ParserWarningCode,
    ProviderResponseEvidenceClass,
    ReferenceOutcomeStatus,
    ResponseCompletenessStatus,
    ResponseRestrictionSignal,
    ScanOrderingHandoffStatus,
    SearchConfigurationCandidate,
    SearchConfigurationEvidence,
    SearchConfigurationExtractionField,
    SearchConfigurationExtractionOutcome,
    SearchConfigurationFieldStatus,
    SearchConfigurationParameterCandidate,
    SearchConfigurationValueKind,
    SearchConfigurationWarningCode,
    SourceBoundaryOutcome,
    SourceBoundaryPolicyRequirement,
    SourceBoundaryRiskCode,
    SourceBoundaryStatus,
    SourceReferenceKind,
    TransportOutcomeReference,
    TransportOutcomeStatus,
    TransportResponseClassificationOutcome,
)
from mayak.platform import boundaries


def test_package_exports_expected_module_id_and_contract_symbols() -> None:
    assert MODULE_ID == boundaries.AVITO_PARSER_ADAPTER_MODULE_ID
    assert avito_parser_adapter.MODULE_ID == boundaries.AVITO_PARSER_ADAPTER_MODULE_ID

    expected_symbols = {
        "CompatibilityProfileLifecycleStatus",
        "CompatibilityProfileAuthorityClass",
        "CompatibilityChangeClass",
        "CompatibilityRevalidationTrigger",
        "ParserCompatibilityProfile",
        "ParserCompatibilityOutcome",
        "ParserRequestEnvelope",
        "TransportOutcomeReference",
        "TransportResponseClassificationOutcome",
        "ParserAttemptOutcome",
        "SearchSourceAnalysisOutcome",
        "SearchConfigurationExtractionOutcome",
        "ListingPageParseOutcome",
        "ListingBatchParseOutcome",
        "ParserWarning",
        "ParserEvidenceReference",
        "ParserOutcomeExplanation",
        "ParserResponseClassificationRule",
        "ParserSourceReference",
        "SearchConfigurationCandidate",
        "SearchConfigurationEvidence",
        "SearchConfigurationExtractionField",
        "SearchConfigurationExtractionOutcome",
        "SearchConfigurationFieldStatus",
        "SearchConfigurationParameterCandidate",
        "MultivalueNormalizationOutcome",
        "MultivalueNormalizationRule",
        "MultivalueNormalizationStatus",
        "MultivaluePreservationMode",
        "MultivalueLossReason",
        "SearchConfigurationValueKind",
        "SearchConfigurationWarningCode",
        "ListingFieldFamily",
        "ListingFieldTier",
        "ListingFieldAvailability",
        "ListingFieldQuality",
        "ListingCandidateStatus",
        "ListingSortContextStatus",
        "ScanOrderingHandoffStatus",
        "SourceBoundaryOutcome",
        "SourceBoundaryPolicyRequirement",
        "SourceBoundaryRiskCode",
        "SourceBoundaryStatus",
        "SourceReferenceKind",
        "ProviderResponseEvidenceClass",
        "ResponseCompletenessStatus",
        "ResponseRestrictionSignal",
        "ListingFieldCandidate",
        "NormalizedListingCandidate",
        "ListingCardCandidate",
        "ObservedListingPosition",
        "ListingOrderingEvidence",
        "ParserScanOrderingHandoff",
        "FIXTURE_IDS",
        "SYNTHETIC_FIXTURE_CASES",
        "SYNTHETIC_FIXTURE_BY_ID",
    }
    assert expected_symbols.issubset(set(avito_parser_adapter.__all__))


def test_contract_objects_are_frozen_and_safe() -> None:
    evidence = ParserEvidenceReference(
        reference_id="fx::contract::evidence",
        evidence_kind="contract",
    )
    warning = ParserWarning(
        code=ParserWarningCode.EMPTY_RESULT_PROVEN,
        message="clean empty result is explicit",
        evidence_reference=evidence,
    )
    profile = ParserCompatibilityProfile(
        profile_id="fx::contract::profile",
        semantic_version="2026.07.09",
        profile_version="2026.07.09",
        lifecycle_status=CompatibilityProfileLifecycleStatus.CURRENT,
        authority_class=CompatibilityProfileAuthorityClass.OBSERVATION_ONLY,
        authority_scope=("observation-only",),
        reference_ids=("AVITO-PRIMARY-PARSER-001",),
        primary_reference_repository="Duff89/parser_avito",
        primary_reference_commit="48441c352e36919abef13c436f41a3a62636da17",
        reference_status=ReferenceOutcomeStatus.CURRENT,
        evidence_reference=evidence,
        supported_extraction_claims=("tier-1 semantic claims",),
        unsupported_extraction_claims=("official/public contract",),
        required_fields=("profile_id", "semantic_version", "reference_ids"),
        completeness_rules=("claims are explicit",),
        warning_mappings=("REFERENCE_CHANGED->COMPATIBILITY_REVALIDATION_REQUIRED",),
        error_mappings=("REFERENCE_WITHDRAWN->WITHDRAWN_PROFILE_BLOCKED",),
        fixture_ids=("FX-APA03-CURRENT-REFERENCE-PROFILE-001",),
        acceptance_matrix_rows=("APA03::CURRENT::TIER1::ACCEPT",),
        revalidation_triggers=(CompatibilityRevalidationTrigger.REFERENCE_CHANGED,),
        compatibility_change_classes=(CompatibilityChangeClass.COMPATIBLE,),
    )
    explanation = ParserOutcomeExplanation(
        summary="safe summary",
        reason_code="FX::SAFE",
        status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
        evidence_references=(evidence,),
        warnings=(warning,),
    )
    outcome = ParserCompatibilityOutcome(
        outcome_id="fx::contract::compatibility-outcome",
        compatibility_profile=profile,
        lifecycle_status=CompatibilityProfileLifecycleStatus.CURRENT,
        change_class=CompatibilityChangeClass.COMPATIBLE,
        status=CompatibilityProfileLifecycleStatus.CURRENT,
        warnings=(warning,),
        error_messages=("none",),
        revalidation_triggers=(CompatibilityRevalidationTrigger.REFERENCE_CHANGED,),
        evidence_references=(evidence,),
        explanation=explanation,
    )
    request = ParserRequestEnvelope(
        request_id="fx::contract::request",
        contract_name="mayak.avito.parser.request",
        contract_version="1.0",
        producer="mayak.tests.synthetic",
        purpose="response-classification",
        compatibility_profile=profile,
        safe_source_reference="bounded-source-value",
        configuration_revision_id="cfg::contract::001",
        safe_transport_reference="transport::contract",
    )
    transport_outcome = TransportOutcomeReference(
        transport_reference_id="fx::contract::transport",
        transport_status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
        request_reference=request.request_id,
        response_reference="response::contract",
        route_reference="route::contract",
    )
    classification_rule = ParserResponseClassificationRule(
        rule_id="fx::contract::classification-rule",
        summary="transport success alone is insufficient",
        required_transport_statuses=(TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,),
        required_parser_statuses=(ParserOutcomeStatus.USABLE_RESPONSE,),
        required_provider_evidence_classes=(ProviderResponseEvidenceClass.USABLE_RESPONSE,),
        required_response_completeness_statuses=(ResponseCompletenessStatus.COMPLETE,),
        required_response_restriction_signals=(ResponseRestrictionSignal.NONE,),
        requires_current_profile_proof=True,
        notes=("transport success alone is insufficient",),
    )
    classification = TransportResponseClassificationOutcome(
        classification_id="fx::contract::classification",
        status=ParserOutcomeStatus.USABLE_RESPONSE,
        transport_status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
        parser_status=ParserOutcomeStatus.USABLE_RESPONSE,
        reference_status=ReferenceOutcomeStatus.CURRENT,
        provider_response_evidence_class=ProviderResponseEvidenceClass.USABLE_RESPONSE,
        response_completeness_status=ResponseCompletenessStatus.COMPLETE,
        response_restriction_signal=ResponseRestrictionSignal.NONE,
        classification_rule=classification_rule,
        transport_outcome=transport_outcome,
        request_envelope=request,
        evidence_references=(evidence,),
        explanation=explanation,
        notes=("synthetic transport/response classification",),
    )
    attempt = ParserAttemptOutcome(
        attempt_id="fx::contract::attempt",
        transport_status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
        parser_status=ParserOutcomeStatus.USABLE_RESPONSE,
        reference_status=ReferenceOutcomeStatus.CURRENT,
        request_envelope=request,
        transport_outcome=transport_outcome,
        response_reference="response::contract",
        transport_response_classification=classification,
        warnings=(warning,),
        evidence_references=(evidence,),
        explanation=explanation,
    )

    assert profile.evidence_reference is evidence
    assert explanation.warnings == (warning,)
    assert outcome.compatibility_profile is profile
    assert outcome.change_class is CompatibilityChangeClass.COMPATIBLE
    assert outcome.lifecycle_status is CompatibilityProfileLifecycleStatus.CURRENT
    assert outcome.revalidation_triggers == (CompatibilityRevalidationTrigger.REFERENCE_CHANGED,)
    assert attempt.transport_response_classification is classification
    assert classification.classification_rule is classification_rule
    assert (
        classification.provider_response_evidence_class
        is ProviderResponseEvidenceClass.USABLE_RESPONSE
    )
    assert classification.response_completeness_status is ResponseCompletenessStatus.COMPLETE
    assert classification.response_restriction_signal is ResponseRestrictionSignal.NONE
    assert {field.name for field in fields(ParserAttemptOutcome)} >= {
        "transport_response_classification",
        "transport_status",
        "parser_status",
        "reference_status",
        "request_envelope",
        "transport_outcome",
        "response_reference",
    }
    assert {field.name for field in fields(TransportResponseClassificationOutcome)} >= {
        "classification_id",
        "status",
        "transport_status",
        "parser_status",
        "reference_status",
        "provider_response_evidence_class",
        "response_completeness_status",
        "response_restriction_signal",
        "classification_rule",
        "transport_outcome",
        "request_envelope",
        "evidence_references",
        "explanation",
        "notes",
    }
    assert {field.name for field in fields(ParserResponseClassificationRule)} >= {
        "rule_id",
        "summary",
        "required_transport_statuses",
        "required_parser_statuses",
        "required_reference_statuses",
        "required_provider_evidence_classes",
        "required_response_completeness_statuses",
        "required_response_restriction_signals",
        "requires_current_profile_proof",
        "requires_required_structure",
        "notes",
    }
    assert {field.name for field in fields(ParserCompatibilityProfile)} >= {
        "semantic_version",
        "lifecycle_status",
        "authority_class",
        "authority_scope",
        "reference_ids",
        "primary_reference_repository",
        "primary_reference_commit",
        "supported_extraction_claims",
        "unsupported_extraction_claims",
        "required_fields",
        "completeness_rules",
        "warning_mappings",
        "error_mappings",
        "fixture_ids",
        "acceptance_matrix_rows",
        "revalidation_triggers",
        "compatibility_change_classes",
    }

    try:
        profile.profile_version = "changed"  # type: ignore[misc]
    except FrozenInstanceError:
        pass
    else:  # pragma: no cover - defensive
        raise AssertionError("ParserCompatibilityProfile must be frozen")


def test_listing_contracts_are_frozen_and_authoritative_field_based() -> None:
    evidence = ParserEvidenceReference(
        reference_id="fx::listing::evidence",
        evidence_kind="listing-field",
    )
    profile = ParserCompatibilityProfile(
        profile_id="fx::listing::profile",
        semantic_version="2026.07.09",
        profile_version="2026.07.09",
        lifecycle_status=CompatibilityProfileLifecycleStatus.CURRENT,
        authority_class=CompatibilityProfileAuthorityClass.OBSERVATION_ONLY,
        authority_scope=("observation-only",),
        reference_ids=("AVITO-PRIMARY-PARSER-001",),
        primary_reference_repository="Duff89/parser_avito",
        primary_reference_commit="48441c352e36919abef13c436f41a3a62636da17",
        reference_status=ReferenceOutcomeStatus.CURRENT,
        evidence_reference=evidence,
        supported_extraction_claims=("tier-1 listing fields",),
        unsupported_extraction_claims=("raw provider payload",),
        required_fields=("profile_id", "semantic_version", "reference_ids"),
        completeness_rules=("current profile only",),
        warning_mappings=("REFERENCE_CHANGED->COMPATIBILITY_REVALIDATION_REQUIRED",),
        error_mappings=("REFERENCE_WITHDRAWN->WITHDRAWN_PROFILE_BLOCKED",),
        fixture_ids=("FX-APA08-TIER1-LISTING-CARD-PROVEN-001",),
        acceptance_matrix_rows=("APA08::CURRENT::TIER1::ACCEPT",),
        revalidation_triggers=(CompatibilityRevalidationTrigger.REFERENCE_CHANGED,),
        compatibility_change_classes=(CompatibilityChangeClass.COMPATIBLE,),
    )
    field = ListingFieldCandidate(
        field_candidate_id="fx::listing::field::title",
        field_family=ListingFieldFamily.TITLE,
        tier=ListingFieldTier.TIER_1_SEARCH_RESULT,
        availability=ListingFieldAvailability.PROVEN_AVAILABLE,
        quality=ListingFieldQuality.PROFILE_PROVEN,
        value="Synthetic title",
        compatibility_profile=profile,
        evidence_references=(evidence,),
    )
    card = ListingCardCandidate(
        listing_card_id="fx::listing::card::1",
        field_candidates=(field,),
        evidence_references=(evidence,),
    )
    candidate = NormalizedListingCandidate(
        listing_candidate_id="fx::listing::candidate::1",
        status=ListingCandidateStatus.USABLE,
        card_candidate=card,
        evidence_references=(evidence,),
    )

    assert field.field_family is ListingFieldFamily.TITLE
    assert field.tier is ListingFieldTier.TIER_1_SEARCH_RESULT
    assert field.availability is ListingFieldAvailability.PROVEN_AVAILABLE
    assert field.value == "Synthetic title"
    assert field.compatibility_profile is profile
    assert card.field_candidates == (field,)
    assert candidate.status is ListingCandidateStatus.USABLE
    assert candidate.card_candidate is card
    assert {field.name for field in fields(ListingFieldCandidate)} >= {
        "field_candidate_id",
        "field_family",
        "tier",
        "availability",
        "quality",
        "value",
        "compatibility_profile",
        "warnings",
        "evidence_references",
        "notes",
    }
    assert {field.name for field in fields(ListingCardCandidate)} >= {
        "listing_card_id",
        "field_candidates",
        "warnings",
        "evidence_references",
    }
    assert {field.name for field in fields(NormalizedListingCandidate)} >= {
        "listing_candidate_id",
        "status",
        "card_candidate",
        "warnings",
        "evidence_references",
    }
    for forbidden in {"baseline", "newness", "anchor", "history", "notification", "route_state"}:
        assert forbidden not in {field.name for field in fields(ListingCardCandidate)}
        assert forbidden not in {field.name for field in fields(NormalizedListingCandidate)}
    with pytest.raises(FrozenInstanceError):
        field.value = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        card.field_candidates = ()  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        candidate.status = ListingCandidateStatus.BLOCKED  # type: ignore[misc]


def test_listing_ordering_contracts_are_frozen_and_boundary_only() -> None:
    evidence = ParserEvidenceReference(
        reference_id="fx::ordering::evidence",
        evidence_kind="listing-ordering",
    )
    profile = ParserCompatibilityProfile(
        profile_id="fx::ordering::profile",
        semantic_version="2026.07.09",
        profile_version="2026.07.09",
        lifecycle_status=CompatibilityProfileLifecycleStatus.CURRENT,
        authority_class=CompatibilityProfileAuthorityClass.OBSERVATION_ONLY,
        authority_scope=("observation-only",),
        reference_ids=("AVITO-PRIMARY-PARSER-001",),
        primary_reference_repository="Duff89/parser_avito",
        primary_reference_commit="48441c352e36919abef13c436f41a3a62636da17",
        reference_status=ReferenceOutcomeStatus.CURRENT,
        evidence_reference=evidence,
        supported_extraction_claims=("listing order evidence only",),
        unsupported_extraction_claims=("baseline/newness/anchor ownership",),
        required_fields=("profile_id", "semantic_version", "reference_ids"),
        completeness_rules=("current profile only",),
        warning_mappings=("REFERENCE_CHANGED->COMPATIBILITY_REVALIDATION_REQUIRED",),
        error_mappings=("REFERENCE_WITHDRAWN->WITHDRAWN_PROFILE_BLOCKED",),
        fixture_ids=("FX-APA09-NEWEST-FIRST-PROVEN-001",),
        acceptance_matrix_rows=("APA09::CURRENT::TIER1::ACCEPT",),
        revalidation_triggers=(CompatibilityRevalidationTrigger.REFERENCE_CHANGED,),
        compatibility_change_classes=(CompatibilityChangeClass.COMPATIBLE,),
    )
    positions = (
        ObservedListingPosition(
            position_id="fx::ordering::position::1",
            listing_candidate_id="fx::ordering::candidate::1",
            observed_rank=1,
            evidence_references=(evidence,),
        ),
        ObservedListingPosition(
            position_id="fx::ordering::position::2",
            listing_candidate_id="fx::ordering::candidate::2",
            observed_rank=2,
            evidence_references=(evidence,),
        ),
    )
    ordering = ListingOrderingEvidence(
        ordering_evidence_id="fx::ordering::ordering",
        status=ListingSortContextStatus.PROVEN_NEWEST_FIRST,
        positions=positions,
        sort_context_reference="sort-context::ordering::proven",
        compatibility_profile=profile,
        warnings=(
            ParserWarning(
                code=ParserWarningCode.NEWEST_FIRST_SORT_PROVEN,
                message="newest-first sort is proven by synthetic evidence",
            ),
        ),
        evidence_references=(evidence,),
    )
    cards = (
        ListingCardCandidate(
            listing_card_id="fx::ordering::card::1", evidence_references=(evidence,)
        ),
        ListingCardCandidate(
            listing_card_id="fx::ordering::card::2", evidence_references=(evidence,)
        ),
    )
    candidates = (
        NormalizedListingCandidate(
            listing_candidate_id="fx::ordering::candidate::1",
            status=ListingCandidateStatus.USABLE,
            card_candidate=cards[0],
            evidence_references=(evidence,),
        ),
        NormalizedListingCandidate(
            listing_candidate_id="fx::ordering::candidate::2",
            status=ListingCandidateStatus.USABLE,
            card_candidate=cards[1],
            evidence_references=(evidence,),
        ),
    )
    handoff = ParserScanOrderingHandoff(
        handoff_id="fx::ordering::handoff",
        page_id="fx::ordering::page",
        page_status=ParserOutcomeStatus.USABLE_RESPONSE,
        status=ScanOrderingHandoffStatus.COMPARISON_ELIGIBLE,
        ordering_evidence=ordering,
        listing_candidate_ids=("fx::ordering::candidate::1", "fx::ordering::candidate::2"),
        evidence_references=(evidence,),
    )
    page = ListingPageParseOutcome(
        page_id="fx::ordering::page",
        request_envelope=ParserRequestEnvelope(
            request_id="fx::ordering::request",
            contract_name="mayak.avito.parser.request",
            contract_version="1.0",
            producer="mayak.tests.synthetic",
            purpose="listing-ordering",
            compatibility_profile=profile,
            safe_source_reference="bounded-source-value",
            configuration_revision_id="cfg::ordering::001",
            safe_transport_reference="transport::ordering",
        ),
        transport_outcome=TransportOutcomeReference(
            transport_reference_id="fx::ordering::transport",
            transport_status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
            request_reference="fx::ordering::request",
            response_reference="response::ordering",
            route_reference="route::ordering",
        ),
        status=ParserOutcomeStatus.USABLE_RESPONSE,
        compatibility_profile=profile,
        normalized_listing_candidates=candidates,
        card_candidates=cards,
        ordering_evidence=ordering,
        scan_ordering_handoff=handoff,
        evidence_references=(evidence,),
    )

    assert {field.name for field in fields(ObservedListingPosition)} >= {
        "position_id",
        "listing_candidate_id",
        "observed_rank",
        "publication_order_signal_reference",
        "warnings",
        "evidence_references",
        "notes",
    }
    assert {field.name for field in fields(ListingOrderingEvidence)} >= {
        "ordering_evidence_id",
        "status",
        "positions",
        "sort_context_reference",
        "compatibility_profile",
        "warnings",
        "evidence_references",
        "notes",
    }
    assert {field.name for field in fields(ParserScanOrderingHandoff)} >= {
        "handoff_id",
        "page_id",
        "page_status",
        "status",
        "ordering_evidence",
        "listing_candidate_ids",
        "warnings",
        "evidence_references",
        "notes",
    }
    assert {field.name for field in fields(ListingPageParseOutcome)} >= {
        "ordering_evidence",
        "scan_ordering_handoff",
    }
    for forbidden in {"baseline", "newness", "anchor", "notification", "is_new"}:
        assert forbidden not in {field.name for field in fields(ObservedListingPosition)}
        assert forbidden not in {field.name for field in fields(ListingOrderingEvidence)}
        assert forbidden not in {field.name for field in fields(ParserScanOrderingHandoff)}
        assert forbidden not in {field.name for field in fields(ListingPageParseOutcome)}

    assert page.ordering_evidence is ordering
    assert page.scan_ordering_handoff is handoff
    with pytest.raises(FrozenInstanceError):
        positions[0].observed_rank = 2  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        ordering.status = ListingSortContextStatus.MISSING  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        handoff.status = ScanOrderingHandoffStatus.BLOCKED_PAGE_NOT_USABLE  # type: ignore[misc]


def test_listing_field_candidate_rejects_invalid_semantics() -> None:
    evidence = ParserEvidenceReference(
        reference_id="fx::listing::invalid::evidence",
        evidence_kind="listing-field",
    )
    current_profile = ParserCompatibilityProfile(
        profile_id="fx::listing::current-profile",
        semantic_version="2026.07.09",
        profile_version="2026.07.09",
        lifecycle_status=CompatibilityProfileLifecycleStatus.CURRENT,
        authority_class=CompatibilityProfileAuthorityClass.OBSERVATION_ONLY,
        authority_scope=("observation-only",),
        reference_ids=("AVITO-PRIMARY-PARSER-001",),
        primary_reference_repository="Duff89/parser_avito",
        primary_reference_commit="48441c352e36919abef13c436f41a3a62636da17",
        reference_status=ReferenceOutcomeStatus.CURRENT,
        evidence_reference=evidence,
        supported_extraction_claims=("tier-1 listing fields",),
        unsupported_extraction_claims=("raw provider payload",),
        required_fields=("profile_id", "semantic_version", "reference_ids"),
        completeness_rules=("current profile only",),
        warning_mappings=("REFERENCE_CHANGED->COMPATIBILITY_REVALIDATION_REQUIRED",),
        error_mappings=("REFERENCE_WITHDRAWN->WITHDRAWN_PROFILE_BLOCKED",),
        fixture_ids=("FX-APA08-TIER1-LISTING-CARD-PROVEN-001",),
        acceptance_matrix_rows=("APA08::CURRENT::TIER1::ACCEPT",),
        revalidation_triggers=(CompatibilityRevalidationTrigger.REFERENCE_CHANGED,),
        compatibility_change_classes=(CompatibilityChangeClass.COMPATIBLE,),
    )
    stale_profile = ParserCompatibilityProfile(
        profile_id="fx::listing::stale-profile",
        semantic_version="2026.07.09",
        profile_version="2026.07.09",
        lifecycle_status=CompatibilityProfileLifecycleStatus.STALE,
        authority_class=CompatibilityProfileAuthorityClass.OBSERVATION_ONLY,
        authority_scope=("observation-only",),
        reference_ids=("AVITO-PRIMARY-PARSER-001",),
        primary_reference_repository="Duff89/parser_avito",
        primary_reference_commit="48441c352e36919abef13c436f41a3a62636da17",
        reference_status=ReferenceOutcomeStatus.REFERENCE_STALE,
        evidence_reference=evidence,
        supported_extraction_claims=("tier-1 listing fields",),
        unsupported_extraction_claims=("raw provider payload",),
        required_fields=("profile_id", "semantic_version", "reference_ids"),
        completeness_rules=("current profile only",),
        warning_mappings=("REFERENCE_CHANGED->COMPATIBILITY_REVALIDATION_REQUIRED",),
        error_mappings=("REFERENCE_WITHDRAWN->WITHDRAWN_PROFILE_BLOCKED",),
        fixture_ids=("FX-APA08-TIER1-LISTING-CARD-PROVEN-001",),
        acceptance_matrix_rows=("APA08::STALE::TIER1::BLOCK",),
        revalidation_triggers=(CompatibilityRevalidationTrigger.REFERENCE_CHANGED,),
        compatibility_change_classes=(CompatibilityChangeClass.BREAKING,),
    )
    disputed_profile = ParserCompatibilityProfile(
        profile_id="fx::listing::disputed-profile",
        semantic_version="2026.07.09",
        profile_version="2026.07.09",
        lifecycle_status=CompatibilityProfileLifecycleStatus.DISPUTED,
        authority_class=CompatibilityProfileAuthorityClass.OBSERVATION_ONLY,
        authority_scope=("observation-only",),
        reference_ids=("AVITO-PRIMARY-PARSER-001",),
        primary_reference_repository="Duff89/parser_avito",
        primary_reference_commit="48441c352e36919abef13c436f41a3a62636da17",
        reference_status=ReferenceOutcomeStatus.REFERENCE_DISPUTED,
        evidence_reference=evidence,
        supported_extraction_claims=("tier-1 listing fields",),
        unsupported_extraction_claims=("raw provider payload",),
        required_fields=("profile_id", "semantic_version", "reference_ids"),
        completeness_rules=("current profile only",),
        warning_mappings=("REFERENCE_CHANGED->COMPATIBILITY_REVALIDATION_REQUIRED",),
        error_mappings=("REFERENCE_WITHDRAWN->WITHDRAWN_PROFILE_BLOCKED",),
        fixture_ids=("FX-APA08-TIER1-LISTING-CARD-PROVEN-001",),
        acceptance_matrix_rows=("APA08::DISPUTED::TIER1::BLOCK",),
        revalidation_triggers=(CompatibilityRevalidationTrigger.REFERENCE_CHANGED,),
        compatibility_change_classes=(CompatibilityChangeClass.DISPUTED,),
    )

    with pytest.raises(ValueError):
        ListingFieldCandidate(
            field_candidate_id="fx::listing::field::wrong-tier",
            field_family=ListingFieldFamily.TITLE,
            tier=ListingFieldTier.TIER_2_LISTING_DETAIL,
            availability=ListingFieldAvailability.PROVEN_AVAILABLE,
            quality=ListingFieldQuality.PROFILE_PROVEN,
            value="Synthetic title",
            compatibility_profile=current_profile,
            evidence_references=(evidence,),
        )
    with pytest.raises(ValueError):
        ListingFieldCandidate(
            field_candidate_id="fx::listing::field::value-on-unavailable",
            field_family=ListingFieldFamily.SELLER,
            tier=ListingFieldTier.TIER_2_LISTING_DETAIL,
            availability=ListingFieldAvailability.PROVEN_UNAVAILABLE,
            quality=ListingFieldQuality.UNVERIFIED,
            value="Synthetic seller",
            compatibility_profile=current_profile,
            evidence_references=(evidence,),
        )
    with pytest.raises(ValueError):
        ListingFieldCandidate(
            field_candidate_id="fx::listing::field::missing-evidence",
            field_family=ListingFieldFamily.SELLER,
            tier=ListingFieldTier.TIER_2_LISTING_DETAIL,
            availability=ListingFieldAvailability.PROVEN_AVAILABLE,
            quality=ListingFieldQuality.PROFILE_PROVEN,
            value="Synthetic seller",
            compatibility_profile=current_profile,
        )
    with pytest.raises(ValueError):
        ListingFieldCandidate(
            field_candidate_id="fx::listing::field::missing-profile",
            field_family=ListingFieldFamily.SELLER,
            tier=ListingFieldTier.TIER_2_LISTING_DETAIL,
            availability=ListingFieldAvailability.PROVEN_AVAILABLE,
            quality=ListingFieldQuality.PROFILE_PROVEN,
            value="Synthetic seller",
            evidence_references=(evidence,),
        )
    for invalid_profile in (stale_profile, disputed_profile):
        with pytest.raises(ValueError):
            ListingFieldCandidate(
                field_candidate_id="fx::listing::field::invalid-profile",
                field_family=ListingFieldFamily.SELLER,
                tier=ListingFieldTier.TIER_2_LISTING_DETAIL,
                availability=ListingFieldAvailability.PROVEN_AVAILABLE,
                quality=ListingFieldQuality.PROFILE_PROVEN,
                value="Synthetic seller",
                compatibility_profile=invalid_profile,
                evidence_references=(evidence,),
            )
    with pytest.raises(ValueError):
        ListingFieldCandidate(
            field_candidate_id="fx::listing::field::blank-value",
            field_family=ListingFieldFamily.PHONE_VALUE,
            tier=ListingFieldTier.TIER_3_CONTACT,
            availability=ListingFieldAvailability.PROOF_GATED,
            quality=ListingFieldQuality.UNVERIFIED,
            value=" ",
            compatibility_profile=current_profile,
            evidence_references=(evidence,),
        )


def test_search_configuration_contracts_are_evidence_bound_and_frozen() -> None:
    evidence_reference = ParserEvidenceReference(
        reference_id="fx::search-config::evidence",
        evidence_kind="search-configuration",
    )
    warning = ParserWarning(
        code=SearchConfigurationWarningCode.MULTIVALUE_PARAMETER_PRESERVED,
        message="repeated parameter values are preserved",
        evidence_reference=evidence_reference,
    )
    profile = ParserCompatibilityProfile(
        profile_id="fx::search-config::profile",
        semantic_version="2026.07.09",
        profile_version="2026.07.09",
        lifecycle_status=CompatibilityProfileLifecycleStatus.CURRENT,
        authority_class=CompatibilityProfileAuthorityClass.OBSERVATION_ONLY,
        authority_scope=("observation-only", "synthetic"),
        reference_ids=("AVITO-PRIMARY-PARSER-001",),
        primary_reference_repository="Duff89/parser_avito",
        primary_reference_commit="48441c352e36919abef13c436f41a3a62636da17",
        supported_extraction_claims=("search configuration candidates are evidence-bound",),
        unsupported_extraction_claims=("filter editability authority",),
        required_fields=("profile_id", "semantic_version", "reference_ids"),
        completeness_rules=("compatibility profile and source boundary gate confidence",),
        warning_mappings=("MULTIVALUE_PARAMETER_PRESERVED->PRESERVED",),
        error_mappings=("LOSSY_NORMALIZATION_BLOCKED->BLOCKED",),
        fixture_ids=("FX-APA06-REPEATED-MULTIVALUE-PARAM-PRESERVED-001",),
        acceptance_matrix_rows=("APA06::MULTIVALUE::PRESERVED",),
    )
    source_reference = ParserSourceReference(
        source_reference_id="fx::search-config::source-reference",
        source_reference_kind=SourceReferenceKind.SAFE_REFERENCE,
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
    )
    boundary = SourceBoundaryOutcome(
        boundary_id="fx::search-config::boundary",
        source_reference=source_reference,
        status=SourceBoundaryStatus.SOURCE_URL_UNTRUSTED,
        policy_requirements=(
            SourceBoundaryPolicyRequirement.HOST_POLICY_REQUIRED,
            SourceBoundaryPolicyRequirement.PATH_POLICY_REQUIRED,
            SourceBoundaryPolicyRequirement.QUERY_POLICY_REQUIRED,
        ),
        risk_codes=(SourceBoundaryRiskCode.SOURCE_URL_UNTRUSTED,),
        warnings=(warning,),
    )
    request = ParserRequestEnvelope(
        request_id="fx::search-config::request",
        contract_name="mayak.avito.parser.request",
        contract_version="1.0",
        producer="mayak.tests.synthetic",
        purpose="search-configuration-extraction",
        compatibility_profile=profile,
        safe_source_reference=source_reference.bounded_value,
        source_reference=source_reference,
        source_boundary_outcome=boundary,
        configuration_revision_id="cfg::search-config::001",
        safe_transport_reference="transport::search-config",
    )
    transport = TransportOutcomeReference(
        transport_reference_id="fx::search-config::transport",
        transport_status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
        request_reference=request.request_id,
        response_reference="response::search-config",
        route_reference="route::synthetic",
    )
    evidence = SearchConfigurationEvidence(
        evidence_id="fx::search-config::evidence-bundle",
        request_envelope=request,
        compatibility_profile=profile,
        source_reference=source_reference,
        source_boundary_outcome=boundary,
        transport_outcome=transport,
        evidence_references=(evidence_reference,),
        notes=("search configuration extraction stays evidence-bound",),
    )
    parameter = SearchConfigurationParameterCandidate(
        parameter_key="filter-key:synthetic-color",
        parameter_value=None,
        field_status=SearchConfigurationFieldStatus.PRESERVED,
        value_kind=SearchConfigurationValueKind.COLLECTION,
        repeated_values=("value:synthetic-red", "value:synthetic-blue"),
        multivalue_normalization=MultivalueNormalizationOutcome(
            normalization_id="fx::search-config::normalization",
            parameter_key="filter-key:synthetic-color",
            input_values=("value:synthetic-red", "value:synthetic-blue"),
            normalization_rule=MultivalueNormalizationRule(
                rule_id="fx::search-config::rule",
                status=MultivalueNormalizationStatus.PRESERVED,
                preservation_mode=MultivaluePreservationMode.ORDERED_COLLECTION,
            ),
            status=MultivalueNormalizationStatus.PRESERVED,
            preservation_mode=MultivaluePreservationMode.ORDERED_COLLECTION,
            normalized_values=("value:synthetic-red", "value:synthetic-blue"),
            compatibility_profile=profile,
            source_boundary_outcome=boundary,
            warnings=(warning,),
            evidence_references=(evidence_reference,),
            notes=("repeated values are preserved",),
        ),
        evidence_references=(evidence_reference,),
        warnings=(warning,),
        notes=("repeated values are preserved",),
    )
    candidate = SearchConfigurationCandidate(
        candidate_id="fx::search-config::candidate",
        extraction_field=SearchConfigurationExtractionField.REPEATED_PARAMETER,
        field_status=SearchConfigurationFieldStatus.PRESERVED,
        value_kind=SearchConfigurationValueKind.COLLECTION,
        parameter_candidates=(parameter,),
        evidence_references=(evidence_reference,),
        warnings=(warning,),
        notes=("repeated values are preserved",),
    )
    outcome = SearchConfigurationExtractionOutcome(
        extraction_id="fx::search-config::outcome",
        request_envelope=request,
        transport_outcome=transport,
        status=ParserOutcomeStatus.USABLE_RESPONSE,
        compatibility_profile=profile,
        search_configuration_evidence=evidence,
        search_configuration_candidates=(candidate,),
        parameter_candidates=(parameter,),
        normalized_geography_candidates=("synthetic-city",),
        normalized_category_candidates=("synthetic-category",),
        normalized_filter_candidates=("filter-key:synthetic-color=value:synthetic-red",),
        observed_sort_context_reference="sort-context::synthetic-newest",
        warnings=(warning,),
        evidence_references=(evidence_reference,),
        explanation=ParserOutcomeExplanation(
            summary="search configuration extraction stays evidence-bound",
            reason_code="FX::search-config",
            status=ParserOutcomeStatus.USABLE_RESPONSE,
            evidence_references=(evidence_reference,),
            warnings=(warning,),
        ),
    )

    assert warning.code is SearchConfigurationWarningCode.MULTIVALUE_PARAMETER_PRESERVED
    assert evidence.source_reference is source_reference
    assert evidence.source_boundary_outcome is boundary
    assert evidence.compatibility_profile is profile
    assert parameter.repeated_values == ("value:synthetic-red", "value:synthetic-blue")
    assert parameter.multivalue_normalization is not None
    assert parameter.multivalue_normalization.normalized_values == (
        "value:synthetic-red",
        "value:synthetic-blue",
    )
    assert (
        parameter.multivalue_normalization.normalization_rule.status
        is MultivalueNormalizationStatus.PRESERVED
    )
    assert candidate.parameter_candidates == (parameter,)
    assert candidate.field_status is SearchConfigurationFieldStatus.PRESERVED
    assert outcome.search_configuration_evidence is evidence
    assert outcome.search_configuration_candidates == (candidate,)
    assert outcome.parameter_candidates == (parameter,)
    assert outcome.request_envelope.safe_source_reference == source_reference.bounded_value
    assert outcome.request_envelope.source_boundary_outcome is boundary
    assert {field.name for field in fields(SearchConfigurationEvidence)} >= {
        "evidence_id",
        "request_envelope",
        "compatibility_profile",
        "source_reference",
        "source_boundary_outcome",
        "transport_outcome",
        "evidence_references",
        "notes",
    }
    assert {field.name for field in fields(SearchConfigurationParameterCandidate)} >= {
        "parameter_key",
        "parameter_value",
        "field_status",
        "value_kind",
        "repeated_values",
        "multivalue_normalization",
        "evidence_references",
        "warnings",
        "notes",
    }
    assert {field.name for field in fields(MultivalueNormalizationRule)} >= {
        "rule_id",
        "status",
        "preservation_mode",
        "loss_reason",
        "notes",
    }
    assert {field.name for field in fields(MultivalueNormalizationOutcome)} >= {
        "normalization_id",
        "parameter_key",
        "input_values",
        "normalization_rule",
        "status",
        "preservation_mode",
        "normalized_values",
        "loss_reason",
        "compatibility_profile",
        "source_boundary_outcome",
        "transport_response_classification",
        "warnings",
        "evidence_references",
        "notes",
    }
    assert {field.name for field in fields(SearchConfigurationCandidate)} >= {
        "candidate_id",
        "extraction_field",
        "field_status",
        "value_kind",
        "parameter_candidates",
        "evidence_references",
        "warnings",
        "notes",
    }
    assert {field.name for field in fields(SearchConfigurationExtractionOutcome)} >= {
        "search_configuration_evidence",
        "search_configuration_candidates",
        "parameter_candidates",
        "normalized_geography_candidates",
        "normalized_category_candidates",
        "normalized_filter_candidates",
        "observed_sort_context_reference",
    }
    assert {member.value for member in SearchConfigurationWarningCode} >= {
        "MULTIVALUE_PARAMETER_PRESERVED",
        "UNSUPPORTED_PARAMETER_EXPLICIT",
        "AMBIGUOUS_PARAMETER_EXPLICIT",
        "LOSSY_NORMALIZATION_BLOCKED",
    }
    assert [member.value for member in MultivalueNormalizationStatus] == [
        "PRESERVED",
        "BLOCKED",
        "UNSUPPORTED",
        "AMBIGUOUS",
        "LOSSY",
    ]
    assert [member.value for member in MultivaluePreservationMode] == [
        "ORDERED_TUPLE",
        "ORDERED_COLLECTION",
        "SCALAR_BLOCKED",
    ]
    assert [member.value for member in MultivalueLossReason] == [
        "FIRST_VALUE_OVERWRITE_BLOCKED",
        "LATER_VALUE_LOSS_BLOCKED",
        "DUPLICATE_REMOVAL_BLOCKED",
        "COLLECTION_TO_SCALAR_COLLAPSE_BLOCKED",
        "UNSUPPORTED_MULTIVALUE_PARAMETER",
        "AMBIGUOUS_MULTIVALUE_PARAMETER",
        "LOSSY_NORMALIZATION_BLOCKED",
        "PROFILE_STALE",
        "PROFILE_MISSING",
        "PROFILE_DISPUTED",
        "SOURCE_BOUNDARY_INVALID",
        "RESPONSE_CLASSIFICATION_NOT_TRUSTED",
    ]
    assert [member.value for member in SearchConfigurationExtractionField] == [
        "GEOGRAPHY_CONTEXT",
        "CATEGORY_CONTEXT",
        "PRICE_LOWER_BOUND",
        "PRICE_UPPER_BOUND",
        "STRUCTURED_FILTER",
        "REPEATED_PARAMETER",
        "SORT_CONTEXT",
        "PAGINATION_CONTEXT",
        "UNSUPPORTED_PARAMETER",
        "AMBIGUOUS_PARAMETER",
        "COUNTRY_WIDE_CONTEXT",
        "FILTER_EDITABILITY_CONTEXT",
        "BEACON_SNAPSHOT_CONTEXT",
    ]
    assert [member.value for member in SearchConfigurationFieldStatus] == [
        "EVIDENCE_BOUND",
        "PRESERVED",
        "UNPROVEN",
        "UNSUPPORTED",
        "AMBIGUOUS",
        "POLICY_GATED",
        "LOSSY_NORMALIZATION_BLOCKED",
    ]
    assert [member.value for member in SearchConfigurationValueKind] == [
        "SCALAR",
        "RANGE_BOUND",
        "KEY_VALUE_PAIR",
        "COLLECTION",
        "CONTEXT",
        "PROVENANCE",
        "UNSUPPORTED",
        "AMBIGUOUS",
    ]

    try:
        parameter.parameter_key = "changed"  # type: ignore[misc]
    except FrozenInstanceError:
        pass
    else:  # pragma: no cover - defensive
        raise AssertionError("SearchConfigurationParameterCandidate must be frozen")


def test_source_boundary_contracts_keep_bounded_references_explicit() -> None:
    evidence = ParserEvidenceReference(
        reference_id="fx::boundary::evidence",
        evidence_kind="source-boundary",
    )
    source_reference = ParserSourceReference(
        source_reference_id="fx::boundary::source-reference",
        source_reference_kind=SourceReferenceKind.BEACON_OWNED_SUBMISSION,
        beacon_source_reference="source-ref:beacon-revision-999",
        bounded_value="bounded-source-value",
        host_reference="provider.example",
        path_reference="/search",
        query_reference="q=bounded",
        policy_requirements=(
            SourceBoundaryPolicyRequirement.HOST_POLICY_REQUIRED,
            SourceBoundaryPolicyRequirement.PATH_POLICY_REQUIRED,
            SourceBoundaryPolicyRequirement.QUERY_POLICY_REQUIRED,
        ),
        risk_codes=(SourceBoundaryRiskCode.SOURCE_URL_UNTRUSTED,),
    )
    warning = ParserWarning(
        code=ParserWarningCode.SOURCE_URL_UNTRUSTED,
        message="bounded source reference is explicitly untrusted",
        evidence_reference=evidence,
    )
    boundary = SourceBoundaryOutcome(
        boundary_id="fx::boundary::outcome",
        source_reference=source_reference,
        status=SourceBoundaryStatus.SOURCE_URL_UNTRUSTED,
        policy_requirements=(
            SourceBoundaryPolicyRequirement.HOST_POLICY_REQUIRED,
            SourceBoundaryPolicyRequirement.PATH_POLICY_REQUIRED,
            SourceBoundaryPolicyRequirement.QUERY_POLICY_REQUIRED,
        ),
        risk_codes=(SourceBoundaryRiskCode.SOURCE_URL_UNTRUSTED,),
        warnings=(warning,),
    )
    request = ParserRequestEnvelope(
        request_id="fx::boundary::request",
        contract_name="mayak.avito.parser.request",
        contract_version="1.0",
        producer="mayak.tests.synthetic",
        purpose="source-boundary-analysis",
        compatibility_profile=ParserCompatibilityProfile(
            profile_id="fx::boundary::profile",
            semantic_version="2026.07.09",
            profile_version="2026.07.09",
            reference_ids=("AVITO-PRIMARY-PARSER-001",),
            primary_reference_repository="Duff89/parser_avito",
            primary_reference_commit="48441c352e36919abef13c436f41a3a62636da17",
        ),
        safe_source_reference="bounded-source-value",
        source_reference=source_reference,
        source_boundary_outcome=boundary,
        configuration_revision_id="cfg::boundary::001",
        safe_transport_reference="transport::boundary",
    )

    assert request.source_reference is source_reference
    assert request.source_boundary_outcome is boundary
    assert request.source_boundary_outcome.source_reference is source_reference
    assert request.safe_source_reference == source_reference.bounded_value
    assert boundary.status is SourceBoundaryStatus.SOURCE_URL_UNTRUSTED
    assert boundary.policy_requirements == (
        SourceBoundaryPolicyRequirement.HOST_POLICY_REQUIRED,
        SourceBoundaryPolicyRequirement.PATH_POLICY_REQUIRED,
        SourceBoundaryPolicyRequirement.QUERY_POLICY_REQUIRED,
    )
    assert boundary.risk_codes == (SourceBoundaryRiskCode.SOURCE_URL_UNTRUSTED,)
    assert warning.code is ParserWarningCode.SOURCE_URL_UNTRUSTED
    assert {field.name for field in fields(ParserRequestEnvelope)} >= {
        "safe_source_reference",
        "source_reference",
        "source_boundary_outcome",
        "configuration_revision_id",
        "safe_transport_reference",
    }
    assert {field.name for field in fields(ParserSourceReference)} >= {
        "source_reference_id",
        "source_reference_kind",
        "beacon_source_reference",
        "bounded_value",
        "policy_requirements",
        "risk_codes",
    }
    assert {field.name for field in fields(SourceBoundaryOutcome)} >= {
        "boundary_id",
        "source_reference",
        "status",
        "policy_requirements",
        "risk_codes",
        "warnings",
    }
    assert {member.value for member in ParserWarningCode} >= {
        "SOURCE_URL_UNTRUSTED",
        "SOURCE_URL_POLICY_MISSING",
        "SOURCE_URL_MALFORMED",
        "SOURCE_URL_UNSUPPORTED",
        "OBSERVED_LISTING_ORDER_PRESERVED",
        "NEWEST_FIRST_SORT_PROVEN",
        "SORT_CONTEXT_MISSING",
        "SORT_CONTEXT_AMBIGUOUS",
        "SORT_CONTEXT_UNSUPPORTED",
        "SORT_CONTEXT_UNPROVEN",
        "SORT_CONTEXT_CONTRADICTORY",
        "PUBLICATION_ORDER_SIGNAL_UNAVAILABLE",
        "SCAN_NEWNESS_DECISION_NOT_PERFORMED",
        "SCAN_ANCHOR_STATE_NOT_MUTATED",
    }


def test_synthetic_fixture_cases_are_safe_and_non_empty() -> None:
    assert len(SYNTHETIC_FIXTURE_BY_ID) == len(
        {fixture.fixture_id for fixture in SYNTHETIC_FIXTURE_BY_ID.values()}
    )
    avito_live_url_marker = "".join(("a", "v", "i", "t", "o", ".", "r", "u"))
    for fixture in SYNTHETIC_FIXTURE_BY_ID.values():
        assert fixture.fixture_id.startswith(
            (
                "FX-APA02-",
                "FX-APA03-",
                "FX-APA04-",
                "FX-APA05-",
                "FX-APA06-",
                "FX-APA07-",
                "FX-APA08-",
                "FX-APA09-",
            )
        )
        assert avito_live_url_marker not in fixture.summary.lower()
