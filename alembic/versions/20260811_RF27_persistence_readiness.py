"""RF27: allow readiness to observe the migration revision safely.

The application role needs to read ``alembic_version`` for the runtime
readiness contract, but migration authority remains exclusively with
``mayak_migration``.
"""

from __future__ import annotations

from alembic import op

revision = "RF27_PERSISTENCE_READINESS"
down_revision = "RF20_ADMIN_SUPPORT_RUNTIME"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("GRANT SELECT ON TABLE mayak.alembic_version TO mayak_application")


def downgrade() -> None:
    op.execute("REVOKE SELECT ON TABLE mayak.alembic_version FROM mayak_application")
