from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.runtime.verify_rf24_expired_access import PHASES, TAMPER_IDS, verify


def valid():
    common = {"account_id": "a", "grant_id": "g", "beacon_id": "b"}
    phases = [dict(common, phase=x) for x in PHASES]
    phases[1].update(effective_status="ALLOWED", tariff="BASIC", beacon_state="ACTIVE")
    phases[2].update(
        effective_status="DENIED",
        actionable_expiry=True,
        beacon_state="FROZEN",
        system_actor="ENTITLEMENTS_AND_BILLING_SERVICE",
        actor_account_id=None,
        freeze_effect_count=1,
        post_expiry_work_count=0,
    )
    phases[3].update(freeze_effect_count=1, beacon_row_version_delta=0, new_work_count=0)
    phases[4].update(
        parser_delta=0,
        egress_delta=0,
        notification_provider_delta=0,
        work_state="BLOCKED_ACCESS_EXPIRED",
        comparison_effect_count=0,
    )
    phases[5].update(
        terminal_comparison_status="DENIED", new_listing_event_count=0, notification_effect_count=0
    )
    phases[6].update(
        customer_bypass_accepted=False, beacon_row_version_delta=0, lifecycle_event_count=0
    )
    phases[7].update(
        free_grant_count=0,
        automatic_selection=False,
        automatic_activation=False,
        beacon_state="FROZEN",
    )
    phases[8].update(
        replacement_effective_status="ALLOWED",
        replacement_tariff="BASIC",
        stale_freeze=False,
        scheduler_eligible=True,
    )
    return {
        "technical_id": "RF24-EXPIRED-ACCESS-SCENARIO-01",
        "source_sha": "a" * 40,
        "phases": phases,
        "tamper_matrix": {
            "registered": list(TAMPER_IDS),
            "collected": list(TAMPER_IDS),
            "executed": list(TAMPER_IDS),
            "accepted_tamper_count": 0,
        },
    }


def test_verifier_accepts_complete_matrix(tmp_path: Path):
    path = tmp_path / "evidence.json"
    path.write_text(json.dumps(valid()), encoding="utf-8")
    assert verify(path, "a" * 40)["status"] == "PASS"


@pytest.mark.parametrize(
    "mutation",
    [
        lambda d: d.update(source_sha="b" * 40),
        lambda d: d["phases"].pop(),
        lambda d: d["phases"][2].update(system_actor="CUSTOMER"),
        lambda d: d["tamper_matrix"].update(accepted_tamper_count=1),
    ],
)
def test_verifier_fails_closed(tmp_path: Path, mutation):
    data = valid()
    mutation(data)
    path = tmp_path / "evidence.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError):
        verify(path, "a" * 40)
