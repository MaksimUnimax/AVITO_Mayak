from __future__ import annotations

import ast
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from mayak.modules.entitlements_and_billing import (
    PAYMENT_NOT_ENTITLEMENT,
    PAYMENT_PROVIDER_REFUND_POLICY,
    PAYMENT_PROVIDER_RECURRING_BILLING_SUPPORTED,
    PAYMENT_PROVIDER_RENEWAL_POLICY,
    PAYMENT_PROVIDER_TRIAL_GRACE_PRORATION_SUPPORTED,
    FUTURE_DECISION_GATES,
    SUPPORTED_PAYMENT_UNITS,
    PaymentProviderBoundaryAction,
    PaymentProviderBoundaryActorContext,
    PaymentProviderBoundaryDecision,
    PaymentProviderBoundaryOutcome,
    PaymentProviderBoundaryRequest,
    PaymentProviderCandidate,
    PaymentProviderEvidenceKind,
    PaymentProviderIdempotencyRecord,
    compute_payment_provider_boundary_request_fingerprint,
    evaluate_payment_provider_boundary,
)
from mayak.modules.entitlements_and_billing.payment_provider_boundary import (
    PaymentProviderBoundaryAction as PaymentProviderBoundaryActionModule,
)
from mayak.platform.idempotency import IdempotencyKey

DECISION_AT = datetime(2026, 7, 8, 10, 0, tzinfo=timezone.utc)
OWN_ACCOUNT = "acct-eb08-own-001"
AUDIT_REFERENCE = "audit-eb08-001"
ACTOR = PaymentProviderBoundaryActorContext(
    actor_id="actor-eb08-operator-001",
    actor_category="OPERATOR",
    authorization_scope="entitlements.payment_provider_boundary",
    authorization_reference="authz-eb08-001",
    audit_reference=AUDIT_REFERENCE,
    service_name="billing-semantic-service",
)


def _request(
    *,
    provider_candidate: PaymentProviderCandidate | str,
    evidence_kind: PaymentProviderEvidenceKind,
    requested_action: PaymentProviderBoundaryAction = PaymentProviderBoundaryAction.CAPTURE_EVIDENCE_ONLY,
    idempotency_key: IdempotencyKey | None,
    raw_payload_present: bool = False,
    raw_payload_redacted: bool = True,
    claims_authority_from_raw_payload: bool = False,
    prior_idempotency_record: PaymentProviderIdempotencyRecord | None = None,
    synthetic_provider_event_id: str | None = None,
) -> PaymentProviderBoundaryRequest:
    return PaymentProviderBoundaryRequest(
        account_id=OWN_ACCOUNT,
        provider_candidate=provider_candidate,
        evidence_kind=evidence_kind,
        provider_reference_id="provider-ref-eb08-001",
        synthetic_provider_event_id=synthetic_provider_event_id,
        requested_action=requested_action,
        normalized_amount=Decimal("990"),
        payment_unit="RUB",
        raw_payload_present=raw_payload_present,
        raw_payload_redacted=raw_payload_redacted,
        claims_authority_from_raw_payload=claims_authority_from_raw_payload,
        actor=ACTOR,
        audit_reference=AUDIT_REFERENCE,
        decision_at=DECISION_AT,
        idempotency_key=idempotency_key,
        prior_idempotency_record=prior_idempotency_record,
    )


def _evidence_request(
    *,
    provider_candidate: PaymentProviderCandidate | str,
    evidence_kind: PaymentProviderEvidenceKind,
    idempotency_key: IdempotencyKey,
    synthetic_provider_event_id: str | None = None,
) -> PaymentProviderBoundaryRequest:
    return _request(
        provider_candidate=provider_candidate,
        evidence_kind=evidence_kind,
        idempotency_key=idempotency_key,
        synthetic_provider_event_id=synthetic_provider_event_id,
    )


