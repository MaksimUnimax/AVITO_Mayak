"""Synchronous session factory and minimal transaction lifecycle."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker


class TransactionBoundaryError(RuntimeError):
    """Raised when a caller-owned transaction boundary cannot be opened."""


@contextmanager
def caller_owned_transaction(session: Session) -> Iterator[Session]:
    """Run one top-level transaction on an existing caller-owned session."""

    if not isinstance(session, Session):
        raise TransactionBoundaryError("session must be a SQLAlchemy Session")
    if session.in_transaction():
        raise TransactionBoundaryError("session already has an active transaction")
    with session.begin():
        yield session


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(engine, class_=Session, autoflush=False, expire_on_commit=False)


@contextmanager
def session_scope(factory: sessionmaker[Session]) -> Iterator[Session]:
    session = factory()
    try:
        yield session
        session.commit()
    except BaseException:
        session.rollback()
        raise
    finally:
        session.close()


__all__ = [
    "TransactionBoundaryError",
    "caller_owned_transaction",
    "create_session_factory",
    "session_scope",
]
