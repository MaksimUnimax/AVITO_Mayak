from __future__ import annotations

import ast
from datetime import datetime, timedelta, timezone
from pathlib import Path

from mayak.modules.entitlements_and_billing import (
    BEACON_MANAGEMENT_MODULE_LABEL,
    BEACON_MANAGEMENT_SOURCE_FACTS_OWNER_LABEL,
    BASIC_TARIFF_POLICY,
    FREE_TARIFF_POLICY,
    BeaconIntegrationCapability,
    BeaconIntegrationIdempotencyRecord,
    BeaconIntegrationOutcome,
    BeaconIntegrationRequest,
    BeaconIntegrationRequestKind,
    BeaconIntegrationRequesterModule,
    BeaconIntegrationSourceFactsOwner,
    compute_beacon_integration_request_fingerprint,
    evaluate_beacon_integration,
)
from mayak.modules.entitlements_and_billing.evaluation import (
    EffectiveEntitlementEvaluationRequest,
    evaluate_effective_entitlement,
)
from mayak.modules.entitlements_and_billing.contracts import (
    EffectiveInterval,
    EntitlementDecisionStatus,
    PaymentEvent,
    PaymentEventState,
    PaymentRecord,
    PaymentRecordState,
    Subscription,
    SubscriptionState,
)
from mayak.modules.entitlements_and_billing.subscription_lifecycle import (
    SubscriptionLifecycleAction,
    SubscriptionLifecycleActorContext,
    SubscriptionLifecycleOutcome,
    SubscriptionLifecycleRequest,
    evaluate_subscription_lifecycle,
)
from mayak.modules.entitlements_and_billing.usage_consumption import (
    ActiveBeaconSlotEvidence,
    ScanIntervalTimingEvidence,
    UsageConsumptionOutcome,
    UsageConsumptionRequest,
    UsageCounterFamily,
    compute_usage_consumption_request_fingerprint,
    evaluate_usage_consumption,
)
from mayak.platform.idempotency import IdempotencyKey

DECISION_AT = datetime(2026, 7, 8, 10, 0, tzinfo=timezone.utc)
OWN_ACCOUNT = "acct-eb07-own-001"
FOREIGN_ACCOUNT = "acct-eb07-foreign-001"
BEACON_ID = "beacon-eb07-001"
EVAL_INTERVAL = EffectiveInterval(
    starts_at=datetime(2026, 7, 8, 9, 0, tzinfo=timezone.utc),
    ends_at=datetime(2026, 8, 8, 9, 0, tzinfo=timezone.utc),
)
EVAL_GAP_INTERVAL = EffectiveInterval(
    starts_at=datetime(2026, 7, 8, 9, 0, tzinfo=timezone.utc),
    ends_at=datetime(2026, 7, 8, 10, 0, tzinfo=timezone.utc),
)


def _subscription(*, tariff_policy, status: SubscriptionState = SubscriptionState.ACTIVE) -> Subscription:
    return Subscription(
        account_id=OWN_ACCOUNT,
        subscription_id=f"subscription-{tariff_policy.tariff_name.value.lower()}-{status.value.lower()}",
        tariff_name=tariff_policy.tariff_name,
        status=status,
        effective_interval=EVAL_INTERVAL,
        source_reference=f"subscription-ref-{tariff_policy.tariff_name.value.lower()}",
    )


def _effective_decision(
    *,
    scope_account_id: str | None,
    tariff_policy,
    subscription: Subscription | None = None,
    requested_interval_minutes: int | None = 5,
    requested_capability: str = "beacon.scan",
    payment_records: tuple[PaymentRecord, ...] = (),
    payment_events: tuple[PaymentEvent, ...] = (),
):
    return evaluate_effective_entitlement(
        EffectiveEntitlementEvaluationRequest(
            target_account_id=OWN_ACCOUNT,
            scope_account_id=scope_account_id,
            requested_capability=requested_capability,
            requested_scope="beacon.scan",
            requested_interval_minutes=requested_interval_minutes,
            evaluated_at=DECISION_AT,
            subscription=subscription,
            tariff_policy=tariff_policy,
            payment_records=payment_records,
            payment_events=payment_events,
        )
    )


