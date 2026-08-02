"""Independent fail-closed RF-13 evidence verifier."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

MARKER = "RF13_ACCEPTANCE_VERIFIED"
TECHNICAL_ID = "RF-13-BEACON-MANAGEMENT-RUNTIME-POSTGRES-20260802-01"
HEAD = "RF13_BEACON_RUNTIME"


def verify(root: Path, evidence: Path, candidate_sha: str) -> None:
    item = json.loads(evidence.read_text(encoding="utf-8"))
    actual_sha = subprocess.check_output(("git", "rev-parse", "HEAD"), cwd=root, text=True).strip()
    actual_tree = subprocess.check_output(
        ("git", "rev-parse", "HEAD^{tree}"), cwd=root, text=True
    ).strip()
    if (
        item.get("technical_id") != TECHNICAL_ID
        or item.get("candidate_sha") != candidate_sha
        or candidate_sha != actual_sha
    ):
        raise SystemExit("RF13 candidate identity failed")
    if item.get("candidate_tree") != actual_tree or item.get("alembic_head") != HEAD:
        raise SystemExit("RF13 tree/head evidence failed")
    if (
        item.get("prior_main_parent")
        != subprocess.check_output(("git", "rev-parse", "HEAD^"), cwd=root, text=True).strip()
    ):
        raise SystemExit("RF13 parent evidence failed")
    if (
        item.get("python") != "3.14.6"
        or item.get("uv") != "0.11.31"
        or item.get("postgres_major") != 18
    ):
        raise SystemExit("RF13 toolchain/PostgreSQL evidence failed")
    if item.get("lock_identity") != hashlib.sha256((root / "uv.lock").read_bytes()).hexdigest():
        raise SystemExit("RF13 lock identity failed")
    required = {
        "beacon_beacons",
        "beacon_configuration_revisions",
        "beacon_filter_overrides",
        "beacon_lifecycle_events",
    }
    if not required.issubset(set(item.get("module04_tables", []))):
        raise SystemExit("RF13 Module04 table evidence failed")
    draft = item.get("required_draft_representation", {})
    if (
        draft.get("source_url_nullable") is not True
        or draft.get("current_revision_nullable") is not True
    ):
        raise SystemExit("RF13 DRAFT representation failed")
    if item.get("synthetic_cleanup") is not True or item.get("credential_exposure") is not False:
        raise SystemExit("RF13 safety evidence failed")
    print(MARKER)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("evidence", type=Path)
    parser.add_argument("candidate_sha")
    args = parser.parse_args()
    verify(args.root, args.evidence, args.candidate_sha)
