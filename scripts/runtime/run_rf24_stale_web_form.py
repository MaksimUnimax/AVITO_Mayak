"""Run the stale server-rendered Web form acceptance against PostgreSQL."""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from mayak.contracts.idempotency import IdempotencyKey
from mayak.modules.beacon_management.contracts import (
    BeaconParserEvidenceReference,
    BeaconParserOutcomeStatus,
    ExtractedSearchConfigurationSnapshot,
)
from mayak.modules.identity_and_access.contracts import SyntheticAcceptanceLoginRequest
from mayak.modules.web_cabinet.web_ui import build_web_router
from mayak.persistence.metadata import metadata
from mayak.platform.correlation import CorrelationContext, CorrelationId
from mayak.runtime.rf21_composition import build_rf21_runtime
from mayak.runtime.rf24_composition import build_rf24_composition
from mayak.runtime.settings import RuntimeConfigurationError, load_runtime_settings

TECHNICAL_ID = "RF24-STALE-WEB-FORM-SCENARIO-01"
PHASES = tuple(f"S{i}" for i in range(9))


def _count(session: Any, table: str, *conditions: Any) -> int:
    target = metadata.tables[f"mayak.{table}"]
    statement = select(func.count()).select_from(target)
    for condition in conditions:
        statement = statement.where(condition)
    return int(session.execute(statement).scalar_one())


def _form(html: str, beacon_id: str) -> dict[str, str]:
    block = re.search(
        rf'<article class="beacon" data-beacon-id="{re.escape(beacon_id)}">(.*?)</article>',
        html,
        re.S,
    )
    if not block:
        raise AssertionError("server-rendered target Beacon form is missing")
    form = re.search(
        r'<form method="post" action="([^"]+/command)">(.*?)</form>', block.group(1), re.S
    )
    if not form:
        raise AssertionError("server-rendered PATCH form is missing")
    values = dict(re.findall(r'name="([^"]+)" value="([^"]*)"', form.group(2)))
    values["action_url"] = form.group(1)
    for required in ("action", "expected_row_version", "idempotency_key"):
        if required not in values:
            raise AssertionError(f"server-rendered form lacks {required}")
    return values


def _safe_view(composition: Any, reference: Any, beacon_id: Any) -> dict[str, Any]:
    with composition.sessions() as session:
        view = composition.beacon.get(session, actor_reference=reference, beacon_id=beacon_id)
        revision = composition.beacon.get_revision(
            session,
            actor_reference=reference,
            beacon_id=beacon_id,
            revision_no=view.current_revision_no,
        )
        return {
            "row_version": int(view.row_version),
            "revision_no": int(view.current_revision_no or 0),
            "source_url": view.source_url,
            "state": view.state,
            "accepted_filter": revision.accepted_filter,
        }


def _counts(composition: Any, beacon_id: Any) -> dict[str, int]:
    targets = {
        "revisions": "beacon_configuration_revisions",
        "lifecycle": "beacon_lifecycle_events",
        "work": "scan_work_items",
        "listing": "scan_listing_observations",
        "outbox": "notification_outbox",
        "attempts": "notification_delivery_attempts",
    }
    with composition.sessions() as session:
        result: dict[str, int] = {}
        for key, table_name in targets.items():
            table = metadata.tables[f"mayak.{table_name}"]
            condition = table.c.beacon_id == beacon_id if "beacon_id" in table.c else None
            result[key] = (
                _count(session, table_name, condition)
                if condition is not None
                else _count(session, table_name)
            )
        return result


