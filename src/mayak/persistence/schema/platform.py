"""Module 01 Platform & Contracts physical table registrations."""

from __future__ import annotations

from sqlalchemy import (
    CHAR,
    BigInteger,
    CheckConstraint,
    Column,
    Index,
    MetaData,
    String,
    Table,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID

_TABLE_NAMES = (
    "platform_idempotency_records",
    "platform_audit_entries",
    "platform_event_outbox",
)
_DEFERRED_ACTOR_FK = {
    "local_column": "actor_account_id",
    "target": "mayak.identity_accounts.id",
    "on_delete": "RESTRICT",
    "planned_revision": "RF09_M02",
}


def register_platform_tables(target_metadata: MetaData) -> tuple[Table, Table, Table]:
    """Register and return the three platform tables exactly once."""

    def key(name: str) -> str:
        return f"{target_metadata.schema}.{name}" if target_metadata.schema else name

    present = [name for name in _TABLE_NAMES if key(name) in target_metadata.tables]
    if present and len(present) != len(_TABLE_NAMES):
        raise RuntimeError("partial platform table registration is not supported")
    if len(present) == len(_TABLE_NAMES):
        return tuple(target_metadata.tables[key(name)] for name in _TABLE_NAMES)  # type: ignore[return-value]

    idempotency = Table(
        "platform_idempotency_records",
        target_metadata,
        Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        Column("scope", Text, nullable=False),
        Column("idempotency_key", String(200), nullable=False),
        Column("request_fingerprint", CHAR(64), nullable=False),
        Column("result", JSONB, nullable=False),
        Column("expires_at", TIMESTAMP(timezone=True), nullable=False),
        Column("created_at", TIMESTAMP(timezone=True), nullable=False),
        UniqueConstraint(
            "scope", "idempotency_key", name="uq_platform_idempotency_records_scope_key"
        ),
        CheckConstraint("btrim(scope) <> ''", name="scope_nonempty"),
        CheckConstraint("btrim(idempotency_key) <> ''", name="key_nonempty"),
        CheckConstraint("request_fingerprint ~ '^[0-9a-f]{64}$'", name="fingerprint"),
        CheckConstraint("octet_length(result::text) <= 65536", name="result_size"),
    )
    Index("ix_platform_idempotency_records_expires_at", idempotency.c.expires_at)
    Index(
        "ix_platform_idempotency_records_scope_key",
        idempotency.c.scope,
        idempotency.c.idempotency_key,
    )

    audit = Table(
        "platform_audit_entries",
        target_metadata,
        Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        Column("actor_account_id", UUID(as_uuid=True), nullable=True),
        Column("action_code", String(64), nullable=False),
        Column("target_type", String(128), nullable=False),
        Column("target_id", Text, nullable=True),
        Column("reason", Text, nullable=False),
        Column("correlation_id", Text, nullable=False),
        Column("details", JSONB, nullable=False),
        Column("created_at", TIMESTAMP(timezone=True), nullable=False),
        CheckConstraint("btrim(reason) <> ''", name="reason_nonempty"),
        CheckConstraint("octet_length(details::text) <= 65536", name="details_size"),
        info={"deferred_foreign_keys": (_DEFERRED_ACTOR_FK,)},
    )
    Index("ix_platform_audit_entries_created_at", audit.c.created_at)
    Index("ix_platform_audit_entries_correlation_id", audit.c.correlation_id)
    Index(
        "ix_platform_audit_entries_actor_created_at", audit.c.actor_account_id, audit.c.created_at
    )

    outbox = Table(
        "platform_event_outbox",
        target_metadata,
        Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        Column("event_fingerprint", CHAR(64), nullable=False),
        Column("contract_name", String(128), nullable=False),
        Column("contract_version", String(32), nullable=False),
        Column("payload", JSONB, nullable=False),
        Column("state", String(64), nullable=False),
        Column("available_at", TIMESTAMP(timezone=True), nullable=False),
        Column("lease_started_at", TIMESTAMP(timezone=True), nullable=True),
        Column("lease_expires_at", TIMESTAMP(timezone=True), nullable=True),
        Column("lease_token", UUID(as_uuid=True), nullable=True),
        Column("attempt_count", BigInteger, nullable=False, server_default=text("0")),
        Column("created_at", TIMESTAMP(timezone=True), nullable=False),
        Column("row_version", BigInteger, nullable=False, server_default=text("1")),
        UniqueConstraint("event_fingerprint", name="uq_platform_event_outbox_event_fingerprint"),
        CheckConstraint("event_fingerprint ~ '^[0-9a-f]{64}$'", name="fingerprint"),
        CheckConstraint("octet_length(payload::text) <= 65536", name="payload_size"),
        CheckConstraint("attempt_count >= 0", name="attempt_count"),
        CheckConstraint("row_version > 0", name="row_version"),
        CheckConstraint("btrim(state) <> ''", name="state_nonempty"),
        CheckConstraint(
            "(lease_started_at IS NULL AND lease_expires_at IS NULL) "
            "OR lease_expires_at > lease_started_at",
            name="lease_window",
        ),
    )
    Index(
        "ix_platform_event_outbox_available",
        outbox.c.available_at,
        outbox.c.id,
        postgresql_where=outbox.c.state.in_(("PENDING", "RETRY")),
    )
    Index(
        "ix_platform_event_outbox_expired_lease",
        outbox.c.lease_expires_at,
        postgresql_where=outbox.c.state == "CLAIMED",
    )
    return idempotency, audit, outbox
