"""Safe synthetic fixtures for Beacon Management semantic contracts."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Final

from pydantic import BaseModel, ConfigDict, Field

from .contracts import (
    Beacon,
    BeaconAccessTier,
    BeaconActionCausation,
    BeaconActivationDecision,
    BeaconActorContext,
    BeaconActorKind,
    BeaconAuthorizationDecision,
    BeaconAuthorizationOutcome,
    BeaconConfigurationEvidenceRetentionDecision,
    BeaconConfigurationRetentionBoundary,
    BeaconConfigurationStoragePolicyOutcome,
    BeaconConfigurationStoragePolicyRejectionReason,
    BeaconCurrentConfiguration,
    BeaconCurrentConfigurationAuthorityStatus,
    BeaconCurrentConfigurationDecision,
    BeaconDecisionStatus,
    BeaconEffectiveConfigurationDecision,
    BeaconEffectiveConfigurationRejectionReason,
    BeaconEffectiveEntitlementSnapshot,
    BeaconEntitlementEvidenceFreshnessStatus,
    BeaconEntitlementEvidenceReference,
    BeaconExpiryOutcome,
    BeaconFilterOverride,
    BeaconHistoryEntry,
    BeaconHistoryOutcome,
    BeaconLifecycleActionKind,
    BeaconLifecycleEntitlementDecision,
    BeaconLifecycleEntitlementOutcome,
    BeaconLifecycleEntitlementRejectionReason,
    BeaconLifecycleState,
    BeaconMutationDecision,
    BeaconNameOrigin,
    BeaconNamingMetadata,
    BeaconOverrideApplicationOutcome,
    BeaconOverrideFieldSupportStatus,
    BeaconOverridePatchOperation,
    BeaconOverrideRejectionReason,
    BeaconOverrideStatus,
    BeaconOwnershipDecision,
    BeaconParserEvidenceReference,
    BeaconParserEvidenceSafetyClass,
    BeaconParserOutcomeStatus,
    BeaconPatchSaveDecision,
    BeaconPatchSaveRejectionReason,
    BeaconPreparedSourceUrl,
    BeaconProtectedAction,
    BeaconSnapshotAcceptanceDecision,
    BeaconSnapshotAcceptanceOutcome,
    BeaconSnapshotRejectionReason,
    BeaconSourceUrl,
    BeaconSourceUrlFingerprintPolicy,
    BeaconSourceUrlIdempotencyBasis,
    BeaconSourceUrlPreparationDecision,
    BeaconSourceUrlPreparationOutcome,
    BeaconSourceUrlSafetyClassification,
    BeaconSystemActorClass,
    BeaconTariffPolicyBand,
    ExtractedSearchConfigurationSnapshot,
)


class SyntheticFixtureCase(BaseModel):
    """Frozen synthetic fixture case for Beacon Management tests."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    fixture_id: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    account_id: str = Field(min_length=1)
    foreign_account_id: str = Field(min_length=1)
    beacon: Beacon | None = None
    peer_beacon: Beacon | None = None
    source_url: BeaconSourceUrl | None = None
    snapshot: ExtractedSearchConfigurationSnapshot | None = None
    snapshot_acceptance_decision: BeaconSnapshotAcceptanceDecision | None = None
    override: BeaconFilterOverride | None = None
    override_patch_operation: BeaconOverridePatchOperation | None = None
    current_configuration: BeaconCurrentConfiguration | None = None
    effective_configuration_decision: BeaconEffectiveConfigurationDecision | None = None
    activation_decision: BeaconActivationDecision | None = None
    mutation_decision: BeaconMutationDecision | None = None
    patch_save_decision: BeaconPatchSaveDecision | None = None
    entitlement_evidence_reference: BeaconEntitlementEvidenceReference | None = None
    tariff_policy_band: BeaconTariffPolicyBand | None = None
    effective_entitlement_snapshot: BeaconEffectiveEntitlementSnapshot | None = None
    lifecycle_entitlement_decision: BeaconLifecycleEntitlementDecision | None = None
    source_url_preparation_decision: BeaconSourceUrlPreparationDecision | None = None
    ownership_decision: BeaconOwnershipDecision | None = None
    authorization_decision: BeaconAuthorizationDecision | None = None
    history_entry: BeaconHistoryEntry | None = None
    current_configuration_decision: BeaconCurrentConfigurationDecision | None = None
    configuration_evidence_retention_decision: (
        BeaconConfigurationEvidenceRetentionDecision | None
    ) = None


_OWN_ACCOUNT_ID = "acct-bm-synth-own-001"
_FOREIGN_ACCOUNT_ID = "acct-bm-synth-foreign-001"
_SUPPORT_ACCOUNT_ID = "acct-bm-synth-support-001"
_BASE_URL = "https://example.invalid/search?query=beacon-management&city=synthetic"
_SUBMITTED_AT = datetime(2026, 7, 9, 10, 0, tzinfo=timezone.utc)
_RECORD_AT = datetime(2026, 7, 9, 10, 5, tzinfo=timezone.utc)
_REVISION_AT = datetime(2026, 7, 9, 10, 10, tzinfo=timezone.utc)


def _source_url(reference: str, submitted_url: str = _BASE_URL) -> BeaconSourceUrl:
    return BeaconSourceUrl(
        submitted_url=submitted_url,
        evidence_reference=reference,
        submitted_at=_SUBMITTED_AT,
        source_channel="user-submitted",
        submitted_by_label="synthetic-user",
    )


def _snapshot(
    *,
    snapshot_id: str,
    status: BeaconParserOutcomeStatus,
    accepted_as_clean: bool,
    evidence_reference: str,
    parser_evidence_reference: BeaconParserEvidenceReference | None = None,
    normalized_filter_values: tuple[str, ...] = (),
    unsupported_parameters: tuple[str, ...] = (),
    warning_codes: tuple[str, ...] = (),
) -> ExtractedSearchConfigurationSnapshot:
    return ExtractedSearchConfigurationSnapshot(
        snapshot_id=snapshot_id,
        parser_outcome_status=status,
        accepted_as_clean=accepted_as_clean,
        normalized_filter_values=normalized_filter_values,
        unsupported_parameters=unsupported_parameters,
        warning_codes=warning_codes,
        evidence_reference=evidence_reference,
        parser_evidence_reference=parser_evidence_reference,
    )


def _parser_evidence_reference(
    *,
    evidence_reference: str,
    safety_class: BeaconParserEvidenceSafetyClass = BeaconParserEvidenceSafetyClass.OPAQUE,
    raw_provider_payload_authority: bool = False,
) -> BeaconParserEvidenceReference:
    return BeaconParserEvidenceReference(
        evidence_reference=evidence_reference,
        safety_class=safety_class,
        raw_provider_payload_authority=raw_provider_payload_authority,
    )


def _snapshot_acceptance_decision(
    *,
    decision_id: str,
    parser_outcome_status: BeaconParserOutcomeStatus,
    parser_evidence_reference: BeaconParserEvidenceReference | None,
    acceptance_outcome: BeaconSnapshotAcceptanceOutcome,
    rejection_reason: BeaconSnapshotRejectionReason | None = None,
    parser_adapter_evidence_gate_reference: str | None = None,
    exact_acceptance_threshold_percent: int | None = None,
    unsupported_parameters: tuple[str, ...] = (),
    claims_full_parser_adapter_implementation_present: bool = False,
) -> BeaconSnapshotAcceptanceDecision:
    return BeaconSnapshotAcceptanceDecision(
        decision_id=decision_id,
        parser_outcome_status=parser_outcome_status,
        parser_evidence_reference=parser_evidence_reference,
        acceptance_outcome=acceptance_outcome,
        rejection_reason=rejection_reason,
        parser_adapter_evidence_gate_reference=parser_adapter_evidence_gate_reference,
        exact_acceptance_threshold_percent=exact_acceptance_threshold_percent,
        unsupported_parameters=unsupported_parameters,
        claims_full_parser_adapter_implementation_present=claims_full_parser_adapter_implementation_present,
    )


def _override(
    *,
    field_name: str,
    supported: bool,
    status: BeaconOverrideStatus,
    requested_values: tuple[str, ...],
    applied_values: tuple[str, ...] | None,
    reference: str,
    reason: str,
) -> BeaconFilterOverride:
    return BeaconFilterOverride(
        field_name=field_name,
        field_supported=supported,
        status=status,
        requested_values=requested_values,
        applied_values=applied_values,
        override_reference=reference,
        reason=reason,
    )


def _override_patch_operation(
    *,
    field_name: str,
    support_status: BeaconOverrideFieldSupportStatus,
    outcome: BeaconOverrideApplicationOutcome,
    requested_values: tuple[str, ...],
    applied_values: tuple[str, ...] | None,
    parser_filter_evidence_reference: str,
    override_evidence_reference: str,
    rejection_reason: BeaconOverrideRejectionReason | None = None,
) -> BeaconOverridePatchOperation:
    return BeaconOverridePatchOperation(
        field_name=field_name,
        support_status=support_status,
        outcome=outcome,
        requested_values=requested_values,
        applied_values=applied_values,
        parser_filter_evidence_reference=parser_filter_evidence_reference,
        override_evidence_reference=override_evidence_reference,
        rejection_reason=rejection_reason,
    )


def _configuration(
    *,
    beacon_id: str,
    account_id: str,
    source_url: BeaconSourceUrl,
    snapshot: ExtractedSearchConfigurationSnapshot,
    display_name: str,
    lifecycle_state: BeaconLifecycleState,
    current_revision_id: str,
    overrides: tuple[BeaconFilterOverride, ...] = (),
    retained_evidence_references: tuple[str, ...] = (),
    previous_user_facing_revision_ids: tuple[str, ...] = (),
) -> BeaconCurrentConfiguration:
    return BeaconCurrentConfiguration(
        beacon_id=beacon_id,
        account_id=account_id,
        source_url=source_url,
        accepted_snapshot=snapshot,
        overrides=overrides,
        current_revision_id=current_revision_id,
        display_name=display_name,
        lifecycle_state=lifecycle_state,
        retained_evidence_references=retained_evidence_references,
        previous_user_facing_revision_ids=previous_user_facing_revision_ids,
    )


def _current_configuration_decision(
    *,
    decision_id: str,
    beacon_id: str,
    account_id: str,
    current_user_facing_active_configurations: tuple[BeaconCurrentConfiguration, ...],
    current_scan_configuration_reference: str,
    authority_status: BeaconCurrentConfigurationAuthorityStatus,
    storage_policy_outcome: BeaconConfigurationStoragePolicyOutcome,
    retention_boundary: BeaconConfigurationRetentionBoundary,
    replaced_current_user_facing_configuration: BeaconCurrentConfiguration | None = None,
    committed_scan_audit_evidence_configuration_reference: str | None = None,
    configuration_change_replaces_current_working_configuration: bool = True,
    already_committed_scan_audit_facts_reinterpreted: bool = False,
    physical_delete_or_compaction_claimed: bool = False,
    db_repository_runtime_persistence_claimed: bool = False,
    scanrun_listing_history_state_claimed: bool = False,
    minimal_committed_evidence_editable: bool = False,
    drops_committed_scan_audit_evidence: bool = False,
    provenance_boundary_changed: bool = False,
    rejection_reason: BeaconConfigurationStoragePolicyRejectionReason | None = None,
) -> BeaconCurrentConfigurationDecision:
    return BeaconCurrentConfigurationDecision(
        decision_id=decision_id,
        beacon_id=beacon_id,
        account_id=account_id,
        authority_status=authority_status,
        storage_policy_outcome=storage_policy_outcome,
        retention_boundary=retention_boundary,
        current_user_facing_active_configurations=current_user_facing_active_configurations,
        replaced_current_user_facing_configuration=replaced_current_user_facing_configuration,
        current_scan_configuration_reference=current_scan_configuration_reference,
        committed_scan_audit_evidence_configuration_reference=committed_scan_audit_evidence_configuration_reference,
        configuration_change_replaces_current_working_configuration=(
            configuration_change_replaces_current_working_configuration
        ),
        already_committed_scan_audit_facts_reinterpreted=already_committed_scan_audit_facts_reinterpreted,
        physical_delete_or_compaction_claimed=physical_delete_or_compaction_claimed,
        db_repository_runtime_persistence_claimed=db_repository_runtime_persistence_claimed,
        scanrun_listing_history_state_claimed=scanrun_listing_history_state_claimed,
        minimal_committed_evidence_editable=minimal_committed_evidence_editable,
        drops_committed_scan_audit_evidence=drops_committed_scan_audit_evidence,
        provenance_boundary_changed=provenance_boundary_changed,
        rejection_reason=rejection_reason,
    )


def _configuration_evidence_retention_decision(
    *,
    decision_id: str,
    beacon_id: str,
    account_id: str,
    committed_scan_audit_evidence_reference: str,
    original_current_configuration_reference: str,
    current_configuration_reference: str | None,
    minimal_immutable_scan_audit_evidence_reference: str,
    authority_status: BeaconCurrentConfigurationAuthorityStatus,
    storage_policy_outcome: BeaconConfigurationStoragePolicyOutcome,
    retention_boundary: BeaconConfigurationRetentionBoundary,
    minimal_committed_evidence_editable: bool = False,
    already_committed_scan_audit_facts_reinterpreted: bool = False,
    physical_delete_or_compaction_claimed: bool = False,
    db_repository_runtime_persistence_claimed: bool = False,
    scanrun_listing_history_state_claimed: bool = False,
    drops_committed_scan_audit_evidence: bool = False,
    provenance_boundary_changed: bool = False,
    rejection_reason: BeaconConfigurationStoragePolicyRejectionReason | None = None,
) -> BeaconConfigurationEvidenceRetentionDecision:
    return BeaconConfigurationEvidenceRetentionDecision(
        decision_id=decision_id,
        beacon_id=beacon_id,
        account_id=account_id,
        authority_status=authority_status,
        storage_policy_outcome=storage_policy_outcome,
        retention_boundary=retention_boundary,
        committed_scan_audit_evidence_reference=committed_scan_audit_evidence_reference,
        original_current_configuration_reference=original_current_configuration_reference,
        current_configuration_reference=current_configuration_reference,
        minimal_immutable_scan_audit_evidence_reference=minimal_immutable_scan_audit_evidence_reference,
        minimal_committed_evidence_editable=minimal_committed_evidence_editable,
        already_committed_scan_audit_facts_reinterpreted=already_committed_scan_audit_facts_reinterpreted,
        physical_delete_or_compaction_claimed=physical_delete_or_compaction_claimed,
        db_repository_runtime_persistence_claimed=db_repository_runtime_persistence_claimed,
        scanrun_listing_history_state_claimed=scanrun_listing_history_state_claimed,
        drops_committed_scan_audit_evidence=drops_committed_scan_audit_evidence,
        provenance_boundary_changed=provenance_boundary_changed,
        rejection_reason=rejection_reason,
    )


def _entitlement_evidence_reference(
    *,
    evidence_reference: str,
    source_reference: str,
    freshness_status: BeaconEntitlementEvidenceFreshnessStatus = (
        BeaconEntitlementEvidenceFreshnessStatus.FRESH
    ),
    freshness_reference: str,
) -> BeaconEntitlementEvidenceReference:
    return BeaconEntitlementEvidenceReference(
        evidence_reference=evidence_reference,
        source_reference=source_reference,
        freshness_status=freshness_status,
        freshness_reference=freshness_reference,
    )


def _tariff_policy_band(
    *,
    access_tier: BeaconAccessTier,
    active_beacon_limit: int,
    minimum_interval_minutes: int,
    interval_step_minutes: int,
    country_wide_allowed: bool,
    country_wide_city_required: bool,
) -> BeaconTariffPolicyBand:
    return BeaconTariffPolicyBand(
        access_tier=access_tier,
        active_beacon_limit=active_beacon_limit,
        minimum_interval_minutes=minimum_interval_minutes,
        interval_step_minutes=interval_step_minutes,
        country_wide_allowed=country_wide_allowed,
        country_wide_city_required=country_wide_city_required,
    )


def _effective_entitlement_snapshot(
    *,
    snapshot_reference: str,
    beacon_source_reference: str,
    entitlement_source_reference: str,
    entitlement_evidence_reference: BeaconEntitlementEvidenceReference,
    tariff_policy_band: BeaconTariffPolicyBand,
    effective_outcome: BeaconLifecycleEntitlementOutcome,
    active_beacon_count: int,
    archived_beacon_count: int = 0,
    history_beacon_count: int = 0,
    deleted_beacon_count: int = 0,
    requested_interval_minutes: int,
    requested_country_wide: bool,
    selected_city: str | None = None,
    selected_free_beacon_id: str | None = None,
    selected_free_beacon_user_choice_reference: str | None = None,
    free_compliance_reference: str | None = None,
    expired_paid_active_beacon_count: int = 0,
    future_notification_reference: str | None = None,
    provenance_reference: str,
) -> BeaconEffectiveEntitlementSnapshot:
    return BeaconEffectiveEntitlementSnapshot(
        snapshot_reference=snapshot_reference,
        beacon_source_reference=beacon_source_reference,
        entitlement_source_reference=entitlement_source_reference,
        entitlement_evidence_reference=entitlement_evidence_reference,
        tariff_policy_band=tariff_policy_band,
        effective_outcome=effective_outcome,
        active_beacon_count=active_beacon_count,
        archived_beacon_count=archived_beacon_count,
        history_beacon_count=history_beacon_count,
        deleted_beacon_count=deleted_beacon_count,
        requested_interval_minutes=requested_interval_minutes,
        requested_country_wide=requested_country_wide,
        selected_city=selected_city,
        selected_free_beacon_id=selected_free_beacon_id,
        selected_free_beacon_user_choice_reference=selected_free_beacon_user_choice_reference,
        free_compliance_reference=free_compliance_reference,
        expired_paid_active_beacon_count=expired_paid_active_beacon_count,
        future_notification_reference=future_notification_reference,
        provenance_reference=provenance_reference,
    )


def _lifecycle_entitlement_decision(
    *,
    decision_id: str,
    beacon_id: str,
    account_id: str,
    action_kind: BeaconLifecycleActionKind,
    outcome: BeaconLifecycleEntitlementOutcome,
    beacon_source_reference: str,
    entitlement_evidence_reference: BeaconEntitlementEvidenceReference | None,
    effective_entitlement_snapshot: BeaconEffectiveEntitlementSnapshot | None,
    requested_interval_minutes: int,
    active_beacon_count: int,
    archived_beacon_count: int = 0,
    history_beacon_count: int = 0,
    deleted_beacon_count: int = 0,
    requested_country_wide: bool,
    selected_city: str | None = None,
    paid_access_expired: bool = False,
    selected_free_beacon_id: str | None = None,
    selected_free_beacon_user_choice_reference: str | None = None,
    free_compliance_reference: str | None = None,
    entitlement_recheck_reference: str | None = None,
    future_notification_reference: str | None = None,
    client_channel_flag: str | None = None,
    client_channel_flag_is_authorization_proof: bool = False,
    notification_sending_claimed: bool = False,
    billing_payment_tariff_mutation_claimed: bool = False,
    scheduler_runtime_claimed: bool = False,
    db_repository_runtime_persistence_claimed: bool = False,
    scanrun_listing_history_state_claimed: bool = False,
    parser_filter_catalog_ownership_claimed: bool = False,
    provenance_boundary_changed: bool = False,
    rejection_reason: BeaconLifecycleEntitlementRejectionReason | None = None,
) -> BeaconLifecycleEntitlementDecision:
    return BeaconLifecycleEntitlementDecision(
        decision_id=decision_id,
        beacon_id=beacon_id,
        account_id=account_id,
        action_kind=action_kind,
        outcome=outcome,
        beacon_source_reference=beacon_source_reference,
        entitlement_evidence_reference=entitlement_evidence_reference,
        effective_entitlement_snapshot=effective_entitlement_snapshot,
        requested_interval_minutes=requested_interval_minutes,
        active_beacon_count=active_beacon_count,
        archived_beacon_count=archived_beacon_count,
        history_beacon_count=history_beacon_count,
        deleted_beacon_count=deleted_beacon_count,
        requested_country_wide=requested_country_wide,
        selected_city=selected_city,
        paid_access_expired=paid_access_expired,
        selected_free_beacon_id=selected_free_beacon_id,
        selected_free_beacon_user_choice_reference=selected_free_beacon_user_choice_reference,
        free_compliance_reference=free_compliance_reference,
        entitlement_recheck_reference=entitlement_recheck_reference,
        future_notification_reference=future_notification_reference,
        client_channel_flag=client_channel_flag,
        client_channel_flag_is_authorization_proof=client_channel_flag_is_authorization_proof,
        notification_sending_claimed=notification_sending_claimed,
        billing_payment_tariff_mutation_claimed=billing_payment_tariff_mutation_claimed,
        scheduler_runtime_claimed=scheduler_runtime_claimed,
        db_repository_runtime_persistence_claimed=db_repository_runtime_persistence_claimed,
        scanrun_listing_history_state_claimed=scanrun_listing_history_state_claimed,
        parser_filter_catalog_ownership_claimed=parser_filter_catalog_ownership_claimed,
        provenance_boundary_changed=provenance_boundary_changed,
        rejection_reason=rejection_reason,
    )


def _effective_configuration_decision(
    *,
    decision_id: str,
    beacon_id: str,
    account_id: str,
    source_url: BeaconSourceUrl,
    accepted_snapshot: ExtractedSearchConfigurationSnapshot,
    override_operations: tuple[BeaconOverridePatchOperation, ...] = (),
    status: BeaconDecisionStatus,
    effective_configuration_reference: str,
    authoritative_state_reference: str,
    source_url_overwritten_by_snapshot: bool = False,
    source_url_overwritten_by_override: bool = False,
    rejection_reason: BeaconEffectiveConfigurationRejectionReason | None = None,
) -> BeaconEffectiveConfigurationDecision:
    return BeaconEffectiveConfigurationDecision(
        decision_id=decision_id,
        beacon_id=beacon_id,
        account_id=account_id,
        source_url=source_url,
        accepted_snapshot=accepted_snapshot,
        override_operations=override_operations,
        status=status,
        effective_configuration_reference=effective_configuration_reference,
        authoritative_state_reference=authoritative_state_reference,
        source_url_overwritten_by_snapshot=source_url_overwritten_by_snapshot,
        source_url_overwritten_by_override=source_url_overwritten_by_override,
        rejection_reason=rejection_reason,
    )


def _patch_save_decision(
    *,
    decision_id: str,
    beacon_id: str,
    account_id: str,
    status: BeaconDecisionStatus,
    patch_fields: tuple[str, ...],
    applied_fields: tuple[str, ...],
    preserved_fields: tuple[str, ...] = (),
    same_field_concurrent_change: bool = False,
    last_write_wins: bool = False,
    different_field_updates_merge: bool = False,
    stale_full_form_overwrite: bool = False,
    authoritative_state_reference: str | None = None,
    claims_db_repository_runtime_persistence_implementation: bool = False,
    rejection_reason: BeaconPatchSaveRejectionReason | None = None,
) -> BeaconPatchSaveDecision:
    return BeaconPatchSaveDecision(
        decision_id=decision_id,
        beacon_id=beacon_id,
        account_id=account_id,
        status=status,
        patch_fields=patch_fields,
        applied_fields=applied_fields,
        preserved_fields=preserved_fields,
        same_field_concurrent_change=same_field_concurrent_change,
        last_write_wins=last_write_wins,
        different_field_updates_merge=different_field_updates_merge,
        stale_full_form_overwrite=stale_full_form_overwrite,
        authoritative_state_reference=authoritative_state_reference,
        claims_db_repository_runtime_persistence_implementation=claims_db_repository_runtime_persistence_implementation,
        rejection_reason=rejection_reason,
    )


def _naming(
    *,
    display_name: str,
    origin: BeaconNameOrigin,
    source_title: str,
    source_context_reference: str,
    default_name: str | None = None,
) -> BeaconNamingMetadata:
    return BeaconNamingMetadata(
        display_name=display_name,
        name_origin=origin,
        source_title=source_title,
        source_context_reference=source_context_reference,
        default_name=default_name,
    )


def _actor_context(
    *,
    actor_context_id: str,
    actor_kind: BeaconActorKind,
    is_verified: bool,
    account_id: str | None = None,
    actor_reference_id: str | None = None,
    client_channel_flag: str | None = None,
    client_channel_flag_is_authorization_proof: bool = False,
) -> BeaconActorContext:
    return BeaconActorContext(
        actor_context_id=actor_context_id,
        actor_kind=actor_kind,
        is_verified=is_verified,
        account_id=account_id,
        actor_reference_id=actor_reference_id,
        client_channel_flag=client_channel_flag,
        client_channel_flag_is_authorization_proof=client_channel_flag_is_authorization_proof,
    )


def _ownership_decision(
    *,
    decision_id: str,
    protected_action: BeaconProtectedAction,
    actor_context: BeaconActorContext,
    beacon_id: str,
    beacon_account_id: str,
    outcome: BeaconAuthorizationOutcome,
    safe_reason_code: str,
    reason: str,
) -> BeaconOwnershipDecision:
    return BeaconOwnershipDecision(
        decision_id=decision_id,
        protected_action=protected_action,
        actor_context=actor_context,
        beacon_id=beacon_id,
        beacon_account_id=beacon_account_id,
        outcome=outcome,
        safe_reason_code=safe_reason_code,
        reason=reason,
    )


