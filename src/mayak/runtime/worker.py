# ruff: noqa: E501
"""Production-shaped durable Scan worker process for Module 06."""

from __future__ import annotations

import logging
import os
import signal
import time
from datetime import UTC, datetime
from types import FrameType
from typing import Any, cast
from uuid import UUID, uuid4

from sqlalchemy import func, select

from mayak.modules.avito_parser_adapter.contracts import (
    ParserOutcomeStatus,
    TransportOutcomeReference,
    TransportOutcomeStatus,
)
from mayak.modules.avito_parser_adapter.runtime import NormalizedListingSnapshot
from mayak.modules.egress_routing.simulator import EgressAgentSimulator, SimulatorScenario
from mayak.modules.notification_delivery.attempt import NotificationProviderOutcomeClass
from mayak.modules.notification_delivery.runtime import (
    AttemptLease,
    FakeProviderOutcome,
    run_worker_cycle,
)
from mayak.modules.scan_orchestration.contracts import AccessTier, DecisionStatus
from mayak.modules.scan_orchestration.services import (
    claim_work,
    commit_comparison,
    record_parser_outcome,
    start_run,
    validate_cadence,
)
from mayak.persistence.metadata import metadata
from mayak.platform.observability import configure_logging, emit
from mayak.runtime.rf24_composition import RF24RuntimeComposition, build_rf24_composition
from mayak.runtime.rf24_provenance import _authorized_technical_id, emit_process_observation
from mayak.runtime.settings import load_runtime_settings

LOGGER = logging.getLogger("mayak.worker")
_RF24_SHUTDOWN_REQUESTED = False


class Shutdown:
    requested = False

    def __call__(self, _signum: int, _frame: FrameType | None) -> None:
        global _RF24_SHUTDOWN_REQUESTED
        self.requested = True
        _RF24_SHUTDOWN_REQUESTED = True


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
    if _rf24_hook_enabled() and os.environ.get("RF24_FORCE_COMPLETE_SAME_LISTING") == "true":
        return "usable_listing_page"
    if value in {"usable_listing_page", "usable_listing_page_with_new_listing"}:
        runs = metadata.tables["mayak.scan_runs"]
        prior = session.execute(
            select(func.count()).select_from(runs).where(runs.c.beacon_id == beacon_id)
        ).scalar_one()
        return "usable_listing_page" if prior <= 1 else "usable_listing_page_with_new_listing"
    return value if value in allowed else "usable_listing_page"


def _rf24_hook_enabled() -> bool:
    return (
        os.environ.get("MAYAK_RUNTIME_PROFILE") == "synthetic_acceptance"
        and os.environ.get("MAYAK_SYNTHETIC_SCENARIO_RUN_ID")
        == os.environ.get("MAYAK_ENVIRONMENT_ID")
        and os.environ.get("RF24_ACCEPTANCE_HOOKS_ENABLED") == "true"
        and _authorized_technical_id() is not None
    )


def _rf24_wait_for_release() -> None:
    """Bounded acceptance control; no production/default runtime path reads it."""
    if not _rf24_hook_enabled():
        return
    configured = os.environ.get("RF24_ACCEPTANCE_CONTROL_FILE")
    if not configured or len(configured) > 240 or not os.path.isabs(configured):
        raise RuntimeError("RF24 acceptance control file is missing or unsafe")
    deadline = time.monotonic() + 90
    while time.monotonic() < deadline:
        if _RF24_SHUTDOWN_REQUESTED:
            raise InterruptedError("worker shutdown requested during RF24 hold")
        try:
            with open(configured, encoding="utf-8") as control:
                if control.read(32).strip() == "release":
                    return
        except FileNotFoundError:
            pass
        time.sleep(0.1)
    raise TimeoutError("RF24 acceptance control release timed out")


