from __future__ import annotations

import inspect
from dataclasses import fields, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any, cast, get_type_hints

from mayak.contracts.idempotency import IdempotencyDecision
from mayak.modules import notification_delivery
from mayak.modules.notification_delivery import deduplication as notification_delivery_deduplication
from mayak.modules.notification_delivery.deduplication import (
    ND07_TASK_ID,
    NotificationDeduplicationAuthority,
    NotificationDeduplicationDecision,
    NotificationDeduplicationDecisionStatus,
    NotificationDeduplicationRecord,
    NotificationDeduplicationRecordState,
    NotificationDeduplicationRequest,
    NotificationDeduplicationStage,
    evaluate_notification_deduplication,
)
from mayak.modules.notification_delivery.eligibility import NotificationChannelClass
from mayak.modules.notification_delivery.source_intake import NotificationSourceFamily
from mayak.platform.idempotency import (
    IdempotencyFingerprint as PlatformIdempotencyFingerprint,
)
from mayak.platform.idempotency import IdempotencyKey as PlatformIdempotencyKey
from mayak.platform.idempotency import IdempotencyScope as PlatformIdempotencyScope

EXPECTED_MODULE_EXPORTS = (
    "ND07_TASK_ID",
    "NotificationDeduplicationAuthority",
    "NotificationDeduplicationStage",
    "NotificationDeduplicationRecordState",
    "NotificationDeduplicationDecisionStatus",
    "NotificationDeduplicationRequest",
    "NotificationDeduplicationRecord",
    "NotificationDeduplicationDecision",
    "evaluate_notification_deduplication",
)

EXPECTED_PACKAGE_EXPORT_PREFIX = (
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
)

EXPECTED_ENUM_VALUES: dict[type[Enum], tuple[str, ...]] = {
    NotificationDeduplicationAuthority: ("NOTIFICATION_DELIVERY_SERVER",),
    NotificationDeduplicationStage: (
        "SOURCE_INTAKE",
        "OUTBOX_CREATION",
        "ATTEMPT_CREATION",
        "PROVIDER_OUTCOME_RECORDING",
    ),
    NotificationDeduplicationRecordState: ("PENDING", "TERMINAL", "AMBIGUOUS"),
    NotificationDeduplicationDecisionStatus: (
        "NEW_EFFECT",
        "REPLAY_TERMINAL",
        "REPLAY_PENDING",
        "RECONCILIATION_REQUIRED",
        "IDEMPOTENCY_MISMATCH",
        "MISSING_REQUIRED_IDEMPOTENCY",
    ),
}

EXPECTED_DATACLASS_FIELDS: dict[type[object], tuple[str, ...]] = {
    NotificationDeduplicationRequest: (
        "stage",
        "source_family",
        "account_id",
        "beacon_id",
        "channel_class",
        "semantic_effect_reference_id",
        "idempotency_key",
        "idempotency_fingerprint",
        "idempotency_scope",
        "proposed_record_state",
        "proposed_result_reference_id",
        "correlation_id",
        "causation_id",
        "evidence_reference_ids",
    ),
    NotificationDeduplicationRecord: (
        "record_id",
        "authority",
        "stage",
        "source_family",
        "account_id",
        "beacon_id",
        "channel_class",
        "semantic_effect_reference_id",
        "idempotency_key",
        "idempotency_fingerprint",
        "idempotency_scope",
        "record_state",
        "protected_result_reference_id",
        "correlation_id",
        "causation_id",
        "reason_codes",
        "evidence_reference_ids",
    ),
    NotificationDeduplicationDecision: (
        "decision_id",
        "authority",
        "request",
        "existing_record",
        "status",
        "resulting_record",
        "effect_authorized",
        "replayed",
        "reconciliation_required",
        "idempotency_decision",
        "reason_codes",
        "evidence_reference_ids",
    ),
}

