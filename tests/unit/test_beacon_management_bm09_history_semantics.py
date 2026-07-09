from __future__ import annotations

from datetime import datetime, timezone

from mayak.modules.beacon_management.contracts import (
    Beacon,
    BeaconAccessTier,
    BeaconCurrentConfiguration,
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
    BeaconParserEvidenceReference,
    BeaconParserOutcomeStatus,
    BeaconSourceUrl,
    BeaconTariffPolicyBand,
    ExtractedSearchConfigurationSnapshot,
)

_NOW = datetime(2026, 7, 9, 10, 0, tzinfo=timezone.utc)
_ACCOUNT_ID = "acct-bm09-unit-001"


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


def _beacon(
    *,
    beacon_id: str,
    lifecycle_state: BeaconLifecycleState,
    history_entry: BeaconHistoryEntry,
    restorable: bool,
) -> Beacon:
    source_url = _source_url(beacon_id)
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
        current_configuration=BeaconCurrentConfiguration(
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
        ),
        lifecycle_state=lifecycle_state,
        restorable=restorable,
        counts_toward_active_limit=False,
        history_entries=(history_entry,),
    )


def _fresh_entitlement_decision(active_beacon_count: int) -> BeaconLifecycleEntitlementDecision:
    entitlement_evidence_reference = BeaconEntitlementEvidenceReference(
        evidence_reference="entitlement-evidence-bm09-unit-001",
        source_reference="entitlement-source-bm09-unit-001",
        freshness_status=BeaconEntitlementEvidenceFreshnessStatus.FRESH,
        freshness_reference="freshness-ref-bm09-unit-001",
    )
    tariff_policy_band = BeaconTariffPolicyBand(
        access_tier=BeaconAccessTier.BASIC,
        active_beacon_limit=5,
        minimum_interval_minutes=5,
        interval_step_minutes=5,
        country_wide_allowed=True,
        country_wide_city_required=False,
    )
    snapshot = BeaconEffectiveEntitlementSnapshot(
        snapshot_reference="snapshot-bm09-unit-entitlement-001",
        beacon_source_reference="beacon-source-bm09-unit-001",
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
        provenance_reference="provenance-bm09-unit-001",
    )
    return BeaconLifecycleEntitlementDecision(
        decision_id="decision-bm09-unit-resume-allowed-001",
        beacon_id="beacon-bm09-unit-001",
        account_id=_ACCOUNT_ID,
        action_kind=BeaconLifecycleActionKind.RESUME,
        outcome=BeaconLifecycleEntitlementOutcome.ALLOWED,
        beacon_source_reference=snapshot.beacon_source_reference,
        entitlement_evidence_reference=entitlement_evidence_reference,
        effective_entitlement_snapshot=snapshot,
        requested_interval_minutes=5,
        active_beacon_count=active_beacon_count,
        archived_beacon_count=1,
        history_beacon_count=1,
        deleted_beacon_count=1,
        requested_country_wide=False,
        entitlement_recheck_reference="entitlement-recheck-bm09-unit-001",
    )


def test_bm09_history_boundary_excludes_frozen_archived_deleted_beacons() -> None:
    frozen_beacon = _beacon(
        beacon_id="beacon-bm09-unit-frozen-001",
        lifecycle_state=BeaconLifecycleState.FROZEN,
        restorable=True,
        history_entry=_history_entry(
            beacon_id="beacon-bm09-unit-frozen-001",
            outcome=BeaconHistoryOutcome.HISTORY,
            restorable=True,
            reason="Frozen after entitlement expiry remains visible in history.",
        ),
    )
    archived_beacon = _beacon(
        beacon_id="beacon-bm09-unit-archived-001",
        lifecycle_state=BeaconLifecycleState.ARCHIVED,
        restorable=True,
        history_entry=_history_entry(
            beacon_id="beacon-bm09-unit-archived-001",
            outcome=BeaconHistoryOutcome.ARCHIVED,
            restorable=True,
            reason="Archived Beacon is a history-visible semantic outcome.",
        ),
    )
    deleted_beacon = _beacon(
        beacon_id="beacon-bm09-unit-deleted-001",
        lifecycle_state=BeaconLifecycleState.ARCHIVED,
        restorable=True,
        history_entry=_history_entry(
            beacon_id="beacon-bm09-unit-deleted-001",
            outcome=BeaconHistoryOutcome.DELETED,
            restorable=True,
            reason="User-deleted Beacon remains visible in history.",
        ),
    )

    history_boundary = (frozen_beacon, archived_beacon, deleted_beacon)

    assert {beacon.lifecycle_state for beacon in history_boundary} == {
        BeaconLifecycleState.FROZEN,
        BeaconLifecycleState.ARCHIVED,
    }
    assert all(beacon.counts_toward_active_limit is False for beacon in history_boundary)
    assert all(
        beacon.source_url == beacon.current_configuration.source_url
        for beacon in history_boundary
    )
    assert frozen_beacon.history_entries[0].outcome is BeaconHistoryOutcome.HISTORY
    assert archived_beacon.history_entries[0].outcome is BeaconHistoryOutcome.ARCHIVED
    assert deleted_beacon.history_entries[0].outcome is BeaconHistoryOutcome.DELETED


def test_bm09_restore_from_history_preserves_source_url_and_does_not_require_reentry() -> None:
    archived_history_entry = _history_entry(
        beacon_id="beacon-bm09-unit-restore-001",
        outcome=BeaconHistoryOutcome.ARCHIVED,
        restorable=True,
        reason="Archived Beacon can return without re-entering the source URL.",
    )
    archived_beacon = _beacon(
        beacon_id="beacon-bm09-unit-restore-001",
        lifecycle_state=BeaconLifecycleState.ARCHIVED,
        restorable=True,
        history_entry=archived_history_entry,
    )
    restore_entitlement = _fresh_entitlement_decision(active_beacon_count=4)
    restored_beacon = Beacon.model_validate(
        archived_beacon.model_copy(
            update={
                "lifecycle_state": BeaconLifecycleState.ACTIVE,
                "counts_toward_active_limit": True,
                "current_configuration": archived_beacon.current_configuration.model_copy(
                    update={"lifecycle_state": BeaconLifecycleState.ACTIVE}
                ),
            }
        ).model_dump()
    )

    assert restore_entitlement.outcome is BeaconLifecycleEntitlementOutcome.ALLOWED
    assert restored_beacon.source_url == archived_beacon.source_url
    assert (
        restored_beacon.current_configuration.source_url
        == archived_beacon.current_configuration.source_url
    )
    assert (
        restored_beacon.current_configuration.accepted_snapshot
        == archived_beacon.current_configuration.accepted_snapshot
    )
    assert restored_beacon.lifecycle_state is BeaconLifecycleState.ACTIVE
