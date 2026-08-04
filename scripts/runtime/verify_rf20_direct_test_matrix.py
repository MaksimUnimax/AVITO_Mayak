"""Fail-closed categorized RF20 behavioral test manifest verifier."""

# ruff: noqa: E501
from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[2]
UI = "tests/runtime/test_rf20_admin_ui.py"
COMP = "tests/runtime/test_rf20_composition.py"
RUNTIME = "tests/runtime/test_rf20_admin_support_runtime.py"
PG = "tests/runtime/test_rf20_postgres_acceptance.py"
NOTIFY = "tests/runtime/test_rf17_notification_delivery_runtime.py"


def _nodes(path: str, names: str) -> set[str]:
    return {f"{path}::{name}" for name in names.split()}


MANIFEST = {
    "UI_BEHAVIOR": _nodes(
        UI,
        """test_ui_authorized_landing_renders_cases test_ui_unauthenticated_landing_is_safe test_ui_account_summary_uses_server_authority test_ui_open_case_posts_to_runtime test_ui_malformed_open_case_is_400 test_ui_internal_note_posts_and_escapes_body test_ui_sensitive_internal_note_is_rejected test_ui_assignment_posts_selected_operator test_ui_invalid_assignment_is_safe test_ui_escalation_posts_to_runtime test_ui_transition_posts_expected_case_version test_ui_resolve_requires_evidence test_ui_close_requires_evidence test_ui_role_action_posts_exact_selected_action test_ui_duplicate_action_fields_are_rejected test_ui_tariff_action_posts_to_runtime test_ui_access_grant_posts_to_runtime test_ui_access_revoke_posts_grant_id_to_runtime test_ui_beacon_patch_uses_beacon_row_version_not_case_version test_ui_beacon_source_url_patch_is_rejected test_ui_malformed_beacon_patch_is_400 test_ui_notification_diagnostics_uses_case_account test_ui_unknown_action_family_is_rejected test_ui_client_actor_or_role_override_cannot_authorize test_ui_policy_blocked_result_renders_safely test_ui_conflict_result_renders_safely test_ui_ambiguous_result_renders_safely""",
    ),
    "COMPOSITION_BEHAVIOR": _nodes(
        COMP,
        """test_composition_factory_returns_exact_rf20_adapters test_identity_operator_requires_persisted_active_session test_identity_operator_rejects_non_operator_role test_identity_admin_cross_account_authority_keeps_actor_and_target_distinct test_identity_admin_entitlements_scope_is_exact_account_id test_identity_support_has_no_entitlements_admin_capabilities test_notification_admin_scope_targets_customer_account test_notification_support_scope_targets_customer_account test_notification_user_privileged_scope_is_denied test_notification_unauthorized_scope_is_denied test_notification_scope_account_mismatch_is_denied test_tariff_adapter_maps_bootstrap_to_actual_owner_method test_tariff_adapter_maps_basic_assignment_to_actual_owner_method test_access_adapter_maps_grant_to_actual_owner_method test_access_adapter_maps_revoke_to_actual_owner_method test_unsupported_entitlements_action_never_calls_owner test_scan_adapter_preserves_safe_policy_boundary test_beacon_adapter_preserves_operator_target_account_separation test_beacon_adapter_blocks_source_url_before_owner_effect test_entitlements_owner_call_observes_bound_rf20_correlation""",
    ),
    "RUNTIME_BEHAVIOR": _nodes(
        RUNTIME,
        """test_support_case_view_maps_physical_id_to_case_id test_get_case_and_list_cases_use_same_projection_mapper test_support_runtime_requires_verified_operator test_role_command_is_case_account_scoped test_tariff_command_is_case_account_scoped test_access_grant_is_case_account_scoped test_access_revoke_uses_case_account_as_owner_scope test_beacon_account_scope_comes_from_support_case test_unsupported_action_is_policy_blocked_without_owner_call test_terminal_success_replay_preserves_state_and_marks_replay test_terminal_policy_block_replay_preserves_state_and_marks_replay test_terminal_ambiguous_replay_preserves_state_and_marks_replay test_idempotency_fingerprint_mismatch_is_conflict test_replay_does_not_call_owner_twice test_role_owner_receives_resolved_rf20_correlation test_tariff_owner_executes_inside_resolved_rf20_correlation test_access_owner_executes_inside_resolved_rf20_correlation test_beacon_owner_receives_resolved_rf20_correlation""",
    ),
    "POSTGRES_BEHAVIOR": _nodes(
        PG,
        """test_pg_support_case_round_trip_maps_physical_id_to_case_id test_pg_support_open_get_and_list_round_trip test_pg_support_assignment_persists_operator test_pg_support_note_persists_and_is_not_duplicated_into_event_details test_pg_support_escalation_persists test_pg_support_resolve_requires_and_persists_evidence test_pg_support_close_requires_and_persists_evidence test_pg_support_stale_row_version_is_rejected test_pg_same_key_same_fingerprint_concurrent_command_has_one_effect test_pg_same_key_different_fingerprint_is_conflict test_pg_policy_blocked_replay_has_zero_owner_effect test_pg_ambiguous_replay_calls_owner_once test_pg_actual_identity_role_delegation_is_case_scoped test_pg_actual_tariff_bootstrap_uses_entitlements_owner test_pg_actual_basic_assignment_uses_entitlements_owner test_pg_actual_manual_access_grant_uses_entitlements_owner test_pg_actual_manual_access_revoke_uses_entitlements_owner test_pg_entitlements_owner_audit_uses_rf20_correlation test_pg_actual_beacon_support_patch_mutates_once test_pg_beacon_success_replay_adds_no_second_revision test_pg_notification_admin_privileged_read_is_target_scoped test_pg_notification_privileged_read_is_read_only test_pg_operator_and_customer_accounts_remain_distinct test_pg_direct_unrelated_foreign_dml_is_denied test_pg_rf20_acceptance_scenario_reaches_evidence_ready_state""",
    ),
    "NOTIFICATION_OWNER_BEHAVIOR": _nodes(
        NOTIFY,
        """test_notification_user_history_still_requires_same_account test_notification_admin_scope_reads_target_account test_notification_support_scope_reads_target_account test_notification_user_cannot_use_privileged_read test_notification_unauthorized_privileged_scope_is_denied test_notification_privileged_scope_account_mismatch_is_denied test_notification_beacon_scope_limits_history test_notification_privileged_read_limit_is_bounded test_notification_privileged_read_does_not_mutate_delivery_state""",
    ),
}

