from __future__ import annotations

import importlib
from typing import Any

import pytest
from sqlalchemy import CheckConstraint, MetaData, Table
from sqlalchemy.dialects import postgresql

from mayak.persistence.metadata import NAMING_CONVENTION, metadata
from mayak.persistence.schema.scan import register_scan_tables

NAMES = (
    "scan_schedules",
    "scan_work_items",
    "scan_runs",
    "scan_listing_observations",
    "scan_beacon_listing_state",
    "scan_anchors",
)
MARKER = {
    "local_columns": ("parser_outcome_id",),
    "target_columns": ("mayak.parser_outcomes.id",),
    "on_delete": "RESTRICT",
    "planned_revision": "RF09_FINALIZE",
}


def isolated() -> MetaData:
    return MetaData(schema="mayak", naming_convention=NAMING_CONVENTION)


def tables() -> tuple[Table, ...]:
    return register_scan_tables(isolated())


def checks(t: Table) -> set[str]:
    return {
        " ".join(str(c.sqltext).split()) for c in t.constraints if isinstance(c, CheckConstraint)
    }


def pred(i: Any) -> str:
    return " ".join(
        str(
            i.dialect_options["postgresql"]["where"].compile(
                dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
            )
        ).split()
    )


def test_exact_six_table_return_order() -> None:
    assert tuple(t.name for t in tables()) == NAMES


def test_global_counts() -> None:
    assert (
        len(metadata.tables) == 51 and sum(len(t.indexes) for t in metadata.tables.values()) == 73
    )


def test_scan_index_count() -> None:
    assert sum(len(t.indexes) for t in tables()) == 8


def test_rf14_parser_index_is_not_a_scan_index() -> None:
    assert sum(len(t.indexes) for t in tables()) == 8
    assert sum(len(t.indexes) for t in metadata.tables.values()) == 73


def test_schedule_columns() -> None:
    assert [c.name for c in tables()[0].columns] == [
        "id",
        "beacon_id",
        "interval_seconds",
        "next_due_at",
        "state",
        "created_at",
        "updated_at",
        "row_version",
    ]


def test_work_columns() -> None:
    assert [c.name for c in tables()[1].columns] == [
        "id",
        "schedule_id",
        "beacon_id",
        "due_at",
        "state",
        "lease_started_at",
        "lease_expires_at",
        "lease_token",
        "attempt_count",
        "created_at",
        "row_version",
    ]


def test_run_columns() -> None:
    assert [c.name for c in tables()[2].columns] == [
        "id",
        "work_item_id",
        "beacon_id",
        "revision_no",
        "parser_outcome_id",
        "route_id",
        "state",
        "started_at",
        "completed_at",
        "row_version",
    ]


def test_observation_columns() -> None:
    assert [c.name for c in tables()[3].columns] == [
        "id",
        "run_id",
        "beacon_id",
        "external_listing_key",
        "snapshot",
        "observed_at",
        "fingerprint",
    ]


def test_listing_columns() -> None:
    assert [c.name for c in tables()[4].columns] == [
        "id",
        "beacon_id",
        "external_listing_key",
        "last_seen_at",
        "last_snapshot",
        "first_seen_at",
        "row_version",
        "updated_at",
    ]


def test_anchor_columns() -> None:
    assert [c.name for c in tables()[5].columns] == [
        "id",
        "beacon_id",
        "anchor_key",
        "corrected_by_account_id",
        "correction_reason",
        "updated_at",
        "row_version",
    ]


def test_uuid_columns_are_application_generated() -> None:
    assert all(
        c.server_default is None
        for t in tables()
        for c in t.columns
        if isinstance(c.type, postgresql.UUID)
    )


def test_timestamps_timezone_aware() -> None:
    assert all(
        c.type.timezone
        for t in tables()
        for c in t.columns
        if isinstance(c.type, postgresql.TIMESTAMP)
    )


def test_json_is_jsonb() -> None:
    assert all(
        isinstance(c.type, postgresql.JSONB)
        for t in tables()
        for c in t.columns
        if c.name in {"snapshot", "last_snapshot"}
    )


def test_row_defaults() -> None:
    assert all(
        t.c.row_version.server_default is not None
        for t in (tables()[0], tables()[2], tables()[4], tables()[5])
    )


def test_unique_constraint_names() -> None:
    assert {
        c.name
        for t in tables()
        for c in t.constraints
        if c.__class__.__name__ == "UniqueConstraint"
    } == {
        "uq_scan_schedules_beacon_id",
        "uq_scan_work_items_schedule_due_at",
        "uq_scan_runs_work_item_id",
        "uq_scan_listing_observations_run_external_key",
        "uq_scan_beacon_listing_state_beacon_external_key",
        "uq_scan_anchors_beacon_id",
    }


