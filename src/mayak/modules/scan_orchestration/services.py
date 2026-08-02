"""Durable schedule, claim, run and comparison services."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert

from .contracts import (
    AccessTier,
    BeaconPort,
    BeaconSnapshot,
    CadenceRejected,
    ComparisonResult,
    DecisionStatus,
    DependencyBlocked,
    EntitlementPort,
    EntitlementSnapshot,
    IdempotencyMismatch,
    LeaseConflict,
    ParserOutcome,
    RevisionConflict,
    RunResult,
    ScheduleCommand,
    ScheduleResult,
    WorkClaim,
)
from .repository import ScanRepository, _table


def validate_cadence(decision: EntitlementSnapshot, interval: int) -> None:
    if (
        decision.status is not DecisionStatus.ALLOWED
        or interval < decision.minimum_seconds
        or interval % decision.step_seconds
    ):
        raise CadenceRejected("interval is not allowed by the authoritative entitlement decision")
    expected = (300, 300) if decision.tier is AccessTier.BASIC else (10800, 10800)
    if (decision.minimum_seconds, decision.step_seconds) != expected:
        raise CadenceRejected("unsupported tariff policy")


class ScheduleService:
    def __init__(
        self, repository: ScanRepository, beacon: BeaconPort, entitlement: EntitlementPort
    ):
        self.repo, self.beacon, self.entitlement = repository, beacon, entitlement

    def create_or_update(self, command: ScheduleCommand) -> ScheduleResult:
        b = self.beacon.current(command.beacon_id)
        e = self.entitlement.current(command.beacon_id, b.account_id)
        validate_cadence(e, command.interval_seconds)
        schedules = _table("scan_schedules")
        with self.repo.session.begin():
            row = (
                self.repo.session.execute(
                    select(schedules)
                    .where(schedules.c.beacon_id == command.beacon_id)
                    .with_for_update()
                )
                .mappings()
                .first()
            )
            now = datetime.now(UTC)
            if row:
                self.repo.session.execute(
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
                return ScheduleResult(
                    schedule_id=row["id"],
                    beacon_id=command.beacon_id,
                    interval_seconds=command.interval_seconds,
                    next_due_at=command.next_due_at,
                    state="ACTIVE",
                )
            sid = self.repo.create_schedule(
                command.beacon_id, command.interval_seconds, command.next_due_at
            )
            return ScheduleResult(
                schedule_id=sid,
                beacon_id=command.beacon_id,
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
    now = now or datetime.now(UTC)
    snapshot = beacon.current(claim.beacon_id)
    with repo.session.begin():
        return repo.start_run(claim, snapshot.revision_no, now)


def commit_comparison(
    repo: ScanRepository,
    run: RunResult,
    parser: ParserOutcome,
    beacon: BeaconSnapshot,
    entitlement: EntitlementSnapshot,
    idempotency_key: str,
    now: datetime | None = None,
) -> ComparisonResult:
    now = now or datetime.now(UTC)
    if not parser.comparison_eligible:
        raise DependencyBlocked(f"parser outcome {parser.status} is not comparison eligible")
    if beacon.lifecycle_eligible is not True:
        raise DependencyBlocked("Beacon lifecycle is not eligible")
    validate_cadence(entitlement, 300 if entitlement.tier is AccessTier.BASIC else 10800)
    session = repo.session
    listings, observations, anchors, runs, outbox = (
        _table(n)
        for n in (
            "scan_beacon_listing_state",
            "scan_listing_observations",
            "scan_anchors",
            "scan_runs",
            "platform_event_outbox",
        )
    )
    candidates = {c.identity_key: c for c in parser.candidates}
    fingerprint = hashlib.sha256(
        json.dumps(
            {
                "run": str(run.run_id),
                "candidates": sorted(candidates),
                "parser": str(parser.outcome_id),
            },
            sort_keys=True,
        ).encode()
    ).hexdigest()
    with session.begin():
        old = (
            session.execute(
                select(_table("platform_idempotency_records"))
                .where(
                    _table("platform_idempotency_records").c.scope == "scan",
                    _table("platform_idempotency_records").c.idempotency_key == idempotency_key,
                )
                .with_for_update()
            )
            .mappings()
            .first()
        )
        if old:
            if old["request_fingerprint"] != fingerprint:
                raise IdempotencyMismatch("IDEMPOTENCY_MISMATCH")
            stored = old["result"]
            return ComparisonResult.model_validate(
                stored, strict=False, from_attributes=False
            ).model_copy(update={"replayed": True})
        runrow = (
            session.execute(select(runs).where(runs.c.id == run.run_id).with_for_update())
            .mappings()
            .one()
        )
        work = _table("scan_work_items")
        workrow = (
            session.execute(select(work).where(work.c.id == run.work_item_id).with_for_update())
            .mappings()
            .one()
        )
        if (
            workrow["lease_token"] != run.lease_token
            or workrow["lease_expires_at"] <= now
            or workrow["state"] != "CLAIMED"
        ):
            raise LeaseConflict("terminal effects require the current unexpired lease")
        if runrow["revision_no"] != beacon.revision_no:
            raise RevisionConflict("Beacon revision changed during run")
        prior = session.execute(
            select(listings.c.external_listing_key)
            .where(listings.c.beacon_id == beacon.beacon_id)
            .limit(1)
        ).first()
        baseline = prior is None
        new_keys: list[str] = []
        event_ids: list[UUID] = []
        for candidate in candidates.values():
            snap = candidate.snapshot
            obs_id = uuid4()
            session.execute(
                insert(observations).values(
                    id=obs_id,
                    run_id=run.run_id,
                    beacon_id=beacon.beacon_id,
                    external_listing_key=candidate.identity_key,
                    snapshot=snap,
                    observed_at=now,
                    fingerprint=hashlib.sha256(
                        json.dumps(snap, sort_keys=True).encode()
                    ).hexdigest(),
                )
            )
            known = session.execute(
                select(listings.c.id)
                .where(
                    listings.c.beacon_id == beacon.beacon_id,
                    listings.c.external_listing_key == candidate.identity_key,
                )
                .with_for_update()
            ).first()
            if known:
                session.execute(
                    update(listings)
                    .where(listings.c.id == known[0])
                    .values(
                        last_seen_at=now,
                        last_snapshot=snap,
                        updated_at=now,
                        row_version=listings.c.row_version + 1,
                    )
                )
            else:
                session.execute(
                    insert(listings).values(
                        id=uuid4(),
                        beacon_id=beacon.beacon_id,
                        external_listing_key=candidate.identity_key,
                        last_seen_at=now,
                        last_snapshot=snap,
                        first_seen_at=now,
                        updated_at=now,
                        row_version=1,
                    )
                )
                if not baseline:
                    new_keys.append(candidate.identity_key)
                    event_id = uuid4()
                    event_ids.append(event_id)
                    event_fp = hashlib.sha256(
                        f"scan-new:{beacon.beacon_id}:{candidate.identity_key}".encode()
                    ).hexdigest()
                    session.execute(
                        insert(outbox)
                        .values(
                            id=event_id,
                            event_fingerprint=event_fp,
                            contract_name="ScanNewListing",
                            contract_version="1",
                            payload={
                                "beacon_id": str(beacon.beacon_id),
                                "scan_run_id": str(run.run_id),
                                "listing_key": candidate.identity_key,
                            },
                            state="PENDING",
                            available_at=now,
                            created_at=now,
                            attempt_count=0,
                            row_version=1,
                        )
                        .on_conflict_do_nothing(index_elements=["event_fingerprint"])
                    )
        if candidates:
            anchor_key = next(iter(candidates))
            anchor = (
                session.execute(
                    select(anchors).where(anchors.c.beacon_id == beacon.beacon_id).with_for_update()
                )
                .mappings()
                .first()
            )
            if anchor:
                session.execute(
                    update(anchors)
                    .where(anchors.c.id == anchor["id"])
                    .values(
                        anchor_key=anchor_key, updated_at=now, row_version=anchor["row_version"] + 1
                    )
                )
            else:
                session.execute(
                    insert(anchors).values(
                        id=uuid4(),
                        beacon_id=beacon.beacon_id,
                        anchor_key=anchor_key,
                        updated_at=now,
                        row_version=1,
                    )
                )
        result = ComparisonResult(
            run_id=run.run_id,
            baseline_established=baseline,
            new_listing_keys=tuple(new_keys),
            event_ids=tuple(event_ids),
        )
        session.execute(
            update(runs)
            .where(runs.c.id == run.run_id, runs.c.row_version == runrow["row_version"])
            .values(
                state="SUCCEEDED",
                parser_outcome_id=parser.outcome_id,
                completed_at=now,
                row_version=runrow["row_version"] + 1,
            )
        )
        session.execute(
            update(work)
            .where(work.c.id == run.work_item_id, work.c.lease_token == run.lease_token)
            .values(
                state="SUCCEEDED",
                lease_started_at=None,
                lease_expires_at=None,
                lease_token=None,
                row_version=workrow["row_version"] + 1,
            )
        )
        session.execute(
            insert(_table("platform_idempotency_records")).values(
                id=uuid4(),
                scope="scan",
                idempotency_key=idempotency_key,
                request_fingerprint=fingerprint,
                result=result.model_dump(mode="json"),
                expires_at=now.replace(year=now.year + 1),
                created_at=now,
            )
        )
        return result


__all__ = [
    "ScheduleService",
    "claim_work",
    "commit_comparison",
    "materialize_due_work",
    "start_run",
    "validate_cadence",
]
