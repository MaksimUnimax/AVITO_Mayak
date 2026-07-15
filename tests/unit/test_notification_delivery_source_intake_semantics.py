from __future__ import annotations

from mayak.contracts.idempotency import IdempotencyFingerprint, IdempotencyKey, IdempotencyScope
from mayak.modules.notification_delivery import (
    NotificationSourceEvent,
    NotificationSourceFamily,
    NotificationSourceIntakeStatus,
    NotificationSourceProducer,
    evaluate_notification_source_intake,
)


def _base_event(
    *,
    family: NotificationSourceFamily = NotificationSourceFamily.NEW_LISTINGS_FOUND,
    producer: NotificationSourceProducer = NotificationSourceProducer.SCAN_ORCHESTRATION,
    committed: bool = True,
    commit_reference: str | None = "commit-1",
    listing_count: int = 1,
    safe_listing_reference_ids: tuple[str, ...] = ("listing-1",),
    beacon_id: str | None = "beacon-1",
    scan_run_id: str | None = "scan-run-1",
    raw_provider_payload: bool = False,
    identity_ambiguous: bool = False,
    gate_approved: bool = False,
) -> NotificationSourceEvent:
    return NotificationSourceEvent(
        source_event_id="source-event-1",
        source_family=family,
        source_producer=producer,
        source_contract="scan.notification.v1",
        source_contract_version="1.0",
        source_fact_id="fact-1",
        source_committed=committed,
        source_commit_reference=commit_reference,
        account_id="account-1",
        beacon_id=beacon_id,
        scan_run_id=scan_run_id,
        listing_count=listing_count,
        safe_listing_reference_ids=safe_listing_reference_ids,
        correlation_id="corr-1",
        causation_id="cause-1",
        idempotency_key=IdempotencyKey(value="key-1"),
        idempotency_fingerprint=IdempotencyFingerprint(value="fingerprint-1"),
        idempotency_scope=IdempotencyScope(value="scope-1"),
        source_identity_ambiguous=identity_ambiguous,
        contains_raw_provider_payload=raw_provider_payload,
        service_access_gate_approved=gate_approved,
        evidence_reference_ids=("evidence-1",),
    )


def test_new_listings_are_accepted_and_safe_listing_references_are_preserved() -> None:
    safe_listing_reference_ids = tuple(f"listing-{index:02d}" for index in range(1, 21))
    event = _base_event(
        listing_count=20,
        safe_listing_reference_ids=safe_listing_reference_ids,
    )

    decision = evaluate_notification_source_intake(
        decision_id="decision-1",
        source_event=event,
        evidence_reference_ids=("decision-evidence-1",),
    )

    assert decision.status is NotificationSourceIntakeStatus.ACCEPTED_NOTIFICATION_CANDIDATE
    assert decision.source_accepted is True
    assert decision.notification_candidate is True
    assert decision.status_read_model_candidate is True
    assert decision.outbox_effect_authorized is False
    assert decision.delivery_attempt_authorized is False
    assert event.safe_listing_reference_ids == safe_listing_reference_ids
    assert len(event.safe_listing_reference_ids) == 20
    assert event.safe_listing_reference_ids[0] == "listing-01"
    assert event.safe_listing_reference_ids[-1] == "listing-20"


def test_recovery_result_with_listings_is_accepted() -> None:
    event = _base_event(
        family=NotificationSourceFamily.RECOVERY_SCAN_COMPLETED,
        listing_count=2,
        safe_listing_reference_ids=("listing-1", "listing-2"),
    )

    decision = evaluate_notification_source_intake(
        decision_id="decision-2",
        source_event=event,
        evidence_reference_ids=("decision-evidence-2",),
    )

    assert decision.status is NotificationSourceIntakeStatus.ACCEPTED_NOTIFICATION_CANDIDATE
    assert decision.reason_codes == ("source-accepted-recovery-result",)


