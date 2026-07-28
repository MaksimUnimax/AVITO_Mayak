from __future__ import annotations

import importlib
from typing import Any

import pytest
from sqlalchemy import CheckConstraint, Column, Index, MetaData, String, Table, UniqueConstraint
from sqlalchemy.dialects import postgresql

from mayak.persistence.metadata import NAMING_CONVENTION, metadata
from mayak.persistence.schema.egress import register_egress_tables

NAMES = ("egress_agents", "egress_routes", "egress_agent_heartbeats", "egress_route_leases")
MARKER = {
    "local_columns": ("work_item_id",),
    "target_columns": ("mayak.scan_work_items.id",),
    "on_delete": "RESTRICT",
    "planned_revision": "RF09_FINALIZE",
}


def isolated() -> MetaData:
    return MetaData(schema="mayak", naming_convention=NAMING_CONVENTION)


def checks(table: Table) -> set[str]:
    return {
        " ".join(str(c.sqltext).split())
        for c in table.constraints
        if isinstance(c, CheckConstraint)
    }


def predicate(index: Any) -> str:
    where = index.dialect_options["postgresql"].get("where")
    assert where is not None
    return " ".join(
        str(
            where.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True})
        ).split()
    )


def metadata_snapshot(target: MetaData) -> tuple[Any, ...]:
    tables = tuple(target.tables.items())
    objects = tuple(
        (
            id(table),
            tuple((id(constraint), constraint.name) for constraint in table.constraints),
            tuple((id(index), index.name) for index in table.indexes),
        )
        for _, table in tables
    )
    return target.schema, dict(target.naming_convention), dict(target.info), tables, objects


def test_canonical_order_columns_types_and_counts() -> None:
    target = isolated()
    tables = register_egress_tables(target)
    assert tuple(t.name for t in tables) == NAMES
    assert list(target.tables) == [f"mayak.{n}" for n in NAMES]
    assert len(target.tables) == 4 and sum(len(t.indexes) for t in target.tables.values()) == 5
    expected: Any = {
        "egress_agents": [
            "id",
            "agent_code",
            "credential_fingerprint",
            "state",
            "created_at",
            "updated_at",
            "row_version",
        ],
        "egress_routes": [
            "id",
            "agent_id",
            "route_code",
            "endpoint_ref",
            "state",
            "created_at",
            "updated_at",
            "row_version",
        ],
        "egress_agent_heartbeats": ["id", "agent_id", "observed_at", "state", "safe_metadata"],
        "egress_route_leases": [
            "id",
            "route_id",
            "work_item_id",
            "lease_token",
            "lease_started_at",
            "lease_expires_at",
            "state",
        ],
    }
    for table in tables:
        assert [c.name for c in table.columns] == expected[table.name]
        assert table.schema == "mayak" and [c.name for c in table.primary_key.columns] == ["id"]
        for column in table.columns:
            if isinstance(column.type, postgresql.UUID):
                assert column.type.as_uuid is True and column.server_default is None
            if isinstance(column.type, postgresql.TIMESTAMP):
                assert column.type.timezone is True
    assert len(metadata.tables) == 35
    assert sum(len(t.indexes) for t in metadata.tables.values()) == 49


def test_exact_column_options_and_defaults() -> None:
    agents = metadata.tables["mayak.egress_agents"]
    assert isinstance(agents.c.agent_code.type, String) and agents.c.agent_code.type.length == 128
    assert (
        isinstance(agents.c.credential_fingerprint.type, postgresql.CHAR)
        and agents.c.credential_fingerprint.type.length == 64
    )
    assert agents.c.credential_fingerprint.nullable is True
    assert agents.c.row_version.server_default is not None
    assert agents.c.row_version.server_default.arg.text == "1"  # type: ignore[attr-defined]
    routes = metadata.tables["mayak.egress_routes"]
    assert routes.c.endpoint_ref.type.length == 255  # type: ignore[attr-defined]
    assert routes.c.row_version.server_default is not None
    assert routes.c.row_version.server_default.arg.text == "1"  # type: ignore[attr-defined]
    assert metadata.tables["mayak.egress_route_leases"].c.lease_token.server_default is None
    assert isinstance(
        metadata.tables["mayak.egress_agent_heartbeats"].c.safe_metadata.type, postgresql.JSONB
    )


