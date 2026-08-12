# ruff: noqa: E501
"""Fail-closed verifier for the executable RF22 acceptance chain."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, NoReturn, cast

TECHNICAL_ID = "RF22-FILTER-CATALOG-BUILDER-RUNTIME-01"
SCANNER_METHOD = "rf22-safety-scanner/v2"
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
LEGACY_KEYS = {"REQUIRED_TRUE", "candidate_prepared", "catalog_conflict", "zero_provider_calls", "valid_draft"}
SUMMARY = re.compile(r"^(?:=|\s)*(?P<parts>(?:[0-9][0-9,]* (?:passed|skipped|failed|error|errors)(?:,?\s*|$))+)(?:[0-9][0-9,]* warnings?,?\s*)?\s*in\s+[0-9.]+s(?:\s+\([^)]*\))?\s*=*$")


def _fail(message: str) -> NoReturn:
    raise SystemExit(f"RF22 verification failed: {message}")


def _obs(observations: dict[str, object], name: str) -> dict[str, Any]:
    value = observations.get(name)
    if not isinstance(value, dict):
        _fail(f"structured observation missing: {name}")
    return cast(dict[str, Any], value)


def _reasons(value: object) -> set[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        _fail("reason_codes must be a list of strings")
    return set(cast(list[str], value))


def _require_outcome(value: object, *, state: str, reasons: set[str], name: str) -> None:
    if not isinstance(value, dict) or value.get("state") != state or _reasons(value.get("reason_codes")) != reasons:
        _fail(f"exact semantic observation failed: {name}")


def _verify_pytest_log(path: Path) -> None:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        _fail(f"focused pytest log unreadable: {exc}")
    summaries = []
    for line in lines:
        match = SUMMARY.search(line.strip())
        if match:
            counts = {name: 0 for name in ("passed", "skipped", "failed", "errors")}
            for number, label in re.findall(r"([0-9][0-9,]*)\s+(passed|skipped|failed|errors?)", match.group("parts")):
                counts["errors" if label.startswith("error") else label] = int(number.replace(",", ""))
            if sum(counts.values()):
                summaries.append(counts)
    if len(summaries) != 1 or summaries[0]["failed"] or summaries[0]["errors"]:
        _fail("focused pytest log is not a single clean summary")


def _verify_manifest(manifest: dict[str, Any], *, root: Path) -> None:
    if manifest.get("scanner_method") != SCANNER_METHOD:
        _fail("scanner method/version mismatch")
    if manifest.get("classification") != "CLEAN" or manifest.get("finding_count") != 0 or manifest.get("findings") != []:
        _fail("scanner findings/classification failed")
    payloads = manifest.get("payloads")
    if not isinstance(payloads, list):
        _fail("scanner payload inventory is not exact")
    basenames = [item.get("basename") for item in payloads if isinstance(item, dict)]
    if basenames != ["rf22.json", "rf22-focused-pytest.log"] or len(payloads) != 2:
        _fail("scanner payload inventory is not exact")
    for item in payloads:
        if not isinstance(item, dict) or set(item) != {"basename", "size", "sha256"}:
            _fail("malformed scanner payload entry")
        basename = item["basename"]
        if not isinstance(basename, str) or basename not in {"rf22.json", "rf22-focused-pytest.log"} or Path(basename).name != basename:
            _fail("unsafe scanner basename")
        path = root / basename
        if not path.is_file():
            _fail(f"scanner payload missing: {basename}")
        raw = path.read_bytes()
        digest = item["sha256"]
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            _fail("scanner digest is not lowercase SHA-256")
        if item["size"] != len(raw) or digest != hashlib.sha256(raw).hexdigest():
            _fail(f"scanner payload binding failed: {basename}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact", type=Path)
    parser.add_argument("--candidate-sha", required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--pytest-log", type=Path)
    args = parser.parse_args()
    root = args.artifact.parent
    log = args.pytest_log or root / "rf22-focused-pytest.log"
    try:
        evidence: Any = json.loads(args.artifact.read_text(encoding="utf-8"))
        manifest: Any = json.loads(args.manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        _fail(f"artifact unreadable: {exc}")
    if not isinstance(evidence, dict) or not isinstance(manifest, dict):
        _fail("root documents must be objects")
    if LEGACY_KEYS.intersection(evidence) or "required_true" in evidence:
        _fail("legacy boolean evidence shape is forbidden")
    _verify_pytest_log(log)
    if evidence.get("technical_id") != TECHNICAL_ID or evidence.get("candidate_sha") != args.candidate_sha:
        _fail("identity mismatch")
    if evidence.get("postgres_major") != 18 or evidence.get("catalog_tables") != TABLES:
        _fail("PostgreSQL 18 or exact seven-table observation missing")
    if evidence.get("application_role") != "mayak_application" or evidence.get("migration_role") != "mayak_migration":
        _fail("application/migration role identity mismatch")
    observations = evidence.get("observations")
    if not isinstance(observations, dict):
        _fail("structured observations missing")
    required = _obs(observations, "required_semantics")
    _require_outcome(required.get("missing"), state="INVALID", reasons={"REQUIRED_FIELD_MISSING"}, name="required missing")
    _require_outcome(required.get("present"), state="VALID", reasons={"DRAFT_VALID"}, name="required present")
    _require_outcome(required.get("optional_missing"), state="VALID", reasons={"DRAFT_VALID"}, name="optional missing")
    option = _obs(observations, "option_isolation")
    if option.get("same_code_scoped") is not True or option.get("cross_definition_id_rejected") is not True:
        _fail("option isolation observation failed")
    profile = _obs(observations, "profile_selection")
    if profile.get("all_profiles_reconstructed") is not True or not isinstance(profile.get("selected_profile_ids"), dict) or not profile.get("selected_profile_ids"):
        _fail("profile reconstruction observation failed")
    if not isinstance(profile.get("expected_profile_id"), str) or profile.get("actual_profile_id") != profile.get("expected_profile_id"):
        _fail("exact expected profile identity is not bound")
    if profile.get("order_invariant") is not True:
        _fail("profile order invariance proof missing")
    semantic = _obs(observations, "semantic_exposure")
    for name, expected in {
        "provider_mismatch": {"PROVIDER_SURFACE_MISMATCH"},
        "category_mismatch": {"CATEGORY_SCOPE_MISMATCH"},
        "geography_mismatch": {"GEOGRAPHY_SCOPE_MISMATCH"},
        "global_approval_missing": {
            "CATEGORY_SCOPE_REQUIRED",
            "GEOGRAPHY_SCOPE_REQUIRED",
            "GLOBAL_SCOPE_APPROVAL_REQUIRED",
        },
        "requires": {"DEPENDENCY_BLOCKED"},
        "excludes": {"DEPENDENCY_BLOCKED"},
        "constrains": {"DEPENDENCY_BLOCKED"},
        "not_evaluated": {"DEPENDENCY_NOT_EVALUATED"},
        "cycle": {"DEPENDENCY_GRAPH_CYCLE"},
    }.items():
        _require_outcome(semantic.get(name), state="BLOCKED", reasons=expected, name=name)
    conflicts = _obs(observations, "conflicts")
    for name, code in (("catalog", "CATALOG_VERSION_MISMATCH"), ("beacon", "BEACON_REVISION_MISMATCH")):
        value = conflicts.get(name)
        if not isinstance(value, dict) or value.get("state") != "CONFLICT" or value.get("reason_code") != code:
            _fail(f"conflict observation failed: {name}")
    candidate = _obs(observations, "candidate_preparation")
    if candidate.get("state") != "PREPARED" or candidate.get("beacon_acceptance_required") is not True or candidate.get("beacon_mutation_performed") is not False or candidate.get("direct_table_write_performed") is not False or candidate.get("runtime_or_persistence_performed") is not False or not isinstance(candidate.get("validated_builder_field_ids"), list) or candidate.get("validated_builder_field_ids") != candidate.get("expected_validated_builder_field_ids"):
        _fail("candidate invariants failed")
    multi = _obs(observations, "multivalue")
    raw, canonical, validation, prepared = (
        multi.get(name)
        for name in ("raw_sequence", "canonical_sequence", "validation_sequence", "candidate_sequence")
    )
    sequences = (raw, canonical, validation, prepared)
    if not all(isinstance(item, list) for item in sequences):
        _fail("multivalue transformation binding failed")
    raw, canonical, validation, prepared = (cast(list[Any], item) for item in sequences)
    if raw != ["OPTION_A", "OPTION_B", "OPTION_A"] or len(raw) != len(canonical) or len(canonical) != len(validation) or validation != prepared or len(prepared) != len(set(prepared)) + 1 or prepared[0] != prepared[-1] or not multi.get("definition_scoped"):
        _fail("multivalue transformation binding failed")
    range_candidate = _obs(observations, "range_candidate")
    normalized = range_candidate.get("normalized")
    if not isinstance(normalized, list) or len(normalized) != 1 or not isinstance(normalized[0], dict) or any(
        normalized[0].get(key) != value
        for key, value in {
            "unit_code": "UNIT",
            "lower_value": "10",
            "upper_value": "20",
            "lower_inclusive": True,
            "upper_inclusive": True,
            "step_origin": "0",
        }.items()
    ):
        _fail("normalized range payload failed")
    if range_candidate.get("state") != "PREPARED" or not isinstance(range_candidate.get("reference"), str) or not isinstance(range_candidate.get("second_reference"), str) or range_candidate.get("reference") == range_candidate.get("second_reference") or range_candidate.get("candidate_reference") != range_candidate.get("reference") or range_candidate.get("beacon_mutation_performed") is not False:
        _fail("range candidate binding failed")
    reads = _obs(observations, "read_models")
    web = reads.get("web")
    admin = reads.get("admin")
    if not isinstance(web, dict) or web.get("audience") != "WEB_CUSTOMER" or web.get("details_redacted") is not True or web.get("evidence_reference_ids") != [] or web.get("warning_ids") != []:
        _fail("Web projection proof failed")
    if not isinstance(admin, dict) or admin.get("audience") != "ADMIN_AUTHORIZED" or admin.get("details_redacted") is not False or not isinstance(admin.get("evidence_reference_ids"), list) or not all(isinstance(item, str) for item in admin["evidence_reference_ids"]) or admin.get("contains_raw_provider_payload") is not False:
        _fail("Admin projection proof failed")
    sql = _obs(observations, "sql_observer")
    if sql.get("select_table_inventory") != TABLES or any(sql.get(name) != 0 for name in ("insert_count", "update_count", "delete_count", "foreign_table_access_count")):
        _fail("SQL observer inventory or mutation boundary failed")
    provider = _obs(observations, "provider_observer")
    if provider.get("call_count") != 0 or provider.get("forbidden_import_count") != 0:
        _fail("provider boundary failed")
    permissions = _obs(observations, "permission_boundary")
    if any(permissions.get(name) is not True for name in ("application_select_succeeds", "application_insert_denied", "application_update_denied", "application_delete_denied")):
        _fail("application permission boundary failed")
    if evidence.get("raw_provider_payload_persisted") is not False:
        _fail("raw provider payload invariant missing")
    _verify_manifest(manifest, root=root)
    print("RF22_ACCEPTANCE_VERIFIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