def _authorization_decision(
    *,
    decision_id: str,
    protected_action: BeaconProtectedAction,
    actor_context: BeaconActorContext,
    beacon_id: str,
    beacon_account_id: str,
    outcome: BeaconAuthorizationOutcome,
    safe_reason_code: str,
    reason: str,
    server_role_scope_reference: str | None = None,
    server_audit_reference: str | None = None,
    action_causation: BeaconActionCausation | None = None,
) -> BeaconAuthorizationDecision:
    return BeaconAuthorizationDecision(
        decision_id=decision_id,
        protected_action=protected_action,
        actor_context=actor_context,
        beacon_id=beacon_id,
        beacon_account_id=beacon_account_id,
        outcome=outcome,
        safe_reason_code=safe_reason_code,
        reason=reason,
        server_role_scope_reference=server_role_scope_reference,
        server_audit_reference=server_audit_reference,
        action_causation=action_causation,
    )


def _causation(
    *,
    service_actor_class: BeaconSystemActorClass,
    causation_reference: str,
    policy_source_reference: str,
) -> BeaconActionCausation:
    return BeaconActionCausation(
        service_actor_class=service_actor_class,
        causation_reference=causation_reference,
        policy_source_reference=policy_source_reference,
    )


def _beacon(
    *,
    beacon_id: str,
    account_id: str,
    display_name: str,
    lifecycle_state: BeaconLifecycleState,
    current_revision_id: str,
    source_reference: str,
    snapshot: ExtractedSearchConfigurationSnapshot,
    source_url: BeaconSourceUrl | None = None,
    overrides: tuple[BeaconFilterOverride, ...] = (),
    restorable: bool = True,
    counts_toward_active_limit: bool = True,
    history_entries: tuple[BeaconHistoryEntry, ...] = (),
    source_title: str = "synthetic search source",
    source_context_reference: str = "ctx-synth-001",
) -> Beacon:
    source_url = source_url or _source_url(source_reference)
    current_configuration = _configuration(
        beacon_id=beacon_id,
        account_id=account_id,
        source_url=source_url,
        snapshot=snapshot,
        display_name=display_name,
        lifecycle_state=lifecycle_state,
        current_revision_id=current_revision_id,
        overrides=overrides,
        retained_evidence_references=(f"{beacon_id}-audit-ref",),
    )
    return Beacon(
        beacon_id=beacon_id,
        account_id=account_id,
        naming=_naming(
            display_name=display_name,
            origin=BeaconNameOrigin.USER_PROVIDED,
            source_title=source_title,
            source_context_reference=source_context_reference,
            default_name="synthetic-default-name",
        ),
        source_url=source_url,
        current_configuration=current_configuration,
        lifecycle_state=lifecycle_state,
        restorable=restorable,
        counts_toward_active_limit=counts_toward_active_limit,
        history_entries=history_entries,
    )


def _fingerprint_policy(
    *,
    policy_reference: str,
    comparison_reference: str,
    idempotency_reference: str,
    debug_reference: str,
) -> BeaconSourceUrlFingerprintPolicy:
    return BeaconSourceUrlFingerprintPolicy(
        policy_reference=policy_reference,
        comparison_reference=comparison_reference,
        idempotency_reference=idempotency_reference,
        debug_reference=debug_reference,
    )


def _idempotency_basis(
    *,
    source_url_reference: str,
    command_reference: str | None = None,
    account_id: str | None = None,
    beacon_id: str | None = None,
    requested_beacon_id: str | None = None,
) -> BeaconSourceUrlIdempotencyBasis:
    return BeaconSourceUrlIdempotencyBasis(
        source_url_reference=source_url_reference,
        command_reference=command_reference,
        account_id=account_id,
        beacon_id=beacon_id,
        requested_beacon_id=requested_beacon_id,
    )


def _prepared_source_url(
    *,
    prepared_source_url_reference: str,
    source_url: BeaconSourceUrl,
    classification: BeaconSourceUrlSafetyClassification,
    opaque_fingerprint_reference: str | None = None,
    fingerprint_policy: BeaconSourceUrlFingerprintPolicy | None = None,
    source_url_overwritten_by_snapshot: bool = False,
    source_url_overwritten_by_override: bool = False,
    source_url_rewritten: bool = False,
) -> BeaconPreparedSourceUrl:
    return BeaconPreparedSourceUrl(
        prepared_source_url_reference=prepared_source_url_reference,
        submitted_source_url=source_url,
        preserved_submitted_url=source_url.submitted_url,
        safety_classification=classification,
        source_url_overwritten_by_snapshot=source_url_overwritten_by_snapshot,
        source_url_overwritten_by_override=source_url_overwritten_by_override,
        source_url_rewritten=source_url_rewritten,
        opaque_fingerprint_reference=opaque_fingerprint_reference,
        fingerprint_policy=fingerprint_policy,
    )


def _source_url_preparation_decision(
    *,
    decision_id: str,
    account_id: str,
    beacon_id: str | None = None,
    requested_beacon_id: str | None = None,
    source_url: BeaconSourceUrl,
    prepared_source_url: BeaconPreparedSourceUrl,
    outcome: BeaconSourceUrlPreparationOutcome,
    safe_reason_code: str,
    duplicate_source_url_blocking_policy: bool = False,
    idempotency_basis: BeaconSourceUrlIdempotencyBasis,
    source_url_is_unique_key: bool = False,
    shell_command_text: str | None = None,
    shell_interpolation_field: str | None = None,
    tracking_params_ignored: bool = False,
    tracking_policy_reference: str | None = None,
    opaque_fingerprint_reference: str | None = None,
) -> BeaconSourceUrlPreparationDecision:
    return BeaconSourceUrlPreparationDecision(
        decision_id=decision_id,
        account_id=account_id,
        beacon_id=beacon_id,
        requested_beacon_id=requested_beacon_id,
        submitted_source_url=source_url,
        prepared_source_url=prepared_source_url,
        outcome=outcome,
        safe_reason_code=safe_reason_code,
        duplicate_source_url_blocking_policy=duplicate_source_url_blocking_policy,
        idempotency_basis=idempotency_basis,
        source_url_is_unique_key=source_url_is_unique_key,
        shell_command_text=shell_command_text,
        shell_interpolation_field=shell_interpolation_field,
        tracking_params_ignored=tracking_params_ignored,
        tracking_policy_reference=tracking_policy_reference,
        opaque_fingerprint_reference=opaque_fingerprint_reference,
    )


_ACTIVE_SNAPSHOT = _snapshot(
    snapshot_id="snap-bm-001",
    status=BeaconParserOutcomeStatus.CLEAN,
    accepted_as_clean=True,
    evidence_reference="evidence-bm-001",
    parser_evidence_reference=_parser_evidence_reference(
        evidence_reference="parser-evidence-bm04-active-001"
    ),
    normalized_filter_values=("city=synthetic-city", "category=synthetic-category"),
)

_ACTIVE_OVERRIDE = _override(
    field_name="price_range",
    supported=True,
    status=BeaconOverrideStatus.APPLIED,
    requested_values=("1000-2000",),
    applied_values=("1000-2000",),
    reference="override-bm-001",
    reason="synthetic supported override",
)

_MULTIVALUE_OVERRIDE = _override(
    field_name="amenities",
    supported=True,
    status=BeaconOverrideStatus.APPLIED,
    requested_values=("wifi", "parking"),
    applied_values=("wifi", "parking"),
    reference="override-bm-002",
    reason="synthetic multivalue override that preserves every approved value",
)

_UNSUPPORTED_OVERRIDE = _override(
    field_name="unsupported_field",
    supported=False,
    status=BeaconOverrideStatus.REJECTED,
    requested_values=("unexpected",),
    applied_values=None,
    reference="override-bm-003",
    reason="unsupported field remains unapplied",
)

_MALFORMED_SNAPSHOT = _snapshot(
    snapshot_id="snap-bm-002",
    status=BeaconParserOutcomeStatus.MALFORMED,
    accepted_as_clean=False,
    evidence_reference="evidence-bm-002",
    warning_codes=("MALFORMED_SHAPE",),
)

_CAPTCHA_SNAPSHOT = _snapshot(
    snapshot_id="snap-bm-003",
    status=BeaconParserOutcomeStatus.CAPTCHA_AFFECTED,
    accepted_as_clean=False,
    evidence_reference="evidence-bm-003",
    warning_codes=("CAPTCHA_BLOCK",),
)

_BM05_CLEAN_EVIDENCE = _parser_evidence_reference(
    evidence_reference="parser-evidence-bm05-clean-accepted-001"
)
_BM05_MALFORMED_EVIDENCE = _parser_evidence_reference(
    evidence_reference="parser-evidence-bm05-malformed-001"
)
_BM05_INCOMPLETE_EVIDENCE = _parser_evidence_reference(
    evidence_reference="parser-evidence-bm05-incomplete-001"
)
_BM05_CAPTCHA_EVIDENCE = _parser_evidence_reference(
    evidence_reference="parser-evidence-bm05-captcha-001"
)
_BM05_BLOCKED_EVIDENCE = _parser_evidence_reference(
    evidence_reference="parser-evidence-bm05-blocked-001"
)
_BM05_ROUTE_FAILED_EVIDENCE = _parser_evidence_reference(
    evidence_reference="parser-evidence-bm05-route-failed-001"
)
_BM05_AMBIGUOUS_EVIDENCE = _parser_evidence_reference(
    evidence_reference="parser-evidence-bm05-ambiguous-001",
    safety_class=BeaconParserEvidenceSafetyClass.AMBIGUOUS,
)
_BM05_UNSUPPORTED_EVIDENCE = _parser_evidence_reference(
    evidence_reference="parser-evidence-bm05-unsupported-001",
    safety_class=BeaconParserEvidenceSafetyClass.UNSUPPORTED,
)
_BM05_RAW_PROVIDER_AUTHORITY_EVIDENCE = _parser_evidence_reference(
    evidence_reference="parser-evidence-bm05-raw-provider-authority-001",
    safety_class=BeaconParserEvidenceSafetyClass.RAW_PROVIDER_PAYLOAD_AUTHORITY,
    raw_provider_payload_authority=True,
)
_BM05_RAW_HTML_EVIDENCE = _parser_evidence_reference(
    evidence_reference="parser-evidence-bm05-raw-html-001",
    safety_class=BeaconParserEvidenceSafetyClass.RAW_HTML,
)
_BM05_RAW_SEARCH_CORE_EVIDENCE = _parser_evidence_reference(
    evidence_reference="parser-evidence-bm05-search-core-ref-001",
    safety_class=BeaconParserEvidenceSafetyClass.RAW_SEARCH_CORE,
)
_BM05_RAW_CONTEXT_EVIDENCE = _parser_evidence_reference(
    evidence_reference="parser-evidence-bm05-raw-context-001",
    safety_class=BeaconParserEvidenceSafetyClass.RAW_CONTEXT,
)
_BM05_THRESHOLD_DEFERRED_EVIDENCE = _parser_evidence_reference(
    evidence_reference="parser-evidence-bm05-threshold-deferred-001"
)
_BM05_UNSUPPORTED_PARAMETERS_EVIDENCE = _parser_evidence_reference(
    evidence_reference="parser-evidence-bm05-unsupported-parameters-001"
)
_BM05_CLEAN_ACCEPTANCE = _snapshot_acceptance_decision(
    decision_id="decision-bm05-clean-accepted-001",
    parser_outcome_status=BeaconParserOutcomeStatus.CLEAN,
    parser_evidence_reference=_BM05_CLEAN_EVIDENCE,
    acceptance_outcome=BeaconSnapshotAcceptanceOutcome.ACCEPTED,
    parser_adapter_evidence_gate_reference="parser-adapter-evidence-gate-bm05-001",
)

_BM05_MALFORMED_ACCEPTANCE = _snapshot_acceptance_decision(
    decision_id="decision-bm05-malformed-rejected-001",
    parser_outcome_status=BeaconParserOutcomeStatus.MALFORMED,
    parser_evidence_reference=_BM05_MALFORMED_EVIDENCE,
    acceptance_outcome=BeaconSnapshotAcceptanceOutcome.REJECTED,
    rejection_reason=BeaconSnapshotRejectionReason.NON_CLEAN_PARSER_OUTCOME,
)

_BM05_INCOMPLETE_ACCEPTANCE = _snapshot_acceptance_decision(
    decision_id="decision-bm05-incomplete-rejected-001",
    parser_outcome_status=BeaconParserOutcomeStatus.INCOMPLETE,
    parser_evidence_reference=_BM05_INCOMPLETE_EVIDENCE,
    acceptance_outcome=BeaconSnapshotAcceptanceOutcome.REJECTED,
    rejection_reason=BeaconSnapshotRejectionReason.NON_CLEAN_PARSER_OUTCOME,
)

_BM05_CAPTCHA_ACCEPTANCE = _snapshot_acceptance_decision(
    decision_id="decision-bm05-captcha-rejected-001",
    parser_outcome_status=BeaconParserOutcomeStatus.CAPTCHA_AFFECTED,
    parser_evidence_reference=_BM05_CAPTCHA_EVIDENCE,
    acceptance_outcome=BeaconSnapshotAcceptanceOutcome.BLOCKED,
    rejection_reason=BeaconSnapshotRejectionReason.NON_CLEAN_PARSER_OUTCOME,
)

_BM05_BLOCKED_ACCEPTANCE = _snapshot_acceptance_decision(
    decision_id="decision-bm05-blocked-rejected-001",
    parser_outcome_status=BeaconParserOutcomeStatus.BLOCKED,
    parser_evidence_reference=_BM05_BLOCKED_EVIDENCE,
    acceptance_outcome=BeaconSnapshotAcceptanceOutcome.BLOCKED,
    rejection_reason=BeaconSnapshotRejectionReason.NON_CLEAN_PARSER_OUTCOME,
)

_BM05_ROUTE_FAILED_ACCEPTANCE = _snapshot_acceptance_decision(
    decision_id="decision-bm05-route-failed-rejected-001",
    parser_outcome_status=BeaconParserOutcomeStatus.ROUTE_FAILED,
    parser_evidence_reference=_BM05_ROUTE_FAILED_EVIDENCE,
    acceptance_outcome=BeaconSnapshotAcceptanceOutcome.BLOCKED,
    rejection_reason=BeaconSnapshotRejectionReason.NON_CLEAN_PARSER_OUTCOME,
)

_BM05_AMBIGUOUS_ACCEPTANCE = _snapshot_acceptance_decision(
    decision_id="decision-bm05-ambiguous-rejected-001",
    parser_outcome_status=BeaconParserOutcomeStatus.AMBIGUOUS,
    parser_evidence_reference=_BM05_AMBIGUOUS_EVIDENCE,
    acceptance_outcome=BeaconSnapshotAcceptanceOutcome.REJECTED,
    rejection_reason=BeaconSnapshotRejectionReason.AMBIGUOUS_PARSER_EVIDENCE,
)

_BM05_UNSUPPORTED_ACCEPTANCE = _snapshot_acceptance_decision(
    decision_id="decision-bm05-unsupported-rejected-001",
    parser_outcome_status=BeaconParserOutcomeStatus.UNSUPPORTED,
    parser_evidence_reference=_BM05_UNSUPPORTED_EVIDENCE,
    acceptance_outcome=BeaconSnapshotAcceptanceOutcome.UNSUPPORTED,
    rejection_reason=BeaconSnapshotRejectionReason.UNSUPPORTED_PARSER_OUTCOME,
)

_BM05_RAW_PROVIDER_AUTHORITY_ACCEPTANCE = _snapshot_acceptance_decision(
    decision_id="decision-bm05-raw-provider-authority-rejected-001",
    parser_outcome_status=BeaconParserOutcomeStatus.CLEAN,
    parser_evidence_reference=_BM05_RAW_PROVIDER_AUTHORITY_EVIDENCE,
    acceptance_outcome=BeaconSnapshotAcceptanceOutcome.REJECTED,
    rejection_reason=BeaconSnapshotRejectionReason.RAW_PROVIDER_PAYLOAD_AUTHORITY,
)

_BM05_RAW_HTML_ACCEPTANCE = _snapshot_acceptance_decision(
    decision_id="decision-bm05-raw-html-rejected-001",
    parser_outcome_status=BeaconParserOutcomeStatus.CLEAN,
    parser_evidence_reference=_BM05_RAW_HTML_EVIDENCE,
    acceptance_outcome=BeaconSnapshotAcceptanceOutcome.REJECTED,
    rejection_reason=BeaconSnapshotRejectionReason.RAW_HTML_SEARCH_CORE_CONTEXT_PAYLOAD,
)

_BM05_RAW_SEARCH_CORE_ACCEPTANCE = _snapshot_acceptance_decision(
    decision_id="decision-bm05-raw-searchcore-rejected-001",
    parser_outcome_status=BeaconParserOutcomeStatus.CLEAN,
    parser_evidence_reference=_BM05_RAW_SEARCH_CORE_EVIDENCE,
    acceptance_outcome=BeaconSnapshotAcceptanceOutcome.REJECTED,
    rejection_reason=BeaconSnapshotRejectionReason.RAW_HTML_SEARCH_CORE_CONTEXT_PAYLOAD,
)

_BM05_RAW_CONTEXT_ACCEPTANCE = _snapshot_acceptance_decision(
    decision_id="decision-bm05-raw-context-rejected-001",
    parser_outcome_status=BeaconParserOutcomeStatus.CLEAN,
    parser_evidence_reference=_BM05_RAW_CONTEXT_EVIDENCE,
    acceptance_outcome=BeaconSnapshotAcceptanceOutcome.REJECTED,
    rejection_reason=BeaconSnapshotRejectionReason.RAW_HTML_SEARCH_CORE_CONTEXT_PAYLOAD,
)

_BM05_THRESHOLD_DEFERRED_ACCEPTANCE = _snapshot_acceptance_decision(
    decision_id="decision-bm05-threshold-deferred-001",
    parser_outcome_status=BeaconParserOutcomeStatus.CLEAN,
    parser_evidence_reference=_BM05_THRESHOLD_DEFERRED_EVIDENCE,
    acceptance_outcome=BeaconSnapshotAcceptanceOutcome.DEFERRED,
    rejection_reason=BeaconSnapshotRejectionReason.INVENTED_NUMERIC_ACCEPTANCE_THRESHOLD,
)

_BM05_UNSUPPORTED_PARAMETERS_ACCEPTANCE = _snapshot_acceptance_decision(
    decision_id="decision-bm05-unsupported-parameters-rejected-001",
    parser_outcome_status=BeaconParserOutcomeStatus.CLEAN,
    parser_evidence_reference=_BM05_UNSUPPORTED_PARAMETERS_EVIDENCE,
    acceptance_outcome=BeaconSnapshotAcceptanceOutcome.REJECTED,
    rejection_reason=BeaconSnapshotRejectionReason.UNSUPPORTED_PARAMETERS_SILENTLY_ACCEPTED,
    unsupported_parameters=("unsupported=synthetic",),
)

_BM05_CLEAN_SNAPSHOT = _snapshot(
    snapshot_id="snap-bm-050",
    status=BeaconParserOutcomeStatus.CLEAN,
    accepted_as_clean=True,
    evidence_reference="evidence-bm-050",
    parser_evidence_reference=_BM05_CLEAN_EVIDENCE,
    normalized_filter_values=("city=synthetic-city", "category=synthetic-category"),
)
_BM05_MALFORMED_SNAPSHOT = _snapshot(
    snapshot_id="snap-bm-051",
    status=BeaconParserOutcomeStatus.MALFORMED,
    accepted_as_clean=False,
    evidence_reference="evidence-bm-051",
    parser_evidence_reference=_BM05_MALFORMED_EVIDENCE,
    warning_codes=("MALFORMED_SHAPE",),
)
_BM05_INCOMPLETE_SNAPSHOT = _snapshot(
    snapshot_id="snap-bm-052",
    status=BeaconParserOutcomeStatus.INCOMPLETE,
    accepted_as_clean=False,
    evidence_reference="evidence-bm-052",
    parser_evidence_reference=_BM05_INCOMPLETE_EVIDENCE,
    warning_codes=("INCOMPLETE_RESULT",),
)
_BM05_CAPTCHA_SNAPSHOT = _snapshot(
    snapshot_id="snap-bm-053",
    status=BeaconParserOutcomeStatus.CAPTCHA_AFFECTED,
    accepted_as_clean=False,
    evidence_reference="evidence-bm-053",
    parser_evidence_reference=_BM05_CAPTCHA_EVIDENCE,
    warning_codes=("CAPTCHA_BLOCK",),
)
_BM05_BLOCKED_SNAPSHOT = _snapshot(
    snapshot_id="snap-bm-054",
    status=BeaconParserOutcomeStatus.BLOCKED,
    accepted_as_clean=False,
    evidence_reference="evidence-bm-054",
    parser_evidence_reference=_BM05_BLOCKED_EVIDENCE,
    warning_codes=("BLOCKED_ROUTE",),
)
_BM05_ROUTE_FAILED_SNAPSHOT = _snapshot(
    snapshot_id="snap-bm-055",
    status=BeaconParserOutcomeStatus.ROUTE_FAILED,
    accepted_as_clean=False,
    evidence_reference="evidence-bm-055",
    parser_evidence_reference=_BM05_ROUTE_FAILED_EVIDENCE,
    warning_codes=("ROUTE_FAILED",),
)
_BM05_AMBIGUOUS_SNAPSHOT = _snapshot(
    snapshot_id="snap-bm-056",
    status=BeaconParserOutcomeStatus.AMBIGUOUS,
    accepted_as_clean=False,
    evidence_reference="evidence-bm-056",
    parser_evidence_reference=_BM05_AMBIGUOUS_EVIDENCE,
    warning_codes=("AMBIGUOUS_EVIDENCE",),
)
_BM05_UNSUPPORTED_SNAPSHOT = _snapshot(
    snapshot_id="snap-bm-057",
    status=BeaconParserOutcomeStatus.UNSUPPORTED,
    accepted_as_clean=False,
    evidence_reference="evidence-bm-057",
    parser_evidence_reference=_BM05_UNSUPPORTED_EVIDENCE,
    unsupported_parameters=("unsupported=synthetic",),
    warning_codes=("UNSUPPORTED_OUTCOME",),
)
_BM05_RAW_PROVIDER_AUTHORITY_SNAPSHOT = _snapshot(
    snapshot_id="snap-bm-058",
    status=BeaconParserOutcomeStatus.CLEAN,
    accepted_as_clean=False,
    evidence_reference="evidence-bm-058",
    parser_evidence_reference=_BM05_RAW_PROVIDER_AUTHORITY_EVIDENCE,
    warning_codes=("RAW_PROVIDER_PAYLOAD_AUTHORITY",),
)
_BM05_RAW_HTML_SNAPSHOT = _snapshot(
    snapshot_id="snap-bm-059",
    status=BeaconParserOutcomeStatus.CLEAN,
    accepted_as_clean=False,
    evidence_reference="evidence-bm-059",
    parser_evidence_reference=_BM05_RAW_HTML_EVIDENCE,
    warning_codes=("RAW_HTML_PAYLOAD",),
)
_BM05_RAW_SEARCH_CORE_SNAPSHOT = _snapshot(
    snapshot_id="snap-bm-060",
    status=BeaconParserOutcomeStatus.CLEAN,
    accepted_as_clean=False,
    evidence_reference="evidence-bm-060",
    parser_evidence_reference=_BM05_RAW_SEARCH_CORE_EVIDENCE,
    warning_codes=("RAW_SEARCH_CORE_PAYLOAD",),
)
_BM05_RAW_CONTEXT_SNAPSHOT = _snapshot(
    snapshot_id="snap-bm-061",
    status=BeaconParserOutcomeStatus.CLEAN,
    accepted_as_clean=False,
    evidence_reference="evidence-bm-061",
    parser_evidence_reference=_BM05_RAW_CONTEXT_EVIDENCE,
    warning_codes=("RAW_CONTEXT_PAYLOAD",),
)
_BM05_THRESHOLD_DEFERRED_SNAPSHOT = _snapshot(
    snapshot_id="snap-bm-062",
    status=BeaconParserOutcomeStatus.CLEAN,
    accepted_as_clean=False,
    evidence_reference="evidence-bm-062",
    parser_evidence_reference=_BM05_THRESHOLD_DEFERRED_EVIDENCE,
    warning_codes=("THRESHOLD_DEFERRED",),
)
_BM05_UNSUPPORTED_PARAMETERS_SNAPSHOT = _snapshot(
    snapshot_id="snap-bm-063",
    status=BeaconParserOutcomeStatus.CLEAN,
    accepted_as_clean=False,
    evidence_reference="evidence-bm-063",
    parser_evidence_reference=_BM05_UNSUPPORTED_PARAMETERS_EVIDENCE,
    unsupported_parameters=("unsupported=synthetic",),
    warning_codes=("UNSUPPORTED_PARAMETERS",),
)

