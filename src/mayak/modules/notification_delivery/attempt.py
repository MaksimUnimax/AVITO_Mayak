from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum

from mayak.platform.idempotency import IdempotencyFingerprint, IdempotencyKey, IdempotencyScope

from .delivery_plan import (
    NotificationDeliveryChannelPlanEntry,
    NotificationDeliveryPlan,
    NotificationDeliveryPlanDecision,
    NotificationDeliveryPlanDecisionStatus,
)
from .eligibility import NotificationChannelClass

ND06_TASK_ID = "ND-06-ATTEMPT-OUTCOME-SEMANTICS-20260715-008"

_ALLOWED_PUSH_CHANNEL_CLASSES = (
    NotificationChannelClass.TELEGRAM,
    NotificationChannelClass.MAX,
)

_PRE_OUTCOME_LIFECYCLE_STATUSES = {
    "NOT_ATTEMPTED",
    "ATTEMPT_PLANNED",
    "ATTEMPT_IN_PROGRESS",
}

_DELIVERED_LIFECYCLE_STATUSES = {
    "PROVIDER_ACCEPTED",
    "DELIVERED_ACCEPTED",
}

_AMBIGUOUS_LIFECYCLE_STATUSES = {
    "DISPATCH_AMBIGUOUS",
    "DELIVERY_AMBIGUOUS",
    "RECONCILIATION_REQUIRED",
}

_IMMEDIATE_FAILURE_LIFECYCLE_STATUSES = {
    "PROVIDER_REJECTED",
    "PROVIDER_UNAVAILABLE",
    "RATE_OR_ACCESS_RESTRICTED",
    "MALFORMED_OR_UNUSABLE_PROVIDER_RESPONSE",
    "DELIVERY_FAILURE",
    "SUPPRESSED_OR_CANCELLED",
    "TARGET_UNAVAILABLE_OR_UNVERIFIED",
}

_POLICY_FAILURE_LIFECYCLE_STATUSES = {
    "FAILED_RETRYABLE_AFTER_POLICY",
    "FAILED_NON_RETRYABLE",
}

_ALL_FAILURE_LIFECYCLE_STATUSES = (
    _IMMEDIATE_FAILURE_LIFECYCLE_STATUSES | _POLICY_FAILURE_LIFECYCLE_STATUSES
)

_AMBIGUOUS_OUTCOME_CLASSES = {
    "DISPATCH_AMBIGUOUS",
    "DELIVERY_AMBIGUOUS",
}

_FAILURE_OUTCOME_CLASSES = {
    "PROVIDER_REJECTED",
    "PROVIDER_UNAVAILABLE",
    "RATE_OR_ACCESS_RESTRICTED",
    "MALFORMED_OR_UNUSABLE_PROVIDER_RESPONSE",
    "DELIVERY_FAILURE",
    "SUPPRESSED_OR_CANCELLED",
    "TARGET_UNAVAILABLE_OR_UNVERIFIED",
}

_REASON_CODES = {
    "attempt-planned",
    "attempt-delivery-plan-blocked",
    "attempt-channel-plan-blocked",
    "provider-outcome-accepted-delivered",
    "provider-outcome-accepted-failure",
    "provider-outcome-accepted-ambiguous",
    "provider-outcome-replayed",
    "provider-outcome-uncommitted",
    "provider-outcome-unsafe-payload",
    "provider-outcome-identity-ambiguous",
    "provider-outcome-scope-mismatch",
    "provider-outcome-state-mismatch",
}

_ATTEMPT_REASON_BY_LIFECYCLE = {
    "NOT_ATTEMPTED": "attempt-planned",
    "ATTEMPT_PLANNED": "attempt-planned",
    "ATTEMPT_IN_PROGRESS": "attempt-planned",
    "PROVIDER_ACCEPTED": "provider-outcome-accepted-delivered",
    "DELIVERED_ACCEPTED": "provider-outcome-accepted-delivered",
    "DISPATCH_AMBIGUOUS": "provider-outcome-accepted-ambiguous",
    "DELIVERY_AMBIGUOUS": "provider-outcome-accepted-ambiguous",
    "RECONCILIATION_REQUIRED": "provider-outcome-accepted-ambiguous",
    "PROVIDER_REJECTED": "provider-outcome-accepted-failure",
    "PROVIDER_UNAVAILABLE": "provider-outcome-accepted-failure",
    "RATE_OR_ACCESS_RESTRICTED": "provider-outcome-accepted-failure",
    "MALFORMED_OR_UNUSABLE_PROVIDER_RESPONSE": "provider-outcome-accepted-failure",
    "DELIVERY_FAILURE": "provider-outcome-accepted-failure",
    "SUPPRESSED_OR_CANCELLED": "provider-outcome-accepted-failure",
    "TARGET_UNAVAILABLE_OR_UNVERIFIED": "provider-outcome-accepted-failure",
    "FAILED_RETRYABLE_AFTER_POLICY": "provider-outcome-accepted-failure",
    "FAILED_NON_RETRYABLE": "provider-outcome-accepted-failure",
}

_ACCEPTANCE_REASON_BY_STATUS = {
    "ACCEPTED_DELIVERED": "provider-outcome-accepted-delivered",
    "ACCEPTED_FAILURE": "provider-outcome-accepted-failure",
    "ACCEPTED_AMBIGUOUS": "provider-outcome-accepted-ambiguous",
    "REPLAYED": "provider-outcome-replayed",
    "REJECTED_UNCOMMITTED": "provider-outcome-uncommitted",
    "REJECTED_UNSAFE_PAYLOAD": "provider-outcome-unsafe-payload",
    "REJECTED_IDENTITY_AMBIGUOUS": "provider-outcome-identity-ambiguous",
    "REJECTED_SCOPE_MISMATCH": "provider-outcome-scope-mismatch",
    "REJECTED_STATE_MISMATCH": "provider-outcome-state-mismatch",
}

_PREFERRED_DELIVERED_STATUS = "DELIVERED_ACCEPTED"
_PREFERRED_RECONCILIATION_STATUS = "RECONCILIATION_REQUIRED"


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


def _require_exact_enum(value: object, enum_cls: type[Enum], field_name: str) -> object:
    if type(value) is not enum_cls:
        raise ValueError(f"{field_name} must be {enum_cls.__name__}")
    return value


def _require_exact_record(value: object, record_cls: type[object], field_name: str) -> object:
    if type(value) is not record_cls:
        raise ValueError(f"{field_name} must be {record_cls.__name__}")
    return value


