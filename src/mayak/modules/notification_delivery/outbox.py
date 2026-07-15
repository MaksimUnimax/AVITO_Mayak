from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from mayak.contracts.idempotency import IdempotencyDecision
from mayak.platform.idempotency import IdempotencyFingerprint, IdempotencyKey, IdempotencyScope

from .eligibility import (
    NotificationChannelClass,
    NotificationChannelGateDecision,
    NotificationChannelGateStatus,
    NotificationEligibilityDecision,
    NotificationEligibilityStatus,
)
from .source_intake import NotificationSourceFamily, NotificationSourceProducer

ND04_TASK_ID = "ND-04-GENERIC-OUTBOX-SEMANTICS-20260715-006"

_ALLOWED_PUSH_CHANNEL_CLASSES = (
    NotificationChannelClass.TELEGRAM,
    NotificationChannelClass.MAX,
)

_OUTBOX_REASON_CODES = (
    "outbox-created",
    "outbox-replayed",
    "outbox-eligibility-blocked",
    "outbox-idempotency-fingerprint-mismatch",
    "outbox-idempotency-semantic-mismatch",
)


class NotificationOutboxAuthority(str, Enum):
    NOTIFICATION_DELIVERY_SERVER = "NOTIFICATION_DELIVERY_SERVER"


class NotificationOutboxLifecycleStatus(str, Enum):
    PLANNED = "PLANNED"


class NotificationOutboxCreationStatus(str, Enum):
    CREATED = "CREATED"
    REPLAYED = "REPLAYED"
    BLOCKED_ELIGIBILITY = "BLOCKED_ELIGIBILITY"
    IDEMPOTENCY_MISMATCH = "IDEMPOTENCY_MISMATCH"


def _require_text(value: object, field_name: str) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-blank string")
    return value


def _require_optional_text(value: object, field_name: str) -> str | None:
    if value is None:
        return None
    return _require_text(value, field_name)


def _require_bool(value: object, field_name: str) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _require_int(value: object, field_name: str) -> int:
    if type(value) is not int or value < 0:
        raise ValueError(f"{field_name} must be a non-negative integer")
    return value


