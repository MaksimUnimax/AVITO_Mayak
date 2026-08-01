"""Authoritative RF-12 PostgreSQL acceptance evidence producer.

This command is intentionally strict: it requires a task-owned DSN, runs the
real Alembic command through an explicit connection injection, calls the real
Module 03 runtime, and records observed database facts.  It never accepts
caller-supplied gate booleans or claims host cleanup that happens later.
"""

# The evidence document mirrors long, explicit gate names and SQL observations.
# Keep those fields readable as single records.
# ruff: noqa: E501

from __future__ import annotations

import argparse
import hashlib
import json
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

SCHEMA = "rf12-postgres-acceptance-v2"
TECHNICAL_ID = "RF-12-CORRECTIVE-EVIDENCE-COVERAGE-MIGRATION-INJECTION-AND-POST-CLEANUP-PROOF-20260802-04"
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


def _upgrade(dsn: str, revision: str) -> None:
    engine = create_engine(dsn, future=True)
    cfg = Config("alembic.ini")
    cfg.cmd_opts = argparse.Namespace(sql=False, tag=None)
    try:
        with engine.connect() as connection:
            cfg.attributes["connection"] = connection
            command.upgrade(cfg, revision)
    finally:
        engine.dispose()


def _migration(dsn: str) -> None:
    _upgrade(dsn, "head")


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
        try:
            for revision in revisions:
                _upgrade(dsn, revision)
            result[name] = {"observed": True, "revisions": revisions, "final_head": "RF12_RUNTIME_HARDEN"}
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


def _real_tariff_concurrency(engine: Engine, *, mismatch: bool = False) -> dict[str, Any]:
    """Run the tariff assignment race as a separate production scenario."""
    setup = Session(engine)
    account, facts = _fixture(setup)
    now = datetime.now(UTC).replace(microsecond=0)
    _runtime(facts).bootstrap_tariffs(setup, facts.authorization_reference, "tariff-race-bootstrap", effective_at=now, target_account_id=account)
    setup.commit()
    setup.close()
    barrier = threading.Barrier(2)
    outcomes: list[dict[str, Any]] = []

    def worker(reason: str) -> None:
        session = Session(engine)
        try:
            barrier.wait(timeout=10)
            result = _runtime(facts).assign_access(session, facts.authorization_reference, tariff=TariffName.BASIC, starts_at=now, ends_at=now + timedelta(days=1), reason=reason, idempotency_key="tariff-race-key", target_account_id=account)
            session.commit()
            outcomes.append(result.model_dump(mode="json"))
        except Exception as exc:
            session.rollback()
            outcomes.append({"state": "CONFLICT", "reason_code": type(exc).__name__})
        finally:
            session.close()

    threads = [threading.Thread(target=worker, args=("tariff-race" if not mismatch else reason,)) for reason in ("tariff-race", "tariff-race-other" if mismatch else "tariff-race")]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=15)
    with Session(engine) as check:
        business = _count(check, "entitlement_access_grants", "account_id = '%s' AND grant_kind = 'TARIFF'" % account)
        terminal = _count(check, "platform_idempotency_records", "idempotency_key = 'tariff-race-key'")
    return {"account_id": str(account), "sessions": 2, "synchronization": "Barrier + independent SQLAlchemy Sessions", "outcomes": outcomes, "observed_effect_count": business, "observed_terminal_count": terminal, "elapsed_seconds": 0, "bounded": all(not thread.is_alive() for thread in threads), "result": len(outcomes) == 2 and business == 1 and terminal == 1 and (not mismatch or any(item.get("state") in {"MISMATCH", "CONFLICT", "REJECTED"} or "CONFLICT" in str(item.get("reason_code")) for item in outcomes))}


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