def _require_text_tuple(
    value: object,
    field_name: str,
    *,
    unique: bool,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value and not allow_empty:
        raise ValueError(f"{field_name} must not be empty")
    validated = tuple(_require_text(item, field_name) for item in value)
    if unique and len(set(validated)) != len(validated):
        raise ValueError(f"{field_name} must not contain duplicate values")
    return validated


def _require_push_channel_class(value: object, field_name: str) -> NotificationChannelClass:
    channel_class: NotificationChannelClass = _require_exact_enum(  # type: ignore[assignment]
        value,
        NotificationChannelClass,
        field_name,
    )
    assert isinstance(channel_class, NotificationChannelClass)
    if channel_class not in _ALLOWED_PUSH_CHANNEL_CLASSES:
        raise ValueError(f"{field_name} must be TELEGRAM or MAX")
    return channel_class


def _tuple_union(*tuples: tuple[str, ...]) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []
    for items in tuples:
        for item in items:
            if item not in seen:
                seen.add(item)
                ordered.append(item)
    return tuple(ordered)


def _require_internal_reason_codes(
    value: object,
    field_name: str,
    *,
    allowed: set[str],
) -> tuple[str, ...]:
    reason_codes = _require_text_tuple(value, field_name, unique=True, allow_empty=False)
    if any(code not in allowed for code in reason_codes):
        raise ValueError(f"{field_name} contains unsupported reason codes")
    return reason_codes


class NotificationAttemptAuthority(str, Enum):
    NOTIFICATION_DELIVERY_SERVER = "NOTIFICATION_DELIVERY_SERVER"


class NotificationAttemptLifecycleStatus(str, Enum):
    NOT_ATTEMPTED = "NOT_ATTEMPTED"
    ATTEMPT_PLANNED = "ATTEMPT_PLANNED"
    ATTEMPT_IN_PROGRESS = "ATTEMPT_IN_PROGRESS"
    DISPATCH_AMBIGUOUS = "DISPATCH_AMBIGUOUS"
    PROVIDER_ACCEPTED = "PROVIDER_ACCEPTED"
    PROVIDER_REJECTED = "PROVIDER_REJECTED"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    RATE_OR_ACCESS_RESTRICTED = "RATE_OR_ACCESS_RESTRICTED"
    MALFORMED_OR_UNUSABLE_PROVIDER_RESPONSE = "MALFORMED_OR_UNUSABLE_PROVIDER_RESPONSE"
    DELIVERY_FAILURE = "DELIVERY_FAILURE"
    DELIVERY_AMBIGUOUS = "DELIVERY_AMBIGUOUS"
    SUPPRESSED_OR_CANCELLED = "SUPPRESSED_OR_CANCELLED"
    TARGET_UNAVAILABLE_OR_UNVERIFIED = "TARGET_UNAVAILABLE_OR_UNVERIFIED"
    RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"
    DELIVERED_ACCEPTED = "DELIVERED_ACCEPTED"
    FAILED_RETRYABLE_AFTER_POLICY = "FAILED_RETRYABLE_AFTER_POLICY"
    FAILED_NON_RETRYABLE = "FAILED_NON_RETRYABLE"


class NotificationAttemptPlanningStatus(str, Enum):
    PLANNED = "PLANNED"
    BLOCKED_DELIVERY_PLAN = "BLOCKED_DELIVERY_PLAN"
    BLOCKED_CHANNEL_PLAN = "BLOCKED_CHANNEL_PLAN"


class NotificationProviderOutcomeClass(str, Enum):
    DISPATCH_AMBIGUOUS = "DISPATCH_AMBIGUOUS"
    PROVIDER_ACCEPTED = "PROVIDER_ACCEPTED"
    PROVIDER_REJECTED = "PROVIDER_REJECTED"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    RATE_OR_ACCESS_RESTRICTED = "RATE_OR_ACCESS_RESTRICTED"
    MALFORMED_OR_UNUSABLE_PROVIDER_RESPONSE = "MALFORMED_OR_UNUSABLE_PROVIDER_RESPONSE"
    DELIVERY_FAILURE = "DELIVERY_FAILURE"
    DELIVERY_AMBIGUOUS = "DELIVERY_AMBIGUOUS"
    SUPPRESSED_OR_CANCELLED = "SUPPRESSED_OR_CANCELLED"
    TARGET_UNAVAILABLE_OR_UNVERIFIED = "TARGET_UNAVAILABLE_OR_UNVERIFIED"


class NotificationProviderOutcomeAcceptanceStatus(str, Enum):
    ACCEPTED_DELIVERED = "ACCEPTED_DELIVERED"
    ACCEPTED_FAILURE = "ACCEPTED_FAILURE"
    ACCEPTED_AMBIGUOUS = "ACCEPTED_AMBIGUOUS"
    REPLAYED = "REPLAYED"
    REJECTED_UNCOMMITTED = "REJECTED_UNCOMMITTED"
    REJECTED_UNSAFE_PAYLOAD = "REJECTED_UNSAFE_PAYLOAD"
    REJECTED_IDENTITY_AMBIGUOUS = "REJECTED_IDENTITY_AMBIGUOUS"
    REJECTED_SCOPE_MISMATCH = "REJECTED_SCOPE_MISMATCH"
    REJECTED_STATE_MISMATCH = "REJECTED_STATE_MISMATCH"


@dataclass(frozen=True, slots=True)
class NotificationAttempt:
    attempt_id: str
    authority: NotificationAttemptAuthority
    delivery_plan_id: str
    outbox_item_id: str
    account_id: str
    beacon_id: str | None
    channel_class: NotificationChannelClass
    target_reference_id: str
    lifecycle_status: NotificationAttemptLifecycleStatus
    idempotency_key: IdempotencyKey
    idempotency_fingerprint: IdempotencyFingerprint
    idempotency_scope: IdempotencyScope
    provider_outcome_reference_id: str | None
    provider_outcome_class: NotificationProviderOutcomeClass | None
    adapter_contract: str | None
    adapter_contract_version: str | None
    provider_safe_delivery_reference: str | None
    egress_correlation_reference: str | None
    provider_reason_codes: tuple[str, ...]
    failure_policy_reference: str | None
    reconciliation_required: bool
    delivery_accepted: bool
    retry_authorized: bool
    dispatch_effect_authorized: bool
    provider_mapping_authorized: bool
    correlation_id: str
    causation_id: str
    reason_codes: tuple[str, ...]
    evidence_reference_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        attempt_id = _require_text(self.attempt_id, "attempt_id")
        authority: NotificationAttemptAuthority = _require_exact_enum(  # type: ignore[assignment]
            self.authority,
            NotificationAttemptAuthority,
            "authority",
        )
        delivery_plan_id = _require_text(self.delivery_plan_id, "delivery_plan_id")
        outbox_item_id = _require_text(self.outbox_item_id, "outbox_item_id")
        account_id = _require_text(self.account_id, "account_id")
        beacon_id = _require_optional_text(self.beacon_id, "beacon_id")
        channel_class: NotificationChannelClass = _require_exact_enum(  # type: ignore[assignment]
            self.channel_class,
            NotificationChannelClass,
            "channel_class",
        )
        target_reference_id = _require_text(self.target_reference_id, "target_reference_id")
        lifecycle_status: NotificationAttemptLifecycleStatus = _require_exact_enum(  # type: ignore[assignment]
            self.lifecycle_status,
            NotificationAttemptLifecycleStatus,
            "lifecycle_status",
        )
        idempotency_key: IdempotencyKey = _require_exact_record(  # type: ignore[assignment]
            self.idempotency_key,
            IdempotencyKey,
            "idempotency_key",
        )
        idempotency_fingerprint: IdempotencyFingerprint = _require_exact_record(  # type: ignore[assignment]
            self.idempotency_fingerprint,
            IdempotencyFingerprint,
            "idempotency_fingerprint",
        )
        idempotency_scope: IdempotencyScope = _require_exact_record(  # type: ignore[assignment]
            self.idempotency_scope,
            IdempotencyScope,
            "idempotency_scope",
        )
        provider_outcome_reference_id = _require_optional_text(
            self.provider_outcome_reference_id,
            "provider_outcome_reference_id",
        )
        provider_outcome_class = (
            None
            if self.provider_outcome_class is None
            else _require_exact_enum(  # type: ignore[assignment]
                self.provider_outcome_class,
                NotificationProviderOutcomeClass,
                "provider_outcome_class",
            )
        )
        adapter_contract = _require_optional_text(self.adapter_contract, "adapter_contract")
        adapter_contract_version = _require_optional_text(
            self.adapter_contract_version,
            "adapter_contract_version",
        )
        provider_safe_delivery_reference = _require_optional_text(
            self.provider_safe_delivery_reference,
            "provider_safe_delivery_reference",
        )
        egress_correlation_reference = _require_optional_text(
            self.egress_correlation_reference,
            "egress_correlation_reference",
        )
        provider_reason_codes = _require_text_tuple(
            self.provider_reason_codes,
            "provider_reason_codes",
            unique=True,
            allow_empty=True,
        )
        failure_policy_reference = _require_optional_text(
            self.failure_policy_reference,
            "failure_policy_reference",
        )
        reconciliation_required = _require_bool(
            self.reconciliation_required, "reconciliation_required"
        )
        delivery_accepted = _require_bool(self.delivery_accepted, "delivery_accepted")
        retry_authorized = _require_bool(self.retry_authorized, "retry_authorized")
        dispatch_effect_authorized = _require_bool(
            self.dispatch_effect_authorized,
            "dispatch_effect_authorized",
        )
        provider_mapping_authorized = _require_bool(
            self.provider_mapping_authorized,
            "provider_mapping_authorized",
        )
        correlation_id = _require_text(self.correlation_id, "correlation_id")
        causation_id = _require_text(self.causation_id, "causation_id")
        reason_codes = _require_internal_reason_codes(
            self.reason_codes,
            "reason_codes",
            allowed=_REASON_CODES,
        )
        evidence_reference_ids = _require_text_tuple(
            self.evidence_reference_ids,
            "evidence_reference_ids",
            unique=True,
            allow_empty=True,
        )

        object.__setattr__(self, "attempt_id", attempt_id)
        object.__setattr__(self, "authority", authority)
        object.__setattr__(self, "delivery_plan_id", delivery_plan_id)
        object.__setattr__(self, "outbox_item_id", outbox_item_id)
        object.__setattr__(self, "account_id", account_id)
        object.__setattr__(self, "beacon_id", beacon_id)
        object.__setattr__(self, "channel_class", channel_class)
        object.__setattr__(self, "target_reference_id", target_reference_id)
        object.__setattr__(self, "lifecycle_status", lifecycle_status)
        object.__setattr__(self, "idempotency_key", idempotency_key)
        object.__setattr__(self, "idempotency_fingerprint", idempotency_fingerprint)
        object.__setattr__(self, "idempotency_scope", idempotency_scope)
        object.__setattr__(self, "provider_outcome_reference_id", provider_outcome_reference_id)
        object.__setattr__(self, "provider_outcome_class", provider_outcome_class)
        object.__setattr__(self, "adapter_contract", adapter_contract)
        object.__setattr__(self, "adapter_contract_version", adapter_contract_version)
        object.__setattr__(
            self, "provider_safe_delivery_reference", provider_safe_delivery_reference
        )
        object.__setattr__(self, "egress_correlation_reference", egress_correlation_reference)
        object.__setattr__(self, "provider_reason_codes", provider_reason_codes)
        object.__setattr__(self, "failure_policy_reference", failure_policy_reference)
        object.__setattr__(self, "reconciliation_required", reconciliation_required)
        object.__setattr__(self, "delivery_accepted", delivery_accepted)
        object.__setattr__(self, "retry_authorized", retry_authorized)
        object.__setattr__(self, "dispatch_effect_authorized", dispatch_effect_authorized)
        object.__setattr__(self, "provider_mapping_authorized", provider_mapping_authorized)
        object.__setattr__(self, "correlation_id", correlation_id)
        object.__setattr__(self, "causation_id", causation_id)
        object.__setattr__(self, "reason_codes", reason_codes)
        object.__setattr__(self, "evidence_reference_ids", evidence_reference_ids)

        if authority is not NotificationAttemptAuthority.NOTIFICATION_DELIVERY_SERVER:
            raise ValueError("authority must be NOTIFICATION_DELIVERY_SERVER")
        if retry_authorized or dispatch_effect_authorized or provider_mapping_authorized:
            raise ValueError("attempts must not authorize retry, dispatch, or provider mapping")

        if provider_outcome_class is None:
            if provider_outcome_reference_id is not None:
                raise ValueError("provider outcome metadata must be unset before acceptance")
            if adapter_contract is not None or adapter_contract_version is not None:
                raise ValueError("adapter contract metadata must be unset before acceptance")
            if provider_safe_delivery_reference is not None:
                raise ValueError("provider_safe_delivery_reference must be unset before acceptance")
            if egress_correlation_reference is not None:
                raise ValueError("egress_correlation_reference must be unset before acceptance")
            if provider_reason_codes:
                raise ValueError("provider_reason_codes must be empty before acceptance")
            if failure_policy_reference is not None:
                raise ValueError("failure_policy_reference must be unset before acceptance")
            if delivery_accepted or reconciliation_required:
                raise ValueError("pre-acceptance attempts must not be delivered or reconciled")
            if lifecycle_status.value not in _PRE_OUTCOME_LIFECYCLE_STATUSES:
                raise ValueError("pre-acceptance attempts must stay in a pre-outcome lifecycle")
            if reason_codes != ("attempt-planned",):
                raise ValueError("pre-acceptance attempts require attempt-planned")
            return

        assert isinstance(provider_outcome_class, NotificationProviderOutcomeClass)

        if provider_outcome_reference_id is None:
            raise ValueError("provider outcome metadata requires a reference id")
        if adapter_contract is None or adapter_contract_version is None:
            raise ValueError("provider outcome metadata requires adapter contract details")
        if lifecycle_status.value in _PRE_OUTCOME_LIFECYCLE_STATUSES:
            raise ValueError("accepted provider outcomes must not remain pre-outcome")

        if lifecycle_status.value in _DELIVERED_LIFECYCLE_STATUSES:
            if provider_outcome_class is not NotificationProviderOutcomeClass.PROVIDER_ACCEPTED:
                raise ValueError("delivered attempts require PROVIDER_ACCEPTED")
            if provider_safe_delivery_reference is None:
                raise ValueError("delivered attempts require a safe delivery reference")
            if delivery_accepted is not True or reconciliation_required is not False:
                raise ValueError("delivered attempts must be accepted without reconciliation")
            if reason_codes != ("provider-outcome-accepted-delivered",):
                raise ValueError("delivered attempts require provider-outcome-accepted-delivered")
            return

        if lifecycle_status.value in _AMBIGUOUS_LIFECYCLE_STATUSES:
            if provider_outcome_class not in {
                NotificationProviderOutcomeClass.DISPATCH_AMBIGUOUS,
                NotificationProviderOutcomeClass.DELIVERY_AMBIGUOUS,
            }:
                raise ValueError("ambiguous attempts require an ambiguous provider outcome")
            if delivery_accepted is not False or reconciliation_required is not True:
                raise ValueError("ambiguous attempts require reconciliation without delivery")
            if reason_codes != ("provider-outcome-accepted-ambiguous",):
                raise ValueError("ambiguous attempts require provider-outcome-accepted-ambiguous")
            return

        if lifecycle_status.value in _IMMEDIATE_FAILURE_LIFECYCLE_STATUSES:
            if (
                provider_outcome_class is None
                or provider_outcome_class.value != lifecycle_status.value
            ):
                raise ValueError("failure attempts require matching provider outcome classes")
            if delivery_accepted or reconciliation_required:
                raise ValueError("failure attempts must not be delivered or reconciled")
            if failure_policy_reference is not None:
                raise ValueError("failure attempts must not carry a failure policy reference")
            if reason_codes != ("provider-outcome-accepted-failure",):
                raise ValueError("failure attempts require provider-outcome-accepted-failure")
            return

        if lifecycle_status.value in _POLICY_FAILURE_LIFECYCLE_STATUSES:
            if (
                provider_outcome_class is None
                or provider_outcome_class.value not in _FAILURE_OUTCOME_CLASSES
            ):
                raise ValueError("policy failures require a failure provider outcome")
            if failure_policy_reference is None:
                raise ValueError("policy failures require a failure policy reference")
            if delivery_accepted or reconciliation_required:
                raise ValueError("policy failures must not be delivered or reconciled")
            if reason_codes != ("provider-outcome-accepted-failure",):
                raise ValueError("policy failures require provider-outcome-accepted-failure")
            return

        if lifecycle_status.value == _PREFERRED_RECONCILIATION_STATUS:
            if provider_outcome_class not in {
                NotificationProviderOutcomeClass.DISPATCH_AMBIGUOUS,
                NotificationProviderOutcomeClass.DELIVERY_AMBIGUOUS,
            }:
                raise ValueError("reconciliation attempts require an ambiguous provider outcome")
            if not reconciliation_required or delivery_accepted:
                raise ValueError("reconciliation attempts must require reconciliation only")
            if reason_codes != ("provider-outcome-accepted-ambiguous",):
                raise ValueError(
                    "reconciliation attempts require provider-outcome-accepted-ambiguous"
                )
            return

        if lifecycle_status.value == "PROVIDER_ACCEPTED":
            if provider_outcome_class is not NotificationProviderOutcomeClass.PROVIDER_ACCEPTED:
                raise ValueError("PROVIDER_ACCEPTED attempts require PROVIDER_ACCEPTED outcomes")
            if (
                provider_safe_delivery_reference is None
                or not delivery_accepted
                or reconciliation_required
            ):
                raise ValueError("PROVIDER_ACCEPTED attempts require delivery acceptance")
            if reason_codes != ("provider-outcome-accepted-delivered",):
                raise ValueError(
                    "PROVIDER_ACCEPTED attempts require provider-outcome-accepted-delivered"
                )
            return

        raise ValueError("unsupported lifecycle status")


@dataclass(frozen=True, slots=True)
class NotificationAttemptPlanningDecision:
    decision_id: str
    authority: NotificationAttemptAuthority
    delivery_plan_decision: NotificationDeliveryPlanDecision
    channel_class: NotificationChannelClass
    status: NotificationAttemptPlanningStatus
    attempt: NotificationAttempt | None
    attempt_created: bool
    dispatch_effect_authorized: bool
    provider_mapping_authorized: bool
    reason_codes: tuple[str, ...]
    evidence_reference_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        decision_id = _require_text(self.decision_id, "decision_id")
        authority: NotificationAttemptAuthority = _require_exact_enum(  # type: ignore[assignment]
            self.authority,
            NotificationAttemptAuthority,
            "authority",
        )
        assert isinstance(authority, NotificationAttemptAuthority)
        delivery_plan_decision: NotificationDeliveryPlanDecision = _require_exact_record(  # type: ignore[assignment]
            self.delivery_plan_decision,
            NotificationDeliveryPlanDecision,
            "delivery_plan_decision",
        )
        assert isinstance(delivery_plan_decision, NotificationDeliveryPlanDecision)
        channel_class: NotificationChannelClass = _require_exact_enum(  # type: ignore[assignment]
            self.channel_class,
            NotificationChannelClass,
            "channel_class",
        )
        assert isinstance(channel_class, NotificationChannelClass)
        status: NotificationAttemptPlanningStatus = _require_exact_enum(  # type: ignore[assignment]
            self.status,
            NotificationAttemptPlanningStatus,
            "status",
        )
        assert isinstance(status, NotificationAttemptPlanningStatus)
        if self.attempt is not None and type(self.attempt) is not NotificationAttempt:
            raise ValueError("attempt must be NotificationAttempt | None")
        attempt_created = _require_bool(self.attempt_created, "attempt_created")
        dispatch_effect_authorized = _require_bool(
            self.dispatch_effect_authorized,
            "dispatch_effect_authorized",
        )
        provider_mapping_authorized = _require_bool(
            self.provider_mapping_authorized,
            "provider_mapping_authorized",
        )
        reason_codes = _require_internal_reason_codes(
            self.reason_codes,
            "reason_codes",
            allowed={
                "attempt-planned",
                "attempt-delivery-plan-blocked",
                "attempt-channel-plan-blocked",
            },
        )
        evidence_reference_ids = _require_text_tuple(
            self.evidence_reference_ids,
            "evidence_reference_ids",
            unique=True,
            allow_empty=True,
        )

        object.__setattr__(self, "decision_id", decision_id)
        object.__setattr__(self, "authority", authority)
        object.__setattr__(self, "delivery_plan_decision", delivery_plan_decision)
        object.__setattr__(self, "channel_class", channel_class)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "attempt", self.attempt)
        object.__setattr__(self, "attempt_created", attempt_created)
        object.__setattr__(self, "dispatch_effect_authorized", dispatch_effect_authorized)
        object.__setattr__(self, "provider_mapping_authorized", provider_mapping_authorized)
        object.__setattr__(self, "reason_codes", reason_codes)
        object.__setattr__(self, "evidence_reference_ids", evidence_reference_ids)

        if authority is not NotificationAttemptAuthority.NOTIFICATION_DELIVERY_SERVER:
            raise ValueError("authority must be NOTIFICATION_DELIVERY_SERVER")
        if dispatch_effect_authorized or provider_mapping_authorized:
            raise ValueError("attempt planning decisions must not authorize execution")

        if status is NotificationAttemptPlanningStatus.PLANNED:
            if channel_class not in _ALLOWED_PUSH_CHANNEL_CLASSES:
                raise ValueError("planned attempts require TELEGRAM or MAX channels")
            if not attempt_created or self.attempt is None:
                raise ValueError("planned attempts require an attempt record")
            if reason_codes != ("attempt-planned",):
                raise ValueError("planned attempts require attempt-planned")
            return

        if attempt_created or self.attempt is not None:
            raise ValueError("blocked attempt planning decisions must not carry an attempt")
        if status is NotificationAttemptPlanningStatus.BLOCKED_DELIVERY_PLAN:
            if reason_codes != ("attempt-delivery-plan-blocked",):
                raise ValueError(
                    "blocked delivery plan decisions require attempt-delivery-plan-blocked"
                )
            return
        if status is NotificationAttemptPlanningStatus.BLOCKED_CHANNEL_PLAN:
            if reason_codes != ("attempt-channel-plan-blocked",):
                raise ValueError(
                    "blocked channel plan decisions require attempt-channel-plan-blocked"
                )
            return

        raise ValueError("unsupported planning status")