def test_recovery_result_with_zero_listings_is_accepted() -> None:
    event = _base_event(
        family=NotificationSourceFamily.RECOVERY_SCAN_COMPLETED,
        listing_count=0,
        safe_listing_reference_ids=(),
    )

    decision = evaluate_notification_source_intake(
        decision_id="decision-3",
        source_event=event,
        evidence_reference_ids=("decision-evidence-3",),
    )

    assert decision.status is NotificationSourceIntakeStatus.ACCEPTED_NOTIFICATION_CANDIDATE
    assert decision.source_accepted is True


def test_external_unavailable_status_is_accepted() -> None:
    event = _base_event(
        family=NotificationSourceFamily.EXTERNAL_UNAVAILABLE_STATUS,
        listing_count=0,
        safe_listing_reference_ids=(),
    )

    decision = evaluate_notification_source_intake(
        decision_id="decision-4",
        source_event=event,
        evidence_reference_ids=("decision-evidence-4",),
    )

    assert decision.status is NotificationSourceIntakeStatus.ACCEPTED_NOTIFICATION_CANDIDATE
    assert decision.reason_codes == ("source-accepted-external-status",)


def test_lost_anchors_are_accepted_as_state_restored_and_not_confirmed_new() -> None:
    event = _base_event(
        family=NotificationSourceFamily.LOST_ANCHORS_RECOVERED,
        listing_count=1,
        safe_listing_reference_ids=("listing-1",),
    )

    decision = evaluate_notification_source_intake(
        decision_id="decision-5",
        source_event=event,
        evidence_reference_ids=("decision-evidence-5",),
    )

    assert decision.status is NotificationSourceIntakeStatus.ACCEPTED_NOTIFICATION_CANDIDATE
    assert decision.reason_codes == ("source-accepted-lost-anchors-state-restored",)


def test_no_new_is_accepted_as_status_only_not_notification_candidate() -> None:
    event = _base_event(
        family=NotificationSourceFamily.NO_NEW_LISTINGS_STATUS,
        listing_count=0,
        safe_listing_reference_ids=(),
    )

    decision = evaluate_notification_source_intake(
        decision_id="decision-6",
        source_event=event,
        evidence_reference_ids=("decision-evidence-6",),
    )

    assert decision.status is NotificationSourceIntakeStatus.ACCEPTED_STATUS_ONLY
    assert decision.source_accepted is True
    assert decision.notification_candidate is False
    assert decision.status_read_model_candidate is True


def test_service_access_fact_is_blocked_without_gate() -> None:
    event = _base_event(
        family=NotificationSourceFamily.APPROVED_SERVICE_ACCESS_FACT,
        producer=NotificationSourceProducer.ENTITLEMENTS_OR_BEACON,
        beacon_id=None,
        scan_run_id=None,
        listing_count=0,
        safe_listing_reference_ids=(),
    )

    decision = evaluate_notification_source_intake(
        decision_id="decision-7",
        source_event=event,
        evidence_reference_ids=("decision-evidence-7",),
    )

    assert decision.status is NotificationSourceIntakeStatus.BLOCKED_UPSTREAM_GATE
    assert decision.source_accepted is False
    assert decision.notification_candidate is False
    assert decision.status_read_model_candidate is False


def test_service_access_fact_is_accepted_with_gate() -> None:
    event = _base_event(
        family=NotificationSourceFamily.APPROVED_SERVICE_ACCESS_FACT,
        producer=NotificationSourceProducer.ENTITLEMENTS_OR_BEACON,
        beacon_id=None,
        scan_run_id=None,
        listing_count=0,
        safe_listing_reference_ids=(),
        gate_approved=True,
    )

    decision = evaluate_notification_source_intake(
        decision_id="decision-8",
        source_event=event,
        evidence_reference_ids=("decision-evidence-8",),
    )

    assert decision.status is NotificationSourceIntakeStatus.ACCEPTED_NOTIFICATION_CANDIDATE
    assert decision.reason_codes == ("source-accepted-service-access",)


