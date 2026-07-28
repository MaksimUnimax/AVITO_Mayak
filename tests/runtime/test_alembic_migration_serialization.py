from __future__ import annotations

import importlib
import subprocess
import sys
from pathlib import Path
from typing import Any

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
        self.transaction = False
        self.commits = 0
        self.rollbacks = 0

    def execute(self, statement: TextClause, params: dict[str, object]) -> object:
        self.calls.append((str(statement), params))
        self.transaction = True
        return self.results.pop(0)

    def in_transaction(self) -> bool:
        return self.transaction

    def commit(self) -> None:
        self.commits += 1
        self.transaction = False

    def rollback(self) -> None:
        self.rollbacks += 1
        self.transaction = False


class LifecycleConnection(FakeConnection):
    def __init__(self, results: list[object]) -> None:
        super().__init__(results)
        self.events: list[str] = []
        self.fail_commit = False
        self.fail_rollback = False
        self.fail_state = False
        self.state_after_commit = False
        self.lock_held = False

    def execute(self, statement: TextClause, params: dict[str, object]) -> object:
        self.events.append(str(statement))
        self.transaction = True
        if "pg_try_advisory_lock" in str(statement):
            candidate = self.results[0]
            self.lock_held = isinstance(candidate, FakeRowResult) and candidate.rows == [(True,)]
        elif "pg_advisory_unlock" in str(statement):
            self.lock_held = False
        return super().execute(statement, params)

    def in_transaction(self) -> bool:
        if self.fail_state:
            raise RuntimeError("driver detail")
        return self.transaction

    def commit(self) -> None:
        self.events.append("commit")
        self.commits += 1
        if self.fail_commit:
            raise RuntimeError("driver detail")
        self.transaction = self.state_after_commit

    def rollback(self) -> None:
        self.events.append("rollback")
        self.rollbacks += 1
        if self.fail_rollback:
            raise RuntimeError("driver detail")
        self.transaction = False


def lifecycle_connection() -> LifecycleConnection:
    return LifecycleConnection([result((True,)), result((True,))])


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
    module = importlib.import_module("mayak.persistence.migration")
    assert module.MIGRATION_LOCK_KEY == 7342190310


def test_database_independent_alembic_topology() -> None:
    commands = [("heads",), ("history",), ("branches",), ("show", "RF09_BOOTSTRAP")]

    def run_alembic(*command: str) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "-c", "alembic.ini", *command],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        output = result.stdout + result.stderr
        assert "mayak_database_migration_password" not in output
        return result

    for command in commands:
        run_alembic(*command)

    heads = run_alembic("heads").stdout
    head_lines = [line.strip() for line in heads.splitlines() if line.strip()]
    assert len(head_lines) == 1
    assert head_lines[0].endswith("(head)")
    assert head_lines[0].split()[0]

    history = run_alembic("history").stdout
    assert "RF09_BOOTSTRAP" in history

    shown = run_alembic("show", "RF09_BOOTSTRAP").stdout
    assert "RF09_BOOTSTRAP" in shown

    assert run_alembic("branches").stdout.strip() == ""


def test_clean_entry_state_is_required() -> None:
    connection = lifecycle_connection()
    entered = False
    with serialized_migration(connection):
        entered = True
    assert entered
    assert connection.events[:2] == ["SELECT pg_try_advisory_lock(:lock_key)", "commit"]


def test_pre_existing_transaction_is_rejected_before_lock_sql() -> None:
    connection = lifecycle_connection()
    connection.transaction = True
    with pytest.raises(MigrationSerializationError, match="migration serialization unavailable"):
        with serialized_migration(connection):
            raise AssertionError("body must not run")
    assert connection.calls == []
    assert connection.rollbacks == 0


def test_entry_state_inspection_failure_is_redacted_and_body_does_not_run() -> None:
    connection = lifecycle_connection()
    connection.fail_state = True
    with pytest.raises(MigrationSerializationError, match="migration serialization unavailable"):
        with serialized_migration(connection):
            raise AssertionError("body must not run")
    assert connection.calls == []


def test_non_boolean_entry_state_is_rejected() -> None:
    class NonBooleanState(LifecycleConnection):
        def in_transaction(self) -> Any:
            return 0

    connection = NonBooleanState([])
    with pytest.raises(MigrationSerializationError, match="migration serialization unavailable"):
        with serialized_migration(connection):
            raise AssertionError("body must not run")
    assert connection.calls == []


def test_acquisition_commit_precedes_body_and_body_is_clean() -> None:
    connection = lifecycle_connection()
    with serialized_migration(connection):
        assert connection.in_transaction() is False
        assert connection.lock_held
    assert connection.events == [
        "SELECT pg_try_advisory_lock(:lock_key)",
        "commit",
        "SELECT pg_advisory_unlock(:lock_key)",
        "commit",
    ]
    assert connection.rollbacks == 0


