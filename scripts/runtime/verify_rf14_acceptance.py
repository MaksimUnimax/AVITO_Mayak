"""Independent RF14 acceptance over operation-level observations only."""
# ruff: noqa: E501
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from copy import deepcopy
from pathlib import Path
from typing import Any, Callable, NoReturn

MARKER = "RF14_ACCEPTANCE_VERIFIED"
TECHNICAL_ID = "RF-14-AVITO-PARSER-AUTHORITY-BEHAVIORAL-ACCEPTANCE-20260802-09"
EXPECTED_PARENT = "58bb0b8502f02107ed1c67f8bbb4aec036b40c79"
EXPECTED_HEAD = "RF13_BEACON_RUNTIME_HARDEN"

Evidence = dict[str, Any]
Checker = Callable[[Evidence], bool]
Tamper = Callable[[Evidence], tuple[Evidence, list[str]]]


class EvidenceFailure(Exception):
    """An attributed failure caused by missing or malformed acceptance evidence."""


def _require(value: Any, path: str) -> Any:
    if value is None:
        raise EvidenceFailure(f"{path}: missing value")
    return value


def _case(runtime: Evidence, name: str) -> Evidence:
    cases = _require(runtime["classifier"], "runtime.classifier")["cases"]
    for item in _require(cases, "runtime.classifier.cases"):
        if item.get("case_id") == name:
            return item
    raise EvidenceFailure(f"classifier_separation: missing classifier case {name}")


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def check_dispatch_authority(data: Evidence) -> bool:
    dispatch = data["runtime"]["dispatch"]
    return dispatch["default_calls"] == 0 and dispatch["trusted_handler_calls_after"] - dispatch["trusted_handler_calls_before"] == 1 and dispatch["trusted_observed_request_url"] == dispatch["trusted_resolved_target"]


def check_dispatch_mismatch_fail_closed(data: Evidence) -> bool:
    scenarios = data["runtime"]["dispatch"]["mismatch_scenarios"]
    expected = {
        "source_identity_mismatch": ("SOURCE_IDENTITY_MISMATCH", "source"),
        "provenance_mismatch": ("PROVENANCE_MISMATCH", "provenance"),
        "profile_identity_version_mismatch": ("PROFILE_IDENTITY_VERSION_MISMATCH", "profile"),
        "authority_proof_mismatch": ("AUTHORITY_IDENTITY_MISMATCH", "authority"),
        "invalid_final_target": ("TRUSTED_TARGET_POLICY_MISMATCH", "target"),
    }
    if {item["scenario_id"] for item in scenarios} != set(expected):
        return False
    for item in scenarios:
        reason, dimension = expected[item["scenario_id"]]
        if (
            item["handler_calls_after"] - item["handler_calls_before"] != 0
            or item["transport_status"] != "NOT_SENT"
            or item["observed_request_url"] is not None
            or item["reason_code"] != reason
        ):
            return False
        if dimension == "source" and item["input_source_reference_id"] == item["expected_source_reference_id"]:
            return False
        if dimension == "provenance" and item["input_provenance_reference"] == item["expected_provenance_reference"]:
            return False
        if dimension == "profile" and item["input_profile_version"] == item["expected_profile_version"]:
            return False
        if dimension == "authority" and item["attempted_authority_identity"] == item["expected_authority_identity"]:
            return False
        if dimension == "target" and item["attempted_target"] == item["expected_target"]:
            return False
    return True


def check_classifier_separation(data: Evidence) -> bool:
    runtime = data["runtime"]
    forbidden = {"USABLE_RESPONSE", "CLEAN_EMPTY"}
    return all(
        _case(runtime, name)["classifier_status"] not in forbidden
        and _case(runtime, name).get("provider_response_evidence_class") != "EMPTY_WITH_PROOF"
        for name in (
            "generic_empty", "generic_items_empty", "generic_items_one",
            "generic_items_empty_proof", "arbitrary_parseable_json",
            "generic_challenge", "syntactically_valid_json_list",
        )
    )


def check_classifier_negative_matrix(data: Evidence) -> bool:
    runtime = data["runtime"]
    return all(_case(runtime, name)["classifier_status"] not in {"USABLE_RESPONSE", "CLEAN_EMPTY"} for name in ("captcha", "rate_restricted", "malformed_bytes", "oversized_body", "incomplete", "partial", "unsupported", "redirect", "403", "429", "500", "timeout", "network_failure", "stale_profile", "missing_profile", "disputed_profile"))


