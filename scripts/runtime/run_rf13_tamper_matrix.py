"""RF-13 pristine-first tamper-negative evidence check."""

from __future__ import annotations

import argparse
import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


def _run(root: Path, evidence: Path, sha: str) -> int:
    proc = subprocess.run(
        (
            sys.executable,
            str(root / "scripts/runtime/verify_rf13_acceptance.py"),
            str(root),
            str(evidence),
            sha,
        ),
        capture_output=True,
        text=True,
    )
    return proc.returncode


def main(root: Path, evidence: Path, sha: str, output: Path) -> None:
    pristine = json.loads(evidence.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory(prefix="rf13-tamper-") as directory:
        pristine_path = Path(directory) / "pristine.json"
        pristine_path.write_text(json.dumps(pristine), encoding="utf-8")
        pristine_rc = _run(root, pristine_path, sha)
        pristine_marker = pristine_rc == 0
        if not pristine_marker:
            raise SystemExit("tamper matrix requires accepted pristine evidence")

        cases: dict[str, Any] = {}

        def mutate(case: str, path: tuple[str, ...], value: Any) -> None:
            item = copy.deepcopy(pristine)
            node: Any = item
            for key in path[:-1]:
                node = node[key]
            node[path[-1]] = value
            case_path = Path(directory) / (case + ".json")
            case_path.write_text(json.dumps(item), encoding="utf-8")
            cases[case] = {"return_code": _run(root, case_path, sha)}

        mutate("identity-candidate-sha", ("identity", "candidate_sha"), "0" * 40)
        mutate("identity-tree", ("identity", "candidate_tree"), "0" * 40)
        mutate("identity-parent", ("identity", "parent"), "0" * 40)
        mutate("identity-technical-id", ("identity", "technical_id"), "tampered")
        mutate("identity-schema", ("schema_version",), "rf13-postgres-acceptance-v2")
        mutate("migration-head", ("identity", "alembic_head"), "RF13_BEACON_RUNTIME")
        mutate("patch-sessions", ("patch_lww_concurrency_witness", "sessions"), 1)
        mutate("patch-revisions", ("patch_lww_concurrency_witness", "revision_count"), 1)
        mutate("patch-orphan", ("patch_lww_concurrency_witness", "orphan_revision_count"), 1)
        mutate(
            "idempotency-effects", ("idempotency_concurrency_witness", "business_effect_count"), 2
        )
        mutate(
            "idempotency-terminals", ("idempotency_concurrency_witness", "terminal_record_count"), 2
        )
        mutate("active-final-count", ("active_slot_concurrency_witness", "final_active_count"), 2)
        mutate("rollback-residue", ("rollback_witness", "post_rollback_counts"), {})
        mutate("freeze-actor", ("system_freeze_witness", "actor_account_id"), "owner")
        mutate(
            "history-restorable",
            ("lifecycle_witness", "restore_after_permanent_delete"),
            "ACCEPTED",
        )
        mutate(
            "schema-causation",
            (
                "physical_schema",
                "constraints",
                "ck_beacon_lifecycle_events_actor_causation_pair",
                "definition",
            ),
            "",
        )
        mutate("cleanup-residue", ("cleanup_witness", "synthetic_counts_zero"), False)
        mutate("security-raw-payload", ("security_witness", "raw_provider_payload_persisted"), True)
        all_rejected = all(result["return_code"] != 0 for result in cases.values())
        result = {
            "pristine_accepted": pristine_marker,
            "pristine_return_code": pristine_rc,
            "pristine_marker": pristine_marker,
            "cases": cases,
            "case_count": len(cases),
            "all_rejected": all_rejected,
        }
        output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        if not all_rejected:
            raise SystemExit("tamper mutation accepted")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("evidence", type=Path)
    parser.add_argument("candidate_sha")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    main(args.root, args.evidence, args.candidate_sha, args.output)
