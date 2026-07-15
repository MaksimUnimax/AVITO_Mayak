from __future__ import annotations

import inspect
import re
from dataclasses import fields, is_dataclass
from enum import Enum, EnumMeta
from pathlib import Path
from typing import get_type_hints

from mayak.contracts.idempotency import IdempotencyFingerprint, IdempotencyKey, IdempotencyScope
from mayak.modules import notification_delivery
from mayak.modules.notification_delivery.eligibility import (
    ND03_TASK_ID,
    NO_NEW_MINIMUM_FREQUENCY_MINUTES,
    NotificationBeaconLifecycleStatus,
    NotificationChannelClass,
    NotificationChannelEligibilityEvidence,
    NotificationChannelGateDecision,
    NotificationChannelGateStatus,
    NotificationEligibilityAuthority,
    NotificationEligibilityContext,
    NotificationEligibilityDecision,
    NotificationEligibilityStatus,
    NotificationEntitlementStatus,
    NotificationRecoveryGraceEvidence,
    evaluate_notification_eligibility,
)
from mayak.modules.notification_delivery.source_intake import (
    ND02_TASK_ID,
    NotificationSourceEvent,
    NotificationSourceFamily,
    NotificationSourceIntakeAuthority,
    NotificationSourceIntakeDecision,
    NotificationSourceIntakeStatus,
    NotificationSourceProducer,
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
)

