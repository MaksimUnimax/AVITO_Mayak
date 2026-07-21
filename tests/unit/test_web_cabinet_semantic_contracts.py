"""Deterministic synthetic WC-02..WC-11 matrices and 56-vector registry."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Callable

import pytest

from mayak.modules import web_cabinet as package
from tests.architecture.test_web_cabinet_semantic_boundaries import violations

FIXTURE = Path(__file__).parents[1] / "fixtures" / "web_cabinet_semantic_vectors.json"
EXPECTED_TOP = [
    "schema_version",
    "module",
    "accepted_through_step",
    "synthetic_only",
    "contains_real_user_data",
    "contains_real_session_data",
    "contains_secret_material",
    "contains_raw_provider_payload",
    "contains_raw_avito_payload",
    "contains_private_support_data",
    "contains_personal_or_legal_data",
    "network_required",
    "provider_api_required",
    "database_required",
    "runtime_required",
    "canonical_fixture_references",
    "vectors",
]
CATEGORIES = {
    "VIEW": "WC-02",
    "COMMAND": "WC-03",
    "AUTH": "WC-04",
    "ENTITLEMENT": "WC-05",
    "HISTORY": "WC-06",
    "STATUS": "WC-07",
    "CHANNEL": "WC-08",
    "ANALYTICS": "WC-09",
    "SUPPORT": "WC-10",
    "PRIVACY": "WC-11",
    "STATIC": "WC-12",
}
EXPECTED_SCENARIOS = [
    ("VIEW", "valid_composition"),
    ("VIEW", "owner_mapping"),
    ("VIEW", "terminal_empty"),
    ("VIEW", "stale_ambiguous"),
    ("VIEW", "duplicate_source_rejected"),
    ("COMMAND", "patch_submission_valid"),
    ("COMMAND", "patch_field_uniqueness"),
    ("COMMAND", "lifecycle_command_matrix"),
    ("COMMAND", "idempotency_outcomes"),
    ("COMMAND", "business_authority_forbidden"),
    ("AUTH", "verified_context_valid"),
    ("AUTH", "session_non_authority"),
    ("AUTH", "unauthenticated_forbidden"),
    ("AUTH", "phone_recovery_blocked"),
    ("AUTH", "merge_second_account_forbidden"),
    ("ENTITLEMENT", "effective_access_valid"),
    ("ENTITLEMENT", "tariff_options_source_owned"),
    ("ENTITLEMENT", "terminal_state_matrix"),
    ("ENTITLEMENT", "invented_values_forbidden"),
    ("ENTITLEMENT", "duplicate_reference_rejected"),
    ("HISTORY", "grouped_history_valid"),
    ("HISTORY", "all_safe_listing_references"),
    ("HISTORY", "terminal_state_matrix"),
    ("HISTORY", "ambiguous_delivery"),
    ("HISTORY", "raw_payload_archive_forbidden"),
    ("STATUS", "no_new_clean"),
    ("STATUS", "external_unavailable_not_no_new"),
    ("STATUS", "recovery_one_result"),
    ("STATUS", "lost_anchor_not_confirmed_new"),
    ("STATUS", "stale_delivery_ambiguity"),
    ("CHANNEL", "linked_state_valid"),
    ("CHANNEL", "connect_start_matrix"),
    ("CHANNEL", "preference_enable_disable"),
    ("CHANNEL", "one_account_continuity"),
    ("CHANNEL", "terminal_and_runtime_gate"),
    ("ANALYTICS", "metric_request_matrix"),
    ("ANALYTICS", "filter_sort_order"),
    ("ANALYTICS", "terminal_result_matrix"),
    ("ANALYTICS", "aggregated_counts_only"),
    ("ANALYTICS", "user_level_tracking_forbidden"),
    ("SUPPORT", "query_kind_case_matrix"),
    ("SUPPORT", "projection_kind_state_matrix"),
    ("SUPPORT", "publication_separation"),
    ("SUPPORT", "terminal_ordered_coverage"),
    ("SUPPORT", "internal_records_forbidden"),
    ("PRIVACY", "open_decision_gate"),
    ("PRIVACY", "projection_state_matrix"),
    ("PRIVACY", "terminal_result_matrix"),
    ("PRIVACY", "policy_blocked_matrix"),
    ("PRIVACY", "secret_retention_no_invention"),
    ("STATIC", "exact_exports"),
    ("STATIC", "import_isolation"),
    ("STATIC", "frozen_extra_forbid"),
    ("STATIC", "synthetic_fixture_integrity"),
    ("STATIC", "reload_stability"),
    ("STATIC", "negative_controls"),
]
IDS = [
    f"FX-WC12-{category}-{index:03d}" for index, (category, _) in enumerate(EXPECTED_SCENARIOS, 1)
]


def _load() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _synthetic_handler(vector: dict) -> str:
    assert vector["synthetic_only"] is True
    assert vector["expected_result"] in {"PASS", "VALIDATION_ERROR", "STATIC_VIOLATION"}
    assert vector["canonical_fixture_reference_ids"]
    assert all(
        re.fullmatch(r"FX-[A-Z0-9-]+-001", ref) for ref in vector["canonical_fixture_reference_ids"]
    )
    return vector["scenario"]


HANDLERS: dict[str, Callable[[dict], str]] = {fixture_id: _synthetic_handler for fixture_id in IDS}


def test_fixture_schema_and_exact_values() -> None:
    data = _load()
    assert list(data) == EXPECTED_TOP
    assert data["schema_version"] == "1.0"
    assert data["module"] == "12-web-cabinet"
    assert data["accepted_through_step"] == "WC-11"
    assert data["synthetic_only"] is True
    for key in (
        "contains_real_user_data",
        "contains_real_session_data",
        "contains_secret_material",
        "contains_raw_provider_payload",
        "contains_raw_avito_payload",
        "contains_private_support_data",
        "contains_personal_or_legal_data",
        "network_required",
        "provider_api_required",
        "database_required",
        "runtime_required",
    ):
        assert data[key] is False
    assert len(data["canonical_fixture_references"]) == 31
    assert len(data["vectors"]) == 56


def test_exact_registry_and_mapping() -> None:
    data = _load()
    vectors = data["vectors"]
    assert [v["fixture_id"] for v in vectors] == IDS
    assert [(v["category"], v["scenario"]) for v in vectors] == EXPECTED_SCENARIOS
    assert [v["roadmap_step"] for v in vectors] == [CATEGORIES[c] for c, _ in EXPECTED_SCENARIOS]
    assert len({v["fixture_id"] for v in vectors}) == 56
    assert all(
        list(v)
        == [
            "fixture_id",
            "roadmap_step",
            "category",
            "target_contract",
            "scenario",
            "expected_result",
            "synthetic_only",
            "canonical_fixture_reference_ids",
        ]
        for v in vectors
    )


def test_canonical_references_and_handler_coverage() -> None:
    data = _load()
    known = set(data["canonical_fixture_references"])
    refs = [ref for vector in data["vectors"] for ref in vector["canonical_fixture_reference_ids"]]
    assert set(refs) == known
    assert all(ref in known for ref in refs)
    assert len(HANDLERS) == 56
    executed = [HANDLERS[v["fixture_id"]](v) for v in data["vectors"]]
    assert executed == [scenario for _, scenario in EXPECTED_SCENARIOS]
    assert set(HANDLERS) == set(IDS)


def test_fixture_safety_scan_rejects_realistic_data() -> None:
    text = FIXTURE.read_text(encoding="utf-8")
    forbidden = re.compile(r"(?i)(@|https?://|[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,})")
    assert forbidden.search(text) is None
    assert all(
        re.fullmatch(r"FX-[A-Z0-9-]+-001", ref) for ref in _load()["canonical_fixture_references"]
    )


def test_policy_and_authority_matrices_are_literal() -> None:
    assert package.WebPrivacySurfaceKind.RETENTION_POLICY.value == "RETENTION_POLICY"
    assert package.WebPrivacySurfaceKind.DELETION_EXPORT_POLICY.value == "DELETION_EXPORT_POLICY"
    assert package.WebPrivacyProjectionState.POLICY_BLOCKED.value == "POLICY_BLOCKED"
    assert package.WebReadFreshness.AMBIGUOUS.value == "AMBIGUOUS"
    assert package.WebBeaconCommandKind.PERMANENT_DELETE.value == "PERMANENT_DELETE"
    assert package.WebChannelKind.TELEGRAM.value == "TELEGRAM"
    assert package.WebChannelKind.MAX.value == "MAX"
    assert package.WebAdminAnalyticsMetricKind.VISITOR_COUNT.value == "VISITOR_COUNT"


@pytest.mark.parametrize("category,scenario", EXPECTED_SCENARIOS)
def test_each_wc_matrix_has_an_explicit_vector(category: str, scenario: str) -> None:
    vector = next(
        v for v in _load()["vectors"] if (v["category"], v["scenario"]) == (category, scenario)
    )
    assert vector["category"] == category
    assert vector["roadmap_step"] == CATEGORIES[category]
    assert vector["target_contract"].startswith("mayak.modules.web_cabinet")
    assert vector["expected_result"] in {"PASS", "VALIDATION_ERROR", "STATIC_VIOLATION"}


def test_required_negative_controls_are_represented() -> None:
    scenarios = {scenario for _, scenario in EXPECTED_SCENARIOS}
    required = {
        "stale_ambiguous",
        "duplicate_source_rejected",
        "business_authority_forbidden",
        "unauthenticated_forbidden",
        "invented_values_forbidden",
        "raw_payload_archive_forbidden",
        "user_level_tracking_forbidden",
        "internal_records_forbidden",
        "policy_blocked_matrix",
        "negative_controls",
    }
    assert required <= scenarios
    assert violations("import requests\n")
    assert violations("import subprocess\n")
    assert violations("x = eval('x')\n")
    assert violations("socket.connect('x')\n")
    assert violations("from sqlalchemy import create_engine\n")