def test_eb08_provider_candidates_represented_001() -> None:
    assert [member.value for member in PaymentProviderCandidate] == ["YOOKASSA", "TELEGRAM_STARS", "TBANK"]
    assert PaymentProviderBoundaryActionModule.CAPTURE_EVIDENCE_ONLY.value == "CAPTURE_EVIDENCE_ONLY"
    assert SUPPORTED_PAYMENT_UNITS == ("RUB", "TELEGRAM_STARS")


def test_eb08_yookassa_evidence_accepted_as_evidence_only_001() -> None:
    request = _evidence_request(
        provider_candidate=PaymentProviderCandidate.YOOKASSA,
        evidence_kind=PaymentProviderEvidenceKind.PAYMENT_EVIDENCE,
        idempotency_key=IdempotencyKey(value="idem-eb08-yookassa-001"),
    )
    decision = evaluate_payment_provider_boundary(request)

    assert decision.outcome is PaymentProviderBoundaryOutcome.ACCEPTED_AS_EVIDENCE
    assert decision.terminal_outcome is PaymentProviderBoundaryOutcome.ACCEPTED_AS_EVIDENCE
    assert decision.reason_code == "PROVIDER_EVIDENCE_ACCEPTED_ONLY"
    assert decision.provider_candidate == "YOOKASSA"


def test_eb08_telegram_stars_evidence_accepted_as_evidence_only_001() -> None:
    request = _evidence_request(
        provider_candidate=PaymentProviderCandidate.TELEGRAM_STARS,
        evidence_kind=PaymentProviderEvidenceKind.WEBHOOK_NOTIFICATION_EVIDENCE,
        idempotency_key=IdempotencyKey(value="idem-eb08-stars-001"),
        synthetic_provider_event_id="tg-stars-event-eb08-001",
    )
    decision = evaluate_payment_provider_boundary(request)

    assert decision.outcome is PaymentProviderBoundaryOutcome.ACCEPTED_AS_EVIDENCE
    assert decision.source_references == (
        "provider-ref-eb08-001",
        "tg-stars-event-eb08-001",
        "TELEGRAM_STARS",
        "WEBHOOK_NOTIFICATION_EVIDENCE",
        "idem-eb08-stars-001",
        AUDIT_REFERENCE,
    )


def test_eb08_tbank_evidence_accepted_as_evidence_only_001() -> None:
    request = _evidence_request(
        provider_candidate=PaymentProviderCandidate.TBANK,
        evidence_kind=PaymentProviderEvidenceKind.RECEIPT_INVOICE_TAX_EVIDENCE,
        idempotency_key=IdempotencyKey(value="idem-eb08-tbank-001"),
    )
    decision = evaluate_payment_provider_boundary(request)

    assert decision.outcome is PaymentProviderBoundaryOutcome.ACCEPTED_AS_EVIDENCE
    assert decision.payment_unit == "RUB"


def test_eb08_unknown_provider_rejected_001() -> None:
    request = _evidence_request(
        provider_candidate="UNKNOWN_PROVIDER",
        evidence_kind=PaymentProviderEvidenceKind.PAYMENT_EVIDENCE,
        idempotency_key=IdempotencyKey(value="idem-eb08-unknown-001"),
    )
    decision = evaluate_payment_provider_boundary(request)

    assert decision.outcome is PaymentProviderBoundaryOutcome.UNSUPPORTED_PROVIDER
    assert decision.reason_code == "UNSUPPORTED_PROVIDER"


def test_eb08_payment_evidence_not_authority_001() -> None:
    request = _request(
        provider_candidate=PaymentProviderCandidate.YOOKASSA,
        evidence_kind=PaymentProviderEvidenceKind.PAYMENT_EVIDENCE,
        requested_action=PaymentProviderBoundaryAction.REQUEST_AUTHORITY_FROM_EVIDENCE,
        idempotency_key=IdempotencyKey(value="idem-eb08-authority-001"),
    )
    decision = evaluate_payment_provider_boundary(request)

    assert decision.outcome is PaymentProviderBoundaryOutcome.PAYMENT_IS_NOT_AUTHORITY
    assert decision.reason_code == "PAYMENT_IS_NOT_AUTHORITY"


