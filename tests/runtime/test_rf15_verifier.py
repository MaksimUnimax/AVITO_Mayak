from __future__ import annotations

import ast
import importlib.util
import inspect
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "rf15_verifier", Path(__file__).parents[2] / "scripts/runtime/verify_rf15_acceptance.py"
)
assert SPEC and SPEC.loader
V = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(V)


def test_registry_has_exactly_29_requirements_and_raw_dependencies() -> None:
    assert len(V.REQUIREMENT_IDS) == 29
    assert set(V.REQUIREMENT_IDS) == set(V.CHECKERS)
    assert set(V.REQUIREMENT_IDS) == set(V.RAW_DEPENDENCY_PATHS)
    assert set(V.REQUIREMENT_IDS) == set(V.TAMPER_PATHS)
    assert all(paths for paths in V.RAW_DEPENDENCY_PATHS.values())


def test_verifier_does_not_depend_on_conclusion_fields() -> None:
    forbidden = {
        "passed",
        "accepted",
        "checker_before",
        "checker_after",
        "requirement_verdict",
        "producer_success",
    }
    assert not any(
        any(token in path.rsplit(".", 1)[-1] for token in forbidden)
        for paths in V.RAW_DEPENDENCY_PATHS.values()
        for path in paths
    )


def test_raw_operation_requires_result_or_exception() -> None:
    with pytest.raises(ValueError):
        V._op(
            {
                "callable": "x",
                "input": {},
                "started_at": "2026-08-02T00:00:00+00:00",
                "finished_at": "2026-08-02T00:00:01+00:00",
                "backend_pid": 1,
            }
        )


def test_list_result_is_raw_success_but_not_a_mapping_contract() -> None:
    operation = {
        "callable": "materialize_due_work",
        "input": {},
        "result": ["work-id"],
        "started_at": "2026-08-02T00:00:00+00:00",
        "finished_at": "2026-08-02T00:00:01+00:00",
        "backend_pid": 1,
    }
    case = {
        "operation": operation,
        "physical_before": V._representative_physical(work=[]),
        "physical_after": V._representative_physical(
            work=[{"id": "w", "state": "DUE", "due_at": "2026-08-02T00:00:00+00:00"}]
        ),
    }
    assert V._success(case, "materialize_due_work")
    assert not V._check("due_work_current_slot", case)


def test_cadence_contract_is_actual_policy() -> None:
    assert V._check(
        "cadence_policy",
        {
            "operation": {
                "callable": "validate_cadence",
                "input": {},
                "result": {"basic": [300, 600], "free": [10800, 21600]},
                "started_at": "2026-08-02T00:00:00+00:00",
                "finished_at": "2026-08-02T00:00:01+00:00",
                "backend_pid": 1,
            },
            "attempts": [
                {
                    "operation": {
                        "callable": "validate_cadence",
                        "input": {},
                        "exception": {"class": "CadenceRejected"},
                        "started_at": "2026-08-02T00:00:00+00:00",
                        "finished_at": "2026-08-02T00:00:01+00:00",
                        "backend_pid": i,
                    }
                }
                for i in range(6)
            ],
        },
    )


def test_missing_semantic_evidence_is_rejected() -> None:
    assert not V._check(
        "schedule_uniqueness",
        {"operation": {"callable": "create_or_update", "input": {}, "result": {}}},
    )
    assert not hasattr(V, "_safe_check")


def test_tamper_paths_are_requirement_specific() -> None:
    assert len(V.TAMPER_PATHS) == 29
    assert V.TAMPER_PATHS["raw_payload_snapshot_boundary"] != V.TAMPER_PATHS["cadence_policy"]
    assert V.TAMPER_PATHS["due_work_coalescing"] != V.TAMPER_PATHS["due_work_current_slot"]


def test_verifier_is_structurally_fail_closed() -> None:
    source = inspect.getsource(V)
    assert "return bool(ops)" not in source
    assert "operation.callable" not in source
    assert "_safe_check" not in source


def test_producer_has_no_preoperation_session_autobegin_or_foreign_fixture_write() -> None:
    source_path = Path(__file__).parents[2] / "scripts/runtime/run_rf15_postgres_acceptance.py"
    source = source_path.read_text()
    tree = ast.parse(source)
    assert "session.connection()" not in source
    assert "insert into mayak.parser_outcomes" not in source.lower()
    assert "_materialize_on_engine" not in source
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "connection"
        for node in ast.walk(tree)
    )


def test_fixture_proof_uses_fresh_connection_and_synthetic_only_queue_reset() -> None:
    source_path = Path(__file__).parents[2] / "scripts/runtime/run_rf15_postgres_acceptance.py"
    source = source_path.read_text()
    assert "def _assert_committed_fixture" in source
    assert "independent_connection" in source
    assert "def _reset_synthetic_scan_state" in source
    assert "https://synthetic.invalid/rf15" in source
    assert "truncate table" not in source.lower()
    assert "state in ('DUE', 'RETRY')" in source


def test_terminal_concurrency_helper_has_no_scheduler_overlap_fixture() -> None:
    source = (
        Path(__file__).parents[2] / "scripts/runtime/run_rf15_postgres_acceptance.py"
    ).read_text()
    helper = source.split("def _concurrent_terminal", 1)[1].split(
        "def scenario_expired_claim_reconciliation", 1
    )[0]
    assert "prepare_next_run" not in helper
    assert "SCEN_" not in helper
    assert "_adversarial_terminal_pair" in helper


def test_all_rf15_registries_are_explicit_and_not_defaulted() -> None:
    assert set(V.REQUIREMENT_IDS) == set(V.CHECKERS) == set(V.RAW_DEPENDENCY_PATHS)
    assert set(V.REQUIREMENT_IDS) == set(V.TAMPER_PATHS)
    assert "default-for-all" not in inspect.getsource(V)


def test_exact_29_representative_cases_and_own_causal_tampers() -> None:
    evidence = V.build_representative_evidence()
    assert len(evidence["behavioral_cases"]) == 29
    assert all(V.CHECKERS[name](evidence) for name in V.REQUIREMENT_IDS)
    assert all(not V.CHECKERS[name](V._tamper(evidence, name)) for name in V.REQUIREMENT_IDS)
