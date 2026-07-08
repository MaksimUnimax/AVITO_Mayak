"""Semantic contract primitives for Entitlements & Billing."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Final

from pydantic import BaseModel, ConfigDict, Field, model_validator

from mayak.platform.idempotency import IdempotencyKey

ACCOUNT_ID_OWNERSHIP_SCOPE: Final[str] = "account_id"


class TariffName(str, Enum):
    """Approved tariff names currently authorized for semantic contracts."""

    FREE = "FREE"
    BASIC = "BASIC"


class EntitlementDecisionStatus(str, Enum):
    """Semantic outcomes for effective entitlement decisions."""

    ALLOWED = "ALLOWED"
    DENIED = "DENIED"
    BLOCKED = "BLOCKED"
    EXPIRED = "EXPIRED"
    AMBIGUOUS = "AMBIGUOUS"
    UNSUPPORTED = "UNSUPPORTED"
    USER_CHOICE_REQUIRED = "USER_CHOICE_REQUIRED"
    FREE_COMPLIANCE_REQUIRED = "FREE_COMPLIANCE_REQUIRED"
    CONFLICT = "CONFLICT"


class SubscriptionState(str, Enum):
    """Semantic subscription states."""

    ACTIVE = "ACTIVE"
    PENDING = "PENDING"
    SUSPENDED = "SUSPENDED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class ManualAccessGrantState(str, Enum):
    """Semantic manual-access states."""

    ACTIVE = "ACTIVE"
    REPLAYED = "REPLAYED"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"
    REJECTED = "REJECTED"
    CONFLICT = "CONFLICT"


class PaymentRecordState(str, Enum):
    """Semantic normalized payment-record states."""

    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"
    AMBIGUOUS = "AMBIGUOUS"
    RECONCILE_REQUIRED = "RECONCILE_REQUIRED"


class PaymentEventState(str, Enum):
    """Semantic normalized payment-event states."""

    VERIFIED_RECORDED = "VERIFIED_RECORDED"
    REJECTED = "REJECTED"
    DUPLICATE = "DUPLICATE"
    AMBIGUOUS = "AMBIGUOUS"
    RECONCILE_REQUIRED = "RECONCILE_REQUIRED"


class _NonEmptyBillingText(BaseModel):
    """Frozen non-empty text wrapper used by billing semantic primitives."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    value: str = Field(min_length=1)


class EffectiveInterval(BaseModel):
    """Frozen closed interval for entitlement semantics."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    starts_at: datetime
    ends_at: datetime

    @model_validator(mode="after")
    def _validate_interval(self) -> "EffectiveInterval":
        if self.ends_at <= self.starts_at:
            raise ValueError("effective interval ends_at must be after starts_at")
        return self


class ActorContext(BaseModel):
    """Semantic actor context without importing identity module state."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    actor_id: str = Field(min_length=1)
    actor_category: str = Field(min_length=1)
    authorization_scope: str = Field(min_length=1)
    authorization_reference: str = Field(min_length=1)


class TariffDefinition(BaseModel):
    """Versioned semantic definition for a tariff."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    tariff_name: TariffName
    semantic_version: str = Field(min_length=1)
    price_rub: int = Field(ge=0)
    billing_period_label: str | None = None
    scan_interval_floor_minutes: int = Field(gt=0)
    scan_interval_step_minutes: int = Field(gt=0)
    active_beacon_limit: int | None = Field(default=None, ge=1)
    feature_notes: str | None = None
    mechanism_notes: str | None = None

    @model_validator(mode="after")
    def _validate_approved_tariff_values(self) -> "TariffDefinition":
        if self.tariff_name is TariffName.FREE:
            if self.price_rub != 0:
                raise ValueError("Free tariff price must be zero")
            if self.billing_period_label is not None:
                raise ValueError("Free tariff does not declare a billing period")
            if self.scan_interval_floor_minutes != 180:
                raise ValueError("Free tariff scan interval floor must be 180 minutes")
            if self.scan_interval_step_minutes != 180:
                raise ValueError("Free tariff scan interval step must be 180 minutes")
            if self.active_beacon_limit != 1:
                raise ValueError("Free tariff active beacon limit must be one")
            if self.feature_notes != "reduced features":
                raise ValueError("Free tariff feature notes must describe reduced features")
            if self.mechanism_notes != "same entitlement mechanism as paid tariff, stricter limits":
                raise ValueError("Free tariff mechanism notes must describe the approved entitlement mechanism")
        elif self.tariff_name is TariffName.BASIC:
            if self.price_rub != 990:
                raise ValueError("Basic tariff price must be 990 RUB")
            if self.billing_period_label != "1 month":
                raise ValueError("Basic tariff billing period must be one month")
            if self.scan_interval_floor_minutes != 5:
                raise ValueError("Basic tariff scan interval floor must be 5 minutes")
            if self.scan_interval_step_minutes != 5:
                raise ValueError("Basic tariff scan interval step must be 5 minutes")
            if self.active_beacon_limit is not None:
                raise ValueError("Basic tariff active beacon limit is not approved")
            if self.feature_notes is not None:
                raise ValueError("Basic tariff must not predeclare extra feature notes")
            if self.mechanism_notes is not None:
                raise ValueError("Basic tariff must not predeclare extra mechanism notes")
        return self


class AccountScopedRecord(BaseModel):
    """Frozen semantic base for records owned by account_id."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    account_id: str = Field(min_length=1)
    ownership_scope: str = Field(default=ACCOUNT_ID_OWNERSHIP_SCOPE, frozen=True)


