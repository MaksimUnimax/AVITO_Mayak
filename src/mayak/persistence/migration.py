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


def _scalar(result: Any) -> Any:
    try:
        return result.scalar()
    except Exception:
        raise MigrationSerializationError("migration serialization unavailable") from None


def _acquire(connection: Any) -> None:
    try:
        acquired = _scalar(connection.execute(_ACQUIRE, {"lock_key": MIGRATION_LOCK_KEY}))
    except MigrationSerializationError:
        raise
    except Exception:
        raise MigrationSerializationError("migration serialization unavailable") from None
    if acquired is not True:
        raise MigrationSerializationError("migration serialization unavailable")


def _release(connection: Any) -> None:
    try:
        released = _scalar(connection.execute(_RELEASE, {"lock_key": MIGRATION_LOCK_KEY}))
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
