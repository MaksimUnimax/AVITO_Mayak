# ruff: noqa: E501
"""Single, fail-closed RF26 PostgreSQL bootstrap and migration preflight.

This module is deliberately narrow: it owns only the task-database setup
performed before the RF26 backup/restore runner.  Every boundary reconnects
and proves its result so a hosted failure identifies the first failed
transition without exposing credentials.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

import psycopg
from psycopg import sql

BOUNDARIES = (
    "H8A_CONNECTIVITY", "H8B_BOOTSTRAP_AUTHORITY", "H8C_ROLE_STATE",
    "H8D_DATABASE_CREATE", "H8E_DATABASE_OWNERSHIP", "H8F_SCHEMA_PREPARE",
    "H8G_SOURCE_MIGRATION", "H8H_CONFLICT_MIGRATION", "H8I_REVISION_PROOF",
    "H8J_APPLICATION_GRANTS", "H8K_TARGET_EMPTY",
)
_SECRET = re.compile(r"(?i)(password|token|secret|authorization|dsn)[^\s=:/]*[\s:=]+[^\s]+")
_URL = re.compile(r"(?i)(postgres(?:ql)?://)[^\s]+")


def _redact(value: object) -> str:
    message = str(value).replace("\n", " ")[:400]
    message = _URL.sub(r"\1[REDACTED]", message)
    return _SECRET.sub(lambda match: match.group(1) + "=[REDACTED]", message)


def _ident(name: str) -> None:
    if re.fullmatch(r"rf26_(?:source|target|conflict)_[0-9]+", name) is None:
        raise ValueError("unsafe RF26 database identity")


class PreflightFailure(RuntimeError):
    def __init__(self, boundary: str, error: BaseException) -> None:
        self.boundary = boundary
        self.error_class = type(error).__name__
        self.reason = _redact(error)
        super().__init__(f"{boundary}: {self.error_class}: {self.reason}")


def _password(name: str, default: str) -> str:
    return os.environ.get(name, default)


def _connect(database: str, *, user: str, password: str) -> psycopg.Connection[Any]:
    return psycopg.connect(
        host=os.environ.get("RF26_POSTGRES_HOST", "mayak-postgres"),
        port=int(os.environ.get("RF26_POSTGRES_PORT", "5432")),
        dbname=database, user=user, password=password, autocommit=True,
        connect_timeout=10,
    )


def _names(run_id: str) -> tuple[str, str, str]:
    if re.fullmatch(r"[0-9]+", run_id) is None:
        raise ValueError("unsafe RF26 run identity")
    values = tuple(f"rf26_{kind}_{run_id}" for kind in ("source", "target", "conflict"))
    if len(set(values)) != 3:
        raise ValueError("non-unique RF26 database identities")
    return values  # type: ignore[return-value]


def _query(database: str, statement: str, *params: object, user: str = "mayak_migration", password: str = "rf26-migration-only") -> list[tuple[Any, ...]]:
    with _connect(database, user=user, password=password) as connection:
        with connection.cursor() as cursor:
            cursor.execute(statement, params)
            return list(cursor.fetchall())


def _bootstrap_authority() -> None:
    rows = _query("postgres", "SELECT rolsuper, rolcreatedb, rolcreaterole FROM pg_roles WHERE rolname=current_user", user="mayak", password=_password("RF26_BOOTSTRAP_PASSWORD", "rf26-bootstrap-only"))
    if rows != [(True, True, True)]:
        raise RuntimeError("bootstrap authority proof failed")


def _role_state() -> None:
    password = _password("RF26_BOOTSTRAP_PASSWORD", "rf26-bootstrap-only")
    with _connect("postgres", user="mayak", password=password) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM pg_roles WHERE rolname IN ('mayak_migration', 'mayak_application')")
            if cursor.fetchone() is not None:
                raise RuntimeError("unexpected pre-existing RF26 role")
            cursor.execute(sql.SQL("CREATE ROLE mayak_migration LOGIN PASSWORD {} CREATEDB").format(sql.Literal("rf26-migration-only")))
            cursor.execute(sql.SQL("CREATE ROLE mayak_application LOGIN PASSWORD {}").format(sql.Literal("rf26-application-only")))
            cursor.execute("SELECT rolcreatedb, rolsuper FROM pg_roles WHERE rolname='mayak_migration'")
            if cursor.fetchone() != (True, False):
                raise RuntimeError("migration role capability proof failed")
            cursor.execute("SELECT rolcreatedb, rolsuper, rolcreaterole FROM pg_roles WHERE rolname='mayak_application'")
            if cursor.fetchone() != (False, False, False):
                raise RuntimeError("application role capability proof failed")
            cursor.execute("SELECT 1 FROM pg_auth_members m JOIN pg_roles r ON r.oid=m.member JOIN pg_roles g ON g.oid=m.roleid WHERE r.rolname IN ('mayak_migration', 'mayak_application') OR g.rolname IN ('mayak_migration', 'mayak_application')")
            if cursor.fetchone() is not None:
                raise RuntimeError("RF26 role membership authority proof failed")


def _create_databases(names: tuple[str, ...]) -> None:
    password = _password("RF26_BOOTSTRAP_PASSWORD", "rf26-bootstrap-only")
    with _connect("postgres", user="mayak", password=password) as connection:
        with connection.cursor() as cursor:
            for name in names:
                _ident(name)
                cursor.execute("SELECT 1 FROM pg_database WHERE datname=%s", (name,))
                if cursor.fetchone() is not None:
                    raise RuntimeError("unexpected pre-existing RF26 database")
                cursor.execute(sql.SQL("CREATE DATABASE {} OWNER mayak_migration").format(sql.Identifier(name)))


def _owners(names: tuple[str, ...]) -> None:
    for name in names:
        rows = _query(name, "SELECT pg_get_userbyid(datdba) FROM pg_database WHERE datname=current_database()")
        if rows != [("mayak_migration",)]:
            raise RuntimeError(f"database owner proof failed for {name}")


def _schemas(source: str, target: str, conflict: str) -> None:
    for name in (source, conflict):
        with _connect(name, user="mayak_migration", password="rf26-migration-only") as connection:
            with connection.cursor() as cursor:
                cursor.execute("CREATE SCHEMA mayak AUTHORIZATION mayak_migration")
                cursor.execute("SELECT pg_get_userbyid(nspowner) FROM pg_namespace WHERE nspname='mayak'")
                if cursor.fetchone() != ("mayak_migration",):
                    raise RuntimeError(f"schema owner proof failed for {name}")
    if _query(target, "SELECT 1 FROM information_schema.schemata WHERE schema_name='mayak'"):
        raise RuntimeError("target must remain schema-empty before restore")


def _migrate(database: str, repo_root: Path) -> None:
    env = dict(os.environ)
    env["RF15_MIGRATION_DSN"] = f"postgresql+psycopg://mayak_migration:rf26-migration-only@{env.get('RF26_POSTGRES_HOST', 'mayak-postgres')}:{env.get('RF26_POSTGRES_PORT', '5432')}/{database}"
    result = subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=repo_root, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"alembic upgrade failed with exit code {result.returncode}")


def _revision_proof(source: str, target: str, conflict: str, repo_root: Path) -> None:
    from alembic.config import Config
    from alembic.script import ScriptDirectory
    expected = set(ScriptDirectory.from_config(Config(str(repo_root / "alembic.ini"))).get_heads())
    for name in (source, conflict):
        rows = set(row[0] for row in _query(name, "SELECT version_num::text FROM mayak.alembic_version"))
        if rows != expected:
            raise RuntimeError(f"exact migration head proof failed for {name}")
    if _query(target, "SELECT 1 FROM information_schema.tables WHERE table_schema='mayak' AND table_name='alembic_version'"):
        raise RuntimeError("target Alembic state unexpectedly present")


def _grants(source: str, conflict: str) -> None:
    for name in (source, conflict):
        with _connect(name, user="mayak_migration", password="rf26-migration-only") as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql.SQL("GRANT CONNECT ON DATABASE {} TO mayak_application").format(sql.Identifier(name)))
                cursor.execute("GRANT USAGE ON SCHEMA mayak TO mayak_application")
                cursor.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA mayak TO mayak_application")
                cursor.execute("GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA mayak TO mayak_application")
        rows = _query(name, "SELECT has_schema_privilege(current_user, 'mayak', 'USAGE'), has_database_privilege(current_user, current_database(), 'CONNECT')", user="mayak_application", password="rf26-application-only")
        if rows != [(True, True)]:
            raise RuntimeError(f"application privilege proof failed for {name}")


def _target_empty(target: str) -> None:
    if _query(target, "SELECT EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name='mayak'), EXISTS (SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='mayak')") != [(False, False)]:
        raise RuntimeError("target emptiness proof failed")


def run_preflight(*, run_id: str, repo_root: Path, output: Path) -> dict[str, Any]:
    source, target, conflict = _names(run_id)
    trace = {
        "input": {"run_id": run_id},
        "derived": {"source": source, "target": target, "conflict": conflict},
        "function": {"module": __name__, "entrypoint": "run_preflight"},
        "environment": {"postgres_host": os.environ.get("RF26_POSTGRES_HOST", "mayak-postgres"), "postgres_port": os.environ.get("RF26_POSTGRES_PORT", "5432")},
        "source_runtime_evidence": {"repo_root": str(repo_root), "python": sys.version.split()[0]},
    }
    operations: tuple[tuple[str, Callable[[], None]], ...] = (
        ("H8A_CONNECTIVITY", lambda: _query("postgres", "SELECT 1", user="mayak", password=_password("RF26_BOOTSTRAP_PASSWORD", "rf26-bootstrap-only"))),
        ("H8B_BOOTSTRAP_AUTHORITY", _bootstrap_authority),
        ("H8C_ROLE_STATE", _role_state),
        ("H8D_DATABASE_CREATE", lambda: _create_databases((source, target, conflict))),
        ("H8E_DATABASE_OWNERSHIP", lambda: _owners((source, target, conflict))),
        ("H8F_SCHEMA_PREPARE", lambda: _schemas(source, target, conflict)),
        ("H8G_SOURCE_MIGRATION", lambda: _migrate(source, repo_root)),
        ("H8H_CONFLICT_MIGRATION", lambda: _migrate(conflict, repo_root)),
        ("H8I_REVISION_PROOF", lambda: _revision_proof(source, target, conflict, repo_root)),
        ("H8J_APPLICATION_GRANTS", lambda: _grants(source, conflict)),
        ("H8K_TARGET_EMPTY", lambda: _target_empty(target)),
    )
    passed: list[str] = []
    try:
        for boundary, operation in operations:
            operation()
            passed.append(boundary)
            print(f"RF26 H8 {boundary}: PASS", flush=True)
    except BaseException as error:
        failure = error if isinstance(error, PreflightFailure) else PreflightFailure(operations[len(passed)][0], error)
        diagnostic = {"schema_version": 1, "technical_id": "RF26-OBSERVABILITY-BACKUP-RECOVERY-01", "run_id": run_id, "passed_boundaries": passed, "failed_boundary": failure.boundary, "exception_class": failure.error_class, "reason": failure.reason, "trace": trace}
        output.write_text(json.dumps(diagnostic, sort_keys=True) + "\n", encoding="utf-8")
        print(f"::error title=RF26 H8 {failure.boundary}::{failure.reason}", flush=True)
        summary = os.environ.get("GITHUB_STEP_SUMMARY")
        if summary:
            Path(summary).write_text(f"### RF26 H8 failure\n- Boundary: `{failure.boundary}`\n- Exception: `{failure.error_class}`\n- Reason: `{failure.reason}`\n", encoding="utf-8")
        raise SystemExit(1)
    diagnostic = {"schema_version": 1, "technical_id": "RF26-OBSERVABILITY-BACKUP-RECOVERY-01", "run_id": run_id, "passed_boundaries": passed, "failed_boundary": None, "trace": trace}
    output.write_text(json.dumps(diagnostic, sort_keys=True) + "\n", encoding="utf-8")
    return diagnostic


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", default=os.environ.get("GITHUB_RUN_ID", ""))
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, default=Path("rf26-H8-preflight.json"))
    args = parser.parse_args()
    run_preflight(run_id=args.run_id, repo_root=args.repo_root, output=args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
