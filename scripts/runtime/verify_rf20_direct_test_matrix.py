"""Mechanically verify the canonical RF20 direct-test node matrix."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[2]
CANONICAL_FILES = (
    "tests/runtime/test_rf20_admin_ui.py",
    "tests/runtime/test_rf20_admin_support_runtime.py",
    "tests/runtime/test_rf20_composition.py",
    "tests/runtime/test_rf20_corrective_direct.py",
    "tests/runtime/test_rf20_postgres_acceptance.py",
    "tests/runtime/test_rf17_notification_delivery_runtime.py",
    "tests/runtime/test_support_schema.py",
    "tests/architecture/test_admin_and_support_semantic_boundaries.py",
    "tests/contract/test_admin_and_support_semantic_contract_exports.py",
)

REQUIRED_NODES = frozenset(
    {
        "tests/runtime/test_rf20_admin_ui.py::test_authorized_landing_is_server_rendered_and_escapes_title",
        "tests/runtime/test_rf20_admin_ui.py::test_unauthenticated_landing_is_safe",
        "tests/runtime/test_rf20_admin_ui.py::test_account_summary_uses_safe_projection",
        "tests/runtime/test_rf20_admin_ui.py::test_assignment_route_persists_selected_operator",
        "tests/runtime/test_rf20_admin_ui.py::test_explicit_escalation_route_is_exposed",
        "tests/runtime/test_rf20_admin_ui.py::test_notification_diagnostics_navigation_is_exposed",
        "tests/runtime/test_rf20_admin_support_runtime.py::test_terminal_replay_preserves_every_semantic_state_and_marks_replay",
        "tests/runtime/test_rf20_admin_support_runtime.py::test_delegated_commands_require_case_target_scope",
        "tests/runtime/test_rf20_admin_support_runtime.py::test_unsupported_action_is_policy_blocked_without_owner_call",
        "tests/runtime/test_rf20_composition.py::test_identity_authority_maps_cross_account_to_owner_scope_and_bound_correlation",
        "tests/runtime/test_rf20_composition.py::test_support_identity_authority_has_no_entitlements_admin_capabilities",
        "tests/runtime/test_rf20_composition.py::test_notification_scope_rejects_user_unauthorized_and_mismatch_without_query",
        "tests/runtime/test_rf20_composition.py::test_entitlements_access_adapter_maps_grant_and_revoke_to_actual_owner",
        "tests/runtime/test_rf20_corrective_direct.py::test_notification_privileged_read_is_exported",
        "tests/runtime/test_rf20_corrective_direct.py::test_notification_user_read_rule_is_unchanged",
        "tests/runtime/test_rf20_corrective_direct.py::test_notification_scope_beacon_restriction_is_enforced",
        "tests/runtime/test_rf20_corrective_direct.py::test_entitlements_scope_contract_is_exact_account_id",
        "tests/runtime/test_rf20_corrective_direct.py::test_support_runtime_forwards_case_account_to_entitlements",
        "tests/runtime/test_rf20_corrective_direct.py::test_beacon_row_version_is_not_case_row_version",
        "tests/runtime/test_rf20_corrective_direct.py::test_producer_uses_actual_composition_and_owner_commands",
        "tests/runtime/test_rf20_corrective_direct.py::test_verifier_requires_factual_provider_provenance",
        "tests/runtime/test_rf20_corrective_direct.py::test_workflow_runs_matrix_before_producer",
        "tests/runtime/test_rf20_corrective_direct.py::test_acceptance_artifact_is_success_only_and_strict",
        "tests/runtime/test_rf20_postgres_acceptance.py::test_support_events_have_physical_timezone_aware_timestamps",
        "tests/runtime/test_rf20_postgres_acceptance.py::test_postgresql_advisory_lock_serializes_independent_transactions",
        "tests/runtime/test_rf17_notification_delivery_runtime.py::test_rf17_runtime_requires_actor_authorization_and_typed_reconciliation",
    }
)


def collect() -> tuple[set[str], str]:
    command = [sys.executable, "-m", "pytest", "--collect-only", "-q", *CANONICAL_FILES]
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    output = result.stdout + result.stderr
    nodes = {
        line.strip() for line in output.splitlines() if "::" in line and " " not in line.strip()
    }
    if result.returncode != 0:
        raise SystemExit("RF20 direct-test collection failed")
    return nodes, output


def main() -> int:
    nodes, _ = collect()
    missing = sorted(REQUIRED_NODES - nodes)
    if missing:
        for node in missing:
            print(f"MISSING {node}")
        return 1
    print(
        f"RF20 direct-test matrix verified: {len(nodes)} collected, {len(REQUIRED_NODES)} required"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
