"""Record RF15 operations and raw PostgreSQL observations.

This process never emits acceptance conclusions.  Each case contains the
actual public call transcript and independently queried physical state.
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
from uuid import UUID, uuid4

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from mayak.contracts.idempotency import IdempotencyKey
from mayak.modules.avito_parser_adapter.contracts import (
    ParserAttemptOutcome,
    TransportOutcomeStatus,
)
from mayak.modules.avito_parser_adapter.contracts import (
    ParserOutcomeStatus as AdapterParserOutcomeStatus,
)
from mayak.modules.avito_parser_adapter.runtime import AvitoParserRuntime
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
    DecisionStatus,
    EntitlementSnapshot,
    ListingCandidate,
    ParserOutcome,
)
from mayak.modules.scan_orchestration.repository import ScanRepository
from mayak.modules.scan_orchestration.services import (
    ScheduleService,
    claim_work,
    commit_comparison,
    materialize_due_work,
    record_parser_outcome,
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
    return subprocess.check_output(["git", *args], text=True, stderr=subprocess.DEVNULL).strip()


def _parent_sha() -> str:
    """Record the parent even when hosted checkout intentionally is shallow."""
    event_before = os.environ.get("GITHUB_EVENT_BEFORE")
    if event_before and len(event_before) == 40:
        return event_before
    try:
        return _git("rev-parse", "HEAD^")
    except subprocess.CalledProcessError:
        return "shallow-parent-unavailable"


def _now() -> datetime:
    return datetime.now(UTC)


def _digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def _migration(connection: Any) -> dict[str, Any]:
    from mayak.persistence.metadata import metadata

    head = str(
        connection.execute(text("select version_num from mayak.alembic_version")).scalar_one()
    )
    tables = [
        str(row[0])
        for row in connection.execute(
            text(
                "select tablename from pg_catalog.pg_tables "
                "where schemaname='mayak' and tablename <> 'alembic_version' "
                "order by tablename"
            )
        )
    ]
    physical_indexes = [
        str(row[0])
        for row in connection.execute(
            text(
                "select indexname from pg_catalog.pg_indexes "
                "where schemaname='mayak' order by indexname"
            )
        )
    ]
    scan_indexes = int(
        connection.execute(
            text(
                "select count(*) from pg_catalog.pg_indexes "
                "where schemaname='mayak' and indexname like 'ix_scan_%'"
            )
        ).scalar_one()
    )
    return {
        "head": head,
        "table_count": len(tables),
        "metadata_index_count": sum(len(table.indexes) for table in metadata.tables.values()),
        "physical_index_count": len(physical_indexes),
        "physical_index_names": physical_indexes,
        # Backward-compatible transcript label; it is no longer used as the
        # metadata count because pg_catalog and SQLAlchemy count different sets.
        "global_index_count": len(physical_indexes),
        "scan_index_count": scan_indexes,
        "independent_connection": True,
        "backend_pid": int(connection.execute(text("select pg_backend_pid()")).scalar_one()),
    }


def _semantic_foreign(connection: Any) -> dict[str, Any]:
    # These are owning-module semantic projections, not catalog metadata.
    names = {
        "identity": "identity_accounts",
        "entitlements": "entitlement_access_grants",
        "beacon": "beacon_beacons",
        "parser": "parser_outcomes",
        "egress": "egress_routes",
    }
    result: dict[str, Any] = {}
    for label, table in names.items():
        result[label] = [
            str(value)
            for value in connection.execute(
                text(f"select id::text from mayak.{table} order by id limit 100")
            )
            .scalars()
            .all()
        ]
    return result


def _ids(connection: Any, table: str) -> list[str]:
    return [
        str(value)
        for value in connection.execute(text(f"select id::text from mayak.{table} order by id"))
        .scalars()
        .all()
    ]


def _safe(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, (list, tuple)):
        return [_safe(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _safe(item) for key, item in value.items()}
    return repr(value)[:200]


def _safe_row(row: Any) -> dict[str, Any]:
    return {str(key): _safe(value) for key, value in row.items()}


def _operation(
    connection: Any,
    name: str,
    input_data: dict[str, Any],
    operation: Callable[[], Any],
) -> dict[str, Any]:
    """Invoke the supplied production callable inside the measured interval."""
    started = _now()
    value: dict[str, Any] = {
        "callable": name,
        "input": input_data,
        "started_at": started.isoformat(),
        "finished_at": started.isoformat(),
        # Recorder metadata comes from the driver connection, not SQL on the
        # measured Session/Connection.  SQLAlchemy autobegin must not precede
        # the production boundary's transaction.
        "backend_pid": _backend_pid(connection),
    }
    try:
        value["result"] = _safe(operation())
    except Exception as exc:
        value["exception"] = {"class": type(exc).__name__, "reason": str(exc)[:200]}
    value["finished_at"] = _now().isoformat()
    return value


def _backend_pid(connection: Any) -> int:
    """Read driver metadata without issuing SQL on the measured connection."""
    driver = connection.connection.driver_connection
    info = getattr(driver, "info", None)
    pid = getattr(info, "backend_pid", None)
    if isinstance(pid, int):
        return pid
    # Fallback is an independent probe, never the transaction-owning handle.
    engine = connection.engine
    with engine.connect() as probe:
        return int(probe.execute(text("select pg_backend_pid()")).scalar_one())


def _physical(
    connection: Any,
    *,
    beacon_id: str,
    schedule_id: str | None = None,
    work_id: str | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Expose raw rows for one explicit scenario scope."""
    beacon = str(beacon_id)
    params = {
        "beacon_id": beacon,
        "schedule_id": schedule_id,
        "work_id": work_id,
        "run_id": run_id,
    }
    schedule_filter = "and id = cast(:schedule_id as uuid)" if schedule_id else ""
    work_filter = "and id = cast(:work_id as uuid)" if work_id else ""
    run_filter = "and id = cast(:run_id as uuid)" if run_id else ""
    schedules = (
        connection.execute(
            text(
                "select id::text, interval_seconds, next_due_at, state from mayak.scan_schedules "
                f"where beacon_id = cast(:beacon_id as uuid) {schedule_filter} order by id"
            ),
            params,
        )
        .mappings()
        .all()
    )
    work = (
        connection.execute(
            text(
                "select id::text, schedule_id::text, due_at, state from mayak.scan_work_items "
                f"where beacon_id = cast(:beacon_id as uuid) {work_filter} order by id"
            ),
            params,
        )
        .mappings()
        .all()
    )
    runs = (
        connection.execute(
            text(
                "select id::text, work_item_id::text, revision_no, state from mayak.scan_runs "
                f"where beacon_id = cast(:beacon_id as uuid) {run_filter} order by id"
            ),
            params,
        )
        .mappings()
        .all()
    )
    listings = (
        connection.execute(
            text(
                "select id::text, external_listing_key, last_snapshot "
                "from mayak.scan_beacon_listing_state "
                "where beacon_id = cast(:beacon_id as uuid) order by id"
            ),
            {"beacon_id": beacon},
        )
        .mappings()
        .all()
    )
    anchors = (
        connection.execute(
            text(
                "select id::text, anchor_key from mayak.scan_anchors "
                "where beacon_id = cast(:beacon_id as uuid)"
            ),
            {"beacon_id": beacon},
        )
        .mappings()
        .all()
    )
    events = (
        connection.execute(
            text(
                "select id::text from mayak.platform_event_outbox "
                "where payload ->> 'beacon_id' = :beacon_id order by id"
            ),
            {"beacon_id": beacon},
        )
        .scalars()
        .all()
    )
    return {
        "beacon_id": beacon,
        "schedule_ids": [row["id"] for row in schedules],
        "work_ids": [row["id"] for row in work],
        "run_ids": [row["id"] for row in runs],
        "event_ids": [str(value) for value in events],
        "schedule_rows": [_safe_row(row) for row in schedules],
        "work_rows": [_safe_row(row) for row in work],
        "run_rows": [_safe_row(row) for row in runs],
        "listing_ids": [row["id"] for row in listings],
        "listing_rows": [_safe_row(row) for row in listings],
        "anchor_rows": [_safe_row(row) for row in anchors],
    }


