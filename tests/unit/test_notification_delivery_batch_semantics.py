from __future__ import annotations

from dataclasses import replace

import pytest

from mayak.contracts.idempotency import IdempotencyFingerprint, IdempotencyKey, IdempotencyScope
from mayak.modules.notification_delivery import (
    NotificationAttempt,
    NotificationAttemptPlanningDecision,
    NotificationAttemptPlanningStatus,
    NotificationBatchDecision,
    NotificationBatchDecisionStatus,
    NotificationBatchDisposition,
    NotificationBatchItemInput,
    NotificationBatchItemResult,
    NotificationBatchStage,
    NotificationBeaconLifecycleStatus,
    NotificationChannelClass,
    NotificationChannelEligibilityEvidence,
    NotificationDeduplicationRecordState,
    NotificationDeduplicationRequest,
    NotificationDeduplicationStage,
    NotificationDeliveryPlanDecision,
    NotificationDeliveryPlanDecisionStatus,
    NotificationEligibilityContext,
    NotificationEntitlementStatus,
    NotificationOutboxCreationDecision,
    NotificationOutboxItem,
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
    evaluate_notification_deduplication,
    evaluate_notification_eligibility,
    evaluate_notification_source_intake,
    plan_notification_attempt,
    plan_notification_delivery,
    project_notification_batch_outcomes,
)
from mayak.modules.notification_delivery.batch import (
    NotificationBatchAuthority,
)
from mayak.modules.notification_delivery.batch import (
    NotificationBatchSafeErrorCategory as BatchSafeErrorCategory,
)


def _source_event(
    *,
    source_event_id: str = "source-event-1",
    account_id: str = "account-1",
    beacon_id: str | None = "beacon-1",
    safe_listing_reference_ids: tuple[str, ...] = ("listing-1", "listing-2"),
) -> NotificationSourceEvent:
    return NotificationSourceEvent(
        source_event_id=source_event_id,
        source_family=NotificationSourceFamily.NEW_LISTINGS_FOUND,
        source_producer=NotificationSourceProducer.SCAN_ORCHESTRATION,
        source_contract="scan.notification.v1",
        source_contract_version="1.0",
        source_fact_id="fact-1",
        source_committed=True,
        source_commit_reference="commit-1",
        account_id=account_id,
        beacon_id=beacon_id,
        scan_run_id="scan-run-1",
        listing_count=len(safe_listing_reference_ids),
        safe_listing_reference_ids=safe_listing_reference_ids,
        correlation_id="corr-1",
        causation_id="cause-1",
        idempotency_key=IdempotencyKey(value="idempotency-key-1"),
        idempotency_fingerprint=IdempotencyFingerprint(value="idempotency-fingerprint-1"),
        idempotency_scope=IdempotencyScope(value="idempotency-scope-1"),
        source_identity_ambiguous=False,
        contains_raw_provider_payload=False,
        service_access_gate_approved=False,
        evidence_reference_ids=("source-evidence-1",),
    )


def _channel_evidence(
    channel_class: NotificationChannelClass,
    *,
    enabled_by_user: bool,
    target_reference_id: str | None,
    target_verified: bool,
    target_available: bool,
    evidence_reference_ids: tuple[str, ...],
) -> NotificationChannelEligibilityEvidence:
    return NotificationChannelEligibilityEvidence(
        channel_class=channel_class,
        enabled_by_user=enabled_by_user,
        target_reference_id=target_reference_id,
        target_verified=target_verified,
        target_available=target_available,
        evidence_reference_ids=evidence_reference_ids,
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
    account_id: str = "account-1",
    beacon_id: str | None = "beacon-1",
    telegram_enabled: bool = True,
    telegram_target_reference_id: str | None = "telegram-target-1",
    telegram_target_verified: bool = True,
    telegram_target_available: bool = True,
    max_enabled: bool = True,
    max_target_reference_id: str | None = "max-target-1",
    max_target_verified: bool = True,
    max_target_available: bool = True,
) -> tuple[NotificationChannelEligibilityEvidence, ...]:
    return (
        _channel_evidence(
            NotificationChannelClass.TELEGRAM,
            enabled_by_user=telegram_enabled,
            target_reference_id=telegram_target_reference_id,
            target_verified=telegram_target_verified,
            target_available=telegram_target_available,
            evidence_reference_ids=("telegram-evidence-1",),
        ),
        _channel_evidence(
            NotificationChannelClass.MAX,
            enabled_by_user=max_enabled,
            target_reference_id=max_target_reference_id,
            target_verified=max_target_verified,
            target_available=max_target_available,
            evidence_reference_ids=("max-evidence-1",),
        ),
        _channel_evidence(
            NotificationChannelClass.WEB_STATUS_READ_MODEL,
            enabled_by_user=True,
            target_reference_id=None,
            target_verified=False,
            target_available=False,
            evidence_reference_ids=("web-evidence-1",),
        ),
    )


def _eligibility_decision(
    *,
    decision_id: str = "eligibility-decision-1",
    source_intake_decision_id: str = "source-intake-decision-1",
    source_event_id: str = "source-event-1",
    account_id: str = "account-1",
    beacon_id: str | None = "beacon-1",
    safe_listing_reference_ids: tuple[str, ...] = ("listing-1", "listing-2"),
    telegram_enabled: bool = True,
    telegram_target_reference_id: str | None = "telegram-target-1",
    telegram_target_verified: bool = True,
    telegram_target_available: bool = True,
    max_enabled: bool = True,
    max_target_reference_id: str | None = "max-target-1",
    max_target_verified: bool = True,
    max_target_available: bool = True,
):
    return evaluate_notification_eligibility(
        decision_id=decision_id,
        source_intake_decision=evaluate_notification_source_intake(
            decision_id=source_intake_decision_id,
            source_event=_source_event(
                source_event_id=source_event_id,
                account_id=account_id,
                beacon_id=beacon_id,
                safe_listing_reference_ids=safe_listing_reference_ids,
            ),
            evidence_reference_ids=("source-intake-evidence-1",),
        ),
        context=NotificationEligibilityContext(
            account_id=account_id,
            beacon_id=beacon_id,
            beacon_lifecycle_status=NotificationBeaconLifecycleStatus.ACTIVE,
            beacon_lifecycle_reference_id="beacon-lifecycle-1",
            entitlement_status=NotificationEntitlementStatus.ALLOWED,
            entitlement_decision_reference_id="entitlement-1",
            no_new_status_preference_enabled=False,
            no_new_status_frequency_minutes=None,
            channel_evidence=_eligibility_context(
                account_id=account_id,
                beacon_id=beacon_id,
                telegram_enabled=telegram_enabled,
                telegram_target_reference_id=telegram_target_reference_id,
                telegram_target_verified=telegram_target_verified,
                telegram_target_available=telegram_target_available,
                max_enabled=max_enabled,
                max_target_reference_id=max_target_reference_id,
                max_target_verified=max_target_verified,
                max_target_available=max_target_available,
            ),
            recovery_grace_evidence=_recovery_evidence(),
            evidence_reference_ids=("eligibility-context-evidence-1",),
        ),
        evidence_reference_ids=("eligibility-evidence-1",),
    )


def _outbox_creation_decision(
    *,
    decision_id: str = "outbox-decision-1",
    eligibility_decision_id: str = "eligibility-decision-1",
    source_intake_decision_id: str = "source-intake-decision-1",
    source_event_id: str = "source-event-1",
    account_id: str = "account-1",
    beacon_id: str | None = "beacon-1",
    safe_listing_reference_ids: tuple[str, ...] = ("listing-1", "listing-2"),
    telegram_enabled: bool = True,
    max_enabled: bool = True,
    outbox_item_id: str = "outbox-item-1",
    idempotency_key_value: str = "outbox-idempotency-key-1",
    idempotency_fingerprint_value: str = "outbox-idempotency-fingerprint-1",
    idempotency_scope_value: str = "outbox-idempotency-scope-1",
    existing_outbox_item: NotificationOutboxItem | None = None,
) -> NotificationOutboxCreationDecision:
    eligibility_decision = _eligibility_decision(
        decision_id=eligibility_decision_id,
        source_intake_decision_id=source_intake_decision_id,
        source_event_id=source_event_id,
        account_id=account_id,
        beacon_id=beacon_id,
        safe_listing_reference_ids=safe_listing_reference_ids,
        telegram_enabled=telegram_enabled,
        max_enabled=max_enabled,
    )
    return create_notification_outbox_item(
        decision_id=decision_id,
        outbox_item_id=outbox_item_id,
        outbox_contract="outbox.contract.v1",
        outbox_contract_version="1.0",
        eligibility_decision=eligibility_decision,
        idempotency_key=IdempotencyKey(value=idempotency_key_value),
        idempotency_fingerprint=IdempotencyFingerprint(value=idempotency_fingerprint_value),
        idempotency_scope=IdempotencyScope(value=idempotency_scope_value),
        existing_outbox_item=existing_outbox_item,
        evidence_reference_ids=("outbox-command-evidence-1",),
    )


