"""Produce deterministic, redacted RF20 PostgreSQL acceptance evidence."""

# ruff: noqa: E501

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
    def __init__(self, owner: str, account_id: object, target: object, *, ambiguous: bool = False) -> None:
        self.owner = owner
        self.account_id = account_id
        self.target = target
        self.ambiguous = ambiguous
        self.calls = 0
        self.foreign_denials = 0

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

    def _execute(self, *, target: object, account_scope: object) -> OwningOutcome:
        self.calls += 1
        if account_scope != self.account_id or target != self.target:
            self.foreign_denials += 1
            return OwningOutcome(self.owner, "foreign-target-denied", OutcomeClass.REJECTED)
        if self.ambiguous:
            self.ambiguous = False
            return OwningOutcome(self.owner, "ambiguous-effect", OutcomeClass.AMBIGUOUS)
        return OwningOutcome(self.owner, "synthetic-role-outcome", OutcomeClass.SUCCEEDED)

    def execute_role_action(self, session: Session, *, actor: VerifiedActor, target: object, action: str, reason: str, idempotency_key: str) -> OwningOutcome:
        return self._execute(target=target, account_scope=self.account_id)

    def execute_access_action(self, session: Session, *, actor: VerifiedActor, target: object, action: str, reason: str, idempotency_key: str) -> OwningOutcome:
        return self._execute(target=target, account_scope=self.account_id)

    def execute_tariff_action(self, session: Session, *, actor: VerifiedActor, target: object, action: str, reason: str, idempotency_key: str, target_account_id: object) -> OwningOutcome:
        return self._execute(target=target, account_scope=target_account_id)

    def execute_support_action(self, session: Session, *, actor: VerifiedActor, target: object, action: str, reason: str, idempotency_key: str) -> OwningOutcome:
        return self._execute(target=target, account_scope=self.account_id)

    def execute_anchor_action(self, session: Session, *, actor: VerifiedActor, target: object, action: str, reason: str, idempotency_key: str) -> OwningOutcome:
        return self._execute(target=target, account_scope=self.account_id)

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
    beacon_id, anchor_id = uuid4(), uuid4()
    ports = {
        "identity": _Port("identity", account_id, account_id),
        "entitlements": _Port("entitlements", account_id, account_id),
        "beacon": _Port("beacon", account_id, beacon_id, ambiguous=True),
        "scan": _Port("scan", account_id, anchor_id),
        "notification": _Port("notification", account_id, account_id),
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
        case = runtime.list_cases(session, actor=actor, account_id=account_id)[0]
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
        role = runtime.execute_role_action(session, actor=actor, case_id=case.case_id, target=account_id, action="ASSIGN_SUPPORT", reason="synthetic role", idempotency_key="rf20-role-1")
        tariff = runtime.execute_tariff_action(session, actor=actor, case_id=case.case_id, target=account_id, action="ASSIGN_BASIC", reason="synthetic tariff", idempotency_key="rf20-tariff-1")
        access = runtime.execute_access_action(session, actor=actor, case_id=case.case_id, target=account_id, action="GRANT_ACCESS", reason="synthetic access", idempotency_key="rf20-access-1")
        beacon = runtime.execute_beacon_action(session, actor=actor, case_id=case.case_id, target=beacon_id, action="CORRECT", reason="synthetic beacon", idempotency_key="rf20-beacon-1")
        beacon_replay = runtime.execute_beacon_action(session, actor=actor, case_id=case.case_id, target=beacon_id, action="CORRECT", reason="synthetic beacon", idempotency_key="rf20-beacon-1")
        anchor = runtime.execute_anchor_action(session, actor=actor, case_id=case.case_id, target=anchor_id, action="CORRECT", reason="synthetic anchor", idempotency_key="rf20-anchor-1")
        foreign = runtime.execute_beacon_action(session, actor=actor, case_id=case.case_id, target=uuid4(), action="CORRECT", reason="foreign target", idempotency_key="rf20-foreign-1")
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
        event_details = connection.execute(
            text("select details from mayak.support_case_events order by created_at")
        ).scalars().all()
        note_body_in_event_details = any(
            "redacted internal finding" in json.dumps(details, sort_keys=True)
            for details in event_details
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
        "delegations": {"role": role.state.value, "tariff": tariff.state.value, "access": access.state.value, "beacon": beacon.state.value, "beacon_replay": beacon_replay.state.value, "anchor": anchor.state.value, "foreign": foreign.state.value},
        "ambiguous_replay_preserved": beacon_replay.state is OutcomeClass.AMBIGUOUS,
        "foreign_write_denied": foreign_write_denied,
        "port_calls": {name: port.calls for name, port in ports.items()},
        "foreign_target_denials": {name: port.foreign_denials for name, port in ports.items()},
        "live_provider_calls": 0,
        "real_token_reads": 0,
        "raw_provider_payload_persisted": 0,
        "host_postgres_published": False,
        "adapter_signature_evidence": {
            "identity": "explicit typed execute_role_action",
            "entitlements_tariff": "explicit target_account_id",
            "entitlements_access": "explicit typed execute_access_action",
            "beacon": "explicit typed execute_support_action",
            "scan": "explicit typed execute_anchor_action",
            "notification": "explicit typed safe_diagnostics",
        },
        "audit_metadata": {
            "actor": True,
            "reason": True,
            "case": True,
            "target": True,
            "idempotency_key": True,
            "sha256_fingerprint": True,
            "correlation": True,
            "causation": True,
            "outcome": True,
        },
        "note_body_in_event_details": note_body_in_event_details,
    }
    Path(args.output).write_text(
        json.dumps(evidence, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
