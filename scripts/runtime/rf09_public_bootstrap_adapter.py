"""RF-08's bounded adapter for the accepted RF-09 public bootstrap API.

The module is mounted read-only into the accepted application image by the
stage-55 executor.  It deliberately contains no bootstrap SQL and never
prints exception text, SQL, parameters, or secret material.
"""

from __future__ import annotations

import json
import os
import re
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

import psycopg

from mayak.persistence.bootstrap import (
    BootstrapInvariantError,
    BootstrapResult,
    bootstrap_database,
)
from mayak.persistence.config import BootstrapDatabaseSettings

SCHEMA_VERSION: Final = "rf08-post-recovery-bootstrap-v1"
INVARIANT_CODES: Final[dict[str, str]] = {
    "role capability invariant failed": "RF09_ROLE_CAPABILITY_INVARIANT_FAILED",
    "role membership invariant failed": "RF09_ROLE_MEMBERSHIP_INVARIANT_FAILED",
    "schema owner invariant failed": "RF09_SCHEMA_OWNER_INVARIANT_FAILED",
    "schema privilege invariant failed": "RF09_SCHEMA_PRIVILEGE_INVARIANT_FAILED",
    "database bootstrap failed": "RF09_DATABASE_BOOTSTRAP_FAILED",
}
OPERATION_IDS: Final[tuple[str, ...]] = (
    "RF09_CONNECT", "RF09_ADVISORY_LOCK", "RF09_SET_MIGRATION_CREDENTIAL",
    "RF09_SET_APPLICATION_CREDENTIAL", "RF09_UPSERT_MIGRATION_ROLE",
    "RF09_UPSERT_APPLICATION_ROLE", "RF09_REVOKE_ROLE_MEMBERSHIPS",
    "RF09_DATABASE_CONNECT_GRANTS", "RF09_PUBLIC_SCHEMA_REVOKE",
    "RF09_SCHEMA_OWNER_QUERY", "RF09_SCHEMA_CREATE", "RF09_SCHEMA_GRANTS",
    "RF09_DEFAULT_TABLE_PRIVILEGES", "RF09_DEFAULT_SEQUENCE_PRIVILEGES",
    "RF09_VERIFY_ROLE_CAPABILITIES", "RF09_VERIFY_ROLE_MEMBERSHIPS",
    "RF09_VERIFY_SCHEMA_PRIVILEGES", "RF09_CLEAR_TRANSACTION_SETTINGS",
    "RF09_COMMIT",
)
_SAFE_SQLSTATE = re.compile(r"^[0-9A-Z]{5}$")


def _static_fragments(statement: Any) -> tuple[str, ...]:
    """Read only SQL.Composable structure, never identifiers or values."""
    if type(statement).__name__ == "SQL":
        value = getattr(statement, "_obj", None)
        return (value,) if isinstance(value, str) else ()
    sequence = getattr(statement, "_obj", None)
    if isinstance(sequence, (list, tuple)):
        return tuple(fragment for item in sequence for fragment in _static_fragments(item))
    return ()


