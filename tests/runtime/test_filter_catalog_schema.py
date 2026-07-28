from __future__ import annotations

import importlib
import sys
from collections.abc import Callable
from typing import Any

import pytest
from sqlalchemy import (
    CheckConstraint,
    Column,
    ColumnDefault,
    Constraint,
    ForeignKeyConstraint,
    Index,
    MetaData,
    String,
    Table,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import ExcludeConstraint

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
EXPECTED_TABLE_KEYS = tuple(
    f"mayak.{name}"
    for name in (
        "filter_catalog_versions",
        "filter_evidence_references",
        "filter_definitions",
        "filter_options",
        "filter_dependencies",
        "filter_category_applicability",
        "filter_capability_profiles",
    )
)


def _new_metadata() -> MetaData:
    return MetaData(schema="mayak", naming_convention=dict(NAMING_CONVENTION))


def _tables(target: MetaData) -> tuple[Table, ...]:
    return tuple(target.tables[key] for key in EXPECTED_TABLE_KEYS)


def _normal(value: object) -> object:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, dict):
        return tuple(sorted((str(k), _normal(v)) for k, v in value.items()))
    if isinstance(value, (list, tuple)):
        return tuple(_normal(v) for v in value)
    return " ".join(str(value).split())


def _options(value: object) -> object:
    if not hasattr(value, "items"):
        return ()
    return tuple(
        sorted(
            (str(dialect), tuple(sorted((str(k), _normal(v)) for k, v in opts.items())))
            for dialect, opts in value.items()
        )
    )


def _value_signature(value: object) -> object:
    if value is None:
        return None
    argument = getattr(value, "arg", value)
    if callable(argument):
        return (
            "callable",
            getattr(argument, "__module__", ""),
            getattr(argument, "__qualname__", ""),
        )
    return _normal(argument)


def _type_signature(column: Column[Any]) -> tuple[object, ...]:
    column_type = column.type
    names: tuple[str, ...] = ("length", "precision", "scale", "timezone", "as_uuid", "collation")
    if isinstance(column_type, postgresql.JSONB):
        names += ("none_as_null", "hashable", "should_evaluate_none", "astext_type")
    options = tuple(
        (name, _normal(getattr(column_type, name))) for name in names if hasattr(column_type, name)
    )
    return (
        type(column_type).__module__,
        type(column_type).__name__,
        str(column_type.compile(dialect=postgresql.dialect())),
        options,
    )


def _column_signature(column: Column[Any]) -> tuple[object, ...]:
    return (
        id(column),
        column.name,
        column.key,
        _type_signature(column),
        column.nullable,
        column.primary_key,
        column.autoincrement,
        column.unique,
        column.index,
        _value_signature(column.server_default),
        _value_signature(column.default),
        _value_signature(column.onupdate),
        _value_signature(column.server_onupdate),
        column.comment,
        _normal(column.info),
        column.system,
        column.doc,
        tuple(
            (
                id(fk),
                fk.name,
                fk.parent.name,
                fk.target_fullname,
                fk.ondelete,
                fk.onupdate,
                fk.deferrable,
                fk.initially,
                fk.use_alter,
                fk.match,
                _options(fk.dialect_options),
            )
            for fk in column.foreign_keys
        ),
    )


def _constraint_signature(constraint: Constraint) -> tuple[object, ...]:
    columns = tuple(column.name for column in getattr(constraint, "columns", ()))
    return (
        id(constraint),
        type(constraint).__module__,
        type(constraint).__name__,
        constraint.name,
        columns,
        " ".join(str(getattr(constraint, "sqltext", "")).split()),
        getattr(constraint, "deferrable", None),
        getattr(constraint, "initially", None),
        getattr(constraint, "use_alter", None),
        getattr(constraint, "match", None),
        getattr(constraint, "ondelete", None),
        getattr(constraint, "onupdate", None),
        _options(getattr(constraint, "dialect_options", {})),
        constraint.comment,
        _normal(constraint.info),
    )


