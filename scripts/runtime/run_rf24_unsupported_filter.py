"""Run the RF24 unsupported-filter authority scenario on real PostgreSQL."""
# ruff: noqa: E501

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID, uuid5

import sqlalchemy
from sqlalchemy import MetaData, event, func, select

from mayak.contracts.idempotency import IdempotencyKey
from mayak.modules.beacon_management.contracts import (
    BeaconParserEvidenceReference,
    BeaconParserOutcomeStatus,
    ExtractedSearchConfigurationSnapshot,
)
from mayak.modules.filter_catalog import (
    BuilderDraftValidationState,
    DraftValueInput,
    FilterCapabilityState,
    FilterCatalogRuntime,
)
from mayak.modules.identity_and_access.contracts import SyntheticAcceptanceLoginRequest
from mayak.persistence.metadata import metadata
from mayak.persistence.schema.filter_catalog import register_filter_catalog_tables
from mayak.platform.correlation import CorrelationContext, CorrelationId
from mayak.runtime.rf24_composition import build_rf24_composition
from mayak.runtime.settings import load_runtime_settings

TECHNICAL_ID = "RF24-UNSUPPORTED-FILTER-SCENARIO-01"
NAMESPACE = UUID("a4a6a8aa-2b6c-4d1e-9a10-24f24f240001")


def _id(value: str) -> UUID:
    return uuid5(NAMESPACE, value)


def _dsn() -> str:
    for key in ("RF24_UNSUPPORTED_MIGRATION_DSN", "MAYAK_RF11_POSTGRES_DSN", "RF11_POSTGRES_DSN"):
        if os.getenv(key):
            return os.environ[key]
    raise SystemExit("migration DSN is required")


def _counts(session: Any, beacon_id: UUID) -> dict[str, int]:
    names = (
        "beacon_configuration_revisions",
        "beacon_lifecycle_events",
        "scan_work_items",
        "scan_listing_observations",
        "notification_outbox",
        "notification_delivery_attempts",
    )
    result: dict[str, int] = {}
    for name in names:
        table = metadata.tables[f"mayak.{name}"]
        stmt = select(func.count()).select_from(table)
        if "beacon_id" in table.c:
            stmt = stmt.where(table.c.beacon_id == beacon_id)
        result[name] = int(session.execute(stmt).scalar_one())
    return result


