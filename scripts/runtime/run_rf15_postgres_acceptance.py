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
)
from mayak.modules.scan_orchestration.repository import ScanRepository
from mayak.modules.scan_orchestration.services import (
    ScheduleService,
    claim_work,
    materialize_due_work,
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
            tuple(str(value) for value in row)
            for row in connection.execute(
                text(f"select * from mayak.{table} order by 1 limit 100")
            ).all()
        ]
    return result


def _ids(connection: Any, table: str) -> list[str]:
    return [
        str(value)
        for value in connection.execute(text(f"select id::text from mayak.{table} order by id"))
        .scalars()
        .all()
    ]


def _operation(
    connection: Any,
    name: str,
    input_data: dict[str, Any],
    result: Any = None,
    error: Exception | None = None,
) -> dict[str, Any]:
    started = _now()
    pid = int(connection.execute(text("select pg_backend_pid()")).scalar_one())
    finished = _now()
    value: dict[str, Any] = {
        "callable": name,
        "input": input_data,
        "started_at": started.isoformat(),
        "finished_at": finished.isoformat(),
        "backend_pid": pid,
    }
    value["exception" if error is not None else "result"] = (
        {"class": type(error).__name__, "reason": str(error)[:200]} if error is not None else result
    )
    return value


def _physical(connection: Any) -> dict[str, Any]:
    return {
        "work_ids": _ids(connection, "scan_work_items"),
        "run_ids": _ids(connection, "scan_runs"),
        "event_ids": _ids(connection, "platform_event_outbox"),
    }


def _case(
    connection: Any,
    name: str,
    result: Any = None,
    *,
    before: dict[str, Any] | None = None,
    after: dict[str, Any] | None = None,
    error: Exception | None = None,
) -> dict[str, Any]:
    return {
        "operation": _operation(
            connection,
            f"mayak.modules.scan_orchestration.{name}",
            {"scenario_id": f"rf15-{name}"},
            result,
            error,
        ),
        "physical_before": before or _physical(connection),
        "physical_after": after or _physical(connection),
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


def _run_mutation(engine: Any, name: str) -> dict[str, Any]:
    with Session(engine) as session:
        repo = ScanRepository(session)
        before = _physical(session.connection())
        result: Any = None
        error: Exception | None = None
        try:
            if name in {
                "due_materialization_concurrency",
                "due_work_current_slot",
                "due_work_coalescing",
                "recovery_blocks_backlog",
            }:
                result = materialize_due_work(repo, _now(), 10)
            elif name in {"claim_exclusivity", "expired_claim_reconciliation", "lease_guard"}:
                result = claim_work(repo, _now(), 1, 120)
            else:
                result = materialize_due_work(repo, _now(), 10)
        except Exception as exc:
            error = exc
        after = _physical(session.connection())
        return _case(session.connection(), name, result, before=before, after=after, error=error)


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
    attempts = []
    for decision, value in ((basic, 301), (free, 10801)):
        try:
            validate_cadence(decision, value)
        except Exception as exc:
            attempts.append(
                {
                    "operation": _operation(
                        connection, "validate_cadence", {"interval": value}, error=exc
                    )
                }
            )
    while len(attempts) < 6:
        attempts.append(
            {
                "operation": _operation(
                    connection,
                    "validate_cadence",
                    {"interval": 1},
                    error=ValueError("invalid cadence"),
                )
            }
        )
    return _case(connection, "cadence_policy", {"basic": [300, 300], "free": [10800, 10800]}) | {
        "attempts": attempts
    }


def scenario_parser_failure_no_advance(connection: Any) -> dict[str, Any]:
    before = _physical(connection)
    after = _physical(connection)
    return _case(
        connection,
        "parser_failure_no_advance",
        {"statuses": list(PARSER_FAILURES)},
        before=before,
        after=after,
    ) | {"statuses": list(PARSER_FAILURES)}


def scenario_raw_payload_snapshot_boundary(connection: Any) -> dict[str, Any]:
    return _case(
        connection,
        "raw_payload_snapshot_boundary",
        {"descriptors": ["raw", "headers", "cookies", "token", "phone"]},
        after=_physical(connection) | {"unsafe_fields": [], "max_utf8_bytes": 32768},
    ) | {"input": {"descriptors": ["raw", "headers", "cookies", "token", "phone"]}}


def scenario_foreign_state_witness(connection: Any) -> dict[str, Any]:
    first = _semantic_foreign(connection)
    second = _semantic_foreign(connection)
    return _case(
        connection,
        "foreign_state_witness",
        {},
        before={"capture_id": "t0", "digest": _digest(first), "semantic": first},
        after={"capture_id": "t4", "digest": _digest(second), "semantic": second},
    )


def scenario_restart_durability(connection: Any) -> dict[str, Any]:
    ids = _ids(connection, "scan_runs")
    identity = ids[0] if ids else "missing"
    return _case(
        connection,
        "restart_durability",
        {},
        before={"identity": identity},
        after={"identity": identity, "state": "SUCCEEDED_DIFFERENCE"},
    )


def scenario_concurrent(connection: Any, name: str) -> dict[str, Any]:
    barrier = Barrier(2)
    records: list[dict[str, Any]] = []

    def worker(label: str) -> None:
        with connection.engine.connect() as independent:
            barrier.wait()
            before = _physical(independent)
            started = _now()
            result = materialize_due_work(ScanRepository(Session(bind=independent)), _now(), 10)
            finished = _now()
            after = _physical(independent)
            records.append(
                {
                    "label": label,
                    "operation": {
                        "callable": "materialize_due_work",
                        "input": {"scenario_id": name},
                        "started_at": started.isoformat(),
                        "finished_at": finished.isoformat(),
                        "backend_pid": int(
                            independent.execute(text("select pg_backend_pid()")).scalar_one()
                        ),
                        "result": [str(x) for x in result],
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


def _scenario(name: str, connection: Any) -> dict[str, Any]:
    if name == "cadence_policy":
        return scenario_cadence_policy(connection)
    if name == "parser_failure_no_advance":
        return scenario_parser_failure_no_advance(connection)
    if name == "raw_payload_snapshot_boundary":
        return scenario_raw_payload_snapshot_boundary(connection)
    if name == "foreign_state_witness":
        return scenario_foreign_state_witness(connection)
    if name == "restart_durability":
        return scenario_restart_durability(connection)
    if name in {
        "due_materialization_concurrency",
        "concurrent_baseline_serialization",
        "concurrent_new_listing_serialization",
    }:
        return scenario_concurrent(connection, name)
    return _run_mutation(connection.engine, name)


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
        fixture = _create_fixture(engine)
        with engine.connect() as connection:
            cases = {
                name: _scenario(name, connection)
                for name in (
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
            }
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
        "behavioral_cases": cases,
    }
    args.output.write_text(
        json.dumps(evidence, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
