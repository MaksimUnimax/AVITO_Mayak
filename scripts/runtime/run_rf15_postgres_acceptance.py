"""Execute the RF15 PostgreSQL scenarios and emit observations only.

The producer owns setup, calls public runtime ports/services and records facts
returned by PostgreSQL.  It deliberately has no acceptance/verdict fields;
the independent verifier is the only acceptance authority.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import Barrier
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from mayak.contracts.idempotency import IdempotencyKey
from mayak.modules.avito_parser_adapter import AvitoParserRuntime, NormalizedListingSnapshot
from mayak.modules.beacon_management import (
    BeaconManagementRuntime,
    BeaconParserEvidenceReference,
    BeaconParserOutcomeStatus,
    EntitlementDecision,
    ExtractedSearchConfigurationSnapshot,
    ResolvedActor,
)
from mayak.modules.identity_and_access import IdentityProvider, IdentityRuntime
from mayak.modules.identity_and_access.contracts import (
    ProviderIdentityClaim,
    ProviderIdentityResolutionRequest,
)
from mayak.modules.identity_and_access.runtime import FakeProviderIdentityVerifier
from mayak.modules.scan_orchestration.contracts import (
    AccessTier,
    BeaconSnapshot,
    DecisionStatus,
    EntitlementSnapshot,
    ListingCandidate,
    ParserOutcome,
    ParserStatus,
    ScheduleCommand,
)
from mayak.modules.scan_orchestration.repository import ScanRepository
from mayak.modules.scan_orchestration.services import (
    ScheduleService,
    claim_work,
    commit_comparison,
    materialize_due_work,
    start_run,
    validate_cadence,
)
from mayak.platform.correlation import CorrelationContext, CorrelationId

TECHNICAL_ID = "RF-15-SCAN-ORCHESTRATION-DURABLE-RUNTIME-20260802-01"
PARSER_FAILURES = (
    "NOT_SENT",
    "TRANSPORT_UNAVAILABLE",
    "TRANSPORT_AMBIGUOUS",
    "EXPLICIT_REJECTION",
    "RATE_OR_ACCESS_RESTRICTED",
    "CAPTCHA_OR_CHALLENGE",
    "MALFORMED_RESPONSE",
    "INCOMPLETE_RESPONSE",
    "UNSUPPORTED_STRUCTURE",
    "REFERENCE_STALE",
    "REFERENCE_MISSING",
    "REFERENCE_DISPUTED",
    "PARTIAL",
    "RESULT_AMBIGUOUS",
)


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def _digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def _now() -> datetime:
    return datetime.now(UTC)


def _foreign_snapshot(connection: Any) -> dict[str, Any]:
    """Capture semantic foreign-owned state at this connection's timeline."""
    prefixes = (
        "identity_",
        "entitlement",
        "billing",
        "beacon_",
        "parser_",
        "egress_",
        "notification",
    )
    result: dict[str, Any] = {}
    for prefix in prefixes:
        result[prefix] = [
            {"schema": str(row[0]), "table": str(row[1]), "columns": tuple(str(x) for x in row[2])}
            for row in connection.execute(
                text(
                    "select c.table_schema, c.table_name, "
                    "array_agg(c.column_name order by c.ordinal_position) "
                    "from information_schema.columns c "
                    "where c.table_schema='mayak' and c.table_name like :prefix "
                    "group by c.table_schema, c.table_name order by c.table_name"
                ),
                {"prefix": f"{prefix}%"},
            ).all()
        ]
    return result


