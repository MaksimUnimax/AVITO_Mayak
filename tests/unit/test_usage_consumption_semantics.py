from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from mayak.modules.entitlements_and_billing import (
    APPROVED_USAGE_COUNTER_FAMILIES,
    BASIC_TARIFF_POLICY,
    BEACON_MANAGEMENT_MODULE_LABEL,
    BLOCKED_USAGE_COUNTER_FAMILIES,
    FREE_TARIFF_POLICY,
    FUTURE_DECISION_GATES,
    SCAN_ORCHESTRATION_MODULE_LABEL,
    ActiveBeaconSlotEvidence,
    ScanIntervalTimingEvidence,
    UsageConsumptionCommitState,
    UsageConsumptionIdempotencyRecord,
    UsageConsumptionOutcome,
    UsageConsumptionRequest,
    UsageCounterFamily,
    compute_usage_consumption_request_fingerprint,
    evaluate_usage_consumption,
)
from mayak.platform.idempotency import IdempotencyKey


DECISION_AT = datetime(2026, 7, 8, 10, 0, tzinfo=timezone.utc)
TARGET_ACCOUNT_ID = "acct-eb06-usage-001"
ACTIVE_BEACON_LIMIT_ONE = 1


def _active_beacon_request(
    *,
    tariff_definition=FREE_TARIFF_POLICY,
    active_beacon_count: int = 1,
    source_fact_active_beacon_count: int | None = None,
    idempotency_key: IdempotencyKey | None = None,
    prior_idempotency_record: UsageConsumptionIdempotencyRecord | None = None,
    commit_state: UsageConsumptionCommitState | None = None,
) -> UsageConsumptionRequest:
    return UsageConsumptionRequest(
        account_id=TARGET_ACCOUNT_ID,
        counter_family=UsageCounterFamily.ACTIVE_BEACON_SLOT.value,
        requester_module=BEACON_MANAGEMENT_MODULE_LABEL,
        source_facts_owner=BEACON_MANAGEMENT_MODULE_LABEL,
        decision_at=DECISION_AT,
        idempotency_key=idempotency_key,
        prior_idempotency_record=prior_idempotency_record,
        current_tariff_definition=tariff_definition,
        active_beacon_slot_evidence=ActiveBeaconSlotEvidence(
            snapshot_reference="beacon-snapshot-eb06-001",
            snapshot_active_beacon_count=active_beacon_count,
            source_fact_reference="beacon-source-eb06-001"
            if source_fact_active_beacon_count is not None
            else None,
            source_fact_active_beacon_count=source_fact_active_beacon_count,
        ),
        commit_state=commit_state,
    )


def _scan_interval_request(
    *,
    tariff_definition=FREE_TARIFF_POLICY,
    interval_minutes: int = 180,
    idempotency_key: IdempotencyKey | None = None,
    prior_idempotency_record: UsageConsumptionIdempotencyRecord | None = None,
    commit_state: UsageConsumptionCommitState | None = None,
    od011_safety_required: bool = False,
    missing_timing: bool = False,
) -> UsageConsumptionRequest:
    last_scan_at = DECISION_AT
    next_scan_at = DECISION_AT + timedelta(minutes=interval_minutes)
    return UsageConsumptionRequest(
        account_id=TARGET_ACCOUNT_ID,
        counter_family=UsageCounterFamily.SCAN_INTERVAL_WINDOW.value,
        requester_module=SCAN_ORCHESTRATION_MODULE_LABEL,
        source_facts_owner=SCAN_ORCHESTRATION_MODULE_LABEL,
        decision_at=DECISION_AT,
        idempotency_key=idempotency_key,
        prior_idempotency_record=prior_idempotency_record,
        current_tariff_definition=tariff_definition,
        scan_interval_timing_evidence=None
        if missing_timing
        else ScanIntervalTimingEvidence(
            evidence_reference="scan-timing-eb06-001",
            last_scan_at=last_scan_at,
            next_scan_at=next_scan_at,
            source_fact_interval_minutes=interval_minutes,
        ),
        commit_state=commit_state,
        od011_safety_required=od011_safety_required,
    )


def _module_source_text() -> str:
    return Path(
        __file__
    ).resolve().parents[2].joinpath(
        "src/mayak/modules/entitlements_and_billing/usage_consumption.py"
    ).read_text().lower()