def _active_usage_decision(*, count: int, source_fact_count: int | None = None, tariff_policy=FREE_TARIFF_POLICY):
    request = UsageConsumptionRequest(
        account_id=OWN_ACCOUNT,
        counter_family=UsageCounterFamily.ACTIVE_BEACON_SLOT.value,
        requester_module=BEACON_MANAGEMENT_MODULE_LABEL,
        source_facts_owner=BEACON_MANAGEMENT_MODULE_LABEL,
        decision_at=DECISION_AT,
        idempotency_key=IdempotencyKey(value=f"idem-active-{count}-{source_fact_count or count}"),
        current_tariff_definition=tariff_policy,
        active_beacon_slot_evidence=ActiveBeaconSlotEvidence(
            snapshot_reference="beacon-snapshot-eb07-001",
            snapshot_active_beacon_count=count,
            source_fact_reference="beacon-source-eb07-001" if source_fact_count is not None else None,
            source_fact_active_beacon_count=source_fact_count,
        ),
    )
    return evaluate_usage_consumption(request)


def _scan_usage_decision(*, interval_minutes: int, safety_required: bool = False, tariff_policy=FREE_TARIFF_POLICY):
    request = UsageConsumptionRequest(
        account_id=OWN_ACCOUNT,
        counter_family=UsageCounterFamily.SCAN_INTERVAL_WINDOW.value,
        requester_module="Scan Orchestration",
        source_facts_owner="Scan Orchestration",
        decision_at=DECISION_AT,
        idempotency_key=IdempotencyKey(value=f"idem-scan-{interval_minutes}-{int(safety_required)}"),
        current_tariff_definition=tariff_policy,
        scan_interval_timing_evidence=ScanIntervalTimingEvidence(
            evidence_reference="scan-timing-eb07-001",
            last_scan_at=DECISION_AT,
            next_scan_at=DECISION_AT + timedelta(minutes=interval_minutes),
            source_fact_interval_minutes=interval_minutes,
        ),
        od011_safety_required=safety_required,
    )
    return evaluate_usage_consumption(request)


def _subscription_lifecycle_decision(*, status: SubscriptionState, requested_interval_minutes: int):
    subscription = _subscription(tariff_policy=BASIC_TARIFF_POLICY, status=status)
    request = SubscriptionLifecycleRequest(
        actor=SubscriptionLifecycleActorContext(
            actor_id="actor-eb07-operator-001",
            actor_category="OPERATOR",
            authorization_scope="entitlements.subscription_lifecycle",
            authorization_reference="authz-eb07-001",
            audit_reference="audit-eb07-001",
        ),
        target_account_id=OWN_ACCOUNT,
        requested_action=SubscriptionLifecycleAction.ASSESS,
        current_subscription=subscription,
        current_tariff_family=subscription.tariff_name.value,
        requested_tariff_family=subscription.tariff_name.value,
        paid_access_interval=subscription.effective_interval,
        requested_interval_minutes=requested_interval_minutes,
        decision_at=DECISION_AT,
    )
    return evaluate_subscription_lifecycle(request)


def _beacon_request(
    *,
    requested_capability: BeaconIntegrationCapability,
    entitlement_decision,
    usage_decision=None,
    subscription_lifecycle_decision=None,
    requested_active_beacon_count: int | None = None,
    requested_scan_interval_minutes: int | None = None,
    requested_geography_scope: str | None = None,
    requested_filter_edit_capability: str | None = None,
    requested_lifecycle_effect: str | None = None,
    request_kind: BeaconIntegrationRequestKind = BeaconIntegrationRequestKind.EFFECT,
    idempotency_key: IdempotencyKey | None = None,
    prior_idempotency_record: BeaconIntegrationIdempotencyRecord | None = None,
    beacon_id: str | None = BEACON_ID,
    payment_records: tuple[PaymentRecord, ...] = (),
    payment_events: tuple[PaymentEvent, ...] = (),
) -> BeaconIntegrationRequest:
    return BeaconIntegrationRequest(
        account_id=OWN_ACCOUNT,
        beacon_id=beacon_id,
        requested_capability=requested_capability,
        requested_active_beacon_count=requested_active_beacon_count,
        requested_geography_scope=requested_geography_scope,
        requested_scan_interval_minutes=requested_scan_interval_minutes,
        requested_filter_edit_capability=requested_filter_edit_capability,
        requested_lifecycle_effect=requested_lifecycle_effect,
        requester_module=BEACON_MANAGEMENT_MODULE_LABEL,
        source_facts_owner=BEACON_MANAGEMENT_SOURCE_FACTS_OWNER_LABEL,
        effective_entitlement_decision=entitlement_decision,
        usage_consumption_decision=usage_decision,
        subscription_lifecycle_decision=subscription_lifecycle_decision,
        payment_records=payment_records,
        payment_events=payment_events,
        decision_at=DECISION_AT,
        request_kind=request_kind,
        idempotency_key=idempotency_key,
        prior_idempotency_record=prior_idempotency_record,
    )


