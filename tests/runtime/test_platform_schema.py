from __future__ import annotations

import importlib

import pytest
from sqlalchemy import MetaData, Table
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CheckConstraint, ForeignKeyConstraint, UniqueConstraint

from mayak.persistence.metadata import NAMING_CONVENTION, metadata
from mayak.persistence.schema.platform import register_platform_tables

NAMES = ("platform_idempotency_records", "platform_audit_entries", "platform_event_outbox")


def test_exact_metadata_shape() -> None:
    assert metadata.schema == "mayak"
    assert set(metadata.tables) == {f"mayak.{name}" for name in NAMES}
    assert len(metadata.tables) == 3
    assert "identity_accounts" not in {table.name for table in metadata.tables.values()}
    assert metadata.naming_convention == NAMING_CONVENTION


def test_registration_is_idempotent() -> None:
    first = register_platform_tables(metadata)
    second = register_platform_tables(metadata)
    assert first == second
    assert len(metadata.tables) == 3
    assert sum(len(table.constraints) for table in metadata.tables.values()) == 17
    assert sum(len(table.indexes) for table in metadata.tables.values()) == 7


def test_partial_registration_fails_safely() -> None:
    partial = MetaData(schema="mayak", naming_convention=NAMING_CONVENTION)
    Table("platform_idempotency_records", partial)
    with pytest.raises(RuntimeError, match="partial platform table registration"):
        register_platform_tables(partial)
    assert list(partial.tables) == ["mayak.platform_idempotency_records"]


def test_import_is_deterministic_and_inert(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    monkeypatch.setattr("sqlalchemy.create_engine", lambda *a, **k: calls.append("engine"))
    monkeypatch.setattr("sqlalchemy.engine.Engine.connect", lambda *a, **k: calls.append("connect"))
    for name in ("mayak.persistence.schema.platform", "mayak.persistence.schema"):
        assert importlib.import_module(name)
    assert calls == []


def test_idempotency_columns_constraints_and_indexes() -> None:
    table = metadata.tables["mayak.platform_idempotency_records"]
    assert list(table.c) == [
        table.c[name]
        for name in (
            "id",
            "scope",
            "idempotency_key",
            "request_fingerprint",
            "result",
            "expires_at",
            "created_at",
        )
    ]
    assert isinstance(table.c.id.type, postgresql.UUID) and table.c.id.server_default is None
    assert (
        table.c.id.nullable is False
        and table.c.idempotency_key.type.length == 200  # type: ignore[attr-defined]
        and table.c.request_fingerprint.type.length == 64  # type: ignore[attr-defined]
    )
    assert {c.name for c in table.constraints if isinstance(c, UniqueConstraint)} == {
        "uq_platform_idempotency_records_scope_key"
    }
    assert {c.name for c in table.constraints if isinstance(c, CheckConstraint)} == {
        "ck_platform_idempotency_records_scope_nonempty",
        "ck_platform_idempotency_records_key_nonempty",
        "ck_platform_idempotency_records_fingerprint",
        "ck_platform_idempotency_records_result_size",
    }
    assert {i.name: [c.name for c in i.columns] for i in table.indexes} == {
        "ix_platform_idempotency_records_expires_at": ["expires_at"],
        "ix_platform_idempotency_records_scope_key": ["scope", "idempotency_key"],
    }


def test_audit_columns_constraints_indexes_and_deferred_marker() -> None:
    table = metadata.tables["mayak.platform_audit_entries"]
    assert [c.name for c in table.columns] == [
        "id",
        "actor_account_id",
        "action_code",
        "target_type",
        "target_id",
        "reason",
        "correlation_id",
        "details",
        "created_at",
    ]
    assert table.c.actor_account_id.nullable and table.c.target_id.nullable
    assert not [c for c in table.constraints if isinstance(c, ForeignKeyConstraint)]
    assert table.info == {
        "deferred_foreign_keys": (
            {
                "local_column": "actor_account_id",
                "target": "mayak.identity_accounts.id",
                "on_delete": "RESTRICT",
                "planned_revision": "RF09_M02",
            },
        )
    }
    assert {i.name for i in table.indexes} == {
        "ix_platform_audit_entries_created_at",
        "ix_platform_audit_entries_correlation_id",
        "ix_platform_audit_entries_actor_created_at",
    }


def test_outbox_columns_defaults_constraints_and_partial_indexes() -> None:
    table = metadata.tables["mayak.platform_event_outbox"]
    assert [c.name for c in table.columns] == [
        "id",
        "event_fingerprint",
        "contract_name",
        "contract_version",
        "payload",
        "state",
        "available_at",
        "lease_started_at",
        "lease_expires_at",
        "lease_token",
        "attempt_count",
        "created_at",
        "row_version",
    ]
    assert table.c.attempt_count.server_default.arg.text == "0"  # type: ignore[union-attr]
    assert table.c.row_version.server_default.arg.text == "1"  # type: ignore[union-attr]
    assert {c.name for c in table.constraints if isinstance(c, UniqueConstraint)} == {
        "uq_platform_event_outbox_event_fingerprint"
    }
    checks = {str(c.sqltext) for c in table.constraints if isinstance(c, CheckConstraint)}
    assert any("btrim(state)" in value for value in checks)
    assert not any("PENDING" in value or "RETRY" in value or "CLAIMED" in value for value in checks)
    assert {i.name for i in table.indexes} == {
        "ix_platform_event_outbox_available",
        "ix_platform_event_outbox_expired_lease",
    }
    predicates = {
        i.name: str(
            i.dialect_options["postgresql"]
            .get("where")
            .compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True})  # type: ignore[union-attr]
        )
        for i in table.indexes
    }
    assert "state IN ('PENDING', 'RETRY')" in predicates["ix_platform_event_outbox_available"]  # type: ignore[index]
    assert "state = 'CLAIMED'" in predicates["ix_platform_event_outbox_expired_lease"]  # type: ignore[index]


