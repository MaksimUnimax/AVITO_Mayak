"""RF-09 Module 01 platform contracts schema.

Technical ID: RF-09-06-M01-PLATFORM-CONTRACTS-SCHEMA-BATCH-20260727
Implementation owner: Module 14 / RF-09
Domain owner: Module 01
Domain tables created: 3
Deferred FK count: 1
Status: roll-forward-only
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "RF09_M01"
down_revision = "RF09_BOOTSTRAP"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "platform_idempotency_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("scope", sa.Text(), nullable=False),
        sa.Column("idempotency_key", sa.String(200), nullable=False),
        sa.Column("request_fingerprint", sa.CHAR(64), nullable=False),
        sa.Column("result", postgresql.JSONB(), nullable=False),
        sa.Column("expires_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "scope", "idempotency_key", name="uq_platform_idempotency_records_scope_key"
        ),
        sa.CheckConstraint("btrim(scope) <> ''", name="scope_nonempty"),
        sa.CheckConstraint("btrim(idempotency_key) <> ''", name="key_nonempty"),
        sa.CheckConstraint("request_fingerprint ~ '^[0-9a-f]{64}$'", name="fingerprint"),
        sa.CheckConstraint("octet_length(result::text) <= 65536", name="result_size"),
        schema="mayak",
    )
    op.create_index(
        "ix_platform_idempotency_records_expires_at",
        "platform_idempotency_records",
        ["expires_at"],
        schema="mayak",
    )
    op.create_index(
        "ix_platform_idempotency_records_scope_key",
        "platform_idempotency_records",
        ["scope", "idempotency_key"],
        schema="mayak",
    )
    op.create_table(
        "platform_audit_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("actor_account_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action_code", sa.String(64), nullable=False),
        sa.Column("target_type", sa.String(128), nullable=False),
        sa.Column("target_id", sa.Text(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("correlation_id", sa.Text(), nullable=False),
        sa.Column("details", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.CheckConstraint("btrim(reason) <> ''", name="reason_nonempty"),
        sa.CheckConstraint("octet_length(details::text) <= 65536", name="details_size"),
        schema="mayak",
    )
    op.create_index(
        "ix_platform_audit_entries_created_at",
        "platform_audit_entries",
        ["created_at"],
        schema="mayak",
    )
    op.create_index(
        "ix_platform_audit_entries_correlation_id",
        "platform_audit_entries",
        ["correlation_id"],
        schema="mayak",
    )
    op.create_index(
        "ix_platform_audit_entries_actor_created_at",
        "platform_audit_entries",
        ["actor_account_id", "created_at"],
        schema="mayak",
    )
    op.create_table(
        "platform_event_outbox",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("event_fingerprint", sa.CHAR(64), nullable=False),
        sa.Column("contract_name", sa.String(128), nullable=False),
        sa.Column("contract_version", sa.String(32), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("state", sa.String(64), nullable=False),
        sa.Column("available_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("lease_started_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("lease_expires_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("lease_token", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("attempt_count", sa.BigInteger(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("row_version", sa.BigInteger(), nullable=False, server_default=sa.text("1")),
        sa.UniqueConstraint("event_fingerprint", name="uq_platform_event_outbox_event_fingerprint"),
        sa.CheckConstraint("event_fingerprint ~ '^[0-9a-f]{64}$'", name="fingerprint"),
        sa.CheckConstraint("octet_length(payload::text) <= 65536", name="payload_size"),
        sa.CheckConstraint("attempt_count >= 0", name="attempt_count"),
        sa.CheckConstraint("row_version > 0", name="row_version"),
        sa.CheckConstraint("btrim(state) <> ''", name="state_nonempty"),
        sa.CheckConstraint(
            "(lease_started_at IS NULL AND lease_expires_at IS NULL) "
            "OR lease_expires_at > lease_started_at",
            name="lease_window",
        ),
        schema="mayak",
    )
    op.create_index(
        "ix_platform_event_outbox_available",
        "platform_event_outbox",
        ["available_at", "id"],
        schema="mayak",
        postgresql_where=sa.text("state IN ('PENDING', 'RETRY')"),
    )
    op.create_index(
        "ix_platform_event_outbox_expired_lease",
        "platform_event_outbox",
        ["lease_expires_at"],
        schema="mayak",
        postgresql_where=sa.text("state = 'CLAIMED'"),
    )


def downgrade() -> None:
    raise RuntimeError("RF09_M01 is roll-forward only")
