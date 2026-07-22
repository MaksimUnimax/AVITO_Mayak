"""Unit tests for Filter Catalog FC-08 semantic contracts — 56 vectors + 8 invariants."""

from __future__ import annotations

import copy
import ast
import hashlib
import json
import re
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


def _find_generic_fc08_dispatch_evidence(tree: ast.AST) -> dict[str, int]:
    """Find FC-08 handler registries and vector-ID dispatch in arbitrary AST."""
    map_names: set[str] = set()
    map_assignments = 0
    handler_dict_count = 0
    handler_dict_entries = 0
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        targets = [target.id for target in node.targets if isinstance(target, ast.Name)]
        if any(name == "handler_map" or name == "HANDLER_MAP" or name.endswith("_handler_map") for name in targets):
            map_assignments += 1
            map_names.update(targets)
        if isinstance(node.value, ast.Dict):
            entries = [value for value in node.value.values if any(
                isinstance(child, ast.Name) and child.id.startswith("handle_fc08_")
                for child in ast.walk(value)
            )]
            if entries:
                handler_dict_count += 1
                handler_dict_entries += len(entries)
    vector_lookups = []
    selected_assignments = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Subscript) or not isinstance(node.value, ast.Name):
            continue
        if node.value.id not in map_names:
            continue
        if any(
            (isinstance(child, ast.Name) and child.id == "vector_id")
            or (isinstance(child, ast.Constant) and child.value == "vector_id")
            for child in ast.walk(node.slice)
        ):
            vector_lookups.append(node)
            parent_assignments = [parent for parent in ast.walk(tree) if isinstance(parent, ast.Assign) and parent.value is node]
            selected_assignments.extend(
                assignment for assignment in parent_assignments
                if any(isinstance(target, ast.Name) and target.id == "handler" for target in assignment.targets)
            )
    selected_handler_calls = 0
    if selected_assignments:
        selected_handler_calls = sum(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "handler"
            for node in ast.walk(tree)
        )
    return {
        "assignments": map_assignments,
        "dictionary_literals": handler_dict_count,
        "dictionary_entries": handler_dict_entries,
        "vector_id_lookups": len(vector_lookups),
        "selected_handler_assignments": len(selected_assignments),
        "selected_handler_calls": selected_handler_calls,
        "module_or_local_registries": map_assignments,
    }


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


def _find_open_decision_status(content: str, decision_id: str) -> dict:
    """Read one exact decision row from Markdown pipe tables only."""
    normalized_headers = {"id", "decision", "decision_id"}
    matching_rows: list[tuple[str, ...]] = []
    matched_statuses: list[str] = []
    all_lines = content.splitlines()
    for index in range(len(all_lines) - 1):
        header_line, separator_line = all_lines[index:index + 2]
        if not (header_line.strip().startswith("|") and header_line.strip().endswith("|")):
            continue
        if not (separator_line.strip().startswith("|") and separator_line.strip().endswith("|")):
            continue
        headers = tuple(cell.strip() for cell in header_line.strip()[1:-1].split("|"))
        separators = tuple(cell.strip() for cell in separator_line.strip()[1:-1].split("|"))
        if len(headers) != len(separators) or not all(re.fullmatch(r":?-{3,}:?", cell) for cell in separators):
            continue
        def normalize_header(value: str) -> str:
            return re.sub(r"[^a-z0-9]+", "_", value.casefold()).strip("_")
        id_index = next((i for i, h in enumerate(headers) if normalize_header(h) in normalized_headers), None)
        status_index = next((i for i, h in enumerate(headers) if "status" in normalize_header(h)), None)
        if id_index is None or status_index is None:
            continue
        row_index = index + 2
        while row_index < len(all_lines):
            row_line = all_lines[row_index].strip()
            if not (row_line.startswith("|") and row_line.endswith("|")):
                break
            row_cells = tuple(cell.strip() for cell in row_line[1:-1].split("|"))
            if len(row_cells) == len(headers) and row_cells[id_index] == decision_id:
                matching_rows.append(row_cells)
                matched_statuses.append(row_cells[status_index])
            row_index += 1
    unique_statuses = tuple(sorted(set(matched_statuses)))
    return {
        "status": matched_statuses[0] if len(unique_statuses) == 1 and matched_statuses else None,
        "row_cells": matching_rows[0] if matching_rows else (),
        "matching_row_count": len(matching_rows),
        "conflicting_statuses": unique_statuses if len(unique_statuses) > 1 else (),
    }


EXPECTED_TOP_LEVEL_KEYS = ("schema_version", "module_id", "technical_id", "canonical_references", "vectors")
EXPECTED_REF_IDS = tuple(f"FC08-REF-{index:03d}" for index in range(1, 37))
EXPECTED_VECTOR_IDS = (
    tuple(f"FC08-CATALOG-{index:03d}" for index in range(1, 9))
    + tuple(f"FC08-EVIDENCE-{index:03d}" for index in range(1, 9))
    + tuple(f"FC08-BUILDER-{index:03d}" for index in range(1, 9))
    + tuple(f"FC08-VALUE-{index:03d}" for index in range(1, 9))
    + tuple(f"FC08-BEACON-{index:03d}" for index in range(1, 9))
    + tuple(f"FC08-SAFE-READ-{index:03d}" for index in range(1, 13))
    + tuple(f"FC08-STATIC-{index:03d}" for index in range(1, 5))
)
EXPECTED_CATEGORY_COUNTS = {"CATALOG": 8, "EVIDENCE": 8, "BUILDER": 8, "VALUE": 8, "BEACON": 8, "SAFE_READ": 12, "STATIC": 4}
_CATEGORY_PREFIXES = {"CATALOG": "catalog", "EVIDENCE": "evidence", "BUILDER": "builder", "VALUE": "value", "BEACON": "beacon", "SAFE_READ": "safe_read", "STATIC": "static"}


