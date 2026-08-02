"""RF-13 Beacon runtime preparation/provenance reconciliation.

The RF-09 projection required a current revision for every row.  Accepted
Module-04 preparation semantics require a DRAFT Beacon before the first clean
snapshot, so the projection must explicitly represent a null current revision.
The submitted URL is retained on the Beacon projection because preparation has
no revision row yet.
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "RF13_BEACON_RUNTIME"
down_revision = "RF12_BASIC_BEACON_LIMIT"
branch_labels = None
depends_on = None


def upgrade() -> None:
    connection = op.get_bind()
    op.add_column(
        "beacon_beacons",
        sa.Column("source_url", sa.String(4096), nullable=True),
        schema="mayak",
    )
    op.alter_column("beacon_beacons", "current_revision_no", schema="mayak", nullable=True)
    op.alter_column("beacon_beacons", "current_revision_id", schema="mayak", nullable=True)
    op.add_column(
        "beacon_configuration_revisions",
        sa.Column("revision_id", postgresql.UUID(as_uuid=True), nullable=True),
        schema="mayak",
    )
    op.add_column(
        "beacon_configuration_revisions",
        sa.Column("snapshot_id", sa.String(256), nullable=True),
        schema="mayak",
    )
    op.add_column(
        "beacon_configuration_revisions",
        sa.Column("parser_outcome_status", sa.String(64), nullable=True),
        schema="mayak",
    )
    op.add_column(
        "beacon_configuration_revisions",
        sa.Column("accepted_as_clean", sa.Boolean(), nullable=True),
        schema="mayak",
    )
    op.add_column(
        "beacon_configuration_revisions",
        sa.Column("parser_evidence_reference", sa.String(4096), nullable=True),
        schema="mayak",
    )
    op.add_column(
        "beacon_configuration_revisions",
        sa.Column("unsupported_parameters", postgresql.JSONB(), nullable=True),
        schema="mayak",
    )
    op.add_column(
        "beacon_configuration_revisions",
        sa.Column("warning_codes", postgresql.JSONB(), nullable=True),
        schema="mayak",
    )
    op.add_column(
        "beacon_filter_overrides",
        sa.Column("parser_evidence_reference", sa.String(4096), nullable=True),
        schema="mayak",
    )
    op.add_column(
        "beacon_filter_overrides",
        sa.Column("override_evidence_reference", sa.String(4096), nullable=True),
        schema="mayak",
    )
    connection.execute(sa.text(
        "UPDATE mayak.beacon_beacons b SET source_url = r.source_url "
        "FROM mayak.beacon_configuration_revisions r "
        "WHERE r.beacon_id = b.id AND r.revision_no = b.current_revision_no "
        "AND b.source_url IS NULL"
    ))
    connection.execute(sa.text(
        "UPDATE mayak.beacon_configuration_revisions "
        "SET revision_id = (md5(beacon_id::text || ':' || revision_no::text)::uuid), "
        "snapshot_id = 'legacy-rf09-' || beacon_id::text || '-' || revision_no::text, "
        "parser_outcome_status = 'CLEAN', accepted_as_clean = TRUE, "
        "parser_evidence_reference = 'legacy-rf09:' || beacon_id::text || ':' "
        "|| revision_no::text, "
        "unsupported_parameters = '[]'::jsonb, warning_codes = '[]'::jsonb"
    ))
    connection.execute(sa.text(
        "UPDATE mayak.beacon_beacons b SET current_revision_id = r.revision_id "
        "FROM mayak.beacon_configuration_revisions r "
        "WHERE r.beacon_id = b.id AND r.revision_no = b.current_revision_no"
    ))
    connection.execute(sa.text(
        "UPDATE mayak.beacon_filter_overrides o SET "
        "parser_evidence_reference = 'legacy-rf09:' || o.beacon_id::text || ':' "
        "|| o.revision_no::text, "
        "override_evidence_reference = 'legacy-rf09-override:' || o.id::text"
    ))
    for table, column in (
        ("beacon_configuration_revisions", "revision_id"),
        ("beacon_configuration_revisions", "snapshot_id"),
        ("beacon_configuration_revisions", "parser_outcome_status"),
        ("beacon_configuration_revisions", "accepted_as_clean"),
        ("beacon_configuration_revisions", "parser_evidence_reference"),
        ("beacon_configuration_revisions", "unsupported_parameters"),
        ("beacon_configuration_revisions", "warning_codes"),
        ("beacon_filter_overrides", "parser_evidence_reference"),
        ("beacon_filter_overrides", "override_evidence_reference"),
    ):
        op.alter_column(table, column, schema="mayak", nullable=False)
    op.create_unique_constraint(
        "uq_beacon_configuration_revisions_revision_id",
        "beacon_configuration_revisions",
        ["revision_id"],
        schema="mayak",
    )
    op.create_foreign_key(
        "fk_beacon_beacons_current_revision_id",
        "beacon_beacons",
        "beacon_configuration_revisions",
        ["current_revision_id"],
        ["revision_id"],
        source_schema="mayak",
        referent_schema="mayak",
        ondelete="RESTRICT",
    )
    op.execute(
        "ALTER TABLE mayak.beacon_beacons "
        "DROP CONSTRAINT IF EXISTS ck_beacon_beacons_revision_positive"
    )
    op.execute(
        "ALTER TABLE mayak.beacon_beacons "
        "DROP CONSTRAINT IF EXISTS revision_positive"
    )
    op.create_check_constraint(
        "ck_beacon_beacons_revision_positive",
        "beacon_beacons",
        "current_revision_no IS NULL OR current_revision_no > 0",
        schema="mayak",
    )
    op.create_check_constraint(
        "current_revision_pair",
        "beacon_beacons",
        "(current_revision_no IS NULL AND current_revision_id IS NULL) OR "
        "(current_revision_no IS NOT NULL AND current_revision_id IS NOT NULL)",
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
