from pathlib import Path

import pytest

from mayak.persistence.bootstrap import (
    BOOTSTRAP_LOCK_KEY,
    BootstrapInvariantError,
    BootstrapResult,
    bootstrap_database,
)
from mayak.persistence.config import BootstrapDatabaseSettings

MIGRATION = "mayak_migration"
APPLICATION = "mayak_application"


def valid_roles() -> list[tuple[object, ...]]:
    return [
        (MIGRATION, True, False, False, False, False, False, False),
        (APPLICATION, True, False, False, False, False, False, False),
    ]


class Cursor:
    def __init__(
        self,
        *,
        roles: list[tuple[object, ...]] | None = None,
        memberships: list[tuple[object, ...]] | None = None,
        privileges: tuple[object, ...] = (True, False, True, True, False, False),
        wrong_owner: bool = False,
    ) -> None:
        self.roles = valid_roles() if roles is None else roles
        self.memberships = [] if memberships is None else memberships
        self.privileges = privileges
        self.wrong_owner = wrong_owner
        self.executed: list[tuple[str, tuple[object, ...]]] = []
        self.closed = False

    def execute(self, query: object, params: tuple[object, ...] = ()) -> None:
        rendered = query.as_string(None) if hasattr(query, "as_string") else str(query)
        self.executed.append((rendered, params))

    def fetchone(self) -> tuple[object, ...] | None:
        query = self.executed[-1][0]
        if "pg_get_userbyid" in query:
            return ("foreign_owner" if self.wrong_owner else MIGRATION,)
        if "has_schema_privilege" in query:
            return self.privileges
        return None

    def fetchall(self) -> list[tuple[object, ...]]:
        query = self.executed[-1][0]
        if "pg_auth_members" in query:
            return self.memberships
        if "FROM pg_roles" in query:
            return self.roles
        return []

    def close(self) -> None:
        self.closed = True


class Connection:
    def __init__(
        self,
        *,
        roles: list[tuple[object, ...]] | None = None,
        memberships: list[tuple[object, ...]] | None = None,
        privileges: tuple[object, ...] = (True, False, True, True, False, False),
        wrong_owner: bool = False,
    ) -> None:
        self.cursor_obj = Cursor(
            roles=roles,
            memberships=memberships,
            privileges=privileges,
            wrong_owner=wrong_owner,
        )
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


def run_bootstrap(tmp_path: Path, connection: Connection) -> BootstrapResult:
    bootstrap, migration, application = _files(tmp_path)
    return bootstrap_database(
        settings=BootstrapDatabaseSettings(secret_path=bootstrap),
        connection_factory=lambda **_: connection,
        migration_secret_path=migration,
        application_secret_path=application,
    )


def test_synthetic_success_is_transactional_and_secret_safe(tmp_path: Path) -> None:
    connection = Connection()
    result = run_bootstrap(tmp_path, connection)
    assert isinstance(result, BootstrapResult)
    assert result.current_object_grants is False
    assert connection.commits == 1 and connection.rollbacks == 0
    assert connection.cursor_obj.closed and connection.closed
    assert connection.cursor_obj.executed[0][1] == (BOOTSTRAP_LOCK_KEY,)
    all_text = " ".join(query for query, _ in connection.cursor_obj.executed)
    all_params = [value for _, params in connection.cursor_obj.executed for value in params]
    assert "synthetic-migration-only" not in all_text
    assert "synthetic-application-only" not in all_text
    assert "synthetic-migration-only" in all_params
    assert "synthetic-application-only" in all_params


def test_role_query_uses_bound_values_and_login_capability(tmp_path: Path) -> None:
    connection = Connection()
    run_bootstrap(tmp_path, connection)
    query, params = next((q, p) for q, p in connection.cursor_obj.executed if "rolname IN" in q)
    assert "rolname, rolcanlogin, rolsuper" in query
    assert "rolname IN (%s, %s)" in query
    assert params == (MIGRATION, APPLICATION)
    assert '"mayak_migration"' not in query and '"mayak_application"' not in query