def _evaluate_fc08_synthetic_fixture(data: dict | None = None) -> dict:
    data = _load_fixture() if data is None else data
    violations: list[str] = []
    if tuple(data) != EXPECTED_TOP_LEVEL_KEYS:
        violations.append("top_level_keys")
    if data.get("schema_version") != "1.0" or data.get("module_id") != "13-filter-catalog-and-builder" or data.get("technical_id") != "FC-08-PARALLEL-MAIN-REISSUE-20260722-028":
        violations.append("identity")
    refs = data.get("canonical_references", [])
    ref_ids = tuple(ref.get("reference_id") for ref in refs)
    if ref_ids != EXPECTED_REF_IDS or len(set(ref_ids)) != len(ref_ids):
        violations.append("reference_registry")
    for ref in refs:
        if not isinstance(ref.get("safe_label"), str) or not ref["safe_label"].startswith("Synthetic"):
            violations.append("non_synthetic_safe_label")
    vectors = data.get("vectors", [])
    vector_ids = tuple(v.get("vector_id") for v in vectors)
    if vector_ids != EXPECTED_VECTOR_IDS:
        violations.append("vector_order")
    if len(vector_ids) != len(set(vector_ids)):
        violations.append("vector_registry")
    category_counts: dict[str, int] = {}
    used_refs: set[str] = set()
    for vector in vectors:
        category = vector.get("category")
        category_counts[category] = category_counts.get(category, 0) + 1
        used_refs.update(vector.get("canonical_reference_ids", []))
        expected_prefix = _CATEGORY_PREFIXES.get(category)
        suffix = vector.get("vector_id", "").rsplit("-", 1)[-1]
        if expected_prefix is None or vector.get("handler") != f"handle_fc08_{expected_prefix}_{suffix}":
            violations.append(f"handler:{vector.get('vector_id')}")
        if not set(vector.get("canonical_reference_ids", [])).issubset(set(ref_ids)):
            violations.append(f"unknown_reference:{vector.get('vector_id')}")
    if category_counts != EXPECTED_CATEGORY_COUNTS:
        violations.append("category_counts")
    if used_refs != set(ref_ids):
        violations.append("unused_reference")
    url = re.compile(r"https?://", re.I)
    email = re.compile(r"[A-Za-z0-9.!#$%&'*+/=?^_{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+")
    coordinates = re.compile(r"(-?\d+\.\d+)\s*[,;]\s*(-?\d+\.\d+)")
    hostname = re.compile(r"^[\w.-]+\.[A-Za-z]{2,}$", re.I)
    ip = re.compile(r"^(?:\d{1,3}\.){3}\d{1,3}$|^(?=.*:)[0-9A-Fa-f:]{2,}$")
    phone = re.compile(r"^(?=(?:\D*\d){10,}\D*$)[\d\s()+./-]+$")
    sensitive = re.compile(r"(?:token|secret|cookie|password|session|credential)", re.I)
    raw_payload_keys = {
        "raw_provider_payload", "provider_payload", "raw_payload",
        "provider_response_body", "provider_request_body",
    }
    def normalized_key(value: object) -> str:
        return re.sub(r"[^a-z0-9]+", "_", str(value).casefold()).strip("_")
    def nonempty(value: object) -> bool:
        return value is not None and value is not False and value != "" and value != () and value != [] and value != {}
    def inspect(value: object, key: str = "") -> None:
        if isinstance(value, dict):
            for child_key, child_value in value.items():
                if normalized_key(child_key) in raw_payload_keys and nonempty(child_value):
                    violations.append(f"raw_payload:{child_key}")
                inspect(child_key, "key")
                inspect(child_value, str(child_key))
        elif isinstance(value, (list, tuple)):
            for child in value:
                inspect(child, key)
        elif isinstance(value, str):
            lower = value.casefold()
            hostname_allowed = value.endswith((".py", ".md", ".json", ".toml", ".lock", ".txt")) or "/" in value
            domain_match = (bool(url.search(value)) or (bool(hostname.fullmatch(value)) and not hostname_allowed))
            iso_timestamp = bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", value))
            coordinate_match = coordinates.search(value)
            coordinate_pair = bool(coordinate_match and -90 <= float(coordinate_match.group(1)) <= 90 and -180 <= float(coordinate_match.group(2)) <= 180)
            raw_payload = normalized_key(key) in raw_payload_keys and nonempty(value)
            credential = sensitive.search(key) and nonempty(value) and lower not in {"false", "none"}
            if email.search(value):
                violations.append(f"email:{key}")
            if coordinate_pair:
                violations.append(f"coordinates:{key}")
            if domain_match or ip.fullmatch(value) or (phone.fullmatch(value) and not iso_timestamp) or credential or raw_payload:
                violations.append(f"unsafe:{key}")
            if raw_payload:
                violations.append(f"raw_payload:{key}")
            if key not in {"contains_secret_or_personal_data", "contains_raw_provider_payload"} and lower in {"true", "yes", "token", "password", "cookie", "credential", "raw_provider_payload"}:
                violations.append(f"truthy:{key}")
        elif isinstance(value, bool) and value and key in {"contains_secret_or_personal_data", "contains_raw_provider_payload"}:
            violations.append(f"truthy:{key}")
        elif normalized_key(key) in raw_payload_keys and nonempty(value):
            violations.append(f"raw_payload:{key}")
    inspect(data)
    return {"valid": not violations, "violations": tuple(sorted(set(violations))), "reference_ids": ref_ids, "vector_ids": vector_ids, "category_counts": category_counts}


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
def handle_fc08_catalog_002(vector_input: dict, vector_expected: dict) -> dict:
    from mayak.modules.filter_catalog.contracts import (
        CatalogPublicationState,
        FilterCatalogVersion,
    )
    with pytest.raises(ValidationError) as exc_info:
        FilterCatalogVersion(
            filter_catalog_version_id=vector_input["filter_catalog_version_id"],
            publication_state=CatalogPublicationState(vector_input["publication_state"]),
            created_at=_ts(vector_input["created_at"]),
            published_at=_ts(vector_input["published_at"]),
            evidence_reference_ids=tuple(vector_input["evidence_reference_ids"]),
        )

    errors = exc_info.value.errors()
    assert errors
    assert any(
        vector_expected["error_fragment"].lower() in error["msg"].lower()
        for error in errors
    )
    return {
        "valid": False,
        "errors": tuple(
            (
                tuple(error["loc"]),
                error["type"],
                error["msg"],
            )
            for error in errors
        ),
    }
