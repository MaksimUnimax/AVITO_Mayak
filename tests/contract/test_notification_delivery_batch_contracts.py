from __future__ import annotations

import inspect
from dataclasses import fields, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any, cast, get_type_hints

from mayak.modules import notification_delivery
from mayak.modules.notification_delivery import batch as notification_delivery_batch
from mayak.modules.notification_delivery.batch import (
    ND11_TASK_ID,
    NotificationBatchAuthority,
    NotificationBatchDecision,
    NotificationBatchDecisionStatus,
    NotificationBatchDisposition,
    NotificationBatchItemInput,
    NotificationBatchItemResult,
    NotificationBatchSafeErrorCategory,
    NotificationBatchStage,
    project_notification_batch_outcomes,
)

EXPECTED_TASK_ID = "ND-11-BATCH-PARTIAL-OUTCOME-SEMANTICS-20260716-019"

EXPECTED_MODULE_EXPORTS = (
    "ND11_TASK_ID",
    "NotificationBatchAuthority",
    "NotificationBatchStage",
    "NotificationBatchDisposition",
    "NotificationBatchSafeErrorCategory",
    "NotificationBatchDecisionStatus",
    "NotificationBatchItemInput",
    "NotificationBatchItemResult",
    "NotificationBatchDecision",
    "project_notification_batch_outcomes",
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
    "ND09_TASK_ID",
    "NotificationExternalRecoveryAuthority",
    "NotificationExternalRecoveryEffectClass",
    "NotificationExternalProblemGateStatus",
    "NotificationExternalRecoveryDecisionStatus",
    "NotificationExternalRecoveryPolicyContext",
    "NotificationExternalRecoveryPolicyDecision",
    "evaluate_external_recovery_policy",
    "ND10_TASK_ID",
    "NotificationListingCardAuthority",
    "NotificationListingCardReasonClass",
    "NotificationListingCardFieldClass",
    "NotificationListingCardValueClass",
    "NotificationListingCardProvenanceTier",
    "NotificationListingCardProjectionStatus",
    "NotificationListingCardFieldFact",
    "NotificationListingCardInput",
    "NotificationListingCard",
    "NotificationListingCardProjectionDecision",
    "project_notification_listing_cards",
)

EXPECTED_PACKAGE_EXPORTS = EXPECTED_PACKAGE_PREFIX + EXPECTED_MODULE_EXPORTS

EXPECTED_ENUM_VALUES: dict[type[Enum], tuple[str, ...]] = {
    NotificationBatchAuthority: ("NOTIFICATION_DELIVERY_SERVER",),
    NotificationBatchStage: (
        "DEDUPLICATION",
        "OUTBOX_CREATION",
        "DELIVERY_PLAN",
        "ATTEMPT_PLANNING",
        "PROVIDER_OUTCOME",
    ),
    NotificationBatchDisposition: (
        "CREATED",
        "REPLAYED",
        "SUPPRESSED",
        "BLOCKED",
        "DELIVERED",
        "FAILED",
        "RECONCILIATION_REQUIRED",
    ),
    NotificationBatchSafeErrorCategory: (
        "NONE",
        "ELIGIBILITY_BLOCKED",
        "IDEMPOTENCY_BLOCKED",
        "DELIVERY_PLAN_BLOCKED",
        "CHANNEL_PLAN_BLOCKED",
        "PROVIDER_FAILURE",
        "PROVIDER_OUTCOME_REJECTED",
        "AMBIGUOUS_RECONCILIATION",
    ),
    NotificationBatchDecisionStatus: (
        "ALL_ACCEPTED",
        "PARTIAL_OUTCOME",
        "ALL_BLOCKED_OR_FAILED",
        "RECONCILIATION_REQUIRED",
    ),
}

EXPECTED_DATACLASS_FIELDS: dict[type[object], tuple[str, ...]] = {
    NotificationBatchItemInput: (
        "batch_item_id",
        "source_decision",
        "outbox_item_context",
        "evidence_reference_ids",
    ),
    NotificationBatchItemResult: (
        "batch_item_id",
        "authority",
        "item_input",
        "stage",
        "source_decision_id",
        "account_id",
        "beacon_id",
        "channel_class",
        "outbox_item_id",
        "attempt_id",
        "safe_result_reference_id",
        "safe_listing_reference_ids",
        "disposition",
        "safe_error_category",
        "replayed",
        "delivery_accepted",
        "reconciliation_required",
        "retry_policy_required",
        "execution_authorized",
        "provider_mapping_authorized",
        "reason_codes",
        "evidence_reference_ids",
    ),
    NotificationBatchDecision: (
        "batch_id",
        "authority",
        "account_id",
        "item_inputs",
        "item_results",
        "status",
        "item_count",
        "accepted_count",
        "created_count",
        "replayed_count",
        "suppressed_count",
        "blocked_count",
        "delivered_count",
        "failed_count",
        "reconciliation_count",
        "retry_policy_required_count",
        "listing_references_preserved",
        "per_item_outcomes_exposed",
        "execution_authorized",
        "provider_mapping_authorized",
        "reason_codes",
        "evidence_reference_ids",
    ),
}

