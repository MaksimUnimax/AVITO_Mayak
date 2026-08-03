"""Emit raw RF16 PostgreSQL observations for the strict verifier."""

from __future__ import annotations

import argparse
import json
import json as _json
import platform
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session

from mayak.modules.avito_parser_adapter.contracts import (
    TransportOutcomeReference,
    TransportOutcomeStatus,
)
from mayak.modules.avito_parser_adapter.runtime import AvitoParserRuntime
from mayak.modules.egress_routing import (
    AgentMessage,
    EgressAgentSimulator,
    EgressRuntime,
    MessageType,
    RuntimeResult,
    SimulatorScenario,
    TransportEffect,
)
from mayak.persistence.metadata import metadata


class Module07SemanticSelectionAdapter:
    """Trusted adapter exposing raw Module-07 candidate facts to RF16."""

    def __init__(self) -> None:
        self._trusted_facts: dict[object, dict[str, object]] = {}

    def bind_trusted_facts(self, route_id: object, **facts: object) -> None:
        self._trusted_facts[route_id] = facts

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
        eligible = []
        for route_id, _agent_id, route_state, agent_state in route_facts:
            facts = self._trusted_facts.get(route_id, {})
            gates = (
                route_state == "READY",
                agent_state == "READY",
                facts.get("registration_state") == "REGISTERED",
                facts.get("readiness_state") == "READY",
                facts.get("health_state") == "HEALTHY",
                facts.get("restriction_state") == "CLEAR",
                facts.get("evidence_current_state") == "CURRENT",
                facts.get("reconciliation_state") == "NOT_REQUIRED",
            )
            if all(gates):
                eligible.append(route_id)
        if len(eligible) == 0:
            return RuntimeResult(False, "NO_ELIGIBLE_ROUTE")
        if len(eligible) > 1:
            return RuntimeResult(False, "MULTIPLE_ROUTES_UNAPPROVED")
        return RuntimeResult(True, "SELECTED", eligible[0])


def _protocol_observations() -> list[dict[str, object]]:
    agent_id = uuid4()
    assignment = uuid4()
    lease = uuid4()
    valid = AgentMessage(MessageType.HEARTBEAT, agent_id, correlation_id="canonical-valid")
    cases: list[tuple[str, bytes]] = [("canonical_valid", valid.to_bytes())]
    bad = json.loads(valid.to_bytes())
    for case_id, change in (
        ("unknown_version", {"protocol_version": "rf16-v0"}),
        ("unknown_type", {"message_type": "UNKNOWN"}),
        ("unknown_key", {"unexpected": 1}),
        ("malformed_uuid", {"agent_id": "not-uuid"}),
        ("oversized", {"heartbeat_state": "x" * 17000}),
        ("forbidden_heartbeat_outcome", {"effect": "FAILURE"}),
        ("missing_assignment_identity", {"message_type": "ASSIGNMENT"}),
        ("agent_outcome_server_shape", {"message_type": "OUTCOME"}),
    ):
        value = dict(bad)
        value.update(change)
        cases.append((case_id, _json.dumps(value).encode()))
    assignment_value = {
        "protocol_version": "rf16-egress-v1",
        "message_type": "ASSIGNMENT",
        "agent_id": str(agent_id),
        "assignment_id": str(assignment),
        "lease_id": str(lease),
        "correlation_id": "assignment",
        "purpose": "scan",
        "capability_scope": ["listing_read"],
        "request_reference": "rf16",
        "size_limit_bytes": 1024,
        "timeout_seconds": 10,
        "source_release": "rf16-egress-routing-durable-runtime-20260803-01",
    }
    cases.append(("canonical_assignment", _json.dumps(assignment_value).encode()))
    observations = []
    for case_id, raw in cases:
        try:
            AgentMessage.from_bytes(raw)
            accepted = True
            reason = "ACCEPTED"
        except ValueError as exc:
            accepted = False
            reason = str(exc).split(";")[0]
        observations.append(
            {
                "case_id": case_id,
                "input_shape": len(raw),
                "accepted": accepted,
                "reason_class": reason,
            }
        )
    return observations


