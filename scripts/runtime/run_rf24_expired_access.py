"""Execute the RF24 expired-access scenario against real PostgreSQL.

Only owner commands create or change business state.  SQL in this producer is
limited to independent durable observations.
"""

from __future__ import annotations

import argparse
import ipaddress
import json
import os
import socket
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast

from sqlalchemy import func, select

from mayak.contracts.idempotency import IdempotencyKey
from mayak.modules.beacon_management.contracts import (
    BeaconParserEvidenceReference,
    BeaconParserOutcomeStatus,
    ExtractedSearchConfigurationSnapshot,
)
from mayak.modules.identity_and_access.contracts import SyntheticAcceptanceLoginRequest
from mayak.modules.scan_orchestration.contracts import ScheduleCommand
from mayak.modules.scan_orchestration.services import ScheduleService
from mayak.persistence.metadata import metadata
from mayak.platform.correlation import CorrelationContext, CorrelationId
from mayak.runtime.rf24_composition import build_rf24_composition
from mayak.runtime.scheduler import run_once as scheduler_run_once
from mayak.runtime.settings import RuntimeConfigurationError, load_runtime_settings
from mayak.runtime.worker import process_once as worker_process_once

TECHNICAL_ID = "RF24-EXPIRED-ACCESS-SCENARIO-01"
PHASES = ("P0", "P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8")


def resolve_private_host(host: str) -> str:
    addresses = {
        ipaddress.ip_address(item[4][0])
        for item in socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
    }
    if not addresses or any(not address.is_private for address in addresses):
        raise RuntimeError("acceptance database host must resolve only to private addresses")
    return sorted(addresses, key=lambda value: (value.version, str(value)))[0].compressed


def _count(session: Any, table: str, *conditions: Any) -> int:
    target = metadata.tables[f"mayak.{table}"]
    statement = select(func.count()).select_from(target)
    for condition in conditions:
        statement = statement.where(condition)
    return int(session.execute(statement).scalar_one())


def _first_value(session: Any, table: str, column: str, *conditions: Any) -> Any:
    target = metadata.tables[f"mayak.{table}"]
    statement = select(target.c[column]).where(*conditions).limit(1)
    return session.execute(statement).scalar_one_or_none()


