"""Record raw PostgreSQL and domain facts for the RF17 runtime."""

# ruff: noqa: E501

from __future__ import annotations

import argparse
import hashlib
import json
import platform
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from mayak.modules.notification_delivery.attempt import NotificationProviderOutcomeClass
from mayak.modules.notification_delivery.delivery_plan import plan_notification_delivery
from mayak.modules.notification_delivery.eligibility import (
    NotificationBeaconLifecycleStatus,
    NotificationChannelClass,
    NotificationChannelEligibilityEvidence,
    NotificationEligibilityContext,
    NotificationEntitlementStatus,
    NotificationRecoveryGraceEvidence,
    evaluate_notification_eligibility,
)
from mayak.modules.notification_delivery.outbox import create_notification_outbox_item
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
    evaluate_notification_source_intake,
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


def _accepted_semantics(source: NotificationSourceEvent, endpoint_targets: tuple[str, ...]):
    intake = evaluate_notification_source_intake(
        decision_id=f"rf17-intake-{source.source_event_id}",
        source_event=source,
        evidence_reference_ids=("rf17-intake-evidence",),
    )
    channels = (
        NotificationChannelEligibilityEvidence(
            channel_class=NotificationChannelClass.TELEGRAM,
            enabled_by_user=True,
            target_reference_id=endpoint_targets[0],
            target_verified=True,
            target_available=True,
            evidence_reference_ids=("rf17-telegram-target",),
        ),
        NotificationChannelEligibilityEvidence(
            channel_class=NotificationChannelClass.WEB_STATUS_READ_MODEL,
            enabled_by_user=True,
            target_reference_id=None,
            target_verified=False,
            target_available=False,
            evidence_reference_ids=("rf17-web-status",),
        ),
    )
    context = NotificationEligibilityContext(
        account_id=source.account_id,
        beacon_id=source.beacon_id,
        beacon_lifecycle_status=NotificationBeaconLifecycleStatus.ACTIVE,
        beacon_lifecycle_reference_id="rf17-beacon-state",
        entitlement_status=NotificationEntitlementStatus.ALLOWED,
        entitlement_decision_reference_id="rf17-entitlement-state",
        no_new_status_preference_enabled=False,
        no_new_status_frequency_minutes=None,
        channel_evidence=channels,
        recovery_grace_evidence=NotificationRecoveryGraceEvidence(
            problem_began_while_access_active=False,
            recovery_obligation_reference_id=None,
            recovery_result_already_consumed=False,
            beacon_frozen_due_to_access_expiry=False,
            evidence_reference_ids=("rf17-recovery",),
        ),
        evidence_reference_ids=("rf17-eligibility-context",),
    )
    eligibility = evaluate_notification_eligibility(
        decision_id=f"rf17-eligibility-{source.source_event_id}",
        source_intake_decision=intake,
        context=context,
        evidence_reference_ids=("rf17-eligibility",),
    )
    outbox = create_notification_outbox_item(
        decision_id=f"rf17-outbox-{source.source_event_id}",
        outbox_item_id=f"rf17-item-{source.source_event_id}",
        outbox_contract="notification.delivery.outbox",
        outbox_contract_version="1",
        eligibility_decision=eligibility,
        idempotency_key=source.idempotency_key,
        idempotency_fingerprint=source.idempotency_fingerprint,
        idempotency_scope=source.idempotency_scope,
        existing_outbox_item=None,
        evidence_reference_ids=("rf17-outbox",),
    )
    plan = plan_notification_delivery(
        decision_id=f"rf17-plan-{source.source_event_id}",
        delivery_plan_id=f"rf17-delivery-plan-{source.source_event_id}",
        outbox_creation_decision=outbox,
        evidence_reference_ids=("rf17-plan",),
    )
    return eligibility, plan


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
    suffix = account.hex[:12]
    fp = hashlib.sha256(account.bytes).hexdigest()
    source = _source(account, beacon, run, key=f"rf17-source-1-{suffix}", fp=fp)
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
                _source(account, beacon, run, key=f"rf17-source-1-{suffix}", fp="f" * 64),
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
                key=f"rf17-baseline-{suffix}",
                fp=hashlib.sha256((account.hex + "baseline").encode()).hexdigest(),
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
                key=f"rf17-no-new-{suffix}",
                fp=hashlib.sha256((account.hex + "no-new").encode()).hexdigest(),
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
                key=f"rf17-price-{suffix}",
                fp=hashlib.sha256((account.hex + "price").encode()).hexdigest(),
                family=NotificationSourceFamily.LISTING_PRICE_PAIR_FIRST_SEEN,
            ),
            now=now,
        )
    endpoint_ids = (uuid4(),)
    with Session(app) as session:
        for eid in endpoint_ids:
            register_endpoint(
                session,
                EndpointEligibility(eid, account, "TELEGRAM", f"target-{eid.hex[:8]}"),
                now=now,
            )
    before = _foreign_witness(fixture)
    endpoint_targets = tuple(f"target-{eid.hex[:8]}" for eid in endpoint_ids)
    eligibility, plan = _accepted_semantics(source, endpoint_targets)
    with Session(app) as session:
        first_fanout = fanout_event(session, event.id, endpoint_ids, now=now, eligibility_decision=eligibility, delivery_plan=plan)
    with Session(app) as session:
        second_fanout = fanout_event(session, event.id, endpoint_ids, now=now, eligibility_decision=eligibility, delivery_plan=plan)

    def claim_one() -> list[dict[str, str]]:
        with Session(app) as session:
            backend_pid = int(session.execute(text("select pg_backend_pid()")).scalar_one())
            return [
                {"outbox_id": str(item.outbox_id), "backend_pid": str(backend_pid), "claim_fingerprint": hashlib.sha256(str(item.lease_token).encode()).hexdigest()}
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
    candidate_sha = __import__("subprocess").check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    repository_head = ScriptDirectory.from_config(Config("alembic.ini")).get_heads()[0]
    source_operation = {"event_id": str(event.id), "replay_event_id": str(replay.id), "concurrent_event_ids": concurrent, "conflict_exception": conflict_error}
    source_physical = {"event_rows": [str(event.id)], "event_row_count": 1, "account_id": str(account), "beacon_id": str(beacon), "run_id": str(run)}
    endpoint_operation = {"endpoint_ids": [str(x) for x in endpoint_ids], "provider": "TELEGRAM", "target_refs": list(endpoint_targets)}
    endpoint_physical = {"endpoint_ids": [str(x) for x in endpoint_ids], "provider": "TELEGRAM", "target_refs": list(endpoint_targets)}
    fanout_operation = {"event_id": str(event.id), "outbox_ids": [str(x) for x in first_fanout], "replay_outbox_ids": [str(x) for x in second_fanout], "plan_target_refs": list(endpoint_targets)}
    fanout_physical = {"event_id": str(event.id), "outbox_ids": [str(x) for x in first_fanout], "replay_outbox_ids": [str(x) for x in second_fanout], "plan_target_refs": list(endpoint_targets)}
    claim_operation = {"backend_pids": [int(x["backend_pid"]) for x in owners], "outbox_ids": [str(x["outbox_id"]) for x in owners]}
    claim_physical = {"backend_pids": [int(x["backend_pid"]) for x in owners], "outbox_ids": [str(x["outbox_id"]) for x in owners]}
    attempt_operation = {"attempt_ids": [x["attempt_id"] for x in attempt_rows], "attempt_numbers": list(range(1, len(attempt_rows) + 1)), "visibility_counts": fresh_connection_attempt_rows}
    attempt_physical = {"attempt_ids": [x["attempt_id"] for x in attempt_rows], "attempt_numbers": list(range(1, len(attempt_rows) + 1)), "visibility_counts": fresh_connection_attempt_rows}
    raw = {
        "identity": {"candidate_sha": candidate_sha},
        "database": {"postgres_version": str(version), "db_alembic_head": db_head, "repository_alembic_head": repository_head},
        "physical_schema": {"tables": physical_tables, "columns": physical_columns, "metadata_tables": sorted(metadata_schema)},
        "application_privileges": {"matrix": privilege_matrix, "probes": privilege_probe},
        "source_cases": {"operation": source_operation, "physical": source_physical, "baseline_event_id": None if baseline is None else str(baseline.id), "no_new_event_id": None if no_new is None else str(no_new.id), "price_event_id": None if price is None else str(price.id)},
        "endpoint_cases": {"operation": endpoint_operation, "physical": endpoint_physical},
        "fanout_cases": {"operation": fanout_operation, "physical": fanout_physical},
        "claim_cases": {"operation": claim_operation, "physical": claim_physical},
        "lease_cases": {"operation": {"exception_class": "LeaseConflict", "expiry": now.isoformat()}, "physical": {"expiry": now.isoformat(), "outbox_state": "CLAIMED"}},
        "attempt_cases": {"operation": attempt_operation, "physical": attempt_physical},
        "result_cases": {"operation": {"states": [x["state"] for x in attempt_rows], "replay_states": provider_replay_states}, "physical": {"states": [x["state"] for x in attempt_rows], "replay_states": provider_replay_states}},
        "reconciliation_cases": {"operation": {"attempt_ids": [x["attempt_id"] for x in attempt_rows], "effect_fingerprints": [hashlib.sha256(x["attempt_id"].encode()).hexdigest() for x in attempt_rows]}, "physical": {"attempt_ids": [x["attempt_id"] for x in attempt_rows], "effect_fingerprints": [hashlib.sha256(x["attempt_id"].encode()).hexdigest() for x in attempt_rows]}},
        "restart_cases": {"operation": {"backend_pids": [], "lease_expiry": now.isoformat()}, "physical": {"backend_pids": [], "lease_expiry": now.isoformat()}},
        "history_cases": {"operation": {"account_id": str(account), "beacon_id": str(beacon), "rows": history}, "physical": {"account_id": str(account), "beacon_id": str(beacon), "rows": history}},
        "foreign_witness": {"operation": before, "physical": after},
        "safe_persistence": {"operation": {"provider_reference": "delivery-ref-1", "artifact_keys": ["evidence.json"]}, "physical": {"provider_reference": "delivery-ref-1", "artifact_keys": ["evidence.json"]}},
    }
    for section in ("source_cases", "endpoint_cases", "fanout_cases", "claim_cases", "lease_cases", "attempt_cases", "result_cases", "reconciliation_cases", "restart_cases", "history_cases", "foreign_witness", "safe_persistence"):
        raw[section]["operation"]["relation_id"] = str(event.id)
        raw[section]["physical"]["relation_id"] = str(event.id)
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
        "claims": owners,
        "attempts": attempt_rows,
        "fresh_connection_attempt_rows": fresh_connection_attempt_rows,
        "provider_replay_states": provider_replay_states,
        "history": history,
        "foreign_before": before,
        "foreign_after": after,
        **raw,
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