def check_foreign_state_witness(data: Evidence) -> bool:
    foreign = data["persistence"]
    before = foreign["foreign_snapshot_before_parser"]
    after = foreign["foreign_snapshot_after_parser"]
    timeline = foreign["foreign_timeline"]
    return before == after and foreign["foreign_snapshot_before_digest"] == _digest(before) and foreign["foreign_snapshot_after_digest"] == _digest(after) and foreign["foreign_snapshot_before_digest"] == foreign["foreign_snapshot_after_digest"] and timeline["fixture_commit_end"] <= timeline["foreign_before_capture_start"] <= timeline["foreign_before_capture_end"] < timeline["parser_window_start"] <= timeline["parser_window_end"] < timeline["foreign_after_capture_start"] <= timeline["foreign_after_capture_end"]


def check_concurrent_overlap(data: Evidence) -> bool:
    concurrency = data["persistence"]["concurrency"]
    return concurrency["backend_pid_a"] != concurrency["backend_pid_b"] and max(concurrency["call_start_a"], concurrency["call_start_b"]) < min(concurrency["call_end_a"], concurrency["call_end_b"])


def check_concurrent_single_row(data: Evidence) -> bool:
    return data["persistence"]["concurrency"]["physical_rows"] == 1


def check_concurrent_same_effect(data: Evidence) -> bool:
    concurrency = data["persistence"]["concurrency"]
    return (
        concurrency["actual_result_id_a"] == concurrency["actual_result_id_b"]
        and bool(concurrency["fingerprint"])
        and {concurrency["replay_a"], concurrency["replay_b"]} == {False, True}
    )


def check_snapshot_bound(data: Evidence) -> bool:
    return data["persistence"]["snapshot_bytes"] <= 32768


def check_raw_payload_blocked(data: Evidence) -> bool:
    operations = data["persistence"]["raw_payload_operations"]
    return operations["persist_attempt_exception"] == "TypeError" and operations["dto_attempt_exception"] == "ValueError"


def check_rollback_proof(data: Evidence) -> bool:
    persistence = data["persistence"]
    return persistence["rollback_before"] == persistence["rollback_after"] and persistence["rollback_operation_result"] == "rollback_completed" and isinstance(persistence["rollback_retry_result"], dict)


def check_replay_uniqueness(data: Evidence) -> bool:
    return data["persistence"]["replayed"] is True


BEHAVIORAL_CHECKERS: dict[str, Checker] = {
    "dispatch_authority": check_dispatch_authority,
    "dispatch_mismatch_fail_closed": check_dispatch_mismatch_fail_closed,
    "classifier_separation": check_classifier_separation,
    "classifier_negative_matrix": check_classifier_negative_matrix,
    "foreign_state_witness": check_foreign_state_witness,
    "concurrent_overlap": check_concurrent_overlap,
    "concurrent_single_row": check_concurrent_single_row,
    "concurrent_same_effect": check_concurrent_same_effect,
    "snapshot_bound": check_snapshot_bound,
    "raw_payload_blocked": check_raw_payload_blocked,
    "rollback_proof": check_rollback_proof,
    "replay_uniqueness": check_replay_uniqueness,
}
BEHAVIORAL_REQUIREMENTS = tuple(BEHAVIORAL_CHECKERS)


def _tamper_value(data: Evidence, requirement: str) -> tuple[Evidence, list[str]]:
    changed = deepcopy(data)
    persistence = changed["persistence"]
    if requirement == "dispatch_authority":
        changed["runtime"]["dispatch"]["trusted_observed_request_url"] = "https://tampered.invalid"
        return changed, ["runtime.dispatch.trusted_observed_request_url"]
    if requirement == "dispatch_mismatch_fail_closed":
        changed["runtime"]["dispatch"]["mismatch_scenarios"][0]["handler_calls_after"] += 1
        return changed, ["runtime.dispatch.mismatch_scenarios[0].handler_calls_after"]
    if requirement == "classifier_separation":
        _case(changed["runtime"], "generic_items_one")["classifier_status"] = "USABLE_RESPONSE"
        _case(changed["runtime"], "generic_items_empty_proof")["classifier_status"] = "USABLE_RESPONSE"
        return changed, ["runtime.classifier.cases[generic_items_one].classifier_status", "runtime.classifier.cases[generic_items_empty_proof].classifier_status"]
    if requirement == "classifier_negative_matrix":
        _case(changed["runtime"], "captcha")["classifier_status"] = "USABLE_RESPONSE"
        return changed, ["runtime.classifier.cases[captcha].classifier_status"]
    if requirement == "foreign_state_witness":
        row = persistence["foreign_snapshot_after_parser"][0]["rows"][0]
        semantic_key = next(key for key in row if key not in {"id", "table"})
        row[semantic_key] = "tampered-semantic-state"
        return changed, ["persistence.foreign_snapshot_after_parser[0].rows[0]." + semantic_key]
    if requirement == "concurrent_overlap":
        concurrency = persistence["concurrency"]
        concurrency["call_end_a"] = min(concurrency["call_start_a"], concurrency["call_start_b"])
        return changed, ["persistence.concurrency.call_end_a"]
    if requirement == "concurrent_single_row":
        persistence["concurrency"]["physical_rows"] = 2
        return changed, ["persistence.concurrency.physical_rows"]
    if requirement == "concurrent_same_effect":
        persistence["concurrency"]["actual_result_id_b"] = "tampered-result-id"
        return changed, ["persistence.concurrency.actual_result_id_b"]
    if requirement == "snapshot_bound":
        persistence["snapshot_bytes"] = 32769
        return changed, ["persistence.snapshot_bytes"]
    if requirement == "raw_payload_blocked":
        persistence["raw_payload_operations"]["persist_attempt_exception"] = None
        return changed, ["persistence.raw_payload_operations.persist_attempt_exception"]
    if requirement == "rollback_proof":
        persistence["rollback_after"] = persistence["rollback_before"] + 1
        return changed, ["persistence.rollback_after"]
    persistence["replayed"] = False
    return changed, ["persistence.replayed"]