_OWN_ACTIVE_BEACON = _beacon(
    beacon_id="beacon-bm-001",
    account_id=_OWN_ACCOUNT_ID,
    display_name="Synthetic own-account active beacon",
    lifecycle_state=BeaconLifecycleState.ACTIVE,
    current_revision_id="rev-bm-001",
    source_reference="source-ref-bm-001",
    snapshot=_ACTIVE_SNAPSHOT,
    overrides=(_ACTIVE_OVERRIDE,),
)

_FOREIGN_ACCESS_BEACON = _beacon(
    beacon_id="beacon-bm-002",
    account_id=_FOREIGN_ACCOUNT_ID,
    display_name="Synthetic foreign-account beacon",
    lifecycle_state=BeaconLifecycleState.ACTIVE,
    current_revision_id="rev-bm-002",
    source_reference="source-ref-bm-002",
    snapshot=_ACTIVE_SNAPSHOT,
)

_DUPLICATE_SAME_ACCOUNT_FIRST = _beacon(
    beacon_id="beacon-bm-003",
    account_id=_OWN_ACCOUNT_ID,
    display_name="Synthetic same-account duplicate beacon A",
    lifecycle_state=BeaconLifecycleState.READY,
    current_revision_id="rev-bm-003",
    source_reference="source-ref-bm-003",
    snapshot=_ACTIVE_SNAPSHOT,
)

_DUPLICATE_SAME_ACCOUNT_SECOND = _beacon(
    beacon_id="beacon-bm-004",
    account_id=_OWN_ACCOUNT_ID,
    display_name="Synthetic same-account duplicate beacon B",
    lifecycle_state=BeaconLifecycleState.READY,
    current_revision_id="rev-bm-004",
    source_reference="source-ref-bm-003",
    snapshot=_ACTIVE_SNAPSHOT,
)

_DUPLICATE_CROSS_ACCOUNT = _beacon(
    beacon_id="beacon-bm-005",
    account_id=_FOREIGN_ACCOUNT_ID,
    display_name="Synthetic cross-account duplicate beacon",
    lifecycle_state=BeaconLifecycleState.READY,
    current_revision_id="rev-bm-005",
    source_reference="source-ref-bm-003",
    snapshot=_ACTIVE_SNAPSHOT,
)

_FREE_COUNTRY_WIDE_BLOCKED = BeaconActivationDecision(
    beacon_id="beacon-bm-006",
    account_id=_OWN_ACCOUNT_ID,
    access_tier=BeaconAccessTier.FREE,
    status=BeaconDecisionStatus.BLOCKED,
    requested_interval_minutes=180,
    interval_floor_minutes=180,
    interval_step_minutes=180,
    active_beacon_limit=1,
    requested_country_wide=True,
    country_wide_allowed=False,
    city_required=True,
    requested_city=None,
    selected_beacon_id=None,
    expiry_outcomes=(BeaconExpiryOutcome.USER_CHOICE_REQUIRED,),
    reason_code="FREE_COUNTRY_WIDE_BLOCKED",
    reason="Synthetic free-tier country-wide activation requires a city.",
)

_BASIC_COUNTRY_WIDE_ALLOWED = BeaconActivationDecision(
    beacon_id="beacon-bm-007",
    account_id=_OWN_ACCOUNT_ID,
    access_tier=BeaconAccessTier.BASIC,
    status=BeaconDecisionStatus.ALLOWED,
    requested_interval_minutes=5,
    interval_floor_minutes=5,
    interval_step_minutes=5,
    active_beacon_limit=5,
    requested_country_wide=True,
    country_wide_allowed=True,
    city_required=False,
    requested_city=None,
    selected_beacon_id=None,
    expiry_outcomes=(),
    reason_code="BASIC_COUNTRY_WIDE_ALLOWED",
    reason="Synthetic basic-tier country-wide activation is allowed.",
)

_FREE_INTERVAL_ACCEPTED = BeaconActivationDecision(
    beacon_id="beacon-bm-008",
    account_id=_OWN_ACCOUNT_ID,
    access_tier=BeaconAccessTier.FREE,
    status=BeaconDecisionStatus.ALLOWED,
    requested_interval_minutes=180,
    interval_floor_minutes=180,
    interval_step_minutes=180,
    active_beacon_limit=1,
    requested_country_wide=False,
    country_wide_allowed=False,
    city_required=True,
    requested_city="synthetic-city",
    selected_beacon_id=None,
    expiry_outcomes=(),
    reason_code="FREE_INTERVAL_ACCEPTED",
    reason="Synthetic free-tier interval meets the approved floor and step.",
)

_BASIC_INTERVAL_ACCEPTED = BeaconActivationDecision(
    beacon_id="beacon-bm-009",
    account_id=_OWN_ACCOUNT_ID,
    access_tier=BeaconAccessTier.BASIC,
    status=BeaconDecisionStatus.ALLOWED,
    requested_interval_minutes=5,
    interval_floor_minutes=5,
    interval_step_minutes=5,
    active_beacon_limit=5,
    requested_country_wide=False,
    country_wide_allowed=True,
    city_required=False,
    requested_city=None,
    selected_beacon_id=None,
    expiry_outcomes=(),
    reason_code="BASIC_INTERVAL_ACCEPTED",
    reason="Synthetic basic-tier interval meets the approved floor and step.",
)

_ARCHIVED_HISTORY_ENTRY = BeaconHistoryEntry(
    history_entry_id="history-bm-001",
    beacon_id="beacon-bm-010",
    account_id=_OWN_ACCOUNT_ID,
    outcome=BeaconHistoryOutcome.ARCHIVED,
    restorable=True,
    recorded_at=_RECORD_AT,
    minimal_snapshot_reference="minimal-snapshot-bm-001",
    reason="Archived synthetic beacon is excluded from active limit.",
    counts_toward_active_limit=False,
)

_ARCHIVED_BEACON = _beacon(
    beacon_id="beacon-bm-010",
    account_id=_OWN_ACCOUNT_ID,
    display_name="Synthetic archived beacon",
    lifecycle_state=BeaconLifecycleState.ARCHIVED,
    current_revision_id="rev-bm-010",
    source_reference="source-ref-bm-010",
    snapshot=_ACTIVE_SNAPSHOT,
    restorable=True,
    counts_toward_active_limit=False,
    history_entries=(_ARCHIVED_HISTORY_ENTRY,),
)

_PERMANENTLY_DELETED_HISTORY_ENTRY = BeaconHistoryEntry(
    history_entry_id="history-bm-002",
    beacon_id="beacon-bm-011",
    account_id=_OWN_ACCOUNT_ID,
    outcome=BeaconHistoryOutcome.PERMANENTLY_DELETED,
    restorable=False,
    recorded_at=_RECORD_AT,
    minimal_snapshot_reference="minimal-snapshot-bm-002",
    reason="Permanent synthetic deletion is terminal.",
    counts_toward_active_limit=False,
)

_PERMANENTLY_DELETED_BEACON = _beacon(
    beacon_id="beacon-bm-011",
    account_id=_OWN_ACCOUNT_ID,
    display_name="Synthetic permanently deleted beacon",
    lifecycle_state=BeaconLifecycleState.PERMANENTLY_DELETED,
    current_revision_id="rev-bm-011",
    source_reference="source-ref-bm-011",
    snapshot=_ACTIVE_SNAPSHOT,
    restorable=False,
    counts_toward_active_limit=False,
    history_entries=(_PERMANENTLY_DELETED_HISTORY_ENTRY,),
)

_PATCH_SAVE_MUTATION = BeaconMutationDecision(
    beacon_id="beacon-bm-012",
    account_id=_OWN_ACCOUNT_ID,
    status=BeaconDecisionStatus.ALLOWED,
    patch_fields=("display_name", "interval_minutes"),
    applied_fields=("display_name",),
    same_field_concurrent_change=False,
    last_write_wins=False,
    current_revision_id="rev-bm-012a",
    new_revision_id="rev-bm-012b",
    current_configuration_replaced=True,
    retained_evidence_references=("audit-bm-012",),
    conflict_fields=(),
    reason_code="PATCH_APPLIED_ONLY_SUPPLIED_FIELDS",
    reason="Synthetic patch save applies only supplied fields.",
)

_LAST_WRITE_WINS_MUTATION = BeaconMutationDecision(
    beacon_id="beacon-bm-013",
    account_id=_OWN_ACCOUNT_ID,
    status=BeaconDecisionStatus.ALLOWED,
    patch_fields=("interval_minutes",),
    applied_fields=("interval_minutes",),
    same_field_concurrent_change=True,
    last_write_wins=True,
    current_revision_id="rev-bm-013a",
    new_revision_id="rev-bm-013b",
    current_configuration_replaced=True,
    retained_evidence_references=("audit-bm-013",),
    conflict_fields=("interval_minutes",),
    reason_code="LAST_WRITE_WINS_AUTHORITATIVE",
    reason="Synthetic same-field conflict resolves by later successful save.",
)

_BM06_SUPPORTED_OVERRIDE_OPERATION = _override_patch_operation(
    field_name="district",
    support_status=BeaconOverrideFieldSupportStatus.SUPPORTED,
    outcome=BeaconOverrideApplicationOutcome.APPLIED,
    requested_values=("north",),
    applied_values=("north",),
    parser_filter_evidence_reference="parser-filter-evidence-bm06-supported-001",
    override_evidence_reference="override-evidence-bm06-supported-001",
)

_BM06_UNSUPPORTED_OVERRIDE_OPERATION = _override_patch_operation(
    field_name="unsupported_field",
    support_status=BeaconOverrideFieldSupportStatus.UNSUPPORTED,
    outcome=BeaconOverrideApplicationOutcome.BLOCKED,
    requested_values=("unexpected",),
    applied_values=None,
    parser_filter_evidence_reference="parser-filter-evidence-bm06-unsupported-001",
    override_evidence_reference="override-evidence-bm06-unsupported-001",
    rejection_reason=BeaconOverrideRejectionReason.UNSUPPORTED_FIELD,
)

_BM06_UNCERTAIN_OVERRIDE_OPERATION = _override_patch_operation(
    field_name="uncertain_field",
    support_status=BeaconOverrideFieldSupportStatus.UNCERTAIN,
    outcome=BeaconOverrideApplicationOutcome.REJECTED,
    requested_values=("maybe",),
    applied_values=None,
    parser_filter_evidence_reference="parser-filter-evidence-bm06-uncertain-001",
    override_evidence_reference="override-evidence-bm06-uncertain-001",
    rejection_reason=BeaconOverrideRejectionReason.UNCERTAIN_EVIDENCE,
)

_BM06_AMBIGUOUS_OVERRIDE_OPERATION = _override_patch_operation(
    field_name="ambiguous_field",
    support_status=BeaconOverrideFieldSupportStatus.AMBIGUOUS,
    outcome=BeaconOverrideApplicationOutcome.BLOCKED,
    requested_values=("ambiguous",),
    applied_values=None,
    parser_filter_evidence_reference="parser-filter-evidence-bm06-ambiguous-001",
    override_evidence_reference="override-evidence-bm06-ambiguous-001",
    rejection_reason=BeaconOverrideRejectionReason.AMBIGUOUS_EVIDENCE,
)

_BM06_SOURCE_URL_OVERRIDE_OPERATION = _override_patch_operation(
    field_name="source_url",
    support_status=BeaconOverrideFieldSupportStatus.SUPPORTED,
    outcome=BeaconOverrideApplicationOutcome.REJECTED,
    requested_values=("https://example.invalid/search?query=blocked-source-url",),
    applied_values=None,
    parser_filter_evidence_reference="parser-filter-evidence-bm06-source-url-001",
    override_evidence_reference="override-evidence-bm06-source-url-001",
    rejection_reason=BeaconOverrideRejectionReason.SOURCE_URL_OVERRIDE,
)

_BM06_MULTIVALUE_OVERRIDE_OPERATION = _override_patch_operation(
    field_name="amenities",
    support_status=BeaconOverrideFieldSupportStatus.SUPPORTED,
    outcome=BeaconOverrideApplicationOutcome.APPLIED,
    requested_values=("wifi", "parking"),
    applied_values=("wifi", "parking"),
    parser_filter_evidence_reference="parser-filter-evidence-bm06-multivalue-001",
    override_evidence_reference="override-evidence-bm06-multivalue-001",
)

_BM06_MULTIVALUE_COLLAPSE_OVERRIDE_OPERATION = _override_patch_operation(
    field_name="amenities",
    support_status=BeaconOverrideFieldSupportStatus.SUPPORTED,
    outcome=BeaconOverrideApplicationOutcome.BLOCKED,
    requested_values=("wifi", "parking"),
    applied_values=None,
    parser_filter_evidence_reference="parser-filter-evidence-bm06-multivalue-collapse-001",
    override_evidence_reference="override-evidence-bm06-multivalue-collapse-001",
    rejection_reason=BeaconOverrideRejectionReason.MULTIVALUE_COLLAPSE,
)

_BM06_SINGLE_VALUE_MISMATCH_OVERRIDE_OPERATION = BeaconOverridePatchOperation.model_construct(
    field_name="district",
    support_status=BeaconOverrideFieldSupportStatus.SUPPORTED,
    outcome=BeaconOverrideApplicationOutcome.APPLIED,
    requested_values=("north",),
    applied_values=("south",),
    parser_filter_evidence_reference="parser-filter-evidence-bm06-single-value-mismatch-001",
    override_evidence_reference="override-evidence-bm06-single-value-mismatch-001",
    rejection_reason=None,
)

_BM06_ACCEPTED_EFFECTIVE_SOURCE_URL = _source_url(
    "evidence-bm06-effective-accepted-001",
    "https://example.invalid/search?query=beacon-management&city=synthetic&case=bm06-effective",
)

_BM06_REJECTED_EFFECTIVE_SOURCE_URL = _source_url(
    "evidence-bm06-effective-rejected-001",
    "https://example.invalid/search?query=beacon-management&city=synthetic&case=bm06-rejected",
)

_BM06_ACCEPTED_EFFECTIVE_SNAPSHOT = _snapshot(
    snapshot_id="snap-bm06-effective-001",
    status=BeaconParserOutcomeStatus.CLEAN,
    accepted_as_clean=True,
    evidence_reference="evidence-bm06-effective-snapshot-accepted-001",
    parser_evidence_reference=_parser_evidence_reference(
        evidence_reference="parser-evidence-bm06-effective-accepted-001"
    ),
    normalized_filter_values=("city=synthetic-city", "category=synthetic-category"),
)

_BM06_REJECTED_EFFECTIVE_SNAPSHOT = _snapshot(
    snapshot_id="snap-bm06-effective-002",
    status=BeaconParserOutcomeStatus.AMBIGUOUS,
    accepted_as_clean=False,
    evidence_reference="evidence-bm06-effective-snapshot-rejected-001",
    parser_evidence_reference=_parser_evidence_reference(
        evidence_reference="parser-evidence-bm06-effective-rejected-001",
        safety_class=BeaconParserEvidenceSafetyClass.AMBIGUOUS,
    ),
    warning_codes=("AMBIGUOUS_SNAPSHOT",),
)

_BM06_ACCEPTED_EFFECTIVE_CONFIGURATION = _effective_configuration_decision(
    decision_id="decision-bm06-effective-accepted-001",
    beacon_id="beacon-bm06-effective-001",
    account_id=_OWN_ACCOUNT_ID,
    source_url=_BM06_ACCEPTED_EFFECTIVE_SOURCE_URL,
    accepted_snapshot=_BM06_ACCEPTED_EFFECTIVE_SNAPSHOT,
    override_operations=(
        _BM06_SUPPORTED_OVERRIDE_OPERATION,
        _BM06_MULTIVALUE_OVERRIDE_OPERATION,
    ),
    status=BeaconDecisionStatus.ALLOWED,
    effective_configuration_reference="effective-config-bm06-001",
    authoritative_state_reference="authoritative-state-bm06-effective-001",
)

_BM06_SINGLE_VALUE_MISMATCH_EFFECTIVE_CONFIGURATION = (
    BeaconEffectiveConfigurationDecision.model_construct(
        decision_id="decision-bm06-effective-single-value-mismatch-001",
        beacon_id="beacon-bm06-effective-single-value-mismatch-001",
        account_id=_OWN_ACCOUNT_ID,
        source_url=_BM06_ACCEPTED_EFFECTIVE_SOURCE_URL,
        accepted_snapshot=_BM06_ACCEPTED_EFFECTIVE_SNAPSHOT,
        override_operations=(_BM06_SINGLE_VALUE_MISMATCH_OVERRIDE_OPERATION,),
        status=BeaconDecisionStatus.ALLOWED,
        effective_configuration_reference="effective-config-bm06-single-value-mismatch-001",
        authoritative_state_reference=(
            "authoritative-state-bm06-effective-single-value-mismatch-001"
        ),
        source_url_overwritten_by_snapshot=False,
        source_url_overwritten_by_override=False,
        rejection_reason=None,
    )
)

_BM06_REJECTED_EFFECTIVE_CONFIGURATION = _effective_configuration_decision(
    decision_id="decision-bm06-effective-rejected-001",
    beacon_id="beacon-bm06-effective-002",
    account_id=_OWN_ACCOUNT_ID,
    source_url=_BM06_REJECTED_EFFECTIVE_SOURCE_URL,
    accepted_snapshot=_BM06_REJECTED_EFFECTIVE_SNAPSHOT,
    override_operations=(),
    status=BeaconDecisionStatus.REJECTED,
    effective_configuration_reference="effective-config-bm06-rejected-001",
    authoritative_state_reference="authoritative-state-bm06-effective-rejected-001",
    rejection_reason=BeaconEffectiveConfigurationRejectionReason.NON_ACCEPTED_SNAPSHOT,
)

_BM06_PATCH_MERGE_DECISION = _patch_save_decision(
    decision_id="decision-bm06-patch-merge-001",
    beacon_id="beacon-bm06-patch-merge-001",
    account_id=_OWN_ACCOUNT_ID,
    status=BeaconDecisionStatus.ALLOWED,
    patch_fields=("display_name", "interval_minutes"),
    applied_fields=("display_name", "interval_minutes"),
    preserved_fields=("source_url", "accepted_snapshot"),
    different_field_updates_merge=True,
    authoritative_state_reference="authoritative-state-bm06-patch-merge-001",
)

_BM06_PATCH_LAST_WRITE_WINS_DECISION = _patch_save_decision(
    decision_id="decision-bm06-patch-last-write-wins-001",
    beacon_id="beacon-bm06-patch-lww-001",
    account_id=_OWN_ACCOUNT_ID,
    status=BeaconDecisionStatus.ALLOWED,
    patch_fields=("interval_minutes",),
    applied_fields=("interval_minutes",),
    preserved_fields=("display_name", "source_url"),
    same_field_concurrent_change=True,
    last_write_wins=True,
    authoritative_state_reference="authoritative-state-bm06-patch-lww-001",
)

_BM06_PATCH_STALE_FULL_FORM_DECISION = _patch_save_decision(
    decision_id="decision-bm06-patch-stale-full-form-001",
    beacon_id="beacon-bm06-patch-stale-001",
    account_id=_OWN_ACCOUNT_ID,
    status=BeaconDecisionStatus.REJECTED,
    patch_fields=("display_name", "interval_minutes", "source_url"),
    applied_fields=("display_name", "interval_minutes"),
    preserved_fields=(),
    stale_full_form_overwrite=True,
    rejection_reason=BeaconPatchSaveRejectionReason.STALE_FULL_FORM_OVERWRITE,
)

_SOURCE_URL_PREPARED_CREATED = _source_url(
    "evidence-bm-prep-created-001",
    "https://example.invalid/search?query=beacon-management&city=synthetic&case=created",
)

_SOURCE_URL_PREPARED_REPLAYED = _source_url(
    "evidence-bm-prep-replayed-001",
    "https://example.invalid/search?query=beacon-management&city=synthetic&case=replayed",
)

_SOURCE_URL_PREPARED_MALFORMED = _source_url(
    "evidence-bm-prep-malformed-001",
    "https://example.invalid/%zz-malformed-source-url",
)

_SOURCE_URL_PREPARED_TRACKING = _source_url(
    "evidence-bm-prep-tracking-001",
    "https://example.invalid/search?query=beacon-management&utm_source=synthetic&utm_campaign=fixture",
)

_SOURCE_URL_PREPARED_SHELL = _source_url(
    "evidence-bm-prep-shell-001",
    "https://example.invalid/search?query=beacon-management&city=synthetic&case=shell",
)

_SOURCE_URL_PREPARED_FINGERPRINT = _source_url(
    "evidence-bm-prep-fingerprint-001",
    "https://example.invalid/search?query=beacon-management&city=synthetic&case=fingerprint",
)

_SOURCE_URL_PREPARED_OVERRIDE = _source_url(
    "evidence-bm-prep-override-001",
    "https://example.invalid/search?query=beacon-management&city=synthetic&case=override",
)

_SOURCE_URL_PREPARED_CREATED_POLICY = _prepared_source_url(
    prepared_source_url_reference="prepared-ref-bm-prep-created-001",
    source_url=_SOURCE_URL_PREPARED_CREATED,
    classification=BeaconSourceUrlSafetyClassification.PRESERVED,
)

_SOURCE_URL_PREPARED_REPLAYED_POLICY = _prepared_source_url(
    prepared_source_url_reference="prepared-ref-bm-prep-replayed-001",
    source_url=_SOURCE_URL_PREPARED_REPLAYED,
    classification=BeaconSourceUrlSafetyClassification.PRESERVED,
)

_SOURCE_URL_PREPARED_MALFORMED_POLICY = _prepared_source_url(
    prepared_source_url_reference="prepared-ref-bm-prep-malformed-001",
    source_url=_SOURCE_URL_PREPARED_MALFORMED,
    classification=BeaconSourceUrlSafetyClassification.MALFORMED,
)

_SOURCE_URL_PREPARED_FINGERPRINT_POLICY = _prepared_source_url(
    prepared_source_url_reference="prepared-ref-bm-prep-fingerprint-001",
    source_url=_SOURCE_URL_PREPARED_FINGERPRINT,
    classification=BeaconSourceUrlSafetyClassification.PRESERVED,
    opaque_fingerprint_reference="fingerprint-bm-prep-001",
    fingerprint_policy=_fingerprint_policy(
        policy_reference="policy-bm-prep-fingerprint-001",
        comparison_reference="comparison-bm-prep-001",
        idempotency_reference="idempotency-bm-prep-001",
        debug_reference="debug-bm-prep-001",
    ),
)

_SOURCE_URL_PREPARED_OVERRIDE_POLICY = _prepared_source_url(
    prepared_source_url_reference="prepared-ref-bm-prep-override-001",
    source_url=_SOURCE_URL_PREPARED_OVERRIDE,
    classification=BeaconSourceUrlSafetyClassification.PRESERVED,
)

_SOURCE_URL_PREPARED_TRACKING_POLICY = _prepared_source_url(
    prepared_source_url_reference="prepared-ref-bm-prep-tracking-001",
    source_url=_SOURCE_URL_PREPARED_TRACKING,
    classification=BeaconSourceUrlSafetyClassification.PRESERVED,
)

_SOURCE_URL_PREPARED_SHELL_POLICY = _prepared_source_url(
    prepared_source_url_reference="prepared-ref-bm-prep-shell-001",
    source_url=_SOURCE_URL_PREPARED_SHELL,
    classification=BeaconSourceUrlSafetyClassification.BLOCKED,
)

_SOURCE_URL_CREATED_BASIS = _idempotency_basis(
    source_url_reference=_SOURCE_URL_PREPARED_CREATED.evidence_reference,
    command_reference="command-bm-prep-created-001",
    account_id=_OWN_ACCOUNT_ID,
    beacon_id="beacon-bm-prep-created-001",
)

_SOURCE_URL_REPLAYED_BASIS = _idempotency_basis(
    source_url_reference=_SOURCE_URL_PREPARED_REPLAYED.evidence_reference,
    command_reference="command-bm-prep-replayed-001",
    account_id=_OWN_ACCOUNT_ID,
    beacon_id="beacon-bm-prep-replayed-001",
    requested_beacon_id="requested-beacon-bm-prep-replayed-001",
)

_SOURCE_URL_MALFORMED_BASIS = _idempotency_basis(
    source_url_reference=_SOURCE_URL_PREPARED_MALFORMED.evidence_reference,
    command_reference="command-bm-prep-malformed-001",
    account_id=_OWN_ACCOUNT_ID,
    requested_beacon_id="requested-beacon-bm-prep-malformed-001",
)

_SOURCE_URL_TRACKING_BASIS = _idempotency_basis(
    source_url_reference=_SOURCE_URL_PREPARED_TRACKING.evidence_reference,
    command_reference="command-bm-prep-tracking-001",
    account_id=_OWN_ACCOUNT_ID,
    beacon_id="beacon-bm-prep-tracking-001",
)

_SOURCE_URL_SHELL_BASIS = _idempotency_basis(
    source_url_reference=_SOURCE_URL_PREPARED_SHELL.evidence_reference,
    command_reference="command-bm-prep-shell-001",
    account_id=_OWN_ACCOUNT_ID,
    requested_beacon_id="requested-beacon-bm-prep-shell-001",
)

