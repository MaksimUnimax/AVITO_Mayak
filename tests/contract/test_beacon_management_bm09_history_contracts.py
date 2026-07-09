from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from mayak.modules.beacon_management.contracts import (
    Beacon,
    BeaconAccessTier,
    BeaconActorContext,
    BeaconActorKind,
    BeaconAuthorizationDecision,
    BeaconAuthorizationOutcome,
    BeaconConfigurationEvidenceRetentionDecision,
    BeaconConfigurationRetentionBoundary,
    BeaconConfigurationStoragePolicyOutcome,
    BeaconCurrentConfiguration,
    BeaconCurrentConfigurationAuthorityStatus,
    BeaconEffectiveEntitlementSnapshot,
    BeaconEntitlementEvidenceFreshnessStatus,
    BeaconEntitlementEvidenceReference,
    BeaconHistoryEntry,
    BeaconHistoryOutcome,
    BeaconLifecycleActionKind,
    BeaconLifecycleEntitlementDecision,
    BeaconLifecycleEntitlementOutcome,
    BeaconLifecycleState,
    BeaconNameOrigin,
    BeaconNamingMetadata,
    BeaconOwnershipDecision,
    BeaconParserEvidenceReference,
    BeaconParserOutcomeStatus,
    BeaconProtectedAction,
    BeaconSourceUrl,
    BeaconTariffPolicyBand,
    ExtractedSearchConfigurationSnapshot,
)

_NOW = datetime(2026, 7, 9, 10, 0, tzinfo=timezone.utc)
_ACCOUNT_ID = "acct-bm09-own-001"
_FOREIGN_ACCOUNT_ID = "acct-bm09-foreign-001"
_BEACON_ID = "beacon-bm09-001"


def _source_url(beacon_id: str) -> BeaconSourceUrl:
    return BeaconSourceUrl(
        submitted_url=f"https://example.invalid/search?query={beacon_id}&city=synthetic",
        evidence_reference=f"source-url-{beacon_id}",
        submitted_at=_NOW,
        source_channel="user-submitted",
        submitted_by_label="synthetic-user",
    )


def _snapshot(beacon_id: str) -> ExtractedSearchConfigurationSnapshot:
    return ExtractedSearchConfigurationSnapshot(
        snapshot_id=f"snapshot-{beacon_id}",
        parser_outcome_status=BeaconParserOutcomeStatus.CLEAN,
        accepted_as_clean=True,
        normalized_filter_values=("city=synthetic",),
        unsupported_parameters=(),
        warning_codes=(),
        evidence_reference=f"snapshot-evidence-{beacon_id}",
        parser_evidence_reference=BeaconParserEvidenceReference(
            evidence_reference=f"parser-evidence-{beacon_id}",
        ),
    )


def _configuration(
    *,
    beacon_id: str,
    lifecycle_state: BeaconLifecycleState,
    source_url: BeaconSourceUrl,
) -> BeaconCurrentConfiguration:
    return BeaconCurrentConfiguration(
        beacon_id=beacon_id,
        account_id=_ACCOUNT_ID,
        source_url=source_url,
        accepted_snapshot=_snapshot(beacon_id),
        overrides=(),
        current_revision_id=f"revision-{beacon_id}",
        display_name=f"Synthetic {beacon_id}",
        lifecycle_state=lifecycle_state,
        retained_evidence_references=(f"retained-{beacon_id}",),
        previous_user_facing_revision_ids=(),
    )


def _beacon(
    *,
    beacon_id: str,
    lifecycle_state: BeaconLifecycleState,
    restorable: bool,
    counts_toward_active_limit: bool,
    history_entry: BeaconHistoryEntry,
    source_url: BeaconSourceUrl | None = None,
) -> Beacon:
    source_url = source_url or _source_url(beacon_id)
    return Beacon(
        beacon_id=beacon_id,
        account_id=_ACCOUNT_ID,
        naming=BeaconNamingMetadata(
            display_name=f"Synthetic {beacon_id}",
            name_origin=BeaconNameOrigin.USER_PROVIDED,
            source_title="synthetic source",
            source_context_reference=f"context-{beacon_id}",
            default_name="synthetic-default-name",
        ),
        source_url=source_url,
        current_configuration=_configuration(
            beacon_id=beacon_id,
            lifecycle_state=lifecycle_state,
            source_url=source_url,
        ),
        lifecycle_state=lifecycle_state,
        restorable=restorable,
        counts_toward_active_limit=counts_toward_active_limit,
        history_entries=(history_entry,),
    )


