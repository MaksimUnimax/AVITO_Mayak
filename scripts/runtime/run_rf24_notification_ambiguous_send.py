"""Run the RF24 Notification ambiguous-send acceptance on real PostgreSQL."""

from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import os
import socket
import subprocess
import sys
import time
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import cast
from uuid import UUID, uuid4, uuid5

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from mayak.modules.notification_delivery.attempt import NotificationProviderOutcomeClass
from mayak.modules.notification_delivery.delivery_plan import (
    NotificationDeliveryPlanDecision,
    plan_notification_delivery,
)
from mayak.modules.notification_delivery.eligibility import (
    NotificationBeaconLifecycleStatus,
    NotificationChannelClass,
    NotificationChannelEligibilityEvidence,
    NotificationEligibilityContext,
    NotificationEligibilityDecision,
    NotificationEntitlementStatus,
    NotificationRecoveryGraceEvidence,
    evaluate_notification_eligibility,
)
from mayak.modules.notification_delivery.outbox import create_notification_outbox_item
from mayak.modules.notification_delivery.runtime import (
    AttemptLease,
    EndpointEligibility,
    FakeProviderOutcome,
    ReconciliationDisposition,
    TrustedReconciliationEvidence,
    fanout_event,
    ingest_source,
    register_endpoint,
    resolve_reconciliation,
    run_worker_cycle,
)
from mayak.modules.notification_delivery.source_intake import (
    NotificationSourceEvent,
    NotificationSourceFamily,
    NotificationSourceProducer,
    evaluate_notification_source_intake,
)
from mayak.platform.idempotency import IdempotencyFingerprint, IdempotencyKey, IdempotencyScope
from mayak.runtime.settings import compose_runtime_settings

TECHNICAL_ID = "RF24-NOTIFICATION-AMBIGUOUS-SEND-SCENARIO-01"


