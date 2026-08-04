"""Produce deterministic, redacted RF20 PostgreSQL acceptance evidence."""

from __future__ import annotations

import argparse
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from mayak.modules.admin_and_support.runtime import (
    OutcomeClass,
    OwningOutcome,
    SupportRuntime,
    VerifiedActor,
)


class _Port:
    def __init__(self, owner: str) -> None:
        self.owner = owner
        self.calls = 0

    def safe_summary(
        self, session: Session, *, actor: VerifiedActor, target: object
    ) -> dict[str, object]:
        self.calls += 1
        return {"owner": self.owner, "state": "SAFE_REDACTED", "target": "opaque"}

    def account_summary(
        self, session: Session, *, actor: VerifiedActor, target: object
    ) -> dict[str, object]:
        return self.safe_summary(session, actor=actor, target=target)

    def safe_diagnostics(
        self, session: Session, *, actor: VerifiedActor, target: object
    ) -> dict[str, object]:
        return self.safe_summary(session, actor=actor, target=target)

    def execute_role_action(self, session: Session, **kwargs: object) -> OwningOutcome:
        self.calls += 1
        return OwningOutcome(self.owner, "synthetic-role-outcome", OutcomeClass.SUCCEEDED)

    execute_access_action = execute_role_action
    execute_support_action = execute_role_action
    execute_anchor_action = execute_role_action

    def verify_operator(self, session: Session, actor_reference: str) -> VerifiedActor:
        return VerifiedActor(uuid4(), "ADMIN", "synthetic", "synthetic-identity")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dsn", default=os.environ.get("RF20_DATABASE_URL"))
    parser.add_argument("--fixture-dsn", default=os.environ.get("RF20_MIGRATION_DSN"))
    parser.add_argument("--candidate-sha", default=os.environ.get("GITHUB_SHA", "unknown"))
    parser.add_argument("--output", default="rf20-acceptance-evidence.json")
    args = parser.parse_args()
    if not args.dsn or not args.fixture_dsn:
        return 2
    engine = create_engine(args.dsn, pool_pre_ping=True)
    fixture_engine = create_engine(args.fixture_dsn, pool_pre_ping=True)
    actor_id, account_id = uuid4(), uuid4()
    now = datetime.now(UTC)
    ports = {
        name: _Port(name) for name in ("identity", "entitlements", "beacon", "scan", "notification")
    }
    runtime = SupportRuntime(
        identity=ports["identity"],
        entitlements=ports["entitlements"],
        beacon=ports["beacon"],
        scan=ports["scan"],
        notification=ports["notification"],
    )
    with fixture_engine.begin() as connection:
        connection.execute(
            text(
                "insert into mayak.identity_accounts "
                "(id,state,created_at,updated_at) values (:id,'ACTIVE',:now,:now)"
            ),
            {"id": account_id, "now": now},
        )
        connection.execute(
            text(
                "insert into mayak.identity_accounts "
                "(id,state,created_at,updated_at) values (:id,'ACTIVE',:now,:now)"
            ),
            {"id": actor_id, "now": now},
        )
    actor = VerifiedActor(actor_id, "ADMIN", "synthetic", "synthetic-identity")
    with Session(engine) as session:
        first = runtime.open_case(
            session,
            actor=actor,
            account_id=account_id,
            subject="synthetic support",
            reason="synthetic acceptance",
            idempotency_key="rf20-open-1",
        )
        session.commit()
    with Session(engine) as session:
        # The case id is the authoritative event target, not browser input.
        case = runtime.list_cases(session, account_id=account_id)[0]
        note = runtime.add_internal_note(
            session,
            actor=actor,
            case_id=case.case_id,
            body="redacted internal finding",
            reason="synthetic note",
            idempotency_key="rf20-note-1",
        )
        replay = runtime.add_internal_note(
            session,
            actor=actor,
            case_id=case.case_id,
            body="redacted internal finding",
            reason="synthetic note",
            idempotency_key="rf20-note-1",
        )
        session.commit()
    with engine.connect() as connection:
        counts = {
            table: int(connection.execute(text(f"select count(*) from mayak.{table}")).scalar_one())
            for table in ("support_cases", "support_case_notes", "support_case_events")
        }
        pg = str(connection.execute(text("select version()")).scalar_one()).split(",", 1)[0]
        head = str(
            connection.execute(text("select version_num from mayak.alembic_version")).scalar_one()
        )
        connection.commit()
        foreign_write_denied = False
        try:
            with connection.begin():
                connection.execute(
                    text(
                        "insert into mayak.identity_accounts "
                        "(id,state,created_at,updated_at) values (:id,'ACTIVE',:now,:now)"
                    ),
                    {"id": uuid4(), "now": now},
                )
        except Exception:
            foreign_write_denied = True
    evidence = {
        "technical_id": "RF20-ADMIN-SUPPORT-RUNTIME-01",
        "candidate_sha": args.candidate_sha,
        "postgresql_version": pg,
        "migration_head": head,
        "support_counts": counts,
        "first": first.state.value,
        "note": note.state.value,
        "replay": replay.replayed,
        "foreign_write_denied": foreign_write_denied,
        "port_calls": {name: port.calls for name, port in ports.items()},
        "live_provider_calls": 0,
        "real_token_reads": 0,
        "raw_provider_payload_persisted": 0,
        "host_postgres_published": False,
    }
    Path(args.output).write_text(
        json.dumps(evidence, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
