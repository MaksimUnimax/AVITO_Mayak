from pathlib import Path

import pytest

from mayak.persistence.bootstrap import (
    BOOTSTRAP_LOCK_KEY,
    BootstrapInvariantError,
    BootstrapResult,
    bootstrap_database,
)
from mayak.persistence.config import BootstrapDatabaseSettings


class Cursor:
    def __init__(self, owner: "Connection", wrong_owner: bool = False) -> None:
        self.owner = owner
        self.queries: list[tuple[str, tuple[object, ...]]] = []
        self.closed = False
        self.wrong_owner = wrong_owner
        self.owner_query_count = 0

    def execute(self, query: object, params: tuple[object, ...] = ()) -> None:
        rendered = query.as_string(None) if hasattr(query, "as_string") else str(query)
        self.queries.append((rendered, params))

    def fetchone(self) -> tuple[object, ...] | None:
        query = self.queries[-1][0]
        if "pg_get_userbyid" in query:
            self.owner_query_count += 1
            return (("foreign_owner" if self.wrong_owner else "mayak_migration"),)
        if "has_schema_privilege" in query:
            return (True, False, True, True, False)
        return None

    def fetchall(self) -> list[tuple[object, ...]]:
        if "pg_auth_members" in self.queries[-1][0]:
            return []
        return [
            ("mayak_migration", False, False, False, False, False, False),
            ("mayak_application", False, False, False, False, False, False),
        ]

    def close(self) -> None:
        self.closed = True


class Connection:
    def __init__(self, wrong_owner: bool = False, fail: bool = False) -> None:
        self.cursor_obj = Cursor(self, wrong_owner)
        self.fail = fail
        self.commits = 0
        self.rollbacks = 0
        self.closed = False

    def cursor(self) -> Cursor:
        return self.cursor_obj

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1

    def close(self) -> None:
        self.closed = True


def _files(tmp_path: Path) -> tuple[Path, Path, Path]:
    bootstrap = tmp_path / "bootstrap"
    migration = tmp_path / "migration"
    application = tmp_path / "application"
    bootstrap.write_text("synthetic-bootstrap-only\n", encoding="utf-8")
    migration.write_text("synthetic-migration-only\n", encoding="utf-8")
    application.write_text("synthetic-application-only\n", encoding="utf-8")
    return bootstrap, migration, application


def test_synthetic_success_is_transactional_and_secret_safe(tmp_path: Path) -> None:
    bootstrap, migration, application = _files(tmp_path)
    connection = Connection()
    calls: list[tuple[str, int, str, str]] = []

    def connect_factory(**kwargs: object) -> Connection:
        calls.append(
            (str(kwargs["host"]), int(kwargs["port"]), str(kwargs["dbname"]), str(kwargs["user"]))
        )
        return connection

    result = bootstrap_database(
        settings=BootstrapDatabaseSettings(secret_path=bootstrap),
        connection_factory=connect_factory,
        migration_secret_path=migration,
        application_secret_path=application,
    )
    assert isinstance(result, BootstrapResult)
    assert result.current_object_grants is False
    assert len(calls) == 1
    assert calls[0] == ("mayak-postgres", 5432, "mayak", "mayak")
    assert connection.commits == 1 and connection.rollbacks == 0
    assert connection.cursor_obj.closed and connection.closed
    assert connection.cursor_obj.queries[0][0].startswith("SELECT pg_advisory_xact_lock")
    assert connection.cursor_obj.queries[0][1] == (BOOTSTRAP_LOCK_KEY,)
    all_text = " ".join(query for query, _ in connection.cursor_obj.queries)
    all_params = [value for _, params in connection.cursor_obj.queries for value in params]
    for secret in (
        "synthetic-bootstrap-only",
        "synthetic-migration-only",
        "synthetic-application-only",
    ):
        assert secret not in all_text
        assert secret not in repr(result)
    assert "synthetic-migration-only" in all_params
    assert "synthetic-application-only" in all_params


def test_wrong_schema_owner_rolls_back_and_closes(tmp_path: Path) -> None:
    bootstrap, migration, application = _files(tmp_path)
    connection = Connection(wrong_owner=True)
    with pytest.raises(BootstrapInvariantError, match="schema owner invariant failed"):
        bootstrap_database(
            settings=BootstrapDatabaseSettings(secret_path=bootstrap),
            connection_factory=lambda **_: connection,
            migration_secret_path=migration,
            application_secret_path=application,
        )
    assert connection.rollbacks == 1
    assert connection.commits == 0
    assert connection.cursor_obj.closed and connection.closed