def test_eb06_usage_counter_families_and_blocked_families_are_represented_001() -> None:
    assert [family.value for family in UsageCounterFamily] == [
        "ACTIVE_BEACON_SLOT",
        "SCAN_INTERVAL_WINDOW",
        "SCAN_COUNT_QUOTA",
        "NOTIFICATION_COUNT_QUOTA",
        "PAYMENT_RELATED_CONSUMPTION",
        "STORAGE_QUOTA",
        "PROVIDER_SPECIFIC_QUOTA",
        "MONETARY_PAYMENT_CONSUMPTION",
    ]
    assert APPROVED_USAGE_COUNTER_FAMILIES == (
        UsageCounterFamily.ACTIVE_BEACON_SLOT,
        UsageCounterFamily.SCAN_INTERVAL_WINDOW,
    )
    assert BLOCKED_USAGE_COUNTER_FAMILIES == (
        UsageCounterFamily.SCAN_COUNT_QUOTA,
        UsageCounterFamily.NOTIFICATION_COUNT_QUOTA,
        UsageCounterFamily.PAYMENT_RELATED_CONSUMPTION,
        UsageCounterFamily.STORAGE_QUOTA,
        UsageCounterFamily.PROVIDER_SPECIFIC_QUOTA,
        UsageCounterFamily.MONETARY_PAYMENT_CONSUMPTION,
    )
    assert BEACON_MANAGEMENT_MODULE_LABEL == "Beacon Management"
    assert SCAN_ORCHESTRATION_MODULE_LABEL == "Scan Orchestration"
    assert FREE_TARIFF_POLICY.active_beacon_limit == ACTIVE_BEACON_LIMIT_ONE
    assert BASIC_TARIFF_POLICY.active_beacon_limit is None


def test_eb06_usage_active_beacon_slot_free_accepted_001() -> None:
    request = _active_beacon_request(
        active_beacon_count=1,
        idempotency_key=IdempotencyKey(value="idem-eb06-active-free-001"),
    )
    decision = evaluate_usage_consumption(request)

    assert decision.outcome is UsageConsumptionOutcome.ACCEPTED
    assert decision.reason_code == "ACTIVE_BEACON_SLOT_ACCEPTED"
    assert decision.active_beacon_limit == 1
    assert decision.active_beacon_count == 1


def test_eb06_usage_active_beacon_slot_free_denied_001() -> None:
    request = _active_beacon_request(
        active_beacon_count=2,
        idempotency_key=IdempotencyKey(value="idem-eb06-active-free-002"),
    )
    decision = evaluate_usage_consumption(request)

    assert decision.outcome is UsageConsumptionOutcome.DENIED
    assert decision.reason_code == "ACTIVE_BEACON_SLOT_EXCEEDED"
    assert decision.active_beacon_limit == 1
    assert decision.active_beacon_count == 2


def test_eb06_usage_active_beacon_slot_basic_limit_gated_001() -> None:
    request = _active_beacon_request(
        tariff_definition=BASIC_TARIFF_POLICY,
        active_beacon_count=1,
        idempotency_key=IdempotencyKey(value="idem-eb06-active-basic-001"),
    )
    decision = evaluate_usage_consumption(request)

    assert decision.outcome is UsageConsumptionOutcome.BLOCKED
    assert decision.reason_code == "ACTIVE_BEACON_LIMIT_GATED"
    assert decision.current_tariff_name == "BASIC"


def test_eb06_usage_active_beacon_slot_missing_evidence_unavailable_001() -> None:
    request = UsageConsumptionRequest(
        account_id=TARGET_ACCOUNT_ID,
        counter_family=UsageCounterFamily.ACTIVE_BEACON_SLOT.value,
        requester_module=BEACON_MANAGEMENT_MODULE_LABEL,
        source_facts_owner=BEACON_MANAGEMENT_MODULE_LABEL,
        decision_at=DECISION_AT,
        idempotency_key=IdempotencyKey(value="idem-eb06-active-missing-001"),
        current_tariff_definition=FREE_TARIFF_POLICY,
    )
    decision = evaluate_usage_consumption(request)

    assert decision.outcome is UsageConsumptionOutcome.UNAVAILABLE
    assert decision.reason_code == "ACTIVE_BEACON_EVIDENCE_REQUIRED"


