from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest
from pytest import raises

from mayak.contracts.idempotency import IdempotencyFingerprint, IdempotencyKey, IdempotencyScope
from mayak.modules.notification_delivery import (
    NotificationSourceEvent,
    NotificationSourceFamily,
    NotificationSourceIntakeDecision,
    NotificationSourceProducer,
    evaluate_notification_source_intake,
)
from mayak.modules.notification_delivery.eligibility import (
    NotificationBeaconLifecycleStatus,
    NotificationChannelClass,
    NotificationChannelEligibilityEvidence,
    NotificationChannelGateDecision,
    NotificationEligibilityContext,
    NotificationEligibilityDecision,
    NotificationEntitlementStatus,
    NotificationRecoveryGraceEvidence,
    evaluate_notification_eligibility,
)
from mayak.modules.notification_delivery.read_model import NotificationReadAudience
from mayak.modules.notification_delivery.security_privacy import (
    NotificationContentSafetyStatus,
    NotificationHistoricalEvidenceSnapshot,
    NotificationIdentityScopeStatus,
    NotificationProtectedAction,
    NotificationSafeContentScope,
    NotificationSecurityAuthorizationScope,
    NotificationSecurityDecisionStatus,
    NotificationSecurityPrivacyDecision,
    NotificationSecurityPublicErrorClass,
    evaluate_notification_security_privacy,
)


def _source_event(
    *,
    family: NotificationSourceFamily = NotificationSourceFamily.NEW_LISTINGS_FOUND,
    account_id: str = "account-1",
    beacon_id: str | None = "beacon-1",
    listing_count: int = 1,
    safe_listing_reference_ids: tuple[str, ...] = ("listing-1",),
    committed: bool = True,
    commit_reference: str | None = "commit-1",
) -> NotificationSourceEvent:
    return NotificationSourceEvent(
        source_event_id="source-event-1",
        source_family=family,
        source_producer=NotificationSourceProducer.SCAN_ORCHESTRATION,
        source_contract="scan.notification.v1",
        source_contract_version="1.0",
        source_fact_id="fact-1",
        source_committed=committed,
        source_commit_reference=commit_reference,
        account_id=account_id,
        beacon_id=beacon_id,
        scan_run_id="scan-run-1",
        listing_count=listing_count,
        safe_listing_reference_ids=safe_listing_reference_ids,
        correlation_id="corr-1",
        causation_id="cause-1",
        idempotency_key=IdempotencyKey(value="key-1"),
        idempotency_fingerprint=IdempotencyFingerprint(value="fingerprint-1"),
        idempotency_scope=IdempotencyScope(value="scope-1"),
        source_identity_ambiguous=False,
        contains_raw_provider_payload=False,
        service_access_gate_approved=False,
        evidence_reference_ids=("source-evidence-1",),
    )


def _source_intake_decision(
    source_event: NotificationSourceEvent,
) -> NotificationSourceIntakeDecision:
    return evaluate_notification_source_intake(
        decision_id="source-intake-1",
        source_event=source_event,
        evidence_reference_ids=("intake-evidence-1",),
    )


def _channel_evidence(
    *,
    channel_class: NotificationChannelClass,
    enabled_by_user: bool = True,
    target_reference_id: str | None = None,
    target_verified: bool = True,
    target_available: bool = True,
) -> NotificationChannelEligibilityEvidence:
    if (
        target_reference_id is None
        and channel_class is not NotificationChannelClass.WEB_STATUS_READ_MODEL
    ):
        target_reference_id = f"{channel_class.value.lower()}-target-1"
    return NotificationChannelEligibilityEvidence(
        channel_class=channel_class,
        enabled_by_user=enabled_by_user,
        target_reference_id=target_reference_id,
        target_verified=target_verified,
        target_available=target_available,
        evidence_reference_ids=(f"{channel_class.value.lower()}-evidence-1",),
    )


def _web_evidence() -> NotificationChannelEligibilityEvidence:
    return NotificationChannelEligibilityEvidence(
        channel_class=NotificationChannelClass.WEB_STATUS_READ_MODEL,
        enabled_by_user=True,
        target_reference_id=None,
        target_verified=False,
        target_available=False,
        evidence_reference_ids=("web-status-read-model-evidence-1",),
    )


def _recovery_evidence(
    *,
    problem_began_while_access_active: bool = False,
    recovery_obligation_reference_id: str | None = None,
    recovery_result_already_consumed: bool = False,
    beacon_frozen_due_to_access_expiry: bool = False,
) -> NotificationRecoveryGraceEvidence:
    return NotificationRecoveryGraceEvidence(
        problem_began_while_access_active=problem_began_while_access_active,
        recovery_obligation_reference_id=recovery_obligation_reference_id,
        recovery_result_already_consumed=recovery_result_already_consumed,
        beacon_frozen_due_to_access_expiry=beacon_frozen_due_to_access_expiry,
        evidence_reference_ids=("recovery-evidence-1",),
    )