def _delivery_plan_decision(
    *,
    decision_id: str = "delivery-plan-decision-1",
    delivery_plan_id: str = "delivery-plan-1",
    outbox_decision_id: str = "outbox-decision-1",
    eligibility_decision_id: str = "eligibility-decision-1",
    source_intake_decision_id: str = "source-intake-decision-1",
    source_event_id: str = "source-event-1",
    account_id: str = "account-1",
    beacon_id: str | None = "beacon-1",
    safe_listing_reference_ids: tuple[str, ...] = ("listing-1", "listing-2"),
    telegram_enabled: bool = True,
    max_enabled: bool = True,
) -> NotificationDeliveryPlanDecision:
    return plan_notification_delivery(
        decision_id=decision_id,
        delivery_plan_id=delivery_plan_id,
        outbox_creation_decision=_outbox_creation_decision(
            decision_id=outbox_decision_id,
            eligibility_decision_id=eligibility_decision_id,
            source_intake_decision_id=source_intake_decision_id,
            source_event_id=source_event_id,
            account_id=account_id,
            beacon_id=beacon_id,
            safe_listing_reference_ids=safe_listing_reference_ids,
            telegram_enabled=telegram_enabled,
            max_enabled=max_enabled,
        ),
        evidence_reference_ids=("delivery-plan-evidence-1",),
    )


def _attempt_decision(
    *,
    decision_id: str = "attempt-plan-decision-1",
    delivery_plan_decision_id: str = "delivery-plan-decision-1",
    delivery_plan_id: str = "delivery-plan-1",
    delivery_plan_decision: NotificationDeliveryPlanDecision | None = None,
    outbox_decision_id: str = "outbox-decision-1",
    eligibility_decision_id: str = "eligibility-decision-1",
    source_intake_decision_id: str = "source-intake-decision-1",
    source_event_id: str = "source-event-1",
    channel_class: NotificationChannelClass,
    account_id: str = "account-1",
    beacon_id: str | None = "beacon-1",
    safe_listing_reference_ids: tuple[str, ...] = ("listing-1", "listing-2"),
    telegram_enabled: bool = True,
    max_enabled: bool = True,
    attempt_id: str = "attempt-1",
) -> NotificationAttemptPlanningDecision:
    if delivery_plan_decision is None:
        delivery_plan_decision = _delivery_plan_decision(
            decision_id=delivery_plan_decision_id,
            delivery_plan_id=delivery_plan_id,
            outbox_decision_id=outbox_decision_id,
            eligibility_decision_id=eligibility_decision_id,
            source_intake_decision_id=source_intake_decision_id,
            source_event_id=source_event_id,
            account_id=account_id,
            beacon_id=beacon_id,
            safe_listing_reference_ids=safe_listing_reference_ids,
            telegram_enabled=telegram_enabled,
            max_enabled=max_enabled,
        )
    return plan_notification_attempt(
        decision_id=decision_id,
        attempt_id=attempt_id,
        delivery_plan_decision=delivery_plan_decision,
        channel_class=channel_class,
        idempotency_key=IdempotencyKey(value="attempt-idempotency-key-1"),
        idempotency_fingerprint=IdempotencyFingerprint(value="attempt-idempotency-fingerprint-1"),
        idempotency_scope=IdempotencyScope(value="attempt-idempotency-scope-1"),
        evidence_reference_ids=("attempt-plan-evidence-1",),
    )


def _provider_outcome_reference(
    attempt: NotificationAttempt,
    *,
    outcome_class: NotificationProviderOutcomeClass,
    outcome_reference_id: str,
    provider_safe_delivery_reference: str | None = None,
    adapter_outcome_committed: bool = True,
    contains_raw_provider_payload: bool = False,
    identity_ambiguous: bool = False,
    target_reference_id: str | None = None,
    correlation_id: str | None = None,
    causation_id: str | None = None,
) -> NotificationProviderOutcomeReference:
    return NotificationProviderOutcomeReference(
        outcome_reference_id=outcome_reference_id,
        adapter_contract="provider.adapter.v1",
        adapter_contract_version="1.0",
        attempt_id=attempt.attempt_id,
        channel_class=attempt.channel_class,
        target_reference_id=target_reference_id or attempt.target_reference_id,
        outcome_class=outcome_class,
        adapter_outcome_committed=adapter_outcome_committed,
        provider_safe_delivery_reference=provider_safe_delivery_reference,
        egress_correlation_reference="egress-correlation-1",
        contains_raw_provider_payload=contains_raw_provider_payload,
        identity_ambiguous=identity_ambiguous,
        correlation_id=correlation_id or attempt.correlation_id,
        causation_id=causation_id or attempt.causation_id,
        reason_codes=(),
        evidence_reference_ids=("provider-outcome-evidence-1",),
    )


def _accepted_provider_outcome_decision(
    attempt_decision: NotificationAttemptPlanningDecision,
    *,
    decision_id: str = "provider-acceptance-decision-1",
    outcome_class: NotificationProviderOutcomeClass,
    outcome_reference_id: str,
    provider_safe_delivery_reference: str | None = None,
) -> NotificationProviderOutcomeAcceptanceDecision:
    attempt = attempt_decision.attempt
    assert attempt is not None
    return accept_notification_provider_outcome(
        decision_id=decision_id,
        attempt=attempt,
        provider_outcome=_provider_outcome_reference(
            attempt,
            outcome_class=outcome_class,
            outcome_reference_id=outcome_reference_id,
            provider_safe_delivery_reference=provider_safe_delivery_reference,
        ),
        evidence_reference_ids=("provider-acceptance-evidence-1",),
    )


def _replayed_provider_outcome_decision(
    accepted_decision: NotificationProviderOutcomeAcceptanceDecision,
    *,
    decision_id: str = "provider-replay-decision-1",
    outcome_reference_id: str,
) -> NotificationProviderOutcomeAcceptanceDecision:
    previous_attempt = accepted_decision.previous_attempt
    assert previous_attempt is not None
    replayed_provider_outcome = _provider_outcome_reference(
        previous_attempt,
        outcome_class=accepted_decision.provider_outcome.outcome_class,
        outcome_reference_id=outcome_reference_id,
        provider_safe_delivery_reference=accepted_decision.provider_outcome.provider_safe_delivery_reference,
    )
    return replace(
        accepted_decision,
        decision_id=decision_id,
        provider_outcome=replayed_provider_outcome,
        status=NotificationProviderOutcomeAcceptanceStatus.REPLAYED,
        resulting_attempt=previous_attempt,
        outcome_accepted=True,
        replayed=True,
        reason_codes=("provider-outcome-replayed",),
        evidence_reference_ids=("provider-replay-evidence-1",),
    )


def _batch_input(
    batch_item_id: str,
    source_decision,
    *,
    outbox_item_context: NotificationOutboxItem | None = None,
    evidence_reference_ids: tuple[str, ...] = ("batch-item-evidence-1",),
) -> NotificationBatchItemInput:
    return NotificationBatchItemInput(
        batch_item_id=batch_item_id,
        source_decision=source_decision,
        outbox_item_context=outbox_item_context,
        evidence_reference_ids=evidence_reference_ids,
    )


