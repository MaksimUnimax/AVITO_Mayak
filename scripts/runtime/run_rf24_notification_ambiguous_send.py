"""Run the RF24 Notification ambiguous-send acceptance on real PostgreSQL."""
# ruff: noqa: E501, E701, E702, E401, I001, F401
# mypy: ignore-errors
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4, uuid5

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from mayak.modules.notification_delivery.attempt import NotificationProviderOutcomeClass
from mayak.modules.notification_delivery.delivery_plan import plan_notification_delivery
from mayak.modules.notification_delivery.eligibility import (
    NotificationBeaconLifecycleStatus, NotificationChannelClass,
    NotificationChannelEligibilityEvidence, NotificationEligibilityContext,
    NotificationEntitlementStatus, NotificationRecoveryGraceEvidence,
    evaluate_notification_eligibility,
)
from mayak.modules.notification_delivery.outbox import create_notification_outbox_item
from mayak.modules.notification_delivery.runtime import (
    EndpointEligibility, FakeProviderOutcome, IdempotencyConflict,
    ReconciliationConflict, ReconciliationDisposition, TrustedReconciliationEvidence,
    commit_outcome, fanout_event, ingest_source, register_endpoint,
    resolve_reconciliation, run_worker_cycle,
)
from mayak.modules.notification_delivery.source_intake import (
    NotificationSourceEvent, NotificationSourceFamily, NotificationSourceProducer,
    evaluate_notification_source_intake,
)
from mayak.platform.idempotency import IdempotencyFingerprint, IdempotencyKey, IdempotencyScope

TABLES = ("notification_events", "notification_outbox", "notification_delivery_attempts", "notification_delivery_reconciliations")
TECHNICAL_ID = "RF24-NOTIFICATION-AMBIGUOUS-SEND-SCENARIO-01"

def sha(value: str) -> str: return hashlib.sha256(value.encode()).hexdigest()

def fixture(engine: object) -> tuple[UUID, UUID, UUID]:
    """Only establishes prerequisite synthetic scope; Notification rows use public owners."""
    account, beacon, revision, schedule, work, run = (uuid4() for _ in range(6))
    now = datetime.now(UTC)
    with engine.begin() as c:  # type: ignore[union-attr]
        c.execute(text("insert into mayak.identity_accounts(id,state,created_at,updated_at) values (:id,'ACTIVE',:n,:n)"), {"id": account, "n": now})
        c.execute(text("insert into mayak.beacon_beacons(id,account_id,name,state,created_at,updated_at,row_version) values (:id,:a,'rf24-ambiguous','ACTIVE',:n,:n,1)"), {"id": beacon, "a": account, "n": now})
        c.execute(text("insert into mayak.beacon_configuration_revisions(beacon_id,revision_no,source_url,accepted_filter,created_by_account_id,created_at,revision_id,snapshot_id,parser_outcome_status,accepted_as_clean,parser_evidence_reference,unsupported_parameters,warning_codes) values (:b,1,'synthetic-source','{}',:a,:n,:r,'rf24-snapshot','CLEAN',true,'rf24-evidence','[]','[]')"), {"b": beacon, "a": account, "n": now, "r": revision})
        c.execute(text("update mayak.beacon_beacons set current_revision_no=1,current_revision_id=:r where id=:b"), {"r": revision, "b": beacon})
        c.execute(text("insert into mayak.scan_schedules(id,beacon_id,interval_seconds,next_due_at,state,created_at,updated_at,row_version) values (:id,:b,300,:n,'ACTIVE',:n,:n,1)"), {"id": schedule, "b": beacon, "n": now})
        c.execute(text("insert into mayak.scan_work_items(id,schedule_id,beacon_id,due_at,state,attempt_count,created_at,row_version) values (:id,:s,:b,:n,'DONE',0,:n,1)"), {"id": work, "s": schedule, "b": beacon, "n": now})
        c.execute(text("insert into mayak.scan_runs(id,work_item_id,beacon_id,revision_no,state,started_at,completed_at,row_version) values (:id,:w,:b,1,'SUCCEEDED_DIFFERENCE',:n,:n,1)"), {"id": run, "w": work, "b": beacon, "n": now})
    return account, beacon, run

def rows(engine: object, table: str, ids: dict[str, object] | None = None) -> list[dict[str, object]]:
    where = " and ".join(f"{k}=:{k}" for k in (ids or {})) or "true"
    with engine.connect() as c:  # type: ignore[union-attr]
        result = c.execute(text(f'SELECT * FROM mayak."{table}" WHERE {where} ORDER BY id'), ids or {}).mappings().all()
    safe = []
    for row in result:
        value = {k: v for k, v in dict(row).items() if k not in {"lease_token", "payload"}}
        safe.append({k: (str(v) if isinstance(v, UUID) else v) for k, v in value.items()})
    return safe

