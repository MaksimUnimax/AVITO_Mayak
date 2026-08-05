from datetime import datetime, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

from mayak.modules.filter_catalog import (
    CapabilityEnvelope,
    DependencyEnvelope,
    EvidenceEnvelope,
    FilterDependencyKind,
    WarningEnvelope,
)
from mayak.modules.filter_catalog.contracts import (
    FilterCapabilityProfile,
    FilterCapabilityState,
    FilterDefinition,
    FilterDefinitionState,
    FilterValueKind,
)
from mayak.modules.filter_catalog.value_dependency_semantics import (
    FilterSemanticExposureReason,
    FilterSemanticExposureRequest,
    MultivaluePreservationRequest,
    RangeValueValidationRequest,
    evaluate_filter_semantic_exposure,
    evaluate_multivalue_preservation,
    validate_range_value,
)


def _evidence() -> dict:
    return {
        "schema_version": "rf22-filter-evidence/v1",
        "evidence_state": "CURRENT",
        "evidence_kind_code": "SYNTHETIC_ACCEPTANCE",
        "scope_reference_ids": ["SYNTHETIC_PROVIDER_SURFACE", "SYNTHETIC_GEO"],
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "limitations": ["SYNTHETIC_ONLY"],
        "refresh_required": False,
    }


def test_rf22_envelopes_are_versioned_and_fail_closed() -> None:
    assert EvidenceEnvelope.model_validate(_evidence()).schema_version == "rf22-filter-evidence/v1"
    with pytest.raises(ValidationError):
        EvidenceEnvelope.model_validate({**_evidence(), "unexpected": True})
    with pytest.raises(ValidationError):
        EvidenceEnvelope.model_validate(
            {**_evidence(), "schema_version": "rf22-filter-evidence/v0"}
        )


def test_rf22_capability_range_and_warning_are_strict() -> None:
    warning = WarningEnvelope(
        warning_id="SYNTHETIC_WARNING",
        compatibility_state="CHANGED_BREAKING",
        safe_code="SYNTHETIC_BLOCKING_WARNING",
        evidence_reference_ids=("SYNTHETIC_EVIDENCE",),
        blocks_editability=True,
    )
    envelope = CapabilityEnvelope(
        schema_version="rf22-filter-capability-profile/v1",
        provider_surface_reference_id="SYNTHETIC_PROVIDER_SURFACE",
        category_scope_reference_id="SYNTHETIC_CATEGORY",
        geography_scope_reference_id="SYNTHETIC_GEO",
        fields={
            "SYNTHETIC_RANGE": {
                "definition_id": "SYNTHETIC_RANGE_DEFINITION",
                "capability_state": "EDITABLE",
                "value_kind": "RANGE",
                "required": False,
                "evidence_reference_ids": ["SYNTHETIC_EVIDENCE"],
                "range_definition": {
                    "range_definition_id": "SYNTHETIC_RANGE",
                    "unit_code": "SYNTHETIC_UNIT",
                    "lower_bound": "0",
                    "upper_bound": "100",
                    "lower_inclusive": True,
                    "upper_inclusive": False,
                    "step": "5",
                    "evidence_reference_ids": ["SYNTHETIC_EVIDENCE"],
                },
                "warning_ids": ["SYNTHETIC_WARNING"],
                "compatibility_warnings": [warning.model_dump()],
            }
        },
    )
    assert envelope.fields["SYNTHETIC_RANGE"].range_definition is not None
    assert envelope.fields["SYNTHETIC_RANGE"].range_definition.step == Decimal("5")
    with pytest.raises(ValidationError):
        DependencyEnvelope(
            schema_version="rf22-filter-dependency/v1",
            dependency_kind=FilterDependencyKind.CONSTRAINS,
            condition_code="SYNTHETIC_ACTIVE",
            outcome_code="SYNTHETIC_ALLOWED",
            evidence_reference_ids=("SYNTHETIC_EVIDENCE",),
        )


