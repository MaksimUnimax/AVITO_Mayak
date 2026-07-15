from __future__ import annotations

from dataclasses import replace
from typing import Any, cast

import pytest

from mayak.modules.egress_routing import (
    PolicyFallbackTransportOutcomeBoundary,
    TransportAvailabilityOutcomeBoundary,
    TransportOutcomeCommitmentBoundary,
    TransportResponseFailureOutcomeBoundary,
    TransportResponsePresenceOutcomeBoundary,
)
from mayak.modules.notification_delivery import (
    NotificationAttempt,
    NotificationAttemptLifecycleStatus,
    NotificationAttemptPlanningStatus,
    NotificationBeaconLifecycleStatus,
    NotificationChannelClass,
    NotificationChannelEligibilityEvidence,
    NotificationDeliveryPlanDecision,
    NotificationEligibilityContext,
    NotificationEligibilityDecision,
    NotificationEntitlementStatus,
    NotificationOutboxCreationDecision,
    NotificationProviderOutcomeAcceptanceDecision,
    NotificationProviderOutcomeAcceptanceStatus,
    NotificationProviderOutcomeClass,
    NotificationProviderOutcomeReference,
    NotificationRecoveryGraceEvidence,
    NotificationSourceEvent,
    NotificationSourceFamily,
    NotificationSourceProducer,
    accept_notification_provider_outcome,
    create_notification_outbox_item,
    evaluate_notification_eligibility,
    evaluate_notification_source_intake,
    plan_notification_attempt,
    plan_notification_delivery,
)
from mayak.platform.idempotency import IdempotencyFingerprint, IdempotencyKey, IdempotencyScope


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


def _tuple_union(*tuples: tuple[str, ...]) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []
    for items in tuples:
        for item in items:
            if item not in seen:
                seen.add(item)
                ordered.append(item)
    return tuple(ordered)


def _source_event(
    *,
    committed: bool = True,
    raw_payload: bool = False,
    identity_ambiguous: bool = False,
    account_id: str = "account-1",
    beacon_id: str | None = "beacon-1",
    scan_run_id: str | None = "scan-run-1",
    safe_listing_reference_ids: tuple[str, ...] = ("listing-1", "listing-2"),
) -> NotificationSourceEvent:
    return NotificationSourceEvent(
        source_event_id="source-event-1",
        source_family=NotificationSourceFamily.NEW_LISTINGS_FOUND,
        source_producer=NotificationSourceProducer.SCAN_ORCHESTRATION,
        source_contract="scan.notification.v1",
        source_contract_version="1.0",
        source_fact_id="fact-1",
        source_committed=committed,
        source_commit_reference="commit-1" if committed else None,
        account_id=account_id,
        beacon_id=beacon_id,
        scan_run_id=scan_run_id,
        listing_count=len(safe_listing_reference_ids),
        safe_listing_reference_ids=safe_listing_reference_ids,
        correlation_id="corr-1",
        causation_id="cause-1",
        idempotency_key=IdempotencyKey(value="key-1"),
        idempotency_fingerprint=IdempotencyFingerprint(value="fingerprint-1"),
        idempotency_scope=IdempotencyScope(value="scope-1"),
        source_identity_ambiguous=identity_ambiguous,
        contains_raw_provider_payload=raw_payload,
        service_access_gate_approved=False,
        evidence_reference_ids=("source-evidence-1",),
    )


def _context(
    *,
    account_id: str = "account-1",
    beacon_id: str | None = "beacon-1",
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
        beacon_lifecycle_status=NotificationBeaconLifecycleStatus.ACTIVE,
        beacon_lifecycle_reference_id="beacon-lifecycle-1",
        entitlement_status=NotificationEntitlementStatus.ALLOWED,
        entitlement_decision_reference_id="entitlement-1",
        no_new_status_preference_enabled=False,
        no_new_status_frequency_minutes=None,
        channel_evidence=channel_evidence,
        recovery_grace_evidence=_recovery_evidence(),
        evidence_reference_ids=("context-evidence-1",),
    )


def _eligibility_decision(
    *,
    committed: bool = True,
    raw_payload: bool = False,
    identity_ambiguous: bool = False,
    telegram_enabled_by_user: bool = True,
    telegram_target_reference_id: str | None = "telegram-target-1",
    telegram_target_verified: bool = True,
    telegram_target_available: bool = True,
    max_enabled_by_user: bool = True,
    max_target_reference_id: str | None = "max-target-1",
    max_target_verified: bool = True,
    max_target_available: bool = True,
    channel_evidence: tuple[NotificationChannelEligibilityEvidence, ...] | None = None,
) -> NotificationEligibilityDecision:
    source_intake_decision = evaluate_notification_source_intake(
        decision_id="intake-decision-1",
        source_event=_source_event(
            committed=committed,
            raw_payload=raw_payload,
            identity_ambiguous=identity_ambiguous,
        ),
        evidence_reference_ids=("intake-evidence-1",),
    )
    context = _context(
        telegram_enabled_by_user=telegram_enabled_by_user,
        telegram_target_reference_id=telegram_target_reference_id,
        telegram_target_verified=telegram_target_verified,
        telegram_target_available=telegram_target_available,
        max_enabled_by_user=max_enabled_by_user,
        max_target_reference_id=max_target_reference_id,
        max_target_verified=max_target_verified,
        max_target_available=max_target_available,
        channel_evidence=channel_evidence,
    )
    return evaluate_notification_eligibility(
        decision_id="eligibility-decision-1",
        source_intake_decision=source_intake_decision,
        context=context,
        evidence_reference_ids=("eligibility-evidence-1",),
    )


