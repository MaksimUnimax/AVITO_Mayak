"""Deterministic semantic contracts for payment reconciliation and manual refunds."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Final

from pydantic import BaseModel, ConfigDict, Field, model_validator

from mayak.platform.idempotency import IdempotencyFingerprint, IdempotencyKey

from .payment_provider_boundary import (
    PAYMENT_PROVIDER_REFUND_POLICY,
    PAYMENT_PROVIDER_RECURRING_BILLING_SUPPORTED,
    PAYMENT_PROVIDER_RENEWAL_POLICY,
    PAYMENT_PROVIDER_TRIAL_GRACE_PRORATION_SUPPORTED,
    SUPPORTED_PAYMENT_UNITS,
    PaymentProviderCandidate,
    PaymentProviderEvidenceKind,
)

APPROVED_PAYMENT_RECONCILIATION_PROVIDER_CANDIDATES: Final[tuple[PaymentProviderCandidate, ...]] = (
    PaymentProviderCandidate.YOOKASSA,
    PaymentProviderCandidate.TELEGRAM_STARS,
    PaymentProviderCandidate.TBANK,
)


class SemanticCommitState(str, Enum):
    """Semantic commit-point labels only; no durable state exists here."""

    UNKNOWN = "UNKNOWN"
    OWNER_APPROVED = "OWNER_APPROVED"
    BLOCKED = "BLOCKED"


class ProviderEventEffect(str, Enum):
    """Synthetic provider effect classifications used in semantic contracts."""

    CONFIRMED = "CONFIRMED"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"
    AMBIGUOUS = "AMBIGUOUS"


class ReconciliationAction(str, Enum):
    """Semantic request actions for reconciliation contracts."""

    RECORD_EVIDENCE_ONLY = "RECORD_EVIDENCE_ONLY"
    CONFIRM_EXTERNAL_EFFECT = "CONFIRM_EXTERNAL_EFFECT"
    REQUEST_MANUAL_REVIEW = "REQUEST_MANUAL_REVIEW"
    BLIND_RETRY = "BLIND_RETRY"
    RUNTIME_RECONCILIATION = "RUNTIME_RECONCILIATION"
    WEBHOOK_PROCESSING = "WEBHOOK_PROCESSING"
    PROVIDER_REFUND_API = "PROVIDER_REFUND_API"
    AUTOMATIC_REFUND = "AUTOMATIC_REFUND"
    RECURRING_BILLING = "RECURRING_BILLING"
    INVOICE_RECEIPT_TAX_RUNTIME = "INVOICE_RECEIPT_TAX_RUNTIME"
    ENTITLEMENT_GRANT = "ENTITLEMENT_GRANT"
    UNKNOWN_COMMIT_STATE = "UNKNOWN_COMMIT_STATE"


class RefundAction(str, Enum):
    """Semantic request actions for manual refund contracts."""

    REQUEST_MANUAL_REVIEW = "REQUEST_MANUAL_REVIEW"
    RECORD_MANUAL_REFUND_EVIDENCE = "RECORD_MANUAL_REFUND_EVIDENCE"
    AUTOMATIC_REFUND_ATTEMPT = "AUTOMATIC_REFUND_ATTEMPT"
    PROVIDER_REFUND_API_ATTEMPT = "PROVIDER_REFUND_API_ATTEMPT"
    RECURRING_BILLING_ATTEMPT = "RECURRING_BILLING_ATTEMPT"
    TRIAL_GRACE_PRORATION_ATTEMPT = "TRIAL_GRACE_PRORATION_ATTEMPT"
    UNKNOWN_COMMIT_STATE = "UNKNOWN_COMMIT_STATE"


class PaymentReconciliationOutcome(str, Enum):
    """Approved deterministic outcomes for reconciliation contracts."""

    RECORDED = "RECORDED"
    DUPLICATE = "DUPLICATE"
    REJECTED = "REJECTED"
    AMBIGUOUS = "AMBIGUOUS"
    RECONCILE_REQUIRED = "RECONCILE_REQUIRED"
    CONFIRMED = "CONFIRMED"
    UNRESOLVED = "UNRESOLVED"
    MANUAL_REVIEW_REQUIRED = "MANUAL_REVIEW_REQUIRED"
    REPLAYED = "REPLAYED"
    IDEMPOTENCY_MISMATCH = "IDEMPOTENCY_MISMATCH"
    BLOCKED = "BLOCKED"


class ManualRefundOutcome(str, Enum):
    """Approved deterministic outcomes for manual refund contracts."""

    MANUAL_REFUND_REVIEW_REQUIRED = "MANUAL_REFUND_REVIEW_REQUIRED"
    MANUAL_REFUND_REFERENCED = "MANUAL_REFUND_REFERENCED"
    AUTOMATIC_REFUND_BLOCKED = "AUTOMATIC_REFUND_BLOCKED"
    PROVIDER_REFUND_API_BLOCKED = "PROVIDER_REFUND_API_BLOCKED"
    REFUND_REJECTED = "REFUND_REJECTED"
    REFUND_REPLAYED = "REFUND_REPLAYED"
    REFUND_IDEMPOTENCY_MISMATCH = "REFUND_IDEMPOTENCY_MISMATCH"


class PaymentReconciliationIdempotencyRecord(BaseModel):
    """Explicit prior idempotency evidence for deterministic replay semantics."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    requested_action: ReconciliationAction
    idempotency_key: IdempotencyKey
    request_fingerprint: IdempotencyFingerprint
    terminal_outcome: PaymentReconciliationOutcome
    provider_event_identity: str | None = Field(default=None, min_length=1)


