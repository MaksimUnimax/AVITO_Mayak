"""Canonical RF20 PostgreSQL companion tests.

These tests are intentionally collectable without a database.  Hosted CI sets
``RF20_REQUIRE_POSTGRES=1`` and a private DSN; in that mode a missing DSN or a
database failure is a test failure rather than a skip.
"""

from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from sqlalchemy import create_engine, text


def _engine():
    dsn = os.environ.get("RF20_DATABASE_URL")
    if not dsn:
        if os.environ.get("RF20_REQUIRE_POSTGRES") == "1":
            pytest.fail("RF20_DATABASE_URL is required for hosted PostgreSQL acceptance")
        pytest.skip("local PostgreSQL is intentionally not available")
    return create_engine(dsn, pool_pre_ping=True)


def test_support_events_have_physical_timezone_aware_timestamps() -> None:
    engine = _engine()
    with engine.connect() as connection:
        row = connection.execute(text("""
            select data_type, datetime_precision
            from information_schema.columns
            where table_schema = 'mayak' and table_name = 'support_case_events'
              and column_name = 'created_at'
        """)).mappings().one()
        assert row["data_type"] == "timestamp with time zone"


def test_postgresql_advisory_lock_serializes_independent_transactions() -> None:
    engine = _engine()
    lock_key = 87200420

    entered = Barrier(2)
    released = Barrier(2)

    def acquire() -> bool:
        with engine.connect() as connection:
            transaction = connection.begin()
            try:
                # pg_advisory_xact_lock returns void; select a separate
                # boolean marker and never coerce the void expression.
                connection.execute(text("select pg_advisory_xact_lock(:key)"), {"key": lock_key})
                entered.wait(timeout=5)
                released.wait(timeout=5)
                transaction.commit()
                return True
            except BaseException:
                transaction.rollback()
                raise

    def contender() -> bool:
        with engine.connect() as connection:
            entered.wait(timeout=5)
            with connection.begin():
                # A second independent transaction can only complete after A
                # commits.  pg_try_advisory_xact_lock must be false while A
                # owns the protected section.
                blocked = connection.execute(
                    text("select pg_try_advisory_xact_lock(:key)"), {"key": lock_key}
                ).scalar_one()
                released.wait(timeout=5)
                return blocked is False

    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(acquire)
        second = pool.submit(contender)
        assert first.result(timeout=10) is True
        assert second.result(timeout=10) is True
