# ruff: noqa: E501, E701, E702
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[2]))

from mayak.runtime.rf24_scan_resilience import ACTION_BOUNDARIES, SCENARIO_NAMES, TECHNICAL_ID
from scripts.runtime.verify_rf24_scan_resilience import verify


def package() -> dict[str, object]:
    scenarios: dict[str, object] = {}
    for name in SCENARIO_NAMES:
        action: dict[str, object] = {"public_boundary": ACTION_BOUNDARIES[name], "actual_action_invoked": f"observed:{name}", "observation_source": "runtime-return-and-read-model"}
        after: dict[str, object] = {}
        if name == "worker-restart":
            action |= {"process_observed": True, "pid_1": 11, "pid_2": 12, "generation_1": "W1", "generation_2": "W2"}; after |= {"terminal_state": "SUCCEEDED_BASELINE", "duplicate_effect": False}
        elif name == "scheduler-restart":
            action |= {"process_observed": True, "pid_1": 21, "pid_2": 22, "generation_1": "S1", "generation_2": "S2"}; after |= {"materialized_work_count": 1, "persistent_schedule": True}
        elif name == "partial-parser":
            action["parser_outcome"] = "PARTIAL"; after |= {"scan_state": "PENDING_RECONCILIATION", "new_listing_delta": 0, "notification_effect_delta": 0}
        elif name == "captcha-restriction":
            action["parser_outcome"] = "CAPTCHA_OR_CHALLENGE"; after |= {"scan_state": "FAILED", "new_listing_delta": 0, "notification_effect_delta": 0}
        elif name == "route-failure":
            action |= {"route_selected": True, "route_failure_observed": True, "parser_success": False}; after |= {"new_listing_delta": 0, "notification_effect_delta": 0}
        elif name == "lost-lease":
            action |= {"owner_a": "A", "owner_b": "B", "stale_owner_rejected": True}; after["authoritative_owner"] = "B"
        else:
            after |= {"listing_known": True, "new_listing_delta": 0, "event_delta": 0, "notification_effect_delta": 0}
        raw = [{"technical_id": TECHNICAL_ID, "acceptance_run_id": "run-1", "process_kind": "mayak-worker", "process_pid": 101, "record_type": "worker_claim"}]
        if name == "scheduler-restart":
            raw = [{"technical_id": TECHNICAL_ID, "acceptance_run_id": "run-1", "process_kind": "mayak-scheduler", "process_pid": 201, "record_type": "scheduler_materialization", "materialized_count": 1, "work_item_id": "work"}]
        if name == "route-failure":
            raw.append({"technical_id": TECHNICAL_ID, "acceptance_run_id": "run-1", "process_kind": "mayak-worker", "process_pid": 101, "record_type": "egress_route_failure", "outcome": "FAILURE", "parser_correlation": "parser-1", "work_item_id": "work", "run_id": "run"})
        if name == "lost-lease":
            raw = [{"technical_id": TECHNICAL_ID, "acceptance_run_id": "run-1", "process_kind": "mayak-worker", "process_pid": pid, "record_type": record_type} for pid, record_type in ((301, "worker_claim"), (302, "worker_reclaim"), (301, "stale_terminal_attempt"), (301, "stale_terminal_rejected"), (302, "worker_terminal"))]
        owner_notification = {"source_intake": 0, "outbox_effect": 0, "delivery_attempt": 0, "observation_source": "notification-delivery-owned-read"}
        durable_before = {"authoritative_effect_count": 1, "observation_source": "owning-read-model", "scan_event_count": 0, "notification": owner_notification.copy()}
        durable_after = {"authoritative_effect_count": 1, "observation_source": "owning-read-model", "scan_event_count": 0, "notification": owner_notification.copy()}
        if name == "lost-lease": durable_after = {"authoritative_terminal_count": 1, "observation_source": "owning-read-model", "scan_event_count": 0, "notification": owner_notification.copy()}
        if name == "duplicate-listing": durable_before = {"listing_identity": "listing-1", "observation_source": "owning-read-model", "scan_event_count": 0, "notification": owner_notification.copy()}; durable_after = {"listing_identity": "listing-1", "observation_source": "owning-read-model", "scan_event_count": 0, "notification": owner_notification.copy()}
        if name == "route-failure": action["parser_attempt_id"] = "parser-1"
        scenarios[name] = {"scenario_name": name, "acceptance_run_id": "run-1", "source_sha": "a" * 40, "account_id": "account", "beacon_id": "beacon", "schedule_id": "schedule", "work_id": "work", "scan_run_id": "run", "before": {"state": "before"}, "action": action, "after": after, "raw_observations": raw, "durable_before": durable_before, "durable_after": durable_after, "notification_deltas": {"source_intake": 0, "outbox_effect": 0, "delivery_attempt": 0, "observation_source": "notification-delivery-owned-read"}}
    return {"technical_id": TECHNICAL_ID, "source_sha": "a" * 40, "source_sha_observation": {"observed_sha": "a" * 40, "expected_sha": "a" * 40}, "acceptance_run_id": "run-1", "scenarios": scenarios, "provider_live_calls": 0, "foreign_resource_impact": 0, "production_personal_data": 0, "credentials_exposure": False, "remaining_scenario_stubs": 0, "remaining_unwired_drivers": 0, "remaining_hardcoded_observed_values": 0}


def write(tmp_path: Path, data: dict[str, object]) -> Path:
    path = tmp_path / "evidence.json"; path.write_text(json.dumps(data)); return path


def test_accepts_exact_resilience_matrix(tmp_path: Path) -> None:
    verify(write(tmp_path, package()), "a" * 40)


@pytest.mark.parametrize("mutation", ["missing", "same_pid", "partial_success", "route_success", "stale_owner", "duplicate_effect", "sha", "raw_missing", "durable_missing", "scheduler_zero"])
def test_rejects_adversarial_contracts(tmp_path: Path, mutation: str) -> None:
    data = package(); scenarios = data["scenarios"]; assert isinstance(scenarios, dict)
    if mutation == "missing": scenarios.pop("route-failure")
    elif mutation == "same_pid": scenarios["worker-restart"]["action"]["pid_2"] = 11
    elif mutation == "partial_success": scenarios["partial-parser"]["action"]["parser_outcome"] = "USABLE_RESPONSE"
    elif mutation == "route_success": scenarios["route-failure"]["action"]["parser_success"] = True
    elif mutation == "stale_owner": scenarios["lost-lease"]["raw_observations"] = scenarios["lost-lease"]["raw_observations"][:-1]
    elif mutation == "duplicate_effect": scenarios["duplicate-listing"]["after"]["event_delta"] = 1
    elif mutation == "raw_missing": scenarios["worker-restart"].pop("raw_observations")
    elif mutation == "durable_missing": scenarios["worker-restart"].pop("durable_after")
    elif mutation == "scheduler_zero": scenarios["scheduler-restart"]["raw_observations"][0]["materialized_count"] = 0
    else: data["source_sha"] = "b" * 40
    with pytest.raises(ValueError): verify(write(tmp_path, data), "a" * 40)
