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
    BeaconCurrentConfiguration,
    BeaconDecisionStatus,
    BeaconExpiryOutcome,
    BeaconFilterOverride,
    BeaconHistoryEntry,
    BeaconHistoryOutcome,
    BeaconLifecycleState,
    BeaconMutationDecision,
    BeaconNameOrigin,
    BeaconNamingMetadata,
    BeaconOverrideStatus,
    BeaconOwnershipDecision,
    BeaconParserEvidenceReference,
    BeaconParserEvidenceSafetyClass,
    BeaconParserOutcomeStatus,
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
    current_configuration: BeaconCurrentConfiguration | None = None
    activation_decision: BeaconActivationDecision | None = None
    mutation_decision: BeaconMutationDecision | None = None
    source_url_preparation_decision: BeaconSourceUrlPreparationDecision | None = None
    ownership_decision: BeaconOwnershipDecision | None = None
    authorization_decision: BeaconAuthorizationDecision | None = None
    history_entry: BeaconHistoryEntry | None = None


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