def process_once(
    composition: RF24RuntimeComposition, *, now: datetime | None = None
) -> int:
    moment = now or datetime.now(UTC)
    with composition.sessions() as session:
        repo = composition.scan_repository(session)
        target_work_item_id = None
        if _rf24_hook_enabled() and os.environ.get("RF24_TARGET_WORK_ITEM_ID"):
            target_work_item_id = UUID(os.environ["RF24_TARGET_WORK_ITEM_ID"])
        claims = claim_work(
            repo,
            moment,
            composition.settings.worker.batch_size,
            composition.settings.worker.lease_seconds,
            reclaim_pending=_rf24_hook_enabled()
            and os.environ.get("RF24_RECLAIM_PENDING") == "true",
            target_work_item_id=target_work_item_id,
        )
        processed = 0
        emit(LOGGER, operation="worker.claim", outcome="success", reason_code="CLAIM_COMPLETED", work_item_id=str(claims[0].work_item_id) if claims else None, claim_count=len(claims))
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
            if _rf24_hook_enabled() and os.environ.get("RF24_RECLAIM_PENDING") == "true":
                emit_process_observation(
                    {
                        "record_type": "worker_reclaim",
                        "work_item_id": str(claim.work_item_id),
                        "reclaim_owner": os.environ.get("RF24_PROCESS_GENERATION", "unknown"),
                    }
                )
            if _rf24_hook_enabled() and os.environ.get("RF24_HOLD_AFTER_CLAIM") == "true":
                emit_process_observation(
                    {
                        "record_type": "worker_controlled_hold",
                        "work_item_id": str(claim.work_item_id),
                    }
                )
                while not os.environ.get("RF24_RELEASE_HOLD") == "true":
                    if _RF24_SHUTDOWN_REQUESTED:
                        raise InterruptedError("worker shutdown requested during RF24 claim hold")
                    time.sleep(0.1)
            run: Any = None
            try:
                beacon = composition.scan_beacon(session)
                current = beacon.current(claim.beacon_id)
                entitlement = composition.scan_entitlement(session, at=moment)
                decision = entitlement.current(claim.beacon_id, current.account_id)
                interval = 300 if decision.tier is AccessTier.BASIC else 10_800
                eligible = (
                    current.lifecycle_eligible
                    and decision.status is DecisionStatus.ALLOWED
                )
                if eligible:
                    try:
                        validate_cadence(decision, interval)
                    except Exception:
                        eligible = False
                if not eligible:
                    composition.scan_repository(session).block_claim_before_external_work(
                        claim.work_item_id, claim.lease_token, moment
                    )
                    session.commit()
                    emit_process_observation(
                        {
                            "record_type": "worker_pre_provider_block",
                            "work_item_id": str(claim.work_item_id),
                            "reason": "OWNER_ACCESS_OR_LIFECYCLE_DENIED",
                            "parser_calls": 0,
                            "egress_calls": 0,
                            "notification_provider_calls": 0,
                        }
                    )
                    continue
                session.commit()
                run = start_run(repo, claim, beacon, now=moment)
                LOGGER.info(
                    "worker claim work_item_id=%s schedule_id=%s run_id=%s",
                    claim.work_item_id, claim.schedule_id, run.run_id,
                )
                scenario = _scenario(session, run.beacon_id)
                session.commit()
                if _rf24_hook_enabled() and os.environ.get("RF24_HOLD_AFTER_START_RUN") == "true":
                    emit_process_observation(
                        {
                            "record_type": "worker_controlled_hold",
                            "hold_stage": "post_start_run",
                            "work_item_id": str(claim.work_item_id),
                            "run_id": str(run.run_id),
                        }
                    )
                    _rf24_wait_for_release()
                egress_observation: dict[str, object] | None = None
                if scenario == "route_failure":
                    # Exercise the accepted Egress simulator boundary and feed
                    # its classified transport result through Parser's public
                    # integration port.  No route credential or payload crosses
                    # this observation seam.
                    request = composition.parser.run_synthetic(
                        "usable_listing_page", request_id=f"rf24::{run.run_id}"
                    ).attempt.request_envelope
                    if request is None:
                        raise RuntimeError("synthetic Egress request envelope is missing")
                    simulator = EgressAgentSimulator(uuid4())
                    receipt = simulator.run(SimulatorScenario.ACCEPTED_ASSIGNMENT)
                    failed = simulator.run(SimulatorScenario.FAILURE)
                    transport = TransportOutcomeReference(
                        transport_reference_id=f"egress::{failed.correlation_id}",
                        transport_status=TransportOutcomeStatus.TRANSPORT_UNAVAILABLE,
                        request_reference=f"request::{run.run_id}",
                        route_reference=f"route::{receipt.assignment_id}",
                        notes=("synthetic acceptance route failure",),
                    )
                    synthetic_attempt = composition.parser.consume_egress_transport(
                        request, transport
                    )
                    synthetic = type("SyntheticEgressResult", (), {
                        "attempt": synthetic_attempt,
                        "page": None,
                    })()
                    egress_observation = {
                        "record_type": "egress_route_failure",
                        "work_item_id": str(claim.work_item_id),
                        "run_id": str(run.run_id),
                        "route_selection": "accepted_assignment",
                        "assignment_id": str(receipt.assignment_id),
                        "transport_reference_id": transport.transport_reference_id,
                        "outcome": transport.transport_status.value,
                        "parser_correlation": synthetic_attempt.attempt_id,
                    }
                    emit_process_observation(egress_observation)
                else:
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
                    if (
                        _rf24_hook_enabled()
                        and os.environ.get("RF24_STALE_ATTEMPT_EXPECTED") == "true"
                    ):
                        emit_process_observation(
                            {
                                "record_type": "stale_terminal_attempt",
                                "work_item_id": str(claim.work_item_id),
                                "run_id": str(run.run_id),
                                "terminal_operation": "commit_comparison",
                            }
                        )
                    comparison = commit_comparison(
                        repo,
                        run,
                        persisted.outcome_id,
                        beacon,
                        composition.scan_entitlement(session, at=moment),
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
                                "SUCCEEDED_BASELINE"
                                if comparison.baseline_established
                                else "SUCCEEDED_DIFFERENCE"
                            ),
                            "new_listing_count": len(comparison.new_listing_keys),
                            "event_ids": [str(event_id) for event_id in comparison.event_ids],
                            "parser_attempt_id": (
                                None if egress_observation is None
                                else egress_observation["parser_correlation"]
                            ),
                        }
                    )
                else:
                    if (
                        _rf24_hook_enabled()
                        and os.environ.get("RF24_STALE_ATTEMPT_EXPECTED") == "true"
                    ):
                        emit_process_observation(
                            {
                                "record_type": "stale_terminal_attempt",
                                "work_item_id": str(claim.work_item_id),
                                "run_id": str(run.run_id),
                                "terminal_operation": "record_parser_outcome",
                            }
                        )
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
                            "parser_attempt_id": (
                                None if egress_observation is None
                                else egress_observation["parser_correlation"]
                            ),
                        }
                    )
                processed += 1
            except Exception as exc:
                if (
                    _rf24_hook_enabled()
                    and os.environ.get("RF24_STALE_ATTEMPT_EXPECTED") == "true"
                ):
                    emit_process_observation(
                        {
                            "record_type": "stale_terminal_rejected",
                            "work_item_id": str(claim.work_item_id),
                            "run_id": str(run.run_id) if run is not None else None,
                            "rejection_class": type(exc).__name__,
                        }
                    )
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
    configure_logging(settings.observability.log_level.value)
    shutdown = Shutdown()
    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)
    emit(LOGGER, operation="process.start", outcome="success", reason_code="PROCESS_STARTED")
    emit_process_observation({"record_type": "worker_process_started"})
    composition = build_rf24_composition(settings)
    try:
        while not shutdown.requested:
            process_once(composition)
            deadline = time.monotonic() + min(settings.worker.poll_interval_seconds, 30)
            while not shutdown.requested and time.monotonic() < deadline:
                time.sleep(min(0.25, max(0.0, deadline - time.monotonic())))
    finally:
        emit_process_observation({"record_type": "worker_process_stopped"})
        composition.close()
        emit(LOGGER, operation="process.stop", outcome="success", reason_code="PROCESS_STOPPED")


if __name__ == "__main__":
    main()


__all__ = ["main", "process_once"]
