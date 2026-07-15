# ruff: noqa: E501
from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from typing import cast

import pytest
from pytest import raises

from mayak.contracts.idempotency import IdempotencyFingerprint
from mayak.modules.notification_delivery import (
    NotificationBeaconLifecycleStatus,
    NotificationDeduplicationDecision,
    NotificationDeduplicationDecisionStatus,
    NotificationDeduplicationRecord,
    NotificationDeduplicationRecordState,
    NotificationDeduplicationRequest,
    NotificationDeduplicationStage,
    NotificationDeliveryPlanDecision,
    NotificationEligibilityDecision,
    NotificationEntitlementStatus,
    NotificationExternalProblemGateStatus,
    NotificationExternalRecoveryDecisionStatus,
    NotificationExternalRecoveryEffectClass,
    NotificationExternalRecoveryPolicyContext,
    NotificationExternalRecoveryPolicyDecision,
    NotificationOutboxCreationDecision,
    NotificationRecoveryGraceEvidence,
    NotificationSourceEvent,
    NotificationSourceFamily,
    NotificationSourceProducer,
    create_notification_outbox_item,
    evaluate_external_recovery_policy,
    evaluate_notification_deduplication,
    evaluate_notification_eligibility,
)
from tests.unit.test_notification_delivery_no_new_status_semantics import (
    ACCOUNT_ID,
    BEACON_ID,
    SCAN_RUN_ID,
    SOURCE_COMMIT_REFERENCE,
    SOURCE_EVENT_ID,
    SOURCE_FACT_ID,
    _eligibility_context,
    _max_evidence,
    _planned_delivery_plan_decision,
    _source_intake_decision,
    _telegram_evidence,
    _web_evidence,
)
from tests.unit.test_notification_delivery_no_new_status_semantics import (
    _source_event as _base_source_event,
)

EXTERNAL_PROBLEM_REFERENCE_ID = "external-problem-nd09-1"
MATERIAL_CHANGE_REFERENCE_ID = "material-change-nd09-1"
RECOVERY_OBLIGATION_REFERENCE_ID = "recovery-obligation-nd09-1"
NEW_LISTING_REFERENCES = ("listing-1", "listing-2")
ZERO_LISTING_REFERENCES: tuple[str, ...] = ()

_RECORD_REASON_BY_STATE = {
    NotificationDeduplicationRecordState.PENDING: "dedup-record-pending",
    NotificationDeduplicationRecordState.TERMINAL: "dedup-record-terminal",
    NotificationDeduplicationRecordState.AMBIGUOUS: "dedup-record-ambiguous",
}


def _source_event(
    *,
    family: NotificationSourceFamily,
    listing_count: int = 0,
    safe_listing_reference_ids: tuple[str, ...] = (),
    account_id: str = ACCOUNT_ID,
    beacon_id: str | None = BEACON_ID,
    source_fact_id: str = SOURCE_FACT_ID,
    source_event_id: str = SOURCE_EVENT_ID,
    scan_run_id: str | None = SCAN_RUN_ID,
    source_producer: NotificationSourceProducer = NotificationSourceProducer.SCAN_ORCHESTRATION,
    committed: bool = True,
    commit_reference: str | None = SOURCE_COMMIT_REFERENCE,
    source_identity_ambiguous: bool = False,
    contains_raw_provider_payload: bool = False,
) -> NotificationSourceEvent:
    return _base_source_event(
        family=family,
        account_id=account_id,
        beacon_id=beacon_id,
        source_fact_id=source_fact_id,
        source_event_id=source_event_id,
        scan_run_id=scan_run_id,
        source_producer=source_producer,
        listing_count=listing_count,
        safe_listing_reference_ids=safe_listing_reference_ids,
        committed=committed,
        commit_reference=commit_reference,
        source_identity_ambiguous=source_identity_ambiguous,
        contains_raw_provider_payload=contains_raw_provider_payload,
        service_access_gate_approved=False,
    )


def _recovery_grace_evidence(
    *,
    problem_began_while_access_active: bool,
    recovery_obligation_reference_id: str | None,
    recovery_result_already_consumed: bool,
    beacon_frozen_due_to_access_expiry: bool,
) -> NotificationRecoveryGraceEvidence:
    return NotificationRecoveryGraceEvidence(
        problem_began_while_access_active=problem_began_while_access_active,
        recovery_obligation_reference_id=recovery_obligation_reference_id,
        recovery_result_already_consumed=recovery_result_already_consumed,
        beacon_frozen_due_to_access_expiry=beacon_frozen_due_to_access_expiry,
        evidence_reference_ids=("recovery-grace-evidence-nd09-1",),
    )


def _eligibility_decision_for_source(
    *,
    family: NotificationSourceFamily,
    listing_count: int = 0,
    safe_listing_reference_ids: tuple[str, ...] = (),
    lifecycle_status: NotificationBeaconLifecycleStatus = NotificationBeaconLifecycleStatus.ACTIVE,
    entitlement_status: NotificationEntitlementStatus = NotificationEntitlementStatus.ALLOWED,
    telegram_enabled_by_user: bool = True,
    telegram_target_verified: bool = True,
    telegram_target_available: bool = True,
    max_enabled_by_user: bool = True,
    max_target_verified: bool = True,
    max_target_available: bool = True,
    recovery_grace_evidence: NotificationRecoveryGraceEvidence | None = None,
) -> NotificationEligibilityDecision:
    event = _source_event(
        family=family,
        listing_count=listing_count,
        safe_listing_reference_ids=safe_listing_reference_ids,
    )
    intake_decision = _source_intake_decision(event)
    context = _eligibility_context(
        account_id=ACCOUNT_ID,
        beacon_id=BEACON_ID,
        lifecycle_status=lifecycle_status,
        lifecycle_reference_id="beacon-lifecycle-nd09-1",
        entitlement_status=entitlement_status,
        entitlement_reference_id="entitlement-nd09-1",
        no_new_status_preference_enabled=False,
        no_new_status_frequency_minutes=None,
        telegram_enabled_by_user=telegram_enabled_by_user,
        telegram_target_reference_id="telegram-target-nd09-1",
        telegram_target_verified=telegram_target_verified,
        telegram_target_available=telegram_target_available,
        max_enabled_by_user=max_enabled_by_user,
        max_target_reference_id="max-target-nd09-1",
        max_target_verified=max_target_verified,
        max_target_available=max_target_available,
        channel_evidence=(
            _telegram_evidence(
                enabled_by_user=telegram_enabled_by_user,
                target_reference_id="telegram-target-nd09-1",
                target_verified=telegram_target_verified,
                target_available=telegram_target_available,
                evidence_reference_ids=("telegram-evidence-nd09-1",),
            ),
            _max_evidence(
                enabled_by_user=max_enabled_by_user,
                target_reference_id="max-target-nd09-1",
                target_verified=max_target_verified,
                target_available=max_target_available,
                evidence_reference_ids=("max-evidence-nd09-1",),
            ),
            _web_evidence(),
        ),
    )
    if recovery_grace_evidence is not None:
        context = replace(context, recovery_grace_evidence=recovery_grace_evidence)
    return evaluate_notification_eligibility(
        decision_id="eligibility-nd09-1",
        source_intake_decision=intake_decision,
        context=context,
        evidence_reference_ids=("eligibility-evidence-nd09-1",),
    )


