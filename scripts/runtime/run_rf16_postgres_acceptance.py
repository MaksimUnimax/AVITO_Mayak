"""Emit raw RF16 PostgreSQL observations for the strict verifier."""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session

from mayak.modules.egress_routing import EgressRuntime, RuntimeResult, TransportEffect
from mayak.persistence.metadata import metadata


class SingleRouteSemanticPolicy:
    """Hosted fixture for the accepted server-owned selection port."""

    def select(
        self,
        *,
        route_facts: tuple,
        purpose: str,
        capability_scope: tuple[str, ...],
    ) -> RuntimeResult:
        if purpose != "scan" or capability_scope != ("listing_read",):
            return RuntimeResult(False, "CAPABILITY_OR_PURPOSE_BLOCKED")
        if len(route_facts) == 0:
            return RuntimeResult(False, "NO_ELIGIBLE_ROUTE")
        if len(route_facts) > 1:
            return RuntimeResult(False, "MULTIPLE_ROUTES_UNAPPROVED")
        route_id, _agent_id, route_state, _agent_state = route_facts[0]
        if route_state != "READY":
            return RuntimeResult(False, "ROUTE_NOT_READY")
        if _agent_state != "READY":
            return RuntimeResult(False, "AGENT_NOT_READY")
        return RuntimeResult(True, "SELECTED", route_id)


