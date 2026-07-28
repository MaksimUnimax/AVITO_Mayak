"""RF-09-14-M08: Module 08 Notification Delivery physical schema.

Technical ID: RF-09-14-M08-NOTIFICATION-DELIVERY-SCHEMA-BATCH-20260728
Domain owner: Module 08 Notification Delivery
Implementation owner: Module 14/RF-09
Tables: notification_endpoints, notification_events, notification_outbox,
notification_delivery_attempts, notification_delivery_reconciliations
Platform and Notification outboxes are distinct.
No new deferred foreign key. This migration is roll-forward-only.
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "RF09_M08"
down_revision = "RF09_M05"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "notification_endpoints",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider_code", sa.String(length=64), nullable=False),
        sa.Column("endpoint_ref", sa.String(length=255), nullable=False),
        sa.Column("state", sa.String(length=64), nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("row_version", sa.BigInteger(), server_default=sa.text("1"), nullable=False),
        sa.ForeignKeyConstraint(
            ["account_id"], ["mayak.identity_accounts.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "provider_code", "endpoint_ref", name="uq_notification_endpoints_provider_endpoint"
        ),
        sa.CheckConstraint("btrim(provider_code) <> ''", name="provider_code_nonempty"),
        sa.CheckConstraint("btrim(endpoint_ref) <> ''", name="endpoint_ref_nonempty"),
        sa.CheckConstraint("btrim(state) <> ''", name="state_nonempty"),
        sa.CheckConstraint("row_version > 0", name="row_version_positive"),
        schema="mayak",
    )
    op.create_table(
        "notification_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("beacon_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("source_effect_fingerprint", postgresql.CHAR(length=64), nullable=False),
        sa.Column("event_code", sa.String(length=64), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["account_id"], ["mayak.identity_accounts.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["beacon_id"], ["mayak.beacon_beacons.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["run_id"], ["mayak.scan_runs.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source_effect_fingerprint", name="uq_notification_events_source_effect_fingerprint"
        ),
        sa.CheckConstraint(
            "source_effect_fingerprint ~ '^[0-9a-f]{64}$'", name="source_effect_fingerprint_format"
        ),
        sa.CheckConstraint("btrim(event_code) <> ''", name="event_code_nonempty"),
        sa.CheckConstraint("octet_length(payload::text) <= 65536", name="payload_size"),
        schema="mayak",
    )
    op.create_table(
        "notification_outbox",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("endpoint_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("state", sa.String(length=64), nullable=False),
        sa.Column("available_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("lease_started_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("lease_expires_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("lease_token", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("attempt_count", sa.BigInteger(), server_default=sa.text("0"), nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("row_version", sa.BigInteger(), server_default=sa.text("1"), nullable=False),
        sa.ForeignKeyConstraint(
            ["event_id"], ["mayak.notification_events.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["endpoint_id"], ["mayak.notification_endpoints.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "event_id", "endpoint_id", name="uq_notification_outbox_event_endpoint"
        ),
        sa.CheckConstraint("attempt_count >= 0", name="attempt_nonnegative"),
        sa.CheckConstraint("btrim(state) <> ''", name="state_nonempty"),
        sa.CheckConstraint("row_version > 0", name="row_version_positive"),
        sa.CheckConstraint(
            "(lease_started_at IS NULL AND lease_expires_at IS NULL) OR "
            "lease_expires_at > lease_started_at",
            name="lease_window",
        ),
        schema="mayak",
    )
    op.create_table(
        "notification_delivery_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("outbox_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("attempt_number", sa.BigInteger(), nullable=False),
        sa.Column("state", sa.String(length=64), nullable=False),
        sa.Column("provider_reference", sa.String(length=255), nullable=True),
        sa.Column("effect_fingerprint", postgresql.CHAR(length=64), nullable=False),
        sa.Column("started_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("completed_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("safe_metadata", postgresql.JSONB(), nullable=False),
        sa.ForeignKeyConstraint(
            ["outbox_id"], ["mayak.notification_outbox.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "outbox_id", "attempt_number", name="uq_notification_delivery_attempts_outbox_attempt"
        ),
        sa.CheckConstraint("attempt_number >= 1", name="attempt_number_positive"),
        sa.CheckConstraint("btrim(state) <> ''", name="state_nonempty"),
        sa.CheckConstraint(
            "effect_fingerprint ~ '^[0-9a-f]{64}$'", name="effect_fingerprint_format"
        ),
        sa.CheckConstraint("octet_length(safe_metadata::text) <= 8192", name="safe_metadata_size"),
        sa.CheckConstraint(
            "completed_at IS NULL OR completed_at >= started_at", name="completion_order"
        ),
        schema="mayak",
    )
    op.create_table(
        "notification_delivery_reconciliations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("attempt_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("state", sa.String(length=64), nullable=False),
        sa.Column("due_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("resolved_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("safe_metadata", postgresql.JSONB(), nullable=False),
        sa.Column("row_version", sa.BigInteger(), server_default=sa.text("1"), nullable=False),
        sa.ForeignKeyConstraint(
            ["attempt_id"], ["mayak.notification_delivery_attempts.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "attempt_id", name="uq_notification_delivery_reconciliations_attempt_id"
        ),
        sa.CheckConstraint("btrim(state) <> ''", name="state_nonempty"),
        sa.CheckConstraint("octet_length(safe_metadata::text) <= 8192", name="safe_metadata_size"),
        sa.CheckConstraint("row_version > 0", name="row_version_positive"),
        schema="mayak",
    )
    op.create_index(
        "ix_notification_endpoints_account_state",
        "notification_endpoints",
        ["account_id", "state"],
        unique=False,
        schema="mayak",
    )
    op.create_index(
        "ix_notification_events_account_created_at",
        "notification_events",
        ["account_id", "created_at"],
        unique=False,
        schema="mayak",
    )
    op.create_index(
        "ix_notification_events_beacon_created_at",
        "notification_events",
        ["beacon_id", "created_at"],
        unique=False,
        schema="mayak",
    )
    op.create_index(
        "ix_notification_outbox_due",
        "notification_outbox",
        ["available_at", "id"],
        unique=False,
        schema="mayak",
        postgresql_where=sa.text("state IN ('PENDING', 'RETRY')"),
    )
    op.create_index(
        "ix_notification_outbox_claimed_expiry",
        "notification_outbox",
        ["lease_expires_at"],
        unique=False,
        schema="mayak",
        postgresql_where=sa.text("state = 'CLAIMED'"),
    )
    op.create_index(
        "ix_notification_delivery_attempts_outbox_started_at",
        "notification_delivery_attempts",
        ["outbox_id", "started_at"],
        unique=False,
        schema="mayak",
    )
    op.create_index(
        "ix_notification_delivery_reconciliations_unresolved_due",
        "notification_delivery_reconciliations",
        ["due_at"],
        unique=False,
        schema="mayak",
        postgresql_where=sa.text("resolved_at IS NULL"),
    )


def downgrade() -> None:
    raise RuntimeError("RF09_M08 is roll-forward only")
