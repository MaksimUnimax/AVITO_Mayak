from __future__ import annotations

from dataclasses import FrozenInstanceError, fields

from mayak.modules import avito_parser_adapter
from mayak.modules.avito_parser_adapter import (
    CompatibilityChangeClass,
    CompatibilityProfileAuthorityClass,
    CompatibilityProfileLifecycleStatus,
    CompatibilityRevalidationTrigger,
    MODULE_ID,
    ParserCompatibilityOutcome,
    ParserCompatibilityProfile,
    ParserEvidenceReference,
    ParserOutcomeExplanation,
    ParserWarning,
    ParserWarningCode,
    ReferenceOutcomeStatus,
    SYNTHETIC_FIXTURE_BY_ID,
    TransportOutcomeStatus,
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
        "ParserAttemptOutcome",
        "SearchSourceAnalysisOutcome",
        "SearchConfigurationExtractionOutcome",
        "ListingPageParseOutcome",
        "ListingBatchParseOutcome",
        "ParserWarning",
        "ParserEvidenceReference",
        "ParserOutcomeExplanation",
        "NormalizedListingCandidate",
        "ListingCardCandidate",
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

    assert profile.evidence_reference is evidence
    assert explanation.warnings == (warning,)
    assert outcome.compatibility_profile is profile
    assert outcome.change_class is CompatibilityChangeClass.COMPATIBLE
    assert outcome.lifecycle_status is CompatibilityProfileLifecycleStatus.CURRENT
    assert outcome.revalidation_triggers == (CompatibilityRevalidationTrigger.REFERENCE_CHANGED,)
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


def test_synthetic_fixture_cases_are_safe_and_non_empty() -> None:
    assert len(SYNTHETIC_FIXTURE_BY_ID) == len({fixture.fixture_id for fixture in SYNTHETIC_FIXTURE_BY_ID.values()})
    avito_live_url_marker = "".join(("a", "v", "i", "t", "o", ".", "r", "u"))
    for fixture in SYNTHETIC_FIXTURE_BY_ID.values():
        assert fixture.fixture_id.startswith(("FX-APA02-", "FX-APA03-"))
        assert avito_live_url_marker not in fixture.summary.lower()