def _outbox_decision(
    *, eligibility_decision: NotificationEligibilityDecision
) -> NotificationOutboxCreationDecision:
    source_event = eligibility_decision.source_intake_decision.source_event
    return create_notification_outbox_item(
        decision_id="outbox-decision-1",
        outbox_item_id="outbox-item-1",
        outbox_contract="notification.outbox.v1",
        outbox_contract_version="1.0",
        eligibility_decision=eligibility_decision,
        idempotency_key=source_event.idempotency_key,
        idempotency_fingerprint=source_event.idempotency_fingerprint,
        idempotency_scope=source_event.idempotency_scope,
        existing_outbox_item=None,
        evidence_reference_ids=("outbox-evidence-1",),
    )


def _plan_decision(
    *,
    committed: bool = True,
    raw_payload: bool = False,
    identity_ambiguous: bool = False,
    telegram_enabled_by_user: bool = True,
    telegram_target_reference_id: str | None = "telegram-target-1",
    telegram_target_verified: bool = True,
    telegram_target_available: bool = True,
    max_enabled_by_user: bool = True,
    max_target_reference_id: str | None = "max-target-1",
    max_target_verified: bool = True,
    max_target_available: bool = True,
    channel_evidence: tuple[NotificationChannelEligibilityEvidence, ...] | None = None,
) -> NotificationDeliveryPlanDecision:
    eligibility_decision = _eligibility_decision(
        committed=committed,
        raw_payload=raw_payload,
        identity_ambiguous=identity_ambiguous,
        telegram_enabled_by_user=telegram_enabled_by_user,
        telegram_target_reference_id=telegram_target_reference_id,
        telegram_target_verified=telegram_target_verified,
        telegram_target_available=telegram_target_available,
        max_enabled_by_user=max_enabled_by_user,
        max_target_reference_id=max_target_reference_id,
        max_target_verified=max_target_verified,
        max_target_available=max_target_available,
        channel_evidence=channel_evidence,
    )
    return plan_notification_delivery(
        decision_id="delivery-plan-decision-1",
        delivery_plan_id="delivery-plan-1",
        outbox_creation_decision=_outbox_decision(eligibility_decision=eligibility_decision),
        evidence_reference_ids=("plan-evidence-1",),
    )


def _planned_attempt(
    *,
    channel_class: NotificationChannelClass,
    attempt_id: str = "attempt-1",
    plan_decision: NotificationDeliveryPlanDecision | None = None,
    committed: bool = True,
    raw_payload: bool = False,
    identity_ambiguous: bool = False,
    telegram_enabled_by_user: bool = True,
    telegram_target_reference_id: str | None = "telegram-target-1",
    telegram_target_verified: bool = True,
    telegram_target_available: bool = True,
    max_enabled_by_user: bool = True,
    max_target_reference_id: str | None = "max-target-1",
    max_target_verified: bool = True,
    max_target_available: bool = True,
    channel_evidence: tuple[NotificationChannelEligibilityEvidence, ...] | None = None,
) -> NotificationAttempt:
    if plan_decision is None:
        plan_decision = _plan_decision(
            committed=committed,
            raw_payload=raw_payload,
            identity_ambiguous=identity_ambiguous,
            telegram_enabled_by_user=telegram_enabled_by_user,
            telegram_target_reference_id=telegram_target_reference_id,
            telegram_target_verified=telegram_target_verified,
            telegram_target_available=telegram_target_available,
            max_enabled_by_user=max_enabled_by_user,
            max_target_reference_id=max_target_reference_id,
            max_target_verified=max_target_verified,
            max_target_available=max_target_available,
            channel_evidence=channel_evidence,
        )
    decision = plan_notification_attempt(
        decision_id="attempt-planning-decision-1",
        attempt_id=attempt_id,
        delivery_plan_decision=plan_decision,
        channel_class=channel_class,
        idempotency_key=IdempotencyKey(value="command-key-1"),
        idempotency_fingerprint=IdempotencyFingerprint(value="command-fingerprint-1"),
        idempotency_scope=IdempotencyScope(value="command-scope-1"),
        evidence_reference_ids=("command-evidence-1",),
    )
    assert decision.attempt is not None
    return decision.attempt


def _provider_outcome(
    attempt: NotificationAttempt,
    *,
    outcome_reference_id: str = "provider-outcome-1",
    outcome_class: NotificationProviderOutcomeClass = (
        NotificationProviderOutcomeClass.PROVIDER_ACCEPTED
    ),
    adapter_outcome_committed: bool = True,
    provider_safe_delivery_reference: str | None = "provider-safe-delivery-1",
    egress_correlation_reference: str | None = None,
    contains_raw_provider_payload: bool = False,
    identity_ambiguous: bool = False,
    correlation_id: str | None = None,
    causation_id: str | None = None,
    reason_codes: tuple[str, ...] = ("provider-reason-1",),
    evidence_reference_ids: tuple[str, ...] = ("provider-evidence-1",),
) -> NotificationProviderOutcomeReference:
    return NotificationProviderOutcomeReference(
        outcome_reference_id=outcome_reference_id,
        adapter_contract="adapter-contract-1",
        adapter_contract_version="1.0",
        attempt_id=attempt.attempt_id,
        channel_class=attempt.channel_class,
        target_reference_id=attempt.target_reference_id,
        outcome_class=outcome_class,
        adapter_outcome_committed=adapter_outcome_committed,
        provider_safe_delivery_reference=provider_safe_delivery_reference,
        egress_correlation_reference=egress_correlation_reference,
        contains_raw_provider_payload=contains_raw_provider_payload,
        identity_ambiguous=identity_ambiguous,
        correlation_id=attempt.correlation_id if correlation_id is None else correlation_id,
        causation_id=attempt.causation_id if causation_id is None else causation_id,
        reason_codes=reason_codes,
        evidence_reference_ids=evidence_reference_ids,
    )


