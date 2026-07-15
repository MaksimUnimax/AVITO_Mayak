from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .source_intake import (
    NotificationSourceFamily,
    NotificationSourceIntakeDecision,
    NotificationSourceIntakeStatus,
)

ND03_TASK_ID = "ND-03-ELIGIBILITY-PREFERENCES-20260715-004"

NO_NEW_MINIMUM_FREQUENCY_MINUTES = 60


class NotificationEligibilityAuthority(str, Enum):
    NOTIFICATION_DELIVERY_SERVER = "NOTIFICATION_DELIVERY_SERVER"


class NotificationBeaconLifecycleStatus(str, Enum):
    DRAFT = "DRAFT"
    READY = "READY"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    FROZEN = "FROZEN"
    ARCHIVED = "ARCHIVED"
    PERMANENTLY_DELETED = "PERMANENTLY_DELETED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    AMBIGUOUS = "AMBIGUOUS"


class NotificationEntitlementStatus(str, Enum):
    ALLOWED = "ALLOWED"
    DENIED = "DENIED"
    BLOCKED = "BLOCKED"
    EXPIRED = "EXPIRED"
    AMBIGUOUS = "AMBIGUOUS"
    UNSUPPORTED = "UNSUPPORTED"
    USER_CHOICE_REQUIRED = "USER_CHOICE_REQUIRED"
    FREE_COMPLIANCE_REQUIRED = "FREE_COMPLIANCE_REQUIRED"
    CONFLICT = "CONFLICT"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class NotificationChannelClass(str, Enum):
    TELEGRAM = "TELEGRAM"
    MAX = "MAX"
    WEB_STATUS_READ_MODEL = "WEB_STATUS_READ_MODEL"


class NotificationChannelGateStatus(str, Enum):
    ELIGIBLE = "ELIGIBLE"
    DISABLED_BY_USER = "DISABLED_BY_USER"
    TARGET_UNVERIFIED = "TARGET_UNVERIFIED"
    TARGET_UNAVAILABLE = "TARGET_UNAVAILABLE"
    READ_MODEL_ONLY = "READ_MODEL_ONLY"


class NotificationEligibilityStatus(str, Enum):
    ELIGIBLE = "ELIGIBLE"
    ELIGIBLE_RECOVERY_GRACE = "ELIGIBLE_RECOVERY_GRACE"
    STATUS_READ_MODEL_ONLY = "STATUS_READ_MODEL_ONLY"
    SUPPRESSED_BY_PREFERENCE = "SUPPRESSED_BY_PREFERENCE"
    BLOCKED_SOURCE_INTAKE = "BLOCKED_SOURCE_INTAKE"
    BLOCKED_SCOPE_MISMATCH = "BLOCKED_SCOPE_MISMATCH"
    BLOCKED_BEACON_LIFECYCLE = "BLOCKED_BEACON_LIFECYCLE"
    BLOCKED_ENTITLEMENT = "BLOCKED_ENTITLEMENT"
    BLOCKED_AMBIGUOUS = "BLOCKED_AMBIGUOUS"
    BLOCKED_NO_ELIGIBLE_PUSH_CHANNEL = "BLOCKED_NO_ELIGIBLE_PUSH_CHANNEL"


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


def _require_positive_int(value: object, field_name: str) -> int:
    if type(value) is not int or value <= 0:
        raise ValueError(f"{field_name} must be a positive int")
    return value


