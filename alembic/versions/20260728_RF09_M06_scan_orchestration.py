"""RF-09 Module 06 Scan Orchestration schema batch.

Parent Technical ID: RF-09-12-M06-SCAN-ORCHESTRATION-SCHEMA-BATCH-20260728
Corrective Technical ID: RF-09-12-M06-CORRECTIVE-01-STALE-EGRESS-GLOBAL-METADATA-ASSERTIONS-20260728
Domain owner: Module 06 Scan Orchestration & Listing State
Implementation owner: Module 14/RF-09
Domain tables created: six Scan tables.
Deferred parser FK: 1; roll-forward-only.
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "RF09_M06"
down_revision = "RF09_M07"
branch_labels = None
depends_on = None
S = "mayak"


def U(*c: str, name: str) -> sa.UniqueConstraint:
    return sa.UniqueConstraint(*c, name=name)


def F(*c: str, ref: list[str]) -> sa.ForeignKeyConstraint:
    return sa.ForeignKeyConstraint(c, ref, ondelete="RESTRICT")


def upgrade() -> None:
    op.create_table(
        "scan_schedules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("beacon_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("interval_seconds", sa.BigInteger, nullable=False),
        sa.Column("next_due_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("state", sa.String(64), nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("row_version", sa.BigInteger, nullable=False, server_default=sa.text("1")),
        F("beacon_id", ref=["mayak.beacon_beacons.id"]),
        U("beacon_id", name="uq_scan_schedules_beacon_id"),
        sa.CheckConstraint("interval_seconds > 0", name="interval_positive"),
        sa.CheckConstraint("btrim(state) <> ''", name="state_nonempty"),
        sa.CheckConstraint("row_version > 0", name="row_version_positive"),
        schema=S,
    )
    op.create_index(
        "ix_scan_schedules_active_due",
        "scan_schedules",
        ("next_due_at", "id"),
        postgresql_where=sa.text("state = 'ACTIVE'"),
        schema=S,
    )
    op.create_table(
        "scan_work_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("schedule_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("beacon_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("due_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("state", sa.String(64), nullable=False),
        sa.Column("lease_started_at", postgresql.TIMESTAMP(timezone=True)),
        sa.Column("lease_expires_at", postgresql.TIMESTAMP(timezone=True)),
        sa.Column("lease_token", postgresql.UUID(as_uuid=True)),
        sa.Column("attempt_count", sa.BigInteger, nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("row_version", sa.BigInteger, nullable=False, server_default=sa.text("1")),
        F("schedule_id", ref=["mayak.scan_schedules.id"]),
        F("beacon_id", ref=["mayak.beacon_beacons.id"]),
        U("schedule_id", "due_at", name="uq_scan_work_items_schedule_due_at"),
        sa.CheckConstraint("attempt_count >= 0", name="attempt_nonnegative"),
        sa.CheckConstraint("btrim(state) <> ''", name="state_nonempty"),
        sa.CheckConstraint("row_version > 0", name="row_version_positive"),
        sa.CheckConstraint(
            "(lease_started_at IS NULL AND lease_expires_at IS NULL) OR "
            "lease_expires_at > lease_started_at",
            name="lease_window",
        ),
        schema=S,
    )
    op.create_index(
        "ix_scan_work_items_due",
        "scan_work_items",
        ("due_at", "id"),
        postgresql_where=sa.text("state IN ('DUE', 'RETRY')"),
        schema=S,
    )
    op.create_index(
        "ix_scan_work_items_claimed_expiry",
        "scan_work_items",
        ("lease_expires_at",),
        postgresql_where=sa.text("state = 'CLAIMED'"),
        schema=S,
    )
    op.create_table(
        "scan_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("work_item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("beacon_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("revision_no", sa.BigInteger, nullable=False),
        sa.Column("parser_outcome_id", postgresql.UUID(as_uuid=True)),
        sa.Column("route_id", postgresql.UUID(as_uuid=True)),
        sa.Column("state", sa.String(64), nullable=False),
        sa.Column("started_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("completed_at", postgresql.TIMESTAMP(timezone=True)),
        sa.Column("row_version", sa.BigInteger, nullable=False, server_default=sa.text("1")),
        F("work_item_id", ref=["mayak.scan_work_items.id"]),
        F("beacon_id", ref=["mayak.beacon_beacons.id"]),
        sa.ForeignKeyConstraint(
            ["beacon_id", "revision_no"],
            [
                "mayak.beacon_configuration_revisions.beacon_id",
                "mayak.beacon_configuration_revisions.revision_no",
            ],
            ondelete="RESTRICT",
        ),
        F("route_id", ref=["mayak.egress_routes.id"]),
        U("work_item_id", name="uq_scan_runs_work_item_id"),
        sa.CheckConstraint("revision_no > 0", name="revision_positive"),
        sa.CheckConstraint("btrim(state) <> ''", name="state_nonempty"),
        sa.CheckConstraint(
            "completed_at IS NULL OR completed_at >= started_at", name="completion_order"
        ),
        sa.CheckConstraint("row_version > 0", name="row_version_positive"),
        schema=S,
    )
    op.create_index(
        "ix_scan_runs_beacon_started_at", "scan_runs", ("beacon_id", "started_at"), schema=S
    )
    op.create_index(
        "ix_scan_runs_active_states",
        "scan_runs",
        ("state", "started_at"),
        postgresql_where=sa.text("state IN ('RUNNING', 'PENDING_RECONCILIATION')"),
        schema=S,
    )
    op.create_table(
        "scan_listing_observations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("beacon_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("external_listing_key", sa.String(255), nullable=False),
        sa.Column("snapshot", postgresql.JSONB, nullable=False),
        sa.Column("observed_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("fingerprint", postgresql.CHAR(64), nullable=False),
        F("run_id", ref=["mayak.scan_runs.id"]),
        F("beacon_id", ref=["mayak.beacon_beacons.id"]),
        U("run_id", "external_listing_key", name="uq_scan_listing_observations_run_external_key"),
        sa.CheckConstraint("btrim(external_listing_key) <> ''", name="external_key_nonempty"),
        sa.CheckConstraint("octet_length(snapshot::text) <= 32768", name="snapshot_size"),
        sa.CheckConstraint("fingerprint ~ '^[0-9a-f]{64}$'", name="fingerprint_format"),
        schema=S,
    )
    op.create_index(
        "ix_scan_listing_observations_beacon_observed_at",
        "scan_listing_observations",
        ("beacon_id", "observed_at"),
        schema=S,
    )
    op.create_table(
        "scan_beacon_listing_state",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("beacon_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("external_listing_key", sa.String(255), nullable=False),
        sa.Column("last_seen_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("last_snapshot", postgresql.JSONB, nullable=False),
        sa.Column("first_seen_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("row_version", sa.BigInteger, nullable=False, server_default=sa.text("1")),
        sa.Column("updated_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        F("beacon_id", ref=["mayak.beacon_beacons.id"]),
        U(
            "beacon_id",
            "external_listing_key",
            name="uq_scan_beacon_listing_state_beacon_external_key",
        ),
        sa.CheckConstraint("btrim(external_listing_key) <> ''", name="external_key_nonempty"),
        sa.CheckConstraint("octet_length(last_snapshot::text) <= 32768", name="snapshot_size"),
        sa.CheckConstraint("row_version > 0", name="row_version_positive"),
        schema=S,
    )
    op.create_index(
        "ix_scan_beacon_listing_state_beacon_last_seen_at",
        "scan_beacon_listing_state",
        ("beacon_id", "last_seen_at"),
        schema=S,
    )
    op.create_table(
        "scan_anchors",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("beacon_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("anchor_key", sa.String(255), nullable=False),
        sa.Column("corrected_by_account_id", postgresql.UUID(as_uuid=True)),
        sa.Column("correction_reason", sa.Text, nullable=True),
        sa.Column("updated_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("row_version", sa.BigInteger, nullable=False, server_default=sa.text("1")),
        F("beacon_id", ref=["mayak.beacon_beacons.id"]),
        F("corrected_by_account_id", ref=["mayak.identity_accounts.id"]),
        U("beacon_id", name="uq_scan_anchors_beacon_id"),
        sa.CheckConstraint("btrim(anchor_key) <> ''", name="anchor_nonempty"),
        sa.CheckConstraint("row_version > 0", name="row_version_positive"),
        sa.CheckConstraint(
            "(corrected_by_account_id IS NULL AND correction_reason IS NULL) OR "
            "(corrected_by_account_id IS NOT NULL AND correction_reason IS NOT NULL "
            "AND btrim(correction_reason) <> '')",
            name="correction_pair",
        ),
        schema=S,
    )
    op.create_index(
        "ix_scan_anchors_beacon_updated_at", "scan_anchors", ("beacon_id", "updated_at"), schema=S
    )


def downgrade() -> None:
    raise RuntimeError("RF09_M06 is roll-forward only")