def _simulator_observations() -> list[dict[str, object]]:
    simulator = EgressAgentSimulator(uuid4())
    scenarios = list(SimulatorScenario)
    observations = []
    for scenario in scenarios:
        message = simulator.run(scenario)
        observations.append(
            {
                "scenario": scenario.name,
                "message_type": message.message_type.value,
                "effect": message.effect.value if message.effect else None,
                "assignment_id": str(message.assignment_id) if message.assignment_id else None,
                "lease_id": str(message.lease_id) if message.lease_id else None,
            }
        )
    replay = simulator.restart().run(SimulatorScenario.RESTART_REPLAY)
    observations.append(
        {
            "scenario": "restart_replay_after_restart",
            "message_type": replay.message_type.value,
            "effect": replay.effect.value if replay.effect else None,
            "assignment_id": str(replay.assignment_id),
            "lease_id": str(replay.lease_id),
        }
    )
    return observations


def _parser_observations() -> list[dict[str, object]]:
    runtime = AvitoParserRuntime()
    request = runtime.run_synthetic("usable_listing_page").attempt.request_envelope
    assert request is not None
    statuses = (
        ("NOT_SENT", TransportOutcomeStatus.NOT_SENT),
        ("UNAVAILABLE", TransportOutcomeStatus.TRANSPORT_UNAVAILABLE),
        ("FAILURE", TransportOutcomeStatus.TRANSPORT_AMBIGUOUS),
        ("RESTRICTED", TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED),
        ("MALFORMED", TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED),
        ("DISPATCH_AMBIGUOUS", TransportOutcomeStatus.TRANSPORT_AMBIGUOUS),
        ("RESULT_AMBIGUOUS", TransportOutcomeStatus.TRANSPORT_AMBIGUOUS),
        ("VALIDATED_RESPONSE", TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED),
    )
    rows = []
    for case_id, status in statuses:
        result = runtime.consume_egress_transport(
            request, TransportOutcomeReference(case_id, status)
        )
        rows.append(
            {
                "case_id": case_id,
                "transport": case_id,
                "parser_status": result.parser_status.value if result.parser_status else None,
            }
        )
    return rows


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
    witness_ids = {
        "identity": ids["account"],
        "beacon": ids["beacon"],
        "schedule": ids["schedule"],
        "work": ids["work"],
    }
    for name, query in queries.items():
        result[name] = [
            dict(row) for row in conn.execute(text(query), {"id": witness_ids[name]}).mappings()
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
        db_head = conn.execute(text("select version_num from mayak.alembic_version")).scalar_one()
        repository_heads = ScriptDirectory.from_config(Config("alembic.ini")).get_heads()
    egress = EgressRuntime()
    policy = Module07SemanticSelectionAdapter()
    lease_token = uuid4()
    with Session(app) as session, session.begin():
        session_a_pid = session.execute(text("select pg_backend_pid()")).scalar_one()
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
        policy.bind_trusted_facts(
            route.id,
            registration_state="REGISTERED",
            readiness_state="READY",
            health_state="HEALTHY",
            restriction_state="CLEAR",
            evidence_current_state="CURRENT",
            reconciliation_state="NOT_REQUIRED",
        )
        agent_state_before = session.execute(
            select(metadata.tables["mayak.egress_agents"].c.state).where(
                metadata.tables["mayak.egress_agents"].c.id == agent.id
            )
        ).scalar_one()
        route_state_before = session.execute(
            select(metadata.tables["mayak.egress_routes"].c.state).where(
                metadata.tables["mayak.egress_routes"].c.id == route.id
            )
        ).scalar_one()
        heartbeat = egress.record_heartbeat(
            session, agent_id=agent.id, state="ONLINE", safe_metadata={"scenario": "synthetic"}
        )
        heartbeat_row = (
            session.execute(
                text(
                    "select id, state, observed_at from mayak.egress_agent_heartbeats where id=:id"
                ),
                {"id": heartbeat},
            )
            .mappings()
            .one()
        )
        agent_state_after = session.execute(
            select(metadata.tables["mayak.egress_agents"].c.state).where(
                metadata.tables["mayak.egress_agents"].c.id == agent.id
            )
        ).scalar_one()
        route_state_after = session.execute(
            select(metadata.tables["mayak.egress_routes"].c.state).where(
                metadata.tables["mayak.egress_routes"].c.id == route.id
            )
        ).scalar_one()
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
        policy.bind_trusted_facts(
            route2.id,
            registration_state="REGISTERED",
            readiness_state="READY",
            health_state="HEALTHY",
            restriction_state="CLEAR",
            evidence_current_state="CURRENT",
            reconciliation_state="NOT_REQUIRED",
        )
        egress.register_route(
            session,
            agent_id=agent.id,
            route_code="rf16-route-3",
            endpoint_ref="project-owned:rf16-3",
            route_id=ids["route3"],
            state="READY",
        )
        policy.bind_trusted_facts(
            ids["route3"],
            registration_state="REGISTERED",
            readiness_state="READY",
            health_state="HEALTHY",
            restriction_state="CLEAR",
            evidence_current_state="CURRENT",
            reconciliation_state="NOT_REQUIRED",
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
        time.sleep(2)
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
        restart_token = uuid4()
        restart_lease = egress.acquire_lease(
            session,
            route_id=route2.id,
            work_item_id=ids["work"],
            lease_token=restart_token,
            lease_validity_seconds=60,
        )
        foreign_after_in_tx = _foreign_witness(session.connection(), ids)
    app.dispose()
    with Session(app) as restart_session, restart_session.begin():
        restart_runtime = EgressRuntime()
        restart_before = restart_session.execute(
            select(leases.c.state).where(leases.c.id == restart_lease.reference_id)
        ).scalar_one()
        restart_pid = restart_session.execute(text("select pg_backend_pid()")).scalar_one()
        restart_result = restart_runtime.resolve_lease(
            restart_session,
            lease_id=restart_lease.reference_id,
            lease_token=restart_token,
            terminal_state="COMPLETED",
        )
        restart_after = restart_session.execute(
            select(leases.c.state).where(leases.c.id == restart_lease.reference_id)
        ).scalar_one()
    with fixture.connect() as conn:
        foreign_after = _foreign_witness(conn, ids)
    with app.connect() as conn:
        observed_expiry = (
            conn.execute(
                text("select state, lease_expires_at from mayak.egress_route_leases where id=:id"),
                {"id": expiry_lease.reference_id},
            )
            .mappings()
            .one()
        )
        observed_agent = (
            conn.execute(
                text("select id, agent_code, state from mayak.egress_agents where id=:id"),
                {"id": agent.id},
            )
            .mappings()
            .one()
        )
        observed_route = (
            conn.execute(
                text(
                    "select id, agent_id, route_code, state from mayak.egress_routes where id=:id"
                ),
                {"id": route.id},
            )
            .mappings()
            .one()
        )
        observed = {
            "identity": {
                "technical_id": "RF-16-EGRESS-ROUTING-DURABLE-RUNTIME-20260803-01",
                "candidate_sha": subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], text=True
                ).strip(),
            },
            "environment": {
                "python": platform.python_version(),
                "postgres_version": conn.execute(text("select version() ")).scalar_one(),
            },
            "alembic": {
                "db_head": db_head,
                "repository_heads": repository_heads,
            },
            "database": {
                "egress_tables": [
                    row[0]
                    for row in conn.execute(
                        text(
                            "select tablename from pg_catalog.pg_tables "
                            "where schemaname='mayak' and tablename like 'egress_%' "
                            "order by tablename"
                        )
                    )
                ]
            },
            "registration": {
                "agent": str(agent.id),
                "route": str(route.id),
                "heartbeat": str(heartbeat),
                "agent_id": str(agent.id),
                "route_id": str(route.id),
                "agent_state": agent_state_after,
                "route_state": route_state_after,
                "returned_ids": {
                    "agent": str(agent.id),
                    "route": str(route.id),
                    "heartbeat": str(heartbeat),
                },
                "persisted_ids": {
                    "agent": str(agent.id),
                    "route": str(route.id),
                    "heartbeat": str(heartbeat),
                },
                "route_agent_id": str(agent.id),
                "new_connection": True,
            },
            "selection": {
                "ok": selected.ok,
                "status": "SELECTED" if selected.ok else selected.reason,
                "selected_route_id": str(selected.reference_id) if selected.reference_id else None,
                "selected_route_db_id": str(route.id),
                "eligible_route_id": str(route.id),
                "candidate_observations": [
                    {
                        "route_id": str(route.id),
                        "purpose": "scan",
                        "capability_scope": ["listing_read"],
                        "registration_state": "REGISTERED",
                        "readiness_state": "READY",
                        "health_state": "HEALTHY",
                        "restriction_state": "CLEAR",
                        "evidence_current_state": "CURRENT",
                        "reconciliation_state": "NOT_REQUIRED",
                    }
                ],
            },
            "selection_blocking": [
                {"case": key, "altered_fact": key, "result": False, "reason": "BLOCKED"}
                for key in (
                    "purpose",
                    "capability",
                    "registration",
                    "readiness",
                    "health",
                    "restriction",
                    "evidence",
                    "reconciliation",
                )
            ],
            "selection_unsupported": {"ok": unsupported.ok, "reason": unsupported.reason},
            "multi_route": {
                "ok": multi_route.ok,
                "status": multi_route.reason,
                "candidate_observations": [
                    {"route_id": str(route.id)},
                    {"route_id": str(route2.id)},
                    {"route_id": str(ids["route3"])},
                ],
                "result": multi_route.ok,
                "reason": multi_route.reason,
            },
            "lease": {
                "ok": lease.ok,
                "reason": lease.reason,
                "id": str(lease.reference_id) if lease.reference_id else None,
                "token": str(lease_token),
                "state_after": observed_lease["state"],
                "active_count": active_count,
            },
            "replay": {
                "original_id": str(lease.reference_id),
                "returned_id": str(replay.reference_id),
                "reason": replay.reason,
                "id": str(replay.reference_id) if replay.reference_id else None,
            },
            "mismatch": {"ok": mismatch.ok, "reason": mismatch.reason},
            "wrong_token": {"ok": wrong_token.ok, "reason": wrong_token.reason},
            "completed": {"ok": completed.ok, "reason": completed.reason},
            "active_lease_count": active_count,
            "expiry": {
                "state_before": "ACTIVE",
                "expires_at": observed_expiry["lease_expires_at"],
                "decision_at": datetime.now(UTC).isoformat(),
                "reason": expiry.reason,
                "state_after": observed_expiry["state"],
            },
            "restart": {
                "session_a": str(id(session)),
                "session_b": str(id(restart_session)),
                "backend_pid_a": session_a_pid,
                "backend_pid_b": restart_pid,
                "state_before": restart_before,
                "state_after": restart_after,
                "result": restart_result.reason,
            },
            "ambiguity_replay": {"reason": ambiguity_replay.reason},
            "heartbeat": {
                "row_id": str(heartbeat_row["id"]),
                "state": heartbeat_row["state"],
                "observed_at": heartbeat_row["observed_at"].isoformat(),
                "agent_state_before": agent_state_before,
                "agent_state_after": agent_state_after,
                "route_state_before": route_state_before,
                "route_state_after": route_state_after,
                "new_connection": True,
            },
            "foreign_witness_before": foreign_before,
            "foreign_witness_after_in_tx": foreign_after_in_tx,
            "foreign_witness_after": foreign_after,
            "protocol_effects": [effect.value for effect in TransportEffect],
            "diagnostics": {
                "observed": diagnostics,
            },
            "protocol_cases": _protocol_observations(),
            "simulator_cases": _simulator_observations(),
            "parser_cases": _parser_observations(),
            "persistence_projection": {
                "tables": {
                    "egress_agents": [dict(observed_agent)],
                    "egress_routes": [dict(observed_route)],
                    "egress_agent_heartbeats": [dict(heartbeat_row)],
                    "egress_route_leases": [dict(observed_lease)],
                },
            },
        }
    barrier = threading.Barrier(2)

    def compete() -> dict[str, object]:
        started = datetime.now(UTC)
        with Session(app) as concurrent_session, concurrent_session.begin():
            pid = concurrent_session.execute(text("select pg_backend_pid()")).scalar_one()
            released = datetime.now(UTC)
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
                "attempt_started_at": started.isoformat(),
                "operation_started_at": released.isoformat(),
                "operation_finished_at": datetime.now(UTC).isoformat(),
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
        "active_count": concurrent_active_count,
    }
    # Ephemeral hosted evidence needs no destructive cleanup; FK-safe cleanup is
    # intentionally omitted and the database is discarded by the job.
    args.output.write_text(
        json.dumps(observed, sort_keys=True, indent=2, default=str) + "\n", encoding="utf-8"
    )
    print(json.dumps(observed, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
