"""Module 05 parser outcome physical table registration."""

from __future__ import annotations

from typing import Any

from sqlalchemy import (
    CheckConstraint,
    Column,
    ForeignKeyConstraint,
    Index,
    MetaData,
    String,
    Table,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import CHAR, JSONB, TIMESTAMP, UUID
from sqlalchemy.dialects.postgresql import dialect as postgresql_dialect
from sqlalchemy.sql.elements import conv
from sqlalchemy.sql.type_api import TypeEngine

_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}
_DIALECT = postgresql_dialect()
_PREREQUISITES = ("beacon_beacons", "scan_runs", "egress_routes")


def _key(metadata: MetaData, name: str) -> str:
    return f"{metadata.schema}.{name}" if metadata.schema else name


def _normal(value: object) -> str:
    return " ".join(str(value).split())


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
        _stable(column.identity) if column.identity is not None else None,
        (_normal(column.computed.sqltext), column.computed.persisted)
        if column.computed is not None
        else None,
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
    return (
        index.name,
        tuple(getattr(expression, "name", _normal(expression)) for expression in index.expressions),
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


def _canonical(metadata: MetaData) -> Table:
    table = Table(
        "parser_outcomes",
        metadata,
        Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        Column("beacon_id", UUID(as_uuid=True), nullable=False),
        Column("run_id", UUID(as_uuid=True), nullable=True),
        Column("route_id", UUID(as_uuid=True), nullable=True),
        Column("outcome_code", String(64), nullable=False),
        Column("listing_snapshot", JSONB, nullable=True),
        Column("observed_at", TIMESTAMP(timezone=True), nullable=False),
        Column("fingerprint", CHAR(64), nullable=False),
        Column("created_at", TIMESTAMP(timezone=True), nullable=False),
        ForeignKeyConstraint(["beacon_id"], ["mayak.beacon_beacons.id"], ondelete="RESTRICT"),
        ForeignKeyConstraint(["run_id"], ["mayak.scan_runs.id"], ondelete="RESTRICT"),
        ForeignKeyConstraint(["route_id"], ["mayak.egress_routes.id"], ondelete="RESTRICT"),
        UniqueConstraint(
            "run_id",
            "fingerprint",
            name="uq_parser_outcomes_run_fingerprint",
            postgresql_nulls_not_distinct=True,
        ),
        CheckConstraint("btrim(outcome_code) <> ''", name=conv("outcome_code_nonempty")),
        CheckConstraint(
            "listing_snapshot IS NULL OR octet_length(listing_snapshot::text) <= 32768",
            name=conv("listing_snapshot_size"),
        ),
        CheckConstraint("fingerprint ~ '^[0-9a-f]{64}$'", name=conv("fingerprint_sha256")),
    )
    Index("ix_parser_outcomes_beacon_observed_at", table.c.beacon_id, table.c.observed_at)
    Index("ix_parser_outcomes_outcome_code_observed_at", table.c.outcome_code, table.c.observed_at)
    return table


def _validation_metadata() -> MetaData:
    metadata = MetaData(schema="mayak", naming_convention=_CONVENTION)
    for name in _PREREQUISITES:
        Table(name, metadata, Column("id", UUID(as_uuid=True), primary_key=True))
    return metadata


def register_parser_tables(target_metadata: MetaData) -> tuple[Table]:
    """Attach or validate the single immutable parser outcome table."""
    if target_metadata.schema != "mayak":
        raise RuntimeError("parser tables require mayak schema")
    if _stable(target_metadata.naming_convention) != _stable(_CONVENTION):
        raise RuntimeError("conflicting existing parser metadata")
    if _stable(target_metadata.info) != _stable({}):
        raise RuntimeError("conflicting existing parser metadata")
    missing = tuple(
        _key(target_metadata, name)
        for name in _PREREQUISITES
        if _key(target_metadata, name) not in target_metadata.tables
    )
    if missing:
        raise RuntimeError("missing parser prerequisites: " + ", ".join(missing))
    key = _key(target_metadata, "parser_outcomes")
    if key in target_metadata.tables:
        actual = target_metadata.tables[key]
        expected = _canonical(_validation_metadata())
        if _table_signature(actual) != _table_signature(expected):
            raise RuntimeError("conflicting existing parser registration")
        return (actual,)
    return (_canonical(target_metadata),)


__all__ = ["register_parser_tables"]