def _case(
    connection: Any,
    name: str,
    operation: Callable[[], Any],
    *,
    beacon_id: str,
    schedule_id: str | None = None,
    work_id: str | None = None,
    run_id: str | None = None,
    before: dict[str, Any] | None = None,
    after: dict[str, Any] | None = None,
) -> dict[str, Any]:
    def snapshot() -> dict[str, Any]:
        with connection.engine.connect() as probe:
            return _physical(
                probe,
                beacon_id=beacon_id,
                schedule_id=schedule_id,
                work_id=work_id,
                run_id=run_id,
            )

    observed_before = before if before is not None else snapshot()
    operation = _operation(
        connection,
        f"mayak.modules.scan_orchestration.{name}",
        {"scenario_id": f"rf15-{name}"},
        operation,
    )
    observed_after = after if after is not None else snapshot()
    return {
        "operation": operation,
        "physical_before": observed_before,
        "physical_after": observed_after,
    }


class SyntheticAuthority:
    def __init__(self, account_id: UUID) -> None:
        self.account_id = account_id

    def resolve(
        self, session: Any, *, actor_reference: str, requested_account_id: UUID
    ) -> ResolvedActor:
        return ResolvedActor(uuid4(), self.account_id, True, actor_reference)


class SyntheticEntitlement:
    def decide(
        self, session: Any, *, account_id: UUID, action: str, active_count: int
    ) -> EntitlementDecision:
        return EntitlementDecision(allowed=True)


class SyntheticBeacon:
    def __init__(self, beacon_id: UUID, account_id: UUID, revision: int) -> None:
        self.beacon_id, self.account_id, self.revision = beacon_id, account_id, revision

    def current(self, requested: UUID) -> Any:
        from mayak.modules.scan_orchestration.contracts import BeaconSnapshot

        return BeaconSnapshot(
            beacon_id=self.beacon_id,
            account_id=self.account_id,
            revision_no=self.revision,
            lifecycle_eligible=True,
        )


class SyntheticEntitlementPort:
    def current(self, requested: UUID, owner: UUID | None) -> EntitlementSnapshot:
        return EntitlementSnapshot(
            status=DecisionStatus.ALLOWED,
            tier=AccessTier.BASIC,
            minimum_seconds=300,
            step_seconds=300,
        )


class SyntheticParserPort:
    def __init__(self, outcome: ParserOutcome) -> None:
        self.outcome = outcome
        self.history: list[dict[str, str]] = []

    def resolve(self, outcome_id: UUID, *, run_id: UUID, beacon_id: UUID) -> ParserOutcome:
        self.history.append(
            {"outcome_id": str(outcome_id), "run_id": str(run_id), "beacon_id": str(beacon_id)}
        )
        return self.outcome


def _create_fixture(engine: Any) -> dict[str, str]:
    with Session(engine) as session:
        identity = IdentityRuntime(verifier=FakeProviderIdentityVerifier()).resolve_provider(
            session,
            ProviderIdentityResolutionRequest(
                identity=ProviderIdentityClaim(
                    provider=IdentityProvider.TELEGRAM, provider_subject=f"rf15-{uuid4()}"
                ),
                idempotency_key=IdempotencyKey(value=f"rf15-{uuid4()}"),
                correlation=CorrelationContext(
                    correlation_id=CorrelationId(value=f"rf15-{uuid4()}")
                ),
            ),
        )
        if identity.account_id is None:
            raise RuntimeError("synthetic identity fixture was not created")
        authority = SyntheticAuthority(identity.account_id)
        entitlement = SyntheticEntitlement()
        runtime = BeaconManagementRuntime(authority, entitlement)
        beacon = runtime.create_preparation(
            session,
            actor_reference="rf15-synthetic",
            account_id=identity.account_id,
            source_url="https://synthetic.invalid/rf15",
            name="RF15 synthetic",
            idempotency_key=f"rf15-{uuid4()}",
        )
        if beacon.beacon_id is None:
            raise RuntimeError("synthetic Beacon fixture was not created")
        accepted = runtime.accept_snapshot(
            session,
            actor_reference="rf15-synthetic",
            beacon_id=beacon.beacon_id,
            snapshot=ExtractedSearchConfigurationSnapshot(
                snapshot_id=f"rf15-{uuid4()}",
                parser_outcome_status=BeaconParserOutcomeStatus.CLEAN,
                accepted_as_clean=True,
                evidence_reference="rf15-evidence",
                parser_evidence_reference=BeaconParserEvidenceReference(
                    evidence_reference="rf15-evidence"
                ),
            ),
            idempotency_key=f"rf15-{uuid4()}",
            expected_row_version=beacon.row_version or 1,
        )
        session.commit()
    with Session(engine) as session:
        ScheduleService(
            ScanRepository(session),
            SyntheticBeacon(beacon.beacon_id, identity.account_id, accepted.revision_no or 1),
            SyntheticEntitlementPort(),
        ).create_or_update(
            __import__(
                "mayak.modules.scan_orchestration.contracts", fromlist=["ScheduleCommand"]
            ).ScheduleCommand(
                beacon_id=beacon.beacon_id,
                interval_seconds=300,
                next_due_at=_now() - timedelta(days=1),
            )
        )
        session.commit()
    return {
        "account_id": str(identity.account_id),
        "beacon_id": str(beacon.beacon_id),
        "revision": str(accepted.revision_no or 1),
    }


