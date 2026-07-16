from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .eligibility import (
    NotificationBeaconLifecycleStatus,
    NotificationChannelClass,
    NotificationChannelGateDecision,
    NotificationChannelGateStatus,
    NotificationEligibilityDecision,
    NotificationEligibilityStatus,
    NotificationEntitlementStatus,
)
from .read_model import NotificationReadAudience

ND13_TASK_ID = "MAYAK-ND-13-SECURITY-PRIVACY-SUPPRESSION-20260716-008"


class NotificationSecurityPrivacyAuthority(str, Enum):
    NOTIFICATION_DELIVERY_SERVER = "NOTIFICATION_DELIVERY_SERVER"


class NotificationProtectedAction(str, Enum):
    PROTECTED_READ = "PROTECTED_READ"
    OUTBOX_EFFECT = "OUTBOX_EFFECT"
    CHANNEL_DELIVERY = "CHANNEL_DELIVERY"


class NotificationIdentityScopeStatus(str, Enum):
    VERIFIED = "VERIFIED"
    UNAUTHORIZED = "UNAUTHORIZED"
    AMBIGUOUS = "AMBIGUOUS"


class NotificationContentSafetyStatus(str, Enum):
    EMPTY = "EMPTY"
    APPROVED_SAFE_REFERENCES = "APPROVED_SAFE_REFERENCES"
    UNSAFE_OR_UNAPPROVED = "UNSAFE_OR_UNAPPROVED"
    AMBIGUOUS = "AMBIGUOUS"


class NotificationSecurityDecisionStatus(str, Enum):
    AUTHORIZED_READ = "AUTHORIZED_READ"
    AUTHORIZED_EFFECT = "AUTHORIZED_EFFECT"
    AUTHORIZED_RECOVERY_GRACE = "AUTHORIZED_RECOVERY_GRACE"
    SUPPRESSED_BY_USER = "SUPPRESSED_BY_USER"
    BLOCKED_NOT_AUTHORIZED_OR_NOT_FOUND = "BLOCKED_NOT_AUTHORIZED_OR_NOT_FOUND"
    BLOCKED_AMBIGUOUS = "BLOCKED_AMBIGUOUS"
    BLOCKED_TARGET_UNVERIFIED = "BLOCKED_TARGET_UNVERIFIED"
    BLOCKED_UNSAFE_CONTENT = "BLOCKED_UNSAFE_CONTENT"
    BLOCKED_EVIDENCE_CONFLICT = "BLOCKED_EVIDENCE_CONFLICT"


class NotificationSecurityPublicErrorClass(str, Enum):
    NONE = "NONE"
    NOT_AUTHORIZED_OR_NOT_FOUND = "NOT_AUTHORIZED_OR_NOT_FOUND"
    REQUEST_BLOCKED = "REQUEST_BLOCKED"


def _require_text(value: object, field_name: str) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-blank string")
    return value


def _require_optional_text(value: object, field_name: str) -> str | None:
    if value is None:
        return None
    return _require_text(value, field_name)


def _require_bool(value: object, field_name: str) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _require_exact_enum(value: object, enum_type: type[Enum], field_name: str) -> Enum:
    if type(value) is not enum_type:
        raise ValueError(f"{field_name} must be {enum_type.__name__}")
    return value