@dataclass(frozen=True, slots=True)
class NotificationProviderOutcomeReference:
    outcome_reference_id: str
    adapter_contract: str
    adapter_contract_version: str
    attempt_id: str
    channel_class: NotificationChannelClass
    target_reference_id: str
    outcome_class: NotificationProviderOutcomeClass
    adapter_outcome_committed: bool
    provider_safe_delivery_reference: str | None
    egress_correlation_reference: str | None
    contains_raw_provider_payload: bool
    identity_ambiguous: bool
    correlation_id: str
    causation_id: str
    reason_codes: tuple[str, ...]
    evidence_reference_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        outcome_reference_id = _require_text(self.outcome_reference_id, "outcome_reference_id")
        adapter_contract = _require_text(self.adapter_contract, "adapter_contract")
        adapter_contract_version = _require_text(
            self.adapter_contract_version, "adapter_contract_version"
        )
        attempt_id = _require_text(self.attempt_id, "attempt_id")
        channel_class = _require_push_channel_class(self.channel_class, "channel_class")
        target_reference_id = _require_text(self.target_reference_id, "target_reference_id")
        outcome_class: NotificationProviderOutcomeClass = _require_exact_enum(  # type: ignore[assignment]
            self.outcome_class,
            NotificationProviderOutcomeClass,
            "outcome_class",
        )
        assert isinstance(outcome_class, NotificationProviderOutcomeClass)
        adapter_outcome_committed = _require_bool(
            self.adapter_outcome_committed,
            "adapter_outcome_committed",
        )
        provider_safe_delivery_reference = _require_optional_text(
            self.provider_safe_delivery_reference,
            "provider_safe_delivery_reference",
        )
        egress_correlation_reference = _require_optional_text(
            self.egress_correlation_reference,
            "egress_correlation_reference",
        )
        contains_raw_provider_payload = _require_bool(
            self.contains_raw_provider_payload,
            "contains_raw_provider_payload",
        )
        identity_ambiguous = _require_bool(self.identity_ambiguous, "identity_ambiguous")
        correlation_id = _require_text(self.correlation_id, "correlation_id")
        causation_id = _require_text(self.causation_id, "causation_id")
        reason_codes = _require_text_tuple(
            self.reason_codes,
            "reason_codes",
            unique=True,
            allow_empty=True,
        )
        evidence_reference_ids = _require_text_tuple(
            self.evidence_reference_ids,
            "evidence_reference_ids",
            unique=True,
            allow_empty=True,
        )

        object.__setattr__(self, "outcome_reference_id", outcome_reference_id)
        object.__setattr__(self, "adapter_contract", adapter_contract)
        object.__setattr__(self, "adapter_contract_version", adapter_contract_version)
        object.__setattr__(self, "attempt_id", attempt_id)
        object.__setattr__(self, "channel_class", channel_class)
        object.__setattr__(self, "target_reference_id", target_reference_id)
        object.__setattr__(self, "outcome_class", outcome_class)
        object.__setattr__(self, "adapter_outcome_committed", adapter_outcome_committed)
        object.__setattr__(
            self, "provider_safe_delivery_reference", provider_safe_delivery_reference
        )
        object.__setattr__(self, "egress_correlation_reference", egress_correlation_reference)
        object.__setattr__(self, "contains_raw_provider_payload", contains_raw_provider_payload)
        object.__setattr__(self, "identity_ambiguous", identity_ambiguous)
        object.__setattr__(self, "correlation_id", correlation_id)
        object.__setattr__(self, "causation_id", causation_id)
        object.__setattr__(self, "reason_codes", reason_codes)
        object.__setattr__(self, "evidence_reference_ids", evidence_reference_ids)

        if adapter_outcome_committed is not True:
            return


