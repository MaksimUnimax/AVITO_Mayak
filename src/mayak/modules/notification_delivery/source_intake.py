from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from mayak.contracts.idempotency import IdempotencyFingerprint, IdempotencyKey, IdempotencyScope

ND02_TASK_ID = "ND-02-SOURCE-INTAKE-CONTRACTS-20260715-003"


class NotificationSourceProducer(str, Enum):
    SCAN_ORCHESTRATION = "SCAN_ORCHESTRATION"
    ENTITLEMENTS_OR_BEACON = "ENTITLEMENTS_OR_BEACON"
    PARSER_ADAPTER = "PARSER_ADAPTER"
    EGRESS_ROUTING = "EGRESS_ROUTING"
    PROVIDER_ADAPTER = "PROVIDER_ADAPTER"


class NotificationSourceFamily(str, Enum):
    NEW_LISTINGS_FOUND = "NEW_LISTINGS_FOUND"
    RECOVERY_SCAN_COMPLETED = "RECOVERY_SCAN_COMPLETED"
    EXTERNAL_UNAVAILABLE_STATUS = "EXTERNAL_UNAVAILABLE_STATUS"
    LOST_ANCHORS_RECOVERED = "LOST_ANCHORS_RECOVERED"
    NO_NEW_LISTINGS_STATUS = "NO_NEW_LISTINGS_STATUS"
    APPROVED_SERVICE_ACCESS_FACT = "APPROVED_SERVICE_ACCESS_FACT"
    BEACON_BASELINE_ESTABLISHED = "BEACON_BASELINE_ESTABLISHED"
    SCAN_RUN_PLANNED = "SCAN_RUN_PLANNED"
    SCAN_RUN_STARTED = "SCAN_RUN_STARTED"
    LISTING_PRICE_PAIR_FIRST_SEEN = "LISTING_PRICE_PAIR_FIRST_SEEN"
    PARSER_ONLY_OUTCOME = "PARSER_ONLY_OUTCOME"
    EGRESS_ONLY_OUTCOME = "EGRESS_ONLY_OUTCOME"
    PROVIDER_ONLY_CALLBACK = "PROVIDER_ONLY_CALLBACK"


class NotificationSourceIntakeAuthority(str, Enum):
    NOTIFICATION_DELIVERY_SERVER = "NOTIFICATION_DELIVERY_SERVER"


class NotificationSourceIntakeStatus(str, Enum):
    ACCEPTED_NOTIFICATION_CANDIDATE = "ACCEPTED_NOTIFICATION_CANDIDATE"
    ACCEPTED_STATUS_ONLY = "ACCEPTED_STATUS_ONLY"
    BLOCKED_UPSTREAM_GATE = "BLOCKED_UPSTREAM_GATE"
    REJECTED_UNCOMMITTED = "REJECTED_UNCOMMITTED"
    REJECTED_AMBIGUOUS = "REJECTED_AMBIGUOUS"
    REJECTED_UNSAFE_PAYLOAD = "REJECTED_UNSAFE_PAYLOAD"
    REJECTED_DISABLED_SOURCE = "REJECTED_DISABLED_SOURCE"
    REJECTED_NON_NOTIFICATION_SOURCE = "REJECTED_NON_NOTIFICATION_SOURCE"
    REJECTED_INVALID_PRODUCER = "REJECTED_INVALID_PRODUCER"


_SCAN_PRODUCER_FAMILIES = (
    NotificationSourceFamily.NEW_LISTINGS_FOUND,
    NotificationSourceFamily.RECOVERY_SCAN_COMPLETED,
    NotificationSourceFamily.EXTERNAL_UNAVAILABLE_STATUS,
    NotificationSourceFamily.LOST_ANCHORS_RECOVERED,
    NotificationSourceFamily.NO_NEW_LISTINGS_STATUS,
    NotificationSourceFamily.BEACON_BASELINE_ESTABLISHED,
    NotificationSourceFamily.SCAN_RUN_PLANNED,
    NotificationSourceFamily.SCAN_RUN_STARTED,
    NotificationSourceFamily.LISTING_PRICE_PAIR_FIRST_SEEN,
)


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
    expected_type: type[IdempotencyFingerprint | IdempotencyKey | IdempotencyScope],
) -> IdempotencyFingerprint | IdempotencyKey | IdempotencyScope:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be {expected_type.__name__}")
    return value


