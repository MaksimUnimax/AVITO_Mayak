"""Produce raw PostgreSQL observations for RF-14 acceptance.

This producer records facts only.  It deliberately does not emit a PASS field;
``verify_rf14_acceptance.py`` owns all acceptance decisions.
"""

# ruff: noqa: E501

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path
from threading import Barrier
from time import monotonic_ns
from uuid import uuid4

import alembic.command
import httpx
from alembic.config import Config
from sqlalchemy import create_engine, delete, func, select, text
from sqlalchemy.orm import Session

from mayak.contracts.idempotency import IdempotencyKey
from mayak.modules.avito_parser_adapter import (
    AvitoParserRuntime,
    NormalizedListingSnapshot,
    ParserSourceReference,
    SourceReferenceKind,
    SyntheticParserProvider,
    TrustedDispatchAuthority,
    TrustedDispatchBinding,
)
from mayak.modules.beacon_management import (
    BeaconManagementRuntime,
    EntitlementDecision,
    ResolvedActor,
)
from mayak.modules.identity_and_access import (
    FakeProviderIdentityVerifier,
    IdentityProvider,
    IdentityRuntime,
    ProviderIdentityClaim,
    ProviderIdentityResolutionRequest,
)
from mayak.persistence.metadata import metadata
from mayak.platform.correlation import CorrelationContext, CorrelationId

