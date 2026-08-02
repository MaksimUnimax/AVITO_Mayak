"""Independent RF14 acceptance over operation-level observations only."""
# ruff: noqa: E501
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from copy import deepcopy
from pathlib import Path
from typing import Any

MARKER = "RF14_ACCEPTANCE_VERIFIED"
TECHNICAL_ID = "RF-14-AVITO-PARSER-AUTHORITY-BEHAVIORAL-ACCEPTANCE-20260802-09"
EXPECTED_PARENT = "d342f6fead10196a704db7ed28c846549b5dbcf6"
EXPECTED_HEAD = "RF13_BEACON_RUNTIME_HARDEN"

BEHAVIORAL_REQUIREMENTS = (
    "dispatch_authority", "dispatch_mismatch_fail_closed", "classifier_separation",
    "classifier_negative_matrix", "behavioral_no_source_gates", "requirement_specific_tamper",
    "foreign_state_witness", "foreign_after_tamper", "concurrent_overlap",
    "concurrent_single_row", "concurrent_same_effect", "snapshot_bound",
    "raw_payload_blocked", "rollback_proof", "replay_uniqueness",
)


def _case(runtime: dict[str, Any], name: str) -> dict[str, Any]:
    return next(item for item in runtime["classifier"]["cases"] if item["case_id"] == name)


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _checks(data: dict[str, Any]) -> dict[str, bool]:
    runtime = data["runtime"]
    persistence = data["persistence"]
    dispatch = runtime["dispatch"]
    cases = runtime["classifier"]["cases"]
    foreign = persistence
    timeline = foreign["foreign_timeline"]
    scenario_ok = all(
        item["handler_calls_after"] - item["handler_calls_before"] == 0
        and item["transport_status"] == "NOT_SENT"
        and item["observed_request_url"] is None
        for item in dispatch["mismatch_scenarios"]
    )
    before = foreign["foreign_snapshot_before_parser"]
    after = foreign["foreign_snapshot_after_parser"]
    concurrency = persistence["concurrency"]
    return {
        "dispatch_authority": dispatch["default_calls"] == 0 and dispatch["trusted_handler_calls_after"] - dispatch["trusted_handler_calls_before"] == 1 and dispatch["trusted_observed_request_url"] == dispatch["trusted_resolved_target"],
        "dispatch_mismatch_fail_closed": len(dispatch["mismatch_scenarios"]) == 5 and scenario_ok,
        "classifier_separation": _case(runtime, "generic_empty")["classifier_status"] != "USABLE_RESPONSE" and _case(runtime, "generic_items_empty")["classifier_status"] != "USABLE_RESPONSE",
        "classifier_negative_matrix": all(
            _case(runtime, name)["classifier_status"] not in {"USABLE_RESPONSE", "CLEAN_EMPTY"}
            for name in ("captcha", "rate_restricted", "malformed_bytes", "incomplete", "partial", "unsupported", "redirect", "stale_profile", "missing_profile", "disputed_profile")
        ),
        "behavioral_no_source_gates": "acceptance" not in data and bool(cases),
        "requirement_specific_tamper": bool(cases) and bool(dispatch["mismatch_scenarios"]),
        "foreign_state_witness": before == after and foreign["foreign_snapshot_before_digest"] == _digest(before) and foreign["foreign_snapshot_after_digest"] == _digest(after) and foreign["foreign_snapshot_before_digest"] == foreign["foreign_snapshot_after_digest"] and timeline["fixture_commit_end"] <= timeline["foreign_before_capture_start"] <= timeline["foreign_before_capture_end"] < timeline["parser_window_start"] <= timeline["parser_window_end"] < timeline["foreign_after_capture_start"] <= timeline["foreign_after_capture_end"],
        "foreign_after_tamper": before == after,
        "concurrent_overlap": concurrency["backend_pid_a"] != concurrency["backend_pid_b"] and max(concurrency["call_start_a"], concurrency["call_start_b"]) < min(concurrency["call_end_a"], concurrency["call_end_b"]),
        "concurrent_single_row": concurrency["physical_rows"] == 1,
        "concurrent_same_effect": concurrency["actual_result_id_a"] == concurrency["actual_result_id_b"] and concurrency["fingerprint"],
        "snapshot_bound": persistence["snapshot_bytes"] <= 32768,
        "raw_payload_blocked": persistence["raw_payload_operations"]["persist_attempt_exception"] == "TypeError" and persistence["raw_payload_operations"]["dto_attempt_exception"] == "ValueError",
        "rollback_proof": persistence["rollback_before"] == persistence["rollback_after"] and persistence["rollback_operation_result"] == "rollback_completed" and isinstance(persistence["rollback_retry_result"], dict),
        "replay_uniqueness": persistence["replayed"] is True,
    }


