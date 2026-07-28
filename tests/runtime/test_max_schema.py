from __future__ import annotations

import importlib
from typing import Any, cast

import pytest
from sqlalchemy import CheckConstraint, Column, MetaData, String, Table, UniqueConstraint
from sqlalchemy.dialects import postgresql

from mayak.persistence.metadata import NAMING_CONVENTION, metadata
from mayak.persistence.schema.max import register_max_tables

NAMES = (
    "max_inbound_events",
    "max_identity_mappings",
    "max_delivery_mappings",
    "max_miniapp_nonces",
)
FORBIDDEN = (
    "token",
    "secret",
    "credential",
    "password",
    "cookie",
    "private_key",
    "raw",
    "payload",
    "body",
    "headers",
    "webhook",
    "polling",
    "human_read",
    "click",
    "merge",
    "fallback",
    "retry",
    "interval",
    "offset",
)


def isolated() -> MetaData:
    target = MetaData(schema="mayak", naming_convention=dict(NAMING_CONVENTION))
    for name in ("identity_provider_links", "notification_delivery_attempts", "identity_accounts"):
        Table(name, target, Column("id", postgresql.UUID(as_uuid=True), primary_key=True))
    return target


def tables() -> tuple[Table, Table, Table, Table]:
    return register_max_tables(isolated())


def checks(table: Table) -> set[str]:
    return {str(c.name) for c in table.constraints if isinstance(c, CheckConstraint)}


def uniques(table: Table) -> set[str]:
    return {str(c.name) for c in table.constraints if isinstance(c, UniqueConstraint)}


def predicate(index: Any) -> str:
    where = index.dialect_options["postgresql"].get("where")
    return (
        "" if where is None else " ".join(str(where.compile(dialect=postgresql.dialect())).split())
    )


def test_exact_tuple_order() -> None:
    assert tuple(t.name for t in tables()) == NAMES


def test_global_totals() -> None:
    assert (
        len(metadata.tables) == 48 and sum(len(t.indexes) for t in metadata.tables.values()) == 67
    )


def test_isolated_totals() -> None:
    value = tables()
    assert len(value) == 4 and sum(len(t.indexes) for t in value) == 5


def test_isolated_fk_total() -> None:
    assert sum(len(t.foreign_key_constraints) for t in tables()) == 3


@pytest.mark.parametrize(
    "table, expected",
    [
        (
            0,
            [
                "id",
                "provider_event_id",
                "event_fingerprint",
                "schema_version",
                "normalized_data",
                "received_at",
            ],
        ),
        (1, ["id", "provider_link_id", "max_user_ref", "created_at", "updated_at", "row_version"]),
        (2, ["id", "attempt_id", "max_message_ref", "created_at"]),
        (
            3,
            [
                "id",
                "nonce_hash",
                "account_id",
                "expires_at",
                "consumed_at",
                "created_at",
                "row_version",
            ],
        ),
    ],
)
def test_column_order(table: int, expected: list[str]) -> None:
    assert [c.name for c in tables()[table].columns] == expected


def test_schema_is_mayak() -> None:
    assert {t.schema for t in tables()} == {"mayak"}


def test_uuid_options_and_no_uuid_defaults() -> None:
    assert all(
        isinstance(t.c.id.type, postgresql.UUID)
        and t.c.id.type.as_uuid
        and t.c.id.server_default is None
        for t in tables()
    )


def test_postgres_types() -> None:
    inbound, identity, delivery, nonces = tables()
    assert isinstance(inbound.c.normalized_data.type, postgresql.JSONB)
    assert (
        isinstance(inbound.c.event_fingerprint.type, postgresql.CHAR)
        and inbound.c.event_fingerprint.type.length == 64
    )
    assert (
        isinstance(identity.c.max_user_ref.type, String)
        and identity.c.max_user_ref.type.length == 255
    )
    assert (
        isinstance(delivery.c.max_message_ref.type, String)
        and delivery.c.max_message_ref.type.length == 255
    )
    assert (
        isinstance(nonces.c.nonce_hash.type, postgresql.CHAR)
        and nonces.c.nonce_hash.type.length == 64
    )


@pytest.mark.parametrize("table", range(4))
def test_all_timestamp_columns_are_timezone_aware(table: int) -> None:
    assert all(
        not isinstance(c.type, postgresql.TIMESTAMP) or c.type.timezone
        for c in tables()[table].columns
    )


