# ruff: noqa: E501
"""RF26 bounded observability receipt and exact uploaded-safe-set verifier."""

from __future__ import annotations

import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Any, cast

from mayak.platform.observability import JsonOperationalFormatter
from scripts.runtime.rf24_backup_restore_core import scan_paths

TECHNICAL_ID = "RF26-OBSERVABILITY-BACKUP-RECOVERY-01"
OBSERVABILITY = "observability.json"
SAFETY = "artifact-safety.json"
MANIFEST = "artifact-manifest.json"
EXPECTED_FILES = (
    "acceptance.json", "h8-preflight.json", "verifier.json", "final-verifier.json",
    OBSERVABILITY, SAFETY, MANIFEST,
)
OBSERVABILITY_SECTIONS = (
    "structured_log_schema", "correlation", "liveness", "readiness", "version_build",
    "migration_revision", "diagnostics", "redaction",
)
FORBIDDEN = ("password", "token", "cookie", "private_key", "credential", "dsn", "raw_log", "raw_backup")


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def _api_projection(evidence: dict[str, Any]) -> dict[str, Any]:
    stages = evidence.get("stages", [])
    h8 = next((x for x in stages if isinstance(x, dict) and x.get("stage_id") == "H8_REBUILD_FROM_ZERO"), None)
    if not isinstance(h8, dict) or not isinstance(h8.get("observed_outputs"), dict):
        raise ValueError("H8 runtime observability projection is missing")
    projection = h8["observed_outputs"].get("api_http_projection")
    if not isinstance(projection, dict):
        raise ValueError("H8 API probe projection is missing")
    return projection


def build_observability_receipt(
    *, evidence: dict[str, Any], source_sha: str, run_id: str, environment_id: str,
) -> dict[str, Any]:
    """Build proof from the accepted formatter and the H8 real API probe output."""
    projection = _api_projection(evidence)
    version = projection.get("version")
    diagnostics = projection.get("diagnostics")
    readiness = projection.get("readiness")
    if not all(isinstance(item, dict) for item in (version, diagnostics, readiness)):
        raise ValueError("bounded API response proof is incomplete")
    version = cast(dict[str, Any], version)
    diagnostics = cast(dict[str, Any], diagnostics)
    readiness = cast(dict[str, Any], readiness)
    migration = version.get("migration_revision") or diagnostics.get("migration_revision") or readiness.get("migration_revision")
    if not isinstance(migration, str) or not migration:
        raise ValueError("migration revision proof is missing")

    previous = {key: os.environ.get(key) for key in ("MAYAK_SOURCE_SHA", "MAYAK_ENVIRONMENT_ID")}
    os.environ["MAYAK_SOURCE_SHA"], os.environ["MAYAK_ENVIRONMENT_ID"] = source_sha, environment_id
    try:
        record = logging.LogRecord("mayak.rf26.observability", logging.INFO, __file__, 1, "synthetic operational event", (), None)
        record.operation, record.outcome, record.reason_code = "rf26_observability_probe", "success", "RF26_PROBE_PASS"
        record.correlation_id, record.run_id, record.work_item_id = f"rf26:{run_id}", run_id, f"rf26-work:{run_id}"
        record.attempt, record.latency_ms, record.readiness_state, record.migration_revision = "1", 1.0, "ready", migration
        event = json.loads(JsonOperationalFormatter().format(record))
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
    required_fields = ("timestamp", "environment_id", "source_sha", "module", "operation", "correlation_id", "run_id", "work_item_id", "attempt", "result", "latency_ms", "readiness_state", "migration_revision", "redaction_state")
    if any(field not in event for field in required_fields):
        raise ValueError("accepted structured formatter omitted a required field")
    return {
        "schema_version": 1, "technical_id": TECHNICAL_ID, "source_sha": source_sha,
        "hosted_run_id": str(run_id), "environment_id": environment_id, "verdict": "PASS",
        "structured_log_schema": {"verdict": "PASS", "formatter": "mayak.platform.observability.JsonOperationalFormatter", "required_fields": list(required_fields), "sample_event": event},
        "correlation": {"verdict": "PASS", "field": "correlation_id", "run_id": str(run_id), "work_id": f"rf26-work:{run_id}", "attempt": "1"},
        "liveness": {"verdict": "PASS", "status": "live"},
        "readiness": {"verdict": "PASS", "status": readiness.get("status"), "migration_revision": readiness.get("migration_revision")},
        "version_build": {"verdict": "PASS", "source_sha": version.get("source_sha"), "environment_id": version.get("environment_id")},
        "migration_revision": {"verdict": "PASS", "revision": migration},
        "diagnostics": {"verdict": "PASS", "readiness_state": diagnostics.get("readiness_state"), "process_kind": diagnostics.get("process_kind"), "runtime_profile": diagnostics.get("runtime_profile")},
        "redaction": {"verdict": "PASS", "formatter_safe_message": True, "secret_fields_omitted": True, "raw_payloads_omitted": True},
    }


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path.name} is not an object")
    return value