def test_eb07_beacon_integration_allowed_effective_entitlement_001() -> None:
    entitlement = _effective_decision(
        scope_account_id=OWN_ACCOUNT,
        tariff_policy=FREE_TARIFF_POLICY,
        subscription=_subscription(tariff_policy=FREE_TARIFF_POLICY),
        requested_interval_minutes=180,
    )
    usage = _active_usage_decision(count=1, tariff_policy=FREE_TARIFF_POLICY)
    decision = evaluate_beacon_integration(
        _beacon_request(
            requested_capability=BeaconIntegrationCapability.ACTIVE_BEACON_COUNT,
            entitlement_decision=entitlement,
            usage_decision=usage,
            requested_active_beacon_count=1,
        )
    )

    assert decision.outcome is BeaconIntegrationOutcome.ALLOWED
    assert decision.effective_entitlement_status is EntitlementDecisionStatus.ALLOWED
    assert decision.usage_consumption_outcome is UsageConsumptionOutcome.ACCEPTED


def test_eb07_beacon_integration_denied_blocks_effect_001() -> None:
    entitlement = _effective_decision(
        scope_account_id=FOREIGN_ACCOUNT,
        tariff_policy=FREE_TARIFF_POLICY,
        subscription=_subscription(tariff_policy=FREE_TARIFF_POLICY),
        requested_interval_minutes=180,
    )
    usage = _active_usage_decision(count=1, tariff_policy=FREE_TARIFF_POLICY)
    decision = evaluate_beacon_integration(
        _beacon_request(
            requested_capability=BeaconIntegrationCapability.ACTIVE_BEACON_COUNT,
            entitlement_decision=entitlement,
            usage_decision=usage,
            requested_active_beacon_count=1,
        )
    )

    assert decision.outcome is BeaconIntegrationOutcome.DENIED
    assert decision.reason_code == "ENTITLEMENT_DENIED"


def test_eb07_beacon_integration_ambiguous_blocks_no_guess_001() -> None:
    entitlement = _effective_decision(
        scope_account_id=OWN_ACCOUNT,
        tariff_policy=FREE_TARIFF_POLICY,
        subscription=_subscription(tariff_policy=FREE_TARIFF_POLICY),
        requested_interval_minutes=None,
    )
    usage = _active_usage_decision(count=1, tariff_policy=FREE_TARIFF_POLICY)
    decision = evaluate_beacon_integration(
        _beacon_request(
            requested_capability=BeaconIntegrationCapability.ACTIVE_BEACON_COUNT,
            entitlement_decision=entitlement,
            usage_decision=usage,
            requested_active_beacon_count=1,
        )
    )

    assert decision.outcome is BeaconIntegrationOutcome.AMBIGUOUS
    assert decision.reason_code == "ENTITLEMENT_AMBIGUOUS"


def test_eb07_beacon_integration_unsupported_blocks_001() -> None:
    entitlement = _effective_decision(
        scope_account_id=OWN_ACCOUNT,
        tariff_policy=FREE_TARIFF_POLICY,
        subscription=_subscription(tariff_policy=FREE_TARIFF_POLICY),
        requested_interval_minutes=180,
        requested_capability="beacon.unknown",
    )
    decision = evaluate_beacon_integration(
        _beacon_request(
            requested_capability=BeaconIntegrationCapability.FILTER_EDIT_CAPABILITY,
            entitlement_decision=entitlement,
            requested_filter_edit_capability="filters.edit",
        )
    )

    assert decision.outcome is BeaconIntegrationOutcome.UNSUPPORTED
    assert decision.reason_code == "ENTITLEMENT_UNSUPPORTED"


