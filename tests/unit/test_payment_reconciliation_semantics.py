from __future__ import annotations

import ast
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError

from mayak.modules.entitlements_and_billing.payment_provider_boundary import (
    PAYMENT_PROVIDER_REFUND_POLICY,
    PAYMENT_PROVIDER_RECURRING_BILLING_SUPPORTED,
    PAYMENT_PROVIDER_RENEWAL_POLICY,
    PAYMENT_PROVIDER_TRIAL_GRACE_PRORATION_SUPPORTED,
    SUPPORTED_PAYMENT_UNITS,
    PaymentProviderCandidate,
    PaymentProviderEvidenceKind,
)
from mayak.modules.entitlements_and_billing.payment_reconciliation import (
    APPROVED_PAYMENT_RECONCILIATION_PROVIDER_CANDIDATES,
    ManualRefundAction,
    ManualRefundIdempotencyRecord,
    ManualRefundOutcome,
    ManualRefundRequest,
    PaymentReconciliationAction,
    PaymentReconciliationIdempotencyRecord,
    PaymentReconciliationOutcome,
    PaymentReconciliationRequest,
    ProviderEventEffect,
    ReconciliationAction,
    ReconciliationIdempotencyRecord,
    SemanticCommitState,
    RefundAction,
    compute_manual_refund_request_fingerprint,
    compute_payment_reconciliation_request_fingerprint,
    evaluate_manual_refund,
    evaluate_payment_reconciliation,
)
from mayak.modules.entitlements_and_billing.policies import FUTURE_DECISION_GATES
from mayak.platform.idempotency import IdempotencyKey

DECISION_AT = datetime(2026, 7, 8, 10, 0, tzinfo=timezone.utc)
OWN_ACCOUNT = "acct-eb09-own-001"
AUDIT_REFERENCE = "audit-eb09-001"


def _reconciliation_request(
    *,
    provider_candidate: PaymentProviderCandidate | str = PaymentProviderCandidate.YOOKASSA,
    synthetic_provider_event_reference: str = "provider-event-ref-eb09-001",
    provider_event_identity: str | None = "provider-event-id-eb09-001",
    evidence_kind: PaymentProviderEvidenceKind = PaymentProviderEvidenceKind.PAYMENT_EVIDENCE,
    requested_action: ReconciliationAction = ReconciliationAction.RECORD_EVIDENCE_ONLY,
    provider_effect: ProviderEventEffect = ProviderEventEffect.CONFIRMED,
    idempotency_key: IdempotencyKey | None = IdempotencyKey(value="idem-eb09-recon-001"),
    normalized_amount: Decimal | None = Decimal("990"),
    payment_unit: str | None = "RUB",
    raw_payload_present: bool = False,
    raw_payload_redacted: bool = True,
    commit_state: SemanticCommitState = SemanticCommitState.OWNER_APPROVED,
    prior_idempotency_record: ReconciliationIdempotencyRecord | None = None,
    request_fingerprint=None,
    audit_reference: str = AUDIT_REFERENCE,
) -> PaymentReconciliationRequest:
    request = PaymentReconciliationRequest(
        account_id=OWN_ACCOUNT,
        provider_candidate=provider_candidate,
        synthetic_provider_event_reference=synthetic_provider_event_reference,
        provider_event_identity=provider_event_identity,
        evidence_kind=evidence_kind,
        requested_action=requested_action,
        provider_effect=provider_effect,
        normalized_amount=normalized_amount,
        payment_unit=payment_unit,
        raw_payload_present=raw_payload_present,
        raw_payload_redacted=raw_payload_redacted,
        commit_state=commit_state,
        idempotency_key=idempotency_key,
        request_fingerprint=request_fingerprint,
        audit_reference=audit_reference,
        decision_at=DECISION_AT,
        prior_idempotency_record=prior_idempotency_record,
    )
    if request.request_fingerprint is None:
        request = request.model_copy(
            update={"request_fingerprint": compute_payment_reconciliation_request_fingerprint(request)}
        )
    return request


