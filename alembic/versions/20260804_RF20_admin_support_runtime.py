"""RF20: align the support active-case index with accepted runtime states."""

import sqlalchemy as sa

from alembic import op

revision = "RF20_ADMIN_SUPPORT_RUNTIME"
down_revision = "RF13_BEACON_RUNTIME_HARDEN"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index(
        "ix_support_cases_open_pending_updated_at", table_name="support_cases", schema="mayak"
    )
    op.create_index(
        "ix_support_cases_open_pending_updated_at",
        "support_cases",
        ["state", "updated_at"],
        unique=False,
        schema="mayak",
        postgresql_where=sa.text(
            "state IN ('OPEN', 'IN_PROGRESS', 'WAITING_FOR_EVIDENCE', 'ESCALATED', 'AMBIGUOUS')"
        ),
    )


def downgrade() -> None:
    raise RuntimeError("RF20 is roll-forward only")
