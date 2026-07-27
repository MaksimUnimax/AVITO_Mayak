"""One-shot, idempotent PostgreSQL role and schema bootstrap."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Final

import psycopg
from psycopg import sql

from mayak.persistence.config import (
    APPLICATION_SECRET_PATH,
    DATABASE_APPLICATION_USER,
    DATABASE_MIGRATION_USER,
    DATABASE_NAME,
    MIGRATION_SECRET_PATH,
    BootstrapDatabaseSettings,
    build_bootstrap_connect_kwargs,
    resolve_secret_file,
)

BOOTSTRAP_LOCK_KEY: Final[int] = 7342190309
_MIGRATION_SETTING: Final = "mayak.bootstrap.migration_password"
_APPLICATION_SETTING: Final = "mayak.bootstrap.application_password"


class BootstrapInvariantError(RuntimeError):
    """A redacted, operator-actionable bootstrap invariant failure."""


@dataclass(frozen=True, slots=True)
class BootstrapResult:
    migration_role: str
    application_role: str
    schema: str
    migration_role_valid: bool
    application_role_valid: bool
    schema_owner_valid: bool
    application_schema_create: bool
    current_object_grants: bool


ConnectionFactory = Callable[..., Any]


def _q(value: str) -> sql.Identifier:
    return sql.Identifier(value)


def _execute(cursor: Any, statement: sql.Composable, params: tuple[Any, ...] = ()) -> None:
    cursor.execute(statement, params)


def _role_sql(role: str, setting: str) -> sql.Composed:
    role_id = _q(role)
    return sql.SQL("""
DO $rf09$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = {role_literal}) THEN
    CREATE ROLE {role_name} LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT
      NOREPLICATION NOBYPASSRLS;
  ELSE
    ALTER ROLE {role_name} LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT
      NOREPLICATION NOBYPASSRLS;
  END IF;
  EXECUTE format('ALTER ROLE %I PASSWORD %L', {role_literal}, current_setting({setting_literal}));
