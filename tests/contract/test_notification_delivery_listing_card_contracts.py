# ruff: noqa: E501, F401, I001
from __future__ import annotations

import inspect
from dataclasses import fields, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any, cast, get_type_hints

from mayak.modules import notification_delivery
from mayak.modules.notification_delivery import listing_card as notification_delivery_listing_card
from mayak.modules.notification_delivery.listing_card import (
    ND10_TASK_ID,
    NotificationListingCard,
    NotificationListingCardAuthority,
    NotificationListingCardFieldClass,
    NotificationListingCardFieldFact,
    NotificationListingCardInput,
    NotificationListingCardProvenanceTier,
    NotificationListingCardProjectionDecision,
    NotificationListingCardProjectionStatus,
    NotificationListingCardReasonClass,
    NotificationListingCardValueClass,
    project_notification_listing_cards,
)
from mayak.modules.notification_delivery.source_intake import NotificationSourceIntakeDecision

EXPECTED_TASK_ID = "ND-10-LISTING-CARD-PAYLOAD-BOUNDARY-SEMANTICS-20260716-017"

EXPECTED_MODULE_EXPORTS = (
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
)

EXPECTED_PACKAGE_EXPORTS = EXPECTED_PACKAGE_PREFIX + EXPECTED_MODULE_EXPORTS

EXPECTED_ENUM_VALUES: dict[type[Enum], tuple[str, ...]] = {
    NotificationListingCardAuthority: ("NOTIFICATION_DELIVERY_SERVER",),
    NotificationListingCardReasonClass: (
        "NEW_LISTING",
        "RECOVERED_NEW_LISTING",
        "LATEST_FRESH_STATE_RESTORED",
    ),
    NotificationListingCardFieldClass: (
        "TITLE",
        "PRICE",
        "GEOGRAPHY",
        "LISTING_URL_REFERENCE",
        "PREVIEW_REFERENCE",
        "DESCRIPTION",
        "SELLER",
        "SELLER_RATING",
        "PHONE",
    ),
    NotificationListingCardValueClass: (
        "SAFE_TEXT",
        "SAFE_REFERENCE",
    ),
    NotificationListingCardProvenanceTier: (
        "TIER_1_SEARCH_RESULT",
        "TIER_2_LISTING_DETAIL",
        "TIER_3_CONTACT",
    ),
    NotificationListingCardProjectionStatus: (
        "ACCEPTED_FIELDS",
        "ACCEPTED_REFERENCE_ONLY",
        "NOT_APPLICABLE_NO_LISTINGS",
    ),
}

EXPECTED_DATACLASS_FIELDS: dict[type[object], tuple[str, ...]] = {
    NotificationListingCardFieldFact: (
        "field_fact_id",
        "listing_reference_id",
        "field_class",
        "value_class",
        "safe_value",
        "upstream_field_family",
        "provenance_tier",
        "upstream_field_reference_id",
        "compatibility_profile_reference_id",
        "source_committed",
        "source_commit_reference",
        "field_evidence_approved",
        "detail_gate_approved",
        "contact_gate_approved",
        "contains_raw_provider_payload",
        "evidence_reference_ids",
    ),
    NotificationListingCardInput: (
        "listing_card_id",
        "listing_reference_id",
        "beacon_name_reference_id",
        "field_facts",
        "evidence_reference_ids",
    ),
    NotificationListingCard: (
        "listing_card_id",
        "listing_reference_id",
        "account_id",
        "beacon_id",
        "source_event_id",
        "source_fact_id",
        "source_family",
        "reason_class",
        "beacon_name_reference_id",
        "field_facts",
        "correlation_id",
        "causation_id",
        "evidence_reference_ids",
    ),
    NotificationListingCardProjectionDecision: (
        "decision_id",
        "authority",
        "source_intake_decision",
        "cards",
        "status",
        "listing_references_preserved",
        "optional_fields_missing_allowed",
        "display_rendering_authorized",
        "delivery_attempt_authorized",
        "provider_mapping_authorized",
        "reason_codes",
        "evidence_reference_ids",
    ),
}

