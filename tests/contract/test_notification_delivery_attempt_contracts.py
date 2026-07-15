from __future__ import annotations

import inspect
from dataclasses import fields, is_dataclass
from enum import Enum, EnumMeta
from pathlib import Path
from typing import Any, cast, get_type_hints

from mayak.modules import notification_delivery
from mayak.modules.notification_delivery import attempt as notification_delivery_attempt
from mayak.modules.notification_delivery.attempt import (
    ND06_TASK_ID,
    NotificationAttempt,
    NotificationAttemptAuthority,
    NotificationAttemptLifecycleStatus,
    NotificationAttemptPlanningDecision,
    NotificationAttemptPlanningStatus,
    NotificationProviderOutcomeAcceptanceDecision,
    NotificationProviderOutcomeAcceptanceStatus,
    NotificationProviderOutcomeClass,
    NotificationProviderOutcomeReference,
    accept_notification_provider_outcome,
    plan_notification_attempt,
)
from mayak.modules.notification_delivery.delivery_plan import NotificationDeliveryPlanDecision
from mayak.modules.notification_delivery.eligibility import NotificationChannelClass
from mayak.platform.idempotency import IdempotencyFingerprint as PlatformIdempotencyFingerprint
from mayak.platform.idempotency import IdempotencyKey as PlatformIdempotencyKey
from mayak.platform.idempotency import IdempotencyScope as PlatformIdempotencyScope

EXPECTED_MODULE_EXPORTS = (
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
    *EXPECTED_MODULE_EXPORTS,
)

EXPECTED_DATACLASS_FIELDS: dict[type[object], tuple[str, ...]] = {
    NotificationAttempt: (
        "attempt_id",
        "authority",
        "delivery_plan_id",
        "outbox_item_id",
        "account_id",
        "beacon_id",
        "channel_class",
        "target_reference_id",
        "lifecycle_status",
        "idempotency_key",
        "idempotency_fingerprint",
        "idempotency_scope",
        "provider_outcome_reference_id",
        "provider_outcome_class",
        "adapter_contract",
        "adapter_contract_version",
        "provider_safe_delivery_reference",
        "egress_correlation_reference",
        "provider_reason_codes",
        "failure_policy_reference",
        "reconciliation_required",
        "delivery_accepted",
        "retry_authorized",
        "dispatch_effect_authorized",
        "provider_mapping_authorized",
        "correlation_id",
        "causation_id",
        "reason_codes",
        "evidence_reference_ids",
    ),
    NotificationAttemptPlanningDecision: (
        "decision_id",
        "authority",
        "delivery_plan_decision",
        "channel_class",
        "status",
        "attempt",
        "attempt_created",
        "dispatch_effect_authorized",
        "provider_mapping_authorized",
        "reason_codes",
        "evidence_reference_ids",
    ),
    NotificationProviderOutcomeReference: (
        "outcome_reference_id",
        "adapter_contract",
        "adapter_contract_version",
        "attempt_id",
        "channel_class",
        "target_reference_id",
        "outcome_class",
        "adapter_outcome_committed",
        "provider_safe_delivery_reference",
        "egress_correlation_reference",
        "contains_raw_provider_payload",
        "identity_ambiguous",
        "correlation_id",
        "causation_id",
        "reason_codes",
        "evidence_reference_ids",
    ),
    NotificationProviderOutcomeAcceptanceDecision: (
        "decision_id",
        "authority",
        "previous_attempt",
        "provider_outcome",
        "status",
        "resulting_attempt",
        "outcome_accepted",
        "replayed",
        "delivery_accepted",
        "reconciliation_required",
        "retry_authorized",
        "dispatch_effect_authorized",
        "provider_mapping_authorized",
        "reason_codes",
        "evidence_reference_ids",
    ),
}

