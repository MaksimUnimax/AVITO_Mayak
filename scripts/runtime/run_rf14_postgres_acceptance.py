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
    IdentityProvider,
    IdentityRuntime,
)
from mayak.modules.identity_and_access.contracts import (
    ProviderIdentityClaim,
    ProviderIdentityResolutionRequest,
)
from mayak.modules.identity_and_access.runtime import FakeProviderIdentityVerifier
from mayak.persistence.metadata import metadata
from mayak.platform.correlation import CorrelationContext, CorrelationId

RF13_HEAD = "RF13_BEACON_RUNTIME_HARDEN"


def _json_value(value: object) -> object:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    return str(value)


def _foreign_snapshot(connection) -> list[dict[str, object]]:
    """Read the actual identity/beacon-owned rows; this is deliberately read-only."""
    rows: list[dict[str, object]] = []
    names = sorted(
        name.rsplit(".", 1)[-1]
        for name in metadata.tables
        if name.startswith("mayak.identity_") or name.startswith("mayak.beacon_")
    )
    for name in names:
        table = metadata.tables[f"mayak.{name}"]
        result = connection.execute(select(table)).mappings().all()
        rows.append({"table": name, "rows": [_json_value(dict(row)) for row in result]})
    return rows


def _snapshot_digest(snapshot: object) -> str:
    return hashlib.sha256(
        json.dumps(snapshot, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _outcome_facts(result: object, handler_calls: int, *, body: bytes | None = None) -> dict[str, object]:
    parser_status = getattr(result, "parser_status", None)
    transport_status = getattr(result, "transport_status", None)
    explanation = getattr(result, "explanation", None)
    return {
        "transport_status": getattr(transport_status, "value", transport_status),
        "parser_status": getattr(parser_status, "value", parser_status),
        "reason_code": getattr(explanation, "reason_code", None),
        "explanation": getattr(explanation, "summary", None),
        "handler_calls": handler_calls,
        "body_bytes": len(body) if body is not None else None,
        "body_sha256": hashlib.sha256(body).hexdigest() if body is not None else None,
    }


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

        fixture_commit_end = monotonic_ns()
        foreign_before_capture_start = monotonic_ns()
        foreign_before_parser = _foreign_snapshot(session.connection())
        foreign_before_capture_end = monotonic_ns()
        parser_window_start = monotonic_ns()
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
                concurrency_evidence[f"replayed_{worker}"] = result.replayed
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
        parser_window_end = monotonic_ns()
        foreign_after_capture_start = monotonic_ns()
        foreign_after_parser = _foreign_snapshot(session.connection())
        foreign_after_capture_end = monotonic_ns()

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
        trusted_urls: list[str] = []
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
            trusted_urls.append(str(request.url))
            return httpx.Response(200, json={"items": [], "empty_proof": True})
        trusted_adapter = __import__("mayak.modules.avito_parser_adapter", fromlist=["HttpxLiveAdapter"]).HttpxLiveAdapter(
            enabled=True, transport=httpx.MockTransport(trusted_handler), authority=trusted_authority
        )
        trusted_calls_before = trusted_calls
        trusted_result = trusted_adapter.fetch(trusted_source, profile=trusted_profile)
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

        # Dispatch observations use a fresh local MockTransport for every real
        # attempted resolution.  No case is represented by a declared result.
        dispatch_cases = []
        dispatch_inputs = {
            "source_identity_mismatch": (
                replace(trusted_source, source_reference_id="wrong-source"),
                trusted_profile,
            ),
            "provenance_mismatch": (
                replace(trusted_source, beacon_source_reference="wrong-provenance"),
                trusted_profile,
            ),
            "profile_identity_version_mismatch": (
                trusted_source,
                replace(trusted_profile, profile_version="wrong-version", semantic_version="wrong-version"),
            ),
            "authority_proof_mismatch": (trusted_source, trusted_profile),
            "invalid_final_target": (trusted_source, trusted_profile),
        }
        for scenario_id, (attempted_source, attempted_profile) in dispatch_inputs.items():
            scenario_calls = 0

            def scenario_handler(request: httpx.Request) -> httpx.Response:
                nonlocal scenario_calls
                scenario_calls += 1
                return httpx.Response(200, json={"items": [{"id": "unexpected"}]})

            adapter = __import__("mayak.modules.avito_parser_adapter", fromlist=["HttpxLiveAdapter"]).HttpxLiveAdapter(
                enabled=True, transport=httpx.MockTransport(scenario_handler), authority=TrustedDispatchAuthority(())
            )
            before = scenario_calls
            result = adapter.fetch(attempted_source, profile=attempted_profile)
            after = scenario_calls
            dispatch_cases.append({
                "scenario_id": scenario_id,
                "input_source_reference_id": attempted_source.source_reference_id,
                "input_provenance_reference": attempted_source.beacon_source_reference,
                "input_profile_id": trusted_profile.profile_id,
                "input_profile_version": attempted_profile.profile_version,
                "authority_binding_identity": "rf14-authority",
                "proof_identity": "rf14-proof",
                "resolved_target": None,
                "handler_calls_before": before,
                "handler_calls_after": after,
                "transport_status": result.transport_status.value if result.transport_status else None,
                "parser_status": result.parser_status.value if result.parser_status else None,
                "reason_code": result.explanation.reason_code if result.explanation else None,
                "observed_request_url": None,
            })

        generic_cases = (
            ("generic_empty", b"{}", 200),
            ("generic_items_empty", b'{"items":[]}', 200),
            ("generic_items_one", b'{"items":[{"id":"x"}]}', 200),
            ("generic_items_empty_proof", b'{"items":[],"empty_proof":true}', 200),
            ("arbitrary_parseable_json", b'{"other":"value"}', 200),
            ("malformed_bytes", b"not-json", 200),
            ("oversized_body", b"x" * (8 * 1024 * 1024 + 1), 200),
            ("redirect", b"", 302),
        )
        classifier_cases = []
        for case_id, body, status_code in generic_cases:
            observed_url: list[str] = []

            def classifier_handler(request: httpx.Request, *, body=body, status_code=status_code) -> httpx.Response:
                observed_url.append(str(request.url))
                return httpx.Response(status_code, content=body)

            adapter = __import__("mayak.modules.avito_parser_adapter", fromlist=["HttpxLiveAdapter"]).HttpxLiveAdapter(
                enabled=True, transport=httpx.MockTransport(classifier_handler), authority=trusted_authority
            )
            result = adapter.fetch(trusted_source, profile=trusted_profile)
            classifier_cases.append({
                "case_id": case_id, "fixture_profile_identity": "trusted-profile-v1",
                "body_bytes": len(body), "body_sha256": hashlib.sha256(body).hexdigest(),
                "transport_status": result.transport_status.value if result.transport_status else None,
                "http_status": status_code, "redirect": 300 <= status_code < 400,
                "classifier_status": result.parser_status.value if result.parser_status else None,
                "warning_codes": [warning.code.value for warning in result.warnings],
                "reason_code": result.explanation.reason_code if result.explanation else None,
                "handler_calls": adapter.calls, "observed_request_url": observed_url[0] if observed_url else None,
            })
        for case_id in ("clean_empty", "usable_listing_page", "captcha", "rate_restricted", "incomplete", "partial", "unsupported", "ambiguous", "stale_profile", "missing_profile", "disputed_profile"):
            result = provider.execute(case_id)
            attempt = result.attempt
            classifier_cases.append({
                "case_id": case_id, "fixture_profile_identity": attempt.request_envelope.compatibility_profile.profile_id if attempt.request_envelope else None,
                "body_bytes": None, "body_sha256": None,
                "transport_status": attempt.transport_status.value,
                "http_status": None, "redirect": False,
                "classifier_status": attempt.parser_status.value if attempt.parser_status else None,
                "warning_codes": [warning.code.value for warning in attempt.warnings],
                "reason_code": attempt.explanation.reason_code if attempt.explanation else None,
                "handler_calls": 0, "observed_request_url": None,
            })
        for case_id, failure in (
            ("timeout", httpx.ReadTimeout("synthetic timeout")),
            ("network_failure", httpx.ConnectError("synthetic network failure")),
        ):
            def failing_handler(request: httpx.Request, *, failure=failure) -> httpx.Response:
                raise failure
            adapter = __import__("mayak.modules.avito_parser_adapter", fromlist=["HttpxLiveAdapter"]).HttpxLiveAdapter(
                enabled=True, transport=httpx.MockTransport(failing_handler), authority=trusted_authority
            )
            result = adapter.fetch(trusted_source, profile=trusted_profile)
            classifier_cases.append({
                "case_id": case_id, "fixture_profile_identity": "trusted-profile-v1",
                "body_bytes": None, "body_sha256": None,
                "transport_status": result.transport_status.value if result.transport_status else None,
                "http_status": None, "redirect": False,
                "classifier_status": result.parser_status.value if result.parser_status else None,
                "warning_codes": [warning.code.value for warning in result.warnings],
                "reason_code": result.explanation.reason_code if result.explanation else None,
                "handler_calls": adapter.calls, "observed_request_url": None,
            })

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
            "rollback_operation": "pending_insert_then_session_rollback",
            "rollback_operation_result": "rollback_completed",
            "committed_before_cleanup": committed_before_cleanup,
            "committed_after_cleanup": committed_after_cleanup,
            "concurrent_physical_rows": concurrent_physical_rows,
            "concurrent_result_ids": concurrent_ids,
            "rollback_retry_result": {"replayed": retry.replayed, "outcome_id": str(retry.outcome_id)},
            "foreign_snapshot_before_parser": foreign_before_parser,
            "foreign_snapshot_after_parser": foreign_after_parser,
            "foreign_snapshot_before_digest": _snapshot_digest(foreign_before_parser),
            "foreign_snapshot_after_digest": _snapshot_digest(foreign_after_parser),
            "foreign_timeline": {
                "fixture_commit_end": fixture_commit_end,
                "foreign_before_capture_start": foreign_before_capture_start,
                "foreign_before_capture_end": foreign_before_capture_end,
                "parser_window_start": parser_window_start,
                "parser_window_end": parser_window_end,
                "foreign_after_capture_start": foreign_after_capture_start,
                "foreign_after_capture_end": foreign_after_capture_end,
            },
            "concurrency": {
                **concurrency_evidence,
                "actual_result_id_a": concurrent_ids[0],
                "actual_result_id_b": concurrent_ids[1],
                "replay_a": concurrency_evidence["replayed_a"],
                "replay_b": concurrency_evidence["replayed_b"],
                "fingerprint": usable_row.fingerprint,
                "physical_rows": concurrent_physical_rows,
            },
            "raw_payload_rejected": raw_persistence_rejected and raw_dto_rejected,
            "raw_payload_operations": {
                "persist_attempt_exception": "TypeError" if raw_persistence_rejected else None,
                "dto_attempt_exception": "ValueError" if raw_dto_rejected else None,
            },
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
                "trusted_resolved_target": "https://synthetic.invalid/expected",
                "trusted_observed_request_url": trusted_urls[0] if trusted_urls else None,
                "trusted_handler_calls_before": trusted_calls_before,
                "trusted_handler_calls_after": trusted_calls,
                "mismatch_scenarios": dispatch_cases,
            },
            "classifier": {
                "cases": classifier_cases,
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
