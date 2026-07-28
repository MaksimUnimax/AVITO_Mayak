"""RF-09-18-CORRECTIVE-01-FINALIZE-ALL-DEFERRED-CONSTRAINTS-AND-ZERO-TO-HEAD-20260728.

Parent Technical ID: RF-09-18-FINALIZE-DEFERRED-CONSTRAINTS-AND-ZERO-TO-HEAD-PROOF-20260728
Implementation owner: Module 14/RF-09
Domain tables created: 0
Indexes created: 0
Deferred constraints finalized: 3
Module 12 no-table boundary preserved
All domain ownership preserved
Roll-forward-only.
"""

import sqlalchemy as sa

from alembic import op

revision = "RF09_FINALIZE"
down_revision = "RF09_M11"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_foreign_key(
        "fk_beacon_beacons_id_beacon_configuration_revisions",
        "beacon_beacons",
        "beacon_configuration_revisions",
        ["id", "current_revision_no"],
        ["beacon_id", "revision_no"],
        source_schema="mayak",
        referent_schema="mayak",
        ondelete="RESTRICT",
        postgresql_not_valid=True,
    )
    op.create_foreign_key(
        "fk_scan_runs_parser_outcome_id_parser_outcomes",
        "scan_runs",
        "parser_outcomes",
        ["parser_outcome_id"],
        ["id"],
        source_schema="mayak",
        referent_schema="mayak",
        ondelete="RESTRICT",
        postgresql_not_valid=True,
    )
    op.create_foreign_key(
        "fk_egress_route_leases_work_item_id_scan_work_items",
        "egress_route_leases",
        "scan_work_items",
        ["work_item_id"],
        ["id"],
        source_schema="mayak",
        referent_schema="mayak",
        ondelete="RESTRICT",
        postgresql_not_valid=True,
    )
    op.execute(
        sa.text(
            "ALTER TABLE mayak.beacon_beacons VALIDATE CONSTRAINT "
            "fk_beacon_beacons_id_beacon_configuration_revisions"
        )
    )
    op.execute(
        sa.text(
            "ALTER TABLE mayak.scan_runs VALIDATE CONSTRAINT "
            "fk_scan_runs_parser_outcome_id_parser_outcomes"
        )
    )
    op.execute(
        sa.text(
            "ALTER TABLE mayak.egress_route_leases VALIDATE CONSTRAINT "
            "fk_egress_route_leases_work_item_id_scan_work_items"
        )
    )


def downgrade() -> None:
    raise RuntimeError("RF09_FINALIZE is roll-forward only")