def test_eb07_beacon_integration_expired_user_choice_required_001() -> None:
    subscription_decision = _subscription_lifecycle_decision(
        status=SubscriptionState.EXPIRED,
        requested_interval_minutes=180,
    )
    decision = evaluate_beacon_integration(
        _beacon_request(
            requested_capability=BeaconIntegrationCapability.ACTIVE_BEACON_COUNT,
            entitlement_decision=_effective_decision(
                scope_account_id=OWN_ACCOUNT,
                tariff_policy=BASIC_TARIFF_POLICY,
                subscription=_subscription(tariff_policy=BASIC_TARIFF_POLICY, status=SubscriptionState.EXPIRED),
                requested_interval_minutes=180,
            ),
            subscription_lifecycle_decision=subscription_decision,
            requested_active_beacon_count=1,
        )
    )

    assert decision.outcome is BeaconIntegrationOutcome.USER_CHOICE_REQUIRED
    assert decision.subscription_lifecycle_outcome is SubscriptionLifecycleOutcome.USER_CHOICE_REQUIRED


def test_eb07_beacon_integration_expired_free_compliance_required_001() -> None:
    subscription_decision = _subscription_lifecycle_decision(
        status=SubscriptionState.EXPIRED,
        requested_interval_minutes=5,
    )
    decision = evaluate_beacon_integration(
        _beacon_request(
            requested_capability=BeaconIntegrationCapability.SCAN_INTERVAL_WINDOW,
            entitlement_decision=_effective_decision(
                scope_account_id=OWN_ACCOUNT,
                tariff_policy=BASIC_TARIFF_POLICY,
                subscription=_subscription(tariff_policy=BASIC_TARIFF_POLICY, status=SubscriptionState.EXPIRED),
                requested_interval_minutes=5,
            ),
            subscription_lifecycle_decision=subscription_decision,
            requested_scan_interval_minutes=5,
        )
    )

    assert decision.outcome is BeaconIntegrationOutcome.FREE_COMPLIANCE_REQUIRED
    assert decision.subscription_lifecycle_outcome is SubscriptionLifecycleOutcome.FREE_COMPLIANCE_REQUIRED


def test_eb07_beacon_integration_no_auto_beacon_choice_001() -> None:
    subscription_decision = _subscription_lifecycle_decision(
        status=SubscriptionState.EXPIRED,
        requested_interval_minutes=180,
    )
    decision = evaluate_beacon_integration(
        _beacon_request(
            requested_capability=BeaconIntegrationCapability.ACTIVE_BEACON_COUNT,
            entitlement_decision=_effective_decision(
                scope_account_id=OWN_ACCOUNT,
                tariff_policy=BASIC_TARIFF_POLICY,
                subscription=_subscription(tariff_policy=BASIC_TARIFF_POLICY, status=SubscriptionState.EXPIRED),
                requested_interval_minutes=180,
            ),
            subscription_lifecycle_decision=subscription_decision,
            requested_active_beacon_count=1,
            beacon_id=None,
        )
    )

    assert decision.outcome is BeaconIntegrationOutcome.USER_CHOICE_REQUIRED
    assert decision.beacon_id is None


def test_eb07_beacon_integration_active_beacon_slot_accepted_001() -> None:
    entitlement = _effective_decision(
        scope_account_id=OWN_ACCOUNT,
        tariff_policy=FREE_TARIFF_POLICY,
        subscription=_subscription(tariff_policy=FREE_TARIFF_POLICY),
        requested_interval_minutes=180,
    )
    usage = _active_usage_decision(count=1, tariff_policy=FREE_TARIFF_POLICY)
    decision = evaluate_beacon_integration(
        _beacon_request(
            requested_capability=BeaconIntegrationCapability.ACTIVE_BEACON_COUNT,
            entitlement_decision=entitlement,
            usage_decision=usage,
            requested_active_beacon_count=1,
        )
    )

    assert decision.outcome is BeaconIntegrationOutcome.ALLOWED
    assert decision.reason_code == "ACTIVE_BEACON_COUNT_ALLOWED"


