"""Fail-fast session serialization for the complete Alembic online run."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Final, Iterator

from sqlalchemy import text

MIGRATION_LOCK_KEY: Final[int] = 7342190310


class MigrationSerializationError(RuntimeError):
    """A redacted, operator-actionable migration serialization failure."""


_ACQUIRE = text("SELECT pg_try_advisory_lock(:lock_key)")
_RELEASE = text("SELECT pg_advisory_unlock(:lock_key)")


def _single_value(result: Any, message: str) -> Any:
    try:
        row = result.one()
        if len(row) != 1:
            raise ValueError("unexpected result width")
        return row[0]
    except Exception:
        raise MigrationSerializationError(message) from None


def _acquire(connection: Any) -> None:
    try:
        acquired = _single_value(
            connection.execute(_ACQUIRE, {"lock_key": MIGRATION_LOCK_KEY}),
            "migration serialization unavailable",
        )
    except MigrationSerializationError:
        raise
    except Exception:
        raise MigrationSerializationError("migration serialization unavailable") from None
    if acquired is not True:
        raise MigrationSerializationError("migration serialization unavailable")


def _release(connection: Any) -> None:
    try:
        released = _single_value(
            connection.execute(_RELEASE, {"lock_key": MIGRATION_LOCK_KEY}),
            "migration serialization release failed",
        )
    except Exception:
        raise MigrationSerializationError("migration serialization release failed") from None
    if released is not True:
        raise MigrationSerializationError("migration serialization release failed")


def _transaction_state(connection: Any, message: str) -> bool:
    try:
        state = connection.in_transaction()
    except Exception:
        raise MigrationSerializationError(message) from None
    if type(state) is not bool:
        raise MigrationSerializationError(message)
    return state


def _best_effort_cleanup(connection: Any) -> None:
    body_transaction_clean = False
    try:
        body_transaction_active = _transaction_state(
            connection, "migration serialization release failed"
        )
    except BaseException:
        body_transaction_active = None
    if body_transaction_active is False:
        body_transaction_clean = True
    elif body_transaction_active is True:
        try:
            connection.rollback()
        except BaseException:
            pass
        else:
            try:
                body_transaction_clean = not _transaction_state(
                    connection, "migration serialization release failed"
                )
            except BaseException:
                pass

    unlock_succeeded = False
    try:
        _release(connection)
        unlock_succeeded = True
    except BaseException:
        pass
    if body_transaction_clean and unlock_succeeded:
        try:
            if _transaction_state(connection, "migration serialization release failed"):
                connection.commit()
        except BaseException:
            pass


@contextmanager
def serialized_migration(connection: Any) -> Iterator[None]:
    """Hold one session-level lock over configuration and all migrations."""
    if _transaction_state(connection, "migration serialization unavailable"):
        raise MigrationSerializationError("migration serialization unavailable")
    _acquire(connection)
    try:
        connection.commit()
        if _transaction_state(connection, "migration serialization unavailable"):
            raise MigrationSerializationError("migration serialization unavailable")
    except MigrationSerializationError:
        _best_effort_cleanup(connection)
        raise
    except Exception:
        _best_effort_cleanup(connection)
        raise MigrationSerializationError("migration serialization unavailable") from None
    try:
        yield
    except BaseException:
        _best_effort_cleanup(connection)
        raise
    else:
        try:
            if _transaction_state(connection, "migration serialization release failed"):
                connection.rollback()
            _release(connection)
            connection.commit()
            if _transaction_state(connection, "migration serialization release failed"):
                raise MigrationSerializationError("migration serialization release failed")
        except MigrationSerializationError:
            raise
        except Exception:
            raise MigrationSerializationError("migration serialization release failed") from None
