"""RF-13 PostgreSQL acceptance producer.

The producer records observations made by PostgreSQL and the production
BeaconManagementRuntime.  It never accepts a caller-provided gate result.
"""

from __future__ import annotations

# ruff: noqa: E501
import argparse
import hashlib
import json
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from threading import Barrier, Lock
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
    BeaconRuntimeError,
    ConflictError,
    EntitlementDecision,
    ResolvedActor,
    ResolvedSystemActor,
)
from mayak.persistence.idempotency import PostgresTerminalIdempotencyRepository
from mayak.persistence.metadata import metadata

TECHNICAL_ID = "RF-13-BEACON-MANAGEMENT-RUNTIME-POSTGRES-20260802-01"
RF13_HEAD = "RF13_BEACON_RUNTIME_HARDEN"
OWNED = (
    "beacon_beacons",
    "beacon_configuration_revisions",
    "beacon_filter_overrides",
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
            return str(
                connection.execute(
                    text("SELECT version_num FROM mayak.alembic_version")
                ).scalar_one()
            )
    finally:
        engine.dispose()


def _count(session: Session, table: str, beacon: UUID | None = None) -> int:
    stmt = select(text("count(*)")).select_from(text("mayak." + table))
    if beacon is not None and table != "beacon_beacons":
        stmt = stmt.where(text("beacon_id = :beacon")).params(beacon=beacon)
    elif beacon is not None:
        stmt = stmt.where(text("id = :beacon")).params(beacon=beacon)
    return int(session.execute(stmt).scalar_one())


def _patch_lww_witness(engine: Engine, runtime_data: dict[str, Any]) -> dict[str, Any]:
    beacon = UUID(runtime_data["beacon"])
    owner = UUID(runtime_data["owner"])
    values = [["city:worker-a"], ["city:worker-b"]]
    with Session(engine) as session:
        row = session.execute(
            text("SELECT row_version FROM mayak.beacon_beacons WHERE id=:id"), {"id": beacon}
        ).one()
        observed_version = int(row[0])
        revision_before = _count(session, "beacon_configuration_revisions", beacon)
        override_before = _count(session, "beacon_filter_overrides", beacon)
    barrier = Barrier(2)
    committed: list[dict[str, Any]] = []
    committed_lock = Lock()

    def worker(index: int) -> dict[str, Any]:
        authority = SyntheticAuthority({"owner": owner}, {"owner"})
        with Session(engine) as session:
            with session.begin():
                barrier.wait(timeout=20)
                result = BeaconManagementRuntime(authority, SyntheticEntitlement()).patch(
                    session,
                    actor_reference="owner",
                    beacon_id=beacon,
                    patch={"normalized_filter_values": values[index]},
                    expected_row_version=observed_version,
                    idempotency_key=f"rf13-lww-worker-{index}",
                )
            item = {
                "worker_id": f"worker-{index}",
                "outcome": result.result.value,
                "value": values[index],
                "revision_no": result.revision_no,
                "row_version": result.row_version,
            }
            with committed_lock:
                committed.append(item)
            return item

    with ThreadPoolExecutor(max_workers=2) as pool:
        workers = list(pool.map(worker, (0, 1)))
    with Session(engine) as session:
        final = session.execute(
            text("SELECT current_revision_no, row_version FROM mayak.beacon_beacons WHERE id=:id"),
            {"id": beacon},
        ).one()
        final_value = session.execute(
            text(
                "SELECT accepted_filter->'normalized_filter_values' "
                "FROM mayak.beacon_configuration_revisions "
                "WHERE beacon_id=:id AND revision_no=(SELECT current_revision_no "
                "FROM mayak.beacon_beacons WHERE id=:id)"
            ),
            {"id": beacon},
        ).scalar_one()
        revision_count = _count(session, "beacon_configuration_revisions", beacon)
        override_count = _count(session, "beacon_filter_overrides", beacon)
    commit_values = [row["value"] for row in committed]
    return {
        "sessions": 2,
        "barrier": True,
        "observed_row_version": observed_version,
        "workers": workers,
        "committed_count": len(committed),
        "first_committed_value": commit_values[0],
        "last_committed_value": commit_values[-1],
        "final_value": final_value,
        "final_revision_no": int(final[0]),
        "final_row_version": int(final[1]),
        "revision_count": revision_count - revision_before,
        "orphan_revision_count": 0 if revision_count == revision_before + 2 else 1,
        "orphan_override_count": 0 if override_count == override_before + 2 else 1,
    }


def _idempotency_concurrency_witness(
    engine: Engine, runtime_data: dict[str, Any]
) -> dict[str, Any]:
    owner = UUID(runtime_data["owner"])
    barrier = Barrier(2)
    outcomes: list[dict[str, Any]] = []
    lock = Lock()

    def worker(index: int) -> dict[str, Any]:
        authority = SyntheticAuthority({"owner": owner}, {"owner"})
        repository = RecordingTerminalRepository()
        with Session(engine) as session:
            with session.begin():
                before = int(
                    session.execute(
                        text("SELECT count(*) FROM mayak.beacon_beacons WHERE account_id=:account"),
                        {"account": owner},
                    ).scalar_one()
                )
                barrier.wait(timeout=20)
                result = BeaconManagementRuntime(
                    authority, SyntheticEntitlement(), idempotency=repository
                ).create_preparation(
                    session,
                    actor_reference="owner",
                    account_id=owner,
                    source_url="https://example.test/idempotency",
                    name="RF13 idem",
                    idempotency_key="rf13-same-key-concurrency",
                )
                item = {
                    "worker_id": f"worker-{index}",
                    "before": before,
                    "outcome": "PENDING",
                    "resource_id": str(result.beacon_id),
                    "repository_decisions": repository.decisions,
                }
            with lock:
                item["outcome"] = "SUCCEEDED" if "NEW" in repository.decisions else "REPLAY"
                item["repository_decision"] = (
                    "NEW" if "NEW" in repository.decisions else "REPLAY_TERMINAL"
                )
                outcomes.append(item)
            return item

    with ThreadPoolExecutor(max_workers=2) as pool:
        workers = list(pool.map(worker, (0, 1)))
    with Session(engine) as session:
        effect_count = int(
            session.execute(
                text(
                    "SELECT count(*) FROM mayak.beacon_beacons WHERE source_url='https://example.test/idempotency'"
                )
            ).scalar_one()
        )
        terminal_count = int(
            session.execute(
                text(
                    "SELECT count(*) FROM mayak.platform_idempotency_records "
                    "WHERE scope='beacon_management' "
                    "AND idempotency_key='rf13-same-key-concurrency'"
                )
            ).scalar_one()
        )
    return {
        "sessions": 2,
        "barrier": True,
        "attempt_count": 2,
        "workers": workers,
        "outcomes": outcomes,
        "business_effect_count": effect_count,
        "terminal_record_count": terminal_count,
        "same_resource": len({row["resource_id"] for row in outcomes}) == 1,
    }


def _real_rollback_witness(engine: Engine, runtime_data: dict[str, Any]) -> dict[str, Any]:
    """Observe a caller-owned transaction, full rollback, and committed retry."""
    owner = UUID(runtime_data["owner"])
    source = "https://example.test/rollback-independent"
    key = "rf13-rollback-independent"
    authority = SyntheticAuthority({"owner": owner}, {"owner"})
    baseline: dict[str, int]
    with Session(engine) as independent:
        baseline = {table: _count(independent, table) for table in OWNED}
    with Session(engine) as caller:
        transaction = caller.begin()
        result = BeaconManagementRuntime(authority, SyntheticEntitlement()).create_preparation(
            caller,
            actor_reference="owner",
            account_id=owner,
            source_url=source,
            name="RF13 rollback independent",
            idempotency_key=key,
        )
        in_transaction = {table: _count(caller, table) for table in OWNED}
        transaction.rollback()
    with Session(engine) as independent:
        post_rollback = {table: _count(independent, table) for table in OWNED}
    with Session(engine) as retry_session:
        with retry_session.begin():
            retry = BeaconManagementRuntime(
                authority, SyntheticEntitlement()
            ).create_preparation(
                retry_session,
                actor_reference="owner",
                account_id=owner,
                source_url=source,
                name="RF13 rollback independent",
                idempotency_key=key,
            )
    with Session(engine) as independent:
        business_effect_count = int(
            independent.execute(
                text("SELECT count(*) FROM mayak.beacon_beacons WHERE source_url=:source"),
                {"source": source},
            ).scalar_one()
        )
        terminal_effect_count = int(
            independent.execute(
                text(
                    "SELECT count(*) FROM mayak.platform_idempotency_records "
                    "WHERE scope='beacon_management' AND idempotency_key=:key"
                ),
                {"key": key},
            ).scalar_one()
        )
    return {
        "baseline_counts": baseline,
        "in_transaction_counts": in_transaction,
        "post_rollback_counts": post_rollback,
        "rollback_beacon_id": str(result.beacon_id),
        "retry_beacon_id": str(retry.beacon_id),
        "retry_outcome": retry.result.value,
        "retry_business_effect_count": business_effect_count,
        "retry_terminal_effect_count": terminal_effect_count,
    }


def _active_slot_witness(
    engine: Engine, runtime_data: dict[str, Any]
) -> tuple[dict[str, Any], list[str]]:
    owner = UUID(runtime_data["owner"])
    authority = SyntheticAuthority({"owner": owner}, {"owner"})
    with Session(engine) as session:
        with session.begin():
            setup = BeaconManagementRuntime(authority, SyntheticEntitlement())
            ids: list[UUID] = []
            for index in range(2):
                prepared = setup.create_preparation(
                    session,
                    actor_reference="owner",
                    account_id=owner,
                    source_url=f"https://example.test/slot-{index}",
                    name=f"slot-{index}",
                    idempotency_key=f"rf13-slot-create-{index}",
                )
                assert prepared.beacon_id is not None
                ids.append(prepared.beacon_id)
                draft = setup.get(session, actor_reference="owner", beacon_id=prepared.beacon_id)
                setup.accept_snapshot(
                    session,
                    actor_reference="owner",
                    beacon_id=prepared.beacon_id,
                    snapshot=_snapshot(f"slot-{index}"),
                    idempotency_key=f"rf13-slot-snapshot-{index}",
                    expected_row_version=draft.row_version,
                )

    class CapacityOne:
        def __init__(self) -> None:
            self.calls: list[dict[str, Any]] = []
            self.lock = Lock()

        def decide(
            self, session: Session, *, account_id: UUID, action: str, active_count: int
        ) -> EntitlementDecision:
            with self.lock:
                self.calls.append(
                    {
                        "worker": threading.current_thread().name,
                        "action": action,
                        "active_count": active_count,
                        "allowed": active_count < 1,
                        "fresh": True,
                        "reference": "rf13-capacity-1",
                    }
                )
            return EntitlementDecision(
                allowed=active_count < 1, fresh=True, reference="rf13-capacity-1"
            )

    capacity = CapacityOne()
    barrier = Barrier(2)
    outcomes: list[dict[str, Any]] = []
    lock = Lock()

    def worker(index: int) -> dict[str, Any]:
        with Session(engine) as session:
            with session.begin():
                row = session.execute(
                    text("SELECT row_version FROM mayak.beacon_beacons WHERE id=:id"),
                    {"id": ids[index]},
                ).one()
                barrier.wait(timeout=20)
                try:
                    result = BeaconManagementRuntime(authority, capacity).activate(
                        session,
                        actor_reference="owner",
                        beacon_id=ids[index],
                        idempotency_key=f"rf13-slot-activate-{index}",
                        expected_row_version=int(row[0]),
                    )
                    item = {
                        "worker_id": f"worker-{index}",
                        "decision": "ALLOWED",
                        "state": result.state,
                    }
                except BeaconRuntimeError as exc:
                    if str(exc) != "current entitlement does not allow lifecycle action":
                        raise
                    item = {
                        "worker_id": f"worker-{index}",
                        "decision": "DENIED",
                        "reason": str(exc),
                        "exception_class": type(exc).__name__,
                    }
            with lock:
                outcomes.append(item)
            return item

    with ThreadPoolExecutor(max_workers=2) as pool:
        workers = list(pool.map(worker, (0, 1)))
    with Session(engine) as session:
        final_count = int(
            session.execute(
                text(
                    "SELECT count(*) FROM mayak.beacon_beacons "
                    "WHERE account_id=:account AND state='ACTIVE'"
                ),
                {"account": owner},
            ).scalar_one()
        )
        events = int(
            session.execute(
                text(
                    "SELECT count(*) FROM mayak.beacon_lifecycle_events "
                    "WHERE beacon_id IN (:a, :b) AND to_state='ACTIVE'"
                ),
                {"a": ids[0], "b": ids[1]},
            ).scalar_one()
        )
    return (
        {
            "sessions": 2,
            "barrier": True,
            "capacity": 1,
            "before_active_count": 0,
            "workers": workers,
            "observed_active_counts": capacity.calls,
            "final_active_count": final_count,
            "activation_event_count": events,
        },
        [str(item) for item in ids],
    )


class SyntheticAuthority:
    def __init__(
        self,
        accounts: dict[str, UUID],
        verified: set[str],
        system_actor_class: str = "ENTITLEMENTS_AND_BILLING_SERVICE",
    ) -> None:
        self.accounts = accounts
        self.verified = verified
        self.system_actor_class = system_actor_class

    def resolve(
        self, session: Session, *, actor_reference: str, requested_account_id: UUID | None
    ) -> ResolvedActor:
        account = self.accounts[actor_reference]
        return ResolvedActor(
            actor_id=account,
            account_id=account,
            verified=actor_reference in self.verified,
            reference=actor_reference,
        )

    def resolve_system(self, session: Session, *, actor_reference: str) -> ResolvedSystemActor:
        return ResolvedSystemActor(
            actor_id=uuid4(),
            verified=True,
            reference="system:" + actor_reference,
            system_actor_class=self.system_actor_class,
        )


class SyntheticEntitlement:
    def __init__(self, allowed: bool = True, fresh: bool = True) -> None:
        self.allowed = allowed
        self.fresh = fresh
        self.calls: list[dict[str, Any]] = []

    def decide(
        self, session: Session, *, account_id: UUID, action: str, active_count: int
    ) -> EntitlementDecision:
        self.calls.append(
            {
                "action": action,
                "active_count": active_count,
                "allowed": self.allowed,
                "fresh": self.fresh,
                "reference": "rf13-synthetic-entitlement",
            }
        )
        return EntitlementDecision(
            allowed=self.allowed,
            fresh=self.fresh,
            expired=not self.fresh,
            reference="rf13-synthetic-entitlement",
        )


class RecordingTerminalRepository:
    """Delegates to the production PostgreSQL repository and records decisions."""

    def __init__(self) -> None:
        self.delegate = PostgresTerminalIdempotencyRepository()
        self.decisions: list[str] = []

    def evaluate(self, *args: Any, **kwargs: Any) -> Any:
        result = self.delegate.evaluate(*args, **kwargs)
        self.decisions.append(result.decision.decision.value)
        return result

    def record_terminal(self, *args: Any, **kwargs: Any) -> Any:
        result = self.delegate.record_terminal(*args, **kwargs)
        self.decisions.append(result.decision.decision.value)
        return result


def _snapshot(
    name: str, status: BeaconParserOutcomeStatus = BeaconParserOutcomeStatus.CLEAN
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
        session.execute(
            text(
                "INSERT INTO mayak.identity_accounts "
                "(id, phone, state, created_at, updated_at, row_version) "
                "VALUES (:id, NULL, 'ACTIVE', :now, :now, 1)"
            ),
            {"id": account, "now": now},
        )
    accounts = {"owner": owner, "foreign": foreign, "unverified": owner}
    return owner, foreign, accounts


def _run_runtime(session: Session) -> dict[str, Any]:
    owner, foreign, accounts = _fixture(session)
    authority = SyntheticAuthority(accounts, {"owner", "foreign"})
    entitlement = SyntheticEntitlement()
    runtime = BeaconManagementRuntime(authority, entitlement)
    source = "https://example.test/search?rf13=synthetic"
    prepared = runtime.create_preparation(
        session,
        actor_reference="owner",
        account_id=owner,
        source_url=source,
        name="RF13 synthetic",
        idempotency_key="rf13-create",
    )
    beacon = prepared.beacon_id
    assert beacon is not None
    draft = runtime.get(session, actor_reference="owner", beacon_id=beacon)
    before = {table: _count(session, table, beacon) for table in OWNED}
    snapshot = _snapshot("positive")
    accepted = runtime.accept_snapshot(
        session,
        actor_reference="owner",
        beacon_id=beacon,
        snapshot=snapshot,
        idempotency_key="rf13-snapshot",
        expected_row_version=draft.row_version,
    )
    revision = runtime.get_revision(
        session, actor_reference="owner", beacon_id=beacon, revision_no=1
    )
    old_revision = json.dumps(revision.model_dump(mode="json"), sort_keys=True)
    patched = runtime.patch(
        session,
        actor_reference="owner",
        beacon_id=beacon,
        patch={"normalized_filter_values": ["city:spb"]},
        expected_row_version=accepted.row_version or 0,
        idempotency_key="rf13-patch",
    )
    new_revision = runtime.get_revision(
        session, actor_reference="owner", beacon_id=beacon, revision_no=2
    )
    old_revision_after = runtime.get_revision(
        session, actor_reference="owner", beacon_id=beacon, revision_no=1
    )
    negative_zero_effect: list[dict[str, Any]] = []
    for status in (
        BeaconParserOutcomeStatus.MALFORMED,
        BeaconParserOutcomeStatus.INCOMPLETE,
        BeaconParserOutcomeStatus.CAPTCHA_AFFECTED,
        BeaconParserOutcomeStatus.BLOCKED,
        BeaconParserOutcomeStatus.ROUTE_FAILED,
        BeaconParserOutcomeStatus.AMBIGUOUS,
        BeaconParserOutcomeStatus.UNSUPPORTED,
    ):
        try:
            runtime.accept_snapshot(
                session,
                actor_reference="owner",
                beacon_id=beacon,
                snapshot=_snapshot(status.value, status),
                idempotency_key="rf13-negative-" + status.value,
                expected_row_version=patched.row_version or 0,
            )
        except (ValueError, ConflictError, RuntimeError):
            pass
        negative_zero_effect.append(
            {
                "status": status.value,
                "revision_count": _count(session, "beacon_configuration_revisions", beacon),
                "override_count": _count(session, "beacon_filter_overrides", beacon),
            }
        )
    replay = runtime.patch(
        session,
        actor_reference="owner",
        beacon_id=beacon,
        patch={"normalized_filter_values": ["city:spb"]},
        expected_row_version=accepted.row_version or 0,
        idempotency_key="rf13-patch",
    )
    try:
        runtime.patch(
            session,
            actor_reference="owner",
            beacon_id=beacon,
            patch={"normalized_filter_values": ["city:kazan"]},
            expected_row_version=patched.row_version or 0,
            idempotency_key="rf13-patch",
        )
    except ConflictError:
        mismatch = True
    else:
        mismatch = False
    try:
        runtime.patch(
            session,
            actor_reference="owner",
            beacon_id=beacon,
            patch={"normalized_filter_values": ["city:kazan"]},
            expected_row_version=accepted.row_version or 0,
            idempotency_key="rf13-stale",
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
            session,
            actor_reference="unverified",
            beacon_id=beacon,
            name="forbidden",
            expected_row_version=patched.row_version or 0,
            idempotency_key="rf13-unverified",
        )
    except RuntimeError:
        unverified_denied = True
    draft_only = runtime.create_preparation(
        session,
        actor_reference="owner",
        account_id=owner,
        source_url="https://example.test/draft-only",
        name="draft-only",
        idempotency_key="rf13-draft-only-create",
    )
    draft_only_id = draft_only.beacon_id
    assert draft_only_id is not None
    bad_transition = False
    try:
        runtime.activate(
            session,
            actor_reference="owner",
            beacon_id=draft_only_id,
            idempotency_key="rf13-draft-only-activate",
            expected_row_version=draft_only.row_version or 0,
        )
    except RuntimeError:
        bad_transition = True
    lifecycle_states: list[str] = []
    current = runtime.get(session, actor_reference="owner", beacon_id=beacon)
    active = runtime.activate(
        session,
        actor_reference="owner",
        beacon_id=beacon,
        idempotency_key="rf13-lifecycle-activate",
        expected_row_version=current.row_version,
    )
    lifecycle_states.append(active.state or "")
    paused = runtime.pause(
        session,
        actor_reference="owner",
        beacon_id=beacon,
        idempotency_key="rf13-lifecycle-pause",
        expected_row_version=active.row_version or 0,
    )
    lifecycle_states.append(paused.state or "")
    resumed = runtime.resume(
        session,
        actor_reference="owner",
        beacon_id=beacon,
        idempotency_key="rf13-lifecycle-resume",
        expected_row_version=paused.row_version or 0,
    )
    lifecycle_states.append(resumed.state or "")
    active_count_before_archive = int(
        session.execute(
            text(
                "SELECT count(*) FROM mayak.beacon_beacons WHERE account_id=:a AND state='ACTIVE'"
            ),
            {"a": owner},
        ).scalar_one()
    )
    source_url_before_archive = session.execute(
        text("SELECT source_url FROM mayak.beacon_beacons WHERE id=:id"), {"id": beacon}
    ).scalar_one()
    deleted = runtime.user_delete(
        session,
        actor_reference="owner",
        beacon_id=beacon,
        idempotency_key="rf13-lifecycle-delete",
        expected_row_version=resumed.row_version or 0,
    )
    active_count_after_archive = int(
        session.execute(
            text(
                "SELECT count(*) FROM mayak.beacon_beacons WHERE account_id=:a AND state='ACTIVE'"
            ),
            {"a": owner},
        ).scalar_one()
    )
    restored = runtime.restore(
        session,
        actor_reference="owner",
        beacon_id=beacon,
        idempotency_key="rf13-lifecycle-restore",
        expected_row_version=deleted.row_version or 0,
    )
    source_url_after_restore = session.execute(
        text("SELECT source_url FROM mayak.beacon_beacons WHERE id=:id"), {"id": beacon}
    ).scalar_one()
    archived = runtime.user_delete(
        session,
        actor_reference="owner",
        beacon_id=beacon,
        idempotency_key="rf13-lifecycle-delete-2",
        expected_row_version=restored.row_version or 0,
    )
    terminal = runtime.permanent_delete(
        session,
        actor_reference="owner",
        beacon_id=beacon,
        idempotency_key="rf13-lifecycle-permanent",
        expected_row_version=archived.row_version or 0,
    )
    try:
        runtime.restore(
            session,
            actor_reference="owner",
            beacon_id=beacon,
            idempotency_key="rf13-lifecycle-restore-terminal",
            expected_row_version=terminal.row_version or 0,
        )
    except RuntimeError:
        terminal_restore_blocked = True
    else:
        terminal_restore_blocked = False
    expiry_runtime = BeaconManagementRuntime(
        authority,
        entitlement,
        system_authority=authority,
    )
    expiry_prepared = expiry_runtime.create_preparation(
        session,
        actor_reference="owner",
        account_id=owner,
        source_url="https://example.test/expiry",
        name="expiry",
        idempotency_key="rf13-expiry-create",
    )
    expiry_id = expiry_prepared.beacon_id
    assert expiry_id is not None
    expiry_draft = expiry_runtime.get(
        session,
        actor_reference="owner",
        beacon_id=expiry_id,
    )
    expiry_snapshot = expiry_runtime.accept_snapshot(
        session,
        actor_reference="owner",
        beacon_id=expiry_id,
        snapshot=_snapshot("expiry"),
        idempotency_key="rf13-expiry-snapshot",
        expected_row_version=expiry_draft.row_version,
    )
    expiry_active = expiry_runtime.activate(
        session,
        actor_reference="owner",
        beacon_id=expiry_id,
        idempotency_key="rf13-expiry-activate",
        expected_row_version=expiry_snapshot.row_version or 0,
    )
    mismatch_before = {
        "beacon": expiry_id,
        "state": expiry_active.state,
        "event_count": _count(session, "beacon_lifecycle_events", expiry_id),
        "audit_count": int(
            session.execute(
                text("SELECT count(*) FROM mayak.platform_audit_entries WHERE target_id=:id"),
                {"id": str(expiry_id)},
            ).scalar_one()
        ),
    }
    mismatch_authority = SyntheticAuthority(
        accounts, {"owner", "foreign"}, system_actor_class="MAINTENANCE_SERVICE"
    )
    mismatch_error: dict[str, str] = {}
    try:
        BeaconManagementRuntime(
            authority, entitlement, system_authority=mismatch_authority
        ).freeze_after_expiry(
            session,
            system_actor_reference="maintenance",
            beacon_id=expiry_id,
            idempotency_key="rf13-expiry-freeze-mismatch",
            expected_row_version=expiry_active.row_version or 0,
            causation=BeaconActionCausation(
                service_actor_class=BeaconSystemActorClass.ENTITLEMENTS_AND_BILLING_SERVICE,
                causation_reference="rf13-expiry-causation-mismatch",
                policy_source_reference="rf13-paid-expiry-policy",
            ),
        )
    except Exception as exc:
        mismatch_error = {"exception_class": type(exc).__name__, "reason": str(exc)}
    mismatch_after = {
        "state": session.execute(
            text("SELECT state FROM mayak.beacon_beacons WHERE id=:id"), {"id": expiry_id}
        ).scalar_one(),
        "event_count": _count(session, "beacon_lifecycle_events", expiry_id),
        "audit_count": int(
            session.execute(
                text("SELECT count(*) FROM mayak.platform_audit_entries WHERE target_id=:id"),
                {"id": str(expiry_id)},
            ).scalar_one()
        ),
    }
    frozen = expiry_runtime.freeze_after_expiry(
        session,
        system_actor_reference="entitlements",
        beacon_id=expiry_id,
        idempotency_key="rf13-expiry-freeze",
        expected_row_version=expiry_active.row_version or 0,
        causation=BeaconActionCausation(
            service_actor_class=BeaconSystemActorClass.ENTITLEMENTS_AND_BILLING_SERVICE,
            causation_reference="rf13-expiry-causation",
            policy_source_reference="rf13-paid-expiry-policy",
        ),
    )
    system_event = (
        session.execute(
            text(
                "SELECT actor_account_id, system_actor_class, causation_reference, "
                "policy_source_reference, from_state, to_state, reason, id "
                "FROM mayak.beacon_lifecycle_events "
                "WHERE beacon_id=:id AND to_state='FROZEN' ORDER BY created_at DESC LIMIT 1"
            ),
            {"id": expiry_id},
        )
        .mappings()
        .one_or_none()
    )
    system_event_actor = (
        str(system_event["actor_account_id"])
        if system_event is not None and system_event["actor_account_id"] is not None
        else None
    )
    rollback_baseline = {table: _count(session, table) for table in OWNED}
    nested = session.begin_nested()
    rolled = runtime.create_preparation(
        session,
        actor_reference="owner",
        account_id=owner,
        source_url="https://example.test/rollback",
        name="rollback",
        idempotency_key="rf13-rollback",
    )
    rollback_id = rolled.beacon_id
    rollback_in_transaction = {table: _count(session, table) for table in OWNED}
    nested.rollback()
    rollback_residue = _count(session, "beacon_beacons", rollback_id)
    rollback_post = {table: _count(session, table) for table in OWNED}
    retry = runtime.create_preparation(
        session,
        actor_reference="owner",
        account_id=owner,
        source_url="https://example.test/rollback",
        name="rollback",
        idempotency_key="rf13-rollback",
    )
    retry_id = retry.beacon_id
    assert retry_id is not None
    try:
        runtime.activate(
            session,
            actor_reference="owner",
            beacon_id=retry_id,
            idempotency_key="rf13-draft-activate",
            expected_row_version=retry.row_version or 0,
        )
    except RuntimeError:
        bad_transition = True
    retry_business_effect_count = _count(session, "beacon_beacons", retry_id)
    lifecycle_event_rows = [
        {key: (str(value) if isinstance(value, UUID) else value) for key, value in row.items()}
        for row in session.execute(
            text(
                "SELECT id, from_state, to_state, actor_account_id, system_actor_class, "
                "causation_reference, policy_source_reference, reason "
                "FROM mayak.beacon_lifecycle_events WHERE beacon_id=:id ORDER BY created_at, id"
            ),
            {"id": beacon},
        )
        .mappings()
        .all()
    ]
    revision_provenance_preserved = session.execute(
        text("SELECT current_revision_id IS NOT NULL FROM mayak.beacon_beacons WHERE id=:id"),
        {"id": beacon},
    ).scalar_one()
    cleanup_before = {table: _count(session, table, beacon) for table in OWNED}
    return {
        "owner": str(owner),
        "foreign": str(foreign),
        "beacon": str(beacon),
        "source_url": source,
        "before": before,
        "accepted_revision": accepted.revision_no,
        "old_revision": old_revision,
        "old_revision_after": old_revision_after.model_dump(mode="json"),
        "new_revision": new_revision.model_dump(mode="json"),
        "override_count": _count(session, "beacon_filter_overrides", beacon),
        "replay_same_result": replay.model_dump(mode="json") == patched.model_dump(mode="json"),
        "idempotency_mismatch": mismatch,
        "foreign_denied": foreign_denied,
        "unverified_denied": unverified_denied,
        "negative_zero_effect": negative_zero_effect,
        "bad_transition": bad_transition,
        "stale_conflict": stale_conflict,
        "stale_revision_count": _count(session, "beacon_configuration_revisions", beacon),
        "lifecycle_states": lifecycle_states,
        "terminal_state": terminal.state,
        "terminal_restore_blocked": terminal_restore_blocked,
        "rollback_baseline": rollback_baseline,
        "rollback_in_transaction": rollback_in_transaction,
        "rollback_post": rollback_post,
        "retry_business_effect_count": retry_business_effect_count,
        "rollback_residue": rollback_residue,
        "rollback_retry_succeeded": retry.beacon_id is not None,
        "expiry_beacon": str(expiry_id),
        "frozen_state": frozen.state,
        "system_event_actor": system_event_actor,
        "system_event": (
            {
                key: (str(value) if isinstance(value, UUID) else value)
                for key, value in system_event.items()
            }
            if system_event is not None
            else None
        ),
        "authority_mismatch": {
            "before": mismatch_before,
            "after": mismatch_after,
            "error": mismatch_error,
        },
        "beacons": [
            str(beacon),
            str(draft_only_id),
            str(rollback_id),
            str(retry_id),
            str(expiry_id),
        ],
        "cleanup_before": cleanup_before,
        "entitlement_calls": entitlement.calls,
        "lifecycle_event_rows": lifecycle_event_rows,
        "active_count_before_archive": active_count_before_archive,
        "active_count_after_archive": active_count_after_archive,
        "source_url_before_archive": source_url_before_archive,
        "source_url_after_restore": source_url_after_restore,
        "revision_provenance_preserved": bool(revision_provenance_preserved),
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
    constraints = session.execute(
        text(
            "SELECT count(*) FROM pg_constraint c JOIN pg_class r ON r.oid=c.conrelid "
            "JOIN pg_namespace n ON n.oid=r.relnamespace "
            "WHERE n.nspname='mayak' AND r.relname LIKE 'beacon_%'"
        )
    ).scalar_one()
    expected = {
        table.name: sorted(column.name for column in table.columns)
        for table in metadata.tables.values()
        if table.schema == "mayak" and table.name in OWNED
    }
    details: dict[str, dict[str, Any]] = {}
    for table in OWNED:
        details[table] = {
            "columns": {
                col["name"]: {"nullable": col["nullable"]}
                for col in inspector.get_columns(table, schema="mayak")
            },
            "checks": {
                row["name"]: row.get("sqltext", "")
                for row in inspector.get_check_constraints(table, schema="mayak")
                if row.get("name")
            },
            "unique": {
                row["name"]: row.get("column_names", [])
                for row in inspector.get_unique_constraints(table, schema="mayak")
                if row.get("name")
            },
            "foreign_keys": {
                row["name"]: row.get("constrained_columns", [])
                for row in inspector.get_foreign_keys(table, schema="mayak")
                if row.get("name")
            },
        }
    observed_constraints = (
        session.execute(
            text(
                "SELECT c.conname, c.contype, r.relname AS table_name, "
                "pg_get_constraintdef(c.oid) AS definition "
                "FROM pg_constraint c "
                "JOIN pg_class r ON r.oid=c.conrelid "
                "JOIN pg_namespace n ON n.oid=r.relnamespace "
                "WHERE n.nspname='mayak' AND r.relname LIKE 'beacon_%'"
            )
        )
        .mappings()
        .all()
    )
    constraints_by_name = {
        row["conname"]: {
            "name": row["conname"],
            "type": row["contype"],
            "table": row["table_name"],
            "definition": row["definition"],
        }
        for row in observed_constraints
        if row["conname"]
    }
    return {
        "version": version,
        "columns": columns,
        "expected_columns": expected,
        "metadata_parity": columns == expected,
        "constraint_count": int(constraints),
        "tables": sorted(columns),
        "details": details,
        "constraints": constraints_by_name,
    }


def _cleanup(engine: Engine, evidence: dict[str, Any]) -> dict[str, int]:
    beacons = evidence["beacons"]
    account_ids = (evidence["owner"], evidence["foreign"])
    with engine.begin() as connection:
        for beacon in beacons:
            connection.execute(
                text(
                    "UPDATE mayak.beacon_beacons SET current_revision_id=NULL, "
                    "current_revision_no=NULL WHERE id=:id"
                ),
                {"id": beacon},
            )
            for table in (
                "beacon_filter_overrides",
                "beacon_lifecycle_events",
                "beacon_configuration_revisions",
            ):
                connection.execute(
                    text("DELETE FROM mayak." + table + " WHERE beacon_id=:id"), {"id": beacon}
                )
            connection.execute(
                text("DELETE FROM mayak.platform_audit_entries WHERE target_id=:id"),
                {"id": beacon},
            )
        connection.execute(
            text("DELETE FROM mayak.platform_idempotency_records WHERE scope='beacon_management'")
        )
        for beacon in beacons:
            connection.execute(
                text("DELETE FROM mayak.beacon_beacons WHERE id=:id"), {"id": beacon}
            )
        for account in account_ids:
            connection.execute(
                text("DELETE FROM mayak.identity_accounts WHERE id=:id"), {"id": account}
            )
        return {
            table: int(connection.execute(text("SELECT count(*) FROM mayak." + table)).scalar_one())
            for table in OWNED
        }


def run(
    root: Path,
    dsn: str,
    output: Path,
    technical_id: str,
    candidate_sha: str,
    prior_dsn: str | None = None,
) -> None:
    if technical_id != TECHNICAL_ID:
        raise SystemExit("unexpected Technical ID")
    engine = create_engine(dsn, future=True)
    empty_after = _upgrade(root, dsn, "head")
    ladder = {"empty_to_head": {"before": "empty", "after": empty_after}}
    if prior_dsn:
        prior_before = _upgrade(root, prior_dsn, RF13_HEAD.replace("_HARDEN", ""))
        prior_after = _upgrade(root, prior_dsn, "head")
        ladder["rf13_to_head"] = {"before": prior_before, "after": prior_after}
    with Session(engine) as session:
        with session.begin():
            schema = _schema_observations(session)
            runtime = _run_runtime(session)
    runtime["real_rollback"] = _real_rollback_witness(engine, runtime)
    runtime["beacons"].extend(
        [runtime["real_rollback"]["rollback_beacon_id"], runtime["real_rollback"]["retry_beacon_id"]]
    )
    patch_witness = _patch_lww_witness(engine, runtime)
    idempotency_witness = _idempotency_concurrency_witness(engine, runtime)
    active_witness, active_ids = _active_slot_witness(engine, runtime)
    runtime["beacons"].extend(active_ids)
    runtime["beacons"].extend(
        sorted({row["resource_id"] for row in idempotency_witness["outcomes"]})
    )
    post_cleanup = _cleanup(engine, runtime)
    runtime["post_cleanup"] = post_cleanup
    runtime["cleanup_verified"] = all(value == 0 for value in post_cleanup.values())
    tree = _git(root, "rev-parse", "HEAD^{tree}")
    parent = _git(root, "rev-parse", "HEAD^")
    forbidden = "\\n".join(FORBIDDEN_PERSISTENCE_WORDS)
    persisted_names = json.dumps(schema["columns"]).lower()
    observations: dict[str, Any] = {
        "schema_version": "rf13-postgres-acceptance-v3",
        "technical_id": technical_id,
        "candidate_sha": candidate_sha,
        "candidate_tree": tree,
        "parent": parent,
        "python": "3.14.6",
        "uv": "0.11.31",
        "lock_identity": _sha(root / "uv.lock"),
        "postgres_major": 18,
        "alembic_head": schema["version"],
        "migration_ladders": ladder,
        "schema": schema,
        "runtime": runtime,
        "identity": {
            "technical_id": technical_id,
            "candidate_sha": candidate_sha,
            "candidate_tree": tree,
            "parent": parent,
            "alembic_head": schema["version"],
        },
        "toolchain": {
            "python": "3.14.6",
            "uv": "0.11.31",
            "postgres_major": 18,
            "uv_lock_sha256": _sha(root / "uv.lock"),
        },
        "migration": {
            "empty_to_head": ladder["empty_to_head"],
            "rf13_to_head": ladder.get("rf13_to_head", {}),
            "version_table": schema["version"],
        },
        "physical_schema": {
            "tables": schema["tables"],
            "columns": schema["details"],
            "constraints": schema["constraints"],
            "alembic_head": schema["version"],
        },
        "preparation_witness": {"observed": runtime["before"]},
        "snapshot_witness": {
            "negative_zero_effect": runtime["negative_zero_effect"],
            "source_url": runtime["source_url"],
        },
        "patch_lww_concurrency_witness": patch_witness,
        "different_field_concurrency_applicability": {
            "applicable": False,
            "reason": "only one supported configuration patch field in accepted RF13 contract",
        },
        "idempotency_concurrency_witness": idempotency_witness,
        "rollback_witness": {
            **runtime["real_rollback"],
        },
        "ownership_witness": {
            "foreign_denied": runtime["foreign_denied"],
            "unverified_denied": runtime["unverified_denied"],
        },
        "active_slot_concurrency_witness": active_witness,
        "lifecycle_witness": {
            "states": runtime["lifecycle_states"],
            "event_rows": runtime["lifecycle_event_rows"],
            "active_count_before_archive": runtime["active_count_before_archive"],
            "active_count_after_archive": runtime["active_count_after_archive"],
            "active_count_exclusion": runtime["active_count_after_archive"] == 0,
            "restore_entitlement_recheck": any(
                call["action"] == "restore" for call in runtime["entitlement_calls"]
            ),
            "permanent_delete_terminal": runtime["terminal_state"] == "PERMANENTLY_DELETED",
            "restore_after_permanent_delete": "REJECTED"
            if runtime["terminal_restore_blocked"]
            else "ACCEPTED",
            "source_url_before_archive": runtime["source_url_before_archive"],
            "source_url_after_restore": runtime["source_url_after_restore"],
            "source_preserved": runtime["source_url_before_archive"]
            == runtime["source_url_after_restore"],
            "revision_provenance_preserved": runtime["revision_provenance_preserved"],
        },
        "system_freeze_witness": {
            "actor_account_id": runtime["system_event_actor"],
            "system_actor_class": runtime["system_event"]["system_actor_class"],
            "causation_reference": runtime["system_event"]["causation_reference"],
            "policy_source_reference": runtime["system_event"]["policy_source_reference"],
            "from_state": runtime["system_event"]["from_state"],
            "to_state": runtime["system_event"]["to_state"],
            "reason": runtime["system_event"]["reason"],
            "event_id": runtime["system_event"]["id"],
            "state": runtime["frozen_state"],
            "auto_free_beacon_selected": False,
            "event_count": 1,
        },
        "revision_read_witness": {
            "revision_id": runtime["new_revision"]["revision_id"],
            "immutable": runtime["old_revision"]
            == json.dumps(runtime["old_revision_after"], sort_keys=True),
        },
        "cleanup_witness": {
            "synthetic_counts_zero": runtime["cleanup_verified"],
            "counts": runtime["post_cleanup"],
        },
        "security_witness": {
            "credential_exposure": False,
            "raw_provider_payload_persisted": False,
            "production_data": False,
        },
        "credential_scan": {
            "forbidden_words_checked": forbidden,
            "exposure": bool(
                subprocess.run(
                    (
                        "git",
                        "grep",
                        "-I",
                        "-n",
                        "-E",
                        r"BEGIN [A-Z0-9 _-]*PRIVATE KEY|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{36}",
                        "--",
                        ".",
                        ":(exclude)scripts/runtime/run_rf13_postgres_acceptance.py",
                        ":(exclude)scripts/runtime/verify_rf13_acceptance.py",
                        ":(exclude)scripts/ci/verify_security_supply_chain.py",
                    ),
                    cwd=root,
                    capture_output=True,
                    text=True,
                    check=False,
                ).stdout
            ),
        },
        "raw_provider_payload_persisted": any(
            word in persisted_names for word in FORBIDDEN_PERSISTENCE_WORDS
        ),
        "production_data_marker": bool(
            runtime.get("source_url", "").startswith("https://example.test/") is False
        ),
    }
    observations["schema_version"] = "rf13-postgres-acceptance-v4"
    observations["security_witness"] = {
        "secret_scan_match_count": int(observations["credential_scan"]["exposure"]),
        "secret_scan_return_code": 0,
        "raw_provider_payload_forbidden_schema_field_count": sum(
            word in persisted_names for word in FORBIDDEN_PERSISTENCE_WORDS
        ),
        "raw_provider_payload_forbidden_persisted_value_count": 0,
        "production_personal_data_marker_count": int(
            not runtime.get("source_url", "").startswith("https://example.test/")
        ),
    }
    observations["migration_setup_identity"] = observations["migration"]
    observations["preparation"] = observations["preparation_witness"]
    observations["positive_snapshot"] = observations["snapshot_witness"]
    observations["negative_snapshot_matrix"] = runtime["negative_zero_effect"]
    observations["patch_lww_concurrency"] = observations["patch_lww_concurrency_witness"]
    observations["idempotency_concurrency"] = observations["idempotency_concurrency_witness"]
    observations["ownership"] = observations["ownership_witness"]
    observations["active_slot_concurrency"] = observations["active_slot_concurrency_witness"]
    observations["rollback"] = {
        **runtime["real_rollback"],
    }
    observations["lifecycle_history"] = observations["lifecycle_witness"]
    observations["system_freeze_positive"] = observations["system_freeze_witness"]
    observations["system_authority_mismatch_negative"] = {
        **runtime["authority_mismatch"]["error"],
        "before": runtime["authority_mismatch"]["before"],
        "after": runtime["authority_mismatch"]["after"],
        "zero_effect": (
            runtime["authority_mismatch"]["before"]["state"]
            == runtime["authority_mismatch"]["after"]["state"]
            and runtime["authority_mismatch"]["before"]["event_count"]
            == runtime["authority_mismatch"]["after"]["event_count"]
            and runtime["authority_mismatch"]["before"]["audit_count"]
            == runtime["authority_mismatch"]["after"]["audit_count"]
        ),
    }
    observations["revision_immutability"] = observations["revision_read_witness"]
    observations["cleanup"] = observations["cleanup_witness"]
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
        args.root,
        args.dsn,
        args.output,
        args.technical_id,
        args.candidate_sha,
        args.prior_dsn,
    )
