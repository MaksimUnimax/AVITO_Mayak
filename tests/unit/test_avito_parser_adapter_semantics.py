from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from mayak.modules.avito_parser_adapter import (
    FIXTURE_IDS,
    SYNTHETIC_FIXTURE_BY_ID,
    CompatibilityChangeClass,
    CompatibilityProfileAuthorityClass,
    CompatibilityProfileLifecycleStatus,
    CompatibilityRevalidationTrigger,
    ListingCandidateStatus,
    ListingCardCandidate,
    ListingFieldAvailability,
    ListingFieldFamily,
    ListingOrderingEvidence,
    ListingPageParseOutcome,
    ListingSortContextStatus,
    MultivalueLossReason,
    MultivalueNormalizationStatus,
    NormalizedListingCandidate,
    ObservedListingPosition,
    ParserCompatibilityProfile,
    ParserEvidenceReference,
    ParserOutcomeStatus,
    ParserRequestEnvelope,
    ParserScanOrderingHandoff,
    ParserWarningCode,
    ProviderResponseEvidenceClass,
    ReferenceOutcomeStatus,
    ResponseCompletenessStatus,
    ResponseRestrictionSignal,
    ScanOrderingHandoffStatus,
    SearchConfigurationExtractionField,
    SearchConfigurationFieldStatus,
    SearchConfigurationValueKind,
    SearchConfigurationWarningCode,
    SourceBoundaryPolicyRequirement,
    SourceBoundaryRiskCode,
    SourceBoundaryStatus,
    SourceReferenceKind,
    TransportOutcomeReference,
    TransportOutcomeStatus,
)


def test_parser_adapter_status_enums_are_stable() -> None:
    assert [member.value for member in TransportOutcomeStatus] == [
        "NOT_SENT",
        "TRANSPORT_UNAVAILABLE",
        "TRANSPORT_AMBIGUOUS",
        "RESPONSE_RECEIVED_UNCLASSIFIED",
    ]
    assert [member.value for member in ParserOutcomeStatus] == [
        "USABLE_RESPONSE",
        "EXPLICIT_REJECTION",
        "RATE_OR_ACCESS_RESTRICTED",
        "CAPTCHA_OR_CHALLENGE",
        "MALFORMED_RESPONSE",
        "INCOMPLETE_RESPONSE",
        "UNSUPPORTED_STRUCTURE",
        "PARTIAL",
        "RESULT_AMBIGUOUS",
    ]
    assert [member.value for member in ProviderResponseEvidenceClass] == [
        "UNCLASSIFIED",
        "BODY_PRESENT_UNCLASSIFIED",
        "USABLE_RESPONSE",
        "EXPLICIT_REJECTION",
        "RATE_OR_ACCESS_RESTRICTED",
        "CAPTCHA_OR_CHALLENGE",
        "MALFORMED_RESPONSE",
        "INCOMPLETE_RESPONSE",
        "UNSUPPORTED_STRUCTURE",
        "PARTIAL",
        "RESULT_AMBIGUOUS",
        "EMPTY_WITH_PROOF",
        "EMPTY_WITHOUT_PROOF",
    ]
    assert [member.value for member in ResponseCompletenessStatus] == [
        "UNVERIFIED",
        "COMPLETE",
        "PARTIAL",
        "INCOMPLETE",
        "EMPTY_PROVEN",
        "EMPTY_BLOCKED",
        "AMBIGUOUS",
    ]
    assert [member.value for member in ResponseRestrictionSignal] == [
        "NONE",
        "RATE_LIMIT",
        "ACCESS_RESTRICTED",
        "CAPTCHA",
        "CHALLENGE",
    ]
    assert [member.value for member in ReferenceOutcomeStatus] == [
        "REFERENCE_STALE",
        "REFERENCE_MISSING",
        "REFERENCE_DISPUTED",
        "CURRENT",
    ]
    assert [member.value for member in ListingSortContextStatus] == [
        "PROVEN_NEWEST_FIRST",
        "MISSING",
        "AMBIGUOUS",
        "UNSUPPORTED",
        "UNPROVEN",
        "CONTRADICTORY",
    ]
    assert [member.value for member in ScanOrderingHandoffStatus] == [
        "COMPARISON_ELIGIBLE",
        "BLOCKED_PAGE_NOT_USABLE",
        "BLOCKED_SORT_MISSING",
        "BLOCKED_SORT_AMBIGUOUS",
        "BLOCKED_SORT_UNSUPPORTED",
        "BLOCKED_SORT_UNPROVEN",
        "BLOCKED_SORT_CONTRADICTORY",
        "BLOCKED_PROFILE_NOT_CURRENT",
        "BLOCKED_ORDER_MISMATCH",
    ]


def test_apa03_compatibility_enums_are_stable() -> None:
    assert [member.value for member in CompatibilityProfileLifecycleStatus] == [
        "CURRENT",
        "STALE",
        "SUPERSEDED",
        "WITHDRAWN",
        "UNAVAILABLE",
        "DISPUTED",
    ]
    assert [member.value for member in CompatibilityProfileAuthorityClass] == [
        "OBSERVATION_ONLY",
        "OWNER_CAPTURED",
        "SYNTHETIC",
        "PROOF_GATED",
        "OFFICIAL_PRIMARY_ONLY",
    ]
    assert [member.value for member in CompatibilityChangeClass] == [
        "COMPATIBLE",
        "WARNING",
        "BREAKING",
        "UNKNOWN",
        "DISPUTED",
        "UNAVAILABLE",
    ]
    assert [member.value for member in CompatibilityRevalidationTrigger] == [
        "REFERENCE_CHANGED",
        "EXTRACTION_CLAIM_CHANGED",
        "PARSER_WARNING_MAPPING_CHANGED",
        "FIXTURE_MATRIX_CHANGED",
        "PROVIDER_STRUCTURE_UNPROVEN_OR_STALE",
        "OWNER_DECISION_CHANGED",
    ]