def _semantic_fixture() -> tuple[FilterDefinition, FilterCapabilityProfile]:
    definition = FilterDefinition(
        filter_definition_id="DEF_A",
        filter_catalog_version_id="CATALOG",
        normalized_key="FIELD_A",
        safe_label="Field A",
        value_kind=FilterValueKind.SCALAR,
        definition_state=FilterDefinitionState.APPROVED,
        evidence_reference_ids=("EVIDENCE",),
        capability_profile_ids=("PROFILE",),
    )
    profile = FilterCapabilityProfile(
        filter_capability_profile_id="PROFILE",
        filter_catalog_version_id="CATALOG",
        provider_surface_reference_id="PROVIDER",
        category_scope_reference_id="CATEGORY",
        geography_scope_reference_id="GEO",
        capability_state=FilterCapabilityState.EDITABLE,
        evidence_reference_ids=("EVIDENCE",),
    )
    return definition, profile


@pytest.mark.parametrize(
    ("field", "expected"),
    (
        ("provider_surface_reference_id", FilterSemanticExposureReason.PROVIDER_SURFACE_MISMATCH),
        ("category_scope_reference_id", FilterSemanticExposureReason.CATEGORY_SCOPE_MISMATCH),
        ("geography_scope_reference_id", FilterSemanticExposureReason.GEOGRAPHY_SCOPE_MISMATCH),
    ),
)
def test_runtime_semantic_mismatch_requires_exact_reason(field: str, expected: object) -> None:
    definition, profile = _semantic_fixture()
    values = {
        "provider_surface_reference_id": "PROVIDER",
        "category_scope_reference_id": "CATEGORY",
        "geography_scope_reference_id": "GEO",
        field: "WRONG",
    }
    result = evaluate_filter_semantic_exposure(
        FilterSemanticExposureRequest(
            filter_catalog_version_id="CATALOG",
            filter_definition=definition,
            capability_profile=profile,
            known_filter_definition_ids=("DEF_A",),
            **values,
        )
    )
    assert result.decision.value == "BLOCKED"
    assert expected in result.reason_codes


def test_runtime_global_scope_missing_scopes_blocks() -> None:
    definition, profile = _semantic_fixture()
    result = evaluate_filter_semantic_exposure(
        FilterSemanticExposureRequest(
            filter_catalog_version_id="CATALOG",
            filter_definition=definition,
            capability_profile=profile,
            provider_surface_reference_id="PROVIDER",
            category_scope_reference_id=None,
            geography_scope_reference_id=None,
            known_filter_definition_ids=("DEF_A",),
        )
    )
    assert result.decision.value == "BLOCKED"
    assert FilterSemanticExposureReason.CATEGORY_SCOPE_REQUIRED in result.reason_codes
    assert FilterSemanticExposureReason.GEOGRAPHY_SCOPE_REQUIRED in result.reason_codes


def test_runtime_multivalue_preserves_order_and_repetition() -> None:
    result = evaluate_multivalue_preservation(
        MultivaluePreservationRequest(
            filter_definition_id="DEF_MULTI",
            source_value_reference_ids=("A", "B", "A"),
            candidate_value_reference_ids=("A", "B", "A"),
        )
    )
    assert result.preserved_value_reference_ids == ("A", "B", "A")
    assert result.candidate_changed is False


def test_runtime_multivalue_collapse_is_blocked() -> None:
    result = evaluate_multivalue_preservation(
        MultivaluePreservationRequest(
            filter_definition_id="DEF_MULTI",
            source_value_reference_ids=("A", "B", "A"),
            candidate_value_reference_ids=("A", "B"),
        )
    )
    assert result.decision.value == "BLOCKED"
    assert "REPEATED_VALUE_COLLAPSE_DETECTED" in result.reason_codes


def test_runtime_range_normalization_preserves_decimal_boundaries() -> None:
    from mayak.modules.filter_catalog.contracts import FilterRangeDefinition

    definition = FilterRangeDefinition(
        filter_range_definition_id="RANGE",
        filter_definition_id="DEF_RANGE",
        unit_code="UNIT",
        lower_bound=Decimal("0"),
        upper_bound=Decimal("100"),
        lower_inclusive=True,
        upper_inclusive=False,
        step=Decimal("5"),
        evidence_reference_ids=("EVIDENCE",),
    )
    result = validate_range_value(
        RangeValueValidationRequest(
            filter_definition_id="DEF_RANGE",
            range_definition=definition,
            candidate_unit_code="UNIT",
            lower_value=Decimal("10"),
            upper_value=Decimal("20"),
            lower_inclusive=True,
            upper_inclusive=False,
            step_origin=Decimal("0"),
        )
    )
    assert result.decision.value == "VALID"
    assert result.lower_value == Decimal("10")
    assert result.upper_value == Decimal("20")
