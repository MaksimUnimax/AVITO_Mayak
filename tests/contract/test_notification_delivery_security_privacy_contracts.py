from __future__ import annotations

import inspect
from dataclasses import fields, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any, cast, get_type_hints

from mayak.modules import notification_delivery
from mayak.modules.notification_delivery import (
    security_privacy as notification_delivery_security_privacy,
)
from mayak.modules.notification_delivery.eligibility import NotificationChannelClass
from mayak.modules.notification_delivery.read_model import NotificationReadAudience
from mayak.modules.notification_delivery.security_privacy import (
    ND13_TASK_ID,
    NotificationContentSafetyStatus,
    NotificationHistoricalEvidenceSnapshot,
    NotificationIdentityScopeStatus,
    NotificationProtectedAction,
    NotificationSafeContentScope,
    NotificationSecurityAuthorizationScope,
    NotificationSecurityDecisionStatus,
    NotificationSecurityPrivacyAuthority,
    NotificationSecurityPrivacyDecision,
    NotificationSecurityPublicErrorClass,
    evaluate_notification_security_privacy,
)

EXPECTED_TASK_ID = "MAYAK-ND-13-SECURITY-PRIVACY-SUPPRESSION-20260716-008"

EXPECTED_MODULE_EXPORTS = (
    "ND13_TASK_ID",
    "NotificationSecurityPrivacyAuthority",
    "NotificationProtectedAction",
    "NotificationIdentityScopeStatus",
    "NotificationContentSafetyStatus",
    "NotificationSecurityDecisionStatus",
    "NotificationSecurityPublicErrorClass",
    "NotificationSecurityAuthorizationScope",
    "NotificationSafeContentScope",
    "NotificationHistoricalEvidenceSnapshot",
    "NotificationSecurityPrivacyDecision",
    "evaluate_notification_security_privacy",
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
    "ND13_TASK_ID",
    "NotificationSecurityPrivacyAuthority",
    "NotificationProtectedAction",
    "NotificationIdentityScopeStatus",
    "NotificationContentSafetyStatus",
    "NotificationSecurityDecisionStatus",
    "NotificationSecurityPublicErrorClass",
    "NotificationSecurityAuthorizationScope",
    "NotificationSafeContentScope",
    "NotificationHistoricalEvidenceSnapshot",
    "NotificationSecurityPrivacyDecision",
    "evaluate_notification_security_privacy",
)

EXPECTED_PACKAGE_PREFIX = EXPECTED_PACKAGE_EXPORTS[: -len(EXPECTED_MODULE_EXPORTS)]

EXPECTED_ENUM_VALUES: dict[type[Enum], tuple[str, ...]] = {
    NotificationSecurityPrivacyAuthority: ("NOTIFICATION_DELIVERY_SERVER",),
    NotificationProtectedAction: (
        "PROTECTED_READ",
        "OUTBOX_EFFECT",
        "CHANNEL_DELIVERY",
    ),
    NotificationIdentityScopeStatus: (
        "VERIFIED",
        "UNAUTHORIZED",
        "AMBIGUOUS",
    ),
    NotificationContentSafetyStatus: (
        "EMPTY",
        "APPROVED_SAFE_REFERENCES",
        "UNSAFE_OR_UNAPPROVED",
        "AMBIGUOUS",
    ),
    NotificationSecurityDecisionStatus: (
        "AUTHORIZED_READ",
        "AUTHORIZED_EFFECT",
        "AUTHORIZED_RECOVERY_GRACE",
        "SUPPRESSED_BY_USER",
        "BLOCKED_NOT_AUTHORIZED_OR_NOT_FOUND",
        "BLOCKED_AMBIGUOUS",
        "BLOCKED_TARGET_UNVERIFIED",
        "BLOCKED_UNSAFE_CONTENT",
        "BLOCKED_EVIDENCE_CONFLICT",
    ),
    NotificationSecurityPublicErrorClass: (
        "NONE",
        "NOT_AUTHORIZED_OR_NOT_FOUND",
        "REQUEST_BLOCKED",
    ),
}

