# ruff: noqa: E501
"""Pure, fail-closed checks for the RF24 PostgreSQL recovery rehearsal.

The module deliberately contains no database authority.  It validates the
safe projection emitted by the acceptance runner and is therefore also useful
to offline tests and independent artifact verification.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, cast

TECHNICAL_ID = "RF24-BACKUP-RESTORE-SCENARIO-01"

# The acceptance projections are intentionally declared once.  This is the
# read-only contract checked against the migrated SOURCE database before any
# semantic projection or backup/restore mutation is attempted.
RF24_PROJECTION_SCHEMA: dict[str, tuple[str, tuple[str, ...]]] = {
    "identity": ("identity_accounts", ("id", "state", "row_version")),
    "entitlements": ("entitlement_access_grants", ("id", "account_id", "tariff_id", "source_code", "grant_kind", "granted_capability", "granted_scope", "valid_from", "valid_until", "state", "row_version")),
    "beacon": ("beacon_beacons", ("id", "account_id", "source_url", "state", "current_revision_no", "current_revision_id", "row_version")),
    "beacon_configuration_history": ("beacon_configuration_revisions", ("beacon_id", "revision_no", "source_url", "accepted_filter", "created_by_account_id", "created_at")),
    "beacon_history": ("beacon_lifecycle_events", ("id", "beacon_id", "from_state", "to_state", "actor_account_id", "reason", "created_at", "system_actor_class", "causation_reference", "policy_source_reference")),
    "scan_listing": ("scan_beacon_listing_state", ("id", "beacon_id", "external_listing_key", "last_seen_at", "last_snapshot", "first_seen_at", "row_version", "updated_at")),
    "scan_runs": ("scan_runs", ("id", "work_item_id", "beacon_id", "revision_no", "state", "started_at", "completed_at", "row_version")),
    "notification": ("notification_events", ("id", "account_id", "beacon_id", "run_id", "source_effect_fingerprint", "event_code", "payload")),
    "notification_endpoint": ("notification_endpoints", ("id", "provider_code")),
    "notification_outbox": ("notification_outbox", ("id", "event_id", "endpoint_id", "state", "row_version")),
    "notification_delivery": ("notification_delivery_attempts", ("id", "outbox_id", "attempt_number", "state", "effect_fingerprint")),
    "idempotency": ("platform_idempotency_records", ("id", "scope", "idempotency_key", "request_fingerprint")),
    "audit": ("platform_audit_entries", ("id", "action_code", "target_type", "target_id", "correlation_id")),
    "scan_schedules": ("scan_schedules", ("id", "beacon_id", "interval_seconds", "next_due_at", "state", "row_version")),
    "scan_work_items": ("scan_work_items", ("id", "schedule_id", "beacon_id", "due_at", "state", "created_at", "row_version")),
}


class ProjectionSchemaError(ValueError):
    """Safe, deterministic projection/schema mismatch."""


def validate_projection_schema(connection: Any, *, schema: str = "mayak") -> None:
    """Fail closed using only information_schema identifiers, never data/DSNs."""
    required = {(table, column) for table, columns in RF24_PROJECTION_SCHEMA.values() for column in columns}
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT table_name, column_name FROM information_schema.columns "
            "WHERE table_schema=%s",
            (schema,),
        )
        actual = {(str(table), str(column)) for table, column in cursor.fetchall()}
    missing = sorted(f"{table}.{column}" for table, column in required - actual)
    missing_tables = sorted({table for table, _ in required if not any(t == table for t, _ in actual)})
    if missing:
        detail = ", ".join([*(f"table:{table}" for table in missing_tables), *(f"column:{item}" for item in missing)])
        raise ProjectionSchemaError(f"RF24 projection schema incompatible: {detail}")
REQUIRED_CONTROLS = (
    "tampered_digest",
    "corrupt_copy",
    "wrong_source_sha",
    "wrong_source_revision",
    "nonempty_newer_target",
    "duplicate_restore",
)
REQUIRED_STATE_CLASSES = tuple(RF24_PROJECTION_SCHEMA)
SECRET = re.compile(
    r"((?:postgres|postgresql)(?:\+[^\s:/]+)?://[^\s:@/]+:[^\s@/]+@|password\s*[=:]\s*[^<\s,}]+|"
    r"bearer\s+[A-Za-z0-9._-]+|BEGIN [A-Z ]+PRIVATE KEY|set-cookie|authorization)",
    re.I,
)
RAW_SUFFIXES = {".dump", ".backup", ".tar", ".tar.gz", ".sql.gz", ".pgdump"}


def canonical_digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def require(condition: object, message: str) -> None:
    if not condition:
        raise ValueError(message)


def verify_evidence(
    evidence: dict[str, Any], *, source_sha: str, run_id: str | None = None
) -> dict[str, Any]:
    require(evidence.get("technical_id") == TECHNICAL_ID, "technical identity mismatch")
    require(evidence.get("schema_version") == 2, "unsupported evidence schema")
    require(
        re.fullmatch(r"[0-9a-f]{40}", str(evidence.get("source_sha", "")))
        and evidence["source_sha"] == source_sha,
        "source SHA mismatch",
    )
    if run_id is not None:
        require(evidence.get("hosted_run_id") == run_id, "hosted run identity mismatch")
    require(evidence.get("backup", {}).get("sha256"), "backup digest missing")
    require(int(evidence.get("backup", {}).get("size", 0)) > 0, "backup size missing")
    backup = evidence.get("backup", {})
    require(backup.get("verified") is True, "backup not verified")
    require(backup.get("format") == "custom", "logical custom backup required")
    require(backup.get("inventory_verified") is True, "backup inventory not verified")
    require(backup.get("readability_verified") is True, "backup readability not verified")
    require(backup.get("pg_dump_version"), "pg_dump version proof missing")
    require(backup.get("pg_restore_version"), "pg_restore version proof missing")
    require(backup.get("postgres_server_version"), "server version proof missing")
    require("server_version" not in backup, "mislabeled server version proof")
    require(evidence.get("restore", {}).get("result") == "PASS", "restore failed")
    require(evidence.get("runtime_read_proof") is True, "restored runtime read proof missing")
    require(
        evidence.get("source_fingerprint_before") == evidence.get("source_fingerprint_after"),
        "source mutated",
    )
    require(
        evidence.get("target_semantic_equivalence") is True, "target is not semantically equivalent"
    )
    source_projection = evidence.get("source_projection")
    target_projection = evidence.get("target_projection")
    require(isinstance(source_projection, dict), "source semantic projection missing")
    require(isinstance(target_projection, dict), "target semantic projection missing")
    source_projection = cast(dict[str, Any], source_projection)
    target_projection = cast(dict[str, Any], target_projection)
    require(set(source_projection) >= set(REQUIRED_STATE_CLASSES), "source projection omits required state class")
    require(set(target_projection) >= set(REQUIRED_STATE_CLASSES), "target projection omits required state class")
    require(source_projection == target_projection, "source/target semantic projection mismatch")
    controls = evidence.get("negative_controls", {})
    for name in REQUIRED_CONTROLS:
        control = controls.get(name)
        require(isinstance(control, dict), f"negative control proof missing: {name}")
        require(control.get("executed") is True, f"negative control not executed: {name}")
        require(control.get("shared_preflight_used") is True, f"negative control bypassed shared preflight: {name}")
        require(control.get("preflight_result") == "BLOCKED", f"negative control not blocked: {name}")
        require(control.get("observed_reason"), f"negative control reason missing: {name}")
        require(control.get("target_fingerprint_before"), f"negative control target proof missing: {name}")
        require(control.get("target_fingerprint_after") == control.get("target_fingerprint_before"), f"negative control mutated target: {name}")
    seed = cast(dict[str, Any], evidence.get("seed", {}))
    require(seed.get("runtime_boundary") == "accepted-public-runtime", "runtime seed proof missing")
    seeded = seed.get("state_classes", {})
    require(isinstance(seeded, dict) and seeded, "seed state proof missing")
    require(all(isinstance(v, dict) and int(v.get("count", 0)) > 0 and v.get("projection_digest") for v in seeded.values()), "seed state is not meaningful")
    aliases = {"account": "identity", "entitlement": "entitlements", "notification_outbox": "notification_outbox"}
    for name, item in seeded.items():
        observed = source_projection.get(aliases.get(name, name), {})
        require(int(observed.get("count", 0)) > 0, f"seed state absent from source projection: {name}")
    replay = evidence.get("idempotency_replay")
    require(isinstance(replay, dict), "idempotency replay proof missing")
    require(replay.get("executed") is True, "idempotency replay was not executed")
    for field in ("boundary", "scope", "key", "fingerprint", "result", "before", "after"):
        require(replay.get(field), f"idempotency replay proof missing: {field}")
    require(replay.get("boundary") in {"POST /api/v1/beacons", "accepted-public-runtime"}, "unknown replay boundary")
    result = replay.get("result")
    require(isinstance(result, dict) and result.get("class") in {"duplicate", "idempotent"} and result.get("status") in {200, 201, 204}, "replay result is not duplicate/idempotent")
    before_replay, after_replay = replay["before"], replay["after"]
    require(isinstance(before_replay, dict) and isinstance(after_replay, dict), "replay snapshots missing")
    require(before_replay.get("fingerprint") and after_replay.get("fingerprint"), "replay fingerprints missing")
    require(isinstance(before_replay.get("counts"), dict) and isinstance(after_replay.get("counts"), dict), "replay count proof missing")
    require(replay.get("scope") and replay.get("key") and replay.get("fingerprint"), "replay identity proof missing")
    require(before_replay.get("fingerprint") == after_replay.get("fingerprint"), "replay fingerprint changed")
    for field in ("beacon_revision_delta", "lifecycle_delta", "notification_delta", "outbox_delta", "provider_effect_delta"):
        require(replay.get(field) == 0, f"replay duplicate effect observed: {field}")
    require(replay.get("live_provider_calls") == 0, "replay made a live provider call")
    security = evidence.get("security", {})
    for name, expected in {
        "provider_live_calls": 0,
        "raw_provider_payload": False,
        "production_personal_data": False,
        "public_ingress": False,
        "postgres_host_published": False,
        "foreign_resource_impact": "none",
        "credentials_exposure": False,
        "raw_backup_uploaded": False,
        "raw_backup_cleanup": True,
        "direct_foreign_module_dml": False,
        "owner_bypass": False,
    }.items():
        require(security.get(name) == expected, f"security invariant failed: {name}")
    require(evidence.get("clean_target_prerequisite") is True, "clean target prerequisite missing")
    return {
        "schema_version": 2,
        "technical_id": TECHNICAL_ID,
        "source_sha": source_sha,
        "verdict": "PASS",
    }


def scan_paths(paths: list[Path]) -> dict[str, Any]:
    require(paths == list(dict.fromkeys(paths)), "artifact upload set contains duplicates")
    findings: list[dict[str, str]] = []
    for path in paths:
        if not path.is_file() or path.stat().st_size == 0:
            findings.append({"path": path.name, "reason": "missing-or-empty"})
            continue
        if path.suffix.lower() in RAW_SUFFIXES or path.name.endswith(".sql.gz"):
            findings.append({"path": path.name, "reason": "raw-backup-file"})
        data = path.read_bytes()
        text = data.decode("utf-8", "replace")
        if SECRET.search(text):
            findings.append({"path": path.name, "reason": "credential-or-secret-material"})
        if "raw_provider_payload" in text and '"raw_provider_payload": false' not in text:
            findings.append({"path": path.name, "reason": "raw-provider-payload-marker"})
        if (
            re.search(r"production[_ -]?personal|real[_ -]?person|@avito\.ru", text, re.I)
            and '"production_personal_data": false' not in text
        ):
            findings.append({"path": path.name, "reason": "production-personal-data-marker"})
    return {
        "schema_version": 1,
        "scanner": "rf24-backup-restore",
        "finding_count": len(findings),
        "findings": findings,
        "sha256": {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths if p.is_file()
        },
    }


def build_manifest(
    paths: list[Path], *, source_sha: str, run_id: str, scanner: dict[str, Any]
) -> dict[str, Any]:
    require(scanner.get("finding_count") == 0, "artifact scanner is not clean")
    expected_names = {p.name for p in paths}
    require(set(scanner.get("sha256", {})) == expected_names, "scanner set is not the upload set")
    require(all(p.suffix.lower() not in RAW_SUFFIXES for p in paths), "raw backup in upload set")
    return {
        "schema_version": 2,
        "artifact_name": "rf24-backup-restore",
        "technical_id": TECHNICAL_ID,
        "source_sha": source_sha,
        "hosted_run_id": run_id,
        "raw_backup_excluded": True,
        "upload_set_exact": True,
        "finding_count": 0,
        "files": [
            {
                "filename": p.name,
                "size": p.stat().st_size,
                "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
            }
            for p in paths
        ],
    }