def snapshot(engine: object, account: UUID, event_id: UUID | None = None, outbox_id: UUID | None = None) -> dict[str, object]:
    filters = {"notification_events": {"account_id": account}}
    if event_id: filters["notification_events"] = {"id": event_id}
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
        recs = [item for item in rows(engine, "notification_delivery_reconciliations") if str(item["attempt_id"]) in attempt_ids]
    return {"events": event_rows, "outbox": out, "attempts": attempts, "reconciliations": recs}

def source(account: UUID, beacon: UUID, run: UUID, run_id: str) -> NotificationSourceEvent:
    key = f"rf24-ambiguous-source-{run_id}"; fp = sha(key)
    return NotificationSourceEvent(
        source_event_id=f"event-{run_id}", source_family=NotificationSourceFamily.NEW_LISTINGS_FOUND,
        source_producer=NotificationSourceProducer.SCAN_ORCHESTRATION, source_contract="rf24.synthetic.v1",
        source_contract_version="1", source_fact_id=f"fact-{run_id}", source_committed=True,
        source_commit_reference=f"commit-{run_id}", account_id=str(account), beacon_id=str(beacon), scan_run_id=str(run),
        listing_count=1, safe_listing_reference_ids=(f"listing-{run_id}",), correlation_id=f"corr-{run_id}",
        causation_id=f"cause-{run_id}", idempotency_key=IdempotencyKey(value=key),
        idempotency_fingerprint=IdempotencyFingerprint(value=fp), idempotency_scope=IdempotencyScope(value="rf24.synthetic"),
        source_identity_ambiguous=False, contains_raw_provider_payload=False, service_access_gate_approved=True,
        evidence_reference_ids=(f"evidence-{run_id}",),
    )

def semantics(s: NotificationSourceEvent, target: str):
    intake = evaluate_notification_source_intake(decision_id=f"intake-{s.source_event_id}", source_event=s, evidence_reference_ids=("rf24-intake",))
    channel = NotificationChannelEligibilityEvidence(NotificationChannelClass.TELEGRAM, True, target, True, True, ("rf24-channel",))
    web = NotificationChannelEligibilityEvidence(NotificationChannelClass.WEB_STATUS_READ_MODEL, True, None, False, False, ("rf24-web",))
    context = NotificationEligibilityContext(account_id=s.account_id, beacon_id=s.beacon_id, beacon_lifecycle_status=NotificationBeaconLifecycleStatus.ACTIVE, beacon_lifecycle_reference_id=s.beacon_id or "none", entitlement_status=NotificationEntitlementStatus.ALLOWED, entitlement_decision_reference_id="rf24-entitlement", no_new_status_preference_enabled=False, no_new_status_frequency_minutes=None, channel_evidence=(channel, web), recovery_grace_evidence=NotificationRecoveryGraceEvidence(False, None, False, False, ("rf24-recovery",)), evidence_reference_ids=("rf24-context",))
    eligibility = evaluate_notification_eligibility(decision_id=f"eligibility-{s.source_event_id}", source_intake_decision=intake, context=context, evidence_reference_ids=("rf24-eligibility",))
    item = create_notification_outbox_item(decision_id=f"outbox-{s.source_event_id}", outbox_item_id=f"item-{s.source_event_id}", outbox_contract="rf24.notification.v1", outbox_contract_version="1", eligibility_decision=eligibility, idempotency_key=s.idempotency_key, idempotency_fingerprint=s.idempotency_fingerprint, idempotency_scope=s.idempotency_scope, existing_outbox_item=None, evidence_reference_ids=("rf24-outbox",))
    plan = plan_notification_delivery(decision_id=f"plan-{s.source_event_id}", delivery_plan_id=f"plan-{s.source_event_id}", outbox_creation_decision=item, evidence_reference_ids=("rf24-plan",))
    return eligibility, plan

