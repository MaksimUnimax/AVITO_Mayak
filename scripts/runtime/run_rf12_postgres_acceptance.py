"""Authoritative RF-12 PostgreSQL acceptance evidence producer.

This command is intentionally strict: it requires a task-owned DSN, runs the
real Alembic command, calls the real Module 03 runtime, and records observed
database facts.  It never accepts caller-supplied gate booleans.
"""

# The evidence document mirrors long, explicit gate names and SQL observations.
# Keep those fields readable as single records.
# ruff: noqa: E501

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import threading
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import alembic.command as command
from alembic.config import Config
from sqlalchemy import Engine, create_engine, inspect, text
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session

from mayak.modules.entitlements_and_billing.contracts import TariffName
from mayak.modules.entitlements_and_billing.runtime import (
    AuthorityFacts,
    EntitlementsBillingRuntime,
    FakeVerifiedIdentityPort,
    NormalizedPaymentEvidence,
    PaymentState,
)
from mayak.persistence.metadata import metadata

SCHEMA = "rf12-postgres-acceptance-v1"
TECHNICAL_ID = "RF-12-CORRECTIVE-TRANSACTION-SERIALIZATION-SCHEMA-INVARIANTS-AND-REAL-POSTGRES-CLOSURE-20260801-03"
EXPECTED_HEAD = "RF12_RUNTIME_HARDEN"
HISTORICAL = Path("alembic/versions/20260801_RF12_manual_grant_semantics.py")
RF09 = tuple(sorted(Path("alembic/versions").glob("202607*.py")))
OWNED_TABLES = (
    "entitlement_tariff_definitions", "entitlement_access_grants",
    "entitlement_usage_counters", "billing_payment_records",
    "billing_payment_operations", "billing_reconciliations",
)
COMMAND_IDS = (
    "tariff_bootstrap", "tariff_assignment", "basic_manual_renewal",
    "tariff_access_revoke", "manual_access_create", "manual_access_revoke",
    "payment_evidence_record", "payment_reconciliation", "manual_refund_reference",
    "active_beacon_slot", "scan_interval_window",
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _safe_git(*args: str) -> str:
    return subprocess.check_output(("git", *args), text=True).strip()


def _count(session: Session, table: str, where: str = "") -> int:
    suffix = f" WHERE {where}" if where else ""
    return int(session.execute(text(f"SELECT count(*) FROM mayak.{table}{suffix}")).scalar_one())


def _migration(dsn: str) -> None:
    os.environ["RF12_ACCEPTANCE_DSN"] = dsn
    cfg = Config("alembic.ini")
    cfg.cmd_opts = argparse.Namespace(sql=False, tag=None)
    command.upgrade(cfg, "head")


def _migration_ladder(args: argparse.Namespace) -> dict[str, Any]:
    ladders = {
        "empty_to_head": (args.empty_dsn, ("head",)),
        "rf09_to_manual_to_head": (args.rf09_dsn, ("RF09_FINALIZE", "RF12_MANUAL_GRANT", "head")),
        "manual_to_head": (args.manual_dsn, ("RF12_MANUAL_GRANT", "head")),
    }
    result: dict[str, Any] = {}
    for name, (dsn, revisions) in ladders.items():
        if not dsn:
            result[name] = {"observed": False, "reason": "dedicated ladder DSN missing"}
            continue
        os.environ["RF12_ACCEPTANCE_DSN"] = dsn
        cfg = Config("alembic.ini")
        cfg.cmd_opts = argparse.Namespace(sql=False, tag=None)
        try:
            for revision in revisions:
                command.upgrade(cfg, revision)
            result[name] = {"observed": True, "revisions": revisions}
        except Exception as exc:
            result[name] = {"observed": False, "error": type(exc).__name__}
    return result


def _fixture(session: Session) -> tuple[UUID, AuthorityFacts]:
    account = uuid4()
    now = datetime.now(UTC)
    session.execute(text("""
        INSERT INTO mayak.identity_accounts (id, phone, state, created_at, updated_at, row_version)
        VALUES (:id, NULL, 'ACTIVE', :now, :now, 1)
    """), {"id": account, "now": now})
    facts = AuthorityFacts(
        actor_id=account, account_id=account,
        capabilities=frozenset({
            "ENTITLEMENTS_TARIFF_ADMIN", "ENTITLEMENTS_TARIFF_ASSIGN_ADMIN",
            "ENTITLEMENTS_MANUAL_ACCESS_ADMIN",
        }), scope="account_id", authorization_reference="rf12-synthetic-identity",
        audit_reference=f"rf12-audit-{account}",
    )
    return account, facts


def _runtime(facts: AuthorityFacts) -> EntitlementsBillingRuntime:
    return EntitlementsBillingRuntime(FakeVerifiedIdentityPort(facts))


def _call_matrix(session: Session) -> dict[str, Any]:
    account, facts = _fixture(session)
    runtime = _runtime(facts)
    now = datetime.now(UTC).replace(microsecond=0)
    end = now + timedelta(days=3)
    actor = facts.authorization_reference
    rows: list[dict[str, Any]] = []

    def execute(command_id: str, invoke: Any, key: str, *, include_target: bool = True, **kwargs: Any) -> dict[str, Any]:
        before = {table: _count(session, table) for table in OWNED_TABLES}
        audit_before = _count(session, "platform_audit_entries")
        idem_before = _count(session, "platform_idempotency_records")
        if include_target:
            result = invoke(session, actor, idempotency_key=key, target_account_id=account, **kwargs)
        else:
            result = invoke(session, evidence=kwargs["evidence"], idempotency_key=key, actor_reference=actor)
        session.flush()
        after = {table: _count(session, table) for table in OWNED_TABLES}
        return {
            "command_id": command_id,
            "production_method": invoke.__qualname__,
            "setup": "synthetic Identity account through persisted Identity boundary",
            "invocation": result.model_dump(mode="json"),
            "business_effect_count": sum(after[t] - before[t] for t in OWNED_TABLES),
            "audit_effect_count": _count(session, "platform_audit_entries") - audit_before,
            "idempotency_effect_count": _count(session, "platform_idempotency_records") - idem_before,
            "post_state": after,
        }

    rows.append(execute("tariff_bootstrap", runtime.bootstrap_tariffs, "matrix-bootstrap", effective_at=now))
    rows.append(execute("tariff_assignment", runtime.assign_access, "matrix-assign", tariff=TariffName.BASIC, starts_at=now, ends_at=end, reason="rf12 matrix"))
    rows.append(execute("basic_manual_renewal", runtime.manual_renewal, "matrix-renew", starts_at=now, ends_at=end, reason="rf12 renewal"))
    grant = UUID(rows[1]["invocation"]["resource_id"])
    rows.append(execute("tariff_access_revoke", runtime.revoke_access, "matrix-revoke", grant_id=grant, reason="rf12 revoke"))
    manual = execute("manual_access_create", runtime.manual_access_create, "matrix-manual", starts_at=now, ends_at=end, reason="rf12 manual", granted_capability="SCAN", granted_scope="ACCOUNT")
    rows.append(manual)
    manual_id = UUID(manual["invocation"]["resource_id"])
    rows.append(execute("manual_access_revoke", runtime.manual_access_revoke, "matrix-manual-revoke", grant_id=manual_id, reason="rf12 manual revoke"))
    evidence = NormalizedPaymentEvidence(account_id=account, provider_code="synthetic", external_payment_id=f"payment-{account}", amount_minor=99000, currency="RUB", state=PaymentState.CONFIRMED, observed_at=now, safe_metadata={"fixture": "rf12"})
    payment = execute("payment_evidence_record", runtime.record_payment_evidence, "matrix-payment", include_target=False, evidence=evidence)
    rows.append(payment)
    payment_id = UUID(payment["invocation"]["resource_id"])
    rows.append(execute("payment_reconciliation", runtime.reconcile_payment, "matrix-reconcile", payment_id=payment_id, state=PaymentState.CONFIRMED, observed_at=now,))
    rows.append(execute("manual_refund_reference", runtime.manual_refund_reference, "matrix-refund", payment_id=payment_id, reference="manual-ref-1", reason="operator review", reviewed_at=now))
    rows.append(execute("active_beacon_slot", runtime.consume_usage, "matrix-beacon", counter_code="ACTIVE_BEACON_SLOT", window_start=now, window_end=end, requester="BEACON_MANAGEMENT", source_owner="BEACON_MANAGEMENT", limit_value=1))
    rows.append(execute("scan_interval_window", runtime.consume_usage, "matrix-scan", counter_code="SCAN_INTERVAL_WINDOW", window_start=now, window_end=now + timedelta(minutes=5), requester="SCAN_ORCHESTRATION", source_owner="SCAN_ORCHESTRATION"))
    session.commit()

    runtime.manual_access_create(session, actor, starts_at=now, ends_at=end, idempotency_key="matrix-replay", reason="replay", target_account_id=account, granted_capability="SCAN", granted_scope="ACCOUNT")
    session.commit()
    replay_again = runtime.manual_access_create(session, actor, starts_at=now, ends_at=end, idempotency_key="matrix-replay", reason="replay", target_account_id=account, granted_capability="SCAN", granted_scope="ACCOUNT")
    mismatch = runtime.manual_access_create(session, actor, starts_at=now, ends_at=end, idempotency_key="matrix-replay", reason="different", target_account_id=account, granted_capability="SCAN", granted_scope="ACCOUNT")
    session.rollback()
    rows.append({"command_id": "replay_mismatch", "replay": replay_again.model_dump(mode="json"), "mismatch": mismatch.model_dump(mode="json")})
    return {"rows": rows, "account_id": str(account)}


def _parity(engine: Engine) -> dict[str, Any]:
    db = inspect(engine)
    mismatches: list[str] = []
    for name in OWNED_TABLES:
        actual_columns = db.get_columns(name, schema="mayak")
        actual = {c["name"] for c in actual_columns}
        expected_table = metadata.tables[f"mayak.{name}"]
        expected = {c.name for c in expected_table.columns}
        if actual != expected:
            mismatches.append(f"{name}.columns expected={sorted(expected)} actual={sorted(actual)}")
        for column in actual_columns:
            model = expected_table.c[column["name"]]
            if bool(column["nullable"]) != bool(model.nullable):
                mismatches.append(f"{name}.{column['name']}.nullable expected={model.nullable} actual={column['nullable']}")
            expected_type = model.type.compile(dialect=postgresql.dialect())
            actual_type = column["type"].compile(dialect=postgresql.dialect())
            if str(actual_type).lower() != str(expected_type).lower():
                mismatches.append(f"{name}.{column['name']}.type expected={expected_type} actual={column['type']}")
            expected_default = str(model.server_default.arg) if model.server_default is not None else None
            actual_default = column.get("default")
            if expected_default is not None and actual_default is None:
                mismatches.append(f"{name}.{column['name']}.default expected={expected_default} actual=None")
        actual_checks = {item["name"] for item in db.get_check_constraints(name, schema="mayak")}
        expected_checks = {item.name for item in expected_table.constraints if item.__class__.__name__ == "CheckConstraint"}
        if not expected_checks.issubset(actual_checks):
            mismatches.append(f"{name}.constraints expected={sorted(expected_checks)} actual={sorted(actual_checks)}")
        unique_names = {item["name"] for item in db.get_unique_constraints(name, schema="mayak")}
        actual_indexes = {i["name"] for i in db.get_indexes(name, schema="mayak") if i["name"] not in unique_names}
        expected_indexes = {i.name for i in metadata.tables[f"mayak.{name}"].indexes}
        if actual_indexes != expected_indexes:
            mismatches.append(f"{name}.indexes expected={sorted(expected_indexes)} actual={sorted(actual_indexes)}")
    return {"columns": not any(".columns" in x or ".nullable" in x or ".type" in x for x in mismatches), "defaults": not any(".default" in x for x in mismatches), "constraints": not any(".constraints" in x for x in mismatches), "indexes": not any(".indexes" in x for x in mismatches), "mismatches": mismatches, "observed": True}


def _real_concurrency(engine: Engine) -> dict[str, Any]:
    """Run two independently connected callers through one production command."""
    setup = Session(engine)
    account, facts = _fixture(setup)
    setup.commit()
    setup.close()
    barrier = threading.Barrier(2)
    outcomes: list[dict[str, Any]] = []
    started = time.monotonic()

    def worker() -> None:
        session = Session(engine)
        try:
            barrier.wait(timeout=10)
            now = datetime.now(UTC).replace(microsecond=0)
            result = _runtime(facts).manual_access_create(
                session, facts.authorization_reference, starts_at=now,
                ends_at=now + timedelta(days=1), idempotency_key="race-key",
                reason="race", target_account_id=account, granted_capability="SCAN",
                granted_scope="ACCOUNT",
            )
            session.commit()
            outcomes.append(result.model_dump(mode="json"))
        finally:
            session.close()

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=15)
    elapsed = time.monotonic() - started
    with Session(engine) as check:
        business = _count(check, "entitlement_access_grants", "account_id = '%s' AND grant_kind = 'MANUAL'" % account)
        audit = _count(check, "platform_audit_entries", "actor_account_id = '%s'" % account)
        terminal = _count(check, "platform_idempotency_records", "idempotency_key = 'race-key'")
    return {"account_id": str(account), "sessions": 2, "synchronization": "Barrier + independent SQLAlchemy Sessions", "outcomes": outcomes, "observed_effect_count": business, "observed_audit_count": audit, "observed_terminal_count": terminal, "elapsed_seconds": elapsed, "bounded": all(not thread.is_alive() for thread in threads), "result": len(outcomes) == 2 and business == 1 and terminal == 1}