@dataclass(frozen=True, slots=True)
class NotificationProviderOutcomeAcceptanceDecision:
    decision_id: str
    authority: NotificationAttemptAuthority
    previous_attempt: NotificationAttempt
    provider_outcome: NotificationProviderOutcomeReference
    status: NotificationProviderOutcomeAcceptanceStatus
    resulting_attempt: NotificationAttempt | None
    outcome_accepted: bool
    replayed: bool
    delivery_accepted: bool
    reconciliation_required: bool
    retry_authorized: bool
    dispatch_effect_authorized: bool
    provider_mapping_authorized: bool
    reason_codes: tuple[str, ...]
    evidence_reference_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        decision_id = _require_text(self.decision_id, "decision_id")
        authority: NotificationAttemptAuthority = _require_exact_enum(  # type: ignore[assignment]
            self.authority,
            NotificationAttemptAuthority,
            "authority",
        )
        assert isinstance(authority, NotificationAttemptAuthority)
        previous_attempt: NotificationAttempt = _require_exact_record(  # type: ignore[assignment]
            self.previous_attempt,
            NotificationAttempt,
            "previous_attempt",
        )
        assert isinstance(previous_attempt, NotificationAttempt)
        provider_outcome: NotificationProviderOutcomeReference = _require_exact_record(  # type: ignore[assignment]
            self.provider_outcome,
            NotificationProviderOutcomeReference,
            "provider_outcome",
        )
        assert isinstance(provider_outcome, NotificationProviderOutcomeReference)
        status: NotificationProviderOutcomeAcceptanceStatus = _require_exact_enum(  # type: ignore[assignment]
            self.status,
            NotificationProviderOutcomeAcceptanceStatus,
            "status",
        )
        assert isinstance(status, NotificationProviderOutcomeAcceptanceStatus)
        if (
            self.resulting_attempt is not None
            and type(self.resulting_attempt) is not NotificationAttempt
        ):
            raise ValueError("resulting_attempt must be NotificationAttempt | None")
        outcome_accepted = _require_bool(self.outcome_accepted, "outcome_accepted")
        replayed = _require_bool(self.replayed, "replayed")
        delivery_accepted = _require_bool(self.delivery_accepted, "delivery_accepted")
        reconciliation_required = _require_bool(
            self.reconciliation_required,
            "reconciliation_required",
        )
        retry_authorized = _require_bool(self.retry_authorized, "retry_authorized")
        dispatch_effect_authorized = _require_bool(
            self.dispatch_effect_authorized,
            "dispatch_effect_authorized",
        )
        provider_mapping_authorized = _require_bool(
            self.provider_mapping_authorized,
            "provider_mapping_authorized",
        )
        reason_codes = _require_internal_reason_codes(
            self.reason_codes,
            "reason_codes",
            allowed=set(_ACCEPTANCE_REASON_BY_STATUS.values()),
        )
        evidence_reference_ids = _require_text_tuple(
            self.evidence_reference_ids,
            "evidence_reference_ids",
            unique=True,
            allow_empty=True,
        )

        object.__setattr__(self, "decision_id", decision_id)
        object.__setattr__(self, "authority", authority)
        object.__setattr__(self, "previous_attempt", previous_attempt)
        object.__setattr__(self, "provider_outcome", provider_outcome)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "resulting_attempt", self.resulting_attempt)
        object.__setattr__(self, "outcome_accepted", outcome_accepted)
        object.__setattr__(self, "replayed", replayed)
        object.__setattr__(self, "delivery_accepted", delivery_accepted)
        object.__setattr__(self, "reconciliation_required", reconciliation_required)
        object.__setattr__(self, "retry_authorized", retry_authorized)
        object.__setattr__(self, "dispatch_effect_authorized", dispatch_effect_authorized)
        object.__setattr__(self, "provider_mapping_authorized", provider_mapping_authorized)
        object.__setattr__(self, "reason_codes", reason_codes)
        object.__setattr__(self, "evidence_reference_ids", evidence_reference_ids)

        if authority is not NotificationAttemptAuthority.NOTIFICATION_DELIVERY_SERVER:
            raise ValueError("authority must be NOTIFICATION_DELIVERY_SERVER")
        if retry_authorized or dispatch_effect_authorized or provider_mapping_authorized:
            raise ValueError("provider outcome decisions must not authorize execution")

        if status is NotificationProviderOutcomeAcceptanceStatus.REPLAYED:
            if not outcome_accepted or not replayed:
                raise ValueError("replayed decisions must be accepted and replayed")
            if self.resulting_attempt is not previous_attempt:
                raise ValueError("replayed decisions must return the previous attempt")
            if reason_codes != ("provider-outcome-replayed",):
                raise ValueError("replayed decisions require provider-outcome-replayed")
            return

        if status is NotificationProviderOutcomeAcceptanceStatus.REJECTED_UNCOMMITTED:
            if outcome_accepted or replayed or self.resulting_attempt is not None:
                raise ValueError("uncommitted rejections must not carry a resulting attempt")
            if reason_codes != ("provider-outcome-uncommitted",):
                raise ValueError("uncommitted rejections require provider-outcome-uncommitted")
            if delivery_accepted or reconciliation_required:
                raise ValueError("rejections must not be delivered or reconciled")
            return

        if status is NotificationProviderOutcomeAcceptanceStatus.REJECTED_UNSAFE_PAYLOAD:
            if outcome_accepted or replayed or self.resulting_attempt is not None:
                raise ValueError("unsafe payload rejections must not carry a resulting attempt")
            if reason_codes != ("provider-outcome-unsafe-payload",):
                raise ValueError(
                    "unsafe payload rejections require provider-outcome-unsafe-payload"
                )
            if delivery_accepted or reconciliation_required:
                raise ValueError("rejections must not be delivered or reconciled")
            return

        if status is NotificationProviderOutcomeAcceptanceStatus.REJECTED_IDENTITY_AMBIGUOUS:
            if outcome_accepted or replayed or self.resulting_attempt is not None:
                raise ValueError("identity ambiguous rejections must not carry a resulting attempt")
            if reason_codes != ("provider-outcome-identity-ambiguous",):
                raise ValueError(
                    "identity ambiguous rejections require provider-outcome-identity-ambiguous"
                )
            if delivery_accepted or reconciliation_required:
                raise ValueError("rejections must not be delivered or reconciled")
            return

        if status is NotificationProviderOutcomeAcceptanceStatus.REJECTED_SCOPE_MISMATCH:
            if outcome_accepted or replayed or self.resulting_attempt is not None:
                raise ValueError("scope mismatch rejections must not carry a resulting attempt")
            if reason_codes != ("provider-outcome-scope-mismatch",):
                raise ValueError(
                    "scope mismatch rejections require provider-outcome-scope-mismatch"
                )
            if delivery_accepted or reconciliation_required:
                raise ValueError("rejections must not be delivered or reconciled")
            return

        if status is NotificationProviderOutcomeAcceptanceStatus.REJECTED_STATE_MISMATCH:
            if outcome_accepted or replayed or self.resulting_attempt is not None:
                raise ValueError("state mismatch rejections must not carry a resulting attempt")
            if reason_codes != ("provider-outcome-state-mismatch",):
                raise ValueError(
                    "state mismatch rejections require provider-outcome-state-mismatch"
                )
            if delivery_accepted or reconciliation_required:
                raise ValueError("rejections must not be delivered or reconciled")
            return

        if replayed or self.resulting_attempt is None or not outcome_accepted:
            raise ValueError("accepted decisions must carry a resulting attempt")

        if status is NotificationProviderOutcomeAcceptanceStatus.ACCEPTED_DELIVERED:
            if reason_codes != ("provider-outcome-accepted-delivered",):
                raise ValueError("delivered outcomes require provider-outcome-accepted-delivered")
            if not delivery_accepted or reconciliation_required:
                raise ValueError("delivered outcomes must be accepted without reconciliation")
            return

        if status is NotificationProviderOutcomeAcceptanceStatus.ACCEPTED_AMBIGUOUS:
            if reason_codes != ("provider-outcome-accepted-ambiguous",):
                raise ValueError("ambiguous outcomes require provider-outcome-accepted-ambiguous")
            if delivery_accepted or not reconciliation_required:
                raise ValueError("ambiguous outcomes require reconciliation without delivery")
            return

        if status is NotificationProviderOutcomeAcceptanceStatus.ACCEPTED_FAILURE:
            if reason_codes != ("provider-outcome-accepted-failure",):
                raise ValueError("failure outcomes require provider-outcome-accepted-failure")
            if delivery_accepted or reconciliation_required:
                raise ValueError("failure outcomes must not be delivered or reconciled")
            return

        raise ValueError("unsupported acceptance status")


