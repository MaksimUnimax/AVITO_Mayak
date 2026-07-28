"""Module 08 generic Notification Delivery physical table registration."""

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
    "notification_endpoints",
    "notification_events",
    "notification_outbox",
    "notification_delivery_attempts",
    "notification_delivery_reconciliations",
)
_PREREQUISITES = ("identity_accounts", "beacon_beacons", "scan_runs")


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
        tuple((item, _stable(getattr(value, item))) for item in options if hasattr(value, item)),
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


def _canonical(metadata: MetaData) -> tuple[Table, Table, Table, Table, Table]:
    endpoints = Table(
        "notification_endpoints",
        metadata,
        Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        Column("account_id", UUID(as_uuid=True), nullable=False),
        Column("provider_code", String(64), nullable=False),
        Column("endpoint_ref", String(255), nullable=False),
        Column("state", String(64), nullable=False),
        Column("created_at", TIMESTAMP(timezone=True), nullable=False),
        Column("updated_at", TIMESTAMP(timezone=True), nullable=False),
        Column("row_version", BIGINT, nullable=False, server_default=text("1")),
        ForeignKeyConstraint(["account_id"], ["mayak.identity_accounts.id"], ondelete="RESTRICT"),
        UniqueConstraint(
            "provider_code", "endpoint_ref", name="uq_notification_endpoints_provider_endpoint"
        ),
        CheckConstraint("btrim(provider_code) <> ''", name=conv("provider_code_nonempty")),
        CheckConstraint("btrim(endpoint_ref) <> ''", name=conv("endpoint_ref_nonempty")),
        CheckConstraint("btrim(state) <> ''", name=conv("state_nonempty")),
        CheckConstraint("row_version > 0", name=conv("row_version_positive")),
    )
    Index("ix_notification_endpoints_account_state", endpoints.c.account_id, endpoints.c.state)

    events = Table(
        "notification_events",
        metadata,
        Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        Column("account_id", UUID(as_uuid=True), nullable=False),
        Column("beacon_id", UUID(as_uuid=True), nullable=True),
        Column("run_id", UUID(as_uuid=True), nullable=True),
        Column("source_effect_fingerprint", CHAR(64), nullable=False),
        Column("event_code", String(64), nullable=False),
        Column("payload", JSONB, nullable=False),
        Column("created_at", TIMESTAMP(timezone=True), nullable=False),
        ForeignKeyConstraint(["account_id"], ["mayak.identity_accounts.id"], ondelete="RESTRICT"),
        ForeignKeyConstraint(["beacon_id"], ["mayak.beacon_beacons.id"], ondelete="RESTRICT"),
        ForeignKeyConstraint(["run_id"], ["mayak.scan_runs.id"], ondelete="RESTRICT"),
        UniqueConstraint(
            "source_effect_fingerprint", name="uq_notification_events_source_effect_fingerprint"
        ),
        CheckConstraint(
            "source_effect_fingerprint ~ '^[0-9a-f]{64}$'",
            name=conv("source_effect_fingerprint_format"),
        ),
        CheckConstraint("btrim(event_code) <> ''", name=conv("event_code_nonempty")),
        CheckConstraint("octet_length(payload::text) <= 65536", name=conv("payload_size")),
    )
    Index("ix_notification_events_account_created_at", events.c.account_id, events.c.created_at)
    Index("ix_notification_events_beacon_created_at", events.c.beacon_id, events.c.created_at)

    outbox = Table(
        "notification_outbox",
        metadata,
        Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        Column("event_id", UUID(as_uuid=True), nullable=False),
        Column("endpoint_id", UUID(as_uuid=True), nullable=False),
        Column("state", String(64), nullable=False),
        Column("available_at", TIMESTAMP(timezone=True), nullable=False),
        Column("lease_started_at", TIMESTAMP(timezone=True), nullable=True),
        Column("lease_expires_at", TIMESTAMP(timezone=True), nullable=True),
        Column("lease_token", UUID(as_uuid=True), nullable=True),
        Column("attempt_count", BIGINT, nullable=False, server_default=text("0")),
        Column("created_at", TIMESTAMP(timezone=True), nullable=False),
        Column("row_version", BIGINT, nullable=False, server_default=text("1")),
        ForeignKeyConstraint(["event_id"], ["mayak.notification_events.id"], ondelete="RESTRICT"),
        ForeignKeyConstraint(
            ["endpoint_id"], ["mayak.notification_endpoints.id"], ondelete="RESTRICT"
        ),
        UniqueConstraint("event_id", "endpoint_id", name="uq_notification_outbox_event_endpoint"),
        CheckConstraint("attempt_count >= 0", name=conv("attempt_nonnegative")),
        CheckConstraint("btrim(state) <> ''", name=conv("state_nonempty")),
        CheckConstraint("row_version > 0", name=conv("row_version_positive")),
        CheckConstraint(
            "(lease_started_at IS NULL AND lease_expires_at IS NULL) OR "
            "lease_expires_at > lease_started_at",
            name=conv("lease_window"),
        ),
    )
    Index(
        "ix_notification_outbox_due",
        outbox.c.available_at,
        outbox.c.id,
        postgresql_where=text("state IN ('PENDING', 'RETRY')"),
    )
    Index(
        "ix_notification_outbox_claimed_expiry",
        outbox.c.lease_expires_at,
        postgresql_where=text("state = 'CLAIMED'"),
    )

    attempts = Table(
        "notification_delivery_attempts",
        metadata,
        Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        Column("outbox_id", UUID(as_uuid=True), nullable=False),
        Column("attempt_number", BIGINT, nullable=False),
        Column("state", String(64), nullable=False),
        Column("provider_reference", String(255), nullable=True),
        Column("effect_fingerprint", CHAR(64), nullable=False),
        Column("started_at", TIMESTAMP(timezone=True), nullable=False),
        Column("completed_at", TIMESTAMP(timezone=True), nullable=True),
        Column("safe_metadata", JSONB, nullable=False),
        ForeignKeyConstraint(["outbox_id"], ["mayak.notification_outbox.id"], ondelete="RESTRICT"),
        UniqueConstraint(
            "outbox_id", "attempt_number", name="uq_notification_delivery_attempts_outbox_attempt"
        ),
        CheckConstraint("attempt_number >= 1", name=conv("attempt_number_positive")),
        CheckConstraint("btrim(state) <> ''", name=conv("state_nonempty")),
        CheckConstraint(
            "effect_fingerprint ~ '^[0-9a-f]{64}$'", name=conv("effect_fingerprint_format")
        ),
        CheckConstraint(
            "octet_length(safe_metadata::text) <= 8192", name=conv("safe_metadata_size")
        ),
        CheckConstraint(
            "completed_at IS NULL OR completed_at >= started_at", name=conv("completion_order")
        ),
    )
    Index(
        "ix_notification_delivery_attempts_outbox_started_at",
        attempts.c.outbox_id,
        attempts.c.started_at,
    )

    reconciliations = Table(
        "notification_delivery_reconciliations",
        metadata,
        Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        Column("attempt_id", UUID(as_uuid=True), nullable=False),
        Column("state", String(64), nullable=False),
        Column("due_at", TIMESTAMP(timezone=True), nullable=False),
        Column("resolved_at", TIMESTAMP(timezone=True), nullable=True),
        Column("safe_metadata", JSONB, nullable=False),
        Column("row_version", BIGINT, nullable=False, server_default=text("1")),
        ForeignKeyConstraint(
            ["attempt_id"], ["mayak.notification_delivery_attempts.id"], ondelete="RESTRICT"
        ),
        UniqueConstraint("attempt_id", name="uq_notification_delivery_reconciliations_attempt_id"),
        CheckConstraint("btrim(state) <> ''", name=conv("state_nonempty")),
        CheckConstraint(
            "octet_length(safe_metadata::text) <= 8192", name=conv("safe_metadata_size")
        ),
        CheckConstraint("row_version > 0", name=conv("row_version_positive")),
    )
    Index(
        "ix_notification_delivery_reconciliations_unresolved_due",
        reconciliations.c.due_at,
        postgresql_where=text("resolved_at IS NULL"),
    )
    return endpoints, events, outbox, attempts, reconciliations


