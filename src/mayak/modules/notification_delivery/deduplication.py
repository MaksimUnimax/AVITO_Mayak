from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from mayak.contracts.idempotency import IdempotencyDecision
from mayak.platform.idempotency import IdempotencyFingerprint, IdempotencyKey, IdempotencyScope

from .eligibility import NotificationChannelClass
from .source_intake import NotificationSourceFamily

ND07_TASK_ID = "ND-07-IDEMPOTENCY-DEDUP-REPLAY-SEMANTICS-20260716-010"

_ALLOWED_PUSH_CHANNEL_CLASSES = (
    NotificationChannelClass.TELEGRAM,
    NotificationChannelClass.MAX,
)

_RECORD_REASON_BY_STATE = {
    "PENDING": "dedup-record-pending",
    "TERMINAL": "dedup-record-terminal",
    "AMBIGUOUS": "dedup-record-ambiguous",
}

_DECISION_REASON_CODES = {
    "dedup-new-effect",
    "dedup-replay-terminal",
    "dedup-replay-pending",
    "dedup-reconciliation-required",
    "dedup-missing-idempotency",
    "dedup-idempotency-fingerprint-mismatch",
    "dedup-semantic-mismatch",
}


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


def _require_exact_enum(value: object, enum_cls: type[Enum], field_name: str) -> object:
    if type(value) is not enum_cls:
        raise ValueError(f"{field_name} must be {enum_cls.__name__}")
    return value


