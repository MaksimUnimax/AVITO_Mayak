"""RF-09 Module 04 Beacon Management schema batch.

Technical ID: RF-09-10-M04-BEACON-MANAGEMENT-SCHEMA-BATCH-20260728
Implementation owner: Module 14 / RF-09
Domain owner: Module 04
Domain tables created: 4
Deferred FK count: 1
Roll-forward-only.
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "RF09_M04"
down_revision = "RF09_M13"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "beacon_beacons",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("current_revision_no", sa.BigInteger(), nullable=False),
        sa.Column("current_revision_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("state", sa.String(64), nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("row_version", sa.BigInteger(), nullable=False, server_default=sa.text("1")),
        sa.ForeignKeyConstraint(
            ["account_id"], ["mayak.identity_accounts.id"], ondelete="RESTRICT"
        ),
        sa.UniqueConstraint(
            "id", "current_revision_no", name="uq_beacon_beacons_id_current_revision"
        ),
        sa.CheckConstraint("btrim(name) <> ''", name="name_nonempty"),
        sa.CheckConstraint("current_revision_no > 0", name="revision_positive"),
        sa.CheckConstraint("btrim(state) <> ''", name="state_nonempty"),
        sa.CheckConstraint("row_version > 0", name="row_version_positive"),
        schema="mayak",
    )
    op.create_index(
        "ix_beacon_beacons_account_state", "beacon_beacons", ["account_id", "state"], schema="mayak"
    )

    op.create_table(
        "beacon_configuration_revisions",
        sa.Column("beacon_id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("revision_no", sa.BigInteger(), primary_key=True, nullable=False),
        sa.Column("source_url", sa.String(4096), nullable=False),
        sa.Column("filter_candidate", postgresql.JSONB(), nullable=True),
        sa.Column("accepted_filter", postgresql.JSONB(), nullable=False),
        sa.Column("created_by_account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("catalog_version_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["beacon_id"], ["mayak.beacon_beacons.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["created_by_account_id"], ["mayak.identity_accounts.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["catalog_version_id"], ["mayak.filter_catalog_versions.id"], ondelete="RESTRICT"
        ),
        sa.CheckConstraint("revision_no > 0", name="revision_positive"),
        sa.CheckConstraint("btrim(source_url) <> ''", name="source_url_nonempty"),
        sa.CheckConstraint(
            "filter_candidate IS NULL OR octet_length(filter_candidate::text) <= 65536",
            name="filter_candidate_size",
        ),
        sa.CheckConstraint(
            "octet_length(accepted_filter::text) <= 65536", name="accepted_filter_size"
        ),
        schema="mayak",
    )
    op.create_index(
        "ix_beacon_configuration_revisions_beacon_created_at",
        "beacon_configuration_revisions",
        ["beacon_id", "created_at"],
        schema="mayak",
    )

    op.create_table(
        "beacon_filter_overrides",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("beacon_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("revision_no", sa.BigInteger(), nullable=False),
        sa.Column("field_code", sa.String(128), nullable=False),
        sa.Column("value", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("row_version", sa.BigInteger(), nullable=False, server_default=sa.text("1")),
        sa.ForeignKeyConstraint(
            ["beacon_id", "revision_no"],
            [
                "mayak.beacon_configuration_revisions.beacon_id",
                "mayak.beacon_configuration_revisions.revision_no",
            ],
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint(
            "beacon_id",
            "revision_no",
            "field_code",
            name="uq_beacon_filter_overrides_beacon_revision_field",
        ),
        sa.CheckConstraint("revision_no > 0", name="revision_positive"),
        sa.CheckConstraint("btrim(field_code) <> ''", name="field_code_nonempty"),
        sa.CheckConstraint("octet_length(value::text) <= 65536", name="value_size"),
        sa.CheckConstraint("row_version > 0", name="row_version_positive"),
        schema="mayak",
    )
    op.create_index(
        "ix_beacon_filter_overrides_beacon_field",
        "beacon_filter_overrides",
        ["beacon_id", "field_code"],
        schema="mayak",
    )

    op.create_table(
        "beacon_lifecycle_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("beacon_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("from_state", sa.String(64), nullable=True),
        sa.Column("to_state", sa.String(64), nullable=False),
        sa.Column("actor_account_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["beacon_id"], ["mayak.beacon_beacons.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["actor_account_id"], ["mayak.identity_accounts.id"], ondelete="RESTRICT"
        ),
        sa.CheckConstraint(
            "from_state IS NULL OR btrim(from_state) <> ''", name="from_state_nonempty"
        ),
        sa.CheckConstraint("btrim(to_state) <> ''", name="to_state_nonempty"),
        sa.CheckConstraint("btrim(reason) <> ''", name="reason_nonempty"),
        schema="mayak",
    )
    op.create_index(
        "ix_beacon_lifecycle_events_beacon_created_at",
        "beacon_lifecycle_events",
        ["beacon_id", "created_at"],
        schema="mayak",
    )


def downgrade() -> None:
    raise RuntimeError("RF09_M04 is roll-forward only")