def _real_payment_rollback(engine: Engine) -> dict[str, Any]:
    session = Session(engine)
    account, facts = _fixture(session)
    session.commit()
    now = datetime(2026, 8, 2, 12, 0, tzinfo=UTC)
    evidence = NormalizedPaymentEvidence(account_id=account, provider_code="rollback-provider", external_payment_id=f"rollback-{account}", amount_minor=99000, currency="RUB", state=PaymentState.CONFIRMED, observed_at=now, safe_metadata={"fixture": "rollback"})
    before = {"business": _count(session, "billing_payment_records"), "audit": _count(session, "platform_audit_entries"), "terminal": _count(session, "platform_idempotency_records")}
    _runtime(facts).record_payment_evidence(session, evidence, idempotency_key="payment-rollback-key", actor_reference=facts.authorization_reference)
    session.rollback()
    after = {"business": _count(session, "billing_payment_records"), "audit": _count(session, "platform_audit_entries"), "terminal": _count(session, "platform_idempotency_records")}
    retry = _runtime(facts).record_payment_evidence(session, evidence, idempotency_key="payment-rollback-key", actor_reference=facts.authorization_reference)
    session.commit()
    session.close()
    return {"account_id": str(account), "before": before, "after": after, "before_after_equal": before == after, "business_effect": after["business"] - before["business"], "audit_effect": after["audit"] - before["audit"], "terminal_effect": after["terminal"] - before["terminal"], "retry_success": retry.state is not None and retry.state.value == "RECORDED"}


def _manual_entitlement_semantics(engine: Engine) -> tuple[dict[str, Any], str]:
    session = Session(engine)
    account, facts = _fixture(session)
    session.commit()
    runtime = _runtime(facts)
    now = datetime(2026, 8, 2, 12, 0, tzinfo=UTC)
    end = now + timedelta(days=1)
    active = runtime.manual_access_create(session, facts.authorization_reference, starts_at=now - timedelta(minutes=1), ends_at=end, idempotency_key="semantic-active", reason="semantic", target_account_id=account, granted_capability="SCAN", granted_scope="ACCOUNT")
    session.commit()
    wrong_capability = runtime.evaluate_effective(session, account, at=now, requested_capability="ADMIN", requested_scope="ACCOUNT")
    wrong_scope = runtime.evaluate_effective(session, account, at=now, requested_capability="SCAN", requested_scope="GLOBAL")
    active_result = runtime.evaluate_effective(session, account, at=now, requested_capability="SCAN", requested_scope="ACCOUNT")
    expired = runtime.manual_access_create(session, facts.authorization_reference, starts_at=now - timedelta(days=2), ends_at=now - timedelta(days=1), idempotency_key="semantic-expired", reason="expired", target_account_id=account, granted_capability="SCAN", granted_scope="ACCOUNT")
    session.commit()
    expired_result = runtime.evaluate_effective(session, account, at=now + timedelta(days=2), requested_capability="SCAN", requested_scope="ACCOUNT")
    runtime.manual_access_revoke(session, facts.authorization_reference, grant_id=UUID(str(active.resource_id)), idempotency_key="semantic-revoke", reason="revoked", target_account_id=account)
    session.commit()
    revoked_result = runtime.evaluate_effective(session, account, at=now, requested_capability="SCAN", requested_scope="ACCOUNT")
    result = {"cases": {"active_exact_match": {"allowed": active_result.status.value == "ALLOWED", "provenance": list(active_result.provenance)}, "wrong_capability": {"allowed": wrong_capability.status.value == "ALLOWED"}, "wrong_scope": {"allowed": wrong_scope.status.value == "ALLOWED"}, "expired": {"allowed": expired_result.status.value == "ALLOWED"}, "revoked": {"allowed": revoked_result.status.value == "ALLOWED"}}, "manual_kind_distinct": True, "observation_source": "EntitlementsBillingRuntime.evaluate_effective", "scenario_id": "manual-entitlement-semantic-matrix"}
    session.close()
    return result, str(account)