_SOURCE_URL_OVERRIDE_BASIS = _idempotency_basis(
    source_url_reference=_SOURCE_URL_PREPARED_OVERRIDE.evidence_reference,
    command_reference="command-bm-prep-override-001",
    account_id=_OWN_ACCOUNT_ID,
    beacon_id="beacon-bm-prep-override-001",
)

_SOURCE_URL_PREP_CREATED_DECISION = _source_url_preparation_decision(
    decision_id="decision-bm-prep-created-001",
    account_id=_OWN_ACCOUNT_ID,
    beacon_id="beacon-bm-prep-created-001",
    source_url=_SOURCE_URL_PREPARED_CREATED,
    prepared_source_url=_SOURCE_URL_PREPARED_CREATED_POLICY,
    outcome=BeaconSourceUrlPreparationOutcome.CREATED,
    safe_reason_code="SOURCE_URL_CREATED_WITH_PRESERVATION",
    idempotency_basis=_SOURCE_URL_CREATED_BASIS,
)

_SOURCE_URL_PREP_REPLAYED_DECISION = _source_url_preparation_decision(
    decision_id="decision-bm-prep-replayed-001",
    account_id=_OWN_ACCOUNT_ID,
    beacon_id="beacon-bm-prep-replayed-001",
    requested_beacon_id="requested-beacon-bm-prep-replayed-001",
    source_url=_SOURCE_URL_PREPARED_REPLAYED,
    prepared_source_url=_SOURCE_URL_PREPARED_REPLAYED_POLICY,
    outcome=BeaconSourceUrlPreparationOutcome.REPLAYED,
    safe_reason_code="SOURCE_URL_REPLAYED_WITH_EXPLICIT_SCOPE",
    idempotency_basis=_SOURCE_URL_REPLAYED_BASIS,
)

_SOURCE_URL_PREP_MALFORMED_DECISION = _source_url_preparation_decision(
    decision_id="decision-bm-prep-malformed-001",
    account_id=_OWN_ACCOUNT_ID,
    requested_beacon_id="requested-beacon-bm-prep-malformed-001",
    source_url=_SOURCE_URL_PREPARED_MALFORMED,
    prepared_source_url=_SOURCE_URL_PREPARED_MALFORMED_POLICY,
    outcome=BeaconSourceUrlPreparationOutcome.REJECTED,
    safe_reason_code="SOURCE_URL_MALFORMED_REJECTED",
    idempotency_basis=_SOURCE_URL_MALFORMED_BASIS,
)

_SOURCE_URL_PREP_DUPLICATE_BLOCKING_POLICY_DECISION = _source_url_preparation_decision(
    decision_id="decision-bm-prep-duplicate-blocking-001",
    account_id=_OWN_ACCOUNT_ID,
    requested_beacon_id="requested-beacon-bm-prep-duplicate-blocking-001",
    source_url=_SOURCE_URL_PREPARED_CREATED,
    prepared_source_url=_SOURCE_URL_PREPARED_CREATED_POLICY,
    outcome=BeaconSourceUrlPreparationOutcome.REJECTED,
    safe_reason_code="DUPLICATE_URL_BLOCKING_POLICY_NOT_ALLOWED",
    idempotency_basis=_idempotency_basis(
        source_url_reference=_SOURCE_URL_PREPARED_CREATED.evidence_reference,
        command_reference="command-bm-prep-duplicate-blocking-001",
        account_id=_OWN_ACCOUNT_ID,
        requested_beacon_id="requested-beacon-bm-prep-duplicate-blocking-001",
    ),
)

_SOURCE_URL_PREP_SOURCE_ONLY_IDEMPOTENCY_DECISION = _source_url_preparation_decision(
    decision_id="decision-bm-prep-source-only-idempotency-001",
    account_id=_OWN_ACCOUNT_ID,
    requested_beacon_id="requested-beacon-bm-prep-source-only-idempotency-001",
    source_url=_SOURCE_URL_PREPARED_CREATED,
    prepared_source_url=_SOURCE_URL_PREPARED_CREATED_POLICY,
    outcome=BeaconSourceUrlPreparationOutcome.REJECTED,
    safe_reason_code="SOURCE_URL_ONLY_IDEMPOTENCY_BASIS_REJECTED",
    idempotency_basis=_idempotency_basis(
        source_url_reference=_SOURCE_URL_PREPARED_CREATED.evidence_reference,
        command_reference="command-bm-prep-source-only-idempotency-001",
        account_id=_OWN_ACCOUNT_ID,
        requested_beacon_id="requested-beacon-bm-prep-source-only-idempotency-001",
    ),
)

_SOURCE_URL_PREP_OVERRIDE_DECISION = _source_url_preparation_decision(
    decision_id="decision-bm-prep-override-001",
    account_id=_OWN_ACCOUNT_ID,
    beacon_id="beacon-bm-prep-override-001",
    source_url=_SOURCE_URL_PREPARED_OVERRIDE,
    prepared_source_url=_SOURCE_URL_PREPARED_OVERRIDE_POLICY,
    outcome=BeaconSourceUrlPreparationOutcome.CREATED,
    safe_reason_code="SOURCE_URL_PRESERVED_ACROSS_OVERRIDE",
    idempotency_basis=_SOURCE_URL_OVERRIDE_BASIS,
)

_SOURCE_URL_PREP_FINGERPRINT_DECISION = _source_url_preparation_decision(
    decision_id="decision-bm-prep-fingerprint-001",
    account_id=_OWN_ACCOUNT_ID,
    beacon_id="beacon-bm-prep-fingerprint-001",
    source_url=_SOURCE_URL_PREPARED_FINGERPRINT,
    prepared_source_url=_SOURCE_URL_PREPARED_FINGERPRINT_POLICY,
    outcome=BeaconSourceUrlPreparationOutcome.CREATED,
    safe_reason_code="OPAQUE_FINGERPRINT_REFERENCE_ONLY",
    idempotency_basis=_idempotency_basis(
        source_url_reference=_SOURCE_URL_PREPARED_FINGERPRINT.evidence_reference,
        command_reference="command-bm-prep-fingerprint-001",
        account_id=_OWN_ACCOUNT_ID,
        beacon_id="beacon-bm-prep-fingerprint-001",
    ),
    opaque_fingerprint_reference="fingerprint-bm-prep-001",
)

_SOURCE_URL_PREP_TRACKING_DECISION = _source_url_preparation_decision(
    decision_id="decision-bm-prep-tracking-001",
    account_id=_OWN_ACCOUNT_ID,
    beacon_id="beacon-bm-prep-tracking-001",
    source_url=_SOURCE_URL_PREPARED_TRACKING,
    prepared_source_url=_SOURCE_URL_PREPARED_TRACKING_POLICY,
    outcome=BeaconSourceUrlPreparationOutcome.CREATED,
    safe_reason_code="TRACKING_PARAMS_IGNORED_ONLY_WITH_POLICY",
    idempotency_basis=_SOURCE_URL_TRACKING_BASIS,
    tracking_params_ignored=True,
    tracking_policy_reference="policy-bm-prep-tracking-001",
)

_SOURCE_URL_PREP_SHELL_DECISION = _source_url_preparation_decision(
    decision_id="decision-bm-prep-shell-001",
    account_id=_OWN_ACCOUNT_ID,
    requested_beacon_id="requested-beacon-bm-prep-shell-001",
    source_url=_SOURCE_URL_PREPARED_SHELL,
    prepared_source_url=_SOURCE_URL_PREPARED_SHELL_POLICY,
    outcome=BeaconSourceUrlPreparationOutcome.BLOCKED,
    safe_reason_code="EXTERNAL_URL_NOT_INTERPOLATED_INTO_SHELL",
    idempotency_basis=_SOURCE_URL_SHELL_BASIS,
    shell_command_text="curl --fail --silent <blocked-source-url>",
)

_OWNER_VERIFIED_CONTEXT = _actor_context(
    actor_context_id="actor-bm-001",
    actor_kind=BeaconActorKind.ACCOUNT_OWNER,
    is_verified=True,
    account_id=_OWN_ACCOUNT_ID,
    actor_reference_id="actor-ref-bm-owner-001",
)

_OWNER_UNVERIFIED_CONTEXT = _actor_context(
    actor_context_id="actor-bm-002",
    actor_kind=BeaconActorKind.ACCOUNT_OWNER,
    is_verified=False,
    account_id=_OWN_ACCOUNT_ID,
    actor_reference_id="actor-ref-bm-owner-002",
)

_FOREIGN_OWNER_CONTEXT = _actor_context(
    actor_context_id="actor-bm-003",
    actor_kind=BeaconActorKind.ACCOUNT_OWNER,
    is_verified=True,
    account_id=_OWN_ACCOUNT_ID,
    actor_reference_id="actor-ref-bm-owner-003",
)

_ADMIN_SUPPORT_CONTEXT = _actor_context(
    actor_context_id="actor-bm-004",
    actor_kind=BeaconActorKind.ADMIN_SUPPORT,
    is_verified=True,
    account_id=_SUPPORT_ACCOUNT_ID,
    actor_reference_id="actor-ref-bm-support-001",
)

_ADMIN_SUPPORT_UNVERIFIED_CONTEXT = _actor_context(
    actor_context_id="actor-bm-009",
    actor_kind=BeaconActorKind.ADMIN_SUPPORT,
    is_verified=False,
    account_id=_SUPPORT_ACCOUNT_ID,
    actor_reference_id="actor-ref-bm-support-002",
)

_TELEGRAM_CLIENT_CONTEXT = _actor_context(
    actor_context_id="actor-bm-005",
    actor_kind=BeaconActorKind.ANONYMOUS,
    is_verified=False,
    client_channel_flag="TELEGRAM",
    actor_reference_id="actor-ref-bm-telegram-001",
)

_WEB_CLIENT_CONTEXT = _actor_context(
    actor_context_id="actor-bm-006",
    actor_kind=BeaconActorKind.ANONYMOUS,
    is_verified=False,
    client_channel_flag="WEB",
    actor_reference_id="actor-ref-bm-web-001",
)

_ADMIN_CLIENT_CONTEXT = _actor_context(
    actor_context_id="actor-bm-007",
    actor_kind=BeaconActorKind.ANONYMOUS,
    is_verified=False,
    client_channel_flag="ADMIN",
    actor_reference_id="actor-ref-bm-admin-flag-001",
)

_SYSTEM_CONTEXT = _actor_context(
    actor_context_id="actor-bm-008",
    actor_kind=BeaconActorKind.SYSTEM,
    is_verified=False,
    actor_reference_id="actor-ref-bm-system-001",
)

_OWN_UPDATE_ALLOWED = _ownership_decision(
    decision_id="decision-bm-001",
    protected_action=BeaconProtectedAction.UPDATE_BEACON,
    actor_context=_OWNER_VERIFIED_CONTEXT,
    beacon_id="beacon-bm-001",
    beacon_account_id=_OWN_ACCOUNT_ID,
    outcome=BeaconAuthorizationOutcome.ALLOWED,
    safe_reason_code="OWNER_UPDATE_ALLOWED",
    reason="Verified owner may update the owned Beacon.",
)

_OWN_UPDATE_REQUIRES_VERIFIED = _ownership_decision(
    decision_id="decision-bm-002",
    protected_action=BeaconProtectedAction.UPDATE_BEACON,
    actor_context=_OWNER_UNVERIFIED_CONTEXT,
    beacon_id="beacon-bm-001",
    beacon_account_id=_OWN_ACCOUNT_ID,
    outcome=BeaconAuthorizationOutcome.REQUIRES_VERIFIED_ACTOR,
    safe_reason_code="OWNER_UPDATE_REQUIRES_VERIFIED_ACTOR",
    reason="Unverified owner mutation is blocked until the actor is verified.",
)

_FOREIGN_READ_BLOCKED = _ownership_decision(
    decision_id="decision-bm-003",
    protected_action=BeaconProtectedAction.READ_BEACON,
    actor_context=_FOREIGN_OWNER_CONTEXT,
    beacon_id="beacon-bm-002",
    beacon_account_id=_FOREIGN_ACCOUNT_ID,
    outcome=BeaconAuthorizationOutcome.BLOCKED,
    safe_reason_code="FOREIGN_READ_BLOCKED",
    reason="Foreign-account read is blocked without existence-sensitive detail.",
)

_FOREIGN_MUTATE_BLOCKED = _ownership_decision(
    decision_id="decision-bm-004",
    protected_action=BeaconProtectedAction.UPDATE_BEACON,
    actor_context=_FOREIGN_OWNER_CONTEXT,
    beacon_id="beacon-bm-002",
    beacon_account_id=_FOREIGN_ACCOUNT_ID,
    outcome=BeaconAuthorizationOutcome.BLOCKED,
    safe_reason_code="FOREIGN_MUTATE_BLOCKED",
    reason="Foreign-account mutation is blocked without existence-sensitive detail.",
)

_ADMIN_SUPPORT_READ_ALLOWED = _authorization_decision(
    decision_id="decision-bm-005",
    protected_action=BeaconProtectedAction.ADMIN_SUPPORT_READ,
    actor_context=_ADMIN_SUPPORT_CONTEXT,
    beacon_id="beacon-bm-001",
    beacon_account_id=_OWN_ACCOUNT_ID,
    outcome=BeaconAuthorizationOutcome.ALLOWED,
    safe_reason_code="ADMIN_SUPPORT_READ_ALLOWED",
    reason="Admin/support read is allowed only with server-side scope and audit reference.",
    server_role_scope_reference="support-scope-bm-001",
    server_audit_reference="audit-bm-005",
)

_ADMIN_SUPPORT_READ_REQUIRES_VERIFIED = _authorization_decision(
    decision_id="decision-bm-012",
    protected_action=BeaconProtectedAction.ADMIN_SUPPORT_READ,
    actor_context=_ADMIN_SUPPORT_UNVERIFIED_CONTEXT,
    beacon_id="beacon-bm-001",
    beacon_account_id=_OWN_ACCOUNT_ID,
    outcome=BeaconAuthorizationOutcome.REQUIRES_VERIFIED_ACTOR,
    safe_reason_code="ADMIN_SUPPORT_READ_REQUIRES_VERIFIED_ACTOR",
    reason="Admin/support read requires a verified actor.",
)

_ADMIN_SUPPORT_READ_REQUIRES_SCOPE = _authorization_decision(
    decision_id="decision-bm-013",
    protected_action=BeaconProtectedAction.ADMIN_SUPPORT_READ,
    actor_context=_ADMIN_SUPPORT_CONTEXT,
    beacon_id="beacon-bm-001",
    beacon_account_id=_OWN_ACCOUNT_ID,
    outcome=BeaconAuthorizationOutcome.REQUIRES_SCOPE,
    safe_reason_code="ADMIN_SUPPORT_READ_REQUIRES_SCOPE",
    reason="Admin/support read requires server-side scope.",
    server_audit_reference="audit-bm-013",
)

_ADMIN_SUPPORT_MUTATE_REQUIRES_AUDIT = _authorization_decision(
    decision_id="decision-bm-006",
    protected_action=BeaconProtectedAction.ADMIN_SUPPORT_MUTATE,
    actor_context=_ADMIN_SUPPORT_CONTEXT,
    beacon_id="beacon-bm-001",
    beacon_account_id=_OWN_ACCOUNT_ID,
    outcome=BeaconAuthorizationOutcome.REQUIRES_AUDIT,
    safe_reason_code="ADMIN_SUPPORT_MUTATE_REQUIRES_AUDIT",
    reason="Admin/support mutation is blocked until an audit reference is supplied.",
    server_role_scope_reference="support-scope-bm-001",
)

_TELEGRAM_CLIENT_FLAG_DENIED = _ownership_decision(
    decision_id="decision-bm-007",
    protected_action=BeaconProtectedAction.READ_BEACON,
    actor_context=_TELEGRAM_CLIENT_CONTEXT,
    beacon_id="beacon-bm-001",
    beacon_account_id=_OWN_ACCOUNT_ID,
    outcome=BeaconAuthorizationOutcome.DENIED,
    safe_reason_code="TELEGRAM_CLIENT_FLAG_DENIED",
    reason="Telegram client flag alone is not authorization.",
)

_WEB_CLIENT_FLAG_DENIED = _ownership_decision(
    decision_id="decision-bm-008",
    protected_action=BeaconProtectedAction.READ_BEACON,
    actor_context=_WEB_CLIENT_CONTEXT,
    beacon_id="beacon-bm-001",
    beacon_account_id=_OWN_ACCOUNT_ID,
    outcome=BeaconAuthorizationOutcome.DENIED,
    safe_reason_code="WEB_CLIENT_FLAG_DENIED",
    reason="Web client flag alone is not authorization.",
)

_ADMIN_CLIENT_FLAG_DENIED = _ownership_decision(
    decision_id="decision-bm-009",
    protected_action=BeaconProtectedAction.READ_BEACON,
    actor_context=_ADMIN_CLIENT_CONTEXT,
    beacon_id="beacon-bm-001",
    beacon_account_id=_OWN_ACCOUNT_ID,
    outcome=BeaconAuthorizationOutcome.DENIED,
    safe_reason_code="ADMIN_CLIENT_FLAG_DENIED",
    reason="Admin client flag alone is not authorization.",
)

_SYSTEM_FREEZE_ALLOWED = _authorization_decision(
    decision_id="decision-bm-010",
    protected_action=BeaconProtectedAction.SYSTEM_FREEZE_AFTER_EXPIRY,
    actor_context=_SYSTEM_CONTEXT,
    beacon_id="beacon-bm-001",
    beacon_account_id=_OWN_ACCOUNT_ID,
    outcome=BeaconAuthorizationOutcome.ALLOWED,
    safe_reason_code="SYSTEM_FREEZE_ALLOWED",
    reason="System freeze after expiry is allowed only with causation and policy source.",
    action_causation=_causation(
        service_actor_class=BeaconSystemActorClass.MAINTENANCE_SERVICE,
        causation_reference="causation-bm-001",
        policy_source_reference="policy-source-bm-001",
    ),
)

_SYSTEM_FREEZE_BLOCKED = _authorization_decision(
    decision_id="decision-bm-011",
    protected_action=BeaconProtectedAction.SYSTEM_FREEZE_AFTER_EXPIRY,
    actor_context=_SYSTEM_CONTEXT,
    beacon_id="beacon-bm-001",
    beacon_account_id=_OWN_ACCOUNT_ID,
    outcome=BeaconAuthorizationOutcome.BLOCKED,
    safe_reason_code="SYSTEM_FREEZE_BLOCKED",
    reason="System freeze after expiry is blocked until causation and policy source exist.",
)

_BM07_CURRENT_SOURCE_URL = _source_url(
    "current-config-bm07-source-ref-001",
    "https://example.invalid/search?query=current-config-bm07&city=synthetic",
)

_BM07_CURRENT_SNAPSHOT = _snapshot(
    snapshot_id="snapshot-current-config-bm07-001",
    status=BeaconParserOutcomeStatus.CLEAN,
    accepted_as_clean=True,
    evidence_reference="current-config-bm07-snapshot-ref-001",
    parser_evidence_reference=_parser_evidence_reference(
        evidence_reference="current-config-bm07-parser-evidence-001"
    ),
    normalized_filter_values=("city=synthetic-city", "category=synthetic-category"),
)

_BM07_CURRENT_OVERRIDE = _override(
    field_name="district",
    supported=True,
    status=BeaconOverrideStatus.APPLIED,
    requested_values=("north",),
    applied_values=("north",),
    reference="current-config-bm07-override-ref-001",
    reason="synthetic BM07 override",
)

_BM07_CURRENT_CONFIGURATION = _configuration(
    beacon_id="beacon-bm07-current-001",
    account_id=_OWN_ACCOUNT_ID,
    source_url=_BM07_CURRENT_SOURCE_URL,
    snapshot=_BM07_CURRENT_SNAPSHOT,
    display_name="Synthetic BM07 current configuration",
    lifecycle_state=BeaconLifecycleState.ACTIVE,
    current_revision_id="current-config-bm07-effective-ref-001",
    overrides=(_BM07_CURRENT_OVERRIDE,),
    retained_evidence_references=("committed-scan-evidence-bm07-current-accepted-001",),
    previous_user_facing_revision_ids=(),
)

_BM07_CURRENT_CONFIGURATION_DECISION = _current_configuration_decision(
    decision_id="storage-policy-bm07-current-config-accepted-001",
    beacon_id="beacon-bm07-current-001",
    account_id=_OWN_ACCOUNT_ID,
    current_user_facing_active_configurations=(_BM07_CURRENT_CONFIGURATION,),
    current_scan_configuration_reference=_BM07_CURRENT_CONFIGURATION.current_revision_id,
    authority_status=BeaconCurrentConfigurationAuthorityStatus.CURRENT_USER_FACING_ACTIVE,
    storage_policy_outcome=BeaconConfigurationStoragePolicyOutcome.ALLOWED,
    retention_boundary=BeaconConfigurationRetentionBoundary.CURRENT_USER_FACING_WORKING_CONFIGURATION,
)

_BM07_SECOND_CURRENT_CONFIGURATION = _BM07_CURRENT_CONFIGURATION.model_copy(
    update={
        "current_revision_id": "current-config-bm07-effective-ref-002",
        "display_name": "Synthetic BM07 second current configuration",
    }
)

_BM07_MULTIPLE_CURRENT_CONFIGURATIONS_DECISION = BeaconCurrentConfigurationDecision.model_construct(
    decision_id="storage-policy-bm07-multiple-current-configurations-rejected-001",
    beacon_id="beacon-bm07-current-001",
    account_id=_OWN_ACCOUNT_ID,
    authority_status=BeaconCurrentConfigurationAuthorityStatus.CURRENT_USER_FACING_ACTIVE,
    storage_policy_outcome=BeaconConfigurationStoragePolicyOutcome.REJECTED,
    retention_boundary=BeaconConfigurationRetentionBoundary.CURRENT_USER_FACING_WORKING_CONFIGURATION,
    current_user_facing_active_configurations=(
        _BM07_CURRENT_CONFIGURATION,
        _BM07_SECOND_CURRENT_CONFIGURATION,
    ),
    replaced_current_user_facing_configuration=None,
    current_scan_configuration_reference=_BM07_CURRENT_CONFIGURATION.current_revision_id,
    committed_scan_audit_evidence_configuration_reference=None,
    configuration_change_replaces_current_working_configuration=True,
    already_committed_scan_audit_facts_reinterpreted=False,
    physical_delete_or_compaction_claimed=False,
    db_repository_runtime_persistence_claimed=False,
    scanrun_listing_history_state_claimed=False,
    minimal_committed_evidence_editable=False,
    drops_committed_scan_audit_evidence=False,
    provenance_boundary_changed=False,
    rejection_reason=(
        BeaconConfigurationStoragePolicyRejectionReason.MORE_THAN_ONE_CURRENT_USER_FACING_ACTIVE_CONFIGURATION
    ),
)

_BM07_REPLACED_OLD_CONFIGURATION = _configuration(
    beacon_id="beacon-bm07-replaced-001",
    account_id=_OWN_ACCOUNT_ID,
    source_url=_source_url(
        "current-config-bm07-replaced-old-source-ref-001",
        "https://example.invalid/search?query=current-config-bm07-replaced-old&city=synthetic",
    ),
    snapshot=_snapshot(
        snapshot_id="snapshot-current-config-bm07-replaced-old-001",
        status=BeaconParserOutcomeStatus.CLEAN,
        accepted_as_clean=True,
        evidence_reference="current-config-bm07-replaced-old-snapshot-ref-001",
        parser_evidence_reference=_parser_evidence_reference(
            evidence_reference="current-config-bm07-replaced-old-parser-evidence-001"
        ),
        normalized_filter_values=("city=synthetic-city",),
    ),
    display_name="Synthetic BM07 replaced configuration old",
    lifecycle_state=BeaconLifecycleState.READY,
    current_revision_id="current-config-bm07-replaced-old-ref-001",
    retained_evidence_references=("committed-scan-evidence-bm07-replaced-old-001",),
    previous_user_facing_revision_ids=(),
)

_BM07_REPLACED_NEW_CONFIGURATION = _configuration(
    beacon_id="beacon-bm07-replaced-001",
    account_id=_OWN_ACCOUNT_ID,
    source_url=_source_url(
        "current-config-bm07-replaced-new-source-ref-001",
        "https://example.invalid/search?query=current-config-bm07-replaced-new&city=synthetic",
    ),
    snapshot=_snapshot(
        snapshot_id="snapshot-current-config-bm07-replaced-new-001",
        status=BeaconParserOutcomeStatus.CLEAN,
        accepted_as_clean=True,
        evidence_reference="current-config-bm07-replaced-new-snapshot-ref-001",
        parser_evidence_reference=_parser_evidence_reference(
            evidence_reference="current-config-bm07-replaced-new-parser-evidence-001"
        ),
        normalized_filter_values=("city=synthetic-city", "district=north"),
    ),
    display_name="Synthetic BM07 replaced configuration new",
    lifecycle_state=BeaconLifecycleState.ACTIVE,
    current_revision_id="current-config-bm07-replaced-new-ref-001",
    overrides=(
        _override(
            field_name="district",
            supported=True,
            status=BeaconOverrideStatus.APPLIED,
            requested_values=("north",),
            applied_values=("north",),
            reference="current-config-bm07-replaced-override-ref-001",
            reason="synthetic BM07 replacement override",
        ),
    ),
    retained_evidence_references=("committed-scan-evidence-bm07-replaced-new-001",),
    previous_user_facing_revision_ids=("current-config-bm07-replaced-old-ref-001",),
)