EXPECTED_FIELD_TYPES: dict[type[object], dict[str, object]] = {
    NotificationBatchItemInput: {
        "batch_item_id": str,
        "source_decision": (
            notification_delivery_batch.NotificationDeduplicationDecision
            | notification_delivery_batch.NotificationOutboxCreationDecision
            | notification_delivery_batch.NotificationDeliveryPlanDecision
            | notification_delivery_batch.NotificationAttemptPlanningDecision
            | notification_delivery_batch.NotificationProviderOutcomeAcceptanceDecision
        ),
        "outbox_item_context": notification_delivery_batch.NotificationOutboxItem | None,
        "evidence_reference_ids": tuple[str, ...],
    },
    NotificationBatchItemResult: {
        "batch_item_id": str,
        "authority": NotificationBatchAuthority,
        "item_input": NotificationBatchItemInput,
        "stage": NotificationBatchStage,
        "source_decision_id": str,
        "account_id": str,
        "beacon_id": str | None,
        "channel_class": notification_delivery_batch.NotificationChannelClass | None,
        "outbox_item_id": str | None,
        "attempt_id": str | None,
        "safe_result_reference_id": str,
        "safe_listing_reference_ids": tuple[str, ...],
        "disposition": NotificationBatchDisposition,
        "safe_error_category": NotificationBatchSafeErrorCategory,
        "replayed": bool,
        "delivery_accepted": bool,
        "reconciliation_required": bool,
        "retry_policy_required": bool,
        "execution_authorized": bool,
        "provider_mapping_authorized": bool,
        "reason_codes": tuple[str, ...],
        "evidence_reference_ids": tuple[str, ...],
    },
    NotificationBatchDecision: {
        "batch_id": str,
        "authority": NotificationBatchAuthority,
        "account_id": str,
        "item_inputs": tuple[NotificationBatchItemInput, ...],
        "item_results": tuple[NotificationBatchItemResult, ...],
        "status": NotificationBatchDecisionStatus,
        "item_count": int,
        "accepted_count": int,
        "created_count": int,
        "replayed_count": int,
        "suppressed_count": int,
        "blocked_count": int,
        "delivered_count": int,
        "failed_count": int,
        "reconciliation_count": int,
        "retry_policy_required_count": int,
        "listing_references_preserved": bool,
        "per_item_outcomes_exposed": bool,
        "execution_authorized": bool,
        "provider_mapping_authorized": bool,
        "reason_codes": tuple[str, ...],
        "evidence_reference_ids": tuple[str, ...],
    },
}


def _enum_values(enum_type: type[Enum]) -> tuple[str, ...]:
    return tuple(member.value for member in enum_type)


def _enum_names(enum_type: type[Enum]) -> tuple[str, ...]:
    return tuple(member.name for member in enum_type)


def test_task_id_constant_and_package_exports_are_exact() -> None:
    assert ND11_TASK_ID == EXPECTED_TASK_ID
    assert type(notification_delivery_batch.__all__) is tuple
    assert notification_delivery_batch.__all__ == EXPECTED_MODULE_EXPORTS
    assert type(notification_delivery.__all__) is tuple
    assert notification_delivery.__all__ == EXPECTED_PACKAGE_EXPORTS
    assert len(notification_delivery_batch.__all__) == len(set(notification_delivery_batch.__all__))
    assert len(notification_delivery.__all__) == len(set(notification_delivery.__all__))
    assert notification_delivery_batch.ND11_TASK_ID is ND11_TASK_ID
    assert notification_delivery.ND11_TASK_ID is ND11_TASK_ID
    assert notification_delivery._batch is notification_delivery_batch
    assert "__getattr__" not in notification_delivery_batch.__dict__
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
    signature = inspect.signature(project_notification_batch_outcomes)
    assert tuple(signature.parameters) == (
        "batch_id",
        "item_inputs",
        "evidence_reference_ids",
    )
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for parameter in signature.parameters.values()
    )


def test_import_star_and_package_identity_bindings_are_exact() -> None:
    namespace: dict[str, object] = {}
    exec("from mayak.modules.notification_delivery.batch import *", namespace)
    for name in EXPECTED_MODULE_EXPORTS:
        assert namespace[name] is getattr(notification_delivery_batch, name)

    package_namespace: dict[str, object] = {}
    exec("from mayak.modules.notification_delivery import *", package_namespace)
    for name in EXPECTED_PACKAGE_EXPORTS:
        assert package_namespace[name] is getattr(notification_delivery, name)


def test_production_source_contains_task_id_exactly_once() -> None:
    source = Path("src/mayak/modules/notification_delivery/batch.py").read_text()
    assert source.count(EXPECTED_TASK_ID) == 1


def test_package_exports_append_nd11_after_nd10() -> None:
    nd10_start = len(EXPECTED_PACKAGE_PREFIX)
    assert notification_delivery.__all__[:nd10_start] == EXPECTED_PACKAGE_PREFIX
    assert (
        notification_delivery.__all__[nd10_start : nd10_start + len(EXPECTED_MODULE_EXPORTS)]
        == EXPECTED_MODULE_EXPORTS
    )
    assert notification_delivery.__all__[nd10_start + len(EXPECTED_MODULE_EXPORTS) :] == ()