class ManualRefundIdempotencyRecord(BaseModel):
    """Explicit prior idempotency evidence for deterministic refund replay semantics."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    requested_action: RefundAction
    idempotency_key: IdempotencyKey
    request_fingerprint: IdempotencyFingerprint
    terminal_outcome: ManualRefundOutcome
    provider_event_identity: str | None = Field(default=None, min_length=1)


class PaymentReconciliationRequest(BaseModel):
    """Explicit synthetic-contract input for reconciliation semantics."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    account_id: str = Field(min_length=1)
    provider_candidate: PaymentProviderCandidate | str
    synthetic_provider_event_reference: str = Field(min_length=1)
    provider_event_identity: str | None = Field(default=None, min_length=1)
    evidence_kind: PaymentProviderEvidenceKind
    requested_action: ReconciliationAction = ReconciliationAction.RECORD_EVIDENCE_ONLY
    provider_effect: ProviderEventEffect = ProviderEventEffect.UNKNOWN
    normalized_amount: Decimal | None = Field(default=None, ge=0)
    payment_unit: str | None = Field(default=None, min_length=1)
    raw_payload_present: bool = False
    raw_payload_redacted: bool = True
    commit_state: SemanticCommitState = SemanticCommitState.OWNER_APPROVED
    idempotency_key: IdempotencyKey | None = None
    request_fingerprint: IdempotencyFingerprint | None = None
    audit_reference: str = Field(min_length=1)
    decision_at: datetime
    prior_idempotency_record: PaymentReconciliationIdempotencyRecord | None = None

    @model_validator(mode="after")
    def _validate_amount_and_unit(self) -> "PaymentReconciliationRequest":
        if (self.normalized_amount is None) != (self.payment_unit is None):
            raise ValueError("normalized amount and payment unit must be provided together")
        return self