def test_exact_nullability() -> None:
    assert [c.nullable for c in tables()[0].columns] == [False] * 6
    assert [c.nullable for c in tables()[1].columns] == [False] * 6
    assert [c.nullable for c in tables()[2].columns] == [False, False, True, False]
    assert [c.nullable for c in tables()[3].columns] == [
        False,
        False,
        True,
        False,
        True,
        False,
        False,
    ]


def test_exact_defaults() -> None:
    assert [(t.name, c.name) for t in tables() for c in t.columns if c.server_default] == [
        ("max_identity_mappings", "row_version"),
        ("max_miniapp_nonces", "row_version"),
    ]
    assert all(
        c.server_default is None
        or str(getattr(getattr(c.server_default, "arg", None), "text", "")) == "1"
        for t in tables()
        for c in t.columns
    )


def test_primary_keys() -> None:
    assert all([c.name for c in t.primary_key.columns] == ["id"] for t in tables())


def test_fk_mappings() -> None:
    assert {
        (t.name, e.parent.name, e.target_fullname)
        for t in tables()
        for f in t.foreign_key_constraints
        for e in f.elements
    } == {
        ("max_identity_mappings", "provider_link_id", "mayak.identity_provider_links.id"),
        ("max_delivery_mappings", "attempt_id", "mayak.notification_delivery_attempts.id"),
        ("max_miniapp_nonces", "account_id", "mayak.identity_accounts.id"),
    }


def test_fk_actions_restrict() -> None:
    assert all(f.ondelete == "RESTRICT" for t in tables() for f in t.foreign_key_constraints)


def test_no_cascade() -> None:
    assert all(f.ondelete != "CASCADE" for t in tables() for f in t.foreign_key_constraints)


def test_exact_uniques() -> None:
    assert uniques(tables()[0]) == {"uq_max_inbound_events_provider_event_fingerprint"}
    assert uniques(tables()[1]) == {
        "uq_max_identity_mappings_max_user_ref",
        "uq_max_identity_mappings_provider_link_id",
    }
    assert uniques(tables()[2]) == {"uq_max_delivery_mappings_attempt_id"}
    assert uniques(tables()[3]) == {"uq_max_miniapp_nonces_nonce_hash"}


def test_exact_index_names() -> None:
    assert {i.name for t in tables() for i in t.indexes} == {
        "ix_max_inbound_events_provider_event_id",
        "ix_max_inbound_events_received_at",
        "ix_max_identity_mappings_provider_link_id",
        "ux_max_delivery_mappings_message_ref",
        "ix_max_miniapp_nonces_expires_at",
    }


def test_inbound_indexes() -> None:
    assert {i.name for i in tables()[0].indexes} == {
        "ix_max_inbound_events_provider_event_id",
        "ix_max_inbound_events_received_at",
    }


def test_identity_index() -> None:
    assert [i.name for i in tables()[1].indexes] == ["ix_max_identity_mappings_provider_link_id"]


def test_delivery_partial_unique_index() -> None:
    i = next(iter(tables()[2].indexes))
    assert (
        i.unique
        and [getattr(e, "name", "") for e in i.expressions] == ["max_message_ref"]
        and predicate(i) == "max_message_ref IS NOT NULL"
    )


def test_nonce_partial_index() -> None:
    i = next(iter(tables()[3].indexes))
    assert (
        not i.unique
        and [getattr(e, "name", "") for e in i.expressions] == ["expires_at"]
        and predicate(i) == "consumed_at IS NULL"
    )


def test_exact_checks() -> None:
    assert checks(tables()[0]) == {
        "provider_event_id_nonempty",
        "event_fingerprint_format",
        "schema_version_nonempty",
        "normalized_data_size",
    }
    assert checks(tables()[1]) == {"max_user_ref_nonempty", "row_version_positive"}
    assert checks(tables()[2]) == {"max_message_ref_nonempty_when_present"}
    assert checks(tables()[3]) == {
        "nonce_hash_format",
        "expires_after_created",
        "row_version_positive",
    }


@pytest.mark.parametrize("table", range(4))
def test_no_deferred_marker(table: int) -> None:
    assert "deferred_foreign_keys" not in tables()[table].info


