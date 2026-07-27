from __future__ import annotations

import importlib
from typing import Any, cast

import pytest
from sqlalchemy import CheckConstraint, ForeignKeyConstraint, MetaData, Table, UniqueConstraint
from sqlalchemy.dialects import postgresql

from mayak.persistence.metadata import NAMING_CONVENTION, metadata
from mayak.persistence.schema.filter_catalog import register_filter_catalog_tables

NAMES = (
    "filter_catalog_versions",
    "filter_definitions",
    "filter_options",
    "filter_dependencies",
    "filter_category_applicability",
    "filter_evidence_references",
    "filter_capability_profiles",
)


def _tables() -> tuple[Table, ...]:
    return tuple(metadata.tables[f"mayak.{name}"] for name in NAMES)


def test_exact_tables_and_canonical_order() -> None:
    assert len(_tables()) == 7
    assert tuple(table.name for table in register_filter_catalog_tables(metadata)) == NAMES


def test_columns_types_and_immutability() -> None:
    expected = {
        "filter_catalog_versions": [
            "id",
            "version_code",
            "provenance_ref",
            "evidence_fingerprint",
            "state",
            "created_at",
        ],
        "filter_definitions": [
            "id",
            "catalog_version_id",
            "field_code",
            "label",
            "support_state",
            "evidence_id",
            "created_at",
        ],
        "filter_options": [
            "id",
            "definition_id",
            "option_code",
            "label",
            "sort_order",
            "created_at",
        ],
        "filter_dependencies": [
            "id",
            "catalog_version_id",
            "source_definition_id",
            "depends_on_definition_id",
            "rule",
            "created_at",
        ],
        "filter_category_applicability": [
            "id",
            "catalog_version_id",
            "category_code",
            "definition_id",
            "applicability_state",
            "evidence_id",
            "created_at",
        ],
        "filter_evidence_references": [
            "id",
            "catalog_version_id",
            "reference_code",
            "evidence_fingerprint",
            "safe_metadata",
            "created_at",
        ],
        "filter_capability_profiles": [
            "id",
            "catalog_version_id",
            "profile_code",
            "capabilities",
            "created_at",
        ],
    }
    for table in _tables():
        assert [column.name for column in table.columns] == expected[table.name]
        assert isinstance(table.c.id.type, postgresql.UUID) and table.c.id.type.as_uuid is True
        assert table.c.id.server_default is None and table.c.id.default is None
        assert isinstance(table.c.created_at.type, postgresql.TIMESTAMP)
        assert table.c.created_at.type.timezone is True
        assert all(
            column.server_default is None and column.default is None for column in table.columns
        )
        assert "updated_at" not in table.c and "row_version" not in table.c
        assert table.schema == "mayak"
    assert (
        cast(Any, metadata.tables["mayak.filter_catalog_versions"].c.version_code.type).length == 32
    )
    assert cast(Any, metadata.tables["mayak.filter_definitions"].c.field_code.type).length == 128
    assert cast(Any, metadata.tables["mayak.filter_options"].c.option_code.type).length == 128
    assert (
        cast(
            Any, metadata.tables["mayak.filter_evidence_references"].c.evidence_fingerprint.type
        ).length
        == 64
    )
    assert isinstance(metadata.tables["mayak.filter_dependencies"].c.rule.type, postgresql.JSONB)
    assert isinstance(
        metadata.tables["mayak.filter_capability_profiles"].c.capabilities.type, postgresql.JSONB
    )


