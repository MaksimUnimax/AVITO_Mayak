"""Core-only PostgreSQL repository. Long-running provider work is outside transactions."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from mayak.persistence.metadata import metadata

from .contracts import IdempotencyMismatch, LeaseConflict, RunResult, WorkClaim


def _table(name: str):
    return metadata.tables[f"mayak.{name}"]


class ScanRepository:
    """Persistence operations with explicit caller-owned transaction boundaries."""

    def __init__(self, session: Session):
        self.session = session

    def create_schedule(self, beacon_id: UUID, interval: int, due: datetime) -> UUID:
        sid = uuid4()
        now = datetime.now(UTC)
        self.session.execute(
            insert(_table("scan_schedules")).values(
                id=sid,
                beacon_id=beacon_id,
                interval_seconds=interval,
                next_due_at=due,
                state="ACTIVE",
                created_at=now,
                updated_at=now,
                row_version=1,
            )
        )
        return sid

    def materialize_due_work(self, now: datetime, limit: int) -> list[UUID]:
        if not 1 <= limit <= 1000:
            raise ValueError("limit must be between 1 and 1000")
        schedules = _table("scan_schedules")
        work = _table("scan_work_items")
        made: list[UUID] = []
        rows = self.session.execute(
            select(schedules)
            .where(schedules.c.state == "ACTIVE", schedules.c.next_due_at <= now)
            .order_by(schedules.c.next_due_at, schedules.c.id)
            .limit(limit)
            .with_for_update(skip_locked=True)
        ).mappings()
        for row in rows:
            due = row["next_due_at"]
            wid = uuid4()
            result = self.session.execute(
                insert(work)
                .values(
                    id=wid,
                    schedule_id=row["id"],
                    beacon_id=row["beacon_id"],
                    due_at=due,
                    state="DUE",
                    attempt_count=0,
                    created_at=now,
                    row_version=1,
                )
                .on_conflict_do_nothing(index_elements=["schedule_id", "due_at"])
            )
            if result.rowcount:
                made.append(wid)
            self.session.execute(
                update(schedules)
                .where(schedules.c.id == row["id"], schedules.c.row_version == row["row_version"])
                .values(
                    next_due_at=now + timedelta(seconds=row["interval_seconds"]),
                    updated_at=now,
                    row_version=row["row_version"] + 1,
                )
            )
        return made

    def claim(self, now: datetime, limit: int, lease_seconds: int) -> list[WorkClaim]:
        if lease_seconds <= 0:
            raise ValueError("lease_seconds must be explicit and positive")
        work = _table("scan_work_items")
        rows = self.session.execute(
            select(work)
            .where(
                ((work.c.state.in_(["DUE", "RETRY"])) & (work.c.due_at <= now))
                | ((work.c.state == "CLAIMED") & (work.c.lease_expires_at < now))
            )
            .order_by(work.c.due_at, work.c.id)
            .limit(limit)
            .with_for_update(skip_locked=True)
        ).mappings()
        claims: list[WorkClaim] = []
        for row in rows:
            token = uuid4()
            expiry = now + timedelta(seconds=lease_seconds)
            self.session.execute(
                update(work)
                .where(work.c.id == row["id"])
                .values(
                    state="CLAIMED",
                    lease_started_at=now,
                    lease_expires_at=expiry,
                    lease_token=token,
                    attempt_count=row["attempt_count"] + 1,
                    row_version=row["row_version"] + 1,
                )
            )
            claims.append(
                WorkClaim(
                    work_item_id=row["id"],
                    beacon_id=row["beacon_id"],
                    schedule_id=row["schedule_id"],
                    due_at=row["due_at"],
                    lease_token=token,
                    lease_started_at=now,
                    lease_expires_at=expiry,
                )
            )
        return claims

    def start_run(self, claim: WorkClaim, beacon_revision: int, now: datetime) -> RunResult:
        work, runs = _table("scan_work_items"), _table("scan_runs")
        row = (
            self.session.execute(
                select(work).where(work.c.id == claim.work_item_id).with_for_update()
            )
            .mappings()
            .one()
        )
        if (
            row["lease_token"] != claim.lease_token
            or row["state"] != "CLAIMED"
            or row["lease_expires_at"] <= now
        ):
            raise LeaseConflict("lease token is lost, wrong or expired")
        existing = (
            self.session.execute(select(runs).where(runs.c.work_item_id == claim.work_item_id))
            .mappings()
            .first()
        )
        if existing:
            if existing["revision_no"] != beacon_revision:
                raise LeaseConflict("replay cannot substitute a Beacon revision")
            return RunResult(
                run_id=existing["id"],
                work_item_id=claim.work_item_id,
                beacon_id=existing["beacon_id"],
                revision_no=existing["revision_no"],
                state=existing["state"],
                lease_token=claim.lease_token,
                replayed=True,
            )
        run_id = uuid4()
        self.session.execute(
            insert(runs).values(
                id=run_id,
                work_item_id=claim.work_item_id,
                beacon_id=claim.beacon_id,
                revision_no=beacon_revision,
                state="RUNNING",
                started_at=now,
                row_version=1,
            )
        )
        return RunResult(
            run_id=run_id,
            work_item_id=claim.work_item_id,
            beacon_id=claim.beacon_id,
            revision_no=beacon_revision,
            state="RUNNING",
            lease_token=claim.lease_token,
        )

    def _idempotency(self, key: str, fingerprint: str, result: dict, now: datetime) -> bool:
        table = _table("platform_idempotency_records")
        old = (
            self.session.execute(
                select(table)
                .where(table.c.scope == "scan", table.c.idempotency_key == key)
                .with_for_update()
            )
            .mappings()
            .first()
        )
        if old:
            if old["request_fingerprint"] != fingerprint:
                raise IdempotencyMismatch("IDEMPOTENCY_MISMATCH")
            return True
        self.session.execute(
            insert(table).values(
                id=uuid4(),
                scope="scan",
                idempotency_key=key,
                request_fingerprint=fingerprint,
                result=result,
                expires_at=now + timedelta(days=30),
                created_at=now,
            )
        )
        return False

    def commit_comparison(
        self, run: RunResult, parser, beacon, entitlement, idempotency_key: str, now: datetime
    ):
        from .services import commit_comparison

        return commit_comparison(self, run, parser, beacon, entitlement, idempotency_key, now)


__all__ = ["ScanRepository"]