def _eligibility_context(
    *,
    account_id: str = "account-1",
    beacon_id: str | None = "beacon-1",
    lifecycle_status: NotificationBeaconLifecycleStatus = NotificationBeaconLifecycleStatus.ACTIVE,
    entitlement_status: NotificationEntitlementStatus = NotificationEntitlementStatus.ALLOWED,
    no_new_status_preference_enabled: bool = False,
    no_new_status_frequency_minutes: int | None = None,
    telegram_enabled_by_user: bool = True,
    telegram_target_verified: bool = True,
    telegram_target_available: bool = True,
    max_enabled_by_user: bool = True,
    max_target_verified: bool = True,
    max_target_available: bool = True,
    recovery_grace_evidence: NotificationRecoveryGraceEvidence | None = None,
) -> NotificationEligibilityContext:
    if recovery_grace_evidence is None:
        recovery_grace_evidence = _recovery_evidence()
    return NotificationEligibilityContext(
        account_id=account_id,
        beacon_id=beacon_id,
        beacon_lifecycle_status=lifecycle_status,
        beacon_lifecycle_reference_id="beacon-lifecycle-1",
        entitlement_status=entitlement_status,
        entitlement_decision_reference_id="entitlement-1",
        no_new_status_preference_enabled=no_new_status_preference_enabled,
        no_new_status_frequency_minutes=no_new_status_frequency_minutes,
        channel_evidence=(
            _channel_evidence(
                channel_class=NotificationChannelClass.TELEGRAM,
                enabled_by_user=telegram_enabled_by_user,
                target_verified=telegram_target_verified,
                target_available=telegram_target_available,
            ),
            _channel_evidence(
                channel_class=NotificationChannelClass.MAX,
                enabled_by_user=max_enabled_by_user,
                target_verified=max_target_verified,
                target_available=max_target_available,
            ),
            _web_evidence(),
        ),
        recovery_grace_evidence=recovery_grace_evidence,
        evidence_reference_ids=("context-evidence-1",),
    )


def _eligibility_decision(
    *,
    family: NotificationSourceFamily = NotificationSourceFamily.NEW_LISTINGS_FOUND,
    account_id: str = "account-1",
    beacon_id: str | None = "beacon-1",
    lifecycle_status: NotificationBeaconLifecycleStatus = NotificationBeaconLifecycleStatus.ACTIVE,
    entitlement_status: NotificationEntitlementStatus = NotificationEntitlementStatus.ALLOWED,
    no_new_status_preference_enabled: bool = False,
    no_new_status_frequency_minutes: int | None = None,
    telegram_enabled_by_user: bool = True,
    telegram_target_verified: bool = True,
    telegram_target_available: bool = True,
    max_enabled_by_user: bool = True,
    max_target_verified: bool = True,
    max_target_available: bool = True,
    recovery_grace_evidence: NotificationRecoveryGraceEvidence | None = None,
) -> NotificationEligibilityDecision:
    if family is NotificationSourceFamily.NO_NEW_LISTINGS_STATUS:
        source_event = _source_event(
            family=family,
            account_id=account_id,
            beacon_id=beacon_id,
            listing_count=0,
            safe_listing_reference_ids=(),
        )
    else:
        source_event = _source_event(family=family, account_id=account_id, beacon_id=beacon_id)
    intake_decision = _source_intake_decision(source_event)
    return evaluate_notification_eligibility(
        decision_id="eligibility-1",
        source_intake_decision=intake_decision,
        context=_eligibility_context(
            account_id=account_id,
            beacon_id=beacon_id,
            lifecycle_status=lifecycle_status,
            entitlement_status=entitlement_status,
            no_new_status_preference_enabled=no_new_status_preference_enabled,
            no_new_status_frequency_minutes=no_new_status_frequency_minutes,
            telegram_enabled_by_user=telegram_enabled_by_user,
            telegram_target_verified=telegram_target_verified,
            telegram_target_available=telegram_target_available,
            max_enabled_by_user=max_enabled_by_user,
            max_target_verified=max_target_verified,
            max_target_available=max_target_available,
            recovery_grace_evidence=recovery_grace_evidence,
        ),
        evidence_reference_ids=("eligibility-evidence-1",),
    )


def _authorization_scope(
    *,
    audience: NotificationReadAudience = NotificationReadAudience.USER,
    identity_status: NotificationIdentityScopeStatus = NotificationIdentityScopeStatus.VERIFIED,
    authorized: bool = True,
    account_ids: tuple[str, ...] = ("account-1",),
    beacon_ids: tuple[str, ...] = ("beacon-1",),
) -> NotificationSecurityAuthorizationScope:
    return NotificationSecurityAuthorizationScope(
        scope_id="scope-1",
        audience=audience,
        identity_status=identity_status,
        authorized=authorized,
        principal_reference_id="principal-1",
        authorized_account_ids=account_ids,
        authorized_beacon_ids=beacon_ids,
        authorization_reference_id="authorization-1",
        evidence_reference_ids=("scope-evidence-1",),
    )


