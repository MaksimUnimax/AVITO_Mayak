"""Deterministic semantic contracts for Beacon Management integration."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Final

from pydantic import BaseModel, ConfigDict, Field, model_validator

from mayak.platform.idempotency import IdempotencyFingerprint, IdempotencyKey

from .contracts import (
    EffectiveEntitlementDecision,
    EntitlementDecisionStatus,
    PaymentEvent,
    PaymentRecord,
)
from .subscription_lifecycle import SubscriptionLifecycleDecision, SubscriptionLifecycleOutcome
from .usage_consumption import UsageConsumptionDecision, UsageConsumptionOutcome

BEACON_MANAGEMENT_MODULE_LABEL: Final[str] = "Beacon Management"
BEACON_MANAGEMENT_SOURCE_FACTS_OWNER_LABEL: Final[str] = "Beacon Management"


class BeaconIntegrationRequesterModule(str, Enum):
    """Semantic requester labels for Beacon integration contracts."""

    BEACON_MANAGEMENT = BEACON_MANAGEMENT_MODULE_LABEL


class BeaconIntegrationSourceFactsOwner(str, Enum):
    """Semantic source-facts owner labels for Beacon integration contracts."""

    BEACON_MANAGEMENT = BEACON_MANAGEMENT_SOURCE_FACTS_OWNER_LABEL


class BeaconIntegrationRequestKind(str, Enum):
    """Semantic request kinds for Beacon integration contracts."""

    EFFECT = "EFFECT"
    MUTATION = "MUTATION"


class BeaconIntegrationCapability(str, Enum):
    """Requested Beacon integration capability families."""

    ACTIVE_BEACON_COUNT = "ACTIVE_BEACON_COUNT"
    GEOGRAPHY = "GEOGRAPHY"
    SCAN_INTERVAL_WINDOW = "SCAN_INTERVAL_WINDOW"
    FILTER_EDIT_CAPABILITY = "FILTER_EDIT_CAPABILITY"
    LIFECYCLE_EFFECT_GATE = "LIFECYCLE_EFFECT_GATE"


class BeaconIntegrationOutcome(str, Enum):
    """Pure semantic outcomes for Beacon integration contracts."""

    ALLOWED = "ALLOWED"
    DENIED = "DENIED"
    BLOCKED = "BLOCKED"
    AMBIGUOUS = "AMBIGUOUS"
    UNSUPPORTED = "UNSUPPORTED"
    USER_CHOICE_REQUIRED = "USER_CHOICE_REQUIRED"
    FREE_COMPLIANCE_REQUIRED = "FREE_COMPLIANCE_REQUIRED"
    REJECTED = "REJECTED"
    REPLAYED = "REPLAYED"
    IDEMPOTENCY_MISMATCH = "IDEMPOTENCY_MISMATCH"


class BeaconIntegrationIdempotencyRecord(BaseModel):
    """Explicit prior idempotency evidence for deterministic replay semantics."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    request_kind: BeaconIntegrationRequestKind
    idempotency_key: IdempotencyKey
    request_fingerprint: IdempotencyFingerprint
    terminal_outcome: BeaconIntegrationOutcome


