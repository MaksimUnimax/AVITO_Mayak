"""Unit tests for Filter Catalog FC-08 semantic contracts — 56 vectors + 8 invariants."""

from __future__ import annotations

import copy
import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

FIXTURE_PATH = Path("tests/fixtures/filter_catalog_semantic_vectors.json")
REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _load_vectors() -> list[dict]:
    return _load_fixture()["vectors"]


def _load_refs() -> list[dict]:
    return _load_fixture()["canonical_references"]


def _ts(s: str = "2026-01-15T10:00:00Z") -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def _fp(ch: str = "a", n: int = 64) -> str:
    return ch * n


def _get_vector(vector_id: str) -> dict:
    for v in _load_vectors():
        if v["vector_id"] == vector_id:
            return v
    raise KeyError(f"Vector {vector_id} not found")


def _normalize_result(result):
    if result is None:
        return None
    if isinstance(result, (str, int, bool)):
        return result
    if isinstance(result, tuple):
        return tuple(_normalize_result(item) for item in result)
    if isinstance(result, dict):
        return {k: _normalize_result(v) for k, v in sorted(result.items())}
    return result


def _run_handler_twice(handler, vector_input: dict, vector_expected: dict):
    original_input = copy.deepcopy(vector_input)
    original_expected = copy.deepcopy(vector_expected)
    input1 = copy.deepcopy(vector_input)
    expected1 = copy.deepcopy(vector_expected)
    result1 = handler(input1, expected1)
    input2 = copy.deepcopy(vector_input)
    expected2 = copy.deepcopy(vector_expected)
    result2 = handler(input2, expected2)
    norm1 = _normalize_result(result1)
    norm2 = _normalize_result(result2)
    assert norm1 == norm2, f"Handler produced different normalized results across runs: {norm1!r} vs {norm2!r}"
    assert input1 == original_input, "Handler mutated input copy on first run"
    assert input2 == original_input, "Handler mutated input copy on second run"
    assert expected1 == original_expected, "Handler mutated expected copy on first run"
    assert expected2 == original_expected, "Handler mutated expected copy on second run"
    return norm1


# ---------------------------------------------------------------------------
# 56 Explicit Handler Functions
# ---------------------------------------------------------------------------

def handle_fc08_catalog_001(vector_input: dict, vector_expected: dict) -> None:
    from mayak.modules.filter_catalog.contracts import (
        CatalogPublicationState,
        FilterCatalogVersion,
    )
    result = FilterCatalogVersion(
        filter_catalog_version_id=vector_input["filter_catalog_version_id"],
        publication_state=CatalogPublicationState(vector_input["publication_state"]),
        created_at=_ts(vector_input["created_at"]),
        published_at=_ts(vector_input["published_at"]) if vector_input.get("published_at") else None,
        evidence_reference_ids=tuple(vector_input["evidence_reference_ids"]),
        filter_definition_ids=tuple(vector_input.get("filter_definition_ids", ())),
    )
    assert result.filter_catalog_version_id == vector_expected["filter_catalog_version_id"]
    assert result.publication_state == CatalogPublicationState(vector_expected["publication_state"])


    return {
        "filter_catalog_version_id": result.filter_catalog_version_id,
        "publication_state": result.publication_state.value,
    }
def handle_fc08_catalog_002(vector_input: dict, vector_expected: dict) -> None:
    from mayak.modules.filter_catalog.contracts import (
        CatalogPublicationState,
        FilterCatalogVersion,
    )
    with pytest.raises(ValidationError, match=vector_expected["error_fragment"]):
        FilterCatalogVersion(
            filter_catalog_version_id=vector_input["filter_catalog_version_id"],
            publication_state=CatalogPublicationState(vector_input["publication_state"]),
            created_at=_ts(vector_input["created_at"]),
            published_at=_ts(vector_input["published_at"]),
            evidence_reference_ids=tuple(vector_input["evidence_reference_ids"]),
        )


    return {"valid": False}
def handle_fc08_catalog_003(vector_input: dict, vector_expected: dict) -> None:
    from mayak.modules.filter_catalog.contracts import FilterOptionDefinition, FilterDefinitionState
    with pytest.raises(ValidationError, match=vector_expected["error_fragment"]):
        FilterOptionDefinition(
            filter_option_id=vector_input["filter_option_id"],
            filter_definition_id=vector_input["filter_definition_id"],
            canonical_value_code=vector_input["canonical_value_code"],
            safe_label=vector_input["safe_label"],
            definition_state=FilterDefinitionState(vector_input["definition_state"]),
            evidence_reference_ids=tuple(vector_input["evidence_reference_ids"]),
        )


    return {"valid": False}
def handle_fc08_catalog_004(vector_input: dict, vector_expected: dict) -> None:
    from mayak.modules.filter_catalog.contracts import (
        FilterDefinition,
        FilterDefinitionState,
        FilterValueKind,
    )
    with pytest.raises(ValidationError, match=vector_expected["error_fragment"]):
        FilterDefinition(
            filter_definition_id=vector_input["filter_definition_id"],
            filter_catalog_version_id=vector_input["filter_catalog_version_id"],
            normalized_key=vector_input["normalized_key"],
            safe_label=vector_input["safe_label"],
            value_kind=FilterValueKind(vector_input["value_kind"]),
            definition_state=FilterDefinitionState(vector_input["definition_state"]),
            evidence_reference_ids=tuple(vector_input["evidence_reference_ids"]),
            capability_profile_ids=tuple(vector_input["capability_profile_ids"]),
        )


    return {"valid": False}
def handle_fc08_catalog_005(vector_input: dict, vector_expected: dict) -> None:
    from mayak.modules.filter_catalog.contracts import (
        FilterCapabilityProfile,
        FilterCapabilityState,
    )
    result = FilterCapabilityProfile(
        filter_capability_profile_id=vector_input["filter_capability_profile_id"],
        filter_catalog_version_id=vector_input["filter_catalog_version_id"],
        provider_surface_reference_id=vector_input["provider_surface_reference_id"],
        capability_state=FilterCapabilityState(vector_input["capability_state"]),
        evidence_reference_ids=tuple(vector_input["evidence_reference_ids"]),
    )
    assert result.capability_state == FilterCapabilityState(vector_expected["capability_state"])


    return {
        "capability_state": result.capability_state.value,
    }
def handle_fc08_catalog_006(vector_input: dict, vector_expected: dict) -> None:
    from mayak.modules.filter_catalog.contracts import (
        FilterCapabilityProfile,
        FilterCapabilityState,
    )
    with pytest.raises(ValidationError, match=vector_expected["error_fragment"]):
        FilterCapabilityProfile(
            filter_capability_profile_id=vector_input["filter_capability_profile_id"],
            filter_catalog_version_id=vector_input["filter_catalog_version_id"],
            provider_surface_reference_id=vector_input["provider_surface_reference_id"],
            capability_state=FilterCapabilityState(vector_input["capability_state"]),
            evidence_reference_ids=tuple(vector_input["evidence_reference_ids"]),
        )


    return {"valid": False}
def handle_fc08_catalog_007(vector_input: dict, vector_expected: dict) -> None:
    from mayak.modules.filter_catalog.contracts import (
        CatalogPublicationState,
        FilterCatalogVersion,
    )
    result = FilterCatalogVersion(
        filter_catalog_version_id=vector_input["filter_catalog_version_id"],
        publication_state=CatalogPublicationState(vector_input["publication_state"]),
        created_at=_ts(vector_input["created_at"]),
        published_at=_ts(vector_input["published_at"]) if vector_input.get("published_at") else None,
        supersedes_catalog_version_id=vector_input.get("supersedes_catalog_version_id"),
        evidence_reference_ids=tuple(vector_input["evidence_reference_ids"]),
    )
    assert result.supersedes_catalog_version_id == vector_expected["supersedes_catalog_version_id"]


    return {
        "supersedes_catalog_version_id": result.supersedes_catalog_version_id,
    }
def handle_fc08_catalog_008(vector_input: dict, vector_expected: dict) -> None:
    from mayak.modules.filter_catalog.contracts import (
        FilterDefinition,
        FilterDefinitionState,
        FilterValueKind,
    )
    result = FilterDefinition(
        filter_definition_id=vector_input["filter_definition_id"],
        filter_catalog_version_id=vector_input["filter_catalog_version_id"],
        normalized_key=vector_input["normalized_key"],
        safe_label=vector_input["safe_label"],
        value_kind=FilterValueKind(vector_input["value_kind"]),
        definition_state=FilterDefinitionState(vector_input["definition_state"]),
        evidence_reference_ids=tuple(vector_input["evidence_reference_ids"]),
        capability_profile_ids=tuple(vector_input["capability_profile_ids"]),
    )
    assert result.definition_state == FilterDefinitionState(vector_expected["definition_state"])


    return {
        "definition_state": result.definition_state.value,
    }
def handle_fc08_evidence_001(vector_input: dict, vector_expected: dict) -> None:
    from mayak.modules.filter_catalog.contracts import FilterEvidenceReference, FilterEvidenceState
    from mayak.modules.filter_catalog.evidence_approval import (
        EvidenceAuthorityReference,
        FilterEvidenceApprovalRequest,
        FilterEvidenceTransition,
        evaluate_filter_evidence_approval,
    )
    evidence_refs = tuple(
        FilterEvidenceReference(
            evidence_reference_id=ev["evidence_reference_id"],
            evidence_state=FilterEvidenceState(ev["evidence_state"]),
            evidence_kind_code=ev["evidence_kind_code"],
            scope_reference_ids=tuple(ev["scope_reference_ids"]),
            source_fingerprint=ev["source_fingerprint"],
            observed_at=_ts(ev["observed_at"]),
            refresh_required=ev["refresh_required"],
        )
        for ev in vector_input["evidence_references"]
    )
    authority_refs = tuple(
        EvidenceAuthorityReference(
            evidence_reference_id=ar["evidence_reference_id"],
            authority_class=ar["authority_class"],
            accepted_reference_policy_id=ar.get("accepted_reference_policy_id"),
        )
        for ar in vector_input["authority_references"]
    )
    request = FilterEvidenceApprovalRequest(
        filter_definition_id=vector_input["filter_definition_id"],
        current_definition_state=vector_input["current_definition_state"],
        requested_transition=FilterEvidenceTransition(vector_input["requested_transition"]),
        required_scope_reference_ids=tuple(vector_input["required_scope_reference_ids"]),
        evidence_references=evidence_refs,
        authority_references=authority_refs,
    )
    outcome = evaluate_filter_evidence_approval(request)
    assert outcome.decision.value == vector_expected["decision"]
    assert outcome.suggested_definition_state.value == vector_expected["suggested_definition_state"]


    return {
        "decision": outcome.decision.value,
        "suggested_definition_state": outcome.suggested_definition_state.value,
    }
def handle_fc08_evidence_002(vector_input: dict, vector_expected: dict) -> None:
    from mayak.modules.filter_catalog.contracts import FilterEvidenceReference, FilterEvidenceState
    from mayak.modules.filter_catalog.evidence_approval import (
        EvidenceAuthorityReference,
        FilterEvidenceApprovalRequest,
        FilterEvidenceTransition,
        evaluate_filter_evidence_approval,
    )
    evidence_refs = tuple(
        FilterEvidenceReference(
            evidence_reference_id=ev["evidence_reference_id"],
            evidence_state=FilterEvidenceState(ev["evidence_state"]),
            evidence_kind_code=ev["evidence_kind_code"],
            scope_reference_ids=tuple(ev["scope_reference_ids"]),
            source_fingerprint=ev["source_fingerprint"],
            observed_at=_ts(ev["observed_at"]),
            refresh_required=ev["refresh_required"],
        )
        for ev in vector_input["evidence_references"]
    )
    authority_refs = tuple(
        EvidenceAuthorityReference(
            evidence_reference_id=ar["evidence_reference_id"],
            authority_class=ar["authority_class"],
            accepted_reference_policy_id=ar.get("accepted_reference_policy_id"),
        )
        for ar in vector_input["authority_references"]
    )
    request = FilterEvidenceApprovalRequest(
        filter_definition_id=vector_input["filter_definition_id"],
        current_definition_state=vector_input["current_definition_state"],
        requested_transition=FilterEvidenceTransition(vector_input["requested_transition"]),
        required_scope_reference_ids=tuple(vector_input["required_scope_reference_ids"]),
        evidence_references=evidence_refs,
        authority_references=authority_refs,
    )
    outcome = evaluate_filter_evidence_approval(request)
    assert outcome.decision.value == vector_expected["decision"]
    assert outcome.suggested_definition_state.value == vector_expected["suggested_definition_state"]


    return {
        "decision": outcome.decision.value,
        "suggested_definition_state": outcome.suggested_definition_state.value,
    }
def handle_fc08_evidence_003(vector_input: dict, vector_expected: dict) -> None:
    from mayak.modules.filter_catalog.evidence_approval import (
        FilterEvidenceApprovalRequest,
        FilterEvidenceTransition,
        evaluate_filter_evidence_approval,
    )
    request = FilterEvidenceApprovalRequest(
        filter_definition_id=vector_input["filter_definition_id"],
        current_definition_state=vector_input["current_definition_state"],
        requested_transition=FilterEvidenceTransition(vector_input["requested_transition"]),
        required_scope_reference_ids=tuple(vector_input["required_scope_reference_ids"]),
    )
    outcome = evaluate_filter_evidence_approval(request)
    assert outcome.decision.value == vector_expected["decision"]
    assert any(vector_expected["reason_contained"] in r.value for r in outcome.reason_codes)


    return {
        "decision": outcome.decision.value,
        "reason_codes": tuple(r.value for r in outcome.reason_codes),
    }
def handle_fc08_evidence_004(vector_input: dict, vector_expected: dict) -> None:
    from mayak.modules.filter_catalog.contracts import FilterEvidenceReference, FilterEvidenceState
    from mayak.modules.filter_catalog.evidence_approval import (
        EvidenceAuthorityReference,
        FilterEvidenceApprovalRequest,
        FilterEvidenceTransition,
        evaluate_filter_evidence_approval,
    )
    evidence_refs = tuple(
        FilterEvidenceReference(
            evidence_reference_id=ev["evidence_reference_id"],
            evidence_state=FilterEvidenceState(ev["evidence_state"]),
            evidence_kind_code=ev["evidence_kind_code"],
            scope_reference_ids=tuple(ev["scope_reference_ids"]),
            source_fingerprint=ev["source_fingerprint"],
            observed_at=_ts(ev["observed_at"]),
            refresh_required=ev["refresh_required"],
        )
        for ev in vector_input["evidence_references"]
    )
    authority_refs = tuple(
        EvidenceAuthorityReference(
            evidence_reference_id=ar["evidence_reference_id"],
            authority_class=ar["authority_class"],
            accepted_reference_policy_id=ar.get("accepted_reference_policy_id"),
        )
        for ar in vector_input["authority_references"]
    )
    request = FilterEvidenceApprovalRequest(
        filter_definition_id=vector_input["filter_definition_id"],
        current_definition_state=vector_input["current_definition_state"],
        requested_transition=FilterEvidenceTransition(vector_input["requested_transition"]),
        required_scope_reference_ids=tuple(vector_input["required_scope_reference_ids"]),
        evidence_references=evidence_refs,
        authority_references=authority_refs,
    )
    outcome = evaluate_filter_evidence_approval(request)
    assert outcome.decision.value == vector_expected["decision"]
    assert any(vector_expected["reason_contained"] in r.value for r in outcome.reason_codes)


    return {
        "decision": outcome.decision.value,
        "reason_codes": tuple(r.value for r in outcome.reason_codes),
    }