EXPECTED_FIELD_TYPES: dict[type[object], dict[str, object]] = {
    NotificationAttempt: {
        "attempt_id": str,
        "authority": NotificationAttemptAuthority,
        "delivery_plan_id": str,
        "outbox_item_id": str,
        "account_id": str,
        "beacon_id": str | None,
        "channel_class": NotificationChannelClass,
        "target_reference_id": str,
        "lifecycle_status": NotificationAttemptLifecycleStatus,
        "idempotency_key": PlatformIdempotencyKey,
        "idempotency_fingerprint": PlatformIdempotencyFingerprint,
        "idempotency_scope": PlatformIdempotencyScope,
        "provider_outcome_reference_id": str | None,
        "provider_outcome_class": NotificationProviderOutcomeClass | None,
        "adapter_contract": str | None,
        "adapter_contract_version": str | None,
        "provider_safe_delivery_reference": str | None,
        "egress_correlation_reference": str | None,
        "provider_reason_codes": tuple[str, ...],
        "failure_policy_reference": str | None,
        "reconciliation_required": bool,
        "delivery_accepted": bool,
        "retry_authorized": bool,
        "dispatch_effect_authorized": bool,
        "provider_mapping_authorized": bool,
        "correlation_id": str,
        "causation_id": str,
        "reason_codes": tuple[str, ...],
        "evidence_reference_ids": tuple[str, ...],
    },
    NotificationAttemptPlanningDecision: {
        "decision_id": str,
        "authority": NotificationAttemptAuthority,
        "delivery_plan_decision": NotificationDeliveryPlanDecision,
        "channel_class": NotificationChannelClass,
        "status": NotificationAttemptPlanningStatus,
        "attempt": NotificationAttempt | None,
        "attempt_created": bool,
        "dispatch_effect_authorized": bool,
        "provider_mapping_authorized": bool,
        "reason_codes": tuple[str, ...],
        "evidence_reference_ids": tuple[str, ...],
    },
    NotificationProviderOutcomeReference: {
        "outcome_reference_id": str,
        "adapter_contract": str,
        "adapter_contract_version": str,
        "attempt_id": str,
        "channel_class": NotificationChannelClass,
        "target_reference_id": str,
        "outcome_class": NotificationProviderOutcomeClass,
        "adapter_outcome_committed": bool,
        "provider_safe_delivery_reference": str | None,
        "egress_correlation_reference": str | None,
        "contains_raw_provider_payload": bool,
        "identity_ambiguous": bool,
        "correlation_id": str,
        "causation_id": str,
        "reason_codes": tuple[str, ...],
        "evidence_reference_ids": tuple[str, ...],
    },
    NotificationProviderOutcomeAcceptanceDecision: {
        "decision_id": str,
        "authority": NotificationAttemptAuthority,
        "previous_attempt": NotificationAttempt,
        "provider_outcome": NotificationProviderOutcomeReference,
        "status": NotificationProviderOutcomeAcceptanceStatus,
        "resulting_attempt": NotificationAttempt | None,
        "outcome_accepted": bool,
        "replayed": bool,
        "delivery_accepted": bool,
        "reconciliation_required": bool,
        "retry_authorized": bool,
        "dispatch_effect_authorized": bool,
        "provider_mapping_authorized": bool,
        "reason_codes": tuple[str, ...],
        "evidence_reference_ids": tuple[str, ...],
    },
}

EXPECTED_ENUM_VALUES = {
    NotificationAttemptAuthority: ("NOTIFICATION_DELIVERY_SERVER",),
    NotificationAttemptLifecycleStatus: (
        "NOT_ATTEMPTED",
        "ATTEMPT_PLANNED",
        "ATTEMPT_IN_PROGRESS",
        "DISPATCH_AMBIGUOUS",
        "PROVIDER_ACCEPTED",
        "PROVIDER_REJECTED",
        "PROVIDER_UNAVAILABLE",
        "RATE_OR_ACCESS_RESTRICTED",
        "MALFORMED_OR_UNUSABLE_PROVIDER_RESPONSE",
        "DELIVERY_FAILURE",
        "DELIVERY_AMBIGUOUS",
        "SUPPRESSED_OR_CANCELLED",
        "TARGET_UNAVAILABLE_OR_UNVERIFIED",
        "RECONCILIATION_REQUIRED",
        "DELIVERED_ACCEPTED",
        "FAILED_RETRYABLE_AFTER_POLICY",
        "FAILED_NON_RETRYABLE",
    ),
    NotificationAttemptPlanningStatus: (
        "PLANNED",
        "BLOCKED_DELIVERY_PLAN",
        "BLOCKED_CHANNEL_PLAN",
    ),
    NotificationProviderOutcomeClass: (
        "DISPATCH_AMBIGUOUS",
        "PROVIDER_ACCEPTED",
        "PROVIDER_REJECTED",
        "PROVIDER_UNAVAILABLE",
        "RATE_OR_ACCESS_RESTRICTED",
        "MALFORMED_OR_UNUSABLE_PROVIDER_RESPONSE",
        "DELIVERY_FAILURE",
        "DELIVERY_AMBIGUOUS",
        "SUPPRESSED_OR_CANCELLED",
        "TARGET_UNAVAILABLE_OR_UNVERIFIED",
    ),
    NotificationProviderOutcomeAcceptanceStatus: (
        "ACCEPTED_DELIVERED",
        "ACCEPTED_FAILURE",
        "ACCEPTED_AMBIGUOUS",
        "REPLAYED",
        "REJECTED_UNCOMMITTED",
        "REJECTED_UNSAFE_PAYLOAD",
        "REJECTED_IDENTITY_AMBIGUOUS",
        "REJECTED_SCOPE_MISMATCH",
        "REJECTED_STATE_MISMATCH",
    ),
}