def _index_signature(index: Index) -> tuple[object, ...]:
    return (
        id(index),
        type(index).__module__,
        type(index).__name__,
        index.name,
        tuple(getattr(expression, "name", str(expression)) for expression in index.expressions),
        index.unique,
        _options(index.dialect_options),
        _normal(index.info),
    )


def _snapshot(target: MetaData) -> tuple[object, ...]:
    table_snapshots = []
    for table in target.tables.values():
        table_snapshots.append(
            (
                id(table),
                table.schema,
                table.name,
                table.fullname,
                table.key,
                table.comment,
                _normal(table.info),
                tuple(getattr(table, "prefixes", ())),
                table.implicit_returning,
                _options(table.dialect_options),
                tuple(_column_signature(column) for column in table.columns),
                tuple(sorted(_constraint_signature(c) for c in table.constraints)),
                tuple(sorted(_index_signature(i) for i in table.indexes)),
            )
        )
    return (
        target.schema,
        _normal(target.naming_convention),
        _normal(target.info),
        tuple(target.tables.keys()),
        tuple(table_snapshots),
    )


def _canonical(target: MetaData) -> tuple[Table, ...]:
    return _tables(target) if target.tables else register_filter_catalog_tables(target)


def _reject(mutator: Callable[[MetaData], None], case_id: str) -> None:
    target = _new_metadata()
    register_filter_catalog_tables(target)
    mutator(target)
    before = _snapshot(target)
    with pytest.raises(
        RuntimeError, match="conflicting existing|partial filter catalog|mayak schema"
    ):
        register_filter_catalog_tables(target)
    assert _snapshot(target) == before, case_id
    assert tuple(target.tables) == before[3]


def test_exact_tables_and_canonical_order() -> None:
    target = _new_metadata()
    tables = register_filter_catalog_tables(target)
    assert tuple(table.name for table in tables) == NAMES
    assert tuple(target.tables) == EXPECTED_TABLE_KEYS


def test_empty_registration_creates_exactly_seven_tables() -> None:
    target = _new_metadata()
    assert len(register_filter_catalog_tables(target)) == 7
    assert tuple(target.tables) == EXPECTED_TABLE_KEYS


def test_three_correct_calls_preserve_table_identity_and_shape() -> None:
    target = _new_metadata()
    first = register_filter_catalog_tables(target)
    before = _snapshot(target)
    second = register_filter_catalog_tables(target)
    third = register_filter_catalog_tables(target)
    assert first == second == third
    assert tuple(map(id, first)) == tuple(map(id, second)) == tuple(map(id, third))
    assert _snapshot(target) == before


@pytest.mark.parametrize(
    "case_id", ["import", "registration"], ids=lambda value: f"no_db_io_{value}"
)
def test_import_and_registration_do_not_perform_db_io(
    monkeypatch: pytest.MonkeyPatch, case_id: str
) -> None:
    calls: list[str] = []
    monkeypatch.setattr("sqlalchemy.create_engine", lambda *a, **k: calls.append("engine"))
    monkeypatch.setattr("sqlalchemy.engine.Engine.connect", lambda *a, **k: calls.append("connect"))
    if case_id == "import":
        module_name = "mayak.persistence.schema.filter_catalog"
        cached_module = sys.modules[module_name]
        sys.modules.pop(module_name)
        try:
            fresh_module = importlib.import_module(module_name)
            assert fresh_module is not cached_module
            assert fresh_module.register_filter_catalog_tables.__module__ == module_name
            assert fresh_module.__dict__["_TABLE_NAMES"] == NAMES
        finally:
            sys.modules.pop(module_name, None)
            sys.modules[module_name] = cached_module
    else:
        register_filter_catalog_tables(_new_metadata())
    assert calls == []


