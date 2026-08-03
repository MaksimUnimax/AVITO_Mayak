"""Durable, provider-neutral Notification Delivery runtime.

This module is deliberately synchronous and transaction explicit.  The only
external execution boundary is an injected adapter callable; callers must
invoke it after :func:`create_attempt` has returned and committed.
"""

# ruff: noqa: E501

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Iterable, Protocol, cast
from uuid import UUID, uuid4

from sqlalchemy import Select, Table, select, text, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session, sessionmaker

from mayak.persistence.metadata import metadata

from .attempt import NotificationProviderOutcomeClass
from .delivery_plan import NotificationDeliveryPlanDecision
from .eligibility import NotificationChannelClass, NotificationEligibilityDecision
from .source_intake import (
    NotificationSourceEvent,
    NotificationSourceIntakeDecision,
    evaluate_notification_source_intake,
)

RF17_TASK_ID = "RF-17-NOTIFICATION-DELIVERY-DURABLE-RUNTIME-20260803-01"
_SAFE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,254}$")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_MAX_SAFE_TEXT = 255


class NotificationRuntimeError(RuntimeError):
    """Base class for fail-closed durable runtime errors."""


class IdempotencyConflict(NotificationRuntimeError):
    pass


class InvalidNotificationSource(NotificationRuntimeError):
    pass


class LeaseConflict(NotificationRuntimeError):
    pass


class ReconciliationRequired(NotificationRuntimeError):
    pass


class ReconciliationConflict(NotificationRuntimeError):
    pass


class AccountScopeConflict(NotificationRuntimeError):
    pass


class ReconciliationDisposition(StrEnum):
    DELIVERED = "RESOLVED_DELIVERED"
    FAILED = "RESOLVED_FAILED"
    NO_EFFECT_RETRY = "RESOLVED_NO_EFFECT_RETRY"
    MANUAL_REVIEW = "MANUAL_REVIEW"


@dataclass(frozen=True, slots=True)
class TrustedReconciliationEvidence:
    """Server-trusted, provider-redacted reconciliation conclusion."""

    attempt_id: UUID
    effect_fingerprint: str
    resolution_id: str
    conclusion: ReconciliationDisposition
    committed: bool
    evidence_reference_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if not _HEX64.fullmatch(self.effect_fingerprint) or not _safe_text(self.resolution_id):
            raise ValueError("reconciliation evidence identity is unsafe")
        if not self.committed or not self.evidence_reference_ids:
            raise ValueError("reconciliation evidence must be committed and referenced")
        if any(not _safe_text(item) for item in self.evidence_reference_ids):
            raise ValueError("reconciliation evidence references must be safe")


class OutboxState(StrEnum):
    PENDING = "PENDING"
    RETRY = "RETRY"
    CLAIMED = "CLAIMED"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"
    RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"
    CANCELLED = "CANCELLED"


class FakeOutcomeClass(StrEnum):
    """The generic simulator vocabulary; values use the accepted semantic port."""

    DEFINITE_ACCEPTED = "PROVIDER_ACCEPTED"
    DEFINITE_FAILURE = "PROVIDER_REJECTED"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    RESTRICTED = "RATE_OR_ACCESS_RESTRICTED"
    MALFORMED = "MALFORMED_OR_UNUSABLE_PROVIDER_RESPONSE"
    DISPATCH_AMBIGUOUS = "DISPATCH_AMBIGUOUS"
    DELIVERY_AMBIGUOUS = "DELIVERY_AMBIGUOUS"
    NOT_SENT = "NOT_SENT"


@dataclass(frozen=True, slots=True)
class EndpointEligibility:
    endpoint_id: UUID
    account_id: UUID
    provider_code: str
    endpoint_ref: str
    channel_class: NotificationChannelClass = NotificationChannelClass.TELEGRAM


@dataclass(frozen=True, slots=True)
class NotificationEventRecord:
    id: UUID
    account_id: UUID
    beacon_id: UUID | None
    run_id: UUID | None
    source_effect_fingerprint: str
    event_code: str
    payload: dict[str, object]


@dataclass(frozen=True, slots=True)
class OutboxClaim:
    outbox_id: UUID
    event_id: UUID
    endpoint_id: UUID
    lease_token: UUID
    lease_expires_at: datetime


