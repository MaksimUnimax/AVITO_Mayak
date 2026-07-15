from __future__ import annotations

from collections.abc import Callable

import pytest

from mayak.contracts.idempotency import IdempotencyDecision
from mayak.modules.notification_delivery import (
    NO_NEW_MINIMUM_FREQUENCY_MINUTES,
    NotificationBeaconLifecycleStatus,
    NotificationChannelClass,
    NotificationChannelEligibilityEvidence,
    NotificationEligibilityContext,
    NotificationEligibilityDecision,
    NotificationEligibilityStatus,
    NotificationEntitlementStatus,
    NotificationOutboxAuthority,
    NotificationOutboxCreationStatus,
    NotificationOutboxItem,
    NotificationOutboxLifecycleStatus,
    NotificationRecoveryGraceEvidence,
    NotificationSourceEvent,
    NotificationSourceFamily,
    NotificationSourceIntakeDecision,
    NotificationSourceIntakeStatus,
    NotificationSourceProducer,
    evaluate_notification_eligibility,
    evaluate_notification_source_intake,
)
from mayak.modules.notification_delivery.outbox import create_notification_outbox_item
from mayak.platform.idempotency import IdempotencyFingerprint, IdempotencyKey, IdempotencyScope


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
        source_identity_ambiguous=False,
        contains_raw_provider_payload=False,
        service_access_gate_approved=service_access_gate_approved,
        evidence_reference_ids=("source-evidence-1",),
    )


def _source_intake_decision(
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
    service_access_gate_approved: bool = False,
    decision_id: str = "intake-decision-1",
) -> NotificationSourceIntakeDecision:
    event = _source_event(
        family=family,
        producer=producer,
        account_id=account_id,
        beacon_id=beacon_id,
        scan_run_id=scan_run_id,
        listing_count=listing_count,
        safe_listing_reference_ids=safe_listing_reference_ids,
        committed=committed,
        commit_reference=commit_reference,
        service_access_gate_approved=service_access_gate_approved,
    )
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
    family: NotificationSourceFamily = NotificationSourceFamily.NEW_LISTINGS_FOUND,
    producer: NotificationSourceProducer = NotificationSourceProducer.SCAN_ORCHESTRATION,
    listing_count: int = 1,
    safe_listing_reference_ids: tuple[str, ...] = ("listing-1",),
    committed: bool = True,
    commit_reference: str | None = "commit-1",
    service_access_gate_approved: bool = False,
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
    _ = family
    _ = producer
    _ = listing_count
    _ = safe_listing_reference_ids
    _ = committed
    _ = commit_reference
    _ = service_access_gate_approved
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


def _eligibility_decision(
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
    service_access_gate_approved: bool = False,
    context: NotificationEligibilityContext | None = None,
    decision_id: str = "eligibility-decision-1",
) -> NotificationEligibilityDecision:
    intake_decision = _source_intake_decision(
        family=family,
        producer=producer,
        account_id=account_id,
        beacon_id=beacon_id,
        scan_run_id=scan_run_id,
        listing_count=listing_count,
        safe_listing_reference_ids=safe_listing_reference_ids,
        committed=committed,
        commit_reference=commit_reference,
        service_access_gate_approved=service_access_gate_approved,
    )
    if context is None:
        context = _context(account_id=account_id, beacon_id=beacon_id)
    return evaluate_notification_eligibility(
        decision_id=decision_id,
        source_intake_decision=intake_decision,
        context=context,
        evidence_reference_ids=("eligibility-evidence-1",),
    )


def _outbox_decision(
    *,
    eligibility_decision: NotificationEligibilityDecision,
    decision_id: str = "outbox-decision-1",
    outbox_item_id: str = "outbox-item-1",
    outbox_contract: str = "notification.outbox.v1",
    outbox_contract_version: str = "1.0",
    idempotency_key: IdempotencyKey | None = None,
    idempotency_fingerprint: IdempotencyFingerprint | None = None,
    idempotency_scope: IdempotencyScope | None = None,
    existing_outbox_item: NotificationOutboxItem | None = None,
    evidence_reference_ids: tuple[str, ...] = ("outbox-evidence-1",),
) -> NotificationOutboxItem | None:
    source_event = eligibility_decision.source_intake_decision.source_event
    if idempotency_key is None:
        idempotency_key = source_event.idempotency_key
    if idempotency_fingerprint is None:
        idempotency_fingerprint = source_event.idempotency_fingerprint
    if idempotency_scope is None:
        idempotency_scope = source_event.idempotency_scope

    decision = create_notification_outbox_item(
        decision_id=decision_id,
        outbox_item_id=outbox_item_id,
        outbox_contract=outbox_contract,
        outbox_contract_version=outbox_contract_version,
        eligibility_decision=eligibility_decision,
        idempotency_key=idempotency_key,
        idempotency_fingerprint=idempotency_fingerprint,
        idempotency_scope=idempotency_scope,
        existing_outbox_item=existing_outbox_item,
        evidence_reference_ids=evidence_reference_ids,
    )
    return decision.outbox_item


