from __future__ import annotations

import importlib
import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy.sql.elements import TextClause

from mayak.persistence.migration import (
    MIGRATION_LOCK_KEY,
    MigrationSerializationError,
    serialized_migration,
)

ROOT = Path(__file__).parents[2]


class FakeResult:
    def __init__(self, value: object) -> None:
        self.value = value

    def scalar(self) -> object:
        return self.value


class FakeConnection:
    def __init__(self, values: list[object]) -> None:
        self.values = values
        self.calls: list[tuple[str, dict[str, object]]] = []

    def execute(self, statement: TextClause, params: dict[str, object]) -> FakeResult:
        self.calls.append((str(statement), params))
        return FakeResult(self.values.pop(0))


@pytest.mark.parametrize("outcome", [False, None, "true", 1, object()])
def test_lock_acquisition_is_fail_fast_for_non_literal_true(outcome: object) -> None:
    connection = FakeConnection([outcome])
    with pytest.raises(MigrationSerializationError, match="migration serialization unavailable"):
        with serialized_migration(connection):
            raise AssertionError("body must not run")
    assert len(connection.calls) == 1
    assert connection.calls[0][0] == "SELECT pg_try_advisory_lock(:lock_key)"
    assert connection.calls[0][1] == {"lock_key": MIGRATION_LOCK_KEY}


def test_normal_execution_releases_once_with_bound_key() -> None:
    connection = FakeConnection([True, True])
    with serialized_migration(connection):
        pass
    assert [call[0] for call in connection.calls] == [
        "SELECT pg_try_advisory_lock(:lock_key)",
        "SELECT pg_advisory_unlock(:lock_key)",
    ]
    assert all(call[1] == {"lock_key": MIGRATION_LOCK_KEY} for call in connection.calls)


def test_body_exception_is_unchanged_and_unlock_failure_does_not_mask() -> None:
    connection = FakeConnection([True, False])
    original = ValueError("body")
    with pytest.raises(ValueError) as caught:
        with serialized_migration(connection):
            raise original
    assert caught.value is original


def test_successful_body_with_unlock_failure_fails_safely() -> None:
    connection = FakeConnection([True, None])
    with pytest.raises(MigrationSerializationError, match="migration serialization release failed"):
        with serialized_migration(connection):
            pass


def test_static_lock_boundary_has_no_blocking_xact_retry_or_secret_behavior() -> None:
    source = (ROOT / "src/mayak/persistence/migration.py").read_text(encoding="utf-8")
    assert source.count("pg_try_advisory_lock") == 1
    assert source.count("pg_advisory_unlock") == 1
    assert "pg_advisory_lock(" not in source
    assert "pg_advisory_xact_lock" not in source
    assert "sleep" not in source.lower()
    assert "retry" not in source.lower()
    assert ":lock_key" in source
    assert "password" not in source.lower()
    assert "secret" not in source.lower()


def test_environment_uses_one_transaction_per_revision_and_serialized_online_run() -> None:
    source = (ROOT / "alembic" / "env.py").read_text(encoding="utf-8")
    assert '"transaction_per_migration": True' in source
    assert "with serialized_migration(connection):" in source
    online = source[
        source.index("def run_migrations_online") : source.index("def run_migrations()")
    ]
    assert online.index("with serialized_migration(connection):") < online.index(
        "context.run_migrations()"
    )
    offline = source[
        source.index("def run_migrations_offline") : source.index("def run_migrations_online")
    ]
    assert "serialized_migration" not in offline


def test_importing_migration_module_is_inert() -> None:
    module = importlib.reload(sys.modules["mayak.persistence.migration"])
    assert module.MIGRATION_LOCK_KEY == 7342190310


def test_database_independent_alembic_topology() -> None:
    commands = [("heads",), ("history",), ("branches",), ("show", "RF09_BOOTSTRAP")]
    for command in commands:
        argv = [sys.executable, "-m", "alembic", "-c", "alembic.ini", *command]
        result = subprocess.run(argv, cwd=ROOT, check=True, capture_output=True, text=True)
        output = result.stdout + result.stderr
        assert "mayak_database_migration_password" not in output
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "-c", "alembic.ini", "heads"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "RF09_BOOTSTRAP" in result.stdout
