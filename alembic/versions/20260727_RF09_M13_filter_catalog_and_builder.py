"""RF-09 Module 13 Filter Catalog & Builder schema batch.

Technical ID: RF-09-09-M13-FILTER-CATALOG-SCHEMA-BATCH-20260727
Implementation owner: Module 14 / RF-09
Domain owner: Module 13
Domain tables created: 7
Deferred FK count: 0
Roll-forward-only.
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "RF09_M13"
down_revision = "RF09_M03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "filter_catalog_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("version_code", sa.String(32), nullable=False),
        sa.Column("provenance_ref", sa.String(255), nullable=False),
        sa.Column("evidence_fingerprint", sa.CHAR(64), nullable=False),
        sa.Column("state", sa.String(64), nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.UniqueConstraint("version_code", name="uq_filter_catalog_versions_version_code"),
        sa.UniqueConstraint(
            "evidence_fingerprint", name="uq_filter_catalog_versions_evidence_fingerprint"
        ),
        sa.CheckConstraint("btrim(version_code) <> ''", name="version_code_nonempty"),
        sa.CheckConstraint("btrim(provenance_ref) <> ''", name="provenance_ref_nonempty"),
        sa.CheckConstraint(
            "evidence_fingerprint ~ '^[0-9a-f]{64}$'", name="evidence_fingerprint_sha256"
        ),
        sa.CheckConstraint("btrim(state) <> ''", name="state_nonempty"),
        schema="mayak",
    )
    op.create_index(
        "ix_filter_catalog_versions_state_created_at",
        "filter_catalog_versions",
        ["state", "created_at"],
        schema="mayak",
    )
    op.create_table(
        "filter_evidence_references",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("catalog_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reference_code", sa.String(255), nullable=False),
        sa.Column("evidence_fingerprint", sa.CHAR(64), nullable=False),
        sa.Column("safe_metadata", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["catalog_version_id"], ["mayak.filter_catalog_versions.id"], ondelete="RESTRICT"
        ),
        sa.UniqueConstraint(
            "catalog_version_id",
            "reference_code",
            name="uq_filter_evidence_references_catalog_reference",
        ),
        sa.UniqueConstraint(
            "evidence_fingerprint", name="uq_filter_evidence_references_fingerprint"
        ),
        sa.CheckConstraint("btrim(reference_code) <> ''", name="reference_code_nonempty"),
        sa.CheckConstraint(
            "evidence_fingerprint ~ '^[0-9a-f]{64}$'", name="evidence_fingerprint_sha256"
        ),
        sa.CheckConstraint("octet_length(safe_metadata::text) <= 8192", name="safe_metadata_size"),
        schema="mayak",
    )
    op.create_index(
        "ix_filter_evidence_references_catalog_created_at",
        "filter_evidence_references",
        ["catalog_version_id", "created_at"],
        schema="mayak",
    )
    op.create_table(
        "filter_definitions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("catalog_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("field_code", sa.String(128), nullable=False),
        sa.Column("label", sa.Text(), nullable=False),
        sa.Column("support_state", sa.String(64), nullable=False),
        sa.Column("evidence_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["catalog_version_id"], ["mayak.filter_catalog_versions.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["evidence_id"], ["mayak.filter_evidence_references.id"], ondelete="RESTRICT"
        ),
        sa.UniqueConstraint(
            "catalog_version_id", "field_code", name="uq_filter_definitions_catalog_field"
        ),
        sa.CheckConstraint("btrim(field_code) <> ''", name="field_code_nonempty"),
        sa.CheckConstraint("btrim(label) <> ''", name="label_nonempty"),
        sa.CheckConstraint("btrim(support_state) <> ''", name="support_state_nonempty"),
        schema="mayak",
    )
    op.create_index(
        "ix_filter_definitions_catalog_support_state",
        "filter_definitions",
        ["catalog_version_id", "support_state"],
        schema="mayak",
    )
    op.create_index(
        "ix_filter_definitions_field_code", "filter_definitions", ["field_code"], schema="mayak"
    )
    op.create_table(
        "filter_options",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("definition_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("option_code", sa.String(128), nullable=False),
        sa.Column("label", sa.Text(), nullable=False),
        sa.Column("sort_order", sa.BigInteger(), nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["definition_id"], ["mayak.filter_definitions.id"], ondelete="RESTRICT"
        ),
        sa.UniqueConstraint(
            "definition_id", "option_code", name="uq_filter_options_definition_option"
        ),
        sa.CheckConstraint("btrim(option_code) <> ''", name="option_code_nonempty"),
        sa.CheckConstraint("btrim(label) <> ''", name="label_nonempty"),
        sa.CheckConstraint("sort_order >= 0", name="sort_order_nonnegative"),
        schema="mayak",
    )
    op.create_index(
        "ix_filter_options_definition_sort_order",
        "filter_options",
        ["definition_id", "sort_order"],
        schema="mayak",
    )
    op.create_table(
        "filter_dependencies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("catalog_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_definition_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("depends_on_definition_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rule", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["catalog_version_id"], ["mayak.filter_catalog_versions.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["source_definition_id"], ["mayak.filter_definitions.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["depends_on_definition_id"], ["mayak.filter_definitions.id"], ondelete="RESTRICT"
        ),
        sa.UniqueConstraint(
            "catalog_version_id",
            "source_definition_id",
            "depends_on_definition_id",
            name="uq_filter_dependencies_catalog_source_dependency",
        ),
        sa.CheckConstraint("octet_length(rule::text) <= 65536", name="rule_size"),
        sa.CheckConstraint(
            "source_definition_id <> depends_on_definition_id", name="source_differs_from_target"
        ),
        schema="mayak",
    )
    op.create_index(
        "ix_filter_dependencies_catalog_source",
        "filter_dependencies",
        ["catalog_version_id", "source_definition_id"],
        schema="mayak",
    )
    op.create_table(
        "filter_category_applicability",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("catalog_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("category_code", sa.String(128), nullable=False),
        sa.Column("definition_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("applicability_state", sa.String(64), nullable=False),
        sa.Column("evidence_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["catalog_version_id"], ["mayak.filter_catalog_versions.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["definition_id"], ["mayak.filter_definitions.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["evidence_id"], ["mayak.filter_evidence_references.id"], ondelete="RESTRICT"
        ),
        sa.UniqueConstraint(
            "catalog_version_id",
            "category_code",
            "definition_id",
            name="uq_filter_category_applicability_catalog_category_definition",
        ),
        sa.CheckConstraint("btrim(category_code) <> ''", name="category_code_nonempty"),
        sa.CheckConstraint("btrim(applicability_state) <> ''", name="applicability_state_nonempty"),
        schema="mayak",
    )
    op.create_index(
        "ix_filter_category_applicability_catalog_category",
        "filter_category_applicability",
        ["catalog_version_id", "category_code"],
        schema="mayak",
    )
    op.create_index(
        "ix_filter_category_applicability_definition",
        "filter_category_applicability",
        ["definition_id"],
        schema="mayak",
    )
    op.create_table(
        "filter_capability_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("catalog_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("profile_code", sa.String(128), nullable=False),
        sa.Column("capabilities", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["catalog_version_id"], ["mayak.filter_catalog_versions.id"], ondelete="RESTRICT"
        ),
        sa.UniqueConstraint(
            "catalog_version_id",
            "profile_code",
            name="uq_filter_capability_profiles_catalog_profile",
        ),
        sa.CheckConstraint("btrim(profile_code) <> ''", name="profile_code_nonempty"),
        sa.CheckConstraint("octet_length(capabilities::text) <= 65536", name="capabilities_size"),
        schema="mayak",
    )
    op.create_index(
        "ix_filter_capability_profiles_catalog_profile",
        "filter_capability_profiles",
        ["catalog_version_id", "profile_code"],
        schema="mayak",
    )


def downgrade() -> None:
    raise RuntimeError("RF09_M13 is roll-forward only")