def _require_tuple_text(
    value: object,
    field_name: str,
    *,
    unique: bool,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    validated = tuple(_require_text(item, field_name) for item in value)
    if unique and len(set(validated)) != len(validated):
        raise ValueError(f"{field_name} must not contain duplicate values")
    return validated


@dataclass(frozen=True, slots=True)
class NotificationChannelEligibilityEvidence:
    channel_class: NotificationChannelClass
    enabled_by_user: bool
    target_reference_id: str | None
    target_verified: bool
    target_available: bool
    evidence_reference_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if type(self.channel_class) is not NotificationChannelClass:
            raise ValueError("channel_class must be NotificationChannelClass")
        _require_bool(self.enabled_by_user, "enabled_by_user")
        _require_optional_text(self.target_reference_id, "target_reference_id")
        _require_bool(self.target_verified, "target_verified")
        _require_bool(self.target_available, "target_available")
        _require_tuple_text(self.evidence_reference_ids, "evidence_reference_ids", unique=True)

        if self.channel_class is NotificationChannelClass.WEB_STATUS_READ_MODEL:
            if not self.enabled_by_user:
                raise ValueError("web read model evidence must be enabled by user")
            if self.target_reference_id is not None:
                raise ValueError("web read model evidence must not carry a target reference")
            if self.target_verified or self.target_available:
                raise ValueError("web read model evidence must not carry push target state")
            return

        if self.target_verified and self.target_reference_id is None:
            raise ValueError("verified push targets require a target reference")


@dataclass(frozen=True, slots=True)
class NotificationRecoveryGraceEvidence:
    problem_began_while_access_active: bool
    recovery_obligation_reference_id: str | None
    recovery_result_already_consumed: bool
    beacon_frozen_due_to_access_expiry: bool
    evidence_reference_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_bool(
            self.problem_began_while_access_active,
            "problem_began_while_access_active",
        )
        _require_optional_text(
            self.recovery_obligation_reference_id,
            "recovery_obligation_reference_id",
        )
        _require_bool(self.recovery_result_already_consumed, "recovery_result_already_consumed")
        _require_bool(self.beacon_frozen_due_to_access_expiry, "beacon_frozen_due_to_access_expiry")
        _require_tuple_text(self.evidence_reference_ids, "evidence_reference_ids", unique=True)

        if self.problem_began_while_access_active and self.recovery_obligation_reference_id is None:
            raise ValueError("problem began while access active requires an obligation reference")
        if self.recovery_result_already_consumed and self.recovery_obligation_reference_id is None:
            raise ValueError("consumed recovery results require an obligation reference")


@dataclass(frozen=True, slots=True)
class NotificationEligibilityContext:
    account_id: str
    beacon_id: str | None
    beacon_lifecycle_status: NotificationBeaconLifecycleStatus
    beacon_lifecycle_reference_id: str | None
    entitlement_status: NotificationEntitlementStatus
    entitlement_decision_reference_id: str | None
    no_new_status_preference_enabled: bool
    no_new_status_frequency_minutes: int | None
    channel_evidence: tuple[NotificationChannelEligibilityEvidence, ...]
    recovery_grace_evidence: NotificationRecoveryGraceEvidence
    evidence_reference_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_text(self.account_id, "account_id")
        _require_optional_text(self.beacon_id, "beacon_id")
        if type(self.beacon_lifecycle_status) is not NotificationBeaconLifecycleStatus:
            raise ValueError("beacon_lifecycle_status must be NotificationBeaconLifecycleStatus")
        _require_optional_text(self.beacon_lifecycle_reference_id, "beacon_lifecycle_reference_id")
        if type(self.entitlement_status) is not NotificationEntitlementStatus:
            raise ValueError("entitlement_status must be NotificationEntitlementStatus")
        _require_optional_text(
            self.entitlement_decision_reference_id,
            "entitlement_decision_reference_id",
        )
        _require_bool(self.no_new_status_preference_enabled, "no_new_status_preference_enabled")
        if self.no_new_status_frequency_minutes is not None:
            _require_positive_int(
                self.no_new_status_frequency_minutes,
                "no_new_status_frequency_minutes",
            )
        if type(self.channel_evidence) is not tuple or not self.channel_evidence:
            raise ValueError("channel_evidence must be a non-empty tuple")
        if type(self.recovery_grace_evidence) is not NotificationRecoveryGraceEvidence:
            raise ValueError("recovery_grace_evidence must be NotificationRecoveryGraceEvidence")
        _require_tuple_text(self.evidence_reference_ids, "evidence_reference_ids", unique=True)

        for evidence in self.channel_evidence:
            if type(evidence) is not NotificationChannelEligibilityEvidence:
                raise ValueError(
                    "channel_evidence must contain NotificationChannelEligibilityEvidence"
                )

        channel_classes = tuple(evidence.channel_class for evidence in self.channel_evidence)
        if len(set(channel_classes)) != len(channel_classes):
            raise ValueError("duplicate channel classes are not allowed")
        if channel_classes.count(NotificationChannelClass.WEB_STATUS_READ_MODEL) != 1:
            raise ValueError("exactly one web read model evidence item is required")

        if self.no_new_status_preference_enabled and self.no_new_status_frequency_minutes is None:
            raise ValueError("enabled no-new preference requires a supplied frequency")
        if (
            not self.no_new_status_preference_enabled
            and self.no_new_status_frequency_minutes is not None
        ):
            raise ValueError("disabled no-new preference must not carry a frequency")

        if self.beacon_lifecycle_status is NotificationBeaconLifecycleStatus.NOT_APPLICABLE:
            if self.beacon_id is not None or self.beacon_lifecycle_reference_id is not None:
                raise ValueError("not-applicable beacon lifecycle requires empty beacon scope")
        else:
            if self.beacon_id is None or self.beacon_lifecycle_reference_id is None:
                raise ValueError("beacon lifecycle evidence requires beacon scope references")

        if self.entitlement_status is NotificationEntitlementStatus.NOT_APPLICABLE:
            if self.entitlement_decision_reference_id is not None:
                raise ValueError("not-applicable entitlement must not carry a decision reference")
        else:
            if self.entitlement_decision_reference_id is None:
                raise ValueError("entitlement evidence requires a decision reference")


@dataclass(frozen=True, slots=True)
class NotificationChannelGateDecision:
    channel_class: NotificationChannelClass
    status: NotificationChannelGateStatus
    push_eligible: bool
    target_reference_id: str | None
    reason_codes: tuple[str, ...]
    evidence_reference_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if type(self.channel_class) is not NotificationChannelClass:
            raise ValueError("channel_class must be NotificationChannelClass")
        if type(self.status) is not NotificationChannelGateStatus:
            raise ValueError("status must be NotificationChannelGateStatus")
        _require_bool(self.push_eligible, "push_eligible")
        _require_optional_text(self.target_reference_id, "target_reference_id")
        _require_tuple_text(self.reason_codes, "reason_codes", unique=False)
        if not self.reason_codes:
            raise ValueError("reason_codes must not be empty")
        _require_tuple_text(self.evidence_reference_ids, "evidence_reference_ids", unique=False)

        if self.channel_class is NotificationChannelClass.WEB_STATUS_READ_MODEL:
            if self.status is not NotificationChannelGateStatus.READ_MODEL_ONLY:
                raise ValueError("web read model gates must be read-model-only")
            if self.push_eligible:
                raise ValueError("web read model gates must not be push eligible")
            if self.target_reference_id is not None:
                raise ValueError("web read model gates must not carry a target reference")
            return

        if self.status is NotificationChannelGateStatus.READ_MODEL_ONLY:
            raise ValueError("push channels must not be read-model-only")
        if self.status is NotificationChannelGateStatus.ELIGIBLE:
            if not self.push_eligible:
                raise ValueError("eligible push channels must be push eligible")
            if self.channel_class not in (
                NotificationChannelClass.TELEGRAM,
                NotificationChannelClass.MAX,
            ):
                raise ValueError("eligible push channels must be telegram or max")
            if self.target_reference_id is None:
                raise ValueError("eligible push channels require a target reference")
            return

        if self.push_eligible:
            raise ValueError("non-eligible push channels must not be push eligible")


@dataclass(frozen=True, slots=True)
class NotificationEligibilityDecision:
    decision_id: str
    authority: NotificationEligibilityAuthority
    source_intake_decision: NotificationSourceIntakeDecision
    context: NotificationEligibilityContext
    status: NotificationEligibilityStatus
    source_eligible: bool
    outbox_candidate_eligible: bool
    status_read_model_eligible: bool
    recovery_grace_applied: bool
    eligible_push_channels: tuple[NotificationChannelClass, ...]
    channel_gate_decisions: tuple[NotificationChannelGateDecision, ...]
    outbox_effect_authorized: bool
    delivery_attempt_authorized: bool
    reason_codes: tuple[str, ...]
    evidence_reference_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_text(self.decision_id, "decision_id")
        if type(self.authority) is not NotificationEligibilityAuthority:
            raise ValueError("authority must be NotificationEligibilityAuthority")
        if type(self.source_intake_decision) is not NotificationSourceIntakeDecision:
            raise ValueError("source_intake_decision must be NotificationSourceIntakeDecision")
        if type(self.context) is not NotificationEligibilityContext:
            raise ValueError("context must be NotificationEligibilityContext")
        if type(self.status) is not NotificationEligibilityStatus:
            raise ValueError("status must be NotificationEligibilityStatus")
        _require_bool(self.source_eligible, "source_eligible")
        _require_bool(self.outbox_candidate_eligible, "outbox_candidate_eligible")
        _require_bool(self.status_read_model_eligible, "status_read_model_eligible")
        _require_bool(self.recovery_grace_applied, "recovery_grace_applied")
        if type(self.eligible_push_channels) is not tuple:
            raise ValueError("eligible_push_channels must be a tuple")
        if type(self.channel_gate_decisions) is not tuple:
            raise ValueError("channel_gate_decisions must be a tuple")
        if type(self.outbox_effect_authorized) is not bool:
            raise ValueError("outbox_effect_authorized must be a bool")
        if type(self.delivery_attempt_authorized) is not bool:
            raise ValueError("delivery_attempt_authorized must be a bool")
        _require_tuple_text(self.reason_codes, "reason_codes", unique=False)
        if not self.reason_codes:
            raise ValueError("reason_codes must not be empty")
        _require_tuple_text(self.evidence_reference_ids, "evidence_reference_ids", unique=False)

        for channel_class in self.eligible_push_channels:
            if type(channel_class) is not NotificationChannelClass:
                raise ValueError("eligible_push_channels must contain NotificationChannelClass")
            if channel_class is NotificationChannelClass.WEB_STATUS_READ_MODEL:
                raise ValueError("web read model channels must not be push eligible")

        for gate in self.channel_gate_decisions:
            if type(gate) is not NotificationChannelGateDecision:
                raise ValueError(
                    "channel_gate_decisions must contain NotificationChannelGateDecision"
                )

        if self.outbox_effect_authorized or self.delivery_attempt_authorized:
            raise ValueError("ND-03 decisions must not authorize outbox or delivery attempts")

        push_eligible_gate_channels = tuple(
            gate.channel_class for gate in self.channel_gate_decisions if gate.push_eligible
        )
        if self.eligible_push_channels != push_eligible_gate_channels:
            raise ValueError("eligible push channels must mirror eligible gate decisions")
        if len(set(self.eligible_push_channels)) != len(self.eligible_push_channels):
            raise ValueError("eligible push channels must not contain duplicates")

        if self.status is NotificationEligibilityStatus.ELIGIBLE:
            if not self.source_eligible or not self.outbox_candidate_eligible:
                raise ValueError("eligible decisions must authorize source and outbox eligibility")
            if not self.status_read_model_eligible:
                raise ValueError("eligible decisions must keep the read model eligible")
            if self.recovery_grace_applied:
                raise ValueError("plain eligible decisions must not apply recovery grace")
            if not self.eligible_push_channels:
                raise ValueError("eligible decisions must have at least one push channel")
        elif self.status is NotificationEligibilityStatus.ELIGIBLE_RECOVERY_GRACE:
            if not self.source_eligible or not self.outbox_candidate_eligible:
                raise ValueError("recovery grace decisions must authorize source and outbox")
            if not self.status_read_model_eligible:
                raise ValueError("recovery grace decisions must keep the read model eligible")
            if not self.recovery_grace_applied:
                raise ValueError("recovery grace decisions must mark grace as applied")
            if not self.eligible_push_channels:
                raise ValueError("recovery grace decisions must have at least one push channel")
        elif self.status is NotificationEligibilityStatus.SUPPRESSED_BY_PREFERENCE:
            if not self.source_eligible or self.outbox_candidate_eligible:
                raise ValueError(
                    "suppressed decisions must keep source eligible and outbox blocked"
                )
            if not self.status_read_model_eligible:
                raise ValueError("suppressed decisions must keep the read model eligible")
            if self.recovery_grace_applied:
                raise ValueError("suppressed decisions must not apply recovery grace")
        elif self.status is NotificationEligibilityStatus.BLOCKED_NO_ELIGIBLE_PUSH_CHANNEL:
            if not self.source_eligible or self.outbox_candidate_eligible:
                raise ValueError(
                    "blocked push decisions must keep source eligible and outbox blocked"
                )
            if not self.status_read_model_eligible:
                raise ValueError("blocked push decisions must keep the read model eligible")
            if self.recovery_grace_applied:
                raise ValueError("blocked push decisions must not apply recovery grace")
            if self.eligible_push_channels:
                raise ValueError("blocked push decisions must not expose push channels")
        elif self.status is NotificationEligibilityStatus.STATUS_READ_MODEL_ONLY:
            if not self.source_eligible or self.outbox_candidate_eligible:
                raise ValueError("read-model-only decisions must not authorize outbox")
            if not self.status_read_model_eligible:
                raise ValueError("read-model-only decisions must keep the read model eligible")
            if self.recovery_grace_applied:
                raise ValueError("read-model-only decisions must not apply recovery grace")
            if self.eligible_push_channels:
                raise ValueError("read-model-only decisions must not expose push channels")
        elif self.status is NotificationEligibilityStatus.BLOCKED_SOURCE_INTAKE:
            if (
                self.source_eligible
                or self.outbox_candidate_eligible
                or self.status_read_model_eligible
            ):
                raise ValueError("blocked intake decisions must not authorize any eligibility")
            if self.recovery_grace_applied:
                raise ValueError("blocked intake decisions must not apply recovery grace")
        elif self.status is NotificationEligibilityStatus.BLOCKED_SCOPE_MISMATCH:
            if (
                self.source_eligible
                or self.outbox_candidate_eligible
                or self.status_read_model_eligible
            ):
                raise ValueError("scope mismatches must not authorize any eligibility")
            if self.recovery_grace_applied:
                raise ValueError("scope mismatches must not apply recovery grace")
        elif self.status is NotificationEligibilityStatus.BLOCKED_AMBIGUOUS:
            if (
                self.source_eligible
                or self.outbox_candidate_eligible
                or self.status_read_model_eligible
            ):
                raise ValueError("ambiguous decisions must not authorize any eligibility")
            if self.recovery_grace_applied:
                raise ValueError("ambiguous decisions must not apply recovery grace")
        elif self.status is NotificationEligibilityStatus.BLOCKED_BEACON_LIFECYCLE:
            if self.source_eligible or self.outbox_candidate_eligible:
                raise ValueError("lifecycle blocks must not authorize source or outbox eligibility")
            if not self.status_read_model_eligible:
                raise ValueError("lifecycle blocks must keep the read model eligible")
            if self.recovery_grace_applied:
                raise ValueError("lifecycle blocks must not apply recovery grace")
        elif self.status is NotificationEligibilityStatus.BLOCKED_ENTITLEMENT:
            if self.source_eligible or self.outbox_candidate_eligible:
                raise ValueError(
                    "entitlement blocks must not authorize source or outbox eligibility"
                )
            if not self.status_read_model_eligible:
                raise ValueError("entitlement blocks must keep the read model eligible")
            if self.recovery_grace_applied:
                raise ValueError("entitlement blocks must not apply recovery grace")


def _evaluate_channel_gate(
    evidence: NotificationChannelEligibilityEvidence,
) -> NotificationChannelGateDecision:
    if evidence.channel_class is NotificationChannelClass.WEB_STATUS_READ_MODEL:
        return NotificationChannelGateDecision(
            channel_class=NotificationChannelClass.WEB_STATUS_READ_MODEL,
            status=NotificationChannelGateStatus.READ_MODEL_ONLY,
            push_eligible=False,
            target_reference_id=None,
            reason_codes=("channel-read-model-only",),
            evidence_reference_ids=evidence.evidence_reference_ids,
        )

    if not evidence.enabled_by_user:
        return NotificationChannelGateDecision(
            channel_class=evidence.channel_class,
            status=NotificationChannelGateStatus.DISABLED_BY_USER,
            push_eligible=False,
            target_reference_id=evidence.target_reference_id,
            reason_codes=("channel-disabled-by-user",),
            evidence_reference_ids=evidence.evidence_reference_ids,
        )

    if evidence.target_reference_id is None or not evidence.target_verified:
        return NotificationChannelGateDecision(
            channel_class=evidence.channel_class,
            status=NotificationChannelGateStatus.TARGET_UNVERIFIED,
            push_eligible=False,
            target_reference_id=evidence.target_reference_id,
            reason_codes=("channel-target-unverified",),
            evidence_reference_ids=evidence.evidence_reference_ids,
        )

    if not evidence.target_available:
        return NotificationChannelGateDecision(
            channel_class=evidence.channel_class,
            status=NotificationChannelGateStatus.TARGET_UNAVAILABLE,
            push_eligible=False,
            target_reference_id=evidence.target_reference_id,
            reason_codes=("channel-target-unavailable",),
            evidence_reference_ids=evidence.evidence_reference_ids,
        )

    return NotificationChannelGateDecision(
        channel_class=evidence.channel_class,
        status=NotificationChannelGateStatus.ELIGIBLE,
        push_eligible=True,
        target_reference_id=evidence.target_reference_id,
        reason_codes=("channel-eligible",),
        evidence_reference_ids=evidence.evidence_reference_ids,
    )


def _build_channel_gate_decisions(
    channel_evidence: tuple[NotificationChannelEligibilityEvidence, ...],
) -> tuple[NotificationChannelGateDecision, ...]:
    return tuple(_evaluate_channel_gate(evidence) for evidence in channel_evidence)


def _combine_evidence_reference_ids(
    *,
    evidence_reference_ids: tuple[str, ...],
    source_intake_decision: NotificationSourceIntakeDecision,
    context: NotificationEligibilityContext,
    channel_gate_decisions: tuple[NotificationChannelGateDecision, ...],
) -> tuple[str, ...]:
    combined = (
        evidence_reference_ids
        + context.evidence_reference_ids
        + source_intake_decision.evidence_reference_ids
        + context.recovery_grace_evidence.evidence_reference_ids
    )
    for gate in channel_gate_decisions:
        combined += gate.evidence_reference_ids
    return combined


def _build_decision(
    *,
    decision_id: str,
    source_intake_decision: NotificationSourceIntakeDecision,
    context: NotificationEligibilityContext,
    status: NotificationEligibilityStatus,
    source_eligible: bool,
    outbox_candidate_eligible: bool,
    status_read_model_eligible: bool,
    recovery_grace_applied: bool,
    eligible_push_channels: tuple[NotificationChannelClass, ...],
    channel_gate_decisions: tuple[NotificationChannelGateDecision, ...],
    reason_codes: tuple[str, ...],
    evidence_reference_ids: tuple[str, ...],
) -> NotificationEligibilityDecision:
    return NotificationEligibilityDecision(
        decision_id=decision_id,
        authority=NotificationEligibilityAuthority.NOTIFICATION_DELIVERY_SERVER,
        source_intake_decision=source_intake_decision,
        context=context,
        status=status,
        source_eligible=source_eligible,
        outbox_candidate_eligible=outbox_candidate_eligible,
        status_read_model_eligible=status_read_model_eligible,
        recovery_grace_applied=recovery_grace_applied,
        eligible_push_channels=eligible_push_channels,
        channel_gate_decisions=channel_gate_decisions,
        outbox_effect_authorized=False,
        delivery_attempt_authorized=False,
        reason_codes=reason_codes,
        evidence_reference_ids=evidence_reference_ids,
    )


def evaluate_notification_eligibility(
    *,
    decision_id: str,
    source_intake_decision: NotificationSourceIntakeDecision,
    context: NotificationEligibilityContext,
    evidence_reference_ids: tuple[str, ...],
) -> NotificationEligibilityDecision:
    _require_text(decision_id, "decision_id")
    if type(source_intake_decision) is not NotificationSourceIntakeDecision:
        raise ValueError("source_intake_decision must be NotificationSourceIntakeDecision")
    if type(context) is not NotificationEligibilityContext:
        raise ValueError("context must be NotificationEligibilityContext")
    _require_tuple_text(evidence_reference_ids, "evidence_reference_ids", unique=False)

    source_family = source_intake_decision.source_event.source_family
    if source_family is not NotificationSourceFamily.NO_NEW_LISTINGS_STATUS and (
        context.no_new_status_preference_enabled
        or context.no_new_status_frequency_minutes is not None
    ):
        raise ValueError("non-no-new sources must not carry no-new preference values")

    channel_gate_decisions = _build_channel_gate_decisions(context.channel_evidence)
    eligible_push_channels = tuple(
        gate.channel_class for gate in channel_gate_decisions if gate.push_eligible
    )
    combined_evidence_reference_ids = _combine_evidence_reference_ids(
        evidence_reference_ids=evidence_reference_ids,
        source_intake_decision=source_intake_decision,
        context=context,
        channel_gate_decisions=channel_gate_decisions,
    )

    if (
        source_intake_decision.status
        not in (
            NotificationSourceIntakeStatus.ACCEPTED_NOTIFICATION_CANDIDATE,
            NotificationSourceIntakeStatus.ACCEPTED_STATUS_ONLY,
        )
        or not source_intake_decision.source_accepted
    ):
        return _build_decision(
            decision_id=decision_id,
            source_intake_decision=source_intake_decision,
            context=context,
            status=NotificationEligibilityStatus.BLOCKED_SOURCE_INTAKE,
            source_eligible=False,
            outbox_candidate_eligible=False,
            status_read_model_eligible=False,
            recovery_grace_applied=False,
            eligible_push_channels=eligible_push_channels,
            channel_gate_decisions=channel_gate_decisions,
            reason_codes=("eligibility-source-intake-blocked",),
            evidence_reference_ids=combined_evidence_reference_ids,
        )

    source_event = source_intake_decision.source_event
    if context.account_id != source_event.account_id:
        return _build_decision(
            decision_id=decision_id,
            source_intake_decision=source_intake_decision,
            context=context,
            status=NotificationEligibilityStatus.BLOCKED_SCOPE_MISMATCH,
            source_eligible=False,
            outbox_candidate_eligible=False,
            status_read_model_eligible=False,
            recovery_grace_applied=False,
            eligible_push_channels=eligible_push_channels,
            channel_gate_decisions=channel_gate_decisions,
            reason_codes=("eligibility-account-scope-mismatch",),
            evidence_reference_ids=combined_evidence_reference_ids,
        )

    if source_family is NotificationSourceFamily.APPROVED_SERVICE_ACCESS_FACT:
        if source_event.beacon_id is not None or context.beacon_id is not None:
            return _build_decision(
                decision_id=decision_id,
                source_intake_decision=source_intake_decision,
                context=context,
                status=NotificationEligibilityStatus.BLOCKED_SCOPE_MISMATCH,
                source_eligible=False,
                outbox_candidate_eligible=False,
                status_read_model_eligible=False,
                recovery_grace_applied=False,
                eligible_push_channels=eligible_push_channels,
                channel_gate_decisions=channel_gate_decisions,
                reason_codes=("eligibility-beacon-scope-mismatch",),
                evidence_reference_ids=combined_evidence_reference_ids,
            )
        if (
            context.beacon_lifecycle_status is not NotificationBeaconLifecycleStatus.NOT_APPLICABLE
            or context.beacon_lifecycle_reference_id is not None
            or context.entitlement_status is not NotificationEntitlementStatus.NOT_APPLICABLE
            or context.entitlement_decision_reference_id is not None
        ):
            raise ValueError(
                "service access facts require not-applicable beacon and entitlement state"
            )
        if eligible_push_channels:
            return _build_decision(
                decision_id=decision_id,
                source_intake_decision=source_intake_decision,
                context=context,
                status=NotificationEligibilityStatus.ELIGIBLE,
                source_eligible=True,
                outbox_candidate_eligible=True,
                status_read_model_eligible=True,
                recovery_grace_applied=False,
                eligible_push_channels=eligible_push_channels,
                channel_gate_decisions=channel_gate_decisions,
                reason_codes=("eligibility-service-access-eligible",),
                evidence_reference_ids=combined_evidence_reference_ids,
            )
        return _build_decision(
            decision_id=decision_id,
            source_intake_decision=source_intake_decision,
            context=context,
            status=NotificationEligibilityStatus.BLOCKED_NO_ELIGIBLE_PUSH_CHANNEL,
            source_eligible=True,
            outbox_candidate_eligible=False,
            status_read_model_eligible=True,
            recovery_grace_applied=False,
            eligible_push_channels=eligible_push_channels,
            channel_gate_decisions=channel_gate_decisions,
            reason_codes=("eligibility-no-eligible-push-channel",),
            evidence_reference_ids=combined_evidence_reference_ids,
        )

    if source_event.beacon_id != context.beacon_id:
        return _build_decision(
            decision_id=decision_id,
            source_intake_decision=source_intake_decision,
            context=context,
            status=NotificationEligibilityStatus.BLOCKED_SCOPE_MISMATCH,
            source_eligible=False,
            outbox_candidate_eligible=False,
            status_read_model_eligible=False,
            recovery_grace_applied=False,
            eligible_push_channels=eligible_push_channels,
            channel_gate_decisions=channel_gate_decisions,
            reason_codes=("eligibility-beacon-scope-mismatch",),
            evidence_reference_ids=combined_evidence_reference_ids,
        )

    if (
        context.beacon_lifecycle_status is NotificationBeaconLifecycleStatus.AMBIGUOUS
        or context.entitlement_status is NotificationEntitlementStatus.AMBIGUOUS
        or context.entitlement_status is NotificationEntitlementStatus.CONFLICT
    ):
        return _build_decision(
            decision_id=decision_id,
            source_intake_decision=source_intake_decision,
            context=context,
            status=NotificationEligibilityStatus.BLOCKED_AMBIGUOUS,
            source_eligible=False,
            outbox_candidate_eligible=False,
            status_read_model_eligible=False,
            recovery_grace_applied=False,
            eligible_push_channels=eligible_push_channels,
            channel_gate_decisions=channel_gate_decisions,
            reason_codes=(
                "eligibility-beacon-lifecycle-ambiguous"
                if context.beacon_lifecycle_status is NotificationBeaconLifecycleStatus.AMBIGUOUS
                else "eligibility-entitlement-ambiguous",
            ),
            evidence_reference_ids=combined_evidence_reference_ids,
        )

    if source_family is NotificationSourceFamily.NO_NEW_LISTINGS_STATUS:
        if not context.no_new_status_preference_enabled or (
            context.no_new_status_frequency_minutes is not None
            and context.no_new_status_frequency_minutes < NO_NEW_MINIMUM_FREQUENCY_MINUTES
        ):
            reason_code = (
                "eligibility-no-new-preference-disabled"
                if not context.no_new_status_preference_enabled
                else "eligibility-no-new-frequency-below-minimum"
            )
            return _build_decision(
                decision_id=decision_id,
                source_intake_decision=source_intake_decision,
                context=context,
                status=NotificationEligibilityStatus.SUPPRESSED_BY_PREFERENCE,
                source_eligible=True,
                outbox_candidate_eligible=False,
                status_read_model_eligible=True,
                recovery_grace_applied=False,
                eligible_push_channels=eligible_push_channels,
                channel_gate_decisions=channel_gate_decisions,
                reason_codes=(reason_code,),
                evidence_reference_ids=combined_evidence_reference_ids,
            )

    lifecycle_is_active = (
        context.beacon_lifecycle_status is NotificationBeaconLifecycleStatus.ACTIVE
    )
    lifecycle_allows_recovery = (
        source_family is NotificationSourceFamily.RECOVERY_SCAN_COMPLETED
        and context.beacon_lifecycle_status is NotificationBeaconLifecycleStatus.FROZEN
        and context.recovery_grace_evidence.beacon_frozen_due_to_access_expiry
    )
    if not lifecycle_is_active and not lifecycle_allows_recovery:
        return _build_decision(
            decision_id=decision_id,
            source_intake_decision=source_intake_decision,
            context=context,
            status=NotificationEligibilityStatus.BLOCKED_BEACON_LIFECYCLE,
            source_eligible=False,
            outbox_candidate_eligible=False,
            status_read_model_eligible=True,
            recovery_grace_applied=False,
            eligible_push_channels=eligible_push_channels,
            channel_gate_decisions=channel_gate_decisions,
            reason_codes=("eligibility-beacon-lifecycle-not-active",),
            evidence_reference_ids=combined_evidence_reference_ids,
        )

    entitlement_allows = context.entitlement_status is NotificationEntitlementStatus.ALLOWED
    recovery_grace_allows = (
        source_family is NotificationSourceFamily.RECOVERY_SCAN_COMPLETED
        and context.recovery_grace_evidence.problem_began_while_access_active
        and context.recovery_grace_evidence.recovery_obligation_reference_id is not None
        and not context.recovery_grace_evidence.recovery_result_already_consumed
        and context.entitlement_status
        in (
            NotificationEntitlementStatus.EXPIRED,
            NotificationEntitlementStatus.USER_CHOICE_REQUIRED,
            NotificationEntitlementStatus.FREE_COMPLIANCE_REQUIRED,
        )
        and (
            lifecycle_is_active
            or (
                context.beacon_lifecycle_status is NotificationBeaconLifecycleStatus.FROZEN
                and context.recovery_grace_evidence.beacon_frozen_due_to_access_expiry
            )
        )
    )

    if not entitlement_allows and not recovery_grace_allows:
        return _build_decision(
            decision_id=decision_id,
            source_intake_decision=source_intake_decision,
            context=context,
            status=NotificationEligibilityStatus.BLOCKED_ENTITLEMENT,
            source_eligible=False,
            outbox_candidate_eligible=False,
            status_read_model_eligible=True,
            recovery_grace_applied=False,
            eligible_push_channels=eligible_push_channels,
            channel_gate_decisions=channel_gate_decisions,
            reason_codes=("eligibility-entitlement-not-allowed",),
            evidence_reference_ids=combined_evidence_reference_ids,
        )

    if not eligible_push_channels:
        return _build_decision(
            decision_id=decision_id,
            source_intake_decision=source_intake_decision,
            context=context,
            status=NotificationEligibilityStatus.BLOCKED_NO_ELIGIBLE_PUSH_CHANNEL,
            source_eligible=True,
            outbox_candidate_eligible=False,
            status_read_model_eligible=True,
            recovery_grace_applied=False,
            eligible_push_channels=eligible_push_channels,
            channel_gate_decisions=channel_gate_decisions,
            reason_codes=("eligibility-no-eligible-push-channel",),
            evidence_reference_ids=combined_evidence_reference_ids,
        )

    if recovery_grace_allows:
        return _build_decision(
            decision_id=decision_id,
            source_intake_decision=source_intake_decision,
            context=context,
            status=NotificationEligibilityStatus.ELIGIBLE_RECOVERY_GRACE,
            source_eligible=True,
            outbox_candidate_eligible=True,
            status_read_model_eligible=True,
            recovery_grace_applied=True,
            eligible_push_channels=eligible_push_channels,
            channel_gate_decisions=channel_gate_decisions,
            reason_codes=("eligibility-recovery-grace-applied",),
            evidence_reference_ids=combined_evidence_reference_ids,
        )

    return _build_decision(
        decision_id=decision_id,
        source_intake_decision=source_intake_decision,
        context=context,
        status=NotificationEligibilityStatus.ELIGIBLE,
        source_eligible=True,
        outbox_candidate_eligible=True,
        status_read_model_eligible=True,
        recovery_grace_applied=False,
        eligible_push_channels=eligible_push_channels,
        channel_gate_decisions=channel_gate_decisions,
        reason_codes=("eligibility-eligible",),
        evidence_reference_ids=combined_evidence_reference_ids,
    )


__all__ = (
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