@pytest.mark.parametrize("index", range(1, 8))
def test_each_prohibited_role_capability_fails_safely(tmp_path: Path, index: int) -> None:
    roles = valid_roles()
    row = list(roles[0])
    row[index] = False if index == 1 else True
    roles[0] = tuple(row)
    connection = Connection(roles=roles)
    with pytest.raises(BootstrapInvariantError, match="^role capability invariant failed$"):
        run_bootstrap(tmp_path, connection)
    assert connection.rollbacks == 1


@pytest.mark.parametrize(
    "roles",
    [
        [valid_roles()[1]],
    [
        valid_roles()[0],
        valid_roles()[1],
        ("unexpected", True, False, False, False, False, False, False),
    ],
        [valid_roles()[0], valid_roles()[0], valid_roles()[1]],
        [(MIGRATION, True, False, False, False, False, False)],
    ],
)
def test_role_cardinality_identity_and_width_fail_safely(
    tmp_path: Path, roles: list[tuple[object, ...]]
) -> None:
    connection = Connection(roles=roles)
    with pytest.raises(BootstrapInvariantError, match="^role capability invariant failed$"):
        run_bootstrap(tmp_path, connection)


@pytest.mark.parametrize("member", [MIGRATION, APPLICATION])
def test_any_membership_is_rejected_without_allowlist(tmp_path: Path, member: str) -> None:
    connection = Connection(memberships=[(member, "unrelated_synthetic_role")])
    with pytest.raises(BootstrapInvariantError, match="^role membership invariant failed$"):
        run_bootstrap(tmp_path, connection)
    query, params = next(
        (q, p) for q, p in connection.cursor_obj.executed if "pg_auth_members" in q
    )
    assert "member.rolname IN (%s, %s)" in query
    assert "granted.rolname IN" not in query
    assert params == (MIGRATION, APPLICATION)


def test_no_membership_rows_pass(tmp_path: Path) -> None:
    connection = Connection()
    run_bootstrap(tmp_path, connection)
    assert any("pg_auth_members" in query for query, _ in connection.cursor_obj.executed)


@pytest.mark.parametrize(
    "privileges",
    [
        (True, False, True, True, True, False),
        (True, True, True, True, False, False),
        (False, False, True, True, False, False),
        (True, False, False, True, False, False),
        (True, False, True, False, False, False),
        (True, False, True, True, False, True),
        (True, False, True, True, False),
    ],
)
def test_schema_privilege_tuple_is_exact_and_safe(
    tmp_path: Path, privileges: tuple[object, ...]
) -> None:
    connection = Connection(privileges=privileges)
    with pytest.raises(BootstrapInvariantError, match="^schema privilege invariant failed$"):
        run_bootstrap(tmp_path, connection)
    query = next(q for q, _ in connection.cursor_obj.executed if "has_schema_privilege" in q)
    assert "'public', 'public', 'CREATE'" in query
    assert "'public', 'mayak', 'CREATE'" in query


def test_schema_privilege_success_checks_both_public_schemas(tmp_path: Path) -> None:
    connection = Connection()
    run_bootstrap(tmp_path, connection)
    query = next(q for q, _ in connection.cursor_obj.executed if "has_schema_privilege" in q)
    assert query.count("has_schema_privilege") == 6


def test_wrong_schema_owner_rolls_back_and_closes(tmp_path: Path) -> None:
    connection = Connection(wrong_owner=True)
    with pytest.raises(BootstrapInvariantError, match="^schema owner invariant failed$"):
        run_bootstrap(tmp_path, connection)
    assert connection.rollbacks == 1
    assert connection.commits == 0
    assert connection.cursor_obj.closed and connection.closed


def test_failure_is_redacted_and_does_not_print_sql_or_secrets(tmp_path: Path) -> None:
    connection = Connection(memberships=[(MIGRATION, "secret-like-role")])
    with pytest.raises(BootstrapInvariantError) as raised:
        run_bootstrap(tmp_path, connection)
    message = str(raised.value)
    assert "secret-like-role" not in message
    assert "pg_auth_members" not in message
    assert "synthetic-" not in message
