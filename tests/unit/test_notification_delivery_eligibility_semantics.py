from __future__ import annotations

from pytest import raises

from mayak.contracts.idempotency import IdempotencyFingerprint, IdempotencyKey, IdempotencyScope
from mayak.modules.notification_delivery import (
    NotificationSourceEvent,
    NotificationSourceFamily,
    NotificationSourceIntakeDecision,
    NotificationSourceIntakeStatus,
    NotificationSourceProducer,
    evaluate_notification_source_intake,
)
from mayak.modules.notification_delivery.eligibility import (
    ND03_TASK_ID,
    NO_NEW_MINIMUM_FREQUENCY_MINUTES,
    NotificationBeaconLifecycleStatus,
    NotificationChannelClass,
    NotificationChannelEligibilityEvidence,
    NotificationEligibilityContext,
    NotificationEligibilityDecision,
    NotificationEligibilityStatus,
    NotificationEntitlementStatus,
    NotificationRecoveryGraceEvidence,
    evaluate_notification_eligibility,
)


def _source_event(
    *,
    family: NotificationSourceFamily = NotificationSourceFamily.NEW_LISTINGS_FOUND,
    producer: NotificationSourceProducer = NotificationSourceProducer.SCAN_ORCHESTRATION,
    account_id: str = "account-1",
    beacon_id: str | None = "beacon-1",
    scan_run_id: str | None = "scan-run-1",
    listing_count: int = 1,
    safe_listing_reference_ids: tuple[str, ...] = ("listing-1",),
    committed: bool = True,
    commit_reference: str | None = "commit-1",
    source_identity_ambiguous: bool = False,
    contains_raw_provider_payload: bool = False,
    service_access_gate_approved: bool = False,
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
        account_id=account_id,
        beacon_id=beacon_id,
        scan_run_id=scan_run_id,
        listing_count=listing_count,
        safe_listing_reference_ids=safe_listing_reference_ids,
        correlation_id="corr-1",
        causation_id="cause-1",
        idempotency_key=IdempotencyKey(value="key-1"),
        idempotency_fingerprint=IdempotencyFingerprint(value="fingerprint-1"),
        idempotency_scope=IdempotencyScope(value="scope-1"),
        source_identity_ambiguous=source_identity_ambiguous,
        contains_raw_provider_payload=contains_raw_provider_payload,
        service_access_gate_approved=service_access_gate_approved,
        evidence_reference_ids=("source-evidence-1",),
    )


def _accepted_intake_decision(
    event: NotificationSourceEvent,
    *,
    decision_id: str = "intake-decision-1",
) -> NotificationSourceIntakeDecision:
    return evaluate_notification_source_intake(
        decision_id=decision_id,
        source_event=event,
        evidence_reference_ids=("intake-evidence-1",),
    )


def _telegram_evidence(
    *,
    enabled_by_user: bool = True,
    target_reference_id: str | None = "telegram-target-1",
    target_verified: bool = True,
    target_available: bool = True,
    evidence_reference_ids: tuple[str, ...] = ("telegram-evidence-1",),
) -> NotificationChannelEligibilityEvidence:
    return NotificationChannelEligibilityEvidence(
        channel_class=NotificationChannelClass.TELEGRAM,
        enabled_by_user=enabled_by_user,
        target_reference_id=target_reference_id,
        target_verified=target_verified,
        target_available=target_available,
        evidence_reference_ids=evidence_reference_ids,
    )


def _max_evidence(
    *,
    enabled_by_user: bool = True,
    target_reference_id: str | None = "max-target-1",
    target_verified: bool = True,
    target_available: bool = True,
    evidence_reference_ids: tuple[str, ...] = ("max-evidence-1",),
) -> NotificationChannelEligibilityEvidence:
    return NotificationChannelEligibilityEvidence(
        channel_class=NotificationChannelClass.MAX,
        enabled_by_user=enabled_by_user,
        target_reference_id=target_reference_id,
        target_verified=target_verified,
        target_available=target_available,
        evidence_reference_ids=evidence_reference_ids,
    )


def _web_evidence() -> NotificationChannelEligibilityEvidence:
    return NotificationChannelEligibilityEvidence(
        channel_class=NotificationChannelClass.WEB_STATUS_READ_MODEL,
        enabled_by_user=True,
        target_reference_id=None,
        target_verified=False,
        target_available=False,
        evidence_reference_ids=("web-evidence-1",),
    )