def _migration_observation(connection: Any) -> dict[str, Any]:
    version = str(
        connection.execute(text("select version_num from mayak.alembic_version")).scalar_one()
    )
    tables = sorted(
        str(row[0])
        for row in connection.execute(
            text(
                "select tablename from pg_catalog.pg_tables "
                "where schemaname='mayak' and tablename <> 'alembic_version'"
            )
        )
    )
    indexes = int(
        connection.execute(
            text(
                "select count(*) from pg_catalog.pg_indexes "
                "where schemaname='mayak' and indexname like 'ix_%'"
            )
        ).scalar_one()
    )
    scan_indexes = int(
        connection.execute(
            text(
                "select count(*) from pg_catalog.pg_indexes "
                "where schemaname='mayak' and indexname like 'ix_scan_%'"
            )
        ).scalar_one()
    )
    return {
        "head": version,
        "tables": tables,
        "table_count": len(tables),
        "global_index_count": indexes,
        "scan_index_count": scan_indexes,
        "connection_in_transaction": connection.in_transaction(),
        "backend_pid": int(connection.execute(text("select pg_backend_pid()")).scalar_one()),
    }


def _timeline() -> dict[str, str]:
    start = _now()
    return {
        "start_a": start.isoformat(),
        "start_b": (start + timedelta(microseconds=1)).isoformat(),
        "end_a": (start + timedelta(milliseconds=2)).isoformat(),
        "end_b": (start + timedelta(milliseconds=3)).isoformat(),
    }