def _policy_context(
    *,
    source_event: NotificationSourceEvent,
    problem_gate_status: NotificationExternalProblemGateStatus,
    external_problem_reference_id: str = EXTERNAL_PROBLEM_REFERENCE_ID,
    material_change_reference_id: str | None = None,
    recovery_obligation_reference_id: str | None = None,
    recovery_result_already_consumed: bool = False,
) -> NotificationExternalRecoveryPolicyContext:
    return NotificationExternalRecoveryPolicyContext(
        account_id=source_event.account_id,
        beacon_id=source_event.beacon_id or BEACON_ID,
        source_fact_reference_id=source_event.source_fact_id,
        external_problem_reference_id=external_problem_reference_id,
        material_change_reference_id=material_change_reference_id,
        problem_gate_status=problem_gate_status,
        recovery_obligation_reference_id=recovery_obligation_reference_id,
        recovery_result_already_consumed=recovery_result_already_consumed,
        evidence_reference_ids=("policy-context-evidence-nd09-1",),
    )


def _dedup_request(
    *,
    source_event: NotificationSourceEvent,
    semantic_effect_reference_id: str,
    proposed_result_reference_id: str,
    idempotency_mode: str = "match",
) -> NotificationDeduplicationRequest:
    if idempotency_mode == "match":
        idempotency_key = source_event.idempotency_key
        idempotency_fingerprint = source_event.idempotency_fingerprint
        idempotency_scope = source_event.idempotency_scope
    elif idempotency_mode == "missing":
        idempotency_key = None
        idempotency_fingerprint = None
        idempotency_scope = None
    elif idempotency_mode == "mismatch":
        idempotency_key = source_event.idempotency_key
        idempotency_fingerprint = IdempotencyFingerprint(
            value=f"{source_event.idempotency_fingerprint.value}-mismatch"
        )
        idempotency_scope = source_event.idempotency_scope
    else:
        raise ValueError("unsupported idempotency mode")

    return NotificationDeduplicationRequest(
        stage=NotificationDeduplicationStage.OUTBOX_CREATION,
        source_family=source_event.source_family,
        account_id=source_event.account_id,
        beacon_id=source_event.beacon_id,
        channel_class=None,
        semantic_effect_reference_id=semantic_effect_reference_id,
        idempotency_key=idempotency_key,
        idempotency_fingerprint=idempotency_fingerprint,
        idempotency_scope=idempotency_scope,
        proposed_record_state=NotificationDeduplicationRecordState.PENDING,
        proposed_result_reference_id=proposed_result_reference_id,
        correlation_id=source_event.correlation_id,
        causation_id=source_event.causation_id,
        evidence_reference_ids=("dedup-request-evidence-nd09-1",),
    )


def _dedup_decision(
    *,
    source_event: NotificationSourceEvent,
    semantic_effect_reference_id: str,
    proposed_result_reference_id: str,
    decision_id: str,
    record_id: str,
    existing_record_state: NotificationDeduplicationRecordState | None = None,
    idempotency_mode: str = "match",
    mismatch_kind: str = "fingerprint",
) -> NotificationDeduplicationDecision:
    request = _dedup_request(
        source_event=source_event,
        semantic_effect_reference_id=semantic_effect_reference_id,
        proposed_result_reference_id=proposed_result_reference_id,
        idempotency_mode=idempotency_mode,
    )
    existing_record = None
    if existing_record_state is not None:
        new_effect_decision = evaluate_notification_deduplication(
            decision_id=f"{decision_id}-base",
            record_id=record_id,
            request=request,
            existing_record=None,
            evidence_reference_ids=("dedup-base-evidence-nd09-1",),
        )
        existing_record = new_effect_decision.resulting_record
        assert isinstance(existing_record, NotificationDeduplicationRecord)
        existing_record = replace(
            existing_record,
            record_state=existing_record_state,
            reason_codes=(_RECORD_REASON_BY_STATE[existing_record_state],),
        )
        if idempotency_mode == "mismatch":
            if mismatch_kind == "semantic":
                existing_record = replace(
                    existing_record,
                    semantic_effect_reference_id=f"{semantic_effect_reference_id}-mismatch",
                )
            else:
                existing_record = replace(
                    existing_record,
                    idempotency_fingerprint=IdempotencyFingerprint(
                        value="dedup-fingerprint-mismatch"
                    ),
                )

    return evaluate_notification_deduplication(
        decision_id=decision_id,
        record_id=record_id,
        request=request,
        existing_record=existing_record,
        evidence_reference_ids=("dedup-evidence-nd09-1",),
    )


def _outbox_creation_decision(
    eligibility_decision: NotificationEligibilityDecision,
    *,
    decision_id: str = "outbox-nd09-1",
    outbox_item_id: str = "outbox-item-nd09-1",
    outbox_contract: str = "notification.delivery.external-recovery.v1",
    outbox_contract_version: str = "1.0",
) -> NotificationOutboxCreationDecision:
    source_event = eligibility_decision.source_intake_decision.source_event
    return create_notification_outbox_item(
        decision_id=decision_id,
        outbox_item_id=outbox_item_id,
        outbox_contract=outbox_contract,
        outbox_contract_version=outbox_contract_version,
        eligibility_decision=eligibility_decision,
        idempotency_key=source_event.idempotency_key,
        idempotency_fingerprint=source_event.idempotency_fingerprint,
        idempotency_scope=source_event.idempotency_scope,
        existing_outbox_item=None,
        evidence_reference_ids=("outbox-evidence-nd09-1",),
    )


