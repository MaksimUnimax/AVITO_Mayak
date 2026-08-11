# ruff: noqa: E501
"""Real PG18 proof for the RF24 host archive stdin boundary.

The test is opt-in because the repository's ordinary focused suite must not
silently create Docker resources.  The opt-in gate uses the exact runner
helpers and production-shaped Docker tool prefix.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import time
import uuid
from pathlib import Path

import pytest

from scripts.runtime.run_rf24_backup_restore import (
    database_tool_role_args,
    run_binary_to_file,
    run_with_archive,
    tool,
)


@pytest.mark.skipif(os.environ.get("RF24_RUN_REAL_DOCKER_GATE") != "1", reason="opt-in real Docker gate")
def test_real_pg18_archive_transport_and_restore(monkeypatch: pytest.MonkeyPatch) -> None:
    if shutil.which("docker") is None:
        pytest.fail("Docker CLI is required for the real RF24 transport gate")
    name = f"rf24-transport-{uuid.uuid4().hex[:12]}"
    archive = Path(f"/tmp/{name}.dump")
    passfile = f"/tmp/{name}.pgpass"
    source = f"rf24_source_{name[-8:]}"
    target = f"rf24_target_{name[-8:]}"
    monkeypatch.setenv("RF24_PG_DATABASE_ROLE", "mayak_migration")
    monkeypatch.setenv("RF24_PG_TOOL_PREFIX", f"docker exec -i -u postgres -e PGPASSFILE={passfile} {name}")
    monkeypatch.setenv("RF24_PG_TOOL_SOURCE_DSN", source)
    monkeypatch.setenv("RF24_PG_TOOL_TARGET_DSN", target)
    env = os.environ.copy()

    def docker(*args: str, input_bytes: bytes | None = None, check: bool = True) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run(
            ["docker", *args], input=input_bytes, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            check=check, shell=False,
        )

    def psql(database: str, statement: str, *, user: str = "postgres") -> str:
        result = docker("exec", "-u", "postgres", name, "psql", "-X", "-v", "ON_ERROR_STOP=1", "-At", "-U", user, "-d", database, "-c", statement)
        return result.stdout.decode()

    try:
        docker(
            "run", "--detach", "--name", name, "--label", "rf24-technical-id=RF24-BACKUP-RESTORE-SCENARIO-01",
            "--label", "rf24-resource=transport-test", "--tmpfs", "/var/lib/postgresql:rw,size=512m",
            "-e", "POSTGRES_PASSWORD=bootstrap-only", "postgres:18-bookworm",
        )
        for _ in range(60):
            ready = docker("exec", name, "pg_isready", "-U", "postgres", "-d", "postgres", check=False)
            if ready.returncode == 0:
                break
            time.sleep(1)
        else:
            pytest.fail("task-owned PostgreSQL 18 container did not become ready")
        assert psql("postgres", "SELECT version()").startswith("PostgreSQL 18.")

        docker("exec", "-i", "-u", "postgres", name, "sh", "-c", f"umask 077; cat > {passfile}", input_bytes=b"*:*:*:mayak_migration:migration-only\n")
        psql("postgres", "CREATE ROLE mayak_migration LOGIN PASSWORD 'migration-only' CREATEDB")
        psql("postgres", f"CREATE DATABASE {source} OWNER mayak_migration")
        psql("postgres", f"CREATE DATABASE {target} OWNER mayak_migration")
        psql(source, "CREATE SCHEMA rf24_transport AUTHORIZATION mayak_migration; CREATE TABLE rf24_transport.synthetic (id integer PRIMARY KEY, value text); INSERT INTO rf24_transport.synthetic VALUES (7, 'stdin-crossed')", user="mayak_migration")
        archive.write_bytes(b"")
        run_binary_to_file(tool("pg_dump", "--format=custom", "--no-owner", "--no-acl", *database_tool_role_args(), source), archive, env=env)
        assert archive.is_file() and archive.stat().st_size > 0
        assert b"migration-only" not in archive.read_bytes()

        listing = run_with_archive(tool("pg_restore", "--list"), archive, env=env)
        assert "rf24_transport" in listing and "synthetic" in listing
        run_with_archive(tool("pg_restore", "--no-owner", "--no-acl", *database_tool_role_args(), "--dbname", target), archive, env=env)
        assert psql(target, "SELECT value FROM rf24_transport.synthetic ORDER BY id", user="mayak_migration").strip() == "stdin-crossed"
        assert psql(target, "SELECT pg_get_userbyid(c.relowner) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='rf24_transport' AND c.relname='synthetic'", user="mayak_migration").strip() == "mayak_migration"
        assert psql(source, "SELECT value FROM rf24_transport.synthetic ORDER BY id", user="mayak_migration").strip() == "stdin-crossed"
    finally:
        docker("rm", "--force", name, check=False)
        archive.unlink(missing_ok=True)