class ManualRefundRequest(BaseModel):
    """Explicit synthetic-contract input for manual refund semantics."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    account_id: str = Field(min_length=1)
    provider_candidate: PaymentProviderCandidate | str
    synthetic_provider_event_reference: str = Field(min_length=1)
    provider_event_identity: str | None = Field(default=None, min_length=1)
    evidence_kind: PaymentProviderEvidenceKind
    requested_action: RefundAction = RefundAction.REQUEST_MANUAL_REVIEW
    normalized_amount: Decimal | None = Field(default=None, ge=0)
    payment_unit: str | None = Field(default=None, min_length=1)
    raw_payload_present: bool = False
    raw_payload_redacted: bool = True
    commit_state: SemanticCommitState = SemanticCommitState.OWNER_APPROVED
    idempotency_key: IdempotencyKey | None = None
    request_fingerprint: IdempotencyFingerprint | None = None
    audit_reference: str = Field(min_length=1)
    decision_at: datetime
    prior_idempotency_record: ManualRefundIdempotencyRecord | None = None

    @model_validator(mode="after")
    def _validate_amount_and_unit(self) -> "ManualRefundRequest":
        if (self.normalized_amount is None) != (self.payment_unit is None):
            raise ValueError("normalized amount and payment unit must be provided together")
        return self


class PaymentReconciliationDecision(BaseModel):
    """Pure semantic decision for reconciliation contracts."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    account_id: str = Field(min_length=1)
    provider_candidate: str = Field(min_length=1)
    synthetic_provider_event_reference: str = Field(min_length=1)
    provider_event_identity: str | None = Field(default=None, min_length=1)
    evidence_kind: PaymentProviderEvidenceKind
    requested_action: ReconciliationAction
    provider_effect: ProviderEventEffect
    outcome: PaymentReconciliationOutcome
    terminal_outcome: PaymentReconciliationOutcome
    reason_code: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    decision_at: datetime
    idempotency_key: IdempotencyKey | None = None
    request_fingerprint: IdempotencyFingerprint
    audit_reference: str = Field(min_length=1)
    normalized_amount: Decimal | None = Field(default=None, ge=0)
    payment_unit: str | None = Field(default=None, min_length=1)
    raw_payload_present: bool = False
    raw_payload_redacted: bool = True
    commit_state: SemanticCommitState = SemanticCommitState.OWNER_APPROVED
    source_references: tuple[str, ...] = Field(default_factory=tuple)
    history_preserved: bool = True

    @model_validator(mode="after")
    def _validate_terminal_outcome(self) -> "PaymentReconciliationDecision":
        if self.outcome not in {PaymentReconciliationOutcome.REPLAYED, PaymentReconciliationOutcome.DUPLICATE} and self.outcome != self.terminal_outcome:
            raise ValueError("terminal outcome must match the current outcome except for replayed decisions")
        return self


