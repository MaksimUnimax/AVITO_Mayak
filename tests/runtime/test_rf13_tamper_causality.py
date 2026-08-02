# ruff: noqa

from __future__ import annotations

import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
sys.path.insert(0, str(Path(__file__).parents[1]))
from fixtures.rf13.local_valid_evidence import valid_fixture
from scripts.runtime.verify_rf13_acceptance import REQUIRED_TAMPER_CASES, TAMPER_MUTATIONS, prepare_verification_context, run_requirement_checks


def _diff(before, after, prefix=""):
    if type(before) is not type(after):
        return {prefix}
    if isinstance(before, dict):
        return {path for key in set(before) | set(after) for path in _diff(before.get(key), after.get(key), f"{prefix}.{key}".strip("."))}
    if isinstance(before, list):
        return {path for index in range(max(len(before), len(after))) for path in _diff(before[index] if index < len(before) else None, after[index] if index < len(after) else None, f"{prefix}.{index}".strip("."))}
    return {prefix} if before != after else set()


def test_all_required_tamper_mutations_causally_fail_mapped_checker() -> None:
    pristine = valid_fixture()
    pristine = prepare_verification_context(pristine, __import__("pathlib").Path("."), "fixture-sha")
    pristine_results = run_requirement_checks(pristine)
    assert all(result.passed for result in pristine_results.values()), {key: result.reason for key, result in pristine_results.items() if not result.passed}
    for case in REQUIRED_TAMPER_CASES:
        mutated = copy.deepcopy(pristine)
        TAMPER_MUTATIONS[case].mutate(mutated)
        actual_paths = _diff(pristine, mutated)
        declared = TAMPER_MUTATIONS[case].changed_paths
        assert actual_paths
        assert all(any(path == prefix or path.startswith(prefix + ".") or prefix.startswith(path + ".") for prefix in declared) for path in actual_paths), case
        results = run_requirement_checks(mutated)
        mapped = TAMPER_MUTATIONS[case].requirement_ids
        assert any(not results[requirement].passed for requirement in mapped), case


def test_unordered_semantic_selectors_survive_reordering() -> None:
    for case, section, key in (
        ("active_denial_reason", "active_slot_concurrency", "workers"),
        ("idempotency_missing_replay", "idempotency_concurrency", "outcomes"),
        ("idempotency_fake_replay", "idempotency_concurrency", "outcomes"),
        ("patch_duplicate_revision", "patch_lww_concurrency", "workers"),
        ("patch_current_not_max", "patch_lww_concurrency", "workers"),
        ("patch_value_not_max", "patch_lww_concurrency", "workers"),
    ):
        item = valid_fixture()
        item[section][key].reverse()
        item = prepare_verification_context(item, Path("."), "fixture-sha")
        TAMPER_MUTATIONS[case].mutate(item)
        results = run_requirement_checks(item)
        assert any(not results[requirement].passed for requirement in TAMPER_MUTATIONS[case].requirement_ids), case


def test_active_denial_selector_handles_both_indices() -> None:
    for index in (0, 1):
        item = valid_fixture()
        workers = item["active_slot_concurrency"]["workers"]
        workers.reverse() if index == 0 else None
        TAMPER_MUTATIONS["active_denial_reason"].mutate(item)
        assert next(row for row in workers if row["decision"] == "DENIED")["reason"] == "capacity unavailable"