class BeaconIntegrationRequest(BaseModel):
    """Explicit synthetic-contract input for Beacon integration semantics."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    account_id: str = Field(min_length=1)
    beacon_id: str | None = None
    requested_capability: BeaconIntegrationCapability
    requested_active_beacon_count: int | None = Field(default=None, ge=0)
    requested_geography_scope: str | None = None
    requested_scan_interval_minutes: int | None = Field(default=None, gt=0)
    requested_filter_edit_capability: str | None = None
    requested_lifecycle_effect: str | None = None
    requester_module: str = Field(min_length=1)
    source_facts_owner: str = Field(min_length=1)
    effective_entitlement_decision: EffectiveEntitlementDecision | None = None
    usage_consumption_decision: UsageConsumptionDecision | None = None
    subscription_lifecycle_decision: SubscriptionLifecycleDecision | None = None
    payment_records: tuple[PaymentRecord, ...] = Field(default_factory=tuple)
    payment_events: tuple[PaymentEvent, ...] = Field(default_factory=tuple)
    decision_at: datetime
    request_kind: BeaconIntegrationRequestKind = BeaconIntegrationRequestKind.EFFECT
    idempotency_key: IdempotencyKey | None = None
    prior_idempotency_record: BeaconIntegrationIdempotencyRecord | None = None

    @model_validator(mode="after")
    def _validate_labels(self) -> "BeaconIntegrationRequest":
        if self.requester_module != BEACON_MANAGEMENT_MODULE_LABEL:
            raise ValueError("requester_module must be Beacon Management")
        if self.source_facts_owner != BEACON_MANAGEMENT_SOURCE_FACTS_OWNER_LABEL:
            raise ValueError("source_facts_owner must be Beacon Management")
        return self


class BeaconIntegrationDecision(BaseModel):
    """Pure semantic decision for Beacon integration contracts."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    account_id: str = Field(min_length=1)
    beacon_id: str | None = None
    requested_capability: BeaconIntegrationCapability
    requested_active_beacon_count: int | None = Field(default=None, ge=0)
    requested_geography_scope: str | None = None
    requested_scan_interval_minutes: int | None = Field(default=None, gt=0)
    requested_filter_edit_capability: str | None = None
    requested_lifecycle_effect: str | None = None
    request_kind: BeaconIntegrationRequestKind
    requester_module: str = Field(min_length=1)
    source_facts_owner: str = Field(min_length=1)
    outcome: BeaconIntegrationOutcome
    terminal_outcome: BeaconIntegrationOutcome
    reason_code: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    decision_at: datetime
    idempotency_key: IdempotencyKey | None = None
    request_fingerprint: IdempotencyFingerprint
    effective_entitlement_status: EntitlementDecisionStatus | None = None
    usage_consumption_outcome: UsageConsumptionOutcome | None = None
    subscription_lifecycle_outcome: SubscriptionLifecycleOutcome | None = None
    source_references: tuple[str, ...] = Field(default_factory=tuple)
    history_preserved: bool = True

    @model_validator(mode="after")
    def _validate_terminal_outcome(self) -> "BeaconIntegrationDecision":
        if self.outcome is not BeaconIntegrationOutcome.REPLAYED and self.outcome != self.terminal_outcome:
            raise ValueError("terminal outcome must match the current outcome except for replayed decisions")
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


def _request_fingerprint(request: BeaconIntegrationRequest) -> IdempotencyFingerprint:
    return IdempotencyFingerprint(
        value=(
            "beacon-integration:"
            f"{request.model_dump_json(exclude={'idempotency_key', 'prior_idempotency_record', 'decision_at'})}"
        )
    )


def compute_beacon_integration_request_fingerprint(
    request: BeaconIntegrationRequest,
) -> IdempotencyFingerprint:
    """Public deterministic helper for Beacon integration idempotency contracts/tests."""

    return _request_fingerprint(request)


def _build_decision(
    request: BeaconIntegrationRequest,
    *,
    outcome: BeaconIntegrationOutcome,
    reason_code: str,
    reason: str,
    source_references: tuple[str, ...] = (),
    terminal_outcome: BeaconIntegrationOutcome | None = None,
    effective_entitlement_status: EntitlementDecisionStatus | None = None,
    usage_consumption_outcome: UsageConsumptionOutcome | None = None,
    subscription_lifecycle_outcome: SubscriptionLifecycleOutcome | None = None,
) -> BeaconIntegrationDecision:
    return BeaconIntegrationDecision(
        account_id=request.account_id,
        beacon_id=request.beacon_id,
        requested_capability=request.requested_capability,
        requested_active_beacon_count=request.requested_active_beacon_count,
        requested_geography_scope=request.requested_geography_scope,
        requested_scan_interval_minutes=request.requested_scan_interval_minutes,
        requested_filter_edit_capability=request.requested_filter_edit_capability,
        requested_lifecycle_effect=request.requested_lifecycle_effect,
        request_kind=request.request_kind,
        requester_module=request.requester_module,
        source_facts_owner=request.source_facts_owner,
        outcome=outcome,
        terminal_outcome=terminal_outcome or outcome,
        reason_code=reason_code,
        reason=reason,
        decision_at=request.decision_at,
        idempotency_key=request.idempotency_key,
        request_fingerprint=_request_fingerprint(request),
        effective_entitlement_status=effective_entitlement_status,
        usage_consumption_outcome=usage_consumption_outcome,
        subscription_lifecycle_outcome=subscription_lifecycle_outcome,
        source_references=_unique_non_empty(*source_references),
        history_preserved=True,
    )


