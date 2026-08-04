"""Module 11 Admin & Support physical schema registration."""

from __future__ import annotations

from typing import Any, cast

from sqlalchemy import (
    CheckConstraint,
    Column,
    ForeignKeyConstraint,
    Index,
    MetaData,
    String,
    Table,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import BIGINT, JSONB, TIMESTAMP, UUID
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
_NAMES = ("support_cases", "support_case_notes", "support_case_events")


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
        return tuple(sorted((str(k), _stable(v)) for k, v in value.items()))
    if hasattr(value, "compile"):
        return _normal(value)
    return (type(value).__module__, type(value).__name__)


def _type_signature(value: TypeEngine[Any]) -> tuple[object, ...]:
    options: tuple[str, ...] = (
        "length",
        "precision",
        "scale",
        "timezone",
        "as_uuid",
        "collation",
    )
    if isinstance(value, JSONB):
        options += ("none_as_null", "hashable", "should_evaluate_none", "astext_type")
    return (
        type(value).__module__,
        type(value).__name__,
        str(value.compile(dialect=_DIALECT)),
        tuple((name, _stable(getattr(value, name))) for name in options if hasattr(value, name)),
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
        (str(d), tuple(sorted((str(k), _normal(v)) for k, v in opts.items())))
        for d, opts in sorted(value.items())
        if opts
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
        tuple(c.name for c in getattr(constraint, "columns", ())),
        _normal(getattr(constraint, "sqltext", ""))
        if isinstance(constraint, CheckConstraint)
        else "",
        getattr(constraint, "deferrable", None),
        getattr(constraint, "initially", None),
        _dialect_options(getattr(constraint, "dialect_options", {})),
        _stable(getattr(constraint, "info", {})),
    )


def _fk_signature(constraint: ForeignKeyConstraint) -> tuple[object, ...]:
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
            _fk_signature(constraint)
            if isinstance(constraint, ForeignKeyConstraint)
            else _constraint_signature(constraint)
            for constraint in table.constraints
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


def _canonical(metadata: MetaData) -> tuple[Table, Table, Table]:
    cases = Table(
        "support_cases",
        metadata,
        Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        Column("account_id", UUID(as_uuid=True), nullable=False),
        Column("opened_by_account_id", UUID(as_uuid=True), nullable=False),
        Column("assigned_to_account_id", UUID(as_uuid=True), nullable=True),
        Column("state", String(64), nullable=False),
        Column("subject", Text, nullable=False),
        Column("created_at", TIMESTAMP(timezone=True), nullable=False),
        Column("updated_at", TIMESTAMP(timezone=True), nullable=False),
        Column("row_version", BIGINT, nullable=False, server_default=text("1")),
        ForeignKeyConstraint(["account_id"], ["mayak.identity_accounts.id"], ondelete="RESTRICT"),
        ForeignKeyConstraint(
            ["opened_by_account_id"], ["mayak.identity_accounts.id"], ondelete="RESTRICT"
        ),
        ForeignKeyConstraint(
            ["assigned_to_account_id"], ["mayak.identity_accounts.id"], ondelete="RESTRICT"
        ),
        CheckConstraint("btrim(state) <> ''", name=conv("state_nonempty")),
        CheckConstraint("btrim(subject) <> ''", name=conv("subject_nonempty")),
        CheckConstraint("row_version > 0", name=conv("row_version_positive")),
    )
    Index(
        "ix_support_cases_open_pending_updated_at",
        cases.c.state,
        cases.c.updated_at,
        postgresql_where=text(
            "state IN ('OPEN', 'IN_PROGRESS', 'WAITING_FOR_EVIDENCE', 'ESCALATED', 'AMBIGUOUS')"
        ),
    )
    Index("ix_support_cases_account_updated_at", cases.c.account_id, cases.c.updated_at)

    notes = Table(
        "support_case_notes",
        metadata,
        Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        Column("case_id", UUID(as_uuid=True), nullable=False),
        Column("author_account_id", UUID(as_uuid=True), nullable=False),
        Column("visibility", String(64), nullable=False),
        Column("body", Text, nullable=False),
        Column("created_at", TIMESTAMP(timezone=True), nullable=False),
        ForeignKeyConstraint(["case_id"], ["mayak.support_cases.id"], ondelete="RESTRICT"),
        ForeignKeyConstraint(
            ["author_account_id"], ["mayak.identity_accounts.id"], ondelete="RESTRICT"
        ),
        CheckConstraint("visibility IN ('PUBLIC', 'INTERNAL')", name=conv("visibility_allowed")),
        CheckConstraint("btrim(body) <> ''", name=conv("body_nonempty")),
    )
    Index("ix_support_case_notes_case_created_at", notes.c.case_id, notes.c.created_at)

    events = Table(
        "support_case_events",
        metadata,
        Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        Column("case_id", UUID(as_uuid=True), nullable=False),
        Column("actor_account_id", UUID(as_uuid=True), nullable=False),
        Column("event_code", String(64), nullable=False),
        Column("reason", Text, nullable=False),
        Column("details", JSONB, nullable=False),
        Column("created_at", TIMESTAMP(timezone=True), nullable=False),
        ForeignKeyConstraint(["case_id"], ["mayak.support_cases.id"], ondelete="RESTRICT"),
        ForeignKeyConstraint(
            ["actor_account_id"], ["mayak.identity_accounts.id"], ondelete="RESTRICT"
        ),
        CheckConstraint("btrim(event_code) <> ''", name=conv("event_code_nonempty")),
        CheckConstraint("btrim(reason) <> ''", name=conv("reason_nonempty")),
        CheckConstraint("octet_length(details::text) <= 65536", name=conv("details_size")),
    )
    Index("ix_support_case_events_case_created_at", events.c.case_id, events.c.created_at)
    Index("ix_support_case_events_actor_created_at", events.c.actor_account_id, events.c.created_at)
    return cases, notes, events


def register_support_tables(target_metadata: MetaData) -> tuple[Table, Table, Table]:
    """Attach or validate the three Support tables without I/O."""
    if target_metadata.schema != "mayak":
        raise RuntimeError("support tables require mayak schema")
    if _stable(target_metadata.naming_convention) != _stable(_CONVENTION):
        raise RuntimeError("conflicting existing support metadata")
    if _stable(target_metadata.info) != _stable({}):
        raise RuntimeError("conflicting existing support metadata")
    accounts_key = _key(target_metadata, "identity_accounts")
    if accounts_key not in target_metadata.tables:
        raise RuntimeError("missing support prerequisite: mayak.identity_accounts")
    accounts = target_metadata.tables[accounts_key]
    if accounts.schema != target_metadata.schema or "id" not in accounts.c:
        raise RuntimeError("incompatible support prerequisite: mayak.identity_accounts")
    present = tuple(
        name for name in _NAMES if _key(target_metadata, name) in target_metadata.tables
    )
    if present and present != _NAMES:
        raise RuntimeError("partial support table registration")
    existing_order = tuple(
        key.rsplit(".", 1)[-1] for key in target_metadata.tables if key.rsplit(".", 1)[-1] in _NAMES
    )
    if existing_order and existing_order != _NAMES:
        raise RuntimeError("conflicting support table order")
    expected_metadata = MetaData(schema="mayak", naming_convention=_CONVENTION)
    Table(
        "identity_accounts", expected_metadata, Column("id", UUID(as_uuid=True), primary_key=True)
    )
    expected = _canonical(expected_metadata)
    if present == _NAMES:
        actual = tuple(target_metadata.tables[_key(target_metadata, name)] for name in _NAMES)
        if any(_table_signature(a) != _table_signature(e) for a, e in zip(actual, expected)):
            raise RuntimeError("conflicting existing support registration")
        return cast(tuple[Table, Table, Table], actual)
    return _canonical(target_metadata)


__all__ = ["register_support_tables"]
