from __future__ import annotations

import ast
from datetime import datetime, timezone
from pathlib import Path

from mayak.modules.entitlements_and_billing.subscription_lifecycle import (
    APPROVED_SUBSCRIPTION_TARIFF_FAMILIES,
    BASIC_TARIFF_POLICY,
    FREE_TARIFF_POLICY,
    FUTURE_DECISION_GATES,
    GRACE_SEMANTICS_SUPPORTED,
    PRORATION_SEMANTICS_SUPPORTED,
    SUBSCRIPTION_TARIFF_FAMILY_BASIC,
    SUBSCRIPTION_TARIFF_FAMILY_FREE,
    TRIAL_SEMANTICS_SUPPORTED,
    SubscriptionLifecycleAction,
    SubscriptionLifecycleActorContext,
    SubscriptionLifecycleDecision,
    SubscriptionLifecycleIdempotencyRecord,
    SubscriptionLifecycleOutcome,
    SubscriptionLifecycleRequest,
    SubscriptionPaymentMode,
    compute_subscription_lifecycle_request_fingerprint,
    evaluate_subscription_lifecycle,
)
from mayak.modules.entitlements_and_billing.contracts import EffectiveInterval, PaymentEvent, PaymentEventState, PaymentRecord, PaymentRecordState, Subscription, SubscriptionState
from mayak.platform.idempotency import IdempotencyKey

DECISION_AT = datetime(2026, 7, 8, 10, 0, tzinfo=timezone.utc)
ACTIVE_INTERVAL = EffectiveInterval(
    starts_at=datetime(2026, 7, 8, 9, 0, tzinfo=timezone.utc),
    ends_at=datetime(2026, 8, 8, 9, 0, tzinfo=timezone.utc),
)
EXPIRED_INTERVAL = EffectiveInterval(
    starts_at=datetime(2026, 6, 8, 9, 0, tzinfo=timezone.utc),
    ends_at=datetime(2026, 7, 8, 9, 0, tzinfo=timezone.utc),
)
OWN_ACCOUNT = "acct-eb05-own-001"
ALLOWED_SCOPE = "entitlements.subscription_lifecycle"


def _actor() -> SubscriptionLifecycleActorContext:
    return SubscriptionLifecycleActorContext(
        actor_id="actor-eb05-operator-001",
        actor_category="OPERATOR",
        authorization_scope=ALLOWED_SCOPE,
        authorization_reference="authz-eb05-001",
        audit_reference="audit-eb05-001",
    )


def _subscription(
    *,
    tariff_family,
    status: SubscriptionState = SubscriptionState.ACTIVE,
    interval: EffectiveInterval = ACTIVE_INTERVAL,
) -> Subscription:
    return Subscription(
        account_id=OWN_ACCOUNT,
        subscription_id=f"subscription-{tariff_family.value.lower()}-{status.value.lower()}",
        tariff_name=tariff_family,
        status=status,
        effective_interval=interval,
        source_reference=f"subscription-ref-{tariff_family.value.lower()}",
    )


def _request(
    *,
    requested_action: SubscriptionLifecycleAction,
    current_subscription: Subscription | None = None,
    current_tariff_family: str | None = None,
    requested_tariff_family: str | None = None,
    paid_access_interval: EffectiveInterval | None = None,
    requested_interval_minutes: int | None = 180,
    idempotency_key: IdempotencyKey | None = None,
    payment_records: tuple[PaymentRecord, ...] = (),
    payment_events: tuple[PaymentEvent, ...] = (),
    prior_idempotency_record: SubscriptionLifecycleIdempotencyRecord | None = None,
) -> SubscriptionLifecycleRequest:
    return SubscriptionLifecycleRequest(
        actor=_actor(),
        target_account_id=OWN_ACCOUNT,
        requested_action=requested_action,
        current_subscription=current_subscription,
        current_tariff_family=current_tariff_family,
        requested_tariff_family=requested_tariff_family,
        paid_access_interval=paid_access_interval,
        requested_interval_minutes=requested_interval_minutes,
        decision_at=DECISION_AT,
        idempotency_key=idempotency_key,
        payment_records=payment_records,
        payment_events=payment_events,
        prior_idempotency_record=prior_idempotency_record,
    )


