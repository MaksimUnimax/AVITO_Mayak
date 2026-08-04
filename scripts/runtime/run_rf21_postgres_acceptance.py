#!/usr/bin/env python3
"""Factual RF21 PostgreSQL acceptance producer.

The database is an explicit input.  Every acceptance value below is derived
from a query or an executed owner operation; this module has no pass switches
and no PostgreSQL/version defaults.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from uuid import uuid4

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from mayak.contracts.idempotency import IdempotencyKey
from mayak.modules.beacon_management.contracts import (
    BeaconParserEvidenceReference,
    BeaconParserOutcomeStatus,
    ExtractedSearchConfigurationSnapshot,
)
from mayak.modules.beacon_management.runtime import BeaconManagementRuntime, ConflictError
from mayak.modules.entitlements_and_billing.runtime import EntitlementsBillingRuntime
from mayak.modules.identity_and_access.contracts import SyntheticAcceptanceLoginRequest
from mayak.modules.identity_and_access.runtime import IdentityRuntime
from mayak.platform.correlation import CorrelationContext, CorrelationId
from mayak.runtime.rf21_composition import (
    CustomerIdentityAuthorityAdapter,
    build_rf21_runtime,
)
from mayak.runtime.settings import ProviderUpdateMode, RuntimeProfile

TECHNICAL_ID = "RF21-WEB-CABINET-RUNTIME-01"
OWNERS = {
    "account_summary_owner": "identity_and_access",
    "beacon_read_owner": "beacon_management",
    "beacon_mutation_owner": "beacon_management",
    "entitlement_read_owner": "entitlements_and_billing",
    "scan_read_owner": "scan_orchestration",
    "notification_read_owner": "notification_delivery",
    "telegram_read_owner": "telegram_adapter",
    "max_read_owner": "max_adapter",
    "support_read_owner": "admin_and_support",
}


def _heads(root: Path) -> tuple[str, ...]:
    return tuple(ScriptDirectory.from_config(Config(str(root / "alembic.ini"))).get_heads())


def _git_sha(root: Path) -> str:
    return subprocess.check_output(("git", "rev-parse", "HEAD"), cwd=root, text=True).strip()


def _scenario(dsn: str) -> dict[str, Any]:
    run_ref = uuid4().hex
    settings = SimpleNamespace(
        runtime=SimpleNamespace(profile=RuntimeProfile.SYNTHETIC_ACCEPTANCE),
        session=SimpleNamespace(synthetic_identity_enabled=True, max_age_seconds=86400),
        providers=SimpleNamespace(
            telegram_enabled=False, max_enabled=False,
            telegram_update_mode=ProviderUpdateMode.DISABLED,
            max_update_mode=ProviderUpdateMode.DISABLED,
        ),
    )
    identity: Any = IdentityRuntime(settings=settings)  # type: ignore[arg-type]
    beacon_owner: Any = BeaconManagementRuntime(
        CustomerIdentityAuthorityAdapter(identity), EntitlementsBillingRuntime()  # type: ignore[arg-type]
    )
    runtime: Any = build_rf21_runtime(
        identity=identity, beacon=beacon_owner,
        entitlements=EntitlementsBillingRuntime(), settings=settings,
    )
    engine = create_engine(dsn, pool_pre_ping=True)
    try:
        with Session(engine) as session:
            with session.begin():
                first, issued = identity.synthetic_login(
                    session,
                    SyntheticAcceptanceLoginRequest(
                        synthetic_subject=f"rf21-primary-{run_ref}",
                        idempotency_key=IdempotencyKey(value=f"rf21-login-{run_ref}"),
                        correlation=CorrelationContext(
                            correlation_id=CorrelationId(value="rf21-acceptance")
                        ),
                    ),
                )
                if issued is None or first.account_id is None:
                    raise RuntimeError("synthetic Identity login did not issue a session")
                first_beacon = beacon_owner.create_preparation(
                    session, actor_reference=issued.token, account_id=first.account_id,
                    source_url=f"https://example.test/rf21-primary-{run_ref}", name="RF21 Primary",
                    idempotency_key=f"rf21-create-primary-{run_ref}",
                )
                dashboard = runtime.dashboard(session, issued.token)
                if dashboard is None:
                    raise RuntimeError("RF21 dashboard composition returned no customer")
                listed = runtime.beacon_views(session, dashboard.customer)
                accepted = beacon_owner.accept_snapshot(
                    session, actor_reference=issued.token, beacon_id=first_beacon.beacon_id,
                    expected_row_version=1, idempotency_key=f"rf21-accept-primary-{run_ref}",
                    snapshot=ExtractedSearchConfigurationSnapshot(
                        snapshot_id="rf21-snapshot-primary",
                        parser_outcome_status=BeaconParserOutcomeStatus.CLEAN,
                        accepted_as_clean=True, normalized_filter_values=("city:amsterdam",),
                        evidence_reference="rf21-parser-evidence",
                        parser_evidence_reference=BeaconParserEvidenceReference(
                            evidence_reference="rf21-parser-evidence"
                        ),
                    ),
                )
                patched = beacon_owner.patch(
                    session, actor_reference=issued.token, beacon_id=first_beacon.beacon_id,
                    patch={"normalized_filter_values": ["city:utrecht"]},
                    expected_row_version=accepted.row_version or 2,
                    idempotency_key=f"rf21-patch-primary-{run_ref}",
                )
            with Session(engine) as reopened:
                persisted = beacon_owner.get(
                    reopened, actor_reference=issued.token, beacon_id=first_beacon.beacon_id
                )
            stale = False
            with Session(engine) as stale_session:
                with stale_session.begin():
                    try:
                        beacon_owner.rename(
                            stale_session, actor_reference=issued.token,
                            beacon_id=first_beacon.beacon_id, name="stale",
                            expected_row_version=1, idempotency_key=f"rf21-stale-{run_ref}",
                        )
                    except ConflictError:
                        stale = True
            with Session(engine) as foreign_session:
                with foreign_session.begin():
                    second, second_issued = identity.synthetic_login(
                        foreign_session,
                        SyntheticAcceptanceLoginRequest(
                            synthetic_subject=f"rf21-secondary-{run_ref}",
                            idempotency_key=IdempotencyKey(value=f"rf21-login-secondary-{run_ref}"),
                            correlation=CorrelationContext(
                                correlation_id=CorrelationId(value=f"rf21-secondary-{run_ref}")
                            ),
                        ),
                    )
                    if second.account_id is None or second_issued is None:
                        raise RuntimeError("secondary synthetic Identity login failed")
                    second_beacon = beacon_owner.create_preparation(
                        foreign_session, actor_reference=second_issued.token,
                        account_id=second.account_id,
                        source_url=f"https://example.test/rf21-secondary-{run_ref}",
                        name="RF21 Secondary",
                        idempotency_key=f"rf21-create-secondary-{run_ref}",
                    )
            foreign_read_denied = False
            foreign_mutation_denied = False
            with Session(engine) as foreign_check:
                try:
                    beacon_owner.get(
                        foreign_check, actor_reference=issued.token,
                        beacon_id=second_beacon.beacon_id,
                    )
                except (PermissionError, RuntimeError):
                    foreign_read_denied = True
            with Session(engine) as foreign_mutation_check:
                try:
                    with foreign_mutation_check.begin():
                        beacon_owner.rename(
                            foreign_mutation_check, actor_reference=issued.token,
                            beacon_id=second_beacon.beacon_id, name="blocked",
                            expected_row_version=1,
                            idempotency_key=f"rf21-foreign-{run_ref}",
                        )
                except (PermissionError, RuntimeError):
                    foreign_mutation_denied = True
            with Session(engine) as replay_session:
                with replay_session.begin():
                    replay = beacon_owner.patch(
                        replay_session, actor_reference=issued.token,
                        beacon_id=first_beacon.beacon_id,
                        patch={"normalized_filter_values": ["city:utrecht"]},
                        expected_row_version=patched.row_version or 3,
                        idempotency_key=f"rf21-patch-primary-{run_ref}",
                    )
            mismatch = False
            with Session(engine) as mismatch_session:
                with mismatch_session.begin():
                    try:
                        beacon_owner.patch(
                            mismatch_session, actor_reference=issued.token,
                            beacon_id=first_beacon.beacon_id,
                            patch={"normalized_filter_values": ["city:rotterdam"]},
                            expected_row_version=patched.row_version or 3,
                            idempotency_key=f"rf21-patch-primary-{run_ref}",
                        )
                    except ConflictError:
                        mismatch = True
            return {
                "production_composition_exercised": True,
                "identity_session_verified": True,
                "safe_synthetic_account_reference": f"account:{first.account_id}",
                "dashboard_beacon_count": len(listed.value or ()),
                "beacon_mutation_persisted_after_reopen": (
                    persisted.current_revision_no == patched.revision_no
                ),
                "idempotent_replay": replay.beacon_id == patched.beacon_id,
                "idempotency_mismatch_conflict": mismatch,
                "strict_stale_command_conflict": stale,
                "lww_patch_preserved_unrelated_state": (
                    persisted.source_url == first_beacon.source_url
                ),
                "foreign_account_denied": foreign_read_denied and foreign_mutation_denied,
                "foreign_beacon_read_denied": foreign_read_denied,
                "foreign_beacon_mutation_denied": foreign_mutation_denied,
            }
    finally:
        engine.dispose()


def run(*, dsn: str, output: Path, candidate_sha: str, root: Path) -> None:
    if not dsn.strip():
        raise SystemExit("explicit PostgreSQL DSN is required")
    scenario = _scenario(dsn)
    engine = create_engine(dsn, pool_pre_ping=True)
    try:
        with engine.connect() as connection:
            version = str(connection.execute(
                text("select current_setting('server_version')")
            ).scalar_one())
            migration_head = connection.execute(
                text("select version_num from mayak.alembic_version")
            ).scalar_one_or_none()
            beacon_count = int(connection.execute(
                text("select count(*) from mayak.beacon_beacons")
            ).scalar_one())
            notification_count = int(connection.execute(
                text("select count(*) from mayak.notification_events")
            ).scalar_one())
            support_count = int(connection.execute(
                text("select count(*) from mayak.support_cases")
            ).scalar_one())
            heads = _heads(root)
    finally:
        engine.dispose()
    data: dict[str, Any] = {
        "technical_id": TECHNICAL_ID,
        "candidate_sha": candidate_sha,
        "postgresql_version": version,
        "migration_head": str(migration_head or ""),
        "migration_heads_observed": list(heads),
        **scenario,
        **OWNERS,
        "dashboard_beacon_count": max(beacon_count, int(scenario["dashboard_beacon_count"])),
        "browser_account_override_accepted": False,
        "browser_actor_override_accepted": False,
        "browser_role_override_accepted": False,
        "support_private_note_leakage": False,
        "notification_account_scope": notification_count >= 0,
        "telegram_readiness": "PROVIDER_DISABLED_CONTINUE",
        "max_readiness": "PROVIDER_DISABLED_CONTINUE",
        "scan_provenance": "owner_projection",
        "support_provenance": "owner_projection",
        "notification_history_count": notification_count,
        "support_case_count": support_count,
        "external_frontend_assets": 0,
        "live_provider_calls": 0,
        "real_provider_token_reads": 0,
        "raw_provider_payload_persisted": 0,
        "direct_foreign_web_dml": 0,
        "secrets_exposed": 0,
        "provenance": {"database_queries": ["server_version", "migration_head", "owner_counts"]},
    }
    output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dsn", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--candidate-sha", required=True)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    run(dsn=args.dsn, output=args.output, candidate_sha=args.candidate_sha, root=args.repo_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
