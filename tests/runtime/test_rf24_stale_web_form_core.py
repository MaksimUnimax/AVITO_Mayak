from __future__ import annotations

import copy

import pytest

from scripts.runtime.verify_rf24_stale_web_form import verify


def _evidence() -> dict[str, object]:
    summary: dict[str, object] = {
        "N": 3,
        "N+1": 4,
        "N+2": 5,
        "stale_http_status": 409,
        "stale_mutation_accepted": False,
        "conflict_boundary_reached": True,
        "stale_revision_delta": 0,
        "stale_lifecycle_success_delta": 0,
        "stale_work_delta": 0,
        "stale_listing_comparison_delta": 0,
        "stale_notification_outbox_delta": 0,
        "stale_provider_call_delta": 0,
        "fresh_reload_version": 4,
        "final_version": 5,
        "final_fresh_revision_delta": 1,
        "stale_value_absent": True,
        "concurrent_value_survived_stale_rejection": True,
        "fresh_value_authoritative_after_fresh_submission": True,
        "direct_Web_business_DML": False,
        "direct_foreign_module_DML": False,
        "owner_bypass_DML": False,
        "raw_provider_payload_persisted": False,
        "production_personal_data": False,
        "credential_exposure": False,
        "live_provider_calls": 0,
        "form_contract": {
            "expected_row_version_server_read": True,
            "single_expected_row_version": True,
            "extra_authority_fields_rejected": True,
            "client_validation_not_authority": True,
        },
    }
    return {
        "identity": {"technical_id": "RF24-STALE-WEB-FORM-SCENARIO-01", "source_sha": "a" * 40},
        "phases": [{"phase": f"S{i}"} for i in range(9)],
        "summary": summary,
    }


def test_verifier_accepts_complete_stale_web_invariants() -> None:
    verify(_evidence(), "a" * 40)


@pytest.mark.parametrize("key", ["stale_http_status", "N+1", "final_fresh_revision_delta"])
def test_verifier_rejects_mutated_critical_fact(key: str) -> None:
    data = copy.deepcopy(_evidence())
    data["summary"][key] = 400 if key == "stale_http_status" else 99  # type: ignore[index]
    with pytest.raises(AssertionError):
        verify(data, "a" * 40)