def _content_scope(
    *,
    safety_status: NotificationContentSafetyStatus,
    safe_listing_reference_ids: tuple[str, ...] = (),
    approved_listing_reference_ids: tuple[str, ...] = (),
) -> NotificationSafeContentScope:
    if safety_status is NotificationContentSafetyStatus.APPROVED_SAFE_REFERENCES:
        if not safe_listing_reference_ids and not approved_listing_reference_ids:
            safe_listing_reference_ids = ("listing-1",)
            approved_listing_reference_ids = ("listing-1",)
        elif not safe_listing_reference_ids:
            safe_listing_reference_ids = approved_listing_reference_ids
        elif not approved_listing_reference_ids:
            approved_listing_reference_ids = safe_listing_reference_ids
    return NotificationSafeContentScope(
        content_scope_id="content-1",
        safety_status=safety_status,
        safe_listing_reference_ids=safe_listing_reference_ids,
        approved_listing_reference_ids=approved_listing_reference_ids,
        evidence_reference_ids=("content-evidence-1",),
        fetch_authorized=False,
        enrichment_authorized=False,
        provider_rendering_authorized=False,
    )


def _snapshot(
    *,
    account_id: str = "account-1",
    beacon_id: str | None = "beacon-1",
) -> NotificationHistoricalEvidenceSnapshot:
    return NotificationHistoricalEvidenceSnapshot(
        snapshot_id="snapshot-1",
        account_id=account_id,
        beacon_id=beacon_id,
        entitlement_decision_reference_id="entitlement-1",
        beacon_lifecycle_reference_id="beacon-lifecycle-1",
        recovery_obligation_reference_id="recovery-obligation-1",
        evidence_reference_ids=("snapshot-evidence-1",),
        mutation_authorized=False,
    )


def _public_fingerprint(decision: NotificationSecurityPrivacyDecision) -> tuple[object, ...]:
    return (
        decision.authority,
        decision.action,
        decision.status,
        decision.public_error_class,
        decision.authorization_scope_id,
        decision.account_id,
        decision.beacon_id,
        decision.eligibility_decision_id,
        decision.channel_class,
        decision.target_reference_id,
        decision.safe_listing_reference_ids,
        decision.historical_evidence_snapshot,
        decision.protected_read_authorized,
        decision.outbox_effect_authorized,
        decision.channel_delivery_authorized,
        decision.recovery_grace_applied,
        decision.suppressed_by_user,
        decision.historical_entitlement_evidence_rewritten,
        decision.historical_beacon_evidence_rewritten,
        decision.historical_evidence_mutation_authorized,
        decision.provider_mapping_authorized,
        decision.provider_execution_authorized,
        decision.read_tracking_authorized,
        decision.click_tracking_authorized,
        decision.retention_authorized,
        decision.reason_codes,
        decision.evidence_reference_ids,
    )


def _assert_non_authority_flags_false(decision: NotificationSecurityPrivacyDecision) -> None:
    assert decision.historical_entitlement_evidence_rewritten is False
    assert decision.historical_beacon_evidence_rewritten is False
    assert decision.historical_evidence_mutation_authorized is False
    assert decision.provider_mapping_authorized is False
    assert decision.provider_execution_authorized is False
    assert decision.read_tracking_authorized is False
    assert decision.click_tracking_authorized is False
    assert decision.retention_authorized is False


def _channel_gate(
    eligibility_decision: NotificationEligibilityDecision,
    channel_class: NotificationChannelClass,
) -> NotificationChannelGateDecision:
    for gate in eligibility_decision.channel_gate_decisions:
        if gate.channel_class is channel_class:
            return gate
    raise AssertionError(f"missing gate for {channel_class}")


def _foreign_gate_like(gate: NotificationChannelGateDecision) -> NotificationChannelGateDecision:
    return NotificationChannelGateDecision(
        channel_class=gate.channel_class,
        status=gate.status,
        push_eligible=gate.push_eligible,
        target_reference_id=gate.target_reference_id,
        reason_codes=gate.reason_codes,
        evidence_reference_ids=gate.evidence_reference_ids,
    )


@pytest.mark.parametrize(
    "audience",
    [
        NotificationReadAudience.USER,
        NotificationReadAudience.ADMIN,
        NotificationReadAudience.SUPPORT,
    ],
)
def test_verified_scoped_protected_read_authorizes_user_admin_and_support(
    audience: NotificationReadAudience,
) -> None:
    content_scope = _content_scope(safety_status=NotificationContentSafetyStatus.EMPTY)
    if audience is NotificationReadAudience.USER:
        assert content_scope.safe_listing_reference_ids == ()

    decision = evaluate_notification_security_privacy(
        decision_id=f"security-read-{audience.value.lower()}",
        action=NotificationProtectedAction.PROTECTED_READ,
        authorization_scope=_authorization_scope(audience=audience),
        content_scope=content_scope,
        historical_evidence_snapshot=_snapshot(),
        eligibility_decision=None,
        channel_gate_decision=None,
        evidence_reference_ids=("security-evidence-1",),
    )

    assert decision.status is NotificationSecurityDecisionStatus.AUTHORIZED_READ
    assert decision.public_error_class is NotificationSecurityPublicErrorClass.NONE
    assert decision.protected_read_authorized is True
    assert decision.outbox_effect_authorized is False
    assert decision.channel_delivery_authorized is False
    assert decision.historical_evidence_snapshot is not None
    assert decision.safe_listing_reference_ids is content_scope.safe_listing_reference_ids
    assert decision.safe_listing_reference_ids == ()
    assert decision.channel_class is NotificationChannelClass.WEB_STATUS_READ_MODEL
    assert decision.target_reference_id is None
    _assert_non_authority_flags_false(decision)