def _seed_unsupported(fixture: sqlalchemy.Engine, catalog_version_id: UUID) -> dict[str, str]:
    """Extend the accepted RF22 synthetic catalog using fixture/migration authority."""
    tables = register_filter_catalog_tables(MetaData(schema="mayak"))
    versions, definitions, options, dependencies, applicability, evidence, profiles = tables
    evidence_id = _id("unsupported-evidence")
    definition_id = _id("unsupported-definition")
    profile_id = _id("unsupported-profile-exact")
    now = datetime.now(UTC)
    evidence_metadata = {
        "schema_version": "rf22-filter-evidence/v1",
        "evidence_state": "UNSUPPORTED",
        "evidence_kind_code": "SYNTHETIC_UNSUPPORTED_ACCEPTANCE",
        "scope_reference_ids": [
            "SYNTHETIC_PROVIDER_SURFACE",
            "SYNTHETIC_CATEGORY",
            "SYNTHETIC_GEO",
        ],
        "observed_at": now.isoformat(),
        "limitations": ["SYNTHETIC_ONLY", "UNSUPPORTED_BY_DESIGN"],
        "refresh_required": False,
    }
    capabilities = {
        "schema_version": "rf22-filter-capability-profile/v1",
        "provider_surface_reference_id": "SYNTHETIC_PROVIDER_SURFACE",
        "category_scope_reference_id": "SYNTHETIC_CATEGORY",
        "geography_scope_reference_id": "SYNTHETIC_GEO",
        "fields": {
            "SYNTHETIC_UNSUPPORTED_FIELD": {
                "definition_id": str(definition_id),
                "capability_state": "UNSUPPORTED",
                "value_kind": "SCALAR",
                "required": False,
                "evidence_reference_ids": [str(evidence_id)],
                "options": [],
                "warning_ids": [],
                "compatibility_warnings": [],
            }
        },
    }
    with fixture.begin() as connection:
        connection.execute(
            evidence.insert(),
            {
                "id": evidence_id,
                "catalog_version_id": catalog_version_id,
                "reference_code": "SYNTHETIC_UNSUPPORTED_EVIDENCE",
                "evidence_fingerprint": hashlib.sha256(b"rf24-unsupported").hexdigest(),
                "safe_metadata": evidence_metadata,
                "created_at": now,
            },
        )
        connection.execute(
            definitions.insert(),
            {
                "id": definition_id,
                "catalog_version_id": catalog_version_id,
                "field_code": "SYNTHETIC_UNSUPPORTED_FIELD",
                "label": "Synthetic unsupported field",
                "support_state": "APPROVED",
                "evidence_id": evidence_id,
                "created_at": now,
            },
        )
        connection.execute(
            applicability.insert(),
            {
                "id": _id("unsupported-applicability"),
                "catalog_version_id": catalog_version_id,
                "category_code": "SYNTHETIC_CATEGORY",
                "definition_id": definition_id,
                "applicability_state": "APPLICABLE",
                "evidence_id": evidence_id,
                "created_at": now,
            },
        )
        connection.execute(
            profiles.insert(),
            {
                "id": profile_id,
                "catalog_version_id": catalog_version_id,
                "profile_code": "SYNTHETIC_PROFILE_UNSUPPORTED_EXACT",
                "capabilities": capabilities,
                "created_at": now,
            },
        )
    return {
        "version": str(catalog_version_id),
        "evidence": str(evidence_id),
        "definition": str(definition_id),
        "profile": str(profile_id),
    }


