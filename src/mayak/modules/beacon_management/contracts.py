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
    UNSUPPORTED = "UNSUPPORTED"


class BeaconParserEvidenceSafetyClass(str, Enum):
    """Safety classification for opaque parser evidence references."""

    OPAQUE = "OPAQUE"
    RAW_PROVIDER_PAYLOAD = "RAW_PROVIDER_PAYLOAD"
    RAW_PROVIDER_PAYLOAD_AUTHORITY = "RAW_PROVIDER_PAYLOAD_AUTHORITY"
    RAW_HTML = "RAW_HTML"
    RAW_SEARCH_CORE = "RAW_SEARCH_CORE"
    RAW_CONTEXT = "RAW_CONTEXT"
    AMBIGUOUS = "AMBIGUOUS"
    UNSUPPORTED = "UNSUPPORTED"


class BeaconSnapshotAcceptanceOutcome(str, Enum):
    """Semantic acceptance outcomes for extracted snapshots."""

    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    BLOCKED = "BLOCKED"
    DEFERRED = "DEFERRED"
    REPLAYED = "REPLAYED"
    CONFLICT = "CONFLICT"
    UNSUPPORTED = "UNSUPPORTED"


class BeaconSnapshotRejectionReason(str, Enum):
    """Semantic rejection reasons for extracted snapshot acceptance decisions."""

    NON_CLEAN_PARSER_OUTCOME = "NON_CLEAN_PARSER_OUTCOME"
    MISSING_PARSER_EVIDENCE_REFERENCE = "MISSING_PARSER_EVIDENCE_REFERENCE"
    NON_OPAQUE_PARSER_EVIDENCE_REFERENCE = "NON_OPAQUE_PARSER_EVIDENCE_REFERENCE"
    AMBIGUOUS_PARSER_EVIDENCE = "AMBIGUOUS_PARSER_EVIDENCE"
    RAW_PROVIDER_PAYLOAD_AUTHORITY = "RAW_PROVIDER_PAYLOAD_AUTHORITY"
    RAW_HTML_SEARCH_CORE_CONTEXT_PAYLOAD = "RAW_HTML_SEARCH_CORE_CONTEXT_PAYLOAD"
    INVENTED_NUMERIC_ACCEPTANCE_THRESHOLD = "INVENTED_NUMERIC_ACCEPTANCE_THRESHOLD"
    FULL_PARSER_ADAPTER_IMPLEMENTATION_CLAIM = "FULL_PARSER_ADAPTER_IMPLEMENTATION_CLAIM"
    UNSUPPORTED_PARAMETERS_SILENTLY_ACCEPTED = "UNSUPPORTED_PARAMETERS_SILENTLY_ACCEPTED"
    UNSUPPORTED_PARSER_OUTCOME = "UNSUPPORTED_PARSER_OUTCOME"