def test_approved_safe_references_preserve_order_and_allow_admin_and_support_reads() -> None:
    safe_refs = ("listing-3", "listing-1", "listing-2")
    content_scope = _content_scope(
        safety_status=NotificationContentSafetyStatus.APPROVED_SAFE_REFERENCES,
        safe_listing_reference_ids=safe_refs,
        approved_listing_reference_ids=("listing-1", "listing-2", "listing-3", "listing-4"),
    )

    for audience in (NotificationReadAudience.ADMIN, NotificationReadAudience.SUPPORT):
        decision = evaluate_notification_security_privacy(
            decision_id=f"security-read-approved-{audience.value.lower()}",
            action=NotificationProtectedAction.PROTECTED_READ,
            authorization_scope=_authorization_scope(audience=audience),
            content_scope=content_scope,
            historical_evidence_snapshot=_snapshot(),
            eligibility_decision=None,
            channel_gate_decision=None,
            evidence_reference_ids=("security-evidence-2",),
        )

        assert decision.status is NotificationSecurityDecisionStatus.AUTHORIZED_READ
        assert decision.safe_listing_reference_ids == safe_refs
        assert decision.safe_listing_reference_ids is content_scope.safe_listing_reference_ids
        assert decision.historical_evidence_snapshot is not None
        _assert_non_authority_flags_false(decision)


def test_authorization_failure_precedes_unsafe_content_disclosure() -> None:
    decision = evaluate_notification_security_privacy(
        decision_id="security-authz-unsafe-1",
        action=NotificationProtectedAction.PROTECTED_READ,
        authorization_scope=_authorization_scope(
            identity_status=NotificationIdentityScopeStatus.UNAUTHORIZED,
            authorized=False,
            account_ids=(),
            beacon_ids=(),
        ),
        content_scope=_content_scope(
            safety_status=NotificationContentSafetyStatus.UNSAFE_OR_UNAPPROVED
        ),
        historical_evidence_snapshot=_snapshot(),
        eligibility_decision=None,
        channel_gate_decision=None,
        evidence_reference_ids=("security-evidence-3",),
    )

    assert decision.status is NotificationSecurityDecisionStatus.BLOCKED_NOT_AUTHORIZED_OR_NOT_FOUND
    assert (
        decision.public_error_class
        is NotificationSecurityPublicErrorClass.NOT_AUTHORIZED_OR_NOT_FOUND
    )
    assert decision.historical_evidence_snapshot is None
    assert decision.account_id is None
    assert decision.beacon_id is None
    assert decision.safe_listing_reference_ids == ()
    _assert_non_authority_flags_false(decision)


def test_ambiguous_identity_blocks_without_leaking_scope() -> None:
    decision = evaluate_notification_security_privacy(
        decision_id="security-ambiguous-identity-1",
        action=NotificationProtectedAction.OUTBOX_EFFECT,
        authorization_scope=_authorization_scope(
            identity_status=NotificationIdentityScopeStatus.AMBIGUOUS,
            authorized=False,
            account_ids=(),
            beacon_ids=(),
        ),
        content_scope=_content_scope(
            safety_status=NotificationContentSafetyStatus.APPROVED_SAFE_REFERENCES
        ),
        historical_evidence_snapshot=_snapshot(),
        eligibility_decision=_eligibility_decision(),
        channel_gate_decision=None,
        evidence_reference_ids=("security-evidence-4",),
    )

    assert decision.status is NotificationSecurityDecisionStatus.BLOCKED_AMBIGUOUS
    assert decision.public_error_class is NotificationSecurityPublicErrorClass.REQUEST_BLOCKED
    assert decision.historical_evidence_snapshot is None
    assert decision.account_id is None
    assert decision.beacon_id is None