def _history_entry(
    *,
    beacon_id: str,
    outcome: BeaconHistoryOutcome,
    restorable: bool,
    reason: str,
) -> BeaconHistoryEntry:
    return BeaconHistoryEntry(
        history_entry_id=f"history-{beacon_id}-{outcome.value.lower()}",
        beacon_id=beacon_id,
        account_id=_ACCOUNT_ID,
        outcome=outcome,
        restorable=restorable,
        recorded_at=_NOW,
        minimal_snapshot_reference=f"minimal-snapshot-{beacon_id}",
        reason=reason,
        counts_toward_active_limit=False,
    )


def _fresh_entitlement_snapshot(*, active_beacon_count: int) -> BeaconEffectiveEntitlementSnapshot:
    entitlement_evidence_reference = BeaconEntitlementEvidenceReference(
        evidence_reference="entitlement-evidence-bm09-001",
        source_reference="entitlement-source-bm09-001",
        freshness_status=BeaconEntitlementEvidenceFreshnessStatus.FRESH,
        freshness_reference="freshness-ref-bm09-001",
    )
    tariff_policy_band = BeaconTariffPolicyBand(
        access_tier=BeaconAccessTier.BASIC,
        active_beacon_limit=5,
        minimum_interval_minutes=5,
        interval_step_minutes=5,
        country_wide_allowed=True,
        country_wide_city_required=False,
    )
    return BeaconEffectiveEntitlementSnapshot(
        snapshot_reference="snapshot-bm09-entitlement-001",
        beacon_source_reference="beacon-source-bm09-001",
        entitlement_source_reference=entitlement_evidence_reference.source_reference,
        entitlement_evidence_reference=entitlement_evidence_reference,
        tariff_policy_band=tariff_policy_band,
        effective_outcome=BeaconLifecycleEntitlementOutcome.ALLOWED,
        active_beacon_count=active_beacon_count,
        archived_beacon_count=1,
        history_beacon_count=1,
        deleted_beacon_count=1,
        requested_interval_minutes=5,
        requested_country_wide=False,
        provenance_reference="provenance-bm09-001",
    )


def _allowed_resume_decision(*, active_beacon_count: int) -> BeaconLifecycleEntitlementDecision:
    effective_entitlement_snapshot = _fresh_entitlement_snapshot(
        active_beacon_count=active_beacon_count
    )
    entitlement_evidence_reference = effective_entitlement_snapshot.entitlement_evidence_reference
    return BeaconLifecycleEntitlementDecision(
        decision_id="decision-bm09-resume-allowed-001",
        beacon_id=_BEACON_ID,
        account_id=_ACCOUNT_ID,
        action_kind=BeaconLifecycleActionKind.RESUME,
        outcome=BeaconLifecycleEntitlementOutcome.ALLOWED,
        beacon_source_reference=effective_entitlement_snapshot.beacon_source_reference,
        entitlement_evidence_reference=entitlement_evidence_reference,
        effective_entitlement_snapshot=effective_entitlement_snapshot,
        requested_interval_minutes=5,
        active_beacon_count=active_beacon_count,
        archived_beacon_count=1,
        history_beacon_count=1,
        deleted_beacon_count=1,
        requested_country_wide=False,
        entitlement_recheck_reference="entitlement-recheck-bm09-001",
    )


