# ruff: noqa: E501
"""Deployable one-shot PostgreSQL logical backup boundary.

The command deliberately keeps credentials in the process environment supplied
by the secret-file boundary and never constructs a password-bearing argv/DSN.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

import psycopg
from alembic.config import Config
from alembic.script import ScriptDirectory

from mayak.persistence.config import resolve_secret_file
from mayak.runtime.settings import ProcessKind, load_runtime_settings
from scripts.runtime.rf26_operability import canonical_root, write_verified_set


def authoritative_migration_revision(settings: object, password: str) -> str:
    """Read the sole database revision and require the repository head."""
    database = settings.database  # type: ignore[attr-defined]
    with psycopg.connect(
        host=database.host,
        port=database.port,
        dbname=database.name,
        user=database.migration_user,
        password=password,
        connect_timeout=database.connect_timeout_seconds,
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT version_num::text FROM mayak.alembic_version ORDER BY version_num")
            revisions = [str(row[0]) for row in cursor.fetchall()]
    heads = tuple(ScriptDirectory.from_config(Config("alembic.ini")).get_heads())
    if len(revisions) != 1 or len(heads) != 1 or revisions[0] != heads[0]:
        raise RuntimeError("database migration revision is unavailable or does not equal current head")
    return revisions[0]


def verify_archive(archive: Path) -> tuple[bool, bool, str, str]:
    """Verify readability and inventory with PostgreSQL's pg_restore."""
    result = subprocess.run(
        ["pg_restore", "--list", str(archive)],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    listing = result.stdout.splitlines()
    version = subprocess.run(
        ["pg_restore", "--version"], check=True, stdout=subprocess.PIPE, text=True
    ).stdout.strip()
    readable = result.returncode == 0
    inventory = readable and any(line.strip() and not line.startswith(";") for line in listing)
    return readable, inventory, version, "pg_dump-compatible-custom"


def create_backup() -> Path:
    settings = load_runtime_settings()
    if settings.runtime.process_kind is not ProcessKind.BACKUP:
        raise RuntimeError("invalid process kind")
    root = canonical_root(settings.backup.backup_root)
    password = resolve_secret_file(
        settings.runtime.secrets_dir / "mayak_database_application_password"
    ).as_text()
    migration_password = resolve_secret_file(
        settings.runtime.secrets_dir / "mayak_database_migration_password"
    ).as_text()
    migration_revision = authoritative_migration_revision(settings, migration_password)
    env = {**os.environ, "PGPASSWORD": password}
    database = settings.database
    args = ["pg_dump", "--format=custom", "--no-owner", "--no-acl", "--file"]
    with tempfile.TemporaryDirectory(prefix=".rf26-backup-", dir=root) as temp:
        temporary = Path(temp) / "backup.dump"
        subprocess.run(
            args
            + [
                str(temporary),
                "--host",
                database.host,
                "--port",
                str(database.port),
                "--username",
                database.application_user,
                database.name,
            ],
            check=True,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        readable, inventory, tool_version, identity = verify_archive(temporary)
        if not tool_version.startswith("pg_restore (PostgreSQL) 18."):
            raise RuntimeError("PostgreSQL 18 pg_restore is required")
        dump_version = subprocess.run(
            ["pg_dump", "--version"], check=True, stdout=subprocess.PIPE, text=True
        ).stdout.strip()
        if not dump_version.startswith("pg_dump (PostgreSQL) 18."):
            raise RuntimeError("PostgreSQL 18 pg_dump is required")
        backup_id = f"{settings.build.source_sha}-{temporary.stat().st_mtime_ns}"
        return write_verified_set(
            root,
            backup_id,
            lambda destination: destination.write_bytes(temporary.read_bytes()),
            {
                "environment_id": settings.build.environment_id,
                "source_sha": settings.build.source_sha,
                "migration_revision": migration_revision,
                "tool_identity": f"{dump_version}; {tool_version}; {identity}",
            },
            readable=lambda _: readable,
            inventory=lambda _: inventory,
        )


def main() -> None:
    create_backup()


if __name__ == "__main__":
    main()
