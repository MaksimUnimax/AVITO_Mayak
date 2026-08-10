# ruff: noqa: E501, E701, E702
from __future__ import annotations

import json
import sys
from copy import deepcopy
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
        def row(pid: int, generation: str, record_type: str, **extra: object) -> dict[str, object]:
            return {"technical_id": TECHNICAL_ID, "acceptance_run_id": "run-1", "process_kind": "mayak-worker", "process_pid": pid, "process_generation": generation, "record_type": record_type, **extra}
        terminal = after.get("terminal_state", "FAILED")
        raw = [row(101, "worker-W", "worker_process_started"), row(101, "worker-W", "worker_claim", work_item_id="work"), row(101, "worker-W", "worker_terminal", work_item_id="work", run_id="run", terminal_state=terminal, parser_outcome=action.get("parser_outcome", "PARTIAL"), parser_attempt_id="parser-1"), row(101, "worker-W", "worker_process_stopped")]
        if name == "worker-restart":
            raw = [row(101, "W1", "worker_process_started"), row(101, "W1", "worker_claim", work_item_id="work"), row(101, "W1", "worker_controlled_hold", work_item_id="work"), row(101, "W1", "worker_process_stopped"), row(102, "W2", "worker_process_started"), row(102, "W2", "worker_claim", work_item_id="work"), row(102, "W2", "worker_reclaim", work_item_id="work"), row(102, "W2", "worker_terminal", work_item_id="work", run_id="run", terminal_state="SUCCEEDED_BASELINE"), row(102, "W2", "worker_process_stopped")]
        if name == "scheduler-restart":
            raw = [{"technical_id": TECHNICAL_ID, "acceptance_run_id": "run-1", "process_kind": "mayak-scheduler", "process_pid": pid, "process_generation": generation, "record_type": kind, **extra} for pid, generation, kind, extra in ((201, "S1", "scheduler_process_started", {}), (201, "S1", "scheduler_process_stopped", {}), (202, "S2", "scheduler_process_started", {}), (202, "S2", "scheduler_materialization", {"materialized_count": 1, "work_item_id": "work", "schedule_id": "schedule", "beacon_id": "beacon"}), (202, "S2", "scheduler_process_stopped", {}))]
        if name in {"partial-parser", "captcha-restriction"}:
            raw[2]["parser_outcome"] = "PARTIAL" if name == "partial-parser" else "CAPTCHA_OR_CHALLENGE"
            raw[2]["terminal_state"] = "PENDING_RECONCILIATION" if name == "partial-parser" else "FAILED"
            raw[0]["process_generation"] = raw[1]["process_generation"] = raw[2]["process_generation"] = raw[3]["process_generation"] = f"{name}-W"
        if name == "route-failure":
            for route_row in raw[:4]: route_row["process_generation"] = "route-failure-W"
            raw[2]["parser_outcome"] = "TRANSPORT_UNAVAILABLE"
            raw.append(row(101, "worker-W", "egress_route_failure", outcome="TRANSPORT_UNAVAILABLE", parser_correlation="parser-1", work_item_id="work", run_id="run"))
        if name == "lost-lease":
            raw = [row(pid, generation, record_type, work_item_id="work", **({"run_id": "run"} if record_type in {"worker_controlled_hold", "stale_terminal_attempt", "stale_terminal_rejected", "worker_terminal"} else {})) for pid, generation, record_type in ((301, "lost-A", "worker_process_started"), (301, "lost-A", "worker_claim"), (301, "lost-A", "worker_controlled_hold"), (302, "lost-B", "worker_process_started"), (302, "lost-B", "worker_claim"), (302, "lost-B", "worker_reclaim"), (302, "lost-B", "worker_controlled_hold"), (301, "lost-A", "stale_terminal_attempt"), (301, "lost-A", "stale_terminal_rejected"), (301, "lost-A", "worker_process_stopped"), (302, "lost-B", "worker_terminal"), (302, "lost-B", "worker_process_stopped"))]
        if name == "duplicate-listing":
            raw = [row(404, "duplicate-W", "worker_process_started"), row(404, "duplicate-W", "worker_claim", work_item_id="work"), row(404, "duplicate-W", "worker_terminal", work_item_id="work", run_id="run", terminal_state="SUCCEEDED_BASELINE"), row(404, "duplicate-W", "worker_process_stopped")]
        owner_notification = {"source_intake": 0, "outbox_effect": 0, "delivery_attempt": 0, "observation_source": "notification-delivery-owned-read"}
        durable_before = {"authoritative_effect_count": 1, "observation_source": "owning-read-model", "scan_event_count": 0, "notification": owner_notification.copy()}
        durable_after = {"authoritative_effect_count": 1, "observation_source": "owning-read-model", "scan_event_count": 0, "notification": owner_notification.copy()}
        if name == "lost-lease": durable_after = {"authoritative_terminal_run_count": 1, "observation_source": "owning-read-model", "scan_event_count": 0, "notification": owner_notification.copy()}
        if name == "scheduler-restart": durable_before |= {"schedule_exists": True, "work_count": 0}; durable_after |= {"schedule_exists": True, "work_count": 1}
        if name == "duplicate-listing": durable_before = {"listing_identity": "listing-1", "observation_source": "owning-read-model", "scan_event_count": 0, "notification": owner_notification.copy()}; durable_after = {"listing_identity": "listing-1", "observation_source": "owning-read-model", "scan_event_count": 0, "notification": owner_notification.copy()}
        if name == "route-failure": action["parser_attempt_id"] = "parser-1"
        if name in {"partial-parser", "captcha-restriction"}: durable_after["runs"] = [{"run_id": "run", "state": "PENDING_RECONCILIATION" if name == "partial-parser" else "FAILED"}]
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
    elif mutation == "same_pid": next(row for row in scenarios["worker-restart"]["raw_observations"] if row.get("process_generation") == "W2")["process_pid"] = 101
    elif mutation == "partial_success": next(row for row in scenarios["partial-parser"]["raw_observations"] if row.get("record_type") == "worker_terminal")["parser_outcome"] = "USABLE_RESPONSE"
    elif mutation == "route_success": scenarios["route-failure"]["raw_observations"] = [row for row in scenarios["route-failure"]["raw_observations"] if row.get("record_type") != "egress_route_failure"]
    elif mutation == "stale_owner": scenarios["lost-lease"]["raw_observations"] = scenarios["lost-lease"]["raw_observations"][:-1]
    elif mutation == "duplicate_effect": scenarios["duplicate-listing"]["durable_after"]["scan_event_count"] = 1
    elif mutation == "raw_missing": scenarios["worker-restart"].pop("raw_observations")
    elif mutation == "durable_missing": scenarios["worker-restart"].pop("durable_after")
    elif mutation == "scheduler_zero": next(row for row in scenarios["scheduler-restart"]["raw_observations"] if row.get("record_type") == "scheduler_materialization")["materialized_count"] = 0
    else: data["source_sha"] = "b" * 40
    with pytest.raises(ValueError): verify(write(tmp_path, data), "a" * 40)


