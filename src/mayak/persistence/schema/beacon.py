"""Module 04 Beacon Management physical table registrations."""

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
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID
from sqlalchemy.dialects.postgresql import dialect as postgresql_dialect
from sqlalchemy.sql.type_api import TypeEngine

_TABLE_NAMES = (
    "beacon_beacons",
    "beacon_configuration_revisions",
    "beacon_filter_overrides",
    "beacon_lifecycle_events",
)
_NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}
_POSTGRESQL_DIALECT = postgresql_dialect()


def _key(metadata: MetaData, name: str) -> str:
    return f"{metadata.schema}.{name}" if metadata.schema else name


def _normalized_sql(value: object) -> str:
    result = " ".join(str(value).split())
    while result.startswith("(") and result.endswith(")"):
        depth = 0
        enclosed = True
        for index, char in enumerate(result):
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0 and index != len(result) - 1:
                    enclosed = False
                    break
        if enclosed:
            result = result[1:-1].strip()
        else:
            break
    return result


def _compiled_type(column_type: TypeEngine[Any]) -> str:
    return str(column_type.compile(dialect=_POSTGRESQL_DIALECT))


def _stable(value: object) -> object:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, (list, tuple)):
        return tuple(_stable(item) for item in value)
    if isinstance(value, dict):
        return tuple(sorted((str(key), _stable(item)) for key, item in value.items()))
    if hasattr(value, "compile"):
        return _normalized_sql(value)
    return (type(value).__module__, type(value).__name__)


def _dialect_options(options: object) -> tuple[tuple[str, object], ...]:
    if not hasattr(options, "items"):
        return ()
    return tuple(
        (
            str(dialect),
            tuple(
                sorted(
                    (str(key), _normalized_sql(value))
                    for key, value in values.items()
                    if value is not None and value is not False and value != {} and value != ()
                )
            ),
        )
        for dialect, values in sorted(options.items())
        if any(
            value is not None and value is not False and value != {} and value != ()
            for value in values.values()
        )
    )


def _type_signature(column_type: TypeEngine[Any]) -> tuple[object, ...]:
    names: tuple[str, ...] = ("length", "precision", "scale", "timezone", "as_uuid", "collation")
    if isinstance(column_type, JSONB):
        names += ("none_as_null", "hashable", "should_evaluate_none", "astext_type")
    return (
        type(column_type).__module__,
        type(column_type).__name__,
        _compiled_type(column_type),
        tuple(
            (
                name,
                _stable(getattr(column_type, name))
                if name != "astext_type" or getattr(column_type, name) is None
                else (
                    type(getattr(column_type, name)).__module__,
                    type(getattr(column_type, name)).__name__,
                    str(getattr(column_type, name).compile(dialect=_POSTGRESQL_DIALECT)),
                ),
            )
            for name in names
            if hasattr(column_type, name)
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
        tuple(
            (name, _stable(getattr(identity, name, None)))
            for name in (
                "name",
                "start",
                "increment",
                "minvalue",
                "maxvalue",
                "cycle",
                "cache",
                "order",
            )
        )
        if identity is not None
        else None,
        (_normalized_sql(computed.sqltext), computed.persisted) if computed is not None else None,
    )


def _constraint_signature(constraint: Any) -> tuple[object, ...]:
    return (
        type(constraint).__module__,
        type(constraint).__name__,
        constraint.name,
        tuple(column.name for column in getattr(constraint, "columns", ())),
        _normalized_sql(getattr(constraint, "sqltext", ""))
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
        getattr(constraint, "comment", None),
        _stable(constraint.info),
    )


def _index_signature(index: Index) -> tuple[object, ...]:
    return (
        type(index).__module__,
        type(index).__name__,
        index.name,
        tuple(getattr(expression, "name", str(expression)) for expression in index.expressions),
        index.unique,
        _dialect_options(index.dialect_options),
        _stable(index.info),
    )


def _table_signature(table: Table) -> tuple[object, ...]:
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
        tuple(
            sorted(
                _foreign_key_signature(item)
                if isinstance(item, ForeignKeyConstraint)
                else _constraint_signature(item)
                for item in table.constraints
            )
        ),
        tuple(sorted(_index_signature(index) for index in table.indexes)),
    )