def test_exact_constraints_checks_and_restrict_fks() -> None:
    agents = metadata.tables["mayak.egress_agents"]
    routes = metadata.tables["mayak.egress_routes"]
    heartbeats = metadata.tables["mayak.egress_agent_heartbeats"]
    leases = metadata.tables["mayak.egress_route_leases"]
    assert {c.name for c in agents.constraints if isinstance(c, UniqueConstraint)} == {
        "uq_egress_agents_agent_code"
    }
    assert {c.name for c in routes.constraints if isinstance(c, UniqueConstraint)} == {
        "uq_egress_routes_agent_route_code"
    }
    assert {c.name for c in leases.constraints if isinstance(c, UniqueConstraint)} == {
        "uq_egress_route_leases_lease_token"
    }
    assert checks(agents) == {
        "btrim(agent_code) <> ''",
        "credential_fingerprint IS NULL OR credential_fingerprint ~ '^[0-9a-f]{64}$'",
        "btrim(state) <> ''",
        "row_version > 0",
    }
    assert checks(routes) == {
        "btrim(route_code) <> ''",
        "btrim(endpoint_ref) <> ''",
        "btrim(state) <> ''",
        "row_version > 0",
    }
    assert checks(heartbeats) == {"btrim(state) <> ''", "octet_length(safe_metadata::text) <= 8192"}
    assert checks(leases) == {"lease_expires_at > lease_started_at", "btrim(state) <> ''"}
    assert sum(len(t.foreign_key_constraints) for t in (agents, routes, heartbeats, leases)) == 3
    expected = (
        (routes, "agent_id", "mayak.egress_agents.id"),
        (heartbeats, "agent_id", "mayak.egress_agents.id"),
        (leases, "route_id", "mayak.egress_routes.id"),
    )
    for table, local, target in expected:
        fk: Any = next(iter(table.foreign_key_constraints))
        assert [e.parent.name for e in fk.elements] == [local]
        assert [e.target_fullname for e in fk.elements] == [target] and fk.ondelete == "RESTRICT"
    assert not any(
        element.parent.name == "work_item_id"
        for constraint in leases.foreign_key_constraints
        for element in constraint.elements
    )
    assert not any(
        " IN (" in str(c) for t in (agents, routes, heartbeats, leases) for c in t.constraints
    )


def test_deferred_marker_and_no_physical_work_item_fk() -> None:
    leases = metadata.tables["mayak.egress_route_leases"]
    assert leases.info == {"deferred_foreign_keys": (MARKER,)}
    assert not any(
        "scan_work_items" in element.target_fullname
        for constraint in leases.foreign_key_constraints
        for element in constraint.elements
    )
    target = isolated()
    register_egress_tables(target)
    assert target.tables["mayak.egress_route_leases"].info == leases.info


def test_indexes_are_exact_and_postgresql_predicates_compile() -> None:
    expected: Any = {
        "egress_agents": {
            "ix_egress_agents_state_agent_code": (("state", "agent_code"), False, None)
        },
        "egress_routes": {"ix_egress_routes_state_agent": (("state", "agent_id"), False, None)},
        "egress_agent_heartbeats": {
            "ix_egress_agent_heartbeats_agent_observed_at": (
                ("agent_id", "observed_at"),
                False,
                None,
            )
        },
        "egress_route_leases": {
            "uq_egress_route_leases_active_route_work_item": (
                ("route_id", "work_item_id"),
                True,
                "state = 'ACTIVE'",
            ),
            "ix_egress_route_leases_active_expires_at": (
                ("lease_expires_at",),
                False,
                "state = 'ACTIVE'",
            ),
        },
    }
    for name, wanted in expected.items():
        actual = metadata.tables[f"mayak.{name}"].indexes
        assert {i.name for i in actual} == set(wanted)
        for index in actual:
            columns, unique, where = wanted[index.name]
            assert tuple(getattr(c, "name", str(c)) for c in index.expressions) == columns
            assert index.unique is unique
            if where:
                assert predicate(index) == where


def test_replay_identity_partial_registration_and_conflicts_fail_closed() -> None:
    target = isolated()
    first = register_egress_tables(target)
    before = (list(target.tables), sum(len(t.indexes) for t in target.tables.values()))
    second = register_egress_tables(target)
    assert all(a is b for a, b in zip(first, second)) and before == (
        list(target.tables),
        sum(len(t.indexes) for t in target.tables.values()),
    )
    for count in (1, 2, 3):
        partial = isolated()
        for name in NAMES[:count]:
            Table(name, partial)
        with pytest.raises(RuntimeError, match="partial egress"):
            register_egress_tables(partial)
    for name in NAMES:
        conflict = isolated()
        register_egress_tables(conflict)
        before_names = list(conflict.tables)
        conflict.tables[f"mayak.{name}"].append_column(Column("wrong", String(1)))
        with pytest.raises(RuntimeError, match="conflicting existing"):
            register_egress_tables(conflict)
        assert list(conflict.tables) == before_names


