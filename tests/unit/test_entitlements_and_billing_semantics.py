from __future__ import annotations

import ast
from datetime import datetime, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

from mayak.modules.entitlements_and_billing import (
    BASIC_TARIFF_POLICY,
    FREE_TARIFF_POLICY,
    FUTURE_DECISION_GATES,
    EntitlementDecisionStatus,
    ManualAccessGrant,
    PaymentEvent,
    PaymentEventState,
    PaymentRecord,
    PaymentRecordState,
    Subscription,
    SubscriptionState,
)
from mayak.modules.entitlements_and_billing.contracts import (
    ActorContext,
    EffectiveEntitlementDecision,
    EffectiveInterval,
    EntitlementGrant,
)
from mayak.modules.entitlements_and_billing.evaluation import (
    EffectiveEntitlementEvaluationRequest,
    evaluate_effective_entitlement,
)
from mayak.platform.idempotency import IdempotencyKey

EVAL_AT = datetime(2026, 7, 8, 10, 0, tzinfo=timezone.utc)
ACTIVE_INTERVAL = EffectiveInterval(
    starts_at=datetime(2026, 7, 8, 9, 0, tzinfo=timezone.utc),
    ends_at=datetime(2026, 8, 8, 9, 0, tzinfo=timezone.utc),
)
GRANT_INTERVAL = EffectiveInterval(
    starts_at=datetime(2026, 7, 8, 9, 30, tzinfo=timezone.utc),
    ends_at=datetime(2026, 7, 8, 10, 30, tzinfo=timezone.utc),
)
OWN_ACCOUNT = "acct-eb03-own-001"
FOREIGN_ACCOUNT = "acct-eb03-foreign-001"
MANUAL_ACTOR = ActorContext(
    actor_id="actor-eb03-operator-001",
    actor_category="OPERATOR",
    authorization_scope="entitlements.manual_access",
    authorization_reference="authz-eb03-001",
)


def _subscription(
    *,
    tariff_policy,
    status: SubscriptionState = SubscriptionState.ACTIVE,
) -> Subscription:
    return Subscription(
        account_id=OWN_ACCOUNT,
        subscription_id=f"subscription-{tariff_policy.tariff_name.value.lower()}-{status.value.lower()}",
        tariff_name=tariff_policy.tariff_name,
        status=status,
        effective_interval=ACTIVE_INTERVAL,
        source_reference=f"subscription-ref-{tariff_policy.tariff_name.value.lower()}",
    )


def _manual_grant(
    *,
    scope: str = "beacon.scan",
    capability: str = "beacon.scan",
    account_id: str = OWN_ACCOUNT,
    state: str = "ACTIVE",
) -> ManualAccessGrant:
    return ManualAccessGrant(
        account_id=account_id,
        grant_id=f"manual-grant-{scope.replace('.', '-')}-{state.lower()}",
        actor=MANUAL_ACTOR,
        reason="synthetic operator approval",
        scope=scope,
        capability=capability,
        effective_interval=GRANT_INTERVAL,
        idempotency_key=IdempotencyKey(value=f"idem-{scope.replace('.', '-')}-{state.lower()}"),
        audit_reference=f"audit-{scope.replace('.', '-')}-{state.lower()}",
        state=state,  # type: ignore[arg-type]
    )


def _entitlement_grant(
    *,
    scope: str = "beacon.scan",
    capability: str = "beacon.scan",
    account_id: str = OWN_ACCOUNT,
    status: str = "ACTIVE",
) -> EntitlementGrant:
    return EntitlementGrant(
        account_id=account_id,
        grant_id=f"entitlement-grant-{scope.replace('.', '-')}-{status.lower()}",
        capability=capability,
        scope=scope,
        limit_value=None,
        status=status,
        effective_interval=GRANT_INTERVAL,
        source_kind="synthetic-contract",
        source_reference=f"grant-source-{scope.replace('.', '-')}",
    )


def _payment_evidence() -> tuple[PaymentRecord, PaymentEvent]:
    record = PaymentRecord(
        account_id=OWN_ACCOUNT,
        record_id="payment-record-eb03-001",
        payment_reference="payment-ref-eb03-001",
        provider_name="provider-placeholder",
        status=PaymentRecordState.CONFIRMED,
        observed_at=EVAL_AT,
        amount_rub=990,
        currency_code="RUB",
        source_event_reference="payment-event-eb03-001",
        provider_payload_reference="payload-ref-eb03-001",
    )
    event = PaymentEvent(
        account_id=OWN_ACCOUNT,
        event_id="payment-event-eb03-001",
        event_reference="event-ref-eb03-001",
        provider_name="provider-placeholder",
        event_kind="payment.confirmed",
        status=PaymentEventState.VERIFIED_RECORDED,
        observed_at=EVAL_AT,
        source_record_reference="payment-record-eb03-001",
        provider_payload_reference="payload-ref-eb03-001",
    )
    return record, event