def _marker() -> dict[str, object]:
    return {
        "local_columns": ("id", "current_revision_no"),
        "target_columns": (
            "mayak.beacon_configuration_revisions.beacon_id",
            "mayak.beacon_configuration_revisions.revision_no",
        ),
        "on_delete": "RESTRICT",
        "planned_revision": "RF09_FINALIZE",
    }


def _validate_prerequisites(metadata: MetaData) -> None:
    for name in ("identity_accounts", "filter_catalog_versions"):
        key = _key(metadata, name)
        table = metadata.tables.get(key)
        if table is None or "id" not in table.c:
            raise RuntimeError(f"missing or malformed prerequisite table {key}")
        column = table.c.id
        if not isinstance(column.type, UUID) or column.type.as_uuid is not True or column.nullable:
            raise RuntimeError(f"malformed prerequisite column {key}.id")


def _register_canonical(metadata: MetaData) -> tuple[Table, Table, Table, Table]:
    beacons = Table(
        "beacon_beacons",
        metadata,
        Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        Column("account_id", UUID(as_uuid=True), nullable=False),
        Column("name", Text, nullable=False),
        Column("current_revision_no", BigInteger, nullable=False),
        Column("current_revision_id", UUID(as_uuid=True), nullable=False),
        Column("state", String(64), nullable=False),
        Column("created_at", TIMESTAMP(timezone=True), nullable=False),
        Column("updated_at", TIMESTAMP(timezone=True), nullable=False),
        Column("row_version", BigInteger, nullable=False, server_default=text("1")),
        ForeignKeyConstraint(["account_id"], ["mayak.identity_accounts.id"], ondelete="RESTRICT"),
        UniqueConstraint("id", "current_revision_no", name="uq_beacon_beacons_id_current_revision"),
        CheckConstraint("btrim(name) <> ''", name="name_nonempty"),
        CheckConstraint("current_revision_no > 0", name="revision_positive"),
        CheckConstraint("btrim(state) <> ''", name="state_nonempty"),
        CheckConstraint("row_version > 0", name="row_version_positive"),
        info={"deferred_foreign_keys": (_marker(),)},
    )
    Index("ix_beacon_beacons_account_state", beacons.c.account_id, beacons.c.state)

    revisions = Table(
        "beacon_configuration_revisions",
        metadata,
        Column("beacon_id", UUID(as_uuid=True), primary_key=True, nullable=False),
        Column("revision_no", BigInteger, primary_key=True, nullable=False),
        Column("source_url", String(4096), nullable=False),
        Column("filter_candidate", JSONB, nullable=True),
        Column("accepted_filter", JSONB, nullable=False),
        Column("created_by_account_id", UUID(as_uuid=True), nullable=False),
        Column("created_at", TIMESTAMP(timezone=True), nullable=False),
        Column("catalog_version_id", UUID(as_uuid=True), nullable=True),
        ForeignKeyConstraint(["beacon_id"], ["mayak.beacon_beacons.id"], ondelete="RESTRICT"),
        ForeignKeyConstraint(
            ["created_by_account_id"], ["mayak.identity_accounts.id"], ondelete="RESTRICT"
        ),
        ForeignKeyConstraint(
            ["catalog_version_id"], ["mayak.filter_catalog_versions.id"], ondelete="RESTRICT"
        ),
        CheckConstraint("revision_no > 0", name="revision_positive"),
        CheckConstraint("btrim(source_url) <> ''", name="source_url_nonempty"),
        CheckConstraint(
            "filter_candidate IS NULL OR octet_length(filter_candidate::text) <= 65536",
            name="filter_candidate_size",
        ),
        CheckConstraint(
            "octet_length(accepted_filter::text) <= 65536", name="accepted_filter_size"
        ),
    )
    Index(
        "ix_beacon_configuration_revisions_beacon_created_at",
        revisions.c.beacon_id,
        revisions.c.created_at,
    )

    overrides = Table(
        "beacon_filter_overrides",
        metadata,
        Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        Column("beacon_id", UUID(as_uuid=True), nullable=False),
        Column("revision_no", BigInteger, nullable=False),
        Column("field_code", String(128), nullable=False),
        Column("value", JSONB, nullable=False),
        Column("created_at", TIMESTAMP(timezone=True), nullable=False),
        Column("row_version", BigInteger, nullable=False, server_default=text("1")),
        ForeignKeyConstraint(
            ["beacon_id", "revision_no"],
            [
                "mayak.beacon_configuration_revisions.beacon_id",
                "mayak.beacon_configuration_revisions.revision_no",
            ],
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "beacon_id",
            "revision_no",
            "field_code",
            name="uq_beacon_filter_overrides_beacon_revision_field",
        ),
        CheckConstraint("revision_no > 0", name="revision_positive"),
        CheckConstraint("btrim(field_code) <> ''", name="field_code_nonempty"),
        CheckConstraint("octet_length(value::text) <= 65536", name="value_size"),
        CheckConstraint("row_version > 0", name="row_version_positive"),
    )
    Index("ix_beacon_filter_overrides_beacon_field", overrides.c.beacon_id, overrides.c.field_code)

    events = Table(
        "beacon_lifecycle_events",
        metadata,
        Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        Column("beacon_id", UUID(as_uuid=True), nullable=False),
        Column("from_state", String(64), nullable=True),
        Column("to_state", String(64), nullable=False),
        Column("actor_account_id", UUID(as_uuid=True), nullable=True),
        Column("reason", Text, nullable=False),
        Column("created_at", TIMESTAMP(timezone=True), nullable=False),
        ForeignKeyConstraint(["beacon_id"], ["mayak.beacon_beacons.id"], ondelete="RESTRICT"),
        ForeignKeyConstraint(
            ["actor_account_id"], ["mayak.identity_accounts.id"], ondelete="RESTRICT"
        ),
        CheckConstraint(
            "from_state IS NULL OR btrim(from_state) <> ''", name="from_state_nonempty"
        ),
        CheckConstraint("btrim(to_state) <> ''", name="to_state_nonempty"),
        CheckConstraint("btrim(reason) <> ''", name="reason_nonempty"),
    )
    Index("ix_beacon_lifecycle_events_beacon_created_at", events.c.beacon_id, events.c.created_at)
    return beacons, revisions, overrides, events