def _plan_attempt_reason_codes() -> tuple[str, ...]:
    return ("attempt-planned",)


def _blocked_delivery_plan_reason_codes() -> tuple[str, ...]:
    return ("attempt-delivery-plan-blocked",)


def _blocked_channel_plan_reason_codes() -> tuple[str, ...]:
    return ("attempt-channel-plan-blocked",)


def _accepted_delivered_reason_codes() -> tuple[str, ...]:
    return ("provider-outcome-accepted-delivered",)


def _accepted_failure_reason_codes() -> tuple[str, ...]:
    return ("provider-outcome-accepted-failure",)


def _accepted_ambiguous_reason_codes() -> tuple[str, ...]:
    return ("provider-outcome-accepted-ambiguous",)


def _replayed_reason_codes() -> tuple[str, ...]:
    return ("provider-outcome-replayed",)


def _rejected_uncommitted_reason_codes() -> tuple[str, ...]:
    return ("provider-outcome-uncommitted",)


def _rejected_unsafe_payload_reason_codes() -> tuple[str, ...]:
    return ("provider-outcome-unsafe-payload",)


def _rejected_identity_ambiguous_reason_codes() -> tuple[str, ...]:
    return ("provider-outcome-identity-ambiguous",)


def _rejected_scope_mismatch_reason_codes() -> tuple[str, ...]:
    return ("provider-outcome-scope-mismatch",)


def _rejected_state_mismatch_reason_codes() -> tuple[str, ...]:
    return ("provider-outcome-state-mismatch",)


def _attempt_reason_codes_for_lifecycle(
    lifecycle_status: NotificationAttemptLifecycleStatus,
) -> tuple[str, ...]:
    reason_code = _ATTEMPT_REASON_BY_LIFECYCLE[lifecycle_status.value]
    return (reason_code,)


