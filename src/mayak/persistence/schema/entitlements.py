"""Module 03 Entitlements & Billing physical table registrations.

"""

# ruff: noqa: E501

from __future__ import annotations

from typing import Any

from sqlalchemy import (
    CHAR,
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
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID
from sqlalchemy.dialects.postgresql import dialect as postgresql_dialect

_TABLE_NAMES = (
    "entitlement_tariff_definitions",
    "entitlement_access_grants",
    "entitlement_usage_counters",
    "billing_payment_records",
    "billing_payment_operations",
    "billing_reconciliations",
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
        for index, character in enumerate(result):
            if character == "(":
                depth += 1
            elif character == ")":
                depth -= 1
                if depth == 0 and index != len(result) - 1:
                    enclosed = False
                    break
        if enclosed:
            result = result[1:-1].strip()
        else:
            break
    return result


def _stable_value(value: object) -> object:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, (list, tuple)):
        return tuple(_stable_value(item) for item in value)
    if isinstance(value, dict):
        return tuple(sorted((str(key), _stable_value(item)) for key, item in value.items()))
    return _normalized_sql(value)


def _compiled_type(column_type: Any) -> str:
    return str(column_type.compile(dialect=_POSTGRESQL_DIALECT))


def _type_options(column_type: object) -> tuple[tuple[str, object], ...]:
    options: tuple[str, ...] = (
        "length",
        "precision",
        "scale",
        "timezone",
        "as_uuid",
        "collation",
    )
    if isinstance(column_type, JSONB):
        options += ("none_as_null", "hashable", "should_evaluate_none", "astext_type")
    values: list[tuple[str, object]] = []
    for name in options:
        if hasattr(column_type, name):
            value = getattr(column_type, name)
            if name == "astext_type" and value is not None:
                value = (type(value).__module__, type(value).__name__, _compiled_type(value))
            values.append((name, _stable_value(value)))
    return tuple(values)


def _type_signature(column: Column[object]) -> tuple[object, ...]:
    column_type = column.type
    return (
        type(column_type).__module__,
        type(column_type).__name__,
        _compiled_type(column_type),
        _type_options(column_type),
    )


def _default_signature(column: Column[object]) -> str | None:
    if column.server_default is None:
        return None
    return _normalized_sql(getattr(column.server_default, "arg", column.server_default))


def _value_signature(value: object) -> object:
    if value is None:
        return None
    argument = getattr(value, "arg", value)
    if callable(argument):
        return (
            "callable",
            getattr(argument, "__module__", ""),
            getattr(argument, "__qualname__", repr(argument)),
        )
    return _stable_value(argument)


def _column_property_signature(column: Column[object]) -> tuple[object, ...]:
    identity = column.identity
    computed = column.computed
    return (
        column.name,
        _type_signature(column),
        column.nullable,
        column.primary_key,
        _default_signature(column),
        _value_signature(column.default),
        _value_signature(column.onupdate),
        _value_signature(column.server_onupdate),
        column.autoincrement,
        column.unique,
        column.index,
        column.comment,
        column.system,
        tuple(
            (name, _stable_value(getattr(identity, name, None)))
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


def _dialect_options_signature(options: object) -> tuple[tuple[str, object], ...]:
    if not hasattr(options, "items"):
        return ()

    def is_default(value: object) -> bool:
        return value is None or value is False or value == {} or value == ()

    return tuple(
        (
            str(dialect),
            tuple(
                sorted(
                    (str(key), _normalized_sql(value))
                    for key, value in values.items()
                    if not is_default(value)
                )
            ),
        )
        for dialect, values in sorted(options.items())
        if any(not is_default(value) for value in values.values())
    )


def _constraint_signature(constraint: Any) -> tuple[object, ...]:
    columns = tuple(column.name for column in getattr(constraint, "columns", ()))
    return (
        type(constraint).__module__,
        type(constraint).__name__,
        constraint.name,
        columns,
        _normalized_sql(getattr(constraint, "sqltext", ""))
        if isinstance(constraint, CheckConstraint)
        else "",
        getattr(constraint, "deferrable", None),
        getattr(constraint, "initially", None),
        _dialect_options_signature(getattr(constraint, "dialect_options", {})),
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
        _dialect_options_signature(constraint.dialect_options),
    )


def _index_signature(index: Index) -> tuple[object, ...]:
    postgresql_options: Any = index.dialect_options.get("postgresql", {})
    predicate = postgresql_options.get("where")
    return (
        type(index).__module__,
        type(index).__name__,
        index.name,
        tuple(getattr(column, "name", str(column)) for column in index.expressions),
        index.unique,
        _normalized_sql(predicate) if predicate is not None else None,
        _dialect_options_signature(index.dialect_options),
    )


def _table_signature(table: Table) -> tuple[object, ...]:
    return (
        table.name,
        table.schema,
        table.comment,
        tuple(getattr(table, "prefixes", ())),
        table.implicit_returning,
        _dialect_options_signature(table.dialect_options),
        tuple(sorted((str(key), _stable_value(value)) for key, value in table.info.items())),
        tuple(_column_property_signature(column) for column in table.columns),
        tuple(
            sorted(
                _foreign_key_signature(constraint)
                if isinstance(constraint, ForeignKeyConstraint)
                else _constraint_signature(constraint)
                for constraint in table.constraints
            )
        ),
        tuple(sorted(_index_signature(index) for index in table.indexes)),
    )


def _canonical_model() -> tuple[Table, Table, Table, Table, Table, Table]:
    canonical = MetaData(
        schema="mayak",
        naming_convention=_NAMING_CONVENTION,
    )
    Table("identity_accounts", canonical, Column("id", UUID(as_uuid=True), primary_key=True))
    return _register_canonical_tables(canonical)


def _validate_existing(tables: list[Table]) -> None:
    expected = _canonical_model()
    for actual, canonical in zip(tables, expected):
        if _table_signature(actual) != _table_signature(canonical):
            raise RuntimeError(f"conflicting existing {actual.name} registration")


def register_entitlement_tables(
    target_metadata: MetaData,
) -> tuple[Table, Table, Table, Table, Table, Table]:
    """Register exactly the canonical Module 03 tables, without database I/O."""
    if target_metadata.schema != "mayak":
        raise RuntimeError("entitlement tables require mayak schema")
    if _key(target_metadata, "identity_accounts") not in target_metadata.tables:
        raise RuntimeError("identity table registration is required before entitlements")
    present = [_key(target_metadata, name) in target_metadata.tables for name in _TABLE_NAMES]
    if any(present) and not all(present):
        raise RuntimeError("partial entitlement table registration is not supported")
    if all(present):
        tables = [target_metadata.tables[_key(target_metadata, name)] for name in _TABLE_NAMES]
        _validate_existing(tables)
        return tuple(tables)  # type: ignore[return-value]

    return _register_canonical_tables(target_metadata)


def _register_canonical_tables(
    target_metadata: MetaData,
) -> tuple[Table, Table, Table, Table, Table, Table]:
    """Build the unchanged canonical Module 03 metadata registration."""

    tariffs = Table(
        "entitlement_tariff_definitions",
        target_metadata,
        Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        Column("code", String(64), nullable=False),
        Column("version", BigInteger, nullable=False),
        Column("price_minor", BigInteger, nullable=False),
        Column("currency", CHAR(3), nullable=False),
        Column("min_interval_seconds", BigInteger, nullable=False),
        Column("step_seconds", BigInteger, nullable=False),
        Column("active_from", TIMESTAMP(timezone=True), nullable=False),
        Column("active_until", TIMESTAMP(timezone=True), nullable=True),
        Column("created_at", TIMESTAMP(timezone=True), nullable=False),
        UniqueConstraint("code", "version", name="uq_entitlement_tariff_definitions_code_version"),
        CheckConstraint("btrim(code) <> ''", name="code_nonempty"),
        CheckConstraint("price_minor >= 0", name="price_nonnegative"),
        CheckConstraint("min_interval_seconds > 0", name="min_interval_positive"),
        CheckConstraint("step_seconds > 0", name="step_positive"),
        CheckConstraint(
            "currency !~ '\\s' AND char_length(currency) = 3", name="currency_iso_length"
        ),
        CheckConstraint(
            "active_until IS NULL OR active_until > active_from", name="active_interval"
        ),
    )
    Index(
        "ix_entitlement_tariff_definitions_code_active_from", tariffs.c.code, tariffs.c.active_from
    )
    grants = Table(
        "entitlement_access_grants",
        target_metadata,
        Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        Column("account_id", UUID(as_uuid=True), nullable=False),
        Column("tariff_id", UUID(as_uuid=True), nullable=True),
        Column("source_code", String(64), nullable=False),
        # Semantic fields are application-owned after RF12_RUNTIME_HARDEN;
        # production writes must state the grant kind explicitly.
        Column("grant_kind", String(32), nullable=False),
        Column("granted_capability", String(128), nullable=True),
        Column("granted_scope", String(128), nullable=True),
        Column("reason", String(512), nullable=False),
        Column("valid_from", TIMESTAMP(timezone=True), nullable=False),
        Column("valid_until", TIMESTAMP(timezone=True), nullable=False),
        Column("state", String(64), nullable=False),
        Column("created_at", TIMESTAMP(timezone=True), nullable=False),
        Column("updated_at", TIMESTAMP(timezone=True), nullable=False),
        Column("row_version", BigInteger, nullable=False, server_default=text("1")),
        ForeignKeyConstraint(["account_id"], ["mayak.identity_accounts.id"], ondelete="RESTRICT"),
        ForeignKeyConstraint(
            ["tariff_id"], ["mayak.entitlement_tariff_definitions.id"], ondelete="RESTRICT"
        ),
        CheckConstraint("btrim(source_code) <> ''", name="source_code_nonempty"),
        CheckConstraint("grant_kind IN ('TARIFF', 'MANUAL')", name="grant_kind_allowed"),
        CheckConstraint(
            "grant_kind <> 'TARIFF' OR (tariff_id IS NOT NULL AND granted_capability IS NULL AND granted_scope IS NULL)",
            name="tariff_grant_fields_empty",
        ),
        CheckConstraint(
            "grant_kind <> 'MANUAL' OR (tariff_id IS NULL AND granted_capability IS NOT NULL AND btrim(granted_capability) <> '' AND granted_scope IS NOT NULL AND btrim(granted_scope) <> '')",
            name="manual_grant_fields_present",
        ),
        CheckConstraint(
            "reason IS NOT NULL AND btrim(reason) <> '' AND octet_length(reason) <= 512",
            name="reason_nonempty",
        ),
        CheckConstraint("btrim(state) <> ''", name="state_nonempty"),
        CheckConstraint("valid_until > valid_from", name="valid_interval"),
        CheckConstraint("row_version > 0", name="row_version_positive"),
    )
    Index(
        "ix_entitlement_access_grants_account_valid_until",
        grants.c.account_id,
        grants.c.valid_until,
    )
    Index(
        "ix_entitlement_access_grants_active",
        grants.c.account_id,
        grants.c.valid_from,
        grants.c.valid_until,
        postgresql_where=text("state = 'ACTIVE'"),
    )
    Index(
        "ix_entitlement_access_grants_manual_capability_scope",
        grants.c.account_id,
        grants.c.granted_capability,
        grants.c.granted_scope,
        postgresql_where=text("grant_kind = 'MANUAL' AND state = 'ACTIVE'"),
    )
    usage = Table(
        "entitlement_usage_counters",
        target_metadata,
        Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        Column("account_id", UUID(as_uuid=True), nullable=False),
        Column("counter_code", String(64), nullable=False),
        Column("window_start", TIMESTAMP(timezone=True), nullable=False),
        Column("window_end", TIMESTAMP(timezone=True), nullable=False),
        Column("consumed", BigInteger, nullable=False, server_default=text("0")),
        Column("limit_value", BigInteger, nullable=False),
        Column("created_at", TIMESTAMP(timezone=True), nullable=False),
        Column("updated_at", TIMESTAMP(timezone=True), nullable=False),
        Column("row_version", BigInteger, nullable=False, server_default=text("1")),
        ForeignKeyConstraint(["account_id"], ["mayak.identity_accounts.id"], ondelete="RESTRICT"),
        UniqueConstraint(
            "account_id",
            "counter_code",
            "window_start",
            name="uq_entitlement_usage_counters_account_code_window",
        ),
        CheckConstraint("btrim(counter_code) <> ''", name="counter_code_nonempty"),
        CheckConstraint("consumed >= 0", name="consumed_nonnegative"),
        CheckConstraint("limit_value >= 0", name="limit_value_nonnegative"),
        CheckConstraint("window_end > window_start", name="window_interval"),
        CheckConstraint("row_version > 0", name="row_version_positive"),
    )
    Index(
        "ix_entitlement_usage_counters_account_code_window_end",
        usage.c.account_id,
        usage.c.counter_code,
        usage.c.window_end,
    )
    payments = Table(
        "billing_payment_records",
        target_metadata,
        Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        Column("account_id", UUID(as_uuid=True), nullable=False),
        Column("provider_code", String(64), nullable=False),
        Column("external_payment_id", String(255), nullable=False),
        Column("amount_minor", BigInteger, nullable=False),
        Column("currency", CHAR(3), nullable=False),
        Column("state", String(64), nullable=False),
        Column("observed_at", TIMESTAMP(timezone=True), nullable=False),
        Column("safe_metadata", JSONB, nullable=False),
        Column("created_at", TIMESTAMP(timezone=True), nullable=False),
        Column("updated_at", TIMESTAMP(timezone=True), nullable=False),
        Column("row_version", BigInteger, nullable=False, server_default=text("1")),
        ForeignKeyConstraint(["account_id"], ["mayak.identity_accounts.id"], ondelete="RESTRICT"),
        UniqueConstraint(
            "provider_code",
            "external_payment_id",
            name="uq_billing_payment_records_provider_external_payment",
        ),
        CheckConstraint("btrim(provider_code) <> ''", name="provider_code_nonempty"),
        CheckConstraint("btrim(external_payment_id) <> ''", name="external_payment_id_nonempty"),
        CheckConstraint("amount_minor >= 0", name="amount_nonnegative"),
        CheckConstraint(
            "currency !~ '\\s' AND char_length(currency) = 3", name="currency_iso_length"
        ),
        CheckConstraint("btrim(state) <> ''", name="state_nonempty"),
        CheckConstraint("octet_length(safe_metadata::text) <= 8192", name="safe_metadata_size"),
        CheckConstraint("row_version > 0", name="row_version_positive"),
    )
    Index(
        "ix_billing_payment_records_account_observed_at",
        payments.c.account_id,
        payments.c.observed_at,
    )
    Index(
        "ix_billing_payment_records_pending_unknown",
        payments.c.state,
        payments.c.observed_at,
        postgresql_where=text("state IN ('PENDING', 'UNKNOWN')"),
    )
    operations = Table(
        "billing_payment_operations",
        target_metadata,
        Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        Column("payment_record_id", UUID(as_uuid=True), nullable=False),
        Column("operation_code", String(64), nullable=False),
        Column("idempotency_key", String(200), nullable=False),
        Column("request_fingerprint", CHAR(64), nullable=False),
        Column("state", String(64), nullable=False),
        Column("attempt_count", BigInteger, nullable=False, server_default=text("0")),
        Column("next_due_at", TIMESTAMP(timezone=True), nullable=True),
        Column("created_at", TIMESTAMP(timezone=True), nullable=False),
        Column("updated_at", TIMESTAMP(timezone=True), nullable=False),
        Column("row_version", BigInteger, nullable=False, server_default=text("1")),
        ForeignKeyConstraint(
            ["payment_record_id"], ["mayak.billing_payment_records.id"], ondelete="RESTRICT"
        ),
        UniqueConstraint(
            "payment_record_id",
            "operation_code",
            "idempotency_key",
            name="uq_billing_payment_operations_payment_operation_idempotency",
        ),
        CheckConstraint("btrim(operation_code) <> ''", name="operation_code_nonempty"),
        CheckConstraint("btrim(idempotency_key) <> ''", name="idempotency_key_nonempty"),
        CheckConstraint(
            "request_fingerprint ~ '^[0-9a-f]{64}$'", name="request_fingerprint_sha256"
        ),
        CheckConstraint("btrim(state) <> ''", name="state_nonempty"),
        CheckConstraint("attempt_count >= 0", name="attempt_count_nonnegative"),
        CheckConstraint("row_version > 0", name="row_version_positive"),
        CheckConstraint("state <> 'UNKNOWN' OR next_due_at IS NULL", name="unknown_without_due"),
    )
    Index(
        "ix_billing_payment_operations_due",
        operations.c.next_due_at,
        postgresql_where=text("state IN ('PENDING', 'RETRY')"),
    )
    reconciliations = Table(
        "billing_reconciliations",
        target_metadata,
        Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        Column("payment_record_id", UUID(as_uuid=True), nullable=False),
        Column("operation_id", UUID(as_uuid=True), nullable=True),
        Column("state", String(64), nullable=False),
        Column("due_at", TIMESTAMP(timezone=True), nullable=False),
        Column("resolved_at", TIMESTAMP(timezone=True), nullable=True),
        Column("safe_metadata", JSONB, nullable=False),
        Column("created_at", TIMESTAMP(timezone=True), nullable=False),
        Column("row_version", BigInteger, nullable=False, server_default=text("1")),
        ForeignKeyConstraint(
            ["payment_record_id"], ["mayak.billing_payment_records.id"], ondelete="RESTRICT"
        ),
        ForeignKeyConstraint(
            ["operation_id"], ["mayak.billing_payment_operations.id"], ondelete="RESTRICT"
        ),
        UniqueConstraint(
            "payment_record_id",
            "operation_id",
            name="uq_billing_reconciliations_payment_operation",
            postgresql_nulls_not_distinct=True,
        ),
        CheckConstraint("btrim(state) <> ''", name="state_nonempty"),
        CheckConstraint("octet_length(safe_metadata::text) <= 8192", name="safe_metadata_size"),
        CheckConstraint("resolved_at IS NULL OR resolved_at >= created_at", name="resolved_at"),
        CheckConstraint("row_version > 0", name="row_version_positive"),
    )
    Index(
        "ix_billing_reconciliations_unresolved_due",
        reconciliations.c.due_at,
        postgresql_where=reconciliations.c.resolved_at.is_(None),
    )
    return tariffs, grants, usage, payments, operations, reconciliations


__all__ = ["register_entitlement_tables"]
