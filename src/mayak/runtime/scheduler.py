"""Production-shaped durable scheduler process for Module 06."""

from __future__ import annotations

import logging
import signal
import time
from datetime import UTC, datetime
from types import FrameType

from sqlalchemy import select

from mayak.modules.scan_orchestration.services import materialize_due_work
from mayak.persistence.metadata import metadata
from mayak.runtime.rf24_composition import RF24RuntimeComposition, build_rf24_composition
from mayak.runtime.rf24_provenance import emit_process_observation
from mayak.runtime.settings import load_runtime_settings

LOGGER = logging.getLogger("mayak.scheduler")


class Shutdown:
    requested = False

    def __call__(self, _signum: int, _frame: FrameType | None) -> None:
        self.requested = True


def run_once(
    composition: RF24RuntimeComposition, *, now: datetime | None = None
) -> int:
    moment = now or datetime.now(UTC)
    with composition.sessions() as session:
        made = materialize_due_work(
            composition.scan_repository(session), moment, composition.settings.worker.batch_size
        )
        if made:
            work = metadata.tables["mayak.scan_work_items"]
            rows = session.execute(
                select(work.c.id, work.c.schedule_id, work.c.beacon_id, work.c.due_at)
                .where(work.c.id.in_(made))
            ).mappings()
            for row in rows:
                emit_process_observation(
                    {
                        "record_type": "scheduler_materialization",
                        "materialized_count": len(made),
                        "schedule_id": str(row["schedule_id"]),
                        "work_item_id": str(row["id"]),
                        "beacon_id": str(row["beacon_id"]),
                        "due_at": row["due_at"].isoformat(),
                    }
                )
        message = (
            f"scheduler process=mayak-scheduler materialized={len(made)} "
            f"work_item_ids={','.join(str(item) for item in made) or 'none'}"
        )
        LOGGER.info(message)
        print(message, flush=True)
    return len(made)


def main() -> None:
    settings = load_runtime_settings()
    if settings.runtime.process_kind.value != "mayak-scheduler":
        raise RuntimeError("invalid process kind")
    logging.basicConfig(level=settings.observability.log_level.value, force=True)
    shutdown = Shutdown()
    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)
    composition = build_rf24_composition(settings)
    try:
        while not shutdown.requested:
            run_once(composition)
            shutdown_event = min(settings.scheduler.poll_interval_seconds, 30)
            deadline = time.monotonic() + shutdown_event
            while not shutdown.requested and time.monotonic() < deadline:
                time.sleep(min(0.25, max(0.0, deadline - time.monotonic())))
    finally:
        composition.close()
        LOGGER.info("scheduler process stopped")


if __name__ == "__main__":
    main()


__all__ = ["main", "run_once"]