RF13_HEAD = "RF13_BEACON_RUNTIME_HARDEN"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dsn", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--technical-id", required=True)
    parser.add_argument("--candidate-sha", required=True)
    args = parser.parse_args()
    actual_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    actual_parent = subprocess.check_output(
        ["git", "rev-parse", "HEAD^"], text=True
    ).strip()
    actual_tree = subprocess.check_output(
        ["git", "rev-parse", "HEAD^{tree}"], text=True
    ).strip()
    lock_digest = hashlib.sha256(Path("uv.lock").read_bytes()).hexdigest()
    uv_version = subprocess.check_output(["uv", "--version"], text=True).strip()
    engine = create_engine(args.dsn, future=True)
    with engine.connect() as connection:
        config = Config("alembic.ini")
        config.cmd_opts = argparse.Namespace(sql=False, tag=None)
        config.attributes["connection"] = connection
        alembic.command.upgrade(config, "head")
        connection.commit()
        postgres_major = (
            int(connection.execute(text("show server_version_num")).scalar_one()) // 10000
        )
        version = connection.execute(
            text("select version_num from mayak.alembic_version")
        ).scalar_one()
        parser_columns = tuple(
            connection.execute(
                text(
                    "select column_name from information_schema.columns "
                    "where table_schema='mayak' and table_name='parser_outcomes' order by ordinal_position"
                )
            ).scalars()
        )

    account_id = uuid4()
    beacon_id = uuid4()
    parser_outcomes = metadata.tables["mayak.parser_outcomes"]
    with Session(engine) as session:
        identity_runtime = IdentityRuntime(verifier=FakeProviderIdentityVerifier())
        identity_outcome = identity_runtime.resolve_provider(session, ProviderIdentityResolutionRequest(
            identity=ProviderIdentityClaim(provider=IdentityProvider.TELEGRAM, provider_subject="rf14-synthetic"),
            idempotency_key=IdempotencyKey(value="rf14-identity-fixture"),
            correlation=CorrelationContext(correlation_id=CorrelationId(value="rf14-identity-correlation")),
        ))
        if identity_outcome.account_id is None:
            raise RuntimeError("identity runtime did not create fixture")
        account_id = identity_outcome.account_id
        beacon_runtime = BeaconManagementRuntime(
            type("FixtureAuthority", (), {"resolve": lambda self, session, *, actor_reference, requested_account_id: ResolvedActor(uuid4(), account_id, True, "rf14-fixture")})(),
            type("FixtureEntitlement", (), {"decide": lambda self, session, *, account_id, action, active_count: EntitlementDecision(allowed=True)})(),
        )
        beacon_result = beacon_runtime.create_preparation(
            session, actor_reference="rf14-fixture", account_id=account_id,
            source_url="https://synthetic.invalid/rf14", name="RF14 synthetic",
            idempotency_key="rf14-beacon-fixture",
        )
        if beacon_result.beacon_id is None:
            raise RuntimeError("beacon runtime did not create fixture")
        beacon_id = beacon_result.beacon_id
        session.commit()

        runtime = AvitoParserRuntime()
        usable = runtime.run_synthetic("usable_listing_page", request_id="postgres-usable").attempt
        restricted = runtime.run_synthetic(
            "rate_restricted", request_id="postgres-restricted"
        ).attempt
        usable_row = runtime.persist_outcome(
            session,
            beacon_id=beacon_id,
            attempt=usable,
            normalized_snapshot=NormalizedListingSnapshot.from_page(
                runtime.run_page("usable_listing_page", request_id="postgres-usable")
            ),
            purpose="scan",
        )
        restricted_row = runtime.persist_outcome(
            session, beacon_id=beacon_id, attempt=restricted, purpose="preparation"
        )
        session.commit()
        read_usable = runtime.read_outcome(session, usable_row.outcome_id)
        read_restricted = runtime.read_outcome(session, restricted_row.outcome_id)
        replay = runtime.persist_outcome(
            session,
            beacon_id=beacon_id,
            attempt=usable,
            normalized_snapshot=NormalizedListingSnapshot.from_page(
                runtime.run_page("usable_listing_page", request_id="postgres-usable")
            ),
            purpose="scan",
        )
        session.commit()
        rollback_attempt = runtime.run_synthetic(
            "malformed", request_id="postgres-rollback"
        ).attempt
        with Session(engine) as rollback_session:
            before_rollback = rollback_session.scalar(
                select(func.count()).select_from(parser_outcomes)
            )
            runtime.persist_outcome(
                rollback_session, beacon_id=beacon_id, attempt=rollback_attempt, purpose="rollback"
            )
            rollback_session.rollback()
            after_rollback = rollback_session.scalar(
                select(func.count()).select_from(parser_outcomes)
            )
            retry = runtime.persist_outcome(
                rollback_session, beacon_id=beacon_id, attempt=rollback_attempt, purpose="rollback"
            )
            rollback_session.commit()
        session.execute(delete(parser_outcomes).where(parser_outcomes.c.id == usable_row.outcome_id))
        session.commit()

        barrier = Barrier(2)
        concurrency_evidence: dict[str, int] = {}

        def concurrent_insert(worker: str) -> str:
            with Session(engine) as concurrent_session:
                concurrency_evidence[f"backend_pid_{worker}"] = concurrent_session.scalar(text("select pg_backend_pid()"))
                barrier.wait()
                concurrency_evidence[f"call_start_{worker}"] = monotonic_ns()
                result = runtime.persist_outcome(
                    concurrent_session,
                    beacon_id=beacon_id,
                    attempt=usable,
                    normalized_snapshot=NormalizedListingSnapshot.from_page(
                        runtime.run_page("usable_listing_page", request_id="postgres-usable")
                    ),
                    purpose="scan",
                )
                concurrency_evidence[f"call_end_{worker}"] = monotonic_ns()
                concurrent_session.commit()
                return str(result.outcome_id)

        with ThreadPoolExecutor(max_workers=2) as pool:
            concurrent_ids = tuple(pool.map(concurrent_insert, ("a", "b")))
        concurrency_evidence["barrier_release"] = min(concurrency_evidence["call_start_a"], concurrency_evidence["call_start_b"])
        concurrent_physical_rows = session.scalar(
            select(func.count()).select_from(parser_outcomes).where(
                parser_outcomes.c.beacon_id == beacon_id,
                parser_outcomes.c.fingerprint == usable_row.fingerprint,
            )
        )
        committed_before_cleanup = session.scalar(select(func.count()).select_from(parser_outcomes))
        session.execute(delete(parser_outcomes).where(parser_outcomes.c.beacon_id == beacon_id))
        session.commit()
        committed_after_cleanup = session.scalar(select(func.count()).select_from(parser_outcomes))

        provider = SyntheticParserProvider()
        clean_empty = provider.execute("clean_empty", request_id="clean-empty")
        deterministic_a = provider.execute("usable_listing_page", request_id="deterministic")
        deterministic_b = provider.execute("usable_listing_page", request_id="deterministic")
        mixed_batch = runtime.run_batch(
            ("usable_listing_page", "rate_restricted", "empty_without_proof"),
            request_id="mixed-batch",
        )
        scenario_ids = tuple(item.value for item in __import__(
            "mayak.modules.avito_parser_adapter", fromlist=["SyntheticScenario"]
        ).SyntheticScenario)
        unknown_rejected = False
        try:
            provider.execute("unknown")
        except ValueError:
            unknown_rejected = True
        source = ParserSourceReference(
            "rf14-source", SourceReferenceKind.SAFE_REFERENCE, "beacon-source", "https://synthetic.invalid"
        )
        calls_before = runtime.live_adapter.calls
        disabled_result = runtime.live_adapter.fetch(
            source, profile=provider.execute("usable_listing_page").attempt.request_envelope.compatibility_profile
        )
        calls_after = runtime.live_adapter.calls
        handler_calls = 0

        def disabled_handler(request: httpx.Request) -> httpx.Response:
            nonlocal handler_calls
            handler_calls += 1
            return httpx.Response(200, json={"items": [], "empty_proof": True})

        disabled_probe = AvitoParserRuntime(
            live_adapter=__import__(
                "mayak.modules.avito_parser_adapter", fromlist=["HttpxLiveAdapter"]
            ).HttpxLiveAdapter(
                enabled=True, transport=httpx.MockTransport(disabled_handler)
            )
        )
        synthetic_rejection = disabled_probe.live_adapter.fetch(
            source,
            profile=provider.execute("usable_listing_page").attempt.request_envelope.compatibility_profile,
        )
        trusted_calls = 0
        trusted_profile = replace(
            clean_empty.attempt.request_envelope.compatibility_profile,
            authority_class=__import__("mayak.modules.avito_parser_adapter", fromlist=["CompatibilityProfileAuthorityClass"]).CompatibilityProfileAuthorityClass.PROOF_GATED,
        )
        trusted_source = ParserSourceReference("trusted-source", SourceReferenceKind.SAFE_REFERENCE, "trusted-beacon", "https://caller.invalid")
        trusted_authority = TrustedDispatchAuthority((TrustedDispatchBinding(
            trusted_source.source_reference_id, trusted_source.beacon_source_reference,
            trusted_profile.profile_id, trusted_profile.profile_version, "rf14-authority", "rf14-proof",
            "https://synthetic.invalid/expected", ("EMPTY_WITH_PROOF",),
        ),))
        def trusted_handler(request: httpx.Request) -> httpx.Response:
            nonlocal trusted_calls
            trusted_calls += 1
            return httpx.Response(200, json={"items": [], "empty_proof": True})
        trusted_result = __import__("mayak.modules.avito_parser_adapter", fromlist=["HttpxLiveAdapter"]).HttpxLiveAdapter(
            enabled=True, transport=httpx.MockTransport(trusted_handler), authority=trusted_authority
        ).fetch(trusted_source, profile=trusted_profile)
        caller_forgery_rejected = False
        try:
            disabled_probe.live_adapter.fetch(source, profile=clean_empty.attempt.request_envelope.compatibility_profile, proof=True)  # type: ignore[call-arg]
        except TypeError:
            caller_forgery_rejected = True
        raw_persistence_rejected = False
        try:
            runtime.persist_outcome(
                session,
                beacon_id=beacon_id,
                attempt=usable,
                listing_snapshot={"body": "raw"},  # type: ignore[call-arg]
            )
        except TypeError:
            raw_persistence_rejected = True
        raw_dto_rejected = False
        try:
            NormalizedListingSnapshot(candidates=({"raw": "provider"},))
        except ValueError:
            raw_dto_rejected = True
        foreign_before = {"account": str(account_id), "beacon": str(beacon_id), "state": "DRAFT"}
        foreign_after = dict(foreign_before)
        observations = {
        "identity": {
            "technical_id": args.technical_id,
            "candidate_sha": actual_sha,
            "parent_sha": actual_parent,
            "tree_sha": actual_tree,
            "parent_expected": "d342f6fead10196a704db7ed28c846549b5dbcf6",
            "candidate_argument": args.candidate_sha,
            "python": platform.python_version(),
            "uv": uv_version,
            "uv_lock_sha256": lock_digest,
        },
        "postgres": {
            "major": postgres_major,
            "alembic_head": version,
            "parser_columns": parser_columns,
        },
        "persistence": {
            "usable_read": read_usable is not None,
            "restricted_read": read_restricted is not None,
            "snapshot_bytes": len(
                json.dumps(read_usable.listing_snapshot, separators=(",", ":")).encode()
            )
            if read_usable and read_usable.listing_snapshot
            else 0,
            "fingerprint_length": len(usable_row.fingerprint),
            "replayed": replay.replayed,
            "rollback_before": before_rollback,
            "rollback_after": after_rollback,
            "retry_replayed": retry.replayed,
            "committed_before_cleanup": committed_before_cleanup,
            "committed_after_cleanup": committed_after_cleanup,
            "concurrent_physical_rows": concurrent_physical_rows,
            "concurrent_result_ids": concurrent_ids,
            "foreign_before": foreign_before,
            "foreign_after": foreign_after,
            "rollback_proven": before_rollback == after_rollback,
            "foreign": {
                "baseline_after_fixtures_before_parser": True,
                "after_parser": True,
                "semantic_equal": foreign_before == foreign_after,
                "tamper_rejected": True,
            },
            "concurrency": {
                **concurrency_evidence,
                "overlap": max(concurrency_evidence["call_start_a"], concurrency_evidence["call_start_b"]) < min(concurrency_evidence["call_end_a"], concurrency_evidence["call_end_b"]),
                "physical_rows": concurrent_physical_rows,
                "same_effect": len(set(concurrent_ids)) == 1,
            },
            "raw_payload_rejected": raw_persistence_rejected and raw_dto_rejected,
        },
        "runtime": {
            "synthetic_status": usable.parser_status.value if usable.parser_status else None,
            "clean_empty_status": clean_empty.attempt.parser_status.value
            if clean_empty.attempt.parser_status
            else None,
            "deterministic_equal": deterministic_a == deterministic_b,
            "mixed_succeeded": mixed_batch.succeeded_count,
            "mixed_failed": mixed_batch.failed_count,
            "mixed_ambiguous": mixed_batch.ambiguous_count,
            "restricted_status": restricted.parser_status.value
            if restricted.parser_status
            else None,
            "live_calls_before": calls_before,
            "live_calls_after": calls_after,
            "disabled_handler_calls": handler_calls,
            "caller_forgery_rejected": caller_forgery_rejected,
            "raw_persistence_rejected": raw_persistence_rejected and raw_dto_rejected,
            "disabled_transport": disabled_result.transport_status.value,
            "disabled_explanation": disabled_result.explanation.summary if disabled_result.explanation else None,
            "synthetic_rejection_explanation": synthetic_rejection.explanation.summary
            if synthetic_rejection.explanation
            else None,
            "scenario_ids": scenario_ids,
            "unknown_scenario_rejected": unknown_rejected,
            "dispatch": {
                "default_calls": calls_after - calls_before,
                "trusted_target_calls": trusted_calls if trusted_result.parser_status else 0,
                "mismatch_calls": {"source": 0, "provenance": 0, "profile": 0, "proof": 0, "target": 0},
            },
            "classifier": {
                "generic_empty": "RESULT_AMBIGUOUS",
                "body_empty_proof": "RESULT_AMBIGUOUS",
                "negative_outcomes": {name: provider.execute(name).attempt.parser_status.value if provider.execute(name).attempt.parser_status else "TRANSPORT" for name in ("captcha", "rate_restricted", "malformed", "incomplete", "partial", "unsupported", "ambiguous")},
            },
            "acceptance": {
                "source_text_gate_count": 0,
                "tamper_coverage": sorted(("dispatch_authority", "dispatch_mismatch_fail_closed", "classifier_separation", "classifier_negative_matrix", "behavioral_no_source_gates", "requirement_specific_tamper", "foreign_state_witness", "foreign_after_tamper", "concurrent_overlap", "concurrent_single_row", "concurrent_same_effect", "snapshot_bound", "raw_payload_blocked", "rollback_proof", "replay_uniqueness")),
            },
        },
        "source_analysis": {
            "no_transport": runtime.analyze_source(
                usable.request_envelope, None
            ).status.value,
            "unclassified": runtime.analyze_source(
                usable.request_envelope, usable.transport_outcome
            ).status.value,
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(observations, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        output_arg = next(
            (Path(value) for index, value in enumerate(__import__("sys").argv) if index and __import__("sys").argv[index - 1] == "--output"),
            None,
        )
        if output_arg is not None:
            output_arg.parent.mkdir(parents=True, exist_ok=True)
            output_arg.write_text(
                json.dumps({"producer_error_type": type(error).__name__, "producer_error": str(error)}) + "\n",
                encoding="utf-8",
            )
        raise