@pytest.mark.parametrize(
    "case_id,mutator",
    [
        (
            "string_length",
            lambda m: setattr(
                m.tables["mayak.filter_definitions"].c.field_code, "type", String(127)
            ),
        ),
        (
            "string_collation",
            lambda m: setattr(
                m.tables["mayak.filter_definitions"].c.field_code.type, "collation", "C"
            ),
        ),
        (
            "jsonb_safe_metadata_none_as_null",
            lambda m: setattr(
                m.tables["mayak.filter_evidence_references"].c.safe_metadata,
                "type",
                postgresql.JSONB(none_as_null=True),
            ),
        ),
        (
            "jsonb_rule_none_as_null",
            lambda m: setattr(
                m.tables["mayak.filter_dependencies"].c.rule,
                "type",
                postgresql.JSONB(none_as_null=True),
            ),
        ),
        (
            "jsonb_capabilities_none_as_null",
            lambda m: setattr(
                m.tables["mayak.filter_capability_profiles"].c.capabilities,
                "type",
                postgresql.JSONB(none_as_null=True),
            ),
        ),
        (
            "uuid_as_uuid",
            lambda m: setattr(
                m.tables["mayak.filter_catalog_versions"].c.id,
                "type",
                postgresql.UUID(as_uuid=False),
            ),
        ),
        (
            "timestamp_timezone",
            lambda m: setattr(
                m.tables["mayak.filter_catalog_versions"].c.created_at,
                "type",
                postgresql.TIMESTAMP(timezone=False),
            ),
        ),
        (
            "mandatory_nullable",
            lambda m: setattr(m.tables["mayak.filter_options"].c.sort_order, "nullable", True),
        ),
        (
            "nullable_mandatory",
            lambda m: setattr(
                m.tables["mayak.filter_definitions"].c.evidence_id, "nullable", False
            ),
        ),
        (
            "wrong_server_default",
            lambda m: setattr(
                m.tables["mayak.filter_options"].c.sort_order, "server_default", text("1")
            ),
        ),
        (
            "extra_server_default",
            lambda m: setattr(
                m.tables["mayak.filter_options"].c.sort_order, "server_default", text("0")
            ),
        ),
        (
            "wrong_client_default",
            lambda m: setattr(
                m.tables["mayak.filter_options"].c.sort_order, "default", ColumnDefault(1)
            ),
        ),
        (
            "extra_client_default",
            lambda m: setattr(
                m.tables["mayak.filter_options"].c.sort_order, "default", ColumnDefault(0)
            ),
        ),
        (
            "onupdate",
            lambda m: setattr(
                m.tables["mayak.filter_options"].c.sort_order, "onupdate", ColumnDefault(1)
            ),
        ),
        (
            "server_onupdate",
            lambda m: setattr(
                m.tables["mayak.filter_options"].c.sort_order, "server_onupdate", text("1")
            ),
        ),
        (
            "column_comment",
            lambda m: setattr(m.tables["mayak.filter_options"].c.sort_order, "comment", "wrong"),
        ),
        (
            "primary_key_membership",
            lambda m: setattr(m.tables["mayak.filter_options"].c.sort_order, "primary_key", True),
        ),
    ],
    ids=lambda value: value if isinstance(value, str) else None,
)
def test_existing_column_conflicts_fail_closed(
    case_id: str, mutator: Callable[[MetaData], None]
) -> None:
    _reject(mutator, case_id)


def _constraint(target: MetaData, name: str, kind: type[Constraint]) -> Constraint:
    return next(
        constraint
        for table in target.tables.values()
        for constraint in table.constraints
        if constraint.name == name and isinstance(constraint, kind)
    )


def _filter_options(target: MetaData) -> Table:
    return target.tables["mayak.filter_options"]


