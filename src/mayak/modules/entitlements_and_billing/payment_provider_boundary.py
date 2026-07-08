"""Deterministic semantic contracts for payment provider boundary evidence."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Final

from pydantic import BaseModel, ConfigDict, Field, model_validator

from mayak.platform.idempotency import IdempotencyFingerprint, IdempotencyKey

PAYMENT_PROVIDER_RENEWAL_POLICY: Final[str] = "MANUAL_RENEWAL_ONLY"
PAYMENT_PROVIDER_REFUND_POLICY: Final[str] = "MANUAL_REFUNDS_ONLY"
PAYMENT_PROVIDER_RECURRING_BILLING_SUPPORTED: Final[bool] = False
PAYMENT_PROVIDER_TRIAL_GRACE_PRORATION_SUPPORTED: Final[bool] = False
SUPPORTED_PAYMENT_UNITS: Final[tuple[str, ...]] = ("RUB", "TELEGRAM_STARS")


class PaymentProviderCandidate(str, Enum):
    """Approved provider candidates for semantic provider-boundary contracts."""

    YOOKASSA = "YOOKASSA"
    TELEGRAM_STARS = "TELEGRAM_STARS"
    TBANK = "TBANK"


class PaymentProviderEvidenceKind(str, Enum):
    """Semantic evidence families captured at the provider boundary."""

    PAYMENT_EVIDENCE = "PAYMENT_EVIDENCE"
    REFUND_EVIDENCE = "REFUND_EVIDENCE"
    WEBHOOK_NOTIFICATION_EVIDENCE = "WEBHOOK_NOTIFICATION_EVIDENCE"
    RECEIPT_INVOICE_TAX_EVIDENCE = "RECEIPT_INVOICE_TAX_EVIDENCE"


class PaymentProviderBoundaryAction(str, Enum):
    """Semantic request actions for the provider boundary."""

    CAPTURE_EVIDENCE_ONLY = "CAPTURE_EVIDENCE_ONLY"
    REQUEST_AUTHORITY_FROM_EVIDENCE = "REQUEST_AUTHORITY_FROM_EVIDENCE"
    GRANT_ENTITLEMENT = "GRANT_ENTITLEMENT"
    EXTEND_ENTITLEMENT = "EXTEND_ENTITLEMENT"
    CHANGE_ENTITLEMENT = "CHANGE_ENTITLEMENT"
    SDK_API_CALL = "SDK_API_CALL"
    WEBHOOK_PROCESSING = "WEBHOOK_PROCESSING"
    RECEIPT_INVOICE_TAX_RUNTIME = "RECEIPT_INVOICE_TAX_RUNTIME"
    REFUND_AUTOMATION = "REFUND_AUTOMATION"
    RECURRING_BILLING = "RECURRING_BILLING"
    PAYMENT_ACCOUNT_SETUP = "PAYMENT_ACCOUNT_SETUP"
    CARD_DATA_HANDLING = "CARD_DATA_HANDLING"
    MANUAL_REVIEW = "MANUAL_REVIEW"


class PaymentProviderBoundaryOutcome(str, Enum):
    """Approved deterministic outcomes for provider-boundary semantics."""

    ACCEPTED_AS_EVIDENCE = "ACCEPTED_AS_EVIDENCE"
    REJECTED = "REJECTED"
    UNSUPPORTED_PROVIDER = "UNSUPPORTED_PROVIDER"
    UNSUPPORTED_RUNTIME_ACTION = "UNSUPPORTED_RUNTIME_ACTION"
    PAYMENT_IS_NOT_AUTHORITY = "PAYMENT_IS_NOT_AUTHORITY"
    RAW_PAYLOAD_NOT_AUTHORITY = "RAW_PAYLOAD_NOT_AUTHORITY"
    MANUAL_REVIEW_REQUIRED = "MANUAL_REVIEW_REQUIRED"
    REPLAYED = "REPLAYED"
    IDEMPOTENCY_MISMATCH = "IDEMPOTENCY_MISMATCH"
    BLOCKED = "BLOCKED"


class PaymentProviderBoundaryActorContext(BaseModel):
    """Semantic actor/service context for provider-boundary contracts."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    actor_id: str = Field(min_length=1)
    actor_category: str = Field(min_length=1)
    authorization_scope: str = Field(min_length=1)
    authorization_reference: str = Field(min_length=1)
    audit_reference: str = Field(min_length=1)
    service_name: str | None = None


