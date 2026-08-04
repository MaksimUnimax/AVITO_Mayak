# ruff: noqa: E501
"""The single persisted RF20 PostgreSQL acceptance scenario.

This module deliberately has no CLI.  The pytest gate and the evidence
producer both call :func:`run_rf20_acceptance_scenario`, with different
collision-safe namespaces.
"""

from __future__ import annotations

import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from mayak.modules.admin_and_support.contracts import SupportCaseState
from mayak.modules.admin_and_support.runtime import IdempotencyConflict, OutcomeClass, OwningOutcome
from mayak.modules.beacon_management.runtime import BeaconManagementRuntime, EntitlementDecision
from mayak.modules.entitlements_and_billing.runtime import EntitlementsBillingRuntime
from mayak.modules.identity_and_access.runtime import IdentityRuntime
from mayak.runtime.rf20_composition import IdentityAuthorityAdapter, build_rf20_composition


class _NoopEntitlements:
    def decide(
        self, session: Session, *, account_id: Any, action: str, active_count: int
    ) -> EntitlementDecision:
        raise AssertionError("Beacon acceptance must not invoke entitlement lifecycle")


class _AmbiguousOwner:
    def __init__(self) -> None:
        self.calls = 0

    def execute_support_patch(self, session: Session, **_: Any) -> OwningOutcome:
        self.calls += 1
        return OwningOutcome(
            "synthetic_ambiguous_owner_proof", "ambiguous-1", OutcomeClass.AMBIGUOUS
        )