def _require_text_tuple(
    value: object,
    field_name: str,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value and not allow_empty:
        raise ValueError(f"{field_name} must not be empty")
    return tuple(_require_text(item, field_name) for item in value)


def _require_optional_idempotency_value(
    value: object,
    field_name: str,
    expected_type: type[IdempotencyFingerprint | IdempotencyKey | IdempotencyScope],
) -> IdempotencyFingerprint | IdempotencyKey | IdempotencyScope | None:
    if value is None:
        return None
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be {expected_type.__name__}")
    return value


def _require_idempotency_value(
    value: object,
    field_name: str,
    expected_type: type[IdempotencyFingerprint | IdempotencyKey | IdempotencyScope],
) -> IdempotencyFingerprint | IdempotencyKey | IdempotencyScope:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be {expected_type.__name__}")
    return value


def _require_record_reason_codes(
    value: object,
    field_name: str,
    record_state: "NotificationDeduplicationRecordState",
) -> tuple[str, ...]:
    reason_codes = _require_text_tuple(value, field_name, allow_empty=False)
    if len(reason_codes) != 1 or reason_codes[0] != _RECORD_REASON_BY_STATE[record_state.name]:
        raise ValueError(f"{field_name} must match {record_state.name}")
    return reason_codes


def _require_decision_reason_codes(value: object, field_name: str) -> tuple[str, ...]:
    reason_codes = _require_text_tuple(value, field_name, allow_empty=False)
    if len(reason_codes) != 1 or reason_codes[0] not in _DECISION_REASON_CODES:
        raise ValueError(f"{field_name} contains unsupported reason codes")
    return reason_codes


def _require_channel_scope(
    *,
    stage: "NotificationDeduplicationStage",
    channel_class: NotificationChannelClass | None,
) -> NotificationChannelClass | None:
    if channel_class is not None and type(channel_class) is not NotificationChannelClass:
        raise ValueError("channel_class must be NotificationChannelClass")
    if stage in (
        NotificationDeduplicationStage.SOURCE_INTAKE,
        NotificationDeduplicationStage.OUTBOX_CREATION,
    ):
        if channel_class is not None:
            raise ValueError("source and outbox stages must not carry a channel_class")
        return None
    if stage in (
        NotificationDeduplicationStage.ATTEMPT_CREATION,
        NotificationDeduplicationStage.PROVIDER_OUTCOME_RECORDING,
    ):
        if channel_class not in _ALLOWED_PUSH_CHANNEL_CLASSES:
            raise ValueError("attempt and provider stages require TELEGRAM or MAX")
        return channel_class
    raise ValueError("stage is not supported")


def _first_occurrence_union(*tuples: tuple[str, ...]) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []
    for items in tuples:
        for item in items:
            if item not in seen:
                seen.add(item)
                ordered.append(item)
    return tuple(ordered)


def _semantic_signature_request(
    request: "NotificationDeduplicationRequest",
) -> tuple[object, ...]:
    return (
        request.stage,
        request.source_family,
        request.account_id,
        request.beacon_id,
        request.channel_class,
        request.semantic_effect_reference_id,
        request.correlation_id,
        request.causation_id,
    )


def _semantic_signature_record(
    record: "NotificationDeduplicationRecord",
) -> tuple[object, ...]:
    return (
        record.stage,
        record.source_family,
        record.account_id,
        record.beacon_id,
        record.channel_class,
        record.semantic_effect_reference_id,
        record.correlation_id,
        record.causation_id,
    )


class NotificationDeduplicationAuthority(str, Enum):
    NOTIFICATION_DELIVERY_SERVER = "NOTIFICATION_DELIVERY_SERVER"


class NotificationDeduplicationStage(str, Enum):
    SOURCE_INTAKE = "SOURCE_INTAKE"
    OUTBOX_CREATION = "OUTBOX_CREATION"
    ATTEMPT_CREATION = "ATTEMPT_CREATION"
    PROVIDER_OUTCOME_RECORDING = "PROVIDER_OUTCOME_RECORDING"


class NotificationDeduplicationRecordState(str, Enum):
    PENDING = "PENDING"
    TERMINAL = "TERMINAL"
    AMBIGUOUS = "AMBIGUOUS"


class NotificationDeduplicationDecisionStatus(str, Enum):
    NEW_EFFECT = "NEW_EFFECT"
    REPLAY_TERMINAL = "REPLAY_TERMINAL"
    REPLAY_PENDING = "REPLAY_PENDING"
    RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"
    IDEMPOTENCY_MISMATCH = "IDEMPOTENCY_MISMATCH"
    MISSING_REQUIRED_IDEMPOTENCY = "MISSING_REQUIRED_IDEMPOTENCY"


@dataclass(frozen=True, slots=True)
class NotificationDeduplicationRequest:
    stage: NotificationDeduplicationStage
    source_family: NotificationSourceFamily
    account_id: str
    beacon_id: str | None
    channel_class: NotificationChannelClass | None
    semantic_effect_reference_id: str
    idempotency_key: IdempotencyKey | None
    idempotency_fingerprint: IdempotencyFingerprint | None
    idempotency_scope: IdempotencyScope | None
    proposed_record_state: NotificationDeduplicationRecordState
    proposed_result_reference_id: str
    correlation_id: str
    causation_id: str
    evidence_reference_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_exact_enum(self.stage, NotificationDeduplicationStage, "stage")
        if type(self.source_family) is not NotificationSourceFamily:
            raise ValueError("source_family must be NotificationSourceFamily")
        _require_text(self.account_id, "account_id")
        _require_optional_text(self.beacon_id, "beacon_id")
        _require_channel_scope(stage=self.stage, channel_class=self.channel_class)
        _require_text(self.semantic_effect_reference_id, "semantic_effect_reference_id")
        _require_optional_idempotency_value(
            self.idempotency_key,
            "idempotency_key",
            IdempotencyKey,
        )
        _require_optional_idempotency_value(
            self.idempotency_fingerprint,
            "idempotency_fingerprint",
            IdempotencyFingerprint,
        )
        _require_optional_idempotency_value(
            self.idempotency_scope,
            "idempotency_scope",
            IdempotencyScope,
        )
        _require_exact_enum(
            self.proposed_record_state,
            NotificationDeduplicationRecordState,
            "proposed_record_state",
        )
        _require_text(self.proposed_result_reference_id, "proposed_result_reference_id")
        _require_text(self.correlation_id, "correlation_id")
        _require_text(self.causation_id, "causation_id")
        _require_text_tuple(self.evidence_reference_ids, "evidence_reference_ids", allow_empty=True)


@dataclass(frozen=True, slots=True)
class NotificationDeduplicationRecord:
    record_id: str
    authority: NotificationDeduplicationAuthority
    stage: NotificationDeduplicationStage
    source_family: NotificationSourceFamily
    account_id: str
    beacon_id: str | None
    channel_class: NotificationChannelClass | None
    semantic_effect_reference_id: str
    idempotency_key: IdempotencyKey
    idempotency_fingerprint: IdempotencyFingerprint
    idempotency_scope: IdempotencyScope
    record_state: NotificationDeduplicationRecordState
    protected_result_reference_id: str
    correlation_id: str
    causation_id: str
    reason_codes: tuple[str, ...]
    evidence_reference_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_text(self.record_id, "record_id")
        _require_exact_enum(
            self.authority,
            NotificationDeduplicationAuthority,
            "authority",
        )
        _require_exact_enum(self.stage, NotificationDeduplicationStage, "stage")
        if type(self.source_family) is not NotificationSourceFamily:
            raise ValueError("source_family must be NotificationSourceFamily")
        _require_text(self.account_id, "account_id")
        _require_optional_text(self.beacon_id, "beacon_id")
        _require_channel_scope(stage=self.stage, channel_class=self.channel_class)
        _require_text(self.semantic_effect_reference_id, "semantic_effect_reference_id")
        _require_idempotency_value(self.idempotency_key, "idempotency_key", IdempotencyKey)
        _require_idempotency_value(
            self.idempotency_fingerprint,
            "idempotency_fingerprint",
            IdempotencyFingerprint,
        )
        _require_idempotency_value(self.idempotency_scope, "idempotency_scope", IdempotencyScope)
        _require_exact_enum(
            self.record_state,
            NotificationDeduplicationRecordState,
            "record_state",
        )
        _require_text(self.protected_result_reference_id, "protected_result_reference_id")
        _require_text(self.correlation_id, "correlation_id")
        _require_text(self.causation_id, "causation_id")
        _require_record_reason_codes(
            self.reason_codes,
            "reason_codes",
            self.record_state,
        )
        _require_text_tuple(self.evidence_reference_ids, "evidence_reference_ids", allow_empty=True)


@dataclass(frozen=True, slots=True)
class NotificationDeduplicationDecision:
    decision_id: str
    authority: NotificationDeduplicationAuthority
    request: NotificationDeduplicationRequest
    existing_record: NotificationDeduplicationRecord | None
    status: NotificationDeduplicationDecisionStatus
    resulting_record: NotificationDeduplicationRecord | None
    effect_authorized: bool
    replayed: bool
    reconciliation_required: bool
    idempotency_decision: IdempotencyDecision | None
    reason_codes: tuple[str, ...]
    evidence_reference_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_text(self.decision_id, "decision_id")
        _require_exact_enum(
            self.authority,
            NotificationDeduplicationAuthority,
            "authority",
        )
        if type(self.request) is not NotificationDeduplicationRequest:
            raise ValueError("request must be NotificationDeduplicationRequest")
        if (
            self.existing_record is not None
            and type(self.existing_record) is not NotificationDeduplicationRecord
        ):
            raise ValueError("existing_record must be NotificationDeduplicationRecord")
        _require_exact_enum(self.status, NotificationDeduplicationDecisionStatus, "status")
        if (
            self.resulting_record is not None
            and type(self.resulting_record) is not NotificationDeduplicationRecord
        ):
            raise ValueError("resulting_record must be NotificationDeduplicationRecord")
        _require_bool(self.effect_authorized, "effect_authorized")
        _require_bool(self.replayed, "replayed")
        _require_bool(self.reconciliation_required, "reconciliation_required")
        if (
            self.idempotency_decision is not None
            and type(self.idempotency_decision) is not IdempotencyDecision
        ):
            raise ValueError("idempotency_decision must be IdempotencyDecision")
        _require_decision_reason_codes(self.reason_codes, "reason_codes")
        _require_text_tuple(self.evidence_reference_ids, "evidence_reference_ids", allow_empty=True)


def _build_decision(
    *,
    decision_id: str,
    request: NotificationDeduplicationRequest,
    existing_record: NotificationDeduplicationRecord | None,
    status: NotificationDeduplicationDecisionStatus,
    resulting_record: NotificationDeduplicationRecord | None,
    effect_authorized: bool,
    replayed: bool,
    reconciliation_required: bool,
    idempotency_decision: IdempotencyDecision | None,
    reason_code: str,
    evidence_reference_ids: tuple[str, ...],
) -> NotificationDeduplicationDecision:
    return NotificationDeduplicationDecision(
        decision_id=decision_id,
        authority=NotificationDeduplicationAuthority.NOTIFICATION_DELIVERY_SERVER,
        request=request,
        existing_record=existing_record,
        status=status,
        resulting_record=resulting_record,
        effect_authorized=effect_authorized,
        replayed=replayed,
        reconciliation_required=reconciliation_required,
        idempotency_decision=idempotency_decision,
        reason_codes=(reason_code,),
        evidence_reference_ids=evidence_reference_ids,
    )


def evaluate_notification_deduplication(
    *,
    decision_id: str,
    record_id: str,
    request: NotificationDeduplicationRequest,
    existing_record: NotificationDeduplicationRecord | None,
    evidence_reference_ids: tuple[str, ...],
) -> NotificationDeduplicationDecision:
    _require_text(decision_id, "decision_id")
    _require_text(record_id, "record_id")
    _require_text_tuple(evidence_reference_ids, "evidence_reference_ids", allow_empty=True)
    if type(request) is not NotificationDeduplicationRequest:
        raise ValueError("request must be NotificationDeduplicationRequest")
    if existing_record is not None and type(existing_record) is not NotificationDeduplicationRecord:
        raise ValueError("existing_record must be NotificationDeduplicationRecord")

    if (
        request.idempotency_key is None
        or request.idempotency_fingerprint is None
        or request.idempotency_scope is None
    ):
        return _build_decision(
            decision_id=decision_id,
            request=request,
            existing_record=None,
            status=NotificationDeduplicationDecisionStatus.MISSING_REQUIRED_IDEMPOTENCY,
            resulting_record=None,
            effect_authorized=False,
            replayed=False,
            reconciliation_required=False,
            idempotency_decision=None,
            reason_code="dedup-missing-idempotency",
            evidence_reference_ids=_first_occurrence_union(
                request.evidence_reference_ids,
                evidence_reference_ids,
            ),
        )

    if existing_record is None:
        resulting_record = NotificationDeduplicationRecord(
            record_id=record_id,
            authority=NotificationDeduplicationAuthority.NOTIFICATION_DELIVERY_SERVER,
            stage=request.stage,
            source_family=request.source_family,
            account_id=request.account_id,
            beacon_id=request.beacon_id,
            channel_class=request.channel_class,
            semantic_effect_reference_id=request.semantic_effect_reference_id,
            idempotency_key=request.idempotency_key,
            idempotency_fingerprint=request.idempotency_fingerprint,
            idempotency_scope=request.idempotency_scope,
            record_state=request.proposed_record_state,
            protected_result_reference_id=request.proposed_result_reference_id,
            correlation_id=request.correlation_id,
            causation_id=request.causation_id,
            reason_codes=(_RECORD_REASON_BY_STATE[request.proposed_record_state.name],),
            evidence_reference_ids=_first_occurrence_union(
                request.evidence_reference_ids,
                evidence_reference_ids,
            ),
        )
        return _build_decision(
            decision_id=decision_id,
            request=request,
            existing_record=None,
            status=NotificationDeduplicationDecisionStatus.NEW_EFFECT,
            resulting_record=resulting_record,
            effect_authorized=True,
            replayed=False,
            reconciliation_required=request.proposed_record_state
            is NotificationDeduplicationRecordState.AMBIGUOUS,
            idempotency_decision=IdempotencyDecision.NEW,
            reason_code="dedup-new-effect",
            evidence_reference_ids=resulting_record.evidence_reference_ids,
        )

    if (
        existing_record.idempotency_key != request.idempotency_key
        or existing_record.idempotency_scope != request.idempotency_scope
    ):
        raise ValueError("existing_record key or scope must match the request")

    if existing_record.idempotency_fingerprint != request.idempotency_fingerprint:
        return _build_decision(
            decision_id=decision_id,
            request=request,
            existing_record=existing_record,
            status=NotificationDeduplicationDecisionStatus.IDEMPOTENCY_MISMATCH,
            resulting_record=None,
            effect_authorized=False,
            replayed=False,
            reconciliation_required=False,
            idempotency_decision=IdempotencyDecision.MISMATCH,
            reason_code="dedup-idempotency-fingerprint-mismatch",
            evidence_reference_ids=_first_occurrence_union(
                existing_record.evidence_reference_ids,
                request.evidence_reference_ids,
                evidence_reference_ids,
            ),
        )

    if _semantic_signature_request(request) != _semantic_signature_record(existing_record):
        return _build_decision(
            decision_id=decision_id,
            request=request,
            existing_record=existing_record,
            status=NotificationDeduplicationDecisionStatus.IDEMPOTENCY_MISMATCH,
            resulting_record=None,
            effect_authorized=False,
            replayed=False,
            reconciliation_required=False,
            idempotency_decision=IdempotencyDecision.MISMATCH,
            reason_code="dedup-semantic-mismatch",
            evidence_reference_ids=_first_occurrence_union(
                existing_record.evidence_reference_ids,
                request.evidence_reference_ids,
                evidence_reference_ids,
            ),
        )

    if existing_record.record_state is NotificationDeduplicationRecordState.TERMINAL:
        return _build_decision(
            decision_id=decision_id,
            request=request,
            existing_record=existing_record,
            status=NotificationDeduplicationDecisionStatus.REPLAY_TERMINAL,
            resulting_record=existing_record,
            effect_authorized=False,
            replayed=True,
            reconciliation_required=False,
            idempotency_decision=IdempotencyDecision.REPLAY_TERMINAL,
            reason_code="dedup-replay-terminal",
            evidence_reference_ids=_first_occurrence_union(
                existing_record.evidence_reference_ids,
                request.evidence_reference_ids,
                evidence_reference_ids,
            ),
        )
    if existing_record.record_state is NotificationDeduplicationRecordState.PENDING:
        return _build_decision(
            decision_id=decision_id,
            request=request,
            existing_record=existing_record,
            status=NotificationDeduplicationDecisionStatus.REPLAY_PENDING,
            resulting_record=existing_record,
            effect_authorized=False,
            replayed=True,
            reconciliation_required=False,
            idempotency_decision=IdempotencyDecision.PENDING,
            reason_code="dedup-replay-pending",
            evidence_reference_ids=_first_occurrence_union(
                existing_record.evidence_reference_ids,
                request.evidence_reference_ids,
                evidence_reference_ids,
            ),
        )
    return _build_decision(
        decision_id=decision_id,
        request=request,
        existing_record=existing_record,
        status=NotificationDeduplicationDecisionStatus.RECONCILIATION_REQUIRED,
        resulting_record=existing_record,
        effect_authorized=False,
        replayed=True,
        reconciliation_required=True,
        idempotency_decision=IdempotencyDecision.RECONCILE_REQUIRED,
        reason_code="dedup-reconciliation-required",
        evidence_reference_ids=_first_occurrence_union(
            existing_record.evidence_reference_ids,
            request.evidence_reference_ids,
            evidence_reference_ids,
        ),
    )


__all__ = (
    "ND07_TASK_ID",
    "NotificationDeduplicationAuthority",
    "NotificationDeduplicationStage",
    "NotificationDeduplicationRecordState",
    "NotificationDeduplicationDecisionStatus",
    "NotificationDeduplicationRequest",
    "NotificationDeduplicationRecord",
    "NotificationDeduplicationDecision",
    "evaluate_notification_deduplication",
)