def _eligible_new_listing_outbox_decision(
    *,
    outbox_item_id: str = "outbox-item-1",
    existing_outbox_item: NotificationOutboxItem | None = None,
    idempotency_fingerprint: IdempotencyFingerprint | None = None,
    eligibility_decision: NotificationEligibilityDecision | None = None,
    decision_id: str = "outbox-decision-1",
) -> tuple[NotificationEligibilityDecision, NotificationOutboxItem | None]:
    if eligibility_decision is None:
        eligibility_decision = _eligibility_decision()
    return (
        eligibility_decision,
        _outbox_decision(
            eligibility_decision=eligibility_decision,
            decision_id=decision_id,
            outbox_item_id=outbox_item_id,
            existing_outbox_item=existing_outbox_item,
            idempotency_fingerprint=idempotency_fingerprint,
        ),
    )


def test_eligible_new_listing_creates_one_planned_item() -> None:
    eligibility_decision = _eligibility_decision()
    outbox_item = create_notification_outbox_item(
        decision_id="outbox-decision-1",
        outbox_item_id="outbox-item-1",
        outbox_contract="notification.outbox.v1",
        outbox_contract_version="1.0",
        eligibility_decision=eligibility_decision,
        idempotency_key=eligibility_decision.source_intake_decision.source_event.idempotency_key,
        idempotency_fingerprint=eligibility_decision.source_intake_decision.source_event.idempotency_fingerprint,
        idempotency_scope=eligibility_decision.source_intake_decision.source_event.idempotency_scope,
        existing_outbox_item=None,
        evidence_reference_ids=("outbox-evidence-1",),
    ).outbox_item

    assert outbox_item is not None
    assert outbox_item.authority is NotificationOutboxAuthority.NOTIFICATION_DELIVERY_SERVER
    assert outbox_item.lifecycle_status is NotificationOutboxLifecycleStatus.PLANNED
    assert outbox_item.outbox_item_id == "outbox-item-1"
    assert outbox_item.outbox_contract == "notification.outbox.v1"
    assert outbox_item.outbox_contract_version == "1.0"
    assert outbox_item.eligibility_decision_id == eligibility_decision.decision_id
    assert outbox_item.event_reason is NotificationSourceFamily.NEW_LISTINGS_FOUND
    assert outbox_item.listing_count == 1
    assert outbox_item.safe_listing_reference_ids == ("listing-1",)
    assert outbox_item.source_event_id == "source-event-1"
    assert outbox_item.source_fact_id == "fact-1"
    assert outbox_item.source_commit_reference == "commit-1"
    assert outbox_item.source_producer is NotificationSourceProducer.SCAN_ORCHESTRATION
    assert outbox_item.source_contract == "scan.notification.v1"
    assert outbox_item.source_contract_version == "1.0"
    assert outbox_item.account_id == "account-1"
    assert outbox_item.beacon_id == "beacon-1"
    assert outbox_item.scan_run_id == "scan-run-1"
    assert outbox_item.correlation_id == "corr-1"
    assert outbox_item.causation_id == "cause-1"
    assert outbox_item.idempotency_key.value == "key-1"
    assert outbox_item.idempotency_fingerprint.value == "fingerprint-1"
    assert outbox_item.idempotency_scope.value == "scope-1"
    assert outbox_item.evidence_reference_ids == ("outbox-evidence-1",)
    assert len(outbox_item.channel_intents) == 2
    assert tuple(intent.channel_class for intent in outbox_item.channel_intents) == (
        NotificationChannelClass.TELEGRAM,
        NotificationChannelClass.MAX,
    )
    assert all(
        intent.target_reference_id in {"telegram-target-1", "max-target-1"}
        for intent in outbox_item.channel_intents
    )


def test_telegram_and_max_create_one_item_with_two_intents_not_two_items() -> None:
    eligibility_decision = _eligibility_decision()
    decision = create_notification_outbox_item(
        decision_id="outbox-decision-2",
        outbox_item_id="outbox-item-2",
        outbox_contract="notification.outbox.v1",
        outbox_contract_version="1.0",
        eligibility_decision=eligibility_decision,
        idempotency_key=eligibility_decision.source_intake_decision.source_event.idempotency_key,
        idempotency_fingerprint=eligibility_decision.source_intake_decision.source_event.idempotency_fingerprint,
        idempotency_scope=eligibility_decision.source_intake_decision.source_event.idempotency_scope,
        existing_outbox_item=None,
        evidence_reference_ids=("outbox-evidence-2",),
    )

    assert decision.status is NotificationOutboxCreationStatus.CREATED
    assert decision.outbox_item_created is True
    assert decision.replayed is False
    assert decision.outbox_item is not None
    assert len(decision.outbox_item.channel_intents) == 2
    assert decision.delivery_attempt_authorized is False