def _payment_evidence() -> tuple[PaymentRecord, PaymentEvent]:
    record = PaymentRecord(
        account_id=OWN_ACCOUNT,
        record_id="payment-record-eb05-001",
        payment_reference="payment-ref-eb05-001",
        provider_name="provider-placeholder",
        status=PaymentRecordState.CONFIRMED,
        observed_at=DECISION_AT,
        amount_rub=990,
        currency_code="RUB",
        source_event_reference="payment-event-eb05-001",
        provider_payload_reference="payload-ref-eb05-001",
    )
    event = PaymentEvent(
        account_id=OWN_ACCOUNT,
        event_id="payment-event-eb05-001",
        event_reference="event-ref-eb05-001",
        provider_name="provider-placeholder",
        event_kind="payment.confirmed",
        status=PaymentEventState.VERIFIED_RECORDED,
        observed_at=DECISION_AT,
        source_record_reference="payment-record-eb05-001",
        provider_payload_reference="payload-ref-eb05-001",
    )
    return record, event


def test_eb05_subscription_lifecycle_outcomes_are_approved_and_complete_001() -> None:
    assert [member.value for member in SubscriptionLifecycleOutcome] == [
        "ASSIGNED",
        "CHANGED",
        "CANCELLED",
        "EXPIRED",
        "PENDING",
        "BLOCKED",
        "CONFLICT",
        "REPLAYED",
        "IDEMPOTENCY_MISMATCH",
        "REJECTED",
        "USER_CHOICE_REQUIRED",
        "FREE_COMPLIANCE_REQUIRED",
    ]


def test_eb05_subscription_active_basic_monthly_001() -> None:
    subscription = _subscription(tariff_family=SUBSCRIPTION_TARIFF_FAMILY_BASIC)
    decision = evaluate_subscription_lifecycle(
        _request(
            requested_action=SubscriptionLifecycleAction.ASSESS,
            current_subscription=subscription,
            current_tariff_family=subscription.tariff_name.value,
            requested_tariff_family=SUBSCRIPTION_TARIFF_FAMILY_BASIC.value,
            paid_access_interval=subscription.effective_interval,
            requested_interval_minutes=5,
        )
    )

    assert decision.outcome is SubscriptionLifecycleOutcome.ASSIGNED
    assert decision.payment_mode is SubscriptionPaymentMode.MANUAL_RENEWAL_ONLY
    assert decision.current_tariff_family == "BASIC"
    assert decision.paid_access_interval == subscription.effective_interval
    assert BASIC_TARIFF_POLICY.billing_period_label == "1 month"
    assert APPROVED_SUBSCRIPTION_TARIFF_FAMILIES == (
        SUBSCRIPTION_TARIFF_FAMILY_FREE,
        SUBSCRIPTION_TARIFF_FAMILY_BASIC,
    )


def test_eb05_subscription_free_fallback_no_trial_grace_001() -> None:
    subscription = _subscription(tariff_family=SUBSCRIPTION_TARIFF_FAMILY_FREE)
    decision = evaluate_subscription_lifecycle(
        _request(
            requested_action=SubscriptionLifecycleAction.ASSESS,
            current_subscription=subscription,
            current_tariff_family=subscription.tariff_name.value,
            requested_tariff_family=SUBSCRIPTION_TARIFF_FAMILY_FREE.value,
            paid_access_interval=subscription.effective_interval,
            requested_interval_minutes=180,
        )
    )

    assert decision.outcome is SubscriptionLifecycleOutcome.ASSIGNED
    assert decision.free_only_requirement is True
    assert TRIAL_SEMANTICS_SUPPORTED is False
    assert GRACE_SEMANTICS_SUPPORTED is False
    assert PRORATION_SEMANTICS_SUPPORTED is False
    assert FREE_TARIFF_POLICY.mechanism_notes == "same entitlement mechanism as paid tariff, stricter limits"