def _accepted_lifecycle_for_outcome_class(
    outcome_class: NotificationProviderOutcomeClass,
) -> NotificationAttemptLifecycleStatus:
    if outcome_class is NotificationProviderOutcomeClass.PROVIDER_ACCEPTED:
        return NotificationAttemptLifecycleStatus.DELIVERED_ACCEPTED
    if outcome_class in {
        NotificationProviderOutcomeClass.DISPATCH_AMBIGUOUS,
        NotificationProviderOutcomeClass.DELIVERY_AMBIGUOUS,
    }:
        return NotificationAttemptLifecycleStatus.RECONCILIATION_REQUIRED
    if outcome_class in {
        NotificationProviderOutcomeClass.PROVIDER_REJECTED,
        NotificationProviderOutcomeClass.PROVIDER_UNAVAILABLE,
        NotificationProviderOutcomeClass.RATE_OR_ACCESS_RESTRICTED,
        NotificationProviderOutcomeClass.MALFORMED_OR_UNUSABLE_PROVIDER_RESPONSE,
        NotificationProviderOutcomeClass.DELIVERY_FAILURE,
        NotificationProviderOutcomeClass.SUPPRESSED_OR_CANCELLED,
        NotificationProviderOutcomeClass.TARGET_UNAVAILABLE_OR_UNVERIFIED,
    }:
        return NotificationAttemptLifecycleStatus(outcome_class.value)
    raise ValueError("unsupported provider outcome class")


def _build_planned_attempt(
    *,
    attempt_id: str,
    delivery_plan: NotificationDeliveryPlan,
    channel_class: NotificationChannelClass,
    target_reference_id: str,
    idempotency_key: IdempotencyKey,
    idempotency_fingerprint: IdempotencyFingerprint,
    idempotency_scope: IdempotencyScope,
    evidence_reference_ids: tuple[str, ...],
) -> NotificationAttempt:
    outbox_item = delivery_plan.outbox_item
    return NotificationAttempt(
        attempt_id=attempt_id,
        authority=NotificationAttemptAuthority.NOTIFICATION_DELIVERY_SERVER,
        delivery_plan_id=delivery_plan.delivery_plan_id,
        outbox_item_id=outbox_item.outbox_item_id,
        account_id=outbox_item.account_id,
        beacon_id=outbox_item.beacon_id,
        channel_class=channel_class,
        target_reference_id=target_reference_id,
        lifecycle_status=NotificationAttemptLifecycleStatus.ATTEMPT_PLANNED,
        idempotency_key=idempotency_key,
        idempotency_fingerprint=idempotency_fingerprint,
        idempotency_scope=idempotency_scope,
        provider_outcome_reference_id=None,
        provider_outcome_class=None,
        adapter_contract=None,
        adapter_contract_version=None,
        provider_safe_delivery_reference=None,
        egress_correlation_reference=None,
        provider_reason_codes=(),
        failure_policy_reference=None,
        reconciliation_required=False,
        delivery_accepted=False,
        retry_authorized=False,
        dispatch_effect_authorized=False,
        provider_mapping_authorized=False,
        correlation_id=outbox_item.correlation_id,
        causation_id=outbox_item.causation_id,
        reason_codes=_plan_attempt_reason_codes(),
        evidence_reference_ids=evidence_reference_ids,
    )


def _is_delivery_plan_eligible_for_attempt(
    delivery_plan_decision: NotificationDeliveryPlanDecision,
) -> bool:
    return (
        delivery_plan_decision.status is NotificationDeliveryPlanDecisionStatus.PLANNED
        and delivery_plan_decision.delivery_plan is not None
    )


def _channel_entry_by_class(
    delivery_plan: NotificationDeliveryPlan,
    channel_class: NotificationChannelClass,
) -> NotificationDeliveryChannelPlanEntry | None:
    for entry in delivery_plan.channel_entries:
        if entry.channel_class is channel_class:
            return entry
    return None


def plan_notification_attempt(
    *,
    decision_id: str,
    attempt_id: str,
    delivery_plan_decision: NotificationDeliveryPlanDecision,
    channel_class: NotificationChannelClass,
    idempotency_key: IdempotencyKey,
    idempotency_fingerprint: IdempotencyFingerprint,
    idempotency_scope: IdempotencyScope,
    evidence_reference_ids: tuple[str, ...],
) -> NotificationAttemptPlanningDecision:
    _require_text(decision_id, "decision_id")
    _require_text(attempt_id, "attempt_id")
    if type(delivery_plan_decision) is not NotificationDeliveryPlanDecision:
        raise ValueError("delivery_plan_decision must be NotificationDeliveryPlanDecision")
    validated_channel_class: NotificationChannelClass = _require_exact_enum(  # type: ignore[assignment]
        channel_class,
        NotificationChannelClass,
        "channel_class",
    )
    assert isinstance(validated_channel_class, NotificationChannelClass)
    _require_exact_record(idempotency_key, IdempotencyKey, "idempotency_key")
    _require_exact_record(
        idempotency_fingerprint, IdempotencyFingerprint, "idempotency_fingerprint"
    )
    _require_exact_record(idempotency_scope, IdempotencyScope, "idempotency_scope")
    _require_text_tuple(
        evidence_reference_ids, "evidence_reference_ids", unique=True, allow_empty=True
    )

    if not _is_delivery_plan_eligible_for_attempt(delivery_plan_decision):
        return NotificationAttemptPlanningDecision(
            decision_id=decision_id,
            authority=NotificationAttemptAuthority.NOTIFICATION_DELIVERY_SERVER,
            delivery_plan_decision=delivery_plan_decision,
            channel_class=validated_channel_class,
            status=NotificationAttemptPlanningStatus.BLOCKED_DELIVERY_PLAN,
            attempt=None,
            attempt_created=False,
            dispatch_effect_authorized=False,
            provider_mapping_authorized=False,
            reason_codes=_blocked_delivery_plan_reason_codes(),
            evidence_reference_ids=_tuple_union(
                delivery_plan_decision.evidence_reference_ids, evidence_reference_ids
            ),
        )

    delivery_plan = delivery_plan_decision.delivery_plan
    assert delivery_plan is not None
    entry = _channel_entry_by_class(delivery_plan, validated_channel_class)
    if entry is None:
        blocked = True
    else:
        blocked = not (
            validated_channel_class in _ALLOWED_PUSH_CHANNEL_CLASSES
            and entry.push_planned is True
            and entry.target_reference_id is not None
            and entry.status.value in {"TELEGRAM_ENABLED", "MAX_ENABLED"}
            and entry.outbox_channel_intent is not None
            and entry.outbox_channel_intent.channel_class is validated_channel_class
            and entry.outbox_channel_intent.target_reference_id == entry.target_reference_id
        )

    if blocked:
        return NotificationAttemptPlanningDecision(
            decision_id=decision_id,
            authority=NotificationAttemptAuthority.NOTIFICATION_DELIVERY_SERVER,
            delivery_plan_decision=delivery_plan_decision,
            channel_class=validated_channel_class,
            status=NotificationAttemptPlanningStatus.BLOCKED_CHANNEL_PLAN,
            attempt=None,
            attempt_created=False,
            dispatch_effect_authorized=False,
            provider_mapping_authorized=False,
            reason_codes=_blocked_channel_plan_reason_codes(),
            evidence_reference_ids=_tuple_union(
                delivery_plan_decision.evidence_reference_ids, evidence_reference_ids
            ),
        )

    assert entry is not None
    target_reference_id = entry.target_reference_id
    assert target_reference_id is not None
    attempt = _build_planned_attempt(
        attempt_id=attempt_id,
        delivery_plan=delivery_plan,
        channel_class=validated_channel_class,
        target_reference_id=target_reference_id,
        idempotency_key=idempotency_key,
        idempotency_fingerprint=idempotency_fingerprint,
        idempotency_scope=idempotency_scope,
        evidence_reference_ids=_tuple_union(
            delivery_plan_decision.evidence_reference_ids, evidence_reference_ids
        ),
    )
    return NotificationAttemptPlanningDecision(
        decision_id=decision_id,
        authority=NotificationAttemptAuthority.NOTIFICATION_DELIVERY_SERVER,
        delivery_plan_decision=delivery_plan_decision,
        channel_class=channel_class,
        status=NotificationAttemptPlanningStatus.PLANNED,
        attempt=attempt,
        attempt_created=True,
        dispatch_effect_authorized=False,
        provider_mapping_authorized=False,
        reason_codes=_plan_attempt_reason_codes(),
        evidence_reference_ids=_tuple_union(
            delivery_plan_decision.evidence_reference_ids, evidence_reference_ids
        ),
    )