def test_eb07_beacon_integration_active_beacon_slot_denied_001() -> None:
    entitlement = _effective_decision(
        scope_account_id=OWN_ACCOUNT,
        tariff_policy=FREE_TARIFF_POLICY,
        subscription=_subscription(tariff_policy=FREE_TARIFF_POLICY),
        requested_interval_minutes=180,
    )
    usage = _active_usage_decision(count=2, tariff_policy=FREE_TARIFF_POLICY)
    decision = evaluate_beacon_integration(
        _beacon_request(
            requested_capability=BeaconIntegrationCapability.ACTIVE_BEACON_COUNT,
            entitlement_decision=entitlement,
            usage_decision=usage,
            requested_active_beacon_count=2,
        )
    )

    assert decision.outcome is BeaconIntegrationOutcome.DENIED
    assert decision.reason_code == "ACTIVE_BEACON_COUNT_DENIED"


def test_eb07_beacon_integration_active_beacon_slot_conflict_blocks_001() -> None:
    entitlement = _effective_decision(
        scope_account_id=OWN_ACCOUNT,
        tariff_policy=FREE_TARIFF_POLICY,
        subscription=_subscription(tariff_policy=FREE_TARIFF_POLICY),
        requested_interval_minutes=180,
    )
    usage = _active_usage_decision(count=1, source_fact_count=2, tariff_policy=FREE_TARIFF_POLICY)
    decision = evaluate_beacon_integration(
        _beacon_request(
            requested_capability=BeaconIntegrationCapability.ACTIVE_BEACON_COUNT,
            entitlement_decision=entitlement,
            usage_decision=usage,
            requested_active_beacon_count=1,
        )
    )

    assert decision.outcome is BeaconIntegrationOutcome.AMBIGUOUS
    assert decision.reason_code == "ACTIVE_BEACON_COUNT_AMBIGUOUS"


def test_eb07_beacon_integration_scan_interval_accepted_001() -> None:
    entitlement = _effective_decision(
        scope_account_id=OWN_ACCOUNT,
        tariff_policy=FREE_TARIFF_POLICY,
        subscription=_subscription(tariff_policy=FREE_TARIFF_POLICY),
        requested_interval_minutes=180,
    )
    usage = _scan_usage_decision(interval_minutes=180, tariff_policy=FREE_TARIFF_POLICY)
    decision = evaluate_beacon_integration(
        _beacon_request(
            requested_capability=BeaconIntegrationCapability.SCAN_INTERVAL_WINDOW,
            entitlement_decision=entitlement,
            usage_decision=usage,
            requested_scan_interval_minutes=180,
        )
    )

    assert decision.outcome is BeaconIntegrationOutcome.ALLOWED
    assert decision.reason_code == "SCAN_INTERVAL_WINDOW_ALLOWED"


def test_eb07_beacon_integration_scan_interval_denied_001() -> None:
    entitlement = _effective_decision(
        scope_account_id=OWN_ACCOUNT,
        tariff_policy=FREE_TARIFF_POLICY,
        subscription=_subscription(tariff_policy=FREE_TARIFF_POLICY),
        requested_interval_minutes=180,
    )
    usage = _scan_usage_decision(interval_minutes=60, tariff_policy=FREE_TARIFF_POLICY)
    decision = evaluate_beacon_integration(
        _beacon_request(
            requested_capability=BeaconIntegrationCapability.SCAN_INTERVAL_WINDOW,
            entitlement_decision=entitlement,
            usage_decision=usage,
            requested_scan_interval_minutes=60,
        )
    )

    assert decision.outcome is BeaconIntegrationOutcome.DENIED
    assert decision.reason_code == "SCAN_INTERVAL_WINDOW_DENIED"


def test_eb07_beacon_integration_od011_safety_blocks_001() -> None:
    entitlement = _effective_decision(
        scope_account_id=OWN_ACCOUNT,
        tariff_policy=BASIC_TARIFF_POLICY,
        subscription=_subscription(tariff_policy=BASIC_TARIFF_POLICY),
        requested_interval_minutes=5,
    )
    usage = _scan_usage_decision(interval_minutes=5, safety_required=True, tariff_policy=BASIC_TARIFF_POLICY)
    decision = evaluate_beacon_integration(
        _beacon_request(
            requested_capability=BeaconIntegrationCapability.SCAN_INTERVAL_WINDOW,
            entitlement_decision=entitlement,
            usage_decision=usage,
            requested_scan_interval_minutes=5,
        )
    )

    assert decision.outcome is BeaconIntegrationOutcome.BLOCKED
    assert decision.reason_code == "SCAN_INTERVAL_WINDOW_BLOCKED"