def test_mutability_classification() -> None:
    assert (
        tables()[0].info == {}
        and tables()[1].info == {}
        and tables()[2].info == {}
        and tables()[3].info == {}
    )


def test_identity_is_referenced_not_owned() -> None:
    assert "account_id" not in tables()[1].c and "merge" not in " ".join(
        c.name for c in tables()[1].columns
    )


def test_notification_is_referenced_not_owned() -> None:
    assert "outbox_id" not in tables()[2].c and "state" not in tables()[2].c


def test_provider_identifiers_are_text() -> None:
    assert all(
        isinstance(t.c[n].type, String)
        for t, n in (
            (tables()[0], "provider_event_id"),
            (tables()[1], "max_user_ref"),
            (tables()[2], "max_message_ref"),
        )
    )


@pytest.mark.parametrize("word", FORBIDDEN)
def test_forbidden_policy_words_absent(word: str) -> None:
    haystack = " ".join(
        t.name + " " + " ".join(c.name for c in t.columns) for t in tables()
    ).lower()
    assert word not in haystack


def test_no_provider_payload_column() -> None:
    assert "normalized_data" in tables()[0].c and "raw_payload" not in tables()[0].c


def test_normalized_data_is_bounded() -> None:
    assert "normalized_data_size" in checks(tables()[0])


def test_fingerprints_are_lower_hex_checks() -> None:
    assert "event_fingerprint_format" in checks(tables()[0]) and "nonce_hash_format" in checks(
        tables()[3]
    )


def test_miniapp_data_is_not_authority() -> None:
    assert "auth" not in " ".join(c.name for c in tables()[3].columns).lower()


def test_webhook_boundary_not_persisted() -> None:
    assert not any("webhook" in c.name.lower() for t in tables() for c in t.columns)


def test_polling_boundary_not_persisted() -> None:
    assert not any("poll" in c.name.lower() for t in tables() for c in t.columns)


def test_first_registration_is_all_or_none() -> None:
    target = isolated()
    result = register_max_tables(target)
    assert tuple(t.name for t in result) == NAMES and all(
        target.tables[f"mayak.{n}"] is t for n, t in zip(NAMES, result)
    )


def test_replay_returns_identity() -> None:
    target = isolated()
    first = register_max_tables(target)
    second = register_max_tables(target)
    assert all(a is b for a, b in zip(first, second))


def test_equal_convention_replays() -> None:
    target = isolated()
    target.naming_convention = dict(NAMING_CONVENTION)
    assert register_max_tables(target)


def test_wrong_schema_rejected_before_mutation() -> None:
    target = isolated()
    target.schema = "other"
    before = tuple(target.tables)
    with pytest.raises(RuntimeError, match="require mayak"):
        register_max_tables(target)
    assert tuple(target.tables) == before


def test_wrong_convention_rejected() -> None:
    target = isolated()
    cast(dict[str, object], target.naming_convention)["ix"] = "wrong_%(column_0_label)s"
    with pytest.raises(RuntimeError, match="conflicting"):
        register_max_tables(target)


def test_nonempty_info_rejected() -> None:
    target = isolated()
    target.info["x"] = 1
    with pytest.raises(RuntimeError, match="conflicting"):
        register_max_tables(target)


@pytest.mark.parametrize(
    "missing", ("identity_provider_links", "notification_delivery_attempts", "identity_accounts")
)
def test_each_missing_prerequisite_rejected(missing: str) -> None:
    target = isolated()
    target.remove(target.tables[f"mayak.{missing}"])
    with pytest.raises(RuntimeError, match="missing max prerequisites"):
        register_max_tables(target)
    assert not any(n in target.tables for n in NAMES)


def test_partial_registration_rejected() -> None:
    target = isolated()
    Table(NAMES[0], target)
    with pytest.raises(RuntimeError, match="partial max"):
        register_max_tables(target)


def test_conflicting_order_rejected() -> None:
    target = isolated()
    [Table(n, target) for n in reversed(NAMES)]
    with pytest.raises(RuntimeError, match="partial max|order"):
        register_max_tables(target)


def test_conflicting_existing_column_rejected() -> None:
    target = isolated()
    register_max_tables(target)
    target.tables["mayak.max_inbound_events"].append_column(Column("wrong", postgresql.TEXT))
    with pytest.raises(RuntimeError, match="conflicting existing"):
        register_max_tables(target)


