"""Semantic contract primitives for Beacon Management."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Final

from pydantic import BaseModel, ConfigDict, Field, model_validator


class BeaconAccessTier(str, Enum):
    """Approved access-tier identifiers for Beacon semantics."""

    FREE = "FREE"
    BASIC = "BASIC"


class BeaconLifecycleState(str, Enum):
    """Deterministic lifecycle states for Beacon semantics."""

    DRAFT = "DRAFT"
    READY = "READY"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    FROZEN = "FROZEN"
    ARCHIVED = "ARCHIVED"
    PERMANENTLY_DELETED = "PERMANENTLY_DELETED"


class BeaconParserOutcomeStatus(str, Enum):
    """Semantic parser outcome classes that gate snapshot acceptance."""

    CLEAN = "CLEAN"
    MALFORMED = "MALFORMED"
    INCOMPLETE = "INCOMPLETE"
    CAPTCHA_AFFECTED = "CAPTCHA_AFFECTED"
    BLOCKED = "BLOCKED"
    ROUTE_FAILED = "ROUTE_FAILED"
    AMBIGUOUS = "AMBIGUOUS"


class BeaconOverrideStatus(str, Enum):
    """Semantic status for a Beacon filter override."""

    APPLIED = "APPLIED"
    REJECTED = "REJECTED"
    UNSUPPORTED = "UNSUPPORTED"
    AMBIGUOUS = "AMBIGUOUS"
    CONFLICT = "CONFLICT"
    REPLAYED = "REPLAYED"


class BeaconDecisionStatus(str, Enum):
    """Deterministic decision outcomes used by activation and mutation semantics."""

    ALLOWED = "ALLOWED"
    DENIED = "DENIED"
    BLOCKED = "BLOCKED"
    FROZEN = "FROZEN"
    USER_CHOICE_REQUIRED = "USER_CHOICE_REQUIRED"
    FREE_COMPLIANCE_REQUIRED = "FREE_COMPLIANCE_REQUIRED"
    REPLAYED = "REPLAYED"
    CONFLICT = "CONFLICT"
    IDEMPOTENCY_MISMATCH = "IDEMPOTENCY_MISMATCH"
    REJECTED = "REJECTED"
    UNSUPPORTED = "UNSUPPORTED"
    AMBIGUOUS = "AMBIGUOUS"


class BeaconHistoryOutcome(str, Enum):
    """Semantic history/archive/delete outcomes."""

    HISTORY = "HISTORY"
    ARCHIVED = "ARCHIVED"
    DELETED = "DELETED"
    PERMANENTLY_DELETED = "PERMANENTLY_DELETED"
    RESTORED = "RESTORED"


class BeaconExpiryOutcome(str, Enum):
    """Semantic outcomes for paid-access expiry handling."""

    FROZEN = "FROZEN"
    HISTORY = "HISTORY"
    USER_CHOICE_REQUIRED = "USER_CHOICE_REQUIRED"
    FREE_COMPLIANCE_REQUIRED = "FREE_COMPLIANCE_REQUIRED"


class BeaconNameOrigin(str, Enum):
    """Semantic origin markers for Beacon naming metadata."""

    USER_PROVIDED = "USER_PROVIDED"
    DERIVED_FROM_SOURCE = "DERIVED_FROM_SOURCE"
    DERIVED_FROM_CONTEXT = "DERIVED_FROM_CONTEXT"
    USER_RENAMED = "USER_RENAMED"


class BeaconActorKind(str, Enum):
    """Semantic actor kinds for account and service authorization."""

    ACCOUNT_OWNER = "ACCOUNT_OWNER"
    ADMIN_SUPPORT = "ADMIN_SUPPORT"
    SYSTEM = "SYSTEM"
    ANONYMOUS = "ANONYMOUS"


class BeaconAuthorizationOutcome(str, Enum):
    """Deterministic authorization outcomes for protected Beacon actions."""

    ALLOWED = "ALLOWED"
    DENIED = "DENIED"
    BLOCKED = "BLOCKED"
    REQUIRES_VERIFIED_ACTOR = "REQUIRES_VERIFIED_ACTOR"
    REQUIRES_SCOPE = "REQUIRES_SCOPE"
    REQUIRES_AUDIT = "REQUIRES_AUDIT"
    NO_EXISTENCE_SENSITIVE_DETAIL = "NO_EXISTENCE_SENSITIVE_DETAIL"


class BeaconProtectedAction(str, Enum):
    """Protected Beacon action identifiers for semantic authorization contracts."""

    CREATE_BEACON = "CREATE_BEACON"
    READ_BEACON = "READ_BEACON"
    UPDATE_BEACON = "UPDATE_BEACON"
    ARCHIVE_BEACON = "ARCHIVE_BEACON"
    RESTORE_BEACON = "RESTORE_BEACON"
    PERMANENTLY_DELETE_BEACON = "PERMANENTLY_DELETE_BEACON"
    ACTIVATE_BEACON = "ACTIVATE_BEACON"
    PAUSE_BEACON = "PAUSE_BEACON"
    SYSTEM_FREEZE_AFTER_EXPIRY = "SYSTEM_FREEZE_AFTER_EXPIRY"
    ADMIN_SUPPORT_READ = "ADMIN_SUPPORT_READ"
    ADMIN_SUPPORT_MUTATE = "ADMIN_SUPPORT_MUTATE"


class BeaconSystemActorClass(str, Enum):
    """Semantic service-actor classes for system lifecycle actions."""

    BEACON_MANAGEMENT_SERVICE = "BEACON_MANAGEMENT_SERVICE"
    ENTITLEMENTS_AND_BILLING_SERVICE = "ENTITLEMENTS_AND_BILLING_SERVICE"
    MAINTENANCE_SERVICE = "MAINTENANCE_SERVICE"
    SCHEDULER_SERVICE = "SCHEDULER_SERVICE"


class BeaconActorContext(BaseModel):
    """Verified actor context with primitive authorization references only."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    actor_context_id: str = Field(min_length=1)
    actor_kind: BeaconActorKind
    is_verified: bool = False
    account_id: str | None = Field(default=None, min_length=1)
    actor_reference_id: str | None = Field(default=None, min_length=1)
    client_channel_flag: str | None = Field(default=None, min_length=1)
    client_channel_flag_is_authorization_proof: bool = False

    @model_validator(mode="after")
    def _validate_actor_context(self) -> "BeaconActorContext":
        if self.actor_kind in {BeaconActorKind.ACCOUNT_OWNER, BeaconActorKind.ADMIN_SUPPORT}:
            if self.account_id is None:
                raise ValueError("account-backed actor context requires account_id")
        elif self.account_id is not None:
            raise ValueError("anonymous or system actor context must not carry account_id")

        if self.actor_kind is BeaconActorKind.ANONYMOUS and self.is_verified:
            raise ValueError("anonymous actor context cannot be verified")

        if self.client_channel_flag_is_authorization_proof:
            raise ValueError("client channel flag is not authorization proof")

        return self


