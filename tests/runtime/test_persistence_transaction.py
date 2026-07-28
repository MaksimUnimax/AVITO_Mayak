"""Proof of the caller-owned SQLAlchemy transaction boundary."""

# mypy: disable-error-code="no-untyped-def"

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session

from mayak.contracts.idempotency import IdempotencyDecision
from mayak.contracts.results import CommonOutcome, Result
from mayak.persistence import (
    TransactionBoundaryError,
    caller_owned_transaction,
    create_session_factory,
    session_scope,
)
from mayak.persistence.idempotency import PostgresTerminalIdempotencyRepository
from mayak.platform.idempotency import IdempotencyFingerprint, IdempotencyKey, IdempotencyScope


@pytest.fixture
def sqlite_session():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    with Session(engine) as session:
        yield session
    engine.dispose()


def test_transaction_boundary_rejects_non_session_input():
    with pytest.raises(TransactionBoundaryError, match="session must be a SQLAlchemy Session"):
        with caller_owned_transaction(object()):  # type: ignore[arg-type]
            pass


def test_transaction_boundary_rejects_preexisting_active_transaction(sqlite_session):
    sqlite_session.begin()
    try:
        with pytest.raises(
            TransactionBoundaryError, match="session already has an active transaction"
        ):
            with caller_owned_transaction(sqlite_session):
                pass
        assert sqlite_session.in_transaction()
    finally:
        sqlite_session.rollback()


def test_transaction_boundary_yields_same_caller_owned_session(sqlite_session):
    with caller_owned_transaction(sqlite_session) as yielded:
        assert yielded is sqlite_session


def test_transaction_boundary_keeps_transaction_active_during_body(sqlite_session):
    with caller_owned_transaction(sqlite_session):
        assert sqlite_session.in_transaction()


def test_transaction_boundary_success_ends_transaction_without_closing_session(sqlite_session):
    closed = 0
    original_close = sqlite_session.close

    def close(*args, **kwargs):
        nonlocal closed
        closed += 1
        return original_close(*args, **kwargs)

    sqlite_session.close = close  # type: ignore[method-assign]
    with caller_owned_transaction(sqlite_session):
        pass
    assert not sqlite_session.in_transaction()
    assert closed == 0


def test_transaction_boundary_failure_rolls_back_and_reraises_same_exception(sqlite_session):
    error = ValueError("synthetic")
    with pytest.raises(ValueError) as caught:
        with caller_owned_transaction(sqlite_session):
            raise error
    assert caught.value is error
    assert not sqlite_session.in_transaction()


def test_transaction_boundary_base_exception_rolls_back_and_reraises(sqlite_session):
    class SyntheticBaseException(BaseException):
        pass

    error = SyntheticBaseException()
    with pytest.raises(SyntheticBaseException) as caught:
        with caller_owned_transaction(sqlite_session):
            raise error
    assert caught.value is error
    assert not sqlite_session.in_transaction()


def test_transaction_boundary_does_not_use_nested_transaction_or_savepoint(sqlite_session):
    nested = 0
    original = sqlite_session.begin_nested

    def begin_nested(*args, **kwargs):
        nonlocal nested
        nested += 1
        return original(*args, **kwargs)

    sqlite_session.begin_nested = begin_nested  # type: ignore[method-assign]
    with caller_owned_transaction(sqlite_session):
        pass
    assert nested == 0


def test_transaction_boundary_does_not_commit_before_body_finishes(sqlite_session):
    committed = False

    @event.listens_for(sqlite_session, "after_commit")
    def after_commit(_session):
        nonlocal committed
        committed = True

    with caller_owned_transaction(sqlite_session):
        assert not committed
    assert committed


def test_transaction_boundary_session_is_reusable_after_success(sqlite_session):
    with caller_owned_transaction(sqlite_session):
        pass
    assert not sqlite_session.in_transaction()
    sqlite_session.execute(text("SELECT 1")).scalar_one()
    sqlite_session.rollback()


def test_transaction_boundary_session_is_reusable_after_failure(sqlite_session):
    with pytest.raises(RuntimeError):
        with caller_owned_transaction(sqlite_session):
            raise RuntimeError("synthetic")
    assert not sqlite_session.in_transaction()
    sqlite_session.execute(text("SELECT 1")).scalar_one()
    sqlite_session.rollback()


def test_transaction_boundary_supports_repeated_independent_transactions(sqlite_session):
    for _ in range(3):
        with caller_owned_transaction(sqlite_session):
            assert sqlite_session.in_transaction()
        assert not sqlite_session.in_transaction()


def test_postgres_transaction_boundary_commits_insert(postgres_engine):
    record_id = uuid4()
    scope = f"rf1005-{uuid4().hex}"
    key = f"key-{uuid4().hex}"
    with Session(postgres_engine) as session:
        with caller_owned_transaction(session):
            session.execute(
                text("INSERT INTO mayak.platform_idempotency_records "
                     "(id, scope, idempotency_key, request_fingerprint, result, created_at, "
                     "expires_at) VALUES (:id, :scope, :key, :fingerprint, "
                     "CAST(:result AS jsonb), :created, :expires)"),
                {"id": record_id, "scope": scope, "key": key, "fingerprint": "a" * 64,
                 "result": '{"result":"SUCCEEDED","reason_code":"rf1005"}',
                 "created": datetime.now(timezone.utc),
                 "expires": datetime.now(timezone.utc) + timedelta(hours=1)},
            )
        assert session.execute(
            text("SELECT id FROM mayak.platform_idempotency_records WHERE id = :id"),
            {"id": record_id},
        ).scalar_one() == record_id