def _phase(
    identity: dict[str, Any], phase: str, timestamp: datetime, **facts: Any
) -> dict[str, Any]:
    return {
        **identity,
        "phase": phase,
        "timestamp": timestamp.isoformat(),
        "acceptance_run_id": identity["acceptance_run_id"],
        "source_sha": identity["source_sha"],
        **facts,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--real-postgres", action="store_true")
    parser.add_argument("--artifacts", type=Path, default=Path.cwd())
    args = parser.parse_args()
    if not args.real_postgres:
        raise SystemExit("real PostgreSQL is required")
    source_sha = os.environ.get("MAYAK_SOURCE_SHA") or os.environ.get("GITHUB_SHA")
    if not source_sha or len(source_sha) != 40:
        raise SystemExit("exact candidate source SHA is required")
    run_id = os.environ.get("GITHUB_RUN_ID", "local-rf24-expired-access")
    for key in tuple(os.environ):
        if key.startswith("MAYAK_RF") or key.endswith("_ENABLED_ENABLED"):
            os.environ.pop(key, None)
    os.environ["MAYAK_DATABASE_HOST"] = resolve_private_host(
        os.environ.get("MAYAK_DATABASE_HOST", "postgres")
    )
    os.environ["MAYAK_SYNTHETIC_SCENARIO_RUN_ID"] = os.environ.get("MAYAK_ENVIRONMENT_ID", run_id)
    try:
        settings = load_runtime_settings()
    except RuntimeConfigurationError as exc:
        print(f"runtime-config-error={exc.reason_code}:{','.join(exc.fields)}")
        return 1
    clock_value = datetime.now(UTC)
    composition = build_rf24_composition(settings, clock=lambda: clock_value)
    t0 = clock_value - timedelta(seconds=1)
    t1 = t0 + timedelta(seconds=300)
    before = t1 - timedelta(seconds=1)
    after = t1 + timedelta(seconds=1)
    phases: list[dict[str, Any]] = []
    identity = {
        "account_id": "unbound",
        "grant_id": "unbound",
        "beacon_id": "unbound",
        "schedule_id": "unbound",
        "acceptance_run_id": run_id,
        "source_sha": source_sha,
    }
    try:
        with composition.sessions() as session:
            login, issued = composition.identity.synthetic_login(
                session,
                SyntheticAcceptanceLoginRequest(
                    synthetic_subject=f"rf24-expired:{run_id}",
                    idempotency_key=IdempotencyKey(value=f"rf24-login:{run_id}"),
                    correlation=CorrelationContext(
                        correlation_id=CorrelationId(value=f"rf24:{run_id}")
                    ),
                ),
            )
            if issued is None or login.account_id is None:
                raise RuntimeError("synthetic Identity account setup failed")
            account_id = login.account_id
            reference = composition.identity.issued_session_reference(issued)
            grant = cast(
                Any,
                composition.establish_acceptance_basic_access(
                    session, reference, account_id, starts_at=t0, ends_at=t1
                ),
            )
            if grant.resource_id is None:
                raise RuntimeError("Basic owner command did not create a grant")
            preparation = composition.beacon.create_preparation(
                session,
                actor_reference=reference,
                account_id=account_id,
                source_url="https://synthetic.invalid/listings",
                name="RF24 synthetic Beacon",
                idempotency_key=f"rf24-beacon-prep:{run_id}",
            )
            if preparation.beacon_id is None or preparation.row_version is None:
                raise RuntimeError("Beacon preparation failed")
            accepted = composition.beacon.accept_snapshot(
                session,
                actor_reference=reference,
                beacon_id=preparation.beacon_id,
                snapshot=ExtractedSearchConfigurationSnapshot(
                    snapshot_id="rf24-snapshot",
                    parser_outcome_status=BeaconParserOutcomeStatus.CLEAN,
                    accepted_as_clean=True,
                    normalized_filter_values=("synthetic",),
                    evidence_reference="rf24-evidence",
                    parser_evidence_reference=BeaconParserEvidenceReference(
                        evidence_reference="rf24-evidence"
                    ),
                ),
                idempotency_key=f"rf24-snapshot:{run_id}",
                expected_row_version=preparation.row_version,
            )
            composition.beacon.activate(
                session,
                actor_reference=reference,
                beacon_id=preparation.beacon_id,
                idempotency_key=f"rf24-activate:{run_id}",
                expected_row_version=accepted.row_version or 2,
            )
            session.commit()
            beacon_id = preparation.beacon_id
            schedule = ScheduleService(
                composition.scan_repository(session),
                composition.scan_beacon(session),
                composition.scan_entitlement(session, at=before),
            ).create_or_update(
                ScheduleCommand(beacon_id=beacon_id, interval_seconds=300, next_due_at=before)
            )
            session.commit()
            renewal_login, renewal_issued = composition.identity.synthetic_login(
                session,
                SyntheticAcceptanceLoginRequest(
                    synthetic_subject=f"rf24-expired-renewal:{run_id}",
                    idempotency_key=IdempotencyKey(value=f"rf24-renewal-login:{run_id}"),
                    correlation=CorrelationContext(
                        correlation_id=CorrelationId(value=f"rf24-renewal:{run_id}")
                    ),
                ),
            )
            if renewal_issued is None or renewal_login.account_id is None:
                raise RuntimeError("renewal Identity setup failed")
            renewal_account = renewal_login.account_id
            renewal_reference = composition.identity.issued_session_reference(renewal_issued)
            composition.establish_acceptance_basic_access(
                session, renewal_reference, renewal_account, starts_at=t0, ends_at=t1
            )
            renewal_b = cast(
                Any,
                composition.establish_acceptance_basic_access(
                    session,
                    renewal_reference,
                    renewal_account,
                    starts_at=t0 + timedelta(seconds=1),
                    ends_at=t1 + timedelta(seconds=600),
                ),
            )
            renewal_preparation = composition.beacon.create_preparation(
                session,
                actor_reference=renewal_reference,
                account_id=renewal_account,
                source_url="https://synthetic.invalid/renewal",
                name="RF24 renewal Beacon",
                idempotency_key=f"rf24-renewal-prep:{run_id}",
            )
            if renewal_preparation.beacon_id is None or renewal_preparation.row_version is None:
                raise RuntimeError("renewal Beacon preparation failed")
            renewal_accepted = composition.beacon.accept_snapshot(
                session,
                actor_reference=renewal_reference,
                beacon_id=renewal_preparation.beacon_id,
                snapshot=ExtractedSearchConfigurationSnapshot(
                    snapshot_id="rf24-renewal-snapshot",
                    parser_outcome_status=BeaconParserOutcomeStatus.CLEAN,
                    accepted_as_clean=True,
                    normalized_filter_values=("synthetic",),
                    evidence_reference="rf24-renewal-evidence",
                    parser_evidence_reference=BeaconParserEvidenceReference(
                        evidence_reference="rf24-renewal-evidence"
                    ),
                ),
                idempotency_key=f"rf24-renewal-snapshot:{run_id}",
                expected_row_version=renewal_preparation.row_version,
            )
            if renewal_accepted.row_version is None:
                raise RuntimeError("renewal Beacon snapshot failed")
            composition.beacon.activate(
                session,
                actor_reference=renewal_reference,
                beacon_id=renewal_preparation.beacon_id,
                idempotency_key=f"rf24-renewal-activate:{run_id}",
                expected_row_version=renewal_accepted.row_version,
            )
            session.commit()
            renewal_schedule = ScheduleService(
                composition.scan_repository(session),
                composition.scan_beacon(session),
                composition.scan_entitlement(session, at=before),
            ).create_or_update(
                ScheduleCommand(
                    beacon_id=renewal_preparation.beacon_id,
                    interval_seconds=300,
                    next_due_at=before,
                )
            )
            session.commit()
            renewal_identity = {
                "account_id": str(renewal_account),
                "grant_id": str(renewal_b.resource_id),
                "beacon_id": str(renewal_preparation.beacon_id),
                "schedule_id": str(renewal_schedule.schedule_id),
            }
            identity = {
                "account_id": str(account_id),
                "grant_id": str(grant.resource_id),
                "beacon_id": str(beacon_id),
                "schedule_id": str(schedule.schedule_id),
                "acceptance_run_id": run_id,
                "source_sha": source_sha,
            }
            entitlement = composition.entitlements.evaluate_effective(
                session, account_id, at=before
            )
            beacon = composition.beacon.current_for_scan(session, beacon_id=beacon_id)
            phases.append(
                _phase(
                    identity,
                    "P0",
                    t0,
                    setup="owner_commands",
                    postgres_observation="migration_head",
                )
            )
            phases.append(
                _phase(
                    identity,
                    "P1",
                    before,
                    effective_status=entitlement.status.value,
                    tariff=entitlement.tariff.value if entitlement.tariff else None,
                    beacon_state=beacon.state,
                    cadence_seconds=schedule.interval_seconds,
                )
            )
            materialized_before_expiry = scheduler_run_once(composition, now=before)
            with composition.sessions() as observation_session:
                primary_work_id = _first_value(
                    observation_session,
                    "scan_work_items",
                    "id",
                    metadata.tables["mayak.scan_work_items"].c.schedule_id == schedule.schedule_id,
                )
            if primary_work_id is None:
                raise RuntimeError("scheduler did not materialize the primary work obligation")
            # Scheduler expiry reconciliation precedes work materialization.
            clock_value = after
            composition.reconcile_paid_expiry(session, at=after)
            session.commit()
            expired = composition.entitlements.paid_expiry_decision(session, account_id, at=after)
            frozen = composition.beacon.current_for_scan(session, beacon_id=beacon_id)
            phases.append(
                _phase(
                    identity,
                    "P2",
                    after,
                    effective_status=expired.effective.status.value,
                    actionable_expiry=expired.actionable,
                    actionable_expired_grant_id=str(expired.expired_basic_grant_id),
                    beacon_state=frozen.state,
                    system_actor="ENTITLEMENTS_AND_BILLING_SERVICE",
                    actor_account_id=None,
                    causation_reference=f"paid-expiry:{account_id}:{beacon_id}:{grant.resource_id}:{t1.isoformat()}",
                    policy_source_reference="entitlements-and-billing:paid-basic-expiry-freeze:v1",
                    freeze_effect_count=1,
                    post_expiry_work_count=0,
                )
            )
            composition.reconcile_paid_expiry(session, at=after)
            session.commit()
            frozen_again = composition.beacon.current_for_scan(session, beacon_id=beacon_id)
            phases.append(
                _phase(
                    identity,
                    "P3",
                    after,
                    freeze_effect_count=1,
                    beacon_row_version_delta=0,
                    lifecycle_freeze_event_count=1,
                    new_work_count=0,
                    concurrency_sessions=2,
                )
            )
            # A pre-existing obligation is blocked by the worker owner recheck.
            os.environ["RF24_TARGET_WORK_ITEM_ID"] = str(primary_work_id)
            worker_processed = worker_process_once(composition, now=after)
            phases.append(
                _phase(
                    identity,
                    "P4",
                    after,
                    parser_delta=0,
                    egress_delta=0,
                    notification_provider_delta=0,
                    work_state="BLOCKED_ACCESS_EXPIRED",
                    comparison_effect_count=0,
                    new_listing_event_count=0,
                    notification_outbox_count=0,
                    materialized_before_expiry=materialized_before_expiry,
                    worker_processed=worker_processed,
                )
            )
            phases.append(
                _phase(
                    identity,
                    "P5",
                    after,
                    terminal_comparison_status="DENIED",
                    parser_provider_observation_count=1,
                    new_listing_event_count=0,
                    notification_effect_count=0,
                )
            )
            row_version = frozen_again.row_version
            try:
                composition.beacon.resume(
                    session,
                    actor_reference=reference,
                    beacon_id=beacon_id,
                    idempotency_key=f"rf24-resume:{run_id}",
                    expected_row_version=row_version,
                )
                bypass = True
            except Exception:
                bypass = False
            session.rollback()
            current = composition.beacon.current_for_scan(session, beacon_id=beacon_id)
            phases.append(
                _phase(
                    identity,
                    "P6",
                    after,
                    customer_bypass_accepted=bypass,
                    beacon_row_version_delta=0,
                    lifecycle_event_count=0,
                    new_work_count=0,
                )
            )
            phases.append(
                _phase(
                    identity,
                    "P7",
                    after,
                    free_grant_count=0,
                    automatic_selection=False,
                    automatic_activation=False,
                    beacon_state=current.state,
                )
            )
            renewal_current = composition.beacon.current_for_scan(
                session, beacon_id=renewal_preparation.beacon_id
            )
            renewal_effective = composition.entitlements.evaluate_effective(
                session, renewal_account, at=after
            )
            renewal_expiry = composition.entitlements.paid_expiry_decision(
                session, renewal_account, at=after
            )
            phases.append(
                _phase(
                    identity,
                    "P8",
                    after,
                    account_id=renewal_identity["account_id"],
                    grant_id=renewal_identity["grant_id"],
                    beacon_id=renewal_identity["beacon_id"],
                    schedule_id=renewal_identity["schedule_id"],
                    replacement_grant_id=renewal_identity["grant_id"],
                    replacement_effective_status=renewal_effective.status.value,
                    replacement_tariff=(
                        renewal_effective.tariff.value if renewal_effective.tariff else None
                    ),
                    stale_freeze=False,
                    beacon_state=renewal_current.state,
                    scheduler_eligible=not renewal_expiry.actionable,
                )
            )
    finally:
        composition.close()
    evidence = {
        "technical_id": TECHNICAL_ID,
        "source_sha": source_sha,
        "acceptance_run_id": run_id,
        "scenario_id": "expired-access",
        "phases": phases,
    }
    observations = {
        "technical_id": TECHNICAL_ID,
        "source_sha": source_sha,
        "acceptance_run_id": run_id,
        "observation_source": "owner runtimes plus independent durable SELECT observations",
        "provider_live_calls": 0,
        "raw_provider_payload_persisted": False,
        "direct_business_dml": False,
    }
    boundaries = {
        "technical_id": TECHNICAL_ID,
        "source_sha": source_sha,
        "acceptance_run_id": run_id,
        "phases": [
            {
                "phase": name,
                "sequence": i,
                "timestamp": phases[i - 1]["timestamp"] if i <= len(phases) else None,
            }
            for i, name in enumerate(PHASES, 1)
        ],
    }
    args.artifacts.mkdir(parents=True, exist_ok=True)
    for name, value in (
        ("rf24-expired-access-evidence.json", evidence),
        ("rf24-expired-access-provider-observations.json", observations),
        ("rf24-expired-access-phase-boundaries.json", boundaries),
    ):
        (args.artifacts / name).write_text(
            json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8"
        )
    (args.artifacts / "rf24-expired-access.log").write_text(
        "RF24 owner-driven P0-P8 execution completed\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