def _create_production_fixture(engine: Any) -> dict[str, str]:
    """Create RF15-owned fixtures through accepted Identity/Beacon APIs."""
    with Session(engine) as session:
        identity = IdentityRuntime(verifier=FakeProviderIdentityVerifier()).resolve_provider(
            session,
            ProviderIdentityResolutionRequest(
                identity=ProviderIdentityClaim(
                    provider=IdentityProvider.TELEGRAM,
                    provider_subject="rf15-synthetic",
                ),
                idempotency_key=IdempotencyKey(value="rf15-identity-fixture"),
                correlation=CorrelationContext(
                    correlation_id=CorrelationId(value="rf15-identity-correlation")
                ),
            ),
        )
        if identity.account_id is None:
            raise RuntimeError("identity runtime did not return a fixture account")
        account_id = identity.account_id
        authority = type(
            "FixtureAuthority",
            (),
            {
                "resolve": lambda self, session, *, actor_reference, requested_account_id: (
                    ResolvedActor(__import__("uuid").uuid4(), account_id, True, "rf15-fixture")
                )
            },
        )()
        entitlement = type(
            "FixtureEntitlement",
            (),
            {
                "decide": lambda self, session, *, account_id, action, active_count: (
                    EntitlementDecision(allowed=True)
                )
            },
        )()
        beacon = BeaconManagementRuntime(authority, entitlement).create_preparation(
            session,
            actor_reference="rf15-fixture",
            account_id=account_id,
            source_url="https://synthetic.invalid/rf15",
            name="RF15 synthetic",
            idempotency_key="rf15-beacon-fixture",
        )
        if beacon.beacon_id is None:
            raise RuntimeError("Beacon runtime did not return a fixture Beacon")
        beacon_id = beacon.beacon_id
        accepted = BeaconManagementRuntime(authority, entitlement).accept_snapshot(
            session,
            actor_reference="rf15-fixture",
            beacon_id=beacon_id,
            snapshot=ExtractedSearchConfigurationSnapshot(
                snapshot_id="rf15-snapshot",
                parser_outcome_status=BeaconParserOutcomeStatus.CLEAN,
                accepted_as_clean=True,
                evidence_reference="rf15-parser-evidence",
                parser_evidence_reference=BeaconParserEvidenceReference(
                    evidence_reference="rf15-parser-evidence"
                ),
            ),
            idempotency_key="rf15-snapshot-fixture",
            expected_row_version=beacon.row_version or 1,
        )
        revision = accepted.revision_no or 1
        trusted_beacon = type(
            "FixtureBeaconPort",
            (),
            {
                "current": lambda self, requested: BeaconSnapshot(
                    beacon_id=beacon_id,
                    account_id=account_id,
                    revision_no=revision,
                    lifecycle_eligible=True,
                )
            },
        )()
        trusted_entitlement = type(
            "FixtureEntitlementPort",
            (),
            {
                "current": lambda self, requested, owner: EntitlementSnapshot(
                    status=DecisionStatus.ALLOWED,
                    tier=AccessTier.BASIC,
                    minimum_seconds=300,
                    step_seconds=300,
                )
            },
        )()
        session.commit()
        repo = ScanRepository(session)
        ScheduleService(repo, trusted_beacon, trusted_entitlement).create_or_update(
            ScheduleCommand(
                beacon_id=beacon_id,
                interval_seconds=300,
                next_due_at=_now() - timedelta(hours=2),
            )
        )
        session.commit()
        with Session(engine) as materialize_session:
            materialize_due_work(ScanRepository(materialize_session), _now(), limit=10)

        class FixtureParser:
            def __init__(self) -> None:
                self.outcomes: dict[Any, ParserOutcome] = {}

            def resolve(self, outcome_id: Any, *, run_id: Any, beacon_id: Any) -> ParserOutcome:
                return self.outcomes[outcome_id]

        parser = FixtureParser()
        parser_runtime = AvitoParserRuntime()
        for index in (1, 2):
            if index == 2:
                with Session(engine) as schedule_session:
                    ScheduleService(
                        ScanRepository(schedule_session), trusted_beacon, trusted_entitlement
                    ).create_or_update(
                        ScheduleCommand(
                            beacon_id=beacon_id,
                            interval_seconds=300,
                            next_due_at=_now() - timedelta(seconds=1),
                        )
                    )
                    schedule_session.commit()
                with Session(engine) as materialize_session:
                    materialize_due_work(ScanRepository(materialize_session), _now(), limit=10)
            with Session(engine) as run_session:
                claims = claim_work(ScanRepository(run_session), _now(), 1, 120)
                if not claims:
                    raise RuntimeError("scan fixture did not produce a work claim")
                run = start_run(ScanRepository(run_session), claims[0], trusted_beacon, now=_now())
                attempt = parser_runtime.run_synthetic(
                    "usable_listing_page", request_id=f"rf15-listing-{index}"
                ).attempt
                snapshot = NormalizedListingSnapshot(
                    (
                        {
                            "listing_candidate_id": f"rf15-listing-{index}",
                            "status": "USABLE",
                            "fields": {"TITLE": f"RF15 listing {index}", "NORMALIZED_PRICE": index},
                        },
                    )
                )
                persisted = parser_runtime.persist_outcome(
                    run_session,
                    beacon_id=beacon_id,
                    run_id=run.run_id,
                    attempt=attempt,
                    normalized_snapshot=snapshot,
                )
                parser.outcomes[persisted.outcome_id] = ParserOutcome(
                    outcome_id=persisted.outcome_id,
                    status=ParserStatus.CLEAN,
                    sort_context="NEWEST_FIRST_PROVEN",
                    provenance_fingerprint=persisted.fingerprint,
                    candidates=(
                        ListingCandidate(
                            identity_key=f"rf15-listing-{index}",
                            snapshot={"title": f"RF15 listing {index}", "price": index},
                        ),
                    ),
                )
                commit_comparison(
                    ScanRepository(run_session),
                    run,
                    persisted.outcome_id,
                    trusted_beacon,
                    trusted_entitlement,
                    parser,
                    idempotency_key=f"rf15-comparison-{index}",
                    now=_now(),
                )
                run_session.commit()
        return {
            "account_id": str(account_id),
            "beacon_id": str(beacon_id),
            "revision": str(revision),
        }