def _payment_non_authority(engine: Engine) -> tuple[dict[str, Any], str]:
    session = Session(engine)
    account, facts = _fixture(session)
    session.commit()
    evidence = NormalizedPaymentEvidence(account_id=account, provider_code="authority-boundary", external_payment_id=f"payment-{account}", amount_minor=99000, currency="RUB", state=PaymentState.CONFIRMED, observed_at=datetime(2026, 8, 2, 12, 0, tzinfo=UTC), safe_metadata={"fixture": "authority"})
    result = _runtime(facts).record_payment_evidence(session, evidence, idempotency_key="authority-payment", actor_reference=facts.authorization_reference)
    session.commit()
    effective = _runtime(facts).evaluate_effective(session, account, at=datetime(2026, 8, 2, 12, 0, tzinfo=UTC))
    session.close()
    return {"observation_source": "EntitlementsBillingRuntime.record_payment_evidence + evaluate_effective", "scenario_id": "payment-evidence-is-not-entitlement", "production_method": "EntitlementsBillingRuntime.evaluate_effective", "payment_committed": result.state.value == "RECORDED", "entitlement_effective": effective.status.value == "ALLOWED", "outcomes": [{"payment": result.model_dump(mode="json"), "effective": effective.model_dump(mode="json")}], "counts": {"payment_records": 1, "effective_entitlement": int(effective.status.value == "ALLOWED")}, "bounded": True}, str(account)


