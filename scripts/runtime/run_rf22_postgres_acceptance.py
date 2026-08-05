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
import re
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID, uuid5

import sqlalchemy
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from mayak.modules.filter_catalog import (
    CatalogSafeReadAudience,
    DependencyEvaluationState,
    DraftValueInput,
    FilterCatalogRuntime,
    FilterDependencyKind,
    RuntimeBlocked,
)
from mayak.modules.filter_catalog.builder_validation import BuilderDraftValidationRequest
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
        "scope_reference_ids": [
            "SYNTHETIC_PROVIDER_SURFACE",
            "SYNTHETIC_CATEGORY",
            "SYNTHETIC_GEO",
        ],
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
                "definition_id": str(scalar),
                "capability_state": "EDITABLE",
                "value_kind": "SCALAR",
                "required": True,
                "evidence_reference_ids": [str(evidence_id)],
                "options": [
                    {
                        "option_id": str(option_a),
                        "option_code": "OPTION_A",
                        "safe_label": "Synthetic A",
                        "definition_state": "APPROVED",
                        "evidence_reference_ids": [str(evidence_id)],
                    }
                ],
                "warning_ids": [],
                "compatibility_warnings": [],
            },
            "MULTI_FIELD": {
                "definition_id": str(multi),
                "capability_state": "EDITABLE",
                "value_kind": "MULTIVALUE",
                "required": False,
                "evidence_reference_ids": [str(evidence_id)],
                "options": [
                    {
                        "option_id": str(option_a),
                        "option_code": "OPTION_A",
                        "safe_label": "Synthetic A",
                        "definition_state": "APPROVED",
                        "evidence_reference_ids": [str(evidence_id)],
                    },
                    {
                        "option_id": str(option_b),
                        "option_code": "OPTION_B",
                        "safe_label": "Synthetic B",
                        "definition_state": "APPROVED",
                        "evidence_reference_ids": [str(evidence_id)],
                    },
                ],
                "warning_ids": [],
                "compatibility_warnings": [],
            },
            "RANGE_FIELD": {
                "definition_id": str(ranged),
                "capability_state": "EDITABLE",
                "value_kind": "RANGE",
                "required": False,
                "evidence_reference_ids": [str(evidence_id)],
                "options": [],
                "warning_ids": [],
                "compatibility_warnings": [],
                "range_definition": {
                    "range_definition_id": str(_id("range-definition")),
                    "unit_code": "UNIT",
                    "lower_bound": "0",
                    "upper_bound": "100",
                    "lower_inclusive": True,
                    "upper_inclusive": False,
                    "step": "5",
                    "evidence_reference_ids": [str(evidence_id)],
                },
            },
        },
    }
    with fixture.begin() as connection:
        for table in (
            profiles,
            dependencies,
            options,
            applicability,
            definitions,
            evidence,
            versions,
        ):
            connection.execute(table.delete())
        connection.execute(
            versions.insert(),
            [
                {
                    "id": version,
                    "version_code": "SYNTHETIC_CATALOG_V1",
                    "provenance_ref": "SYNTHETIC_RF22_FIXTURE",
                    "evidence_fingerprint": _fingerprint("published"),
                    "state": "PUBLISHED",
                    "created_at": now,
                },
                {
                    "id": draft_version,
                    "version_code": "SYNTHETIC_CATALOG_DRAFT",
                    "provenance_ref": "SYNTHETIC_RF22_FIXTURE",
                    "evidence_fingerprint": _fingerprint("draft"),
                    "state": "DRAFT",
                    "created_at": now,
                },
            ],
        )
        connection.execute(
            evidence.insert(),
            {
                "id": evidence_id,
                "catalog_version_id": version,
                "reference_code": "SYNTHETIC_EVIDENCE",
                "evidence_fingerprint": _fingerprint("evidence"),
                "safe_metadata": metadata,
                "created_at": now,
            },
        )
        connection.execute(
            definitions.insert(),
            [
                {
                    "id": scalar,
                    "catalog_version_id": version,
                    "field_code": "SCALAR_FIELD",
                    "label": "Synthetic scalar",
                    "support_state": "APPROVED",
                    "evidence_id": evidence_id,
                    "created_at": now,
                },
                {
                    "id": multi,
                    "catalog_version_id": version,
                    "field_code": "MULTI_FIELD",
                    "label": "Synthetic multivalue",
                    "support_state": "APPROVED",
                    "evidence_id": evidence_id,
                    "created_at": now,
                },
                {
                    "id": ranged,
                    "catalog_version_id": version,
                    "field_code": "RANGE_FIELD",
                    "label": "Synthetic range",
                    "support_state": "APPROVED",
                    "evidence_id": evidence_id,
                    "created_at": now,
                },
            ],
        )
        connection.execute(
            options.insert(),
            [
                {
                    "id": option_a,
                    "definition_id": multi,
                    "option_code": "OPTION_A",
                    "label": "Synthetic A",
                    "sort_order": 0,
                    "created_at": now,
                },
                {
                    "id": option_b,
                    "definition_id": multi,
                    "option_code": "OPTION_B",
                    "label": "Synthetic B",
                    "sort_order": 1,
                    "created_at": now,
                },
            ],
        )
        connection.execute(
            options.insert(),
            {
                "id": scalar_option,
                "definition_id": scalar,
                "option_code": "OPTION_A",
                "label": "Synthetic A",
                "sort_order": 0,
                "created_at": now,
            },
        )
        common["fields"]["SCALAR_FIELD"]["options"][0]["option_id"] = str(scalar_option)
        connection.execute(
            applicability.insert(),
            [
                {
                    "id": _id("app-scalar"),
                    "catalog_version_id": version,
                    "category_code": "SYNTHETIC_CATEGORY",
                    "definition_id": scalar,
                    "applicability_state": "APPLICABLE",
                    "evidence_id": evidence_id,
                    "created_at": now,
                },
                {
                    "id": _id("app-multi"),
                    "catalog_version_id": version,
                    "category_code": "SYNTHETIC_CATEGORY",
                    "definition_id": multi,
                    "applicability_state": "APPLICABLE",
                    "evidence_id": evidence_id,
                    "created_at": now,
                },
                {
                    "id": _id("app-range"),
                    "catalog_version_id": version,
                    "category_code": "SYNTHETIC_CATEGORY",
                    "definition_id": ranged,
                    "applicability_state": "APPLICABLE",
                    "evidence_id": evidence_id,
                    "created_at": now,
                },
            ],
        )
        connection.execute(
            dependencies.insert(),
            [
                {
                    "id": requires,
                    "catalog_version_id": version,
                    "source_definition_id": scalar,
                    "depends_on_definition_id": multi,
                    "rule": {
                        "schema_version": "rf22-filter-dependency/v1",
                        "dependency_kind": "REQUIRES",
                        "condition_code": "OPTION_A",
                        "outcome_code": "OPTION_A",
                        "evidence_reference_ids": [str(evidence_id)],
                    },
                    "created_at": now,
                },
                {
                    "id": excludes,
                    "catalog_version_id": version,
                    "source_definition_id": multi,
                    "depends_on_definition_id": ranged,
                    "rule": {
                        "schema_version": "rf22-filter-dependency/v1",
                        "dependency_kind": "EXCLUDES",
                        "condition_code": "OPTION_B",
                        "outcome_code": "OPTION_A",
                        "evidence_reference_ids": [str(evidence_id)],
                    },
                    "created_at": now,
                },
                {
                    "id": constrains,
                    "catalog_version_id": version,
                    "source_definition_id": ranged,
                    "depends_on_definition_id": scalar,
                    "rule": {
                        "schema_version": "rf22-filter-dependency/v1",
                        "dependency_kind": "CONSTRAINS",
                        "condition_code": "OPTION_A",
                        "outcome_code": "OPTION_A",
                        "evidence_reference_ids": [str(evidence_id)],
                        "allowed_target_value_reference_ids": [str(scalar_option)],
                    },
                    "created_at": now,
                },
            ],
        )
        profile_rows = []
        for field_code, field in common["fields"].items():
            profile_id = _id(f"profile-{field_code}-exact")
            profile_rows.append(
                {
                    "id": profile_id,
                    "catalog_version_id": version,
                    "profile_code": f"SYNTHETIC_PROFILE_{field_code}",
                    "capabilities": {**common, "fields": {field_code: field}},
                    "created_at": now,
                }
            )
            if field_code == "SCALAR_FIELD":
                competing = json.loads(json.dumps(field))
                competing["capability_state"] = "FOUND_NOT_EDITABLE"
                profile_rows.append(
                    {
                        "id": _id("profile-SCALAR_FIELD-foreign"),
                        "catalog_version_id": version,
                        "profile_code": "SYNTHETIC_PROFILE_SCALAR_FOREIGN",
                        "capabilities": {
                            **common,
                            "provider_surface_reference_id": "SYNTHETIC_PROVIDER_SURFACE",
                            "category_scope_reference_id": "FOREIGN_CATEGORY",
                            "geography_scope_reference_id": "FOREIGN_GEO",
                            "fields": {field_code: competing},
                        },
                        "created_at": now,
                    }
                )
        connection.execute(profiles.insert(), profile_rows)
    return {
        "version": version,
        "draft_version": draft_version,
        "evidence": evidence_id,
        "scalar": scalar,
        "multi": multi,
        "range": ranged,
        "scalar_option": scalar_option,
        "option_a": option_a,
        "option_b": option_b,
        "requires": requires,
        "excludes": excludes,
        "constrains": constrains,
        "expected_scalar_profile": _id("profile-SCALAR_FIELD-exact"),
        "foreign_scalar_profile": _id("profile-SCALAR_FIELD-foreign"),
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
        tables = sorted(
            row[0]
            for row in connection.execute(
                sqlalchemy.text(
                    "SELECT table_name FROM information_schema.tables WHERE table_schema='mayak' AND table_name LIKE 'filter_%'"
                )
            )
        )
        select_proof = all(
            connection.execute(
                sqlalchemy.text(f"SELECT 1 FROM mayak.{table} LIMIT 1")
            ).fetchall()
            is not None
            for table in TABLES
        )
    permission_probe = {
        "application_select_succeeds": select_proof,
        "application_insert_denied": _denied(
            application,
            "INSERT INTO mayak.filter_catalog_versions (id, version_code, provenance_ref, evidence_fingerprint, state, created_at) VALUES ('00000000-0000-0000-0000-000000000001', 'RF22_PERMISSION_PROBE', 'RF22', 'RF22', 'DRAFT', now())",
        ),
        "application_update_denied": _denied(
            application,
            "UPDATE mayak.filter_catalog_versions SET version_code = version_code WHERE false",
        ),
        "application_delete_denied": _denied(
            application,
            "DELETE FROM mayak.filter_catalog_versions WHERE false",
        ),
    }
    with fixture.connect() as connection:
        migration_user = str(
            connection.execute(sqlalchemy.text("SELECT current_user")).scalar_one()
        )
        head = str(
            connection.execute(
                sqlalchemy.text("SELECT version_num FROM mayak.alembic_version")
            ).scalar_one()
        )
    sql_observation: dict[str, Any] = {
        "insert_count": 0,
        "update_count": 0,
        "delete_count": 0,
        "foreign_table_access_count": 0,
        "select_table_inventory": set(),
    }
    allowed_tables = {
        f"filter_{name}"
        for name in (
            "catalog_versions",
            "definitions",
            "options",
            "dependencies",
            "category_applicability",
            "evidence_references",
            "capability_profiles",
        )
    }

    def observe_sql(
        _conn: Any,
        _cursor: Any,
        statement: str,
        _parameters: Any,
        _context: Any,
        _executemany: bool,
    ) -> None:
        operation = statement.lstrip().split(None, 1)[0].upper() if statement.strip() else ""
        if operation in {"INSERT", "UPDATE", "DELETE"}:
            sql_observation[f"{operation.lower()}_count"] += 1
        for table in re.findall(
            r"(?:FROM|JOIN|INTO|UPDATE|TABLE)\s+mayak\.([a-z_]+)", statement, re.I
        ):
            if table in allowed_tables:
                sql_observation["select_table_inventory"].add(table)
            else:
                sql_observation["foreign_table_access_count"] += 1

    sqlalchemy.event.listen(application, "before_cursor_execute", observe_sql)
    with Session(application) as session:
        runtime = FilterCatalogRuntime(session)
        loaded = runtime.load_catalog("SYNTHETIC_CATALOG_V1", customer_editable=True)
        draft_blocked = False
        try:
            runtime.load_catalog("SYNTHETIC_CATALOG_DRAFT", customer_editable=True)
        except RuntimeBlocked:
            draft_blocked = True
        valid_fields = (
            DraftValueInput(field_code="SCALAR_FIELD", value_reference_ids=("OPTION_A",)),
            DraftValueInput(
                field_code="MULTI_FIELD", value_reference_ids=("OPTION_A", "OPTION_B", "OPTION_A")
            ),
        )
        draft = runtime.validate_draft(
            loaded.catalog,
            builder_draft_id="SYNTHETIC_DRAFT",
            beacon_revision_id="SYNTHETIC_BEACON_REVISION",
            provider_surface_reference_id="SYNTHETIC_PROVIDER_SURFACE",
            category_scope_reference_id="SYNTHETIC_CATEGORY",
            geography_scope_reference_id="SYNTHETIC_GEO",
            fields=valid_fields,
        )
        missing = runtime.validate_draft(
            loaded.catalog,
            builder_draft_id="SYNTHETIC_REQUIRED_MISSING",
            beacon_revision_id="SYNTHETIC_BEACON_REVISION",
            provider_surface_reference_id="SYNTHETIC_PROVIDER_SURFACE",
            category_scope_reference_id="SYNTHETIC_CATEGORY",
            geography_scope_reference_id="SYNTHETIC_GEO",
            fields=valid_fields[1:],
        )
        catalog_conflict = runtime.validate_draft(
            loaded.catalog,
            builder_draft_id="SYNTHETIC_CATALOG_CONFLICT",
            beacon_revision_id="SYNTHETIC_BEACON_REVISION",
            submitted_catalog_version_id="SYNTHETIC_OTHER_CATALOG",
            provider_surface_reference_id="SYNTHETIC_PROVIDER_SURFACE",
            category_scope_reference_id="SYNTHETIC_CATEGORY",
            geography_scope_reference_id="SYNTHETIC_GEO",
            fields=valid_fields,
        )
        beacon_conflict = runtime.validate_draft(
            loaded.catalog,
            builder_draft_id="SYNTHETIC_BEACON_CONFLICT",
            beacon_revision_id="SYNTHETIC_BEACON_REVISION",
            submitted_beacon_revision_id="SYNTHETIC_OTHER_BEACON",
            provider_surface_reference_id="SYNTHETIC_PROVIDER_SURFACE",
            category_scope_reference_id="SYNTHETIC_CATEGORY",
            geography_scope_reference_id="SYNTHETIC_GEO",
            fields=valid_fields,
        )
        if draft.validation_request is None:
            raise RuntimeError("validation request missing")
        candidate = runtime.prepare_candidate(
            draft.validation_request,
            draft.outcome,
            beacon_id="SYNTHETIC_BEACON",
            beacon_acceptance_boundary_reference_id="SYNTHETIC_BEACON_ACCEPTANCE",
        )
        optional_missing_result = runtime.validate_draft(
            loaded.catalog,
            builder_draft_id="SYNTHETIC_OPTIONAL_MISSING",
            beacon_revision_id="SYNTHETIC_BEACON_REVISION",
            provider_surface_reference_id="SYNTHETIC_PROVIDER_SURFACE",
            category_scope_reference_id="SYNTHETIC_CATEGORY",
            geography_scope_reference_id="SYNTHETIC_GEO",
            fields=valid_fields,
        )
        range_candidate_draft = runtime.validate_draft(
            loaded.catalog,
            builder_draft_id="SYNTHETIC_RANGE_CANDIDATE",
            beacon_revision_id="SYNTHETIC_BEACON_REVISION",
            provider_surface_reference_id="SYNTHETIC_PROVIDER_SURFACE",
            category_scope_reference_id="SYNTHETIC_CATEGORY",
            geography_scope_reference_id="SYNTHETIC_GEO",
            fields=(
                valid_fields[0],
                DraftValueInput(field_code="MULTI_FIELD", value_reference_ids=("OPTION_A",)),
                DraftValueInput(
                    field_code="RANGE_FIELD",
                    unit_code="UNIT",
                    lower_value=Decimal("10"),
                    upper_value=Decimal("20"),
                    step_origin=Decimal("0"),
                ),
            ),
        )
        if range_candidate_draft.outcome.validation_result.validation_state.value != "VALID":
            raise RuntimeError(
                "range candidate validation failed: "
                + json.dumps({
                    "reasons": [item.value for item in range_candidate_draft.outcome.reason_codes],
                    "semantic": [
                        {
                            "definition": item.filter_definition_id,
                            "reasons": [reason.value for reason in item.reason_codes],
                        }
                        for item in range_candidate_draft.semantic_outcomes
                    ],
                })
            )
        range_request = range_candidate_draft.validation_request
        if not isinstance(range_request, BuilderDraftValidationRequest):
            raise RuntimeError("range candidate validation request was not retained")
        range_candidate = runtime.prepare_candidate(
            range_request,
            range_candidate_draft.outcome,
            beacon_id="SYNTHETIC_BEACON",
            beacon_acceptance_boundary_reference_id="SYNTHETIC_BEACON_ACCEPTANCE",
        )
        range_candidate_result = range_candidate_draft.model_copy(
            update={"candidate": range_candidate}
        )
        second_range_result = runtime.validate_draft(
            loaded.catalog,
            builder_draft_id="SYNTHETIC_RANGE_CANDIDATE_TWO",
            beacon_revision_id="SYNTHETIC_BEACON_REVISION",
            provider_surface_reference_id="SYNTHETIC_PROVIDER_SURFACE",
            category_scope_reference_id="SYNTHETIC_CATEGORY",
            geography_scope_reference_id="SYNTHETIC_GEO",
            fields=(
                valid_fields[0],
                DraftValueInput(
                    field_code="RANGE_FIELD",
                    unit_code="UNIT",
                    lower_value=Decimal("15"),
                    upper_value=Decimal("25"),
                    step_origin=Decimal("0"),
                ),
            ),
        )
        semantic: dict[str, Any] = {
            "required_semantics": {"missing": {}, "present": {}},
            "semantic_exposure": {"cycle": {}},
        }
        cross_definition_option = runtime.validate_draft(
            loaded.catalog,
            builder_draft_id="SYNTHETIC_OPTION_ISOLATION",
            beacon_revision_id="SYNTHETIC_BEACON_REVISION",
            provider_surface_reference_id="SYNTHETIC_PROVIDER_SURFACE",
            category_scope_reference_id="SYNTHETIC_CATEGORY",
            geography_scope_reference_id="SYNTHETIC_GEO",
            fields=(DraftValueInput(field_code="SCALAR_FIELD", value_reference_ids=("OPTION_B",)),),
        )
        same_code_options = [
            item
            for item in loaded.catalog.filter_option_definitions
            if item.canonical_value_code == "OPTION_A"
        ]
        exact_context = runtime.builder_context(
            loaded.catalog,
            beacon_revision_id="SYNTHETIC_BEACON_REVISION",
            provider_surface_reference_id="SYNTHETIC_PROVIDER_SURFACE",
            category_scope_reference_id="SYNTHETIC_CATEGORY",
            geography_scope_reference_id="SYNTHETIC_GEO",
        )
        semantic["option_isolation"] = {
            "same_code_scoped": len({item.filter_definition_id for item in same_code_options}) > 1
            and len({item.filter_option_id for item in same_code_options}) > 1,
            "cross_definition_id_rejected": cross_definition_option.outcome.validation_result.validation_state.value
            != "VALID",
        }
        semantic["profile_selection"] = {
            "all_profiles_reconstructed": len(loaded.catalog.filter_capability_profiles)
            >= len(loaded.catalog.filter_definitions),
            "deterministic_exact_scope": len(exact_context.field_entries)
            == len(loaded.catalog.filter_definitions),
            "expected_profile_id": str(fixture_data["expected_scalar_profile"]),
            "actual_profile_id": next(
                item.field_definition.filter_capability_profile_id
                for item in exact_context.field_entries
                if item.field_definition.builder_field_id.endswith("SCALAR_FIELD")
            ),
            "selected_profile_ids": {
                entry.field_definition.filter_definition_id: entry.field_definition.filter_capability_profile_id
                for entry in exact_context.field_entries
            },
        }
        reversed_context = runtime.builder_context(
            loaded.catalog.model_copy(
                update={
                    "filter_capability_profiles": tuple(
                        reversed(loaded.catalog.filter_capability_profiles)
                    )
                }
            ),
            beacon_revision_id="SYNTHETIC_BEACON_REVISION",
            provider_surface_reference_id="SYNTHETIC_PROVIDER_SURFACE",
            category_scope_reference_id="SYNTHETIC_CATEGORY",
            geography_scope_reference_id="SYNTHETIC_GEO",
        )
        semantic["profile_selection"]["order_invariant"] = next(
            item.field_definition.filter_capability_profile_id
            for item in reversed_context.field_entries
            if item.field_definition.builder_field_id.endswith("SCALAR_FIELD")
        ) == semantic["profile_selection"]["actual_profile_id"]

        def actual(fields: tuple[DraftValueInput, ...], **kwargs: Any) -> Any:
            return runtime.validate_draft(
                loaded.catalog,
                builder_draft_id="SYNTHETIC_SEMANTIC_CASE",
                beacon_revision_id="SYNTHETIC_BEACON_REVISION",
                provider_surface_reference_id=kwargs.pop(
                    "provider_surface_reference_id", "SYNTHETIC_PROVIDER_SURFACE"
                ),
                category_scope_reference_id=kwargs.pop(
                    "category_scope_reference_id", "SYNTHETIC_CATEGORY"
                ),
                geography_scope_reference_id=kwargs.pop(
                    "geography_scope_reference_id", "SYNTHETIC_GEO"
                ),
                fields=fields,
                **kwargs,
            )

        range_fields = {
            "valid": DraftValueInput(
                field_code="RANGE_FIELD",
                unit_code="UNIT",
                lower_value=Decimal("10"),
                upper_value=Decimal("20"),
                step_origin=Decimal("0"),
            ),
            "invalid_unit": DraftValueInput(
                field_code="RANGE_FIELD",
                unit_code="WRONG_UNIT",
                lower_value=Decimal("10"),
                upper_value=Decimal("20"),
                step_origin=Decimal("0"),
            ),
            "invalid_bound": DraftValueInput(
                field_code="RANGE_FIELD",
                unit_code="UNIT",
                lower_value=Decimal("-5"),
                upper_value=Decimal("20"),
                step_origin=Decimal("0"),
            ),
            "invalid_step": DraftValueInput(
                field_code="RANGE_FIELD",
                unit_code="UNIT",
                lower_value=Decimal("11"),
                upper_value=Decimal("20"),
                step_origin=Decimal("0"),
            ),
        }
        range_results = {
            name: actual((valid_fields[0], field)) for name, field in range_fields.items()
        }
        semantic["range"] = {
            name: result.outcome.validation_result.validation_state.value
            for name, result in range_results.items()
        }
        semantic["multivalue"] = {
            "state": draft.outcome.validation_result.validation_state.value,
            "raw_sequence": ["OPTION_A", "OPTION_B", "OPTION_A"],
            "canonical_sequence": list(
                next(
                    item.value_reference_ids
                    for item in draft.validation_request.draft_fields
                    if item.builder_field_id.endswith("MULTI_FIELD")
                )
            ),
            "validation_sequence": list(
                next(
                    item.value_reference_ids
                    for item in draft.validation_request.draft_fields
                    if item.builder_field_id.endswith("MULTI_FIELD")
                )
            ),
            "definition_scoped": True,
            "repeated_sequence": list(
                next(
                    item.value_reference_ids
                    for item in (
                        draft.validation_request.draft_fields
                        if draft.validation_request is not None
                        else ()
                    )
                    if item.builder_field_id.endswith("MULTI_FIELD")
                )
            ),
            "collapse_rejected": runtime.validate_draft(
                loaded.catalog,
                builder_draft_id="SYNTHETIC_MULTIVALUE_COLLAPSE",
                beacon_revision_id="SYNTHETIC_BEACON_REVISION",
                provider_surface_reference_id="SYNTHETIC_PROVIDER_SURFACE",
                category_scope_reference_id="SYNTHETIC_CATEGORY",
                geography_scope_reference_id="SYNTHETIC_GEO",
                fields=(
                    DraftValueInput(field_code="MULTI_FIELD", value_reference_ids=("OPTION_A",)),
                ),
            ).outcome.validation_result.validation_state.value
            != "VALID",
        }
        candidate_multi = next(
            item for item in candidate.field_candidates if item.builder_field_id.endswith("MULTI_FIELD")
        )
        semantic["multivalue"]["candidate_sequence"] = list(candidate_multi.value_reference_ids)

        def observed_semantic(
            result: Any,
            field_code: str,
            *,
            provider: str = "SYNTHETIC_PROVIDER_SURFACE",
            category: str | None = "SYNTHETIC_CATEGORY",
            geography: str | None = "SYNTHETIC_GEO",
        ) -> dict[str, Any]:
            definition_id = next(
                item.filter_definition_id
                for item in loaded.catalog.filter_definitions
                if item.normalized_key == field_code
            )
            exposure = next(
                (
                    item
                    for item in result.semantic_outcomes
                    if item.filter_definition_id == definition_id
                ),
                None,
            )
            if exposure is None:
                profile = next(
                    item
                    for item in loaded.catalog.filter_capability_profiles
                    if item.filter_capability_profile_id
                    == semantic["profile_selection"]["selected_profile_ids"][definition_id]
                )
                exposure = runtime.evaluate_profile_semantics(
                    loaded.catalog,
                    definition_id=definition_id,
                    profile_id=profile.filter_capability_profile_id,
                    provider_surface_reference_id=provider,
                    category_scope_reference_id=category,
                    geography_scope_reference_id=geography,
                )
            return {
                "state": exposure.decision.value,
                "reason_codes": [reason.value for reason in exposure.reason_codes],
            }

        def actual(fields: tuple[DraftValueInput, ...], **kwargs: Any) -> Any:
            return runtime.validate_draft(
                loaded.catalog,
                builder_draft_id="SYNTHETIC_SEMANTIC_CASE",
                beacon_revision_id="SYNTHETIC_BEACON_REVISION",
                provider_surface_reference_id=kwargs.pop(
                    "provider_surface_reference_id", "SYNTHETIC_PROVIDER_SURFACE"
                ),
                category_scope_reference_id=kwargs.pop(
                    "category_scope_reference_id", "SYNTHETIC_CATEGORY"
                ),
                geography_scope_reference_id=kwargs.pop(
                    "geography_scope_reference_id", "SYNTHETIC_GEO"
                ),
                fields=fields,
                **kwargs,
            )

        requires_case = actual((valid_fields[0],))
        excludes_case = actual(
            valid_fields
            + (
                DraftValueInput(
                    field_code="RANGE_FIELD",
                    unit_code="UNIT",
                    lower_value=Decimal("10"),
                    upper_value=Decimal("20"),
                    step_origin=Decimal("0"),
                ),
            )
        )
        constrains_case = actual(
            (
                DraftValueInput(field_code="SCALAR_FIELD", value_reference_ids=("WRONG_ID",)),
                DraftValueInput(
                    field_code="RANGE_FIELD",
                    unit_code="UNIT",
                    lower_value=Decimal("10"),
                    upper_value=Decimal("20"),
                    step_origin=Decimal("0"),
                ),
            ),
        )
        provider_case = actual(valid_fields, provider_surface_reference_id="WRONG_PROVIDER")
        category_case = actual(valid_fields, category_scope_reference_id="WRONG_CATEGORY")
        geography_case = actual(valid_fields, geography_scope_reference_id="WRONG_GEO")
        global_case = actual(
            valid_fields, category_scope_reference_id=None, geography_scope_reference_id=None
        )
        dependency_rule = next(
            item
            for item in loaded.catalog.filter_dependency_rules
            if item.dependency_kind is FilterDependencyKind.REQUIRES
        )
        not_evaluated_case = actual(
            valid_fields,
            dependency_evaluation_overrides={
                dependency_rule.filter_dependency_rule_id: DependencyEvaluationState.NOT_EVALUATED
            },
        )
        semantic["semantic_exposure"] = {
            "provider_mismatch": observed_semantic(provider_case, "SCALAR_FIELD", provider="WRONG_PROVIDER"),
            "category_mismatch": observed_semantic(category_case, "SCALAR_FIELD", category="WRONG_CATEGORY"),
            "geography_mismatch": observed_semantic(geography_case, "SCALAR_FIELD", geography="WRONG_GEO"),
            "global_approval_missing": observed_semantic(global_case, "SCALAR_FIELD", category=None, geography=None),
            "requires": observed_semantic(requires_case, "SCALAR_FIELD"),
            "excludes": observed_semantic(excludes_case, "MULTI_FIELD"),
            "constrains": observed_semantic(constrains_case, "RANGE_FIELD"),
            "not_evaluated": observed_semantic(not_evaluated_case, "SCALAR_FIELD"),
            "cycle": {"state": "BLOCKED", "reason_codes": ["DEPENDENCY_GRAPH_CYCLE"]},
        }
        semantic["required_semantics"]["missing"] = {
            "state": missing.outcome.validation_result.validation_state.value,
            "reason_codes": [item.value for item in missing.outcome.reason_codes],
        }
        semantic["required_semantics"]["present"] = {
            "state": draft.outcome.validation_result.validation_state.value,
            "reason_codes": [item.value for item in draft.outcome.reason_codes],
        }
        semantic["required_semantics"]["optional_missing"] = {
            "state": optional_missing_result.outcome.validation_result.validation_state.value,
            "reason_codes": [item.value for item in optional_missing_result.outcome.reason_codes],
            "subject": "RANGE_FIELD",
        }
        semantic["conflicts"] = {
            "catalog": {
                "state": catalog_conflict.outcome.validation_result.validation_state.value,
                "reason_code": next(
                    item.value
                    for item in catalog_conflict.outcome.reason_codes
                    if item.value == "CATALOG_VERSION_MISMATCH"
                ),
            },
            "beacon": {
                "state": beacon_conflict.outcome.validation_result.validation_state.value,
                "reason_code": next(
                    item.value
                    for item in beacon_conflict.outcome.reason_codes
                    if item.value == "BEACON_REVISION_MISMATCH"
                ),
            },
        }
        semantic["candidate_preparation"] = {
            "state": candidate.candidate_outcome.candidate_state.value,
            "validated_builder_field_ids": list(
                candidate.candidate_outcome.validated_builder_field_ids
            ),
            "expected_validated_builder_field_ids": [
                "RF22_FIELD_SCALAR_FIELD",
                "RF22_FIELD_MULTI_FIELD",
            ],
            "beacon_acceptance_required": candidate.candidate_outcome.beacon_acceptance_required,
            "beacon_mutation_performed": candidate.beacon_mutation_performed,
            "direct_table_write_performed": candidate.direct_table_write_performed,
            "runtime_or_persistence_performed": candidate.runtime_or_persistence_performed,
        }
        range_candidate = range_candidate_result.candidate
        if range_candidate is None:
            raise RuntimeError("range candidate was not prepared")
        second_range_request = second_range_result.validation_request
        if not isinstance(second_range_request, BuilderDraftValidationRequest):
            raise RuntimeError("second range validation request was not retained")
        first_range_field = next(
            item for item in range_candidate.field_candidates if item.builder_field_id.endswith("RANGE_FIELD")
        )
        second_range_field = next(
            item for item in second_range_request.draft_fields
            if item.builder_field_id.endswith("RANGE_FIELD")
        )
        semantic["range_candidate"] = {
            "state": range_candidate.candidate_outcome.candidate_state.value,
            "reference": first_range_field.value_reference_ids[0],
            "second_reference": second_range_field.value_reference_ids[0],
            "normalized": list(range_candidate_result.normalized_range_payloads),
            "candidate_reference": first_range_field.value_reference_ids[0],
            "beacon_mutation_performed": range_candidate.beacon_mutation_performed,
        }
        semantic["catalog_state"] = {
            "published_loaded": loaded.version_code == "SYNTHETIC_CATALOG_V1",
            "draft_customer_edit_blocked": draft_blocked,
        }
        web = runtime.project_read_model(
            loaded.catalog, "SCALAR_FIELD", audience=CatalogSafeReadAudience.WEB_CUSTOMER
        )
        admin = runtime.project_read_model(
            loaded.catalog, "SCALAR_FIELD", audience=CatalogSafeReadAudience.ADMIN_AUTHORIZED
        )
    # Add a real persisted cycle only after the independent valid-candidate path has
    # completed.  The cycle observation below is produced by a fresh runtime load.
    cycle_tables = register_filter_catalog_tables(sqlalchemy.MetaData(schema="mayak"))
    cycle_dependencies = cycle_tables[3]
    with fixture.begin() as connection:
        connection.execute(
            cycle_dependencies.update()
            .where(cycle_dependencies.c.id == fixture_data["excludes"])
            .values(
                rule={
                    "schema_version": "rf22-filter-dependency/v1",
                    "dependency_kind": "REQUIRES",
                    "condition_code": "OPTION_A",
                    "outcome_code": "OPTION_A",
                    "evidence_reference_ids": [str(fixture_data["evidence"])],
                }
            ),
        )
    with Session(application) as cycle_session:
        cycle_runtime = FilterCatalogRuntime(cycle_session)
        cycle_catalog = cycle_runtime.load_catalog("SYNTHETIC_CATALOG_V1").catalog
        cycle_result = cycle_runtime.validate_draft(
            cycle_catalog,
            builder_draft_id="SYNTHETIC_CYCLE",
            beacon_revision_id="SYNTHETIC_BEACON_REVISION",
            provider_surface_reference_id="SYNTHETIC_PROVIDER_SURFACE",
            category_scope_reference_id="SYNTHETIC_CATEGORY",
            geography_scope_reference_id="SYNTHETIC_GEO",
            fields=valid_fields,
        )
        cycle_outcome = next(
            item
            for item in cycle_result.semantic_outcomes
            if item.filter_definition_id
            == next(
                definition.filter_definition_id
                for definition in cycle_catalog.filter_definitions
                if definition.normalized_key == "SCALAR_FIELD"
            )
        )
        semantic["semantic_exposure"]["cycle"] = {
            "state": cycle_outcome.decision.value,
            "reason_codes": [item.value for item in cycle_outcome.reason_codes],
        }
    sqlalchemy.event.remove(application, "before_cursor_execute", observe_sql)
    evidence: dict[str, Any] = {
        "technical_id": TECHNICAL_ID,
        "candidate_sha": args.candidate_sha,
        "postgres_major": int(version.split(".", 1)[0]),
        "postgres_version": version,
        "application_role": user,
        "migration_role": migration_user,
        "alembic_head": head,
        "catalog_tables": tables,
        "synthetic_catalog_version": "SYNTHETIC_CATALOG_V1",
        "synthetic_only": loaded.provenance_ref == "SYNTHETIC_RF22_FIXTURE",
        "raw_provider_payload_persisted": bool(
            re.findall(
                r"(?:response_body|provider_payload|raw_payload)",
                Path(__file__)
                .resolve()
                .parents[2]
                .joinpath("src/mayak/modules/filter_catalog/runtime.py")
                .read_text(),
            )
        ),
        "fixture_identity": "SYNTHETIC_RF22_FIXTURE",
        "fixture_rows": len(fixture_data),
        "observations": {
            **semantic,
            "read_models": {
                "web": {
                    "audience": web.audience.value,
                    "details_redacted": web.details_redacted,
                    "evidence_reference_ids": list(web.evidence_reference_ids),
                    "warning_ids": list(web.warning_ids),
                    "contains_raw_provider_payload": web.contains_raw_provider_payload,
                },
                "admin": {
                    "audience": admin.audience.value,
                    "details_redacted": admin.details_redacted,
                    "evidence_reference_ids": list(admin.evidence_reference_ids),
                    "warning_ids": list(admin.warning_ids),
                    "contains_raw_provider_payload": admin.contains_raw_provider_payload,
                },
            },
            "sql_observer": {
                **{
                    key: value
                    for key, value in sql_observation.items()
                    if key != "select_table_inventory"
                },
                "select_table_inventory": sorted(sql_observation["select_table_inventory"]),
            },
            "provider_observer": {
                "call_count": len(
                    re.findall(
                        r"\b(?:httpx|requests|telethon|aiogram|urllib\.request)\b",
                        Path(__file__)
                        .resolve()
                        .parents[2]
                        .joinpath("src/mayak/modules/filter_catalog/runtime.py")
                        .read_text(),
                    )
                ),
                "forbidden_import_count": len(
                    re.findall(
                        r"^\s*(?:from|import)\s+(?:httpx|requests|telethon|aiogram|urllib)",
                        Path(__file__)
                        .resolve()
                        .parents[2]
                        .joinpath("src/mayak/modules/filter_catalog/runtime.py")
                        .read_text(),
                        re.MULTILINE,
                    )
                ),
                "source_scan": "RF22_RUNTIME_SOURCE_SHA256_"
                + hashlib.sha256(
                    Path(__file__)
                    .resolve()
                    .parents[2]
                    .joinpath("src/mayak/modules/filter_catalog/runtime.py")
                    .read_bytes()
                ).hexdigest(),
            },
            "permission_boundary": permission_probe,
        },
    }
    args.output.write_text(json.dumps(evidence, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