def _tamper_for(requirement: str) -> Tamper:
    def apply(data: Evidence) -> tuple[Evidence, list[str]]:
        return _tamper_value(data, requirement)

    return apply


BEHAVIORAL_TAMPERS: dict[str, Tamper] = {
    requirement: _tamper_for(requirement) for requirement in BEHAVIORAL_REQUIREMENTS
}


def check_verifier_source_independence(data: Evidence) -> bool:
    del data
    source = Path(__file__).read_text(encoding="utf-8")
    producer_name = "run_rf14_" + "postgres_" + "acceptance.py"
    production_module = "src/" + "mayak/" + "modules/"
    source_gate_name = "production_" + "source"
    return producer_name not in source and production_module not in source and source_gate_name not in source


PRODUCER_DERIVED_FIELDS = ("semantic_equal", "overlap", "same_effect", "rollback_proven", "tamper_coverage", "source_text_gate_count", "final_pass")


def _contains_key(value: object, forbidden: tuple[str, ...]) -> bool:
    if isinstance(value, dict):
        return any(key in forbidden or _contains_key(item, forbidden) for key, item in value.items())
    if isinstance(value, list):
        return any(_contains_key(item, forbidden) for item in value)
    return False


def check_producer_authority_absence(data: Evidence) -> bool:
    return not _contains_key(data, PRODUCER_DERIVED_FIELDS)


def check_registry_coverage(data: Evidence) -> bool:
    del data
    return set(BEHAVIORAL_CHECKERS) == set(BEHAVIORAL_TAMPERS) == set(BEHAVIORAL_REQUIREMENTS)


META_STATIC_ACCEPTANCE_CHECKS: dict[str, Checker] = {
    "behavioral_verifier_source_independence": check_verifier_source_independence,
    "producer_derived_authority_absence": check_producer_authority_absence,
    "behavioral_checker_tamper_coverage": check_registry_coverage,
}


RAW_PATHS = {
    "dispatch_authority": ["runtime.dispatch.trusted_handler_calls_before", "runtime.dispatch.trusted_handler_calls_after", "runtime.dispatch.trusted_observed_request_url"],
    "dispatch_mismatch_fail_closed": ["runtime.dispatch.mismatch_scenarios[*]"],
    "classifier_separation": ["runtime.classifier.cases[generic_empty|generic_items_empty|generic_items_one|generic_items_empty_proof|arbitrary_parseable_json|generic_challenge|syntactically_valid_json_list].classifier_status"],
    "classifier_negative_matrix": ["runtime.classifier.cases[captcha|rate_restricted|malformed_bytes|oversized_body|incomplete|partial|unsupported|redirect|403|429|500|timeout|network_failure|stale_profile|missing_profile|disputed_profile].classifier_status"],
    "foreign_state_witness": ["persistence.foreign_snapshot_before_parser", "persistence.foreign_snapshot_after_parser", "persistence.foreign_timeline"],
    "concurrent_overlap": ["persistence.concurrency.call_start_*", "persistence.concurrency.call_end_*"],
    "concurrent_single_row": ["persistence.concurrency.physical_rows"],
    "concurrent_same_effect": ["persistence.concurrency.actual_result_id_*", "persistence.concurrency.fingerprint"],
    "snapshot_bound": ["persistence.snapshot_bytes"],
    "raw_payload_blocked": ["persistence.raw_payload_operations.persist_attempt_exception", "persistence.raw_payload_operations.dto_attempt_exception"],
    "rollback_proof": ["persistence.rollback_before", "persistence.rollback_after", "persistence.rollback_retry_result"],
    "replay_uniqueness": ["persistence.replayed"],
}


