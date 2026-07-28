from __future__ import annotations

import importlib
from typing import Any

import pytest
from sqlalchemy import CheckConstraint, Column, MetaData, String, Table, UniqueConstraint
from sqlalchemy.dialects import postgresql

from mayak.persistence.metadata import NAMING_CONVENTION, metadata
from mayak.persistence.schema.notification import register_notification_tables

NAMES = (
    "notification_endpoints",
    "notification_events",
    "notification_outbox",
    "notification_delivery_attempts",
    "notification_delivery_reconciliations",
)
FORBIDDEN = (
    "payload_raw",
    "raw_payload",
    "body",
    "html",
    "headers",
    "cookies",
    "cookie",
    "credential",
    "secret",
    "password",
    "telegram_message_id",
    "max_message_id",
    "retry_delay",
    "backoff",
    "quiet_hours",
    "batching",
    "template",
    "read",
    "click",
    "egress_route_id",
    "parser_outcome_id",
    "baseline",
    "newness",
    "beacon_mutation",
)


def isolated() -> MetaData:
    target = MetaData(schema="mayak", naming_convention=dict(NAMING_CONVENTION))
    for name in ("identity_accounts", "beacon_beacons", "scan_runs"):
        Table(name, target, Column("id", postgresql.UUID(as_uuid=True), primary_key=True))
    return target


def tables() -> tuple[Table, ...]:
    target = isolated()
    return register_notification_tables(target)


def checks(table: Table) -> set[str]:
    return {str(item.name) for item in table.constraints if isinstance(item, CheckConstraint)}


def predicate(index: Any) -> str:
    where = index.dialect_options["postgresql"].get("where")
    if where is None:
        return ""
    return " ".join(
        str(
            where.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True})
        ).split()
    )


def snapshot(target: MetaData) -> tuple[Any, ...]:
    return (
        target.schema,
        dict(target.naming_convention),
        dict(target.info),
        tuple(target.tables.items()),
        tuple(
            (
                id(table),
                tuple((id(c), c.name) for c in table.constraints),
                tuple((id(i), i.name) for i in table.indexes),
            )
            for table in target.tables.values()
        ),
    )


def test_exact_return_order() -> None:
    assert tuple(item.name for item in tables()) == NAMES


def test_exact_isolated_totals() -> None:
    value = tables()
    assert len(value) == 5 and sum(len(item.indexes) for item in value) == 7
    assert sum(len(item.foreign_key_constraints) for item in value) == 8


def test_global_totals() -> None:
    assert len(metadata.tables) == 44
    assert sum(len(item.indexes) for item in metadata.tables.values()) == 62


def test_endpoint_columns() -> None:
    assert [item.name for item in tables()[0].columns] == [
        "id",
        "account_id",
        "provider_code",
        "endpoint_ref",
        "state",
        "created_at",
        "updated_at",
        "row_version",
    ]


def test_event_columns() -> None:
    assert [item.name for item in tables()[1].columns] == [
        "id",
        "account_id",
        "beacon_id",
        "run_id",
        "source_effect_fingerprint",
        "event_code",
        "payload",
        "created_at",
    ]


def test_outbox_columns() -> None:
    assert [item.name for item in tables()[2].columns] == [
        "id",
        "event_id",
        "endpoint_id",
        "state",
        "available_at",
        "lease_started_at",
        "lease_expires_at",
        "lease_token",
        "attempt_count",
        "created_at",
        "row_version",
    ]


def test_attempt_columns() -> None:
    assert [item.name for item in tables()[3].columns] == [
        "id",
        "outbox_id",
        "attempt_number",
        "state",
        "provider_reference",
        "effect_fingerprint",
        "started_at",
        "completed_at",
        "safe_metadata",
    ]


def test_reconciliation_columns() -> None:
    assert [item.name for item in tables()[4].columns] == [
        "id",
        "attempt_id",
        "state",
        "due_at",
        "resolved_at",
        "safe_metadata",
        "row_version",
    ]


def test_all_schema_names_are_mayak() -> None:
    assert {item.schema for item in tables()} == {"mayak"}


def test_uuid_options_and_no_uuid_defaults() -> None:
    for table in tables():
        for column in table.columns:
            if isinstance(column.type, postgresql.UUID):
                assert column.type.as_uuid is True and column.server_default is None


def test_timestamp_options() -> None:
    for table in tables():
        for column in table.columns:
            if isinstance(column.type, postgresql.TIMESTAMP):
                assert column.type.timezone is True


