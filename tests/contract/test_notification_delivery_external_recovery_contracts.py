from __future__ import annotations

import inspect
from dataclasses import fields, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any, cast, get_type_hints

from mayak.modules import notification_delivery
from mayak.modules.notification_delivery import (
    external_recovery as notification_delivery_external_recovery,
)
from mayak.modules.notification_delivery.deduplication import NotificationDeduplicationDecision
from mayak.modules.notification_delivery.delivery_plan import NotificationDeliveryPlanDecision

EXPECTED_TASK_ID = "ND-09-EXTERNAL-RECOVERY-POLICY-SEMANTICS-20260716-015"

EXPECTED_MODULE_EXPORTS = (
    "ND09_TASK_ID",
    "NotificationExternalRecoveryAuthority",
    "NotificationExternalRecoveryEffectClass",
    "NotificationExternalProblemGateStatus",
    "NotificationExternalRecoveryDecisionStatus",
    "NotificationExternalRecoveryPolicyContext",
    "NotificationExternalRecoveryPolicyDecision",
    "evaluate_external_recovery_policy",
)

EXPECTED_PACKAGE_PREFIX = (
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
    notification_delivery_external_recovery.NotificationExternalRecoveryAuthority: (
        "NOTIFICATION_DELIVERY_SERVER",
    ),
    notification_delivery_external_recovery.NotificationExternalRecoveryEffectClass: (
        "AVITO_UNAVAILABLE_CONTINUING_SCAN",
        "RECOVERY_RESULT_WITH_NEW_LISTINGS",
        "RECOVERY_RESULT_NO_NEW_LISTINGS",
        "RECOVERY_RESULT_LOST_ANCHORS_RESTORED",
        "RECOVERY_BLOCKED_OR_AMBIGUOUS",
    ),
    notification_delivery_external_recovery.NotificationExternalProblemGateStatus: (
        "NOT_APPLICABLE",
        "PROBLEM_BEGAN",
        "MATERIAL_CHANGE",
        "SAME_PROBLEM_UNCHANGED",
        "AMBIGUOUS",
    ),
    notification_delivery_external_recovery.NotificationExternalRecoveryDecisionStatus: (
        "PUSH_WORK_ELIGIBLE",
        "READ_MODEL_ONLY_SAME_PROBLEM",
        "READ_MODEL_ONLY_REPLAY_TERMINAL",
        "READ_MODEL_ONLY_REPLAY_PENDING",
        "READ_MODEL_ONLY_NO_ELIGIBLE_PUSH_CHANNEL",
        "RECONCILIATION_REQUIRED",
        "BLOCKED_ELIGIBILITY",
        "BLOCKED_PROBLEM_GATE_AMBIGUOUS",
        "BLOCKED_IDEMPOTENCY",
        "BLOCKED_CHANNEL_PLAN",
        "BLOCKED_RECOVERY_ALREADY_CONSUMED",
    ),
}

EXPECTED_DATACLASS_FIELDS: dict[type[object], tuple[str, ...]] = {
    notification_delivery_external_recovery.NotificationExternalRecoveryPolicyContext: (
        "account_id",
        "beacon_id",
        "source_fact_reference_id",
        "external_problem_reference_id",
        "material_change_reference_id",
        "problem_gate_status",
        "recovery_obligation_reference_id",
        "recovery_result_already_consumed",
        "evidence_reference_ids",
    ),
    notification_delivery_external_recovery.NotificationExternalRecoveryPolicyDecision: (
        "decision_id",
        "authority",
        "eligibility_decision",
        "deduplication_decision",
        "delivery_plan_decision",
        "context",
        "effect_class",
        "status",
        "status_read_model_eligible",
        "push_work_eligible",
        "replayed",
        "reconciliation_required",
        "recovery_grace_applied",
        "delivery_attempt_authorized",
        "provider_mapping_authorized",
        "reason_codes",
        "evidence_reference_ids",
    ),
}

