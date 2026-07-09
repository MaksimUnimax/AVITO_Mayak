from __future__ import annotations

from dataclasses import FrozenInstanceError, fields

from mayak.modules import avito_parser_adapter
from mayak.modules.avito_parser_adapter import (
    CompatibilityChangeClass,
    CompatibilityProfileAuthorityClass,
    CompatibilityProfileLifecycleStatus,
    CompatibilityRevalidationTrigger,
    MODULE_ID,
    ParserAttemptOutcome,
    ParserCompatibilityOutcome,
    ParserCompatibilityProfile,
    ParserEvidenceReference,
    ParserOutcomeExplanation,
    ParserOutcomeStatus,
    ParserResponseClassificationRule,
    ParserRequestEnvelope,
    ParserWarning,
    ParserWarningCode,
    ProviderResponseEvidenceClass,
    ReferenceOutcomeStatus,
    ResponseCompletenessStatus,
    ResponseRestrictionSignal,
    SYNTHETIC_FIXTURE_BY_ID,
    ParserSourceReference,
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
        "SourceBoundaryOutcome",
        "SourceBoundaryPolicyRequirement",
        "SourceBoundaryRiskCode",
        "SourceBoundaryStatus",
        "SourceReferenceKind",
        "ProviderResponseEvidenceClass",
        "ResponseCompletenessStatus",
        "ResponseRestrictionSignal",
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
    assert classification.provider_response_evidence_class is ProviderResponseEvidenceClass.USABLE_RESPONSE
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
    }


def test_synthetic_fixture_cases_are_safe_and_non_empty() -> None:
    assert len(SYNTHETIC_FIXTURE_BY_ID) == len({fixture.fixture_id for fixture in SYNTHETIC_FIXTURE_BY_ID.values()})
    avito_live_url_marker = "".join(("a", "v", "i", "t", "o", ".", "r", "u"))
    for fixture in SYNTHETIC_FIXTURE_BY_ID.values():
        assert fixture.fixture_id.startswith(("FX-APA02-", "FX-APA03-", "FX-APA04-", "FX-APA05-"))
        assert avito_live_url_marker not in fixture.summary.lower()