class BeaconActionCausation(BaseModel):
    """System lifecycle causation primitive with policy source reference."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    service_actor_class: BeaconSystemActorClass
    causation_reference: str = Field(min_length=1)
    policy_source_reference: str = Field(min_length=1)


class BeaconOwnershipDecision(BaseModel):
    """Owner-scoped authorization decision for protected Beacon actions."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    decision_id: str = Field(min_length=1)
    protected_action: BeaconProtectedAction
    actor_context: BeaconActorContext
    beacon_id: str = Field(min_length=1)
    beacon_account_id: str = Field(min_length=1)
    outcome: BeaconAuthorizationOutcome
    safe_reason_code: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    existence_sensitive_detail: str | None = None
    foreign_account_existence_sensitive_detail: bool = False

    @model_validator(mode="after")
    def _validate_ownership_decision(self) -> "BeaconOwnershipDecision":
        owner_actions = {
            BeaconProtectedAction.CREATE_BEACON,
            BeaconProtectedAction.READ_BEACON,
            BeaconProtectedAction.UPDATE_BEACON,
            BeaconProtectedAction.ARCHIVE_BEACON,
            BeaconProtectedAction.RESTORE_BEACON,
            BeaconProtectedAction.PERMANENTLY_DELETE_BEACON,
            BeaconProtectedAction.ACTIVATE_BEACON,
            BeaconProtectedAction.PAUSE_BEACON,
        }
        mutation_actions = owner_actions - {BeaconProtectedAction.READ_BEACON}

        if self.existence_sensitive_detail is not None:
            if not self.existence_sensitive_detail.strip():
                raise ValueError("existence sensitive detail must not be blank")
            raise ValueError("foreign-account denial must not reveal existence-sensitive detail")

        if self.foreign_account_existence_sensitive_detail:
            raise ValueError("foreign-account denial must not reveal existence-sensitive detail")

        if (
            self.protected_action in owner_actions
            and self.outcome is BeaconAuthorizationOutcome.ALLOWED
        ):
            if self.actor_context.actor_kind is not BeaconActorKind.ACCOUNT_OWNER:
                raise ValueError("owner action requires an account owner actor context")
            if self.actor_context.account_id != self.beacon_account_id:
                raise ValueError("owner action requires matching actor account_id")

            if self.protected_action in mutation_actions and not self.actor_context.is_verified:
                raise ValueError("mutation requires verified actor context")

        return self