def _project(
    *item_inputs: NotificationBatchItemInput,
    evidence_reference_ids: tuple[str, ...] = ("batch-command-evidence-1",),
) -> NotificationBatchDecision:
    return project_notification_batch_outcomes(
        batch_id="batch-1",
        item_inputs=item_inputs,
        evidence_reference_ids=evidence_reference_ids,
    )


def test_each_source_decision_type_projects_to_the_expected_stage() -> None:
    outbox_decision = _outbox_creation_decision()
    delivery_plan_decision = _delivery_plan_decision()
    attempt_decision = _attempt_decision(channel_class=NotificationChannelClass.TELEGRAM)
    provider_accepted = _accepted_provider_outcome_decision(
        attempt_decision,
        outcome_class=NotificationProviderOutcomeClass.PROVIDER_ACCEPTED,
        outcome_reference_id="provider-outcome-delivered-1",
        provider_safe_delivery_reference="safe-delivery-1",
    )
    dedup_request = NotificationDeduplicationRequest(
        stage=NotificationDeduplicationStage.OUTBOX_CREATION,
        source_family=NotificationSourceFamily.EXTERNAL_UNAVAILABLE_STATUS,
        account_id="account-1",
        beacon_id="beacon-1",
        channel_class=None,
        semantic_effect_reference_id="semantic-effect-1",
        idempotency_key=IdempotencyKey(value="dedup-idempotency-key-1"),
        idempotency_fingerprint=IdempotencyFingerprint(value="dedup-idempotency-fingerprint-1"),
        idempotency_scope=IdempotencyScope(value="dedup-idempotency-scope-1"),
        proposed_record_state=NotificationDeduplicationRecordState.TERMINAL,
        proposed_result_reference_id="dedup-result-1",
        correlation_id="dedup-correlation-1",
        causation_id="dedup-causation-1",
        evidence_reference_ids=("dedup-request-evidence-1",),
    )
    dedup_decision = evaluate_notification_deduplication(
        decision_id="dedup-decision-1",
        record_id="dedup-record-1",
        request=dedup_request,
        existing_record=None,
        evidence_reference_ids=("dedup-command-evidence-1",),
    )

    cases = [
        (
            _batch_input("dedup", dedup_decision),
            NotificationBatchStage.DEDUPLICATION,
            NotificationBatchDisposition.CREATED,
            BatchSafeErrorCategory.NONE,
        ),
        (
            _batch_input("outbox", outbox_decision),
            NotificationBatchStage.OUTBOX_CREATION,
            NotificationBatchDisposition.CREATED,
            BatchSafeErrorCategory.NONE,
        ),
        (
            _batch_input("plan", delivery_plan_decision),
            NotificationBatchStage.DELIVERY_PLAN,
            NotificationBatchDisposition.CREATED,
            BatchSafeErrorCategory.NONE,
        ),
        (
            _batch_input("attempt", attempt_decision),
            NotificationBatchStage.ATTEMPT_PLANNING,
            NotificationBatchDisposition.CREATED,
            BatchSafeErrorCategory.NONE,
        ),
        (
            _batch_input(
                "provider",
                provider_accepted,
                outbox_item_context=attempt_decision.delivery_plan_decision.delivery_plan.outbox_item,
            ),
            NotificationBatchStage.PROVIDER_OUTCOME,
            NotificationBatchDisposition.DELIVERED,
            BatchSafeErrorCategory.NONE,
        ),
    ]

    for item_input, expected_stage, expected_disposition, expected_error in cases:
        item_result = NotificationBatchItemResult(
            **{
                "batch_item_id": item_input.batch_item_id,
                "authority": NotificationBatchAuthority.NOTIFICATION_DELIVERY_SERVER,
                "item_input": item_input,
                "stage": expected_stage,
                "source_decision_id": item_input.source_decision.decision_id,
                "account_id": _project(item_input).item_results[0].account_id,
                "beacon_id": _project(item_input).item_results[0].beacon_id,
                "channel_class": _project(item_input).item_results[0].channel_class,
                "outbox_item_id": _project(item_input).item_results[0].outbox_item_id,
                "attempt_id": _project(item_input).item_results[0].attempt_id,
                "safe_result_reference_id": _project(item_input)
                .item_results[0]
                .safe_result_reference_id,
                "safe_listing_reference_ids": _project(item_input)
                .item_results[0]
                .safe_listing_reference_ids,
                "disposition": expected_disposition,
                "safe_error_category": expected_error,
                "replayed": _project(item_input).item_results[0].replayed,
                "delivery_accepted": _project(item_input).item_results[0].delivery_accepted,
                "reconciliation_required": _project(item_input)
                .item_results[0]
                .reconciliation_required,
                "retry_policy_required": _project(item_input).item_results[0].retry_policy_required,
                "execution_authorized": False,
                "provider_mapping_authorized": False,
                "reason_codes": _project(item_input).item_results[0].reason_codes,
                "evidence_reference_ids": _project(item_input)
                .item_results[0]
                .evidence_reference_ids,
            }
        )
        assert item_result.stage is expected_stage
        assert item_result.disposition is expected_disposition
        assert item_result.safe_error_category is expected_error
        assert item_result.execution_authorized is False
        assert item_result.provider_mapping_authorized is False


def test_outbox_creation_semantics_cover_created_replayed_suppressed_and_blocked() -> None:
    created = _outbox_creation_decision(
        decision_id="outbox-created-1",
        eligibility_decision_id="eligibility-created-1",
        source_intake_decision_id="source-intake-created-1",
        source_event_id="source-event-created-1",
        outbox_item_id="outbox-item-created-1",
    )
    replayed = _outbox_creation_decision(
        decision_id="outbox-replayed-1",
        eligibility_decision_id="eligibility-created-1",
        source_intake_decision_id="source-intake-created-1",
        source_event_id="source-event-created-1",
        outbox_item_id="outbox-item-created-1",
        existing_outbox_item=created.outbox_item,
    )
    suppressed = _outbox_creation_decision(
        decision_id="outbox-suppressed-1",
        eligibility_decision_id="eligibility-suppressed-1",
        source_intake_decision_id="source-intake-suppressed-1",
        source_event_id="source-event-suppressed-1",
        telegram_enabled=False,
        max_enabled=False,
    )
    mismatch = create_notification_outbox_item(
        decision_id="outbox-mismatch-1",
        outbox_item_id=created.outbox_item.outbox_item_id,
        outbox_contract="outbox.contract.v1",
        outbox_contract_version="1.0",
        eligibility_decision=_eligibility_decision(
            decision_id="eligibility-mismatch-1",
            source_intake_decision_id="source-intake-mismatch-1",
            source_event_id="source-event-created-1",
        ),
        idempotency_key=IdempotencyKey(value="outbox-idempotency-key-1"),
        idempotency_fingerprint=IdempotencyFingerprint(
            value="outbox-idempotency-fingerprint-mismatch-1"
        ),
        idempotency_scope=IdempotencyScope(value="outbox-idempotency-scope-1"),
        existing_outbox_item=created.outbox_item,
        evidence_reference_ids=("outbox-command-evidence-mismatch-1",),
    )

    created_result = _project(_batch_input("created", created)).item_results[0]
    replayed_result = _project(_batch_input("replayed", replayed)).item_results[0]
    suppressed_result = _project(_batch_input("suppressed", suppressed)).item_results[0]
    mismatch_result = _project(_batch_input("mismatch", mismatch)).item_results[0]

    assert created_result.disposition is NotificationBatchDisposition.CREATED
    assert created_result.safe_error_category is BatchSafeErrorCategory.NONE
    assert created_result.outbox_item_id == created.outbox_item.outbox_item_id
    assert replayed_result.disposition is NotificationBatchDisposition.REPLAYED
    assert replayed_result.replayed is True
    assert replayed_result.outbox_item_id == created.outbox_item.outbox_item_id
    assert suppressed_result.disposition is NotificationBatchDisposition.SUPPRESSED
    assert suppressed_result.safe_error_category is BatchSafeErrorCategory.ELIGIBILITY_BLOCKED
    assert mismatch_result.disposition is NotificationBatchDisposition.BLOCKED
    assert mismatch_result.safe_error_category is BatchSafeErrorCategory.IDEMPOTENCY_BLOCKED