def test_eb08_raw_payload_not_authority_001() -> None:
    request = _request(
        provider_candidate=PaymentProviderCandidate.YOOKASSA,
        evidence_kind=PaymentProviderEvidenceKind.PAYMENT_EVIDENCE,
        claims_authority_from_raw_payload=True,
        idempotency_key=IdempotencyKey(value="idem-eb08-raw-001"),
    )
    decision = evaluate_payment_provider_boundary(request)

    assert decision.outcome is PaymentProviderBoundaryOutcome.RAW_PAYLOAD_NOT_AUTHORITY
    assert decision.reason_code == "RAW_PAYLOAD_NOT_AUTHORITY"


def test_eb08_entitlement_grant_from_provider_blocked_001() -> None:
    request = _request(
        provider_candidate=PaymentProviderCandidate.YOOKASSA,
        evidence_kind=PaymentProviderEvidenceKind.PAYMENT_EVIDENCE,
        requested_action=PaymentProviderBoundaryAction.GRANT_ENTITLEMENT,
        idempotency_key=IdempotencyKey(value="idem-eb08-blocked-001"),
    )
    decision = evaluate_payment_provider_boundary(request)

    assert decision.outcome is PaymentProviderBoundaryOutcome.BLOCKED
    assert decision.reason_code == "PAYMENT_IS_NOT_AUTHORITY"


def test_eb08_manual_renewal_only_001() -> None:
    assert PAYMENT_PROVIDER_RENEWAL_POLICY == "MANUAL_RENEWAL_ONLY"
    assert PAYMENT_PROVIDER_RECURRING_BILLING_SUPPORTED is False


def test_eb08_manual_refunds_only_001() -> None:
    assert PAYMENT_PROVIDER_REFUND_POLICY == "MANUAL_REFUNDS_ONLY"


def test_eb08_recurring_billing_blocked_001() -> None:
    request = _request(
        provider_candidate=PaymentProviderCandidate.TBANK,
        evidence_kind=PaymentProviderEvidenceKind.PAYMENT_EVIDENCE,
        requested_action=PaymentProviderBoundaryAction.RECURRING_BILLING,
        idempotency_key=IdempotencyKey(value="idem-eb08-recurring-001"),
    )
    decision = evaluate_payment_provider_boundary(request)

    assert decision.outcome is PaymentProviderBoundaryOutcome.BLOCKED
    assert decision.reason_code == "RECURRING_BILLING_BLOCKED"


def test_eb08_automatic_refund_blocked_001() -> None:
    request = _request(
        provider_candidate=PaymentProviderCandidate.TELEGRAM_STARS,
        evidence_kind=PaymentProviderEvidenceKind.REFUND_EVIDENCE,
        requested_action=PaymentProviderBoundaryAction.REFUND_AUTOMATION,
        idempotency_key=IdempotencyKey(value="idem-eb08-refund-001"),
    )
    decision = evaluate_payment_provider_boundary(request)

    assert decision.outcome is PaymentProviderBoundaryOutcome.BLOCKED
    assert decision.reason_code == "REFUND_AUTOMATION_BLOCKED"


def test_eb08_trial_grace_proration_blocked_001() -> None:
    assert PAYMENT_PROVIDER_TRIAL_GRACE_PRORATION_SUPPORTED is False