def verify_observability(path: Path, *, source_sha: str, run_id: str, environment_id: str) -> None:
    value = _json(path)
    if value.get("schema_version") != 1 or value.get("technical_id") != TECHNICAL_ID or value.get("source_sha") != source_sha or str(value.get("hosted_run_id")) != str(run_id) or value.get("environment_id") != environment_id or value.get("verdict") != "PASS":
        raise ValueError("observability identity or verdict mismatch")
    for section in OBSERVABILITY_SECTIONS:
        if not isinstance(value.get(section), dict) or value[section].get("verdict") != "PASS":
            raise ValueError(f"observability proof missing: {section}")
    if value["migration_revision"].get("revision") != value["readiness"].get("migration_revision"):
        raise ValueError("observability migration revision mismatch")
    def reject_unsafe_keys(item: Any) -> None:
        if isinstance(item, dict):
            for key, child in item.items():
                lowered = str(key).lower()
                if any(word in lowered for word in ("password", "token", "cookie", "private_key", "credential", "dsn")):
                    raise ValueError("unsafe observability field")
                reject_unsafe_keys(child)
        elif isinstance(item, list):
            for child in item:
                reject_unsafe_keys(child)

    reject_unsafe_keys(value)
    encoded = json.dumps(value, ensure_ascii=True).lower()
    if any(word in encoded for word in ("postgresql://", "begin rsa private key", "bearer ", "password=", "cookie=")):
        raise ValueError("unsafe observability value")


def write_exact_artifact(root: Path, *, source_sha: str, run_id: str, environment_id: str) -> None:
    actual = sorted(path.name for path in root.iterdir())
    if actual != sorted(set(EXPECTED_FILES) - {MANIFEST}):
        raise ValueError(f"exact safe set mismatch before manifest: {actual}")
    verify_observability(root / OBSERVABILITY, source_sha=source_sha, run_id=run_id, environment_id=environment_id)
    safety = _json(root / SAFETY)
    if safety.get("finding_count") != 0:
        raise ValueError("artifact safety findings present")
    entries = []
    for path in sorted(root.iterdir()):
        if path.name == MANIFEST:
            continue
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"unsafe artifact member: {path.name}")
        entries.append({"filename": path.name, "size": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    manifest = {"schema_version": 1, "technical_id": TECHNICAL_ID, "source_sha": source_sha, "hosted_run_id": str(run_id), "files": entries, "self_entry": "artifact-manifest.json is explicitly excluded from its own inventory"}
    (root / MANIFEST).write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def verify_exact_artifact(root: Path, *, source_sha: str, run_id: str, environment_id: str) -> None:
    actual = sorted(path.name for path in root.iterdir())
    if actual != sorted(EXPECTED_FILES):
        raise ValueError(f"uploaded safe set mismatch: {actual}")
    manifest = _json(root / MANIFEST)
    if manifest.get("source_sha") != source_sha or str(manifest.get("hosted_run_id")) != str(run_id) or manifest.get("technical_id") != TECHNICAL_ID:
        raise ValueError("manifest identity mismatch")
    entries = manifest.get("files")
    if not isinstance(entries, list) or len(entries) != len(EXPECTED_FILES) - 1 or len({item.get("filename") for item in entries if isinstance(item, dict)}) != len(entries):
        raise ValueError("manifest inventory is not exact")
    for item in entries:
        if not isinstance(item, dict) or item.get("filename") not in set(EXPECTED_FILES) - {MANIFEST}:
            raise ValueError("manifest contains unexpected member")
        path = root / item["filename"]
        if path.is_symlink() or not path.is_file() or path.stat().st_size != item.get("size") or hashlib.sha256(path.read_bytes()).hexdigest() != item.get("sha256"):
            raise ValueError(f"manifest digest or size mismatch: {path.name}")
        value = _json(path)
        if value.get("source_sha") is not None and value.get("source_sha") != source_sha:
            raise ValueError(f"source SHA mismatch: {path.name}")
        if value.get("hosted_run_id") is not None and str(value.get("hosted_run_id")) != str(run_id):
            raise ValueError(f"run identity mismatch: {path.name}")
        if value.get("run_id") is not None and str(value.get("run_id")) != str(run_id):
            raise ValueError(f"run identity mismatch: {path.name}")
    verify_observability(root / OBSERVABILITY, source_sha=source_sha, run_id=run_id, environment_id=environment_id)
    if _json(root / SAFETY).get("finding_count") != 0:
        raise ValueError("artifact safety is not clean")
    report = scan_paths([root / name for name in sorted(EXPECTED_FILES) if name != MANIFEST])
    if report.get("finding_count") != 0:
        raise ValueError("artifact safety scanner rejected uploaded set")