class BeaconParserEvidenceReference(BaseModel):
    """Opaque parser evidence reference with a non-authoritative safety class."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    evidence_reference: str = Field(min_length=1)
    safety_class: BeaconParserEvidenceSafetyClass = BeaconParserEvidenceSafetyClass.OPAQUE
    raw_provider_payload_authority: bool = False

    @model_validator(mode="after")
    def _validate_parser_evidence_reference(self) -> "BeaconParserEvidenceReference":
        evidence_reference = self.evidence_reference.lower()
        if "<html" in evidence_reference or "</html" in evidence_reference:
            raise ValueError("parser evidence reference must not contain raw HTML payload text")
        if "searchcore" in evidence_reference:
            raise ValueError(
                "parser evidence reference must not contain raw searchCore payload text"
            )
        if "context=" in evidence_reference or "context{" in evidence_reference:
            raise ValueError("parser evidence reference must not contain raw context payload text")
        return self


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

        if self.outcome is BeaconAuthorizationOutcome.REQUIRES_VERIFIED_ACTOR:
            if self.actor_context.is_verified:
                raise ValueError("requires verified actor outcome cannot target a verified actor")

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
        if self.outcome is BeaconAuthorizationOutcome.REQUIRES_SCOPE:
            if self.server_role_scope_reference is not None:
                raise ValueError(
                    "requires scope outcome must not carry server role scope reference"
                )

        if self.outcome is BeaconAuthorizationOutcome.REQUIRES_AUDIT:
            if self.server_audit_reference is not None:
                raise ValueError("requires audit outcome must not carry audit reference")

        if self.protected_action in {
            BeaconProtectedAction.ADMIN_SUPPORT_READ,
            BeaconProtectedAction.ADMIN_SUPPORT_MUTATE,
        }:
            if self.outcome is BeaconAuthorizationOutcome.ALLOWED:
                if self.actor_context.actor_kind is not BeaconActorKind.ADMIN_SUPPORT:
                    raise ValueError("admin/support action requires an admin/support actor context")
                if not self.actor_context.is_verified:
                    raise ValueError("admin/support action requires verified actor context")
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
            elif self.action_causation is not None:
                raise ValueError(
                    "system lifecycle missing-causation outcome must not carry action causation"
                )

        return self


def _reject_blank_values(label: str, values: tuple[str, ...]) -> None:
    if any(not value.strip() for value in values):
        raise ValueError(f"{label} must not contain blank values")


def _validate_source_url_match(
    source_url: BeaconSourceUrl,
    current_configuration_source_url: BeaconSourceUrl,
) -> None:
    if source_url.submitted_url != current_configuration_source_url.submitted_url:
        raise ValueError("Beacon source URL must match current configuration source URL")

    if source_url.evidence_reference != current_configuration_source_url.evidence_reference:
        raise ValueError(
            "Beacon source URL evidence reference must match current configuration source URL"
        )

    if source_url.source_channel != current_configuration_source_url.source_channel:
        raise ValueError(
            "Beacon source URL source channel must not contradict current configuration"
        )

    if source_url.submitted_at != current_configuration_source_url.submitted_at:
        raise ValueError("Beacon source URL submitted_at must not contradict current configuration")

    if source_url.submitted_by_label != current_configuration_source_url.submitted_by_label:
        raise ValueError(
            "Beacon source URL submitted_by_label must not contradict current configuration"
        )


class BeaconSourceUrl(BaseModel):
    """User-submitted source URL preserved as evidence."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    submitted_url: str = Field(min_length=1)
    evidence_reference: str = Field(min_length=1)
    submitted_at: datetime | None = None
    source_channel: str = Field(default="user-submitted", min_length=1)
    submitted_by_label: str | None = None


class BeaconSourceUrlSafetyClassification(str, Enum):
    """Semantic safety classifications for source URL preparation."""

    PRESERVED = "PRESERVED"
    MALFORMED = "MALFORMED"
    BLOCKED = "BLOCKED"
    AMBIGUOUS = "AMBIGUOUS"
    UNSUPPORTED = "UNSUPPORTED"
    REWRITTEN = "REWRITTEN"


class BeaconSourceUrlPreparationOutcome(str, Enum):
    """Deterministic outcomes for source URL preparation semantics."""

    CREATED = "CREATED"
    REPLAYED = "REPLAYED"
    REJECTED = "REJECTED"
    BLOCKED = "BLOCKED"
    IDEMPOTENCY_MISMATCH = "IDEMPOTENCY_MISMATCH"
    UNSUPPORTED = "UNSUPPORTED"
    AMBIGUOUS = "AMBIGUOUS"


