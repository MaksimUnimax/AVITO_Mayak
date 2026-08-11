# ruff: noqa: E501
"""Independent, fail-closed verifier for RF26 current-run receipts."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from scripts.runtime.rf24_backup_restore_core import verify_evidence

TECHNICAL_ID = "RF26-OBSERVABILITY-BACKUP-RECOVERY-01"
STAGES = (
    "H8_REBUILD_FROM_ZERO", "H9_BACKUP", "H10_RESTORE_SEMANTIC_EQUIVALENCE",
    "H11_API_RESTART", "H12_WORKER_INTERRUPTION_RESTART", "H13_SCHEDULER_RESTART",
    "H14_INTERRUPTED_MIGRATION", "H15_OUTBOX_RECONCILIATION", "H16_RETENTION_RPO_RTO",
)
SECRET = re.compile(r"(BEGIN [A-Z ]+PRIVATE KEY|postgres(?:ql)?://[^\s:]+:[^\s@]+@|password\s*[=:]|bearer\s+|authorization\s*[:=])", re.I)


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def _require(condition: object, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _stage(data: dict[str, Any], stage_id: str) -> dict[str, Any]:
    stages = data.get("stages")
    _require(isinstance(stages, list), "stage receipts missing")
    matches = [item for item in stages if isinstance(item, dict) and item.get("stage_id") == stage_id]
    _require(len(matches) == 1, f"mandatory or duplicate stage: {stage_id}")
    return matches[0]


def verify_evidence_file(data: dict[str, Any], *, source_sha: str, run_id: str) -> dict[str, Any]:
    _require(data.get("schema_version") == 3, "unsupported RF26 evidence schema")
    _require(data.get("technical_id") == TECHNICAL_ID, "technical identity mismatch")
    _require(data.get("source_sha") == source_sha, "source SHA mismatch")
    _require(str(data.get("hosted_run_id")) == str(run_id), "run ID mismatch")
    _require(data.get("environment_id"), "environment identity missing")
    stages = data.get("stages")
    _require(isinstance(stages, list) and [s.get("stage_id") for s in stages if isinstance(s, dict)] == list(STAGES), "stage order mismatch")
    for stage_id in STAGES:
        item = _stage(data, stage_id)
        _require(item.get("source_sha") == source_sha, f"stage source SHA mismatch: {stage_id}")
        _require(str(item.get("hosted_run_id")) == str(run_id), f"stage run ID mismatch: {stage_id}")
        _require(item.get("environment_id") == data["environment_id"], f"stage environment mismatch: {stage_id}")
        started = datetime.fromisoformat(str(item.get("started_at")))
        finished = datetime.fromisoformat(str(item.get("finished_at")))
        _require(finished >= started, f"finish before start: {stage_id}")
        duration = item.get("duration_seconds")
        _require(isinstance(duration, (int, float)) and not isinstance(duration, bool) and duration > 0, f"invalid duration: {stage_id}")
        _require(item.get("observed_inputs") and item.get("observed_outputs"), f"scenario observations missing: {stage_id}")
        _require(item.get("operation_identity"), f"operation identity missing: {stage_id}")
        _require(item.get("assertion", {}).get("result") == "PASS", f"stage did not pass: {stage_id}")
        expected_hash = hashlib.sha256(_canonical({k: v for k, v in item.items() if k != "receipt_sha256"})).hexdigest()
        _require(item.get("receipt_sha256") == expected_hash, f"receipt hash mismatch: {stage_id}")
    h8 = _stage(data, "H8_REBUILD_FROM_ZERO")["observed_outputs"]
    _require(h8.get("migration_revision") and h8.get("readiness_recovered") is True and h8.get("runtime_seed_observed") is True, "H8 proof incomplete")
    h9 = _stage(data, "H9_BACKUP")["observed_outputs"]
    for key in ("sha256", "size", "pg_dump_version", "pg_restore_version", "readability_verified", "inventory_verified", "migration_revision"):
        _require(h9.get(key), f"H9 observation missing: {key}")
    _require(h9.get("format") == "custom" and int(h9["size"]) > 0 and h9.get("readability_verified") is True and h9.get("inventory_verified") is True, "backup is not verified PG archive")
    h10 = _stage(data, "H10_RESTORE_SEMANTIC_EQUIVALENCE")
    _require(h10["observed_inputs"].get("source") != h10["observed_inputs"].get("target"), "restore source equals target")
    for key in ("source_semantic_digest", "target_semantic_digest", "semantic_equivalence", "source_unchanged", "application_read", "migration_revision"):
        _require(h10["observed_outputs"].get(key), f"H10 observation missing: {key}")
    _require(h10["observed_outputs"]["source_semantic_digest"] == h10["observed_outputs"]["target_semantic_digest"], "semantic equivalence mismatch")
    h11 = _stage(data, "H11_API_RESTART")["observed_outputs"]
    _require(h11.get("process_identity_before") != h11.get("process_identity_after") and h11.get("readiness_recovered") is True, "restart identity proof missing")
    h12 = _stage(data, "H12_WORKER_INTERRUPTION_RESTART")["observed_outputs"]
    for key in ("one_logical_work_item", "lease_recovery_persisted", "recovery_completed", "duplicate_effect", "live_provider_calls"):
        _require(key in h12, f"H12 observation missing: {key}")
    _require(h12["live_provider_calls"] == 0 and h12["duplicate_effect"] is False, "H12 unsafe effect")
    h13 = _stage(data, "H13_SCHEDULER_RESTART")["observed_outputs"]
    _require(h13.get("scheduler_before") and h13.get("scheduler_after") and h13.get("scheduler_before") != h13.get("scheduler_after") and h13.get("duplicate_scheduling") is False, "H13 proof incomplete")
    h14 = _stage(data, "H14_INTERRUPTED_MIGRATION")["observed_outputs"]
    for key in ("interrupted_revision", "recovered_revision", "readiness_did_not_pass", "readiness_recovered"):
        _require(key in h14, f"H14 observation missing: {key}")
    _require(h14["readiness_did_not_pass"] is True, "interrupted migration falsely passed readiness")
    h15 = _stage(data, "H15_OUTBOX_RECONCILIATION")["observed_outputs"]
    for key in ("effect_unknown_until_reconciled", "reconciliation_required", "blind_retry_count", "live_provider_calls", "duplicate_external_effect"):
        _require(key in h15, f"H15 observation missing: {key}")
    _require(h15["blind_retry_count"] == 0 and h15["live_provider_calls"] == 0 and h15["duplicate_external_effect"] is False, "H15 unsafe reconciliation")
    h16 = _stage(data, "H16_RETENTION_RPO_RTO")["observed_outputs"]
    _require(set(h16.get("deleted", [])) == {"expired-verified-inactive"}, "retention deletion classification invalid")
    _require(set(h16.get("preserved", [])) == {"current", "active", "malformed", "tampered", "unverified", "unknown", "symlink"}, "retention preservation classification invalid")
    _require(0 < float(h16.get("rto_measured_seconds", 0)) < 7200, "RTO is not a measured bounded value")
    _require(0 < float(h16.get("rpo_interval_hours", 0)) <= 24, "RPO policy proof missing")
    current = data.get("rf24_current_run")
    _require(isinstance(current, dict), "current-run RF24 evidence missing")
    verify_evidence(current, source_sha=source_sha, run_id=run_id)
    security = data.get("security")
    _require(security == {"raw_backup_uploaded": False, "credentials_exposure": False, "production_personal_data": False, "live_provider_calls": 0, "foreign_resource_impact": "none"}, "security invariant failed")
    encoded = json.dumps(data, ensure_ascii=True)
    _require(not SECRET.search(encoded), "secret-bearing evidence")
    return {"schema_version": 1, "technical_id": TECHNICAL_ID, "source_sha": source_sha, "hosted_run_id": run_id, "verdict": "PASS"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--result", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = verify_evidence_file(json.loads(args.evidence.read_text(encoding="utf-8")), source_sha=args.source_sha, run_id=args.run_id)
    except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise SystemExit(f"RF26 evidence rejected: {exc}") from exc
    result["evidence_sha256"] = hashlib.sha256(args.evidence.read_bytes()).hexdigest()
    args.result.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