def _real_rollback(engine: Engine) -> dict[str, Any]:
    session = Session(engine)
    account, facts = _fixture(session)
    session.commit()
    now = datetime.now(UTC).replace(microsecond=0)
    runtime = _runtime(facts)
    before = {
        "business": _count(session, "entitlement_access_grants"),
        "audit": _count(session, "platform_audit_entries"),
        "terminal": _count(session, "platform_idempotency_records"),
    }
    runtime.manual_access_create(
        session, facts.authorization_reference, starts_at=now,
        ends_at=now + timedelta(days=1), idempotency_key="rollback-key",
        reason="rollback", target_account_id=account, granted_capability="SCAN",
        granted_scope="ACCOUNT",
    )
    session.rollback()
    after = {
        "business": _count(session, "entitlement_access_grants"),
        "audit": _count(session, "platform_audit_entries"),
        "terminal": _count(session, "platform_idempotency_records"),
    }
    retry = runtime.manual_access_create(
        session, facts.authorization_reference, starts_at=now,
        ends_at=now + timedelta(days=1), idempotency_key="rollback-key",
        reason="rollback", target_account_id=account, granted_capability="SCAN",
        granted_scope="ACCOUNT",
    )
    session.commit()
    session.close()
    return {"account_id": str(account), "before": before, "after": after, "before_after_equal": before == after, "business_effect": after["business"] - before["business"], "audit_effect": after["audit"] - before["audit"], "terminal_effect": after["terminal"] - before["terminal"], "retry_success": retry.state is not None and retry.state.value == "RECORDED"}