@dataclass(frozen=True, slots=True)
class AttemptLease:
    attempt_id: UUID
    outbox_id: UUID
    attempt_number: int
    effect_fingerprint: str
    channel_class: str
    target_reference: str
    lease_token: UUID


@dataclass(frozen=True, slots=True)
class FakeProviderOutcome:
    outcome_reference_id: str
    outcome_class: NotificationProviderOutcomeClass
    provider_safe_delivery_reference: str | None = None
    reason_code: str = "generic-outcome"

    def __post_init__(self) -> None:
        if not _safe_text(self.outcome_reference_id):
            raise ValueError("outcome_reference_id must be a safe opaque reference")
        if self.provider_safe_delivery_reference is not None and not _safe_text(
            self.provider_safe_delivery_reference
        ):
            raise ValueError("provider delivery reference must be safe")
        if not _safe_text(self.reason_code):
            raise ValueError("reason_code must be safe")


class ProviderNeutralAdapter(Protocol):
    def __call__(self, attempt: AttemptLease) -> FakeProviderOutcome: ...


@dataclass(frozen=True, slots=True)
class NotificationHistoryEntry:
    account_id: UUID
    beacon_id: UUID | None
    event_id: UUID
    outbox_id: UUID | None
    attempt_id: UUID | None
    event_code: str
    listing_count: int
    listing_reference_ids: tuple[str, ...]
    channel_class: str | None
    delivery_status: str
    failure_or_reconciliation: str | None


def _table(name: str) -> Table:
    return metadata.tables[f"mayak.{name}"]


def _safe_text(value: object) -> bool:
    return (
        type(value) is str
        and bool(value)
        and len(value) <= _MAX_SAFE_TEXT
        and bool(_SAFE.fullmatch(value))
    )


def _uuid(value: str | UUID, field: str) -> UUID:
    try:
        return value if isinstance(value, UUID) else UUID(value)
    except (ValueError, AttributeError, TypeError) as exc:
        raise InvalidNotificationSource(f"{field} is not an opaque UUID") from exc


def _now(value: datetime | None) -> datetime:
    result = value or datetime.now(UTC)
    if result.tzinfo is None:
        raise ValueError("runtime timestamps must be timezone-aware")
    return result.astimezone(UTC)


def _advisory_key(prefix: str, value: str) -> int:
    return int.from_bytes(
        hashlib.sha256(f"{prefix}:{value}".encode()).digest()[:8], "big", signed=True
    )