def _canonical_model() -> tuple[Table, Table, Table, Table]:
    metadata = MetaData(schema="mayak", naming_convention=_NAMING_CONVENTION)
    Table(
        "identity_accounts",
        metadata,
        Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
    )
    Table(
        "filter_catalog_versions",
        metadata,
        Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
    )
    return _register_canonical(metadata)


def _validate_existing(metadata: MetaData, tables: list[Table]) -> None:
    canonical = MetaData(schema="mayak", naming_convention=_NAMING_CONVENTION)
    if _stable(metadata.naming_convention) != _stable(canonical.naming_convention) or _stable(
        metadata.info
    ) != _stable(canonical.info):
        raise RuntimeError("conflicting existing beacon metadata")
    for actual, expected in zip(tables, _canonical_model()):
        if _table_signature(actual) != _table_signature(expected):
            raise RuntimeError(f"conflicting existing {actual.name} registration")


def register_beacon_tables(target_metadata: MetaData) -> tuple[Table, Table, Table, Table]:
    """Register the four Beacon tables without engine, connection, or SQL I/O."""
    if target_metadata.schema != "mayak":
        raise RuntimeError("beacon tables require mayak schema")
    _validate_prerequisites(target_metadata)
    present = [_key(target_metadata, name) in target_metadata.tables for name in _TABLE_NAMES]
    if any(present) and not all(present):
        raise RuntimeError("partial beacon table registration is not supported")
    if all(present):
        tables = [target_metadata.tables[_key(target_metadata, name)] for name in _TABLE_NAMES]
        _validate_existing(target_metadata, tables)
        return tuple(tables)  # type: ignore[return-value]
    return _register_canonical(target_metadata)


__all__ = ["register_beacon_tables"]