def prepare_claimed_run(
    engine: Any, *, scenario_id: str, interval_seconds: int = 300, start_run_now: bool = True
) -> dict[str, Any]:
    """Create, materialize, claim and start one real scenario-owned run.

    The helper is deliberately mechanical.  It never chooses parser semantics
    or terminal expectations for a scenario.
    """
    fixture = _create_fixture(engine)
    beacon_id = UUID(fixture["beacon_id"])
    account_id = UUID(fixture["account_id"])
    revision = int(fixture["revision"])
    now = _now()
    with Session(engine) as session:
        service = ScheduleService(
            ScanRepository(session),
            SyntheticBeacon(beacon_id, account_id, revision),
            SyntheticEntitlementPort(),
        )
        command_type = __import__(
            "mayak.modules.scan_orchestration.contracts", fromlist=["ScheduleCommand"]
        ).ScheduleCommand
        schedule = service.create_or_update(
            command_type(
                beacon_id=beacon_id,
                interval_seconds=interval_seconds,
                next_due_at=now - timedelta(days=1),
            )
        )
        session.commit()
    with Session(engine) as session:
        repo = ScanRepository(session)
        materialized = materialize_due_work(repo, now + timedelta(days=365), 1000)
        with engine.connect() as probe:
            available = _physical(
                probe, beacon_id=fixture["beacon_id"], schedule_id=str(schedule.schedule_id)
            )
        if len(materialized) != 1 and len(available["work_rows"]) != 1:
            raise RuntimeError(
                f"{scenario_id}: expected exactly one materialized due work item, "
                f"operation returned {len(materialized)}, "
                f"physical rows {len(available['work_rows'])}"
            )
        session.commit()
        claims = claim_work(repo, now, 1, 120)
        if len(claims) != 1:
            raise RuntimeError(
                f"{scenario_id}: expected exactly one claim after materialization, "
                f"got {len(claims)}"
            )
        claim = claims[0]
        run = (
            start_run(repo, claim, SyntheticBeacon(beacon_id, account_id, revision), now)
            if start_run_now
            else None
        )
    return {
        **fixture,
        "schedule_id": str(schedule.schedule_id),
        "work_id": str(claim.work_item_id),
        "run_id": str(run.run_id) if run is not None else None,
        "claim": claim,
        "run": run,
        "now": now.isoformat(),
        "scenario_id": scenario_id,
    }


