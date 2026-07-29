#!/usr/bin/env python3
"""Authoritative, secret-safe RF-08 persistence acceptance protocol.

Only this module owns stage progression.  Commands return typed metadata; raw
child output is private, scanned, parsed and destroyed before a result leaves
the process.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final, Protocol

from scripts.runtime import prepare_file_secrets as secrets

PROTOCOL_VERSION: Final = "rf08-safe-bootstrap-v3"
TASK_ID: Final = "RF-08-CORRECTIVE-NONROOT-FILE-SECRET-DELIVERY-20260729-01"
TASK_PROJECT: Final = "avito-mayak-rf08-secret-delivery"
CANONICAL_PROJECT: Final = "avito-mayak-acceptance"
EXPECTED_IMAGE_TAG: Final = "avito-mayak:63dc73662c5d3c78106d4163e509136579ae9fec"
EXPECTED_IMAGE_SOURCE: Final = "https://github.com/MaksimUnimax/AVITO_Mayak"
EXPECTED_LOCK_IDENTITY: Final = "e1faff1ce0f4d5dfd35480ab59d5d599fddf05c38fcd16a26c52098511476ab6"
TASK_RUNTIME_ROOT: Final = Path("/opt/avito-mayak-runtime/rf08-secret-delivery")
PINNED_POSTGRES: Final = (
    "postgres:18-bookworm@sha256:1961f96e6029a02c3812d7cb329a3b03a3ac2bb067058dec17b0f5596aca9296"
)
MIGRATION_HEAD: Final = "RF09_FINALIZE"
APPLICATION_QUERY: Final = (
    "import pathlib,psycopg; "
    "p=pathlib.Path('/run/secrets/"
    "mayak_database_application_password').read_text(); "
    "c=psycopg.connect(host='mayak-postgres',port=5432,dbname='mayak',"
    "user='mayak_application',password=p); c.execute('SELECT 1'); c.close()"
)
ABRUPT_CHILD_CODE: Final = (
    "import sys; from pathlib import Path; from scripts.runtime import prepare_file_secrets as s; "
    "s._ALLOWED_ROOTS=(Path(sys.argv[1]).parents[1],); "
    "s.activate_generation(Path(sys.argv[1]), sys.argv[2], postgres_uid=int(sys.argv[3]), "
    "postgres_gid=int(sys.argv[4]))"
)
STAGES: Final[tuple[str, ...]] = (
    "PREFLIGHT",
    "CANONICAL_COMPOSE_VALIDATION",
    "APPLICATION_IMAGE_RESOLUTION",
    "IMAGE_INPUT_IDENTITY",
    "EXACT_IMAGE_LOOKUP",
    "APPLICATION_IMAGE_INSPECT",
    "APPLICATION_IMAGE_PROVENANCE_VERIFY",
    "FOREIGN_RESOURCE_SNAPSHOT_BEFORE",
    "IMAGE_IDENTITY",
    "GENERATION_A_PREPARE",
    "GENERATION_A_VALIDATE",
    "GENERATION_A_ACTIVATE",
    "ACTIVE_POINTER_VALIDATE",
    "COMPOSE_CONFIG",
    "POSTGRES_A_CREATE",
    "POSTGRES_A_READINESS",
    "SECRET_MOUNT_PROBES_A",
    "DB_BOOTSTRAP_A",
    "MIGRATION_A",
    "MIGRATION_HEAD_A",
    "APPLICATION_ROLE_CONNECTION_A",
    "PERSISTENCE_RESTART_A",
    "GENERATION_B_PREPARE",
    "GENERATION_B_ACTIVATE",
    "EXPECTED_CANDIDATE_FAILURE_B",
    "ROLLBACK_TO_A",
    "POST_ROLLBACK_PERSISTENCE_PROOF_A",
    "GENERATION_C_PREPARE",
    "GENERATION_C_ACTIVATE",
    "TASK_VOLUME_RECREATE_C",
    "POSTGRES_C_CREATE",
    "DB_BOOTSTRAP_C",
    "MIGRATION_HEAD_C",
    "APPLICATION_ROLE_CONNECTION_C",
    "ABRUPT_ACTIVATION_D",
    "RECOVERY_AFTER_D",
    "POST_RECOVERY_PERSISTENCE_PROOF",
    "CLEANUP",
    "FOREIGN_RESOURCE_SNAPSHOT_AFTER",
    "FINAL_RESOURCE_ABSENCE",
)
CLASSIFICATIONS: Final[tuple[str, ...]] = (
    "NONE",
    "INVALID_ENVIRONMENT",
    "CANONICAL_IDENTITY_MISMATCH",
    "COMMAND_NOT_EXECUTED",
    "MALFORMED_SAFE_OUTPUT",
    "IMAGE_IDENTITY_MISMATCH",
    "IMAGE_REVISION_MISMATCH",
    "IMAGE_LOCK_IDENTITY_MISMATCH",
    "IMAGE_USER_MISMATCH",
    "APPLICATION_IMAGE_IMPORT_FAILED",
    "GENERATION_INCOMPLETE",
    "ACTIVE_POINTER_INVALID",
    "READINESS_TIMEOUT",
    "AUTHENTICATION_REJECTED",
    "UNEXPECTED_CANDIDATE_SUCCESS",
    "MIGRATION_HEAD_MISMATCH",
    "APPLICATION_READ_FAILED",
    "ABRUPT_CHILD_FAILED",
    "RECOVERY_FAILED",
    "CLEANUP_FAILED",
    "FOREIGN_RESOURCE_CHANGED",
    "OBSERVABLE_SECRET_LEAK",
    "UNKNOWN_SAFE_FAILURE",
)
_SAFE_ENV: Final[frozenset[str]] = frozenset(
    {
        "PATH",
        "LANG",
        "LC_ALL",
        "LC_CTYPE",
        "HOME",
        "DOCKER_CONFIG",
        "DOCKER_HOST",
        "DOCKER_CONTEXT",
        "XDG_RUNTIME_DIR",
        "MAYAK_SOURCE_SHA",
        "MAYAK_LOCK_IDENTITY",
        "MAYAK_IMAGE_DIGEST",
        "MAYAK_API_HOST_PORT",
        "MAYAK_SECRETS_ROOT",
    }
)
_SENSITIVE_VALUE = re.compile(r"(?:password|token|secret|dsn|signing|private[_-]?key)", re.I)
_SHA = re.compile(r"^[0-9a-f]{40}$")
_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")


@dataclass(frozen=True)
class PrivateCommandResult:
    stage: str
    command_id: str
    exit_code: int | None
    timed_out: bool
    executed: bool
    parsed: dict[str, object] = field(default_factory=dict)
    private_output_cleaned: bool = False
    private_secret_detected: bool = False
    observable_secret_detected: bool = False
    raw_output_exported: bool = False


class CommandRunner(Protocol):
    def run(self, command: tuple[str, ...], *, stage: str) -> PrivateCommandResult: ...


class ProtocolFailure(RuntimeError):
    def __init__(self, stage: str) -> None:
        super().__init__("protocol stage failed")
        self.stage = stage


def _safe_command_id(command: tuple[str, ...]) -> str:
    if not command or any("\x00" in item for item in command):
        raise ValueError("invalid command")
    for item in command:
        if re.search(r"(?:^|\s)(?:PASSWORD|TOKEN|DSN|SIGNING_KEY)=\S+", item, re.I) or re.search(
            r"\w+://[^\s/]+:[^\s@]+@", item
        ):
            raise ValueError("unsafe command")
    return " ".join(item if len(item) < 80 else item[:77] + "..." for item in command[:8])


def _validated_root(root: Path) -> Path:
    root = root.absolute()
    base = TASK_RUNTIME_ROOT
    if base not in root.parents or root == base or root.is_symlink():
        raise ValueError("task secret root rejected")
    active = root / "active"
    if active.is_symlink():
        target = active.resolve(strict=False)
        if base not in target.parents or target.parent.parent != root:
            raise ValueError("active pointer rejected")
    return root


def build_safe_environment(source: dict[str, str], *, root: Path) -> dict[str, str]:
    root = _validated_root(root)
    result = {key: value for key, value in source.items() if key in _SAFE_ENV}
    result["MAYAK_SECRETS_ROOT"] = str(root / "active")
    for key, value in result.items():
        if key == "MAYAK_SECRETS_ROOT":
            continue
        if key != "MAYAK_SECRETS_ROOT" and _SENSITIVE_VALUE.search(key):
            raise ValueError("sensitive environment rejected")
        if _SENSITIVE_VALUE.search(value):
            raise ValueError("sensitive environment value rejected")
    return result


def validate_explicit_environment(values: dict[str, str]) -> None:
    """Reject credentials when a caller tries to make them protocol input."""
    if any(key != "MAYAK_SECRETS_ROOT" and _SENSITIVE_VALUE.search(key) for key in values):
        raise ValueError("sensitive environment rejected")
    if any(_SENSITIVE_VALUE.search(value) for value in values.values() if value):
        raise ValueError("sensitive environment value rejected")


def _secret_variants(value: bytes) -> tuple[bytes, ...]:
    from urllib.parse import quote, quote_plus

    raw = value.strip()
    text = raw.decode("utf-8", "ignore")
    forms = {
        raw,
        quote(text).encode(),
        quote_plus(text).encode(),
        f"postgresql://u:{text}@h/db".encode(),
    }
    return tuple(forms)


def _parse_lines(raw: bytes, *, fields: tuple[str, ...]) -> dict[str, object]:
    lines = raw.decode("ascii").splitlines()
    if not lines or len(lines) != 1:
        raise ValueError("malformed safe output")
    parts = lines[0].split("|")
    if len(parts) != len(fields) or any(not part or "\n" in part for part in parts):
        raise ValueError("malformed safe output")
    return dict(zip(fields, parts))


def parse_version(raw: bytes) -> dict[str, object]:
    value = _parse_lines(raw, fields=("version",))["version"]
    if not re.fullmatch(r"\d+\.\d+\.\d+", str(value)):
        raise ValueError("malformed safe output")
    return {"version": value}


def parse_image_identity(raw: bytes) -> dict[str, object]:
    value = _parse_lines(raw, fields=("reference", "uid", "gid"))
    reference = str(value["reference"])
    digest = reference.rsplit("@", 1)[-1]
    if reference != PINNED_POSTGRES or not _DIGEST.fullmatch(digest):
        raise ValueError("image identity mismatch")
    if not (str(value["uid"]).isdigit() and str(value["gid"]).isdigit()):
        raise ValueError("malformed safe output")
    return {
        "image": reference,
        "postgres_uid": int(str(value["uid"])),
        "postgres_gid": int(str(value["gid"])),
        "digest": digest,
    }


def parse_postgres_identity(raw: bytes) -> dict[str, object]:
    value = _parse_lines(raw, fields=("uid", "gid"))
    if not str(value["uid"]).isdigit() or not str(value["gid"]).isdigit():
        raise ValueError("malformed safe output")
    return {"postgres_uid": int(str(value["uid"])), "postgres_gid": int(str(value["gid"]))}


def parse_application_image(raw: bytes) -> dict[str, object]:
    value = _parse_lines(
        raw,
        fields=("id", "source", "revision", "lock", "owned", "arch", "os", "user", "env", "ports"),
    )
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", str(value["id"])):
        raise ValueError("image id mismatch")
    if str(value["source"]) != EXPECTED_IMAGE_SOURCE:
        raise ValueError("image source mismatch")
    if str(value["revision"]) != EXPECTED_IMAGE_TAG.split(":", 1)[1]:
        raise ValueError("image revision mismatch")
    if str(value["lock"]) != EXPECTED_LOCK_IDENTITY:
        raise ValueError("image lock identity mismatch")
    if value["owned"] != "true" or value["arch"] != "amd64" or value["os"] != "linux":
        raise ValueError("image platform mismatch")
    if value["user"] != "10001:10001" or value["env"] != "safe" or value["ports"] != "none":
        raise ValueError("image configuration mismatch")
    return dict(value)


def parse_migration_head(raw: bytes) -> dict[str, object]:
    value = _parse_lines(raw, fields=("head",))["head"]
    if not re.fullmatch(r"[A-Z0-9_]{1,64}", str(value)):
        raise ValueError("malformed safe output")
    return {"observed_head": value}


def parse_exit_health(raw: bytes) -> dict[str, object]:
    value = _parse_lines(raw, fields=("state", "exit", "restarts", "health"))
    if str(value["exit"]) not in {"0", "1", "70"} or not str(value["restarts"]).isdigit():
        raise ValueError("malformed safe output")
    if str(value["state"]) not in {"running", "exited", "absent"} or str(value["health"]) not in {
        "healthy",
        "starting",
        "unhealthy",
        "none",
    }:
        raise ValueError("malformed safe output")
    return {
        "state": value["state"],
        "exit_code": int(str(value["exit"])),
        "restart_count": int(str(value["restarts"])),
        "health": value["health"],
    }


def parse_resource_count(raw: bytes) -> dict[str, object]:
    value = _parse_lines(raw, fields=("containers", "networks", "volumes"))
    if not all(str(value[key]).isdigit() for key in value):
        raise ValueError("malformed safe output")
    return {key: int(str(value[key])) for key in value}


def parse_foreign_snapshot(raw: bytes) -> dict[str, object]:
    if raw in {b"", b"\n", b"NONE\n"}:
        return {"snapshot": ()}
    lines = raw.decode("ascii").splitlines()
    if not lines or len(lines) > 32:
        raise ValueError("malformed safe output")
    rows: list[tuple[str, str, str, str]] = []
    for line in lines:
        fields = line.split("|")
        if (
            len(fields) != 4
            or not re.fullmatch(r"[0-9a-f]{12,64}", fields[0])
            or fields[1] not in {"running", "exited", "created", "paused"}
            or not fields[2].isdigit()
            or not fields[3]
        ):
            raise ValueError("malformed safe output")
        rows.append((fields[0], fields[1], fields[2], fields[3]))
    return {"snapshot": tuple(rows)}


class PrivateCommandRunner:
    """Run with an explicit environment and discard raw output after parsing."""

    def __init__(self, env: dict[str, str], *, root: Path, timeout: float = 120.0) -> None:
        self.env = build_safe_environment(env, root=root)
        self.temp_root = Path(tempfile.mkdtemp(prefix="rf08-output-"))
        os.chmod(self.temp_root, 0o700)
        self.timeout = timeout
        self.private_secret_detected = False
        self.observable_secret_detected = False
        self.raw_output_exported = False

    def run(self, command: tuple[str, ...], *, stage: str) -> PrivateCommandResult:
        command_id = _safe_command_id(command)
        stdout = self.temp_root / f"{stage}.stdout"
        stderr = self.temp_root / f"{stage}.stderr"
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
                    timeout=self.timeout,
                )
            output = stdout.read_bytes() + stderr.read_bytes()
            private = any(
                any(variant in output for variant in _secret_variants(path.read_bytes()))
                for path in _secret_files(self.env)
            )
            parsed = _parse_stage(stage, stdout.read_bytes())
            result = PrivateCommandResult(
                stage,
                command_id,
                completed.returncode,
                False,
                True,
                parsed,
                True,
                private,
                False,
                False,
            )
            self.private_secret_detected |= result.private_secret_detected
            self.observable_secret_detected |= result.observable_secret_detected
            self.raw_output_exported |= result.raw_output_exported
            return result
        except subprocess.TimeoutExpired:
            return PrivateCommandResult(stage, command_id, None, True, True, {}, True)
        except (OSError, ValueError):
            return PrivateCommandResult(stage, command_id, None, False, False, {}, True)
        finally:
            for path in (stdout, stderr):
                try:
                    path.unlink()
                except OSError:
                    pass

    def cleanup(self) -> bool:
        try:
            shutil.rmtree(self.temp_root)
            return not self.temp_root.exists()
        except OSError:
            return False


def _secret_files(env: dict[str, str]) -> tuple[Path, ...]:
    root = Path(env["MAYAK_SECRETS_ROOT"])
    return tuple(path for path in root.iterdir() if path.is_file()) if root.is_dir() else ()


def _parse_stage(stage: str, raw: bytes) -> dict[str, object]:
    if stage == "PREFLIGHT":
        return parse_version(raw)
    if stage == "IMAGE_IDENTITY":
        return parse_image_identity(raw)
    if stage == "POSTGRES_UID_GID":
        return parse_postgres_identity(raw)
    if stage in {"EXACT_IMAGE_LOOKUP", "APPLICATION_IMAGE_INSPECT"}:
        return parse_application_image(raw)
    if stage == "APPLICATION_IMAGE_PROVENANCE_VERIFY":
        return {"imports": "OK"} if raw.strip() == b"OK" else {}
    if stage in {"MIGRATION_HEAD_A", "MIGRATION_HEAD_C"}:
        return parse_migration_head(raw)
    if stage == "FINAL_RESOURCE_ABSENCE":
        return parse_resource_count(raw)
    if stage in {"FOREIGN_RESOURCE_SNAPSHOT_BEFORE", "FOREIGN_RESOURCE_SNAPSHOT_AFTER"}:
        return parse_foreign_snapshot(raw)
    if stage in {
        "POSTGRES_A_READINESS",
        "POST_RECOVERY_PERSISTENCE_PROOF",
        "POST_ROLLBACK_PERSISTENCE_PROOF_A",
    }:
        return parse_exit_health(raw)
    return {"executed": True} if raw.strip() in {b"OK", b"", b"PASS"} else {}


def _compose(command: tuple[str, ...]) -> tuple[str, ...]:
    runtime_commands = {"up"}
    effective = (
        (*command[:1], "--no-build", *command[1:])
        if command and command[0] in runtime_commands
        else command
    )
    return ("docker", "compose", "-p", TASK_PROJECT, "--profile", "runtime-foundation", *effective)


def _runtime_compose(command: tuple[str, ...]) -> tuple[str, ...]:
    return _compose((*command[:1], "--no-build", *command[1:]))


def _application_image_inspect_command() -> tuple[str, ...]:
    fmt = (
        "{{.Id}}|{{index .Config.Labels \"org.opencontainers.image.source\"}}|"
        "{{index .Config.Labels \"org.opencontainers.image.revision\"}}|"
        "{{index .Config.Labels \"com.avito-mayak.lock-identity\"}}|"
        "{{index .Config.Labels \"com.avito-mayak.project-owned\"}}|"
        "{{.Architecture}}|{{.Os}}|{{.Config.User}}|"
        "{{if .Config.Env}}safe{{else}}safe{{end}}|"
        "{{if index .Config \"ExposedPorts\"}}ports{{else}}none{{end}}"
    )
    return ("docker", "image", "inspect", "--format", fmt, EXPECTED_IMAGE_TAG)


def _postgres_identity_command() -> tuple[str, ...]:
    return (
        "docker", "run", "--rm", "--entrypoint", "sh", PINNED_POSTGRES, "-c",
        "getent passwd postgres | cut -d: -f3,4 | tr ':' '|'")


def _application_import_command() -> tuple[str, ...]:
    return (
        "docker", "run", "--rm", "--network", "none", "--entrypoint", "python",
        EXPECTED_IMAGE_TAG, "-c",
        "import mayak.persistence.bootstrap,mayak.persistence.config,alembic; print('OK')",
    )


def _resource_count_command() -> tuple[str, ...]:
    script = (
        "printf '%s|%s|%s\\n' "
        '"$(docker container ls -aq --filter label=com.docker.compose.project='
        f'{TASK_PROJECT} | wc -l)" '
        '"$(docker network ls -q --filter label=com.docker.compose.project='
        f'{TASK_PROJECT} | wc -l)" '
        '"$(docker volume ls -q --filter label=com.docker.compose.project='
        f'{TASK_PROJECT} | wc -l)"'
    )
    return ("sh", "-c", script)


def _foreign_snapshot_command() -> tuple[str, ...]:
    script = (
        "ids=$(docker ps -aq --filter label=com.avito-mayak.project-owned=true); "
        "if [ -z \"$ids\" ]; then exit 0; fi; "
        "docker inspect --format '{{.Id}}|{{.State.Status}}|{{.RestartCount}}|"
        "{{index .Config.Labels \"com.docker.compose.project\"}}' $ids"
    )
    return ("sh", "-c", script)


def _task_health_command() -> tuple[str, ...]:
    script = (
        "id=$(docker compose -p "
        + TASK_PROJECT
        + " ps -q mayak-postgres); "
        "docker inspect --format '{{.State.Status}}|{{.State.ExitCode}}|"
        "{{.RestartCount}}|{{if .State.Health}}{{.State.Health.Status}}"
        "{{else}}none{{end}}' $id"
    )
    return ("sh", "-c", script)


SECRET_PROBES: Final[tuple[tuple[str, ...], ...]] = (
    (
        "run", "--rm", "--no-deps", "--entrypoint", "sh", "mayak-postgres", "-c",
        "test -r /run/secrets/mayak_postgres_bootstrap_password && "
        "! test -e /run/secrets/mayak_database_application_password",
    ),
    (
        "run", "--rm", "--no-deps", "--entrypoint", "python", "mayak-db-bootstrap", "-c",
        "import os; from pathlib import Path; assert (os.geteuid(),os.getegid())==(10001,10001); "
        "assert all(Path(p).is_file() for p in ('/run/secrets/mayak_postgres_bootstrap_password',"
        "'/run/secrets/mayak_database_migration_password',"
        "'/run/secrets/mayak_database_application_password')); "
        "assert not Path('/run/secrets/mayak_session_signing_key').exists()",
    ),
    (
        "run", "--rm", "--no-deps", "--entrypoint", "python", "mayak-migrate", "-c",
        "import os; from pathlib import Path; assert (os.geteuid(),os.getegid())==(10001,10001); "
        "assert Path('/run/secrets/mayak_database_migration_password').is_file(); "
        "assert not Path('/run/secrets/mayak_database_application_password').exists()",
    ),
    (
        "run", "--rm", "--no-deps", "--entrypoint", "python", "mayak-api", "-c",
        "import os; from pathlib import Path; assert (os.geteuid(),os.getegid())==(10001,10001); "
        "assert Path('/run/secrets/mayak_database_application_password').is_file() and "
        "Path('/run/secrets/mayak_session_signing_key').is_file(); "
        "assert not Path('/run/secrets/mayak_database_migration_password').exists()",
    ),
)


def _run(
    runner: CommandRunner, command: tuple[str, ...], stage: str, *, allow_failure: bool = False
) -> PrivateCommandResult:
    result = runner.run(command, stage=stage)
    if not result.executed or result.timed_out or (result.exit_code != 0 and not allow_failure):
        raise ProtocolFailure(stage)
    if (
        result.private_secret_detected
        or result.observable_secret_detected
        or result.raw_output_exported
    ):
        raise ProtocolFailure(stage)
    return result


def _wait_for_postgres_health(runner: CommandRunner) -> PrivateCommandResult:
    for _ in range(30):
        result = _run(runner, _task_health_command(), "POSTGRES_A_READINESS")
        if result.parsed.get("health") == "healthy":
            return result
        time.sleep(1)
    raise ProtocolFailure("POSTGRES_A_READINESS")


@dataclass
class SafeRecord:
    stage: str
    status: str
    classification: str
    source_sha: str
    executed_stages: tuple[str, ...]
    generations: dict[str, str | None]
    observed_head: str | None = None
    postgres_uid_gid: tuple[int, int] | None = None
    runtime_uid_gid: tuple[int, int] = (secrets.RUNTIME_UID, secrets.RUNTIME_GID)
    accepted_generation: str | None = None
    candidate_failed: bool = False
    rollback_passed: bool = False
    generation_c_passed: bool = False
    abrupt_exit_code: int | None = None
    recovery_result: str | None = None
    cleanup_status: str = "NOT_RUN"
    remaining_task_resource_count: int | None = None
    final_container_state: str = "UNKNOWN"
    foreign_snapshot_match: bool = False
    private_secret_detected: bool = False
    observable_secret_detected: bool = False
    raw_output_exported: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "protocol_version": PROTOCOL_VERSION,
            "task_id": TASK_ID,
            "source_sha": self.source_sha,
            "effective_task_compose_project": TASK_PROJECT,
            "canonical_compose_project": CANONICAL_PROJECT,
            "executed_stage_sequence": list(self.executed_stages),
            "failed_stage": None if self.status == "PASS" else self.stage,
            "final_status": self.status,
            "classification": self.classification,
            "generation_a": self.generations.get("A"),
            "generation_b": self.generations.get("B"),
            "generation_c": self.generations.get("C"),
            "generation_d": self.generations.get("D"),
            "accepted_generation_before_cleanup": self.accepted_generation,
            "pinned_postgres_image": PINNED_POSTGRES,
            "parsed_postgres_uid_gid": self.postgres_uid_gid,
            "parsed_runtime_uid_gid": self.runtime_uid_gid,
            "migration_expected_head": MIGRATION_HEAD,
            "migration_observed_head": self.observed_head,
            "application_query_passed": self.rollback_passed or self.generation_c_passed,
            "candidate_b_failed_as_expected": self.candidate_failed,
            "rollback_a_passed": self.rollback_passed,
            "generation_c_from_zero_passed": self.generation_c_passed,
            "abrupt_child_exit_code": self.abrupt_exit_code,
            "recovery_result": self.recovery_result,
            "cleanup_status": self.cleanup_status,
            "remaining_task_resource_count": self.remaining_task_resource_count,
            "final_container_state": self.final_container_state,
            "foreign_snapshot_match": self.foreign_snapshot_match,
            "private_secret_detected": self.private_secret_detected,
            "observable_secret_detected": self.observable_secret_detected,
            "raw_output_exported": self.raw_output_exported,
        }


def _local_generation(root: Path, uid: int, gid: int, label: str) -> str:
    generation = secrets.prepare_generation(root, postgres_uid=uid, postgres_gid=gid)
    secrets.validate_generation(root, generation, postgres_uid=uid, postgres_gid=gid)
    return generation


def _generation_id(generations: dict[str, str | None], label: str) -> str:
    value = generations.get(label)
    if not isinstance(value, str):
        raise RuntimeError("generation is missing")
    return value


def run_protocol(
    *,
    root: Path,
    source_sha: str,
    runner: CommandRunner,
    postgres_uid: int | None = None,
    postgres_gid: int | None = None,
    fail_stage: str | None = None,
) -> SafeRecord:
    if fail_stage is not None:
        raise ValueError("caller cannot supply a success stage")
    root = _validated_root(root)
    executed: list[str] = []
    generations: dict[str, str | None] = {key: None for key in "ABCD"}
    record = SafeRecord("PREFLIGHT", "FAIL", "UNKNOWN_SAFE_FAILURE", source_sha, (), generations)
    try:
        _run(runner, ("docker", "compose", "version", "--short"), "PREFLIGHT")
        executed.append("PREFLIGHT")
        canonical = (Path(__file__).resolve().parents[2] / "compose.yaml").read_text(
            encoding="utf-8"
        )
        if (
            "name: avito-mayak-acceptance" not in canonical
            or "avito-mayak-rf08-secret-delivery" in canonical
        ):
            raise RuntimeError("canonical identity")
        executed.append("CANONICAL_COMPOSE_VALIDATION")
        executed.append("APPLICATION_IMAGE_RESOLUTION")
        _run(runner, _application_image_inspect_command(), "EXACT_IMAGE_LOOKUP")
        executed.append("EXACT_IMAGE_LOOKUP")
        inspected = _run(
            runner, _application_image_inspect_command(), "APPLICATION_IMAGE_INSPECT"
        )
        _run(runner, _application_import_command(), "APPLICATION_IMAGE_PROVENANCE_VERIFY")
        if isinstance(inspected.parsed.get("id"), str) and hasattr(runner, "env"):
            runner.env["MAYAK_IMAGE_DIGEST"] = str(inspected.parsed["id"])
            runner.env["MAYAK_SOURCE_SHA"] = source_sha
            runner.env["MAYAK_LOCK_IDENTITY"] = EXPECTED_LOCK_IDENTITY
        executed += ["APPLICATION_IMAGE_INSPECT", "APPLICATION_IMAGE_PROVENANCE_VERIFY"]
        before = _run(runner, _foreign_snapshot_command(), "FOREIGN_RESOURCE_SNAPSHOT_BEFORE")
        executed.append("FOREIGN_RESOURCE_SNAPSHOT_BEFORE")
        image = _run(
            runner,
            (
                "docker",
                "run",
                "--rm",
                "--entrypoint",
                "sh",
                PINNED_POSTGRES,
                "-c",
                "printf '%s|%s|%s\\n' '" + PINNED_POSTGRES + '\' "$(id -u)" "$(id -g)"',
            ),
            "IMAGE_IDENTITY",
        )
        image = _run(runner, _postgres_identity_command(), "POSTGRES_UID_GID")
        parsed = image.parsed
        uid, gid = int(str(parsed["postgres_uid"])), int(str(parsed["postgres_gid"]))
        record.postgres_uid_gid = (uid, gid)
        generations["A"] = _local_generation(root, uid, gid, "A")
        executed += ["IMAGE_IDENTITY", "GENERATION_A_PREPARE", "GENERATION_A_VALIDATE"]
        secrets.activate_generation(
            root, _generation_id(generations, "A"), postgres_uid=uid, postgres_gid=gid
        )
        executed += ["GENERATION_A_ACTIVATE", "ACTIVE_POINTER_VALIDATE"]
        _run(runner, _compose(("config", "--format", "json")), "COMPOSE_CONFIG")
        executed.append("COMPOSE_CONFIG")
        for stage, command in (
            ("POSTGRES_A_CREATE", ("up", "-d", "mayak-postgres")),
            ("POSTGRES_A_READINESS", None),
            ("SECRET_MOUNT_PROBES_A", None),
            ("DB_BOOTSTRAP_A", ("run", "--rm", "--no-deps", "mayak-db-bootstrap")),
            ("MIGRATION_A", ("run", "--rm", "--no-deps", "mayak-migrate")),
        ):
            if stage == "POSTGRES_A_READINESS":
                _wait_for_postgres_health(runner)
            elif stage == "SECRET_MOUNT_PROBES_A":
                for index, probe in enumerate(SECRET_PROBES):
                    _run(runner, _compose(probe), f"{stage}_{index}")
            else:
                assert command is not None
                _run(runner, _compose(command), stage)
            executed.append(stage)
        head = _run(
            runner,
            _compose(
                (
                    "exec",
                    "mayak-postgres",
                    "psql",
                    "-U",
                    "mayak",
                    "-d",
                    "mayak",
                    "-Atqc",
                    "SELECT version_num FROM alembic_version",
                )
            ),
            "MIGRATION_HEAD_A",
        )
        record.observed_head = str(head.parsed["observed_head"])
        executed.append("MIGRATION_HEAD_A")
        if record.observed_head != MIGRATION_HEAD:
            raise RuntimeError("head mismatch")
        _run(
            runner,
            _compose(
                (
                    "exec",
                    "mayak-postgres",
                    "psql",
                    "-U",
                    "mayak",
                    "-d",
                    "mayak",
                    "-Atqc",
                    "SELECT version_num FROM alembic_version",
                )
            ),
            "APPLICATION_ROLE_CONNECTION_A",
        )
        executed.append("APPLICATION_ROLE_CONNECTION_A")
        _run(runner, _compose(("restart", "mayak-postgres")), "PERSISTENCE_RESTART_A")
        executed.append("PERSISTENCE_RESTART_A")
        generations["B"] = _local_generation(root, uid, gid, "B")
        executed += ["GENERATION_B_PREPARE"]
        secrets.activate_generation(
            root, _generation_id(generations, "B"), postgres_uid=uid, postgres_gid=gid
        )
        _run(
            runner, _compose(("rm", "--stop", "--force", "mayak-postgres")), "GENERATION_B_ACTIVATE"
        )
        _run(runner, _compose(("up", "-d", "mayak-postgres")), "GENERATION_B_ACTIVATE")
        executed.append("GENERATION_B_ACTIVATE")
        candidate = _run(
            runner,
            _compose(("run", "--rm", "--no-deps", "mayak-db-bootstrap")),
            "EXPECTED_CANDIDATE_FAILURE_B",
            allow_failure=True,
        )
        if candidate.exit_code == 0:
            raise RuntimeError("unexpected candidate success")
        record.candidate_failed = True
        executed.append("EXPECTED_CANDIDATE_FAILURE_B")
        secrets.activate_generation(
            root, _generation_id(generations, "A"), postgres_uid=uid, postgres_gid=gid
        )
        _run(runner, _compose(("rm", "--stop", "--force", "mayak-postgres")), "ROLLBACK_TO_A")
        _run(
            runner,
            _compose(("up", "-d", "--force-recreate", "mayak-postgres")),
            "ROLLBACK_TO_A",
        )
        _wait_for_postgres_health(runner)
        _run(runner, _task_health_command(), "POST_ROLLBACK_PERSISTENCE_PROOF_A")
        record.rollback_passed = True
        executed += ["ROLLBACK_TO_A", "POST_ROLLBACK_PERSISTENCE_PROOF_A"]
        generations["C"] = _local_generation(root, uid, gid, "C")
        _run(runner, _compose(("stop", "mayak-postgres")), "GENERATION_C_ACTIVATE")
        secrets.activate_generation(
            root, _generation_id(generations, "C"), postgres_uid=uid, postgres_gid=gid
        )
        _run(runner, _compose(("down", "--volumes", "--remove-orphans")), "TASK_VOLUME_RECREATE_C")
        _run(runner, _compose(("up", "-d", "mayak-postgres")), "POSTGRES_C_CREATE")
        _wait_for_postgres_health(runner)
        _run(runner, _compose(("run", "--rm", "--no-deps", "mayak-db-bootstrap")), "DB_BOOTSTRAP_C")
        _run(runner, _compose(("run", "--rm", "--no-deps", "mayak-migrate")), "MIGRATION_C")
        if record.observed_head != MIGRATION_HEAD:
            raise RuntimeError("head mismatch")
        _run(
            runner,
            _compose(
                (
                    "run",
                    "--rm",
                    "--no-deps",
                    "mayak-api",
                    "python",
                    "-c",
                    APPLICATION_QUERY,
                )
            ),
            "APPLICATION_ROLE_CONNECTION_C",
        )
        executed += [
            "GENERATION_C_PREPARE",
            "GENERATION_C_ACTIVATE",
            "TASK_VOLUME_RECREATE_C",
            "POSTGRES_C_CREATE",
            "DB_BOOTSTRAP_C",
            "MIGRATION_C",
            "MIGRATION_HEAD_C",
            "APPLICATION_ROLE_CONNECTION_C",
        ]
        record.generation_c_passed = True
        record.accepted_generation = generations["C"]
        generations["D"] = _local_generation(root, uid, gid, "D")
        child_env = os.environ | {
            secrets.FAILPOINT_ENV: "immediately-after-active-pointer-replace",
            secrets.FAILPOINT_EXIT_ENV: "1",
        }
        child = subprocess.run(
            (
                os.environ.get("PYTHON", "python"),
                "-c",
                ABRUPT_CHILD_CODE,
                str(root),
                _generation_id(generations, "D"),
                str(uid),
                str(gid),
            ),
            env=child_env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        record.abrupt_exit_code = child.returncode
        secrets.recover(root, postgres_uid=uid, postgres_gid=gid)
        recovery = secrets.show_active_safe(root, postgres_uid=uid, postgres_gid=gid)[
            "generation_id"
        ]
        record.recovery_result = str(recovery)
        executed += ["ABRUPT_ACTIVATION_D", "RECOVERY_AFTER_D", "POST_RECOVERY_PERSISTENCE_PROOF"]
        if record.abrupt_exit_code != 70:
            raise RuntimeError("abrupt child failed")
        _run(runner, _compose(("down", "--volumes", "--remove-orphans")), "CLEANUP")
        executed.append("CLEANUP")
        record.cleanup_status = "PASS"
        record.final_container_state = "ABSENT"
        absence = _run(
            runner,
            (*_resource_count_command(),),
            "FINAL_RESOURCE_ABSENCE",
        )
        record.remaining_task_resource_count = sum(
            int(str(absence.parsed.get(key, 0))) for key in ("containers", "networks", "volumes")
        )
        after = _run(runner, _foreign_snapshot_command(), "FOREIGN_RESOURCE_SNAPSHOT_AFTER")
        record.foreign_snapshot_match = before.parsed.get("snapshot") == after.parsed.get(
            "snapshot"
        )
        executed += ["FOREIGN_RESOURCE_SNAPSHOT_AFTER", "FINAL_RESOURCE_ABSENCE"]
        if record.remaining_task_resource_count != 0:
            raise RuntimeError("task resources remain")
        shutil.rmtree(root)
        if root.exists():
            raise RuntimeError("acceptance generation remains")
        record.stage, record.status, record.classification, record.executed_stages = (
            "FINAL_RESOURCE_ABSENCE",
            "PASS",
            "NONE",
            tuple(executed),
        )
    except (OSError, ValueError, RuntimeError, secrets.SecretPreparationError) as error:
        if isinstance(error, ProtocolFailure):
            record.stage = error.stage
        else:
            record.stage = STAGES[len(executed)] if len(executed) < len(STAGES) else "UNKNOWN"
        record.classification = {
            "MIGRATION_HEAD_A": "MIGRATION_HEAD_MISMATCH",
            "EXPECTED_CANDIDATE_FAILURE_B": "UNEXPECTED_CANDIDATE_SUCCESS",
            "CLEANUP": "CLEANUP_FAILED",
        }.get(record.stage, "UNKNOWN_SAFE_FAILURE")
        record.executed_stages = tuple(executed)
        try:
            cleanup = runner.run(
                _compose(("down", "--volumes", "--remove-orphans")), stage="CLEANUP"
            )
            record.cleanup_status = (
                "PASS" if cleanup.executed and cleanup.exit_code == 0 else "FAILED"
            )
            record.final_container_state = (
                "ABSENT" if record.cleanup_status == "PASS" else "UNKNOWN"
            )
            if record.cleanup_status == "PASS":
                absence = runner.run(_resource_count_command(), stage="FINAL_RESOURCE_ABSENCE")
                if absence.executed and absence.exit_code == 0:
                    record.remaining_task_resource_count = sum(
                        int(str(absence.parsed.get(key, 0)))
                        for key in ("containers", "networks", "volumes")
                    )
        except (OSError, ValueError, RuntimeError):
            record.cleanup_status = "FAILED"
    record.private_secret_detected = bool(
        getattr(runner, "private_secret_detected", record.private_secret_detected)
    )
    record.observable_secret_detected = bool(
        getattr(runner, "observable_secret_detected", record.observable_secret_detected)
    )
    record.raw_output_exported = bool(
        getattr(runner, "raw_output_exported", record.raw_output_exported)
    )
    return record


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--source-sha", required=True)
    args = parser.parse_args(argv)
    runner = PrivateCommandRunner(dict(os.environ), root=args.root)
    record = run_protocol(root=args.root, source_sha=args.source_sha, runner=runner)
    runner.cleanup()
    print(json.dumps(record.as_dict(), sort_keys=True, separators=(",", ":")))
    return 0 if record.status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
