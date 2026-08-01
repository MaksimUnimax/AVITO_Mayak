"""Fail-closed RF-12 acceptance verifier.

It consumes evidence emitted by the real runner; it never manufactures a
PostgreSQL or concurrency result from source inspection alone.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

EXPECTED_HEAD = "RF12_RUNTIME_HARDEN"
REQUIRED = {
    "empty_to_head", "rf09_to_manual_to_head", "manual_to_head", "metadata_parity",
    "physical_constraints", "command_matrix", "rollback", "concurrency",
    "payment_race", "foreign_equality", "cleanup",
}


def verify(root: Path, evidence_path: Path) -> None:
    if not evidence_path.is_file():
        raise SystemExit("RF12 acceptance evidence is absent")
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    if evidence.get("alembic_head") != EXPECTED_HEAD:
        raise SystemExit("current Alembic head is not RF12_RUNTIME_HARDEN")
    results = evidence.get("gates")
    if not isinstance(results, dict) or REQUIRED - set(results):
        raise SystemExit("RF12 acceptance gate set is incomplete")
    if any(results[name] is not True for name in REQUIRED):
        raise SystemExit("RF12 acceptance contains a failed gate")
    source = (root / "src/mayak/modules/entitlements_and_billing/runtime.py").read_text()
    if "_AUDIT.insert" in source or 'metadata.tables["mayak.platform_audit_entries"]' in source:
        raise SystemExit("direct foreign audit write remains")
    historical = root / "alembic/versions/20260801_RF12_manual_grant_semantics.py"
    historical_sha = hashlib.sha256(historical.read_bytes()).hexdigest()
    if historical_sha != evidence.get("historical_rf12_manual_grant_sha256"):
        raise SystemExit("historical RF12 migration integrity evidence is invalid")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: verify_rf12_acceptance.py ROOT EVIDENCE")
    verify(Path(sys.argv[1]), Path(sys.argv[2]))
