"""RF-09-15-M09: Module 09 Telegram Adapter physical schema.

Technical ID: RF-09-15-M09-TELEGRAM-ADAPTER-SCHEMA-BATCH-20260728
Domain owner: Module 09 Telegram Adapter
Implementation owner: Module 14/RF-09
Tables: telegram_inbound_updates, telegram_identity_mappings, telegram_delivery_mappings
Identity remains account/link authority; Notification remains generic delivery authority.
Provider acceptance is not human read. No new deferred FK. Roll-forward-only.
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "RF09_M09"
down_revision = "RF09_M08"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "telegram_inbound_updates",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider_update_id", sa.String(length=255), nullable=False),
        sa.Column("event_fingerprint", postgresql.CHAR(length=64), nullable=False),
        sa.Column("schema_version", sa.String(length=32), nullable=False),
        sa.Column("normalized_data", postgresql.JSONB(), nullable=False),
        sa.Column("received_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "provider_update_id",
            "event_fingerprint",
            name="uq_telegram_inbound_updates_provider_update_fingerprint",
        ),
        sa.CheckConstraint("btrim(provider_update_id) <> ''", name="provider_update_id_nonempty"),
        sa.CheckConstraint("event_fingerprint ~ '^[0-9a-f]{64}$'", name="event_fingerprint_format"),
        sa.CheckConstraint("btrim(schema_version) <> ''", name="schema_version_nonempty"),
        sa.CheckConstraint(
            "octet_length(normalized_data::text) <= 65536", name="normalized_data_size"
        ),
        schema="mayak",
    )
    op.create_table(
        "telegram_identity_mappings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider_link_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("telegram_user_ref", sa.String(length=255), nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("row_version", sa.BigInteger(), server_default=sa.text("1"), nullable=False),
        sa.ForeignKeyConstraint(
            ["provider_link_id"], ["mayak.identity_provider_links.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "telegram_user_ref", name="uq_telegram_identity_mappings_telegram_user_ref"
        ),
        sa.UniqueConstraint(
            "provider_link_id", name="uq_telegram_identity_mappings_provider_link_id"
        ),
        sa.CheckConstraint("btrim(telegram_user_ref) <> ''", name="telegram_user_ref_nonempty"),
        sa.CheckConstraint("row_version > 0", name="row_version_positive"),
        schema="mayak",
    )
    op.create_table(
        "telegram_delivery_mappings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("attempt_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("telegram_message_ref", sa.String(length=255), nullable=True),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["attempt_id"], ["mayak.notification_delivery_attempts.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("attempt_id", name="uq_telegram_delivery_mappings_attempt_id"),
        sa.CheckConstraint(
            "telegram_message_ref IS NULL OR btrim(telegram_message_ref) <> ''",
            name="telegram_message_ref_nonempty_when_present",
        ),
        schema="mayak",
    )
    op.create_index(
        "ix_telegram_inbound_updates_provider_update_id",
        "telegram_inbound_updates",
        ["provider_update_id"],
        unique=False,
        schema="mayak",
    )
    op.create_index(
        "ix_telegram_inbound_updates_received_at",
        "telegram_inbound_updates",
        ["received_at"],
        unique=False,
        schema="mayak",
    )
    op.create_index(
        "ix_telegram_identity_mappings_provider_link_id",
        "telegram_identity_mappings",
        ["provider_link_id"],
        unique=False,
        schema="mayak",
    )
    op.create_index(
        "ux_telegram_delivery_mappings_message_ref",
        "telegram_delivery_mappings",
        ["telegram_message_ref"],
        unique=True,
        schema="mayak",
        postgresql_where=sa.text("telegram_message_ref IS NOT NULL"),
    )


def downgrade() -> None:
    raise RuntimeError("RF09_M09 is roll-forward only")