def test_bm09_restore_is_allowed_only_for_authorized_owner_with_fresh_entitlement() -> None:
    actor_context = BeaconActorContext(
        actor_context_id="actor-bm09-owner-001",
        actor_kind=BeaconActorKind.ACCOUNT_OWNER,
        is_verified=True,
        account_id=_ACCOUNT_ID,
        actor_reference_id="actor-ref-bm09-owner-001",
    )
    authorization = BeaconAuthorizationDecision(
        decision_id="decision-bm09-restore-authz-001",
        protected_action=BeaconProtectedAction.RESTORE_BEACON,
        actor_context=actor_context,
        beacon_id=_BEACON_ID,
        beacon_account_id=_ACCOUNT_ID,
        outcome=BeaconAuthorizationOutcome.ALLOWED,
        safe_reason_code="RESTORE_ALLOWED",
        reason="Verified owner can restore a non-permanently deleted Beacon.",
    )
    entitlement = _allowed_resume_decision(active_beacon_count=4)

    assert authorization.outcome is BeaconAuthorizationOutcome.ALLOWED
    assert authorization.existence_sensitive_detail is None
    assert entitlement.outcome is BeaconLifecycleEntitlementOutcome.ALLOWED
    assert entitlement.effective_entitlement_snapshot is not None
    assert entitlement.effective_entitlement_snapshot.active_beacon_count == 4
    assert entitlement.effective_entitlement_snapshot.archived_beacon_count == 1
    assert entitlement.effective_entitlement_snapshot.history_beacon_count == 1
    assert entitlement.effective_entitlement_snapshot.deleted_beacon_count == 1


def test_bm09_restore_from_history_preserves_source_url_and_current_configuration() -> None:
    archived_history_entry = _history_entry(
        beacon_id="beacon-bm09-archive-001",
        outcome=BeaconHistoryOutcome.ARCHIVED,
        restorable=True,
        reason="Archived Beacon remains a semantic history item.",
    )
    archived_beacon = _beacon(
        beacon_id="beacon-bm09-archive-001",
        lifecycle_state=BeaconLifecycleState.ARCHIVED,
        restorable=True,
        counts_toward_active_limit=False,
        history_entry=archived_history_entry,
    )
    restored_configuration = archived_beacon.current_configuration.model_copy(
        update={"lifecycle_state": BeaconLifecycleState.ACTIVE}
    )
    restored_beacon = Beacon.model_validate(
        archived_beacon.model_copy(
            update={
                "lifecycle_state": BeaconLifecycleState.ACTIVE,
                "counts_toward_active_limit": True,
                "current_configuration": restored_configuration,
            }
        ).model_dump()
    )

    assert restored_beacon.source_url == archived_beacon.source_url
    assert restored_beacon.current_configuration.source_url == archived_beacon.source_url
    assert restored_beacon.current_configuration.accepted_snapshot == (
        archived_beacon.current_configuration.accepted_snapshot
    )
    assert restored_beacon.lifecycle_state is BeaconLifecycleState.ACTIVE


def test_bm09_restore_is_blocked_for_permanently_deleted_beacon() -> None:
    permanently_deleted_history_entry = _history_entry(
        beacon_id="beacon-bm09-permanent-001",
        outcome=BeaconHistoryOutcome.PERMANENTLY_DELETED,
        restorable=False,
        reason="Permanent delete is terminal.",
    )
    permanently_deleted_beacon = _beacon(
        beacon_id="beacon-bm09-permanent-001",
        lifecycle_state=BeaconLifecycleState.PERMANENTLY_DELETED,
        restorable=False,
        counts_toward_active_limit=False,
        history_entry=permanently_deleted_history_entry,
    )
    foreign_actor_context = BeaconActorContext(
        actor_context_id="actor-bm09-foreign-001",
        actor_kind=BeaconActorKind.ACCOUNT_OWNER,
        is_verified=True,
        account_id=_FOREIGN_ACCOUNT_ID,
        actor_reference_id="actor-ref-bm09-foreign-001",
    )
    blocked_restore = BeaconOwnershipDecision(
        decision_id="decision-bm09-restore-blocked-001",
        protected_action=BeaconProtectedAction.RESTORE_BEACON,
        actor_context=foreign_actor_context,
        beacon_id=permanently_deleted_beacon.beacon_id,
        beacon_account_id=permanently_deleted_beacon.account_id,
        outcome=BeaconAuthorizationOutcome.BLOCKED,
        safe_reason_code="PERMANENT_DELETE_IRREVERSIBLE",
        reason="Foreign actor cannot restore a permanently deleted Beacon.",
    )

    with pytest.raises(
        ValidationError, match="permanently deleted beacon cannot be restorable"
    ):
        Beacon.model_validate(
            permanently_deleted_beacon.model_copy(update={"restorable": True}).model_dump()
        )

    assert blocked_restore.outcome is BeaconAuthorizationOutcome.BLOCKED
    assert blocked_restore.existence_sensitive_detail is None
    assert blocked_restore.foreign_account_existence_sensitive_detail is False
    assert permanently_deleted_beacon.history_entries[0].outcome is (
        BeaconHistoryOutcome.PERMANENTLY_DELETED
    )


