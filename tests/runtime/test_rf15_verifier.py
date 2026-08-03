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


def test_fixture_proof_uses_fresh_connection_and_ownership_safe_queue_isolation() -> None:
    source_path = Path(__file__).parents[2] / "scripts/runtime/run_rf15_postgres_acceptance.py"
    source = source_path.read_text()
    assert "def _assert_committed_fixture" in source
    assert "independent_connection" in source
    assert "def _reset_synthetic_scan_state" in source
    assert "https://synthetic.invalid/rf15" in source
    assert "truncate table" not in source.lower()
    assert "state in ('DUE', 'RETRY')" in source
    reset = (
        source.split("def _reset_synthetic_scan_state", 1)[1]
        .split("def _assert_committed_fixture", 1)[0]
        .lower()
    )
    assert "delete from" not in reset
    assert "update mayak.scan_schedules" in reset
    assert "update mayak.scan_work_items" in reset
    assert "state = 'pending_reconciliation'" in reset
    assert "parser_outcomes" not in reset
    assert "notification_" not in reset


def test_scan_queue_isolation_preserves_foreign_referenced_history() -> None:
    source = (
        Path(__file__).parents[2] / "scripts/runtime/run_rf15_postgres_acceptance.py"
    ).read_text()
    reset = (
        source.split("def _reset_synthetic_scan_state", 1)[1]
        .split("def _assert_committed_fixture", 1)[0]
        .lower()
    )
    for historical_table in (
        "scan_runs",
        "scan_listing_observations",
        "scan_beacon_listing_state",
        "scan_anchors",
    ):
        assert f"delete from mayak.{historical_table}" not in reset
    assert "state in ('due', 'retry')" in reset
    assert "where state in ('due', 'retry') and due_at <= now()" in reset


def test_producer_has_no_direct_parser_or_foreign_module_mutation() -> None:
    source = (
        Path(__file__).parents[2] / "scripts/runtime/run_rf15_postgres_acceptance.py"
    ).read_text()
    lowered = source.lower()
    assert "delete from mayak.parser_outcomes" not in lowered
    assert "update mayak.parser_outcomes" not in lowered
    for foreign_table in (
        "identity_",
        "entitlement_",
        "billing_",
        "egress_",
        "notification_",
    ):
        assert f"delete from mayak.{foreign_table}" not in lowered
        assert f"update mayak.{foreign_table}" not in lowered


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


def test_adversarial_second_run_requires_existing_fixture_and_has_no_fresh_fixture_path() -> None:
    source = (
        Path(__file__).parents[2] / "scripts/runtime/run_rf15_postgres_acceptance.py"
    ).read_text()
    tree = ast.parse(source)
    helper = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "_adversarial_second_run"
    )
    arguments = {arg.arg for arg in helper.args.args}
    assert {"engine", "first"} <= arguments
    helper_source = ast.get_source_segment(source, helper) or ""
    assert "prepare_claimed_run" not in helper_source
    assert "_create_fixture" not in helper_source
    assert "mayak.scan_beacons" not in helper_source.lower()
    concurrent_new = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "scenario_concurrent_new_listing_serialization"
    )
    calls = [
        node for node in ast.walk(concurrent_new)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    ]
    assert any(node.func.id == "prepare_next_run" for node in calls)
    assert any(node.func.id == "_adversarial_second_run" for node in calls)
    assert not any(node.func.id == "_adversarial_terminal_pair" for node in calls)


def test_both_foreign_scenarios_use_one_shared_two_layer_builder() -> None:
    source = (
        Path(__file__).parents[2] / "scripts/runtime/run_rf15_postgres_acceptance.py"
    ).read_text()
    tree = ast.parse(source)
    calls = {}
    for name in ("scenario_foreign_state_witness", "scenario_no_foreign_domain_effect"):
        node = next(
            item for item in tree.body
            if isinstance(item, ast.FunctionDef) and item.name == name
        )
        calls[name] = [
            item.func.id for item in ast.walk(node)
            if isinstance(item, ast.Call) and isinstance(item.func, ast.Name)
        ]
    assert calls["scenario_foreign_state_witness"] == ["_foreign_two_layer_witness"]
    assert calls["scenario_no_foreign_domain_effect"] == ["_foreign_two_layer_witness"]
    assert "def _build_foreign_two_layer_witness" in source


def test_all_rf15_registries_are_explicit_and_not_defaulted() -> None:
    assert set(V.REQUIREMENT_IDS) == set(V.CHECKERS) == set(V.RAW_DEPENDENCY_PATHS)
    assert set(V.REQUIREMENT_IDS) == set(V.TAMPER_PATHS)
    assert "default-for-all" not in inspect.getsource(V)


def test_exact_29_representative_cases_and_own_causal_tampers() -> None:
    evidence = V.build_representative_evidence()
    assert len(evidence["behavioral_cases"]) == 29
    assert all(V.CHECKERS[name](evidence) for name in V.REQUIREMENT_IDS)
    assert all(not V.CHECKERS[name](V._tamper(evidence, name)) for name in V.REQUIREMENT_IDS)


def test_operation_namespace_is_fail_closed_and_replay_uses_durable_identity() -> None:
    evidence = V.build_representative_evidence()
    replay = evidence["behavioral_cases"]["run_replay"]
    assert "operation_first" not in replay
    assert "first_run_result" in replay
    assert V._check("run_replay", replay)
    replay["operation_malformed"] = "not-a-raw-operation"
    with pytest.raises(ValueError):
        V._ops(replay)


def test_corrected_semantic_shapes_cover_expiry_authority_and_races() -> None:
    evidence = V.build_representative_evidence()
    assert V._check(
        "expired_claim_reconciliation",
        evidence["behavioral_cases"]["expired_claim_reconciliation"],
    )
    assert V._check("authority_recheck", evidence["behavioral_cases"]["authority_recheck"])
    assert V._check(
        "concurrent_baseline_serialization",
        evidence["behavioral_cases"]["concurrent_baseline_serialization"],
    )
    assert V._check(
        "concurrent_new_listing_serialization",
        evidence["behavioral_cases"]["concurrent_new_listing_serialization"],
    )


def test_foreign_witness_uses_two_layer_snapshots() -> None:
    evidence = V.build_representative_evidence()
    for name in ("foreign_state_witness", "no_foreign_domain_effect"):
        case = evidence["behavioral_cases"][name]
        assert "rf15_physical" in case
        assert any("physical_before.semantic" in path for path in V.RAW_DEPENDENCY_PATHS[name])
        assert any(
            "rf15_physical.physical_after.run_rows" in path
            for path in V.RAW_DEPENDENCY_PATHS[name]
        )
        assert V._check(name, case)


def test_foreign_checker_does_not_treat_foreign_semantics_as_scan_physical() -> None:
    evidence = V.build_representative_evidence()
    for name in ("foreign_state_witness", "no_foreign_domain_effect"):
        case = evidence["behavioral_cases"][name]
        case["physical_before"]["schedule_rows"] = []
        case["physical_after"]["schedule_rows"] = []
        assert V._check(name, case)
