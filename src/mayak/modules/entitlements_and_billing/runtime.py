"""PostgreSQL-backed RF-12 runtime.

The module owns only the six Module 03 tables.  Callers own the transaction:
these methods never commit, rollback, or touch foreign-module tables.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from pathlib import Path
from typing import Any, Protocol
from uuid import UUID, uuid4, uuid5

import httpx
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from mayak.contracts.results import CommonOutcome, Result
from mayak.persistence.idempotency import PostgresTerminalIdempotencyRepository
from mayak.persistence.metadata import metadata
from mayak.platform.idempotency import IdempotencyFingerprint, IdempotencyKey, IdempotencyScope

from .contracts import EntitlementDecisionStatus, TariffName
from .policies import BASIC_TARIFF_POLICY, FREE_TARIFF_POLICY

_TARIFFS = metadata.tables["mayak.entitlement_tariff_definitions"]
_GRANTS = metadata.tables["mayak.entitlement_access_grants"]
_USAGE = metadata.tables["mayak.entitlement_usage_counters"]
_PAYMENTS = metadata.tables["mayak.billing_payment_records"]
_OPERATIONS = metadata.tables["mayak.billing_payment_operations"]
_RECONCILIATIONS = metadata.tables["mayak.billing_reconciliations"]
_AUDIT = metadata.tables["mayak.platform_audit_entries"]
_SCOPE = IdempotencyScope(value="entitlements_and_billing")
_TARIFF_NAMESPACE = UUID("b7c25d70-1c9b-4d29-a6b9-0a0d6b0a4f12")


class RuntimeState(StrEnum):
    RECORDED = "RECORDED"
    REPLAYED = "REPLAYED"
    MISMATCH = "MISMATCH"
    UNAUTHORIZED = "UNAUTHORIZED"
    CONFLICT = "CONFLICT"
    REJECTED = "REJECTED"
    RECONCILE_REQUIRED = "RECONCILE_REQUIRED"
    BLOCKED = "BLOCKED"


class PaymentState(StrEnum):
    RECORDED = "RECORDED"
    DUPLICATE = "DUPLICATE"
    REJECTED = "REJECTED"
    AMBIGUOUS = "AMBIGUOUS"
    RECONCILE_REQUIRED = "RECONCILE_REQUIRED"
    CONFIRMED = "CONFIRMED"
    UNRESOLVED = "UNRESOLVED"
    MANUAL_REVIEW_REQUIRED = "MANUAL_REVIEW_REQUIRED"


class RefundState(StrEnum):
    MANUAL_REFUND_REVIEW_REQUIRED = "MANUAL_REFUND_REVIEW_REQUIRED"
    MANUAL_REFUND_REFERENCED = "MANUAL_REFUND_REFERENCED"
    AUTOMATIC_REFUND_BLOCKED = "AUTOMATIC_REFUND_BLOCKED"
    PROVIDER_REFUND_API_BLOCKED = "PROVIDER_REFUND_API_BLOCKED"
    REFUND_REJECTED = "REFUND_REJECTED"
    REFUND_REPLAYED = "REFUND_REPLAYED"
    REFUND_IDEMPOTENCY_MISMATCH = "REFUND_IDEMPOTENCY_MISMATCH"


class AuthorityFacts(BaseModel):
    """Verified authority supplied by Identity; never constructed from UI claims."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    actor_id: UUID
    account_id: UUID
    capabilities: frozenset[str] = frozenset()
    scope: str = Field(min_length=1)
    authorization_reference: str = Field(min_length=1)
    audit_reference: str = Field(min_length=1)


class CommandResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    state: RuntimeState
    reason_code: str
    resource_id: UUID | None = None
    audit_reference: str
    terminal: bool = True


