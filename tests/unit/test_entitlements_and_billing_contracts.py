from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from mayak.modules.entitlements_and_billing import (
    ACCOUNT_ID_OWNERSHIP_SCOPE,
    APPROVED_TARIFF_DEFINITIONS,
    BASIC_TARIFF_POLICY,
    FIXTURE_IDS,
    FREE_TARIFF_POLICY,
    FUTURE_DECISION_GATES,
    MANUAL_GRANT_AUTHORIZED,
    ManualAccessGrant,
    ManualAccessGrantState,
    PaymentEvent,
    PaymentEventState,
    PaymentRecord,
    PaymentRecordState,
    TariffDefinition,
    TariffName,
)
from mayak.modules.entitlements_and_billing.contracts import EffectiveInterval
from mayak.platform.idempotency import IdempotencyKey


def test_approved_tariff_values_are_exact_and_versioned() -> None:
    assert FREE_TARIFF_POLICY.tariff_name is TariffName.FREE
    assert FREE_TARIFF_POLICY.semantic_version == "v1"
    assert FREE_TARIFF_POLICY.price_rub == 0
    assert FREE_TARIFF_POLICY.billing_period_label is None
    assert FREE_TARIFF_POLICY.scan_interval_floor_minutes == 180
    assert FREE_TARIFF_POLICY.scan_interval_step_minutes == 180
    assert FREE_TARIFF_POLICY.active_beacon_limit == 1
    assert FREE_TARIFF_POLICY.feature_notes == "reduced features"
    assert FREE_TARIFF_POLICY.mechanism_notes == "same entitlement mechanism as paid tariff, stricter limits"

    assert BASIC_TARIFF_POLICY.tariff_name is TariffName.BASIC
    assert BASIC_TARIFF_POLICY.semantic_version == "v1"
    assert BASIC_TARIFF_POLICY.price_rub == 990
    assert BASIC_TARIFF_POLICY.billing_period_label == "1 month"
    assert BASIC_TARIFF_POLICY.scan_interval_floor_minutes == 5
    assert BASIC_TARIFF_POLICY.scan_interval_step_minutes == 5
    assert BASIC_TARIFF_POLICY.active_beacon_limit is None
    assert BASIC_TARIFF_POLICY.feature_notes is None
    assert BASIC_TARIFF_POLICY.mechanism_notes is None

    assert APPROVED_TARIFF_DEFINITIONS == (FREE_TARIFF_POLICY, BASIC_TARIFF_POLICY)
    assert FIXTURE_IDS == (
        "FX-EB-OWN-ACCOUNT-DECISION-001",
        "FX-EB-FOREIGN-ACCOUNT-FORBIDDEN-001",
        "FX-EB-NO-FABRICATED-TARIFF-001",
        "FX-EB-PAYMENT-NOT-ENTITLEMENT-001",
        "FX-EB-MANUAL-GRANT-AUTHORIZED-001",
        "FX-EB-MANUAL-GRANT-REPLAY-001",
        "FX-EB-MANUAL-GRANT-MISMATCH-001",
        "FX-EB-MANUAL-GRANT-EXPIRED-001",
        "FX-EB-LIMIT-ALLOW-001",
        "FX-EB-LIMIT-DENY-001",
        "FX-EB-REDACTION-001",
    )


def test_future_decision_gates_remain_explicit() -> None:
    assert FUTURE_DECISION_GATES == ("OD-010", "OD-011", "OD-013")


def test_tariff_definition_rejects_fabricated_defaults() -> None:
    with pytest.raises(ValidationError):
        TariffDefinition(
            tariff_name=TariffName.BASIC,
            semantic_version="v1",
            price_rub=123,
            billing_period_label="1 month",
            scan_interval_floor_minutes=5,
            scan_interval_step_minutes=5,
        )


def test_manual_access_grant_requires_actor_reason_scope_interval_idempotency_and_audit_reference() -> None:
    starts_at = datetime(2026, 7, 8, 10, 0, tzinfo=timezone.utc)
    ends_at = datetime(2026, 7, 8, 11, 0, tzinfo=timezone.utc)
    interval = EffectiveInterval(starts_at=starts_at, ends_at=ends_at)
    actor = MANUAL_GRANT_AUTHORIZED.manual_access_grant.actor if MANUAL_GRANT_AUTHORIZED.manual_access_grant else None

    grant = ManualAccessGrant(
        account_id="acct-synth-own-001",
        grant_id="manual-grant-test-001",
        actor=actor,
        reason="synthetic support case",
        scope="beacon.scan",
        capability="beacon.scan",
        effective_interval=interval,
        idempotency_key=IdempotencyKey(value="idem-test-001"),
        audit_reference="audit-test-001",
        state=ManualAccessGrantState.ACTIVE,
    )

    assert grant.ownership_scope == ACCOUNT_ID_OWNERSHIP_SCOPE
    assert grant.reason == "synthetic support case"
    assert grant.scope == "beacon.scan"
    assert grant.capability == "beacon.scan"
    assert grant.idempotency_key.value == "idem-test-001"
    assert grant.audit_reference == "audit-test-001"

    for missing_field in ("actor", "reason", "scope", "effective_interval", "idempotency_key", "audit_reference"):
        payload = grant.model_dump()
        payload.pop(missing_field)
        with pytest.raises(ValidationError):
            ManualAccessGrant.model_validate(payload)


def test_payment_records_and_events_do_not_expose_entitlement_authority_fields() -> None:
    record = PaymentRecord(
        account_id="acct-synth-own-001",
        record_id="payment-record-test-001",
        payment_reference="payment-ref-test-001",
        provider_name="provider-placeholder",
        status=PaymentRecordState.CONFIRMED,
        observed_at=datetime(2026, 7, 8, 10, 0, tzinfo=timezone.utc),
        amount_rub=990,
        currency_code="RUB",
    )
    event = PaymentEvent(
        account_id="acct-synth-own-001",
        event_id="payment-event-test-001",
        event_reference="event-ref-test-001",
        provider_name="provider-placeholder",
        event_kind="payment.confirmed",
        status=PaymentEventState.VERIFIED_RECORDED,
        observed_at=datetime(2026, 7, 8, 10, 0, tzinfo=timezone.utc),
    )

    assert "entitlement" not in type(record).model_fields
    assert "authority" not in type(record).model_fields
    assert "entitlement" not in type(event).model_fields
    assert "authority" not in type(event).model_fields
    assert not hasattr(record, "entitlement_grant")
    assert not hasattr(event, "entitlement_grant")


def test_manual_grant_fixture_uses_safe_synthetic_references() -> None:
    fixture = MANUAL_GRANT_AUTHORIZED
    payload = fixture.model_dump()
    payload_text = str(payload).lower()

    assert "token" not in payload_text
    assert "secret" not in payload_text
    assert "credential" not in payload_text
    assert "password" not in payload_text
    assert "card" not in payload_text
    assert "cvv" not in payload_text
    assert "pan" not in payload_text