def test_no_forbidden_columns_or_database_uuid_defaults() -> None:
    forbidden = {"raw_payload", "provider_payload", "secret", "token", "cookie", "telegram", "max"}
    for table in metadata.tables.values():
        assert not [c for c in table.constraints if isinstance(c, ForeignKeyConstraint)]
        for column in table.columns:
            assert column.server_default is None or column.name in {"attempt_count", "row_version"}
            assert column.name == "lease_token" or not any(
                word in column.name.lower() for word in forbidden
            )


def test_metadata_registration_does_not_connect_or_execute_sql(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    monkeypatch.setattr("sqlalchemy.create_engine", lambda *a, **k: calls.append("engine"))
    monkeypatch.setattr("sqlalchemy.engine.Engine.connect", lambda *a, **k: calls.append("connect"))
    register_platform_tables(metadata)
    assert calls == []


def test_primary_keys_are_exactly_single_id_columns() -> None:
    for table in metadata.tables.values():
        assert [column.name for column in table.primary_key.columns] == ["id"]
        assert table.primary_key.columns.id.nullable is False


def test_required_type_families_are_postgresql_and_timezone_aware() -> None:
    for table in metadata.tables.values():
        assert isinstance(table.c.id.type, postgresql.UUID)
        assert isinstance(table.c.created_at.type, postgresql.TIMESTAMP)
        assert table.c.created_at.type.timezone is True
    assert isinstance(
        metadata.tables["mayak.platform_event_outbox"].c.payload.type, postgresql.JSONB
    )


def test_required_columns_have_no_server_generated_uuid() -> None:
    for table in metadata.tables.values():
        for column in table.columns:
            if isinstance(column.type, postgresql.UUID):
                assert column.server_default is None


def test_all_tables_use_mayak_schema() -> None:
    assert {table.schema for table in metadata.tables.values()} == {"mayak"}


def test_idempotency_has_no_actor_reference() -> None:
    assert "actor_account_id" not in metadata.tables["mayak.platform_idempotency_records"].c


def test_audit_and_outbox_have_expected_nullable_lease_fields() -> None:
    audit = metadata.tables["mayak.platform_audit_entries"]
    outbox = metadata.tables["mayak.platform_event_outbox"]
    assert audit.c.actor_account_id.nullable is True
    assert outbox.c.lease_started_at.nullable is True
    assert outbox.c.lease_expires_at.nullable is True
    assert outbox.c.lease_token.nullable is True


def test_outbox_has_no_exhaustive_state_check() -> None:
    checks = metadata.tables["mayak.platform_event_outbox"].constraints
    assert not any("state IN" in str(constraint) for constraint in checks)


def test_registration_returns_canonical_table_order() -> None:
    assert tuple(table.name for table in register_platform_tables(metadata)) == NAMES