class BeaconSourceUrlFingerprintPolicy(BaseModel):
    """Opaque policy reference for fingerprint comparison and debug semantics."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    policy_reference: str = Field(min_length=1)
    comparison_reference: str | None = Field(default=None, min_length=1)
    idempotency_reference: str | None = Field(default=None, min_length=1)
    debug_reference: str | None = Field(default=None, min_length=1)
    authoritative_configuration_source: bool = False

    @model_validator(mode="after")
    def _validate_fingerprint_policy(self) -> "BeaconSourceUrlFingerprintPolicy":
        if self.authoritative_configuration_source:
            raise ValueError("fingerprint policy must not be authoritative configuration source")

        if (
            self.comparison_reference is None
            and self.idempotency_reference is None
            and self.debug_reference is None
        ):
            raise ValueError(
                "fingerprint policy must carry at least one opaque comparison or debug reference"
            )

        return self


class BeaconSourceUrlIdempotencyBasis(BaseModel):
    """Opaque idempotency basis for source URL preparation semantics."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    source_url_reference: str = Field(min_length=1)
    command_reference: str | None = Field(default=None, min_length=1)
    account_id: str | None = Field(default=None, min_length=1)
    beacon_id: str | None = Field(default=None, min_length=1)
    requested_beacon_id: str | None = Field(default=None, min_length=1)
    source_url_only_basis: bool = False

    @model_validator(mode="after")
    def _validate_idempotency_basis(self) -> "BeaconSourceUrlIdempotencyBasis":
        if self.source_url_only_basis:
            raise ValueError("source URL alone is not a valid idempotency basis")

        if (
            self.command_reference is None
            and self.account_id is None
            and self.beacon_id is None
            and self.requested_beacon_id is None
        ):
            raise ValueError("idempotency basis requires explicit command, account or beacon scope")

        return self