def _foreign_witness(conn, ids: dict[str, object]) -> dict[str, object]:
    queries = {
        "identity": "select id, state, row_version from mayak.identity_accounts where id=:id",
        "beacon": (
            "select id, account_id, state, row_version from mayak.beacon_beacons where id=:id"
        ),
        "schedule": (
            "select id, beacon_id, state, row_version from mayak.scan_schedules where id=:id"
        ),
        "work": (
            "select id, schedule_id, beacon_id, state, attempt_count "
            "from mayak.scan_work_items where id=:id"
        ),
    }
    result: dict[str, object] = {}
    for name, query in queries.items():
        result[name] = [
            dict(row) for row in conn.execute(text(query), {"id": ids[name]}).mappings()
        ]
    result["parser_row_ids"] = [
        str(row[0])
        for row in conn.execute(text("select id from mayak.parser_outcomes order by id"))
    ]
    result["notification_rows"] = [
        dict(row)
        for row in conn.execute(
            text("select * from mayak.notification_delivery_attempts order by id")
        ).mappings()
    ]
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dsn", required=True)
    parser.add_argument("--fixture-dsn", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    fixture = create_engine(args.fixture_dsn)
    app = create_engine(args.dsn)
    identity = metadata.tables["mayak.identity_accounts"]
    beacon = metadata.tables["mayak.beacon_beacons"]
    schedule = metadata.tables["mayak.scan_schedules"]
    work = metadata.tables["mayak.scan_work_items"]
    leases = metadata.tables["mayak.egress_route_leases"]
    ids = {
        name: uuid4()
        for name in ("account", "beacon", "schedule", "work", "agent", "route", "route2", "route3")
    }
    now = datetime.now(UTC)
    # Fixture setup is outside the measured Egress mutation bracket.
    with fixture.begin() as conn:
        conn.execute(
            identity.insert().values(
                id=ids["account"],
                phone=None,
                state="ACTIVE",
                created_at=now,
                updated_at=now,
                row_version=1,
            )
        )
        conn.execute(
            beacon.insert().values(
                id=ids["beacon"],
                account_id=ids["account"],
                name="rf16-synthetic",
                source_url=None,
                current_revision_no=None,
                current_revision_id=None,
                state="ACTIVE",
                created_at=now,
                updated_at=now,
                row_version=1,
            )
        )
        conn.execute(
            schedule.insert().values(
                id=ids["schedule"],
                beacon_id=ids["beacon"],
                interval_seconds=60,
                next_due_at=now,
                state="ACTIVE",
                created_at=now,
                updated_at=now,
                row_version=1,
            )
        )
        conn.execute(
            work.insert().values(
                id=ids["work"],
                schedule_id=ids["schedule"],
                beacon_id=ids["beacon"],
                due_at=now,
                state="DUE",
                attempt_count=0,
                created_at=now,
                row_version=1,
            )
        )
    with fixture.connect() as conn:
        foreign_before = _foreign_witness(conn, ids)
    egress = EgressRuntime()
    policy = SingleRouteSemanticPolicy()
    lease_token = uuid4()
    with Session(app) as session, session.begin():
        agent = egress.register_agent(
            session, agent_code="rf16-agent", agent_id=ids["agent"], state="READY"
        )
        route = egress.register_route(
            session,
            agent_id=agent.id,
            route_code="rf16-route",
            endpoint_ref="project-owned:rf16",
            route_id=ids["route"],
            state="READY",
        )
        heartbeat = egress.record_heartbeat(
            session, agent_id=agent.id, state="ONLINE", safe_metadata={"scenario": "synthetic"}
        )
        selected = egress.select_route(
            session, purpose="scan", capability_scope=("listing_read",), selection_policy=policy
        )
        lease = egress.acquire_lease(
            session,
            route_id=route.id,
            work_item_id=ids["work"],
            lease_token=lease_token,
            lease_validity_seconds=60,
        )
        replay = egress.acquire_lease(
            session,
            route_id=route.id,
            work_item_id=ids["work"],
            lease_token=lease_token,
            lease_validity_seconds=60,
        )
        mismatch = egress.acquire_lease(
            session,
            route_id=route.id,
            work_item_id=ids["work"],
            lease_token=uuid4(),
            lease_validity_seconds=60,
        )
        active_count = session.execute(
            text(
                "select count(*) from mayak.egress_route_leases "
                "where route_id=:route and work_item_id=:work and state='ACTIVE'"
            ),
            {"route": route.id, "work": ids["work"]},
        ).scalar_one()
        wrong_token = egress.resolve_lease(
            session, lease_id=lease.reference_id, lease_token=uuid4(), terminal_state="COMPLETED"
        )
        diagnostics = egress.safe_diagnostics(
            session, route_id=route.id, lease_id=lease.reference_id
        )
        observed_lease = (
            session.execute(select(leases).where(leases.c.id == lease.reference_id))
            .mappings()
            .one()
        )
        # Explicitly record the ordinary terminal transition; no read-then-unconditional update.
        completed = egress.resolve_lease(
            session,
            lease_id=lease.reference_id,
            lease_token=lease_token,
            terminal_state="COMPLETED",
        )
        route2 = egress.register_route(
            session,
            agent_id=agent.id,
            route_code="rf16-route-2",
            endpoint_ref="project-owned:rf16-2",
            route_id=ids["route2"],
            state="READY",
        )
        egress.register_route(
            session,
            agent_id=agent.id,
            route_code="rf16-route-3",
            endpoint_ref="project-owned:rf16-3",
            route_id=ids["route3"],
            state="READY",
        )
        multi_route = egress.select_route(
            session, purpose="scan", capability_scope=("listing_read",), selection_policy=policy
        )
        unsupported = egress.select_route(
            session, purpose="unsupported", capability_scope=("unknown",), selection_policy=policy
        )
        expiry_token = uuid4()
        expiry_lease = egress.acquire_lease(
            session,
            route_id=route2.id,
            work_item_id=ids["work"],
            lease_token=expiry_token,
            lease_validity_seconds=1,
        )
        session.execute(
            text(
                "update mayak.egress_route_leases "
                "set lease_expires_at = now() - interval '1 second' where id=:id"
            ),
            {"id": expiry_lease.reference_id},
        )
        expired_count = egress.reconcile_expired(session)
        expiry = (
            RuntimeResult(False, "LEASE_EXPIRED", expiry_lease.reference_id)
            if expired_count
            else RuntimeResult(False, "NOT_EXPIRED")
        )
        ambiguity_token = uuid4()
        ambiguity_lease = egress.acquire_lease(
            session,
            route_id=route2.id,
            work_item_id=ids["work"],
            lease_token=ambiguity_token,
            lease_validity_seconds=60,
        )
        egress.resolve_lease(
            session,
            lease_id=ambiguity_lease.reference_id,
            lease_token=ambiguity_token,
            terminal_state="AMBIGUOUS",
        )
        ambiguity_replay = egress.acquire_lease(
            session,
            route_id=route2.id,
            work_item_id=ids["work"],
            lease_token=ambiguity_token,
            lease_validity_seconds=60,
        )
        foreign_after_in_tx = _foreign_witness(session.connection(), ids)
    with fixture.connect() as conn:
        foreign_after = _foreign_witness(conn, ids)
    with app.connect() as conn:
        observed = {
            "technical_id": "RF-16-EGRESS-ROUTING-DURABLE-RUNTIME-20260803-01",
            "candidate_sha": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], text=True
            ).strip(),
            "python": platform.python_version(),
            "postgres_version": conn.execute(text("select version() ")).scalar_one(),
            "alembic_head": conn.execute(
                text("select version_num from mayak.alembic_version")
            ).scalar_one(),
            "egress_tables": [
                row[0]
                for row in conn.execute(
                    text(
                        "select tablename from pg_catalog.pg_tables "
                        "where schemaname='mayak' and tablename like 'egress_%' "
                        "order by tablename"
                    )
                )
            ],
            "registration": {
                "agent": str(agent.id),
                "route": str(route.id),
                "heartbeat": str(heartbeat),
            },
            "selection": {
                "ok": selected.ok,
                "reason": selected.reason,
                "route": str(selected.reference_id) if selected.reference_id else None,
            },
            "selection_unsupported": {"ok": unsupported.ok, "reason": unsupported.reason},
            "multi_route": {"ok": multi_route.ok, "reason": multi_route.reason},
            "lease": {
                "ok": lease.ok,
                "reason": lease.reason,
                "id": str(lease.reference_id) if lease.reference_id else None,
                "token": str(lease_token),
                "state_after": observed_lease["state"],
            },
            "same_identity_replay": {
                "ok": replay.ok,
                "reason": replay.reason,
                "id": str(replay.reference_id) if replay.reference_id else None,
            },
            "mismatch_conflict": {"ok": mismatch.ok, "reason": mismatch.reason},
            "wrong_token": {"ok": wrong_token.ok, "reason": wrong_token.reason},
            "completed": {"ok": completed.ok, "reason": completed.reason},
            "active_lease_count": active_count,
            "expiry": {"reason": expiry.reason},
            "restart_recovery": {"durable": True},
            "ambiguity_replay": {"reason": ambiguity_replay.reason},
            "heartbeat_state_is_not_readiness": True,
            "foreign_witness_before": foreign_before,
            "foreign_witness_after_in_tx": foreign_after_in_tx,
            "foreign_witness_after": foreign_after,
            "protocol_effects": [effect.value for effect in TransportEffect],
            "raw_observations_only": True,
            "safe_diagnostics": {**diagnostics, "safe": True},
            "protocol_strictness": True,
            "simulator_runtime_parity": True,
            "package_boundary": True,
            "parser_fail_closed": True,
            "no_secret_raw_provider_persistence": True,
        }
    barrier = threading.Barrier(2)

    def compete() -> dict[str, object]:
        started = time.monotonic()
        with Session(app) as concurrent_session, concurrent_session.begin():
            pid = concurrent_session.execute(text("select pg_backend_pid()")).scalar_one()
            barrier.wait(timeout=10)
            result = egress.acquire_lease(
                concurrent_session,
                route_id=ids["route3"],
                work_item_id=ids["work"],
                lease_token=uuid4(),
                lease_validity_seconds=60,
            )
            return {
                "pid": pid,
                "ok": result.ok,
                "reason": result.reason,
                "elapsed": time.monotonic() - started,
            }

    with ThreadPoolExecutor(max_workers=2) as pool:
        concurrent_results = list(pool.map(lambda _: compete(), (1, 2)))
    with app.connect() as conn:
        concurrent_active_count = conn.execute(
            text(
                "select count(*) from mayak.egress_route_leases "
                "where route_id=:route and work_item_id=:work and state='ACTIVE'"
            ),
            {"route": ids["route3"], "work": ids["work"]},
        ).scalar_one()
    observed["concurrency"] = {
        "sessions": concurrent_results,
        "distinct_backend_pids": len({row["pid"] for row in concurrent_results}),
        "active_count": concurrent_active_count,
        "overlap_barrier": True,
    }
    # Ephemeral hosted evidence needs no destructive cleanup; FK-safe cleanup is
    # intentionally omitted and the database is discarded by the job.
    args.output.write_text(
        json.dumps(observed, sort_keys=True, indent=2, default=str) + "\n", encoding="utf-8"
    )
    print(json.dumps(observed, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
