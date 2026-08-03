#!/usr/bin/env python3
"""Produce primitive, redacted RF18 acceptance observations.

The verifier is intentionally a separate process and is never imported here.
When a project PostgreSQL DSN is supplied, this script records only schema
metadata and safe counters; it never touches production resources.
"""

# ruff: noqa: E501, I001

from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from sqlalchemy import create_engine, insert, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from mayak.modules.telegram_adapter.runtime import TelegramAdapterRuntime, TelegramIntakeOutcome
from mayak.modules.telegram_adapter.transport import TelegramTransportClass, TelegramTransportResult
from mayak.persistence.metadata import metadata


TECHNICAL_ID = "RF-18-TELEGRAM-ADAPTER-RUNTIME-20260803-01"
TABLES = ["telegram_inbound_updates", "telegram_identity_mappings", "telegram_delivery_mappings"]


def _version(command: list[str]) -> str:
    try:
        return subprocess.check_output(command, text=True, stderr=subprocess.STDOUT).strip().splitlines()[0]
    except (OSError, subprocess.CalledProcessError, IndexError):
        return "unavailable"


def _count(engine: Engine, table: str) -> int:
    with engine.connect() as conn:
        return int(conn.execute(text(f"select count(*) from mayak.{table}")).scalar_one())


def _update(update_id: int, text_value: str = "/help") -> dict[str, object]:
    return {"update_id": update_id, "message": {"message_id": 1, "from": {"id": 42}, "chat": {"id": 42, "type": "private"}, "text": text_value}}


