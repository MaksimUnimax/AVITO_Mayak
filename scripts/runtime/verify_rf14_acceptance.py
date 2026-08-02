"""Independent RF14 verifier.

The producer supplies measured raw observations only.  This verifier contains
the requirement map and derives every decision from the mapped evidence; it
does not inspect implementation source as behavioural proof.
"""
# ruff: noqa: E501
from __future__ import annotations

import argparse
import json
import subprocess
from copy import deepcopy
from pathlib import Path
from typing import Any

MARKER = "RF14_ACCEPTANCE_VERIFIED"
TECHNICAL_ID = "RF-14-AVITO-PARSER-AUTHORITY-BEHAVIORAL-ACCEPTANCE-20260802-09"
EXPECTED_PARENT = "d342f6fead10196a704db7ed28c846549b5dbcf6"
EXPECTED_HEAD = "RF13_BEACON_RUNTIME_HARDEN"

REQUIREMENTS: dict[str, tuple[str, str]] = {
    "dispatch_authority": ("runtime.dispatch", "default_calls"),
    "dispatch_mismatch_fail_closed": ("runtime.dispatch", "mismatch_calls"),
    "classifier_separation": ("runtime.classifier", "generic_empty"),
    "classifier_negative_matrix": ("runtime.classifier", "negative_outcomes"),
    "behavioral_no_source_gates": ("runtime.acceptance", "source_text_gate_count"),
    "requirement_specific_tamper": ("runtime.acceptance", "tamper_coverage"),
    "foreign_state_witness": ("persistence.foreign", "semantic_equal"),
    "foreign_after_tamper": ("persistence.foreign", "tamper_rejected"),
    "concurrent_overlap": ("persistence.concurrency", "overlap"),
    "concurrent_single_row": ("persistence.concurrency", "physical_rows"),
    "concurrent_same_effect": ("persistence.concurrency", "same_effect"),
    "snapshot_bound": ("persistence", "snapshot_bytes"),
    "raw_payload_blocked": ("persistence", "raw_payload_rejected"),
    "rollback_proof": ("persistence", "rollback_proven"),
    "replay_uniqueness": ("persistence", "replayed"),
}


def _lookup(data: dict[str, Any], path: str, field: str) -> Any:
    current: Any = data
    for part in path.split("."):
        current = current[part]
    return current[field]


def _checks(data: dict[str, Any]) -> dict[str, bool]:
    runtime = data["runtime"]
    persistence = data["persistence"]
    dispatch = runtime["dispatch"]
    classifier = runtime["classifier"]
    acceptance = runtime["acceptance"]
    foreign = persistence["foreign"]
    concurrency = persistence["concurrency"]
    return {
        "dispatch_authority": dispatch["default_calls"] == 0 and dispatch["trusted_target_calls"] == 1,
        "dispatch_mismatch_fail_closed": all(value == 0 for value in dispatch["mismatch_calls"].values()),
        "classifier_separation": classifier["generic_empty"] != "USABLE_RESPONSE" and classifier["body_empty_proof"] != "USABLE_RESPONSE",
        "classifier_negative_matrix": all(value not in {"USABLE_RESPONSE", "CLEAN_EMPTY"} for value in classifier["negative_outcomes"].values()),
        "behavioral_no_source_gates": acceptance["source_text_gate_count"] == 0,
        "requirement_specific_tamper": acceptance["tamper_coverage"] == sorted(REQUIREMENTS),
        "foreign_state_witness": foreign["semantic_equal"] and foreign["baseline_after_fixtures_before_parser"] and foreign["after_parser"],
        "foreign_after_tamper": foreign["tamper_rejected"],
        "concurrent_overlap": concurrency["overlap"] and max(concurrency["call_start_a"], concurrency["call_start_b"]) < min(concurrency["call_end_a"], concurrency["call_end_b"]),
        "concurrent_single_row": concurrency["physical_rows"] == 1,
        "concurrent_same_effect": concurrency["same_effect"],
        "snapshot_bound": persistence["snapshot_bytes"] <= 32768,
        "raw_payload_blocked": persistence["raw_payload_rejected"],
        "rollback_proof": persistence["rollback_proven"],
        "replay_uniqueness": persistence["replayed"],
    }


def _tamper_matrix(data: dict[str, Any], checks: dict[str, bool]) -> list[dict[str, Any]]:
    rows = []
    for requirement_id, (path, field) in REQUIREMENTS.items():
        tampered = deepcopy(data)
        target: Any = tampered
        for part in path.split("."):
            target = target[part]
        original = target[field]
        if requirement_id == "classifier_separation":
            target[field] = "USABLE_RESPONSE"
        elif requirement_id == "classifier_negative_matrix":
            target[field] = dict(original)
            first_key = next(iter(target[field]))
            target[field][first_key] = "USABLE_RESPONSE"
        elif requirement_id == "snapshot_bound":
            target[field] = 32769
        elif isinstance(original, bool):
            target[field] = not original
        elif isinstance(original, int):
            target[field] = original + 1
        elif isinstance(original, list):
            target[field] = []
        elif isinstance(original, dict):
            target[field] = dict(original)
            if target[field]:
                first_key = next(iter(target[field]))
                target[field][first_key] = 1
            else:
                target[field]["tampered"] = 1
        else:
            target[field] = "tampered"
        after = _checks(tampered)[requirement_id]
        rows.append({"requirement_id": requirement_id, "raw_field": f"{path}.{field}",
                     "original": original, "tampered": target[field],
                     "checker_before": checks[requirement_id], "checker_after": after,
                     "expected_causal_failure": not after})
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("observations", type=Path)
    parser.add_argument("candidate_sha")
    parser.add_argument("--tamper-output", type=Path)
    parser.add_argument("--map-output", type=Path)
    args = parser.parse_args()
    data = json.loads(args.observations.read_text(encoding="utf-8"))
    actual_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    actual_parent = subprocess.check_output(["git", "rev-parse", "HEAD^"], text=True).strip()
    actual_tree = subprocess.check_output(["git", "rev-parse", "HEAD^{tree}"], text=True).strip()
    identity = data["identity"]
    checks = _checks(data)
    matrix = _tamper_matrix(data, checks)
    if args.map_output:
        args.map_output.write_text(json.dumps({
            requirement_id: {"evidence_path": f"{path}.{field}", "checker": requirement_id}
            for requirement_id, (path, field) in REQUIREMENTS.items()
        }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.tamper_output:
        args.tamper_output.write_text(json.dumps(matrix, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    identity_ok = (identity["technical_id"] == TECHNICAL_ID and identity["candidate_sha"] == actual_sha == args.candidate_sha
                   and actual_parent == EXPECTED_PARENT and identity["parent_sha"] == EXPECTED_PARENT
                   and identity["tree_sha"] == actual_tree and data["postgres"]["alembic_head"] == EXPECTED_HEAD
                   and data["postgres"]["major"] == 18)
    matrix_ok = len(matrix) == len(REQUIREMENTS) and all(row["expected_causal_failure"] for row in matrix)
    failed = [name for name, passed in checks.items() if not passed]
    if not identity_ok or not matrix_ok or failed:
        raise SystemExit("RF14 acceptance gate failure: " + ",".join(failed or (["identity_or_tamper"] if not (identity_ok and matrix_ok) else [])))
    print(MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