def test_account_outside_scope_and_beacon_outside_scope_return_same_safe_public_result() -> None:
    unauthorized_decision = evaluate_notification_security_privacy(
        decision_id="security-unauthorized-1",
        action=NotificationProtectedAction.OUTBOX_EFFECT,
        authorization_scope=_authorization_scope(
            identity_status=NotificationIdentityScopeStatus.UNAUTHORIZED,
            authorized=False,
            account_ids=(),
            beacon_ids=(),
        ),
        content_scope=_content_scope(
            safety_status=NotificationContentSafetyStatus.APPROVED_SAFE_REFERENCES
        ),
        historical_evidence_snapshot=_snapshot(),
        eligibility_decision=_eligibility_decision(),
        channel_gate_decision=None,
        evidence_reference_ids=("security-evidence-5",),
    )
    account_mismatch_decision = evaluate_notification_security_privacy(
        decision_id="security-account-mismatch-1",
        action=NotificationProtectedAction.OUTBOX_EFFECT,
        authorization_scope=_authorization_scope(),
        content_scope=_content_scope(
            safety_status=NotificationContentSafetyStatus.APPROVED_SAFE_REFERENCES
        ),
        historical_evidence_snapshot=_snapshot(account_id="account-2"),
        eligibility_decision=_eligibility_decision(),
        channel_gate_decision=None,
        evidence_reference_ids=("security-evidence-5",),
    )
    beacon_mismatch_decision = evaluate_notification_security_privacy(
        decision_id="security-beacon-mismatch-1",
        action=NotificationProtectedAction.OUTBOX_EFFECT,
        authorization_scope=_authorization_scope(),
        content_scope=_content_scope(
            safety_status=NotificationContentSafetyStatus.APPROVED_SAFE_REFERENCES
        ),
        historical_evidence_snapshot=_snapshot(beacon_id="beacon-2"),
        eligibility_decision=_eligibility_decision(beacon_id="beacon-2"),
        channel_gate_decision=None,
        evidence_reference_ids=("security-evidence-5",),
    )

    assert (
        unauthorized_decision.status
        is NotificationSecurityDecisionStatus.BLOCKED_NOT_AUTHORIZED_OR_NOT_FOUND
    )
    assert (
        account_mismatch_decision.status
        is NotificationSecurityDecisionStatus.BLOCKED_NOT_AUTHORIZED_OR_NOT_FOUND
    )
    assert (
        beacon_mismatch_decision.status
        is NotificationSecurityDecisionStatus.BLOCKED_NOT_AUTHORIZED_OR_NOT_FOUND
    )
    assert _public_fingerprint(unauthorized_decision) == _public_fingerprint(
        account_mismatch_decision
    )
    assert _public_fingerprint(unauthorized_decision) == _public_fingerprint(
        beacon_mismatch_decision
    )


def test_empty_safe_content_allows_protected_read_but_not_outbox_effect() -> None:
    read_decision = evaluate_notification_security_privacy(
        decision_id="security-empty-read-1",
        action=NotificationProtectedAction.PROTECTED_READ,
        authorization_scope=_authorization_scope(),
        content_scope=_content_scope(safety_status=NotificationContentSafetyStatus.EMPTY),
        historical_evidence_snapshot=_snapshot(),
        eligibility_decision=None,
        channel_gate_decision=None,
        evidence_reference_ids=("security-evidence-6",),
    )
    outbox_decision = evaluate_notification_security_privacy(
        decision_id="security-empty-outbox-1",
        action=NotificationProtectedAction.OUTBOX_EFFECT,
        authorization_scope=_authorization_scope(),
        content_scope=_content_scope(safety_status=NotificationContentSafetyStatus.EMPTY),
        historical_evidence_snapshot=_snapshot(),
        eligibility_decision=_eligibility_decision(),
        channel_gate_decision=None,
        evidence_reference_ids=("security-evidence-6",),
    )

    assert read_decision.status is NotificationSecurityDecisionStatus.AUTHORIZED_READ
    assert outbox_decision.status is NotificationSecurityDecisionStatus.BLOCKED_UNSAFE_CONTENT


def test_unapproved_and_ambiguous_content_are_blocked() -> None:
    unapproved_decision = evaluate_notification_security_privacy(
        decision_id="security-unapproved-content-1",
        action=NotificationProtectedAction.OUTBOX_EFFECT,
        authorization_scope=_authorization_scope(),
        content_scope=_content_scope(
            safety_status=NotificationContentSafetyStatus.UNSAFE_OR_UNAPPROVED
        ),
        historical_evidence_snapshot=_snapshot(),
        eligibility_decision=_eligibility_decision(),
        channel_gate_decision=None,
        evidence_reference_ids=("security-evidence-7",),
    )
    ambiguous_decision = evaluate_notification_security_privacy(
        decision_id="security-ambiguous-content-1",
        action=NotificationProtectedAction.OUTBOX_EFFECT,
        authorization_scope=_authorization_scope(),
        content_scope=_content_scope(safety_status=NotificationContentSafetyStatus.AMBIGUOUS),
        historical_evidence_snapshot=_snapshot(),
        eligibility_decision=_eligibility_decision(),
        channel_gate_decision=None,
        evidence_reference_ids=("security-evidence-8",),
    )

    assert unapproved_decision.status is NotificationSecurityDecisionStatus.BLOCKED_UNSAFE_CONTENT
    assert ambiguous_decision.status is NotificationSecurityDecisionStatus.BLOCKED_AMBIGUOUS


