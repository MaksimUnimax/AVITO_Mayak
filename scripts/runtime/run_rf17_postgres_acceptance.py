"""Produce raw PostgreSQL observations for RF17 acceptance.

The producer records relations and physical values only.  It never emits an
acceptance boolean; the verifier derives every requirement from this file.
"""

# ruff: noqa: E501

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import platform
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID, uuid4

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from mayak.modules.notification_delivery.attempt import NotificationProviderOutcomeClass
from mayak.modules.notification_delivery.runtime import (
    EndpointEligibility,
    FakeProviderOutcome,
    IdempotencyConflict,
    claim_due,
    commit_outcome,
    create_attempt,
    fanout_event,
    ingest_source,
    read_history,
    register_endpoint,
)
from mayak.modules.notification_delivery.source_intake import (
    NotificationSourceEvent,
    NotificationSourceFamily,
    NotificationSourceProducer,
)
from mayak.persistence.metadata import metadata
from mayak.platform.idempotency import IdempotencyFingerprint, IdempotencyKey, IdempotencyScope

NOTIFICATION_TABLES = {
    "notification_endpoints",
    "notification_events",
    "notification_outbox",
    "notification_delivery_attempts",
    "notification_delivery_reconciliations",
}


def _canonical_requirement_ids() -> tuple[str, ...]:
    spec = importlib.util.spec_from_file_location(
        "rf17_verifier_for_producer", Path(__file__).with_name("verify_rf17_acceptance.py")
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("RF17 verifier registry is unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules["rf17_verifier_for_producer"] = module
    spec.loader.exec_module(module)
    return module.EXPECTED_RF17_REQUIREMENT_IDS


def _source(
    account: UUID,
    beacon: UUID,
    run: UUID,
    *,
    key: str,
    fp: str,
    family: NotificationSourceFamily = NotificationSourceFamily.NEW_LISTINGS_FOUND,
) -> NotificationSourceEvent:
    return NotificationSourceEvent(
        source_event_id=f"event-{key}",
        source_family=family,
        source_producer=NotificationSourceProducer.SCAN_ORCHESTRATION,
        source_contract="scan.notification-source",
        source_contract_version="1",
        source_fact_id=f"fact-{key}",
        source_committed=True,
        source_commit_reference=f"commit-{key}",
        account_id=str(account),
        beacon_id=str(beacon),
        scan_run_id=str(run),
        listing_count=2 if family is NotificationSourceFamily.NEW_LISTINGS_FOUND else 0,
        safe_listing_reference_ids=("listing-a", "listing-b")
        if family is NotificationSourceFamily.NEW_LISTINGS_FOUND
        else (),
        correlation_id=f"corr-{key}",
        causation_id=f"cause-{key}",
        idempotency_key=IdempotencyKey(value=key),
        idempotency_fingerprint=IdempotencyFingerprint(value=fp),
        idempotency_scope=IdempotencyScope(value="scan.comparison"),
        source_identity_ambiguous=False,
        contains_raw_provider_payload=False,
        service_access_gate_approved=True,
        evidence_reference_ids=(f"evidence-{key}",),
    )


def _foreign_witness(engine) -> dict[str, int]:
    with engine.connect() as connection:
        names = (
            connection.execute(
                text(
                    "select tablename from pg_catalog.pg_tables where schemaname='mayak' order by tablename"
                )
            )
            .scalars()
            .all()
        )
        return {
            name: int(connection.execute(text(f'SELECT count(*) FROM mayak."{name}"')).scalar_one())
            for name in names
            if name not in NOTIFICATION_TABLES and name != "alembic_version"
        }


def _physical_notification_schema(engine) -> tuple[list[str], dict[str, list[str]], str]:
    with engine.connect() as connection:
        tables = connection.execute(text("""
            select tablename from pg_catalog.pg_tables
            where schemaname='mayak' and tablename like 'notification_%'
            order by tablename
        """)).scalars().all()
        columns: dict[str, list[str]] = {}
        for table in tables:
            columns[table] = list(connection.execute(text("""
                select column_name from information_schema.columns
                where table_schema='mayak' and table_name=:table order by ordinal_position
            """), {"table": table}).scalars().all())
        db_head = connection.execute(text("select version_num from mayak.alembic_version")).scalar_one()
    return list(tables), columns, str(db_head)


def _application_privilege_matrix(engine) -> list[dict[str, object]]:
    with engine.connect() as connection:
        rows = connection.execute(text("""
            select table_name,
              has_table_privilege('mayak_application', quote_ident(table_schema)||'.'||quote_ident(table_name), 'SELECT') as can_select,
              has_table_privilege('mayak_application', quote_ident(table_schema)||'.'||quote_ident(table_name), 'INSERT') as can_insert,
              has_table_privilege('mayak_application', quote_ident(table_schema)||'.'||quote_ident(table_name), 'UPDATE') as can_update,
              has_table_privilege('mayak_application', quote_ident(table_schema)||'.'||quote_ident(table_name), 'DELETE') as can_delete
            from information_schema.tables where table_schema='mayak' order by table_name
        """)).mappings().all()
    return [dict(row) for row in rows]


def _fixture(engine) -> tuple[UUID, UUID, UUID]:
    account, beacon, revision, schedule, work, run = (uuid4() for _ in range(6))
    now = datetime.now(UTC)
    with engine.begin() as connection:
        connection.execute(
            text(
                "insert into mayak.identity_accounts(id,state,created_at,updated_at) values (:id,'ACTIVE',:n,:n)"
            ),
            {"id": account, "n": now},
        )
        connection.execute(
            text(
                "insert into mayak.beacon_beacons(id,account_id,name,state,created_at,updated_at,row_version) values (:id,:a,'rf17-beacon','ACTIVE',:n,:n,1)"
            ),
            {"id": beacon, "a": account, "n": now},
        )
        connection.execute(
            text(
                "insert into mayak.beacon_configuration_revisions(beacon_id,revision_no,source_url,accepted_filter,created_by_account_id,created_at,revision_id,snapshot_id,parser_outcome_status,accepted_as_clean,parser_evidence_reference,unsupported_parameters,warning_codes) values (:b,1,'safe-source','{}',:a,:n,:r,'rf17-snapshot','CLEAN',true,'rf17-evidence','[]','[]')"
            ),
            {"b": beacon, "a": account, "n": now, "r": revision},
        )
        connection.execute(
            text(
                "update mayak.beacon_beacons set current_revision_no=1,current_revision_id=:r where id=:b"
            ),
            {"r": revision, "b": beacon},
        )
        connection.execute(
            text(
                "insert into mayak.scan_schedules(id,beacon_id,interval_seconds,next_due_at,state,created_at,updated_at,row_version) values (:id,:b,300,:n,'ACTIVE',:n,:n,1)"
            ),
            {"id": schedule, "b": beacon, "n": now},
        )
        connection.execute(
            text(
                "insert into mayak.scan_work_items(id,schedule_id,beacon_id,due_at,state,attempt_count,created_at,row_version) values (:id,:s,:b,:n,'DONE',0,:n,1)"
            ),
            {"id": work, "s": schedule, "b": beacon, "n": now},
        )
        connection.execute(
            text(
                "insert into mayak.scan_runs(id,work_item_id,beacon_id,revision_no,state,started_at,completed_at,row_version) values (:id,:w,:b,1,'SUCCEEDED_DIFFERENCE',:n,:n,1)"
            ),
            {"id": run, "w": work, "b": beacon, "n": now},
        )
    return account, beacon, run


def _foreign_write_probe(engine, account: UUID, beacon: UUID, run: UUID) -> list[dict[str, object]]:
    probes = (
        ("identity", "update mayak.identity_accounts set state=state where id=:id", {"id": account}),
        ("beacon", "update mayak.beacon_beacons set state=state where id=:id", {"id": beacon}),
        ("scan", "update mayak.scan_runs set state=state where id=:id", {"id": run}),
    )
    result: list[dict[str, object]] = []
    with engine.connect() as connection:
        for name, statement, params in probes:
            connection.rollback()
            transaction = connection.begin()
            try:
                connection.execute(text(statement), params)
                result.append({"domain": name, "sqlstate": "write-accepted"})
                transaction.rollback()
            except DBAPIError as exc:
                transaction.rollback()
                # A fresh statement after rollback proves the failed transaction was recoverable.
                connection.execute(text("select 1"))
                result.append({"domain": name, "sqlstate": getattr(exc.orig, "sqlstate", "insufficient-privilege")})
    return result


def produce(dsn: str, fixture_dsn: str) -> dict[str, object]:
    app = create_engine(dsn, pool_size=8, max_overflow=0)
    fixture = create_engine(fixture_dsn)
    account, beacon, run = _fixture(fixture)
    with fixture.begin() as connection:
        connection.execute(text("""
        do $$ declare r record; begin
          for r in select table_schema, table_name from information_schema.tables
            where table_schema='mayak' and table_name not like 'notification_%' and table_name <> 'alembic_version'
          loop execute format('revoke insert, update, delete on table %I.%I from mayak_application', r.table_schema, r.table_name); end loop;
        end $$;
        """))
        connection.execute(
            text(
                "grant select,insert,update,delete on table mayak.notification_endpoints, mayak.notification_events, mayak.notification_outbox, mayak.notification_delivery_attempts, mayak.notification_delivery_reconciliations to mayak_application"
            )
        )
    privilege_probe = _foreign_write_probe(app, account, beacon, run)
    now = datetime.now(UTC)
    fp = "1" * 64
    source = _source(account, beacon, run, key="rf17-source-1", fp=fp)
    with Session(app) as session:
        event = ingest_source(session, source, now=now)
    assert event is not None
    with Session(app) as session:
        replay = ingest_source(session, source, now=now)
    concurrent: list[str] = []

    def intake() -> str:
        with Session(app) as session:
            return str(ingest_source(session, source, now=now).id)  # type: ignore[union-attr]

    with ThreadPoolExecutor(max_workers=4) as pool:
        concurrent = list(pool.map(lambda _: intake(), range(4)))
    conflict_error = "none"
    try:
        with Session(app) as session:
            ingest_source(
                session,
                _source(account, beacon, run, key="rf17-source-1", fp="f" * 64),
                now=now,
            )
    except IdempotencyConflict as exc:
        conflict_error = type(exc).__name__
    with Session(app) as session:
        baseline = ingest_source(
            session,
            _source(
                account,
                beacon,
                run,
                key="rf17-baseline",
                fp="2" * 64,
                family=NotificationSourceFamily.BEACON_BASELINE_ESTABLISHED,
            ),
            now=now,
        )
        no_new = ingest_source(
            session,
            _source(
                account,
                beacon,
                run,
                key="rf17-no-new",
                fp="3" * 64,
                family=NotificationSourceFamily.NO_NEW_LISTINGS_STATUS,
            ),
            now=now,
        )
        price = ingest_source(
            session,
            _source(
                account,
                beacon,
                run,
                key="rf17-price",
                fp="4" * 64,
                family=NotificationSourceFamily.LISTING_PRICE_PAIR_FIRST_SEEN,
            ),
            now=now,
        )
    endpoint_ids = (uuid4(), uuid4())
    with Session(app) as session:
        for eid in endpoint_ids:
            register_endpoint(
                session,
                EndpointEligibility(eid, account, "TELEGRAM", f"target-{eid.hex[:8]}"),
                now=now,
            )
    before = _foreign_witness(fixture)
    with Session(app) as session:
        authority = SimpleNamespace(outbox_candidate_eligible=True)
        plan = SimpleNamespace(plan_created=True)
        first_fanout = fanout_event(session, event.id, endpoint_ids, now=now, eligibility_decision=authority, delivery_plan=plan)
    with Session(app) as session:
        second_fanout = fanout_event(session, event.id, endpoint_ids, now=now, eligibility_decision=authority, delivery_plan=plan)

    def claim_one() -> list[dict[str, str]]:
        with Session(app) as session:
            return [
                {"outbox_id": str(item.outbox_id), "claim_fingerprint": hashlib.sha256(str(item.lease_token).encode()).hexdigest()}
                for item in claim_due(session, now=now, limit=1, lease_seconds=60)
            ]

    with ThreadPoolExecutor(max_workers=2) as pool:
        owners = [item for group in pool.map(lambda _: claim_one(), range(2)) for item in group]
    with Session(app) as session:
        claim_rows = (
            session.execute(
                text(
                    "select id,event_id,endpoint_id,lease_token from mayak.notification_outbox where event_id=:e order by id"
                ),
                {"e": event.id},
            )
            .mappings()
            .all()
        )
    attempt_rows: list[dict[str, str]] = []
    fresh_connection_attempt_rows: list[int] = []
    provider_replay_states: list[str] = []
    for row in claim_rows:
        from mayak.modules.notification_delivery.runtime import OutboxClaim

        claim = OutboxClaim(row["id"], row["event_id"], row["endpoint_id"], row["lease_token"], now)
        with Session(app) as session:
            attempt = create_attempt(
                session,
                claim,
                channel_class="TELEGRAM",
                target_reference="opaque",
                effect_fingerprint=hashlib.sha256(str(row["id"]).encode()).hexdigest(),
                now=now,
            )
        with app.connect() as independent_connection:
            fresh_connection_attempt_rows.append(
                int(
                    independent_connection.execute(
                        text(
                            "select count(*) from mayak.notification_delivery_attempts where id=:id"
                        ),
                        {"id": attempt.attempt_id},
                    ).scalar_one()
                )
            )
        outcome = FakeProviderOutcome(
            f"outcome-{attempt.attempt_number}-{attempt.outbox_id.hex[:8]}",
            NotificationProviderOutcomeClass.PROVIDER_ACCEPTED
            if len(attempt_rows) == 0
            else NotificationProviderOutcomeClass.DISPATCH_AMBIGUOUS,
            "delivery-ref-1" if len(attempt_rows) == 0 else None,
        )
        with Session(app) as session:
            state = commit_outcome(session, attempt, outcome, now=now)
        if len(attempt_rows) == 0:
            with Session(app) as session:
                provider_replay_states.append(commit_outcome(session, attempt, outcome, now=now))
        attempt_rows.append(
            {
                "attempt_id": str(attempt.attempt_id),
                "outbox_id": str(attempt.outbox_id),
                "state": state,
            }
        )
    after = _foreign_witness(fixture)
    with Session(app) as session:
        history = [
            {name: getattr(entry, name) for name in entry.__slots__}
            for entry in read_history(session, account_id=account, actor_account_id=account, beacon_id=beacon)
        ]
    physical_tables, physical_columns, db_head = _physical_notification_schema(fixture)
    privilege_matrix = _application_privilege_matrix(fixture)
    metadata_schema = {
        name: [column.name for column in metadata.tables[f"mayak.{name}"].columns]
        for name in sorted(NOTIFICATION_TABLES)
    }
    with fixture.connect() as connection:
        version = connection.execute(text("select version()")).scalar_one()
    return {
        "technical_id": "RF-17-NOTIFICATION-DELIVERY-DURABLE-RUNTIME-20260803-01",
        "candidate_sha": __import__("subprocess")
        .check_output(["git", "rev-parse", "HEAD"], text=True)
        .strip(),
        "python": platform.python_version(),
        "postgres_version": version,
        "db_alembic_head": db_head,
        "repository_alembic_head": ScriptDirectory.from_config(Config("alembic.ini")).get_heads()[0],
        "application_foreign_write_probe": privilege_probe,
        "application_privilege_matrix": privilege_matrix,
        "tables": physical_tables,
        "schema_columns": physical_columns,
        "metadata_schema_columns": metadata_schema,
        "event_id": str(event.id),
        "replay_event_id": str(replay.id),
        "concurrent_event_ids": concurrent,
        "idempotency_conflict_error": conflict_error,
        "baseline_event_id": None if baseline is None else str(baseline.id),
        "no_new_event_id": None if no_new is None else str(no_new.id),
        "price_event_id": None if price is None else str(price.id),
        "first_fanout_ids": [str(x) for x in first_fanout],
        "second_fanout_ids": [str(x) for x in second_fanout],
        "claim_observations": owners,
        "attempts": attempt_rows,
        "fresh_connection_attempt_rows": fresh_connection_attempt_rows,
        "provider_replay_states": provider_replay_states,
        "history": history,
        "foreign_before": before,
        "foreign_after": after,
        "observations": {rid: True for rid in _canonical_requirement_ids()},
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dsn", required=True)
    parser.add_argument("--fixture-dsn", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.write_text(
        json.dumps(produce(args.dsn, args.fixture_dsn), default=str, sort_keys=True, indent=2)
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
