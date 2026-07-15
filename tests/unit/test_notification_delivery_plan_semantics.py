from __future__ import annotations

import inspect
import re
from dataclasses import fields
from pathlib import Path

import pytest

from mayak.contracts.idempotency import (
    IdempotencyDecision,
    IdempotencyFingerprint,
    IdempotencyKey,
    IdempotencyScope,
)
from mayak.modules import notification_delivery
from mayak.modules.notification_delivery import (
    NotificationBeaconLifecycleStatus,
    NotificationChannelClass,
    NotificationChannelEligibilityEvidence,
    NotificationEligibilityContext,
    NotificationEligibilityDecision,
    NotificationEntitlementStatus,
    NotificationOutboxChannelIntent,
    NotificationOutboxCreationDecision,
    NotificationOutboxCreationStatus,
    NotificationOutboxItem,
    NotificationRecoveryGraceEvidence,
    NotificationSourceEvent,
    NotificationSourceFamily,
    NotificationSourceIntakeDecision,
    NotificationSourceProducer,
    create_notification_outbox_item,
    evaluate_notification_eligibility,
    evaluate_notification_source_intake,
)
from mayak.modules.notification_delivery import delivery_plan as notification_delivery_plan
from mayak.modules.notification_delivery.delivery_plan import (
    ND05_TASK_ID,
    NotificationDeliveryChannelPlanEntry,
    NotificationDeliveryChannelPlanStatus,
    NotificationDeliveryPlan,
    NotificationDeliveryPlanAuthority,
    NotificationDeliveryPlanDecision,
    NotificationDeliveryPlanDecisionStatus,
    plan_notification_delivery,
)

EXPECTED_ND05_PACKAGE_EXPORTS = (
    "ND05_TASK_ID",
    "NotificationDeliveryPlanAuthority",
    "NotificationDeliveryChannelPlanStatus",
    "NotificationDeliveryPlanDecisionStatus",
    "NotificationDeliveryChannelPlanEntry",
    "NotificationDeliveryPlan",
    "NotificationDeliveryPlanDecision",
    "plan_notification_delivery",
)