class EffectiveEntitlement(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: EntitlementDecisionStatus
    account_id: UUID
    tariff: TariffName | None = None
    grant_id: UUID | None = None
    provenance: tuple[str, ...] = ()
    free_compliance_required: bool = False
    user_choice_required: bool = False
    frozen_at_beacon_boundary: bool = False


class NormalizedPaymentEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    account_id: UUID
    provider_code: str = Field(min_length=1, max_length=64)
    external_payment_id: str = Field(min_length=1, max_length=255)
    amount_minor: int = Field(ge=0)
    currency: str = Field(min_length=3, max_length=3)
    state: PaymentState
    observed_at: datetime
    safe_metadata: dict[str, str] = Field(default_factory=dict)


class VerifiedIdentityPort(Protocol):
    def authority(
        self, session: Session, actor_reference: str, account_id: UUID
    ) -> AuthorityFacts: ...


class FakeVerifiedIdentityPort:
    """Deterministic acceptance-only authority port."""

    def __init__(self, facts: AuthorityFacts) -> None:
        self.facts = facts

    def authority(self, session: Session, actor_reference: str, account_id: UUID) -> AuthorityFacts:
        if (
            account_id != self.facts.account_id
            or actor_reference != self.facts.authorization_reference
        ):
            raise PermissionError("verified authority unavailable")
        return self.facts


def _now() -> datetime:
    return datetime.now(UTC)


def _fingerprint(value: Any) -> IdempotencyFingerprint:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    return IdempotencyFingerprint(value=hashlib.sha256(payload).hexdigest())


def _key(value: str | IdempotencyKey) -> IdempotencyKey:
    return value if isinstance(value, IdempotencyKey) else IdempotencyKey(value=value)


def _safe_metadata(values: dict[str, str] | None) -> dict[str, str]:
    values = values or {}
    if len(json.dumps(values, separators=(",", ":"), ensure_ascii=True).encode()) > 8192:
        raise ValueError("safe metadata exceeds bounded size")
    if any(not isinstance(key, str) or not isinstance(value, str) for key, value in values.items()):
        raise ValueError("safe metadata must contain strings")
    forbidden = {"authorization", "token", "secret", "password", "pan", "cvv", "cookie"}
    if any(any(word in key.lower() for word in forbidden) for key in values):
        raise ValueError("sensitive metadata key is forbidden")
    return dict(values)


def _tariff_id(code: str, version: int) -> UUID:
    return uuid5(_TARIFF_NAMESPACE, f"{code}:{version}")


def _policy_values(code: TariffName) -> tuple[int, int, int, str]:
    policy = FREE_TARIFF_POLICY if code is TariffName.FREE else BASIC_TARIFF_POLICY
    return (
        policy.price_rub * 100,
        policy.scan_interval_floor_minutes * 60,
        policy.scan_interval_step_minutes * 60,
        "RUB",
    )


def _authorized(authority: AuthorityFacts, capability: str) -> bool:
    return capability in authority.capabilities and authority.scope == "account_id"


def _audit(
    session: Session,
    authority: AuthorityFacts,
    *,
    action: str,
    target: UUID | None,
    reason: str,
) -> None:
    """Append a bounded Platform audit record without owning the transaction."""
    session.execute(
        _AUDIT.insert().values(
            id=uuid4(),
            actor_account_id=authority.actor_id,
            action_code=action,
            target_type="entitlements_and_billing",
            target_id=str(target) if target is not None else None,
            reason=reason[:512],
            correlation_id=authority.audit_reference,
            details={
                "module": "entitlements_and_billing",
                "authorization_reference": authority.authorization_reference,
            },
            created_at=_now(),
        )
    )


class EntitlementsBillingRuntime:
    """Production-shaped Module 03 commands and effective-state reads."""

    def __init__(self, identity: VerifiedIdentityPort | None = None) -> None:
        self.identity = identity
        self.idempotency = PostgresTerminalIdempotencyRepository()

    def _terminal(
        self, session: Session, key: str | IdempotencyKey, fingerprint: IdempotencyFingerprint
    ) -> tuple[RuntimeState, UUID | None]:
        resolution = self.idempotency.evaluate(
            session, scope=_SCOPE, key=_key(key), fingerprint=fingerprint, now=_now()
        )
        if resolution.decision.decision.value == "REPLAY_TERMINAL":
            details = resolution.outcome.details if resolution.outcome else ()
            return RuntimeState.REPLAYED, UUID(details[0]) if details else None
        if resolution.decision.decision.value == "MISMATCH":
            return RuntimeState.MISMATCH, None
        return RuntimeState.RECORDED, None

    def _record_terminal(
        self,
        session: Session,
        key: str | IdempotencyKey,
        fingerprint: IdempotencyFingerprint,
        result: CommandResult,
    ) -> None:
        now = _now()
        self.idempotency.record_terminal(
            session,
            record_id=uuid4(),
            scope=_SCOPE,
            key=_key(key),
            fingerprint=fingerprint,
            outcome=CommonOutcome(
                result=Result.SUCCEEDED,
                reason_code=result.reason_code,
                details=((str(result.resource_id),) if result.resource_id else ()),
            ),
            created_at=now,
            expires_at=now + timedelta(days=30),
            now=now,
        )

    @staticmethod
    def _require_authority(
        authority: AuthorityFacts, capability: str, target: UUID
    ) -> CommandResult | None:
        if authority.account_id != target or not _authorized(authority, capability):
            return CommandResult(
                state=RuntimeState.UNAUTHORIZED,
                reason_code="VERIFIED_CAPABILITY_REQUIRED",
                audit_reference=authority.audit_reference,
            )
        return None

    def bootstrap_tariffs(
        self,
        session: Session,
        authority: AuthorityFacts,
        idempotency_key: str,
        *,
        effective_at: datetime,
    ) -> CommandResult:
        denied = self._require_authority(
            authority, "ENTITLEMENTS_TARIFF_ADMIN", authority.account_id
        )
        if denied:
            return denied
        fingerprint = _fingerprint(("bootstrap", str(effective_at)))
        state, resource = self._terminal(session, idempotency_key, fingerprint)
        if state is RuntimeState.REPLAYED:
            return CommandResult(
                state=state,
                reason_code="IDEMPOTENCY_REPLAY",
                resource_id=resource,
                audit_reference=authority.audit_reference,
            )
        if state is RuntimeState.MISMATCH:
            return CommandResult(
                state=state,
                reason_code="IDEMPOTENCY_FINGERPRINT_MISMATCH",
                audit_reference=authority.audit_reference,
            )
        for code in (TariffName.FREE, TariffName.BASIC):
            price, floor, step, currency = _policy_values(code)
            tariff_id = _tariff_id(code.value, 1)
            existing = (
                session.execute(
                    select(
                        _TARIFFS.c.id,
                        _TARIFFS.c.price_minor,
                        _TARIFFS.c.min_interval_seconds,
                        _TARIFFS.c.step_seconds,
                    ).where(_TARIFFS.c.code == code.value, _TARIFFS.c.version == 1)
                )
                .mappings()
                .one_or_none()
            )
            if existing is not None and tuple(existing.values())[1:] != (price, floor, step):
                return CommandResult(
                    state=RuntimeState.CONFLICT,
                    reason_code="TARIFF_AUTHORITY_CONFLICT",
                    audit_reference=authority.audit_reference,
                )
            if existing is None:
                session.execute(
                    _TARIFFS.insert().values(
                        id=tariff_id,
                        code=code.value,
                        version=1,
                        price_minor=price,
                        currency=currency,
                        min_interval_seconds=floor,
                        step_seconds=step,
                        active_from=effective_at,
                        active_until=None,
                        created_at=effective_at,
                    )
                )
        _audit(
            session,
            authority,
            action="TARIFF_BOOTSTRAP",
            target=None,
            reason="tariff authority bootstrap",
        )
        result = CommandResult(
            state=RuntimeState.RECORDED,
            reason_code="TARIFFS_BOOTSTRAPPED",
            resource_id=_tariff_id("BASIC", 1),
            audit_reference=authority.audit_reference,
        )
        self._record_terminal(session, idempotency_key, fingerprint, result)
        return result

    def _tariff(self, session: Session, code: TariffName, at: datetime) -> Any:
        rows = (
            session.execute(
                select(_TARIFFS)
                .where(
                    _TARIFFS.c.code == code.value,
                    _TARIFFS.c.active_from <= at,
                    (_TARIFFS.c.active_until.is_(None) | (_TARIFFS.c.active_until > at)),
                )
                .order_by(_TARIFFS.c.version.desc())
            )
            .mappings()
            .all()
        )
        if len(rows) != 1:
            raise ValueError("tariff authority is missing or conflicting")
        return rows[0]

    def assign_access(
        self,
        session: Session,
        authority: AuthorityFacts,
        *,
        tariff: TariffName,
        starts_at: datetime,
        ends_at: datetime,
        reason: str,
        idempotency_key: str,
    ) -> CommandResult:
        denied = self._require_authority(
            authority, "ENTITLEMENTS_TARIFF_ASSIGN_ADMIN", authority.account_id
        )
        if denied:
            return denied
        if ends_at <= starts_at or not reason.strip():
            raise ValueError("closed interval and reason required")
        fingerprint = _fingerprint(
            ("assign", str(authority.account_id), tariff.value, starts_at, ends_at, reason)
        )
        state, resource = self._terminal(session, idempotency_key, fingerprint)
        if state is RuntimeState.REPLAYED:
            return CommandResult(
                state=state,
                reason_code="IDEMPOTENCY_REPLAY",
                resource_id=resource,
                audit_reference=authority.audit_reference,
            )
        if state is RuntimeState.MISMATCH:
            return CommandResult(
                state=state,
                reason_code="IDEMPOTENCY_FINGERPRINT_MISMATCH",
                audit_reference=authority.audit_reference,
            )
        tariff_row = self._tariff(session, tariff, starts_at)
        grant_id = uuid4()
        session.execute(
            _GRANTS.insert().values(
                id=grant_id,
                account_id=authority.account_id,
                tariff_id=tariff_row.id,
                source_code="ASSIGN_ACCESS",
                valid_from=starts_at,
                valid_until=ends_at,
                state="ACTIVE",
                created_at=_now(),
                updated_at=_now(),
                row_version=1,
            )
        )
        _audit(session, authority, action="ACCESS_ASSIGN", target=grant_id, reason=reason)
        result = CommandResult(
            state=RuntimeState.RECORDED,
            reason_code="ACCESS_ASSIGNED",
            resource_id=grant_id,
            audit_reference=authority.audit_reference,
        )
        self._record_terminal(session, idempotency_key, fingerprint, result)
        return result

    def manual_renewal(
        self,
        session: Session,
        authority: AuthorityFacts,
        *,
        starts_at: datetime,
        ends_at: datetime,
        idempotency_key: str,
        reason: str,
    ) -> CommandResult:
        return self.assign_access(
            session,
            authority,
            tariff=TariffName.BASIC,
            starts_at=starts_at,
            ends_at=ends_at,
            reason=reason,
            idempotency_key=idempotency_key,
        )

    def revoke_access(
        self,
        session: Session,
        authority: AuthorityFacts,
        *,
        grant_id: UUID,
        idempotency_key: str,
        reason: str,
    ) -> CommandResult:
        denied = self._require_authority(
            authority, "ENTITLEMENTS_TARIFF_ASSIGN_ADMIN", authority.account_id
        )
        if denied:
            return denied
        fingerprint = _fingerprint(("revoke", str(grant_id), reason))
        state, resource = self._terminal(session, idempotency_key, fingerprint)
        if state is not RuntimeState.RECORDED:
            return CommandResult(
                state=state,
                reason_code="IDEMPOTENCY_REPLAY"
                if state is RuntimeState.REPLAYED
                else "IDEMPOTENCY_FINGERPRINT_MISMATCH",
                resource_id=resource,
                audit_reference=authority.audit_reference,
            )
        update_result = session.execute(
            update(_GRANTS)
            .where(
                _GRANTS.c.id == grant_id,
                _GRANTS.c.account_id == authority.account_id,
                _GRANTS.c.state == "ACTIVE",
            )
            .values(state="REVOKED", updated_at=_now(), row_version=_GRANTS.c.row_version + 1)
        )
        changed = int(getattr(update_result, "rowcount", 0) or 0)
        if changed != 1:
            return CommandResult(
                state=RuntimeState.REJECTED,
                reason_code="GRANT_NOT_ACTIVE_OR_NOT_OWNED",
                audit_reference=authority.audit_reference,
            )
        _audit(session, authority, action="ACCESS_REVOKE", target=grant_id, reason=reason)
        result = CommandResult(
            state=RuntimeState.RECORDED,
            reason_code="ACCESS_REVOKED",
            resource_id=grant_id,
            audit_reference=authority.audit_reference,
        )
        self._record_terminal(session, idempotency_key, fingerprint, result)
        return result

    def manual_access_create(
        self,
        session: Session,
        authority: AuthorityFacts,
        *,
        starts_at: datetime,
        ends_at: datetime,
        idempotency_key: str,
        reason: str,
    ) -> CommandResult:
        if not _authorized(authority, "ENTITLEMENTS_MANUAL_ACCESS_ADMIN"):
            return CommandResult(
                state=RuntimeState.UNAUTHORIZED,
                reason_code="MANUAL_ACCESS_CAPABILITY_REQUIRED",
                audit_reference=authority.audit_reference,
            )
        return self.assign_access(
            session,
            authority.model_copy(
                update={
                    "capabilities": authority.capabilities | {"ENTITLEMENTS_TARIFF_ASSIGN_ADMIN"}
                }
            ),
            tariff=TariffName.BASIC,
            starts_at=starts_at,
            ends_at=ends_at,
            reason=reason,
            idempotency_key=idempotency_key,
        )

    def manual_access_revoke(
        self,
        session: Session,
        authority: AuthorityFacts,
        *,
        grant_id: UUID,
        idempotency_key: str,
        reason: str,
    ) -> CommandResult:
        if not _authorized(authority, "ENTITLEMENTS_MANUAL_ACCESS_ADMIN"):
            return CommandResult(
                state=RuntimeState.UNAUTHORIZED,
                reason_code="MANUAL_ACCESS_CAPABILITY_REQUIRED",
                audit_reference=authority.audit_reference,
            )
        return self.revoke_access(
            session,
            authority.model_copy(
                update={
                    "capabilities": authority.capabilities | {"ENTITLEMENTS_TARIFF_ASSIGN_ADMIN"}
                }
            ),
            grant_id=grant_id,
            idempotency_key=idempotency_key,
            reason=reason,
        )

    def evaluate_effective(
        self,
        session: Session,
        account_id: UUID,
        *,
        at: datetime,
        active_beacon_count: int | None = None,
        interval_minutes: int | None = None,
    ) -> EffectiveEntitlement:
        rows = (
            session.execute(
                select(_GRANTS, _TARIFFS.c.code)
                .join(_TARIFFS, _TARIFFS.c.id == _GRANTS.c.tariff_id)
                .where(
                    _GRANTS.c.account_id == account_id,
                    _GRANTS.c.state == "ACTIVE",
                    _GRANTS.c.valid_from <= at,
                )
                .order_by(_GRANTS.c.valid_until.desc())
            )
            .mappings()
            .all()
        )
        if not rows:
            return EffectiveEntitlement(
                status=EntitlementDecisionStatus.DENIED,
                account_id=account_id,
                provenance=("NO_EFFECTIVE_ACCESS",),
            )
        row = rows[0]
        if row["valid_until"] <= at:
            return EffectiveEntitlement(
                status=EntitlementDecisionStatus.EXPIRED,
                account_id=account_id,
                tariff=TariffName(row["code"]),
                grant_id=row["id"],
                provenance=("PAID_ACCESS_EXPIRED", "FREE_ONLY_SEMANTICS"),
                free_compliance_required=True,
                frozen_at_beacon_boundary=True,
            )
        tariff = TariffName(row["code"])
        if (
            tariff is TariffName.FREE
            and active_beacon_count is not None
            and active_beacon_count > 1
        ):
            return EffectiveEntitlement(
                status=EntitlementDecisionStatus.USER_CHOICE_REQUIRED,
                account_id=account_id,
                tariff=tariff,
                grant_id=row["id"],
                provenance=("FREE_ONE_BEACON_LIMIT", "NO_AUTOMATIC_SELECTION"),
                user_choice_required=True,
            )
        policy = FREE_TARIFF_POLICY if tariff is TariffName.FREE else BASIC_TARIFF_POLICY
        if interval_minutes is not None and (
            interval_minutes < policy.scan_interval_floor_minutes
            or (interval_minutes - policy.scan_interval_floor_minutes)
            % policy.scan_interval_step_minutes
        ):
            return EffectiveEntitlement(
                status=EntitlementDecisionStatus.DENIED,
                account_id=account_id,
                tariff=tariff,
                grant_id=row["id"],
                provenance=("SCAN_INTERVAL_POLICY_REJECTED",),
            )
        return EffectiveEntitlement(
            status=EntitlementDecisionStatus.ALLOWED,
            account_id=account_id,
            tariff=tariff,
            grant_id=row["id"],
            provenance=("PERSISTED_TARIFF", "EFFECTIVE_ACCESS_GRANT"),
        )

    def record_payment_evidence(
        self,
        session: Session,
        evidence: NormalizedPaymentEvidence,
        *,
        idempotency_key: str,
        authority: AuthorityFacts,
    ) -> CommandResult:
        if authority.account_id != evidence.account_id:
            return CommandResult(
                state=RuntimeState.UNAUTHORIZED,
                reason_code="ACCOUNT_SCOPE_MISMATCH",
                audit_reference=authority.audit_reference,
            )
        safe = _safe_metadata(evidence.safe_metadata)
        existing = session.execute(
            select(_PAYMENTS.c.id).where(
                _PAYMENTS.c.provider_code == evidence.provider_code,
                _PAYMENTS.c.external_payment_id == evidence.external_payment_id,
            )
        ).scalar_one_or_none()
        if existing is not None:
            return CommandResult(
                state=RuntimeState.RECORDED,
                reason_code="DUPLICATE_PAYMENT_EVIDENCE",
                resource_id=existing,
                audit_reference=authority.audit_reference,
            )
        payment_id = uuid4()
        session.execute(
            _PAYMENTS.insert().values(
                id=payment_id,
                account_id=evidence.account_id,
                provider_code=evidence.provider_code,
                external_payment_id=evidence.external_payment_id,
                amount_minor=evidence.amount_minor,
                currency=evidence.currency.upper(),
                state=evidence.state.value,
                observed_at=evidence.observed_at,
                safe_metadata=safe,
                created_at=_now(),
                updated_at=_now(),
                row_version=1,
            )
        )
        _audit(
            session,
            authority,
            action="PAYMENT_EVIDENCE_RECORD",
            target=payment_id,
            reason="normalized payment evidence",
        )
        return CommandResult(
            state=RuntimeState.RECORDED,
            reason_code="PAYMENT_EVIDENCE_RECORDED",
            resource_id=payment_id,
            audit_reference=authority.audit_reference,
        )

    def reconcile_payment(
        self,
        session: Session,
        authority: AuthorityFacts,
        *,
        payment_id: UUID,
        state: PaymentState,
        idempotency_key: str,
        observed_at: datetime,
    ) -> CommandResult:
        row = (
            session.execute(
                select(_PAYMENTS).where(
                    _PAYMENTS.c.id == payment_id, _PAYMENTS.c.account_id == authority.account_id
                )
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            return CommandResult(
                state=RuntimeState.REJECTED,
                reason_code="PAYMENT_NOT_FOUND",
                audit_reference=authority.audit_reference,
            )
        if state in {PaymentState.AMBIGUOUS, PaymentState.RECONCILE_REQUIRED}:
            return CommandResult(
                state=RuntimeState.RECONCILE_REQUIRED,
                reason_code="UNKNOWN_EFFECT_REQUIRES_RECONCILIATION",
                resource_id=payment_id,
                audit_reference=authority.audit_reference,
            )
        session.execute(
            update(_PAYMENTS)
            .where(_PAYMENTS.c.id == payment_id)
            .values(
                state=state.value,
                observed_at=observed_at,
                updated_at=_now(),
                row_version=_PAYMENTS.c.row_version + 1,
            )
        )
        recon_id = uuid4()
        session.execute(
            _RECONCILIATIONS.insert().values(
                id=recon_id,
                payment_record_id=payment_id,
                operation_id=None,
                state=state.value,
                due_at=observed_at,
                resolved_at=observed_at,
                safe_metadata={"evidence_only": "true"},
                created_at=observed_at,
                row_version=1,
            )
        )
        _audit(
            session,
            authority,
            action="PAYMENT_RECONCILE",
            target=recon_id,
            reason="reconciliation evidence only",
        )
        return CommandResult(
            state=RuntimeState.RECORDED,
            reason_code="RECONCILIATION_EVIDENCE_ONLY",
            resource_id=recon_id,
            audit_reference=authority.audit_reference,
        )

    def manual_refund_reference(
        self,
        session: Session,
        authority: AuthorityFacts,
        *,
        payment_id: UUID,
        reference: str,
        idempotency_key: str,
        reason: str,
        reviewed_at: datetime,
    ) -> CommandResult:
        if (
            not _authorized(authority, "ENTITLEMENTS_TARIFF_ASSIGN_ADMIN")
            or not reason.strip()
            or not reference.strip()
        ):
            return CommandResult(
                state=RuntimeState.UNAUTHORIZED,
                reason_code="PROTECTED_MANUAL_REFUND_REQUIRED",
                audit_reference=authority.audit_reference,
            )
        payment = session.execute(
            select(_PAYMENTS.c.id).where(
                _PAYMENTS.c.id == payment_id, _PAYMENTS.c.account_id == authority.account_id
            )
        ).scalar_one_or_none()
        if payment is None:
            return CommandResult(
                state=RuntimeState.REJECTED,
                reason_code="PAYMENT_NOT_FOUND",
                audit_reference=authority.audit_reference,
            )
        fp = _fingerprint(("manual-refund", payment_id, reference, reason))
        state, prior = self._terminal(session, idempotency_key, fp)
        if state is RuntimeState.REPLAYED:
            return CommandResult(
                state=state,
                reason_code="REFUND_REPLAYED",
                resource_id=prior,
                audit_reference=authority.audit_reference,
            )
        if state is RuntimeState.MISMATCH:
            return CommandResult(
                state=state,
                reason_code="REFUND_IDEMPOTENCY_MISMATCH",
                audit_reference=authority.audit_reference,
            )
        operation_id = uuid4()
        session.execute(
            _OPERATIONS.insert().values(
                id=operation_id,
                payment_record_id=payment_id,
                operation_code="MANUAL_REFUND_REFERENCED",
                idempotency_key=_key(idempotency_key).value,
                request_fingerprint=fp.value,
                state=RefundState.MANUAL_REFUND_REFERENCED.value,
                attempt_count=0,
                next_due_at=None,
                created_at=reviewed_at,
                updated_at=reviewed_at,
                row_version=1,
            )
        )
        _audit(
            session, authority, action="MANUAL_REFUND_REFERENCE", target=operation_id, reason=reason
        )
        result = CommandResult(
            state=RuntimeState.RECORDED,
            reason_code="MANUAL_REFUND_REFERENCED",
            resource_id=operation_id,
            audit_reference=authority.audit_reference,
        )
        self._record_terminal(session, idempotency_key, fp, result)
        return result

    def consume_usage(
        self,
        session: Session,
        authority: AuthorityFacts,
        *,
        counter_code: str,
        window_start: datetime,
        window_end: datetime,
        limit_value: int,
        idempotency_key: str,
    ) -> CommandResult:
        if counter_code not in {"ACTIVE_BEACON_SLOT", "SCAN_INTERVAL_WINDOW"}:
            return CommandResult(
                state=RuntimeState.BLOCKED,
                reason_code="USAGE_COUNTER_FAMILY_NOT_APPROVED",
                audit_reference=authority.audit_reference,
            )
        if limit_value < 0 or window_end <= window_start:
            raise ValueError("bounded nonnegative counter and closed window required")
        row = (
            session.execute(
                select(_USAGE)
                .where(
                    _USAGE.c.account_id == authority.account_id,
                    _USAGE.c.counter_code == counter_code,
                    _USAGE.c.window_start == window_start,
                )
                .with_for_update()
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            ident = uuid4()
            session.execute(
                _USAGE.insert().values(
                    id=ident,
                    account_id=authority.account_id,
                    counter_code=counter_code,
                    window_start=window_start,
                    window_end=window_end,
                    consumed=1,
                    limit_value=limit_value,
                    created_at=_now(),
                    updated_at=_now(),
                    row_version=1,
                )
            )
            _audit(
                session,
                authority,
                action="USAGE_RECORD",
                target=ident,
                reason="bounded approved usage family",
            )
            return CommandResult(
                state=RuntimeState.RECORDED,
                reason_code="USAGE_RECORDED",
                resource_id=ident,
                audit_reference=authority.audit_reference,
            )
        if row["consumed"] >= row["limit_value"]:
            return CommandResult(
                state=RuntimeState.REJECTED,
                reason_code="USAGE_LIMIT_REACHED",
                resource_id=row["id"],
                audit_reference=authority.audit_reference,
            )
        session.execute(
            update(_USAGE)
            .where(_USAGE.c.id == row["id"])
            .values(
                consumed=_USAGE.c.consumed + 1,
                updated_at=_now(),
                row_version=_USAGE.c.row_version + 1,
            )
        )
        _audit(
            session,
            authority,
            action="USAGE_RECORD",
            target=row["id"],
            reason="bounded approved usage family",
        )
        return CommandResult(
            state=RuntimeState.RECORDED,
            reason_code="USAGE_RECORDED",
            resource_id=row["id"],
            audit_reference=authority.audit_reference,
        )


@dataclass(frozen=True, slots=True)
class ProviderResponse:
    state: PaymentState
    external_payment_id: str | None = None
    safe_reference: str | None = None


class FakeYooKassaProvider:
    """Deterministic provider fake; never performs network I/O."""

    def __init__(self, responses: dict[str, ProviderResponse] | None = None) -> None:
        self.responses = responses or {}
        self.calls: list[tuple[str, str]] = []

    def create_payment(
        self, idempotency_key: str, amount_minor: int, currency: str
    ) -> ProviderResponse:
        self.calls.append(("create", idempotency_key))
        return self.responses.get(
            idempotency_key,
            ProviderResponse(PaymentState.CONFIRMED, "fake-payment", "fake-reference"),
        )

    def retrieve_payment(self, external_payment_id: str) -> ProviderResponse:
        self.calls.append(("retrieve", external_payment_id))
        return self.responses.get(
            external_payment_id,
            ProviderResponse(PaymentState.UNRESOLVED, external_payment_id, "reconcile-required"),
        )

    def refund_payment(self, *args: Any, **kwargs: Any) -> ProviderResponse:
        raise RuntimeError("provider refund API is blocked")


class YooKassaSandboxAdapter:
    """Credential-disabled-by-default HTTPX adapter for create/retrieve only."""

    def __init__(
        self,
        *,
        enabled: bool = False,
        api_base: str = "https://api.yookassa.ru/v3",
        secret_file: Path | None = None,
        timeout: httpx.Timeout | None = None,
        max_response_bytes: int = 2_097_152,
        client: httpx.Client | None = None,
    ) -> None:
        self.enabled = enabled
        self.api_base = api_base.rstrip("/")
        self.secret_file = secret_file
        self.timeout = timeout or httpx.Timeout(connect=5, read=30, write=30, pool=5)
        self.max_response_bytes = max_response_bytes
        self.client = client

    def _secret(self) -> str | None:
        if not self.enabled or self.secret_file is None or not self.secret_file.is_file():
            return None
        return self.secret_file.read_text(encoding="utf-8").strip() or None

    def _disabled(self) -> ProviderResponse:
        return ProviderResponse(PaymentState.REJECTED, safe_reference="PROVIDER_DISABLED_CONTINUE")

    def create_payment(
        self, *, idempotency_key: str, amount_minor: int, currency: str
    ) -> ProviderResponse:
        secret = self._secret()
        if secret is None:
            return self._disabled()
        payload = {
            "amount": {"value": f"{amount_minor / 100:.2f}", "currency": currency},
            "capture": True,
        }
        try:
            response = (self.client or httpx.Client(timeout=self.timeout)).post(
                f"{self.api_base}/payments",
                json=payload,
                auth=(secret, ""),
                headers={"Idempotence-Key": idempotency_key},
            )
            if len(response.content) > self.max_response_bytes:
                return ProviderResponse(PaymentState.AMBIGUOUS, safe_reference="RESPONSE_TOO_LARGE")
            if response.status_code >= 500:
                return ProviderResponse(
                    PaymentState.AMBIGUOUS, safe_reference="TRANSPORT_OR_PROVIDER_UNKNOWN"
                )
            body = response.json()
            payment_id = body.get("id") if isinstance(body, dict) else None
            status = body.get("status") if isinstance(body, dict) else None
            return ProviderResponse(
                PaymentState.CONFIRMED
                if status == "succeeded"
                else PaymentState.RECONCILE_REQUIRED,
                payment_id,
                "normalized-provider-response",
            )
        except httpx.HTTPError, ValueError:
            return ProviderResponse(
                PaymentState.AMBIGUOUS, safe_reference="PROVIDER_RESPONSE_UNAVAILABLE"
            )

    def retrieve_payment(self, *, external_payment_id: str) -> ProviderResponse:
        secret = self._secret()
        if secret is None:
            return self._disabled()
        try:
            response = (self.client or httpx.Client(timeout=self.timeout)).get(
                f"{self.api_base}/payments/{external_payment_id}", auth=(secret, "")
            )
            if len(response.content) > self.max_response_bytes:
                return ProviderResponse(
                    PaymentState.AMBIGUOUS, external_payment_id, "RESPONSE_TOO_LARGE"
                )
            body = response.json()
            status = body.get("status") if isinstance(body, dict) else None
            return ProviderResponse(
                PaymentState.CONFIRMED
                if status == "succeeded"
                else (PaymentState.REJECTED if status == "canceled" else PaymentState.UNRESOLVED),
                external_payment_id,
                "normalized-provider-response",
            )
        except httpx.HTTPError, ValueError:
            return ProviderResponse(
                PaymentState.AMBIGUOUS, external_payment_id, "PROVIDER_RESPONSE_UNAVAILABLE"
            )

    def refund_payment(self, *args: Any, **kwargs: Any) -> ProviderResponse:
        raise RuntimeError("provider refund API is blocked")


__all__ = [
    "AuthorityFacts",
    "CommandResult",
    "EffectiveEntitlement",
    "EntitlementsBillingRuntime",
    "FakeVerifiedIdentityPort",
    "FakeYooKassaProvider",
    "NormalizedPaymentEvidence",
    "PaymentState",
    "ProviderResponse",
    "RefundState",
    "RuntimeState",
    "YooKassaSandboxAdapter",
]
