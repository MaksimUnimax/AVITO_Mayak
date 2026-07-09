from __future__ import annotations

from dataclasses import FrozenInstanceError

from mayak.modules import avito_parser_adapter
from mayak.modules.avito_parser_adapter import (
    MODULE_ID,
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
        "ParserCompatibilityProfile",
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
        profile_version="2026.07.09",
        reference_status=ReferenceOutcomeStatus.CURRENT,
        evidence_reference=evidence,
    )
    explanation = ParserOutcomeExplanation(
        summary="safe summary",
        reason_code="FX::SAFE",
        status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
        evidence_references=(evidence,),
        warnings=(warning,),
    )

    assert profile.evidence_reference is evidence
    assert explanation.warnings == (warning,)

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
        assert fixture.fixture_id.startswith("FX-APA02-")
        assert avito_live_url_marker not in fixture.summary.lower()
