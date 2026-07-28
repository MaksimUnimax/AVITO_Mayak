"""Module 02 Identity & Access physical table registrations."""

from __future__ import annotations

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
    text,
)
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID

_TABLE_NAMES = (
    "identity_accounts",
    "identity_provider_links",
    "identity_role_assignments",
    "identity_sessions",
    "identity_link_challenges",
)
_AUDIT_TABLE = "platform_audit_entries"
_AUDIT_FK_NAME = "fk_platform_audit_entries_actor_account_id_identity_accounts"
_EXPECTED_AUDIT_FK_MARKER = {
    "local_column": "actor_account_id",
    "target": "{schema}.identity_accounts.id",
    "on_delete": "RESTRICT",
    "planned_revision": "RF09_M02",
}


def _key(metadata: MetaData, name: str) -> str:
    return f"{metadata.schema}.{name}" if metadata.schema else name


def _validate_audit_fk(metadata: MetaData) -> bool:
    audit = metadata.tables[_key(metadata, _AUDIT_TABLE)]
    expected_target = f"{metadata.schema}.identity_accounts.id"
    deferred = audit.info.get("deferred_foreign_keys")
    expected_marker = {
        key: value.format(schema=metadata.schema)
        if isinstance(value, str)
        else value
        for key, value in _EXPECTED_AUDIT_FK_MARKER.items()
    }
    if "actor_account_id" not in audit.c:
        raise RuntimeError("platform audit actor_account_id column is missing")
    fks = list(audit.foreign_key_constraints)
    if deferred is not None and fks:
        raise RuntimeError("conflicting platform audit deferred FK and constraint")
    if not fks:
        if deferred != (expected_marker,):
            raise RuntimeError("conflicting platform audit deferred FK marker")
        return False
    if deferred is not None:
        raise RuntimeError("conflicting platform audit deferred FK and constraint")
    if len(fks) != 1:
        raise RuntimeError("conflicting platform audit foreign keys")
    fk = fks[0]
    if (
        fk.name != _AUDIT_FK_NAME
        or [element.parent.name for element in fk.elements] != ["actor_account_id"]
        or [element.target_fullname for element in fk.elements] != [expected_target]
        or fk.ondelete != "RESTRICT"
    ):
        raise RuntimeError("conflicting platform audit foreign key")
    return True


def _resolve_audit_fk(metadata: MetaData, accounts: Table) -> None:
    audit = metadata.tables[_key(metadata, _AUDIT_TABLE)]
    if not _validate_audit_fk(metadata):
        ForeignKeyConstraint(
            [audit.c.actor_account_id],
            [f"{accounts.fullname}.id"],
            name=_AUDIT_FK_NAME,
            ondelete="RESTRICT",
        )._set_parent(audit)
        audit.info.pop("deferred_foreign_keys", None)
        return


