"""Production-shaped durable Scan worker process for Module 06."""

from __future__ import annotations

import logging
import os
import signal
import time
from datetime import UTC, datetime
from types import FrameType
from typing import Any, cast
from uuid import UUID

from sqlalchemy import func, select

from mayak.modules.avito_parser_adapter.contracts import ParserOutcomeStatus
from mayak.modules.avito_parser_adapter.runtime import NormalizedListingSnapshot
from mayak.modules.notification_delivery.attempt import NotificationProviderOutcomeClass
from mayak.modules.notification_delivery.runtime import (
    AttemptLease,
    FakeProviderOutcome,
    run_worker_cycle,
)
from mayak.modules.scan_orchestration.services import (
    claim_work,
    commit_comparison,
    record_parser_outcome,
    start_run,
)
from mayak.persistence.metadata import metadata
from mayak.runtime.rf24_composition import RF24RuntimeComposition, build_rf24_composition
from mayak.runtime.rf24_provenance import emit_process_observation
from mayak.runtime.settings import load_runtime_settings

LOGGER = logging.getLogger("mayak.worker")


class Shutdown:
    requested = False

    def __call__(self, _signum: int, _frame: FrameType | None) -> None:
        self.requested = True


def _scenario(session: Any, beacon_id: UUID) -> str:
    """Resolve only fixed, run-scoped synthetic controls in acceptance mode."""
    profile = os.environ.get("MAYAK_RUNTIME_PROFILE")
    value = os.environ.get("MAYAK_SYNTHETIC_SCENARIO", "usable_listing_page")
    allowed = {
        "usable_listing_page",
        "usable_listing_page_with_new_listing",
        "partial",
        "captcha",
        "rate_restricted",
        "transport_unavailable", "transport_ambiguous", "clean_empty",
        "route_failure",
    }
    if profile != "synthetic_acceptance":
        return "usable_listing_page"
    if os.environ.get("MAYAK_SYNTHETIC_SCENARIO_RUN_ID") != os.environ.get("MAYAK_ENVIRONMENT_ID"):
        return "usable_listing_page"
    if os.environ.get("RF24_FORCE_COMPLETE_SAME_LISTING") == "true":
        return "usable_listing_page"
    if value in {"usable_listing_page", "usable_listing_page_with_new_listing"}:
        runs = metadata.tables["mayak.scan_runs"]
        prior = session.execute(
            select(func.count()).select_from(runs).where(runs.c.beacon_id == beacon_id)
        ).scalar_one()
        return "usable_listing_page" if prior <= 1 else "usable_listing_page_with_new_listing"
    return value if value in allowed else "usable_listing_page"