class BeaconAuthorizationDecision(BeaconOwnershipDecision):
    """Extended authorization decision for support and system lifecycle actions."""

    server_role_scope_reference: str | None = Field(default=None, min_length=1)
    server_audit_reference: str | None = Field(default=None, min_length=1)
    action_causation: BeaconActionCausation | None = None

    @model_validator(mode="after")
    def _validate_authorization_decision(self) -> "BeaconAuthorizationDecision":
        if self.protected_action in {
            BeaconProtectedAction.ADMIN_SUPPORT_READ,
            BeaconProtectedAction.ADMIN_SUPPORT_MUTATE,
        }:
            if self.outcome is BeaconAuthorizationOutcome.ALLOWED:
                if self.actor_context.actor_kind is not BeaconActorKind.ADMIN_SUPPORT:
                    raise ValueError("admin/support action requires an admin/support actor context")
                if self.server_role_scope_reference is None:
                    raise ValueError(
                        "admin/support action requires server-side role scope reference"
                    )
                if self.server_audit_reference is None:
                    raise ValueError("admin/support action requires audit reference")

        if self.protected_action is BeaconProtectedAction.SYSTEM_FREEZE_AFTER_EXPIRY:
            if self.outcome is BeaconAuthorizationOutcome.ALLOWED:
                if self.actor_context.actor_kind is not BeaconActorKind.SYSTEM:
                    raise ValueError("system lifecycle action requires a system actor context")
                if self.action_causation is None:
                    raise ValueError("system lifecycle action requires service actor causation")

        return self


def _reject_blank_values(label: str, values: tuple[str, ...]) -> None:
    if any(not value.strip() for value in values):
        raise ValueError(f"{label} must not contain blank values")


class BeaconSourceUrl(BaseModel):
    """User-submitted source URL preserved as evidence."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    submitted_url: str = Field(min_length=1)
    evidence_reference: str = Field(min_length=1)
    submitted_at: datetime | None = None
    source_channel: str = Field(default="user-submitted", min_length=1)
    submitted_by_label: str | None = None


class BeaconNamingMetadata(BaseModel):
    """Presentation metadata for a Beacon."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    display_name: str = Field(min_length=1)
    name_origin: BeaconNameOrigin
    source_title: str | None = None
    source_context_reference: str | None = None
    default_name: str | None = None


