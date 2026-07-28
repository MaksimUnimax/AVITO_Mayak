from __future__ import annotations

import importlib
from typing import Any, cast

import pytest
from sqlalchemy import CheckConstraint, Column, MetaData, Table, text
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import ForeignKeyConstraint, UniqueConstraint

from mayak.persistence.metadata import NAMING_CONVENTION, metadata
from mayak.persistence.schema.parser import register_parser_tables

NAMES = ("parser_outcomes",)
COLUMNS = (
    "id",
    "beacon_id",
    "run_id",
    "route_id",
    "outcome_code",
    "listing_snapshot",
    "observed_at",
    "fingerprint",
    "created_at",
)


def isolated() -> MetaData:
    target = MetaData(schema="mayak", naming_convention=dict(NAMING_CONVENTION))
    for name in ("beacon_beacons", "scan_runs", "egress_routes"):
        Table(name, target, Column("id", postgresql.UUID(as_uuid=True), primary_key=True))
    return target


def table() -> Table:
    return register_parser_tables(isolated())[0]


def checks(value: Table) -> set[str]:
    return {
        " ".join(str(c.sqltext).split())
        for c in value.constraints
        if isinstance(c, CheckConstraint)
    }


def fks(value: Table) -> list[ForeignKeyConstraint]:
    return [c for c in value.constraints if isinstance(c, ForeignKeyConstraint)]


def test_one_table_tuple_return() -> None:
    result = register_parser_tables(isolated())
    assert isinstance(result, tuple) and len(result) == 1


def test_exact_table_name_and_order() -> None:
    result = register_parser_tables(isolated())
    assert tuple(item.name for item in result) == NAMES
    assert list(result[0].metadata.tables)[:4] == [
        "mayak.beacon_beacons",
        "mayak.scan_runs",
        "mayak.egress_routes",
        "mayak.parser_outcomes",
    ]


def test_exact_column_order() -> None:
    assert tuple(column.name for column in table().columns) == COLUMNS


def test_postgresql_type_families() -> None:
    value = table()
    assert isinstance(value.c.id.type, postgresql.UUID) and value.c.id.type.as_uuid is True
    assert isinstance(value.c.beacon_id.type, postgresql.UUID)
    assert isinstance(value.c.run_id.type, postgresql.UUID)
    assert isinstance(value.c.route_id.type, postgresql.UUID)
    assert isinstance(value.c.listing_snapshot.type, postgresql.JSONB)
    assert (
        isinstance(value.c.fingerprint.type, postgresql.CHAR)
        and value.c.fingerprint.type.length == 64
    )
    assert (
        isinstance(value.c.observed_at.type, postgresql.TIMESTAMP)
        and value.c.observed_at.type.timezone is True
    )
    assert (
        isinstance(value.c.created_at.type, postgresql.TIMESTAMP)
        and value.c.created_at.type.timezone is True
    )


def test_string_and_json_options() -> None:
    value = table()
    assert value.c.outcome_code.type.length == 64  # type: ignore[attr-defined]
    assert isinstance(value.c.listing_snapshot.type, postgresql.JSONB)
    assert all(column.server_default is None for column in value.columns)


def test_nullability_is_exact() -> None:
    value = table()
    assert [column.nullable for column in value.columns] == [
        False,
        False,
        True,
        True,
        False,
        True,
        False,
        False,
        False,
    ]


def test_primary_key_is_application_generated() -> None:
    value = table()
    assert [column.name for column in value.primary_key.columns] == ["id"]
    assert value.c.id.server_default is None and value.c.id.default is None


def test_no_mutable_or_scan_state_columns() -> None:
    value = table()
    assert "updated_at" not in value.c and "row_version" not in value.c
    assert not any(name in str(value.info).lower() for name in ("scan", "notification", "state"))


def test_exact_foreign_keys() -> None:
    expected = {
        ("beacon_id", "mayak.beacon_beacons.id"),
        ("run_id", "mayak.scan_runs.id"),
        ("route_id", "mayak.egress_routes.id"),
    }
    assert len(fks(table())) == 3
    assert {
        (e.parent.name, e.target_fullname) for fk in fks(table()) for e in fk.elements
    } == expected


def test_foreign_keys_restrict_and_nullable() -> None:
    value = table()
    assert all(fk.ondelete == "RESTRICT" and fk.onupdate is None for fk in fks(value))
    assert value.c.run_id.nullable and value.c.route_id.nullable


def test_no_cascade_or_deferred_parser_marker() -> None:
    value = table()
    assert all(fk.ondelete != "CASCADE" for fk in fks(value))
    assert value.info == {}