def sha(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def resolve_acceptance_database_host(host: str) -> str:
    """Convert a private service alias to one deterministic private literal."""
    try:
        addresses = {
            ipaddress.ip_address(item[4][0])
            for item in socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
        }
    except (OSError, ValueError) as exc:
        raise RuntimeError("database host resolution failed") from exc
    if not addresses or any(not address.is_private for address in addresses):
        raise RuntimeError("database host did not resolve only to private addresses")
    return sorted(addresses, key=lambda address: (address.version, str(address)))[0].compressed


def _child_environment(
    parent: Mapping[str, str], source_sha: str, run_id: str, kind: str
) -> dict[str, str]:
    """Build the small, explicit MAYAK environment accepted by child settings."""
    database_host = resolve_acceptance_database_host(parent.get("MAYAK_DATABASE_HOST", "postgres"))
    values = {
        "MAYAK_RUNTIME_PROFILE": "synthetic_acceptance",
        "MAYAK_ENVIRONMENT_ID": run_id,
        "MAYAK_SOURCE_SHA": source_sha,
        "MAYAK_LOCK_IDENTITY": "0" * 64,
        "MAYAK_IMAGE_DIGEST": "sha256:" + "0" * 64,
        "MAYAK_PROCESS_KIND": kind,
        "MAYAK_DATABASE_HOST": database_host,
        "MAYAK_DATABASE_PORT": parent.get("MAYAK_DATABASE_PORT", "5432"),
        "MAYAK_DATABASE_NAME": parent.get("MAYAK_DATABASE_NAME", "mayak"),
        "MAYAK_DATABASE_APPLICATION_USER": parent.get(
            "MAYAK_DATABASE_APPLICATION_USER", "mayak_application"
        ),
        "MAYAK_DATABASE_MIGRATION_USER": parent.get(
            "MAYAK_DATABASE_MIGRATION_USER", "mayak_migration"
        ),
        "MAYAK_SECRETS_DIR": parent.get("MAYAK_SECRETS_DIR", "/run/secrets"),
        "MAYAK_API_BIND_HOST": "127.0.0.1",
        "MAYAK_API_INTERNAL_PORT": parent.get("MAYAK_API_INTERNAL_PORT", "18080"),
        "MAYAK_API_HOST_PORT": "disabled",
        "MAYAK_SYNTHETIC_IDENTITY_ENABLED": "true",
        "MAYAK_IDENTITY_ADMIN_BOOTSTRAP_ENABLED": "true",
        "MAYAK_AVITO_LIVE_ENABLED": "false",
        "MAYAK_TELEGRAM_ENABLED": "false",
        "MAYAK_TELEGRAM_UPDATE_MODE": "disabled",
        "MAYAK_MAX_ENABLED": "false",
        "MAYAK_MAX_UPDATE_MODE": "disabled",
        "MAYAK_YOOKASSA_ENABLED": "false",
        "MAYAK_EGRESS_AGENT_ENABLED": "false",
        "MAYAK_WORKER_POLL_INTERVAL_SECONDS": "1",
        "MAYAK_WORKER_LEASE_SECONDS": "30",
        "MAYAK_SCHEDULER_POLL_INTERVAL_SECONDS": "1",
        "MAYAK_SYNTHETIC_SCENARIO": "usable_listing_page",
        "MAYAK_SYNTHETIC_SCENARIO_RUN_ID": run_id,
    }
    compose_runtime_settings(values)
    return {key: value for key, value in parent.items() if not key.startswith("MAYAK_")} | values


def _public_setup(
    engine: Engine, run_id: str, source_sha: str
) -> tuple[UUID, UUID, UUID, list[subprocess.Popen[str]]]:
    """Create foreign-module prerequisites through the accepted public API only."""
    from run_rf24_vertical_spine import _json_payload, request  # type: ignore[import-not-found]

    port = os.environ.get("MAYAK_API_INTERNAL_PORT", "18080")
    base = f"http://127.0.0.1:{port}"
    parent = dict(os.environ)
    parent["MAYAK_API_INTERNAL_PORT"] = port
    processes: list[subprocess.Popen[str]] = []
    streams: list[object] = []
    log_dir = Path(os.environ.get("RF24_PUBLIC_LOG_DIR", "/tmp"))
    log_dir.mkdir(parents=True, exist_ok=True)
    for kind in ("api", "scheduler", "worker"):
        stream = (log_dir / f"rf24-public-{kind}.log").open("w", encoding="utf-8")
        streams.append(stream)
        child_env = _child_environment(parent, source_sha, run_id, f"mayak-{kind}")
        processes.append(
            subprocess.Popen(
                (sys.executable, "-m", f"mayak.runtime.{kind}"),
                env=child_env,
                stdout=stream,
                stderr=subprocess.STDOUT,
                text=True,
            )
        )
    try:
        for _ in range(80):
            if processes[0].poll() is not None:
                raise RuntimeError(f"api exited during startup: {processes[0].poll()}")
            version = request(f"{base}/version")
            if version.status == 200:
                body = _json_payload(version.payload)
                if body.get("source_sha") != source_sha:
                    raise RuntimeError("public API reported an unexpected source SHA")
                if request(f"{base}/health/live").status == 200:
                    break
            for kind, process in zip(("scheduler", "worker"), processes[1:], strict=True):
                if process.poll() is not None:
                    raise RuntimeError(f"{kind} exited during startup: {process.poll()}")
            time.sleep(0.25)
        else:
            raise RuntimeError("public acceptance API did not become live")
        login = request(
            f"{base}/acceptance/login",
            method="POST",
            body={"synthetic_subject": f"{run_id}:target"},
            idempotency_key=f"{run_id}:login",
        )
        if login._session_cookie is None:
            raise RuntimeError("public synthetic login did not issue a session")
        cookie = login._session_cookie
        account = UUID(str(_json_payload(login.payload)["account_id"]))
        for path, body, key in (
            ("/acceptance/admin/bootstrap", None, "admin"),
            ("/acceptance/entitlement", None, "entitlement"),
        ):
            response = request(
                f"{base}{path}",
                method="POST",
                body=body,
                session_cookie=cookie,
                idempotency_key=f"{run_id}:{key}",
            )
            if response.status not in (200, 201):
                raise RuntimeError(f"public setup rejected {path}: {response.status}")
        beacon_response = request(
            f"{base}/api/v1/beacons",
            method="POST",
            body={"source_url": "https://synthetic.invalid/rf24", "name": f"{run_id}-beacon"},
            session_cookie=cookie,
            idempotency_key=f"{run_id}:beacon",
        )
        beacon_body = _json_payload(beacon_response.payload)
        if beacon_response.status not in (200, 201) or not beacon_body.get("beacon_id"):
            raise RuntimeError("public beacon setup failed")
        beacon = UUID(str(beacon_body["beacon_id"]))
        version = int(beacon_body.get("row_version", 1))
        for suffix in (
            f"/accept-synthetic-snapshot?expected_row_version={version}",
            f"/activate?expected_row_version={version + 1}",
        ):
            response = request(
                f"{base}/api/v1/beacons/{beacon}{suffix}",
                method="POST",
                session_cookie=cookie,
                idempotency_key=f"{run_id}:{suffix.split('/')[1].split('?')[0]}",
            )
            if response.status not in (200, 201):
                raise RuntimeError(f"public beacon transition failed: {response.status}")
        schedule = request(
            f"{base}/api/v1/beacons/{beacon}/scan-schedule",
            method="POST",
            body={
                "interval_seconds": 10800,
                "next_due_at": (datetime.now(UTC) - timedelta(seconds=5)).isoformat(),
            },
            session_cookie=cookie,
            idempotency_key=f"{run_id}:schedule",
        )
        if schedule.status not in (200, 201):
            raise RuntimeError("public scan schedule setup failed")
        for _ in range(80):
            with engine.connect() as connection:  # read-only observation
                result = connection.execute(
                    text(
                        "SELECT id FROM mayak.scan_runs WHERE beacon_id=:beacon "
                        "ORDER BY started_at DESC NULLS LAST, id DESC LIMIT 1"
                    ),
                    {"beacon": beacon},
                ).scalar_one_or_none()
            if result is not None:
                for kind, process in zip(("scheduler", "worker"), processes[1:], strict=True):
                    if process.poll() is not None:
                        raise RuntimeError(
                            f"{kind} exited before public setup completed: {process.poll()}"
                        )
                return account, beacon, UUID(str(result)), processes
            time.sleep(0.25)
        raise RuntimeError("public scheduler did not materialize a scan run")
    except BaseException:
        for process in processes:
            process.terminate()
        raise


def rows(
    engine: Engine, table: str, ids: Mapping[str, object] | None = None
) -> list[dict[str, object]]:
    where = " and ".join(f"{k}=:{k}" for k in (ids or {})) or "true"
    with engine.connect() as c:
        result = (
            c.execute(text(f'SELECT * FROM mayak."{table}" WHERE {where} ORDER BY id'), ids or {})
            .mappings()
            .all()
        )
    safe = []
    for row in result:
        value = {k: v for k, v in dict(row).items() if k not in {"lease_token", "payload"}}
        safe.append({k: (str(v) if isinstance(v, UUID) else v) for k, v in value.items()})
    return safe


def snapshot(
    engine: Engine, account: UUID, event_id: UUID | None = None, outbox_id: UUID | None = None
) -> dict[str, object]:
    filters = {"notification_events": {"account_id": account}}
    if event_id:
        filters["notification_events"] = {"id": event_id}
    event_rows = rows(engine, "notification_events", filters["notification_events"])
    event_ids = [r["id"] for r in event_rows]
    out = rows(engine, "notification_outbox", {"id": outbox_id} if outbox_id else None)
    if outbox_id is None and event_ids:
        out = rows(engine, "notification_outbox", {"event_id": event_ids[0]})
    out_ids = [r["id"] for r in out]
    attempts = rows(engine, "notification_delivery_attempts")
    recs = rows(engine, "notification_delivery_reconciliations")
    if out_ids:
        attempts = rows(engine, "notification_delivery_attempts", {"outbox_id": out_ids[0]})
    if attempts:
        attempt_ids = {str(item["id"]) for item in attempts}
        recs = [
            item
            for item in rows(engine, "notification_delivery_reconciliations")
            if str(item["attempt_id"]) in attempt_ids
        ]
    return {"events": event_rows, "outbox": out, "attempts": attempts, "reconciliations": recs}


def source(account: UUID, beacon: UUID, run: UUID, run_id: str) -> NotificationSourceEvent:
    key = f"rf24-ambiguous-source-{run_id}"
    fp = sha(key)
    return NotificationSourceEvent(
        source_event_id=f"event-{run_id}",
        source_family=NotificationSourceFamily.NEW_LISTINGS_FOUND,
        source_producer=NotificationSourceProducer.SCAN_ORCHESTRATION,
        source_contract="rf24.synthetic.v1",
        source_contract_version="1",
        source_fact_id=f"fact-{run_id}",
        source_committed=True,
        source_commit_reference=f"commit-{run_id}",
        account_id=str(account),
        beacon_id=str(beacon),
        scan_run_id=str(run),
        listing_count=1,
        safe_listing_reference_ids=(f"listing-{run_id}",),
        correlation_id=f"corr-{run_id}",
        causation_id=f"cause-{run_id}",
        idempotency_key=IdempotencyKey(value=key),
        idempotency_fingerprint=IdempotencyFingerprint(value=fp),
        idempotency_scope=IdempotencyScope(value="rf24.synthetic"),
        source_identity_ambiguous=False,
        contains_raw_provider_payload=False,
        service_access_gate_approved=True,
        evidence_reference_ids=(f"evidence-{run_id}",),
    )


def semantics(
    s: NotificationSourceEvent, target: str
) -> tuple[NotificationEligibilityDecision, NotificationDeliveryPlanDecision]:
    intake = evaluate_notification_source_intake(
        decision_id=f"intake-{s.source_event_id}",
        source_event=s,
        evidence_reference_ids=("rf24-intake",),
    )
    channel = NotificationChannelEligibilityEvidence(
        NotificationChannelClass.TELEGRAM, True, target, True, True, ("rf24-channel",)
    )
    web = NotificationChannelEligibilityEvidence(
        NotificationChannelClass.WEB_STATUS_READ_MODEL, True, None, False, False, ("rf24-web",)
    )
    context = NotificationEligibilityContext(
        account_id=s.account_id,
        beacon_id=s.beacon_id,
        beacon_lifecycle_status=NotificationBeaconLifecycleStatus.ACTIVE,
        beacon_lifecycle_reference_id=s.beacon_id or "none",
        entitlement_status=NotificationEntitlementStatus.ALLOWED,
        entitlement_decision_reference_id="rf24-entitlement",
        no_new_status_preference_enabled=False,
        no_new_status_frequency_minutes=None,
        channel_evidence=(channel, web),
        recovery_grace_evidence=NotificationRecoveryGraceEvidence(
            False, None, False, False, ("rf24-recovery",)
        ),
        evidence_reference_ids=("rf24-context",),
    )
    eligibility = evaluate_notification_eligibility(
        decision_id=f"eligibility-{s.source_event_id}",
        source_intake_decision=intake,
        context=context,
        evidence_reference_ids=("rf24-eligibility",),
    )
    item = create_notification_outbox_item(
        decision_id=f"outbox-{s.source_event_id}",
        outbox_item_id=f"item-{s.source_event_id}",
        outbox_contract="rf24.notification.v1",
        outbox_contract_version="1",
        eligibility_decision=eligibility,
        idempotency_key=s.idempotency_key,
        idempotency_fingerprint=s.idempotency_fingerprint,
        idempotency_scope=s.idempotency_scope,
        existing_outbox_item=None,
        evidence_reference_ids=("rf24-outbox",),
    )
    plan = plan_notification_delivery(
        decision_id=f"plan-{s.source_event_id}",
        delivery_plan_id=f"plan-{s.source_event_id}",
        outbox_creation_decision=item,
        evidence_reference_ids=("rf24-plan",),
    )
    return eligibility, plan


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--dsn", required=True)
    p.add_argument("--output", default="rf24-notification-ambiguous-send-evidence.json")
    p.add_argument("--probes", default="rf24-notification-ambiguous-send-provider-probes.json")
    p.add_argument("--log", default="rf24-notification-ambiguous-send.log")
    p.add_argument("--source-sha", required=True)
    p.add_argument("--repo-root", default=".")
    a = p.parse_args()
    os.environ["MAYAK_SOURCE_SHA"] = a.source_sha
    run_id = f"run-{uuid4().hex[:16]}"
    now = datetime.now(UTC)
    engine = create_engine(a.dsn)
    factory = sessionmaker(bind=engine)
    processes: list[subprocess.Popen[str]] = []
    try:
        account, beacon, run, processes = _public_setup(engine, run_id, a.source_sha)
    except Exception as exc:
        diagnostics = []
        for kind in ("api", "scheduler", "worker"):
            path = Path(os.environ.get("RF24_PUBLIC_LOG_DIR", "/tmp")) / f"rf24-public-{kind}.log"
            diagnostics.append(
                {
                    "process_kind": kind,
                    "log_name": path.name,
                    "log_exists": path.is_file(),
                    "log_size": path.stat().st_size if path.is_file() else 0,
                    "process_state": processes[("api", "scheduler", "worker").index(kind)].poll()
                    if len(processes) == 3
                    else None,
                }
            )
        print(
            f"RF24_PUBLIC_SETUP_FAILURE={type(exc).__name__}: {exc}\n"
            + json.dumps(diagnostics, sort_keys=True)
        )
        raise
    try:
        s = source(account, beacon, run, run_id)
        target = f"rf24-telegram-{run_id}"
        endpoint_id = uuid5(UUID("00000000-0000-0000-0000-000000000024"), target)
        with Session(engine) as db:
            event = ingest_source(db, s, now=now)
        if event is None:
            raise RuntimeError("public source semantics did not produce a Notification event")
        with Session(engine) as db:
            register_endpoint(
                db,
                EndpointEligibility(
                    endpoint_id, account, "TELEGRAM", target, NotificationChannelClass.TELEGRAM
                ),
                now=now,
            )
        elig, plan = semantics(s, target)
        with Session(engine) as db:
            outbox_id = fanout_event(
                db, event.id, (endpoint_id,), now=now, eligibility_decision=elig, delivery_plan=plan
            )[0]
        phases: dict[str, object] = {"P0": snapshot(engine, account, event.id, outbox_id)}
        probes: list[dict[str, object]] = []
        rejections: list[dict[str, object]] = []
        phase_boundaries: list[dict[str, object]] = []

        def record_boundary(phase_name: str, observed: dict[str, object]) -> None:
            attempts = cast(list[dict[str, object]], observed["attempts"])
            reconciliations = cast(list[dict[str, object]], observed["reconciliations"])
            outboxes = cast(list[dict[str, object]], observed["outbox"])
            events = cast(list[dict[str, object]], observed["events"])
            phase_boundaries.append(
                {
                    "phase_name": phase_name,
                    "sequence": len(phase_boundaries) + 1,
                    "acceptance_run_id": run_id,
                    "source_sha": a.source_sha,
                    "provider_observation_count": len(probes),
                    "event_id": str(events[0]["id"]),
                    "outbox_id": str(outboxes[0]["id"]),
                    "effect_fingerprint": str(
                        attempts[0].get(
                            "effect_fingerprint", outboxes[0].get("effect_fingerprint", "")
                        )
                        if attempts
                        else outboxes[0].get("effect_fingerprint", "")
                    ),
                    "attempt_ids": [str(item["id"]) for item in attempts],
                    "attempt_numbers": [item.get("attempt_number") for item in attempts],
                    "reconciliation_ids": [str(item["id"]) for item in reconciliations],
                    "durable_attempt_count": len(attempts),
                    "durable_reconciliation_count": len(reconciliations),
                    "outbox_state": outboxes[0].get("state") if outboxes else None,
                    "attempt_states": [item.get("state") for item in attempts],
                    "reconciliation_state": reconciliations[0].get("state")
                    if reconciliations
                    else None,
                }
            )

        record_boundary("P0", cast(dict[str, object], phases["P0"]))

        def adapter(attempt: AttemptLease) -> FakeProviderOutcome:
            outcome_class = (
                NotificationProviderOutcomeClass.DISPATCH_AMBIGUOUS
                if not probes
                else NotificationProviderOutcomeClass.PROVIDER_ACCEPTED
            )
            probes.append(
                {
                    "sequence": len(probes) + 1,
                    "acceptance_run_id": run_id,
                    "source_sha": a.source_sha,
                    "phase": "P1" if not probes else "P5",
                    "attempt_id": str(attempt.attempt_id),
                    "outbox_id": str(attempt.outbox_id),
                    "attempt_number": attempt.attempt_number,
                    "effect_fingerprint": attempt.effect_fingerprint,
                    "synthetic_outcome_class": outcome_class.value,
                }
            )
            return FakeProviderOutcome(
                f"outcome-{len(probes)}-{run_id}",
                outcome_class,
                "safe-delivery-ref"
                if outcome_class is NotificationProviderOutcomeClass.PROVIDER_ACCEPTED
                else None,
                "rf24-synthetic",
            )

        run_worker_cycle(factory, adapter, now=now, limit=1, lease_seconds=60)
        phases["P1"] = snapshot(engine, account, event.id, outbox_id)
        record_boundary("P1", cast(dict[str, object], phases["P1"]))
        run_worker_cycle(factory, adapter, now=now + timedelta(hours=1), limit=1, lease_seconds=60)
        phases["P2"] = snapshot(engine, account, event.id, outbox_id)
        record_boundary("P2", cast(dict[str, object], phases["P2"]))
        p1 = cast(dict[str, object], phases["P1"])
        p1_attempt = cast(list[dict[str, object]], p1["attempts"])[0]
        attempt_id = UUID(str(p1_attempt["id"]))
        effect = str(p1_attempt["effect_fingerprint"])
        bad: list[tuple[str, object]] = [
            ("disposition_without_typed_evidence", None),
            (
                "wrong_attempt_id",
                TrustedReconciliationEvidence(
                    uuid4(),
                    effect,
                    "rf24-wrong-attempt",
                    ReconciliationDisposition.NO_EFFECT_RETRY,
                    True,
                    ("rf24-evidence",),
                ),
            ),
            (
                "wrong_effect_fingerprint",
                TrustedReconciliationEvidence(
                    attempt_id,
                    "0" * 64,
                    "rf24-wrong-fp",
                    ReconciliationDisposition.NO_EFFECT_RETRY,
                    True,
                    ("rf24-evidence",),
                ),
            ),
            (
                "wrong_resolution_id",
                TrustedReconciliationEvidence(
                    attempt_id,
                    effect,
                    "rf24-wrong-resolution",
                    ReconciliationDisposition.NO_EFFECT_RETRY,
                    True,
                    ("rf24-evidence",),
                ),
            ),
        ]
        rejected_cases: list[dict[str, object]] = []
        for case_name, candidate in bad:
            try:
                with Session(engine) as db:
                    resolve_reconciliation(
                        db,
                        attempt_id,
                        resolution_id="caller-only",
                        evidence=candidate,  # type: ignore[arg-type]
                    )
            except Exception as exc:
                rejections.append(
                    {"case": case_name, "class": type(exc).__name__, "reason": str(exc)}
                )
            rejected_cases.append(
                {"case": case_name, "snapshot": snapshot(engine, account, event.id, outbox_id)}
            )
            record_boundary(
                f"P3:{case_name}", cast(dict[str, object], rejected_cases[-1]["snapshot"])
            )
        for case_name, constructor in (
            (
                "uncommitted_evidence",
                (
                    attempt_id,
                    effect,
                    "rf24-uncommitted",
                    ReconciliationDisposition.NO_EFFECT_RETRY,
                    False,
                    ("rf24-evidence",),
                ),
            ),
            (
                "empty_evidence_references",
                (
                    attempt_id,
                    effect,
                    "rf24-empty-refs",
                    ReconciliationDisposition.NO_EFFECT_RETRY,
                    True,
                    (),
                ),
            ),
        ):
            try:
                candidate = TrustedReconciliationEvidence(*constructor)
                with Session(engine) as db:
                    resolve_reconciliation(
                        db, attempt_id, resolution_id=str(constructor[2]), evidence=candidate
                    )
            except Exception as exc:
                rejections.append(
                    {"case": case_name, "class": type(exc).__name__, "reason": str(exc)}
                )
            rejected_cases.append(
                {"case": case_name, "snapshot": snapshot(engine, account, event.id, outbox_id)}
            )
            record_boundary(
                f"P3:{case_name}", cast(dict[str, object], rejected_cases[-1]["snapshot"])
            )
        phases["P3"] = {
            "snapshot": snapshot(engine, account, event.id, outbox_id),
            "rejections": rejections,
            "rejected_cases": rejected_cases,
        }
        trusted = TrustedReconciliationEvidence(
            attempt_id,
            effect,
            f"resolution-{run_id}",
            ReconciliationDisposition.NO_EFFECT_RETRY,
            True,
            (f"evidence-{run_id}",),
        )
        with Session(engine) as db:
            resolve_reconciliation(
                db,
                attempt_id,
                resolution_id=trusted.resolution_id,
                evidence=trusted,
                now=now + timedelta(hours=1),
            )
        phases["P4"] = snapshot(engine, account, event.id, outbox_id)
        record_boundary("P4", cast(dict[str, object], phases["P4"]))
        run_worker_cycle(factory, adapter, now=now + timedelta(hours=2), limit=1, lease_seconds=60)
        phases["P5"] = snapshot(engine, account, event.id, outbox_id)
        record_boundary("P5", cast(dict[str, object], phases["P5"]))
        evidence = {
            "technical_id": TECHNICAL_ID,
            "acceptance_run_id": run_id,
            "source_sha": a.source_sha,
            "source_idempotency_identity": s.idempotency_key.value,
            "account_id": str(account),
            "beacon_id": str(beacon),
            "event_id": str(event.id),
            "outbox_id": str(outbox_id),
            "effect_fingerprint": effect,
            "phases": phases,
            "phase_boundaries": phase_boundaries,
            "reconciliation_evidence": {
                "attempt_id": str(attempt_id),
                "effect_fingerprint": effect,
                "resolution_id": trusted.resolution_id,
                "committed": True,
                "evidence_reference_ids": list(trusted.evidence_reference_ids),
                "conclusion": trusted.conclusion.value,
            },
            "provider_live_calls": 0,
            "foreign_business_dml": [],
            "provider_replay_test": "covered by verifier/unit tests",
            "provider_different_fingerprint_test": "covered by verifier/unit tests",
        }
        Path(a.output).write_text(
            json.dumps(evidence, default=str, sort_keys=True, indent=2) + "\n"
        )
        Path(a.probes).write_text(
            json.dumps(
                {"acceptance_run_id": run_id, "source_sha": a.source_sha, "observations": probes},
                sort_keys=True,
                indent=2,
            )
            + "\n"
        )
        Path(a.log).write_text(
            f"{TECHNICAL_ID} acceptance_run_id={run_id} source_sha={a.source_sha} "
            "provider_live_calls=0\n"
        )
        print(
            json.dumps(
                {
                    "acceptance_run_id": run_id,
                    "event_id": str(event.id),
                    "outbox_id": str(outbox_id),
                    "provider_calls": len(probes),
                    "source_sha": a.source_sha,
                },
                sort_keys=True,
            )
        )
    finally:
        for process in processes:
            process.terminate()
        for process in processes:
            process.wait(timeout=10)


if __name__ == "__main__":
    main()