def _accept(
    attempt: NotificationAttempt,
    provider_outcome: NotificationProviderOutcomeReference,
    *,
    decision_id: str = "accept-decision-1",
    evidence_reference_ids: tuple[str, ...] = ("command-evidence-2",),
) -> NotificationProviderOutcomeAcceptanceDecision:
    return accept_notification_provider_outcome(
        decision_id=decision_id,
        attempt=attempt,
        provider_outcome=provider_outcome,
        evidence_reference_ids=evidence_reference_ids,
    )


def _attempt_with_lifecycle(
    *,
    lifecycle_status: NotificationAttemptLifecycleStatus,
    channel_class: NotificationChannelClass = NotificationChannelClass.TELEGRAM,
    evidence_reference_ids: tuple[str, ...] = ("command-evidence-1",),
) -> NotificationAttempt:
    return replace(
        _planned_attempt(channel_class=channel_class),
        lifecycle_status=lifecycle_status,
        evidence_reference_ids=evidence_reference_ids,
    )


def test_planning_creates_exact_attempt_for_telegram_and_max() -> None:
    plan_decision = _plan_decision()

    telegram_result = plan_notification_attempt(
        decision_id="attempt-planning-decision-telegram",
        attempt_id="attempt-telegram-1",
        delivery_plan_decision=plan_decision,
        channel_class=NotificationChannelClass.TELEGRAM,
        idempotency_key=IdempotencyKey(value="command-key-telegram"),
        idempotency_fingerprint=IdempotencyFingerprint(value="command-fingerprint-telegram"),
        idempotency_scope=IdempotencyScope(value="command-scope-telegram"),
        evidence_reference_ids=("command-evidence-telegram",),
    )
    assert telegram_result.status is NotificationAttemptPlanningStatus.PLANNED
    assert telegram_result.attempt_created is True
    assert telegram_result.dispatch_effect_authorized is False
    assert telegram_result.provider_mapping_authorized is False
    assert telegram_result.reason_codes == ("attempt-planned",)
    assert telegram_result.attempt is not None
    telegram_attempt = telegram_result.attempt
    assert telegram_attempt.lifecycle_status is NotificationAttemptLifecycleStatus.ATTEMPT_PLANNED
    assert telegram_attempt.channel_class is NotificationChannelClass.TELEGRAM
    assert telegram_attempt.target_reference_id == "telegram-target-1"
    assert telegram_attempt.delivery_plan_id == "delivery-plan-1"
    assert telegram_attempt.outbox_item_id == "outbox-item-1"
    assert telegram_attempt.account_id == "account-1"
    assert telegram_attempt.beacon_id == "beacon-1"
    assert telegram_attempt.correlation_id == "corr-1"
    assert telegram_attempt.causation_id == "cause-1"
    assert telegram_attempt.idempotency_key == IdempotencyKey(value="command-key-telegram")
    assert telegram_attempt.idempotency_fingerprint == IdempotencyFingerprint(
        value="command-fingerprint-telegram"
    )
    assert telegram_attempt.idempotency_scope == IdempotencyScope(value="command-scope-telegram")
    assert telegram_attempt.provider_outcome_reference_id is None
    assert telegram_attempt.provider_outcome_class is None
    assert telegram_attempt.provider_safe_delivery_reference is None
    assert telegram_attempt.egress_correlation_reference is None
    assert telegram_attempt.provider_reason_codes == ()
    assert telegram_attempt.failure_policy_reference is None
    assert telegram_attempt.reconciliation_required is False
    assert telegram_attempt.delivery_accepted is False
    assert telegram_attempt.retry_authorized is False
    assert telegram_attempt.dispatch_effect_authorized is False
    assert telegram_attempt.provider_mapping_authorized is False
    assert telegram_attempt.reason_codes == ("attempt-planned",)

    max_result = plan_notification_attempt(
        decision_id="attempt-planning-decision-max",
        attempt_id="attempt-max-1",
        delivery_plan_decision=plan_decision,
        channel_class=NotificationChannelClass.MAX,
        idempotency_key=IdempotencyKey(value="command-key-max"),
        idempotency_fingerprint=IdempotencyFingerprint(value="command-fingerprint-max"),
        idempotency_scope=IdempotencyScope(value="command-scope-max"),
        evidence_reference_ids=("command-evidence-max",),
    )
    assert max_result.status is NotificationAttemptPlanningStatus.PLANNED
    assert max_result.attempt is not None
    assert max_result.attempt is not telegram_attempt
    assert max_result.attempt.channel_class is NotificationChannelClass.MAX
    assert max_result.attempt.target_reference_id == "max-target-1"