def test_eb05_subscription_expired_paid_user_choice_required_001() -> None:
    subscription = _subscription(
        tariff_family=SUBSCRIPTION_TARIFF_FAMILY_BASIC,
        status=SubscriptionState.EXPIRED,
        interval=EXPIRED_INTERVAL,
    )
    decision = evaluate_subscription_lifecycle(
        _request(
            requested_action=SubscriptionLifecycleAction.ASSESS,
            current_subscription=subscription,
            current_tariff_family=subscription.tariff_name.value,
            requested_tariff_family=SUBSCRIPTION_TARIFF_FAMILY_BASIC.value,
            paid_access_interval=subscription.effective_interval,
            requested_interval_minutes=180,
        )
    )

    assert decision.outcome is SubscriptionLifecycleOutcome.USER_CHOICE_REQUIRED
    assert decision.free_only_requirement is True
    assert decision.user_choice_required is True
    assert decision.free_compliance_required is False


def test_eb05_subscription_expired_paid_free_compliance_required_001() -> None:
    subscription = _subscription(
        tariff_family=SUBSCRIPTION_TARIFF_FAMILY_BASIC,
        status=SubscriptionState.EXPIRED,
        interval=EXPIRED_INTERVAL,
    )
    decision = evaluate_subscription_lifecycle(
        _request(
            requested_action=SubscriptionLifecycleAction.ASSESS,
            current_subscription=subscription,
            current_tariff_family=subscription.tariff_name.value,
            requested_tariff_family=SUBSCRIPTION_TARIFF_FAMILY_BASIC.value,
            paid_access_interval=subscription.effective_interval,
            requested_interval_minutes=5,
        )
    )

    assert decision.outcome is SubscriptionLifecycleOutcome.FREE_COMPLIANCE_REQUIRED
    assert decision.free_only_requirement is True
    assert decision.user_choice_required is True
    assert decision.free_compliance_required is True


def test_eb05_subscription_expired_paid_no_auto_beacon_choice_001() -> None:
    subscription = _subscription(
        tariff_family=SUBSCRIPTION_TARIFF_FAMILY_BASIC,
        status=SubscriptionState.EXPIRED,
        interval=EXPIRED_INTERVAL,
    )
    decision = evaluate_subscription_lifecycle(
        _request(
            requested_action=SubscriptionLifecycleAction.ASSESS,
            current_subscription=subscription,
            current_tariff_family=subscription.tariff_name.value,
            requested_tariff_family=SUBSCRIPTION_TARIFF_FAMILY_BASIC.value,
            paid_access_interval=subscription.effective_interval,
            requested_interval_minutes=180,
        )
    )

    assert decision.outcome is SubscriptionLifecycleOutcome.USER_CHOICE_REQUIRED
    assert not any("beacon" in field for field in type(decision).model_fields)


def test_eb05_subscription_manual_renewal_authorized_001() -> None:
    subscription = _subscription(
        tariff_family=SUBSCRIPTION_TARIFF_FAMILY_BASIC,
        status=SubscriptionState.EXPIRED,
        interval=EXPIRED_INTERVAL,
    )
    decision = evaluate_subscription_lifecycle(
        _request(
            requested_action=SubscriptionLifecycleAction.RENEW,
            current_subscription=subscription,
            current_tariff_family=subscription.tariff_name.value,
            requested_tariff_family=SUBSCRIPTION_TARIFF_FAMILY_BASIC.value,
            paid_access_interval=subscription.effective_interval,
            idempotency_key=IdempotencyKey(value="idem-eb05-renew-001"),
        )
    )

    assert decision.outcome is SubscriptionLifecycleOutcome.CHANGED
    assert decision.reason_code == "MANUAL_RENEWAL_AUTHORIZED"
    assert decision.payment_mode is SubscriptionPaymentMode.MANUAL_RENEWAL_ONLY


def test_eb05_subscription_payment_evidence_non_authority_001() -> None:
    record, event = _payment_evidence()
    decision = evaluate_subscription_lifecycle(
        _request(
            requested_action=SubscriptionLifecycleAction.RENEW,
            requested_tariff_family=SUBSCRIPTION_TARIFF_FAMILY_BASIC.value,
            idempotency_key=IdempotencyKey(value="idem-eb05-payment-001"),
            payment_records=(record,),
            payment_events=(event,),
        )
    )

    assert decision.outcome is SubscriptionLifecycleOutcome.PENDING
    assert decision.reason_code == "PAYMENT_EVIDENCE_IS_NON_AUTHORITATIVE"
    assert decision.payment_evidence_references == ("payment-ref-eb05-001", "event-ref-eb05-001")