def test_json_fields_are_jsonb() -> None:
    assert isinstance(metadata.tables["mayak.notification_events"].c.payload.type, postgresql.JSONB)
    assert isinstance(
        metadata.tables["mayak.notification_delivery_attempts"].c.safe_metadata.type,
        postgresql.JSONB,
    )
    assert isinstance(
        metadata.tables["mayak.notification_delivery_reconciliations"].c.safe_metadata.type,
        postgresql.JSONB,
    )


def test_defaults_are_exact() -> None:
    assert (
        metadata.tables["mayak.notification_endpoints"].c.row_version.server_default.arg.text == "1"  # type: ignore[union-attr]
    )
    outbox = metadata.tables["mayak.notification_outbox"]
    assert outbox.c.attempt_count.server_default.arg.text == "0"  # type: ignore[union-attr]
    assert outbox.c.row_version.server_default.arg.text == "1"  # type: ignore[union-attr]
    assert (
        metadata.tables[
            "mayak.notification_delivery_reconciliations"
        ].c.row_version.server_default.arg.text  # type: ignore[union-attr]
        == "1"
    )  # type: ignore[union-attr]


def test_nullable_columns_are_exact() -> None:
    assert metadata.tables["mayak.notification_events"].c.beacon_id.nullable
    assert metadata.tables["mayak.notification_events"].c.run_id.nullable
    outbox = metadata.tables["mayak.notification_outbox"]
    assert (
        outbox.c.lease_started_at.nullable
        and outbox.c.lease_expires_at.nullable
        and outbox.c.lease_token.nullable
    )
    assert metadata.tables["mayak.notification_delivery_attempts"].c.provider_reference.nullable
    assert metadata.tables["mayak.notification_delivery_attempts"].c.completed_at.nullable
    assert metadata.tables["mayak.notification_delivery_reconciliations"].c.resolved_at.nullable


def test_primary_keys_are_exact() -> None:
    assert all([item.name for item in table.primary_key.columns] == ["id"] for table in tables())


def test_unique_constraints_are_exact() -> None:
    assert {
        item.name
        for table in tables()
        for item in table.constraints
        if isinstance(item, UniqueConstraint)
    } == {
        "uq_notification_endpoints_provider_endpoint",
        "uq_notification_events_source_effect_fingerprint",
        "uq_notification_outbox_event_endpoint",
        "uq_notification_delivery_attempts_outbox_attempt",
        "uq_notification_delivery_reconciliations_attempt_id",
    }


def test_endpoint_checks() -> None:
    assert checks(tables()[0]) == {
        "provider_code_nonempty",
        "endpoint_ref_nonempty",
        "state_nonempty",
        "row_version_positive",
    }


def test_event_checks() -> None:
    assert checks(tables()[1]) == {
        "source_effect_fingerprint_format",
        "event_code_nonempty",
        "payload_size",
    }


def test_outbox_checks() -> None:
    assert checks(tables()[2]) == {
        "attempt_nonnegative",
        "state_nonempty",
        "row_version_positive",
        "lease_window",
    }


def test_attempt_checks() -> None:
    assert checks(tables()[3]) == {
        "attempt_number_positive",
        "state_nonempty",
        "effect_fingerprint_format",
        "safe_metadata_size",
        "completion_order",
    }


def test_reconciliation_checks() -> None:
    assert checks(tables()[4]) == {"state_nonempty", "safe_metadata_size", "row_version_positive"}


def test_index_names_are_exact() -> None:
    assert {item.name for table in tables() for item in table.indexes} == {
        "ix_notification_endpoints_account_state",
        "ix_notification_events_account_created_at",
        "ix_notification_events_beacon_created_at",
        "ix_notification_outbox_due",
        "ix_notification_outbox_claimed_expiry",
        "ix_notification_delivery_attempts_outbox_started_at",
        "ix_notification_delivery_reconciliations_unresolved_due",
    }


def test_simple_index_expressions() -> None:
    value = tables()
    assert [getattr(item, "name", str(item)) for item in value[0].indexes.pop().expressions] == [
        "account_id",
        "state",
    ]


def test_event_index_expressions() -> None:
    indexes: dict[str, Any] = {str(item.name): item for item in tables()[1].indexes}
    assert [
        getattr(item, "name", str(item))
        for item in indexes["ix_notification_events_account_created_at"].expressions
    ] == ["account_id", "created_at"]
    assert [
        getattr(item, "name", str(item))
        for item in indexes["ix_notification_events_beacon_created_at"].expressions
    ] == ["beacon_id", "created_at"]


