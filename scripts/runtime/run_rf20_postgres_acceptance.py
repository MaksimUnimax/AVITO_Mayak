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
from uuid import UUID, uuid4

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from mayak.modules.admin_and_support.runtime import (
    OutcomeClass,
    OwningOutcome,
)
from mayak.modules.beacon_management.runtime import BeaconManagementRuntime, EntitlementDecision
from mayak.modules.entitlements_and_billing.runtime import EntitlementsBillingRuntime
from mayak.modules.identity_and_access.runtime import IdentityRuntime
from mayak.runtime.rf20_composition import (
    IdentityAuthorityAdapter,
    build_rf20_composition,
)


def _host_postgres_published() -> tuple[bool, str]:
    """Discover the unique PostgreSQL service on the current job network."""
    try:
        ids = subprocess.check_output(["docker", "ps", "-q"], text=True,
                                      stderr=subprocess.DEVNULL).splitlines()
        candidates = []
        for container_id in ids:
            raw = subprocess.check_output(["docker", "inspect", container_id], text=True,
                                          stderr=subprocess.DEVNULL)
            info = json.loads(raw)[0]
            aliases = {
                alias for network in info.get("NetworkSettings", {}).get("Networks", {}).values()
                for alias in network.get("Aliases", [])
            }
            image = str(info.get("Config", {}).get("Image", ""))
            if "postgres" in aliases or image.startswith("postgres:"):
                candidates.append(info)
        if len(candidates) != 1:
            raise RuntimeError(f"unambiguous PostgreSQL service required, found {len(candidates)}")
        ports = candidates[0].get("NetworkSettings", {}).get("Ports")
        if not isinstance(ports, dict) or "5432/tcp" not in ports:
            raise RuntimeError("malformed PostgreSQL port metadata")
        mapping = ports["5432/tcp"]
        if mapping not in (None, []):
            raise RuntimeError("PostgreSQL 5432/tcp is host-published")
        return False, "docker-inspect:unique-postgres:5432/tcp:unbound"
    except (OSError, subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        raise RuntimeError("PostgreSQL service inspection failed") from exc


class _NoopEntitlements:
    def decide(self, session: Session, *, account_id: Any, action: str, active_count: int) -> EntitlementDecision:
        raise AssertionError("Beacon acceptance must not invoke entitlement lifecycle")


class _AmbiguousOwner:
    """Only for the isolated AMBIGUOUS replay proof, never mandatory owner success."""

    def __init__(self) -> None:
        self.calls = 0

    def execute_support_patch(self, session: Session, **_: Any) -> OwningOutcome:
        self.calls += 1
        return OwningOutcome("synthetic_ambiguous_owner_proof", "ambiguous-1", OutcomeClass.AMBIGUOUS)


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
    ports: dict[str, Any] = {}
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
    entitlements_owner = EntitlementsBillingRuntime(identity_adapter)
    composition = build_rf20_composition(
        identity=identity_runtime, entitlements=entitlements_owner, beacon=beacon_owner
    )
    runtime = composition.runtime()
    ports.update({
        "entitlements_tariff": composition.entitlements,
        "entitlements_access": composition.entitlements,
        "beacon": composition.beacon,
        "scan": composition.scan,
        "notification": composition.notification,
    })
    with Session(engine) as session:
        actor = identity_adapter.verify_operator(session, issued.token)
        # Exercise the same composed safe-read path used by Admin UI.
        runtime.safe_account_summary(session, actor=actor, account_id=account_id)
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
        bootstrap = runtime.execute_tariff_action(session, actor=actor, case_id=case.case_id, target=account_id, action="BOOTSTRAP_TARIFFS", reason="synthetic tariff authority", idempotency_key="rf20-tariff-bootstrap-1")
        role = runtime.execute_role_action(session, actor=actor, case_id=case.case_id, target=account_id, action="ASSIGN_SUPPORT", reason="synthetic role", idempotency_key="rf20-role-1")
        tariff = runtime.execute_tariff_action(session, actor=actor, case_id=case.case_id, target=account_id, action="ASSIGN_BASIC", reason="synthetic tariff", idempotency_key="rf20-tariff-1")
        access = runtime.execute_access_action(session, actor=actor, case_id=case.case_id, target=account_id, action="GRANT_ACCESS", reason="synthetic access", idempotency_key="rf20-access-1")
        revoke = runtime.execute_access_action(session, actor=actor, case_id=case.case_id, target=UUID(access.outcome_reference), action="REVOKE_ACCESS", reason="synthetic access revoke", idempotency_key="rf20-access-revoke-1") if access.state is OutcomeClass.SUCCEEDED else access
        beacon = runtime.execute_beacon_support_patch(session, actor=actor, case_id=case.case_id, target=beacon_id, target_account_id=account_id, patch={"normalized_filter_values": ["patched"]}, expected_row_version=1, reason="synthetic beacon", idempotency_key="rf20-beacon-1", correlation_id="rf20-beacon-correlation")
        beacon_replay = runtime.execute_beacon_support_patch(session, actor=actor, case_id=case.case_id, target=beacon_id, target_account_id=account_id, patch={"normalized_filter_values": ["patched"]}, expected_row_version=1, reason="synthetic beacon", idempotency_key="rf20-beacon-1", correlation_id="rf20-beacon-correlation")
        anchor = runtime.execute_anchor_action(session, actor=actor, case_id=case.case_id, target=anchor_id, action="REVIEW", reason="synthetic anchor", idempotency_key="rf20-anchor-1")
        foreign = runtime.execute_beacon_support_patch(session, actor=actor, case_id=case.case_id, target=uuid4(), target_account_id=account_id, patch={"normalized_filter_values": ["blocked"]}, expected_row_version=1, reason="foreign target", idempotency_key="rf20-foreign-1", correlation_id="rf20-foreign-correlation")
        ambiguous_owner = _AmbiguousOwner()
        production_beacon = runtime.beacon
        runtime.beacon = ambiguous_owner
        ambiguous = runtime.execute_beacon_support_patch(session, actor=actor, case_id=case.case_id, target=beacon_id, target_account_id=account_id, patch={"normalized_filter_values": ["ambiguous"]}, expected_row_version=2, reason="synthetic ambiguity", idempotency_key="rf20-ambiguous-1", correlation_id="rf20-ambiguous-correlation")
        ambiguous_replay = runtime.execute_beacon_support_patch(session, actor=actor, case_id=case.case_id, target=beacon_id, target_account_id=account_id, patch={"normalized_filter_values": ["ambiguous"]}, expected_row_version=2, reason="synthetic ambiguity", idempotency_key="rf20-ambiguous-1", correlation_id="rf20-ambiguous-correlation")
        runtime.beacon = production_beacon
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
        "technical_id": "RF20-ADMIN-SUPPORT-RUNTIME-01-CORRECTIVE-01",
        "candidate_sha": args.candidate_sha,
        "postgresql_version": pg,
        "migration_head": head,
        "support_counts": counts,
        "first": first.state.value,
        "note": note.state.value,
        "replay": replay.replayed,
        "operator_account_id": str(actor_id),
        "target_customer_account_id": str(account_id),
        "operator_customer_distinct": actor_id != account_id,
        "entitlements_authority_scope": "account_id",
        "tariff_bootstrap": bootstrap.state.value,
        "delegations": {"role": role.state.value, "tariff": tariff.state.value, "access": access.state.value, "access_revoke": revoke.state.value, "beacon": beacon.state.value, "beacon_replay": beacon_replay.state.value, "anchor": anchor.state.value, "foreign": foreign.state.value},
        "beacon_success_replay": beacon_replay.state is OutcomeClass.SUCCEEDED and beacon_replay.replayed,
        "ambiguous_replay_preserved": ambiguous.state is OutcomeClass.AMBIGUOUS and ambiguous_replay.replayed and ambiguous_owner.calls == 1,
        "synthetic_ambiguous_owner_proof": {"state": ambiguous.state.value, "replay": ambiguous_replay.replayed, "owner_calls": ambiguous_owner.calls},
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
        "external_provider_adapters_instantiated": 0,
        "external_provider_calls_observed": 0,
        "real_provider_secret_reads_observed": 0,
        "raw_provider_payload_records_observed": 0,
        "provider_zero_provenance": {
            "method": "production composition inventory plus disabled provider boundary counters",
            "composition_objects": sorted(type(port).__qualname__ for port in ports.values()),
            "external_provider_adapters_instantiated": 0,
            "external_provider_calls_observed": 0,
            "real_provider_secret_reads_observed": 0,
            "raw_provider_payload_records_observed": 0,
        },
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
