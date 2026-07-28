"""RF-09-13-M05: Module 05 Avito Parser Adapter outcome evidence.

Technical ID: RF-09-13-M05-AVITO-PARSER-SCHEMA-BATCH-20260728
Domain owner: Module 05 Avito Parser Adapter
Implementation owner: Module 14/RF-09
Table: mayak.parser_outcomes
The reverse Scan FK remains deferred to RF09_FINALIZE.
This migration is roll-forward-only.
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "RF09_M05"
down_revision = "RF09_M06"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "parser_outcomes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("beacon_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("route_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("outcome_code", sa.String(length=64), nullable=False),
        sa.Column("listing_snapshot", postgresql.JSONB(), nullable=True),
        sa.Column("observed_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("fingerprint", postgresql.CHAR(length=64), nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["beacon_id"], ["mayak.beacon_beacons.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["run_id"], ["mayak.scan_runs.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["route_id"], ["mayak.egress_routes.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "run_id",
            "fingerprint",
            name="uq_parser_outcomes_run_fingerprint",
            postgresql_nulls_not_distinct=True,
        ),
        sa.CheckConstraint("btrim(outcome_code) <> ''", name="outcome_code_nonempty"),
        sa.CheckConstraint(
            "listing_snapshot IS NULL OR octet_length(listing_snapshot::text) <= 32768",
            name="listing_snapshot_size",
        ),
        sa.CheckConstraint("fingerprint ~ '^[0-9a-f]{64}$'", name="fingerprint_sha256"),
        schema="mayak",
    )
    op.create_index(
        "ix_parser_outcomes_beacon_observed_at",
        "parser_outcomes",
        ["beacon_id", "observed_at"],
        unique=False,
        schema="mayak",
    )
    op.create_index(
        "ix_parser_outcomes_outcome_code_observed_at",
        "parser_outcomes",
        ["outcome_code", "observed_at"],
        unique=False,
        schema="mayak",
    )


def downgrade() -> None:
    raise RuntimeError("RF09_M05 is roll-forward only")
