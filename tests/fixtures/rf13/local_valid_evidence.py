# ruff: noqa

from __future__ import annotations

from copy import deepcopy

from scripts.runtime.verify_rf13_acceptance import EXPECTED_BASE, SCHEMA_VERSION, TECHNICAL_ID


def valid_fixture() -> dict:
    workers = [
        {"worker_id": "a", "outcome": "SUCCEEDED", "value": ["city:a"], "revision_no": 1, "idempotency_key": "a"},
        {"worker_id": "b", "outcome": "SUCCEEDED", "value": ["city:b"], "revision_no": 2, "idempotency_key": "b"},
    ]
    outcomes = [
        {"idempotency_key": "same", "fingerprint": "fp", "repository_decision": "NEW", "resource_id": "resource"},
        {"idempotency_key": "same", "fingerprint": "fp", "repository_decision": "REPLAY_TERMINAL", "resource_id": "resource"},
    ]
    active_workers = [
        {"decision": "ALLOWED", "exception_class": None, "reason": ""},
        {"decision": "DENIED", "exception_class": "BeaconRuntimeError", "reason": "current entitlement does not allow lifecycle action"},
    ]
    zero_effect = {"exception_class": "BeaconRuntimeError", "safe_reason": "actor does not own Beacon", "row_version_before": 2, "row_version_after": 2, "revision_count_before": 2, "revision_count_after": 2, "event_count_before": 2, "event_count_after": 2, "audit_count_before": 2, "audit_count_after": 2, "idempotency_count_before": 2, "idempotency_count_after": 2}
    ownership = {name: deepcopy(zero_effect) for name in ("foreign_read", "foreign_state_change", "unverified_mutation", "accepted_violation")}
    ownership["unverified_mutation"]["safe_reason"] = "actor verification required"
    ownership["accepted_violation"]["safe_reason"] = "actor verification required"
    definitions = [
        "CHECK (current_revision_no IS NULL OR current_revision_no > 0)",
        "CHECK (source_url IS NULL OR btrim(source_url) <> '')",
        "CHECK (current_revision_no IS NULL AND current_revision_id IS NULL OR current_revision_no IS NOT NULL AND current_revision_id IS NOT NULL)",
        "CHECK (actor_account_id IS NOT NULL AND system_actor_class IS NULL OR actor_account_id IS NULL AND system_actor_class IS NOT NULL)",
    ]
    constraints = [
        {"name": "uq_revision_id", "type": "u", "columns": ["revision_id"], "definition": "UNIQUE (revision_id)"},
        {"name": "fk_current_revision", "type": "f", "columns": ["current_revision_id"], "referenced_table": "beacon_configuration_revisions", "referenced_columns": ["revision_id"], "definition": "FOREIGN KEY (current_revision_id) REFERENCES beacon_configuration_revisions (revision_id)"},
    ]
    negatives = [{"status": status, "exception_or_result": "REJECTED", "pre_revision_count": 2, "post_revision_count": 2, "pre_override_count": 0, "post_override_count": 0, "current_revision_before": "r2", "current_revision_after": "r2", "row_version_before": 3, "row_version_after": 3} for status in ("MALFORMED", "INCOMPLETE", "CAPTCHA_AFFECTED", "BLOCKED", "ROUTE_FAILED", "AMBIGUOUS", "UNSUPPORTED")]
    events = [{"sequence": n, "to_state": state} for n, state in enumerate(("DRAFT", "READY", "ACTIVE", "PAUSED", "ARCHIVED", "PERMANENTLY_DELETED"), 1)]
    return {
        "_local_fixture": True, "schema_version": SCHEMA_VERSION,
        "identity": {"technical_id": TECHNICAL_ID, "candidate_sha": "fixture-sha", "candidate_tree": "fixture-tree", "parent": EXPECTED_BASE, "schema_version": SCHEMA_VERSION},
        "toolchain": {"python": "3.14.6", "uv": "0.11.31", "uv_lock_sha256": "fixture", "postgres_major": 18},
        "migration_setup_identity": {"empty_to_head": {"before": "empty", "after": "RF13_BEACON_RUNTIME_HARDEN"}, "version_table": "RF13_BEACON_RUNTIME_HARDEN", "head": "RF13_BEACON_RUNTIME_HARDEN"},
        "physical_schema": {"metadata_parity": True, "constraints": constraints, "exact_constraint_definitions": definitions},
        "preparation": {"state": "DRAFT", "current_revision_no": None, "current_revision_id": None, "lifecycle_event_count": 1, "lifecycle_events": [{"from_state": None, "to_state": "DRAFT"}], "revision_count": 0, "override_count": 0, "source_url": "u", "submitted_source_url": "u"},
        "positive_snapshot": {"post_revision_count": 1, "pre_revision_count": 0, "state_after": "READY", "parser_outcome": "CLEAN", "accepted_as_clean": True, "parser_evidence_reference": "e", "current_revision_id": "r1", "persisted_revision_id": "r1", "current_revision_no": 1, "persisted_revision_no": 1, "source_url_before": "u", "source_url_after": "u", "override_count": 0},
        "negative_snapshot_matrix": negatives,
        "patch_lww_concurrency": {"sessions": 2, "barrier": True, "workers": workers, "committed_count": 2, "revision_count": 2, "final_revision_no": 2, "final_value": ["city:b"], "final_row_version_delta": 2, "orphan_revision_count": 0, "orphan_override_count": 0},
        "idempotency_concurrency": {"sessions": 2, "barrier": True, "attempt_count": 2, "outcomes": outcomes, "business_effect_count": 1, "terminal_record_count": 1},
        "active_slot_concurrency": {"sessions": 2, "barrier": True, "capacity": 1, "baseline_active_count": 0, "entitlement_observations": [{"active_count": 0}, {"active_count": 1}], "workers": active_workers, "final_active_count": 1, "activation_event_count": 1},
        "rollback": {"in_transaction": {"beacon_beacons": 1}, "baseline": {"beacon_beacons": 0}, "post_rollback": {"beacon_beacons": 0}, "post_independent_query": {"beacon_beacons": 0}, "retry_business_effect_count": 1, "retry_terminal_effect_count": 1, "retry_resource_absent": True, "retry_resource_persisted": True, "retry_outcome": "SUCCEEDED"},
        "ownership": ownership,
        "lifecycle_history": {"event_rows": events, "active_count_after_archive": 0, "restore_entitlement": {"action": "restore", "fresh": True, "allowed": True}, "source_url_before_archive": "u", "source_url_after_restore": "u", "revision_id_before_archive": "r1", "revision_id_after_restore": "r1", "permanent_delete_state": "PERMANENTLY_DELETED", "permanent_delete_restorable": False, "rejected_restore": {"accepted": False, "exception_class": "BeaconRuntimeError", "reason": "permanent delete is terminal"}},
        "system_freeze_positive": {"resolved_class": "ENTITLEMENTS_AND_BILLING_SERVICE", "requested_service_class": "ENTITLEMENTS_AND_BILLING_SERVICE", "persisted_system_actor_class": "ENTITLEMENTS_AND_BILLING_SERVICE", "event": {"actor_account_id": None, "to_state": "FROZEN", "causation_reference": "rf13-expiry-causation", "policy_source_reference": "rf13-paid-expiry-policy"}, "freeze_event_count": 1, "auto_free_observations": []},
        "system_authority_mismatch_negative": {"resolved_class": "MAINTENANCE_SERVICE", "requested_causation_class": "ENTITLEMENTS_AND_BILLING_SERVICE", "exception_class": "BeaconRuntimeError", "reason": "system authority class does not match causation", "before": {"x": 1}, "after": {"x": 1}},
        "revision_immutability": {"revision_1_hash_before": "h", "revision_1_hash_after": "h", "revision_1_id": "r1", "revision_2_id": "r2", "revision_2_no": 2, "current_revision_id": "r2", "current_revision_no": 2},
        "cleanup": {"synthetic_post_counts": {"beacon_beacons": 0}, "preexisting_preserved": True, "preexisting_baseline": {"x": 1}, "preexisting_after": {"x": 1}},
        "security_witness": {"secret_scan_match_count": 0, "raw_provider_payload_forbidden_schema_field_count": 0, "raw_provider_payload_forbidden_persisted_value_count": 0, "production_personal_data_marker_count": 0, "non_synthetic_source_count": 0},
        "different_field_concurrency_applicability": {"applicable": False, "reason": "one supported field"},
    }
