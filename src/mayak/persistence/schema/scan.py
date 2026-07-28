"""Module 06 Scan Orchestration physical table registrations."""

from __future__ import annotations

from typing import Any

import sqlalchemy as sa
from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Column,
    ForeignKeyConstraint,
    Index,
    MetaData,
    String,
    Table,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import CHAR, JSONB, TIMESTAMP, UUID
from sqlalchemy.dialects.postgresql import dialect as postgresql_dialect
from sqlalchemy.sql.type_api import TypeEngine

_NAMES = (
    "scan_schedules",
    "scan_work_items",
    "scan_runs",
    "scan_listing_observations",
    "scan_beacon_listing_state",
    "scan_anchors",
)
_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}
_DIALECT = postgresql_dialect()
def _key(m: MetaData, n: str) -> str:
    return f"{m.schema}.{n}" if m.schema else n


def _norm(v: object) -> str:
    s = " ".join(str(v).split())
    while len(s) > 1 and s[0] == "(" and s[-1] == ")":
        depth = 0
        if all(
            (depth := depth + (1 if c == "(" else -1 if c == ")" else 0)) != 0 or i == len(s) - 1
            for i, c in enumerate(s)
        ):
            s = s[1:-1].strip()
        else:
            break
    return s


def _stable(v: object) -> object:
    if v is None or isinstance(v, (bool, int, float, str)):
        return v
    if isinstance(v, (list, tuple)):
        return tuple(_stable(x) for x in v)
    if isinstance(v, dict):
        return tuple(sorted((str(k), _stable(x)) for k, x in v.items()))
    if hasattr(v, "compile"):
        return _norm(v)
    return (type(v).__module__, type(v).__name__)


def _type(v: TypeEngine[Any]) -> object:
    opts = (
        "length",
        "precision",
        "scale",
        "timezone",
        "as_uuid",
        "collation",
        "none_as_null",
        "hashable",
        "should_evaluate_none",
        "astext_type",
    )
    return (
        type(v).__module__,
        type(v).__name__,
        str(v.compile(dialect=_DIALECT)),
        tuple((o, _stable(getattr(v, o))) for o in opts if hasattr(v, o)),
    )


def _value(v: object) -> object:
    if v is None:
        return None
    a = getattr(v, "arg", v)
    return (
        ("callable", getattr(a, "__module__", ""), getattr(a, "__qualname__", ""))
        if callable(a)
        else _stable(a)
    )


def _dialect(v: object) -> object:
    if not hasattr(v, "items"):
        return ()
    return tuple(
        (str(k), tuple(sorted((str(a), _norm(b)) for a, b in x.items())))
        for k, x in sorted(v.items())
        if x
    )


def _constraint(c: Any) -> object:
    return (
        type(c).__module__,
        type(c).__name__,
        c.name,
        tuple(x.name for x in getattr(c, "columns", ())),
        _norm(getattr(c, "sqltext", "")) if isinstance(c, CheckConstraint) else "",
        getattr(c, "deferrable", None),
        getattr(c, "initially", None),
        _dialect(getattr(c, "dialect_options", {})),
        _stable(getattr(c, "info", {})),
    )


def _fk(c: ForeignKeyConstraint) -> object:
    return (
        type(c).__module__,
        type(c).__name__,
        c.name,
        tuple(x.parent.name for x in c.elements),
        tuple(x.target_fullname for x in c.elements),
        c.ondelete,
        c.onupdate,
        c.deferrable,
        c.initially,
        c.use_alter,
        c.match,
        _dialect(c.dialect_options),
        _stable(c.info),
    )


def _index(i: Index) -> object:
    return (
        i.name,
        tuple(getattr(x, "name", _norm(x)) for x in i.expressions),
        i.unique,
        _dialect(i.dialect_options),
        _stable(i.info),
    )


def _table(t: Table) -> object:
    cs = tuple(
        sorted(
            (
                _fk(x) if isinstance(x, ForeignKeyConstraint) else _constraint(x)
                for x in t.constraints
            ),
            key=str,
        )
    )
    return (
        type(t).__module__,
        type(t).__name__,
        t.name,
        t.schema,
        t.comment,
        tuple(getattr(t, "prefixes", ())),
        t.implicit_returning,
        _dialect(t.dialect_options),
        _stable(t.info),
        tuple(
            (
                c.name,
                c.key,
                _type(c.type),
                c.nullable,
                c.primary_key,
                c.autoincrement,
                c.unique,
                c.index,
                _value(c.server_default),
                _value(c.default),
                _value(c.onupdate),
                _value(c.server_onupdate),
                c.comment,
                _stable(c.info),
                c.system,
                _stable(c.identity) if c.identity else None,
                (_norm(c.computed.sqltext), c.computed.persisted) if c.computed else None,
            )
            for c in t.columns
        ),
        cs,
        tuple(sorted((_index(i) for i in t.indexes), key=str)),
    )


