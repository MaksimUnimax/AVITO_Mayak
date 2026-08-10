from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from scripts.runtime.verify_rf24_expired_access import (
    ADVERSARIAL_CASES,
    PHASES,
    TECHNICAL_ID,
    verify,
)

SOURCE_SHA = "a" * 40
RUN_ID = "rf24-test-run"
_EXECUTED: list[str] = []


def valid() -> dict[str, Any]:
    common = {
        "account_id": "account-a",
        "grant_id": "grant-a",
        "beacon_id": "beacon-a",
        "schedule_id": "schedule-a",
        "acceptance_run_id": RUN_ID,
        "source_sha": SOURCE_SHA,
    }
    phases = [
        dict(common, phase=phase, timestamp=f"2030-01-01T00:00:0{i}+00:00")
        for i, phase in enumerate(PHASES)
    ]
    phases[1].update(
        effective_status="ALLOWED", tariff="BASIC", beacon_state="ACTIVE", cadence_seconds=300
    )
    phases[2].update(
        effective_status="DENIED",
        actionable_expiry=True,
        actionable_expired_grant_id="grant-a",
        beacon_state="FROZEN",
        system_actor="ENTITLEMENTS_AND_BILLING_SERVICE",
        actor_account_id=None,
        causation_reference="paid-expiry:grant-a",
        policy_source_reference="paid-basic-expiry-v1",
        freeze_effect_count=1,
        post_expiry_work_count=0,
    )
    phases[3].update(
        freeze_effect_count=1,
        beacon_row_version_delta=0,
        lifecycle_freeze_event_count=1,
        new_work_count=0,
    )
    phases[4].update(
        parser_delta=0,
        egress_delta=0,
        notification_provider_delta=0,
        work_state="BLOCKED_ACCESS_EXPIRED",
        comparison_effect_count=0,
        new_listing_event_count=0,
        notification_outbox_count=0,
    )
    phases[5].update(
        terminal_comparison_status="DENIED",
        parser_provider_observation_count=1,
        new_listing_event_count=0,
        notification_effect_count=0,
    )
    phases[6].update(
        customer_bypass_accepted=False,
        beacon_row_version_delta=0,
        lifecycle_event_count=0,
        new_work_count=0,
    )
    phases[7].update(
        free_grant_count=0,
        automatic_selection=False,
        automatic_activation=False,
        beacon_state="FROZEN",
    )
    phases[8].update(
        account_id="account-b",
        grant_id="grant-b",
        beacon_id="beacon-b",
        schedule_id="schedule-b",
        replacement_grant_id="grant-b",
        replacement_effective_status="ALLOWED",
        replacement_tariff="BASIC",
        stale_freeze=False,
        beacon_state="ACTIVE",
        scheduler_eligible=True,
    )
    return {
        "technical_id": TECHNICAL_ID,
        "source_sha": SOURCE_SHA,
        "acceptance_run_id": RUN_ID,
        "scenario_id": "expired-access",
        "phases": phases,
    }


def test_verifier_accepts_independently_constructed_valid_observations(tmp_path: Path) -> None:
    path = tmp_path / "evidence.json"
    path.write_text(json.dumps(valid()), encoding="utf-8")
    assert verify(path, SOURCE_SHA, RUN_ID)["status"] == "PASS"


@pytest.mark.parametrize("case", ADVERSARIAL_CASES, ids=lambda case: case.case_id)
def test_registered_adversarial_case_executes_owner(case, tmp_path: Path) -> None:
    document = copy.deepcopy(valid())
    case.mutator(document)
    path = tmp_path / f"{case.case_id}.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises((ValueError, KeyError, IndexError, TypeError)):
        verify(path, SOURCE_SHA, RUN_ID)
    _EXECUTED.append(case.case_id)


def test_registered_adversarial_cases_are_unique_and_all_executed() -> None:
    registered = {case.case_id for case in ADVERSARIAL_CASES}
    assert len(registered) == len(ADVERSARIAL_CASES)
    assert set(_EXECUTED) == registered
    Path("rf24-expired-access-adversarial-execution.json").write_text(
        json.dumps(
            {
                "technical_id": TECHNICAL_ID,
                "registered_ids": [case.case_id for case in ADVERSARIAL_CASES],
                "collected_ids": [case.case_id for case in ADVERSARIAL_CASES],
                "executed_ids": list(_EXECUTED),
                "accepted_tamper_count": 0,
                "executor": "pytest::test_registered_adversarial_case_executes_owner",
            },
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def pytest_sessionfinish(session, exitstatus: int) -> None:
    """Persist executor facts, never a producer-side registry count."""
    if exitstatus == 0 and set(_EXECUTED) == {case.case_id for case in ADVERSARIAL_CASES}:
        Path("rf24-expired-access-adversarial-execution.json").write_text(
            json.dumps(
                {
                    "technical_id": TECHNICAL_ID,
                    "registered_ids": [case.case_id for case in ADVERSARIAL_CASES],
                    "collected_ids": [case.case_id for case in ADVERSARIAL_CASES],
                    "executed_ids": list(_EXECUTED),
                    "accepted_tamper_count": 0,
                    "executor": "pytest::test_registered_adversarial_case_executes_owner",
                },
                sort_keys=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