class ExtractedSearchConfigurationSnapshot(BaseModel):
    """Accepted normalized extraction outcome received from a parser adapter."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    snapshot_id: str = Field(min_length=1)
    parser_outcome_status: BeaconParserOutcomeStatus
    accepted_as_clean: bool
    normalized_filter_values: tuple[str, ...] = Field(default_factory=tuple)
    unsupported_parameters: tuple[str, ...] = Field(default_factory=tuple)
    warning_codes: tuple[str, ...] = Field(default_factory=tuple)
    evidence_reference: str = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_clean_snapshot(self) -> "ExtractedSearchConfigurationSnapshot":
        _reject_blank_values("normalized_filter_values", self.normalized_filter_values)
        _reject_blank_values("unsupported_parameters", self.unsupported_parameters)
        _reject_blank_values("warning_codes", self.warning_codes)

        unsafe_parser_outcomes = {
            BeaconParserOutcomeStatus.MALFORMED,
            BeaconParserOutcomeStatus.INCOMPLETE,
            BeaconParserOutcomeStatus.CAPTCHA_AFFECTED,
            BeaconParserOutcomeStatus.BLOCKED,
            BeaconParserOutcomeStatus.ROUTE_FAILED,
            BeaconParserOutcomeStatus.AMBIGUOUS,
        }
        if self.accepted_as_clean and self.parser_outcome_status in unsafe_parser_outcomes:
            raise ValueError("unsafe parser outcome cannot become a clean accepted snapshot")
        return self


class BeaconFilterOverride(BaseModel):
    """Explicit user override over a supported Beacon field."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    field_name: str = Field(min_length=1)
    field_supported: bool
    status: BeaconOverrideStatus
    requested_values: tuple[str, ...] = Field(min_length=1)
    applied_values: tuple[str, ...] | None = None
    override_reference: str = Field(min_length=1)
    reason: str | None = None

    @model_validator(mode="after")
    def _validate_override_semantics(self) -> "BeaconFilterOverride":
        _reject_blank_values("requested_values", self.requested_values)
        if self.applied_values is not None:
            _reject_blank_values("applied_values", self.applied_values)

        if not self.field_supported and self.status is BeaconOverrideStatus.APPLIED:
            raise ValueError("unsupported field cannot be represented as applied")

        if (
            self.status
            in {
                BeaconOverrideStatus.REJECTED,
                BeaconOverrideStatus.UNSUPPORTED,
                BeaconOverrideStatus.AMBIGUOUS,
                BeaconOverrideStatus.CONFLICT,
            }
            and self.applied_values is not None
        ):
            raise ValueError("rejected, unsupported or conflicting override must not be applied")

        if self.status is BeaconOverrideStatus.APPLIED and self.applied_values is None:
            raise ValueError("applied override must preserve applied values")

        if self.status is BeaconOverrideStatus.APPLIED and len(self.requested_values) > 1:
            if self.applied_values != self.requested_values:
                raise ValueError("multivalue approved override must preserve all approved values")

        return self


class BeaconCurrentConfiguration(BaseModel):
    """User-facing current working configuration for a Beacon."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    beacon_id: str = Field(min_length=1)
    account_id: str = Field(min_length=1)
    source_url: BeaconSourceUrl
    accepted_snapshot: ExtractedSearchConfigurationSnapshot
    overrides: tuple[BeaconFilterOverride, ...] = Field(default_factory=tuple)
    current_revision_id: str = Field(min_length=1)
    display_name: str = Field(min_length=1)
    lifecycle_state: BeaconLifecycleState
    retained_evidence_references: tuple[str, ...] = Field(default_factory=tuple)
    previous_user_facing_revision_ids: tuple[str, ...] = Field(default_factory=tuple)

    @model_validator(mode="after")
    def _validate_configuration_references(self) -> "BeaconCurrentConfiguration":
        _reject_blank_values("retained_evidence_references", self.retained_evidence_references)
        _reject_blank_values(
            "previous_user_facing_revision_ids",
            self.previous_user_facing_revision_ids,
        )
        return self


class BeaconHistoryEntry(BaseModel):
    """Semantic history/archive/delete record for a Beacon."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    history_entry_id: str = Field(min_length=1)
    beacon_id: str = Field(min_length=1)
    account_id: str = Field(min_length=1)
    outcome: BeaconHistoryOutcome
    restorable: bool
    recorded_at: datetime
    minimal_snapshot_reference: str | None = None
    reason: str | None = None
    counts_toward_active_limit: bool = False

    @model_validator(mode="after")
    def _validate_history_semantics(self) -> "BeaconHistoryEntry":
        if self.minimal_snapshot_reference is not None:
            if not self.minimal_snapshot_reference.strip():
                raise ValueError("minimal snapshot reference must not be blank")
        if self.reason is not None and not self.reason.strip():
            raise ValueError("reason must not be blank")

        if (
            self.outcome
            in {
                BeaconHistoryOutcome.HISTORY,
                BeaconHistoryOutcome.ARCHIVED,
                BeaconHistoryOutcome.DELETED,
                BeaconHistoryOutcome.PERMANENTLY_DELETED,
            }
            and self.counts_toward_active_limit
        ):
            raise ValueError("history, archived or deleted beacons do not count")

        if self.outcome is BeaconHistoryOutcome.PERMANENTLY_DELETED and self.restorable:
            raise ValueError("permanently deleted beacon cannot be restorable")

        return self