@pytest.mark.parametrize(
    "kwargs, channel_class, expected_status",
    [
        (
            {"telegram_enabled_by_user": False},
            NotificationChannelClass.TELEGRAM,
            NotificationAttemptPlanningStatus.BLOCKED_CHANNEL_PLAN,
        ),
        (
            {"telegram_target_verified": False},
            NotificationChannelClass.TELEGRAM,
            NotificationAttemptPlanningStatus.BLOCKED_CHANNEL_PLAN,
        ),
        (
            {"telegram_target_available": False},
            NotificationChannelClass.TELEGRAM,
            NotificationAttemptPlanningStatus.BLOCKED_CHANNEL_PLAN,
        ),
        (
            {"max_enabled_by_user": False},
            NotificationChannelClass.MAX,
            NotificationAttemptPlanningStatus.BLOCKED_CHANNEL_PLAN,
        ),
        (
            {"channel_evidence": (_max_evidence(), _web_evidence())},
            NotificationChannelClass.TELEGRAM,
            NotificationAttemptPlanningStatus.BLOCKED_CHANNEL_PLAN,
        ),
        (
            {},
            NotificationChannelClass.WEB_STATUS_READ_MODEL,
            NotificationAttemptPlanningStatus.BLOCKED_CHANNEL_PLAN,
        ),
    ],
)
def test_non_push_or_unavailable_channels_are_blocked(
    kwargs: dict[str, object],
    channel_class: NotificationChannelClass,
    expected_status: NotificationAttemptPlanningStatus,
) -> None:
    plan_decision = _plan_decision(**cast(Any, kwargs))
    decision = plan_notification_attempt(
        decision_id="attempt-blocked-channel-decision",
        attempt_id="attempt-blocked-channel",
        delivery_plan_decision=plan_decision,
        channel_class=channel_class,
        idempotency_key=IdempotencyKey(value="blocked-key"),
        idempotency_fingerprint=IdempotencyFingerprint(value="blocked-fingerprint"),
        idempotency_scope=IdempotencyScope(value="blocked-scope"),
        evidence_reference_ids=("blocked-evidence",),
    )
    assert decision.status is expected_status
    assert decision.attempt is None
    assert decision.attempt_created is False
    assert decision.reason_codes == ("attempt-channel-plan-blocked",)
    assert decision.dispatch_effect_authorized is False
    assert decision.provider_mapping_authorized is False


def test_invalid_delivery_plan_is_blocked_before_channel_validation() -> None:
    blocked_plan = _plan_decision(committed=False)
    decision = plan_notification_attempt(
        decision_id="attempt-blocked-plan-decision",
        attempt_id="attempt-blocked-plan",
        delivery_plan_decision=blocked_plan,
        channel_class=NotificationChannelClass.TELEGRAM,
        idempotency_key=IdempotencyKey(value="blocked-plan-key"),
        idempotency_fingerprint=IdempotencyFingerprint(value="blocked-plan-fingerprint"),
        idempotency_scope=IdempotencyScope(value="blocked-plan-scope"),
        evidence_reference_ids=("blocked-plan-evidence",),
    )
    assert decision.status is NotificationAttemptPlanningStatus.BLOCKED_DELIVERY_PLAN
    assert decision.attempt is None
    assert decision.attempt_created is False
    assert decision.reason_codes == ("attempt-delivery-plan-blocked",)


def test_propagation_scope_and_idempotency_are_exact() -> None:
    attempt = _planned_attempt(channel_class=NotificationChannelClass.TELEGRAM)
    assert attempt.delivery_plan_id == "delivery-plan-1"
    assert attempt.outbox_item_id == "outbox-item-1"
    assert attempt.account_id == "account-1"
    assert attempt.beacon_id == "beacon-1"
    assert attempt.correlation_id == "corr-1"
    assert attempt.causation_id == "cause-1"
    assert attempt.idempotency_key == IdempotencyKey(value="command-key-1")
    assert attempt.idempotency_fingerprint == IdempotencyFingerprint(value="command-fingerprint-1")
    assert attempt.idempotency_scope == IdempotencyScope(value="command-scope-1")
    assert attempt.dispatch_effect_authorized is False
    assert attempt.provider_mapping_authorized is False
    assert attempt.retry_authorized is False


def test_explicit_committed_provider_acceptance_delivers() -> None:
    attempt = _planned_attempt(channel_class=NotificationChannelClass.TELEGRAM)
    provider_outcome = _provider_outcome(
        attempt,
        provider_safe_delivery_reference="provider-safe-delivery-accepted-1",
        egress_correlation_reference="egress-corr-1",
        evidence_reference_ids=("provider-evidence-1", "shared-evidence"),
        reason_codes=("provider-reason-1",),
    )
    decision = _accept(
        attempt,
        provider_outcome,
        evidence_reference_ids=("command-evidence-2", "shared-evidence"),
    )
    assert decision.status is NotificationProviderOutcomeAcceptanceStatus.ACCEPTED_DELIVERED
    assert decision.outcome_accepted is True
    assert decision.replayed is False
    assert decision.delivery_accepted is True
    assert decision.reconciliation_required is False
    assert decision.retry_authorized is False
    assert decision.dispatch_effect_authorized is False
    assert decision.provider_mapping_authorized is False
    assert decision.reason_codes == ("provider-outcome-accepted-delivered",)
    assert decision.resulting_attempt is not None
    resulting_attempt = decision.resulting_attempt
    assert (
        resulting_attempt.lifecycle_status is NotificationAttemptLifecycleStatus.DELIVERED_ACCEPTED
    )
    assert resulting_attempt.provider_outcome_reference_id == "provider-outcome-1"
    assert (
        resulting_attempt.provider_outcome_class
        is NotificationProviderOutcomeClass.PROVIDER_ACCEPTED
    )
    assert resulting_attempt.provider_safe_delivery_reference == "provider-safe-delivery-accepted-1"
    assert resulting_attempt.egress_correlation_reference == "egress-corr-1"
    assert resulting_attempt.delivery_accepted is True
    assert resulting_attempt.reconciliation_required is False
    assert resulting_attempt.retry_authorized is False
    assert resulting_attempt.dispatch_effect_authorized is False
    assert resulting_attempt.provider_mapping_authorized is False
    assert resulting_attempt.reason_codes == ("provider-outcome-accepted-delivered",)
    assert decision.evidence_reference_ids == _tuple_union(
        attempt.evidence_reference_ids,
        provider_outcome.evidence_reference_ids,
        ("command-evidence-2", "shared-evidence"),
    )
    assert resulting_attempt.evidence_reference_ids == _tuple_union(
        attempt.evidence_reference_ids,
        provider_outcome.evidence_reference_ids,
        ("command-evidence-2", "shared-evidence"),
    )


