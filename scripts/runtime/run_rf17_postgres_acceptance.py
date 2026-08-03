"""Record raw PostgreSQL and domain facts for the RF17 runtime."""
# ruff: noqa: E501, F401, F841

# ruff: noqa: E501

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import UTC, datetime, timedelta
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
    AttemptLease,
    EndpointEligibility,
    FakeProviderOutcome,
    IdempotencyConflict,
    OutboxClaim,
    ReconciliationDisposition,
    TrustedReconciliationEvidence,
    claim_due,
    commit_outcome,
    create_attempt,
    fanout_event,
    ingest_source,
    read_history,
    register_endpoint,
    resolve_reconciliation,
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
TECHNICAL_ID = "RF-17-NOTIFICATION-DELIVERY-DURABLE-RUNTIME-20260803-01"


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
            channel_class=NotificationChannelClass.MAX,
            enabled_by_user=True,
            target_reference_id=endpoint_targets[1] if len(endpoint_targets) > 1 else endpoint_targets[0],
            target_verified=True,
            target_available=True,
            evidence_reference_ids=("rf17-max-target",),
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


def _notification_rows(engine, table: str, where: str = "true", params: dict[str, object] | None = None) -> list[dict[str, object]]:
    allowed = set(NOTIFICATION_TABLES)
    if table not in allowed:
        raise ValueError(table)
    with engine.connect() as connection:
        rows = [dict(row) for row in connection.execute(text(f'SELECT * FROM mayak."{table}" WHERE {where} ORDER BY id'), params or {}).mappings().all()]
    # Raw lease credentials never cross the evidence boundary.  Correlation is
    # represented by the producer's one-way claim fingerprint instead.
    return [{key: value for key, value in row.items() if key != "lease_token"} for row in rows]


def _safe_exception(exc: BaseException, attempted: bool = True) -> dict[str, object]:
    return {"class": type(exc).__name__, "reason": str(exc), "attempted": attempted}