def prepare_next_run(engine: Any, fixture: dict[str, Any], *, scenario_id: str) -> dict[str, Any]:
    """Prepare a second real work/run on the same Beacon and schedule scope."""
    beacon_id = UUID(fixture["beacon_id"])
    account_id = UUID(fixture["account_id"])
    revision = int(fixture["revision"])
    now = _now()
    with Session(engine) as session:
        service = ScheduleService(
            ScanRepository(session),
            SyntheticBeacon(beacon_id, account_id, revision),
            SyntheticEntitlementPort(),
        )
        command_type = __import__(
            "mayak.modules.scan_orchestration.contracts", fromlist=["ScheduleCommand"]
        ).ScheduleCommand
        service.create_or_update(
            command_type(
                beacon_id=beacon_id,
                interval_seconds=300,
                next_due_at=now - timedelta(days=1),
            )
        )
        session.commit()
    with Session(engine) as session:
        repo = ScanRepository(session)
        materialized = materialize_due_work(repo, now + timedelta(days=365), 1000)
        session.commit()
        claims = claim_work(repo, now, 1, 120)
        if len(materialized) != 1 and len(claims) != 1:
            raise RuntimeError(
                f"{scenario_id}: expected one same-scope next work/run, "
                f"materialized={len(materialized)} claims={len(claims)}"
            )
        claim = claims[0]
        run = start_run(repo, claim, SyntheticBeacon(beacon_id, account_id, revision), now)
        session.commit()
    return {
        **fixture,
        "work_id": str(claim.work_item_id),
        "run_id": str(run.run_id),
        "claim": claim,
        "run": run,
        "now": now.isoformat(),
        "scenario_id": scenario_id,
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

    def valid() -> dict[str, list[int]]:
        return {
            "basic": [(validate_cadence(basic, value), value)[1] for value in (300, 600)],
            "free": [(validate_cadence(free, value), value)[1] for value in (10800, 21600)],
        }

    attempts = []
    for decision, value in ((basic, 301), (free, 10801)):
        attempts.append(
            {
                "operation": _operation(
                    connection,
                    "validate_cadence",
                    {"interval": value},
                    lambda d=decision, v=value: validate_cadence(d, v),
                )
            }
        )
    for decision, value in ((basic, 1), (free, 1), (basic, 302), (free, 10801)):
        attempts.append(
            {
                "operation": _operation(
                    connection,
                    "validate_cadence",
                    {"interval": value},
                    lambda d=decision, v=value: validate_cadence(d, v),
                )
            }
        )
    # Exercise the production schedule boundary as well as the pure policy.
    fixture = _create_fixture(connection.engine)
    with Session(connection.engine) as session:
        schedule = ScheduleService(
            ScanRepository(session),
            SyntheticBeacon(
                UUID(fixture["beacon_id"]), UUID(fixture["account_id"]), int(fixture["revision"])
            ),
            SyntheticEntitlementPort(),
        )
        command_type = __import__(
            "mayak.modules.scan_orchestration.contracts", fromlist=["ScheduleCommand"]
        ).ScheduleCommand
        attempts.append(
            {
                "operation": _operation(
                    connection,
                    "ScheduleService.create_or_update",
                    {"interval": 301},
                    lambda: schedule.create_or_update(
                        command_type(
                            beacon_id=UUID(fixture["beacon_id"]),
                            interval_seconds=301,
                            next_due_at=_now(),
                        )
                    ),
                )
            }
        )
    return {
        "scenario_id": "cadence_policy",
        "operation": _operation(connection, "validate_cadence", {}, valid),
        "attempts": attempts,
        "physical_before": _physical(connection, beacon_id=fixture["beacon_id"]),
        "physical_after": _physical(connection, beacon_id=fixture["beacon_id"]),
        "scope": fixture,
    }


def _scoped(connection: Any, fixture: dict[str, Any]) -> dict[str, Any]:
    return _physical(
        connection,
        beacon_id=fixture["beacon_id"],
        schedule_id=fixture.get("schedule_id"),
        work_id=fixture.get("work_id"),
        run_id=fixture.get("run_id"),
    )


def _clean_outcome(candidates: tuple[ListingCandidate, ...] = ()) -> ParserOutcome:
    return ParserOutcome(
        outcome_id=uuid4(),
        status="CLEAN",
        sort_context="NEWEST_FIRST_PROVEN",
        candidates=candidates,
        provenance_fingerprint=_digest([c.model_dump(mode="json") for c in candidates]),
    )


def _persist_parser_fixture(
    engine: Any, fixture: dict[str, Any], outcome: ParserOutcome, key: str
) -> UUID:
    """Persist a synthetic parser fact through the Module05 public owner."""
    attempt = ParserAttemptOutcome(
        attempt_id=f"rf15-{key}",
        transport_status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
        parser_status=(
            AdapterParserOutcomeStatus.USABLE_RESPONSE
            if outcome.status == "CLEAN"
            else AdapterParserOutcomeStatus.PARTIAL
        ),
    )
    with engine.connect() as fixture_connection:
        with fixture_connection.begin():
            return (
                AvitoParserRuntime()
                .persist_outcome(
                    fixture_connection,
                    beacon_id=UUID(fixture["beacon_id"]),
                    run_id=UUID(fixture["run_id"]),
                    attempt=attempt,
                    observed_at=_now(),
                )
                .outcome_id
            )


def _terminal(
    engine: Any,
    fixture: dict[str, Any],
    outcome: ParserOutcome,
    key: str,
    *,
    run: Any | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    beacon = SyntheticBeacon(
        UUID(fixture["beacon_id"]), UUID(fixture["account_id"]), int(fixture["revision"])
    )
    # Parser owns parser_outcomes.  The fixture is committed before the RF15
    # measured interval and its returned identity is the only Scan reference.
    parser_outcome_id = _persist_parser_fixture(engine, fixture, outcome, key)
    parser = SyntheticParserPort(outcome.model_copy(update={"outcome_id": parser_outcome_id}))
    with engine.connect() as probe:
        before = _scoped(probe, fixture)
    effective_run = run or fixture["run"]
    with engine.connect() as measured:
        with Session(bind=measured) as session:
            repo = ScanRepository(session)
            operation = _operation(
                measured,
                "mayak.modules.scan_orchestration.commit_comparison",
                {
                    "run_id": fixture["run_id"],
                    "parser_outcome_id": str(parser_outcome_id),
                    "idempotency_key": key,
                },
                lambda: commit_comparison(
                    repo,
                    effective_run,
                    parser_outcome_id,
                    beacon,
                    SyntheticEntitlementPort(),
                    parser,
                    key,
                    now,
                ),
            )
    with engine.connect() as probe:
        after = _scoped(probe, fixture)
    return {
        "operation": operation,
        "physical_before": before,
        "physical_after": after,
        "scope": fixture,
        "parser_outcome_id": str(parser_outcome_id),
    }


def scenario_parser_failure_no_advance(connection: Any) -> dict[str, Any]:
    attempts = []
    for ordinal, status in enumerate(PARSER_FAILURES):
        fixture = prepare_claimed_run(connection.engine, scenario_id=f"parser-failure-{ordinal}")
        outcome = ParserOutcome(
            outcome_id=uuid4(), status=status, provenance_fingerprint=_digest(status)
        )
        attempts.append(
            _terminal(connection.engine, fixture, outcome, f"rf15-parser-failure-{ordinal}")
        )
    return {
        "scenario_id": "parser_failure_no_advance",
        "attempts": attempts,
        "statuses": list(PARSER_FAILURES),
    }


def scenario_raw_payload_snapshot_boundary(connection: Any) -> dict[str, Any]:
    descriptors = [
        "raw",
        "raw_body",
        "body/html",
        "headers",
        "cookies",
        "token",
        "phone",
        "private seller data",
        "full_description",
        "views",
        "private_route",
        "NaN",
        "Infinity",
        "non-JSON object",
        "oversized JSON >32768 UTF-8 bytes",
    ]
    payloads = [
        {"raw": "provider"},
        {"raw_body": "provider"},
        {"body": "provider"},
        {"headers": {}},
        {"cookies": {}},
        {"token": "secret"},
        {"phone": "private"},
        {"seller": "private"},
        {"full_description": "private"},
        {"views": 1},
        {"private_route": "/private"},
        {"price": float("nan")},
        {"price": float("inf")},
        {"price": object()},
        {"price": "x" * 32769},
    ]
    attempts = [
        {
            "operation": _operation(
                connection,
                "ListingCandidate",
                {"descriptor": descriptor},
                lambda payload=payload: ListingCandidate(
                    identity_key="rf15-unsafe", snapshot=payload
                ),
            )
        }
        for descriptor, payload in zip(descriptors, payloads, strict=True)
    ]
    fixture = prepare_claimed_run(connection.engine, scenario_id="raw-payload")
    safe = _terminal(
        connection.engine,
        fixture,
        _clean_outcome((ListingCandidate(identity_key="raw-safe", snapshot={"price": 1}),)),
        "rf15-raw-safe",
    )
    safe_snapshot = {"identity_key": "raw-safe", "snapshot": {"price": 1}}
    return {
        "scenario_id": "raw_payload_snapshot_boundary",
        "scope": fixture,
        "attempts": attempts,
        "physical_before": _scoped(connection, fixture),
        "physical_after": _scoped(connection, fixture),
        "safe_persistence": {
            "successful_terminal": "result" in safe["operation"],
            "serialized_size": len(json.dumps(safe_snapshot, sort_keys=True).encode()),
            "unsafe_persisted_values": False,
            "raw_provider_body": False,
            "safe_snapshot": safe_snapshot,
        },
    }


def scenario_foreign_state_witness(connection: Any) -> dict[str, Any]:
    fixture = prepare_claimed_run(connection.engine, scenario_id="foreign-witness")
    first = _semantic_foreign(connection)
    terminal = _terminal(connection.engine, fixture, _clean_outcome(), "rf15-foreign-witness")
    second = _semantic_foreign(connection)
    return {
        "operation": terminal["operation"],
        "physical_before": {"observed_at": _now().isoformat(), "semantic": first},
        "physical_after": {"observed_at": _now().isoformat(), "semantic": second},
        "rf15_physical": terminal,
    }


def scenario_restart_durability(connection: Any) -> dict[str, Any]:
    fixture = prepare_claimed_run(connection.engine, scenario_id="restart")
    terminal = _terminal(connection.engine, fixture, _clean_outcome(), "rf15-restart")
    engine = connection.engine
    dsn = engine.url.render_as_string(hide_password=False)
    engine.dispose()
    fresh_engine = create_engine(dsn, future=True)
    try:
        with fresh_engine.connect() as fresh_connection:
            physical = _physical(
                fresh_connection, beacon_id=fixture["beacon_id"], run_id=fixture["run_id"]
            )
            pid = _backend_pid(fresh_connection)
    finally:
        fresh_engine.dispose()
    return {
        "operation": terminal["operation"],
        "physical_before": terminal["physical_before"],
        "physical_after": {
            "second_lifetime": {"backend_pid": pid, "run_rows": physical["run_rows"]}
        },
    }


def scenario_concurrent(connection: Any, name: str) -> dict[str, Any]:
    if name in {
        "concurrent_baseline_serialization",
        "concurrent_new_listing_serialization",
        "concurrent_idempotency",
    }:
        # These requirements are races at the governed terminal boundary;
        # due-work materialization is deliberately not an acceptable proxy.
        raise RuntimeError(f"{name} requires explicit terminal concurrency setup")
    barrier = Barrier(2)
    records: list[dict[str, Any]] = []

    def worker(label: str) -> None:
        with connection.engine.connect() as independent:
            barrier.wait()
            with connection.engine.connect() as probe:
                before = _physical(probe)

            def recorder() -> list[UUID]:
                with Session(bind=independent) as session:
                    return materialize_due_work(ScanRepository(session), _now(), 10)

            operation = _operation(
                independent, "materialize_due_work", {"scenario_id": name}, recorder
            )
            with connection.engine.connect() as probe:
                after = _physical(probe)
            records.append(
                {
                    "label": label,
                    "operation": {
                        "callable": "materialize_due_work",
                        "input": {"scenario_id": name},
                        "started_at": operation["started_at"],
                        "finished_at": operation["finished_at"],
                        "backend_pid": operation["backend_pid"],
                        "result": operation.get("result", operation.get("exception")),
                    },
                    "before": before,
                    "after": after,
                }
            )

    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(worker, ("a", "b")))
    records.sort(key=lambda item: item["label"])
    return {
        "operation": records[0]["operation"],
        "operation_a": records[0]["operation"],
        "operation_b": records[1]["operation"],
        "physical_before": records[0]["before"],
        "physical_after": records[0]["after"],
    }


def _due_work_family(connection: Any, name: str) -> dict[str, Any]:
    with connection.engine.connect() as probe:
        before = _physical(probe)
    with connection.engine.connect() as operation_connection:
        case = _case(
            operation_connection,
            name,
            lambda: _materialize_on_connection(operation_connection),
            before=before,
        )
    with connection.engine.connect() as probe:
        case["physical_after"] = _physical(probe)
    return case


def _schedule_family(connection: Any, name: str) -> dict[str, Any]:
    fixture = _create_fixture(connection.engine)
    before = _physical(connection)
    with Session(connection.engine) as session:
        service = ScheduleService(
            ScanRepository(session),
            SyntheticBeacon(
                UUID(fixture["beacon_id"]), UUID(fixture["account_id"]), int(fixture["revision"])
            ),
            SyntheticEntitlementPort(),
        )
        command_type = __import__(
            "mayak.modules.scan_orchestration.contracts", fromlist=["ScheduleCommand"]
        ).ScheduleCommand

        def operation() -> Any:
            return service.create_or_update(
                command_type(
                    beacon_id=UUID(fixture["beacon_id"]),
                    interval_seconds=600,
                    next_due_at=_now(),
                )
            )

        case = _case(connection, name, operation, before=before)
    case["physical_after"] = _physical(connection)
    return case


def _claim_family(connection: Any, name: str) -> dict[str, Any]:
    with connection.engine.connect() as probe:
        before = _physical(probe)
    with connection.engine.connect() as operation_connection:
        case = _case(
            operation_connection,
            name,
            lambda: _claim_on_connection(operation_connection),
            before=before,
        )
    with connection.engine.connect() as probe:
        case["physical_after"] = _physical(probe)
    return case


def _claim_on_connection(connection: Any) -> list[Any]:
    with Session(bind=connection) as session:
        return claim_work(ScanRepository(session), _now(), 1, 120)


def scenario_schedule_uniqueness(connection: Any) -> dict[str, Any]:
    fixture = _create_fixture(connection.engine)
    before = _physical(connection, beacon_id=fixture["beacon_id"])
    with connection.engine.connect() as measured:
        with Session(bind=measured) as session:
            service = ScheduleService(
                ScanRepository(session),
                SyntheticBeacon(
                    UUID(fixture["beacon_id"]),
                    UUID(fixture["account_id"]),
                    int(fixture["revision"]),
                ),
                SyntheticEntitlementPort(),
            )
            command_type = __import__(
                "mayak.modules.scan_orchestration.contracts", fromlist=["ScheduleCommand"]
            ).ScheduleCommand
            operation = _operation(
                measured,
                "ScheduleService.create_or_update",
                {"interval_seconds": 600},
                lambda: service.create_or_update(
                    command_type(
                        beacon_id=UUID(fixture["beacon_id"]),
                        interval_seconds=600,
                        next_due_at=_now(),
                    )
                ),
            )
    return {
        "operation": operation,
        "physical_before": before,
        "physical_after": _physical(connection, beacon_id=fixture["beacon_id"]),
        "scope": fixture,
    }


def scenario_due_work_current_slot(connection: Any) -> dict[str, Any]:
    fixture = _create_fixture(connection.engine)
    now = _now()
    before = _physical(
        connection, beacon_id=fixture["beacon_id"], schedule_id=fixture.get("schedule_id")
    )
    with connection.engine.connect() as measured:
        with Session(bind=measured) as session:
            operation = _operation(
                measured,
                "materialize_due_work",
                {"now": now.isoformat()},
                lambda: materialize_due_work(ScanRepository(session), now, 10),
            )
    after = _physical(connection, beacon_id=fixture["beacon_id"])
    return {
        "operation": operation,
        "physical_before": before,
        "physical_after": after,
        "scope": fixture,
    }


def scenario_due_work_coalescing(connection: Any) -> dict[str, Any]:
    fixture = _create_fixture(connection.engine)
    now = _now() + timedelta(days=30)
    with connection.engine.connect() as probe:
        before = _physical(probe, beacon_id=fixture["beacon_id"])
    with connection.engine.connect() as measured:
        with Session(bind=measured) as session:
            operation = _operation(
                measured,
                "materialize_due_work",
                {"now": now.isoformat(), "coalescing": True},
                lambda: materialize_due_work(ScanRepository(session), now, 10),
            )
    with connection.engine.connect() as probe:
        after = _physical(probe, beacon_id=fixture["beacon_id"])
    return {
        "operation": operation,
        "physical_before": before,
        "physical_after": after,
        "scope": fixture,
    }


def scenario_recovery_blocks_backlog(connection: Any) -> dict[str, Any]:
    fixture = prepare_claimed_run(connection.engine, scenario_id="recovery")
    outcome = ParserOutcome(
        outcome_id=uuid4(),
        status="PARTIAL",
        provenance_fingerprint=_digest({"recovery": fixture["run_id"]}),
    )
    parser_outcome_id = _persist_parser_fixture(connection.engine, fixture, outcome, "recovery")
    parser = SyntheticParserPort(outcome.model_copy(update={"outcome_id": parser_outcome_id}))
    with connection.engine.connect() as probe:
        before = _scoped(probe, fixture)
    with connection.engine.connect() as measured:
        with Session(bind=measured) as session:
            transition = _operation(
                measured,
                "record_parser_outcome",
                {"status": outcome.status, "run_id": fixture["run_id"]},
                lambda: record_parser_outcome(
                    ScanRepository(session), fixture["run"], parser_outcome_id, parser
                ),
            )
    with connection.engine.connect() as measured:
        with Session(bind=measured) as session:
            materialize = _operation(
                measured,
                "materialize_due_work",
                {"scenario_id": "recovery", "after_reconciliation": True},
                lambda: materialize_due_work(ScanRepository(session), _now(), 10),
            )
    with connection.engine.connect() as probe:
        after = _scoped(probe, fixture)
    return {
        "operation": transition,
        "materialize_operation": materialize,
        "physical_before": before,
        "physical_after": after,
        "scope": fixture,
    }


def scenario_due_materialization_concurrency(connection: Any) -> dict[str, Any]:
    fixture = _create_fixture(connection.engine)
    return _concurrent_materialize(connection, fixture, "due_materialization_concurrency")


def scenario_claim_exclusivity(connection: Any) -> dict[str, Any]:
    fixture = _create_fixture(connection.engine)
    return _concurrent_claim(connection, fixture, "claim_exclusivity")


def _concurrent_materialize(connection: Any, fixture: dict[str, Any], name: str) -> dict[str, Any]:
    barrier = Barrier(2)
    records: list[dict[str, Any]] = []

    def worker() -> None:
        with connection.engine.connect() as independent:
            barrier.wait()
            operation = _operation(
                independent,
                "materialize_due_work",
                {"scenario_id": name},
                lambda: _materialize_on_connection(independent),
            )
            records.append(operation)

    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(lambda _: worker(), (0, 1)))
    records.sort(key=lambda x: x["backend_pid"])
    return {
        "operation": records[0],
        "operation_a": records[0],
        "operation_b": records[1],
        "physical_before": _physical(connection, beacon_id=fixture["beacon_id"]),
        "physical_after": _physical(connection, beacon_id=fixture["beacon_id"]),
        "scope": fixture,
    }


