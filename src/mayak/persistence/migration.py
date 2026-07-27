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


@contextmanager
def serialized_migration(connection: Any) -> Iterator[None]:
    """Hold one session-level lock over configuration and all migrations."""
    _acquire(connection)
    try:
        yield
    except BaseException:
        try:
            _release(connection)
        except MigrationSerializationError:
            pass
        raise
    else:
        _release(connection)
