"""RF20 PostgreSQL behavioral nodes, all backed by the shared scenario."""

from __future__ import annotations

import os
from functools import lru_cache

import pytest
from sqlalchemy import create_engine

from mayak.runtime.rf20_acceptance_scenario import run_rf20_acceptance_scenario


def _engines():
    dsn = os.environ.get("RF20_DATABASE_URL")
    fixture = os.environ.get("RF20_MIGRATION_DSN")
    if not dsn or not fixture:
        if os.environ.get("RF20_REQUIRE_POSTGRES") == "1":
            pytest.fail("RF20_DATABASE_URL and RF20_MIGRATION_DSN are required")
        pytest.skip("local PostgreSQL is intentionally not available")
    return create_engine(dsn, pool_pre_ping=True), create_engine(fixture, pool_pre_ping=True)


@lru_cache(maxsize=1)
def _evidence() -> dict[str, object]:
    application, fixture = _engines()
    return run_rf20_acceptance_scenario(
        application_engine=application,
        fixture_engine=fixture,
        candidate_sha=os.environ.get("GITHUB_SHA", "0" * 40),
        namespace="pg-test:rf20",
    )


def _pg_probe() -> dict[str, object]:
    evidence = _evidence()
    assert str(evidence["postgresql_version"]).startswith("PostgreSQL 18")
    assert evidence["migration_head"] == "RF20_ADMIN_SUPPORT_RUNTIME"
    return evidence


def test_pg_support_case_round_trip_maps_physical_id_to_case_id() -> None:
    e = _pg_probe()
    assert e["physical_case_id"] == e["support_case_id"]
    assert e["runtime_get_case_id"] == e["support_case_id"]
    assert e["runtime_list_case_id"] == e["support_case_id"]
    assert e["case_projection_match"] is True


def test_pg_support_open_get_and_list_round_trip() -> None:
    e = _pg_probe()
    assert e["open"] is True and e["case_projection_match"] is True


def test_pg_support_assignment_persists_operator() -> None:
    assert _pg_probe()["assignment"] is True


def test_pg_support_note_persists_and_is_not_duplicated_into_event_details() -> None:
    e = _pg_probe()
    assert e["note"] is True and e["note_body_in_event_details"] is False


def test_pg_support_escalation_persists() -> None:
    assert _pg_probe()["support_lifecycle"]["escalated"] is True


def test_pg_support_resolve_requires_and_persists_evidence() -> None:
    assert _pg_probe()["support_lifecycle"]["resolved"] is True


def test_pg_support_close_requires_and_persists_evidence() -> None:
    e = _pg_probe()
    assert e["support_lifecycle"]["closed"] is True and e["final_case_state"] == "CLOSED"


def test_pg_support_stale_row_version_is_rejected() -> None:
    e = _pg_probe()
    assert e["support_stale_row_version"] == "CONFLICT"
    assert e["support_stale_state_unchanged"] is True


def test_pg_same_key_same_fingerprint_concurrent_command_has_one_effect() -> None:
    e = _pg_probe()
    assert e["concurrency"]["one_logical_effect"] is True
    assert e["concurrency"]["owner_effect_count"] == 1
    assert e["concurrency"]["owner_resource_count"] == 1


def test_pg_same_key_different_fingerprint_is_conflict() -> None:
    # The shared command path records normalized fingerprints in PostgreSQL.
    assert _pg_probe()["fingerprint_conflict"] is True


def test_pg_policy_blocked_replay_has_zero_owner_effect() -> None:
    e = _pg_probe()
    assert e["foreign_beacon"] == "POLICY_BLOCKED" and e["foreign_beacon_replay"] is True


def test_pg_ambiguous_replay_calls_owner_once() -> None:
    e = _pg_probe()
    assert (
        e["ambiguity"] == "AMBIGUOUS"
        and e["ambiguity_replay"] is True
        and e["ambiguous_owner_calls"] == 1
    )


def test_pg_actual_identity_role_delegation_is_case_scoped() -> None:
    assert _pg_probe()["identity_role_mutation"] is True


def test_pg_actual_tariff_bootstrap_uses_entitlements_owner() -> None:
    assert _pg_probe()["tariff_bootstrap"] is True


def test_pg_actual_basic_assignment_uses_entitlements_owner() -> None:
    assert _pg_probe()["basic_assignment"] is True


def test_pg_actual_manual_access_grant_uses_entitlements_owner() -> None:
    assert _pg_probe()["access_grant"] is True


def test_pg_actual_manual_access_revoke_uses_entitlements_owner() -> None:
    assert _pg_probe()["access_revoke"] is True


def test_pg_entitlements_owner_audit_uses_rf20_correlation() -> None:
    e = _pg_probe()
    assert e["correlation_equality"] is True and e["entitlements_owner_correlation"] is not None


def test_pg_actual_beacon_support_patch_mutates_once() -> None:
    assert _pg_probe()["beacon"] is True


def test_pg_beacon_success_replay_adds_no_second_revision() -> None:
    e = _pg_probe()
    assert e["beacon_replay_flag"] is True
    assert e["beacon_revision_count_after_first"] == e["beacon_revision_count_before"] + 1
    assert e["beacon_revision_count_after_replay"] == e["beacon_revision_count_after_first"]


def test_pg_notification_admin_privileged_read_is_target_scoped() -> None:
    assert _pg_probe()["notification_diagnostics"] is True


def test_pg_notification_privileged_read_is_read_only() -> None:
    e = _pg_probe()
    assert e["notification_read_only"] is True
    assert e["notification_before_snapshot"] == e["notification_after_snapshot"]


def test_pg_operator_and_customer_accounts_remain_distinct() -> None:
    assert _pg_probe()["operator_customer_distinct"] is True


def test_pg_direct_unrelated_foreign_dml_is_denied() -> None:
    assert _pg_probe()["direct_foreign_dml_denied"] is True


def test_pg_rf20_acceptance_scenario_reaches_evidence_ready_state() -> None:
    e = _pg_probe()
    assert e["host_postgres_published"] is False and e["provider_calls"] == 0
