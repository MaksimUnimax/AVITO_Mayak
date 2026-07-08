"""Safe synthetic fixture definitions for Entitlements & Billing."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Final

from pydantic import BaseModel, ConfigDict, Field

from mayak.platform.idempotency import IdempotencyKey
from mayak.platform.redaction import RedactedValue, redact_sensitive_value

from .contracts import (
    ActorContext,
    EffectiveEntitlementDecision,
    EffectiveInterval,
    EntitlementDecisionStatus,
    ManualAccessGrant,
    PaymentEvent,
    PaymentEventState,
    PaymentRecord,
    PaymentRecordState,
    TariffDefinition,
)
from .policies import APPROVED_TARIFF_DEFINITIONS, FREE_TARIFF_POLICY


class SyntheticFixtureCase(BaseModel):
    """Frozen synthetic fixture record used by deterministic contract tests."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    fixture_id: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    account_id: str = Field(min_length=1)
    target_account_id: str = Field(min_length=1)
    foreign_account_id: str = Field(min_length=1)
    decision: EffectiveEntitlementDecision | None = None
    manual_access_grant: ManualAccessGrant | None = None
    payment_record: PaymentRecord | None = None
    payment_event: PaymentEvent | None = None
    tariff_definition: TariffDefinition | None = None
    approved_tariffs: tuple[TariffDefinition, ...] = Field(default_factory=tuple)
    redacted_values: tuple[RedactedValue, ...] = Field(default_factory=tuple)


_OWN_ACCOUNT = "acct-synth-own-001"
_FOREIGN_ACCOUNT = "acct-synth-foreign-001"
_EVAL_AT = datetime(2026, 7, 8, 10, 0, tzinfo=timezone.utc)
_INTERVAL = EffectiveInterval(
    starts_at=datetime(2026, 7, 8, 10, 0, tzinfo=timezone.utc),
    ends_at=datetime(2026, 8, 8, 10, 0, tzinfo=timezone.utc),
)
_MANUAL_ACTOR = ActorContext(
    actor_id="actor-synth-operator-001",
    actor_category="OPERATOR",
    authorization_scope="entitlements.manual_access",
    authorization_reference="authz-synth-001",
)
_IDEMPOTENCY_KEY = IdempotencyKey(value="idem-synth-manual-access-001")

OWN_ACCOUNT_DECISION = SyntheticFixtureCase(
    fixture_id="FX-EB-OWN-ACCOUNT-DECISION-001",
    summary="Own account entitlement decision is allowed.",
    account_id=_OWN_ACCOUNT,
    target_account_id=_OWN_ACCOUNT,
    foreign_account_id=_FOREIGN_ACCOUNT,
    decision=EffectiveEntitlementDecision(
        account_id=_OWN_ACCOUNT,
        decision_id="decision-synth-001",
        status=EntitlementDecisionStatus.ALLOWED,
        reason_code="OWN_ACCOUNT_ALLOWED",
        reason="Own-account request is inside the ownership scope.",
        evaluated_at=_EVAL_AT,
        capability="beacon.scan",
        limit_value=1,
        source_references=("source-synth-owned-account",),
        effective_interval=_INTERVAL,
    ),
)

FOREIGN_ACCOUNT_FORBIDDEN = SyntheticFixtureCase(
    fixture_id="FX-EB-FOREIGN-ACCOUNT-FORBIDDEN-001",
    summary="Foreign account access is denied.",
    account_id=_OWN_ACCOUNT,
    target_account_id=_FOREIGN_ACCOUNT,
    foreign_account_id=_FOREIGN_ACCOUNT,
    decision=EffectiveEntitlementDecision(
        account_id=_OWN_ACCOUNT,
        decision_id="decision-synth-002",
        status=EntitlementDecisionStatus.DENIED,
        reason_code="FOREIGN_ACCOUNT_FORBIDDEN",
        reason="Entitlement ownership stays bound to account_id.",
        evaluated_at=_EVAL_AT,
        capability="beacon.scan",
        limit_value=None,
        source_references=("source-synth-foreign-account",),
        effective_interval=_INTERVAL,
    ),
)

NO_FABRICATED_TARIFF = SyntheticFixtureCase(
    fixture_id="FX-EB-NO-FABRICATED-TARIFF-001",
    summary="Only approved tariff definitions are exposed.",
    account_id=_OWN_ACCOUNT,
    target_account_id=_OWN_ACCOUNT,
    foreign_account_id=_FOREIGN_ACCOUNT,
    approved_tariffs=APPROVED_TARIFF_DEFINITIONS,
)