def _request(
    *,
    scope_account_id: str | None,
    tariff_policy,
    subscription: Subscription | None = None,
    requested_interval_minutes: int | None = 5,
    entitlement_grants: tuple[EntitlementGrant, ...] = (),
    manual_access_grants: tuple[ManualAccessGrant, ...] = (),
    payment_records: tuple[PaymentRecord, ...] = (),
    payment_events: tuple[PaymentEvent, ...] = (),
    requested_capability: str = "beacon.scan",
    requested_scope: str = "beacon.scan",
) -> EffectiveEntitlementEvaluationRequest:
    return EffectiveEntitlementEvaluationRequest(
        target_account_id=OWN_ACCOUNT,
        scope_account_id=scope_account_id,
        requested_capability=requested_capability,
        requested_scope=requested_scope,
        requested_interval_minutes=requested_interval_minutes,
        evaluated_at=EVAL_AT,
        subscription=subscription,
        tariff_policy=tariff_policy,
        entitlement_grants=entitlement_grants,
        manual_access_grants=manual_access_grants,
        payment_records=payment_records,
        payment_events=payment_events,
    )


def test_effective_entitlement_statuses_are_approved_and_complete() -> None:
    assert [member.value for member in EntitlementDecisionStatus] == [
        "ALLOWED",
        "DENIED",
        "BLOCKED",
        "EXPIRED",
        "AMBIGUOUS",
        "UNSUPPORTED",
        "USER_CHOICE_REQUIRED",
        "FREE_COMPLIANCE_REQUIRED",
        "CONFLICT",
    ]
    assert EntitlementDecisionStatus("CONFLICT") is EntitlementDecisionStatus.CONFLICT


def test_eb03_account_scope_foreign_deny_001() -> None:
    record, event = _payment_evidence()
    decision = evaluate_effective_entitlement(
        _request(
            scope_account_id=FOREIGN_ACCOUNT,
            tariff_policy=BASIC_TARIFF_POLICY,
            subscription=_subscription(tariff_policy=BASIC_TARIFF_POLICY),
            payment_records=(record,),
            payment_events=(event,),
        )
    )

    assert decision.status is EntitlementDecisionStatus.DENIED
    assert decision.reason_code == "FOREIGN_ACCOUNT_SCOPE_DENIED"
    assert decision.source_references == ()


def test_eb03_payment_non_authority_001() -> None:
    record, event = _payment_evidence()
    decision = evaluate_effective_entitlement(
        _request(
            scope_account_id=OWN_ACCOUNT,
            tariff_policy=FREE_TARIFF_POLICY,
            subscription=None,
            payment_records=(record,),
            payment_events=(event,),
            requested_interval_minutes=5,
        )
    )

    assert decision.status is EntitlementDecisionStatus.BLOCKED
    assert decision.reason_code == "PAYMENT_IS_NOT_AUTHORITY"
    assert decision.source_references == ("payment-ref-eb03-001", "event-ref-eb03-001")


def test_eb03_active_basic_allows_basic_interval_001() -> None:
    decision = evaluate_effective_entitlement(
        _request(
            scope_account_id=OWN_ACCOUNT,
            tariff_policy=BASIC_TARIFF_POLICY,
            subscription=_subscription(tariff_policy=BASIC_TARIFF_POLICY),
            requested_interval_minutes=5,
        )
    )

    assert decision.status is EntitlementDecisionStatus.ALLOWED
    assert decision.reason_code == "BASELINE_TARIFF_ALLOWED"
    assert decision.source_references == ("subscription-basic-active", "BASIC")


def test_eb03_free_denies_too_frequent_interval_001() -> None:
    decision = evaluate_effective_entitlement(
        _request(
            scope_account_id=OWN_ACCOUNT,
            tariff_policy=FREE_TARIFF_POLICY,
            subscription=_subscription(tariff_policy=FREE_TARIFF_POLICY),
            requested_interval_minutes=5,
        )
    )

    assert decision.status is EntitlementDecisionStatus.DENIED
    assert decision.reason_code == "REQUEST_INTERVAL_NOT_ALLOWED_BY_TARIFF"


def test_eb03_expired_paid_user_choice_required_001() -> None:
    decision = evaluate_effective_entitlement(
        _request(
            scope_account_id=OWN_ACCOUNT,
            tariff_policy=BASIC_TARIFF_POLICY,
            subscription=_subscription(
                tariff_policy=BASIC_TARIFF_POLICY,
                status=SubscriptionState.EXPIRED,
            ),
            requested_interval_minutes=None,
        )
    )

    assert decision.status is EntitlementDecisionStatus.USER_CHOICE_REQUIRED
    assert decision.reason_code == "PAID_ACCESS_EXPIRED_USER_CHOICE_REQUIRED"
    assert decision.source_references == ("subscription-basic-expired", "FREE")