def test_ordinary_eligible_outbox_effect_and_recovery_grace_effects() -> None:
    approved_content = _content_scope(
        safety_status=NotificationContentSafetyStatus.APPROVED_SAFE_REFERENCES,
        safe_listing_reference_ids=("listing-1", "listing-2"),
        approved_listing_reference_ids=("listing-1", "listing-2", "listing-3"),
    )
    ordinary_decision = evaluate_notification_security_privacy(
        decision_id="security-outbox-eligible-1",
        action=NotificationProtectedAction.OUTBOX_EFFECT,
        authorization_scope=_authorization_scope(),
        content_scope=approved_content,
        historical_evidence_snapshot=_snapshot(),
        eligibility_decision=_eligibility_decision(),
        channel_gate_decision=None,
        evidence_reference_ids=("security-evidence-9",),
    )
    recovery_decision = evaluate_notification_security_privacy(
        decision_id="security-outbox-recovery-1",
        action=NotificationProtectedAction.OUTBOX_EFFECT,
        authorization_scope=_authorization_scope(),
        content_scope=approved_content,
        historical_evidence_snapshot=_snapshot(),
        eligibility_decision=_eligibility_decision(
            family=NotificationSourceFamily.RECOVERY_SCAN_COMPLETED,
            entitlement_status=NotificationEntitlementStatus.EXPIRED,
            recovery_grace_evidence=_recovery_evidence(
                problem_began_while_access_active=True,
                recovery_obligation_reference_id="recovery-obligation-1",
            ),
        ),
        channel_gate_decision=None,
        evidence_reference_ids=("security-evidence-9",),
    )

    assert ordinary_decision.status is NotificationSecurityDecisionStatus.AUTHORIZED_EFFECT
    assert ordinary_decision.outbox_effect_authorized is True
    assert ordinary_decision.recovery_grace_applied is False
    assert recovery_decision.status is NotificationSecurityDecisionStatus.AUTHORIZED_RECOVERY_GRACE
    assert recovery_decision.outbox_effect_authorized is True
    assert recovery_decision.recovery_grace_applied is True
    assert (
        recovery_decision.safe_listing_reference_ids is approved_content.safe_listing_reference_ids
    )


def test_denied_entitlement_cannot_manufacture_recovery_grace() -> None:
    decision = evaluate_notification_security_privacy(
        decision_id="security-denied-entitlement-1",
        action=NotificationProtectedAction.OUTBOX_EFFECT,
        authorization_scope=_authorization_scope(),
        content_scope=_content_scope(
            safety_status=NotificationContentSafetyStatus.APPROVED_SAFE_REFERENCES,
            safe_listing_reference_ids=("listing-1",),
            approved_listing_reference_ids=("listing-1",),
        ),
        historical_evidence_snapshot=_snapshot(),
        eligibility_decision=_eligibility_decision(
            family=NotificationSourceFamily.RECOVERY_SCAN_COMPLETED,
            entitlement_status=NotificationEntitlementStatus.DENIED,
            recovery_grace_evidence=_recovery_evidence(
                problem_began_while_access_active=True,
                recovery_obligation_reference_id="recovery-obligation-1",
            ),
        ),
        channel_gate_decision=None,
        evidence_reference_ids=("security-evidence-10",),
    )

    assert decision.status is NotificationSecurityDecisionStatus.BLOCKED_AMBIGUOUS
    assert decision.recovery_grace_applied is False
    assert decision.outbox_effect_authorized is False


def test_ambiguous_lifecycle_or_entitlement_blocks_effect() -> None:
    decision = evaluate_notification_security_privacy(
        decision_id="security-ambiguous-lifecycle-1",
        action=NotificationProtectedAction.OUTBOX_EFFECT,
        authorization_scope=_authorization_scope(),
        content_scope=_content_scope(
            safety_status=NotificationContentSafetyStatus.APPROVED_SAFE_REFERENCES,
            safe_listing_reference_ids=("listing-1",),
            approved_listing_reference_ids=("listing-1",),
        ),
        historical_evidence_snapshot=_snapshot(),
        eligibility_decision=_eligibility_decision(
            lifecycle_status=NotificationBeaconLifecycleStatus.AMBIGUOUS,
            entitlement_status=NotificationEntitlementStatus.AMBIGUOUS,
        ),
        channel_gate_decision=None,
        evidence_reference_ids=("security-evidence-11",),
    )

    assert decision.status is NotificationSecurityDecisionStatus.BLOCKED_AMBIGUOUS
    assert decision.outbox_effect_authorized is False
    assert decision.recovery_grace_applied is False


def test_user_preference_suppression_blocks_effect_without_becoming_delivery_failure() -> None:
    decision = evaluate_notification_security_privacy(
        decision_id="security-suppression-1",
        action=NotificationProtectedAction.OUTBOX_EFFECT,
        authorization_scope=_authorization_scope(),
        content_scope=_content_scope(
            safety_status=NotificationContentSafetyStatus.APPROVED_SAFE_REFERENCES,
            safe_listing_reference_ids=("listing-1",),
            approved_listing_reference_ids=("listing-1",),
        ),
        historical_evidence_snapshot=_snapshot(),
        eligibility_decision=_eligibility_decision(
            family=NotificationSourceFamily.NO_NEW_LISTINGS_STATUS,
            no_new_status_preference_enabled=False,
        ),
        channel_gate_decision=None,
        evidence_reference_ids=("security-evidence-12",),
    )

    assert decision.status is NotificationSecurityDecisionStatus.SUPPRESSED_BY_USER
    assert decision.suppressed_by_user is True
    assert decision.outbox_effect_authorized is False
    assert decision.recovery_grace_applied is False