def _recovery_evidence(
    *,
    problem_began_while_access_active: bool = False,
    recovery_obligation_reference_id: str | None = None,
    recovery_result_already_consumed: bool = False,
    beacon_frozen_due_to_access_expiry: bool = False,
    evidence_reference_ids: tuple[str, ...] = ("recovery-evidence-1",),
) -> NotificationRecoveryGraceEvidence:
    return NotificationRecoveryGraceEvidence(
        problem_began_while_access_active=problem_began_while_access_active,
        recovery_obligation_reference_id=recovery_obligation_reference_id,
        recovery_result_already_consumed=recovery_result_already_consumed,
        beacon_frozen_due_to_access_expiry=beacon_frozen_due_to_access_expiry,
        evidence_reference_ids=evidence_reference_ids,
    )


def _context(
    *,
    account_id: str = "account-1",
    beacon_id: str | None = "beacon-1",
    lifecycle_status: NotificationBeaconLifecycleStatus = NotificationBeaconLifecycleStatus.ACTIVE,
    lifecycle_reference_id: str | None = "beacon-lifecycle-1",
    entitlement_status: NotificationEntitlementStatus = NotificationEntitlementStatus.ALLOWED,
    entitlement_reference_id: str | None = "entitlement-1",
    no_new_status_preference_enabled: bool = False,
    no_new_status_frequency_minutes: int | None = None,
    telegram_enabled_by_user: bool = True,
    telegram_target_reference_id: str | None = "telegram-target-1",
    telegram_target_verified: bool = True,
    telegram_target_available: bool = True,
    max_enabled_by_user: bool = True,
    max_target_reference_id: str | None = "max-target-1",
    max_target_verified: bool = True,
    max_target_available: bool = True,
    recovery_grace_evidence: NotificationRecoveryGraceEvidence | None = None,
    channel_evidence: tuple[NotificationChannelEligibilityEvidence, ...] | None = None,
) -> NotificationEligibilityContext:
    if recovery_grace_evidence is None:
        recovery_grace_evidence = _recovery_evidence()
    if channel_evidence is None:
        channel_evidence = (
            _telegram_evidence(
                enabled_by_user=telegram_enabled_by_user,
                target_reference_id=telegram_target_reference_id,
                target_verified=telegram_target_verified,
                target_available=telegram_target_available,
            ),
            _max_evidence(
                enabled_by_user=max_enabled_by_user,
                target_reference_id=max_target_reference_id,
                target_verified=max_target_verified,
                target_available=max_target_available,
            ),
            _web_evidence(),
        )

    return NotificationEligibilityContext(
        account_id=account_id,
        beacon_id=beacon_id,
        beacon_lifecycle_status=lifecycle_status,
        beacon_lifecycle_reference_id=lifecycle_reference_id,
        entitlement_status=entitlement_status,
        entitlement_decision_reference_id=entitlement_reference_id,
        no_new_status_preference_enabled=no_new_status_preference_enabled,
        no_new_status_frequency_minutes=no_new_status_frequency_minutes,
        channel_evidence=channel_evidence,
        recovery_grace_evidence=recovery_grace_evidence,
        evidence_reference_ids=("context-evidence-1",),
    )


def _assert_no_effects(decision: NotificationEligibilityDecision) -> None:
    assert decision.outbox_effect_authorized is False
    assert decision.delivery_attempt_authorized is False


def test_accepted_new_listing_with_telegram_only_is_eligible() -> None:
    assert ND03_TASK_ID == "ND-03-ELIGIBILITY-PREFERENCES-20260715-004"
    source_event = _source_event()
    intake_decision = _accepted_intake_decision(source_event)
    context = _context(max_enabled_by_user=False)

    decision = evaluate_notification_eligibility(
        decision_id="eligibility-1",
        source_intake_decision=intake_decision,
        context=context,
        evidence_reference_ids=("eligibility-evidence-1",),
    )

    assert decision.status is NotificationEligibilityStatus.ELIGIBLE
    assert decision.eligible_push_channels == (NotificationChannelClass.TELEGRAM,)
    assert decision.channel_gate_decisions[0].status.name == "ELIGIBLE"
    assert decision.channel_gate_decisions[1].status.name == "DISABLED_BY_USER"
    assert decision.channel_gate_decisions[2].status.name == "READ_MODEL_ONLY"
    assert decision.recovery_grace_applied is False
    _assert_no_effects(decision)