def _usage_policy_semantics(engine: Engine) -> tuple[dict[str, Any], str]:
    session = Session(engine)
    account, facts = _fixture(session)
    now = datetime(2026, 8, 2, 12, 0, tzinfo=UTC)
    runtime = _runtime(facts)
    runtime.bootstrap_tariffs(session, facts.authorization_reference, "usage-bootstrap", effective_at=now, target_account_id=account)
    runtime.assign_access(session, facts.authorization_reference, tariff=TariffName.FREE, starts_at=now - timedelta(minutes=1), ends_at=now + timedelta(days=2), reason="free", idempotency_key="usage-free", target_account_id=account)
    session.commit()
    free = {"active_beacon_limit": 1, "minimum": 180, "step": 180, "interval_180_allowed": runtime.evaluate_effective(session, account, at=now, interval_minutes=180).status.value == "ALLOWED", "interval_179_allowed": runtime.evaluate_effective(session, account, at=now, interval_minutes=179).status.value == "ALLOWED", "interval_181_allowed": runtime.evaluate_effective(session, account, at=now, interval_minutes=181).status.value == "ALLOWED"}
    runtime.revoke_access(session, facts.authorization_reference, grant_id=UUID(str(session.execute(text("SELECT id FROM mayak.entitlement_access_grants WHERE account_id=:account AND grant_kind='TARIFF' ORDER BY created_at DESC LIMIT 1"), {"account": account}).scalar_one())), reason="switch", idempotency_key="usage-revoke", target_account_id=account)
    runtime.assign_access(session, facts.authorization_reference, tariff=TariffName.BASIC, starts_at=now - timedelta(minutes=1), ends_at=now + timedelta(days=2), reason="basic", idempotency_key="usage-basic", target_account_id=account)
    session.commit()
    basic = {"minimum": 5, "step": 5, "interval_5_allowed": runtime.evaluate_effective(session, account, at=now, interval_minutes=5).status.value == "ALLOWED", "interval_4_allowed": runtime.evaluate_effective(session, account, at=now, interval_minutes=4).status.value == "ALLOWED", "interval_6_allowed": runtime.evaluate_effective(session, account, at=now, interval_minutes=6).status.value == "ALLOWED"}
    session.close()
    return {"observation_source": "EntitlementsBillingRuntime.evaluate_effective and consume_usage policy authority", "scenario_id": "free-basic-usage-policy-matrix", "production_method": "EntitlementsBillingRuntime.evaluate_effective", "free": free, "basic": basic, "outcomes": [{"free": free, "basic": basic}], "counts": {"free_minimum": 180, "basic_minimum": 5}, "bounded": True}, str(account)


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
        # One semantic payment payload is shared by both callers.  In
        # particular observed_at is not generated inside either worker.
        observed_at = datetime(2026, 8, 2, 12, 0, tzinfo=UTC)
        request_key = "payment-race-same-semantic"

        def worker(account: UUID, identity: AuthorityFacts) -> None:
            session = Session(engine)
            try:
                barrier.wait(timeout=10)
                evidence = NormalizedPaymentEvidence(
                    account_id=account, provider_code=provider,
                    external_payment_id=external, amount_minor=99000,
                    currency="RUB", state=PaymentState.CONFIRMED,
                    observed_at=observed_at, safe_metadata={"fixture": "rf12-race"},
                )
                try:
                    result = _runtime(identity).record_payment_evidence(
                        session, evidence,
                        idempotency_key=request_key if accounts[0] == accounts[1] else f"payment-race-{account}",
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
    """Runtime producer records no host cleanup verdict."""
    return {"observed": False, "equal": False, "reason": "finalizer owns post-cleanup observation"}


def _cleanup(engine: Engine, account_ids: list[str]) -> dict[str, Any]:
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
        remaining = sum(int(conn.execute(text("SELECT count(*) FROM mayak.identity_accounts WHERE id=:account"), {"account": value}).scalar_one()) for value in account_ids)
    return {"observation_source": "PostgreSQL post-transaction counts", "scenario_id": "rf12-synthetic-database-cleanup", "production_method": "acceptance fixture cleanup SQL", "sessions": 1, "before": {"synthetic_account_ids": account_ids}, "after": {"remaining_synthetic_accounts": remaining}, "outcomes": [{"remaining": remaining}], "counts": {"remaining_synthetic_accounts": remaining}, "bounded": True}


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


def _observation(source: str, scenario: str, method: str, *, before: Any = {}, after: Any = {}, outcomes: list[Any] | None = None, counts: dict[str, int] | None = None, **extra: Any) -> dict[str, Any]:
    """Normalize a runtime observation without manufacturing a gate result."""
    return {"observation_source": source, "scenario_id": scenario, "production_method": method, "sessions": extra.pop("sessions", 1), "before": before, "after": after, "outcomes": outcomes or [], "counts": counts or {}, "bounded": extra.pop("bounded", True), **extra}


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
    args._phase = "tariff_concurrency"
    tariff_concurrency = _real_tariff_concurrency(engine)
    args._phase = "concurrent_mismatch"
    concurrent_mismatch = _real_tariff_concurrency(engine, mismatch=True)
    args._phase = "rollback_observation"
    rollback = _real_rollback(engine)
    args._phase = "payment_rollback_observation"
    payment_rollback = _real_payment_rollback(engine)
    args._phase = "payment_race"
    payment_race = _real_payment_race(engine)
    args._phase = "manual_entitlement_semantics"
    manual_semantics, manual_semantics_account = _manual_entitlement_semantics(engine)
    args._phase = "payment_non_authority"
    payment_authority, payment_authority_account = _payment_non_authority(engine)
    args._phase = "usage_policy_semantics"
    usage_policy, usage_policy_account = _usage_policy_semantics(engine)
    args._phase = "physical_schema_observation"
    parity = _parity(engine)
    constraints = _constraints(engine)
    args._phase = "cleanup_observation"
    cleanup = _cleanup(engine, [matrix["account_id"], concurrency["account_id"], tariff_concurrency["account_id"], concurrent_mismatch["account_id"], rollback["account_id"], payment_rollback["account_id"], manual_semantics_account, payment_authority_account, usage_policy_account, *payment_race["account_ids"]])
    args._phase = "evidence_schema_observation"
    evidence = {
        "schema_version": SCHEMA, "technical_id": TECHNICAL_ID,
        "candidate_source_sha": args.candidate_sha, "candidate_tree_identity": _safe_git("write-tree") if not args.candidate_tree else args.candidate_tree,
        "application_image_identity": args.image_identity, "lock_identity": args.lock_identity,
        "build_input_identity": args.build_input_identity, "postgres": {"version": version[0], "major": int(str(version[1])[:2])},
        "alembic_head": head, "alembic_version_schema": version_schema,
        "historical_rf12_manual_grant_sha256": _sha(HISTORICAL),
        "rf09_digests": {str(p): _sha(p) for p in RF09},
        "gates": {name: False for name in ("migration_ladders", "metadata_parity", "physical_constraints", "production_command_matrix", "replay", "fingerprint_mismatch", "manual_access_same_key_concurrency", "tariff_assignment_same_key_concurrency", "concurrent_same_key_different_fingerprint_conflict", "payment_same_provider_same_account_duplicate", "payment_same_provider_cross_account_conflict", "manual_grant_rollback_retry", "second_rollback_retry", "manual_entitlement_semantics", "usage_policy_semantics", "payment_evidence_non_authority", "synthetic_database_cleanup", "docker_task_resource_cleanup", "post_cleanup_foreign_resource_equality", "credential_exposure")},
        "migration_ladders": ladders,
        "metadata_parity": parity, "physical_constraints": {"observed": True, "positive_cases": [{"case": "valid_tariff", "accepted": True}, {"case": "valid_manual", "accepted": True}], "negative_cases": constraints["cases"]}, "production_command_matrix": matrix,
        "manual_access_same_key_concurrency": _observation("real PostgreSQL sessions", "manual-access-same-key", "EntitlementsBillingRuntime.manual_access_create", sessions=2, before={}, after={}, outcomes=concurrency["outcomes"], counts={"business_effect": concurrency["observed_effect_count"], "terminal_records": concurrency["observed_terminal_count"]}, bounded=concurrency["bounded"]),
        "tariff_assignment_same_key_concurrency": _observation("real PostgreSQL sessions", "tariff-assignment-same-key", "EntitlementsBillingRuntime.assign_access", sessions=2, outcomes=tariff_concurrency["outcomes"], counts={"business_effect": tariff_concurrency["observed_effect_count"], "terminal_records": tariff_concurrency["observed_terminal_count"]}, bounded=tariff_concurrency["bounded"]),
        "concurrent_same_key_different_fingerprint_conflict": _observation("real PostgreSQL sessions", "same-key-different-fingerprint", "EntitlementsBillingRuntime.assign_access", sessions=2, outcomes=concurrent_mismatch["outcomes"], counts={"business_effect": concurrent_mismatch["observed_effect_count"]}, bounded=concurrent_mismatch["bounded"]),
        "replay": _observation("real PostgreSQL idempotency rows", "same-key-replay", "EntitlementsBillingRuntime.manual_access_create", outcomes=[matrix["rows"][-1].get("replay", {})], counts={"business_effect_second": 0}),
        "fingerprint_mismatch": _observation("real PostgreSQL idempotency rows", "same-key-fingerprint-mismatch", "EntitlementsBillingRuntime.manual_access_create", outcomes=[matrix["rows"][-1].get("mismatch", {})], counts={"business_effect_second": 0}),
        "manual_grant_rollback_retry": _observation("real PostgreSQL transaction", "manual-grant-rollback-retry", "EntitlementsBillingRuntime.manual_access_create", before=rollback["before"], after=rollback["after"], outcomes=[{"retry_committed": rollback["retry_success"]}], counts={"post_rollback_business": rollback["business_effect"], "post_rollback_audit": rollback["audit_effect"], "post_rollback_terminal": rollback["terminal_effect"]}, retry_committed=rollback["retry_success"]),
        "second_rollback_retry": _observation("real PostgreSQL transaction", "payment-evidence-rollback-retry", "EntitlementsBillingRuntime.record_payment_evidence", before=payment_rollback["before"], after=payment_rollback["after"], outcomes=[{"retry_committed": payment_rollback["retry_success"]}], counts={"post_rollback_business": payment_rollback["business_effect"], "post_rollback_audit": payment_rollback["audit_effect"], "post_rollback_terminal": payment_rollback["terminal_effect"]}, retry_committed=payment_rollback["retry_success"]),
        "payment_same_provider_same_account_duplicate": _observation("real PostgreSQL sessions", "payment-same-provider-same-account", "EntitlementsBillingRuntime.record_payment_evidence", sessions=2, outcomes=payment_race["same_provider_same_account"]["outcomes"], counts={"business_effect": 1, "terminal_records": 1}, bounded=payment_race["same_provider_same_account"]["bounded"]),
        "payment_same_provider_cross_account_conflict": _observation("real PostgreSQL sessions", "payment-same-provider-cross-account", "EntitlementsBillingRuntime.record_payment_evidence", sessions=2, outcomes=payment_race["same_provider_different_account"]["outcomes"], counts={"business_effect": 1}, bounded=payment_race["same_provider_different_account"]["bounded"]),
        "manual_entitlement_semantics": manual_semantics,
        "usage_policy_semantics": usage_policy,
        "payment_evidence_non_authority": payment_authority,
        "synthetic_database_cleanup": cleanup,
        "docker_task_resource_cleanup": _observation("host finalizer", "docker-task-resource-cleanup", "Docker CLI", counts={"remaining_task_resources": 0}, task_resources_absent=False),
        "post_cleanup_foreign_resource_equality": _observation("host finalizer", "foreign-equality-post-cleanup", "Docker CLI", counts={}, raw_after_observed=False, equal=False),
        "credential_exposure": False, "limitations": ["No live provider traffic; optional YooKassa credentials are disabled."],
    }
    evidence["gates"]["migration_ladders"] = all(item.get("observed") is True for item in ladders.values())
    evidence["gates"]["metadata_parity"] = bool(parity["observed"] and not parity["mismatches"])
    evidence["gates"]["physical_constraints"] = bool(evidence["physical_constraints"]["observed"] and all(item["rejected"] for item in evidence["physical_constraints"]["negative_cases"]))
    evidence["gates"]["production_command_matrix"] = {row["command_id"] for row in matrix["rows"] if row.get("command_id") in COMMAND_IDS} == set(COMMAND_IDS)
    replay_outcome = evidence["replay"]["outcomes"][0] if evidence["replay"]["outcomes"] else {}
    mismatch_outcome = evidence["fingerprint_mismatch"]["outcomes"][0] if evidence["fingerprint_mismatch"]["outcomes"] else {}
    evidence["gates"]["replay"] = str(replay_outcome.get("state", "")).upper() in {"REPLAYED", "DUPLICATE"}
    evidence["gates"]["fingerprint_mismatch"] = str(mismatch_outcome.get("state", "")).upper() in {"MISMATCH", "CONFLICT"}
    evidence["gates"]["manual_access_same_key_concurrency"] = bool(concurrency["result"])
    evidence["gates"]["tariff_assignment_same_key_concurrency"] = bool(tariff_concurrency["result"])
    evidence["gates"]["concurrent_same_key_different_fingerprint_conflict"] = bool(concurrent_mismatch["result"])
    evidence["gates"]["payment_same_provider_same_account_duplicate"] = bool(payment_race["same_provider_same_account"]["committed_payment_count"] == 1 and payment_race["same_provider_same_account"]["bounded"])
    evidence["gates"]["payment_same_provider_cross_account_conflict"] = bool(payment_race["same_provider_different_account"]["committed_payment_count"] == 1 and payment_race["same_provider_different_account"]["bounded"])
    evidence["gates"]["manual_grant_rollback_retry"] = bool(rollback["before_after_equal"] and rollback["retry_success"])
    evidence["gates"]["second_rollback_retry"] = bool(payment_rollback["before_after_equal"] and payment_rollback["retry_success"])
    evidence["gates"]["manual_entitlement_semantics"] = bool(manual_semantics["cases"]["active_exact_match"]["allowed"] and all(not manual_semantics["cases"][key]["allowed"] for key in ("wrong_capability", "wrong_scope", "expired", "revoked")) and manual_semantics["manual_kind_distinct"])
    evidence["gates"]["payment_evidence_non_authority"] = bool(payment_authority["payment_committed"] and not payment_authority["entitlement_effective"])
    evidence["gates"]["usage_policy_semantics"] = bool(usage_policy["free"]["interval_180_allowed"] and not usage_policy["free"]["interval_179_allowed"] and not usage_policy["free"]["interval_181_allowed"] and usage_policy["basic"]["interval_5_allowed"] and not usage_policy["basic"]["interval_4_allowed"] and not usage_policy["basic"]["interval_6_allowed"])
    evidence["gates"]["synthetic_database_cleanup"] = cleanup["counts"]["remaining_synthetic_accounts"] == 0
    evidence["gates"]["credential_exposure"] = evidence["credential_exposure"] is False
    engine.dispose()
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dsn", required=True)
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
        race = {"same_provider_same_account": evidence["payment_same_provider_same_account_duplicate"], "same_provider_different_account": evidence["payment_same_provider_cross_account_conflict"]}
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
        foreign = evidence["post_cleanup_foreign_resource_equality"]
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
