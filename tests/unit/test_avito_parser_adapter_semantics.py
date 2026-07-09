from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from mayak.modules.avito_parser_adapter import (
    CompatibilityChangeClass,
    CompatibilityProfileAuthorityClass,
    CompatibilityProfileLifecycleStatus,
    CompatibilityRevalidationTrigger,
    FIXTURE_IDS,
    ParserOutcomeStatus,
    ParserWarningCode,
    ReferenceOutcomeStatus,
    SourceBoundaryPolicyRequirement,
    SourceBoundaryRiskCode,
    SourceBoundaryStatus,
    SourceReferenceKind,
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


def test_apa04_source_boundary_enums_are_stable() -> None:
    assert [member.value for member in SourceReferenceKind] == [
        "BEACON_SUBMITTED_URL",
        "SAFE_BOUNDED_VALUE",
        "APPROVED_REQUEST_REFERENCE",
        "BEACON_PERSISTED_REFERENCE",
    ]
    assert [member.value for member in SourceBoundaryStatus] == [
        "ACCEPTED",
        "BLOCKED",
        "REJECTED",
        "POLICY_MISSING",
        "MALFORMED",
        "UNSUPPORTED",
        "UNPROVEN",
    ]
    assert [member.value for member in SourceBoundaryPolicyRequirement] == [
        "BEACON_OWNERSHIP_PRESERVED",
        "SAFE_REFERENCE_ONLY",
        "HOST_PATH_QUERY_POLICY",
        "REDIRECT_POLICY",
        "DNS_POLICY",
        "CANONICALIZATION_POLICY",
        "NO_SHELL_TARGETS",
        "NO_FILESYSTEM_TARGETS",
        "NO_NETWORK_TARGETS",
    ]
    assert [member.value for member in SourceBoundaryRiskCode] == [
        "SOURCE_URL_UNTRUSTED",
        "SOURCE_URL_POLICY_MISSING",
        "SOURCE_URL_MALFORMED",
        "SOURCE_URL_UNSUPPORTED",
        "SOURCE_URL_CANONICALIZATION_UNPROVEN",
        "SOURCE_URL_REDIRECT_POLICY_BLOCKED",
        "SOURCE_URL_DNS_POLICY_BLOCKED",
        "SOURCE_VALUE_SHELL_TARGET_BLOCKED",
        "SOURCE_VALUE_FILESYSTEM_TARGET_BLOCKED",
        "SOURCE_VALUE_NETWORK_TARGET_BLOCKED",
    ]
    assert {member.value for member in ParserWarningCode} >= {
        "SOURCE_URL_UNTRUSTED",
        "SOURCE_URL_POLICY_MISSING",
        "SOURCE_URL_MALFORMED",
        "SOURCE_URL_UNSUPPORTED",
        "SOURCE_URL_CANONICALIZATION_UNPROVEN",
        "SOURCE_URL_REDIRECT_POLICY_BLOCKED",
        "SOURCE_URL_DNS_POLICY_BLOCKED",
        "SOURCE_VALUE_SHELL_TARGET_BLOCKED",
        "SOURCE_VALUE_FILESYSTEM_TARGET_BLOCKED",
        "SOURCE_VALUE_NETWORK_TARGET_BLOCKED",
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


def test_apa03_compatibility_lifecycle_states_and_revalidation_are_explicit() -> None:
    current = SYNTHETIC_FIXTURE_BY_ID["FX-APA03-CURRENT-REFERENCE-PROFILE-001"]
    stale = SYNTHETIC_FIXTURE_BY_ID["FX-APA03-STALE-REFERENCE-PROFILE-BLOCKS-CLEAN-EMPTY-001"]
    disputed = SYNTHETIC_FIXTURE_BY_ID["FX-APA03-DISPUTED-REFERENCE-PROFILE-WARNING-001"]
    superseded = SYNTHETIC_FIXTURE_BY_ID["FX-APA03-SUPERSEDED-REFERENCE-PROFILE-001"]
    withdrawn = SYNTHETIC_FIXTURE_BY_ID["FX-APA03-WITHDRAWN-REFERENCE-PROFILE-BLOCKS-SUCCESS-001"]
    unavailable = SYNTHETIC_FIXTURE_BY_ID["FX-APA03-UNAVAILABLE-REFERENCE-PROFILE-001"]

    assert current.compatibility_profile is not None
    assert current.compatibility_profile.lifecycle_status is CompatibilityProfileLifecycleStatus.CURRENT
    assert current.compatibility_outcome is not None
    assert current.compatibility_outcome.change_class is CompatibilityChangeClass.COMPATIBLE

    assert stale.compatibility_profile is not None
    assert stale.compatibility_profile.lifecycle_status is CompatibilityProfileLifecycleStatus.STALE
    assert stale.compatibility_outcome is not None
    assert stale.compatibility_outcome.lifecycle_status is CompatibilityProfileLifecycleStatus.STALE
    assert stale.listing_page_parse_outcome is not None
    assert stale.listing_page_parse_outcome.status is CompatibilityProfileLifecycleStatus.STALE

    assert disputed.compatibility_profile is not None
    assert disputed.compatibility_profile.lifecycle_status is CompatibilityProfileLifecycleStatus.DISPUTED
    assert disputed.compatibility_outcome is not None
    assert disputed.compatibility_outcome.change_class is CompatibilityChangeClass.DISPUTED
    assert disputed.search_source_analysis_outcome is not None
    assert disputed.search_source_analysis_outcome.status is CompatibilityProfileLifecycleStatus.DISPUTED

    assert superseded.compatibility_profile is not None
    assert superseded.compatibility_profile.lifecycle_status is CompatibilityProfileLifecycleStatus.SUPERSEDED
    assert superseded.compatibility_outcome is not None
    assert superseded.compatibility_outcome.revalidation_triggers == (
        CompatibilityRevalidationTrigger.REFERENCE_CHANGED,
    )

    assert withdrawn.compatibility_profile is not None
    assert withdrawn.compatibility_profile.lifecycle_status is CompatibilityProfileLifecycleStatus.WITHDRAWN
    assert withdrawn.compatibility_outcome is not None
    assert withdrawn.compatibility_outcome.change_class is CompatibilityChangeClass.BREAKING
    assert withdrawn.listing_page_parse_outcome is not None
    assert withdrawn.listing_page_parse_outcome.status is CompatibilityProfileLifecycleStatus.WITHDRAWN

    assert unavailable.compatibility_profile is not None
    assert unavailable.compatibility_profile.lifecycle_status is CompatibilityProfileLifecycleStatus.UNAVAILABLE
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
    assert current.compatibility_profile.primary_reference_commit == "48441c352e36919abef13c436f41a3a62636da17"
    assert current.compatibility_profile.authority_class is not CompatibilityProfileAuthorityClass.OFFICIAL_PRIMARY_ONLY

    assert unsupported.compatibility_profile is not None
    assert unsupported.compatibility_profile.supported_extraction_claims
    assert unsupported.compatibility_profile.unsupported_extraction_claims
    assert unsupported.search_configuration_extraction_outcome is not None
    assert unsupported.search_configuration_extraction_outcome.status is ParserOutcomeStatus.UNSUPPORTED_STRUCTURE

    assert changed.compatibility_outcome is not None
    assert changed.compatibility_outcome.revalidation_triggers == (
        CompatibilityRevalidationTrigger.REFERENCE_CHANGED,
    )
    assert changed.compatibility_outcome.change_class is CompatibilityChangeClass.WARNING

    assert internal.compatibility_profile is not None
    assert internal.compatibility_profile.authority_class is CompatibilityProfileAuthorityClass.OBSERVATION_ONLY
    assert internal.compatibility_outcome is not None
    assert internal.compatibility_outcome.change_class is CompatibilityChangeClass.UNKNOWN


def test_apa04_source_boundary_accepts_only_safe_bounded_metadata() -> None:
    accepted = SYNTHETIC_FIXTURE_BY_ID["FX-APA04-SOURCE-REFERENCE-BOUNDED-INPUT-ACCEPTED-001"]
    preserved = SYNTHETIC_FIXTURE_BY_ID["FX-APA04-SOURCE-BOUNDARY-PARSER-OUTPUT-PRESERVES-BEACON-SOURCE-001"]

    assert accepted.source_boundary_outcome is not None
    assert accepted.source_boundary_outcome.status is SourceBoundaryStatus.ACCEPTED
    assert accepted.source_boundary_outcome.source_reference.owner == "Beacon Management"
    assert accepted.source_boundary_outcome.source_reference.untrusted_input is True
    assert accepted.request_envelope.source_reference is not None
    assert accepted.request_envelope.source_reference.bounded_value == "source-ref:beacon-revision-001"
    assert accepted.request_envelope.safe_source_reference == "source-ref:beacon-revision-001"
    assert accepted.attempt_outcome.transport_status is TransportOutcomeStatus.NOT_SENT
    assert accepted.attempt_outcome.parser_status is ParserOutcomeStatus.USABLE_RESPONSE
    assert not hasattr(accepted.attempt_outcome, "source_reference")
    assert not hasattr(accepted.transport_outcome, "source_reference")

    assert preserved.source_boundary_outcome is not None
    assert preserved.source_boundary_outcome.status is SourceBoundaryStatus.ACCEPTED
    assert preserved.request_envelope.source_reference is not None
    assert preserved.request_envelope.source_reference.source_reference_kind is SourceReferenceKind.BEACON_PERSISTED_REFERENCE
    assert preserved.request_envelope.source_boundary_outcome is preserved.source_boundary_outcome
    assert preserved.attempt_outcome.transport_status is TransportOutcomeStatus.NOT_SENT
    assert preserved.attempt_outcome.parser_status is ParserOutcomeStatus.USABLE_RESPONSE
    assert not hasattr(preserved.attempt_outcome, "source_reference")


def test_apa04_source_boundary_malformed_unsupported_and_policy_missing_are_explicit() -> None:
    malformed = SYNTHETIC_FIXTURE_BY_ID["FX-APA04-SOURCE-BOUNDARY-MALFORMED-REJECTED-001"]
    unsupported = SYNTHETIC_FIXTURE_BY_ID["FX-APA04-SOURCE-BOUNDARY-UNSUPPORTED-BLOCKED-001"]
    policy_missing = SYNTHETIC_FIXTURE_BY_ID["FX-APA04-SOURCE-BOUNDARY-POLICY-MISSING-001"]
    redirect_missing = SYNTHETIC_FIXTURE_BY_ID["FX-APA04-SOURCE-BOUNDARY-REDIRECT-POLICY-MISSING-001"]
    dns_missing = SYNTHETIC_FIXTURE_BY_ID["FX-APA04-SOURCE-BOUNDARY-DNS-POLICY-MISSING-001"]

    assert malformed.source_boundary_outcome is not None
    assert malformed.source_boundary_outcome.status is SourceBoundaryStatus.MALFORMED
    assert malformed.source_boundary_outcome.risk_codes == (SourceBoundaryRiskCode.SOURCE_URL_MALFORMED,)
    assert malformed.attempt_outcome.parser_status is ParserOutcomeStatus.MALFORMED_RESPONSE

    assert unsupported.source_boundary_outcome is not None
    assert unsupported.source_boundary_outcome.status is SourceBoundaryStatus.UNSUPPORTED
    assert unsupported.source_boundary_outcome.risk_codes == (SourceBoundaryRiskCode.SOURCE_URL_UNSUPPORTED,)
    assert unsupported.attempt_outcome.parser_status is ParserOutcomeStatus.UNSUPPORTED_STRUCTURE

    assert policy_missing.source_boundary_outcome is not None
    assert policy_missing.source_boundary_outcome.status is SourceBoundaryStatus.POLICY_MISSING
    assert policy_missing.source_boundary_outcome.policy_requirements == (
        SourceBoundaryPolicyRequirement.HOST_PATH_QUERY_POLICY,
    )
    assert policy_missing.source_boundary_outcome.risk_codes == (SourceBoundaryRiskCode.SOURCE_URL_POLICY_MISSING,)
    assert policy_missing.attempt_outcome.parser_status is ParserOutcomeStatus.EXPLICIT_REJECTION

    assert redirect_missing.source_boundary_outcome is not None
    assert redirect_missing.source_boundary_outcome.status is SourceBoundaryStatus.POLICY_MISSING
    assert redirect_missing.source_boundary_outcome.policy_requirements == (
        SourceBoundaryPolicyRequirement.REDIRECT_POLICY,
    )
    assert redirect_missing.source_boundary_outcome.risk_codes == (
        SourceBoundaryRiskCode.SOURCE_URL_REDIRECT_POLICY_BLOCKED,
    )
    assert redirect_missing.attempt_outcome.parser_status is ParserOutcomeStatus.EXPLICIT_REJECTION

    assert dns_missing.source_boundary_outcome is not None
    assert dns_missing.source_boundary_outcome.status is SourceBoundaryStatus.POLICY_MISSING
    assert dns_missing.source_boundary_outcome.policy_requirements == (
        SourceBoundaryPolicyRequirement.DNS_POLICY,
    )
    assert dns_missing.source_boundary_outcome.risk_codes == (
        SourceBoundaryRiskCode.SOURCE_URL_DNS_POLICY_BLOCKED,
    )
    assert dns_missing.attempt_outcome.parser_status is ParserOutcomeStatus.EXPLICIT_REJECTION


def test_apa04_canonicalization_and_target_blocking_remain_explicit() -> None:
    canonicalization = SYNTHETIC_FIXTURE_BY_ID["FX-APA04-SOURCE-BOUNDARY-CANONICALIZATION-UNPROVEN-001"]
    shell = SYNTHETIC_FIXTURE_BY_ID["FX-APA04-SOURCE-BOUNDARY-SHELL-TARGET-BLOCKED-001"]
    filesystem = SYNTHETIC_FIXTURE_BY_ID["FX-APA04-SOURCE-BOUNDARY-FILESYSTEM-TARGET-BLOCKED-001"]
    network = SYNTHETIC_FIXTURE_BY_ID["FX-APA04-SOURCE-BOUNDARY-NETWORK-TARGET-BLOCKED-001"]

    assert canonicalization.source_boundary_outcome is not None
    assert canonicalization.source_boundary_outcome.status is SourceBoundaryStatus.UNPROVEN
    assert canonicalization.source_boundary_outcome.risk_codes == (
        SourceBoundaryRiskCode.SOURCE_URL_CANONICALIZATION_UNPROVEN,
    )
    assert canonicalization.attempt_outcome.parser_status is ParserOutcomeStatus.RESULT_AMBIGUOUS

    assert shell.source_boundary_outcome is not None
    assert shell.source_boundary_outcome.status is SourceBoundaryStatus.BLOCKED
    assert shell.source_boundary_outcome.risk_codes == (
        SourceBoundaryRiskCode.SOURCE_VALUE_SHELL_TARGET_BLOCKED,
    )
    assert shell.attempt_outcome.parser_status is ParserOutcomeStatus.EXPLICIT_REJECTION

    assert filesystem.source_boundary_outcome is not None
    assert filesystem.source_boundary_outcome.status is SourceBoundaryStatus.BLOCKED
    assert filesystem.source_boundary_outcome.risk_codes == (
        SourceBoundaryRiskCode.SOURCE_VALUE_FILESYSTEM_TARGET_BLOCKED,
    )
    assert filesystem.attempt_outcome.parser_status is ParserOutcomeStatus.EXPLICIT_REJECTION

    assert network.source_boundary_outcome is not None
    assert network.source_boundary_outcome.status is SourceBoundaryStatus.BLOCKED
    assert network.source_boundary_outcome.risk_codes == (
        SourceBoundaryRiskCode.SOURCE_VALUE_NETWORK_TARGET_BLOCKED,
    )
    assert network.attempt_outcome.parser_status is ParserOutcomeStatus.EXPLICIT_REJECTION