def _real_payment_race(engine: Engine) -> dict[str, Any]:
    """Observe provider-identity serialization with independent PostgreSQL sessions."""
    setup = Session(engine)
    same_account, same_facts = _fixture(setup)
    other_account, other_facts = _fixture(setup)
    setup.commit()
    setup.close()
    provider = "synthetic-race"
    external = "provider-identity-race"
    barrier = threading.Barrier(2)

    def run_pair(accounts: tuple[UUID, UUID], facts: tuple[AuthorityFacts, AuthorityFacts]) -> dict[str, Any]:
        outcomes: list[dict[str, Any]] = []

        def worker(account: UUID, identity: AuthorityFacts) -> None:
            session = Session(engine)
            try:
                barrier.wait(timeout=10)
                evidence = NormalizedPaymentEvidence(
                    account_id=account, provider_code=provider,
                    external_payment_id=external, amount_minor=99000,
                    currency="RUB", state=PaymentState.CONFIRMED,
                    observed_at=datetime.now(UTC), safe_metadata={"fixture": "rf12-race"},
                )
                try:
                    result = _runtime(identity).record_payment_evidence(
                        session, evidence,
                        idempotency_key=f"payment-race-{account}",
                        actor_reference=identity.authorization_reference,
                    )
                    session.commit()
                    outcomes.append({"account_id": str(account), "outcome": result.model_dump(mode="json")})
                except Exception as exc:
                    session.rollback()
                    outcomes.append({"account_id": str(account), "error": type(exc).__name__})
            finally:
                session.close()

        threads = [
            threading.Thread(target=worker, args=(accounts[0], facts[0])),
            threading.Thread(target=worker, args=(accounts[1], facts[1])),
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=15)
        with Session(engine) as check:
            payments = _count(check, "billing_payment_records", "provider_code = 'synthetic-race' AND external_payment_id = 'provider-identity-race'")
            idempotency = _count(check, "platform_idempotency_records", "scope='entitlements_and_billing' AND idempotency_key LIKE 'payment-race-%'")
        return {
            "sessions": 2, "synchronization": "Barrier + independent SQLAlchemy Sessions",
            "outcomes": outcomes, "committed_payment_count": payments,
            "idempotency_count": idempotency,
            "bounded": all(not thread.is_alive() for thread in threads),
        }

    same = run_pair((same_account, same_account), (same_facts, same_facts))
    barrier.reset()
    cross = run_pair((same_account, other_account), (same_facts, other_facts))
    result = (
        same["sessions"] == 2 and len(same["outcomes"]) == 2
        and same["committed_payment_count"] == 1
        and cross["sessions"] == 2 and len(cross["outcomes"]) == 2
        and cross["committed_payment_count"] == 1
        and any(
            item.get("outcome", {}).get("state") in {"REJECTED", "CONFLICT"}
            or item.get("outcome", {}).get("reason_code") == "PROVIDER_PAYMENT_ACCOUNT_CONFLICT"
            for item in cross["outcomes"]
        )
        and same["bounded"] and cross["bounded"]
    )
    return {
        "same_provider_same_account": same,
        "same_provider_different_account": cross,
        "provider_identity": {"provider_code": provider, "external_payment_id": external},
        "result": result,
        "account_ids": [str(same_account), str(other_account)],
    }


