"""Module 13 Filter Catalog & Builder physical table registrations."""

from __future__ import annotations

from typing import Any

from sqlalchemy import (
    CHAR,
    BigInteger,
    CheckConstraint,
    Column,
    ForeignKeyConstraint,
    Index,
    MetaData,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID
from sqlalchemy.dialects.postgresql import dialect as postgresql_dialect

_TABLE_NAMES = (
    "filter_catalog_versions",
    "filter_definitions",
    "filter_options",
    "filter_dependencies",
    "filter_category_applicability",
    "filter_evidence_references",
    "filter_capability_profiles",
)
_NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}
_POSTGRESQL_DIALECT = postgresql_dialect()


def _key(metadata: MetaData, name: str) -> str:
    return f"{metadata.schema}.{name}" if metadata.schema else name


def _normalized_sql(value: object) -> str:
    result = " ".join(str(value).split())
    while result.startswith("(") and result.endswith(")"):
        depth = 0
        enclosed = True
        for index, character in enumerate(result):
            if character == "(":
                depth += 1
            elif character == ")":
                depth -= 1
                if depth == 0 and index != len(result) - 1:
                    enclosed = False
                    break
        if enclosed:
            result = result[1:-1].strip()
        else:
            break
    return result


def _stable_value(value: object) -> object:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, (list, tuple)):
        return tuple(_stable_value(item) for item in value)
    if isinstance(value, dict):
        return tuple(sorted((str(key), _stable_value(item)) for key, item in value.items()))
    return _normalized_sql(value)


def _compiled_type(column_type: Any) -> str:
    return str(column_type.compile(dialect=_POSTGRESQL_DIALECT))


def _type_options(column_type: object) -> tuple[tuple[str, object], ...]:
    names: tuple[str, ...] = ("length", "precision", "scale", "timezone", "as_uuid", "collation")
    if isinstance(column_type, JSONB):
        names += ("none_as_null", "hashable", "should_evaluate_none", "astext_type")
    values: list[tuple[str, object]] = []
    for name in names:
        if hasattr(column_type, name):
            value = getattr(column_type, name)
            if name == "astext_type" and value is not None:
                value = (type(value).__module__, type(value).__name__, _compiled_type(value))
            values.append((name, _stable_value(value)))
    return tuple(values)


def _type_signature(column: Column[Any]) -> tuple[object, ...]:
    column_type = column.type
    return (
        type(column_type).__module__,
        type(column_type).__name__,
        _compiled_type(column_type),
        _type_options(column_type),
    )


def _default_signature(column: Column[Any]) -> str | None:
    if column.server_default is None:
        return None
    return _normalized_sql(getattr(column.server_default, "arg", column.server_default))


def _value_signature(value: object) -> object:
    if value is None:
        return None
    argument = getattr(value, "arg", value)
    if callable(argument):
        return (
            "callable",
            getattr(argument, "__module__", ""),
            getattr(argument, "__qualname__", repr(argument)),
        )
    return _stable_value(argument)


def _column_signature(column: Column[Any]) -> tuple[object, ...]:
    identity = column.identity
    computed = column.computed
    return (
        column.name,
        _type_signature(column),
        column.nullable,
        column.primary_key,
        _default_signature(column),
        _value_signature(column.default),
        _value_signature(column.onupdate),
        _value_signature(column.server_onupdate),
        column.autoincrement,
        column.unique,
        column.index,
        column.comment,
        column.system,
        tuple(
            (name, _stable_value(getattr(identity, name, None)))
            for name in (
                "name",
                "start",
                "increment",
                "minvalue",
                "maxvalue",
                "cycle",
                "cache",
                "order",
            )
        )
        if identity is not None
        else None,
        (_normalized_sql(computed.sqltext), computed.persisted) if computed is not None else None,
    )


def _dialect_options_signature(options: object) -> tuple[tuple[str, object], ...]:
    if not hasattr(options, "items"):
        return ()

    def is_default(value: object) -> bool:
        return value is None or value is False or value == {} or value == ()

    return tuple(
        (
            str(dialect),
            tuple(
                sorted(
                    (str(key), _normalized_sql(value))
                    for key, value in values.items()
                    if not is_default(value)
                )
            ),
        )
        for dialect, values in sorted(options.items())
        if any(not is_default(value) for value in values.values())
    )