@pytest.mark.parametrize(
    "flag_name,expected_message",
    (
        ("notification_sending_claimed", "notification sending claim is forbidden"),
        (
            "billing_payment_tariff_mutation_claimed",
            "billing/payment/tariff mutation claim is forbidden",
        ),
        ("scheduler_runtime_claimed", "scheduler/runtime claim is forbidden"),
        (
            "db_repository_runtime_persistence_claimed",
            "DB/repository/runtime persistence implementation claim is forbidden",
        ),
        (
            "scanrun_listing_history_state_claimed",
            "ScanRun/listing history state claim is forbidden",
        ),
        (
            "parser_filter_catalog_ownership_claimed",
            "Parser/Filter Catalog ownership claim is forbidden",
        ),
        (
            "client_channel_flag_is_authorization_proof",
            "client channel flag is not authorization proof",
        ),
    ),
)
def test_bm09_restore_path_rejects_runtime_notification_and_history_claims(
    flag_name: str,
    expected_message: str,
) -> None:
    decision = _allowed_resume_decision(active_beacon_count=4)
    unsafe_decision = decision.model_copy(update={flag_name: True})

    with pytest.raises(ValidationError, match=expected_message):
        BeaconLifecycleEntitlementDecision.model_validate(unsafe_decision.model_dump())


def test_bm09_permanent_delete_retention_boundary_is_explicit() -> None:
    retention_decision = BeaconConfigurationEvidenceRetentionDecision(
        decision_id="decision-bm09-retention-001",
        beacon_id="beacon-bm09-retention-001",
        account_id=_ACCOUNT_ID,
        authority_status=(
            BeaconCurrentConfigurationAuthorityStatus.MINIMAL_IMMUTABLE_SCAN_AUDIT_EVIDENCE
        ),
        storage_policy_outcome=BeaconConfigurationStoragePolicyOutcome.ALLOWED,
        retention_boundary=(
            BeaconConfigurationRetentionBoundary.MINIMAL_IMMUTABLE_SCAN_AUDIT_EVIDENCE
        ),
        committed_scan_audit_evidence_reference="committed-scan-audit-bm09-001",
        original_current_configuration_reference="original-current-config-bm09-001",
        current_configuration_reference="current-config-bm09-001",
        minimal_immutable_scan_audit_evidence_reference="minimal-scan-audit-bm09-001",
        minimal_committed_evidence_editable=False,
        already_committed_scan_audit_facts_reinterpreted=False,
        physical_delete_or_compaction_claimed=False,
        db_repository_runtime_persistence_claimed=False,
        scanrun_listing_history_state_claimed=False,
        drops_committed_scan_audit_evidence=False,
        provenance_boundary_changed=False,
    )

    assert (
        retention_decision.storage_policy_outcome
        is BeaconConfigurationStoragePolicyOutcome.ALLOWED
    )
    assert retention_decision.physical_delete_or_compaction_claimed is False
    assert retention_decision.db_repository_runtime_persistence_claimed is False
    assert retention_decision.scanrun_listing_history_state_claimed is False