EXPECTED_DATACLASS_FIELDS: dict[type[object], tuple[str, ...]] = {
    NotificationSecurityAuthorizationScope: (
        "scope_id",
        "audience",
        "identity_status",
        "authorized",
        "principal_reference_id",
        "authorized_account_ids",
        "authorized_beacon_ids",
        "authorization_reference_id",
        "evidence_reference_ids",
    ),
    NotificationSafeContentScope: (
        "content_scope_id",
        "safety_status",
        "safe_listing_reference_ids",
        "approved_listing_reference_ids",
        "evidence_reference_ids",
        "fetch_authorized",
        "enrichment_authorized",
        "provider_rendering_authorized",
    ),
    NotificationHistoricalEvidenceSnapshot: (
        "snapshot_id",
        "account_id",
        "beacon_id",
        "entitlement_decision_reference_id",
        "beacon_lifecycle_reference_id",
        "recovery_obligation_reference_id",
        "evidence_reference_ids",
        "mutation_authorized",
    ),
    NotificationSecurityPrivacyDecision: (
        "decision_id",
        "authority",
        "action",
        "status",
        "public_error_class",
        "authorization_scope_id",
        "account_id",
        "beacon_id",
        "eligibility_decision_id",
        "channel_class",
        "target_reference_id",
        "safe_listing_reference_ids",
        "historical_evidence_snapshot",
        "protected_read_authorized",
        "outbox_effect_authorized",
        "channel_delivery_authorized",
        "recovery_grace_applied",
        "suppressed_by_user",
        "historical_entitlement_evidence_rewritten",
        "historical_beacon_evidence_rewritten",
        "historical_evidence_mutation_authorized",
        "provider_mapping_authorized",
        "provider_execution_authorized",
        "read_tracking_authorized",
        "click_tracking_authorized",
        "retention_authorized",
        "reason_codes",
        "evidence_reference_ids",
    ),
}