def classify_statement(statement: Any) -> str:
    fragments = " ".join(_static_fragments(statement)).upper()
    if "PG_ADVISORY_XACT_LOCK" in fragments:
        return "RF09_ADVISORY_LOCK"
    if "SET_CONFIG" in fragments and "MIGRATION_PASSWORD" in fragments:
        return "RF09_SET_MIGRATION_CREDENTIAL"
    if "SET_CONFIG" in fragments and "APPLICATION_PASSWORD" in fragments:
        return "RF09_SET_APPLICATION_CREDENTIAL"
    if "CREATE ROLE" in fragments:
        return (
            "RF09_UPSERT_MIGRATION_ROLE"
            if "MIGRATION" in fragments else "RF09_UPSERT_APPLICATION_ROLE"
        )
    if "REVOKE" in fragments and "CONNECT" not in fragments and "SCHEMA" not in fragments:
        return "RF09_REVOKE_ROLE_MEMBERSHIPS"
    if "REVOKE CONNECT" in fragments or "GRANT CONNECT" in fragments:
        return "RF09_DATABASE_CONNECT_GRANTS"
    if "REVOKE CREATE ON SCHEMA PUBLIC" in fragments:
        return "RF09_PUBLIC_SCHEMA_REVOKE"
    if "PG_GET_USERBYID" in fragments:
        return "RF09_SCHEMA_OWNER_QUERY"
    if "CREATE SCHEMA" in fragments:
        return "RF09_SCHEMA_CREATE"
    if "REVOKE ALL ON SCHEMA" in fragments:
        return "RF09_SCHEMA_GRANTS"
    if "ALTER DEFAULT PRIVILEGES" in fragments and "ON TABLES" in fragments:
        return "RF09_DEFAULT_TABLE_PRIVILEGES"
    if "ALTER DEFAULT PRIVILEGES" in fragments and "ON SEQUENCES" in fragments:
        return "RF09_DEFAULT_SEQUENCE_PRIVILEGES"
    if "ROLNAME" in fragments and "ROLCANLOGIN" in fragments:
        return "RF09_VERIFY_ROLE_CAPABILITIES"
    if "PG_AUTH_MEMBERS" in fragments:
        return "RF09_VERIFY_ROLE_MEMBERSHIPS"
    if "HAS_SCHEMA_PRIVILEGE" in fragments:
        return "RF09_VERIFY_SCHEMA_PRIVILEGES"
    if "SET_CONFIG" in fragments:
        return "RF09_CLEAR_TRANSACTION_SETTINGS"
    return "RF09_UNRECOGNIZED_OPERATION"


def _sqlstate(exc: BaseException) -> str | None:
    value = getattr(exc, "sqlstate", None) or getattr(getattr(exc, "diag", None), "sqlstate", None)
    return value if isinstance(value, str) and _SAFE_SQLSTATE.fullmatch(value) else None


@dataclass
class Observation:
    connection_attempted: bool = False
    connected: bool = False
    last_rf09_operation: str = "RF09_CONNECT"
    client_sqlstate: str | None = None
    cause_type: str | None = None
    committed: bool = False
    rolled_back: bool = False
    cursor_closed: bool = False
    connection_closed: bool = False


class CursorProxy:
    def __init__(self, cursor: Any, observation: Observation) -> None:
        self._cursor = cursor
        self._observation = observation

    def execute(self, statement: Any, params: Any = None) -> Any:
        operation = classify_statement(statement)
        self._observation.last_rf09_operation = operation
        if operation == "RF09_UNRECOGNIZED_OPERATION":
            raise RuntimeError("unrecognized RF-09 operation")
        try:
            if params is None:
                return self._cursor.execute(statement)
            return self._cursor.execute(statement, params)
        except BaseException as exc:
            self._observation.client_sqlstate = _sqlstate(exc)
            self._observation.cause_type = type(exc).__name__
            raise

    def __getattr__(self, name: str) -> Any:
        return getattr(self._cursor, name)

    def close(self) -> Any:
        try:
            return self._cursor.close()
        finally:
            self._observation.cursor_closed = True


class ConnectionProxy:
    def __init__(self, connection: Any, observation: Observation) -> None:
        self._connection = connection
        self._observation = observation

    def cursor(self, *args: Any, **kwargs: Any) -> CursorProxy:
        return CursorProxy(self._connection.cursor(*args, **kwargs), self._observation)

    def commit(self) -> Any:
        try:
            result = self._connection.commit()
            self._observation.committed = True
            self._observation.last_rf09_operation = "RF09_COMMIT"
            return result
        except BaseException as exc:
            self._observation.client_sqlstate = _sqlstate(exc)
            self._observation.cause_type = type(exc).__name__
            raise

    def rollback(self) -> Any:
        self._observation.rolled_back = True
        try:
            return self._connection.rollback()
        except BaseException as exc:
            self._observation.client_sqlstate = _sqlstate(exc)
            self._observation.cause_type = type(exc).__name__
            raise

    def __getattr__(self, name: str) -> Any:
        return getattr(self._connection, name)

    def close(self) -> Any:
        try:
            return self._connection.close()
        finally:
            self._observation.connection_closed = True


