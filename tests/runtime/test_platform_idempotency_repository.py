"""Unit proof for terminal idempotency repository behavior."""

# The fake session deliberately models only execute() for transaction-boundary proof.
# mypy: disable-error-code="no-untyped-def,arg-type"

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from sqlalchemy.dialects import postgresql

from mayak.contracts.idempotency import IdempotencyDecision, IdempotencyDecisionOutcome
from mayak.contracts.results import CommonOutcome, Result
from mayak.persistence.idempotency import (
    PostgresTerminalIdempotencyRepository,
    TerminalIdempotencyResolution,
)
from mayak.platform.idempotency import IdempotencyFingerprint, IdempotencyKey, IdempotencyScope

NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)
SCOPE = IdempotencyScope(value="rf10-unit")
KEY = IdempotencyKey(value="key")
FP = IdempotencyFingerprint(value="a" * 64)
OTHER_FP = IdempotencyFingerprint(value="b" * 64)
OUTCOME = CommonOutcome(result=Result.SUCCEEDED, reason_code="done")


class ResultSet:
    def __init__(self, row=None):
        self.row = row

    def mappings(self):
        return self

    def one_or_none(self):
        return self.row

    def scalar_one_or_none(self):
        return self.row


class Session:
    def __init__(self, *results):
        self.results = list(results)
        self.calls = []

    def execute(self, statement):
        self.calls.append(statement)
        return ResultSet(self.results.pop(0) if self.results else None)


def row(fingerprint=FP.value, result=None, expires_at=None):
    return {
        "request_fingerprint": fingerprint,
        "result": OUTCOME.model_dump(mode="json") if result is None else result,
        "expires_at": NOW + timedelta(hours=1) if expires_at is None else expires_at,
    }


def test_resolution_requires_outcome_only_for_terminal_replay():
    with pytest.raises(ValueError):
        TerminalIdempotencyResolution(
            decision=IdempotencyDecisionOutcome.replay_terminal(reason_code="x"),
            outcome=None,
        )
    resolution = TerminalIdempotencyResolution(
        decision=IdempotencyDecisionOutcome.new(reason_code="x"), outcome=None
    )
    assert resolution.outcome is None


def test_evaluate_absent_returns_new_without_transaction_control():
    session = Session(None)
    result = PostgresTerminalIdempotencyRepository().evaluate(
        session, scope=SCOPE, key=KEY, fingerprint=FP, now=NOW
    )
    assert result.decision.decision is IdempotencyDecision.NEW
    assert result.decision.reason_code == "IDEMPOTENCY_KEY_AVAILABLE"


def test_evaluate_expired_returns_new_without_deleting():
    session = Session(row(expires_at=NOW))
    result = PostgresTerminalIdempotencyRepository().evaluate(
        session, scope=SCOPE, key=KEY, fingerprint=FP, now=NOW
    )
    assert result.decision.reason_code == "IDEMPOTENCY_RECORD_EXPIRED"
    assert len(session.calls) == 1


def test_evaluate_same_fingerprint_replays_valid_terminal_outcome():
    result = PostgresTerminalIdempotencyRepository().evaluate(
        Session(row()), scope=SCOPE, key=KEY, fingerprint=FP, now=NOW
    )
    assert result.decision.decision is IdempotencyDecision.REPLAY_TERMINAL
    assert result.outcome == OUTCOME


def test_evaluate_different_fingerprint_returns_mismatch_without_deserializing():
    result = PostgresTerminalIdempotencyRepository().evaluate(
        Session(row(fingerprint=OTHER_FP.value, result={"not": "an outcome"})),
        scope=SCOPE, key=KEY, fingerprint=FP, now=NOW,
    )
    assert result.decision.reason_code == "IDEMPOTENCY_FINGERPRINT_MISMATCH"
    assert result.outcome is None


def test_evaluate_corrupt_same_fingerprint_returns_reconcile_required_without_payload():
    result = PostgresTerminalIdempotencyRepository().evaluate(
        Session(row(result={"secret": "must not escape"})),
        scope=SCOPE, key=KEY, fingerprint=FP, now=NOW,
    )
    assert result.decision.reason_code == "IDEMPOTENCY_STORED_RESULT_INVALID"
    assert "secret" not in repr(result)


def test_record_terminal_new_uses_conflict_safe_insert():
    session = Session(uuid4())
    result = PostgresTerminalIdempotencyRepository().record_terminal(
        session, record_id=uuid4(), scope=SCOPE, key=KEY, fingerprint=FP,
        outcome=OUTCOME, created_at=NOW, expires_at=NOW + timedelta(hours=1), now=NOW,
    )
    sql = str(session.calls[0].compile(dialect=postgresql.dialect()))
    assert "ON CONFLICT" in sql and "DO UPDATE" in sql and "RETURNING" in sql
    assert result.decision.reason_code == "IDEMPOTENCY_TERMINAL_RECORDED"


def test_record_terminal_same_fingerprint_conflict_replays_existing():
    result = PostgresTerminalIdempotencyRepository().record_terminal(
        Session(None, row()), record_id=uuid4(), scope=SCOPE, key=KEY, fingerprint=FP,
        outcome=OUTCOME, created_at=NOW, expires_at=NOW + timedelta(hours=1), now=NOW,
    )
    assert result.decision.decision is IdempotencyDecision.REPLAY_TERMINAL


def test_record_terminal_different_fingerprint_conflict_returns_mismatch():
    result = PostgresTerminalIdempotencyRepository().record_terminal(
        Session(None, row(fingerprint=OTHER_FP.value)), record_id=uuid4(), scope=SCOPE, key=KEY,
        fingerprint=FP, outcome=OUTCOME, created_at=NOW,
        expires_at=NOW + timedelta(hours=1), now=NOW,
    )
    assert result.decision.decision is IdempotencyDecision.MISMATCH


def test_record_terminal_unknown_conflict_state_requires_reconciliation():
    result = PostgresTerminalIdempotencyRepository().record_terminal(
        Session(None, None), record_id=uuid4(), scope=SCOPE, key=KEY, fingerprint=FP,
        outcome=OUTCOME, created_at=NOW, expires_at=NOW + timedelta(hours=1), now=NOW,
    )
    assert result.decision.reason_code == "IDEMPOTENCY_CONFLICT_STATE_UNKNOWN"


def test_repository_rejects_invalid_inputs_before_sql():
    session = Session()
    with pytest.raises(ValueError):
        PostgresTerminalIdempotencyRepository().record_terminal(
            session, record_id=uuid4(), scope=SCOPE, key=KEY,
            fingerprint=IdempotencyFingerprint(value="x" * 64), outcome=OUTCOME,
            created_at=NOW, expires_at=NOW, now=NOW,
        )
    assert not session.calls


def test_repository_never_controls_caller_transaction_or_session():
    session = Session(None)
    PostgresTerminalIdempotencyRepository().evaluate(
        session, scope=SCOPE, key=KEY, fingerprint=FP, now=NOW
    )
    assert not any(name in repr(session.calls) for name in ("commit", "rollback", "close", "begin"))