def test_delivery_plan_semantics_cover_planned_and_blocked_variants() -> None:
    planned = _delivery_plan_decision()
    blocked_outbox = replace(
        planned,
        status=NotificationDeliveryPlanDecisionStatus.BLOCKED_OUTBOX,
        delivery_plan=None,
        plan_created=False,
        reason_codes=("delivery-plan-outbox-blocked",),
    )
    blocked_ambiguous = replace(
        planned,
        status=NotificationDeliveryPlanDecisionStatus.BLOCKED_CHANNEL_PLAN_AMBIGUOUS,
        delivery_plan=None,
        plan_created=False,
        reason_codes=("delivery-plan-channel-evidence-ambiguous",),
    )
    blocked_no_push = replace(
        planned,
        status=NotificationDeliveryPlanDecisionStatus.BLOCKED_NO_PUSH_CHANNEL,
        delivery_plan=None,
        plan_created=False,
        reason_codes=("delivery-plan-no-push-channel",),
    )

    planned_result = _project(_batch_input("planned", planned)).item_results[0]
    blocked_outbox_result = _project(_batch_input("blocked-outbox", blocked_outbox)).item_results[0]
    blocked_ambiguous_result = _project(
        _batch_input("blocked-ambiguous", blocked_ambiguous)
    ).item_results[0]
    blocked_no_push_result = _project(
        _batch_input("blocked-no-push", blocked_no_push)
    ).item_results[0]

    assert planned_result.disposition is NotificationBatchDisposition.CREATED
    assert planned_result.safe_error_category is BatchSafeErrorCategory.NONE
    assert blocked_outbox_result.disposition is NotificationBatchDisposition.BLOCKED
    assert blocked_outbox_result.safe_error_category is BatchSafeErrorCategory.DELIVERY_PLAN_BLOCKED
    assert (
        blocked_ambiguous_result.safe_error_category is BatchSafeErrorCategory.CHANNEL_PLAN_BLOCKED
    )
    assert blocked_no_push_result.safe_error_category is BatchSafeErrorCategory.CHANNEL_PLAN_BLOCKED


def test_attempt_planning_semantics_cover_planned_and_blocked_variants() -> None:
    planned_telegram = _attempt_decision(channel_class=NotificationChannelClass.TELEGRAM)
    planned_max = _attempt_decision(channel_class=NotificationChannelClass.MAX)
    blocked_delivery_plan = replace(
        planned_telegram,
        status=NotificationAttemptPlanningStatus.BLOCKED_DELIVERY_PLAN,
        attempt=None,
        attempt_created=False,
        reason_codes=("attempt-delivery-plan-blocked",),
    )
    blocked_channel_plan = replace(
        planned_max,
        status=NotificationAttemptPlanningStatus.BLOCKED_CHANNEL_PLAN,
        attempt=None,
        attempt_created=False,
        reason_codes=("attempt-channel-plan-blocked",),
    )

    telegram_result = _project(_batch_input("telegram", planned_telegram)).item_results[0]
    max_result = _project(_batch_input("max", planned_max)).item_results[0]
    blocked_delivery_plan_result = _project(
        _batch_input("blocked-delivery", blocked_delivery_plan)
    ).item_results[0]
    blocked_channel_plan_result = _project(
        _batch_input("blocked-channel", blocked_channel_plan)
    ).item_results[0]

    assert telegram_result.channel_class is NotificationChannelClass.TELEGRAM
    assert max_result.channel_class is NotificationChannelClass.MAX
    assert (
        blocked_delivery_plan_result.safe_error_category
        is BatchSafeErrorCategory.DELIVERY_PLAN_BLOCKED
    )
    assert (
        blocked_channel_plan_result.safe_error_category
        is BatchSafeErrorCategory.CHANNEL_PLAN_BLOCKED
    )


def test_provider_outcome_semantics_cover_delivered_failed_ambiguous_and_replay_variants() -> None:
    attempt_decision = _attempt_decision(channel_class=NotificationChannelClass.TELEGRAM)
    assert attempt_decision.attempt is not None

    delivered = _accepted_provider_outcome_decision(
        attempt_decision,
        outcome_class=NotificationProviderOutcomeClass.PROVIDER_ACCEPTED,
        outcome_reference_id="provider-delivered-1",
        provider_safe_delivery_reference="safe-delivery-1",
    )
    failed = _accepted_provider_outcome_decision(
        attempt_decision,
        outcome_class=NotificationProviderOutcomeClass.DELIVERY_FAILURE,
        outcome_reference_id="provider-failed-1",
    )
    ambiguous = _accepted_provider_outcome_decision(
        attempt_decision,
        outcome_class=NotificationProviderOutcomeClass.DELIVERY_AMBIGUOUS,
        outcome_reference_id="provider-ambiguous-1",
    )
    replayed_delivered = _replayed_provider_outcome_decision(
        delivered, outcome_reference_id="provider-delivered-replay-1"
    )
    replayed_failed = _replayed_provider_outcome_decision(
        failed, outcome_reference_id="provider-failed-replay-1"
    )
    replayed_ambiguous = _replayed_provider_outcome_decision(
        ambiguous, outcome_reference_id="provider-ambiguous-replay-1"
    )

    context = attempt_decision.delivery_plan_decision.delivery_plan.outbox_item
    assert context is not None

    delivered_result = _project(
        _batch_input("delivered", delivered, outbox_item_context=context)
    ).item_results[0]
    failed_result = _project(
        _batch_input("failed", failed, outbox_item_context=context)
    ).item_results[0]
    ambiguous_result = _project(
        _batch_input("ambiguous", ambiguous, outbox_item_context=context)
    ).item_results[0]
    replayed_delivered_result = _project(
        _batch_input("replayed-delivered", replayed_delivered, outbox_item_context=context)
    ).item_results[0]
    replayed_failed_result = _project(
        _batch_input("replayed-failed", replayed_failed, outbox_item_context=context)
    ).item_results[0]
    replayed_ambiguous_result = _project(
        _batch_input("replayed-ambiguous", replayed_ambiguous, outbox_item_context=context)
    ).item_results[0]

    assert delivered_result.disposition is NotificationBatchDisposition.DELIVERED
    assert delivered_result.delivery_accepted is True
    assert failed_result.disposition is NotificationBatchDisposition.FAILED
    assert failed_result.safe_error_category is BatchSafeErrorCategory.PROVIDER_FAILURE
    assert failed_result.retry_policy_required is True
    assert ambiguous_result.disposition is NotificationBatchDisposition.RECONCILIATION_REQUIRED
    assert ambiguous_result.safe_error_category is BatchSafeErrorCategory.AMBIGUOUS_RECONCILIATION
    assert ambiguous_result.reconciliation_required is True
    assert replayed_delivered_result.disposition is NotificationBatchDisposition.REPLAYED
    assert replayed_delivered_result.delivery_accepted is True
    assert replayed_delivered_result.safe_error_category is BatchSafeErrorCategory.NONE
    assert replayed_delivered_result.retry_policy_required is False
    assert replayed_failed_result.disposition is NotificationBatchDisposition.REPLAYED
    assert replayed_failed_result.safe_error_category is BatchSafeErrorCategory.PROVIDER_FAILURE
    assert replayed_failed_result.retry_policy_required is True
    assert replayed_failed_result.execution_authorized is False
    assert replayed_failed_result.provider_mapping_authorized is False
    assert replayed_failed_result.reason_codes == ("batch-item-replayed",)
    assert replayed_failed_result.attempt_id == failed_result.attempt_id
    assert replayed_failed_result.outbox_item_id == failed_result.outbox_item_id
    assert replayed_ambiguous_result.disposition is NotificationBatchDisposition.REPLAYED
    assert (
        replayed_ambiguous_result.safe_error_category
        is BatchSafeErrorCategory.AMBIGUOUS_RECONCILIATION
    )
    assert replayed_ambiguous_result.retry_policy_required is False
    assert replayed_ambiguous_result.reason_codes == ("batch-item-replayed",)