def test_eb05_subscription_no_recurring_billing_001() -> None:
    assert [member.value for member in SubscriptionPaymentMode] == ["MANUAL_RENEWAL_ONLY"]
    assert TRIAL_SEMANTICS_SUPPORTED is False
    assert GRACE_SEMANTICS_SUPPORTED is False
    assert PRORATION_SEMANTICS_SUPPORTED is False


def test_eb05_subscription_cancelled_semantic_only_001() -> None:
    subscription = _subscription(tariff_family=SUBSCRIPTION_TARIFF_FAMILY_BASIC)
    decision = evaluate_subscription_lifecycle(
        _request(
            requested_action=SubscriptionLifecycleAction.CANCEL,
            current_subscription=subscription,
            current_tariff_family=subscription.tariff_name.value,
            requested_tariff_family=SUBSCRIPTION_TARIFF_FAMILY_BASIC.value,
            paid_access_interval=subscription.effective_interval,
            idempotency_key=IdempotencyKey(value="idem-eb05-cancel-001"),
        )
    )

    assert decision.outcome is SubscriptionLifecycleOutcome.CANCELLED
    assert decision.history_preserved is True
    assert decision.reason_code == "SUBSCRIPTION_CANCELLED"


def test_eb05_subscription_expire_semantic_only_001() -> None:
    subscription = _subscription(tariff_family=SUBSCRIPTION_TARIFF_FAMILY_BASIC)
    decision = evaluate_subscription_lifecycle(
        _request(
            requested_action=SubscriptionLifecycleAction.EXPIRE,
            current_subscription=subscription,
            current_tariff_family=subscription.tariff_name.value,
            requested_tariff_family=SUBSCRIPTION_TARIFF_FAMILY_BASIC.value,
            paid_access_interval=subscription.effective_interval,
            idempotency_key=IdempotencyKey(value="idem-eb05-expire-001"),
        )
    )

    assert decision.outcome is SubscriptionLifecycleOutcome.EXPIRED
    assert decision.reason_code == "SUBSCRIPTION_EXPIRED"


def test_eb05_subscription_idempotent_replay_same_fingerprint_001() -> None:
    subscription = _subscription(tariff_family=SUBSCRIPTION_TARIFF_FAMILY_BASIC)
    request = _request(
        requested_action=SubscriptionLifecycleAction.CHANGE,
        current_subscription=subscription,
        current_tariff_family=subscription.tariff_name.value,
        requested_tariff_family=SUBSCRIPTION_TARIFF_FAMILY_FREE.value,
        paid_access_interval=subscription.effective_interval,
        idempotency_key=IdempotencyKey(value="idem-eb05-idem-001"),
    )
    prior = SubscriptionLifecycleIdempotencyRecord(
        requested_action=SubscriptionLifecycleAction.CHANGE,
        idempotency_key=request.idempotency_key,
        request_fingerprint=compute_subscription_lifecycle_request_fingerprint(request),
        terminal_outcome=SubscriptionLifecycleOutcome.CHANGED,
    )
    replay_request = request.model_copy(update={"prior_idempotency_record": prior})
    decision = evaluate_subscription_lifecycle(replay_request)

    assert decision.outcome is SubscriptionLifecycleOutcome.REPLAYED
    assert decision.terminal_outcome is SubscriptionLifecycleOutcome.CHANGED
    assert decision.reason_code == "IDEMPOTENT_REPLAY"


def test_eb05_subscription_idempotency_mismatch_001() -> None:
    subscription = _subscription(tariff_family=SUBSCRIPTION_TARIFF_FAMILY_BASIC)
    request = _request(
        requested_action=SubscriptionLifecycleAction.CHANGE,
        current_subscription=subscription,
        current_tariff_family=subscription.tariff_name.value,
        requested_tariff_family=SUBSCRIPTION_TARIFF_FAMILY_FREE.value,
        paid_access_interval=subscription.effective_interval,
        idempotency_key=IdempotencyKey(value="idem-eb05-idem-002"),
    )
    prior = SubscriptionLifecycleIdempotencyRecord(
        requested_action=SubscriptionLifecycleAction.CHANGE,
        idempotency_key=request.idempotency_key,
        request_fingerprint=compute_subscription_lifecycle_request_fingerprint(request),
        terminal_outcome=SubscriptionLifecycleOutcome.CHANGED,
    )
    changed_request = request.model_copy(
        update={
            "requested_tariff_family": SUBSCRIPTION_TARIFF_FAMILY_BASIC.value,
            "prior_idempotency_record": prior,
        }
    )
    decision = evaluate_subscription_lifecycle(changed_request)

    assert decision.outcome is SubscriptionLifecycleOutcome.IDEMPOTENCY_MISMATCH
    assert decision.reason_code == "IDEMPOTENCY_MISMATCH"