@dataclass(frozen=True, slots=True)
class NotificationSourceEvent:
    source_event_id: str
    source_family: NotificationSourceFamily
    source_producer: NotificationSourceProducer
    source_contract: str
    source_contract_version: str
    source_fact_id: str
    source_committed: bool
    source_commit_reference: str | None
    account_id: str
    beacon_id: str | None
    scan_run_id: str | None
    listing_count: int
    safe_listing_reference_ids: tuple[str, ...]
    correlation_id: str
    causation_id: str
    idempotency_key: IdempotencyKey
    idempotency_fingerprint: IdempotencyFingerprint
    idempotency_scope: IdempotencyScope
    source_identity_ambiguous: bool
    contains_raw_provider_payload: bool
    service_access_gate_approved: bool
    evidence_reference_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_text(self.source_event_id, "source_event_id")
        if type(self.source_family) is not NotificationSourceFamily:
            raise ValueError("source_family must be NotificationSourceFamily")
        if type(self.source_producer) is not NotificationSourceProducer:
            raise ValueError("source_producer must be NotificationSourceProducer")
        _require_text(self.source_contract, "source_contract")
        _require_text(self.source_contract_version, "source_contract_version")
        _require_text(self.source_fact_id, "source_fact_id")
        _require_bool(self.source_committed, "source_committed")
        if self.source_committed:
            _require_text(self.source_commit_reference, "source_commit_reference")
        else:
            _require_optional_text(self.source_commit_reference, "source_commit_reference")
        _require_text(self.account_id, "account_id")
        _require_optional_text(self.beacon_id, "beacon_id")
        _require_optional_text(self.scan_run_id, "scan_run_id")
        _require_int(self.listing_count, "listing_count")
        _require_tuple_text(
            self.safe_listing_reference_ids,
            "safe_listing_reference_ids",
            unique=True,
        )
        _require_text(self.correlation_id, "correlation_id")
        _require_text(self.causation_id, "causation_id")
        _require_idempotency_value(self.idempotency_key, "idempotency_key", IdempotencyKey)
        _require_idempotency_value(
            self.idempotency_fingerprint,
            "idempotency_fingerprint",
            IdempotencyFingerprint,
        )
        _require_idempotency_value(self.idempotency_scope, "idempotency_scope", IdempotencyScope)
        _require_bool(self.source_identity_ambiguous, "source_identity_ambiguous")
        _require_bool(self.contains_raw_provider_payload, "contains_raw_provider_payload")
        _require_bool(self.service_access_gate_approved, "service_access_gate_approved")
        _require_tuple_text(self.evidence_reference_ids, "evidence_reference_ids", unique=True)

        if self.source_family in (
            NotificationSourceFamily.NEW_LISTINGS_FOUND,
            NotificationSourceFamily.LOST_ANCHORS_RECOVERED,
        ):
            if self.beacon_id is None or self.scan_run_id is None:
                raise ValueError(f"{self.source_family.value} requires beacon_id and scan_run_id")
            if self.listing_count <= 0:
                raise ValueError(f"{self.source_family.value} requires a positive listing_count")
            if self.listing_count != len(self.safe_listing_reference_ids):
                raise ValueError(
                    f"{self.source_family.value} requires listing_count to match safe references"
                )
            if not self.safe_listing_reference_ids:
                raise ValueError(f"{self.source_family.value} requires safe_listing_reference_ids")
        elif self.source_family is NotificationSourceFamily.RECOVERY_SCAN_COMPLETED:
            if self.beacon_id is None or self.scan_run_id is None:
                raise ValueError("RECOVERY_SCAN_COMPLETED requires beacon_id and scan_run_id")
            if self.listing_count != len(self.safe_listing_reference_ids):
                raise ValueError(
                    "RECOVERY_SCAN_COMPLETED requires listing_count to match safe references"
                )
        elif self.source_family in (
            NotificationSourceFamily.EXTERNAL_UNAVAILABLE_STATUS,
            NotificationSourceFamily.NO_NEW_LISTINGS_STATUS,
        ):
            if self.beacon_id is None or self.scan_run_id is None:
                raise ValueError(f"{self.source_family.value} requires beacon_id and scan_run_id")
            if self.listing_count != 0:
                raise ValueError(f"{self.source_family.value} requires zero listing_count")
            if self.safe_listing_reference_ids:
                raise ValueError(
                    f"{self.source_family.value} requires empty safe_listing_reference_ids"
                )