def _refund_request(
    *,
    provider_candidate: PaymentProviderCandidate | str = PaymentProviderCandidate.TBANK,
    synthetic_provider_event_reference: str = "refund-event-ref-eb09-001",
    provider_event_identity: str | None = "refund-event-id-eb09-001",
    evidence_kind: PaymentProviderEvidenceKind = PaymentProviderEvidenceKind.REFUND_EVIDENCE,
    requested_action: RefundAction = RefundAction.REQUEST_MANUAL_REVIEW,
    idempotency_key: IdempotencyKey | None = IdempotencyKey(value="idem-eb09-refund-001"),
    normalized_amount: Decimal | None = Decimal("990"),
    payment_unit: str | None = "RUB",
    raw_payload_present: bool = False,
    raw_payload_redacted: bool = True,
    commit_state: SemanticCommitState = SemanticCommitState.OWNER_APPROVED,
    prior_idempotency_record: ManualRefundIdempotencyRecord | None = None,
    request_fingerprint=None,
    audit_reference: str = AUDIT_REFERENCE,
) -> ManualRefundRequest:
    request = ManualRefundRequest(
        account_id=OWN_ACCOUNT,
        provider_candidate=provider_candidate,
        synthetic_provider_event_reference=synthetic_provider_event_reference,
        provider_event_identity=provider_event_identity,
        evidence_kind=evidence_kind,
        requested_action=requested_action,
        normalized_amount=normalized_amount,
        payment_unit=payment_unit,
        raw_payload_present=raw_payload_present,
        raw_payload_redacted=raw_payload_redacted,
        commit_state=commit_state,
        idempotency_key=idempotency_key,
        request_fingerprint=request_fingerprint,
        audit_reference=audit_reference,
        decision_at=DECISION_AT,
        prior_idempotency_record=prior_idempotency_record,
    )
    if request.request_fingerprint is None:
        request = request.model_copy(update={"request_fingerprint": compute_manual_refund_request_fingerprint(request)})
    return request


def test_eb09_reconciliation_outcomes_represented_001() -> None:
    assert [member.value for member in PaymentReconciliationOutcome] == [
        "RECORDED",
        "DUPLICATE",
        "REJECTED",
        "AMBIGUOUS",
        "RECONCILE_REQUIRED",
        "CONFIRMED",
        "UNRESOLVED",
        "MANUAL_REVIEW_REQUIRED",
        "REPLAYED",
        "IDEMPOTENCY_MISMATCH",
        "BLOCKED",
    ]
    assert PaymentReconciliationOutcome("BLOCKED") is PaymentReconciliationOutcome.BLOCKED


def test_eb09_manual_refund_outcomes_represented_001() -> None:
    assert [member.value for member in ManualRefundOutcome] == [
        "MANUAL_REFUND_REVIEW_REQUIRED",
        "MANUAL_REFUND_REFERENCED",
        "AUTOMATIC_REFUND_BLOCKED",
        "PROVIDER_REFUND_API_BLOCKED",
        "REFUND_REJECTED",
        "REFUND_REPLAYED",
        "REFUND_IDEMPOTENCY_MISMATCH",
    ]
    assert ManualRefundOutcome("REFUND_REPLAYED") is ManualRefundOutcome.REFUND_REPLAYED


def test_eb09_records_payment_evidence_only_001() -> None:
    decision = evaluate_payment_reconciliation(_reconciliation_request())

    assert decision.outcome is PaymentReconciliationOutcome.RECORDED
    assert decision.reason_code == "RECONCILIATION_RECORDED_EVIDENCE_ONLY"
    assert decision.source_references == (
        "provider-event-ref-eb09-001",
        "provider-event-id-eb09-001",
        "YOOKASSA",
        "PAYMENT_EVIDENCE",
        "idem-eb09-recon-001",
        AUDIT_REFERENCE,
    )


def test_eb09_confirmed_reconciliation_non_authority_001() -> None:
    request = _reconciliation_request(requested_action=ReconciliationAction.CONFIRM_EXTERNAL_EFFECT)
    decision = evaluate_payment_reconciliation(request)

    assert decision.outcome is PaymentReconciliationOutcome.CONFIRMED
    assert decision.reason_code == "RECONCILIATION_CONFIRMED_EVIDENCE_ONLY"
    assert not hasattr(decision, "grant_id")
    assert not hasattr(decision, "subscription_id")


def test_eb09_duplicate_provider_event_no_second_effect_001() -> None:
    request = _reconciliation_request(provider_event_identity="provider-event-id-eb09-duplicate")
    prior = ReconciliationIdempotencyRecord(
        requested_action=request.requested_action,
        idempotency_key=IdempotencyKey(value="idem-eb09-recon-duplicate-prior"),
        request_fingerprint=request.request_fingerprint,
        terminal_outcome=PaymentReconciliationOutcome.RECORDED,
        provider_event_identity="provider-event-id-eb09-duplicate",
    )
    decision = evaluate_payment_reconciliation(request.model_copy(update={"prior_idempotency_record": prior}))

    assert decision.outcome is PaymentReconciliationOutcome.DUPLICATE
    assert decision.terminal_outcome is PaymentReconciliationOutcome.RECORDED
    assert decision.reason_code == "DUPLICATE_PROVIDER_EVENT_IDENTITY"