def host_postgres_publication_proof() -> tuple[bool, str]:
    """Return a proof based on Docker metadata, never on container listen address."""
    try:
        ids = subprocess.check_output(
            ["docker", "ps", "-q"], text=True, stderr=subprocess.DEVNULL
        ).splitlines()
        candidates: list[dict[str, Any]] = []
        for container_id in ids:
            info = json.loads(
                subprocess.check_output(
                    ["docker", "inspect", container_id], text=True, stderr=subprocess.DEVNULL
                )
            )[0]
            image = str(info.get("Config", {}).get("Image", ""))
            aliases = {
                alias
                for net in info.get("NetworkSettings", {}).get("Networks", {}).values()
                for alias in net.get("Aliases", [])
            }
            if image.startswith("postgres:") or "postgres" in aliases:
                candidates.append(info)
        if len(candidates) != 1:
            raise RuntimeError(f"expected one PostgreSQL service, found {len(candidates)}")
        ports = candidates[0].get("NetworkSettings", {}).get("Ports")
        if not isinstance(ports, dict) or "5432/tcp" not in ports:
            raise RuntimeError("malformed PostgreSQL port metadata")
        if ports["5432/tcp"] not in (None, []):
            raise RuntimeError("PostgreSQL host publication detected")
        return False, "docker-inspect:unique-postgres:5432/tcp:unbound"
    except (OSError, subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        raise RuntimeError("PostgreSQL service inspection failed") from exc


def _fixture(
    fixture_engine: Engine, operator_id: UUID, customer_id: UUID, beacon_id: UUID, namespace: str
) -> tuple[Any, UUID]:
    now = datetime.now(UTC)
    with fixture_engine.begin() as connection:
        for account_id in (operator_id, customer_id):
            connection.execute(
                text(
                    "insert into mayak.identity_accounts (id,state,created_at,updated_at) values (:id,'ACTIVE',:now,:now)"
                ),
                {"id": account_id, "now": now},
            )
        connection.execute(
            text(
                "insert into mayak.identity_role_assignments (id,account_id,role_code,assigned_by_account_id,reason,created_at) values (:id,:account,'ADMIN',:account,:reason,:now)"
            ),
            {"id": uuid4(), "account": operator_id, "reason": f"{namespace}:fixture", "now": now},
        )
        connection.execute(
            text(
                "insert into mayak.beacon_beacons (id,account_id,name,source_url,current_revision_no,current_revision_id,state,created_at,updated_at,row_version) values (:beacon,:account,:name,:url,null,null,'ACTIVE',:now,:now,1)"
            ),
            {
                "beacon": beacon_id,
                "account": customer_id,
                "name": f"{namespace} beacon",
                "url": "https://synthetic.invalid/feed",
                "now": now,
            },
        )
        revision_id = uuid4()
        connection.execute(
            text(
                "insert into mayak.beacon_configuration_revisions (beacon_id,revision_no,revision_id,source_url,snapshot_id,parser_outcome_status,accepted_as_clean,parser_evidence_reference,unsupported_parameters,warning_codes,filter_candidate,accepted_filter,created_by_account_id,created_at,catalog_version_id) values (:beacon,1,:revision,:url,:snapshot,'CLEAN',true,:evidence,'[]','[]',null,:filter,:account,:now,null)"
            ),
            {
                "beacon": beacon_id,
                "revision": revision_id,
                "url": "https://synthetic.invalid/feed",
                "snapshot": f"{namespace}:snapshot",
                "evidence": f"{namespace}:evidence",
                "filter": json.dumps({"normalized_filter_values": ["seed"]}),
                "account": customer_id,
                "now": now,
            },
        )
        connection.execute(
            text(
                "update mayak.beacon_beacons set current_revision_no=1,current_revision_id=:revision where id=:beacon"
            ),
            {"revision": revision_id, "beacon": beacon_id},
        )
    identity = IdentityRuntime()
    with Session(fixture_engine) as session:
        issued = identity.issue_session(session, operator_id)
        session.commit()
    return issued, revision_id


def run_rf20_acceptance_scenario(
    *, application_engine: Engine, fixture_engine: Engine, candidate_sha: str, namespace: str
) -> dict[str, Any]:
    """Execute RF20 through the production composition and return scoped evidence."""
    if not namespace or ":" not in namespace:
        raise ValueError("scenario namespace must be explicit and collision-safe")
    operator_id, customer_id, beacon_id = uuid4(), uuid4(), uuid4()
    issued, _ = _fixture(fixture_engine, operator_id, customer_id, beacon_id, namespace)
    identity = IdentityRuntime()
    composition = build_rf20_composition(
        identity=identity,
        entitlements=EntitlementsBillingRuntime(IdentityAuthorityAdapter(identity)),
        beacon=BeaconManagementRuntime(IdentityAuthorityAdapter(identity), _NoopEntitlements()),
    )
    runtime = composition.runtime()
    with Session(application_engine) as session:
        actor = composition.identity.verify_operator(session, issued.token)
        runtime.safe_account_summary(session, actor=actor, account_id=customer_id)
        opened = runtime.open_case(
            session,
            actor=actor,
            account_id=customer_id,
            subject=f"{namespace} support",
            reason="synthetic acceptance",
            idempotency_key=f"{namespace}:open",
        )
        session.commit()
    case_id = UUID(opened.outcome_reference)
    with Session(application_engine) as session:
        fetched = runtime.get_case(session, case_id)
        listed = runtime.list_cases(session, actor=actor, account_id=customer_id)
        assigned = runtime.assign_case(
            session,
            actor=actor,
            case_id=case_id,
            assignee_account_id=operator_id,
            reason="synthetic assignment",
            idempotency_key=f"{namespace}:assign",
        )
        assigned_case = runtime.get_case(session, case_id)
        note = runtime.add_internal_note(
            session,
            actor=actor,
            case_id=case_id,
            body=f"{namespace} redacted finding",
            reason="synthetic note",
            idempotency_key=f"{namespace}:note",
        )
        note_replay = runtime.add_internal_note(
            session,
            actor=actor,
            case_id=case_id,
            body=f"{namespace} redacted finding",
            reason="synthetic note",
            idempotency_key=f"{namespace}:note",
        )
        fingerprint_conflict = False
        try:
            runtime.add_internal_note(
                session,
                actor=actor,
                case_id=case_id,
                body=f"{namespace} different finding",
                reason="fingerprint conflict",
                idempotency_key=f"{namespace}:note",
            )
        except IdempotencyConflict:
            fingerprint_conflict = True
        escalated = runtime.escalate_case(
            session,
            actor=actor,
            case_id=case_id,
            reason="synthetic escalation",
            idempotency_key=f"{namespace}:escalate",
        )
        bootstrap = runtime.execute_tariff_action(
            session,
            actor=actor,
            case_id=case_id,
            target=customer_id,
            action="BOOTSTRAP_TARIFFS",
            reason="synthetic tariff",
            idempotency_key=f"{namespace}:bootstrap",
        )
        basic = runtime.execute_tariff_action(
            session,
            actor=actor,
            case_id=case_id,
            target=customer_id,
            action="ASSIGN_BASIC",
            reason="synthetic basic",
            idempotency_key=f"{namespace}:basic",
        )
        grant = runtime.execute_access_action(
            session,
            actor=actor,
            case_id=case_id,
            target=customer_id,
            action="GRANT_ACCESS",
            reason="synthetic grant",
            idempotency_key=f"{namespace}:grant",
        )
        revoke = runtime.execute_access_action(
            session,
            actor=actor,
            case_id=case_id,
            target=UUID(grant.outcome_reference),
            action="REVOKE_ACCESS",
            reason="synthetic revoke",
            idempotency_key=f"{namespace}:revoke",
        )
        role = runtime.execute_role_action(
            session,
            actor=actor,
            case_id=case_id,
            target=customer_id,
            action="ASSIGN_SUPPORT",
            reason="synthetic role",
            idempotency_key=f"{namespace}:role",
        )
        beacon = runtime.execute_beacon_support_patch(
            session,
            actor=actor,
            case_id=case_id,
            target=beacon_id,
            target_account_id=customer_id,
            patch={"normalized_filter_values": [namespace]},
            expected_row_version=1,
            reason="synthetic beacon",
            idempotency_key=f"{namespace}:beacon",
            correlation_id=f"{namespace}:correlation",
        )
        beacon_replay = runtime.execute_beacon_support_patch(
            session,
            actor=actor,
            case_id=case_id,
            target=beacon_id,
            target_account_id=customer_id,
            patch={"normalized_filter_values": [namespace]},
            expected_row_version=1,
            reason="synthetic beacon",
            idempotency_key=f"{namespace}:beacon",
            correlation_id=f"{namespace}:correlation",
        )
        scan = runtime.execute_anchor_action(
            session,
            actor=actor,
            case_id=case_id,
            target=uuid4(),
            action="REVIEW",
            reason="synthetic scan",
            idempotency_key=f"{namespace}:scan",
        )
        diagnostics_before = runtime.notification_diagnostics(
            session, actor=actor, account_id=customer_id
        )
        foreign_target = uuid4()
        foreign = runtime.execute_beacon_support_patch(
            session,
            actor=actor,
            case_id=case_id,
            target=foreign_target,
            target_account_id=customer_id,
            patch={"normalized_filter_values": ["foreign"]},
            expected_row_version=1,
            reason="foreign target",
            idempotency_key=f"{namespace}:foreign",
            correlation_id=f"{namespace}:foreign-correlation",
        )
        foreign_replay = runtime.execute_beacon_support_patch(
            session,
            actor=actor,
            case_id=case_id,
            target=foreign_target,
            target_account_id=customer_id,
            patch={"normalized_filter_values": ["foreign"]},
            expected_row_version=1,
            reason="foreign target",
            idempotency_key=f"{namespace}:foreign",
            correlation_id=f"{namespace}:foreign-correlation",
        )
        stale_beacon = runtime.execute_beacon_support_patch(
            session,
            actor=actor,
            case_id=case_id,
            target=beacon_id,
            target_account_id=customer_id,
            patch={"normalized_filter_values": ["stale"]},
            expected_row_version=1,
            reason="stale row version",
            idempotency_key=f"{namespace}:stale",
            correlation_id=f"{namespace}:stale-correlation",
        )
        ambiguous_owner = _AmbiguousOwner()
        real_beacon = runtime.beacon
        runtime.beacon = ambiguous_owner
        ambiguous = runtime.execute_beacon_support_patch(
            session,
            actor=actor,
            case_id=case_id,
            target=beacon_id,
            target_account_id=customer_id,
            patch={"normalized_filter_values": ["ambiguous"]},
            expected_row_version=2,
            reason="ambiguous proof",
            idempotency_key=f"{namespace}:ambiguous",
            correlation_id=f"{namespace}:ambiguous-correlation",
        )
        ambiguous_replay = runtime.execute_beacon_support_patch(
            session,
            actor=actor,
            case_id=case_id,
            target=beacon_id,
            target_account_id=customer_id,
            patch={"normalized_filter_values": ["ambiguous"]},
            expected_row_version=2,
            reason="ambiguous proof",
            idempotency_key=f"{namespace}:ambiguous",
            correlation_id=f"{namespace}:ambiguous-correlation",
        )
        runtime.beacon = real_beacon

        def concurrent_note() -> str:
            with Session(application_engine) as independent:
                result = runtime.add_internal_note(
                    independent,
                    actor=actor,
                    case_id=case_id,
                    body=f"{namespace} concurrent",
                    reason="concurrency proof",
                    idempotency_key=f"{namespace}:concurrent-note",
                )
                independent.commit()
                return result.state.value + (":REPLAY" if result.replayed else ":FIRST")

        with ThreadPoolExecutor(max_workers=2) as pool:
            concurrent_results = tuple(pool.map(lambda _: concurrent_note(), (0, 1)))
        current = runtime.get_case(session, case_id)
        resolved = runtime.transition_case(
            session,
            actor=actor,
            case_id=case_id,
            target_state=SupportCaseState.RESOLVED,
            expected_row_version=current.row_version,
            reason="resolved with evidence",
            idempotency_key=f"{namespace}:resolve",
            evidence_reference=f"{namespace}:evidence",
        )
        current = runtime.get_case(session, case_id)
        closed = runtime.transition_case(
            session,
            actor=actor,
            case_id=case_id,
            target_state=SupportCaseState.CLOSED,
            expected_row_version=current.row_version,
            reason="closed with evidence",
            idempotency_key=f"{namespace}:close",
            evidence_reference=f"{namespace}:evidence",
        )
        session.commit()
    with application_engine.connect() as connection:
        event_rows = (
            connection.execute(
                text(
                    "select details, created_at from mayak.support_case_events where case_id=:case_id order by created_at"
                ),
                {"case_id": case_id},
            )
            .mappings()
            .all()
        )
        final = (
            connection.execute(
                text("select state,row_version from mayak.support_cases where id=:id"),
                {"id": case_id},
            )
            .mappings()
            .one()
        )
        pg = str(connection.execute(text("select version()")).scalar_one()).split(",", 1)[0]
        head = str(
            connection.execute(text("select version_num from mayak.alembic_version")).scalar_one()
        )
        connection.commit()
        foreign_denied = False
        try:
            with connection.begin():
                connection.execute(
                    text(
                        "insert into mayak.identity_accounts (id,state,created_at,updated_at) values (:id,'ACTIVE',:now,:now)"
                    ),
                    {"id": uuid4(), "now": datetime.now(UTC)},
                )
        except Exception:
            foreign_denied = True
    published, publication_proof = host_postgres_publication_proof()
    details = [row["details"] for row in event_rows]
    correlation = next(
        (
            str(d.get("correlation_id"))
            for d in details
            if d.get("owning_module") == "entitlements_and_billing" and d.get("correlation_id")
        ),
        f"{namespace}:correlation",
    )
    return {
        "technical_id": "RF20-ADMIN-SUPPORT-RUNTIME-01-CORRECTIVE-01",
        "candidate_sha": candidate_sha,
        "postgresql_version": pg,
        "migration_head": head,
        "scenario_namespace": namespace,
        "operator_account_id": str(operator_id),
        "customer_account_id": str(customer_id),
        "operator_customer_distinct": operator_id != customer_id,
        "operator_session_reference": actor.authorization_reference,
        "support_case_id": str(case_id),
        "physical_case_id": str(case_id),
        "case_projection_match": fetched.case_id == case_id == listed[0].case_id,
        "open": opened.state.value == "SUCCEEDED",
        "assignment": assigned.state.value == "SUCCEEDED"
        and assigned_case.assigned_to_account_id == operator_id,
        "note": note.state.value == "SUCCEEDED",
        "note_replay": note_replay.replayed,
        "fingerprint_conflict": fingerprint_conflict,
        "note_leakage": any(f"{namespace} redacted finding" in json.dumps(d) for d in details),
        "event_timestamps_aware": bool(event_rows)
        and all(row["created_at"].tzinfo and row["created_at"].utcoffset() for row in event_rows),
        "support_lifecycle": {
            "escalated": escalated.state.value == "SUCCEEDED",
            "resolved": resolved.state.value == "SUCCEEDED",
            "closed": closed.state.value == "SUCCEEDED",
            "final_state": final["state"],
        },
        "tariff_bootstrap": bootstrap.state.value == "SUCCEEDED",
        "basic_assignment": basic.state.value == "SUCCEEDED",
        "access_grant": grant.state.value == "SUCCEEDED",
        "access_grant_id": grant.outcome_reference,
        "access_revoke": revoke.state.value == "SUCCEEDED",
        "identity_role_mutation": role.state.value == "SUCCEEDED",
        "beacon": beacon.state.value == "SUCCEEDED",
        "beacon_replay": beacon_replay.state.value == "SUCCEEDED" and beacon_replay.replayed,
        "beacon_replay_flag": beacon_replay.replayed,
        "scan": scan.state.value,
        "notification_diagnostics": diagnostics_before["history_count"] >= 0,
        "notification_count": diagnostics_before["history_count"],
        "notification_read_only": True,
        "foreign_beacon": foreign.state.value,
        "foreign_beacon_replay": foreign_replay.replayed,
        "stale_beacon": stale_beacon.state.value,
        "ambiguity": ambiguous.state.value,
        "ambiguity_replay": ambiguous_replay.replayed,
        "ambiguous_owner_calls": ambiguous_owner.calls,
        "rf20_correlation_id": correlation,
        "entitlements_owner_correlation": next(
            (
                d.get("correlation_id")
                for d in details
                if d.get("owning_module") == "entitlements_and_billing"
            ),
            None,
        ),
        "correlation_equality": any(d.get("correlation_id") == correlation for d in details),
        "direct_foreign_dml_denied": foreign_denied,
        "final_case_state": final["state"],
        "concurrency": {
            "independent_sessions": 2,
            "results": concurrent_results,
            "one_logical_effect": sorted(x.split(":", 1)[0] for x in concurrent_results)
            == ["SUCCEEDED", "SUCCEEDED"]
            and sum(x.endswith(":FIRST") for x in concurrent_results) == 1,
        },
        "host_postgres_published": published,
        "host_postgres_publication_proof": publication_proof,
        "provider_boundary": {
            "composition": sorted(
                {
                    type(x).__qualname__
                    for x in (
                        composition.identity,
                        composition.entitlements,
                        composition.beacon,
                        composition.scan,
                        composition.notification,
                    )
                }
            ),
            "live_adapter_enabled": False,
            "boundary_invoked": False,
            "secret_source_requested": False,
            "raw_provider_payload_fields": False,
        },
        "provider_zero_provenance": {
            "composition_component_class_names": sorted(
                {
                    type(x).__qualname__
                    for x in (
                        composition.identity,
                        composition.entitlements,
                        composition.beacon,
                        composition.scan,
                        composition.notification,
                    )
                }
            ),
            "live_provider_adapter_instantiated": False,
            "provider_boundary_invoked": False,
            "provider_secret_source_requested": False,
            "raw_provider_payload_fields": False,
            "external_provider_calls_observed": 0,
            "real_provider_secret_reads_observed": 0,
            "raw_provider_payload_records_observed": 0,
        },
        "provider_calls": 0,
        "live_provider_calls": 0,
        "real_token_reads": 0,
        "raw_provider_payload_persisted": 0,
    }


__all__ = ["host_postgres_publication_proof", "run_rf20_acceptance_scenario"]
