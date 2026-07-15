from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from typing import cast

import pytest
from pytest import raises

from mayak.contracts.idempotency import IdempotencyFingerprint, IdempotencyKey, IdempotencyScope
from mayak.modules.notification_delivery import (
    NotificationBeaconLifecycleStatus,
    NotificationChannelClass,
    NotificationChannelEligibilityEvidence,
    NotificationEligibilityContext,
    NotificationEligibilityDecision,
    NotificationEligibilityStatus,
    NotificationEntitlementStatus,
    NotificationNoNewMinimumFrequencyGateStatus,
    NotificationNoNewStatusAuthority,
    NotificationNoNewStatusDecisionStatus,
    NotificationNoNewStatusPolicyContext,
    NotificationNoNewStatusPolicyDecision,
    NotificationOutboxCreationDecision,
    NotificationRecoveryGraceEvidence,
    NotificationSourceEvent,
    NotificationSourceFamily,
    NotificationSourceIntakeDecision,
    NotificationSourceProducer,
    create_notification_outbox_item,
    evaluate_notification_eligibility,
    evaluate_notification_source_intake,
    plan_notification_delivery,
)
from mayak.modules.notification_delivery.delivery_plan import (
    NotificationDeliveryPlanAuthority,
    NotificationDeliveryPlanDecision,
    NotificationDeliveryPlanDecisionStatus,
)
from mayak.modules.notification_delivery.eligibility import NO_NEW_MINIMUM_FREQUENCY_MINUTES
from mayak.modules.notification_delivery.no_new_status import evaluate_no_new_status_policy

ACCOUNT_ID = "account-1"
BEACON_ID = "beacon-1"
SOURCE_FACT_ID = "fact-1"
SOURCE_EVENT_ID = "source-event-1"
SOURCE_COMMIT_REFERENCE = "commit-1"
SCAN_RUN_ID = "scan-run-1"
LAST_SUCCESSFUL_SCAN_REFERENCE_ID = "scan-success-1"
CONFIGURED_SCAN_INTERVAL_REFERENCE_ID = "scan-interval-1"


