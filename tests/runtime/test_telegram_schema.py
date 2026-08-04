from __future__ import annotations

import importlib
from typing import Any, cast

import pytest
from sqlalchemy import CheckConstraint, Column, MetaData, String, Table, UniqueConstraint, text
from sqlalchemy.dialects import postgresql

from mayak.persistence.metadata import NAMING_CONVENTION, metadata
from mayak.persistence.schema.telegram import register_telegram_tables

NAMES = (
    "telegram_inbound_updates",
    "telegram_identity_mappings",
    "telegram_delivery_mappings",
)
FORBIDDEN = (
    "token",
    "secret",
    "cookie",
    "password",
    "private_key",
    "credential",
    "raw",
    "payload",
    "body",
    "html",
    "headers",
    "initdataunsafe",
    "webhook",
    "polling",
    "retry",
    "backoff",
    "rate",
    "command",
    "human_read",
    "click",
    "merge",
    "phone",
)


def isolated() -> MetaData:
    target = MetaData(schema="mayak", naming_convention=dict(NAMING_CONVENTION))
    Table(
        "identity_provider_links",
        target,
        Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
    )
    Table(
        "notification_delivery_attempts",
        target,
        Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
    )
    return target


def tables() -> tuple[Table, Table, Table]:
    return register_telegram_tables(isolated())


def checks(table: Table) -> set[str]:
    return {str(c.name) for c in table.constraints if isinstance(c, CheckConstraint)}


def uniques(table: Table) -> set[str]:
    return {str(c.name) for c in table.constraints if isinstance(c, UniqueConstraint)}


def predicate(index: Any) -> str:
    where = index.dialect_options["postgresql"].get("where")
    return (
        "" if where is None else " ".join(str(where.compile(dialect=postgresql.dialect())).split())
    )


def snapshot(target: MetaData) -> tuple[Any, ...]:
    return (
        target.schema,
        dict(target.naming_convention),
        dict(target.info),
        tuple(target.tables.items()),
        tuple(
            (id(t), tuple(id(c) for c in t.columns), tuple(id(i) for i in t.indexes))
            for t in target.tables.values()
        ),
    )


def test_exact_three_table_return_order() -> None:
    assert tuple(t.name for t in tables()) == NAMES


def test_exact_global_totals() -> None:
    assert len(metadata.tables) == 51
    assert sum(len(t.indexes) for t in metadata.tables.values()) == 73


def test_isolated_totals() -> None:
    value = tables()
    assert len(value) == 3
    assert sum(len(t.indexes) for t in value) == 4
    assert sum(len(t.foreign_key_constraints) for t in value) == 2


def test_inbound_column_order() -> None:
    assert [c.name for c in tables()[0].columns] == [
        "id",
        "provider_update_id",
        "event_fingerprint",
        "schema_version",
        "normalized_data",
        "received_at",
    ]


def test_identity_column_order() -> None:
    assert [c.name for c in tables()[1].columns] == [
        "id",
        "provider_link_id",
        "telegram_user_ref",
        "created_at",
        "updated_at",
        "row_version",
    ]


def test_delivery_column_order() -> None:
    assert [c.name for c in tables()[2].columns] == [
        "id",
        "attempt_id",
        "telegram_message_ref",
        "created_at",
    ]


def test_all_tables_use_mayak_schema() -> None:
    assert {t.schema for t in tables()} == {"mayak"}


def test_uuid_options_are_exact() -> None:
    for t in tables():
        assert cast(postgresql.UUID, t.c.id.type).as_uuid is True
        assert t.c.id.server_default is None


def test_inbound_types_are_exact() -> None:
    inbound = tables()[0]
    assert isinstance(inbound.c.id.type, postgresql.UUID)
    assert cast(String, inbound.c.provider_update_id.type).length == 255
    assert isinstance(inbound.c.event_fingerprint.type, postgresql.CHAR)
    assert cast(postgresql.CHAR, inbound.c.event_fingerprint.type).length == 64


def test_inbound_jsonb_and_timestamp() -> None:
    inbound = tables()[0]
    assert isinstance(inbound.c.normalized_data.type, postgresql.JSONB)
    assert isinstance(inbound.c.received_at.type, postgresql.TIMESTAMP)
    assert cast(postgresql.TIMESTAMP, inbound.c.received_at.type).timezone is True


def test_identity_types_are_exact() -> None:
    identity = tables()[1]
    assert isinstance(identity.c.provider_link_id.type, postgresql.UUID)
    assert cast(postgresql.UUID, identity.c.provider_link_id.type).as_uuid is True
    assert cast(String, identity.c.telegram_user_ref.type).length == 255
    assert identity.c.row_version.type.python_type is int


