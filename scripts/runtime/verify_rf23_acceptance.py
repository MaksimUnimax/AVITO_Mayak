"""Fail-closed verifier for RF23 evidence, pytest output, and scanner binding."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, NoReturn

TECHNICAL_ID = "RF23-CROSS-MODULE-API-COMMAND-WIRING-01-CORRECTIVE-05"
LEGACY_TECHNICAL_ID = "RF23-CROSS-MODULE-API-COMMAND-WIRING-01-CORRECTIVE-02"
SCANNER = "rf23-safety-scanner/v1"
SUMMARY = re.compile(
    r"^(?:=|\s)*(?P<parts>(?:[0-9][0-9,]*\s+(?:passed|skipped|failed|errors?)(?:,?\s*|$))+).*\bin\s+[0-9.]+s(?:\s+\([^)]*\))?.*=*$"
)


def _fail(message: str) -> NoReturn:
    raise SystemExit(f"RF23 verification failed: {message}")


def _pytest_log(path: Path) -> None:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        _fail(f"pytest log unreadable: {exc}")
    matches: list[dict[str, int]] = []
    for line in lines:
        match = SUMMARY.search(line.strip())
        if not match:
            continue
        counts = {name: 0 for name in ("passed", "skipped", "failed", "errors")}
        for number, label in re.findall(
            r"([0-9][0-9,]*)\s+(passed|skipped|failed|errors?)", match.group("parts")
        ):
            counts["errors" if label.startswith("error") else label] = int(number.replace(",", ""))
        if sum(counts.values()):
            matches.append(counts)
    if len(matches) != 1:
        _fail("pytest log must contain exactly one authoritative terminal summary")
    if matches[0]["failed"] or matches[0]["errors"]:
        _fail(f"pytest log is not green: {matches[0]}")


def _manifest(path: Path, *, root: Path, require_probe: bool = False) -> None:
    try:
        value: Any = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        _fail(f"scanner manifest unreadable: {exc}")
    if (
        not isinstance(value, dict)
        or value.get("scanner_method") != SCANNER
        or value.get("scanner_result") != "PASS"
        or value.get("classification") != "PASS"
        or value.get("finding_count") != 0
        or value.get("findings") != []
    ):
        _fail("scanner manifest is not a clean PASS")
    payloads = value.get("payloads")
    expected_payloads = ["rf23-evidence.json", "rf23-full-pytest.log"]
    if require_probe:
        expected_payloads.append("rf23-runtime-probes.json")
    if (
        not isinstance(payloads, list)
        or [x.get("basename") for x in payloads if isinstance(x, dict)] != expected_payloads
    ):
        _fail("scanner manifest payload inventory is not exact")
    for item in payloads:
        if not isinstance(item, dict) or set(item) != {
            "path",
            "basename",
            "size",
            "sha256",
            "result",
            "classification",
            "finding_count",
        }:
            _fail("malformed scanner payload entry")
        basename = item["basename"]
        if (
            not isinstance(basename, str)
            or basename not in set(expected_payloads)
            or Path(basename).name != basename
        ):
            _fail("unsafe scanner payload identity")
        target = root / basename
        if item["path"] != target.resolve().as_posix() or not target.is_file():
            _fail(f"scanner payload path binding failed: {basename}")
        raw = target.read_bytes()
        if item["size"] != len(raw) or item["sha256"] != hashlib.sha256(raw).hexdigest():
            _fail(f"scanner payload digest binding failed: {basename}")
        if (
            item["result"] != "PASS"
            or item["classification"] != "NONE"
            or item["finding_count"] != 0
        ):
            _fail(f"scanner payload result binding failed: {basename}")


def verify(
    path: str,
    *,
    expected_sha: str | None = None,
    expected_tree: str | None = None,
    manifest: str | None = None,
    pytest_log: str | None = None,
) -> bool:
    root = Path(path).resolve().parent
    try:
        evidence: Any = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    if not isinstance(evidence, dict) or evidence.get("technical_id") not in (
        TECHNICAL_ID,
        LEGACY_TECHNICAL_ID,
    ):
        return False
    corrective_02 = evidence.get("technical_id") == LEGACY_TECHNICAL_ID
    if not corrective_02:
        probe_path = evidence.get("probe_artifact")
        if (
            not isinstance(probe_path, str)
            or Path(probe_path).resolve() != root / "rf23-runtime-probes.json"
        ):
            return False
        if (
            evidence.get("probe_version") != "rf23-runtime-probes/v1"
            or evidence.get("observation_method") != "live_http_and_process_local_git_and_ast"
        ):
            return False
    required = (
        "candidate_sha",
        "candidate_tree_identity",
        "observation_source",
        "producer_result",
        "postgres_major",
        "migration_current_user",
        "application_current_user",
        "migration_revision",
        "pytest_log_sha256",
        "route_inventory",
        "health",
        "readiness",
        "version",
        "authentication_outcomes",
        "authorization_outcomes",
        "idempotency",
        "idempotency_conflict_outcome",
        "cross_account_denial",
        "unauthorized_admin_mutation",
        "explicit_http_error_mapping",
        "optional_provider_state",
        "filter_catalog_beacon_mutations",
        "provider_calls",
        "direct_transport_dml",
        "foreign_table_mutation",
        "fastapi_background_durable_work",
        "duplicate_domain_effect_count",
        "foreign_resource_impact",
        "api_host_published_bind",
        "postgres_host_published",
        "container_user",
        "container_root",
    )
    if (
        any(key not in evidence for key in required)
        or expected_sha is None
        or evidence.get("candidate_sha") != expected_sha
    ):
        return False
    if corrective_02:
        inventory = evidence.get("transport_inventory")
        if not isinstance(inventory, dict) or any(
            inventory.get(key) != 0
            for key in ("forbidden", "private_identity", "owner_read_model", "direct_dml")
        ):
            return False
        if not evidence.get("expected_migration_head") or evidence.get(
            "expected_migration_head"
        ) != evidence.get("observed_migration_revision"):
            return False
        version_body = (
            evidence.get("version", {}).get("body", {})
            if isinstance(evidence.get("version"), dict)
            else {}
        )
        if (
            not isinstance(version_body, dict)
            or not version_body.get("migration_head")
            or not version_body.get("migration_revision")
        ):
            return False
        if evidence.get("stale_schema_readiness") != "rejected":
            return False
        if any(
            evidence.get(key) != "rejected"
            for key in (
                "cross_origin_rejected",
                "missing_origin_rejected",
                "malformed_origin_rejected",
            )
        ):
            return False
        if (
            evidence.get("same_origin_allowed") != "allowed"
            or evidence.get("csrf_rejected_owner_mutations") != 0
        ):
            return False
        if not evidence.get("beacon_create_unknown_field_rejected") or not evidence.get(
            "beacon_create_forged_authority_rejected"
        ):
            return False
    if expected_tree is None or evidence.get("candidate_tree_identity") != expected_tree:
        return False
    if (
        not isinstance(evidence["route_inventory"], list)
        or not evidence["route_inventory"]
        or not evidence["candidate_tree_identity"]
    ):
        return False
    if (
        evidence.get("producer_result") != "PASS"
        or evidence.get("observation_source") != "live_http_and_process_local_git"
        or evidence.get("postgres_major") not in (18, "18")
        or evidence.get("migration_current_user") != "mayak_migration"
        or evidence.get("application_current_user") != "mayak_application"
        or not evidence.get("migration_revision")
    ):
        return False
    required_routes = {"/health/live", "/health/ready", "/version", "/acceptance/login"}
    if not required_routes.issubset(set(evidence["route_inventory"])):
        return False
    if (
        not isinstance(evidence["health"], dict)
        or evidence["health"].get("status") != 200
        or not isinstance(evidence["readiness"], dict)
        or evidence["readiness"].get("status") != 200
        or not isinstance(evidence["version"], dict)
        or evidence["version"].get("status") != 200
    ):
        return False
    if any(
        evidence.get(key) != "proven"
        for key in (
            "authentication_outcomes",
            "authorization_outcomes",
            "idempotency",
            "cross_account_denial",
            "unauthorized_admin_mutation",
            "explicit_http_error_mapping",
            "idempotency_conflict_outcome",
        )
    ):
        return False
    if evidence.get("optional_provider_state") != "disabled":
        return False
    if any(
        evidence.get(key) != 0
        for key in (
            "provider_calls",
            "direct_transport_dml",
            "foreign_table_mutation",
            "fastapi_background_durable_work",
            "duplicate_domain_effect_count",
            "foreign_resource_impact",
            "filter_catalog_beacon_mutations",
        )
    ):
        return False
    if (
        evidence.get("api_host_published_bind") != "127.0.0.1"
        or evidence.get("postgres_host_published") != 0
        or evidence.get("container_root") is True
        or evidence.get("container_user") in (None, "", "root", "0", 0)
    ):
        return False
    if (
        evidence.get("provider_mode") != "disabled"
        or evidence.get("runtime_profile") != "synthetic_acceptance"
    ):
        return False
    if (
        evidence.get("db_loss_readiness") != "unhealthy"
        or evidence.get("db_recovery_readiness") != "healthy"
    ):
        return False
    if evidence.get("idempotency") in (None, "not_observed") or evidence.get(
        "cross_account_denial"
    ) in (None, "not_observed"):
        return False
    try:
        log_path = Path(pytest_log) if pytest_log else root / "rf23-full-pytest.log"
        _pytest_log(log_path)
        if evidence.get("pytest_log_sha256") != hashlib.sha256(log_path.read_bytes()).hexdigest():
            return False
        _manifest(
            Path(manifest) if manifest else root / "rf23-safety-manifest.json",
            root=root,
            require_probe=not corrective_02,
        )
    except SystemExit:
        return False
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence")
    parser.add_argument("--expected-sha", required=True)
    parser.add_argument("--expected-tree", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--pytest-log", required=True)
    args = parser.parse_args()
    raise SystemExit(
        0
        if verify(
            args.evidence,
            expected_sha=args.expected_sha,
            expected_tree=args.expected_tree,
            manifest=args.manifest,
            pytest_log=args.pytest_log,
        )
        else 1
    )