def test_metadata_conflicts_and_index_mutation_are_rejected() -> None:
    target = isolated()
    register_egress_tables(target)
    target.naming_convention = {"ix": "different"}
    with pytest.raises(RuntimeError):
        register_egress_tables(target)
    target.naming_convention = NAMING_CONVENTION
    target.info["unexpected"] = True
    with pytest.raises(RuntimeError):
        register_egress_tables(target)
    target.info.clear()
    target.tables["mayak.egress_agents"].indexes.pop()
    with pytest.raises(RuntimeError):
        register_egress_tables(target)
    bad = MetaData(schema="other", naming_convention=NAMING_CONVENTION)
    with pytest.raises(RuntimeError):
        register_egress_tables(bad)


def test_first_registration_naming_conflict_is_rejected_without_mutation() -> None:
    conflicting = {"ix": "ix_%(column_0_label)s", "pk": "wrong_%(table_name)s"}
    target = MetaData(schema="mayak", naming_convention=conflicting)
    unrelated = Table(
        "unrelated",
        target,
        Column("id", String(1), primary_key=True),
        UniqueConstraint("id", name="uq_unrelated_id"),
    )
    index = Index("ix_unrelated_id", unrelated.c.id)
    before = metadata_snapshot(target)
    with pytest.raises(RuntimeError):
        register_egress_tables(target)
    assert metadata_snapshot(target) == before
    assert not any(key.rsplit(".", 1)[-1] in NAMES for key in target.tables)
    assert tuple(unrelated.indexes) == (index,)
    with pytest.raises(RuntimeError):
        register_egress_tables(target)
    assert metadata_snapshot(target) == before


def test_first_registration_metadata_info_conflict_is_rejected_without_mutation() -> None:
    target = isolated()
    target.info["unexpected"] = True
    before = metadata_snapshot(target)
    with pytest.raises(RuntimeError):
        register_egress_tables(target)
    assert metadata_snapshot(target) == before
    assert not target.tables


def test_first_registration_accepts_semantically_equal_convention_copy() -> None:
    target = MetaData(schema="mayak", naming_convention=dict(NAMING_CONVENTION))
    first = register_egress_tables(target)
    second = register_egress_tables(target)
    assert tuple(table.name for table in first) == NAMES
    assert len(target.tables) == 4
    assert sum(len(table.indexes) for table in target.tables.values()) == 5
    assert all(left is right for left, right in zip(first, second))


def test_first_registration_accepts_convention_in_different_insertion_order() -> None:
    reordered = {key: NAMING_CONVENTION[key] for key in reversed(tuple(NAMING_CONVENTION))}
    target = MetaData(schema="mayak", naming_convention=reordered)
    tables = register_egress_tables(target)
    assert tuple(table.name for table in tables) == NAMES
    assert {constraint.name for table in tables for constraint in table.constraints} >= {
        "pk_egress_agents",
        "pk_egress_routes",
        "pk_egress_agent_heartbeats",
        "pk_egress_route_leases",
    }
    assert {index.name for table in tables for index in table.indexes} == {
        "ix_egress_agents_state_agent_code",
        "ix_egress_routes_state_agent",
        "ix_egress_agent_heartbeats_agent_observed_at",
        "uq_egress_route_leases_active_route_work_item",
        "ix_egress_route_leases_active_expires_at",
    }


def test_forbidden_fields_and_uninvented_policy_are_absent() -> None:
    forbidden = (
        "raw",
        "payload",
        "html",
        "password",
        "secret",
        "cookie",
        "browser",
        "private_key",
        "certificate",
        "hostname",
        "ip_address",
        "port",
        "proxy",
        "vpn",
        "tunnel",
        "fallback",
        "priority",
        "retry",
        "backoff",
        "rate_limit",
        "capacity",
    )
    for name in NAMES:
        table = metadata.tables[f"mayak.{name}"]
        for column in table.columns:
            assert column.name == "lease_token" or not any(
                word in column.name.lower() for word in forbidden
            )
            assert column.server_default is None or column.name == "row_version"
        assert not any(" IN (" in str(c) for c in table.constraints)
    assert "lease_token" in metadata.tables["mayak.egress_route_leases"].c


def test_import_and_registration_are_inert(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    monkeypatch.setattr("sqlalchemy.create_engine", lambda *a, **k: calls.append("engine"))
    monkeypatch.setattr("sqlalchemy.engine.Engine.connect", lambda *a, **k: calls.append("connect"))
    assert importlib.import_module("mayak.persistence.schema.egress")
    register_egress_tables(isolated())
    assert calls == []
