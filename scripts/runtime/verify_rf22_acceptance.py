"""Fail-closed verifier for structured, digest-bound RF22 observations."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, cast

TECHNICAL_ID = "RF22-FILTER-CATALOG-BUILDER-RUNTIME-01"
TABLES = sorted(
    {
        "filter_catalog_versions",
        "filter_definitions",
        "filter_options",
        "filter_dependencies",
        "filter_category_applicability",
        "filter_evidence_references",
        "filter_capability_profiles",
    }
)
LEGACY_KEYS = {
    "REQUIRED_TRUE",
    "candidate_prepared",
    "catalog_conflict",
    "zero_provider_calls",
    "valid_draft",
}


def _fail(message: str) -> None:
    raise SystemExit(f"RF22 verification failed: {message}")


def _obs(observations: dict[str, object], name: str) -> dict[str, Any]:
    value = observations.get(name)
    if not isinstance(value, dict):
        _fail(f"structured observation missing: {name}")
    return cast(dict[str, Any], value)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact", type=Path)
    parser.add_argument("--candidate-sha", required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    try:
        evidence: Any = json.loads(args.artifact.read_text(encoding="utf-8"))
        manifest: Any = json.loads(args.manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        _fail(f"artifact unreadable: {exc}")
    if not isinstance(evidence, dict) or not isinstance(manifest, dict):
        _fail("root documents must be objects")
    if LEGACY_KEYS.intersection(evidence) or "required_true" in evidence:
        _fail("legacy boolean evidence shape is forbidden")
    if (
        evidence.get("technical_id") != TECHNICAL_ID
        or evidence.get("candidate_sha") != args.candidate_sha
    ):
        _fail("identity mismatch")
    if evidence.get("postgres_major") != 18 or evidence.get("catalog_tables") != TABLES:
        _fail("PostgreSQL 18 or exact seven-table observation missing")
    if (
        evidence.get("application_role") != "mayak_application"
        or evidence.get("migration_role") != "mayak_migration"
    ):
        _fail("application/migration role identity mismatch")
    observations: Any = evidence.get("observations")
    if not isinstance(observations, dict):
        _fail("structured observations missing")
    required = _obs(observations, "required_semantics")
    if required.get("missing", {}).get(
        "state"
    ) != "INVALID" or "REQUIRED_FIELD_MISSING" not in required.get("missing", {}).get(
        "reason_codes", []
    ):
        _fail("required missing observation failed")
    optional = required.get("optional_missing", {})
    if (
        required.get("present", {}).get("state") != "VALID"
        or optional.get("state") != "VALID"
        or "REQUIRED_FIELD_MISSING" in optional.get("reason_codes", [])
    ):
        _fail("required propagation observation failed")
    option = _obs(observations, "option_isolation")
    if (
        option.get("same_code_scoped") is not True
        or option.get("cross_definition_id_rejected") is not True
    ):
        _fail("option isolation observation failed")
    profile = _obs(observations, "profile_selection")
    if (profile.get("all_profiles_reconstructed") is not True
        or profile.get("deterministic_exact_scope") is not True
        or not isinstance(profile.get("selected_profile_ids"), dict)
        or not profile.get("selected_profile_ids")):
        _fail("profile selection observation failed")
    semantic = _obs(observations, "semantic_exposure")
    expected_reasons = {
        "provider_mismatch": {"PROVIDER_SURFACE_MISMATCH"},
        "category_mismatch": {"CATEGORY_SCOPE_MISMATCH"},
        "geography_mismatch": {"GEOGRAPHY_SCOPE_MISMATCH"},
        "global_approval_missing": {"GLOBAL_SCOPE_APPROVAL_REQUIRED"},
        "requires": {"DEPENDENCY_BLOCKED"},
        "excludes": {"DEPENDENCY_BLOCKED"},
        "constrains": {"DEPENDENCY_BLOCKED"},
        "not_evaluated": {"DEPENDENCY_NOT_EVALUATED"},
        "cycle": {"DEPENDENCY_GRAPH_CYCLE"},
    }
    for name, expected in expected_reasons.items():
        value = semantic.get(name)
        if (not isinstance(value, dict) or value.get("state") != "BLOCKED"
                or not expected.intersection(value.get("reason_codes", []))):
            _fail(f"semantic observation failed: {name}")
    conflicts = _obs(observations, "conflicts")
    if (
        conflicts.get("catalog", {}).get("reason_code") != "CATALOG_VERSION_MISMATCH"
        or conflicts.get("beacon", {}).get("reason_code") != "BEACON_REVISION_MISMATCH"
    ):
        _fail("actual conflict observations missing")
    candidate = _obs(observations, "candidate_preparation")
    if candidate.get("state") != "PREPARED" or not isinstance(
        candidate.get("validated_builder_field_ids"), list
    ):
        _fail("candidate result missing")
    if (
        candidate.get("beacon_mutation_performed") is not False
        or candidate.get("direct_table_write_performed") is not False
    ):
        _fail("candidate mutation invariant failed")
    multivalue = _obs(observations, "multivalue")
    if (multivalue.get("raw_sequence") != ["OPTION_A", "OPTION_B", "OPTION_A"]
            or multivalue.get("repeated_sequence") != multivalue.get("candidate_sequence")
            or multivalue.get("candidate_sequence", [])[0]
            != multivalue.get("candidate_sequence", [None])[-1]
    ):
        _fail("multivalue sequence was not preserved")
    range_candidate = _obs(observations, "range_candidate")
    if (range_candidate.get("state") != "PREPARED"
            or range_candidate.get("reference") == range_candidate.get("second_reference")
            or range_candidate.get("beacon_mutation_performed") is not False):
        _fail("range candidate preservation failed")
    sql = _obs(observations, "sql_observer")
    if (
        sql.get("insert_count") != 0
        or sql.get("update_count") != 0
        or sql.get("delete_count") != 0
        or sql.get("foreign_table_access_count") != 0
    ):
        _fail("SQL observer detected mutation or foreign access")
    provider = _obs(observations, "provider_observer")
    if provider.get("call_count") != 0 or provider.get("forbidden_import_count") != 0:
        _fail("provider boundary failed")
    permissions = _obs(observations, "permission_boundary")
    if any(
        permissions.get(name) is not True
        for name in (
            "application_select_succeeds",
            "application_insert_denied",
            "application_update_denied",
            "application_delete_denied",
        )
    ):
        _fail("application permission boundary failed")
    if evidence.get("raw_provider_payload_persisted") is not False:
        _fail("raw provider payload invariant missing")
    if evidence.get("catalog_tables") != TABLES:
        _fail("table inventory mismatch")
    payloads = manifest.get("payloads")
    if (
        manifest.get("classification") != "CLEAN"
        or not isinstance(payloads, list)
        or [item.get("basename") for item in payloads] != ["rf22.json", "rf22-full-pytest.log"]
    ):
        _fail("invalid scanner manifest")
    for item in payloads:
        path = args.artifact.parent / str(item["basename"])
        if hashlib.sha256(path.read_bytes()).hexdigest() != item.get("sha256"):
            _fail(f"payload digest mismatch: {item.get('basename')}")
    print("RF22_ACCEPTANCE_VERIFIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