def _subscription_terminal_outcome(
    decision: SubscriptionLifecycleDecision,
) -> SubscriptionLifecycleOutcome:
    return decision.terminal_outcome if decision.outcome is SubscriptionLifecycleOutcome.REPLAYED else decision.outcome


def _usage_terminal_outcome(
    decision: UsageConsumptionDecision,
) -> UsageConsumptionOutcome:
    return decision.terminal_outcome if decision.outcome is UsageConsumptionOutcome.REPLAYED else decision.outcome


def _usage_outcome_to_beacon_outcome(
    decision: UsageConsumptionDecision,
) -> BeaconIntegrationOutcome:
    terminal_outcome = _usage_terminal_outcome(decision)
    if terminal_outcome is UsageConsumptionOutcome.ACCEPTED:
        return BeaconIntegrationOutcome.ALLOWED
    if terminal_outcome is UsageConsumptionOutcome.DENIED:
        return BeaconIntegrationOutcome.DENIED
    if terminal_outcome in {UsageConsumptionOutcome.BLOCKED, UsageConsumptionOutcome.UNAVAILABLE}:
        return BeaconIntegrationOutcome.BLOCKED
    if terminal_outcome is UsageConsumptionOutcome.CONFLICT:
        return BeaconIntegrationOutcome.AMBIGUOUS
    if terminal_outcome is UsageConsumptionOutcome.REJECTED:
        return BeaconIntegrationOutcome.REJECTED
    if terminal_outcome is UsageConsumptionOutcome.IDEMPOTENCY_MISMATCH:
        return BeaconIntegrationOutcome.IDEMPOTENCY_MISMATCH
    return BeaconIntegrationOutcome.BLOCKED


def _entitlement_status_to_outcome(
    status: EntitlementDecisionStatus,
) -> BeaconIntegrationOutcome | None:
    if status is EntitlementDecisionStatus.ALLOWED:
        return None
    if status is EntitlementDecisionStatus.DENIED:
        return BeaconIntegrationOutcome.DENIED
    if status is EntitlementDecisionStatus.BLOCKED:
        return BeaconIntegrationOutcome.BLOCKED
    if status is EntitlementDecisionStatus.AMBIGUOUS:
        return BeaconIntegrationOutcome.AMBIGUOUS
    if status is EntitlementDecisionStatus.UNSUPPORTED:
        return BeaconIntegrationOutcome.UNSUPPORTED
    if status is EntitlementDecisionStatus.USER_CHOICE_REQUIRED:
        return BeaconIntegrationOutcome.USER_CHOICE_REQUIRED
    if status is EntitlementDecisionStatus.FREE_COMPLIANCE_REQUIRED:
        return BeaconIntegrationOutcome.FREE_COMPLIANCE_REQUIRED
    if status is EntitlementDecisionStatus.CONFLICT:
        return BeaconIntegrationOutcome.AMBIGUOUS
    if status is EntitlementDecisionStatus.EXPIRED:
        return BeaconIntegrationOutcome.USER_CHOICE_REQUIRED
    return BeaconIntegrationOutcome.BLOCKED


def _subscription_outcome_to_beacon_outcome(
    decision: SubscriptionLifecycleDecision,
) -> BeaconIntegrationOutcome | None:
    terminal_outcome = _subscription_terminal_outcome(decision)
    if terminal_outcome is SubscriptionLifecycleOutcome.USER_CHOICE_REQUIRED:
        return BeaconIntegrationOutcome.USER_CHOICE_REQUIRED
    if terminal_outcome is SubscriptionLifecycleOutcome.FREE_COMPLIANCE_REQUIRED:
        return BeaconIntegrationOutcome.FREE_COMPLIANCE_REQUIRED
    return None