def test_schedule_checks() -> None:
    assert checks(tables()[0]) == {"interval_seconds > 0", "btrim(state) <> ''", "row_version > 0"}


def test_work_checks() -> None:
    assert len(checks(tables()[1])) == 4


def test_run_checks() -> None:
    assert checks(tables()[2]) == {
        "revision_no > 0",
        "btrim(state) <> ''",
        "completed_at IS NULL OR completed_at >= started_at",
        "row_version > 0",
    }


def test_observation_checks() -> None:
    assert len(checks(tables()[3])) == 3


def test_listing_checks() -> None:
    assert len(checks(tables()[4])) == 3


def test_anchor_checks() -> None:
    assert len(checks(tables()[5])) == 3


def test_immediate_fk_count() -> None:
    assert sum(len(t.foreign_key_constraints) for t in tables()) == 13


def test_all_fks_restrict() -> None:
    assert all(f.ondelete == "RESTRICT" for t in tables() for f in t.foreign_key_constraints)


def test_composite_revision_fk() -> None:
    assert any(
        tuple(e.parent.name for e in f.elements) == ("beacon_id", "revision_no")
        for f in tables()[2].foreign_key_constraints
    )


def test_route_fk_immediate_and_nullable() -> None:
    assert tables()[2].c.route_id.nullable and any(
        f.elements[0].target_fullname == "mayak.egress_routes.id"
        for f in tables()[2].foreign_key_constraints
    )


def test_parser_fk_is_absent() -> None:
    assert any(
        f.name == "fk_scan_runs_parser_outcome_id_parser_outcomes"
        and f.use_alter is True
        and f.elements[0].target_fullname == "mayak.parser_outcomes.id"
        for f in tables()[2].foreign_key_constraints
    )


def test_deferred_parser_marker_exact() -> None:
    assert tables()[2].info == {}


def test_no_cascades() -> None:
    assert all(f.ondelete != "CASCADE" for t in tables() for f in t.foreign_key_constraints)


def test_exact_index_names() -> None:
    assert {i.name for t in tables() for i in t.indexes} == {
        "ix_scan_schedules_active_due",
        "ix_scan_work_items_due",
        "ix_scan_work_items_claimed_expiry",
        "ix_scan_runs_beacon_started_at",
        "ix_scan_runs_active_states",
        "ix_scan_listing_observations_beacon_observed_at",
        "ix_scan_beacon_listing_state_beacon_last_seen_at",
        "ix_scan_anchors_beacon_updated_at",
    }


def test_partial_predicates_compile() -> None:
    assert all(
        pred(i)
        for t in tables()
        for i in t.indexes
        if i.dialect_options["postgresql"].get("where") is not None
    )


def test_no_forbidden_fields() -> None:
    assert not any(
        x in c.name.lower()
        for t in tables()
        for c in t.columns
        for x in ("payload", "html", "cookie", "password", "secret", "proxy")
    )


def test_no_state_enum_checks() -> None:
    assert not any(
        " IN (" in str(c.sqltext)
        for t in tables()
        for c in t.constraints
        if isinstance(c, CheckConstraint)
    )


def test_schema_is_mayak() -> None:
    assert all(t.schema == "mayak" for t in tables())


def test_naming_convention_is_canonical() -> None:
    assert isolated().naming_convention == NAMING_CONVENTION


def test_registration_replay_identity() -> None:
    m = isolated()
    first = register_scan_tables(m)
    second = register_scan_tables(m)
    assert all(a is b for a, b in zip(first, second))


def test_partial_registration_fails_closed() -> None:
    m = isolated()
    Table(NAMES[0], m)
    with pytest.raises(RuntimeError):
        register_scan_tables(m)


def test_wrong_first_schema_fails_before_mutation() -> None:
    m = MetaData(schema="other", naming_convention=NAMING_CONVENTION)
    with pytest.raises(RuntimeError):
        register_scan_tables(m)


def test_wrong_first_info_fails_before_mutation() -> None:
    m = isolated()
    m.info["x"] = 1
    with pytest.raises(RuntimeError):
        register_scan_tables(m)


def test_import_is_inert(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = []
    monkeypatch.setattr("sqlalchemy.create_engine", lambda *a, **k: calls.append("engine"))
    importlib.import_module("mayak.persistence.schema.scan")
    assert calls == []