class BeaconPreparedSourceUrl(BaseModel):
    """Prepared source URL evidence that preserves the submitted URL."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    prepared_source_url_reference: str = Field(min_length=1)
    submitted_source_url: BeaconSourceUrl
    preserved_submitted_url: str = Field(min_length=1)
    safety_classification: BeaconSourceUrlSafetyClassification
    source_url_overwritten_by_snapshot: bool = False
    source_url_overwritten_by_override: bool = False
    source_url_rewritten: bool = False
    opaque_fingerprint_reference: str | None = Field(default=None, min_length=1)
    fingerprint_policy: BeaconSourceUrlFingerprintPolicy | None = None

    @model_validator(mode="after")
    def _validate_prepared_source_url(self) -> "BeaconPreparedSourceUrl":
        if self.preserved_submitted_url != self.submitted_source_url.submitted_url:
            raise ValueError("submitted source URL must not be rewritten")

        if self.source_url_overwritten_by_snapshot:
            raise ValueError("submitted source URL must not be overwritten by snapshot")

        if self.source_url_overwritten_by_override:
            raise ValueError("submitted source URL must not be overwritten by override")

        if self.source_url_rewritten:
            raise ValueError("submitted source URL must not be rewritten in prepared form")

        if self.opaque_fingerprint_reference is not None and self.fingerprint_policy is None:
            raise ValueError("opaque fingerprint reference requires captured policy")

        return self


class BeaconSourceUrlPreparationDecision(BaseModel):
    """Semantic preparation decision for a submitted source URL."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    decision_id: str = Field(min_length=1)
    account_id: str = Field(min_length=1)
    beacon_id: str | None = Field(default=None, min_length=1)
    requested_beacon_id: str | None = Field(default=None, min_length=1)
    submitted_source_url: BeaconSourceUrl
    prepared_source_url: BeaconPreparedSourceUrl
    outcome: BeaconSourceUrlPreparationOutcome
    safe_reason_code: str = Field(min_length=1)
    duplicate_source_url_blocking_policy: bool = False
    idempotency_basis: BeaconSourceUrlIdempotencyBasis
    source_url_is_unique_key: bool = False
    shell_command_text: str | None = Field(default=None, min_length=1)
    shell_interpolation_field: str | None = Field(default=None, min_length=1)
    tracking_params_ignored: bool = False
    tracking_policy_reference: str | None = Field(default=None, min_length=1)
    opaque_fingerprint_reference: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def _validate_preparation_decision(self) -> "BeaconSourceUrlPreparationDecision":
        if self.beacon_id is None and self.requested_beacon_id is None:
            raise ValueError("preparation decision requires beacon_id or requested_beacon_id")

        if self.duplicate_source_url_blocking_policy:
            raise ValueError("duplicate source URL must not be blocking by default")

        if self.source_url_is_unique_key:
            raise ValueError("source URL alone is not a unique key")

        submitted_url = self.submitted_source_url.submitted_url
        if self.prepared_source_url.submitted_source_url != self.submitted_source_url:
            raise ValueError("submitted source URL must be preserved in the prepared form")

        if self.prepared_source_url.preserved_submitted_url != submitted_url:
            raise ValueError("prepared source URL must preserve the submitted URL")

        if (
            self.prepared_source_url.safety_classification
            is BeaconSourceUrlSafetyClassification.MALFORMED
            and self.outcome
            in {
                BeaconSourceUrlPreparationOutcome.CREATED,
                BeaconSourceUrlPreparationOutcome.REPLAYED,
            }
        ):
            raise ValueError("malformed URL cannot be represented as created or replayed")

        if self.shell_command_text is not None and submitted_url in self.shell_command_text:
            raise ValueError("external URL must not be interpolated into shell command text")

        if self.shell_interpolation_field is not None:
            raise ValueError(
                "shell interpolation field must not represent external source URL interpolation"
            )

        if self.tracking_params_ignored and self.tracking_policy_reference is None:
            raise ValueError("tracking params may be ignored only with captured policy reference")

        if (
            self.opaque_fingerprint_reference is not None
            and self.prepared_source_url.opaque_fingerprint_reference
            != self.opaque_fingerprint_reference
        ):
            raise ValueError("opaque fingerprint reference must remain captured, not rewritten")

        if (
            self.opaque_fingerprint_reference is not None
            and self.prepared_source_url.fingerprint_policy is None
        ):
            raise ValueError("opaque fingerprint reference requires captured policy")

        return self


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
    parser_evidence_reference: BeaconParserEvidenceReference | None = None

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
            BeaconParserOutcomeStatus.UNSUPPORTED,
        }
        if self.accepted_as_clean and self.parser_outcome_status in unsafe_parser_outcomes:
            raise ValueError("unsafe parser outcome cannot become a clean accepted snapshot")
        if self.accepted_as_clean:
            if self.parser_outcome_status is not BeaconParserOutcomeStatus.CLEAN:
                raise ValueError("clean accepted snapshot requires clean parser outcome")
            if self.parser_evidence_reference is None:
                raise ValueError("clean accepted snapshot requires parser evidence reference")
            evidence_is_opaque = (
                self.parser_evidence_reference.safety_class
                is BeaconParserEvidenceSafetyClass.OPAQUE
            )
            if not evidence_is_opaque:
                raise ValueError("clean accepted snapshot requires non-ambiguous parser evidence")
        return self