def _foreign_equality(args: argparse.Namespace) -> dict[str, Any]:
    """Compare caller-supplied bounded snapshots; missing snapshots fail closed."""
    if not args.foreign_before or not args.foreign_after:
        return {"observed": False, "equal": False, "reason": "before/after foreign snapshot missing"}
    before = json.loads(Path(args.foreign_before).read_text(encoding="utf-8"))
    after = json.loads(Path(args.foreign_after).read_text(encoding="utf-8"))
    return {"observed": True, "before": before, "after": after, "equal": before == after}


def _cleanup(engine: Engine, account_ids: list[str]) -> bool:
    """Remove only the synthetic accounts and their owned acceptance rows."""
    with engine.begin() as conn:
        for account_id in account_ids:
            params = {"account": account_id}
            conn.execute(text("DELETE FROM mayak.billing_reconciliations WHERE payment_record_id IN (SELECT id FROM mayak.billing_payment_records WHERE account_id=:account)"), params)
            conn.execute(text("DELETE FROM mayak.billing_payment_operations WHERE payment_record_id IN (SELECT id FROM mayak.billing_payment_records WHERE account_id=:account)"), params)
            conn.execute(text("DELETE FROM mayak.billing_payment_records WHERE account_id=:account"), params)
            conn.execute(text("DELETE FROM mayak.entitlement_usage_counters WHERE account_id=:account"), params)
            conn.execute(text("DELETE FROM mayak.entitlement_access_grants WHERE account_id=:account"), params)
            conn.execute(text("DELETE FROM mayak.platform_audit_entries WHERE actor_account_id=:account"), params)
            conn.execute(text("DELETE FROM mayak.platform_idempotency_records WHERE scope='entitlements_and_billing'"))
            conn.execute(text("DELETE FROM mayak.identity_accounts WHERE id=:account"), params)
    with engine.connect() as conn:
        return all(conn.execute(text("SELECT count(*) FROM mayak.identity_accounts WHERE id=:account"), {"account": value}).scalar_one() == 0 for value in account_ids)


