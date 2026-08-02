"""Execute RF-13 v5 semantic tamper mutations and record structural diffs."""

# ruff: noqa

from __future__ import annotations

import argparse
import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).parents[2]))

from scripts.runtime.verify_rf13_acceptance import (
    MARKER,
    REQUIRED_TAMPER_CASES,
    REQUIREMENT_REGISTRY,
    TAMPER_MUTATIONS,
    prepare_verification_context,
    run_requirement_checks,
    verify,
)


def _run(root: Path, evidence: Path, sha: str) -> dict[str, Any]:
    proc = subprocess.run((sys.executable, str(root / "scripts/runtime/verify_rf13_acceptance.py"), str(root), str(evidence), sha), capture_output=True, text=True)
    return {"return_code": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr, "marker_count": proc.stdout.count(MARKER), "marker_in_stderr": MARKER in proc.stderr}


def _diff(before: Any, after: Any, prefix: str = "") -> set[str]:
    if type(before) is not type(after): return {prefix}
    if isinstance(before, dict):
        paths = set()
        for key in set(before) | set(after): paths |= _diff(before.get(key), after.get(key), f"{prefix}.{key}".strip("."))
        return paths
    if isinstance(before, list):
        paths = set()
        for index in range(max(len(before), len(after))): paths |= _diff(before[index] if index < len(before) else None, after[index] if index < len(after) else None, f"{prefix}.{index}".strip("."))
        return paths
    return {prefix} if before != after else set()


def _matches(actual: str, declared: str) -> bool:
    return actual == declared or actual.startswith(declared + ".") or declared.startswith(actual + ".")


def main(root: Path, evidence: Path, sha: str, output: Path) -> None:
    pristine = json.loads(evidence.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory(prefix="rf13-tamper-") as directory:
        pristine_path = Path(directory) / "pristine.json"
        pristine_path.write_text(json.dumps(pristine), encoding="utf-8")
        pristine_result = _run(root, pristine_path, sha)
        pristine_exact = pristine_result["return_code"] == 0 and pristine_result["stdout"].strip() == MARKER and pristine_result["marker_count"] == 1 and not pristine_result["marker_in_stderr"]
        if not pristine_exact: raise SystemExit("tamper matrix requires exact accepted pristine marker")
        cases: dict[str, Any] = {}
        for case in REQUIRED_TAMPER_CASES:
            mutation = TAMPER_MUTATIONS[case]
            mutated = copy.deepcopy(pristine)
            mutation_error = ""
            try:
                mutation.mutate(mutated)
            except Exception as exc:
                mutation_error = f"{type(exc).__name__}: {exc}"
            actual = sorted(_diff(pristine, mutated))
            declared = list(mutation.changed_paths)
            changed_paths_valid = bool(actual) and all(any(_matches(path, prefix) for prefix in declared) for path in actual)
            try:
                context = prepare_verification_context(mutated, root, sha)
                attribution = run_requirement_checks(context)
            except Exception as exc:
                attribution = {requirement: type("Result", (), {"passed": False, "reason": f"{type(exc).__name__}: {exc}"})() for requirement in REQUIREMENT_REGISTRY}
            failed_ids = sorted(requirement for requirement, result in attribution.items() if not result.passed)
            passed_ids = sorted(requirement for requirement, result in attribution.items() if result.passed)
            mapped_ids = list(mutation.requirement_ids)
            mapped_failures = {requirement: attribution[requirement].reason for requirement in mapped_ids if requirement in attribution and not attribution[requirement].passed}
            case_path = Path(directory) / (case + ".json")
            case_path.write_text(json.dumps(mutated), encoding="utf-8")
            result = _run(root, case_path, sha)
            cases[case] = {"case_id": case, "mapped_requirement_ids": mapped_ids, "declared_changed_paths": declared, "actual_changed_paths": actual, "mutation_error": mutation_error, "mutation_effective": bool(actual) and not mutation_error, "changed_paths_valid": changed_paths_valid, "failed_requirement_ids": failed_ids, "passed_requirement_ids": passed_ids, "mapped_requirement_failure": mapped_failures, "verifier_return_code": result["return_code"], "verifier_stdout": result["stdout"], "verifier_stderr": result["stderr"], "marker_count": result["marker_count"], "marker_in_stderr": result["marker_in_stderr"], "rejected": result["return_code"] != 0 and result["marker_count"] == 0 and not result["marker_in_stderr"], "all_mapped_requirements_failed": bool(mapped_ids) and bool(mapped_failures)}
        uncovered = sorted(set(REQUIREMENT_REGISTRY) - {req for mutation in TAMPER_MUTATIONS.values() for req in mutation.requirement_ids})
        unmapped = sorted(set(REQUIRED_TAMPER_CASES) - set(TAMPER_MUTATIONS))
        result = {"pristine_return_code": pristine_result["return_code"], "pristine_stdout": pristine_result["stdout"], "pristine_stderr": pristine_result["stderr"], "pristine_marker_count": pristine_result["marker_count"], "pristine_exact_marker": pristine_exact, "required_case_count": len(REQUIRED_TAMPER_CASES), "executed_case_count": len(cases), "case_ids": list(cases), "cases": cases, "all_required_cases_present": set(cases) == set(REQUIRED_TAMPER_CASES), "all_mutations_effective": all(row["mutation_effective"] for row in cases.values()), "all_changed_paths_valid": all(row["changed_paths_valid"] for row in cases.values()), "all_rejected": all(row["rejected"] for row in cases.values()), "all_mapped_requirement_failures": all(row["all_mapped_requirements_failed"] for row in cases.values()), "uncovered_requirement_ids": uncovered, "unmapped_case_ids": unmapped, "marker_leakage": any(row["marker_count"] or row["marker_in_stderr"] for row in cases.values())}
        output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        failed_cases = [case for case, row in cases.items() if not row["mutation_effective"] or not row["changed_paths_valid"] or not row["rejected"] or not row["all_mapped_requirements_failed"]]
        if failed_cases:
            first = failed_cases[0]
            print(f"::error file=scripts/runtime/run_rf13_tamper_matrix.py::case={first} details={json.dumps(cases[first], sort_keys=True)[:900]}")
        if not result["all_required_cases_present"] or not result["all_mutations_effective"] or not result["all_changed_paths_valid"] or not result["all_rejected"] or not result["all_mapped_requirement_failures"] or uncovered or unmapped or result["marker_leakage"]: raise SystemExit("tamper coverage failed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("root", type=Path); parser.add_argument("evidence", type=Path); parser.add_argument("candidate_sha"); parser.add_argument("output", type=Path)
    args = parser.parse_args(); main(args.root, args.evidence, args.candidate_sha, args.output)