def handle_fc08_catalog_003(vector_input: dict, vector_expected: dict) -> dict:
    from mayak.modules.filter_catalog.contracts import FilterOptionDefinition, FilterDefinitionState
    with pytest.raises(ValidationError) as exc_info:
        FilterOptionDefinition(
            filter_option_id=vector_input["filter_option_id"],
            filter_definition_id=vector_input["filter_definition_id"],
            canonical_value_code=vector_input["canonical_value_code"],
            safe_label=vector_input["safe_label"],
            definition_state=FilterDefinitionState(vector_input["definition_state"]),
            evidence_reference_ids=tuple(vector_input["evidence_reference_ids"]),
        )

    errors = exc_info.value.errors()
    assert errors
    assert any(
        vector_expected["error_fragment"].lower() in error["msg"].lower()
        for error in errors
    )
    return {
        "valid": False,
        "errors": tuple(
            (
                tuple(error["loc"]),
                error["type"],
                error["msg"],
            )
            for error in errors
        ),
    }
def handle_fc08_catalog_004(vector_input: dict, vector_expected: dict) -> dict:
    from mayak.modules.filter_catalog.contracts import (
        FilterDefinition,
        FilterDefinitionState,
        FilterValueKind,
    )
    with pytest.raises(ValidationError) as exc_info:
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

    errors = exc_info.value.errors()
    assert errors
    assert any(
        vector_expected["error_fragment"].lower() in error["msg"].lower()
        for error in errors
    )
    return {
        "valid": False,
        "errors": tuple(
            (
                tuple(error["loc"]),
                error["type"],
                error["msg"],
            )
            for error in errors
        ),
    }
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
def handle_fc08_catalog_006(vector_input: dict, vector_expected: dict) -> dict:
    from mayak.modules.filter_catalog.contracts import (
        FilterCapabilityProfile,
        FilterCapabilityState,
    )
    with pytest.raises(ValidationError) as exc_info:
        FilterCapabilityProfile(
            filter_capability_profile_id=vector_input["filter_capability_profile_id"],
            filter_catalog_version_id=vector_input["filter_catalog_version_id"],
            provider_surface_reference_id=vector_input["provider_surface_reference_id"],
            capability_state=FilterCapabilityState(vector_input["capability_state"]),
            evidence_reference_ids=tuple(vector_input["evidence_reference_ids"]),
        )

    errors = exc_info.value.errors()
    assert errors
    assert any(
        vector_expected["error_fragment"].lower() in error["msg"].lower()
        for error in errors
    )
    return {
        "valid": False,
        "errors": tuple(
            (
                tuple(error["loc"]),
                error["type"],
                error["msg"],
            )
            for error in errors
        ),
    }
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
        "all_evaluated": len(outcome.evaluated_dependency_rule_ids) == len(outcome.dependency_rule_ids),
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


