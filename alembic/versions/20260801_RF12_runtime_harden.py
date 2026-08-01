"""RF-12 corrective hardening for grant semantics.

This is deliberately additive.  The published RF12_MANUAL_GRANT revision is
historical and its destructive downgrade must never be reached from the
current head.
"""

import sqlalchemy as sa

from alembic import op

revision = "RF12_RUNTIME_HARDEN"
down_revision = "RF12_MANUAL_GRANT"
branch_labels = None
depends_on = None


def upgrade() -> None:
    table = "entitlement_access_grants"
    # Existing RF12 rows are tariff grants.  Make that one-time backfill
    # explicit before removing the historical semantic defaults.
    op.execute(
        sa.text(
            "UPDATE mayak.entitlement_access_grants "
            "SET grant_kind = 'TARIFF' WHERE grant_kind IS NULL"
        )
    )
    op.execute(
        sa.text(
            "UPDATE mayak.entitlement_access_grants "
            "SET reason = 'legacy grant' WHERE reason IS NULL OR btrim(reason) = ''"
        )
    )
    op.alter_column(table, "grant_kind", schema="mayak", server_default=None)
    op.alter_column(table, "reason", schema="mayak", server_default=None)

    for name in (
        "grant_kind_allowed",
        "tariff_grant_fields_empty",
        "manual_grant_fields_present",
        "reason_nonempty",
    ):
        op.drop_constraint(name, table, schema="mayak", type_="check")

    op.create_check_constraint(
        "grant_kind_allowed", table,
        "grant_kind IN ('TARIFF', 'MANUAL')", schema="mayak",
    )
    op.create_check_constraint(
        "tariff_grant_fields_empty", table,
        "grant_kind <> 'TARIFF' OR (tariff_id IS NOT NULL AND "
        "granted_capability IS NULL AND granted_scope IS NULL)",
        schema="mayak",
    )
    op.create_check_constraint(
        "manual_grant_fields_present", table,
        "grant_kind <> 'MANUAL' OR (tariff_id IS NULL AND "
        "granted_capability IS NOT NULL AND btrim(granted_capability) <> '' AND "
        "granted_scope IS NOT NULL AND btrim(granted_scope) <> '')",
        schema="mayak",
    )
    op.create_check_constraint(
        "reason_nonempty", table,
        "reason IS NOT NULL AND btrim(reason) <> '' AND octet_length(reason) <= 512",
        schema="mayak",
    )
    # The published revision created this index but omitted it from metadata;
    # retain it and make the canonical registration exact.


def downgrade() -> None:
    raise RuntimeError("RF12_RUNTIME_HARDEN is roll-forward only")