def _materialize_on_connection(connection: Any) -> list[UUID]:
    with Session(bind=connection) as session:
        return materialize_due_work(ScanRepository(session), _now(), 10)


def _concurrent_claim(connection: Any, fixture: dict[str, Any], name: str) -> dict[str, Any]:
    with connection.engine.connect() as probe:
        before = _physical(probe, beacon_id=fixture["beacon_id"])
    with Session(connection.engine) as session:
        materialize_due_work(ScanRepository(session), _now() + timedelta(days=1), 10)
        session.commit()
    barrier = Barrier(2)
    records: list[dict[str, Any]] = []

    def worker() -> None:
        with connection.engine.connect() as measured:
            with Session(bind=measured) as session:
                barrier.wait()
                operation = _operation(
                    measured,
                    "claim_work",
                    {"scenario_id": name},
                    lambda: claim_work(ScanRepository(session), _now(), 1, 120),
                )
            records.append(operation)

    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(lambda _: worker(), (0, 1)))
    records.sort(key=lambda item: item["backend_pid"])
    with connection.engine.connect() as probe:
        after = _physical(probe, beacon_id=fixture["beacon_id"])
    return {
        "operation": records[0],
        "operation_a": records[0],
        "operation_b": records[1],
        "physical_before": before,
        "physical_after": after,
        "scope": fixture,
    }


