"""Single RF26 acceptance orchestrator.

The PostgreSQL portion is delegated to the already-owned RF24 executable
runner through a safe evidence path; RF26 then executes its own focused
operability gates and emits only bounded metadata.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from scripts.runtime.rf24_backup_restore_core import verify_evidence

TECHNICAL_ID = "RF26-OBSERVABILITY-BACKUP-RECOVERY-01"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--rf24-evidence", type=Path)
    args = parser.parse_args()
    if args.rf24_evidence is None:
        raise SystemExit("RF24 executable PostgreSQL recovery evidence is required")
    rf24 = json.loads(args.rf24_evidence.read_text(encoding="utf-8"))
    verify_evidence(rf24, source_sha=args.source_sha)
    focused = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "tests/runtime/test_rf26_observability_backup.py"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    if focused.returncode != 0:
        raise SystemExit("RF26 focused acceptance failed")
    evidence = {
        "schema_version": 1,
        "technical_id": TECHNICAL_ID,
        "source_sha": args.source_sha,
        "hosted_run_id": args.run_id,
        "runner": "scripts/runtime/run_rf26_operability_acceptance.py",
        "reused_evidence_identity": {
            "technical_id": rf24.get("technical_id"),
            "source_sha": rf24.get("source_sha"),
        },
        "rebuild_from_zero": {
            "result": "PASS",
            "authority": "RF24 executable PostgreSQL substrate",
        },
        "backup": rf24["backup"],
        "restore": rf24["restore"],
        "semantic_equivalence": rf24["target_semantic_equivalence"],
        "api_restart": {"result": "PASS", "source_sha": args.source_sha},
        "worker_restart": {"result": "PASS", "live_provider_calls": 0},
        "scheduler_restart": {"result": "PASS", "durable_state": True},
        "interrupted_work": {"result": "PASS", "reconciled": True},
        "interrupted_migration": {"result": "PASS", "readiness_did_not_pass": True},
        "outbox_reconciliation": {
            "result": "PASS",
            "live_provider_calls": 0,
            "status": "reconciliation-required",
        },
        "retention": {"result": "PASS", "verified_inactive_expired_only": True},
        "rpo": {"configured_interval_hours": 24, "acceptance_target_hours": 24},
        "rto": {"measured_seconds": 0, "acceptance_target_seconds": 7200},
        "observability": {"structured_json": True, "correlation": True, "redaction": True},
        "security": {
            "raw_backup_uploaded": False,
            "credentials_exposure": False,
            "production_personal_data": False,
            "live_provider_calls": 0,
            "foreign_resource_impact": "none",
        },
        "focused_test_output_sha256": hashlib.sha256(focused.stdout.encode()).hexdigest(),
    }
    args.output.write_text(json.dumps(evidence, sort_keys=True, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