def _enum_values(enum_type: EnumMeta) -> tuple[str, ...]:
    members: list[Enum] = list(enum_type)
    return tuple(str(member.value) for member in members)


def _enum_names(enum_type: EnumMeta) -> tuple[str, ...]:
    members: list[Enum] = list(enum_type)
    return tuple(member.name for member in members)


def test_task_id_constant_and_package_exports_are_exact() -> None:
    assert ND06_TASK_ID == "ND-06-ATTEMPT-OUTCOME-SEMANTICS-20260715-008"
    assert type(notification_delivery_attempt.__all__) is tuple
    assert notification_delivery_attempt.__all__ == EXPECTED_MODULE_EXPORTS
    assert (
        notification_delivery.__all__[: len(EXPECTED_PACKAGE_EXPORTS)] == EXPECTED_PACKAGE_EXPORTS
    )
    assert notification_delivery.__all__[-len(EXPECTED_MODULE_EXPORTS) :] == EXPECTED_MODULE_EXPORTS
    assert len(notification_delivery.__all__) == len(set(notification_delivery.__all__))
    assert notification_delivery_attempt.ND06_TASK_ID is ND06_TASK_ID
    assert notification_delivery.ND06_TASK_ID is ND06_TASK_ID
    assert notification_delivery.NotificationAttemptAuthority is NotificationAttemptAuthority
    assert (
        notification_delivery.NotificationAttemptLifecycleStatus
        is NotificationAttemptLifecycleStatus
    )
    assert (
        notification_delivery.NotificationAttemptPlanningStatus is NotificationAttemptPlanningStatus
    )
    assert (
        notification_delivery.NotificationProviderOutcomeClass is NotificationProviderOutcomeClass
    )
    assert (
        notification_delivery.NotificationProviderOutcomeAcceptanceStatus
        is NotificationProviderOutcomeAcceptanceStatus
    )
    assert notification_delivery.NotificationAttempt is NotificationAttempt
    assert (
        notification_delivery.NotificationAttemptPlanningDecision
        is NotificationAttemptPlanningDecision
    )
    assert (
        notification_delivery.NotificationProviderOutcomeReference
        is NotificationProviderOutcomeReference
    )
    assert (
        notification_delivery.NotificationProviderOutcomeAcceptanceDecision
        is NotificationProviderOutcomeAcceptanceDecision
    )
    assert notification_delivery.plan_notification_attempt is plan_notification_attempt
    assert (
        notification_delivery.accept_notification_provider_outcome
        is accept_notification_provider_outcome
    )
    assert "__getattr__" not in notification_delivery.__dict__
    assert "_attempt" in notification_delivery.__dict__

    namespace: dict[str, object] = {}
    exec("from mayak.modules.notification_delivery.attempt import *", namespace)
    assert all(name in namespace for name in notification_delivery_attempt.__all__)
    assert (
        tuple(name for name in namespace if not name.startswith("__"))
        == notification_delivery_attempt.__all__
    )


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


def test_public_function_signatures_are_exact() -> None:
    plan_signature = inspect.signature(plan_notification_attempt)
    assert tuple(plan_signature.parameters) == (
        "decision_id",
        "attempt_id",
        "delivery_plan_decision",
        "channel_class",
        "idempotency_key",
        "idempotency_fingerprint",
        "idempotency_scope",
        "evidence_reference_ids",
    )

    accept_signature = inspect.signature(accept_notification_provider_outcome)
    assert tuple(accept_signature.parameters) == (
        "decision_id",
        "attempt",
        "provider_outcome",
        "evidence_reference_ids",
    )


def test_import_star_and_package_identity_bindings_are_exact() -> None:
    namespace: dict[str, object] = {}
    exec("from mayak.modules.notification_delivery import *", namespace)
    for name in EXPECTED_MODULE_EXPORTS:
        assert namespace[name] is getattr(notification_delivery, name)

    before = dict(notification_delivery.__dict__)
    import mayak.modules.notification_delivery as second_import

    after = dict(notification_delivery.__dict__)
    assert before.keys() == after.keys()
    assert second_import is notification_delivery


def test_production_source_contains_task_id_exactly_once() -> None:
    source = Path("src/mayak/modules/notification_delivery/attempt.py").read_text()
    assert source.count(ND06_TASK_ID) == 1
