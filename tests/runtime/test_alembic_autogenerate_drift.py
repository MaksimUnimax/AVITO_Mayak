from __future__ import annotations

import ast
from pathlib import Path

from sqlalchemy import MetaData

from mayak.persistence.config import (
    ApplicationDatabaseSettings,
    DatabaseEndpoint,
    MigrationDatabaseSettings,
    build_application_url,
    build_migration_url,
)
from mayak.persistence.metadata import NAMING_CONVENTION, metadata
from mayak.persistence.schema.identity import register_identity_tables
from mayak.persistence.schema.platform import register_platform_tables

ROOT = Path(__file__).parents[2]
M02_FK = "fk_identity_role_assignments_assigned_by_account_id_ide_a4f6"
FINALIZER_FKS = {
    "fk_beacon_beacons_id_beacon_configuration_revisions": (
        "mayak.beacon_beacons",
        "mayak.beacon_configuration_revisions.beacon_id",
    ),
    "fk_scan_runs_parser_outcome_id_parser_outcomes": (
        "mayak.scan_runs",
        "mayak.parser_outcomes.id",
    ),
    "fk_egress_route_leases_work_item_id_scan_work_items": (
        "mayak.egress_route_leases",
        "mayak.scan_work_items.id",
    ),
}


def _secret_path(tmp_path: Path, name: str = "synthetic") -> Path:
    path = tmp_path / name
    path.write_text("local-test-secret", encoding="utf-8")
    return path


def test_application_url_keeps_domain_search_path(tmp_path: Path) -> None:
    url = build_application_url(
        ApplicationDatabaseSettings(secret_path=_secret_path(tmp_path))
    )
    assert url.query["options"] == "-csearch_path=mayak"


def test_migration_url_uses_public_then_domain_search_path(tmp_path: Path) -> None:
    url = build_migration_url(
        MigrationDatabaseSettings(secret_path=_secret_path(tmp_path)), require_secret=False
    )
    assert url.query["options"] == "-csearch_path=public"


def test_custom_migration_schema_and_public_are_not_duplicated(tmp_path: Path) -> None:
    custom = build_migration_url(
        MigrationDatabaseSettings(
            endpoint=DatabaseEndpoint(schema="tenant"), secret_path=_secret_path(tmp_path)
        ),
        require_secret=False,
    )
    public = build_migration_url(
        MigrationDatabaseSettings(
            endpoint=DatabaseEndpoint(schema="public"), secret_path=_secret_path(tmp_path)
        ),
        require_secret=False,
    )
    assert custom.query["options"] == "-csearch_path=public"
    assert public.query["options"] == "-csearch_path=public"


def test_corrective_09_migration_search_path_is_exactly_public(tmp_path: Path) -> None:
    for schema in ("mayak", "tenant"):
        url = build_migration_url(
            MigrationDatabaseSettings(
                endpoint=DatabaseEndpoint(schema=schema), secret_path=_secret_path(tmp_path)
            ),
            require_secret=False,
        )
        assert url.query == {"options": "-csearch_path=public"}
        assert schema not in url.query["options"]


def test_corrective_09_application_and_migration_search_paths_are_separate(
    tmp_path: Path,
) -> None:
    application = build_application_url(
        ApplicationDatabaseSettings(
            endpoint=DatabaseEndpoint(schema="tenant"), secret_path=_secret_path(tmp_path)
        )
    )
    migration = build_migration_url(
        MigrationDatabaseSettings(
            endpoint=DatabaseEndpoint(schema="tenant"), secret_path=_secret_path(tmp_path)
        ),
        require_secret=False,
    )
    assert application.query["options"] == "-csearch_path=tenant"
    assert migration.query["options"] == "-csearch_path=public"
    assert "public,tenant" not in migration.query["options"]


def test_corrective_09_schema_qualified_alembic_contract_remains_explicit() -> None:
    text = (ROOT / "alembic/env.py").read_text(encoding="utf-8")
    assert '"include_schemas": True' in text
    assert '"version_table_schema": "mayak"' in text
    assert "include_object" not in text
    assert "include_name" not in text
    assert 'search_path="public"' in (
        (ROOT / "src/mayak/persistence/config.py").read_text(encoding="utf-8")
    )


def test_application_and_migration_urls_differ_only_by_search_path_policy(
    tmp_path: Path,
) -> None:
    app = build_application_url(
        ApplicationDatabaseSettings(secret_path=_secret_path(tmp_path, "application"))
    ).set(password=None)
    migration = build_migration_url(
        MigrationDatabaseSettings(
            secret_path=_secret_path(tmp_path, "migration")
        ),
        require_secret=False,
    )
    assert app.host == migration.host
    assert app.port == migration.port
    assert app.database == migration.database
    assert app.query["options"] != migration.query["options"]


def test_m02_metadata_fk_is_explicit_and_untruncated() -> None:
    fk = next(
        fk
        for fk in metadata.tables["mayak.identity_role_assignments"].foreign_key_constraints
        if fk.columns.keys() == ["assigned_by_account_id"]
    )
    assert fk.name == M02_FK
    assert len(M02_FK) <= 63
    assert not fk.use_alter and not fk.deferrable


def test_metadata_inventory_is_accepted() -> None:
    assert len(metadata.tables) == 51
    assert sum(len(table.indexes) for table in metadata.tables.values()) == 72
    assert sum(len(table.foreign_key_constraints) for table in metadata.tables.values()) == 72


def test_finalizer_foreign_keys_are_registered_exactly() -> None:
    found = {
        fk.name: (fk.parent.fullname, fk.elements[0].target_fullname)
        for table in metadata.tables.values()
        for fk in table.foreign_key_constraints
        if fk.name in FINALIZER_FKS
    }
    assert found == FINALIZER_FKS


def test_alembic_schema_contract_has_no_broad_filters() -> None:
    text = (ROOT / "alembic/env.py").read_text(encoding="utf-8")
    tree = ast.parse(text)
    assert '"include_schemas": True' in text
    assert '"version_table_schema": "mayak"' in text
    assert "include_object" not in text
    assert "include_name" not in text
    assert tree.body


def test_metadata_registration_is_duplicate_free_and_deterministic() -> None:
    isolated = MetaData(schema="mayak", naming_convention=NAMING_CONVENTION)
    register_platform_tables(isolated)
    register_identity_tables(isolated)
    first = tuple(isolated.tables)
    register_identity_tables(isolated)
    assert tuple(isolated.tables) == first
    assert len(isolated.tables) == 8


def test_secret_values_do_not_appear_in_url_diagnostics(tmp_path: Path) -> None:
    secret = tmp_path / "secret"
    value = "task-owned-synthetic-secret"
    secret.write_text(value, encoding="utf-8")
    url = build_application_url(ApplicationDatabaseSettings(secret_path=secret))
    assert value not in repr(url)
    assert value not in str(url)