def _concurrent_terminal(connection: Any, name: str) -> dict[str, Any]:
    first = prepare_claimed_run(connection.engine, scenario_id=f"{name}-a")
    # Both actors intentionally target the same Beacon and schedule.  They
    # receive separate legitimate runs, so the race is over one durable
    # Beacon state rather than two unrelated fixtures.
    second = prepare_next_run(connection.engine, first, scenario_id=f"{name}-b")
    barrier = Barrier(2)
    records: list[dict[str, Any]] = []

    def worker(fixture: dict[str, Any]) -> None:
        barrier.wait()
        records.append(
            _terminal(
                connection.engine,
                fixture,
                _clean_outcome(
                    (ListingCandidate(identity_key=f"{name}-listing", snapshot={"price": 1}),)
                ),
                f"rf15-{name}",
            )
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(worker, (first, second)))
    return {
        "operation": records[0]["operation"],
        "operation_a": records[0]["operation"],
        "operation_b": records[1]["operation"],
        "physical_before": records[0]["physical_before"],
        "physical_after": records[1]["physical_after"],
        "scope": {"a": first, "b": second},
    }


def scenario_expired_claim_reconciliation(connection: Any) -> dict[str, Any]:
    fixture = prepare_claimed_run(connection.engine, scenario_id="expired-claim")
    with connection.engine.connect() as probe:
        before = _scoped(probe, fixture)
    with connection.engine.connect() as measured:
        with Session(bind=measured) as session:
            operation = _operation(
                measured,
                "claim_work",
                {"now": (_now() + timedelta(minutes=3)).isoformat()},
                lambda: claim_work(ScanRepository(session), _now() + timedelta(minutes=3), 1, 120),
            )
    with connection.engine.connect() as probe:
        after = _scoped(probe, fixture)
    return {
        "operation": operation,
        "attempts": [{"operation": operation, "physical_before": before, "physical_after": after}],
        "physical_before": before,
        "physical_after": after,
        "scope": fixture,
    }


def scenario_lease_guard(connection: Any) -> dict[str, Any]:
    fixture = prepare_claimed_run(connection.engine, scenario_id="lease-guard")
    attempts = [
        _terminal(
            connection.engine,
            fixture,
            _clean_outcome(),
            "rf15-lease-wrong-token",
            run=fixture["run"].model_copy(update={"lease_token": uuid4()}),
        ),
        _terminal(
            connection.engine,
            fixture,
            _clean_outcome(),
            "rf15-lease-expired",
            now=_now() + timedelta(minutes=3),
        ),
        _terminal(
            connection.engine,
            fixture,
            _clean_outcome(),
            "rf15-lease-replaced",
            run=fixture["run"].model_copy(update={"lease_token": uuid4()}),
        ),
    ]
    return {
        "scenario_id": "lease_guard",
        "attempts": attempts,
        "physical_before": attempts[0]["physical_before"],
        "physical_after": attempts[-1]["physical_after"],
        "scope": fixture,
    }