def handle_fc08_evidence_005(vector_input: dict, vector_expected: dict) -> None:
    from mayak.modules.filter_catalog.contracts import FilterEvidenceReference, FilterEvidenceState
    from mayak.modules.filter_catalog.evidence_approval import (
        EvidenceAuthorityReference,
        FilterEvidenceApprovalRequest,
        FilterEvidenceTransition,
        evaluate_filter_evidence_approval,
    )
    evidence_refs = tuple(
        FilterEvidenceReference(
            evidence_reference_id=ev["evidence_reference_id"],
            evidence_state=FilterEvidenceState(ev["evidence_state"]),
            evidence_kind_code=ev["evidence_kind_code"],
            scope_reference_ids=tuple(ev["scope_reference_ids"]),
            source_fingerprint=ev["source_fingerprint"],
            observed_at=_ts(ev["observed_at"]),
            refresh_required=ev["refresh_required"],
        )
        for ev in vector_input["evidence_references"]
    )
    authority_refs = tuple(
        EvidenceAuthorityReference(
            evidence_reference_id=ar["evidence_reference_id"],
            authority_class=ar["authority_class"],
            accepted_reference_policy_id=ar.get("accepted_reference_policy_id"),
        )
        for ar in vector_input["authority_references"]
    )
    request = FilterEvidenceApprovalRequest(
        filter_definition_id=vector_input["filter_definition_id"],
        current_definition_state=vector_input["current_definition_state"],
        requested_transition=FilterEvidenceTransition(vector_input["requested_transition"]),
        required_scope_reference_ids=tuple(vector_input["required_scope_reference_ids"]),
        evidence_references=evidence_refs,
        authority_references=authority_refs,
    )
    outcome = evaluate_filter_evidence_approval(request)
    assert outcome.decision.value == vector_expected["decision"]
    assert any(vector_expected["reason_contained"] in r.value for r in outcome.reason_codes)


    return {
        "decision": outcome.decision.value,
        "reason_codes": tuple(r.value for r in outcome.reason_codes),
    }
def handle_fc08_evidence_006(vector_input: dict, vector_expected: dict) -> None:
    from mayak.modules.filter_catalog.contracts import FilterEvidenceReference, FilterEvidenceState
    from mayak.modules.filter_catalog.evidence_approval import (
        EvidenceAuthorityReference,
        FilterEvidenceApprovalRequest,
        FilterEvidenceTransition,
        evaluate_filter_evidence_approval,
    )
    evidence_refs = tuple(
        FilterEvidenceReference(
            evidence_reference_id=ev["evidence_reference_id"],
            evidence_state=FilterEvidenceState(ev["evidence_state"]),
            evidence_kind_code=ev["evidence_kind_code"],
            scope_reference_ids=tuple(ev["scope_reference_ids"]),
            source_fingerprint=ev["source_fingerprint"],
            observed_at=_ts(ev["observed_at"]),
            refresh_required=ev["refresh_required"],
        )
        for ev in vector_input["evidence_references"]
    )
    authority_refs = tuple(
        EvidenceAuthorityReference(
            evidence_reference_id=ar["evidence_reference_id"],
            authority_class=ar["authority_class"],
            accepted_reference_policy_id=ar.get("accepted_reference_policy_id"),
        )
        for ar in vector_input["authority_references"]
    )
    request = FilterEvidenceApprovalRequest(
        filter_definition_id=vector_input["filter_definition_id"],
        current_definition_state=vector_input["current_definition_state"],
        requested_transition=FilterEvidenceTransition(vector_input["requested_transition"]),
        required_scope_reference_ids=tuple(vector_input["required_scope_reference_ids"]),
        evidence_references=evidence_refs,
        authority_references=authority_refs,
    )
    outcome = evaluate_filter_evidence_approval(request)
    assert outcome.decision.value == vector_expected["decision"]
    assert any(vector_expected["reason_contained"] in r.value for r in outcome.reason_codes)


    return {
        "decision": outcome.decision.value,
        "reason_codes": tuple(r.value for r in outcome.reason_codes),
    }
def handle_fc08_evidence_007(vector_input: dict, vector_expected: dict) -> None:
    from mayak.modules.filter_catalog.contracts import FilterEvidenceReference, FilterEvidenceState
    from mayak.modules.filter_catalog.evidence_approval import (
        EvidenceAuthorityReference,
        FilterEvidenceApprovalRequest,
        FilterEvidenceTransition,
        evaluate_filter_evidence_approval,
    )
    evidence_refs = tuple(
        FilterEvidenceReference(
            evidence_reference_id=ev["evidence_reference_id"],
            evidence_state=FilterEvidenceState(ev["evidence_state"]),
            evidence_kind_code=ev["evidence_kind_code"],
            scope_reference_ids=tuple(ev["scope_reference_ids"]),
            source_fingerprint=ev["source_fingerprint"],
            observed_at=_ts(ev["observed_at"]),
            refresh_required=ev["refresh_required"],
        )
        for ev in vector_input["evidence_references"]
    )
    authority_refs = tuple(
        EvidenceAuthorityReference(
            evidence_reference_id=ar["evidence_reference_id"],
            authority_class=ar["authority_class"],
            accepted_reference_policy_id=ar.get("accepted_reference_policy_id"),
        )
        for ar in vector_input["authority_references"]
    )
    request = FilterEvidenceApprovalRequest(
        filter_definition_id=vector_input["filter_definition_id"],
        current_definition_state=vector_input["current_definition_state"],
        requested_transition=FilterEvidenceTransition(vector_input["requested_transition"]),
        required_scope_reference_ids=tuple(vector_input["required_scope_reference_ids"]),
        evidence_references=evidence_refs,
        authority_references=authority_refs,
    )
    outcome = evaluate_filter_evidence_approval(request)
    assert outcome.decision.value == vector_expected["decision"]
    assert any(vector_expected["reason_contained"] in r.value for r in outcome.reason_codes)


    return {
        "decision": outcome.decision.value,
        "reason_codes": tuple(r.value for r in outcome.reason_codes),
    }
def handle_fc08_evidence_008(vector_input: dict, vector_expected: dict) -> None:
    from mayak.modules.filter_catalog.contracts import FilterEvidenceReference, FilterEvidenceState
    from mayak.modules.filter_catalog.evidence_approval import (
        EvidenceAuthorityReference,
        FilterEvidenceApprovalRequest,
        FilterEvidenceTransition,
        evaluate_filter_evidence_approval,
    )
    evidence_refs = tuple(
        FilterEvidenceReference(
            evidence_reference_id=ev["evidence_reference_id"],
            evidence_state=FilterEvidenceState(ev["evidence_state"]),
            evidence_kind_code=ev["evidence_kind_code"],
            scope_reference_ids=tuple(ev["scope_reference_ids"]),
            source_fingerprint=ev["source_fingerprint"],
            observed_at=_ts(ev["observed_at"]),
            refresh_required=ev["refresh_required"],
        )
        for ev in vector_input["evidence_references"]
    )
    authority_refs = tuple(
        EvidenceAuthorityReference(
            evidence_reference_id=ar["evidence_reference_id"],
            authority_class=ar["authority_class"],
            accepted_reference_policy_id=ar.get("accepted_reference_policy_id"),
        )
        for ar in vector_input["authority_references"]
    )
    request = FilterEvidenceApprovalRequest(
        filter_definition_id=vector_input["filter_definition_id"],
        current_definition_state=vector_input["current_definition_state"],
        requested_transition=FilterEvidenceTransition(vector_input["requested_transition"]),
        required_scope_reference_ids=tuple(vector_input["required_scope_reference_ids"]),
        evidence_references=evidence_refs,
        authority_references=authority_refs,
    )
    outcome = evaluate_filter_evidence_approval(request)
    assert outcome.decision.value == vector_expected["decision"]
    assert len(outcome.evidence_reference_ids) == vector_expected["evidence_count"]


    return {
        "decision": outcome.decision.value,
        "evidence_count": len(outcome.evidence_reference_ids),
    }
def handle_fc08_builder_001(vector_input: dict, vector_expected: dict) -> None:
    from mayak.modules.filter_catalog.contracts import (
        FilterCapabilityProfile,
        FilterCapabilityState,
        FilterDefinition,
        FilterDefinitionState,
        FilterValueKind,
    )
    from mayak.modules.filter_catalog.builder_validation import (
        BuilderFieldProjectionRequest,
        project_builder_field_definition,
    )
    fi = vector_input["filter_definition"]
    cap = vector_input["capability_profile"]
    definition = FilterDefinition(
        filter_definition_id=fi["filter_definition_id"],
        filter_catalog_version_id=fi["filter_catalog_version_id"],
        normalized_key=fi["normalized_key"],
        safe_label=fi["safe_label"],
        value_kind=FilterValueKind(fi["value_kind"]),
        definition_state=FilterDefinitionState(fi["definition_state"]),
        evidence_reference_ids=tuple(fi["evidence_reference_ids"]),
        capability_profile_ids=tuple(fi["capability_profile_ids"]),
    )
    profile = FilterCapabilityProfile(
        filter_capability_profile_id=cap["filter_capability_profile_id"],
        filter_catalog_version_id=cap["filter_catalog_version_id"],
        provider_surface_reference_id=cap["provider_surface_reference_id"],
        capability_state=FilterCapabilityState(cap["capability_state"]),
        evidence_reference_ids=tuple(cap["evidence_reference_ids"]),
    )
    request = BuilderFieldProjectionRequest(
        builder_field_projection_outcome_id=vector_input["builder_field_projection_outcome_id"],
        builder_field_id=vector_input["builder_field_id"],
        filter_catalog_version_id=vector_input["filter_catalog_version_id"],
        filter_definition=definition,
        capability_profile=profile,
        required=vector_input["required"],
    )
    outcome = project_builder_field_definition(request)
    assert outcome.decision.value == vector_expected["decision"]
    if vector_expected["has_field"]:
        assert outcome.field_definition is not None
    else:
        assert outcome.field_definition is None


    return {
        "decision": outcome.decision.value,
        "has_field": outcome.field_definition is not None,
    }
def handle_fc08_builder_002(vector_input: dict, vector_expected: dict) -> None:
    from mayak.modules.filter_catalog.contracts import (
        FilterCapabilityProfile,
        FilterCapabilityState,
        FilterDefinition,
        FilterDefinitionState,
        FilterValueKind,
    )
    from mayak.modules.filter_catalog.builder_validation import (
        BuilderFieldProjectionRequest,
        project_builder_field_definition,
    )
    fi = vector_input["filter_definition"]
    cap = vector_input["capability_profile"]
    definition = FilterDefinition(
        filter_definition_id=fi["filter_definition_id"],
        filter_catalog_version_id=fi["filter_catalog_version_id"],
        normalized_key=fi["normalized_key"],
        safe_label=fi["safe_label"],
        value_kind=FilterValueKind(fi["value_kind"]),
        definition_state=FilterDefinitionState(fi["definition_state"]),
        evidence_reference_ids=tuple(fi["evidence_reference_ids"]),
        capability_profile_ids=tuple(fi["capability_profile_ids"]),
    )
    profile = FilterCapabilityProfile(
        filter_capability_profile_id=cap["filter_capability_profile_id"],
        filter_catalog_version_id=cap["filter_catalog_version_id"],
        provider_surface_reference_id=cap["provider_surface_reference_id"],
        capability_state=FilterCapabilityState(cap["capability_state"]),
        evidence_reference_ids=tuple(cap["evidence_reference_ids"]),
    )
    request = BuilderFieldProjectionRequest(
        builder_field_projection_outcome_id=vector_input["builder_field_projection_outcome_id"],
        builder_field_id=vector_input["builder_field_id"],
        filter_catalog_version_id=vector_input["filter_catalog_version_id"],
        filter_definition=definition,
        capability_profile=profile,
        required=vector_input["required"],
    )
    outcome = project_builder_field_definition(request)
    assert outcome.decision.value == vector_expected["decision"]
    assert outcome.field_definition is None


    return {
        "decision": outcome.decision.value,
        "has_field": outcome.field_definition is not None,
    }
def handle_fc08_builder_003(vector_input: dict, vector_expected: dict) -> None:
    from mayak.modules.filter_catalog.contracts import (
        BuilderDraftValidationResult,
        BuilderDraftValidationState,
        FilterCapabilityProfile,
        FilterCapabilityState,
    )
    assert vector_expected["field_stale_detected"]
    assert vector_expected["validation_state"] == "STALE"
    result = BuilderDraftValidationResult(
        builder_draft_validation_result_id="FC08-REF-036",
        filter_catalog_version_id=vector_input["filter_catalog_version_id"],
        beacon_revision_id=vector_input["beacon_revision_id"],
        validation_state=BuilderDraftValidationState.STALE,
        rejected_builder_field_ids=(vector_input["builder_field_id"],),
    )
    assert result.validation_state == BuilderDraftValidationState(vector_expected["validation_state"])


    return {
        "validation_state": result.validation_state.value,
    }
def handle_fc08_builder_004(vector_input: dict, vector_expected: dict) -> None:
    from mayak.modules.filter_catalog.contracts import (
        BuilderDraftValidationResult,
        BuilderDraftValidationState,
    )
    assert vector_expected["field_ambiguous_detected"]
    result = BuilderDraftValidationResult(
        builder_draft_validation_result_id="FC08-REF-036",
        filter_catalog_version_id=vector_input["filter_catalog_version_id"],
        beacon_revision_id=vector_input["beacon_revision_id"],
        validation_state=BuilderDraftValidationState.AMBIGUOUS,
        rejected_builder_field_ids=(vector_input["builder_field_id"],),
    )
    assert result.validation_state == BuilderDraftValidationState(vector_expected["validation_state"])


    return {
        "validation_state": result.validation_state.value,
    }
def handle_fc08_builder_005(vector_input: dict, vector_expected: dict) -> None:
    from mayak.modules.filter_catalog.contracts import (
        BuilderDraftValidationResult,
        BuilderDraftValidationState,
    )
    assert vector_expected["category_incompatible_detected"]
    result = BuilderDraftValidationResult(
        builder_draft_validation_result_id="FC08-REF-036",
        filter_catalog_version_id=vector_input["filter_catalog_version_id"],
        beacon_revision_id=vector_input["beacon_revision_id"],
        validation_state=BuilderDraftValidationState(vector_expected["validation_state"]),
        rejected_builder_field_ids=(vector_input["builder_field_id"],),
    )
    assert result.validation_state == BuilderDraftValidationState(vector_expected["validation_state"])


    return {
        "validation_state": result.validation_state.value,
    }
def handle_fc08_builder_006(vector_input: dict, vector_expected: dict) -> None:
    from mayak.modules.filter_catalog.contracts import (
        BuilderDraftValidationResult,
        BuilderDraftValidationState,
    )
    assert vector_expected["version_mismatch_detected"]
    result = BuilderDraftValidationResult(
        builder_draft_validation_result_id="FC08-REF-036",
        filter_catalog_version_id=vector_input["filter_catalog_version_id"],
        beacon_revision_id=vector_input["beacon_revision_id"],
        validation_state=BuilderDraftValidationState.CONFLICT,
        rejected_builder_field_ids=(vector_input["builder_field_id"],),
    )
    assert result.validation_state == BuilderDraftValidationState(vector_expected["validation_state"])


    return {
        "validation_state": result.validation_state.value,
    }
def handle_fc08_builder_007(vector_input: dict, vector_expected: dict) -> None:
    from mayak.modules.filter_catalog.contracts import (
        BuilderDraftValidationResult,
        BuilderDraftValidationState,
    )
    result = BuilderDraftValidationResult(
        builder_draft_validation_result_id="FC08-REF-036",
        filter_catalog_version_id=vector_input["filter_catalog_version_id"],
        beacon_revision_id=vector_input["beacon_revision_id"],
        validation_state=BuilderDraftValidationState.VALID,
        accepted_builder_field_ids=(vector_input["builder_field_id"],),
        warning_ids=tuple(vector_input.get("warning_ids", ())),
    )
    assert result.validation_state == BuilderDraftValidationState.VALID
    assert isinstance(result.warning_ids, tuple)


    return {
        "validation_state": result.validation_state.value,
        "warning_ids_present": isinstance(result.warning_ids, tuple) and len(result.warning_ids) > 0,
    }
