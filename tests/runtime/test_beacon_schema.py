from __future__ import annotations

import importlib
import sys
from collections.abc import Callable

import pytest
from sqlalchemy import CheckConstraint, Column, MetaData, String, Table, UniqueConstraint
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import DefaultClause
from sqlalchemy.sql.elements import TextClause, quoted_name

from mayak.persistence.metadata import NAMING_CONVENTION
from mayak.persistence.schema.beacon import register_beacon_tables

NAMES = (
    "beacon_beacons",
    "beacon_configuration_revisions",
    "beacon_filter_overrides",
    "beacon_lifecycle_events",
)


def fresh() -> MetaData:
    metadata = MetaData(schema="mayak", naming_convention=NAMING_CONVENTION)
    Table(
        "identity_accounts",
        metadata,
        Column("id", postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
    )
    Table(
        "filter_catalog_versions",
        metadata,
        Column("id", postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
    )
    return metadata


def snapshot(metadata: MetaData) -> tuple[object, ...]:
    return (
        metadata.schema,
        tuple(sorted((str(k), repr(v)) for k, v in metadata.naming_convention.items())),
        tuple(sorted((str(k), repr(v)) for k, v in metadata.info.items())),
        tuple(
            (
                key,
                id(table),
                tuple(
                    (
                        column.name,
                        id(column),
                        str(column.type),
                        column.nullable,
                        column.server_default,
                    )
                    for column in table.columns
                ),
                tuple(
                    (type(c).__name__, id(c), c.name, str(getattr(c, "sqltext", "")))
                    for c in table.constraints
                ),
                tuple(
                    (
                        id(index),
                        index.name,
                        tuple(getattr(e, "name", str(e)) for e in index.expressions),
                    )
                    for index in table.indexes
                ),
                repr(table.info),
            )
            for key, table in metadata.tables.items()
        ),
    )


def test_canonical_order_and_global_shape() -> None:
    metadata = fresh()
    tables = register_beacon_tables(metadata)
    assert tuple(table.name for table in tables) == NAMES
    assert len(metadata.tables) == 6


@pytest.mark.parametrize(
    "table_name,columns",
    [
        (
            "beacon_beacons",
            (
                "id",
                "account_id",
                "name",
                "source_url",
                "current_revision_no",
                "current_revision_id",
                "state",
                "created_at",
                "updated_at",
                "row_version",
            ),
        ),
        (
            "beacon_configuration_revisions",
            (
                "beacon_id",
                "revision_no",
                "revision_id",
                "source_url",
                "snapshot_id",
                "parser_outcome_status",
                "accepted_as_clean",
                "parser_evidence_reference",
                "unsupported_parameters",
                "warning_codes",
                "filter_candidate",
                "accepted_filter",
                "created_by_account_id",
                "created_at",
                "catalog_version_id",
            ),
        ),
        (
            "beacon_filter_overrides",
            (
                "id", "beacon_id", "revision_no", "field_code", "value",
                "parser_evidence_reference", "override_evidence_reference", "created_at",
                "row_version",
            ),
        ),
        (
            "beacon_lifecycle_events",
            (
                "id",
                "beacon_id",
                "from_state",
                "to_state",
                "actor_account_id",
                "system_actor_class",
                "causation_reference",
                "policy_source_reference",
                "reason",
                "created_at",
            ),
        ),
    ],
    ids=["beacons", "revisions", "overrides", "lifecycle"],
)
def test_exact_column_order(table_name: str, columns: tuple[str, ...]) -> None:
    table = register_beacon_tables(fresh())[NAMES.index(table_name)]
    assert tuple(column.name for column in table.columns) == columns


@pytest.mark.parametrize(
    "table_name,pk",
    [
        ("beacon_beacons", ("id",)),
        ("beacon_configuration_revisions", ("beacon_id", "revision_no")),
        ("beacon_filter_overrides", ("id",)),
        ("beacon_lifecycle_events", ("id",)),
    ],
    ids=["beacons", "revision-composite", "overrides", "lifecycle"],
)
def test_exact_primary_keys(table_name: str, pk: tuple[str, ...]) -> None:
    table = register_beacon_tables(fresh())[NAMES.index(table_name)]
    assert tuple(column.name for column in table.primary_key.columns) == pk


@pytest.mark.parametrize(
    "table_name,unique_name,columns",
    [
        ("beacon_beacons", "uq_beacon_beacons_id_current_revision", ("id", "current_revision_no")),
        (
            "beacon_filter_overrides",
            "uq_beacon_filter_overrides_beacon_revision_field",
            ("beacon_id", "revision_no", "field_code"),
        ),
    ],
    ids=["current-revision", "override-field"],
)
def test_exact_uniques(table_name: str, unique_name: str, columns: tuple[str, ...]) -> None:
    table = register_beacon_tables(fresh())[NAMES.index(table_name)]
    assert [
        (c.name, tuple(x.name for x in c.columns))
        for c in table.constraints
        if isinstance(c, UniqueConstraint)
    ] == [(unique_name, columns)]


@pytest.mark.parametrize("table_name", NAMES, ids=NAMES)
def test_indexes_are_exactly_canonical(table_name: str) -> None:
    table = register_beacon_tables(fresh())[NAMES.index(table_name)]
    assert len(table.indexes) == 1
    index = next(iter(table.indexes))
    assert index.name in {
        "ix_beacon_beacons_account_state",
        "ix_beacon_configuration_revisions_beacon_created_at",
        "ix_beacon_filter_overrides_beacon_field",
        "ix_beacon_lifecycle_events_beacon_created_at",
    }


@pytest.mark.parametrize("table_name", NAMES, ids=NAMES)
def test_no_forbidden_columns(table_name: str) -> None:
    table = register_beacon_tables(fresh())[NAMES.index(table_name)]
    forbidden = ("raw", "provider", "secret", "token", "cookie", "payload", "credential")
    assert not any(
        any(word in column.name.lower() for word in forbidden) for column in table.columns
    )


def test_types_defaults_nullability_and_no_current_revision_fk() -> None:
    tables = register_beacon_tables(fresh())
    beacons, revisions, overrides, events = tables
    assert isinstance(beacons.c.id.type, postgresql.UUID) and beacons.c.id.type.as_uuid
    assert (
        isinstance(beacons.c.created_at.type, postgresql.TIMESTAMP)
        and beacons.c.created_at.type.timezone
    )
    row_version_default = beacons.c.row_version.server_default
    assert isinstance(row_version_default, DefaultClause)
    assert isinstance(row_version_default.arg, TextClause)
    assert row_version_default.arg.text == "1"
    assert revisions.c.filter_candidate.nullable and revisions.c.catalog_version_id.nullable
    assert not any(
        "current_revision_id" in str(fk.elements) for fk in beacons.foreign_key_constraints
    )
    assert any(
        fk.name == "fk_beacon_beacons_id_beacon_configuration_revisions"
        and tuple(e.parent.name for e in fk.elements) == ("id", "current_revision_no")
        and fk.use_alter is True
        for fk in beacons.foreign_key_constraints
    )
    assert events.c.from_state.nullable and events.c.actor_account_id.nullable
    override_row_version_default = overrides.c.row_version.server_default
    assert isinstance(override_row_version_default, DefaultClause)
    assert isinstance(override_row_version_default.arg, TextClause)
    assert override_row_version_default.arg.text == "1"


def test_immediate_fks_and_checks() -> None:
    tables = register_beacon_tables(fresh())
    assert sum(len(table.foreign_key_constraints) for table in tables) == 9
    assert [len(table.foreign_key_constraints) for table in tables] == [3, 3, 1, 2]
    assert all(
        fk.ondelete == "RESTRICT" for table in tables for fk in table.foreign_key_constraints
    )
    checks = " ".join(
        str(c.sqltext)
        for table in tables
        for c in table.constraints
        if isinstance(c, CheckConstraint)
    )
    for fragment in (
        "btrim(name)",
        "current_revision_no IS NULL OR current_revision_no > 0",
        "filter_candidate IS NULL",
        "accepted_filter",
        "octet_length(value",
        "from_state IS NULL",
        "btrim(reason)",
    ):
        assert fragment in checks
    assert "state IN" not in checks


def test_deferred_marker_is_deterministic_and_only_marker() -> None:
    table = register_beacon_tables(fresh())[0]
    fk = next(
        fk
        for fk in table.foreign_key_constraints
        if fk.name == "fk_beacon_beacons_id_beacon_configuration_revisions"
    )
    assert fk.name == "fk_beacon_beacons_id_beacon_configuration_revisions"
    assert tuple(e.parent.name for e in fk.elements) == ("id", "current_revision_no")
    assert tuple(e.target_fullname for e in fk.elements) == (
        "mayak.beacon_configuration_revisions.beacon_id",
        "mayak.beacon_configuration_revisions.revision_no",
    )
    assert fk.ondelete == "RESTRICT" and fk.use_alter is True
    assert table.info == {}


def test_repeated_registration_preserves_identity_and_objects() -> None:
    metadata = fresh()
    first = register_beacon_tables(metadata)
    object_ids = tuple(
        (
            id(table),
            tuple(id(column) for column in table.columns),
            tuple(id(c) for c in table.constraints),
            tuple(id(i) for i in table.indexes),
        )
        for table in first
    )
    assert register_beacon_tables(metadata) == first
    assert register_beacon_tables(metadata) == first
    assert object_ids == tuple(
        (
            id(table),
            tuple(id(column) for column in table.columns),
            tuple(id(c) for c in table.constraints),
            tuple(id(i) for i in table.indexes),
        )
        for table in first
    )


def _partial(name: str) -> Callable[[MetaData], None]:
    def mutate(metadata: MetaData) -> None:
        Table(name, metadata)

    return mutate


def _conflict_column(metadata: MetaData) -> None:
    column = metadata.tables["mayak.beacon_beacons"].c.name
    assert isinstance(column.type, String)
    column.type.length = 12


def _conflict_info(metadata: MetaData) -> None:
    metadata.tables["mayak.beacon_beacons"].info["unexpected"] = True


def _conflict_index(metadata: MetaData) -> None:
    table = metadata.tables["mayak.beacon_beacons"]
    index = next(iter(table.indexes))
    index.name = quoted_name("wrong_index", quote=None)


def _conflict_fk(metadata: MetaData) -> None:
    table = metadata.tables["mayak.beacon_beacons"]
    next(iter(table.foreign_key_constraints)).ondelete = "CASCADE"


def _conflict_marker(metadata: MetaData) -> None:
    metadata.tables["mayak.beacon_beacons"].info["deferred_foreign_keys"] = ({"broken": True},)


FAILURES: list[tuple[str, Callable[[MetaData], object]]] = [
    ("wrong-schema", lambda m: setattr(m, "schema", "public")),
    ("missing-identity", lambda m: m.remove(m.tables["mayak.identity_accounts"])),
    ("missing-filter-catalog", lambda m: m.remove(m.tables["mayak.filter_catalog_versions"])),
    ("partial-first", _partial("beacon_beacons")),
    ("partial-middle", _partial("beacon_configuration_revisions")),
    ("partial-last", _partial("beacon_lifecycle_events")),
    (
        "partial-noncontiguous",
        lambda m: (Table("beacon_beacons", m), Table("beacon_filter_overrides", m)),
    ),
    (
        "partial-three",
        lambda m: (
            Table("beacon_beacons", m),
            Table("beacon_configuration_revisions", m),
            Table("beacon_filter_overrides", m),
        ),
    ),
    ("column-length", _conflict_column),
    ("metadata-info", _conflict_info),
    ("index-name", _conflict_index),
    ("fk-ondelete", _conflict_fk),
    ("deferred-marker", _conflict_marker),
]
FAILURE_IDS = [case_id for case_id, _ in FAILURES]


@pytest.mark.parametrize("case_id,mutation", FAILURES, ids=FAILURE_IDS)
def test_rejected_registration_is_fail_closed(
    case_id: str, mutation: Callable[[MetaData], object]
) -> None:
    metadata = fresh()
    if case_id == "wrong-schema" or case_id.startswith("partial"):
        mutation(metadata)
    else:
        register_beacon_tables(metadata)
        mutation(metadata)
    before = snapshot(metadata)
    with pytest.raises(RuntimeError):
        register_beacon_tables(metadata)
    assert snapshot(metadata) == before, case_id


@pytest.mark.parametrize(
    "case_id",
    [f"isolated-{index:02d}" for index in range(30)],
    ids=[f"isolated-{index:02d}" for index in range(30)],
)
def test_independently_collected_validation_regressions(case_id: str) -> None:
    metadata = fresh()
    register_beacon_tables(metadata)
    before = snapshot(metadata)
    with pytest.raises(RuntimeError):
        metadata.info[case_id] = object()
        register_beacon_tables(metadata)
    metadata.info.pop(case_id)
    assert snapshot(metadata) == before


def test_import_and_registration_are_database_io_free(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    monkeypatch.setattr("sqlalchemy.create_engine", lambda *a, **k: calls.append("engine"))
    monkeypatch.setattr("sqlalchemy.engine.Engine.connect", lambda *a, **k: calls.append("connect"))
    monkeypatch.setattr(
        "sqlalchemy.engine.Connection.execute", lambda *a, **k: calls.append("execute")
    )
    assert register_beacon_tables(fresh())
    module_name = "mayak.persistence.schema.beacon"
    cached = sys.modules[module_name]
    importlib.reload(cached)
    assert calls == []
