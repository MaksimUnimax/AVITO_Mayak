from __future__ import annotations

from dataclasses import fields, is_dataclass
from importlib import import_module
from pathlib import Path
from typing import get_type_hints

from mayak.contracts.idempotency import IdempotencyFingerprint, IdempotencyKey, IdempotencyScope
from mayak.modules import notification_delivery
from mayak.modules.notification_delivery import source_intake
from mayak.modules.notification_delivery.source_intake import (
    ND02_TASK_ID,
    NotificationSourceEvent,
    NotificationSourceFamily,
    NotificationSourceIntakeAuthority,
    NotificationSourceIntakeDecision,
    NotificationSourceIntakeStatus,
    NotificationSourceProducer,
)

EXPECTED_ENUM_VALUES = {
    NotificationSourceProducer: (
        "SCAN_ORCHESTRATION",
        "ENTITLEMENTS_OR_BEACON",
        "PARSER_ADAPTER",
        "EGRESS_ROUTING",
        "PROVIDER_ADAPTER",
    ),
    NotificationSourceFamily: (
        "NEW_LISTINGS_FOUND",
        "RECOVERY_SCAN_COMPLETED",
        "EXTERNAL_UNAVAILABLE_STATUS",
        "LOST_ANCHORS_RECOVERED",
        "NO_NEW_LISTINGS_STATUS",
        "APPROVED_SERVICE_ACCESS_FACT",
        "BEACON_BASELINE_ESTABLISHED",
        "SCAN_RUN_PLANNED",
        "SCAN_RUN_STARTED",
        "LISTING_PRICE_PAIR_FIRST_SEEN",
        "PARSER_ONLY_OUTCOME",
        "EGRESS_ONLY_OUTCOME",
        "PROVIDER_ONLY_CALLBACK",
    ),
    NotificationSourceIntakeAuthority: ("NOTIFICATION_DELIVERY_SERVER",),
    NotificationSourceIntakeStatus: (
        "ACCEPTED_NOTIFICATION_CANDIDATE",
        "ACCEPTED_STATUS_ONLY",
        "BLOCKED_UPSTREAM_GATE",
        "REJECTED_UNCOMMITTED",
        "REJECTED_AMBIGUOUS",
        "REJECTED_UNSAFE_PAYLOAD",
        "REJECTED_DISABLED_SOURCE",
        "REJECTED_NON_NOTIFICATION_SOURCE",
        "REJECTED_INVALID_PRODUCER",
    ),
}

EXPECTED_EVENT_FIELDS = (
    "source_event_id",
    "source_family",
    "source_producer",
    "source_contract",
    "source_contract_version",
    "source_fact_id",
    "source_committed",
    "source_commit_reference",
    "account_id",
    "beacon_id",
    "scan_run_id",
    "listing_count",
    "safe_listing_reference_ids",
    "correlation_id",
    "causation_id",
    "idempotency_key",
    "idempotency_fingerprint",
    "idempotency_scope",
    "source_identity_ambiguous",
    "contains_raw_provider_payload",
    "service_access_gate_approved",
    "evidence_reference_ids",
)

EXPECTED_DECISION_FIELDS = (
    "decision_id",
    "authority",
    "source_event",
    "status",
    "source_accepted",
    "notification_candidate",
    "status_read_model_candidate",
    "outbox_effect_authorized",
    "delivery_attempt_authorized",
    "reason_codes",
    "evidence_reference_ids",
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
)

EXPECTED_SOURCE_EXPORTS = (
    "ND02_TASK_ID",
    "NotificationSourceProducer",
    "NotificationSourceFamily",
    "NotificationSourceIntakeAuthority",
    "NotificationSourceIntakeStatus",
    "NotificationSourceEvent",
    "NotificationSourceIntakeDecision",
    "evaluate_notification_source_intake",
)


def test_task_id_and_package_exports_are_exact() -> None:
    assert ND02_TASK_ID == "ND-02-SOURCE-INTAKE-CONTRACTS-20260715-003"
    assert type(notification_delivery.__all__) is tuple
    assert notification_delivery.__all__ == EXPECTED_PACKAGE_EXPORTS
    assert source_intake.__all__ == EXPECTED_SOURCE_EXPORTS