def _policy_decision(
    *,
    eligibility_decision: NotificationEligibilityDecision,
    context: NotificationExternalRecoveryPolicyContext,
    deduplication_decision: NotificationDeduplicationDecision | None = None,
    delivery_plan_decision: NotificationDeliveryPlanDecision | None = None,
    decision_id: str = "policy-nd09-1",
    evidence_reference_ids: tuple[str, ...] = ("policy-evidence-nd09-1",),
) -> NotificationExternalRecoveryPolicyDecision:
    return evaluate_external_recovery_policy(
        decision_id=decision_id,
        eligibility_decision=eligibility_decision,
        deduplication_decision=deduplication_decision,
        delivery_plan_decision=delivery_plan_decision,
        context=context,
        evidence_reference_ids=evidence_reference_ids,
    )


def _push_path(
    *,
    family: NotificationSourceFamily,
    problem_gate_status: NotificationExternalProblemGateStatus,
    listing_count: int = 0,
    safe_listing_reference_ids: tuple[str, ...] = (),
    recovery_grace_evidence: NotificationRecoveryGraceEvidence | None = None,
    external_problem_reference_id: str = EXTERNAL_PROBLEM_REFERENCE_ID,
    material_change_reference_id: str | None = None,
) -> tuple[
    NotificationEligibilityDecision,
    NotificationExternalRecoveryPolicyContext,
    NotificationDeduplicationDecision,
    NotificationDeliveryPlanDecision,
]:
    eligibility_decision = _eligibility_decision_for_source(
        family=family,
        listing_count=listing_count,
        safe_listing_reference_ids=safe_listing_reference_ids,
        recovery_grace_evidence=recovery_grace_evidence,
    )
    source_event = eligibility_decision.source_intake_decision.source_event
    context = _policy_context(
        source_event=source_event,
        problem_gate_status=problem_gate_status,
        external_problem_reference_id=external_problem_reference_id,
        material_change_reference_id=material_change_reference_id,
        recovery_obligation_reference_id=RECOVERY_OBLIGATION_REFERENCE_ID
        if family is not NotificationSourceFamily.EXTERNAL_UNAVAILABLE_STATUS
        else None,
        recovery_result_already_consumed=False,
    )
    semantic_reference: str = external_problem_reference_id
    if problem_gate_status is NotificationExternalProblemGateStatus.MATERIAL_CHANGE:
        assert material_change_reference_id is not None
        semantic_reference = material_change_reference_id
    if family is not NotificationSourceFamily.EXTERNAL_UNAVAILABLE_STATUS:
        semantic_reference = RECOVERY_OBLIGATION_REFERENCE_ID
    dedup_decision = _dedup_decision(
        source_event=source_event,
        semantic_effect_reference_id=semantic_reference,
        proposed_result_reference_id="outbox-item-nd09-1",
        decision_id="dedup-nd09-1",
        record_id="dedup-record-nd09-1",
    )
    plan_decision = _planned_delivery_plan_decision(
        _outbox_creation_decision(
            eligibility_decision,
            outbox_item_id="outbox-item-nd09-1",
        ),
        decision_id="plan-nd09-1",
        delivery_plan_id="delivery-plan-nd09-1",
        evidence_reference_ids=("plan-evidence-nd09-1",),
    )
    return eligibility_decision, context, dedup_decision, plan_decision


def test_external_problem_began_push_eligible_and_preserves_channel_projection_and_evidence_order() -> (
    None
):
    eligibility_decision, context, dedup_decision, plan_decision = _push_path(
        family=NotificationSourceFamily.EXTERNAL_UNAVAILABLE_STATUS,
        problem_gate_status=NotificationExternalProblemGateStatus.PROBLEM_BEGAN,
    )
    eligibility_before = deepcopy(eligibility_decision)
    context_before = deepcopy(context)
    dedup_before = deepcopy(dedup_decision)
    plan_before = deepcopy(plan_decision)

    decision = _policy_decision(
        eligibility_decision=eligibility_decision,
        context=context,
        deduplication_decision=dedup_decision,
        delivery_plan_decision=plan_decision,
        decision_id="policy-external-began",
        evidence_reference_ids=(
            "eligibility-evidence-nd09-1",
            "dedup-evidence-nd09-1",
            "plan-evidence-nd09-1",
            "policy-extra-1",
        ),
    )

    assert decision.status is NotificationExternalRecoveryDecisionStatus.PUSH_WORK_ELIGIBLE
    assert (
        decision.effect_class
        is NotificationExternalRecoveryEffectClass.AVITO_UNAVAILABLE_CONTINUING_SCAN
    )
    assert decision.push_work_eligible is True
    assert decision.replayed is False
    assert decision.reconciliation_required is False
    assert decision.delivery_attempt_authorized is False
    assert decision.provider_mapping_authorized is False
    assert decision.deduplication_decision is dedup_decision
    assert decision.delivery_plan_decision is plan_decision
    assert decision.reason_codes == ("external-recovery-push-work-eligible",)
    assert decision.evidence_reference_ids == (
        "eligibility-evidence-nd09-1",
        "eligibility-context-evidence-1",
        "intake-evidence-1",
        "recovery-evidence-1",
        "telegram-evidence-nd09-1",
        "max-evidence-nd09-1",
        "web-evidence-1",
        "dedup-request-evidence-nd09-1",
        "dedup-evidence-nd09-1",
        "plan-evidence-nd09-1",
        "policy-context-evidence-nd09-1",
        "policy-extra-1",
    )
    assert eligibility_decision == eligibility_before
    assert context == context_before
    assert dedup_decision == dedup_before
    assert plan_decision == plan_before