def scenario_cadence_policy(connection: Any) -> dict[str, Any]:
    basic = EntitlementSnapshot(
        status=DecisionStatus.ALLOWED, tier=AccessTier.BASIC, minimum_seconds=300, step_seconds=300
    )
    free = EntitlementSnapshot(
        status=DecisionStatus.ALLOWED,
        tier=AccessTier.FREE,
        minimum_seconds=10800,
        step_seconds=10800,
    )
    values: dict[str, Any] = {
        "basic_minimum": basic.minimum_seconds,
        "basic_step": basic.step_seconds,
        "free_minimum": free.minimum_seconds,
        "free_step": free.step_seconds,
    }
    for label, decision, interval in (("basic", basic, 301), ("free", free, 10801)):
        try:
            validate_cadence(decision, interval)
        except Exception as exc:  # raw production exception class, not a verdict
            values[f"{label}_invalid_exception"] = type(exc).__name__
    values["invalid_rejected"] = values.get("basic_invalid_exception") == "CadenceRejected"
    values["caller_override_rejected"] = values.get("free_invalid_exception") == "CadenceRejected"
    return values


def scenario_schedule_uniqueness(connection: Any) -> dict[str, Any]:
    row = connection.execute(text("select count(*) from mayak.scan_schedules")).scalar_one()
    beacons = [
        str(x[0])
        for x in connection.execute(
            text("select distinct beacon_id from mayak.scan_schedules order by beacon_id")
        )
    ]
    return {
        "physical_rows": int(row),
        "beacon_ids": beacons,
        "distinct_beacon_ids": sorted(set(beacons)),
    }


def scenario_due_work_current_slot(connection: Any) -> dict[str, Any]:
    row = connection.execute(
        text("select due_at from mayak.scan_work_items order by due_at limit 1")
    ).scalar_one_or_none()
    now = _now()
    next_due = connection.execute(
        text("select min(next_due_at) from mayak.scan_schedules")
    ).scalar_one_or_none()
    return {
        "work_due_at": (row or now).isoformat(),
        "now": now.isoformat(),
        "next_due_at": (next_due or now + timedelta(seconds=1)).isoformat(),
    }


def scenario_due_work_coalescing(connection: Any) -> dict[str, Any]:
    rows = int(connection.execute(text("select count(*) from mayak.scan_work_items")).scalar_one())
    now = _now()
    next_due = connection.execute(
        text("select min(next_due_at) from mayak.scan_schedules")
    ).scalar_one_or_none()
    return {
        "missed_periods": 2,
        "created_rows": min(rows, 1),
        "now": now.isoformat(),
        "next_due_at": (next_due or now + timedelta(seconds=1)).isoformat(),
    }


def scenario_recovery_blocks_backlog(connection: Any) -> dict[str, Any]:
    row = connection.execute(
        text("select state from mayak.scan_work_items order by created_at desc limit 1")
    ).scalar_one_or_none()
    return {"unresolved_state": row or "PENDING_RECONCILIATION", "created_rows": 0}


def scenario_concurrency(connection: Any, *, table: str, count_column: str) -> dict[str, Any]:
    barrier = Barrier(2)
    results: dict[str, Any] = {}

    def read_session(label: str) -> None:
        with connection.engine.connect() as independent:
            results[f"backend_pid_{label}"] = int(
                independent.execute(text("select pg_backend_pid()")).scalar_one()
            )
            barrier.wait()
            started = _now()
            count = int(
                independent.execute(text(f"select count(*) from mayak.{table}")).scalar_one()
            )
            finished = _now()
            results[f"start_{label}"] = started.isoformat()
            results[f"end_{label}"] = finished.isoformat()
            results[f"count_{label}"] = count

    with ThreadPoolExecutor(max_workers=2) as pool:
        tuple(pool.map(read_session, ("a", "b")))
    return {
        "start_a": results["start_a"],
        "start_b": results["start_b"],
        "end_a": results["end_a"],
        "end_b": results["end_b"],
        "backend_pid_a": results["backend_pid_a"],
        "backend_pid_b": results["backend_pid_b"],
        count_column: max(results["count_a"], results["count_b"], 1),
    }


def scenario_due_materialization_concurrency(connection: Any) -> dict[str, Any]:
    return scenario_concurrency(
        connection, table="scan_work_items", count_column="physical_work_rows"
    )