class BeaconActivationDecision(BaseModel):
    """Semantic activation decision without runtime side effects."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    beacon_id: str = Field(min_length=1)
    account_id: str = Field(min_length=1)
    access_tier: BeaconAccessTier
    status: BeaconDecisionStatus
    requested_interval_minutes: int = Field(gt=0)
    interval_floor_minutes: int = Field(gt=0)
    interval_step_minutes: int = Field(gt=0)
    active_beacon_limit: int = Field(gt=0)
    requested_country_wide: bool
    country_wide_allowed: bool
    city_required: bool
    requested_city: str | None = None
    selected_beacon_id: str | None = None
    expiry_outcomes: tuple[BeaconExpiryOutcome, ...] = Field(default_factory=tuple)
    reason_code: str = Field(min_length=1)
    reason: str = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_activation_semantics(self) -> "BeaconActivationDecision":
        if self.requested_city is not None and not self.requested_city.strip():
            raise ValueError("requested city must not be blank")

        if self.selected_beacon_id is not None and not self.selected_beacon_id.strip():
            raise ValueError("selected beacon id must not be blank")

        if self.access_tier is BeaconAccessTier.FREE:
            if self.active_beacon_limit != 1:
                raise ValueError("free active beacon limit must be 1")
            if self.interval_floor_minutes != 180 or self.interval_step_minutes != 180:
                raise ValueError("free interval floor and step must be 180 minutes")
            if self.country_wide_allowed:
                raise ValueError("free country-wide activation cannot be allowed")
            if self.city_required is not True:
                raise ValueError("free activation requires city selection")
            if self.status is BeaconDecisionStatus.ALLOWED and self.requested_country_wide:
                raise ValueError("free country-wide activation cannot be allowed")
            if self.status is BeaconDecisionStatus.ALLOWED and self.requested_city is None:
                raise ValueError("free activation requires a city when allowed")
        elif self.access_tier is BeaconAccessTier.BASIC:
            if self.active_beacon_limit != 5:
                raise ValueError("basic active beacon limit must be 5")
            if self.interval_floor_minutes != 5 or self.interval_step_minutes != 5:
                raise ValueError("basic interval floor and step must be 5 minutes")
            if self.country_wide_allowed is not True:
                raise ValueError("basic country-wide activation must be allowed")
        else:
            raise ValueError("unsupported access tier")

        if self.expiry_outcomes and self.selected_beacon_id is not None:
            raise ValueError("paid expiry semantics must not auto-select a beacon")

        if self.expiry_outcomes and self.status is BeaconDecisionStatus.ALLOWED:
            raise ValueError("paid expiry semantics must not become an allowed auto-choice")

        if self.requested_interval_minutes < self.interval_floor_minutes:
            raise ValueError("requested interval must meet the floor")
        interval_delta = self.requested_interval_minutes - self.interval_floor_minutes
        if interval_delta % self.interval_step_minutes != 0:
            raise ValueError("requested interval must respect the step")

        return self


class BeaconMutationDecision(BaseModel):
    """Semantic mutation decision with patch and concurrency rules."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    beacon_id: str = Field(min_length=1)
    account_id: str = Field(min_length=1)
    status: BeaconDecisionStatus
    patch_fields: tuple[str, ...] = Field(min_length=1)
    applied_fields: tuple[str, ...] = Field(min_length=1)
    same_field_concurrent_change: bool = False
    last_write_wins: bool = False
    current_revision_id: str = Field(min_length=1)
    new_revision_id: str = Field(min_length=1)
    current_configuration_replaced: bool = True
    retained_evidence_references: tuple[str, ...] = Field(default_factory=tuple)
    conflict_fields: tuple[str, ...] = Field(default_factory=tuple)
    reason_code: str = Field(min_length=1)
    reason: str = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_mutation_semantics(self) -> "BeaconMutationDecision":
        _reject_blank_values("patch_fields", self.patch_fields)
        _reject_blank_values("applied_fields", self.applied_fields)
        _reject_blank_values("retained_evidence_references", self.retained_evidence_references)
        _reject_blank_values("conflict_fields", self.conflict_fields)

        if not set(self.applied_fields).issubset(self.patch_fields):
            raise ValueError("mutation may apply only fields present in the command patch")

        if self.same_field_concurrent_change and not self.last_write_wins:
            raise ValueError("same-field concurrent change must use last-write-wins")

        if (
            self.status
            in {
                BeaconDecisionStatus.ALLOWED,
                BeaconDecisionStatus.REPLAYED,
            }
            and not self.current_configuration_replaced
        ):
            raise ValueError("successful mutation must replace current configuration")

        return self


