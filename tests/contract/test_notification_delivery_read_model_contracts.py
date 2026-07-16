# ruff: noqa: E501, F401, I001
from __future__ import annotations

import inspect
from dataclasses import fields, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any, cast, get_type_hints

from mayak.modules import notification_delivery
from mayak.modules.notification_delivery import read_model as notification_delivery_read_model
from mayak.modules.notification_delivery.read_model import (
    ND12_TASK_ID,
    NotificationDeliveryHistoryClassification,
    NotificationDeliveryHistoryEntry,
    NotificationDeliveryReadStatus,
    NotificationReadAudience,
    NotificationReadAuthorizationScope,
    NotificationReadModel,
    NotificationReadModelProjectionDecision,
    NotificationReadProjectionStatus,
    project_notification_read_model,
)

EXPECTED_TASK_ID = "MAYAK-ND-12-READ-MODEL-HISTORY-20260716-003"

EXPECTED_MODULE_EXPORTS = (
    "ND12_TASK_ID",
    "NotificationReadAudience",
    "NotificationDeliveryReadStatus",
    "NotificationDeliveryHistoryClassification",
    "NotificationReadProjectionStatus",
    "NotificationReadAuthorizationScope",
    "NotificationDeliveryHistoryEntry",
    "NotificationReadModel",
    "NotificationReadModelProjectionDecision",
    "project_notification_read_model",
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
    "ND12_TASK_ID",
    "NotificationReadAudience",
    "NotificationDeliveryReadStatus",
    "NotificationDeliveryHistoryClassification",
    "NotificationReadProjectionStatus",
    "NotificationReadAuthorizationScope",
    "NotificationDeliveryHistoryEntry",
    "NotificationReadModel",
    "NotificationReadModelProjectionDecision",
    "project_notification_read_model",
)

EXPECTED_PACKAGE_PREFIX = EXPECTED_PACKAGE_EXPORTS[: -len(EXPECTED_MODULE_EXPORTS)]

EXPECTED_ENUM_VALUES: dict[type[Enum], tuple[str, ...]] = {
    NotificationReadAudience: ("USER", "ADMIN", "SUPPORT"),
    NotificationDeliveryReadStatus: (
        "PLANNED",
        "REPLAYED",
        "SUPPRESSED",
        "BLOCKED",
        "DELIVERED",
        "FAILED",
        "RECONCILIATION_REQUIRED",
    ),
    NotificationDeliveryHistoryClassification: (
        "PLANNED",
        "REPLAYED",
        "SUPPRESSED",
        "BLOCKED",
        "DELIVERED",
        "FAILED",
        "RECONCILIATION_REQUIRED",
    ),
    NotificationReadProjectionStatus: ("PROJECTED", "RECONCILIATION_REQUIRED"),
}

EXPECTED_DATACLASS_FIELDS: dict[type[object], tuple[str, ...]] = {
    NotificationReadAuthorizationScope: (
        "scope_id",
        "audience",
        "authorized",
        "account_id",
        "beacon_scope_ids",
        "authorization_reference_id",
        "evidence_reference_ids",
        "freshness_reference_ids",
        "provenance_reference_ids",
    ),
    NotificationDeliveryHistoryEntry: (
        "history_entry_id",
        "batch_item_id",
        "account_id",
        "beacon_id",
        "source_decision_id",
        "outbox_item_id",
        "attempt_id",
        "channel_class",
        "delivery_status",
        "history_classification",
        "reconciliation_required",
        "retry_policy_required",
        "provider_safe_error_category",
        "safe_reason_codes",
        "safe_listing_reference_ids",
        "listing_count",
        "evidence_reference_ids",
        "freshness_reference_ids",
        "provenance_reference_ids",
        "audience",
        "mutation_authorized",
        "execution_authorized",
        "provider_mapping_authorized",
        "read_tracking_authorized",
        "click_tracking_authorized",
        "retention_authorized",
    ),
    NotificationReadModel: (
        "read_model_id",
        "audience",
        "account_id",
        "beacon_scope_ids",
        "batch_decision_id",
        "history_entries",
        "safe_listing_reference_ids",
        "listing_count",
        "history_entry_count",
        "listing_references_preserved",
        "per_item_outcomes_exposed",
        "execution_authorized",
        "provider_mapping_authorized",
        "mutation_authorized",
        "read_tracking_authorized",
        "click_tracking_authorized",
        "retention_authorized",
        "replay_visible",
        "failure_visible",
        "ambiguous_visible",
        "reconciliation_required",
        "freshness_reference_ids",
        "provenance_reference_ids",
        "evidence_reference_ids",
        "reason_codes",
    ),
    NotificationReadModelProjectionDecision: (
        "decision_id",
        "authorization_scope",
        "source_batch_decision",
        "read_model",
        "status",
        "listing_references_preserved",
        "per_item_outcomes_exposed",
        "execution_authorized",
        "provider_mapping_authorized",
        "mutation_authorized",
        "read_tracking_authorized",
        "click_tracking_authorized",
        "retention_authorized",
        "reason_codes",
        "evidence_reference_ids",
    ),
}

