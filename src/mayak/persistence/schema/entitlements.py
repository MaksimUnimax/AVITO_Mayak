"""Module 03 Entitlements & Billing physical table registrations."""

from __future__ import annotations

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

_TABLE_NAMES = (
    "entitlement_tariff_definitions",
    "entitlement_access_grants",
    "entitlement_usage_counters",
    "billing_payment_records",
    "billing_payment_operations",
    "billing_reconciliations",
)


def _key(metadata: MetaData, name: str) -> str:
    return f"{metadata.schema}.{name}" if metadata.schema else name


def _validate_existing(metadata: MetaData, tables: list[Table]) -> None:
    expected_columns = {
        name: columns
        for name, columns in zip(
            _TABLE_NAMES,
            (
                (
                    "id",
                    "code",
                    "version",
                    "price_minor",
                    "currency",
                    "min_interval_seconds",
                    "step_seconds",
                    "active_from",
                    "active_until",
                    "created_at",
                ),
                (
                    "id",
                    "account_id",
                    "tariff_id",
                    "source_code",
                    "valid_from",
                    "valid_until",
                    "state",
                    "created_at",
                    "updated_at",
                    "row_version",
                ),
                (
                    "id",
                    "account_id",
                    "counter_code",
                    "window_start",
                    "window_end",
                    "consumed",
                    "limit_value",
                    "created_at",
                    "updated_at",
                    "row_version",
                ),
                (
                    "id",
                    "account_id",
                    "provider_code",
                    "external_payment_id",
                    "amount_minor",
                    "currency",
                    "state",
                    "observed_at",
                    "safe_metadata",
                    "created_at",
                    "updated_at",
                    "row_version",
                ),
                (
                    "id",
                    "payment_record_id",
                    "operation_code",
                    "idempotency_key",
                    "request_fingerprint",
                    "state",
                    "attempt_count",
                    "next_due_at",
                    "created_at",
                    "updated_at",
                    "row_version",
                ),
                (
                    "id",
                    "payment_record_id",
                    "operation_id",
                    "state",
                    "due_at",
                    "resolved_at",
                    "safe_metadata",
                    "created_at",
                    "row_version",
                ),
            ),
        )
    }
    for table in tables:
        if tuple(table.c) != tuple(table.c[name] for name in expected_columns[table.name]):
            raise RuntimeError(f"conflicting existing {table.name} registration")
    expected_fks = {
        "entitlement_access_grants": {
            "mayak.identity_accounts.id",
            "mayak.entitlement_tariff_definitions.id",
        },
        "entitlement_usage_counters": {"mayak.identity_accounts.id"},
        "billing_payment_records": {"mayak.identity_accounts.id"},
        "billing_payment_operations": {"mayak.billing_payment_records.id"},
        "billing_reconciliations": {
            "mayak.billing_payment_records.id",
            "mayak.billing_payment_operations.id",
        },
    }
    for table in tables:
        actual = {
            element.target_fullname
            for fk in table.foreign_key_constraints
            for element in fk.elements
        }
        if actual != expected_fks.get(table.name, set()) or any(
            fk.ondelete != "RESTRICT" for fk in table.foreign_key_constraints
        ):
            raise RuntimeError(f"conflicting existing {table.name} foreign keys")


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
        _validate_existing(target_metadata, tables)
        return tuple(tables)  # type: ignore[return-value]

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
        Column("tariff_id", UUID(as_uuid=True), nullable=False),
        Column("source_code", String(64), nullable=False),
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