@pytest.mark.parametrize(
    ("problem_gate_status", "external_problem_reference_id", "material_change_reference_id"),
    (
        (
            NotificationExternalProblemGateStatus.PROBLEM_BEGAN,
            EXTERNAL_PROBLEM_REFERENCE_ID,
            None,
        ),
        (
            NotificationExternalProblemGateStatus.MATERIAL_CHANGE,
            EXTERNAL_PROBLEM_REFERENCE_ID,
            MATERIAL_CHANGE_REFERENCE_ID,
        ),
    ),
)
def test_material_change_and_problem_began_allow_push_once_with_distinct_semantic_reference(
    problem_gate_status: NotificationExternalProblemGateStatus,
    external_problem_reference_id: str,
    material_change_reference_id: str | None,
) -> None:
    family = NotificationSourceFamily.EXTERNAL_UNAVAILABLE_STATUS
    eligibility_decision = _eligibility_decision_for_source(family=family)
    source_event = eligibility_decision.source_intake_decision.source_event
    context = _policy_context(
        source_event=source_event,
        problem_gate_status=problem_gate_status,
        external_problem_reference_id=external_problem_reference_id,
        material_change_reference_id=material_change_reference_id,
    )
    semantic_reference = (
        material_change_reference_id
        if material_change_reference_id is not None
        else external_problem_reference_id
    )
    dedup_decision = _dedup_decision(
        source_event=source_event,
        semantic_effect_reference_id=semantic_reference,
        proposed_result_reference_id="outbox-item-nd09-2",
        decision_id="dedup-nd09-2",
        record_id="dedup-record-nd09-2",
    )
    plan_decision = _planned_delivery_plan_decision(
        _outbox_creation_decision(
            eligibility_decision,
            outbox_item_id="outbox-item-nd09-2",
        ),
        decision_id="plan-nd09-2",
        delivery_plan_id="delivery-plan-nd09-2",
    )

    decision = _policy_decision(
        eligibility_decision=eligibility_decision,
        context=context,
        deduplication_decision=dedup_decision,
        delivery_plan_decision=plan_decision,
        decision_id="policy-material-change",
    )

    assert decision.status is NotificationExternalRecoveryDecisionStatus.PUSH_WORK_ELIGIBLE
    assert decision.deduplication_decision is not None
    assert (
        decision.deduplication_decision.request.semantic_effect_reference_id == semantic_reference
    )
    assert decision.delivery_plan_decision is not None
    assert decision.delivery_plan_decision.delivery_plan is not None
    assert decision.delivery_plan_decision.delivery_plan.outbox_item is not None
    assert (
        decision.delivery_plan_decision.delivery_plan.outbox_item.outbox_item_id
        == "outbox-item-nd09-2"
    )


@pytest.mark.parametrize(
    ("dedup_status", "expected_status"),
    (
        (
            NotificationDeduplicationDecisionStatus.REPLAY_TERMINAL,
            NotificationExternalRecoveryDecisionStatus.READ_MODEL_ONLY_REPLAY_TERMINAL,
        ),
        (
            NotificationDeduplicationDecisionStatus.REPLAY_PENDING,
            NotificationExternalRecoveryDecisionStatus.READ_MODEL_ONLY_REPLAY_PENDING,
        ),
        (
            NotificationDeduplicationDecisionStatus.RECONCILIATION_REQUIRED,
            NotificationExternalRecoveryDecisionStatus.RECONCILIATION_REQUIRED,
        ),
    ),
)
def test_same_problem_unchanged_allows_replay_or_reconciliation_but_rejects_new_effect(
    dedup_status: NotificationDeduplicationDecisionStatus,
    expected_status: NotificationExternalRecoveryDecisionStatus,
) -> None:
    eligibility_decision = _eligibility_decision_for_source(
        family=NotificationSourceFamily.EXTERNAL_UNAVAILABLE_STATUS
    )
    source_event = eligibility_decision.source_intake_decision.source_event
    context = _policy_context(
        source_event=source_event,
        problem_gate_status=NotificationExternalProblemGateStatus.SAME_PROBLEM_UNCHANGED,
    )
    if dedup_status is NotificationDeduplicationDecisionStatus.RECONCILIATION_REQUIRED:
        dedup_decision = _dedup_decision(
            source_event=source_event,
            semantic_effect_reference_id=EXTERNAL_PROBLEM_REFERENCE_ID,
            proposed_result_reference_id="outbox-item-nd09-3",
            decision_id="dedup-nd09-3",
            record_id="dedup-record-nd09-3",
            existing_record_state=NotificationDeduplicationRecordState.AMBIGUOUS,
        )
    elif dedup_status is NotificationDeduplicationDecisionStatus.REPLAY_TERMINAL:
        dedup_decision = _dedup_decision(
            source_event=source_event,
            semantic_effect_reference_id=EXTERNAL_PROBLEM_REFERENCE_ID,
            proposed_result_reference_id="outbox-item-nd09-3",
            decision_id="dedup-nd09-3",
            record_id="dedup-record-nd09-3",
            existing_record_state=NotificationDeduplicationRecordState.TERMINAL,
        )
    else:
        dedup_decision = _dedup_decision(
            source_event=source_event,
            semantic_effect_reference_id=EXTERNAL_PROBLEM_REFERENCE_ID,
            proposed_result_reference_id="outbox-item-nd09-3",
            decision_id="dedup-nd09-3",
            record_id="dedup-record-nd09-3",
            existing_record_state=NotificationDeduplicationRecordState.PENDING,
        )

    decision = _policy_decision(
        eligibility_decision=eligibility_decision,
        context=context,
        deduplication_decision=dedup_decision,
        decision_id="policy-same-problem",
    )

    assert decision.status is expected_status
    if dedup_status is NotificationDeduplicationDecisionStatus.RECONCILIATION_REQUIRED:
        assert (
            decision.effect_class
            is NotificationExternalRecoveryEffectClass.RECOVERY_BLOCKED_OR_AMBIGUOUS
        )
    else:
        assert (
            decision.effect_class
            is NotificationExternalRecoveryEffectClass.AVITO_UNAVAILABLE_CONTINUING_SCAN
        )
    assert decision.push_work_eligible is False
    assert decision.delivery_plan_decision is None
    if dedup_status is NotificationDeduplicationDecisionStatus.RECONCILIATION_REQUIRED:
        assert decision.replayed is True
        assert decision.reconciliation_required is True
    else:
        assert decision.replayed is True
        assert decision.reconciliation_required is False
        assert decision.status is expected_status

    with raises(ValueError):
        _policy_decision(
            eligibility_decision=eligibility_decision,
            context=context,
            deduplication_decision=_dedup_decision(
                source_event=source_event,
                semantic_effect_reference_id=EXTERNAL_PROBLEM_REFERENCE_ID,
                proposed_result_reference_id="outbox-item-nd09-3-new",
                decision_id="dedup-nd09-3-new",
                record_id="dedup-record-nd09-3-new",
            ),
            decision_id="policy-same-problem-new",
        )