class PaymentProviderIdempotencyRecord(BaseModel):
    """Explicit prior idempotency evidence for deterministic replay semantics."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    requested_action: PaymentProviderBoundaryAction
    idempotency_key: IdempotencyKey
    request_fingerprint: IdempotencyFingerprint
    terminal_outcome: PaymentProviderBoundaryOutcome


class PaymentProviderBoundaryRequest(BaseModel):
    """Explicit synthetic-contract input for provider-boundary semantics."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    account_id: str = Field(min_length=1)
    provider_candidate: PaymentProviderCandidate | str
    evidence_kind: PaymentProviderEvidenceKind
    provider_reference_id: str = Field(min_length=1)
    synthetic_provider_event_id: str | None = None
    requested_action: PaymentProviderBoundaryAction = PaymentProviderBoundaryAction.CAPTURE_EVIDENCE_ONLY
    normalized_amount: Decimal | None = None
    payment_unit: str | None = None
    raw_payload_present: bool = False
    raw_payload_redacted: bool = True
    claims_authority_from_raw_payload: bool = False
    actor: PaymentProviderBoundaryActorContext | None = None
    audit_reference: str | None = None
    decision_at: datetime
    idempotency_key: IdempotencyKey | None = None
    prior_idempotency_record: PaymentProviderIdempotencyRecord | None = None

    @model_validator(mode="after")
    def _validate_normalized_amount_pair(self) -> "PaymentProviderBoundaryRequest":
        if (self.normalized_amount is None) != (self.payment_unit is None):
            raise ValueError("normalized amount and payment unit must be provided together")
        if self.raw_payload_present and not self.raw_payload_redacted:
            raise ValueError("raw payload contents must stay redacted")
        return self