def _attempt_signature(
    attempt: NotificationAttempt,
) -> tuple[object, ...]:
    return (
        attempt.lifecycle_status,
        attempt.provider_outcome_reference_id,
        attempt.provider_outcome_class,
        attempt.adapter_contract,
        attempt.adapter_contract_version,
        attempt.provider_safe_delivery_reference,
        attempt.egress_correlation_reference,
        attempt.provider_reason_codes,
        attempt.failure_policy_reference,
        attempt.reconciliation_required,
        attempt.delivery_accepted,
        attempt.retry_authorized,
        attempt.dispatch_effect_authorized,
        attempt.provider_mapping_authorized,
        attempt.reason_codes,
    )


def _provider_outcome_signature(
    provider_outcome: NotificationProviderOutcomeReference,
) -> tuple[object, ...]:
    return (
        provider_outcome.outcome_reference_id,
        provider_outcome.adapter_contract,
        provider_outcome.adapter_contract_version,
        provider_outcome.attempt_id,
        provider_outcome.channel_class,
        provider_outcome.target_reference_id,
        provider_outcome.outcome_class,
        provider_outcome.adapter_outcome_committed,
        provider_outcome.provider_safe_delivery_reference,
        provider_outcome.egress_correlation_reference,
        provider_outcome.contains_raw_provider_payload,
        provider_outcome.identity_ambiguous,
        provider_outcome.correlation_id,
        provider_outcome.causation_id,
        provider_outcome.reason_codes,
    )


def _same_scope(
    attempt: NotificationAttempt,
    provider_outcome: NotificationProviderOutcomeReference,
) -> bool:
    return (
        attempt.attempt_id == provider_outcome.attempt_id
        and attempt.channel_class is provider_outcome.channel_class
        and attempt.target_reference_id == provider_outcome.target_reference_id
        and attempt.correlation_id == provider_outcome.correlation_id
        and attempt.causation_id == provider_outcome.causation_id
    )


def _replay_matches(
    previous_attempt: NotificationAttempt,
    provider_outcome: NotificationProviderOutcomeReference,
) -> bool:
    expected_lifecycle = _accepted_lifecycle_for_outcome_class(provider_outcome.outcome_class)
    return (
        previous_attempt.lifecycle_status == expected_lifecycle
        and previous_attempt.provider_outcome_reference_id == provider_outcome.outcome_reference_id
        and previous_attempt.provider_outcome_class is provider_outcome.outcome_class
        and previous_attempt.adapter_contract == provider_outcome.adapter_contract
        and previous_attempt.adapter_contract_version == provider_outcome.adapter_contract_version
        and previous_attempt.provider_safe_delivery_reference
        == provider_outcome.provider_safe_delivery_reference
        and previous_attempt.egress_correlation_reference
        == provider_outcome.egress_correlation_reference
        and previous_attempt.provider_reason_codes == provider_outcome.reason_codes
        and previous_attempt.reconciliation_required
        == (expected_lifecycle is NotificationAttemptLifecycleStatus.RECONCILIATION_REQUIRED)
        and previous_attempt.delivery_accepted
        == (expected_lifecycle is NotificationAttemptLifecycleStatus.DELIVERED_ACCEPTED)
        and previous_attempt.retry_authorized is False
        and previous_attempt.dispatch_effect_authorized is False
        and previous_attempt.provider_mapping_authorized is False
        and previous_attempt.reason_codes == _attempt_reason_codes_for_lifecycle(expected_lifecycle)
    )


def _build_resulting_attempt(
    previous_attempt: NotificationAttempt,
    provider_outcome: NotificationProviderOutcomeReference,
    command_evidence_reference_ids: tuple[str, ...],
) -> NotificationAttempt:
    lifecycle_status = _accepted_lifecycle_for_outcome_class(provider_outcome.outcome_class)
    return replace(
        previous_attempt,
        lifecycle_status=lifecycle_status,
        provider_outcome_reference_id=provider_outcome.outcome_reference_id,
        provider_outcome_class=provider_outcome.outcome_class,
        adapter_contract=provider_outcome.adapter_contract,
        adapter_contract_version=provider_outcome.adapter_contract_version,
        provider_safe_delivery_reference=provider_outcome.provider_safe_delivery_reference,
        egress_correlation_reference=provider_outcome.egress_correlation_reference,
        provider_reason_codes=provider_outcome.reason_codes,
        failure_policy_reference=(
            previous_attempt.failure_policy_reference
            if lifecycle_status.value in _POLICY_FAILURE_LIFECYCLE_STATUSES
            else None
        ),
        reconciliation_required=lifecycle_status
        in {
            NotificationAttemptLifecycleStatus.RECONCILIATION_REQUIRED,
            NotificationAttemptLifecycleStatus.DISPATCH_AMBIGUOUS,
            NotificationAttemptLifecycleStatus.DELIVERY_AMBIGUOUS,
        },
        delivery_accepted=lifecycle_status
        in {
            NotificationAttemptLifecycleStatus.DELIVERED_ACCEPTED,
            NotificationAttemptLifecycleStatus.PROVIDER_ACCEPTED,
        },
        retry_authorized=False,
        dispatch_effect_authorized=False,
        provider_mapping_authorized=False,
        reason_codes=_attempt_reason_codes_for_lifecycle(lifecycle_status),
        evidence_reference_ids=_tuple_union(
            previous_attempt.evidence_reference_ids,
            provider_outcome.evidence_reference_ids,
            command_evidence_reference_ids,
        ),
    )


def _accepted_outcome_status(
    outcome_class: NotificationProviderOutcomeClass,
) -> NotificationProviderOutcomeAcceptanceStatus:
    if outcome_class is NotificationProviderOutcomeClass.PROVIDER_ACCEPTED:
        return NotificationProviderOutcomeAcceptanceStatus.ACCEPTED_DELIVERED
    if outcome_class in {
        NotificationProviderOutcomeClass.DISPATCH_AMBIGUOUS,
        NotificationProviderOutcomeClass.DELIVERY_AMBIGUOUS,
    }:
        return NotificationProviderOutcomeAcceptanceStatus.ACCEPTED_AMBIGUOUS
    if outcome_class in {
        NotificationProviderOutcomeClass.PROVIDER_REJECTED,
        NotificationProviderOutcomeClass.PROVIDER_UNAVAILABLE,
        NotificationProviderOutcomeClass.RATE_OR_ACCESS_RESTRICTED,
        NotificationProviderOutcomeClass.MALFORMED_OR_UNUSABLE_PROVIDER_RESPONSE,
        NotificationProviderOutcomeClass.DELIVERY_FAILURE,
        NotificationProviderOutcomeClass.SUPPRESSED_OR_CANCELLED,
        NotificationProviderOutcomeClass.TARGET_UNAVAILABLE_OR_UNVERIFIED,
    }:
        return NotificationProviderOutcomeAcceptanceStatus.ACCEPTED_FAILURE
    raise ValueError("unsupported provider outcome class")


def _is_terminal_replay_attempt(attempt: NotificationAttempt) -> bool:
    return attempt.provider_outcome_reference_id is not None


