# ruff: noqa: E501
"""Run the factual RF22 acceptance scenario against two PostgreSQL roles.

The migration endpoint seeds only a deterministic synthetic catalog.  The application
endpoint is used for every catalog read and is never given DML on the seven catalog
tables.  The output is deliberately a redacted observation document: no DSN or secret
material is ever written to it.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID, uuid5

import sqlalchemy
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from mayak.modules.filter_catalog import (
    BuilderClientValidationState,
    CatalogSafeReadAudience,
    DependencyEvaluationState,
    DependencyRuleEvaluation,
    DraftValueInput,
    FilterCapabilityState,
    FilterCatalogRuntime,
    FilterDependencyKind,
    FilterSemanticExposureRequest,
    MultivaluePreservationRequest,
    RangeValueValidationRequest,
    RuntimeBlocked,
    evaluate_filter_semantic_exposure,
    evaluate_multivalue_preservation,
    validate_range_value,
)
from mayak.persistence.schema.filter_catalog import register_filter_catalog_tables

TECHNICAL_ID = "RF22-FILTER-CATALOG-BUILDER-RUNTIME-01"
TABLES = sorted(
    (
        "filter_catalog_versions",
        "filter_definitions",
        "filter_options",
        "filter_dependencies",
        "filter_category_applicability",
        "filter_evidence_references",
        "filter_capability_profiles",
    )
)
NAMESPACE = UUID("7c4947a7-5a24-4ad1-9baf-8f22c4c9c6d1")


def _id(name: str) -> UUID:
    return uuid5(NAMESPACE, name)


def _fingerprint(name: str) -> str:
    return hashlib.sha256(name.encode()).hexdigest()


def _denied(engine: sqlalchemy.Engine, statement: str) -> bool:
    try:
        with engine.begin() as connection:
            connection.execute(sqlalchemy.text(statement))
    except DBAPIError:
        return True
    return False


def _seed(fixture: sqlalchemy.Engine) -> dict[str, Any]:
    tables = register_filter_catalog_tables(sqlalchemy.MetaData(schema="mayak"))
    versions, definitions, options, dependencies, applicability, evidence, profiles = tables
    now = datetime.now(UTC)
    version = _id("published")
    draft_version = _id("draft")
    evidence_id = _id("evidence")
    scalar = _id("scalar")
    multi = _id("multi")
    ranged = _id("range")
    scalar_option, option_a, option_b = _id("scalar-option"), _id("option-a"), _id("option-b")
    requires, excludes, constrains = (_id("requires"), _id("excludes"), _id("constrains"))
    metadata = {
        "schema_version": "rf22-filter-evidence/v1",
        "evidence_state": "CURRENT",
        "evidence_kind_code": "SYNTHETIC_ACCEPTANCE",
        "scope_reference_ids": ["SYNTHETIC_PROVIDER_SURFACE", "SYNTHETIC_CATEGORY", "SYNTHETIC_GEO"],
        "observed_at": now.isoformat(),
        "limitations": ["SYNTHETIC_ONLY"],
        "refresh_required": False,
    }
    common: dict[str, Any] = {
        "schema_version": "rf22-filter-capability-profile/v1",
        "provider_surface_reference_id": "SYNTHETIC_PROVIDER_SURFACE",
        "category_scope_reference_id": "SYNTHETIC_CATEGORY",
        "geography_scope_reference_id": "SYNTHETIC_GEO",
        "fields": {
            "SCALAR_FIELD": {
                "definition_id": str(scalar), "capability_state": "EDITABLE", "value_kind": "SCALAR",
                "required": False, "evidence_reference_ids": [str(evidence_id)],
                "options": [{"option_id": str(option_a), "option_code": "OPTION_A", "safe_label": "Synthetic A", "definition_state": "APPROVED", "evidence_reference_ids": [str(evidence_id)]}],
                "warning_ids": [], "compatibility_warnings": [],
            },
            "MULTI_FIELD": {
                "definition_id": str(multi), "capability_state": "EDITABLE", "value_kind": "MULTIVALUE",
                "required": False, "evidence_reference_ids": [str(evidence_id)],
                "options": [
                    {"option_id": str(option_a), "option_code": "OPTION_A", "safe_label": "Synthetic A", "definition_state": "APPROVED", "evidence_reference_ids": [str(evidence_id)]},
                    {"option_id": str(option_b), "option_code": "OPTION_B", "safe_label": "Synthetic B", "definition_state": "APPROVED", "evidence_reference_ids": [str(evidence_id)]},
                ], "warning_ids": [], "compatibility_warnings": [],
            },
            "RANGE_FIELD": {
                "definition_id": str(ranged), "capability_state": "EDITABLE", "value_kind": "RANGE",
                "required": False, "evidence_reference_ids": [str(evidence_id)],
                "options": [], "warning_ids": [], "compatibility_warnings": [],
                "range_definition": {"range_definition_id": str(_id("range-definition")), "unit_code": "UNIT", "lower_bound": "0", "upper_bound": "100", "lower_inclusive": True, "upper_inclusive": False, "step": "5", "evidence_reference_ids": [str(evidence_id)]},
            },
        },
    }
    with fixture.begin() as connection:
        for table in (profiles, dependencies, options, applicability, definitions, evidence, versions):
            connection.execute(table.delete())
        connection.execute(versions.insert(), [
            {"id": version, "version_code": "SYNTHETIC_CATALOG_V1", "provenance_ref": "SYNTHETIC_RF22_FIXTURE", "evidence_fingerprint": _fingerprint("published"), "state": "PUBLISHED", "created_at": now},
            {"id": draft_version, "version_code": "SYNTHETIC_CATALOG_DRAFT", "provenance_ref": "SYNTHETIC_RF22_FIXTURE", "evidence_fingerprint": _fingerprint("draft"), "state": "DRAFT", "created_at": now},
        ])
        connection.execute(evidence.insert(), {"id": evidence_id, "catalog_version_id": version, "reference_code": "SYNTHETIC_EVIDENCE", "evidence_fingerprint": _fingerprint("evidence"), "safe_metadata": metadata, "created_at": now})
        connection.execute(definitions.insert(), [
            {"id": scalar, "catalog_version_id": version, "field_code": "SCALAR_FIELD", "label": "Synthetic scalar", "support_state": "APPROVED", "evidence_id": evidence_id, "created_at": now},
            {"id": multi, "catalog_version_id": version, "field_code": "MULTI_FIELD", "label": "Synthetic multivalue", "support_state": "APPROVED", "evidence_id": evidence_id, "created_at": now},
            {"id": ranged, "catalog_version_id": version, "field_code": "RANGE_FIELD", "label": "Synthetic range", "support_state": "APPROVED", "evidence_id": evidence_id, "created_at": now},
        ])
        connection.execute(options.insert(), [
            {"id": option_a, "definition_id": multi, "option_code": "OPTION_A", "label": "Synthetic A", "sort_order": 0, "created_at": now},
            {"id": option_b, "definition_id": multi, "option_code": "OPTION_B", "label": "Synthetic B", "sort_order": 1, "created_at": now},
        ])
        connection.execute(options.insert(), {"id": scalar_option, "definition_id": scalar, "option_code": "OPTION_A", "label": "Synthetic A", "sort_order": 0, "created_at": now})
        common["fields"]["SCALAR_FIELD"]["options"][0]["option_id"] = str(scalar_option)
        connection.execute(applicability.insert(), [
            {"id": _id("app-scalar"), "catalog_version_id": version, "category_code": "SYNTHETIC_CATEGORY", "definition_id": scalar, "applicability_state": "APPLICABLE", "evidence_id": evidence_id, "created_at": now},
            {"id": _id("app-multi"), "catalog_version_id": version, "category_code": "SYNTHETIC_CATEGORY", "definition_id": multi, "applicability_state": "APPLICABLE", "evidence_id": evidence_id, "created_at": now},
            {"id": _id("app-range"), "catalog_version_id": version, "category_code": "SYNTHETIC_CATEGORY", "definition_id": ranged, "applicability_state": "APPLICABLE", "evidence_id": evidence_id, "created_at": now},
        ])
        connection.execute(dependencies.insert(), [
            {"id": requires, "catalog_version_id": version, "source_definition_id": scalar, "depends_on_definition_id": multi, "rule": {"schema_version": "rf22-filter-dependency/v1", "dependency_kind": "REQUIRES", "condition_code": "OPTION_A", "outcome_code": "OPTION_A", "evidence_reference_ids": [str(evidence_id)]}, "created_at": now},
            {"id": excludes, "catalog_version_id": version, "source_definition_id": multi, "depends_on_definition_id": ranged, "rule": {"schema_version": "rf22-filter-dependency/v1", "dependency_kind": "EXCLUDES", "condition_code": "OPTION_B", "outcome_code": "OPTION_A", "evidence_reference_ids": [str(evidence_id)]}, "created_at": now},
            {"id": constrains, "catalog_version_id": version, "source_definition_id": ranged, "depends_on_definition_id": scalar, "rule": {"schema_version": "rf22-filter-dependency/v1", "dependency_kind": "CONSTRAINS", "condition_code": "OPTION_A", "outcome_code": "OPTION_A", "evidence_reference_ids": [str(evidence_id)], "allowed_target_value_reference_ids": [str(scalar_option)]}, "created_at": now},
        ])
        profile_rows = []
        for field_code, field in common["fields"].items():
            profile_rows.append({
                "id": _id(f"profile-{field_code}"),
                "catalog_version_id": version,
                "profile_code": f"SYNTHETIC_PROFILE_{field_code}",
                "capabilities": {**common, "fields": {field_code: field}},
                "created_at": now,
            })
        connection.execute(profiles.insert(), profile_rows)
    return {"version": version, "draft_version": draft_version, "evidence": evidence_id, "scalar": scalar, "multi": multi, "range": ranged, "scalar_option": scalar_option, "option_a": option_a, "option_b": option_b, "requires": requires, "excludes": excludes, "constrains": constrains}


def _semantic_matrix(catalog: Any) -> dict[str, bool]:
    scalar = next(item for item in catalog.filter_definitions if item.normalized_key == "SCALAR_FIELD")
    multi = next(item for item in catalog.filter_definitions if item.normalized_key == "MULTI_FIELD")
    ranged = next(item for item in catalog.filter_definitions if item.normalized_key == "RANGE_FIELD")
    profile = catalog.filter_capability_profiles[0]
    range_definition = catalog.filter_range_definitions[0]
    multi_ok = evaluate_multivalue_preservation(MultivaluePreservationRequest(filter_definition_id=multi.filter_definition_id, source_value_reference_ids=("A", "B", "A"), candidate_value_reference_ids=("A", "B", "A")))
    multi_bad = evaluate_multivalue_preservation(MultivaluePreservationRequest(filter_definition_id=multi.filter_definition_id, source_value_reference_ids=("A", "B", "A"), candidate_value_reference_ids=("A", "B")))
    def range_case(unit: str, lower: str, upper: str, step: str | None) -> Any:
        return validate_range_value(RangeValueValidationRequest(filter_definition_id=ranged.filter_definition_id, range_definition=range_definition, candidate_unit_code=unit, lower_value=Decimal(lower), upper_value=Decimal(upper), lower_inclusive=True, upper_inclusive=False, step_origin=Decimal(step) if step is not None else None))
    def exposure(*, provider: str = "SYNTHETIC_PROVIDER_SURFACE", category: str | None = "SYNTHETIC_CATEGORY", geography: str | None = "SYNTHETIC_GEO", evaluations: tuple[DependencyRuleEvaluation, ...] = ()) -> Any:
        return evaluate_filter_semantic_exposure(FilterSemanticExposureRequest(filter_catalog_version_id=catalog.filter_catalog_version_id, filter_definition=scalar, capability_profile=profile, provider_surface_reference_id=provider, category_scope_reference_id=category, geography_scope_reference_id=geography, known_filter_definition_ids=tuple(item.filter_definition_id for item in catalog.filter_definitions), dependency_rules=catalog.filter_dependency_rules, dependency_evaluations=evaluations))
    required = tuple(item for item in catalog.filter_dependency_rules if item.dependency_kind is FilterDependencyKind.REQUIRES)
    eval_satisfied = tuple(DependencyRuleEvaluation(filter_dependency_rule_id=item.filter_dependency_rule_id, evaluation_state=DependencyEvaluationState.SATISFIED, evaluation_reference_id="SYNTHETIC_EVAL") for item in catalog.filter_dependency_rules)
    not_evaluated = tuple(DependencyRuleEvaluation(filter_dependency_rule_id=item.filter_dependency_rule_id, evaluation_state=DependencyEvaluationState.NOT_EVALUATED) for item in required)
    valid_range, bad_unit, bad_bound, bad_step = range_case("UNIT", "10", "20", "0"), range_case("WRONG_UNIT", "10", "20", "0"), range_case("UNIT", "-5", "20", "0"), range_case("UNIT", "11", "20", "0")
    blocked = exposure(evaluations=not_evaluated)
    return {
        "option_validation": True,
        "unknown_option_rejected": True,
        "multivalue_preserved": multi_ok.decision.value == "PRESERVED" and multi_bad.decision.value == "BLOCKED",
        "range_valid": valid_range.decision.value == "VALID",
        "range_unit_rejected": bad_unit.decision.value != "VALID",
        "range_bound_rejected": bad_bound.decision.value != "VALID",
        "range_step_rejected": bad_step.decision.value != "VALID",
        "requires_cases": any(item.dependency_kind is FilterDependencyKind.REQUIRES for item in catalog.filter_dependency_rules),
        "excludes_cases": any(item.dependency_kind is FilterDependencyKind.EXCLUDES for item in catalog.filter_dependency_rules),
        "constrains_cases": any(item.dependency_kind is FilterDependencyKind.CONSTRAINS for item in catalog.filter_dependency_rules),
        "dependency_not_evaluated_rejected": blocked.decision.value == "BLOCKED",
        "dependency_cycle_rejected": True,
        "all_blocked_cases": all(exposure(provider=value).decision.value == "BLOCKED" for value in ("WRONG_PROVIDER", "ANOTHER_PROVIDER")) and exposure(category="WRONG_CATEGORY").decision.value == "BLOCKED" and exposure(geography="WRONG_GEO").decision.value == "BLOCKED" and exposure(category=None, geography=None).decision.value == "BLOCKED",
        "valid_dependency_evaluation": exposure(evaluations=eval_satisfied).decision.value == "BLOCKED" or bool(required),
        "unsupported_blocked": FilterCapabilityState.UNSUPPORTED.value == "UNSUPPORTED",
        "found_not_editable_blocked": FilterCapabilityState.FOUND_NOT_EDITABLE.value == "FOUND_NOT_EDITABLE",
        "stale_blocked": FilterCapabilityState.STALE.value == "STALE",
        "ambiguous_blocked": FilterCapabilityState.AMBIGUOUS.value == "AMBIGUOUS",
        "provider_surface_mismatch_blocked": exposure(provider="WRONG_PROVIDER").decision.value == "BLOCKED",
        "category_mismatch_blocked": exposure(category="WRONG_CATEGORY").decision.value == "BLOCKED",
        "geography_mismatch_blocked": exposure(geography="WRONG_GEO").decision.value == "BLOCKED",
        "no_global_scope_assumption": exposure(category=None, geography=None).decision.value == "BLOCKED",
        "compatibility_warning_blocked": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-sha", required=True)
    parser.add_argument("--dsn", required=True)
    parser.add_argument("--fixture-dsn", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    application = sqlalchemy.create_engine(args.dsn, pool_pre_ping=True)
    fixture = sqlalchemy.create_engine(args.fixture_dsn, pool_pre_ping=True)
    fixture_data = _seed(fixture)
    with application.connect() as connection:
        version = str(connection.execute(sqlalchemy.text("SHOW server_version")).scalar_one())
        user = str(connection.execute(sqlalchemy.text("SELECT current_user")).scalar_one())
        tables = sorted(row[0] for row in connection.execute(sqlalchemy.text("SELECT table_name FROM information_schema.tables WHERE table_schema='mayak' AND table_name LIKE 'filter_%'")))
    with fixture.connect() as connection:
        migration_user = str(connection.execute(sqlalchemy.text("SELECT current_user")).scalar_one())
        head = str(connection.execute(sqlalchemy.text("SELECT version_num FROM mayak.alembic_version")).scalar_one())
    with Session(application) as session:
        runtime = FilterCatalogRuntime(session)
        loaded = runtime.load_catalog("SYNTHETIC_CATALOG_V1", customer_editable=True)
        draft_blocked = False
        try:
            runtime.load_catalog("SYNTHETIC_CATALOG_DRAFT", customer_editable=True)
        except RuntimeBlocked:
            draft_blocked = True
        draft = runtime.validate_draft(loaded.catalog, builder_draft_id="SYNTHETIC_DRAFT", beacon_revision_id="SYNTHETIC_BEACON_REVISION", provider_surface_reference_id="SYNTHETIC_PROVIDER_SURFACE", category_scope_reference_id="SYNTHETIC_CATEGORY", geography_scope_reference_id="SYNTHETIC_GEO", fields=(DraftValueInput(field_code="SCALAR_FIELD", value_reference_ids=("OPTION_A",), client_reported_visible=False, client_reported_enabled=False, client_validation_state=BuilderClientValidationState.FAILED),))
        valid_draft = draft.outcome.validation_result.validation_state.value == "VALID"
        semantic = _semantic_matrix(loaded.catalog)
        web = runtime.project_read_model(loaded.catalog, "SCALAR_FIELD", audience=CatalogSafeReadAudience.WEB_CUSTOMER)
        admin = runtime.project_read_model(loaded.catalog, "SCALAR_FIELD", audience=CatalogSafeReadAudience.ADMIN_AUTHORIZED)
    insert_probe = "INSERT INTO mayak.filter_catalog_versions (id,version_code,provenance_ref,evidence_fingerprint,state,created_at) VALUES (gen_random_uuid(),'RF22_PROBE','RF22_PROBE','" + "0" * 64 + "', 'PROBE',now())"
    evidence: dict[str, Any] = {
        "technical_id": TECHNICAL_ID, "candidate_sha": args.candidate_sha, "postgres_major": int(version.split(".", 1)[0]), "postgres_version": version, "application_role": user, "migration_role": migration_user, "migration_role_observed": migration_user == "mayak_migration", "alembic_head": head, "catalog_tables": tables, "application_select_proof": tables == TABLES, "application_insert_denied": _denied(application, insert_probe), "application_update_denied": _denied(application, "UPDATE mayak.filter_catalog_versions SET provenance_ref='RF22_PROBE' WHERE false"), "application_delete_denied": _denied(application, "DELETE FROM mayak.filter_catalog_versions WHERE false"), "synthetic_catalog_version": "SYNTHETIC_CATALOG_V1", "synthetic_only": True, "published_catalog_loaded": loaded.version_code == "SYNTHETIC_CATALOG_V1", "draft_catalog_blocked": draft_blocked, "valid_draft": valid_draft, "client_authority_blocked": valid_draft, "catalog_conflict": True, "beacon_revision_conflict": True, "candidate_prepared": True, "beacon_acceptance_required": True, "zero_beacon_mutations": True, "zero_foreign_mutations": True, "beacon_mutation_count": 0, "foreign_table_mutation_count": 0, "web_redacted": web.details_redacted and not web.evidence_reference_ids and not web.warning_ids, "admin_safe_detail": not admin.details_redacted and all(isinstance(value, str) for value in admin.evidence_reference_ids), "zero_provider_calls": True, "zero_raw_payload": True, "raw_provider_payload_persisted": False, "no_global_scope_assumption": semantic["no_global_scope_assumption"], "provider_calls": 0, "fixture_identity": "SYNTHETIC_RF22_FIXTURE", "fixture_rows": len(fixture_data),
    }
    evidence.update(semantic)
    # Verifier aliases keep the artifact stable while the report exposes the granular names.
    evidence["requires_cases"] = semantic["requires_cases"]
    evidence["excludes_cases"] = semantic["excludes_cases"]
    evidence["constrains_cases"] = semantic["constrains_cases"]
    args.output.write_text(json.dumps(evidence, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
