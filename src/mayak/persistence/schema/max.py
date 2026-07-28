"""Module 10 MAX Adapter physical schema registration."""

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
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import BIGINT, CHAR, JSONB, TIMESTAMP, UUID
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
_NAMES = (
    "max_inbound_events",
    "max_identity_mappings",
    "max_delivery_mappings",
    "max_miniapp_nonces",
)


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
    options: tuple[str, ...] = ("length", "precision", "scale", "timezone", "as_uuid", "collation")
    if isinstance(value, JSONB):
        options += ("none_as_null", "hashable", "should_evaluate_none", "astext_type")
    return (
        type(value).__module__,
        type(value).__name__,
        str(value.compile(dialect=_DIALECT)),
        tuple((n, _stable(getattr(value, n))) for n in options if hasattr(value, n)),
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
        tuple(e.parent.name for e in constraint.elements),
        tuple(e.target_fullname for e in constraint.elements),
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
        tuple(getattr(e, "name", _normal(e)) for e in index.expressions),
        index.unique,
        _dialect_options(index.dialect_options),
        _stable(index.info),
    )


def _table_signature(table: Table) -> tuple[object, ...]:
    constraints = tuple(
        sorted(
            _fk_signature(c) if isinstance(c, ForeignKeyConstraint) else _constraint_signature(c)
            for c in table.constraints
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
        tuple(_column_signature(c) for c in table.columns),
        constraints,
        tuple(sorted(_index_signature(i) for i in table.indexes)),
    )


def _canonical(metadata: MetaData) -> tuple[Table, Table, Table, Table]:
    inbound = Table(
        "max_inbound_events",
        metadata,
        Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        Column("provider_event_id", String(255), nullable=False),
        Column("event_fingerprint", CHAR(64), nullable=False),
        Column("schema_version", String(32), nullable=False),
        Column("normalized_data", JSONB, nullable=False),
        Column("received_at", TIMESTAMP(timezone=True), nullable=False),
        UniqueConstraint(
            "provider_event_id",
            "event_fingerprint",
            name="uq_max_inbound_events_provider_event_fingerprint",
        ),
        CheckConstraint("btrim(provider_event_id) <> ''", name=conv("provider_event_id_nonempty")),
        CheckConstraint(
            "event_fingerprint ~ '^[0-9a-f]{64}$'", name=conv("event_fingerprint_format")
        ),
        CheckConstraint("btrim(schema_version) <> ''", name=conv("schema_version_nonempty")),
        CheckConstraint(
            "octet_length(normalized_data::text) <= 65536", name=conv("normalized_data_size")
        ),
    )
    Index("ix_max_inbound_events_provider_event_id", inbound.c.provider_event_id)
    Index("ix_max_inbound_events_received_at", inbound.c.received_at)

    identity = Table(
        "max_identity_mappings",
        metadata,
        Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        Column("provider_link_id", UUID(as_uuid=True), nullable=False),
        Column("max_user_ref", String(255), nullable=False),
        Column("created_at", TIMESTAMP(timezone=True), nullable=False),
        Column("updated_at", TIMESTAMP(timezone=True), nullable=False),
        Column("row_version", BIGINT, nullable=False, server_default=text("1")),
        ForeignKeyConstraint(
            ["provider_link_id"], ["mayak.identity_provider_links.id"], ondelete="RESTRICT"
        ),
        UniqueConstraint("max_user_ref", name="uq_max_identity_mappings_max_user_ref"),
        UniqueConstraint("provider_link_id", name="uq_max_identity_mappings_provider_link_id"),
        CheckConstraint("btrim(max_user_ref) <> ''", name=conv("max_user_ref_nonempty")),
        CheckConstraint("row_version > 0", name=conv("row_version_positive")),
    )
    Index("ix_max_identity_mappings_provider_link_id", identity.c.provider_link_id)

    delivery = Table(
        "max_delivery_mappings",
        metadata,
        Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        Column("attempt_id", UUID(as_uuid=True), nullable=False),
        Column("max_message_ref", String(255), nullable=True),
        Column("created_at", TIMESTAMP(timezone=True), nullable=False),
        ForeignKeyConstraint(
            ["attempt_id"], ["mayak.notification_delivery_attempts.id"], ondelete="RESTRICT"
        ),
        UniqueConstraint("attempt_id", name="uq_max_delivery_mappings_attempt_id"),
        CheckConstraint(
            "max_message_ref IS NULL OR btrim(max_message_ref) <> ''",
            name=conv("max_message_ref_nonempty_when_present"),
        ),
    )
    Index(
        "ux_max_delivery_mappings_message_ref",
        delivery.c.max_message_ref,
        unique=True,
        postgresql_where=text("max_message_ref IS NOT NULL"),
    )

    nonces = Table(
        "max_miniapp_nonces",
        metadata,
        Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        Column("nonce_hash", CHAR(64), nullable=False),
        Column("account_id", UUID(as_uuid=True), nullable=True),
        Column("expires_at", TIMESTAMP(timezone=True), nullable=False),
        Column("consumed_at", TIMESTAMP(timezone=True), nullable=True),
        Column("created_at", TIMESTAMP(timezone=True), nullable=False),
        Column("row_version", BIGINT, nullable=False, server_default=text("1")),
        ForeignKeyConstraint(["account_id"], ["mayak.identity_accounts.id"], ondelete="RESTRICT"),
        UniqueConstraint("nonce_hash", name="uq_max_miniapp_nonces_nonce_hash"),
        CheckConstraint("nonce_hash ~ '^[0-9a-f]{64}$'", name=conv("nonce_hash_format")),
        CheckConstraint("expires_at > created_at", name=conv("expires_after_created")),
        CheckConstraint("row_version > 0", name=conv("row_version_positive")),
    )
    Index(
        "ix_max_miniapp_nonces_expires_at",
        nonces.c.expires_at,
        postgresql_where=text("consumed_at IS NULL"),
    )
    return inbound, identity, delivery, nonces


def register_max_tables(target_metadata: MetaData) -> tuple[Table, Table, Table, Table]:
    """Attach or validate the four MAX Adapter tables without I/O."""
    if target_metadata.schema != "mayak":
        raise RuntimeError("max tables require mayak schema")
    if _stable(target_metadata.naming_convention) != _stable(_CONVENTION) or _stable(
        target_metadata.info
    ) != _stable({}):
        raise RuntimeError("conflicting existing max metadata")
    prerequisites = (
        "identity_provider_links",
        "notification_delivery_attempts",
        "identity_accounts",
    )
    missing = tuple(
        _key(target_metadata, n)
        for n in prerequisites
        if _key(target_metadata, n) not in target_metadata.tables
    )
    if missing:
        raise RuntimeError("missing max prerequisites: " + ", ".join(missing))
    present = tuple(n for n in _NAMES if _key(target_metadata, n) in target_metadata.tables)
    if present and present != _NAMES:
        raise RuntimeError("partial max table registration")
    existing_order = tuple(
        k.rsplit(".", 1)[-1] for k in target_metadata.tables if k.rsplit(".", 1)[-1] in _NAMES
    )
    if existing_order and existing_order != _NAMES:
        raise RuntimeError("conflicting max table order")
    expected = _canonical(MetaData(schema="mayak", naming_convention=_CONVENTION))
    if present == _NAMES:
        actual = tuple(target_metadata.tables[_key(target_metadata, n)] for n in _NAMES)
        if any(_table_signature(a) != _table_signature(e) for a, e in zip(actual, expected)):
            raise RuntimeError("conflicting existing max registration")
        return cast(tuple[Table, Table, Table, Table], actual)
    return _canonical(target_metadata)


__all__ = ["register_max_tables"]
