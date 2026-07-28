from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
from sqlalchemy import (
    CheckConstraint,
    Column,
    Index,
    MetaData,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects import postgresql

from mayak.persistence.metadata import NAMING_CONVENTION, metadata
from mayak.persistence.schema.support import register_support_tables

NAMES = ("support_cases", "support_case_notes", "support_case_events")
COLUMNS = (
    (
        "id",
        "account_id",
        "opened_by_account_id",
        "assigned_to_account_id",
        "state",
        "subject",
        "created_at",
        "updated_at",
        "row_version",
    ),
    ("id", "case_id", "author_account_id", "visibility", "body", "created_at"),
    ("id", "case_id", "actor_account_id", "event_code", "reason", "details", "created_at"),
)


def isolated() -> MetaData:
    target = MetaData(schema="mayak", naming_convention=dict(NAMING_CONVENTION))
    Table(
        "identity_accounts", target, Column("id", postgresql.UUID(as_uuid=True), primary_key=True)
    )
    return target


def tables() -> tuple[Table, Table, Table]:
    return register_support_tables(isolated())


def predicate(index: Index) -> str:
    where = index.dialect_options["postgresql"].get("where")
    return (
        "" if where is None else " ".join(str(where.compile(dialect=postgresql.dialect())).split())
    )


def checks(table: Table) -> dict[str, str]:
    return {
        str(c.name): " ".join(str(c.sqltext).split())
        for c in table.constraints
        if isinstance(c, CheckConstraint)
    }


def test_exact_tuple_order() -> None:
    assert tuple(table.name for table in tables()) == NAMES


@pytest.mark.parametrize("number, expected", list(enumerate(COLUMNS)))
def test_exact_column_order(number: int, expected: tuple[str, ...]) -> None:
    assert tuple(column.name for column in tables()[number].columns) == expected


def test_global_totals() -> None:
    assert len(metadata.tables) == 51
    assert sum(len(table.indexes) for table in metadata.tables.values()) == 72


def test_isolated_totals() -> None:
    value = tables()
    assert len(value) == 3 and sum(len(table.indexes) for table in value) == 5
    assert sum(len(table.foreign_key_constraints) for table in value) == 7


@pytest.mark.parametrize("number", [0, 1, 2])
def test_schema_and_primary_key(number: int) -> None:
    table = tables()[number]
    assert table.schema == "mayak"
    assert [column.name for column in table.primary_key.columns] == ["id"]
    assert isinstance(table.c.id.type, postgresql.UUID)
    assert table.c.id.type.as_uuid is True
    assert table.c.id.server_default is None and table.c.id.default is None


@pytest.mark.parametrize("number", [0, 1, 2])
def test_timestamps_are_timezone_aware(number: int) -> None:
    for column in tables()[number].columns:
        if isinstance(column.type, postgresql.TIMESTAMP):
            assert column.type.timezone is True


def test_case_types_nullability_and_default() -> None:
    table = tables()[0]
    assert isinstance(table.c.state.type, String) and table.c.state.type.length == 64
    assert isinstance(table.c.subject.type, Text)
    assert isinstance(table.c.row_version.type, postgresql.BIGINT)
    assert table.c.assigned_to_account_id.nullable is True
    assert all(
        table.c[name].nullable is False for name in COLUMNS[0] if name != "assigned_to_account_id"
    )
    assert table.c.row_version.server_default is not None
    assert str(getattr(table.c.row_version.server_default, "arg")) == "1"


def test_note_types_and_append_only_shape() -> None:
    table = tables()[1]
    assert isinstance(table.c.visibility.type, String) and table.c.visibility.type.length == 64
    assert isinstance(table.c.body.type, Text)
    assert "updated_at" not in table.c and "row_version" not in table.c
    assert not any(isinstance(c, UniqueConstraint) for c in table.constraints)


def test_event_types_and_append_only_shape() -> None:
    table = tables()[2]
    assert isinstance(table.c.event_code.type, String) and table.c.event_code.type.length == 64
    assert isinstance(table.c.details.type, postgresql.JSONB)
    assert table.c.actor_account_id.nullable is False and table.c.reason.nullable is False
    assert "updated_at" not in table.c and "row_version" not in table.c


def test_case_checks_are_exact() -> None:
    assert checks(tables()[0]) == {
        "state_nonempty": "btrim(state) <> ''",
        "subject_nonempty": "btrim(subject) <> ''",
        "row_version_positive": "row_version > 0",
    }


def test_note_checks_are_exact() -> None:
    assert checks(tables()[1]) == {
        "visibility_allowed": "visibility IN ('PUBLIC', 'INTERNAL')",
        "body_nonempty": "btrim(body) <> ''",
    }


def test_event_checks_are_exact() -> None:
    assert checks(tables()[2]) == {
        "event_code_nonempty": "btrim(event_code) <> ''",
        "reason_nonempty": "btrim(reason) <> ''",
        "details_size": "octet_length(details::text) <= 65536",
    }


def test_all_foreign_keys_are_immediate_restrict() -> None:
    for table in tables():
        for foreign_key in table.foreign_key_constraints:
            assert foreign_key.deferrable is None and foreign_key.initially is None
            assert foreign_key.ondelete == "RESTRICT"
            assert foreign_key.onupdate is None


def test_foreign_key_mappings_are_exact() -> None:
    actual = sorted(
        (table.name, element.parent.name, element.target_fullname, foreign_key.ondelete)
        for table in tables()
        for foreign_key in table.foreign_key_constraints
        for element in foreign_key.elements
    )
    assert actual == sorted(
        [
            ("support_cases", "account_id", "mayak.identity_accounts.id", "RESTRICT"),
            ("support_cases", "opened_by_account_id", "mayak.identity_accounts.id", "RESTRICT"),
            ("support_cases", "assigned_to_account_id", "mayak.identity_accounts.id", "RESTRICT"),
            ("support_case_notes", "case_id", "mayak.support_cases.id", "RESTRICT"),
            ("support_case_notes", "author_account_id", "mayak.identity_accounts.id", "RESTRICT"),
            ("support_case_events", "case_id", "mayak.support_cases.id", "RESTRICT"),
            ("support_case_events", "actor_account_id", "mayak.identity_accounts.id", "RESTRICT"),
        ]
    )


def test_no_unique_constraints_or_cascade() -> None:
    assert not any(isinstance(c, UniqueConstraint) for table in tables() for c in table.constraints)
    assert not any(
        fk.ondelete == "CASCADE" for table in tables() for fk in table.foreign_key_constraints
    )


def test_case_indexes_are_exact() -> None:
    value = {str(index.name): index for index in tables()[0].indexes}
    assert set(value) == {
        "ix_support_cases_open_pending_updated_at",
        "ix_support_cases_account_updated_at",
    }
    assert [e.name for e in value["ix_support_cases_open_pending_updated_at"].columns] == [
        "state",
        "updated_at",
    ]
    assert (
        predicate(value["ix_support_cases_open_pending_updated_at"])
        == "state IN ('OPEN', 'PENDING')"
    )
    assert predicate(value["ix_support_cases_account_updated_at"]) == ""
    assert all(index.unique is False for index in value.values())


@pytest.mark.parametrize(
    "number, expected",
    [
        (1, {"ix_support_case_notes_case_created_at": ["case_id", "created_at"]}),
        (
            2,
            {
                "ix_support_case_events_case_created_at": ["case_id", "created_at"],
                "ix_support_case_events_actor_created_at": ["actor_account_id", "created_at"],
            },
        ),
    ],
)
def test_child_indexes_are_exact(number: int, expected: dict[str, list[str]]) -> None:
    actual = tables()[number].indexes
    assert {str(index.name): [e.name for e in index.columns] for index in actual} == expected
    assert all(index.unique is False and predicate(index) == "" for index in actual)


@pytest.mark.parametrize(
    "word",
    [
        "password",
        "token",
        "secret",
        "credential",
        "cookie",
        "private_key",
        "shell_history",
        "raw_provider_payload",
        "http_headers",
        "one_time_code",
        "payment_details",
        "impersonation",
        "break_glass",
    ],
)
def test_forbidden_privacy_words_absent(word: str) -> None:
    for table in tables():
        haystack = " ".join(
            [
                table.name,
                *(column.name for column in table.columns),
                *(str(c.name) for c in table.constraints),
                *(str(i.name) for i in table.indexes),
            ]
        ).lower()
        assert word not in haystack


@pytest.mark.parametrize(
    "foreign_name",
    ["entitlement", "beacon", "scan", "egress", "notification", "telegram", "max", "filter"],
)
def test_no_foreign_domain_authority(foreign_name: str) -> None:
    assert not any(
        foreign_name in element.target_fullname.lower()
        for table in tables()
        for fk in table.foreign_key_constraints
        for element in fk.elements
    )


def test_identity_is_only_account_authority() -> None:
    assert "mayak.identity_accounts" in {
        element.target_fullname.rsplit(".id", 1)[0]
        for table in tables()
        for fk in table.foreign_key_constraints
        for element in fk.elements
    }
    assert not any(
        name in {column.name for table in tables() for column in table.columns}
        for name in ("role_id", "authorization_decision_id", "entitlement_id")
    )


def test_notes_visibility_is_explicitly_not_customer_authority() -> None:
    table = tables()[1]
    assert "customer_visible" not in table.c
    assert checks(table)["visibility_allowed"] == "visibility IN ('PUBLIC', 'INTERNAL')"
    assert "business_success" not in table.c


def test_events_are_history_not_foreign_mutation_authority() -> None:
    table = tables()[2]
    assert {c.name for c in table.columns} >= {"actor_account_id", "reason", "details"}
    assert not any(
        name in table.c
        for name in ("provider_payload", "provider_success", "command_id", "target_table")
    )


def test_no_deferred_support_marker() -> None:
    assert all("deferred_foreign_keys" not in table.info for table in tables())


def test_registration_replay_identity() -> None:
    target = isolated()
    first = register_support_tables(target)
    second = register_support_tables(target)
    assert all(left is right for left, right in zip(first, second))


def test_semantically_equal_naming_convention_replays() -> None:
    target = MetaData(schema="mayak", naming_convention=dict(NAMING_CONVENTION))
    Table(
        "identity_accounts", target, Column("id", postgresql.UUID(as_uuid=True), primary_key=True)
    )
    first = register_support_tables(target)
    assert register_support_tables(target) == first


@pytest.mark.parametrize(
    "target, message",
    [
        (MetaData(schema="public", naming_convention=dict(NAMING_CONVENTION)), "mayak schema"),
        (MetaData(schema="mayak", naming_convention={}), "metadata"),
    ],
)
def test_malformed_metadata_rejected_before_mutation(target: MetaData, message: str) -> None:
    before = tuple(target.tables)
    with pytest.raises(RuntimeError, match=message):
        register_support_tables(target)
    assert tuple(target.tables) == before


def test_nonempty_metadata_info_rejected() -> None:
    target = MetaData(schema="mayak", naming_convention=dict(NAMING_CONVENTION), info={"x": "y"})
    Table(
        "identity_accounts", target, Column("id", postgresql.UUID(as_uuid=True), primary_key=True)
    )
    before = tuple(target.tables)
    with pytest.raises(RuntimeError):
        register_support_tables(target)
    assert tuple(target.tables) == before


def test_missing_identity_rejected() -> None:
    target = MetaData(schema="mayak", naming_convention=dict(NAMING_CONVENTION))
    with pytest.raises(RuntimeError, match="identity_accounts"):
        register_support_tables(target)
    assert tuple(target.tables) == ()


@pytest.mark.parametrize("partial", ["support_cases", "support_case_notes"])
def test_partial_registration_rejected(partial: str) -> None:
    target = isolated()
    Table(partial, target, Column("id", postgresql.UUID(as_uuid=True), primary_key=True))
    before = tuple(target.tables)
    with pytest.raises(RuntimeError, match="partial"):
        register_support_tables(target)
    assert tuple(target.tables) == before


def test_unrelated_and_identity_identity_preserved() -> None:
    target = isolated()
    unrelated = Table(
        "unrelated", target, Column("id", postgresql.UUID(as_uuid=True), primary_key=True)
    )
    identity = target.tables["mayak.identity_accounts"]
    register_support_tables(target)
    assert target.tables["mayak.unrelated"] is unrelated
    assert target.tables["mayak.identity_accounts"] is identity


@pytest.mark.parametrize(
    "change", ["column", "type", "nullable", "default", "pk", "fk", "check", "index"]
)
def test_conflicts_are_rejected_without_replacement(change: str) -> None:
    target = isolated()
    register_support_tables(target)
    table = target.tables["mayak.support_cases"]
    if change == "column":
        table.append_column(Column("extra", String(1)))
    elif change == "type":
        table.c.state.type = String(63)
    elif change == "nullable":
        table.c.subject.nullable = True
    elif change == "default":
        table.c.row_version.server_default = None
    elif change == "pk":
        table.c.subject.primary_key = True
    elif change == "fk":
        next(iter(table.foreign_key_constraints)).ondelete = "CASCADE"
    elif change == "check":
        table.constraints.clear()
    else:
        table.indexes.clear()
    snapshot = tuple(target.tables), table
    with pytest.raises(RuntimeError):
        register_support_tables(target)
    assert (
        tuple(target.tables) == snapshot[0] and target.tables["mayak.support_cases"] is snapshot[1]
    )


def test_global_registration_order() -> None:
    names = tuple(table.name for table in metadata.tables.values())
    assert names[-3:] == NAMES
    assert names.index("max_inbound_events") < names.index("support_cases")


def test_existing_deferred_markers_unchanged() -> None:
    assert (
        metadata.tables["mayak.scan_runs"].info["deferred_foreign_keys"][0]["planned_revision"]
        == "RF09_FINALIZE"
    )
    assert (
        metadata.tables["mayak.egress_route_leases"].info["deferred_foreign_keys"][0][
            "planned_revision"
        ]
        == "RF09_FINALIZE"
    )


def test_import_is_database_inert(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    monkeypatch.setattr("sqlalchemy.create_engine", lambda *args, **kwargs: calls.append("engine"))
    monkeypatch.setattr(
        "sqlalchemy.engine.Engine.connect", lambda *args, **kwargs: calls.append("connect")
    )
    spec = importlib.util.spec_from_file_location(
        "support_isolated", Path(__file__).parents[2] / "src/mayak/persistence/schema/support.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert calls == [] and module.__all__ == ["register_support_tables"]


def test_no_support_table_comment_or_info_policy() -> None:
    assert all(table.comment is None and table.info == {} for table in tables())


def test_case_has_no_complete_state_enum() -> None:
    assert not any(
        isinstance(c, CheckConstraint) and "state IN" in str(c.sqltext)
        for c in tables()[0].constraints
    )


def test_notes_and_events_are_append_only_by_shape() -> None:
    for table in tables()[1:]:
        assert "updated_at" not in table.c
        assert "deleted_at" not in table.c
        assert "mutable_state" not in table.c


def test_public_does_not_bypass_policy() -> None:
    assert "authorization" not in {column.name for column in tables()[1].columns}
    assert "redaction" not in {column.name for column in tables()[1].columns}


def test_details_is_normalized_internal_json() -> None:
    table = tables()[2]
    assert table.c.details.nullable is False
    assert checks(table)["details_size"] == "octet_length(details::text) <= 65536"


def test_no_database_or_runtime_state_requirements() -> None:
    assert register_support_tables(isolated())[0].name == "support_cases"


def test_registration_does_not_duplicate_indexes() -> None:
    target = isolated()
    register_support_tables(target)
    indexes = [index.name for table in target.tables.values() for index in table.indexes]
    assert len(indexes) == len(set(indexes))


def test_fk_count_is_stable_on_replay() -> None:
    target = isolated()
    register_support_tables(target)
    first = sum(len(table.foreign_key_constraints) for table in target.tables.values())
    register_support_tables(target)
    assert sum(len(table.foreign_key_constraints) for table in target.tables.values()) == first


def test_no_support_unique_index() -> None:
    assert not any(index.unique for table in tables() for index in table.indexes)


def test_only_one_partial_index() -> None:
    assert sum(bool(predicate(index)) for table in tables() for index in table.indexes) == 1


def test_exact_support_table_names() -> None:
    assert {table.name for table in tables()} == set(NAMES)


def test_support_tables_have_no_foreign_business_columns() -> None:
    forbidden = {
        "beacon_id",
        "scan_id",
        "route_id",
        "notification_id",
        "telegram_id",
        "max_id",
        "filter_id",
    }
    assert not forbidden.intersection(
        {column.name for table in tables() for column in table.columns}
    )


def test_case_assignee_only_nullable_account_reference() -> None:
    assert tables()[0].c.assigned_to_account_id.nullable is True
    assert (
        tables()[0].c.account_id.nullable is False
        and tables()[0].c.opened_by_account_id.nullable is False
    )


def test_event_actor_is_required() -> None:
    assert tables()[2].c.actor_account_id.nullable is False


def test_reason_and_body_are_required() -> None:
    assert tables()[1].c.body.nullable is False and tables()[2].c.reason.nullable is False


def test_event_code_is_bounded() -> None:
    value = tables()[2].c.event_code.type
    assert isinstance(value, String) and value.length == 64


def test_state_is_bounded() -> None:
    value = tables()[0].c.state.type
    assert isinstance(value, String) and value.length == 64


def test_visibility_is_bounded() -> None:
    value = tables()[1].c.visibility.type
    assert isinstance(value, String) and value.length == 64


def test_subject_is_text_not_payload() -> None:
    assert isinstance(tables()[0].c.subject.type, Text)


def test_row_version_is_positive() -> None:
    assert checks(tables()[0])["row_version_positive"] == "row_version > 0"


def test_child_case_fks_are_restrict() -> None:
    assert all(
        fk.ondelete == "RESTRICT" for table in tables()[1:] for fk in table.foreign_key_constraints
    )


def test_no_support_deferred_info() -> None:
    assert all(table.info.get("deferred_foreign_keys") is None for table in tables())


def test_exact_index_total_per_table() -> None:
    assert [len(table.indexes) for table in tables()] == [2, 1, 2]


def test_no_python_defaults() -> None:
    assert all(column.default is None for table in tables() for column in table.columns)


def test_no_uuid_database_defaults() -> None:
    assert all(
        column.server_default is None
        for table in tables()
        for column in table.columns
        if isinstance(column.type, postgresql.UUID)
    )


def test_metadata_naming_is_canonical() -> None:
    target = isolated()
    assert target.naming_convention == NAMING_CONVENTION
    register_support_tables(target)
    assert target.naming_convention == NAMING_CONVENTION


def test_metadata_info_is_empty() -> None:
    assert all(table.info == {} for table in tables())


def test_migration_path_is_exact() -> None:
    assert (
        Path(__file__).parents[2] / "alembic/versions/20260728_RF09_M11_admin_support.py"
    ).is_file()


def test_migration_revision_identity() -> None:
    path = Path(__file__).parents[2] / "alembic/versions/20260728_RF09_M11_admin_support.py"
    text = path.read_text(encoding="utf-8")
    assert 'revision = "RF09_M11"' in text and 'down_revision = "RF09_M10"' in text


def test_support_has_no_provider_payload_columns() -> None:
    assert not any(
        "payload" in column.name or "request" in column.name or "response" in column.name
        for table in tables()
        for column in table.columns
    )


def test_support_has_no_role_or_authorization_tables() -> None:
    assert not any("role" in table.name or "authorization" in table.name for table in tables())


def test_support_case_note_does_not_claim_customer_visibility() -> None:
    assert "customer_visible" not in tables()[1].c


def test_event_existence_is_not_success() -> None:
    assert "success" not in {column.name for column in tables()[2].columns}


def test_cases_are_current_state_only() -> None:
    assert "state" in tables()[0].c and "updated_at" in tables()[0].c


def test_note_created_at_is_present() -> None:
    assert tables()[1].c.created_at.nullable is False


def test_event_created_at_is_present() -> None:
    assert tables()[2].c.created_at.nullable is False


def test_support_schema_does_not_create_engine() -> None:
    assert not hasattr(tables()[0].metadata, "bind")


def test_support_schema_does_not_require_identity_roles() -> None:
    assert set(isolated().tables) == {"mayak.identity_accounts"}


def test_support_schema_does_not_require_provider_credentials() -> None:
    assert all("credential" not in column.name for table in tables() for column in table.columns)


def test_support_schema_does_not_require_application_settings() -> None:
    assert tables()[0].metadata.info == {}


def test_support_schema_is_deterministic() -> None:
    first = [(table.name, tuple(column.name for column in table.columns)) for table in tables()]
    second = [(table.name, tuple(column.name for column in table.columns)) for table in tables()]
    assert first == second


def test_support_schema_isolated_foreign_target_set() -> None:
    assert {
        element.target_fullname
        for table in tables()
        for fk in table.foreign_key_constraints
        for element in fk.elements
    } == {"mayak.identity_accounts.id", "mayak.support_cases.id"}


def test_support_schema_no_duplicate_constraints() -> None:
    for table in tables():
        names = [str(constraint.name) for constraint in table.constraints]
        assert len(names) == len(set(names))


def test_support_schema_no_duplicate_columns() -> None:
    for table in tables():
        names = [column.name for column in table.columns]
        assert len(names) == len(set(names))


def test_support_schema_no_unique_flags() -> None:
    assert all(column.unique is not True for table in tables() for column in table.columns)


def test_support_schema_no_column_indexes() -> None:
    assert all(column.index is not True for table in tables() for column in table.columns)


def test_support_schema_no_triggers_or_procedures() -> None:
    assert all("trigger" not in table.info and "procedure" not in table.info for table in tables())


def test_support_schema_no_materialized_view() -> None:
    assert all(type(table).__name__ == "Table" for table in tables())


def test_support_schema_no_extensions() -> None:
    assert all("extension" not in table.info for table in tables())


def test_support_schema_no_attachment_payload() -> None:
    assert not any("attachment" in column.name for table in tables() for column in table.columns)


def test_support_schema_no_read_model_projection() -> None:
    assert not any(
        "projection" in column.name or "read_model" in column.name
        for table in tables()
        for column in table.columns
    )


def test_support_schema_no_command_envelope() -> None:
    assert not any("command" in column.name for table in tables() for column in table.columns)


def test_support_schema_no_evidence_table() -> None:
    assert not any("evidence" in table.name for table in tables())


def test_support_schema_no_retention_table() -> None:
    assert not any("retention" in table.name for table in tables())


def test_support_schema_no_operator_action_table() -> None:
    assert not any("operator_action" in table.name for table in tables())


def test_support_schema_no_foreign_mutation_table() -> None:
    assert not any("mutation" in table.name for table in tables())


def test_support_schema_no_customer_personal_data_column() -> None:
    assert not any(
        column.name in {"email", "name", "address", "birth_date"}
        for table in tables()
        for column in table.columns
    )


def test_support_schema_no_credential_value_column() -> None:
    assert not any(
        column.name.endswith("_secret") or column.name.endswith("_token")
        for table in tables()
        for column in table.columns
    )


def test_support_schema_no_onupdate() -> None:
    assert all(column.onupdate is None for table in tables() for column in table.columns)


def test_support_schema_no_server_onupdate() -> None:
    assert all(column.server_onupdate is None for table in tables() for column in table.columns)


def test_support_schema_has_exact_index_names() -> None:
    assert {index.name for table in tables() for index in table.indexes} == {
        "ix_support_cases_open_pending_updated_at",
        "ix_support_cases_account_updated_at",
        "ix_support_case_notes_case_created_at",
        "ix_support_case_events_case_created_at",
        "ix_support_case_events_actor_created_at",
    }


def test_support_schema_has_exact_fk_name_count() -> None:
    assert len({fk.name for table in tables() for fk in table.foreign_key_constraints}) == 7


def test_support_schema_no_index_predicate_on_children() -> None:
    assert all(predicate(index) == "" for table in tables()[1:] for index in table.indexes)


def test_support_schema_case_queue_is_nonunique() -> None:
    queue = next(
        index
        for index in tables()[0].indexes
        if index.name == "ix_support_cases_open_pending_updated_at"
    )
    assert queue.unique is False


def test_support_schema_case_account_index_is_nonunique() -> None:
    index = next(
        index
        for index in tables()[0].indexes
        if index.name == "ix_support_cases_account_updated_at"
    )
    assert index.unique is False


def test_support_schema_event_indexes_are_nonunique() -> None:
    assert all(index.unique is False for index in tables()[2].indexes)


def test_support_schema_note_index_is_nonunique() -> None:
    assert next(iter(tables()[1].indexes)).unique is False


def test_support_schema_is_not_bound() -> None:
    assert not hasattr(tables()[0].metadata, "bind")


def test_support_schema_replay_keeps_unrelated_order() -> None:
    target = isolated()
    unrelated = Table(
        "unrelated", target, Column("id", postgresql.UUID(as_uuid=True), primary_key=True)
    )
    register_support_tables(target)
    register_support_tables(target)
    assert tuple(target.tables)[1] == "mayak.unrelated"
    assert target.tables["mayak.unrelated"] is unrelated


def test_support_schema_no_foreign_table_writes() -> None:
    assert not any(column.name.endswith("_write") for table in tables() for column in table.columns)


def test_support_schema_notes_are_not_case_state() -> None:
    assert not {column.name for column in tables()[1].columns}.intersection(
        {"state", "status", "success"}
    )


def test_support_schema_events_are_not_case_state() -> None:
    assert not {column.name for column in tables()[2].columns}.intersection(
        {"state", "status", "success"}
    )


def test_support_schema_case_subject_nonempty() -> None:
    assert checks(tables()[0])["subject_nonempty"] == "btrim(subject) <> ''"


def test_support_schema_note_body_nonempty() -> None:
    assert checks(tables()[1])["body_nonempty"] == "btrim(body) <> ''"


def test_support_schema_event_reason_nonempty() -> None:
    assert checks(tables()[2])["reason_nonempty"] == "btrim(reason) <> ''"


def test_support_schema_event_code_nonempty() -> None:
    assert checks(tables()[2])["event_code_nonempty"] == "btrim(event_code) <> ''"


def test_support_schema_exact_fk_total_again() -> None:
    assert sum(len(table.foreign_key_constraints) for table in tables()) == 7


def test_support_schema_exact_table_total_again() -> None:
    assert len(tables()) == 3


def test_support_schema_exact_index_total_again() -> None:
    assert sum(len(table.indexes) for table in tables()) == 5


def test_support_schema_no_unique_constraint_again() -> None:
    assert (
        sum(
            isinstance(constraint, UniqueConstraint)
            for table in tables()
            for constraint in table.constraints
        )
        == 0
    )


def test_support_schema_import_public_surface() -> None:
    from mayak.persistence.schema import __all__

    assert "register_support_tables" in __all__
