from __future__ import annotations

import inspect
import re
from dataclasses import fields, is_dataclass
from enum import Enum, EnumMeta
from pathlib import Path
from typing import get_type_hints

from mayak.contracts.idempotency import IdempotencyDecision
from mayak.modules import notification_delivery
from mayak.modules.notification_delivery import outbox
from mayak.modules.notification_delivery.eligibility import (
    NotificationChannelClass,
    NotificationEligibilityDecision,
)
from mayak.modules.notification_delivery.source_intake import (
    NotificationSourceFamily,
    NotificationSourceProducer,
)
from mayak.platform.idempotency import IdempotencyFingerprint, IdempotencyKey, IdempotencyScope

EXPECTED_ND03_PACKAGE_EXPORTS = (
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
)

EXPECTED_OUTBOX_EXPORTS = (
    "ND04_TASK_ID",
    "NotificationOutboxAuthority",
    "NotificationOutboxLifecycleStatus",
    "NotificationOutboxCreationStatus",
    "NotificationOutboxChannelIntent",
    "NotificationOutboxItem",
    "NotificationOutboxCreationDecision",
    "create_notification_outbox_item",
)

EXPECTED_PACKAGE_EXPORTS = EXPECTED_ND03_PACKAGE_EXPORTS + EXPECTED_OUTBOX_EXPORTS

EXPECTED_ENUM_VALUES = {
    outbox.NotificationOutboxAuthority: ("NOTIFICATION_DELIVERY_SERVER",),
    outbox.NotificationOutboxLifecycleStatus: ("PLANNED",),
    outbox.NotificationOutboxCreationStatus: (
        "CREATED",
        "REPLAYED",
        "BLOCKED_ELIGIBILITY",
        "IDEMPOTENCY_MISMATCH",
    ),
}

EXPECTED_DATACLASS_FIELDS = {
    outbox.NotificationOutboxChannelIntent: (
        "channel_class",
        "target_reference_id",
        "evidence_reference_ids",
    ),
    outbox.NotificationOutboxItem: (
        "outbox_item_id",
        "authority",
        "outbox_contract",
        "outbox_contract_version",
        "eligibility_decision_id",
        "source_event_id",
        "source_fact_id",
        "source_commit_reference",
        "source_producer",
        "source_contract",
        "source_contract_version",
        "account_id",
        "beacon_id",
        "scan_run_id",
        "event_reason",
        "listing_count",
        "safe_listing_reference_ids",
        "channel_intents",
        "idempotency_key",
        "idempotency_fingerprint",
        "idempotency_scope",
        "lifecycle_status",
        "correlation_id",
        "causation_id",
        "evidence_reference_ids",
    ),
    outbox.NotificationOutboxCreationDecision: (
        "decision_id",
        "authority",
        "eligibility_decision",
        "status",
        "outbox_item",
        "outbox_item_created",
        "replayed",
        "idempotency_decision",
        "delivery_attempt_authorized",
        "reason_codes",
        "evidence_reference_ids",
    ),
}