def test_web_channel_is_excluded_from_push_intents() -> None:
    eligibility_decision = _eligibility_decision()
    decision = create_notification_outbox_item(
        decision_id="outbox-decision-3",
        outbox_item_id="outbox-item-3",
        outbox_contract="notification.outbox.v1",
        outbox_contract_version="1.0",
        eligibility_decision=eligibility_decision,
        idempotency_key=eligibility_decision.source_intake_decision.source_event.idempotency_key,
        idempotency_fingerprint=eligibility_decision.source_intake_decision.source_event.idempotency_fingerprint,
        idempotency_scope=eligibility_decision.source_intake_decision.source_event.idempotency_scope,
        existing_outbox_item=None,
        evidence_reference_ids=("outbox-evidence-3",),
    )

    assert decision.outbox_item is not None
    assert all(
        intent.channel_class is not NotificationChannelClass.WEB_STATUS_READ_MODEL
        for intent in decision.outbox_item.channel_intents
    )


def test_telegram_only_case_creates_a_single_intent() -> None:
    context = _context(max_enabled_by_user=False)
    eligibility_decision = _eligibility_decision(context=context)
    decision = create_notification_outbox_item(
        decision_id="outbox-decision-4",
        outbox_item_id="outbox-item-4",
        outbox_contract="notification.outbox.v1",
        outbox_contract_version="1.0",
        eligibility_decision=eligibility_decision,
        idempotency_key=eligibility_decision.source_intake_decision.source_event.idempotency_key,
        idempotency_fingerprint=eligibility_decision.source_intake_decision.source_event.idempotency_fingerprint,
        idempotency_scope=eligibility_decision.source_intake_decision.source_event.idempotency_scope,
        existing_outbox_item=None,
        evidence_reference_ids=("outbox-evidence-4",),
    )

    assert decision.status is NotificationOutboxCreationStatus.CREATED
    assert decision.outbox_item is not None
    assert tuple(intent.channel_class for intent in decision.outbox_item.channel_intents) == (
        NotificationChannelClass.TELEGRAM,
    )


def test_twenty_listing_references_are_preserved_exactly_without_truncation() -> None:
    safe_listing_reference_ids = tuple(f"listing-{index:02d}" for index in range(1, 21))
    eligibility_decision = _eligibility_decision(
        safe_listing_reference_ids=safe_listing_reference_ids,
        listing_count=20,
    )
    decision = create_notification_outbox_item(
        decision_id="outbox-decision-5",
        outbox_item_id="outbox-item-5",
        outbox_contract="notification.outbox.v1",
        outbox_contract_version="1.0",
        eligibility_decision=eligibility_decision,
        idempotency_key=eligibility_decision.source_intake_decision.source_event.idempotency_key,
        idempotency_fingerprint=eligibility_decision.source_intake_decision.source_event.idempotency_fingerprint,
        idempotency_scope=eligibility_decision.source_intake_decision.source_event.idempotency_scope,
        existing_outbox_item=None,
        evidence_reference_ids=("outbox-evidence-5",),
    )

    assert decision.outbox_item is not None
    assert decision.outbox_item.listing_count == 20
    assert decision.outbox_item.safe_listing_reference_ids == safe_listing_reference_ids


def test_recovery_result_with_zero_listings_creates_an_item() -> None:
    recovery_context = _context(
        lifecycle_status=NotificationBeaconLifecycleStatus.FROZEN,
        entitlement_status=NotificationEntitlementStatus.EXPIRED,
        recovery_grace_evidence=_recovery_evidence(
            problem_began_while_access_active=True,
            recovery_obligation_reference_id="obligation-1",
            recovery_result_already_consumed=False,
            beacon_frozen_due_to_access_expiry=True,
        ),
    )
    eligibility_decision = _eligibility_decision(
        family=NotificationSourceFamily.RECOVERY_SCAN_COMPLETED,
        listing_count=0,
        safe_listing_reference_ids=(),
        context=recovery_context,
    )
    decision = create_notification_outbox_item(
        decision_id="outbox-decision-6",
        outbox_item_id="outbox-item-6",
        outbox_contract="notification.outbox.v1",
        outbox_contract_version="1.0",
        eligibility_decision=eligibility_decision,
        idempotency_key=eligibility_decision.source_intake_decision.source_event.idempotency_key,
        idempotency_fingerprint=eligibility_decision.source_intake_decision.source_event.idempotency_fingerprint,
        idempotency_scope=eligibility_decision.source_intake_decision.source_event.idempotency_scope,
        existing_outbox_item=None,
        evidence_reference_ids=("outbox-evidence-6",),
    )

    assert decision.status is NotificationOutboxCreationStatus.CREATED
    assert decision.outbox_item is not None
    assert decision.outbox_item.listing_count == 0
    assert decision.outbox_item.safe_listing_reference_ids == ()
    assert decision.outbox_item.event_reason is NotificationSourceFamily.RECOVERY_SCAN_COMPLETED