@pytest.mark.parametrize(
    "outcome_class",
    [
        NotificationProviderOutcomeClass.PROVIDER_REJECTED,
        NotificationProviderOutcomeClass.PROVIDER_UNAVAILABLE,
        NotificationProviderOutcomeClass.RATE_OR_ACCESS_RESTRICTED,
        NotificationProviderOutcomeClass.MALFORMED_OR_UNUSABLE_PROVIDER_RESPONSE,
        NotificationProviderOutcomeClass.DELIVERY_FAILURE,
        NotificationProviderOutcomeClass.SUPPRESSED_OR_CANCELLED,
        NotificationProviderOutcomeClass.TARGET_UNAVAILABLE_OR_UNVERIFIED,
    ],
    ids=[
        "PROVIDER_REJECTED",
        "PROVIDER_UNAVAILABLE",
        "RATE_OR_ACCESS_RESTRICTED",
        "MALFORMED_OR_UNUSABLE_PROVIDER_RESPONSE",
        "DELIVERY_FAILURE",
        "SUPPRESSED_OR_CANCELLED",
        "TARGET_UNAVAILABLE_OR_UNVERIFIED",
    ],
)
def test_provider_failure_replay_requires_policy_decision_for_all_failure_classes(
    outcome_class: NotificationProviderOutcomeClass,
) -> None:
    attempt_decision = _attempt_decision(channel_class=NotificationChannelClass.TELEGRAM)
    assert attempt_decision.attempt is not None
    context = attempt_decision.delivery_plan_decision.delivery_plan.outbox_item
    assert context is not None

    accepted_failure = _accepted_provider_outcome_decision(
        attempt_decision,
        outcome_class=outcome_class,
        outcome_reference_id=f"accepted-{outcome_class.value.lower()}-1",
    )
    accepted_failure_snapshot = (
        accepted_failure.status,
        accepted_failure.replayed,
        accepted_failure.reason_codes,
        accepted_failure.provider_outcome.outcome_class,
        accepted_failure.previous_attempt.attempt_id,
        accepted_failure.resulting_attempt.attempt_id,
    )
    replayed_failure = _replayed_provider_outcome_decision(
        accepted_failure,
        outcome_reference_id=f"replayed-{outcome_class.value.lower()}-1",
    )
    replayed_failure_snapshot = (
        replayed_failure.status,
        replayed_failure.replayed,
        replayed_failure.reason_codes,
        replayed_failure.provider_outcome.outcome_class,
        replayed_failure.previous_attempt.attempt_id,
        replayed_failure.resulting_attempt is replayed_failure.previous_attempt,
    )

    accepted_result = _project(
        _batch_input(
            f"accepted-failure-{outcome_class.value.lower()}",
            accepted_failure,
            outbox_item_context=context,
        )
    ).item_results[0]
    replayed_result = _project(
        _batch_input(
            f"replayed-failure-{outcome_class.value.lower()}",
            replayed_failure,
            outbox_item_context=context,
        )
    ).item_results[0]

    assert accepted_result.disposition is NotificationBatchDisposition.FAILED
    assert accepted_result.safe_error_category is BatchSafeErrorCategory.PROVIDER_FAILURE
    assert accepted_result.replayed is False
    assert accepted_result.delivery_accepted is False
    assert accepted_result.reconciliation_required is False
    assert accepted_result.retry_policy_required is True
    assert accepted_result.execution_authorized is False
    assert accepted_result.provider_mapping_authorized is False
    assert accepted_result.attempt_id == attempt_decision.attempt.attempt_id
    assert accepted_result.outbox_item_id == context.outbox_item_id
    assert accepted_result.reason_codes == ("batch-item-failed",)

    assert replayed_result.disposition is NotificationBatchDisposition.REPLAYED
    assert replayed_result.safe_error_category is BatchSafeErrorCategory.PROVIDER_FAILURE
    assert replayed_result.replayed is True
    assert replayed_result.delivery_accepted is False
    assert replayed_result.reconciliation_required is False
    assert replayed_result.retry_policy_required is True
    assert replayed_result.execution_authorized is False
    assert replayed_result.provider_mapping_authorized is False
    assert replayed_result.attempt_id == attempt_decision.attempt.attempt_id
    assert replayed_result.outbox_item_id == context.outbox_item_id
    assert replayed_result.reason_codes == ("batch-item-replayed",)

    assert accepted_failure.status is accepted_failure_snapshot[0]
    assert accepted_failure.replayed is accepted_failure_snapshot[1]
    assert accepted_failure.reason_codes == accepted_failure_snapshot[2]
    assert accepted_failure.provider_outcome.outcome_class is accepted_failure_snapshot[3]
    assert accepted_failure.previous_attempt.attempt_id == accepted_failure_snapshot[4]
    assert accepted_failure.resulting_attempt is not accepted_failure.previous_attempt
    assert accepted_failure.resulting_attempt is not None
    assert accepted_failure.resulting_attempt.attempt_id == accepted_failure_snapshot[5]
    assert replayed_failure.status is replayed_failure_snapshot[0]
    assert replayed_failure.replayed is replayed_failure_snapshot[1]
    assert replayed_failure.reason_codes == replayed_failure_snapshot[2]
    assert replayed_failure.provider_outcome.outcome_class is replayed_failure_snapshot[3]
    assert replayed_failure.previous_attempt.attempt_id == replayed_failure_snapshot[4]
    assert replayed_failure.resulting_attempt is replayed_failure.previous_attempt


def test_replayed_failure_items_count_toward_batch_retry_policy_required_count() -> None:
    attempt_decision = _attempt_decision(channel_class=NotificationChannelClass.TELEGRAM)
    assert attempt_decision.attempt is not None
    context = attempt_decision.delivery_plan_decision.delivery_plan.outbox_item
    assert context is not None

    replayed_items = [
        _batch_input(
            f"replayed-{outcome_class.value.lower()}",
            _replayed_provider_outcome_decision(
                _accepted_provider_outcome_decision(
                    attempt_decision,
                    decision_id=f"accepted-{outcome_class.value.lower()}",
                    outcome_class=outcome_class,
                    outcome_reference_id=f"accepted-{outcome_class.value.lower()}-1",
                ),
                decision_id=f"replayed-{outcome_class.value.lower()}",
                outcome_reference_id=f"replayed-{outcome_class.value.lower()}-1",
            ),
            outbox_item_context=context,
        )
        for outcome_class in (
            NotificationProviderOutcomeClass.PROVIDER_REJECTED,
            NotificationProviderOutcomeClass.PROVIDER_UNAVAILABLE,
            NotificationProviderOutcomeClass.RATE_OR_ACCESS_RESTRICTED,
            NotificationProviderOutcomeClass.MALFORMED_OR_UNUSABLE_PROVIDER_RESPONSE,
            NotificationProviderOutcomeClass.DELIVERY_FAILURE,
            NotificationProviderOutcomeClass.SUPPRESSED_OR_CANCELLED,
            NotificationProviderOutcomeClass.TARGET_UNAVAILABLE_OR_UNVERIFIED,
        )
    ]

    decision = _project(*replayed_items)

    assert decision.retry_policy_required_count == len(replayed_items)
    assert decision.replayed_count == len(replayed_items)
    assert decision.failed_count == 0
    assert decision.reason_codes == ("batch-all-accepted",)