def main() -> None:
    p = argparse.ArgumentParser(); p.add_argument("--dsn", required=True); p.add_argument("--output", default="rf24-notification-ambiguous-send-evidence.json"); p.add_argument("--probes", default="rf24-notification-ambiguous-send-provider-probes.json"); p.add_argument("--log", default="rf24-notification-ambiguous-send.log"); p.add_argument("--source-sha", required=True); p.add_argument("--repo-root", default=".")
    a = p.parse_args(); run_id = f"run-{uuid4().hex[:16]}"; now = datetime.now(UTC); engine = create_engine(a.dsn); factory = sessionmaker(bind=engine)
    account, beacon, run = fixture(engine); s = source(account, beacon, run, run_id); target = f"rf24-telegram-{run_id}"; endpoint_id = uuid5(UUID("00000000-0000-0000-0000-000000000024"), target)
    with Session(engine) as db: event = ingest_source(db, s, now=now)
    with Session(engine) as db: register_endpoint(db, EndpointEligibility(endpoint_id, account, "TELEGRAM", target, NotificationChannelClass.TELEGRAM), now=now)
    elig, plan = semantics(s, target)
    with Session(engine) as db: outbox_id = fanout_event(db, event.id, (endpoint_id,), now=now, eligibility_decision=elig, delivery_plan=plan)[0]  # type: ignore[union-attr]
    phases: dict[str, object] = {"P0": snapshot(engine, account, event.id, outbox_id)}; probes: list[dict[str, object]] = []; rejections: list[dict[str, object]] = []
    def adapter(attempt):
        outcome_class = NotificationProviderOutcomeClass.DISPATCH_AMBIGUOUS if not probes else NotificationProviderOutcomeClass.PROVIDER_ACCEPTED
        probes.append({"sequence": len(probes)+1, "acceptance_run_id": run_id, "source_sha": a.source_sha, "attempt_id": str(attempt.attempt_id), "outbox_id": str(attempt.outbox_id), "attempt_number": attempt.attempt_number, "effect_fingerprint": attempt.effect_fingerprint, "synthetic_outcome_class": outcome_class.value})
        return FakeProviderOutcome(f"outcome-{len(probes)}-{run_id}", outcome_class, "safe-delivery-ref" if outcome_class is NotificationProviderOutcomeClass.PROVIDER_ACCEPTED else None, "rf24-synthetic")
    run_worker_cycle(factory, adapter, now=now, limit=1, lease_seconds=60); phases["P1"] = snapshot(engine, account, event.id, outbox_id)
    run_worker_cycle(factory, adapter, now=now + timedelta(hours=1), limit=1, lease_seconds=60); phases["P2"] = snapshot(engine, account, event.id, outbox_id)
    p1_attempt = phases["P1"]["attempts"][0]; attempt_id = UUID(str(p1_attempt["id"])); effect = str(p1_attempt["effect_fingerprint"])
    bad = [None, TrustedReconciliationEvidence(uuid4(), effect, "rf24-wrong-attempt", ReconciliationDisposition.NO_EFFECT_RETRY, True, ("rf24-evidence",)), TrustedReconciliationEvidence(attempt_id, "0"*64, "rf24-wrong-fp", ReconciliationDisposition.NO_EFFECT_RETRY, True, ("rf24-evidence",)), TrustedReconciliationEvidence(attempt_id, effect, "rf24-wrong-resolution", ReconciliationDisposition.NO_EFFECT_RETRY, True, ("rf24-evidence",))]
    for evidence in bad:
        try:
            with Session(engine) as db: resolve_reconciliation(db, attempt_id, resolution_id="caller-only", evidence=evidence)  # type: ignore[arg-type]
        except Exception as exc: rejections.append({"class": type(exc).__name__, "reason": str(exc)})
    phases["P3"] = {"snapshot": snapshot(engine, account, event.id, outbox_id), "rejections": rejections}
    trusted = TrustedReconciliationEvidence(attempt_id, effect, f"resolution-{run_id}", ReconciliationDisposition.NO_EFFECT_RETRY, True, (f"evidence-{run_id}",))
    with Session(engine) as db: resolve_reconciliation(db, attempt_id, resolution_id=trusted.resolution_id, evidence=trusted, now=now + timedelta(hours=1))
    phases["P4"] = snapshot(engine, account, event.id, outbox_id)
    run_worker_cycle(factory, adapter, now=now + timedelta(hours=2), limit=1, lease_seconds=60); phases["P5"] = snapshot(engine, account, event.id, outbox_id)
    evidence = {"technical_id": TECHNICAL_ID, "acceptance_run_id": run_id, "source_sha": a.source_sha, "source_idempotency_identity": s.idempotency_key.value, "account_id": str(account), "beacon_id": str(beacon), "event_id": str(event.id), "outbox_id": str(outbox_id), "effect_fingerprint": effect, "phases": phases, "reconciliation_evidence": {"attempt_id": str(attempt_id), "effect_fingerprint": effect, "resolution_id": trusted.resolution_id, "committed": True, "evidence_reference_ids": list(trusted.evidence_reference_ids), "conclusion": trusted.conclusion.value}, "provider_live_calls": 0, "provider_replay_test": "covered by verifier/unit tests", "provider_different_fingerprint_test": "covered by verifier/unit tests"}
    Path(a.output).write_text(json.dumps(evidence, default=str, sort_keys=True, indent=2)+"\n"); Path(a.probes).write_text(json.dumps({"acceptance_run_id":run_id,"source_sha":a.source_sha,"observations":probes}, sort_keys=True, indent=2)+"\n"); Path(a.log).write_text(f"{TECHNICAL_ID} acceptance_run_id={run_id} source_sha={a.source_sha} provider_live_calls=0\n")
    print(json.dumps({"acceptance_run_id": run_id, "event_id": str(event.id), "outbox_id": str(outbox_id), "provider_calls": len(probes), "source_sha": a.source_sha}, sort_keys=True))

if __name__ == "__main__": main()
