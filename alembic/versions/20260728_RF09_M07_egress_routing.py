"""RF-09 Module 07 Egress Routing schema batch.

Technical ID: RF-09-11-M07-EGRESS-ROUTING-SCHEMA-BATCH-20260728
Implementation owner: Module 14/RF-09
Domain owner: Module 07
Domain tables created: 4
Deferred FK count: 1
Roll-forward-only.
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "RF09_M07"
down_revision = "RF09_M04"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "egress_agents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("agent_code", sa.String(128), nullable=False),
        sa.Column("credential_fingerprint", sa.CHAR(64), nullable=True),
        sa.Column("state", sa.String(64), nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("row_version", sa.BigInteger(), nullable=False, server_default=sa.text("1")),
        sa.UniqueConstraint("agent_code", name="uq_egress_agents_agent_code"),
        sa.CheckConstraint("btrim(agent_code) <> ''", name="agent_code_nonempty"),
        sa.CheckConstraint(
            "credential_fingerprint IS NULL OR credential_fingerprint ~ '^[0-9a-f]{64}$'",
            name="credential_fingerprint",
        ),
        sa.CheckConstraint("btrim(state) <> ''", name="state_nonempty"),
        sa.CheckConstraint("row_version > 0", name="row_version_positive"),
        schema="mayak",
    )
    op.create_index(
        "ix_egress_agents_state_agent_code",
        "egress_agents",
        ["state", "agent_code"],
        schema="mayak",
    )
    op.create_table(
        "egress_routes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("route_code", sa.String(128), nullable=False),
        sa.Column("endpoint_ref", sa.String(255), nullable=False),
        sa.Column("state", sa.String(64), nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("row_version", sa.BigInteger(), nullable=False, server_default=sa.text("1")),
        sa.ForeignKeyConstraint(["agent_id"], ["mayak.egress_agents.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("agent_id", "route_code", name="uq_egress_routes_agent_route_code"),
        sa.CheckConstraint("btrim(route_code) <> ''", name="route_code_nonempty"),
        sa.CheckConstraint("btrim(endpoint_ref) <> ''", name="endpoint_ref_nonempty"),
        sa.CheckConstraint("btrim(state) <> ''", name="state_nonempty"),
        sa.CheckConstraint("row_version > 0", name="row_version_positive"),
        schema="mayak",
    )
    op.create_index(
        "ix_egress_routes_state_agent", "egress_routes", ["state", "agent_id"], schema="mayak"
    )
    op.create_table(
        "egress_agent_heartbeats",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("observed_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("state", sa.String(64), nullable=False),
        sa.Column("safe_metadata", postgresql.JSONB(), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["mayak.egress_agents.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("btrim(state) <> ''", name="state_nonempty"),
        sa.CheckConstraint("octet_length(safe_metadata::text) <= 8192", name="safe_metadata_size"),
        schema="mayak",
    )
    op.create_index(
        "ix_egress_agent_heartbeats_agent_observed_at",
        "egress_agent_heartbeats",
        ["agent_id", "observed_at"],
        schema="mayak",
    )
    op.create_table(
        "egress_route_leases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("route_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("work_item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("lease_token", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("lease_started_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("lease_expires_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("state", sa.String(64), nullable=False),
        sa.ForeignKeyConstraint(["route_id"], ["mayak.egress_routes.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("lease_token", name="uq_egress_route_leases_lease_token"),
        sa.CheckConstraint("lease_expires_at > lease_started_at", name="lease_window"),
        sa.CheckConstraint("btrim(state) <> ''", name="state_nonempty"),
        schema="mayak",
    )
    op.create_index(
        "uq_egress_route_leases_active_route_work_item",
        "egress_route_leases",
        ["route_id", "work_item_id"],
        unique=True,
        schema="mayak",
        postgresql_where=sa.text("state = 'ACTIVE'"),
    )
    op.create_index(
        "ix_egress_route_leases_active_expires_at",
        "egress_route_leases",
        ["lease_expires_at"],
        schema="mayak",
        postgresql_where=sa.text("state = 'ACTIVE'"),
    )


def downgrade() -> None:
    raise RuntimeError("RF09_M07 is roll-forward only")