EXPECTED_ND02_EXPORTS = (
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

EXPECTED_ND03_EXPORTS = EXPECTED_PACKAGE_EXPORTS[len(EXPECTED_ND02_EXPORTS) :]

ACCEPTED_NOTIFICATION_CANDIDATE = NotificationSourceIntakeStatus.ACCEPTED_NOTIFICATION_CANDIDATE

EXPECTED_ENUM_VALUES = {
    NotificationEligibilityAuthority: ("NOTIFICATION_DELIVERY_SERVER",),
    NotificationBeaconLifecycleStatus: (
        "DRAFT",
        "READY",
        "ACTIVE",
        "PAUSED",
        "FROZEN",
        "ARCHIVED",
        "PERMANENTLY_DELETED",
        "NOT_APPLICABLE",
        "AMBIGUOUS",
    ),
    NotificationEntitlementStatus: (
        "ALLOWED",
        "DENIED",
        "BLOCKED",
        "EXPIRED",
        "AMBIGUOUS",
        "UNSUPPORTED",
        "USER_CHOICE_REQUIRED",
        "FREE_COMPLIANCE_REQUIRED",
        "CONFLICT",
        "NOT_APPLICABLE",
    ),
    NotificationChannelClass: (
        "TELEGRAM",
        "MAX",
        "WEB_STATUS_READ_MODEL",
    ),
    NotificationChannelGateStatus: (
        "ELIGIBLE",
        "DISABLED_BY_USER",
        "TARGET_UNVERIFIED",
        "TARGET_UNAVAILABLE",
        "READ_MODEL_ONLY",
    ),
    NotificationEligibilityStatus: (
        "ELIGIBLE",
        "ELIGIBLE_RECOVERY_GRACE",
        "STATUS_READ_MODEL_ONLY",
        "SUPPRESSED_BY_PREFERENCE",
        "BLOCKED_SOURCE_INTAKE",
        "BLOCKED_SCOPE_MISMATCH",
        "BLOCKED_BEACON_LIFECYCLE",
        "BLOCKED_ENTITLEMENT",
        "BLOCKED_AMBIGUOUS",
        "BLOCKED_NO_ELIGIBLE_PUSH_CHANNEL",
    ),
}

EXPECTED_DATACLASS_FIELDS = {
    NotificationChannelEligibilityEvidence: (
        "channel_class",
        "enabled_by_user",
        "target_reference_id",
        "target_verified",
        "target_available",
        "evidence_reference_ids",
    ),
    NotificationRecoveryGraceEvidence: (
        "problem_began_while_access_active",
        "recovery_obligation_reference_id",
        "recovery_result_already_consumed",
        "beacon_frozen_due_to_access_expiry",
        "evidence_reference_ids",
    ),
    NotificationEligibilityContext: (
        "account_id",
        "beacon_id",
        "beacon_lifecycle_status",
        "beacon_lifecycle_reference_id",
        "entitlement_status",
        "entitlement_decision_reference_id",
        "no_new_status_preference_enabled",
        "no_new_status_frequency_minutes",
        "channel_evidence",
        "recovery_grace_evidence",
        "evidence_reference_ids",
    ),
    NotificationChannelGateDecision: (
        "channel_class",
        "status",
        "push_eligible",
        "target_reference_id",
        "reason_codes",
        "evidence_reference_ids",
    ),
    NotificationEligibilityDecision: (
        "decision_id",
        "authority",
        "source_intake_decision",
        "context",
        "status",
        "source_eligible",
        "outbox_candidate_eligible",
        "status_read_model_eligible",
        "recovery_grace_applied",
        "eligible_push_channels",
        "channel_gate_decisions",
        "outbox_effect_authorized",
        "delivery_attempt_authorized",
        "reason_codes",
        "evidence_reference_ids",
    ),
}

EXPECTED_REASON_CODES = {
    "channel-read-model-only",
    "channel-disabled-by-user",
    "channel-target-unverified",
    "channel-target-unavailable",
    "channel-eligible",
    "eligibility-source-intake-blocked",
    "eligibility-account-scope-mismatch",
    "eligibility-beacon-scope-mismatch",
    "eligibility-beacon-lifecycle-ambiguous",
    "eligibility-entitlement-ambiguous",
    "eligibility-no-new-preference-disabled",
    "eligibility-no-new-frequency-below-minimum",
    "eligibility-service-access-eligible",
    "eligibility-beacon-lifecycle-not-active",
    "eligibility-entitlement-not-allowed",
    "eligibility-recovery-grace-applied",
    "eligibility-no-eligible-push-channel",
    "eligibility-eligible",
}

FORBIDDEN_PROVIDER_FIELD_NAMES = {
    "raw_payload",
    "provider_payload",
    "payload",
    "body",
    "html",
    "json",
    "chat_title",
    "username",
    "phone",
    "cookie",
    "token",
    "secret",
    "credential",
}


def _source_event(
    *,
    family: NotificationSourceFamily = NotificationSourceFamily.NEW_LISTINGS_FOUND,
    producer: NotificationSourceProducer = NotificationSourceProducer.SCAN_ORCHESTRATION,
    account_id: str = "account-1",
    beacon_id: str | None = "beacon-1",
    scan_run_id: str | None = "scan-run-1",
    listing_count: int = 1,
    safe_listing_reference_ids: tuple[str, ...] = ("listing-1",),
    committed: bool = True,
    commit_reference: str | None = "commit-1",
    service_access_gate_approved: bool = False,
) -> NotificationSourceEvent:
    return NotificationSourceEvent(
        source_event_id="source-event-1",
        source_family=family,
        source_producer=producer,
        source_contract="scan.notification.v1",
        source_contract_version="1.0",
        source_fact_id="fact-1",
        source_committed=committed,
        source_commit_reference=commit_reference,
        account_id=account_id,
        beacon_id=beacon_id,
        scan_run_id=scan_run_id,
        listing_count=listing_count,
        safe_listing_reference_ids=safe_listing_reference_ids,
        correlation_id="corr-1",
        causation_id="cause-1",
        idempotency_key=IdempotencyKey(value="key-1"),
        idempotency_fingerprint=IdempotencyFingerprint(value="fingerprint-1"),
        idempotency_scope=IdempotencyScope(value="scope-1"),
        source_identity_ambiguous=False,
        contains_raw_provider_payload=False,
        service_access_gate_approved=service_access_gate_approved,
        evidence_reference_ids=("source-evidence-1",),
    )


def _source_intake_decision(
    *,
    family: NotificationSourceFamily = NotificationSourceFamily.NEW_LISTINGS_FOUND,
    status: NotificationSourceIntakeStatus = ACCEPTED_NOTIFICATION_CANDIDATE,
    source_accepted: bool = True,
    notification_candidate: bool = True,
    status_read_model_candidate: bool = True,
    beacon_id: str | None = "beacon-1",
    scan_run_id: str | None = "scan-run-1",
    listing_count: int = 1,
    safe_listing_reference_ids: tuple[str, ...] = ("listing-1",),
    reason_codes: tuple[str, ...] = ("source-accepted-new-listings",),
) -> NotificationSourceIntakeDecision:
    event = _source_event(
        family=family,
        beacon_id=beacon_id,
        scan_run_id=scan_run_id,
        listing_count=listing_count,
        safe_listing_reference_ids=safe_listing_reference_ids,
    )
    return NotificationSourceIntakeDecision(
        decision_id="intake-decision-1",
        authority=NotificationSourceIntakeAuthority.NOTIFICATION_DELIVERY_SERVER,
        source_event=event,
        status=status,
        source_accepted=source_accepted,
        notification_candidate=notification_candidate,
        status_read_model_candidate=status_read_model_candidate,
        outbox_effect_authorized=False,
        delivery_attempt_authorized=False,
        reason_codes=reason_codes,
        evidence_reference_ids=("intake-evidence-1",),
    )


def _context() -> NotificationEligibilityContext:
    return NotificationEligibilityContext(
        account_id="account-1",
        beacon_id="beacon-1",
        beacon_lifecycle_status=NotificationBeaconLifecycleStatus.ACTIVE,
        beacon_lifecycle_reference_id="beacon-lifecycle-1",
        entitlement_status=NotificationEntitlementStatus.ALLOWED,
        entitlement_decision_reference_id="entitlement-1",
        no_new_status_preference_enabled=False,
        no_new_status_frequency_minutes=None,
        channel_evidence=(
            NotificationChannelEligibilityEvidence(
                channel_class=NotificationChannelClass.TELEGRAM,
                enabled_by_user=True,
                target_reference_id="telegram-target-1",
                target_verified=True,
                target_available=True,
                evidence_reference_ids=("telegram-evidence-1",),
            ),
            NotificationChannelEligibilityEvidence(
                channel_class=NotificationChannelClass.MAX,
                enabled_by_user=True,
                target_reference_id="max-target-1",
                target_verified=True,
                target_available=True,
                evidence_reference_ids=("max-evidence-1",),
            ),
            NotificationChannelEligibilityEvidence(
                channel_class=NotificationChannelClass.WEB_STATUS_READ_MODEL,
                enabled_by_user=True,
                target_reference_id=None,
                target_verified=False,
                target_available=False,
                evidence_reference_ids=("web-evidence-1",),
            ),
        ),
        recovery_grace_evidence=NotificationRecoveryGraceEvidence(
            problem_began_while_access_active=False,
            recovery_obligation_reference_id=None,
            recovery_result_already_consumed=False,
            beacon_frozen_due_to_access_expiry=False,
            evidence_reference_ids=("recovery-evidence-1",),
        ),
        evidence_reference_ids=("context-evidence-1",),
    )


def _enum_values(enum_type: EnumMeta) -> tuple[str, ...]:
    members: list[Enum] = list(enum_type)
    return tuple(str(member.value) for member in members)


def _enum_names(enum_type: EnumMeta) -> tuple[str, ...]:
    members: list[Enum] = list(enum_type)
    return tuple(member.name for member in members)


def test_task_id_constant_and_package_exports_are_exact() -> None:
    assert ND03_TASK_ID == "ND-03-ELIGIBILITY-PREFERENCES-20260715-004"
    assert NO_NEW_MINIMUM_FREQUENCY_MINUTES == 60
    assert ND02_TASK_ID == "ND-02-SOURCE-INTAKE-CONTRACTS-20260715-003"
    original_all = notification_delivery.__all__
    try:
        assert getattr(notification_delivery, "ND03_TASK_ID") == ND03_TASK_ID
        assert type(notification_delivery.__all__) is tuple
        assert notification_delivery.__all__ == EXPECTED_PACKAGE_EXPORTS
        assert notification_delivery.__all__[: len(EXPECTED_ND02_EXPORTS)] == EXPECTED_ND02_EXPORTS
    finally:
        notification_delivery.__all__ = original_all
        for export_name in EXPECTED_ND03_EXPORTS:
            notification_delivery.__dict__.pop(export_name, None)


def test_enum_values_are_exact_and_have_no_extras() -> None:
    for enum_type, expected_values in EXPECTED_ENUM_VALUES.items():
        assert _enum_values(enum_type) == expected_values
        assert _enum_names(enum_type) == expected_values


def test_dataclass_field_order_and_slotting_are_exact() -> None:
    for dataclass_type, expected_fields in EXPECTED_DATACLASS_FIELDS.items():
        assert is_dataclass(dataclass_type)
        assert getattr(dataclass_type, "__dataclass_params__").frozen is True
        assert getattr(dataclass_type, "__slots__") == expected_fields
        assert tuple(field.name for field in fields(dataclass_type)) == expected_fields


def test_source_intake_type_references_are_exact() -> None:
    decision_hints = get_type_hints(NotificationEligibilityDecision)
    context_hints = get_type_hints(NotificationEligibilityContext)
    assert decision_hints["source_intake_decision"] is NotificationSourceIntakeDecision
    assert (
        get_type_hints(evaluate_notification_eligibility)["source_intake_decision"]
        is NotificationSourceIntakeDecision
    )
    assert context_hints["recovery_grace_evidence"] is NotificationRecoveryGraceEvidence


def test_main_function_signature_is_exact() -> None:
    signature = inspect.signature(evaluate_notification_eligibility)
    assert tuple(signature.parameters) == (
        "decision_id",
        "source_intake_decision",
        "context",
        "evidence_reference_ids",
    )
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for parameter in signature.parameters.values()
    )