END
$rf09$;
""").format(
        role_name=role_id,
        role_literal=sql.Literal(role),
        setting_literal=sql.Literal(setting),
    )


def _verify_roles(cursor: Any) -> tuple[bool, bool]:
    _execute(
        cursor,
        sql.SQL(
            "SELECT rolname, rolsuper, rolcreatedb, rolcreaterole, rolinherit, "
            "rolreplication, rolbypassrls FROM pg_roles WHERE rolname IN ({}, {})"
        ).format(_q(DATABASE_MIGRATION_USER), _q(DATABASE_APPLICATION_USER)),
    )
    rows = cursor.fetchall()
    expected = {
        DATABASE_MIGRATION_USER: False,
        DATABASE_APPLICATION_USER: False,
    }
    for row in rows:
        if len(row) >= 7 and row[0] in expected:
            expected[row[0]] = not any(row[1:7])
    if not all(expected.values()):
        raise BootstrapInvariantError("role capability invariant failed")
    return expected[DATABASE_MIGRATION_USER], expected[DATABASE_APPLICATION_USER]


def _verify_memberships(cursor: Any) -> None:
    _execute(
        cursor,
        sql.SQL(
            "SELECT 1 FROM pg_auth_members m "
            "JOIN pg_roles member ON member.oid = m.member "
            "JOIN pg_roles granted ON granted.oid = m.roleid "
            "WHERE member.rolname IN ({}, {}) "
            "AND granted.rolname IN ({}, {})"
        ).format(
            _q(DATABASE_MIGRATION_USER),
            _q(DATABASE_APPLICATION_USER),
            _q("mayak"),
            _q(DATABASE_MIGRATION_USER),
        ),
    )
    if cursor.fetchall():
        raise BootstrapInvariantError("role membership invariant failed")


def bootstrap_database(
    *,
    settings: BootstrapDatabaseSettings | None = None,
    connection_factory: ConnectionFactory = psycopg.connect,
    migration_secret_path: Any = MIGRATION_SECRET_PATH,
    application_secret_path: Any = APPLICATION_SECRET_PATH,
) -> BootstrapResult:
    """Apply the accepted RF-09 role/schema boundary in one transaction."""
    kwargs = build_bootstrap_connect_kwargs(settings)
    migration_secret = resolve_secret_file(migration_secret_path).as_text()
    application_secret = resolve_secret_file(application_secret_path).as_text()
    connection = None
    cursor = None
    try:
        connection = connection_factory(**kwargs)
        cursor = connection.cursor()
        _execute(cursor, sql.SQL("SELECT pg_advisory_xact_lock(%s)"), (BOOTSTRAP_LOCK_KEY,))
        _execute(
            cursor,
            sql.SQL("SELECT set_config(%s, %s, true)"),
            (_MIGRATION_SETTING, migration_secret),
        )
        _execute(
            cursor,
            sql.SQL("SELECT set_config(%s, %s, true)"),
            (_APPLICATION_SETTING, application_secret),
        )
        _execute(cursor, _role_sql(DATABASE_MIGRATION_USER, _MIGRATION_SETTING))
        _execute(cursor, _role_sql(DATABASE_APPLICATION_USER, _APPLICATION_SETTING))
        _execute(
            cursor,
            sql.SQL(
                "REVOKE {bootstrap} FROM {migration}; "
                "REVOKE {bootstrap} FROM {application}; "
                "REVOKE {migration} FROM {application};"
            ).format(
                migration=_q(DATABASE_MIGRATION_USER),
                application=_q(DATABASE_APPLICATION_USER),
                bootstrap=_q("mayak"),
            ),
        )
        _execute(
            cursor,
            sql.SQL(
                "REVOKE CONNECT, TEMPORARY ON DATABASE {db} FROM PUBLIC; "
                "GRANT CONNECT ON DATABASE {db} TO {migration}, {application};"
            ).format(
                db=_q(DATABASE_NAME),
                migration=_q(DATABASE_MIGRATION_USER),
                application=_q(DATABASE_APPLICATION_USER),
            ),
        )
        _execute(cursor, sql.SQL("REVOKE CREATE ON SCHEMA public FROM PUBLIC"))
        _execute(
            cursor,
            sql.SQL(
                "SELECT pg_get_userbyid(n.nspowner) FROM pg_namespace n WHERE n.nspname = {schema}"
            ).format(schema=sql.Literal("mayak")),
        )
        owner_row = cursor.fetchone()
        if owner_row is None:
            _execute(
                cursor,
                sql.SQL("CREATE SCHEMA IF NOT EXISTS {schema} AUTHORIZATION {owner}").format(
                    schema=_q("mayak"), owner=_q(DATABASE_MIGRATION_USER)
                ),
            )
            _execute(
                cursor,
                sql.SQL(
                    "SELECT pg_get_userbyid(n.nspowner) FROM pg_namespace n "
                    "WHERE n.nspname = {schema}"
                ).format(schema=sql.Literal("mayak")),
            )
            owner_row = cursor.fetchone()
        if not owner_row or owner_row[0] != DATABASE_MIGRATION_USER:
            raise BootstrapInvariantError("schema owner invariant failed")
        _execute(
            cursor,
            sql.SQL(
                "REVOKE ALL ON SCHEMA {schema} FROM PUBLIC; "
                "GRANT USAGE, CREATE ON SCHEMA {schema} TO {migration}; "
                "GRANT USAGE ON SCHEMA {schema} TO {application}; "
                "REVOKE CREATE ON SCHEMA {schema} FROM {application};"
            ).format(
                schema=_q("mayak"),
                migration=_q(DATABASE_MIGRATION_USER),
                application=_q(DATABASE_APPLICATION_USER),
            ),
        )
        _execute(
            cursor,
            sql.SQL(
                "ALTER DEFAULT PRIVILEGES FOR ROLE {owner} IN SCHEMA {schema} "
                "REVOKE ALL ON TABLES FROM PUBLIC, {application}; "
                "ALTER DEFAULT PRIVILEGES FOR ROLE {owner} IN SCHEMA {schema} "
                "GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {application}; "
                "ALTER DEFAULT PRIVILEGES FOR ROLE {owner} IN SCHEMA {schema} "
                "REVOKE ALL ON SEQUENCES FROM PUBLIC, {application}; "
                "ALTER DEFAULT PRIVILEGES FOR ROLE {owner} IN SCHEMA {schema} "
                "GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO {application};"
            ).format(
                owner=_q(DATABASE_MIGRATION_USER),
                schema=_q("mayak"),
                application=_q(DATABASE_APPLICATION_USER),
            ),
        )
        migration_valid, application_valid = _verify_roles(cursor)
        _verify_memberships(cursor)
        _execute(
            cursor,
            sql.SQL(
                "SELECT has_schema_privilege({application}, {schema}, 'USAGE'), "
                "has_schema_privilege({application}, {schema}, 'CREATE'), "
                "has_schema_privilege({migration}, {schema}, 'USAGE'), "
                "has_schema_privilege({migration}, {schema}, 'CREATE'), "
                "has_schema_privilege('public', {schema}, 'CREATE')"
            ).format(
                application=sql.Literal(DATABASE_APPLICATION_USER),
                migration=sql.Literal(DATABASE_MIGRATION_USER),
                schema=sql.Literal("mayak"),
            ),
        )
        privileges = cursor.fetchone()
        if (
            not privileges
            or privileges[0] is not True
            or privileges[1] is not False
            or privileges[2] is not True
            or privileges[3] is not True
            or privileges[4] is not False
        ):
            raise BootstrapInvariantError("schema privilege invariant failed")
        _execute(
            cursor,
            sql.SQL("SELECT set_config(%s, %s, true), set_config(%s, %s, true)"),
            (_MIGRATION_SETTING, "", _APPLICATION_SETTING, ""),
        )
        connection.commit()
        return BootstrapResult(
            DATABASE_MIGRATION_USER,
            DATABASE_APPLICATION_USER,
            "mayak",
            migration_valid,
            application_valid,
            True,
            False,
            False,
        )
    except BootstrapInvariantError:
        if connection is not None:
            connection.rollback()
        raise
    except Exception as exc:
        if connection is not None:
            connection.rollback()
        raise BootstrapInvariantError("database bootstrap failed") from exc
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()


def main() -> int:
    try:
        bootstrap_database()
    except (BootstrapInvariantError, OSError, ValueError) as exc:
        classification = type(exc).__name__
        print(f"RF09_DATABASE_BOOTSTRAP_ERROR: {classification}")
        return 1
    print("RF09_DATABASE_BOOTSTRAP_COMPLETE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