def _require_tuple_text(
    value: object,
    field_name: str,
    *,
    unique: bool,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")

    validated = tuple(_require_text(item, field_name) for item in value)
    if unique and len(set(validated)) != len(validated):
        raise ValueError(f"{field_name} must not contain duplicate values")
    return validated


def _require_idempotency_value(
    value: object,
    field_name: str,
    expected_type: type,
) -> object:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be {expected_type.__name__}")
    return value


def _require_enum_value(value: object, field_name: str, expected_type: type[Enum]) -> Enum:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be {expected_type.__name__}")
    return value


def _require_reason_codes(value: object, field_name: str) -> tuple[str, ...]:
    reason_codes = _require_tuple_text(value, field_name, unique=True)
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    if any(code not in _OUTBOX_REASON_CODES for code in reason_codes):
        raise ValueError(f"{field_name} contains unsupported outbox reason codes")
    return reason_codes


@dataclass(frozen=True, slots=True)
class NotificationOutboxChannelIntent:
    channel_class: NotificationChannelClass
    target_reference_id: str
    evidence_reference_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if type(self.channel_class) is not NotificationChannelClass:
            raise ValueError("channel_class must be NotificationChannelClass")
        if self.channel_class not in _ALLOWED_PUSH_CHANNEL_CLASSES:
            raise ValueError("channel_class must be TELEGRAM or MAX")
        _require_text(self.target_reference_id, "target_reference_id")
        _require_tuple_text(self.evidence_reference_ids, "evidence_reference_ids", unique=True)


@dataclass(frozen=True, slots=True)
class NotificationOutboxItem:
    outbox_item_id: str
    authority: NotificationOutboxAuthority
    outbox_contract: str
    outbox_contract_version: str
    eligibility_decision_id: str
    source_event_id: str
    source_fact_id: str
    source_commit_reference: str
    source_producer: NotificationSourceProducer
    source_contract: str
    source_contract_version: str
    account_id: str
    beacon_id: str | None
    scan_run_id: str | None
    event_reason: NotificationSourceFamily
    listing_count: int
    safe_listing_reference_ids: tuple[str, ...]
    channel_intents: tuple[NotificationOutboxChannelIntent, ...]
    idempotency_key: IdempotencyKey
    idempotency_fingerprint: IdempotencyFingerprint
    idempotency_scope: IdempotencyScope
    lifecycle_status: NotificationOutboxLifecycleStatus
    correlation_id: str
    causation_id: str
    evidence_reference_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_text(self.outbox_item_id, "outbox_item_id")
        if type(self.authority) is not NotificationOutboxAuthority:
            raise ValueError("authority must be NotificationOutboxAuthority")
        _require_text(self.outbox_contract, "outbox_contract")
        _require_text(self.outbox_contract_version, "outbox_contract_version")
        _require_text(self.eligibility_decision_id, "eligibility_decision_id")
        _require_text(self.source_event_id, "source_event_id")
        _require_text(self.source_fact_id, "source_fact_id")
        _require_text(self.source_commit_reference, "source_commit_reference")
        if type(self.source_producer) is not NotificationSourceProducer:
            raise ValueError("source_producer must be NotificationSourceProducer")
        _require_text(self.source_contract, "source_contract")
        _require_text(self.source_contract_version, "source_contract_version")
        _require_text(self.account_id, "account_id")
        _require_optional_text(self.beacon_id, "beacon_id")
        _require_optional_text(self.scan_run_id, "scan_run_id")
        if type(self.event_reason) is not NotificationSourceFamily:
            raise ValueError("event_reason must be NotificationSourceFamily")
        _require_int(self.listing_count, "listing_count")
        _require_tuple_text(
            self.safe_listing_reference_ids, "safe_listing_reference_ids", unique=True
        )
        if type(self.channel_intents) is not tuple or not self.channel_intents:
            raise ValueError("channel_intents must be a non-empty tuple")
        if type(self.idempotency_key) is not IdempotencyKey:
            raise ValueError("idempotency_key must be IdempotencyKey")
        if type(self.idempotency_fingerprint) is not IdempotencyFingerprint:
            raise ValueError("idempotency_fingerprint must be IdempotencyFingerprint")
        if type(self.idempotency_scope) is not IdempotencyScope:
            raise ValueError("idempotency_scope must be IdempotencyScope")
        if type(self.lifecycle_status) is not NotificationOutboxLifecycleStatus:
            raise ValueError("lifecycle_status must be NotificationOutboxLifecycleStatus")
        _require_text(self.correlation_id, "correlation_id")
        _require_text(self.causation_id, "causation_id")
        _require_tuple_text(self.evidence_reference_ids, "evidence_reference_ids", unique=True)

        for channel_intent in self.channel_intents:
            if type(channel_intent) is not NotificationOutboxChannelIntent:
                raise ValueError("channel_intents must contain NotificationOutboxChannelIntent")

        channel_classes = tuple(intent.channel_class for intent in self.channel_intents)
        if len(set(channel_classes)) != len(channel_classes):
            raise ValueError("channel_intents must not contain duplicate channel classes")
        if any(
            channel_class not in _ALLOWED_PUSH_CHANNEL_CLASSES for channel_class in channel_classes
        ):
            raise ValueError("channel_intents must contain only Telegram or MAX channels")
        if self.listing_count != len(self.safe_listing_reference_ids):
            raise ValueError("listing_count must match safe_listing_reference_ids")
        if self.lifecycle_status is not NotificationOutboxLifecycleStatus.PLANNED:
            raise ValueError("lifecycle_status must be PLANNED")


@dataclass(frozen=True, slots=True)
class NotificationOutboxCreationDecision:
    decision_id: str
    authority: NotificationOutboxAuthority
    eligibility_decision: NotificationEligibilityDecision
    status: NotificationOutboxCreationStatus
    outbox_item: NotificationOutboxItem | None
    outbox_item_created: bool
    replayed: bool
    idempotency_decision: IdempotencyDecision | None
    delivery_attempt_authorized: bool
    reason_codes: tuple[str, ...]
    evidence_reference_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_text(self.decision_id, "decision_id")
        if type(self.authority) is not NotificationOutboxAuthority:
            raise ValueError("authority must be NotificationOutboxAuthority")
        if type(self.eligibility_decision) is not NotificationEligibilityDecision:
            raise ValueError("eligibility_decision must be NotificationEligibilityDecision")
        if type(self.status) is not NotificationOutboxCreationStatus:
            raise ValueError("status must be NotificationOutboxCreationStatus")
        if self.outbox_item is not None and type(self.outbox_item) is not NotificationOutboxItem:
            raise ValueError("outbox_item must be NotificationOutboxItem | None")
        _require_bool(self.outbox_item_created, "outbox_item_created")
        _require_bool(self.replayed, "replayed")
        if (
            self.idempotency_decision is not None
            and type(self.idempotency_decision) is not IdempotencyDecision
        ):
            raise ValueError("idempotency_decision must be IdempotencyDecision | None")
        _require_bool(self.delivery_attempt_authorized, "delivery_attempt_authorized")
        _require_reason_codes(self.reason_codes, "reason_codes")
        _require_tuple_text(self.evidence_reference_ids, "evidence_reference_ids", unique=True)

        if self.delivery_attempt_authorized:
            raise ValueError("delivery_attempt_authorized must be False")

        if self.status is NotificationOutboxCreationStatus.CREATED:
            if self.outbox_item is None or not self.outbox_item_created or self.replayed:
                raise ValueError("created decisions require a new outbox item")
            if self.idempotency_decision is not IdempotencyDecision.NEW:
                raise ValueError("created decisions require NEW idempotency")
            if self.reason_codes != ("outbox-created",):
                raise ValueError("created decisions require outbox-created")
            return

        if self.status is NotificationOutboxCreationStatus.REPLAYED:
            if self.outbox_item is None or self.outbox_item_created or not self.replayed:
                raise ValueError("replayed decisions require the original outbox item")
            if self.idempotency_decision is not IdempotencyDecision.REPLAY_TERMINAL:
                raise ValueError("replayed decisions require replay idempotency")
            if self.reason_codes != ("outbox-replayed",):
                raise ValueError("replayed decisions require outbox-replayed")
            return

        if self.status is NotificationOutboxCreationStatus.BLOCKED_ELIGIBILITY:
            if self.outbox_item is not None or self.outbox_item_created or self.replayed:
                raise ValueError("blocked decisions must not carry an outbox item")
            if self.idempotency_decision is not None:
                raise ValueError("blocked decisions must not carry idempotency decisions")
            if self.reason_codes != ("outbox-eligibility-blocked",):
                raise ValueError("blocked decisions require outbox-eligibility-blocked")
            return

        if self.status is NotificationOutboxCreationStatus.IDEMPOTENCY_MISMATCH:
            if self.outbox_item is not None or self.outbox_item_created or self.replayed:
                raise ValueError("mismatch decisions must not carry an outbox item")
            if self.idempotency_decision is not IdempotencyDecision.MISMATCH:
                raise ValueError("mismatch decisions require mismatch idempotency")
            if self.reason_codes not in (
                ("outbox-idempotency-fingerprint-mismatch",),
                ("outbox-idempotency-semantic-mismatch",),
            ):
                raise ValueError("mismatch decisions require a supported mismatch reason")


def _channel_intent_from_gate(
    gate: NotificationChannelGateDecision,
) -> NotificationOutboxChannelIntent:
    if type(gate) is not NotificationChannelGateDecision:
        raise ValueError("channel gate must be NotificationChannelGateDecision")
    if gate.channel_class not in _ALLOWED_PUSH_CHANNEL_CLASSES:
        raise ValueError("eligible push channels must be Telegram or MAX")
    if gate.status is not NotificationChannelGateStatus.ELIGIBLE or not gate.push_eligible:
        raise ValueError("eligible push channel gates must be eligible")
    if gate.target_reference_id is None:
        raise ValueError("eligible push channel gates require a target reference")
    return NotificationOutboxChannelIntent(
        channel_class=gate.channel_class,
        target_reference_id=gate.target_reference_id,
        evidence_reference_ids=gate.evidence_reference_ids,
    )


def _build_channel_intents(
    eligibility_decision: NotificationEligibilityDecision,
) -> tuple[NotificationOutboxChannelIntent, ...]:
    gate_by_channel_class = {
        gate.channel_class: gate
        for gate in eligibility_decision.channel_gate_decisions
        if gate.push_eligible
    }
    return tuple(
        _channel_intent_from_gate(gate_by_channel_class[channel_class])
        for channel_class in eligibility_decision.eligible_push_channels
    )


def _item_semantics(
    *,
    outbox_contract: str,
    outbox_contract_version: str,
    eligibility_decision: NotificationEligibilityDecision,
    idempotency_key: IdempotencyKey,
    idempotency_fingerprint: IdempotencyFingerprint,
    idempotency_scope: IdempotencyScope,
    channel_intents: tuple[NotificationOutboxChannelIntent, ...],
) -> tuple[object, ...]:
    source_event = eligibility_decision.source_intake_decision.source_event
    source_commit_reference = _require_text(
        source_event.source_commit_reference,
        "source_commit_reference",
    )
    return (
        NotificationOutboxAuthority.NOTIFICATION_DELIVERY_SERVER,
        outbox_contract,
        outbox_contract_version,
        eligibility_decision.decision_id,
        source_event.source_event_id,
        source_event.source_fact_id,
        source_commit_reference,
        source_event.source_producer,
        source_event.source_contract,
        source_event.source_contract_version,
        source_event.account_id,
        source_event.beacon_id,
        source_event.scan_run_id,
        source_event.source_family,
        source_event.listing_count,
        source_event.safe_listing_reference_ids,
        channel_intents,
        idempotency_key,
        idempotency_fingerprint,
        idempotency_scope,
        NotificationOutboxLifecycleStatus.PLANNED,
        source_event.correlation_id,
        source_event.causation_id,
    )


def _item_semantics_from_item(
    item: NotificationOutboxItem,
) -> tuple[object, ...]:
    return (
        item.authority,
        item.outbox_contract,
        item.outbox_contract_version,
        item.eligibility_decision_id,
        item.source_event_id,
        item.source_fact_id,
        item.source_commit_reference,
        item.source_producer,
        item.source_contract,
        item.source_contract_version,
        item.account_id,
        item.beacon_id,
        item.scan_run_id,
        item.event_reason,
        item.listing_count,
        item.safe_listing_reference_ids,
        item.channel_intents,
        item.idempotency_key,
        item.idempotency_fingerprint,
        item.idempotency_scope,
        item.lifecycle_status,
        item.correlation_id,
        item.causation_id,
    )


def _item_from_request(
    *,
    outbox_item_id: str,
    outbox_contract: str,
    outbox_contract_version: str,
    eligibility_decision: NotificationEligibilityDecision,
    idempotency_key: IdempotencyKey,
    idempotency_fingerprint: IdempotencyFingerprint,
    idempotency_scope: IdempotencyScope,
    evidence_reference_ids: tuple[str, ...],
) -> NotificationOutboxItem:
    source_event = eligibility_decision.source_intake_decision.source_event
    source_commit_reference = _require_text(
        source_event.source_commit_reference,
        "source_commit_reference",
    )
    channel_intents = _build_channel_intents(eligibility_decision)
    return NotificationOutboxItem(
        outbox_item_id=outbox_item_id,
        authority=NotificationOutboxAuthority.NOTIFICATION_DELIVERY_SERVER,
        outbox_contract=outbox_contract,
        outbox_contract_version=outbox_contract_version,
        eligibility_decision_id=eligibility_decision.decision_id,
        source_event_id=source_event.source_event_id,
        source_fact_id=source_event.source_fact_id,
        source_commit_reference=source_commit_reference,
        source_producer=source_event.source_producer,
        source_contract=source_event.source_contract,
        source_contract_version=source_event.source_contract_version,
        account_id=source_event.account_id,
        beacon_id=source_event.beacon_id,
        scan_run_id=source_event.scan_run_id,
        event_reason=source_event.source_family,
        listing_count=source_event.listing_count,
        safe_listing_reference_ids=source_event.safe_listing_reference_ids,
        channel_intents=channel_intents,
        idempotency_key=idempotency_key,
        idempotency_fingerprint=idempotency_fingerprint,
        idempotency_scope=idempotency_scope,
        lifecycle_status=NotificationOutboxLifecycleStatus.PLANNED,
        correlation_id=source_event.correlation_id,
        causation_id=source_event.causation_id,
        evidence_reference_ids=evidence_reference_ids,
    )


def _eligible_for_creation(eligibility_decision: NotificationEligibilityDecision) -> bool:
    return (
        eligibility_decision.status
        in (
            NotificationEligibilityStatus.ELIGIBLE,
            NotificationEligibilityStatus.ELIGIBLE_RECOVERY_GRACE,
        )
        and eligibility_decision.source_eligible
        and eligibility_decision.outbox_candidate_eligible
        and bool(eligibility_decision.eligible_push_channels)
        and not eligibility_decision.delivery_attempt_authorized
    )


def _blocked_decision(
    *,
    decision_id: str,
    eligibility_decision: NotificationEligibilityDecision,
    evidence_reference_ids: tuple[str, ...],
) -> NotificationOutboxCreationDecision:
    return NotificationOutboxCreationDecision(
        decision_id=decision_id,
        authority=NotificationOutboxAuthority.NOTIFICATION_DELIVERY_SERVER,
        eligibility_decision=eligibility_decision,
        status=NotificationOutboxCreationStatus.BLOCKED_ELIGIBILITY,
        outbox_item=None,
        outbox_item_created=False,
        replayed=False,
        idempotency_decision=None,
        delivery_attempt_authorized=False,
        reason_codes=("outbox-eligibility-blocked",),
        evidence_reference_ids=evidence_reference_ids,
    )


def _mismatch_decision(
    *,
    decision_id: str,
    eligibility_decision: NotificationEligibilityDecision,
    status: NotificationOutboxCreationStatus,
    reason_code: str,
    evidence_reference_ids: tuple[str, ...],
) -> NotificationOutboxCreationDecision:
    return NotificationOutboxCreationDecision(
        decision_id=decision_id,
        authority=NotificationOutboxAuthority.NOTIFICATION_DELIVERY_SERVER,
        eligibility_decision=eligibility_decision,
        status=status,
        outbox_item=None,
        outbox_item_created=False,
        replayed=False,
        idempotency_decision=IdempotencyDecision.MISMATCH,
        delivery_attempt_authorized=False,
        reason_codes=(reason_code,),
        evidence_reference_ids=evidence_reference_ids,
    )


def _replay_decision(
    *,
    decision_id: str,
    eligibility_decision: NotificationEligibilityDecision,
    outbox_item: NotificationOutboxItem,
    evidence_reference_ids: tuple[str, ...],
) -> NotificationOutboxCreationDecision:
    return NotificationOutboxCreationDecision(
        decision_id=decision_id,
        authority=NotificationOutboxAuthority.NOTIFICATION_DELIVERY_SERVER,
        eligibility_decision=eligibility_decision,
        status=NotificationOutboxCreationStatus.REPLAYED,
        outbox_item=outbox_item,
        outbox_item_created=False,
        replayed=True,
        idempotency_decision=IdempotencyDecision.REPLAY_TERMINAL,
        delivery_attempt_authorized=False,
        reason_codes=("outbox-replayed",),
        evidence_reference_ids=evidence_reference_ids,
    )


def _created_decision(
    *,
    decision_id: str,
    eligibility_decision: NotificationEligibilityDecision,
    outbox_item: NotificationOutboxItem,
    evidence_reference_ids: tuple[str, ...],
) -> NotificationOutboxCreationDecision:
    return NotificationOutboxCreationDecision(
        decision_id=decision_id,
        authority=NotificationOutboxAuthority.NOTIFICATION_DELIVERY_SERVER,
        eligibility_decision=eligibility_decision,
        status=NotificationOutboxCreationStatus.CREATED,
        outbox_item=outbox_item,
        outbox_item_created=True,
        replayed=False,
        idempotency_decision=IdempotencyDecision.NEW,
        delivery_attempt_authorized=False,
        reason_codes=("outbox-created",),
        evidence_reference_ids=evidence_reference_ids,
    )


def create_notification_outbox_item(
    *,
    decision_id: str,
    outbox_item_id: str,
    outbox_contract: str,
    outbox_contract_version: str,
    eligibility_decision: NotificationEligibilityDecision,
    idempotency_key: IdempotencyKey,
    idempotency_fingerprint: IdempotencyFingerprint,
    idempotency_scope: IdempotencyScope,
    existing_outbox_item: NotificationOutboxItem | None,
    evidence_reference_ids: tuple[str, ...],
) -> NotificationOutboxCreationDecision:
    _require_text(decision_id, "decision_id")
    _require_text(outbox_item_id, "outbox_item_id")
    _require_text(outbox_contract, "outbox_contract")
    _require_text(outbox_contract_version, "outbox_contract_version")
    if type(eligibility_decision) is not NotificationEligibilityDecision:
        raise ValueError("eligibility_decision must be NotificationEligibilityDecision")
    _require_idempotency_value(idempotency_key, "idempotency_key", IdempotencyKey)
    _require_idempotency_value(
        idempotency_fingerprint,
        "idempotency_fingerprint",
        IdempotencyFingerprint,
    )
    _require_idempotency_value(idempotency_scope, "idempotency_scope", IdempotencyScope)
    if (
        existing_outbox_item is not None
        and type(existing_outbox_item) is not NotificationOutboxItem
    ):
        raise ValueError("existing_outbox_item must be NotificationOutboxItem | None")
    _require_tuple_text(evidence_reference_ids, "evidence_reference_ids", unique=True)

    if existing_outbox_item is None:
        if not _eligible_for_creation(eligibility_decision):
            return _blocked_decision(
                decision_id=decision_id,
                eligibility_decision=eligibility_decision,
                evidence_reference_ids=evidence_reference_ids,
            )
        outbox_item = _item_from_request(
            outbox_item_id=outbox_item_id,
            outbox_contract=outbox_contract,
            outbox_contract_version=outbox_contract_version,
            eligibility_decision=eligibility_decision,
            idempotency_key=idempotency_key,
            idempotency_fingerprint=idempotency_fingerprint,
            idempotency_scope=idempotency_scope,
            evidence_reference_ids=evidence_reference_ids,
        )
        return _created_decision(
            decision_id=decision_id,
            eligibility_decision=eligibility_decision,
            outbox_item=outbox_item,
            evidence_reference_ids=evidence_reference_ids,
        )

    if (
        existing_outbox_item.idempotency_key != idempotency_key
        or existing_outbox_item.idempotency_scope != idempotency_scope
    ):
        raise ValueError("caller supplied an unrelated existing record.")

    if existing_outbox_item.idempotency_fingerprint != idempotency_fingerprint:
        return _mismatch_decision(
            decision_id=decision_id,
            eligibility_decision=eligibility_decision,
            status=NotificationOutboxCreationStatus.IDEMPOTENCY_MISMATCH,
            reason_code="outbox-idempotency-fingerprint-mismatch",
            evidence_reference_ids=evidence_reference_ids,
        )

    requested_semantics = _item_semantics(
        outbox_contract=outbox_contract,
        outbox_contract_version=outbox_contract_version,
        eligibility_decision=eligibility_decision,
        idempotency_key=idempotency_key,
        idempotency_fingerprint=idempotency_fingerprint,
        idempotency_scope=idempotency_scope,
        channel_intents=_build_channel_intents(eligibility_decision),
    )
    existing_semantics = _item_semantics_from_item(existing_outbox_item)

    if requested_semantics == existing_semantics:
        return _replay_decision(
            decision_id=decision_id,
            eligibility_decision=eligibility_decision,
            outbox_item=existing_outbox_item,
            evidence_reference_ids=evidence_reference_ids,
        )

    return _mismatch_decision(
        decision_id=decision_id,
        eligibility_decision=eligibility_decision,
        status=NotificationOutboxCreationStatus.IDEMPOTENCY_MISMATCH,
        reason_code="outbox-idempotency-semantic-mismatch",
        evidence_reference_ids=evidence_reference_ids,
    )


__all__ = (
    "ND04_TASK_ID",
    "NotificationOutboxAuthority",
    "NotificationOutboxLifecycleStatus",
    "NotificationOutboxCreationStatus",
    "NotificationOutboxChannelIntent",
    "NotificationOutboxItem",
    "NotificationOutboxCreationDecision",
    "create_notification_outbox_item",
)
