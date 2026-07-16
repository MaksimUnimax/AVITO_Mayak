from __future__ import annotations

import inspect
from dataclasses import fields, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any, cast, get_type_hints

from mayak.modules import notification_delivery
from mayak.modules.notification_delivery import (
    deferred_runtime_gate as deferred_runtime_gate_module,
)
from mayak.modules.notification_delivery.deferred_runtime_gate import (
    ND14_TASK_ID,
    NotificationDeferredRuntimeAuthority,
    NotificationDeferredRuntimeCapability,
    NotificationDeferredRuntimeGateBoundary,
    NotificationDeferredRuntimeGateStatus,
    NotificationDeferredRuntimeRequirement,
    NotificationPreRuntimeAllowedWork,
    build_notification_deferred_runtime_gate,
)

EXPECTED_TASK_ID = "MAYAK-ND-14-DEFERRED-RUNTIME-GATES-20260716-010"

EXPECTED_MODULE_EXPORTS = (
    "ND14_TASK_ID",
    "NotificationDeferredRuntimeAuthority",
    "NotificationDeferredRuntimeGateStatus",
    "NotificationDeferredRuntimeRequirement",
    "NotificationPreRuntimeAllowedWork",
    "NotificationDeferredRuntimeCapability",
    "NotificationDeferredRuntimeGateBoundary",
    "build_notification_deferred_runtime_gate",
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
    "ND14_TASK_ID",
    "NotificationDeferredRuntimeAuthority",
    "NotificationDeferredRuntimeGateStatus",
    "NotificationDeferredRuntimeRequirement",
    "NotificationPreRuntimeAllowedWork",
    "NotificationDeferredRuntimeCapability",
    "NotificationDeferredRuntimeGateBoundary",
    "build_notification_deferred_runtime_gate",
)

EXPECTED_PACKAGE_PREFIX = EXPECTED_PACKAGE_EXPORTS[: -len(EXPECTED_MODULE_EXPORTS)]

EXPECTED_ENUM_VALUES: dict[type[Enum], tuple[str, ...]] = {
    NotificationDeferredRuntimeAuthority: ("NOTIFICATION_DELIVERY_SERVER",),
    NotificationDeferredRuntimeGateStatus: ("BLOCKED_PENDING_EXPLICIT_GATES",),
    NotificationDeferredRuntimeRequirement: (
        "PHYSICAL_SCHEMA_AND_MIGRATIONS",
        "QUEUE_WORKER_BROKER",
        "PROVIDER_ADAPTER_PLAYBOOKS",
        "PROVIDER_CREDENTIALS_POLICY",
        "RETRY_RATE_TIME_POLICY",
        "OPERATIONS_DEPLOY_RUNTIME_TOPOLOGY",
        "EXACT_IMPLEMENTATION_TASK",
    ),
    NotificationPreRuntimeAllowedWork: (
        "SEMANTIC_CONTRACTS",
        "SYNTHETIC_DETERMINISTIC_FAKES",
        "ARCHITECTURE_STATIC_CHECKS",
        "DOCS_ONLY_DECISIONS",
        "EVIDENCE_HANDOFF",
    ),
    NotificationDeferredRuntimeCapability: (
        "POSTGRESQL_TABLES",
        "SQLALCHEMY_MODELS",
        "PSYCOPG_USAGE",
        "ALEMBIC_MIGRATIONS",
        "QUEUE",
        "WORKER",
        "BROKER_OR_CACHE",
        "SCHEDULER_OR_POLLING",
        "TELEGRAM_PROVIDER_ADAPTER",
        "MAX_PROVIDER_ADAPTER",
        "WEB_PUSH_DELIVERY",
        "WEBHOOK",
        "MINI_APP",
        "PROVIDER_API_CALLS",
        "MESSAGE_TEMPLATES",
        "PROVIDER_CREDENTIALS",
        "PROVIDER_RETRY_OR_BACKOFF",
        "PROVIDER_RATE_LIMITS",
        "QUIET_HOURS",
        "DIGEST_OR_TIME_BATCHING",
        "RETENTION_TOOLING",
        "RUNTIME_SERVICES",
        "DOCKER_CICD_DEPLOY",
        "LIVE_DELIVERY",
    ),
}

EXPECTED_DATACLASS_FIELDS: dict[type[object], tuple[str, ...]] = {
    NotificationDeferredRuntimeGateBoundary: (
        "boundary_id",
        "authority",
        "status",
        "required_gate_classes",
        "satisfied_gate_classes",
        "allowed_pre_runtime_work",
        "blocked_runtime_capabilities",
        "runtime_execution_authorized",
        "persistence_implementation_authorized",
        "provider_adapter_implementation_authorized",
        "production_readiness_inferred",
        "provider_permission_inferred",
        "retention_policy_resolved",
        "od013_closed",
        "reason_codes",
        "evidence_reference_ids",
    ),
}

