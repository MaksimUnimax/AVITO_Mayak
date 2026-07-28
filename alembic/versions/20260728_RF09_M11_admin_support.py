"""RF-09-17-M11: Module 11 Admin & Support physical schema.

Technical ID: RF-09-17-M11-ADMIN-SUPPORT-SCHEMA-BATCH-20260728
Domain owner: Module 11 Admin & Support
Implementation owner: Module 14/RF-09
Tables: support_cases, support_case_notes, support_case_events
Identity remains account/actor/authorization authority.
Foreign modules retain business-state authority.
Notes are not business-state authority; internal notes are never customer-visible.
Foreign actions remain owning-module public commands.
No new deferred FK. Roll-forward-only.
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "RF09_M11"
down_revision = "RF09_M10"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "support_cases",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("opened_by_account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("assigned_to_account_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("state", sa.String(length=64), nullable=False),
        sa.Column("subject", sa.Text(), nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("row_version", postgresql.BIGINT(), server_default=sa.text("1"), nullable=False),
        sa.ForeignKeyConstraint(
            ["account_id"], ["mayak.identity_accounts.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["opened_by_account_id"], ["mayak.identity_accounts.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["assigned_to_account_id"], ["mayak.identity_accounts.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("btrim(state) <> ''", name="state_nonempty"),
        sa.CheckConstraint("btrim(subject) <> ''", name="subject_nonempty"),
        sa.CheckConstraint("row_version > 0", name="row_version_positive"),
        schema="mayak",
    )
    op.create_table(
        "support_case_notes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("author_account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("visibility", sa.String(length=64), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["mayak.support_cases.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["author_account_id"], ["mayak.identity_accounts.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("visibility IN ('PUBLIC', 'INTERNAL')", name="visibility_allowed"),
        sa.CheckConstraint("btrim(body) <> ''", name="body_nonempty"),
        schema="mayak",
    )
    op.create_table(
        "support_case_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_code", sa.String(length=64), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("details", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["mayak.support_cases.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["actor_account_id"], ["mayak.identity_accounts.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("btrim(event_code) <> ''", name="event_code_nonempty"),
        sa.CheckConstraint("btrim(reason) <> ''", name="reason_nonempty"),
        sa.CheckConstraint("octet_length(details::text) <= 65536", name="details_size"),
        schema="mayak",
    )
    op.create_index(
        "ix_support_cases_open_pending_updated_at",
        "support_cases",
        ["state", "updated_at"],
        unique=False,
        schema="mayak",
        postgresql_where=sa.text("state IN ('OPEN', 'PENDING')"),
    )
    op.create_index(
        "ix_support_cases_account_updated_at",
        "support_cases",
        ["account_id", "updated_at"],
        unique=False,
        schema="mayak",
    )
    op.create_index(
        "ix_support_case_notes_case_created_at",
        "support_case_notes",
        ["case_id", "created_at"],
        unique=False,
        schema="mayak",
    )
    op.create_index(
        "ix_support_case_events_case_created_at",
        "support_case_events",
        ["case_id", "created_at"],
        unique=False,
        schema="mayak",
    )
    op.create_index(
        "ix_support_case_events_actor_created_at",
        "support_case_events",
        ["actor_account_id", "created_at"],
        unique=False,
        schema="mayak",
    )


def downgrade() -> None:
    raise RuntimeError("RF09_M11 is roll-forward only")