EXPECTED_PACKAGE_EXPORTS = (
    "MODULE_ID",
    "ND02_TASK_ID",
    "NotificationSourceProducer",
    "NotificationSourceFamily",
    "NotificationSourceIntakeAuthority",
    "NotificationSourceIntakeStatus",
    "NotificationSourceEvent",
    "NotificationSourceIntakeDecision",
    "evaluate_notification_source_intake",
    "ND03_TASK_ID",
    "NO_NEW_MINIMUM_FREQUENCY_MINUTES",
    "NotificationEligibilityAuthority",
    "NotificationBeaconLifecycleStatus",
    "NotificationEntitlementStatus",
    "NotificationChannelClass",
    "NotificationChannelGateStatus",
    "NotificationEligibilityStatus",
    "NotificationChannelEligibilityEvidence",
    "NotificationRecoveryGraceEvidence",
    "NotificationEligibilityContext",
    "NotificationChannelGateDecision",
    "NotificationEligibilityDecision",
    "evaluate_notification_eligibility",
    "ND04_TASK_ID",
    "NotificationOutboxAuthority",
    "NotificationOutboxLifecycleStatus",
    "NotificationOutboxCreationStatus",
    "NotificationOutboxChannelIntent",
    "NotificationOutboxItem",
    "NotificationOutboxCreationDecision",
    "create_notification_outbox_item",
    *EXPECTED_ND05_PACKAGE_EXPORTS,
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
        service_access_gate_approved=False,
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


def _recovery_evidence() -> NotificationRecoveryGraceEvidence:
    return NotificationRecoveryGraceEvidence(
        problem_began_while_access_active=False,
        recovery_obligation_reference_id=None,
        recovery_result_already_consumed=False,
        beacon_frozen_due_to_access_expiry=False,
        evidence_reference_ids=("recovery-evidence-1",),
    )


def _context(
    *,
    account_id: str = "account-1",
    beacon_id: str | None = "beacon-1",
    lifecycle_status: NotificationBeaconLifecycleStatus = NotificationBeaconLifecycleStatus.ACTIVE,
    lifecycle_reference_id: str | None = "beacon-lifecycle-1",
    entitlement_status: NotificationEntitlementStatus = NotificationEntitlementStatus.ALLOWED,
    entitlement_reference_id: str | None = "entitlement-1",
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
        no_new_status_preference_enabled=False,
        no_new_status_frequency_minutes=None,
        channel_evidence=channel_evidence,
        recovery_grace_evidence=_recovery_evidence(),
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
    context: NotificationEligibilityContext | None = None,
    decision_id: str = "eligibility-decision-1",
) -> NotificationEligibilityDecision:
    source_intake_decision = _source_intake_decision(
        family=family,
        producer=producer,
        account_id=account_id,
        beacon_id=beacon_id,
        scan_run_id=scan_run_id,
        listing_count=listing_count,
        safe_listing_reference_ids=safe_listing_reference_ids,
    )
    if context is None:
        context = _context(account_id=account_id, beacon_id=beacon_id)
    return evaluate_notification_eligibility(
        decision_id=decision_id,
        source_intake_decision=source_intake_decision,
        context=context,
        evidence_reference_ids=("eligibility-evidence-1",),
    )


def _outbox_decision(
    *,
    eligibility_decision: NotificationEligibilityDecision,
    decision_id: str = "outbox-decision-1",
    outbox_item_id: str = "outbox-item-1",
    existing_outbox_item: NotificationOutboxItem | None = None,
) -> NotificationOutboxCreationDecision:
    source_event = eligibility_decision.source_intake_decision.source_event
    return create_notification_outbox_item(
        decision_id=decision_id,
        outbox_item_id=outbox_item_id,
        outbox_contract="notification.outbox.v1",
        outbox_contract_version="1.0",
        eligibility_decision=eligibility_decision,
        idempotency_key=source_event.idempotency_key,
        idempotency_fingerprint=source_event.idempotency_fingerprint,
        idempotency_scope=source_event.idempotency_scope,
        existing_outbox_item=existing_outbox_item,
        evidence_reference_ids=("outbox-evidence-1",),
    )


def _plan_decision(
    *,
    outbox_creation_decision: NotificationOutboxCreationDecision,
    decision_id: str = "delivery-plan-decision-1",
    delivery_plan_id: str = "delivery-plan-1",
) -> NotificationDeliveryPlanDecision:
    return plan_notification_delivery(
        decision_id=decision_id,
        delivery_plan_id=delivery_plan_id,
        outbox_creation_decision=outbox_creation_decision,
        evidence_reference_ids=("plan-evidence-1",),
    )


def _set_attr(obj: object, field_name: str, value: object) -> None:
    object.__setattr__(obj, field_name, value)


def _fake_web_intent() -> NotificationOutboxChannelIntent:
    intent = object.__new__(NotificationOutboxChannelIntent)
    _set_attr(intent, "channel_class", NotificationChannelClass.WEB_STATUS_READ_MODEL)
    _set_attr(intent, "target_reference_id", "web-target-1")
    _set_attr(intent, "evidence_reference_ids", ("web-evidence-1",))
    return intent


def _mutate_channel_intents(
    outbox_item: NotificationOutboxItem,
    channel_intents: tuple[NotificationOutboxChannelIntent, ...],
) -> None:
    _set_attr(outbox_item, "channel_intents", channel_intents)


def _forge_no_push_outbox_creation_decision() -> NotificationOutboxCreationDecision:
    valid_eligibility = _eligibility_decision()
    valid_outbox = _outbox_decision(eligibility_decision=valid_eligibility)
    assert valid_outbox.outbox_item is not None
    _mutate_channel_intents(valid_outbox.outbox_item, ())

    no_push_eligibility = _eligibility_decision(
        context=_context(
            telegram_enabled_by_user=False,
            max_enabled_by_user=False,
        ),
    )
    decision = object.__new__(NotificationOutboxCreationDecision)
    _set_attr(decision, "decision_id", "outbox-no-push-decision")
    _set_attr(decision, "authority", valid_outbox.authority)
    _set_attr(decision, "eligibility_decision", no_push_eligibility)
    _set_attr(decision, "status", NotificationOutboxCreationStatus.CREATED)
    _set_attr(decision, "outbox_item", valid_outbox.outbox_item)
    _set_attr(decision, "outbox_item_created", True)
    _set_attr(decision, "replayed", False)
    _set_attr(decision, "idempotency_decision", IdempotencyDecision.NEW)
    _set_attr(decision, "delivery_attempt_authorized", False)
    _set_attr(decision, "reason_codes", ("outbox-created",))
    _set_attr(decision, "evidence_reference_ids", ("outbox-evidence-2",))
    return decision


def test_task_id_constant_and_package_exports_are_exact() -> None:
    assert ND05_TASK_ID == "ND-05-MULTI-CHANNEL-DELIVERY-PLAN-20260715-007"
    assert type(notification_delivery.__all__) is tuple
    assert (
        notification_delivery.__all__[: len(EXPECTED_PACKAGE_EXPORTS)] == EXPECTED_PACKAGE_EXPORTS
    )
    nd05_start = len(EXPECTED_PACKAGE_EXPORTS) - len(EXPECTED_ND05_PACKAGE_EXPORTS)
    assert (
        notification_delivery.__all__[nd05_start : nd05_start + len(EXPECTED_ND05_PACKAGE_EXPORTS)]
        == EXPECTED_ND05_PACKAGE_EXPORTS
    )
    assert len(notification_delivery.__all__) == len(set(notification_delivery.__all__))
    assert notification_delivery.ND05_TASK_ID is ND05_TASK_ID
    assert (
        notification_delivery.NotificationDeliveryPlanAuthority is NotificationDeliveryPlanAuthority
    )
    assert (
        notification_delivery.NotificationDeliveryChannelPlanStatus
        is NotificationDeliveryChannelPlanStatus
    )
    assert (
        notification_delivery.NotificationDeliveryPlanDecisionStatus
        is NotificationDeliveryPlanDecisionStatus
    )
    assert (
        notification_delivery.NotificationDeliveryChannelPlanEntry
        is NotificationDeliveryChannelPlanEntry
    )
    assert notification_delivery.NotificationDeliveryPlan is NotificationDeliveryPlan
    assert (
        notification_delivery.NotificationDeliveryPlanDecision is NotificationDeliveryPlanDecision
    )
    assert notification_delivery.plan_notification_delivery is plan_notification_delivery
    assert notification_delivery._delivery_plan is notification_delivery_plan
    assert "__getattr__" not in notification_delivery.__dict__

    namespace: dict[str, object] = {}
    exec("from mayak.modules.notification_delivery import *", namespace)
    assert all(name in namespace for name in notification_delivery.__all__)
    assert (
        tuple(name for name in namespace if not name.startswith("__"))
        == notification_delivery.__all__
    )


def test_enum_values_are_exact_and_have_no_extras() -> None:
    assert tuple(member.value for member in NotificationDeliveryPlanAuthority) == (
        "NOTIFICATION_DELIVERY_SERVER",
    )
    assert tuple(member.value for member in NotificationDeliveryChannelPlanStatus) == (
        "TELEGRAM_ENABLED",
        "MAX_ENABLED",
        "WEB_STATUS_READ_MODEL",
        "CHANNEL_DISABLED_BY_USER",
        "CHANNEL_TARGET_UNVERIFIED",
        "CHANNEL_TARGET_UNAVAILABLE",
    )
    assert tuple(member.value for member in NotificationDeliveryPlanDecisionStatus) == (
        "PLANNED",
        "BLOCKED_OUTBOX",
        "BLOCKED_CHANNEL_PLAN_AMBIGUOUS",
        "BLOCKED_NO_PUSH_CHANNEL",
    )


def test_dataclass_field_order_and_slotting_are_exact() -> None:
    expected_fields = {
        NotificationDeliveryChannelPlanEntry: (
            "channel_class",
            "status",
            "push_planned",
            "read_model_planned",
            "target_reference_id",
            "outbox_channel_intent",
            "reason_codes",
            "evidence_reference_ids",
        ),
        NotificationDeliveryPlan: (
            "delivery_plan_id",
            "authority",
            "outbox_item",
            "account_id",
            "beacon_id",
            "channel_entries",
            "push_channel_classes",
            "web_status_read_model_planned",
            "delivery_attempt_authorized",
            "provider_mapping_authorized",
            "evidence_reference_ids",
        ),
        NotificationDeliveryPlanDecision: (
            "decision_id",
            "authority",
            "outbox_creation_decision",
            "status",
            "delivery_plan",
            "plan_created",
            "delivery_attempt_authorized",
            "provider_mapping_authorized",
            "reason_codes",
            "evidence_reference_ids",
        ),
    }

    for dataclass_type, expected in expected_fields.items():
        assert getattr(dataclass_type, "__dataclass_params__").frozen is True
        assert getattr(dataclass_type, "__slots__") == expected
        assert tuple(field.name for field in fields(dataclass_type)) == expected


def test_dataclass_type_references_are_exact() -> None:
    entry_hints = inspect.get_annotations(NotificationDeliveryChannelPlanEntry, eval_str=True)
    plan_hints = inspect.get_annotations(NotificationDeliveryPlan, eval_str=True)
    decision_hints = inspect.get_annotations(NotificationDeliveryPlanDecision, eval_str=True)

    assert entry_hints["channel_class"] is NotificationChannelClass
    assert entry_hints["status"] is NotificationDeliveryChannelPlanStatus
    assert entry_hints["push_planned"] is bool
    assert entry_hints["read_model_planned"] is bool
    assert entry_hints["target_reference_id"] == str | None
    assert entry_hints["outbox_channel_intent"] == NotificationOutboxChannelIntent | None
    assert entry_hints["reason_codes"] == tuple[str, ...]
    assert entry_hints["evidence_reference_ids"] == tuple[str, ...]

    assert plan_hints["delivery_plan_id"] is str
    assert plan_hints["authority"] is NotificationDeliveryPlanAuthority
    assert plan_hints["outbox_item"] is NotificationOutboxItem
    assert plan_hints["account_id"] is str
    assert plan_hints["beacon_id"] == str | None
    assert plan_hints["channel_entries"] == tuple[NotificationDeliveryChannelPlanEntry, ...]
    assert plan_hints["push_channel_classes"] == tuple[NotificationChannelClass, ...]
    assert plan_hints["web_status_read_model_planned"] is bool
    assert plan_hints["delivery_attempt_authorized"] is bool
    assert plan_hints["provider_mapping_authorized"] is bool
    assert plan_hints["evidence_reference_ids"] == tuple[str, ...]

    assert decision_hints["decision_id"] is str
    assert decision_hints["authority"] is NotificationDeliveryPlanAuthority
    assert decision_hints["outbox_creation_decision"] is NotificationOutboxCreationDecision
    assert decision_hints["status"] is NotificationDeliveryPlanDecisionStatus
    assert decision_hints["delivery_plan"] == NotificationDeliveryPlan | None
    assert decision_hints["plan_created"] is bool
    assert decision_hints["delivery_attempt_authorized"] is bool
    assert decision_hints["provider_mapping_authorized"] is bool
    assert decision_hints["reason_codes"] == tuple[str, ...]
    assert decision_hints["evidence_reference_ids"] == tuple[str, ...]


def test_main_function_signature_is_exact() -> None:
    signature = inspect.signature(plan_notification_delivery)
    assert tuple(signature.parameters) == (
        "decision_id",
        "delivery_plan_id",
        "outbox_creation_decision",
        "evidence_reference_ids",
    )
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for parameter in signature.parameters.values()
    )
    assert (
        inspect.get_annotations(plan_notification_delivery, eval_str=True)["return"]
        is NotificationDeliveryPlanDecision
    )