EXPECTED_FIELD_TYPES: dict[type[object], dict[str, object]] = {
    NotificationDeduplicationRequest: {
        "stage": NotificationDeduplicationStage,
        "source_family": NotificationSourceFamily,
        "account_id": str,
        "beacon_id": str | None,
        "channel_class": NotificationChannelClass | None,
        "semantic_effect_reference_id": str,
        "idempotency_key": PlatformIdempotencyKey | None,
        "idempotency_fingerprint": PlatformIdempotencyFingerprint | None,
        "idempotency_scope": PlatformIdempotencyScope | None,
        "proposed_record_state": NotificationDeduplicationRecordState,
        "proposed_result_reference_id": str,
        "correlation_id": str,
        "causation_id": str,
        "evidence_reference_ids": tuple[str, ...],
    },
    NotificationDeduplicationRecord: {
        "record_id": str,
        "authority": NotificationDeduplicationAuthority,
        "stage": NotificationDeduplicationStage,
        "source_family": NotificationSourceFamily,
        "account_id": str,
        "beacon_id": str | None,
        "channel_class": NotificationChannelClass | None,
        "semantic_effect_reference_id": str,
        "idempotency_key": PlatformIdempotencyKey,
        "idempotency_fingerprint": PlatformIdempotencyFingerprint,
        "idempotency_scope": PlatformIdempotencyScope,
        "record_state": NotificationDeduplicationRecordState,
        "protected_result_reference_id": str,
        "correlation_id": str,
        "causation_id": str,
        "reason_codes": tuple[str, ...],
        "evidence_reference_ids": tuple[str, ...],
    },
    NotificationDeduplicationDecision: {
        "decision_id": str,
        "authority": NotificationDeduplicationAuthority,
        "request": NotificationDeduplicationRequest,
        "existing_record": NotificationDeduplicationRecord | None,
        "status": NotificationDeduplicationDecisionStatus,
        "resulting_record": NotificationDeduplicationRecord | None,
        "effect_authorized": bool,
        "replayed": bool,
        "reconciliation_required": bool,
        "idempotency_decision": IdempotencyDecision | None,
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
    assert ND07_TASK_ID == "ND-07-IDEMPOTENCY-DEDUP-REPLAY-SEMANTICS-20260716-010"
    assert type(notification_delivery_deduplication.__all__) is tuple
    assert notification_delivery_deduplication.__all__ == EXPECTED_MODULE_EXPORTS
    assert (
        notification_delivery.__all__[: len(EXPECTED_PACKAGE_EXPORT_PREFIX)]
        == EXPECTED_PACKAGE_EXPORT_PREFIX
    )
    assert notification_delivery.__all__[len(EXPECTED_PACKAGE_EXPORT_PREFIX) :] == (
        EXPECTED_MODULE_EXPORTS
    )
    assert len(notification_delivery_deduplication.__all__) == len(
        set(notification_delivery_deduplication.__all__)
    )
    assert len(notification_delivery.__all__) == len(set(notification_delivery.__all__))
    assert notification_delivery_deduplication.ND07_TASK_ID is ND07_TASK_ID
    assert notification_delivery.ND07_TASK_ID is ND07_TASK_ID
    assert (
        notification_delivery.NotificationDeduplicationAuthority
        is NotificationDeduplicationAuthority
    )
    assert notification_delivery.NotificationDeduplicationStage is NotificationDeduplicationStage
    assert (
        notification_delivery.NotificationDeduplicationRecordState
        is NotificationDeduplicationRecordState
    )
    assert (
        notification_delivery.NotificationDeduplicationDecisionStatus
        is NotificationDeduplicationDecisionStatus
    )
    assert (
        notification_delivery.NotificationDeduplicationRequest
        is NotificationDeduplicationRequest
    )
    assert notification_delivery.NotificationDeduplicationRecord is NotificationDeduplicationRecord
    assert (
        notification_delivery.NotificationDeduplicationDecision
        is NotificationDeduplicationDecision
    )
    assert (
        notification_delivery.evaluate_notification_deduplication
        is evaluate_notification_deduplication
    )
    assert "__getattr__" not in notification_delivery_deduplication.__dict__
    assert "__getattr__" not in notification_delivery.__dict__
    assert "_deduplication" in notification_delivery.__dict__


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
    signature = inspect.signature(evaluate_notification_deduplication)
    assert tuple(signature.parameters) == (
        "decision_id",
        "record_id",
        "request",
        "existing_record",
        "evidence_reference_ids",
    )
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for parameter in signature.parameters.values()
    )


def test_import_star_and_package_identity_bindings_are_exact() -> None:
    namespace: dict[str, object] = {}
    exec("from mayak.modules.notification_delivery.deduplication import *", namespace)
    for name in EXPECTED_MODULE_EXPORTS:
        assert namespace[name] is getattr(notification_delivery_deduplication, name)

    package_namespace: dict[str, object] = {}
    exec("from mayak.modules.notification_delivery import *", package_namespace)
    for name in EXPECTED_PACKAGE_EXPORT_PREFIX + EXPECTED_MODULE_EXPORTS:
        assert package_namespace[name] is getattr(notification_delivery, name)


def test_production_source_contains_task_id_exactly_once() -> None:
    source = Path("src/mayak/modules/notification_delivery/deduplication.py").read_text()
    assert source.count(ND07_TASK_ID) == 1