@dataclass(frozen=True, slots=True)
class NotificationSourceIntakeDecision:
    decision_id: str
    authority: NotificationSourceIntakeAuthority
    source_event: NotificationSourceEvent
    status: NotificationSourceIntakeStatus
    source_accepted: bool
    notification_candidate: bool
    status_read_model_candidate: bool
    outbox_effect_authorized: bool
    delivery_attempt_authorized: bool
    reason_codes: tuple[str, ...]
    evidence_reference_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_text(self.decision_id, "decision_id")
        if type(self.authority) is not NotificationSourceIntakeAuthority:
            raise ValueError("authority must be NotificationSourceIntakeAuthority")
        if type(self.source_event) is not NotificationSourceEvent:
            raise ValueError("source_event must be NotificationSourceEvent")
        if type(self.status) is not NotificationSourceIntakeStatus:
            raise ValueError("status must be NotificationSourceIntakeStatus")
        _require_bool(self.source_accepted, "source_accepted")
        _require_bool(self.notification_candidate, "notification_candidate")
        _require_bool(self.status_read_model_candidate, "status_read_model_candidate")
        _require_bool(self.outbox_effect_authorized, "outbox_effect_authorized")
        _require_bool(self.delivery_attempt_authorized, "delivery_attempt_authorized")
        _require_tuple_text(self.reason_codes, "reason_codes", unique=False)
        _require_tuple_text(self.evidence_reference_ids, "evidence_reference_ids", unique=False)

        if self.outbox_effect_authorized or self.delivery_attempt_authorized:
            raise ValueError("ND-02 decisions must not authorize outbox or delivery attempts")

        if self.status is NotificationSourceIntakeStatus.ACCEPTED_NOTIFICATION_CANDIDATE:
            if (
                not self.source_accepted
                or not self.notification_candidate
                or not self.status_read_model_candidate
            ):
                raise ValueError("accepted notification candidates require all acceptance flags")
        elif self.status is NotificationSourceIntakeStatus.ACCEPTED_STATUS_ONLY:
            if (
                not self.source_accepted
                or self.notification_candidate
                or not self.status_read_model_candidate
            ):
                raise ValueError(
                    "accepted status-only decisions require read-model-only acceptance"
                )
        elif self.status is NotificationSourceIntakeStatus.BLOCKED_UPSTREAM_GATE:
            if (
                self.source_accepted
                or self.notification_candidate
                or self.status_read_model_candidate
            ):
                raise ValueError("blocked decisions must not mark source acceptance")
        else:
            if (
                self.source_accepted
                or self.notification_candidate
                or self.status_read_model_candidate
            ):
                raise ValueError("rejected decisions must not mark source acceptance")


def _produce_invalid_producer_decision(
    *,
    decision_id: str,
    source_event: NotificationSourceEvent,
    evidence_reference_ids: tuple[str, ...],
) -> NotificationSourceIntakeDecision:
    return NotificationSourceIntakeDecision(
        decision_id=decision_id,
        authority=NotificationSourceIntakeAuthority.NOTIFICATION_DELIVERY_SERVER,
        source_event=source_event,
        status=NotificationSourceIntakeStatus.REJECTED_INVALID_PRODUCER,
        source_accepted=False,
        notification_candidate=False,
        status_read_model_candidate=False,
        outbox_effect_authorized=False,
        delivery_attempt_authorized=False,
        reason_codes=("source-producer-mismatch",),
        evidence_reference_ids=evidence_reference_ids,
    )