def test_postgres_transaction_boundary_rolls_back_insert_on_failure(postgres_engine):
    record_id = uuid4()
    scope = f"rf1005-{uuid4().hex}"
    key = f"key-{uuid4().hex}"
    with Session(postgres_engine) as session:
        with pytest.raises(ValueError) as caught:
            with caller_owned_transaction(session):
                session.execute(
                    text("INSERT INTO mayak.platform_idempotency_records "
                         "(id, scope, idempotency_key, request_fingerprint, result, created_at, "
                         "expires_at) VALUES (:id, :scope, :key, :fingerprint, "
                         "CAST(:result AS jsonb), :created, :expires)"),
                    {"id": record_id, "scope": scope, "key": key, "fingerprint": "a" * 64,
                     "result": '{"result":"SUCCEEDED","reason_code":"rf1005"}',
                     "created": datetime.now(timezone.utc),
                     "expires": datetime.now(timezone.utc) + timedelta(hours=1)},
                )
                raise (error := ValueError("synthetic"))
        assert caught.value is error
        assert not session.in_transaction()
        assert session.execute(
            text("SELECT count(*) FROM mayak.platform_idempotency_records WHERE id = :id"),
            {"id": record_id},
        ).scalar_one() == 0


def test_postgres_transaction_boundary_rolls_back_multiple_writes_atomically(postgres_engine):
    with Session(postgres_engine) as session:
        rows = [(uuid4(), f"rf1005-{uuid4().hex}", f"key-{uuid4().hex}") for _ in range(2)]
        with pytest.raises(RuntimeError):
            with caller_owned_transaction(session):
                for record_id, scope, key in rows:
                    session.execute(
                        text("INSERT INTO mayak.platform_idempotency_records "
                             "(id, scope, idempotency_key, request_fingerprint, result, "
                             "created_at, "
                             "expires_at) VALUES (:id, :scope, :key, :fingerprint, "
                             "CAST(:result AS jsonb), :created, :expires)"),
                        {"id": record_id, "scope": scope, "key": key, "fingerprint": "a" * 64,
                         "result": '{"result":"SUCCEEDED","reason_code":"rf1005"}',
                         "created": datetime.now(timezone.utc),
                         "expires": datetime.now(timezone.utc) + timedelta(hours=1)},
                    )
                raise RuntimeError("synthetic")
        assert session.execute(
            text("SELECT count(*) FROM mayak.platform_idempotency_records "
                 "WHERE id = :first OR id = :second"),
            {"first": rows[0][0], "second": rows[1][0]},
        ).scalar_one() == 0


def _postgres_dsn() -> str:
    value = os.environ.get("MAYAK_RF10_POSTGRES_DSN")
    if not value:
        pytest.fail("MAYAK_RF10_POSTGRES_DSN is required for PostgreSQL proof")
    return value


@pytest.fixture(scope="module")
def postgres_engine():
    engine = create_engine(_postgres_dsn(), pool_size=2, max_overflow=2)
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    yield engine
    engine.dispose()


def _record_inputs():
    now = datetime.now(timezone.utc)
    return (
        now,
        IdempotencyScope(value=f"rf1005-{uuid4().hex}"),
        IdempotencyKey(value=f"key-{uuid4().hex}"),
        IdempotencyFingerprint(value="a" * 64),
    )


def _record(session, now, scope, key, fingerprint):
    return PostgresTerminalIdempotencyRepository().record_terminal(
        session,
        record_id=uuid4(),
        scope=scope,
        key=key,
        fingerprint=fingerprint,
        outcome=CommonOutcome(result=Result.SUCCEEDED, reason_code="rf1005"),
        created_at=now,
        expires_at=now + timedelta(hours=1),
        now=now,
    )


def test_postgres_transaction_boundary_commits_idempotency_repository_record(postgres_engine):
    now, scope, key, fingerprint = _record_inputs()
    with Session(postgres_engine) as session:
        with caller_owned_transaction(session):
            result = _record(session, now, scope, key, fingerprint)
        replay = PostgresTerminalIdempotencyRepository().evaluate(
            session, scope=scope, key=key, fingerprint=fingerprint, now=now
        )
        assert result.decision.decision is IdempotencyDecision.NEW
        assert replay.decision.decision is IdempotencyDecision.REPLAY_TERMINAL


def test_postgres_transaction_boundary_rolls_back_idempotency_repository_record(postgres_engine):
    now, scope, key, fingerprint = _record_inputs()
    error = RuntimeError("synthetic")
    with Session(postgres_engine) as session:
        with pytest.raises(RuntimeError) as caught:
            with caller_owned_transaction(session):
                _record(session, now, scope, key, fingerprint)
                raise error
        assert caught.value is error
        available = PostgresTerminalIdempotencyRepository().evaluate(
            session, scope=scope, key=key, fingerprint=fingerprint, now=now
        )
        assert available.decision.decision is IdempotencyDecision.NEW


def test_public_persistence_package_exports_transaction_boundary_api():
    import mayak.persistence as persistence

    assert persistence.TransactionBoundaryError is TransactionBoundaryError
    assert persistence.caller_owned_transaction is caller_owned_transaction
    assert persistence.create_session_factory is create_session_factory
    assert persistence.session_scope is session_scope