def test_no_new_status_with_approved_preference_creates_one_item() -> None:
    context = _context(
        family=NotificationSourceFamily.NO_NEW_LISTINGS_STATUS,
        listing_count=0,
        safe_listing_reference_ids=(),
        no_new_status_preference_enabled=True,
        no_new_status_frequency_minutes=NO_NEW_MINIMUM_FREQUENCY_MINUTES,
    )
    eligibility_decision = _eligibility_decision(
        family=NotificationSourceFamily.NO_NEW_LISTINGS_STATUS,
        listing_count=0,
        safe_listing_reference_ids=(),
        context=context,
    )
    decision = create_notification_outbox_item(
        decision_id="outbox-decision-7",
        outbox_item_id="outbox-item-7",
        outbox_contract="notification.outbox.v1",
        outbox_contract_version="1.0",
        eligibility_decision=eligibility_decision,
        idempotency_key=eligibility_decision.source_intake_decision.source_event.idempotency_key,
        idempotency_fingerprint=eligibility_decision.source_intake_decision.source_event.idempotency_fingerprint,
        idempotency_scope=eligibility_decision.source_intake_decision.source_event.idempotency_scope,
        existing_outbox_item=None,
        evidence_reference_ids=("outbox-evidence-7",),
    )

    assert decision.status is NotificationOutboxCreationStatus.CREATED
    assert decision.outbox_item is not None
    assert decision.outbox_item.listing_count == 0
    assert decision.outbox_item.safe_listing_reference_ids == ()
    assert decision.outbox_item.event_reason is NotificationSourceFamily.NO_NEW_LISTINGS_STATUS


def test_service_access_fact_with_beacon_id_none_creates_one_item() -> None:
    context = _context(
        beacon_id=None,
        lifecycle_status=NotificationBeaconLifecycleStatus.NOT_APPLICABLE,
        lifecycle_reference_id=None,
        entitlement_status=NotificationEntitlementStatus.NOT_APPLICABLE,
        entitlement_reference_id=None,
    )
    eligibility_decision = _eligibility_decision(
        family=NotificationSourceFamily.APPROVED_SERVICE_ACCESS_FACT,
        producer=NotificationSourceProducer.ENTITLEMENTS_OR_BEACON,
        beacon_id=None,
        scan_run_id=None,
        listing_count=0,
        safe_listing_reference_ids=(),
        service_access_gate_approved=True,
        context=context,
    )
    decision = create_notification_outbox_item(
        decision_id="outbox-decision-8",
        outbox_item_id="outbox-item-8",
        outbox_contract="notification.outbox.v1",
        outbox_contract_version="1.0",
        eligibility_decision=eligibility_decision,
        idempotency_key=eligibility_decision.source_intake_decision.source_event.idempotency_key,
        idempotency_fingerprint=eligibility_decision.source_intake_decision.source_event.idempotency_fingerprint,
        idempotency_scope=eligibility_decision.source_intake_decision.source_event.idempotency_scope,
        existing_outbox_item=None,
        evidence_reference_ids=("outbox-evidence-8",),
    )

    assert decision.status is NotificationOutboxCreationStatus.CREATED
    assert decision.outbox_item is not None
    assert decision.outbox_item.beacon_id is None
    assert decision.outbox_item.scan_run_id is None
    assert (
        decision.outbox_item.event_reason is NotificationSourceFamily.APPROVED_SERVICE_ACCESS_FACT
    )


@pytest.mark.parametrize(
    "family, context, expected_status",
    [
        (
            NotificationSourceFamily.LISTING_PRICE_PAIR_FIRST_SEEN,
            _context(),
            NotificationEligibilityStatus.BLOCKED_SOURCE_INTAKE,
        ),
        (
            NotificationSourceFamily.BEACON_BASELINE_ESTABLISHED,
            _context(),
            NotificationEligibilityStatus.BLOCKED_SOURCE_INTAKE,
        ),
        (
            NotificationSourceFamily.NO_NEW_LISTINGS_STATUS,
            _context(
                family=NotificationSourceFamily.NO_NEW_LISTINGS_STATUS,
                listing_count=0,
                safe_listing_reference_ids=(),
                no_new_status_preference_enabled=False,
            ),
            NotificationEligibilityStatus.SUPPRESSED_BY_PREFERENCE,
        ),
        (
            NotificationSourceFamily.NEW_LISTINGS_FOUND,
            _context(
                lifecycle_status=NotificationBeaconLifecycleStatus.AMBIGUOUS,
                lifecycle_reference_id="beacon-lifecycle-ambiguous-1",
            ),
            NotificationEligibilityStatus.BLOCKED_AMBIGUOUS,
        ),
        (
            NotificationSourceFamily.NEW_LISTINGS_FOUND,
            _context(
                telegram_enabled_by_user=False,
                max_enabled_by_user=False,
            ),
            NotificationEligibilityStatus.BLOCKED_NO_ELIGIBLE_PUSH_CHANNEL,
        ),
    ],
)
def test_blocked_suppressed_ambiguous_and_no_channel_eligibility_create_no_item(
    family: NotificationSourceFamily,
    context: NotificationEligibilityContext,
    expected_status: NotificationEligibilityStatus,
) -> None:
    if family is NotificationSourceFamily.NO_NEW_LISTINGS_STATUS:
        eligibility_decision = _eligibility_decision(
            family=family,
            listing_count=0,
            safe_listing_reference_ids=(),
            context=context,
        )
    else:
        eligibility_decision = _eligibility_decision(family=family, context=context)
    decision = create_notification_outbox_item(
        decision_id="outbox-decision-9",
        outbox_item_id="outbox-item-9",
        outbox_contract="notification.outbox.v1",
        outbox_contract_version="1.0",
        eligibility_decision=eligibility_decision,
        idempotency_key=eligibility_decision.source_intake_decision.source_event.idempotency_key,
        idempotency_fingerprint=eligibility_decision.source_intake_decision.source_event.idempotency_fingerprint,
        idempotency_scope=eligibility_decision.source_intake_decision.source_event.idempotency_scope,
        existing_outbox_item=None,
        evidence_reference_ids=("outbox-evidence-9",),
    )

    assert eligibility_decision.status is expected_status
    assert decision.status is NotificationOutboxCreationStatus.BLOCKED_ELIGIBILITY
    assert decision.outbox_item is None
    assert decision.outbox_item_created is False
    assert decision.replayed is False
    assert decision.idempotency_decision is None
    assert decision.delivery_attempt_authorized is False