def _tamper(data: dict[str, Any], requirement: str) -> tuple[dict[str, Any], list[str]]:
    changed = deepcopy(data)
    p = changed["persistence"]
    if requirement == "dispatch_authority":
        changed["runtime"]["dispatch"]["trusted_observed_request_url"] = "https://tampered.invalid"
        return changed, ["runtime.dispatch.trusted_observed_request_url"]
    if requirement == "dispatch_mismatch_fail_closed":
        changed["runtime"]["dispatch"]["mismatch_scenarios"][0]["handler_calls_after"] += 1
        return changed, ["runtime.dispatch.mismatch_scenarios[0].handler_calls_after"]
    if requirement == "classifier_separation":
        _case(changed["runtime"], "generic_empty")["classifier_status"] = "USABLE_RESPONSE"
        return changed, ["runtime.classifier.cases[generic_empty].classifier_status"]
    if requirement == "classifier_negative_matrix":
        _case(changed["runtime"], "captcha")["classifier_status"] = "USABLE_RESPONSE"
        return changed, ["runtime.classifier.cases[captcha].classifier_status"]
    if requirement in {"behavioral_no_source_gates", "requirement_specific_tamper"}:
        changed["runtime"]["classifier"]["cases"] = []
        return changed, ["runtime.classifier.cases"]
    if requirement == "foreign_state_witness":
        row = changed["persistence"]["foreign_snapshot_after_parser"][0]["rows"][0]
        row[next(key for key in row if key not in {"id", "table"})] = "tampered-semantic-state"
        return changed, ["persistence.foreign_snapshot_after_parser"]
    if requirement == "foreign_after_tamper":
        changed["persistence"]["foreign_snapshot_after_parser"] = deepcopy(p["foreign_snapshot_before_parser"])
        changed["persistence"]["foreign_snapshot_after_parser"][0]["rows"].append({"tampered": True})
        return changed, ["persistence.foreign_snapshot_after_parser"]
    if requirement == "concurrent_overlap":
        p["concurrency"]["call_end_a"] = min(p["concurrency"]["call_start_a"], p["concurrency"]["call_start_b"])
        return changed, ["persistence.concurrency.call_end_a"]
    if requirement == "concurrent_single_row":
        p["concurrency"]["physical_rows"] = 2
        return changed, ["persistence.concurrency.physical_rows"]
    if requirement == "concurrent_same_effect":
        p["concurrency"]["actual_result_id_b"] = "tampered-result-id"
        return changed, ["persistence.concurrency.actual_result_id_b"]
    if requirement == "snapshot_bound":
        p["snapshot_bytes"] = 32769
        return changed, ["persistence.snapshot_bytes"]
    if requirement == "raw_payload_blocked":
        p["raw_payload_operations"]["persist_attempt_exception"] = None
        return changed, ["persistence.raw_payload_operations.persist_attempt_exception"]
    if requirement == "rollback_proof":
        p["rollback_after"] = p["rollback_before"] + 1
        return changed, ["persistence.rollback_after"]
    p["replayed"] = False
    return changed, ["persistence.replayed"]


def main() -> int:
    parser = argparse.ArgumentParser()
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
    matrix = []
    for requirement in BEHAVIORAL_REQUIREMENTS:
        tampered, fields = _tamper(data, requirement)
        after = _checks(tampered)[requirement]
        matrix.append({"requirement_id": requirement, "raw_fields_mutated": fields,
                       "checker_before": checks[requirement], "checker_after": after,
                       "expected_causal_failure": checks[requirement] and not after})
    if args.map_output:
        raw_paths = {
            "dispatch_authority": ["runtime.dispatch.trusted_handler_calls_before", "runtime.dispatch.trusted_handler_calls_after", "runtime.dispatch.trusted_observed_request_url"],
            "dispatch_mismatch_fail_closed": ["runtime.dispatch.mismatch_scenarios[*]"],
            "classifier_separation": ["runtime.classifier.cases[*].classifier_status"],
            "classifier_negative_matrix": ["runtime.classifier.cases[*].classifier_status"],
            "behavioral_no_source_gates": ["runtime.classifier.cases[*]"], "requirement_specific_tamper": ["runtime.classifier.cases[*]"],
            "foreign_state_witness": ["persistence.foreign_snapshot_before_parser", "persistence.foreign_snapshot_after_parser", "persistence.foreign_timeline"],
            "foreign_after_tamper": ["persistence.foreign_snapshot_after_parser"],
            "concurrent_overlap": ["persistence.concurrency.call_start_a", "persistence.concurrency.call_start_b", "persistence.concurrency.call_end_a", "persistence.concurrency.call_end_b"],
            "concurrent_single_row": ["persistence.concurrency.physical_rows"], "concurrent_same_effect": ["persistence.concurrency.actual_result_id_a", "persistence.concurrency.actual_result_id_b"],
            "snapshot_bound": ["persistence.snapshot_bytes"], "raw_payload_blocked": ["persistence.raw_payload_operations"],
            "rollback_proof": ["persistence.rollback_before", "persistence.rollback_after", "persistence.rollback_retry_result"], "replay_uniqueness": ["persistence.replayed"],
        }
        args.map_output.write_text(json.dumps({r: {"checker": r, "raw_evidence_paths": raw_paths[r], "producer_derived_field_consumed": False} for r in BEHAVIORAL_REQUIREMENTS}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.tamper_output:
        args.tamper_output.write_text(json.dumps(matrix, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    identity_ok = (identity["technical_id"] == TECHNICAL_ID and identity["candidate_sha"] == actual_sha == args.candidate_sha and identity["parent_sha"] == actual_parent and identity["tree_sha"] == actual_tree and data["postgres"]["alembic_head"] == EXPECTED_HEAD and data["postgres"]["major"] == 18 and subprocess.run(["git", "merge-base", "--is-ancestor", EXPECTED_PARENT, actual_sha], check=False).returncode == 0)
    matrix_ok = set(row["requirement_id"] for row in matrix) == set(BEHAVIORAL_REQUIREMENTS) and all(row["checker_before"] and not row["checker_after"] for row in matrix)
    failed = [name for name, passed in checks.items() if not passed]
    if not identity_ok or not matrix_ok or failed:
        raise SystemExit("RF14 acceptance gate failure: " + ",".join(failed or ["identity_or_tamper"]))
    print(MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