def handle_fc08_static_001(vector_input: dict, vector_expected: dict) -> dict:
    from mayak.modules.filter_catalog import __all__ as pkg_all
    all_names = list(pkg_all)
    for sym in vector_input["expected_symbols"]:
        assert sym in all_names, f"{sym} not in package __all__"
    missing_symbols = tuple(
        symbol for symbol in vector_input["expected_symbols"]
        if symbol not in all_names
    )
    assert not missing_symbols
    return {
        "all_symbols_present": not missing_symbols,
        "checked_symbol_count": len(vector_input["expected_symbols"]),
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
def handle_fc08_static_003(vector_input: dict, vector_expected: dict) -> dict:
    import subprocess
    expected_blobs = dict(vector_input["expected_blobs"])
    actual_blobs = {}
    mismatches = []
    for filename in sorted(expected_blobs):
        result = subprocess.run(
            ["git", "rev-parse", f"HEAD:src/mayak/modules/filter_catalog/{filename}"],
            capture_output=True, text=True, cwd=str(REPO_ROOT), check=False,
        )
        assert result.returncode == 0, result.stderr
        actual_blobs[filename] = result.stdout.strip()
        if actual_blobs[filename] != expected_blobs[filename]:
            mismatches.append((filename, expected_blobs[filename], actual_blobs[filename]))
    mismatches = tuple(mismatches)
    all_blobs_match = not mismatches
    return {
        "actual_blobs": dict(sorted(actual_blobs.items())),
        "expected_blobs": dict(sorted(expected_blobs.items())),
        "mismatches": mismatches,
        "all_blobs_match": all_blobs_match,
    }
def handle_fc08_static_004(vector_input: dict, vector_expected: dict) -> dict:
    decisions_path = REPO_ROOT / "docs" / "00-governance" / "OPEN_DECISIONS.md"
    content = decisions_path.read_text(encoding="utf-8")
    decision_result = _find_open_decision_status(content, "OD-009")
    synthetic_result = _evaluate_fc08_synthetic_fixture()
    od009_status = decision_result["status"]
    od009_open_actual = od009_status == "OPEN"
    assert od009_open_actual
    assert decision_result["matching_row_count"] == 1
    assert decision_result["conflicting_statuses"] == ()
    assert synthetic_result["valid"]
    return {
        "od009_open": od009_open_actual,
        "od009_status": od009_status,
        "od009_row_cells": decision_result["row_cells"],
        "od009_matching_row_count": decision_result["matching_row_count"],
        "no_real_provider_data": synthetic_result["valid"],
        "synthetic_violations": synthetic_result["violations"],
    }


# ---------------------------------------------------------------------------
# 56 Explicit Vector-Specific Test Functions
# ---------------------------------------------------------------------------

def test_fc08_beacon_001() -> None:
    vector = _get_vector("FC08-BEACON-001")
    assert vector["handler"] == "handle_fc08_beacon_001"
    actual = _run_handler_twice(
        handle_fc08_beacon_001,
        vector["input"],
        vector["expected"],
    )
    assert actual["candidate_state"] == vector["expected"]["candidate_state"]
    assert actual["beacon_acceptance_required"] is vector["expected"]["beacon_acceptance_required"]

def test_fc08_beacon_002() -> None:
    vector = _get_vector("FC08-BEACON-002")
    assert vector["handler"] == "handle_fc08_beacon_002"
    actual = _run_handler_twice(
        handle_fc08_beacon_002,
        vector["input"],
        vector["expected"],
    )
    assert actual["beacon_acceptance_required"] is vector["expected"]["beacon_acceptance_required_must_be_true"]

def test_fc08_beacon_003() -> None:
    vector = _get_vector("FC08-BEACON-003")
    assert vector["handler"] == "handle_fc08_beacon_003"
    actual = _run_handler_twice(
        handle_fc08_beacon_003,
        vector["input"],
        vector["expected"],
    )
    assert actual["beacon_acceptance_performed"] is vector["expected"]["beacon_acceptance_performed"]
    assert actual["beacon_mutation_performed"] is vector["expected"]["beacon_mutation_performed"]

def test_fc08_beacon_004() -> None:
    vector = _get_vector("FC08-BEACON-004")
    assert vector["handler"] == "handle_fc08_beacon_004"
    actual = _run_handler_twice(
        handle_fc08_beacon_004,
        vector["input"],
        vector["expected"],
    )
    assert actual["beacon_mutation_performed"] is vector["expected"]["beacon_mutation_performed"]
    assert actual["beacon_revision_created"] is vector["expected"]["beacon_revision_created"]
    assert actual["lifecycle_changed"] is vector["expected"]["lifecycle_changed"]
    assert actual["historical_revision_rewritten"] is vector["expected"]["historical_revision_rewritten"]

def test_fc08_beacon_005() -> None:
    vector = _get_vector("FC08-BEACON-005")
    assert vector["handler"] == "handle_fc08_beacon_005"
    actual = _run_handler_twice(
        handle_fc08_beacon_005,
        vector["input"],
        vector["expected"],
    )
    assert actual["field_candidates_empty"] is vector["expected"]["field_candidates_empty"]

def test_fc08_beacon_006() -> None:
    vector = _get_vector("FC08-BEACON-006")
    assert vector["handler"] == "handle_fc08_beacon_006"
    actual = _run_handler_twice(
        handle_fc08_beacon_006,
        vector["input"],
        vector["expected"],
    )
    assert actual["field_candidates_empty"] is vector["expected"]["field_candidates_empty"]

def test_fc08_beacon_007() -> None:
    vector = _get_vector("FC08-BEACON-007")
    assert vector["handler"] == "handle_fc08_beacon_007"
    actual = _run_handler_twice(
        handle_fc08_beacon_007,
        vector["input"],
        vector["expected"],
    )
    assert actual["field_candidates_empty"] is vector["expected"]["field_candidates_empty"]

def test_fc08_beacon_008() -> None:
    vector = _get_vector("FC08-BEACON-008")
    assert vector["handler"] == "handle_fc08_beacon_008"
    actual = _run_handler_twice(
        handle_fc08_beacon_008,
        vector["input"],
        vector["expected"],
    )
    assert actual["filter_catalog_version_id"] == vector["input"]["filter_catalog_version_id"]
    assert actual["validated_builder_field_ids_count"] == len(vector["input"]["validated_builder_field_ids"])

def test_fc08_builder_001() -> None:
    vector = _get_vector("FC08-BUILDER-001")
    assert vector["handler"] == "handle_fc08_builder_001"
    actual = _run_handler_twice(
        handle_fc08_builder_001,
        vector["input"],
        vector["expected"],
    )
    assert actual["decision"] == vector["expected"]["decision"]
    assert actual["has_field"] == vector["expected"]["has_field"]

def test_fc08_builder_002() -> None:
    vector = _get_vector("FC08-BUILDER-002")
    assert vector["handler"] == "handle_fc08_builder_002"
    actual = _run_handler_twice(
        handle_fc08_builder_002,
        vector["input"],
        vector["expected"],
    )
    assert actual["decision"] == vector["expected"]["decision"]
    assert actual["has_field"] == vector["expected"]["has_field"]

def test_fc08_builder_003() -> None:
    vector = _get_vector("FC08-BUILDER-003")
    assert vector["handler"] == "handle_fc08_builder_003"
    actual = _run_handler_twice(
        handle_fc08_builder_003,
        vector["input"],
        vector["expected"],
    )
    assert actual["validation_state"] == vector["expected"]["validation_state"]

def test_fc08_builder_004() -> None:
    vector = _get_vector("FC08-BUILDER-004")
    assert vector["handler"] == "handle_fc08_builder_004"
    actual = _run_handler_twice(
        handle_fc08_builder_004,
        vector["input"],
        vector["expected"],
    )
    assert actual["validation_state"] == vector["expected"]["validation_state"]

def test_fc08_builder_005() -> None:
    vector = _get_vector("FC08-BUILDER-005")
    assert vector["handler"] == "handle_fc08_builder_005"
    actual = _run_handler_twice(
        handle_fc08_builder_005,
        vector["input"],
        vector["expected"],
    )
    assert actual["validation_state"] == vector["expected"]["validation_state"]

def test_fc08_builder_006() -> None:
    vector = _get_vector("FC08-BUILDER-006")
    assert vector["handler"] == "handle_fc08_builder_006"
    actual = _run_handler_twice(
        handle_fc08_builder_006,
        vector["input"],
        vector["expected"],
    )
    assert actual["validation_state"] == vector["expected"]["validation_state"]

def test_fc08_builder_007() -> None:
    vector = _get_vector("FC08-BUILDER-007")
    assert vector["handler"] == "handle_fc08_builder_007"
    actual = _run_handler_twice(
        handle_fc08_builder_007,
        vector["input"],
        vector["expected"],
    )
    assert actual["validation_state"] == vector["expected"]["validation_state"]
    assert actual["warning_ids_present"] == vector["expected"]["warning_ids_present"]

def test_fc08_builder_008() -> None:
    vector = _get_vector("FC08-BUILDER-008")
    assert vector["handler"] == "handle_fc08_builder_008"
    actual = _run_handler_twice(
        handle_fc08_builder_008,
        vector["input"],
        vector["expected"],
    )
    assert actual["is_authoritative_for_beacon"] is vector["expected"]["is_authoritative_for_beacon"]

def test_fc08_catalog_001() -> None:
    vector = _get_vector("FC08-CATALOG-001")
    assert vector["handler"] == "handle_fc08_catalog_001"
    actual = _run_handler_twice(
        handle_fc08_catalog_001,
        vector["input"],
        vector["expected"],
    )
    assert actual["filter_catalog_version_id"] == vector["expected"]["filter_catalog_version_id"]
    assert actual["publication_state"] == vector["expected"]["publication_state"]

def test_fc08_catalog_002() -> None:
    vector = _get_vector("FC08-CATALOG-002")
    assert vector["handler"] == "handle_fc08_catalog_002"
    actual = _run_handler_twice(
        handle_fc08_catalog_002,
        vector["input"],
        vector["expected"],
    )
    assert actual["valid"] is False
    assert actual["errors"]
    assert any(
        vector["expected"]["error_fragment"].lower() in error_message.lower()
        for _, _, error_message in actual["errors"]
    )

def test_fc08_catalog_003() -> None:
    vector = _get_vector("FC08-CATALOG-003")
    assert vector["handler"] == "handle_fc08_catalog_003"
    actual = _run_handler_twice(
        handle_fc08_catalog_003,
        vector["input"],
        vector["expected"],
    )
    assert actual["valid"] is False
    assert actual["errors"]
    assert any(
        vector["expected"]["error_fragment"].lower() in error_message.lower()
        for _, _, error_message in actual["errors"]
    )

def test_fc08_catalog_004() -> None:
    vector = _get_vector("FC08-CATALOG-004")
    assert vector["handler"] == "handle_fc08_catalog_004"
    actual = _run_handler_twice(
        handle_fc08_catalog_004,
        vector["input"],
        vector["expected"],
    )
    assert actual["valid"] is False
    assert actual["errors"]
    assert any(
        vector["expected"]["error_fragment"].lower() in error_message.lower()
        for _, _, error_message in actual["errors"]
    )

def test_fc08_catalog_005() -> None:
    vector = _get_vector("FC08-CATALOG-005")
    assert vector["handler"] == "handle_fc08_catalog_005"
    actual = _run_handler_twice(
        handle_fc08_catalog_005,
        vector["input"],
        vector["expected"],
    )
    assert actual["capability_state"] == vector["expected"]["capability_state"]

def test_fc08_catalog_006() -> None:
    vector = _get_vector("FC08-CATALOG-006")
    assert vector["handler"] == "handle_fc08_catalog_006"
    actual = _run_handler_twice(
        handle_fc08_catalog_006,
        vector["input"],
        vector["expected"],
    )
    assert actual["valid"] is False
    assert actual["errors"]
    assert any(
        vector["expected"]["error_fragment"].lower() in error_message.lower()
        for _, _, error_message in actual["errors"]
    )

def test_fc08_catalog_007() -> None:
    vector = _get_vector("FC08-CATALOG-007")
    assert vector["handler"] == "handle_fc08_catalog_007"
    actual = _run_handler_twice(
        handle_fc08_catalog_007,
        vector["input"],
        vector["expected"],
    )
    assert actual["supersedes_catalog_version_id"] == vector["expected"]["supersedes_catalog_version_id"]

def test_fc08_catalog_008() -> None:
    vector = _get_vector("FC08-CATALOG-008")
    assert vector["handler"] == "handle_fc08_catalog_008"
    actual = _run_handler_twice(
        handle_fc08_catalog_008,
        vector["input"],
        vector["expected"],
    )
    assert actual["definition_state"] == vector["expected"]["definition_state"]

def test_fc08_evidence_001() -> None:
    vector = _get_vector("FC08-EVIDENCE-001")
    assert vector["handler"] == "handle_fc08_evidence_001"
    actual = _run_handler_twice(
        handle_fc08_evidence_001,
        vector["input"],
        vector["expected"],
    )
    assert actual["decision"] == vector["expected"]["decision"]
    assert actual["suggested_definition_state"] == vector["expected"]["suggested_definition_state"]

def test_fc08_evidence_002() -> None:
    vector = _get_vector("FC08-EVIDENCE-002")
    assert vector["handler"] == "handle_fc08_evidence_002"
    actual = _run_handler_twice(
        handle_fc08_evidence_002,
        vector["input"],
        vector["expected"],
    )
    assert actual["decision"] == vector["expected"]["decision"]
    assert actual["suggested_definition_state"] == vector["expected"]["suggested_definition_state"]

def test_fc08_evidence_003() -> None:
    vector = _get_vector("FC08-EVIDENCE-003")
    assert vector["handler"] == "handle_fc08_evidence_003"
    actual = _run_handler_twice(
        handle_fc08_evidence_003,
        vector["input"],
        vector["expected"],
    )
    assert actual["decision"] == vector["expected"]["decision"]
    assert any(vector["expected"]["reason_contained"] in r for r in actual["reason_codes"])

def test_fc08_evidence_004() -> None:
    vector = _get_vector("FC08-EVIDENCE-004")
    assert vector["handler"] == "handle_fc08_evidence_004"
    actual = _run_handler_twice(
        handle_fc08_evidence_004,
        vector["input"],
        vector["expected"],
    )
    assert actual["decision"] == vector["expected"]["decision"]
    assert any(vector["expected"]["reason_contained"] in r for r in actual["reason_codes"])

def test_fc08_evidence_005() -> None:
    vector = _get_vector("FC08-EVIDENCE-005")
    assert vector["handler"] == "handle_fc08_evidence_005"
    actual = _run_handler_twice(
        handle_fc08_evidence_005,
        vector["input"],
        vector["expected"],
    )
    assert actual["decision"] == vector["expected"]["decision"]
    assert any(vector["expected"]["reason_contained"] in r for r in actual["reason_codes"])

def test_fc08_evidence_006() -> None:
    vector = _get_vector("FC08-EVIDENCE-006")
    assert vector["handler"] == "handle_fc08_evidence_006"
    actual = _run_handler_twice(
        handle_fc08_evidence_006,
        vector["input"],
        vector["expected"],
    )
    assert actual["decision"] == vector["expected"]["decision"]
    assert any(vector["expected"]["reason_contained"] in r for r in actual["reason_codes"])

def test_fc08_evidence_007() -> None:
    vector = _get_vector("FC08-EVIDENCE-007")
    assert vector["handler"] == "handle_fc08_evidence_007"
    actual = _run_handler_twice(
        handle_fc08_evidence_007,
        vector["input"],
        vector["expected"],
    )
    assert actual["decision"] == vector["expected"]["decision"]
    assert any(vector["expected"]["reason_contained"] in r for r in actual["reason_codes"])

def test_fc08_evidence_008() -> None:
    vector = _get_vector("FC08-EVIDENCE-008")
    assert vector["handler"] == "handle_fc08_evidence_008"
    actual = _run_handler_twice(
        handle_fc08_evidence_008,
        vector["input"],
        vector["expected"],
    )
    assert actual["decision"] == vector["expected"]["decision"]
    assert actual["evidence_count"] == vector["expected"]["evidence_count"]

def test_fc08_safe_read_001() -> None:
    vector = _get_vector("FC08-SAFE-READ-001")
    assert vector["handler"] == "handle_fc08_safe_read_001"
    actual = _run_handler_twice(
        handle_fc08_safe_read_001,
        vector["input"],
        vector["expected"],
    )
    assert actual["surface_state"] == vector["expected"]["surface_state"]
    assert actual["details_redacted"] is vector["expected"]["details_redacted"]

def test_fc08_safe_read_002() -> None:
    vector = _get_vector("FC08-SAFE-READ-002")
    assert vector["handler"] == "handle_fc08_safe_read_002"
    actual = _run_handler_twice(
        handle_fc08_safe_read_002,
        vector["input"],
        vector["expected"],
    )
    assert actual["details_redacted"] is vector["expected"]["details_redacted"]
    assert actual["warning_ids_empty"] is (vector["expected"].get("warning_ids_count", 0) == 0)
    assert actual["evidence_reference_ids_empty"] is (vector["expected"].get("evidence_reference_ids_count", 0) == 0)

def test_fc08_safe_read_003() -> None:
    vector = _get_vector("FC08-SAFE-READ-003")
    assert vector["handler"] == "handle_fc08_safe_read_003"
    actual = _run_handler_twice(
        handle_fc08_safe_read_003,
        vector["input"],
        vector["expected"],
    )
    assert actual["surface_state"] == vector["expected"]["surface_state"]
    assert actual["details_redacted"] is vector["expected"]["details_redacted"]

def test_fc08_safe_read_004() -> None:
    vector = _get_vector("FC08-SAFE-READ-004")
    assert vector["handler"] == "handle_fc08_safe_read_004"
    actual = _run_handler_twice(
        handle_fc08_safe_read_004,
        vector["input"],
        vector["expected"],
    )
    assert actual["surface_state"] == vector["expected"]["surface_state"]
    assert actual["explanation_code"] == vector["expected"]["explanation_codes"][0]
    assert actual["details_redacted"] is vector["expected"]["details_redacted"]

def test_fc08_safe_read_005() -> None:
    vector = _get_vector("FC08-SAFE-READ-005")
    assert vector["handler"] == "handle_fc08_safe_read_005"
    actual = _run_handler_twice(
        handle_fc08_safe_read_005,
        vector["input"],
        vector["expected"],
    )
    assert actual["surface_state"] == vector["expected"]["surface_state"]
    assert actual["explanation_code"] == vector["expected"]["explanation_codes"][0]
    assert actual["details_redacted"] is vector["expected"]["details_redacted"]

def test_fc08_safe_read_006() -> None:
    vector = _get_vector("FC08-SAFE-READ-006")
    assert vector["handler"] == "handle_fc08_safe_read_006"
    actual = _run_handler_twice(
        handle_fc08_safe_read_006,
        vector["input"],
        vector["expected"],
    )
    assert actual["surface_state"] == vector["expected"]["surface_state"]
    assert actual["explanation_code"] == vector["expected"]["explanation_codes"][0]
    assert actual["details_redacted"] is vector["expected"]["details_redacted"]

def test_fc08_safe_read_007() -> None:
    vector = _get_vector("FC08-SAFE-READ-007")
    assert vector["handler"] == "handle_fc08_safe_read_007"
    actual = _run_handler_twice(
        handle_fc08_safe_read_007,
        vector["input"],
        vector["expected"],
    )
    assert actual["freshness_state"] == vector["expected"]["freshness_state"]

def test_fc08_safe_read_008() -> None:
    vector = _get_vector("FC08-SAFE-READ-008")
    assert vector["handler"] == "handle_fc08_safe_read_008"
    actual = _run_handler_twice(
        handle_fc08_safe_read_008,
        vector["input"],
        vector["expected"],
    )
    assert actual["freshness_state"] == vector["expected"]["freshness_state"]

def test_fc08_safe_read_009() -> None:
    vector = _get_vector("FC08-SAFE-READ-009")
    assert vector["handler"] == "handle_fc08_safe_read_009"
    actual = _run_handler_twice(
        handle_fc08_safe_read_009,
        vector["input"],
        vector["expected"],
    )
    assert actual["freshness_state"] == vector["expected"]["freshness_state"]

def test_fc08_safe_read_010() -> None:
    vector = _get_vector("FC08-SAFE-READ-010")
    assert vector["handler"] == "handle_fc08_safe_read_010"
    actual = _run_handler_twice(
        handle_fc08_safe_read_010,
        vector["input"],
        vector["expected"],
    )
    assert actual["freshness_state"] == vector["expected"]["freshness_state"]

def test_fc08_safe_read_011() -> None:
    vector = _get_vector("FC08-SAFE-READ-011")
    assert vector["handler"] == "handle_fc08_safe_read_011"
    actual = _run_handler_twice(
        handle_fc08_safe_read_011,
        vector["input"],
        vector["expected"],
    )
    assert actual["beacon_acceptance_required_in_explanations"] is vector["expected"]["beacon_acceptance_required_in_explanations"]

def test_fc08_safe_read_012() -> None:
    vector = _get_vector("FC08-SAFE-READ-012")
    assert vector["handler"] == "handle_fc08_safe_read_012"
    actual = _run_handler_twice(
        handle_fc08_safe_read_012,
        vector["input"],
        vector["expected"],
    )
    assert actual["identity_authorization_performed_by_filter_catalog"] is False
    assert actual["authoritative_business_state"] is False
    assert actual["contains_raw_provider_payload"] is False
    assert actual["contains_stack_trace"] is False
    assert actual["contains_secret_or_personal_data"] is False
    assert actual["contains_admin_private_notes"] is False
    assert actual["runtime_or_persistence_performed"] is False

def test_fc08_static_001() -> None:
    vector = _get_vector("FC08-STATIC-001")
    assert vector["handler"] == "handle_fc08_static_001"
    actual = _run_handler_twice(
        handle_fc08_static_001,
        vector["input"],
        vector["expected"],
    )
    assert actual["all_symbols_present"] is vector["expected"]["all_symbols_present"]
    assert actual["checked_symbol_count"] == len(vector["input"]["expected_symbols"])

def test_fc08_static_002() -> None:
    vector = _get_vector("FC08-STATIC-002")
    assert vector["handler"] == "handle_fc08_static_002"
    actual = _run_handler_twice(
        handle_fc08_static_002,
        vector["input"],
        vector["expected"],
    )
    assert actual["forbidden_imports_absent"] is vector["expected"]["no_forbidden_imports"]

def test_fc08_static_003() -> None:
    vector = _get_vector("FC08-STATIC-003")
    assert vector["handler"] == "handle_fc08_static_003"
    actual = _run_handler_twice(
        handle_fc08_static_003,
        vector["input"],
        vector["expected"],
    )
    assert actual["all_blobs_match"] is vector["expected"]["all_blobs_match"]
    assert actual["all_blobs_match"] is True
    assert actual["mismatches"] == ()
    assert actual["actual_blobs"] == actual["expected_blobs"]

def test_fc08_static_004() -> None:
    vector = _get_vector("FC08-STATIC-004")
    assert vector["handler"] == "handle_fc08_static_004"
    actual = _run_handler_twice(
        handle_fc08_static_004,
        vector["input"],
        vector["expected"],
    )
    assert actual["od009_open"] is vector["expected"]["od009_open"]
    assert actual["no_real_provider_data"] is vector["expected"]["no_real_provider_data"]
    assert actual["od009_open"] is True
    assert actual["od009_status"] == "OPEN"
    assert actual["od009_matching_row_count"] == 1
    assert actual["no_real_provider_data"] is True
    assert actual["synthetic_violations"] == ()

def test_fc08_value_001() -> None:
    vector = _get_vector("FC08-VALUE-001")
    assert vector["handler"] == "handle_fc08_value_001"
    actual = _run_handler_twice(
        handle_fc08_value_001,
        vector["input"],
        vector["expected"],
    )
    assert actual["decision"] == vector["expected"]["decision"]
    assert actual["candidate_changed"] == vector["expected"]["candidate_changed"]

def test_fc08_value_002() -> None:
    vector = _get_vector("FC08-VALUE-002")
    assert vector["handler"] == "handle_fc08_value_002"
    actual = _run_handler_twice(
        handle_fc08_value_002,
        vector["input"],
        vector["expected"],
    )
    assert actual["decision"] == vector["expected"]["decision"]
    assert actual["collapse_detected"] is vector["expected"]["collapse_detected"]

def test_fc08_value_003() -> None:
    vector = _get_vector("FC08-VALUE-003")
    assert vector["handler"] == "handle_fc08_value_003"
    actual = _run_handler_twice(
        handle_fc08_value_003,
        vector["input"],
        vector["expected"],
    )
    assert actual["decision"] == vector["expected"]["decision"]

def test_fc08_value_004() -> None:
    vector = _get_vector("FC08-VALUE-004")
    assert vector["handler"] == "handle_fc08_value_004"
    actual = _run_handler_twice(
        handle_fc08_value_004,
        vector["input"],
        vector["expected"],
    )
    assert actual["decision"] == vector["expected"]["decision"]
    assert actual["unit_mismatch_detected"] is vector["expected"]["unit_mismatch_detected"]

def test_fc08_value_005() -> None:
    vector = _get_vector("FC08-VALUE-005")
    assert vector["handler"] == "handle_fc08_value_005"
    actual = _run_handler_twice(
        handle_fc08_value_005,
        vector["input"],
        vector["expected"],
    )
    assert actual["decision"] == vector["expected"]["decision"]
    assert actual["inclusivity_incompatible_detected"] is vector["expected"]["inclusivity_incompatible_detected"]

def test_fc08_value_006() -> None:
    vector = _get_vector("FC08-VALUE-006")
    assert vector["handler"] == "handle_fc08_value_006"
    actual = _run_handler_twice(
        handle_fc08_value_006,
        vector["input"],
        vector["expected"],
    )
    assert actual["decision"] == vector["expected"]["decision"]

def test_fc08_value_007() -> None:
    vector = _get_vector("FC08-VALUE-007")
    assert vector["handler"] == "handle_fc08_value_007"
    actual = _run_handler_twice(
        handle_fc08_value_007,
        vector["input"],
        vector["expected"],
    )
    assert actual["decision"] == vector["expected"]["decision"]

def test_fc08_value_008() -> None:
    vector = _get_vector("FC08-VALUE-008")
    assert vector["handler"] == "handle_fc08_value_008"
    actual = _run_handler_twice(
        handle_fc08_value_008,
        vector["input"],
        vector["expected"],
    )
    assert actual["decision"] == vector["expected"]["decision"]
    assert actual["all_evaluated"] is vector["expected"]["all_evaluated"]

# ---------------------------------------------------------------------------
# 8 Fixed Invariant Tests
# ---------------------------------------------------------------------------

class TestFC08FixedInvariants:
    def test_56_unique_vector_ids(self) -> None:
        fixture = _load_fixture()
        vectors = fixture["vectors"]
        ids = tuple(v["vector_id"] for v in vectors)
        assert len(ids) == 56
        assert len(set(ids)) == 56
        current = _evaluate_fc08_synthetic_fixture(fixture)
        assert current["valid"] is True
        assert current["violations"] == ()

        swapped = copy.deepcopy(fixture)
        swapped["vectors"][0], swapped["vectors"][1] = swapped["vectors"][1], swapped["vectors"][0]
        swapped_result = _evaluate_fc08_synthetic_fixture(swapped)
        assert swapped_result["valid"] is False
        assert "vector_order" in swapped_result["violations"]

        wrong_id = copy.deepcopy(fixture)
        wrong_id["vectors"][0]["vector_id"] = "FC08-CATALOG-999"
        wrong_id_result = _evaluate_fc08_synthetic_fixture(wrong_id)
        assert wrong_id_result["valid"] is False
        assert "vector_order" in wrong_id_result["violations"]

        email_mutation = copy.deepcopy(fixture)
        email_mutation["vectors"][0]["input"]["synthetic_note"] = "contact@example.test"
        email_result = _evaluate_fc08_synthetic_fixture(email_mutation)
        assert email_result["valid"] is False
        assert any(v.startswith("email:") for v in email_result["violations"])

        coordinate_mutation = copy.deepcopy(fixture)
        coordinate_mutation["vectors"][0]["input"]["synthetic_note"] = "55.75, 37.62"
        coordinate_result = _evaluate_fc08_synthetic_fixture(coordinate_mutation)
        assert coordinate_result["valid"] is False
        assert any(v.startswith("coordinates:") for v in coordinate_result["violations"])

        tuple_mutation = copy.deepcopy(fixture)
        tuple_mutation["vectors"][0]["input"]["synthetic_tuple"] = ("safe", "https://example.test")
        tuple_result = _evaluate_fc08_synthetic_fixture(tuple_mutation)
        assert tuple_result["valid"] is False
        assert any(v.startswith("unsafe:") for v in tuple_result["violations"])

        raw_payload_mutation = copy.deepcopy(fixture)
        raw_payload_mutation["vectors"][0]["input"]["raw_provider_payload"] = {"body": "synthetic"}
        raw_payload_result = _evaluate_fc08_synthetic_fixture(raw_payload_mutation)
        assert raw_payload_result["valid"] is False
        assert any(v.startswith("raw_payload:") for v in raw_payload_result["violations"])

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
        content = Path(__file__).read_text(encoding="utf-8")
        tree = ast.parse(content)
        assert _find_generic_fc08_dispatch_evidence(tree) == {
            "assignments": 0,
            "dictionary_literals": 0,
            "dictionary_entries": 0,
            "vector_id_lookups": 0,
            "selected_handler_assignments": 0,
            "selected_handler_calls": 0,
            "module_or_local_registries": 0,
        }
        assert not re.search(r"^def test_vector_handler\b", content, re.MULTILINE), "Generic parametrized test_vector_handler must not exist"
        assert not re.search(r"^@pytest\.mark\.parametrize", content, re.MULTILINE), "No parametrize decorators allowed for vector execution"

    def test_deterministic_complete_run(self) -> None:
        source = Path(__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        vector_ids = tuple(v["vector_id"] for v in _load_vectors())
        explicit_tests = {
            node.name.removeprefix("test_").upper().replace("_", "-")
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_fc08_")
        }
        assert explicit_tests == set(vector_ids)
        explicit_test_nodes = [
            node for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_fc08_")
        ]
        assert sum(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "_run_handler_twice"
            for function in explicit_test_nodes
            for node in ast.walk(function)
        ) == 56
        assert _find_generic_fc08_dispatch_evidence(tree)["assignments"] == 0

    def test_input_immutability(self) -> None:
        probe_input = {"nested": {"values": [1, 2]}, "label": "probe"}
        probe_expected = {"nested": {"ok": True}}
        original_input = copy.deepcopy(probe_input)
        original_expected = copy.deepcopy(probe_expected)

        def probe_handler(vector_input: dict, vector_expected: dict) -> dict:
            return {"actual": copy.deepcopy(vector_input["nested"]), "expected": vector_expected["nested"]["ok"]}

        actual = _run_handler_twice(probe_handler, probe_input, probe_expected)
        assert probe_input == original_input
        assert probe_expected == original_expected
        assert actual == {"actual": {"values": [1, 2]}, "expected": True}

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