def test_eb06_usage_active_beacon_slot_conflict_001() -> None:
    request = _active_beacon_request(
        active_beacon_count=1,
        source_fact_active_beacon_count=2,
        idempotency_key=IdempotencyKey(value="idem-eb06-active-conflict-001"),
    )
    decision = evaluate_usage_consumption(request)

    assert decision.outcome is UsageConsumptionOutcome.CONFLICT
    assert decision.reason_code == "ACTIVE_BEACON_SOURCE_FACT_CONFLICT"


def test_eb06_usage_scan_interval_free_accepted_001() -> None:
    request = _scan_interval_request(
        interval_minutes=180,
        idempotency_key=IdempotencyKey(value="idem-eb06-scan-free-001"),
    )
    decision = evaluate_usage_consumption(request)

    assert decision.outcome is UsageConsumptionOutcome.ACCEPTED
    assert decision.reason_code == "SCAN_INTERVAL_WINDOW_ACCEPTED"
    assert decision.scan_interval_minutes == 180


def test_eb06_usage_scan_interval_free_denied_001() -> None:
    request = _scan_interval_request(
        interval_minutes=60,
        idempotency_key=IdempotencyKey(value="idem-eb06-scan-free-002"),
    )
    decision = evaluate_usage_consumption(request)

    assert decision.outcome is UsageConsumptionOutcome.DENIED
    assert decision.reason_code == "SCAN_INTERVAL_BELOW_FLOOR"
    assert decision.scan_interval_minutes == 60


def test_eb06_usage_scan_interval_basic_accepted_001() -> None:
    request = _scan_interval_request(
        tariff_definition=BASIC_TARIFF_POLICY,
        interval_minutes=5,
        idempotency_key=IdempotencyKey(value="idem-eb06-scan-basic-001"),
    )
    decision = evaluate_usage_consumption(request)

    assert decision.outcome is UsageConsumptionOutcome.ACCEPTED
    assert decision.reason_code == "SCAN_INTERVAL_WINDOW_ACCEPTED"
    assert decision.scan_interval_minutes == 5


def test_eb06_usage_scan_interval_od011_safety_blocked_001() -> None:
    request = _scan_interval_request(
        tariff_definition=BASIC_TARIFF_POLICY,
        interval_minutes=5,
        idempotency_key=IdempotencyKey(value="idem-eb06-scan-od011-001"),
        od011_safety_required=True,
    )
    decision = evaluate_usage_consumption(request)

    assert decision.outcome is UsageConsumptionOutcome.BLOCKED
    assert decision.reason_code == "OD011_SAFETY_REQUIRED"


def test_eb06_usage_scan_interval_missing_evidence_unavailable_001() -> None:
    request = _scan_interval_request(
        missing_timing=True,
        idempotency_key=IdempotencyKey(value="idem-eb06-scan-missing-001"),
    )
    decision = evaluate_usage_consumption(request)

    assert decision.outcome is UsageConsumptionOutcome.UNAVAILABLE
    assert decision.reason_code == "SCAN_INTERVAL_EVIDENCE_REQUIRED"


def test_eb06_usage_idempotent_replay_same_fingerprint_001() -> None:
    request = _active_beacon_request(
        idempotency_key=IdempotencyKey(value="idem-eb06-replay-001"),
    )
    fingerprint = compute_usage_consumption_request_fingerprint(request)
    prior = UsageConsumptionIdempotencyRecord(
        counter_family=request.counter_family,
        idempotency_key=request.idempotency_key,
        request_fingerprint=fingerprint,
        terminal_outcome=UsageConsumptionOutcome.ACCEPTED,
    )
    decision = evaluate_usage_consumption(request.model_copy(update={"prior_idempotency_record": prior}))

    assert decision.outcome is UsageConsumptionOutcome.REPLAYED
    assert decision.terminal_outcome is UsageConsumptionOutcome.ACCEPTED
    assert decision.reason_code == "IDEMPOTENT_REPLAY"


