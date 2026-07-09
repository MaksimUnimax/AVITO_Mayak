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
    BeaconParserOutcomeStatus,
    BeaconProtectedAction,
    BeaconSourceUrl,
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
    override: BeaconFilterOverride | None = None
    current_configuration: BeaconCurrentConfiguration | None = None
    activation_decision: BeaconActivationDecision | None = None
    mutation_decision: BeaconMutationDecision | None = None
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


def _source_url(reference: str) -> BeaconSourceUrl:
    return BeaconSourceUrl(
        submitted_url=_BASE_URL,
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
    overrides: tuple[BeaconFilterOverride, ...] = (),
    restorable: bool = True,
    counts_toward_active_limit: bool = True,
    history_entries: tuple[BeaconHistoryEntry, ...] = (),
    source_title: str = "synthetic search source",
    source_context_reference: str = "ctx-synth-001",
) -> Beacon:
    source_url = _source_url(source_reference)
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


_ACTIVE_SNAPSHOT = _snapshot(
    snapshot_id="snap-bm-001",
    status=BeaconParserOutcomeStatus.CLEAN,
    accepted_as_clean=True,
    evidence_reference="evidence-bm-001",
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