class Subscription(AccountScopedRecord):
    """Semantic subscription record."""

    subscription_id: str = Field(min_length=1)
    tariff_name: TariffName
    status: SubscriptionState = SubscriptionState.ACTIVE
    effective_interval: EffectiveInterval
    source_reference: str | None = None


class EntitlementGrant(AccountScopedRecord):
    """Semantic entitlement grant record."""

    grant_id: str = Field(min_length=1)
    capability: str = Field(min_length=1)
    scope: str = Field(min_length=1)
    limit_value: int | None = Field(default=None, ge=0)
    status: str = Field(default="ACTIVE", min_length=1)
    effective_interval: EffectiveInterval
    source_kind: str = Field(min_length=1)
    source_reference: str | None = None


class ManualAccessGrant(AccountScopedRecord):
    """Protected manual access grant with explicit audit and idempotency references."""

    grant_id: str = Field(min_length=1)
    actor: ActorContext
    reason: str = Field(min_length=1)
    scope: str = Field(min_length=1)
    capability: str = Field(min_length=1)
    effective_interval: EffectiveInterval
    idempotency_key: IdempotencyKey
    audit_reference: str = Field(min_length=1)
    state: ManualAccessGrantState = ManualAccessGrantState.ACTIVE


class PaymentRecord(AccountScopedRecord):
    """Semantic payment record placeholder without entitlement authority."""

    record_id: str = Field(min_length=1)
    payment_reference: str = Field(min_length=1)
    provider_name: str | None = None
    status: PaymentRecordState
    observed_at: datetime
    amount_rub: int | None = Field(default=None, ge=0)
    currency_code: str = Field(default="RUB", min_length=1)
    source_event_reference: str | None = None
    provider_payload_reference: str | None = None


class PaymentEvent(AccountScopedRecord):
    """Semantic payment-event placeholder without entitlement authority."""

    event_id: str = Field(min_length=1)
    event_reference: str = Field(min_length=1)
    provider_name: str | None = None
    event_kind: str = Field(min_length=1)
    status: PaymentEventState
    observed_at: datetime
    source_record_reference: str | None = None
    provider_payload_reference: str | None = None


class EffectiveEntitlementDecision(AccountScopedRecord):
    """Derived entitlement decision that is never a source of authority by itself."""

    decision_id: str = Field(min_length=1)
    status: EntitlementDecisionStatus
    reason_code: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    evaluated_at: datetime
    capability: str | None = None
    limit_value: int | None = Field(default=None, ge=0)
    source_references: tuple[str, ...] = Field(default_factory=tuple)
    effective_interval: EffectiveInterval | None = None
    provenance: str = Field(default="semantic-contract", min_length=1)

    @model_validator(mode="after")
    def _validate_source_references(self) -> "EffectiveEntitlementDecision":
        if any(not reference.strip() for reference in self.source_references):
            raise ValueError("source references must be non-empty")
        return self


__all__ = [
    "ACCOUNT_ID_OWNERSHIP_SCOPE",
    "ActorContext",
    "EffectiveEntitlementDecision",
    "EffectiveInterval",
    "EntitlementDecisionStatus",
    "EntitlementGrant",
    "ManualAccessGrant",
    "ManualAccessGrantState",
    "PaymentEvent",
    "PaymentEventState",
    "PaymentRecord",
    "PaymentRecordState",
    "Subscription",
    "SubscriptionState",
    "TariffDefinition",
    "TariffName",
]
