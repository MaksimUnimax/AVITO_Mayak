from __future__ import annotations

import importlib
from copy import deepcopy
from pathlib import Path

import pytest
from sqlalchemy import ForeignKeyConstraint, MetaData, Table
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CheckConstraint, CreateTable, UniqueConstraint

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
        for column in table.columns:
            if isinstance(column.type, postgresql.UUID):
                assert column.type.as_uuid is True
                assert column.server_default is None
            if column.name == "created_at":
                assert isinstance(column.type, postgresql.TIMESTAMP)
                assert column.type.timezone is True
    accounts = metadata.tables["mayak.identity_accounts"]
    assert [column.name for column in accounts.primary_key.columns] == ["id"]
    assert isinstance(accounts.c.id.type, postgresql.UUID)
    assert accounts.c.id.type.as_uuid is True
    assert accounts.c.id.server_default is None
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
    assigned_by_fk = next(
        fk
        for fk in roles.foreign_key_constraints
        if fk.elements[0].parent.name == "assigned_by_account_id"
    )
    physical_name = "fk_identity_role_assignments_assigned_by_account_id_ide_a4f6"
    logical_name = (
        "fk_identity_role_assignments_assigned_by_account_id_identity_accounts"
    )
    assert assigned_by_fk.name == physical_name
    assert dict(metadata.naming_convention) == dict(NAMING_CONVENTION)
    assert [element.target_fullname for element in assigned_by_fk.elements] == [
        "mayak.identity_accounts.id"
    ]
    assert assigned_by_fk.ondelete == "RESTRICT"
    compiled = str(CreateTable(roles).compile(dialect=postgresql.dialect()))
    assert f"CONSTRAINT {physical_name}" in compiled
    assert physical_name in compiled
    migration_text = (
        Path(__file__).parents[2]
        / "alembic"
        / "versions"
        / "20260727_RF09_M02_identity_and_access.py"
    ).read_text(encoding="utf-8")
    assert migration_text.count(physical_name) == 1
    assert logical_name not in migration_text
    assert len(physical_name.encode("utf-8")) == 60
    assert len(physical_name.encode("utf-8")) <= 63
    assert physical_name in compiled
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


def _isolated_platform_metadata() -> MetaData:
    isolated = MetaData(schema="mayak", naming_convention=NAMING_CONVENTION)
    register_platform_tables(isolated)
    return isolated


def _metadata_snapshot(target_metadata: MetaData) -> dict[str, object]:
    platform_tables = tuple(
        target_metadata.tables[f"mayak.{name}"]
        for name in (
            "platform_idempotency_records",
            "platform_audit_entries",
            "platform_event_outbox",
        )
    )
    audit = target_metadata.tables["mayak.platform_audit_entries"]
    return {
        "table_keys": tuple(target_metadata.tables),
        "platform_table_ids": tuple(id(table) for table in platform_tables),
        "audit_columns": tuple(column.name for column in audit.columns),
        "constraint_ids": tuple(
            (id(constraint), constraint.name)
            for table in platform_tables
            for constraint in table.constraints
        ),
        "index_ids": tuple(
            (id(index), index.name)
            for table in platform_tables
            for index in table.indexes
        ),
        "foreign_key_ids": tuple(
            (
                id(foreign_key),
                foreign_key.name,
                tuple(element.target_fullname for element in foreign_key.elements),
                foreign_key.ondelete,
            )
            for table in platform_tables
            for foreign_key in table.foreign_key_constraints
        ),
        "audit_info": deepcopy(audit.info),
    }


def _assert_rejected_without_metadata_mutation(
    target_metadata: MetaData, message: str
) -> None:
    before = _metadata_snapshot(target_metadata)
    with pytest.raises(RuntimeError, match=message):
        register_identity_tables(target_metadata)
    assert _metadata_snapshot(target_metadata) == before
    assert not any(
        name.endswith(f".{identity_name}")
        for name in target_metadata.tables
        for identity_name in NAMES
    )


def test_conflicting_deferred_marker_rejects_before_identity_mutation() -> None:
    isolated = _isolated_platform_metadata()
    audit = isolated.tables["mayak.platform_audit_entries"]
    audit.info["deferred_foreign_keys"] = (
        {
            "local_column": "actor_account_id",
            "target": "mayak.other_accounts.id",
            "on_delete": "RESTRICT",
            "planned_revision": "RF09_M02",
        },
    )
    _assert_rejected_without_metadata_mutation(
        isolated, "conflicting platform audit deferred FK marker"
    )
    assert audit.info["deferred_foreign_keys"][0]["target"] == "mayak.other_accounts.id"


def test_conflicting_existing_fk_rejects_before_identity_mutation() -> None:
    isolated = _isolated_platform_metadata()
    audit = isolated.tables["mayak.platform_audit_entries"]
    del audit.info["deferred_foreign_keys"]
    ForeignKeyConstraint(
        [audit.c.actor_account_id],
        ["mayak.platform_event_outbox.id"],
        name="fk_conflicting_platform_audit",
    )._set_parent(audit)
    _assert_rejected_without_metadata_mutation(
        isolated, "conflicting platform audit foreign key"
    )


def test_missing_marker_and_fk_rejects_before_identity_mutation() -> None:
    isolated = _isolated_platform_metadata()
    del isolated.tables["mayak.platform_audit_entries"].info["deferred_foreign_keys"]
    _assert_rejected_without_metadata_mutation(
        isolated, "conflicting platform audit deferred FK marker"
    )


def test_marker_plus_existing_fk_rejects_before_identity_mutation() -> None:
    isolated = _isolated_platform_metadata()
    audit = isolated.tables["mayak.platform_audit_entries"]
    ForeignKeyConstraint(
        [audit.c.actor_account_id],
        ["mayak.platform_event_outbox.id"],
        name="fk_conflicting_platform_audit",
    )._set_parent(audit)
    _assert_rejected_without_metadata_mutation(
        isolated, "conflicting platform audit deferred FK and constraint"
    )