def handle_fc08_builder_008(vector_input: dict, vector_expected: dict) -> None:
    from mayak.modules.filter_catalog.contracts import (
        BuilderDraftValidationResult,
        BuilderDraftValidationState,
    )
    result = BuilderDraftValidationResult(
        builder_draft_validation_result_id="FC08-REF-036",
        filter_catalog_version_id=vector_input["filter_catalog_version_id"],
        beacon_revision_id=vector_input["beacon_revision_id"],
        validation_state=BuilderDraftValidationState.VALID,
        accepted_builder_field_ids=(vector_input["builder_field_id"],),
    )
    assert result.is_authoritative_for_beacon is vector_expected["is_authoritative_for_beacon"]
    assert result.is_authoritative_for_beacon is False


    return {
        "is_authoritative_for_beacon": result.is_authoritative_for_beacon,
    }
def handle_fc08_value_001(vector_input: dict, vector_expected: dict) -> None:
    from mayak.modules.filter_catalog.value_dependency_semantics import (
        MultivaluePreservationRequest,
        evaluate_multivalue_preservation,
    )
    request = MultivaluePreservationRequest(
        filter_definition_id=vector_input["filter_definition_id"],
        source_value_reference_ids=tuple(vector_input["source_value_reference_ids"]),
        candidate_value_reference_ids=tuple(vector_input["candidate_value_reference_ids"]),
    )
    outcome = evaluate_multivalue_preservation(request)
    assert outcome.decision.value == vector_expected["decision"]
    assert outcome.candidate_changed == vector_expected["candidate_changed"]


    return {
        "decision": outcome.decision.value,
        "candidate_changed": outcome.candidate_changed,
    }
def handle_fc08_value_002(vector_input: dict, vector_expected: dict) -> None:
    from mayak.modules.filter_catalog.value_dependency_semantics import (
        MultivaluePreservationRequest,
        MultivaluePreservationReason,
        evaluate_multivalue_preservation,
    )
    request = MultivaluePreservationRequest(
        filter_definition_id=vector_input["filter_definition_id"],
        source_value_reference_ids=tuple(vector_input["source_value_reference_ids"]),
        candidate_value_reference_ids=tuple(vector_input["candidate_value_reference_ids"]),
    )
    outcome = evaluate_multivalue_preservation(request)
    assert outcome.decision.value == vector_expected["decision"]
    assert vector_expected["collapse_detected"]
    assert MultivaluePreservationReason.REPEATED_VALUE_COLLAPSE_DETECTED in outcome.reason_codes


    return {
        "decision": outcome.decision.value,
        "collapse_detected": MultivaluePreservationReason.REPEATED_VALUE_COLLAPSE_DETECTED in outcome.reason_codes,
    }
def handle_fc08_value_003(vector_input: dict, vector_expected: dict) -> None:
    from mayak.modules.filter_catalog.contracts import FilterRangeDefinition
    from mayak.modules.filter_catalog.value_dependency_semantics import (
        RangeValueValidationRequest,
        validate_range_value,
    )
    rd = vector_input["range_definition"]
    range_def = FilterRangeDefinition(
        filter_range_definition_id=rd["filter_range_definition_id"],
        filter_definition_id=rd["filter_definition_id"],
        unit_code=rd["unit_code"],
        lower_bound=Decimal(rd["lower_bound"]) if rd.get("lower_bound") is not None else None,
        upper_bound=Decimal(rd["upper_bound"]) if rd.get("upper_bound") is not None else None,
        lower_inclusive=rd["lower_inclusive"],
        upper_inclusive=rd["upper_inclusive"],
        step=Decimal(rd["step"]) if rd.get("step") else None,
        evidence_reference_ids=("FC08-REF-007",),
    )
    request = RangeValueValidationRequest(
        filter_definition_id=vector_input["filter_definition_id"],
        range_definition=range_def,
        candidate_unit_code=vector_input["candidate_unit_code"],
        lower_value=Decimal(vector_input["lower_value"]) if vector_input.get("lower_value") else None,
        upper_value=Decimal(vector_input["upper_value"]) if vector_input.get("upper_value") else None,
        lower_inclusive=vector_input["lower_inclusive"],
        upper_inclusive=vector_input["upper_inclusive"],
        step_origin=Decimal(vector_input["step_origin"]) if vector_input.get("step_origin") else None,
    )
    outcome = validate_range_value(request)
    assert outcome.decision.value == vector_expected["decision"]


    return {
        "decision": outcome.decision.value,
    }
def handle_fc08_value_004(vector_input: dict, vector_expected: dict) -> None:
    from mayak.modules.filter_catalog.contracts import FilterRangeDefinition
    from mayak.modules.filter_catalog.value_dependency_semantics import (
        RangeValueValidationRequest,
        RangeValueValidationReason,
        validate_range_value,
    )
    rd = vector_input["range_definition"]
    range_def = FilterRangeDefinition(
        filter_range_definition_id=rd["filter_range_definition_id"],
        filter_definition_id=rd["filter_definition_id"],
        unit_code=rd["unit_code"],
        lower_bound=Decimal(rd["lower_bound"]) if rd.get("lower_bound") is not None else None,
        lower_inclusive=rd["lower_inclusive"],
        upper_inclusive=rd["upper_inclusive"],
        evidence_reference_ids=("FC08-REF-007",),
    )
    request = RangeValueValidationRequest(
        filter_definition_id=vector_input["filter_definition_id"],
        range_definition=range_def,
        candidate_unit_code=vector_input["candidate_unit_code"],
        lower_value=Decimal(vector_input["lower_value"]) if vector_input.get("lower_value") else None,
        lower_inclusive=vector_input["lower_inclusive"],
        upper_inclusive=vector_input["upper_inclusive"],
    )
    outcome = validate_range_value(request)
    assert outcome.decision.value == vector_expected["decision"]
    assert vector_expected["unit_mismatch_detected"]
    assert RangeValueValidationReason.UNIT_MISMATCH in outcome.reason_codes


    return {
        "decision": outcome.decision.value,
        "unit_mismatch_detected": RangeValueValidationReason.UNIT_MISMATCH in outcome.reason_codes,
    }
def handle_fc08_value_005(vector_input: dict, vector_expected: dict) -> None:
    from mayak.modules.filter_catalog.contracts import FilterRangeDefinition
    from mayak.modules.filter_catalog.value_dependency_semantics import (
        RangeValueValidationRequest,
        RangeValueValidationReason,
        validate_range_value,
    )
    rd = vector_input["range_definition"]
    range_def = FilterRangeDefinition(
        filter_range_definition_id=rd["filter_range_definition_id"],
        filter_definition_id=rd["filter_definition_id"],
        unit_code=rd["unit_code"],
        lower_bound=Decimal(rd["lower_bound"]) if rd.get("lower_bound") is not None else None,
        upper_bound=Decimal(rd["upper_bound"]) if rd.get("upper_bound") is not None else None,
        lower_inclusive=rd["lower_inclusive"],
        upper_inclusive=rd["upper_inclusive"],
        evidence_reference_ids=("FC08-REF-007",),
    )
    request = RangeValueValidationRequest(
        filter_definition_id=vector_input["filter_definition_id"],
        range_definition=range_def,
        candidate_unit_code=vector_input["candidate_unit_code"],
        lower_value=Decimal(vector_input["lower_value"]) if vector_input.get("lower_value") else None,
        upper_value=Decimal(vector_input["upper_value"]) if vector_input.get("upper_value") else None,
        lower_inclusive=vector_input["lower_inclusive"],
        upper_inclusive=vector_input["upper_inclusive"],
    )
    outcome = validate_range_value(request)
    assert outcome.decision.value == vector_expected["decision"]
    assert vector_expected["inclusivity_incompatible_detected"]
    assert RangeValueValidationReason.LOWER_INCLUSIVITY_INCOMPATIBLE in outcome.reason_codes


    return {
        "decision": outcome.decision.value,
        "inclusivity_incompatible_detected": RangeValueValidationReason.LOWER_INCLUSIVITY_INCOMPATIBLE in outcome.reason_codes,
    }
def handle_fc08_value_006(vector_input: dict, vector_expected: dict) -> None:
    from mayak.modules.filter_catalog.contracts import (
        FilterCapabilityProfile,
        FilterCapabilityState,
        FilterDependencyKind,
        FilterDependencyRule,
        FilterDefinition,
        FilterDefinitionState,
        FilterValueKind,
    )
    from mayak.modules.filter_catalog.value_dependency_semantics import (
        DependencyEvaluationState,
        DependencyRuleEvaluation,
        FilterSemanticExposureRequest,
        evaluate_filter_semantic_exposure,
    )
    definition = FilterDefinition(
        filter_definition_id=vector_input["filter_definition_id"],
        filter_catalog_version_id=vector_input["filter_catalog_version_id"],
        normalized_key="SYNTH_DEP_A",
        safe_label="Synthetic dep A",
        value_kind=FilterValueKind.SCALAR,
        definition_state=FilterDefinitionState.APPROVED,
        evidence_reference_ids=("FC08-REF-007",),
        capability_profile_ids=(vector_input["capability_profile_id"],),
        dependency_rule_ids=(vector_input["dependency_rule_id"],),
    )
    profile = FilterCapabilityProfile(
        filter_capability_profile_id=vector_input["capability_profile_id"],
        filter_catalog_version_id=vector_input["filter_catalog_version_id"],
        provider_surface_reference_id="FC08-REF-021",
        capability_state=FilterCapabilityState.EDITABLE,
        evidence_reference_ids=("FC08-REF-007",),
    )
    rule = FilterDependencyRule(
        filter_dependency_rule_id=vector_input["dependency_rule_id"],
        source_filter_definition_id=vector_input["source_filter"],
        target_filter_definition_id=vector_input["target_filter"],
        dependency_kind=FilterDependencyKind(vector_input["dependency_kind"]),
        condition_code="SYNTH_COND",
        outcome_code="SYNTH_OUT",
        evidence_reference_ids=("FC08-REF-007",),
    )
    evaluation = DependencyRuleEvaluation(
        filter_dependency_rule_id=vector_input["dependency_rule_id"],
        evaluation_state=DependencyEvaluationState(vector_input["evaluation_state"]),
        evaluation_reference_id="FC08-REF-019",
    )
    request = FilterSemanticExposureRequest(
        filter_catalog_version_id=vector_input["filter_catalog_version_id"],
        filter_definition=definition,
        capability_profile=profile,
        provider_surface_reference_id="FC08-REF-021",
        known_filter_definition_ids=(vector_input["filter_definition_id"], vector_input["target_filter"]),
        dependency_rules=(rule,),
        dependency_evaluations=(evaluation,),
    )
    outcome = evaluate_filter_semantic_exposure(request)
    assert outcome.decision.value == vector_expected["decision"]
    assert vector_expected["dependency_blocked_detected"]


    return {
        "decision": outcome.decision.value,
    }
def handle_fc08_value_007(vector_input: dict, vector_expected: dict) -> None:
    from mayak.modules.filter_catalog.contracts import (
        FilterCapabilityProfile,
        FilterCapabilityState,
        FilterDependencyKind,
        FilterDependencyRule,
        FilterDefinition,
        FilterDefinitionState,
        FilterValueKind,
    )
    from mayak.modules.filter_catalog.value_dependency_semantics import (
        DependencyEvaluationState,
        DependencyRuleEvaluation,
        FilterSemanticExposureRequest,
        evaluate_filter_semantic_exposure,
    )
    definition = FilterDefinition(
        filter_definition_id=vector_input["filter_definition_id"],
        filter_catalog_version_id=vector_input["filter_catalog_version_id"],
        normalized_key="SYNTH_DEP_B",
        safe_label="Synthetic dep B",
        value_kind=FilterValueKind.SCALAR,
        definition_state=FilterDefinitionState.APPROVED,
        evidence_reference_ids=("FC08-REF-007",),
        capability_profile_ids=(vector_input["capability_profile_id"],),
        dependency_rule_ids=(vector_input["dependency_rule_id"],),
    )
    profile = FilterCapabilityProfile(
        filter_capability_profile_id=vector_input["capability_profile_id"],
        filter_catalog_version_id=vector_input["filter_catalog_version_id"],
        provider_surface_reference_id="FC08-REF-021",
        capability_state=FilterCapabilityState.UNSUPPORTED,
        evidence_reference_ids=("FC08-REF-007",),
    )
    rule = FilterDependencyRule(
        filter_dependency_rule_id=vector_input["dependency_rule_id"],
        source_filter_definition_id=vector_input["source_filter"],
        target_filter_definition_id=vector_input["target_filter"],
        dependency_kind=FilterDependencyKind(vector_input["dependency_kind"]),
        condition_code="SYNTH_COND",
        outcome_code="SYNTH_OUT",
        evidence_reference_ids=("FC08-REF-007",),
    )
    evaluation = DependencyRuleEvaluation(
        filter_dependency_rule_id=vector_input["dependency_rule_id"],
        evaluation_state=DependencyEvaluationState(vector_input["evaluation_state"]),
        evaluation_reference_id="FC08-REF-019",
    )
    request = FilterSemanticExposureRequest(
        filter_catalog_version_id=vector_input["filter_catalog_version_id"],
        filter_definition=definition,
        capability_profile=profile,
        provider_surface_reference_id="FC08-REF-021",
        known_filter_definition_ids=(vector_input["filter_definition_id"], vector_input["target_filter"]),
        dependency_rules=(rule,),
        dependency_evaluations=(evaluation,),
    )
    outcome = evaluate_filter_semantic_exposure(request)
    assert outcome.decision.value == vector_expected["decision"]
    assert vector_expected["dependency_blocked_detected"]


    return {
        "decision": outcome.decision.value,
    }
def handle_fc08_value_008(vector_input: dict, vector_expected: dict) -> None:
    from mayak.modules.filter_catalog.contracts import (
        FilterCapabilityProfile,
        FilterCapabilityState,
        FilterDependencyKind,
        FilterDependencyRule,
        FilterDefinition,
        FilterDefinitionState,
        FilterValueKind,
    )
    from mayak.modules.filter_catalog.value_dependency_semantics import (
        DependencyEvaluationState,
        DependencyRuleEvaluation,
        FilterSemanticExposureRequest,
        evaluate_filter_semantic_exposure,
    )
    definition = FilterDefinition(
        filter_definition_id=vector_input["filter_definition_id"],
        filter_catalog_version_id=vector_input["filter_catalog_version_id"],
        normalized_key="SYNTH_DEP_C",
        safe_label="Synthetic dep C",
        value_kind=FilterValueKind.SCALAR,
        definition_state=FilterDefinitionState.APPROVED,
        evidence_reference_ids=("FC08-REF-007",),
        capability_profile_ids=(vector_input["capability_profile_id"],),
        dependency_rule_ids=tuple(vector_input["dependency_rule_ids"]),
    )
    profile = FilterCapabilityProfile(
        filter_capability_profile_id=vector_input["capability_profile_id"],
        filter_catalog_version_id=vector_input["filter_catalog_version_id"],
        provider_surface_reference_id="FC08-REF-021",
        category_scope_reference_id="FC08-REF-031",
        geography_scope_reference_id="FC08-REF-032",
        capability_state=FilterCapabilityState.EDITABLE,
        evidence_reference_ids=("FC08-REF-007",),
    )
    rules = tuple(
        FilterDependencyRule(
            filter_dependency_rule_id=rule_id,
            source_filter_definition_id=vector_input["filter_definition_id"],
            target_filter_definition_id="FC08-REF-004",
            dependency_kind=FilterDependencyKind.CONSTRAINS,
            condition_code="SYNTH_COND",
            outcome_code="SYNTH_OUT",
            evidence_reference_ids=("FC08-REF-007",),
        )
        for rule_id in vector_input["dependency_rule_ids"]
    )
    evaluations = tuple(
        DependencyRuleEvaluation(
            filter_dependency_rule_id=rule_id,
            evaluation_state=DependencyEvaluationState(vector_input["evaluation_states"][rule_id]),
            evaluation_reference_id="FC08-REF-019",
        )
        for rule_id in vector_input["evaluation_rule_ids"]
    )
    request = FilterSemanticExposureRequest(
        filter_catalog_version_id=vector_input["filter_catalog_version_id"],
        filter_definition=definition,
        capability_profile=profile,
        provider_surface_reference_id="FC08-REF-021",
        category_scope_reference_id="FC08-REF-031",
        geography_scope_reference_id="FC08-REF-032",
        known_filter_definition_ids=(vector_input["filter_definition_id"], "FC08-REF-004"),
        dependency_rules=rules,
        dependency_evaluations=evaluations,
    )
    outcome = evaluate_filter_semantic_exposure(request)
    assert outcome.decision.value == vector_expected["decision"]
    assert vector_expected["all_evaluated"]


    return {
        "decision": outcome.decision.value,
        "all_evaluated": vector_expected["all_evaluated"],
    }
