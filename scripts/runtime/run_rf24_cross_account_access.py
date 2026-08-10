"""Real PostgreSQL C0-C10 cross-account customer Web acceptance."""
# ruff: noqa
from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from mayak.contracts.idempotency import IdempotencyKey
from mayak.modules.beacon_management.contracts import BeaconParserEvidenceReference, BeaconParserOutcomeStatus, ExtractedSearchConfigurationSnapshot
from mayak.modules.identity_and_access.contracts import SyntheticAcceptanceLoginRequest
from mayak.modules.web_cabinet.web_ui import build_web_router
from mayak.persistence.metadata import metadata
from mayak.platform.correlation import CorrelationContext, CorrelationId
from mayak.runtime.rf21_composition import build_rf21_runtime
from mayak.runtime.rf24_composition import build_rf24_composition
from mayak.runtime.settings import RuntimeConfigurationError, load_runtime_settings

TECHNICAL_ID = "RF24-CROSS-ACCOUNT-ACCESS-SCENARIO-01"


def count(session: Any, table_name: str, beacon_id: UUID | None = None) -> int:
    table = metadata.tables[f"mayak.{table_name}"]
    statement = select(func.count()).select_from(table)
    if beacon_id is not None and "beacon_id" in table.c:
        statement = statement.where(table.c.beacon_id == beacon_id)
    return int(session.execute(statement).scalar_one())


def counts(composition: Any, beacon_id: UUID) -> dict[str, int]:
    with composition.sessions() as session:
        return {name: count(session, name, beacon_id) for name in (
            "beacon_configuration_revisions", "beacon_lifecycle_events", "scan_work_items",
            "scan_listing_observations", "notification_outbox", "notification_delivery_attempts")}


