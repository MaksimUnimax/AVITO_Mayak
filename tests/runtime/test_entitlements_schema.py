from __future__ import annotations

import importlib
from typing import Any

import pytest
from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Constraint,
    ForeignKeyConstraint,
    Index,
    MetaData,
    String,
    Table,
    text,
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import UniqueConstraint

from mayak.persistence.metadata import NAMING_CONVENTION, metadata
from mayak.persistence.schema.entitlements import register_entitlement_tables
from mayak.persistence.schema.identity import register_identity_tables
from mayak.persistence.schema.platform import register_platform_tables

NAMES = (
    "entitlement_tariff_definitions",
    "entitlement_access_grants",
    "entitlement_usage_counters",
    "billing_payment_records",
    "billing_payment_operations",
    "billing_reconciliations",
)


def _table(name: str) -> Table:
    return metadata.tables[f"mayak.{name}"]


def test_exact_tables_and_columns() -> None:
    tables = register_entitlement_tables(metadata)
    assert tuple(table.name for table in tables) == NAMES
    assert [tuple(table.c) for table in tables] == [
        tuple(table.c[name] for name in columns)
        for table, columns in zip(
            tables,
            (
                (
                    "id",
                    "code",
                    "version",
                    "price_minor",
                    "currency",
                    "min_interval_seconds",
                    "step_seconds",
                    "active_from",
                    "active_until",
                    "created_at",
                ),
                (
                    "id",
                    "account_id",
                    "tariff_id",
                    "source_code",
                    "grant_kind",
                    "granted_capability",
                    "granted_scope",
                    "reason",
                    "valid_from",
                    "valid_until",
                    "state",
                    "created_at",
                    "updated_at",
                    "row_version",
                ),
                (
                    "id",
                    "account_id",
                    "counter_code",
                    "window_start",
                    "window_end",
                    "consumed",
                    "limit_value",
                    "created_at",
                    "updated_at",
                    "row_version",
                ),
                (
                    "id",
                    "account_id",
                    "provider_code",
                    "external_payment_id",
                    "amount_minor",
                    "currency",
                    "state",
                    "observed_at",
                    "safe_metadata",
                    "created_at",
                    "updated_at",
                    "row_version",
                ),
                (
                    "id",
                    "payment_record_id",
                    "operation_code",
                    "idempotency_key",
                    "request_fingerprint",
                    "state",
                    "attempt_count",
                    "next_due_at",
                    "created_at",
                    "updated_at",
                    "row_version",
                ),
                (
                    "id",
                    "payment_record_id",
                    "operation_id",
                    "state",
                    "due_at",
                    "resolved_at",
                    "safe_metadata",
                    "created_at",
                    "row_version",
                ),
            ),
        )
    ]
    assert {table.schema for table in tables} == {"mayak"}
    assert all([column.name for column in table.primary_key.columns] == ["id"] for table in tables)