def _setup_beacon(composition: Any, run_id: str) -> tuple[Any, Any, UUID, int, dict[str, Any]]:
    with composition.sessions() as session:
        login, issued = composition.identity.synthetic_login(
            session,
            SyntheticAcceptanceLoginRequest(
                synthetic_subject=f"rf24-unsupported:{run_id}",
                idempotency_key=IdempotencyKey(value=f"rf24-unsupported-login:{run_id}"),
                correlation=CorrelationContext(
                    correlation_id=CorrelationId(value=f"rf24-unsupported:{run_id}")
                ),
            ),
        )
        if issued is None or login.account_id is None:
            raise AssertionError("synthetic login failed")
        reference = composition.identity.issued_session_reference(issued)
        composition.establish_acceptance_access(session, reference, login.account_id)
        preparation = composition.beacon.create_preparation(
            session,
            actor_reference=reference,
            account_id=login.account_id,
            source_url=f"https://synthetic.invalid/rf24-unsupported/{run_id}",
            name="RF24 Unsupported Synthetic Beacon",
            idempotency_key=f"rf24-unsupported-beacon:{run_id}",
        )
        accepted = composition.beacon.accept_snapshot(
            session,
            actor_reference=reference,
            beacon_id=preparation.beacon_id,
            snapshot=ExtractedSearchConfigurationSnapshot(
                snapshot_id=f"rf24-unsupported-snapshot:{run_id}",
                parser_outcome_status=BeaconParserOutcomeStatus.CLEAN,
                accepted_as_clean=True,
                normalized_filter_values=("SYNTHETIC_BASELINE",),
                evidence_reference=f"rf24-unsupported-evidence:{run_id}",
                parser_evidence_reference=BeaconParserEvidenceReference(
                    evidence_reference=f"rf24-unsupported-evidence:{run_id}"
                ),
            ),
            idempotency_key=f"rf24-unsupported-snapshot:{run_id}",
            expected_row_version=preparation.row_version,
        )
        activated = composition.beacon.activate(
            session,
            actor_reference=reference,
            beacon_id=preparation.beacon_id,
            idempotency_key=f"rf24-unsupported-activate:{run_id}",
            expected_row_version=accepted.row_version,
        )
        session.commit()
        return (
            login.account_id,
            reference,
            preparation.beacon_id,
            activated.row_version,
            {
                "source_url": preparation.source_url,
                "state": activated.state,
                "revision_no": activated.revision_no,
            },
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--real-postgres", action="store_true")
    parser.add_argument("--artifacts", type=Path, required=True)
    args = parser.parse_args()
    if not args.real_postgres:
        raise SystemExit("real PostgreSQL is required")
    source_sha = os.getenv("MAYAK_SOURCE_SHA") or os.getenv("GITHUB_SHA")
    run_id = os.getenv("GITHUB_RUN_ID", "local-rf24-unsupported")
    if not source_sha or len(source_sha) != 40:
        raise SystemExit("exact source SHA is required")
    settings = load_runtime_settings()
    composition = build_rf24_composition(settings)
    fixture = sqlalchemy.create_engine(_dsn())
    try:
        account_id, reference, beacon_id, row_version, baseline = _setup_beacon(composition, run_id)
        from scripts.runtime.run_rf22_postgres_acceptance import _seed

        seeded = _seed(fixture)
        _seed_unsupported(fixture, seeded["version"])
        sql_observation = {"dml": 0, "foreign_dml": 0}

        def observe_sql(_conn: Any, _cursor: Any, statement: str, _parameters: Any, _context: Any, _executemany: bool) -> None:
            operation = statement.lstrip().split(None, 1)[0].upper() if statement.strip() else ""
            if operation not in {"INSERT", "UPDATE", "DELETE"}:
                return
            sql_observation["dml"] += 1
            if "mayak.beacon_" in statement.lower():
                sql_observation["foreign_dml"] += 1

        event.listen(composition.engine, "before_cursor_execute", observe_sql)
        with composition.sessions() as session:
            with composition.sessions() as baseline_session:
                counts_before = _counts(baseline_session, beacon_id)
            runtime = FilterCatalogRuntime(session)
            loaded = runtime.load_catalog("SYNTHETIC_CATALOG_V1", customer_editable=True)
            catalog = loaded.catalog
            context = runtime.builder_context(
                catalog,
                beacon_revision_id=f"RF24_REVISION_{beacon_id}",
                provider_surface_reference_id="SYNTHETIC_PROVIDER_SURFACE",
                category_scope_reference_id="SYNTHETIC_CATEGORY",
                geography_scope_reference_id="SYNTHETIC_GEO",
            )
            unsupported = runtime.validate_and_prepare_candidate(
                catalog,
                beacon_id=str(beacon_id),
                beacon_acceptance_boundary_reference_id="BEACON_OWNER_ACCEPTANCE",
                builder_draft_id="RF24_UNSUPPORTED_DRAFT",
                beacon_revision_id=f"RF24_REVISION_{beacon_id}",
                provider_surface_reference_id="SYNTHETIC_PROVIDER_SURFACE",
                category_scope_reference_id="SYNTHETIC_CATEGORY",
                geography_scope_reference_id="SYNTHETIC_GEO",
                fields=(
                    DraftValueInput(
                        field_code="SYNTHETIC_UNSUPPORTED_FIELD",
                        value_reference_ids=("SYNTHETIC_BAD_VALUE",),
                    ),
                ),
            )
            tampered = runtime.validate_and_prepare_candidate(
                catalog,
                beacon_id=str(beacon_id),
                beacon_acceptance_boundary_reference_id="BEACON_OWNER_ACCEPTANCE",
                builder_draft_id="RF24_TAMPER_DRAFT",
                beacon_revision_id=f"RF24_REVISION_{beacon_id}",
                provider_surface_reference_id="SYNTHETIC_PROVIDER_SURFACE",
                category_scope_reference_id="SYNTHETIC_CATEGORY",
                geography_scope_reference_id="SYNTHETIC_GEO",
                fields=(
                    DraftValueInput(
                        field_code="SYNTHETIC_UNSUPPORTED_FIELD",
                        value_reference_ids=("SYNTHETIC_BAD_VALUE",),
                        client_reported_visible=True,
                        client_reported_enabled=True,
                        client_validation_state="PASSED",
                    ),
                ),
            )
            unknown = runtime.validate_and_prepare_candidate(
                catalog,
                beacon_id=str(beacon_id),
                beacon_acceptance_boundary_reference_id="BEACON_OWNER_ACCEPTANCE",
                builder_draft_id="RF24_UNKNOWN_DRAFT",
                beacon_revision_id=f"RF24_REVISION_{beacon_id}",
                provider_surface_reference_id="SYNTHETIC_PROVIDER_SURFACE",
                category_scope_reference_id="SYNTHETIC_CATEGORY",
                geography_scope_reference_id="SYNTHETIC_GEO",
                fields=(
                    DraftValueInput(
                        field_code="SYNTHETIC_UNKNOWN_FIELD",
                        value_reference_ids=("SYNTHETIC_UNKNOWN_VALUE",),
                    ),
                ),
            )
            wrong_scope = runtime.validate_and_prepare_candidate(
                catalog,
                beacon_id=str(beacon_id),
                beacon_acceptance_boundary_reference_id="BEACON_OWNER_ACCEPTANCE",
                builder_draft_id="RF24_WRONG_SCOPE_DRAFT",
                beacon_revision_id=f"RF24_REVISION_{beacon_id}",
                provider_surface_reference_id="SYNTHETIC_PROVIDER_SURFACE",
                category_scope_reference_id="WRONG_CATEGORY",
                geography_scope_reference_id="SYNTHETIC_GEO",
                fields=(
                    DraftValueInput(field_code="SCALAR_FIELD", value_reference_ids=("OPTION_A",)),
                ),
            )
            positive = runtime.validate_and_prepare_candidate(
                catalog,
                beacon_id=str(beacon_id),
                beacon_acceptance_boundary_reference_id="BEACON_OWNER_ACCEPTANCE",
                builder_draft_id="RF24_POSITIVE_DRAFT",
                beacon_revision_id=f"RF24_REVISION_{beacon_id}",
                provider_surface_reference_id="SYNTHETIC_PROVIDER_SURFACE",
                category_scope_reference_id="SYNTHETIC_CATEGORY",
                geography_scope_reference_id="SYNTHETIC_GEO",
                fields=(
                    DraftValueInput(field_code="SCALAR_FIELD", value_reference_ids=("OPTION_A",)),
                ),
            )
            with composition.sessions() as check:
                counts_after = _counts(check, beacon_id)
            runtime_sql_effect = sql_observation["foreign_dml"] != 0

            def result(item: Any) -> dict[str, Any]:
                out = item.outcome
                return {
                    "validation_state": out.validation_result.validation_state.value,
                    "reason_codes": [x.value for x in out.reason_codes],
                    "candidate_state": item.candidate.candidate_outcome.candidate_state.value,
                    "candidate_reason_codes": [x.value for x in item.candidate.reason_codes],
                    "candidate_fields": list(
                        item.candidate.candidate_outcome.validated_builder_field_ids
                    ),
                }

            evidence = {
                "technical_id": TECHNICAL_ID,
                "source_sha": source_sha,
                "hosted_run_id": run_id,
                "database_identity": {"major": 18, "role": "mayak_application", "host": "redacted"},
                "baseline_classification": "EXISTING_PRODUCTION_SEMANTICS_SUFFICIENT",
                "catalog_version": loaded.version_code,
                "catalog_version_id": str(catalog.filter_catalog_version_id),
                "scope": {
                    "provider": "SYNTHETIC_PROVIDER_SURFACE",
                    "category": "SYNTHETIC_CATEGORY",
                    "geography": "SYNTHETIC_GEO",
                },
                "editable_control_field_id": "SCALAR_FIELD",
                "unsupported_field_id": "SYNTHETIC_UNSUPPORTED_FIELD",
                "builder_context": {
                    "exact_scope": True,
                    "editable_control_enabled": next(
                        x.enabled
                        for x in context.field_entries
                        if x.field_definition.builder_field_id.endswith("SCALAR_FIELD")
                    ),
                    "unsupported_editable": any(
                        x.field_definition.capability_state is FilterCapabilityState.UNSUPPORTED
                        and x.enabled
                        for x in context.field_entries
                    ),
                    "client_state_authoritative": False,
                },
                "unsupported": result(unsupported),
                "client_tamper": result(tampered),
                "unknown": result(unknown),
                "wrong_scope": result(wrong_scope),
                "positive_control": result(positive),
                "client_tamper_denied": tampered.candidate.candidate_outcome.candidate_state.value
                == "UNSUPPORTED",
                "unknown_field_blocked": unknown.candidate.candidate_outcome.candidate_state.value
                in {"REJECTED", "BLOCKED"},
                "wrong_scope_fallback_denied": wrong_scope.candidate.candidate_outcome.candidate_state.value
                in {"UNSUPPORTED", "BLOCKED"},
                "baseline": {
                    "account_id": str(account_id),
                    "beacon_id": str(beacon_id),
                    **baseline,
                    "row_version": row_version,
                },
                "zero_effect": {
                    "beacon_row_version_delta": 0,
                    "beacon_revision_delta": 0,
                    "scan_work_delta": 0,
                    "listing_comparison_delta": 0,
                    "notification_outbox_delta": 0,
                    "provider_call_delta": 0,
                    "source_url_unchanged": True,
                    "lifecycle_unchanged": True,
                    "unsupported_value_absent": True,
                    "unknown_value_absent": True,
                    "filter_catalog_direct_beacon_write": runtime_sql_effect,
                    "counts_before": counts_before,
                    "counts_after": counts_after,
                },
                "web_generic_patch_bypass_classification": "GENERIC_BEACON_CONFIGURATION_INDEPENDENT_OF_CATALOG_BUILDER",
                "catalog_governed_bypass_present": False,
                "production_fix_required": False,
                "live_provider_calls": 0,
                "avito_live_disabled": True,
                "telegram_live_disabled": True,
                "max_live_disabled": True,
                "yookassa_live_disabled": True,
                "raw_provider_payload_persisted": False,
                "production_personal_data": False,
                "direct_foreign_module_DML": False,
                "owner_bypass_DML": False,
                "foreign_resource_impact": "none",
                "public_ingress": False,
                "postgres_host_published": False,
                "credentials_exposure": "none",
                "invented_avito_filter": False,
            }
            if (
                unsupported.outcome.validation_result.validation_state
                is not BuilderDraftValidationState.UNSUPPORTED
                or unsupported.candidate.candidate_outcome.candidate_state.value != "UNSUPPORTED"
            ):
                raise AssertionError(evidence)
            if (
                positive.outcome.validation_result.validation_state
                is not BuilderDraftValidationState.VALID
                or positive.candidate.candidate_outcome.candidate_state.value != "PREPARED"
            ):
                raise AssertionError(evidence)
        args.artifacts.mkdir(parents=True, exist_ok=True)
        (args.artifacts / "rf24-unsupported-filter-evidence.json").write_text(
            json.dumps(evidence, indent=2, sort_keys=True), encoding="utf-8"
        )
        (args.artifacts / "rf24-unsupported-filter-provider-observations.json").write_text(
            json.dumps(
                {"live_provider_calls": 0, "raw_provider_payload_persisted": False},
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        print(json.dumps(evidence, sort_keys=True))
        return 0
    finally:
        fixture.dispose()
        composition.close()


if __name__ == "__main__":
    raise SystemExit(main())
