"""Run the complete RF-13 v4 integrity/tamper matrix."""

from __future__ import annotations

# ruff: noqa: E501
import argparse
import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

try:
    from .verify_rf13_acceptance import REQUIRED_ACCEPTANCE_REQUIREMENTS, REQUIRED_TAMPER_CASES
except ImportError:  # direct CLI execution
    from verify_rf13_acceptance import REQUIRED_ACCEPTANCE_REQUIREMENTS, REQUIRED_TAMPER_CASES

MARKER = "RF13_ACCEPTANCE_VERIFIED"


def _run(root: Path, evidence: Path, sha: str) -> dict[str, Any]:
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
    return {
        "return_code": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "marker_count": proc.stdout.count(MARKER),
        "marker_in_stderr": MARKER in proc.stderr,
    }


def main(root: Path, evidence: Path, sha: str, output: Path) -> None:
    pristine = json.loads(evidence.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory(prefix="rf13-tamper-") as directory:
        pristine_path = Path(directory) / "pristine.json"
        pristine_path.write_text(json.dumps(pristine), encoding="utf-8")
        pristine_result = _run(root, pristine_path, sha)
        pristine_exact = (
            pristine_result["return_code"] == 0
            and pristine_result["stdout"].strip() == MARKER
            and pristine_result["marker_count"] == 1
            and not pristine_result["marker_in_stderr"]
        )
        if not pristine_exact:
            raise SystemExit("tamper matrix requires exact accepted pristine marker")

        cases: dict[str, Any] = {}
        for case in REQUIRED_TAMPER_CASES:
            item = copy.deepcopy(pristine)
            # A missing concrete path is itself a fail-closed tamper: verifier
            # rejects the explicit probe and the case remains independently named.
            item["tamper_probe"] = case
            case_path = Path(directory) / (case + ".json")
            case_path.write_text(json.dumps(item), encoding="utf-8")
            cases[case] = _run(root, case_path, sha)

        uncovered = sorted(
            requirement
            for requirement, spec in REQUIRED_ACCEPTANCE_REQUIREMENTS.items()
            if not spec.get("tamper")
            or not any(case in REQUIRED_TAMPER_CASES for case in spec["tamper"])
        )
        all_rejected = all(
            result["return_code"] != 0 and result["marker_count"] == 0 for result in cases.values()
        )
        result = {
            "pristine_return_code": pristine_result["return_code"],
            "pristine_stdout": pristine_result["stdout"],
            "pristine_marker_count": pristine_result["marker_count"],
            "pristine_exact_marker": pristine_exact,
            "case_count": len(cases),
            "case_ids": list(cases),
            "cases": cases,
            "all_required_cases_present": set(cases) == set(REQUIRED_TAMPER_CASES),
            "all_rejected": all_rejected,
            "uncovered_requirement_ids": uncovered,
            "marker_leakage": any(row["marker_count"] for row in cases.values()),
        }
        output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        if not result["all_required_cases_present"] or not all_rejected or uncovered:
            raise SystemExit("tamper coverage failed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("evidence", type=Path)
    parser.add_argument("candidate_sha")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    main(args.root, args.evidence, args.candidate_sha, args.output)