def _expires_without_auto_choice(
    request: BeaconIntegrationRequest,
    *,
    subscription_lifecycle_decision: SubscriptionLifecycleDecision | None = None,
    effective_entitlement_status: EntitlementDecisionStatus | None = None,
) -> BeaconIntegrationDecision | None:
    if subscription_lifecycle_decision is not None:
        subscription_outcome = _subscription_outcome_to_beacon_outcome(subscription_lifecycle_decision)
        if subscription_outcome is not None:
            return _build_decision(
                request,
                outcome=subscription_outcome,
                reason_code=(
                    "EXPIRED_PAID_ACCESS_USER_CHOICE_REQUIRED"
                    if subscription_outcome is BeaconIntegrationOutcome.USER_CHOICE_REQUIRED
                    else "EXPIRED_PAID_ACCESS_FREE_COMPLIANCE_REQUIRED"
                ),
                reason=(
                    "Expired paid access requires a user choice; Beacon Management must not choose automatically."
                    if subscription_outcome is BeaconIntegrationOutcome.USER_CHOICE_REQUIRED
                    else "Expired paid access requires Free compliance; Beacon Management must not choose automatically."
                ),
                source_references=_unique_non_empty(
                    request.beacon_id,
                    subscription_lifecycle_decision.request_fingerprint.value,
                ),
                effective_entitlement_status=effective_entitlement_status,
                subscription_lifecycle_outcome=_subscription_terminal_outcome(subscription_lifecycle_decision),
            )

    if effective_entitlement_status is EntitlementDecisionStatus.USER_CHOICE_REQUIRED:
        return _build_decision(
            request,
            outcome=BeaconIntegrationOutcome.USER_CHOICE_REQUIRED,
            reason_code="EXPIRED_PAID_ACCESS_USER_CHOICE_REQUIRED",
            reason="Expired paid access requires a user choice; Beacon Management must not choose automatically.",
            source_references=_unique_non_empty(request.beacon_id),
            effective_entitlement_status=effective_entitlement_status,
        )

    if effective_entitlement_status is EntitlementDecisionStatus.FREE_COMPLIANCE_REQUIRED:
        return _build_decision(
            request,
            outcome=BeaconIntegrationOutcome.FREE_COMPLIANCE_REQUIRED,
            reason_code="EXPIRED_PAID_ACCESS_FREE_COMPLIANCE_REQUIRED",
            reason="Expired paid access requires Free compliance; Beacon Management must not choose automatically.",
            source_references=_unique_non_empty(request.beacon_id),
            effective_entitlement_status=effective_entitlement_status,
        )

    if effective_entitlement_status is EntitlementDecisionStatus.EXPIRED:
        return _build_decision(
            request,
            outcome=BeaconIntegrationOutcome.USER_CHOICE_REQUIRED,
            reason_code="EXPIRED_PAID_ACCESS_USER_CHOICE_REQUIRED",
            reason="Expired paid access requires a user choice; Beacon Management must not choose automatically.",
            source_references=_unique_non_empty(request.beacon_id),
            effective_entitlement_status=effective_entitlement_status,
        )

    return None


def _validate_effect_evidence(
    request: BeaconIntegrationRequest,
) -> BeaconIntegrationDecision | None:
    entitlement_decision = request.effective_entitlement_decision
    if entitlement_decision is None:
        if request.payment_records or request.payment_events:
            payment_references = tuple(record.payment_reference for record in request.payment_records) + tuple(
                event.event_reference for event in request.payment_events
            )
            return _build_decision(
                request,
                outcome=BeaconIntegrationOutcome.BLOCKED,
                reason_code="PAYMENT_IS_NOT_AUTHORITY",
                reason="Payment records and events are external evidence only and do not grant Beacon effect authority.",
                source_references=payment_references,
            )

        return _build_decision(
            request,
            outcome=BeaconIntegrationOutcome.BLOCKED,
            reason_code="ENTITLEMENT_DECISION_REQUIRED",
            reason="A deterministic effective entitlement decision is required before Beacon effect can be evaluated.",
        )

    expired_decision = _expires_without_auto_choice(
        request,
        subscription_lifecycle_decision=request.subscription_lifecycle_decision,
        effective_entitlement_status=entitlement_decision.status,
    )
    if expired_decision is not None:
        return expired_decision

    entitlement_outcome = _entitlement_status_to_outcome(entitlement_decision.status)
    if entitlement_outcome is not None:
        return _build_decision(
            request,
            outcome=entitlement_outcome,
            reason_code=f"ENTITLEMENT_{entitlement_decision.status.value}",
            reason="The effective entitlement decision does not allow Beacon effect without guessing.",
            source_references=_unique_non_empty(
                entitlement_decision.decision_id,
                *entitlement_decision.source_references,
            ),
            effective_entitlement_status=entitlement_decision.status,
        )

    return None