def test_constraints_fks_indexes_and_checks_are_exact() -> None:
    unique_names = {
        constraint.name
        for table in _tables()
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
    }
    assert len(unique_names) == 9
    assert unique_names == {
        "uq_filter_catalog_versions_version_code",
        "uq_filter_catalog_versions_evidence_fingerprint",
        "uq_filter_definitions_catalog_field",
        "uq_filter_options_definition_option",
        "uq_filter_dependencies_catalog_source_dependency",
        "uq_filter_category_applicability_catalog_category_definition",
        "uq_filter_evidence_references_catalog_reference",
        "uq_filter_evidence_references_fingerprint",
        "uq_filter_capability_profiles_catalog_profile",
    }
    fks = [
        constraint
        for table in _tables()
        for constraint in table.constraints
        if isinstance(constraint, ForeignKeyConstraint)
    ]
    assert len(fks) == 11
    assert all(fk.ondelete == "RESTRICT" and fk.onupdate is None for fk in fks)
    assert {tuple(element.target_fullname for element in fk.elements) for fk in fks} == {
        ("mayak.filter_catalog_versions.id",),
        ("mayak.filter_definitions.id",),
        ("mayak.filter_evidence_references.id",),
    }
    indexes: dict[str, tuple[str, ...]] = {
        str(index.name): tuple(column.name for column in index.columns)
        for table in _tables()
        for index in table.indexes
    }
    assert len(indexes) == 9
    assert indexes["ix_filter_catalog_versions_state_created_at"] == ("state", "created_at")
    assert indexes["ix_filter_definitions_catalog_support_state"] == (
        "catalog_version_id",
        "support_state",
    )
    assert indexes["ix_filter_definitions_field_code"] == ("field_code",)
    assert indexes["ix_filter_options_definition_sort_order"] == ("definition_id", "sort_order")
    assert indexes["ix_filter_dependencies_catalog_source"] == (
        "catalog_version_id",
        "source_definition_id",
    )
    assert indexes["ix_filter_category_applicability_catalog_category"] == (
        "catalog_version_id",
        "category_code",
    )
    assert indexes["ix_filter_category_applicability_definition"] == ("definition_id",)
    assert indexes["ix_filter_evidence_references_catalog_created_at"] == (
        "catalog_version_id",
        "created_at",
    )
    assert indexes["ix_filter_capability_profiles_catalog_profile"] == (
        "catalog_version_id",
        "profile_code",
    )
    checks = {
        table.name: {str(c.sqltext) for c in table.constraints if isinstance(c, CheckConstraint)}
        for table in _tables()
    }
    assert "octet_length(rule::text) <= 65536" in checks["filter_dependencies"]
    assert "source_definition_id <> depends_on_definition_id" in checks["filter_dependencies"]
    assert "octet_length(safe_metadata::text) <= 8192" in checks["filter_evidence_references"]
    assert "octet_length(capabilities::text) <= 65536" in checks["filter_capability_profiles"]
    assert any(
        "evidence_fingerprint" in value and "[0-9a-f]" in value
        for value in checks["filter_catalog_versions"]
    )
    assert any(
        "evidence_fingerprint" in value and "[0-9a-f]" in value
        for value in checks["filter_evidence_references"]
    )


def test_nullable_evidence_fields_and_forbidden_scope() -> None:
    assert metadata.tables["mayak.filter_definitions"].c.evidence_id.nullable is True
    assert metadata.tables["mayak.filter_category_applicability"].c.evidence_id.nullable is True
    forbidden = (
        "raw",
        "payload",
        "html",
        "cookie",
        "secret",
        "password",
        "provider_response",
        "beacon",
        "web",
    )
    for table in _tables():
        assert not any(
            any(word in column.name.lower() for word in forbidden) for column in table.columns
        )
    assert not any(
        "country" in str(getattr(c, "sqltext", "")).lower()
        for table in _tables()
        for c in table.constraints
    )


def test_registration_is_idempotent_and_inert(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    monkeypatch.setattr("sqlalchemy.create_engine", lambda *args, **kwargs: calls.append("engine"))
    monkeypatch.setattr(
        "sqlalchemy.engine.Engine.connect", lambda *args, **kwargs: calls.append("connect")
    )
    assert (
        register_filter_catalog_tables(metadata)
        == register_filter_catalog_tables(metadata)
        == register_filter_catalog_tables(metadata)
    )
    assert calls == []
    assert importlib.import_module("mayak.persistence.schema.filter_catalog")


def test_partial_wrong_schema_and_conflicting_shape_fail_before_mutation() -> None:
    partial = MetaData(schema="mayak", naming_convention=NAMING_CONVENTION)
    Table(NAMES[0], partial)
    snapshot = list(partial.tables)
    with pytest.raises(RuntimeError, match="partial filter catalog"):
        register_filter_catalog_tables(partial)
    assert list(partial.tables) == snapshot
    wrong_schema = MetaData(schema="public", naming_convention=NAMING_CONVENTION)
    with pytest.raises(RuntimeError, match="mayak schema"):
        register_filter_catalog_tables(wrong_schema)
    assert not wrong_schema.tables
    conflicting = MetaData(schema="mayak", naming_convention=NAMING_CONVENTION)
    register_filter_catalog_tables(conflicting)
    before = list(conflicting.tables)
    conflicting.tables["mayak.filter_options"].c.sort_order.nullable = True
    with pytest.raises(RuntimeError, match="conflicting existing"):
        register_filter_catalog_tables(conflicting)
    assert list(conflicting.tables) == before