def test_telegram_and_max_both_eligible_are_preserved_in_input_order() -> None:
    source_event = _source_event()
    intake_decision = _accepted_intake_decision(source_event)
    context = _context()

    decision = evaluate_notification_eligibility(
        decision_id="eligibility-2",
        source_intake_decision=intake_decision,
        context=context,
        evidence_reference_ids=("eligibility-evidence-2",),
    )

    assert decision.status is NotificationEligibilityStatus.ELIGIBLE
    assert decision.eligible_push_channels == (
        NotificationChannelClass.TELEGRAM,
        NotificationChannelClass.MAX,
    )
    assert tuple(gate.channel_class for gate in decision.channel_gate_decisions) == (
        NotificationChannelClass.TELEGRAM,
        NotificationChannelClass.MAX,
        NotificationChannelClass.WEB_STATUS_READ_MODEL,
    )
    assert tuple(gate.status.name for gate in decision.channel_gate_decisions) == (
        "ELIGIBLE",
        "ELIGIBLE",
        "READ_MODEL_ONLY",
    )
    _assert_no_effects(decision)


def test_no_primary_channel_selection_is_made() -> None:
    source_event = _source_event()
    intake_decision = _accepted_intake_decision(source_event)
    context = _context()

    decision = evaluate_notification_eligibility(
        decision_id="eligibility-3",
        source_intake_decision=intake_decision,
        context=context,
        evidence_reference_ids=("eligibility-evidence-3",),
    )

    assert decision.eligible_push_channels == (
        NotificationChannelClass.TELEGRAM,
        NotificationChannelClass.MAX,
    )
    assert decision.channel_gate_decisions[0].status is decision.channel_gate_decisions[1].status
    _assert_no_effects(decision)


def test_disabled_telegram_does_not_suppress_eligible_max() -> None:
    source_event = _source_event()
    intake_decision = _accepted_intake_decision(source_event)
    context = _context(
        telegram_enabled_by_user=False,
        max_enabled_by_user=True,
    )

    decision = evaluate_notification_eligibility(
        decision_id="eligibility-4",
        source_intake_decision=intake_decision,
        context=context,
        evidence_reference_ids=("eligibility-evidence-4",),
    )

    assert decision.status is NotificationEligibilityStatus.ELIGIBLE
    assert decision.eligible_push_channels == (NotificationChannelClass.MAX,)
    assert decision.channel_gate_decisions[0].status.name == "DISABLED_BY_USER"
    assert decision.channel_gate_decisions[1].status.name == "ELIGIBLE"
    _assert_no_effects(decision)


def test_unverified_target_is_blocked_per_channel() -> None:
    source_event = _source_event()
    intake_decision = _accepted_intake_decision(source_event)
    context = _context(
        telegram_target_verified=False,
        telegram_target_reference_id="telegram-target-1",
        max_enabled_by_user=True,
    )

    decision = evaluate_notification_eligibility(
        decision_id="eligibility-5",
        source_intake_decision=intake_decision,
        context=context,
        evidence_reference_ids=("eligibility-evidence-5",),
    )

    assert decision.status is NotificationEligibilityStatus.ELIGIBLE
    assert decision.eligible_push_channels == (NotificationChannelClass.MAX,)
    assert decision.channel_gate_decisions[0].status.name == "TARGET_UNVERIFIED"
    assert decision.channel_gate_decisions[1].status.name == "ELIGIBLE"
    _assert_no_effects(decision)


def test_unavailable_target_is_blocked_per_channel() -> None:
    source_event = _source_event()
    intake_decision = _accepted_intake_decision(source_event)
    context = _context(
        telegram_enabled_by_user=True,
        max_target_available=False,
        max_enabled_by_user=True,
    )

    decision = evaluate_notification_eligibility(
        decision_id="eligibility-6",
        source_intake_decision=intake_decision,
        context=context,
        evidence_reference_ids=("eligibility-evidence-6",),
    )

    assert decision.status is NotificationEligibilityStatus.ELIGIBLE
    assert decision.eligible_push_channels == (NotificationChannelClass.TELEGRAM,)
    assert decision.channel_gate_decisions[1].status.name == "TARGET_UNAVAILABLE"
    _assert_no_effects(decision)


def test_web_is_always_read_model_only() -> None:
    source_event = _source_event()
    intake_decision = _accepted_intake_decision(source_event)
    context = _context(channel_evidence=(_web_evidence(),))

    decision = evaluate_notification_eligibility(
        decision_id="eligibility-7",
        source_intake_decision=intake_decision,
        context=context,
        evidence_reference_ids=("eligibility-evidence-7",),
    )

    assert decision.status is NotificationEligibilityStatus.BLOCKED_NO_ELIGIBLE_PUSH_CHANNEL
    assert decision.eligible_push_channels == ()
    assert decision.channel_gate_decisions == (decision.channel_gate_decisions[0],)
    assert decision.channel_gate_decisions[0].status.name == "READ_MODEL_ONLY"
    assert decision.channel_gate_decisions[0].push_eligible is False
    _assert_no_effects(decision)