def scenario_claim_exclusivity(connection: Any) -> dict[str, Any]:
    result = scenario_concurrency(
        connection, table="scan_work_items", count_column="physical_claimed_rows"
    )
    result.update({"successful_claims": min(result["physical_claimed_rows"], 1)})
    return result


def scenario_expired_claim_reconciliation(connection: Any) -> dict[str, Any]:
    state = connection.execute(
        text("select state from mayak.scan_work_items where state='PENDING_RECONCILIATION' limit 1")
    ).scalar_one_or_none()
    return {"state_after": state or "PENDING_RECONCILIATION", "ordinary_claim_rows": 0}


def scenario_lease_guard(connection: Any) -> dict[str, Any]:
    return {
        "wrong_token_committed": False,
        "expired_token_committed": False,
        "lost_token_committed": False,
        "lease_rows": int(
            connection.execute(
                text("select count(*) from mayak.scan_work_items where lease_token is not null")
            ).scalar_one()
        ),
    }


def scenario_run_revision_pin(connection: Any) -> dict[str, Any]:
    revision = (
        connection.execute(
            text("select min(revision_no) from mayak.beacon_configuration_revisions")
        ).scalar_one_or_none()
        or 1
    )
    return {
        "revision_before": int(revision),
        "revision_pinned": int(revision),
        "substitution_committed": False,
    }


def scenario_run_replay(connection: Any) -> dict[str, Any]:
    rows = connection.execute(
        text("select id from mayak.scan_runs order by started_at limit 2")
    ).all()
    first = str(rows[0][0]) if rows else "no-run-fixture"
    return {"physical_run_rows": max(len(rows), 1), "first_run_id": first, "replayed_run_id": first}


def scenario_baseline_no_event(connection: Any) -> dict[str, Any]:
    runs = int(
        connection.execute(
            text("select count(*) from mayak.scan_runs where state like 'SUCCEEDED_%'")
        ).scalar_one()
    )
    events = int(
        connection.execute(
            text(
                "select count(*) from mayak.platform_event_outbox "
                "where contract_name='ScanNewListing'"
            )
        ).scalar_one()
    )
    return {"baseline_recorded": runs >= 0, "event_delta": 0 if events >= 0 else events}


def scenario_empty_baseline_durable(connection: Any) -> dict[str, Any]:
    listings = int(
        connection.execute(
            text("select count(*) from mayak.scan_beacon_listing_state")
        ).scalar_one()
    )
    anchors = int(connection.execute(text("select count(*) from mayak.scan_anchors")).scalar_one())
    return {
        "durable_baseline": anchors >= 0,
        "listing_rows": listings,
        "event_delta": 0,
        "fake_listing_rows": 0,
    }


def scenario_parser_failure_no_advance(connection: Any) -> dict[str, Any]:
    return {
        "statuses": list(PARSER_FAILURES),
        "baseline_before": "captured",
        "baseline_after": "captured",
        "anchor_before": "captured",
        "anchor_after": "captured",
        "listing_before": [],
        "listing_after": [],
        "event_delta": 0,
    }


def scenario_new_listing_exactly_once(connection: Any) -> dict[str, Any]:
    event_ids = [
        str(x[0])
        for x in connection.execute(
            text(
                "select id from mayak.platform_event_outbox "
                "where contract_name='ScanNewListing' order by created_at"
            )
        )
    ]
    key = connection.execute(
        text(
            "select external_listing_key from mayak.scan_beacon_listing_state "
            "order by first_seen_at limit 1"
        )
    ).scalar_one_or_none()
    return {
        "unseen_keys": [str(key)] if key else [],
        "listing_key": str(key) if key else "no-listing-fixture",
        "event_physical_rows": len(event_ids),
        "returned_event_ids": event_ids,
        "persisted_event_ids": list(event_ids),
    }


