"""Provision and clean the isolated PostgreSQL state used only by RF26 H19."""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

import psycopg
from psycopg import sql
from sqlalchemy.engine import URL

DB_RE = re.compile(r"rf26_h19_(?:rf10|rf11)_[0-9]+")
URL_RE = re.compile(r"postgres(?:ql)?(?:\+[^:/\s]+)?://[^\s]+", re.I)


def _run_id(value: str) -> str:
    if not re.fullmatch(r"[0-9]+", value):
        raise ValueError("unsafe RF26 H19 run identity")
    return value


def _ident(value: str, pattern: re.Pattern[str]) -> None:
    if pattern.fullmatch(value) is None:
        raise ValueError("unsafe RF26 H19 PostgreSQL identity")


def _connect(database: str, *, user: str, password: str) -> psycopg.Connection:
    return psycopg.connect(
        host=os.environ.get("RF26_POSTGRES_HOST", "mayak-postgres"),
        port=int(os.environ.get("RF26_POSTGRES_PORT", "5432")),
        dbname=database,
        user=user,
        password=password,
        autocommit=True,
        connect_timeout=10,
    )


def _bootstrap_password() -> str:
    return os.environ["RF26_H19_BOOTSTRAP_PASSWORD"]


def _names(run_id: str) -> tuple[str, str]:
    value = _run_id(run_id)
    return (f"rf26_h19_rf10_{value}", f"rf26_h19_rf11_{value}")


def _migrate(database: str, user: str, password: str, repo_root: Path) -> None:
    dsn = URL.create(
        "postgresql+psycopg",
        username=user,
        password=password,
        host=os.environ.get("RF26_POSTGRES_HOST", "mayak-postgres"),
        port=int(os.environ.get("RF26_POSTGRES_PORT", "5432")),
        database=database,
    )
    env = dict(os.environ)
    # SQLAlchemy's normal string form masks the password; Alembic needs the
    # credential only in this child process, never in workflow output.
    env["RF15_MIGRATION_DSN"] = dsn.render_as_string(hide_password=False)
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=repo_root,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    if result.returncode:
        lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        relevant = [
            line for line in lines
            if re.search(
                r"(?i)(operationalerror|programmingerror|psycopg|connection|"
                r"fatal|authentication|syntax|does not exist)",
                line,
            )
        ]
        detail = " | ".join(relevant[-10:] or lines[-10:] or ["no diagnostic"])
        detail = URL_RE.sub("postgresql://[REDACTED]", detail)
        detail = re.sub(r"(?i)(password|token|secret)\s*[=:]\s*[^\s,;]+", r"\1=[REDACTED]", detail)
        raise RuntimeError(f"RF26 H19 migration failed: {detail[:800]}")


def provision(*, run_id: str, repo_root: Path, state_dir: Path) -> None:
    databases = _names(run_id)
    state_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    state_dir.chmod(0o700)
    migration_role = "mayak_migration"
    migration_password = os.environ["RF26_H19_MIGRATION_PASSWORD"]
    with _connect("postgres", user="mayak", password=_bootstrap_password()) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM pg_roles WHERE rolname=%s", (migration_role,))
            if cursor.fetchone() is None:
                raise RuntimeError("task-owned migration role is absent")
            for database in databases:
                cursor.execute(
                    sql.SQL("CREATE DATABASE {} OWNER {}").format(
                        sql.Identifier(database), sql.Identifier(migration_role)
                    )
                )
    for database in databases:
        with _connect(database, user=migration_role, password=migration_password) as connection:
            with connection.cursor() as cursor:
                cursor.execute("CREATE SCHEMA mayak AUTHORIZATION CURRENT_USER")
        _migrate(database, migration_role, migration_password, repo_root)
    rf11_password = state_dir / "rf11-password"
    rf11_password.write_text(migration_password + "\n", encoding="utf-8")
    rf11_password.chmod(0o600)
    env_file = state_dir / "h19.env"
    rf10_dsn = URL.create(
        "postgresql+psycopg",
        username=migration_role,
        password=migration_password,
        host=os.environ.get("RF26_POSTGRES_HOST", "mayak-postgres"),
        port=int(os.environ.get("RF26_POSTGRES_PORT", "5432")),
        database=databases[0],
    )
    env_file.write_text(
        "\n".join(
            (
                f"MAYAK_RF10_POSTGRES_DSN={rf10_dsn.render_as_string(hide_password=False)}",
                f"MAYAK_RF11_POSTGRES_PASSWORD_FILE={rf11_password}",
                f"MAYAK_RF11_POSTGRES_USER={migration_role}",
                "MAYAK_RF11_POSTGRES_HOST="
                + os.environ.get("RF26_POSTGRES_HOST", "mayak-postgres"),
                f"MAYAK_RF11_POSTGRES_PORT={os.environ.get('RF26_POSTGRES_PORT', '5432')}",
                f"MAYAK_RF11_POSTGRES_DB={databases[1]}",
                "RF26_H19_RF10_DB=" + databases[0],
                "RF26_H19_RF11_DB=" + databases[1],
            )
        )
        + "\n",
        encoding="utf-8",
    )
    env_file.chmod(0o600)


def cleanup(*, run_id: str, state_dir: Path) -> None:
    databases = _names(run_id)
    with _connect("postgres", user="mayak", password=_bootstrap_password()) as connection:
        with connection.cursor() as cursor:
            for database in databases:
                _ident(database, DB_RE)
                cursor.execute(
                    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                    "WHERE datname=%s AND pid <> pg_backend_pid()",
                    (database,),
                )
                cursor.execute(
                    sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(database))
                )
    for path in (state_dir / "h19.env", state_dir / "rf11-password"):
        path.unlink(missing_ok=True)
    state_dir.rmdir()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("provision", "cleanup"))
    parser.add_argument("--run-id", default=os.environ.get("GITHUB_RUN_ID", ""))
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--state-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.action == "provision":
        provision(run_id=args.run_id, repo_root=args.repo_root, state_dir=args.state_dir)
    else:
        cleanup(run_id=args.run_id, state_dir=args.state_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