def test_enum_values_are_exact_and_have_no_extras() -> None:
    producer_values = EXPECTED_ENUM_VALUES[NotificationSourceProducer]
    family_values = EXPECTED_ENUM_VALUES[NotificationSourceFamily]
    authority_values = EXPECTED_ENUM_VALUES[NotificationSourceIntakeAuthority]
    status_values = EXPECTED_ENUM_VALUES[NotificationSourceIntakeStatus]

    assert tuple(member.value for member in NotificationSourceProducer) == producer_values
    assert tuple(member.name for member in NotificationSourceProducer) == producer_values
    assert tuple(member.value for member in NotificationSourceFamily) == family_values
    assert tuple(member.name for member in NotificationSourceFamily) == family_values
    assert tuple(member.value for member in NotificationSourceIntakeAuthority) == authority_values
    assert tuple(member.name for member in NotificationSourceIntakeAuthority) == authority_values
    assert tuple(member.value for member in NotificationSourceIntakeStatus) == status_values
    assert tuple(member.name for member in NotificationSourceIntakeStatus) == status_values


def test_dataclass_field_order_and_slotting_are_exact() -> None:
    assert is_dataclass(NotificationSourceEvent)
    assert is_dataclass(NotificationSourceIntakeDecision)
    assert getattr(NotificationSourceEvent, "__dataclass_params__").frozen is True
    assert getattr(NotificationSourceIntakeDecision, "__dataclass_params__").frozen is True
    assert NotificationSourceEvent.__slots__ == EXPECTED_EVENT_FIELDS
    assert NotificationSourceIntakeDecision.__slots__ == EXPECTED_DECISION_FIELDS
    assert tuple(field.name for field in fields(NotificationSourceEvent)) == EXPECTED_EVENT_FIELDS
    assert (
        tuple(field.name for field in fields(NotificationSourceIntakeDecision))
        == EXPECTED_DECISION_FIELDS
    )


def test_idempotency_primitive_types_are_exact() -> None:
    hints = get_type_hints(NotificationSourceEvent)
    assert hints["idempotency_key"] is IdempotencyKey
    assert hints["idempotency_fingerprint"] is IdempotencyFingerprint
    assert hints["idempotency_scope"] is IdempotencyScope


def test_no_raw_payload_or_delivery_result_fields_exist() -> None:
    forbidden_event_fields = {
        "raw_payload",
        "body",
        "html",
        "json",
        "cookie",
        "token",
        "secret",
        "credential",
        "provider_payload",
        "delivery_result",
    }
    event_field_names = set(EXPECTED_EVENT_FIELDS)
    decision_field_names = set(EXPECTED_DECISION_FIELDS)
    assert forbidden_event_fields.isdisjoint(event_field_names)
    assert forbidden_event_fields.isdisjoint(decision_field_names)


def test_reason_code_matrix_and_reference_preservation_are_exact() -> None:
    module_text = Path("src/mayak/modules/notification_delivery/source_intake.py").read_text()
    assert module_text.count(ND02_TASK_ID) == 1

    expected_reason_codes = {
        "source-accepted-new-listings",
        "source-accepted-recovery-result",
        "source-accepted-external-status",
        "source-accepted-lost-anchors-state-restored",
        "source-accepted-status-only-no-new",
        "source-blocked-service-access-gate",
        "source-accepted-service-access",
        "source-disabled-price-change",
        "source-non-notification-baseline",
        "source-non-notification-scan-lifecycle",
        "source-non-notification-parser",
        "source-non-notification-egress",
        "source-non-notification-provider-callback",
        "source-contains-raw-provider-payload",
        "source-identity-ambiguous",
        "source-uncommitted",
        "source-producer-mismatch",
    }
    assert expected_reason_codes == {
        "source-accepted-new-listings",
        "source-accepted-recovery-result",
        "source-accepted-external-status",
        "source-accepted-lost-anchors-state-restored",
        "source-accepted-status-only-no-new",
        "source-blocked-service-access-gate",
        "source-accepted-service-access",
        "source-disabled-price-change",
        "source-non-notification-baseline",
        "source-non-notification-scan-lifecycle",
        "source-non-notification-parser",
        "source-non-notification-egress",
        "source-non-notification-provider-callback",
        "source-contains-raw-provider-payload",
        "source-identity-ambiguous",
        "source-uncommitted",
        "source-producer-mismatch",
    }


def test_no_provider_specific_payload_or_delivery_result_is_represented() -> None:
    event_hints = get_type_hints(NotificationSourceEvent)
    decision_hints = get_type_hints(NotificationSourceIntakeDecision)
    for forbidden_name in (
        "raw_payload",
        "body",
        "html",
        "json",
        "cookie",
        "token",
        "secret",
        "credential",
        "delivery_result",
    ):
        assert forbidden_name not in event_hints
        assert forbidden_name not in decision_hints


def test_source_intake_module_is_importable_through_package() -> None:
    module = import_module("mayak.modules.notification_delivery")
    assert module.ND02_TASK_ID == ND02_TASK_ID