PAYMENT_NOT_ENTITLEMENT = SyntheticFixtureCase(
    fixture_id="FX-EB-PAYMENT-NOT-ENTITLEMENT-001",
    summary="Payment evidence does not directly grant entitlement authority.",
    account_id=_OWN_ACCOUNT,
    target_account_id=_OWN_ACCOUNT,
    foreign_account_id=_FOREIGN_ACCOUNT,
    payment_record=PaymentRecord(
        account_id=_OWN_ACCOUNT,
        record_id="payment-record-synth-001",
        payment_reference="payment-ref-synth-001",
        provider_name="provider-placeholder",
        status=PaymentRecordState.CONFIRMED,
        observed_at=_EVAL_AT,
        amount_rub=990,
        currency_code="RUB",
        source_event_reference="payment-event-synth-001",
        provider_payload_reference="payload-ref-synth-001",
    ),
    payment_event=PaymentEvent(
        account_id=_OWN_ACCOUNT,
        event_id="payment-event-synth-001",
        event_reference="event-ref-synth-001",
        provider_name="provider-placeholder",
        event_kind="payment.confirmed",
        status=PaymentEventState.VERIFIED_RECORDED,
        observed_at=_EVAL_AT,
        source_record_reference="payment-record-synth-001",
        provider_payload_reference="payload-ref-synth-001",
    ),
    decision=EffectiveEntitlementDecision(
        account_id=_OWN_ACCOUNT,
        decision_id="decision-synth-003",
        status=EntitlementDecisionStatus.BLOCKED,
        reason_code="PAYMENT_IS_NOT_AUTHORITY",
        reason="Normalized payment records remain external evidence and are not entitlement authority.",
        evaluated_at=_EVAL_AT,
        capability="beacon.scan",
        limit_value=None,
        source_references=("payment-record-synth-001", "payment-event-synth-001"),
    ),
)

MANUAL_GRANT_AUTHORIZED = SyntheticFixtureCase(
    fixture_id="FX-EB-MANUAL-GRANT-AUTHORIZED-001",
    summary="Manual grant contains all required protected references.",
    account_id=_OWN_ACCOUNT,
    target_account_id=_OWN_ACCOUNT,
    foreign_account_id=_FOREIGN_ACCOUNT,
    manual_access_grant=ManualAccessGrant(
        account_id=_OWN_ACCOUNT,
        grant_id="manual-grant-synth-001",
        actor=_MANUAL_ACTOR,
        reason="Operator approved temporary access for support verification.",
        scope="beacon.scan",
        capability="beacon.scan",
        effective_interval=_INTERVAL,
        idempotency_key=_IDEMPOTENCY_KEY,
        audit_reference="audit-ref-synth-001",
    ),
)

MANUAL_GRANT_REPLAY = SyntheticFixtureCase(
    fixture_id="FX-EB-MANUAL-GRANT-REPLAY-001",
    summary="Replay with the same idempotency key returns the first outcome.",
    account_id=_OWN_ACCOUNT,
    target_account_id=_OWN_ACCOUNT,
    foreign_account_id=_FOREIGN_ACCOUNT,
    manual_access_grant=ManualAccessGrant(
        account_id=_OWN_ACCOUNT,
        grant_id="manual-grant-synth-001",
        actor=_MANUAL_ACTOR,
        reason="Operator approved temporary access for support verification.",
        scope="beacon.scan",
        capability="beacon.scan",
        effective_interval=_INTERVAL,
        idempotency_key=_IDEMPOTENCY_KEY,
        audit_reference="audit-ref-synth-001",
    ),
)

MANUAL_GRANT_MISMATCH = SyntheticFixtureCase(
    fixture_id="FX-EB-MANUAL-GRANT-MISMATCH-001",
    summary="Same idempotency key with a different fingerprint is a mismatch.",
    account_id=_OWN_ACCOUNT,
    target_account_id=_OWN_ACCOUNT,
    foreign_account_id=_FOREIGN_ACCOUNT,
    manual_access_grant=ManualAccessGrant(
        account_id=_OWN_ACCOUNT,
        grant_id="manual-grant-synth-002",
        actor=_MANUAL_ACTOR,
        reason="Operator approved a changed scope that must not replay silently.",
        scope="beacon.manage",
        capability="beacon.manage",
        effective_interval=_INTERVAL,
        idempotency_key=IdempotencyKey(value="idem-synth-manual-access-001"),
        audit_reference="audit-ref-synth-002",
        state="CONFLICT",
    ),
)

