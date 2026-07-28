"""Module 07 Egress Routing physical table registrations."""

from __future__ import annotations

from typing import Any

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Column,
    ForeignKeyConstraint,
    Index,
    MetaData,
    String,
    Table,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import CHAR, JSONB, TIMESTAMP, UUID
from sqlalchemy.dialects.postgresql import dialect as postgresql_dialect
from sqlalchemy.sql.type_api import TypeEngine

_TABLE_NAMES = (
    "egress_agents",
    "egress_routes",
    "egress_agent_heartbeats",
    "egress_route_leases",
)
_NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}
_DIALECT = postgresql_dialect()
_MARKER = {
    "local_columns": ("work_item_id",),
    "target_columns": ("mayak.scan_work_items.id",),
    "on_delete": "RESTRICT",
    "planned_revision": "RF09_FINALIZE",
}


def _key(metadata: MetaData, name: str) -> str:
    return f"{metadata.schema}.{name}" if metadata.schema else name


def _normal(value: object) -> str:
    result = " ".join(str(value).split())
    while result.startswith("(") and result.endswith(")"):
        depth = 0
        enclosed = True
        for position, character in enumerate(result):
            if character == "(":
                depth += 1
            elif character == ")":
                depth -= 1
                if depth == 0 and position != len(result) - 1:
                    enclosed = False
                    break
        if not enclosed:
            break
        result = result[1:-1].strip()
    return result


def _stable(value: object) -> object:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, (list, tuple)):
        return tuple(_stable(item) for item in value)
    if isinstance(value, dict):
        return tuple(sorted((str(key), _stable(item)) for key, item in value.items()))
    if hasattr(value, "compile"):
        return _normal(value)
    return (type(value).__module__, type(value).__name__)


def _type_signature(value: TypeEngine[Any]) -> tuple[object, ...]:
    options: tuple[str, ...] = ("length", "precision", "scale", "timezone", "as_uuid", "collation")
    if isinstance(value, JSONB):
        options += ("none_as_null", "hashable", "should_evaluate_none", "astext_type")
    return (
        type(value).__module__,
        type(value).__name__,
        str(value.compile(dialect=_DIALECT)),
        tuple(
            (option, _stable(getattr(value, option)))
            for option in options
            if hasattr(value, option)
        ),
    )


def _value_signature(value: object) -> object:
    if value is None:
        return None
    argument = getattr(value, "arg", value)
    if callable(argument):
        return (
            "callable",
            getattr(argument, "__module__", ""),
            getattr(argument, "__qualname__", ""),
        )
    return _stable(argument)


def _dialect_options(value: object) -> object:
    if not hasattr(value, "items"):
        return ()
    return tuple(
        (str(dialect), tuple(sorted((str(key), _normal(item)) for key, item in options.items())))
        for dialect, options in sorted(value.items())
        if options
    )


def _column_signature(column: Column[Any]) -> tuple[object, ...]:
    identity = column.identity
    computed = column.computed
    return (
        column.name,
        column.key,
        _type_signature(column.type),
        column.nullable,
        column.primary_key,
        column.autoincrement,
        column.unique,
        column.index,
        _value_signature(column.server_default),
        _value_signature(column.default),
        _value_signature(column.onupdate),
        _value_signature(column.server_onupdate),
        column.comment,
        _stable(column.info),
        column.system,
        _stable(identity) if identity is not None else None,
        (_normal(computed.sqltext), computed.persisted) if computed is not None else None,
    )


def _constraint_signature(constraint: Any) -> tuple[object, ...]:
    return (
        type(constraint).__module__,
        type(constraint).__name__,
        constraint.name,
        tuple(column.name for column in getattr(constraint, "columns", ())),
        _normal(getattr(constraint, "sqltext", ""))
        if isinstance(constraint, CheckConstraint)
        else "",
        getattr(constraint, "deferrable", None),
        getattr(constraint, "initially", None),
        _dialect_options(getattr(constraint, "dialect_options", {})),
        getattr(constraint, "comment", None),
        _stable(getattr(constraint, "info", {})),
    )


def _foreign_key_signature(constraint: ForeignKeyConstraint) -> tuple[object, ...]:
    return (
        type(constraint).__module__,
        type(constraint).__name__,
        constraint.name,
        tuple(element.parent.name for element in constraint.elements),
        tuple(element.target_fullname for element in constraint.elements),
        constraint.ondelete,
        constraint.onupdate,
        constraint.deferrable,
        constraint.initially,
        constraint.use_alter,
        constraint.match,
        _dialect_options(constraint.dialect_options),
        _stable(constraint.info),
    )


def _index_signature(index: Index) -> tuple[object, ...]:
    expressions = tuple(
        getattr(expression, "name", _normal(expression)) for expression in index.expressions
    )
    return (
        index.name,
        expressions,
        index.unique,
        _dialect_options(index.dialect_options),
        _stable(index.info),
    )


def _table_signature(table: Table) -> tuple[object, ...]:
    constraints = tuple(
        sorted(
            _foreign_key_signature(item)
            if isinstance(item, ForeignKeyConstraint)
            else _constraint_signature(item)
            for item in table.constraints
        )
    )
    return (
        type(table).__module__,
        type(table).__name__,
        table.name,
        table.schema,
        table.comment,
        tuple(getattr(table, "prefixes", ())),
        table.implicit_returning,
        _dialect_options(table.dialect_options),
        _stable(table.info),
        tuple(_column_signature(column) for column in table.columns),
        constraints,
        tuple(sorted(_index_signature(index) for index in table.indexes)),
    )