def test_types_defaults_and_immutable_shapes() -> None:
    for table in metadata.tables.values():
        for column in table.columns:
            if isinstance(column.type, postgresql.UUID):
                assert column.type.as_uuid is True
                assert column.server_default is None
    for name in NAMES:
        table = _table(name)
        assert [column.name for column in table.primary_key.columns] == ["id"]
        assert isinstance(table.c.id.type, postgresql.UUID)
        assert table.c.id.type.as_uuid is True
        assert table.c.id.server_default is None
    for name in NAMES:
        table = _table(name)
        for column in table.columns:
            if column.name.endswith("_at") or column.name in {
                "valid_from",
                "valid_until",
                "window_start",
                "window_end",
                "observed_at",
                "due_at",
                "resolved_at",
            }:
                assert isinstance(column.type, postgresql.TIMESTAMP)
                assert column.type.timezone is True
    assert isinstance(_table("billing_payment_records").c.safe_metadata.type, postgresql.JSONB)
    assert isinstance(_table("billing_reconciliations").c.safe_metadata.type, postgresql.JSONB)
    assert isinstance(_table("entitlement_tariff_definitions").c.currency.type, postgresql.CHAR)
    assert isinstance(_table("entitlement_tariff_definitions").c.version.type, BigInteger)
    assert _table("entitlement_access_grants").c.row_version.server_default.arg.text == "1"  # type: ignore[union-attr]
    assert _table("entitlement_usage_counters").c.consumed.server_default.arg.text == "0"  # type: ignore[union-attr]
    assert _table("entitlement_usage_counters").c.row_version.server_default.arg.text == "1"  # type: ignore[union-attr]
    assert _table("billing_payment_records").c.row_version.server_default.arg.text == "1"  # type: ignore[union-attr]
    assert _table("billing_payment_operations").c.attempt_count.server_default.arg.text == "0"  # type: ignore[union-attr]
    assert _table("billing_payment_operations").c.row_version.server_default.arg.text == "1"  # type: ignore[union-attr]
    assert _table("billing_reconciliations").c.row_version.server_default.arg.text == "1"  # type: ignore[union-attr]
    assert "updated_at" not in _table("entitlement_tariff_definitions").c
    assert "row_version" not in _table("entitlement_tariff_definitions").c
    assert "updated_at" not in _table("billing_reconciliations").c


def test_unique_constraints_and_nulls_not_distinct() -> None:
    expected = {
        "entitlement_tariff_definitions": "uq_entitlement_tariff_definitions_code_version",
        "entitlement_usage_counters": "uq_entitlement_usage_counters_account_code_window",
        "billing_payment_records": "uq_billing_payment_records_provider_external_payment",
        "billing_payment_operations": "uq_billing_payment_operations_payment_operation_idempotency",
        "billing_reconciliations": "uq_billing_reconciliations_payment_operation",
    }
    for name, constraint_name in expected.items():
        constraints = [c for c in _table(name).constraints if isinstance(c, UniqueConstraint)]
        assert {c.name for c in constraints} == {constraint_name}
    reconciliation_unique = next(
        c for c in _table("billing_reconciliations").constraints if isinstance(c, UniqueConstraint)
    )
    assert reconciliation_unique.dialect_options["postgresql"]["nulls_not_distinct"] is True


def test_foreign_keys_and_indexes() -> None:
    expected_fks = {
        "entitlement_access_grants": {
            "mayak.identity_accounts.id",
            "mayak.entitlement_tariff_definitions.id",
        },
        "entitlement_usage_counters": {"mayak.identity_accounts.id"},
        "billing_payment_records": {"mayak.identity_accounts.id"},
        "billing_payment_operations": {"mayak.billing_payment_records.id"},
        "billing_reconciliations": {
            "mayak.billing_payment_records.id",
            "mayak.billing_payment_operations.id",
        },
    }
    assert (
        sum(len(table.foreign_key_constraints) for table in (_table(name) for name in NAMES)) == 7
    )
    for name in NAMES:
        table = _table(name)
        assert all(fk.ondelete == "RESTRICT" for fk in table.foreign_key_constraints)
        assert {
            element.target_fullname
            for fk in table.foreign_key_constraints
            for element in fk.elements
        } == expected_fks.get(name, set())
    expected_indexes = {
        "entitlement_tariff_definitions": {"ix_entitlement_tariff_definitions_code_active_from"},
            "entitlement_access_grants": {
                "ix_entitlement_access_grants_account_valid_until",
                "ix_entitlement_access_grants_active",
                "ix_entitlement_access_grants_manual_capability_scope",
            },
        "entitlement_usage_counters": {"ix_entitlement_usage_counters_account_code_window_end"},
        "billing_payment_records": {
            "ix_billing_payment_records_account_observed_at",
            "ix_billing_payment_records_pending_unknown",
        },
        "billing_payment_operations": {"ix_billing_payment_operations_due"},
        "billing_reconciliations": {"ix_billing_reconciliations_unresolved_due"},
    }
    assert {index.name for name in NAMES for index in _table(name).indexes} == {
        name for names in expected_indexes.values() for name in names
    }
    predicates = {
        index.name: str(index.dialect_options["postgresql"].get("where"))
        for name in NAMES
        for index in _table(name).indexes
    }
    assert "state = 'ACTIVE'" in predicates["ix_entitlement_access_grants_active"]  # type: ignore[index]
    assert (
        "state IN ('PENDING', 'UNKNOWN')"
        in predicates["ix_billing_payment_records_pending_unknown"]  # type: ignore[index]
    )
    assert "state IN ('PENDING', 'RETRY')" in predicates["ix_billing_payment_operations_due"]  # type: ignore[index]
    assert "resolved_at IS NULL" in predicates["ix_billing_reconciliations_unresolved_due"]  # type: ignore[index]


