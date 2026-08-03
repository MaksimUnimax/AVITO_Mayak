"""RF16 raw PostgreSQL observations; no producer-authored pass flag."""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from sqlalchemy import create_engine, delete, select, text
from sqlalchemy.orm import Session

from mayak.modules.egress_routing import EgressRuntime
from mayak.persistence.metadata import metadata


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
    ids = {
        "account": uuid4(),
        "beacon": uuid4(),
        "schedule": uuid4(),
        "work": uuid4(),
        "agent": uuid4(),
        "route": uuid4(),
    }
    now = datetime.now(UTC)
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
    egress = EgressRuntime()
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
        selected = egress.select_route(session)
        lease = egress.acquire_lease(
            session, route_id=route.id, work_item_id=ids["work"], lease_seconds=60
        )
        replay = egress.acquire_lease(
            session,
            route_id=route.id,
            work_item_id=ids["work"],
            lease_token=uuid4(),
            lease_seconds=60,
        )
        diagnostics = egress.safe_diagnostics(
            session, route_id=route.id, lease_id=lease.reference_id
        )
        foreign_before = session.execute(
            text("select count(*) from mayak.scan_work_items")
        ).scalar_one()
        egress.resolve_lease(
            session, lease_id=lease.reference_id, lease_token=uuid4(), terminal_state="COMPLETED"
        )
        egress.resolve_lease(
            session,
            lease_id=lease.reference_id,
            lease_token=session.execute(
                select(metadata.tables["mayak.egress_route_leases"].c.lease_token).where(
                    metadata.tables["mayak.egress_route_leases"].c.id == lease.reference_id
                )
            ).scalar_one(),
            terminal_state="AMBIGUOUS",
        )
        foreign_after = session.execute(
            text("select count(*) from mayak.scan_work_items")
        ).scalar_one()
    with app.connect() as conn:
        observed = {
            "technical_id": "RF-16-EGRESS-ROUTING-DURABLE-RUNTIME-20260803-01",
            "candidate_sha": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], text=True
            ).strip(),
            "python": platform.python_version(),
            "postgres_version": conn.execute(text("select version()")).scalar_one(),
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
            "registration_agent": str(agent.id),
            "registration_route": str(route.id),
            "heartbeat": str(heartbeat),
            "selected": {
                "ok": selected.ok,
                "reason": selected.reason,
                "reference_id": str(selected.reference_id) if selected.reference_id else None,
            },
            "lease": {
                "ok": lease.ok,
                "reason": lease.reason,
                "reference_id": str(lease.reference_id) if lease.reference_id else None,
            },
            "replay": {"ok": replay.ok, "reason": replay.reason},
            "foreign_table_count_before_after": [foreign_before, foreign_after],
            "safe_diagnostics": diagnostics,
        }
    with fixture.begin() as conn:
        conn.execute(delete(work).where(work.c.id == ids["work"]))
        conn.execute(delete(schedule).where(schedule.c.id == ids["schedule"]))
        conn.execute(delete(beacon).where(beacon.c.id == ids["beacon"]))
        conn.execute(delete(identity).where(identity.c.id == ids["account"]))
    args.output.write_text(
        json.dumps(observed, sort_keys=True, indent=2, default=str) + "\n", encoding="utf-8"
    )
    print(json.dumps(observed, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