def test_outbox_index_predicates() -> None:
    indexes: dict[str, Any] = {str(item.name): item for item in tables()[2].indexes}
    assert [
        getattr(item, "name", str(item))
        for item in indexes["ix_notification_outbox_due"].expressions
    ] == [
        "available_at",
        "id",
    ]
    assert predicate(indexes["ix_notification_outbox_due"]) == "state IN ('PENDING', 'RETRY')"
    assert predicate(indexes["ix_notification_outbox_claimed_expiry"]) == "state = 'CLAIMED'"


def test_attempt_index() -> None:
    index = next(iter(tables()[3].indexes))
    assert index.name == "ix_notification_delivery_attempts_outbox_started_at"
    assert [getattr(item, "name", str(item)) for item in index.expressions] == [
        "outbox_id",
        "started_at",
    ]


def test_reconciliation_index() -> None:
    index = next(iter(tables()[4].indexes))
    assert index.name == "ix_notification_delivery_reconciliations_unresolved_due"
    assert [getattr(item, "name", str(item)) for item in index.expressions] == ["due_at"]
    assert predicate(index) == "resolved_at IS NULL"


def test_all_indexes_nonunique() -> None:
    assert all(item.unique is False for table in tables() for item in table.indexes)


def test_foreign_key_mappings() -> None:
    actual = {
        (item.parent.name, item.target_fullname, item.ondelete)
        for table in tables()
        for fk in table.foreign_key_constraints
        for item in fk.elements
    }
    assert actual == {
        ("account_id", "mayak.identity_accounts.id", "RESTRICT"),
        ("beacon_id", "mayak.beacon_beacons.id", "RESTRICT"),
        ("run_id", "mayak.scan_runs.id", "RESTRICT"),
        ("event_id", "mayak.notification_events.id", "RESTRICT"),
        ("endpoint_id", "mayak.notification_endpoints.id", "RESTRICT"),
        ("outbox_id", "mayak.notification_outbox.id", "RESTRICT"),
        ("attempt_id", "mayak.notification_delivery_attempts.id", "RESTRICT"),
    }
    assert len(actual) == 7


def test_composite_fk_count_is_eight_constraints() -> None:
    assert sum(len(table.foreign_key_constraints) for table in tables()) == 8


def test_no_cascade_or_deferred_fks() -> None:
    assert all(
        fk.ondelete == "RESTRICT" and not fk.deferrable
        for table in tables()
        for fk in table.foreign_key_constraints
    )
    assert all("deferred_foreign_keys" not in table.info for table in tables())


def test_outboxes_are_distinct_objects() -> None:
    assert (
        metadata.tables["mayak.platform_event_outbox"]
        is not metadata.tables["mayak.notification_outbox"]
    )


def test_outbox_has_only_generic_ownership_fks() -> None:
    outbox = metadata.tables["mayak.notification_outbox"]
    assert {
        (item.parent.name, item.target_fullname)
        for fk in outbox.foreign_key_constraints
        for item in fk.elements
    } == {
        ("event_id", "mayak.notification_events.id"),
        ("endpoint_id", "mayak.notification_endpoints.id"),
    }


def test_scan_and_egress_deferred_markers_survive() -> None:
    assert metadata.tables["mayak.scan_runs"].info["deferred_foreign_keys"]
    assert metadata.tables["mayak.egress_route_leases"].info["deferred_foreign_keys"]


def test_no_notification_deferred_marker() -> None:
    assert all("deferred_foreign_keys" not in table.info for table in tables())


def test_no_enum_types() -> None:
    assert all(
        "Enum" not in type(column.type).__name__ for table in tables() for column in table.columns
    )


def test_no_speculative_index_types() -> None:
    assert all(
        "gin" not in str(index.dialect_options).lower()
        and "brin" not in str(index.dialect_options).lower()
        for table in tables()
        for index in table.indexes
    )


def test_no_forbidden_column_names() -> None:
    assert not any(
        term in column.name.lower()
        for table in tables()
        for column in table.columns
        for term in FORBIDDEN
    )


def test_no_forbidden_metadata_strings() -> None:
    text = repr(
        [(table.name, table.info, [column.name for column in table.columns]) for table in tables()]
    )
    assert not any(term in text.lower() for term in FORBIDDEN)


def test_provider_reference_is_bounded_generic_string() -> None:
    column = metadata.tables["mayak.notification_delivery_attempts"].c.provider_reference
    assert isinstance(column.type, String) and column.type.length == 255


def test_safe_metadata_sizes_are_bounded() -> None:
    assert "safe_metadata_size" in checks(metadata.tables["mayak.notification_delivery_attempts"])
    assert "safe_metadata_size" in checks(
        metadata.tables["mayak.notification_delivery_reconciliations"]
    )


