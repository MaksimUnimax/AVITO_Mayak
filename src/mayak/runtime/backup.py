"""Deployable one-shot PostgreSQL logical backup boundary.

The command deliberately keeps credentials in the process environment supplied
by the secret-file boundary and never constructs a password-bearing argv/DSN.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

from mayak.persistence.config import resolve_secret_file
from mayak.runtime.settings import ProcessKind, load_runtime_settings
from scripts.runtime.rf26_operability import canonical_root, write_verified_set


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
                "migration_revision": "runtime-observed",
                "tool_identity": f"{dump_version}; {tool_version}; {identity}",
            },
            readable=lambda _: readable,
            inventory=lambda _: inventory,
        )


def main() -> None:
    create_backup()


if __name__ == "__main__":
    main()