def _canonical_source_payload(source: NotificationSourceEvent) -> dict[str, object]:
    safe_refs = tuple(sorted(source.safe_listing_reference_ids))
    if any(not _safe_text(item) for item in safe_refs):
        raise InvalidNotificationSource("listing references are not safe opaque references")
    safe_fields = {
        "source_identity": source.idempotency_key.value,
        "source_event_id": source.source_event_id,
        "source_fact_id": source.source_fact_id,
        "source_contract": source.source_contract,
        "source_contract_version": source.source_contract_version,
        "source_commit_reference": source.source_commit_reference,
        "source_family": source.source_family.value,
        "source_producer": source.source_producer.value,
        "listing_count": source.listing_count,
        "listing_reference_ids": list(safe_refs),
        "correlation_id": source.correlation_id,
        "causation_id": source.causation_id,
    }
    encoded = json.dumps(safe_fields, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    if len(encoded.encode()) > 60000:
        raise InvalidNotificationSource("canonical notification payload is too large")
    if any(
        not _safe_text(str(value))
        for value in (source.idempotency_key.value, source.source_event_id, source.source_fact_id)
    ):
        raise InvalidNotificationSource("source identity contains unsafe material")
    return safe_fields


def _decision(source: NotificationSourceEvent) -> NotificationSourceIntakeDecision:
    return evaluate_notification_source_intake(
        decision_id=f"rf17:{source.source_event_id}",
        source_event=source,
        evidence_reference_ids=("rf17-source-intake",),
    )


def ingest_source(
    session: Session, source: NotificationSourceEvent, *, now: datetime | None = None
) -> NotificationEventRecord | None:
    """Commit one source event, or return ``None`` for a rejected/status-only source."""
    decision = _decision(source)
    if not decision.notification_candidate:
        return None
    payload = _canonical_source_payload(source)
    fingerprint = source.idempotency_fingerprint.value
    if not _HEX64.fullmatch(fingerprint):
        raise InvalidNotificationSource("source fingerprint must be lowercase SHA-256")
    account_id = _uuid(source.account_id, "account_id")
    beacon_id = _uuid(source.beacon_id, "beacon_id") if source.beacon_id else None
    run_id = _uuid(source.scan_run_id, "scan_run_id") if source.scan_run_id else None
    events = _table("notification_events")
    moment = _now(now)
    with session.begin():
        session.execute(
            text("SELECT pg_advisory_xact_lock(:key)"),
            {"key": _advisory_key("notification-source", source.idempotency_key.value)},
        )
        session.execute(
            text("SELECT pg_advisory_xact_lock(:key)"),
            {"key": _advisory_key("notification-fingerprint", fingerprint)},
        )
        existing = (
            session.execute(select(events).where(events.c.source_effect_fingerprint == fingerprint))
            .mappings()
            .first()
        )
        if existing is None:
            existing = (
                session.execute(
                    select(events).where(
                        events.c.payload["source_identity"].astext == source.idempotency_key.value
                    )
                )
                .mappings()
                .first()
            )
        if existing is not None:
            old_payload = dict(existing["payload"] or {})
            same_scope = (
                existing["account_id"] == account_id
                and existing["beacon_id"] == beacon_id
                and existing["run_id"] == run_id
                and old_payload.get("source_identity") == source.idempotency_key.value
                and old_payload.get("source_family") == source.source_family.value
                and old_payload == payload
            )
            if existing["source_effect_fingerprint"] != fingerprint or not same_scope:
                raise IdempotencyConflict("source identity, fingerprint, or scope conflicts")
            return _event_record(existing)
        event_id = uuid4()
        session.execute(
            insert(events).values(
                id=event_id,
                account_id=account_id,
                beacon_id=beacon_id,
                run_id=run_id,
                source_effect_fingerprint=fingerprint,
                event_code=source.source_family.value,
                payload=payload,
                created_at=moment,
            )
        )
        return NotificationEventRecord(
            event_id,
            account_id,
            beacon_id,
            run_id,
            fingerprint,
            source.source_family.value,
            payload,
        )


def _event_record(row: object) -> NotificationEventRecord:
    if not isinstance(row, Mapping):
        raise TypeError("event row must be a mapping")
    data = row
    return NotificationEventRecord(
        data["id"],
        data["account_id"],
        data["beacon_id"],
        data["run_id"],
        data["source_effect_fingerprint"],
        data["event_code"],
        data["payload"],
    )


def register_endpoint(
    session: Session, endpoint: EndpointEligibility, *, now: datetime | None = None
) -> UUID:
    if endpoint.channel_class not in (NotificationChannelClass.TELEGRAM, NotificationChannelClass.MAX):
        raise AccountScopeConflict("only accepted push channel classes may be registered")
    if endpoint.provider_code != endpoint.channel_class.value:
        raise AccountScopeConflict("provider code must equal accepted logical channel class")
    if not _safe_text(endpoint.provider_code) or not _safe_text(endpoint.endpoint_ref):
        raise InvalidNotificationSource("endpoint identity is not a safe opaque reference")
    endpoints = _table("notification_endpoints")
    moment = _now(now)
    with session.begin():
        result = session.execute(
            insert(endpoints)
            .values(
                id=endpoint.endpoint_id,
                account_id=endpoint.account_id,
                provider_code=endpoint.provider_code,
                endpoint_ref=endpoint.endpoint_ref,
                state="ACTIVE",
                created_at=moment,
                updated_at=moment,
                row_version=1,
            )
            .on_conflict_do_nothing(constraint="uq_notification_endpoints_provider_endpoint")
            .returning(endpoints.c.id)
        )
        if result.scalar_one_or_none() is not None:
            return endpoint.endpoint_id
        existing = session.execute(
            select(endpoints).where(
                endpoints.c.provider_code == endpoint.provider_code,
                endpoints.c.endpoint_ref == endpoint.endpoint_ref,
            )
        ).mappings().one()
        if (
            existing["account_id"] != endpoint.account_id
            or existing["id"] != endpoint.endpoint_id
            or existing["provider_code"] != endpoint.channel_class.value
        ):
            raise AccountScopeConflict("endpoint ownership or semantic identity conflicts")
        return existing["id"]


def fanout_event(
    session: Session,
    event_id: UUID,
    eligible_endpoints: Iterable[UUID],
    *,
    now: datetime | None = None,
    eligibility_decision: NotificationEligibilityDecision | None = None,
    delivery_plan: NotificationDeliveryPlanDecision | None = None,
) -> tuple[UUID, ...]:
    endpoints = _table("notification_endpoints")
    events = _table("notification_events")
    outbox = _table("notification_outbox")
    ids = tuple(dict.fromkeys(eligible_endpoints))
    if not ids:
        raise AccountScopeConflict("no eligible push endpoint; fan-out is blocked")
    if type(eligibility_decision) is not NotificationEligibilityDecision:
        raise AccountScopeConflict("fan-out requires the accepted eligibility decision type")
    if type(delivery_plan) is not NotificationDeliveryPlanDecision:
        raise AccountScopeConflict("fan-out requires the accepted delivery-plan decision type")
    eligibility_decision = cast(NotificationEligibilityDecision, eligibility_decision)
    delivery_plan = cast(NotificationDeliveryPlanDecision, delivery_plan)
    if (
        not eligibility_decision.outbox_candidate_eligible
        or not eligibility_decision.source_eligible
        or eligibility_decision.outbox_effect_authorized is not False
        or delivery_plan.status.value != "PLANNED"
        or not delivery_plan.plan_created
        or delivery_plan.delivery_plan is None
    ):
        raise AccountScopeConflict("semantic authority does not authorize outbox creation")
    moment = _now(now)
    with session.begin():
        event = (
            session.execute(select(events).where(events.c.id == event_id).with_for_update())
            .mappings()
            .first()
        )
        if event is None:
            raise InvalidNotificationSource("unknown notification event")
        source_event = eligibility_decision.source_intake_decision.source_event
        item = delivery_plan.outbox_creation_decision.outbox_item
        plan = delivery_plan.delivery_plan
        if item is None or plan.outbox_item != item:
            raise AccountScopeConflict("delivery plan is not bound to its accepted outbox item")
        if (
            str(event["account_id"]) != item.account_id
            or str(event["beacon_id"]) != str(item.beacon_id)
            or (event["payload"] or {}).get("source_event_id") != item.source_event_id
            or event["event_code"] != item.event_reason.value
            or source_event.source_event_id != item.source_event_id
            or source_event.account_id != item.account_id
            or source_event.beacon_id != item.beacon_id
            or source_event.source_fact_id != item.source_fact_id
            or source_event.source_contract != item.source_contract
            or source_event.listing_count != item.listing_count
            or source_event.safe_listing_reference_ids != item.safe_listing_reference_ids
        ):
            raise AccountScopeConflict("eligibility/outbox/event semantic scope mismatch")
        if plan.account_id != item.account_id or plan.beacon_id != item.beacon_id:
            raise AccountScopeConflict("delivery plan scope mismatch")
        plan_entries = {
            entry.channel_class: entry
            for entry in plan.channel_entries
            if entry.push_planned
        }
        made: list[UUID] = []
        for endpoint_id in ids:
            endpoint = (
                session.execute(
                    select(endpoints).where(endpoints.c.id == endpoint_id).with_for_update()
                )
                .mappings()
                .first()
            )
            if (
                endpoint is None
                or endpoint["account_id"] != event["account_id"]
                or endpoint["state"] != "ACTIVE"
            ):
                raise InvalidNotificationSource(
                    "eligible endpoint is absent, inactive, or cross-account"
                )
            if endpoint["provider_code"] not in (NotificationChannelClass.TELEGRAM.value, NotificationChannelClass.MAX.value):
                raise AccountScopeConflict("WEB_STATUS_READ_MODEL and arbitrary channels cannot fan out")
            channel = NotificationChannelClass(endpoint["provider_code"])
            entry = plan_entries.get(channel)
            if (
                entry is None
                or entry.target_reference_id != endpoint["endpoint_ref"]
                or entry.outbox_channel_intent is None
                or entry.outbox_channel_intent.channel_class is not channel
                or entry.outbox_channel_intent.target_reference_id != endpoint["endpoint_ref"]
                or channel not in eligibility_decision.eligible_push_channels
            ):
                raise AccountScopeConflict("endpoint is not authorized by the accepted channel plan")
            outbox_id = uuid4()
            result = session.execute(
                insert(outbox)
                .values(
                    id=outbox_id,
                    event_id=event_id,
                    endpoint_id=endpoint_id,
                    state=OutboxState.PENDING.value,
                    available_at=moment,
                    attempt_count=0,
                    created_at=moment,
                    row_version=1,
                )
                .on_conflict_do_nothing(index_elements=["event_id", "endpoint_id"])
                .returning(outbox.c.id)
            )
            inserted_id = result.scalar_one_or_none()
            if inserted_id is not None:
                made.append(inserted_id)
        return tuple(made)


def claim_due(
    session: Session, *, now: datetime, limit: int, lease_seconds: int
) -> tuple[OutboxClaim, ...]:
    if not 1 <= limit <= 1000 or lease_seconds <= 0:
        raise ValueError("bounded claim limit and explicit positive lease are required")
    outbox = _table("notification_outbox")
    attempts = _table("notification_delivery_attempts")
    moment = _now(now)
    with session.begin():
        expired = (
            session.execute(
                select(outbox)
                .where(
                    outbox.c.state == OutboxState.CLAIMED.value, outbox.c.lease_expires_at <= moment
                )
                .with_for_update(skip_locked=True)
            )
            .mappings()
            .all()
        )
        for row in expired:
            current_claim_attempt = (
                session.execute(
                    select(attempts.c.id).where(
                        attempts.c.outbox_id == row["id"],
                        attempts.c.started_at >= row["lease_started_at"],
                        attempts.c.state.in_(("STARTED", "RECONCILIATION_REQUIRED")),
                    ).limit(1)
                ).first()
                if row["lease_started_at"] is not None
                else None
            )
            new_state = (
                OutboxState.RECONCILIATION_REQUIRED.value
                if current_claim_attempt is not None
                else OutboxState.PENDING.value
            )
            session.execute(
                update(outbox)
                .where(outbox.c.id == row["id"], outbox.c.row_version == row["row_version"])
                .values(
                    state=new_state,
                    lease_started_at=None,
                    lease_expires_at=None,
                    lease_token=None,
                    row_version=row["row_version"] + 1,
                )
            )
        rows = (
            session.execute(
                select(outbox)
                .where(
                    outbox.c.state.in_((OutboxState.PENDING.value, OutboxState.RETRY.value)),
                    outbox.c.available_at <= moment,
                )
                .order_by(outbox.c.available_at, outbox.c.id)
                .limit(limit)
                .with_for_update(skip_locked=True)
            )
            .mappings()
            .all()
        )
        result: list[OutboxClaim] = []
        for row in rows:
            token, expiry = uuid4(), moment + timedelta(seconds=lease_seconds)
            session.execute(
                update(outbox)
                .where(outbox.c.id == row["id"], outbox.c.row_version == row["row_version"])
                .values(
                    state=OutboxState.CLAIMED.value,
                    lease_started_at=moment,
                    lease_expires_at=expiry,
                    lease_token=token,
                    row_version=row["row_version"] + 1,
                )
            )
            result.append(
                OutboxClaim(row["id"], row["event_id"], row["endpoint_id"], token, expiry)
            )
        return tuple(result)


def create_attempt(
    session: Session,
    claim: OutboxClaim,
    *,
    channel_class: str,
    target_reference: str,
    effect_fingerprint: str,
    now: datetime | None = None,
) -> AttemptLease:
    if channel_class not in (NotificationChannelClass.TELEGRAM.value, NotificationChannelClass.MAX.value) or (
        not _safe_text(channel_class)
        or not _safe_text(target_reference)
        or not _HEX64.fullmatch(effect_fingerprint)
    ):
        raise InvalidNotificationSource("attempt identity is unsafe")
    outbox, attempts = _table("notification_outbox"), _table("notification_delivery_attempts")
    moment = _now(now)
    with session.begin():
        row = (
            session.execute(select(outbox).where(outbox.c.id == claim.outbox_id).with_for_update())
            .mappings()
            .first()
        )
        if (
            row is None
            or row["state"] != OutboxState.CLAIMED.value
            or row["lease_token"] != claim.lease_token
            or row["lease_expires_at"] <= moment
        ):
            raise LeaseConflict("attempt requires the current unexpired outbox lease")
        if session.execute(
            select(attempts.c.id)
            .where(
                attempts.c.outbox_id == claim.outbox_id,
                attempts.c.state.in_(("STARTED", "RECONCILIATION_REQUIRED")),
            )
            .limit(1)
        ).first():
            raise ReconciliationRequired("outbox already has an unresolved attempt")
        number = (
            int(
                session.execute(
                    select(attempts.c.attempt_number)
                    .where(attempts.c.outbox_id == claim.outbox_id)
                    .order_by(attempts.c.attempt_number.desc())
                    .limit(1)
                ).scalar_one_or_none()
                or 0
            )
            + 1
        )
        attempt_id = uuid4()
        session.execute(
            insert(attempts).values(
                id=attempt_id,
                outbox_id=claim.outbox_id,
                attempt_number=number,
                state="STARTED",
                effect_fingerprint=effect_fingerprint,
                started_at=moment,
                safe_metadata={
                    "channel_class": channel_class,
                    "target_reference": target_reference,
                },
            )
        )
        return AttemptLease(
            attempt_id,
            claim.outbox_id,
            number,
            effect_fingerprint,
            channel_class,
            target_reference,
            claim.lease_token,
        )


def commit_outcome(
    session: Session,
    attempt: AttemptLease,
    outcome: FakeProviderOutcome,
    *,
    now: datetime | None = None,
) -> str:
    attempts, outbox, reconciliations = (
        _table("notification_delivery_attempts"),
        _table("notification_outbox"),
        _table("notification_delivery_reconciliations"),
    )
    moment = _now(now)
    result_fp = hashlib.sha256(
        json.dumps(
            {
                "attempt": str(attempt.attempt_id),
                "effect": attempt.effect_fingerprint,
                "outcome": outcome.outcome_reference_id,
                "class": outcome.outcome_class.value,
            },
            sort_keys=True,
        ).encode()
    ).hexdigest()
    ambiguous = outcome.outcome_class in (
        NotificationProviderOutcomeClass.DISPATCH_AMBIGUOUS,
        NotificationProviderOutcomeClass.DELIVERY_AMBIGUOUS,
    )
    accepted = outcome.outcome_class is NotificationProviderOutcomeClass.PROVIDER_ACCEPTED
    with session.begin():
        row = (
            session.execute(
                select(attempts).where(attempts.c.id == attempt.attempt_id).with_for_update()
            )
            .mappings()
            .first()
        )
        box = (
            session.execute(
                select(outbox).where(outbox.c.id == attempt.outbox_id).with_for_update()
            )
            .mappings()
            .first()
        )
        if row is None or box is None:
            raise LeaseConflict("unknown attempt")
        metadata_value = dict(row["safe_metadata"] or {})
        previous_fp = metadata_value.get("outcome_fingerprint")
        if previous_fp is not None:
            if previous_fp != result_fp:
                raise IdempotencyConflict("provider-result identity has a different fingerprint")
            return str(row["state"])
        if (
            box["state"] != OutboxState.CLAIMED.value
            or box["lease_token"] != attempt.lease_token
            or box["lease_expires_at"] <= moment
        ):
            raise LeaseConflict("terminal result requires the current unexpired lease")
        outbox_state = "RECONCILIATION_REQUIRED" if ambiguous else ("DELIVERED" if accepted else "FAILED")
        attempt_state = "RECONCILIATION_REQUIRED" if ambiguous else ("DELIVERED_ACCEPTED" if accepted else "FAILED_NON_RETRYABLE")
        metadata_value.update(
            {
                "outcome_reference_id": outcome.outcome_reference_id,
                "outcome_fingerprint": result_fp,
                "reason_code": outcome.reason_code,
            }
        )
        session.execute(
            update(attempts)
            .where(attempts.c.id == attempt.attempt_id)
            .values(
                state=attempt_state,
                provider_reference=outcome.provider_safe_delivery_reference,
                completed_at=moment,
                safe_metadata=metadata_value,
            )
        )
        session.execute(
            update(outbox)
            .where(outbox.c.id == attempt.outbox_id, outbox.c.lease_token == attempt.lease_token)
            .values(
                state=outbox_state,
                lease_started_at=None,
                lease_expires_at=None,
                lease_token=None,
                row_version=box["row_version"] + 1,
            )
        )
        if ambiguous:
            session.execute(
                insert(reconciliations)
                .values(
                    id=uuid4(),
                    attempt_id=attempt.attempt_id,
                    state="UNRESOLVED",
                    due_at=moment,
                    safe_metadata={
                        "outcome_reference_id": outcome.outcome_reference_id,
                        "outcome_fingerprint": result_fp,
                        "effect_fingerprint": attempt.effect_fingerprint,
                    },
                )
                .on_conflict_do_nothing(index_elements=["attempt_id"])
            )
        return outbox_state


def resolve_reconciliation(
    session: Session,
    attempt_id: UUID,
    disposition: ReconciliationDisposition | None = None,
    *,
    resolution_id: str,
    now: datetime | None = None,
    evidence: TrustedReconciliationEvidence | None = None,
) -> str:
    if evidence is None or disposition is not None:
        raise ReconciliationConflict("typed trusted reconciliation evidence is required")
    if evidence.attempt_id != attempt_id or evidence.resolution_id != resolution_id:
        raise ReconciliationConflict("reconciliation evidence does not identify this attempt")
    disposition = evidence.conclusion
    recs, outbox, attempts = (
        _table("notification_delivery_reconciliations"),
        _table("notification_outbox"),
        _table("notification_delivery_attempts"),
    )
    moment = _now(now)
    with session.begin():
        rec = (
            session.execute(select(recs).where(recs.c.attempt_id == attempt_id).with_for_update())
            .mappings()
            .first()
        )
        if rec is None:
            raise ReconciliationConflict("reconciliation does not exist")
        current = dict(rec["safe_metadata"] or {})
        attempt_record = (
            session.execute(
                select(attempts)
                .where(attempts.c.id == attempt_id)
                .with_for_update()
            )
            .mappings()
            .first()
        )
        if attempt_record is None or attempt_record["id"] != evidence.attempt_id:
            raise ReconciliationConflict("persisted attempt identity does not match evidence")
        if attempt_record["effect_fingerprint"] != evidence.effect_fingerprint:
            raise ReconciliationConflict("persisted attempt effect fingerprint conflicts with evidence")
        if current.get("effect_fingerprint") != evidence.effect_fingerprint:
            raise ReconciliationConflict("reconciliation effect fingerprint conflicts with attempt")
        if rec["resolved_at"] is not None:
            if (
                current.get("resolution_id") != resolution_id
                or rec["state"] != disposition.value
                or current.get("effect_fingerprint") != evidence.effect_fingerprint
                or tuple(current.get("evidence_reference_ids", ())) != evidence.evidence_reference_ids
            ):
                raise ReconciliationConflict("reconciliation already resolved differently")
            return rec["state"]
        current.update({"resolution_id": resolution_id, "conclusion": disposition.value, "effect_fingerprint": evidence.effect_fingerprint, "evidence_reference_ids": list(evidence.evidence_reference_ids)})
        attempt_row = session.execute(
            select(attempts.c.outbox_id).where(attempts.c.id == attempt_id)
        ).scalar_one()
        next_state = (
            OutboxState.RETRY.value
            if disposition is ReconciliationDisposition.NO_EFFECT_RETRY
            else (
                OutboxState.DELIVERED.value
                if disposition is ReconciliationDisposition.DELIVERED
                else OutboxState.FAILED.value
                if disposition is ReconciliationDisposition.FAILED
                else OutboxState.RECONCILIATION_REQUIRED.value
            )
        )
        attempt_state = (
            "DELIVERED_ACCEPTED" if disposition is ReconciliationDisposition.DELIVERED
            else "FAILED_NON_RETRYABLE" if disposition is ReconciliationDisposition.FAILED
            else "FAILED_RETRYABLE_AFTER_POLICY" if disposition is ReconciliationDisposition.NO_EFFECT_RETRY
            else "RECONCILIATION_REQUIRED"
        )
        session.execute(
            update(recs)
            .where(recs.c.id == rec["id"])
            .values(
                state=disposition.value,
                resolved_at=moment,
                safe_metadata=current,
                row_version=rec["row_version"] + 1,
            )
        )
        session.execute(
            update(attempts).where(attempts.c.id == attempt_id).values(state=attempt_state)
        )
        session.execute(
            update(outbox)
            .where(outbox.c.id == attempt_row)
            .values(
                state=next_state,
                available_at=moment
                if next_state == OutboxState.RETRY.value
                else outbox.c.available_at,
                row_version=outbox.c.row_version + 1,
            )
        )
        return disposition.value


def run_worker_cycle(
    factory: sessionmaker[Session],
    adapter: ProviderNeutralAdapter,
    *,
    now: datetime,
    limit: int,
    lease_seconds: int,
) -> tuple[str, ...]:
    with factory() as session:
        claims = claim_due(session, now=now, limit=limit, lease_seconds=lease_seconds)
    states: list[str] = []
    for claim in claims:
        with factory() as session:
            endpoint = (
                session.execute(
                    select(_table("notification_endpoints")).where(
                        _table("notification_endpoints").c.id == claim.endpoint_id
                    )
                )
                .mappings()
                .one()
            )
            effect = hashlib.sha256(
                f"{claim.event_id}:{claim.endpoint_id}:{endpoint['provider_code']}".encode()
            ).hexdigest()
            attempt = create_attempt(
                session,
                claim,
                channel_class=endpoint["provider_code"],
                target_reference=endpoint["endpoint_ref"],
                effect_fingerprint=effect,
                now=now,
            )
        outcome = adapter(attempt)
        with factory() as session:
            states.append(commit_outcome(session, attempt, outcome, now=now))
    return tuple(states)


def read_history(
    session: Session, *, account_id: UUID, actor_account_id: UUID | None = None, beacon_id: UUID | None = None, limit: int = 100
) -> tuple[NotificationHistoryEntry, ...]:
    if not 1 <= limit <= 1000:
        raise ValueError("bounded history limit is required")
    if actor_account_id is None or actor_account_id != account_id:
        raise AccountScopeConflict("requester is not authorized for this account")
    events, outbox, endpoints, attempts, recs = (
        _table(name)
        for name in (
            "notification_events",
            "notification_outbox",
            "notification_endpoints",
            "notification_delivery_attempts",
            "notification_delivery_reconciliations",
        )
    )
    query: Select = (
        select(events, outbox, endpoints, attempts, recs)
        .select_from(
            events.outerjoin(outbox, outbox.c.event_id == events.c.id)
            .outerjoin(endpoints, endpoints.c.id == outbox.c.endpoint_id)
            .outerjoin(attempts, attempts.c.outbox_id == outbox.c.id)
            .outerjoin(recs, recs.c.attempt_id == attempts.c.id)
        )
        .where(events.c.account_id == account_id)
    )
    if beacon_id is not None:
        query = query.where(events.c.beacon_id == beacon_id)
    query = query.order_by(
        events.c.created_at.desc(), events.c.id, outbox.c.id, attempts.c.attempt_number
    ).limit(limit)
    rows = session.execute(query).mappings().all()
    result: list[NotificationHistoryEntry] = []
    for row in rows:
        payload = row[events.c.payload] or {}
        refs = tuple(payload.get("listing_reference_ids", ()))
        result.append(
            NotificationHistoryEntry(
                account_id,
                row[events.c.beacon_id],
                row[events.c.id],
                row[outbox.c.id],
                row[attempts.c.id],
                row[events.c.event_code],
                int(payload.get("listing_count", 0)),
                refs,
                (row[endpoints.c.provider_code] if row[endpoints.c.id] else None),
                row[outbox.c.state] if row[outbox.c.id] else "EVENT_ONLY",
                row[recs.c.state] if row[recs.c.id] else None,
            )
        )
    return tuple(result)


__all__ = (
    "RF17_TASK_ID",
    "NotificationRuntimeError",
    "IdempotencyConflict",
    "InvalidNotificationSource",
    "LeaseConflict",
    "ReconciliationRequired",
    "ReconciliationConflict",
    "AccountScopeConflict",
    "ReconciliationDisposition",
    "OutboxState",
    "FakeOutcomeClass",
    "EndpointEligibility",
    "NotificationEventRecord",
    "OutboxClaim",
    "AttemptLease",
    "FakeProviderOutcome",
    "TrustedReconciliationEvidence",
    "ProviderNeutralAdapter",
    "NotificationHistoryEntry",
    "ingest_source",
    "register_endpoint",
    "fanout_event",
    "claim_due",
    "create_attempt",
    "commit_outcome",
    "resolve_reconciliation",
    "run_worker_cycle",
    "read_history",
)