_BM07_REPLACEMENT_DECISION = _current_configuration_decision(
    decision_id="storage-policy-bm07-current-config-replaced-001",
    beacon_id="beacon-bm07-replaced-001",
    account_id=_OWN_ACCOUNT_ID,
    current_user_facing_active_configurations=(_BM07_REPLACED_NEW_CONFIGURATION,),
    replaced_current_user_facing_configuration=_BM07_REPLACED_OLD_CONFIGURATION,
    current_scan_configuration_reference=_BM07_REPLACED_NEW_CONFIGURATION.current_revision_id,
    authority_status=BeaconCurrentConfigurationAuthorityStatus.CURRENT_USER_FACING_ACTIVE,
    storage_policy_outcome=BeaconConfigurationStoragePolicyOutcome.ALLOWED,
    retention_boundary=BeaconConfigurationRetentionBoundary.CURRENT_USER_FACING_WORKING_CONFIGURATION,
)

_BM07_COMMITTED_EVIDENCE_DECISION = _configuration_evidence_retention_decision(
    decision_id="storage-policy-bm07-committed-evidence-retained-001",
    beacon_id="beacon-bm07-committed-001",
    account_id=_OWN_ACCOUNT_ID,
    committed_scan_audit_evidence_reference="committed-scan-evidence-bm07-retained-001",
    original_current_configuration_reference="current-config-bm07-original-ref-001",
    current_configuration_reference="current-config-bm07-current-ref-001",
    minimal_immutable_scan_audit_evidence_reference="retention-boundary-bm07-minimal-001",
    authority_status=BeaconCurrentConfigurationAuthorityStatus.MINIMAL_IMMUTABLE_SCAN_AUDIT_EVIDENCE,
    storage_policy_outcome=BeaconConfigurationStoragePolicyOutcome.ALLOWED,
    retention_boundary=BeaconConfigurationRetentionBoundary.MINIMAL_IMMUTABLE_SCAN_AUDIT_EVIDENCE,
)

_BM07_NO_REINTERPRETATION_DECISION = BeaconConfigurationEvidenceRetentionDecision.model_construct(
    decision_id="storage-policy-bm07-no-reinterpretation-001",
    beacon_id="beacon-bm07-committed-001",
    account_id=_OWN_ACCOUNT_ID,
    authority_status=BeaconCurrentConfigurationAuthorityStatus.MINIMAL_IMMUTABLE_SCAN_AUDIT_EVIDENCE,
    storage_policy_outcome=BeaconConfigurationStoragePolicyOutcome.BLOCKED,
    retention_boundary=BeaconConfigurationRetentionBoundary.MINIMAL_IMMUTABLE_SCAN_AUDIT_EVIDENCE,
    committed_scan_audit_evidence_reference="committed-scan-evidence-bm07-no-reinterpretation-001",
    original_current_configuration_reference="current-config-bm07-original-no-reinterpretation-001",
    current_configuration_reference="current-config-bm07-current-no-reinterpretation-001",
    minimal_immutable_scan_audit_evidence_reference="retention-boundary-bm07-no-reinterpretation-001",
    minimal_committed_evidence_editable=False,
    already_committed_scan_audit_facts_reinterpreted=True,
    physical_delete_or_compaction_claimed=False,
    db_repository_runtime_persistence_claimed=False,
    scanrun_listing_history_state_claimed=False,
    drops_committed_scan_audit_evidence=False,
    provenance_boundary_changed=False,
    rejection_reason=BeaconConfigurationStoragePolicyRejectionReason.REINTERPRETING_COMMITTED_SCAN_AUDIT_FACTS,
)

_BM07_UNBOUNDED_REVISIONS_CONFIGURATION = BeaconCurrentConfiguration.model_construct(
    beacon_id="beacon-bm07-unbounded-revisions-001",
    account_id=_OWN_ACCOUNT_ID,
    source_url=_source_url(
        "current-config-bm07-unbounded-source-ref-001",
        "https://example.invalid/search?query=current-config-bm07-unbounded&city=synthetic",
    ),
    accepted_snapshot=_snapshot(
        snapshot_id="snapshot-current-config-bm07-unbounded-001",
        status=BeaconParserOutcomeStatus.CLEAN,
        accepted_as_clean=True,
        evidence_reference="current-config-bm07-unbounded-snapshot-ref-001",
        parser_evidence_reference=_parser_evidence_reference(
            evidence_reference="current-config-bm07-unbounded-parser-evidence-001"
        ),
        normalized_filter_values=("city=synthetic-city",),
    ),
    overrides=(),
    current_revision_id="current-config-bm07-unbounded-ref-001",
    display_name="Synthetic BM07 unbounded revision clutter",
    lifecycle_state=BeaconLifecycleState.ACTIVE,
    retained_evidence_references=("committed-scan-evidence-bm07-unbounded-001",),
    previous_user_facing_revision_ids=(
        "current-config-bm07-unbounded-previous-001",
        "current-config-bm07-unbounded-previous-002",
    ),
)

_BM07_UNBOUNDED_REVISIONS_DECISION = BeaconCurrentConfigurationDecision.model_construct(
    decision_id="storage-policy-bm07-unbounded-revisions-rejected-001",
    beacon_id="beacon-bm07-unbounded-revisions-001",
    account_id=_OWN_ACCOUNT_ID,
    authority_status=BeaconCurrentConfigurationAuthorityStatus.CURRENT_USER_FACING_ACTIVE,
    storage_policy_outcome=BeaconConfigurationStoragePolicyOutcome.REJECTED,
    retention_boundary=BeaconConfigurationRetentionBoundary.CURRENT_USER_FACING_WORKING_CONFIGURATION,
    current_user_facing_active_configurations=(_BM07_UNBOUNDED_REVISIONS_CONFIGURATION,),
    replaced_current_user_facing_configuration=None,
    current_scan_configuration_reference=_BM07_UNBOUNDED_REVISIONS_CONFIGURATION.current_revision_id,
    committed_scan_audit_evidence_configuration_reference=None,
    configuration_change_replaces_current_working_configuration=True,
    already_committed_scan_audit_facts_reinterpreted=False,
    physical_delete_or_compaction_claimed=False,
    db_repository_runtime_persistence_claimed=False,
    scanrun_listing_history_state_claimed=False,
    minimal_committed_evidence_editable=False,
    drops_committed_scan_audit_evidence=False,
    provenance_boundary_changed=False,
    rejection_reason=BeaconConfigurationStoragePolicyRejectionReason.UNBOUNDED_USER_FACING_REVISION_CLOUTTER,
)

_BM07_PHYSICAL_COMPACTION_DELETE_DECISION = (
    BeaconConfigurationEvidenceRetentionDecision.model_construct
)(
    decision_id="storage-policy-bm07-physical-compaction-delete-rejected-001",
    beacon_id="beacon-bm07-committed-001",
    account_id=_OWN_ACCOUNT_ID,
    authority_status=BeaconCurrentConfigurationAuthorityStatus.MINIMAL_IMMUTABLE_SCAN_AUDIT_EVIDENCE,
    storage_policy_outcome=BeaconConfigurationStoragePolicyOutcome.BLOCKED,
    retention_boundary=BeaconConfigurationRetentionBoundary.MINIMAL_IMMUTABLE_SCAN_AUDIT_EVIDENCE,
    committed_scan_audit_evidence_reference="committed-scan-evidence-bm07-physical-delete-001",
    original_current_configuration_reference="current-config-bm07-physical-delete-original-001",
    current_configuration_reference="current-config-bm07-physical-delete-current-001",
    minimal_immutable_scan_audit_evidence_reference="retention-boundary-bm07-physical-delete-001",
    minimal_committed_evidence_editable=False,
    already_committed_scan_audit_facts_reinterpreted=False,
    physical_delete_or_compaction_claimed=True,
    db_repository_runtime_persistence_claimed=False,
    scanrun_listing_history_state_claimed=False,
    drops_committed_scan_audit_evidence=False,
    provenance_boundary_changed=False,
    rejection_reason=BeaconConfigurationStoragePolicyRejectionReason.PHYSICAL_DELETE_OR_COMPACTION_CLAIM,
)

_BM07_RUNTIME_PERSISTENCE_DECISION = BeaconConfigurationEvidenceRetentionDecision.model_construct(
    decision_id="storage-policy-bm07-runtime-persistence-claim-rejected-001",
    beacon_id="beacon-bm07-committed-001",
    account_id=_OWN_ACCOUNT_ID,
    authority_status=BeaconCurrentConfigurationAuthorityStatus.MINIMAL_IMMUTABLE_SCAN_AUDIT_EVIDENCE,
    storage_policy_outcome=BeaconConfigurationStoragePolicyOutcome.BLOCKED,
    retention_boundary=BeaconConfigurationRetentionBoundary.MINIMAL_IMMUTABLE_SCAN_AUDIT_EVIDENCE,
    committed_scan_audit_evidence_reference="committed-scan-evidence-bm07-runtime-persistence-001",
    original_current_configuration_reference="current-config-bm07-runtime-persistence-original-001",
    current_configuration_reference="current-config-bm07-runtime-persistence-current-001",
    minimal_immutable_scan_audit_evidence_reference="retention-boundary-bm07-runtime-persistence-001",
    minimal_committed_evidence_editable=False,
    already_committed_scan_audit_facts_reinterpreted=False,
    physical_delete_or_compaction_claimed=False,
    db_repository_runtime_persistence_claimed=True,
    scanrun_listing_history_state_claimed=False,
    drops_committed_scan_audit_evidence=False,
    provenance_boundary_changed=False,
    rejection_reason=BeaconConfigurationStoragePolicyRejectionReason.DB_REPOSITORY_RUNTIME_PERSISTENCE_CLAIM,
)

_BM07_SCANRUN_HISTORY_CLAIM_DECISION = BeaconConfigurationEvidenceRetentionDecision.model_construct(
    decision_id="storage-policy-bm07-scanrun-history-claim-rejected-001",
    beacon_id="beacon-bm07-committed-001",
    account_id=_OWN_ACCOUNT_ID,
    authority_status=BeaconCurrentConfigurationAuthorityStatus.MINIMAL_IMMUTABLE_SCAN_AUDIT_EVIDENCE,
    storage_policy_outcome=BeaconConfigurationStoragePolicyOutcome.BLOCKED,
    retention_boundary=BeaconConfigurationRetentionBoundary.MINIMAL_IMMUTABLE_SCAN_AUDIT_EVIDENCE,
    committed_scan_audit_evidence_reference="committed-scan-evidence-bm07-scanrun-history-001",
    original_current_configuration_reference="current-config-bm07-scanrun-history-original-001",
    current_configuration_reference="current-config-bm07-scanrun-history-current-001",
    minimal_immutable_scan_audit_evidence_reference="retention-boundary-bm07-scanrun-history-001",
    minimal_committed_evidence_editable=False,
    already_committed_scan_audit_facts_reinterpreted=False,
    physical_delete_or_compaction_claimed=False,
    db_repository_runtime_persistence_claimed=False,
    scanrun_listing_history_state_claimed=True,
    drops_committed_scan_audit_evidence=False,
    provenance_boundary_changed=False,
    rejection_reason=BeaconConfigurationStoragePolicyRejectionReason.SCANRUN_LISTING_HISTORY_STATE_CLAIM,
)

_BM07_MINIMAL_COMMITTED_EVIDENCE_EDITABLE_DECISION = (
    BeaconConfigurationEvidenceRetentionDecision.model_construct
)(
    decision_id="storage-policy-bm07-minimal-committed-evidence-editable-rejected-001",
    beacon_id="beacon-bm07-committed-001",
    account_id=_OWN_ACCOUNT_ID,
    authority_status=BeaconCurrentConfigurationAuthorityStatus.MINIMAL_IMMUTABLE_SCAN_AUDIT_EVIDENCE,
    storage_policy_outcome=BeaconConfigurationStoragePolicyOutcome.BLOCKED,
    retention_boundary=BeaconConfigurationRetentionBoundary.MINIMAL_IMMUTABLE_SCAN_AUDIT_EVIDENCE,
    committed_scan_audit_evidence_reference="committed-scan-evidence-bm07-minimal-editable-001",
    original_current_configuration_reference="current-config-bm07-minimal-editable-original-001",
    current_configuration_reference="current-config-bm07-minimal-editable-current-001",
    minimal_immutable_scan_audit_evidence_reference="retention-boundary-bm07-minimal-editable-001",
    minimal_committed_evidence_editable=True,
    already_committed_scan_audit_facts_reinterpreted=False,
    physical_delete_or_compaction_claimed=False,
    db_repository_runtime_persistence_claimed=False,
    scanrun_listing_history_state_claimed=False,
    drops_committed_scan_audit_evidence=False,
    provenance_boundary_changed=False,
    rejection_reason=BeaconConfigurationStoragePolicyRejectionReason.MINIMAL_COMMITTED_EVIDENCE_EDITABLE,
)

_BM08_BASIC_BAND = _tariff_policy_band(
    access_tier=BeaconAccessTier.BASIC,
    active_beacon_limit=5,
    minimum_interval_minutes=5,
    interval_step_minutes=5,
    country_wide_allowed=True,
    country_wide_city_required=False,
)

_BM08_FREE_BAND = _tariff_policy_band(
    access_tier=BeaconAccessTier.FREE,
    active_beacon_limit=1,
    minimum_interval_minutes=180,
    interval_step_minutes=180,
    country_wide_allowed=False,
    country_wide_city_required=True,
)

_BM08_BASIC_EVIDENCE = _entitlement_evidence_reference(
    evidence_reference="entitlement-evidence-bm08-basic-001",
    source_reference="entitlement-source-bm08-basic-001",
    freshness_reference="freshness-bm08-basic-001",
)

_BM08_FREE_EVIDENCE = _entitlement_evidence_reference(
    evidence_reference="entitlement-evidence-bm08-free-001",
    source_reference="entitlement-source-bm08-free-001",
    freshness_reference="freshness-bm08-free-001",
)

_BM08_AMBIGUOUS_EVIDENCE = _entitlement_evidence_reference(
    evidence_reference="entitlement-evidence-bm08-ambiguous-001",
    source_reference="entitlement-source-bm08-ambiguous-001",
    freshness_reference="freshness-bm08-ambiguous-001",
)

_BM08_DENIED_EVIDENCE = _entitlement_evidence_reference(
    evidence_reference="entitlement-evidence-bm08-denied-001",
    source_reference="entitlement-source-bm08-denied-001",
    freshness_reference="freshness-bm08-denied-001",
)

_BM08_EXPIRED_EVIDENCE = _entitlement_evidence_reference(
    evidence_reference="entitlement-evidence-bm08-expired-001",
    source_reference="entitlement-source-bm08-expired-001",
    freshness_reference="freshness-bm08-expired-001",
)

_BM08_RECHECK_EVIDENCE = _entitlement_evidence_reference(
    evidence_reference="entitlement-evidence-bm08-recheck-001",
    source_reference="entitlement-source-bm08-recheck-001",
    freshness_reference="freshness-bm08-recheck-001",
)

_BM08_STALE_EVIDENCE = _entitlement_evidence_reference(
    evidence_reference="entitlement-evidence-bm08-stale-001",
    source_reference="entitlement-source-bm08-stale-001",
    freshness_status=BeaconEntitlementEvidenceFreshnessStatus.STALE,
    freshness_reference="freshness-bm08-stale-001",
)

_BM08_NOTIFICATION_EVIDENCE = _entitlement_evidence_reference(
    evidence_reference="entitlement-evidence-bm08-notification-001",
    source_reference="entitlement-source-bm08-notification-001",
    freshness_reference="freshness-bm08-notification-001",
)

_BM08_PROVENANCE_EVIDENCE = _entitlement_evidence_reference(
    evidence_reference="entitlement-evidence-bm08-provenance-001",
    source_reference="entitlement-source-bm08-provenance-001",
    freshness_reference="freshness-bm08-provenance-001",
)

_BM08_BASIC_ALLOWED_SNAPSHOT = _effective_entitlement_snapshot(
    snapshot_reference="effective-entitlement-snapshot-bm08-basic-allowed-001",
    beacon_source_reference="beacon-source-bm08-basic-allowed-001",
    entitlement_source_reference=_BM08_BASIC_EVIDENCE.source_reference,
    entitlement_evidence_reference=_BM08_BASIC_EVIDENCE,
    tariff_policy_band=_BM08_BASIC_BAND,
    effective_outcome=BeaconLifecycleEntitlementOutcome.ALLOWED,
    active_beacon_count=4,
    requested_interval_minutes=5,
    requested_country_wide=True,
    provenance_reference="provenance-bm08-basic-allowed-001",
)

_BM08_BASIC_LIMIT_BLOCKED_SNAPSHOT = _effective_entitlement_snapshot(
    snapshot_reference="effective-entitlement-snapshot-bm08-basic-limit-blocked-001",
    beacon_source_reference="beacon-source-bm08-basic-limit-blocked-001",
    entitlement_source_reference=_BM08_BASIC_EVIDENCE.source_reference,
    entitlement_evidence_reference=_BM08_BASIC_EVIDENCE,
    tariff_policy_band=_BM08_BASIC_BAND,
    effective_outcome=BeaconLifecycleEntitlementOutcome.BLOCKED,
    active_beacon_count=5,
    requested_interval_minutes=5,
    requested_country_wide=True,
    provenance_reference="provenance-bm08-basic-limit-blocked-001",
)

_BM08_BASIC_INTERVAL_BELOW_FLOOR_SNAPSHOT = _effective_entitlement_snapshot(
    snapshot_reference="effective-entitlement-snapshot-bm08-basic-floor-blocked-001",
    beacon_source_reference="beacon-source-bm08-basic-floor-blocked-001",
    entitlement_source_reference=_BM08_BASIC_EVIDENCE.source_reference,
    entitlement_evidence_reference=_BM08_BASIC_EVIDENCE,
    tariff_policy_band=_BM08_BASIC_BAND,
    effective_outcome=BeaconLifecycleEntitlementOutcome.BLOCKED,
    active_beacon_count=0,
    requested_interval_minutes=4,
    requested_country_wide=False,
    provenance_reference="provenance-bm08-basic-floor-blocked-001",
)

_BM08_BASIC_INTERVAL_STEP_BLOCKED_SNAPSHOT = _effective_entitlement_snapshot(
    snapshot_reference="effective-entitlement-snapshot-bm08-basic-step-blocked-001",
    beacon_source_reference="beacon-source-bm08-basic-step-blocked-001",
    entitlement_source_reference=_BM08_BASIC_EVIDENCE.source_reference,
    entitlement_evidence_reference=_BM08_BASIC_EVIDENCE,
    tariff_policy_band=_BM08_BASIC_BAND,
    effective_outcome=BeaconLifecycleEntitlementOutcome.BLOCKED,
    active_beacon_count=0,
    requested_interval_minutes=6,
    requested_country_wide=False,
    provenance_reference="provenance-bm08-basic-step-blocked-001",
)

_BM08_FREE_ALLOWED_SNAPSHOT = _effective_entitlement_snapshot(
    snapshot_reference="effective-entitlement-snapshot-bm08-free-allowed-001",
    beacon_source_reference="beacon-source-bm08-free-allowed-001",
    entitlement_source_reference=_BM08_FREE_EVIDENCE.source_reference,
    entitlement_evidence_reference=_BM08_FREE_EVIDENCE,
    tariff_policy_band=_BM08_FREE_BAND,
    effective_outcome=BeaconLifecycleEntitlementOutcome.ALLOWED,
    active_beacon_count=0,
    requested_interval_minutes=180,
    requested_country_wide=False,
    selected_city="synthetic-city",
    provenance_reference="provenance-bm08-free-allowed-001",
)

_BM08_FREE_COUNTRY_WIDE_BLOCKED_SNAPSHOT = _effective_entitlement_snapshot(
    snapshot_reference="effective-entitlement-snapshot-bm08-free-country-wide-blocked-001",
    beacon_source_reference="beacon-source-bm08-free-country-wide-blocked-001",
    entitlement_source_reference=_BM08_FREE_EVIDENCE.source_reference,
    entitlement_evidence_reference=_BM08_FREE_EVIDENCE,
    tariff_policy_band=_BM08_FREE_BAND,
    effective_outcome=BeaconLifecycleEntitlementOutcome.BLOCKED,
    active_beacon_count=0,
    requested_interval_minutes=180,
    requested_country_wide=True,
    provenance_reference="provenance-bm08-free-country-wide-blocked-001",
)

_BM08_FREE_INTERVAL_BELOW_FLOOR_SNAPSHOT = _effective_entitlement_snapshot(
    snapshot_reference="effective-entitlement-snapshot-bm08-free-floor-blocked-001",
    beacon_source_reference="beacon-source-bm08-free-floor-blocked-001",
    entitlement_source_reference=_BM08_FREE_EVIDENCE.source_reference,
    entitlement_evidence_reference=_BM08_FREE_EVIDENCE,
    tariff_policy_band=_BM08_FREE_BAND,
    effective_outcome=BeaconLifecycleEntitlementOutcome.BLOCKED,
    active_beacon_count=0,
    requested_interval_minutes=179,
    requested_country_wide=False,
    selected_city="synthetic-city",
    provenance_reference="provenance-bm08-free-floor-blocked-001",
)

_BM08_FREE_INTERVAL_STEP_BLOCKED_SNAPSHOT = _effective_entitlement_snapshot(
    snapshot_reference="effective-entitlement-snapshot-bm08-free-step-blocked-001",
    beacon_source_reference="beacon-source-bm08-free-step-blocked-001",
    entitlement_source_reference=_BM08_FREE_EVIDENCE.source_reference,
    entitlement_evidence_reference=_BM08_FREE_EVIDENCE,
    tariff_policy_band=_BM08_FREE_BAND,
    effective_outcome=BeaconLifecycleEntitlementOutcome.BLOCKED,
    active_beacon_count=0,
    requested_interval_minutes=181,
    requested_country_wide=False,
    selected_city="synthetic-city",
    provenance_reference="provenance-bm08-free-step-blocked-001",
)

_BM08_FREE_ACTIVE_LIMIT_BLOCKED_SNAPSHOT = _effective_entitlement_snapshot(
    snapshot_reference="effective-entitlement-snapshot-bm08-free-limit-blocked-001",
    beacon_source_reference="beacon-source-bm08-free-limit-blocked-001",
    entitlement_source_reference=_BM08_FREE_EVIDENCE.source_reference,
    entitlement_evidence_reference=_BM08_FREE_EVIDENCE,
    tariff_policy_band=_BM08_FREE_BAND,
    effective_outcome=BeaconLifecycleEntitlementOutcome.BLOCKED,
    active_beacon_count=1,
    requested_interval_minutes=180,
    requested_country_wide=False,
    selected_city="synthetic-city",
    provenance_reference="provenance-bm08-free-limit-blocked-001",
)

_BM08_EXCLUDED_COUNTS_SNAPSHOT = _effective_entitlement_snapshot(
    snapshot_reference="effective-entitlement-snapshot-bm08-excluded-counts-001",
    beacon_source_reference="beacon-source-bm08-excluded-counts-001",
    entitlement_source_reference=_BM08_BASIC_EVIDENCE.source_reference,
    entitlement_evidence_reference=_BM08_BASIC_EVIDENCE,
    tariff_policy_band=_BM08_BASIC_BAND,
    effective_outcome=BeaconLifecycleEntitlementOutcome.ALLOWED,
    active_beacon_count=0,
    archived_beacon_count=1,
    history_beacon_count=1,
    deleted_beacon_count=1,
    requested_interval_minutes=5,
    requested_country_wide=False,
    provenance_reference="provenance-bm08-excluded-counts-001",
)

_BM08_AMBIGUOUS_SNAPSHOT = _effective_entitlement_snapshot(
    snapshot_reference="effective-entitlement-snapshot-bm08-ambiguous-001",
    beacon_source_reference="beacon-source-bm08-ambiguous-001",
    entitlement_source_reference=_BM08_AMBIGUOUS_EVIDENCE.source_reference,
    entitlement_evidence_reference=_BM08_AMBIGUOUS_EVIDENCE,
    tariff_policy_band=_BM08_BASIC_BAND,
    effective_outcome=BeaconLifecycleEntitlementOutcome.AMBIGUOUS,
    active_beacon_count=0,
    requested_interval_minutes=5,
    requested_country_wide=False,
    provenance_reference="provenance-bm08-ambiguous-001",
)