def accept_notification_provider_outcome(
    *,
    decision_id: str,
    attempt: NotificationAttempt,
    provider_outcome: NotificationProviderOutcomeReference,
    evidence_reference_ids: tuple[str, ...],
) -> NotificationProviderOutcomeAcceptanceDecision:
    _require_text(decision_id, "decision_id")
    if type(attempt) is not NotificationAttempt:
        raise ValueError("attempt must be NotificationAttempt")
    if type(provider_outcome) is not NotificationProviderOutcomeReference:
        raise ValueError("provider_outcome must be NotificationProviderOutcomeReference")
    _require_text_tuple(
        evidence_reference_ids, "evidence_reference_ids", unique=True, allow_empty=True
    )

    if not provider_outcome.adapter_outcome_committed:
        return NotificationProviderOutcomeAcceptanceDecision(
            decision_id=decision_id,
            authority=NotificationAttemptAuthority.NOTIFICATION_DELIVERY_SERVER,
            previous_attempt=attempt,
            provider_outcome=provider_outcome,
            status=NotificationProviderOutcomeAcceptanceStatus.REJECTED_UNCOMMITTED,
            resulting_attempt=None,
            outcome_accepted=False,
            replayed=False,
            delivery_accepted=False,
            reconciliation_required=False,
            retry_authorized=False,
            dispatch_effect_authorized=False,
            provider_mapping_authorized=False,
            reason_codes=_rejected_uncommitted_reason_codes(),
            evidence_reference_ids=_tuple_union(
                attempt.evidence_reference_ids,
                provider_outcome.evidence_reference_ids,
                evidence_reference_ids,
            ),
        )

    if provider_outcome.contains_raw_provider_payload:
        return NotificationProviderOutcomeAcceptanceDecision(
            decision_id=decision_id,
            authority=NotificationAttemptAuthority.NOTIFICATION_DELIVERY_SERVER,
            previous_attempt=attempt,
            provider_outcome=provider_outcome,
            status=NotificationProviderOutcomeAcceptanceStatus.REJECTED_UNSAFE_PAYLOAD,
            resulting_attempt=None,
            outcome_accepted=False,
            replayed=False,
            delivery_accepted=False,
            reconciliation_required=False,
            retry_authorized=False,
            dispatch_effect_authorized=False,
            provider_mapping_authorized=False,
            reason_codes=_rejected_unsafe_payload_reason_codes(),
            evidence_reference_ids=_tuple_union(
                attempt.evidence_reference_ids,
                provider_outcome.evidence_reference_ids,
                evidence_reference_ids,
            ),
        )

    if provider_outcome.identity_ambiguous:
        return NotificationProviderOutcomeAcceptanceDecision(
            decision_id=decision_id,
            authority=NotificationAttemptAuthority.NOTIFICATION_DELIVERY_SERVER,
            previous_attempt=attempt,
            provider_outcome=provider_outcome,
            status=NotificationProviderOutcomeAcceptanceStatus.REJECTED_IDENTITY_AMBIGUOUS,
            resulting_attempt=None,
            outcome_accepted=False,
            replayed=False,
            delivery_accepted=False,
            reconciliation_required=False,
            retry_authorized=False,
            dispatch_effect_authorized=False,
            provider_mapping_authorized=False,
            reason_codes=_rejected_identity_ambiguous_reason_codes(),
            evidence_reference_ids=_tuple_union(
                attempt.evidence_reference_ids,
                provider_outcome.evidence_reference_ids,
                evidence_reference_ids,
            ),
        )

    if not _same_scope(attempt, provider_outcome):
        return NotificationProviderOutcomeAcceptanceDecision(
            decision_id=decision_id,
            authority=NotificationAttemptAuthority.NOTIFICATION_DELIVERY_SERVER,
            previous_attempt=attempt,
            provider_outcome=provider_outcome,
            status=NotificationProviderOutcomeAcceptanceStatus.REJECTED_SCOPE_MISMATCH,
            resulting_attempt=None,
            outcome_accepted=False,
            replayed=False,
            delivery_accepted=False,
            reconciliation_required=False,
            retry_authorized=False,
            dispatch_effect_authorized=False,
            provider_mapping_authorized=False,
            reason_codes=_rejected_scope_mismatch_reason_codes(),
            evidence_reference_ids=_tuple_union(
                attempt.evidence_reference_ids,
                provider_outcome.evidence_reference_ids,
                evidence_reference_ids,
            ),
        )

    if _is_terminal_replay_attempt(attempt):
        if _replay_matches(attempt, provider_outcome):
            return NotificationProviderOutcomeAcceptanceDecision(
                decision_id=decision_id,
                authority=NotificationAttemptAuthority.NOTIFICATION_DELIVERY_SERVER,
                previous_attempt=attempt,
                provider_outcome=provider_outcome,
                status=NotificationProviderOutcomeAcceptanceStatus.REPLAYED,
                resulting_attempt=attempt,
                outcome_accepted=True,
                replayed=True,
                delivery_accepted=attempt.delivery_accepted,
                reconciliation_required=attempt.reconciliation_required,
                retry_authorized=attempt.retry_authorized,
                dispatch_effect_authorized=attempt.dispatch_effect_authorized,
                provider_mapping_authorized=attempt.provider_mapping_authorized,
                reason_codes=_replayed_reason_codes(),
                evidence_reference_ids=_tuple_union(
                    attempt.evidence_reference_ids,
                    provider_outcome.evidence_reference_ids,
                    evidence_reference_ids,
                ),
            )
        return NotificationProviderOutcomeAcceptanceDecision(
            decision_id=decision_id,
            authority=NotificationAttemptAuthority.NOTIFICATION_DELIVERY_SERVER,
            previous_attempt=attempt,
            provider_outcome=provider_outcome,
            status=NotificationProviderOutcomeAcceptanceStatus.REJECTED_STATE_MISMATCH,
            resulting_attempt=None,
            outcome_accepted=False,
            replayed=False,
            delivery_accepted=False,
            reconciliation_required=False,
            retry_authorized=False,
            dispatch_effect_authorized=False,
            provider_mapping_authorized=False,
            reason_codes=_rejected_state_mismatch_reason_codes(),
                evidence_reference_ids=_tuple_union(
                    attempt.evidence_reference_ids,
                    provider_outcome.evidence_reference_ids,
                    evidence_reference_ids,
                ),
            )

    if attempt.lifecycle_status not in {
        NotificationAttemptLifecycleStatus.ATTEMPT_PLANNED,
        NotificationAttemptLifecycleStatus.ATTEMPT_IN_PROGRESS,
    }:
        return NotificationProviderOutcomeAcceptanceDecision(
            decision_id=decision_id,
            authority=NotificationAttemptAuthority.NOTIFICATION_DELIVERY_SERVER,
            previous_attempt=attempt,
            provider_outcome=provider_outcome,
            status=NotificationProviderOutcomeAcceptanceStatus.REJECTED_STATE_MISMATCH,
            resulting_attempt=None,
            outcome_accepted=False,
            replayed=False,
            delivery_accepted=False,
            reconciliation_required=False,
            retry_authorized=False,
            dispatch_effect_authorized=False,
            provider_mapping_authorized=False,
            reason_codes=_rejected_state_mismatch_reason_codes(),
            evidence_reference_ids=_tuple_union(
                attempt.evidence_reference_ids,
                provider_outcome.evidence_reference_ids,
                evidence_reference_ids,
            ),
        )

    if (
        provider_outcome.outcome_class is NotificationProviderOutcomeClass.PROVIDER_ACCEPTED
        and provider_outcome.provider_safe_delivery_reference is None
    ):
        return NotificationProviderOutcomeAcceptanceDecision(
            decision_id=decision_id,
            authority=NotificationAttemptAuthority.NOTIFICATION_DELIVERY_SERVER,
            previous_attempt=attempt,
            provider_outcome=provider_outcome,
            status=NotificationProviderOutcomeAcceptanceStatus.REJECTED_STATE_MISMATCH,
            resulting_attempt=None,
            outcome_accepted=False,
            replayed=False,
            delivery_accepted=False,
            reconciliation_required=False,
            retry_authorized=False,
            dispatch_effect_authorized=False,
            provider_mapping_authorized=False,
            reason_codes=_rejected_state_mismatch_reason_codes(),
            evidence_reference_ids=_tuple_union(
                attempt.evidence_reference_ids,
                provider_outcome.evidence_reference_ids,
                evidence_reference_ids,
            ),
        )

    status = _accepted_outcome_status(provider_outcome.outcome_class)
    resulting_attempt = _build_resulting_attempt(
        attempt,
        provider_outcome,
        evidence_reference_ids,
    )
    return NotificationProviderOutcomeAcceptanceDecision(
        decision_id=decision_id,
        authority=NotificationAttemptAuthority.NOTIFICATION_DELIVERY_SERVER,
        previous_attempt=attempt,
        provider_outcome=provider_outcome,
        status=status,
        resulting_attempt=resulting_attempt,
        outcome_accepted=True,
        replayed=False,
        delivery_accepted=resulting_attempt.delivery_accepted,
        reconciliation_required=resulting_attempt.reconciliation_required,
        retry_authorized=False,
        dispatch_effect_authorized=False,
        provider_mapping_authorized=False,
        reason_codes=(
            _accepted_delivered_reason_codes()
            if status is NotificationProviderOutcomeAcceptanceStatus.ACCEPTED_DELIVERED
            else _accepted_ambiguous_reason_codes()
            if status is NotificationProviderOutcomeAcceptanceStatus.ACCEPTED_AMBIGUOUS
            else _accepted_failure_reason_codes()
        ),
        evidence_reference_ids=_tuple_union(
            attempt.evidence_reference_ids,
            provider_outcome.evidence_reference_ids,
            evidence_reference_ids,
        ),
    )


__all__ = (
    "ND06_TASK_ID",
    "NotificationAttemptAuthority",
    "NotificationAttemptLifecycleStatus",
    "NotificationAttemptPlanningStatus",
    "NotificationProviderOutcomeClass",
    "NotificationProviderOutcomeAcceptanceStatus",
    "NotificationAttempt",
    "NotificationAttemptPlanningDecision",
    "NotificationProviderOutcomeReference",
    "NotificationProviderOutcomeAcceptanceDecision",
    "plan_notification_attempt",
    "accept_notification_provider_outcome",
)