def test_eb07_beacon_integration_od010_geography_blocked_001() -> None:
    entitlement = _effective_decision(
        scope_account_id=OWN_ACCOUNT,
        tariff_policy=BASIC_TARIFF_POLICY,
        subscription=_subscription(tariff_policy=BASIC_TARIFF_POLICY),
        requested_interval_minutes=5,
    )
    decision = evaluate_beacon_integration(
        _beacon_request(
            requested_capability=BeaconIntegrationCapability.GEOGRAPHY,
            entitlement_decision=entitlement,
            requested_geography_scope="country-wide",
        )
    )

    assert decision.outcome is BeaconIntegrationOutcome.BLOCKED
    assert decision.reason_code == "OD010_GEOGRAPHY_BLOCKED"


def test_eb07_beacon_integration_no_tariff_table_duplication_001() -> None:
    source = Path(__file__).resolve().parents[2].joinpath(
        "src/mayak/modules/entitlements_and_billing/beacon_integration.py"
    ).read_text()

    assert "FREE_TARIFF_POLICY" not in source
    assert "BASIC_TARIFF_POLICY" not in source
    assert "TariffDefinition(" not in source
    assert "price_rub=990" not in source
    assert 'billing_period_label="1 month"' not in source


def test_eb07_beacon_integration_payment_evidence_non_authority_001() -> None:
    payment_record = PaymentRecord(
        account_id=OWN_ACCOUNT,
        record_id="payment-record-eb07-001",
        payment_reference="payment-ref-eb07-001",
        provider_name="provider-placeholder",
        status=PaymentRecordState.CONFIRMED,
        observed_at=DECISION_AT,
        amount_rub=990,
        currency_code="RUB",
        source_event_reference="payment-event-eb07-001",
        provider_payload_reference="payload-ref-eb07-001",
    )
    payment_event = PaymentEvent(
        account_id=OWN_ACCOUNT,
        event_id="payment-event-eb07-001",
        event_reference="event-ref-eb07-001",
        provider_name="provider-placeholder",
        event_kind="payment.confirmed",
        status=PaymentEventState.VERIFIED_RECORDED,
        observed_at=DECISION_AT,
        source_record_reference="payment-record-eb07-001",
        provider_payload_reference="payload-ref-eb07-001",
    )
    decision = evaluate_beacon_integration(
        _beacon_request(
            requested_capability=BeaconIntegrationCapability.ACTIVE_BEACON_COUNT,
            entitlement_decision=None,
            payment_records=(payment_record,),
            payment_events=(payment_event,),
            requested_active_beacon_count=1,
        )
    )

    assert decision.outcome is BeaconIntegrationOutcome.BLOCKED
    assert decision.reason_code == "PAYMENT_IS_NOT_AUTHORITY"


def test_eb07_beacon_integration_idempotent_replay_same_fingerprint_001() -> None:
    entitlement = _effective_decision(
        scope_account_id=OWN_ACCOUNT,
        tariff_policy=FREE_TARIFF_POLICY,
        subscription=_subscription(tariff_policy=FREE_TARIFF_POLICY),
        requested_interval_minutes=180,
    )
    usage = _active_usage_decision(count=1, tariff_policy=FREE_TARIFF_POLICY)
    request = _beacon_request(
        requested_capability=BeaconIntegrationCapability.ACTIVE_BEACON_COUNT,
        entitlement_decision=entitlement,
        usage_decision=usage,
        requested_active_beacon_count=1,
        request_kind=BeaconIntegrationRequestKind.MUTATION,
        idempotency_key=IdempotencyKey(value="idem-eb07-beacon-001"),
    )
    fingerprint = compute_beacon_integration_request_fingerprint(request)
    prior = BeaconIntegrationIdempotencyRecord(
        request_kind=BeaconIntegrationRequestKind.MUTATION,
        idempotency_key=request.idempotency_key,
        request_fingerprint=fingerprint,
        terminal_outcome=BeaconIntegrationOutcome.ALLOWED,
    )
    decision = evaluate_beacon_integration(request.model_copy(update={"prior_idempotency_record": prior}))

    assert decision.outcome is BeaconIntegrationOutcome.REPLAYED
    assert decision.terminal_outcome is BeaconIntegrationOutcome.ALLOWED
    assert decision.reason_code == "IDEMPOTENT_REPLAY"


