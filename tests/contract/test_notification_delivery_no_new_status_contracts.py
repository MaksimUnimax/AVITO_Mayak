from __future__ import annotations

import inspect
from dataclasses import fields, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any, cast, get_type_hints

import mayak.modules.notification_delivery.no_new_status as notification_delivery_no_new_status
from mayak.modules import notification_delivery
from mayak.modules.notification_delivery.delivery_plan import NotificationDeliveryPlanDecision
from mayak.modules.notification_delivery.eligibility import NotificationEligibilityDecision
from mayak.modules.notification_delivery.no_new_status import (
    ND08_TASK_ID,
    NotificationNoNewMinimumFrequencyGateStatus,
    NotificationNoNewStatusAuthority,
    NotificationNoNewStatusDecisionStatus,
    NotificationNoNewStatusPolicyContext,
    NotificationNoNewStatusPolicyDecision,
    evaluate_no_new_status_policy,
)

EXPECTED_MODULE_EXPORTS = (
    "ND08_TASK_ID",
    "NotificationNoNewStatusAuthority",
    "NotificationNoNewMinimumFrequencyGateStatus",
    "NotificationNoNewStatusDecisionStatus",
    "NotificationNoNewStatusPolicyContext",
    "NotificationNoNewStatusPolicyDecision",
    "evaluate_no_new_status_policy",
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
    "ND05_TASK_ID",
    "NotificationDeliveryPlanAuthority",
    "NotificationDeliveryChannelPlanStatus",
    "NotificationDeliveryPlanDecisionStatus",
    "NotificationDeliveryChannelPlanEntry",
    "NotificationDeliveryPlan",
    "NotificationDeliveryPlanDecision",
    "plan_notification_delivery",
    "ND06_TASK_ID",
    "NotificationAttemptAuthority",
    "NotificationAttemptLifecycleStatus",
    "NotificationAttemptPlanningStatus",
    "NotificationProviderOutcomeClass",
    "NotificationProviderOutcomeAcceptanceStatus",
    "NotificationAttempt",
    "NotificationAttemptPlanningDecision",
    "NotificationProviderOutcomeReference",
    "NotificationProviderOutcomeAcceptanceDecision",
    "plan_notification_attempt",
    "accept_notification_provider_outcome",
    "ND07_TASK_ID",
    "NotificationDeduplicationAuthority",
    "NotificationDeduplicationStage",
    "NotificationDeduplicationRecordState",
    "NotificationDeduplicationDecisionStatus",
    "NotificationDeduplicationRequest",
    "NotificationDeduplicationRecord",
    "NotificationDeduplicationDecision",
    "evaluate_notification_deduplication",
    "ND08_TASK_ID",
    "NotificationNoNewStatusAuthority",
    "NotificationNoNewMinimumFrequencyGateStatus",
    "NotificationNoNewStatusDecisionStatus",
    "NotificationNoNewStatusPolicyContext",
    "NotificationNoNewStatusPolicyDecision",
    "evaluate_no_new_status_policy",
)

EXPECTED_ENUM_VALUES: dict[type[Enum], tuple[str, ...]] = {
    NotificationNoNewStatusAuthority: ("NOTIFICATION_DELIVERY_SERVER",),
    NotificationNoNewMinimumFrequencyGateStatus: (
        "NOT_APPLICABLE",
        "NO_PRIOR_NOTIFICATION",
        "MINIMUM_FREQUENCY_ELAPSED",
        "MINIMUM_FREQUENCY_NOT_ELAPSED",
        "AMBIGUOUS",
    ),
    NotificationNoNewStatusDecisionStatus: (
        "PUSH_STATUS_ELIGIBLE",
        "READ_MODEL_ONLY_PREFERENCE_DISABLED",
        "READ_MODEL_ONLY_FREQUENCY_BELOW_MINIMUM",
        "READ_MODEL_ONLY_MINIMUM_FREQUENCY_NOT_ELAPSED",
        "READ_MODEL_ONLY_NO_ELIGIBLE_PUSH_CHANNEL",
        "BLOCKED_ELIGIBILITY",
        "BLOCKED_MINIMUM_FREQUENCY_AMBIGUOUS",
        "BLOCKED_CHANNEL_PLAN",
    ),
}

EXPECTED_DATACLASS_FIELDS: dict[type[object], tuple[str, ...]] = {
    NotificationNoNewStatusPolicyContext: (
        "account_id",
        "beacon_id",
        "last_successful_scan_reference_id",
        "no_new_status_fact_reference_id",
        "configured_scan_interval_reference_id",
        "status_preference_enabled",
        "configured_status_frequency_minutes",
        "last_no_new_status_notification_reference_id",
        "minimum_frequency_gate_status",
        "evidence_reference_ids",
    ),
    NotificationNoNewStatusPolicyDecision: (
        "decision_id",
        "authority",
        "eligibility_decision",
        "delivery_plan_decision",
        "context",
        "status",
        "status_read_model_eligible",
        "push_status_work_eligible",
        "delivery_attempt_authorized",
        "provider_mapping_authorized",
        "reason_codes",
        "evidence_reference_ids",
    ),
}