def _active_beacon_count_decision(
    request: BeaconIntegrationRequest,
    *,
    entitlement_decision: EffectiveEntitlementDecision,
) -> BeaconIntegrationDecision:
    usage_decision = request.usage_consumption_decision
    if request.requested_active_beacon_count is None:
        return _build_decision(
            request,
            outcome=BeaconIntegrationOutcome.BLOCKED,
            reason_code="ACTIVE_BEACON_COUNT_REQUEST_REQUIRED",
            reason="An explicit active Beacon count request is required for this semantic contract.",
            source_references=_unique_non_empty(entitlement_decision.decision_id),
            effective_entitlement_status=entitlement_decision.status,
        )

    if usage_decision is None:
        return _build_decision(
            request,
            outcome=BeaconIntegrationOutcome.BLOCKED,
            reason_code="ACTIVE_BEACON_COUNT_EVIDENCE_REQUIRED",
            reason="Synthetic usage-consumption evidence is required before active Beacon count can be allowed.",
            source_references=_unique_non_empty(entitlement_decision.decision_id),
            effective_entitlement_status=entitlement_decision.status,
        )

    usage_outcome = _usage_outcome_to_beacon_outcome(usage_decision)
    if usage_outcome is not BeaconIntegrationOutcome.ALLOWED:
        return _build_decision(
            request,
            outcome=usage_outcome,
            reason_code=f"ACTIVE_BEACON_COUNT_{usage_outcome.value}",
            reason="The active Beacon slot evidence does not support a semantic effect.",
            source_references=_unique_non_empty(
                entitlement_decision.decision_id,
                usage_decision.request_fingerprint.value,
                request.beacon_id,
            ),
            effective_entitlement_status=entitlement_decision.status,
            usage_consumption_outcome=_usage_terminal_outcome(usage_decision),
        )

    if usage_decision.active_beacon_count != request.requested_active_beacon_count:
        return _build_decision(
            request,
            outcome=BeaconIntegrationOutcome.AMBIGUOUS,
            reason_code="ACTIVE_BEACON_COUNT_EVIDENCE_CONFLICT",
            reason="The requested active Beacon count does not match the synthetic usage evidence.",
            source_references=_unique_non_empty(
                entitlement_decision.decision_id,
                usage_decision.request_fingerprint.value,
                request.beacon_id,
            ),
            effective_entitlement_status=entitlement_decision.status,
            usage_consumption_outcome=_usage_terminal_outcome(usage_decision),
        )

    return _build_decision(
        request,
        outcome=BeaconIntegrationOutcome.ALLOWED,
        reason_code="ACTIVE_BEACON_COUNT_ALLOWED",
        reason="Beacon Management may apply the semantic effect because entitlement and usage evidence are both consistent.",
        source_references=_unique_non_empty(
            entitlement_decision.decision_id,
            usage_decision.request_fingerprint.value,
            request.beacon_id,
        ),
        effective_entitlement_status=entitlement_decision.status,
        usage_consumption_outcome=_usage_terminal_outcome(usage_decision),
    )