EXPECTED_FIELD_TYPES: dict[type[object], dict[str, object]] = {
    NotificationReadAuthorizationScope: {
        "scope_id": str,
        "audience": NotificationReadAudience,
        "authorized": bool,
        "account_id": str,
        "beacon_scope_ids": tuple[str, ...],
        "authorization_reference_id": str,
        "evidence_reference_ids": tuple[str, ...],
        "freshness_reference_ids": tuple[str, ...],
        "provenance_reference_ids": tuple[str, ...],
    },
    NotificationDeliveryHistoryEntry: {
        "history_entry_id": str,
        "batch_item_id": str,
        "account_id": str,
        "beacon_id": str | None,
        "source_decision_id": str,
        "outbox_item_id": str | None,
        "attempt_id": str | None,
        "channel_class": notification_delivery_read_model.NotificationChannelClass | None,
        "delivery_status": NotificationDeliveryReadStatus,
        "history_classification": NotificationDeliveryHistoryClassification,
        "reconciliation_required": bool,
        "retry_policy_required": bool,
        "provider_safe_error_category": notification_delivery_read_model.NotificationBatchSafeErrorCategory,
        "safe_reason_codes": tuple[str, ...],
        "safe_listing_reference_ids": tuple[str, ...],
        "listing_count": int,
        "evidence_reference_ids": tuple[str, ...],
        "freshness_reference_ids": tuple[str, ...],
        "provenance_reference_ids": tuple[str, ...],
        "audience": NotificationReadAudience,
        "mutation_authorized": bool,
        "execution_authorized": bool,
        "provider_mapping_authorized": bool,
        "read_tracking_authorized": bool,
        "click_tracking_authorized": bool,
        "retention_authorized": bool,
    },
    NotificationReadModel: {
        "read_model_id": str,
        "audience": NotificationReadAudience,
        "account_id": str,
        "beacon_scope_ids": tuple[str, ...],
        "batch_decision_id": str,
        "history_entries": tuple[NotificationDeliveryHistoryEntry, ...],
        "safe_listing_reference_ids": tuple[str, ...],
        "listing_count": int,
        "history_entry_count": int,
        "listing_references_preserved": bool,
        "per_item_outcomes_exposed": bool,
        "execution_authorized": bool,
        "provider_mapping_authorized": bool,
        "mutation_authorized": bool,
        "read_tracking_authorized": bool,
        "click_tracking_authorized": bool,
        "retention_authorized": bool,
        "replay_visible": bool,
        "failure_visible": bool,
        "ambiguous_visible": bool,
        "reconciliation_required": bool,
        "freshness_reference_ids": tuple[str, ...],
        "provenance_reference_ids": tuple[str, ...],
        "evidence_reference_ids": tuple[str, ...],
        "reason_codes": tuple[str, ...],
    },
    NotificationReadModelProjectionDecision: {
        "decision_id": str,
        "authorization_scope": NotificationReadAuthorizationScope,
        "source_batch_decision": notification_delivery_read_model.NotificationBatchDecision,
        "read_model": NotificationReadModel,
        "status": NotificationReadProjectionStatus,
        "listing_references_preserved": bool,
        "per_item_outcomes_exposed": bool,
        "execution_authorized": bool,
        "provider_mapping_authorized": bool,
        "mutation_authorized": bool,
        "read_tracking_authorized": bool,
        "click_tracking_authorized": bool,
        "retention_authorized": bool,
        "reason_codes": tuple[str, ...],
        "evidence_reference_ids": tuple[str, ...],
    },
}