@pytest.mark.parametrize(
    "family",
    [
        NotificationSourceFamily.LISTING_PRICE_PAIR_FIRST_SEEN,
        NotificationSourceFamily.BEACON_BASELINE_ESTABLISHED,
    ],
)
def test_price_change_and_baseline_sources_cannot_reach_outbox_creation_through_nd02_nd03_flow(
    family: NotificationSourceFamily,
) -> None:
    intake_decision = _source_intake_decision(family=family)
    eligibility_decision = evaluate_notification_eligibility(
        decision_id="eligibility-blocked-1",
        source_intake_decision=intake_decision,
        context=_context(),
        evidence_reference_ids=("eligibility-evidence-blocked-1",),
    )
    decision = create_notification_outbox_item(
        decision_id="outbox-decision-10",
        outbox_item_id="outbox-item-10",
        outbox_contract="notification.outbox.v1",
        outbox_contract_version="1.0",
        eligibility_decision=eligibility_decision,
        idempotency_key=intake_decision.source_event.idempotency_key,
        idempotency_fingerprint=intake_decision.source_event.idempotency_fingerprint,
        idempotency_scope=intake_decision.source_event.idempotency_scope,
        existing_outbox_item=None,
        evidence_reference_ids=("outbox-evidence-10",),
    )

    assert intake_decision.status in (
        NotificationSourceIntakeStatus.REJECTED_DISABLED_SOURCE,
        NotificationSourceIntakeStatus.REJECTED_NON_NOTIFICATION_SOURCE,
    )
    assert decision.status is NotificationOutboxCreationStatus.BLOCKED_ELIGIBILITY
    assert decision.outbox_item is None


def test_same_request_without_existing_item_is_deterministic() -> None:
    eligibility_decision = _eligibility_decision()
    first = create_notification_outbox_item(
        decision_id="outbox-decision-11",
        outbox_item_id="outbox-item-11",
        outbox_contract="notification.outbox.v1",
        outbox_contract_version="1.0",
        eligibility_decision=eligibility_decision,
        idempotency_key=eligibility_decision.source_intake_decision.source_event.idempotency_key,
        idempotency_fingerprint=eligibility_decision.source_intake_decision.source_event.idempotency_fingerprint,
        idempotency_scope=eligibility_decision.source_intake_decision.source_event.idempotency_scope,
        existing_outbox_item=None,
        evidence_reference_ids=("outbox-evidence-11",),
    )
    second = create_notification_outbox_item(
        decision_id="outbox-decision-11",
        outbox_item_id="outbox-item-11",
        outbox_contract="notification.outbox.v1",
        outbox_contract_version="1.0",
        eligibility_decision=eligibility_decision,
        idempotency_key=eligibility_decision.source_intake_decision.source_event.idempotency_key,
        idempotency_fingerprint=eligibility_decision.source_intake_decision.source_event.idempotency_fingerprint,
        idempotency_scope=eligibility_decision.source_intake_decision.source_event.idempotency_scope,
        existing_outbox_item=None,
        evidence_reference_ids=("outbox-evidence-11",),
    )

    assert first == second
    assert first.status is NotificationOutboxCreationStatus.CREATED
    assert second.status is NotificationOutboxCreationStatus.CREATED
    assert first.outbox_item == second.outbox_item
    assert first.outbox_item is not None
    assert second.outbox_item is not None
    assert first.outbox_item_created is True
    assert second.outbox_item_created is True
    assert first.delivery_attempt_authorized is False
    assert second.delivery_attempt_authorized is False


