"""Real PostgreSQL proof nodes for terminal idempotency persistence."""

# mypy: disable-error-code="no-untyped-def"

from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from mayak.contracts.idempotency import IdempotencyDecision
from mayak.contracts.results import CommonOutcome, Result
from mayak.persistence.idempotency import PostgresTerminalIdempotencyRepository
from mayak.platform.idempotency import IdempotencyFingerprint, IdempotencyKey, IdempotencyScope


def _required_postgres() -> str:
    dsn = os.environ.get("MAYAK_RF10_POSTGRES_DSN")
    if not dsn:
        pytest.fail("MAYAK_RF10_POSTGRES_DSN is required for PostgreSQL proof")
    return dsn


@pytest.fixture(scope="module")
def engine():
    value = create_engine(_required_postgres(), pool_size=4, max_overflow=4)
    with value.connect() as connection:
        connection.execute(text("SELECT 1"))
    yield value
    value.dispose()


def _inputs(suffix: str) -> tuple[IdempotencyScope, IdempotencyKey, IdempotencyFingerprint]:
    return (
        IdempotencyScope(value=f"rf10-pg-{suffix}"),
        IdempotencyKey(value=f"key-{uuid4()}"),
        IdempotencyFingerprint(value="a" * 64),
    )


def _outcome(reason: str = "accepted") -> CommonOutcome:
    return CommonOutcome(result=Result.SUCCEEDED, reason_code=reason)


def _record(
    session: Session,
    scope: IdempotencyScope,
    key: IdempotencyKey,
    fingerprint: IdempotencyFingerprint,
    *,
    now: datetime,
    outcome: CommonOutcome | None = None,
    expires_at: datetime | None = None,
):
    return PostgresTerminalIdempotencyRepository().record_terminal(
        session,
        record_id=uuid4(),
        scope=scope,
        key=key,
        fingerprint=fingerprint,
        outcome=outcome or _outcome(),
        created_at=now,
        expires_at=expires_at or now + timedelta(hours=1),
        now=now,
    )


def test_postgres_application_role_records_and_replays_terminal_outcome(engine):
    now = datetime.now(timezone.utc)
    scope, key, fingerprint = _inputs("replay")
    expected = _outcome("database-proof")
    with Session(engine) as session:
        recorded = _record(session, scope, key, fingerprint, now=now, outcome=expected)
        session.commit()
        replayed = PostgresTerminalIdempotencyRepository().evaluate(
            session, scope=scope, key=key, fingerprint=fingerprint, now=now
        )
    assert recorded.decision.decision is IdempotencyDecision.NEW
    assert replayed.decision.decision is IdempotencyDecision.REPLAY_TERMINAL
    assert replayed.outcome == expected


def test_postgres_different_fingerprint_does_not_overwrite_terminal_outcome(engine):
    now = datetime.now(timezone.utc)
    scope, key, fingerprint = _inputs("mismatch")
    other = IdempotencyFingerprint(value="b" * 64)
    with Session(engine) as session:
        first = _record(session, scope, key, fingerprint, now=now)
        session.commit()
        loser = _record(session, scope, key, other, now=now)
        session.commit()
        replay = PostgresTerminalIdempotencyRepository().evaluate(
            session, scope=scope, key=key, fingerprint=fingerprint, now=now
        )
    assert first.decision.decision is IdempotencyDecision.NEW
    assert loser.decision.decision is IdempotencyDecision.MISMATCH
    assert replay.outcome == _outcome()


def test_postgres_expired_terminal_record_is_atomically_replaced(engine):
    now = datetime.now(timezone.utc)
    scope, key, fingerprint = _inputs("replace")
    with Session(engine) as session:
        _record(session, scope, key, fingerprint, now=now - timedelta(hours=2), expires_at=now)
        session.commit()
        replacement = _record(session, scope, key, fingerprint, now=now, outcome=_outcome("new"))
        session.commit()
        replay = PostgresTerminalIdempotencyRepository().evaluate(
            session, scope=scope, key=key, fingerprint=fingerprint, now=now
        )
    assert replacement.decision.decision is IdempotencyDecision.NEW
    assert replay.outcome == _outcome("new")