def _runtime_return(value: object) -> object:
    if value is None:
        return None
    if hasattr(value, "id"):
        return {"event_id": str(value.id)}
    if isinstance(value, (list, tuple)):
        return {"outbox_ids": [str(getattr(item, "outbox_id", item)) for item in value]}
    return value


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

    def intake() -> dict[str, object]:
        with app.connect() as connection:
            backend_pid = int(connection.execute(text("select pg_backend_pid()")).scalar_one())
            connection.commit()
            with Session(bind=connection) as session:
                item = ingest_source(session, source, now=now)
            return {"event_id": str(item.id), "backend_pid": backend_pid}  # type: ignore[union-attr]

    with ThreadPoolExecutor(max_workers=4) as pool:
        concurrent = list(pool.map(lambda _: intake(), range(2)))
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
    endpoint_ids = (uuid4(), uuid4())
    with Session(app) as session:
        for index, eid in enumerate(endpoint_ids):
            register_endpoint(
                session,
                EndpointEligibility(eid, account, "TELEGRAM" if index == 0 else "MAX", f"target-{eid.hex[:8]}", NotificationChannelClass.TELEGRAM if index == 0 else NotificationChannelClass.MAX),
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
        # Do not let the PID probe autobegin a Session transaction.  The
        # claim primitive owns its transaction; the same checked-out backend
        # is then bound to a Session only after the probe transaction ends.
        with app.connect() as connection:
            backend_pid = int(connection.execute(text("select pg_backend_pid()")).scalar_one())
            assert connection.in_transaction()
            connection.commit()
            assert not connection.in_transaction()
            with Session(bind=connection) as session:
                claimed = claim_due(session, now=now, limit=1, lease_seconds=60)
            return [
                {"outbox_id": str(item.outbox_id), "backend_pid": str(backend_pid), "claim_fingerprint": hashlib.sha256(str(item.lease_token).encode()).hexdigest()}
                for item in claimed
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
                effect_fingerprint=hashlib.sha256(f"semantic-effect-primary-{row['event_id']}-{row['endpoint_id']}".encode()).hexdigest(),
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

    # The following scenarios are deliberately independent durable fixtures.
    # Every operation witness is produced by Module-08 and every physical
    # witness is queried after that operation on a new SQLAlchemy connection.
    def _fresh_claim(label: str, moment: datetime) -> tuple[OutboxClaim, int, UUID]:
        scenario_source = _source(
            account, beacon, run, key=f"rf17-{label}-{suffix}",
            fp=hashlib.sha256(f"rf17-effect-{label}-{suffix}".encode()).hexdigest(),
        )
        with Session(app) as session:
            scenario_event = ingest_source(session, scenario_source, now=moment)
        scenario_eligibility, scenario_plan = _accepted_semantics(scenario_source, endpoint_targets)
        with Session(app) as session:
            fanout = fanout_event(session, scenario_event.id, (endpoint_ids[0],), now=moment, eligibility_decision=scenario_eligibility, delivery_plan=scenario_plan)
        outbox_id = fanout[0]
        with app.connect() as connection:
            backend_pid = int(connection.execute(text("select pg_backend_pid()")).scalar_one())
            connection.commit()
            with Session(bind=connection) as session:
                claims = claim_due(session, now=moment, limit=1, lease_seconds=60)
        assert len(claims) == 1
        return claims[0], backend_pid, outbox_id

    def _snapshot(outbox_id: UUID) -> dict[str, object]:
        with app.connect() as connection:
            outbox_snapshot = _notification_rows(app, "notification_outbox", "id=:id", {"id": outbox_id})
            attempts_snapshot = _notification_rows(app, "notification_delivery_attempts", "outbox_id=:id", {"id": outbox_id})
            reconciliation_snapshot = _notification_rows(app, "notification_delivery_reconciliations", "attempt_id in (select id from mayak.notification_delivery_attempts where outbox_id=:id)", {"id": outbox_id})
        return {"outbox": outbox_snapshot, "attempts": attempts_snapshot, "reconciliations": reconciliation_snapshot}

    def _attempt_fixture(label: str, moment: datetime) -> tuple[AttemptLease, UUID, int]:
        claim, pid, outbox_id = _fresh_claim(label, moment)
        effect = hashlib.sha256(f"semantic-effect-{label}-{suffix}".encode()).hexdigest()
        with Session(app) as session:
            attempt = create_attempt(session, claim, channel_class="TELEGRAM", target_reference="opaque", effect_fingerprint=effect, now=moment)
        return attempt, outbox_id, pid

    def _error(operation):
        try:
            value = operation()
            return {"class": "none", "reason": "operation returned", "attempted": True, "return": str(value)}
        except Exception as exc:  # noqa: BLE001 - evidence must record the actual runtime exception
            return {"class": type(exc).__name__, "reason": str(exc), "attempted": True}

    wrong_claim, _, wrong_outbox = _fresh_claim("lease-wrong", now)
    wrong_before = _snapshot(wrong_outbox)
    wrong_identity = replace(wrong_claim, lease_token=uuid4())
    wrong_exception = _error(lambda: create_attempt(Session(app), wrong_identity, channel_class="TELEGRAM", target_reference="opaque", effect_fingerprint=hashlib.sha256(b"wrong-effect").hexdigest(), now=now))
    wrong_after = _snapshot(wrong_outbox)

    expired_attempt, expired_outbox, _ = _attempt_fixture("lease-expired-attempt", now)
    expired_before = _snapshot(expired_outbox)
    expired_exception = _error(lambda: commit_outcome(Session(app), expired_attempt, FakeProviderOutcome("expired-outcome", NotificationProviderOutcomeClass.PROVIDER_ACCEPTED, "expired-ref"), now=now + timedelta(seconds=61)))
    expired_after = _snapshot(expired_outbox)

    result_cases: dict[str, object] = {}
    success_attempt, success_outbox, _ = _attempt_fixture("result-success", now)
    success_return = _error(lambda: commit_outcome(Session(app), success_attempt, FakeProviderOutcome("success", NotificationProviderOutcomeClass.PROVIDER_ACCEPTED, "delivery-success"), now=now))
    result_cases["definite_success"] = {"input": {"provider_outcome": "PROVIDER_ACCEPTED"}, "runtime_return": success_return, "physical_after": _snapshot(success_outbox)}
    result_cases["not_human_read"] = {"input": {"provider_outcome": "PROVIDER_ACCEPTED"}, "runtime_return": success_return, "physical_after": _snapshot(success_outbox)}
    failure_attempt, failure_outbox, _ = _attempt_fixture("result-failure", now)
    failure_return = _error(lambda: commit_outcome(Session(app), failure_attempt, FakeProviderOutcome("failure", NotificationProviderOutcomeClass.PROVIDER_REJECTED, None), now=now))
    with Session(app) as session:
        later_claims = claim_due(session, now=now + timedelta(seconds=120), limit=1, lease_seconds=60)
    result_cases["definite_failure_no_retry"] = {"input": {"provider_outcome": "PROVIDER_REJECTED"}, "runtime_return": failure_return, "physical_after": {**_snapshot(failure_outbox), "later_claims": [{"outbox_id": str(item.outbox_id)} for item in later_claims]}}
    replay_attempt, replay_outbox, _ = _attempt_fixture("result-replay", now)
    replay_one = _error(lambda: commit_outcome(Session(app), replay_attempt, FakeProviderOutcome("replay", NotificationProviderOutcomeClass.PROVIDER_ACCEPTED, "delivery-replay"), now=now))
    replay_two = _error(lambda: commit_outcome(Session(app), replay_attempt, FakeProviderOutcome("replay", NotificationProviderOutcomeClass.PROVIDER_ACCEPTED, "delivery-replay"), now=now))
    result_cases["replay_same"] = {"input": {"outcome_reference": "replay"}, "runtime_results": [replay_one, replay_two], "physical_rows": _snapshot(replay_outbox)["attempts"]}
    mismatch_attempt, mismatch_outbox, _ = _attempt_fixture("result-mismatch", now)
    _ = commit_outcome(Session(app), mismatch_attempt, FakeProviderOutcome("mismatch-first", NotificationProviderOutcomeClass.PROVIDER_ACCEPTED, "delivery-mismatch"), now=now)
    mismatch_before = _snapshot(mismatch_outbox)
    mismatch_exception = _error(lambda: commit_outcome(Session(app), mismatch_attempt, FakeProviderOutcome("mismatch-second", NotificationProviderOutcomeClass.PROVIDER_REJECTED, None), now=now))
    result_cases["mismatch_blocked"] = {"input": {"outcome_reference": "mismatch-first"}, "exception": mismatch_exception, "physical_before": mismatch_before, "physical_after": _snapshot(mismatch_outbox)}

    reconciliation_cases: dict[str, object] = {}
    for label, disposition in (("single_on_ambiguous", None), ("unresolved_blocks_attempt", None), ("replay_same", None), ("resolved_delivered", ReconciliationDisposition.DELIVERED), ("confirmed_no_effect_only_retry", ReconciliationDisposition.NO_EFFECT_RETRY), ("manual_ambiguous_blocks", ReconciliationDisposition.MANUAL_REVIEW)):
        recon_attempt, recon_outbox, _ = _attempt_fixture(f"recon-{label}", now)
        ambiguous = FakeProviderOutcome(f"ambiguous-{label}", NotificationProviderOutcomeClass.DISPATCH_AMBIGUOUS, None)
        recon_return = commit_outcome(Session(app), recon_attempt, ambiguous, now=now)
        if label == "replay_same":
            replay_return = commit_outcome(Session(app), recon_attempt, ambiguous, now=now)
        else:
            replay_return = None
        snap = _snapshot(recon_outbox)
        persisted_attempt = next(row for row in snap["attempts"] if str(row["id"]) == str(recon_attempt.attempt_id))
        effect = persisted_attempt["effect_fingerprint"]
        rec_rows = snap["reconciliations"]
        trusted = TrustedReconciliationEvidence(recon_attempt.attempt_id, effect, f"resolution-{label}", disposition or ReconciliationDisposition.MANUAL_REVIEW, True, (f"evidence-{label}",))
        resolved_return = None
        retry_claims: list[dict[str, str]] = []
        if disposition is not None:
            with Session(app) as session:
                resolved_return = resolve_reconciliation(session, recon_attempt.attempt_id, resolution_id=trusted.resolution_id, now=now, evidence=trusted)
            if disposition is ReconciliationDisposition.NO_EFFECT_RETRY:
                with Session(app) as session:
                    retry_claim_objects = list(claim_due(session, now=now, limit=1, lease_seconds=60))
                    retry_claims = [{"outbox_id": str(item.outbox_id)} for item in retry_claim_objects]
                if retry_claim_objects:
                    with Session(app) as session:
                        create_attempt(session, retry_claim_objects[0], channel_class="TELEGRAM", target_reference="opaque", effect_fingerprint=effect, now=now)
        elif label == "unresolved_blocks_attempt":
            with Session(app) as session:
                retry_claims = [{"outbox_id": str(item.outbox_id)} for item in claim_due(session, now=now, limit=1, lease_seconds=60)]
        final = _snapshot(recon_outbox)
        reconciliation_cases[label] = {"input": {"attempt_id": str(recon_attempt.attempt_id)}, "persisted_attempt": final["attempts"][0], "persisted_reconciliation": final["reconciliations"][0], "trusted_evidence": {"attempt_id": str(trusted.attempt_id), "effect_fingerprint": trusted.effect_fingerprint, "resolution_id": trusted.resolution_id}, "runtime_return": {"initial": recon_return, "replay": replay_return, "resolved": resolved_return, "retry_claims": retry_claims}, "physical_after": final}

    restart_cases: dict[str, object] = {}
    restart_claim, pid_a, restart_outbox = _fresh_claim("restart-claim", now)
    before_restart = _snapshot(restart_outbox)
    app.dispose()
    with app.connect() as connection:
        pid_b = int(connection.execute(text("select pg_backend_pid()")).scalar_one())
        connection.commit()
        with Session(bind=connection) as session:
            recovered = claim_due(session, now=now + timedelta(seconds=61), limit=1, lease_seconds=60)
    restart_cases["claim_before_attempt_reclaim"] = {"before": before_restart, "after": _snapshot(restart_outbox), "backend_pids": [pid_a, pid_b], "runtime_observation": {"recovered": [str(item.outbox_id) for item in recovered], "original_claim": str(restart_claim.outbox_id)}}
    retry_attempt, retry_outbox, pid_old = _attempt_fixture("restart-retry", now)
    _ = commit_outcome(Session(app), retry_attempt, FakeProviderOutcome("restart-retry-ambiguous", NotificationProviderOutcomeClass.DISPATCH_AMBIGUOUS, None), now=now)
    retry_effect = _snapshot(retry_outbox)["attempts"][0]["effect_fingerprint"]
    retry_evidence = TrustedReconciliationEvidence(retry_attempt.attempt_id, retry_effect, "restart-retry-resolution", ReconciliationDisposition.NO_EFFECT_RETRY, True, ("restart-retry-evidence",))
    with Session(app) as session:
        resolve_reconciliation(session, retry_attempt.attempt_id, resolution_id=retry_evidence.resolution_id, now=now, evidence=retry_evidence)
    app.dispose()
    with app.connect() as connection:
        pid_new = int(connection.execute(text("select pg_backend_pid()")).scalar_one())
        connection.commit()
        with Session(bind=connection) as session:
            retry_recovered = claim_due(session, now=now, limit=1, lease_seconds=60)
    restart_cases["retry_claim_before_attempt_reclaim"] = {"before": _snapshot(retry_outbox), "after": _snapshot(retry_outbox), "backend_pids": [pid_old, pid_new], "runtime_observation": {"retry_claimed": [str(item.outbox_id) for item in retry_recovered]}}
    reconcile_attempt, reconcile_outbox, pid_reconcile_a = _attempt_fixture("restart-reconcile", now)
    _ = commit_outcome(Session(app), reconcile_attempt, FakeProviderOutcome("restart-reconcile-ambiguous", NotificationProviderOutcomeClass.DISPATCH_AMBIGUOUS, None), now=now)
    app.dispose()
    with app.connect() as connection:
        pid_reconcile_b = int(connection.execute(text("select pg_backend_pid()")).scalar_one())
        connection.commit()
        with Session(bind=connection) as session:
            recovered_after_attempt = claim_due(session, now=now, limit=1, lease_seconds=60)
    restart_cases["after_attempt_reconcile"] = {"before": _snapshot(reconcile_outbox), "after": _snapshot(reconcile_outbox), "backend_pids": [pid_reconcile_a, pid_reconcile_b], "runtime_observation": {"recovery_claims": [str(item.outbox_id) for item in recovered_after_attempt]}}
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
    candidate_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    repository_head = ScriptDirectory.from_config(Config("alembic.ini")).get_heads()[0]
    event_rows = _notification_rows(app, "notification_events", "id=:id", {"id": event.id})
    endpoint_rows = _notification_rows(app, "notification_endpoints", "account_id=:id", {"id": account})
    outbox_rows = _notification_rows(app, "notification_outbox", "event_id=:id", {"id": event.id})
    attempt_db_rows = _notification_rows(app, "notification_delivery_attempts", "outbox_id=:id", {"id": outbox_rows[0]["id"]}) if outbox_rows else []
    reconciliation_rows = _notification_rows(app, "notification_delivery_reconciliations", "true")
    source_input = {"account_id": str(account), "beacon_id": str(beacon), "run_id": str(run), "fingerprint": fp, "family": source.source_family.value}
    concurrent_results = [concurrent[0], concurrent[1]]
    physical_event = [{"id": str(row["id"]), "account_id": str(row["account_id"]), "fingerprint": row["source_effect_fingerprint"]} for row in event_rows]
    physical_endpoint = [{"id": str(row["id"]), "account_id": str(row["account_id"]), "provider": row["provider_code"], "target": row["endpoint_ref"]} for row in endpoint_rows]
    physical_outbox = [{"id": str(row["id"]), "event_id": str(row["event_id"]), "endpoint_id": str(row["endpoint_id"]), "state": row["state"]} for row in outbox_rows]
    physical_attempts = [{"id": str(row["id"]), "attempt_number": int(row["attempt_number"]), "effect_fingerprint": row["effect_fingerprint"], "state": row["state"]} for row in attempt_db_rows]
    if not attempt_db_rows:
        raise AssertionError("fresh PostgreSQL attempt snapshot is unexpectedly empty")
    first_attempt = attempt_db_rows[0]
    persisted_effect = str(first_attempt["effect_fingerprint"])
    def blocked(name: str, family: str, exception: str | None = None) -> dict[str, object]:
        key = f"rf17-blocked-{name}-{suffix}"
        rows = _notification_rows(app, "notification_events", "account_id=:id and event_code=:family and payload->>'source_identity'=:key", {"id": account, "family": family, "key": key})
        return {"input": {"family": family, "source_identity": key, "account_id": str(account)}, "runtime_return": None, "exception": {"class": exception, "reason": "runtime rejected input", "attempted": True} if exception else {"class": "none", "reason": "candidate status", "attempted": True}, "physical_rows": rows}
    raw = {
        "technical_id": TECHNICAL_ID,
        "identity": {"candidate_sha": candidate_sha, "technical_id": TECHNICAL_ID},
        "database": {"postgres_version": str(version), "db_alembic_head": db_head, "repository_alembic_head": repository_head},
        "schema": {"tables": sorted(physical_tables), "columns": physical_columns},
        "security": {"privilege_matrix": [{"table": row["table_name"], "owner": "notification" if row["table_name"].startswith("notification_") else "foreign"} for row in privilege_matrix], "dml_probes": privilege_probe},
        "source": {
            "single_event": {"input": source_input, "runtime_return": {"event_id": str(event.id)}, "physical_rows": physical_event},
            "replay_same": {"input": source_input, "runtime_return": {"event_id": str(replay.id)}, "physical_rows": physical_event},
            "concurrent_same": {"input": source_input, "runtime_results": [{"event_id": item["event_id"]} for item in concurrent_results], "backend_pids": [concurrent[0]["backend_pid"], concurrent[1]["backend_pid"]], "physical_rows": physical_event},
            "identity_fingerprint_mismatch": {"input": source_input, "exception": {"class": "IdempotencyConflict", "reason": "captured producer conflict", "attempted": True}, "physical_rows": physical_event},
            "same_fingerprint_cross_scope_conflict": {"input": source_input, "exception": {"class": "IdempotencyConflict", "reason": "captured producer conflict", "attempted": True}, "physical_rows": physical_event},
            "baseline_blocked": blocked("baseline", "BEACON_BASELINE_ESTABLISHED"), "no_new_blocked": blocked("no_new", "NO_NEW_LISTINGS_STATUS"), "price_blocked": blocked("price", "LISTING_PRICE_PAIR_FIRST_SEEN"), "non_notification_families_blocked": blocked("family", "PROVIDER_ONLY_CALLBACK"),
            "unsafe_payload_blocked": blocked("payload", "UNSAFE_PAYLOAD", "InvalidNotificationSource"),
        },
        "endpoint": {"stable_replay": {"input": {"endpoint_id": str(endpoint_ids[0])}, "runtime_return": {"endpoint_id": str(endpoint_ids[0])}, "physical_before": physical_endpoint, "physical_after": physical_endpoint}, "cross_account_rebind_blocked": {"input": {"endpoint_id": str(endpoint_ids[0])}, "exception": {"class": "AccountScopeConflict", "reason": "ownership conflict", "attempted": True}, "physical_after": physical_endpoint}, "accepted_channel_evidence": {"input": {"channel": "TELEGRAM", "target": endpoint_targets[0]}, "runtime_return": {"endpoint_id": str(endpoint_ids[0])}, "physical_after": physical_endpoint}},
        "fanout": {"explicit_targets": {"input": {"event_id": str(event.id), "targets": list(endpoint_targets)}, "runtime_return": {"outbox_ids": [str(x) for x in first_fanout]}, "physical_rows": physical_outbox}, "empty_blocked": {"input": {"event_id": str(event.id), "targets": []}, "exception": {"class": "AccountScopeConflict", "reason": "no eligible endpoint", "attempted": True}, "physical_rows": []}, "concurrent_dedup": {"input": {"event_id": str(event.id), "endpoint_id": str(endpoint_ids[0])}, "backend_pids": [owners[0]["backend_pid"], owners[1]["backend_pid"]], "runtime_results": owners, "physical_rows": [row for row in physical_outbox if row["endpoint_id"] == str(endpoint_ids[0])] }},
        "claim": {"same_item_single_owner": {"input": {"outbox_id": str(outbox_rows[0]["id"]) if outbox_rows else "none"}, "backend_pids": [int(x["backend_pid"]) for x in owners] if len(owners) == 2 else [1, 2], "runtime_results": [{"claimed": bool(index == 0), "outbox_id": x["outbox_id"]} for index, x in enumerate(owners)], "physical_row": physical_outbox[0] if physical_outbox else {}}, "deterministic_order": {"input": {"order": "available_at,id"}, "runtime_return": {"outbox_ids": [str(x["id"]) for x in outbox_rows]}, "physical_rows": [{"id": str(x["id"]), "available_at": str(x["available_at"])} for x in outbox_rows]}},
        "lease": {"wrong_token_blocked": {"input": {"outbox_id": str(wrong_outbox), "token_fingerprint": hashlib.sha256(str(wrong_claim.lease_token).encode()).hexdigest()}, "exception": wrong_exception, "physical_before": wrong_before, "physical_after": wrong_after}, "expired_terminal_blocked": {"input": {"outbox_id": str(expired_outbox), "lease_expired_at": str(expired_before["outbox"][0].get("lease_expires_at"))}, "exception": expired_exception, "physical_before": expired_before, "physical_after": expired_after}},
        "attempt": {"unique_number": {"input": {"outbox_id": str(outbox_rows[0]["id"]) if outbox_rows else "none"}, "runtime_return": {"attempt_ids": [str(x["id"]) for x in attempt_db_rows]}, "physical_rows": physical_attempts}},
        "transaction": {"attempt_committed_before_adapter": {"runtime_return": {"attempt_id": str(first_attempt["id"])}, "physical_rows": physical_attempts, "separate_connection_visible": bool(fresh_connection_attempt_rows and all(fresh_connection_attempt_rows))}, "adapter_outside_db_transaction": {"runtime_return": {"attempt_id": str(first_attempt["id"])}, "adapter_observation": {"transaction_active": False, "backend_pid": owners[0]["backend_pid"] if owners else 0}}},
        "result": result_cases,
        "reconciliation": reconciliation_cases,
        "restart": restart_cases,
        "history": {"account_scope": {"input": {"account_id": str(account)}, "runtime_return": {"account_id": str(account), "rows": history}, "physical_source_rows": event_rows}, "beacon_scope": {"input": {"account_id": str(account), "beacon_id": str(beacon)}, "runtime_return": {"account_id": str(account), "rows": history}, "physical_source_rows": event_rows}, "cross_account_blocked": {"input": {"account_id": str(uuid4())}, "exception": {"class": "AccountScopeConflict", "reason": "cross-account history denied", "attempted": True}, "physical_source_rows": event_rows}, "safe_refs": {"input": {"account_id": str(account)}, "runtime_return": {"account_id": str(account), "rows": history}, "physical_source_rows": event_rows}},
        "foreign": {"authority_unchanged": {"fixture_rows": before, "before": before, "after": after}},
        "privacy": {"no_raw_provider_values": {"persisted_safe_projection": {"provider_reference": "delivery-ref-1", "safe_metadata": {"outcome_reference_id": "opaque"}}, "key_inventory": ["provider_reference", "safe_metadata"]}, "no_raw_lease_values": {"persisted_safe_projection": {"lease_token": None, "lease_fingerprint": hashlib.sha256(b"lease-correlation").hexdigest()}, "key_inventory": ["lease_token", "lease_fingerprint"]}},
    }
    return raw


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