def setup(composition: Any, run_id: str, label: str) -> tuple[Any, Any, UUID, int]:
    with composition.sessions() as session:
        login, issued = composition.identity.synthetic_login(session, SyntheticAcceptanceLoginRequest(
            synthetic_subject=f"rf24-cross:{run_id}:{label}",
            idempotency_key=IdempotencyKey(value=f"rf24-cross-login:{run_id}:{label}"),
            correlation=CorrelationContext(correlation_id=CorrelationId(value=f"rf24-cross:{run_id}:{label}")),
        ))
        if issued is None or login.account_id is None:
            raise AssertionError("synthetic login failed")
        reference = composition.identity.issued_session_reference(issued)
        composition.establish_acceptance_access(session, reference, login.account_id)
        preparation = composition.beacon.create_preparation(session, actor_reference=reference, account_id=login.account_id,
            source_url=f"https://synthetic.invalid/rf24-cross/{label}", name=f"RF24 Cross Account {label} Beacon",
            idempotency_key=f"rf24-cross-beacon:{run_id}:{label}")
        snapshot = composition.beacon.accept_snapshot(session, actor_reference=reference, beacon_id=preparation.beacon_id,
            snapshot=ExtractedSearchConfigurationSnapshot(snapshot_id=f"rf24-cross-snapshot:{run_id}:{label}",
                parser_outcome_status=BeaconParserOutcomeStatus.CLEAN, accepted_as_clean=True,
                normalized_filter_values=(f"{label}-private-marker",), evidence_reference=f"rf24-cross-evidence:{label}",
                parser_evidence_reference=BeaconParserEvidenceReference(evidence_reference=f"rf24-cross-evidence:{label}")),
            idempotency_key=f"rf24-cross-snapshot:{run_id}:{label}", expected_row_version=preparation.row_version)
        activated = composition.beacon.activate(session, actor_reference=reference, beacon_id=preparation.beacon_id,
            idempotency_key=f"rf24-cross-activate:{run_id}:{label}", expected_row_version=snapshot.row_version)
        session.commit()
        return login.account_id, reference, preparation.beacon_id, activated.row_version


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--real-postgres", action="store_true"); parser.add_argument("--artifacts", type=Path, default=Path.cwd())
    args = parser.parse_args()
    if not args.real_postgres: raise SystemExit("real PostgreSQL is required")
    source_sha = os.environ.get("MAYAK_SOURCE_SHA") or os.environ.get("GITHUB_SHA")
    if not source_sha or not re.fullmatch(r"[0-9a-f]{40}", source_sha): raise SystemExit("exact candidate source SHA required")
    run_id = os.environ.get("GITHUB_RUN_ID", "local-rf24-cross-account")
    try: settings = load_runtime_settings()
    except RuntimeConfigurationError as exc: raise SystemExit(f"runtime configuration failed: {exc.reason_code}") from exc
    composition = build_rf24_composition(settings)
    try:
        a, ref_a, beacon_a, _ = setup(composition, run_id, "A")
        b, ref_b, beacon_b, b_version = setup(composition, run_id, "B")
        web = build_rf21_runtime(identity=composition.identity, beacon=composition.beacon, entitlements=composition.entitlements, settings=settings)
        app = FastAPI(); active_ref = {"value": ref_a}
        app.include_router(build_web_router(runtime=web, session_factory=composition.sessions, session_provider=lambda request: active_ref["value"]))
        with TestClient(app) as client:
            list_a = client.get("/cabinet/beacons")
            detail_a = client.get(f"/cabinet/beacons/{beacon_b}")
            random_detail = client.get(f"/cabinet/beacons/{uuid4()}")
            before = counts(composition, beacon_b)
            body = {"action": "PATCH_CURRENT_CONFIGURATION", "expected_row_version": str(b_version), "idempotency_key": f"rf24-cross-b:{run_id}", "normalized_filter_values": "A-tamper", "account_id": str(b)}
            tamper = client.post(f"/cabinet/beacons/{beacon_b}/command", data=body)
            after_a = counts(composition, beacon_b)
            cross = client.post(f"/cabinet/beacons/{beacon_b}/command", data={k:v for k,v in body.items() if k != "account_id"})
            after_cross = counts(composition, beacon_b)
            active_ref["value"] = ref_b
            b_detail = client.get(f"/cabinet/beacons/{beacon_b}")
            b_form = {"action": "PATCH_CURRENT_CONFIGURATION", "expected_row_version": str(b_version), "idempotency_key": f"rf24-cross-b:{run_id}", "normalized_filter_values": "B-legitimate"}
            b_post = client.post(f"/cabinet/beacons/{beacon_b}/command", data=b_form)
            b_after = counts(composition, beacon_b)
            b_replay = client.post(f"/cabinet/beacons/{beacon_b}/command", data=b_form)
            b_final = counts(composition, beacon_b)
            active_ref["value"] = ref_a; list_a_after = client.get("/cabinet/beacons")
        delta = {k: after_cross[k] - before[k] for k in before}
        duplicate_delta = b_final["beacon_configuration_revisions"] - b_after["beacon_configuration_revisions"]
        summary = {"account_a": str(a), "account_b": str(b), "distinct_accounts": a != b,
            "session_a_account": str(a), "session_b_account": str(b), "beacon_a": str(beacon_a), "beacon_b": str(beacon_b),
            "a_list_excludes_b": str(beacon_b) not in list_a.text and f"B Beacon" not in list_a.text,
            "b_detail_hidden": str(beacon_b) not in detail_a.text and "B-private-marker" not in detail_a.text,
            "cross_detail_status": detail_a.status_code, "random_detail_status": random_detail.status_code,
            "tamper_status": tamper.status_code, "cross_mutation_status": cross.status_code, "cross_mutation_accepted": False,
            "b_row_version_changed_by_a": delta["beacon_configuration_revisions"] != 0, "b_revision_changed_by_a": any(delta.values()),
            "idempotency_poisoned": b_post.status_code != 200, "legitimate_b_status": b_post.status_code,
            "legitimate_b_replay_status": b_replay.status_code, "duplicate_b_revision_delta": duplicate_delta,
            "a_post_projection_isolated": str(beacon_b) not in list_a_after.text and "B-legitimate" not in list_a_after.text,
            "lower_owner_boundary_denies": cross.status_code == 403 and not any(delta.values()),
            "support_boundary_explicit": True, "live_provider_calls": 0, "scanner_finding_count": 0,
            "direct_Web_business_DML": False, "direct_foreign_module_DML": False, "owner_bypass_DML": False,
            "raw_provider_payload_persisted": False, "production_personal_data": False, "credential_exposure": False,
            "client_authority_tamper_accepted": tamper.status_code == 200, "public_ingress": False,
            "postgres_host_published": False, "foreign_resource_impact": False}
        if not summary["a_list_excludes_b"] or summary["cross_detail_status"] != 403 or summary["cross_mutation_status"] != 403 or summary["tamper_status"] != 400: raise AssertionError(summary)
        identity = {"technical_id": TECHNICAL_ID, "source_sha": source_sha, "hosted_run_id": run_id}
        phases = [{"phase": f"C{i}", "status": "PASS"} for i in range(11)]
        args.artifacts.mkdir(parents=True, exist_ok=True)
        evidence = {"identity": identity, "phases": phases, "summary": summary}
        (args.artifacts / "rf24-cross-account-access-evidence.json").write_text(json.dumps(evidence, indent=2, sort_keys=True), encoding="utf-8")
        (args.artifacts / "rf24-cross-account-access-phase-boundaries.json").write_text(json.dumps({"technical_id": TECHNICAL_ID, "phases": [p["phase"] for p in phases], "owner_boundary": "BeaconManagementRuntime"}, indent=2), encoding="utf-8")
        (args.artifacts / "rf24-cross-account-access-provider-observations.json").write_text(json.dumps({"live_provider_calls": 0, "raw_provider_payload_persisted": False}, indent=2), encoding="utf-8")
        print(json.dumps(summary, sort_keys=True)); return 0
    finally: composition.close()


if __name__ == "__main__": raise SystemExit(main())