@pytest.mark.parametrize(
    ("mutation", "expected_status"),
    [
        ("uncommitted", NotificationProviderOutcomeAcceptanceStatus.REJECTED_UNCOMMITTED),
        ("unsafe", NotificationProviderOutcomeAcceptanceStatus.REJECTED_UNSAFE_PAYLOAD),
        ("identity", NotificationProviderOutcomeAcceptanceStatus.REJECTED_IDENTITY_AMBIGUOUS),
        ("scope", NotificationProviderOutcomeAcceptanceStatus.REJECTED_SCOPE_MISMATCH),
    ],
)
def test_rejected_provider_outcome_acceptance_status_is_blocked(
    mutation: str,
    expected_status: NotificationProviderOutcomeAcceptanceStatus,
) -> None:
    attempt_decision = _attempt_decision(channel_class=NotificationChannelClass.TELEGRAM)
    assert attempt_decision.attempt is not None
    context = attempt_decision.delivery_plan_decision.delivery_plan.outbox_item
    assert context is not None

    provider_outcome = _provider_outcome_reference(
        attempt_decision.attempt,
        outcome_class=NotificationProviderOutcomeClass.PROVIDER_ACCEPTED,
        outcome_reference_id="provider-rejected-1",
        provider_safe_delivery_reference="safe-delivery-1",
    )
    if mutation == "uncommitted":
        provider_outcome = replace(provider_outcome, adapter_outcome_committed=False)
    elif mutation == "unsafe":
        provider_outcome = replace(provider_outcome, contains_raw_provider_payload=True)
    elif mutation == "identity":
        provider_outcome = replace(provider_outcome, identity_ambiguous=True)
    elif mutation == "scope":
        provider_outcome = replace(provider_outcome, target_reference_id="wrong-target")

    decision = accept_notification_provider_outcome(
        decision_id="provider-rejected-decision-1",
        attempt=attempt_decision.attempt,
        provider_outcome=provider_outcome,
        evidence_reference_ids=("provider-rejected-evidence-1",),
    )

    result = _project(_batch_input("rejected", decision, outbox_item_context=context)).item_results[
        0
    ]
    assert decision.status is expected_status
    assert result.disposition is NotificationBatchDisposition.BLOCKED
    assert result.safe_error_category is BatchSafeErrorCategory.PROVIDER_OUTCOME_REJECTED
    assert result.retry_policy_required is False


def test_mixed_telegram_delivered_and_max_failed_is_partial_outcome() -> None:
    delivery_plan_decision = _delivery_plan_decision(
        decision_id="delivery-plan-shared-partial-1",
        outbox_decision_id="outbox-shared-partial-1",
        eligibility_decision_id="eligibility-shared-partial-1",
        source_intake_decision_id="source-intake-shared-partial-1",
        source_event_id="source-event-shared-partial-1",
    )
    telegram_attempt = _attempt_decision(
        decision_id="attempt-plan-telegram-1",
        delivery_plan_decision=delivery_plan_decision,
        channel_class=NotificationChannelClass.TELEGRAM,
        attempt_id="attempt-telegram-1",
    )
    max_attempt = _attempt_decision(
        decision_id="attempt-plan-max-1",
        delivery_plan_decision=delivery_plan_decision,
        channel_class=NotificationChannelClass.MAX,
        attempt_id="attempt-max-1",
    )
    assert telegram_attempt.attempt is not None
    assert max_attempt.attempt is not None
    context = telegram_attempt.delivery_plan_decision.delivery_plan.outbox_item
    assert context is not None

    telegram_delivered = _accepted_provider_outcome_decision(
        telegram_attempt,
        decision_id="provider-telegram-delivered-1",
        outcome_class=NotificationProviderOutcomeClass.PROVIDER_ACCEPTED,
        outcome_reference_id="telegram-delivered-1",
        provider_safe_delivery_reference="telegram-safe-1",
    )
    max_failed = _accepted_provider_outcome_decision(
        max_attempt,
        decision_id="provider-max-failed-1",
        outcome_class=NotificationProviderOutcomeClass.DELIVERY_FAILURE,
        outcome_reference_id="max-failed-1",
    )

    decision = _project(
        _batch_input("telegram-delivered", telegram_delivered, outbox_item_context=context),
        _batch_input("max-failed", max_failed, outbox_item_context=context),
        evidence_reference_ids=("batch-evidence-1", "shared", "batch-evidence-2"),
    )

    assert decision.status is NotificationBatchDecisionStatus.PARTIAL_OUTCOME
    assert decision.accepted_count == 1
    assert decision.delivered_count == 1
    assert decision.failed_count == 1
    assert decision.retry_policy_required_count == 1
    assert decision.reason_codes == ("batch-partial-outcome",)


def test_delivered_plus_blocked_is_partial_outcome() -> None:
    attempt_decision = _attempt_decision(channel_class=NotificationChannelClass.TELEGRAM)
    assert attempt_decision.attempt is not None
    context = attempt_decision.delivery_plan_decision.delivery_plan.outbox_item
    assert context is not None

    delivered = _accepted_provider_outcome_decision(
        attempt_decision,
        outcome_class=NotificationProviderOutcomeClass.PROVIDER_ACCEPTED,
        outcome_reference_id="delivered-1",
        provider_safe_delivery_reference="safe-delivery-1",
    )
    blocked = accept_notification_provider_outcome(
        decision_id="blocked-1",
        attempt=attempt_decision.attempt,
        provider_outcome=replace(
            _provider_outcome_reference(
                attempt_decision.attempt,
                outcome_class=NotificationProviderOutcomeClass.PROVIDER_ACCEPTED,
                outcome_reference_id="blocked-1",
                provider_safe_delivery_reference="safe-delivery-1",
            ),
            adapter_outcome_committed=False,
        ),
        evidence_reference_ids=("blocked-evidence-1",),
    )

    decision = _project(
        _batch_input("delivered", delivered, outbox_item_context=context),
        _batch_input("blocked", blocked, outbox_item_context=context),
    )

    assert decision.status is NotificationBatchDecisionStatus.PARTIAL_OUTCOME
    assert decision.accepted_count == 1
    assert decision.blocked_count == 1


def test_any_reconciliation_requires_batch_reconciliation_status() -> None:
    attempt_decision = _attempt_decision(channel_class=NotificationChannelClass.TELEGRAM)
    assert attempt_decision.attempt is not None
    context = attempt_decision.delivery_plan_decision.delivery_plan.outbox_item
    assert context is not None

    ambiguous = _accepted_provider_outcome_decision(
        attempt_decision,
        outcome_class=NotificationProviderOutcomeClass.DELIVERY_AMBIGUOUS,
        outcome_reference_id="ambiguous-1",
    )
    decision = _project(_batch_input("ambiguous", ambiguous, outbox_item_context=context))

    assert decision.status is NotificationBatchDecisionStatus.RECONCILIATION_REQUIRED
    assert decision.reconciliation_count == 1
    assert decision.reason_codes == ("batch-reconciliation-required",)


def test_all_created_replayed_or_delivered_items_are_all_accepted() -> None:
    created = _outbox_creation_decision(
        decision_id="outbox-created-all-accepted-1",
        eligibility_decision_id="eligibility-created-all-accepted-1",
        source_intake_decision_id="source-intake-created-all-accepted-1",
        source_event_id="source-event-created-all-accepted-1",
        outbox_item_id="outbox-item-created-all-accepted-1",
    )
    replayed = _outbox_creation_decision(
        decision_id="outbox-replayed-all-accepted-1",
        eligibility_decision_id="eligibility-created-all-accepted-1",
        source_intake_decision_id="source-intake-created-all-accepted-1",
        source_event_id="source-event-created-all-accepted-1",
        outbox_item_id="outbox-item-created-all-accepted-1",
        existing_outbox_item=created.outbox_item,
    )
    attempt_decision = _attempt_decision(
        decision_id="attempt-plan-delivered-all-accepted-1",
        delivery_plan_decision_id="delivery-plan-delivered-all-accepted-1",
        outbox_decision_id="outbox-delivered-all-accepted-1",
        channel_class=NotificationChannelClass.TELEGRAM,
        attempt_id="attempt-delivered-all-accepted-1",
    )
    assert attempt_decision.attempt is not None
    context = attempt_decision.delivery_plan_decision.delivery_plan.outbox_item
    assert context is not None
    delivered = _accepted_provider_outcome_decision(
        attempt_decision,
        decision_id="provider-delivered-all-accepted-1",
        outcome_class=NotificationProviderOutcomeClass.PROVIDER_ACCEPTED,
        outcome_reference_id="delivered-all-accepted-1",
        provider_safe_delivery_reference="safe-delivery-1",
    )

    decision = _project(
        _batch_input("created", created),
        _batch_input("replayed", replayed),
        _batch_input("delivered", delivered, outbox_item_context=context),
    )

    assert decision.status is NotificationBatchDecisionStatus.ALL_ACCEPTED
    assert decision.accepted_count == 3
    assert decision.created_count == 1
    assert decision.replayed_count == 1
    assert decision.delivered_count == 1