def test_apa09_warning_codes_are_explicit_and_stable() -> None:
    assert {member.value for member in ParserWarningCode} >= {
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


def test_fixture_ids_are_unique_and_cover_required_semantics() -> None:
    assert FIXTURE_IDS == tuple(fixture.fixture_id for fixture in SYNTHETIC_FIXTURE_BY_ID.values())
    assert len(FIXTURE_IDS) == len(set(FIXTURE_IDS))

    expected_ids = {
        "FX-APA02-USABLE-SEARCH-TIER1-001",
        "FX-APA02-CLEAN-EMPTY-COMPATIBILITY-PROOF-001",
        "FX-APA02-FALSE-EMPTY-RESTRICTED-001",
        "FX-APA02-FALSE-EMPTY-MALFORMED-001",
        "FX-APA02-FALSE-EMPTY-AMBIGUOUS-001",
        "FX-APA02-OPTIONAL-PHONE-UNAVAILABLE-001",
        "FX-APA02-SELLER-RATING-DESCRIPTION-UNAVAILABLE-001",
        "FX-APA02-REPEATED-MULTIVALUE-FILTER-PRESERVATION-001",
        "FX-APA02-AMBIGUOUS-SORT-NEWEST-EVIDENCE-001",
        "FX-APA02-PARTIAL-PAGE-BATCH-001",
        "FX-APA02-STALE-COMPATIBILITY-PROFILE-001",
        "FX-APA03-CURRENT-REFERENCE-PROFILE-001",
        "FX-APA03-STALE-REFERENCE-PROFILE-BLOCKS-CLEAN-EMPTY-001",
        "FX-APA03-DISPUTED-REFERENCE-PROFILE-WARNING-001",
        "FX-APA03-SUPERSEDED-REFERENCE-PROFILE-001",
        "FX-APA03-WITHDRAWN-REFERENCE-PROFILE-BLOCKS-SUCCESS-001",
        "FX-APA03-UNAVAILABLE-REFERENCE-PROFILE-001",
        "FX-APA03-UNSUPPORTED-EXTRACTION-CLAIM-001",
        "FX-APA03-REFERENCE-COMMIT-REVALIDATION-001",
        "FX-APA03-INTERNAL-ENDPOINT-OBSERVATION-NOT-STABLE-001",
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
        "FX-APA05-NOT-SENT-001",
        "FX-APA05-TRANSPORT-UNAVAILABLE-001",
        "FX-APA05-TRANSPORT-AMBIGUOUS-001",
        "FX-APA05-SENT-SUCCESS-RESPONSE-UNCLASSIFIED-001",
        "FX-APA05-USABLE-RESPONSE-CURRENT-PROFILE-PROOF-001",
        "FX-APA05-EXPLICIT-PROVIDER-REJECTION-001",
        "FX-APA05-RATE-ACCESS-RESTRICTED-001",
        "FX-APA05-CAPTCHA-CHALLENGE-001",
        "FX-APA05-MALFORMED-RESPONSE-001",
        "FX-APA05-INCOMPLETE-RESPONSE-001",
        "FX-APA05-UNSUPPORTED-STRUCTURE-001",
        "FX-APA05-STALE-REFERENCE-PROFILE-001",
        "FX-APA05-MISSING-REFERENCE-PROFILE-001",
        "FX-APA05-DISPUTED-REFERENCE-PROFILE-001",
        "FX-APA05-PARTIAL-RESPONSE-PAGE-001",
        "FX-APA05-AMBIGUOUS-RESULT-001",
        "FX-APA05-CLEAN-EMPTY-BLOCKED-WITHOUT-PROOF-001",
        "FX-APA05-HTTP-200-NON-EMPTY-NOT-ENOUGH-001",
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
        "FX-APA07-REPEATED-VALUES-ORDER-PRESERVED-001",
        "FX-APA07-DUPLICATES-PRESERVED-001",
        "FX-APA07-FIRST-VALUE-OVERWRITE-BLOCKED-001",
        "FX-APA07-LATER-VALUE-LOSS-BLOCKED-001",
        "FX-APA07-COLLECTION-TO-SCALAR-BLOCKED-001",
        "FX-APA07-UNSUPPORTED-MULTIVALUE-EXPLICIT-001",
        "FX-APA07-AMBIGUOUS-MULTIVALUE-EXPLICIT-001",
        "FX-APA07-LOSSY-NORMALIZATION-EXPLICIT-001",
        "FX-APA07-PROFILE-BOUND-COLLECTION-PRESERVED-001",
        "FX-APA07-PROFILE-NOT-CURRENT-BLOCKS-001",
        "FX-APA07-PROFILE-MISSING-BLOCKS-001",
        "FX-APA07-PROFILE-DISPUTED-BLOCKS-001",
        "FX-APA07-SOURCE-BOUNDARY-BLOCKS-001",
        "FX-APA07-RESPONSE-CLASSIFICATION-BLOCKS-001",
        "FX-APA07-FILTER-EDITABILITY-NOT-DECLARED-001",
        "FX-APA07-BEACON-NO-MUTATION-001",
        "FX-APA07-SCAN-NO-MUTATION-001",
        "FX-APA08-TIER1-LISTING-CARD-PROVEN-001",
        "FX-APA08-OPTIONAL-DETAIL-FIELDS-UNAVAILABLE-001",
        "FX-APA08-PHONE-VALUE-PROOF-GATED-001",
        "FX-APA08-OPTIONAL-FIELD-AMBIGUOUS-WARNING-001",
        "FX-APA08-FIELD-PROVENANCE-REQUIRED-001",
        "FX-APA08-NO-SCAN-NEWNESS-MUTATION-001",
        "FX-APA08-NO-RAW-PROVIDER-PAYLOAD-001",
        "FX-APA09-NEWEST-FIRST-PROVEN-001",
        "FX-APA09-OBSERVED-ORDER-PRESERVED-001",
        "FX-APA09-SORT-CONTEXT-MISSING-BLOCKS-001",
        "FX-APA09-SORT-CONTEXT-AMBIGUOUS-BLOCKS-001",
        "FX-APA09-SORT-CONTEXT-UNSUPPORTED-BLOCKS-001",
        "FX-APA09-SORT-CONTEXT-UNPROVEN-BLOCKS-001",
        "FX-APA09-SORT-CONTEXT-CONTRADICTORY-BLOCKS-001",
        "FX-APA09-PUBLICATION-SIGNAL-OPTIONAL-001",
        "FX-APA09-PARTIAL-PAGE-NOT-COMPARISON-ELIGIBLE-001",
        "FX-APA09-NO-SCAN-NEWNESS-DECISION-001",
        "FX-APA09-NO-ANCHOR-STATE-MUTATION-001",
    }
    assert expected_ids.issubset(SYNTHETIC_FIXTURE_BY_ID)


def test_optional_listing_fields_do_not_fail_parser_semantics() -> None:
    phone_fixture = SYNTHETIC_FIXTURE_BY_ID["FX-APA02-OPTIONAL-PHONE-UNAVAILABLE-001"]
    detail_fixture = SYNTHETIC_FIXTURE_BY_ID["FX-APA02-SELLER-RATING-DESCRIPTION-UNAVAILABLE-001"]

    assert (
        phone_fixture.attempt_outcome.transport_status
        is TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED
    )
    assert phone_fixture.attempt_outcome.parser_status is ParserOutcomeStatus.USABLE_RESPONSE
    assert phone_fixture.listing_page_parse_outcome is not None
    assert phone_fixture.listing_page_parse_outcome.status is ParserOutcomeStatus.USABLE_RESPONSE
    assert (
        phone_fixture.listing_page_parse_outcome.normalized_listing_candidates[0].status
        is ListingCandidateStatus.USABLE
    )
    phone_fields = {
        field.field_family: field
        for field in phone_fixture.listing_page_parse_outcome.card_candidates[0].field_candidates
    }
    assert (
        phone_fields[ListingFieldFamily.PHONE_AVAILABILITY].availability
        is ListingFieldAvailability.PROOF_GATED
    )
    assert (
        phone_fields[ListingFieldFamily.PHONE_VALUE].availability
        is ListingFieldAvailability.PROOF_GATED
    )
    assert phone_fields[ListingFieldFamily.PHONE_VALUE].value is None

    assert (
        detail_fixture.attempt_outcome.transport_status
        is TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED
    )
    assert detail_fixture.attempt_outcome.parser_status is ParserOutcomeStatus.USABLE_RESPONSE
    assert detail_fixture.listing_page_parse_outcome is not None
    assert detail_fixture.listing_page_parse_outcome.status is ParserOutcomeStatus.USABLE_RESPONSE
    assert (
        detail_fixture.listing_page_parse_outcome.normalized_listing_candidates[0].status
        is ListingCandidateStatus.USABLE
    )
    detail_fields = {
        field.field_family: field
        for field in detail_fixture.listing_page_parse_outcome.card_candidates[0].field_candidates
    }
    assert (
        detail_fields[ListingFieldFamily.DESCRIPTION].availability
        is ListingFieldAvailability.PROVEN_UNAVAILABLE
    )
    assert (
        detail_fields[ListingFieldFamily.SELLER].availability
        is ListingFieldAvailability.PROVEN_UNAVAILABLE
    )
    assert (
        detail_fields[ListingFieldFamily.SELLER_RATING].availability
        is ListingFieldAvailability.PROVEN_UNAVAILABLE
    )


def test_apa08_listing_fixtures_are_registered_once_and_payload_free() -> None:
    apa08_ids = {fixture_id for fixture_id in FIXTURE_IDS if fixture_id.startswith("FX-APA08-")}

    assert apa08_ids == {
        "FX-APA08-TIER1-LISTING-CARD-PROVEN-001",
        "FX-APA08-OPTIONAL-DETAIL-FIELDS-UNAVAILABLE-001",
        "FX-APA08-PHONE-VALUE-PROOF-GATED-001",
        "FX-APA08-OPTIONAL-FIELD-AMBIGUOUS-WARNING-001",
        "FX-APA08-FIELD-PROVENANCE-REQUIRED-001",
        "FX-APA08-NO-SCAN-NEWNESS-MUTATION-001",
        "FX-APA08-NO-RAW-PROVIDER-PAYLOAD-001",
    }
    assert len(apa08_ids) == 7
    for fixture_id in apa08_ids:
        fixture = SYNTHETIC_FIXTURE_BY_ID[fixture_id]
        assert fixture.listing_page_parse_outcome is not None
        assert not hasattr(fixture, "raw_provider_payload")


def test_apa08_listing_semantics_keep_tier1_usable_with_optional_gaps() -> None:
    optional_detail = SYNTHETIC_FIXTURE_BY_ID["FX-APA08-OPTIONAL-DETAIL-FIELDS-UNAVAILABLE-001"]
    phone = SYNTHETIC_FIXTURE_BY_ID["FX-APA08-PHONE-VALUE-PROOF-GATED-001"]
    ambiguous = SYNTHETIC_FIXTURE_BY_ID["FX-APA08-OPTIONAL-FIELD-AMBIGUOUS-WARNING-001"]
    provenance = SYNTHETIC_FIXTURE_BY_ID["FX-APA08-FIELD-PROVENANCE-REQUIRED-001"]

    assert optional_detail.listing_page_parse_outcome is not None
    assert (
        optional_detail.listing_page_parse_outcome.normalized_listing_candidates[0].status
        is ListingCandidateStatus.USABLE
    )
    assert (
        optional_detail.listing_page_parse_outcome.card_candidates[0]
        .field_candidates[0]
        .field_family
        is ListingFieldFamily.TITLE
    )
    assert (
        optional_detail.listing_page_parse_outcome.card_candidates[0]
        .field_candidates[0]
        .availability
        is ListingFieldAvailability.PROVEN_AVAILABLE
    )
    assert (
        optional_detail.listing_page_parse_outcome.card_candidates[0]
        .field_candidates[-1]
        .availability
        is ListingFieldAvailability.PROVEN_UNAVAILABLE
    )

    assert phone.listing_page_parse_outcome is not None
    assert (
        phone.listing_page_parse_outcome.normalized_listing_candidates[0].status
        is ListingCandidateStatus.USABLE
    )
    phone_fields = {
        field.field_family: field
        for field in phone.listing_page_parse_outcome.card_candidates[0].field_candidates
    }
    assert (
        phone_fields[ListingFieldFamily.PHONE_VALUE].availability
        is ListingFieldAvailability.PROOF_GATED
    )
    assert phone_fields[ListingFieldFamily.PHONE_VALUE].value is None

    assert ambiguous.listing_page_parse_outcome is not None
    assert (
        ambiguous.listing_page_parse_outcome.normalized_listing_candidates[0].status
        is ListingCandidateStatus.AMBIGUOUS
    )
    assert (
        ambiguous.listing_page_parse_outcome.warnings[0].code
        is ParserWarningCode.FIELD_CANDIDATE_OPTIONAL
    )

    assert provenance.listing_page_parse_outcome is not None
    proven_field = provenance.listing_page_parse_outcome.card_candidates[0].field_candidates[-1]
    assert proven_field.availability is ListingFieldAvailability.PROVEN_AVAILABLE
    assert proven_field.compatibility_profile is not None
    assert (
        proven_field.compatibility_profile.lifecycle_status
        is CompatibilityProfileLifecycleStatus.CURRENT
    )


def test_repeated_filters_and_sort_context_are_preserved_as_evidence() -> None:
    multivalue = SYNTHETIC_FIXTURE_BY_ID["FX-APA02-REPEATED-MULTIVALUE-FILTER-PRESERVATION-001"]
    sort_case = SYNTHETIC_FIXTURE_BY_ID["FX-APA02-AMBIGUOUS-SORT-NEWEST-EVIDENCE-001"]

    assert multivalue.search_configuration_extraction_outcome is not None
    assert multivalue.search_configuration_extraction_outcome.normalized_filter_candidates == (
        "city=synthetic",
        "city=synthetic",
        "metro=synthetic",
    )

    assert sort_case.search_configuration_extraction_outcome is not None
    assert sort_case.search_configuration_extraction_outcome.observed_sort_context_reference == (
        "sort-context::newest-vs-ambiguous"
    )
    assert sort_case.listing_page_parse_outcome is not None
    assert sort_case.listing_page_parse_outcome.warnings[0].code.value == "SORT_CONTEXT_AMBIGUOUS"


def test_apa09_listing_ordering_fixtures_preserve_order_and_gate_comparison() -> None:
    apa09_ids = {fixture_id for fixture_id in FIXTURE_IDS if fixture_id.startswith("FX-APA09-")}
    assert apa09_ids == {
        "FX-APA09-NEWEST-FIRST-PROVEN-001",
        "FX-APA09-OBSERVED-ORDER-PRESERVED-001",
        "FX-APA09-SORT-CONTEXT-MISSING-BLOCKS-001",
        "FX-APA09-SORT-CONTEXT-AMBIGUOUS-BLOCKS-001",
        "FX-APA09-SORT-CONTEXT-UNSUPPORTED-BLOCKS-001",
        "FX-APA09-SORT-CONTEXT-UNPROVEN-BLOCKS-001",
        "FX-APA09-SORT-CONTEXT-CONTRADICTORY-BLOCKS-001",
        "FX-APA09-PUBLICATION-SIGNAL-OPTIONAL-001",
        "FX-APA09-PARTIAL-PAGE-NOT-COMPARISON-ELIGIBLE-001",
        "FX-APA09-NO-SCAN-NEWNESS-DECISION-001",
        "FX-APA09-NO-ANCHOR-STATE-MUTATION-001",
    }
    assert len(apa09_ids) == 11

    cases = (
        (
            "FX-APA09-NEWEST-FIRST-PROVEN-001",
            ListingSortContextStatus.PROVEN_NEWEST_FIRST,
            ScanOrderingHandoffStatus.COMPARISON_ELIGIBLE,
        ),
        (
            "FX-APA09-OBSERVED-ORDER-PRESERVED-001",
            ListingSortContextStatus.UNPROVEN,
            ScanOrderingHandoffStatus.BLOCKED_SORT_UNPROVEN,
        ),
        (
            "FX-APA09-SORT-CONTEXT-MISSING-BLOCKS-001",
            ListingSortContextStatus.MISSING,
            ScanOrderingHandoffStatus.BLOCKED_SORT_MISSING,
        ),
        (
            "FX-APA09-SORT-CONTEXT-AMBIGUOUS-BLOCKS-001",
            ListingSortContextStatus.AMBIGUOUS,
            ScanOrderingHandoffStatus.BLOCKED_SORT_AMBIGUOUS,
        ),
        (
            "FX-APA09-SORT-CONTEXT-UNSUPPORTED-BLOCKS-001",
            ListingSortContextStatus.UNSUPPORTED,
            ScanOrderingHandoffStatus.BLOCKED_SORT_UNSUPPORTED,
        ),
        (
            "FX-APA09-SORT-CONTEXT-UNPROVEN-BLOCKS-001",
            ListingSortContextStatus.UNPROVEN,
            ScanOrderingHandoffStatus.BLOCKED_SORT_UNPROVEN,
        ),
        (
            "FX-APA09-SORT-CONTEXT-CONTRADICTORY-BLOCKS-001",
            ListingSortContextStatus.CONTRADICTORY,
            ScanOrderingHandoffStatus.BLOCKED_SORT_CONTRADICTORY,
        ),
        (
            "FX-APA09-PUBLICATION-SIGNAL-OPTIONAL-001",
            ListingSortContextStatus.PROVEN_NEWEST_FIRST,
            ScanOrderingHandoffStatus.COMPARISON_ELIGIBLE,
        ),
        (
            "FX-APA09-PARTIAL-PAGE-NOT-COMPARISON-ELIGIBLE-001",
            ListingSortContextStatus.PROVEN_NEWEST_FIRST,
            ScanOrderingHandoffStatus.BLOCKED_PAGE_NOT_USABLE,
        ),
        (
            "FX-APA09-NO-SCAN-NEWNESS-DECISION-001",
            ListingSortContextStatus.PROVEN_NEWEST_FIRST,
            ScanOrderingHandoffStatus.COMPARISON_ELIGIBLE,
        ),
        (
            "FX-APA09-NO-ANCHOR-STATE-MUTATION-001",
            ListingSortContextStatus.PROVEN_NEWEST_FIRST,
            ScanOrderingHandoffStatus.COMPARISON_ELIGIBLE,
        ),
    )

    for fixture_id, expected_ordering_status, expected_handoff_status in cases:
        page_fixture = SYNTHETIC_FIXTURE_BY_ID[fixture_id].listing_page_parse_outcome
        assert page_fixture is not None
        assert page_fixture.ordering_evidence is not None
        assert page_fixture.scan_ordering_handoff is not None
        assert page_fixture.ordering_evidence.status is expected_ordering_status
        assert page_fixture.scan_ordering_handoff.status is expected_handoff_status
        assert page_fixture.scan_ordering_handoff.listing_candidate_ids == tuple(
            candidate.listing_candidate_id
            for candidate in page_fixture.normalized_listing_candidates
        )
        assert [
            position.observed_rank for position in page_fixture.ordering_evidence.positions
        ] == [
            1,
            2,
            3,
        ]
        assert tuple(
            position.listing_candidate_id for position in page_fixture.ordering_evidence.positions
        ) == tuple(
            candidate.listing_candidate_id
            for candidate in page_fixture.normalized_listing_candidates
        )

    proven = SYNTHETIC_FIXTURE_BY_ID["FX-APA09-NEWEST-FIRST-PROVEN-001"].listing_page_parse_outcome
    assert proven is not None
    assert proven.ordering_evidence is not None
    assert proven.ordering_evidence.compatibility_profile is not None
    assert (
        proven.ordering_evidence.compatibility_profile.lifecycle_status
        is CompatibilityProfileLifecycleStatus.CURRENT
    )
    assert proven.ordering_evidence.sort_context_reference == "sort-context::apa09-newest-first"
    assert (
        proven.ordering_evidence.warnings[0].code
        is ParserWarningCode.OBSERVED_LISTING_ORDER_PRESERVED
    )
    assert proven.ordering_evidence.warnings[1].code is ParserWarningCode.NEWEST_FIRST_SORT_PROVEN

    observed = SYNTHETIC_FIXTURE_BY_ID[
        "FX-APA09-OBSERVED-ORDER-PRESERVED-001"
    ].listing_page_parse_outcome
    assert observed is not None
    assert observed.ordering_evidence is not None
    assert (
        observed.ordering_evidence.warnings[0].code
        is ParserWarningCode.OBSERVED_LISTING_ORDER_PRESERVED
    )
    assert observed.ordering_evidence.warnings[1].code is ParserWarningCode.SORT_CONTEXT_UNPROVEN

    publication = SYNTHETIC_FIXTURE_BY_ID[
        "FX-APA09-PUBLICATION-SIGNAL-OPTIONAL-001"
    ].listing_page_parse_outcome
    assert publication is not None
    assert publication.ordering_evidence is not None
    assert any(
        position.publication_order_signal_reference is not None
        for position in publication.ordering_evidence.positions
    )
    assert any(
        position.publication_order_signal_reference is None
        for position in publication.ordering_evidence.positions
    )
    assert (
        publication.ordering_evidence.warnings[0].code
        is ParserWarningCode.PUBLICATION_ORDER_SIGNAL_UNAVAILABLE
    )
    assert publication.scan_ordering_handoff is not None
    assert publication.scan_ordering_handoff.status is ScanOrderingHandoffStatus.COMPARISON_ELIGIBLE

    no_newness = SYNTHETIC_FIXTURE_BY_ID[
        "FX-APA09-NO-SCAN-NEWNESS-DECISION-001"
    ].listing_page_parse_outcome
    assert no_newness is not None
    assert no_newness.scan_ordering_handoff is not None
    assert no_newness.scan_ordering_handoff.warnings[0].code is (
        ParserWarningCode.SCAN_NEWNESS_DECISION_NOT_PERFORMED
    )

    no_anchor = SYNTHETIC_FIXTURE_BY_ID[
        "FX-APA09-NO-ANCHOR-STATE-MUTATION-001"
    ].listing_page_parse_outcome
    assert no_anchor is not None
    assert no_anchor.scan_ordering_handoff is not None
    assert no_anchor.scan_ordering_handoff.warnings[0].code is (
        ParserWarningCode.SCAN_ANCHOR_STATE_NOT_MUTATED
    )


def test_apa09_ordering_contracts_reject_invalid_sequences_and_profiles() -> None:
    evidence = (
        ParserEvidenceReference(
            reference_id="fx::apa09::invalid::evidence", evidence_kind="ordering"
        ),
    )[0]
    current_profile = SYNTHETIC_FIXTURE_BY_ID[
        "FX-APA09-NEWEST-FIRST-PROVEN-001"
    ].compatibility_profile
    assert current_profile is not None

    valid_position = ObservedListingPosition(
        position_id="fx::apa09::position::1",
        listing_candidate_id="fx::apa09::candidate::1",
        observed_rank=1,
        evidence_references=(evidence,),
    )
    valid_position_2 = ObservedListingPosition(
        position_id="fx::apa09::position::2",
        listing_candidate_id="fx::apa09::candidate::2",
        observed_rank=2,
        evidence_references=(evidence,),
    )

    with pytest.raises(ValueError):
        ObservedListingPosition(
            position_id="fx::apa09::position::blank",
            listing_candidate_id="fx::apa09::candidate::blank",
            observed_rank=1,
            publication_order_signal_reference=" ",
            evidence_references=(evidence,),
        )

    invalid_sequences = (
        (
            (
                ObservedListingPosition(
                    position_id="fx::apa09::dup::1",
                    listing_candidate_id="fx::apa09::candidate::1",
                    observed_rank=1,
                    evidence_references=(evidence,),
                ),
                ObservedListingPosition(
                    position_id="fx::apa09::dup::1",
                    listing_candidate_id="fx::apa09::candidate::2",
                    observed_rank=2,
                    evidence_references=(evidence,),
                ),
            ),
        ),
        (
            (
                ObservedListingPosition(
                    position_id="fx::apa09::dup-candidate::1",
                    listing_candidate_id="fx::apa09::candidate::1",
                    observed_rank=1,
                    evidence_references=(evidence,),
                ),
                ObservedListingPosition(
                    position_id="fx::apa09::dup-candidate::2",
                    listing_candidate_id="fx::apa09::candidate::1",
                    observed_rank=2,
                    evidence_references=(evidence,),
                ),
            ),
        ),
        (
            (
                ObservedListingPosition(
                    position_id="fx::apa09::dup-rank::1",
                    listing_candidate_id="fx::apa09::candidate::1",
                    observed_rank=1,
                    evidence_references=(evidence,),
                ),
                ObservedListingPosition(
                    position_id="fx::apa09::dup-rank::2",
                    listing_candidate_id="fx::apa09::candidate::2",
                    observed_rank=1,
                    evidence_references=(evidence,),
                ),
            ),
        ),
        (
            (
                ObservedListingPosition(
                    position_id="fx::apa09::gap::1",
                    listing_candidate_id="fx::apa09::candidate::1",
                    observed_rank=1,
                    evidence_references=(evidence,),
                ),
                ObservedListingPosition(
                    position_id="fx::apa09::gap::2",
                    listing_candidate_id="fx::apa09::candidate::2",
                    observed_rank=3,
                    evidence_references=(evidence,),
                ),
            ),
        ),
        (
            (
                valid_position_2,
                valid_position,
            ),
        ),
    )
    for (positions,) in invalid_sequences:
        with pytest.raises(ValueError):
            ListingOrderingEvidence(
                ordering_evidence_id="fx::apa09::invalid-ordering",
                status=ListingSortContextStatus.PROVEN_NEWEST_FIRST,
                positions=positions,
                sort_context_reference="sort-context::invalid",
                compatibility_profile=current_profile,
                evidence_references=(evidence,),
            )

    for profile in (
        None,
        ParserCompatibilityProfile(
            profile_id="fx::apa09::stale-profile",
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
        ),
        ParserCompatibilityProfile(
            profile_id="fx::apa09::disputed-profile",
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
        ),
        ParserCompatibilityProfile(
            profile_id="fx::apa09::unavailable-profile",
            semantic_version="2026.07.09",
            profile_version="2026.07.09",
            lifecycle_status=CompatibilityProfileLifecycleStatus.UNAVAILABLE,
            authority_class=CompatibilityProfileAuthorityClass.OBSERVATION_ONLY,
            authority_scope=("observation-only",),
            reference_ids=("AVITO-PRIMARY-PARSER-001",),
            primary_reference_repository="Duff89/parser_avito",
            primary_reference_commit="48441c352e36919abef13c436f41a3a62636da17",
            reference_status=ReferenceOutcomeStatus.REFERENCE_MISSING,
            evidence_reference=evidence,
        ),
    ):
        with pytest.raises(ValueError):
            ListingOrderingEvidence(
                ordering_evidence_id="fx::apa09::profile-gated",
                status=ListingSortContextStatus.PROVEN_NEWEST_FIRST,
                positions=(valid_position, valid_position_2),
                sort_context_reference="sort-context::profile-gated",
                compatibility_profile=profile,
                evidence_references=(evidence,),
            )
    with pytest.raises(ValueError):
        ListingOrderingEvidence(
            ordering_evidence_id="fx::apa09::blank-sort-ref",
            status=ListingSortContextStatus.PROVEN_NEWEST_FIRST,
            positions=(valid_position, valid_position_2),
            sort_context_reference=" ",
            compatibility_profile=current_profile,
            evidence_references=(evidence,),
        )
    with pytest.raises(ValueError):
        ListingOrderingEvidence(
            ordering_evidence_id="fx::apa09::missing-evidence",
            status=ListingSortContextStatus.PROVEN_NEWEST_FIRST,
            positions=(valid_position, valid_position_2),
            sort_context_reference="sort-context::missing-evidence",
            compatibility_profile=current_profile,
        )


def test_apa09_page_and_handoff_reject_order_mismatch() -> None:
    evidence = ParserEvidenceReference(
        reference_id="fx::apa09::mismatch::evidence",
        evidence_kind="ordering",
    )
    profile = SYNTHETIC_FIXTURE_BY_ID["FX-APA09-NEWEST-FIRST-PROVEN-001"].compatibility_profile
    assert profile is not None
    positions = (
        ObservedListingPosition(
            position_id="fx::apa09::mismatch::position::1",
            listing_candidate_id="fx::apa09::mismatch::candidate::1",
            observed_rank=1,
            evidence_references=(evidence,),
        ),
        ObservedListingPosition(
            position_id="fx::apa09::mismatch::position::2",
            listing_candidate_id="fx::apa09::mismatch::candidate::2",
            observed_rank=2,
            evidence_references=(evidence,),
        ),
    )
    ordering = ListingOrderingEvidence(
        ordering_evidence_id="fx::apa09::mismatch::ordering",
        status=ListingSortContextStatus.PROVEN_NEWEST_FIRST,
        positions=positions,
        sort_context_reference="sort-context::mismatch",
        compatibility_profile=profile,
        evidence_references=(evidence,),
    )
    card_1 = ListingCardCandidate(
        listing_card_id="fx::apa09::mismatch::card::1",
        evidence_references=(evidence,),
    )
    card_2 = ListingCardCandidate(
        listing_card_id="fx::apa09::mismatch::card::2",
        evidence_references=(evidence,),
    )
    candidate_1 = NormalizedListingCandidate(
        listing_candidate_id="fx::apa09::mismatch::candidate::1",
        status=ListingCandidateStatus.USABLE,
        card_candidate=card_1,
        evidence_references=(evidence,),
    )
    candidate_2 = NormalizedListingCandidate(
        listing_candidate_id="fx::apa09::mismatch::candidate::2",
        status=ListingCandidateStatus.USABLE,
        card_candidate=card_2,
        evidence_references=(evidence,),
    )
    with pytest.raises(ValueError):
        ParserScanOrderingHandoff(
            handoff_id="fx::apa09::mismatch::handoff",
            page_id="fx::apa09::mismatch::page",
            page_status=ParserOutcomeStatus.USABLE_RESPONSE,
            status=ScanOrderingHandoffStatus.COMPARISON_ELIGIBLE,
            ordering_evidence=ordering,
            listing_candidate_ids=(
                "fx::apa09::mismatch::candidate::2",
                "fx::apa09::mismatch::candidate::1",
            ),
            evidence_references=(evidence,),
        )
    handoff = ParserScanOrderingHandoff(
        handoff_id="fx::apa09::mismatch::handoff::ok",
        page_id="fx::apa09::mismatch::page",
        page_status=ParserOutcomeStatus.USABLE_RESPONSE,
        status=ScanOrderingHandoffStatus.COMPARISON_ELIGIBLE,
        ordering_evidence=ordering,
        listing_candidate_ids=(
            "fx::apa09::mismatch::candidate::1",
            "fx::apa09::mismatch::candidate::2",
        ),
        evidence_references=(evidence,),
    )
    with pytest.raises(ValueError):
        ListingPageParseOutcome(
            page_id="fx::apa09::mismatch::page",
            request_envelope=ParserRequestEnvelope(
                request_id="fx::apa09::mismatch::request",
                contract_name="mayak.avito.parser.request",
                contract_version="1.0",
                producer="mayak.tests.synthetic",
                purpose="listing-ordering",
                compatibility_profile=profile,
                safe_source_reference="bounded-source-value",
                configuration_revision_id="cfg::apa09::mismatch::001",
                safe_transport_reference="transport::apa09::mismatch",
            ),
            transport_outcome=TransportOutcomeReference(
                transport_reference_id="fx::apa09::mismatch::transport",
                transport_status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
                request_reference="fx::apa09::mismatch::request",
                response_reference="response::apa09::mismatch",
                route_reference="route::apa09::mismatch",
            ),
            status=ParserOutcomeStatus.USABLE_RESPONSE,
            compatibility_profile=profile,
            normalized_listing_candidates=(candidate_2, candidate_1),
            card_candidates=(card_2, card_1),
            ordering_evidence=ordering,
            scan_ordering_handoff=handoff,
            evidence_references=(evidence,),
        )


def test_apa09_non_usable_pages_are_never_comparison_eligible() -> None:
    evidence = ParserEvidenceReference(
        reference_id="fx::apa09::page-gate::evidence",
        evidence_kind="listing-ordering",
    )
    profile = SYNTHETIC_FIXTURE_BY_ID["FX-APA09-NEWEST-FIRST-PROVEN-001"].compatibility_profile
    assert profile is not None
    positions = (
        ObservedListingPosition(
            position_id="fx::apa09::page-gate::position::1",
            listing_candidate_id="fx::apa09::page-gate::candidate::1",
            observed_rank=1,
            evidence_references=(evidence,),
        ),
    )
    ordering = ListingOrderingEvidence(
        ordering_evidence_id="fx::apa09::page-gate::ordering",
        status=ListingSortContextStatus.PROVEN_NEWEST_FIRST,
        positions=positions,
        sort_context_reference="sort-context::page-gate",
        compatibility_profile=profile,
        evidence_references=(evidence,),
    )
    for page_status in (
        ParserOutcomeStatus.PARTIAL,
        ParserOutcomeStatus.MALFORMED_RESPONSE,
        ParserOutcomeStatus.INCOMPLETE_RESPONSE,
        ParserOutcomeStatus.RATE_OR_ACCESS_RESTRICTED,
        ParserOutcomeStatus.RESULT_AMBIGUOUS,
    ):
        handoff = ParserScanOrderingHandoff(
            handoff_id=f"fx::apa09::page-gate::{page_status.value.lower()}",
            page_id="fx::apa09::page-gate",
            page_status=page_status,
            status=ScanOrderingHandoffStatus.BLOCKED_PAGE_NOT_USABLE,
            ordering_evidence=ordering,
            listing_candidate_ids=("fx::apa09::page-gate::candidate::1",),
            evidence_references=(evidence,),
        )
        assert handoff.status is ScanOrderingHandoffStatus.BLOCKED_PAGE_NOT_USABLE


def test_partial_and_stale_outcomes_remain_explicit() -> None:
    partial = SYNTHETIC_FIXTURE_BY_ID["FX-APA02-PARTIAL-PAGE-BATCH-001"]
    stale = SYNTHETIC_FIXTURE_BY_ID["FX-APA02-STALE-COMPATIBILITY-PROFILE-001"]

    assert partial.listing_batch_parse_outcome is not None
    assert partial.listing_batch_parse_outcome.status is ParserOutcomeStatus.PARTIAL
    assert (
        partial.listing_batch_parse_outcome.page_outcomes[0].status is ParserOutcomeStatus.PARTIAL
    )
    assert stale.search_source_analysis_outcome is not None
    assert stale.search_source_analysis_outcome.status is ReferenceOutcomeStatus.REFERENCE_STALE


def test_contract_instances_are_frozen() -> None:
    fixture = SYNTHETIC_FIXTURE_BY_ID["FX-APA02-USABLE-SEARCH-TIER1-001"]

    with pytest.raises(FrozenInstanceError):
        fixture.summary = "changed"  # type: ignore[misc]


def test_apa03_compatibility_lifecycle_states_and_revalidation_are_explicit() -> None:
    current = SYNTHETIC_FIXTURE_BY_ID["FX-APA03-CURRENT-REFERENCE-PROFILE-001"]
    stale = SYNTHETIC_FIXTURE_BY_ID["FX-APA03-STALE-REFERENCE-PROFILE-BLOCKS-CLEAN-EMPTY-001"]
    disputed = SYNTHETIC_FIXTURE_BY_ID["FX-APA03-DISPUTED-REFERENCE-PROFILE-WARNING-001"]
    superseded = SYNTHETIC_FIXTURE_BY_ID["FX-APA03-SUPERSEDED-REFERENCE-PROFILE-001"]
    withdrawn = SYNTHETIC_FIXTURE_BY_ID["FX-APA03-WITHDRAWN-REFERENCE-PROFILE-BLOCKS-SUCCESS-001"]
    unavailable = SYNTHETIC_FIXTURE_BY_ID["FX-APA03-UNAVAILABLE-REFERENCE-PROFILE-001"]

    assert current.compatibility_profile is not None
    assert (
        current.compatibility_profile.lifecycle_status
        is CompatibilityProfileLifecycleStatus.CURRENT
    )
    assert current.compatibility_outcome is not None
    assert current.compatibility_outcome.change_class is CompatibilityChangeClass.COMPATIBLE

    assert stale.compatibility_profile is not None
    assert stale.compatibility_profile.lifecycle_status is CompatibilityProfileLifecycleStatus.STALE
    assert stale.compatibility_outcome is not None
    assert stale.compatibility_outcome.lifecycle_status is CompatibilityProfileLifecycleStatus.STALE
    assert stale.listing_page_parse_outcome is not None
    assert stale.listing_page_parse_outcome.status is CompatibilityProfileLifecycleStatus.STALE

    assert disputed.compatibility_profile is not None
    assert (
        disputed.compatibility_profile.lifecycle_status
        is CompatibilityProfileLifecycleStatus.DISPUTED
    )
    assert disputed.compatibility_outcome is not None
    assert disputed.compatibility_outcome.change_class is CompatibilityChangeClass.DISPUTED
    assert disputed.search_source_analysis_outcome is not None
    assert (
        disputed.search_source_analysis_outcome.status
        is CompatibilityProfileLifecycleStatus.DISPUTED
    )

    assert superseded.compatibility_profile is not None
    assert (
        superseded.compatibility_profile.lifecycle_status
        is CompatibilityProfileLifecycleStatus.SUPERSEDED
    )
    assert superseded.compatibility_outcome is not None
    assert superseded.compatibility_outcome.revalidation_triggers == (
        CompatibilityRevalidationTrigger.REFERENCE_CHANGED,
    )

    assert withdrawn.compatibility_profile is not None
    assert (
        withdrawn.compatibility_profile.lifecycle_status
        is CompatibilityProfileLifecycleStatus.WITHDRAWN
    )
    assert withdrawn.compatibility_outcome is not None
    assert withdrawn.compatibility_outcome.change_class is CompatibilityChangeClass.BREAKING
    assert withdrawn.listing_page_parse_outcome is not None
    assert (
        withdrawn.listing_page_parse_outcome.status is CompatibilityProfileLifecycleStatus.WITHDRAWN
    )

    assert unavailable.compatibility_profile is not None
    assert (
        unavailable.compatibility_profile.lifecycle_status
        is CompatibilityProfileLifecycleStatus.UNAVAILABLE
    )
    assert unavailable.compatibility_outcome is not None
    assert unavailable.compatibility_outcome.change_class is CompatibilityChangeClass.UNAVAILABLE


def test_apa03_reference_metadata_stays_observation_only_and_claim_scoped() -> None:
    current = SYNTHETIC_FIXTURE_BY_ID["FX-APA03-CURRENT-REFERENCE-PROFILE-001"]
    unsupported = SYNTHETIC_FIXTURE_BY_ID["FX-APA03-UNSUPPORTED-EXTRACTION-CLAIM-001"]
    changed = SYNTHETIC_FIXTURE_BY_ID["FX-APA03-REFERENCE-COMMIT-REVALIDATION-001"]
    internal = SYNTHETIC_FIXTURE_BY_ID["FX-APA03-INTERNAL-ENDPOINT-OBSERVATION-NOT-STABLE-001"]

    assert current.compatibility_profile is not None
    assert current.compatibility_profile.reference_ids == ("AVITO-PRIMARY-PARSER-001",)
    assert current.compatibility_profile.primary_reference_repository == "Duff89/parser_avito"
    assert (
        current.compatibility_profile.primary_reference_commit
        == "48441c352e36919abef13c436f41a3a62636da17"
    )
    assert (
        current.compatibility_profile.authority_class
        is not CompatibilityProfileAuthorityClass.OFFICIAL_PRIMARY_ONLY
    )

    assert unsupported.compatibility_profile is not None
    assert unsupported.compatibility_profile.supported_extraction_claims
    assert unsupported.compatibility_profile.unsupported_extraction_claims
    assert unsupported.search_configuration_extraction_outcome is not None
    assert (
        unsupported.search_configuration_extraction_outcome.status
        is ParserOutcomeStatus.UNSUPPORTED_STRUCTURE
    )

    assert changed.compatibility_outcome is not None
    assert changed.compatibility_outcome.revalidation_triggers == (
        CompatibilityRevalidationTrigger.REFERENCE_CHANGED,
    )
    assert changed.compatibility_outcome.change_class is CompatibilityChangeClass.WARNING

    assert internal.compatibility_profile is not None
    assert (
        internal.compatibility_profile.authority_class
        is CompatibilityProfileAuthorityClass.OBSERVATION_ONLY
    )
    assert internal.compatibility_outcome is not None
    assert internal.compatibility_outcome.change_class is CompatibilityChangeClass.UNKNOWN


def test_apa04_beacon_owned_source_reference_is_bounded_and_untrusted() -> None:
    fixture = SYNTHETIC_FIXTURE_BY_ID["FX-APA04-BEACON-OWNED-SOURCE-REFERENCE-001"]
    avito_live_url_marker = "".join(("a", "v", "i", "t", "o", ".", "r", "u"))

    assert fixture.request_envelope.source_reference is not None
    assert (
        fixture.request_envelope.source_reference.source_reference_kind
        is SourceReferenceKind.BEACON_OWNED_SUBMISSION
    )
    assert fixture.request_envelope.source_reference.ownership == "Beacon Management"
    assert fixture.request_envelope.source_reference.untrusted_input is True
    assert fixture.request_envelope.safe_source_reference == "bounded-source-value"
    assert fixture.request_envelope.source_boundary_outcome is not None
    assert (
        fixture.request_envelope.source_boundary_outcome.status
        is SourceBoundaryStatus.SOURCE_URL_UNTRUSTED
    )
    assert fixture.request_envelope.source_boundary_outcome.risk_codes == (
        SourceBoundaryRiskCode.SOURCE_URL_UNTRUSTED,
    )
    assert fixture.request_envelope.source_boundary_outcome.policy_requirements == (
        SourceBoundaryPolicyRequirement.HOST_POLICY_REQUIRED,
        SourceBoundaryPolicyRequirement.PATH_POLICY_REQUIRED,
        SourceBoundaryPolicyRequirement.QUERY_POLICY_REQUIRED,
    )
    assert fixture.transport_outcome.transport_status is TransportOutcomeStatus.NOT_SENT
    assert fixture.attempt_outcome.parser_status is ParserOutcomeStatus.USABLE_RESPONSE
    assert fixture.search_source_analysis_outcome is not None
    assert (
        fixture.search_source_analysis_outcome.status is SourceBoundaryStatus.SOURCE_URL_UNTRUSTED
    )
    assert (
        avito_live_url_marker not in fixture.request_envelope.source_reference.bounded_value.lower()
    )


def test_apa04_blocked_source_boundaries_remain_explicit() -> None:
    malformed = SYNTHETIC_FIXTURE_BY_ID["FX-APA04-MALFORMED-SOURCE-BLOCKED-001"]
    unsupported = SYNTHETIC_FIXTURE_BY_ID["FX-APA04-UNSUPPORTED-SOURCE-BLOCKED-001"]
    policy_missing = SYNTHETIC_FIXTURE_BY_ID["FX-APA04-POLICY-MISSING-SOURCE-BLOCKED-001"]
    redirect_blocked = SYNTHETIC_FIXTURE_BY_ID["FX-APA04-REDIRECT-POLICY-BLOCKED-001"]
    dns_blocked = SYNTHETIC_FIXTURE_BY_ID["FX-APA04-DNS-POLICY-BLOCKED-001"]
    canonicalization = SYNTHETIC_FIXTURE_BY_ID["FX-APA04-CANONICALIZATION-UNPROVEN-WARNING-001"]

    assert malformed.search_source_analysis_outcome is not None
    assert (
        malformed.search_source_analysis_outcome.status is SourceBoundaryStatus.SOURCE_URL_MALFORMED
    )
    assert malformed.transport_outcome.transport_status is TransportOutcomeStatus.NOT_SENT
    assert malformed.attempt_outcome.parser_status is ParserOutcomeStatus.EXPLICIT_REJECTION

    assert unsupported.search_source_analysis_outcome is not None
    assert (
        unsupported.search_source_analysis_outcome.status
        is SourceBoundaryStatus.SOURCE_URL_UNSUPPORTED
    )
    assert unsupported.attempt_outcome.parser_status is ParserOutcomeStatus.EXPLICIT_REJECTION

    assert policy_missing.search_source_analysis_outcome is not None
    assert (
        policy_missing.search_source_analysis_outcome.status
        is SourceBoundaryStatus.SOURCE_URL_POLICY_MISSING
    )
    assert policy_missing.request_envelope.source_reference is not None
    assert policy_missing.request_envelope.source_reference.host_reference == "provider.example"
    assert policy_missing.request_envelope.source_reference.path_reference == "/search"
    assert (
        policy_missing.request_envelope.source_reference.query_reference == "q=bounded-source-value"
    )

    assert redirect_blocked.search_source_analysis_outcome is not None
    assert (
        redirect_blocked.search_source_analysis_outcome.status
        is SourceBoundaryStatus.SOURCE_URL_REDIRECT_POLICY_BLOCKED
    )
    assert redirect_blocked.request_envelope.source_boundary_outcome is not None
    assert redirect_blocked.request_envelope.source_boundary_outcome.policy_requirements == (
        SourceBoundaryPolicyRequirement.REDIRECT_POLICY_REQUIRED,
    )

    assert dns_blocked.search_source_analysis_outcome is not None
    assert (
        dns_blocked.search_source_analysis_outcome.status
        is SourceBoundaryStatus.SOURCE_URL_DNS_POLICY_BLOCKED
    )
    assert dns_blocked.request_envelope.source_boundary_outcome is not None
    assert dns_blocked.request_envelope.source_boundary_outcome.policy_requirements == (
        SourceBoundaryPolicyRequirement.DNS_POLICY_REQUIRED,
    )

    assert canonicalization.search_source_analysis_outcome is not None
    assert (
        canonicalization.search_source_analysis_outcome.status
        is SourceBoundaryStatus.SOURCE_URL_CANONICALIZATION_UNPROVEN
    )
    assert canonicalization.attempt_outcome.parser_status is ParserOutcomeStatus.RESULT_AMBIGUOUS
    assert (
        canonicalization.search_source_analysis_outcome.warnings[0].code
        is ParserWarningCode.SOURCE_URL_CANONICALIZATION_UNPROVEN
    )


def test_apa05_transport_classification_stays_explicit_before_parser_success() -> None:
    not_sent = SYNTHETIC_FIXTURE_BY_ID["FX-APA05-NOT-SENT-001"]
    transport_unavailable = SYNTHETIC_FIXTURE_BY_ID["FX-APA05-TRANSPORT-UNAVAILABLE-001"]
    transport_ambiguous = SYNTHETIC_FIXTURE_BY_ID["FX-APA05-TRANSPORT-AMBIGUOUS-001"]
    response_unclassified = SYNTHETIC_FIXTURE_BY_ID[
        "FX-APA05-SENT-SUCCESS-RESPONSE-UNCLASSIFIED-001"
    ]

    assert not_sent.attempt_outcome.parser_status is None
    assert not_sent.attempt_outcome.transport_response_classification is not None
    assert (
        not_sent.attempt_outcome.transport_response_classification.status
        is TransportOutcomeStatus.NOT_SENT
    )
    assert (
        not_sent.attempt_outcome.transport_response_classification.classification_rule is not None
    )
    assert (
        "transport success alone is insufficient"
        in not_sent.attempt_outcome.transport_response_classification.classification_rule.notes
    )

    assert transport_unavailable.attempt_outcome.parser_status is None
    assert transport_unavailable.attempt_outcome.transport_response_classification is not None
    assert (
        transport_unavailable.attempt_outcome.transport_response_classification.status
        is TransportOutcomeStatus.TRANSPORT_UNAVAILABLE
    )

    assert transport_ambiguous.attempt_outcome.parser_status is None
    assert transport_ambiguous.attempt_outcome.transport_response_classification is not None
    assert (
        transport_ambiguous.attempt_outcome.transport_response_classification.status
        is TransportOutcomeStatus.TRANSPORT_AMBIGUOUS
    )

    assert (
        response_unclassified.attempt_outcome.transport_status
        is TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED
    )
    assert response_unclassified.attempt_outcome.parser_status is None
    assert response_unclassified.attempt_outcome.transport_response_classification is not None
    assert (
        response_unclassified.attempt_outcome.transport_response_classification.status
        is TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED
    )
    assert (
        response_unclassified.attempt_outcome.transport_response_classification.provider_response_evidence_class
        is ProviderResponseEvidenceClass.UNCLASSIFIED
    )


def test_apa05_current_profile_proof_and_boundary_keep_parser_success_explicit() -> None:
    fixture = SYNTHETIC_FIXTURE_BY_ID["FX-APA05-USABLE-RESPONSE-CURRENT-PROFILE-PROOF-001"]

    assert fixture.request_envelope.source_reference is not None
    assert fixture.request_envelope.source_boundary_outcome is not None
    assert (
        fixture.request_envelope.source_boundary_outcome.status
        is SourceBoundaryStatus.SOURCE_URL_UNTRUSTED
    )
    assert fixture.attempt_outcome.transport_response_classification is not None
    assert (
        fixture.attempt_outcome.transport_response_classification.status
        is ParserOutcomeStatus.USABLE_RESPONSE
    )
    assert fixture.attempt_outcome.transport_response_classification.classification_rule is not None
    assert (
        fixture.attempt_outcome.transport_response_classification.classification_rule.requires_current_profile_proof
        is True
    )
    assert fixture.search_source_analysis_outcome is not None
    assert fixture.search_source_analysis_outcome.status is ParserOutcomeStatus.USABLE_RESPONSE
    assert fixture.search_configuration_extraction_outcome is not None
    assert (
        fixture.search_configuration_extraction_outcome.status
        is ParserOutcomeStatus.USABLE_RESPONSE
    )
    assert fixture.listing_page_parse_outcome is not None
    assert fixture.listing_page_parse_outcome.status is ParserOutcomeStatus.USABLE_RESPONSE


def test_apa05_reference_and_partial_negative_cases_remain_explicit() -> None:
    stale = SYNTHETIC_FIXTURE_BY_ID["FX-APA05-STALE-REFERENCE-PROFILE-001"]
    missing = SYNTHETIC_FIXTURE_BY_ID["FX-APA05-MISSING-REFERENCE-PROFILE-001"]
    disputed = SYNTHETIC_FIXTURE_BY_ID["FX-APA05-DISPUTED-REFERENCE-PROFILE-001"]
    partial = SYNTHETIC_FIXTURE_BY_ID["FX-APA05-PARTIAL-RESPONSE-PAGE-001"]
    ambiguous = SYNTHETIC_FIXTURE_BY_ID["FX-APA05-AMBIGUOUS-RESULT-001"]
    clean_empty = SYNTHETIC_FIXTURE_BY_ID["FX-APA05-CLEAN-EMPTY-BLOCKED-WITHOUT-PROOF-001"]
    body_only = SYNTHETIC_FIXTURE_BY_ID["FX-APA05-HTTP-200-NON-EMPTY-NOT-ENOUGH-001"]

    assert stale.attempt_outcome.reference_status is ReferenceOutcomeStatus.REFERENCE_STALE
    assert stale.attempt_outcome.transport_response_classification is not None
    assert (
        stale.attempt_outcome.transport_response_classification.status
        is ReferenceOutcomeStatus.REFERENCE_STALE
    )
    assert stale.search_source_analysis_outcome is not None
    assert stale.search_source_analysis_outcome.status is ReferenceOutcomeStatus.REFERENCE_STALE

    assert missing.attempt_outcome.reference_status is ReferenceOutcomeStatus.REFERENCE_MISSING
    assert missing.attempt_outcome.transport_response_classification is not None
    assert (
        missing.attempt_outcome.transport_response_classification.status
        is ReferenceOutcomeStatus.REFERENCE_MISSING
    )

    assert disputed.attempt_outcome.reference_status is ReferenceOutcomeStatus.REFERENCE_DISPUTED
    assert disputed.attempt_outcome.transport_response_classification is not None
    assert (
        disputed.attempt_outcome.transport_response_classification.status
        is ReferenceOutcomeStatus.REFERENCE_DISPUTED
    )

    assert partial.attempt_outcome.parser_status is ParserOutcomeStatus.PARTIAL
    assert partial.attempt_outcome.transport_response_classification is not None
    assert (
        partial.attempt_outcome.transport_response_classification.status
        is ParserOutcomeStatus.PARTIAL
    )
    assert partial.listing_batch_parse_outcome is not None
    assert partial.listing_batch_parse_outcome.status is ParserOutcomeStatus.PARTIAL

    assert ambiguous.attempt_outcome.parser_status is ParserOutcomeStatus.RESULT_AMBIGUOUS
    assert ambiguous.attempt_outcome.transport_response_classification is not None
    assert (
        ambiguous.attempt_outcome.transport_response_classification.status
        is ParserOutcomeStatus.RESULT_AMBIGUOUS
    )
    assert ambiguous.listing_page_parse_outcome is not None
    assert ambiguous.listing_page_parse_outcome.status is ParserOutcomeStatus.RESULT_AMBIGUOUS

    assert clean_empty.attempt_outcome.parser_status is ParserOutcomeStatus.EXPLICIT_REJECTION
    assert clean_empty.attempt_outcome.transport_response_classification is not None
    assert (
        clean_empty.attempt_outcome.transport_response_classification.status
        is ReferenceOutcomeStatus.REFERENCE_MISSING
    )
    assert (
        clean_empty.attempt_outcome.transport_response_classification.provider_response_evidence_class
        is ProviderResponseEvidenceClass.EMPTY_WITHOUT_PROOF
    )
    assert (
        clean_empty.attempt_outcome.transport_response_classification.response_completeness_status
        is ResponseCompletenessStatus.EMPTY_BLOCKED
    )

    assert body_only.attempt_outcome.parser_status is None
    assert body_only.attempt_outcome.transport_response_classification is not None
    assert (
        body_only.attempt_outcome.transport_response_classification.status
        is TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED
    )
    assert (
        body_only.attempt_outcome.transport_response_classification.provider_response_evidence_class
        is ProviderResponseEvidenceClass.BODY_PRESENT_UNCLASSIFIED
    )


def test_apa04_parser_output_preserves_beacon_source_ownership() -> None:
    fixture = SYNTHETIC_FIXTURE_BY_ID["FX-APA04-PARSER-OUTPUT-NOT-OVERWRITING-BEACON-SOURCE-001"]

    assert fixture.request_envelope.source_reference is not None
    assert fixture.request_envelope.source_boundary_outcome is not None
    assert (
        fixture.request_envelope.source_boundary_outcome.source_reference
        is fixture.request_envelope.source_reference
    )
    assert fixture.search_configuration_extraction_outcome is not None
    assert (
        fixture.search_configuration_extraction_outcome.status
        is SourceBoundaryStatus.SOURCE_URL_UNTRUSTED
    )
    assert fixture.search_configuration_extraction_outcome.normalized_geography_candidates == (
        "safe-geography",
    )
    assert fixture.search_configuration_extraction_outcome.normalized_category_candidates == (
        "safe-category",
    )
    assert fixture.search_configuration_extraction_outcome.normalized_filter_candidates == (
        "ownership=beacon",
    )
    assert not hasattr(fixture.search_configuration_extraction_outcome, "source_reference")


def test_apa06_search_configuration_candidates_keep_provenance_and_repeated_values_explicit() -> (
    None
):
    geography = SYNTHETIC_FIXTURE_BY_ID["FX-APA06-GEOGRAPHY-CANDIDATE-001"]
    category = SYNTHETIC_FIXTURE_BY_ID["FX-APA06-CATEGORY-CANDIDATE-001"]
    price = SYNTHETIC_FIXTURE_BY_ID["FX-APA06-PRICE-BOUNDS-CANDIDATE-001"]
    structured = SYNTHETIC_FIXTURE_BY_ID["FX-APA06-STRUCTURED-FILTER-KV-CANDIDATE-001"]
    multivalue = SYNTHETIC_FIXTURE_BY_ID["FX-APA06-REPEATED-MULTIVALUE-PARAM-PRESERVED-001"]

    assert geography.search_configuration_extraction_outcome is not None
    assert (
        geography.search_configuration_extraction_outcome.search_configuration_evidence is not None
    )
    assert (
        geography.search_configuration_extraction_outcome.search_configuration_candidates[
            0
        ].extraction_field
        is SearchConfigurationExtractionField.GEOGRAPHY_CONTEXT
    )
    assert (
        geography.search_configuration_extraction_outcome.search_configuration_candidates[
            0
        ].field_status
        is SearchConfigurationFieldStatus.EVIDENCE_BOUND
    )
    assert (
        geography.search_configuration_extraction_outcome.search_configuration_candidates[0]
        .parameter_candidates[0]
        .evidence_references
    )

    assert category.search_configuration_extraction_outcome is not None
    assert (
        category.search_configuration_extraction_outcome.search_configuration_candidates[
            0
        ].extraction_field
        is SearchConfigurationExtractionField.CATEGORY_CONTEXT
    )
    assert (
        category.search_configuration_extraction_outcome.search_configuration_candidates[
            0
        ].value_kind
        is SearchConfigurationValueKind.SCALAR
    )

    assert price.search_configuration_extraction_outcome is not None
    assert [
        candidate.extraction_field
        for candidate in (
            price.search_configuration_extraction_outcome.search_configuration_candidates
        )
    ] == [
        SearchConfigurationExtractionField.PRICE_LOWER_BOUND,
        SearchConfigurationExtractionField.PRICE_UPPER_BOUND,
    ]
    assert [
        parameter.parameter_value
        for parameter in price.search_configuration_extraction_outcome.parameter_candidates
    ] == ["1000", "5000"]

    assert structured.search_configuration_extraction_outcome is not None
    assert structured.search_configuration_extraction_outcome.normalized_filter_candidates == (
        "filter-key:synthetic-color=value:synthetic-red",
    )
    assert (
        structured.search_configuration_extraction_outcome.search_configuration_candidates[
            0
        ].field_status
        is SearchConfigurationFieldStatus.EVIDENCE_BOUND
    )

    assert multivalue.search_configuration_extraction_outcome is not None
    assert (
        multivalue.search_configuration_extraction_outcome.search_configuration_candidates[
            0
        ].field_status
        is SearchConfigurationFieldStatus.PRESERVED
    )
    assert multivalue.search_configuration_extraction_outcome.search_configuration_candidates[
        0
    ].parameter_candidates[0].repeated_values == (
        "value:synthetic-red",
        "value:synthetic-blue",
    )
    assert multivalue.search_configuration_extraction_outcome.parameter_candidates[
        0
    ].repeated_values == (
        "value:synthetic-red",
        "value:synthetic-blue",
    )
    assert (
        multivalue.search_configuration_extraction_outcome.search_configuration_evidence is not None
    )
    assert (
        multivalue.search_configuration_extraction_outcome.search_configuration_evidence.request_envelope.safe_source_reference
        == "source-ref:beacon-revision-060"
    )
    assert not hasattr(multivalue.search_configuration_extraction_outcome, "source_reference")


def test_apa06_search_configuration_negative_and_policy_gated_cases_remain_explicit() -> None:
    unsupported = SYNTHETIC_FIXTURE_BY_ID["FX-APA06-UNSUPPORTED-PARAMETER-WARNING-001"]
    ambiguous = SYNTHETIC_FIXTURE_BY_ID["FX-APA06-AMBIGUOUS-PARAMETER-WARNING-001"]
    lossy = SYNTHETIC_FIXTURE_BY_ID["FX-APA06-LOSSY-NORMALIZATION-BLOCKED-001"]
    sort = SYNTHETIC_FIXTURE_BY_ID["FX-APA06-SORT-CONTEXT-UNPROVEN-001"]
    pagination = SYNTHETIC_FIXTURE_BY_ID["FX-APA06-PAGINATION-CONTEXT-BLOCKED-001"]
    country_wide = SYNTHETIC_FIXTURE_BY_ID["FX-APA06-COUNTRY-WIDE-CANDIDATE-POLICY-GATED-001"]
    filter_editability = SYNTHETIC_FIXTURE_BY_ID["FX-APA06-FILTER-EDITABILITY-NOT-DECLARED-001"]
    beacon_snapshot = SYNTHETIC_FIXTURE_BY_ID[
        "FX-APA06-BEACON-SNAPSHOT-ACCEPTANCE-NOT-PERFORMED-001"
    ]

    assert unsupported.search_configuration_extraction_outcome is not None
    assert (
        unsupported.search_configuration_extraction_outcome.status
        is ParserOutcomeStatus.UNSUPPORTED_STRUCTURE
    )
    assert (
        unsupported.search_configuration_extraction_outcome.search_configuration_candidates[
            0
        ].field_status
        is SearchConfigurationFieldStatus.UNSUPPORTED
    )
    assert (
        unsupported.search_configuration_extraction_outcome.warnings[0].code
        is SearchConfigurationWarningCode.UNSUPPORTED_PARAMETER_EXPLICIT
    )

    assert ambiguous.search_configuration_extraction_outcome is not None
    assert (
        ambiguous.search_configuration_extraction_outcome.status
        is ParserOutcomeStatus.RESULT_AMBIGUOUS
    )
    assert (
        ambiguous.search_configuration_extraction_outcome.search_configuration_candidates[
            0
        ].field_status
        is SearchConfigurationFieldStatus.AMBIGUOUS
    )
    assert (
        ambiguous.search_configuration_extraction_outcome.warnings[0].code
        is SearchConfigurationWarningCode.AMBIGUOUS_PARAMETER_EXPLICIT
    )

    assert lossy.search_configuration_extraction_outcome is not None
    assert (
        lossy.search_configuration_extraction_outcome.status is ParserOutcomeStatus.RESULT_AMBIGUOUS
    )
    assert (
        lossy.search_configuration_extraction_outcome.search_configuration_candidates[
            0
        ].field_status
        is SearchConfigurationFieldStatus.LOSSY_NORMALIZATION_BLOCKED
    )
    assert (
        lossy.search_configuration_extraction_outcome.warnings[0].code
        is SearchConfigurationWarningCode.LOSSY_NORMALIZATION_BLOCKED
    )

    assert sort.search_configuration_extraction_outcome is not None
    assert (
        sort.search_configuration_extraction_outcome.observed_sort_context_reference
        == "sort-context::synthetic-newest"
    )
    assert (
        sort.search_configuration_extraction_outcome.search_configuration_candidates[0].field_status
        is SearchConfigurationFieldStatus.UNPROVEN
    )
    assert (
        sort.search_configuration_extraction_outcome.warnings[0].code
        is SearchConfigurationWarningCode.SORT_CONTEXT_UNPROVEN
    )

    assert pagination.search_configuration_extraction_outcome is not None
    assert (
        pagination.search_configuration_extraction_outcome.status
        is ParserOutcomeStatus.EXPLICIT_REJECTION
    )
    assert (
        pagination.search_configuration_extraction_outcome.search_configuration_candidates[
            0
        ].field_status
        is SearchConfigurationFieldStatus.POLICY_GATED
    )
    assert (
        pagination.search_configuration_extraction_outcome.warnings[0].code
        is SearchConfigurationWarningCode.PAGINATION_CONTEXT_BLOCKED
    )

    assert country_wide.search_configuration_extraction_outcome is not None
    assert (
        country_wide.search_configuration_extraction_outcome.search_configuration_candidates[
            0
        ].field_status
        is SearchConfigurationFieldStatus.POLICY_GATED
    )
    assert (
        country_wide.search_configuration_extraction_outcome.warnings[0].code
        is SearchConfigurationWarningCode.COUNTRY_WIDE_POLICY_GATED
    )

    assert filter_editability.search_configuration_extraction_outcome is not None
    assert (
        filter_editability.search_configuration_extraction_outcome.search_configuration_candidates[
            0
        ].field_status
        is SearchConfigurationFieldStatus.POLICY_GATED
    )
    assert (
        filter_editability.search_configuration_extraction_outcome.parameter_candidates[
            0
        ].parameter_value
        == "not-declared"
    )
    assert (
        filter_editability.search_configuration_extraction_outcome.warnings[0].code
        is SearchConfigurationWarningCode.FILTER_EDITABILITY_NOT_DECLARED
    )

    assert beacon_snapshot.search_configuration_extraction_outcome is not None
    assert (
        beacon_snapshot.search_configuration_extraction_outcome.search_configuration_candidates[
            0
        ].field_status
        is SearchConfigurationFieldStatus.POLICY_GATED
    )
    assert (
        beacon_snapshot.search_configuration_extraction_outcome.warnings[0].code
        is SearchConfigurationWarningCode.BEACON_SNAPSHOT_ACCEPTANCE_NOT_PERFORMED
    )


def test_apa06_search_configuration_depends_on_profile_and_source_boundary_gates() -> None:
    fixture = SYNTHETIC_FIXTURE_BY_ID["FX-APA06-GEOGRAPHY-CANDIDATE-001"]

    assert fixture.compatibility_profile is not None
    assert (
        fixture.compatibility_profile.lifecycle_status
        is CompatibilityProfileLifecycleStatus.CURRENT
    )
    assert fixture.request_envelope.source_reference is not None
    assert (
        fixture.request_envelope.source_reference.bounded_value == "source-ref:beacon-revision-060"
    )
    assert (
        fixture.request_envelope.source_reference.beacon_source_reference
        == "source-ref:beacon-revision-060"
    )
    assert fixture.request_envelope.source_boundary_outcome is not None
    assert (
        fixture.request_envelope.source_boundary_outcome.status
        is SourceBoundaryStatus.SOURCE_URL_UNTRUSTED
    )
    assert fixture.search_configuration_extraction_outcome is not None
    assert fixture.search_configuration_extraction_outcome.search_configuration_evidence is not None
    assert (
        fixture.search_configuration_extraction_outcome.search_configuration_evidence.compatibility_profile
        is fixture.compatibility_profile
    )
    assert (
        fixture.search_configuration_extraction_outcome.search_configuration_evidence.source_boundary_outcome
        is fixture.request_envelope.source_boundary_outcome
    )
    assert (
        fixture.search_configuration_extraction_outcome.request_envelope.safe_source_reference
        == fixture.request_envelope.safe_source_reference
    )
    assert not hasattr(fixture.search_configuration_extraction_outcome, "source_reference")


def test_apa07_multivalue_normalization_preserves_order_and_duplicates() -> None:
    repeated = SYNTHETIC_FIXTURE_BY_ID["FX-APA07-REPEATED-VALUES-ORDER-PRESERVED-001"]
    duplicates = SYNTHETIC_FIXTURE_BY_ID["FX-APA07-DUPLICATES-PRESERVED-001"]
    approved = SYNTHETIC_FIXTURE_BY_ID["FX-APA07-PROFILE-BOUND-COLLECTION-PRESERVED-001"]
    first_blocked = SYNTHETIC_FIXTURE_BY_ID["FX-APA07-FIRST-VALUE-OVERWRITE-BLOCKED-001"]
    later_blocked = SYNTHETIC_FIXTURE_BY_ID["FX-APA07-LATER-VALUE-LOSS-BLOCKED-001"]
    scalar_blocked = SYNTHETIC_FIXTURE_BY_ID["FX-APA07-COLLECTION-TO-SCALAR-BLOCKED-001"]

    assert repeated.search_configuration_extraction_outcome is not None
    assert (
        repeated.search_configuration_extraction_outcome.parameter_candidates[
            0
        ].multivalue_normalization
        is not None
    )
    assert (
        repeated.search_configuration_extraction_outcome.parameter_candidates[
            0
        ].multivalue_normalization.status
        is MultivalueNormalizationStatus.PRESERVED
    )
    assert repeated.search_configuration_extraction_outcome.parameter_candidates[
        0
    ].multivalue_normalization.normalized_values == (
        "value:synthetic-red",
        "value:synthetic-blue",
    )
    assert repeated.search_configuration_extraction_outcome.normalized_filter_candidates == (
        "filter-key:synthetic-color=value:synthetic-red",
        "filter-key:synthetic-color=value:synthetic-blue",
    )

    assert duplicates.search_configuration_extraction_outcome is not None
    assert duplicates.search_configuration_extraction_outcome.parameter_candidates[
        0
    ].repeated_values == (
        "value:synthetic-red",
        "value:synthetic-red",
        "value:synthetic-blue",
    )
    assert (
        duplicates.search_configuration_extraction_outcome.parameter_candidates[
            0
        ].multivalue_normalization
        is not None
    )
    assert duplicates.search_configuration_extraction_outcome.parameter_candidates[
        0
    ].multivalue_normalization.normalized_values == (
        "value:synthetic-red",
        "value:synthetic-red",
        "value:synthetic-blue",
    )

    assert approved.search_configuration_extraction_outcome is not None
    assert (
        approved.search_configuration_extraction_outcome.parameter_candidates[
            0
        ].multivalue_normalization
        is not None
    )
    assert approved.search_configuration_extraction_outcome.parameter_candidates[
        0
    ].multivalue_normalization.normalized_values == (
        "value:synthetic-red",
        "value:synthetic-blue",
    )

    assert first_blocked.search_configuration_extraction_outcome is not None
    assert (
        first_blocked.search_configuration_extraction_outcome.status
        is ParserOutcomeStatus.RESULT_AMBIGUOUS
    )
    assert (
        first_blocked.search_configuration_extraction_outcome.parameter_candidates[
            0
        ].multivalue_normalization
        is not None
    )
    assert (
        first_blocked.search_configuration_extraction_outcome.parameter_candidates[
            0
        ].multivalue_normalization.status
        is MultivalueNormalizationStatus.LOSSY
    )
    assert (
        first_blocked.search_configuration_extraction_outcome.parameter_candidates[
            0
        ].multivalue_normalization.loss_reason
        is MultivalueLossReason.FIRST_VALUE_OVERWRITE_BLOCKED
    )
    assert (
        first_blocked.search_configuration_extraction_outcome.parameter_candidates[
            0
        ].multivalue_normalization.normalized_values
        == ()
    )

    assert later_blocked.search_configuration_extraction_outcome is not None
    assert (
        later_blocked.search_configuration_extraction_outcome.parameter_candidates[
            0
        ].multivalue_normalization
        is not None
    )
    assert (
        later_blocked.search_configuration_extraction_outcome.parameter_candidates[
            0
        ].multivalue_normalization.loss_reason
        is MultivalueLossReason.LATER_VALUE_LOSS_BLOCKED
    )
    assert (
        later_blocked.search_configuration_extraction_outcome.parameter_candidates[
            0
        ].multivalue_normalization.normalized_values
        == ()
    )

    assert scalar_blocked.search_configuration_extraction_outcome is not None
    assert (
        scalar_blocked.search_configuration_extraction_outcome.parameter_candidates[
            0
        ].multivalue_normalization
        is not None
    )
    assert (
        scalar_blocked.search_configuration_extraction_outcome.parameter_candidates[
            0
        ].multivalue_normalization.loss_reason
        is MultivalueLossReason.COLLECTION_TO_SCALAR_COLLAPSE_BLOCKED
    )
    assert (
        scalar_blocked.search_configuration_extraction_outcome.parameter_candidates[
            0
        ].multivalue_normalization.normalized_values
        == ()
    )


def test_apa07_multivalue_unsupported_ambiguous_and_lossy_states_remain_explicit() -> None:
    unsupported = SYNTHETIC_FIXTURE_BY_ID["FX-APA07-UNSUPPORTED-MULTIVALUE-EXPLICIT-001"]
    ambiguous = SYNTHETIC_FIXTURE_BY_ID["FX-APA07-AMBIGUOUS-MULTIVALUE-EXPLICIT-001"]
    lossy = SYNTHETIC_FIXTURE_BY_ID["FX-APA07-LOSSY-NORMALIZATION-EXPLICIT-001"]

    assert unsupported.search_configuration_extraction_outcome is not None
    assert (
        unsupported.search_configuration_extraction_outcome.status
        is ParserOutcomeStatus.UNSUPPORTED_STRUCTURE
    )
    assert (
        unsupported.search_configuration_extraction_outcome.search_configuration_candidates[
            0
        ].field_status
        is SearchConfigurationFieldStatus.UNSUPPORTED
    )
    assert (
        unsupported.search_configuration_extraction_outcome.parameter_candidates[
            0
        ].multivalue_normalization
        is not None
    )
    assert (
        unsupported.search_configuration_extraction_outcome.parameter_candidates[
            0
        ].multivalue_normalization.status
        is MultivalueNormalizationStatus.UNSUPPORTED
    )
    assert (
        unsupported.search_configuration_extraction_outcome.parameter_candidates[
            0
        ].multivalue_normalization.loss_reason
        is MultivalueLossReason.UNSUPPORTED_MULTIVALUE_PARAMETER
    )
    assert (
        unsupported.search_configuration_extraction_outcome.warnings[0].code
        is SearchConfigurationWarningCode.UNSUPPORTED_PARAMETER_EXPLICIT
    )

    assert ambiguous.search_configuration_extraction_outcome is not None
    assert (
        ambiguous.search_configuration_extraction_outcome.status
        is ParserOutcomeStatus.RESULT_AMBIGUOUS
    )
    assert (
        ambiguous.search_configuration_extraction_outcome.search_configuration_candidates[
            0
        ].field_status
        is SearchConfigurationFieldStatus.AMBIGUOUS
    )
    assert (
        ambiguous.search_configuration_extraction_outcome.parameter_candidates[
            0
        ].multivalue_normalization
        is not None
    )
    assert (
        ambiguous.search_configuration_extraction_outcome.parameter_candidates[
            0
        ].multivalue_normalization.status
        is MultivalueNormalizationStatus.AMBIGUOUS
    )
    assert (
        ambiguous.search_configuration_extraction_outcome.parameter_candidates[
            0
        ].multivalue_normalization.loss_reason
        is MultivalueLossReason.AMBIGUOUS_MULTIVALUE_PARAMETER
    )
    assert (
        ambiguous.search_configuration_extraction_outcome.warnings[0].code
        is SearchConfigurationWarningCode.AMBIGUOUS_PARAMETER_EXPLICIT
    )

    assert lossy.search_configuration_extraction_outcome is not None
    assert (
        lossy.search_configuration_extraction_outcome.status is ParserOutcomeStatus.RESULT_AMBIGUOUS
    )
    assert (
        lossy.search_configuration_extraction_outcome.search_configuration_candidates[
            0
        ].field_status
        is SearchConfigurationFieldStatus.LOSSY_NORMALIZATION_BLOCKED
    )
    assert (
        lossy.search_configuration_extraction_outcome.parameter_candidates[
            0
        ].multivalue_normalization
        is not None
    )
    assert (
        lossy.search_configuration_extraction_outcome.parameter_candidates[
            0
        ].multivalue_normalization.status
        is MultivalueNormalizationStatus.LOSSY
    )
    assert (
        lossy.search_configuration_extraction_outcome.parameter_candidates[
            0
        ].multivalue_normalization.loss_reason
        is MultivalueLossReason.DUPLICATE_REMOVAL_BLOCKED
    )
    assert (
        lossy.search_configuration_extraction_outcome.warnings[0].code
        is SearchConfigurationWarningCode.LOSSY_NORMALIZATION_BLOCKED
    )


def test_apa07_multivalue_profile_source_response_and_ownership_gates_are_explicit() -> None:
    stale = SYNTHETIC_FIXTURE_BY_ID["FX-APA07-PROFILE-NOT-CURRENT-BLOCKS-001"]
    missing = SYNTHETIC_FIXTURE_BY_ID["FX-APA07-PROFILE-MISSING-BLOCKS-001"]
    disputed = SYNTHETIC_FIXTURE_BY_ID["FX-APA07-PROFILE-DISPUTED-BLOCKS-001"]
    source_blocked = SYNTHETIC_FIXTURE_BY_ID["FX-APA07-SOURCE-BOUNDARY-BLOCKS-001"]
    response_blocked = SYNTHETIC_FIXTURE_BY_ID["FX-APA07-RESPONSE-CLASSIFICATION-BLOCKS-001"]
    filter_editability = SYNTHETIC_FIXTURE_BY_ID["FX-APA07-FILTER-EDITABILITY-NOT-DECLARED-001"]
    beacon = SYNTHETIC_FIXTURE_BY_ID["FX-APA07-BEACON-NO-MUTATION-001"]
    scan = SYNTHETIC_FIXTURE_BY_ID["FX-APA07-SCAN-NO-MUTATION-001"]

    assert stale.compatibility_profile is not None
    assert stale.compatibility_profile.lifecycle_status is CompatibilityProfileLifecycleStatus.STALE
    assert stale.search_configuration_extraction_outcome is not None
    assert (
        stale.search_configuration_extraction_outcome.status
        is CompatibilityProfileLifecycleStatus.STALE
    )
    assert (
        stale.search_configuration_extraction_outcome.parameter_candidates[
            0
        ].multivalue_normalization
        is not None
    )
    assert (
        stale.search_configuration_extraction_outcome.parameter_candidates[
            0
        ].multivalue_normalization.loss_reason
        is MultivalueLossReason.PROFILE_STALE
    )
    assert (
        stale.search_configuration_extraction_outcome.warnings[0].code
        is ParserWarningCode.STALE_COMPATIBILITY_PROFILE
    )

    assert missing.compatibility_profile is not None
    assert (
        missing.compatibility_profile.lifecycle_status
        is CompatibilityProfileLifecycleStatus.UNAVAILABLE
    )
    assert missing.search_configuration_extraction_outcome is not None
    assert (
        missing.search_configuration_extraction_outcome.status
        is ReferenceOutcomeStatus.REFERENCE_MISSING
    )
    assert (
        missing.search_configuration_extraction_outcome.parameter_candidates[
            0
        ].multivalue_normalization
        is not None
    )
    assert (
        missing.search_configuration_extraction_outcome.parameter_candidates[
            0
        ].multivalue_normalization.loss_reason
        is MultivalueLossReason.PROFILE_MISSING
    )
    assert (
        missing.search_configuration_extraction_outcome.warnings[0].code
        is ParserWarningCode.UNAVAILABLE_PROFILE_WARNING
    )

    assert disputed.compatibility_profile is not None
    assert (
        disputed.compatibility_profile.lifecycle_status
        is CompatibilityProfileLifecycleStatus.DISPUTED
    )
    assert disputed.search_configuration_extraction_outcome is not None
    assert (
        disputed.search_configuration_extraction_outcome.status
        is ReferenceOutcomeStatus.REFERENCE_DISPUTED
    )
    assert (
        disputed.search_configuration_extraction_outcome.parameter_candidates[
            0
        ].multivalue_normalization
        is not None
    )
    assert (
        disputed.search_configuration_extraction_outcome.parameter_candidates[
            0
        ].multivalue_normalization.loss_reason
        is MultivalueLossReason.PROFILE_DISPUTED
    )
    assert (
        disputed.search_configuration_extraction_outcome.warnings[0].code
        is ParserWarningCode.DISPUTED_PROFILE_WARNING
    )

    assert source_blocked.search_configuration_extraction_outcome is not None
    assert (
        source_blocked.search_configuration_extraction_outcome.status
        is SourceBoundaryStatus.SOURCE_URL_MALFORMED
    )
    assert (
        source_blocked.search_configuration_extraction_outcome.parameter_candidates[
            0
        ].multivalue_normalization
        is not None
    )
    assert (
        source_blocked.search_configuration_extraction_outcome.parameter_candidates[
            0
        ].multivalue_normalization.loss_reason
        is MultivalueLossReason.SOURCE_BOUNDARY_INVALID
    )
    assert (
        source_blocked.search_configuration_extraction_outcome.warnings[0].code
        is ParserWarningCode.SOURCE_URL_MALFORMED
    )
    assert (
        source_blocked.search_configuration_extraction_outcome.search_configuration_evidence
        is not None
    )
    assert (
        source_blocked.search_configuration_extraction_outcome.search_configuration_evidence.source_boundary_outcome
        is not None
    )
    assert (
        source_blocked.search_configuration_extraction_outcome.search_configuration_evidence.source_boundary_outcome.status
        is SourceBoundaryStatus.SOURCE_URL_MALFORMED
    )

    assert response_blocked.search_configuration_extraction_outcome is not None
    assert (
        response_blocked.search_configuration_extraction_outcome.status
        is ParserOutcomeStatus.RESULT_AMBIGUOUS
    )
    assert (
        response_blocked.search_configuration_extraction_outcome.parameter_candidates[
            0
        ].multivalue_normalization
        is not None
    )
    assert (
        response_blocked.search_configuration_extraction_outcome.parameter_candidates[
            0
        ].multivalue_normalization.loss_reason
        is MultivalueLossReason.RESPONSE_CLASSIFICATION_NOT_TRUSTED
    )
    assert (
        response_blocked.search_configuration_extraction_outcome.parameter_candidates[
            0
        ].multivalue_normalization.transport_response_classification
        is not None
    )
    assert (
        response_blocked.search_configuration_extraction_outcome.parameter_candidates[
            0
        ].multivalue_normalization.transport_response_classification.response_completeness_status
        is ResponseCompletenessStatus.AMBIGUOUS
    )
    assert (
        response_blocked.search_configuration_extraction_outcome.warnings[0].code
        is SearchConfigurationWarningCode.LOSSY_NORMALIZATION_BLOCKED
    )

    assert filter_editability.search_configuration_extraction_outcome is not None
    assert (
        filter_editability.search_configuration_extraction_outcome.search_configuration_candidates[
            0
        ].field_status
        is SearchConfigurationFieldStatus.POLICY_GATED
    )
    assert (
        filter_editability.search_configuration_extraction_outcome.warnings[0].code
        is SearchConfigurationWarningCode.FILTER_EDITABILITY_NOT_DECLARED
    )

    assert beacon.search_configuration_extraction_outcome is not None
    assert (
        beacon.search_configuration_extraction_outcome.search_configuration_candidates[
            0
        ].field_status
        is SearchConfigurationFieldStatus.POLICY_GATED
    )
    assert (
        beacon.search_configuration_extraction_outcome.warnings[0].code
        is SearchConfigurationWarningCode.BEACON_SNAPSHOT_ACCEPTANCE_NOT_PERFORMED
    )

    assert scan.search_configuration_extraction_outcome is not None
    assert (
        scan.search_configuration_extraction_outcome.search_configuration_candidates[0].field_status
        is SearchConfigurationFieldStatus.POLICY_GATED
    )
    assert (
        scan.search_configuration_extraction_outcome.warnings[0].code
        is SearchConfigurationWarningCode.PAGINATION_CONTEXT_BLOCKED
    )