def _safe_check(requirement: str, checker: Checker, data: Evidence) -> tuple[bool, str | None]:
    try:
        return checker(data), None
    except (KeyError, IndexError, TypeError, ValueError, EvidenceFailure, StopIteration) as error:
        return False, f"{requirement}: malformed or missing raw evidence ({error})"


def _fail(message: str) -> NoReturn:
    raise SystemExit("RF14 acceptance gate failure: " + message)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("observations", type=Path)
    parser.add_argument("candidate_sha")
    parser.add_argument("--tamper-output", type=Path)
    parser.add_argument("--map-output", type=Path)
    args = parser.parse_args()
    try:
        data = json.loads(args.observations.read_text(encoding="utf-8"))
        actual_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
        actual_parent = subprocess.check_output(["git", "rev-parse", "HEAD^"], text=True).strip()
        actual_tree = subprocess.check_output(["git", "rev-parse", "HEAD^{tree}"], text=True).strip()
        identity = data["identity"]
        checks: dict[str, bool] = {}
        errors: list[str] = []
        for requirement, checker in BEHAVIORAL_CHECKERS.items():
            checks[requirement], error = _safe_check(requirement, checker, data)
            if error:
                errors.append(error)
        matrix = []
        for requirement, checker in BEHAVIORAL_CHECKERS.items():
            tampered, fields = BEHAVIORAL_TAMPERS[requirement](data)
            after, error = _safe_check(requirement, checker, tampered)
            if error:
                errors.append(error)
            matrix.append({"requirement_id": requirement, "checker": checker.__name__, "tamper": BEHAVIORAL_TAMPERS[requirement].__name__, "raw_fields_mutated": fields, "checker_before": checks[requirement], "checker_after": after, "expected_causal_failure": checks[requirement] and not after})
        meta_results = {}
        for requirement, checker in META_STATIC_ACCEPTANCE_CHECKS.items():
            meta_results[requirement], error = _safe_check(requirement, checker, data)
            if error:
                errors.append(error)
        if args.map_output:
            mapping = {requirement: {"checker": checker.__name__, "raw_evidence_paths": RAW_PATHS[requirement], "tamper": BEHAVIORAL_TAMPERS[requirement].__name__, "producer_derived_field_consumed": False} for requirement, checker in BEHAVIORAL_CHECKERS.items()}
            meta_mapping = {requirement: {"integrity_checker": checker.__name__, "evidence_or_source_of_integrity_proof": "verifier-owned registry/source inspection", "semantic_tamper_required": False} for requirement, checker in META_STATIC_ACCEPTANCE_CHECKS.items()}
            args.map_output.write_text(json.dumps({"behavioral_requirements": mapping, "meta_static_integrity_checks": meta_mapping, "behavioral_requirement_count": len(BEHAVIORAL_CHECKERS)}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if args.tamper_output:
            args.tamper_output.write_text(json.dumps(matrix, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        identity_ok = identity["technical_id"] == TECHNICAL_ID and identity["candidate_sha"] == actual_sha == args.candidate_sha and identity["parent_sha"] == actual_parent and identity["tree_sha"] == actual_tree and data["postgres"]["alembic_head"] == EXPECTED_HEAD and data["postgres"]["major"] == 18 and subprocess.run(["git", "merge-base", "--is-ancestor", EXPECTED_PARENT, actual_sha], check=False).returncode == 0
        matrix_ok = set(row["requirement_id"] for row in matrix) == set(BEHAVIORAL_CHECKERS) and len(matrix) == len(BEHAVIORAL_CHECKERS) and all(row["checker_before"] and not row["checker_after"] and row["expected_causal_failure"] for row in matrix)
        failed = [name for name, passed in checks.items() if not passed] + [name for name, passed in meta_results.items() if not passed]
        if errors or not identity_ok or not matrix_ok or failed:
            _fail(", ".join(errors + failed or ["identity_or_tamper"]))
        print(MARKER)
        return 0
    except SystemExit:
        raise
    except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError, EvidenceFailure) as error:
        _fail(f"evidence: malformed or missing raw evidence ({error})")


if __name__ == "__main__":
    raise SystemExit(main())
