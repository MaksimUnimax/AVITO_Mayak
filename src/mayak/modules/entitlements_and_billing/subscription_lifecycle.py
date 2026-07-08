"""Deterministic semantic contracts for subscription lifecycle."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Final

from pydantic import BaseModel, ConfigDict, Field, model_validator

from mayak.platform.idempotency import IdempotencyFingerprint, IdempotencyKey

from .contracts import (
    EffectiveInterval,
    PaymentEvent,
    PaymentRecord,
    Subscription,
    SubscriptionState,
    TariffName,
)
from .policies import BASIC_TARIFF_POLICY, FREE_TARIFF_POLICY, FUTURE_DECISION_GATES

SUBSCRIPTION_TARIFF_FAMILY_FREE: Final[TariffName] = TariffName.FREE
SUBSCRIPTION_TARIFF_FAMILY_BASIC: Final[TariffName] = TariffName.BASIC
APPROVED_SUBSCRIPTION_TARIFF_FAMILIES: Final[tuple[TariffName, ...]] = (
    SUBSCRIPTION_TARIFF_FAMILY_FREE,
    SUBSCRIPTION_TARIFF_FAMILY_BASIC,
)

TRIAL_SEMANTICS_SUPPORTED: Final[bool] = False
GRACE_SEMANTICS_SUPPORTED: Final[bool] = False
PRORATION_SEMANTICS_SUPPORTED: Final[bool] = False


class SubscriptionPaymentMode(str, Enum):
    """Approved payment mode semantics for the first-stage subscription lifecycle."""

    MANUAL_RENEWAL_ONLY = "MANUAL_RENEWAL_ONLY"


class SubscriptionLifecycleAction(str, Enum):
    """Semantic lifecycle request actions."""

    ASSESS = "ASSESS"
    ASSIGN = "ASSIGN"
    CHANGE = "CHANGE"
    CANCEL = "CANCEL"
    EXPIRE = "EXPIRE"
    RENEW = "RENEW"


class SubscriptionLifecycleOutcome(str, Enum):
    """Approved deterministic lifecycle outcomes."""

    ASSIGNED = "ASSIGNED"
    CHANGED = "CHANGED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"
    PENDING = "PENDING"
    BLOCKED = "BLOCKED"
    CONFLICT = "CONFLICT"
    REPLAYED = "REPLAYED"
    IDEMPOTENCY_MISMATCH = "IDEMPOTENCY_MISMATCH"
    REJECTED = "REJECTED"
    USER_CHOICE_REQUIRED = "USER_CHOICE_REQUIRED"
    FREE_COMPLIANCE_REQUIRED = "FREE_COMPLIANCE_REQUIRED"


class SubscriptionLifecycleActorContext(BaseModel):
    """Semantic actor context for subscription lifecycle requests."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    actor_id: str = Field(min_length=1)
    actor_category: str = Field(min_length=1)
    authorization_scope: str = Field(min_length=1)
    authorization_reference: str = Field(min_length=1)
    audit_reference: str = Field(min_length=1)


class SubscriptionLifecycleIdempotencyRecord(BaseModel):
    """Explicit prior idempotency evidence for deterministic replay semantics."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    requested_action: SubscriptionLifecycleAction
    idempotency_key: IdempotencyKey
    request_fingerprint: IdempotencyFingerprint
    terminal_outcome: SubscriptionLifecycleOutcome


class SubscriptionLifecycleRequest(BaseModel):
    """Explicit synthetic-contract input for subscription lifecycle semantics."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    actor: SubscriptionLifecycleActorContext
    target_account_id: str = Field(min_length=1)
    requested_action: SubscriptionLifecycleAction
    current_subscription: Subscription | None = None
    current_tariff_family: str | None = None
    requested_tariff_family: str | None = None
    paid_access_interval: EffectiveInterval | None = None
    requested_interval_minutes: int | None = Field(default=None, gt=0)
    decision_at: datetime
    payment_mode: SubscriptionPaymentMode = SubscriptionPaymentMode.MANUAL_RENEWAL_ONLY
    idempotency_key: IdempotencyKey | None = None
    payment_records: tuple[PaymentRecord, ...] = Field(default_factory=tuple)
    payment_events: tuple[PaymentEvent, ...] = Field(default_factory=tuple)
    prior_idempotency_record: SubscriptionLifecycleIdempotencyRecord | None = None