@pytest.mark.parametrize(
    "provider_safe_delivery_reference, egress_correlation_reference",
    [
        (None, None),
        (None, "egress-corr-only-1"),
    ],
)
def test_acceptance_without_safe_delivery_reference_is_rejected(
    provider_safe_delivery_reference: str | None,
    egress_correlation_reference: str | None,
) -> None:
    attempt = _planned_attempt(channel_class=NotificationChannelClass.TELEGRAM)
    provider_outcome = _provider_outcome(
        attempt,
        provider_safe_delivery_reference=provider_safe_delivery_reference,
        egress_correlation_reference=egress_correlation_reference,
        reason_codes=("http-200",),
    )
    decision = _accept(attempt, provider_outcome)
    assert decision.status is NotificationProviderOutcomeAcceptanceStatus.REJECTED_STATE_MISMATCH
    assert decision.resulting_attempt is None
    assert decision.outcome_accepted is False
    assert decision.replayed is False
    assert decision.delivery_accepted is False
    assert decision.reconciliation_required is False
    assert attempt.provider_outcome_reference_id is None
    assert attempt.delivery_accepted is False
    assert attempt.reconciliation_required is False


def test_egress_correlation_alone_cannot_deliver() -> None:
    attempt = _planned_attempt(channel_class=NotificationChannelClass.TELEGRAM)
    provider_outcome = _provider_outcome(
        attempt,
        provider_safe_delivery_reference=None,
        egress_correlation_reference="egress-corr-only-1",
        reason_codes=("http-200",),
    )
    decision = _accept(attempt, provider_outcome)
    assert decision.status is NotificationProviderOutcomeAcceptanceStatus.REJECTED_STATE_MISMATCH
    assert decision.resulting_attempt is None


@pytest.mark.parametrize(
    "outcome_class, provider_safe_delivery_reference",
    [
        (
            NotificationProviderOutcomeClass.PROVIDER_ACCEPTED,
            "provider-safe-delivery-not-attempted-1",
        ),
        (
            NotificationProviderOutcomeClass.DISPATCH_AMBIGUOUS,
            "provider-safe-delivery-not-attempted-2",
        ),
        (
            NotificationProviderOutcomeClass.PROVIDER_REJECTED,
            None,
        ),
    ],
)
def test_not_attempted_rejects_committed_provider_outcomes(
    outcome_class: NotificationProviderOutcomeClass,
    provider_safe_delivery_reference: str | None,
) -> None:
    attempt = _attempt_with_lifecycle(
        lifecycle_status=NotificationAttemptLifecycleStatus.NOT_ATTEMPTED,
        evidence_reference_ids=("attempt-evidence-1", "shared-evidence"),
    )
    provider_outcome = _provider_outcome(
        attempt,
        outcome_class=outcome_class,
        provider_safe_delivery_reference=provider_safe_delivery_reference,
        evidence_reference_ids=("shared-evidence", "provider-evidence-1"),
    )
    decision = _accept(
        attempt,
        provider_outcome,
        evidence_reference_ids=("provider-evidence-1", "command-evidence-1"),
    )
    assert decision.status is NotificationProviderOutcomeAcceptanceStatus.REJECTED_STATE_MISMATCH
    assert decision.resulting_attempt is None
    assert decision.outcome_accepted is False
    assert decision.replayed is False
    assert decision.delivery_accepted is False
    assert decision.reconciliation_required is False
    assert decision.retry_authorized is False
    assert decision.dispatch_effect_authorized is False
    assert decision.provider_mapping_authorized is False
    assert decision.reason_codes == ("provider-outcome-state-mismatch",)
    assert decision.evidence_reference_ids == (
        "attempt-evidence-1",
        "shared-evidence",
        "provider-evidence-1",
        "command-evidence-1",
    )
    assert attempt.lifecycle_status is NotificationAttemptLifecycleStatus.NOT_ATTEMPTED
    assert attempt.provider_outcome_reference_id is None
    assert attempt.delivery_accepted is False
    assert attempt.reconciliation_required is False