def test_conflicting_existing_index_rejected() -> None:
    target = isolated()
    register_max_tables(target)
    target.tables["mayak.max_inbound_events"].indexes.pop()
    with pytest.raises(RuntimeError, match="conflicting existing"):
        register_max_tables(target)


def test_rejected_registration_preserves_unrelated_identity() -> None:
    target = isolated()
    unrelated = Table("unrelated", target)
    before = tuple(target.tables.items())
    cast(dict[str, object], target.naming_convention)["ix"] = "bad"
    with pytest.raises(RuntimeError):
        register_max_tables(target)
    assert tuple(target.tables.items()) == before and target.tables["mayak.unrelated"] is unrelated


def test_prerequisite_identity_preserved() -> None:
    target = isolated()
    prerequisite = target.tables["mayak.identity_accounts"]
    result = register_max_tables(target)
    assert target.tables["mayak.identity_accounts"] is prerequisite and result


def test_registration_has_no_runtime_services() -> None:
    assert all(isinstance(t, Table) for t in register_max_tables(isolated()))


def test_import_exports_only_public_api() -> None:
    module = importlib.import_module("mayak.persistence.schema.max")
    assert module.__all__ == ["register_max_tables"]


def test_import_does_not_create_engine(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    monkeypatch.setattr("sqlalchemy.create_engine", lambda *a, **k: calls.append("engine"))
    importlib.import_module("mayak.persistence.schema.max")
    assert calls == []


def test_global_order_after_telegram() -> None:
    names = [k.rsplit(".", 1)[1] for k in metadata.tables]
    assert (
        names.index("telegram_delivery_mappings")
        < names.index("max_inbound_events")
        < names.index("max_miniapp_nonces")
    )


def test_scan_deferred_marker_unchanged() -> None:
    assert metadata.tables["mayak.scan_runs"].info["deferred_foreign_keys"]


def test_egress_deferred_marker_unchanged() -> None:
    assert metadata.tables["mayak.egress_route_leases"].info["deferred_foreign_keys"]


def test_no_max_deferred_marker_global() -> None:
    assert not any("deferred_foreign_keys" in t.info for t in tables())


def test_no_database_defaults_except_row_version() -> None:
    assert all(
        c.server_default is None or c.name == "row_version" for t in tables() for c in t.columns
    )


def test_no_enum_types() -> None:
    assert all("Enum" not in type(c.type).__name__ for t in tables() for c in t.columns)


def test_no_table_comments_or_info_policy() -> None:
    assert all(t.comment is None and t.info == {} for t in tables())


def test_all_max_fk_are_immediate() -> None:
    assert all(
        not f.use_alter and not f.deferrable for t in tables() for f in t.foreign_key_constraints
    )


def test_append_only_tables_have_no_row_version() -> None:
    assert "row_version" not in tables()[0].c and "row_version" not in tables()[2].c


def test_current_state_tables_have_row_version() -> None:
    assert "row_version" in tables()[1].c and "row_version" in tables()[3].c


def test_no_account_merge_fields() -> None:
    assert not any(
        c.name in {"phone", "username", "display_name", "avatar"}
        for t in tables()
        for c in t.columns
    )


def test_no_credentials_or_transport_fields() -> None:
    assert not any(
        any(term in c.name.lower() for term in ("credential", "header", "cookie", "key"))
        for t in tables()
        for c in t.columns
    )


def test_exact_index_predicate_count() -> None:
    assert sum(bool(predicate(i)) for t in tables() for i in t.indexes) == 2


def test_exact_unique_constraint_count() -> None:
    assert sum(len(uniques(t)) for t in tables()) == 5


def test_provider_acceptance_not_read_state() -> None:
    assert not any(
        c.name in {"read_at", "clicked_at", "business_success"} for t in tables() for c in t.columns
    )


def test_unknown_effect_not_blind_retry_state() -> None:
    assert not any(
        c.name in {"retry_count", "blind_retry", "provider_accepted"}
        for t in tables()
        for c in t.columns
    )


def test_no_provider_runtime_dependency_import() -> None:
    module = importlib.import_module("mayak.persistence.schema.max")
    assert "httpx" not in module.__dict__ and "requests" not in module.__dict__