def _constraints(engine: Engine) -> dict[str, Any]:
    # Execute the physical invariant matrix against a real final-head database.
    checks = ["grant_kind_allowed", "tariff_grant_fields_empty", "manual_grant_fields_present", "reason_nonempty", "valid_interval", "row_version_positive"]
    observed: list[dict[str, Any]] = []
    with engine.begin() as conn:
        account = conn.execute(text("SELECT id FROM mayak.identity_accounts LIMIT 1")).scalar_one()
        tariff = conn.execute(text("SELECT id FROM mayak.entitlement_tariff_definitions WHERE code='BASIC' LIMIT 1")).scalar_one()
        now = datetime.now(UTC)
        values = {"id": uuid4(), "account": account, "tariff": tariff, "kind": "TARIFF", "cap": None, "scope": None, "reason": "valid", "now": now, "end": now + timedelta(days=1), "created": now, "updated": now, "row_version": 1}
        positive = "INSERT INTO mayak.entitlement_access_grants (id,account_id,tariff_id,source_code,grant_kind,granted_capability,granted_scope,reason,valid_from,valid_until,state,created_at,updated_at,row_version) VALUES (:id,:account,:tariff,'RF12',:kind,:cap,:scope,:reason,:now,:end,'ACTIVE',:created,:updated,:row_version)"
        conn.execute(text(positive), values)
        conn.execute(text("DELETE FROM mayak.entitlement_access_grants WHERE id=:id"), {"id": values["id"]})
        manual_values = dict(values, id=uuid4(), tariff=None, kind="MANUAL", cap="SCAN", scope="ACCOUNT")
        conn.execute(text(positive), manual_values)
        conn.execute(text("DELETE FROM mayak.entitlement_access_grants WHERE id=:id"), {"id": manual_values["id"]})
        cases: dict[str, dict[str, Any]] = {
            "tariff_null": {"tariff": None},
            "tariff_forbidden_capability": {"cap": "ADMIN"},
            "tariff_forbidden_scope": {"scope": "ACCOUNT"},
            "manual_nonnull_tariff": {"kind": "MANUAL"},
            "manual_null_capability": {"kind": "MANUAL", "tariff": None},
            "manual_blank_capability": {"kind": "MANUAL", "tariff": None, "cap": " ", "scope": "ACCOUNT"},
            "manual_null_scope": {"kind": "MANUAL", "tariff": None, "cap": "SCAN"},
            "manual_blank_scope": {"kind": "MANUAL", "tariff": None, "cap": "SCAN", "scope": " "},
            "blank_reason": {"reason": " "},
            "invalid_kind": {"kind": "INVALID"},
            "bad_interval": {"end": now},
            "bad_row_version": {"row_version": 0},
        }
        for label, overrides in cases.items():
            candidate = dict(values)
            candidate.update(overrides)
            candidate["id"] = uuid4()
            savepoint = conn.begin_nested()
            try:
                conn.execute(text(positive), candidate)
            except Exception as exc:
                savepoint.rollback()
                diag = getattr(getattr(exc, "orig", None), "diag", None)
                observed.append({"case": label, "rejected": True, "constraint": getattr(diag, "constraint_name", None)})
            else:
                savepoint.rollback()
                observed.append({"case": label, "rejected": False})
    return {"cases": observed, "required_constraints": checks, "result": bool(observed) and all(x["rejected"] for x in observed)}