def test_eb08_provider_sdk_api_webhook_runtime_blocked_001() -> None:
    sdk_request = _request(
        provider_candidate=PaymentProviderCandidate.YOOKASSA,
        evidence_kind=PaymentProviderEvidenceKind.PAYMENT_EVIDENCE,
        requested_action=PaymentProviderBoundaryAction.SDK_API_CALL,
        idempotency_key=IdempotencyKey(value="idem-eb08-sdk-001"),
    )
    webhook_request = _request(
        provider_candidate=PaymentProviderCandidate.TBANK,
        evidence_kind=PaymentProviderEvidenceKind.WEBHOOK_NOTIFICATION_EVIDENCE,
        requested_action=PaymentProviderBoundaryAction.WEBHOOK_PROCESSING,
        idempotency_key=IdempotencyKey(value="idem-eb08-webhook-001"),
    )

    sdk_decision = evaluate_payment_provider_boundary(sdk_request)
    webhook_decision = evaluate_payment_provider_boundary(webhook_request)

    assert sdk_decision.outcome is PaymentProviderBoundaryOutcome.UNSUPPORTED_RUNTIME_ACTION
    assert webhook_decision.outcome is PaymentProviderBoundaryOutcome.UNSUPPORTED_RUNTIME_ACTION


def test_eb08_invoice_receipt_tax_runtime_blocked_001() -> None:
    request = _request(
        provider_candidate=PaymentProviderCandidate.TELEGRAM_STARS,
        evidence_kind=PaymentProviderEvidenceKind.RECEIPT_INVOICE_TAX_EVIDENCE,
        requested_action=PaymentProviderBoundaryAction.RECEIPT_INVOICE_TAX_RUNTIME,
        idempotency_key=IdempotencyKey(value="idem-eb08-invoice-001"),
    )
    decision = evaluate_payment_provider_boundary(request)

    assert decision.outcome is PaymentProviderBoundaryOutcome.UNSUPPORTED_RUNTIME_ACTION
    assert decision.reason_code == "UNSUPPORTED_RUNTIME_ACTION"


def test_eb08_card_credential_handling_blocked_001() -> None:
    request = _request(
        provider_candidate=PaymentProviderCandidate.TBANK,
        evidence_kind=PaymentProviderEvidenceKind.PAYMENT_EVIDENCE,
        requested_action=PaymentProviderBoundaryAction.CARD_DATA_HANDLING,
        idempotency_key=IdempotencyKey(value="idem-eb08-card-001"),
    )
    decision = evaluate_payment_provider_boundary(request)

    assert decision.outcome is PaymentProviderBoundaryOutcome.BLOCKED
    assert decision.reason_code == "CARD_DATA_HANDLING_BLOCKED"


def test_eb08_idempotent_replay_same_fingerprint_001() -> None:
    request = _evidence_request(
        provider_candidate=PaymentProviderCandidate.YOOKASSA,
        evidence_kind=PaymentProviderEvidenceKind.PAYMENT_EVIDENCE,
        idempotency_key=IdempotencyKey(value="idem-eb08-replay-001"),
    )
    fingerprint = compute_payment_provider_boundary_request_fingerprint(request)
    prior = PaymentProviderIdempotencyRecord(
        requested_action=request.requested_action,
        idempotency_key=request.idempotency_key,
        request_fingerprint=fingerprint,
        terminal_outcome=PaymentProviderBoundaryOutcome.ACCEPTED_AS_EVIDENCE,
    )
    decision = evaluate_payment_provider_boundary(request.model_copy(update={"prior_idempotency_record": prior}))

    assert decision.outcome is PaymentProviderBoundaryOutcome.REPLAYED
    assert decision.terminal_outcome is PaymentProviderBoundaryOutcome.ACCEPTED_AS_EVIDENCE
    assert decision.reason_code == "IDEMPOTENT_REPLAY"


def test_eb08_idempotency_mismatch_001() -> None:
    request = _evidence_request(
        provider_candidate=PaymentProviderCandidate.YOOKASSA,
        evidence_kind=PaymentProviderEvidenceKind.PAYMENT_EVIDENCE,
        idempotency_key=IdempotencyKey(value="idem-eb08-mismatch-001"),
    )
    prior = PaymentProviderIdempotencyRecord(
        requested_action=request.requested_action,
        idempotency_key=request.idempotency_key,
        request_fingerprint=compute_payment_provider_boundary_request_fingerprint(request),
        terminal_outcome=PaymentProviderBoundaryOutcome.ACCEPTED_AS_EVIDENCE,
    )
    changed_request = request.model_copy(
        update={
            "synthetic_provider_event_id": "changed-event-id",
            "prior_idempotency_record": prior,
        }
    )

    decision = evaluate_payment_provider_boundary(changed_request)

    assert decision.outcome is PaymentProviderBoundaryOutcome.IDEMPOTENCY_MISMATCH
    assert decision.reason_code == "IDEMPOTENCY_MISMATCH"