def test_eb09_malformed_evidence_rejected_001() -> None:
    with pytest.raises(ValidationError):
        PaymentReconciliationRequest(
            account_id=OWN_ACCOUNT,
            provider_candidate=PaymentProviderCandidate.YOOKASSA,
            synthetic_provider_event_reference="provider-event-ref-eb09-invalid",
            provider_event_identity="provider-event-id-eb09-invalid",
            evidence_kind=PaymentProviderEvidenceKind.PAYMENT_EVIDENCE,
            requested_action=ReconciliationAction.RECORD_EVIDENCE_ONLY,
            provider_effect=ProviderEventEffect.CONFIRMED,
            normalized_amount=Decimal("990"),
            payment_unit=None,
            raw_payload_present=False,
            raw_payload_redacted=True,
            commit_state=SemanticCommitState.OWNER_APPROVED,
            idempotency_key=IdempotencyKey(value="idem-eb09-invalid-001"),
            audit_reference=AUDIT_REFERENCE,
            decision_at=DECISION_AT,
        )


def test_eb09_non_redacted_payload_rejected_001() -> None:
    decision = evaluate_payment_reconciliation(
        _reconciliation_request(raw_payload_present=True, raw_payload_redacted=False)
    )

    assert decision.outcome is PaymentReconciliationOutcome.REJECTED
    assert decision.reason_code == "RAW_PAYLOAD_MUST_BE_REDACTED"


def test_eb09_ambiguous_provider_effect_reconcile_required_001() -> None:
    decision = evaluate_payment_reconciliation(
        _reconciliation_request(
            requested_action=ReconciliationAction.CONFIRM_EXTERNAL_EFFECT,
            provider_effect=ProviderEventEffect.AMBIGUOUS,
        )
    )

    assert decision.outcome is PaymentReconciliationOutcome.RECONCILE_REQUIRED
    assert decision.reason_code == "AMBIGUOUS_PROVIDER_EFFECT_RECONCILE_REQUIRED"


def test_eb09_unknown_provider_effect_not_no_effect_001() -> None:
    decision = evaluate_payment_reconciliation(
        _reconciliation_request(
            requested_action=ReconciliationAction.CONFIRM_EXTERNAL_EFFECT,
            provider_effect=ProviderEventEffect.UNKNOWN,
        )
    )

    assert decision.outcome is PaymentReconciliationOutcome.UNRESOLVED
    assert decision.reason_code == "UNKNOWN_PROVIDER_EFFECT_UNRESOLVED"
    assert decision.outcome is not PaymentReconciliationOutcome.RECORDED
    assert decision.outcome is not PaymentReconciliationOutcome.CONFIRMED


def test_eb09_blind_retry_blocked_001() -> None:
    decision = evaluate_payment_reconciliation(
        _reconciliation_request(
            requested_action=ReconciliationAction.BLIND_RETRY,
            provider_effect=ProviderEventEffect.UNKNOWN,
        )
    )

    assert decision.outcome is PaymentReconciliationOutcome.BLOCKED
    assert decision.reason_code == "BLIND_RETRY_FORBIDDEN"


def test_eb09_manual_refund_review_required_001() -> None:
    decision = evaluate_manual_refund(_refund_request(requested_action=RefundAction.REQUEST_MANUAL_REVIEW))

    assert decision.outcome is ManualRefundOutcome.MANUAL_REFUND_REVIEW_REQUIRED
    assert decision.reason_code == "MANUAL_REFUND_REVIEW_REQUIRED"


def test_eb09_manual_refund_referenced_evidence_only_001() -> None:
    decision = evaluate_manual_refund(
        _refund_request(requested_action=RefundAction.RECORD_MANUAL_REFUND_EVIDENCE)
    )

    assert decision.outcome is ManualRefundOutcome.MANUAL_REFUND_REFERENCED
    assert decision.reason_code == "MANUAL_REFUND_REFERENCED"


def test_eb09_automatic_refund_blocked_001() -> None:
    decision = evaluate_manual_refund(_refund_request(requested_action=RefundAction.AUTOMATIC_REFUND_ATTEMPT))

    assert decision.outcome is ManualRefundOutcome.AUTOMATIC_REFUND_BLOCKED
    assert decision.reason_code == "AUTOMATIC_REFUND_BLOCKED"