def _replace_unique_columns(target: MetaData, columns: tuple[str, ...]) -> None:
    table = _filter_options(target)
    canonical = _constraint(
        target, "uq_filter_options_definition_option", UniqueConstraint
    )
    assert isinstance(canonical, UniqueConstraint)
    unrelated_before = {
        id(constraint): _constraint_signature(constraint)
        for constraint in table.constraints
        if constraint is not canonical
    }
    table.constraints.remove(canonical)
    replacement = UniqueConstraint(
        *columns,
        name=canonical.name,
        deferrable=canonical.deferrable,
        initially=canonical.initially,
        comment=canonical.comment,
        info=dict(canonical.info),
    )
    replacement._set_parent(table)
    corresponding = [
        constraint
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
        and constraint.name == "uq_filter_options_definition_option"
    ]
    assert len(corresponding) == 1
    assert corresponding[0] is replacement
    assert tuple(column.name for column in replacement.columns) == columns
    assert tuple(column.name for column in replacement.columns) != (
        "definition_id",
        "option_code",
    )
    assert {
        id(constraint): _constraint_signature(constraint)
        for constraint in table.constraints
        if constraint is not replacement
    } == unrelated_before


def _replace_filter_option_fk(target: MetaData, local_column: str) -> None:
    table = _filter_options(target)
    foreign_keys = tuple(table.foreign_key_constraints)
    assert len(foreign_keys) == 1
    canonical = foreign_keys[0]
    assert canonical.name == "fk_filter_options_definition_id_filter_definitions"
    element = canonical.elements[0]
    preserved = (
        element.target_fullname,
        canonical.ondelete,
        canonical.onupdate,
        canonical.deferrable,
        canonical.initially,
        canonical.use_alter,
        canonical.match,
        _options(canonical.dialect_options),
    )
    table.constraints.remove(canonical)
    for element in canonical.elements:
        table.foreign_keys.remove(element)
        element.parent.foreign_keys.remove(element)
    replacement = ForeignKeyConstraint(
        [local_column],
        [element.target_fullname],
        name=canonical.name,
        ondelete=canonical.ondelete,
        onupdate=canonical.onupdate,
        deferrable=canonical.deferrable,
        initially=canonical.initially,
        use_alter=canonical.use_alter,
        match=canonical.match,
        info=dict(canonical.info),
        comment=canonical.comment,
    )
    replacement._set_parent(table)
    relevant = tuple(table.foreign_key_constraints)
    assert len(relevant) == 1
    assert relevant[0] is replacement
    assert replacement.name == canonical.name
    assert tuple(element.parent.name for element in replacement.elements) == (local_column,)
    assert (
        replacement.elements[0].target_fullname,
        replacement.ondelete,
        replacement.onupdate,
        replacement.deferrable,
        replacement.initially,
        replacement.use_alter,
        replacement.match,
        _options(replacement.dialect_options),
    ) == preserved
    assert local_column != "definition_id"


def _mutate_live_fk_dialect_option(target: MetaData) -> None:
    table = _filter_options(target)
    foreign_keys = tuple(table.foreign_key_constraints)
    assert len(foreign_keys) == 1
    foreign_key = foreign_keys[0]
    identity = id(foreign_key)
    before = (
        foreign_key.name,
        tuple(element.parent.name for element in foreign_key.elements),
        tuple(element.target_fullname for element in foreign_key.elements),
        foreign_key.ondelete,
        foreign_key.onupdate,
        foreign_key.deferrable,
        foreign_key.initially,
        foreign_key.use_alter,
        foreign_key.match,
    )
    foreign_key.dialect_options["postgresql"]["not_valid"] = True
    assert id(foreign_key) == identity
    assert foreign_key in table.foreign_key_constraints
    assert len(table.foreign_key_constraints) == 1
    assert foreign_key.dialect_options["postgresql"]["not_valid"] is True
    assert (
        foreign_key.name,
        tuple(element.parent.name for element in foreign_key.elements),
        tuple(element.target_fullname for element in foreign_key.elements),
        foreign_key.ondelete,
        foreign_key.onupdate,
        foreign_key.deferrable,
        foreign_key.initially,
        foreign_key.use_alter,
        foreign_key.match,
    ) == before


def _canonical_applicability_index(target: MetaData) -> Index:
    table = target.tables["mayak.filter_category_applicability"]
    indexes = tuple(
        index
        for index in table.indexes
        if index.name == "ix_filter_category_applicability_catalog_category"
    )
    assert len(indexes) == 1
    return indexes[0]


