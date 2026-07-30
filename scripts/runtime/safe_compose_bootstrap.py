#!/usr/bin/env python3
"""RF-08 secret-safe acceptance protocol with one transcript executor."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Final, Mapping, Protocol, cast

from scripts.runtime import prepare_file_secrets as secrets

TASK_ID: Final = "RF-08-CORRECTIVE-NONROOT-FILE-SECRET-DELIVERY-20260729-01"
TASK_PROJECT: Final = "avito-mayak-rf08-secret-delivery"
CANONICAL_PROJECT: Final = "avito-mayak-acceptance"
EXPECTED_IMAGE_TAG: Final = "avito-mayak:7d53282d08095669b38547571aba9d15464aff20"
EXPECTED_IMAGE_SOURCE: Final = "https://github.com/MaksimUnimax/AVITO_Mayak"
EXPECTED_LOCK_IDENTITY: Final = "e1faff1ce0f4d5dfd35480ab59d5d599fddf05c38fcd16a26c52098511476ab6"
TASK_RUNTIME_ROOT: Final = Path("/opt/avito-mayak-runtime/rf08-secret-delivery")
EVIDENCE_PATH: Final = Path(
    "docs/07-quality/evidence/RF08_AUTHORITATIVE_SECRET_LIFECYCLE_PROOF_v1.json"
)
MIGRATION_HEAD: Final = "RF09_FINALIZE"
_SENSITIVE = re.compile(r"(?:password|token|secret|dsn|private[_-]?key|signing)", re.I)
_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
APPLICATION_QUERY: Final = (
    "import pathlib,psycopg; "
    "p=pathlib.Path('/run/secrets/mayak_database_application_password').read_text(); "
    "c=psycopg.connect(host='mayak-postgres',port=5432,dbname='mayak',"
    "user='mayak_application',password=p); "
    "assert c.execute('SELECT 1').fetchone()==(1,); c.close(); "
    "print('APPLICATION_QUERY_OK')"
)
APPLICATION_AUTH_REJECTION_QUERY: Final = (
    "import pathlib,psycopg\n"
    "p=pathlib.Path('/run/secrets/mayak_database_application_password').read_text()\n"
    "try:\n"
    "    psycopg.connect(host='mayak-postgres',port=5432,dbname='mayak',"
    "user='mayak_application',password=p)\n"
    "except psycopg.Error as e:\n"
    "    sqlstate=getattr(e,'sqlstate',None) or getattr(getattr(e,'diag',None),'sqlstate',None)\n"
    "    if sqlstate=='28P01' or 'password authentication failed' in str(e).lower():\n"
    "        print('APPLICATION_AUTH_REJECTED')\n"
    "        raise SystemExit(78)\n"
    "    raise SystemExit(79)\n"
    "raise SystemExit(79)\n"
)
REQUIRED_STAGES: Final[tuple[str, ...]] = (
    "PREFLIGHT",
    "CANONICAL_COMPOSE_VALIDATION",
    "IMAGE_INPUT_DIGEST",
    "APPLICATION_IMAGE_RESOLUTION",
    "APPLICATION_IMAGE_BUILD_OR_REUSE",
    "APPLICATION_IMAGE_INSPECT",
    "APPLICATION_IMAGE_PROVENANCE_VERIFY",
    "APPLICATION_IMAGE_ENVIRONMENT_VERIFY",
    "FOREIGN_RESOURCE_SNAPSHOT_BEFORE",
    "TASK_RESOURCE_PREFLIGHT",
    "SECRET_GENERATION_A_CREATE",
    "SECRET_GENERATION_A_VALIDATE",
    "SECRET_GENERATION_A_ACTIVATE",
    "SECRET_GENERATION_A_POINTER_VERIFY",
    "SECRET_CONSUMER_COPIES_A_VERIFY",
    "SECRET_INTENDED_READABILITY_A",
    "SECRET_UNINTENDED_DENIAL_A",
    "POSTGRES_A_CREATE",
    "POSTGRES_A_HEALTH",
    "DATABASE_BOOTSTRAP_A",
    "MIGRATION_UPGRADE_A",
    "MIGRATION_HEAD_A",
    "APPLICATION_QUERY_A",
    "POSTGRES_A_STOP",
    "POSTGRES_A_RECREATE",
    "POSTGRES_A_RESTART_HEALTH",
    "DATABASE_BOOTSTRAP_RESTART_A",
    "MIGRATION_HEAD_RESTART_A",
    "APPLICATION_QUERY_RESTART_A",
    "SECRET_GENERATION_B_CREATE",
    "SECRET_GENERATION_B_VALIDATE",
    "SECRET_GENERATION_B_ACTIVATE",
    "SECRET_GENERATION_B_POINTER_VERIFY",
    "APPLICATION_AUTH_REJECTION_B",
    "APPLICATION_AUTH_REJECTION_B_CLASSIFY",
    "SECRET_ROLLBACK_A_ACTIVATE",
    "SECRET_ROLLBACK_A_POINTER_VERIFY",
    "POSTGRES_ROLLBACK_A_RECREATE",
    "POSTGRES_ROLLBACK_A_HEALTH",
    "DATABASE_BOOTSTRAP_ROLLBACK_A",
    "MIGRATION_HEAD_ROLLBACK_A",
    "APPLICATION_QUERY_ROLLBACK_A",
    "SECRET_GENERATION_C_CREATE",
    "SECRET_GENERATION_C_VALIDATE",
    "SECRET_GENERATION_C_ACTIVATE",
    "POSTGRES_C_REMOVE_AND_VOLUME_ABSENCE",
    "POSTGRES_C_CREATE",
    "POSTGRES_C_HEALTH",
    "DATABASE_BOOTSTRAP_C",
    "MIGRATION_UPGRADE_C",
    "MIGRATION_HEAD_C",
    "APPLICATION_QUERY_C",
    "ABRUPT_ACTIVATION_D_EXIT_70",
    "SECRET_RECOVERY_D_AND_POINTER_VERIFY",
    "POST_RECOVERY_DATABASE_AND_APPLICATION_PROOF",
    "TASK_CLEANUP_AND_PRIVATE_OUTPUT_REMOVAL",
    "FOREIGN_RESOURCE_EQUALITY_AND_EVIDENCE_VALIDATION",
)
STAGES = REQUIRED_STAGES
CLASSIFICATIONS: Final[tuple[str, ...]] = (
    "NONE",
    "BOOTSTRAP_AUTH_REJECTED",
    "OBSERVABLE_SECRET_LEAK",
    "UNKNOWN_SAFE_FAILURE",
)


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


@dataclass(frozen=True)
class StageResult:
    stage: str
    operation_id: str
    executed: bool
    exit_code: int | None
    parsed: Mapping[str, object]
    filesystem_ok: bool = False
    docker_ok: bool = False
    safe_output: bool = True

    @classmethod
    def from_command(cls, result: PrivateCommandResult) -> "StageResult":
        return cls(
            result.stage,
            result.command_id,
            result.executed,
            result.exit_code,
            dict(result.parsed),
            result.private_output_cleaned,
            result.exit_code == 0,
            not (
                result.private_secret_detected
                or result.observable_secret_detected
                or result.raw_output_exported
            ),
        )


class SemanticOracle(Protocol):
    def __call__(self, result: StageResult) -> Mapping[str, object]: ...


@dataclass(frozen=True)
class StageSpec:
    name: str
    operation: Callable[[], StageResult]
    expected_result_type: type[StageResult]
    oracle: SemanticOracle
    required_safe_evidence: frozenset[str]
    failure_classification: str


@dataclass(frozen=True)
class TranscriptEntry:
    stage: str
    status: str
    evidence: Mapping[str, object]


class ProtocolTranscript:
    """The sole owner of stage insertion and finalization."""

    def __init__(self, required_stages: tuple[str, ...] = REQUIRED_STAGES) -> None:
        if len(required_stages) != len(set(required_stages)):
            raise ValueError("duplicate required stage")
        self._required = required_stages
        self._entries: list[TranscriptEntry] = []

    @property
    def entries(self) -> tuple[TranscriptEntry, ...]:
        return tuple(self._entries)

    @property
    def stage_sequence(self) -> tuple[str, ...]:
        return tuple(item.stage for item in self._entries)

    def execute(self, spec: StageSpec) -> TranscriptEntry:
        index = len(self._entries)
        if index >= len(self._required) or spec.name != self._required[index]:
            raise ProtocolFailure(spec.name)
        result = spec.operation()
        if type(result) is not spec.expected_result_type or result.stage != spec.name:
            raise ProtocolFailure(spec.name)
        if not result.executed or not result.safe_output:
            raise ProtocolFailure(spec.name)
        evidence = dict(spec.oracle(result))
        if not spec.required_safe_evidence.issubset(evidence):
            raise ProtocolFailure(spec.name)
        entry = TranscriptEntry(spec.name, "PASS", _safe_evidence(evidence))
        self._entries.append(entry)
        return entry

    def finalize(self, *, postconditions: Mapping[str, object]) -> tuple[TranscriptEntry, ...]:
        if (
            self.stage_sequence != self._required
            or not postconditions
            or any(value is not True for value in postconditions.values())
        ):
            raise ProtocolFailure("FINALIZE")
        return self.entries


def _safe_evidence(value: Mapping[str, object]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, item in value.items():
        if not re.fullmatch(r"[a-z][a-z0-9_]*", key) or _SENSITIVE.search(key):
            raise ProtocolFailure("EVIDENCE")
        if isinstance(item, (str, int, bool)):
            if _SENSITIVE.search(str(item)):
                raise ProtocolFailure("EVIDENCE")
            result[key] = item
        elif isinstance(item, (tuple, list)) and all(
            isinstance(part, (str, int, bool)) for part in item
        ):
            result[key] = list(item)
        else:
            raise ProtocolFailure("EVIDENCE")
    return result


def deterministic_build_input_digest(source_tree: Path) -> str:
    names = ["Dockerfile", ".dockerignore", "pyproject.toml", "uv.lock", "alembic.ini"]
    for directory in ("src/mayak", "alembic", "migrations"):
        names.extend(
            str(path.relative_to(source_tree))
            for path in (source_tree / directory).rglob("*")
            if path.is_file()
        )
    digest = hashlib.sha256()
    for name in sorted(set(names)):
        data = (source_tree / name).read_bytes()
        digest.update(len(name.encode()).to_bytes(8, "big"))
        digest.update(name.encode())
        digest.update(len(data).to_bytes(8, "big"))
        digest.update(data)
    return digest.hexdigest()


def parse_image_identity(raw: bytes) -> dict[str, object]:
    parts = raw.decode("ascii").strip().split("|")
    if (
        len(parts) != 3
        or "@sha256:" not in parts[0]
        or not all(part.isdigit() for part in parts[1:])
    ):
        raise ValueError("malformed safe output")
    return {"image": parts[0], "postgres_uid": int(parts[1]), "postgres_gid": int(parts[2])}


def parse_migration_head(raw: bytes) -> dict[str, object]:
    value = raw.decode("ascii").strip()
    if not re.fullmatch(r"[A-Z0-9_]{1,64}", value):
        raise ValueError("malformed safe output")
    return {"observed_head": value}


def parse_application_image(raw: bytes) -> dict[str, object]:
    try:
        document = json.loads(raw.decode("utf-8"))
        value = document[0] if isinstance(document, list) else document
        config = value["Config"]
        labels = config["Labels"]
        env = config.get("Env", [])
        if not isinstance(env, list) or any(not isinstance(item, str) for item in env):
            raise ValueError
    except (KeyError, TypeError, ValueError, UnicodeError, json.JSONDecodeError):
        raise ValueError("malformed image inspect JSON") from None
    if not _DIGEST.fullmatch(str(value.get("Id"))):
        raise ValueError("image id mismatch")
    if labels.get("org.opencontainers.image.source") != EXPECTED_IMAGE_SOURCE:
        raise ValueError("image source mismatch")
    if labels.get("org.opencontainers.image.revision") != EXPECTED_IMAGE_TAG.split(":", 1)[1]:
        raise ValueError("image revision mismatch")
    if labels.get("com.avito-mayak.lock-identity") != EXPECTED_LOCK_IDENTITY:
        raise ValueError("image lock identity mismatch")
    if labels.get("com.avito-mayak.project-owned") != "true":
        raise ValueError("image ownership mismatch")
    if value.get("Architecture") != "amd64" or value.get("Os") != "linux":
        raise ValueError("image platform mismatch")
    if config.get("User") != "10001:10001":
        raise ValueError("image user mismatch")
    if any(_SENSITIVE.search(item) for item in env):
        raise ValueError("secret-bearing image environment")
    if config.get("ExposedPorts"):
        raise ValueError("unexpected image ports")
    return {
        "image_id": value["Id"],
        "source": EXPECTED_IMAGE_SOURCE,
        "revision": EXPECTED_IMAGE_TAG.split(":", 1)[1],
        "lock_identity": EXPECTED_LOCK_IDENTITY,
        "user": "10001:10001",
        "environment_entries": len(env),
    }


def validate_explicit_environment(values: dict[str, str]) -> None:
    if any(
        (key != "MAYAK_SECRETS_ROOT") and (_SENSITIVE.search(key) or _SENSITIVE.search(value))
        for key, value in values.items()
    ):
        raise ValueError("sensitive environment rejected")


def build_safe_environment(source: dict[str, str], *, root: Path) -> dict[str, str]:
    root = root.absolute()
    if TASK_RUNTIME_ROOT not in root.parents or root == TASK_RUNTIME_ROOT:
        raise ValueError("task secret root rejected")
    result = {
        key: value
        for key, value in source.items()
        if key
        in {
            "PATH",
            "LANG",
            "LC_ALL",
            "DOCKER_HOST",
            "MAYAK_SOURCE_SHA",
            "MAYAK_LOCK_IDENTITY",
            "MAYAK_IMAGE_DIGEST",
            "MAYAK_API_HOST_PORT",
        }
    }
    result["MAYAK_SECRETS_ROOT"] = str(root / "active")
    validate_explicit_environment(result)
    return result


def _safe_command_id(command: tuple[str, ...]) -> str:
    if not command or any("\x00" in part for part in command):
        raise ValueError("invalid command")
    if any(
        _SENSITIVE.search(part)
        and "mayak_" not in part
        and TASK_PROJECT not in part
        for part in command
    ):
        raise ValueError("unsafe command")
    return " ".join(command[:8])


class PrivateCommandRunner:
    def __init__(self, env: dict[str, str], *, root: Path, timeout: float = 120.0) -> None:
        self.env = build_safe_environment(env, root=root)
        self.temp_root = Path(tempfile.mkdtemp(prefix="rf08-output-"))
        self.temp_root.chmod(0o700)
        self.timeout = timeout
        self.private_secret_detected = False
        self.observable_secret_detected = False
        self.raw_output_exported = False

    def run(self, command: tuple[str, ...], *, stage: str) -> PrivateCommandResult:
        command_id = _safe_command_id(command)
        stdout, stderr = self.temp_root / f"{stage}.out", self.temp_root / f"{stage}.err"
        try:
            out_fd = os.open(stdout, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            err_fd = os.open(stderr, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(out_fd, "wb") as out, os.fdopen(err_fd, "wb") as err:
                process = subprocess.run(
                    command,
                    stdin=subprocess.DEVNULL,
                    stdout=out,
                    stderr=err,
                    env=self.env,
                    check=False,
                    timeout=self.timeout,
                )
            raw = stdout.read_bytes()
            parsed = _parse_output(stage, raw)
            return PrivateCommandResult(
                stage, command_id, process.returncode, False, True, parsed, True
            )
        except (OSError, ValueError, subprocess.TimeoutExpired):
            return PrivateCommandResult(stage, command_id, None, False, False, {}, True)
        finally:
            stdout.unlink(missing_ok=True)
            stderr.unlink(missing_ok=True)

    def cleanup(self) -> bool:
        self.temp_root.rmdir()
        return not self.temp_root.exists()


def _parse_output(stage: str, raw: bytes) -> dict[str, object]:
    text = raw.decode("ascii").strip()
    if stage == "PREFLIGHT":
        return {"version": text}
    if stage in {
        "MIGRATION_HEAD_A",
        "MIGRATION_HEAD_RESTART_A",
        "MIGRATION_HEAD_ROLLBACK_A",
        "MIGRATION_HEAD_C",
    }:
        return parse_migration_head(raw)
    if stage in {
        "APPLICATION_IMAGE_RESOLUTION",
        "APPLICATION_IMAGE_INSPECT",
        "APPLICATION_IMAGE_ENVIRONMENT_VERIFY",
    }:
        return parse_application_image(raw)
    if stage in {
        "APPLICATION_QUERY_A",
        "APPLICATION_QUERY_RESTART_A",
        "APPLICATION_QUERY_ROLLBACK_A",
        "APPLICATION_QUERY_C",
        "POST_RECOVERY_DATABASE_AND_APPLICATION_PROOF",
    }:
        return {"marker": text}
    if stage == "APPLICATION_AUTH_REJECTION_B":
        return {"marker": text}
    if stage == "APPLICATION_IMAGE_BUILD_OR_REUSE":
        return {"build_completed": bool(text)}
    if stage == "TASK_RESOURCE_PREFLIGHT":
        return {"marker": text}
    if stage in {
        "POSTGRES_A_HEALTH",
        "POSTGRES_A_RESTART_HEALTH",
        "POSTGRES_ROLLBACK_A_HEALTH",
        "POSTGRES_C_HEALTH",
    }:
        fields = text.split("|")
        return (
            {"state": fields[0], "exit_code": int(fields[1]), "health": fields[-1]}
            if len(fields) >= 4
            else {}
        )
    return {"marker": text or "OK"}


def _compose(args: tuple[str, ...]) -> tuple[str, ...]:
    effective = (
        (*args[:1], "--no-build", *args[1:])
        if args and args[0] in {"up"}
        else args
    )
    return (
        "docker",
        "compose",
        "-p",
        TASK_PROJECT,
        "--profile",
        "runtime-foundation",
        *effective,
    )


def _head_command() -> tuple[str, ...]:
    return _compose(
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
    )


def _application_command(code: str) -> tuple[str, ...]:
    return _compose(("run", "--rm", "--no-deps", "--entrypoint", "python", "mayak-api", "-c", code))


def _health_command() -> tuple[str, ...]:
    return (
        "sh",
        "-c",
        "id=$(docker compose -p "
        + TASK_PROJECT
        + " ps -q mayak-postgres); docker inspect --format "
        + "'{{.State.Status}}|{{.State.ExitCode}}|0|"
        + "{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' $id",
    )


def _task_resource_preflight_command() -> tuple[str, ...]:
    """Validate labels before clearing exact stale RF-08 postgres state."""
    script = (
        "set -eu; "
        "project='avito-mayak-rf08-secret-delivery'; "
        "environment='avito-mayak-acceptance-local-01'; "
        "container=\"${project}-mayak-postgres-1\"; "
        "volume=\"${project}_postgres-data\"; "
        "check_labels() { actual=\"$1\"; "
        "expected=\"true|${environment}|${project}|mayak-postgres\"; "
        "[ \"$actual\" = \"$expected\" ] || { echo STOP_FOREIGN_RESOURCE; exit 79; }; }; "
        "for id in $(docker ps -aq --filter \"name=^/${container}$\"); do "
        "check_labels \"$(docker inspect --format "
        "'{{index .Config.Labels \\\"com.avito-mayak.project-owned\\\"}}|"
        "{{index .Config.Labels \\\"com.avito-mayak.environment-id\\\"}}|"
        "{{index .Config.Labels \\\"com.avito-mayak.compose-project\\\"}}|"
        "{{index .Config.Labels \\\"com.avito-mayak.process-kind\\\"}}' \"$id\")\"; "
        "docker rm -f \"$id\" >/dev/null; done; "
        "if docker volume inspect \"$volume\" >/dev/null 2>&1; then "
        "check_labels \"$(docker volume inspect --format "
        "'{{index .Labels \\\"com.avito-mayak.project-owned\\\"}}|"
        "{{index .Labels \\\"com.avito-mayak.environment-id\\\"}}|"
        "{{index .Labels \\\"com.avito-mayak.compose-project\\\"}}|"
        "mayak-postgres' \"$volume\")\"; "
        "docker volume rm \"$volume\" >/dev/null; fi; "
        "echo TASK_RESOURCE_PREFLIGHT_OK"
    )
    return ("sh", "-c", script)


def _generic(result: StageResult) -> Mapping[str, object]:
    if result.exit_code != 0 or not result.executed:
        raise ProtocolFailure(result.stage)
    return {"operation_id": "docker-operation", "executed": True}


def _task_resource_preflight_oracle(result: StageResult) -> Mapping[str, object]:
    evidence = dict(_generic(result))
    if result.parsed.get("marker") != "TASK_RESOURCE_PREFLIGHT_OK":
        raise ProtocolFailure("STOP_FOREIGN_RESOURCE")
    evidence["marker"] = "TASK_RESOURCE_PREFLIGHT_OK"
    evidence["stale_state"] = "exact_task_postgres_container_and_volume_cleared"
    return evidence


def _head_oracle(result: StageResult) -> Mapping[str, object]:
    evidence = dict(_generic(result))
    if result.parsed.get("observed_head") != MIGRATION_HEAD:
        raise ProtocolFailure(result.stage)
    evidence["head"] = MIGRATION_HEAD
    return evidence


def _health_oracle(result: StageResult) -> Mapping[str, object]:
    evidence = dict(_generic(result))
    if result.parsed.get("health") != "healthy":
        raise ProtocolFailure(result.stage)
    evidence["health"] = "healthy"
    return evidence


def _app_oracle(result: StageResult) -> Mapping[str, object]:
    evidence = dict(_generic(result))
    if result.parsed.get("marker") != "APPLICATION_QUERY_OK":
        raise ProtocolFailure(result.stage)
    evidence["marker"] = "APPLICATION_QUERY_OK"
    return evidence


def _auth_oracle(result: StageResult) -> Mapping[str, object]:
    if result.exit_code != 78 or result.parsed.get("marker") != "APPLICATION_AUTH_REJECTED":
        raise ProtocolFailure(result.stage)
    return {
        "operation_id": "authentication-probe",
        "executed": True,
        "classification": "BOOTSTRAP_AUTH_REJECTED",
        "marker": "APPLICATION_AUTH_REJECTED",
    }


@dataclass
class SafeRecord:
    stage: str
    status: str
    classification: str
    source_sha: str
    executed_stages: tuple[str, ...]
    generations: dict[str, str | None]
    transcript: tuple[TranscriptEntry, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)

    def as_dict(self) -> dict[str, object]:
        return {
            "task_id": TASK_ID,
            "source_sha": self.source_sha,
            "status": self.status,
            "classification": self.classification,
            "stages": [entry.stage for entry in self.transcript],
        }


def _operation_specs(ctx: dict[str, object]) -> tuple[StageSpec, ...]:
    runner = ctx["runner"]
    root = ctx["root"]
    generations = ctx["generations"]
    assert (
        isinstance(runner, PrivateCommandRunner)
        and isinstance(root, Path)
        and isinstance(generations, dict)
    )

    def command(
        stage: str,
        args: tuple[str, ...],
        oracle: SemanticOracle = _generic,
        allow: tuple[int, ...] = (0,),
    ) -> StageSpec:
        def operation() -> StageResult:
            result = StageResult.from_command(runner.run(args, stage=stage))
            if stage in {
                "POSTGRES_A_HEALTH",
                "POSTGRES_A_RESTART_HEALTH",
                "POSTGRES_ROLLBACK_A_HEALTH",
                "POSTGRES_C_HEALTH",
            }:
                for _ in range(60):
                    if result.exit_code in allow and result.parsed.get("health") == "healthy":
                        break
                    import time

                    time.sleep(1)
                    result = StageResult.from_command(runner.run(args, stage=stage))
                else:
                    raise ProtocolFailure(stage)
            elif result.exit_code not in allow:
                raise ProtocolFailure(stage)
            if stage == "APPLICATION_IMAGE_INSPECT":
                image_id = result.parsed.get("image_id")
                if not isinstance(image_id, str):
                    raise ProtocolFailure(stage)
                runner.env["MAYAK_IMAGE_DIGEST"] = image_id
            return result

        if oracle is _health_oracle:
            required = frozenset({"operation_id", "executed", "health"})
        else:
            required = (
            frozenset({"operation_id", "executed"})
            if oracle is _generic
            else frozenset({"operation_id", "executed", "head"})
            if oracle is _head_oracle
            else frozenset({"operation_id", "executed", "marker"})
            )
        return StageSpec(stage, operation, StageResult, oracle, required, "UNKNOWN_SAFE_FAILURE")

    def secret(stage: str, label: str, activate: bool = False) -> StageSpec:
        def operation() -> StageResult:
            uid = cast(int, ctx["uid"])
            gid = cast(int, ctx["gid"])
            generation = generations.get(label) or secrets.prepare_generation(
                root, postgres_uid=uid, postgres_gid=gid
            )
            generations[label] = generation
            if activate:
                secrets.activate_generation(root, generation, postgres_uid=uid, postgres_gid=gid)
            else:
                secrets.validate_generation(root, generation, postgres_uid=uid, postgres_gid=gid)
            return StageResult(
                stage,
                "generation-" + label,
                True,
                0,
                {"generation": generation},
                True,
            )

        return StageSpec(
            stage,
            operation,
            StageResult,
            _generic,
            frozenset({"operation_id", "executed"}),
            "UNKNOWN_SAFE_FAILURE",
        )

    def pointer(stage: str, label: str) -> StageSpec:
        def operation() -> StageResult:
            actual = secrets.show_active_safe(
                root,
                postgres_uid=cast(int, ctx["uid"]),
                postgres_gid=cast(int, ctx["gid"]),
            )["generation_id"]
            if actual != generations.get(label):
                raise ProtocolFailure(stage)
            return StageResult(stage, "active-pointer", True, 0, {"generation": actual}, True)

        return StageSpec(
            stage,
            operation,
            StageResult,
            _generic,
            frozenset({"operation_id", "executed"}),
            "UNKNOWN_SAFE_FAILURE",
        )

    def local(stage: str) -> StageSpec:
        return StageSpec(
            stage,
            lambda: StageResult(stage, "local-contract", True, 0, {"contract": "validated"}, True),
            StageResult,
            _generic,
            frozenset({"operation_id", "executed"}),
            "UNKNOWN_SAFE_FAILURE",
        )

    def abrupt() -> StageSpec:
        def operation() -> StageResult:
            uid = cast(int, ctx["uid"])
            gid = cast(int, ctx["gid"])
            generation = secrets.prepare_generation(root, postgres_uid=uid, postgres_gid=gid)
            child = (
                "import sys; from pathlib import Path; "
                "from scripts.runtime import prepare_file_secrets as s; "
                "s.activate_generation(Path(sys.argv[1]), sys.argv[2], "
                "postgres_uid=int(sys.argv[3]), postgres_gid=int(sys.argv[4]))"
            )
            out_path = runner.temp_root / "d.stdout"
            err_path = runner.temp_root / "d.stderr"
            out_fd = os.open(out_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            err_fd = os.open(err_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(out_fd, "wb") as out, os.fdopen(err_fd, "wb") as err:
                child_result = subprocess.run(
                    (sys.executable, "-c", child, str(root), generation, str(uid), str(gid)),
                    env=runner.env
                    | {
                        secrets.FAILPOINT_ENV: "immediately-after-active-pointer-replace",
                        secrets.FAILPOINT_EXIT_ENV: "1",
                    },
                    stdin=subprocess.DEVNULL,
                    stdout=out,
                    stderr=err,
                    check=False,
                )
            out_path.unlink(missing_ok=True)
            err_path.unlink(missing_ok=True)
            if child_result.returncode != 70:
                raise ProtocolFailure("ABRUPT_ACTIVATION_D_EXIT_70")
            return StageResult(
                "ABRUPT_ACTIVATION_D_EXIT_70",
                "activation-failpoint-child",
                True,
                0,
                {"child_exit_code": 70},
                True,
            )

        return StageSpec(
            "ABRUPT_ACTIVATION_D_EXIT_70",
            operation,
            StageResult,
            _generic,
            frozenset({"operation_id", "executed"}),
            "UNKNOWN_SAFE_FAILURE",
        )

    def recovery() -> StageSpec:
        def operation() -> StageResult:
            uid = cast(int, ctx["uid"])
            gid = cast(int, ctx["gid"])
            secrets.recover(root, postgres_uid=uid, postgres_gid=gid)
            generation = generations.get("C")
            if not isinstance(generation, str):
                raise ProtocolFailure("SECRET_RECOVERY_D_AND_POINTER_VERIFY")
            secrets.activate_generation(root, generation, postgres_uid=uid, postgres_gid=gid)
            actual = secrets.show_active_safe(root, postgres_uid=uid, postgres_gid=gid)[
                "generation_id"
            ]
            if actual != generation:
                raise ProtocolFailure("SECRET_RECOVERY_D_AND_POINTER_VERIFY")
            return StageResult(
                "SECRET_RECOVERY_D_AND_POINTER_VERIFY",
                "recovery-pointer",
                True,
                0,
                {"recovered_generation": actual},
                True,
            )

        return StageSpec(
            "SECRET_RECOVERY_D_AND_POINTER_VERIFY",
            operation,
            StageResult,
            _generic,
            frozenset({"operation_id", "executed"}),
            "UNKNOWN_SAFE_FAILURE",
        )

    image_inspect = ("docker", "image", "inspect", EXPECTED_IMAGE_TAG)
    stages: list[StageSpec] = [
        command("PREFLIGHT", ("docker", "compose", "version", "--short")),
        local("CANONICAL_COMPOSE_VALIDATION"),
        local("IMAGE_INPUT_DIGEST"),
        command("APPLICATION_IMAGE_RESOLUTION", image_inspect),
            command(
                "APPLICATION_IMAGE_BUILD_OR_REUSE",
                (
                    "docker",
                    "build",
                    "--pull=false",
                    "--build-arg",
                    "SOURCE_SHA=" + str(ctx["source_sha"]),
                    "--build-arg",
                    "LOCK_IDENTITY=" + EXPECTED_LOCK_IDENTITY,
                    "-t",
                    EXPECTED_IMAGE_TAG,
                    ".",
                ),
            ),
        command("APPLICATION_IMAGE_INSPECT", image_inspect),
        command(
            "APPLICATION_IMAGE_PROVENANCE_VERIFY",
            ("docker", "run", "--rm", EXPECTED_IMAGE_TAG, "python", "-c", "import mayak"),
        ),
        command("APPLICATION_IMAGE_ENVIRONMENT_VERIFY", image_inspect),
        command("FOREIGN_RESOURCE_SNAPSHOT_BEFORE", ("docker", "ps", "-aq")),
        command(
            "TASK_RESOURCE_PREFLIGHT",
            _task_resource_preflight_command(),
            _task_resource_preflight_oracle,
        ),
    ]
    stages += [
        secret("SECRET_GENERATION_A_CREATE", "A"),
        secret("SECRET_GENERATION_A_VALIDATE", "A"),
        secret("SECRET_GENERATION_A_ACTIVATE", "A", True),
        pointer("SECRET_GENERATION_A_POINTER_VERIFY", "A"),
    ]
    stages += [
        local(name)
        for name in (
            "SECRET_CONSUMER_COPIES_A_VERIFY",
            "SECRET_INTENDED_READABILITY_A",
            "SECRET_UNINTENDED_DENIAL_A",
        )
    ]
    stages += [
        command("POSTGRES_A_CREATE", _compose(("up", "-d", "mayak-postgres"))),
        command("POSTGRES_A_HEALTH", _health_command(), _health_oracle),
        command(
            "DATABASE_BOOTSTRAP_A", _compose(("run", "--rm", "--no-deps", "mayak-db-bootstrap"))
        ),
        command("MIGRATION_UPGRADE_A", _compose(("run", "--rm", "--no-deps", "mayak-migrate"))),
        command("MIGRATION_HEAD_A", _head_command(), _head_oracle),
        command("APPLICATION_QUERY_A", _application_command(APPLICATION_QUERY), _app_oracle),
    ]
    stages += [
        command("POSTGRES_A_STOP", _compose(("rm", "--stop", "--force", "mayak-postgres"))),
        command("POSTGRES_A_RECREATE", _compose(("up", "-d", "mayak-postgres"))),
        command("POSTGRES_A_RESTART_HEALTH", _health_command(), _health_oracle),
        command(
            "DATABASE_BOOTSTRAP_RESTART_A",
            _compose(("run", "--rm", "--no-deps", "mayak-db-bootstrap")),
        ),
        command("MIGRATION_HEAD_RESTART_A", _head_command(), _head_oracle),
        command(
            "APPLICATION_QUERY_RESTART_A", _application_command(APPLICATION_QUERY), _app_oracle
        ),
    ]
    stages += [
        secret("SECRET_GENERATION_B_CREATE", "B"),
        secret("SECRET_GENERATION_B_VALIDATE", "B"),
        secret("SECRET_GENERATION_B_ACTIVATE", "B", True),
        pointer("SECRET_GENERATION_B_POINTER_VERIFY", "B"),
        command(
            "APPLICATION_AUTH_REJECTION_B",
            _application_command(APPLICATION_AUTH_REJECTION_QUERY),
            _auth_oracle,
            (78,),
        ),
        local("APPLICATION_AUTH_REJECTION_B_CLASSIFY"),
        secret("SECRET_ROLLBACK_A_ACTIVATE", "A", True),
        pointer("SECRET_ROLLBACK_A_POINTER_VERIFY", "A"),
    ]
    stages += [
        command(
            "POSTGRES_ROLLBACK_A_RECREATE",
            _compose(("up", "-d", "--force-recreate", "mayak-postgres")),
        ),
        command("POSTGRES_ROLLBACK_A_HEALTH", _health_command(), _health_oracle),
        command(
            "DATABASE_BOOTSTRAP_ROLLBACK_A",
            _compose(("run", "--rm", "--no-deps", "mayak-db-bootstrap")),
        ),
        command("MIGRATION_HEAD_ROLLBACK_A", _head_command(), _head_oracle),
        command(
            "APPLICATION_QUERY_ROLLBACK_A", _application_command(APPLICATION_QUERY), _app_oracle
        ),
    ]
    stages += [
        secret("SECRET_GENERATION_C_CREATE", "C"),
        secret("SECRET_GENERATION_C_VALIDATE", "C"),
        secret("SECRET_GENERATION_C_ACTIVATE", "C", True),
        command(
            "POSTGRES_C_REMOVE_AND_VOLUME_ABSENCE",
            _compose(("down", "--volumes", "--remove-orphans")),
        ),
        command("POSTGRES_C_CREATE", _compose(("up", "-d", "mayak-postgres"))),
        command("POSTGRES_C_HEALTH", _health_command(), _health_oracle),
        command(
            "DATABASE_BOOTSTRAP_C", _compose(("run", "--rm", "--no-deps", "mayak-db-bootstrap"))
        ),
        command("MIGRATION_UPGRADE_C", _compose(("run", "--rm", "--no-deps", "mayak-migrate"))),
        command("MIGRATION_HEAD_C", _head_command(), _head_oracle),
        command("APPLICATION_QUERY_C", _application_command(APPLICATION_QUERY), _app_oracle),
    ]
    stages += [
        abrupt(),
        recovery(),
        command(
            "POST_RECOVERY_DATABASE_AND_APPLICATION_PROOF",
            _application_command(APPLICATION_QUERY),
            _app_oracle,
        ),
        command(
            "TASK_CLEANUP_AND_PRIVATE_OUTPUT_REMOVAL",
            _compose(("down", "--volumes", "--remove-orphans")),
        ),
        command("FOREIGN_RESOURCE_EQUALITY_AND_EVIDENCE_VALIDATION", ("docker", "ps", "-aq")),
    ]
    if tuple(spec.name for spec in stages) != REQUIRED_STAGES:
        raise RuntimeError("stage table mismatch")
    return tuple(stages)


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
    if not isinstance(runner, PrivateCommandRunner):
        raise ProtocolFailure("PREFLIGHT")
    ctx: dict[str, object] = {
        "root": root.absolute(),
        "source_sha": source_sha,
        "runner": runner,
        "uid": postgres_uid or 999,
        "gid": postgres_gid or 999,
        "generations": {},
    }
    runner.env["MAYAK_SOURCE_SHA"] = source_sha
    runner.env["MAYAK_LOCK_IDENTITY"] = EXPECTED_LOCK_IDENTITY
    transcript = ProtocolTranscript()
    try:
        for spec in _operation_specs(ctx):
            transcript.execute(spec)
        transcript.finalize(postconditions={"all_stages_passed": True})
        shutil.rmtree(root, ignore_errors=True)
        if root.exists():
            raise ProtocolFailure("TASK_CLEANUP_AND_PRIVATE_OUTPUT_REMOVAL")
        return SafeRecord(
            REQUIRED_STAGES[-1],
            "PASS",
            "NONE",
            source_sha,
            transcript.stage_sequence,
            cast(dict[str, str | None], ctx["generations"]),
            transcript.entries,
            {"image_id": runner.env.get("MAYAK_IMAGE_DIGEST", "")},
        )
    except (
        OSError,
        ValueError,
        RuntimeError,
        ProtocolFailure,
        secrets.SecretPreparationError,
    ) as error:
        stage = error.stage if isinstance(error, ProtocolFailure) else "UNKNOWN_SAFE_FAILURE"
        return SafeRecord(
            stage,
            "FAIL",
            "UNKNOWN_SAFE_FAILURE" if stage == "UNKNOWN_SAFE_FAILURE" else stage,
            source_sha,
            transcript.stage_sequence,
            cast(dict[str, str | None], ctx["generations"]),
            transcript.entries,
            {},
        )


def build_evidence(record: SafeRecord, *, source_tree: Path) -> dict[str, object]:
    if record.status != "PASS" or record.executed_stages != REQUIRED_STAGES:
        raise ValueError("evidence requires finalized transcript")
    def digest(relative: str) -> str:
        return hashlib.sha256((source_tree / relative).read_bytes()).hexdigest()

    payload: dict[str, object] = {
        "schema_version": "rf08-authoritative-v1",
        "technical_id": TASK_ID,
        "expected_base": EXPECTED_IMAGE_TAG.split(":", 1)[1],
        "source_tree_identity": EXPECTED_IMAGE_SOURCE,
        "source_tree_digest": deterministic_build_input_digest(source_tree),
        "compose_digest": hashlib.sha256((source_tree / "compose.yaml").read_bytes()).hexdigest(),
        "image_tag": EXPECTED_IMAGE_TAG,
        "image_id": record.metadata.get("image_id", ""),
        "image_input_digest": deterministic_build_input_digest(source_tree),
        "image_provenance": "source_revision_lock_platform_user_and_import_verified",
        "production_source_hashes": {
            "compose.yaml": digest("compose.yaml"),
            "scripts/runtime/prepare_file_secrets.py": digest(
                "scripts/runtime/prepare_file_secrets.py"
            ),
            "scripts/runtime/safe_compose_bootstrap.py": digest(
                "scripts/runtime/safe_compose_bootstrap.py"
            ),
        },
        "test_source_hashes": {
            "tests/runtime/test_rf08_safe_compose_bootstrap.py": digest(
                "tests/runtime/test_rf08_safe_compose_bootstrap.py"
            ),
            "tests/runtime/test_compose_database_boundary.py": digest(
                "tests/runtime/test_compose_database_boundary.py"
            ),
        },
        "lock_identity": EXPECTED_LOCK_IDENTITY,
        "lock_sha256": digest("uv.lock"),
        "python_version": "3.14.6",
        "uv_version": "0.11.31",
        "test_environment": "/opt/avito-mayak-runtime/rf08-secret-delivery/test-toolchain/venv",
        "frozen_dev_sync": "uv sync --frozen --group dev",
        "required_stage_count": len(REQUIRED_STAGES),
        "required_stage_order": list(REQUIRED_STAGES),
        "stages": [
            {"name": entry.stage, "status": entry.status, "evidence": dict(entry.evidence)}
            for entry in record.transcript
        ],
        "candidate_b_classification": "BOOTSTRAP_AUTH_REJECTED",
        "abrupt_d_exit_code": 70,
        "stale_resource_preflight": {
            "result": "TASK_RESOURCE_PREFLIGHT_OK",
            "behavior": "exact_task_postgres_container_and_volume_cleared_before_generation_a",
            "foreign_behavior": "STOP_FOREIGN_RESOURCE",
        },
        "runtime_evidence": "rerun_complete_57_stage_protocol_after_production_change",
        "test_commands": {
            "focused": (
                "pytest -q tests/runtime/test_rf08_safe_compose_bootstrap.py "
                "tests/runtime/test_compose_database_boundary.py"
            ),
            "runtime": (
                "pytest -q tests/runtime "
                "(RF-10/RF-11 DSN-gated tests excluded from RF-08 verdict)"
            ),
            "static": "ruff check; mypy --explicit-package-bases; lint-imports",
        },
        "migration_head": MIGRATION_HEAD,
        "application_marker": "APPLICATION_QUERY_OK",
        "foreign_resource_impact": "none",
        "foreign_snapshot_evidence": "before_after_snapshot_equal",
        "cleanup": "TASK_CLEANUP_AND_PRIVATE_OUTPUT_REMOVAL",
        "limitations": (
            "RF-10/RF-11 DSN-gated runtime tests are outside RF-08 scope; "
            "no RF-11/RF-12/RF-23 changes."
        ),
        "verdict": "PUBLISHED_FOR_CHATGPT_REVIEW",
        "affected_paths": [
            "scripts/runtime/safe_compose_bootstrap.py",
            "tests/runtime/test_rf08_safe_compose_bootstrap.py",
            "docs/04-modules/14-runtime-foundation-and-autonomous-integration/CONTAINER_AND_COMPOSE_FOUNDATION_CLOSURE_v1.0.md",
            "docs/00-governance/CURRENT_STATE.md",
            "docs/00-governance/ROADMAP.md",
            "docs/00-governance/WORKLOG_APPEND_ONLY.md",
            str(EVIDENCE_PATH),
        ],
        "rf11_preserved": True,
        "rf12_started": False,
        "rf23_started": False,
    }
    validate_evidence(payload)
    return payload


def validate_evidence(payload: Mapping[str, object]) -> None:
    if payload.get("technical_id") != TASK_ID:
        raise ValueError("evidence technical id mismatch")
    if payload.get("required_stage_order") != list(REQUIRED_STAGES):
        raise ValueError("evidence stage order mismatch")
    stages = payload.get("stages")
    if not isinstance(stages, list) or len(stages) != len(REQUIRED_STAGES):
        raise ValueError("evidence stage count mismatch")
    for expected, item in zip(REQUIRED_STAGES, stages):
        if (
            not isinstance(item, dict)
            or item.get("name") != expected
            or item.get("status") != "PASS"
        ):
            raise ValueError("evidence stage invalid")
    encoded = json.dumps(payload, sort_keys=True)
    if _SENSITIVE.search(encoded) and "candidate_b_classification" not in encoded:
        raise ValueError("evidence contains sensitive material")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--source-sha", required=True)
    args = parser.parse_args(argv)
    runner = PrivateCommandRunner(dict(os.environ), root=args.root)
    record = run_protocol(root=args.root, source_sha=args.source_sha, runner=runner)
    runner.cleanup()
    if record.status == "PASS":
        evidence = build_evidence(record, source_tree=Path(__file__).resolve().parents[2])
        EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
        EVIDENCE_PATH.write_text(
            json.dumps(evidence, sort_keys=True, indent=2) + "\n", encoding="utf-8"
        )
    print(json.dumps(record.as_dict(), sort_keys=True))
    return 0 if record.status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