def _enum_values(enum_type: type[Enum]) -> tuple[str, ...]:
    return tuple(member.value for member in enum_type)


def _enum_names(enum_type: type[Enum]) -> tuple[str, ...]:
    return tuple(member.name for member in enum_type)


def test_task_id_constant_and_package_exports_are_exact() -> None:
    assert ND12_TASK_ID == EXPECTED_TASK_ID
    assert type(notification_delivery_read_model.__all__) is tuple
    assert notification_delivery_read_model.__all__ == EXPECTED_MODULE_EXPORTS
    assert type(notification_delivery.__all__) is tuple
    assert (
        notification_delivery.__all__[: len(EXPECTED_PACKAGE_EXPORTS)] == EXPECTED_PACKAGE_EXPORTS
    )
    assert len(notification_delivery_read_model.__all__) == len(
        set(notification_delivery_read_model.__all__)
    )
    assert len(notification_delivery.__all__) == len(set(notification_delivery.__all__))
    assert notification_delivery_read_model.ND12_TASK_ID is ND12_TASK_ID
    assert notification_delivery.ND12_TASK_ID is ND12_TASK_ID
    assert notification_delivery.NotificationReadAudience is NotificationReadAudience
    assert notification_delivery.NotificationDeliveryReadStatus is NotificationDeliveryReadStatus
    assert (
        notification_delivery.NotificationDeliveryHistoryClassification
        is NotificationDeliveryHistoryClassification
    )
    assert (
        notification_delivery.NotificationReadProjectionStatus is NotificationReadProjectionStatus
    )
    assert (
        notification_delivery.NotificationReadAuthorizationScope
        is NotificationReadAuthorizationScope
    )
    assert (
        notification_delivery.NotificationDeliveryHistoryEntry is NotificationDeliveryHistoryEntry
    )
    assert notification_delivery.NotificationReadModel is NotificationReadModel
    assert (
        notification_delivery.NotificationReadModelProjectionDecision
        is NotificationReadModelProjectionDecision
    )
    assert notification_delivery.project_notification_read_model is project_notification_read_model
    assert notification_delivery.read_model is notification_delivery_read_model
    assert "__getattr__" not in notification_delivery_read_model.__dict__
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
    signature = inspect.signature(project_notification_read_model)
    assert tuple(signature.parameters) == (
        "decision_id",
        "authorization_scope",
        "source_batch_decision",
        "evidence_reference_ids",
    )
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for parameter in signature.parameters.values()
    )


def test_import_star_and_package_identity_bindings_are_exact() -> None:
    namespace: dict[str, object] = {}
    exec("from mayak.modules.notification_delivery.read_model import *", namespace)
    for name in EXPECTED_MODULE_EXPORTS:
        assert namespace[name] is getattr(notification_delivery_read_model, name)

    package_namespace: dict[str, object] = {}
    exec("from mayak.modules.notification_delivery import *", package_namespace)
    for name in EXPECTED_PACKAGE_EXPORTS:
        assert package_namespace[name] is getattr(notification_delivery, name)


def test_package_prefix_survives_append_only_exports() -> None:
    assert notification_delivery.__all__[: len(EXPECTED_PACKAGE_PREFIX)] == EXPECTED_PACKAGE_PREFIX


def test_production_source_contains_task_id_exactly_once() -> None:
    source = Path("src/mayak/modules/notification_delivery/read_model.py").read_text()
    assert source.count(EXPECTED_TASK_ID) == 1
