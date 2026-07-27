"""RF-09 Module 03 Entitlements & Billing schema batch.

Technical ID: RF-09-08-M03-ENTITLEMENTS-AND-BILLING-SCHEMA-BATCH-20260727
Implementation owner: Module 14 / RF-09
Domain owner: Module 03
Domain tables created: 6
Deferred FK count: 0
Roll-forward-only.
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "RF09_M03"
down_revision = "RF09_M02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "entitlement_tariff_definitions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("version", sa.BigInteger(), nullable=False),
        sa.Column("price_minor", sa.BigInteger(), nullable=False),
        sa.Column("currency", sa.CHAR(3), nullable=False),
        sa.Column("min_interval_seconds", sa.BigInteger(), nullable=False),
        sa.Column("step_seconds", sa.BigInteger(), nullable=False),
        sa.Column("active_from", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("active_until", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "code", "version", name="uq_entitlement_tariff_definitions_code_version"
        ),
        sa.CheckConstraint("btrim(code) <> ''", name="code_nonempty"),
        sa.CheckConstraint("price_minor >= 0", name="price_nonnegative"),
        sa.CheckConstraint("min_interval_seconds > 0", name="min_interval_positive"),
        sa.CheckConstraint("step_seconds > 0", name="step_positive"),
        sa.CheckConstraint(
            "currency !~ '\\s' AND char_length(currency) = 3", name="currency_iso_length"
        ),
        sa.CheckConstraint(
            "active_until IS NULL OR active_until > active_from", name="active_interval"
        ),
        schema="mayak",
    )
    op.create_index(
        "ix_entitlement_tariff_definitions_code_active_from",
        "entitlement_tariff_definitions",
        ["code", "active_from"],
        schema="mayak",
    )
    op.create_table(
        "entitlement_access_grants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tariff_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_code", sa.String(64), nullable=False),
        sa.Column("valid_from", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("valid_until", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("state", sa.String(64), nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("row_version", sa.BigInteger(), nullable=False, server_default=sa.text("1")),
        sa.ForeignKeyConstraint(
            ["account_id"], ["mayak.identity_accounts.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["tariff_id"], ["mayak.entitlement_tariff_definitions.id"], ondelete="RESTRICT"
        ),
        sa.CheckConstraint("btrim(source_code) <> ''", name="source_code_nonempty"),
        sa.CheckConstraint("btrim(state) <> ''", name="state_nonempty"),
        sa.CheckConstraint("valid_until > valid_from", name="valid_interval"),
        sa.CheckConstraint("row_version > 0", name="row_version_positive"),
        schema="mayak",
    )
    op.create_index(
        "ix_entitlement_access_grants_account_valid_until",
        "entitlement_access_grants",
        ["account_id", "valid_until"],
        schema="mayak",
    )
    op.create_index(
        "ix_entitlement_access_grants_active",
        "entitlement_access_grants",
        ["account_id", "valid_from", "valid_until"],
        schema="mayak",
        postgresql_where=sa.text("state = 'ACTIVE'"),
    )
    op.create_table(
        "entitlement_usage_counters",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("counter_code", sa.String(64), nullable=False),
        sa.Column("window_start", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("window_end", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("consumed", sa.BigInteger(), nullable=False, server_default=sa.text("0")),
        sa.Column("limit_value", sa.BigInteger(), nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("row_version", sa.BigInteger(), nullable=False, server_default=sa.text("1")),
        sa.ForeignKeyConstraint(
            ["account_id"], ["mayak.identity_accounts.id"], ondelete="RESTRICT"
        ),
        sa.UniqueConstraint(
            "account_id",
            "counter_code",
            "window_start",
            name="uq_entitlement_usage_counters_account_code_window",
        ),
        sa.CheckConstraint("btrim(counter_code) <> ''", name="counter_code_nonempty"),
        sa.CheckConstraint("consumed >= 0", name="consumed_nonnegative"),
        sa.CheckConstraint("limit_value >= 0", name="limit_value_nonnegative"),
        sa.CheckConstraint("window_end > window_start", name="window_interval"),
        sa.CheckConstraint("row_version > 0", name="row_version_positive"),
        schema="mayak",
    )
    op.create_index(
        "ix_entitlement_usage_counters_account_code_window_end",
        "entitlement_usage_counters",
        ["account_id", "counter_code", "window_end"],
        schema="mayak",
    )
    op.create_table(
        "billing_payment_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider_code", sa.String(64), nullable=False),
        sa.Column("external_payment_id", sa.String(255), nullable=False),
        sa.Column("amount_minor", sa.BigInteger(), nullable=False),
        sa.Column("currency", sa.CHAR(3), nullable=False),
        sa.Column("state", sa.String(64), nullable=False),
        sa.Column("observed_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("safe_metadata", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("row_version", sa.BigInteger(), nullable=False, server_default=sa.text("1")),
        sa.ForeignKeyConstraint(
            ["account_id"], ["mayak.identity_accounts.id"], ondelete="RESTRICT"
        ),
        sa.UniqueConstraint(
            "provider_code",
            "external_payment_id",
            name="uq_billing_payment_records_provider_external_payment",
        ),
        sa.CheckConstraint("btrim(provider_code) <> ''", name="provider_code_nonempty"),
        sa.CheckConstraint("btrim(external_payment_id) <> ''", name="external_payment_id_nonempty"),
        sa.CheckConstraint("amount_minor >= 0", name="amount_nonnegative"),
        sa.CheckConstraint(
            "currency !~ '\\s' AND char_length(currency) = 3", name="currency_iso_length"
        ),
        sa.CheckConstraint("btrim(state) <> ''", name="state_nonempty"),
        sa.CheckConstraint("octet_length(safe_metadata::text) <= 8192", name="safe_metadata_size"),
        sa.CheckConstraint("row_version > 0", name="row_version_positive"),
        schema="mayak",
    )
    op.create_index(
        "ix_billing_payment_records_account_observed_at",
        "billing_payment_records",
        ["account_id", "observed_at"],
        schema="mayak",
    )
    op.create_index(
        "ix_billing_payment_records_pending_unknown",
        "billing_payment_records",
        ["state", "observed_at"],
        schema="mayak",
        postgresql_where=sa.text("state IN ('PENDING', 'UNKNOWN')"),
    )
    op.create_table(
        "billing_payment_operations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("payment_record_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("operation_code", sa.String(64), nullable=False),
        sa.Column("idempotency_key", sa.String(200), nullable=False),
        sa.Column("request_fingerprint", sa.CHAR(64), nullable=False),
        sa.Column("state", sa.String(64), nullable=False),
        sa.Column("attempt_count", sa.BigInteger(), nullable=False, server_default=sa.text("0")),
        sa.Column("next_due_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("row_version", sa.BigInteger(), nullable=False, server_default=sa.text("1")),
        sa.ForeignKeyConstraint(
            ["payment_record_id"], ["mayak.billing_payment_records.id"], ondelete="RESTRICT"
        ),
        sa.UniqueConstraint(
            "payment_record_id",
            "operation_code",
            "idempotency_key",
            name="uq_billing_payment_operations_payment_operation_idempotency",
        ),
        sa.CheckConstraint("btrim(operation_code) <> ''", name="operation_code_nonempty"),
        sa.CheckConstraint("btrim(idempotency_key) <> ''", name="idempotency_key_nonempty"),
        sa.CheckConstraint(
            "request_fingerprint ~ '^[0-9a-f]{64}$'", name="request_fingerprint_sha256"
        ),
        sa.CheckConstraint("btrim(state) <> ''", name="state_nonempty"),
        sa.CheckConstraint("attempt_count >= 0", name="attempt_count_nonnegative"),
        sa.CheckConstraint("row_version > 0", name="row_version_positive"),
        sa.CheckConstraint("state <> 'UNKNOWN' OR next_due_at IS NULL", name="unknown_without_due"),
        schema="mayak",
    )
    op.create_index(
        "ix_billing_payment_operations_due",
        "billing_payment_operations",
        ["next_due_at"],
        schema="mayak",
        postgresql_where=sa.text("state IN ('PENDING', 'RETRY')"),
    )
    op.create_table(
        "billing_reconciliations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("payment_record_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("operation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("state", sa.String(64), nullable=False),
        sa.Column("due_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("resolved_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("safe_metadata", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("row_version", sa.BigInteger(), nullable=False, server_default=sa.text("1")),
        sa.ForeignKeyConstraint(
            ["payment_record_id"], ["mayak.billing_payment_records.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["operation_id"], ["mayak.billing_payment_operations.id"], ondelete="RESTRICT"
        ),
        sa.UniqueConstraint(
            "payment_record_id",
            "operation_id",
            name="uq_billing_reconciliations_payment_operation",
            postgresql_nulls_not_distinct=True,
        ),
        sa.CheckConstraint("btrim(state) <> ''", name="state_nonempty"),
        sa.CheckConstraint("octet_length(safe_metadata::text) <= 8192", name="safe_metadata_size"),
        sa.CheckConstraint("resolved_at IS NULL OR resolved_at >= created_at", name="resolved_at"),
        sa.CheckConstraint("row_version > 0", name="row_version_positive"),
        schema="mayak",
    )
    op.create_index(
        "ix_billing_reconciliations_unresolved_due",
        "billing_reconciliations",
        ["due_at"],
        schema="mayak",
        postgresql_where=sa.text("resolved_at IS NULL"),
    )


def downgrade() -> None:
    raise RuntimeError("RF09_M03 is roll-forward only")