def test_no_eligible_push_channel_blocks_outbox_candidate_but_preserves_read_model() -> None:
    source_event = _source_event()
    intake_decision = _accepted_intake_decision(source_event)
    context = _context(
        telegram_enabled_by_user=False,
        max_enabled_by_user=False,
    )

    decision = evaluate_notification_eligibility(
        decision_id="eligibility-8",
        source_intake_decision=intake_decision,
        context=context,
        evidence_reference_ids=("eligibility-evidence-8",),
    )

    assert decision.status is NotificationEligibilityStatus.BLOCKED_NO_ELIGIBLE_PUSH_CHANNEL
    assert decision.source_eligible is True
    assert decision.status_read_model_eligible is True
    assert decision.outbox_candidate_eligible is False
    assert decision.eligible_push_channels == ()
    _assert_no_effects(decision)


def test_rejected_nd02_source_blocks_eligibility() -> None:
    source_event = _source_event(
        family=NotificationSourceFamily.BEACON_BASELINE_ESTABLISHED,
        beacon_id="beacon-1",
        listing_count=0,
        safe_listing_reference_ids=(),
    )
    intake_decision = _accepted_intake_decision(source_event)
    context = _context()

    decision = evaluate_notification_eligibility(
        decision_id="eligibility-9",
        source_intake_decision=intake_decision,
        context=context,
        evidence_reference_ids=("eligibility-evidence-9",),
    )

    assert intake_decision.status is NotificationSourceIntakeStatus.REJECTED_NON_NOTIFICATION_SOURCE
    assert decision.status is NotificationEligibilityStatus.BLOCKED_SOURCE_INTAKE
    assert decision.source_eligible is False
    assert decision.status_read_model_eligible is False
    assert decision.outbox_candidate_eligible is False
    _assert_no_effects(decision)


def test_account_mismatch_blocks() -> None:
    source_event = _source_event()
    intake_decision = _accepted_intake_decision(source_event)
    context = _context(account_id="account-other")

    decision = evaluate_notification_eligibility(
        decision_id="eligibility-10",
        source_intake_decision=intake_decision,
        context=context,
        evidence_reference_ids=("eligibility-evidence-10",),
    )

    assert decision.status is NotificationEligibilityStatus.BLOCKED_SCOPE_MISMATCH
    assert decision.source_eligible is False
    assert decision.status_read_model_eligible is False
    _assert_no_effects(decision)


def test_beacon_mismatch_blocks() -> None:
    source_event = _source_event()
    intake_decision = _accepted_intake_decision(source_event)
    context = _context(beacon_id="beacon-other")

    decision = evaluate_notification_eligibility(
        decision_id="eligibility-11",
        source_intake_decision=intake_decision,
        context=context,
        evidence_reference_ids=("eligibility-evidence-11",),
    )

    assert decision.status is NotificationEligibilityStatus.BLOCKED_SCOPE_MISMATCH
    assert decision.source_eligible is False
    assert decision.reason_codes == ("eligibility-beacon-scope-mismatch",)
    _assert_no_effects(decision)


def test_active_beacon_and_allowed_entitlement_pass() -> None:
    source_event = _source_event()
    intake_decision = _accepted_intake_decision(source_event)
    context = _context()

    decision = evaluate_notification_eligibility(
        decision_id="eligibility-12",
        source_intake_decision=intake_decision,
        context=context,
        evidence_reference_ids=("eligibility-evidence-12",),
    )

    assert decision.status is NotificationEligibilityStatus.ELIGIBLE
    assert decision.source_eligible is True
    assert decision.outbox_candidate_eligible is True
    assert decision.status_read_model_eligible is True
    _assert_no_effects(decision)


def test_lifecycle_blocks_normal_facts() -> None:
    for lifecycle_status in (
        NotificationBeaconLifecycleStatus.DRAFT,
        NotificationBeaconLifecycleStatus.READY,
        NotificationBeaconLifecycleStatus.PAUSED,
        NotificationBeaconLifecycleStatus.FROZEN,
        NotificationBeaconLifecycleStatus.ARCHIVED,
        NotificationBeaconLifecycleStatus.PERMANENTLY_DELETED,
    ):
        source_event = _source_event()
        intake_decision = _accepted_intake_decision(source_event)
        context = _context(lifecycle_status=lifecycle_status)

        decision = evaluate_notification_eligibility(
            decision_id=f"eligibility-lifecycle-{lifecycle_status.value}",
            source_intake_decision=intake_decision,
            context=context,
            evidence_reference_ids=("eligibility-evidence-13",),
        )

        assert decision.status is NotificationEligibilityStatus.BLOCKED_BEACON_LIFECYCLE
        assert decision.reason_codes == ("eligibility-beacon-lifecycle-not-active",)
        assert decision.source_eligible is False
        assert decision.status_read_model_eligible is True
        _assert_no_effects(decision)