class BeaconSnapshotAcceptanceDecision(BaseModel):
    """Semantic decision for accepting or rejecting an extracted parser snapshot."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    decision_id: str = Field(min_length=1)
    parser_outcome_status: BeaconParserOutcomeStatus
    parser_evidence_reference: BeaconParserEvidenceReference | None = None
    acceptance_outcome: BeaconSnapshotAcceptanceOutcome
    rejection_reason: BeaconSnapshotRejectionReason | None = None
    parser_adapter_evidence_gate_reference: str | None = Field(default=None, min_length=1)
    exact_acceptance_threshold_percent: int | None = Field(default=None, gt=0)
    unsupported_parameters: tuple[str, ...] = Field(default_factory=tuple)
    claims_full_parser_adapter_implementation_present: bool = False

    @model_validator(mode="after")
    def _validate_snapshot_acceptance_decision(
        self,
    ) -> "BeaconSnapshotAcceptanceDecision":
        _reject_blank_values("unsupported_parameters", self.unsupported_parameters)

        unsafe_parser_outcomes = {
            BeaconParserOutcomeStatus.MALFORMED,
            BeaconParserOutcomeStatus.INCOMPLETE,
            BeaconParserOutcomeStatus.CAPTCHA_AFFECTED,
            BeaconParserOutcomeStatus.BLOCKED,
            BeaconParserOutcomeStatus.ROUTE_FAILED,
            BeaconParserOutcomeStatus.AMBIGUOUS,
            BeaconParserOutcomeStatus.UNSUPPORTED,
        }

        if self.acceptance_outcome is BeaconSnapshotAcceptanceOutcome.ACCEPTED:
            if self.parser_outcome_status in unsafe_parser_outcomes:
                raise ValueError("unsafe parser outcome cannot become an accepted snapshot")
            if self.parser_outcome_status is not BeaconParserOutcomeStatus.CLEAN:
                raise ValueError("accepted snapshot requires clean parser outcome")
            if self.parser_evidence_reference is None:
                raise ValueError("accepted snapshot requires parser evidence reference")
            evidence_is_opaque = (
                self.parser_evidence_reference.safety_class
                is BeaconParserEvidenceSafetyClass.OPAQUE
            )
            if not evidence_is_opaque:
                raise ValueError("accepted snapshot requires non-ambiguous parser evidence")
            if self.parser_evidence_reference.raw_provider_payload_authority:
                raise ValueError("raw provider payload is not public contract authority")
            if self.unsupported_parameters:
                raise ValueError("unsupported parameters cannot be silently accepted")

        if self.claims_full_parser_adapter_implementation_present:
            raise ValueError("Beacon Management must not claim full Parser Adapter implementation")

        if self.exact_acceptance_threshold_percent is not None and (
            self.parser_adapter_evidence_gate_reference is None
        ):
            raise ValueError(
                "invented numeric acceptance threshold requires explicit parser adapter "
                "evidence gate"
            )

        if self.parser_evidence_reference is not None:
            if (
                self.parser_evidence_reference.safety_class
                in {
                    BeaconParserEvidenceSafetyClass.RAW_PROVIDER_PAYLOAD,
                    BeaconParserEvidenceSafetyClass.RAW_PROVIDER_PAYLOAD_AUTHORITY,
                    BeaconParserEvidenceSafetyClass.RAW_HTML,
                    BeaconParserEvidenceSafetyClass.RAW_SEARCH_CORE,
                    BeaconParserEvidenceSafetyClass.RAW_CONTEXT,
                    BeaconParserEvidenceSafetyClass.AMBIGUOUS,
                    BeaconParserEvidenceSafetyClass.UNSUPPORTED,
                }
                and self.acceptance_outcome is BeaconSnapshotAcceptanceOutcome.ACCEPTED
            ):
                raise ValueError("raw or ambiguous parser evidence cannot become accepted")

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


class BeaconOverrideFieldSupportStatus(str, Enum):
    """Semantic support classification for a structured override field."""

    SUPPORTED = "SUPPORTED"
    UNSUPPORTED = "UNSUPPORTED"
    UNCERTAIN = "UNCERTAIN"
    AMBIGUOUS = "AMBIGUOUS"


class BeaconOverrideApplicationOutcome(str, Enum):
    """Semantic application outcomes for a structured override field."""

    APPLIED = "APPLIED"
    REJECTED = "REJECTED"
    BLOCKED = "BLOCKED"
    CONFLICT = "CONFLICT"
    REPLAYED = "REPLAYED"


class BeaconOverrideRejectionReason(str, Enum):
    """Semantic rejection reasons for structured override application."""

    UNSUPPORTED_FIELD = "UNSUPPORTED_FIELD"
    UNCERTAIN_EVIDENCE = "UNCERTAIN_EVIDENCE"
    AMBIGUOUS_EVIDENCE = "AMBIGUOUS_EVIDENCE"
    SOURCE_URL_OVERRIDE = "SOURCE_URL_OVERRIDE"
    MULTIVALUE_COLLAPSE = "MULTIVALUE_COLLAPSE"
    INVALID_SOURCE_SNAPSHOT = "INVALID_SOURCE_SNAPSHOT"
    RAW_PROVIDER_PAYLOAD_AUTHORITY = "RAW_PROVIDER_PAYLOAD_AUTHORITY"
    TARGET_STATE_GONE = "TARGET_STATE_GONE"


class BeaconEffectiveConfigurationRejectionReason(str, Enum):
    """Semantic rejection reasons for effective configuration assembly."""

    NON_ACCEPTED_SNAPSHOT = "NON_ACCEPTED_SNAPSHOT"
    UNSAFE_SNAPSHOT = "UNSAFE_SNAPSHOT"
    RAW_PROVIDER_PAYLOAD_AUTHORITY = "RAW_PROVIDER_PAYLOAD_AUTHORITY"
    SOURCE_URL_OVERWRITE_ATTEMPT = "SOURCE_URL_OVERWRITE_ATTEMPT"
    UNSUPPORTED_FIELD_APPLIED = "UNSUPPORTED_FIELD_APPLIED"
    UNCERTAIN_EVIDENCE_APPLIED = "UNCERTAIN_EVIDENCE_APPLIED"
    AMBIGUOUS_EVIDENCE_APPLIED = "AMBIGUOUS_EVIDENCE_APPLIED"
    MULTIVALUE_COLLAPSE = "MULTIVALUE_COLLAPSE"
    UNSUPPORTED_PARAMETER_SILENTLY_CHANGED = "UNSUPPORTED_PARAMETER_SILENTLY_CHANGED"


class BeaconPatchSaveRejectionReason(str, Enum):
    """Semantic rejection reasons for patch-based save semantics."""

    STALE_FULL_FORM_OVERWRITE = "STALE_FULL_FORM_OVERWRITE"
    CHANGE_OUTSIDE_PATCH = "CHANGE_OUTSIDE_PATCH"
    RUNTIME_PERSISTENCE_IMPLEMENTATION_CLAIM = "RUNTIME_PERSISTENCE_IMPLEMENTATION_CLAIM"
    UNAUTHORIZED_ACTOR = "UNAUTHORIZED_ACTOR"
    TARGET_STATE_GONE = "TARGET_STATE_GONE"
    UNSUPPORTED_FIELD = "UNSUPPORTED_FIELD"
    INVALID_SOURCE_OR_SNAPSHOT = "INVALID_SOURCE_OR_SNAPSHOT"
    ENTITLEMENT_DENIED = "ENTITLEMENT_DENIED"
    REQUIRED_CONFIRMATION_MISSING = "REQUIRED_CONFIRMATION_MISSING"


class BeaconOverridePatchOperation(BaseModel):
    """Structured override application primitive with explicit field-scoped evidence."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    field_name: str = Field(min_length=1)
    support_status: BeaconOverrideFieldSupportStatus
    outcome: BeaconOverrideApplicationOutcome
    requested_values: tuple[str, ...] = Field(min_length=1)
    applied_values: tuple[str, ...] | None = None
    parser_filter_evidence_reference: str = Field(min_length=1)
    override_evidence_reference: str = Field(min_length=1)
    rejection_reason: BeaconOverrideRejectionReason | None = None

    @model_validator(mode="after")
    def _validate_override_patch_operation(self) -> "BeaconOverridePatchOperation":
        _reject_blank_values("requested_values", self.requested_values)
        if self.applied_values is not None:
            _reject_blank_values("applied_values", self.applied_values)

        if (
            self.field_name == "source_url"
            and self.outcome is BeaconOverrideApplicationOutcome.APPLIED
        ):
            raise ValueError("source URL override must not be applied")

        if self.support_status is BeaconOverrideFieldSupportStatus.UNSUPPORTED and self.outcome in {
            BeaconOverrideApplicationOutcome.APPLIED,
            BeaconOverrideApplicationOutcome.REPLAYED,
        }:
            raise ValueError("unsupported field cannot be applied")

        if self.support_status in {
            BeaconOverrideFieldSupportStatus.UNCERTAIN,
            BeaconOverrideFieldSupportStatus.AMBIGUOUS,
        } and self.outcome in {
            BeaconOverrideApplicationOutcome.APPLIED,
            BeaconOverrideApplicationOutcome.REPLAYED,
        }:
            raise ValueError("uncertain or ambiguous evidence cannot be silently applied")

        if self.outcome is BeaconOverrideApplicationOutcome.APPLIED:
            if self.applied_values is None:
                raise ValueError("applied override must match requested values")
            if self.applied_values != self.requested_values:
                raise ValueError("applied override must match requested values")
        elif self.applied_values is not None:
            raise ValueError("non-applied override must not carry applied values")

        if (
            self.rejection_reason is not None
            and self.outcome is BeaconOverrideApplicationOutcome.APPLIED
        ):
            raise ValueError("applied override must not carry rejection reason")

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