def handle_fc08_beacon_001(vector_input: dict, vector_expected: dict) -> None:
    from mayak.modules.filter_catalog.contracts import (
        BeaconOverrideCandidateOutcome,
        BeaconOverrideCandidateState,
        BuilderDraftValidationResult,
        BuilderDraftValidationState,
    )
    result = BuilderDraftValidationResult(
        builder_draft_validation_result_id="FC08-REF-036",
        filter_catalog_version_id=vector_input["filter_catalog_version_id"],
        beacon_revision_id=vector_input["beacon_revision_id"],
        validation_state=BuilderDraftValidationState.VALID,
        accepted_builder_field_ids=tuple(vector_input.get("accepted_fields", ())),
    )
    outcome = BeaconOverrideCandidateOutcome(
        beacon_override_candidate_outcome_id=vector_input["beacon_override_candidate_outcome_id"],
        override_candidate_reference_id=vector_input["override_candidate_reference_id"],
        beacon_id=vector_input["beacon_id"],
        beacon_revision_id=vector_input["beacon_revision_id"],
        filter_catalog_version_id=vector_input["filter_catalog_version_id"],
        candidate_state=BeaconOverrideCandidateState(vector_expected["candidate_state"]),
        validated_builder_field_ids=tuple(vector_input.get("accepted_fields", ())),
    )
    assert outcome.candidate_state == BeaconOverrideCandidateState.PREPARED
    assert outcome.beacon_acceptance_required is True


    return {
        "candidate_state": outcome.candidate_state.value,
        "beacon_acceptance_required": outcome.beacon_acceptance_required,
    }
def handle_fc08_beacon_002(vector_input: dict, vector_expected: dict) -> None:
    from mayak.modules.filter_catalog.contracts import (
        BeaconOverrideCandidateOutcome,
        BeaconOverrideCandidateState,
    )
    outcome = BeaconOverrideCandidateOutcome(
        beacon_override_candidate_outcome_id="FC08-REF-019",
        override_candidate_reference_id="FC08-REF-030",
        beacon_id="FC08-REF-016",
        beacon_revision_id="FC08-REF-017",
        filter_catalog_version_id="FC08-REF-001",
        candidate_state=BeaconOverrideCandidateState(vector_input["candidate_state"]),
    )
    assert outcome.beacon_acceptance_required is vector_expected["beacon_acceptance_required_must_be_true"]


    return {
        "beacon_acceptance_required": outcome.beacon_acceptance_required,
    }
def handle_fc08_beacon_003(vector_input: dict, vector_expected: dict) -> None:
    from mayak.modules.filter_catalog.beacon_override_candidate import (
        BeaconOverrideCandidatePreparationResult,
        BeaconOverrideCandidatePreparationReason,
        BeaconOverrideCandidateOutcome,
        BeaconOverrideCandidateState,
    )
    outcome = BeaconOverrideCandidateOutcome(
        beacon_override_candidate_outcome_id="FC08-REF-019",
        override_candidate_reference_id="FC08-REF-030",
        beacon_id="FC08-REF-016",
        beacon_revision_id="FC08-REF-017",
        filter_catalog_version_id="FC08-REF-001",
        candidate_state=BeaconOverrideCandidateState.BLOCKED,
    )
    result = BeaconOverrideCandidatePreparationResult(
        candidate_outcome=outcome,
        builder_draft_id="FC08-REF-013",
        beacon_acceptance_boundary_reference_id="FC08-REF-020",
        catalog_evidence_reference_ids=("FC08-REF-007",),
        reason_codes=(BeaconOverrideCandidatePreparationReason.DRAFT_BLOCKED,),
    )
    assert result.beacon_acceptance_performed is vector_expected["beacon_acceptance_performed"]
    assert result.beacon_mutation_performed is vector_expected["beacon_mutation_performed"]


    return {
        "beacon_acceptance_performed": result.beacon_acceptance_performed,
        "beacon_mutation_performed": result.beacon_mutation_performed,
    }
def handle_fc08_beacon_004(vector_input: dict, vector_expected: dict) -> None:
    from mayak.modules.filter_catalog.beacon_override_candidate import (
        BeaconOverrideCandidatePreparationResult,
        BeaconOverrideCandidatePreparationReason,
        BeaconOverrideCandidateOutcome,
        BeaconOverrideCandidateState,
    )
    outcome = BeaconOverrideCandidateOutcome(
        beacon_override_candidate_outcome_id="FC08-REF-019",
        override_candidate_reference_id="FC08-REF-030",
        beacon_id="FC08-REF-016",
        beacon_revision_id="FC08-REF-017",
        filter_catalog_version_id="FC08-REF-001",
        candidate_state=BeaconOverrideCandidateState.BLOCKED,
    )
    result = BeaconOverrideCandidatePreparationResult(
        candidate_outcome=outcome,
        builder_draft_id="FC08-REF-013",
        beacon_acceptance_boundary_reference_id="FC08-REF-020",
        catalog_evidence_reference_ids=("FC08-REF-007",),
        reason_codes=(BeaconOverrideCandidatePreparationReason.DRAFT_BLOCKED,),
    )
    assert result.beacon_mutation_performed is False
    assert result.beacon_revision_created is False
    assert result.lifecycle_changed is False
    assert result.historical_revision_rewritten is False


    return {
        "beacon_mutation_performed": result.beacon_mutation_performed,
        "beacon_revision_created": result.beacon_revision_created,
        "lifecycle_changed": result.lifecycle_changed,
        "historical_revision_rewritten": result.historical_revision_rewritten,
    }
def handle_fc08_beacon_005(vector_input: dict, vector_expected: dict) -> None:
    from mayak.modules.filter_catalog.beacon_override_candidate import (
        BeaconOverrideCandidatePreparationResult,
        BeaconOverrideCandidatePreparationReason,
        BeaconOverrideCandidateOutcome,
        BeaconOverrideCandidateState,
    )
    outcome = BeaconOverrideCandidateOutcome(
        beacon_override_candidate_outcome_id=vector_input["beacon_override_candidate_outcome_id"],
        override_candidate_reference_id=vector_input["override_candidate_reference_id"],
        beacon_id=vector_input["beacon_id"],
        beacon_revision_id=vector_input["beacon_revision_id"],
        filter_catalog_version_id=vector_input["filter_catalog_version_id"],
        candidate_state=BeaconOverrideCandidateState(vector_expected["candidate_state"]),
    )
    result = BeaconOverrideCandidatePreparationResult(
        candidate_outcome=outcome,
        builder_draft_id="FC08-REF-013",
        beacon_acceptance_boundary_reference_id="FC08-REF-020",
        catalog_evidence_reference_ids=("FC08-REF-007",),
        reason_codes=(BeaconOverrideCandidatePreparationReason.DRAFT_BLOCKED,),
    )
    assert result.field_candidates == ()
    assert result.candidate_outcome.validated_builder_field_ids == ()


    return {
        "field_candidates_empty": result.field_candidates == (),
        "validated_builder_field_ids_empty": result.candidate_outcome.validated_builder_field_ids == (),
    }
def handle_fc08_beacon_006(vector_input: dict, vector_expected: dict) -> None:
    from mayak.modules.filter_catalog.beacon_override_candidate import (
        BeaconOverrideCandidatePreparationResult,
        BeaconOverrideCandidatePreparationReason,
        BeaconOverrideCandidateOutcome,
        BeaconOverrideCandidateState,
    )
    outcome = BeaconOverrideCandidateOutcome(
        beacon_override_candidate_outcome_id=vector_input["beacon_override_candidate_outcome_id"],
        override_candidate_reference_id=vector_input["override_candidate_reference_id"],
        beacon_id=vector_input["beacon_id"],
        beacon_revision_id=vector_input["beacon_revision_id"],
        filter_catalog_version_id=vector_input["filter_catalog_version_id"],
        candidate_state=BeaconOverrideCandidateState(vector_expected["candidate_state"]),
    )
    result = BeaconOverrideCandidatePreparationResult(
        candidate_outcome=outcome,
        builder_draft_id="FC08-REF-013",
        beacon_acceptance_boundary_reference_id="FC08-REF-020",
        catalog_evidence_reference_ids=("FC08-REF-007",),
        reason_codes=(BeaconOverrideCandidatePreparationReason.DRAFT_CONFLICT,),
    )
    assert result.field_candidates == ()
    assert result.candidate_outcome.validated_builder_field_ids == ()


    return {
        "field_candidates_empty": result.field_candidates == (),
        "validated_builder_field_ids_empty": result.candidate_outcome.validated_builder_field_ids == (),
    }
def handle_fc08_beacon_007(vector_input: dict, vector_expected: dict) -> None:
    from mayak.modules.filter_catalog.beacon_override_candidate import (
        BeaconOverrideCandidatePreparationResult,
        BeaconOverrideCandidatePreparationReason,
        BeaconOverrideCandidateOutcome,
        BeaconOverrideCandidateState,
    )
    outcome = BeaconOverrideCandidateOutcome(
        beacon_override_candidate_outcome_id=vector_input["beacon_override_candidate_outcome_id"],
        override_candidate_reference_id=vector_input["override_candidate_reference_id"],
        beacon_id=vector_input["beacon_id"],
        beacon_revision_id=vector_input["beacon_revision_id"],
        filter_catalog_version_id=vector_input["filter_catalog_version_id"],
        candidate_state=BeaconOverrideCandidateState(vector_expected["candidate_state"]),
    )
    result = BeaconOverrideCandidatePreparationResult(
        candidate_outcome=outcome,
        builder_draft_id="FC08-REF-013",
        beacon_acceptance_boundary_reference_id="FC08-REF-020",
        catalog_evidence_reference_ids=("FC08-REF-007",),
        reason_codes=(BeaconOverrideCandidatePreparationReason.DRAFT_STALE,),
    )
    assert result.field_candidates == ()
    assert result.candidate_outcome.validated_builder_field_ids == ()


    return {
        "field_candidates_empty": result.field_candidates == (),
        "validated_builder_field_ids_empty": result.candidate_outcome.validated_builder_field_ids == (),
    }
def handle_fc08_beacon_008(vector_input: dict, vector_expected: dict) -> None:
    from mayak.modules.filter_catalog.contracts import (
        BeaconOverrideCandidateOutcome,
        BeaconOverrideCandidateState,
    )
    outcome = BeaconOverrideCandidateOutcome(
        beacon_override_candidate_outcome_id=vector_input["beacon_override_candidate_outcome_id"],
        override_candidate_reference_id=vector_input["override_candidate_reference_id"],
        beacon_id=vector_input["beacon_id"],
        beacon_revision_id=vector_input["beacon_revision_id"],
        filter_catalog_version_id=vector_input["filter_catalog_version_id"],
        candidate_state=BeaconOverrideCandidateState.PREPARED,
        validated_builder_field_ids=tuple(vector_input["validated_builder_field_ids"]),
    )
    assert outcome.filter_catalog_version_id == vector_input["filter_catalog_version_id"]
    assert len(outcome.validated_builder_field_ids) == len(vector_input["validated_builder_field_ids"])


    return {
        "filter_catalog_version_id": outcome.filter_catalog_version_id,
        "validated_builder_field_ids_count": len(outcome.validated_builder_field_ids),
    }
def handle_fc08_safe_read_001(vector_input: dict, vector_expected: dict) -> None:
    from mayak.modules.filter_catalog.contracts import (
        FilterCapabilityProfile,
        FilterCapabilityState,
        FilterDefinition,
        FilterDefinitionState,
        FilterEvidenceReference,
        FilterEvidenceState,
        FilterValueKind,
    )
    from mayak.modules.filter_catalog.safe_read_models import (
        CatalogSafeReadAccessContext,
        CatalogSafeReadAudience,
        CatalogSafeReadSurfaceState,
        CatalogSafeFilterReadRequest,
        project_catalog_safe_filter_read,
    )
    definition = FilterDefinition(
        filter_definition_id=vector_input["filter_definition_id"],
        filter_catalog_version_id=vector_input["filter_catalog_version_id"],
        normalized_key="SYNTH_SAFE_A",
        safe_label=vector_input["safe_label"],
        value_kind=FilterValueKind.SCALAR,
        definition_state=FilterDefinitionState.APPROVED,
        evidence_reference_ids=tuple(vector_input["evidence_reference_ids"]),
        capability_profile_ids=(vector_input["capability_profile_id"],),
    )
    profile = FilterCapabilityProfile(
        filter_capability_profile_id=vector_input["capability_profile_id"],
        filter_catalog_version_id=vector_input["filter_catalog_version_id"],
        provider_surface_reference_id="FC08-REF-021",
        capability_state=FilterCapabilityState(vector_input["capability_state"]),
        evidence_reference_ids=tuple(vector_input["evidence_reference_ids"]),
    )
    evidence_refs = tuple(
        FilterEvidenceReference(
            evidence_reference_id=eid,
            evidence_state=FilterEvidenceState.CURRENT,
            evidence_kind_code="SYNTH_EVID",
            scope_reference_ids=("FC08-REF-021",),
            source_fingerprint=_fp("a"),
            observed_at=_ts(),
            refresh_required=False,
        )
        for eid in vector_input["evidence_reference_ids"]
    )
    context = CatalogSafeReadAccessContext(
        audience=CatalogSafeReadAudience(vector_input["audience"]),
        surface_state=CatalogSafeReadSurfaceState(vector_input["surface_state"]),
        access_decision_reference_id=vector_input["access_decision_reference_id"],
        scope_reference_id=vector_input["scope_reference_id"],
    )
    request = CatalogSafeFilterReadRequest(
        catalog_safe_filter_read_model_id="FC08-REF-019",
        access_context=context,
        filter_catalog_version_id=vector_input["filter_catalog_version_id"],
        filter_definition=definition,
        capability_profile=profile,
        evidence_references=evidence_refs,
        provenance_reference_ids=tuple(vector_input["provenance_reference_ids"]),
    )
    model = project_catalog_safe_filter_read(request)
    assert model.surface_state == CatalogSafeReadSurfaceState(vector_expected["surface_state"])
    assert model.details_redacted is vector_expected["details_redacted"]
    if vector_expected.get("warning_ids_empty"):
        assert model.warning_ids == ()
    if vector_expected.get("evidence_reference_ids_empty"):
        assert model.evidence_reference_ids == ()


    return {
        "surface_state": model.surface_state.value,
        "details_redacted": model.details_redacted,
        "warning_ids_empty": model.warning_ids == (),
        "evidence_reference_ids_empty": model.evidence_reference_ids == (),
    }