def test_entitlement_blocks_normal_facts() -> None:
    for entitlement_status in (
        NotificationEntitlementStatus.DENIED,
        NotificationEntitlementStatus.BLOCKED,
        NotificationEntitlementStatus.EXPIRED,
        NotificationEntitlementStatus.UNSUPPORTED,
        NotificationEntitlementStatus.USER_CHOICE_REQUIRED,
        NotificationEntitlementStatus.FREE_COMPLIANCE_REQUIRED,
        NotificationEntitlementStatus.NOT_APPLICABLE,
    ):
        source_event = _source_event()
        intake_decision = _accepted_intake_decision(source_event)
        entitlement_reference_id = (
            None
            if entitlement_status is NotificationEntitlementStatus.NOT_APPLICABLE
            else "entitlement-1"
        )
        context = _context(
            entitlement_status=entitlement_status,
            entitlement_reference_id=entitlement_reference_id,
        )

        decision = evaluate_notification_eligibility(
            decision_id=f"eligibility-entitlement-{entitlement_status.value}",
            source_intake_decision=intake_decision,
            context=context,
            evidence_reference_ids=("eligibility-evidence-14",),
        )

        assert decision.status is NotificationEligibilityStatus.BLOCKED_ENTITLEMENT
        assert decision.reason_codes == ("eligibility-entitlement-not-allowed",)
        assert decision.source_eligible is False
        assert decision.status_read_model_eligible is True
        _assert_no_effects(decision)


def test_ambiguous_lifecycle_blocks() -> None:
    source_event = _source_event()
    intake_decision = _accepted_intake_decision(source_event)
    context = _context(lifecycle_status=NotificationBeaconLifecycleStatus.AMBIGUOUS)

    decision = evaluate_notification_eligibility(
        decision_id="eligibility-15",
        source_intake_decision=intake_decision,
        context=context,
        evidence_reference_ids=("eligibility-evidence-15",),
    )

    assert decision.status is NotificationEligibilityStatus.BLOCKED_AMBIGUOUS
    assert decision.reason_codes == ("eligibility-beacon-lifecycle-ambiguous",)
    assert decision.source_eligible is False
    _assert_no_effects(decision)


def test_ambiguous_and_conflicting_entitlement_blocks() -> None:
    for entitlement_status in (
        NotificationEntitlementStatus.AMBIGUOUS,
        NotificationEntitlementStatus.CONFLICT,
    ):
        source_event = _source_event()
        intake_decision = _accepted_intake_decision(source_event)
        context = _context(entitlement_status=entitlement_status)

        decision = evaluate_notification_eligibility(
            decision_id=f"eligibility-ambiguous-{entitlement_status.value}",
            source_intake_decision=intake_decision,
            context=context,
            evidence_reference_ids=("eligibility-evidence-16",),
        )

        assert decision.status is NotificationEligibilityStatus.BLOCKED_AMBIGUOUS
        assert decision.reason_codes == ("eligibility-entitlement-ambiguous",)
        assert decision.source_eligible is False
        _assert_no_effects(decision)


def test_no_new_preference_disabled_suppresses_push() -> None:
    source_event = _source_event(
        family=NotificationSourceFamily.NO_NEW_LISTINGS_STATUS,
        listing_count=0,
        safe_listing_reference_ids=(),
    )
    intake_decision = _accepted_intake_decision(source_event)
    context = _context(
        no_new_status_preference_enabled=False,
        no_new_status_frequency_minutes=None,
    )

    decision = evaluate_notification_eligibility(
        decision_id="eligibility-17",
        source_intake_decision=intake_decision,
        context=context,
        evidence_reference_ids=("eligibility-evidence-17",),
    )

    assert decision.status is NotificationEligibilityStatus.SUPPRESSED_BY_PREFERENCE
    assert decision.source_eligible is True
    assert decision.status_read_model_eligible is True
    assert decision.outbox_candidate_eligible is False
    _assert_no_effects(decision)