def test_replay_returns_the_original_object_and_ignores_new_item_id() -> None:
    eligibility_decision = _eligibility_decision()
    initial = create_notification_outbox_item(
        decision_id="outbox-decision-12",
        outbox_item_id="outbox-item-12-original",
        outbox_contract="notification.outbox.v1",
        outbox_contract_version="1.0",
        eligibility_decision=eligibility_decision,
        idempotency_key=eligibility_decision.source_intake_decision.source_event.idempotency_key,
        idempotency_fingerprint=eligibility_decision.source_intake_decision.source_event.idempotency_fingerprint,
        idempotency_scope=eligibility_decision.source_intake_decision.source_event.idempotency_scope,
        existing_outbox_item=None,
        evidence_reference_ids=("outbox-evidence-12",),
    )
    assert initial.outbox_item is not None

    replayed = create_notification_outbox_item(
        decision_id="outbox-decision-12",
        outbox_item_id="outbox-item-12-new",
        outbox_contract="notification.outbox.v1",
        outbox_contract_version="1.0",
        eligibility_decision=eligibility_decision,
        idempotency_key=eligibility_decision.source_intake_decision.source_event.idempotency_key,
        idempotency_fingerprint=eligibility_decision.source_intake_decision.source_event.idempotency_fingerprint,
        idempotency_scope=eligibility_decision.source_intake_decision.source_event.idempotency_scope,
        existing_outbox_item=initial.outbox_item,
        evidence_reference_ids=("outbox-evidence-12",),
    )

    assert replayed.status is NotificationOutboxCreationStatus.REPLAYED
    assert replayed.outbox_item is initial.outbox_item
    assert replayed.outbox_item is not None
    assert replayed.outbox_item_created is False
    assert replayed.replayed is True
    assert replayed.idempotency_decision is IdempotencyDecision.REPLAY_TERMINAL
    assert replayed.delivery_attempt_authorized is False
    assert replayed.reason_codes == ("outbox-replayed",)


def test_fingerprint_mismatch_has_no_effect() -> None:
    eligibility_decision = _eligibility_decision()
    initial = create_notification_outbox_item(
        decision_id="outbox-decision-13",
        outbox_item_id="outbox-item-13",
        outbox_contract="notification.outbox.v1",
        outbox_contract_version="1.0",
        eligibility_decision=eligibility_decision,
        idempotency_key=eligibility_decision.source_intake_decision.source_event.idempotency_key,
        idempotency_fingerprint=eligibility_decision.source_intake_decision.source_event.idempotency_fingerprint,
        idempotency_scope=eligibility_decision.source_intake_decision.source_event.idempotency_scope,
        existing_outbox_item=None,
        evidence_reference_ids=("outbox-evidence-13",),
    )
    assert initial.outbox_item is not None

    mismatch = create_notification_outbox_item(
        decision_id="outbox-decision-13",
        outbox_item_id="outbox-item-13-different",
        outbox_contract="notification.outbox.v1",
        outbox_contract_version="1.0",
        eligibility_decision=eligibility_decision,
        idempotency_key=eligibility_decision.source_intake_decision.source_event.idempotency_key,
        idempotency_fingerprint=IdempotencyFingerprint(value="fingerprint-2"),
        idempotency_scope=eligibility_decision.source_intake_decision.source_event.idempotency_scope,
        existing_outbox_item=initial.outbox_item,
        evidence_reference_ids=("outbox-evidence-13",),
    )

    assert mismatch.status is NotificationOutboxCreationStatus.IDEMPOTENCY_MISMATCH
    assert mismatch.outbox_item is None
    assert mismatch.outbox_item_created is False
    assert mismatch.replayed is False
    assert mismatch.idempotency_decision is IdempotencyDecision.MISMATCH
    assert mismatch.reason_codes == ("outbox-idempotency-fingerprint-mismatch",)
    assert mismatch.delivery_attempt_authorized is False
    assert initial.outbox_item is not None
    assert initial.outbox_item.idempotency_fingerprint.value == "fingerprint-1"


def test_same_fingerprint_but_changed_semantic_request_has_no_effect() -> None:
    eligibility_decision = _eligibility_decision()
    initial = create_notification_outbox_item(
        decision_id="outbox-decision-14",
        outbox_item_id="outbox-item-14",
        outbox_contract="notification.outbox.v1",
        outbox_contract_version="1.0",
        eligibility_decision=eligibility_decision,
        idempotency_key=eligibility_decision.source_intake_decision.source_event.idempotency_key,
        idempotency_fingerprint=eligibility_decision.source_intake_decision.source_event.idempotency_fingerprint,
        idempotency_scope=eligibility_decision.source_intake_decision.source_event.idempotency_scope,
        existing_outbox_item=None,
        evidence_reference_ids=("outbox-evidence-14",),
    )
    assert initial.outbox_item is not None

    telegram_only_decision = _eligibility_decision(
        context=_context(max_enabled_by_user=False),
    )
    mismatch = create_notification_outbox_item(
        decision_id="outbox-decision-14",
        outbox_item_id="outbox-item-14-semantic-change",
        outbox_contract="notification.outbox.v1",
        outbox_contract_version="1.0",
        eligibility_decision=telegram_only_decision,
        idempotency_key=telegram_only_decision.source_intake_decision.source_event.idempotency_key,
        idempotency_fingerprint=telegram_only_decision.source_intake_decision.source_event.idempotency_fingerprint,
        idempotency_scope=telegram_only_decision.source_intake_decision.source_event.idempotency_scope,
        existing_outbox_item=initial.outbox_item,
        evidence_reference_ids=("outbox-evidence-14",),
    )

    assert mismatch.status is NotificationOutboxCreationStatus.IDEMPOTENCY_MISMATCH
    assert mismatch.outbox_item is None
    assert mismatch.reason_codes == ("outbox-idempotency-semantic-mismatch",)
    assert mismatch.idempotency_decision is IdempotencyDecision.MISMATCH
    assert initial.outbox_item is not None
    assert tuple(intent.channel_class for intent in initial.outbox_item.channel_intents) == (
        NotificationChannelClass.TELEGRAM,
        NotificationChannelClass.MAX,
    )
    assert initial.outbox_item is not None
    assert tuple(
        intent.channel_class
        for intent in telegram_only_decision.channel_gate_decisions
        if intent.push_eligible
    ) == (NotificationChannelClass.TELEGRAM,)