STATIC_GATES = frozenset()
CANONICAL_FILES = (UI, COMP, RUNTIME, PG, NOTIFY)


def collect() -> set[str]:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", *CANONICAL_FILES],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        print(result.stdout + result.stderr)
        raise SystemExit("RF20 direct-test collection failed")
    return {
        line.strip()
        for line in (result.stdout + result.stderr).splitlines()
        if "::" in line and " " not in line.strip()
    }


def _behavioral_placeholders() -> list[str]:
    bad: list[str] = []
    forbidden = {"read_text", "getsource", "open"}
    for category, nodes in MANIFEST.items():
        if category == "STATIC_GATES":
            continue
        for node in nodes:
            path, name = node.split("::", 1)
            tree = ast.parse((ROOT / path).read_text(encoding="utf-8"), filename=path)
            function = next(
                (
                    item
                    for item in ast.walk(tree)
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and item.name == name
                ),
                None,
            )
            if function is None:
                continue
            for item in ast.walk(function):
                if (
                    isinstance(item, ast.Call)
                    and isinstance(item.func, ast.Attribute)
                    and item.func.attr in forbidden
                ):
                    bad.append(node)
                if (
                    isinstance(item, ast.Assert)
                    and isinstance(item.test, ast.Constant)
                    and item.test.value is True
                ):
                    bad.append(node)
    return sorted(set(bad))


def main() -> int:
    collected = collect()
    required = set().union(*MANIFEST.values())
    duplicate = sum(len(nodes) for nodes in MANIFEST.values()) != len(required)
    bad_static = bool(required & STATIC_GATES)
    missing = required - collected
    placeholders = _behavioral_placeholders()
    for category, nodes in MANIFEST.items():
        print(
            f"{category}: collected_required={len(nodes & collected)}/{len(nodes)} missing={len(nodes - collected)}"
        )
    if placeholders:
        for node in placeholders:
            print(f"BEHAVIORAL_PLACEHOLDER {node}")
    if duplicate or bad_static or missing or placeholders:
        for node in sorted(missing):
            print(f"MISSING {node}")
        return 1
    print(f"overall PASS: {len(required)} required behavioral nodes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