def evaluate_notification_source_intake(
    *,
    decision_id: str,
    source_event: NotificationSourceEvent,
    evidence_reference_ids: tuple[str, ...],
) -> NotificationSourceIntakeDecision:
    _require_text(decision_id, "decision_id")
    _require_tuple_text(evidence_reference_ids, "evidence_reference_ids", unique=False)

    if source_event.contains_raw_provider_payload:
        return NotificationSourceIntakeDecision(
            decision_id=decision_id,
            authority=NotificationSourceIntakeAuthority.NOTIFICATION_DELIVERY_SERVER,
            source_event=source_event,
            status=NotificationSourceIntakeStatus.REJECTED_UNSAFE_PAYLOAD,
            source_accepted=False,
            notification_candidate=False,
            status_read_model_candidate=False,
            outbox_effect_authorized=False,
            delivery_attempt_authorized=False,
            reason_codes=("source-contains-raw-provider-payload",),
            evidence_reference_ids=evidence_reference_ids,
        )

    if source_event.source_identity_ambiguous:
        return NotificationSourceIntakeDecision(
            decision_id=decision_id,
            authority=NotificationSourceIntakeAuthority.NOTIFICATION_DELIVERY_SERVER,
            source_event=source_event,
            status=NotificationSourceIntakeStatus.REJECTED_AMBIGUOUS,
            source_accepted=False,
            notification_candidate=False,
            status_read_model_candidate=False,
            outbox_effect_authorized=False,
            delivery_attempt_authorized=False,
            reason_codes=("source-identity-ambiguous",),
            evidence_reference_ids=evidence_reference_ids,
        )

    if not source_event.source_committed or source_event.source_commit_reference is None:
        return NotificationSourceIntakeDecision(
            decision_id=decision_id,
            authority=NotificationSourceIntakeAuthority.NOTIFICATION_DELIVERY_SERVER,
            source_event=source_event,
            status=NotificationSourceIntakeStatus.REJECTED_UNCOMMITTED,
            source_accepted=False,
            notification_candidate=False,
            status_read_model_candidate=False,
            outbox_effect_authorized=False,
            delivery_attempt_authorized=False,
            reason_codes=("source-uncommitted",),
            evidence_reference_ids=evidence_reference_ids,
        )

    if source_event.source_family in _SCAN_PRODUCER_FAMILIES:
        expected_producer = NotificationSourceProducer.SCAN_ORCHESTRATION
    elif source_event.source_family is NotificationSourceFamily.APPROVED_SERVICE_ACCESS_FACT:
        expected_producer = NotificationSourceProducer.ENTITLEMENTS_OR_BEACON
    elif source_event.source_family is NotificationSourceFamily.PARSER_ONLY_OUTCOME:
        expected_producer = NotificationSourceProducer.PARSER_ADAPTER
    elif source_event.source_family is NotificationSourceFamily.EGRESS_ONLY_OUTCOME:
        expected_producer = NotificationSourceProducer.EGRESS_ROUTING
    elif source_event.source_family is NotificationSourceFamily.PROVIDER_ONLY_CALLBACK:
        expected_producer = NotificationSourceProducer.PROVIDER_ADAPTER
    else:
        expected_producer = source_event.source_producer

    if source_event.source_producer is not expected_producer:
        return _produce_invalid_producer_decision(
            decision_id=decision_id,
            source_event=source_event,
            evidence_reference_ids=evidence_reference_ids,
        )

    if source_event.source_family is NotificationSourceFamily.NEW_LISTINGS_FOUND:
        return NotificationSourceIntakeDecision(
            decision_id=decision_id,
            authority=NotificationSourceIntakeAuthority.NOTIFICATION_DELIVERY_SERVER,
            source_event=source_event,
            status=NotificationSourceIntakeStatus.ACCEPTED_NOTIFICATION_CANDIDATE,
            source_accepted=True,
            notification_candidate=True,
            status_read_model_candidate=True,
            outbox_effect_authorized=False,
            delivery_attempt_authorized=False,
            reason_codes=("source-accepted-new-listings",),
            evidence_reference_ids=evidence_reference_ids,
        )
    if source_event.source_family is NotificationSourceFamily.RECOVERY_SCAN_COMPLETED:
        return NotificationSourceIntakeDecision(
            decision_id=decision_id,
            authority=NotificationSourceIntakeAuthority.NOTIFICATION_DELIVERY_SERVER,
            source_event=source_event,
            status=NotificationSourceIntakeStatus.ACCEPTED_NOTIFICATION_CANDIDATE,
            source_accepted=True,
            notification_candidate=True,
            status_read_model_candidate=True,
            outbox_effect_authorized=False,
            delivery_attempt_authorized=False,
            reason_codes=("source-accepted-recovery-result",),
            evidence_reference_ids=evidence_reference_ids,
        )
    if source_event.source_family is NotificationSourceFamily.EXTERNAL_UNAVAILABLE_STATUS:
        return NotificationSourceIntakeDecision(
            decision_id=decision_id,
            authority=NotificationSourceIntakeAuthority.NOTIFICATION_DELIVERY_SERVER,
            source_event=source_event,
            status=NotificationSourceIntakeStatus.ACCEPTED_NOTIFICATION_CANDIDATE,
            source_accepted=True,
            notification_candidate=True,
            status_read_model_candidate=True,
            outbox_effect_authorized=False,
            delivery_attempt_authorized=False,
            reason_codes=("source-accepted-external-status",),
            evidence_reference_ids=evidence_reference_ids,
        )
    if source_event.source_family is NotificationSourceFamily.LOST_ANCHORS_RECOVERED:
        return NotificationSourceIntakeDecision(
            decision_id=decision_id,
            authority=NotificationSourceIntakeAuthority.NOTIFICATION_DELIVERY_SERVER,
            source_event=source_event,
            status=NotificationSourceIntakeStatus.ACCEPTED_NOTIFICATION_CANDIDATE,
            source_accepted=True,
            notification_candidate=True,
            status_read_model_candidate=True,
            outbox_effect_authorized=False,
            delivery_attempt_authorized=False,
            reason_codes=("source-accepted-lost-anchors-state-restored",),
            evidence_reference_ids=evidence_reference_ids,
        )
    if source_event.source_family is NotificationSourceFamily.NO_NEW_LISTINGS_STATUS:
        return NotificationSourceIntakeDecision(
            decision_id=decision_id,
            authority=NotificationSourceIntakeAuthority.NOTIFICATION_DELIVERY_SERVER,
            source_event=source_event,
            status=NotificationSourceIntakeStatus.ACCEPTED_STATUS_ONLY,
            source_accepted=True,
            notification_candidate=False,
            status_read_model_candidate=True,
            outbox_effect_authorized=False,
            delivery_attempt_authorized=False,
            reason_codes=("source-accepted-status-only-no-new",),
            evidence_reference_ids=evidence_reference_ids,
        )
    if source_event.source_family is NotificationSourceFamily.APPROVED_SERVICE_ACCESS_FACT:
        if not source_event.service_access_gate_approved:
            return NotificationSourceIntakeDecision(
                decision_id=decision_id,
                authority=NotificationSourceIntakeAuthority.NOTIFICATION_DELIVERY_SERVER,
                source_event=source_event,
                status=NotificationSourceIntakeStatus.BLOCKED_UPSTREAM_GATE,
                source_accepted=False,
                notification_candidate=False,
                status_read_model_candidate=False,
                outbox_effect_authorized=False,
                delivery_attempt_authorized=False,
                reason_codes=("source-blocked-service-access-gate",),
                evidence_reference_ids=evidence_reference_ids,
            )
        return NotificationSourceIntakeDecision(
            decision_id=decision_id,
            authority=NotificationSourceIntakeAuthority.NOTIFICATION_DELIVERY_SERVER,
            source_event=source_event,
            status=NotificationSourceIntakeStatus.ACCEPTED_NOTIFICATION_CANDIDATE,
            source_accepted=True,
            notification_candidate=True,
            status_read_model_candidate=True,
            outbox_effect_authorized=False,
            delivery_attempt_authorized=False,
            reason_codes=("source-accepted-service-access",),
            evidence_reference_ids=evidence_reference_ids,
        )
    if source_event.source_family is NotificationSourceFamily.LISTING_PRICE_PAIR_FIRST_SEEN:
        return NotificationSourceIntakeDecision(
            decision_id=decision_id,
            authority=NotificationSourceIntakeAuthority.NOTIFICATION_DELIVERY_SERVER,
            source_event=source_event,
            status=NotificationSourceIntakeStatus.REJECTED_DISABLED_SOURCE,
            source_accepted=False,
            notification_candidate=False,
            status_read_model_candidate=False,
            outbox_effect_authorized=False,
            delivery_attempt_authorized=False,
            reason_codes=("source-disabled-price-change",),
            evidence_reference_ids=evidence_reference_ids,
        )
    if source_event.source_family is NotificationSourceFamily.BEACON_BASELINE_ESTABLISHED:
        return NotificationSourceIntakeDecision(
            decision_id=decision_id,
            authority=NotificationSourceIntakeAuthority.NOTIFICATION_DELIVERY_SERVER,
            source_event=source_event,
            status=NotificationSourceIntakeStatus.REJECTED_NON_NOTIFICATION_SOURCE,
            source_accepted=False,
            notification_candidate=False,
            status_read_model_candidate=False,
            outbox_effect_authorized=False,
            delivery_attempt_authorized=False,
            reason_codes=("source-non-notification-baseline",),
            evidence_reference_ids=evidence_reference_ids,
        )
    if source_event.source_family in (
        NotificationSourceFamily.SCAN_RUN_PLANNED,
        NotificationSourceFamily.SCAN_RUN_STARTED,
    ):
        return NotificationSourceIntakeDecision(
            decision_id=decision_id,
            authority=NotificationSourceIntakeAuthority.NOTIFICATION_DELIVERY_SERVER,
            source_event=source_event,
            status=NotificationSourceIntakeStatus.REJECTED_NON_NOTIFICATION_SOURCE,
            source_accepted=False,
            notification_candidate=False,
            status_read_model_candidate=False,
            outbox_effect_authorized=False,
            delivery_attempt_authorized=False,
            reason_codes=("source-non-notification-scan-lifecycle",),
            evidence_reference_ids=evidence_reference_ids,
        )
    if source_event.source_family is NotificationSourceFamily.PARSER_ONLY_OUTCOME:
        return NotificationSourceIntakeDecision(
            decision_id=decision_id,
            authority=NotificationSourceIntakeAuthority.NOTIFICATION_DELIVERY_SERVER,
            source_event=source_event,
            status=NotificationSourceIntakeStatus.REJECTED_NON_NOTIFICATION_SOURCE,
            source_accepted=False,
            notification_candidate=False,
            status_read_model_candidate=False,
            outbox_effect_authorized=False,
            delivery_attempt_authorized=False,
            reason_codes=("source-non-notification-parser",),
            evidence_reference_ids=evidence_reference_ids,
        )
    if source_event.source_family is NotificationSourceFamily.EGRESS_ONLY_OUTCOME:
        return NotificationSourceIntakeDecision(
            decision_id=decision_id,
            authority=NotificationSourceIntakeAuthority.NOTIFICATION_DELIVERY_SERVER,
            source_event=source_event,
            status=NotificationSourceIntakeStatus.REJECTED_NON_NOTIFICATION_SOURCE,
            source_accepted=False,
            notification_candidate=False,
            status_read_model_candidate=False,
            outbox_effect_authorized=False,
            delivery_attempt_authorized=False,
            reason_codes=("source-non-notification-egress",),
            evidence_reference_ids=evidence_reference_ids,
        )
    if source_event.source_family is NotificationSourceFamily.PROVIDER_ONLY_CALLBACK:
        return NotificationSourceIntakeDecision(
            decision_id=decision_id,
            authority=NotificationSourceIntakeAuthority.NOTIFICATION_DELIVERY_SERVER,
            source_event=source_event,
            status=NotificationSourceIntakeStatus.REJECTED_NON_NOTIFICATION_SOURCE,
            source_accepted=False,
            notification_candidate=False,
            status_read_model_candidate=False,
            outbox_effect_authorized=False,
            delivery_attempt_authorized=False,
            reason_codes=("source-non-notification-provider-callback",),
            evidence_reference_ids=evidence_reference_ids,
        )

    raise ValueError("unsupported notification source family")


__all__ = (
    "ND02_TASK_ID",
    "NotificationSourceProducer",
    "NotificationSourceFamily",
    "NotificationSourceIntakeAuthority",
    "NotificationSourceIntakeStatus",
    "NotificationSourceEvent",
    "NotificationSourceIntakeDecision",
    "evaluate_notification_source_intake",
)