EXPECTED_FIELD_TYPES: dict[type[object], dict[str, object]] = {
    NotificationDeferredRuntimeGateBoundary: {
        "boundary_id": str,
        "authority": NotificationDeferredRuntimeAuthority,
        "status": NotificationDeferredRuntimeGateStatus,
        "required_gate_classes": tuple[NotificationDeferredRuntimeRequirement, ...],
        "satisfied_gate_classes": tuple[NotificationDeferredRuntimeRequirement, ...],
        "allowed_pre_runtime_work": tuple[NotificationPreRuntimeAllowedWork, ...],
        "blocked_runtime_capabilities": tuple[NotificationDeferredRuntimeCapability, ...],
        "runtime_execution_authorized": bool,
        "persistence_implementation_authorized": bool,
        "provider_adapter_implementation_authorized": bool,
        "production_readiness_inferred": bool,
        "provider_permission_inferred": bool,
        "retention_policy_resolved": bool,
        "od013_closed": bool,
        "reason_codes": tuple[str, ...],
        "evidence_reference_ids": tuple[str, ...],
    },
}


def test_task_id_constant_and_public_surface_are_exact() -> None:
    assert ND14_TASK_ID == EXPECTED_TASK_ID
    assert type(deferred_runtime_gate_module.__all__) is tuple
    assert deferred_runtime_gate_module.__all__ == EXPECTED_MODULE_EXPORTS
    assert type(notification_delivery.__all__) is tuple
    assert notification_delivery.__all__ == EXPECTED_PACKAGE_EXPORTS
    assert len(deferred_runtime_gate_module.__all__) == len(
        set(deferred_runtime_gate_module.__all__)
    )
    assert len(notification_delivery.__all__) == len(set(notification_delivery.__all__))
    assert deferred_runtime_gate_module.ND14_TASK_ID is ND14_TASK_ID
    assert notification_delivery.ND14_TASK_ID is ND14_TASK_ID
    assert (
        notification_delivery.NotificationDeferredRuntimeAuthority
        is NotificationDeferredRuntimeAuthority
    )
    assert (
        notification_delivery.NotificationDeferredRuntimeGateStatus
        is NotificationDeferredRuntimeGateStatus
    )
    assert (
        notification_delivery.NotificationDeferredRuntimeRequirement
        is NotificationDeferredRuntimeRequirement
    )
    assert (
        notification_delivery.NotificationPreRuntimeAllowedWork is NotificationPreRuntimeAllowedWork
    )
    assert (
        notification_delivery.NotificationDeferredRuntimeCapability
        is NotificationDeferredRuntimeCapability
    )
    assert (
        notification_delivery.NotificationDeferredRuntimeGateBoundary
        is NotificationDeferredRuntimeGateBoundary
    )
    assert (
        notification_delivery.build_notification_deferred_runtime_gate
        is build_notification_deferred_runtime_gate
    )
    assert "__getattr__" not in deferred_runtime_gate_module.__dict__
    assert "__getattr__" not in notification_delivery.__dict__


def test_enum_values_are_exact_and_have_no_extras() -> None:
    for enum_type, expected_values in EXPECTED_ENUM_VALUES.items():
        observed_values = tuple(member.value for member in enum_type)
        observed_names = tuple(member.name for member in enum_type)
        assert observed_values == expected_values
        assert observed_names == expected_values


def test_dataclass_field_order_and_slotting_are_exact() -> None:
    dataclass_type = NotificationDeferredRuntimeGateBoundary
    expected_fields = EXPECTED_DATACLASS_FIELDS[dataclass_type]
    assert is_dataclass(dataclass_type)
    assert cast(Any, dataclass_type).__dataclass_params__.frozen is True
    assert cast(Any, dataclass_type).__slots__ == expected_fields
    assert tuple(field.name for field in fields(dataclass_type)) == expected_fields


def test_dataclass_field_types_are_exact() -> None:
    type_hints = get_type_hints(NotificationDeferredRuntimeGateBoundary, include_extras=True)
    for field_name, expected_type in EXPECTED_FIELD_TYPES[
        NotificationDeferredRuntimeGateBoundary
    ].items():
        assert type_hints[field_name] == expected_type


def test_builder_signature_is_keyword_only_and_exact() -> None:
    signature = inspect.signature(build_notification_deferred_runtime_gate)
    assert tuple(signature.parameters) == ("boundary_id", "evidence_reference_ids")
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for parameter in signature.parameters.values()
    )


def test_import_star_and_package_identity_bindings_are_exact() -> None:
    namespace: dict[str, object] = {}
    exec("from mayak.modules.notification_delivery.deferred_runtime_gate import *", namespace)
    for name in EXPECTED_MODULE_EXPORTS:
        assert namespace[name] is getattr(deferred_runtime_gate_module, name)

    package_namespace: dict[str, object] = {}
    exec("from mayak.modules.notification_delivery import *", package_namespace)
    for name in EXPECTED_PACKAGE_EXPORTS:
        assert package_namespace[name] is getattr(notification_delivery, name)


def test_package_prefix_survives_append_only_exports() -> None:
    assert notification_delivery.__all__[: len(EXPECTED_PACKAGE_PREFIX)] == EXPECTED_PACKAGE_PREFIX


def test_production_source_contains_task_id_exactly_once() -> None:
    source = Path("src/mayak/modules/notification_delivery/deferred_runtime_gate.py").read_text()
    assert source.count(EXPECTED_TASK_ID) == 1


def test_forbidden_public_api_concepts_do_not_leak_into_the_surface() -> None:
    forbidden_tokens = (
        "approve",
        "enable",
        "execute",
        "unlock",
    )
    for name in EXPECTED_PACKAGE_EXPORTS + EXPECTED_MODULE_EXPORTS:
        lowered = name.lower()
        for token in forbidden_tokens:
            assert token not in lowered, (name, token)
