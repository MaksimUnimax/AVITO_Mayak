"""RF-09 Identity & Access schema batch.

Technical ID: RF-09-07-M02-IDENTITY-AND-ACCESS-SCHEMA-BATCH-20260727
Implementation owner: Module 14 / RF-09
Domain owner: Module 02
Domain tables created: 5
Deferred FK resolved: 1
Roll-forward-only.
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "RF09_M02"
down_revision = "RF09_M01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "identity_accounts",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False
        ),
        sa.Column("phone", sa.Text(), nullable=True),
        sa.Column("state", sa.String(64), nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column(
            "row_version", sa.BigInteger(), nullable=False, server_default=sa.text("1")
        ),
        sa.CheckConstraint(
            "btrim(state) <> ''", name="ck_identity_accounts_state_nonempty"
        ),
        sa.CheckConstraint("row_version > 0", name="ck_identity_accounts_row_version"),
        schema="mayak",
    )
    op.create_index(
        "ix_identity_accounts_phone",
        "identity_accounts",
        ["phone"],
        schema="mayak",
        postgresql_where=sa.text("phone IS NOT NULL"),
    )
    op.create_index(
        "ix_identity_accounts_state_created_at",
        "identity_accounts",
        ["state", "created_at"],
        schema="mayak",
    )
    op.create_foreign_key(
        "fk_platform_audit_entries_actor_account_id_identity_accounts",
        "platform_audit_entries",
        "identity_accounts",
        ["actor_account_id"],
        ["id"],
        source_schema="mayak",
        referent_schema="mayak",
        ondelete="RESTRICT",
    )
    op.create_table(
        "identity_provider_links",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False
        ),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider_code", sa.String(64), nullable=False),
        sa.Column("provider_subject", sa.Text(), nullable=False),
        sa.Column("state", sa.String(64), nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column(
            "row_version", sa.BigInteger(), nullable=False, server_default=sa.text("1")
        ),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["mayak.identity_accounts.id"],
            name="fk_identity_provider_links_account_id_identity_accounts",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint(
            "provider_code",
            "provider_subject",
            name="uq_identity_provider_links_provider_subject",
        ),
        sa.CheckConstraint(
            "btrim(provider_code) <> ''",
            name="ck_identity_provider_links_provider_code_nonempty",
        ),
        sa.CheckConstraint(
            "btrim(provider_subject) <> ''",
            name="ck_identity_provider_links_provider_subject_nonempty",
        ),
        sa.CheckConstraint(
            "octet_length(provider_subject) <= 255",
            name="ck_identity_provider_links_provider_subject_length",
        ),
        sa.CheckConstraint(
            "btrim(state) <> ''", name="ck_identity_provider_links_state_nonempty"
        ),
        sa.CheckConstraint(
            "row_version > 0", name="ck_identity_provider_links_row_version"
        ),
        schema="mayak",
    )
    op.create_index(
        "ix_identity_provider_links_account_id",
        "identity_provider_links",
        ["account_id"],
        schema="mayak",
    )
    op.create_table(
        "identity_role_assignments",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False
        ),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role_code", sa.String(64), nullable=False),
        sa.Column(
            "assigned_by_account_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("revoked_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["mayak.identity_accounts.id"],
            name="fk_identity_role_assignments_account_id_identity_accounts",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["assigned_by_account_id"],
            ["mayak.identity_accounts.id"],
            name="fk_identity_role_assignments_assigned_by_account_id_identity_accounts",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint(
            "account_id",
            "role_code",
            "created_at",
            name="uq_identity_role_assignments_account_role_created",
        ),
        sa.CheckConstraint(
            "btrim(role_code) <> ''",
            name="ck_identity_role_assignments_role_code_nonempty",
        ),
        sa.CheckConstraint(
            "btrim(reason) <> ''", name="ck_identity_role_assignments_reason_nonempty"
        ),
        sa.CheckConstraint(
            "revoked_at IS NULL OR revoked_at >= created_at",
            name="ck_identity_role_assignments_revoked_at",
        ),
        schema="mayak",
    )
    op.create_index(
        "ix_identity_role_assignments_active",
        "identity_role_assignments",
        ["account_id", "role_code"],
        schema="mayak",
        postgresql_where=sa.text("revoked_at IS NULL"),
    )
    op.create_index(
        "ix_identity_role_assignments_assigned_by_created_at",
        "identity_role_assignments",
        ["assigned_by_account_id", "created_at"],
        schema="mayak",
    )
    op.create_table(
        "identity_sessions",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False
        ),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_hash", sa.CHAR(64), nullable=False),
        sa.Column("issued_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("expires_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("revoked_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column(
            "row_version", sa.BigInteger(), nullable=False, server_default=sa.text("1")
        ),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["mayak.identity_accounts.id"],
            name="fk_identity_sessions_account_id_identity_accounts",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint("token_hash", name="uq_identity_sessions_token_hash"),
        sa.CheckConstraint(
            "token_hash ~ '^[0-9a-f]{64}$'",
            name="ck_identity_sessions_token_hash_sha256",
        ),
        sa.CheckConstraint(
            "expires_at > issued_at", name="ck_identity_sessions_expiry_after_issue"
        ),
        sa.CheckConstraint(
            "expires_at <= issued_at + interval '24 hours'",
            name="ck_identity_sessions_max_lifetime",
        ),
        sa.CheckConstraint(
            "revoked_at IS NULL OR revoked_at >= issued_at",
            name="ck_identity_sessions_revoked_at",
        ),
        sa.CheckConstraint("row_version > 0", name="ck_identity_sessions_row_version"),
        schema="mayak",
    )
    op.create_index(
        "ix_identity_sessions_account_expires_at",
        "identity_sessions",
        ["account_id", "expires_at"],
        schema="mayak",
    )
    op.create_index(
        "ix_identity_sessions_active_expires_at",
        "identity_sessions",
        ["expires_at"],
        schema="mayak",
        postgresql_where=sa.text("revoked_at IS NULL"),
    )
    op.create_table(
        "identity_link_challenges",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False
        ),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("challenge_hash", sa.CHAR(64), nullable=False),
        sa.Column("provider_code", sa.String(64), nullable=False),
        sa.Column("expires_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("consumed_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column(
            "row_version", sa.BigInteger(), nullable=False, server_default=sa.text("1")
        ),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["mayak.identity_accounts.id"],
            name="fk_identity_link_challenges_account_id_identity_accounts",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint(
            "challenge_hash", name="uq_identity_link_challenges_challenge_hash"
        ),
        sa.CheckConstraint(
            "challenge_hash ~ '^[0-9a-f]{64}$'",
            name="ck_identity_link_challenges_challenge_hash_sha256",
        ),
        sa.CheckConstraint(
            "btrim(provider_code) <> ''",
            name="ck_identity_link_challenges_provider_code_nonempty",
        ),
        sa.CheckConstraint(
            "expires_at > created_at",
            name="ck_identity_link_challenges_expiry_after_creation",
        ),
        sa.CheckConstraint(
            "consumed_at IS NULL OR consumed_at >= created_at",
            name="ck_identity_link_challenges_consumed_at",
        ),
        sa.CheckConstraint(
            "row_version > 0", name="ck_identity_link_challenges_row_version"
        ),
        schema="mayak",
    )
    op.create_index(
        "ix_identity_link_challenges_active_expires_at",
        "identity_link_challenges",
        ["expires_at"],
        schema="mayak",
        postgresql_where=sa.text("consumed_at IS NULL"),
    )


def downgrade() -> None:
    raise RuntimeError("RF09_M02 is roll-forward only")