def _index_expression_name(expression: object) -> str:
    return str(getattr(expression, "name", expression))


def _replace_applicability_index(target: MetaData, expressions: tuple[str, ...]) -> None:
    table = target.tables["mayak.filter_category_applicability"]
    canonical = _canonical_applicability_index(target)
    old_names = tuple(_index_expression_name(expression) for expression in canonical.expressions)
    assert len(old_names) == len(expressions)
    table.indexes.remove(canonical)
    replacement = Index(
        canonical.name,
        *(getattr(table.c, name) for name in expressions),
        unique=canonical.unique,
        info=dict(canonical.info),
    )
    replacement._set_parent(table)
    relevant = tuple(
        index for index in table.indexes if index.name == canonical.name
    )
    assert len(relevant) == 1
    assert relevant[0] is replacement
    replacement_names = tuple(
        _index_expression_name(expression) for expression in replacement.expressions
    )
    assert replacement_names == expressions
    assert replacement_names != old_names
    assert replacement.unique == canonical.unique


def _mutate_live_index_dialect_option(target: MetaData) -> None:
    table = _filter_options(target)
    indexes = tuple(table.indexes)
    assert len(indexes) == 1
    index = indexes[0]
    identity = id(index)
    before = (
        index.name,
        tuple(_index_expression_name(expression) for expression in index.expressions),
        index.unique,
        _normal(index.info),
    )
    index.dialect_options["postgresql"]["where"] = text("label IS NOT NULL")
    assert id(index) == identity
    assert index in table.indexes
    assert len(table.indexes) == 1
    assert index.dialect_options["postgresql"]["where"] is not None
    assert (
        index.name,
        tuple(_index_expression_name(expression) for expression in index.expressions),
        index.unique,
        _normal(index.info),
    ) == before


def _check_with_rule(target: MetaData) -> CheckConstraint:
    return next(
        c
        for c in target.tables["mayak.filter_dependencies"].constraints
        if isinstance(c, CheckConstraint) and "octet_length(rule" in str(c.sqltext)
    )


@pytest.mark.parametrize(
    "case_id,mutator",
    [
        (
            "missing_unique",
            lambda m: m.tables["mayak.filter_options"].constraints.remove(
                _constraint(m, "uq_filter_options_definition_option", UniqueConstraint)
            ),
        ),
        (
            "extra_unique",
            lambda m: UniqueConstraint("label", name="extra_unique")._set_parent(
                m.tables["mayak.filter_options"]
            ),
        ),
        (
            "unique_columns",
            lambda m: _replace_unique_columns(m, ("definition_id", "label")),
        ),
        (
            "unique_order",
            lambda m: _replace_unique_columns(m, ("option_code", "definition_id")),
        ),
        (
            "unique_name",
            lambda m: setattr(
                _constraint(m, "uq_filter_options_definition_option", UniqueConstraint),
                "name",
                "wrong_unique_name",
            ),
        ),
        (
            "unique_deferrable",
            lambda m: setattr(
                _constraint(m, "uq_filter_options_definition_option", UniqueConstraint),
                "deferrable",
                True,
            ),
        ),
        (
            "unique_initially",
            lambda m: setattr(
                _constraint(m, "uq_filter_options_definition_option", UniqueConstraint),
                "initially",
                "DEFERRED",
            ),
        ),
    ],
    ids=lambda value: value if isinstance(value, str) else None,
)
def test_existing_unique_conflicts_fail_closed(
    case_id: str, mutator: Callable[[MetaData], None]
) -> None:
    _reject(mutator, case_id)