class PaymentProviderBoundaryDecision(BaseModel):
    """Pure semantic decision for provider-boundary contracts."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    account_id: str = Field(min_length=1)
    provider_candidate: str = Field(min_length=1)
    evidence_kind: PaymentProviderEvidenceKind
    provider_reference_id: str = Field(min_length=1)
    synthetic_provider_event_id: str | None = None
    requested_action: PaymentProviderBoundaryAction
    outcome: PaymentProviderBoundaryOutcome
    terminal_outcome: PaymentProviderBoundaryOutcome
    reason_code: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    decision_at: datetime
    idempotency_key: IdempotencyKey | None = None
    request_fingerprint: IdempotencyFingerprint
    actor: PaymentProviderBoundaryActorContext | None = None
    audit_reference: str | None = None
    normalized_amount: Decimal | None = None
    payment_unit: str | None = None
    raw_payload_present: bool = False
    raw_payload_redacted: bool = True
    claims_authority_from_raw_payload: bool = False
    source_references: tuple[str, ...] = Field(default_factory=tuple)
    history_preserved: bool = True

    @model_validator(mode="after")
    def _validate_terminal_outcome(self) -> "PaymentProviderBoundaryDecision":
        if self.outcome is not PaymentProviderBoundaryOutcome.REPLAYED and self.outcome != self.terminal_outcome:
            raise ValueError("terminal outcome must match the current outcome except for replayed decisions")
        return self


def _provider_candidate_value(provider_candidate: PaymentProviderCandidate | str) -> str:
    if isinstance(provider_candidate, PaymentProviderCandidate):
        return provider_candidate.value
    return provider_candidate


def _provider_candidate_or_none(provider_candidate: PaymentProviderCandidate | str) -> PaymentProviderCandidate | None:
    if isinstance(provider_candidate, PaymentProviderCandidate):
        return provider_candidate
    try:
        return PaymentProviderCandidate(provider_candidate)
    except ValueError:
        return None


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


def _request_fingerprint(request: PaymentProviderBoundaryRequest) -> IdempotencyFingerprint:
    return IdempotencyFingerprint(
        value=(
            "payment-provider-boundary:"
            f"{request.model_dump_json(exclude={'idempotency_key', 'prior_idempotency_record', 'decision_at'})}"
        )
    )


def compute_payment_provider_boundary_request_fingerprint(
    request: PaymentProviderBoundaryRequest,
) -> IdempotencyFingerprint:
    """Public deterministic helper for provider-boundary idempotency contracts/tests."""

    return _request_fingerprint(request)


def _build_decision(
    request: PaymentProviderBoundaryRequest,
    *,
    outcome: PaymentProviderBoundaryOutcome,
    reason_code: str,
    reason: str,
    terminal_outcome: PaymentProviderBoundaryOutcome | None = None,
    source_references: tuple[str, ...] = (),
) -> PaymentProviderBoundaryDecision:
    audit_reference = request.audit_reference or (request.actor.audit_reference if request.actor else None)
    return PaymentProviderBoundaryDecision(
        account_id=request.account_id,
        provider_candidate=_provider_candidate_value(request.provider_candidate),
        evidence_kind=request.evidence_kind,
        provider_reference_id=request.provider_reference_id,
        synthetic_provider_event_id=request.synthetic_provider_event_id,
        requested_action=request.requested_action,
        outcome=outcome,
        terminal_outcome=terminal_outcome or outcome,
        reason_code=reason_code,
        reason=reason,
        decision_at=request.decision_at,
        idempotency_key=request.idempotency_key,
        request_fingerprint=_request_fingerprint(request),
        actor=request.actor,
        audit_reference=audit_reference,
        normalized_amount=request.normalized_amount,
        payment_unit=request.payment_unit,
        raw_payload_present=request.raw_payload_present,
        raw_payload_redacted=request.raw_payload_redacted,
        claims_authority_from_raw_payload=request.claims_authority_from_raw_payload,
        source_references=_unique_non_empty(*source_references),
        history_preserved=True,
    )


def evaluate_payment_provider_boundary(
    request: PaymentProviderBoundaryRequest,
) -> PaymentProviderBoundaryDecision:
    """Evaluate deterministic provider-boundary semantics without runtime side effects."""

    if request.idempotency_key is None:
        return _build_decision(
            request,
            outcome=PaymentProviderBoundaryOutcome.REJECTED,
            reason_code="IDEMPOTENCY_KEY_REQUIRED",
            reason="Provider-boundary requests require an idempotency key before any effect.",
        )

    if request.prior_idempotency_record is not None:
        prior = request.prior_idempotency_record
        request_fingerprint = _request_fingerprint(request)
        if prior.idempotency_key != request.idempotency_key:
            return _build_decision(
                request,
                outcome=PaymentProviderBoundaryOutcome.IDEMPOTENCY_MISMATCH,
                reason_code="IDEMPOTENCY_KEY_CONFLICT",
                reason="The prior idempotency evidence references a different key than the current request.",
                source_references=(prior.idempotency_key.value, request.idempotency_key.value),
            )
        if prior.request_fingerprint != request_fingerprint:
            return _build_decision(
                request,
                outcome=PaymentProviderBoundaryOutcome.IDEMPOTENCY_MISMATCH,
                reason_code="IDEMPOTENCY_MISMATCH",
                reason="The same idempotency key was reused for a different request fingerprint.",
                source_references=(prior.idempotency_key.value, prior.request_fingerprint.value),
            )
        return _build_decision(
            request,
            outcome=PaymentProviderBoundaryOutcome.REPLAYED,
            terminal_outcome=prior.terminal_outcome,
            reason_code="IDEMPOTENT_REPLAY",
            reason="The same idempotency key and request fingerprint replay the original terminal outcome.",
            source_references=(prior.idempotency_key.value, prior.request_fingerprint.value),
        )

    provider_candidate = _provider_candidate_or_none(request.provider_candidate)
    if provider_candidate is None:
        return _build_decision(
            request,
            outcome=PaymentProviderBoundaryOutcome.UNSUPPORTED_PROVIDER,
            reason_code="UNSUPPORTED_PROVIDER",
            reason="The provider candidate is not part of the approved semantic provider set.",
        )

    if request.raw_payload_present and not request.raw_payload_redacted:
        return _build_decision(
            request,
            outcome=PaymentProviderBoundaryOutcome.REJECTED,
            reason_code="RAW_PAYLOAD_MUST_BE_REDACTED",
            reason="Raw provider payload contents must not be captured as-is.",
        )

    if request.claims_authority_from_raw_payload:
        return _build_decision(
            request,
            outcome=PaymentProviderBoundaryOutcome.RAW_PAYLOAD_NOT_AUTHORITY,
            reason_code="RAW_PAYLOAD_NOT_AUTHORITY",
            reason="Raw provider payload is external evidence only and is not entitlement authority.",
        )

    if request.requested_action in {
        PaymentProviderBoundaryAction.SDK_API_CALL,
        PaymentProviderBoundaryAction.WEBHOOK_PROCESSING,
        PaymentProviderBoundaryAction.RECEIPT_INVOICE_TAX_RUNTIME,
    }:
        return _build_decision(
            request,
            outcome=PaymentProviderBoundaryOutcome.UNSUPPORTED_RUNTIME_ACTION,
            reason_code="UNSUPPORTED_RUNTIME_ACTION",
            reason="Runtime provider actions remain blocked in this semantic task.",
        )

    if request.requested_action in {
        PaymentProviderBoundaryAction.REFUND_AUTOMATION,
        PaymentProviderBoundaryAction.RECURRING_BILLING,
        PaymentProviderBoundaryAction.PAYMENT_ACCOUNT_SETUP,
        PaymentProviderBoundaryAction.CARD_DATA_HANDLING,
    }:
        return _build_decision(
            request,
            outcome=PaymentProviderBoundaryOutcome.BLOCKED,
            reason_code=f"{request.requested_action.value}_BLOCKED",
            reason="The requested provider action remains blocked by the current owner policy.",
        )

    if request.requested_action in {
        PaymentProviderBoundaryAction.REQUEST_AUTHORITY_FROM_EVIDENCE,
        PaymentProviderBoundaryAction.GRANT_ENTITLEMENT,
        PaymentProviderBoundaryAction.EXTEND_ENTITLEMENT,
        PaymentProviderBoundaryAction.CHANGE_ENTITLEMENT,
    }:
        outcome = (
            PaymentProviderBoundaryOutcome.PAYMENT_IS_NOT_AUTHORITY
            if request.requested_action is PaymentProviderBoundaryAction.REQUEST_AUTHORITY_FROM_EVIDENCE
            else PaymentProviderBoundaryOutcome.BLOCKED
        )
        return _build_decision(
            request,
            outcome=outcome,
            reason_code="PAYMENT_IS_NOT_AUTHORITY",
            reason="Payment evidence must not create, extend or change access by itself.",
        )

    if request.requested_action is PaymentProviderBoundaryAction.MANUAL_REVIEW:
        return _build_decision(
            request,
            outcome=PaymentProviderBoundaryOutcome.MANUAL_REVIEW_REQUIRED,
            reason_code="MANUAL_REVIEW_REQUIRED",
            reason="The evidence requires manual review at the provider boundary.",
        )

    return _build_decision(
        request,
        outcome=PaymentProviderBoundaryOutcome.ACCEPTED_AS_EVIDENCE,
        reason_code="PROVIDER_EVIDENCE_ACCEPTED_ONLY",
        reason="The provider candidate is accepted only as external evidence and not as authority.",
        source_references=_unique_non_empty(
            request.provider_reference_id,
            request.synthetic_provider_event_id,
            provider_candidate.value,
            request.evidence_kind.value,
            request.idempotency_key.value,
            request.actor.audit_reference if request.actor else None,
            request.audit_reference,
        ),
    )


__all__ = [
    "PAYMENT_PROVIDER_REFUND_POLICY",
    "PAYMENT_PROVIDER_RECURRING_BILLING_SUPPORTED",
    "PAYMENT_PROVIDER_RENEWAL_POLICY",
    "PAYMENT_PROVIDER_TRIAL_GRACE_PRORATION_SUPPORTED",
    "SUPPORTED_PAYMENT_UNITS",
    "PaymentProviderBoundaryAction",
    "PaymentProviderBoundaryActorContext",
    "PaymentProviderBoundaryDecision",
    "PaymentProviderBoundaryOutcome",
    "PaymentProviderBoundaryRequest",
    "PaymentProviderCandidate",
    "PaymentProviderEvidenceKind",
    "PaymentProviderIdempotencyRecord",
    "compute_payment_provider_boundary_request_fingerprint",
    "evaluate_payment_provider_boundary",
]