def test_reason_code_matrix_is_exact() -> None:
    module_text = Path("src/mayak/modules/notification_delivery/delivery_plan.py").read_text()
    reason_codes = set(re.findall(r'"(delivery-plan-[a-z-]+)"', module_text.lower()))
    assert reason_codes == {
        "delivery-plan-created",
        "delivery-plan-outbox-blocked",
        "delivery-plan-channel-evidence-ambiguous",
        "delivery-plan-no-push-channel",
    }


def test_nd05_task_id_appears_exactly_once_in_production_source() -> None:
    module_text = Path("src/mayak/modules/notification_delivery/delivery_plan.py").read_text()
    assert module_text.count(ND05_TASK_ID) == 1


def test_no_primary_fallback_priority_or_runtime_payload_fields_exist() -> None:
    field_names: set[str] = set()
    for dataclass_type in (
        NotificationDeliveryChannelPlanEntry,
        NotificationDeliveryPlan,
        NotificationDeliveryPlanDecision,
    ):
        field_names.update(field.name for field in fields(dataclass_type))
    assert field_names.isdisjoint(
        {
            "created_at",
            "updated_at",
            "deadline",
            "expiry",
            "clock",
            "retry_backoff",
            "reconciliation_record",
            "attempt_id",
            "attempts",
            "provider_payload",
            "raw_payload",
            "message_template",
            "template",
            "dispatch",
            "send",
            "render",
            "cookie",
            "token",
            "secret",
            "credential",
            "primary_channel",
            "fallback_channel",
            "priority",
            "history",
            "read_tracking",
            "click_tracking",
        }
    )


