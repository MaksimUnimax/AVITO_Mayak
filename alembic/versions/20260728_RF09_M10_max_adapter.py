"""RF-09-16-M10: Module 10 MAX Adapter physical schema.

Technical ID: RF-09-16-M10-MAX-ADAPTER-SCHEMA-BATCH-20260728
Domain owner: Module 10 MAX Adapter
Implementation owner: Module 14/RF-09
Tables: max_inbound_events, max_identity_mappings, max_delivery_mappings, max_miniapp_nonces
Identity remains account/provider-link authority; Notification remains generic delivery authority.
Provider acceptance is not human read. Production is webhook-first;
polling is development/test-only.
No new deferred FK. Roll-forward-only.
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "RF09_M10"
down_revision = "RF09_M09"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "max_inbound_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider_event_id", sa.String(length=255), nullable=False),
        sa.Column("event_fingerprint", postgresql.CHAR(length=64), nullable=False),
        sa.Column("schema_version", sa.String(length=32), nullable=False),
        sa.Column("normalized_data", postgresql.JSONB(), nullable=False),
        sa.Column("received_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "provider_event_id",
            "event_fingerprint",
            name="uq_max_inbound_events_provider_event_fingerprint",
        ),
        sa.CheckConstraint("btrim(provider_event_id) <> ''", name="provider_event_id_nonempty"),
        sa.CheckConstraint("event_fingerprint ~ '^[0-9a-f]{64}$'", name="event_fingerprint_format"),
        sa.CheckConstraint("btrim(schema_version) <> ''", name="schema_version_nonempty"),
        sa.CheckConstraint(
            "octet_length(normalized_data::text) <= 65536", name="normalized_data_size"
        ),
        schema="mayak",
    )
    op.create_table(
        "max_identity_mappings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider_link_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("max_user_ref", sa.String(length=255), nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("row_version", sa.BigInteger(), server_default=sa.text("1"), nullable=False),
        sa.ForeignKeyConstraint(
            ["provider_link_id"], ["mayak.identity_provider_links.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("max_user_ref", name="uq_max_identity_mappings_max_user_ref"),
        sa.UniqueConstraint("provider_link_id", name="uq_max_identity_mappings_provider_link_id"),
        sa.CheckConstraint("btrim(max_user_ref) <> ''", name="max_user_ref_nonempty"),
        sa.CheckConstraint("row_version > 0", name="row_version_positive"),
        schema="mayak",
    )
    op.create_table(
        "max_delivery_mappings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("attempt_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("max_message_ref", sa.String(length=255), nullable=True),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["attempt_id"], ["mayak.notification_delivery_attempts.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("attempt_id", name="uq_max_delivery_mappings_attempt_id"),
        sa.CheckConstraint(
            "max_message_ref IS NULL OR btrim(max_message_ref) <> ''",
            name="max_message_ref_nonempty_when_present",
        ),
        schema="mayak",
    )
    op.create_table(
        "max_miniapp_nonces",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("nonce_hash", postgresql.CHAR(length=64), nullable=False),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("expires_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("consumed_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("row_version", sa.BigInteger(), server_default=sa.text("1"), nullable=False),
        sa.ForeignKeyConstraint(
            ["account_id"], ["mayak.identity_accounts.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nonce_hash", name="uq_max_miniapp_nonces_nonce_hash"),
        sa.CheckConstraint("nonce_hash ~ '^[0-9a-f]{64}$'", name="nonce_hash_format"),
        sa.CheckConstraint("expires_at > created_at", name="expires_after_created"),
        sa.CheckConstraint("row_version > 0", name="row_version_positive"),
        schema="mayak",
    )
    op.create_index(
        "ix_max_inbound_events_provider_event_id",
        "max_inbound_events",
        ["provider_event_id"],
        unique=False,
        schema="mayak",
    )
    op.create_index(
        "ix_max_inbound_events_received_at",
        "max_inbound_events",
        ["received_at"],
        unique=False,
        schema="mayak",
    )
    op.create_index(
        "ix_max_identity_mappings_provider_link_id",
        "max_identity_mappings",
        ["provider_link_id"],
        unique=False,
        schema="mayak",
    )
    op.create_index(
        "ux_max_delivery_mappings_message_ref",
        "max_delivery_mappings",
        ["max_message_ref"],
        unique=True,
        schema="mayak",
        postgresql_where=sa.text("max_message_ref IS NOT NULL"),
    )
    op.create_index(
        "ix_max_miniapp_nonces_expires_at",
        "max_miniapp_nonces",
        ["expires_at"],
        unique=False,
        schema="mayak",
        postgresql_where=sa.text("consumed_at IS NULL"),
    )


def downgrade() -> None:
    raise RuntimeError("RF09_M10 is roll-forward only")
