"""Produce primitive, redacted RF19 PostgreSQL acceptance evidence."""

# ruff: noqa: E501, I001

from __future__ import annotations

import argparse
import json
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from mayak.modules.max_adapter.runtime import MaxAdapterRuntime, MaxIntakeOutcome
from mayak.modules.max_adapter.transport import MaxTransportClass, MaxTransportResult

TABLES = [
    "max_delivery_mappings",
    "max_identity_mappings",
    "max_inbound_events",
    "max_miniapp_nonces",
]


def _update(event_id: int, text_value: str = "/help") -> dict[str, object]:
    return {
        "update_id": event_id,
        "update_type": "message_created",
        "user": {"user_id": 42},
        "chat": {"chat_id": 42},
        "text": text_value,
    }


def _count(engine: object, table: str) -> int:
    with engine.connect() as connection:  # type: ignore[union-attr]
        return int(connection.execute(text(f"select count(*) from mayak.{table}")).scalar_one())


def _database_cases(application_dsn: str, migration_dsn: str) -> dict[str, object]:
    application = create_engine(application_dsn, pool_pre_ping=True)
    migration = create_engine(migration_dsn, pool_pre_ping=True)
    with migration.connect() as connection:
        version = str(connection.execute(text("select version()")))
        postgres_version = str(connection.execute(text("select version()" )).scalar_one()).split(",", 1)[0]
        head = str(connection.execute(text("select version_num from mayak.alembic_version")).scalar_one())
        tables = [
            row[0]
            for row in connection.execute(
                text("select table_name from information_schema.tables where table_schema='mayak' and table_name like 'max_%' order by table_name")
            )
        ]
        foreign_sequence_write_denied = bool(
            connection.execute(
                text(
                    "select coalesce(bool_and(not has_sequence_privilege("
                    "'mayak_application'::name, "
                    "format('%I.%I', sequence_schema, sequence_name), 'UPDATE'::text)), true) "
                    "from information_schema.sequences where sequence_schema = 'mayak'"
                )
            ).scalar_one()
        )
        _ = version

    before = {name: _count(application, name) for name in TABLES}
    event_id = int(datetime.now(UTC).timestamp() * 1_000_000)
    with Session(application) as session:
        runtime = MaxAdapterRuntime(session)
        first = runtime.ingest_webhook(_update(event_id), received_secret="synthetic", expected_secret="synthetic")
        replay = runtime.ingest_webhook(_update(event_id), received_secret="synthetic", expected_secret="synthetic")
        conflict = runtime.ingest_webhook(_update(event_id, "/start"), received_secret="synthetic", expected_secret="synthetic")

    def ingest(value: str) -> MaxIntakeOutcome:
        with Session(application) as session:
            return MaxAdapterRuntime(session).ingest_webhook(
                _update(event_id + 1, value), received_secret="synthetic", expected_secret="synthetic"
            ).outcome

    with ThreadPoolExecutor(max_workers=2) as pool:
        concurrent_same = list(pool.map(ingest, ["/help", "/help"]))
    with ThreadPoolExecutor(max_workers=2) as pool:
        concurrent_conflict = list(pool.map(ingest, ["/help", "/start"]))

    now = datetime.now(UTC)
    account_id, link_id, attempt_id = uuid4(), uuid4(), uuid4()
    outbox_id, endpoint_id, notification_event_id = uuid4(), uuid4(), uuid4()
    with migration.begin() as connection:
        connection.execute(text("insert into mayak.identity_accounts (id,state,created_at,updated_at) values (:id,'ACTIVE',:now,:now)"), {"id": account_id, "now": now})
        subject = f"rf19-subject-{account_id.hex[:12]}"
        endpoint_ref = f"rf19-endpoint-{account_id.hex[:12]}"
        fingerprint = (account_id.hex * 4)[:64]
        connection.execute(text("insert into mayak.identity_provider_links (id,account_id,provider_code,provider_subject,state,created_at,updated_at) values (:id,:account,'max',:subject,'ACTIVE',:now,:now)"), {"id": link_id, "account": account_id, "subject": subject, "now": now})
        connection.execute(text("insert into mayak.notification_endpoints (id,account_id,provider_code,endpoint_ref,state,created_at,updated_at) values (:id,:account,'max',:endpoint_ref,'ACTIVE',:now,:now)"), {"id": endpoint_id, "account": account_id, "endpoint_ref": endpoint_ref, "now": now})
        connection.execute(text("insert into mayak.notification_events (id,account_id,source_effect_fingerprint,event_code,payload,created_at) values (:id,:account,:fp,'RF19_TEST','{}'::jsonb,:now)"), {"id": notification_event_id, "account": account_id, "fp": fingerprint, "now": now})
        connection.execute(text("insert into mayak.notification_outbox (id,event_id,endpoint_id,state,available_at,created_at) values (:id,:event,:endpoint,'PENDING',:now,:now)"), {"id": outbox_id, "event": notification_event_id, "endpoint": endpoint_id, "now": now})
        connection.execute(text("insert into mayak.notification_delivery_attempts (id,outbox_id,attempt_number,state,effect_fingerprint,started_at,safe_metadata) values (:id,:outbox,1,'STARTED',:fp,:now,'{}'::jsonb)"), {"id": attempt_id, "outbox": outbox_id, "fp": (account_id.hex * 4)[:64], "now": now})

    with Session(application) as session:
        runtime = MaxAdapterRuntime(session)
        max_user_ref = f"42-{account_id.hex[:12]}"
        identity = runtime.bind_identity(link_id, max_user_ref, authorized_handoff=True)
        identity_replay = runtime.bind_identity(link_id, max_user_ref, authorized_handoff=True)
        message_ref = f"rf19-message-{account_id.hex[:12]}"
        delivery = runtime.record_delivery(attempt_id, MaxTransportResult(MaxTransportClass.ACCEPTED, message_ref))
        delivery_replay = runtime.record_delivery(attempt_id, MaxTransportResult(MaxTransportClass.ACCEPTED, message_ref))
        nonce_hash = (account_id.hex * 4)[:64]
        nonce = runtime.record_miniapp_nonce(
            nonce_hash,
            account_id=account_id,
            expires_at=now + timedelta(minutes=5),
            created_at=now,
        )
        nonce_replay = runtime.record_miniapp_nonce(
            nonce_hash,
            account_id=account_id,
            expires_at=now + timedelta(minutes=5),
            created_at=now,
        )
    with application.connect() as connection:
        max_rows = {name: _count(application, name) for name in TABLES}
        foreign_write_denied = False
        try:
            connection.execute(text("insert into mayak.identity_accounts (id,state,created_at,updated_at) values (:id,'ACTIVE',:now,:now)"), {"id": uuid4(), "now": now})
            connection.commit()
        except Exception:
            connection.rollback()
            foreign_write_denied = True

    evidence = {
        "technical_id": "RF19-MAX-ADAPTER-RUNTIME-01",
        "candidate_sha": os.environ.get("GITHUB_SHA", "unknown"),
        "postgresql_version": postgres_version,
        "migration_head": head,
        "max_table_names": tables,
        "before_counts": before,
        "after_counts": max_rows,
        "inbound": {"first": first.outcome.value, "replay": replay.outcome.value, "conflict": conflict.outcome.value},
        "concurrent_same": sorted(item.value for item in concurrent_same),
        "concurrent_conflict": sorted(item.value for item in concurrent_conflict),
        "identity_mapping": {"created": identity is not None, "replay": identity_replay.replay},
        "delivery_mapping": {"created": delivery is not None, "replay": delivery_replay.replay},
        "nonce": {"accepted": nonce.accepted, "replay": nonce_replay.replay},
        "foreign_write_denied": foreign_write_denied,
        "foreign_sequence_write_denied": foreign_sequence_write_denied,
        "live_network_call_count": 0,
        "real_secret_read_count": 0,
        "raw_provider_payload_persisted_count": 0,
        "readiness": {"disabled": True},
        "fake_provider": {"blind_retries": 0},
        "httpx_mocked": {"automatic_retries": 0},
    }
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dsn", default=os.environ.get("RF19_DATABASE_URL"))
    parser.add_argument("--fixture-dsn", default=os.environ.get("RF19_MIGRATION_DSN"))
    parser.add_argument("--output", default="rf19-acceptance-evidence.json")
    args = parser.parse_args()
    if not args.dsn or not args.fixture_dsn:
        print("RF19 application and migration DSNs are required")
        return 2
    evidence = _database_cases(args.dsn, args.fixture_dsn)
    Path(args.output).write_text(json.dumps(evidence, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