@pytest.mark.parametrize(
    "case_id,mutator",
    [
        (
            "fk_name",
            lambda m: setattr(
                next(iter(m.tables["mayak.filter_options"].foreign_key_constraints)),
                "name",
                "wrong_fk",
            ),
        ),
        (
            "fk_local_column",
            lambda m: _replace_filter_option_fk(m, "label"),
        ),
        (
            "fk_target",
            lambda m: setattr(
                next(iter(m.tables["mayak.filter_options"].foreign_key_constraints)).elements[0],
                "_colspec",
                "mayak.filter_definitions.label",
            ),
        ),
        (
            "fk_ondelete",
            lambda m: setattr(
                next(iter(m.tables["mayak.filter_options"].foreign_key_constraints)),
                "ondelete",
                "CASCADE",
            ),
        ),
        (
            "fk_onupdate",
            lambda m: setattr(
                next(iter(m.tables["mayak.filter_options"].foreign_key_constraints)),
                "onupdate",
                "CASCADE",
            ),
        ),
        (
            "fk_deferrable",
            lambda m: setattr(
                next(iter(m.tables["mayak.filter_options"].foreign_key_constraints)),
                "deferrable",
                True,
            ),
        ),
        (
            "fk_initially",
            lambda m: setattr(
                next(iter(m.tables["mayak.filter_options"].foreign_key_constraints)),
                "initially",
                "DEFERRED",
            ),
        ),
        (
            "fk_use_alter",
            lambda m: setattr(
                next(iter(m.tables["mayak.filter_options"].foreign_key_constraints)),
                "use_alter",
                True,
            ),
        ),
        (
            "fk_match",
            lambda m: setattr(
                next(iter(m.tables["mayak.filter_options"].foreign_key_constraints)),
                "match",
                "FULL",
            ),
        ),
        (
            "fk_dialect_options",
            _mutate_live_fk_dialect_option,
        ),
    ],
    ids=lambda value: value if isinstance(value, str) else None,
)
def test_existing_foreign_key_conflicts_fail_closed(
    case_id: str, mutator: Callable[[MetaData], None]
) -> None:
    _reject(mutator, case_id)


@pytest.mark.parametrize(
    "case_id,mutator",
    [
        (
            "missing_check",
            lambda m: m.tables["mayak.filter_dependencies"].constraints.remove(_check_with_rule(m)),
        ),
        (
            "extra_check",
            lambda m: CheckConstraint("1 = 1", name="extra_check")._set_parent(
                m.tables["mayak.filter_dependencies"]
            ),
        ),
        ("wrong_check_sql", lambda m: setattr(_check_with_rule(m), "sqltext", text("1 = 1"))),
        ("wrong_check_name", lambda m: setattr(_check_with_rule(m), "name", "wrong_check")),
        ("check_deferrable", lambda m: setattr(_check_with_rule(m), "deferrable", True)),
        ("check_initially", lambda m: setattr(_check_with_rule(m), "initially", "DEFERRED")),
        (
            "unsupported_constraint",
            lambda m: ExcludeConstraint(
                (m.tables["mayak.filter_dependencies"].c.rule, "="), name="unsupported"
            )._set_parent(m.tables["mayak.filter_dependencies"]),
        ),
    ],
    ids=lambda value: value if isinstance(value, str) else None,
)
def test_existing_check_and_unsupported_conflicts_fail_closed(
    case_id: str, mutator: Callable[[MetaData], None]
) -> None:
    _reject(mutator, case_id)


def _replace_index(target: MetaData, mutate: Callable[[Index], None]) -> None:
    index = _canonical_applicability_index(target)
    mutate(index)


@pytest.mark.parametrize(
    "case_id,mutator",
    [
        (
            "missing_index",
            lambda m: m.tables["mayak.filter_options"].indexes.remove(
                next(iter(m.tables["mayak.filter_options"].indexes))
            ),
        ),
        (
            "extra_index",
            lambda m: Index("extra_index", m.tables["mayak.filter_options"].c.label)._set_parent(
                m.tables["mayak.filter_options"]
            ),
        ),
        (
            "index_columns",
            lambda m: _replace_applicability_index(m, ("catalog_version_id", "definition_id")),
        ),
        (
            "index_order",
            lambda m: _replace_applicability_index(m, ("category_code", "catalog_version_id")),
        ),
        (
            "index_name",
            lambda m: setattr(
                next(iter(m.tables["mayak.filter_options"].indexes)), "name", "wrong_index"
            ),
        ),
        (
            "index_unique",
            lambda m: setattr(next(iter(m.tables["mayak.filter_options"].indexes)), "unique", True),
        ),
        (
            "index_postgresql_option",
            _mutate_live_index_dialect_option,
        ),
    ],
    ids=lambda value: value if isinstance(value, str) else None,
)
def test_existing_index_conflicts_fail_closed(
    case_id: str, mutator: Callable[[MetaData], None]
) -> None:
    _reject(mutator, case_id)