class ManualRefundDecision(BaseModel):
    """Pure semantic decision for manual refund contracts."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    account_id: str = Field(min_length=1)
    provider_candidate: str = Field(min_length=1)
    synthetic_provider_event_reference: str = Field(min_length=1)
    provider_event_identity: str | None = Field(default=None, min_length=1)
    evidence_kind: PaymentProviderEvidenceKind
    requested_action: RefundAction
    outcome: ManualRefundOutcome
    terminal_outcome: ManualRefundOutcome
    reason_code: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    decision_at: datetime
    idempotency_key: IdempotencyKey | None = None
    request_fingerprint: IdempotencyFingerprint
    audit_reference: str = Field(min_length=1)
    normalized_amount: Decimal | None = Field(default=None, ge=0)
    payment_unit: str | None = Field(default=None, min_length=1)
    raw_payload_present: bool = False
    raw_payload_redacted: bool = True
    commit_state: SemanticCommitState = SemanticCommitState.OWNER_APPROVED
    source_references: tuple[str, ...] = Field(default_factory=tuple)
    history_preserved: bool = True

    @model_validator(mode="after")
    def _validate_terminal_outcome(self) -> "ManualRefundDecision":
        if self.outcome is not ManualRefundOutcome.REFUND_REPLAYED and self.outcome != self.terminal_outcome:
            raise ValueError("terminal outcome must match the current outcome except for replayed decisions")
        return self


ReconciliationIdempotencyRecord = PaymentReconciliationIdempotencyRecord
PaymentReconciliationAction = ReconciliationAction
PaymentReconciliationIdempotencyRecord = ReconciliationIdempotencyRecord
ReconciliationOutcome = PaymentReconciliationOutcome
ManualRefundAction = RefundAction


def _provider_candidate_or_none(provider_candidate: PaymentProviderCandidate | str) -> PaymentProviderCandidate | None:
    if isinstance(provider_candidate, PaymentProviderCandidate):
        return provider_candidate
    try:
        return PaymentProviderCandidate(provider_candidate)
    except ValueError:
        return None


def _provider_candidate_value(provider_candidate: PaymentProviderCandidate | str) -> str:
    if isinstance(provider_candidate, PaymentProviderCandidate):
        return provider_candidate.value
    return provider_candidate


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


def _reconciliation_request_fingerprint(request: PaymentReconciliationRequest) -> IdempotencyFingerprint:
    return IdempotencyFingerprint(
        value=(
            "payment-reconciliation:"
            f"{request.model_dump_json(exclude={'idempotency_key', 'request_fingerprint', 'prior_idempotency_record', 'decision_at'})}"
        )
    )


def _manual_refund_request_fingerprint(request: ManualRefundRequest) -> IdempotencyFingerprint:
    return IdempotencyFingerprint(
        value=(
            "manual-refund:"
            f"{request.model_dump_json(exclude={'idempotency_key', 'request_fingerprint', 'prior_idempotency_record', 'decision_at'})}"
        )
    )


def compute_payment_reconciliation_request_fingerprint(
    request: PaymentReconciliationRequest,
) -> IdempotencyFingerprint:
    """Public deterministic helper for reconciliation idempotency contracts/tests."""

    return _reconciliation_request_fingerprint(request)


def compute_manual_refund_request_fingerprint(
    request: ManualRefundRequest,
) -> IdempotencyFingerprint:
    """Public deterministic helper for refund idempotency contracts/tests."""

    return _manual_refund_request_fingerprint(request)


def _build_reconciliation_decision(
    request: PaymentReconciliationRequest,
    *,
    outcome: PaymentReconciliationOutcome,
    reason_code: str,
    reason: str,
    terminal_outcome: PaymentReconciliationOutcome | None = None,
    source_references: tuple[str, ...] = (),
) -> PaymentReconciliationDecision:
    return PaymentReconciliationDecision(
        account_id=request.account_id,
        provider_candidate=_provider_candidate_value(request.provider_candidate),
        synthetic_provider_event_reference=request.synthetic_provider_event_reference,
        provider_event_identity=request.provider_event_identity,
        evidence_kind=request.evidence_kind,
        requested_action=request.requested_action,
        provider_effect=request.provider_effect,
        outcome=outcome,
        terminal_outcome=terminal_outcome or outcome,
        reason_code=reason_code,
        reason=reason,
        decision_at=request.decision_at,
        idempotency_key=request.idempotency_key,
        request_fingerprint=_reconciliation_request_fingerprint(request),
        audit_reference=request.audit_reference,
        normalized_amount=request.normalized_amount,
        payment_unit=request.payment_unit,
        raw_payload_present=request.raw_payload_present,
        raw_payload_redacted=request.raw_payload_redacted,
        commit_state=request.commit_state,
        source_references=_unique_non_empty(*source_references),
        history_preserved=True,
    )


def _build_manual_refund_decision(
    request: ManualRefundRequest,
    *,
    outcome: ManualRefundOutcome,
    reason_code: str,
    reason: str,
    terminal_outcome: ManualRefundOutcome | None = None,
    source_references: tuple[str, ...] = (),
) -> ManualRefundDecision:
    return ManualRefundDecision(
        account_id=request.account_id,
        provider_candidate=_provider_candidate_value(request.provider_candidate),
        synthetic_provider_event_reference=request.synthetic_provider_event_reference,
        provider_event_identity=request.provider_event_identity,
        evidence_kind=request.evidence_kind,
        requested_action=request.requested_action,
        outcome=outcome,
        terminal_outcome=terminal_outcome or outcome,
        reason_code=reason_code,
        reason=reason,
        decision_at=request.decision_at,
        idempotency_key=request.idempotency_key,
        request_fingerprint=_manual_refund_request_fingerprint(request),
        audit_reference=request.audit_reference,
        normalized_amount=request.normalized_amount,
        payment_unit=request.payment_unit,
        raw_payload_present=request.raw_payload_present,
        raw_payload_redacted=request.raw_payload_redacted,
        commit_state=request.commit_state,
        source_references=_unique_non_empty(*source_references),
        history_preserved=True,
    )


def _validate_payment_unit(payment_unit: str | None) -> bool:
    if payment_unit is None:
        return True
    return payment_unit in SUPPORTED_PAYMENT_UNITS


def _reconciliation_unknown_effect_outcome(
    request: PaymentReconciliationRequest,
) -> tuple[PaymentReconciliationOutcome, str, str]:
    if request.requested_action is ReconciliationAction.REQUEST_MANUAL_REVIEW:
        return (
            PaymentReconciliationOutcome.MANUAL_REVIEW_REQUIRED,
            "MANUAL_REVIEW_REQUIRED",
            "The provider effect cannot be safely resolved without manual review.",
        )
    if request.requested_action is ReconciliationAction.BLIND_RETRY:
        return (
            PaymentReconciliationOutcome.BLOCKED,
            "BLIND_RETRY_FORBIDDEN",
            "Blind retry after an unknown provider effect is forbidden.",
        )
    if request.provider_effect is ProviderEventEffect.AMBIGUOUS:
        return (
            PaymentReconciliationOutcome.RECONCILE_REQUIRED,
            "AMBIGUOUS_PROVIDER_EFFECT_RECONCILE_REQUIRED",
            "Ambiguous provider effect requires reconcile-first semantics.",
        )
    if request.provider_effect is ProviderEventEffect.UNKNOWN:
        return (
            PaymentReconciliationOutcome.UNRESOLVED,
            "UNKNOWN_PROVIDER_EFFECT_UNRESOLVED",
            "Unknown provider effect must not be treated as no effect.",
        )
    return (
        PaymentReconciliationOutcome.AMBIGUOUS,
        "AMBIGUOUS_PROVIDER_EFFECT",
        "The provider effect cannot be safely classified.",
    )


def evaluate_payment_reconciliation(
    request: PaymentReconciliationRequest,
) -> PaymentReconciliationDecision:
    """Evaluate deterministic reconciliation semantics without runtime side effects."""

    if request.idempotency_key is None:
        return _build_reconciliation_decision(
            request,
            outcome=PaymentReconciliationOutcome.REJECTED,
            reason_code="IDEMPOTENCY_KEY_REQUIRED",
            reason="Reconciliation requests require an idempotency key before any semantic effect.",
        )

    computed_fingerprint = _reconciliation_request_fingerprint(request)
    if request.request_fingerprint is not None and request.request_fingerprint != computed_fingerprint:
        return _build_reconciliation_decision(
            request,
            outcome=PaymentReconciliationOutcome.REJECTED,
            reason_code="REQUEST_FINGERPRINT_MISMATCH",
            reason="The explicit request fingerprint does not match the deterministic reconciliation fingerprint.",
        )

    prior = request.prior_idempotency_record
    if prior is not None:
        if prior.idempotency_key == request.idempotency_key:
            if prior.request_fingerprint != computed_fingerprint:
                return _build_reconciliation_decision(
                    request,
                    outcome=PaymentReconciliationOutcome.IDEMPOTENCY_MISMATCH,
                    reason_code="IDEMPOTENCY_MISMATCH",
                    reason="The same idempotency key was reused for a different reconciliation fingerprint.",
                )
            return _build_reconciliation_decision(
                request,
                outcome=PaymentReconciliationOutcome.REPLAYED,
                terminal_outcome=prior.terminal_outcome,
                reason_code="IDEMPOTENT_REPLAY",
                reason="The same idempotency key and fingerprint replay the original terminal outcome.",
                source_references=_unique_non_empty(
                    prior.idempotency_key.value,
                    prior.request_fingerprint.value,
                    prior.provider_event_identity,
                ),
            )
        if request.provider_event_identity is not None and prior.provider_event_identity == request.provider_event_identity:
            return _build_reconciliation_decision(
                request,
                outcome=PaymentReconciliationOutcome.DUPLICATE,
                terminal_outcome=prior.terminal_outcome,
                reason_code="DUPLICATE_PROVIDER_EVENT_IDENTITY",
                reason="A duplicate provider event identity must not create a second semantic effect.",
                source_references=_unique_non_empty(
                    prior.provider_event_identity,
                    prior.idempotency_key.value,
                    prior.request_fingerprint.value,
                ),
            )
        return _build_reconciliation_decision(
            request,
            outcome=PaymentReconciliationOutcome.IDEMPOTENCY_MISMATCH,
            reason_code="PRIOR_IDEMPOTENCY_EVIDENCE_MISMATCH",
            reason="The supplied prior idempotency evidence does not match the current reconciliation request.",
        )

    provider_candidate = _provider_candidate_or_none(request.provider_candidate)
    if provider_candidate is None:
        return _build_reconciliation_decision(
            request,
            outcome=PaymentReconciliationOutcome.REJECTED,
            reason_code="UNSUPPORTED_PROVIDER",
            reason="The provider candidate is not part of the approved semantic provider set.",
        )

    if not _validate_payment_unit(request.payment_unit):
        return _build_reconciliation_decision(
            request,
            outcome=PaymentReconciliationOutcome.REJECTED,
            reason_code="UNSUPPORTED_PAYMENT_UNIT",
            reason="The payment unit is not part of the approved payment unit set.",
        )

    if request.raw_payload_present and not request.raw_payload_redacted:
        return _build_reconciliation_decision(
            request,
            outcome=PaymentReconciliationOutcome.REJECTED,
            reason_code="RAW_PAYLOAD_MUST_BE_REDACTED",
            reason="Raw provider payload contents must not be captured as-is.",
        )

    if request.commit_state is SemanticCommitState.UNKNOWN:
        return _build_reconciliation_decision(
            request,
            outcome=PaymentReconciliationOutcome.UNRESOLVED,
            reason_code="UNKNOWN_COMMIT_STATE",
            reason="Commit-point terminology is semantic-only and unknown commit state cannot imply success.",
        )

    blocked_actions = {
        ReconciliationAction.RUNTIME_RECONCILIATION,
        ReconciliationAction.WEBHOOK_PROCESSING,
        ReconciliationAction.PROVIDER_REFUND_API,
        ReconciliationAction.AUTOMATIC_REFUND,
        ReconciliationAction.RECURRING_BILLING,
        ReconciliationAction.INVOICE_RECEIPT_TAX_RUNTIME,
        ReconciliationAction.ENTITLEMENT_GRANT,
    }
    if request.requested_action in blocked_actions:
        return _build_reconciliation_decision(
            request,
            outcome=PaymentReconciliationOutcome.BLOCKED,
            reason_code="RUNTIME_ACTION_BLOCKED",
            reason="The requested runtime action remains blocked in the semantic contract.",
            source_references=_unique_non_empty(
                request.synthetic_provider_event_reference,
                request.provider_event_identity,
                provider_candidate.value,
                request.evidence_kind.value,
            ),
        )

    if request.requested_action is ReconciliationAction.REQUEST_MANUAL_REVIEW:
        return _build_reconciliation_decision(
            request,
            outcome=PaymentReconciliationOutcome.MANUAL_REVIEW_REQUIRED,
            reason_code="MANUAL_REVIEW_REQUIRED",
            reason="The evidence requires manual operator or business review.",
            source_references=_unique_non_empty(
                request.synthetic_provider_event_reference,
                request.provider_event_identity,
                provider_candidate.value,
                request.evidence_kind.value,
            ),
        )

    if request.provider_effect is ProviderEventEffect.CONFIRMED:
        if request.requested_action is ReconciliationAction.CONFIRM_EXTERNAL_EFFECT:
            return _build_reconciliation_decision(
                request,
                outcome=PaymentReconciliationOutcome.CONFIRMED,
                reason_code="RECONCILIATION_CONFIRMED_EVIDENCE_ONLY",
                reason="Confirmed reconciliation evidence is accepted as evidence only and does not grant access.",
                source_references=_unique_non_empty(
                    request.synthetic_provider_event_reference,
                    request.provider_event_identity,
                    provider_candidate.value,
                    request.evidence_kind.value,
                    request.idempotency_key.value,
                    request.audit_reference,
                ),
            )
        return _build_reconciliation_decision(
            request,
            outcome=PaymentReconciliationOutcome.RECORDED,
            reason_code="RECONCILIATION_RECORDED_EVIDENCE_ONLY",
            reason="Normalized provider evidence is accepted only as evidence and not as authority.",
            source_references=_unique_non_empty(
                request.synthetic_provider_event_reference,
                request.provider_event_identity,
                provider_candidate.value,
                request.evidence_kind.value,
                request.idempotency_key.value,
                request.audit_reference,
            ),
        )

    if request.provider_effect in {ProviderEventEffect.UNKNOWN, ProviderEventEffect.AMBIGUOUS}:
        outcome, reason_code, reason = _reconciliation_unknown_effect_outcome(request)
        return _build_reconciliation_decision(
            request,
            outcome=outcome,
            reason_code=reason_code,
            reason=reason,
            source_references=_unique_non_empty(
                request.synthetic_provider_event_reference,
                request.provider_event_identity,
                provider_candidate.value,
                request.evidence_kind.value,
                request.idempotency_key.value,
                request.audit_reference,
            ),
        )

    return _build_reconciliation_decision(
        request,
        outcome=PaymentReconciliationOutcome.RECORDED,
        reason_code="RECONCILIATION_RECORDED_EVIDENCE_ONLY",
        reason="The provider evidence is recorded only as evidence and not as authority.",
        source_references=_unique_non_empty(
            request.synthetic_provider_event_reference,
            request.provider_event_identity,
            provider_candidate.value,
            request.evidence_kind.value,
            request.idempotency_key.value,
            request.audit_reference,
        ),
    )


def _refund_unknown_commit_state_outcome(
    request: ManualRefundRequest,
) -> tuple[ManualRefundOutcome, str, str]:
    if request.requested_action is RefundAction.REQUEST_MANUAL_REVIEW:
        return (
            ManualRefundOutcome.MANUAL_REFUND_REVIEW_REQUIRED,
            "MANUAL_REFUND_REVIEW_REQUIRED",
            "Unknown commit state requires manual refund review.",
        )
    return (
        ManualRefundOutcome.REFUND_REJECTED,
        "UNKNOWN_COMMIT_STATE",
        "Unknown commit state cannot produce a silent refund decision.",
    )


def evaluate_manual_refund(
    request: ManualRefundRequest,
) -> ManualRefundDecision:
    """Evaluate deterministic manual-refund semantics without runtime side effects."""

    if request.idempotency_key is None:
        return _build_manual_refund_decision(
            request,
            outcome=ManualRefundOutcome.REFUND_REJECTED,
            reason_code="IDEMPOTENCY_KEY_REQUIRED",
            reason="Manual refund requests require an idempotency key before any semantic effect.",
        )

    computed_fingerprint = _manual_refund_request_fingerprint(request)
    if request.request_fingerprint is not None and request.request_fingerprint != computed_fingerprint:
        return _build_manual_refund_decision(
            request,
            outcome=ManualRefundOutcome.REFUND_REJECTED,
            reason_code="REQUEST_FINGERPRINT_MISMATCH",
            reason="The explicit request fingerprint does not match the deterministic refund fingerprint.",
        )

    prior = request.prior_idempotency_record
    if prior is not None:
        if prior.idempotency_key == request.idempotency_key:
            if prior.request_fingerprint != computed_fingerprint:
                return _build_manual_refund_decision(
                    request,
                    outcome=ManualRefundOutcome.REFUND_IDEMPOTENCY_MISMATCH,
                    reason_code="REFUND_IDEMPOTENCY_MISMATCH",
                    reason="The same idempotency key was reused for a different refund fingerprint.",
                )
            return _build_manual_refund_decision(
                request,
                outcome=ManualRefundOutcome.REFUND_REPLAYED,
                terminal_outcome=prior.terminal_outcome,
                reason_code="REFUND_IDEMPOTENT_REPLAY",
                reason="The same idempotency key and fingerprint replay the original refund terminal outcome.",
                source_references=_unique_non_empty(
                    prior.idempotency_key.value,
                    prior.request_fingerprint.value,
                    prior.provider_event_identity,
                ),
            )
        return _build_manual_refund_decision(
            request,
            outcome=ManualRefundOutcome.REFUND_IDEMPOTENCY_MISMATCH,
            reason_code="PRIOR_REFUND_IDEMPOTENCY_EVIDENCE_MISMATCH",
            reason="The supplied prior refund idempotency evidence does not match the current request.",
        )

    provider_candidate = _provider_candidate_or_none(request.provider_candidate)
    if provider_candidate is None:
        return _build_manual_refund_decision(
            request,
            outcome=ManualRefundOutcome.REFUND_REJECTED,
            reason_code="UNSUPPORTED_PROVIDER",
            reason="The provider candidate is not part of the approved semantic provider set.",
        )

    if not _validate_payment_unit(request.payment_unit):
        return _build_manual_refund_decision(
            request,
            outcome=ManualRefundOutcome.REFUND_REJECTED,
            reason_code="UNSUPPORTED_PAYMENT_UNIT",
            reason="The payment unit is not part of the approved payment unit set.",
        )

    if request.raw_payload_present and not request.raw_payload_redacted:
        return _build_manual_refund_decision(
            request,
            outcome=ManualRefundOutcome.REFUND_REJECTED,
            reason_code="RAW_PAYLOAD_MUST_BE_REDACTED",
            reason="Raw provider payload contents must not be captured as-is.",
        )

    if request.commit_state is SemanticCommitState.UNKNOWN:
        outcome, reason_code, reason = _refund_unknown_commit_state_outcome(request)
        return _build_manual_refund_decision(
            request,
            outcome=outcome,
            reason_code=reason_code,
            reason=reason,
            source_references=_unique_non_empty(
                request.synthetic_provider_event_reference,
                request.provider_event_identity,
                provider_candidate.value,
                request.evidence_kind.value,
            ),
        )

    if request.requested_action is RefundAction.REQUEST_MANUAL_REVIEW:
        return _build_manual_refund_decision(
            request,
            outcome=ManualRefundOutcome.MANUAL_REFUND_REVIEW_REQUIRED,
            reason_code="MANUAL_REFUND_REVIEW_REQUIRED",
            reason="The manual refund case requires human or business review.",
            source_references=_unique_non_empty(
                request.synthetic_provider_event_reference,
                request.provider_event_identity,
                provider_candidate.value,
                request.evidence_kind.value,
            ),
        )

    if request.requested_action is RefundAction.RECORD_MANUAL_REFUND_EVIDENCE:
        return _build_manual_refund_decision(
            request,
            outcome=ManualRefundOutcome.MANUAL_REFUND_REFERENCED,
            reason_code="MANUAL_REFUND_REFERENCED",
            reason="Already manually handled refund evidence is accepted as evidence only.",
            source_references=_unique_non_empty(
                request.synthetic_provider_event_reference,
                request.provider_event_identity,
                provider_candidate.value,
                request.evidence_kind.value,
                request.idempotency_key.value,
                request.audit_reference,
            ),
        )

    if request.requested_action is RefundAction.AUTOMATIC_REFUND_ATTEMPT:
        return _build_manual_refund_decision(
            request,
            outcome=ManualRefundOutcome.AUTOMATIC_REFUND_BLOCKED,
            reason_code="AUTOMATIC_REFUND_BLOCKED",
            reason="Automatic refunds remain forbidden in the current semantic contract.",
        )

    if request.requested_action is RefundAction.PROVIDER_REFUND_API_ATTEMPT:
        return _build_manual_refund_decision(
            request,
            outcome=ManualRefundOutcome.PROVIDER_REFUND_API_BLOCKED,
            reason_code="PROVIDER_REFUND_API_BLOCKED",
            reason="Direct provider refund API calls remain forbidden in the current semantic contract.",
        )

    if request.requested_action in {
        RefundAction.RECURRING_BILLING_ATTEMPT,
        RefundAction.TRIAL_GRACE_PRORATION_ATTEMPT,
    }:
        return _build_manual_refund_decision(
            request,
            outcome=ManualRefundOutcome.REFUND_REJECTED,
            reason_code=f"{request.requested_action.value}_BLOCKED",
            reason="The requested refund-related behavior remains blocked or unsupported.",
        )

    return _build_manual_refund_decision(
        request,
        outcome=ManualRefundOutcome.MANUAL_REFUND_REVIEW_REQUIRED,
        reason_code="MANUAL_REFUND_REVIEW_REQUIRED",
        reason="The manual refund case requires review before any semantic effect.",
        source_references=_unique_non_empty(
            request.synthetic_provider_event_reference,
            request.provider_event_identity,
            provider_candidate.value,
            request.evidence_kind.value,
            request.idempotency_key.value,
            request.audit_reference,
        ),
    )


__all__ = [
    "APPROVED_PAYMENT_RECONCILIATION_PROVIDER_CANDIDATES",
    "ManualRefundAction",
    "ManualRefundDecision",
    "ManualRefundIdempotencyRecord",
    "ManualRefundOutcome",
    "ManualRefundRequest",
    "PAYMENT_PROVIDER_REFUND_POLICY",
    "PAYMENT_PROVIDER_RECURRING_BILLING_SUPPORTED",
    "PAYMENT_PROVIDER_RENEWAL_POLICY",
    "PAYMENT_PROVIDER_TRIAL_GRACE_PRORATION_SUPPORTED",
    "PaymentProviderCandidate",
    "PaymentProviderEvidenceKind",
    "PaymentReconciliationAction",
    "PaymentReconciliationDecision",
    "PaymentReconciliationIdempotencyRecord",
    "PaymentReconciliationOutcome",
    "PaymentReconciliationRequest",
    "ProviderEventEffect",
    "ReconciliationAction",
    "ReconciliationIdempotencyRecord",
    "ReconciliationOutcome",
    "RefundAction",
    "SemanticCommitState",
    "SUPPORTED_PAYMENT_UNITS",
    "compute_manual_refund_request_fingerprint",
    "compute_payment_reconciliation_request_fingerprint",
    "evaluate_manual_refund",
    "evaluate_payment_reconciliation",
]