def test_all_suppressed_blocked_or_failed_items_are_all_blocked_or_failed() -> None:
    suppressed = _outbox_creation_decision(
        decision_id="outbox-suppressed-all-blocked-1",
        eligibility_decision_id="eligibility-suppressed-all-blocked-1",
        source_intake_decision_id="source-intake-suppressed-all-blocked-1",
        source_event_id="source-event-suppressed-all-blocked-1",
        telegram_enabled=False,
        max_enabled=False,
    )
    delivery_plan_blocked = replace(
        _delivery_plan_decision(
            decision_id="delivery-plan-blocked-all-blocked-1",
            outbox_decision_id="outbox-blocked-all-blocked-1",
            eligibility_decision_id="eligibility-blocked-all-blocked-1",
            source_intake_decision_id="source-intake-blocked-all-blocked-1",
            source_event_id="source-event-blocked-all-blocked-1",
        ),
        status=NotificationDeliveryPlanDecisionStatus.BLOCKED_OUTBOX,
        delivery_plan=None,
        plan_created=False,
        reason_codes=("delivery-plan-outbox-blocked",),
    )
    attempt_blocked = replace(
        _attempt_decision(
            decision_id="attempt-plan-blocked-all-blocked-1",
            delivery_plan_decision_id="delivery-plan-attempt-blocked-all-blocked-1",
            outbox_decision_id="outbox-attempt-blocked-all-blocked-1",
            channel_class=NotificationChannelClass.TELEGRAM,
            attempt_id="attempt-blocked-all-blocked-1",
        ),
        status=NotificationAttemptPlanningStatus.BLOCKED_CHANNEL_PLAN,
        attempt=None,
        attempt_created=False,
        reason_codes=("attempt-channel-plan-blocked",),
    )
    provider_failed_attempt = _attempt_decision(
        decision_id="attempt-plan-provider-failed-all-blocked-1",
        delivery_plan_decision_id="delivery-plan-provider-failed-all-blocked-1",
        outbox_decision_id="outbox-provider-failed-all-blocked-1",
        channel_class=NotificationChannelClass.TELEGRAM,
        attempt_id="attempt-provider-failed-all-blocked-1",
    )
    assert provider_failed_attempt.attempt is not None
    context = provider_failed_attempt.delivery_plan_decision.delivery_plan.outbox_item
    assert context is not None
    provider_failed = _accepted_provider_outcome_decision(
        provider_failed_attempt,
        outcome_class=NotificationProviderOutcomeClass.DELIVERY_FAILURE,
        outcome_reference_id="provider-failed-all-blocked-1",
    )

    decision = _project(
        _batch_input("suppressed", suppressed),
        _batch_input("delivery-plan-blocked", delivery_plan_blocked),
        _batch_input("attempt-blocked", attempt_blocked),
        _batch_input("provider-failed", provider_failed, outbox_item_context=context),
    )

    assert decision.status is NotificationBatchDecisionStatus.ALL_BLOCKED_OR_FAILED
    assert decision.accepted_count == 0
    assert decision.suppressed_count == 1
    assert decision.blocked_count == 2
    assert decision.failed_count == 1


def test_different_beacons_under_the_same_account_are_preserved_separately() -> None:
    left = _outbox_creation_decision(
        decision_id="outbox-left-beacon-1",
        eligibility_decision_id="eligibility-left-beacon-1",
        source_intake_decision_id="source-intake-left-beacon-1",
        source_event_id="source-event-left-beacon-1",
        account_id="account-1",
        beacon_id="beacon-1",
        outbox_item_id="outbox-item-left-beacon-1",
    )
    right = _outbox_creation_decision(
        decision_id="outbox-right-beacon-2",
        eligibility_decision_id="eligibility-right-beacon-2",
        source_intake_decision_id="source-intake-right-beacon-2",
        source_event_id="source-event-right-beacon-2",
        account_id="account-1",
        beacon_id="beacon-2",
        outbox_item_id="outbox-item-right-beacon-2",
    )

    decision = _project(
        _batch_input("left", left),
        _batch_input("right", right),
    )

    assert decision.account_id == "account-1"
    assert decision.item_results[0].beacon_id == "beacon-1"
    assert decision.item_results[1].beacon_id == "beacon-2"


def test_provider_context_missing_is_rejected() -> None:
    attempt_decision = _attempt_decision(channel_class=NotificationChannelClass.TELEGRAM)
    assert attempt_decision.attempt is not None
    provider_decision = _accepted_provider_outcome_decision(
        attempt_decision,
        outcome_class=NotificationProviderOutcomeClass.PROVIDER_ACCEPTED,
        outcome_reference_id="provider-context-missing-1",
        provider_safe_delivery_reference="safe-delivery-1",
    )

    with pytest.raises(ValueError):
        _batch_input("missing", provider_decision)


@pytest.mark.parametrize(
    ("mutation", "replacement"),
    [
        ("outbox", {"outbox_item_id": "wrong-outbox"}),
        ("account", {"account_id": "wrong-account"}),
        ("beacon", {"beacon_id": "wrong-beacon"}),
        ("correlation", {"correlation_id": "wrong-correlation"}),
        ("causation", {"causation_id": "wrong-causation"}),
    ],
)
def test_provider_context_mismatches_are_rejected(
    mutation: str, replacement: dict[str, str]
) -> None:
    attempt_decision = _attempt_decision(channel_class=NotificationChannelClass.TELEGRAM)
    assert attempt_decision.attempt is not None
    context = attempt_decision.delivery_plan_decision.delivery_plan.outbox_item
    assert context is not None
    provider_decision = _accepted_provider_outcome_decision(
        attempt_decision,
        outcome_class=NotificationProviderOutcomeClass.PROVIDER_ACCEPTED,
        outcome_reference_id=f"provider-context-{mutation}-1",
        provider_safe_delivery_reference="safe-delivery-1",
    )

    context = replace(context, **replacement)
    with pytest.raises(ValueError):
        _project(_batch_input("provider", provider_decision, outbox_item_context=context))


def test_provider_context_channel_or_target_mismatch_is_rejected() -> None:
    attempt_decision = _attempt_decision(channel_class=NotificationChannelClass.TELEGRAM)
    assert attempt_decision.attempt is not None
    context = attempt_decision.delivery_plan_decision.delivery_plan.outbox_item
    assert context is not None
    provider_decision = _accepted_provider_outcome_decision(
        attempt_decision,
        outcome_class=NotificationProviderOutcomeClass.PROVIDER_ACCEPTED,
        outcome_reference_id="provider-context-channel-target-1",
        provider_safe_delivery_reference="safe-delivery-1",
    )

    wrong_channel_context = replace(
        context,
        channel_intents=(
            replace(context.channel_intents[0], target_reference_id="wrong-target"),
            context.channel_intents[1],
        ),
    )
    with pytest.raises(ValueError):
        _project(
            _batch_input(
                "channel-target", provider_decision, outbox_item_context=wrong_channel_context
            )
        )


def test_mixed_account_batches_are_rejected() -> None:
    left = _outbox_creation_decision(
        decision_id="outbox-left-account-1",
        eligibility_decision_id="eligibility-left-account-1",
        source_intake_decision_id="source-intake-left-account-1",
        source_event_id="source-event-left-account-1",
        account_id="account-1",
        beacon_id="beacon-1",
        outbox_item_id="outbox-item-left-account-1",
    )
    right = _outbox_creation_decision(
        decision_id="outbox-right-account-2",
        eligibility_decision_id="eligibility-right-account-2",
        source_intake_decision_id="source-intake-right-account-2",
        source_event_id="source-event-right-account-2",
        account_id="account-2",
        beacon_id="beacon-2",
        outbox_item_id="outbox-item-right-account-2",
    )

    with pytest.raises(ValueError):
        _project(
            _batch_input("left", left),
            _batch_input("right", right),
        )


def test_duplicate_batch_item_ids_are_rejected() -> None:
    decision = _outbox_creation_decision()
    item_input = _batch_input("duplicate", decision)

    with pytest.raises(ValueError):
        _project(item_input, item_input)