def test_one_outbox_item_produces_one_plan_and_preserves_web_read_model() -> None:
    eligibility_decision = _eligibility_decision()
    outbox_decision = _outbox_decision(eligibility_decision=eligibility_decision)
    plan_decision = _plan_decision(outbox_creation_decision=outbox_decision)

    assert plan_decision.status is NotificationDeliveryPlanDecisionStatus.PLANNED
    assert plan_decision.plan_created is True
    assert plan_decision.delivery_attempt_authorized is False
    assert plan_decision.provider_mapping_authorized is False
    assert plan_decision.decision_id == "delivery-plan-decision-1"
    assert plan_decision.reason_codes == ("delivery-plan-created",)
    assert plan_decision.evidence_reference_ids == ("plan-evidence-1",)
    assert plan_decision.delivery_plan is not None
    assert plan_decision.delivery_plan.delivery_plan_id == "delivery-plan-1"
    assert (
        plan_decision.delivery_plan.authority
        is NotificationDeliveryPlanAuthority.NOTIFICATION_DELIVERY_SERVER
    )
    assert plan_decision.delivery_plan.outbox_item == outbox_decision.outbox_item
    assert plan_decision.delivery_plan.delivery_attempt_authorized is False
    assert plan_decision.delivery_plan.provider_mapping_authorized is False
    assert plan_decision.delivery_plan.web_status_read_model_planned is True
    assert tuple(entry.channel_class for entry in plan_decision.delivery_plan.channel_entries) == (
        NotificationChannelClass.TELEGRAM,
        NotificationChannelClass.MAX,
        NotificationChannelClass.WEB_STATUS_READ_MODEL,
    )
    assert tuple(entry.status for entry in plan_decision.delivery_plan.channel_entries) == (
        NotificationDeliveryChannelPlanStatus.TELEGRAM_ENABLED,
        NotificationDeliveryChannelPlanStatus.MAX_ENABLED,
        NotificationDeliveryChannelPlanStatus.WEB_STATUS_READ_MODEL,
    )
    assert plan_decision.delivery_plan.push_channel_classes == (
        NotificationChannelClass.TELEGRAM,
        NotificationChannelClass.MAX,
    )
    assert plan_decision.delivery_plan.channel_entries[2].push_planned is False
    assert plan_decision.delivery_plan.channel_entries[2].read_model_planned is True
    assert plan_decision.delivery_plan.channel_entries[2].outbox_channel_intent is None