def test_eb09_provider_refund_api_blocked_001() -> None:
    decision = evaluate_manual_refund(_refund_request(requested_action=RefundAction.PROVIDER_REFUND_API_ATTEMPT))

    assert decision.outcome is ManualRefundOutcome.PROVIDER_REFUND_API_BLOCKED
    assert decision.reason_code == "PROVIDER_REFUND_API_BLOCKED"


def test_eb09_recurring_billing_blocked_001() -> None:
    decision = evaluate_payment_reconciliation(
        _reconciliation_request(requested_action=ReconciliationAction.RECURRING_BILLING)
    )

    assert decision.outcome is PaymentReconciliationOutcome.BLOCKED
    assert decision.reason_code == "RUNTIME_ACTION_BLOCKED"


def test_eb09_trial_grace_proration_blocked_001() -> None:
    decision = evaluate_manual_refund(
        _refund_request(requested_action=RefundAction.TRIAL_GRACE_PRORATION_ATTEMPT)
    )

    assert decision.outcome is ManualRefundOutcome.REFUND_REJECTED
    assert decision.reason_code == "TRIAL_GRACE_PRORATION_ATTEMPT_BLOCKED"


def test_eb09_reconciliation_missing_idempotency_rejected_001() -> None:
    decision = evaluate_payment_reconciliation(_reconciliation_request(idempotency_key=None))

    assert decision.outcome is PaymentReconciliationOutcome.REJECTED
    assert decision.reason_code == "IDEMPOTENCY_KEY_REQUIRED"


def test_eb09_reconciliation_idempotent_replay_same_fingerprint_001() -> None:
    request = _reconciliation_request(requested_action=ReconciliationAction.CONFIRM_EXTERNAL_EFFECT)
    prior = ReconciliationIdempotencyRecord(
        requested_action=request.requested_action,
        idempotency_key=request.idempotency_key,
        request_fingerprint=request.request_fingerprint,
        terminal_outcome=PaymentReconciliationOutcome.CONFIRMED,
        provider_event_identity=request.provider_event_identity,
    )
    decision = evaluate_payment_reconciliation(request.model_copy(update={"prior_idempotency_record": prior}))

    assert decision.outcome is PaymentReconciliationOutcome.REPLAYED
    assert decision.terminal_outcome is PaymentReconciliationOutcome.CONFIRMED
    assert decision.reason_code == "IDEMPOTENT_REPLAY"


def test_eb09_reconciliation_idempotency_mismatch_001() -> None:
    request = _reconciliation_request(requested_action=ReconciliationAction.CONFIRM_EXTERNAL_EFFECT)
    prior = ReconciliationIdempotencyRecord(
        requested_action=request.requested_action,
        idempotency_key=request.idempotency_key,
        request_fingerprint=request.request_fingerprint,
        terminal_outcome=PaymentReconciliationOutcome.CONFIRMED,
        provider_event_identity=request.provider_event_identity,
    )
    changed_request = request.model_copy(
        update={
            "synthetic_provider_event_reference": "provider-event-ref-eb09-changed",
            "prior_idempotency_record": prior,
        }
    )
    changed_request = changed_request.model_copy(
        update={"request_fingerprint": compute_payment_reconciliation_request_fingerprint(changed_request)}
    )
    decision = evaluate_payment_reconciliation(changed_request)

    assert decision.outcome is PaymentReconciliationOutcome.IDEMPOTENCY_MISMATCH
    assert decision.reason_code == "IDEMPOTENCY_MISMATCH"


def test_eb09_refund_missing_idempotency_rejected_001() -> None:
    decision = evaluate_manual_refund(_refund_request(idempotency_key=None))

    assert decision.outcome is ManualRefundOutcome.REFUND_REJECTED
    assert decision.reason_code == "IDEMPOTENCY_KEY_REQUIRED"


def test_eb09_refund_idempotent_replay_same_fingerprint_001() -> None:
    request = _refund_request(requested_action=RefundAction.RECORD_MANUAL_REFUND_EVIDENCE)
    prior = ManualRefundIdempotencyRecord(
        requested_action=request.requested_action,
        idempotency_key=request.idempotency_key,
        request_fingerprint=request.request_fingerprint,
        terminal_outcome=ManualRefundOutcome.MANUAL_REFUND_REFERENCED,
        provider_event_identity=request.provider_event_identity,
    )
    decision = evaluate_manual_refund(request.model_copy(update={"prior_idempotency_record": prior}))

    assert decision.outcome is ManualRefundOutcome.REFUND_REPLAYED
    assert decision.terminal_outcome is ManualRefundOutcome.MANUAL_REFUND_REFERENCED
    assert decision.reason_code == "REFUND_IDEMPOTENT_REPLAY"