def test_enabled_verified_target_allows_channel_delivery() -> None:
    approved_content = _content_scope(
        safety_status=NotificationContentSafetyStatus.APPROVED_SAFE_REFERENCES,
        safe_listing_reference_ids=("listing-1", "listing-2"),
        approved_listing_reference_ids=("listing-1", "listing-2"),
    )
    eligibility_decision = _eligibility_decision()
    gate = _channel_gate(eligibility_decision, NotificationChannelClass.TELEGRAM)

    decision = evaluate_notification_security_privacy(
        decision_id="security-channel-eligible-1",
        action=NotificationProtectedAction.CHANNEL_DELIVERY,
        authorization_scope=_authorization_scope(),
        content_scope=approved_content,
        historical_evidence_snapshot=_snapshot(),
        eligibility_decision=eligibility_decision,
        channel_gate_decision=gate,
        evidence_reference_ids=("security-evidence-13",),
    )

    assert decision.status is NotificationSecurityDecisionStatus.AUTHORIZED_EFFECT
    assert decision.channel_delivery_authorized is True
    assert decision.outbox_effect_authorized is False
    assert decision.channel_class is NotificationChannelClass.TELEGRAM
    assert decision.target_reference_id == gate.target_reference_id
    assert decision.safe_listing_reference_ids is approved_content.safe_listing_reference_ids


def test_disabled_channel_suppresses_and_unverified_or_unavailable_targets_block() -> None:
    approved_content = _content_scope(
        safety_status=NotificationContentSafetyStatus.APPROVED_SAFE_REFERENCES,
        safe_listing_reference_ids=("listing-1",),
        approved_listing_reference_ids=("listing-1",),
    )
    suppressed_eligibility = _eligibility_decision(telegram_enabled_by_user=False)
    unverified_eligibility = _eligibility_decision(telegram_target_verified=False)
    unavailable_eligibility = _eligibility_decision(telegram_target_available=False)
    suppressed_gate_decision = evaluate_notification_security_privacy(
        decision_id="security-channel-suppressed-1",
        action=NotificationProtectedAction.CHANNEL_DELIVERY,
        authorization_scope=_authorization_scope(),
        content_scope=approved_content,
        historical_evidence_snapshot=_snapshot(),
        eligibility_decision=suppressed_eligibility,
        channel_gate_decision=_channel_gate(
            suppressed_eligibility,
            NotificationChannelClass.TELEGRAM,
        ),
        evidence_reference_ids=("security-evidence-14",),
    )
    unverified_gate_decision = evaluate_notification_security_privacy(
        decision_id="security-channel-unverified-1",
        action=NotificationProtectedAction.CHANNEL_DELIVERY,
        authorization_scope=_authorization_scope(),
        content_scope=approved_content,
        historical_evidence_snapshot=_snapshot(),
        eligibility_decision=unverified_eligibility,
        channel_gate_decision=_channel_gate(
            unverified_eligibility,
            NotificationChannelClass.TELEGRAM,
        ),
        evidence_reference_ids=("security-evidence-14",),
    )
    unavailable_gate_decision = evaluate_notification_security_privacy(
        decision_id="security-channel-unavailable-1",
        action=NotificationProtectedAction.CHANNEL_DELIVERY,
        authorization_scope=_authorization_scope(),
        content_scope=approved_content,
        historical_evidence_snapshot=_snapshot(),
        eligibility_decision=unavailable_eligibility,
        channel_gate_decision=_channel_gate(
            unavailable_eligibility,
            NotificationChannelClass.TELEGRAM,
        ),
        evidence_reference_ids=("security-evidence-14",),
    )

    assert suppressed_gate_decision.status is NotificationSecurityDecisionStatus.SUPPRESSED_BY_USER
    assert suppressed_gate_decision.suppressed_by_user is True
    assert (
        unverified_gate_decision.status
        is NotificationSecurityDecisionStatus.BLOCKED_TARGET_UNVERIFIED
    )
    assert (
        unavailable_gate_decision.status
        is NotificationSecurityDecisionStatus.BLOCKED_TARGET_UNVERIFIED
    )


def test_web_read_model_channel_foreign_gate_and_scope_mismatch_cause_evidence_conflict() -> None:
    approved_content = _content_scope(
        safety_status=NotificationContentSafetyStatus.APPROVED_SAFE_REFERENCES,
        safe_listing_reference_ids=("listing-1",),
        approved_listing_reference_ids=("listing-1",),
    )
    eligibility_decision = _eligibility_decision()
    web_gate = _channel_gate(eligibility_decision, NotificationChannelClass.WEB_STATUS_READ_MODEL)
    foreign_gate = _foreign_gate_like(
        _channel_gate(eligibility_decision, NotificationChannelClass.TELEGRAM)
    )
    mismatch_eligibility = _eligibility_decision()
    mismatch_gate = _channel_gate(mismatch_eligibility, NotificationChannelClass.TELEGRAM)

    web_decision = evaluate_notification_security_privacy(
        decision_id="security-channel-web-1",
        action=NotificationProtectedAction.CHANNEL_DELIVERY,
        authorization_scope=_authorization_scope(),
        content_scope=approved_content,
        historical_evidence_snapshot=_snapshot(),
        eligibility_decision=eligibility_decision,
        channel_gate_decision=web_gate,
        evidence_reference_ids=("security-evidence-15",),
    )
    foreign_decision = evaluate_notification_security_privacy(
        decision_id="security-channel-foreign-1",
        action=NotificationProtectedAction.CHANNEL_DELIVERY,
        authorization_scope=_authorization_scope(),
        content_scope=approved_content,
        historical_evidence_snapshot=_snapshot(),
        eligibility_decision=eligibility_decision,
        channel_gate_decision=foreign_gate,
        evidence_reference_ids=("security-evidence-15",),
    )
    mismatch_decision = evaluate_notification_security_privacy(
        decision_id="security-channel-mismatch-1",
        action=NotificationProtectedAction.CHANNEL_DELIVERY,
        authorization_scope=_authorization_scope(
            account_ids=("account-2",),
        ),
        content_scope=approved_content,
        historical_evidence_snapshot=_snapshot(account_id="account-2"),
        eligibility_decision=mismatch_eligibility,
        channel_gate_decision=mismatch_gate,
        evidence_reference_ids=("security-evidence-15",),
    )

    assert web_decision.status is NotificationSecurityDecisionStatus.BLOCKED_EVIDENCE_CONFLICT
    assert foreign_decision.status is NotificationSecurityDecisionStatus.BLOCKED_EVIDENCE_CONFLICT
    assert mismatch_decision.status is NotificationSecurityDecisionStatus.BLOCKED_EVIDENCE_CONFLICT