def test_delivery_types_are_exact() -> None:
    delivery = tables()[2]
    assert isinstance(delivery.c.attempt_id.type, postgresql.UUID)
    assert cast(String, delivery.c.telegram_message_ref.type).length == 255
    assert cast(postgresql.TIMESTAMP, delivery.c.created_at.type).timezone is True


def test_inbound_nullability() -> None:
    assert all(not c.nullable for c in tables()[0].columns)


def test_identity_nullability() -> None:
    assert [c.nullable for c in tables()[1].columns] == [False] * 6


def test_delivery_nullability() -> None:
    assert [c.nullable for c in tables()[2].columns] == [False, False, True, False]


def test_only_row_version_has_server_default() -> None:
    defaults = [
        (t.name, c.name) for t in tables() for c in t.columns if c.server_default is not None
    ]
    assert defaults == [("telegram_identity_mappings", "row_version")]


def test_row_version_default_is_one() -> None:
    assert tables()[1].c.row_version.server_default.arg.text == "1"  # type: ignore[union-attr]


def test_primary_keys_are_exact() -> None:
    assert [tuple(c.name for c in t.primary_key.columns) for t in tables()] == [("id",)] * 3


def test_identity_fk_target_and_action() -> None:
    fk = next(iter(tables()[1].foreign_key_constraints))
    assert [(e.parent.name, e.target_fullname) for e in fk.elements] == [
        ("provider_link_id", "mayak.identity_provider_links.id")
    ]
    assert fk.ondelete == "RESTRICT" and fk.onupdate is None and fk.deferrable is None


def test_delivery_fk_target_and_action() -> None:
    fk = next(iter(tables()[2].foreign_key_constraints))
    assert [(e.parent.name, e.target_fullname) for e in fk.elements] == [
        ("attempt_id", "mayak.notification_delivery_attempts.id")
    ]
    assert fk.ondelete == "RESTRICT" and fk.onupdate is None and fk.deferrable is None


def test_no_inbound_fks() -> None:
    assert not tables()[0].foreign_key_constraints


def test_no_cascade_actions() -> None:
    assert all(fk.ondelete != "CASCADE" for t in tables() for fk in t.foreign_key_constraints)


def test_inbound_uniques() -> None:
    assert uniques(tables()[0]) == {"uq_telegram_inbound_updates_provider_update_fingerprint"}
    unique = next(c for c in tables()[0].constraints if isinstance(c, UniqueConstraint))
    assert tuple(c.name for c in unique.columns) == ("provider_update_id", "event_fingerprint")


def test_identity_uniques() -> None:
    assert uniques(tables()[1]) == {
        "uq_telegram_identity_mappings_telegram_user_ref",
        "uq_telegram_identity_mappings_provider_link_id",
    }


def test_delivery_unique() -> None:
    assert uniques(tables()[2]) == {"uq_telegram_delivery_mappings_attempt_id"}


def test_exact_ordinary_unique_total() -> None:
    assert sum(len(uniques(t)) for t in tables()) == 4


def test_inbound_indexes() -> None:
    inbound = {i.name: i for i in tables()[0].indexes}
    assert set(inbound) == {
        "ix_telegram_inbound_updates_provider_update_id",
        "ix_telegram_inbound_updates_received_at",
    }
    assert all(not i.unique and predicate(i) == "" for i in inbound.values())


def test_identity_index() -> None:
    index = next(iter(tables()[1].indexes))
    assert index.name == "ix_telegram_identity_mappings_provider_link_id"
    assert [getattr(e, "name", None) for e in index.expressions] == ["provider_link_id"]
    assert index.unique is False and predicate(index) == ""


def test_delivery_partial_index() -> None:
    index = next(iter(tables()[2].indexes))
    assert index.name == "ux_telegram_delivery_mappings_message_ref"
    assert [getattr(e, "name", None) for e in index.expressions] == ["telegram_message_ref"]
    assert index.unique is True
    assert predicate(index) == "telegram_message_ref IS NOT NULL"


def test_exact_index_total() -> None:
    assert sum(len(t.indexes) for t in tables()) == 4


def test_inbound_checks() -> None:
    assert checks(tables()[0]) == {
        "provider_update_id_nonempty",
        "event_fingerprint_format",
        "schema_version_nonempty",
        "normalized_data_size",
    }


def test_identity_checks() -> None:
    assert checks(tables()[1]) == {"telegram_user_ref_nonempty", "row_version_positive"}


def test_delivery_checks() -> None:
    assert checks(tables()[2]) == {"telegram_message_ref_nonempty_when_present"}


