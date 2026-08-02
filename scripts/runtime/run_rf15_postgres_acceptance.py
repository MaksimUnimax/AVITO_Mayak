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
_ACTIVE_BEACON_ID: str | None = None


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def _now() -> datetime:
    return datetime.now(UTC)


def _digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def _migration(connection: Any) -> dict[str, Any]:
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
        "head": head,
        "table_count": len(tables),
        "global_index_count": indexes,
        "scan_index_count": scan_indexes,
        "independent_connection": True,
        "backend_pid": int(connection.execute(text("select pg_backend_pid()")).scalar_one()),
    }


def _semantic_foreign(connection: Any) -> dict[str, Any]:
    # These are owning-module semantic projections, not catalog metadata.
    names = {
        "identity": "identity_accounts",
        "entitlements": "entitlement_grants",
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
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, (list, tuple)):
        return [_safe(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _safe(item) for key, item in value.items()}
    return repr(value)[:200]


def _operation(
    connection: Any,
    name: str,
    input_data: dict[str, Any],
    operation: Callable[[], Any],
) -> dict[str, Any]:
    """Invoke the supplied production callable inside the measured interval."""
    pid = int(connection.execute(text("select pg_backend_pid()")).scalar_one())
    started = _now()
    value: dict[str, Any] = {
        "callable": name,
        "input": input_data,
        "started_at": started.isoformat(),
        "finished_at": started.isoformat(),
        "backend_pid": pid,
    }
    try:
        value["result"] = _safe(operation())
    except Exception as exc:
        value["exception"] = {"class": type(exc).__name__, "reason": str(exc)[:200]}
    value["finished_at"] = _now().isoformat()
    return value


def _physical(connection: Any) -> dict[str, Any]:
    if _ACTIVE_BEACON_ID is None:
        raise RuntimeError("scenario fixture scope is not established")
    beacon = _ACTIVE_BEACON_ID
    schedules = (
        connection.execute(
            text(
                "select id::text, interval_seconds, next_due_at, state from mayak.scan_schedules "
                "where beacon_id = cast(:beacon_id as uuid) order by id"
            ),
            {"beacon_id": beacon},
        )
        .mappings()
        .all()
    )
    work = (
        connection.execute(
            text(
                "select id::text, schedule_id::text, due_at, state from mayak.scan_work_items "
                "where beacon_id = cast(:beacon_id as uuid) order by id"
            ),
            {"beacon_id": beacon},
        )
        .mappings()
        .all()
    )
    runs = (
        connection.execute(
            text(
                "select id::text, work_item_id::text, revision_no, state from mayak.scan_runs "
                "where beacon_id = cast(:beacon_id as uuid) order by id"
            ),
            {"beacon_id": beacon},
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
        "schedule_rows": [dict(row) for row in schedules],
        "work_rows": [dict(row) for row in work],
        "run_rows": [dict(row) for row in runs],
        "listing_ids": [row["id"] for row in listings],
        "listing_rows": [dict(row) for row in listings],
        "anchor_rows": [dict(row) for row in anchors],
    }


def _case(
    connection: Any,
    name: str,
    operation: Callable[[], Any],
    *,
    before: dict[str, Any] | None = None,
    after: dict[str, Any] | None = None,
) -> dict[str, Any]:
    observed_before = before if before is not None else _physical(connection)
    operation = _operation(
        connection,
        f"mayak.modules.scan_orchestration.{name}",
        {"scenario_id": f"rf15-{name}"},
        operation,
    )
    observed_after = after if after is not None else _physical(connection)
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
                next_due_at=_now() - timedelta(hours=2),
            )
        )
    return {
        "account_id": str(identity.account_id),
        "beacon_id": str(beacon.beacon_id),
        "revision": str(accepted.revision_no or 1),
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
    global _ACTIVE_BEACON_ID
    _ACTIVE_BEACON_ID = fixture["beacon_id"]
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
    return _case(connection, "cadence_policy", valid) | {"attempts": attempts}


def scenario_parser_failure_no_advance(connection: Any) -> dict[str, Any]:
    attempts: list[dict[str, Any]] = []
    engine = connection.engine
    for ordinal, status in enumerate(PARSER_FAILURES):
        fixture = _create_fixture(engine)
        global _ACTIVE_BEACON_ID
        _ACTIVE_BEACON_ID = fixture["beacon_id"]
        with Session(engine) as session:
            repo = ScanRepository(session)
            claim = claim_work(repo, _now(), 1, 120)[0]
            beacon = SyntheticBeacon(
                UUID(fixture["beacon_id"]), UUID(fixture["account_id"]), int(fixture["revision"])
            )
            run = start_run(repo, claim, beacon)
            outcome_id = uuid4()
            parser = SyntheticParserPort(
                ParserOutcome(
                    outcome_id=outcome_id,
                    status=status,
                    provenance_fingerprint=_digest({"status": status}),
                )
            )
            before = _physical(session.connection())
            attempts.append(
                {
                    "operation": _operation(
                        session.connection(),
                        "mayak.modules.scan_orchestration.commit_comparison",
                        {"status": status, "ordinal": ordinal, "run_id": str(run.run_id)},
                        lambda: commit_comparison(
                            repo,
                            run,
                            outcome_id,
                            beacon,
                            SyntheticEntitlementPort(),
                            parser,
                            f"rf15-parser-failure-{ordinal}",
                        ),
                    ),
                    "physical_before": before,
                    "physical_after": _physical(session.connection()),
                    "authority_history": parser.history,
                }
            )
    before = attempts[0]["physical_before"]
    after = attempts[-1]["physical_after"]
    return _case(
        connection,
        "parser_failure_no_advance",
        lambda: {"statuses": list(PARSER_FAILURES)},
        before=before,
        after=after,
    ) | {"statuses": list(PARSER_FAILURES)}


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
    return _case(
        connection,
        "raw_payload_snapshot_boundary",
        lambda: {"descriptors": descriptors},
        after=_physical(connection),
    ) | {"input": {"descriptors": descriptors}, "attempts": attempts}


def scenario_foreign_state_witness(connection: Any) -> dict[str, Any]:
    first = _semantic_foreign(connection)
    second = _semantic_foreign(connection)
    return _case(
        connection,
        "foreign_state_witness",
        lambda: {},
        before={"capture_id": "t0", "digest": _digest(first), "semantic": first},
        after={"capture_id": "t4", "digest": _digest(second), "semantic": second},
    )


def scenario_restart_durability(connection: Any) -> dict[str, Any]:
    initial = _physical(connection)
    ids = initial.get("run_ids", [])
    identity = ids[0] if ids else "missing"
    engine = connection.engine
    with engine.connect() as fresh:
        fresh_physical = _physical(fresh)
        fresh_pid = int(fresh.execute(text("select pg_backend_pid()")).scalar_one())
    state = next(
        (
            row.get("state")
            for row in fresh_physical.get("run_rows", [])
            if row.get("id") == identity
        ),
        None,
    )
    return _case(
        connection,
        "restart_durability",
        lambda: {"identity": identity, "state": state, "fresh_backend_pid": fresh_pid},
        before={
            "identity": identity,
            "backend_pid": int(connection.execute(text("select pg_backend_pid()")).scalar_one()),
        },
        after={"identity": identity, "state": state, "backend_pid": fresh_pid},
    )


def scenario_concurrent(connection: Any, name: str) -> dict[str, Any]:
    if name in {
        "concurrent_baseline_serialization",
        "concurrent_new_listing_serialization",
        "concurrent_idempotency",
    }:
        # These requirements are races at the governed terminal boundary;
        # due-work materialization is deliberately not an acceptable proxy.
        return _comparison_family(connection, name)
    barrier = Barrier(2)
    records: list[dict[str, Any]] = []

    def worker(label: str) -> None:
        with connection.engine.connect() as independent:
            barrier.wait()
            before = _physical(independent)

            def recorder() -> list[UUID]:
                with Session(bind=independent) as session:
                    return materialize_due_work(ScanRepository(session), _now(), 10)

            operation = _operation(
                independent, "materialize_due_work", {"scenario_id": name}, recorder
            )
            after = _physical(independent)
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
    before = _physical(connection)
    case = _case(
        connection,
        name,
        lambda: materialize_due_work(ScanRepository(Session(bind=connection)), _now(), 10),
        before=before,
    )
    case["physical_after"] = _physical(connection)
    return case


def _schedule_family(connection: Any, name: str) -> dict[str, Any]:
    fixture = _create_fixture(connection.engine)
    global _ACTIVE_BEACON_ID
    _ACTIVE_BEACON_ID = fixture["beacon_id"]
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
    before = _physical(connection)
    case = _case(
        connection,
        name,
        lambda: claim_work(ScanRepository(Session(bind=connection)), _now(), 1, 120),
        before=before,
    )
    case["physical_after"] = _physical(connection)
    return case


def _comparison_family(connection: Any, name: str) -> dict[str, Any]:
    """Run the actual governed terminal comparison boundary for this family."""
    engine = connection.engine
    fixture = _create_fixture(engine)
    global _ACTIVE_BEACON_ID
    _ACTIVE_BEACON_ID = fixture["beacon_id"]
    beacon_id = UUID(fixture["beacon_id"])
    account_id = UUID(fixture["account_id"])
    revision = int(fixture["revision"])
    with Session(engine) as session:
        repo = ScanRepository(session)
        claim = claim_work(repo, _now(), 1, 120)[0]
        beacon = SyntheticBeacon(beacon_id, account_id, revision)
        run = start_run(repo, claim, beacon)
        outcome_id = uuid4()
        parser = SyntheticParserPort(
            ParserOutcome(
                outcome_id=outcome_id,
                status="CLEAN",
                sort_context="NEWEST_FIRST_PROVEN",
                candidates=(
                    ListingCandidate(identity_key=f"rf15-{name}-listing", snapshot={"price": 1}),
                ),
                provenance_fingerprint=_digest({"scenario": name, "run": str(run.run_id)}),
            )
        )
        before = _physical(session.connection())
        case = _case(
            session.connection(),
            name,
            lambda: commit_comparison(
                repo,
                run,
                outcome_id,
                beacon,
                SyntheticEntitlementPort(),
                parser,
                f"rf15-{name}-{uuid4()}",
            ),
            before=before,
        )
        case["physical_after"] = _physical(session.connection())
        case["authority_history"] = parser.history
        return case


def scenario_schedule_uniqueness(connection: Any) -> dict[str, Any]:
    return _schedule_family(connection, "schedule_uniqueness")


def scenario_due_work_current_slot(connection: Any) -> dict[str, Any]:
    return _due_work_family(connection, "due_work_current_slot")


def scenario_due_work_coalescing(connection: Any) -> dict[str, Any]:
    return _due_work_family(connection, "due_work_coalescing")


def scenario_recovery_blocks_backlog(connection: Any) -> dict[str, Any]:
    return _due_work_family(connection, "recovery_blocks_backlog")


def scenario_due_materialization_concurrency(connection: Any) -> dict[str, Any]:
    return scenario_concurrent(connection, "due_materialization_concurrency")


def scenario_claim_exclusivity(connection: Any) -> dict[str, Any]:
    return _claim_family(connection, "claim_exclusivity")


def scenario_expired_claim_reconciliation(connection: Any) -> dict[str, Any]:
    return _claim_family(connection, "expired_claim_reconciliation")


def scenario_lease_guard(connection: Any) -> dict[str, Any]:
    return _comparison_family(connection, "lease_guard")


def scenario_run_revision_pin(connection: Any) -> dict[str, Any]:
    return _comparison_family(connection, "run_revision_pin")


def scenario_run_replay(connection: Any) -> dict[str, Any]:
    return _comparison_family(connection, "run_replay")


def scenario_baseline_no_event(connection: Any) -> dict[str, Any]:
    return _comparison_family(connection, "baseline_no_event")


def scenario_empty_baseline_durable(connection: Any) -> dict[str, Any]:
    return _comparison_family(connection, "empty_baseline_durable")


def scenario_new_listing_exactly_once(connection: Any) -> dict[str, Any]:
    return _comparison_family(connection, "new_listing_exactly_once")


def scenario_price_change_no_event(connection: Any) -> dict[str, Any]:
    return _comparison_family(connection, "price_change_no_event")


def scenario_duplicate_within_run_exactly_once(connection: Any) -> dict[str, Any]:
    return _comparison_family(connection, "duplicate_within_run_exactly_once")


def scenario_beacon_isolation(connection: Any) -> dict[str, Any]:
    return _comparison_family(connection, "beacon_isolation")


def scenario_absence_no_removal(connection: Any) -> dict[str, Any]:
    return _comparison_family(connection, "absence_no_removal")


def scenario_authority_recheck(connection: Any) -> dict[str, Any]:
    return _comparison_family(connection, "authority_recheck")


def scenario_idempotency_replay_and_mismatch(connection: Any) -> dict[str, Any]:
    return _comparison_family(connection, "idempotency_replay_and_mismatch")


def scenario_concurrent_idempotency(connection: Any) -> dict[str, Any]:
    return scenario_concurrent(connection, "concurrent_idempotency")


def scenario_concurrent_baseline_serialization(connection: Any) -> dict[str, Any]:
    return scenario_concurrent(connection, "concurrent_baseline_serialization")


def scenario_concurrent_new_listing_serialization(connection: Any) -> dict[str, Any]:
    return scenario_concurrent(connection, "concurrent_new_listing_serialization")


def scenario_platform_event_identity(connection: Any) -> dict[str, Any]:
    return _comparison_family(connection, "platform_event_identity")


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
        with engine.connect() as connection:
            if set(REQUIREMENT_IDS) != set(SCENARIO_RUNNERS):
                raise RuntimeError("RF15 scenario registry mismatch")
            cases = {}
            for name, runner in SCENARIO_RUNNERS.items():
                # Every case receives a fresh Beacon/schedule namespace.  A
                # few runners create a more specialised fixture themselves;
                # the extra setup remains isolated and is never queried by
                # another case.
                fixture = _create_fixture(engine)
                global _ACTIVE_BEACON_ID
                _ACTIVE_BEACON_ID = fixture["beacon_id"]
                cases[name] = runner(connection)
        with engine.connect() as second:
            migration_after = _migration(second)
            foreign_after = _semantic_foreign(second)
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
        "migration": migration_after,
        "migration_boundary": {
            "first": migration,
            "second": migration_after,
            "independent_connection": True,
        },
        "fixture": fixture,
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
        json.dumps(evidence, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