def test_eb05_subscription_missing_idempotency_rejected_001() -> None:
    subscription = _subscription(tariff_family=SUBSCRIPTION_TARIFF_FAMILY_BASIC)
    decision = evaluate_subscription_lifecycle(
        _request(
            requested_action=SubscriptionLifecycleAction.CHANGE,
            current_subscription=subscription,
            current_tariff_family=subscription.tariff_name.value,
            requested_tariff_family=SUBSCRIPTION_TARIFF_FAMILY_FREE.value,
            paid_access_interval=subscription.effective_interval,
            idempotency_key=None,
        )
    )

    assert decision.outcome is SubscriptionLifecycleOutcome.REJECTED
    assert decision.reason_code == "IDEMPOTENCY_KEY_REQUIRED"


def test_eb05_subscription_unsupported_future_tariff_blocked_001() -> None:
    decision = evaluate_subscription_lifecycle(
        _request(
            requested_action=SubscriptionLifecycleAction.ASSIGN,
            requested_tariff_family="PREMIUM",
            idempotency_key=IdempotencyKey(value="idem-eb05-unsupported-001"),
        )
    )

    assert decision.outcome is SubscriptionLifecycleOutcome.BLOCKED
    assert decision.reason_code == "UNSUPPORTED_TARIFF_FAMILY"


def test_eb05_subscription_conflict_no_silent_allow_001() -> None:
    subscription = _subscription(tariff_family=SUBSCRIPTION_TARIFF_FAMILY_BASIC)
    decision = evaluate_subscription_lifecycle(
        _request(
            requested_action=SubscriptionLifecycleAction.ASSESS,
            current_subscription=subscription,
            current_tariff_family=SUBSCRIPTION_TARIFF_FAMILY_FREE.value,
            requested_tariff_family=SUBSCRIPTION_TARIFF_FAMILY_BASIC.value,
            paid_access_interval=subscription.effective_interval,
            requested_interval_minutes=180,
        )
    )

    assert decision.outcome is SubscriptionLifecycleOutcome.CONFLICT
    assert decision.reason_code == "CURRENT_TARIFF_CONFLICT"


def test_eb05_od010_od011_od013_remain_gated_001() -> None:
    assert FUTURE_DECISION_GATES == ("OD-010", "OD-011", "OD-013")

    request_field_names = set(SubscriptionLifecycleRequest.model_fields)
    decision_field_names = set(SubscriptionLifecycleDecision.model_fields)

    for forbidden_fragment in ("country", "monitoring_frequency", "retention"):
        assert forbidden_fragment not in request_field_names
        assert forbidden_fragment not in decision_field_names


def test_eb05_no_runtime_db_provider_imports_001() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    module_path = repo_root / "src/mayak/modules/entitlements_and_billing/subscription_lifecycle.py"
    source = module_path.read_text()
    tree = ast.parse(source)

    allowed_import_roots = {
        "__future__",
        "datetime",
        "enum",
        "mayak",
        "pydantic",
        "contracts",
        "policies",
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

    request = _request(
        requested_action=SubscriptionLifecycleAction.ASSESS,
        current_subscription=_subscription(tariff_family=SUBSCRIPTION_TARIFF_FAMILY_BASIC),
        current_tariff_family=SUBSCRIPTION_TARIFF_FAMILY_BASIC.value,
        requested_tariff_family=SUBSCRIPTION_TARIFF_FAMILY_BASIC.value,
        paid_access_interval=ACTIVE_INTERVAL,
        idempotency_key=IdempotencyKey(value="idem-eb05-import-001"),
    )
    decision = evaluate_subscription_lifecycle(request)
    synthetic_payload_text = request.model_dump_json().lower() + decision.model_dump_json().lower()

    for forbidden_fragment in ("token", "secret", "credential", "password", "card", "cvv", "pan"):
        assert forbidden_fragment not in synthetic_payload_text