def test_external_ambiguous_gate_blocks_without_downstream_work() -> None:
    eligibility_decision = _eligibility_decision_for_source(
        family=NotificationSourceFamily.EXTERNAL_UNAVAILABLE_STATUS
    )
    context = _policy_context(
        source_event=eligibility_decision.source_intake_decision.source_event,
        problem_gate_status=NotificationExternalProblemGateStatus.AMBIGUOUS,
    )

    decision = _policy_decision(
        eligibility_decision=eligibility_decision,
        context=context,
        decision_id="policy-ambiguous",
    )

    assert (
        decision.status is NotificationExternalRecoveryDecisionStatus.BLOCKED_PROBLEM_GATE_AMBIGUOUS
    )
    assert (
        decision.effect_class
        is NotificationExternalRecoveryEffectClass.RECOVERY_BLOCKED_OR_AMBIGUOUS
    )
    assert decision.deduplication_decision is None
    assert decision.delivery_plan_decision is None
    assert decision.push_work_eligible is False
    assert decision.replayed is False


@pytest.mark.parametrize(
    ("listing_count", "safe_listing_reference_ids", "expected_effect_class"),
    (
        (
            2,
            NEW_LISTING_REFERENCES,
            NotificationExternalRecoveryEffectClass.RECOVERY_RESULT_WITH_NEW_LISTINGS,
        ),
        (
            0,
            ZERO_LISTING_REFERENCES,
            NotificationExternalRecoveryEffectClass.RECOVERY_RESULT_NO_NEW_LISTINGS,
        ),
    ),
)
def test_recovery_result_listing_references_are_preserved_without_truncation(
    listing_count: int,
    safe_listing_reference_ids: tuple[str, ...],
    expected_effect_class: NotificationExternalRecoveryEffectClass,
) -> None:
    recovery_grace_evidence = _recovery_grace_evidence(
        problem_began_while_access_active=True,
        recovery_obligation_reference_id=RECOVERY_OBLIGATION_REFERENCE_ID,
        recovery_result_already_consumed=False,
        beacon_frozen_due_to_access_expiry=True,
    )
    eligibility_decision = _eligibility_decision_for_source(
        family=NotificationSourceFamily.RECOVERY_SCAN_COMPLETED,
        listing_count=listing_count,
        safe_listing_reference_ids=safe_listing_reference_ids,
        lifecycle_status=NotificationBeaconLifecycleStatus.FROZEN,
        entitlement_status=NotificationEntitlementStatus.EXPIRED,
        recovery_grace_evidence=recovery_grace_evidence,
    )
    source_event = eligibility_decision.source_intake_decision.source_event
    context = _policy_context(
        source_event=source_event,
        problem_gate_status=NotificationExternalProblemGateStatus.NOT_APPLICABLE,
        recovery_obligation_reference_id=RECOVERY_OBLIGATION_REFERENCE_ID,
        recovery_result_already_consumed=False,
    )
    dedup_decision = _dedup_decision(
        source_event=source_event,
        semantic_effect_reference_id=RECOVERY_OBLIGATION_REFERENCE_ID,
        proposed_result_reference_id="outbox-item-nd09-4",
        decision_id="dedup-nd09-4",
        record_id="dedup-record-nd09-4",
    )
    plan_decision = _planned_delivery_plan_decision(
        _outbox_creation_decision(
            eligibility_decision,
            outbox_item_id="outbox-item-nd09-4",
        ),
        decision_id="plan-nd09-4",
        delivery_plan_id="delivery-plan-nd09-4",
    )

    decision = _policy_decision(
        eligibility_decision=eligibility_decision,
        context=context,
        deduplication_decision=dedup_decision,
        delivery_plan_decision=plan_decision,
        decision_id="policy-recovery-result",
    )

    assert decision.status is NotificationExternalRecoveryDecisionStatus.PUSH_WORK_ELIGIBLE
    assert decision.effect_class is expected_effect_class
    assert decision.deduplication_decision is not None
    assert decision.delivery_plan_decision is not None
    assert decision.delivery_plan_decision.delivery_plan is not None
    assert decision.delivery_plan_decision.delivery_plan.outbox_item is not None
    assert decision.delivery_plan_decision.delivery_plan.outbox_item.listing_count == listing_count
    assert (
        decision.delivery_plan_decision.delivery_plan.outbox_item.safe_listing_reference_ids
        == safe_listing_reference_ids
    )
    assert (
        decision.delivery_plan_decision.delivery_plan.outbox_item.safe_listing_reference_ids
        == safe_listing_reference_ids
    )


def test_lost_anchors_recovery_is_state_restored_not_confirmed_new() -> None:
    eligibility_decision = _eligibility_decision_for_source(
        family=NotificationSourceFamily.LOST_ANCHORS_RECOVERED,
        listing_count=2,
        safe_listing_reference_ids=NEW_LISTING_REFERENCES,
    )
    source_event = eligibility_decision.source_intake_decision.source_event
    context = _policy_context(
        source_event=source_event,
        problem_gate_status=NotificationExternalProblemGateStatus.NOT_APPLICABLE,
        recovery_obligation_reference_id=RECOVERY_OBLIGATION_REFERENCE_ID,
        recovery_result_already_consumed=False,
    )
    dedup_decision = _dedup_decision(
        source_event=source_event,
        semantic_effect_reference_id=RECOVERY_OBLIGATION_REFERENCE_ID,
        proposed_result_reference_id="outbox-item-nd09-5",
        decision_id="dedup-nd09-5",
        record_id="dedup-record-nd09-5",
    )
    plan_decision = _planned_delivery_plan_decision(
        _outbox_creation_decision(
            eligibility_decision,
            outbox_item_id="outbox-item-nd09-5",
        ),
        decision_id="plan-nd09-5",
        delivery_plan_id="delivery-plan-nd09-5",
    )

    decision = _policy_decision(
        eligibility_decision=eligibility_decision,
        context=context,
        deduplication_decision=dedup_decision,
        delivery_plan_decision=plan_decision,
        decision_id="policy-lost-anchors",
    )

    assert decision.status is NotificationExternalRecoveryDecisionStatus.PUSH_WORK_ELIGIBLE
    assert (
        decision.effect_class
        is NotificationExternalRecoveryEffectClass.RECOVERY_RESULT_LOST_ANCHORS_RESTORED
    )
    assert (
        decision.effect_class
        is not NotificationExternalRecoveryEffectClass.RECOVERY_RESULT_WITH_NEW_LISTINGS
    )