MANUAL_GRANT_EXPIRED = SyntheticFixtureCase(
    fixture_id="FX-EB-MANUAL-GRANT-EXPIRED-001",
    summary="Expired manual access is represented as an expired grant.",
    account_id=_OWN_ACCOUNT,
    target_account_id=_OWN_ACCOUNT,
    foreign_account_id=_FOREIGN_ACCOUNT,
    manual_access_grant=ManualAccessGrant(
        account_id=_OWN_ACCOUNT,
        grant_id="manual-grant-synth-003",
        actor=_MANUAL_ACTOR,
        reason="Operator temporary access window closed.",
        scope="beacon.scan",
        capability="beacon.scan",
        effective_interval=EffectiveInterval(
            starts_at=datetime(2026, 6, 1, 10, 0, tzinfo=timezone.utc),
            ends_at=datetime(2026, 6, 2, 10, 0, tzinfo=timezone.utc),
        ),
        idempotency_key=IdempotencyKey(value="idem-synth-manual-access-003"),
        audit_reference="audit-ref-synth-003",
        state="EXPIRED",
    ),
)

LIMIT_ALLOW = SyntheticFixtureCase(
    fixture_id="FX-EB-LIMIT-ALLOW-001",
    summary="Limit checks allow values inside the approved policy range.",
    account_id=_OWN_ACCOUNT,
    target_account_id=_OWN_ACCOUNT,
    foreign_account_id=_FOREIGN_ACCOUNT,
    decision=EffectiveEntitlementDecision(
        account_id=_OWN_ACCOUNT,
        decision_id="decision-synth-004",
        status=EntitlementDecisionStatus.ALLOWED,
        reason_code="LIMIT_WITHIN_POLICY",
        reason="Requested limit is within the approved policy envelope.",
        evaluated_at=_EVAL_AT,
        capability="beacon.interval",
        limit_value=5,
        source_references=("tariff-basic-policy-v1",),
        effective_interval=_INTERVAL,
    ),
)

LIMIT_DENY = SyntheticFixtureCase(
    fixture_id="FX-EB-LIMIT-DENY-001",
    summary="Limit checks deny values outside the approved policy range.",
    account_id=_OWN_ACCOUNT,
    target_account_id=_OWN_ACCOUNT,
    foreign_account_id=_FOREIGN_ACCOUNT,
    decision=EffectiveEntitlementDecision(
        account_id=_OWN_ACCOUNT,
        decision_id="decision-synth-005",
        status=EntitlementDecisionStatus.DENIED,
        reason_code="LIMIT_EXCEEDS_POLICY",
        reason="Requested limit exceeds the approved policy envelope.",
        evaluated_at=_EVAL_AT,
        capability="beacon.interval",
        limit_value=999,
        source_references=("tariff-basic-policy-v1",),
        effective_interval=_INTERVAL,
    ),
)

REDACTION = SyntheticFixtureCase(
    fixture_id="FX-EB-REDACTION-001",
    summary="Sensitive placeholder inputs remain redacted.",
    account_id=_OWN_ACCOUNT,
    target_account_id=_OWN_ACCOUNT,
    foreign_account_id=_FOREIGN_ACCOUNT,
    redacted_values=(redact_sensitive_value("synthetic-secret"),),
)

SYNTHETIC_FIXTURE_CASES: Final[tuple[SyntheticFixtureCase, ...]] = (
    OWN_ACCOUNT_DECISION,
    FOREIGN_ACCOUNT_FORBIDDEN,
    NO_FABRICATED_TARIFF,
    PAYMENT_NOT_ENTITLEMENT,
    MANUAL_GRANT_AUTHORIZED,
    MANUAL_GRANT_REPLAY,
    MANUAL_GRANT_MISMATCH,
    MANUAL_GRANT_EXPIRED,
    LIMIT_ALLOW,
    LIMIT_DENY,
    REDACTION,
)

SYNTHETIC_FIXTURE_BY_ID: Final[dict[str, SyntheticFixtureCase]] = {
    fixture.fixture_id: fixture for fixture in SYNTHETIC_FIXTURE_CASES
}

FIXTURE_IDS: Final[tuple[str, ...]] = tuple(fixture.fixture_id for fixture in SYNTHETIC_FIXTURE_CASES)

__all__ = [
    "FIXTURE_IDS",
    "FOREIGN_ACCOUNT_FORBIDDEN",
    "LIMIT_ALLOW",
    "LIMIT_DENY",
    "MANUAL_GRANT_AUTHORIZED",
    "MANUAL_GRANT_EXPIRED",
    "MANUAL_GRANT_MISMATCH",
    "MANUAL_GRANT_REPLAY",
    "NO_FABRICATED_TARIFF",
    "OWN_ACCOUNT_DECISION",
    "PAYMENT_NOT_ENTITLEMENT",
    "REDACTION",
    "SYNTHETIC_FIXTURE_BY_ID",
    "SYNTHETIC_FIXTURE_CASES",
    "SyntheticFixtureCase",
]