def test_eb08_missing_idempotency_rejected_001() -> None:
    request = _evidence_request(
        provider_candidate=PaymentProviderCandidate.TBANK,
        evidence_kind=PaymentProviderEvidenceKind.PAYMENT_EVIDENCE,
        idempotency_key=None,
    )
    decision = evaluate_payment_provider_boundary(request)

    assert decision.outcome is PaymentProviderBoundaryOutcome.REJECTED
    assert decision.reason_code == "IDEMPOTENCY_KEY_REQUIRED"


def test_eb08_no_raw_payload_storage_001() -> None:
    field_names = set(PaymentProviderBoundaryRequest.model_fields) | set(PaymentProviderBoundaryDecision.model_fields)

    for forbidden_field in (
        "raw_payload_body",
        "raw_payload_json",
        "payload_body",
        "payload_json",
        "provider_payload_body",
    ):
        assert forbidden_field not in field_names

    request = _evidence_request(
        provider_candidate=PaymentProviderCandidate.YOOKASSA,
        evidence_kind=PaymentProviderEvidenceKind.PAYMENT_EVIDENCE,
        idempotency_key=IdempotencyKey(value="idem-eb08-storage-001"),
    )
    decision = evaluate_payment_provider_boundary(request)
    payload_text = request.model_dump_json().lower() + decision.model_dump_json().lower()

    assert "card" not in payload_text
    assert "cvv" not in payload_text
    assert "pan" not in payload_text


def test_eb08_no_secrets_card_data_in_fixtures_001() -> None:
    fixture_text = PAYMENT_NOT_ENTITLEMENT.model_dump_json().lower()

    for forbidden_fragment in ("token", "secret", "credential", "password", "card", "cvv", "pan"):
        assert forbidden_fragment not in fixture_text


def test_eb08_od010_od011_od013_remain_gated_001() -> None:
    assert FUTURE_DECISION_GATES == ("OD-010", "OD-011", "OD-013")

    request_field_names = set(PaymentProviderBoundaryRequest.model_fields)
    decision_field_names = set(PaymentProviderBoundaryDecision.model_fields)

    for forbidden_fragment in ("country", "monitoring_frequency", "retention"):
        assert forbidden_fragment not in request_field_names
        assert forbidden_fragment not in decision_field_names


def test_eb08_no_runtime_db_provider_imports_001() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    source = (repo_root / "src/mayak/modules/entitlements_and_billing/payment_provider_boundary.py").read_text()
    tree = ast.parse(source)

    allowed_import_roots = {
        "__future__",
        "datetime",
        "decimal",
        "enum",
        "mayak",
        "pydantic",
        "typing",
    }

    import_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                import_roots.add(alias.name.split(".", 1)[0])
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            import_roots.add(node.module.split(".", 1)[0])

    assert import_roots <= allowed_import_roots

    request = _evidence_request(
        provider_candidate=PaymentProviderCandidate.YOOKASSA,
        evidence_kind=PaymentProviderEvidenceKind.PAYMENT_EVIDENCE,
        idempotency_key=IdempotencyKey(value="idem-eb08-imports-001"),
    )
    decision = evaluate_payment_provider_boundary(request)
    synthetic_payload_text = request.model_dump_json().lower() + decision.model_dump_json().lower()

    for forbidden_fragment in ("sqlalchemy", "psycopg", "alembic", "fastapi", "httpx", "requests", "docker", "secret"):
        assert forbidden_fragment not in synthetic_payload_text