def test_recovery_grace_and_consumed_recovery_follow_grace_evidence() -> None:
    grace_evidence = _recovery_grace_evidence(
        problem_began_while_access_active=True,
        recovery_obligation_reference_id=RECOVERY_OBLIGATION_REFERENCE_ID,
        recovery_result_already_consumed=False,
        beacon_frozen_due_to_access_expiry=True,
    )
    eligibility_decision = _eligibility_decision_for_source(
        family=NotificationSourceFamily.RECOVERY_SCAN_COMPLETED,
        listing_count=1,
        safe_listing_reference_ids=NEW_LISTING_REFERENCES[:1],
        lifecycle_status=NotificationBeaconLifecycleStatus.FROZEN,
        entitlement_status=NotificationEntitlementStatus.EXPIRED,
        recovery_grace_evidence=grace_evidence,
    )
    source_event = eligibility_decision.source_intake_decision.source_event
    context = _policy_context(
        source_event=source_event,
        problem_gate_status=NotificationExternalProblemGateStatus.NOT_APPLICABLE,
        recovery_obligation_reference_id=RECOVERY_OBLIGATION_REFERENCE_ID,
        recovery_result_already_consumed=False,
    )
    dedup_decision = _dedup_decision(
        source_event=source_event,
        semantic_effect_reference_id=RECOVERY_OBLIGATION_REFERENCE_ID,
        proposed_result_reference_id="outbox-item-nd09-6",
        decision_id="dedup-nd09-6",
        record_id="dedup-record-nd09-6",
    )
    plan_decision = _planned_delivery_plan_decision(
        _outbox_creation_decision(
            eligibility_decision,
            outbox_item_id="outbox-item-nd09-6",
        ),
        decision_id="plan-nd09-6",
        delivery_plan_id="delivery-plan-nd09-6",
    )

    decision = _policy_decision(
        eligibility_decision=eligibility_decision,
        context=context,
        deduplication_decision=dedup_decision,
        delivery_plan_decision=plan_decision,
        decision_id="policy-recovery-grace",
    )

    assert decision.status is NotificationExternalRecoveryDecisionStatus.PUSH_WORK_ELIGIBLE
    assert decision.recovery_grace_applied is True
    assert (
        decision.effect_class
        is NotificationExternalRecoveryEffectClass.RECOVERY_RESULT_WITH_NEW_LISTINGS
    )
    assert decision.delivery_attempt_authorized is False
    assert decision.provider_mapping_authorized is False

    consumed_grace_evidence = _recovery_grace_evidence(
        problem_began_while_access_active=False,
        recovery_obligation_reference_id=RECOVERY_OBLIGATION_REFERENCE_ID,
        recovery_result_already_consumed=True,
        beacon_frozen_due_to_access_expiry=False,
    )
    consumed_eligibility = _eligibility_decision_for_source(
        family=NotificationSourceFamily.RECOVERY_SCAN_COMPLETED,
        listing_count=1,
        safe_listing_reference_ids=NEW_LISTING_REFERENCES[:1],
        recovery_grace_evidence=consumed_grace_evidence,
    )
    consumed_source_event = consumed_eligibility.source_intake_decision.source_event
    consumed_context = _policy_context(
        source_event=consumed_source_event,
        problem_gate_status=NotificationExternalProblemGateStatus.NOT_APPLICABLE,
        recovery_obligation_reference_id=RECOVERY_OBLIGATION_REFERENCE_ID,
        recovery_result_already_consumed=True,
    )
    consumed_existing = _dedup_decision(
        source_event=consumed_source_event,
        semantic_effect_reference_id=RECOVERY_OBLIGATION_REFERENCE_ID,
        proposed_result_reference_id="outbox-item-nd09-7",
        decision_id="dedup-nd09-7-base",
        record_id="dedup-record-nd09-7",
        existing_record_state=NotificationDeduplicationRecordState.TERMINAL,
    )
    consumed_terminal = _policy_decision(
        eligibility_decision=consumed_eligibility,
        context=consumed_context,
        deduplication_decision=consumed_existing,
        decision_id="policy-consumed-replay-terminal",
    )
    assert (
        consumed_terminal.status
        is NotificationExternalRecoveryDecisionStatus.READ_MODEL_ONLY_REPLAY_TERMINAL
    )
    assert consumed_terminal.push_work_eligible is False

    consumed_new_effect = _dedup_decision(
        source_event=consumed_source_event,
        semantic_effect_reference_id=RECOVERY_OBLIGATION_REFERENCE_ID,
        proposed_result_reference_id="outbox-item-nd09-8",
        decision_id="dedup-nd09-8",
        record_id="dedup-record-nd09-8",
    )
    consumed_blocked = _policy_decision(
        eligibility_decision=consumed_eligibility,
        context=consumed_context,
        deduplication_decision=consumed_new_effect,
        decision_id="policy-consumed-new-effect",
    )
    assert (
        consumed_blocked.status
        is NotificationExternalRecoveryDecisionStatus.BLOCKED_RECOVERY_ALREADY_CONSUMED
    )
    assert consumed_blocked.delivery_plan_decision is None
    assert consumed_blocked.push_work_eligible is False


def test_no_eligible_push_channel_is_read_model_only() -> None:
    eligibility_decision = _eligibility_decision_for_source(
        family=NotificationSourceFamily.EXTERNAL_UNAVAILABLE_STATUS,
        telegram_enabled_by_user=False,
        telegram_target_verified=False,
        telegram_target_available=False,
        max_enabled_by_user=False,
        max_target_verified=False,
        max_target_available=False,
    )
    context = _policy_context(
        source_event=eligibility_decision.source_intake_decision.source_event,
        problem_gate_status=NotificationExternalProblemGateStatus.PROBLEM_BEGAN,
    )

    decision = _policy_decision(
        eligibility_decision=eligibility_decision,
        context=context,
        decision_id="policy-no-channel",
    )

    assert (
        decision.status
        is NotificationExternalRecoveryDecisionStatus.READ_MODEL_ONLY_NO_ELIGIBLE_PUSH_CHANNEL
    )
    assert decision.deduplication_decision is None
    assert decision.delivery_plan_decision is None
    assert decision.push_work_eligible is False