@pytest.mark.parametrize(
    "telegram_enabled,max_enabled,expected_push_classes,expected_statuses",
    [
        (
            True,
            False,
            (NotificationChannelClass.TELEGRAM,),
            (
                NotificationDeliveryChannelPlanStatus.TELEGRAM_ENABLED,
                NotificationDeliveryChannelPlanStatus.CHANNEL_DISABLED_BY_USER,
                NotificationDeliveryChannelPlanStatus.WEB_STATUS_READ_MODEL,
            ),
        ),
        (
            False,
            True,
            (NotificationChannelClass.MAX,),
            (
                NotificationDeliveryChannelPlanStatus.CHANNEL_DISABLED_BY_USER,
                NotificationDeliveryChannelPlanStatus.MAX_ENABLED,
                NotificationDeliveryChannelPlanStatus.WEB_STATUS_READ_MODEL,
            ),
        ),
    ],
)
def test_single_enabled_push_channel_is_preserved(
    telegram_enabled: bool,
    max_enabled: bool,
    expected_push_classes: tuple[NotificationChannelClass, ...],
    expected_statuses: tuple[NotificationDeliveryChannelPlanStatus, ...],
) -> None:
    eligibility_decision = _eligibility_decision(
        context=_context(
            telegram_enabled_by_user=telegram_enabled,
            max_enabled_by_user=max_enabled,
        ),
    )
    outbox_decision = _outbox_decision(eligibility_decision=eligibility_decision)
    plan_decision = _plan_decision(outbox_creation_decision=outbox_decision)

    assert plan_decision.status is NotificationDeliveryPlanDecisionStatus.PLANNED
    assert plan_decision.delivery_plan is not None
    assert plan_decision.delivery_plan.push_channel_classes == expected_push_classes
    assert tuple(entry.status for entry in plan_decision.delivery_plan.channel_entries) == (
        expected_statuses
    )
    assert plan_decision.delivery_plan.web_status_read_model_planned is True
    assert plan_decision.delivery_plan.delivery_attempt_authorized is False
    assert plan_decision.delivery_plan.provider_mapping_authorized is False


