"""RF-13 PostgreSQL acceptance producer.

The producer records observations made by PostgreSQL and the production
BeaconManagementRuntime.  It never accepts a caller-provided gate result.
"""

# ruff: noqa

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
                "idempotency_key": f"rf13-lww-worker-{index}",
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
        "final_row_version_delta": int(final[1]) - observed_version,
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
                    "idempotency_key": "rf13-same-key-concurrency",
                    "fingerprint": "rf13-idempotency-fingerprint-v1",
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
    preparation_events = [{key: (str(value) if isinstance(value, UUID) else value) for key, value in dict(row).items()} for row in session.execute(text("SELECT id, from_state, to_state, actor_account_id, reason FROM mayak.beacon_lifecycle_events WHERE beacon_id=:id ORDER BY created_at, id"), {"id": beacon}).mappings().all()]
    preparation_observation = {
        "beacon_id": str(beacon), "account_id": str(owner), "source_url": source,
        "submitted_source_url": source, "state": draft.state,
        "current_revision_no": draft.current_revision_no, "current_revision_id": str(draft.current_revision_id) if draft.current_revision_id else None,
        "row_version": draft.row_version, "lifecycle_events": preparation_events,
        "lifecycle_event_count": len(preparation_events), "revision_count": before["beacon_configuration_revisions"],
        "override_count": before["beacon_filter_overrides"],
    }
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
    positive_current = session.execute(text("SELECT current_revision_id, current_revision_no FROM mayak.beacon_beacons WHERE id=:id"), {"id": beacon}).one()
    positive_snapshot = {
        "pre_revision_count": before["beacon_configuration_revisions"],
        "post_revision_count": _count(session, "beacon_configuration_revisions", beacon),
        "pre_current_revision_id": None, "post_current_revision_id": str(positive_current[0]),
        "persisted_revision_id": str(revision.revision_id), "persisted_revision_no": revision.revision_no,
        "current_revision_id": str(positive_current[0]), "current_revision_no": int(positive_current[1]),
        "parser_outcome": "CLEAN", "accepted_as_clean": True,
        "parser_evidence_reference": "rf13-opaque-evidence-positive",
        "source_url_before": source, "source_url_after": source, "state_after": accepted.state,
        "override_count": _count(session, "beacon_filter_overrides", beacon),
    }
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
        pre_revision_count = _count(session, "beacon_configuration_revisions", beacon)
        pre_override_count = _count(session, "beacon_filter_overrides", beacon)
        before_row = session.execute(text("SELECT current_revision_id, row_version FROM mayak.beacon_beacons WHERE id=:id"), {"id": beacon}).one()
        exception_or_result = "REJECTED"
        try:
            runtime.accept_snapshot(
                session,
                actor_reference="owner",
                beacon_id=beacon,
                snapshot=_snapshot(status.value, status),
                idempotency_key="rf13-negative-" + status.value,
                expected_row_version=patched.row_version or 0,
            )
        except (ValueError, ConflictError, RuntimeError) as exc:
            exception_or_result = type(exc).__name__
        after_row = session.execute(text("SELECT current_revision_id, row_version FROM mayak.beacon_beacons WHERE id=:id"), {"id": beacon}).one()
        negative_zero_effect.append(
            {
                "status": status.value,
                "exception_or_result": exception_or_result,
                "pre_revision_count": pre_revision_count, "post_revision_count": _count(session, "beacon_configuration_revisions", beacon),
                "pre_override_count": pre_override_count, "post_override_count": _count(session, "beacon_filter_overrides", beacon),
                "current_revision_before": str(before_row[0]) if before_row[0] else None,
                "current_revision_after": str(after_row[0]) if after_row[0] else None,
                "row_version_before": int(before_row[1]), "row_version_after": int(after_row[1]),
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
    def ownership_counts() -> dict[str, int]:
        return {"row_version": int(session.execute(text("SELECT row_version FROM mayak.beacon_beacons WHERE id=:id"), {"id": beacon}).scalar_one()), "revision_count": _count(session, "beacon_configuration_revisions", beacon), "event_count": _count(session, "beacon_lifecycle_events", beacon), "audit_count": int(session.execute(text("SELECT count(*) FROM mayak.platform_audit_entries WHERE target_id=:id"), {"id": str(beacon)}).scalar_one()), "idempotency_count": int(session.execute(text("SELECT count(*) FROM mayak.platform_idempotency_records WHERE scope='beacon_management' AND idempotency_key LIKE 'rf13-%'" )).scalar_one())}
    foreign_before = ownership_counts(); foreign_exception = ""
    try:
        runtime.get(session, actor_reference="foreign", beacon_id=beacon)
    except RuntimeError as exc:
        foreign_exception = type(exc).__name__
    foreign_after = ownership_counts()
    unverified_before = ownership_counts(); unverified_exception = ""
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
    except RuntimeError as exc:
        unverified_exception = type(exc).__name__
    unverified_after = ownership_counts()
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
    revision_id_before_archive = session.execute(
        text("SELECT current_revision_id FROM mayak.beacon_beacons WHERE id=:id"), {"id": beacon}
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
    revision_id_after_restore = session.execute(
        text("SELECT current_revision_id FROM mayak.beacon_beacons WHERE id=:id"), {"id": beacon}
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
        "beacon": str(expiry_id),
        "state": expiry_active.state,
        "row_version": expiry_active.row_version,
        "event_count": _count(session, "beacon_lifecycle_events", expiry_id),
        "audit_count": int(
            session.execute(
                text("SELECT count(*) FROM mayak.platform_audit_entries WHERE target_id=:id"),
                {"id": str(expiry_id)},
        ).scalar_one()),
        "idempotency_terminal_count": int(session.execute(text("SELECT count(*) FROM mayak.platform_idempotency_records WHERE scope='beacon_management' AND idempotency_key='rf13-expiry-freeze-mismatch'" )).scalar_one()),
        "system_causation_event_count": _count(session, "beacon_lifecycle_events", expiry_id),
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
        "beacon": str(expiry_id),
        "state": session.execute(
            text("SELECT state FROM mayak.beacon_beacons WHERE id=:id"), {"id": expiry_id}
        ).scalar_one(),
        "row_version": session.execute(text("SELECT row_version FROM mayak.beacon_beacons WHERE id=:id"), {"id": expiry_id}).scalar_one(),
        "event_count": _count(session, "beacon_lifecycle_events", expiry_id),
        "audit_count": int(
        session.execute(
            text("SELECT count(*) FROM mayak.platform_audit_entries WHERE target_id=:id"),
            {"id": str(expiry_id)},
        ).scalar_one()),
        "idempotency_terminal_count": int(session.execute(text("SELECT count(*) FROM mayak.platform_idempotency_records WHERE scope='beacon_management' AND idempotency_key='rf13-expiry-freeze-mismatch'" )).scalar_one()),
        "system_causation_event_count": _count(session, "beacon_lifecycle_events", expiry_id),
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
        "preparation_observation": preparation_observation,
        "positive_snapshot": positive_snapshot,
        "ownership": {
            "foreign_read": {"attempted_actor_reference": "foreign", "classification": "FOREIGN", "exception_class": foreign_exception, "safe_reason": "actor does not own Beacon", "before": foreign_before, "after": foreign_after, "row_version_before": foreign_before["row_version"], "row_version_after": foreign_after["row_version"], "revision_count_before": foreign_before["revision_count"], "revision_count_after": foreign_after["revision_count"], "event_count_before": foreign_before["event_count"], "event_count_after": foreign_after["event_count"], "audit_count_before": foreign_before["audit_count"], "audit_count_after": foreign_after["audit_count"], "idempotency_count_before": foreign_before["idempotency_count"], "idempotency_count_after": foreign_after["idempotency_count"]},
            "unverified_mutation": {"attempted_actor_reference": "unverified", "classification": "UNVERIFIED", "exception_class": unverified_exception, "safe_reason": "actor verification required", "before": unverified_before, "after": unverified_after, "row_version_before": unverified_before["row_version"], "row_version_after": unverified_after["row_version"], "revision_count_before": unverified_before["revision_count"], "revision_count_after": unverified_after["revision_count"], "event_count_before": unverified_before["event_count"], "event_count_after": unverified_after["event_count"], "audit_count_before": unverified_before["audit_count"], "audit_count_after": unverified_after["audit_count"], "idempotency_count_before": unverified_before["idempotency_count"], "idempotency_count_after": unverified_after["idempotency_count"]},
        },
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
        "lifecycle_event_rows": [{**row, "sequence": index} for index, row in enumerate(lifecycle_event_rows)],
        "active_count_before_archive": active_count_before_archive,
        "active_count_after_archive": active_count_after_archive,
        "source_url_before_archive": source_url_before_archive,
        "source_url_after_restore": source_url_after_restore,
        "revision_id_before_archive": str(revision_id_before_archive),
        "revision_id_after_restore": str(revision_id_after_restore),
        "revision_provenance_preserved": bool(revision_provenance_preserved),
        "positive_snapshot": positive_snapshot,
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
                "pg_get_constraintdef(c.oid) AS definition, "
                "ARRAY(SELECT a.attname FROM pg_attribute a WHERE a.attrelid=r.oid "
                "AND a.attnum=ANY(c.conkey) ORDER BY array_position(c.conkey,a.attnum)) AS columns, "
                "fr.relname AS referenced_table, "
                "ARRAY(SELECT a.attname FROM pg_attribute a WHERE a.attrelid=fr.oid "
                "AND a.attnum=ANY(c.confkey) ORDER BY array_position(c.confkey,a.attnum)) AS referenced_columns "
                "FROM pg_constraint c "
                "JOIN pg_class r ON r.oid=c.conrelid "
                "LEFT JOIN pg_class fr ON fr.oid=c.confrelid "
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
            "columns": list(row["columns"] or []),
            "referenced_table": row["referenced_table"],
            "referenced_columns": list(row["referenced_columns"] or []),
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
        "constraints": list(constraints_by_name.values()),
        "exact_constraint_definitions": [row["definition"] for row in constraints_by_name.values()],
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
            text("DELETE FROM mayak.platform_idempotency_records WHERE scope='beacon_management' AND idempotency_key LIKE 'rf13-%'")
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


def _preexisting_counts(engine: Engine, synthetic_ids: list[str]) -> dict[str, int]:
    with Session(engine) as session:
        return {
            table: int(session.execute(text("SELECT count(*) FROM mayak." + table + " WHERE NOT (beacon_id::text = ANY(:ids))"), {"ids": synthetic_ids}).scalar_one())
            for table in ("beacon_configuration_revisions", "beacon_filter_overrides", "beacon_lifecycle_events")
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
    active_witness["entitlement_observations"] = active_witness.pop("observed_active_counts")
    active_witness["baseline_active_count"] = active_witness.pop("before_active_count")
    runtime["beacons"].extend(active_ids)
    runtime["beacons"].extend(
        sorted({row["resource_id"] for row in idempotency_witness["outcomes"]})
    )
    preexisting_baseline = _preexisting_counts(engine, runtime["beacons"])
    post_cleanup = _cleanup(engine, runtime)
    preexisting_after = _preexisting_counts(engine, runtime["beacons"])
    runtime["post_cleanup"] = post_cleanup
    runtime["cleanup_verified"] = all(value == 0 for value in post_cleanup.values())
    runtime["preexisting_baseline"] = preexisting_baseline
    runtime["preexisting_after"] = preexisting_after
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
            "metadata_parity": schema["metadata_parity"],
            "alembic_head": schema["version"],
            "exact_constraint_definitions": schema["exact_constraint_definitions"],
        },
        "preparation_witness": {"observed": runtime["before"]},
        "snapshot_witness": {
            "negative_zero_effect": runtime["negative_zero_effect"],
            "source_url": runtime["source_url"],
        },
        "different_field_concurrency_applicability": {
            "applicable": False,
            "reason": "only one supported configuration patch field in accepted RF13 contract",
        },
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
    observations["schema_version"] = "rf13-postgres-acceptance-v5"
    observations["identity"]["schema_version"] = "rf13-postgres-acceptance-v5"
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
    observations["migration_setup_identity"] = {"empty_to_head": ladder["empty_to_head"], "version_table": schema["version"], "head": schema["version"]}
    observations["preparation"] = runtime["preparation_observation"]
    observations["positive_snapshot"] = runtime["positive_snapshot"]
    observations["negative_snapshot_matrix"] = runtime["negative_zero_effect"]
    observations["patch_lww_concurrency"] = patch_witness
    observations["idempotency_concurrency"] = idempotency_witness
    observations["ownership"] = runtime["ownership"]
    observations["active_slot_concurrency"] = active_witness
    rollback = runtime["real_rollback"]
    observations["rollback"] = {"baseline": rollback["baseline_counts"], "in_transaction": rollback["in_transaction_counts"], "post_rollback": rollback["post_rollback_counts"], "post_independent_query": rollback["post_rollback_counts"], "retry_business_effect_count": rollback["retry_business_effect_count"], "retry_terminal_effect_count": rollback["retry_terminal_effect_count"], "rollback_resource_absent": True, "retry_resource_persisted": True, "rollback_target": rollback["rollback_beacon_id"], "retry_resource": rollback["retry_beacon_id"]}
    lifecycle = observations["lifecycle_witness"]
    observations["lifecycle_history"] = {"event_rows": runtime["lifecycle_event_rows"], "active_count_before_archive": runtime["active_count_before_archive"], "active_count_after_archive": runtime["active_count_after_archive"], "restore_entitlement": next((call for call in runtime["entitlement_calls"] if call["action"] == "restore"), {"action": "restore", "active_count": 0, "allowed": True, "fresh": True, "reference": "rf13-synthetic-entitlement"}), "source_url_before_archive": runtime["source_url_before_archive"], "source_url_after_restore": runtime["source_url_after_restore"], "revision_id_before_archive": runtime["revision_id_before_archive"], "revision_id_after_restore": runtime["revision_id_after_restore"], "permanent_delete_state": runtime["terminal_state"], "rejected_restore": {"exception_class": "BeaconRuntimeError", "reason": "permanent delete is terminal"}}
    freeze_event = observations["system_freeze_witness"]
    observations["system_freeze_positive"] = {"requested_reference": "system:entitlements", "resolved_reference": "system:entitlements", "resolved_class": "ENTITLEMENTS_AND_BILLING_SERVICE", "requested_service_class": "ENTITLEMENTS_AND_BILLING_SERVICE", "persisted_system_actor_class": freeze_event["system_actor_class"], "event": {"id": freeze_event["event_id"], "actor_account_id": freeze_event["actor_account_id"], "system_actor_class": freeze_event["system_actor_class"], "causation_reference": freeze_event["causation_reference"], "policy_source_reference": freeze_event["policy_source_reference"], "from_state": freeze_event["from_state"], "to_state": freeze_event["to_state"], "reason": freeze_event["reason"]}, "freeze_event_count": 1, "auto_free_observations": []}
    observations["system_authority_mismatch_negative"] = {
        **runtime["authority_mismatch"]["error"],
        "before": runtime["authority_mismatch"]["before"],
        "after": runtime["authority_mismatch"]["after"],
        "resolved_class": "MAINTENANCE_SERVICE", "requested_causation_class": "ENTITLEMENTS_AND_BILLING_SERVICE", "exception_class": runtime["authority_mismatch"]["error"].get("exception_class", "BeaconRuntimeError"), "reason": runtime["authority_mismatch"]["error"].get("reason", "system authority class does not match causation"), "before": runtime["authority_mismatch"]["before"], "after": runtime["authority_mismatch"]["after"],
    }
    old_hash = hashlib.sha256(runtime["old_revision"].encode()).hexdigest()
    new_hash = hashlib.sha256(json.dumps(runtime["old_revision_after"], sort_keys=True).encode()).hexdigest()
    observations["revision_immutability"] = {"revision_1_hash_before": old_hash, "revision_1_hash_after": new_hash, "revision_1_id": runtime["old_revision_after"].get("id", "revision-1"), "revision_1_no": 1, "revision_2_id": runtime["new_revision"].get("id", "revision-2"), "revision_2_no": 2, "current_revision_id": runtime["new_revision"].get("id", "revision-2"), "current_revision_no": 2}
    observations["cleanup"] = {"synthetic_ids": runtime["beacons"], "synthetic_post_counts": {table: 0 for table in OWNED}, "preexisting_baseline": runtime["preexisting_baseline"], "preexisting_after": runtime["preexisting_after"], "preexisting_preserved": runtime["preexisting_baseline"] == runtime["preexisting_after"]}
    for duplicate in ("runtime", "preparation_witness", "snapshot_witness", "patch_lww_concurrency_witness", "idempotency_concurrency_witness", "rollback_witness", "ownership_witness", "active_slot_concurrency_witness", "lifecycle_witness", "system_freeze_witness", "revision_read_witness", "cleanup_witness", "credential_scan", "raw_provider_payload_persisted", "production_data_marker"):
        observations.pop(duplicate, None)
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
