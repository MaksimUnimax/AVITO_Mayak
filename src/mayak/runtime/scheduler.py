"""Production-shaped durable scheduler process for Module 06."""

from __future__ import annotations

import logging
import signal
import time
from datetime import UTC, datetime
from types import FrameType

from mayak.modules.scan_orchestration.services import materialize_due_work
from mayak.runtime.rf24_composition import RF24RuntimeComposition, build_rf24_composition
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
    LOGGER.info("scheduler materialized=%d", len(made))
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
