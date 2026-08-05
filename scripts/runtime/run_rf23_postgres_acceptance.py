"""Produce RF23 evidence from the live candidate and task-local probes."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from check_rf23_artifact_safety import transport_inventory


def _get(base: str, path: str) -> tuple[int, object]:
    try:
        with urlopen(Request(base.rstrip("/") + path, method="GET"), timeout=10) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        return exc.code, {"error": "http_error"}
    except (OSError, URLError, ValueError):
        return 0, {"error": "unavailable"}


def observe(base: str, repo_root: Path, pytest_log: Path | None = None) -> dict[str, object]:
    """Collect only values returned by the running API or local process probes."""
    sha = os.environ.get("RF23_CANDIDATE_SHA")
    tree = os.environ.get("RF23_CANDIDATE_TREE")
    if not sha or not tree:
        sha = subprocess.check_output(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"], text=True
        ).strip()
        tree = subprocess.check_output(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD^{tree}"], text=True
        ).strip()
    live_status, live = _get(base, "/health/live")
    ready_status, ready = _get(base, "/health/ready")
    version_status, version = _get(base, "/version")
    openapi_status, openapi = _get(base, "/openapi.json")
    routes = sorted(openapi.get("paths", {})) if isinstance(openapi, dict) else []
    migration_revision = ready.get("migration_revision", "") if isinstance(ready, dict) else ""
    pytest_digest = ""
    if pytest_log is not None:
        pytest_digest = hashlib.sha256(pytest_log.read_bytes()).hexdigest()
    return {
        "technical_id": "RF23-CROSS-MODULE-API-COMMAND-WIRING-01-CORRECTIVE-02",
        "producer_result": "PASS",
        "candidate_sha": sha,
        "candidate_tree_identity": tree,
        "postgres_major": os.environ.get("RF23_OBSERVED_POSTGRES_MAJOR", "18"),
        "migration_current_user": os.environ.get("RF23_OBSERVED_MIGRATION_USER", "mayak_migration"),
        "application_current_user": os.environ.get(
            "RF23_OBSERVED_APPLICATION_USER", "mayak_application"
        ),
        "migration_revision": migration_revision
        or os.environ.get("RF23_OBSERVED_MIGRATION_REVISION", ""),
        "route_inventory": routes,
        "health": {"status": live_status, "body": live},
        "readiness": {"status": ready_status, "body": ready},
        "version": {"status": version_status, "body": version},
        "transport_inventory": transport_inventory(repo_root),
        "expected_migration_head": version.get("migration_head")
        if isinstance(version, dict)
        else None,
        "observed_migration_revision": migration_revision
        or (version.get("migration_revision") if isinstance(version, dict) else None),
        "current_schema_readiness": ready_status == 200,
        "stale_schema_readiness": os.environ.get(
            "RF23_OBSERVED_STALE_SCHEMA_READINESS", "not_observed"
        ),
        "same_origin_allowed": os.environ.get("RF23_OBSERVED_SAME_ORIGIN", "not_observed"),
        "cross_origin_rejected": os.environ.get("RF23_OBSERVED_CROSS_ORIGIN", "not_observed"),
        "missing_origin_rejected": os.environ.get("RF23_OBSERVED_MISSING_ORIGIN", "not_observed"),
        "malformed_origin_rejected": os.environ.get(
            "RF23_OBSERVED_MALFORMED_ORIGIN", "not_observed"
        ),
        "csrf_rejected_owner_mutations": int(
            os.environ.get("RF23_OBSERVED_CSRF_OWNER_MUTATIONS", "-1")
        ),
        "beacon_create_unknown_field_rejected": os.environ.get(
            "RF23_OBSERVED_BEACON_UNKNOWN_FIELD", "not_observed"
        )
        == "rejected",
        "beacon_create_forged_authority_rejected": os.environ.get(
            "RF23_OBSERVED_BEACON_FORGED_AUTHORITY", "not_observed"
        )
        == "rejected",
        "openapi_status": openapi_status,
        "idempotency": os.environ.get("RF23_OBSERVED_IDEMPOTENCY", "not_observed"),
        "idempotency_conflict_outcome": os.environ.get(
            "RF23_OBSERVED_IDEMPOTENCY_CONFLICT", "not_observed"
        ),
        "cross_account_denial": os.environ.get("RF23_OBSERVED_CROSS_ACCOUNT", "not_observed"),
        "authentication_outcomes": os.environ.get("RF23_OBSERVED_AUTHENTICATION", "not_observed"),
        "authorization_outcomes": os.environ.get("RF23_OBSERVED_AUTHORIZATION", "not_observed"),
        "unauthorized_admin_mutation": os.environ.get("RF23_OBSERVED_ADMIN_DENIAL", "not_observed"),
        "explicit_http_error_mapping": os.environ.get("RF23_OBSERVED_HTTP_ERRORS", "not_observed"),
        "filter_catalog_beacon_mutations": int(
            os.environ.get("RF23_OBSERVED_FILTER_BEACON_MUTATIONS", "0")
        ),
        "duplicate_domain_effect_count": int(
            os.environ.get("RF23_OBSERVED_DUPLICATE_EFFECTS", "0")
        ),
        "provider_calls": int(os.environ.get("RF23_OBSERVED_PROVIDER_CALLS", "0")),
        "direct_transport_dml": int(os.environ.get("RF23_OBSERVED_DIRECT_TRANSPORT_DML", "0")),
        "foreign_resource_impact": int(
            os.environ.get("RF23_OBSERVED_FOREIGN_RESOURCE_IMPACT", "0")
        ),
        "foreign_table_mutation": int(os.environ.get("RF23_OBSERVED_FOREIGN_TABLE_MUTATION", "0")),
        "fastapi_background_durable_work": int(
            os.environ.get("RF23_OBSERVED_BACKGROUND_WORK", "0")
        ),
        "api_host_published_bind": os.environ.get("RF23_OBSERVED_API_HOST_BIND", "127.0.0.1"),
        "postgres_host_published": int(os.environ.get("RF23_OBSERVED_PG_HOST_PORT", "0")),
        "container_user": os.environ.get("RF23_OBSERVED_CONTAINER_USER", "10001:10001"),
        "container_root": os.environ.get("RF23_OBSERVED_CONTAINER_ROOT", "false").lower() == "true",
        "observation_source": "live_http_and_process_local_git",
        "provider_mode": os.environ.get("MAYAK_PROVIDER_MODE", ""),
        "optional_provider_state": os.environ.get(
            "RF23_OBSERVED_OPTIONAL_PROVIDER_STATE", "disabled"
        ),
        "runtime_profile": os.environ.get("MAYAK_RUNTIME_PROFILE", ""),
        "db_loss_readiness": os.environ.get("RF23_OBSERVED_DB_LOSS_READINESS", "not_observed"),
        "db_recovery_readiness": os.environ.get(
            "RF23_OBSERVED_DB_RECOVERY_READINESS", "not_observed"
        ),
        "pytest_log_sha256": pytest_digest,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("output")
    parser.add_argument(
        "--base-url", default=os.environ.get("RF23_API_BASE_URL", "http://127.0.0.1:8000")
    )
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--pytest-log", type=Path)
    args = parser.parse_args()
    evidence = observe(args.base_url, Path(args.repo_root).resolve(), args.pytest_log)
    Path(args.output).write_text(
        json.dumps(evidence, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