EXPECTED_FIELD_TYPES: dict[type[object], dict[str, object]] = {
    NotificationListingCardFieldFact: {
        "field_fact_id": str,
        "listing_reference_id": str,
        "field_class": NotificationListingCardFieldClass,
        "value_class": NotificationListingCardValueClass,
        "safe_value": str,
        "upstream_field_family": str,
        "provenance_tier": NotificationListingCardProvenanceTier,
        "upstream_field_reference_id": str,
        "compatibility_profile_reference_id": str,
        "source_committed": bool,
        "source_commit_reference": str,
        "field_evidence_approved": bool,
        "detail_gate_approved": bool,
        "contact_gate_approved": bool,
        "contains_raw_provider_payload": bool,
        "evidence_reference_ids": tuple[str, ...],
    },
    NotificationListingCardInput: {
        "listing_card_id": str,
        "listing_reference_id": str,
        "beacon_name_reference_id": str | None,
        "field_facts": tuple[NotificationListingCardFieldFact, ...],
        "evidence_reference_ids": tuple[str, ...],
    },
    NotificationListingCard: {
        "listing_card_id": str,
        "listing_reference_id": str,
        "account_id": str,
        "beacon_id": str,
        "source_event_id": str,
        "source_fact_id": str,
        "source_family": notification_delivery_listing_card.NotificationSourceFamily,
        "reason_class": NotificationListingCardReasonClass,
        "beacon_name_reference_id": str | None,
        "field_facts": tuple[NotificationListingCardFieldFact, ...],
        "correlation_id": str,
        "causation_id": str,
        "evidence_reference_ids": tuple[str, ...],
    },
    NotificationListingCardProjectionDecision: {
        "decision_id": str,
        "authority": NotificationListingCardAuthority,
        "source_intake_decision": NotificationSourceIntakeDecision,
        "cards": tuple[NotificationListingCard, ...],
        "status": NotificationListingCardProjectionStatus,
        "listing_references_preserved": bool,
        "optional_fields_missing_allowed": bool,
        "display_rendering_authorized": bool,
        "delivery_attempt_authorized": bool,
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
    assert ND10_TASK_ID == EXPECTED_TASK_ID
    assert type(notification_delivery_listing_card.__all__) is tuple
    assert notification_delivery_listing_card.__all__ == EXPECTED_MODULE_EXPORTS
    assert type(notification_delivery.__all__) is tuple
    assert notification_delivery.__all__ == EXPECTED_PACKAGE_EXPORTS
    assert len(notification_delivery_listing_card.__all__) == len(set(notification_delivery_listing_card.__all__))
    assert len(notification_delivery.__all__) == len(set(notification_delivery.__all__))
    assert notification_delivery_listing_card.ND10_TASK_ID is ND10_TASK_ID
    assert notification_delivery.ND10_TASK_ID is ND10_TASK_ID
    assert notification_delivery._listing_card is notification_delivery_listing_card
    assert "__getattr__" not in notification_delivery_listing_card.__dict__
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
    signature = inspect.signature(project_notification_listing_cards)
    assert tuple(signature.parameters) == (
        "decision_id",
        "source_intake_decision",
        "card_inputs",
        "evidence_reference_ids",
    )
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for parameter in signature.parameters.values()
    )


def test_import_star_and_package_identity_bindings_are_exact() -> None:
    namespace: dict[str, object] = {}
    exec("from mayak.modules.notification_delivery.listing_card import *", namespace)
    for name in EXPECTED_MODULE_EXPORTS:
        assert namespace[name] is getattr(notification_delivery_listing_card, name)

    package_namespace: dict[str, object] = {}
    exec("from mayak.modules.notification_delivery import *", package_namespace)
    for name in EXPECTED_PACKAGE_EXPORTS:
        assert package_namespace[name] is getattr(notification_delivery, name)


def test_production_source_contains_task_id_exactly_once() -> None:
    source = Path("src/mayak/modules/notification_delivery/listing_card.py").read_text()
    assert source.count(EXPECTED_TASK_ID) == 1


def test_package_exports_remain_append_friendly_after_nd10() -> None:
    assert notification_delivery.__all__[: len(EXPECTED_PACKAGE_PREFIX)] == EXPECTED_PACKAGE_PREFIX
    assert notification_delivery.__all__[len(EXPECTED_PACKAGE_PREFIX) :] == EXPECTED_MODULE_EXPORTS
    assert len(notification_delivery.__all__) == len(set(notification_delivery.__all__))