def _validation_metadata() -> MetaData:
    result = MetaData(schema="mayak", naming_convention=_CONVENTION)
    for name in _PREREQUISITES:
        Table(name, result, Column("id", UUID(as_uuid=True), primary_key=True))
    return result


def register_notification_tables(
    target_metadata: MetaData,
) -> tuple[Table, Table, Table, Table, Table]:
    """Attach or validate the five generic Notification Delivery tables."""
    if target_metadata.schema != "mayak":
        raise RuntimeError("notification tables require mayak schema")
    if _stable(target_metadata.naming_convention) != _stable(_CONVENTION):
        raise RuntimeError("conflicting existing notification metadata")
    if _stable(target_metadata.info) != _stable({}):
        raise RuntimeError("conflicting existing notification metadata")
    missing = tuple(
        _key(target_metadata, name)
        for name in _PREREQUISITES
        if _key(target_metadata, name) not in target_metadata.tables
    )
    if missing:
        raise RuntimeError("missing notification prerequisites: " + ", ".join(missing))
    present = tuple(
        name for name in _NAMES if _key(target_metadata, name) in target_metadata.tables
    )
    if (
        present
        and tuple(
            key.rsplit(".", 1)[-1]
            for key in target_metadata.tables
            if key.rsplit(".", 1)[-1] in _NAMES
        )
        != _NAMES
    ):
        raise RuntimeError("partial notification table registration")
    expected = _canonical(_validation_metadata())
    if present != () and present != _NAMES:
        raise RuntimeError("partial notification table registration")
    if present == _NAMES:
        actual = tuple(target_metadata.tables[_key(target_metadata, name)] for name in _NAMES)
        if any(
            _table_signature(left) != _table_signature(right)
            for left, right in zip(actual, expected)
        ):
            raise RuntimeError("conflicting existing notification registration")
        return cast(tuple[Table, Table, Table, Table, Table], actual)
    return _canonical(target_metadata)


__all__ = ["register_notification_tables"]