def test_postgres_expiration_boundary_is_inclusive(engine):
    now = datetime.now(timezone.utc)
    scope, key, fingerprint = _inputs("boundary")
    with Session(engine) as session:
        _record(session, scope, key, fingerprint, now=now - timedelta(hours=1), expires_at=now)
        session.commit()
        result = PostgresTerminalIdempotencyRepository().evaluate(
            session, scope=scope, key=key, fingerprint=fingerprint, now=now
        )
    assert result.decision.decision is IdempotencyDecision.NEW
    assert result.decision.reason_code == "IDEMPOTENCY_RECORD_EXPIRED"


def test_postgres_caller_rollback_removes_uncommitted_terminal_record(engine):
    now = datetime.now(timezone.utc)
    scope, key, fingerprint = _inputs("rollback")
    with Session(engine) as session:
        result = _record(session, scope, key, fingerprint, now=now)
        assert result.decision.decision is IdempotencyDecision.NEW
        session.rollback()
        absent = PostgresTerminalIdempotencyRepository().evaluate(
            session, scope=scope, key=key, fingerprint=fingerprint, now=now
        )
    assert absent.decision.decision is IdempotencyDecision.NEW
    assert absent.decision.reason_code == "IDEMPOTENCY_KEY_AVAILABLE"


def test_postgres_concurrent_same_fingerprint_yields_new_and_replay(engine):
    now = datetime.now(timezone.utc)
    scope, key, fingerprint = _inputs("same-concurrency")

    def worker():
        with Session(engine) as session:
            result = _record(session, scope, key, fingerprint, now=now)
            session.commit()
            return result

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: worker(), range(2)))
    decisions = sorted(result.decision.decision.value for result in results)
    assert decisions == ["NEW", "REPLAY_TERMINAL"]
    with engine.connect() as connection:
        count = connection.execute(
            text("SELECT count(*) FROM mayak.platform_idempotency_records "
                 "WHERE scope = :scope AND idempotency_key = :key"),
            {"scope": scope.value, "key": key.value},
        ).scalar_one()
    assert count == 1


def test_postgres_concurrent_different_fingerprints_yields_new_and_mismatch(engine):
    now = datetime.now(timezone.utc)
    scope, key, first_fingerprint = _inputs("different-concurrency")
    fingerprints = (first_fingerprint, IdempotencyFingerprint(value="b" * 64))

    def worker(fingerprint: IdempotencyFingerprint):
        with Session(engine) as session:
            result = _record(session, scope, key, fingerprint, now=now)
            session.commit()
            return result

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(worker, fingerprints))
    decisions = sorted(result.decision.decision.value for result in results)
    assert decisions == ["MISMATCH", "NEW"]
    with engine.connect() as connection:
        row = connection.execute(
            text("SELECT request_fingerprint FROM mayak.platform_idempotency_records "
                 "WHERE scope = :scope AND idempotency_key = :key"),
            {"scope": scope.value, "key": key.value},
        ).one()
    assert row.request_fingerprint in {fingerprints[0].value, fingerprints[1].value}


def test_postgres_corrupt_result_fails_closed_without_payload_exposure(engine):
    now = datetime.now(timezone.utc)
    scope, key, fingerprint = _inputs("corrupt")
    with Session(engine) as session:
        session.execute(
            text("INSERT INTO mayak.platform_idempotency_records "
                 "(id, scope, idempotency_key, request_fingerprint, result, created_at, "
                 "expires_at) "
                 "VALUES (:id, :scope, :key, :fingerprint, CAST(:result AS jsonb), "
                 ":created, :expires)"),
            {
                "id": uuid4(), "scope": scope.value, "key": key.value,
                "fingerprint": fingerprint.value, "result": '{"corrupt_secret":"hidden"}',
                "created": now, "expires": now + timedelta(hours=1),
            },
        )
        session.commit()
        result = PostgresTerminalIdempotencyRepository().evaluate(
            session, scope=scope, key=key, fingerprint=fingerprint, now=now
        )
    assert result.decision.decision is IdempotencyDecision.RECONCILE_REQUIRED
    assert "hidden" not in repr(result)
    assert "corrupt_secret" not in repr(result)