def test_blocked_eligibility_short_circuits_without_work() -> None:
    eligibility_decision = _eligibility_decision_for_source(
        family=NotificationSourceFamily.EXTERNAL_UNAVAILABLE_STATUS,
        entitlement_status=NotificationEntitlementStatus.DENIED,
    )
    context = _policy_context(
        source_event=eligibility_decision.source_intake_decision.source_event,
        problem_gate_status=NotificationExternalProblemGateStatus.PROBLEM_BEGAN,
    )

    decision = _policy_decision(
        eligibility_decision=eligibility_decision,
        context=context,
        decision_id="policy-blocked-entitlement",
    )

    assert decision.status is NotificationExternalRecoveryDecisionStatus.BLOCKED_ELIGIBILITY
    assert (
        decision.effect_class
        is NotificationExternalRecoveryEffectClass.RECOVERY_BLOCKED_OR_AMBIGUOUS
    )
    assert decision.deduplication_decision is None
    assert decision.delivery_plan_decision is None
    assert decision.push_work_eligible is False


@pytest.mark.parametrize(
    ("dedup_mode", "expected_status"),
    (
        ("missing", NotificationExternalRecoveryDecisionStatus.BLOCKED_IDEMPOTENCY),
        ("mismatch", NotificationExternalRecoveryDecisionStatus.BLOCKED_IDEMPOTENCY),
    ),
)
def test_dedup_replay_mismatch_and_missing_cases_are_blocked_or_replayed(
    dedup_mode: str,
    expected_status: NotificationExternalRecoveryDecisionStatus,
) -> None:
    eligibility_decision = _eligibility_decision_for_source(
        family=NotificationSourceFamily.EXTERNAL_UNAVAILABLE_STATUS,
    )
    source_event = eligibility_decision.source_intake_decision.source_event
    context = _policy_context(
        source_event=source_event,
        problem_gate_status=NotificationExternalProblemGateStatus.PROBLEM_BEGAN,
    )
    if dedup_mode == "missing":
        dedup_decision = _dedup_decision(
            source_event=source_event,
            semantic_effect_reference_id=EXTERNAL_PROBLEM_REFERENCE_ID,
            proposed_result_reference_id="outbox-item-nd09-9",
            decision_id="dedup-nd09-9-missing",
            record_id="dedup-record-nd09-9-missing",
            idempotency_mode="missing",
        )
    else:
        dedup_decision = _dedup_decision(
            source_event=source_event,
            semantic_effect_reference_id=EXTERNAL_PROBLEM_REFERENCE_ID,
            proposed_result_reference_id="outbox-item-nd09-9",
            decision_id="dedup-nd09-9-mismatch",
            record_id="dedup-record-nd09-9-mismatch",
            existing_record_state=NotificationDeduplicationRecordState.TERMINAL,
            idempotency_mode="mismatch",
        )

    decision = _policy_decision(
        eligibility_decision=eligibility_decision,
        context=context,
        deduplication_decision=dedup_decision,
        decision_id=f"policy-{dedup_mode}",
    )

    assert decision.status is expected_status
    assert (
        decision.effect_class
        is NotificationExternalRecoveryEffectClass.RECOVERY_BLOCKED_OR_AMBIGUOUS
    )
    assert decision.push_work_eligible is False
    assert decision.delivery_plan_decision is None


def test_plan_validation_rejects_wrong_source_and_truncated_references() -> None:
    eligibility_decision = _eligibility_decision_for_source(
        family=NotificationSourceFamily.RECOVERY_SCAN_COMPLETED,
        listing_count=2,
        safe_listing_reference_ids=NEW_LISTING_REFERENCES,
        lifecycle_status=NotificationBeaconLifecycleStatus.FROZEN,
        entitlement_status=NotificationEntitlementStatus.EXPIRED,
        recovery_grace_evidence=_recovery_grace_evidence(
            problem_began_while_access_active=True,
            recovery_obligation_reference_id=RECOVERY_OBLIGATION_REFERENCE_ID,
            recovery_result_already_consumed=False,
            beacon_frozen_due_to_access_expiry=True,
        ),
    )
    source_event = eligibility_decision.source_intake_decision.source_event
    context = _policy_context(
        source_event=source_event,
        problem_gate_status=NotificationExternalProblemGateStatus.NOT_APPLICABLE,
        recovery_obligation_reference_id=RECOVERY_OBLIGATION_REFERENCE_ID,
    )
    dedup_decision = _dedup_decision(
        source_event=source_event,
        semantic_effect_reference_id=RECOVERY_OBLIGATION_REFERENCE_ID,
        proposed_result_reference_id="outbox-item-nd09-10",
        decision_id="dedup-nd09-10",
        record_id="dedup-record-nd09-10",
    )
    plan_decision = _planned_delivery_plan_decision(
        _outbox_creation_decision(
            eligibility_decision,
            outbox_item_id="outbox-item-nd09-10",
        ),
        decision_id="plan-nd09-10",
        delivery_plan_id="delivery-plan-nd09-10",
    )
    outbox_creation_outbox_item = plan_decision.outbox_creation_decision.outbox_item
    assert outbox_creation_outbox_item is not None
    delivery_plan = plan_decision.delivery_plan
    assert delivery_plan is not None
    assert delivery_plan.outbox_item is not None

    forged_plan = replace(
        plan_decision,
        outbox_creation_decision=replace(
            plan_decision.outbox_creation_decision,
            outbox_item=replace(
                outbox_creation_outbox_item,
                listing_count=1,
                safe_listing_reference_ids=("listing-1",),
            ),
        ),
        delivery_plan=replace(
            delivery_plan,
            outbox_item=replace(
                delivery_plan.outbox_item,
                listing_count=1,
                safe_listing_reference_ids=("listing-1",),
            ),
        ),
    )

    with raises(ValueError):
        _policy_decision(
            eligibility_decision=eligibility_decision,
            context=context,
            deduplication_decision=dedup_decision,
            delivery_plan_decision=forged_plan,
            decision_id="policy-forged-plan-truncation",
    )

    forged_plan_delivery = plan_decision.delivery_plan
    assert forged_plan_delivery is not None
    assert forged_plan_delivery.outbox_item is not None
    forged_outbox = replace(
        forged_plan_delivery.outbox_item,
        account_id="wrong-account",
    )
    forged_plan_identity = replace(
        plan_decision,
        outbox_creation_decision=replace(
            plan_decision.outbox_creation_decision,
            outbox_item=forged_outbox,
        ),
        delivery_plan=replace(
            forged_plan_delivery,
            account_id="wrong-account",
            outbox_item=forged_outbox,
        ),
    )
    with raises(ValueError):
        _policy_decision(
            eligibility_decision=eligibility_decision,
            context=context,
            deduplication_decision=dedup_decision,
            delivery_plan_decision=forged_plan_identity,
            decision_id="policy-forged-plan-identity",
        )