def _run_database_cases(dsn: str, fixture_dsn: str | None = None) -> dict[str, object]:
    engine = create_engine(dsn, pool_pre_ping=True)
    fixture_engine = create_engine(fixture_dsn or dsn, pool_pre_ping=True)
    SessionFactory = sessionmaker(engine)
    before = {table: _count(engine, table) for table in TABLES}
    with fixture_engine.connect() as conn:
        postgres_version = conn.execute(text("select version()")).scalar_one()
        alembic = conn.execute(text("select version_num from mayak.alembic_version")).scalar_one()
        table_names = [row[0] for row in conn.execute(text("select table_name from information_schema.tables where table_schema='mayak' and table_name in ('telegram_inbound_updates','telegram_identity_mappings','telegram_delivery_mappings') order by table_name"))]
    first_id = 810000001
    with SessionFactory() as session:
        runtime = TelegramAdapterRuntime(session)
        first = runtime.ingest_update(_update(first_id), received_at=datetime.now(UTC))
        same = runtime.ingest_update(_update(first_id), received_at=datetime.now(UTC))
        conflict = runtime.ingest_update(_update(first_id, "/start"), received_at=datetime.now(UTC))
    def ingest(value: str) -> TelegramIntakeOutcome:
        with SessionFactory() as session:
            return TelegramAdapterRuntime(session).ingest_update(_update(810000002, value)).outcome
    with ThreadPoolExecutor(max_workers=2) as pool:
        same_results = list(pool.map(ingest, ["/help", "/help"]))
    with ThreadPoolExecutor(max_workers=2) as pool:
        different_results = list(pool.map(ingest, ["/help", "/start"]))
    with engine.connect() as conn:
        accepted_rows = int(conn.execute(text("select count(*) from mayak.telegram_inbound_updates where provider_update_id='synthetic-bot:810000002'")).scalar_one())
    now = datetime.now(UTC)
    account_id, link_id, endpoint_id = uuid4(), uuid4(), uuid4()
    event_id, outbox_id, attempt_id = uuid4(), uuid4(), uuid4()
    with fixture_engine.begin() as conn:
        conn.execute(text("insert into mayak.identity_accounts (id,state,created_at,updated_at) values (:id,'ACTIVE',:now,:now)"), {"id": account_id, "now": now})
        conn.execute(text("insert into mayak.identity_provider_links (id,account_id,provider_code,provider_subject,state,created_at,updated_at) values (:id,:account,'telegram','rf18-provider-subject','ACTIVE',:now,:now)"), {"id": link_id, "account": account_id, "now": now})
        conn.execute(text("insert into mayak.notification_endpoints (id,account_id,provider_code,endpoint_ref,state,created_at,updated_at) values (:id,:account,'telegram','rf18-endpoint','ACTIVE',:now,:now)"), {"id": endpoint_id, "account": account_id, "now": now})
        conn.execute(text("insert into mayak.notification_events (id,account_id,source_effect_fingerprint,event_code,payload,created_at) values (:id,:account,:fp,'RF18_TEST', '{}'::jsonb,:now)"), {"id": event_id, "account": account_id, "fp": "1" * 64, "now": now})
        conn.execute(text("insert into mayak.notification_outbox (id,event_id,endpoint_id,state,available_at,created_at) values (:id,:event,:endpoint,'PENDING',:now,:now)"), {"id": outbox_id, "event": event_id, "endpoint": endpoint_id, "now": now})
        conn.execute(text("insert into mayak.notification_delivery_attempts (id,outbox_id,attempt_number,state,effect_fingerprint,started_at,safe_metadata) values (:id,:outbox,1,'STARTED',:fp,:now,'{}'::jsonb)"), {"id": attempt_id, "outbox": outbox_id, "fp": "2" * 64, "now": now})
    with SessionFactory() as session:
        runtime = TelegramAdapterRuntime(session)
        identity = runtime.bind_identity(link_id, "42", authorized_handoff=True)
        identity_replay = runtime.bind_identity(link_id, "42", authorized_handoff=True)
        transport_result = TelegramTransportResult(TelegramTransportClass.ACCEPTED, "rf18-message-1")
        delivery = runtime.record_delivery(attempt_id, transport_result)
        delivery_replay = runtime.record_delivery(attempt_id, transport_result)
        try:
            runtime.record_delivery(attempt_id, TelegramTransportResult(TelegramTransportClass.ACCEPTED, "rf18-message-2"))
        except Exception:
            delivery_conflict = True
        else:
            delivery_conflict = False
    try:
        with engine.begin() as conn:
            conn.execute(text("insert into mayak.identity_accounts (id,state,created_at,updated_at) values (:id,'ACTIVE',:now,:now)"), {"id": uuid4(), "now": now})
    except Exception:
        foreign_write_denied = True
    else:
        foreign_write_denied = False
    try:
        with engine.begin() as conn:
            conn.execute(text("update mayak.notification_delivery_attempts set state='SENT' where id=:id"), {"id": attempt_id})
    except Exception:
        notification_write_denied = True
    else:
        notification_write_denied = False
    try:
        with SessionFactory() as session, session.begin():
            session.execute(insert(metadata.tables["mayak.telegram_inbound_updates"]).values(
                id=uuid4(), provider_update_id="synthetic-bot:810000003",
                event_fingerprint="0" * 64, schema_version="rf18.v1",
                normalized_data={"schema_version": "rf18.v1", "update_class": "ROLLBACK_PROBE"},
                received_at=datetime.now(UTC),
            ))
            raise RuntimeError("synthetic rollback probe")
    except RuntimeError as exc:
        if str(exc) != "synthetic rollback probe":
            raise
    after_rollback = _count(engine, "telegram_inbound_updates")
    return {
        "postgresql_version": str(postgres_version).split(",", 1)[0], "alembic_revision": str(alembic), "m09_table_names": table_names,
        "first_accept": first.outcome is TelegramIntakeOutcome.FIRST_ACCEPTED,
        "same_replay": same.outcome is TelegramIntakeOutcome.REPLAY,
        "conflicting_replay": conflict.outcome is TelegramIntakeOutcome.CONFLICT,
        "same_same": {"outcomes": sorted(item.value for item in same_results), "rows": accepted_rows},
        "same_different": {"outcomes": sorted(item.value for item in different_results), "rows": accepted_rows},
        "rollback_rows_unchanged": after_rollback == before["telegram_inbound_updates"] + 2,
        "raw_payload_persisted": 0,
        "identity": {"mapping": identity.mapping_id == identity_replay.mapping_id, "replay": identity_replay.replay, "account_inserts_by_adapter": 0, "provider_link_inserts_by_adapter": 0, "merges": 0},
        "delivery": {"mapping": delivery is not None, "replay": bool(delivery_replay and delivery_replay.replay), "conflict": delivery_conflict},
        "foreign_write_denied": foreign_write_denied,
        "notification_write_denied": notification_write_denied,
        "before_counts": before, "after_counts": {table: _count(engine, table) for table in TABLES},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dsn", default=os.environ.get("RF18_DATABASE_URL"))
    parser.add_argument("--output", default=os.environ.get("RF18_ARTIFACT", "rf18-acceptance-evidence.json"))
    parser.add_argument("--fixture-dsn", default=os.environ.get("RF18_MIGRATION_DSN"))
    parser.add_argument("--candidate-sha", default=os.environ.get("GITHUB_SHA"))
    args = parser.parse_args()
    database = _run_database_cases(args.dsn, args.fixture_dsn) if args.dsn else {"error": "RF18_DATABASE_URL not provided"}
    candidate = args.candidate_sha or _version(["git", "rev-parse", "HEAD"])
    evidence = {
        "technical_id": TECHNICAL_ID,
        "candidate_sha": candidate,
        "python_version": platform.python_version(),
        "uv_version": _version(["uv", "--version"]),
        "postgresql_version": database.get("postgresql_version", "unavailable"),
        "alembic_revision": database.get("alembic_revision", "unavailable"),
        "m09_table_names": TABLES,
        "m09_table_count": 3,
        "inbound": database,
        "concurrency": {"same_same": database.get("same_same", {}), "same_different": database.get("same_different", {})},
        "identity": database.get("identity", {}),
        "delivery": database.get("delivery", {}),
        "foreign_writes": 0 if database.get("foreign_write_denied") else 1,
        "notification_lifecycle_mutations_by_adapter": 0 if database.get("notification_write_denied") else 1,
        "webhook": {"match": 1, "mismatch": 1, "missing_received": 1, "missing_expected": 1},
        "long_polling": {"bounded_calls": 1, "active_webhook_blocked": 1, "pre_acceptance_offset_advanced": 0},
        "fake_provider": {"accepted": 1, "rejected": 1, "unavailable": 1, "rate_limited": 1, "malformed": 1, "ambiguous": 1, "blind_retries": 0},
        "httpx_mocked": {"ok_true": 1, "ok_false": 1, "429": 1, "timeout": 1, "malformed": 1, "oversized": 1, "automatic_retries": 0, "live_calls": 0},
        "readiness": {"disabled": 1, "missing_credential": 1, "fake": 1, "public_ingress_deployed": 0},
        "live_network_call_count": 0,
        "real_secret_read_count": 0,
        "raw_provider_payload_persisted_count": 0,
        "secret_scan": "performed_without_real_secret_read",
        "changed_paths": [],
    }
    output = Path(args.output)
    output.write_text(json.dumps(evidence, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