def test_eb06_usage_idempotency_mismatch_001() -> None:
    request = _active_beacon_request(
        idempotency_key=IdempotencyKey(value="idem-eb06-mismatch-001"),
    )
    prior = UsageConsumptionIdempotencyRecord(
        counter_family=request.counter_family,
        idempotency_key=request.idempotency_key,
        request_fingerprint=compute_usage_consumption_request_fingerprint(request),
        terminal_outcome=UsageConsumptionOutcome.ACCEPTED,
    )
    changed = request.model_copy(
        update={
            "active_beacon_slot_evidence": ActiveBeaconSlotEvidence(
                snapshot_reference="beacon-snapshot-eb06-002",
                snapshot_active_beacon_count=2,
            ),
            "prior_idempotency_record": prior,
        }
    )
    decision = evaluate_usage_consumption(changed)

    assert decision.outcome is UsageConsumptionOutcome.IDEMPOTENCY_MISMATCH
    assert decision.reason_code == "IDEMPOTENCY_MISMATCH"


def test_eb06_usage_missing_idempotency_rejected_001() -> None:
    request = _active_beacon_request(idempotency_key=None)
    decision = evaluate_usage_consumption(request)

    assert decision.outcome is UsageConsumptionOutcome.REJECTED
    assert decision.reason_code == "IDEMPOTENCY_KEY_REQUIRED"


def test_eb06_usage_unknown_commit_state_blocked_001() -> None:
    request = _active_beacon_request(
        idempotency_key=IdempotencyKey(value="idem-eb06-commit-001"),
        commit_state=UsageConsumptionCommitState.UNKNOWN,
    )
    decision = evaluate_usage_consumption(request)

    assert decision.outcome is UsageConsumptionOutcome.BLOCKED
    assert decision.reason_code == "UNKNOWN_COMMIT_STATE"


def test_eb06_usage_blocked_families_001() -> None:
    for family in BLOCKED_USAGE_COUNTER_FAMILIES:
        request = UsageConsumptionRequest(
            account_id=TARGET_ACCOUNT_ID,
            counter_family=family.value,
            requester_module=BEACON_MANAGEMENT_MODULE_LABEL,
            source_facts_owner=BEACON_MANAGEMENT_MODULE_LABEL,
            decision_at=DECISION_AT,
            idempotency_key=IdempotencyKey(value=f"idem-eb06-blocked-{family.value.lower()}"),
            current_tariff_definition=FREE_TARIFF_POLICY,
        )
        decision = evaluate_usage_consumption(request)

        assert decision.outcome is UsageConsumptionOutcome.BLOCKED
        assert decision.reason_code == "COUNTER_FAMILY_BLOCKED"


def test_eb06_usage_no_persistent_commit_001() -> None:
    request = _active_beacon_request(
        idempotency_key=IdempotencyKey(value="idem-eb06-commitless-001"),
    )
    decision = evaluate_usage_consumption(request)

    assert decision.history_preserved is True
    assert decision.event_candidate_ready is False
    assert "commit_store" not in type(request).model_fields
    assert "event_store" not in type(decision).model_fields
    assert "repository" not in type(request).model_fields
    assert "persistence" not in type(decision).model_fields


def test_eb06_usage_no_beacon_scan_notification_mutation_001() -> None:
    source_text = _module_source_text()
    forbidden_fragments = (
        "create beacons",
        "freeze beacons",
        "start scans",
        "run scans",
        "cancel scans",
        "notification delivery mutation",
        "notification sending",
        "admin ui",
        "web cabinet",
        "scheduler hook",
    )

    assert all(fragment not in source_text for fragment in forbidden_fragments)


def test_eb06_od010_od011_od013_remain_gated_001() -> None:
    assert FUTURE_DECISION_GATES == ("OD-010", "OD-011", "OD-013")
    blocked_decision = evaluate_usage_consumption(
        _scan_interval_request(
            tariff_definition=BASIC_TARIFF_POLICY,
            interval_minutes=5,
            idempotency_key=IdempotencyKey(value="idem-eb06-gates-001"),
            od011_safety_required=True,
        )
    )

    assert blocked_decision.outcome is UsageConsumptionOutcome.BLOCKED
    assert blocked_decision.reason_code == "OD011_SAFETY_REQUIRED"
    assert BASIC_TARIFF_POLICY.active_beacon_limit is None