def test_price_pair_is_rejected_as_disabled() -> None:
    event = _base_event(
        family=NotificationSourceFamily.LISTING_PRICE_PAIR_FIRST_SEEN,
        listing_count=1,
        safe_listing_reference_ids=("listing-1",),
    )

    decision = evaluate_notification_source_intake(
        decision_id="decision-9",
        source_event=event,
        evidence_reference_ids=("decision-evidence-9",),
    )

    assert decision.status is NotificationSourceIntakeStatus.REJECTED_DISABLED_SOURCE
    assert decision.reason_codes == ("source-disabled-price-change",)


def test_baseline_is_rejected() -> None:
    event = _base_event(
        family=NotificationSourceFamily.BEACON_BASELINE_ESTABLISHED,
        listing_count=0,
        safe_listing_reference_ids=(),
    )

    decision = evaluate_notification_source_intake(
        decision_id="decision-10",
        source_event=event,
        evidence_reference_ids=("decision-evidence-10",),
    )

    assert decision.status is NotificationSourceIntakeStatus.REJECTED_NON_NOTIFICATION_SOURCE
    assert decision.reason_codes == ("source-non-notification-baseline",)


def test_scan_planned_and_started_are_rejected() -> None:
    for family in (
        NotificationSourceFamily.SCAN_RUN_PLANNED,
        NotificationSourceFamily.SCAN_RUN_STARTED,
    ):
        event = _base_event(
            family=family,
            listing_count=0,
            safe_listing_reference_ids=(),
        )

        decision = evaluate_notification_source_intake(
            decision_id=f"decision-{family.value}",
            source_event=event,
            evidence_reference_ids=("decision-evidence-11",),
        )

        assert decision.status is NotificationSourceIntakeStatus.REJECTED_NON_NOTIFICATION_SOURCE
        assert decision.reason_codes == ("source-non-notification-scan-lifecycle",)


def test_parser_egress_and_provider_only_callbacks_are_rejected() -> None:
    cases = [
        (
            NotificationSourceFamily.PARSER_ONLY_OUTCOME,
            NotificationSourceProducer.PARSER_ADAPTER,
            ("source-non-notification-parser",),
        ),
        (
            NotificationSourceFamily.EGRESS_ONLY_OUTCOME,
            NotificationSourceProducer.EGRESS_ROUTING,
            ("source-non-notification-egress",),
        ),
        (
            NotificationSourceFamily.PROVIDER_ONLY_CALLBACK,
            NotificationSourceProducer.PROVIDER_ADAPTER,
            ("source-non-notification-provider-callback",),
        ),
    ]

    for family, producer, reason_codes in cases:
        event = _base_event(
            family=family,
            producer=producer,
            listing_count=0,
            safe_listing_reference_ids=(),
        )
        decision = evaluate_notification_source_intake(
            decision_id=f"decision-{family.value}",
            source_event=event,
            evidence_reference_ids=("decision-evidence-12",),
        )

        assert decision.status is NotificationSourceIntakeStatus.REJECTED_NON_NOTIFICATION_SOURCE
        assert decision.reason_codes == reason_codes


def test_uncommitted_source_is_rejected() -> None:
    event = _base_event(committed=False, commit_reference=None)

    decision = evaluate_notification_source_intake(
        decision_id="decision-13",
        source_event=event,
        evidence_reference_ids=("decision-evidence-13",),
    )

    assert decision.status is NotificationSourceIntakeStatus.REJECTED_UNCOMMITTED


def test_ambiguous_identity_is_rejected() -> None:
    event = _base_event(identity_ambiguous=True)

    decision = evaluate_notification_source_intake(
        decision_id="decision-14",
        source_event=event,
        evidence_reference_ids=("decision-evidence-14",),
    )

    assert decision.status is NotificationSourceIntakeStatus.REJECTED_AMBIGUOUS


def test_raw_provider_payload_flag_is_rejected() -> None:
    event = _base_event(raw_provider_payload=True)

    decision = evaluate_notification_source_intake(
        decision_id="decision-15",
        source_event=event,
        evidence_reference_ids=("decision-evidence-15",),
    )

    assert decision.status is NotificationSourceIntakeStatus.REJECTED_UNSAFE_PAYLOAD