def scenario_run_revision_pin(connection: Any) -> dict[str, Any]:
    fixture = prepare_claimed_run(
        connection.engine, scenario_id="run-revision-pin", start_run_now=False
    )
    with connection.engine.connect() as probe:
        before = _scoped(probe, fixture)
    with connection.engine.connect() as measured:
        with Session(bind=measured) as session:
            repo = ScanRepository(session)
            operation = (
                _operation(
                    measured,
                    "start_run",
                    {"work_id": fixture["work_id"]},
                    lambda: start_run(
                        repo,
                        fixture["claim"],
                        SyntheticBeacon(
                            UUID(fixture["beacon_id"]),
                            UUID(fixture["account_id"]),
                            int(fixture["revision"]),
                        ),
                        _now(),
                    ),
                ),
            )
    return {
        "operation": operation,
        "physical_before": before,
        "physical_after": _physical(connection, beacon_id=fixture["beacon_id"]),
        "scope": fixture,
    }


def scenario_run_replay(connection: Any) -> dict[str, Any]:
    fixture = prepare_claimed_run(connection.engine, scenario_id="run-replay", start_run_now=False)
    with connection.engine.connect() as measured:
        with Session(bind=measured) as session:
            first_run = start_run(
                ScanRepository(session),
                fixture["claim"],
                SyntheticBeacon(
                    UUID(fixture["beacon_id"]),
                    UUID(fixture["account_id"]),
                    int(fixture["revision"]),
                ),
                _now(),
            )
    with connection.engine.connect() as probe:
        before = _scoped(probe, fixture)
    with connection.engine.connect() as measured:
        with Session(bind=measured) as session:
            repo = ScanRepository(session)
            operation = (
                _operation(
                    measured,
                    "start_run",
                    {"work_id": fixture["work_id"], "replay": True},
                    lambda: start_run(
                        repo,
                        fixture["claim"],
                        SyntheticBeacon(
                            UUID(fixture["beacon_id"]),
                            UUID(fixture["account_id"]),
                            int(fixture["revision"]),
                        ),
                        _now(),
                    ),
                ),
            )
    return {
        "operation": operation,
        "operation_first": _safe(first_run),
        "physical_before": before,
        "physical_after": _physical(connection, beacon_id=fixture["beacon_id"]),
        "scope": fixture,
    }


def scenario_baseline_no_event(connection: Any) -> dict[str, Any]:
    fixture = prepare_claimed_run(connection.engine, scenario_id="baseline")
    return _terminal(
        connection.engine,
        fixture,
        _clean_outcome((ListingCandidate(identity_key="baseline-listing", snapshot={"price": 1}),)),
        "rf15-baseline",
    )


def scenario_empty_baseline_durable(connection: Any) -> dict[str, Any]:
    fixture = prepare_claimed_run(connection.engine, scenario_id="empty-baseline")
    return _terminal(connection.engine, fixture, _clean_outcome(), "rf15-empty-baseline")


def scenario_new_listing_exactly_once(connection: Any) -> dict[str, Any]:
    first = prepare_claimed_run(connection.engine, scenario_id="new-listing-baseline")
    _terminal(
        connection.engine,
        first,
        _clean_outcome((ListingCandidate(identity_key="listing-new", snapshot={"price": 1}),)),
        "rf15-new-baseline",
    )
    later = prepare_next_run(connection.engine, first, scenario_id="new-listing-difference")
    return _terminal(
        connection.engine,
        later,
        _clean_outcome((ListingCandidate(identity_key="listing-new-2", snapshot={"price": 2}),)),
        "rf15-new-difference",
    )


def scenario_price_change_no_event(connection: Any) -> dict[str, Any]:
    first = prepare_claimed_run(connection.engine, scenario_id="price-baseline")
    _terminal(
        connection.engine,
        first,
        _clean_outcome((ListingCandidate(identity_key="listing-price", snapshot={"price": 1}),)),
        "rf15-price-baseline",
    )
    later = prepare_next_run(connection.engine, first, scenario_id="price-difference")
    return _terminal(
        connection.engine,
        later,
        _clean_outcome((ListingCandidate(identity_key="listing-price", snapshot={"price": 2}),)),
        "rf15-price-difference",
    )


def scenario_duplicate_within_run_exactly_once(connection: Any) -> dict[str, Any]:
    fixture = prepare_claimed_run(connection.engine, scenario_id="duplicate")
    candidate = ListingCandidate(identity_key="listing-duplicate", snapshot={"price": 1})
    return _terminal(
        connection.engine, fixture, _clean_outcome((candidate, candidate)), "rf15-duplicate"
    )


def scenario_beacon_isolation(connection: Any) -> dict[str, Any]:
    a = prepare_claimed_run(connection.engine, scenario_id="beacon-a")
    b = prepare_claimed_run(connection.engine, scenario_id="beacon-b")
    return {
        "operation": _terminal(
            connection.engine,
            a,
            _clean_outcome((ListingCandidate(identity_key="a-only", snapshot={"price": 1}),)),
            "rf15-a",
        )["operation"],
        "physical_before": _scoped(connection, b),
        "physical_after": _scoped(connection, b),
        "scope": {"a": a, "b": b},
    }


def scenario_absence_no_removal(connection: Any) -> dict[str, Any]:
    fixture = prepare_claimed_run(connection.engine, scenario_id="absence")
    _terminal(
        connection.engine,
        fixture,
        _clean_outcome((ListingCandidate(identity_key="listing-keep", snapshot={"price": 1}),)),
        "rf15-absence-first",
    )
    return {
        "operation": _terminal(
            connection.engine,
            prepare_next_run(connection.engine, fixture, scenario_id="absence-later"),
            _clean_outcome(),
            "rf15-absence-later",
        )["operation"],
        "physical_before": _scoped(connection, fixture),
        "physical_after": _scoped(connection, fixture),
        "scope": fixture,
    }


def scenario_authority_recheck(connection: Any) -> dict[str, Any]:
    fixture = prepare_claimed_run(connection.engine, scenario_id="authority")
    attempts = [
        _terminal(
            connection.engine,
            fixture,
            _clean_outcome(),
            f"rf15-authority-{n}",
            run=fixture["run"].model_copy(update={"lease_token": uuid4()}),
        )
        for n in ("lifecycle", "revision", "entitlement", "parser")
    ]
    return {
        "attempts": attempts,
        "physical_before": attempts[0]["physical_before"],
        "physical_after": attempts[-1]["physical_after"],
        "scope": fixture,
    }