def test_exact_unique_constraint() -> None:
    uniques = [c for c in table().constraints if isinstance(c, UniqueConstraint)]
    assert len(uniques) == 1 and uniques[0].name == "uq_parser_outcomes_run_fingerprint"
    assert [column.name for column in uniques[0].columns] == ["run_id", "fingerprint"]


def test_unique_is_null_safe() -> None:
    unique = next(c for c in table().constraints if isinstance(c, UniqueConstraint))
    assert unique.dialect_options["postgresql"]["nulls_not_distinct"] is True


def test_exact_checks() -> None:
    assert checks(table()) == {
        "btrim(outcome_code) <> ''",
        "listing_snapshot IS NULL OR octet_length(listing_snapshot::text) <= 32768",
        "fingerprint ~ '^[0-9a-f]{64}$'",
    }


def test_check_names() -> None:
    assert {c.name for c in table().constraints if isinstance(c, CheckConstraint)} == {
        "outcome_code_nonempty",
        "listing_snapshot_size",
        "fingerprint_sha256",
    }


def test_no_enum_or_literal_outcome_policy() -> None:
    value = table()
    assert not isinstance(value.c.outcome_code.type, postgresql.ENUM)
    assert not any(" IN (" in str(c) for c in value.constraints)


def test_exact_indexes() -> None:
    value = table()
    assert {index.name for index in value.indexes} == {
        "ix_parser_outcomes_beacon_observed_at",
        "ix_parser_outcomes_outcome_code_observed_at",
    }
    assert sum(len(index.expressions) for index in value.indexes) == 4


def test_index_order_and_options() -> None:
    indexes: dict[str, Any] = {str(index.name): index for index in table().indexes}
    assert tuple(c.name for c in indexes["ix_parser_outcomes_beacon_observed_at"].expressions) == (
        "beacon_id",
        "observed_at",
    )
    assert tuple(
        c.name for c in indexes["ix_parser_outcomes_outcome_code_observed_at"].expressions
    ) == ("outcome_code", "observed_at")
    assert all(
        index.unique is False and not index.dialect_options["postgresql"].get("where")
        for index in indexes.values()
    )


def test_global_metadata_totals_and_parser_counts() -> None:
    parser = metadata.tables["mayak.parser_outcomes"]
    assert (
        len(metadata.tables) == 48
        and sum(len(item.indexes) for item in metadata.tables.values()) == 67
    )
    assert len(parser.indexes) == 2 and len(fks(parser)) == 3


def test_global_registration_order() -> None:
    names = [key.rsplit(".", 1)[1] for key in metadata.tables]
    assert (
        names.index("beacon_beacons")
        < names.index("egress_routes")
        < names.index("scan_runs")
        < names.index("parser_outcomes")
        < names.index("notification_endpoints")
    )
    assert names.index("notification_endpoints") < names.index("telegram_inbound_updates")
    assert names.index("telegram_delivery_mappings") < names.index("max_inbound_events")


def test_scan_reverse_fk_is_absent() -> None:
    run = metadata.tables["mayak.scan_runs"]
    assert not any(
        e.target_fullname == "mayak.parser_outcomes.id"
        for fk in run.foreign_key_constraints
        for e in fk.elements
    )


def test_scan_deferred_marker_is_exact() -> None:
    assert metadata.tables["mayak.scan_runs"].info == {
        "deferred_foreign_keys": (
            {
                "local_columns": ("parser_outcome_id",),
                "target_columns": ("mayak.parser_outcomes.id",),
                "on_delete": "RESTRICT",
                "planned_revision": "RF09_FINALIZE",
            },
        )
    }


def test_egress_deferred_marker_is_present_and_parser_has_none() -> None:
    assert metadata.tables["mayak.egress_route_leases"].info["deferred_foreign_keys"]
    assert table().info == {}


def test_prerequisite_failures() -> None:
    for name in ("beacon_beacons", "scan_runs", "egress_routes"):
        target = isolated()
        target.remove(target.tables[f"mayak.{name}"])
        with pytest.raises(RuntimeError, match="missing parser prerequisites"):
            register_parser_tables(target)


def test_wrong_schema_fails_before_mutation() -> None:
    target = MetaData(schema="other", naming_convention=NAMING_CONVENTION)
    before = tuple(target.tables)
    with pytest.raises(RuntimeError):
        register_parser_tables(target)
    assert tuple(target.tables) == before


def test_wrong_naming_fails_before_mutation() -> None:
    target = isolated()
    target.naming_convention = {"pk": "wrong"}
    before = tuple(target.tables)
    with pytest.raises(RuntimeError):
        register_parser_tables(target)
    assert tuple(target.tables) == before


def test_nonempty_info_fails_before_mutation() -> None:
    target = isolated()
    target.info["unexpected"] = True
    before = tuple(target.tables)
    with pytest.raises(RuntimeError):
        register_parser_tables(target)
    assert tuple(target.tables) == before