@pytest.mark.parametrize(
    "channel_class, context, expected_status, expected_target_reference_id",
    [
        (
            NotificationChannelClass.TELEGRAM,
            _context(
                telegram_enabled_by_user=False,
                telegram_target_reference_id="telegram-target-1",
                telegram_target_verified=True,
                telegram_target_available=True,
                max_enabled_by_user=True,
            ),
            NotificationDeliveryChannelPlanStatus.CHANNEL_DISABLED_BY_USER,
            "telegram-target-1",
        ),
        (
            NotificationChannelClass.TELEGRAM,
            _context(
                telegram_enabled_by_user=True,
                telegram_target_reference_id="telegram-target-2",
                telegram_target_verified=False,
                telegram_target_available=True,
                max_enabled_by_user=True,
            ),
            NotificationDeliveryChannelPlanStatus.CHANNEL_TARGET_UNVERIFIED,
            "telegram-target-2",
        ),
        (
            NotificationChannelClass.MAX,
            _context(
                telegram_enabled_by_user=True,
                max_enabled_by_user=True,
                max_target_reference_id="max-target-2",
                max_target_verified=True,
                max_target_available=False,
            ),
            NotificationDeliveryChannelPlanStatus.CHANNEL_TARGET_UNAVAILABLE,
            "max-target-2",
        ),
    ],
)
def test_blocked_channel_entries_are_preserved_as_evidence(
    channel_class: NotificationChannelClass,
    context: NotificationEligibilityContext,
    expected_status: NotificationDeliveryChannelPlanStatus,
    expected_target_reference_id: str,
) -> None:
    eligibility_decision = _eligibility_decision(context=context)
    outbox_decision = _outbox_decision(eligibility_decision=eligibility_decision)
    plan_decision = _plan_decision(outbox_creation_decision=outbox_decision)

    assert plan_decision.delivery_plan is not None
    entries_by_class = {
        entry.channel_class: entry for entry in plan_decision.delivery_plan.channel_entries
    }
    blocked_entry = entries_by_class[channel_class]
    assert blocked_entry.status is expected_status
    assert blocked_entry.push_planned is False
    assert blocked_entry.read_model_planned is False
    assert blocked_entry.outbox_channel_intent is None
    assert blocked_entry.target_reference_id == expected_target_reference_id
    assert blocked_entry.evidence_reference_ids