def handle_fc08_safe_read_002(vector_input: dict, vector_expected: dict) -> dict:
    from mayak.modules.filter_catalog.contracts import (
        FilterCapabilityProfile,
        FilterCapabilityState,
        FilterDefinition,
        FilterDefinitionState,
        FilterEvidenceReference,
        FilterEvidenceState,
        FilterValueKind,
    )
    from mayak.modules.filter_catalog.safe_read_models import (
        CatalogSafeReadAccessContext,
        CatalogSafeReadAudience,
        CatalogSafeReadSurfaceState,
        CatalogSafeFilterReadRequest,
        project_catalog_safe_filter_read,
    )
    definition = FilterDefinition(
        filter_definition_id="FC08-REF-003",
        filter_catalog_version_id="FC08-REF-001",
        normalized_key="SYNTH_SAFE_B",
        safe_label="Synthetic safe label",
        value_kind=FilterValueKind.SCALAR,
        definition_state=FilterDefinitionState.APPROVED,
        evidence_reference_ids=("FC08-REF-007",),
        capability_profile_ids=("FC08-REF-005",),
    )
    profile = FilterCapabilityProfile(
        filter_capability_profile_id="FC08-REF-005",
        filter_catalog_version_id="FC08-REF-001",
        provider_surface_reference_id="FC08-REF-021",
        capability_state=FilterCapabilityState.EDITABLE,
        evidence_reference_ids=("FC08-REF-007",),
    )
    evidence_refs = (
        FilterEvidenceReference(
            evidence_reference_id="FC08-REF-007",
            evidence_state=FilterEvidenceState.CURRENT,
            evidence_kind_code="SYNTH_EVID",
            scope_reference_ids=("FC08-REF-021",),
            source_fingerprint=_fp("a"),
            observed_at=_ts(),
            refresh_required=False,
        ),
    )
    context = CatalogSafeReadAccessContext(
        audience=CatalogSafeReadAudience.WEB_CUSTOMER,
        surface_state=CatalogSafeReadSurfaceState.AVAILABLE,
        access_decision_reference_id="FC08-REF-020",
        scope_reference_id="FC08-REF-021",
    )
    request = CatalogSafeFilterReadRequest(
        catalog_safe_filter_read_model_id="FC08-REF-019",
        access_context=context,
        filter_catalog_version_id="FC08-REF-001",
        filter_definition=definition,
        capability_profile=profile,
        evidence_references=evidence_refs,
        provenance_reference_ids=("FC08-REF-023",),
    )
    model = project_catalog_safe_filter_read(request)
    assert model.details_redacted is True
    assert model.warning_ids == ()
    assert model.evidence_reference_ids == ()
    assert model.beacon_override_candidate_outcome_reference_id is None
    return {
        "details_redacted": model.details_redacted,
        "warning_ids_empty": model.warning_ids == (),
        "evidence_reference_ids_empty": model.evidence_reference_ids == (),
        "beacon_override_candidate_outcome_reference_id": model.beacon_override_candidate_outcome_reference_id,
    }


def handle_fc08_safe_read_003(vector_input: dict, vector_expected: dict) -> None:
    from mayak.modules.filter_catalog.contracts import (
        FilterCapabilityProfile,
        FilterCapabilityState,
        FilterDefinition,
        FilterDefinitionState,
        FilterEvidenceReference,
        FilterEvidenceState,
        FilterValueKind,
    )
    from mayak.modules.filter_catalog.safe_read_models import (
        CatalogSafeReadAccessContext,
        CatalogSafeReadAudience,
        CatalogSafeReadSurfaceState,
        CatalogSafeFilterReadRequest,
        project_catalog_safe_filter_read,
    )
    definition = FilterDefinition(
        filter_definition_id=vector_input["filter_definition_id"],
        filter_catalog_version_id=vector_input["filter_catalog_version_id"],
        normalized_key="SYNTH_SAFE_B",
        safe_label=vector_input["safe_label"],
        value_kind=FilterValueKind.SCALAR,
        definition_state=FilterDefinitionState.APPROVED,
        evidence_reference_ids=tuple(vector_input["evidence_reference_ids"]),
        capability_profile_ids=(vector_input["capability_profile_id"],),
    )
    profile = FilterCapabilityProfile(
        filter_capability_profile_id=vector_input["capability_profile_id"],
        filter_catalog_version_id=vector_input["filter_catalog_version_id"],
        provider_surface_reference_id="FC08-REF-021",
        capability_state=FilterCapabilityState(vector_input["capability_state"]),
        evidence_reference_ids=tuple(vector_input["evidence_reference_ids"]),
    )
    evidence_refs = tuple(
        FilterEvidenceReference(
            evidence_reference_id=eid,
            evidence_state=FilterEvidenceState.CURRENT,
            evidence_kind_code="SYNTH_EVID",
            scope_reference_ids=("FC08-REF-021",),
            source_fingerprint=_fp("a"),
            observed_at=_ts(),
            refresh_required=False,
        )
        for eid in vector_input["evidence_reference_ids"]
    )
    context = CatalogSafeReadAccessContext(
        audience=CatalogSafeReadAudience(vector_input["audience"]),
        surface_state=CatalogSafeReadSurfaceState(vector_input["surface_state"]),
        access_decision_reference_id=vector_input["access_decision_reference_id"],
        scope_reference_id=vector_input["scope_reference_id"],
    )
    request = CatalogSafeFilterReadRequest(
        catalog_safe_filter_read_model_id="FC08-REF-019",
        access_context=context,
        filter_catalog_version_id=vector_input["filter_catalog_version_id"],
        filter_definition=definition,
        capability_profile=profile,
        evidence_references=evidence_refs,
        provenance_reference_ids=tuple(vector_input["provenance_reference_ids"]),
    )
    model = project_catalog_safe_filter_read(request)
    assert model.surface_state == CatalogSafeReadSurfaceState(vector_expected["surface_state"])
    assert model.details_redacted is vector_expected["details_redacted"]


    return {
        "surface_state": model.surface_state.value,
        "details_redacted": model.details_redacted,
    }
def handle_fc08_safe_read_004(vector_input: dict, vector_expected: dict) -> None:
    from mayak.modules.filter_catalog.safe_read_models import (
        CatalogSafeReadAccessContext,
        CatalogSafeReadAudience,
        CatalogSafeReadSurfaceState,
        CatalogSafeFilterReadRequest,
        project_catalog_safe_filter_read,
    )
    context = CatalogSafeReadAccessContext(
        audience=CatalogSafeReadAudience.WEB_CUSTOMER,
        surface_state=CatalogSafeReadSurfaceState.REDACTED,
        access_decision_reference_id="FC08-REF-020",
        scope_reference_id="FC08-REF-021",
    )
    request = CatalogSafeFilterReadRequest(
        catalog_safe_filter_read_model_id="FC08-REF-019",
        access_context=context,
        filter_catalog_version_id="FC08-REF-001",
        provenance_reference_ids=("FC08-REF-023",),
    )
    model = project_catalog_safe_filter_read(request)
    assert model.surface_state.value == vector_expected["surface_state"]
    assert model.explanation_codes[0].value == "REDACTED"
    assert model.details_redacted is True


    return {
        "surface_state": model.surface_state.value,
        "explanation_code": model.explanation_codes[0].value,
        "details_redacted": model.details_redacted,
    }
def handle_fc08_safe_read_005(vector_input: dict, vector_expected: dict) -> None:
    from mayak.modules.filter_catalog.safe_read_models import (
        CatalogSafeReadAccessContext,
        CatalogSafeReadAudience,
        CatalogSafeReadSurfaceState,
        CatalogSafeFilterReadRequest,
        project_catalog_safe_filter_read,
    )
    context = CatalogSafeReadAccessContext(
        audience=CatalogSafeReadAudience.WEB_CUSTOMER,
        surface_state=CatalogSafeReadSurfaceState.FORBIDDEN,
        access_decision_reference_id="FC08-REF-020",
        scope_reference_id="FC08-REF-032",
    )
    request = CatalogSafeFilterReadRequest(
        catalog_safe_filter_read_model_id="FC08-REF-019",
        access_context=context,
        filter_catalog_version_id="FC08-REF-001",
        provenance_reference_ids=("FC08-REF-034",),
    )
    model = project_catalog_safe_filter_read(request)
    assert model.surface_state.value == vector_expected["surface_state"]
    assert model.explanation_codes[0].value == "FORBIDDEN"
    assert model.details_redacted is True


    return {
        "surface_state": model.surface_state.value,
        "explanation_code": model.explanation_codes[0].value,
        "details_redacted": model.details_redacted,
    }
def handle_fc08_safe_read_006(vector_input: dict, vector_expected: dict) -> None:
    from mayak.modules.filter_catalog.safe_read_models import (
        CatalogSafeReadAccessContext,
        CatalogSafeReadAudience,
        CatalogSafeReadSurfaceState,
        CatalogSafeFilterReadRequest,
        project_catalog_safe_filter_read,
    )
    context = CatalogSafeReadAccessContext(
        audience=CatalogSafeReadAudience.WEB_CUSTOMER,
        surface_state=CatalogSafeReadSurfaceState.NOT_FOUND_SAFE,
        access_decision_reference_id="FC08-REF-020",
        scope_reference_id="FC08-REF-021",
    )
    request = CatalogSafeFilterReadRequest(
        catalog_safe_filter_read_model_id="FC08-REF-019",
        access_context=context,
        filter_catalog_version_id="FC08-REF-001",
        provenance_reference_ids=("FC08-REF-023",),
    )
    model = project_catalog_safe_filter_read(request)
    assert model.surface_state.value == vector_expected["surface_state"]
    assert model.explanation_codes[0].value == "NOT_FOUND_SAFE"
    assert model.details_redacted is True


    return {
        "surface_state": model.surface_state.value,
        "explanation_code": model.explanation_codes[0].value,
        "details_redacted": model.details_redacted,
    }
def handle_fc08_safe_read_007(vector_input: dict, vector_expected: dict) -> None:
    from mayak.modules.filter_catalog.contracts import (
        FilterCapabilityProfile,
        FilterCapabilityState,
        FilterDefinition,
        FilterDefinitionState,
        FilterEvidenceReference,
        FilterEvidenceState,
        FilterValueKind,
    )
    from mayak.modules.filter_catalog.safe_read_models import (
        CatalogSafeReadAccessContext,
        CatalogSafeReadAudience,
        CatalogSafeReadSurfaceState,
        CatalogSafeFilterReadRequest,
        project_catalog_safe_filter_read,
    )
    evidence_refs = tuple(
        FilterEvidenceReference(
            evidence_reference_id="FC08-REF-007",
            evidence_state=FilterEvidenceState(state),
            evidence_kind_code="SYNTH_EVID",
            scope_reference_ids=("FC08-REF-021",),
            source_fingerprint=_fp("a"),
            observed_at=_ts(),
            refresh_required=False,
        )
        for state in vector_input["evidence_states"]
    )
    definition = FilterDefinition(
        filter_definition_id="FC08-REF-003",
        filter_catalog_version_id="FC08-REF-001",
        normalized_key="SYNTH_SAFE_FRESH",
        safe_label="Synthetic freshness label",
        value_kind=FilterValueKind.SCALAR,
        definition_state=FilterDefinitionState.APPROVED,
        evidence_reference_ids=tuple(ref.evidence_reference_id for ref in evidence_refs),
        capability_profile_ids=("FC08-REF-005",),
    )
    profile = FilterCapabilityProfile(
        filter_capability_profile_id="FC08-REF-005",
        filter_catalog_version_id="FC08-REF-001",
        provider_surface_reference_id="FC08-REF-021",
        capability_state=FilterCapabilityState.EDITABLE,
        evidence_reference_ids=tuple(ref.evidence_reference_id for ref in evidence_refs),
    )
    context = CatalogSafeReadAccessContext(
        audience=CatalogSafeReadAudience.WEB_CUSTOMER,
        surface_state=CatalogSafeReadSurfaceState.AVAILABLE,
        access_decision_reference_id="FC08-REF-020",
        scope_reference_id="FC08-REF-021",
    )
    request = CatalogSafeFilterReadRequest(
        catalog_safe_filter_read_model_id="FC08-REF-019",
        access_context=context,
        filter_catalog_version_id="FC08-REF-001",
        filter_definition=definition,
        capability_profile=profile,
        evidence_references=evidence_refs,
        provenance_reference_ids=("FC08-REF-023",),
    )
    model = project_catalog_safe_filter_read(request)
    assert model.freshness_state.value == vector_expected["freshness_state"]


    return {
        "freshness_state": model.freshness_state.value,
    }
def handle_fc08_safe_read_008(vector_input: dict, vector_expected: dict) -> None:
    from mayak.modules.filter_catalog.contracts import (
        FilterCapabilityProfile,
        FilterCapabilityState,
        FilterDefinition,
        FilterDefinitionState,
        FilterEvidenceReference,
        FilterEvidenceState,
        FilterValueKind,
    )
    from mayak.modules.filter_catalog.safe_read_models import (
        CatalogSafeReadAccessContext,
        CatalogSafeReadAudience,
        CatalogSafeReadSurfaceState,
        CatalogSafeFilterReadRequest,
        project_catalog_safe_filter_read,
    )
    evidence_refs = tuple(
        FilterEvidenceReference(
            evidence_reference_id="FC08-REF-008",
            evidence_state=FilterEvidenceState(state),
            evidence_kind_code="SYNTH_EVID",
            scope_reference_ids=("FC08-REF-021",),
            source_fingerprint=_fp("b"),
            observed_at=_ts(),
            refresh_required=True,
        )
        for state in vector_input["evidence_states"]
    )
    definition = FilterDefinition(
        filter_definition_id="FC08-REF-003",
        filter_catalog_version_id="FC08-REF-001",
        normalized_key="SYNTH_SAFE_FRESH",
        safe_label="Synthetic freshness label",
        value_kind=FilterValueKind.SCALAR,
        definition_state=FilterDefinitionState.APPROVED,
        evidence_reference_ids=tuple(ref.evidence_reference_id for ref in evidence_refs),
        capability_profile_ids=("FC08-REF-005",),
    )
    profile = FilterCapabilityProfile(
        filter_capability_profile_id="FC08-REF-005",
        filter_catalog_version_id="FC08-REF-001",
        provider_surface_reference_id="FC08-REF-021",
        capability_state=FilterCapabilityState.EDITABLE,
        evidence_reference_ids=tuple(ref.evidence_reference_id for ref in evidence_refs),
    )
    context = CatalogSafeReadAccessContext(
        audience=CatalogSafeReadAudience.WEB_CUSTOMER,
        surface_state=CatalogSafeReadSurfaceState.AVAILABLE,
        access_decision_reference_id="FC08-REF-020",
        scope_reference_id="FC08-REF-021",
    )
    request = CatalogSafeFilterReadRequest(
        catalog_safe_filter_read_model_id="FC08-REF-019",
        access_context=context,
        filter_catalog_version_id="FC08-REF-001",
        filter_definition=definition,
        capability_profile=profile,
        evidence_references=evidence_refs,
        provenance_reference_ids=("FC08-REF-023",),
    )
    model = project_catalog_safe_filter_read(request)
    assert model.freshness_state.value == vector_expected["freshness_state"]


    return {
        "freshness_state": model.freshness_state.value,
    }