@pytest.mark.parametrize(
    "_field_name, update_kwargs, expected_status, expected_reason",
    [
        (
            "adapter_outcome_committed",
            {"adapter_outcome_committed": False},
            NotificationProviderOutcomeAcceptanceStatus.REJECTED_UNCOMMITTED,
            "provider-outcome-uncommitted",
        ),
        (
            "contains_raw_provider_payload",
            {"contains_raw_provider_payload": True},
            NotificationProviderOutcomeAcceptanceStatus.REJECTED_UNSAFE_PAYLOAD,
            "provider-outcome-unsafe-payload",
        ),
        (
            "identity_ambiguous",
            {"identity_ambiguous": True},
            NotificationProviderOutcomeAcceptanceStatus.REJECTED_IDENTITY_AMBIGUOUS,
            "provider-outcome-identity-ambiguous",
        ),
    ],
)
def test_uncommitted_raw_and_identity_mismatches_are_rejected(
    _field_name: str,
    update_kwargs: dict[str, object],
    expected_status: NotificationProviderOutcomeAcceptanceStatus,
    expected_reason: str,
) -> None:
    attempt = _planned_attempt(channel_class=NotificationChannelClass.TELEGRAM)
    provider_outcome = replace(_provider_outcome(attempt), **cast(Any, update_kwargs))
    decision = _accept(attempt, provider_outcome)
    assert decision.status is expected_status
    assert decision.reason_codes == (expected_reason,)
    assert decision.resulting_attempt is None
    assert decision.outcome_accepted is False
    assert attempt.provider_outcome_reference_id is None


def test_scope_mismatch_is_rejected() -> None:
    attempt = _planned_attempt(channel_class=NotificationChannelClass.TELEGRAM)
    provider_outcome = replace(
        _provider_outcome(attempt),
        attempt_id="other-attempt-id",
    )
    decision = _accept(attempt, provider_outcome)
    assert decision.status is NotificationProviderOutcomeAcceptanceStatus.REJECTED_SCOPE_MISMATCH
    assert decision.reason_codes == ("provider-outcome-scope-mismatch",)
    assert decision.resulting_attempt is None
    assert attempt.provider_outcome_reference_id is None


@pytest.mark.parametrize(
    "boundary_type",
    [
        TransportOutcomeCommitmentBoundary,
        TransportAvailabilityOutcomeBoundary,
        TransportResponsePresenceOutcomeBoundary,
        TransportResponseFailureOutcomeBoundary,
        PolicyFallbackTransportOutcomeBoundary,
    ],
)
def test_egress_boundaries_are_rejected_as_provider_outcome_inputs(
    boundary_type: type[object],
) -> None:
    attempt = _planned_attempt(channel_class=NotificationChannelClass.TELEGRAM)
    boundary = object.__new__(boundary_type)
    with pytest.raises(ValueError):
        _accept(attempt, boundary)  # type: ignore[arg-type]
    assert attempt.provider_outcome_reference_id is None


@pytest.mark.parametrize(
    "outcome_class, expected_lifecycle",
    [
        (
            NotificationProviderOutcomeClass.PROVIDER_REJECTED,
            NotificationAttemptLifecycleStatus.PROVIDER_REJECTED,
        ),
        (
            NotificationProviderOutcomeClass.PROVIDER_UNAVAILABLE,
            NotificationAttemptLifecycleStatus.PROVIDER_UNAVAILABLE,
        ),
        (
            NotificationProviderOutcomeClass.RATE_OR_ACCESS_RESTRICTED,
            NotificationAttemptLifecycleStatus.RATE_OR_ACCESS_RESTRICTED,
        ),
        (
            NotificationProviderOutcomeClass.MALFORMED_OR_UNUSABLE_PROVIDER_RESPONSE,
            NotificationAttemptLifecycleStatus.MALFORMED_OR_UNUSABLE_PROVIDER_RESPONSE,
        ),
        (
            NotificationProviderOutcomeClass.DELIVERY_FAILURE,
            NotificationAttemptLifecycleStatus.DELIVERY_FAILURE,
        ),
        (
            NotificationProviderOutcomeClass.SUPPRESSED_OR_CANCELLED,
            NotificationAttemptLifecycleStatus.SUPPRESSED_OR_CANCELLED,
        ),
        (
            NotificationProviderOutcomeClass.TARGET_UNAVAILABLE_OR_UNVERIFIED,
            NotificationAttemptLifecycleStatus.TARGET_UNAVAILABLE_OR_UNVERIFIED,
        ),
    ],
)
def test_provider_failure_mappings_are_exact(
    outcome_class: NotificationProviderOutcomeClass,
    expected_lifecycle: NotificationAttemptLifecycleStatus,
) -> None:
    attempt = _planned_attempt(channel_class=NotificationChannelClass.TELEGRAM)
    provider_outcome = _provider_outcome(
        attempt,
        outcome_class=outcome_class,
        provider_safe_delivery_reference=None,
        reason_codes=("provider-reason-1",),
    )
    decision = _accept(attempt, provider_outcome)
    assert decision.status is NotificationProviderOutcomeAcceptanceStatus.ACCEPTED_FAILURE
    assert decision.replayed is False
    assert decision.delivery_accepted is False
    assert decision.reconciliation_required is False
    assert decision.retry_authorized is False
    assert decision.dispatch_effect_authorized is False
    assert decision.provider_mapping_authorized is False
    assert decision.resulting_attempt is not None
    assert decision.resulting_attempt.lifecycle_status is expected_lifecycle
    assert decision.resulting_attempt.reason_codes == ("provider-outcome-accepted-failure",)