EXPECTED_FIELD_TYPES: dict[type[object], dict[str, object]] = {
    notification_delivery_external_recovery.NotificationExternalRecoveryPolicyContext: {
        "account_id": str,
        "beacon_id": str,
        "source_fact_reference_id": str,
        "external_problem_reference_id": str,
        "material_change_reference_id": str | None,
        "problem_gate_status": (
            notification_delivery_external_recovery.NotificationExternalProblemGateStatus
        ),
        "recovery_obligation_reference_id": str | None,
        "recovery_result_already_consumed": bool,
        "evidence_reference_ids": tuple[str, ...],
    },
    notification_delivery_external_recovery.NotificationExternalRecoveryPolicyDecision: {
        "decision_id": str,
        "authority": notification_delivery_external_recovery.NotificationExternalRecoveryAuthority,
        "eligibility_decision": notification_delivery.NotificationEligibilityDecision,
        "deduplication_decision": NotificationDeduplicationDecision | None,
        "delivery_plan_decision": NotificationDeliveryPlanDecision | None,
        "context": (
            notification_delivery_external_recovery.NotificationExternalRecoveryPolicyContext
        ),
        "effect_class": (
            notification_delivery_external_recovery.NotificationExternalRecoveryEffectClass
        ),
        "status": (
            notification_delivery_external_recovery.NotificationExternalRecoveryDecisionStatus
        ),
        "status_read_model_eligible": bool,
        "push_work_eligible": bool,
        "replayed": bool,
        "reconciliation_required": bool,
        "recovery_grace_applied": bool,
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
    assert notification_delivery_external_recovery.ND09_TASK_ID == EXPECTED_TASK_ID
    assert type(notification_delivery_external_recovery.__all__) is tuple
    assert notification_delivery_external_recovery.__all__ == EXPECTED_MODULE_EXPORTS
    assert type(notification_delivery.__all__) is tuple
    assert notification_delivery.__all__[: len(EXPECTED_PACKAGE_PREFIX)] == EXPECTED_PACKAGE_PREFIX
    assert (
        notification_delivery.__all__[
            len(EXPECTED_PACKAGE_PREFIX) : len(EXPECTED_PACKAGE_PREFIX)
            + len(EXPECTED_MODULE_EXPORTS)
        ]
        == EXPECTED_MODULE_EXPORTS
    )
    assert len(notification_delivery_external_recovery.__all__) == len(
        set(notification_delivery_external_recovery.__all__)
    )
    assert len(notification_delivery.__all__) == len(set(notification_delivery.__all__))
    assert (
        notification_delivery_external_recovery.ND09_TASK_ID is notification_delivery.ND09_TASK_ID
    )
    assert notification_delivery_external_recovery is notification_delivery._external_recovery
    assert notification_delivery._external_recovery is notification_delivery_external_recovery
    assert "__getattr__" not in notification_delivery_external_recovery.__dict__
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
    signature = inspect.signature(
        notification_delivery_external_recovery.evaluate_external_recovery_policy
    )
    assert tuple(signature.parameters) == (
        "decision_id",
        "eligibility_decision",
        "deduplication_decision",
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
    exec("from mayak.modules.notification_delivery.external_recovery import *", namespace)
    for name in EXPECTED_MODULE_EXPORTS:
        assert namespace[name] is getattr(notification_delivery_external_recovery, name)

    package_namespace: dict[str, object] = {}
    exec("from mayak.modules.notification_delivery import *", package_namespace)
    for name in EXPECTED_PACKAGE_PREFIX + EXPECTED_MODULE_EXPORTS:
        assert package_namespace[name] is getattr(notification_delivery, name)


def test_production_source_contains_task_id_exactly_once() -> None:
    source = Path("src/mayak/modules/notification_delivery/external_recovery.py").read_text()
    assert source.count(EXPECTED_TASK_ID) == 1


def test_package_exports_remain_append_friendly_after_nd09() -> None:
    assert notification_delivery.__all__[: len(EXPECTED_PACKAGE_PREFIX)] == EXPECTED_PACKAGE_PREFIX
    assert (
        notification_delivery.__all__[
            len(EXPECTED_PACKAGE_PREFIX) : len(EXPECTED_PACKAGE_PREFIX)
            + len(EXPECTED_MODULE_EXPORTS)
        ]
        == EXPECTED_MODULE_EXPORTS
    )
    assert len(notification_delivery.__all__) == len(set(notification_delivery.__all__))