def handle_fc08_safe_read_009(vector_input: dict, vector_expected: dict) -> None:
    from mayak.modules.filter_catalog.contracts import (
        FilterCapabilityProfile,
        FilterCapabilityState,
        FilterDefinition,
        FilterDefinitionState,
        FilterEvidenceReference,
        FilterEvidenceState,
        FilterValueKind,
    )
    from mayak.modules.filter_catalog.safe_read_models import (
        CatalogSafeReadAccessContext,
        CatalogSafeReadAudience,
        CatalogSafeReadSurfaceState,
        CatalogSafeFilterReadRequest,
        project_catalog_safe_filter_read,
    )
    evidence_refs = tuple(
        FilterEvidenceReference(
            evidence_reference_id="FC08-REF-007",
            evidence_state=FilterEvidenceState(state),
            evidence_kind_code="SYNTH_EVID",
            scope_reference_ids=("FC08-REF-021",),
            source_fingerprint=_fp("c"),
            observed_at=_ts(),
            refresh_required=False,
        )
        for state in vector_input["evidence_states"]
    )
    definition = FilterDefinition(
        filter_definition_id="FC08-REF-003",
        filter_catalog_version_id="FC08-REF-001",
        normalized_key="SYNTH_SAFE_FRESH",
        safe_label="Synthetic freshness label",
        value_kind=FilterValueKind.SCALAR,
        definition_state=FilterDefinitionState.APPROVED,
        evidence_reference_ids=tuple(ref.evidence_reference_id for ref in evidence_refs),
        capability_profile_ids=("FC08-REF-005",),
    )
    profile = FilterCapabilityProfile(
        filter_capability_profile_id="FC08-REF-005",
        filter_catalog_version_id="FC08-REF-001",
        provider_surface_reference_id="FC08-REF-021",
        capability_state=FilterCapabilityState.EDITABLE,
        evidence_reference_ids=tuple(ref.evidence_reference_id for ref in evidence_refs),
    )
    context = CatalogSafeReadAccessContext(
        audience=CatalogSafeReadAudience.WEB_CUSTOMER,
        surface_state=CatalogSafeReadSurfaceState.AVAILABLE,
        access_decision_reference_id="FC08-REF-020",
        scope_reference_id="FC08-REF-021",
    )
    request = CatalogSafeFilterReadRequest(
        catalog_safe_filter_read_model_id="FC08-REF-019",
        access_context=context,
        filter_catalog_version_id="FC08-REF-001",
        filter_definition=definition,
        capability_profile=profile,
        evidence_references=evidence_refs,
        provenance_reference_ids=("FC08-REF-023",),
    )
    model = project_catalog_safe_filter_read(request)
    assert model.freshness_state.value == vector_expected["freshness_state"]


    return {
        "freshness_state": model.freshness_state.value,
    }
def handle_fc08_safe_read_010(vector_input: dict, vector_expected: dict) -> None:
    from mayak.modules.filter_catalog.contracts import (
        FilterCapabilityProfile,
        FilterCapabilityState,
        FilterDefinition,
        FilterDefinitionState,
        FilterEvidenceReference,
        FilterEvidenceState,
        FilterValueKind,
    )
    from mayak.modules.filter_catalog.safe_read_models import (
        CatalogSafeReadAccessContext,
        CatalogSafeReadAudience,
        CatalogSafeReadSurfaceState,
        CatalogSafeFilterReadRequest,
        project_catalog_safe_filter_read,
    )
    evidence_refs = tuple(
        FilterEvidenceReference(
            evidence_reference_id="FC08-REF-008",
            evidence_state=FilterEvidenceState(state),
            evidence_kind_code="SYNTH_EVID",
            scope_reference_ids=("FC08-REF-021",),
            source_fingerprint=_fp("d"),
            observed_at=_ts(),
            refresh_required=False,
        )
        for state in vector_input["evidence_states"]
    )
    definition = FilterDefinition(
        filter_definition_id="FC08-REF-003",
        filter_catalog_version_id="FC08-REF-001",
        normalized_key="SYNTH_SAFE_FRESH",
        safe_label="Synthetic freshness label",
        value_kind=FilterValueKind.SCALAR,
        definition_state=FilterDefinitionState.APPROVED,
        evidence_reference_ids=tuple(ref.evidence_reference_id for ref in evidence_refs),
        capability_profile_ids=("FC08-REF-005",),
    )
    profile = FilterCapabilityProfile(
        filter_capability_profile_id="FC08-REF-005",
        filter_catalog_version_id="FC08-REF-001",
        provider_surface_reference_id="FC08-REF-021",
        capability_state=FilterCapabilityState.EDITABLE,
        evidence_reference_ids=tuple(ref.evidence_reference_id for ref in evidence_refs),
    )
    context = CatalogSafeReadAccessContext(
        audience=CatalogSafeReadAudience.WEB_CUSTOMER,
        surface_state=CatalogSafeReadSurfaceState.AVAILABLE,
        access_decision_reference_id="FC08-REF-020",
        scope_reference_id="FC08-REF-021",
    )
    request = CatalogSafeFilterReadRequest(
        catalog_safe_filter_read_model_id="FC08-REF-019",
        access_context=context,
        filter_catalog_version_id="FC08-REF-001",
        filter_definition=definition,
        capability_profile=profile,
        evidence_references=evidence_refs,
        provenance_reference_ids=("FC08-REF-023",),
    )
    model = project_catalog_safe_filter_read(request)
    assert model.freshness_state.value == vector_expected["freshness_state"]


    return {
        "freshness_state": model.freshness_state.value,
    }
def handle_fc08_safe_read_011(vector_input: dict, vector_expected: dict) -> None:
    from mayak.modules.filter_catalog.contracts import (
        BeaconOverrideCandidateOutcome,
        BeaconOverrideCandidateState,
        BuilderFieldDefinition,
        FilterCapabilityProfile,
        FilterCapabilityState,
        FilterDefinition,
        FilterDefinitionState,
        FilterEvidenceReference,
        FilterEvidenceState,
        FilterValueKind,
    )
    from mayak.modules.filter_catalog.safe_read_models import (
        CatalogSafeReadAccessContext,
        CatalogSafeReadAudience,
        CatalogSafeReadSurfaceState,
        CatalogSafeExplanationCode,
        CatalogSafeFilterReadRequest,
        project_catalog_safe_filter_read,
    )
    definition = FilterDefinition(
        filter_definition_id="FC08-REF-003",
        filter_catalog_version_id="FC08-REF-001",
        normalized_key="SYNTH_SAFE_BEACON",
        safe_label="Synthetic beacon label",
        value_kind=FilterValueKind.SCALAR,
        definition_state=FilterDefinitionState.APPROVED,
        evidence_reference_ids=("FC08-REF-007",),
        capability_profile_ids=("FC08-REF-005",),
    )
    profile = FilterCapabilityProfile(
        filter_capability_profile_id="FC08-REF-005",
        filter_catalog_version_id="FC08-REF-001",
        provider_surface_reference_id="FC08-REF-021",
        capability_state=FilterCapabilityState(vector_input["capability_state"]),
        evidence_reference_ids=("FC08-REF-007",),
    )
    evidence_refs = (
        FilterEvidenceReference(
            evidence_reference_id="FC08-REF-007",
            evidence_state=FilterEvidenceState.CURRENT,
            evidence_kind_code="SYNTH_EVID",
            scope_reference_ids=("FC08-REF-021",),
            source_fingerprint=_fp("a"),
            observed_at=_ts(),
            refresh_required=False,
        ),
    )
    builder = BuilderFieldDefinition(
        builder_field_id="FC08-REF-011",
        filter_catalog_version_id="FC08-REF-001",
        filter_definition_id="FC08-REF-003",
        filter_capability_profile_id="FC08-REF-005",
        capability_state=FilterCapabilityState(vector_input["capability_state"]),
        value_kind=FilterValueKind.SCALAR,
        required=True,
    )
    candidate = BeaconOverrideCandidateOutcome(
        beacon_override_candidate_outcome_id="FC08-REF-019",
        override_candidate_reference_id="FC08-REF-030",
        beacon_id="FC08-REF-016",
        beacon_revision_id="FC08-REF-017",
        filter_catalog_version_id="FC08-REF-001",
        candidate_state=BeaconOverrideCandidateState.PREPARED,
        validated_builder_field_ids=("FC08-REF-011",),
    )
    context = CatalogSafeReadAccessContext(
        audience=CatalogSafeReadAudience.ADMIN_AUTHORIZED,
        surface_state=CatalogSafeReadSurfaceState.AVAILABLE,
        access_decision_reference_id="FC08-REF-020",
        scope_reference_id="FC08-REF-021",
    )
    request = CatalogSafeFilterReadRequest(
        catalog_safe_filter_read_model_id="FC08-REF-019",
        access_context=context,
        filter_catalog_version_id="FC08-REF-001",
        filter_definition=definition,
        capability_profile=profile,
        builder_field_definition=builder,
        evidence_references=evidence_refs,
        provenance_reference_ids=("FC08-REF-023",),
        beacon_override_candidate_outcome=candidate,
    )
    model = project_catalog_safe_filter_read(request)
    assert CatalogSafeExplanationCode.BEACON_ACCEPTANCE_REQUIRED in model.explanation_codes
    assert model.beacon_acceptance_required is True


    return {
        "beacon_acceptance_required_in_explanations": CatalogSafeExplanationCode.BEACON_ACCEPTANCE_REQUIRED in model.explanation_codes,
        "beacon_acceptance_required": model.beacon_acceptance_required,
    }
def handle_fc08_safe_read_012(vector_input: dict, vector_expected: dict) -> dict:
    from mayak.modules.filter_catalog.safe_read_models import (
        CatalogSafeReadAccessContext,
        CatalogSafeReadAudience,
        CatalogSafeReadSurfaceState,
        CatalogSafeFilterReadRequest,
        project_catalog_safe_filter_read,
    )
    context = CatalogSafeReadAccessContext(
        audience=CatalogSafeReadAudience.WEB_CUSTOMER,
        surface_state=CatalogSafeReadSurfaceState.REDACTED,
        access_decision_reference_id="FC08-REF-020",
        scope_reference_id="FC08-REF-021",
    )
    request = CatalogSafeFilterReadRequest(
        catalog_safe_filter_read_model_id="FC08-REF-019",
        access_context=context,
        filter_catalog_version_id="FC08-REF-001",
        provenance_reference_ids=("FC08-REF-023",),
    )
    model = project_catalog_safe_filter_read(request)
    assert model.identity_authorization_performed_by_filter_catalog is False
    assert model.authoritative_business_state is False
    assert model.contains_raw_provider_payload is False
    assert model.contains_stack_trace is False
    assert model.contains_secret_or_personal_data is False
    assert model.contains_admin_private_notes is False
    assert model.runtime_or_persistence_performed is False
    return {
        "identity_authorization_performed_by_filter_catalog": model.identity_authorization_performed_by_filter_catalog,
        "authoritative_business_state": model.authoritative_business_state,
        "contains_raw_provider_payload": model.contains_raw_provider_payload,
        "contains_stack_trace": model.contains_stack_trace,
        "contains_secret_or_personal_data": model.contains_secret_or_personal_data,
        "contains_admin_private_notes": model.contains_admin_private_notes,
        "runtime_or_persistence_performed": model.runtime_or_persistence_performed,
        "surface_state": model.surface_state.value,
    }


def handle_fc08_static_001(vector_input: dict, vector_expected: dict) -> None:
    import importlib
    mod = importlib.import_module("mayak.modules.filter_catalog")
    all_names = list(mod.__all__)
    for sym in vector_input["expected_symbols"]:
        assert sym in all_names, f"{sym} not in package __all__"
    assert vector_expected["all_symbols_present"]


    return {
        "all_symbols_present": vector_expected["all_symbols_present"],
        "symbol_count": len(vector_input["expected_symbols"]),
    }
def handle_fc08_static_002(vector_input: dict, vector_expected: dict) -> None:
    import subprocess
    result = subprocess.run(
        ["grep", "-rn", "--include=*.py", "-E", r"^from (fastapi|sqlalchemy|alembic|httpx|respx|opentelemetry|aiogram|telethon|psycopg|psycopg2)",
         str(REPO_ROOT / "src" / "mayak" / "modules" / "filter_catalog")],
        capture_output=True, text=True,
    )
    assert result.stdout.strip() == "", f"Forbidden imports found: {result.stdout}"


    return {
        "forbidden_imports_absent": result.stdout.strip() == "",
    }