def _canonical(m: MetaData) -> tuple[Table, Table, Table, Table, Table, Table]:
    schedules = Table(
        "scan_schedules",
        m,
        Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        Column("beacon_id", UUID(as_uuid=True), nullable=False),
        Column("interval_seconds", BigInteger, nullable=False),
        Column("next_due_at", TIMESTAMP(timezone=True), nullable=False),
        Column("state", String(64), nullable=False),
        Column("created_at", TIMESTAMP(timezone=True), nullable=False),
        Column("updated_at", TIMESTAMP(timezone=True), nullable=False),
        Column("row_version", BigInteger, nullable=False, server_default=text("1")),
        ForeignKeyConstraint(["beacon_id"], ["mayak.beacon_beacons.id"], ondelete="RESTRICT"),
        UniqueConstraint("beacon_id", name="uq_scan_schedules_beacon_id"),
        CheckConstraint("interval_seconds > 0", name="interval_positive"),
        CheckConstraint("btrim(state) <> ''", name="state_nonempty"),
        CheckConstraint("row_version > 0", name="row_version_positive"),
    )
    Index(
        "ix_scan_schedules_active_due",
        schedules.c.next_due_at,
        schedules.c.id,
        postgresql_where=text("state = 'ACTIVE'"),
    )
    work = Table(
        "scan_work_items",
        m,
        Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        Column("schedule_id", UUID(as_uuid=True), nullable=False),
        Column("beacon_id", UUID(as_uuid=True), nullable=False),
        Column("due_at", TIMESTAMP(timezone=True), nullable=False),
        Column("state", String(64), nullable=False),
        Column("lease_started_at", TIMESTAMP(timezone=True)),
        Column("lease_expires_at", TIMESTAMP(timezone=True)),
        Column("lease_token", UUID(as_uuid=True)),
        Column("attempt_count", BigInteger, nullable=False, server_default=text("0")),
        Column("created_at", TIMESTAMP(timezone=True), nullable=False),
        Column("row_version", BigInteger, nullable=False, server_default=text("1")),
        ForeignKeyConstraint(["schedule_id"], ["mayak.scan_schedules.id"], ondelete="RESTRICT"),
        ForeignKeyConstraint(["beacon_id"], ["mayak.beacon_beacons.id"], ondelete="RESTRICT"),
        UniqueConstraint("schedule_id", "due_at", name="uq_scan_work_items_schedule_due_at"),
        CheckConstraint("attempt_count >= 0", name="attempt_nonnegative"),
        CheckConstraint("btrim(state) <> ''", name="state_nonempty"),
        CheckConstraint("row_version > 0", name="row_version_positive"),
        CheckConstraint(
            "(lease_started_at IS NULL AND lease_expires_at IS NULL) OR "
            "lease_expires_at > lease_started_at",
            name="lease_window",
        ),
    )
    Index(
        "ix_scan_work_items_due",
        work.c.due_at,
        work.c.id,
        postgresql_where=text("state IN ('DUE', 'RETRY')"),
    )
    Index(
        "ix_scan_work_items_claimed_expiry",
        work.c.lease_expires_at,
        postgresql_where=text("state = 'CLAIMED'"),
    )
    runs = Table(
        "scan_runs",
        m,
        Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        Column("work_item_id", UUID(as_uuid=True), nullable=False),
        Column("beacon_id", UUID(as_uuid=True), nullable=False),
        Column("revision_no", BigInteger, nullable=False),
        Column("parser_outcome_id", UUID(as_uuid=True)),
        Column("route_id", UUID(as_uuid=True)),
        Column("state", String(64), nullable=False),
        Column("started_at", TIMESTAMP(timezone=True), nullable=False),
        Column("completed_at", TIMESTAMP(timezone=True)),
        Column("row_version", BigInteger, nullable=False, server_default=text("1")),
        ForeignKeyConstraint(["work_item_id"], ["mayak.scan_work_items.id"], ondelete="RESTRICT"),
        ForeignKeyConstraint(["beacon_id"], ["mayak.beacon_beacons.id"], ondelete="RESTRICT"),
        ForeignKeyConstraint(
            ["beacon_id", "revision_no"],
            [
                "mayak.beacon_configuration_revisions.beacon_id",
                "mayak.beacon_configuration_revisions.revision_no",
            ],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["parser_outcome_id"],
            ["mayak.parser_outcomes.id"],
            name="fk_scan_runs_parser_outcome_id_parser_outcomes",
            ondelete="RESTRICT",
            use_alter=True,
        ),
        ForeignKeyConstraint(["route_id"], ["mayak.egress_routes.id"], ondelete="RESTRICT"),
        UniqueConstraint("work_item_id", name="uq_scan_runs_work_item_id"),
        CheckConstraint("revision_no > 0", name="revision_positive"),
        CheckConstraint("btrim(state) <> ''", name="state_nonempty"),
        CheckConstraint(
            "completed_at IS NULL OR completed_at >= started_at", name="completion_order"
        ),
        CheckConstraint("row_version > 0", name="row_version_positive"),
    )
    Index("ix_scan_runs_beacon_started_at", runs.c.beacon_id, runs.c.started_at)
    Index(
        "ix_scan_runs_active_states",
        runs.c.state,
        runs.c.started_at,
        postgresql_where=text("state IN ('RUNNING', 'PENDING_RECONCILIATION')"),
    )
    obs = Table(
        "scan_listing_observations",
        m,
        Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        Column("run_id", UUID(as_uuid=True), nullable=False),
        Column("beacon_id", UUID(as_uuid=True), nullable=False),
        Column("external_listing_key", String(255), nullable=False),
        Column("snapshot", JSONB, nullable=False),
        Column("observed_at", TIMESTAMP(timezone=True), nullable=False),
        Column("fingerprint", CHAR(64), nullable=False),
        ForeignKeyConstraint(["run_id"], ["mayak.scan_runs.id"], ondelete="RESTRICT"),
        ForeignKeyConstraint(["beacon_id"], ["mayak.beacon_beacons.id"], ondelete="RESTRICT"),
        UniqueConstraint(
            "run_id", "external_listing_key", name="uq_scan_listing_observations_run_external_key"
        ),
        CheckConstraint("btrim(external_listing_key) <> ''", name="external_key_nonempty"),
        CheckConstraint("octet_length(snapshot::text) <= 32768", name="snapshot_size"),
        CheckConstraint("fingerprint ~ '^[0-9a-f]{64}$'", name="fingerprint_format"),
    )
    Index("ix_scan_listing_observations_beacon_observed_at", obs.c.beacon_id, obs.c.observed_at)
    listing = Table(
        "scan_beacon_listing_state",
        m,
        Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        Column("beacon_id", UUID(as_uuid=True), nullable=False),
        Column("external_listing_key", String(255), nullable=False),
        Column("last_seen_at", TIMESTAMP(timezone=True), nullable=False),
        Column("last_snapshot", JSONB, nullable=False),
        Column("first_seen_at", TIMESTAMP(timezone=True), nullable=False),
        Column("row_version", BigInteger, nullable=False, server_default=text("1")),
        Column("updated_at", TIMESTAMP(timezone=True), nullable=False),
        ForeignKeyConstraint(["beacon_id"], ["mayak.beacon_beacons.id"], ondelete="RESTRICT"),
        UniqueConstraint(
            "beacon_id",
            "external_listing_key",
            name="uq_scan_beacon_listing_state_beacon_external_key",
        ),
        CheckConstraint("btrim(external_listing_key) <> ''", name="external_key_nonempty"),
        CheckConstraint("octet_length(last_snapshot::text) <= 32768", name="snapshot_size"),
        CheckConstraint("row_version > 0", name="row_version_positive"),
    )
    Index(
        "ix_scan_beacon_listing_state_beacon_last_seen_at",
        listing.c.beacon_id,
        listing.c.last_seen_at,
    )
    anchors = Table(
        "scan_anchors",
        m,
        Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        Column("beacon_id", UUID(as_uuid=True), nullable=False),
        Column("anchor_key", String(255), nullable=False),
        Column("corrected_by_account_id", UUID(as_uuid=True)),
        Column("correction_reason", sa.Text, nullable=True),
        Column("updated_at", TIMESTAMP(timezone=True), nullable=False),
        Column("row_version", BigInteger, nullable=False, server_default=text("1")),
        ForeignKeyConstraint(["beacon_id"], ["mayak.beacon_beacons.id"], ondelete="RESTRICT"),
        ForeignKeyConstraint(
            ["corrected_by_account_id"], ["mayak.identity_accounts.id"], ondelete="RESTRICT"
        ),
        UniqueConstraint("beacon_id", name="uq_scan_anchors_beacon_id"),
        CheckConstraint("btrim(anchor_key) <> ''", name="anchor_nonempty"),
        CheckConstraint("row_version > 0", name="row_version_positive"),
        CheckConstraint(
            "(corrected_by_account_id IS NULL AND correction_reason IS NULL) OR "
            "(corrected_by_account_id IS NOT NULL AND correction_reason IS NOT NULL "
            "AND btrim(correction_reason) <> '')",
            name="correction_pair",
        ),
    )
    Index("ix_scan_anchors_beacon_updated_at", anchors.c.beacon_id, anchors.c.updated_at)
    return schedules, work, runs, obs, listing, anchors


def register_scan_tables(
    target_metadata: MetaData,
) -> tuple[Table, Table, Table, Table, Table, Table]:
    if target_metadata.schema != "mayak":
        raise RuntimeError("scan tables require mayak schema")
    if _stable(target_metadata.naming_convention) != _stable(_CONVENTION) or _stable(
        target_metadata.info
    ) != _stable({}):
        raise RuntimeError("conflicting existing scan metadata")
    present = [_key(target_metadata, n) in target_metadata.tables for n in _NAMES]
    if any(present) and not all(present):
        raise RuntimeError("partial scan table registration is not supported")
    if all(present):
        actual = tuple(target_metadata.tables[_key(target_metadata, n)] for n in _NAMES)
        expected = _canonical(MetaData(schema="mayak", naming_convention=_CONVENTION))
        if any(_table(a) != _table(e) for a, e in zip(actual, expected)):
            raise RuntimeError("conflicting existing scan registration")
        return actual  # type: ignore[return-value]
    return _canonical(target_metadata)


__all__ = ["register_scan_tables"]
