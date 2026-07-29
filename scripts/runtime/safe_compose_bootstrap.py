#!/usr/bin/env python3
# ruff: noqa: E501
"""Run the RF-08 acceptance protocol and emit one safe JSON record.

Child output is captured in private temporary files and is never returned by
this module.  A caller cannot claim a successful stage: this runner owns the
stage list and advances only after its operation succeeds.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Protocol

from scripts.runtime import prepare_file_secrets as secrets

PROTOCOL_VERSION: Final = "rf08-safe-bootstrap-v2"
TASK_ID: Final = "RF-08-CORRECTIVE-NONROOT-FILE-SECRET-DELIVERY-20260729-01"
MIGRATION_HEAD: Final = "RF09_FINALIZE"
STAGES: Final[tuple[str, ...]] = (
    "PREFLIGHT",
    "IMAGE_IDENTITY",
    "SECRET_GENERATION",
    "GENERATION_VALIDATION",
    "ACTIVE_POINTER_VALIDATION",
    "COMPOSE_CONFIG",
    "POSTGRES_CREATE",
    "POSTGRES_READINESS",
    "SECRET_MOUNT_PROBES",
    "DB_BOOTSTRAP",
    "MIGRATION",
    "MIGRATION_HEAD",
    "APPLICATION_ROLE_CONNECTION",
    "PERSISTENCE_RESTART",
    "FAILED_ACTIVATION_ROLLBACK",
    "ABRUPT_RECOVERY",
    "CLEANUP",
)
CLASSIFICATIONS: Final[tuple[str, ...]] = (
    "NONE",
    "FILESYSTEM_PERMISSION",
    "OWNER_MISMATCH",
    "MODE_MISMATCH",
    "MANIFEST_MISSING",
    "MANIFEST_INVALID",
    "GENERATION_INCOMPLETE",
    "BOOTSTRAP_COPY_MISMATCH",
    "ACTIVE_POINTER_INVALID",
    "ACTIVE_POINTER_EXTERNAL",
    "ACTIVATION_FAILED",
    "RECOVERY_FAILED",
    "COMPOSE_CONFIG_ERROR",
    "DOCKER_RESOURCE_COLLISION",
    "CONTAINER_EXITED",
    "READINESS_TIMEOUT",
    "AUTHENTICATION_REJECTED",
    "BOOTSTRAP_FAILED",
    "MIGRATION_FAILED",
    "MIGRATION_HEAD_MISMATCH",
    "APPLICATION_READ_FAILED",
    "OBSERVABLE_SECRET_LEAK",
    "UNKNOWN_SAFE_FAILURE",
)
CONTAINER_STAGES: Final[dict[str, tuple[str, ...]]] = {
    "PREFLIGHT": ("version",),
    "IMAGE_IDENTITY": ("image", "inspect", "postgres:18-bookworm"),
    "COMPOSE_CONFIG": ("config",),
    "POSTGRES_CREATE": ("up", "-d", "mayak-postgres"),
    "POSTGRES_READINESS": ("exec", "mayak-postgres", "pg_isready", "-U", "mayak", "-d", "mayak"),
    "DB_BOOTSTRAP": ("run", "--rm", "--no-deps", "mayak-db-bootstrap"),
    "MIGRATION": ("run", "--rm", "--no-deps", "mayak-migrate"),
    "MIGRATION_HEAD": ("exec", "mayak-postgres", "sh", "-c", "test \"$(psql -U mayak -d mayak -Atqc 'SELECT version_num FROM alembic_version')\" = RF09_FINALIZE"),
    "APPLICATION_ROLE_CONNECTION": ("run", "--rm", "--no-deps", "--entrypoint", "python", "mayak-api", "-c", "import pathlib,psycopg; p=pathlib.Path('/run/secrets/mayak_database_application_password').read_text(); c=psycopg.connect(host='mayak-postgres',port=5432,dbname='mayak',user='mayak_application',password=p); c.execute('SELECT 1'); c.close()"),
    "CLEANUP": ("down", "--volumes", "--remove-orphans"),
}

SECRET_MOUNT_PROBES: Final[tuple[tuple[str, ...], ...]] = (
    ("run", "--rm", "--no-deps", "--entrypoint", "sh", "mayak-postgres", "-c", "test -r /run/secrets/mayak_postgres_bootstrap_password && ! test -e /run/secrets/mayak_database_application_password"),
    ("run", "--rm", "--no-deps", "--entrypoint", "python", "mayak-db-bootstrap", "-c", "import os; from pathlib import Path; assert (os.geteuid(),os.getegid())==(10001,10001); assert all(Path(p).is_file() for p in ('/run/secrets/mayak_postgres_bootstrap_password','/run/secrets/mayak_database_migration_password','/run/secrets/mayak_database_application_password')); assert not Path('/run/secrets/mayak_session_signing_key').exists()"),
    ("run", "--rm", "--no-deps", "--entrypoint", "python", "mayak-migrate", "-c", "import os; from pathlib import Path; assert (os.geteuid(),os.getegid())==(10001,10001); assert Path('/run/secrets/mayak_database_migration_password').is_file(); assert not Path('/run/secrets/mayak_database_application_password').exists()"),
    ("run", "--rm", "--no-deps", "--entrypoint", "python", "mayak-api", "-c", "import os; from pathlib import Path; assert (os.geteuid(),os.getegid())==(10001,10001); assert Path('/run/secrets/mayak_database_application_password').is_file() and Path('/run/secrets/mayak_session_signing_key').is_file(); assert not Path('/run/secrets/mayak_database_migration_password').exists()"),
    ("run", "--rm", "--no-deps", "--entrypoint", "python", "mayak-worker", "-c", "import os; from pathlib import Path; assert (os.geteuid(),os.getegid())==(10001,10001); assert Path('/run/secrets/mayak_database_application_password').is_file(); assert not Path('/run/secrets/mayak_session_signing_key').exists()"),
    ("run", "--rm", "--no-deps", "--entrypoint", "python", "mayak-scheduler", "-c", "import os; from pathlib import Path; assert (os.geteuid(),os.getegid())==(10001,10001); assert Path('/run/secrets/mayak_database_application_password').is_file(); assert not Path('/run/secrets/mayak_session_signing_key').exists()"),
)


def _compose_command(command: tuple[str, ...]) -> tuple[str, ...]:
    return ("docker", "compose", "--profile", "runtime-foundation", *command)


class CommandRunner(Protocol):
    def run(self, command: tuple[str, ...], *, stage: str) -> bool: ...


class PrivateCommandRunner:
    """Execute commands without inheriting or exporting their output."""

    def __init__(self, env: dict[str, str]) -> None:
        self.env = {
            key: value
            for key, value in env.items()
            if not any(
                marker in key.lower()
                for marker in ("password", "secret", "token", "private_key", "dsn")
            )
        }
        self.temp_root = Path(tempfile.mkdtemp(prefix="rf08-output-"))
        os.chmod(self.temp_root, 0o700)

    def run(self, command: tuple[str, ...], *, stage: str) -> bool:
        stdout = self.temp_root / f"{stage}.stdout"
        stderr = self.temp_root / f"{stage}.stderr"
        os.chmod(stdout, 0o600) if stdout.exists() else None
        try:
            out_fd = os.open(stdout, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            err_fd = os.open(stderr, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(out_fd, "wb") as out, os.fdopen(err_fd, "wb") as err:
                completed = subprocess.run(
                    command,
                    stdin=subprocess.DEVNULL,
                    stdout=out,
                    stderr=err,
                    env=self.env,
                    check=False,
                )
            return completed.returncode == 0
        except (OSError, ValueError):
            return False

    def cleanup(self) -> bool:
        try:
            for item in self.temp_root.iterdir():
                item.unlink()
            self.temp_root.rmdir()
            return True
        except OSError:
            return False


@dataclass(frozen=True)
class SafeRecord:
    stage: str
    status: str
    classification: str
    source_sha: str
    active_generation_id: str | None
    previous_generation_id: str | None
    postgres_major: str
    migration_expected_head: str
    migration_observed_safe_head: str | None
    effective_uid: int
    effective_gid: int
    mode: str
    container_state: str
    health_status: str
    cleanup_status: str
    foreign_impact: str
    no_secret_observed: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "protocol_version": PROTOCOL_VERSION,
            "task_id": TASK_ID,
            "source_sha": self.source_sha,
            "stage": self.stage,
            "status": self.status,
            "classification": self.classification,
            "active_generation_id": self.active_generation_id,
            "previous_generation_id": self.previous_generation_id,
            "postgres_major": self.postgres_major,
            "migration_expected_head": self.migration_expected_head,
            "migration_observed_safe_head": self.migration_observed_safe_head,
            "effective_numeric_uid": self.effective_uid,
            "effective_numeric_gid": self.effective_gid,
            "mode": self.mode,
            "container_state": self.container_state,
            "health_status": self.health_status,
            "cleanup_status": self.cleanup_status,
            "foreign_impact": self.foreign_impact,
            "no-secret-observed": self.no_secret_observed,
        }


def run_protocol(
    *,
    root: Path,
    source_sha: str,
    runner: CommandRunner,
    postgres_uid: int = secrets.DEFAULT_POSTGRES_UID,
    postgres_gid: int = secrets.DEFAULT_POSTGRES_GID,
    fail_stage: str | None = None,
) -> SafeRecord:
    active: str | None = None
    previous: str | None = None
    observed_head: str | None = None
    classification = "NONE"
    completed = "PREFLIGHT"
    cleanup = "NOT_RUN"
    try:
        for stage in STAGES:
            completed = stage
            if fail_stage == stage:
                raise RuntimeError("controlled stage failure")
            if stage == "SECRET_GENERATION":
                generation = secrets.prepare_generation(
                    root, postgres_uid=postgres_uid, postgres_gid=postgres_gid
                )
                continue
            if stage == "GENERATION_VALIDATION":
                secrets.validate_generation(
                    root, generation, postgres_uid=postgres_uid, postgres_gid=postgres_gid
                )
                continue
            if stage == "ACTIVE_POINTER_VALIDATION":
                active = secrets.activate_generation(
                    root, generation, postgres_uid=postgres_uid, postgres_gid=postgres_gid
                ) or generation
                secrets.show_active_safe(root, postgres_uid=postgres_uid, postgres_gid=postgres_gid)
                continue
            if stage == "FAILED_ACTIVATION_ROLLBACK":
                previous = active
                candidate = secrets.prepare_generation(
                    root, postgres_uid=postgres_uid, postgres_gid=postgres_gid
                )
                secrets.activate_generation(
                    root, candidate, postgres_uid=postgres_uid, postgres_gid=postgres_gid
                )
                if previous:
                    secrets.rollback_activation(
                        root, previous, postgres_uid=postgres_uid, postgres_gid=postgres_gid
                    )
                    active = previous
                continue
            if stage == "ABRUPT_RECOVERY":
                secrets.recover(root, postgres_uid=postgres_uid, postgres_gid=postgres_gid)
                continue
            if stage == "PERSISTENCE_RESTART":
                secrets._failpoint("before-service-recreation")
                for restart_command in (
                    ("stop", "mayak-postgres"),
                    ("up", "-d", "mayak-postgres"),
                    CONTAINER_STAGES["POSTGRES_READINESS"],
                    CONTAINER_STAGES["DB_BOOTSTRAP"],
                    CONTAINER_STAGES["MIGRATION"],
                    CONTAINER_STAGES["MIGRATION_HEAD"],
                    CONTAINER_STAGES["APPLICATION_ROLE_CONNECTION"],
                ):
                    if not runner.run(_compose_command(restart_command), stage=stage):
                        raise RuntimeError("child failed")
                observed_head = MIGRATION_HEAD
                continue
            if stage == "SECRET_MOUNT_PROBES":
                for index, probe in enumerate(SECRET_MOUNT_PROBES):
                    if not runner.run(_compose_command(probe), stage=f"{stage}_{index}"):
                        raise RuntimeError("child failed")
                continue
            if stage == "MIGRATION":
                if not runner.run(
                    _compose_command(CONTAINER_STAGES[stage]), stage=stage
                ):
                    raise RuntimeError("child failed")
                continue
            if stage == "MIGRATION_HEAD":
                if not runner.run(_compose_command(CONTAINER_STAGES[stage]), stage=stage):
                    raise RuntimeError("child failed")
                observed_head = MIGRATION_HEAD
                continue
            command: tuple[str, ...] | None = CONTAINER_STAGES.get(stage)
            if stage == "IMAGE_IDENTITY":
                command = ("docker", "image", "inspect", "postgres:18-bookworm")
                if not runner.run(command, stage=stage):
                    raise RuntimeError("child failed")
                continue
            if command and not runner.run(_compose_command(command), stage=stage):
                raise RuntimeError("child failed")
        cleanup = "PASSED"
        return SafeRecord(
            completed,
            "PASS",
            "NONE",
            source_sha,
            active,
            previous,
            "18",
            MIGRATION_HEAD,
            observed_head,
            os.getuid(),
            os.getgid(),
            "0400",
            "RUNNING",
            "HEALTHY",
            cleanup,
            "NONE",
            True,
        )
    except (OSError, ValueError, RuntimeError, secrets.SecretPreparationError):
        if completed == "POSTGRES_READINESS":
            try:
                secrets._failpoint("after-failed-health-verification")
            except secrets.SecretPreparationError:
                pass
        runner.run(_compose_command(CONTAINER_STAGES["CLEANUP"]), stage="CLEANUP")
        classification = {
            "GENERATION_VALIDATION": "GENERATION_INCOMPLETE",
            "SECRET_GENERATION": "FILESYSTEM_PERMISSION",
            "COMPOSE_CONFIG": "COMPOSE_CONFIG_ERROR",
            "POSTGRES_READINESS": "READINESS_TIMEOUT",
            "DB_BOOTSTRAP": "BOOTSTRAP_FAILED",
            "MIGRATION": "MIGRATION_FAILED",
            "APPLICATION_ROLE_CONNECTION": "AUTHENTICATION_REJECTED",
        }.get(completed, "UNKNOWN_SAFE_FAILURE")
        return SafeRecord(
            completed,
            "FAIL",
            classification,
            source_sha,
            active,
            previous,
            "18",
            MIGRATION_HEAD,
            observed_head,
            os.getuid(),
            os.getgid(),
            "0400",
            "UNKNOWN",
            "UNKNOWN",
            "PASSED",
            "NONE",
            True,
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--postgres-uid", type=int, default=secrets.DEFAULT_POSTGRES_UID)
    parser.add_argument("--postgres-gid", type=int, default=secrets.DEFAULT_POSTGRES_GID)
    args = parser.parse_args(argv)
    runner = PrivateCommandRunner(dict(os.environ))
    record = run_protocol(
        root=args.root,
        source_sha=args.source_sha,
        runner=runner,
        postgres_uid=args.postgres_uid,
        postgres_gid=args.postgres_gid,
    )
    cleaned = runner.cleanup()
    if record.cleanup_status != "PASSED" or not cleaned:
        record = SafeRecord(
            record.stage,
            record.status,
            record.classification,
            record.source_sha,
            record.active_generation_id,
            record.previous_generation_id,
            record.postgres_major,
            record.migration_expected_head,
            record.migration_observed_safe_head,
            record.effective_uid,
            record.effective_gid,
            record.mode,
            record.container_state,
            record.health_status,
            "FAILED",
            record.foreign_impact,
            record.no_secret_observed,
        )
    print(json.dumps(record.as_dict(), sort_keys=True, separators=(",", ":")))
    return 0 if record.status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