def test_eb09_refund_idempotency_mismatch_001() -> None:
    request = _refund_request(requested_action=RefundAction.RECORD_MANUAL_REFUND_EVIDENCE)
    prior = ManualRefundIdempotencyRecord(
        requested_action=request.requested_action,
        idempotency_key=request.idempotency_key,
        request_fingerprint=request.request_fingerprint,
        terminal_outcome=ManualRefundOutcome.MANUAL_REFUND_REFERENCED,
        provider_event_identity=request.provider_event_identity,
    )
    changed_request = request.model_copy(
        update={
            "synthetic_provider_event_reference": "refund-event-ref-eb09-changed",
            "prior_idempotency_record": prior,
        }
    )
    changed_request = changed_request.model_copy(
        update={"request_fingerprint": compute_manual_refund_request_fingerprint(changed_request)}
    )
    decision = evaluate_manual_refund(changed_request)

    assert decision.outcome is ManualRefundOutcome.REFUND_IDEMPOTENCY_MISMATCH
    assert decision.reason_code == "REFUND_IDEMPOTENCY_MISMATCH"


def test_eb09_unknown_commit_state_no_silent_success_001() -> None:
    decision = evaluate_payment_reconciliation(
        _reconciliation_request(
            commit_state=SemanticCommitState.UNKNOWN,
            requested_action=ReconciliationAction.CONFIRM_EXTERNAL_EFFECT,
            provider_effect=ProviderEventEffect.CONFIRMED,
        )
    )

    assert decision.outcome is PaymentReconciliationOutcome.UNRESOLVED
    assert decision.reason_code == "UNKNOWN_COMMIT_STATE"
    assert decision.outcome is not PaymentReconciliationOutcome.CONFIRMED


def test_eb09_no_payment_derived_entitlement_grant_001() -> None:
    decision = evaluate_payment_reconciliation(
        _reconciliation_request(requested_action=ReconciliationAction.CONFIRM_EXTERNAL_EFFECT)
    )

    assert not hasattr(decision, "grant_id")
    assert not hasattr(decision, "subscription_id")
    assert not hasattr(decision, "entitlement_grant")
    assert decision.reason.endswith("does not grant access.")


def test_eb09_no_raw_payload_storage_001() -> None:
    request = _reconciliation_request(raw_payload_present=True, raw_payload_redacted=True)
    decision = evaluate_payment_reconciliation(request)

    assert "raw_payload_body" not in type(request).model_fields
    assert "raw_payload_body" not in type(decision).model_fields
    assert decision.raw_payload_present is True
    assert decision.raw_payload_redacted is True


def test_eb09_no_secrets_card_data_in_fixtures_001() -> None:
    request = _reconciliation_request()
    refund_request = _refund_request()
    payload_text = f"{request.model_dump_json()} {refund_request.model_dump_json()}".lower()

    for forbidden in ("token", "secret", "credential", "password", "card", "cvv", "pan"):
        assert forbidden not in payload_text


def test_eb09_od010_od011_od013_remain_gated_001() -> None:
    assert FUTURE_DECISION_GATES == ("OD-010", "OD-011", "OD-013")
    assert PAYMENT_PROVIDER_RENEWAL_POLICY == "MANUAL_RENEWAL_ONLY"
    assert PAYMENT_PROVIDER_REFUND_POLICY == "MANUAL_REFUNDS_ONLY"
    assert PAYMENT_PROVIDER_RECURRING_BILLING_SUPPORTED is False
    assert PAYMENT_PROVIDER_TRIAL_GRACE_PRORATION_SUPPORTED is False
    assert APPROVED_PAYMENT_RECONCILIATION_PROVIDER_CANDIDATES == (
        PaymentProviderCandidate.YOOKASSA,
        PaymentProviderCandidate.TELEGRAM_STARS,
        PaymentProviderCandidate.TBANK,
    )
    assert SUPPORTED_PAYMENT_UNITS == ("RUB", "TELEGRAM_STARS")


def test_eb09_no_runtime_db_provider_imports_001() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    source = (repo_root / "src/mayak/modules/entitlements_and_billing/payment_reconciliation.py").read_text()
    tree = ast.parse(source)
    roots: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".", 1)[0])
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            roots.add(node.module.split(".", 1)[0])

    allowed_roots = {
        "__future__",
        "datetime",
        "decimal",
        "enum",
        "mayak",
        "pydantic",
        "payment_provider_boundary",
        "typing",
    }
    assert roots - allowed_roots == set(), sorted(roots - allowed_roots)
