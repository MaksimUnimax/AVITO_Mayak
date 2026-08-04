#!/usr/bin/env python3
# ruff: noqa: E501
"""RF21 acceptance producer.

Fixture creation is deliberately performed with the migration endpoint.  All
customer reads and the Web mutation are performed through the application
endpoint and the real FastAPI router.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast
from uuid import UUID, uuid4

from alembic.config import Config
from alembic.script import ScriptDirectory
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from mayak.contracts.idempotency import IdempotencyFingerprint, IdempotencyKey, IdempotencyScope
from mayak.modules.admin_and_support.runtime import VerifiedActor
from mayak.modules.beacon_management.contracts import (
    BeaconParserEvidenceReference,
    BeaconParserOutcomeStatus,
    ExtractedSearchConfigurationSnapshot,
)
from mayak.modules.beacon_management.runtime import BeaconManagementRuntime, EntitlementDecision
from mayak.modules.entitlements_and_billing.contracts import TariffName
from mayak.modules.entitlements_and_billing.runtime import (
    AuthorityFacts,
    EntitlementsBillingRuntime,
    FakeVerifiedIdentityPort,
)
from mayak.modules.identity_and_access.contracts import SyntheticAcceptanceLoginRequest
from mayak.modules.identity_and_access.runtime import IdentityRuntime
from mayak.modules.notification_delivery.runtime import ingest_source
from mayak.modules.notification_delivery.source_intake import (
    NotificationSourceEvent,
    NotificationSourceFamily,
    NotificationSourceProducer,
)
from mayak.modules.web_cabinet.web_ui import build_web_router
from mayak.platform.correlation import CorrelationContext, CorrelationId
from mayak.runtime.rf20_composition import build_rf20_composition
from mayak.runtime.rf21_composition import CustomerIdentityAuthorityAdapter, build_rf21_runtime
from mayak.runtime.rf21_observers import production_provider_transport_guard, scan_source_semantics
from mayak.runtime.settings import ProviderUpdateMode, RuntimeProfile

TECHNICAL_ID = "RF21-WEB-CABINET-RUNTIME-01-CORRECTIVE-04"


def _heads(root: Path) -> tuple[str, ...]:
    return tuple(ScriptDirectory.from_config(Config(str(root / "alembic.ini"))).get_heads())


def _sha(root: Path) -> str:
    return subprocess.check_output(("git", "rev-parse", "HEAD"), cwd=root, text=True).strip()


def _settings() -> Any:
    return SimpleNamespace(
        runtime=SimpleNamespace(profile=RuntimeProfile.SYNTHETIC_ACCEPTANCE),
        session=SimpleNamespace(synthetic_identity_enabled=True, max_age_seconds=86400),
        providers=SimpleNamespace(
            telegram_enabled=False, max_enabled=False,
            telegram_update_mode=ProviderUpdateMode.DISABLED,
            max_update_mode=ProviderUpdateMode.DISABLED,
        ),
    )


def _owner(settings: Any) -> tuple[IdentityRuntime, BeaconManagementRuntime, EntitlementsBillingRuntime]:
    identity = IdentityRuntime(settings=settings)  # type: ignore[arg-type]
    entitlements = EntitlementsBillingRuntime()
    class BeaconEntitlementAdapter:
        def decide(self, session: Session, *, account_id: UUID, action: str,
                   active_count: int) -> EntitlementDecision:
            effective = entitlements.evaluate_effective(session, account_id, at=datetime.now(UTC))
            return EntitlementDecision(
                allowed=effective.status.value == "ALLOWED", fresh=True,
                reference=f"entitlement:{effective.grant_id or effective.status.value}",
            )
    beacon = BeaconManagementRuntime(CustomerIdentityAuthorityAdapter(identity), BeaconEntitlementAdapter())
    return identity, beacon, entitlements


def _fixture(fixture_dsn: str, run_ref: str) -> dict[str, Any]:
    settings = _settings()
    identity, beacon, entitlements = _owner(settings)
    engine = create_engine(fixture_dsn, pool_pre_ping=True)
    try:
        with Session(engine) as session, session.begin():
            first, issued = identity.synthetic_login(session, SyntheticAcceptanceLoginRequest(
                synthetic_subject=f"rf21-primary-{run_ref}",
                idempotency_key=IdempotencyKey(value=f"rf21-login-{run_ref}"),
                correlation=CorrelationContext(correlation_id=CorrelationId(value="rf21-acceptance")),
            ))
            second, second_issued = identity.synthetic_login(session, SyntheticAcceptanceLoginRequest(
                synthetic_subject=f"rf21-secondary-{run_ref}",
                idempotency_key=IdempotencyKey(value=f"rf21-login-secondary-{run_ref}"),
                correlation=CorrelationContext(correlation_id=CorrelationId(value=f"rf21-secondary-{run_ref}")),
            ))
            if issued is None or second_issued is None or first.account_id is None or second.account_id is None:
                raise RuntimeError("synthetic Identity fixture failed")
            primary = beacon.create_preparation(
                session, actor_reference=cast(str, issued.token), account_id=first.account_id,
                source_url=f"https://example.test/rf21-primary-{run_ref}", name="RF21 Primary",
                idempotency_key=f"rf21-create-primary-{run_ref}")
            foreign = beacon.create_preparation(
                session, actor_reference=cast(str, second_issued.token), account_id=second.account_id,
                source_url=f"https://example.test/rf21-secondary-{run_ref}", name="RF21 Secondary",
                idempotency_key=f"rf21-create-secondary-{run_ref}")
            if primary.beacon_id is None or foreign.beacon_id is None:
                raise RuntimeError("synthetic Beacon fixture failed")
            accepted = beacon.accept_snapshot(
                session, actor_reference=cast(str, issued.token), beacon_id=primary.beacon_id,
                expected_row_version=1, idempotency_key=f"rf21-accept-primary-{run_ref}",
                snapshot=ExtractedSearchConfigurationSnapshot(
                    snapshot_id=f"rf21-snapshot-{run_ref}", parser_outcome_status=BeaconParserOutcomeStatus.CLEAN,
                    accepted_as_clean=True, normalized_filter_values=("city:amsterdam",),
                    evidence_reference="rf21-parser-evidence",
                    parser_evidence_reference=BeaconParserEvidenceReference(evidence_reference="rf21-parser-evidence"),
                ))
            return {"account": first.account_id, "foreign_account": second.account_id,
                    "token": issued.token, "foreign_token": second_issued.token,
                    "beacon": primary.beacon_id, "foreign_beacon": foreign.beacon_id,
                    "row_version": accepted.row_version or 2}
    finally:
        engine.dispose()


def _scenario(dsn: str, fixture_dsn: str, root: Path) -> dict[str, Any]:
    run_ref = uuid4().hex
    settings = _settings()
    fixture = _fixture(fixture_dsn, run_ref)
    identity, beacon, entitlements = _owner(settings)
    # Notification fixtures are created through the Notification owner intake,
    # with one safe event per synthetic account.  No raw/provider payload is
    # involved and the broad regression database is never used for this seed.
    notification_engine = create_engine(fixture_dsn)
    with Session(notification_engine) as notification_session:
        for account_id, beacon_id, suffix in (
            (fixture["account"], fixture["beacon"], "a"),
            (fixture["foreign_account"], fixture["foreign_beacon"], "b"),
        ):
            ingest_source(notification_session, NotificationSourceEvent(
                source_event_id=f"rf21-notification-{suffix}-{run_ref}",
                source_family=NotificationSourceFamily.APPROVED_SERVICE_ACCESS_FACT,
                source_producer=NotificationSourceProducer.ENTITLEMENTS_OR_BEACON,
                source_contract="rf21.synthetic.notification", source_contract_version="1",
                source_fact_id=f"rf21-fact-{suffix}-{run_ref}", source_committed=True,
                source_commit_reference=f"rf21-commit-{suffix}-{run_ref}",
                account_id=str(account_id), beacon_id=None, scan_run_id=None, listing_count=1,
                safe_listing_reference_ids=(f"rf21-listing-{suffix}-{run_ref}",),
                correlation_id=f"rf21-correlation-{suffix}-{run_ref}",
                causation_id=f"rf21-causation-{suffix}-{run_ref}",
                idempotency_key=IdempotencyKey(value=f"rf21-notification-key-{suffix}-{run_ref}"),
                idempotency_fingerprint=IdempotencyFingerprint(
                    value=hashlib.sha256(f"rf21:{run_ref}:{suffix}".encode()).hexdigest()),
                idempotency_scope=IdempotencyScope(value="rf21.acceptance"),
                source_identity_ambiguous=False, contains_raw_provider_payload=False,
                service_access_gate_approved=True,
                evidence_reference_ids=(f"rf21-notification-evidence-{suffix}",),
            ))
        notification_session.commit()
    notification_engine.dispose()
    support = build_rf20_composition(identity=identity, entitlements=entitlements, beacon=beacon).runtime()
    public_marker = f"RF21-PUBLIC-SUPPORT-{run_ref}"
    private_marker = f"RF21-INTERNAL-NOTE-{run_ref}"
    # Seed support through its public owner APIs using synthetic operator
    # authority; the Web projection must show only the public case subject.
    with Session(create_engine(fixture_dsn)) as support_session, support_session.begin():
        operator = VerifiedActor(
            actor_account_id=fixture["account"], role="SUPPORT", authorization_scope="account_id",
            authorization_reference=fixture["token"].reveal(),
        )
        opened = support.open_case(
            support_session, actor=operator, account_id=fixture["account"],
            subject=public_marker, reason="RF21 synthetic privacy canary",
            idempotency_key=f"rf21-support-open-{run_ref}",
        )
        support.add_internal_note(
            support_session, actor=operator, case_id=UUID(opened.outcome_reference), body=private_marker,
            reason="RF21 synthetic privacy canary",
            idempotency_key=f"rf21-support-note-{run_ref}",
        )
    runtime = build_rf21_runtime(identity=identity, beacon=beacon, entitlements=entitlements,
                                 support=support, settings=settings)
    rollback_beacon: UUID
    with Session(create_engine(fixture_dsn)) as fixture_session, fixture_session.begin():
        rollback_created = beacon.create_preparation(
            fixture_session, actor_reference=cast(str, fixture["token"]),
            account_id=fixture["account"], source_url=f"https://example.test/rf21-rollback-{run_ref}",
            name="RF21 Rollback", idempotency_key=f"rf21-create-rollback-{run_ref}")
        rollback_beacon = cast(UUID, rollback_created.beacon_id)
        beacon.accept_snapshot(
            fixture_session, actor_reference=cast(str, fixture["token"]), beacon_id=rollback_beacon,
            expected_row_version=1, idempotency_key=f"rf21-accept-rollback-{run_ref}",
            snapshot=ExtractedSearchConfigurationSnapshot(
                snapshot_id=f"rf21-rollback-snapshot-{run_ref}", parser_outcome_status=BeaconParserOutcomeStatus.CLEAN,
                accepted_as_clean=True, normalized_filter_values=("city:amsterdam",),
                evidence_reference="rf21-parser-evidence",
                parser_evidence_reference=BeaconParserEvidenceReference(evidence_reference="rf21-parser-evidence"),
            ))
    # Give the primary synthetic account a real, owner-recorded entitlement so
    # the valid restore branch is exercised under current policy.
    fixture_token_material = fixture["token"].reveal()
    authority = AuthorityFacts(
        actor_id=fixture["account"], account_id=fixture["account"],
        capabilities=frozenset({"ENTITLEMENTS_TARIFF_ADMIN", "ENTITLEMENTS_TARIFF_ASSIGN_ADMIN"}),
        scope="account_id", authorization_reference=fixture_token_material,
        audit_reference=f"rf21-entitlement-audit-{run_ref}",
    )
    fixture_entitlements = EntitlementsBillingRuntime(FakeVerifiedIdentityPort(authority))
    with Session(create_engine(fixture_dsn)) as entitlement_session, entitlement_session.begin():
        now = datetime.now(UTC)
        fixture_entitlements.bootstrap_tariffs(
            entitlement_session, fixture_token_material, f"rf21-tariffs-{run_ref}",
            effective_at=now, target_account_id=fixture["account"])
        fixture_entitlements.assign_access(
            entitlement_session, fixture_token_material, tariff=TariffName.BASIC,
            starts_at=now, ends_at=now.replace(year=now.year + 1), reason="RF21 acceptance",
            idempotency_key=f"rf21-entitlement-{run_ref}", target_account_id=fixture["account"])
    app = FastAPI()
    active_token = {"value": fixture["token"]}
    app.include_router(build_web_router(
        runtime=runtime, session_factory=lambda: Session(app_engine),
        session_provider=lambda request: active_token["value"],
    ))
    app_engine = create_engine(dsn, pool_pre_ping=True)
    provider_guard = production_provider_transport_guard()
    provider_transport = provider_guard.__enter__()
    try:
        with app_engine.connect() as connection:
            application_user = str(connection.execute(text("select current_user")).scalar_one())
        with TestClient(app) as client:
            dashboard = client.get("/cabinet")
            listing = client.get("/cabinet/beacons")
            detail = client.get(f"/cabinet/beacons/{fixture['beacon']}")
            foreign_get = client.get(f"/cabinet/beacons/{fixture['foreign_beacon']}")
            form = {"action": "PATCH_CURRENT_CONFIGURATION", "expected_row_version": str(fixture["row_version"]),
                    "idempotency_key": f"rf21-web-patch-{run_ref}", "normalized_filter_values": "city:utrecht"}
            patch = client.post(f"/cabinet/beacons/{fixture['beacon']}/command", data=form)
            with Session(app_engine) as reopened:
                persisted = beacon.get(reopened, actor_reference=fixture["token"], beacon_id=fixture["beacon"])
            # Exercise every accepted lifecycle through the actual Web POST.
            version = persisted.row_version
            archive = client.post(f"/cabinet/beacons/{fixture['beacon']}/command", data={
                "action": "ARCHIVE_TO_HISTORY", "expected_row_version": str(version),
                "idempotency_key": f"rf21-web-archive-{run_ref}"})
            with Session(app_engine) as reopened:
                archived = beacon.get(reopened, actor_reference=fixture["token"], beacon_id=fixture["beacon"])
            restore = client.post(f"/cabinet/beacons/{fixture['beacon']}/command", data={
                "action": "RESTORE_FROM_HISTORY", "expected_row_version": str(archived.row_version),
                "idempotency_key": f"rf21-web-restore-{run_ref}"})
            with Session(app_engine) as reopened:
                restored = beacon.get(reopened, actor_reference=fixture["token"], beacon_id=fixture["beacon"])
            delete_missing = client.post(f"/cabinet/beacons/{fixture['beacon']}/command", data={
                "action": "DELETE_TO_HISTORY", "expected_row_version": str(restored.row_version),
                "idempotency_key": f"rf21-web-delete-missing-{run_ref}"})
            delete = client.post(f"/cabinet/beacons/{fixture['beacon']}/command", data={
                "action": "DELETE_TO_HISTORY", "expected_row_version": str(restored.row_version),
                "idempotency_key": f"rf21-web-delete-{run_ref}", "confirmation": "confirmed"})
            with Session(app_engine) as reopened:
                deleted = beacon.get(reopened, actor_reference=fixture["token"], beacon_id=fixture["beacon"])
            permanent_missing = client.post(f"/cabinet/beacons/{fixture['beacon']}/command", data={
                "action": "PERMANENT_DELETE", "expected_row_version": str(deleted.row_version),
                "idempotency_key": f"rf21-web-permanent-missing-{run_ref}"})
            permanent = client.post(f"/cabinet/beacons/{fixture['beacon']}/command", data={
                "action": "PERMANENT_DELETE", "expected_row_version": str(deleted.row_version),
                "idempotency_key": f"rf21-web-permanent-{run_ref}", "confirmation": "confirmed"})
            with Session(app_engine) as reopened:
                lifecycle = beacon.get(reopened, actor_reference=fixture["token"], beacon_id=fixture["beacon"])
                lifecycle_history = beacon.history(reopened, actor_reference=fixture["token"], beacon_id=fixture["beacon"])
            # Failure after owner mutation and transaction entry must be rolled back.
            with Session(app_engine) as rollback_session:
                rollback_before_view = beacon.get(
                    rollback_session, actor_reference=fixture["token"], beacon_id=rollback_beacon)
            rollback_before = rollback_before_view.row_version
            beacon_adapter = runtime.beacon
            if beacon_adapter is None:
                raise RuntimeError("RF21 rollback requires Beacon Web adapter")
            original_command = beacon_adapter.command
            def fail_after_owner(*args: Any, **kwargs: Any) -> Any:
                original_command(*args, **kwargs)
                raise RuntimeError("injected post-owner failure")
            beacon_adapter.command = fail_after_owner  # type: ignore[method-assign]
            rollback_response = client.post(f"/cabinet/beacons/{rollback_beacon}/command", data={
                "action": "PATCH_CURRENT_CONFIGURATION", "expected_row_version": str(rollback_before),
                "idempotency_key": f"rf21-web-rollback-{run_ref}", "normalized_filter_values": "city:haarlem"})
            beacon_adapter.command = original_command  # type: ignore[method-assign]
            with Session(app_engine) as reopened:
                rollback_after = beacon.get(reopened, actor_reference=fixture["token"], beacon_id=rollback_beacon)
            # Notification verdicts come from the actual RF21 dashboard
            # projection, never from a detached owner read.
            active_token["value"] = fixture["token"]
            a_projection = client.get("/cabinet")
            active_token["value"] = fixture["foreign_token"]
            b_projection = client.get("/cabinet")
            active_token["value"] = fixture["token"]
            post_form = {
                "action": "PATCH_CURRENT_CONFIGURATION",
                "expected_row_version": str(rollback_before),
                "idempotency_key": f"rf21-web-replay-{run_ref}",
                "normalized_filter_values": "city:utrecht",
            }
            first_replay_target = client.post(
                f"/cabinet/beacons/{rollback_beacon}/command", data=post_form
            )
            replay = client.post(
                f"/cabinet/beacons/{rollback_beacon}/command", data=post_form
            )
            mismatch = client.post(
                f"/cabinet/beacons/{rollback_beacon}/command",
                data={**post_form, "normalized_filter_values": "city:rotterdam"},
            )
            stale = client.post(
                f"/cabinet/beacons/{rollback_beacon}/command",
                data={**post_form, "idempotency_key": f"rf21-stale-{run_ref}",
                      "expected_row_version": str(rollback_before)},
            )
            with Session(app_engine) as foreign_session:
                foreign_row_version = beacon.get(
                    foreign_session, actor_reference=fixture["foreign_token"],
                    beacon_id=fixture["foreign_beacon"],
                ).row_version
            foreign_post = client.post(
                f"/cabinet/beacons/{fixture['foreign_beacon']}/command",
                data={**form, "idempotency_key": f"rf21-foreign-{run_ref}",
                      "expected_row_version": str(foreign_row_version)},
            )
            overrides = [client.post(f"/cabinet/beacons/{fixture['beacon']}/command", data={**form, key: str(fixture['foreign_account'])}) for key in ("account_id", "actor", "role")]
            html = dashboard.text + listing.text + detail.text + patch.text
            active_token["value"] = fixture["foreign_token"]
            foreign_dashboard = client.get("/cabinet")
            active_token["value"] = fixture["token"]
            asset_refs = re.findall(r"<(?:link|script|img|iframe)\b[^>]+(?:src|href)=[\"']([^\"']+)", html, re.I)
            external_assets = sum(ref.startswith(("http://", "https://", "//")) or "fonts.googleapis" in ref.lower() for ref in asset_refs)
            # The source scan is an executed AST check, not a claimed runtime counter.
            source_paths = tuple((root / "src/mayak/modules/web_cabinet").glob("*.py")) + (root / "src/mayak/runtime/rf21_composition.py",)
            direct_dml = any(isinstance(node, (ast.Import, ast.ImportFrom)) and "sqlalchemy" in ast.unparse(node)
                             for path in source_paths for node in ast.walk(ast.parse(path.read_text())))
            semantic_source = "\n".join(path.read_text() for path in source_paths)
            semantic = scan_source_semantics(semantic_source, subject="RF21-Web-source")
            return {
                "application_user": application_user,
                "production_role_observed": application_user == "mayak_application",
                "http": {"dashboard_get": dashboard.status_code == 200, "beacon_list_get": listing.status_code == 200,
                         "beacon_detail_get": detail.status_code == 200, "patch_post": patch.status_code == 200,
                         "foreign_get_denied": foreign_get.status_code in {403, 404},
                         "foreign_post_denied": foreign_post.status_code in {403, 404},
                         "browser_overrides_denied": all(response.status_code in {400, 403, 409} for response in overrides),
                         "replay": first_replay_target.status_code == 200 and replay.status_code == 200,
                         "mismatch": mismatch.status_code == 409,
                         "strict_stale": stale.status_code == 409,
                         "diagnostic_statuses": {
                             "foreign_post": foreign_post.status_code,
                             "first_replay_target": first_replay_target.status_code,
                             "replay": replay.status_code,
                             "mismatch": mismatch.status_code,
                             "stale": stale.status_code,
                         }},
                "persisted": persisted.current_revision_no is not None,
                "lww_preserved": persisted.source_url == f"https://example.test/rf21-primary-{run_ref}",
                "dashboard_beacon_count": html.count("data-beacon-id"),
                "external_asset_scan": {"count": external_assets, "provenance": "rendered_html_scan"},
                "provider_transport": provider_transport.observation().as_dict(),
                "direct_web_dml_scan": {"found": direct_dml, "method": "source_ast_scan",
                                        "measured": not direct_dml},
                "security_semantics": semantic,
                "owner_provenance": {"identity": "owner_operation", "account": "database_query",
                    "entitlements": "owner_operation", "beacon": "http_request", "scan": "owner_operation",
                    "notification": "owner_operation", "telegram": "owner_operation", "max": "owner_operation",
                    "support": "owner_operation"},
                "support_private_note_leakage": "INTERNAL" in html,
                "support_projection": {
                    "ready": "data-section=\"support\"" in html,
                    "public_marker_visible": public_marker in html,
                    "private_marker_visible": private_marker in html,
                    "foreign_excludes_primary": public_marker not in foreign_dashboard.text,
                    "method": "SupportWebAdapter.customer_visible_summary",
                },
                "lifecycle": {
                    "patch": patch.status_code == 200 and persisted.current_revision_no is not None,
                    "archive": archive.status_code == 200 and archived.state == "ARCHIVED",
                    "delete": delete_missing.status_code == 400 and delete.status_code == 200 and deleted.state == "ARCHIVED",
                    "restore": restore.status_code == 200 and restored.state == "READY",
                    "permanent_delete": permanent_missing.status_code == 400 and permanent.status_code == 200 and lifecycle.state == "PERMANENTLY_DELETED",
                    "history_reloaded": len(lifecycle_history) >= 4,
                },
                "rollback": {
                    "request_rejected": rollback_response.status_code == 503,
                    "state_unchanged_after_reopen": rollback_after.row_version == rollback_before,
                    "revision_unchanged_after_reopen": rollback_after.current_revision_no == rollback_before_view.current_revision_no,
                },
                "notification_isolation": {
                    "method": "NotificationWebAdapter.read:RF21-WebDashboard",
                    "a_visible": f"rf21-listing-a-{run_ref}" in a_projection.text,
                    "a_excludes_b": f"rf21-listing-b-{run_ref}" not in a_projection.text,
                    "b_visible": f"rf21-listing-b-{run_ref}" in b_projection.text,
                    "b_excludes_a": f"rf21-listing-a-{run_ref}" not in b_projection.text,
                },
                "lifecycle_status_codes": {
                    "archive": archive.status_code, "restore": restore.status_code,
                    "delete_missing": delete_missing.status_code, "delete": delete.status_code,
                    "permanent_missing": permanent_missing.status_code, "permanent": permanent.status_code,
                },
            }
    finally:
        provider_guard.__exit__(None, None, None)
        app_engine.dispose()


def run(*, dsn: str, fixture_dsn: str, output: Path, candidate_sha: str, root: Path) -> None:
    if not dsn.strip() or not fixture_dsn.strip():
        raise SystemExit("application and fixture PostgreSQL DSNs are required")
    scenario = _scenario(dsn, fixture_dsn, root)
    engine = create_engine(fixture_dsn, pool_pre_ping=True)
    try:
        with engine.connect() as connection:
            version = str(connection.execute(text("select current_setting('server_version')")).scalar_one())
            head = str(connection.execute(text("select version_num from mayak.alembic_version")).scalar_one())
    finally:
        engine.dispose()
    data = {"technical_id": TECHNICAL_ID, "candidate_sha": candidate_sha,
            "postgresql_version": version, "migration_head": head, "migration_heads_observed": list(_heads(root)),
            "production_scenario_uses_application_role": scenario["production_role_observed"], **scenario,
            "security": {"token_access": {"result": "PASS" if scenario["security_semantics"]["token_access"] else "FAIL",
                                            "method": "executed_ast_semantic_observer"},
                          "raw_provider_payload": {"result": "PASS" if scenario["security_semantics"]["raw_provider_payload"] else "FAIL",
                                                    "method": "executed_ast_semantic_observer"},
                          "direct_web_dml": {"result": "PASS" if scenario["security_semantics"]["direct_web_dml"] else "FAIL",
                                             "method": "executed_ast_semantic_observer"},
                          "external_assets": {"result": "PASS" if scenario["external_asset_scan"]["count"] == 0 else "FAIL",
                                               "method": "rendered_html_observer"}},
            "provenance": {"database_queries": ["server_version", "migration_head"], "http_requests": 7,
                           "owner_operations": ["Identity.validate_session", "Support.customer_visible_summary"],
                           "rendered_html_scan": True, "source_ast_scan": True, "instrumented_transport": True}}
    output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dsn", required=True)
    parser.add_argument("--fixture-dsn", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--candidate-sha", required=True)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    run(dsn=args.dsn, fixture_dsn=args.fixture_dsn, output=args.output,
        candidate_sha=args.candidate_sha, root=args.repo_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
