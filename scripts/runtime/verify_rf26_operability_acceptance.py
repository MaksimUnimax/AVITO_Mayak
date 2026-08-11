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


def _derive_duplicate_count(raw: dict[str, Any]) -> int:
    ids = raw.get("work_ids_after_second_scheduler_evaluation")
    key = raw.get("schedule_key", {})
    _require(isinstance(ids, list) and isinstance(key, dict) and key.get("work_item_id"), "H13 raw durable identities missing")
    counts = raw.get("counts")
    _require(isinstance(counts, dict), "H13 durable boundary counts missing")
    _require(counts.get("before") == len(raw.get("work_ids_before_scheduler", []))
             and counts.get("after_first") == len(raw.get("work_ids_after_first_materialization", []))
             and counts.get("after_second") == len(ids), "H13 durable counts disagree")
    target = str(key["work_item_id"])
    return max(0, sum(str(item) == target for item in ids) - 1)


def _derive_h15(raw: dict[str, Any]) -> tuple[bool, bool, int, int, int]:
    _require(isinstance(raw, dict), "H15 raw persistence boundaries missing")
    for name in ("P1", "P2", "P3", "P4", "P5"):
        _require(isinstance(raw.get(name), dict), f"H15 boundary missing: {name}")
    p2, p4, p5 = raw["P2"], raw["P4"], raw["P5"]
    attempts2 = p2.get("attempts", [])
    rec4 = p4.get("reconciliations", [])
    attempts5 = p5.get("attempts", [])
    _require(isinstance(attempts2, list) and isinstance(rec4, list) and isinstance(attempts5, list), "H15 persistence identities malformed")
    unknown = any(str(a.get("state", "")).upper() in {"UNKNOWN", "PENDING_RECONCILIATION", "RECONCILIATION_REQUIRED", "AMBIGUOUS"} for a in attempts2)
    required = len(rec4) > 0 and any(str(r.get("state", "")).upper() in {"RESOLVED", "COMMITTED", "DELIVERED", "NO_EFFECT_RETRY", "RESOLVED_NO_EFFECT_RETRY"} for r in rec4)
    attempt_ids_unknown = {str(a.get("id")) for a in attempts2 if str(a.get("state", "")).upper() in {"UNKNOWN", "PENDING_RECONCILIATION", "RECONCILIATION_REQUIRED", "AMBIGUOUS"}}
    blind = sum(1 for a in attempts5 if str(a.get("id")) not in attempt_ids_unknown and str(a.get("state", "")).upper() in {"PENDING", "SENDING"})
    effect_ids = [
        str(a.get("effect_fingerprint"))
        for a in attempts5
        if a.get("effect_fingerprint") and str(a.get("state", "")).upper() in {"DELIVERED", "DELIVERED_ACCEPTED", "SUCCEEDED"}
    ]
    duplicates = len(effect_ids) - len(set(effect_ids))
    return unknown, required, blind, duplicates, len(effect_ids)


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
    _require(isinstance(h8.get("api_http_projection"), dict) and h8["api_http_projection"].get("readiness", {}).get("status") == "ready", "H8 runtime readiness projection missing")
    _require(h8["api_http_projection"].get("version", {}).get("source_sha") == source_sha, "H8 API source identity missing")
    _require(isinstance(_stage(data, "H8_REBUILD_FROM_ZERO")["observed_inputs"].get("seed_sha256"), str), "H8 raw seed observation missing")
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
    before = h11.get("process_identity_before")
    after = h11.get("process_identity_after")
    _require(isinstance(before, dict) and isinstance(after, dict), "restart provenance missing")
    _require(isinstance(before.get("pid"), int) and isinstance(after.get("pid"), int) and before["pid"] != after["pid"], "restart identity proof missing")
    _require(h11.get("readiness_recovered") is True and h11.get("source_sha_unchanged") is True, "restart state proof missing")
    _require(h11.get("old_process_gone") is True and h11.get("providers_disabled") is True, "API process proof incomplete")
    _require(isinstance(h11.get("http_after"), dict) and h11["http_after"].get("version", {}).get("source_sha") == source_sha, "API HTTP provenance missing")
    for identity in (before, after):
        _require("mayak.runtime.api" in identity.get("argv", []) and "python -c" not in " ".join(identity.get("argv", [])), "generic API process rejected")
    h12 = _stage(data, "H12_WORKER_INTERRUPTION_RESTART")["observed_outputs"]
    for key in ("one_logical_work_item", "lease_recovery_persisted", "recovery_completed", "duplicate_effect", "live_provider_calls"):
        _require(key in h12, f"H12 observation missing: {key}")
    _require(all(isinstance(h12.get(key), dict) for key in ("before", "after")), "H12 persisted transition missing")
    _require(h12["live_provider_calls"] == 0 and h12["duplicate_effect"] is False, "H12 unsafe effect")
    h12_in = _stage(data, "H12_WORKER_INTERRUPTION_RESTART")["observed_inputs"]
    _require(isinstance(h12_in.get("worker_pids"), list) and len(set(h12_in["worker_pids"])) == 2, "H12 worker process provenance missing")
    _require(h12.get("recovery_completed") is True and h12["before"] != h12["after"], "H12 persisted transition missing")
    h13 = _stage(data, "H13_SCHEDULER_RESTART")["observed_outputs"]
    _require(isinstance(h13.get("scheduler_before"), dict) and isinstance(h13.get("scheduler_after"), dict), "H13 process provenance missing")
    _require(h13["scheduler_before"].get("pid") != h13["scheduler_after"].get("pid"), "H13 process restart proof incomplete")
    _require("mayak.runtime.scheduler" in h13["scheduler_before"].get("argv", []) and "mayak.runtime.scheduler" in h13["scheduler_after"].get("argv", []), "scheduler command provenance missing")
    _require(h13.get("durable_before") != h13.get("durable_after"), "H13 durable transition missing")
    derived_h13 = _derive_duplicate_count(h13.get("raw_durable_observations", {}))
    _require(derived_h13 == 0, "H13 duplicate scheduling derived from durable IDs")
    if "duplicate_scheduling" in h13:
        _require(h13["duplicate_scheduling"] == derived_h13, "H13 convenience result disagrees with raw derivation")
    h14 = _stage(data, "H14_INTERRUPTED_MIGRATION")["observed_outputs"]
    for key in ("interrupted_revision", "recovered_revision", "readiness_did_not_pass", "readiness_recovered", "interruption_hook", "database_revision_observed", "recovery_head"):
        _require(key in h14, f"H14 observation missing: {key}")
    _require("RF26 deterministic interruption" in str(h14["interruption_hook"]), "H14 deterministic hook identity missing")
    _require(h14["readiness_did_not_pass"] is True and h14["readiness_recovered"] is True, "H14 readiness proof incomplete")
    _require(h14.get("database_revision_observed") == h14.get("interrupted_revision", {}).get("revision") and h14.get("interrupted_revision") != h14.get("recovered_revision"), "H14 database observation missing")
    _require(h14.get("interrupted_revision_is_head") is False and h14.get("recovered_revision") == h14.get("recovery_head"), "H14 exact head recovery missing")
    h15 = _stage(data, "H15_OUTBOX_RECONCILIATION")["observed_outputs"]
    for key in ("raw_persistence_boundaries", "reconciliation_evidence", "provider_live_calls", "provider_observations"):
        _require(key in h15, f"H15 raw observation missing: {key}")
    unknown, required, blind, duplicates, _ = _derive_h15(h15["raw_persistence_boundaries"])
    _require(unknown and required and blind == 0 and duplicates == 0 and h15["provider_live_calls"] == 0, "H15 unsafe derived reconciliation")
    providers = h15["provider_observations"]
    _require(isinstance(providers, list), "H15 provider observations malformed")
    provider_ids = [str(item.get("attempt_id")) for item in providers if isinstance(item, dict) and item.get("attempt_id")]
    _require(len(provider_ids) == len(set(provider_ids)), "H15 duplicate provider effect identity")
    _require(h15.get("before") != h15.get("after"), "H15 persisted transition missing")
    for key, derived in (("effect_unknown_until_reconciled", unknown), ("reconciliation_required", required), ("blind_retry_count", blind), ("duplicate_external_effect", duplicates)):
        if key in h15:
            _require(h15[key] == derived, f"H15 convenience result disagrees: {key}")
    h16 = _stage(data, "H16_RETENTION_RPO_RTO")["observed_outputs"]
    _require(set(h16.get("deleted", [])) == {"expired-verified-inactive"}, "retention deletion classification invalid")
    _require(set(h16.get("preserved", [])) == {"current", "active", "malformed", "tampered", "unverified", "unknown", "symlink"}, "retention preservation classification invalid")
    _require(isinstance(h16.get("filesystem_before"), list) and isinstance(h16.get("filesystem_after"), list), "retention filesystem snapshots missing")
    _require(set(h16["filesystem_before"]) - set(h16["filesystem_after"]) == set(h16.get("deleted", [])), "retention deletion is not filesystem-derived")
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