def test_eb03_entitlement_grant_scope_allow_001() -> None:
    decision = evaluate_effective_entitlement(
        _request(
            scope_account_id=OWN_ACCOUNT,
            tariff_policy=FREE_TARIFF_POLICY,
            subscription=_subscription(tariff_policy=FREE_TARIFF_POLICY),
            requested_interval_minutes=5,
            entitlement_grants=(
                _entitlement_grant(scope="beacon.scan", capability="beacon.scan"),
            ),
        )
    )

    assert decision.status is EntitlementDecisionStatus.ALLOWED
    assert decision.reason_code == "ENTITLEMENT_GRANT_ALLOWED"
    assert "entitlement-grant-beacon-scan-active" in decision.source_references


def test_eb03_entitlement_grant_out_of_scope_deny_001() -> None:
    decision = evaluate_effective_entitlement(
        _request(
            scope_account_id=OWN_ACCOUNT,
            tariff_policy=FREE_TARIFF_POLICY,
            subscription=_subscription(tariff_policy=FREE_TARIFF_POLICY),
            requested_interval_minutes=5,
            entitlement_grants=(
                _entitlement_grant(scope="beacon.manage", capability="beacon.manage"),
            ),
        )
    )

    assert decision.status is EntitlementDecisionStatus.DENIED
    assert decision.reason_code == "REQUEST_INTERVAL_NOT_ALLOWED_BY_TARIFF"
    assert all("entitlement-grant-beacon-manage-active" not in reference for reference in decision.source_references)


def test_eb03_manual_grant_overrides_in_scope_001() -> None:
    decision = evaluate_effective_entitlement(
        _request(
            scope_account_id=OWN_ACCOUNT,
            tariff_policy=FREE_TARIFF_POLICY,
            subscription=_subscription(tariff_policy=FREE_TARIFF_POLICY),
            requested_interval_minutes=5,
            manual_access_grants=(
                _manual_grant(scope="beacon.scan", capability="beacon.scan"),
            ),
        )
    )

    assert decision.status is EntitlementDecisionStatus.ALLOWED
    assert decision.reason_code == "MANUAL_ACCESS_GRANTED"
    assert "audit-beacon-scan-active" in decision.source_references


def test_eb03_manual_grant_out_of_scope_no_override_001() -> None:
    decision = evaluate_effective_entitlement(
        _request(
            scope_account_id=OWN_ACCOUNT,
            tariff_policy=FREE_TARIFF_POLICY,
            subscription=_subscription(tariff_policy=FREE_TARIFF_POLICY),
            requested_interval_minutes=5,
            manual_access_grants=(
                _manual_grant(scope="beacon.manage", capability="beacon.manage"),
            ),
        )
    )

    assert decision.status is EntitlementDecisionStatus.DENIED
    assert decision.reason_code == "REQUEST_INTERVAL_NOT_ALLOWED_BY_TARIFF"
    assert all("audit-beacon-manage-active" not in reference for reference in decision.source_references)


def test_eb03_manual_grant_missing_audit_rejected_001() -> None:
    grant_payload = _manual_grant().model_dump()
    grant_payload.pop("audit_reference")

    with pytest.raises(ValidationError):
        ManualAccessGrant.model_validate(grant_payload)


def test_eb03_conflict_no_silent_allow_001() -> None:
    decision = evaluate_effective_entitlement(
        _request(
            scope_account_id=OWN_ACCOUNT,
            tariff_policy=FREE_TARIFF_POLICY,
            subscription=_subscription(tariff_policy=BASIC_TARIFF_POLICY),
            requested_interval_minutes=5,
        )
    )

    assert decision.status is EntitlementDecisionStatus.CONFLICT
    assert decision.reason_code == "TARIFF_POLICY_CONFLICT"


def test_eb03_od010_od011_od013_remain_gated_001() -> None:
    assert FUTURE_DECISION_GATES == ("OD-010", "OD-011", "OD-013")

    request_field_names = set(EffectiveEntitlementEvaluationRequest.model_fields)
    decision_field_names = set(EffectiveEntitlementDecision.model_fields)

    for forbidden_fragment in ("country", "country_wide", "monitoring_frequency", "retention"):
        assert forbidden_fragment not in request_field_names
        assert forbidden_fragment not in decision_field_names


def test_eb03_no_runtime_db_provider_imports_001() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    evaluation_path = repo_root / "src/mayak/modules/entitlements_and_billing/evaluation.py"
    source = evaluation_path.read_text()
    tree = ast.parse(source)

    allowed_import_roots = {
        "__future__",
        "datetime",
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
        scope_account_id=OWN_ACCOUNT,
        tariff_policy=BASIC_TARIFF_POLICY,
        subscription=_subscription(tariff_policy=BASIC_TARIFF_POLICY),
        requested_interval_minutes=5,
    )
    decision = evaluate_effective_entitlement(request)
    synthetic_payload_text = request.model_dump_json().lower() + decision.model_dump_json().lower()

    for forbidden_fragment in ("token", "secret", "credential", "password", "card", "cvv", "pan"):
        assert forbidden_fragment not in synthetic_payload_text