def test_unrelated_existing_key_scope_raises_value_error() -> None:
    eligibility_decision = _eligibility_decision()
    initial = create_notification_outbox_item(
        decision_id="outbox-decision-15",
        outbox_item_id="outbox-item-15",
        outbox_contract="notification.outbox.v1",
        outbox_contract_version="1.0",
        eligibility_decision=eligibility_decision,
        idempotency_key=eligibility_decision.source_intake_decision.source_event.idempotency_key,
        idempotency_fingerprint=eligibility_decision.source_intake_decision.source_event.idempotency_fingerprint,
        idempotency_scope=eligibility_decision.source_intake_decision.source_event.idempotency_scope,
        existing_outbox_item=None,
        evidence_reference_ids=("outbox-evidence-15",),
    )
    assert initial.outbox_item is not None

    with pytest.raises(ValueError, match=r"^caller supplied an unrelated existing record\.$"):
        create_notification_outbox_item(
            decision_id="outbox-decision-15",
            outbox_item_id="outbox-item-15",
            outbox_contract="notification.outbox.v1",
            outbox_contract_version="1.0",
            eligibility_decision=eligibility_decision,
            idempotency_key=IdempotencyKey(value="different-key"),
            idempotency_fingerprint=eligibility_decision.source_intake_decision.source_event.idempotency_fingerprint,
            idempotency_scope=IdempotencyScope(value="different-scope"),
            existing_outbox_item=initial.outbox_item,
            evidence_reference_ids=("outbox-evidence-15",),
        )


