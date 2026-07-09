from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from mayak.modules.avito_parser_adapter import (
    FIXTURE_IDS,
    ParserOutcomeStatus,
    ReferenceOutcomeStatus,
    SYNTHETIC_FIXTURE_BY_ID,
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
    assert [member.value for member in ReferenceOutcomeStatus] == [
        "REFERENCE_STALE",
        "REFERENCE_MISSING",
        "REFERENCE_DISPUTED",
        "CURRENT",
    ]


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
    }
    assert expected_ids.issubset(SYNTHETIC_FIXTURE_BY_ID)


def test_optional_listing_fields_do_not_fail_parser_semantics() -> None:
    fixture = SYNTHETIC_FIXTURE_BY_ID["FX-APA02-OPTIONAL-PHONE-UNAVAILABLE-001"]

    assert fixture.attempt_outcome.transport_status is TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED
    assert fixture.attempt_outcome.parser_status is ParserOutcomeStatus.USABLE_RESPONSE
    assert fixture.listing_page_parse_outcome is not None
    assert fixture.listing_page_parse_outcome.status is ParserOutcomeStatus.USABLE_RESPONSE
    assert fixture.listing_page_parse_outcome.card_candidates[0].phone is None
    assert fixture.listing_page_parse_outcome.card_candidates[0].seller is None


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


def test_partial_and_stale_outcomes_remain_explicit() -> None:
    partial = SYNTHETIC_FIXTURE_BY_ID["FX-APA02-PARTIAL-PAGE-BATCH-001"]
    stale = SYNTHETIC_FIXTURE_BY_ID["FX-APA02-STALE-COMPATIBILITY-PROFILE-001"]

    assert partial.listing_batch_parse_outcome is not None
    assert partial.listing_batch_parse_outcome.status is ParserOutcomeStatus.PARTIAL
    assert partial.listing_batch_parse_outcome.page_outcomes[0].status is ParserOutcomeStatus.PARTIAL
    assert stale.search_source_analysis_outcome is not None
    assert stale.search_source_analysis_outcome.status is ReferenceOutcomeStatus.REFERENCE_STALE


def test_contract_instances_are_frozen() -> None:
    fixture = SYNTHETIC_FIXTURE_BY_ID["FX-APA02-USABLE-SEARCH-TIER1-001"]

    with pytest.raises(FrozenInstanceError):
        fixture.summary = "changed"  # type: ignore[misc]
