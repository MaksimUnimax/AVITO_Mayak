from typing import cast

from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.pool import NullPool, QueuePool

from mayak.persistence.engine import (
    create_application_engine,
    create_migration_engine,
    dispose_engine,
)


def test_engines_are_lazy_and_use_psycopg() -> None:
    url = URL.create(
        "postgresql+psycopg",
        username="test_user",
        host="mayak-postgres",
        port=5432,
        database="mayak",
    )
    application = create_application_engine(
        url, pool_size=2, max_overflow=1, pool_timeout=4, pool_recycle=10
    )
    migration = create_migration_engine(url)
    try:
        pool = cast(QueuePool, application.pool)
        assert application.url.drivername == "postgresql+psycopg"
        assert pool.size() == 2
        assert pool._max_overflow == 1
        assert pool._timeout == 4
        assert pool._recycle == 10
        assert isinstance(migration.pool, NullPool)
        assert "password" not in repr(application)
        assert "password" not in str(application)
    finally:
        dispose_engine(application)
        dispose_engine(migration)


def test_disposal_and_no_global_engine() -> None:
    from mayak import persistence

    assert not any(
        name in vars(persistence)
        for name in ("_ENGINE", "application_engine", "migration_engine")
    )
    engine = create_engine(URL.create("postgresql+psycopg", username="test_user", database="mayak"))
    dispose_engine(engine)