@pytest.mark.parametrize(
    "decision_factory",
    [
        lambda: create_notification_outbox_item(
            decision_id="outbox-decision-16",
            outbox_item_id="outbox-item-16",
            outbox_contract="notification.outbox.v1",
            outbox_contract_version="1.0",
            eligibility_decision=_eligibility_decision(),
            idempotency_key=_eligibility_decision().source_intake_decision.source_event.idempotency_key,
            idempotency_fingerprint=_eligibility_decision().source_intake_decision.source_event.idempotency_fingerprint,
            idempotency_scope=_eligibility_decision().source_intake_decision.source_event.idempotency_scope,
            existing_outbox_item=None,
            evidence_reference_ids=("outbox-evidence-16",),
        ),
        lambda: create_notification_outbox_item(
            decision_id="outbox-decision-17",
            outbox_item_id="outbox-item-17",
            outbox_contract="notification.outbox.v1",
            outbox_contract_version="1.0",
            eligibility_decision=_eligibility_decision(
                context=_context(max_enabled_by_user=False),
            ),
            idempotency_key=_eligibility_decision(
                context=_context(max_enabled_by_user=False),
            ).source_intake_decision.source_event.idempotency_key,
            idempotency_fingerprint=_eligibility_decision(
                context=_context(max_enabled_by_user=False),
            ).source_intake_decision.source_event.idempotency_fingerprint,
            idempotency_scope=_eligibility_decision(
                context=_context(max_enabled_by_user=False),
            ).source_intake_decision.source_event.idempotency_scope,
            existing_outbox_item=None,
            evidence_reference_ids=("outbox-evidence-17",),
        ),
        lambda: create_notification_outbox_item(
            decision_id="outbox-decision-18",
            outbox_item_id="outbox-item-18",
            outbox_contract="notification.outbox.v1",
            outbox_contract_version="1.0",
            eligibility_decision=_eligibility_decision(
                family=NotificationSourceFamily.NO_NEW_LISTINGS_STATUS,
                listing_count=0,
                safe_listing_reference_ids=(),
                context=_context(
                    family=NotificationSourceFamily.NO_NEW_LISTINGS_STATUS,
                    listing_count=0,
                    safe_listing_reference_ids=(),
                    no_new_status_preference_enabled=True,
                    no_new_status_frequency_minutes=NO_NEW_MINIMUM_FREQUENCY_MINUTES,
                ),
            ),
            idempotency_key=_eligibility_decision(
                family=NotificationSourceFamily.NO_NEW_LISTINGS_STATUS,
                listing_count=0,
                safe_listing_reference_ids=(),
                context=_context(
                    family=NotificationSourceFamily.NO_NEW_LISTINGS_STATUS,
                    listing_count=0,
                    safe_listing_reference_ids=(),
                    no_new_status_preference_enabled=True,
                    no_new_status_frequency_minutes=NO_NEW_MINIMUM_FREQUENCY_MINUTES,
                ),
            ).source_intake_decision.source_event.idempotency_key,
            idempotency_fingerprint=_eligibility_decision(
                family=NotificationSourceFamily.NO_NEW_LISTINGS_STATUS,
                listing_count=0,
                safe_listing_reference_ids=(),
                context=_context(
                    family=NotificationSourceFamily.NO_NEW_LISTINGS_STATUS,
                    listing_count=0,
                    safe_listing_reference_ids=(),
                    no_new_status_preference_enabled=True,
                    no_new_status_frequency_minutes=NO_NEW_MINIMUM_FREQUENCY_MINUTES,
                ),
            ).source_intake_decision.source_event.idempotency_fingerprint,
            idempotency_scope=_eligibility_decision(
                family=NotificationSourceFamily.NO_NEW_LISTINGS_STATUS,
                listing_count=0,
                safe_listing_reference_ids=(),
                context=_context(
                    family=NotificationSourceFamily.NO_NEW_LISTINGS_STATUS,
                    listing_count=0,
                    safe_listing_reference_ids=(),
                    no_new_status_preference_enabled=True,
                    no_new_status_frequency_minutes=NO_NEW_MINIMUM_FREQUENCY_MINUTES,
                ),
            ).source_intake_decision.source_event.idempotency_scope,
            existing_outbox_item=None,
            evidence_reference_ids=("outbox-evidence-18",),
        ),
        lambda: create_notification_outbox_item(
            decision_id="outbox-decision-19",
            outbox_item_id="outbox-item-19",
            outbox_contract="notification.outbox.v1",
            outbox_contract_version="1.0",
            eligibility_decision=_eligibility_decision(
                family=NotificationSourceFamily.APPROVED_SERVICE_ACCESS_FACT,
                producer=NotificationSourceProducer.ENTITLEMENTS_OR_BEACON,
                beacon_id=None,
                scan_run_id=None,
                listing_count=0,
                safe_listing_reference_ids=(),
                service_access_gate_approved=True,
                context=_context(
                    beacon_id=None,
                    lifecycle_status=NotificationBeaconLifecycleStatus.NOT_APPLICABLE,
                    lifecycle_reference_id=None,
                    entitlement_status=NotificationEntitlementStatus.NOT_APPLICABLE,
                    entitlement_reference_id=None,
                ),
            ),
            idempotency_key=_eligibility_decision(
                family=NotificationSourceFamily.APPROVED_SERVICE_ACCESS_FACT,
                producer=NotificationSourceProducer.ENTITLEMENTS_OR_BEACON,
                beacon_id=None,
                scan_run_id=None,
                listing_count=0,
                safe_listing_reference_ids=(),
                service_access_gate_approved=True,
                context=_context(
                    beacon_id=None,
                    lifecycle_status=NotificationBeaconLifecycleStatus.NOT_APPLICABLE,
                    lifecycle_reference_id=None,
                    entitlement_status=NotificationEntitlementStatus.NOT_APPLICABLE,
                    entitlement_reference_id=None,
                ),
            ).source_intake_decision.source_event.idempotency_key,
            idempotency_fingerprint=_eligibility_decision(
                family=NotificationSourceFamily.APPROVED_SERVICE_ACCESS_FACT,
                producer=NotificationSourceProducer.ENTITLEMENTS_OR_BEACON,
                beacon_id=None,
                scan_run_id=None,
                listing_count=0,
                safe_listing_reference_ids=(),
                service_access_gate_approved=True,
                context=_context(
                    beacon_id=None,
                    lifecycle_status=NotificationBeaconLifecycleStatus.NOT_APPLICABLE,
                    lifecycle_reference_id=None,
                    entitlement_status=NotificationEntitlementStatus.NOT_APPLICABLE,
                    entitlement_reference_id=None,
                ),
            ).source_intake_decision.source_event.idempotency_fingerprint,
            idempotency_scope=_eligibility_decision(
                family=NotificationSourceFamily.APPROVED_SERVICE_ACCESS_FACT,
                producer=NotificationSourceProducer.ENTITLEMENTS_OR_BEACON,
                beacon_id=None,
                scan_run_id=None,
                listing_count=0,
                safe_listing_reference_ids=(),
                service_access_gate_approved=True,
                context=_context(
                    beacon_id=None,
                    lifecycle_status=NotificationBeaconLifecycleStatus.NOT_APPLICABLE,
                    lifecycle_reference_id=None,
                    entitlement_status=NotificationEntitlementStatus.NOT_APPLICABLE,
                    entitlement_reference_id=None,
                ),
            ).source_intake_decision.source_event.idempotency_scope,
            existing_outbox_item=None,
            evidence_reference_ids=("outbox-evidence-19",),
        ),
    ],
)
def test_every_outcome_keeps_delivery_attempt_unauthorized(
    decision_factory: Callable[[], NotificationEligibilityDecision],
) -> None:
    decision = decision_factory()
    assert decision.delivery_attempt_authorized is False