def _constraint_signature(constraint: Any) -> tuple[object, ...]:
    columns = tuple(column.name for column in getattr(constraint, "columns", ()))
    return (
        type(constraint).__module__,
        type(constraint).__name__,
        constraint.name,
        columns,
        _normalized_sql(getattr(constraint, "sqltext", ""))
        if isinstance(constraint, CheckConstraint)
        else "",
        getattr(constraint, "deferrable", None),
        getattr(constraint, "initially", None),
        _dialect_options_signature(getattr(constraint, "dialect_options", {})),
    )


def _foreign_key_signature(constraint: ForeignKeyConstraint) -> tuple[object, ...]:
    return (
        type(constraint).__module__,
        type(constraint).__name__,
        constraint.name,
        tuple(element.parent.name for element in constraint.elements),
        tuple(element.target_fullname for element in constraint.elements),
        constraint.ondelete,
        constraint.onupdate,
        constraint.deferrable,
        constraint.initially,
        constraint.use_alter,
        constraint.match,
        _dialect_options_signature(constraint.dialect_options),
    )


def _index_signature(index: Index) -> tuple[object, ...]:
    postgresql_options: Any = index.dialect_options.get("postgresql", {})
    predicate = postgresql_options.get("where")
    return (
        type(index).__module__,
        type(index).__name__,
        index.name,
        tuple(getattr(column, "name", str(column)) for column in index.expressions),
        index.unique,
        _normalized_sql(predicate) if predicate is not None else None,
        _dialect_options_signature(index.dialect_options),
    )


def _table_signature(table: Table) -> tuple[object, ...]:
    return (
        table.name,
        table.schema,
        table.comment,
        tuple(getattr(table, "prefixes", ())),
        table.implicit_returning,
        _dialect_options_signature(table.dialect_options),
        tuple(sorted((str(key), _stable_value(value)) for key, value in table.info.items())),
        tuple(_column_signature(column) for column in table.columns),
        tuple(
            sorted(
                _foreign_key_signature(constraint)
                if isinstance(constraint, ForeignKeyConstraint)
                else _constraint_signature(constraint)
                for constraint in table.constraints
            )
        ),
        tuple(sorted(_index_signature(index) for index in table.indexes)),
    )


def _canonical_model() -> tuple[Table, Table, Table, Table, Table, Table, Table]:
    canonical = MetaData(schema="mayak", naming_convention=_NAMING_CONVENTION)
    return _register_canonical_tables(canonical)


def _validate_existing(tables: list[Table]) -> None:
    for actual, expected in zip(tables, _canonical_model()):
        if _table_signature(actual) != _table_signature(expected):
            raise RuntimeError(f"conflicting existing {actual.name} registration")


def register_filter_catalog_tables(
    target_metadata: MetaData,
) -> tuple[Table, Table, Table, Table, Table, Table, Table]:
    """Register exactly the immutable Module 13 tables without database I/O."""
    if target_metadata.schema != "mayak":
        raise RuntimeError("filter catalog tables require mayak schema")
    present = [_key(target_metadata, name) in target_metadata.tables for name in _TABLE_NAMES]
    if any(present) and not all(present):
        raise RuntimeError("partial filter catalog table registration is not supported")
    if all(present):
        tables = [target_metadata.tables[_key(target_metadata, name)] for name in _TABLE_NAMES]
        _validate_existing(tables)
        return tuple(tables)  # type: ignore[return-value]
    return _register_canonical_tables(target_metadata)