def test_no_new_enabled_at_59_minutes_suppresses_push() -> None:
    source_event = _source_event(
        family=NotificationSourceFamily.NO_NEW_LISTINGS_STATUS,
        listing_count=0,
        safe_listing_reference_ids=(),
    )
    intake_decision = _accepted_intake_decision(source_event)
    context = _context(
        no_new_status_preference_enabled=True,
        no_new_status_frequency_minutes=NO_NEW_MINIMUM_FREQUENCY_MINUTES - 1,
    )

    decision = evaluate_notification_eligibility(
        decision_id="eligibility-18",
        source_intake_decision=intake_decision,
        context=context,
        evidence_reference_ids=("eligibility-evidence-18",),
    )

    assert decision.status is NotificationEligibilityStatus.SUPPRESSED_BY_PREFERENCE
    assert decision.reason_codes == ("eligibility-no-new-frequency-below-minimum",)
    assert decision.source_eligible is True
    assert decision.status_read_model_eligible is True
    _assert_no_effects(decision)


def test_no_new_enabled_at_exactly_60_minutes_passes() -> None:
    source_event = _source_event(
        family=NotificationSourceFamily.NO_NEW_LISTINGS_STATUS,
        listing_count=0,
        safe_listing_reference_ids=(),
    )
    intake_decision = _accepted_intake_decision(source_event)
    context = _context(
        no_new_status_preference_enabled=True,
        no_new_status_frequency_minutes=NO_NEW_MINIMUM_FREQUENCY_MINUTES,
    )

    decision = evaluate_notification_eligibility(
        decision_id="eligibility-19",
        source_intake_decision=intake_decision,
        context=context,
        evidence_reference_ids=("eligibility-evidence-19",),
    )

    assert decision.status is NotificationEligibilityStatus.ELIGIBLE
    assert decision.source_eligible is True
    assert decision.outbox_candidate_eligible is True
    _assert_no_effects(decision)


def test_no_new_enabled_above_60_minutes_passes() -> None:
    source_event = _source_event(
        family=NotificationSourceFamily.NO_NEW_LISTINGS_STATUS,
        listing_count=0,
        safe_listing_reference_ids=(),
    )
    intake_decision = _accepted_intake_decision(source_event)
    context = _context(
        no_new_status_preference_enabled=True,
        no_new_status_frequency_minutes=NO_NEW_MINIMUM_FREQUENCY_MINUTES + 1,
    )

    decision = evaluate_notification_eligibility(
        decision_id="eligibility-20",
        source_intake_decision=intake_decision,
        context=context,
        evidence_reference_ids=("eligibility-evidence-20",),
    )

    assert decision.status is NotificationEligibilityStatus.ELIGIBLE
    assert decision.source_eligible is True
    _assert_no_effects(decision)


def test_non_no_new_context_cannot_carry_no_new_preference_values() -> None:
    source_event = _source_event()
    intake_decision = _accepted_intake_decision(source_event)
    context = _context(
        no_new_status_preference_enabled=True,
        no_new_status_frequency_minutes=NO_NEW_MINIMUM_FREQUENCY_MINUTES,
    )

    with raises(ValueError, match="non-no-new sources must not carry no-new preference values"):
        evaluate_notification_eligibility(
            decision_id="eligibility-21",
            source_intake_decision=intake_decision,
            context=context,
            evidence_reference_ids=("eligibility-evidence-21",),
        )


def test_service_access_fact_with_not_applicable_lifecycle_and_entitlement_passes() -> None:
    source_event = _source_event(
        family=NotificationSourceFamily.APPROVED_SERVICE_ACCESS_FACT,
        producer=NotificationSourceProducer.ENTITLEMENTS_OR_BEACON,
        beacon_id=None,
        scan_run_id=None,
        listing_count=0,
        safe_listing_reference_ids=(),
        service_access_gate_approved=True,
    )
    intake_decision = _accepted_intake_decision(source_event)
    context = _context(
        beacon_id=None,
        lifecycle_status=NotificationBeaconLifecycleStatus.NOT_APPLICABLE,
        lifecycle_reference_id=None,
        entitlement_status=NotificationEntitlementStatus.NOT_APPLICABLE,
        entitlement_reference_id=None,
        telegram_enabled_by_user=True,
        max_enabled_by_user=True,
    )

    decision = evaluate_notification_eligibility(
        decision_id="eligibility-22",
        source_intake_decision=intake_decision,
        context=context,
        evidence_reference_ids=("eligibility-evidence-22",),
    )

    assert decision.status is NotificationEligibilityStatus.ELIGIBLE
    assert decision.reason_codes == ("eligibility-service-access-eligible",)
    assert decision.source_eligible is True
    _assert_no_effects(decision)