_BM08_DENIED_SNAPSHOT = _effective_entitlement_snapshot(
    snapshot_reference="effective-entitlement-snapshot-bm08-denied-001",
    beacon_source_reference="beacon-source-bm08-denied-001",
    entitlement_source_reference=_BM08_DENIED_EVIDENCE.source_reference,
    entitlement_evidence_reference=_BM08_DENIED_EVIDENCE,
    tariff_policy_band=_BM08_BASIC_BAND,
    effective_outcome=BeaconLifecycleEntitlementOutcome.DENIED,
    active_beacon_count=0,
    requested_interval_minutes=5,
    requested_country_wide=False,
    provenance_reference="provenance-bm08-denied-001",
)

_BM08_RECHECK_REQUIRED_SNAPSHOT = _effective_entitlement_snapshot(
    snapshot_reference="effective-entitlement-snapshot-bm08-recheck-001",
    beacon_source_reference="beacon-source-bm08-recheck-001",
    entitlement_source_reference=_BM08_RECHECK_EVIDENCE.source_reference,
    entitlement_evidence_reference=_BM08_RECHECK_EVIDENCE,
    tariff_policy_band=_BM08_BASIC_BAND,
    effective_outcome=BeaconLifecycleEntitlementOutcome.RECHECK_REQUIRED,
    active_beacon_count=0,
    requested_interval_minutes=5,
    requested_country_wide=False,
    provenance_reference="provenance-bm08-recheck-001",
)

_BM08_STALE_RECHECK_SNAPSHOT = _effective_entitlement_snapshot(
    snapshot_reference="effective-entitlement-snapshot-bm08-stale-recheck-001",
    beacon_source_reference="beacon-source-bm08-stale-recheck-001",
    entitlement_source_reference=_BM08_STALE_EVIDENCE.source_reference,
    entitlement_evidence_reference=_BM08_STALE_EVIDENCE,
    tariff_policy_band=_BM08_BASIC_BAND,
    effective_outcome=BeaconLifecycleEntitlementOutcome.RECHECK_REQUIRED,
    active_beacon_count=0,
    requested_interval_minutes=5,
    requested_country_wide=False,
    provenance_reference="provenance-bm08-stale-recheck-001",
)

_BM08_FROZEN_SNAPSHOT = _effective_entitlement_snapshot(
    snapshot_reference="effective-entitlement-snapshot-bm08-frozen-001",
    beacon_source_reference="beacon-source-bm08-frozen-001",
    entitlement_source_reference=_BM08_EXPIRED_EVIDENCE.source_reference,
    entitlement_evidence_reference=_BM08_EXPIRED_EVIDENCE,
    tariff_policy_band=_BM08_BASIC_BAND,
    effective_outcome=BeaconLifecycleEntitlementOutcome.FROZEN,
    active_beacon_count=0,
    requested_interval_minutes=5,
    requested_country_wide=False,
    expired_paid_active_beacon_count=1,
    future_notification_reference="future-notification-reference-bm08-frozen-001",
    provenance_reference="provenance-bm08-frozen-001",
)

_BM08_USER_CHOICE_REQUIRED_SNAPSHOT = _effective_entitlement_snapshot(
    snapshot_reference="effective-entitlement-snapshot-bm08-user-choice-001",
    beacon_source_reference="beacon-source-bm08-user-choice-001",
    entitlement_source_reference=_BM08_EXPIRED_EVIDENCE.source_reference,
    entitlement_evidence_reference=_BM08_EXPIRED_EVIDENCE,
    tariff_policy_band=_BM08_BASIC_BAND,
    effective_outcome=BeaconLifecycleEntitlementOutcome.USER_CHOICE_REQUIRED,
    active_beacon_count=0,
    requested_interval_minutes=5,
    requested_country_wide=False,
    expired_paid_active_beacon_count=1,
    future_notification_reference="future-notification-reference-bm08-user-choice-001",
    provenance_reference="provenance-bm08-user-choice-001",
)

_BM08_FREE_COMPLIANCE_REQUIRED_SNAPSHOT = _effective_entitlement_snapshot(
    snapshot_reference="effective-entitlement-snapshot-bm08-free-compliance-001",
    beacon_source_reference="beacon-source-bm08-free-compliance-001",
    entitlement_source_reference=_BM08_EXPIRED_EVIDENCE.source_reference,
    entitlement_evidence_reference=_BM08_EXPIRED_EVIDENCE,
    tariff_policy_band=_BM08_FREE_BAND,
    effective_outcome=BeaconLifecycleEntitlementOutcome.FREE_COMPLIANCE_REQUIRED,
    active_beacon_count=0,
    requested_interval_minutes=180,
    requested_country_wide=False,
    selected_free_beacon_id="beacon-bm08-free-selected-001",
    selected_free_beacon_user_choice_reference="choice-bm08-free-selected-001",
    future_notification_reference="future-notification-reference-bm08-free-compliance-001",
    expired_paid_active_beacon_count=1,
    provenance_reference="provenance-bm08-free-compliance-001",
)

_BM08_NOTIFICATION_ONLY_SNAPSHOT = _effective_entitlement_snapshot(
    snapshot_reference="effective-entitlement-snapshot-bm08-notification-001",
    beacon_source_reference="beacon-source-bm08-notification-001",
    entitlement_source_reference=_BM08_NOTIFICATION_EVIDENCE.source_reference,
    entitlement_evidence_reference=_BM08_NOTIFICATION_EVIDENCE,
    tariff_policy_band=_BM08_BASIC_BAND,
    effective_outcome=BeaconLifecycleEntitlementOutcome.USER_CHOICE_REQUIRED,
    active_beacon_count=0,
    requested_interval_minutes=5,
    requested_country_wide=False,
    expired_paid_active_beacon_count=1,
    future_notification_reference="future-notification-reference-bm08-notification-001",
    provenance_reference="provenance-bm08-notification-001",
)

_BM08_PROVENANCE_DISTINCT_SNAPSHOT = _effective_entitlement_snapshot(
    snapshot_reference="effective-entitlement-snapshot-bm08-provenance-001",
    beacon_source_reference="beacon-source-bm08-provenance-001",
    entitlement_source_reference=_BM08_PROVENANCE_EVIDENCE.source_reference,
    entitlement_evidence_reference=_BM08_PROVENANCE_EVIDENCE,
    tariff_policy_band=_BM08_BASIC_BAND,
    effective_outcome=BeaconLifecycleEntitlementOutcome.ALLOWED,
    active_beacon_count=2,
    requested_interval_minutes=5,
    requested_country_wide=False,
    provenance_reference="provenance-bm08-provenance-001",
)

_BM08_BASIC_ALLOWED_DECISION = _lifecycle_entitlement_decision(
    decision_id="decision-bm08-basic-allowed-001",
    beacon_id="beacon-bm08-basic-allowed-001",
    account_id=_OWN_ACCOUNT_ID,
    action_kind=BeaconLifecycleActionKind.ACTIVATE,
    outcome=BeaconLifecycleEntitlementOutcome.ALLOWED,
    beacon_source_reference=_BM08_BASIC_ALLOWED_SNAPSHOT.beacon_source_reference,
    entitlement_evidence_reference=_BM08_BASIC_EVIDENCE,
    effective_entitlement_snapshot=_BM08_BASIC_ALLOWED_SNAPSHOT,
    requested_interval_minutes=5,
    active_beacon_count=4,
    requested_country_wide=True,
)

_BM08_BASIC_LIMIT_BLOCKED_DECISION = _lifecycle_entitlement_decision(
    decision_id="decision-bm08-basic-limit-blocked-001",
    beacon_id="beacon-bm08-basic-limit-blocked-001",
    account_id=_OWN_ACCOUNT_ID,
    action_kind=BeaconLifecycleActionKind.ACTIVATE,
    outcome=BeaconLifecycleEntitlementOutcome.BLOCKED,
    beacon_source_reference=_BM08_BASIC_LIMIT_BLOCKED_SNAPSHOT.beacon_source_reference,
    entitlement_evidence_reference=_BM08_BASIC_EVIDENCE,
    effective_entitlement_snapshot=_BM08_BASIC_LIMIT_BLOCKED_SNAPSHOT,
    requested_interval_minutes=5,
    active_beacon_count=5,
    requested_country_wide=True,
    rejection_reason=BeaconLifecycleEntitlementRejectionReason.ACTIVE_LIMIT_EXCEEDED,
)

_BM08_BASIC_INTERVAL_BELOW_FLOOR_DECISION = _lifecycle_entitlement_decision(
    decision_id="decision-bm08-basic-floor-blocked-001",
    beacon_id="beacon-bm08-basic-floor-blocked-001",
    account_id=_OWN_ACCOUNT_ID,
    action_kind=BeaconLifecycleActionKind.ACTIVATE,
    outcome=BeaconLifecycleEntitlementOutcome.BLOCKED,
    beacon_source_reference=_BM08_BASIC_INTERVAL_BELOW_FLOOR_SNAPSHOT.beacon_source_reference,
    entitlement_evidence_reference=_BM08_BASIC_EVIDENCE,
    effective_entitlement_snapshot=_BM08_BASIC_INTERVAL_BELOW_FLOOR_SNAPSHOT,
    requested_interval_minutes=4,
    active_beacon_count=0,
    requested_country_wide=False,
    rejection_reason=BeaconLifecycleEntitlementRejectionReason.BASIC_INTERVAL_BELOW_FLOOR,
)

_BM08_BASIC_INTERVAL_STEP_BLOCKED_DECISION = _lifecycle_entitlement_decision(
    decision_id="decision-bm08-basic-step-blocked-001",
    beacon_id="beacon-bm08-basic-step-blocked-001",
    account_id=_OWN_ACCOUNT_ID,
    action_kind=BeaconLifecycleActionKind.ACTIVATE,
    outcome=BeaconLifecycleEntitlementOutcome.BLOCKED,
    beacon_source_reference=_BM08_BASIC_INTERVAL_STEP_BLOCKED_SNAPSHOT.beacon_source_reference,
    entitlement_evidence_reference=_BM08_BASIC_EVIDENCE,
    effective_entitlement_snapshot=_BM08_BASIC_INTERVAL_STEP_BLOCKED_SNAPSHOT,
    requested_interval_minutes=6,
    active_beacon_count=0,
    requested_country_wide=False,
    rejection_reason=BeaconLifecycleEntitlementRejectionReason.BASIC_INTERVAL_NOT_STEP,
)

_BM08_FREE_ALLOWED_DECISION = _lifecycle_entitlement_decision(
    decision_id="decision-bm08-free-allowed-001",
    beacon_id="beacon-bm08-free-allowed-001",
    account_id=_OWN_ACCOUNT_ID,
    action_kind=BeaconLifecycleActionKind.ACTIVATE,
    outcome=BeaconLifecycleEntitlementOutcome.ALLOWED,
    beacon_source_reference=_BM08_FREE_ALLOWED_SNAPSHOT.beacon_source_reference,
    entitlement_evidence_reference=_BM08_FREE_EVIDENCE,
    effective_entitlement_snapshot=_BM08_FREE_ALLOWED_SNAPSHOT,
    requested_interval_minutes=180,
    active_beacon_count=0,
    requested_country_wide=False,
    selected_city="synthetic-city",
)

_BM08_FREE_COUNTRY_WIDE_BLOCKED_DECISION = _lifecycle_entitlement_decision(
    decision_id="decision-bm08-free-country-wide-blocked-001",
    beacon_id="beacon-bm08-free-country-wide-blocked-001",
    account_id=_OWN_ACCOUNT_ID,
    action_kind=BeaconLifecycleActionKind.ACTIVATE,
    outcome=BeaconLifecycleEntitlementOutcome.BLOCKED,
    beacon_source_reference=_BM08_FREE_COUNTRY_WIDE_BLOCKED_SNAPSHOT.beacon_source_reference,
    entitlement_evidence_reference=_BM08_FREE_EVIDENCE,
    effective_entitlement_snapshot=_BM08_FREE_COUNTRY_WIDE_BLOCKED_SNAPSHOT,
    requested_interval_minutes=180,
    active_beacon_count=0,
    requested_country_wide=True,
    rejection_reason=BeaconLifecycleEntitlementRejectionReason.FREE_COUNTRY_WIDE_REQUIRES_CITY,
)

_BM08_FREE_INTERVAL_BELOW_FLOOR_DECISION = _lifecycle_entitlement_decision(
    decision_id="decision-bm08-free-floor-blocked-001",
    beacon_id="beacon-bm08-free-floor-blocked-001",
    account_id=_OWN_ACCOUNT_ID,
    action_kind=BeaconLifecycleActionKind.ACTIVATE,
    outcome=BeaconLifecycleEntitlementOutcome.BLOCKED,
    beacon_source_reference=_BM08_FREE_INTERVAL_BELOW_FLOOR_SNAPSHOT.beacon_source_reference,
    entitlement_evidence_reference=_BM08_FREE_EVIDENCE,
    effective_entitlement_snapshot=_BM08_FREE_INTERVAL_BELOW_FLOOR_SNAPSHOT,
    requested_interval_minutes=179,
    active_beacon_count=0,
    requested_country_wide=False,
    selected_city="synthetic-city",
    rejection_reason=BeaconLifecycleEntitlementRejectionReason.FREE_INTERVAL_BELOW_FLOOR,
)

_BM08_FREE_INTERVAL_STEP_BLOCKED_DECISION = _lifecycle_entitlement_decision(
    decision_id="decision-bm08-free-step-blocked-001",
    beacon_id="beacon-bm08-free-step-blocked-001",
    account_id=_OWN_ACCOUNT_ID,
    action_kind=BeaconLifecycleActionKind.ACTIVATE,
    outcome=BeaconLifecycleEntitlementOutcome.BLOCKED,
    beacon_source_reference=_BM08_FREE_INTERVAL_STEP_BLOCKED_SNAPSHOT.beacon_source_reference,
    entitlement_evidence_reference=_BM08_FREE_EVIDENCE,
    effective_entitlement_snapshot=_BM08_FREE_INTERVAL_STEP_BLOCKED_SNAPSHOT,
    requested_interval_minutes=181,
    active_beacon_count=0,
    requested_country_wide=False,
    selected_city="synthetic-city",
    rejection_reason=BeaconLifecycleEntitlementRejectionReason.FREE_INTERVAL_NOT_STEP,
)

_BM08_FREE_ACTIVE_LIMIT_BLOCKED_DECISION = _lifecycle_entitlement_decision(
    decision_id="decision-bm08-free-limit-blocked-001",
    beacon_id="beacon-bm08-free-limit-blocked-001",
    account_id=_OWN_ACCOUNT_ID,
    action_kind=BeaconLifecycleActionKind.ACTIVATE,
    outcome=BeaconLifecycleEntitlementOutcome.BLOCKED,
    beacon_source_reference=_BM08_FREE_ACTIVE_LIMIT_BLOCKED_SNAPSHOT.beacon_source_reference,
    entitlement_evidence_reference=_BM08_FREE_EVIDENCE,
    effective_entitlement_snapshot=_BM08_FREE_ACTIVE_LIMIT_BLOCKED_SNAPSHOT,
    requested_interval_minutes=180,
    active_beacon_count=1,
    requested_country_wide=False,
    selected_city="synthetic-city",
    rejection_reason=BeaconLifecycleEntitlementRejectionReason.ACTIVE_LIMIT_EXCEEDED,
)

_BM08_EXCLUDED_COUNTS_DECISION = _lifecycle_entitlement_decision(
    decision_id="decision-bm08-excluded-counts-001",
    beacon_id="beacon-bm08-excluded-counts-001",
    account_id=_OWN_ACCOUNT_ID,
    action_kind=BeaconLifecycleActionKind.ACTIVATE,
    outcome=BeaconLifecycleEntitlementOutcome.ALLOWED,
    beacon_source_reference=_BM08_EXCLUDED_COUNTS_SNAPSHOT.beacon_source_reference,
    entitlement_evidence_reference=_BM08_BASIC_EVIDENCE,
    effective_entitlement_snapshot=_BM08_EXCLUDED_COUNTS_SNAPSHOT,
    requested_interval_minutes=5,
    active_beacon_count=0,
    archived_beacon_count=1,
    history_beacon_count=1,
    deleted_beacon_count=1,
    requested_country_wide=False,
)

_BM08_AMBIGUOUS_DECISION = _lifecycle_entitlement_decision(
    decision_id="decision-bm08-ambiguous-001",
    beacon_id="beacon-bm08-ambiguous-001",
    account_id=_OWN_ACCOUNT_ID,
    action_kind=BeaconLifecycleActionKind.ACTIVATE,
    outcome=BeaconLifecycleEntitlementOutcome.AMBIGUOUS,
    beacon_source_reference=_BM08_AMBIGUOUS_SNAPSHOT.beacon_source_reference,
    entitlement_evidence_reference=_BM08_AMBIGUOUS_EVIDENCE,
    effective_entitlement_snapshot=_BM08_AMBIGUOUS_SNAPSHOT,
    requested_interval_minutes=5,
    active_beacon_count=0,
    requested_country_wide=False,
    rejection_reason=BeaconLifecycleEntitlementRejectionReason.AMBIGUOUS_ENTITLEMENT,
)

_BM08_DENIED_DECISION = _lifecycle_entitlement_decision(
    decision_id="decision-bm08-denied-001",
    beacon_id="beacon-bm08-denied-001",
    account_id=_OWN_ACCOUNT_ID,
    action_kind=BeaconLifecycleActionKind.ACTIVATE,
    outcome=BeaconLifecycleEntitlementOutcome.DENIED,
    beacon_source_reference=_BM08_DENIED_SNAPSHOT.beacon_source_reference,
    entitlement_evidence_reference=_BM08_DENIED_EVIDENCE,
    effective_entitlement_snapshot=_BM08_DENIED_SNAPSHOT,
    requested_interval_minutes=5,
    active_beacon_count=0,
    requested_country_wide=False,
    rejection_reason=BeaconLifecycleEntitlementRejectionReason.DENIED_ENTITLEMENT,
)

_BM08_RECHECK_REQUIRED_DECISION = _lifecycle_entitlement_decision(
    decision_id="decision-bm08-recheck-required-001",
    beacon_id="beacon-bm08-recheck-required-001",
    account_id=_OWN_ACCOUNT_ID,
    action_kind=BeaconLifecycleActionKind.RESUME,
    outcome=BeaconLifecycleEntitlementOutcome.RECHECK_REQUIRED,
    beacon_source_reference=_BM08_RECHECK_REQUIRED_SNAPSHOT.beacon_source_reference,
    entitlement_evidence_reference=_BM08_RECHECK_EVIDENCE,
    effective_entitlement_snapshot=_BM08_RECHECK_REQUIRED_SNAPSHOT,
    requested_interval_minutes=5,
    active_beacon_count=0,
    requested_country_wide=False,
    paid_access_expired=True,
    entitlement_recheck_reference="entitlement-recheck-bm08-001",
    future_notification_reference="future-notification-reference-bm08-recheck-001",
    rejection_reason=BeaconLifecycleEntitlementRejectionReason.RECHECK_REQUIRED,
)

_BM08_FROZEN_DECISION = _lifecycle_entitlement_decision(
    decision_id="decision-bm08-frozen-001",
    beacon_id="beacon-bm08-frozen-001",
    account_id=_OWN_ACCOUNT_ID,
    action_kind=BeaconLifecycleActionKind.FREEZE_AFTER_EXPIRY,
    outcome=BeaconLifecycleEntitlementOutcome.FROZEN,
    beacon_source_reference=_BM08_FROZEN_SNAPSHOT.beacon_source_reference,
    entitlement_evidence_reference=_BM08_EXPIRED_EVIDENCE,
    effective_entitlement_snapshot=_BM08_FROZEN_SNAPSHOT,
    requested_interval_minutes=5,
    active_beacon_count=0,
    requested_country_wide=False,
    paid_access_expired=True,
    future_notification_reference="future-notification-reference-bm08-frozen-001",
    rejection_reason=BeaconLifecycleEntitlementRejectionReason.EXPIRED_ENTITLEMENT,
)

_BM08_USER_CHOICE_REQUIRED_DECISION = _lifecycle_entitlement_decision(
    decision_id="decision-bm08-user-choice-required-001",
    beacon_id="beacon-bm08-user-choice-required-001",
    account_id=_OWN_ACCOUNT_ID,
    action_kind=BeaconLifecycleActionKind.RESUME,
    outcome=BeaconLifecycleEntitlementOutcome.USER_CHOICE_REQUIRED,
    beacon_source_reference=_BM08_USER_CHOICE_REQUIRED_SNAPSHOT.beacon_source_reference,
    entitlement_evidence_reference=_BM08_EXPIRED_EVIDENCE,
    effective_entitlement_snapshot=_BM08_USER_CHOICE_REQUIRED_SNAPSHOT,
    requested_interval_minutes=5,
    active_beacon_count=0,
    requested_country_wide=False,
    paid_access_expired=True,
    entitlement_recheck_reference="entitlement-recheck-bm08-user-choice-001",
    future_notification_reference="future-notification-reference-bm08-user-choice-001",
    rejection_reason=BeaconLifecycleEntitlementRejectionReason.EXPIRED_ENTITLEMENT,
)

_BM08_FREE_COMPLIANCE_REQUIRED_DECISION = _lifecycle_entitlement_decision(
    decision_id="decision-bm08-free-compliance-required-001",
    beacon_id="beacon-bm08-free-compliance-required-001",
    account_id=_OWN_ACCOUNT_ID,
    action_kind=BeaconLifecycleActionKind.ACTIVATE,
    outcome=BeaconLifecycleEntitlementOutcome.FREE_COMPLIANCE_REQUIRED,
    beacon_source_reference=_BM08_FREE_COMPLIANCE_REQUIRED_SNAPSHOT.beacon_source_reference,
    entitlement_evidence_reference=_BM08_EXPIRED_EVIDENCE,
    effective_entitlement_snapshot=_BM08_FREE_COMPLIANCE_REQUIRED_SNAPSHOT,
    requested_interval_minutes=180,
    active_beacon_count=0,
    requested_country_wide=False,
    paid_access_expired=True,
    selected_free_beacon_id="beacon-bm08-free-selected-001",
    selected_free_beacon_user_choice_reference="choice-bm08-free-selected-001",
    future_notification_reference="future-notification-reference-bm08-free-compliance-001",
    rejection_reason=BeaconLifecycleEntitlementRejectionReason.FREE_COMPLIANCE_REQUIRED,
)

_BM08_NOTIFICATION_ONLY_DECISION = _lifecycle_entitlement_decision(
    decision_id="decision-bm08-notification-only-001",
    beacon_id="beacon-bm08-notification-only-001",
    account_id=_OWN_ACCOUNT_ID,
    action_kind=BeaconLifecycleActionKind.FREEZE_AFTER_EXPIRY,
    outcome=BeaconLifecycleEntitlementOutcome.USER_CHOICE_REQUIRED,
    beacon_source_reference=_BM08_NOTIFICATION_ONLY_SNAPSHOT.beacon_source_reference,
    entitlement_evidence_reference=_BM08_NOTIFICATION_EVIDENCE,
    effective_entitlement_snapshot=_BM08_NOTIFICATION_ONLY_SNAPSHOT,
    requested_interval_minutes=5,
    active_beacon_count=0,
    requested_country_wide=False,
    paid_access_expired=True,
    future_notification_reference="future-notification-reference-bm08-notification-001",
    rejection_reason=BeaconLifecycleEntitlementRejectionReason.EXPIRED_ENTITLEMENT,
)

_BM08_PROVENANCE_DISTINCT_DECISION = _lifecycle_entitlement_decision(
    decision_id="decision-bm08-provenance-distinct-001",
    beacon_id="beacon-bm08-provenance-distinct-001",
    account_id=_OWN_ACCOUNT_ID,
    action_kind=BeaconLifecycleActionKind.ACTIVATE,
    outcome=BeaconLifecycleEntitlementOutcome.ALLOWED,
    beacon_source_reference=_BM08_PROVENANCE_DISTINCT_SNAPSHOT.beacon_source_reference,
    entitlement_evidence_reference=_BM08_PROVENANCE_EVIDENCE,
    effective_entitlement_snapshot=_BM08_PROVENANCE_DISTINCT_SNAPSHOT,
    requested_interval_minutes=5,
    active_beacon_count=2,
    requested_country_wide=False,
)