def process_once(
    composition: RF24RuntimeComposition, *, now: datetime | None = None
) -> int:
    moment = now or datetime.now(UTC)
    with composition.sessions() as session:
        repo = composition.scan_repository(session)
        claims = claim_work(
            repo,
            moment,
            composition.settings.worker.batch_size,
            composition.settings.worker.lease_seconds,
            reclaim_pending=os.environ.get("RF24_RECLAIM_PENDING") == "true",
        )
        processed = 0
        LOGGER.info(
            "worker process=%s claims=%d work_item_ids=%s",
            "mayak-worker",
            len(claims),
            ",".join(str(item.work_item_id) for item in claims) or "none",
        )
        for claim in claims:
            emit_process_observation(
                {
                    "record_type": "worker_claim",
                    "claim_id": f"pid-{os.getpid()}-work-{claim.work_item_id}",
                    "work_item_id": str(claim.work_item_id),
                    "schedule_id": str(claim.schedule_id),
                    "beacon_id": str(claim.beacon_id),
                }
            )
            if os.environ.get("RF24_HOLD_AFTER_CLAIM") == "true":
                emit_process_observation(
                    {
                        "record_type": "worker_controlled_hold",
                        "work_item_id": str(claim.work_item_id),
                    }
                )
                while not os.environ.get("RF24_RELEASE_HOLD") == "true":
                    time.sleep(0.1)
            try:
                beacon = composition.scan_beacon(session)
                run = start_run(repo, claim, beacon, now=moment)
                LOGGER.info(
                    "worker claim work_item_id=%s schedule_id=%s run_id=%s",
                    claim.work_item_id, claim.schedule_id, run.run_id,
                )
                scenario = _scenario(session, run.beacon_id)
                if scenario == "route_failure":
                    scenario = "transport_unavailable"
                session.commit()
                synthetic = composition.parser.run_synthetic(
                    scenario, request_id=f"rf24::{run.run_id}"
                )
                page = synthetic.page
                with session.begin():
                    persisted = composition.parser.persist_outcome(
                        session,
                        beacon_id=run.beacon_id,
                        run_id=run.run_id,
                        attempt=synthetic.attempt,
                        normalized_snapshot=(
                            NormalizedListingSnapshot.from_page(page) if page is not None else None
                        ),
                        purpose="scan",
                        observed_at=moment,
                    )
                parser = composition.parser_port(session)
                if (
                    synthetic.attempt.parser_status is ParserOutcomeStatus.USABLE_RESPONSE
                    and page is not None
                ):
                    comparison = commit_comparison(
                        repo,
                        run,
                        persisted.outcome_id,
                        beacon,
                        composition.scan_entitlement(session),
                        parser,
                        f"scan:{claim.work_item_id}",
                        now=moment,
                    )
                    if comparison.event_ids:
                        for event_id in comparison.event_ids:
                            owner_snapshot = beacon.current(run.beacon_id)
                            if owner_snapshot.account_id is None:
                                raise RuntimeError("Beacon owner account is missing")
                            session.commit()
                            composition.ingest_scan_notification(
                                session,
                                account_id=owner_snapshot.account_id,
                                beacon_id=run.beacon_id,
                                run_id=run.run_id,
                                listing_keys=comparison.new_listing_keys,
                                event_id=event_id,
                                now=moment,
                            )
                    emit_process_observation(
                        {
                            "record_type": "worker_terminal",
                            "work_item_id": str(claim.work_item_id),
                            "run_id": str(run.run_id),
                            "terminal_state": (
                                "SUCCEEDED_DIFFERENCE"
                                if comparison.new_listing_keys
                                else "SUCCEEDED_BASELINE"
                            ),
                            "new_listing_count": len(comparison.new_listing_keys),
                            "event_ids": [str(event_id) for event_id in comparison.event_ids],
                        }
                    )
                else:
                    terminal_state = record_parser_outcome(
                        repo, run, persisted.outcome_id, parser, now=moment
                    )
                    emit_process_observation(
                        {
                            "record_type": "worker_terminal",
                            "work_item_id": str(claim.work_item_id),
                            "run_id": str(run.run_id),
                            "terminal_state": terminal_state,
                            "parser_outcome": persisted.outcome_code,
                            "new_listing_count": 0,
                            "event_ids": [],
                        }
                    )
                processed += 1
            except Exception:
                LOGGER.exception("worker failed work_item=%s", claim.work_item_id)
    if processed:
        def fake_provider(_attempt: AttemptLease) -> FakeProviderOutcome:
            return FakeProviderOutcome(
                outcome_reference_id="rf24-fake-telegram-accepted",
                outcome_class=NotificationProviderOutcomeClass.PROVIDER_ACCEPTED,
                provider_safe_delivery_reference="rf24-fake-telegram-delivery",
                reason_code="rf24-provider-disabled",
            )

        run_worker_cycle(
            composition.sessions,
            cast(Any, fake_provider),
            now=moment,
            limit=composition.settings.worker.batch_size,
            lease_seconds=composition.settings.worker.lease_seconds,
        )
    return processed


def main() -> None:
    settings = load_runtime_settings()
    if settings.runtime.process_kind.value != "mayak-worker":
        raise RuntimeError("invalid process kind")
    logging.basicConfig(level=settings.observability.log_level.value, force=True)
    shutdown = Shutdown()
    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)
    composition = build_rf24_composition(settings)
    try:
        while not shutdown.requested:
            process_once(composition)
            deadline = time.monotonic() + min(settings.worker.poll_interval_seconds, 30)
            while not shutdown.requested and time.monotonic() < deadline:
                time.sleep(min(0.25, max(0.0, deadline - time.monotonic())))
    finally:
        composition.close()
        LOGGER.info("worker process stopped")


if __name__ == "__main__":
    main()


__all__ = ["main", "process_once"]