def test_notification_import_is_inert(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    monkeypatch.setattr("sqlalchemy.create_engine", lambda *args, **kwargs: calls.append("engine"))
    monkeypatch.setattr(
        "sqlalchemy.engine.Engine.connect", lambda *args, **kwargs: calls.append("connect")
    )
    assert importlib.import_module("mayak.persistence.schema.notification")
    assert calls == []


def test_first_registration_replay_identity() -> None:
    target = isolated()
    first = register_notification_tables(target)
    second = register_notification_tables(target)
    assert all(left is right for left, right in zip(first, second))


def test_semantically_equal_convention_copy() -> None:
    target = isolated()
    assert tuple(item.name for item in register_notification_tables(target)) == NAMES


def test_convention_insertion_order_variation() -> None:
    convention = {key: NAMING_CONVENTION[key] for key in reversed(tuple(NAMING_CONVENTION))}
    target = MetaData(schema="mayak", naming_convention=convention)
    for name in ("identity_accounts", "beacon_beacons", "scan_runs"):
        Table(name, target, Column("id", postgresql.UUID(as_uuid=True), primary_key=True))
    assert tuple(item.name for item in register_notification_tables(target)) == NAMES


def test_wrong_schema_rejected_before_mutation() -> None:
    target = MetaData(schema="other", naming_convention=NAMING_CONVENTION)
    before = snapshot(target)
    with pytest.raises(RuntimeError):
        register_notification_tables(target)
    assert snapshot(target) == before


def test_wrong_convention_rejected_before_mutation() -> None:
    target = MetaData(schema="mayak", naming_convention={"ix": "wrong"})
    before = snapshot(target)
    with pytest.raises(RuntimeError):
        register_notification_tables(target)
    assert snapshot(target) == before


def test_nonempty_metadata_info_rejected_before_mutation() -> None:
    target = isolated()
    target.info["unexpected"] = True
    before = snapshot(target)
    with pytest.raises(RuntimeError):
        register_notification_tables(target)
    assert snapshot(target) == before


def test_missing_each_prerequisite_fails() -> None:
    for missing in ("identity_accounts", "beacon_beacons", "scan_runs"):
        target = MetaData(schema="mayak", naming_convention=NAMING_CONVENTION)
        for name in ("identity_accounts", "beacon_beacons", "scan_runs"):
            if name != missing:
                Table(name, target, Column("id", postgresql.UUID(as_uuid=True), primary_key=True))
        with pytest.raises(RuntimeError, match="missing notification prerequisites"):
            register_notification_tables(target)
        assert not any(name in key for key in target.tables if name in NAMES)


def test_partial_registration_fails_without_mutation() -> None:
    target = isolated()
    Table("notification_endpoints", target)
    before = snapshot(target)
    with pytest.raises(RuntimeError, match="partial notification"):
        register_notification_tables(target)
    assert snapshot(target) == before


def test_conflicting_table_rejected() -> None:
    target = isolated()
    Table("notification_endpoints", target, Column("wrong", String(1)))
    for name in NAMES[1:]:
        Table(name, target)
    before = snapshot(target)
    with pytest.raises(RuntimeError, match="conflicting existing notification"):
        register_notification_tables(target)
    assert snapshot(target) == before


def test_repeated_malformed_registration_is_deterministic() -> None:
    target = MetaData(schema="wrong", naming_convention=NAMING_CONVENTION)
    messages = []
    for _ in range(2):
        with pytest.raises(RuntimeError) as error:
            register_notification_tables(target)
        messages.append(str(error.value))
    assert messages[0] == messages[1]


def test_unrelated_identity_preserved() -> None:
    target = isolated()
    unrelated = Table(
        "unrelated", target, Column("id", postgresql.UUID(as_uuid=True), primary_key=True)
    )
    assert register_notification_tables(target)
    assert target.tables["mayak.unrelated"] is unrelated


def test_no_database_or_settings_access(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def record_env(*args: Any, **kwargs: Any) -> None:
        calls.append("env")

    monkeypatch.setattr("sqlalchemy.create_engine", lambda *args, **kwargs: calls.append("engine"))
    monkeypatch.setattr(
        "sqlalchemy.engine.Engine.connect", lambda *args, **kwargs: calls.append("connect")
    )
    monkeypatch.setattr("os.getenv", record_env)
    register_notification_tables(isolated())
    assert calls == []


def test_no_runtime_behavior_exports() -> None:
    module = importlib.import_module("mayak.persistence.schema.notification")
    assert module.__all__ == ["register_notification_tables"]


def test_registration_does_not_require_parser() -> None:
    target = isolated()
    assert "mayak.parser_outcomes" not in target.tables
    assert register_notification_tables(target)[0].name == "notification_endpoints"


def test_event_is_immutable_shape() -> None:
    event = metadata.tables["mayak.notification_events"]
    assert "updated_at" not in event.c and "row_version" not in event.c


def test_attempt_is_append_only_shape() -> None:
    attempt = metadata.tables["mayak.notification_delivery_attempts"]
    assert (
        "created_at" not in attempt.c
        and "updated_at" not in attempt.c
        and "row_version" not in attempt.c
    )


def test_reconciliation_has_no_retry_policy_columns() -> None:
    table = metadata.tables["mayak.notification_delivery_reconciliations"]
    assert not any(
        name in table.c for name in ("retry_count", "retry_delay", "backoff", "blind_retry")
    )


def test_endpoints_have_no_credentials() -> None:
    assert not any(
        term in column.name.lower()
        for column in metadata.tables["mayak.notification_endpoints"].columns
        for term in ("token", "cookie", "secret", "password", "credential")
    )


def test_payload_is_generic_event_payload_only() -> None:
    event = metadata.tables["mayak.notification_events"]
    assert {column.name for column in event.c} == {
        "id",
        "account_id",
        "beacon_id",
        "run_id",
        "source_effect_fingerprint",
        "event_code",
        "payload",
        "created_at",
    }


def test_no_platform_outbox_fk() -> None:
    assert not any(
        "platform_event_outbox" in element.target_fullname
        for table in tables()
        for fk in table.foreign_key_constraints
        for element in fk.elements
    )


def test_no_egress_ownership() -> None:
    assert not any(
        "egress_" in element.target_fullname
        for table in tables()
        for fk in table.foreign_key_constraints
        for element in fk.elements
    )


def test_no_parser_authority() -> None:
    assert not any(
        "parser_outcomes" in element.target_fullname or "parser_outcome" in column.name
        for table in tables()
        for column in table.columns
        for fk in table.foreign_key_constraints
        for element in fk.elements
    )


def test_no_scan_state_ownership() -> None:
    assert {
        element.target_fullname
        for table in tables()
        for fk in table.foreign_key_constraints
        for element in fk.elements
        if "scan_" in element.target_fullname
    } == {"mayak.scan_runs.id"}


def test_no_provider_specific_state() -> None:
    assert not any(
        provider in column.name.lower()
        for table in tables()
        for column in table.columns
        for provider in ("telegram", "max", "chat_id", "message_id")
    )


def test_no_read_or_click_proof() -> None:
    assert not any(
        term in column.name.lower()
        for table in tables()
        for column in table.columns
        for term in ("read", "clicked", "opened", "ack")
    )


def test_no_channel_policy() -> None:
    assert not any(
        term in column.name.lower()
        for table in tables()
        for column in table.columns
        for term in ("priority", "fallback", "quiet", "batch", "template")
    )


def test_metadata_registration_order() -> None:
    names = [key.rsplit(".", 1)[1] for key in metadata.tables]
    assert names.index("parser_outcomes") < names.index("notification_endpoints")


def test_all_required_prerequisites_exist_globally() -> None:
    assert all(
        f"mayak.{name}" in metadata.tables
        for name in ("identity_accounts", "beacon_beacons", "scan_runs")
    )


def test_event_nullable_ownership_is_explicit() -> None:
    event = metadata.tables["mayak.notification_events"]
    assert event.c.account_id.nullable is False
    assert event.c.beacon_id.nullable is True and event.c.run_id.nullable is True


def test_lease_window_check_is_present() -> None:
    assert "lease_window" in checks(metadata.tables["mayak.notification_outbox"])


def test_completion_order_check_is_present() -> None:
    assert "completion_order" in checks(metadata.tables["mayak.notification_delivery_attempts"])


def test_safe_metadata_is_not_raw_provider_data() -> None:
    assert all(
        column.name == "safe_metadata"
        for table in tables()[3:]
        for column in table.columns
        if isinstance(column.type, postgresql.JSONB)
    )


def test_registration_returns_tables_not_runtime_services() -> None:
    assert all(isinstance(item, Table) for item in register_notification_tables(isolated()))


def test_metadata_has_exact_notification_inventory() -> None:
    assert (
        tuple(
            key.rsplit(".", 1)[1]
            for key in metadata.tables
            if key.rsplit(".", 1)[1].startswith("notification_")
        )
        == NAMES
    )


def test_no_notification_engine_symbol() -> None:
    module = importlib.import_module("mayak.persistence.schema.notification")
    assert not hasattr(module, "engine") and not hasattr(module, "connection")