def test_historical_snapshot_object_and_reference_identities_are_preserved() -> None:
    content_scope = _content_scope(
        safety_status=NotificationContentSafetyStatus.APPROVED_SAFE_REFERENCES,
        safe_listing_reference_ids=("listing-2", "listing-1"),
        approved_listing_reference_ids=("listing-1", "listing-2"),
    )
    snapshot = _snapshot()
    decision = evaluate_notification_security_privacy(
        decision_id="security-preserve-1",
        action=NotificationProtectedAction.OUTBOX_EFFECT,
        authorization_scope=_authorization_scope(),
        content_scope=content_scope,
        historical_evidence_snapshot=snapshot,
        eligibility_decision=_eligibility_decision(),
        channel_gate_decision=None,
        evidence_reference_ids=("security-evidence-16",),
    )

    assert decision.historical_evidence_snapshot is snapshot
    assert decision.safe_listing_reference_ids is content_scope.safe_listing_reference_ids
    assert decision.safe_listing_reference_ids == ("listing-2", "listing-1")


def test_historical_evidence_cannot_be_mutated_and_tuples_are_immutable() -> None:
    snapshot = _snapshot()
    content_scope = _content_scope(
        safety_status=NotificationContentSafetyStatus.APPROVED_SAFE_REFERENCES,
        safe_listing_reference_ids=("listing-1",),
        approved_listing_reference_ids=("listing-1",),
    )
    decision = evaluate_notification_security_privacy(
        decision_id="security-immutable-1",
        action=NotificationProtectedAction.PROTECTED_READ,
        authorization_scope=_authorization_scope(),
        content_scope=content_scope,
        historical_evidence_snapshot=snapshot,
        eligibility_decision=None,
        channel_gate_decision=None,
        evidence_reference_ids=("security-evidence-17",),
    )

    with raises(FrozenInstanceError):
        snapshot.account_id = "account-2"  # type: ignore[misc]
    with raises(TypeError):
        content_scope.safe_listing_reference_ids[0] = "other"  # type: ignore[index]
    with raises(FrozenInstanceError):
        decision.safe_listing_reference_ids += ("other",)  # type: ignore[misc]


def test_all_non_authority_flags_remain_false() -> None:
    decision = evaluate_notification_security_privacy(
        decision_id="security-flags-1",
        action=NotificationProtectedAction.OUTBOX_EFFECT,
        authorization_scope=_authorization_scope(
            identity_status=NotificationIdentityScopeStatus.UNAUTHORIZED,
            authorized=False,
            account_ids=(),
            beacon_ids=(),
        ),
        content_scope=_content_scope(
            safety_status=NotificationContentSafetyStatus.APPROVED_SAFE_REFERENCES
        ),
        historical_evidence_snapshot=_snapshot(),
        eligibility_decision=_eligibility_decision(),
        channel_gate_decision=None,
        evidence_reference_ids=("security-evidence-18",),
    )

    _assert_non_authority_flags_false(decision)
    assert decision.protected_read_authorized is False
    assert decision.outbox_effect_authorized is False
    assert decision.channel_delivery_authorized is False
    assert decision.recovery_grace_applied is False
    assert decision.suppressed_by_user is False


def test_dataclasses_and_tuple_fields_are_immutable() -> None:
    scope = _authorization_scope()
    content_scope = _content_scope(
        safety_status=NotificationContentSafetyStatus.APPROVED_SAFE_REFERENCES,
        safe_listing_reference_ids=("listing-1", "listing-2"),
        approved_listing_reference_ids=("listing-1", "listing-2"),
    )

    with raises(FrozenInstanceError):
        scope.authorized_account_ids += ("account-2",)  # type: ignore[misc]
    with raises(FrozenInstanceError):
        content_scope.approved_listing_reference_ids += ("listing-3",)  # type: ignore[misc]
    with raises(TypeError):
        content_scope.approved_listing_reference_ids[0] = "other"  # type: ignore[index]