class SubscriptionLifecycleDecision(BaseModel):
    """Pure semantic decision for subscription lifecycle contracts."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    requested_action: SubscriptionLifecycleAction
    outcome: SubscriptionLifecycleOutcome
    terminal_outcome: SubscriptionLifecycleOutcome
    reason_code: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    actor: SubscriptionLifecycleActorContext
    target_account_id: str = Field(min_length=1)
    current_subscription_id: str | None = None
    current_subscription_state: SubscriptionState | None = None
    current_tariff_family: str | None = None
    requested_tariff_family: str | None = None
    payment_mode: SubscriptionPaymentMode = SubscriptionPaymentMode.MANUAL_RENEWAL_ONLY
    free_only_requirement: bool = False
    user_choice_required: bool = False
    free_compliance_required: bool = False
    idempotency_key: IdempotencyKey | None = None
    request_fingerprint: IdempotencyFingerprint
    audit_reference: str = Field(min_length=1)
    decision_at: datetime
    paid_access_interval: EffectiveInterval | None = None
    payment_evidence_references: tuple[str, ...] = Field(default_factory=tuple)
    source_references: tuple[str, ...] = Field(default_factory=tuple)
    history_preserved: bool = True

    @model_validator(mode="after")
    def _validate_terminal_outcome(self) -> "SubscriptionLifecycleDecision":
        if self.outcome is not SubscriptionLifecycleOutcome.REPLAYED and self.outcome != self.terminal_outcome:
            raise ValueError("terminal outcome must match the current outcome except for replayed decisions")
        return self


def _tariff_family_or_none(raw_tariff_family: str | None) -> TariffName | None:
    if raw_tariff_family is None:
        return None
    try:
        return TariffName(raw_tariff_family)
    except ValueError:
        return None


def _request_fingerprint(request: SubscriptionLifecycleRequest) -> IdempotencyFingerprint:
    return IdempotencyFingerprint(
        value=(
            "subscription-lifecycle:"
            f"{request.model_dump_json(exclude={'idempotency_key', 'prior_idempotency_record', 'decision_at'})}"
        )
    )


def compute_subscription_lifecycle_request_fingerprint(
    request: SubscriptionLifecycleRequest,
) -> IdempotencyFingerprint:
    """Public deterministic helper for subscription idempotency contracts/tests."""

    return _request_fingerprint(request)


def _approved_tariff_family(raw_tariff_family: str | None) -> TariffName | None:
    tariff_family = _tariff_family_or_none(raw_tariff_family)
    if tariff_family in APPROVED_SUBSCRIPTION_TARIFF_FAMILIES:
        return tariff_family
    return None


def _is_free_compliant(requested_interval_minutes: int | None) -> bool:
    if requested_interval_minutes is None:
        return False
    if requested_interval_minutes < FREE_TARIFF_POLICY.scan_interval_floor_minutes:
        return False
    return (
        requested_interval_minutes - FREE_TARIFF_POLICY.scan_interval_floor_minutes
    ) % FREE_TARIFF_POLICY.scan_interval_step_minutes == 0


def _build_decision(
    request: SubscriptionLifecycleRequest,
    *,
    outcome: SubscriptionLifecycleOutcome,
    reason_code: str,
    reason: str,
    current_subscription_id: str | None = None,
    current_subscription_state: SubscriptionState | None = None,
    current_tariff_family: str | None = None,
    requested_tariff_family: str | None = None,
    free_only_requirement: bool = False,
    user_choice_required: bool = False,
    free_compliance_required: bool = False,
    paid_access_interval: EffectiveInterval | None = None,
    payment_evidence_references: tuple[str, ...] = (),
    source_references: tuple[str, ...] = (),
    terminal_outcome: SubscriptionLifecycleOutcome | None = None,
) -> SubscriptionLifecycleDecision:
    return SubscriptionLifecycleDecision(
        requested_action=request.requested_action,
        outcome=outcome,
        terminal_outcome=terminal_outcome or outcome,
        reason_code=reason_code,
        reason=reason,
        actor=request.actor,
        target_account_id=request.target_account_id,
        current_subscription_id=current_subscription_id,
        current_subscription_state=current_subscription_state,
        current_tariff_family=current_tariff_family,
        requested_tariff_family=requested_tariff_family,
        payment_mode=request.payment_mode,
        free_only_requirement=free_only_requirement,
        user_choice_required=user_choice_required,
        free_compliance_required=free_compliance_required,
        idempotency_key=request.idempotency_key,
        request_fingerprint=_request_fingerprint(request),
        audit_reference=request.actor.audit_reference,
        decision_at=request.decision_at,
        paid_access_interval=paid_access_interval,
        payment_evidence_references=payment_evidence_references,
        source_references=source_references,
        history_preserved=True,
    )


def _payment_evidence_references(request: SubscriptionLifecycleRequest) -> tuple[str, ...]:
    return tuple(record.payment_reference for record in request.payment_records) + tuple(
        event.event_reference for event in request.payment_events
    )


def evaluate_subscription_lifecycle(
    request: SubscriptionLifecycleRequest,
) -> SubscriptionLifecycleDecision:
    """Evaluate deterministic subscription lifecycle semantics without side effects."""

    current_subscription = request.current_subscription
    current_tariff_family = request.current_tariff_family
    if current_subscription is not None:
        derived_current_tariff_family = current_subscription.tariff_name.value
        if current_tariff_family is not None and current_tariff_family != derived_current_tariff_family:
            return _build_decision(
                request,
                outcome=SubscriptionLifecycleOutcome.CONFLICT,
                reason_code="CURRENT_TARIFF_CONFLICT",
                reason="The explicit current tariff family disagrees with the current subscription state.",
                current_subscription_id=current_subscription.subscription_id,
                current_subscription_state=current_subscription.status,
                current_tariff_family=current_tariff_family,
                requested_tariff_family=request.requested_tariff_family,
                paid_access_interval=request.paid_access_interval or current_subscription.effective_interval,
                source_references=(current_subscription.subscription_id, derived_current_tariff_family),
            )
        current_tariff_family = derived_current_tariff_family

    requested_tariff_family = request.requested_tariff_family
    approved_requested_tariff = _approved_tariff_family(requested_tariff_family)

    if requested_tariff_family is not None and approved_requested_tariff is None:
        return _build_decision(
            request,
            outcome=SubscriptionLifecycleOutcome.BLOCKED,
            reason_code="UNSUPPORTED_TARIFF_FAMILY",
            reason="The requested tariff family is not part of the approved Free/Basic policy.",
            current_subscription_id=current_subscription.subscription_id if current_subscription else None,
            current_subscription_state=current_subscription.status if current_subscription else None,
            current_tariff_family=current_tariff_family,
            requested_tariff_family=requested_tariff_family,
            paid_access_interval=request.paid_access_interval
            or (current_subscription.effective_interval if current_subscription else None),
            source_references=(
                current_subscription.subscription_id if current_subscription else "",
                requested_tariff_family,
            ),
        )

    payment_references = _payment_evidence_references(request)
    if request.prior_idempotency_record is not None:
        request_fingerprint = _request_fingerprint(request)
        prior = request.prior_idempotency_record
        if prior.idempotency_key != request.idempotency_key:
            return _build_decision(
                request,
                outcome=SubscriptionLifecycleOutcome.CONFLICT,
                reason_code="IDEMPOTENCY_KEY_CONFLICT",
                reason="The prior idempotency evidence references a different key than the current request.",
                current_subscription_id=current_subscription.subscription_id if current_subscription else None,
                current_subscription_state=current_subscription.status if current_subscription else None,
                current_tariff_family=current_tariff_family,
                requested_tariff_family=requested_tariff_family,
                paid_access_interval=request.paid_access_interval
                or (current_subscription.effective_interval if current_subscription else None),
                payment_evidence_references=payment_references,
                source_references=(prior.idempotency_key.value, request.idempotency_key.value if request.idempotency_key else ""),
            )
        if prior.request_fingerprint != request_fingerprint:
            return _build_decision(
                request,
                outcome=SubscriptionLifecycleOutcome.IDEMPOTENCY_MISMATCH,
                reason_code="IDEMPOTENCY_MISMATCH",
                reason="The same idempotency key was reused for a different request fingerprint.",
                current_subscription_id=current_subscription.subscription_id if current_subscription else None,
                current_subscription_state=current_subscription.status if current_subscription else None,
                current_tariff_family=current_tariff_family,
                requested_tariff_family=requested_tariff_family,
                paid_access_interval=request.paid_access_interval
                or (current_subscription.effective_interval if current_subscription else None),
                payment_evidence_references=payment_references,
                source_references=(prior.idempotency_key.value, prior.request_fingerprint.value),
            )
        return _build_decision(
            request,
            outcome=SubscriptionLifecycleOutcome.REPLAYED,
            terminal_outcome=prior.terminal_outcome,
            reason_code="IDEMPOTENT_REPLAY",
            reason="The same idempotency key and request fingerprint replay the original terminal outcome.",
            current_subscription_id=current_subscription.subscription_id if current_subscription else None,
            current_subscription_state=current_subscription.status if current_subscription else None,
            current_tariff_family=current_tariff_family,
            requested_tariff_family=requested_tariff_family,
            paid_access_interval=request.paid_access_interval
            or (current_subscription.effective_interval if current_subscription else None),
            payment_evidence_references=payment_references,
            source_references=(prior.idempotency_key.value, prior.request_fingerprint.value),
        )

    mutation_like_actions = {
        SubscriptionLifecycleAction.ASSIGN,
        SubscriptionLifecycleAction.CHANGE,
        SubscriptionLifecycleAction.CANCEL,
        SubscriptionLifecycleAction.EXPIRE,
        SubscriptionLifecycleAction.RENEW,
    }
    if request.requested_action in mutation_like_actions and request.idempotency_key is None:
        return _build_decision(
            request,
            outcome=SubscriptionLifecycleOutcome.REJECTED,
            reason_code="IDEMPOTENCY_KEY_REQUIRED",
            reason="Mutation-like subscription lifecycle requests require an idempotency key before any effect.",
            current_subscription_id=current_subscription.subscription_id if current_subscription else None,
            current_subscription_state=current_subscription.status if current_subscription else None,
            current_tariff_family=current_tariff_family,
            requested_tariff_family=requested_tariff_family,
            paid_access_interval=request.paid_access_interval
            or (current_subscription.effective_interval if current_subscription else None),
            payment_evidence_references=payment_references,
        )

    if current_subscription is not None and current_subscription.tariff_name is TariffName.BASIC and current_subscription.status in {
        SubscriptionState.EXPIRED,
        SubscriptionState.CANCELLED,
        SubscriptionState.SUSPENDED,
    } and request.requested_action in {
        SubscriptionLifecycleAction.ASSESS,
        SubscriptionLifecycleAction.ASSIGN,
        SubscriptionLifecycleAction.CHANGE,
    }:
        free_compliance_required = not _is_free_compliant(request.requested_interval_minutes)
        return _build_decision(
            request,
            outcome=(
                SubscriptionLifecycleOutcome.FREE_COMPLIANCE_REQUIRED
                if free_compliance_required
                else SubscriptionLifecycleOutcome.USER_CHOICE_REQUIRED
            ),
            reason_code=(
                "PAID_ACCESS_EXPIRED_FREE_COMPLIANCE_REQUIRED"
                if free_compliance_required
                else "PAID_ACCESS_EXPIRED_USER_CHOICE_REQUIRED"
            ),
            reason=(
                "Paid access has ended and the requested state must be brought into Free requirements."
                if free_compliance_required
                else "Paid access has ended; the user must choose one Beacon to remain under Free and start it manually."
            ),
            current_subscription_id=current_subscription.subscription_id,
            current_subscription_state=current_subscription.status,
            current_tariff_family=current_tariff_family,
            requested_tariff_family=requested_tariff_family,
            free_only_requirement=True,
            user_choice_required=True,
            free_compliance_required=free_compliance_required,
            paid_access_interval=request.paid_access_interval or current_subscription.effective_interval,
            source_references=(current_subscription.subscription_id, FREE_TARIFF_POLICY.tariff_name.value),
        )

    if request.payment_records or request.payment_events:
        if request.requested_action in {
            SubscriptionLifecycleAction.ASSIGN,
            SubscriptionLifecycleAction.CHANGE,
            SubscriptionLifecycleAction.RENEW,
        }:
            return _build_decision(
                request,
                outcome=SubscriptionLifecycleOutcome.PENDING,
                reason_code="PAYMENT_EVIDENCE_IS_NON_AUTHORITATIVE",
                reason="Payment records and events are external evidence only and cannot assign or change a subscription by themselves.",
                current_subscription_id=current_subscription.subscription_id if current_subscription else None,
                current_subscription_state=current_subscription.status if current_subscription else None,
                current_tariff_family=current_tariff_family,
                requested_tariff_family=requested_tariff_family,
                paid_access_interval=request.paid_access_interval
                or (current_subscription.effective_interval if current_subscription else None),
                payment_evidence_references=payment_references,
                source_references=payment_references,
            )
        if current_subscription is None:
            return _build_decision(
                request,
                outcome=SubscriptionLifecycleOutcome.PENDING,
                reason_code="PAYMENT_EVIDENCE_PENDING_MANUAL_RENEWAL",
                reason="Payment evidence is non-authority evidence; manual renewal remains pending server-authorized input.",
                requested_tariff_family=requested_tariff_family,
                payment_evidence_references=payment_references,
                source_references=payment_references,
            )

    if request.requested_action is SubscriptionLifecycleAction.ASSESS:
        if current_subscription is None:
            if approved_requested_tariff is TariffName.FREE:
                return _build_decision(
                    request,
                    outcome=SubscriptionLifecycleOutcome.ASSIGNED,
                    reason_code="FREE_FALLBACK_ASSIGNED",
                    reason="Free is the fallback product policy when paid access is unavailable.",
                    requested_tariff_family=requested_tariff_family,
                    free_only_requirement=True,
                    source_references=(FREE_TARIFF_POLICY.tariff_name.value,),
                )
            if approved_requested_tariff is TariffName.BASIC:
                return _build_decision(
                    request,
                    outcome=SubscriptionLifecycleOutcome.ASSIGNED,
                    reason_code="BASIC_MONTHLY_ASSIGNED",
                    reason="Basic is the approved one-month tariff family and is represented deterministically.",
                    requested_tariff_family=requested_tariff_family,
                    paid_access_interval=request.paid_access_interval,
                    source_references=(BASIC_TARIFF_POLICY.tariff_name.value, BASIC_TARIFF_POLICY.billing_period_label or ""),
                )
            return _build_decision(
                request,
                outcome=SubscriptionLifecycleOutcome.BLOCKED,
                reason_code="SUBSCRIPTION_STATE_UNRESOLVED",
                reason="No current subscription and no approved fallback request can prove a deterministic state.",
            )

        if current_subscription.tariff_name is TariffName.FREE:
            return _build_decision(
                request,
                outcome=SubscriptionLifecycleOutcome.ASSIGNED,
                reason_code="FREE_FALLBACK_ASSIGNED",
                reason="Free remains available as the fallback product policy without trial or grace semantics.",
                current_subscription_id=current_subscription.subscription_id,
                current_subscription_state=current_subscription.status,
                current_tariff_family=current_tariff_family,
                requested_tariff_family=requested_tariff_family or current_tariff_family,
                free_only_requirement=True,
                paid_access_interval=request.paid_access_interval or current_subscription.effective_interval,
                source_references=(current_subscription.subscription_id, FREE_TARIFF_POLICY.tariff_name.value),
            )

        if current_subscription.tariff_name is TariffName.BASIC:
            return _build_decision(
                request,
                outcome=SubscriptionLifecycleOutcome.ASSIGNED,
                reason_code="BASIC_MONTHLY_ASSIGNED",
                reason="Basic is the approved one-month tariff family and is represented deterministically.",
                current_subscription_id=current_subscription.subscription_id,
                current_subscription_state=current_subscription.status,
                current_tariff_family=current_tariff_family,
                requested_tariff_family=requested_tariff_family or current_tariff_family,
                paid_access_interval=request.paid_access_interval or current_subscription.effective_interval,
                source_references=(
                    current_subscription.subscription_id,
                    BASIC_TARIFF_POLICY.tariff_name.value,
                    BASIC_TARIFF_POLICY.billing_period_label or "",
                ),
            )

        return _build_decision(
            request,
            outcome=SubscriptionLifecycleOutcome.BLOCKED,
            reason_code="SUBSCRIPTION_STATE_UNRESOLVED",
            reason="The subscription state cannot be evaluated safely.",
            current_subscription_id=current_subscription.subscription_id,
            current_subscription_state=current_subscription.status,
            current_tariff_family=current_tariff_family,
            requested_tariff_family=requested_tariff_family,
            paid_access_interval=request.paid_access_interval or current_subscription.effective_interval,
            source_references=(current_subscription.subscription_id,),
        )

    if request.requested_action is SubscriptionLifecycleAction.ASSIGN:
        if current_subscription is not None and current_subscription.status is SubscriptionState.ACTIVE:
            return _build_decision(
                request,
                outcome=SubscriptionLifecycleOutcome.CONFLICT,
                reason_code="ACTIVE_SUBSCRIPTION_ASSIGN_CONFLICT",
                reason="An active subscription already exists, so assign cannot silently succeed.",
                current_subscription_id=current_subscription.subscription_id,
                current_subscription_state=current_subscription.status,
                current_tariff_family=current_tariff_family,
                requested_tariff_family=requested_tariff_family,
                paid_access_interval=request.paid_access_interval or current_subscription.effective_interval,
                source_references=(current_subscription.subscription_id,),
            )
        if approved_requested_tariff in {TariffName.FREE, TariffName.BASIC}:
            return _build_decision(
                request,
                outcome=SubscriptionLifecycleOutcome.ASSIGNED,
                reason_code="SUBSCRIPTION_ASSIGNED",
                reason="The approved subscription family is assigned deterministically.",
                current_subscription_id=current_subscription.subscription_id if current_subscription else None,
                current_subscription_state=current_subscription.status if current_subscription else None,
                current_tariff_family=current_tariff_family,
                requested_tariff_family=requested_tariff_family,
                paid_access_interval=request.paid_access_interval
                or (current_subscription.effective_interval if current_subscription else None),
                source_references=(
                    requested_tariff_family or "",
                    approved_requested_tariff.value if approved_requested_tariff else "",
                ),
            )
        return _build_decision(
            request,
            outcome=SubscriptionLifecycleOutcome.BLOCKED,
            reason_code="SUBSCRIPTION_STATE_UNRESOLVED",
            reason="The requested tariff family cannot be assigned safely.",
        )

    if request.requested_action is SubscriptionLifecycleAction.CHANGE:
        if current_subscription is None:
            return _build_decision(
                request,
                outcome=SubscriptionLifecycleOutcome.CONFLICT,
                reason_code="CURRENT_SUBSCRIPTION_REQUIRED",
                reason="A current subscription is required before change semantics can succeed.",
                requested_tariff_family=requested_tariff_family,
            )
        if approved_requested_tariff is None:
            return _build_decision(
                request,
                outcome=SubscriptionLifecycleOutcome.BLOCKED,
                reason_code="UNSUPPORTED_TARIFF_FAMILY",
                reason="The requested tariff family is not part of the approved Free/Basic policy.",
                current_subscription_id=current_subscription.subscription_id,
                current_subscription_state=current_subscription.status,
                current_tariff_family=current_tariff_family,
                requested_tariff_family=requested_tariff_family,
                paid_access_interval=request.paid_access_interval or current_subscription.effective_interval,
            )
        if current_subscription.status is not SubscriptionState.ACTIVE:
            return _build_decision(
                request,
                outcome=SubscriptionLifecycleOutcome.CONFLICT,
                reason_code="CURRENT_SUBSCRIPTION_STATE_CONFLICT",
                reason="The current subscription state is not active, so a safe change cannot be proven.",
                current_subscription_id=current_subscription.subscription_id,
                current_subscription_state=current_subscription.status,
                current_tariff_family=current_tariff_family,
                requested_tariff_family=requested_tariff_family,
                paid_access_interval=request.paid_access_interval or current_subscription.effective_interval,
            )
        if requested_tariff_family == current_tariff_family:
            return _build_decision(
                request,
                outcome=SubscriptionLifecycleOutcome.CONFLICT,
                reason_code="NO_STATE_CHANGE_CONFLICT",
                reason="Requested and current tariff families are identical, so a change cannot silently succeed.",
                current_subscription_id=current_subscription.subscription_id,
                current_subscription_state=current_subscription.status,
                current_tariff_family=current_tariff_family,
                requested_tariff_family=requested_tariff_family,
                paid_access_interval=request.paid_access_interval or current_subscription.effective_interval,
                source_references=(current_subscription.subscription_id, current_tariff_family or ""),
            )
        return _build_decision(
            request,
            outcome=SubscriptionLifecycleOutcome.CHANGED,
            reason_code="SUBSCRIPTION_CHANGED",
            reason="The approved subscription family change is deterministic and manual-only.",
            current_subscription_id=current_subscription.subscription_id,
            current_subscription_state=current_subscription.status,
            current_tariff_family=current_tariff_family,
            requested_tariff_family=requested_tariff_family,
            paid_access_interval=request.paid_access_interval or current_subscription.effective_interval,
            source_references=(
                current_subscription.subscription_id,
                current_tariff_family or "",
                requested_tariff_family,
            ),
        )

    if request.requested_action is SubscriptionLifecycleAction.CANCEL:
        if current_subscription is None:
            return _build_decision(
                request,
                outcome=SubscriptionLifecycleOutcome.BLOCKED,
                reason_code="CURRENT_SUBSCRIPTION_REQUIRED",
                reason="A current subscription is required before cancellation semantics can be evaluated.",
            )
        if current_subscription.status is SubscriptionState.CANCELLED:
            return _build_decision(
                request,
                outcome=SubscriptionLifecycleOutcome.REPLAYED,
                terminal_outcome=SubscriptionLifecycleOutcome.CANCELLED,
                reason_code="IDEMPOTENT_CANCEL_REPLAY",
                reason="The cancellation has already been applied and only replays deterministically.",
                current_subscription_id=current_subscription.subscription_id,
                current_subscription_state=current_subscription.status,
                current_tariff_family=current_tariff_family,
                requested_tariff_family=requested_tariff_family,
                paid_access_interval=request.paid_access_interval or current_subscription.effective_interval,
                source_references=(current_subscription.subscription_id,),
            )
        return _build_decision(
            request,
            outcome=SubscriptionLifecycleOutcome.CANCELLED,
            reason_code="SUBSCRIPTION_CANCELLED",
            reason="The subscription is cancelled semantically without refund or Beacon mutation.",
            current_subscription_id=current_subscription.subscription_id,
            current_subscription_state=current_subscription.status,
            current_tariff_family=current_tariff_family,
            requested_tariff_family=requested_tariff_family,
            paid_access_interval=request.paid_access_interval or current_subscription.effective_interval,
            source_references=(current_subscription.subscription_id,),
        )

    if request.requested_action is SubscriptionLifecycleAction.EXPIRE:
        if current_subscription is None:
            return _build_decision(
                request,
                outcome=SubscriptionLifecycleOutcome.BLOCKED,
                reason_code="CURRENT_SUBSCRIPTION_REQUIRED",
                reason="A current subscription is required before expiration semantics can be evaluated.",
            )
        return _build_decision(
            request,
            outcome=SubscriptionLifecycleOutcome.EXPIRED,
            reason_code="SUBSCRIPTION_EXPIRED",
            reason="The subscription is represented as expired without any runtime side effects.",
            current_subscription_id=current_subscription.subscription_id,
            current_subscription_state=current_subscription.status,
            current_tariff_family=current_tariff_family,
            requested_tariff_family=requested_tariff_family,
            paid_access_interval=request.paid_access_interval or current_subscription.effective_interval,
            source_references=(current_subscription.subscription_id,),
        )

    if request.requested_action is SubscriptionLifecycleAction.RENEW:
        if current_subscription is None:
            return _build_decision(
                request,
                outcome=SubscriptionLifecycleOutcome.BLOCKED,
                reason_code="CURRENT_SUBSCRIPTION_REQUIRED",
                reason="A current subscription is required before renewal semantics can be evaluated.",
                requested_tariff_family=requested_tariff_family,
                payment_evidence_references=payment_references,
                source_references=payment_references,
            )
        if payment_references:
            return _build_decision(
                request,
                outcome=SubscriptionLifecycleOutcome.PENDING,
                reason_code="PAYMENT_EVIDENCE_PENDING_MANUAL_RENEWAL",
                reason="Payment evidence remains external evidence only; manual renewal must be authorized directly.",
                current_subscription_id=current_subscription.subscription_id,
                current_subscription_state=current_subscription.status,
                current_tariff_family=current_tariff_family,
                requested_tariff_family=requested_tariff_family,
                paid_access_interval=request.paid_access_interval or current_subscription.effective_interval,
                payment_evidence_references=payment_references,
                source_references=payment_references,
            )
        return _build_decision(
            request,
            outcome=SubscriptionLifecycleOutcome.CHANGED,
            reason_code="MANUAL_RENEWAL_AUTHORIZED",
            reason="The subscription renewal is manually authorized and represented without provider runtime.",
            current_subscription_id=current_subscription.subscription_id,
            current_subscription_state=current_subscription.status,
            current_tariff_family=current_tariff_family,
            requested_tariff_family=requested_tariff_family,
            paid_access_interval=request.paid_access_interval or current_subscription.effective_interval,
            source_references=(current_subscription.subscription_id, requested_tariff_family or current_tariff_family or ""),
        )

    return _build_decision(
        request,
        outcome=SubscriptionLifecycleOutcome.BLOCKED,
        reason_code="REQUEST_ACTION_UNSUPPORTED",
        reason="The requested lifecycle action is not part of the approved deterministic semantic scope.",
        current_subscription_id=current_subscription.subscription_id if current_subscription else None,
        current_subscription_state=current_subscription.status if current_subscription else None,
        current_tariff_family=current_tariff_family,
        requested_tariff_family=requested_tariff_family,
        paid_access_interval=request.paid_access_interval or (current_subscription.effective_interval if current_subscription else None),
        payment_evidence_references=payment_references,
        source_references=payment_references,
    )


__all__ = [
    "APPROVED_SUBSCRIPTION_TARIFF_FAMILIES",
    "BASIC_TARIFF_POLICY",
    "FREE_TARIFF_POLICY",
    "FUTURE_DECISION_GATES",
    "GRACE_SEMANTICS_SUPPORTED",
    "PRORATION_SEMANTICS_SUPPORTED",
    "SUBSCRIPTION_TARIFF_FAMILY_BASIC",
    "SUBSCRIPTION_TARIFF_FAMILY_FREE",
    "SubscriptionLifecycleAction",
    "SubscriptionLifecycleActorContext",
    "SubscriptionLifecycleDecision",
    "SubscriptionLifecycleIdempotencyRecord",
    "SubscriptionLifecycleOutcome",
    "SubscriptionLifecycleRequest",
    "SubscriptionPaymentMode",
    "TRIAL_SEMANTICS_SUPPORTED",
    "compute_subscription_lifecycle_request_fingerprint",
    "evaluate_subscription_lifecycle",
]