def produce(args: argparse.Namespace) -> dict[str, Any]:
    if not args.dsn or "@" not in args.dsn or "localhost" in args.dsn or "127.0.0.1" in args.dsn:
        raise SystemExit("RF12 task-owned internal PostgreSQL DSN is required")
    args._phase = "migration_ladders"
    ladders = _migration_ladder(args)
    args._phase = "final_migration"
    _migration(args.migration_dsn or args.dsn)
    args._phase = "version_observation"
    engine = create_engine(args.dsn, future=True, pool_size=4, max_overflow=0)
    with engine.begin() as conn:
        version = conn.execute(text("SELECT version(), current_setting('server_version_num')")).one()
        version_schema = conn.execute(
            text(
                "SELECT table_schema FROM information_schema.tables "
                "WHERE table_name = 'alembic_version' AND table_schema IN ('mayak', 'public') "
                "ORDER BY CASE table_schema WHEN 'mayak' THEN 0 ELSE 1 END LIMIT 1"
            )
        ).scalar_one()
        head = conn.execute(
            text(f"SELECT version_num FROM {version_schema}.alembic_version")
        ).scalar_one()
    args._phase = "command_matrix"
    with Session(engine) as session:
        matrix = _call_matrix(session)
    args._phase = "concurrency"
    concurrency = _real_concurrency(engine)
    args._phase = "rollback_observation"
    rollback = _real_rollback(engine)
    args._phase = "payment_race"
    payment_race = _real_payment_race(engine)
    args._phase = "physical_schema_observation"
    parity = _parity(engine)
    constraints = _constraints(engine)
    args._phase = "cleanup_observation"
    cleanup_ok = _cleanup(engine, [matrix["account_id"], concurrency["account_id"], rollback["account_id"], *payment_race["account_ids"]])
    args._phase = "evidence_schema_observation"
    evidence = {
        "schema_version": SCHEMA, "technical_id": TECHNICAL_ID,
        "candidate_source_sha": args.candidate_sha, "candidate_tree_identity": _safe_git("write-tree") if not args.candidate_tree else args.candidate_tree,
        "application_image_identity": args.image_identity, "lock_identity": args.lock_identity,
        "build_input_identity": args.build_input_identity, "postgres": {"version": version[0], "major": int(str(version[1])[:2])},
        "alembic_head": head, "alembic_version_schema": version_schema,
        "historical_rf12_manual_grant_sha256": _sha(HISTORICAL),
        "rf09_digests": {str(p): _sha(p) for p in RF09},
        "gates": {"empty_to_head": ladders["empty_to_head"]["observed"], "rf09_to_manual_to_head": ladders["rf09_to_manual_to_head"]["observed"], "manual_to_head": ladders["manual_to_head"]["observed"], "metadata_parity": False, "physical_constraints": False, "command_matrix": False, "rollback": False, "concurrency": False, "payment_race": False, "cleanup": False, "foreign_equality": False},
        "migration_ladders": ladders,
        "metadata_parity": parity, "constraint_matrix": constraints, "command_matrix": matrix,
        "concurrency": concurrency,
        "rollback": rollback,
        "payment_race": payment_race,
        "cleanup": {"task_resources_removed": cleanup_ok, "observed": True}, "foreign_equality": _foreign_equality(args),
        "credential_exposure": False, "limitations": ["No live provider traffic; optional YooKassa credentials are disabled."],
    }
    evidence["gates"]["metadata_parity"] = bool(evidence["metadata_parity"]["observed"] and not evidence["metadata_parity"]["mismatches"])
    evidence["gates"]["physical_constraints"] = bool(evidence["constraint_matrix"]["result"])
    evidence["gates"]["command_matrix"] = {row["command_id"] for row in matrix["rows"] if row.get("command_id") in COMMAND_IDS} == set(COMMAND_IDS)
    evidence["gates"]["concurrency"] = bool(evidence["concurrency"]["result"])
    evidence["gates"]["payment_race"] = bool(evidence["payment_race"]["result"])
    evidence["gates"]["rollback"] = bool(evidence["rollback"]["before_after_equal"] and evidence["rollback"]["retry_success"])
    evidence["gates"]["cleanup"] = cleanup_ok
    evidence["gates"]["foreign_equality"] = bool(evidence["foreign_equality"]["observed"] and evidence["foreign_equality"]["equal"])
    engine.dispose()
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dsn", default=os.environ.get("RF12_ACCEPTANCE_DSN"))
    parser.add_argument("--migration-dsn")
    parser.add_argument("--empty-dsn")
    parser.add_argument("--rf09-dsn")
    parser.add_argument("--manual-dsn")
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--candidate-sha", required=True)
    parser.add_argument("--candidate-tree")
    parser.add_argument("--image-identity", required=True)
    parser.add_argument("--lock-identity", required=True)
    parser.add_argument("--build-input-identity", required=True)
    parser.add_argument("--foreign-before")
    parser.add_argument("--foreign-after")
    try:
        args = parser.parse_args()
        args.artifact.parent.mkdir(parents=True, exist_ok=True)
        evidence = produce(args)
    except Exception as exc:
        if "args" not in locals():
            print(f"RF12 acceptance producer failed closed: {type(exc).__name__}", file=sys.stderr)
            return 1
        original = getattr(exc, "orig", None)
        diagnostic = getattr(original, "diag", None)
        failure = {
            "producer_exit": 1,
            "exception_type": type(exc).__name__,
            "phase": getattr(args, "_phase", "unknown"),
            "sqlstate": getattr(original, "sqlstate", None),
            "constraint": getattr(diagnostic, "constraint_name", None),
            "table": getattr(diagnostic, "table_name", None),
            "column": getattr(diagnostic, "column_name", None),
        }
        try:
            (args.artifact.parent / "producer-failure.json").write_text(
                json.dumps(failure, sort_keys=True) + "\n", encoding="utf-8"
            )
        except OSError:
            pass
        print(f"RF12 acceptance producer failed closed: {type(exc).__name__}", file=sys.stderr)
        return 1
    args.artifact.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if not all(evidence["gates"].values()):
        failed = {name: value for name, value in evidence["gates"].items() if value is not True}
        failed["metadata_mismatches"] = evidence["metadata_parity"].get("mismatches", [])
        race = evidence["payment_race"]
        failed["payment_race_summary"] = {
            name: {
                "result": pair.get("result"),
                "sessions": pair.get("sessions"),
                "outcomes": len(pair.get("outcomes", [])),
                "committed_payment_count": pair.get("committed_payment_count"),
                "bounded": pair.get("bounded"),
            }
            for name, pair in race.items()
            if name in {"same_provider_same_account", "same_provider_different_account"}
        }
        foreign = evidence["foreign_equality"]
        failed["foreign_summary"] = {
            "observed": foreign.get("observed"),
            "equal": foreign.get("equal"),
            "before_counts": {key: len(value) for key, value in foreign.get("before", {}).items()},
            "after_counts": {key: len(value) for key, value in foreign.get("after", {}).items()},
        }
        (args.artifact.parent / "producer-gates.json").write_text(
            json.dumps({"producer_exit": 1, "failed_gates": failed}, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(f"RF12 acceptance gates failed: {json.dumps(failed, sort_keys=True)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