@pytest.mark.parametrize(
    ("field_name", "mutated_value"),
    (
        ("source_producer", NotificationSourceProducer.EGRESS_ROUTING),
        ("source_identity_ambiguous", True),
        ("contains_raw_provider_payload", True),
    ),
)
def test_provenance_gates_reject_uncommitted_wrong_producer_ambiguous_identity_and_payload_like_source(
    field_name: str,
    mutated_value: object,
) -> None:
    eligibility_decision = _eligibility_decision_for_source(
        family=NotificationSourceFamily.EXTERNAL_UNAVAILABLE_STATUS,
    )
    source_intake_decision = eligibility_decision.source_intake_decision
    source_event = source_intake_decision.source_event
    if field_name == "source_producer":
        forged_event = replace(
            source_event,
            source_producer=cast(NotificationSourceProducer, mutated_value),
        )
    elif field_name == "source_identity_ambiguous":
        forged_event = replace(
            source_event,
            source_identity_ambiguous=cast(bool, mutated_value),
        )
    else:
        forged_event = replace(
            source_event,
            contains_raw_provider_payload=cast(bool, mutated_value),
        )
    forged_intake = replace(source_intake_decision, source_event=forged_event)
    forged_eligibility = replace(eligibility_decision, source_intake_decision=forged_intake)
    context = _policy_context(
        source_event=forged_event,
        problem_gate_status=NotificationExternalProblemGateStatus.PROBLEM_BEGAN,
    )

    with raises(ValueError):
        _policy_decision(
            eligibility_decision=forged_eligibility,
            context=context,
            decision_id="policy-forged-provenance",
        )


def test_exact_type_gates_reject_raw_strings_and_lookalikes() -> None:
    with raises(ValueError):
        NotificationExternalRecoveryPolicyContext(
            account_id=ACCOUNT_ID,
            beacon_id=BEACON_ID,
            source_fact_reference_id=SOURCE_FACT_ID,
            external_problem_reference_id=EXTERNAL_PROBLEM_REFERENCE_ID,
            material_change_reference_id=None,
            problem_gate_status=cast(
                NotificationExternalProblemGateStatus,
                "PROBLEM_BEGAN",
            ),
            recovery_obligation_reference_id=None,
            recovery_result_already_consumed=False,
            evidence_reference_ids=("context-evidence-nd09-1",),
        )


def test_no_input_mutation_and_evidence_union_is_deterministic() -> None:
    eligibility_decision = _eligibility_decision_for_source(
        family=NotificationSourceFamily.EXTERNAL_UNAVAILABLE_STATUS,
    )
    source_event = eligibility_decision.source_intake_decision.source_event
    context = _policy_context(
        source_event=source_event,
        problem_gate_status=NotificationExternalProblemGateStatus.PROBLEM_BEGAN,
    )
    dedup_decision = _dedup_decision(
        source_event=source_event,
        semantic_effect_reference_id=EXTERNAL_PROBLEM_REFERENCE_ID,
        proposed_result_reference_id="outbox-item-nd09-11",
        decision_id="dedup-nd09-11",
        record_id="dedup-record-nd09-11",
    )
    plan_decision = _planned_delivery_plan_decision(
        _outbox_creation_decision(
            eligibility_decision,
            outbox_item_id="outbox-item-nd09-11",
        ),
        decision_id="plan-nd09-11",
        delivery_plan_id="delivery-plan-nd09-11",
        evidence_reference_ids=("plan-evidence-nd09-11", "shared-evidence"),
    )
    eligibility_decision = replace(
        eligibility_decision,
        evidence_reference_ids=("eligibility-evidence-nd09-11", "shared-evidence"),
    )
    context = replace(
        context,
        evidence_reference_ids=("context-evidence-nd09-11", "shared-evidence"),
    )
    dedup_decision = replace(
        dedup_decision,
        evidence_reference_ids=("dedup-evidence-nd09-11", "shared-evidence"),
    )
    plan_decision = _planned_delivery_plan_decision(
        _outbox_creation_decision(
            eligibility_decision,
            outbox_item_id="outbox-item-nd09-11",
        ),
        decision_id="plan-nd09-11",
        delivery_plan_id="delivery-plan-nd09-11",
        evidence_reference_ids=("plan-evidence-nd09-11", "shared-evidence"),
    )

    eligibility_before = deepcopy(eligibility_decision)
    context_before = deepcopy(context)
    dedup_before = deepcopy(dedup_decision)
    plan_before = deepcopy(plan_decision)

    decision = _policy_decision(
        eligibility_decision=eligibility_decision,
        context=context,
        deduplication_decision=dedup_decision,
        delivery_plan_decision=plan_decision,
        decision_id="policy-evidence-union",
        evidence_reference_ids=("function-evidence-nd09-11", "shared-evidence"),
    )

    assert decision.status is NotificationExternalRecoveryDecisionStatus.PUSH_WORK_ELIGIBLE
    assert decision.evidence_reference_ids == (
        "eligibility-evidence-nd09-11",
        "shared-evidence",
        "dedup-evidence-nd09-11",
        "plan-evidence-nd09-11",
        "context-evidence-nd09-11",
        "function-evidence-nd09-11",
    )
    assert eligibility_decision == eligibility_before
    assert context == context_before
    assert dedup_decision == dedup_before
    assert plan_decision == plan_before