EXPECTED_FIELD_TYPES: dict[type[object], dict[str, object]] = {
    NotificationSecurityAuthorizationScope: {
        "scope_id": str,
        "audience": NotificationReadAudience,
        "identity_status": NotificationIdentityScopeStatus,
        "authorized": bool,
        "principal_reference_id": str,
        "authorized_account_ids": tuple[str, ...],
        "authorized_beacon_ids": tuple[str, ...],
        "authorization_reference_id": str,
        "evidence_reference_ids": tuple[str, ...],
    },
    NotificationSafeContentScope: {
        "content_scope_id": str,
        "safety_status": NotificationContentSafetyStatus,
        "safe_listing_reference_ids": tuple[str, ...],
        "approved_listing_reference_ids": tuple[str, ...],
        "evidence_reference_ids": tuple[str, ...],
        "fetch_authorized": bool,
        "enrichment_authorized": bool,
        "provider_rendering_authorized": bool,
    },
    NotificationHistoricalEvidenceSnapshot: {
        "snapshot_id": str,
        "account_id": str,
        "beacon_id": str | None,
        "entitlement_decision_reference_id": str | None,
        "beacon_lifecycle_reference_id": str | None,
        "recovery_obligation_reference_id": str | None,
        "evidence_reference_ids": tuple[str, ...],
        "mutation_authorized": bool,
    },
    NotificationSecurityPrivacyDecision: {
        "decision_id": str,
        "authority": NotificationSecurityPrivacyAuthority,
        "action": NotificationProtectedAction,
        "status": NotificationSecurityDecisionStatus,
        "public_error_class": NotificationSecurityPublicErrorClass,
        "authorization_scope_id": str,
        "account_id": str | None,
        "beacon_id": str | None,
        "eligibility_decision_id": str | None,
        "channel_class": NotificationChannelClass | None,
        "target_reference_id": str | None,
        "safe_listing_reference_ids": tuple[str, ...],
        "historical_evidence_snapshot": NotificationHistoricalEvidenceSnapshot | None,
        "protected_read_authorized": bool,
        "outbox_effect_authorized": bool,
        "channel_delivery_authorized": bool,
        "recovery_grace_applied": bool,
        "suppressed_by_user": bool,
        "historical_entitlement_evidence_rewritten": bool,
        "historical_beacon_evidence_rewritten": bool,
        "historical_evidence_mutation_authorized": bool,
        "provider_mapping_authorized": bool,
        "provider_execution_authorized": bool,
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
    assert ND13_TASK_ID == EXPECTED_TASK_ID
    assert type(notification_delivery_security_privacy.__all__) is tuple
    assert notification_delivery_security_privacy.__all__ == EXPECTED_MODULE_EXPORTS
    assert type(notification_delivery.__all__) is tuple
    assert notification_delivery.__all__[: len(EXPECTED_PACKAGE_PREFIX)] == EXPECTED_PACKAGE_PREFIX
    assert len(notification_delivery_security_privacy.__all__) == len(
        set(notification_delivery_security_privacy.__all__)
    )
    assert len(notification_delivery.__all__) == len(set(notification_delivery.__all__))
    assert notification_delivery_security_privacy.ND13_TASK_ID is ND13_TASK_ID
    assert notification_delivery.ND13_TASK_ID is ND13_TASK_ID
    assert (
        notification_delivery.NotificationSecurityPrivacyAuthority
        is NotificationSecurityPrivacyAuthority
    )
    assert notification_delivery.NotificationProtectedAction is NotificationProtectedAction
    assert notification_delivery.NotificationIdentityScopeStatus is NotificationIdentityScopeStatus
    assert notification_delivery.NotificationContentSafetyStatus is NotificationContentSafetyStatus
    assert (
        notification_delivery.NotificationSecurityDecisionStatus
        is NotificationSecurityDecisionStatus
    )
    assert (
        notification_delivery.NotificationSecurityPublicErrorClass
        is NotificationSecurityPublicErrorClass
    )
    assert (
        notification_delivery.NotificationSecurityAuthorizationScope
        is NotificationSecurityAuthorizationScope
    )
    assert notification_delivery.NotificationSafeContentScope is NotificationSafeContentScope
    assert (
        notification_delivery.NotificationHistoricalEvidenceSnapshot
        is NotificationHistoricalEvidenceSnapshot
    )
    assert (
        notification_delivery.NotificationSecurityPrivacyDecision
        is NotificationSecurityPrivacyDecision
    )
    assert (
        notification_delivery.evaluate_notification_security_privacy
        is evaluate_notification_security_privacy
    )
    assert notification_delivery.security_privacy is notification_delivery_security_privacy
    assert "__getattr__" not in notification_delivery_security_privacy.__dict__
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
    signature = inspect.signature(evaluate_notification_security_privacy)
    assert tuple(signature.parameters) == (
        "decision_id",
        "action",
        "authorization_scope",
        "content_scope",
        "historical_evidence_snapshot",
        "eligibility_decision",
        "channel_gate_decision",
        "evidence_reference_ids",
    )
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for parameter in signature.parameters.values()
    )


def test_import_star_and_package_identity_bindings_are_exact() -> None:
    namespace: dict[str, object] = {}
    exec("from mayak.modules.notification_delivery.security_privacy import *", namespace)
    for name in EXPECTED_MODULE_EXPORTS:
        assert namespace[name] is getattr(notification_delivery_security_privacy, name)

    package_namespace: dict[str, object] = {}
    exec("from mayak.modules.notification_delivery import *", package_namespace)
    for name in EXPECTED_PACKAGE_EXPORTS:
        assert package_namespace[name] is getattr(notification_delivery, name)


def test_package_prefix_survives_append_only_exports() -> None:
    assert notification_delivery.__all__[: len(EXPECTED_PACKAGE_PREFIX)] == EXPECTED_PACKAGE_PREFIX


def test_production_source_contains_task_id_exactly_once() -> None:
    source = Path("src/mayak/modules/notification_delivery/security_privacy.py").read_text()
    assert source.count(EXPECTED_TASK_ID) == 1


def test_forbidden_export_categories_do_not_leak_into_the_public_surface() -> None:
    forbidden_tokens = (
        "adapter",
        "broker",
        "database",
        "filesystem",
        "hook",
        "mini_app",
        "popen",
        "queue",
        "runtime",
        "scheduler",
        "secret",
        "socket",
        "storage",
        "subprocess",
        "telegram",
        "token",
        "tracking",
        "ui",
        "webhook",
        "worker",
    )
    for name in EXPECTED_PACKAGE_EXPORTS + EXPECTED_MODULE_EXPORTS:
        lowered = name.lower()
        for token in forbidden_tokens:
            assert token not in lowered, (name, token)