@pytest.mark.parametrize(
    (
        "outcome_class, provider_safe_delivery_reference, expected_status, "
        "expected_lifecycle, expected_delivery_accepted, "
        "expected_reconciliation_required, expected_reason"
    ),
    [
        (
            NotificationProviderOutcomeClass.PROVIDER_ACCEPTED,
            "provider-safe-delivery-in-progress-1",
            NotificationProviderOutcomeAcceptanceStatus.ACCEPTED_DELIVERED,
            NotificationAttemptLifecycleStatus.DELIVERED_ACCEPTED,
            True,
            False,
            "provider-outcome-accepted-delivered",
        ),
        (
            NotificationProviderOutcomeClass.DISPATCH_AMBIGUOUS,
            "provider-safe-delivery-in-progress-ambiguous-1",
            NotificationProviderOutcomeAcceptanceStatus.ACCEPTED_AMBIGUOUS,
            NotificationAttemptLifecycleStatus.RECONCILIATION_REQUIRED,
            False,
            True,
            "provider-outcome-accepted-ambiguous",
        ),
        (
            NotificationProviderOutcomeClass.PROVIDER_REJECTED,
            None,
            NotificationProviderOutcomeAcceptanceStatus.ACCEPTED_FAILURE,
            NotificationAttemptLifecycleStatus.PROVIDER_REJECTED,
            False,
            False,
            "provider-outcome-accepted-failure",
        ),
    ],
)
def test_attempt_in_progress_accepts_valid_provider_outcomes(
    outcome_class: NotificationProviderOutcomeClass,
    provider_safe_delivery_reference: str | None,
    expected_status: NotificationProviderOutcomeAcceptanceStatus,
    expected_lifecycle: NotificationAttemptLifecycleStatus,
    expected_delivery_accepted: bool,
    expected_reconciliation_required: bool,
    expected_reason: str,
) -> None:
    attempt = _attempt_with_lifecycle(
        lifecycle_status=NotificationAttemptLifecycleStatus.ATTEMPT_IN_PROGRESS,
    )
    provider_outcome = _provider_outcome(
        attempt,
        outcome_class=outcome_class,
        provider_safe_delivery_reference=provider_safe_delivery_reference,
    )
    decision = _accept(attempt, provider_outcome)
    assert decision.status is expected_status
    assert decision.outcome_accepted is True
    assert decision.replayed is False
    assert decision.delivery_accepted is expected_delivery_accepted
    assert decision.reconciliation_required is expected_reconciliation_required
    assert decision.retry_authorized is False
    assert decision.dispatch_effect_authorized is False
    assert decision.provider_mapping_authorized is False
    assert decision.reason_codes == (expected_reason,)
    assert decision.resulting_attempt is not None
    assert decision.resulting_attempt is not attempt
    assert decision.resulting_attempt.lifecycle_status is expected_lifecycle


@pytest.mark.parametrize(
    "outcome_class",
    [
        NotificationProviderOutcomeClass.DISPATCH_AMBIGUOUS,
        NotificationProviderOutcomeClass.DELIVERY_AMBIGUOUS,
    ],
)
def test_ambiguous_mappings_are_exact_and_never_authorize_retry(
    outcome_class: NotificationProviderOutcomeClass,
) -> None:
    attempt = _planned_attempt(channel_class=NotificationChannelClass.TELEGRAM)
    provider_outcome = _provider_outcome(
        attempt,
        outcome_class=outcome_class,
        provider_safe_delivery_reference="provider-safe-delivery-ambiguous-1",
    )
    decision = _accept(attempt, provider_outcome)
    assert decision.status is NotificationProviderOutcomeAcceptanceStatus.ACCEPTED_AMBIGUOUS
    assert decision.delivery_accepted is False
    assert decision.reconciliation_required is True
    assert decision.retry_authorized is False
    assert decision.dispatch_effect_authorized is False
    assert decision.provider_mapping_authorized is False
    assert decision.resulting_attempt is not None
    assert (
        decision.resulting_attempt.lifecycle_status
        is NotificationAttemptLifecycleStatus.RECONCILIATION_REQUIRED
    )
    assert decision.resulting_attempt.reason_codes == ("provider-outcome-accepted-ambiguous",)


def test_replay_returns_same_attempt_object_when_semantics_match() -> None:
    attempt = _planned_attempt(channel_class=NotificationChannelClass.TELEGRAM)
    provider_outcome = _provider_outcome(
        attempt,
        provider_safe_delivery_reference="provider-safe-delivery-replay-1",
        egress_correlation_reference="egress-replay-1",
        evidence_reference_ids=("provider-evidence-replay-1",),
    )
    accepted = _accept(
        attempt, provider_outcome, evidence_reference_ids=("command-evidence-replay-1",)
    )
    assert accepted.resulting_attempt is not None
    replay = _accept(
        accepted.resulting_attempt,
        provider_outcome,
        evidence_reference_ids=("command-evidence-replay-2",),
    )
    assert replay.status is NotificationProviderOutcomeAcceptanceStatus.REPLAYED
    assert replay.replayed is True
    assert replay.outcome_accepted is True
    assert replay.resulting_attempt is accepted.resulting_attempt
    assert replay.delivery_accepted is True
    assert replay.reconciliation_required is False
    assert replay.retry_authorized is False
    assert replay.dispatch_effect_authorized is False
    assert replay.provider_mapping_authorized is False
    assert replay.reason_codes == ("provider-outcome-replayed",)