def _canonical(metadata: MetaData) -> tuple[Table, Table, Table, Table]:
    agents = Table(
        "egress_agents",
        metadata,
        Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        Column("agent_code", String(128), nullable=False),
        Column("credential_fingerprint", CHAR(64), nullable=True),
        Column("state", String(64), nullable=False),
        Column("created_at", TIMESTAMP(timezone=True), nullable=False),
        Column("updated_at", TIMESTAMP(timezone=True), nullable=False),
        Column("row_version", BigInteger, nullable=False, server_default=text("1")),
        UniqueConstraint("agent_code", name="uq_egress_agents_agent_code"),
        CheckConstraint("btrim(agent_code) <> ''", name="agent_code_nonempty"),
        CheckConstraint(
            "credential_fingerprint IS NULL OR credential_fingerprint ~ '^[0-9a-f]{64}$'",
            name="credential_fingerprint",
        ),
        CheckConstraint("btrim(state) <> ''", name="state_nonempty"),
        CheckConstraint("row_version > 0", name="row_version_positive"),
    )
    Index("ix_egress_agents_state_agent_code", agents.c.state, agents.c.agent_code)

    routes = Table(
        "egress_routes",
        metadata,
        Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        Column("agent_id", UUID(as_uuid=True), nullable=False),
        Column("route_code", String(128), nullable=False),
        Column("endpoint_ref", String(255), nullable=False),
        Column("state", String(64), nullable=False),
        Column("created_at", TIMESTAMP(timezone=True), nullable=False),
        Column("updated_at", TIMESTAMP(timezone=True), nullable=False),
        Column("row_version", BigInteger, nullable=False, server_default=text("1")),
        ForeignKeyConstraint(["agent_id"], ["mayak.egress_agents.id"], ondelete="RESTRICT"),
        UniqueConstraint("agent_id", "route_code", name="uq_egress_routes_agent_route_code"),
        CheckConstraint("btrim(route_code) <> ''", name="route_code_nonempty"),
        CheckConstraint("btrim(endpoint_ref) <> ''", name="endpoint_ref_nonempty"),
        CheckConstraint("btrim(state) <> ''", name="state_nonempty"),
        CheckConstraint("row_version > 0", name="row_version_positive"),
    )
    Index("ix_egress_routes_state_agent", routes.c.state, routes.c.agent_id)

    heartbeats = Table(
        "egress_agent_heartbeats",
        metadata,
        Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        Column("agent_id", UUID(as_uuid=True), nullable=False),
        Column("observed_at", TIMESTAMP(timezone=True), nullable=False),
        Column("state", String(64), nullable=False),
        Column("safe_metadata", JSONB, nullable=False),
        ForeignKeyConstraint(["agent_id"], ["mayak.egress_agents.id"], ondelete="RESTRICT"),
        CheckConstraint("btrim(state) <> ''", name="state_nonempty"),
        CheckConstraint("octet_length(safe_metadata::text) <= 8192", name="safe_metadata_size"),
    )
    Index(
        "ix_egress_agent_heartbeats_agent_observed_at",
        heartbeats.c.agent_id,
        heartbeats.c.observed_at,
    )

    leases = Table(
        "egress_route_leases",
        metadata,
        Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        Column("route_id", UUID(as_uuid=True), nullable=False),
        Column("work_item_id", UUID(as_uuid=True), nullable=False),
        Column("lease_token", UUID(as_uuid=True), nullable=False),
        Column("lease_started_at", TIMESTAMP(timezone=True), nullable=False),
        Column("lease_expires_at", TIMESTAMP(timezone=True), nullable=False),
        Column("state", String(64), nullable=False),
        ForeignKeyConstraint(["route_id"], ["mayak.egress_routes.id"], ondelete="RESTRICT"),
        UniqueConstraint("lease_token", name="uq_egress_route_leases_lease_token"),
        CheckConstraint("lease_expires_at > lease_started_at", name="lease_window"),
        CheckConstraint("btrim(state) <> ''", name="state_nonempty"),
        info={"deferred_foreign_keys": (_MARKER,)},
    )
    Index(
        "uq_egress_route_leases_active_route_work_item",
        leases.c.route_id,
        leases.c.work_item_id,
        unique=True,
        postgresql_where=text("state = 'ACTIVE'"),
    )
    Index(
        "ix_egress_route_leases_active_expires_at",
        leases.c.lease_expires_at,
        postgresql_where=text("state = 'ACTIVE'"),
    )
    return agents, routes, heartbeats, leases


def register_egress_tables(target_metadata: MetaData) -> tuple[Table, Table, Table, Table]:
    """Register Egress tables without engine, connection, or SQL I/O."""
    if target_metadata.schema != "mayak":
        raise RuntimeError("egress tables require mayak schema")
    if _stable(target_metadata.info) != _stable({}):
        raise RuntimeError("conflicting existing egress metadata")
    present = [_key(target_metadata, name) in target_metadata.tables for name in _TABLE_NAMES]
    if any(present) and not all(present):
        raise RuntimeError("partial egress table registration is not supported")
    if all(present):
        if _stable(target_metadata.naming_convention) != _stable(_NAMING_CONVENTION):
            raise RuntimeError("conflicting existing egress metadata")
        tables = tuple(target_metadata.tables[_key(target_metadata, name)] for name in _TABLE_NAMES)
        canonical_metadata = MetaData(schema="mayak", naming_convention=_NAMING_CONVENTION)
        expected = _canonical(canonical_metadata)
        for actual, wanted in zip(tables, expected):
            if _table_signature(actual) != _table_signature(wanted):
                raise RuntimeError(f"conflicting existing {actual.name} registration")
        return tables  # type: ignore[return-value]
    return _canonical(target_metadata)


__all__ = ["register_egress_tables"]