def _register_canonical_tables(
    target_metadata: MetaData,
) -> tuple[Table, Table, Table, Table, Table, Table, Table]:
    versions = Table(
        "filter_catalog_versions",
        target_metadata,
        Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        Column("version_code", String(32), nullable=False),
        Column("provenance_ref", String(255), nullable=False),
        Column("evidence_fingerprint", CHAR(64), nullable=False),
        Column("state", String(64), nullable=False),
        Column("created_at", TIMESTAMP(timezone=True), nullable=False),
        UniqueConstraint("version_code", name="uq_filter_catalog_versions_version_code"),
        UniqueConstraint(
            "evidence_fingerprint", name="uq_filter_catalog_versions_evidence_fingerprint"
        ),
        CheckConstraint("btrim(version_code) <> ''", name="version_code_nonempty"),
        CheckConstraint("btrim(provenance_ref) <> ''", name="provenance_ref_nonempty"),
        CheckConstraint(
            "evidence_fingerprint ~ '^[0-9a-f]{64}$'", name="evidence_fingerprint_sha256"
        ),
        CheckConstraint("btrim(state) <> ''", name="state_nonempty"),
    )
    Index("ix_filter_catalog_versions_state_created_at", versions.c.state, versions.c.created_at)

    evidence = Table(
        "filter_evidence_references",
        target_metadata,
        Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        Column("catalog_version_id", UUID(as_uuid=True), nullable=False),
        Column("reference_code", String(255), nullable=False),
        Column("evidence_fingerprint", CHAR(64), nullable=False),
        Column("safe_metadata", JSONB, nullable=False),
        Column("created_at", TIMESTAMP(timezone=True), nullable=False),
        ForeignKeyConstraint(
            ["catalog_version_id"], ["mayak.filter_catalog_versions.id"], ondelete="RESTRICT"
        ),
        UniqueConstraint(
            "catalog_version_id",
            "reference_code",
            name="uq_filter_evidence_references_catalog_reference",
        ),
        UniqueConstraint("evidence_fingerprint", name="uq_filter_evidence_references_fingerprint"),
        CheckConstraint("btrim(reference_code) <> ''", name="reference_code_nonempty"),
        CheckConstraint(
            "evidence_fingerprint ~ '^[0-9a-f]{64}$'", name="evidence_fingerprint_sha256"
        ),
        CheckConstraint("octet_length(safe_metadata::text) <= 8192", name="safe_metadata_size"),
    )
    Index(
        "ix_filter_evidence_references_catalog_created_at",
        evidence.c.catalog_version_id,
        evidence.c.created_at,
    )

    definitions = Table(
        "filter_definitions",
        target_metadata,
        Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        Column("catalog_version_id", UUID(as_uuid=True), nullable=False),
        Column("field_code", String(128), nullable=False),
        Column("label", Text, nullable=False),
        Column("support_state", String(64), nullable=False),
        Column("evidence_id", UUID(as_uuid=True), nullable=True),
        Column("created_at", TIMESTAMP(timezone=True), nullable=False),
        ForeignKeyConstraint(
            ["catalog_version_id"], ["mayak.filter_catalog_versions.id"], ondelete="RESTRICT"
        ),
        ForeignKeyConstraint(
            ["evidence_id"], ["mayak.filter_evidence_references.id"], ondelete="RESTRICT"
        ),
        UniqueConstraint(
            "catalog_version_id", "field_code", name="uq_filter_definitions_catalog_field"
        ),
        CheckConstraint("btrim(field_code) <> ''", name="field_code_nonempty"),
        CheckConstraint("btrim(label) <> ''", name="label_nonempty"),
        CheckConstraint("btrim(support_state) <> ''", name="support_state_nonempty"),
    )
    Index(
        "ix_filter_definitions_catalog_support_state",
        definitions.c.catalog_version_id,
        definitions.c.support_state,
    )
    Index("ix_filter_definitions_field_code", definitions.c.field_code)

    options = Table(
        "filter_options",
        target_metadata,
        Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        Column("definition_id", UUID(as_uuid=True), nullable=False),
        Column("option_code", String(128), nullable=False),
        Column("label", Text, nullable=False),
        Column("sort_order", BigInteger, nullable=False),
        Column("created_at", TIMESTAMP(timezone=True), nullable=False),
        ForeignKeyConstraint(
            ["definition_id"], ["mayak.filter_definitions.id"], ondelete="RESTRICT"
        ),
        UniqueConstraint(
            "definition_id", "option_code", name="uq_filter_options_definition_option"
        ),
        CheckConstraint("btrim(option_code) <> ''", name="option_code_nonempty"),
        CheckConstraint("btrim(label) <> ''", name="label_nonempty"),
        CheckConstraint("sort_order >= 0", name="sort_order_nonnegative"),
    )
    Index("ix_filter_options_definition_sort_order", options.c.definition_id, options.c.sort_order)

    dependencies = Table(
        "filter_dependencies",
        target_metadata,
        Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        Column("catalog_version_id", UUID(as_uuid=True), nullable=False),
        Column("source_definition_id", UUID(as_uuid=True), nullable=False),
        Column("depends_on_definition_id", UUID(as_uuid=True), nullable=False),
        Column("rule", JSONB, nullable=False),
        Column("created_at", TIMESTAMP(timezone=True), nullable=False),
        ForeignKeyConstraint(
            ["catalog_version_id"], ["mayak.filter_catalog_versions.id"], ondelete="RESTRICT"
        ),
        ForeignKeyConstraint(
            ["source_definition_id"], ["mayak.filter_definitions.id"], ondelete="RESTRICT"
        ),
        ForeignKeyConstraint(
            ["depends_on_definition_id"], ["mayak.filter_definitions.id"], ondelete="RESTRICT"
        ),
        UniqueConstraint(
            "catalog_version_id",
            "source_definition_id",
            "depends_on_definition_id",
            name="uq_filter_dependencies_catalog_source_dependency",
        ),
        CheckConstraint("octet_length(rule::text) <= 65536", name="rule_size"),
        CheckConstraint(
            "source_definition_id <> depends_on_definition_id", name="source_differs_from_target"
        ),
    )
    Index(
        "ix_filter_dependencies_catalog_source",
        dependencies.c.catalog_version_id,
        dependencies.c.source_definition_id,
    )

    applicability = Table(
        "filter_category_applicability",
        target_metadata,
        Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        Column("catalog_version_id", UUID(as_uuid=True), nullable=False),
        Column("category_code", String(128), nullable=False),
        Column("definition_id", UUID(as_uuid=True), nullable=False),
        Column("applicability_state", String(64), nullable=False),
        Column("evidence_id", UUID(as_uuid=True), nullable=True),
        Column("created_at", TIMESTAMP(timezone=True), nullable=False),
        ForeignKeyConstraint(
            ["catalog_version_id"], ["mayak.filter_catalog_versions.id"], ondelete="RESTRICT"
        ),
        ForeignKeyConstraint(
            ["definition_id"], ["mayak.filter_definitions.id"], ondelete="RESTRICT"
        ),
        ForeignKeyConstraint(
            ["evidence_id"], ["mayak.filter_evidence_references.id"], ondelete="RESTRICT"
        ),
        UniqueConstraint(
            "catalog_version_id",
            "category_code",
            "definition_id",
            name="uq_filter_category_applicability_catalog_category_definition",
        ),
        CheckConstraint("btrim(category_code) <> ''", name="category_code_nonempty"),
        CheckConstraint("btrim(applicability_state) <> ''", name="applicability_state_nonempty"),
    )
    Index(
        "ix_filter_category_applicability_catalog_category",
        applicability.c.catalog_version_id,
        applicability.c.category_code,
    )
    Index("ix_filter_category_applicability_definition", applicability.c.definition_id)

    profiles = Table(
        "filter_capability_profiles",
        target_metadata,
        Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        Column("catalog_version_id", UUID(as_uuid=True), nullable=False),
        Column("profile_code", String(128), nullable=False),
        Column("capabilities", JSONB, nullable=False),
        Column("created_at", TIMESTAMP(timezone=True), nullable=False),
        ForeignKeyConstraint(
            ["catalog_version_id"], ["mayak.filter_catalog_versions.id"], ondelete="RESTRICT"
        ),
        UniqueConstraint(
            "catalog_version_id",
            "profile_code",
            name="uq_filter_capability_profiles_catalog_profile",
        ),
        CheckConstraint("btrim(profile_code) <> ''", name="profile_code_nonempty"),
        CheckConstraint("octet_length(capabilities::text) <= 65536", name="capabilities_size"),
    )
    Index(
        "ix_filter_capability_profiles_catalog_profile",
        profiles.c.catalog_version_id,
        profiles.c.profile_code,
    )
    return versions, definitions, options, dependencies, applicability, evidence, profiles


__all__ = ["register_filter_catalog_tables"]