def test_acquisition_commit_failure_is_redacted_and_body_is_not_entered() -> None:
    connection = lifecycle_connection()
    connection.fail_commit = True
    with pytest.raises(MigrationSerializationError, match="migration serialization unavailable"):
        with serialized_migration(connection):
            raise AssertionError("body must not run")
    assert connection.calls[0] == (
        "SELECT pg_try_advisory_lock(:lock_key)",
        {"lock_key": MIGRATION_LOCK_KEY},
    )
    assert connection.events[1] == "commit"


def test_active_state_after_acquisition_commit_fails_closed() -> None:
    connection = lifecycle_connection()
    connection.state_after_commit = True
    with pytest.raises(MigrationSerializationError, match="migration serialization unavailable"):
        with serialized_migration(connection):
            raise AssertionError("body must not run")
    assert connection.rollbacks >= 1


def test_successful_body_rolls_back_unexpected_transaction_before_unlock() -> None:
    connection = lifecycle_connection()
    with serialized_migration(connection):
        connection.transaction = True
    assert connection.events == [
        "SELECT pg_try_advisory_lock(:lock_key)",
        "commit",
        "rollback",
        "SELECT pg_advisory_unlock(:lock_key)",
        "commit",
    ]
    assert connection.commits == 2


def test_unexpected_successful_body_transaction_is_never_committed() -> None:
    connection = lifecycle_connection()
    with serialized_migration(connection):
        connection.transaction = True
    assert connection.events.index("rollback") < connection.events.index(
        "SELECT pg_advisory_unlock(:lock_key)"
    )


def test_unlock_commit_failure_is_redacted() -> None:
    connection = lifecycle_connection()
    original_commit = connection.commit
    calls = 0

    def fail_second_commit() -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("driver detail")
        original_commit()

    connection.commit = fail_second_commit  # type: ignore[method-assign]
    with pytest.raises(MigrationSerializationError, match="migration serialization release failed"):
        with serialized_migration(connection):
            pass


def test_final_active_state_after_unlock_commit_fails_closed() -> None:
    connection = lifecycle_connection()
    commits = 0
    original_commit = connection.commit

    def active_after_unlock_commit() -> None:
        nonlocal commits
        commits += 1
        original_commit()
        if commits == 2:
            connection.transaction = True

    connection.commit = active_after_unlock_commit  # type: ignore[method-assign]
    with pytest.raises(MigrationSerializationError, match="migration serialization release failed"):
        with serialized_migration(connection):
            pass


def test_failed_body_rolls_back_active_transaction_and_preserves_identity() -> None:
    connection = lifecycle_connection()
    original = ValueError("body")
    with pytest.raises(ValueError) as caught:
        with serialized_migration(connection):
            connection.transaction = True
            raise original
    assert caught.value is original
    assert connection.events[-3:] == ["rollback", "SELECT pg_advisory_unlock(:lock_key)", "commit"]


def test_failed_body_never_commits_failed_work() -> None:
    connection = lifecycle_connection()
    with pytest.raises(ValueError):
        with serialized_migration(connection):
            connection.transaction = True
            raise ValueError("failed migration")
    assert connection.commits == 2
    assert connection.rollbacks == 1


def test_failed_body_rollback_failure_does_not_mask_original() -> None:
    connection = lifecycle_connection()
    connection.fail_rollback = True
    original = RuntimeError("original")
    with pytest.raises(RuntimeError) as caught:
        with serialized_migration(connection):
            connection.transaction = True
            raise original
    assert caught.value is original


def test_failed_body_unlock_failure_does_not_mask_original() -> None:
    connection = LifecycleConnection([result((True,)), result((False,))])
    original = RuntimeError("original")
    with pytest.raises(RuntimeError) as caught:
        with serialized_migration(connection):
            raise original
    assert caught.value is original


def test_failed_body_unlock_commit_failure_does_not_mask_original() -> None:
    connection = lifecycle_connection()
    commits = 0
    original_commit = connection.commit

    def fail_unlock_commit() -> None:
        nonlocal commits
        commits += 1
        if commits == 2:
            raise RuntimeError("driver detail")
        original_commit()

    connection.commit = fail_unlock_commit  # type: ignore[method-assign]
    original = RuntimeError("original")
    with pytest.raises(RuntimeError) as caught:
        with serialized_migration(connection):
            raise original
    assert caught.value is original


def test_keyboard_interrupt_is_preserved() -> None:
    connection = lifecycle_connection()
    original = KeyboardInterrupt()
    with pytest.raises(KeyboardInterrupt) as caught:
        with serialized_migration(connection):
            raise original
    assert caught.value is original


def test_source_has_transaction_boundary_safety_invariants() -> None:
    source = (ROOT / "src/mayak/persistence/migration.py").read_text(encoding="utf-8")
    assert source.count("in_transaction()") >= 2
    assert source.count("connection.commit()") >= 2
    assert source.count("connection.rollback()") >= 1
    assert "AUTOCOMMIT" not in source
    assert "begin_nested" not in source
    assert "DBAPI" not in source
