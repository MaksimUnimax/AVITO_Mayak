"""Task-owned RF10/RF11 PostgreSQL foundation for broad CI regression."""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory
import psycopg
from psycopg import sql

NAME = re.compile(r"^ci_full_(?:rf10|rf11)_[0-9]+$")


def _cfg() -> tuple[str, int, str, str]:
    return (os.environ.get("CI_PG_HOST", "postgres"), int(os.environ.get("CI_PG_PORT", "5432")), os.environ.get("POSTGRES_USER", "postgres"), os.environ.get("POSTGRES_PASSWORD", "synthetic"))


def _admin(database: str = "postgres") -> psycopg.Connection:
    host, port, user, password = _cfg()
    return psycopg.connect(host=host, port=port, dbname=database, user=user, password=password, autocommit=True)


def _names(run_id: str) -> tuple[str, str]:
    if not run_id.isdigit():
        raise ValueError("invalid CI run identity")
    return (f"ci_full_rf10_{run_id}", f"ci_full_rf11_{run_id}")


def provision(run_id: str, state: Path, root: Path) -> None:
    rf10, rf11 = _names(run_id)
    migration_password = "ci-migration-synthetic"
    application_password = "ci-application-synthetic"
    state.mkdir(mode=0o700, parents=True, exist_ok=True)
    password_file = state / "rf11-password"
    password_file.write_text(migration_password + "\n", encoding="utf-8")
    password_file.chmod(0o600)
    host, port, admin, password = _cfg()
    with _admin() as conn, conn.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_roles WHERE rolname='mayak_migration'")
        if cur.fetchone() is None:
            cur.execute(sql.SQL("CREATE ROLE mayak_migration LOGIN PASSWORD {}").format(sql.Literal(migration_password)))
        else:
            cur.execute(sql.SQL("ALTER ROLE mayak_migration LOGIN PASSWORD {}").format(sql.Literal(migration_password)))
        cur.execute("SELECT 1 FROM pg_roles WHERE rolname='mayak_application'")
        if cur.fetchone() is None:
            cur.execute(sql.SQL("CREATE ROLE mayak_application LOGIN PASSWORD {}").format(sql.Literal(application_password)))
        else:
            cur.execute(sql.SQL("ALTER ROLE mayak_application LOGIN PASSWORD {}").format(sql.Literal(application_password)))
        for db in (rf10, rf11):
            if not NAME.fullmatch(db):
                raise ValueError("unsafe task-owned database")
            cur.execute("SELECT 1 FROM pg_database WHERE datname=%s", (db,))
            if cur.fetchone() is None:
                cur.execute(sql.SQL("CREATE DATABASE {} OWNER mayak_migration").format(sql.Identifier(db)))
    heads = tuple(sorted(ScriptDirectory.from_config(Config(str(root / "alembic.ini"))).get_heads()))
    if len(heads) != 1:
        raise RuntimeError(f"repository migration graph must have exactly one head, observed {heads!r}")
    expected = heads[0]
    dsn10 = f"postgresql+psycopg://mayak_application:{application_password}@{host}:{port}/{rf10}"
    receipt: list[dict[str, str]] = []
    for db in (rf10, rf11):
        with psycopg.connect(host=host, port=port, dbname=db, user="mayak_migration", password=migration_password, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute("CREATE SCHEMA IF NOT EXISTS mayak AUTHORIZATION mayak_migration")
        env = dict(os.environ)
        env["RF15_MIGRATION_DSN"] = f"postgresql+psycopg://mayak_migration:{migration_password}@{host}:{port}/{db}"
        result = subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=root, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
        if result.returncode:
            raise RuntimeError(f"migration failed for task-owned database {db}")
        with psycopg.connect(host=host, port=port, dbname=db, user="mayak_migration", password=migration_password) as verify:
            with verify.cursor() as verify_cur:
                verify_cur.execute("SELECT version_num FROM mayak.alembic_version")
                observed = tuple(row[0] for row in verify_cur.fetchall())
        status = "PASS" if observed == (expected,) else "FAIL"
        receipt.append({"logical_db_role": "rf10" if db == rf10 else "rf11", "db_id": db, "expected_revision": expected, "observed_revision": observed[0] if len(observed) == 1 else "MULTIPLE_OR_MISSING", "status": status})
        if status != "PASS":
            raise RuntimeError(f"migration head mismatch for task-owned database {db}")
    (state / "migration-receipt.json").write_text(json.dumps({"schema_version": 1, "run_id": run_id, "databases": receipt}, sort_keys=True) + "\n", encoding="utf-8")
    (state / "migration-receipt.json").chmod(0o600)
    marker = state / "full-regression.env"
    marker.write_text("\n".join((f"MAYAK_RF10_POSTGRES_DSN={dsn10}", f"MAYAK_RF11_POSTGRES_PASSWORD_FILE={password_file}", "MAYAK_RF11_POSTGRES_USER=mayak_migration", f"MAYAK_RF11_POSTGRES_HOST={host}", f"MAYAK_RF11_POSTGRES_PORT={port}", f"MAYAK_RF11_POSTGRES_DB={rf11}", "MAYAK_PROVIDER_MODE=disabled", "MAYAK_RUNTIME_PROFILE=synthetic_acceptance")) + "\n", encoding="utf-8")
    marker.chmod(0o600)


def cleanup(run_id: str, state: Path) -> None:
    names = _names(run_id)
    with _admin() as conn, conn.cursor() as cur:
        for db in names:
            cur.execute("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname=%s AND pid <> pg_backend_pid()", (db,))
            cur.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(db)))
    for name in ("full-regression.env", "rf11-password", "migration-receipt.json"):
        (state / name).unlink(missing_ok=True)
    state.rmdir()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("provision", "cleanup"))
    parser.add_argument("--run-id", default=os.environ.get("GITHUB_RUN_ID", "0"))
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    (provision if args.action == "provision" else cleanup)(args.run_id, args.state, args.root) if args.action == "provision" else cleanup(args.run_id, args.state)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