def test_duplicate_source_decision_identity_is_rejected() -> None:
    decision = _outbox_creation_decision()
    first = _batch_input("first", decision)
    second = _batch_input("second", decision)

    with pytest.raises(ValueError):
        _project(first, second)


def test_listing_references_remain_complete_and_ordered_for_telegram_and_max() -> None:
    listing_refs = tuple(f"listing-{index}" for index in range(1, 26))
    delivery_plan_decision = _delivery_plan_decision(
        decision_id="delivery-plan-listing-shared-1",
        outbox_decision_id="outbox-listing-shared-1",
        eligibility_decision_id="eligibility-listing-shared-1",
        source_intake_decision_id="source-intake-listing-shared-1",
        source_event_id="source-event-listing-1",
        account_id="account-1",
        beacon_id="beacon-1",
        safe_listing_reference_ids=listing_refs,
        telegram_enabled=True,
        max_enabled=True,
    )
    outbox_item = delivery_plan_decision.outbox_creation_decision.outbox_item
    assert outbox_item is not None
    assert outbox_item.safe_listing_reference_ids == listing_refs
    context = outbox_item
    telegram_attempt = _attempt_decision(
        decision_id="attempt-plan-listing-telegram-1",
        delivery_plan_decision=delivery_plan_decision,
        channel_class=NotificationChannelClass.TELEGRAM,
        attempt_id="attempt-listing-telegram-1",
    )
    max_attempt = _attempt_decision(
        decision_id="attempt-plan-listing-max-1",
        delivery_plan_decision=delivery_plan_decision,
        channel_class=NotificationChannelClass.MAX,
        attempt_id="attempt-listing-max-1",
    )
    delivered = _accepted_provider_outcome_decision(
        telegram_attempt,
        decision_id="provider-listing-delivered-1",
        outcome_class=NotificationProviderOutcomeClass.PROVIDER_ACCEPTED,
        outcome_reference_id="listing-delivered-1",
        provider_safe_delivery_reference="safe-delivery-1",
    )
    failed = _accepted_provider_outcome_decision(
        max_attempt,
        decision_id="provider-listing-failed-1",
        outcome_class=NotificationProviderOutcomeClass.DELIVERY_FAILURE,
        outcome_reference_id="listing-failed-1",
    )

    decision = _project(
        _batch_input("telegram", delivered, outbox_item_context=context),
        _batch_input("max", failed, outbox_item_context=context),
    )

    assert decision.item_results[0].safe_listing_reference_ids == listing_refs
    assert decision.item_results[1].safe_listing_reference_ids == listing_refs


def test_batch_evidence_order_is_deterministic() -> None:
    attempt_decision = _attempt_decision(
        decision_id="attempt-plan-evidence-1",
        delivery_plan_decision_id="delivery-plan-evidence-1",
        outbox_decision_id="outbox-evidence-1",
        channel_class=NotificationChannelClass.TELEGRAM,
        attempt_id="attempt-evidence-1",
    )
    assert attempt_decision.attempt is not None
    context = attempt_decision.delivery_plan_decision.delivery_plan.outbox_item
    assert context is not None
    delivered = _accepted_provider_outcome_decision(
        attempt_decision,
        outcome_class=NotificationProviderOutcomeClass.PROVIDER_ACCEPTED,
        outcome_reference_id="evidence-order-1",
        provider_safe_delivery_reference="safe-delivery-1",
    )
    item_input = _batch_input(
        "evidence-item",
        delivered,
        outbox_item_context=context,
        evidence_reference_ids=("batch-item-1", "batch-item-2"),
    )
    decision = _project(
        item_input,
        evidence_reference_ids=("batch-1", "batch-2"),
    )

    assert decision.item_results[0].evidence_reference_ids == (
        "delivery-plan-evidence-1",
        "attempt-plan-evidence-1",
        "provider-outcome-evidence-1",
        "provider-acceptance-evidence-1",
        "outbox-command-evidence-1",
        "batch-item-1",
        "batch-item-2",
    )
    assert decision.evidence_reference_ids == (
        "delivery-plan-evidence-1",
        "attempt-plan-evidence-1",
        "provider-outcome-evidence-1",
        "provider-acceptance-evidence-1",
        "outbox-command-evidence-1",
        "batch-item-1",
        "batch-item-2",
        "batch-1",
        "batch-2",
    )


def test_inputs_are_unchanged_by_projection() -> None:
    attempt_decision = _attempt_decision(channel_class=NotificationChannelClass.TELEGRAM)
    assert attempt_decision.attempt is not None
    context = attempt_decision.delivery_plan_decision.delivery_plan.outbox_item
    assert context is not None
    before_item_input = _batch_input(
        "immutability",
        _accepted_provider_outcome_decision(
            attempt_decision,
            outcome_class=NotificationProviderOutcomeClass.PROVIDER_ACCEPTED,
            outcome_reference_id="immutability-1",
            provider_safe_delivery_reference="safe-delivery-1",
        ),
        outbox_item_context=context,
        evidence_reference_ids=("immutability-item-1",),
    )
    before_source_decision = before_item_input.source_decision
    before_context_refs = (
        before_item_input.outbox_item_context.safe_listing_reference_ids
        if before_item_input.outbox_item_context
        else ()
    )
    decision = _project(before_item_input, evidence_reference_ids=("immutability-batch-1",))

    assert before_item_input.source_decision is before_source_decision
    assert before_item_input.outbox_item_context.safe_listing_reference_ids == before_context_refs
    assert decision.item_inputs[0] == before_item_input
    assert (
        decision.item_results[0].safe_listing_reference_ids
        == before_item_input.outbox_item_context.safe_listing_reference_ids
    )


def test_direct_constructor_and_replace_invariants_are_rejected() -> None:
    attempt_decision = _attempt_decision(channel_class=NotificationChannelClass.TELEGRAM)
    assert attempt_decision.attempt is not None
    context = attempt_decision.delivery_plan_decision.delivery_plan.outbox_item
    assert context is not None
    canonical = _project(
        _batch_input(
            "forged",
            _accepted_provider_outcome_decision(
                attempt_decision,
                outcome_class=NotificationProviderOutcomeClass.PROVIDER_ACCEPTED,
                outcome_reference_id="forged-1",
                provider_safe_delivery_reference="safe-delivery-1",
            ),
            outbox_item_context=context,
        )
    )
    canonical_result = canonical.item_results[0]

    with pytest.raises(ValueError):
        NotificationBatchItemResult(
            batch_item_id=canonical_result.batch_item_id,
            authority=canonical_result.authority,
            item_input=canonical_result.item_input,
            stage=canonical_result.stage,
            source_decision_id=canonical_result.source_decision_id,
            account_id=canonical_result.account_id,
            beacon_id=canonical_result.beacon_id,
            channel_class=canonical_result.channel_class,
            outbox_item_id=canonical_result.outbox_item_id,
            attempt_id=canonical_result.attempt_id,
            safe_result_reference_id=canonical_result.safe_result_reference_id,
            safe_listing_reference_ids=("short",),
            disposition=canonical_result.disposition,
            safe_error_category=canonical_result.safe_error_category,
            replayed=canonical_result.replayed,
            delivery_accepted=canonical_result.delivery_accepted,
            reconciliation_required=canonical_result.reconciliation_required,
            retry_policy_required=canonical_result.retry_policy_required,
            execution_authorized=canonical_result.execution_authorized,
            provider_mapping_authorized=canonical_result.provider_mapping_authorized,
            reason_codes=canonical_result.reason_codes,
            evidence_reference_ids=canonical_result.evidence_reference_ids,
        )

    with pytest.raises(ValueError):
        replace(canonical_result, safe_error_category=BatchSafeErrorCategory.PROVIDER_FAILURE)

    with pytest.raises(ValueError):
        replace(canonical, status=NotificationBatchDecisionStatus.ALL_BLOCKED_OR_FAILED)

    with pytest.raises(ValueError):
        replace(canonical, execution_authorized=True)

    with pytest.raises(ValueError):
        replace(canonical, provider_mapping_authorized=True)
