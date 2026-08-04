from __future__ import annotations

# ruff: noqa: I001

import copy
import importlib.util
from pathlib import Path


SPEC = importlib.util.spec_from_file_location(
    "rf14_verifier", Path(__file__).parents[2] / "scripts/runtime/verify_rf14_acceptance.py"
)
assert SPEC is not None and SPEC.loader is not None
VERIFIER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFIER)


def _evidence() -> dict:
    cases = [
        {"case_id": "generic_empty", "classifier_status": "EMPTY_RESPONSE"},
        {"case_id": "generic_items_empty", "classifier_status": "EMPTY_RESPONSE"},
        *({"case_id": name, "classifier_status": "REJECTED"} for name in (
            "generic_items_one", "generic_items_empty_proof", "arbitrary_parseable_json",
            "generic_challenge", "syntactically_valid_json_list",
        )),
        *({"case_id": name, "classifier_status": "REJECTED"} for name in (
            "captcha", "rate_restricted", "malformed_bytes", "oversized_body", "incomplete",
            "partial", "unsupported", "redirect", "403", "429", "500", "timeout",
            "network_failure", "stale_profile", "missing_profile", "disputed_profile",
        )),
    ]
    snapshot = [{"table": "identity_accounts", "rows": [{"id": "account-1", "status": "active"}]}]
    timeline = {
        "fixture_commit_end": 1, "foreign_before_capture_start": 2,
        "foreign_before_capture_end": 3, "parser_window_start": 4,
        "parser_window_end": 5, "foreign_after_capture_start": 6,
        "foreign_after_capture_end": 7,
    }
    return {
        "runtime": {
            "dispatch": {
                "default_calls": 0, "trusted_handler_calls_before": 0,
                "trusted_handler_calls_after": 1,
                "trusted_observed_request_url": "https://synthetic.invalid/expected",
                "trusted_resolved_target": "https://synthetic.invalid/expected",
                "mismatch_scenarios": [
                    {
                        "scenario_id": "source_identity_mismatch",
                        "handler_calls_before": 0, "handler_calls_after": 0,
                        "transport_status": "NOT_SENT", "observed_request_url": None,
                        "reason_code": "SOURCE_IDENTITY_MISMATCH",
                        "input_source_reference_id": "input-source",
                        "expected_source_reference_id": "expected-source",
                    },
                    {
                        "scenario_id": "provenance_mismatch",
                        "handler_calls_before": 0, "handler_calls_after": 0,
                        "transport_status": "NOT_SENT", "observed_request_url": None,
                        "reason_code": "PROVENANCE_MISMATCH",
                        "input_provenance_reference": "input-provenance",
                        "expected_provenance_reference": "expected-provenance",
                    },
                    {
                        "scenario_id": "profile_identity_version_mismatch",
                        "handler_calls_before": 0, "handler_calls_after": 0,
                        "transport_status": "NOT_SENT", "observed_request_url": None,
                        "reason_code": "PROFILE_IDENTITY_VERSION_MISMATCH",
                        "input_profile_version": "input-profile",
                        "expected_profile_version": "expected-profile",
                    },
                    {
                        "scenario_id": "authority_proof_mismatch",
                        "handler_calls_before": 0, "handler_calls_after": 0,
                        "transport_status": "NOT_SENT", "observed_request_url": None,
                        "reason_code": "AUTHORITY_IDENTITY_MISMATCH",
                        "attempted_authority_identity": "input-authority",
                        "expected_authority_identity": "expected-authority",
                    },
                    {
                        "scenario_id": "invalid_final_target",
                        "handler_calls_before": 0, "handler_calls_after": 0,
                        "transport_status": "NOT_SENT", "observed_request_url": None,
                        "reason_code": "TRUSTED_TARGET_POLICY_MISMATCH",
                        "attempted_target": "input-target",
                        "expected_target": "expected-target",
                    },
                ],
            },
            "classifier": {"cases": cases},
        },
        "persistence": {
            "foreign_snapshot_before_parser": snapshot,
            "foreign_snapshot_after_parser": copy.deepcopy(snapshot),
            "foreign_snapshot_before_digest": VERIFIER._digest(snapshot),
            "foreign_snapshot_after_digest": VERIFIER._digest(snapshot),
            "foreign_timeline": timeline,
            "concurrency": {
                "backend_pid_a": 10, "backend_pid_b": 11,
                "call_start_a": 10, "call_start_b": 11,
                "call_end_a": 14, "call_end_b": 15,
                "physical_rows": 1, "actual_result_id_a": "outcome-1",
                "actual_result_id_b": "outcome-1", "fingerprint": "fingerprint",
                "replay_a": False, "replay_b": True,
            },
            "snapshot_bytes": 100,
            "raw_payload_operations": {
                "persist_attempt_exception": "TypeError",
                "dto_attempt_exception": "ValueError",
            },
            "rollback_before": 2, "rollback_after": 2,
            "rollback_operation_result": "rollback_completed",
            "rollback_retry_result": {"replayed": False}, "replayed": True,
        },
    }


def test_meta_checks_do_not_mutate_classifier_cases_or_join_behavioral_matrix() -> None:
    evidence = _evidence()
    before = copy.deepcopy(evidence["runtime"]["classifier"]["cases"])

    assert "behavioral_no_source_gates" not in VERIFIER.BEHAVIORAL_CHECKERS
    assert "requirement_specific_tamper" not in VERIFIER.BEHAVIORAL_CHECKERS
    assert VERIFIER.check_registry_coverage(evidence)
    assert VERIFIER.check_verifier_source_independence(evidence)
    assert evidence["runtime"]["classifier"]["cases"] == before


def test_each_target_tamper_is_shape_preserving_and_causally_false() -> None:
    evidence = _evidence()
    for requirement, checker in VERIFIER.BEHAVIORAL_CHECKERS.items():
        assert checker(evidence), requirement
        tampered, fields = VERIFIER.BEHAVIORAL_TAMPERS[requirement](evidence)
        assert fields, requirement
        assert not checker(tampered), requirement
        assert tampered["runtime"]["classifier"]["cases"], requirement


def test_missing_classifier_case_is_controlled_failure() -> None:
    evidence = _evidence()
    evidence["runtime"]["classifier"]["cases"] = [
        case for case in evidence["runtime"]["classifier"]["cases"]
        if case["case_id"] != "generic_empty"
    ]
    passed, error = VERIFIER._safe_check(
        "classifier_separation", VERIFIER.check_classifier_separation, evidence
    )
    assert not passed
    assert error is not None
    assert "generic_empty" in error