SYNTHETIC_FIXTURE_CASES: Final[tuple[SyntheticFixtureCase, ...]] = (
    SyntheticFixtureCase(
        fixture_id="FX-BM-ACTIVE-OWN-001",
        summary="Own-account active Beacon stays owned and active.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        beacon=_OWN_ACTIVE_BEACON,
        source_url=_OWN_ACTIVE_BEACON.source_url,
        snapshot=_ACTIVE_SNAPSHOT,
        current_configuration=_OWN_ACTIVE_BEACON.current_configuration,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM-FOREIGN-DENIED-001",
        summary="Foreign-account Beacon is denied to the non-owner.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        beacon=_FOREIGN_ACCESS_BEACON,
        source_url=_FOREIGN_ACCESS_BEACON.source_url,
        activation_decision=BeaconActivationDecision(
            beacon_id="beacon-bm-002",
            account_id=_FOREIGN_ACCOUNT_ID,
            access_tier=BeaconAccessTier.FREE,
            status=BeaconDecisionStatus.DENIED,
            requested_interval_minutes=180,
            interval_floor_minutes=180,
            interval_step_minutes=180,
            active_beacon_limit=1,
            requested_country_wide=False,
            country_wide_allowed=False,
            city_required=True,
            requested_city="synthetic-city",
            selected_beacon_id=None,
            expiry_outcomes=(),
            reason_code="FOREIGN_ACCOUNT_DENIED",
            reason="Synthetic foreign-account access is denied.",
        ),
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM-DUPLICATE-SAME-ACCOUNT-001",
        summary="Same-account duplicate source URL is allowed for two Beacon IDs.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        beacon=_DUPLICATE_SAME_ACCOUNT_FIRST,
        peer_beacon=_DUPLICATE_SAME_ACCOUNT_SECOND,
        source_url=_DUPLICATE_SAME_ACCOUNT_FIRST.source_url,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM-DUPLICATE-CROSS-ACCOUNT-001",
        summary="Cross-account duplicate source URL is allowed.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        beacon=_DUPLICATE_SAME_ACCOUNT_FIRST,
        peer_beacon=_DUPLICATE_CROSS_ACCOUNT,
        source_url=_DUPLICATE_SAME_ACCOUNT_FIRST.source_url,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM-FREE-COUNTRY-WIDE-BLOCKED-001",
        summary="Free country-wide activation is blocked and requires a city.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        activation_decision=_FREE_COUNTRY_WIDE_BLOCKED,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM-BASIC-COUNTRY-WIDE-ALLOWED-001",
        summary="Basic country-wide activation is allowed.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        activation_decision=_BASIC_COUNTRY_WIDE_ALLOWED,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM-FREE-INTERVAL-180-ACCEPTED-001",
        summary="Free interval at 180 minutes is accepted.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        activation_decision=_FREE_INTERVAL_ACCEPTED,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM-BASIC-INTERVAL-5-ACCEPTED-001",
        summary="Basic interval at 5 minutes is accepted.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        activation_decision=_BASIC_INTERVAL_ACCEPTED,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM-UNSUPPORTED-OVERRIDE-001",
        summary="Unsupported filter override is rejected and not applied.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        override=_UNSUPPORTED_OVERRIDE,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM-MULTIVALUE-OVERRIDE-001",
        summary="Multivalue override preserves every approved value.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        override=_MULTIVALUE_OVERRIDE,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM-PARSER-UNSAFE-001",
        summary="Malformed parser outcome remains not clean.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        snapshot=_MALFORMED_SNAPSHOT,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM-PARSER-CAPTCHA-001",
        summary="CAPTCHA-affected parser outcome remains not clean.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        snapshot=_CAPTCHA_SNAPSHOT,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM-PARSER-BM05-CLEAN-OPAQUE-ACCEPTED-001",
        summary="Clean parser outcome is accepted only with opaque parser evidence.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        beacon=_beacon(
            beacon_id="beacon-bm05-clean-accepted-001",
            account_id=_OWN_ACCOUNT_ID,
            display_name="Synthetic BM05 clean accepted beacon",
            lifecycle_state=BeaconLifecycleState.ACTIVE,
            current_revision_id="rev-bm05-clean-accepted-001",
            source_reference="source-ref-bm05-clean-accepted-001",
            snapshot=_BM05_CLEAN_SNAPSHOT,
        ),
        source_url=_source_url(
            "source-ref-bm05-clean-accepted-001",
            "https://example.invalid/search?query=bm05-clean-accepted&city=synthetic",
        ),
        snapshot=_BM05_CLEAN_SNAPSHOT,
        snapshot_acceptance_decision=_BM05_CLEAN_ACCEPTANCE,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM-PARSER-BM05-MALFORMED-REJECTED-001",
        summary="Malformed parser outcome is rejected.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        snapshot=_BM05_MALFORMED_SNAPSHOT,
        snapshot_acceptance_decision=_BM05_MALFORMED_ACCEPTANCE,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM-PARSER-BM05-INCOMPLETE-REJECTED-001",
        summary="Incomplete parser outcome is rejected.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        snapshot=_BM05_INCOMPLETE_SNAPSHOT,
        snapshot_acceptance_decision=_BM05_INCOMPLETE_ACCEPTANCE,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM-PARSER-BM05-CAPTCHA-REJECTED-001",
        summary="CAPTCHA-affected parser outcome is rejected.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        snapshot=_BM05_CAPTCHA_SNAPSHOT,
        snapshot_acceptance_decision=_BM05_CAPTCHA_ACCEPTANCE,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM-PARSER-BM05-BLOCKED-REJECTED-001",
        summary="Blocked parser outcome is rejected.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        snapshot=_BM05_BLOCKED_SNAPSHOT,
        snapshot_acceptance_decision=_BM05_BLOCKED_ACCEPTANCE,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM-PARSER-BM05-ROUTE-FAILED-REJECTED-001",
        summary="Route-failed parser outcome is rejected.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        snapshot=_BM05_ROUTE_FAILED_SNAPSHOT,
        snapshot_acceptance_decision=_BM05_ROUTE_FAILED_ACCEPTANCE,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM-PARSER-BM05-AMBIGUOUS-REJECTED-001",
        summary="Ambiguous parser outcome is rejected.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        snapshot=_BM05_AMBIGUOUS_SNAPSHOT,
        snapshot_acceptance_decision=_BM05_AMBIGUOUS_ACCEPTANCE,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM-PARSER-BM05-UNSUPPORTED-REJECTED-001",
        summary="Unsupported parser outcome is rejected.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        snapshot=_BM05_UNSUPPORTED_SNAPSHOT,
        snapshot_acceptance_decision=_BM05_UNSUPPORTED_ACCEPTANCE,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM-PARSER-BM05-RAW-PROVIDER-AUTHORITY-REJECTED-001",
        summary="Raw provider payload authority is rejected.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        snapshot=_BM05_RAW_PROVIDER_AUTHORITY_SNAPSHOT,
        snapshot_acceptance_decision=_BM05_RAW_PROVIDER_AUTHORITY_ACCEPTANCE,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM-PARSER-BM05-RAW-HTML-REJECTED-001",
        summary="Raw HTML parser evidence reference is rejected.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        snapshot=_BM05_RAW_HTML_SNAPSHOT,
        snapshot_acceptance_decision=_BM05_RAW_HTML_ACCEPTANCE,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM-PARSER-BM05-RAW-SEARCHCORE-REJECTED-001",
        summary="Raw searchCore parser evidence reference is rejected.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        snapshot=_BM05_RAW_SEARCH_CORE_SNAPSHOT,
        snapshot_acceptance_decision=_BM05_RAW_SEARCH_CORE_ACCEPTANCE,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM-PARSER-BM05-RAW-CONTEXT-REJECTED-001",
        summary="Raw context parser evidence reference is rejected.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        snapshot=_BM05_RAW_CONTEXT_SNAPSHOT,
        snapshot_acceptance_decision=_BM05_RAW_CONTEXT_ACCEPTANCE,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM-PARSER-BM05-THRESHOLD-DEFERRED-001",
        summary="Acceptance threshold stays deferred without inventing a numeric threshold.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        snapshot=_BM05_THRESHOLD_DEFERRED_SNAPSHOT,
        snapshot_acceptance_decision=_BM05_THRESHOLD_DEFERRED_ACCEPTANCE,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM-PARSER-BM05-UNSUPPORTED-PARAMETERS-REJECTED-001",
        summary="Unsupported parameters are not silently accepted.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        snapshot=_BM05_UNSUPPORTED_PARAMETERS_SNAPSHOT,
        snapshot_acceptance_decision=_BM05_UNSUPPORTED_PARAMETERS_ACCEPTANCE,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM-ARCHIVED-EXCLUDED-001",
        summary="Archived Beacon does not count toward active limit.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        beacon=_ARCHIVED_BEACON,
        history_entry=_ARCHIVED_HISTORY_ENTRY,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM-PERMANENTLY-DELETED-001",
        summary="Permanently deleted Beacon is not restorable.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        beacon=_PERMANENTLY_DELETED_BEACON,
        history_entry=_PERMANENTLY_DELETED_HISTORY_ENTRY,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM-PATCH-SAVE-001",
        summary="Patch-based save changes only supplied fields.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        mutation_decision=_PATCH_SAVE_MUTATION,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM-LAST-WRITE-WINS-001",
        summary="Same-field later successful save is authoritative.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        mutation_decision=_LAST_WRITE_WINS_MUTATION,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM-SOURCE-URL-PREP-CREATED-001",
        summary="Prepared source URL creates a Beacon while preserving submitted evidence.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        beacon=_beacon(
            beacon_id="beacon-bm-prep-created-001",
            account_id=_OWN_ACCOUNT_ID,
            display_name="Synthetic source URL created beacon",
            lifecycle_state=BeaconLifecycleState.ACTIVE,
            current_revision_id="rev-bm-prep-created-001",
            source_reference="source-ref-bm-prep-created-001",
            snapshot=_ACTIVE_SNAPSHOT,
            source_url=_SOURCE_URL_PREPARED_CREATED,
        ),
        source_url=_SOURCE_URL_PREPARED_CREATED,
        current_configuration=_configuration(
            beacon_id="beacon-bm-prep-created-001",
            account_id=_OWN_ACCOUNT_ID,
            source_url=_SOURCE_URL_PREPARED_CREATED,
            snapshot=_ACTIVE_SNAPSHOT,
            display_name="Synthetic source URL created beacon",
            lifecycle_state=BeaconLifecycleState.ACTIVE,
            current_revision_id="rev-bm-prep-created-001",
        ),
        source_url_preparation_decision=_SOURCE_URL_PREP_CREATED_DECISION,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM-SOURCE-URL-PREP-REPLAYED-001",
        summary="Replayed source URL preparation uses explicit scope and idempotency basis.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        beacon=_beacon(
            beacon_id="beacon-bm-prep-replayed-001",
            account_id=_OWN_ACCOUNT_ID,
            display_name="Synthetic source URL replayed beacon",
            lifecycle_state=BeaconLifecycleState.ACTIVE,
            current_revision_id="rev-bm-prep-replayed-001",
            source_reference="source-ref-bm-prep-replayed-001",
            snapshot=_ACTIVE_SNAPSHOT,
            source_url=_SOURCE_URL_PREPARED_REPLAYED,
        ),
        source_url=_SOURCE_URL_PREPARED_REPLAYED,
        current_configuration=_configuration(
            beacon_id="beacon-bm-prep-replayed-001",
            account_id=_OWN_ACCOUNT_ID,
            source_url=_SOURCE_URL_PREPARED_REPLAYED,
            snapshot=_ACTIVE_SNAPSHOT,
            display_name="Synthetic source URL replayed beacon",
            lifecycle_state=BeaconLifecycleState.ACTIVE,
            current_revision_id="rev-bm-prep-replayed-001",
        ),
        source_url_preparation_decision=_SOURCE_URL_PREP_REPLAYED_DECISION,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM-SOURCE-URL-PREP-DUPLICATE-SAME-ACCOUNT-001",
        summary="Same-account duplicate source URL is allowed for two Beacon IDs.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        beacon=_DUPLICATE_SAME_ACCOUNT_FIRST,
        peer_beacon=_DUPLICATE_SAME_ACCOUNT_SECOND,
        source_url=_DUPLICATE_SAME_ACCOUNT_FIRST.source_url,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM-SOURCE-URL-PREP-DUPLICATE-CROSS-ACCOUNT-001",
        summary="Cross-account duplicate source URL is allowed.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        beacon=_DUPLICATE_SAME_ACCOUNT_FIRST,
        peer_beacon=_DUPLICATE_CROSS_ACCOUNT,
        source_url=_DUPLICATE_SAME_ACCOUNT_FIRST.source_url,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM-SOURCE-URL-PREP-MALFORMED-REJECTED-001",
        summary="Malformed submitted source URL is rejected before effect.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        source_url=_SOURCE_URL_PREPARED_MALFORMED,
        source_url_preparation_decision=_SOURCE_URL_PREP_MALFORMED_DECISION,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM-SOURCE-URL-PREP-SOURCE-ONLY-IDEMPOTENCY-REJECTED-001",
        summary="Source URL alone is not a valid idempotency basis.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        source_url=_SOURCE_URL_PREPARED_CREATED,
        source_url_preparation_decision=_SOURCE_URL_PREP_SOURCE_ONLY_IDEMPOTENCY_DECISION,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM-SOURCE-URL-PREP-DUPLICATE-BLOCKING-POLICY-REJECTED-001",
        summary="Duplicate source URL blocking policy is rejected by default.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        source_url=_SOURCE_URL_PREPARED_CREATED,
        source_url_preparation_decision=_SOURCE_URL_PREP_DUPLICATE_BLOCKING_POLICY_DECISION,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM-SOURCE-URL-PREP-SNAPSHOT-OVERRIDE-PRESERVED-001",
        summary="Original source URL is preserved across snapshot and override evidence.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        beacon=_beacon(
            beacon_id="beacon-bm-prep-override-001",
            account_id=_OWN_ACCOUNT_ID,
            display_name="Synthetic source URL override-preserved beacon",
            lifecycle_state=BeaconLifecycleState.ACTIVE,
            current_revision_id="rev-bm-prep-override-001",
            source_reference="source-ref-bm-prep-override-001",
            snapshot=_ACTIVE_SNAPSHOT,
            source_url=_SOURCE_URL_PREPARED_OVERRIDE,
            overrides=(_ACTIVE_OVERRIDE,),
        ),
        source_url=_SOURCE_URL_PREPARED_OVERRIDE,
        current_configuration=_configuration(
            beacon_id="beacon-bm-prep-override-001",
            account_id=_OWN_ACCOUNT_ID,
            source_url=_SOURCE_URL_PREPARED_OVERRIDE,
            snapshot=_ACTIVE_SNAPSHOT,
            display_name="Synthetic source URL override-preserved beacon",
            lifecycle_state=BeaconLifecycleState.ACTIVE,
            current_revision_id="rev-bm-prep-override-001",
            overrides=(_ACTIVE_OVERRIDE,),
        ),
        source_url_preparation_decision=_SOURCE_URL_PREP_OVERRIDE_DECISION,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM-SOURCE-URL-PREP-FINGERPRINT-OPAQUE-001",
        summary="Opaque fingerprint reference is allowed only under captured policy.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        beacon=_beacon(
            beacon_id="beacon-bm-prep-fingerprint-001",
            account_id=_OWN_ACCOUNT_ID,
            display_name="Synthetic source URL fingerprint beacon",
            lifecycle_state=BeaconLifecycleState.ACTIVE,
            current_revision_id="rev-bm-prep-fingerprint-001",
            source_reference="source-ref-bm-prep-fingerprint-001",
            snapshot=_ACTIVE_SNAPSHOT,
            source_url=_SOURCE_URL_PREPARED_FINGERPRINT,
        ),
        source_url=_SOURCE_URL_PREPARED_FINGERPRINT,
        current_configuration=_configuration(
            beacon_id="beacon-bm-prep-fingerprint-001",
            account_id=_OWN_ACCOUNT_ID,
            source_url=_SOURCE_URL_PREPARED_FINGERPRINT,
            snapshot=_ACTIVE_SNAPSHOT,
            display_name="Synthetic source URL fingerprint beacon",
            lifecycle_state=BeaconLifecycleState.ACTIVE,
            current_revision_id="rev-bm-prep-fingerprint-001",
        ),
        source_url_preparation_decision=_SOURCE_URL_PREP_FINGERPRINT_DECISION,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM-SOURCE-URL-PREP-TRACKING-POLICY-001",
        summary="Tracking params are ignored only with explicit captured policy reference.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        beacon=_beacon(
            beacon_id="beacon-bm-prep-tracking-001",
            account_id=_OWN_ACCOUNT_ID,
            display_name="Synthetic source URL tracking-policy beacon",
            lifecycle_state=BeaconLifecycleState.ACTIVE,
            current_revision_id="rev-bm-prep-tracking-001",
            source_reference="source-ref-bm-prep-tracking-001",
            snapshot=_ACTIVE_SNAPSHOT,
            source_url=_SOURCE_URL_PREPARED_TRACKING,
        ),
        source_url=_SOURCE_URL_PREPARED_TRACKING,
        current_configuration=_configuration(
            beacon_id="beacon-bm-prep-tracking-001",
            account_id=_OWN_ACCOUNT_ID,
            source_url=_SOURCE_URL_PREPARED_TRACKING,
            snapshot=_ACTIVE_SNAPSHOT,
            display_name="Synthetic source URL tracking-policy beacon",
            lifecycle_state=BeaconLifecycleState.ACTIVE,
            current_revision_id="rev-bm-prep-tracking-001",
        ),
        source_url_preparation_decision=_SOURCE_URL_PREP_TRACKING_DECISION,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM-SOURCE-URL-PREP-SHELL-BLOCKED-001",
        summary="Blocked shell command remains non-interpolating for the submitted URL.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        source_url=_SOURCE_URL_PREPARED_SHELL,
        source_url_preparation_decision=_SOURCE_URL_PREP_SHELL_DECISION,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM-AUTHZ-OWNER-UPDATE-VERIFIED-001",
        summary="Verified owner can update the owned Beacon.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        beacon=_OWN_ACTIVE_BEACON,
        ownership_decision=_OWN_UPDATE_ALLOWED,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM-AUTHZ-OWNER-UPDATE-UNVERIFIED-001",
        summary="Unverified owner mutation is blocked until verification.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        beacon=_OWN_ACTIVE_BEACON,
        ownership_decision=_OWN_UPDATE_REQUIRES_VERIFIED,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM-AUTHZ-FOREIGN-READ-BLOCKED-001",
        summary="Foreign-account read is blocked without existence-sensitive detail.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        beacon=_FOREIGN_ACCESS_BEACON,
        ownership_decision=_FOREIGN_READ_BLOCKED,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM-AUTHZ-FOREIGN-MUTATE-BLOCKED-001",
        summary="Foreign-account mutation is blocked without existence-sensitive detail.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        beacon=_FOREIGN_ACCESS_BEACON,
        ownership_decision=_FOREIGN_MUTATE_BLOCKED,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM-AUTHZ-ADMIN-SUPPORT-READ-ALLOWED-001",
        summary="Admin/support read requires server-side scope and audit reference.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        beacon=_OWN_ACTIVE_BEACON,
        authorization_decision=_ADMIN_SUPPORT_READ_ALLOWED,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM-AUTHZ-ADMIN-SUPPORT-READ-REQUIRES-VERIFIED-001",
        summary="Admin/support read requires a verified actor.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        beacon=_OWN_ACTIVE_BEACON,
        authorization_decision=_ADMIN_SUPPORT_READ_REQUIRES_VERIFIED,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM-AUTHZ-ADMIN-SUPPORT-READ-REQUIRES-SCOPE-001",
        summary="Admin/support read requires server-side scope.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        beacon=_OWN_ACTIVE_BEACON,
        authorization_decision=_ADMIN_SUPPORT_READ_REQUIRES_SCOPE,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM-AUTHZ-ADMIN-SUPPORT-MUTATE-REQUIRES-AUDIT-001",
        summary="Admin/support mutate is blocked when audit reference is missing.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        beacon=_OWN_ACTIVE_BEACON,
        authorization_decision=_ADMIN_SUPPORT_MUTATE_REQUIRES_AUDIT,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM-AUTHZ-CLIENT-FLAG-TELEGRAM-DENIED-001",
        summary="Telegram client flag alone is not authorization.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        beacon=_OWN_ACTIVE_BEACON,
        ownership_decision=_TELEGRAM_CLIENT_FLAG_DENIED,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM-AUTHZ-CLIENT-FLAG-WEB-DENIED-001",
        summary="Web client flag alone is not authorization.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        beacon=_OWN_ACTIVE_BEACON,
        ownership_decision=_WEB_CLIENT_FLAG_DENIED,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM-AUTHZ-CLIENT-FLAG-ADMIN-DENIED-001",
        summary="Admin client flag alone is not authorization.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        beacon=_OWN_ACTIVE_BEACON,
        ownership_decision=_ADMIN_CLIENT_FLAG_DENIED,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM-AUTHZ-SYSTEM-FREEZE-ALLOWED-001",
        summary="System freeze after expiry requires causation and policy source.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        beacon=_OWN_ACTIVE_BEACON,
        authorization_decision=_SYSTEM_FREEZE_ALLOWED,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM-AUTHZ-SYSTEM-FREEZE-BLOCKED-001",
        summary="System freeze after expiry is blocked when causation or policy source is missing.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        beacon=_OWN_ACTIVE_BEACON,
        authorization_decision=_SYSTEM_FREEZE_BLOCKED,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM06-OVERRIDE-SUPPORTED-APPLIED-001",
        summary="Supported explicit field override is applied.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        override_patch_operation=_BM06_SUPPORTED_OVERRIDE_OPERATION,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM06-OVERRIDE-UNSUPPORTED-BLOCKED-001",
        summary="Unsupported field override is blocked and not applied.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        override_patch_operation=_BM06_UNSUPPORTED_OVERRIDE_OPERATION,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM06-OVERRIDE-UNCERTAIN-BLOCKED-001",
        summary="Uncertain field evidence is blocked and not applied.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        override_patch_operation=_BM06_UNCERTAIN_OVERRIDE_OPERATION,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM06-OVERRIDE-AMBIGUOUS-BLOCKED-001",
        summary="Ambiguous field evidence is blocked and not applied.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        override_patch_operation=_BM06_AMBIGUOUS_OVERRIDE_OPERATION,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM06-OVERRIDE-SOURCE-URL-REJECTED-001",
        summary="Source URL override is rejected.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        source_url=_BM06_ACCEPTED_EFFECTIVE_SOURCE_URL,
        override_patch_operation=_BM06_SOURCE_URL_OVERRIDE_OPERATION,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM06-OVERRIDE-MULTIVALUE-PRESERVED-001",
        summary="Multivalue approved values are preserved.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        override_patch_operation=_BM06_MULTIVALUE_OVERRIDE_OPERATION,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM06-OVERRIDE-MULTIVALUE-COLLAPSE-REJECTED-001",
        summary="Silent multivalue collapse is rejected.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        override_patch_operation=_BM06_MULTIVALUE_COLLAPSE_OVERRIDE_OPERATION,
    ),
    SyntheticFixtureCase.model_construct(
        fixture_id="FX-BM06-OVERRIDE-SINGLE-VALUE-MISMATCH-REJECTED-001",
        summary="Single-value applied override mismatch is rejected.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        override_patch_operation=_BM06_SINGLE_VALUE_MISMATCH_OVERRIDE_OPERATION,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM06-EFFECTIVE-CONFIG-ACCEPTED-001",
        summary="Effective config is assembled from accepted snapshot and explicit overrides.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        source_url=_BM06_ACCEPTED_EFFECTIVE_SOURCE_URL,
        snapshot=_BM06_ACCEPTED_EFFECTIVE_SNAPSHOT,
        effective_configuration_decision=_BM06_ACCEPTED_EFFECTIVE_CONFIGURATION,
    ),
    SyntheticFixtureCase.model_construct(
        fixture_id="FX-BM06-EFFECTIVE-CONFIG-SINGLE-VALUE-MISMATCH-REJECTED-001",
        summary="Single-value applied override mismatch is rejected in effective config.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        source_url=_BM06_ACCEPTED_EFFECTIVE_SOURCE_URL,
        snapshot=_BM06_ACCEPTED_EFFECTIVE_SNAPSHOT,
        effective_configuration_decision=_BM06_SINGLE_VALUE_MISMATCH_EFFECTIVE_CONFIGURATION,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM06-EFFECTIVE-CONFIG-NON-ACCEPTED-REJECTED-001",
        summary="Non-accepted snapshot assembly is rejected.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        source_url=_BM06_REJECTED_EFFECTIVE_SOURCE_URL,
        snapshot=_BM06_REJECTED_EFFECTIVE_SNAPSHOT,
        effective_configuration_decision=_BM06_REJECTED_EFFECTIVE_CONFIGURATION,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM06-PATCH-MERGE-NONOVERLAP-001",
        summary="Non-overlapping patch updates merge and preserve absent fields.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        patch_save_decision=_BM06_PATCH_MERGE_DECISION,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM06-PATCH-LAST-WRITE-WINS-001",
        summary="Same-field later successful save is authoritative without DB/runtime claim.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        patch_save_decision=_BM06_PATCH_LAST_WRITE_WINS_DECISION,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM06-PATCH-STALE-FULL-FORM-REJECTED-001",
        summary="Stale full-form overwrite is rejected.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        patch_save_decision=_BM06_PATCH_STALE_FULL_FORM_DECISION,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM07-CURRENT-CONFIG-ACCEPTED-001",
        summary="Exactly one current working configuration is accepted.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        current_configuration=_BM07_CURRENT_CONFIGURATION,
        current_configuration_decision=_BM07_CURRENT_CONFIGURATION_DECISION,
    ),
    SyntheticFixtureCase.model_construct(
        fixture_id="FX-BM07-MULTIPLE-CURRENT-CONFIGS-REJECTED-001",
        summary="More than one current user-facing active configuration is rejected.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        current_configuration=_BM07_CURRENT_CONFIGURATION,
        current_configuration_decision=_BM07_MULTIPLE_CURRENT_CONFIGURATIONS_DECISION,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM07-CURRENT-CONFIG-REPLACED-001",
        summary="Configuration change replaces the current working configuration semantically.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        current_configuration=_BM07_REPLACED_NEW_CONFIGURATION,
        current_configuration_decision=_BM07_REPLACEMENT_DECISION,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM07-COMMITTED-SCAN-EVIDENCE-RETAINED-001",
        summary="Committed scan/audit evidence retains the original configuration reference.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        configuration_evidence_retention_decision=_BM07_COMMITTED_EVIDENCE_DECISION,
    ),
    SyntheticFixtureCase.model_construct(
        fixture_id="FX-BM07-NO-REINTERPRETATION-BLOCKED-001",
        summary="Newer configuration must not rewrite already committed evidence.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        configuration_evidence_retention_decision=_BM07_NO_REINTERPRETATION_DECISION,
    ),
    SyntheticFixtureCase.model_construct(
        fixture_id="FX-BM07-UNBOUNDED-REVISION-CLOUTTER-REJECTED-001",
        summary=(
            "Unbounded old user-facing revisions are rejected as authoritative current settings."
        ),
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        current_configuration=_BM07_UNBOUNDED_REVISIONS_CONFIGURATION,
        current_configuration_decision=_BM07_UNBOUNDED_REVISIONS_DECISION,
    ),
    SyntheticFixtureCase.model_construct(
        fixture_id="FX-BM07-PHYSICAL-COMPACTION-DELETE-REJECTED-001",
        summary="Physical compaction/delete claims are rejected in semantic contracts.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        configuration_evidence_retention_decision=_BM07_PHYSICAL_COMPACTION_DELETE_DECISION,
    ),
    SyntheticFixtureCase.model_construct(
        fixture_id="FX-BM07-RUNTIME-PERSISTENCE-CLAIM-REJECTED-001",
        summary="DB/repository/runtime persistence claims are rejected in semantic contracts.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        configuration_evidence_retention_decision=_BM07_RUNTIME_PERSISTENCE_DECISION,
    ),
    SyntheticFixtureCase.model_construct(
        fixture_id="FX-BM07-SCANRUN-HISTORY-CLAIM-REJECTED-001",
        summary="ScanRun/listing history ownership claims are rejected in semantic contracts.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        configuration_evidence_retention_decision=_BM07_SCANRUN_HISTORY_CLAIM_DECISION,
    ),
    SyntheticFixtureCase.model_construct(
        fixture_id="FX-BM07-MINIMAL-COMMITTED-EVIDENCE-NOT-EDITABLE-001",
        summary="Minimal committed evidence cannot be treated as editable current config.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        configuration_evidence_retention_decision=_BM07_MINIMAL_COMMITTED_EVIDENCE_EDITABLE_DECISION,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM08-BASIC-ALLOWED-001",
        summary="Basic entitlement allows activation with valid evidence and country-wide use.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        entitlement_evidence_reference=_BM08_BASIC_EVIDENCE,
        tariff_policy_band=_BM08_BASIC_BAND,
        effective_entitlement_snapshot=_BM08_BASIC_ALLOWED_SNAPSHOT,
        lifecycle_entitlement_decision=_BM08_BASIC_ALLOWED_DECISION,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM08-BASIC-LIMIT-BLOCKED-001",
        summary="Basic entitlement blocks activation once the active limit is reached.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        entitlement_evidence_reference=_BM08_BASIC_EVIDENCE,
        tariff_policy_band=_BM08_BASIC_BAND,
        effective_entitlement_snapshot=_BM08_BASIC_LIMIT_BLOCKED_SNAPSHOT,
        lifecycle_entitlement_decision=_BM08_BASIC_LIMIT_BLOCKED_DECISION,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM08-BASIC-INTERVAL-BELOW-FLOOR-BLOCKED-001",
        summary="Basic entitlement blocks activation below the minimum interval.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        entitlement_evidence_reference=_BM08_BASIC_EVIDENCE,
        tariff_policy_band=_BM08_BASIC_BAND,
        effective_entitlement_snapshot=_BM08_BASIC_INTERVAL_BELOW_FLOOR_SNAPSHOT,
        lifecycle_entitlement_decision=_BM08_BASIC_INTERVAL_BELOW_FLOOR_DECISION,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM08-BASIC-INTERVAL-STEP-BLOCKED-001",
        summary="Basic entitlement blocks activation when interval is not a 5-minute step.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        entitlement_evidence_reference=_BM08_BASIC_EVIDENCE,
        tariff_policy_band=_BM08_BASIC_BAND,
        effective_entitlement_snapshot=_BM08_BASIC_INTERVAL_STEP_BLOCKED_SNAPSHOT,
        lifecycle_entitlement_decision=_BM08_BASIC_INTERVAL_STEP_BLOCKED_DECISION,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM08-FREE-ALLOWED-001",
        summary="Free entitlement allows activation only with city and 180-minute interval.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        entitlement_evidence_reference=_BM08_FREE_EVIDENCE,
        tariff_policy_band=_BM08_FREE_BAND,
        effective_entitlement_snapshot=_BM08_FREE_ALLOWED_SNAPSHOT,
        lifecycle_entitlement_decision=_BM08_FREE_ALLOWED_DECISION,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM08-FREE-COUNTRY-WIDE-BLOCKED-001",
        summary="Free country-wide activation is blocked until a city is selected.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        entitlement_evidence_reference=_BM08_FREE_EVIDENCE,
        tariff_policy_band=_BM08_FREE_BAND,
        effective_entitlement_snapshot=_BM08_FREE_COUNTRY_WIDE_BLOCKED_SNAPSHOT,
        lifecycle_entitlement_decision=_BM08_FREE_COUNTRY_WIDE_BLOCKED_DECISION,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM08-FREE-INTERVAL-BELOW-FLOOR-BLOCKED-001",
        summary="Free entitlement blocks activation below the 180-minute floor.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        entitlement_evidence_reference=_BM08_FREE_EVIDENCE,
        tariff_policy_band=_BM08_FREE_BAND,
        effective_entitlement_snapshot=_BM08_FREE_INTERVAL_BELOW_FLOOR_SNAPSHOT,
        lifecycle_entitlement_decision=_BM08_FREE_INTERVAL_BELOW_FLOOR_DECISION,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM08-FREE-INTERVAL-STEP-BLOCKED-001",
        summary="Free entitlement blocks activation when interval is not a 180-minute step.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        entitlement_evidence_reference=_BM08_FREE_EVIDENCE,
        tariff_policy_band=_BM08_FREE_BAND,
        effective_entitlement_snapshot=_BM08_FREE_INTERVAL_STEP_BLOCKED_SNAPSHOT,
        lifecycle_entitlement_decision=_BM08_FREE_INTERVAL_STEP_BLOCKED_DECISION,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM08-FREE-ACTIVE-LIMIT-BLOCKED-001",
        summary="Free entitlement blocks activation when one active Beacon already exists.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        entitlement_evidence_reference=_BM08_FREE_EVIDENCE,
        tariff_policy_band=_BM08_FREE_BAND,
        effective_entitlement_snapshot=_BM08_FREE_ACTIVE_LIMIT_BLOCKED_SNAPSHOT,
        lifecycle_entitlement_decision=_BM08_FREE_ACTIVE_LIMIT_BLOCKED_DECISION,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM08-DELETED-HISTORY-ARCHIVED-EXCLUDED-001",
        summary="Deleted, history and archived Beacons are excluded from active limits.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        entitlement_evidence_reference=_BM08_BASIC_EVIDENCE,
        tariff_policy_band=_BM08_BASIC_BAND,
        effective_entitlement_snapshot=_BM08_EXCLUDED_COUNTS_SNAPSHOT,
        lifecycle_entitlement_decision=_BM08_EXCLUDED_COUNTS_DECISION,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM08-AMBIGUOUS-ENTITLEMENT-BLOCKED-001",
        summary="Ambiguous entitlement blocks lifecycle activation or resume.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        entitlement_evidence_reference=_BM08_AMBIGUOUS_EVIDENCE,
        tariff_policy_band=_BM08_BASIC_BAND,
        effective_entitlement_snapshot=_BM08_AMBIGUOUS_SNAPSHOT,
        lifecycle_entitlement_decision=_BM08_AMBIGUOUS_DECISION,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM08-DENIED-ENTITLEMENT-BLOCKED-001",
        summary="Denied entitlement blocks lifecycle activation or resume.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        entitlement_evidence_reference=_BM08_DENIED_EVIDENCE,
        tariff_policy_band=_BM08_BASIC_BAND,
        effective_entitlement_snapshot=_BM08_DENIED_SNAPSHOT,
        lifecycle_entitlement_decision=_BM08_DENIED_DECISION,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM08-RESUME-RECHECK-REQUIRED-001",
        summary="Resume requires an entitlement re-check before lifecycle completion.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        entitlement_evidence_reference=_BM08_RECHECK_EVIDENCE,
        tariff_policy_band=_BM08_BASIC_BAND,
        effective_entitlement_snapshot=_BM08_RECHECK_REQUIRED_SNAPSHOT,
        lifecycle_entitlement_decision=_BM08_RECHECK_REQUIRED_DECISION,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM08-EXPIRED-PAID-FROZEN-001",
        summary=(
            "Expired paid access freezes active paid Beacons and emits only "
            "a future notification reference."
        ),
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        entitlement_evidence_reference=_BM08_EXPIRED_EVIDENCE,
        tariff_policy_band=_BM08_BASIC_BAND,
        effective_entitlement_snapshot=_BM08_FROZEN_SNAPSHOT,
        lifecycle_entitlement_decision=_BM08_FROZEN_DECISION,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM08-EXPIRED-PAID-USER-CHOICE-REQUIRED-001",
        summary="Expired paid access requires user choice instead of automatic Beacon selection.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        entitlement_evidence_reference=_BM08_EXPIRED_EVIDENCE,
        tariff_policy_band=_BM08_BASIC_BAND,
        effective_entitlement_snapshot=_BM08_USER_CHOICE_REQUIRED_SNAPSHOT,
        lifecycle_entitlement_decision=_BM08_USER_CHOICE_REQUIRED_DECISION,
    ),
    SyntheticFixtureCase.model_construct(
        fixture_id="FX-BM08-EXPIRED-PAID-NO-AUTO-CHOICE-REJECTED-001",
        summary="Expired paid access must not auto-select a free Beacon.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        lifecycle_entitlement_decision=BeaconLifecycleEntitlementDecision.model_construct(
            decision_id="decision-bm08-expired-no-auto-choice-001",
            beacon_id="beacon-bm08-expired-no-auto-choice-001",
            account_id=_OWN_ACCOUNT_ID,
            action_kind=BeaconLifecycleActionKind.RESUME,
            outcome=BeaconLifecycleEntitlementOutcome.USER_CHOICE_REQUIRED,
            beacon_source_reference=_BM08_USER_CHOICE_REQUIRED_SNAPSHOT.beacon_source_reference,
            entitlement_evidence_reference=_BM08_EXPIRED_EVIDENCE,
            effective_entitlement_snapshot=_BM08_USER_CHOICE_REQUIRED_SNAPSHOT,
            requested_interval_minutes=5,
            active_beacon_count=0,
            requested_country_wide=False,
            paid_access_expired=True,
            entitlement_recheck_reference="entitlement-recheck-bm08-no-auto-choice-001",
            selected_free_beacon_id="beacon-bm08-auto-choice-001",
            rejection_reason=BeaconLifecycleEntitlementRejectionReason.EXPIRED_PAID_AUTO_CHOICE_FORBIDDEN,
        ),
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM08-SELECTED-FREE-COMPLIANCE-REQUIRED-001",
        summary="A user-selected free Beacon still requires Free compliance before activation.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        entitlement_evidence_reference=_BM08_EXPIRED_EVIDENCE,
        tariff_policy_band=_BM08_FREE_BAND,
        effective_entitlement_snapshot=_BM08_FREE_COMPLIANCE_REQUIRED_SNAPSHOT,
        lifecycle_entitlement_decision=_BM08_FREE_COMPLIANCE_REQUIRED_DECISION,
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM08-NOTIFICATION-FUTURE-REFERENCE-ONLY-001",
        summary="Notification handling is represented only by a future notification reference.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        entitlement_evidence_reference=_BM08_NOTIFICATION_EVIDENCE,
        tariff_policy_band=_BM08_BASIC_BAND,
        effective_entitlement_snapshot=_BM08_NOTIFICATION_ONLY_SNAPSHOT,
        lifecycle_entitlement_decision=_BM08_NOTIFICATION_ONLY_DECISION,
    ),
    SyntheticFixtureCase.model_construct(
        fixture_id="FX-BM08-NOTIFICATION-SENDING-CLAIM-REJECTED-001",
        summary="Notification sending claims are rejected in lifecycle semantics.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        lifecycle_entitlement_decision=BeaconLifecycleEntitlementDecision.model_construct(
            decision_id="decision-bm08-notification-claim-001",
            beacon_id="beacon-bm08-notification-claim-001",
            account_id=_OWN_ACCOUNT_ID,
            action_kind=BeaconLifecycleActionKind.ACTIVATE,
            outcome=BeaconLifecycleEntitlementOutcome.BLOCKED,
            beacon_source_reference=_BM08_BASIC_ALLOWED_SNAPSHOT.beacon_source_reference,
            entitlement_evidence_reference=_BM08_BASIC_EVIDENCE,
            effective_entitlement_snapshot=_BM08_BASIC_ALLOWED_SNAPSHOT,
            requested_interval_minutes=5,
            active_beacon_count=0,
            requested_country_wide=False,
            future_notification_reference="future-notification-reference-bm08-notification-claim-001",
            notification_sending_claimed=True,
            rejection_reason=BeaconLifecycleEntitlementRejectionReason.NOTIFICATION_SENDING_CLAIM,
        ),
    ),
    SyntheticFixtureCase.model_construct(
        fixture_id="FX-BM08-BILLING-PAYMENT-TARIFF-MUTATION-CLAIM-REJECTED-001",
        summary="Billing/payment/tariff mutation claims are rejected in lifecycle semantics.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        lifecycle_entitlement_decision=BeaconLifecycleEntitlementDecision.model_construct(
            decision_id="decision-bm08-billing-mutation-claim-001",
            beacon_id="beacon-bm08-billing-mutation-claim-001",
            account_id=_OWN_ACCOUNT_ID,
            action_kind=BeaconLifecycleActionKind.ACTIVATE,
            outcome=BeaconLifecycleEntitlementOutcome.BLOCKED,
            beacon_source_reference=_BM08_BASIC_ALLOWED_SNAPSHOT.beacon_source_reference,
            entitlement_evidence_reference=_BM08_BASIC_EVIDENCE,
            effective_entitlement_snapshot=_BM08_BASIC_ALLOWED_SNAPSHOT,
            requested_interval_minutes=5,
            active_beacon_count=0,
            requested_country_wide=False,
            billing_payment_tariff_mutation_claimed=True,
            rejection_reason=BeaconLifecycleEntitlementRejectionReason.BILLING_PAYMENT_TARIFF_MUTATION_CLAIM,
        ),
    ),
    SyntheticFixtureCase.model_construct(
        fixture_id="FX-BM08-SCHEDULER-RUNTIME-CLAIM-REJECTED-001",
        summary="Scheduler/runtime claims are rejected in lifecycle semantics.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        lifecycle_entitlement_decision=BeaconLifecycleEntitlementDecision.model_construct(
            decision_id="decision-bm08-scheduler-claim-001",
            beacon_id="beacon-bm08-scheduler-claim-001",
            account_id=_OWN_ACCOUNT_ID,
            action_kind=BeaconLifecycleActionKind.ACTIVATE,
            outcome=BeaconLifecycleEntitlementOutcome.BLOCKED,
            beacon_source_reference=_BM08_BASIC_ALLOWED_SNAPSHOT.beacon_source_reference,
            entitlement_evidence_reference=_BM08_BASIC_EVIDENCE,
            effective_entitlement_snapshot=_BM08_BASIC_ALLOWED_SNAPSHOT,
            requested_interval_minutes=5,
            active_beacon_count=0,
            requested_country_wide=False,
            scheduler_runtime_claimed=True,
            rejection_reason=BeaconLifecycleEntitlementRejectionReason.SCHEDULER_RUNTIME_CLAIM,
        ),
    ),
    SyntheticFixtureCase.model_construct(
        fixture_id="FX-BM08-DB-REPOSITORY-RUNTIME-CLAIM-REJECTED-001",
        summary="DB/repository/runtime persistence claims are rejected in lifecycle semantics.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        lifecycle_entitlement_decision=BeaconLifecycleEntitlementDecision.model_construct(
            decision_id="decision-bm08-db-claim-001",
            beacon_id="beacon-bm08-db-claim-001",
            account_id=_OWN_ACCOUNT_ID,
            action_kind=BeaconLifecycleActionKind.ACTIVATE,
            outcome=BeaconLifecycleEntitlementOutcome.BLOCKED,
            beacon_source_reference=_BM08_BASIC_ALLOWED_SNAPSHOT.beacon_source_reference,
            entitlement_evidence_reference=_BM08_BASIC_EVIDENCE,
            effective_entitlement_snapshot=_BM08_BASIC_ALLOWED_SNAPSHOT,
            requested_interval_minutes=5,
            active_beacon_count=0,
            requested_country_wide=False,
            db_repository_runtime_persistence_claimed=True,
            rejection_reason=BeaconLifecycleEntitlementRejectionReason.DB_REPOSITORY_RUNTIME_PERSISTENCE_CLAIM,
        ),
    ),
    SyntheticFixtureCase.model_construct(
        fixture_id="FX-BM08-SCANRUN-HISTORY-CLAIM-REJECTED-001",
        summary="ScanRun/listing history ownership claims are rejected in lifecycle semantics.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        lifecycle_entitlement_decision=BeaconLifecycleEntitlementDecision.model_construct(
            decision_id="decision-bm08-scanrun-claim-001",
            beacon_id="beacon-bm08-scanrun-claim-001",
            account_id=_OWN_ACCOUNT_ID,
            action_kind=BeaconLifecycleActionKind.ACTIVATE,
            outcome=BeaconLifecycleEntitlementOutcome.BLOCKED,
            beacon_source_reference=_BM08_BASIC_ALLOWED_SNAPSHOT.beacon_source_reference,
            entitlement_evidence_reference=_BM08_BASIC_EVIDENCE,
            effective_entitlement_snapshot=_BM08_BASIC_ALLOWED_SNAPSHOT,
            requested_interval_minutes=5,
            active_beacon_count=0,
            requested_country_wide=False,
            scanrun_listing_history_state_claimed=True,
            rejection_reason=BeaconLifecycleEntitlementRejectionReason.SCANRUN_LISTING_HISTORY_STATE_CLAIM,
        ),
    ),
    SyntheticFixtureCase.model_construct(
        fixture_id="FX-BM08-PARSER-FILTER-CATALOG-CLAIM-REJECTED-001",
        summary="Parser/Filter Catalog ownership claims are rejected in lifecycle semantics.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        lifecycle_entitlement_decision=BeaconLifecycleEntitlementDecision.model_construct(
            decision_id="decision-bm08-parser-filter-claim-001",
            beacon_id="beacon-bm08-parser-filter-claim-001",
            account_id=_OWN_ACCOUNT_ID,
            action_kind=BeaconLifecycleActionKind.ACTIVATE,
            outcome=BeaconLifecycleEntitlementOutcome.BLOCKED,
            beacon_source_reference=_BM08_BASIC_ALLOWED_SNAPSHOT.beacon_source_reference,
            entitlement_evidence_reference=_BM08_BASIC_EVIDENCE,
            effective_entitlement_snapshot=_BM08_BASIC_ALLOWED_SNAPSHOT,
            requested_interval_minutes=5,
            active_beacon_count=0,
            requested_country_wide=False,
            parser_filter_catalog_ownership_claimed=True,
            rejection_reason=BeaconLifecycleEntitlementRejectionReason.PARSER_FILTER_CATALOG_OWNERSHIP_CLAIM,
        ),
    ),
    SyntheticFixtureCase.model_construct(
        fixture_id="FX-BM08-CLIENT-FLAG-NOT-AUTHORIZATION-REJECTED-001",
        summary="Client flags from Telegram/Web/Admin do not authorize lifecycle changes.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        lifecycle_entitlement_decision=BeaconLifecycleEntitlementDecision.model_construct(
            decision_id="decision-bm08-client-flag-claim-001",
            beacon_id="beacon-bm08-client-flag-claim-001",
            account_id=_OWN_ACCOUNT_ID,
            action_kind=BeaconLifecycleActionKind.ACTIVATE,
            outcome=BeaconLifecycleEntitlementOutcome.BLOCKED,
            beacon_source_reference=_BM08_BASIC_ALLOWED_SNAPSHOT.beacon_source_reference,
            entitlement_evidence_reference=_BM08_BASIC_EVIDENCE,
            effective_entitlement_snapshot=_BM08_BASIC_ALLOWED_SNAPSHOT,
            requested_interval_minutes=5,
            active_beacon_count=0,
            requested_country_wide=False,
            client_channel_flag="TELEGRAM",
            client_channel_flag_is_authorization_proof=True,
            rejection_reason=BeaconLifecycleEntitlementRejectionReason.CLIENT_FLAG_NOT_AUTHORIZATION,
        ),
    ),
    SyntheticFixtureCase.model_construct(
        fixture_id="FX-BM08-ACTIVATE-MISSING-EVIDENCE-REJECTED-001",
        summary="Activation without entitlement evidence reference is rejected.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        lifecycle_entitlement_decision=BeaconLifecycleEntitlementDecision.model_construct(
            decision_id="decision-bm08-missing-evidence-001",
            beacon_id="beacon-bm08-missing-evidence-001",
            account_id=_OWN_ACCOUNT_ID,
            action_kind=BeaconLifecycleActionKind.ACTIVATE,
            outcome=BeaconLifecycleEntitlementOutcome.BLOCKED,
            beacon_source_reference="beacon-source-bm08-missing-evidence-001",
            entitlement_evidence_reference=None,
            effective_entitlement_snapshot=None,
            requested_interval_minutes=5,
            active_beacon_count=0,
            requested_country_wide=False,
            rejection_reason=BeaconLifecycleEntitlementRejectionReason.MISSING_ENTITLEMENT_EVIDENCE_REFERENCE,
        ),
    ),
    SyntheticFixtureCase.model_construct(
        fixture_id="FX-BM08-RESUME-STALE-EVIDENCE-REJECTED-001",
        summary="Resume with stale entitlement evidence is rejected.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        lifecycle_entitlement_decision=BeaconLifecycleEntitlementDecision.model_construct(
            decision_id="decision-bm08-stale-resume-001",
            beacon_id="beacon-bm08-stale-resume-001",
            account_id=_OWN_ACCOUNT_ID,
            action_kind=BeaconLifecycleActionKind.RESUME,
            outcome=BeaconLifecycleEntitlementOutcome.RECHECK_REQUIRED,
            beacon_source_reference=_BM08_STALE_RECHECK_SNAPSHOT.beacon_source_reference,
            entitlement_evidence_reference=_BM08_STALE_EVIDENCE,
            effective_entitlement_snapshot=_BM08_STALE_RECHECK_SNAPSHOT,
            requested_interval_minutes=5,
            active_beacon_count=0,
            requested_country_wide=False,
            paid_access_expired=True,
            entitlement_recheck_reference="entitlement-recheck-bm08-stale-001",
            rejection_reason=BeaconLifecycleEntitlementRejectionReason.STALE_ENTITLEMENT_EVIDENCE_REFERENCE,
        ),
    ),
    SyntheticFixtureCase(
        fixture_id="FX-BM08-PROVENANCE-BOUNDARIES-DISTINCT-001",
        summary="Entitlement evidence, source and provenance boundaries remain distinct.",
        account_id=_OWN_ACCOUNT_ID,
        foreign_account_id=_FOREIGN_ACCOUNT_ID,
        entitlement_evidence_reference=_BM08_PROVENANCE_EVIDENCE,
        tariff_policy_band=_BM08_BASIC_BAND,
        effective_entitlement_snapshot=_BM08_PROVENANCE_DISTINCT_SNAPSHOT,
        lifecycle_entitlement_decision=_BM08_PROVENANCE_DISTINCT_DECISION,
    ),
)

SYNTHETIC_FIXTURE_BY_ID: Final[dict[str, SyntheticFixtureCase]] = {
    fixture.fixture_id: fixture for fixture in SYNTHETIC_FIXTURE_CASES
}

FIXTURE_IDS: Final[tuple[str, ...]] = tuple(
    fixture.fixture_id for fixture in SYNTHETIC_FIXTURE_CASES
)

__all__: Final[tuple[str, ...]] = (
    "FIXTURE_IDS",
    "SYNTHETIC_FIXTURE_BY_ID",
    "SYNTHETIC_FIXTURE_CASES",
    "SyntheticFixtureCase",
)