def test_created_and_replayed_outbox_decisions_produce_equivalent_semantic_plans() -> None:
    eligibility_decision = _eligibility_decision()
    created = _outbox_decision(eligibility_decision=eligibility_decision)
    assert created.outbox_item is not None
    replayed = _outbox_decision(
        eligibility_decision=eligibility_decision,
        decision_id="outbox-decision-2",
        existing_outbox_item=created.outbox_item,
    )

    created_plan = _plan_decision(outbox_creation_decision=created)
    replayed_plan = _plan_decision(
        outbox_creation_decision=replayed,
        decision_id="delivery-plan-decision-2",
        delivery_plan_id="delivery-plan-1",
    )

    assert created_plan.status is NotificationDeliveryPlanDecisionStatus.PLANNED
    assert replayed_plan.status is NotificationDeliveryPlanDecisionStatus.PLANNED
    assert created_plan.delivery_plan == replayed_plan.delivery_plan
    assert created_plan.delivery_plan is not None
    assert replayed_plan.delivery_plan is not None
    assert created_plan.delivery_plan.channel_entries == replayed_plan.delivery_plan.channel_entries


def test_blocked_outbox_and_idempotency_mismatch_do_not_create_plans() -> None:
    blocked_outbox = _outbox_decision(
        eligibility_decision=_eligibility_decision(
            context=_context(
                telegram_enabled_by_user=False,
                max_enabled_by_user=False,
            ),
        ),
        decision_id="outbox-blocked-decision-1",
    )
    blocked_plan = _plan_decision(
        outbox_creation_decision=blocked_outbox,
        decision_id="delivery-plan-blocked-1",
    )

    mismatch_eligibility = _eligibility_decision()
    _set_attr(
        mismatch_eligibility.source_intake_decision.source_event,
        "idempotency_fingerprint",
        IdempotencyFingerprint(value="fingerprint-mismatch"),
    )
    created = _outbox_decision(eligibility_decision=_eligibility_decision())
    mismatch = _outbox_decision(
        eligibility_decision=mismatch_eligibility,
        decision_id="outbox-mismatch-decision-2",
        existing_outbox_item=created.outbox_item,
    )
    mismatch_plan = _plan_decision(
        outbox_creation_decision=mismatch,
        decision_id="delivery-plan-mismatch-2",
    )

    assert blocked_plan.status is NotificationDeliveryPlanDecisionStatus.BLOCKED_OUTBOX
    assert blocked_plan.delivery_plan is None
    assert blocked_plan.reason_codes == ("delivery-plan-outbox-blocked",)
    assert mismatch_plan.status is NotificationDeliveryPlanDecisionStatus.BLOCKED_OUTBOX
    assert mismatch_plan.delivery_plan is None
    assert mismatch_plan.reason_codes == ("delivery-plan-outbox-blocked",)