def test_eb07_beacon_integration_idempotency_mismatch_001() -> None:
    entitlement = _effective_decision(
        scope_account_id=OWN_ACCOUNT,
        tariff_policy=FREE_TARIFF_POLICY,
        subscription=_subscription(tariff_policy=FREE_TARIFF_POLICY),
        requested_interval_minutes=180,
    )
    usage = _active_usage_decision(count=1, tariff_policy=FREE_TARIFF_POLICY)
    request = _beacon_request(
        requested_capability=BeaconIntegrationCapability.ACTIVE_BEACON_COUNT,
        entitlement_decision=entitlement,
        usage_decision=usage,
        requested_active_beacon_count=1,
        request_kind=BeaconIntegrationRequestKind.MUTATION,
        idempotency_key=IdempotencyKey(value="idem-eb07-beacon-002"),
    )
    prior = BeaconIntegrationIdempotencyRecord(
        request_kind=BeaconIntegrationRequestKind.MUTATION,
        idempotency_key=request.idempotency_key,
        request_fingerprint=compute_beacon_integration_request_fingerprint(request),
        terminal_outcome=BeaconIntegrationOutcome.ALLOWED,
    )
    changed_request = request.model_copy(
        update={
            "requested_active_beacon_count": 2,
            "prior_idempotency_record": prior,
        }
    )
    decision = evaluate_beacon_integration(changed_request)

    assert decision.outcome is BeaconIntegrationOutcome.IDEMPOTENCY_MISMATCH
    assert decision.reason_code == "IDEMPOTENCY_MISMATCH"


def test_eb07_beacon_integration_missing_idempotency_rejected_001() -> None:
    entitlement = _effective_decision(
        scope_account_id=OWN_ACCOUNT,
        tariff_policy=FREE_TARIFF_POLICY,
        subscription=_subscription(tariff_policy=FREE_TARIFF_POLICY),
        requested_interval_minutes=180,
    )
    usage = _active_usage_decision(count=1, tariff_policy=FREE_TARIFF_POLICY)
    decision = evaluate_beacon_integration(
        _beacon_request(
            requested_capability=BeaconIntegrationCapability.ACTIVE_BEACON_COUNT,
            entitlement_decision=entitlement,
            usage_decision=usage,
            requested_active_beacon_count=1,
            request_kind=BeaconIntegrationRequestKind.MUTATION,
        )
    )

    assert decision.outcome is BeaconIntegrationOutcome.REJECTED
    assert decision.reason_code == "IDEMPOTENCY_KEY_REQUIRED"


def test_eb07_no_beacon_runtime_mutation_001() -> None:
    source = Path(__file__).resolve().parents[2].joinpath(
        "src/mayak/modules/entitlements_and_billing/beacon_integration.py"
    ).read_text().lower()

    forbidden_fragments = (
        "from mayak.modules.beacon_management",
        "notification_delivery",
        "scheduler",
        "sqlalchemy",
        "psycopg",
        "alembic",
        "fastapi",
        "httpx",
        "requests",
        "redis",
        "celery",
        "provider sdk",
        "yookassa",
        "tinkoff",
        "repository",
        "persistence",
        "database-backed",
    )

    assert all(fragment not in source for fragment in forbidden_fragments)


def test_eb07_od010_od011_od013_remain_gated_001() -> None:
    source = Path(__file__).resolve().parents[2].joinpath(
        "src/mayak/modules/entitlements_and_billing/beacon_integration.py"
    ).read_text().lower()

    assert "od010_geography_blocked" in source
    assert "od011" not in source
    assert "od013" not in source
    assert "retention" not in source
    assert "personal data" not in source
    assert "archive" not in source
