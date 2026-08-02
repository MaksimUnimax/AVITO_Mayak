"""Persist the accepted Free/Basic active-Beacon tariff authority."""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "RF12_BASIC_BEACON_LIMIT"
down_revision = "RF12_RUNTIME_HARDEN"
branch_labels = None
depends_on = None


def upgrade() -> None:
    table = "entitlement_tariff_definitions"
    op.add_column(
        table,
        sa.Column("active_beacon_limit", sa.BigInteger(), nullable=True),
        schema="mayak",
    )

    connection = op.get_bind()
    unknown = connection.execute(
        sa.text(
            "SELECT code FROM mayak.entitlement_tariff_definitions "
            "WHERE code NOT IN ('FREE', 'BASIC') LIMIT 1"
        )
    ).scalar_one_or_none()
    if unknown is not None:
        raise RuntimeError(
            f"cannot backfill active_beacon_limit for unknown tariff code: {unknown}"
        )

    connection.execute(
        sa.text(
            "UPDATE mayak.entitlement_tariff_definitions SET active_beacon_limit = "
            "CASE code WHEN 'FREE' THEN 1 WHEN 'BASIC' THEN 5 END"
        )
    )
    op.alter_column(table, "active_beacon_limit", schema="mayak", nullable=False)
    op.create_check_constraint(
        "active_beacon_limit_positive",
        table,
        "active_beacon_limit > 0",
        schema="mayak",
    )


def downgrade() -> None:
    raise RuntimeError("RF12_BASIC_BEACON_LIMIT is roll-forward only")
