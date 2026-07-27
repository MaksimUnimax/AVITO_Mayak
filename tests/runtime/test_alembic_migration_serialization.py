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


class FakeRowResult:
    def __init__(self, rows: list[object], *, extraction_error: bool = False) -> None:
        self.rows = rows
        self.extraction_error = extraction_error

    def one(self) -> object:
        if self.extraction_error:
            raise RuntimeError("driver detail")
        if len(self.rows) != 1:
            raise RuntimeError("wrong row cardinality")
        return self.rows[0]


class MalformedRow:
    def __len__(self) -> int:
        raise TypeError("malformed row")


class MalformedResult:
    pass


class FakeConnection:
    def __init__(self, results: list[object]) -> None:
        self.results = results
        self.calls: list[tuple[str, dict[str, object]]] = []

    def execute(self, statement: TextClause, params: dict[str, object]) -> object:
        self.calls.append((str(statement), params))
        return self.results.pop(0)


def result(*rows: object, extraction_error: bool = False) -> FakeRowResult:
    return FakeRowResult(list(rows), extraction_error=extraction_error)


ACQUISITION_FAILURES = [
    pytest.param(result(), id="zero-rows"),
    pytest.param(result((True,), (True,)), id="duplicate-true-rows"),
    pytest.param(result((True,), (False,)), id="different-duplicate-rows"),
    pytest.param(result(()), id="empty-row"),
    pytest.param(result((True, "extra")), id="multi-column-row"),
    pytest.param(result(MalformedRow()), id="malformed-row"),
    pytest.param(MalformedResult(), id="missing-one-api"),
    pytest.param(result(extraction_error=True), id="one-extraction-error"),
    pytest.param(result((False,)), id="false"),
    pytest.param(result((None,)), id="none"),
    pytest.param(result((1,)), id="integer-one"),
    pytest.param(result(("true",)), id="string-true"),
    pytest.param(result((object(),)), id="arbitrary-object"),
]


@pytest.mark.parametrize("lock_result", ACQUISITION_FAILURES)
def test_lock_acquisition_rejects_invalid_cardinality_shape_and_value(lock_result: object) -> None:
    connection = FakeConnection([lock_result])
    with pytest.raises(MigrationSerializationError) as caught:
        with serialized_migration(connection):
            raise AssertionError("body must not run")
    assert str(caught.value) == "migration serialization unavailable"
    assert len(connection.calls) == 1
    assert connection.calls[0][0] == "SELECT pg_try_advisory_lock(:lock_key)"
    assert connection.calls[0][1] == {"lock_key": MIGRATION_LOCK_KEY}


@pytest.mark.parametrize(
    "lock_result",
    [
        pytest.param(result(), id="zero-rows"),
        pytest.param(result((True,), (True,)), id="duplicate-true-rows"),
        pytest.param(result(()), id="empty-row"),
        pytest.param(result((True, "extra")), id="multi-column-row"),
        pytest.param(result(MalformedRow()), id="malformed-row"),
        pytest.param(result(extraction_error=True), id="one-extraction-error"),
        pytest.param(result((False,)), id="false"),
        pytest.param(result((None,)), id="none"),
        pytest.param(result((1,)), id="integer-one"),
        pytest.param(result(("true",)), id="string-true"),
    ],
)
def test_lock_release_rejects_invalid_cardinality_shape_and_value(lock_result: object) -> None:
    connection = FakeConnection([result((True,)), lock_result])
    with pytest.raises(MigrationSerializationError) as caught:
        with serialized_migration(connection):
            pass
    assert str(caught.value) == "migration serialization release failed"
    assert [call[0] for call in connection.calls] == [
        "SELECT pg_try_advisory_lock(:lock_key)",
        "SELECT pg_advisory_unlock(:lock_key)",
    ]


def test_release_failure_after_body_failure_does_not_mask_original_exception() -> None:
    connection = FakeConnection([result((True,)), result((True,), (True,))])
    original = ValueError("body")
    with pytest.raises(ValueError) as caught:
        with serialized_migration(connection):
            raise original
    assert caught.value is original


@pytest.mark.parametrize("outcome", [False, None, "true", 1, object()])
def test_lock_acquisition_is_fail_fast_for_non_literal_true(outcome: object) -> None:
    connection = FakeConnection([result((outcome,))])
    with pytest.raises(MigrationSerializationError, match="migration serialization unavailable"):
        with serialized_migration(connection):
            raise AssertionError("body must not run")
    assert len(connection.calls) == 1
    assert connection.calls[0][0] == "SELECT pg_try_advisory_lock(:lock_key)"
    assert connection.calls[0][1] == {"lock_key": MIGRATION_LOCK_KEY}


def test_normal_execution_releases_once_with_bound_key() -> None:
    connection = FakeConnection([result((True,)), result((True,))])
    with serialized_migration(connection):
        pass
    assert [call[0] for call in connection.calls] == [
        "SELECT pg_try_advisory_lock(:lock_key)",
        "SELECT pg_advisory_unlock(:lock_key)",
    ]
    assert all(call[1] == {"lock_key": MIGRATION_LOCK_KEY} for call in connection.calls)


def test_body_exception_is_unchanged_and_unlock_failure_does_not_mask() -> None:
    connection = FakeConnection([result((True,)), result((False,))])
    original = ValueError("body")
    with pytest.raises(ValueError) as caught:
        with serialized_migration(connection):
            raise original
    assert caught.value is original


def test_successful_body_with_unlock_failure_fails_safely() -> None:
    connection = FakeConnection([result((True,)), result((None,))])
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
    assert ".scalar(" not in source
    assert ".scalar_one(" not in source
    assert ".scalars(" not in source
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
