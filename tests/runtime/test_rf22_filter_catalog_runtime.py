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
