"""Direct assertions for the RF20 corrective owner boundaries and gates."""

from __future__ import annotations

from pathlib import Path

from mayak.modules import notification_delivery as notification
from mayak.modules.notification_delivery.runtime import read_history

ROOT = Path(__file__).parents[2]


def _source(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_notification_privileged_read_is_exported() -> None:
    assert notification.read_history_for_authorized_scope is not None
    assert "read_history_for_authorized_scope" in notification.__all__


def test_notification_user_read_rule_is_unchanged() -> None:
    assert "actor_account_id != account_id" in _source(
        "src/mayak/modules/notification_delivery/runtime.py"
    )
    assert "read_history_for_authorized_scope" not in read_history.__name__


def test_notification_scope_beacon_restriction_is_enforced() -> None:
    source = _source("src/mayak/modules/notification_delivery/runtime.py")
    assert "beacon_scope_ids" in source
    assert "Beacon scope mismatch" in source


def test_entitlements_scope_contract_is_exact_account_id() -> None:
    source = _source("src/mayak/runtime/rf20_composition.py")
    assert 'scope="account_id"' in source
    assert "identity:admin" not in source


def test_support_runtime_forwards_case_account_to_entitlements() -> None:
    source = _source("src/mayak/modules/admin_and_support/runtime.py")
    assert 'arguments["target_account_id"] = case.account_id' in source
    assert "case-target-mismatch" in source


def test_beacon_row_version_is_not_case_row_version() -> None:
    template = _source("src/mayak/modules/admin_and_support/templates/admin.html")
    ui = _source("src/mayak/modules/admin_and_support/admin_ui.py")
    assert "beacon_summary.row_versions[0]" in template
    assert "runtime.beacon.safe_summary" in ui
    assert 'name="expected_row_version" value="{{ case.row_version' not in template


def test_producer_uses_actual_composition_and_owner_commands() -> None:
    source = _source("scripts/runtime/run_rf20_postgres_acceptance.py")
    assert "build_rf20_composition" in source
    assert "bootstrap = runtime.execute_tariff_action" in source
    assert "runtime.execute_access_action" in source
    assert "runtime.execute_beacon_support_patch" in source


def test_verifier_requires_factual_provider_provenance() -> None:
    source = _source("scripts/runtime/verify_rf20_acceptance.py")
    assert "provider_zero_provenance" in source
    assert "external_provider_calls_observed" in source
    assert "real_provider_secret_reads_observed" in source
    assert "raw_provider_payload_records_observed" in source


def test_workflow_runs_matrix_before_producer() -> None:
    source = _source(".github/workflows/ci-rf20-acceptance.yml")
    assert "verify_rf20_direct_test_matrix.py" in source
    assert source.index("verify_rf20_direct_test_matrix.py") < source.index(
        "run_rf20_postgres_acceptance.py"
    )


def test_acceptance_artifact_is_success_only_and_strict() -> None:
    source = _source(".github/workflows/ci-rf20-acceptance.yml")
    assert "if: success()" in source
    assert "if-no-files-found: error" in source