def _connect_factory(observation: Observation, **kwargs: Any) -> ConnectionProxy:
    observation.connection_attempted = True
    try:
        connection = psycopg.connect(**kwargs)
        observation.connected = True
        return ConnectionProxy(connection, observation)
    except BaseException as exc:
        observation.client_sqlstate = _sqlstate(exc)
        observation.cause_type = type(exc).__name__
        raise


def _base(observation: Observation) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "operation_id": "rf09.public.bootstrap",
        "run_id": os.environ.get("RF08_RUN_ID", str(uuid.uuid4())),
        "recovered_generation_id": os.environ.get("RF08_RECOVERED_GENERATION_ID", "UNKNOWN"),
        "connection_attempted": observation.connection_attempted,
        "connected": observation.connected,
        "last_rf09_operation": observation.last_rf09_operation,
        "bootstrap_outcome": "RF09_BOOTSTRAP_UNRECOGNIZED_FAILURE",
        "invariant_code": None,
        "client_sqlstate": observation.client_sqlstate,
        "cause_type": observation.cause_type,
        "committed": observation.committed,
        "rolled_back": observation.rolled_back,
        "cursor_closed": observation.cursor_closed,
        "connection_closed": observation.connection_closed,
        "migration_role_valid": None,
        "application_role_valid": None,
        "schema_owner_valid": None,
        "application_schema_create": None,
        "current_object_grants": None,
    }


def run() -> tuple[dict[str, Any], int]:
    observation = Observation()
    result = _base(observation)
    try:
        settings = BootstrapDatabaseSettings()
        value = bootstrap_database(
            settings=settings,
            connection_factory=lambda **kwargs: _connect_factory(observation, **kwargs),
            migration_secret_path=Path("/run/secrets/mayak_database_migration_password"),
            application_secret_path=Path("/run/secrets/mayak_database_application_password"),
        )
        if not isinstance(value, BootstrapResult):
            return result, 83
        result.update(
            bootstrap_outcome="RF09_BOOTSTRAP_SUCCESS",
            migration_role_valid=value.migration_role_valid,
            application_role_valid=value.application_role_valid,
            schema_owner_valid=value.schema_owner_valid,
            application_schema_create=value.application_schema_create,
            current_object_grants=value.current_object_grants,
        )
        return result, 0
    except BootstrapInvariantError as exc:
        code = INVARIANT_CODES.get(str(exc))
        result["invariant_code"] = code or "RF09_UNRECOGNIZED_INVARIANT"
        result["bootstrap_outcome"] = (
            "RF09_BOOTSTRAP_RECOGNIZED_INVARIANT" if code
            else "RF09_BOOTSTRAP_UNRECOGNIZED_FAILURE"
        )
        return result, 81 if code else 83
    except BaseException as exc:
        result["bootstrap_outcome"] = "RF09_BOOTSTRAP_DATABASE_FAILURE"
        result["invariant_code"] = "RF09_DATABASE_BOOTSTRAP_FAILED"
        result["cause_type"] = type(exc).__name__
        result["client_sqlstate"] = _sqlstate(exc) or result["client_sqlstate"]
        return result, 82
    finally:
        result.update({
            "connection_attempted": observation.connection_attempted,
            "connected": observation.connected,
            "last_rf09_operation": observation.last_rf09_operation,
            "client_sqlstate": observation.client_sqlstate,
            "cause_type": observation.cause_type,
            "committed": observation.committed,
            "rolled_back": observation.rolled_back,
            "cursor_closed": observation.cursor_closed,
            "connection_closed": observation.connection_closed,
        })


def main() -> int:
    try:
        result, code = run()
        encoded = json.dumps(result, sort_keys=True, separators=(",", ":"))
        if "\n" in encoded or "\r" in encoded:
            return 85
        sys.stdout.write(encoded + "\n")
        return code
    except BaseException:
        return 85


if __name__ == "__main__":
    raise SystemExit(main())
