"""Pure deterministic semantic evaluator for Entitlements & Billing."""

from __future__ import annotations

from datetime import datetime
from typing import Final

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .contracts import (
    EffectiveEntitlementDecision,
    EffectiveInterval,
    EntitlementDecisionStatus,
    EntitlementGrant,
    ManualAccessGrant,
    ManualAccessGrantState,
    PaymentEvent,
    PaymentRecord,
    Subscription,
    SubscriptionState,
    TariffDefinition,
)
from .policies import APPROVED_TARIFF_DEFINITIONS, FREE_TARIFF_POLICY, TARIFFS_BY_NAME

SUPPORTED_REQUESTED_CAPABILITIES: Final[tuple[str, ...]] = ("beacon.scan",)
SUPPORTED_REQUESTED_SCOPES: Final[tuple[str, ...]] = ("beacon.scan",)


class EffectiveEntitlementEvaluationRequest(BaseModel):
    """Explicit synthetic-contract input for the semantic evaluator."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    target_account_id: str = Field(min_length=1)
    scope_account_id: str | None = None
    requested_capability: str = Field(min_length=1)
    requested_scope: str = Field(min_length=1)
    requested_interval_minutes: int | None = Field(default=None, gt=0)
    evaluated_at: datetime
    subscription: Subscription | None = None
    tariff_policy: TariffDefinition
    entitlement_grants: tuple[EntitlementGrant, ...] = Field(default_factory=tuple)
    manual_access_grants: tuple[ManualAccessGrant, ...] = Field(default_factory=tuple)
    payment_records: tuple[PaymentRecord, ...] = Field(default_factory=tuple)
    payment_events: tuple[PaymentEvent, ...] = Field(default_factory=tuple)
    approved_tariff_definitions: tuple[TariffDefinition, ...] = Field(
        default_factory=lambda: APPROVED_TARIFF_DEFINITIONS
    )

    @model_validator(mode="after")
    def _validate_tariff_policy_reference(self) -> "EffectiveEntitlementEvaluationRequest":
        if self.tariff_policy not in self.approved_tariff_definitions:
            raise ValueError("tariff_policy must reference an approved tariff definition")
        return self


def _unique_non_empty(*values: str | None) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value is None or not value.strip():
            continue
        if value not in seen:
            seen.add(value)
            ordered.append(value)
    return tuple(ordered)


def _decision_id(*parts: str) -> str:
    return "decision-" + "-".join(part.replace(" ", "_") for part in parts if part)


def _interval_contains(interval: EffectiveInterval, evaluated_at: datetime) -> bool:
    return interval.starts_at <= evaluated_at < interval.ends_at


def _is_interval_compliant(policy: TariffDefinition, requested_interval_minutes: int | None) -> bool:
    if requested_interval_minutes is None:
        return False
    if requested_interval_minutes < policy.scan_interval_floor_minutes:
        return False
    return (
        requested_interval_minutes - policy.scan_interval_floor_minutes
    ) % policy.scan_interval_step_minutes == 0


def _build_decision(
    request: EffectiveEntitlementEvaluationRequest,
    *,
    status: EntitlementDecisionStatus,
    reason_code: str,
    reason: str,
    source_references: tuple[str, ...] = (),
    effective_interval: EffectiveInterval | None = None,
    limit_value: int | None = None,
) -> EffectiveEntitlementDecision:
    return EffectiveEntitlementDecision(
        account_id=request.target_account_id,
        decision_id=_decision_id(
            request.target_account_id,
            request.requested_capability,
            request.requested_scope,
            str(request.requested_interval_minutes),
            request.evaluated_at.isoformat(),
            status.value,
            reason_code,
        ),
        status=status,
        reason_code=reason_code,
        reason=reason,
        evaluated_at=request.evaluated_at,
        capability=request.requested_capability,
        limit_value=limit_value,
        source_references=_unique_non_empty(*source_references),
        effective_interval=effective_interval,
    )


def _matching_active_manual_grants(
    request: EffectiveEntitlementEvaluationRequest,
) -> tuple[ManualAccessGrant, ...]:
    matches = []
    for grant in request.manual_access_grants:
        if grant.state is not ManualAccessGrantState.ACTIVE:
            continue
        if grant.account_id != request.target_account_id:
            continue
        if grant.scope != request.requested_scope:
            continue
        if grant.capability != request.requested_capability:
            continue
        if not _interval_contains(grant.effective_interval, request.evaluated_at):
            continue
        matches.append(grant)
    return tuple(matches)


def _matching_active_entitlement_grants(
    request: EffectiveEntitlementEvaluationRequest,
) -> tuple[EntitlementGrant, ...]:
    matches = []
    for grant in request.entitlement_grants:
        if grant.account_id != request.target_account_id:
            continue
        if grant.scope != request.requested_scope:
            continue
        if grant.capability != request.requested_capability:
            continue
        if grant.status != "ACTIVE":
            continue
        if not _interval_contains(grant.effective_interval, request.evaluated_at):
            continue
        matches.append(grant)
    return tuple(matches)


def evaluate_effective_entitlement(
    request: EffectiveEntitlementEvaluationRequest,
) -> EffectiveEntitlementDecision:
    """Evaluate deterministic entitlement semantics without runtime side effects."""

    if request.scope_account_id is None:
        return _build_decision(
            request,
            status=EntitlementDecisionStatus.BLOCKED,
            reason_code="ACCOUNT_SCOPE_REQUIRED",
            reason="An explicit account scope is required before entitlement evaluation.",
        )

    if request.scope_account_id != request.target_account_id:
        return _build_decision(
            request,
            status=EntitlementDecisionStatus.DENIED,
            reason_code="FOREIGN_ACCOUNT_SCOPE_DENIED",
            reason="Foreign-account inputs must not evaluate to access.",
        )

    if request.requested_capability not in SUPPORTED_REQUESTED_CAPABILITIES:
        return _build_decision(
            request,
            status=EntitlementDecisionStatus.UNSUPPORTED,
            reason_code="REQUESTED_CAPABILITY_UNSUPPORTED",
            reason="The requested capability is not part of the approved semantic evaluator scope.",
        )

    if request.requested_scope not in SUPPORTED_REQUESTED_SCOPES:
        return _build_decision(
            request,
            status=EntitlementDecisionStatus.UNSUPPORTED,
            reason_code="REQUESTED_SCOPE_UNSUPPORTED",
            reason="The requested scope is not part of the approved semantic evaluator scope.",
        )

    matching_manual_grants = _matching_active_manual_grants(request)
    if matching_manual_grants:
        grant = matching_manual_grants[0]
        return _build_decision(
            request,
            status=EntitlementDecisionStatus.ALLOWED,
            reason_code="MANUAL_ACCESS_GRANTED",
            reason="A valid manual access grant applies inside the explicit account, scope and interval.",
            source_references=(
                grant.grant_id,
                grant.audit_reference,
                grant.idempotency_key.value,
                grant.actor.actor_id,
            ),
            effective_interval=grant.effective_interval,
            limit_value=request.requested_interval_minutes,
        )

    active_subscription = request.subscription
    if active_subscription is not None and active_subscription.status is SubscriptionState.ACTIVE:
        approved_subscription_policy = TARIFFS_BY_NAME.get(active_subscription.tariff_name)
        if approved_subscription_policy is None:
            return _build_decision(
                request,
                status=EntitlementDecisionStatus.UNSUPPORTED,
                reason_code="ACTIVE_SUBSCRIPTION_TARIFF_UNSUPPORTED",
                reason="The active subscription references an unapproved tariff definition.",
                source_references=(active_subscription.subscription_id,),
            )

        if request.tariff_policy != approved_subscription_policy:
            return _build_decision(
                request,
                status=EntitlementDecisionStatus.CONFLICT,
                reason_code="TARIFF_POLICY_CONFLICT",
                reason="The subscription state and tariff policy reference disagree, so a safe decision is impossible.",
                source_references=(
                    active_subscription.subscription_id,
                    request.tariff_policy.tariff_name.value,
                    approved_subscription_policy.tariff_name.value,
                ),
            )

        matching_entitlement_grants = _matching_active_entitlement_grants(request)
        if matching_entitlement_grants:
            grant = matching_entitlement_grants[0]
            return _build_decision(
                request,
                status=EntitlementDecisionStatus.ALLOWED,
                reason_code="ENTITLEMENT_GRANT_ALLOWED",
                reason="A valid entitlement grant applies inside the explicit account, scope and interval.",
                source_references=(
                    active_subscription.subscription_id,
                    grant.grant_id,
                    grant.source_reference,
                    request.tariff_policy.tariff_name.value,
                ),
                effective_interval=grant.effective_interval,
                limit_value=request.requested_interval_minutes,
            )

        if request.requested_interval_minutes is None:
            return _build_decision(
                request,
                status=EntitlementDecisionStatus.AMBIGUOUS,
                reason_code="REQUEST_INTERVAL_REQUIRED",
                reason="The requested interval is required to evaluate the active tariff policy safely.",
                source_references=(active_subscription.subscription_id, request.tariff_policy.tariff_name.value),
                effective_interval=active_subscription.effective_interval,
            )

        if _is_interval_compliant(request.tariff_policy, request.requested_interval_minutes):
            return _build_decision(
                request,
                status=EntitlementDecisionStatus.ALLOWED,
                reason_code="BASELINE_TARIFF_ALLOWED",
                reason="The active subscription and approved tariff definition allow the requested interval.",
                source_references=(
                    active_subscription.subscription_id,
                    request.tariff_policy.tariff_name.value,
                ),
                effective_interval=active_subscription.effective_interval,
                limit_value=request.requested_interval_minutes,
            )

        return _build_decision(
            request,
            status=EntitlementDecisionStatus.DENIED,
            reason_code="REQUEST_INTERVAL_NOT_ALLOWED_BY_TARIFF",
            reason="The requested interval is outside the approved tariff policy and no in-scope grant overrides it.",
            source_references=(
                active_subscription.subscription_id,
                request.tariff_policy.tariff_name.value,
            ),
            effective_interval=active_subscription.effective_interval,
        )

    if active_subscription is not None and active_subscription.status in {
        SubscriptionState.EXPIRED,
        SubscriptionState.CANCELLED,
        SubscriptionState.SUSPENDED,
    }:
        reason_code = "PAID_ACCESS_EXPIRED_USER_CHOICE_REQUIRED"
        reason = (
            "Paid access has ended; the user must choose a Free-compliant Beacon and start it manually."
        )
        status = EntitlementDecisionStatus.USER_CHOICE_REQUIRED
        if request.requested_interval_minutes is not None and not _is_interval_compliant(
            FREE_TARIFF_POLICY, request.requested_interval_minutes
        ):
            reason_code = "PAID_ACCESS_EXPIRED_FREE_COMPLIANCE_REQUIRED"
            reason = "Paid access has ended and the requested interval must be brought into Free requirements."
            status = EntitlementDecisionStatus.FREE_COMPLIANCE_REQUIRED
        return _build_decision(
            request,
            status=status,
            reason_code=reason_code,
            reason=reason,
            source_references=(
                active_subscription.subscription_id,
                FREE_TARIFF_POLICY.tariff_name.value,
            ),
            effective_interval=active_subscription.effective_interval,
        )

    if active_subscription is None:
        if request.payment_records or request.payment_events:
            payment_references = tuple(
                record.payment_reference for record in request.payment_records
            ) + tuple(event.event_reference for event in request.payment_events)
            return _build_decision(
                request,
                status=EntitlementDecisionStatus.BLOCKED,
                reason_code="PAYMENT_IS_NOT_AUTHORITY",
                reason="Payment records and events are evidence only and do not grant entitlement authority.",
                source_references=payment_references,
            )

        return _build_decision(
            request,
            status=EntitlementDecisionStatus.BLOCKED,
            reason_code="SUBSCRIPTION_REQUIRED",
            reason="No active subscription, manual grant or entitlement grant can prove access.",
        )

    return _build_decision(
        request,
        status=EntitlementDecisionStatus.BLOCKED,
        reason_code="SUBSCRIPTION_STATE_UNRESOLVED",
        reason="The subscription state is not sufficient to prove a deterministic entitlement result.",
        source_references=(active_subscription.subscription_id,),
        effective_interval=active_subscription.effective_interval,
    )


__all__ = [
    "EffectiveEntitlementEvaluationRequest",
    "SUPPORTED_REQUESTED_CAPABILITIES",
    "SUPPORTED_REQUESTED_SCOPES",
    "evaluate_effective_entitlement",
]