@pytest.mark.parametrize("mutation", [
    "duplicate_wrong_owner", "lost_missing_attempt", "lost_unrelated_attempt",
    "lost_unrelated_rejection", "lost_wrong_terminal", "producer_stale_claim",
    "producer_terminal_count", "scheduler_missing_s1", "scheduler_wrong_work",
    "worker_wrong_work", "partial_raw_mismatch", "captcha_raw_mismatch",
    "route_wrong_work", "global_unrelated", "duplicate_terminal_missing",
])
def test_rejects_cross_scenario_and_producer_false_positives(tmp_path: Path, mutation: str) -> None:
    data = deepcopy(package()); scenarios = data["scenarios"]; assert isinstance(scenarios, dict)
    if mutation == "duplicate_wrong_owner": scenarios["duplicate-listing"]["raw_observations"] = [row for row in scenarios["lost-lease"]["raw_observations"] if row.get("record_type") in {"worker_process_started", "worker_claim", "worker_terminal", "worker_process_stopped"}]
    elif mutation == "lost_missing_attempt": scenarios["lost-lease"]["raw_observations"] = [row for row in scenarios["lost-lease"]["raw_observations"] if row.get("record_type") != "stale_terminal_attempt"]
    elif mutation == "lost_unrelated_attempt": next(row for row in scenarios["lost-lease"]["raw_observations"] if row.get("record_type") == "stale_terminal_attempt")["work_item_id"] = "other-work"
    elif mutation == "lost_unrelated_rejection": next(row for row in scenarios["lost-lease"]["raw_observations"] if row.get("record_type") == "stale_terminal_rejected")["work_item_id"] = "other-work"
    elif mutation == "lost_wrong_terminal": next(row for row in scenarios["lost-lease"]["raw_observations"] if row.get("record_type") == "worker_terminal")["run_id"] = "other-run"
    elif mutation == "producer_stale_claim": scenarios["lost-lease"]["action"]["stale_owner_rejected"] = True; scenarios["lost-lease"]["raw_observations"] = [row for row in scenarios["lost-lease"]["raw_observations"] if row.get("record_type") != "stale_terminal_rejected"]
    elif mutation == "producer_terminal_count": scenarios["lost-lease"]["action"]["authoritative_terminal_count"] = 1; scenarios["lost-lease"]["durable_after"]["authoritative_terminal_run_count"] = 2
    elif mutation == "scheduler_missing_s1": scenarios["scheduler-restart"]["raw_observations"] = [row for row in scenarios["scheduler-restart"]["raw_observations"] if row.get("process_generation") != "S1"]
    elif mutation == "scheduler_wrong_work": next(row for row in scenarios["scheduler-restart"]["raw_observations"] if row.get("record_type") == "scheduler_materialization")["work_item_id"] = "other-work"
    elif mutation == "worker_wrong_work": next(row for row in scenarios["worker-restart"]["raw_observations"] if row.get("record_type") == "worker_terminal")["work_item_id"] = "other-work"
    elif mutation == "partial_raw_mismatch": next(row for row in scenarios["partial-parser"]["raw_observations"] if row.get("record_type") == "worker_terminal")["parser_outcome"] = "USABLE_RESPONSE"
    elif mutation == "captcha_raw_mismatch": next(row for row in scenarios["captcha-restriction"]["raw_observations"] if row.get("record_type") == "worker_terminal")["parser_outcome"] = "PARTIAL"
    elif mutation == "route_wrong_work": next(row for row in scenarios["route-failure"]["raw_observations"] if row.get("record_type") == "egress_route_failure")["work_item_id"] = "other-work"
    elif mutation == "global_unrelated": scenarios["duplicate-listing"]["raw_observations"] = [{**row, "work_item_id": "other-work"} for row in scenarios["worker-restart"]["raw_observations"]]
    elif mutation == "duplicate_terminal_missing": scenarios["duplicate-listing"]["raw_observations"] = [row for row in scenarios["duplicate-listing"]["raw_observations"] if row.get("record_type") != "worker_terminal"]
    with pytest.raises(ValueError): verify(write(tmp_path, data), "a" * 40)


def test_producer_summary_flags_are_not_acceptance_authority(tmp_path: Path) -> None:
    data = package(); scenarios = data["scenarios"]; assert isinstance(scenarios, dict)
    scenarios["worker-restart"]["action"].update({"pid_1": 1, "pid_2": 1, "generation_1": "same", "generation_2": "same"})
    scenarios["partial-parser"]["action"]["parser_outcome"] = "USABLE_RESPONSE"
    scenarios["captcha-restriction"]["action"]["parser_outcome"] = "PARTIAL"
    scenarios["route-failure"]["action"].update({"route_failure_observed": False, "parser_success": True})
    verify(write(tmp_path, data), "a" * 40)
