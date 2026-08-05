# ruff: noqa: E501
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
VERIFY = ROOT / "scripts/runtime/verify_rf22_acceptance.py"
SCAN = ROOT / "scripts/runtime/check_rf22_artifact_safety.py"


def _valid_evidence() -> dict[str, object]:
    tables = sorted(
        {
            "filter_catalog_versions", "filter_definitions", "filter_options",
            "filter_dependencies", "filter_category_applicability",
            "filter_evidence_references", "filter_capability_profiles",
        }
    )
    semantic = {name: {"state": "BLOCKED", "reason_codes": [reason]} for name, reason in {
        "provider_mismatch": "PROVIDER_SURFACE_MISMATCH", "category_mismatch": "CATEGORY_SCOPE_MISMATCH",
        "geography_mismatch": "GEOGRAPHY_SCOPE_MISMATCH", "global_approval_missing": "GLOBAL_SCOPE_APPROVAL_REQUIRED",
        "requires": "DEPENDENCY_BLOCKED", "excludes": "DEPENDENCY_BLOCKED",
        "constrains": "DEPENDENCY_BLOCKED", "not_evaluated": "DEPENDENCY_NOT_EVALUATED",
        "cycle": "DEPENDENCY_GRAPH_CYCLE",
    }.items()}
    semantic["global_approval_missing"]["reason_codes"] = [
        "CATEGORY_SCOPE_REQUIRED",
        "GEOGRAPHY_SCOPE_REQUIRED",
        "GLOBAL_SCOPE_APPROVAL_REQUIRED",
    ]
    return {
        "technical_id": "RF22-FILTER-CATALOG-BUILDER-RUNTIME-01", "candidate_sha": "a" * 40,
        "postgres_major": 18, "catalog_tables": tables, "application_role": "mayak_application",
        "migration_role": "mayak_migration", "raw_provider_payload_persisted": False,
        "observations": {
            "required_semantics": {
                "missing": {"state": "INVALID", "reason_codes": ["REQUIRED_FIELD_MISSING"]},
                "present": {"state": "VALID", "reason_codes": ["DRAFT_VALID"]},
                "optional_missing": {"state": "VALID", "reason_codes": ["DRAFT_VALID"]},
            },
            "option_isolation": {"same_code_scoped": True, "cross_definition_id_rejected": True},
            "profile_selection": {"all_profiles_reconstructed": True, "selected_profile_ids": {"D": "P"}, "expected_profile_id": "P", "actual_profile_id": "P", "order_invariant": True},
            "semantic_exposure": semantic,
            "conflicts": {"catalog": {"state": "CONFLICT", "reason_code": "CATALOG_VERSION_MISMATCH"}, "beacon": {"state": "CONFLICT", "reason_code": "BEACON_REVISION_MISMATCH"}},
            "candidate_preparation": {"state": "PREPARED", "validated_builder_field_ids": ["F"], "expected_validated_builder_field_ids": ["F"], "beacon_acceptance_required": True, "beacon_mutation_performed": False, "direct_table_write_performed": False, "runtime_or_persistence_performed": False},
            "multivalue": {"raw_sequence": ["OPTION_A", "OPTION_B", "OPTION_A"], "canonical_sequence": ["A", "B", "A"], "validation_sequence": ["A", "B", "A"], "candidate_sequence": ["A", "B", "A"], "definition_scoped": True},
            "range_candidate": {"state": "PREPARED", "normalized": [{"filter_definition_id": "R", "unit_code": "UNIT", "lower_value": "10", "upper_value": "20", "lower_inclusive": True, "upper_inclusive": True, "step_origin": "0"}], "reference": "RF22_RANGE_ONE", "second_reference": "RF22_RANGE_TWO", "candidate_reference": "RF22_RANGE_ONE", "beacon_mutation_performed": False},
            "read_models": {"web": {"audience": "WEB_CUSTOMER", "details_redacted": True, "evidence_reference_ids": [], "warning_ids": [], "contains_raw_provider_payload": False}, "admin": {"audience": "ADMIN_AUTHORIZED", "details_redacted": False, "evidence_reference_ids": ["E"], "warning_ids": [], "contains_raw_provider_payload": False}},
            "sql_observer": {"select_table_inventory": tables, "insert_count": 0, "update_count": 0, "delete_count": 0, "foreign_table_access_count": 0},
            "provider_observer": {"call_count": 0, "forbidden_import_count": 0},
            "permission_boundary": {"application_select_succeeds": True, "application_insert_denied": True, "application_update_denied": True, "application_delete_denied": True},
        },
    }