EXPECTED_FIELD_TYPES: dict[type[object], dict[str, object]] = {
    NotificationNoNewStatusPolicyContext: {
        "account_id": str,
        "beacon_id": str,
        "last_successful_scan_reference_id": str,
        "no_new_status_fact_reference_id": str,
        "configured_scan_interval_reference_id": str,
        "status_preference_enabled": bool,
        "configured_status_frequency_minutes": int | None,
        "last_no_new_status_notification_reference_id": str | None,
        "minimum_frequency_gate_status": NotificationNoNewMinimumFrequencyGateStatus,
        "evidence_reference_ids": tuple[str, ...],
    },
    NotificationNoNewStatusPolicyDecision: {
        "decision_id": str,
        "authority": NotificationNoNewStatusAuthority,
        "eligibility_decision": NotificationEligibilityDecision,
        "delivery_plan_decision": NotificationDeliveryPlanDecision | None,
        "context": NotificationNoNewStatusPolicyContext,
        "status": NotificationNoNewStatusDecisionStatus,
        "status_read_model_eligible": bool,
        "push_status_work_eligible": bool,
        "delivery_attempt_authorized": bool,
        "provider_mapping_authorized": bool,
        "reason_codes": tuple[str, ...],
        "evidence_reference_ids": tuple[str, ...],
    },
}


def _enum_values(enum_type: type[Enum]) -> tuple[str, ...]:
    members: list[Enum] = list(enum_type)
    return tuple(str(member.value) for member in members)


def _enum_names(enum_type: type[Enum]) -> tuple[str, ...]:
    members: list[Enum] = list(enum_type)
    return tuple(member.name for member in members)


def test_task_id_constant_and_package_exports_are_exact() -> None:
    assert ND08_TASK_ID == "ND-08-NO-NEW-STATUS-POLICY-SEMANTICS-20260716-012"
    assert type(notification_delivery_no_new_status.__all__) is tuple
    assert notification_delivery_no_new_status.__all__ == EXPECTED_MODULE_EXPORTS
    assert type(notification_delivery.__all__) is tuple
    assert notification_delivery.__all__ == EXPECTED_PACKAGE_EXPORTS
    assert len(notification_delivery_no_new_status.__all__) == len(
        set(notification_delivery_no_new_status.__all__)
    )
    assert len(notification_delivery.__all__) == len(set(notification_delivery.__all__))
    assert notification_delivery_no_new_status.ND08_TASK_ID is ND08_TASK_ID
    assert notification_delivery.ND08_TASK_ID is ND08_TASK_ID
    assert (
        notification_delivery_no_new_status.NotificationNoNewStatusAuthority
        is NotificationNoNewStatusAuthority
    )
    assert (
        notification_delivery_no_new_status.NotificationNoNewMinimumFrequencyGateStatus
        is NotificationNoNewMinimumFrequencyGateStatus
    )
    assert (
        notification_delivery_no_new_status.NotificationNoNewStatusDecisionStatus
        is NotificationNoNewStatusDecisionStatus
    )
    assert (
        notification_delivery_no_new_status.NotificationNoNewStatusPolicyContext
        is NotificationNoNewStatusPolicyContext
    )
    assert (
        notification_delivery_no_new_status.NotificationNoNewStatusPolicyDecision
        is NotificationNoNewStatusPolicyDecision
    )
    assert (
        notification_delivery_no_new_status.evaluate_no_new_status_policy
        is evaluate_no_new_status_policy
    )
    assert notification_delivery._no_new_status is notification_delivery_no_new_status
    assert "__getattr__" not in notification_delivery_no_new_status.__dict__
    assert "__getattr__" not in notification_delivery.__dict__


def test_enum_values_are_exact_and_have_no_extras() -> None:
    for enum_type, expected_values in EXPECTED_ENUM_VALUES.items():
        assert _enum_values(enum_type) == expected_values
        assert _enum_names(enum_type) == expected_values


def test_dataclass_field_order_and_slotting_are_exact() -> None:
    for dataclass_type, expected_fields in EXPECTED_DATACLASS_FIELDS.items():
        assert is_dataclass(dataclass_type)
        assert cast(Any, dataclass_type).__dataclass_params__.frozen is True
        assert cast(Any, dataclass_type).__slots__ == expected_fields
        assert tuple(field.name for field in fields(dataclass_type)) == expected_fields


def test_dataclass_field_types_are_exact() -> None:
    for dataclass_type, expected_types in EXPECTED_FIELD_TYPES.items():
        type_hints = get_type_hints(dataclass_type, include_extras=True)
        for field_name, expected_type in expected_types.items():
            assert type_hints[field_name] == expected_type


def test_public_function_signature_is_exact() -> None:
    signature = inspect.signature(evaluate_no_new_status_policy)
    assert tuple(signature.parameters) == (
        "decision_id",
        "eligibility_decision",
        "delivery_plan_decision",
        "context",
        "evidence_reference_ids",
    )
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for parameter in signature.parameters.values()
    )


def test_import_star_and_package_identity_bindings_are_exact() -> None:
    namespace: dict[str, object] = {}
    exec("from mayak.modules.notification_delivery.no_new_status import *", namespace)
    for name in EXPECTED_MODULE_EXPORTS:
        assert namespace[name] is getattr(notification_delivery_no_new_status, name)

    package_namespace: dict[str, object] = {}
    exec("from mayak.modules.notification_delivery import *", package_namespace)
    for name in EXPECTED_PACKAGE_EXPORTS:
        assert package_namespace[name] is getattr(notification_delivery, name)


def test_production_source_contains_task_id_exactly_once() -> None:
    source = Path("src/mayak/modules/notification_delivery/no_new_status.py").read_text()
    assert source.count(ND08_TASK_ID) == 1
