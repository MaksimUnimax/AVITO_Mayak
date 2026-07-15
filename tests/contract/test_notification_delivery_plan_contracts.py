from __future__ import annotations

import inspect
import re
from dataclasses import fields, is_dataclass
from enum import Enum, EnumMeta
from pathlib import Path
from typing import get_type_hints

from mayak.modules import notification_delivery
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
from mayak.modules.notification_delivery.eligibility import NotificationChannelClass
from mayak.modules.notification_delivery.outbox import (
    NotificationOutboxChannelIntent,
    NotificationOutboxCreationDecision,
    NotificationOutboxItem,
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

EXPECTED_ENUM_VALUES = {
    NotificationDeliveryPlanAuthority: ("NOTIFICATION_DELIVERY_SERVER",),
    NotificationDeliveryChannelPlanStatus: (
        "TELEGRAM_ENABLED",
        "MAX_ENABLED",
        "WEB_STATUS_READ_MODEL",
        "CHANNEL_DISABLED_BY_USER",
        "CHANNEL_TARGET_UNVERIFIED",
        "CHANNEL_TARGET_UNAVAILABLE",
    ),
    NotificationDeliveryPlanDecisionStatus: (
        "PLANNED",
        "BLOCKED_OUTBOX",
        "BLOCKED_CHANNEL_PLAN_AMBIGUOUS",
        "BLOCKED_NO_PUSH_CHANNEL",
    ),
}

EXPECTED_DATACLASS_FIELDS = {
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

EXPECTED_FIELD_TYPES: dict[type[object], dict[str, object]] = {
    NotificationDeliveryChannelPlanEntry: {
        "channel_class": NotificationChannelClass,
        "status": NotificationDeliveryChannelPlanStatus,
        "push_planned": bool,
        "read_model_planned": bool,
        "target_reference_id": str | None,
        "outbox_channel_intent": NotificationOutboxChannelIntent | None,
        "reason_codes": tuple[str, ...],
        "evidence_reference_ids": tuple[str, ...],
    },
    NotificationDeliveryPlan: {
        "delivery_plan_id": str,
        "authority": NotificationDeliveryPlanAuthority,
        "outbox_item": NotificationOutboxItem,
        "account_id": str,
        "beacon_id": str | None,
        "channel_entries": tuple[NotificationDeliveryChannelPlanEntry, ...],
        "push_channel_classes": tuple[NotificationChannelClass, ...],
        "web_status_read_model_planned": bool,
        "delivery_attempt_authorized": bool,
        "provider_mapping_authorized": bool,
        "evidence_reference_ids": tuple[str, ...],
    },
    NotificationDeliveryPlanDecision: {
        "decision_id": str,
        "authority": NotificationDeliveryPlanAuthority,
        "outbox_creation_decision": NotificationOutboxCreationDecision,
        "status": NotificationDeliveryPlanDecisionStatus,
        "delivery_plan": NotificationDeliveryPlan | None,
        "plan_created": bool,
        "delivery_attempt_authorized": bool,
        "provider_mapping_authorized": bool,
        "reason_codes": tuple[str, ...],
        "evidence_reference_ids": tuple[str, ...],
    },
}

FORBIDDEN_FIELD_NAMES = {
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


def _enum_values(enum_type: EnumMeta) -> tuple[str, ...]:
    members: list[Enum] = list(enum_type)
    return tuple(str(member.value) for member in members)


def _enum_names(enum_type: EnumMeta) -> tuple[str, ...]:
    members: list[Enum] = list(enum_type)
    return tuple(member.name for member in members)


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
    assert notification_delivery_plan.__all__ == EXPECTED_ND05_PACKAGE_EXPORTS
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
    assert "__getattr__" not in notification_delivery.__dict__
    assert "_delivery_plan" in notification_delivery.__dict__

    namespace: dict[str, object] = {}
    exec("from mayak.modules.notification_delivery import *", namespace)
    assert all(name in namespace for name in notification_delivery.__all__)
    assert (
        tuple(name for name in namespace if not name.startswith("__"))
        == notification_delivery.__all__
    )


def test_enum_values_are_exact_and_have_no_extras() -> None:
    for enum_type, expected_values in EXPECTED_ENUM_VALUES.items():
        assert _enum_values(enum_type) == expected_values
        assert _enum_names(enum_type) == expected_values


def test_dataclass_field_order_and_slotting_are_exact() -> None:
    for dataclass_type, expected_fields in EXPECTED_DATACLASS_FIELDS.items():
        assert is_dataclass(dataclass_type)
        assert getattr(dataclass_type, "__dataclass_params__").frozen is True
        assert getattr(dataclass_type, "__slots__") == expected_fields
        assert tuple(field.name for field in fields(dataclass_type)) == expected_fields


def test_dataclass_type_references_are_exact() -> None:
    entry_hints = get_type_hints(NotificationDeliveryChannelPlanEntry)
    plan_hints = get_type_hints(NotificationDeliveryPlan)
    decision_hints = get_type_hints(NotificationDeliveryPlanDecision)

    for field_name, expected_type in EXPECTED_FIELD_TYPES[
        NotificationDeliveryChannelPlanEntry
    ].items():
        assert entry_hints[field_name] == expected_type
    for field_name, expected_type in EXPECTED_FIELD_TYPES[NotificationDeliveryPlan].items():
        assert plan_hints[field_name] == expected_type
    for field_name, expected_type in EXPECTED_FIELD_TYPES[NotificationDeliveryPlanDecision].items():
        assert decision_hints[field_name] == expected_type


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
    assert get_type_hints(plan_notification_delivery)["return"] is NotificationDeliveryPlanDecision


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
    for dataclass_type in EXPECTED_DATACLASS_FIELDS:
        field_names.update(field.name for field in fields(dataclass_type))
    assert field_names.isdisjoint(FORBIDDEN_FIELD_NAMES)
