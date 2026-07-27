from __future__ import annotations

import importlib

import pytest
from sqlalchemy import MetaData, Table
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CheckConstraint, UniqueConstraint

from mayak.persistence.metadata import NAMING_CONVENTION, metadata
from mayak.persistence.schema.identity import register_identity_tables
from mayak.persistence.schema.platform import register_platform_tables

NAMES = (
    "identity_accounts",
    "identity_provider_links",
    "identity_role_assignments",
    "identity_sessions",
    "identity_link_challenges",
)


def test_exact_identity_table_order_and_columns() -> None:
    tables = register_identity_tables(metadata)
    assert tuple(t.name for t in tables) == NAMES
    expected = {
        "identity_accounts": (
            "id",
            "phone",
            "state",
            "created_at",
            "updated_at",
            "row_version",
        ),
        "identity_provider_links": (
            "id",
            "account_id",
            "provider_code",
            "provider_subject",
            "state",
            "created_at",
            "updated_at",
            "row_version",
        ),
        "identity_role_assignments": (
            "id",
            "account_id",
            "role_code",
            "assigned_by_account_id",
            "reason",
            "created_at",
            "revoked_at",
        ),
        "identity_sessions": (
            "id",
            "account_id",
            "token_hash",
            "issued_at",
            "expires_at",
            "revoked_at",
            "created_at",
            "row_version",
        ),
        "identity_link_challenges": (
            "id",
            "account_id",
            "challenge_hash",
            "provider_code",
            "expires_at",
            "consumed_at",
            "created_at",
            "row_version",
        ),
    }
    assert {t.name: tuple(c.name for c in t.c) for t in tables} == {
        k: tuple(expected[k]) for k in expected
    }
    assert {t.schema for t in tables} == {"mayak"}
    assert all([c.name for c in t.primary_key.columns] == ["id"] for t in tables)


def test_types_defaults_nullable_and_no_database_uuid() -> None:
    for table in metadata.tables.values():
        assert isinstance(table.c.id.type, postgresql.UUID)
        assert table.c.id.server_default is None
        assert isinstance(table.c.created_at.type, postgresql.TIMESTAMP)
        assert table.c.created_at.type.timezone is True
    accounts = metadata.tables["mayak.identity_accounts"]
    assert accounts.c.phone.nullable is True
    assert accounts.c.row_version.server_default.arg.text == "1"  # type: ignore[union-attr]
    assert not any(
        isinstance(c, UniqueConstraint) and "phone" in {x.name for x in c.columns}
        for c in accounts.constraints
    )


def test_identity_constraints_foreign_keys_indexes_and_checks() -> None:
    links = metadata.tables["mayak.identity_provider_links"]
    roles = metadata.tables["mayak.identity_role_assignments"]
    sessions = metadata.tables["mayak.identity_sessions"]
    challenges = metadata.tables["mayak.identity_link_challenges"]
    assert {c.name for c in links.constraints if isinstance(c, UniqueConstraint)} == {
        "uq_identity_provider_links_provider_subject"
    }
    assert {c.name for c in roles.constraints if isinstance(c, UniqueConstraint)} == {
        "uq_identity_role_assignments_account_role_created"
    }
    assert {
        c.name for c in sessions.constraints if isinstance(c, UniqueConstraint)
    } == {"uq_identity_sessions_token_hash"}
    assert {
        c.name for c in challenges.constraints if isinstance(c, UniqueConstraint)
    } == {"uq_identity_link_challenges_challenge_hash"}
    assert (
        len(links.foreign_key_constraints) == 1
        and next(iter(links.foreign_key_constraints)).ondelete == "RESTRICT"
    )
    assert len(roles.foreign_key_constraints) == 2
    assert (
        len(sessions.foreign_key_constraints) == 1
        and next(iter(sessions.foreign_key_constraints)).ondelete == "RESTRICT"
    )
    assert (
        len(challenges.foreign_key_constraints) == 1
        and next(iter(challenges.foreign_key_constraints)).ondelete == "RESTRICT"
    )
    assert {i.name for i in metadata.tables["mayak.identity_accounts"].indexes} == {
        "ix_identity_accounts_phone",
        "ix_identity_accounts_state_created_at",
    }
    assert {i.name for i in roles.indexes} == {
        "ix_identity_role_assignments_active",
        "ix_identity_role_assignments_assigned_by_created_at",
    }
    checks = {
        table.name: {
            str(c.sqltext) for c in table.constraints if isinstance(c, CheckConstraint)
        }
        for table in (links, roles, sessions, challenges)
    }
    assert any(
        "provider_subject" in x and "255" in x
        for x in checks["identity_provider_links"]
    )
    assert any("24 hours" in x for x in checks["identity_sessions"])
    assert any("token_hash ~" in x for x in checks["identity_sessions"])
    assert any("challenge_hash ~" in x for x in checks["identity_link_challenges"])


def test_idempotent_registration_and_deferred_fk_resolution() -> None:
    first = register_identity_tables(metadata)
    second = register_identity_tables(metadata)
    assert first == second
    audit = metadata.tables["mayak.platform_audit_entries"]
    assert len(audit.foreign_key_constraints) == 1
    assert audit.c.actor_account_id.nullable is True
    assert "deferred_foreign_keys" not in audit.info


def test_partial_and_missing_platform_prerequisites_fail_closed() -> None:
    partial = MetaData(schema="mayak", naming_convention=NAMING_CONVENTION)
    register_platform_tables(partial)
    Table("identity_accounts", partial)
    with pytest.raises(RuntimeError, match="partial identity"):
        register_identity_tables(partial)
    assert list(partial.tables) == [
        "mayak.platform_idempotency_records",
        "mayak.platform_audit_entries",
        "mayak.platform_event_outbox",
        "mayak.identity_accounts",
    ]
    missing = MetaData(schema="mayak", naming_convention=NAMING_CONVENTION)
    with pytest.raises(RuntimeError, match="platform table registration"):
        register_identity_tables(missing)
    assert not missing.tables


def test_import_and_registration_are_inert(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    monkeypatch.setattr(
        "sqlalchemy.create_engine", lambda *a, **k: calls.append("engine")
    )
    monkeypatch.setattr(
        "sqlalchemy.engine.Engine.connect", lambda *a, **k: calls.append("connect")
    )
    assert importlib.import_module("mayak.persistence.schema.identity")
    register_identity_tables(metadata)
    assert calls == []


def test_forbidden_raw_secret_payload_columns_absent() -> None:
    forbidden = ("raw", "password", "secret", "cookie", "payload", "provider_token")
    for table_name in NAMES:
        for column in metadata.tables[f"mayak.{table_name}"].columns:
            assert not any(word in column.name.lower() for word in forbidden)


def test_role_assignments_are_append_style() -> None:
    table = metadata.tables["mayak.identity_role_assignments"]
    assert table.c.revoked_at.nullable is True
    assert table.c.created_at.nullable is False
