from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from mayak.contracts.idempotency import IdempotencyDecision
from mayak.platform.idempotency import (
    IdempotencyFingerprint,
    IdempotencyKey,
    IdempotencyScope,
)

from .contracts import DispatchStatus
from .dispatch import TransportDispatchAttemptBoundary, TransportDispatchAuthority

ER06D_TASK_ID = "ER-06D-DISPATCH-REPLAY-DECISION-BOUNDARY-20260715-013"

__all__ = (
    "ER06D_TASK_ID",
    "TransportDispatchReplayAuthority",
    "TransportDispatchReplayBoundary",
)


def _require_text(value: object, field_name: str) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-blank string")
    return value


def _require_bool(value: object, field_name: str) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _require_tuple(value: object, field_name: str) -> tuple[object, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    return value


def _require_non_empty_text_tuple(value: object, field_name: str) -> tuple[str, ...]:
    items = _require_tuple(value, field_name)
    if not items:
        raise ValueError(f"{field_name} must not be empty")
    for item in items:
        _require_text(item, field_name)
    return items  # type: ignore[return-value]


def _require_exact_enum(value: object, enum_cls: type[Enum], field_name: str) -> Enum:
    if type(value) is not enum_cls:
        raise ValueError(f"{field_name} must be {enum_cls.__name__}")
    return value


def _require_exact_record(value: object, record_cls: type[object], field_name: str) -> object:
    if type(value) is not record_cls:
        raise ValueError(f"{field_name} must be {record_cls.__name__}")
    return value


_PENDING_REPLAY_STATUSES = frozenset(
    {
        DispatchStatus.PENDING,
        DispatchStatus.ATTEMPTED,
        DispatchStatus.ACKNOWLEDGED,
    }
)

_TERMINAL_REPLAY_STATUSES = frozenset(
    {
        DispatchStatus.REJECTED,
        DispatchStatus.NOT_SENT,
        DispatchStatus.SENT,
    }
)


class TransportDispatchReplayAuthority(str, Enum):
    EGRESS_ROUTING_SERVER = "EGRESS_ROUTING_SERVER"


@dataclass(frozen=True, slots=True)
class TransportDispatchReplayBoundary:
    boundary_id: str
    authority: TransportDispatchReplayAuthority
    dispatch_attempt: TransportDispatchAttemptBoundary
    original_scope: IdempotencyScope
    original_key: IdempotencyKey
    original_fingerprint: IdempotencyFingerprint
    replay_scope: IdempotencyScope
    replay_key: IdempotencyKey
    replay_fingerprint: IdempotencyFingerprint
    decision: IdempotencyDecision
    original_attempt_reference: str
    replay_dispatch_effect_authorized: bool
    reconciliation_required: bool
    reason_codes: tuple[str, ...]
    evidence_reference_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        boundary_id = _require_text(self.boundary_id, "boundary_id")
        authority = _require_exact_enum(
            self.authority,
            TransportDispatchReplayAuthority,
            "authority",
        )
        dispatch_attempt = _require_exact_record(
            self.dispatch_attempt,
            TransportDispatchAttemptBoundary,
            "dispatch_attempt",
        )
        original_scope = _require_exact_record(
            self.original_scope,
            IdempotencyScope,
            "original_scope",
        )
        original_key = _require_exact_record(self.original_key, IdempotencyKey, "original_key")
        original_fingerprint = _require_exact_record(
            self.original_fingerprint,
            IdempotencyFingerprint,
            "original_fingerprint",
        )
        replay_scope = _require_exact_record(self.replay_scope, IdempotencyScope, "replay_scope")
        replay_key = _require_exact_record(self.replay_key, IdempotencyKey, "replay_key")
        replay_fingerprint = _require_exact_record(
            self.replay_fingerprint,
            IdempotencyFingerprint,
            "replay_fingerprint",
        )
        decision = _require_exact_enum(self.decision, IdempotencyDecision, "decision")
        original_attempt_reference = _require_text(
            self.original_attempt_reference,
            "original_attempt_reference",
        )
        replay_dispatch_effect_authorized = _require_bool(
            self.replay_dispatch_effect_authorized,
            "replay_dispatch_effect_authorized",
        )
        reconciliation_required = _require_bool(
            self.reconciliation_required,
            "reconciliation_required",
        )
        reason_codes = _require_non_empty_text_tuple(self.reason_codes, "reason_codes")
        evidence_reference_ids = _require_non_empty_text_tuple(
            self.evidence_reference_ids,
            "evidence_reference_ids",
        )

        assert isinstance(authority, TransportDispatchReplayAuthority)
        assert isinstance(dispatch_attempt, TransportDispatchAttemptBoundary)
        assert isinstance(original_scope, IdempotencyScope)
        assert isinstance(original_key, IdempotencyKey)
        assert isinstance(original_fingerprint, IdempotencyFingerprint)
        assert isinstance(replay_scope, IdempotencyScope)
        assert isinstance(replay_key, IdempotencyKey)
        assert isinstance(replay_fingerprint, IdempotencyFingerprint)
        assert isinstance(decision, IdempotencyDecision)

        object.__setattr__(self, "boundary_id", boundary_id)
        object.__setattr__(self, "authority", authority)
        object.__setattr__(self, "dispatch_attempt", dispatch_attempt)
        object.__setattr__(self, "original_scope", original_scope)
        object.__setattr__(self, "original_key", original_key)
        object.__setattr__(self, "original_fingerprint", original_fingerprint)
        object.__setattr__(self, "replay_scope", replay_scope)
        object.__setattr__(self, "replay_key", replay_key)
        object.__setattr__(self, "replay_fingerprint", replay_fingerprint)
        object.__setattr__(self, "decision", decision)
        object.__setattr__(self, "original_attempt_reference", original_attempt_reference)
        object.__setattr__(
            self,
            "replay_dispatch_effect_authorized",
            replay_dispatch_effect_authorized,
        )
        object.__setattr__(self, "reconciliation_required", reconciliation_required)
        object.__setattr__(self, "reason_codes", reason_codes)
        object.__setattr__(self, "evidence_reference_ids", evidence_reference_ids)

        if authority is not TransportDispatchReplayAuthority.EGRESS_ROUTING_SERVER:
            raise ValueError("authority must be EGRESS_ROUTING_SERVER")
        if dispatch_attempt.authority is not TransportDispatchAuthority.EGRESS_ROUTING_SERVER:
            raise ValueError("dispatch_attempt.authority must be EGRESS_ROUTING_SERVER")
        if dispatch_attempt.dispatch_state_committed is not True:
            raise ValueError("dispatch_attempt.dispatch_state_committed must be True")
        if dispatch_attempt.attempt.attempt_ordinal != 1:
            raise ValueError("dispatch_attempt.attempt.attempt_ordinal must be 1")
        if dispatch_attempt.attempt.outcome_reference is not None:
            raise ValueError("dispatch_attempt.attempt.outcome_reference must be None")

        if original_attempt_reference != dispatch_attempt.attempt.attempt_id:
            raise ValueError(
                "original_attempt_reference must match "
                "dispatch_attempt.attempt.attempt_id"
            )

        scope_matches = original_scope == replay_scope
        key_matches = original_key == replay_key
        fingerprint_matches = original_fingerprint == replay_fingerprint
        exact_replay_match = scope_matches and key_matches and fingerprint_matches

        if decision is IdempotencyDecision.NEW:
            raise ValueError("decision NEW is forbidden")
        if replay_dispatch_effect_authorized is not False:
            raise ValueError("replay_dispatch_effect_authorized must be False")

        dispatch_status = dispatch_attempt.attempt.dispatch_status
        if dispatch_status is DispatchStatus.UNKNOWN:
            expected_reconciliation_required = True
        else:
            expected_reconciliation_required = False
        if reconciliation_required is not expected_reconciliation_required:
            raise ValueError(
                "reconciliation_required must be True only when dispatch_status is UNKNOWN"
            )

        if not exact_replay_match:
            expected_decision = IdempotencyDecision.MISMATCH
        elif dispatch_status in _PENDING_REPLAY_STATUSES:
            expected_decision = IdempotencyDecision.PENDING
        elif dispatch_status is DispatchStatus.UNKNOWN:
            expected_decision = IdempotencyDecision.RECONCILE_REQUIRED
        elif dispatch_status in _TERMINAL_REPLAY_STATUSES:
            expected_decision = IdempotencyDecision.REPLAY_TERMINAL
        else:  # pragma: no cover - exhaustive guard
            raise ValueError("dispatch_attempt.attempt.dispatch_status is unsupported")

        if decision is not expected_decision:
            raise ValueError("decision does not match replay semantics")
