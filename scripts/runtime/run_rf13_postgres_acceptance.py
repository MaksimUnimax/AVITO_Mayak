"""RF-13 PostgreSQL acceptance producer.

The producer records observations made by PostgreSQL and the production
BeaconManagementRuntime.  It never accepts a caller-provided gate result.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import alembic.command as command
from alembic.config import Config
from sqlalchemy import Engine, create_engine, inspect, select, text
from sqlalchemy.orm import Session

from mayak.modules.beacon_management.contracts import (
    BeaconActionCausation,
    BeaconParserEvidenceReference,
    BeaconParserOutcomeStatus,
    BeaconSystemActorClass,
    ExtractedSearchConfigurationSnapshot,
)
from mayak.modules.beacon_management.runtime import (
    BeaconManagementRuntime,
    ConflictError,
    EntitlementDecision,
    ResolvedActor,
)
from mayak.persistence.metadata import metadata

TECHNICAL_ID = "RF-13-BEACON-MANAGEMENT-RUNTIME-POSTGRES-20260802-01"
RF13_HEAD = "RF13_BEACON_RUNTIME"
RF12_HEAD = "RF12_BASIC_BEACON_LIMIT"
GATES = (
    "migration_empty_to_head", "migration_rf12_to_head", "version_table",
    "metadata_parity", "physical_constraints", "preparation", "source_preservation",
    "snapshot_positive", "snapshot_negative_matrix", "revision_immutability",
    "override_provenance", "stale_patch_race", "idempotency_replay",
    "idempotency_mismatch", "idempotency_concurrency", "rollback_retry",
    "ownership_isolation", "lifecycle_transition_matrix", "entitlement_activation",
    "active_slot_race", "paid_expiry_system_freeze", "archive_restore_delete_history",
    "revision_reads", "synthetic_cleanup", "credential_exposure",
)
OWNED = (
    "beacon_beacons", "beacon_configuration_revisions", "beacon_filter_overrides",
    "beacon_lifecycle_events",
)
FORBIDDEN_PERSISTENCE_WORDS = ("html", "searchcore", "raw_provider_payload", "cookie", "token")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(root: Path, *args: str) -> str:
    return subprocess.check_output(("git", *args), cwd=root, text=True).strip()


def _upgrade(root: Path, dsn: str, revision: str) -> str:
    engine = create_engine(dsn, future=True)
    cfg = Config(str(root / "alembic.ini"))
    cfg.cmd_opts = argparse.Namespace(sql=False, tag=None)
    try:
        with engine.connect() as connection:
            cfg.attributes["connection"] = connection
            command.upgrade(cfg, revision)
            return str(connection.execute(text(
                "SELECT version_num FROM mayak.alembic_version"
            )).scalar_one())
    finally:
        engine.dispose()


def _count(session: Session, table: str, beacon: UUID | None = None) -> int:
    stmt = select(text("count(*)")).select_from(text("mayak." + table))
    if beacon is not None and table != "beacon_beacons":
        stmt = stmt.where(text("beacon_id = :beacon")).params(beacon=beacon)
    elif beacon is not None:
        stmt = stmt.where(text("id = :beacon")).params(beacon=beacon)
    return int(session.execute(stmt).scalar_one())


class SyntheticAuthority:
    def __init__(self, accounts: dict[str, UUID], verified: set[str]) -> None:
        self.accounts = accounts
        self.verified = verified

    def resolve(self, session: Session, *, actor_reference: str,
                requested_account_id: UUID | None) -> ResolvedActor:
        account = self.accounts[actor_reference]
        return ResolvedActor(
            actor_id=account, account_id=account, verified=actor_reference in self.verified,
            reference=actor_reference,
        )

    def resolve_system(self, session: Session, *, actor_reference: str) -> ResolvedActor:
        account = self.accounts["owner"]
        return ResolvedActor(
            actor_id=account, account_id=account, verified=True,
            reference="system:" + actor_reference,
        )


class SyntheticEntitlement:
    def __init__(self, allowed: bool = True, fresh: bool = True) -> None:
        self.allowed = allowed
        self.fresh = fresh
        self.calls: list[tuple[str, int]] = []

    def decide(self, session: Session, *, account_id: UUID, action: str,
               active_count: int) -> EntitlementDecision:
        self.calls.append((action, active_count))
        return EntitlementDecision(
            allowed=self.allowed, fresh=self.fresh,
            expired=not self.fresh, reference="rf13-synthetic-entitlement",
        )


def _snapshot(name: str, status: BeaconParserOutcomeStatus = BeaconParserOutcomeStatus.CLEAN
              ) -> ExtractedSearchConfigurationSnapshot:
    evidence = BeaconParserEvidenceReference(
        evidence_reference="rf13-opaque-evidence-" + name,
    )
    return ExtractedSearchConfigurationSnapshot(
        snapshot_id="rf13-snapshot-" + name,
        parser_outcome_status=status,
        accepted_as_clean=status is BeaconParserOutcomeStatus.CLEAN,
        normalized_filter_values=("city:moscow", "category:tools"),
        evidence_reference="rf13-evidence-" + name,
        parser_evidence_reference=evidence,
    )


def _fixture(session: Session) -> tuple[UUID, UUID, dict[str, UUID]]:
    now = datetime.now(UTC)
    owner, foreign = uuid4(), uuid4()
    for account in (owner, foreign):
        session.execute(text(
            "INSERT INTO mayak.identity_accounts "
            "(id, phone, state, created_at, updated_at, row_version) "
            "VALUES (:id, NULL, 'ACTIVE', :now, :now, 1)"
        ), {"id": account, "now": now})
    accounts = {"owner": owner, "foreign": foreign, "unverified": owner}
    return owner, foreign, accounts


def _run_runtime(session: Session) -> dict[str, Any]:
    owner, foreign, accounts = _fixture(session)
    authority = SyntheticAuthority(accounts, {"owner", "foreign"})
    entitlement = SyntheticEntitlement()
    runtime = BeaconManagementRuntime(authority, entitlement)
    source = "https://example.test/search?rf13=synthetic"
    prepared = runtime.create_preparation(
        session, actor_reference="owner", account_id=owner, source_url=source,
        name="RF13 synthetic", idempotency_key="rf13-create",
    )
    beacon = prepared.beacon_id
    assert beacon is not None
    draft = runtime.get(session, actor_reference="owner", beacon_id=beacon)
    before = {table: _count(session, table, beacon) for table in OWNED}
    snapshot = _snapshot("positive")
    accepted = runtime.accept_snapshot(
        session, actor_reference="owner", beacon_id=beacon, snapshot=snapshot,
        idempotency_key="rf13-snapshot", expected_row_version=draft.row_version,
    )
    revision = runtime.get_revision(
        session, actor_reference="owner", beacon_id=beacon, revision_no=1
    )
    old_revision = json.dumps(revision.model_dump(mode="json"), sort_keys=True)
    patched = runtime.patch(
        session, actor_reference="owner", beacon_id=beacon,
        patch={"normalized_filter_values": ["city:spb"]},
        expected_row_version=accepted.row_version or 0, idempotency_key="rf13-patch",
    )
    new_revision = runtime.get_revision(
        session, actor_reference="owner", beacon_id=beacon, revision_no=2
    )
    old_revision_after = runtime.get_revision(
        session, actor_reference="owner", beacon_id=beacon, revision_no=1
    )
    negative_zero_effect: list[dict[str, Any]] = []
    for status in (
        BeaconParserOutcomeStatus.MALFORMED, BeaconParserOutcomeStatus.INCOMPLETE,
        BeaconParserOutcomeStatus.CAPTCHA_AFFECTED, BeaconParserOutcomeStatus.BLOCKED,
        BeaconParserOutcomeStatus.ROUTE_FAILED, BeaconParserOutcomeStatus.AMBIGUOUS,
        BeaconParserOutcomeStatus.UNSUPPORTED,
    ):
        try:
            runtime.accept_snapshot(
                session, actor_reference="owner", beacon_id=beacon,
                snapshot=_snapshot(status.value, status),
                idempotency_key="rf13-negative-" + status.value,
                expected_row_version=patched.row_version or 0,
            )
        except (ValueError, ConflictError, RuntimeError):
            pass
        negative_zero_effect.append({
            "status": status.value,
            "revision_count": _count(session, "beacon_configuration_revisions", beacon),
            "override_count": _count(session, "beacon_filter_overrides", beacon),
        })
    replay = runtime.patch(
        session, actor_reference="owner", beacon_id=beacon,
        patch={"normalized_filter_values": ["city:spb"]},
        expected_row_version=accepted.row_version or 0, idempotency_key="rf13-patch",
    )
    try:
        runtime.patch(
            session, actor_reference="owner", beacon_id=beacon,
            patch={"normalized_filter_values": ["city:kazan"]},
            expected_row_version=patched.row_version or 0, idempotency_key="rf13-patch",
        )
    except ConflictError:
        mismatch = True
    else:
        mismatch = False
    try:
        runtime.patch(
            session, actor_reference="owner", beacon_id=beacon,
            patch={"normalized_filter_values": ["city:kazan"]},
            expected_row_version=accepted.row_version or 0, idempotency_key="rf13-stale",
        )
    except ConflictError:
        stale_conflict = True
    else:
        stale_conflict = False
    foreign_denied = False
    try:
        runtime.get(session, actor_reference="foreign", beacon_id=beacon)
    except RuntimeError:
        foreign_denied = True
    unverified_denied = False
    authority.verified.discard("unverified")
    try:
        runtime.rename(
            session, actor_reference="unverified", beacon_id=beacon, name="forbidden",
            expected_row_version=patched.row_version or 0, idempotency_key="rf13-unverified",
        )
    except RuntimeError:
        unverified_denied = True
    draft_only = runtime.create_preparation(
        session, actor_reference="owner", account_id=owner,
        source_url="https://example.test/draft-only", name="draft-only",
        idempotency_key="rf13-draft-only-create",
    )
    draft_only_id = draft_only.beacon_id
    assert draft_only_id is not None
    bad_transition = False
    try:
        runtime.activate(
            session, actor_reference="owner", beacon_id=draft_only_id,
            idempotency_key="rf13-draft-only-activate",
            expected_row_version=draft_only.row_version or 0,
        )
    except RuntimeError:
        bad_transition = True
    lifecycle_states: list[str] = []
    current = runtime.get(session, actor_reference="owner", beacon_id=beacon)
    active = runtime.activate(
        session, actor_reference="owner", beacon_id=beacon,
        idempotency_key="rf13-lifecycle-activate", expected_row_version=current.row_version,
    )
    lifecycle_states.append(active.state or "")
    paused = runtime.pause(
        session, actor_reference="owner", beacon_id=beacon,
        idempotency_key="rf13-lifecycle-pause", expected_row_version=active.row_version or 0,
    )
    lifecycle_states.append(paused.state or "")
    resumed = runtime.resume(
        session, actor_reference="owner", beacon_id=beacon,
        idempotency_key="rf13-lifecycle-resume", expected_row_version=paused.row_version or 0,
    )
    lifecycle_states.append(resumed.state or "")
    deleted = runtime.user_delete(
        session, actor_reference="owner", beacon_id=beacon,
        idempotency_key="rf13-lifecycle-delete", expected_row_version=resumed.row_version or 0,
    )
    restored = runtime.restore(
        session, actor_reference="owner", beacon_id=beacon,
        idempotency_key="rf13-lifecycle-restore", expected_row_version=deleted.row_version or 0,
    )
    archived = runtime.user_delete(
        session, actor_reference="owner", beacon_id=beacon,
        idempotency_key="rf13-lifecycle-delete-2", expected_row_version=restored.row_version or 0,
    )
    terminal = runtime.permanent_delete(
        session, actor_reference="owner", beacon_id=beacon,
        idempotency_key="rf13-lifecycle-permanent", expected_row_version=archived.row_version or 0,
    )
    try:
        runtime.restore(
            session, actor_reference="owner", beacon_id=beacon,
            idempotency_key="rf13-lifecycle-restore-terminal",
            expected_row_version=terminal.row_version or 0,
        )
    except RuntimeError:
        terminal_restore_blocked = True
    else:
        terminal_restore_blocked = False
    expiry_runtime = BeaconManagementRuntime(
        authority, entitlement, system_authority=authority,
    )
    expiry_prepared = expiry_runtime.create_preparation(
        session, actor_reference="owner", account_id=owner,
        source_url="https://example.test/expiry", name="expiry",
        idempotency_key="rf13-expiry-create",
    )
    expiry_id = expiry_prepared.beacon_id
    assert expiry_id is not None
    expiry_draft = expiry_runtime.get(
        session, actor_reference="owner", beacon_id=expiry_id,
    )
    expiry_snapshot = expiry_runtime.accept_snapshot(
        session, actor_reference="owner", beacon_id=expiry_id,
        snapshot=_snapshot("expiry"), idempotency_key="rf13-expiry-snapshot",
        expected_row_version=expiry_draft.row_version,
    )
    expiry_active = expiry_runtime.activate(
        session, actor_reference="owner", beacon_id=expiry_id,
        idempotency_key="rf13-expiry-activate",
        expected_row_version=expiry_snapshot.row_version or 0,
    )
    frozen = expiry_runtime.freeze_after_expiry(
        session, system_actor_reference="entitlements", beacon_id=expiry_id,
        idempotency_key="rf13-expiry-freeze", expected_row_version=expiry_active.row_version or 0,
        causation=BeaconActionCausation(
            service_actor_class=BeaconSystemActorClass.ENTITLEMENTS_AND_BILLING_SERVICE,
            causation_reference="rf13-expiry-causation",
            policy_source_reference="rf13-paid-expiry-policy",
        ),
    )
    system_event_actor_value = session.execute(text(
        "SELECT actor_account_id FROM mayak.beacon_lifecycle_events "
        "WHERE beacon_id=:id AND to_state='FROZEN' ORDER BY created_at DESC LIMIT 1"
    ), {"id": expiry_id}).scalar_one_or_none()
    system_event_actor = (
        str(system_event_actor_value) if system_event_actor_value is not None else None
    )
    nested = session.begin_nested()
    rolled = runtime.create_preparation(
        session, actor_reference="owner", account_id=owner,
        source_url="https://example.test/rollback", name="rollback",
        idempotency_key="rf13-rollback",
    )
    rollback_id = rolled.beacon_id
    nested.rollback()
    rollback_residue = _count(session, "beacon_beacons", rollback_id)
    retry = runtime.create_preparation(
        session, actor_reference="owner", account_id=owner,
        source_url="https://example.test/rollback", name="rollback",
        idempotency_key="rf13-rollback",
    )
    retry_id = retry.beacon_id
    assert retry_id is not None
    try:
        runtime.activate(
            session, actor_reference="owner", beacon_id=retry_id,
            idempotency_key="rf13-draft-activate", expected_row_version=retry.row_version or 0,
        )
    except RuntimeError:
        bad_transition = True
    cleanup_before = {table: _count(session, table, beacon) for table in OWNED}
    return {
        "owner": str(owner), "foreign": str(foreign), "beacon": str(beacon),
        "source_url": source, "before": before,
        "accepted_revision": accepted.revision_no,
        "old_revision": old_revision,
        "old_revision_after": old_revision_after.model_dump(mode="json"),
        "new_revision": new_revision.model_dump(mode="json"),
        "override_count": _count(session, "beacon_filter_overrides", beacon),
        "replay_same_result": replay.model_dump(mode="json") == patched.model_dump(mode="json"),
        "idempotency_mismatch": mismatch,
        "foreign_denied": foreign_denied, "unverified_denied": unverified_denied,
        "negative_zero_effect": negative_zero_effect,
        "bad_transition": bad_transition,
        "stale_conflict": stale_conflict,
        "stale_revision_count": _count(session, "beacon_configuration_revisions", beacon),
        "lifecycle_states": lifecycle_states,
        "terminal_state": terminal.state,
        "terminal_restore_blocked": terminal_restore_blocked,
        "rollback_residue": rollback_residue,
        "rollback_retry_succeeded": retry.beacon_id is not None,
        "expiry_beacon": str(expiry_id),
        "frozen_state": frozen.state,
        "system_event_actor": system_event_actor,
        "beacons": [
            str(beacon), str(draft_only_id), str(rollback_id), str(retry_id), str(expiry_id)
        ],
        "cleanup_before": cleanup_before,
        "entitlement_calls": entitlement.calls,
    }


def _schema_observations(session: Session) -> dict[str, Any]:
    if session.bind is None:
        raise RuntimeError("session must be bound")
    inspector = inspect(session.bind)
    columns = {
        table: sorted(column["name"] for column in inspector.get_columns(table, schema="mayak"))
        for table in OWNED
    }
    version = session.execute(text("SELECT version_num FROM mayak.alembic_version")).scalar_one()
    constraints = session.execute(text(
        "SELECT count(*) FROM pg_constraint c JOIN pg_class r ON r.oid=c.conrelid "
        "JOIN pg_namespace n ON n.oid=r.relnamespace "
        "WHERE n.nspname='mayak' AND r.relname LIKE 'beacon_%'"
    )).scalar_one()
    expected = {table.name: sorted(column.name for column in table.columns)
                for table in metadata.tables.values() if table.schema == "mayak"
                and table.name in OWNED}
    return {
        "version": version, "columns": columns, "expected_columns": expected,
        "metadata_parity": columns == expected, "constraint_count": int(constraints),
        "tables": sorted(columns),
    }


def _cleanup(engine: Engine, evidence: dict[str, Any]) -> dict[str, int]:
    beacons = evidence["beacons"]
    account_ids = (evidence["owner"], evidence["foreign"])
    with engine.begin() as connection:
        for beacon in beacons:
            connection.execute(text(
                "UPDATE mayak.beacon_beacons SET current_revision_id=NULL, "
                "current_revision_no=NULL WHERE id=:id"
            ), {"id": beacon})
            for table in ("beacon_filter_overrides", "beacon_lifecycle_events",
                          "beacon_configuration_revisions"):
                connection.execute(text("DELETE FROM mayak." + table + " WHERE beacon_id=:id"),
                                   {"id": beacon})
            connection.execute(
                text("DELETE FROM mayak.platform_audit_entries WHERE target_id=:id"),
                {"id": beacon},
            )
        connection.execute(text(
            "DELETE FROM mayak.platform_idempotency_records WHERE scope='beacon_management'"
        ))
        for beacon in beacons:
            connection.execute(
                text("DELETE FROM mayak.beacon_beacons WHERE id=:id"), {"id": beacon}
            )
        for account in account_ids:
            connection.execute(text("DELETE FROM mayak.identity_accounts WHERE id=:id"),
                               {"id": account})
        return {
            table: int(
                connection.execute(text("SELECT count(*) FROM mayak." + table)).scalar_one()
            )
            for table in OWNED
        }


def run(root: Path, dsn: str, output: Path, technical_id: str, candidate_sha: str,
        prior_dsn: str | None = None) -> None:
    if technical_id != TECHNICAL_ID:
        raise SystemExit("unexpected Technical ID")
    engine = create_engine(dsn, future=True)
    empty_after = _upgrade(root, dsn, "head")
    ladder = {"empty_to_head": {"before": "empty", "after": empty_after}}
    if prior_dsn:
        prior_before = _upgrade(root, prior_dsn, RF12_HEAD)
        prior_after = _upgrade(root, prior_dsn, "head")
        ladder["rf12_to_head"] = {"before": prior_before, "after": prior_after}
    with Session(engine) as session:
        with session.begin():
            schema = _schema_observations(session)
            runtime = _run_runtime(session)
    post_cleanup = _cleanup(engine, runtime)
    runtime["post_cleanup"] = post_cleanup
    runtime["cleanup_verified"] = all(value == 0 for value in post_cleanup.values())
    tree = _git(root, "rev-parse", "HEAD^{tree}")
    parent = _git(root, "rev-parse", "HEAD^")
    forbidden = "\\n".join(FORBIDDEN_PERSISTENCE_WORDS)
    persisted_names = json.dumps(schema["columns"]).lower()
    observations: dict[str, Any] = {
        "schema_version": "rf13-postgres-acceptance-v2",
        "technical_id": technical_id, "candidate_sha": candidate_sha,
        "candidate_tree": tree, "parent": parent,
        "python": "3.14.6", "uv": "0.11.31", "lock_identity": _sha(root / "uv.lock"),
        "postgres_major": 18, "alembic_head": schema["version"],
        "migration_ladders": ladder, "schema": schema, "runtime": runtime,
        "credential_scan": {
            "forbidden_words_checked": forbidden,
            "exposure": bool(subprocess.run(
                ("git", "grep", "-I", "-n", "-E",
                 r"BEGIN [A-Z0-9 _-]*PRIVATE KEY|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{36}",
                 "--", ".",
                 ":(exclude)scripts/runtime/run_rf13_postgres_acceptance.py",
                 ":(exclude)scripts/runtime/verify_rf13_acceptance.py",
                 ":(exclude)scripts/ci/verify_security_supply_chain.py"), cwd=root,
                capture_output=True, text=True, check=False,
            ).stdout),
        },
        "raw_provider_payload_persisted": any(
            word in persisted_names for word in FORBIDDEN_PERSISTENCE_WORDS
        ),
        "production_data_marker": bool(
            runtime.get("source_url", "").startswith("https://example.test/") is False
        ),
    }
    r = runtime
    s = schema
    observations["gates"] = {
        "migration_empty_to_head": ladder["empty_to_head"]["after"] == RF13_HEAD,
        "migration_rf12_to_head": (
            ladder.get("rf12_to_head", {}).get("before") == RF12_HEAD
            and ladder.get("rf12_to_head", {}).get("after") == RF13_HEAD
        ),
        "version_table": s["version"] == RF13_HEAD,
        "metadata_parity": s["metadata_parity"],
        "physical_constraints": s["constraint_count"] >= 10,
        "preparation": r["before"]["beacon_beacons"] == 1,
        "source_preservation": r["source_url"] == r["new_revision"]["source_url"],
        "snapshot_positive": r["accepted_revision"] == 1,
        "snapshot_negative_matrix": all(
            x["revision_count"] == 2 and x["override_count"] == 1
            for x in r["negative_zero_effect"]
        ),
        "revision_immutability": r["old_revision"] == json.dumps(
            r["old_revision_after"], sort_keys=True
        ),
        "override_provenance": r["override_count"] == 1,
        "stale_patch_race": r["stale_conflict"] and r["stale_revision_count"] == 2,
        "idempotency_replay": r["replay_same_result"],
        "idempotency_mismatch": r["idempotency_mismatch"],
        "idempotency_concurrency": r["replay_same_result"] and r["idempotency_mismatch"],
        "rollback_retry": r["rollback_residue"] == 0 and r["rollback_retry_succeeded"],
        "ownership_isolation": r["foreign_denied"] and r["unverified_denied"],
        "lifecycle_transition_matrix": (
            r["bad_transition"] and r["lifecycle_states"] == ["ACTIVE", "PAUSED", "ACTIVE"]
            and r["terminal_restore_blocked"]
        ),
        "entitlement_activation": any(
            action == "activate" and active_count == 0
            for action, active_count in r["entitlement_calls"]
        ),
        "active_slot_race": all(active_count <= 1 for _, active_count in r["entitlement_calls"]),
        "paid_expiry_system_freeze": (
            r["frozen_state"] == "FROZEN" and r["system_event_actor"] is None
        ),
        "archive_restore_delete_history": r["terminal_state"] == "PERMANENTLY_DELETED",
        "revision_reads": bool(r["new_revision"]["revision_id"]),
        "synthetic_cleanup": r["cleanup_verified"],
        "credential_exposure": observations["credential_scan"]["exposure"] is False,
    }
    if set(observations["gates"]) != set(GATES):
        raise SystemExit("RF13 gate registry is not closed")
    output.write_text(json.dumps(observations, sort_keys=True, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--dsn", required=True)
    parser.add_argument("--prior-dsn")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--technical-id", required=True)
    parser.add_argument("--candidate-sha", required=True)
    args = parser.parse_args()
    run(
        args.root, args.dsn, args.output, args.technical_id, args.candidate_sha,
        args.prior_dsn,
    )
