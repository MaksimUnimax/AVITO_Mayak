"""RF-13 additive lifecycle system-causation hardening."""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "RF13_BEACON_RUNTIME_HARDEN"
down_revision = "RF13_BEACON_RUNTIME"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "beacon_lifecycle_events",
        sa.Column("system_actor_class", sa.String(128), nullable=True),
        schema="mayak",
    )
    op.add_column(
        "beacon_lifecycle_events",
        sa.Column("causation_reference", sa.String(512), nullable=True),
        schema="mayak",
    )
    op.add_column(
        "beacon_lifecycle_events",
        sa.Column("policy_source_reference", sa.String(512), nullable=True),
        schema="mayak",
    )
    op.create_check_constraint(
        "ck_beacon_lifecycle_events_actor_causation_pair",
        "beacon_lifecycle_events",
        "(actor_account_id IS NOT NULL AND system_actor_class IS NULL "
        "AND causation_reference IS NULL AND policy_source_reference IS NULL) OR "
        "(actor_account_id IS NULL AND system_actor_class IS NOT NULL "
        "AND causation_reference IS NOT NULL AND policy_source_reference IS NOT NULL)",
        schema="mayak",
    )


def downgrade() -> None:
    raise RuntimeError("RF13_BEACON_RUNTIME_HARDEN is roll-forward only")