def test_checks_encode_only_structural_safety() -> None:
    checks = {
        name: {str(c.sqltext) for c in _table(name).constraints if isinstance(c, CheckConstraint)}
        for name in NAMES
    }
    joined = " ".join(value for values in checks.values() for value in values)
    for expression in (
        "btrim(code)",
        "price_minor >= 0",
        "min_interval_seconds > 0",
        "step_seconds > 0",
        "active_until IS NULL",
        "valid_until > valid_from",
        "consumed >= 0",
        "limit_value >= 0",
        "window_end > window_start",
        "octet_length(safe_metadata::text) <= 8192",
        "request_fingerprint ~ '^[0-9a-f]{64}$'",
        "state <> 'UNKNOWN' OR next_due_at IS NULL",
    ):
        assert expression in joined
    assert all(
        not any(
            word in column.name.lower()
            for word in ("payload", "token", "secret", "cookie", "card", "bank")
        )
        for name in NAMES
        for column in _table(name).columns
    )
    assert "billing_payment_records" not in {
        element.target_fullname.split(".")[1]
        for fk in _table("entitlement_access_grants").foreign_key_constraints
        for element in fk.elements
    }


def test_registration_is_idempotent_and_inert(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    monkeypatch.setattr("sqlalchemy.create_engine", lambda *a, **k: calls.append("engine"))
    monkeypatch.setattr("sqlalchemy.engine.Engine.connect", lambda *a, **k: calls.append("connect"))
    first = register_entitlement_tables(metadata)
    second = register_entitlement_tables(metadata)
    assert first == second
    assert calls == []


def _prerequisite_metadata() -> MetaData:
    isolated = MetaData(schema="mayak", naming_convention=NAMING_CONVENTION)
    register_platform_tables(isolated)
    register_identity_tables(isolated)
    return isolated


def test_missing_or_partial_prerequisite_fails_before_mutation() -> None:
    missing = MetaData(schema="mayak", naming_convention=NAMING_CONVENTION)
    with pytest.raises(RuntimeError, match="identity table registration"):
        register_entitlement_tables(missing)
    assert not missing.tables
    partial = _prerequisite_metadata()
    Table("entitlement_tariff_definitions", partial)
    before = tuple(partial.tables)
    with pytest.raises(RuntimeError, match="partial entitlement"):
        register_entitlement_tables(partial)
    assert tuple(partial.tables) == before


def test_conflicting_existing_fk_fails_without_additional_mutation() -> None:
    isolated = _prerequisite_metadata()
    register_entitlement_tables(isolated)
    grants = isolated.tables["mayak.entitlement_access_grants"]
    ForeignKeyConstraint(
        [grants.c.account_id], ["mayak.identity_accounts.id"], name="conflict"
    )._set_parent(grants)
    before = tuple(isolated.tables)
    with pytest.raises(RuntimeError, match="conflicting existing entitlement_access_grants"):
        register_entitlement_tables(isolated)
    assert tuple(isolated.tables) == before


def _safe_snapshot(isolated: MetaData) -> tuple[object, ...]:
    def options(value: object) -> tuple[tuple[str, str], ...]:
        if not hasattr(value, "items"):
            return ()
        return tuple(
            sorted((str(key), str(option)) for key, option in value.items() if option is not None)
        )

    def predicate(index: Index) -> str | None:
        postgresql_options: Any = index.dialect_options.get("postgresql", {})
        value = postgresql_options.get("where")
        return str(value) if value is not None else None

    tables = []
    for name in NAMES:
        table = isolated.tables[f"mayak.{name}"]
        tables.append(
            (
                name,
                id(table),
                table.schema,
                table.comment,
                tuple(getattr(table, "prefixes", ())),
                table.implicit_returning,
                options(table.dialect_options),
                repr(table.info),
                tuple(
                    (
                        id(column),
                        column.name,
                        repr(column.type),
                        (
                            type(column.type).__module__,
                            type(column.type).__name__,
                            str(column.type.compile(dialect=postgresql.dialect())),
                            tuple(
                                (name, str(getattr(column.type, name)))
                                for name in (
                                    "length",
                                    "precision",
                                    "scale",
                                    "timezone",
                                    "as_uuid",
                                    "collation",
                                    "none_as_null",
                                    "hashable",
                                    "should_evaluate_none",
                                )
                                if hasattr(column.type, name)
                            ),
                        ),
                        column.nullable,
                        column.primary_key,
                        str(getattr(column.server_default, "arg", column.server_default))
                        if column.server_default is not None
                        else None,
                        str(getattr(column.default, "arg", column.default))
                        if column.default is not None
                        else None,
                        str(getattr(column.onupdate, "arg", column.onupdate))
                        if column.onupdate is not None
                        else None,
                        str(getattr(column.server_onupdate, "arg", column.server_onupdate))
                        if column.server_onupdate is not None
                        else None,
                        column.autoincrement,
                        column.unique,
                        column.index,
                        column.comment,
                        column.system,
                        repr(column.identity),
                        repr(column.computed),
                    )
                    for column in table.columns
                ),
                tuple(
                    sorted(
                        (
                            id(constraint),
                            type(constraint).__module__,
                            type(constraint).__name__,
                            constraint.name,
                            tuple(column.name for column in getattr(constraint, "columns", ())),
                            str(constraint.sqltext)
                            if isinstance(constraint, CheckConstraint)
                            else None,
                            getattr(constraint, "ondelete", None),
                            getattr(constraint, "onupdate", None),
                            getattr(constraint, "deferrable", None),
                            getattr(constraint, "initially", None),
                            getattr(constraint, "use_alter", None),
                            getattr(constraint, "match", None),
                            options(constraint.dialect_options),
                        )
                        for constraint in table.constraints
                    )
                ),
                tuple(
                    sorted(
                        (
                            id(foreign_key),
                            type(foreign_key).__module__,
                            type(foreign_key).__name__,
                            foreign_key.name,
                            tuple(element.parent.name for element in foreign_key.elements),
                            tuple(element.target_fullname for element in foreign_key.elements),
                            foreign_key.ondelete,
                            foreign_key.onupdate,
                            foreign_key.deferrable,
                            foreign_key.initially,
                            foreign_key.use_alter,
                            foreign_key.match,
                            options(foreign_key.dialect_options),
                        )
                        for foreign_key in table.foreign_key_constraints
                    )
                ),
                tuple(
                    sorted(
                        (
                            id(index),
                            type(index).__module__,
                            type(index).__name__,
                            index.name,
                            tuple(
                                getattr(column, "name", str(column)) for column in index.expressions
                            ),
                            index.unique,
                            predicate(index),
                            options(index.dialect_options),
                        )
                        for index in table.indexes
                    )
                ),
            )
        )
    return (tuple(isolated.tables), tuple(id(table) for table in isolated.tables.values()), *tables)


def _assert_existing_rejected_without_mutation(isolated: MetaData, mutate: object) -> None:
    assert callable(mutate)
    mutate()
    before = _safe_snapshot(isolated)
    with pytest.raises(RuntimeError, match="conflicting existing"):
        register_entitlement_tables(isolated)
    assert _safe_snapshot(isolated) == before


def test_existing_wrong_column_type_is_rejected_without_mutation() -> None:
    isolated = _prerequisite_metadata()
    register_entitlement_tables(isolated)
    _assert_existing_rejected_without_mutation(
        isolated,
        lambda: setattr(
            isolated.tables["mayak.billing_payment_records"].c.amount_minor, "type", String(20)
        ),
    )


def test_existing_string_collation_is_rejected_without_mutation() -> None:
    isolated = _prerequisite_metadata()
    register_entitlement_tables(isolated)
    _assert_existing_rejected_without_mutation(
        isolated,
        lambda: setattr(
            isolated.tables["mayak.billing_payment_records"].c.external_payment_id,
            "type",
            String(255, collation="C"),
        ),
    )


def test_existing_jsonb_none_as_null_is_rejected_without_mutation() -> None:
    isolated = _prerequisite_metadata()
    register_entitlement_tables(isolated)
    _assert_existing_rejected_without_mutation(
        isolated,
        lambda: setattr(
            isolated.tables["mayak.billing_payment_records"].c.safe_metadata,
            "type",
            postgresql.JSONB(none_as_null=True),
        ),
    )


def test_existing_client_default_is_rejected_without_mutation() -> None:
    isolated = _prerequisite_metadata()
    register_entitlement_tables(isolated)
    _assert_existing_rejected_without_mutation(
        isolated,
        lambda: setattr(
            isolated.tables["mayak.billing_payment_records"].c.provider_code,
            "default",
            text("'provider'"),
        ),
    )


def test_existing_column_comment_is_rejected_without_mutation() -> None:
    isolated = _prerequisite_metadata()
    register_entitlement_tables(isolated)
    _assert_existing_rejected_without_mutation(
        isolated,
        lambda: setattr(
            isolated.tables["mayak.billing_payment_records"].c.provider_code,
            "comment",
            "noncanonical",
        ),
    )


@pytest.mark.parametrize(
    "attribute,value",
    [
        ("onupdate", "CASCADE"),
        ("deferrable", True),
        ("initially", "DEFERRED"),
        ("use_alter", True),
        ("match", "FULL"),
    ],
)
def test_existing_foreign_key_extended_options_are_rejected_without_mutation(
    attribute: str, value: object
) -> None:
    isolated = _prerequisite_metadata()
    register_entitlement_tables(isolated)
    foreign_key = next(
        iter(isolated.tables["mayak.entitlement_access_grants"].foreign_key_constraints)
    )
    _assert_existing_rejected_without_mutation(
        isolated, lambda: setattr(foreign_key, attribute, value)
    )


def test_existing_unique_extended_options_are_rejected_without_mutation() -> None:
    isolated = _prerequisite_metadata()
    register_entitlement_tables(isolated)
    unique = next(
        c
        for c in isolated.tables["mayak.billing_payment_records"].constraints
        if isinstance(c, UniqueConstraint)
    )
    _assert_existing_rejected_without_mutation(
        isolated, lambda: setattr(unique, "deferrable", True)
    )


def test_existing_check_extended_options_are_rejected_without_mutation() -> None:
    isolated = _prerequisite_metadata()
    register_entitlement_tables(isolated)
    check = next(
        c
        for c in isolated.tables["mayak.billing_payment_operations"].constraints
        if isinstance(c, CheckConstraint)
    )
    _assert_existing_rejected_without_mutation(isolated, lambda: setattr(check, "deferrable", True))


def test_existing_unsupported_constraint_is_rejected_without_mutation() -> None:
    isolated = _prerequisite_metadata()
    register_entitlement_tables(isolated)
    table = isolated.tables["mayak.billing_payment_records"]
    table.append_constraint(Constraint(name="unsupported_extra"))
    before = _safe_snapshot(isolated)
    with pytest.raises(RuntimeError, match="conflicting existing billing_payment_records"):
        register_entitlement_tables(isolated)
    assert _safe_snapshot(isolated) == before
    assert any(c.name == "unsupported_extra" for c in table.constraints)


def test_existing_index_dialect_option_is_rejected_without_mutation() -> None:
    isolated = _prerequisite_metadata()
    register_entitlement_tables(isolated)
    index = next(
        index
        for index in isolated.tables["mayak.billing_payment_records"].indexes
        if index.name is not None and index.name.endswith("account_observed_at")
    )
    _assert_existing_rejected_without_mutation(
        isolated,
        lambda: index.dialect_options["postgresql"].update(include=["id"]),
    )


def test_existing_wrong_nullability_is_rejected_without_mutation() -> None:
    isolated = _prerequisite_metadata()
    register_entitlement_tables(isolated)
    _assert_existing_rejected_without_mutation(
        isolated,
        lambda: setattr(
            isolated.tables["mayak.entitlement_access_grants"].c.state, "nullable", True
        ),
    )


@pytest.mark.parametrize(
    "table_name,column_name,default",
    [
        ("entitlement_access_grants", "row_version", None),
        ("billing_payment_operations", "attempt_count", text("7")),
        ("billing_payment_records", "id", text("gen_random_uuid()")),
    ],
)
def test_existing_wrong_server_defaults_are_rejected_without_mutation(
    table_name: str, column_name: str, default: object
) -> None:
    isolated = _prerequisite_metadata()
    register_entitlement_tables(isolated)
    column = isolated.tables[f"mayak.{table_name}"].c[column_name]
    _assert_existing_rejected_without_mutation(
        isolated, lambda: setattr(column, "server_default", default)
    )


def test_existing_wrong_primary_key_is_rejected_without_mutation() -> None:
    isolated = _prerequisite_metadata()
    register_entitlement_tables(isolated)
    _assert_existing_rejected_without_mutation(
        isolated,
        lambda: setattr(
            isolated.tables["mayak.billing_reconciliations"].c.id, "primary_key", False
        ),
    )


def test_existing_unique_constraints_must_be_exact() -> None:
    isolated = _prerequisite_metadata()
    register_entitlement_tables(isolated)
    table = isolated.tables["mayak.billing_payment_records"]
    canonical = next(c for c in table.constraints if isinstance(c, UniqueConstraint))
    _assert_existing_rejected_without_mutation(
        isolated, lambda: table.constraints.remove(canonical)
    )

    isolated = _prerequisite_metadata()
    register_entitlement_tables(isolated)
    table = isolated.tables["mayak.billing_payment_records"]
    _assert_existing_rejected_without_mutation(
        isolated, lambda: UniqueConstraint("state", name="speculative_unique")._set_parent(table)
    )

    isolated = _prerequisite_metadata()
    register_entitlement_tables(isolated)
    table = isolated.tables["mayak.billing_payment_records"]
    _assert_existing_rejected_without_mutation(
        isolated,
        lambda: next(
            c for c in table.constraints if isinstance(c, UniqueConstraint)
        ).columns._collection.clear(),
    )


def test_reconciliation_nulls_not_distinct_is_required() -> None:
    isolated = _prerequisite_metadata()
    register_entitlement_tables(isolated)
    unique = next(
        c
        for c in isolated.tables["mayak.billing_reconciliations"].constraints
        if isinstance(c, UniqueConstraint)
    )
    unique.dialect_options["postgresql"]["nulls_not_distinct"] = False
    _assert_existing_rejected_without_mutation(isolated, lambda: None)


def test_existing_check_constraints_must_be_exact() -> None:
    isolated = _prerequisite_metadata()
    register_entitlement_tables(isolated)
    table = isolated.tables["mayak.billing_payment_operations"]
    canonical = next(c for c in table.constraints if isinstance(c, CheckConstraint))
    _assert_existing_rejected_without_mutation(
        isolated, lambda: table.constraints.remove(canonical)
    )

    isolated = _prerequisite_metadata()
    register_entitlement_tables(isolated)
    table = isolated.tables["mayak.billing_payment_operations"]
    _assert_existing_rejected_without_mutation(
        isolated, lambda: CheckConstraint("1 = 1", name="speculative_check")._set_parent(table)
    )

    isolated = _prerequisite_metadata()
    register_entitlement_tables(isolated)
    table = isolated.tables["mayak.billing_payment_operations"]
    canonical = next(c for c in table.constraints if isinstance(c, CheckConstraint))
    canonical.sqltext = text("attempt_count > 100")
    _assert_existing_rejected_without_mutation(isolated, lambda: None)


def test_existing_indexes_must_be_exact() -> None:
    isolated = _prerequisite_metadata()
    register_entitlement_tables(isolated)
    table = isolated.tables["mayak.billing_payment_records"]
    canonical = next(
        index
        for index in table.indexes
        if index.name is not None and index.name.endswith("account_observed_at")
    )
    _assert_existing_rejected_without_mutation(isolated, lambda: table.indexes.remove(canonical))

    isolated = _prerequisite_metadata()
    register_entitlement_tables(isolated)
    table = isolated.tables["mayak.billing_payment_records"]
    _assert_existing_rejected_without_mutation(
        isolated, lambda: Index("speculative_index", table.c.state)._set_parent(table)
    )

    isolated = _prerequisite_metadata()
    register_entitlement_tables(isolated)
    table = isolated.tables["mayak.billing_payment_records"]
    index = next(
        index
        for index in table.indexes
        if index.name is not None and index.name.endswith("account_observed_at")
    )
    index.expressions.reverse()  # type: ignore[attr-defined]
    _assert_existing_rejected_without_mutation(isolated, lambda: None)


def test_existing_partial_index_predicate_must_be_exact() -> None:
    isolated = _prerequisite_metadata()
    register_entitlement_tables(isolated)
    index = next(
        index
        for index in isolated.tables["mayak.entitlement_access_grants"].indexes
        if index.name is not None and index.name.endswith("_active")
    )
    index.dialect_options["postgresql"]["where"] = text("state = 'ENABLED'")
    _assert_existing_rejected_without_mutation(isolated, lambda: None)


@pytest.mark.parametrize("mutation", ["local", "name", "ondelete"])
def test_existing_foreign_keys_must_be_exact(mutation: str) -> None:
    isolated = _prerequisite_metadata()
    register_entitlement_tables(isolated)
    foreign_key = next(
        iter(isolated.tables["mayak.entitlement_access_grants"].foreign_key_constraints)
    )
    if mutation == "local":
        foreign_key.elements[0].parent = isolated.tables[
            "mayak.entitlement_access_grants"
        ].c.source_code
    elif mutation == "name":
        foreign_key.name = "wrong_foreign_key"
    else:
        foreign_key.ondelete = "CASCADE"
    _assert_existing_rejected_without_mutation(isolated, lambda: None)


def test_existing_canonical_registration_preserves_identities_on_three_calls() -> None:
    isolated = _prerequisite_metadata()
    first = register_entitlement_tables(isolated)
    identities = tuple(id(table) for table in first)
    snapshot = _safe_snapshot(isolated)
    assert tuple(register_entitlement_tables(isolated)) == first
    assert tuple(register_entitlement_tables(isolated)) == first
    assert tuple(id(table) for table in first) == identities
    assert _safe_snapshot(isolated) == snapshot


def test_import_is_deterministic_and_schema_is_global() -> None:
    assert importlib.import_module("mayak.persistence.schema.entitlements")
    assert {table.schema for table in metadata.tables.values()} == {"mayak"}