def register_identity_tables(
    target_metadata: MetaData,
) -> tuple[Table, Table, Table, Table, Table]:
    """Register the canonical five Identity tables and resolve the M01 FK."""

    if target_metadata.schema != "mayak":
        raise RuntimeError("identity tables require mayak schema")
    platform_key = {
        _key(target_metadata, name)
        for name in (
            "platform_idempotency_records",
            _AUDIT_TABLE,
            "platform_event_outbox",
        )
    }
    if not platform_key.issubset(target_metadata.tables):
        raise RuntimeError(
            "platform table registration is required before identity tables"
        )
    present = [
        _key(target_metadata, name) in target_metadata.tables for name in _TABLE_NAMES
    ]
    if any(present) and not all(present):
        raise RuntimeError("partial identity table registration is not supported")

    _validate_audit_fk(target_metadata)
    if not present[0]:
        accounts = Table(
            "identity_accounts",
            target_metadata,
            Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
            Column("phone", Text, nullable=True),
            Column("state", String(64), nullable=False),
            Column("created_at", TIMESTAMP(timezone=True), nullable=False),
            Column("updated_at", TIMESTAMP(timezone=True), nullable=False),
            Column("row_version", BigInteger, nullable=False, server_default=text("1")),
            CheckConstraint("btrim(state) <> ''", name="state_nonempty"),
            CheckConstraint("row_version > 0", name="row_version"),
        )
        Index(
            "ix_identity_accounts_phone",
            accounts.c.phone,
            postgresql_where=accounts.c.phone.is_not(None),
        )
        Index(
            "ix_identity_accounts_state_created_at",
            accounts.c.state,
            accounts.c.created_at,
        )
        _resolve_audit_fk(target_metadata, accounts)
        provider_links = Table(
            "identity_provider_links",
            target_metadata,
            Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
            Column("account_id", UUID(as_uuid=True), nullable=False),
            Column("provider_code", String(64), nullable=False),
            Column("provider_subject", Text, nullable=False),
            Column("state", String(64), nullable=False),
            Column("created_at", TIMESTAMP(timezone=True), nullable=False),
            Column("updated_at", TIMESTAMP(timezone=True), nullable=False),
            Column("row_version", BigInteger, nullable=False, server_default=text("1")),
            ForeignKeyConstraint(
                ["account_id"], ["mayak.identity_accounts.id"], ondelete="RESTRICT"
            ),
            UniqueConstraint(
                "provider_code",
                "provider_subject",
                name="uq_identity_provider_links_provider_subject",
            ),
            CheckConstraint(
                "btrim(provider_code) <> ''", name="provider_code_nonempty"
            ),
            CheckConstraint(
                "btrim(provider_subject) <> ''", name="provider_subject_nonempty"
            ),
            CheckConstraint(
                "octet_length(provider_subject) <= 255", name="provider_subject_length"
            ),
            CheckConstraint("btrim(state) <> ''", name="state_nonempty"),
            CheckConstraint("row_version > 0", name="row_version"),
        )
        Index("ix_identity_provider_links_account_id", provider_links.c.account_id)
        role_assignments = Table(
            "identity_role_assignments",
            target_metadata,
            Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
            Column("account_id", UUID(as_uuid=True), nullable=False),
            Column("role_code", String(64), nullable=False),
            Column("assigned_by_account_id", UUID(as_uuid=True), nullable=False),
            Column("reason", Text, nullable=False),
            Column("created_at", TIMESTAMP(timezone=True), nullable=False),
            Column("revoked_at", TIMESTAMP(timezone=True), nullable=True),
            ForeignKeyConstraint(
                ["account_id"], ["mayak.identity_accounts.id"], ondelete="RESTRICT"
            ),
            ForeignKeyConstraint(
                ["assigned_by_account_id"],
                ["mayak.identity_accounts.id"],
                name="fk_identity_role_assignments_assigned_by_account_id_ide_a4f6",
                ondelete="RESTRICT",
            ),
            UniqueConstraint(
                "account_id",
                "role_code",
                "created_at",
                name="uq_identity_role_assignments_account_role_created",
            ),
            CheckConstraint("btrim(role_code) <> ''", name="role_code_nonempty"),
            CheckConstraint("btrim(reason) <> ''", name="reason_nonempty"),
            CheckConstraint(
                "revoked_at IS NULL OR revoked_at >= created_at", name="revoked_at"
            ),
        )
        Index(
            "ix_identity_role_assignments_active",
            role_assignments.c.account_id,
            role_assignments.c.role_code,
            postgresql_where=role_assignments.c.revoked_at.is_(None),
        )
        Index(
            "ix_identity_role_assignments_assigned_by_created_at",
            role_assignments.c.assigned_by_account_id,
            role_assignments.c.created_at,
        )
        sessions = Table(
            "identity_sessions",
            target_metadata,
            Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
            Column("account_id", UUID(as_uuid=True), nullable=False),
            Column("token_hash", CHAR(64), nullable=False),
            Column("issued_at", TIMESTAMP(timezone=True), nullable=False),
            Column("expires_at", TIMESTAMP(timezone=True), nullable=False),
            Column("revoked_at", TIMESTAMP(timezone=True), nullable=True),
            Column("created_at", TIMESTAMP(timezone=True), nullable=False),
            Column("row_version", BigInteger, nullable=False, server_default=text("1")),
            ForeignKeyConstraint(
                ["account_id"], ["mayak.identity_accounts.id"], ondelete="RESTRICT"
            ),
            UniqueConstraint("token_hash", name="uq_identity_sessions_token_hash"),
            CheckConstraint("token_hash ~ '^[0-9a-f]{64}$'", name="token_hash_sha256"),
            CheckConstraint("expires_at > issued_at", name="expiry_after_issue"),
            CheckConstraint(
                "expires_at <= issued_at + interval '24 hours'", name="max_lifetime"
            ),
            CheckConstraint(
                "revoked_at IS NULL OR revoked_at >= issued_at", name="revoked_at"
            ),
            CheckConstraint("row_version > 0", name="row_version"),
        )
        Index(
            "ix_identity_sessions_account_expires_at",
            sessions.c.account_id,
            sessions.c.expires_at,
        )
        Index(
            "ix_identity_sessions_active_expires_at",
            sessions.c.expires_at,
            postgresql_where=sessions.c.revoked_at.is_(None),
        )
        challenges = Table(
            "identity_link_challenges",
            target_metadata,
            Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
            Column("account_id", UUID(as_uuid=True), nullable=False),
            Column("challenge_hash", CHAR(64), nullable=False),
            Column("provider_code", String(64), nullable=False),
            Column("expires_at", TIMESTAMP(timezone=True), nullable=False),
            Column("consumed_at", TIMESTAMP(timezone=True), nullable=True),
            Column("created_at", TIMESTAMP(timezone=True), nullable=False),
            Column("row_version", BigInteger, nullable=False, server_default=text("1")),
            ForeignKeyConstraint(
                ["account_id"], ["mayak.identity_accounts.id"], ondelete="RESTRICT"
            ),
            UniqueConstraint(
                "challenge_hash", name="uq_identity_link_challenges_challenge_hash"
            ),
            CheckConstraint(
                "challenge_hash ~ '^[0-9a-f]{64}$'", name="challenge_hash_sha256"
            ),
            CheckConstraint(
                "btrim(provider_code) <> ''", name="provider_code_nonempty"
            ),
            CheckConstraint("expires_at > created_at", name="expiry_after_creation"),
            CheckConstraint(
                "consumed_at IS NULL OR consumed_at >= created_at", name="consumed_at"
            ),
            CheckConstraint("row_version > 0", name="row_version"),
        )
        Index(
            "ix_identity_link_challenges_active_expires_at",
            challenges.c.expires_at,
            postgresql_where=challenges.c.consumed_at.is_(None),
        )
    else:
        _resolve_audit_fk(
            target_metadata,
            target_metadata.tables[_key(target_metadata, "identity_accounts")],
        )
    return tuple(
        target_metadata.tables[_key(target_metadata, name)] for name in _TABLE_NAMES
    )  # type: ignore[return-value]


__all__ = ["register_identity_tables"]