def test_service_access_fact_cannot_carry_beacon_scope() -> None:
    source_event = _source_event(
        family=NotificationSourceFamily.APPROVED_SERVICE_ACCESS_FACT,
        producer=NotificationSourceProducer.ENTITLEMENTS_OR_BEACON,
        beacon_id=None,
        scan_run_id=None,
        listing_count=0,
        safe_listing_reference_ids=(),
        service_access_gate_approved=True,
    )
    intake_decision = _accepted_intake_decision(source_event)
    context = _context()

    decision = evaluate_notification_eligibility(
        decision_id="eligibility-23",
        source_intake_decision=intake_decision,
        context=context,
        evidence_reference_ids=("eligibility-evidence-23",),
    )

    assert decision.status is NotificationEligibilityStatus.BLOCKED_SCOPE_MISMATCH
    assert decision.reason_codes == ("eligibility-beacon-scope-mismatch",)
    _assert_no_effects(decision)


def test_recovery_grace_passes_with_expired_entitlement_and_active_beacon() -> None:
    source_event = _source_event(
        family=NotificationSourceFamily.RECOVERY_SCAN_COMPLETED,
        listing_count=1,
        safe_listing_reference_ids=("listing-1",),
    )
    intake_decision = _accepted_intake_decision(source_event)
    context = _context(
        entitlement_status=NotificationEntitlementStatus.EXPIRED,
        recovery_grace_evidence=_recovery_evidence(
            problem_began_while_access_active=True,
            recovery_obligation_reference_id="recovery-obligation-1",
            recovery_result_already_consumed=False,
            beacon_frozen_due_to_access_expiry=False,
        ),
    )

    decision = evaluate_notification_eligibility(
        decision_id="eligibility-24",
        source_intake_decision=intake_decision,
        context=context,
        evidence_reference_ids=("eligibility-evidence-24",),
    )

    assert decision.status is NotificationEligibilityStatus.ELIGIBLE_RECOVERY_GRACE
    assert decision.recovery_grace_applied is True
    assert decision.reason_codes == ("eligibility-recovery-grace-applied",)
    _assert_no_effects(decision)


def test_recovery_grace_passes_with_frozen_beacon_due_to_access_expiry() -> None:
    source_event = _source_event(
        family=NotificationSourceFamily.RECOVERY_SCAN_COMPLETED,
        listing_count=1,
        safe_listing_reference_ids=("listing-1",),
    )
    intake_decision = _accepted_intake_decision(source_event)
    context = _context(
        lifecycle_status=NotificationBeaconLifecycleStatus.FROZEN,
        entitlement_status=NotificationEntitlementStatus.USER_CHOICE_REQUIRED,
        recovery_grace_evidence=_recovery_evidence(
            problem_began_while_access_active=True,
            recovery_obligation_reference_id="recovery-obligation-2",
            recovery_result_already_consumed=False,
            beacon_frozen_due_to_access_expiry=True,
        ),
    )

    decision = evaluate_notification_eligibility(
        decision_id="eligibility-25",
        source_intake_decision=intake_decision,
        context=context,
        evidence_reference_ids=("eligibility-evidence-25",),
    )

    assert decision.status is NotificationEligibilityStatus.ELIGIBLE_RECOVERY_GRACE
    assert decision.recovery_grace_applied is True
    _assert_no_effects(decision)


def test_recovery_grace_fails_when_problem_did_not_begin_while_active() -> None:
    source_event = _source_event(
        family=NotificationSourceFamily.RECOVERY_SCAN_COMPLETED,
        listing_count=1,
        safe_listing_reference_ids=("listing-1",),
    )
    intake_decision = _accepted_intake_decision(source_event)
    context = _context(
        entitlement_status=NotificationEntitlementStatus.EXPIRED,
        recovery_grace_evidence=_recovery_evidence(
            problem_began_while_access_active=False,
            recovery_result_already_consumed=False,
        ),
    )

    decision = evaluate_notification_eligibility(
        decision_id="eligibility-26",
        source_intake_decision=intake_decision,
        context=context,
        evidence_reference_ids=("eligibility-evidence-26",),
    )

    assert decision.status is NotificationEligibilityStatus.BLOCKED_ENTITLEMENT
    assert decision.recovery_grace_applied is False
    _assert_no_effects(decision)


def test_recovery_grace_fails_after_result_consumed() -> None:
    source_event = _source_event(
        family=NotificationSourceFamily.RECOVERY_SCAN_COMPLETED,
        listing_count=1,
        safe_listing_reference_ids=("listing-1",),
    )
    intake_decision = _accepted_intake_decision(source_event)
    context = _context(
        entitlement_status=NotificationEntitlementStatus.EXPIRED,
        recovery_grace_evidence=_recovery_evidence(
            problem_began_while_access_active=True,
            recovery_obligation_reference_id="recovery-obligation-3",
            recovery_result_already_consumed=True,
        ),
    )

    decision = evaluate_notification_eligibility(
        decision_id="eligibility-27",
        source_intake_decision=intake_decision,
        context=context,
        evidence_reference_ids=("eligibility-evidence-27",),
    )

    assert decision.status is NotificationEligibilityStatus.BLOCKED_ENTITLEMENT
    assert decision.recovery_grace_applied is False
    _assert_no_effects(decision)