def _source_event(
    *,
    family: NotificationSourceFamily = NotificationSourceFamily.NO_NEW_LISTINGS_STATUS,
    account_id: str = ACCOUNT_ID,
    beacon_id: str | None = BEACON_ID,
    source_fact_id: str = SOURCE_FACT_ID,
    source_event_id: str = SOURCE_EVENT_ID,
    scan_run_id: str | None = SCAN_RUN_ID,
    source_producer: NotificationSourceProducer = NotificationSourceProducer.SCAN_ORCHESTRATION,
    listing_count: int = 0,
    safe_listing_reference_ids: tuple[str, ...] = (),
    committed: bool = True,
    commit_reference: str | None = SOURCE_COMMIT_REFERENCE,
    source_identity_ambiguous: bool = False,
    contains_raw_provider_payload: bool = False,
    service_access_gate_approved: bool = False,
) -> NotificationSourceEvent:
    return NotificationSourceEvent(
        source_event_id=source_event_id,
        source_family=family,
        source_producer=source_producer,
        source_contract="scan.notification.v1",
        source_contract_version="1.0",
        source_fact_id=source_fact_id,
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


def _source_intake_decision(
    event: NotificationSourceEvent,
    *,
    decision_id: str = "intake-1",
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


def _recovery_evidence() -> NotificationRecoveryGraceEvidence:
    return NotificationRecoveryGraceEvidence(
        problem_began_while_access_active=False,
        recovery_obligation_reference_id=None,
        recovery_result_already_consumed=False,
        beacon_frozen_due_to_access_expiry=False,
        evidence_reference_ids=("recovery-evidence-1",),
    )


def _eligibility_context(
    *,
    account_id: str = ACCOUNT_ID,
    beacon_id: str | None = BEACON_ID,
    lifecycle_status: NotificationBeaconLifecycleStatus = NotificationBeaconLifecycleStatus.ACTIVE,
    lifecycle_reference_id: str | None = "beacon-lifecycle-1",
    entitlement_status: NotificationEntitlementStatus = NotificationEntitlementStatus.ALLOWED,
    entitlement_reference_id: str | None = "entitlement-1",
    no_new_status_preference_enabled: bool = True,
    no_new_status_frequency_minutes: int | None = NO_NEW_MINIMUM_FREQUENCY_MINUTES,
    telegram_enabled_by_user: bool = True,
    telegram_target_reference_id: str | None = "telegram-target-1",
    telegram_target_verified: bool = True,
    telegram_target_available: bool = True,
    max_enabled_by_user: bool = True,
    max_target_reference_id: str | None = "max-target-1",
    max_target_verified: bool = True,
    max_target_available: bool = True,
    channel_evidence: tuple[NotificationChannelEligibilityEvidence, ...] | None = None,
) -> NotificationEligibilityContext:
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
        recovery_grace_evidence=_recovery_evidence(),
        evidence_reference_ids=("eligibility-context-evidence-1",),
    )


def _eligibility_decision(
    *,
    family: NotificationSourceFamily = NotificationSourceFamily.NO_NEW_LISTINGS_STATUS,
    account_id: str = ACCOUNT_ID,
    beacon_id: str | None = BEACON_ID,
    source_fact_id: str = SOURCE_FACT_ID,
    source_event_id: str = SOURCE_EVENT_ID,
    scan_run_id: str | None = SCAN_RUN_ID,
    source_commit_reference: str | None = SOURCE_COMMIT_REFERENCE,
    listing_count: int = 0,
    safe_listing_reference_ids: tuple[str, ...] = (),
    no_new_status_preference_enabled: bool = True,
    no_new_status_frequency_minutes: int | None = NO_NEW_MINIMUM_FREQUENCY_MINUTES,
    lifecycle_status: NotificationBeaconLifecycleStatus = NotificationBeaconLifecycleStatus.ACTIVE,
    entitlement_status: NotificationEntitlementStatus = NotificationEntitlementStatus.ALLOWED,
    telegram_enabled_by_user: bool = True,
    telegram_target_verified: bool = True,
    telegram_target_available: bool = True,
    max_enabled_by_user: bool = True,
    max_target_verified: bool = True,
    max_target_available: bool = True,
    channel_evidence: tuple[NotificationChannelEligibilityEvidence, ...] | None = None,
    decision_id: str = "eligibility-1",
) -> NotificationEligibilityDecision:
    event = _source_event(
        family=family,
        account_id=account_id,
        beacon_id=beacon_id,
        source_fact_id=source_fact_id,
        source_event_id=source_event_id,
        scan_run_id=scan_run_id,
        commit_reference=source_commit_reference,
        listing_count=listing_count,
        safe_listing_reference_ids=safe_listing_reference_ids,
    )
    intake_decision = _source_intake_decision(event)
    context = _eligibility_context(
        account_id=account_id,
        beacon_id=beacon_id,
        lifecycle_status=lifecycle_status,
        entitlement_status=entitlement_status,
        no_new_status_preference_enabled=no_new_status_preference_enabled,
        no_new_status_frequency_minutes=no_new_status_frequency_minutes,
        telegram_enabled_by_user=telegram_enabled_by_user,
        telegram_target_verified=telegram_target_verified,
        telegram_target_available=telegram_target_available,
        max_enabled_by_user=max_enabled_by_user,
        max_target_verified=max_target_verified,
        max_target_available=max_target_available,
        channel_evidence=channel_evidence,
    )
    return evaluate_notification_eligibility(
        decision_id=decision_id,
        source_intake_decision=intake_decision,
        context=context,
        evidence_reference_ids=("eligibility-evidence-1",),
    )


def _outbox_creation_decision(
    eligibility_decision: NotificationEligibilityDecision,
    *,
    decision_id: str = "outbox-1",
    outbox_item_id: str = "outbox-item-1",
    outbox_contract: str = "notification.delivery.no-new.v1",
    outbox_contract_version: str = "1.0",
) -> NotificationOutboxCreationDecision:
    return create_notification_outbox_item(
        decision_id=decision_id,
        outbox_item_id=outbox_item_id,
        outbox_contract=outbox_contract,
        outbox_contract_version=outbox_contract_version,
        eligibility_decision=eligibility_decision,
        idempotency_key=IdempotencyKey(value="outbox-key-1"),
        idempotency_fingerprint=IdempotencyFingerprint(value="outbox-fingerprint-1"),
        idempotency_scope=IdempotencyScope(value="outbox-scope-1"),
        existing_outbox_item=None,
        evidence_reference_ids=("outbox-evidence-1",),
    )


def _planned_delivery_plan_decision(
    outbox_creation_decision: NotificationOutboxCreationDecision,
    *,
    decision_id: str = "plan-1",
    delivery_plan_id: str = "delivery-plan-1",
    evidence_reference_ids: tuple[str, ...] = ("plan-evidence-1",),
) -> NotificationDeliveryPlanDecision:
    return plan_notification_delivery(
        decision_id=decision_id,
        delivery_plan_id=delivery_plan_id,
        outbox_creation_decision=outbox_creation_decision,
        evidence_reference_ids=evidence_reference_ids,
    )


def _blocked_delivery_plan_decision(
    outbox_creation_decision: NotificationOutboxCreationDecision,
    *,
    decision_id: str = "blocked-plan-1",
    status: NotificationDeliveryPlanDecisionStatus = (
        NotificationDeliveryPlanDecisionStatus.BLOCKED_NO_PUSH_CHANNEL
    ),
    reason_codes: tuple[str, ...] = ("delivery-plan-no-push-channel",),
    evidence_reference_ids: tuple[str, ...] = ("blocked-plan-evidence-1",),
) -> NotificationDeliveryPlanDecision:
    return NotificationDeliveryPlanDecision(
        decision_id=decision_id,
        authority=NotificationDeliveryPlanAuthority.NOTIFICATION_DELIVERY_SERVER,
        outbox_creation_decision=outbox_creation_decision,
        status=status,
        delivery_plan=None,
        plan_created=False,
        delivery_attempt_authorized=False,
        provider_mapping_authorized=False,
        reason_codes=reason_codes,
        evidence_reference_ids=evidence_reference_ids,
    )


def _policy_context(
    *,
    account_id: str = ACCOUNT_ID,
    beacon_id: str = BEACON_ID,
    last_successful_scan_reference_id: str = LAST_SUCCESSFUL_SCAN_REFERENCE_ID,
    no_new_status_fact_reference_id: str = SOURCE_FACT_ID,
    configured_scan_interval_reference_id: str = CONFIGURED_SCAN_INTERVAL_REFERENCE_ID,
    status_preference_enabled: bool = True,
    configured_status_frequency_minutes: int | None = NO_NEW_MINIMUM_FREQUENCY_MINUTES,
    last_no_new_status_notification_reference_id: str | None = None,
    minimum_frequency_gate_status: NotificationNoNewMinimumFrequencyGateStatus = (
        NotificationNoNewMinimumFrequencyGateStatus.NO_PRIOR_NOTIFICATION
    ),
    evidence_reference_ids: tuple[str, ...] = ("policy-context-evidence-1",),
) -> NotificationNoNewStatusPolicyContext:
    return NotificationNoNewStatusPolicyContext(
        account_id=account_id,
        beacon_id=beacon_id,
        last_successful_scan_reference_id=last_successful_scan_reference_id,
        no_new_status_fact_reference_id=no_new_status_fact_reference_id,
        configured_scan_interval_reference_id=configured_scan_interval_reference_id,
        status_preference_enabled=status_preference_enabled,
        configured_status_frequency_minutes=configured_status_frequency_minutes,
        last_no_new_status_notification_reference_id=last_no_new_status_notification_reference_id,
        minimum_frequency_gate_status=minimum_frequency_gate_status,
        evidence_reference_ids=evidence_reference_ids,
    )


def _policy_decision(
    *,
    decision_id: str,
    eligibility_decision: NotificationEligibilityDecision,
    delivery_plan_decision: NotificationDeliveryPlanDecision | None,
    context: NotificationNoNewStatusPolicyContext,
    status: NotificationNoNewStatusDecisionStatus,
    evidence_reference_ids: tuple[str, ...] = ("policy-evidence-1",),
) -> NotificationNoNewStatusPolicyDecision:
    decision = evaluate_no_new_status_policy(
        decision_id=decision_id,
        eligibility_decision=eligibility_decision,
        delivery_plan_decision=delivery_plan_decision,
        context=context,
        evidence_reference_ids=evidence_reference_ids,
    )
    assert decision.status is status
    return decision


def _assert_no_execution(decision: NotificationNoNewStatusPolicyDecision) -> None:
    assert decision.delivery_attempt_authorized is False
    assert decision.provider_mapping_authorized is False


def _assert_policy_rejection_preserves_inputs(
    *,
    decision_id: str,
    eligibility_decision: NotificationEligibilityDecision,
    delivery_plan_decision: NotificationDeliveryPlanDecision | None,
    context: NotificationNoNewStatusPolicyContext,
    evidence_reference_ids: tuple[str, ...] = ("policy-evidence-1",),
) -> None:
    eligibility_before = deepcopy(eligibility_decision)
    delivery_plan_before = deepcopy(delivery_plan_decision)
    context_before = deepcopy(context)

    with raises(ValueError):
        evaluate_no_new_status_policy(
            decision_id=decision_id,
            eligibility_decision=eligibility_decision,
            delivery_plan_decision=delivery_plan_decision,
            context=context,
            evidence_reference_ids=evidence_reference_ids,
        )

    assert eligibility_decision == eligibility_before
    assert delivery_plan_decision == delivery_plan_before
    assert context == context_before


def _dedupe_first_occurrence(*tuples: tuple[str, ...]) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []
    for items in tuples:
        for item in items:
            if item not in seen:
                seen.add(item)
                ordered.append(item)
    return tuple(ordered)


def test_preference_disabled_is_read_model_only_with_no_plan_and_no_push() -> None:
    eligibility_decision = _eligibility_decision(
        no_new_status_preference_enabled=False,
        no_new_status_frequency_minutes=None,
    )
    context = _policy_context(
        status_preference_enabled=False,
        configured_status_frequency_minutes=None,
        minimum_frequency_gate_status=NotificationNoNewMinimumFrequencyGateStatus.NOT_APPLICABLE,
    )

    decision = _policy_decision(
        decision_id="policy-1",
        eligibility_decision=eligibility_decision,
        delivery_plan_decision=None,
        context=context,
        status=NotificationNoNewStatusDecisionStatus.READ_MODEL_ONLY_PREFERENCE_DISABLED,
    )

    assert (
        decision.status is NotificationNoNewStatusDecisionStatus.READ_MODEL_ONLY_PREFERENCE_DISABLED
    )
    assert decision.status_read_model_eligible is True
    assert decision.push_status_work_eligible is False
    assert decision.delivery_plan_decision is None
    _assert_no_execution(decision)


def test_frequency_59_is_suppressed_and_read_model_only_with_no_plan() -> None:
    eligibility_decision = _eligibility_decision(
        no_new_status_preference_enabled=True,
        no_new_status_frequency_minutes=NO_NEW_MINIMUM_FREQUENCY_MINUTES - 1,
    )
    context = _policy_context(
        configured_status_frequency_minutes=NO_NEW_MINIMUM_FREQUENCY_MINUTES - 1,
        minimum_frequency_gate_status=NotificationNoNewMinimumFrequencyGateStatus.NOT_APPLICABLE,
    )

    decision = _policy_decision(
        decision_id="policy-2",
        eligibility_decision=eligibility_decision,
        delivery_plan_decision=None,
        context=context,
        status=NotificationNoNewStatusDecisionStatus.READ_MODEL_ONLY_FREQUENCY_BELOW_MINIMUM,
    )

    assert (
        decision.status
        is NotificationNoNewStatusDecisionStatus.READ_MODEL_ONLY_FREQUENCY_BELOW_MINIMUM
    )
    assert decision.status_read_model_eligible is True
    assert decision.push_status_work_eligible is False
    assert decision.delivery_plan_decision is None
    _assert_no_execution(decision)


def test_frequency_60_with_no_prior_notification_is_push_eligible() -> None:
    eligibility_decision = _eligibility_decision(
        no_new_status_preference_enabled=True,
        no_new_status_frequency_minutes=NO_NEW_MINIMUM_FREQUENCY_MINUTES,
    )
    outbox_creation_decision = _outbox_creation_decision(eligibility_decision)
    plan_decision = _planned_delivery_plan_decision(outbox_creation_decision)
    context = _policy_context(
        minimum_frequency_gate_status=NotificationNoNewMinimumFrequencyGateStatus.NO_PRIOR_NOTIFICATION,
        last_no_new_status_notification_reference_id=None,
    )
    eligibility_before = deepcopy(eligibility_decision)
    outbox_before = deepcopy(outbox_creation_decision)
    plan_before = deepcopy(plan_decision)
    context_before = deepcopy(context)

    decision = _policy_decision(
        decision_id="policy-3",
        eligibility_decision=eligibility_decision,
        delivery_plan_decision=plan_decision,
        context=context,
        status=NotificationNoNewStatusDecisionStatus.PUSH_STATUS_ELIGIBLE,
    )

    assert decision.status is NotificationNoNewStatusDecisionStatus.PUSH_STATUS_ELIGIBLE
    assert decision.status_read_model_eligible is True
    assert decision.push_status_work_eligible is True
    assert decision.delivery_plan_decision is plan_decision
    assert decision.eligibility_decision is eligibility_decision
    assert decision.context is context
    assert eligibility_decision == eligibility_before
    assert outbox_creation_decision == outbox_before
    assert plan_decision == plan_before
    assert context == context_before
    _assert_no_execution(decision)


def test_frequency_60_with_elapsed_history_is_push_eligible() -> None:
    eligibility_decision = _eligibility_decision(
        no_new_status_preference_enabled=True,
        no_new_status_frequency_minutes=NO_NEW_MINIMUM_FREQUENCY_MINUTES,
    )
    outbox_creation_decision = _outbox_creation_decision(eligibility_decision)
    plan_decision = _planned_delivery_plan_decision(outbox_creation_decision)
    context = _policy_context(
        minimum_frequency_gate_status=NotificationNoNewMinimumFrequencyGateStatus.MINIMUM_FREQUENCY_ELAPSED,
        last_no_new_status_notification_reference_id="no-new-status-notification-1",
    )

    decision = _policy_decision(
        decision_id="policy-4",
        eligibility_decision=eligibility_decision,
        delivery_plan_decision=plan_decision,
        context=context,
        status=NotificationNoNewStatusDecisionStatus.PUSH_STATUS_ELIGIBLE,
    )

    assert decision.status is NotificationNoNewStatusDecisionStatus.PUSH_STATUS_ELIGIBLE
    assert decision.push_status_work_eligible is True
    assert decision.status_read_model_eligible is True
    _assert_no_execution(decision)


def test_frequency_60_with_not_elapsed_history_is_read_model_only() -> None:
    eligibility_decision = _eligibility_decision(
        no_new_status_preference_enabled=True,
        no_new_status_frequency_minutes=NO_NEW_MINIMUM_FREQUENCY_MINUTES,
    )
    outbox_creation_decision = _outbox_creation_decision(eligibility_decision)
    plan_decision = _planned_delivery_plan_decision(outbox_creation_decision)
    context = _policy_context(
        minimum_frequency_gate_status=NotificationNoNewMinimumFrequencyGateStatus.MINIMUM_FREQUENCY_NOT_ELAPSED,
        last_no_new_status_notification_reference_id="no-new-status-notification-1",
    )

    decision = _policy_decision(
        decision_id="policy-5",
        eligibility_decision=eligibility_decision,
        delivery_plan_decision=plan_decision,
        context=context,
        status=NotificationNoNewStatusDecisionStatus.READ_MODEL_ONLY_MINIMUM_FREQUENCY_NOT_ELAPSED,
    )

    assert (
        decision.status
        is NotificationNoNewStatusDecisionStatus.READ_MODEL_ONLY_MINIMUM_FREQUENCY_NOT_ELAPSED
    )
    assert decision.status_read_model_eligible is True
    assert decision.push_status_work_eligible is False
    _assert_no_execution(decision)


def test_frequency_over_60_with_ambiguous_history_is_blocked() -> None:
    eligibility_decision = _eligibility_decision(
        no_new_status_preference_enabled=True,
        no_new_status_frequency_minutes=NO_NEW_MINIMUM_FREQUENCY_MINUTES + 1,
    )
    outbox_creation_decision = _outbox_creation_decision(eligibility_decision)
    plan_decision = _planned_delivery_plan_decision(outbox_creation_decision)
    context = _policy_context(
        configured_status_frequency_minutes=NO_NEW_MINIMUM_FREQUENCY_MINUTES + 1,
        minimum_frequency_gate_status=NotificationNoNewMinimumFrequencyGateStatus.AMBIGUOUS,
        last_no_new_status_notification_reference_id="no-new-status-notification-1",
    )

    decision = _policy_decision(
        decision_id="policy-6",
        eligibility_decision=eligibility_decision,
        delivery_plan_decision=plan_decision,
        context=context,
        status=NotificationNoNewStatusDecisionStatus.BLOCKED_MINIMUM_FREQUENCY_AMBIGUOUS,
    )

    assert (
        decision.status is NotificationNoNewStatusDecisionStatus.BLOCKED_MINIMUM_FREQUENCY_AMBIGUOUS
    )
    assert decision.status_read_model_eligible is True
    assert decision.push_status_work_eligible is False
    _assert_no_execution(decision)


def test_no_eligible_telegram_or_max_channels_is_read_model_only() -> None:
    eligibility_decision = _eligibility_decision(
        no_new_status_preference_enabled=True,
        no_new_status_frequency_minutes=NO_NEW_MINIMUM_FREQUENCY_MINUTES,
        telegram_enabled_by_user=False,
        telegram_target_verified=False,
        telegram_target_available=False,
        max_enabled_by_user=False,
        max_target_verified=False,
        max_target_available=False,
    )
    context = _policy_context(
        minimum_frequency_gate_status=NotificationNoNewMinimumFrequencyGateStatus.NO_PRIOR_NOTIFICATION,
        last_no_new_status_notification_reference_id=None,
    )

    decision = _policy_decision(
        decision_id="policy-7",
        eligibility_decision=eligibility_decision,
        delivery_plan_decision=None,
        context=context,
        status=NotificationNoNewStatusDecisionStatus.READ_MODEL_ONLY_NO_ELIGIBLE_PUSH_CHANNEL,
    )

    assert (
        decision.status
        is NotificationNoNewStatusDecisionStatus.READ_MODEL_ONLY_NO_ELIGIBLE_PUSH_CHANNEL
    )
    assert decision.status_read_model_eligible is True
    assert decision.push_status_work_eligible is False
    assert decision.delivery_plan_decision is None
    _assert_no_execution(decision)


@pytest.mark.parametrize("commit_reference", (None, "stale-commit-1"))
def test_uncommitted_no_new_source_is_rejected_before_effect(
    commit_reference: str | None,
) -> None:
    eligibility_decision = _eligibility_decision(
        no_new_status_preference_enabled=True,
        no_new_status_frequency_minutes=NO_NEW_MINIMUM_FREQUENCY_MINUTES,
    )
    source_intake_decision = eligibility_decision.source_intake_decision
    forged_source_event = replace(
        source_intake_decision.source_event,
        source_committed=False,
        source_commit_reference=commit_reference,
    )
    forged_source_intake_decision = replace(
        source_intake_decision,
        source_event=forged_source_event,
    )
    forged_eligibility_decision = replace(
        eligibility_decision,
        source_intake_decision=forged_source_intake_decision,
    )
    context = _policy_context(
        minimum_frequency_gate_status=NotificationNoNewMinimumFrequencyGateStatus.NO_PRIOR_NOTIFICATION,
        last_no_new_status_notification_reference_id=None,
    )

    _assert_policy_rejection_preserves_inputs(
        decision_id="policy-fault-source-uncommitted",
        eligibility_decision=forged_eligibility_decision,
        delivery_plan_decision=None,
        context=context,
    )


@pytest.mark.parametrize(
    ("field_name", "mutated_value"),
    (
        ("source_producer", NotificationSourceProducer.EGRESS_ROUTING),
        ("source_identity_ambiguous", True),
        ("contains_raw_provider_payload", True),
    ),
)
def test_forged_accepted_status_source_provenance_is_rejected_before_effect(
    field_name: str,
    mutated_value: object,
) -> None:
    eligibility_decision = _eligibility_decision(
        no_new_status_preference_enabled=True,
        no_new_status_frequency_minutes=NO_NEW_MINIMUM_FREQUENCY_MINUTES,
    )
    source_intake_decision = eligibility_decision.source_intake_decision
    source_event = source_intake_decision.source_event
    if field_name == "source_producer":
        forged_source_event = replace(
            source_event,
            source_producer=cast(NotificationSourceProducer, mutated_value),
        )
    elif field_name == "source_identity_ambiguous":
        forged_source_event = replace(
            source_event,
            source_identity_ambiguous=cast(bool, mutated_value),
        )
    else:
        forged_source_event = replace(
            source_event,
            contains_raw_provider_payload=cast(bool, mutated_value),
        )
    forged_source_intake_decision = replace(
        source_intake_decision,
        source_event=forged_source_event,
    )
    forged_eligibility_decision = replace(
        eligibility_decision,
        source_intake_decision=forged_source_intake_decision,
    )
    context = _policy_context(
        minimum_frequency_gate_status=NotificationNoNewMinimumFrequencyGateStatus.NO_PRIOR_NOTIFICATION,
        last_no_new_status_notification_reference_id=None,
    )

    _assert_policy_rejection_preserves_inputs(
        decision_id="policy-forged-source-provenance",
        eligibility_decision=forged_eligibility_decision,
        delivery_plan_decision=None,
        context=context,
    )


def test_forged_accepted_status_only_reason_is_rejected_before_effect() -> None:
    eligibility_decision = _eligibility_decision(
        no_new_status_preference_enabled=True,
        no_new_status_frequency_minutes=NO_NEW_MINIMUM_FREQUENCY_MINUTES,
    )
    source_intake_decision = eligibility_decision.source_intake_decision
    forged_source_intake_decision = replace(
        source_intake_decision,
        reason_codes=("source-accepted-status-only-no-new-forged",),
    )
    forged_eligibility_decision = replace(
        eligibility_decision,
        source_intake_decision=forged_source_intake_decision,
    )
    context = _policy_context(
        minimum_frequency_gate_status=NotificationNoNewMinimumFrequencyGateStatus.NO_PRIOR_NOTIFICATION,
        last_no_new_status_notification_reference_id=None,
    )

    _assert_policy_rejection_preserves_inputs(
        decision_id="policy-forged-source-reason",
        eligibility_decision=forged_eligibility_decision,
        delivery_plan_decision=None,
        context=context,
    )


def test_preference_disabled_swapped_reason_is_rejected_before_effect() -> None:
    eligibility_decision = _eligibility_decision(
        no_new_status_preference_enabled=False,
        no_new_status_frequency_minutes=None,
    )
    assert eligibility_decision.status is NotificationEligibilityStatus.SUPPRESSED_BY_PREFERENCE
    assert eligibility_decision.reason_codes == ("eligibility-no-new-preference-disabled",)
    forged_eligibility_decision = replace(
        eligibility_decision,
        reason_codes=("eligibility-no-new-frequency-below-minimum",),
    )
    context = _policy_context(
        status_preference_enabled=False,
        configured_status_frequency_minutes=None,
        minimum_frequency_gate_status=NotificationNoNewMinimumFrequencyGateStatus.NOT_APPLICABLE,
    )

    _assert_policy_rejection_preserves_inputs(
        decision_id="policy-swapped-preference-disabled-reason",
        eligibility_decision=forged_eligibility_decision,
        delivery_plan_decision=None,
        context=context,
    )


def test_frequency_59_swapped_reason_is_rejected_before_effect() -> None:
    eligibility_decision = _eligibility_decision(
        no_new_status_preference_enabled=True,
        no_new_status_frequency_minutes=NO_NEW_MINIMUM_FREQUENCY_MINUTES - 1,
    )
    assert eligibility_decision.status is NotificationEligibilityStatus.SUPPRESSED_BY_PREFERENCE
    assert eligibility_decision.reason_codes == ("eligibility-no-new-frequency-below-minimum",)
    forged_eligibility_decision = replace(
        eligibility_decision,
        reason_codes=("eligibility-no-new-preference-disabled",),
    )
    context = _policy_context(
        configured_status_frequency_minutes=NO_NEW_MINIMUM_FREQUENCY_MINUTES - 1,
        minimum_frequency_gate_status=NotificationNoNewMinimumFrequencyGateStatus.NOT_APPLICABLE,
    )

    _assert_policy_rejection_preserves_inputs(
        decision_id="policy-swapped-frequency-reason",
        eligibility_decision=forged_eligibility_decision,
        delivery_plan_decision=None,
        context=context,
    )


def test_eligible_swapped_reason_is_rejected_before_effect() -> None:
    eligibility_decision = _eligibility_decision(
        no_new_status_preference_enabled=True,
        no_new_status_frequency_minutes=NO_NEW_MINIMUM_FREQUENCY_MINUTES,
    )
    assert eligibility_decision.status is NotificationEligibilityStatus.ELIGIBLE
    assert eligibility_decision.reason_codes == ("eligibility-eligible",)
    forged_eligibility_decision = replace(
        eligibility_decision,
        reason_codes=("eligibility-no-eligible-push-channel",),
    )
    context = _policy_context(
        minimum_frequency_gate_status=NotificationNoNewMinimumFrequencyGateStatus.NO_PRIOR_NOTIFICATION,
        last_no_new_status_notification_reference_id=None,
    )

    _assert_policy_rejection_preserves_inputs(
        decision_id="policy-swapped-eligible-reason",
        eligibility_decision=forged_eligibility_decision,
        delivery_plan_decision=None,
        context=context,
    )


def test_no_eligible_push_channel_swapped_reason_is_rejected_before_effect() -> None:
    eligibility_decision = _eligibility_decision(
        no_new_status_preference_enabled=True,
        no_new_status_frequency_minutes=NO_NEW_MINIMUM_FREQUENCY_MINUTES,
        telegram_enabled_by_user=False,
        telegram_target_verified=False,
        telegram_target_available=False,
        max_enabled_by_user=False,
        max_target_verified=False,
        max_target_available=False,
    )
    assert (
        eligibility_decision.status
        is NotificationEligibilityStatus.BLOCKED_NO_ELIGIBLE_PUSH_CHANNEL
    )
    assert eligibility_decision.reason_codes == ("eligibility-no-eligible-push-channel",)
    forged_eligibility_decision = replace(
        eligibility_decision,
        reason_codes=("eligibility-eligible",),
    )
    context = _policy_context(
        minimum_frequency_gate_status=NotificationNoNewMinimumFrequencyGateStatus.NO_PRIOR_NOTIFICATION,
        last_no_new_status_notification_reference_id=None,
    )

    _assert_policy_rejection_preserves_inputs(
        decision_id="policy-swapped-no-channel-reason",
        eligibility_decision=forged_eligibility_decision,
        delivery_plan_decision=None,
        context=context,
    )


@pytest.mark.parametrize(
    ("lifecycle_status", "entitlement_status", "expected_status"),
    (
        (
            NotificationBeaconLifecycleStatus.PAUSED,
            NotificationEntitlementStatus.ALLOWED,
            NotificationEligibilityStatus.BLOCKED_BEACON_LIFECYCLE,
        ),
        (
            NotificationBeaconLifecycleStatus.ACTIVE,
            NotificationEntitlementStatus.DENIED,
            NotificationEligibilityStatus.BLOCKED_ENTITLEMENT,
        ),
    ),
)
def test_blocked_lifecycle_or_entitlement_is_blocked_eligibility(
    lifecycle_status: NotificationBeaconLifecycleStatus,
    entitlement_status: NotificationEntitlementStatus,
    expected_status: NotificationEligibilityStatus,
) -> None:
    eligibility_decision = _eligibility_decision(
        no_new_status_preference_enabled=True,
        no_new_status_frequency_minutes=NO_NEW_MINIMUM_FREQUENCY_MINUTES,
        lifecycle_status=lifecycle_status,
        entitlement_status=entitlement_status,
    )
    context = _policy_context(
        minimum_frequency_gate_status=NotificationNoNewMinimumFrequencyGateStatus.NO_PRIOR_NOTIFICATION,
        last_no_new_status_notification_reference_id=None,
    )

    decision = _policy_decision(
        decision_id="policy-8",
        eligibility_decision=eligibility_decision,
        delivery_plan_decision=None,
        context=context,
        status=NotificationNoNewStatusDecisionStatus.BLOCKED_ELIGIBILITY,
    )

    assert eligibility_decision.status is expected_status
    assert decision.status is NotificationNoNewStatusDecisionStatus.BLOCKED_ELIGIBILITY
    assert decision.status_read_model_eligible is eligibility_decision.status_read_model_eligible
    assert decision.push_status_work_eligible is False
    assert decision.delivery_plan_decision is None
    _assert_no_execution(decision)


def test_wrong_source_family_is_rejected_before_effect() -> None:
    eligibility_decision = _eligibility_decision(
        family=NotificationSourceFamily.NEW_LISTINGS_FOUND,
        beacon_id=BEACON_ID,
        source_fact_id="new-listings-fact-1",
        source_event_id="new-listings-source-event-1",
        scan_run_id="new-listings-scan-run-1",
        source_commit_reference=SOURCE_COMMIT_REFERENCE,
        listing_count=1,
        safe_listing_reference_ids=("listing-1",),
        no_new_status_preference_enabled=False,
        no_new_status_frequency_minutes=None,
    )
    context = _policy_context(
        status_preference_enabled=False,
        configured_status_frequency_minutes=None,
        minimum_frequency_gate_status=NotificationNoNewMinimumFrequencyGateStatus.NOT_APPLICABLE,
    )

    with raises(ValueError):
        _policy_decision(
            decision_id="policy-9",
            eligibility_decision=eligibility_decision,
            delivery_plan_decision=None,
            context=context,
            status=NotificationNoNewStatusDecisionStatus.BLOCKED_ELIGIBILITY,
        )


def test_account_mismatch_is_rejected() -> None:
    eligibility_decision = _eligibility_decision()
    context = _policy_context(account_id="account-2")

    with raises(ValueError):
        _policy_decision(
            decision_id="policy-mismatch-account",
            eligibility_decision=eligibility_decision,
            delivery_plan_decision=None,
            context=context,
            status=NotificationNoNewStatusDecisionStatus.BLOCKED_ELIGIBILITY,
        )


def test_beacon_mismatch_is_rejected() -> None:
    eligibility_decision = _eligibility_decision()
    context = _policy_context(beacon_id="beacon-2")

    with raises(ValueError):
        _policy_decision(
            decision_id="policy-mismatch-beacon",
            eligibility_decision=eligibility_decision,
            delivery_plan_decision=None,
            context=context,
            status=NotificationNoNewStatusDecisionStatus.BLOCKED_ELIGIBILITY,
        )


def test_source_fact_mismatch_is_rejected() -> None:
    eligibility_decision = _eligibility_decision()
    context = _policy_context(no_new_status_fact_reference_id="fact-2")

    with raises(ValueError):
        _policy_decision(
            decision_id="policy-mismatch-fact",
            eligibility_decision=eligibility_decision,
            delivery_plan_decision=None,
            context=context,
            status=NotificationNoNewStatusDecisionStatus.BLOCKED_ELIGIBILITY,
        )


def test_preference_mirror_mismatch_is_rejected() -> None:
    eligibility_decision = _eligibility_decision()
    context = _policy_context(
        status_preference_enabled=False,
        configured_status_frequency_minutes=None,
        minimum_frequency_gate_status=NotificationNoNewMinimumFrequencyGateStatus.NOT_APPLICABLE,
    )

    with raises(ValueError):
        _policy_decision(
            decision_id="policy-mirror-preference",
            eligibility_decision=eligibility_decision,
            delivery_plan_decision=None,
            context=context,
            status=NotificationNoNewStatusDecisionStatus.BLOCKED_ELIGIBILITY,
        )


def test_frequency_mirror_mismatch_is_rejected() -> None:
    eligibility_decision = _eligibility_decision()
    context = _policy_context(
        configured_status_frequency_minutes=NO_NEW_MINIMUM_FREQUENCY_MINUTES - 1,
        minimum_frequency_gate_status=NotificationNoNewMinimumFrequencyGateStatus.NOT_APPLICABLE,
    )

    with raises(ValueError):
        _policy_decision(
            decision_id="policy-mirror-frequency",
            eligibility_decision=eligibility_decision,
            delivery_plan_decision=None,
            context=context,
            status=NotificationNoNewStatusDecisionStatus.BLOCKED_ELIGIBILITY,
        )


def test_bool_as_configured_frequency_is_rejected() -> None:
    with raises(ValueError):
        _policy_context(
            status_preference_enabled=True,
            configured_status_frequency_minutes=True,
            minimum_frequency_gate_status=NotificationNoNewMinimumFrequencyGateStatus.NO_PRIOR_NOTIFICATION,
            last_no_new_status_notification_reference_id=None,
        )


def test_raw_strings_and_lookalikes_for_nd08_enums_are_rejected() -> None:
    eligibility_decision = _eligibility_decision()
    context = _policy_context()

    class AuthorityLookalike(str):
        pass

    class GateStatusLookalike(str):
        pass

    class DecisionStatusLookalike(str):
        pass

    with raises(ValueError):
        NotificationNoNewStatusPolicyContext(
            account_id=ACCOUNT_ID,
            beacon_id=BEACON_ID,
            last_successful_scan_reference_id=LAST_SUCCESSFUL_SCAN_REFERENCE_ID,
            no_new_status_fact_reference_id=SOURCE_FACT_ID,
            configured_scan_interval_reference_id=CONFIGURED_SCAN_INTERVAL_REFERENCE_ID,
            status_preference_enabled=True,
            configured_status_frequency_minutes=NO_NEW_MINIMUM_FREQUENCY_MINUTES,
            last_no_new_status_notification_reference_id=None,
            minimum_frequency_gate_status=cast(
                NotificationNoNewMinimumFrequencyGateStatus,
                GateStatusLookalike("NO_PRIOR_NOTIFICATION"),
            ),
            evidence_reference_ids=("gate-lookalike-evidence-1",),
        )

    with raises(ValueError):
        NotificationNoNewStatusPolicyDecision(
            decision_id="decision-lookalike-1",
            authority=cast(
                NotificationNoNewStatusAuthority,
                AuthorityLookalike("NOTIFICATION_DELIVERY_SERVER"),
            ),
            eligibility_decision=eligibility_decision,
            delivery_plan_decision=None,
            context=context,
            status=NotificationNoNewStatusDecisionStatus.BLOCKED_ELIGIBILITY,
            status_read_model_eligible=True,
            push_status_work_eligible=False,
            delivery_attempt_authorized=False,
            provider_mapping_authorized=False,
            reason_codes=("no-new-status-eligibility-blocked",),
            evidence_reference_ids=("authority-lookalike-evidence-1",),
        )

    with raises(ValueError):
        NotificationNoNewStatusPolicyDecision(
            decision_id="decision-lookalike-2",
            authority=NotificationNoNewStatusAuthority.NOTIFICATION_DELIVERY_SERVER,
            eligibility_decision=eligibility_decision,
            delivery_plan_decision=None,
            context=context,
            status=cast(
                NotificationNoNewStatusDecisionStatus,
                DecisionStatusLookalike("BLOCKED_ELIGIBILITY"),
            ),
            status_read_model_eligible=True,
            push_status_work_eligible=False,
            delivery_attempt_authorized=False,
            provider_mapping_authorized=False,
            reason_codes=("no-new-status-eligibility-blocked",),
            evidence_reference_ids=("status-lookalike-evidence-1",),
        )


def test_mismatched_delivery_plan_is_rejected() -> None:
    eligibility_decision = _eligibility_decision(
        no_new_status_preference_enabled=True,
        no_new_status_frequency_minutes=NO_NEW_MINIMUM_FREQUENCY_MINUTES,
    )
    other_eligibility_decision = _eligibility_decision(
        no_new_status_preference_enabled=True,
        no_new_status_frequency_minutes=NO_NEW_MINIMUM_FREQUENCY_MINUTES,
        decision_id="eligibility-2",
    )
    other_outbox_creation_decision = _outbox_creation_decision(
        other_eligibility_decision,
        decision_id="outbox-2",
        outbox_item_id="outbox-item-2",
    )
    unrelated_plan_decision = _planned_delivery_plan_decision(
        other_outbox_creation_decision,
        decision_id="plan-2",
        delivery_plan_id="delivery-plan-2",
    )
    context = _policy_context(
        minimum_frequency_gate_status=NotificationNoNewMinimumFrequencyGateStatus.NO_PRIOR_NOTIFICATION,
        last_no_new_status_notification_reference_id=None,
    )

    with raises(ValueError):
        _policy_decision(
            decision_id="policy-10",
            eligibility_decision=eligibility_decision,
            delivery_plan_decision=unrelated_plan_decision,
            context=context,
            status=NotificationNoNewStatusDecisionStatus.PUSH_STATUS_ELIGIBLE,
        )


def test_blocked_matching_channel_plan_is_blocked_channel_plan() -> None:
    eligibility_decision = _eligibility_decision(
        no_new_status_preference_enabled=True,
        no_new_status_frequency_minutes=NO_NEW_MINIMUM_FREQUENCY_MINUTES,
    )
    outbox_creation_decision = _outbox_creation_decision(eligibility_decision)
    blocked_plan_decision = _blocked_delivery_plan_decision(outbox_creation_decision)
    context = _policy_context(
        minimum_frequency_gate_status=NotificationNoNewMinimumFrequencyGateStatus.NO_PRIOR_NOTIFICATION,
        last_no_new_status_notification_reference_id=None,
    )

    decision = _policy_decision(
        decision_id="policy-11",
        eligibility_decision=eligibility_decision,
        delivery_plan_decision=blocked_plan_decision,
        context=context,
        status=NotificationNoNewStatusDecisionStatus.BLOCKED_CHANNEL_PLAN,
    )

    assert decision.status is NotificationNoNewStatusDecisionStatus.BLOCKED_CHANNEL_PLAN
    assert decision.delivery_plan_decision is blocked_plan_decision
    assert decision.status_read_model_eligible is True
    assert decision.push_status_work_eligible is False
    _assert_no_execution(decision)


def test_push_channel_projection_mismatch_is_rejected() -> None:
    eligibility_decision = _eligibility_decision(
        no_new_status_preference_enabled=True,
        no_new_status_frequency_minutes=NO_NEW_MINIMUM_FREQUENCY_MINUTES,
    )
    outbox_creation_decision = _outbox_creation_decision(eligibility_decision)
    plan_decision = _planned_delivery_plan_decision(outbox_creation_decision)
    delivery_plan = plan_decision.delivery_plan
    assert delivery_plan is not None

    object.__setattr__(
        delivery_plan,
        "push_channel_classes",
        (NotificationChannelClass.TELEGRAM,),
    )
    context = _policy_context(
        minimum_frequency_gate_status=NotificationNoNewMinimumFrequencyGateStatus.NO_PRIOR_NOTIFICATION,
        last_no_new_status_notification_reference_id=None,
    )

    with raises(ValueError):
        _policy_decision(
            decision_id="policy-12",
            eligibility_decision=eligibility_decision,
            delivery_plan_decision=plan_decision,
            context=context,
            status=NotificationNoNewStatusDecisionStatus.PUSH_STATUS_ELIGIBLE,
        )


def test_evidence_union_is_first_occurrence_and_deduplicated() -> None:
    eligibility_decision = _eligibility_decision(
        no_new_status_preference_enabled=True,
        no_new_status_frequency_minutes=NO_NEW_MINIMUM_FREQUENCY_MINUTES,
        decision_id="eligibility-evidence-1",
    )
    outbox_creation_decision = _outbox_creation_decision(
        eligibility_decision,
        decision_id="outbox-evidence-1",
        outbox_item_id="outbox-item-evidence-1",
    )
    plan_decision = _planned_delivery_plan_decision(
        outbox_creation_decision,
        decision_id="plan-evidence-1",
        delivery_plan_id="delivery-plan-evidence-1",
        evidence_reference_ids=("plan-evidence-1", "shared-evidence-1", "plan-evidence-2"),
    )
    context = _policy_context(
        minimum_frequency_gate_status=NotificationNoNewMinimumFrequencyGateStatus.NO_PRIOR_NOTIFICATION,
        last_no_new_status_notification_reference_id=None,
        evidence_reference_ids=(
            "shared-evidence-1",
            "context-evidence-1",
            "eligibility-evidence-1",
        ),
    )

    decision = _policy_decision(
        decision_id="policy-13",
        eligibility_decision=eligibility_decision,
        delivery_plan_decision=plan_decision,
        context=context,
        status=NotificationNoNewStatusDecisionStatus.PUSH_STATUS_ELIGIBLE,
        evidence_reference_ids=(
            "policy-evidence-1",
            "plan-evidence-1",
            "policy-evidence-2",
            "shared-evidence-1",
        ),
    )

    expected = _dedupe_first_occurrence(
        eligibility_decision.evidence_reference_ids,
        plan_decision.evidence_reference_ids,
        context.evidence_reference_ids,
        ("policy-evidence-1", "plan-evidence-1", "policy-evidence-2", "shared-evidence-1"),
    )
    assert decision.evidence_reference_ids == expected
    assert len(decision.evidence_reference_ids) == len(set(decision.evidence_reference_ids))
    _assert_no_execution(decision)


def test_not_elapsed_never_becomes_push_eligible() -> None:
    eligibility_decision = _eligibility_decision(
        no_new_status_preference_enabled=True,
        no_new_status_frequency_minutes=NO_NEW_MINIMUM_FREQUENCY_MINUTES,
    )
    outbox_creation_decision = _outbox_creation_decision(eligibility_decision)
    plan_decision = _planned_delivery_plan_decision(outbox_creation_decision)
    context = _policy_context(
        minimum_frequency_gate_status=NotificationNoNewMinimumFrequencyGateStatus.MINIMUM_FREQUENCY_NOT_ELAPSED,
        last_no_new_status_notification_reference_id="no-new-status-notification-1",
    )

    decision = _policy_decision(
        decision_id="policy-14",
        eligibility_decision=eligibility_decision,
        delivery_plan_decision=plan_decision,
        context=context,
        status=NotificationNoNewStatusDecisionStatus.READ_MODEL_ONLY_MINIMUM_FREQUENCY_NOT_ELAPSED,
    )

    assert (
        decision.status
        is NotificationNoNewStatusDecisionStatus.READ_MODEL_ONLY_MINIMUM_FREQUENCY_NOT_ELAPSED
    )
    assert decision.push_status_work_eligible is False
    assert decision.status_read_model_eligible is True
    _assert_no_execution(decision)


def test_ambiguous_never_becomes_push_eligible() -> None:
    eligibility_decision = _eligibility_decision(
        no_new_status_preference_enabled=True,
        no_new_status_frequency_minutes=NO_NEW_MINIMUM_FREQUENCY_MINUTES + 1,
    )
    outbox_creation_decision = _outbox_creation_decision(eligibility_decision)
    plan_decision = _planned_delivery_plan_decision(outbox_creation_decision)
    context = _policy_context(
        configured_status_frequency_minutes=NO_NEW_MINIMUM_FREQUENCY_MINUTES + 1,
        minimum_frequency_gate_status=NotificationNoNewMinimumFrequencyGateStatus.AMBIGUOUS,
        last_no_new_status_notification_reference_id="no-new-status-notification-1",
    )

    decision = _policy_decision(
        decision_id="policy-15",
        eligibility_decision=eligibility_decision,
        delivery_plan_decision=plan_decision,
        context=context,
        status=NotificationNoNewStatusDecisionStatus.BLOCKED_MINIMUM_FREQUENCY_AMBIGUOUS,
    )

    assert (
        decision.status is NotificationNoNewStatusDecisionStatus.BLOCKED_MINIMUM_FREQUENCY_AMBIGUOUS
    )
    assert decision.push_status_work_eligible is False
    _assert_no_execution(decision)


def test_preference_disabled_never_becomes_push_eligible() -> None:
    eligibility_decision = _eligibility_decision(
        no_new_status_preference_enabled=False,
        no_new_status_frequency_minutes=None,
    )
    context = _policy_context(
        status_preference_enabled=False,
        configured_status_frequency_minutes=None,
        minimum_frequency_gate_status=NotificationNoNewMinimumFrequencyGateStatus.NOT_APPLICABLE,
    )

    decision = _policy_decision(
        decision_id="policy-16",
        eligibility_decision=eligibility_decision,
        delivery_plan_decision=None,
        context=context,
        status=NotificationNoNewStatusDecisionStatus.READ_MODEL_ONLY_PREFERENCE_DISABLED,
    )

    assert (
        decision.status is NotificationNoNewStatusDecisionStatus.READ_MODEL_ONLY_PREFERENCE_DISABLED
    )
    assert decision.push_status_work_eligible is False
    assert decision.status_read_model_eligible is True
    _assert_no_execution(decision)