def test_missing_mismatched_and_extra_intents_block_ambiguous() -> None:
    missing_intent_outbox = _outbox_decision(eligibility_decision=_eligibility_decision())
    assert missing_intent_outbox.outbox_item is not None
    _mutate_channel_intents(
        missing_intent_outbox.outbox_item,
        (missing_intent_outbox.outbox_item.channel_intents[0],),
    )
    missing_intent_plan = _plan_decision(outbox_creation_decision=missing_intent_outbox)
    assert (
        missing_intent_plan.status
        is NotificationDeliveryPlanDecisionStatus.BLOCKED_CHANNEL_PLAN_AMBIGUOUS
    )
    assert missing_intent_plan.delivery_plan is None
    assert missing_intent_plan.reason_codes == ("delivery-plan-channel-evidence-ambiguous",)

    target_mismatch_outbox = _outbox_decision(eligibility_decision=_eligibility_decision())
    assert target_mismatch_outbox.outbox_item is not None
    _set_attr(
        target_mismatch_outbox.outbox_item.channel_intents[0],
        "target_reference_id",
        "telegram-target-mismatch",
    )
    target_mismatch_plan = _plan_decision(
        outbox_creation_decision=target_mismatch_outbox,
        decision_id="delivery-plan-target-mismatch",
        delivery_plan_id="delivery-plan-target-mismatch",
    )
    assert (
        target_mismatch_plan.status
        is NotificationDeliveryPlanDecisionStatus.BLOCKED_CHANNEL_PLAN_AMBIGUOUS
    )
    assert target_mismatch_plan.delivery_plan is None

    extra_intent_outbox = _outbox_decision(
        eligibility_decision=_eligibility_decision(
            context=_context(max_enabled_by_user=False),
        ),
    )
    assert extra_intent_outbox.outbox_item is not None
    _mutate_channel_intents(
        extra_intent_outbox.outbox_item,
        (
            extra_intent_outbox.outbox_item.channel_intents[0],
            NotificationOutboxChannelIntent(
                channel_class=NotificationChannelClass.MAX,
                target_reference_id="max-target-extra",
                evidence_reference_ids=("max-evidence-extra",),
            ),
        ),
    )
    extra_intent_plan = _plan_decision(outbox_creation_decision=extra_intent_outbox)
    assert (
        extra_intent_plan.status
        is NotificationDeliveryPlanDecisionStatus.BLOCKED_CHANNEL_PLAN_AMBIGUOUS
    )
    assert extra_intent_plan.delivery_plan is None

    web_intent_outbox = _outbox_decision(eligibility_decision=_eligibility_decision())
    assert web_intent_outbox.outbox_item is not None
    _mutate_channel_intents(
        web_intent_outbox.outbox_item,
        (
            *web_intent_outbox.outbox_item.channel_intents,
            _fake_web_intent(),
        ),
    )
    web_intent_plan = _plan_decision(outbox_creation_decision=web_intent_outbox)
    assert (
        web_intent_plan.status
        is NotificationDeliveryPlanDecisionStatus.BLOCKED_CHANNEL_PLAN_AMBIGUOUS
    )
    assert web_intent_plan.delivery_plan is None


def test_duplicate_intents_and_no_push_channel_block() -> None:
    duplicate_intent_outbox = _outbox_decision(eligibility_decision=_eligibility_decision())
    assert duplicate_intent_outbox.outbox_item is not None
    _mutate_channel_intents(
        duplicate_intent_outbox.outbox_item,
        (
            duplicate_intent_outbox.outbox_item.channel_intents[0],
            NotificationOutboxChannelIntent(
                channel_class=NotificationChannelClass.TELEGRAM,
                target_reference_id="telegram-target-duplicate",
                evidence_reference_ids=("telegram-evidence-duplicate",),
            ),
        ),
    )
    duplicate_intent_plan = _plan_decision(outbox_creation_decision=duplicate_intent_outbox)
    assert (
        duplicate_intent_plan.status
        is NotificationDeliveryPlanDecisionStatus.BLOCKED_CHANNEL_PLAN_AMBIGUOUS
    )
    assert duplicate_intent_plan.delivery_plan is None

    no_push_plan = _plan_decision(
        outbox_creation_decision=_forge_no_push_outbox_creation_decision(),
        decision_id="delivery-plan-no-push",
        delivery_plan_id="delivery-plan-no-push",
    )
    assert no_push_plan.status is NotificationDeliveryPlanDecisionStatus.BLOCKED_NO_PUSH_CHANNEL
    assert no_push_plan.delivery_plan is None
    assert no_push_plan.reason_codes == ("delivery-plan-no-push-channel",)


def test_deterministic_identical_input() -> None:
    eligibility_decision = _eligibility_decision()
    outbox_decision = _outbox_decision(eligibility_decision=eligibility_decision)
    first = _plan_decision(outbox_creation_decision=outbox_decision)
    second = _plan_decision(outbox_creation_decision=outbox_decision)

    assert first == second
    assert first.delivery_plan == second.delivery_plan
