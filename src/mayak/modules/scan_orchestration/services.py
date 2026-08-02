"""Durable schedule, claim, run and comparison orchestration."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert

from mayak.contracts.results import CommonOutcome, Result
from mayak.persistence.events import publish_event
from mayak.persistence.idempotency import PostgresTerminalIdempotencyRepository
from mayak.platform.idempotency import IdempotencyFingerprint, IdempotencyKey, IdempotencyScope

from .contracts import (
    AccessTier,
    BeaconPort,
    CadenceRejected,
    ComparisonResult,
    DecisionStatus,
    DependencyBlocked,
    EntitlementPort,
    EntitlementSnapshot,
    IdempotencyMismatch,
    LeaseConflict,
    ParserOutcomePort,
    ParserStatus,
    RevisionConflict,
    RunResult,
    ScheduleCommand,
    ScheduleResult,
    WorkClaim,
)
from .repository import ScanRepository, _table


def validate_cadence(decision: EntitlementSnapshot, interval: int) -> None:
    expected = (300, 300) if decision.tier is AccessTier.BASIC else (10800, 10800)
    if (
        decision.status is not DecisionStatus.ALLOWED
        or (decision.minimum_seconds, decision.step_seconds) != expected
        or interval < decision.minimum_seconds
        or interval % decision.step_seconds
    ):
        raise CadenceRejected("interval is not allowed by the authoritative entitlement decision")


class ScheduleService:
    def __init__(
        self, repository: ScanRepository, beacon: BeaconPort, entitlement: EntitlementPort
    ):
        self.repo, self.beacon, self.entitlement = repository, beacon, entitlement

    def create_or_update(self, command: ScheduleCommand) -> ScheduleResult:
        current = self.beacon.current(command.beacon_id)
        decision = self.entitlement.current(command.beacon_id, current.account_id)
        validate_cadence(decision, command.interval_seconds)
        schedules = _table("scan_schedules")
        with self.repo.session.begin():
            row = (
                self.repo.session.execute(
                    select(schedules)
                    .where(schedules.c.beacon_id == current.beacon_id)
                    .with_for_update()
                )
                .mappings()
                .first()
            )
            now = datetime.now(UTC)
            if row:
                changed = self.repo.session.execute(
                    update(schedules)
                    .where(
                        schedules.c.id == row["id"], schedules.c.row_version == row["row_version"]
                    )
                    .values(
                        interval_seconds=command.interval_seconds,
                        next_due_at=command.next_due_at,
                        updated_at=now,
                        row_version=row["row_version"] + 1,
                    )
                )
                if changed.rowcount != 1:
                    raise RevisionConflict("schedule row version changed")
                return ScheduleResult(
                    schedule_id=row["id"],
                    beacon_id=current.beacon_id,
                    interval_seconds=command.interval_seconds,
                    next_due_at=command.next_due_at,
                    state="ACTIVE",
                )
            sid = self.repo.create_schedule(
                current.beacon_id, command.interval_seconds, command.next_due_at
            )
            return ScheduleResult(
                schedule_id=sid,
                beacon_id=current.beacon_id,
                interval_seconds=command.interval_seconds,
                next_due_at=command.next_due_at,
                state="ACTIVE",
            )


def materialize_due_work(repo: ScanRepository, now: datetime, limit: int) -> list[UUID]:
    with repo.session.begin():
        return repo.materialize_due_work(now, limit)


def claim_work(
    repo: ScanRepository, now: datetime, limit: int, lease_seconds: int
) -> list[WorkClaim]:
    with repo.session.begin():
        return repo.claim(now, limit, lease_seconds)


def start_run(
    repo: ScanRepository, claim: WorkClaim, beacon: BeaconPort, now: datetime | None = None
) -> RunResult:
    moment = now or datetime.now(UTC)
    current = beacon.current(claim.beacon_id)
    with repo.session.begin():
        return repo.start_run(claim, current.revision_no, moment)


def _comparison_outcome(result: ComparisonResult) -> CommonOutcome:
    return CommonOutcome(
        result=Result.SUCCEEDED,
        reason_code="SCAN_COMPARISON_COMMITTED",
        details=(
            json.dumps(result.model_dump(mode="json"), sort_keys=True, separators=(",", ":")),
        ),
    )


def _comparison_from_outcome(outcome: CommonOutcome, replayed: bool) -> ComparisonResult:
    if outcome.reason_code != "SCAN_COMPARISON_COMMITTED" or len(outcome.details) != 1:
        raise DependencyBlocked("stored Scan terminal outcome is not a comparison result")
    return ComparisonResult.model_validate(json.loads(outcome.details[0])).model_copy(
        update={"replayed": replayed}
    )


def commit_comparison(
    repo: ScanRepository,
    run: RunResult,
    parser_outcome_id: UUID,
    beacon: BeaconPort,
    entitlement: EntitlementPort,
    parser: ParserOutcomePort,
    idempotency_key: str,
    now: datetime | None = None,
) -> ComparisonResult:
    """Commit only after resolving all authority through server-owned ports."""
    moment = now or datetime.now(UTC)
    trusted_beacon = beacon.current(run.beacon_id)
    trusted_entitlement = entitlement.current(run.beacon_id, trusted_beacon.account_id)
    trusted_parser = parser.resolve(parser_outcome_id, run_id=run.run_id, beacon_id=run.beacon_id)
    if trusted_parser.outcome_id != parser_outcome_id or not trusted_parser.comparison_eligible:
        raise DependencyBlocked(
            f"parser outcome {trusted_parser.status} is not comparison eligible"
        )
    if trusted_beacon.lifecycle_eligible is not True:
        raise DependencyBlocked("Beacon lifecycle is not eligible")
    validate_cadence(
        trusted_entitlement, 300 if trusted_entitlement.tier is AccessTier.BASIC else 10800
    )
    candidates = {candidate.identity_key: candidate for candidate in trusted_parser.candidates}
    fingerprint = hashlib.sha256(
        json.dumps(
            {
                "run": str(run.run_id),
                "candidates": [
                    {"identity_key": key, "snapshot": candidates[key].snapshot}
                    for key in sorted(candidates)
                ],
                "parser": str(parser_outcome_id),
                "provenance": trusted_parser.provenance_fingerprint,
            },
            sort_keys=True,
        ).encode()
    ).hexdigest()
    session = repo.session
    schedules, work, runs, observations, listings, anchors = (
        _table(name)
        for name in (
            "scan_schedules",
            "scan_work_items",
            "scan_runs",
            "scan_listing_observations",
            "scan_beacon_listing_state",
            "scan_anchors",
        )
    )
    with session.begin():
        idem = PostgresTerminalIdempotencyRepository()
        resolution = idem.evaluate(
            session,
            scope=IdempotencyScope(value="scan.comparison"),
            key=IdempotencyKey(value=idempotency_key),
            fingerprint=IdempotencyFingerprint(value=fingerprint),
            now=moment,
        )
        if resolution.decision.decision.name == "MISMATCH":
            raise IdempotencyMismatch("IDEMPOTENCY_MISMATCH")
        if resolution.outcome is not None:
            return _comparison_from_outcome(resolution.outcome, True)
        runrow = (
            session.execute(select(runs).where(runs.c.id == run.run_id).with_for_update())
            .mappings()
            .one()
        )
        workrow = (
            session.execute(select(work).where(work.c.id == run.work_item_id).with_for_update())
            .mappings()
            .one()
        )
        schedulerow = (
            session.execute(
                select(schedules).where(schedules.c.id == workrow["schedule_id"]).with_for_update()
            )
            .mappings()
            .one()
        )
        if (
            workrow["lease_token"] != run.lease_token
            or workrow["lease_expires_at"] <= moment
            or workrow["state"] != "CLAIMED"
        ):
            raise LeaseConflict("terminal effects require the current unexpired lease")
        if (
            workrow["beacon_id"] != runrow["beacon_id"]
            or schedulerow["beacon_id"] != runrow["beacon_id"]
            or runrow["beacon_id"] != trusted_beacon.beacon_id
            or runrow["revision_no"] != trusted_beacon.revision_no
        ):
            raise RevisionConflict(
                "Run, work item, schedule and Beacon are not the same authority scope"
            )
        current_beacon = beacon.current(runrow["beacon_id"])
        current_entitlement = entitlement.current(runrow["beacon_id"], current_beacon.account_id)
        if not current_beacon.lifecycle_eligible:
            raise DependencyBlocked("Beacon lifecycle recheck denied commit")
        if current_beacon.revision_no != runrow["revision_no"]:
            raise RevisionConflict("Beacon revision changed during run")
        validate_cadence(
            current_entitlement, 300 if current_entitlement.tier is AccessTier.BASIC else 10800
        )
        baseline = (
            session.execute(
                select(runs.c.id)
                .where(
                    runs.c.beacon_id == runrow["beacon_id"],
                    runs.c.state.in_(("SUCCEEDED_BASELINE", "SUCCEEDED_DIFFERENCE")),
                    runs.c.id != run.run_id,
                )
                .limit(1)
            ).first()
            is None
        )
        new_keys: list[str] = []
        event_ids: list[UUID] = []
        for candidate in candidates.values():
            snapshot = candidate.snapshot
            session.execute(
                insert(observations)
                .values(
                    id=uuid4(),
                    run_id=run.run_id,
                    beacon_id=runrow["beacon_id"],
                    external_listing_key=candidate.identity_key,
                    snapshot=snapshot,
                    observed_at=moment,
                    fingerprint=hashlib.sha256(
                        json.dumps(
                            snapshot, sort_keys=True, separators=(",", ":"), ensure_ascii=False
                        ).encode()
                    ).hexdigest(),
                )
                .on_conflict_do_nothing(index_elements=["run_id", "external_listing_key"])
            )
            known = (
                session.execute(
                    select(listings)
                    .where(
                        listings.c.beacon_id == runrow["beacon_id"],
                        listings.c.external_listing_key == candidate.identity_key,
                    )
                    .with_for_update()
                )
                .mappings()
                .first()
            )
            if known:
                session.execute(
                    update(listings)
                    .where(
                        listings.c.id == known["id"], listings.c.row_version == known["row_version"]
                    )
                    .values(
                        last_seen_at=moment,
                        last_snapshot=snapshot,
                        updated_at=moment,
                        row_version=known["row_version"] + 1,
                    )
                )
                continue
            session.execute(
                insert(listings)
                .values(
                    id=uuid4(),
                    beacon_id=runrow["beacon_id"],
                    external_listing_key=candidate.identity_key,
                    last_seen_at=moment,
                    last_snapshot=snapshot,
                    first_seen_at=moment,
                    updated_at=moment,
                    row_version=1,
                )
                .on_conflict_do_nothing(index_elements=["beacon_id", "external_listing_key"])
            )
            if not baseline:
                new_keys.append(candidate.identity_key)
                event_ids.append(
                    publish_event(
                        session,
                        event_id=uuid4(),
                        event_fingerprint=hashlib.sha256(
                            f"scan-new:{runrow['beacon_id']}:{candidate.identity_key}".encode()
                        ).hexdigest(),
                        contract_name="ScanNewListing",
                        contract_version="1",
                        payload={
                            "beacon_id": str(runrow["beacon_id"]),
                            "scan_run_id": str(run.run_id),
                            "listing_key": candidate.identity_key,
                        },
                        available_at=moment,
                    )
                )
        if candidates:
            anchor_key = next(iter(candidates))
            anchor = (
                session.execute(
                    select(anchors)
                    .where(anchors.c.beacon_id == runrow["beacon_id"])
                    .with_for_update()
                )
                .mappings()
                .first()
            )
            if anchor:
                changed = session.execute(
                    update(anchors)
                    .where(
                        anchors.c.id == anchor["id"], anchors.c.row_version == anchor["row_version"]
                    )
                    .values(
                        anchor_key=anchor_key,
                        updated_at=moment,
                        row_version=anchor["row_version"] + 1,
                    )
                )
                if changed.rowcount != 1:
                    raise RevisionConflict("anchor row version changed")
            else:
                session.execute(
                    insert(anchors).values(
                        id=uuid4(),
                        beacon_id=runrow["beacon_id"],
                        anchor_key=anchor_key,
                        updated_at=moment,
                        row_version=1,
                    )
                )
        result = ComparisonResult(
            run_id=run.run_id,
            baseline_established=baseline,
            new_listing_keys=tuple(new_keys),
            event_ids=tuple(event_ids),
        )
        changed_run = session.execute(
            update(runs)
            .where(runs.c.id == run.run_id, runs.c.row_version == runrow["row_version"])
            .values(
                state="SUCCEEDED_BASELINE" if baseline else "SUCCEEDED_DIFFERENCE",
                parser_outcome_id=trusted_parser.outcome_id,
                completed_at=moment,
                row_version=runrow["row_version"] + 1,
            )
        )
        if changed_run.rowcount != 1:
            raise RevisionConflict("run row version changed")
        changed_work = session.execute(
            update(work)
            .where(
                work.c.id == run.work_item_id,
                work.c.lease_token == run.lease_token,
                work.c.row_version == workrow["row_version"],
            )
            .values(
                state="SUCCEEDED",
                lease_started_at=None,
                lease_expires_at=None,
                lease_token=None,
                row_version=workrow["row_version"] + 1,
            )
        )
        if changed_work.rowcount != 1:
            raise LeaseConflict("work lease row changed")
        recorded = idem.record_terminal(
            session,
            record_id=uuid4(),
            scope=IdempotencyScope(value="scan.comparison"),
            key=IdempotencyKey(value=idempotency_key),
            fingerprint=IdempotencyFingerprint(value=fingerprint),
            outcome=_comparison_outcome(result),
            created_at=moment,
            expires_at=moment + timedelta(days=14),
            now=moment,
        )
        return (
            _comparison_from_outcome(recorded.outcome, True)
            if recorded.outcome is not None
            else result
        )


class ScanRuntimeService:
    """Composition root: callers supply identifiers; ports supply authority."""

    def __init__(
        self,
        repository: ScanRepository,
        beacon: BeaconPort,
        entitlement: EntitlementPort,
        parser: ParserOutcomePort,
    ):
        self.repository, self.beacon, self.entitlement, self.parser = (
            repository,
            beacon,
            entitlement,
            parser,
        )

    def commit_comparison(
        self,
        run: RunResult,
        parser_outcome_id: UUID,
        idempotency_key: str,
        now: datetime | None = None,
    ) -> ComparisonResult:
        return commit_comparison(
            self.repository,
            run,
            parser_outcome_id,
            self.beacon,
            self.entitlement,
            self.parser,
            idempotency_key,
            now,
        )


def record_parser_outcome(
    repo: ScanRepository,
    run: RunResult,
    parser_outcome_id: UUID,
    parser: ParserOutcomePort,
    now: datetime | None = None,
) -> str:
    """Durably classify a non-comparison result without touching listing state."""
    moment = now or datetime.now(UTC)
    outcome = parser.resolve(parser_outcome_id, run_id=run.run_id, beacon_id=run.beacon_id)
    ambiguous = outcome.status in {
        ParserStatus.PARTIAL,
        ParserStatus.RESULT_AMBIGUOUS,
        ParserStatus.TRANSPORT_AMBIGUOUS,
        ParserStatus.REFERENCE_DISPUTED,
        ParserStatus.REFERENCE_MISSING,
        ParserStatus.REFERENCE_STALE,
        ParserStatus.TRANSPORT_UNAVAILABLE,
    }
    state = "PENDING_RECONCILIATION" if ambiguous else "FAILED"
    runs, work = _table("scan_runs"), _table("scan_work_items")
    with repo.session.begin():
        runrow = (
            repo.session.execute(select(runs).where(runs.c.id == run.run_id).with_for_update())
            .mappings()
            .one()
        )
        workrow = (
            repo.session.execute(
                select(work).where(work.c.id == run.work_item_id).with_for_update()
            )
            .mappings()
            .one()
        )
        if (
            runrow["beacon_id"] != run.beacon_id
            or workrow["beacon_id"] != run.beacon_id
            or workrow["lease_token"] != run.lease_token
            or workrow["lease_expires_at"] <= moment
        ):
            raise LeaseConflict("parser outcome recording requires the current lease")
        changed = repo.session.execute(
            update(runs)
            .where(runs.c.id == run.run_id, runs.c.row_version == runrow["row_version"])
            .values(
                state=state,
                parser_outcome_id=outcome.outcome_id,
                completed_at=moment,
                row_version=runrow["row_version"] + 1,
            )
        )
        if changed.rowcount != 1:
            raise RevisionConflict("run row version changed while recording parser outcome")
        repo.session.execute(
            update(work)
            .where(
                work.c.id == run.work_item_id,
                work.c.row_version == workrow["row_version"],
                work.c.lease_token == run.lease_token,
            )
            .values(
                state=state,
                lease_started_at=None,
                lease_expires_at=None,
                lease_token=None,
                row_version=workrow["row_version"] + 1,
            )
        )
    return state


__all__ = [
    "ScanRuntimeService",
    "ScheduleService",
    "claim_work",
    "commit_comparison",
    "materialize_due_work",
    "record_parser_outcome",
    "start_run",
    "validate_cadence",
]