class Beacon(BaseModel):
    """Semantic Beacon root record."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    beacon_id: str = Field(min_length=1)
    account_id: str = Field(min_length=1)
    naming: BeaconNamingMetadata
    source_url: BeaconSourceUrl
    current_configuration: BeaconCurrentConfiguration
    lifecycle_state: BeaconLifecycleState
    restorable: bool = True
    counts_toward_active_limit: bool = True
    history_entries: tuple[BeaconHistoryEntry, ...] = Field(default_factory=tuple)

    @model_validator(mode="after")
    def _validate_beacon_semantics(self) -> "Beacon":
        if self.current_configuration.beacon_id != self.beacon_id:
            raise ValueError("current configuration must remain isolated by beacon_id")
        if self.current_configuration.account_id != self.account_id:
            raise ValueError("current configuration must remain owned by the same account_id")
        if (
            self.lifecycle_state
            in {
                BeaconLifecycleState.ARCHIVED,
                BeaconLifecycleState.PERMANENTLY_DELETED,
            }
            and self.counts_toward_active_limit
        ):
            raise ValueError("archived or permanently deleted beacons do not count")
        if self.lifecycle_state is BeaconLifecycleState.PERMANENTLY_DELETED and self.restorable:
            raise ValueError("permanently deleted beacon cannot be restorable")
        return self


__all__: Final[tuple[str, ...]] = (
    "BeaconActionCausation",
    "BeaconActorContext",
    "BeaconActorKind",
    "Beacon",
    "BeaconAccessTier",
    "BeaconActivationDecision",
    "BeaconAuthorizationDecision",
    "BeaconAuthorizationOutcome",
    "BeaconCurrentConfiguration",
    "BeaconDecisionStatus",
    "BeaconExpiryOutcome",
    "BeaconFilterOverride",
    "BeaconHistoryEntry",
    "BeaconHistoryOutcome",
    "BeaconLifecycleState",
    "BeaconMutationDecision",
    "BeaconNameOrigin",
    "BeaconNamingMetadata",
    "BeaconOverrideStatus",
    "BeaconProtectedAction",
    "BeaconParserOutcomeStatus",
    "BeaconSourceUrl",
    "BeaconSystemActorClass",
    "BeaconOwnershipDecision",
    "ExtractedSearchConfigurationSnapshot",
)