def _require_text_tuple(
    value: object,
    field_name: str,
    *,
    allow_empty: bool,
    unique: bool,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value and not allow_empty:
        raise ValueError(f"{field_name} must not be empty")
    validated = tuple(_require_text(item, field_name) for item in value)
    if unique and len(set(validated)) != len(validated):
        raise ValueError(f"{field_name} must not contain duplicate values")
    return validated


def _combined_evidence_reference_ids(*tuples: tuple[str, ...]) -> tuple[str, ...]:
    combined: tuple[str, ...] = ()
    for items in tuples:
        combined += items
    return combined


@dataclass(frozen=True, slots=True)
class NotificationSecurityAuthorizationScope:
    scope_id: str
    audience: NotificationReadAudience
    identity_status: NotificationIdentityScopeStatus
    authorized: bool
    principal_reference_id: str
    authorized_account_ids: tuple[str, ...]
    authorized_beacon_ids: tuple[str, ...]
    authorization_reference_id: str
    evidence_reference_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_text(self.scope_id, "scope_id")
        _require_exact_enum(self.audience, NotificationReadAudience, "audience")
        _require_exact_enum(
            self.identity_status,
            NotificationIdentityScopeStatus,
            "identity_status",
        )
        _require_bool(self.authorized, "authorized")
        _require_text(self.principal_reference_id, "principal_reference_id")
        _require_text_tuple(
            self.authorized_account_ids,
            "authorized_account_ids",
            allow_empty=True,
            unique=True,
        )
        _require_text_tuple(
            self.authorized_beacon_ids,
            "authorized_beacon_ids",
            allow_empty=True,
            unique=True,
        )
        _require_text(self.authorization_reference_id, "authorization_reference_id")
        _require_text_tuple(
            self.evidence_reference_ids,
            "evidence_reference_ids",
            allow_empty=True,
            unique=True,
        )

        if self.identity_status is NotificationIdentityScopeStatus.VERIFIED:
            if not self.authorized:
                raise ValueError("verified identity scope must be authorized")
            if not self.authorized_account_ids:
                raise ValueError("verified identity scope requires an account scope")
            if not self.authorization_reference_id:
                raise ValueError("verified identity scope requires an authorization reference")
            return

        if self.authorized:
            raise ValueError("unverified identity scope must not be authorized")
        if self.authorized_account_ids or self.authorized_beacon_ids:
            raise ValueError("unverified identity scope must not carry authorized references")


@dataclass(frozen=True, slots=True)
class NotificationSafeContentScope:
    content_scope_id: str
    safety_status: NotificationContentSafetyStatus
    safe_listing_reference_ids: tuple[str, ...]
    approved_listing_reference_ids: tuple[str, ...]
    evidence_reference_ids: tuple[str, ...]
    fetch_authorized: bool
    enrichment_authorized: bool
    provider_rendering_authorized: bool

    def __post_init__(self) -> None:
        _require_text(self.content_scope_id, "content_scope_id")
        _require_exact_enum(
            self.safety_status,
            NotificationContentSafetyStatus,
            "safety_status",
        )
        safe_listing_reference_ids = _require_text_tuple(
            self.safe_listing_reference_ids,
            "safe_listing_reference_ids",
            allow_empty=True,
            unique=True,
        )
        approved_listing_reference_ids = _require_text_tuple(
            self.approved_listing_reference_ids,
            "approved_listing_reference_ids",
            allow_empty=True,
            unique=True,
        )
        _require_text_tuple(
            self.evidence_reference_ids,
            "evidence_reference_ids",
            allow_empty=True,
            unique=True,
        )
        if _require_bool(self.fetch_authorized, "fetch_authorized"):
            raise ValueError("fetch_authorized must be False")
        if _require_bool(self.enrichment_authorized, "enrichment_authorized"):
            raise ValueError("enrichment_authorized must be False")
        if _require_bool(self.provider_rendering_authorized, "provider_rendering_authorized"):
            raise ValueError("provider_rendering_authorized must be False")

        if self.safety_status is NotificationContentSafetyStatus.EMPTY:
            if safe_listing_reference_ids or approved_listing_reference_ids:
                raise ValueError("empty content scope must not carry listing references")
            return

        if self.safety_status is NotificationContentSafetyStatus.APPROVED_SAFE_REFERENCES:
            if not safe_listing_reference_ids:
                raise ValueError("approved content scope requires safe listing references")
            if not approved_listing_reference_ids:
                raise ValueError("approved content scope requires approved listing references")
            for safe_reference_id in safe_listing_reference_ids:
                if safe_reference_id not in approved_listing_reference_ids:
                    raise ValueError("safe listing references must be approved")


@dataclass(frozen=True, slots=True)
class NotificationHistoricalEvidenceSnapshot:
    snapshot_id: str
    account_id: str
    beacon_id: str | None
    entitlement_decision_reference_id: str | None
    beacon_lifecycle_reference_id: str | None
    recovery_obligation_reference_id: str | None
    evidence_reference_ids: tuple[str, ...]
    mutation_authorized: bool

    def __post_init__(self) -> None:
        _require_text(self.snapshot_id, "snapshot_id")
        _require_text(self.account_id, "account_id")
        _require_optional_text(self.beacon_id, "beacon_id")
        _require_optional_text(
            self.entitlement_decision_reference_id,
            "entitlement_decision_reference_id",
        )
        _require_optional_text(
            self.beacon_lifecycle_reference_id,
            "beacon_lifecycle_reference_id",
        )
        _require_optional_text(
            self.recovery_obligation_reference_id,
            "recovery_obligation_reference_id",
        )
        _require_text_tuple(
            self.evidence_reference_ids,
            "evidence_reference_ids",
            allow_empty=True,
            unique=True,
        )
        if _require_bool(self.mutation_authorized, "mutation_authorized"):
            raise ValueError("historical evidence snapshot must not authorize mutation")


@dataclass(frozen=True, slots=True)
class NotificationSecurityPrivacyDecision:
    decision_id: str
    authority: NotificationSecurityPrivacyAuthority
    action: NotificationProtectedAction
    status: NotificationSecurityDecisionStatus
    public_error_class: NotificationSecurityPublicErrorClass
    authorization_scope_id: str
    account_id: str | None
    beacon_id: str | None
    eligibility_decision_id: str | None
    channel_class: NotificationChannelClass | None
    target_reference_id: str | None
    safe_listing_reference_ids: tuple[str, ...]
    historical_evidence_snapshot: NotificationHistoricalEvidenceSnapshot | None
    protected_read_authorized: bool
    outbox_effect_authorized: bool
    channel_delivery_authorized: bool
    recovery_grace_applied: bool
    suppressed_by_user: bool
    historical_entitlement_evidence_rewritten: bool
    historical_beacon_evidence_rewritten: bool
    historical_evidence_mutation_authorized: bool
    provider_mapping_authorized: bool
    provider_execution_authorized: bool
    read_tracking_authorized: bool
    click_tracking_authorized: bool
    retention_authorized: bool
    reason_codes: tuple[str, ...]
    evidence_reference_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_text(self.decision_id, "decision_id")
        _require_exact_enum(
            self.authority,
            NotificationSecurityPrivacyAuthority,
            "authority",
        )
        _require_exact_enum(self.action, NotificationProtectedAction, "action")
        _require_exact_enum(self.status, NotificationSecurityDecisionStatus, "status")
        _require_exact_enum(
            self.public_error_class,
            NotificationSecurityPublicErrorClass,
            "public_error_class",
        )
        _require_text(self.authorization_scope_id, "authorization_scope_id")
        _require_optional_text(self.account_id, "account_id")
        _require_optional_text(self.beacon_id, "beacon_id")
        _require_optional_text(self.eligibility_decision_id, "eligibility_decision_id")
        if self.channel_class is not None:
            _require_exact_enum(self.channel_class, NotificationChannelClass, "channel_class")
        _require_optional_text(self.target_reference_id, "target_reference_id")
        _require_text_tuple(
            self.safe_listing_reference_ids,
            "safe_listing_reference_ids",
            allow_empty=True,
            unique=True,
        )
        if self.historical_evidence_snapshot is not None:
            if (
                type(self.historical_evidence_snapshot)
                is not NotificationHistoricalEvidenceSnapshot
            ):
                raise ValueError(
                    "historical_evidence_snapshot must be NotificationHistoricalEvidenceSnapshot"
                )
        _require_bool(self.protected_read_authorized, "protected_read_authorized")
        _require_bool(self.outbox_effect_authorized, "outbox_effect_authorized")
        _require_bool(self.channel_delivery_authorized, "channel_delivery_authorized")
        _require_bool(self.recovery_grace_applied, "recovery_grace_applied")
        _require_bool(self.suppressed_by_user, "suppressed_by_user")
        if _require_bool(
            self.historical_entitlement_evidence_rewritten,
            "historical_entitlement_evidence_rewritten",
        ):
            raise ValueError("historical entitlement evidence must not be rewritten")
        if _require_bool(
            self.historical_beacon_evidence_rewritten,
            "historical_beacon_evidence_rewritten",
        ):
            raise ValueError("historical beacon evidence must not be rewritten")
        if _require_bool(
            self.historical_evidence_mutation_authorized,
            "historical_evidence_mutation_authorized",
        ):
            raise ValueError("historical evidence mutation must not be authorized")
        if _require_bool(self.provider_mapping_authorized, "provider_mapping_authorized"):
            raise ValueError("provider mapping must not be authorized")
        if _require_bool(self.provider_execution_authorized, "provider_execution_authorized"):
            raise ValueError("provider execution must not be authorized")
        if _require_bool(self.read_tracking_authorized, "read_tracking_authorized"):
            raise ValueError("read tracking must not be authorized")
        if _require_bool(self.click_tracking_authorized, "click_tracking_authorized"):
            raise ValueError("click tracking must not be authorized")
        if _require_bool(self.retention_authorized, "retention_authorized"):
            raise ValueError("retention must not be authorized")
        _require_text_tuple(self.reason_codes, "reason_codes", allow_empty=False, unique=False)
        _require_text_tuple(
            self.evidence_reference_ids,
            "evidence_reference_ids",
            allow_empty=True,
            unique=False,
        )

        if self.status is NotificationSecurityDecisionStatus.BLOCKED_NOT_AUTHORIZED_OR_NOT_FOUND:
            if (
                self.public_error_class
                is not NotificationSecurityPublicErrorClass.NOT_AUTHORIZED_OR_NOT_FOUND
            ):
                raise ValueError("authorization failure must use the not-authorized error class")
            if self.historical_evidence_snapshot is not None:
                raise ValueError("authorization failure must not expose historical evidence")
            if any(
                (
                    self.account_id is not None,
                    self.beacon_id is not None,
                    self.eligibility_decision_id is not None,
                    self.channel_class is not None,
                    self.target_reference_id is not None,
                    bool(self.safe_listing_reference_ids),
                    self.protected_read_authorized,
                    self.outbox_effect_authorized,
                    self.channel_delivery_authorized,
                    self.recovery_grace_applied,
                    self.suppressed_by_user,
                )
            ):
                raise ValueError("authorization failure must not expose protected fields")
            return

        if self.public_error_class is NotificationSecurityPublicErrorClass.NONE:
            if self.status not in (
                NotificationSecurityDecisionStatus.AUTHORIZED_READ,
                NotificationSecurityDecisionStatus.AUTHORIZED_EFFECT,
                NotificationSecurityDecisionStatus.AUTHORIZED_RECOVERY_GRACE,
            ):
                raise ValueError("only authorized decisions may use the NONE error class")
        else:
            if self.status in (
                NotificationSecurityDecisionStatus.AUTHORIZED_READ,
                NotificationSecurityDecisionStatus.AUTHORIZED_EFFECT,
                NotificationSecurityDecisionStatus.AUTHORIZED_RECOVERY_GRACE,
            ):
                raise ValueError("authorized decisions must not expose a blocking error class")

        if self.status is NotificationSecurityDecisionStatus.AUTHORIZED_READ:
            if self.action is not NotificationProtectedAction.PROTECTED_READ:
                raise ValueError("authorized read decisions must use PROTECTED_READ")
            if not self.protected_read_authorized:
                raise ValueError("authorized read decisions must authorize protected read")
            if any(
                (
                    self.outbox_effect_authorized,
                    self.channel_delivery_authorized,
                    self.recovery_grace_applied,
                    self.suppressed_by_user,
                    self.target_reference_id is not None,
                    self.eligibility_decision_id is not None,
                )
            ):
                raise ValueError("authorized read decisions must not expose other effects")
            if self.channel_class is not NotificationChannelClass.WEB_STATUS_READ_MODEL:
                raise ValueError("authorized read decisions must use the read-model channel")
        elif self.status is NotificationSecurityDecisionStatus.AUTHORIZED_EFFECT:
            if self.action not in (
                NotificationProtectedAction.OUTBOX_EFFECT,
                NotificationProtectedAction.CHANNEL_DELIVERY,
            ):
                raise ValueError("authorized effect decisions must use a delivery action")
            if self.action is NotificationProtectedAction.OUTBOX_EFFECT:
                if not self.outbox_effect_authorized or self.channel_delivery_authorized:
                    raise ValueError("outbox effect decisions must authorize only the outbox")
                if self.channel_class is not None or self.target_reference_id is not None:
                    raise ValueError("outbox effect decisions must not expose a target reference")
            else:
                if not self.channel_delivery_authorized or self.outbox_effect_authorized:
                    raise ValueError("channel effect decisions must authorize only delivery")
                if self.channel_class is None or self.target_reference_id is None:
                    raise ValueError("channel effect decisions must carry a verified target")
                if self.channel_class is NotificationChannelClass.WEB_STATUS_READ_MODEL:
                    raise ValueError("channel effect decisions must use a push channel")
            if any(
                (
                    self.protected_read_authorized,
                    self.suppressed_by_user,
                    self.recovery_grace_applied,
                    self.eligibility_decision_id is None,
                )
            ):
                raise ValueError("authorized effect decisions must stay provider-neutral")
        elif self.status is NotificationSecurityDecisionStatus.AUTHORIZED_RECOVERY_GRACE:
            if self.action not in (
                NotificationProtectedAction.OUTBOX_EFFECT,
                NotificationProtectedAction.CHANNEL_DELIVERY,
            ):
                raise ValueError("recovery-grace decisions must use a delivery action")
            if not self.recovery_grace_applied:
                raise ValueError("recovery-grace decisions must mark grace as applied")
            if not (self.outbox_effect_authorized or self.channel_delivery_authorized):
                raise ValueError("recovery-grace decisions must authorize an effect")
            if self.action is NotificationProtectedAction.OUTBOX_EFFECT:
                if self.outbox_effect_authorized is not True or self.channel_delivery_authorized:
                    raise ValueError("outbox recovery grace must authorize only the outbox effect")
                if self.channel_class is not None or self.target_reference_id is not None:
                    raise ValueError("outbox recovery grace must not expose a target reference")
            else:
                if self.channel_delivery_authorized is not True or self.outbox_effect_authorized:
                    raise ValueError(
                        "channel recovery grace must authorize only the channel delivery"
                    )
                if self.channel_class is None or self.target_reference_id is None:
                    raise ValueError("channel recovery grace must carry a verified target")
                if self.channel_class is NotificationChannelClass.WEB_STATUS_READ_MODEL:
                    raise ValueError("channel recovery grace must use a push channel")
        elif self.status is NotificationSecurityDecisionStatus.SUPPRESSED_BY_USER:
            if self.public_error_class is not NotificationSecurityPublicErrorClass.REQUEST_BLOCKED:
                raise ValueError("suppression must use the blocked request error class")
            if not self.suppressed_by_user:
                raise ValueError("suppression decisions must mark the user suppression")
            if any(
                (
                    self.protected_read_authorized,
                    self.outbox_effect_authorized,
                    self.channel_delivery_authorized,
                    self.recovery_grace_applied,
                    self.target_reference_id is not None,
                )
            ):
                raise ValueError("suppression decisions must not authorize effects")
        else:
            if self.public_error_class is not NotificationSecurityPublicErrorClass.REQUEST_BLOCKED:
                raise ValueError("blocked decisions must use the blocked request error class")
            if any(
                (
                    self.protected_read_authorized,
                    self.outbox_effect_authorized,
                    self.channel_delivery_authorized,
                    self.recovery_grace_applied,
                    self.suppressed_by_user,
                )
            ):
                raise ValueError("blocked decisions must not authorize effects")


def _build_decision(
    *,
    decision_id: str,
    action: NotificationProtectedAction,
    status: NotificationSecurityDecisionStatus,
    public_error_class: NotificationSecurityPublicErrorClass,
    authorization_scope_id: str,
    account_id: str | None,
    beacon_id: str | None,
    eligibility_decision_id: str | None,
    channel_class: NotificationChannelClass | None,
    target_reference_id: str | None,
    safe_listing_reference_ids: tuple[str, ...],
    historical_evidence_snapshot: NotificationHistoricalEvidenceSnapshot | None,
    protected_read_authorized: bool,
    outbox_effect_authorized: bool,
    channel_delivery_authorized: bool,
    recovery_grace_applied: bool,
    suppressed_by_user: bool,
    reason_codes: tuple[str, ...],
    evidence_reference_ids: tuple[str, ...],
) -> NotificationSecurityPrivacyDecision:
    return NotificationSecurityPrivacyDecision(
        decision_id=decision_id,
        authority=NotificationSecurityPrivacyAuthority.NOTIFICATION_DELIVERY_SERVER,
        action=action,
        status=status,
        public_error_class=public_error_class,
        authorization_scope_id=authorization_scope_id,
        account_id=account_id,
        beacon_id=beacon_id,
        eligibility_decision_id=eligibility_decision_id,
        channel_class=channel_class,
        target_reference_id=target_reference_id,
        safe_listing_reference_ids=safe_listing_reference_ids,
        historical_evidence_snapshot=historical_evidence_snapshot,
        protected_read_authorized=protected_read_authorized,
        outbox_effect_authorized=outbox_effect_authorized,
        channel_delivery_authorized=channel_delivery_authorized,
        recovery_grace_applied=recovery_grace_applied,
        suppressed_by_user=suppressed_by_user,
        historical_entitlement_evidence_rewritten=False,
        historical_beacon_evidence_rewritten=False,
        historical_evidence_mutation_authorized=False,
        provider_mapping_authorized=False,
        provider_execution_authorized=False,
        read_tracking_authorized=False,
        click_tracking_authorized=False,
        retention_authorized=False,
        reason_codes=reason_codes,
        evidence_reference_ids=evidence_reference_ids,
    )


def _blocked_authorization_decision(
    *,
    decision_id: str,
    action: NotificationProtectedAction,
    authorization_scope: NotificationSecurityAuthorizationScope,
    status: NotificationSecurityDecisionStatus,
    reason_codes: tuple[str, ...],
    evidence_reference_ids: tuple[str, ...],
) -> NotificationSecurityPrivacyDecision:
    public_error_class = (
        NotificationSecurityPublicErrorClass.NOT_AUTHORIZED_OR_NOT_FOUND
        if status is NotificationSecurityDecisionStatus.BLOCKED_NOT_AUTHORIZED_OR_NOT_FOUND
        else NotificationSecurityPublicErrorClass.REQUEST_BLOCKED
    )
    return _build_decision(
        decision_id=decision_id,
        action=action,
        status=status,
        public_error_class=public_error_class,
        authorization_scope_id=authorization_scope.scope_id,
        account_id=None,
        beacon_id=None,
        eligibility_decision_id=None,
        channel_class=None,
        target_reference_id=None,
        safe_listing_reference_ids=(),
        historical_evidence_snapshot=None,
        protected_read_authorized=False,
        outbox_effect_authorized=False,
        channel_delivery_authorized=False,
        recovery_grace_applied=False,
        suppressed_by_user=False,
        reason_codes=reason_codes,
        evidence_reference_ids=evidence_reference_ids,
    )


def _safe_content_evidence(
    evidence_reference_ids: tuple[str, ...],
    content_scope: NotificationSafeContentScope,
) -> tuple[str, ...]:
    return _combined_evidence_reference_ids(
        evidence_reference_ids,
        content_scope.evidence_reference_ids,
    )


def _post_auth_evidence(
    *,
    evidence_reference_ids: tuple[str, ...],
    authorization_scope: NotificationSecurityAuthorizationScope,
    historical_evidence_snapshot: NotificationHistoricalEvidenceSnapshot,
    content_scope: NotificationSafeContentScope,
    eligibility_decision: NotificationEligibilityDecision | None,
    channel_gate_decision: NotificationChannelGateDecision | None,
) -> tuple[str, ...]:
    combined = evidence_reference_ids + authorization_scope.evidence_reference_ids
    combined += historical_evidence_snapshot.evidence_reference_ids
    combined += content_scope.evidence_reference_ids
    if eligibility_decision is not None:
        combined += eligibility_decision.evidence_reference_ids
    if channel_gate_decision is not None:
        combined += channel_gate_decision.evidence_reference_ids
    return combined


def _block_due_to_content(
    *,
    decision_id: str,
    action: NotificationProtectedAction,
    authorization_scope: NotificationSecurityAuthorizationScope,
    historical_evidence_snapshot: NotificationHistoricalEvidenceSnapshot,
    reason_codes: tuple[str, ...],
    content_scope: NotificationSafeContentScope,
    evidence_reference_ids: tuple[str, ...],
) -> NotificationSecurityPrivacyDecision:
    return _build_decision(
        decision_id=decision_id,
        action=action,
        status=(
            NotificationSecurityDecisionStatus.BLOCKED_AMBIGUOUS
            if reason_codes == ("ambiguous-content",)
            else NotificationSecurityDecisionStatus.BLOCKED_UNSAFE_CONTENT
        ),
        public_error_class=NotificationSecurityPublicErrorClass.REQUEST_BLOCKED,
        authorization_scope_id=authorization_scope.scope_id,
        account_id=historical_evidence_snapshot.account_id,
        beacon_id=historical_evidence_snapshot.beacon_id,
        eligibility_decision_id=None,
        channel_class=(
            NotificationChannelClass.WEB_STATUS_READ_MODEL
            if action is NotificationProtectedAction.PROTECTED_READ
            else None
        ),
        target_reference_id=None,
        safe_listing_reference_ids=(
            content_scope.safe_listing_reference_ids
            if content_scope.safety_status
            is NotificationContentSafetyStatus.APPROVED_SAFE_REFERENCES
            else ()
        ),
        historical_evidence_snapshot=historical_evidence_snapshot,
        protected_read_authorized=False,
        outbox_effect_authorized=False,
        channel_delivery_authorized=False,
        recovery_grace_applied=False,
        suppressed_by_user=False,
        reason_codes=reason_codes,
        evidence_reference_ids=_safe_content_evidence(evidence_reference_ids, content_scope),
    )


def _project_protected_read(
    *,
    decision_id: str,
    authorization_scope: NotificationSecurityAuthorizationScope,
    historical_evidence_snapshot: NotificationHistoricalEvidenceSnapshot,
    content_scope: NotificationSafeContentScope,
    evidence_reference_ids: tuple[str, ...],
) -> NotificationSecurityPrivacyDecision:
    content_status = content_scope.safety_status
    safe_listing_reference_ids: tuple[str, ...]
    if content_status is NotificationContentSafetyStatus.EMPTY:
        safe_listing_reference_ids = ()
    elif content_status is NotificationContentSafetyStatus.APPROVED_SAFE_REFERENCES:
        safe_listing_reference_ids = content_scope.safe_listing_reference_ids
    elif content_status is NotificationContentSafetyStatus.AMBIGUOUS:
        return _block_due_to_content(
            decision_id=decision_id,
            action=NotificationProtectedAction.PROTECTED_READ,
            authorization_scope=authorization_scope,
            historical_evidence_snapshot=historical_evidence_snapshot,
            reason_codes=("ambiguous-content",),
            content_scope=content_scope,
            evidence_reference_ids=evidence_reference_ids,
        )
    else:
        return _block_due_to_content(
            decision_id=decision_id,
            action=NotificationProtectedAction.PROTECTED_READ,
            authorization_scope=authorization_scope,
            historical_evidence_snapshot=historical_evidence_snapshot,
            reason_codes=("unsafe-or-unapproved-content",),
            content_scope=content_scope,
            evidence_reference_ids=evidence_reference_ids,
        )

    return _build_decision(
        decision_id=decision_id,
        action=NotificationProtectedAction.PROTECTED_READ,
        status=NotificationSecurityDecisionStatus.AUTHORIZED_READ,
        public_error_class=NotificationSecurityPublicErrorClass.NONE,
        authorization_scope_id=authorization_scope.scope_id,
        account_id=historical_evidence_snapshot.account_id,
        beacon_id=historical_evidence_snapshot.beacon_id,
        eligibility_decision_id=None,
        channel_class=NotificationChannelClass.WEB_STATUS_READ_MODEL,
        target_reference_id=None,
        safe_listing_reference_ids=safe_listing_reference_ids,
        historical_evidence_snapshot=historical_evidence_snapshot,
        protected_read_authorized=True,
        outbox_effect_authorized=False,
        channel_delivery_authorized=False,
        recovery_grace_applied=False,
        suppressed_by_user=False,
        reason_codes=("authorized-read",),
        evidence_reference_ids=_safe_content_evidence(evidence_reference_ids, content_scope),
    )


def _project_outbox_effect(
    *,
    decision_id: str,
    authorization_scope: NotificationSecurityAuthorizationScope,
    historical_evidence_snapshot: NotificationHistoricalEvidenceSnapshot,
    content_scope: NotificationSafeContentScope,
    eligibility_decision: NotificationEligibilityDecision,
    evidence_reference_ids: tuple[str, ...],
) -> NotificationSecurityPrivacyDecision:
    if eligibility_decision.context.account_id != historical_evidence_snapshot.account_id:
        return _build_decision(
            decision_id=decision_id,
            action=NotificationProtectedAction.OUTBOX_EFFECT,
            status=NotificationSecurityDecisionStatus.BLOCKED_EVIDENCE_CONFLICT,
            public_error_class=NotificationSecurityPublicErrorClass.REQUEST_BLOCKED,
            authorization_scope_id=authorization_scope.scope_id,
            account_id=historical_evidence_snapshot.account_id,
            beacon_id=historical_evidence_snapshot.beacon_id,
            eligibility_decision_id=eligibility_decision.decision_id,
            channel_class=None,
            target_reference_id=None,
            safe_listing_reference_ids=(),
            historical_evidence_snapshot=historical_evidence_snapshot,
            protected_read_authorized=False,
            outbox_effect_authorized=False,
            channel_delivery_authorized=False,
            recovery_grace_applied=False,
            suppressed_by_user=False,
            reason_codes=("evidence-conflict",),
            evidence_reference_ids=_post_auth_evidence(
                evidence_reference_ids=evidence_reference_ids,
                authorization_scope=authorization_scope,
                historical_evidence_snapshot=historical_evidence_snapshot,
                content_scope=content_scope,
                eligibility_decision=eligibility_decision,
                channel_gate_decision=None,
            ),
        )
    if eligibility_decision.context.beacon_id != historical_evidence_snapshot.beacon_id:
        return _build_decision(
            decision_id=decision_id,
            action=NotificationProtectedAction.OUTBOX_EFFECT,
            status=NotificationSecurityDecisionStatus.BLOCKED_EVIDENCE_CONFLICT,
            public_error_class=NotificationSecurityPublicErrorClass.REQUEST_BLOCKED,
            authorization_scope_id=authorization_scope.scope_id,
            account_id=historical_evidence_snapshot.account_id,
            beacon_id=historical_evidence_snapshot.beacon_id,
            eligibility_decision_id=eligibility_decision.decision_id,
            channel_class=None,
            target_reference_id=None,
            safe_listing_reference_ids=(),
            historical_evidence_snapshot=historical_evidence_snapshot,
            protected_read_authorized=False,
            outbox_effect_authorized=False,
            channel_delivery_authorized=False,
            recovery_grace_applied=False,
            suppressed_by_user=False,
            reason_codes=("evidence-conflict",),
            evidence_reference_ids=_post_auth_evidence(
                evidence_reference_ids=evidence_reference_ids,
                authorization_scope=authorization_scope,
                historical_evidence_snapshot=historical_evidence_snapshot,
                content_scope=content_scope,
                eligibility_decision=eligibility_decision,
                channel_gate_decision=None,
            ),
        )

    content_status = content_scope.safety_status
    if content_status is not NotificationContentSafetyStatus.APPROVED_SAFE_REFERENCES:
        return _block_due_to_content(
            decision_id=decision_id,
            action=NotificationProtectedAction.OUTBOX_EFFECT,
            authorization_scope=authorization_scope,
            historical_evidence_snapshot=historical_evidence_snapshot,
            reason_codes=(
                "ambiguous-content"
                if content_status is NotificationContentSafetyStatus.AMBIGUOUS
                else "unsafe-or-unapproved-content",
            ),
            content_scope=content_scope,
            evidence_reference_ids=_post_auth_evidence(
                evidence_reference_ids=evidence_reference_ids,
                authorization_scope=authorization_scope,
                historical_evidence_snapshot=historical_evidence_snapshot,
                content_scope=content_scope,
                eligibility_decision=eligibility_decision,
                channel_gate_decision=None,
            ),
        )

    status = eligibility_decision.status
    if status is NotificationEligibilityStatus.SUPPRESSED_BY_PREFERENCE:
        return _build_decision(
            decision_id=decision_id,
            action=NotificationProtectedAction.OUTBOX_EFFECT,
            status=NotificationSecurityDecisionStatus.SUPPRESSED_BY_USER,
            public_error_class=NotificationSecurityPublicErrorClass.REQUEST_BLOCKED,
            authorization_scope_id=authorization_scope.scope_id,
            account_id=historical_evidence_snapshot.account_id,
            beacon_id=historical_evidence_snapshot.beacon_id,
            eligibility_decision_id=eligibility_decision.decision_id,
            channel_class=None,
            target_reference_id=None,
            safe_listing_reference_ids=content_scope.safe_listing_reference_ids,
            historical_evidence_snapshot=historical_evidence_snapshot,
            protected_read_authorized=False,
            outbox_effect_authorized=False,
            channel_delivery_authorized=False,
            recovery_grace_applied=False,
            suppressed_by_user=True,
            reason_codes=("suppressed-by-user",),
            evidence_reference_ids=_post_auth_evidence(
                evidence_reference_ids=evidence_reference_ids,
                authorization_scope=authorization_scope,
                historical_evidence_snapshot=historical_evidence_snapshot,
                content_scope=content_scope,
                eligibility_decision=eligibility_decision,
                channel_gate_decision=None,
            ),
        )
    if status is NotificationEligibilityStatus.ELIGIBLE:
        return _build_decision(
            decision_id=decision_id,
            action=NotificationProtectedAction.OUTBOX_EFFECT,
            status=NotificationSecurityDecisionStatus.AUTHORIZED_EFFECT,
            public_error_class=NotificationSecurityPublicErrorClass.NONE,
            authorization_scope_id=authorization_scope.scope_id,
            account_id=historical_evidence_snapshot.account_id,
            beacon_id=historical_evidence_snapshot.beacon_id,
            eligibility_decision_id=eligibility_decision.decision_id,
            channel_class=None,
            target_reference_id=None,
            safe_listing_reference_ids=content_scope.safe_listing_reference_ids,
            historical_evidence_snapshot=historical_evidence_snapshot,
            protected_read_authorized=False,
            outbox_effect_authorized=True,
            channel_delivery_authorized=False,
            recovery_grace_applied=False,
            suppressed_by_user=False,
            reason_codes=("authorized-effect",),
            evidence_reference_ids=_post_auth_evidence(
                evidence_reference_ids=evidence_reference_ids,
                authorization_scope=authorization_scope,
                historical_evidence_snapshot=historical_evidence_snapshot,
                content_scope=content_scope,
                eligibility_decision=eligibility_decision,
                channel_gate_decision=None,
            ),
        )
    if status is NotificationEligibilityStatus.ELIGIBLE_RECOVERY_GRACE:
        return _build_decision(
            decision_id=decision_id,
            action=NotificationProtectedAction.OUTBOX_EFFECT,
            status=NotificationSecurityDecisionStatus.AUTHORIZED_RECOVERY_GRACE,
            public_error_class=NotificationSecurityPublicErrorClass.NONE,
            authorization_scope_id=authorization_scope.scope_id,
            account_id=historical_evidence_snapshot.account_id,
            beacon_id=historical_evidence_snapshot.beacon_id,
            eligibility_decision_id=eligibility_decision.decision_id,
            channel_class=None,
            target_reference_id=None,
            safe_listing_reference_ids=content_scope.safe_listing_reference_ids,
            historical_evidence_snapshot=historical_evidence_snapshot,
            protected_read_authorized=False,
            outbox_effect_authorized=True,
            channel_delivery_authorized=False,
            recovery_grace_applied=True,
            suppressed_by_user=False,
            reason_codes=("authorized-recovery-grace",),
            evidence_reference_ids=_post_auth_evidence(
                evidence_reference_ids=evidence_reference_ids,
                authorization_scope=authorization_scope,
                historical_evidence_snapshot=historical_evidence_snapshot,
                content_scope=content_scope,
                eligibility_decision=eligibility_decision,
                channel_gate_decision=None,
            ),
        )
    if status is NotificationEligibilityStatus.BLOCKED_AMBIGUOUS or (
        eligibility_decision.context.beacon_lifecycle_status
        is NotificationBeaconLifecycleStatus.AMBIGUOUS
        or eligibility_decision.context.entitlement_status
        in (NotificationEntitlementStatus.AMBIGUOUS, NotificationEntitlementStatus.CONFLICT)
    ):
        return _build_decision(
            decision_id=decision_id,
            action=NotificationProtectedAction.OUTBOX_EFFECT,
            status=NotificationSecurityDecisionStatus.BLOCKED_AMBIGUOUS,
            public_error_class=NotificationSecurityPublicErrorClass.REQUEST_BLOCKED,
            authorization_scope_id=authorization_scope.scope_id,
            account_id=historical_evidence_snapshot.account_id,
            beacon_id=historical_evidence_snapshot.beacon_id,
            eligibility_decision_id=eligibility_decision.decision_id,
            channel_class=None,
            target_reference_id=None,
            safe_listing_reference_ids=content_scope.safe_listing_reference_ids,
            historical_evidence_snapshot=historical_evidence_snapshot,
            protected_read_authorized=False,
            outbox_effect_authorized=False,
            channel_delivery_authorized=False,
            recovery_grace_applied=False,
            suppressed_by_user=False,
            reason_codes=("ambiguous-lifecycle-or-entitlement",),
            evidence_reference_ids=_post_auth_evidence(
                evidence_reference_ids=evidence_reference_ids,
                authorization_scope=authorization_scope,
                historical_evidence_snapshot=historical_evidence_snapshot,
                content_scope=content_scope,
                eligibility_decision=eligibility_decision,
                channel_gate_decision=None,
            ),
        )

    return _build_decision(
        decision_id=decision_id,
        action=NotificationProtectedAction.OUTBOX_EFFECT,
        status=NotificationSecurityDecisionStatus.BLOCKED_AMBIGUOUS,
        public_error_class=NotificationSecurityPublicErrorClass.REQUEST_BLOCKED,
        authorization_scope_id=authorization_scope.scope_id,
        account_id=historical_evidence_snapshot.account_id,
        beacon_id=historical_evidence_snapshot.beacon_id,
        eligibility_decision_id=eligibility_decision.decision_id,
        channel_class=None,
        target_reference_id=None,
        safe_listing_reference_ids=content_scope.safe_listing_reference_ids,
        historical_evidence_snapshot=historical_evidence_snapshot,
        protected_read_authorized=False,
        outbox_effect_authorized=False,
        channel_delivery_authorized=False,
        recovery_grace_applied=False,
        suppressed_by_user=False,
        reason_codes=("ambiguous-lifecycle-or-entitlement",),
        evidence_reference_ids=_post_auth_evidence(
            evidence_reference_ids=evidence_reference_ids,
            authorization_scope=authorization_scope,
            historical_evidence_snapshot=historical_evidence_snapshot,
            content_scope=content_scope,
            eligibility_decision=eligibility_decision,
            channel_gate_decision=None,
        ),
    )


def _project_channel_delivery(
    *,
    decision_id: str,
    authorization_scope: NotificationSecurityAuthorizationScope,
    historical_evidence_snapshot: NotificationHistoricalEvidenceSnapshot,
    content_scope: NotificationSafeContentScope,
    eligibility_decision: NotificationEligibilityDecision,
    channel_gate_decision: NotificationChannelGateDecision,
    evidence_reference_ids: tuple[str, ...],
) -> NotificationSecurityPrivacyDecision:
    if not any(
        channel_gate_decision is gate for gate in eligibility_decision.channel_gate_decisions
    ):
        return _build_decision(
            decision_id=decision_id,
            action=NotificationProtectedAction.CHANNEL_DELIVERY,
            status=NotificationSecurityDecisionStatus.BLOCKED_EVIDENCE_CONFLICT,
            public_error_class=NotificationSecurityPublicErrorClass.REQUEST_BLOCKED,
            authorization_scope_id=authorization_scope.scope_id,
            account_id=historical_evidence_snapshot.account_id,
            beacon_id=historical_evidence_snapshot.beacon_id,
            eligibility_decision_id=eligibility_decision.decision_id,
            channel_class=channel_gate_decision.channel_class,
            target_reference_id=None,
            safe_listing_reference_ids=(),
            historical_evidence_snapshot=historical_evidence_snapshot,
            protected_read_authorized=False,
            outbox_effect_authorized=False,
            channel_delivery_authorized=False,
            recovery_grace_applied=False,
            suppressed_by_user=False,
            reason_codes=("evidence-conflict",),
            evidence_reference_ids=_post_auth_evidence(
                evidence_reference_ids=evidence_reference_ids,
                authorization_scope=authorization_scope,
                historical_evidence_snapshot=historical_evidence_snapshot,
                content_scope=content_scope,
                eligibility_decision=eligibility_decision,
                channel_gate_decision=channel_gate_decision,
            ),
        )
    if channel_gate_decision.channel_class is NotificationChannelClass.WEB_STATUS_READ_MODEL:
        return _build_decision(
            decision_id=decision_id,
            action=NotificationProtectedAction.CHANNEL_DELIVERY,
            status=NotificationSecurityDecisionStatus.BLOCKED_EVIDENCE_CONFLICT,
            public_error_class=NotificationSecurityPublicErrorClass.REQUEST_BLOCKED,
            authorization_scope_id=authorization_scope.scope_id,
            account_id=historical_evidence_snapshot.account_id,
            beacon_id=historical_evidence_snapshot.beacon_id,
            eligibility_decision_id=eligibility_decision.decision_id,
            channel_class=channel_gate_decision.channel_class,
            target_reference_id=None,
            safe_listing_reference_ids=(),
            historical_evidence_snapshot=historical_evidence_snapshot,
            protected_read_authorized=False,
            outbox_effect_authorized=False,
            channel_delivery_authorized=False,
            recovery_grace_applied=False,
            suppressed_by_user=False,
            reason_codes=("evidence-conflict",),
            evidence_reference_ids=_post_auth_evidence(
                evidence_reference_ids=evidence_reference_ids,
                authorization_scope=authorization_scope,
                historical_evidence_snapshot=historical_evidence_snapshot,
                content_scope=content_scope,
                eligibility_decision=eligibility_decision,
                channel_gate_decision=channel_gate_decision,
            ),
        )
    if eligibility_decision.context.account_id != historical_evidence_snapshot.account_id:
        return _build_decision(
            decision_id=decision_id,
            action=NotificationProtectedAction.CHANNEL_DELIVERY,
            status=NotificationSecurityDecisionStatus.BLOCKED_EVIDENCE_CONFLICT,
            public_error_class=NotificationSecurityPublicErrorClass.REQUEST_BLOCKED,
            authorization_scope_id=authorization_scope.scope_id,
            account_id=historical_evidence_snapshot.account_id,
            beacon_id=historical_evidence_snapshot.beacon_id,
            eligibility_decision_id=eligibility_decision.decision_id,
            channel_class=channel_gate_decision.channel_class,
            target_reference_id=None,
            safe_listing_reference_ids=(),
            historical_evidence_snapshot=historical_evidence_snapshot,
            protected_read_authorized=False,
            outbox_effect_authorized=False,
            channel_delivery_authorized=False,
            recovery_grace_applied=False,
            suppressed_by_user=False,
            reason_codes=("evidence-conflict",),
            evidence_reference_ids=_post_auth_evidence(
                evidence_reference_ids=evidence_reference_ids,
                authorization_scope=authorization_scope,
                historical_evidence_snapshot=historical_evidence_snapshot,
                content_scope=content_scope,
                eligibility_decision=eligibility_decision,
                channel_gate_decision=channel_gate_decision,
            ),
        )
    if eligibility_decision.context.beacon_id != historical_evidence_snapshot.beacon_id:
        return _build_decision(
            decision_id=decision_id,
            action=NotificationProtectedAction.CHANNEL_DELIVERY,
            status=NotificationSecurityDecisionStatus.BLOCKED_EVIDENCE_CONFLICT,
            public_error_class=NotificationSecurityPublicErrorClass.REQUEST_BLOCKED,
            authorization_scope_id=authorization_scope.scope_id,
            account_id=historical_evidence_snapshot.account_id,
            beacon_id=historical_evidence_snapshot.beacon_id,
            eligibility_decision_id=eligibility_decision.decision_id,
            channel_class=channel_gate_decision.channel_class,
            target_reference_id=None,
            safe_listing_reference_ids=(),
            historical_evidence_snapshot=historical_evidence_snapshot,
            protected_read_authorized=False,
            outbox_effect_authorized=False,
            channel_delivery_authorized=False,
            recovery_grace_applied=False,
            suppressed_by_user=False,
            reason_codes=("evidence-conflict",),
            evidence_reference_ids=_post_auth_evidence(
                evidence_reference_ids=evidence_reference_ids,
                authorization_scope=authorization_scope,
                historical_evidence_snapshot=historical_evidence_snapshot,
                content_scope=content_scope,
                eligibility_decision=eligibility_decision,
                channel_gate_decision=channel_gate_decision,
            ),
        )

    content_status = content_scope.safety_status
    if content_status is not NotificationContentSafetyStatus.APPROVED_SAFE_REFERENCES:
        return _block_due_to_content(
            decision_id=decision_id,
            action=NotificationProtectedAction.CHANNEL_DELIVERY,
            authorization_scope=authorization_scope,
            historical_evidence_snapshot=historical_evidence_snapshot,
            reason_codes=(
                "ambiguous-content"
                if content_status is NotificationContentSafetyStatus.AMBIGUOUS
                else "unsafe-or-unapproved-content",
            ),
            content_scope=content_scope,
            evidence_reference_ids=_post_auth_evidence(
                evidence_reference_ids=evidence_reference_ids,
                authorization_scope=authorization_scope,
                historical_evidence_snapshot=historical_evidence_snapshot,
                content_scope=content_scope,
                eligibility_decision=eligibility_decision,
                channel_gate_decision=channel_gate_decision,
            ),
        )

    gate_status = channel_gate_decision.status
    if gate_status is NotificationChannelGateStatus.DISABLED_BY_USER:
        return _build_decision(
            decision_id=decision_id,
            action=NotificationProtectedAction.CHANNEL_DELIVERY,
            status=NotificationSecurityDecisionStatus.SUPPRESSED_BY_USER,
            public_error_class=NotificationSecurityPublicErrorClass.REQUEST_BLOCKED,
            authorization_scope_id=authorization_scope.scope_id,
            account_id=historical_evidence_snapshot.account_id,
            beacon_id=historical_evidence_snapshot.beacon_id,
            eligibility_decision_id=eligibility_decision.decision_id,
            channel_class=channel_gate_decision.channel_class,
            target_reference_id=None,
            safe_listing_reference_ids=content_scope.safe_listing_reference_ids,
            historical_evidence_snapshot=historical_evidence_snapshot,
            protected_read_authorized=False,
            outbox_effect_authorized=False,
            channel_delivery_authorized=False,
            recovery_grace_applied=False,
            suppressed_by_user=True,
            reason_codes=("suppressed-by-user",),
            evidence_reference_ids=_post_auth_evidence(
                evidence_reference_ids=evidence_reference_ids,
                authorization_scope=authorization_scope,
                historical_evidence_snapshot=historical_evidence_snapshot,
                content_scope=content_scope,
                eligibility_decision=eligibility_decision,
                channel_gate_decision=channel_gate_decision,
            ),
        )
    if gate_status in (
        NotificationChannelGateStatus.TARGET_UNVERIFIED,
        NotificationChannelGateStatus.TARGET_UNAVAILABLE,
    ):
        return _build_decision(
            decision_id=decision_id,
            action=NotificationProtectedAction.CHANNEL_DELIVERY,
            status=NotificationSecurityDecisionStatus.BLOCKED_TARGET_UNVERIFIED,
            public_error_class=NotificationSecurityPublicErrorClass.REQUEST_BLOCKED,
            authorization_scope_id=authorization_scope.scope_id,
            account_id=historical_evidence_snapshot.account_id,
            beacon_id=historical_evidence_snapshot.beacon_id,
            eligibility_decision_id=eligibility_decision.decision_id,
            channel_class=channel_gate_decision.channel_class,
            target_reference_id=None,
            safe_listing_reference_ids=content_scope.safe_listing_reference_ids,
            historical_evidence_snapshot=historical_evidence_snapshot,
            protected_read_authorized=False,
            outbox_effect_authorized=False,
            channel_delivery_authorized=False,
            recovery_grace_applied=False,
            suppressed_by_user=False,
            reason_codes=("target-unverified",),
            evidence_reference_ids=_post_auth_evidence(
                evidence_reference_ids=evidence_reference_ids,
                authorization_scope=authorization_scope,
                historical_evidence_snapshot=historical_evidence_snapshot,
                content_scope=content_scope,
                eligibility_decision=eligibility_decision,
                channel_gate_decision=channel_gate_decision,
            ),
        )
    if eligibility_decision.status is NotificationEligibilityStatus.SUPPRESSED_BY_PREFERENCE:
        return _build_decision(
            decision_id=decision_id,
            action=NotificationProtectedAction.CHANNEL_DELIVERY,
            status=NotificationSecurityDecisionStatus.SUPPRESSED_BY_USER,
            public_error_class=NotificationSecurityPublicErrorClass.REQUEST_BLOCKED,
            authorization_scope_id=authorization_scope.scope_id,
            account_id=historical_evidence_snapshot.account_id,
            beacon_id=historical_evidence_snapshot.beacon_id,
            eligibility_decision_id=eligibility_decision.decision_id,
            channel_class=channel_gate_decision.channel_class,
            target_reference_id=None,
            safe_listing_reference_ids=content_scope.safe_listing_reference_ids,
            historical_evidence_snapshot=historical_evidence_snapshot,
            protected_read_authorized=False,
            outbox_effect_authorized=False,
            channel_delivery_authorized=False,
            recovery_grace_applied=False,
            suppressed_by_user=True,
            reason_codes=("suppressed-by-user",),
            evidence_reference_ids=_post_auth_evidence(
                evidence_reference_ids=evidence_reference_ids,
                authorization_scope=authorization_scope,
                historical_evidence_snapshot=historical_evidence_snapshot,
                content_scope=content_scope,
                eligibility_decision=eligibility_decision,
                channel_gate_decision=channel_gate_decision,
            ),
        )

    if gate_status is NotificationChannelGateStatus.ELIGIBLE:
        if eligibility_decision.status is NotificationEligibilityStatus.ELIGIBLE:
            return _build_decision(
                decision_id=decision_id,
                action=NotificationProtectedAction.CHANNEL_DELIVERY,
                status=NotificationSecurityDecisionStatus.AUTHORIZED_EFFECT,
                public_error_class=NotificationSecurityPublicErrorClass.NONE,
                authorization_scope_id=authorization_scope.scope_id,
                account_id=historical_evidence_snapshot.account_id,
                beacon_id=historical_evidence_snapshot.beacon_id,
                eligibility_decision_id=eligibility_decision.decision_id,
                channel_class=channel_gate_decision.channel_class,
                target_reference_id=channel_gate_decision.target_reference_id,
                safe_listing_reference_ids=content_scope.safe_listing_reference_ids,
                historical_evidence_snapshot=historical_evidence_snapshot,
                protected_read_authorized=False,
                outbox_effect_authorized=False,
                channel_delivery_authorized=True,
                recovery_grace_applied=False,
                suppressed_by_user=False,
                reason_codes=("authorized-effect",),
                evidence_reference_ids=_post_auth_evidence(
                    evidence_reference_ids=evidence_reference_ids,
                    authorization_scope=authorization_scope,
                    historical_evidence_snapshot=historical_evidence_snapshot,
                    content_scope=content_scope,
                    eligibility_decision=eligibility_decision,
                    channel_gate_decision=channel_gate_decision,
                ),
            )
        if eligibility_decision.status is NotificationEligibilityStatus.ELIGIBLE_RECOVERY_GRACE:
            return _build_decision(
                decision_id=decision_id,
                action=NotificationProtectedAction.CHANNEL_DELIVERY,
                status=NotificationSecurityDecisionStatus.AUTHORIZED_RECOVERY_GRACE,
                public_error_class=NotificationSecurityPublicErrorClass.NONE,
                authorization_scope_id=authorization_scope.scope_id,
                account_id=historical_evidence_snapshot.account_id,
                beacon_id=historical_evidence_snapshot.beacon_id,
                eligibility_decision_id=eligibility_decision.decision_id,
                channel_class=channel_gate_decision.channel_class,
                target_reference_id=channel_gate_decision.target_reference_id,
                safe_listing_reference_ids=content_scope.safe_listing_reference_ids,
                historical_evidence_snapshot=historical_evidence_snapshot,
                protected_read_authorized=False,
                outbox_effect_authorized=False,
                channel_delivery_authorized=True,
                recovery_grace_applied=True,
                suppressed_by_user=False,
                reason_codes=("authorized-recovery-grace",),
                evidence_reference_ids=_post_auth_evidence(
                    evidence_reference_ids=evidence_reference_ids,
                    authorization_scope=authorization_scope,
                    historical_evidence_snapshot=historical_evidence_snapshot,
                    content_scope=content_scope,
                    eligibility_decision=eligibility_decision,
                    channel_gate_decision=channel_gate_decision,
                ),
            )

    if eligibility_decision.status is NotificationEligibilityStatus.BLOCKED_AMBIGUOUS or (
        eligibility_decision.context.beacon_lifecycle_status
        is NotificationBeaconLifecycleStatus.AMBIGUOUS
        or eligibility_decision.context.entitlement_status
        in (NotificationEntitlementStatus.AMBIGUOUS, NotificationEntitlementStatus.CONFLICT)
    ):
        return _build_decision(
            decision_id=decision_id,
            action=NotificationProtectedAction.CHANNEL_DELIVERY,
            status=NotificationSecurityDecisionStatus.BLOCKED_AMBIGUOUS,
            public_error_class=NotificationSecurityPublicErrorClass.REQUEST_BLOCKED,
            authorization_scope_id=authorization_scope.scope_id,
            account_id=historical_evidence_snapshot.account_id,
            beacon_id=historical_evidence_snapshot.beacon_id,
            eligibility_decision_id=eligibility_decision.decision_id,
            channel_class=channel_gate_decision.channel_class,
            target_reference_id=None,
            safe_listing_reference_ids=content_scope.safe_listing_reference_ids,
            historical_evidence_snapshot=historical_evidence_snapshot,
            protected_read_authorized=False,
            outbox_effect_authorized=False,
            channel_delivery_authorized=False,
            recovery_grace_applied=False,
            suppressed_by_user=False,
            reason_codes=("ambiguous-lifecycle-or-entitlement",),
            evidence_reference_ids=_post_auth_evidence(
                evidence_reference_ids=evidence_reference_ids,
                authorization_scope=authorization_scope,
                historical_evidence_snapshot=historical_evidence_snapshot,
                content_scope=content_scope,
                eligibility_decision=eligibility_decision,
                channel_gate_decision=channel_gate_decision,
            ),
        )

    return _build_decision(
        decision_id=decision_id,
        action=NotificationProtectedAction.CHANNEL_DELIVERY,
        status=NotificationSecurityDecisionStatus.BLOCKED_AMBIGUOUS,
        public_error_class=NotificationSecurityPublicErrorClass.REQUEST_BLOCKED,
        authorization_scope_id=authorization_scope.scope_id,
        account_id=historical_evidence_snapshot.account_id,
        beacon_id=historical_evidence_snapshot.beacon_id,
        eligibility_decision_id=eligibility_decision.decision_id,
        channel_class=channel_gate_decision.channel_class,
        target_reference_id=None,
        safe_listing_reference_ids=content_scope.safe_listing_reference_ids,
        historical_evidence_snapshot=historical_evidence_snapshot,
        protected_read_authorized=False,
        outbox_effect_authorized=False,
        channel_delivery_authorized=False,
        recovery_grace_applied=False,
        suppressed_by_user=False,
        reason_codes=("ambiguous-lifecycle-or-entitlement",),
        evidence_reference_ids=_post_auth_evidence(
            evidence_reference_ids=evidence_reference_ids,
            authorization_scope=authorization_scope,
            historical_evidence_snapshot=historical_evidence_snapshot,
            content_scope=content_scope,
            eligibility_decision=eligibility_decision,
            channel_gate_decision=channel_gate_decision,
        ),
    )


def evaluate_notification_security_privacy(
    *,
    decision_id: str,
    action: NotificationProtectedAction,
    authorization_scope: NotificationSecurityAuthorizationScope,
    content_scope: NotificationSafeContentScope,
    historical_evidence_snapshot: NotificationHistoricalEvidenceSnapshot,
    eligibility_decision: NotificationEligibilityDecision | None,
    channel_gate_decision: NotificationChannelGateDecision | None,
    evidence_reference_ids: tuple[str, ...],
) -> NotificationSecurityPrivacyDecision:
    _require_text(decision_id, "decision_id")
    _require_exact_enum(action, NotificationProtectedAction, "action")
    if type(authorization_scope) is not NotificationSecurityAuthorizationScope:
        raise ValueError("authorization_scope must be NotificationSecurityAuthorizationScope")
    if type(content_scope) is not NotificationSafeContentScope:
        raise ValueError("content_scope must be NotificationSafeContentScope")
    if type(historical_evidence_snapshot) is not NotificationHistoricalEvidenceSnapshot:
        raise ValueError(
            "historical_evidence_snapshot must be NotificationHistoricalEvidenceSnapshot"
        )
    if (
        eligibility_decision is not None
        and type(eligibility_decision) is not NotificationEligibilityDecision
    ):
        raise ValueError("eligibility_decision must be NotificationEligibilityDecision")
    if (
        channel_gate_decision is not None
        and type(channel_gate_decision) is not NotificationChannelGateDecision
    ):
        raise ValueError("channel_gate_decision must be NotificationChannelGateDecision")
    _require_text_tuple(
        evidence_reference_ids, "evidence_reference_ids", allow_empty=True, unique=False
    )

    auth_status = authorization_scope.identity_status
    if auth_status is NotificationIdentityScopeStatus.AMBIGUOUS:
        return _blocked_authorization_decision(
            decision_id=decision_id,
            action=action,
            authorization_scope=authorization_scope,
            status=NotificationSecurityDecisionStatus.BLOCKED_AMBIGUOUS,
            reason_codes=("ambiguous-identity",),
            evidence_reference_ids=_combined_evidence_reference_ids(
                evidence_reference_ids,
                authorization_scope.evidence_reference_ids,
            ),
        )
    if (
        auth_status is not NotificationIdentityScopeStatus.VERIFIED
        or not authorization_scope.authorized
    ):
        return _blocked_authorization_decision(
            decision_id=decision_id,
            action=action,
            authorization_scope=authorization_scope,
            status=NotificationSecurityDecisionStatus.BLOCKED_NOT_AUTHORIZED_OR_NOT_FOUND,
            reason_codes=("not-authorized-or-not-found",),
            evidence_reference_ids=_combined_evidence_reference_ids(
                evidence_reference_ids,
                authorization_scope.evidence_reference_ids,
            ),
        )

    if historical_evidence_snapshot.account_id not in authorization_scope.authorized_account_ids:
        return _blocked_authorization_decision(
            decision_id=decision_id,
            action=action,
            authorization_scope=authorization_scope,
            status=NotificationSecurityDecisionStatus.BLOCKED_NOT_AUTHORIZED_OR_NOT_FOUND,
            reason_codes=("not-authorized-or-not-found",),
            evidence_reference_ids=_combined_evidence_reference_ids(
                evidence_reference_ids,
                authorization_scope.evidence_reference_ids,
            ),
        )
    if (
        historical_evidence_snapshot.beacon_id is not None
        and historical_evidence_snapshot.beacon_id not in authorization_scope.authorized_beacon_ids
    ):
        return _blocked_authorization_decision(
            decision_id=decision_id,
            action=action,
            authorization_scope=authorization_scope,
            status=NotificationSecurityDecisionStatus.BLOCKED_NOT_AUTHORIZED_OR_NOT_FOUND,
            reason_codes=("not-authorized-or-not-found",),
            evidence_reference_ids=_combined_evidence_reference_ids(
                evidence_reference_ids,
                authorization_scope.evidence_reference_ids,
            ),
        )

    if action is NotificationProtectedAction.PROTECTED_READ:
        if eligibility_decision is not None or channel_gate_decision is not None:
            return _build_decision(
                decision_id=decision_id,
                action=action,
                status=NotificationSecurityDecisionStatus.BLOCKED_EVIDENCE_CONFLICT,
                public_error_class=NotificationSecurityPublicErrorClass.REQUEST_BLOCKED,
                authorization_scope_id=authorization_scope.scope_id,
                account_id=historical_evidence_snapshot.account_id,
                beacon_id=historical_evidence_snapshot.beacon_id,
                eligibility_decision_id=None,
                channel_class=NotificationChannelClass.WEB_STATUS_READ_MODEL,
                target_reference_id=None,
                safe_listing_reference_ids=(),
                historical_evidence_snapshot=historical_evidence_snapshot,
                protected_read_authorized=False,
                outbox_effect_authorized=False,
                channel_delivery_authorized=False,
                recovery_grace_applied=False,
                suppressed_by_user=False,
                reason_codes=("evidence-conflict",),
                evidence_reference_ids=_combined_evidence_reference_ids(
                    evidence_reference_ids,
                    authorization_scope.evidence_reference_ids,
                    historical_evidence_snapshot.evidence_reference_ids,
                    content_scope.evidence_reference_ids,
                ),
            )
        return _project_protected_read(
            decision_id=decision_id,
            authorization_scope=authorization_scope,
            historical_evidence_snapshot=historical_evidence_snapshot,
            content_scope=content_scope,
            evidence_reference_ids=_combined_evidence_reference_ids(
                evidence_reference_ids,
                authorization_scope.evidence_reference_ids,
                historical_evidence_snapshot.evidence_reference_ids,
            ),
        )

    if action is NotificationProtectedAction.OUTBOX_EFFECT:
        if eligibility_decision is None or channel_gate_decision is not None:
            return _build_decision(
                decision_id=decision_id,
                action=action,
                status=NotificationSecurityDecisionStatus.BLOCKED_EVIDENCE_CONFLICT,
                public_error_class=NotificationSecurityPublicErrorClass.REQUEST_BLOCKED,
                authorization_scope_id=authorization_scope.scope_id,
                account_id=historical_evidence_snapshot.account_id,
                beacon_id=historical_evidence_snapshot.beacon_id,
                eligibility_decision_id=None,
                channel_class=None,
                target_reference_id=None,
                safe_listing_reference_ids=(),
                historical_evidence_snapshot=historical_evidence_snapshot,
                protected_read_authorized=False,
                outbox_effect_authorized=False,
                channel_delivery_authorized=False,
                recovery_grace_applied=False,
                suppressed_by_user=False,
                reason_codes=("evidence-conflict",),
                evidence_reference_ids=_combined_evidence_reference_ids(
                    evidence_reference_ids,
                    authorization_scope.evidence_reference_ids,
                    historical_evidence_snapshot.evidence_reference_ids,
                    content_scope.evidence_reference_ids,
                ),
            )
        return _project_outbox_effect(
            decision_id=decision_id,
            authorization_scope=authorization_scope,
            historical_evidence_snapshot=historical_evidence_snapshot,
            content_scope=content_scope,
            eligibility_decision=eligibility_decision,
            evidence_reference_ids=_combined_evidence_reference_ids(
                evidence_reference_ids,
                authorization_scope.evidence_reference_ids,
                historical_evidence_snapshot.evidence_reference_ids,
            ),
        )

    if action is NotificationProtectedAction.CHANNEL_DELIVERY:
        if eligibility_decision is None or channel_gate_decision is None:
            return _build_decision(
                decision_id=decision_id,
                action=action,
                status=NotificationSecurityDecisionStatus.BLOCKED_EVIDENCE_CONFLICT,
                public_error_class=NotificationSecurityPublicErrorClass.REQUEST_BLOCKED,
                authorization_scope_id=authorization_scope.scope_id,
                account_id=historical_evidence_snapshot.account_id,
                beacon_id=historical_evidence_snapshot.beacon_id,
                eligibility_decision_id=None,
                channel_class=None,
                target_reference_id=None,
                safe_listing_reference_ids=(),
                historical_evidence_snapshot=historical_evidence_snapshot,
                protected_read_authorized=False,
                outbox_effect_authorized=False,
                channel_delivery_authorized=False,
                recovery_grace_applied=False,
                suppressed_by_user=False,
                reason_codes=("evidence-conflict",),
                evidence_reference_ids=_combined_evidence_reference_ids(
                    evidence_reference_ids,
                    authorization_scope.evidence_reference_ids,
                    historical_evidence_snapshot.evidence_reference_ids,
                    content_scope.evidence_reference_ids,
                ),
            )
        return _project_channel_delivery(
            decision_id=decision_id,
            authorization_scope=authorization_scope,
            historical_evidence_snapshot=historical_evidence_snapshot,
            content_scope=content_scope,
            eligibility_decision=eligibility_decision,
            channel_gate_decision=channel_gate_decision,
            evidence_reference_ids=_combined_evidence_reference_ids(
                evidence_reference_ids,
                authorization_scope.evidence_reference_ids,
                historical_evidence_snapshot.evidence_reference_ids,
            ),
        )

    raise AssertionError("unreachable action")


__all__ = (
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
)