def test_no_deferred_marker() -> None:
    assert all("deferred_foreign_keys" not in t.info for t in tables())


def test_external_refs_are_text() -> None:
    assert not isinstance(tables()[0].c.provider_update_id.type, postgresql.UUID)
    assert not isinstance(tables()[1].c.telegram_user_ref.type, postgresql.UUID)
    assert not isinstance(tables()[2].c.telegram_message_ref.type, postgresql.UUID)


def test_replay_identity_is_composite() -> None:
    unique = next(c for c in tables()[0].constraints if isinstance(c, UniqueConstraint))
    assert tuple(c.name for c in unique.columns) == ("provider_update_id", "event_fingerprint")
    assert "provider_update_id" not in {
        c.name
        for c in tables()[0].constraints
        if isinstance(c, UniqueConstraint) and len(c.columns) == 1
    }


def test_message_ref_is_nullable_correlation_only() -> None:
    assert tables()[2].c.telegram_message_ref.nullable is True


def test_normalized_data_is_bounded() -> None:
    assert "normalized_data_size" in checks(tables()[0])
    check = next(c for c in tables()[0].constraints if c.name == "normalized_data_size")
    assert "65536" in str(cast(CheckConstraint, check).sqltext)


def test_no_forbidden_names() -> None:
    for t in tables():
        names = (
            [c.name.lower() for c in t.columns]
            + [str(c.name).lower() for c in t.constraints]
            + [str(i.name).lower() for i in t.indexes]
        )
        assert not any(any(word in name for word in FORBIDDEN) for name in names)


def test_no_account_fk() -> None:
    assert all(
        "identity_accounts" not in e.target_fullname
        for t in tables()
        for fk in t.foreign_key_constraints
        for e in fk.elements
    )


def test_no_notification_outbox_fk() -> None:
    assert all(
        "notification_outbox" not in e.target_fullname
        for t in tables()
        for fk in t.foreign_key_constraints
        for e in fk.elements
    )


def test_no_foreign_domain_names() -> None:
    names = {t.name for t in tables()}
    assert not names.intersection(
        {"beacon_beacons", "scan_runs", "egress_routes", "parser_outcomes"}
    )


def test_registration_replay_returns_same_objects() -> None:
    target = isolated()
    first = register_telegram_tables(target)
    assert register_telegram_tables(target) == first
    assert all(register_telegram_tables(target)[n] is first[n] for n in range(3))


def test_semantically_equal_convention_is_accepted() -> None:
    target = MetaData(
        schema="mayak", naming_convention=dict(reversed(tuple(NAMING_CONVENTION.items())))
    )
    Table(
        "identity_provider_links",
        target,
        Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
    )
    Table(
        "notification_delivery_attempts",
        target,
        Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
    )
    assert tuple(t.name for t in register_telegram_tables(target)) == NAMES


def test_wrong_schema_fails_before_mutation() -> None:
    target = isolated()
    target.schema = "public"
    before = snapshot(target)
    with pytest.raises(RuntimeError):
        register_telegram_tables(target)
    assert snapshot(target) == before


def test_wrong_convention_fails_before_mutation() -> None:
    target = isolated()
    target.naming_convention = {"ix": "bad"}
    before = snapshot(target)
    with pytest.raises(RuntimeError):
        register_telegram_tables(target)
    assert snapshot(target) == before


def test_nonempty_info_fails_before_mutation() -> None:
    target = isolated()
    target.info["unexpected"] = True
    before = snapshot(target)
    with pytest.raises(RuntimeError):
        register_telegram_tables(target)
    assert snapshot(target) == before


@pytest.mark.parametrize("missing", ["identity_provider_links", "notification_delivery_attempts"])
def test_missing_prerequisite_fails(missing: str) -> None:
    target = isolated()
    target.remove(target.tables[f"mayak.{missing}"])
    before = snapshot(target)
    with pytest.raises(RuntimeError, match="missing telegram prerequisites"):
        register_telegram_tables(target)
    assert snapshot(target) == before


def test_partial_registration_fails_without_mutation() -> None:
    target = isolated()
    Table("telegram_inbound_updates", target)
    before = snapshot(target)
    with pytest.raises(RuntimeError, match="partial telegram"):
        register_telegram_tables(target)
    assert snapshot(target) == before


