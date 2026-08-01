"""RF-12 corrective: lossless manual grant semantics.

"""

# ruff: noqa: E501

import sqlalchemy as sa

from alembic import op

revision = "RF12_MANUAL_GRANT"
down_revision = "RF09_FINALIZE"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("entitlement_access_grants", "tariff_id", nullable=True, schema="mayak")
    op.add_column(
        "entitlement_access_grants",
        sa.Column("grant_kind", sa.String(32), nullable=False, server_default=sa.text("'TARIFF'")),
        schema="mayak",
    )
    op.add_column(
        "entitlement_access_grants",
        sa.Column("granted_capability", sa.String(128), nullable=True),
        schema="mayak",
    )
    op.add_column(
        "entitlement_access_grants",
        sa.Column("granted_scope", sa.String(128), nullable=True),
        schema="mayak",
    )
    op.add_column(
        "entitlement_access_grants",
        sa.Column(
            "reason", sa.String(512), nullable=False, server_default=sa.text("'legacy grant'")
        ),
        schema="mayak",
    )
    op.create_check_constraint(
        "grant_kind_allowed",
        "entitlement_access_grants",
        "grant_kind IN ('TARIFF', 'MANUAL')",
        schema="mayak",
    )
    op.create_check_constraint(
        "tariff_grant_fields_empty",
        "entitlement_access_grants",
        "grant_kind = 'MANUAL' OR (granted_capability IS NULL AND granted_scope IS NULL)",
        schema="mayak",
    )
    op.create_check_constraint(
        "manual_grant_fields_present",
        "entitlement_access_grants",
        "grant_kind = 'TARIFF' OR (btrim(granted_capability) <> '' AND btrim(granted_scope) <> '')",
        schema="mayak",
    )
    op.create_check_constraint(
        "reason_nonempty", "entitlement_access_grants", "btrim(reason) <> ''", schema="mayak"
    )
    op.create_index(
        "ix_entitlement_access_grants_manual_capability_scope",
        "entitlement_access_grants",
        ["account_id", "granted_capability", "granted_scope"],
        schema="mayak",
        postgresql_where=sa.text("grant_kind = 'MANUAL' AND state = 'ACTIVE'"),
    )


def downgrade() -> None:
    op.drop_index(
        "ix_entitlement_access_grants_manual_capability_scope",
        table_name="entitlement_access_grants",
        schema="mayak",
    )
    for name in (
        "reason_nonempty",
        "manual_grant_fields_present",
        "tariff_grant_fields_empty",
        "grant_kind_allowed",
    ):
        op.drop_constraint(name, "entitlement_access_grants", schema="mayak", type_="check")
    for name in ("reason", "granted_scope", "granted_capability", "grant_kind"):
        op.drop_column("entitlement_access_grants", name, schema="mayak")
    op.alter_column("entitlement_access_grants", "tariff_id", nullable=False, schema="mayak")