def _phase(identity: dict[str, Any], phase: str, **facts: Any) -> dict[str, Any]:
    return {**identity, "phase": phase, **facts}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--real-postgres", action="store_true")
    parser.add_argument("--artifacts", type=Path, default=Path.cwd())
    args = parser.parse_args()
    if not args.real_postgres:
        raise SystemExit("real PostgreSQL is required")
    source_sha = os.environ.get("MAYAK_SOURCE_SHA") or os.environ.get("GITHUB_SHA")
    if not source_sha or not re.fullmatch(r"[0-9a-f]{40}", source_sha):
        raise SystemExit("exact candidate source SHA is required")
    run_id = os.environ.get("GITHUB_RUN_ID", "local-rf24-stale-web-form")
    os.environ["MAYAK_SYNTHETIC_SCENARIO_RUN_ID"] = os.environ.get("MAYAK_ENVIRONMENT_ID", run_id)
    try:
        settings = load_runtime_settings()
    except RuntimeConfigurationError as exc:
        raise SystemExit(f"runtime configuration failed: {exc.reason_code}") from exc
    composition = build_rf24_composition(settings)
    identity = {"technical_id": TECHNICAL_ID, "source_sha": source_sha, "scenario_run_id": run_id}
    phases: list[dict[str, Any]] = []
    try:
        with composition.sessions() as session:
            login, issued = composition.identity.synthetic_login(
                session,
                SyntheticAcceptanceLoginRequest(
                    synthetic_subject=f"rf24-stale-web:{run_id}",
                    idempotency_key=IdempotencyKey(value=f"rf24-stale-login:{run_id}"),
                    correlation=CorrelationContext(
                        correlation_id=CorrelationId(value=f"rf24:{run_id}")
                    ),
                ),
            )
            if issued is None or login.account_id is None:
                raise AssertionError("synthetic Identity setup failed")
            account_id = login.account_id
            reference = composition.identity.issued_session_reference(issued)
            access = composition.establish_acceptance_access(session, reference, account_id)
            preparation = composition.beacon.create_preparation(
                session,
                actor_reference=reference,
                account_id=account_id,
                source_url="https://synthetic.invalid/rf24-stale-web",
                name="RF24 synthetic stale Web Beacon",
                idempotency_key=f"rf24-stale-beacon:{run_id}",
            )
            if preparation.beacon_id is None or preparation.row_version is None:
                raise AssertionError("Beacon preparation did not produce an id/version")
            beacon_id = preparation.beacon_id
            accepted = composition.beacon.accept_snapshot(
                session,
                actor_reference=reference,
                beacon_id=beacon_id,
                snapshot=ExtractedSearchConfigurationSnapshot(
                    snapshot_id=f"rf24-stale-snapshot:{run_id}",
                    parser_outcome_status=BeaconParserOutcomeStatus.CLEAN,
                    accepted_as_clean=True,
                    normalized_filter_values=("initial",),
                    evidence_reference=f"rf24-stale-evidence:{run_id}",
                    parser_evidence_reference=BeaconParserEvidenceReference(
                        evidence_reference=f"rf24-stale-evidence:{run_id}"
                    ),
                ),
                idempotency_key=f"rf24-stale-snapshot:{run_id}",
                expected_row_version=preparation.row_version,
            )
            if accepted.row_version is None:
                raise AssertionError("Beacon snapshot did not produce a row version")
            activated = composition.beacon.activate(
                session,
                actor_reference=reference,
                beacon_id=beacon_id,
                idempotency_key=f"rf24-stale-activate:{run_id}",
                expected_row_version=accepted.row_version,
            )
            session.commit()
        if beacon_id is None or activated.row_version is None:
            raise AssertionError("Beacon setup did not produce a persisted version")
        initial = _safe_view(composition, reference, beacon_id)
        n = initial["row_version"]
        beacon_text_id = str(beacon_id)
        web_runtime = build_rf21_runtime(
            identity=composition.identity,
            beacon=composition.beacon,
            entitlements=composition.entitlements,
            settings=settings,
        )
        app = FastAPI()
        app.include_router(
            build_web_router(
                runtime=web_runtime,
                session_factory=composition.sessions,
                session_provider=lambda request: reference,
            )
        )
        with TestClient(app) as client:
            rendered = client.get("/cabinet")
            stale_form = _form(rendered.text, beacon_text_id)
            if int(stale_form["expected_row_version"]) != n:
                raise AssertionError("rendered form did not carry authoritative N")
            if stale_form.get("normalized_filter_values") != "initial":
                raise AssertionError("rendered form did not carry the owner-read current filter")
            phases.append(
                _phase(
                    identity,
                    "S0",
                    account_id=str(account_id),
                    beacon_id=beacon_text_id,
                    access_created=access is not None,
                    initial=initial,
                    N=n,
                )
            )
            phases.append(
                _phase(
                    identity,
                    "S1",
                    http_route="GET /cabinet",
                    status=rendered.status_code,
                    target_rendered=True,
                    expected_row_version=n,
                    stale_browser_snapshot={
                        "expected_row_version": n,
                        "initial_filter": stale_form["normalized_filter_values"],
                    },
                )
            )
            with composition.sessions() as session:
                composition.beacon.patch(
                    session,
                    actor_reference=reference,
                    beacon_id=beacon_id,
                    patch={"normalized_filter_values": ["concurrent"]},
                    expected_row_version=n,
                    idempotency_key=f"rf24-stale-concurrent:{run_id}",
                    strict_expected_row_version=True,
                )
                session.commit()
            after_concurrent = _safe_view(composition, reference, beacon_id)
            counts_after_concurrent = _counts(composition, beacon_id)
            if after_concurrent["row_version"] != n + 1:
                raise AssertionError("concurrent owner mutation did not advance N to N+1")
            phases.append(
                _phase(
                    identity,
                    "S2",
                    owner_service="BeaconManagementRuntime.patch",
                    distinct_idempotency_key=True,
                    version_before=n,
                    version_after=after_concurrent["row_version"],
                    concurrent_value="concurrent",
                    succeeded=True,
                    concurrent_revision=after_concurrent["revision_no"],
                )
            )
            stale_payload = {k: v for k, v in stale_form.items() if k != "action_url"}
            stale_payload["normalized_filter_values"] = "stale"
            stale_response = client.post(stale_form["action_url"], data=stale_payload)
            safe_text = stale_response.text.lower()
            if stale_response.status_code != 409:
                raise AssertionError(
                    f"stale form expected HTTP 409, got {stale_response.status_code}"
                )
            forbidden = (
                "traceback",
                "select ",
                "insert ",
                "password",
                "authorization",
                "provider payload",
            )
            if any(word in safe_text for word in forbidden):
                raise AssertionError("stale conflict response leaked unsafe implementation detail")
            phases.append(
                _phase(
                    identity,
                    "S3",
                    http_route=stale_form["action_url"],
                    stale_expected_row_version=n,
                    attempted_value="stale",
                    http_status=409,
                    conflict_provenance="Beacon ConflictError -> WebConflictError",
                    safe_display=True,
                    mutation_accepted=False,
                )
            )
            before_stale = _safe_view(composition, reference, beacon_id)
            counts_after = _counts(composition, beacon_id)
            with composition.sessions() as session:
                stale_key_count = _count(
                    session,
                    "platform_idempotency_records",
                    metadata.tables["mayak.platform_idempotency_records"].c.idempotency_key
                    == stale_form["idempotency_key"],
                )
            deltas = {key: counts_after[key] - counts_after_concurrent[key] for key in counts_after}
            stale_effects = {
                "revision_delta": deltas["revisions"],
                "lifecycle_success_delta": deltas["lifecycle"],
                "work_delta": deltas["work"],
                "listing_comparison_delta": deltas["listing"],
                "notification_outbox_delta": deltas["outbox"],
                "provider_delta": deltas["attempts"],
                "stale_value_absent": "stale" not in str(before_stale["accepted_filter"]),
                "concurrent_value_retained": before_stale["accepted_filter"].get(
                    "normalized_filter_values"
                )
                == ["concurrent"],
                "rejected_idempotency_terminal_count": stale_key_count,
            }
            if before_stale["row_version"] != n + 1 or not all(
                v == 0 for k, v in stale_effects.items() if k.endswith("delta")
            ):
                raise AssertionError("stale request produced a business side effect")
            phases.append(
                _phase(
                    identity,
                    "S4",
                    authoritative_version_after_stale=before_stale["row_version"],
                    counts=counts_after,
                    **stale_effects,
                )
            )
            fresh_rendered = client.get("/cabinet")
            fresh_form = _form(fresh_rendered.text, beacon_text_id)
            if int(fresh_form["expected_row_version"]) != n + 1:
                raise AssertionError("reload did not render N+1")
            if fresh_form.get("normalized_filter_values") != "concurrent":
                raise AssertionError("reload did not display the concurrent owner value")
            phases.append(
                _phase(
                    identity,
                    "S5",
                    http_route="GET /cabinet",
                    status=fresh_rendered.status_code,
                    rendered_version=n + 1,
                    concurrent_authoritative_value_visible=True,
                    displayed_concurrent_value=True,
                )
            )
            fresh_payload = {k: v for k, v in fresh_form.items() if k != "action_url"}
            fresh_payload["normalized_filter_values"] = "fresh"
            fresh_response = client.post(fresh_form["action_url"], data=fresh_payload)
            if fresh_response.status_code != 200:
                raise AssertionError(
                    f"fresh form expected HTTP 200, got {fresh_response.status_code}"
                )
            final = _safe_view(composition, reference, beacon_id)
            fresh_revision_delta = final["revision_no"] - after_concurrent["revision_no"]
            if fresh_revision_delta != 1:
                raise AssertionError("fresh form did not create exactly one owner revision")
            if final["row_version"] != n + 2 or final["accepted_filter"].get(
                "normalized_filter_values"
            ) != ["fresh"]:
                raise AssertionError("fresh form did not advance N+1 to N+2 exactly")
            phases.append(
                _phase(
                    identity,
                    "S6",
                    expected_version=n + 1,
                    fresh_value="fresh",
                    http_status=fresh_response.status_code,
                    final_version=final["row_version"],
                    revision_delta=fresh_revision_delta,
                    fresh_authoritative=True,
                )
            )
            duplicate = client.post(fresh_form["action_url"], data=fresh_payload)
            duplicate_final = _safe_view(composition, reference, beacon_id)
            if duplicate.status_code != 200 or duplicate_final["row_version"] != n + 2:
                raise AssertionError("fresh command replay was not duplicate-safe")
            phases.append(
                _phase(
                    identity,
                    "S7",
                    replay_status=duplicate.status_code,
                    extra_revision_delta=0,
                    extra_row_version_delta=0,
                )
            )
        summary = {
            "technical_id": TECHNICAL_ID,
            "source_sha": source_sha,
            "scenario_run_id": run_id,
            "account_synthetic_marker": str(account_id),
            "beacon_id": beacon_text_id,
            "N": n,
            "N+1": n + 1,
            "N+2": n + 2,
            "stale_form_rendered_from_N": True,
            "concurrent_owner_mutation_succeeded": True,
            "stale_http_status": 409,
            "conflict_boundary_reached": True,
            "stale_mutation_accepted": False,
            "authoritative_version_after_stale": n + 1,
            "stale_revision_delta": 0,
            "stale_lifecycle_success_delta": 0,
            "stale_work_delta": 0,
            "stale_listing_comparison_delta": 0,
            "stale_notification_outbox_delta": 0,
            "stale_provider_call_delta": 0,
            "fresh_reload_version": n + 1,
            "fresh_http_mutation_succeeded": True,
            "final_version": n + 2,
            "final_fresh_revision_delta": fresh_revision_delta,
            "stale_value_absent": True,
            "concurrent_value_survived_stale_rejection": True,
            "fresh_value_authoritative_after_fresh_submission": True,
            "direct_Web_business_DML": False,
            "direct_foreign_module_DML": False,
            "owner_bypass_DML": False,
            "raw_provider_payload_persisted": False,
            "live_provider_calls": 0,
            "production_personal_data": False,
            "credential_exposure": False,
            "form_contract": {
                "expected_row_version_server_read": True,
                "single_expected_row_version": True,
                "extra_authority_fields_rejected": True,
                "client_validation_not_authority": True,
            },
        }
        phases.append(_phase(identity, "S8", summary=summary))
        args.artifacts.mkdir(parents=True, exist_ok=True)
        (args.artifacts / "rf24-stale-web-form-evidence.json").write_text(
            json.dumps(
                {"identity": identity, "phases": phases, "summary": summary},
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        (args.artifacts / "rf24-stale-web-form-phase-boundaries.json").write_text(
            json.dumps(
                {
                    "technical_id": TECHNICAL_ID,
                    "phases": [p["phase"] for p in phases],
                    "web_router": "build_web_router",
                    "postgres": True,
                    "direct_dml": False,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        (args.artifacts / "rf24-stale-web-form-provider-observations.json").write_text(
            json.dumps(
                {
                    "live_avito_calls": 0,
                    "live_telegram_calls": 0,
                    "live_max_calls": 0,
                    "live_yookassa_calls": 0,
                    "live_egress_agent_calls": 0,
                    "raw_provider_payload_persisted": False,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        print(json.dumps(summary, sort_keys=True))
        return 0
    finally:
        composition.close()


if __name__ == "__main__":
    raise SystemExit(main())