def test_valid_registration_and_replay_identity() -> None:
    target = isolated()
    first = register_parser_tables(target)
    second = register_parser_tables(target)
    assert first[0] is second[0]


def test_independent_convention_copy_and_reordering() -> None:
    target = isolated()
    target.naming_convention = dict(NAMING_CONVENTION)
    assert register_parser_tables(target)[0].name == "parser_outcomes"
    target = isolated()
    target.naming_convention = {
        key: NAMING_CONVENTION[key] for key in reversed(tuple(NAMING_CONVENTION))
    }
    assert register_parser_tables(target)[0].name == "parser_outcomes"


def test_conflicting_schema_is_rejected() -> None:
    target = isolated()
    register_parser_tables(target)
    target.tables["mayak.parser_outcomes"].schema = "other"
    with pytest.raises(RuntimeError, match="conflicting existing parser"):
        register_parser_tables(target)


def test_conflicting_column_order_is_rejected() -> None:
    target = isolated()
    value = register_parser_tables(target)[0]
    value.append_column(Column("wrong", postgresql.UUID(as_uuid=True)))
    with pytest.raises(RuntimeError):
        register_parser_tables(target)


def test_conflicting_type_nullability_and_default_are_rejected() -> None:
    for change in ("type", "nullable", "default"):
        target = isolated()
        value = register_parser_tables(target)[0]
        if change == "type":
            value.c.fingerprint.type = postgresql.CHAR(32)
        elif change == "nullable":
            value.c.fingerprint.nullable = True
        else:
            cast(Any, value.c.created_at).server_default = text("now()")
        with pytest.raises(RuntimeError):
            register_parser_tables(target)


def test_conflicting_pk_fk_unique_check_and_index_are_rejected() -> None:
    target = isolated()
    value = register_parser_tables(target)[0]
    value.primary_key.name = "wrong_pk"
    with pytest.raises(RuntimeError):
        register_parser_tables(target)
    target = isolated()
    value = register_parser_tables(target)[0]
    unique = next(c for c in value.constraints if isinstance(c, UniqueConstraint))
    unique.dialect_options["postgresql"]["nulls_not_distinct"] = False
    with pytest.raises(RuntimeError):
        register_parser_tables(target)
    target = isolated()
    value = register_parser_tables(target)[0]
    index = next(iter(value.indexes))
    index.unique = True
    with pytest.raises(RuntimeError):
        register_parser_tables(target)


def test_missing_fk_and_conflicting_check_are_rejected() -> None:
    target = isolated()
    value = register_parser_tables(target)
    value[0].constraints.pop()
    with pytest.raises(RuntimeError):
        register_parser_tables(target)


def test_unrelated_identity_and_rejection_snapshot_are_preserved() -> None:
    target = isolated()
    unrelated = Table("unrelated", target, Column("id", postgresql.UUID(as_uuid=True)))
    before = tuple(target.tables.items())
    target.naming_convention = {"bad": "value"}
    with pytest.raises(RuntimeError):
        register_parser_tables(target)
    assert tuple(target.tables.items()) == before and target.tables["mayak.unrelated"] is unrelated


def test_repeated_malformed_registration_is_deterministic() -> None:
    target = isolated()
    target.info["bad"] = True
    messages = []
    for _ in range(2):
        with pytest.raises(RuntimeError) as error:
            register_parser_tables(target)
        messages.append(str(error.value))
    assert messages[0] == messages[1]


def test_forbidden_privacy_and_nonownership_terms_are_absent() -> None:
    forbidden = (
        "raw",
        "payload",
        "body",
        "html",
        "header",
        "cookie",
        "session",
        "token",
        "credential",
        "secret",
        "password",
        "proxy",
        "retry",
        "backoff",
        "notification",
        "baseline",
        "newness",
    )
    value = table()
    names = [column.name.lower() for column in value.columns]
    assert not any(any(word in name for word in forbidden) for name in names)
    assert not any(
        any(word in str(item).lower() for word in forbidden) for item in value.constraints
    )


def test_import_is_inert(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    monkeypatch.setattr("sqlalchemy.create_engine", lambda *args, **kwargs: calls.append("engine"))
    monkeypatch.setattr(
        "sqlalchemy.engine.Engine.connect", lambda *args, **kwargs: calls.append("connect")
    )
    assert importlib.import_module("mayak.persistence.schema.parser")
    register_parser_tables(isolated())
    assert calls == []


def test_no_database_or_provider_surface() -> None:
    source = importlib.import_module("mayak.persistence.schema.parser").__file__
    assert source is not None
    text_value = open(source, encoding="utf-8").read()
    assert all(
        term not in text_value
        for term in ("create_engine", "connect(", "requests", "httpx", "urllib", "os.environ")
    )
