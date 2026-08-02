"""RF-13 Beacon runtime preparation/provenance reconciliation.

The RF-09 projection required a current revision for every row.  Accepted
Module-04 preparation semantics require a DRAFT Beacon before the first clean
snapshot, so the projection must explicitly represent a null current revision.
The submitted URL is retained on the Beacon projection because preparation has
no revision row yet.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "RF13_BEACON_RUNTIME"
down_revision = "RF12_BASIC_BEACON_LIMIT"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "beacon_beacons",
        sa.Column("source_url", sa.String(4096), nullable=True),
        schema="mayak",
    )
    op.alter_column("beacon_beacons", "current_revision_no", schema="mayak", nullable=True)
    op.alter_column("beacon_beacons", "current_revision_id", schema="mayak", nullable=True)
    op.drop_constraint("ck_beacon_beacons_revision_positive", "beacon_beacons", schema="mayak")
    op.create_check_constraint(
        "revision_positive",
        "beacon_beacons",
        "current_revision_no IS NULL OR current_revision_no > 0",
        schema="mayak",
    )
    op.create_check_constraint(
        "source_url_nonempty",
        "beacon_beacons",
        "source_url IS NULL OR btrim(source_url) <> ''",
        schema="mayak",
    )


def downgrade() -> None:
    raise RuntimeError("RF13_BEACON_RUNTIME is roll-forward only")