class BeaconEffectiveConfigurationDecision(BaseModel):
    """Semantic effective-configuration assembly decision."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    decision_id: str = Field(min_length=1)
    beacon_id: str = Field(min_length=1)
    account_id: str = Field(min_length=1)
    source_url: BeaconSourceUrl
    accepted_snapshot: ExtractedSearchConfigurationSnapshot
    override_operations: tuple[BeaconOverridePatchOperation, ...] = Field(default_factory=tuple)
    status: BeaconDecisionStatus
    effective_configuration_reference: str = Field(min_length=1)
    authoritative_state_reference: str = Field(min_length=1)
    source_url_overwritten_by_snapshot: bool = False
    source_url_overwritten_by_override: bool = False
    rejection_reason: BeaconEffectiveConfigurationRejectionReason | None = None

    @model_validator(mode="after")
    def _validate_effective_configuration_semantics(
        self,
    ) -> "BeaconEffectiveConfigurationDecision":
        if self.status in {BeaconDecisionStatus.ALLOWED, BeaconDecisionStatus.REPLAYED}:
            if self.accepted_snapshot.parser_evidence_reference is not None and (
                self.accepted_snapshot.parser_evidence_reference.raw_provider_payload_authority
            ):
                raise ValueError(
                    "raw provider payload must not become effective configuration authority"
                )

            if not self.accepted_snapshot.accepted_as_clean:
                raise ValueError("effective configuration requires accepted snapshot")

            if self.accepted_snapshot.parser_evidence_reference is None:
                raise ValueError("accepted snapshot requires parser evidence reference")

            if self.source_url_overwritten_by_snapshot:
                raise ValueError("source URL must not be overwritten by snapshot")

            if self.source_url_overwritten_by_override:
                raise ValueError("source URL must not be overwritten by override")

            for override_operation in self.override_operations:
                if (
                    override_operation.support_status
                    is not BeaconOverrideFieldSupportStatus.SUPPORTED
                ):
                    raise ValueError(
                        "effective configuration cannot silently apply unsupported evidence"
                    )
                if override_operation.outcome is not BeaconOverrideApplicationOutcome.APPLIED:
                    raise ValueError("effective configuration requires applied override operations")
                if override_operation.field_name == "source_url":
                    raise ValueError("source URL override must not be overwritten")
                if override_operation.applied_values != override_operation.requested_values:
                    raise ValueError(
                        "effective configuration override values must match requested values"
                    )

        if self.rejection_reason is not None and self.status in {
            BeaconDecisionStatus.ALLOWED,
            BeaconDecisionStatus.REPLAYED,
        }:
            raise ValueError("effective configuration decision must not carry rejection reason")

        return self


class BeaconPatchSaveDecision(BaseModel):
    """Semantic patch-based save decision for current Beacon configuration."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    decision_id: str = Field(min_length=1)
    beacon_id: str = Field(min_length=1)
    account_id: str = Field(min_length=1)
    status: BeaconDecisionStatus
    patch_fields: tuple[str, ...] = Field(min_length=1)
    applied_fields: tuple[str, ...] = Field(min_length=1)
    preserved_fields: tuple[str, ...] = Field(default_factory=tuple)
    same_field_concurrent_change: bool = False
    last_write_wins: bool = False
    different_field_updates_merge: bool = False
    stale_full_form_overwrite: bool = False
    authoritative_state_reference: str | None = Field(default=None, min_length=1)
    claims_db_repository_runtime_persistence_implementation: bool = False
    rejection_reason: BeaconPatchSaveRejectionReason | None = None

    @model_validator(mode="after")
    def _validate_patch_save_semantics(self) -> "BeaconPatchSaveDecision":
        _reject_blank_values("patch_fields", self.patch_fields)
        _reject_blank_values("applied_fields", self.applied_fields)
        _reject_blank_values("preserved_fields", self.preserved_fields)

        if not set(self.applied_fields).issubset(self.patch_fields):
            raise ValueError("patch save may change only fields present in patch")

        if set(self.preserved_fields) & set(self.patch_fields):
            raise ValueError("absent fields must remain outside the patch")

        if self.same_field_concurrent_change and not self.last_write_wins:
            raise ValueError("same-field concurrent change must use last-write-wins")

        if self.stale_full_form_overwrite and self.status in {
            BeaconDecisionStatus.ALLOWED,
            BeaconDecisionStatus.REPLAYED,
        }:
            raise ValueError("stale full-form overwrite is forbidden")

        if self.claims_db_repository_runtime_persistence_implementation:
            raise ValueError(
                "patch save decision must not claim database or runtime persistence implementation"
            )

        if self.status in {BeaconDecisionStatus.ALLOWED, BeaconDecisionStatus.REPLAYED}:
            if self.authoritative_state_reference is None:
                raise ValueError("post-save state must be read from authoritative storage")

        if self.rejection_reason is not None and self.status in {
            BeaconDecisionStatus.ALLOWED,
            BeaconDecisionStatus.REPLAYED,
        }:
            raise ValueError("successful patch save decision must not carry rejection reason")

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
        _validate_source_url_match(self.source_url, self.current_configuration.source_url)
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
    "BeaconEffectiveConfigurationDecision",
    "BeaconEffectiveConfigurationRejectionReason",
    "BeaconExpiryOutcome",
    "BeaconFilterOverride",
    "BeaconHistoryEntry",
    "BeaconHistoryOutcome",
    "BeaconLifecycleState",
    "BeaconMutationDecision",
    "BeaconNameOrigin",
    "BeaconNamingMetadata",
    "BeaconOverrideApplicationOutcome",
    "BeaconOverrideFieldSupportStatus",
    "BeaconOverridePatchOperation",
    "BeaconOverrideRejectionReason",
    "BeaconOverrideStatus",
    "BeaconPatchSaveDecision",
    "BeaconPatchSaveRejectionReason",
    "BeaconProtectedAction",
    "BeaconParserOutcomeStatus",
    "BeaconParserEvidenceReference",
    "BeaconParserEvidenceSafetyClass",
    "BeaconPreparedSourceUrl",
    "BeaconSourceUrl",
    "BeaconSourceUrlFingerprintPolicy",
    "BeaconSourceUrlIdempotencyBasis",
    "BeaconSourceUrlPreparationDecision",
    "BeaconSourceUrlPreparationOutcome",
    "BeaconSourceUrlSafetyClassification",
    "BeaconSystemActorClass",
    "BeaconOwnershipDecision",
    "ExtractedSearchConfigurationSnapshot",
    "BeaconSnapshotAcceptanceDecision",
    "BeaconSnapshotAcceptanceOutcome",
    "BeaconSnapshotRejectionReason",
)