@pytest.mark.parametrize(
    "change", ["type", "nullable", "default", "pk", "unique", "check", "index"]
)
def test_conflicting_existing_shape_fails(change: str) -> None:
    target = isolated()
    first = register_telegram_tables(target)
    table = target.tables["mayak.telegram_inbound_updates"]
    if change == "type":
        table.c.provider_update_id.type = String(12)
    elif change == "nullable":
        table.c.provider_update_id.nullable = True
    elif change == "default":
        table.c.provider_update_id.server_default = cast(Any, text("'x'"))
    elif change == "pk":
        table.c.id.primary_key = False
    elif change == "unique":
        table.constraints.clear()
    elif change == "check":
        table.constraints.clear()
    else:
        table.indexes.clear()
    with pytest.raises(RuntimeError, match="conflicting existing telegram"):
        register_telegram_tables(target)
    assert first[0] is table


def test_unrelated_and_prerequisite_identity_is_preserved() -> None:
    target = isolated()
    unrelated = Table("unrelated", target, Column("id", String, primary_key=True))
    identity = target.tables["mayak.identity_provider_links"]
    attempt = target.tables["mayak.notification_delivery_attempts"]
    register_telegram_tables(target)
    assert target.tables["mayak.unrelated"] is unrelated
    assert target.tables["mayak.identity_provider_links"] is identity
    assert target.tables["mayak.notification_delivery_attempts"] is attempt


def test_repeated_malformed_registration_is_deterministic() -> None:
    target = MetaData(schema="public", naming_convention=dict(NAMING_CONVENTION))
    messages = []
    for _ in range(2):
        with pytest.raises(RuntimeError) as error:
            register_telegram_tables(target)
        messages.append(str(error.value))
    assert messages == ["telegram tables require mayak schema"] * 2


def test_import_does_not_create_engine_or_connect(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    monkeypatch.setattr("sqlalchemy.create_engine", lambda *a, **k: calls.append("engine"))
    monkeypatch.setattr("sqlalchemy.engine.Engine.connect", lambda *a, **k: calls.append("connect"))
    module = importlib.import_module("mayak.persistence.schema.telegram")
    assert module.register_telegram_tables and calls == []


def test_import_exports_only_public_registration() -> None:
    module = importlib.import_module("mayak.persistence.schema.telegram")
    assert module.__all__ == ["register_telegram_tables"]


def test_registration_does_not_need_provider_state() -> None:
    assert tuple(t.name for t in register_telegram_tables(isolated())) == NAMES


def test_registration_has_no_deferred_foreign_keys() -> None:
    assert sum(1 for t in tables() for f in t.foreign_key_constraints if f.deferrable) == 0


def test_identity_mapping_has_current_state_columns_only() -> None:
    assert [c.name for c in tables()[1].columns] == [
        "id",
        "provider_link_id",
        "telegram_user_ref",
        "created_at",
        "updated_at",
        "row_version",
    ]


def test_inbound_is_append_only_shape() -> None:
    assert "updated_at" not in tables()[0].c and "row_version" not in tables()[0].c


def test_delivery_is_append_only_shape() -> None:
    assert "updated_at" not in tables()[2].c and "row_version" not in tables()[2].c


def test_provider_acceptance_has_no_read_state() -> None:
    assert not any(
        "read" in c.name.lower() or "success" in c.name.lower() for t in tables() for c in t.columns
    )


def test_telegram_tables_do_not_own_account_state() -> None:
    assert not any(c.name == "account_id" for t in tables() for c in t.columns)


def test_telegram_tables_do_not_own_attempt_state() -> None:
    assert not any(
        c.name in {"state", "retry_count", "reconciliation_state"}
        for t in tables()
        for c in t.columns
    )


def test_metadata_order_follows_notification() -> None:
    names = [key.rsplit(".", 1)[1] for key in metadata.tables]
    assert (
        names.index("notification_delivery_reconciliations")
        < names.index("telegram_inbound_updates")
        < names.index("telegram_identity_mappings")
        < names.index("telegram_delivery_mappings")
    )


def test_notification_attempt_prerequisite_exists() -> None:
    assert "mayak.notification_delivery_attempts" in metadata.tables


def test_identity_link_prerequisite_exists() -> None:
    assert "mayak.identity_provider_links" in metadata.tables


def test_no_enum_types() -> None:
    assert not any(isinstance(c.type, postgresql.ENUM) for t in tables() for c in t.columns)


def test_no_speculative_index_types() -> None:
    assert all(
        str(i.name).startswith(("ix_telegram_", "ux_telegram_"))
        for t in tables()
        for i in t.indexes
    )


def test_table_comments_and_info_are_empty() -> None:
    assert all(t.comment is None and not t.info for t in tables())


def test_column_comments_and_info_are_empty() -> None:
    assert all(c.comment is None and not c.info for t in tables() for c in t.columns)