def test_reason_code_matrix_is_exact() -> None:
    module_text = Path("src/mayak/modules/notification_delivery/eligibility.py").read_text()
    reason_codes = set(re.findall(r'"((?:eligibility|channel)-[a-z-]+)"', module_text.lower()))
    assert reason_codes == EXPECTED_REASON_CODES


def test_eligible_push_channels_match_gate_decisions() -> None:
    intake_decision = _source_intake_decision()
    context = _context()

    decision = evaluate_notification_eligibility(
        decision_id="eligibility-contract-1",
        source_intake_decision=intake_decision,
        context=context,
        evidence_reference_ids=("contract-evidence-1",),
    )

    assert decision.eligible_push_channels == (
        NotificationChannelClass.TELEGRAM,
        NotificationChannelClass.MAX,
    )
    assert decision.eligible_push_channels == tuple(
        gate.channel_class for gate in decision.channel_gate_decisions if gate.push_eligible
    )


def test_no_provider_specific_payload_or_target_value_is_represented() -> None:
    field_names: set[str] = set()
    for dataclass_type in EXPECTED_DATACLASS_FIELDS:
        field_names.update(field.name for field in fields(dataclass_type))
    assert FORBIDDEN_PROVIDER_FIELD_NAMES.isdisjoint(field_names)


def test_nd03_task_id_appears_exactly_once_in_production_source_scope() -> None:
    module_text = Path("src/mayak/modules/notification_delivery/eligibility.py").read_text()
    assert module_text.count(ND03_TASK_ID) == 1


def test_no_extra_enum_values_or_exports() -> None:
    original_all = notification_delivery.__all__
    try:
        assert getattr(notification_delivery, "ND03_TASK_ID") == ND03_TASK_ID
        assert tuple(notification_delivery.__all__) == EXPECTED_PACKAGE_EXPORTS
        assert len(notification_delivery.__all__) == len(set(notification_delivery.__all__))
    finally:
        notification_delivery.__all__ = original_all
        for export_name in EXPECTED_ND03_EXPORTS:
            notification_delivery.__dict__.pop(export_name, None)