def _invoke_verifier(tmp_path: Path, evidence: dict[str, object], *, manifest_mutation=None, log_text: str = "===== 1 passed, 0 skipped in 0.01s =====") -> subprocess.CompletedProcess[str]:
    artifact = tmp_path / "rf22.json"
    log = tmp_path / "rf22-full-pytest.log"
    manifest = tmp_path / "rf22-safety-manifest.json"
    artifact.write_text(json.dumps(evidence), encoding="utf-8")
    log.write_text(log_text, encoding="utf-8")
    scanned = subprocess.run([sys.executable, str(SCAN), str(artifact), str(log), "--manifest", str(manifest)], capture_output=True, text=True, check=False)
    assert scanned.returncode == 0
    if manifest_mutation is not None:
        manifest_data = json.loads(manifest.read_text(encoding="utf-8"))
        manifest_mutation(manifest_data)
        manifest.write_text(json.dumps(manifest_data), encoding="utf-8")
    return subprocess.run([sys.executable, str(VERIFY), str(artifact), "--candidate-sha", "a" * 40, "--manifest", str(manifest), "--pytest-log", str(log)], capture_output=True, text=True, check=False)


def test_rf22_scanner_binds_exact_payload_digests(tmp_path: Path) -> None:
    artifact = tmp_path / "rf22.json"
    log = tmp_path / "rf22-full-pytest.log"
    manifest = tmp_path / "rf22-safety-manifest.json"
    artifact.write_text('{"technical_id":"RF22"}\n', encoding="utf-8")
    log.write_text("focused tests passed\n", encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/runtime/check_rf22_artifact_safety.py"),
            str(artifact),
            str(log),
            "--manifest",
            str(manifest),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    payloads = json.loads(manifest.read_text(encoding="utf-8"))["payloads"]
    assert [item["basename"] for item in payloads] == ["rf22.json", "rf22-full-pytest.log"]
    artifact.write_text('{"technical_id":"TAMPERED"}\n', encoding="utf-8")
    assert (
        next(item for item in payloads if item["basename"] == "rf22.json")["sha256"]
        != __import__("hashlib").sha256(artifact.read_bytes()).hexdigest()
    )


def test_rf22_verifier_rejects_legacy_boolean_artifact(tmp_path: Path) -> None:
    artifact = tmp_path / "rf22.json"
    manifest = tmp_path / "rf22-safety-manifest.json"
    artifact.write_text(json.dumps({"candidate_prepared": True}), encoding="utf-8")
    manifest.write_text("{}", encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/runtime/verify_rf22_acceptance.py"),
            str(artifact),
            "--candidate-sha",
            "0" * 40,
            "--manifest",
            str(manifest),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "legacy boolean" in result.stderr


MUTATIONS = {
    "candidate_sha": lambda d: d.update(candidate_sha="b" * 40),
    "postgres_major": lambda d: d.update(postgres_major=17),
    "application_role": lambda d: d.update(application_role="wrong"),
    "migration_role": lambda d: d.update(migration_role="wrong"),
    "table_inventory": lambda d: d.update(catalog_tables=["foreign_table"]),
    "required_missing_valid": lambda d: d["observations"]["required_semantics"]["missing"].update(state="VALID"),
    "optional_missing_required_invalid": lambda d: d["observations"]["required_semantics"]["optional_missing"].update(state="INVALID"),
    "provider_reason": lambda d: d["observations"]["semantic_exposure"]["provider_mismatch"].update(reason_codes=["CATEGORY_SCOPE_MISMATCH"]),
    "category_reason": lambda d: d["observations"]["semantic_exposure"]["category_mismatch"].update(reason_codes=["PROVIDER_SURFACE_MISMATCH"]),
    "geography_reason": lambda d: d["observations"]["semantic_exposure"]["geography_mismatch"].update(reason_codes=["PROVIDER_SURFACE_MISMATCH"]),
    "global_reason": lambda d: d["observations"]["semantic_exposure"]["global_approval_missing"].update(reason_codes=["CATEGORY_SCOPE_REQUIRED"]),
    "requires_reason": lambda d: d["observations"]["semantic_exposure"]["requires"].update(reason_codes=["EXCLUDES_BLOCKED"]),
    "excludes_reason": lambda d: d["observations"]["semantic_exposure"]["excludes"].update(reason_codes=["EXCLUDES_BLOCKED"]),
    "constrains_reason": lambda d: d["observations"]["semantic_exposure"]["constrains"].update(reason_codes=["REQUIRES_BLOCKED"]),
    "not_evaluated_reason": lambda d: d["observations"]["semantic_exposure"]["not_evaluated"].update(reason_codes=["DEPENDENCY_BLOCKED"]),
    "cycle_reason": lambda d: d["observations"]["semantic_exposure"]["cycle"].update(reason_codes=["DEPENDENCY_BLOCKED"]),
    "wrong_profile": lambda d: d["observations"]["profile_selection"].update(actual_profile_id="FOREIGN"),
    "missing_expected_profile": lambda d: d["observations"]["profile_selection"].pop("expected_profile_id"),
    "multivalue_reordered": lambda d: d["observations"]["multivalue"].update(candidate_sequence=["A", "A", "B"]),
    "multivalue_deduplicated": lambda d: d["observations"]["multivalue"].update(candidate_sequence=["A", "B"]),
    "multivalue_cross_definition": lambda d: d["observations"]["multivalue"].update(definition_scoped=False),
    "range_collision": lambda d: d["observations"]["range_candidate"].update(second_reference="RF22_RANGE_ONE"),
    "wrong_normalized_range": lambda d: d["observations"]["range_candidate"]["normalized"][0].update(lower_value="11"),
    "candidate_not_prepared": lambda d: d["observations"]["candidate_preparation"].update(state="BLOCKED"),
    "beacon_acceptance_false": lambda d: d["observations"]["candidate_preparation"].update(beacon_acceptance_required=False),
    "beacon_mutated": lambda d: d["observations"]["candidate_preparation"].update(beacon_mutation_performed=True),
    "direct_write": lambda d: d["observations"]["candidate_preparation"].update(direct_table_write_performed=True),
    "runtime_persistence": lambda d: d["observations"]["candidate_preparation"].update(runtime_or_persistence_performed=True),
    "web_evidence_leak": lambda d: d["observations"]["read_models"]["web"].update(evidence_reference_ids=["E"]),
    "web_warning_leak": lambda d: d["observations"]["read_models"]["web"].update(warning_ids=["W"]),
    "admin_raw_payload": lambda d: d["observations"]["read_models"]["admin"].update(contains_raw_provider_payload=True),
    "wrong_audience": lambda d: d["observations"]["read_models"]["web"].update(audience="ADMIN_AUTHORIZED"),
    "foreign_select": lambda d: d["observations"]["sql_observer"].update(select_table_inventory=["foreign_table"]),
    "runtime_insert": lambda d: d["observations"]["sql_observer"].update(insert_count=1),
    "runtime_update": lambda d: d["observations"]["sql_observer"].update(update_count=1),
    "runtime_delete": lambda d: d["observations"]["sql_observer"].update(delete_count=1),
    "provider_call": lambda d: d["observations"]["provider_observer"].update(call_count=1),
    "forbidden_import": lambda d: d["observations"]["provider_observer"].update(forbidden_import_count=1),
    "application_insert_allowed": lambda d: d["observations"]["permission_boundary"].update(application_insert_denied=False),
    "application_update_allowed": lambda d: d["observations"]["permission_boundary"].update(application_update_denied=False),
    "application_delete_allowed": lambda d: d["observations"]["permission_boundary"].update(application_delete_denied=False),
    "missing_expected_table": lambda d: d["observations"]["sql_observer"].update(select_table_inventory=d["catalog_tables"][:-1]),
    "foreign_access_count": lambda d: d["observations"]["sql_observer"].update(foreign_table_access_count=1),
    "selected_profile_mapping_missing": lambda d: d["observations"]["profile_selection"].update(selected_profile_ids={}),
    "profile_order_invariance_missing": lambda d: d["observations"]["profile_selection"].update(order_invariant=False),
    "candidate_fields_wrong": lambda d: d["observations"]["candidate_preparation"].update(validated_builder_field_ids=[]),
    "range_unit_wrong": lambda d: d["observations"]["range_candidate"]["normalized"][0].update(unit_code="WRONG"),
    "range_candidate_reference_wrong": lambda d: d["observations"]["range_candidate"].update(candidate_reference="RF22_RANGE_TWO"),
    "web_not_redacted": lambda d: d["observations"]["read_models"]["web"].update(details_redacted=False),
    "admin_redacted": lambda d: d["observations"]["read_models"]["admin"].update(details_redacted=True),
}


@pytest.mark.parametrize("case", tuple(MUTATIONS), ids=tuple(MUTATIONS))
def test_rf22_verifier_rejects_material_mutation(tmp_path: Path, case: str) -> None:
    evidence = _valid_evidence()
    MUTATIONS[case](evidence)
    result = _invoke_verifier(tmp_path, evidence)
    assert result.returncode != 0, case


def test_rf22_verifier_accepts_known_valid_structured_fixture(tmp_path: Path) -> None:
    result = _invoke_verifier(tmp_path, _valid_evidence())
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    "log_text",
    ("===== 1 failed, 1 passed in 0.01s =====", "===== 1 error, 1 passed in 0.01s =====", "Traceback (most recent call last):\ninterrupted"),
    ids=("failing-log", "error-log", "missing-summary"),
)
def test_rf22_verifier_rejects_unclean_or_incomplete_full_log(tmp_path: Path, log_text: str) -> None:
    assert _invoke_verifier(tmp_path, _valid_evidence(), log_text=log_text).returncode != 0


@pytest.mark.parametrize(
    "mutation",
    (
        lambda m: m.update(scanner_method="wrong/v1"),
        lambda m: m.update(finding_count=1),
        lambda m: m["payloads"][0].update(size=0),
        lambda m: m["payloads"][0].update(sha256="BAD"),
        lambda m: m["payloads"].pop(),
        lambda m: m["payloads"].append({"basename": "extra", "size": 0, "sha256": "0" * 64}),
        lambda m: m["payloads"][0].update(basename="../rf22.json"),
    ),
    ids=("scanner-version", "scanner-count", "size", "digest", "missing", "extra", "traversal"),
)
def test_rf22_verifier_rejects_scanner_manifest_mutations(tmp_path: Path, mutation) -> None:
    assert _invoke_verifier(tmp_path, _valid_evidence(), manifest_mutation=mutation).returncode != 0


@pytest.mark.parametrize(
    ("payload", "value"),
    (
        ("rf22.json", "postgresql://user:password@db/mayak"),
        ("rf22.json", "Bearer abcdefghijklmnopqrstuvwxyz"),
        ("rf22.json", "-----BEGIN PRIVATE KEY-----"),
        ("rf22.json", '{"provider_payload": "raw"}'),
        ("../rf22.json", "safe"),
    ),
    ids=("postgres-url", "bearer", "private-key", "raw-provider-key", "path-traversal"),
)
def test_rf22_scanner_blocks_credential_and_unsafe_payloads(tmp_path: Path, payload: str, value: str) -> None:
    target = tmp_path / payload
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(value, encoding="utf-8")
    log = tmp_path / "rf22-full-pytest.log"
    log.write_text("pytest log", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(SCAN), str(target), str(log), "--manifest", str(tmp_path / "manifest.json")],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0


def test_rf22_scanner_blocks_wrong_payload_names_and_extra_payload(tmp_path: Path) -> None:
    (tmp_path / "rf22.json").write_text("{}", encoding="utf-8")
    (tmp_path / "rf22-full-pytest.log").write_text("pytest log", encoding="utf-8")
    (tmp_path / "extra.json").write_text("{}", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(SCAN), str(tmp_path / "rf22.json"), str(tmp_path / "extra.json"), "--manifest", str(tmp_path / "manifest.json")],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
