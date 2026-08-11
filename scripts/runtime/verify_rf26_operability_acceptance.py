"""Fail-closed verifier for the safe RF26 acceptance projection."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--result", type=Path, required=True)
    args = parser.parse_args()
    data = json.loads(args.evidence.read_text(encoding="utf-8"))
    if (
        data.get("technical_id") != "RF26-OBSERVABILITY-BACKUP-RECOVERY-01"
        or data.get("source_sha") != args.source_sha
        or data.get("hosted_run_id") != args.run_id
    ):
        raise SystemExit("RF26 evidence identity mismatch")
    required = (
        "rebuild_from_zero",
        "backup",
        "restore",
        "semantic_equivalence",
        "api_restart",
        "worker_restart",
        "scheduler_restart",
        "interrupted_work",
        "interrupted_migration",
        "outbox_reconciliation",
        "retention",
        "rpo",
        "rto",
        "observability",
        "security",
    )
    if any(key not in data for key in required):
        raise SystemExit("RF26 evidence scenario missing")
    if any(isinstance(data[key], dict) and data[key].get("result") == "FAIL" for key in required):
        raise SystemExit("RF26 scenario failed")
    security = data["security"]
    if security != {
        "raw_backup_uploaded": False,
        "credentials_exposure": False,
        "production_personal_data": False,
        "live_provider_calls": 0,
        "foreign_resource_impact": "none",
    }:
        raise SystemExit("RF26 security invariant failed")
    result = {
        "technical_id": data["technical_id"],
        "source_sha": args.source_sha,
        "hosted_run_id": args.run_id,
        "verdict": "PASS",
        "evidence_sha256": hashlib.sha256(args.evidence.read_bytes()).hexdigest(),
    }
    args.result.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
