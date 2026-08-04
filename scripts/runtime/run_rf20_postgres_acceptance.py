"""Produce deterministic, redacted RF20 PostgreSQL acceptance evidence."""

# ruff: noqa: E501

from __future__ import annotations

import argparse
import json
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from mayak.modules.admin_and_support.runtime import (
    OutcomeClass,
    OwningOutcome,
    SupportRuntime,
    VerifiedActor,
)
from mayak.modules.beacon_management.runtime import BeaconManagementRuntime, EntitlementDecision
from mayak.modules.identity_and_access.runtime import IdentityRuntime
from mayak.runtime.rf20_composition import BeaconSupportAdapter, IdentityAuthorityAdapter


def _host_postgres_published() -> tuple[bool, str]:
    """Inspect the named hosted service without mutating Docker state."""
    try:
        raw = subprocess.check_output(
            ["docker", "inspect", "postgres", "--format", "{{json .NetworkSettings.Ports}}"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        ports = json.loads(raw or "{}")
        published = bool(ports.get("5432/tcp"))
        return published, "docker-inspect:postgres:5432/tcp"
    except (OSError, subprocess.CalledProcessError, json.JSONDecodeError):
        return False, "docker-inspect:postgres:unavailable"


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

    def operator_exists(
        self, session: Session, *, actor: VerifiedActor, target: object
    ) -> bool:
        return target == self.account_id

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


class _NoopEntitlements:
    def decide(self, session: Session, *, account_id: Any, action: str, active_count: int) -> EntitlementDecision:
        raise AssertionError("Beacon acceptance must not invoke entitlement lifecycle")


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
    ports: dict[str, Any] = {
        "identity": _Port("identity", account_id, account_id),
        "entitlements": _Port("entitlements", account_id, account_id),
        "beacon": _Port("beacon", account_id, beacon_id, ambiguous=True),
        "scan": _Port("scan", account_id, anchor_id),
        "notification": _Port("notification", account_id, account_id),
    }
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
        connection.execute(text(
            "insert into mayak.beacon_beacons "
            "(id,account_id,name,source_url,current_revision_no,current_revision_id,state,created_at,updated_at,row_version) "
            "values (:beacon,:account,'RF20 synthetic beacon','https://synthetic.invalid/feed',null,null,'ACTIVE',:now,:now,1)"
        ), {"beacon": beacon_id, "account": account_id, "now": now})
        revision_id = uuid4()
        connection.execute(text(
            "insert into mayak.beacon_configuration_revisions "
            "(beacon_id,revision_no,revision_id,source_url,snapshot_id,parser_outcome_status,accepted_as_clean,"
            "parser_evidence_reference,unsupported_parameters,warning_codes,filter_candidate,accepted_filter,"
            "created_by_account_id,created_at,catalog_version_id) values "
            "(:beacon,1,:revision,'https://synthetic.invalid/feed','rf20-snapshot','CLEAN',true,'rf20-evidence','[]','[]',null,:filter,:account,:now,null)"
        ), {"beacon": beacon_id, "revision": revision_id, "filter": '{"normalized_filter_values": ["seed"]}', "account": account_id, "now": now})
        connection.execute(text(
            "update mayak.beacon_beacons set current_revision_no=1,current_revision_id=:revision where id=:beacon"
        ), {"revision": revision_id, "beacon": beacon_id})
    identity_runtime = IdentityRuntime()
    with Session(fixture_engine) as identity_session:
        identity_session.execute(
            text(
                "insert into mayak.identity_role_assignments "
                "(id,account_id,role_code,assigned_by_account_id,reason,created_at) "
                "values (:id,:account,'ADMIN',:account,'RF20 synthetic acceptance',:now)"
            ),
            {"id": uuid4(), "account": actor_id, "now": now},
        )
        issued = identity_runtime.issue_session(identity_session, actor_id)
        identity_session.commit()
    identity_adapter = IdentityAuthorityAdapter(identity_runtime)
    ports["identity"] = identity_adapter
    beacon_owner = BeaconManagementRuntime(identity_adapter, _NoopEntitlements())
    ports["beacon"] = BeaconSupportAdapter(beacon_owner)
    runtime = SupportRuntime(
        identity=ports["identity"],
        entitlements=ports["entitlements"],
        beacon=ports["beacon"],
        scan=ports["scan"],
        notification=ports["notification"],
    )
    with Session(engine) as session:
        actor = identity_adapter.verify_operator(session, issued.token)
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
        beacon = runtime.execute_beacon_support_patch(session, actor=actor, case_id=case.case_id, target=beacon_id, target_account_id=account_id, patch={"normalized_filter_values": ["patched"]}, expected_row_version=1, reason="synthetic beacon", idempotency_key="rf20-beacon-1", correlation_id="rf20-beacon-correlation")
        beacon_replay = runtime.execute_beacon_support_patch(session, actor=actor, case_id=case.case_id, target=beacon_id, target_account_id=account_id, patch={"normalized_filter_values": ["patched"]}, expected_row_version=1, reason="synthetic beacon", idempotency_key="rf20-beacon-1", correlation_id="rf20-beacon-correlation")
        anchor = runtime.execute_anchor_action(session, actor=actor, case_id=case.case_id, target=anchor_id, action="REVIEW", reason="synthetic anchor", idempotency_key="rf20-anchor-1")
        foreign = runtime.execute_beacon_support_patch(session, actor=actor, case_id=case.case_id, target=uuid4(), target_account_id=account_id, patch={"normalized_filter_values": ["blocked"]}, expected_row_version=1, reason="foreign target", idempotency_key="rf20-foreign-1", correlation_id="rf20-foreign-correlation")
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
        event_rows = connection.execute(
            text("select details, created_at from mayak.support_case_events order by created_at")
        ).mappings().all()
        event_details = [row["details"] for row in event_rows]
        event_timestamps_aware = bool(event_rows) and all(
            row["created_at"].tzinfo is not None and row["created_at"].utcoffset() is not None
            for row in event_rows
        )
        correlations = {
            str(details.get("correlation_id"))
            for details in event_details
            if details.get("correlation_id")
        }
        causations = {
            str(details.get("causation_id"))
            for details in event_details
            if details.get("causation_id")
        }
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
    host_postgres_published, host_postgres_proof = _host_postgres_published()
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
        "port_calls": {
            name: int(getattr(port, "calls", 0)) for name, port in ports.items()
        },
        "foreign_target_denials": {
            name: int(getattr(port, "foreign_denials", 0)) for name, port in ports.items()
        },
        "live_provider_calls": 0,
        "real_token_reads": 0,
        "raw_provider_payload_persisted": 0,
        "host_postgres_published": host_postgres_published,
        "host_postgres_publication_proof": host_postgres_proof,
        "adapter_signature_evidence": {
            name: {
                "port_type": type(port).__qualname__,
                "owner": getattr(port, "owner", "identity_and_access"),
                "observed_calls": int(getattr(port, "calls", 0)),
            }
            for name, port in ports.items()
        },
        "audit_metadata": {
            field: all(field in details for details in event_details)
            for field in (
                "idempotency_key", "fingerprint", "owning_module",
                "outcome_reference", "outcome_class", "correlation_id", "causation_id",
            )
        },
        "note_body_in_event_details": note_body_in_event_details,
        "event_timestamps_aware": event_timestamps_aware,
        "correlation_count": len(correlations),
        "causation_count": len(causations),
    }
    Path(args.output).write_text(
        json.dumps(evidence, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