def test_recovery_grace_fails_without_obligation_reference() -> None:
    with raises(ValueError, match="requires an obligation reference"):
        _context(
            entitlement_status=NotificationEntitlementStatus.EXPIRED,
            recovery_grace_evidence=_recovery_evidence(
                problem_began_while_access_active=True,
                recovery_obligation_reference_id=None,
                recovery_result_already_consumed=False,
            ),
        )


def test_recovery_grace_fails_for_denied_entitlement() -> None:
    source_event = _source_event(
        family=NotificationSourceFamily.RECOVERY_SCAN_COMPLETED,
        listing_count=1,
        safe_listing_reference_ids=("listing-1",),
    )
    intake_decision = _accepted_intake_decision(source_event)
    context = _context(
        entitlement_status=NotificationEntitlementStatus.DENIED,
        recovery_grace_evidence=_recovery_evidence(
            problem_began_while_access_active=True,
            recovery_obligation_reference_id="recovery-obligation-4",
            recovery_result_already_consumed=False,
        ),
    )

    decision = evaluate_notification_eligibility(
        decision_id="eligibility-28",
        source_intake_decision=intake_decision,
        context=context,
        evidence_reference_ids=("eligibility-evidence-28",),
    )

    assert decision.status is NotificationEligibilityStatus.BLOCKED_ENTITLEMENT
    assert decision.recovery_grace_applied is False
    _assert_no_effects(decision)


def test_recovery_grace_does_not_apply_to_normal_new_listing_source() -> None:
    source_event = _source_event()
    intake_decision = _accepted_intake_decision(source_event)
    context = _context(
        recovery_grace_evidence=_recovery_evidence(
            problem_began_while_access_active=True,
            recovery_obligation_reference_id="recovery-obligation-5",
            recovery_result_already_consumed=False,
        ),
    )

    decision = evaluate_notification_eligibility(
        decision_id="eligibility-29",
        source_intake_decision=intake_decision,
        context=context,
        evidence_reference_ids=("eligibility-evidence-29",),
    )

    assert decision.status is NotificationEligibilityStatus.ELIGIBLE
    assert decision.recovery_grace_applied is False
    _assert_no_effects(decision)


def test_duplicate_channel_classes_are_rejected() -> None:
    with raises(ValueError, match="duplicate channel classes are not allowed"):
        _context(
            channel_evidence=(
                _telegram_evidence(),
                _telegram_evidence(evidence_reference_ids=("telegram-evidence-2",)),
                _web_evidence(),
            ),
        )


def test_missing_web_evidence_is_rejected() -> None:
    with raises(ValueError, match="exactly one web read model evidence item is required"):
        _context(
            channel_evidence=(
                _telegram_evidence(),
                _max_evidence(),
            ),
        )


def test_verified_push_target_without_reference_is_rejected() -> None:
    with raises(ValueError, match="verified push targets require a target reference"):
        _context(
            telegram_target_reference_id=None,
            telegram_target_verified=True,
        )


def test_deterministic_identical_input_returns_equal_decision() -> None:
    source_event = _source_event()
    intake_decision = _accepted_intake_decision(source_event)
    context = _context()

    decision_one = evaluate_notification_eligibility(
        decision_id="eligibility-30",
        source_intake_decision=intake_decision,
        context=context,
        evidence_reference_ids=("eligibility-evidence-30",),
    )
    decision_two = evaluate_notification_eligibility(
        decision_id="eligibility-30",
        source_intake_decision=intake_decision,
        context=context,
        evidence_reference_ids=("eligibility-evidence-30",),
    )

    assert decision_one == decision_two
    _assert_no_effects(decision_one)
    _assert_no_effects(decision_two)


def test_all_decisions_keep_outbox_effect_and_delivery_attempt_authorization_false() -> None:
    source_event = _source_event()
    intake_decision = _accepted_intake_decision(source_event)
    context = _context()

    decision = evaluate_notification_eligibility(
        decision_id="eligibility-31",
        source_intake_decision=intake_decision,
        context=context,
        evidence_reference_ids=("eligibility-evidence-31",),
    )

    _assert_no_effects(decision)