@pytest.mark.parametrize(
    "case_id,mutator",
    [
        ("table_comment", lambda m: setattr(m.tables["mayak.filter_options"], "comment", "wrong")),
        ("table_info", lambda m: m.tables["mayak.filter_options"].info.update(wrong=True)),
        (
            "table_prefix",
            lambda m: setattr(m.tables["mayak.filter_options"], "prefixes", ("TEMP",)),
        ),
        (
            "table_dialect_option",
            lambda m: (
                m.tables["mayak.filter_options"]
                .dialect_options["postgresql"]
                .update(partition_by="label")
            ),
        ),
        ("table_schema", lambda m: setattr(m.tables["mayak.filter_options"], "schema", "public")),
        (
            "metadata_naming_convention",
            lambda m: m.naming_convention.update(ix="wrong_%(column_0_name)s"),
        ),
        ("metadata_info", lambda m: m.info.update(wrong=True)),
    ],
    ids=lambda value: value if isinstance(value, str) else None,
)
def test_existing_metadata_and_table_conflicts_fail_closed(
    case_id: str, mutator: Callable[[MetaData], None]
) -> None:
    _reject(mutator, case_id)


@pytest.mark.parametrize(
    "case_id,existing",
    [
        ("first", (0,)),
        ("middle", (3,)),
        ("last", (6,)),
        ("noncontiguous", (0, 2, 5)),
        ("all_but_one", (0, 1, 2, 3, 4, 5)),
        ("incompatible_partial", (0, 1, 2, 3, 4, 5)),
        ("with_foreign_table", (0, 1)),
    ],
    ids=lambda value: value if isinstance(value, str) else None,
)
def test_partial_registration_masks_fail_closed(case_id: str, existing: tuple[int, ...]) -> None:
    target = _new_metadata()
    for index in existing:
        Table(NAMES[index], target)
    if case_id == "with_foreign_table":
        Table("unrelated", target)
    elif case_id == "incompatible_partial":
        incompatible = target.tables["mayak.filter_options"]
        incompatible.append_column(Column("wrong", String(1)))
        assert len(existing) < len(NAMES)
        assert "mayak.filter_capability_profiles" not in target.tables
        assert "wrong" in incompatible.c
        assert tuple(target.tables) != EXPECTED_TABLE_KEYS
        assert isinstance(incompatible.c.wrong.type, String)
        assert incompatible.c.wrong.type.length == 1
    before = _snapshot(target)
    with pytest.raises(RuntimeError, match="partial filter catalog|conflicting existing"):
        register_filter_catalog_tables(target)
    assert _snapshot(target) == before


def test_full_registration_hidden_conflict_in_last_table_is_atomic() -> None:
    _reject(
        lambda m: setattr(
            m.tables["mayak.filter_capability_profiles"].c.profile_code, "nullable", True
        ),
        "last_category",
    )


def test_wrong_schema_is_fail_closed_without_mayak_objects() -> None:
    target = MetaData(schema="public", naming_convention=dict(NAMING_CONVENTION))
    before = _snapshot(target)
    with pytest.raises(RuntimeError, match="mayak schema"):
        register_filter_catalog_tables(target)
    assert _snapshot(target) == before
    assert not any(key.startswith("mayak.") for key in target.tables)


def test_global_registration_remains_canonical() -> None:
    assert tuple(table.name for table in register_filter_catalog_tables(metadata)) == NAMES
    assert all(table.schema == "mayak" for table in _tables(metadata))