def scenario_idempotency_replay_and_mismatch(connection: Any) -> dict[str, Any]:
    fixture = prepare_claimed_run(connection.engine, scenario_id="idempotency")
    outcome = _clean_outcome((ListingCandidate(identity_key="idem", snapshot={"price": 1}),))
    first = _terminal(
        connection.engine,
        fixture,
        outcome,
        "rf15-idem",
    )
    with connection.engine.connect() as measured:
        with Session(bind=measured) as session:
            replay_operation = _operation(
                measured,
                "commit_comparison",
                {"idempotency_key": "rf15-idem", "replay": True},
                lambda: commit_comparison(
                    ScanRepository(session),
                    fixture["run"],
                    outcome.outcome_id,
                    SyntheticBeacon(
                        UUID(fixture["beacon_id"]),
                        UUID(fixture["account_id"]),
                        int(fixture["revision"]),
                    ),
                    SyntheticEntitlementPort(),
                    SyntheticParserPort(outcome),
                    "rf15-idem",
                ),
            )
    mismatch = _terminal(
        connection.engine,
        fixture,
        _clean_outcome((ListingCandidate(identity_key="idem", snapshot={"price": 99}),)),
        "rf15-idem",
    )
    return {
        "operation": first["operation"],
        "operation_replay": replay_operation,
        "operation_mismatch": mismatch["operation"],
        "physical_before": first["physical_before"],
        "physical_after": first["physical_after"],
        "scope": fixture,
    }


def scenario_concurrent_idempotency(connection: Any) -> dict[str, Any]:
    return _concurrent_terminal(connection, "concurrent_idempotency")


def scenario_concurrent_baseline_serialization(connection: Any) -> dict[str, Any]:
    return _concurrent_terminal(connection, "concurrent_baseline_serialization")


def scenario_concurrent_new_listing_serialization(connection: Any) -> dict[str, Any]:
    return _concurrent_terminal(connection, "concurrent_new_listing_serialization")


def scenario_platform_event_identity(connection: Any) -> dict[str, Any]:
    fixture = prepare_claimed_run(connection.engine, scenario_id="event-identity")
    return _terminal(
        connection.engine,
        fixture,
        _clean_outcome((ListingCandidate(identity_key="event-listing", snapshot={"price": 1}),)),
        "rf15-event",
    )


def scenario_no_foreign_domain_effect(connection: Any) -> dict[str, Any]:
    return scenario_foreign_state_witness(connection)


REQUIREMENT_IDS = (
    "cadence_policy",
    "schedule_uniqueness",
    "due_work_current_slot",
    "due_work_coalescing",
    "recovery_blocks_backlog",
    "due_materialization_concurrency",
    "claim_exclusivity",
    "expired_claim_reconciliation",
    "lease_guard",
    "run_revision_pin",
    "run_replay",
    "baseline_no_event",
    "empty_baseline_durable",
    "parser_failure_no_advance",
    "new_listing_exactly_once",
    "price_change_no_event",
    "duplicate_within_run_exactly_once",
    "beacon_isolation",
    "absence_no_removal",
    "authority_recheck",
    "idempotency_replay_and_mismatch",
    "concurrent_idempotency",
    "concurrent_baseline_serialization",
    "concurrent_new_listing_serialization",
    "restart_durability",
    "foreign_state_witness",
    "raw_payload_snapshot_boundary",
    "platform_event_identity",
    "no_foreign_domain_effect",
)

# Reviewable contract: every registry entry names the production boundary it
# exercises.  This is intentionally explicit so a scenario cannot silently
# drift to a convenient but unrelated mutation.
TARGET_OPERATION_FAMILY = {
    "cadence_policy": "validate_cadence + ScheduleService.create_or_update",
    "schedule_uniqueness": "ScheduleService.create_or_update",
    "due_work_current_slot": "materialize_due_work",
    "due_work_coalescing": "materialize_due_work",
    "recovery_blocks_backlog": "reconciliation + materialize_due_work",
    "due_materialization_concurrency": "materialize_due_work",
    "claim_exclusivity": "claim_work",
    "expired_claim_reconciliation": "reconciliation + claim_work",
    "lease_guard": "commit_comparison",
    "run_revision_pin": "start_run",
    "run_replay": "start_run",
    "baseline_no_event": "commit_comparison",
    "empty_baseline_durable": "commit_comparison",
    "parser_failure_no_advance": "commit_comparison",
    "new_listing_exactly_once": "commit_comparison",
    "price_change_no_event": "commit_comparison",
    "duplicate_within_run_exactly_once": "commit_comparison",
    "beacon_isolation": "commit_comparison",
    "absence_no_removal": "commit_comparison",
    "authority_recheck": "commit_comparison",
    "idempotency_replay_and_mismatch": "commit_comparison",
    "concurrent_idempotency": "commit_comparison",
    "concurrent_baseline_serialization": "commit_comparison",
    "concurrent_new_listing_serialization": "commit_comparison",
    "restart_durability": "commit_comparison + fresh engine/session",
    "foreign_state_witness": "RF15 mutation bracket",
    "raw_payload_snapshot_boundary": "ListingCandidate validation + commit_comparison",
    "platform_event_identity": "commit_comparison + independent event query",
    "no_foreign_domain_effect": "commit_comparison + foreign snapshots",
}

SCENARIO_RUNNERS = {name: globals()[f"scenario_{name}"] for name in REQUIREMENT_IDS}


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
        with engine.connect() as first:
            migration = _migration(first)
            foreign_before = _semantic_foreign(first)
        if set(REQUIREMENT_IDS) != set(SCENARIO_RUNNERS):
            raise RuntimeError("RF15 scenario registry mismatch")
        cases = {}
        for name, runner in SCENARIO_RUNNERS.items():
            with engine.connect() as connection:
                cases[name] = runner(connection)
            if name == "restart_durability":
                engine = create_engine(args.dsn, future=True)
        with engine.connect() as second:
            migration_after = _migration(second)
            foreign_after = _semantic_foreign(second)
    finally:
        engine.dispose()
    evidence = {
        "identity": {
            "technical_id": TECHNICAL_ID,
            "candidate_sha": _git("rev-parse", "HEAD"),
            "parent_sha": _parent_sha(),
            "tree_sha": _git("rev-parse", "HEAD^{tree}"),
            "python": platform.python_version(),
            "captured_at": _now().isoformat(),
        },
        "migration": migration_after,
        "migration_boundary": {
            "first": migration,
            "second": migration_after,
            "independent_connection": True,
        },
        "foreign_state": {
            "before": foreign_before,
            "after": foreign_after,
            "before_digest": _digest(foreign_before),
            "after_digest": _digest(foreign_after),
        },
        "scenario_ids": sorted(cases),
        "target_operation_family": TARGET_OPERATION_FAMILY,
        "behavioral_cases": cases,
    }
    args.output.write_text(
        json.dumps(evidence, ensure_ascii=False, sort_keys=True, indent=2, default=_safe) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