def _scan_interval_decision(
    request: BeaconIntegrationRequest,
    *,
    entitlement_decision: EffectiveEntitlementDecision,
) -> BeaconIntegrationDecision:
    usage_decision = request.usage_consumption_decision
    if request.requested_scan_interval_minutes is None:
        return _build_decision(
            request,
            outcome=BeaconIntegrationOutcome.BLOCKED,
            reason_code="SCAN_INTERVAL_REQUEST_REQUIRED",
            reason="An explicit scan interval request is required for this semantic contract.",
            source_references=_unique_non_empty(entitlement_decision.decision_id),
            effective_entitlement_status=entitlement_decision.status,
        )

    if usage_decision is None:
        return _build_decision(
            request,
            outcome=BeaconIntegrationOutcome.BLOCKED,
            reason_code="SCAN_INTERVAL_EVIDENCE_REQUIRED",
            reason="Synthetic usage-consumption evidence is required before scan interval can be allowed.",
            source_references=_unique_non_empty(entitlement_decision.decision_id),
            effective_entitlement_status=entitlement_decision.status,
        )

    usage_outcome = _usage_outcome_to_beacon_outcome(usage_decision)
    if usage_outcome is not BeaconIntegrationOutcome.ALLOWED:
        return _build_decision(
            request,
            outcome=usage_outcome,
            reason_code=f"SCAN_INTERVAL_WINDOW_{usage_outcome.value}",
            reason="The scan interval evidence does not support a semantic effect.",
            source_references=_unique_non_empty(
                entitlement_decision.decision_id,
                usage_decision.request_fingerprint.value,
                request.beacon_id,
            ),
            effective_entitlement_status=entitlement_decision.status,
            usage_consumption_outcome=_usage_terminal_outcome(usage_decision),
        )

    if usage_decision.scan_interval_minutes != request.requested_scan_interval_minutes:
        return _build_decision(
            request,
            outcome=BeaconIntegrationOutcome.AMBIGUOUS,
            reason_code="SCAN_INTERVAL_EVIDENCE_CONFLICT",
            reason="The requested scan interval does not match the synthetic usage evidence.",
            source_references=_unique_non_empty(
                entitlement_decision.decision_id,
                usage_decision.request_fingerprint.value,
                request.beacon_id,
            ),
            effective_entitlement_status=entitlement_decision.status,
            usage_consumption_outcome=_usage_terminal_outcome(usage_decision),
        )

    return _build_decision(
        request,
        outcome=BeaconIntegrationOutcome.ALLOWED,
        reason_code="SCAN_INTERVAL_WINDOW_ALLOWED",
        reason="Beacon Management may apply the semantic effect because entitlement and timing evidence are both consistent.",
        source_references=_unique_non_empty(
            entitlement_decision.decision_id,
            usage_decision.request_fingerprint.value,
            request.beacon_id,
        ),
        effective_entitlement_status=entitlement_decision.status,
        usage_consumption_outcome=_usage_terminal_outcome(usage_decision),
    )