@pytest.mark.parametrize(
    "update_kwargs",
    [
        {"provider_safe_delivery_reference": "different-safe-ref"},
        {"outcome_reference_id": "provider-outcome-2"},
    ],
)
def test_changed_replay_and_second_outcome_are_rejected(update_kwargs: dict[str, object]) -> None:
    attempt = _planned_attempt(channel_class=NotificationChannelClass.TELEGRAM)
    provider_outcome = _provider_outcome(
        attempt,
        provider_safe_delivery_reference="provider-safe-delivery-1",
    )
    accepted = _accept(attempt, provider_outcome)
    assert accepted.resulting_attempt is not None
    changed = replace(provider_outcome, **cast(Any, update_kwargs))
    decision = _accept(accepted.resulting_attempt, changed)
    assert decision.status is NotificationProviderOutcomeAcceptanceStatus.REJECTED_STATE_MISMATCH
    assert decision.resulting_attempt is None
    assert accepted.resulting_attempt.provider_outcome_reference_id == "provider-outcome-1"


def test_one_channel_cannot_mutate_another() -> None:
    plan_decision = _plan_decision()
    telegram_result = plan_notification_attempt(
        decision_id="attempt-planning-telegram-mutation",
        attempt_id="attempt-telegram-mutation",
        delivery_plan_decision=plan_decision,
        channel_class=NotificationChannelClass.TELEGRAM,
        idempotency_key=IdempotencyKey(value="telegram-mutation-key"),
        idempotency_fingerprint=IdempotencyFingerprint(value="telegram-mutation-fingerprint"),
        idempotency_scope=IdempotencyScope(value="telegram-mutation-scope"),
        evidence_reference_ids=("telegram-mutation-evidence",),
    )
    max_result = plan_notification_attempt(
        decision_id="attempt-planning-max-mutation",
        attempt_id="attempt-max-mutation",
        delivery_plan_decision=plan_decision,
        channel_class=NotificationChannelClass.MAX,
        idempotency_key=IdempotencyKey(value="max-mutation-key"),
        idempotency_fingerprint=IdempotencyFingerprint(value="max-mutation-fingerprint"),
        idempotency_scope=IdempotencyScope(value="max-mutation-scope"),
        evidence_reference_ids=("max-mutation-evidence",),
    )
    assert telegram_result.attempt is not None
    assert max_result.attempt is not None
    original_max_attempt = max_result.attempt
    accepted = _accept(
        telegram_result.attempt,
        _provider_outcome(
            telegram_result.attempt,
            provider_safe_delivery_reference="telegram-mutated-safe-ref-1",
        ),
    )
    assert accepted.resulting_attempt is not None
    assert max_result.attempt == original_max_attempt
    assert max_result.attempt is original_max_attempt
    assert max_result.attempt.provider_outcome_reference_id is None


def test_exact_platform_idempotency_types_are_required() -> None:
    attempt = _planned_attempt(channel_class=NotificationChannelClass.TELEGRAM)

    class _DerivedIdempotencyKey(IdempotencyKey):
        pass

    class _DerivedIdempotencyFingerprint(IdempotencyFingerprint):
        pass

    class _DerivedIdempotencyScope(IdempotencyScope):
        pass

    with pytest.raises(ValueError):
        replace(
            attempt,
            idempotency_key=_DerivedIdempotencyKey(value="contract-key"),
        )
    with pytest.raises(ValueError):
        replace(
            attempt,
            idempotency_fingerprint=_DerivedIdempotencyFingerprint(
                value="contract-fingerprint"
            ),
        )
    with pytest.raises(ValueError):
        replace(
            attempt,
            idempotency_scope=_DerivedIdempotencyScope(value="contract-scope"),
        )


def test_tuple_blank_and_duplicate_validation_is_exact() -> None:
    attempt = _planned_attempt(channel_class=NotificationChannelClass.TELEGRAM)
    with pytest.raises(ValueError):
        replace(attempt, attempt_id="")
    with pytest.raises(ValueError):
        replace(attempt, reason_codes=("attempt-planned", "attempt-planned"))
    with pytest.raises(ValueError):
        replace(attempt, evidence_reference_ids=("evidence-1", "evidence-1"))

    provider_outcome = _provider_outcome(attempt)
    with pytest.raises(ValueError):
        replace(provider_outcome, provider_safe_delivery_reference="")
    with pytest.raises(ValueError):
        replace(provider_outcome, egress_correlation_reference="")
    with pytest.raises(ValueError):
        replace(
            provider_outcome, evidence_reference_ids=("provider-evidence-1", "provider-evidence-1")
        )


def test_frozen_records_expose_no_mutable_dict_and_exact_types() -> None:
    attempt = _planned_attempt(channel_class=NotificationChannelClass.TELEGRAM)
    provider_outcome = _provider_outcome(attempt)
    assert hasattr(attempt, "__slots__")
    assert hasattr(provider_outcome, "__slots__")
    assert not hasattr(attempt, "__dict__")
    assert not hasattr(provider_outcome, "__dict__")
    assert type(attempt.idempotency_key) is IdempotencyKey
    assert type(attempt.idempotency_fingerprint) is IdempotencyFingerprint
    assert type(attempt.idempotency_scope) is IdempotencyScope
    assert type(provider_outcome) is NotificationProviderOutcomeReference