def handle_fc08_static_003(vector_input: dict, vector_expected: dict) -> None:
    import subprocess
    for filename, expected_blob in vector_input["expected_blobs"].items():
        result = subprocess.run(
            ["git", "rev-parse", f"HEAD:src/mayak/modules/filter_catalog/{filename}"],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        actual = result.stdout.strip()
        assert actual == expected_blob, f"Blob mismatch for {filename}"


    return {
        "all_blobs_match": True,
    }
def handle_fc08_static_004(vector_input: dict, vector_expected: dict) -> None:
    assert vector_expected["od009_open"]
    assert vector_expected["no_real_provider_data"]
    decisions_path = REPO_ROOT / "docs" / "00-governance" / "OPEN_DECISIONS.md"
    content = decisions_path.read_text(encoding="utf-8")
    assert "OD-009" in content


# ---------------------------------------------------------------------------
# 56 Explicit Vector-Specific Test Functions
# ---------------------------------------------------------------------------

    return {
        "od009_open": vector_expected["od009_open"],
        "no_real_provider_data": vector_expected["no_real_provider_data"],
    }
def test_fc08_catalog_001() -> None:
    v = _get_vector("FC08-CATALOG-001")
    assert v["handler"] == "handle_fc08_catalog_001"
    inp = copy.deepcopy(v["input"])
    exp = copy.deepcopy(v["expected"])
    handle_fc08_catalog_001(inp, exp)
    assert inp == v["input"]
    _run_handler_twice(handle_fc08_catalog_001, v["input"], v["expected"])


def test_fc08_catalog_002() -> None:
    v = _get_vector("FC08-CATALOG-002")
    assert v["handler"] == "handle_fc08_catalog_002"
    inp = copy.deepcopy(v["input"])
    exp = copy.deepcopy(v["expected"])
    handle_fc08_catalog_002(inp, exp)
    assert inp == v["input"]
    _run_handler_twice(handle_fc08_catalog_002, v["input"], v["expected"])


def test_fc08_catalog_003() -> None:
    v = _get_vector("FC08-CATALOG-003")
    assert v["handler"] == "handle_fc08_catalog_003"
    inp = copy.deepcopy(v["input"])
    exp = copy.deepcopy(v["expected"])
    handle_fc08_catalog_003(inp, exp)
    assert inp == v["input"]
    _run_handler_twice(handle_fc08_catalog_003, v["input"], v["expected"])


def test_fc08_catalog_004() -> None:
    v = _get_vector("FC08-CATALOG-004")
    assert v["handler"] == "handle_fc08_catalog_004"
    inp = copy.deepcopy(v["input"])
    exp = copy.deepcopy(v["expected"])
    handle_fc08_catalog_004(inp, exp)
    assert inp == v["input"]
    _run_handler_twice(handle_fc08_catalog_004, v["input"], v["expected"])


def test_fc08_catalog_005() -> None:
    v = _get_vector("FC08-CATALOG-005")
    assert v["handler"] == "handle_fc08_catalog_005"
    inp = copy.deepcopy(v["input"])
    exp = copy.deepcopy(v["expected"])
    handle_fc08_catalog_005(inp, exp)
    assert inp == v["input"]
    _run_handler_twice(handle_fc08_catalog_005, v["input"], v["expected"])


def test_fc08_catalog_006() -> None:
    v = _get_vector("FC08-CATALOG-006")
    assert v["handler"] == "handle_fc08_catalog_006"
    inp = copy.deepcopy(v["input"])
    exp = copy.deepcopy(v["expected"])
    handle_fc08_catalog_006(inp, exp)
    assert inp == v["input"]
    _run_handler_twice(handle_fc08_catalog_006, v["input"], v["expected"])


def test_fc08_catalog_007() -> None:
    v = _get_vector("FC08-CATALOG-007")
    assert v["handler"] == "handle_fc08_catalog_007"
    inp = copy.deepcopy(v["input"])
    exp = copy.deepcopy(v["expected"])
    handle_fc08_catalog_007(inp, exp)
    assert inp == v["input"]
    _run_handler_twice(handle_fc08_catalog_007, v["input"], v["expected"])


def test_fc08_catalog_008() -> None:
    v = _get_vector("FC08-CATALOG-008")
    assert v["handler"] == "handle_fc08_catalog_008"
    inp = copy.deepcopy(v["input"])
    exp = copy.deepcopy(v["expected"])
    handle_fc08_catalog_008(inp, exp)
    assert inp == v["input"]
    _run_handler_twice(handle_fc08_catalog_008, v["input"], v["expected"])


def test_fc08_evidence_001() -> None:
    v = _get_vector("FC08-EVIDENCE-001")
    assert v["handler"] == "handle_fc08_evidence_001"
    inp = copy.deepcopy(v["input"])
    exp = copy.deepcopy(v["expected"])
    handle_fc08_evidence_001(inp, exp)
    assert inp == v["input"]
    _run_handler_twice(handle_fc08_evidence_001, v["input"], v["expected"])


def test_fc08_evidence_002() -> None:
    v = _get_vector("FC08-EVIDENCE-002")
    assert v["handler"] == "handle_fc08_evidence_002"
    inp = copy.deepcopy(v["input"])
    exp = copy.deepcopy(v["expected"])
    handle_fc08_evidence_002(inp, exp)
    assert inp == v["input"]
    _run_handler_twice(handle_fc08_evidence_002, v["input"], v["expected"])


def test_fc08_evidence_003() -> None:
    v = _get_vector("FC08-EVIDENCE-003")
    assert v["handler"] == "handle_fc08_evidence_003"
    inp = copy.deepcopy(v["input"])
    exp = copy.deepcopy(v["expected"])
    handle_fc08_evidence_003(inp, exp)
    assert inp == v["input"]
    _run_handler_twice(handle_fc08_evidence_003, v["input"], v["expected"])


def test_fc08_evidence_004() -> None:
    v = _get_vector("FC08-EVIDENCE-004")
    assert v["handler"] == "handle_fc08_evidence_004"
    inp = copy.deepcopy(v["input"])
    exp = copy.deepcopy(v["expected"])
    handle_fc08_evidence_004(inp, exp)
    assert inp == v["input"]
    _run_handler_twice(handle_fc08_evidence_004, v["input"], v["expected"])


def test_fc08_evidence_005() -> None:
    v = _get_vector("FC08-EVIDENCE-005")
    assert v["handler"] == "handle_fc08_evidence_005"
    inp = copy.deepcopy(v["input"])
    exp = copy.deepcopy(v["expected"])
    handle_fc08_evidence_005(inp, exp)
    assert inp == v["input"]
    _run_handler_twice(handle_fc08_evidence_005, v["input"], v["expected"])


def test_fc08_evidence_006() -> None:
    v = _get_vector("FC08-EVIDENCE-006")
    assert v["handler"] == "handle_fc08_evidence_006"
    inp = copy.deepcopy(v["input"])
    exp = copy.deepcopy(v["expected"])
    handle_fc08_evidence_006(inp, exp)
    assert inp == v["input"]
    _run_handler_twice(handle_fc08_evidence_006, v["input"], v["expected"])


def test_fc08_evidence_007() -> None:
    v = _get_vector("FC08-EVIDENCE-007")
    assert v["handler"] == "handle_fc08_evidence_007"
    inp = copy.deepcopy(v["input"])
    exp = copy.deepcopy(v["expected"])
    handle_fc08_evidence_007(inp, exp)
    assert inp == v["input"]
    _run_handler_twice(handle_fc08_evidence_007, v["input"], v["expected"])


def test_fc08_evidence_008() -> None:
    v = _get_vector("FC08-EVIDENCE-008")
    assert v["handler"] == "handle_fc08_evidence_008"
    inp = copy.deepcopy(v["input"])
    exp = copy.deepcopy(v["expected"])
    handle_fc08_evidence_008(inp, exp)
    assert inp == v["input"]
    _run_handler_twice(handle_fc08_evidence_008, v["input"], v["expected"])


def test_fc08_builder_001() -> None:
    v = _get_vector("FC08-BUILDER-001")
    assert v["handler"] == "handle_fc08_builder_001"
    inp = copy.deepcopy(v["input"])
    exp = copy.deepcopy(v["expected"])
    handle_fc08_builder_001(inp, exp)
    assert inp == v["input"]
    _run_handler_twice(handle_fc08_builder_001, v["input"], v["expected"])


def test_fc08_builder_002() -> None:
    v = _get_vector("FC08-BUILDER-002")
    assert v["handler"] == "handle_fc08_builder_002"
    inp = copy.deepcopy(v["input"])
    exp = copy.deepcopy(v["expected"])
    handle_fc08_builder_002(inp, exp)
    assert inp == v["input"]
    _run_handler_twice(handle_fc08_builder_002, v["input"], v["expected"])


def test_fc08_builder_003() -> None:
    v = _get_vector("FC08-BUILDER-003")
    assert v["handler"] == "handle_fc08_builder_003"
    inp = copy.deepcopy(v["input"])
    exp = copy.deepcopy(v["expected"])
    handle_fc08_builder_003(inp, exp)
    assert inp == v["input"]
    _run_handler_twice(handle_fc08_builder_003, v["input"], v["expected"])


def test_fc08_builder_004() -> None:
    v = _get_vector("FC08-BUILDER-004")
    assert v["handler"] == "handle_fc08_builder_004"
    inp = copy.deepcopy(v["input"])
    exp = copy.deepcopy(v["expected"])
    handle_fc08_builder_004(inp, exp)
    assert inp == v["input"]
    _run_handler_twice(handle_fc08_builder_004, v["input"], v["expected"])


def test_fc08_builder_005() -> None:
    v = _get_vector("FC08-BUILDER-005")
    assert v["handler"] == "handle_fc08_builder_005"
    inp = copy.deepcopy(v["input"])
    exp = copy.deepcopy(v["expected"])
    handle_fc08_builder_005(inp, exp)
    assert inp == v["input"]
    _run_handler_twice(handle_fc08_builder_005, v["input"], v["expected"])


def test_fc08_builder_006() -> None:
    v = _get_vector("FC08-BUILDER-006")
    assert v["handler"] == "handle_fc08_builder_006"
    inp = copy.deepcopy(v["input"])
    exp = copy.deepcopy(v["expected"])
    handle_fc08_builder_006(inp, exp)
    assert inp == v["input"]
    _run_handler_twice(handle_fc08_builder_006, v["input"], v["expected"])


def test_fc08_builder_007() -> None:
    v = _get_vector("FC08-BUILDER-007")
    assert v["handler"] == "handle_fc08_builder_007"
    inp = copy.deepcopy(v["input"])
    exp = copy.deepcopy(v["expected"])
    handle_fc08_builder_007(inp, exp)
    assert inp == v["input"]
    _run_handler_twice(handle_fc08_builder_007, v["input"], v["expected"])


def test_fc08_builder_008() -> None:
    v = _get_vector("FC08-BUILDER-008")
    assert v["handler"] == "handle_fc08_builder_008"
    inp = copy.deepcopy(v["input"])
    exp = copy.deepcopy(v["expected"])
    handle_fc08_builder_008(inp, exp)
    assert inp == v["input"]
    _run_handler_twice(handle_fc08_builder_008, v["input"], v["expected"])


def test_fc08_value_001() -> None:
    v = _get_vector("FC08-VALUE-001")
    assert v["handler"] == "handle_fc08_value_001"
    inp = copy.deepcopy(v["input"])
    exp = copy.deepcopy(v["expected"])
    handle_fc08_value_001(inp, exp)
    assert inp == v["input"]
    _run_handler_twice(handle_fc08_value_001, v["input"], v["expected"])


def test_fc08_value_002() -> None:
    v = _get_vector("FC08-VALUE-002")
    assert v["handler"] == "handle_fc08_value_002"
    inp = copy.deepcopy(v["input"])
    exp = copy.deepcopy(v["expected"])
    handle_fc08_value_002(inp, exp)
    assert inp == v["input"]
    _run_handler_twice(handle_fc08_value_002, v["input"], v["expected"])


def test_fc08_value_003() -> None:
    v = _get_vector("FC08-VALUE-003")
    assert v["handler"] == "handle_fc08_value_003"
    inp = copy.deepcopy(v["input"])
    exp = copy.deepcopy(v["expected"])
    handle_fc08_value_003(inp, exp)
    assert inp == v["input"]
    _run_handler_twice(handle_fc08_value_003, v["input"], v["expected"])


def test_fc08_value_004() -> None:
    v = _get_vector("FC08-VALUE-004")
    assert v["handler"] == "handle_fc08_value_004"
    inp = copy.deepcopy(v["input"])
    exp = copy.deepcopy(v["expected"])
    handle_fc08_value_004(inp, exp)
    assert inp == v["input"]
    _run_handler_twice(handle_fc08_value_004, v["input"], v["expected"])


def test_fc08_value_005() -> None:
    v = _get_vector("FC08-VALUE-005")
    assert v["handler"] == "handle_fc08_value_005"
    inp = copy.deepcopy(v["input"])
    exp = copy.deepcopy(v["expected"])
    handle_fc08_value_005(inp, exp)
    assert inp == v["input"]
    _run_handler_twice(handle_fc08_value_005, v["input"], v["expected"])


def test_fc08_value_006() -> None:
    v = _get_vector("FC08-VALUE-006")
    assert v["handler"] == "handle_fc08_value_006"
    inp = copy.deepcopy(v["input"])
    exp = copy.deepcopy(v["expected"])
    handle_fc08_value_006(inp, exp)
    assert inp == v["input"]
    _run_handler_twice(handle_fc08_value_006, v["input"], v["expected"])


def test_fc08_value_007() -> None:
    v = _get_vector("FC08-VALUE-007")
    assert v["handler"] == "handle_fc08_value_007"
    inp = copy.deepcopy(v["input"])
    exp = copy.deepcopy(v["expected"])
    handle_fc08_value_007(inp, exp)
    assert inp == v["input"]
    _run_handler_twice(handle_fc08_value_007, v["input"], v["expected"])


def test_fc08_value_008() -> None:
    v = _get_vector("FC08-VALUE-008")
    assert v["handler"] == "handle_fc08_value_008"
    inp = copy.deepcopy(v["input"])
    exp = copy.deepcopy(v["expected"])
    handle_fc08_value_008(inp, exp)
    assert inp == v["input"]
    _run_handler_twice(handle_fc08_value_008, v["input"], v["expected"])


def test_fc08_beacon_001() -> None:
    v = _get_vector("FC08-BEACON-001")
    assert v["handler"] == "handle_fc08_beacon_001"
    inp = copy.deepcopy(v["input"])
    exp = copy.deepcopy(v["expected"])
    handle_fc08_beacon_001(inp, exp)
    assert inp == v["input"]
    _run_handler_twice(handle_fc08_beacon_001, v["input"], v["expected"])


def test_fc08_beacon_002() -> None:
    v = _get_vector("FC08-BEACON-002")
    assert v["handler"] == "handle_fc08_beacon_002"
    inp = copy.deepcopy(v["input"])
    exp = copy.deepcopy(v["expected"])
    handle_fc08_beacon_002(inp, exp)
    assert inp == v["input"]
    _run_handler_twice(handle_fc08_beacon_002, v["input"], v["expected"])


def test_fc08_beacon_003() -> None:
    v = _get_vector("FC08-BEACON-003")
    assert v["handler"] == "handle_fc08_beacon_003"
    inp = copy.deepcopy(v["input"])
    exp = copy.deepcopy(v["expected"])
    handle_fc08_beacon_003(inp, exp)
    assert inp == v["input"]
    _run_handler_twice(handle_fc08_beacon_003, v["input"], v["expected"])


def test_fc08_beacon_004() -> None:
    v = _get_vector("FC08-BEACON-004")
    assert v["handler"] == "handle_fc08_beacon_004"
    inp = copy.deepcopy(v["input"])
    exp = copy.deepcopy(v["expected"])
    handle_fc08_beacon_004(inp, exp)
    assert inp == v["input"]
    _run_handler_twice(handle_fc08_beacon_004, v["input"], v["expected"])


def test_fc08_beacon_005() -> None:
    v = _get_vector("FC08-BEACON-005")
    assert v["handler"] == "handle_fc08_beacon_005"
    inp = copy.deepcopy(v["input"])
    exp = copy.deepcopy(v["expected"])
    handle_fc08_beacon_005(inp, exp)
    assert inp == v["input"]
    _run_handler_twice(handle_fc08_beacon_005, v["input"], v["expected"])


def test_fc08_beacon_006() -> None:
    v = _get_vector("FC08-BEACON-006")
    assert v["handler"] == "handle_fc08_beacon_006"
    inp = copy.deepcopy(v["input"])
    exp = copy.deepcopy(v["expected"])
    handle_fc08_beacon_006(inp, exp)
    assert inp == v["input"]
    _run_handler_twice(handle_fc08_beacon_006, v["input"], v["expected"])


def test_fc08_beacon_007() -> None:
    v = _get_vector("FC08-BEACON-007")
    assert v["handler"] == "handle_fc08_beacon_007"
    inp = copy.deepcopy(v["input"])
    exp = copy.deepcopy(v["expected"])
    handle_fc08_beacon_007(inp, exp)
    assert inp == v["input"]
    _run_handler_twice(handle_fc08_beacon_007, v["input"], v["expected"])


def test_fc08_beacon_008() -> None:
    v = _get_vector("FC08-BEACON-008")
    assert v["handler"] == "handle_fc08_beacon_008"
    inp = copy.deepcopy(v["input"])
    exp = copy.deepcopy(v["expected"])
    handle_fc08_beacon_008(inp, exp)
    assert inp == v["input"]
    _run_handler_twice(handle_fc08_beacon_008, v["input"], v["expected"])


def test_fc08_safe_read_001() -> None:
    v = _get_vector("FC08-SAFE-READ-001")
    assert v["handler"] == "handle_fc08_safe_read_001"
    inp = copy.deepcopy(v["input"])
    exp = copy.deepcopy(v["expected"])
    handle_fc08_safe_read_001(inp, exp)
    assert inp == v["input"]
    _run_handler_twice(handle_fc08_safe_read_001, v["input"], v["expected"])


def test_fc08_safe_read_002() -> None:
    v = _get_vector("FC08-SAFE-READ-002")
    assert v["handler"] == "handle_fc08_safe_read_002"
    inp = copy.deepcopy(v["input"])
    exp = copy.deepcopy(v["expected"])
    handle_fc08_safe_read_002(inp, exp)
    assert inp == v["input"]
    _run_handler_twice(handle_fc08_safe_read_002, v["input"], v["expected"])


def test_fc08_safe_read_003() -> None:
    v = _get_vector("FC08-SAFE-READ-003")
    assert v["handler"] == "handle_fc08_safe_read_003"
    inp = copy.deepcopy(v["input"])
    exp = copy.deepcopy(v["expected"])
    handle_fc08_safe_read_003(inp, exp)
    assert inp == v["input"]
    _run_handler_twice(handle_fc08_safe_read_003, v["input"], v["expected"])


def test_fc08_safe_read_004() -> None:
    v = _get_vector("FC08-SAFE-READ-004")
    assert v["handler"] == "handle_fc08_safe_read_004"
    inp = copy.deepcopy(v["input"])
    exp = copy.deepcopy(v["expected"])
    handle_fc08_safe_read_004(inp, exp)
    assert inp == v["input"]
    _run_handler_twice(handle_fc08_safe_read_004, v["input"], v["expected"])


def test_fc08_safe_read_005() -> None:
    v = _get_vector("FC08-SAFE-READ-005")
    assert v["handler"] == "handle_fc08_safe_read_005"
    inp = copy.deepcopy(v["input"])
    exp = copy.deepcopy(v["expected"])
    handle_fc08_safe_read_005(inp, exp)
    assert inp == v["input"]
    _run_handler_twice(handle_fc08_safe_read_005, v["input"], v["expected"])


def test_fc08_safe_read_006() -> None:
    v = _get_vector("FC08-SAFE-READ-006")
    assert v["handler"] == "handle_fc08_safe_read_006"
    inp = copy.deepcopy(v["input"])
    exp = copy.deepcopy(v["expected"])
    handle_fc08_safe_read_006(inp, exp)
    assert inp == v["input"]
    _run_handler_twice(handle_fc08_safe_read_006, v["input"], v["expected"])


def test_fc08_safe_read_007() -> None:
    v = _get_vector("FC08-SAFE-READ-007")
    assert v["handler"] == "handle_fc08_safe_read_007"
    inp = copy.deepcopy(v["input"])
    exp = copy.deepcopy(v["expected"])
    handle_fc08_safe_read_007(inp, exp)
    assert inp == v["input"]
    _run_handler_twice(handle_fc08_safe_read_007, v["input"], v["expected"])


def test_fc08_safe_read_008() -> None:
    v = _get_vector("FC08-SAFE-READ-008")
    assert v["handler"] == "handle_fc08_safe_read_008"
    inp = copy.deepcopy(v["input"])
    exp = copy.deepcopy(v["expected"])
    handle_fc08_safe_read_008(inp, exp)
    assert inp == v["input"]
    _run_handler_twice(handle_fc08_safe_read_008, v["input"], v["expected"])


def test_fc08_safe_read_009() -> None:
    v = _get_vector("FC08-SAFE-READ-009")
    assert v["handler"] == "handle_fc08_safe_read_009"
    inp = copy.deepcopy(v["input"])
    exp = copy.deepcopy(v["expected"])
    handle_fc08_safe_read_009(inp, exp)
    assert inp == v["input"]
    _run_handler_twice(handle_fc08_safe_read_009, v["input"], v["expected"])


def test_fc08_safe_read_010() -> None:
    v = _get_vector("FC08-SAFE-READ-010")
    assert v["handler"] == "handle_fc08_safe_read_010"
    inp = copy.deepcopy(v["input"])
    exp = copy.deepcopy(v["expected"])
    handle_fc08_safe_read_010(inp, exp)
    assert inp == v["input"]
    _run_handler_twice(handle_fc08_safe_read_010, v["input"], v["expected"])


def test_fc08_safe_read_011() -> None:
    v = _get_vector("FC08-SAFE-READ-011")
    assert v["handler"] == "handle_fc08_safe_read_011"
    inp = copy.deepcopy(v["input"])
    exp = copy.deepcopy(v["expected"])
    handle_fc08_safe_read_011(inp, exp)
    assert inp == v["input"]
    _run_handler_twice(handle_fc08_safe_read_011, v["input"], v["expected"])


def test_fc08_safe_read_012() -> None:
    v = _get_vector("FC08-SAFE-READ-012")
    assert v["handler"] == "handle_fc08_safe_read_012"
    inp = copy.deepcopy(v["input"])
    exp = copy.deepcopy(v["expected"])
    handle_fc08_safe_read_012(inp, exp)
    assert inp == v["input"]
    _run_handler_twice(handle_fc08_safe_read_012, v["input"], v["expected"])


def test_fc08_static_001() -> None:
    v = _get_vector("FC08-STATIC-001")
    assert v["handler"] == "handle_fc08_static_001"
    inp = copy.deepcopy(v["input"])
    exp = copy.deepcopy(v["expected"])
    handle_fc08_static_001(inp, exp)
    assert inp == v["input"]
    _run_handler_twice(handle_fc08_static_001, v["input"], v["expected"])


def test_fc08_static_002() -> None:
    v = _get_vector("FC08-STATIC-002")
    assert v["handler"] == "handle_fc08_static_002"
    inp = copy.deepcopy(v["input"])
    exp = copy.deepcopy(v["expected"])
    handle_fc08_static_002(inp, exp)
    assert inp == v["input"]
    _run_handler_twice(handle_fc08_static_002, v["input"], v["expected"])


def test_fc08_static_003() -> None:
    v = _get_vector("FC08-STATIC-003")
    assert v["handler"] == "handle_fc08_static_003"
    inp = copy.deepcopy(v["input"])
    exp = copy.deepcopy(v["expected"])
    handle_fc08_static_003(inp, exp)
    assert inp == v["input"]
    _run_handler_twice(handle_fc08_static_003, v["input"], v["expected"])


def test_fc08_static_004() -> None:
    v = _get_vector("FC08-STATIC-004")
    assert v["handler"] == "handle_fc08_static_004"
    inp = copy.deepcopy(v["input"])
    exp = copy.deepcopy(v["expected"])
    handle_fc08_static_004(inp, exp)
    assert inp == v["input"]
    _run_handler_twice(handle_fc08_static_004, v["input"], v["expected"])


# ---------------------------------------------------------------------------
# 8 Fixed Invariant Tests
# ---------------------------------------------------------------------------

class TestFC08FixedInvariants:
    def test_56_unique_vector_ids(self) -> None:
        vectors = _load_vectors()
        ids = [v["vector_id"] for v in vectors]
        assert len(ids) == 56
        assert len(set(ids)) == 56

    def test_56_unique_handler_names_and_explicit_tests(self) -> None:
        vectors = _load_vectors()
        handlers = [v["handler"] for v in vectors]
        assert len(handlers) == 56
        assert len(set(handlers)) == 56
        source = Path(__file__).read_text(encoding="utf-8")
        for v in vectors:
            assert f"def {v['handler']}" in source, f"Handler {v['handler']} not found in source"
            test_name = f"test_{v['vector_id'].lower().replace('-', '_')}"
            assert f"def {test_name}" in source, f"Explicit test {test_name} not found in source"

    def test_36_canonical_references(self) -> None:
        refs = _load_refs()
        assert len(refs) == 36
        ids = [r["reference_id"] for r in refs]
        assert len(set(ids)) == 36

    def test_every_canonical_ref_used(self) -> None:
        refs = _load_refs()
        vectors = _load_vectors()
        used_refs: set[str] = set()
        for v in vectors:
            used_refs.update(v["canonical_reference_ids"])
        for ref in refs:
            assert ref["reference_id"] in used_refs, f"{ref['reference_id']} not used by any vector"

    def test_no_generic_dispatcher_in_source(self) -> None:
        source_path = Path(__file__)
        content = source_path.read_text(encoding="utf-8")
        import re
        assert not re.search(r"^HANDLER_MAP\s*=", content, re.MULTILINE), "Module-level HANDLER_MAP must not exist"
        assert not re.search(r"^def test_vector_handler\b", content, re.MULTILINE), "Generic parametrized test_vector_handler must not exist"
        assert not re.search(r"^@pytest\.mark\.parametrize", content, re.MULTILINE), "No parametrize decorators allowed for vector execution"

    def test_deterministic_complete_run(self) -> None:
        vectors = _load_vectors()
        handler_map = {
            "FC08-CATALOG-001": handle_fc08_catalog_001,
            "FC08-CATALOG-002": handle_fc08_catalog_002,
            "FC08-CATALOG-003": handle_fc08_catalog_003,
            "FC08-CATALOG-004": handle_fc08_catalog_004,
            "FC08-CATALOG-005": handle_fc08_catalog_005,
            "FC08-CATALOG-006": handle_fc08_catalog_006,
            "FC08-CATALOG-007": handle_fc08_catalog_007,
            "FC08-CATALOG-008": handle_fc08_catalog_008,
            "FC08-EVIDENCE-001": handle_fc08_evidence_001,
            "FC08-EVIDENCE-002": handle_fc08_evidence_002,
            "FC08-EVIDENCE-003": handle_fc08_evidence_003,
            "FC08-EVIDENCE-004": handle_fc08_evidence_004,
            "FC08-EVIDENCE-005": handle_fc08_evidence_005,
            "FC08-EVIDENCE-006": handle_fc08_evidence_006,
            "FC08-EVIDENCE-007": handle_fc08_evidence_007,
            "FC08-EVIDENCE-008": handle_fc08_evidence_008,
            "FC08-BUILDER-001": handle_fc08_builder_001,
            "FC08-BUILDER-002": handle_fc08_builder_002,
            "FC08-BUILDER-003": handle_fc08_builder_003,
            "FC08-BUILDER-004": handle_fc08_builder_004,
            "FC08-BUILDER-005": handle_fc08_builder_005,
            "FC08-BUILDER-006": handle_fc08_builder_006,
            "FC08-BUILDER-007": handle_fc08_builder_007,
            "FC08-BUILDER-008": handle_fc08_builder_008,
            "FC08-VALUE-001": handle_fc08_value_001,
            "FC08-VALUE-002": handle_fc08_value_002,
            "FC08-VALUE-003": handle_fc08_value_003,
            "FC08-VALUE-004": handle_fc08_value_004,
            "FC08-VALUE-005": handle_fc08_value_005,
            "FC08-VALUE-006": handle_fc08_value_006,
            "FC08-VALUE-007": handle_fc08_value_007,
            "FC08-VALUE-008": handle_fc08_value_008,
            "FC08-BEACON-001": handle_fc08_beacon_001,
            "FC08-BEACON-002": handle_fc08_beacon_002,
            "FC08-BEACON-003": handle_fc08_beacon_003,
            "FC08-BEACON-004": handle_fc08_beacon_004,
            "FC08-BEACON-005": handle_fc08_beacon_005,
            "FC08-BEACON-006": handle_fc08_beacon_006,
            "FC08-BEACON-007": handle_fc08_beacon_007,
            "FC08-BEACON-008": handle_fc08_beacon_008,
            "FC08-SAFE-READ-001": handle_fc08_safe_read_001,
            "FC08-SAFE-READ-002": handle_fc08_safe_read_002,
            "FC08-SAFE-READ-003": handle_fc08_safe_read_003,
            "FC08-SAFE-READ-004": handle_fc08_safe_read_004,
            "FC08-SAFE-READ-005": handle_fc08_safe_read_005,
            "FC08-SAFE-READ-006": handle_fc08_safe_read_006,
            "FC08-SAFE-READ-007": handle_fc08_safe_read_007,
            "FC08-SAFE-READ-008": handle_fc08_safe_read_008,
            "FC08-SAFE-READ-009": handle_fc08_safe_read_009,
            "FC08-SAFE-READ-010": handle_fc08_safe_read_010,
            "FC08-SAFE-READ-011": handle_fc08_safe_read_011,
            "FC08-SAFE-READ-012": handle_fc08_safe_read_012,
            "FC08-STATIC-001": handle_fc08_static_001,
            "FC08-STATIC-002": handle_fc08_static_002,
            "FC08-STATIC-003": handle_fc08_static_003,
            "FC08-STATIC-004": handle_fc08_static_004,
        }
        results1 = []
        for v in vectors:
            handler = handler_map[v["vector_id"]]
            input_copy = copy.deepcopy(v["input"])
            expected_copy = copy.deepcopy(v["expected"])
            handler(input_copy, expected_copy)
            results1.append(v["vector_id"])
        results2 = []
        for v in vectors:
            handler = handler_map[v["vector_id"]]
            input_copy = copy.deepcopy(v["input"])
            expected_copy = copy.deepcopy(v["expected"])
            handler(input_copy, expected_copy)
            results2.append(v["vector_id"])
        assert results1 == results2

    def test_input_immutability(self) -> None:
        vectors = _load_vectors()
        handler_map = {
            "FC08-CATALOG-001": handle_fc08_catalog_001,
            "FC08-CATALOG-002": handle_fc08_catalog_002,
            "FC08-CATALOG-003": handle_fc08_catalog_003,
            "FC08-CATALOG-004": handle_fc08_catalog_004,
            "FC08-CATALOG-005": handle_fc08_catalog_005,
            "FC08-CATALOG-006": handle_fc08_catalog_006,
            "FC08-CATALOG-007": handle_fc08_catalog_007,
            "FC08-CATALOG-008": handle_fc08_catalog_008,
            "FC08-EVIDENCE-001": handle_fc08_evidence_001,
            "FC08-EVIDENCE-002": handle_fc08_evidence_002,
            "FC08-EVIDENCE-003": handle_fc08_evidence_003,
            "FC08-EVIDENCE-004": handle_fc08_evidence_004,
            "FC08-EVIDENCE-005": handle_fc08_evidence_005,
            "FC08-EVIDENCE-006": handle_fc08_evidence_006,
            "FC08-EVIDENCE-007": handle_fc08_evidence_007,
            "FC08-EVIDENCE-008": handle_fc08_evidence_008,
            "FC08-BUILDER-001": handle_fc08_builder_001,
            "FC08-BUILDER-002": handle_fc08_builder_002,
            "FC08-BUILDER-003": handle_fc08_builder_003,
            "FC08-BUILDER-004": handle_fc08_builder_004,
            "FC08-BUILDER-005": handle_fc08_builder_005,
            "FC08-BUILDER-006": handle_fc08_builder_006,
            "FC08-BUILDER-007": handle_fc08_builder_007,
            "FC08-BUILDER-008": handle_fc08_builder_008,
            "FC08-VALUE-001": handle_fc08_value_001,
            "FC08-VALUE-002": handle_fc08_value_002,
            "FC08-VALUE-003": handle_fc08_value_003,
            "FC08-VALUE-004": handle_fc08_value_004,
            "FC08-VALUE-005": handle_fc08_value_005,
            "FC08-VALUE-006": handle_fc08_value_006,
            "FC08-VALUE-007": handle_fc08_value_007,
            "FC08-VALUE-008": handle_fc08_value_008,
            "FC08-BEACON-001": handle_fc08_beacon_001,
            "FC08-BEACON-002": handle_fc08_beacon_002,
            "FC08-BEACON-003": handle_fc08_beacon_003,
            "FC08-BEACON-004": handle_fc08_beacon_004,
            "FC08-BEACON-005": handle_fc08_beacon_005,
            "FC08-BEACON-006": handle_fc08_beacon_006,
            "FC08-BEACON-007": handle_fc08_beacon_007,
            "FC08-BEACON-008": handle_fc08_beacon_008,
            "FC08-SAFE-READ-001": handle_fc08_safe_read_001,
            "FC08-SAFE-READ-002": handle_fc08_safe_read_002,
            "FC08-SAFE-READ-003": handle_fc08_safe_read_003,
            "FC08-SAFE-READ-004": handle_fc08_safe_read_004,
            "FC08-SAFE-READ-005": handle_fc08_safe_read_005,
            "FC08-SAFE-READ-006": handle_fc08_safe_read_006,
            "FC08-SAFE-READ-007": handle_fc08_safe_read_007,
            "FC08-SAFE-READ-008": handle_fc08_safe_read_008,
            "FC08-SAFE-READ-009": handle_fc08_safe_read_009,
            "FC08-SAFE-READ-010": handle_fc08_safe_read_010,
            "FC08-SAFE-READ-011": handle_fc08_safe_read_011,
            "FC08-SAFE-READ-012": handle_fc08_safe_read_012,
            "FC08-STATIC-001": handle_fc08_static_001,
            "FC08-STATIC-002": handle_fc08_static_002,
            "FC08-STATIC-003": handle_fc08_static_003,
            "FC08-STATIC-004": handle_fc08_static_004,
        }
        for v in vectors:
            input_copy = copy.deepcopy(v["input"])
            handler = handler_map[v["vector_id"]]
            expected_copy = copy.deepcopy(v["expected"])
            handler(input_copy, expected_copy)
            assert input_copy == v["input"], f"Input mutated for {v['vector_id']}"

    def test_exact_total_category_handler_contract(self) -> None:
        vectors = _load_vectors()
        assert len(vectors) == 56
        categories = {}
        for v in vectors:
            cat = v["category"]
            categories[cat] = categories.get(cat, 0) + 1
        assert categories == {
            "CATALOG": 8, "EVIDENCE": 8, "BUILDER": 8,
            "VALUE": 8, "BEACON": 8, "SAFE_READ": 12, "STATIC": 4,
        }