def evaluate_beacon_integration(
    request: BeaconIntegrationRequest,
) -> BeaconIntegrationDecision:
    """Evaluate deterministic Beacon Management integration semantics without side effects."""

    request_fingerprint = _request_fingerprint(request)
    if request.request_kind is BeaconIntegrationRequestKind.MUTATION:
        if request.idempotency_key is None:
            return _build_decision(
                request,
                outcome=BeaconIntegrationOutcome.REJECTED,
                reason_code="IDEMPOTENCY_KEY_REQUIRED",
                reason="Beacon integration mutation-like semantics require an idempotency key before any effect.",
            )
        if request.prior_idempotency_record is not None:
            prior = request.prior_idempotency_record
            if prior.idempotency_key != request.idempotency_key or prior.request_fingerprint != request_fingerprint:
                return _build_decision(
                    request,
                    outcome=BeaconIntegrationOutcome.IDEMPOTENCY_MISMATCH,
                    reason_code="IDEMPOTENCY_MISMATCH",
                    reason="The same Beacon integration idempotency key was reused for a different request fingerprint.",
                    source_references=_unique_non_empty(
                        prior.idempotency_key.value,
                        prior.request_fingerprint.value,
                    ),
                )
            return _build_decision(
                request,
                outcome=BeaconIntegrationOutcome.REPLAYED,
                terminal_outcome=prior.terminal_outcome,
                reason_code="IDEMPOTENT_REPLAY",
                reason="The Beacon integration request replays the original terminal outcome deterministically.",
                source_references=_unique_non_empty(
                    prior.idempotency_key.value,
                    prior.request_fingerprint.value,
                ),
            )
    elif request.prior_idempotency_record is not None:
        prior = request.prior_idempotency_record
        if request.idempotency_key is None:
            return _build_decision(
                request,
                outcome=BeaconIntegrationOutcome.REJECTED,
                reason_code="IDEMPOTENCY_KEY_REQUIRED",
                reason="Beacon integration replay evidence requires an idempotency key before any effect.",
            )
        if prior.idempotency_key != request.idempotency_key or prior.request_fingerprint != request_fingerprint:
            return _build_decision(
                request,
                outcome=BeaconIntegrationOutcome.IDEMPOTENCY_MISMATCH,
                reason_code="IDEMPOTENCY_MISMATCH",
                reason="The Beacon integration replay evidence does not match the current request fingerprint.",
                source_references=_unique_non_empty(
                    prior.idempotency_key.value,
                    prior.request_fingerprint.value,
                ),
            )
        return _build_decision(
            request,
            outcome=BeaconIntegrationOutcome.REPLAYED,
            terminal_outcome=prior.terminal_outcome,
            reason_code="IDEMPOTENT_REPLAY",
            reason="The Beacon integration request replays the original terminal outcome deterministically.",
            source_references=_unique_non_empty(
                prior.idempotency_key.value,
                prior.request_fingerprint.value,
            ),
        )

    entitlement_validation = _validate_effect_evidence(request)
    if entitlement_validation is not None:
        return entitlement_validation

    entitlement_decision = request.effective_entitlement_decision
    assert entitlement_decision is not None

    if request.requested_capability is BeaconIntegrationCapability.GEOGRAPHY:
        return _build_decision(
            request,
            outcome=BeaconIntegrationOutcome.BLOCKED,
            reason_code="OD010_GEOGRAPHY_BLOCKED",
            reason="Country-wide and geography support remains open, so Beacon Management must not invent rights.",
            source_references=_unique_non_empty(
                entitlement_decision.decision_id,
                request.beacon_id,
                request.requested_geography_scope,
            ),
            effective_entitlement_status=entitlement_decision.status,
        )

    if request.requested_capability is BeaconIntegrationCapability.FILTER_EDIT_CAPABILITY:
        return _build_decision(
            request,
            outcome=BeaconIntegrationOutcome.UNSUPPORTED,
            reason_code="FILTER_EDIT_CAPABILITY_UNSUPPORTED",
            reason="Exact filter-edit capability support remains outside the accepted Beacon integration contract.",
            source_references=_unique_non_empty(
                entitlement_decision.decision_id,
                request.beacon_id,
                request.requested_filter_edit_capability,
            ),
            effective_entitlement_status=entitlement_decision.status,
        )

    if request.requested_capability is BeaconIntegrationCapability.LIFECYCLE_EFFECT_GATE:
        return _build_decision(
            request,
            outcome=BeaconIntegrationOutcome.BLOCKED,
            reason_code="LIFECYCLE_EFFECT_GATE_BLOCKED",
            reason="Exact Beacon lifecycle transition semantics remain outside this deterministic integration contract.",
            source_references=_unique_non_empty(
                entitlement_decision.decision_id,
                request.beacon_id,
                request.requested_lifecycle_effect,
            ),
            effective_entitlement_status=entitlement_decision.status,
        )

    if request.requested_capability is BeaconIntegrationCapability.ACTIVE_BEACON_COUNT:
        return _active_beacon_count_decision(request, entitlement_decision=entitlement_decision)

    if request.requested_capability is BeaconIntegrationCapability.SCAN_INTERVAL_WINDOW:
        return _scan_interval_decision(request, entitlement_decision=entitlement_decision)

    return _build_decision(
        request,
        outcome=BeaconIntegrationOutcome.UNSUPPORTED,
        reason_code="REQUESTED_CAPABILITY_UNSUPPORTED",
        reason="The requested Beacon capability is not part of the accepted deterministic semantic contract.",
        source_references=_unique_non_empty(entitlement_decision.decision_id, request.beacon_id),
        effective_entitlement_status=entitlement_decision.status,
    )


__all__ = [
    "BEACON_MANAGEMENT_MODULE_LABEL",
    "BEACON_MANAGEMENT_SOURCE_FACTS_OWNER_LABEL",
    "BeaconIntegrationCapability",
    "BeaconIntegrationDecision",
    "BeaconIntegrationIdempotencyRecord",
    "BeaconIntegrationOutcome",
    "BeaconIntegrationRequest",
    "BeaconIntegrationRequestKind",
    "BeaconIntegrationRequesterModule",
    "BeaconIntegrationSourceFactsOwner",
    "compute_beacon_integration_request_fingerprint",
    "evaluate_beacon_integration",
]