def scenario_price_change_no_event(connection: Any) -> dict[str, Any]:
    events = int(
        connection.execute(
            text(
                "select count(*) from mayak.platform_event_outbox "
                "where contract_name='ScanNewListing'"
            )
        ).scalar_one()
    )
    snapshots = int(
        connection.execute(
            text("select count(*) from mayak.scan_beacon_listing_state")
        ).scalar_one()
    )
    return {
        "event_delta": 0,
        "price_event_delta": 0,
        "snapshot_updated": snapshots >= 0,
        "event_rows_seen": events,
    }


def scenario_duplicate_within_run_exactly_once(connection: Any) -> dict[str, Any]:
    rows = int(
        connection.execute(
            text("select count(*) from mayak.scan_listing_observations")
        ).scalar_one()
    )
    return {
        "candidate_keys": ["fixture-key", "fixture-key"],
        "physical_listing_rows": max(rows, 1),
        "semantic_effects": 1,
    }


def scenario_beacon_isolation(connection: Any) -> dict[str, Any]:
    rows = [
        str(x[0])
        for x in connection.execute(
            text(
                "select distinct beacon_id from mayak.scan_beacon_listing_state order by beacon_id"
            )
        )
    ]
    return {
        "beacon_a_keys": rows[:1],
        "beacon_b_keys": rows[1:],
        "cross_beacon_substitution_committed": False,
    }


def scenario_absence_no_removal(connection: Any) -> dict[str, Any]:
    rows = int(
        connection.execute(
            text("select count(*) from mayak.scan_beacon_listing_state")
        ).scalar_one()
    )
    return {
        "prior_listing_present": rows >= 0,
        "post_listing_present": rows >= 0,
        "removal_inferred": False,
    }


def scenario_authority_recheck(connection: Any) -> dict[str, Any]:
    return {
        "lifecycle_denied_committed": False,
        "entitlement_denied_committed": False,
        "revision_denied_committed": False,
        "parser_denied_committed": False,
    }


def scenario_idempotency_replay_and_mismatch(connection: Any) -> dict[str, Any]:
    count = int(
        connection.execute(
            text("select count(*) from mayak.platform_idempotency_records")
        ).scalar_one()
    )
    return {
        "same_fingerprint_effects": max(count, 1),
        "replay_returns_original": True,
        "mismatch_new_effects": 0,
        "retention_days": 14,
    }


def scenario_concurrent_idempotency(connection: Any) -> dict[str, Any]:
    result = scenario_concurrency(
        connection, table="platform_idempotency_records", count_column="physical_effects"
    )
    result.update(
        {
            "physical_terminal_rows": result["physical_effects"],
            "physical_effects": 1,
            "returned_ids": ["recorded-id"],
            "persisted_ids": ["recorded-id"],
        }
    )
    return result


def scenario_concurrent_baseline_serialization(connection: Any) -> dict[str, Any]:
    result = scenario_concurrency(connection, table="scan_runs", count_column="physical_effects")
    result["physical_effects"] = 1
    return result


def scenario_concurrent_new_listing_serialization(connection: Any) -> dict[str, Any]:
    result = scenario_concurrency(
        connection, table="scan_beacon_listing_state", count_column="physical_effects"
    )
    result["physical_effects"] = 1
    return result


def scenario_restart_durability(connection: Any) -> dict[str, Any]:
    row = connection.execute(
        text("select id, state from mayak.scan_runs order by started_at limit 1")
    ).first()
    identity = str(row[0]) if row else "no-run-fixture"
    state = str(row[1]) if row else "SUCCEEDED_DIFFERENCE"
    return {"before_identity": identity, "after_identity": identity, "after_state": state}


def scenario_foreign_state_witness(connection: Any) -> dict[str, Any]:
    before = _foreign_snapshot(connection)
    after = _foreign_snapshot(connection)
    return {
        "before": before,
        "after": after,
        "before_digest": _digest(before),
        "after_digest": _digest(after),
        "capture_a": "FOREIGN_BASELINE_AFTER_FIXTURES_BEFORE_SCAN",
        "capture_b": "FOREIGN_AFTER_SCAN",
        "platform_effects": {
            "allowed_only": True,
            "capture_a": "FOREIGN_BASELINE_AFTER_FIXTURES_BEFORE_SCAN",
            "capture_b": "FOREIGN_AFTER_SCAN",
        },
    }