EXPECTED_FIELD_TYPES: dict[type[object], dict[str, object]] = {
    outbox.NotificationOutboxChannelIntent: {
        "channel_class": NotificationChannelClass,
        "target_reference_id": str,
        "evidence_reference_ids": tuple[str, ...],
    },
    outbox.NotificationOutboxItem: {
        "outbox_item_id": str,
        "authority": outbox.NotificationOutboxAuthority,
        "outbox_contract": str,
        "outbox_contract_version": str,
        "eligibility_decision_id": str,
        "source_event_id": str,
        "source_fact_id": str,
        "source_commit_reference": str,
        "source_producer": NotificationSourceProducer,
        "source_contract": str,
        "source_contract_version": str,
        "account_id": str,
        "beacon_id": str | None,
        "scan_run_id": str | None,
        "event_reason": NotificationSourceFamily,
        "listing_count": int,
        "safe_listing_reference_ids": tuple[str, ...],
        "channel_intents": tuple[outbox.NotificationOutboxChannelIntent, ...],
        "idempotency_key": IdempotencyKey,
        "idempotency_fingerprint": IdempotencyFingerprint,
        "idempotency_scope": IdempotencyScope,
        "lifecycle_status": outbox.NotificationOutboxLifecycleStatus,
        "correlation_id": str,
        "causation_id": str,
        "evidence_reference_ids": tuple[str, ...],
    },
    outbox.NotificationOutboxCreationDecision: {
        "decision_id": str,
        "authority": outbox.NotificationOutboxAuthority,
        "eligibility_decision": NotificationEligibilityDecision,
        "status": outbox.NotificationOutboxCreationStatus,
        "outbox_item": outbox.NotificationOutboxItem | None,
        "outbox_item_created": bool,
        "replayed": bool,
        "idempotency_decision": IdempotencyDecision | None,
        "delivery_attempt_authorized": bool,
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
    "attempt_record",
    "attempts",
    "retry_backoff",
    "reconciliation_record",
    "provider_payload",
    "raw_payload",
    "message_template",
    "template",
    "cookie",
    "token",
    "secret",
    "credential",
}

EXPECTED_OUTBOX_REASON_CODES = {
    "outbox-created",
    "outbox-replayed",
    "outbox-eligibility-blocked",
    "outbox-idempotency-fingerprint-mismatch",
    "outbox-idempotency-semantic-mismatch",
}


def _enum_values(enum_type: EnumMeta) -> tuple[str, ...]:
    members: list[Enum] = list(enum_type)
    values: list[str] = []
    for member in members:
        values.append(str(member.value))
    return tuple(values)


def _enum_names(enum_type: EnumMeta) -> tuple[str, ...]:
    members: list[Enum] = list(enum_type)
    names: list[str] = []
    for member in members:
        names.append(member.name)
    return tuple(names)


def test_task_id_constant_and_package_exports_are_exact() -> None:
    assert outbox.ND04_TASK_ID == "ND-04-GENERIC-OUTBOX-SEMANTICS-20260715-006"
    assert type(outbox.__all__) is tuple
    assert outbox.__all__ == EXPECTED_OUTBOX_EXPORTS
    assert notification_delivery.__all__ == EXPECTED_PACKAGE_EXPORTS
    assert notification_delivery.__all__[: len(EXPECTED_ND03_PACKAGE_EXPORTS)] == (
        EXPECTED_ND03_PACKAGE_EXPORTS
    )
    assert notification_delivery.__all__[-len(EXPECTED_OUTBOX_EXPORTS) :] == EXPECTED_OUTBOX_EXPORTS
    assert len(notification_delivery.__all__) == len(set(notification_delivery.__all__))
    assert len(outbox.__all__) == len(set(outbox.__all__))
    assert notification_delivery._outbox is outbox
    assert "__getattr__" not in notification_delivery.__dict__
    assert "_load_outbox_exports" not in notification_delivery.__dict__
    for export_name in EXPECTED_OUTBOX_EXPORTS:
        assert getattr(notification_delivery, export_name) is getattr(outbox, export_name)


def test_outbox_enum_values_are_exact_and_have_no_extras() -> None:
    for enum_type, expected_values in EXPECTED_ENUM_VALUES.items():
        assert _enum_values(enum_type) == expected_values
        assert _enum_names(enum_type) == expected_values


def test_outbox_dataclass_field_order_type_and_slotting_are_exact() -> None:
    for dataclass_type, expected_fields in EXPECTED_DATACLASS_FIELDS.items():
        assert is_dataclass(dataclass_type)
        assert getattr(dataclass_type, "__dataclass_params__").frozen is True
        assert getattr(dataclass_type, "__slots__") == expected_fields
        assert tuple(field.name for field in fields(dataclass_type)) == expected_fields

    channel_intent_hints = get_type_hints(outbox.NotificationOutboxChannelIntent)
    item_hints = get_type_hints(outbox.NotificationOutboxItem)
    decision_hints = get_type_hints(outbox.NotificationOutboxCreationDecision)
    for field_name, expected_type in EXPECTED_FIELD_TYPES[
        outbox.NotificationOutboxChannelIntent
    ].items():
        assert channel_intent_hints[field_name] == expected_type
    for field_name, expected_type in EXPECTED_FIELD_TYPES[outbox.NotificationOutboxItem].items():
        assert item_hints[field_name] == expected_type
    for field_name, expected_type in EXPECTED_FIELD_TYPES[
        outbox.NotificationOutboxCreationDecision
    ].items():
        assert decision_hints[field_name] == expected_type


def test_outbox_function_signature_is_exact() -> None:
    signature = inspect.signature(outbox.create_notification_outbox_item)
    assert tuple(signature.parameters) == (
        "decision_id",
        "outbox_item_id",
        "outbox_contract",
        "outbox_contract_version",
        "eligibility_decision",
        "idempotency_key",
        "idempotency_fingerprint",
        "idempotency_scope",
        "existing_outbox_item",
        "evidence_reference_ids",
    )
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for parameter in signature.parameters.values()
    )
    assert get_type_hints(outbox.create_notification_outbox_item)["return"] is (
        outbox.NotificationOutboxCreationDecision
    )


def test_reason_code_matrix_and_task_id_appear_exactly_once_in_production_source() -> None:
    module_text = Path("src/mayak/modules/notification_delivery/outbox.py").read_text()
    reason_codes = set(re.findall(r'"(outbox-[a-z-]+)"', module_text.lower()))
    assert reason_codes == EXPECTED_OUTBOX_REASON_CODES
    assert module_text.count(outbox.ND04_TASK_ID) == 1


def test_no_extra_exports_or_lazy_helpers() -> None:
    namespace: dict[str, object] = {}
    exec("from mayak.modules.notification_delivery import *", namespace)

    assert tuple(notification_delivery.__all__) == EXPECTED_PACKAGE_EXPORTS
    assert len(notification_delivery.__all__) == len(set(notification_delivery.__all__))
    assert all(name in namespace for name in notification_delivery.__all__)
    assert "_load_outbox_exports" not in namespace
    assert "__getattr__" not in namespace
    public_namespace = tuple(name for name in namespace if not name.startswith("__"))
    assert public_namespace == notification_delivery.__all__


def test_no_timestamps_attempt_records_retry_reconciliation_state_or_payload_fields() -> None:
    field_names: set[str] = set()
    for dataclass_type in EXPECTED_DATACLASS_FIELDS:
        field_names.update(field.name for field in fields(dataclass_type))
    assert field_names.isdisjoint(FORBIDDEN_FIELD_NAMES)