def test_incorrect_producer_is_rejected() -> None:
    event = _base_event(
        family=NotificationSourceFamily.NEW_LISTINGS_FOUND,
        producer=NotificationSourceProducer.PARSER_ADAPTER,
    )

    decision = evaluate_notification_source_intake(
        decision_id="decision-16",
        source_event=event,
        evidence_reference_ids=("decision-evidence-16",),
    )

    assert decision.status is NotificationSourceIntakeStatus.REJECTED_INVALID_PRODUCER
    assert decision.reason_codes == ("source-producer-mismatch",)


def test_duplicate_safe_references_are_rejected() -> None:
    try:
        _base_event(
            safe_listing_reference_ids=("listing-1", "listing-1"),
            listing_count=2,
        )
    except ValueError as exc:
        assert "duplicate" in str(exc)
    else:
        raise AssertionError("duplicate safe listing references must be rejected")


def test_listing_count_reference_mismatch_is_rejected() -> None:
    try:
        _base_event(
            listing_count=2,
            safe_listing_reference_ids=("listing-1",),
        )
    except ValueError as exc:
        assert "match safe references" in str(exc)
    else:
        raise AssertionError("listing count/reference mismatch must be rejected")


def test_identical_semantic_input_returns_equal_decision() -> None:
    event = _base_event()

    decision_one = evaluate_notification_source_intake(
        decision_id="decision-17",
        source_event=event,
        evidence_reference_ids=("decision-evidence-17",),
    )
    decision_two = evaluate_notification_source_intake(
        decision_id="decision-17",
        source_event=event,
        evidence_reference_ids=("decision-evidence-17",),
    )

    assert decision_one == decision_two
    assert decision_one is not decision_two


def test_changed_fingerprint_remains_distinguishable_and_keeps_effects_disabled() -> None:
    event_one = _base_event()
    event_two = NotificationSourceEvent(
        source_event_id="source-event-1",
        source_family=NotificationSourceFamily.NEW_LISTINGS_FOUND,
        source_producer=NotificationSourceProducer.SCAN_ORCHESTRATION,
        source_contract="scan.notification.v1",
        source_contract_version="1.0",
        source_fact_id="fact-1",
        source_committed=True,
        source_commit_reference="commit-1",
        account_id="account-1",
        beacon_id="beacon-1",
        scan_run_id="scan-run-1",
        listing_count=1,
        safe_listing_reference_ids=("listing-1",),
        correlation_id="corr-1",
        causation_id="cause-1",
        idempotency_key=IdempotencyKey(value="key-1"),
        idempotency_fingerprint=IdempotencyFingerprint(value="fingerprint-2"),
        idempotency_scope=IdempotencyScope(value="scope-1"),
        source_identity_ambiguous=False,
        contains_raw_provider_payload=False,
        service_access_gate_approved=False,
        evidence_reference_ids=("evidence-1",),
    )

    decision_one = evaluate_notification_source_intake(
        decision_id="decision-18",
        source_event=event_one,
        evidence_reference_ids=("decision-evidence-18",),
    )
    decision_two = evaluate_notification_source_intake(
        decision_id="decision-18",
        source_event=event_two,
        evidence_reference_ids=("decision-evidence-18",),
    )

    assert decision_one != decision_two
    assert decision_two.outbox_effect_authorized is False
    assert decision_two.delivery_attempt_authorized is False


def test_all_decisions_keep_outbox_and_delivery_attempts_disabled() -> None:
    accepted_event = _base_event()
    rejected_event = _base_event(
        family=NotificationSourceFamily.BEACON_BASELINE_ESTABLISHED,
        listing_count=0,
        safe_listing_reference_ids=(),
    )

    decisions = (
        evaluate_notification_source_intake(
            decision_id="decision-19",
            source_event=accepted_event,
            evidence_reference_ids=("decision-evidence-19",),
        ),
        evaluate_notification_source_intake(
            decision_id="decision-20",
            source_event=rejected_event,
            evidence_reference_ids=("decision-evidence-20",),
        ),
    )

    for decision in decisions:
        assert decision.outbox_effect_authorized is False
        assert decision.delivery_attempt_authorized is False