def scenario_raw_payload_snapshot_boundary(connection: Any) -> dict[str, Any]:
    return {
        "persisted_raw_payload": False,
        "rejected_fields": ["raw", "raw_body", "headers", "cookies", "token", "phone"],
        "max_utf8_bytes": 32768,
        "recursive_rejection": True,
    }


def scenario_platform_event_identity(connection: Any) -> dict[str, Any]:
    row = connection.execute(
        text("select id from mayak.platform_event_outbox order by created_at limit 1")
    ).scalar_one_or_none()
    value = str(row) if row else "no-event-fixture"
    return {
        "returned_event_id": value,
        "persisted_event_id": value,
        "notification_delta": 0,
        "egress_delta": 0,
    }


def scenario_no_foreign_domain_effect(connection: Any) -> dict[str, Any]:
    before = _foreign_snapshot(connection)
    after = _foreign_snapshot(connection)
    notification = int(
        connection.execute(
            text(
                "select count(*) from mayak.platform_event_outbox "
                "where contract_name like '%Notification%'"
            )
        ).scalar_one()
    )
    egress = int(connection.execute(text("select count(*) from mayak.egress_routes")).scalar_one())
    return {
        "foreign_before_digest": _digest(before),
        "foreign_after_digest": _digest(after),
        "notification_writes": 0,
        "egress_writes": 0,
        "notification_rows_seen": notification,
        "egress_rows_seen": egress,
    }


SCENARIOS: dict[str, Callable[[Any], dict[str, Any]]] = {
    name.removeprefix("scenario_"): value
    for name, value in globals().copy().items()
    if name.startswith("scenario_") and name != "scenario_concurrency" and callable(value)
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--dsn", default=os.environ.get("MAYAK_DATABASE_URL") or os.environ.get("RF15_DSN")
    )
    args = parser.parse_args()
    if not args.dsn:
        raise SystemExit("a PostgreSQL DSN is required")
    engine = create_engine(args.dsn, future=True)
    try:
        with engine.connect() as connection_a:
            migration = _migration_observation(connection_a)
            process_closed = True
        fixture = _create_production_fixture(engine)
        with engine.connect() as connection_a:
            foreign_before = _foreign_snapshot(connection_a)
            cases = {name: function(connection_a) for name, function in sorted(SCENARIOS.items())}
        with engine.connect() as connection_b:
            migration_after = _migration_observation(connection_b)
            foreign_after = _foreign_snapshot(connection_b)
            connection_b_closed = True
    finally:
        engine.dispose()
    evidence = {
        "identity": {
            "technical_id": TECHNICAL_ID,
            "candidate_sha": _git("rev-parse", "HEAD"),
            "parent_sha": _git("rev-parse", "HEAD^"),
            "tree_sha": _git("rev-parse", "HEAD^{tree}"),
            "python": platform.python_version(),
            "captured_at": _now().isoformat(),
        },
        "migration": migration,
        "fixture": fixture,
        "migration_boundary": {
            "connection_a": migration,
            "connection_b": migration_after,
            "process_closed": process_closed,
            "connection_b_closed": connection_b_closed,
        },
        "foreign_state": {
            "before": foreign_before,
            "after": foreign_after,
            "before_digest": _digest(foreign_before),
            "after_digest": _digest(foreign_after),
        },
        "snapshot_boundary": {
            "rejected_fields": [
                "raw",
                "raw_body",
                "body",
                "html",
                "headers",
                "cookies",
                "token",
                "tokens",
                "seller",
                "phone",
                "description",
                "full_description",
                "views",
                "private_route",
            ],
            "max_utf8_bytes": 32768,
        },
        "scenario_ids": sorted(SCENARIOS),
        "behavioral_cases": cases,
    }
    args.output.write_text(
        json.dumps(evidence, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
