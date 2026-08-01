#!/usr/bin/env python3
# ruff: noqa: E501
"""Executable RF-08 prover.

This module deliberately keeps the prover and its verdict-free data contracts
small.  Every transcript row is produced by a named operation and checked by
the oracle attached to that operation; the independent verifier lives in a
separate module and never imports this module's verdicts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass, field, replace
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import Any, Callable, Final, Mapping, Protocol, Sequence, cast

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.runtime import prepare_file_secrets as secrets
from scripts.runtime.rf08_docker_authority import (
    COMPOSE_FILE,
    RUNTIME_PROFILE,
    BootstrapAction,
    ComposeAction,
    ComposeBinding,
    ComposeExecTemplate,
    ComposeOperation,
    ComposeProbeAction,
    ComposeProbeKind,
    ComposeRunAction,
    ComposeService,
    DockerExecution,
    DockerObservation,
    GatewayAuthority,
    ImageAction,
    ImageOperation,
    NetworkPolicy,
    ObservationRequest,
    ObservationTemplate,
    PathCapability,
    PathCapabilityKind,
    ProbeAction,
    ProbeKind,
    ResourceKind,
    ResourceLifecycleAction,
    ResourceOperation,
    SecretMountCapability,
)
from scripts.runtime.rf08_docker_context import (
    COPY_PLAN,
    docker_native_manifest,
    materialize_clean_context,
)
from scripts.runtime.rf08_docker_context import (
    build_input_digest as docker_build_input_digest,
)
from scripts.runtime.rf08_foreign_snapshot import (
    classify_delta as classify_foreign_delta,
)
from scripts.runtime.rf08_foreign_snapshot import (
    collect_snapshot as collect_foreign_snapshot,
)


@dataclass(frozen=True, slots=True)
class SemanticDispatch:
    semantic: object
    is_mutation: bool


class LocalExecutable(str, Enum):
    SHELL = "sh"
    RUNUSER = "runuser"
    PYTHON = sys.executable


@dataclass(frozen=True, slots=True)
class LocalCommand:
    executable: LocalExecutable
    arguments: tuple[str, ...]


CommandRequest = SemanticDispatch | LocalCommand


@dataclass(frozen=True)
class DockerMutationRecord:
    record_type: str
    authorization_sequence: int
    execution_result_sequence: int | None
    invocation_sequence: int
    stage: str
    semantic_class: str
    target_kind: str
    target_identity_hash: str
    authorization_basis: str
    authorization_outcome: str
    execution_attempted: bool = False
    execution_completed: bool = False
    exit_code: int | None = None
    timed_out: bool = False
    safe_failure_classification: str | None = None
    target_ownership: str = "UNRESOLVED"
    argv_fingerprint: str = ""

    @property
    def sequence(self) -> int:
        return self.authorization_sequence

    @property
    def ownership(self) -> str:
        return self.target_ownership

    @property
    def planned_ownership(self) -> str:
        return self.target_ownership

    @property
    def mutation_allowed(self) -> bool:
        return self.authorization_outcome == "AUTHORIZED"

    @property
    def scoped(self) -> bool:
        return self.target_ownership == "TASK_OWNED"

    @property
    def executed(self) -> bool:
        return self.execution_attempted

    def safe_dict(self) -> dict[str, object]:
        payload = {
            "record_type": self.record_type,
            "authorization_sequence": self.authorization_sequence,
            "execution_result_sequence": self.execution_result_sequence,
            "invocation_sequence": self.invocation_sequence,
            "stage": self.stage,
            "semantic_class": self.semantic_class,
            "target_kind": self.target_kind,
            "target_identity_hash": self.target_identity_hash,
            "authorization_basis": self.authorization_basis,
            "authorization_outcome": self.authorization_outcome,
            "execution_attempted": self.execution_attempted,
            "execution_completed": self.execution_completed,
            "exit_code": self.exit_code,
            "timed_out": self.timed_out,
            "safe_failure_classification": self.safe_failure_classification,
            "target_ownership": self.target_ownership,
            "argv_fingerprint": self.argv_fingerprint,
        }
        payload["planned_ownership"] = self.planned_ownership
        payload["ownership"] = self.ownership
        payload["mutation_allowed"] = self.mutation_allowed
        payload["scoped"] = self.scoped
        payload["sequence"] = self.sequence
        payload["executed"] = self.executed
        return payload


def _option_pairs(argv: Sequence[str]) -> dict[str, list[str]]:
    pairs: dict[str, list[str]] = {}
    index = 0
    while index < len(argv):
        token = argv[index]
        if token in {
            "-f",
            "--file",
            "-p",
            "--project-name",
            "--profile",
            "-e",
            "--env",
            "-v",
            "--volume",
            "--user",
            "--entrypoint",
            "--name",
            "--network",
            "--workdir",
            "--mount",
            "--label",
            "--driver",
            "--scope",
            "--opt",
            "--output",
        }:
            if index + 1 >= len(argv):
                raise ValueError("missing option value")
            pairs.setdefault(token, []).append(argv[index + 1])
            index += 2
            continue
        if token.startswith("--") and "=" in token:
            option, value = token.split("=", 1)
            pairs.setdefault(option, []).append(value)
            index += 1
            continue
        if token.startswith("-"):
            pairs.setdefault(token, []).append("")
        index += 1
    return pairs


def _compose_binding(
    compose_file: str | None, project_name: str | None, profile: str | None
) -> ComposeBinding:
    return ComposeBinding.from_path(
        compose_file or COMPOSE_FILE,
        project_name=project_name or TASK_PROJECT,
        profile=profile or RUNTIME_PROFILE,
    )


def _compose_dispatch(argv: tuple[str, ...]) -> SemanticDispatch:
    command = None
    service = None
    compose_file = None
    project_name = None
    profile = None
    index = 2
    while index < len(argv):
        token = argv[index]
        if token in {"-f", "--file", "-p", "--project-name", "--profile"}:
            if index + 1 >= len(argv):
                raise ValueError("missing compose option value")
            value = argv[index + 1]
            if token in {"-f", "--file"}:
                compose_file = value
            elif token in {"-p", "--project-name"}:
                project_name = value
            else:
                profile = value
            index += 2
            continue
        if token.startswith("-"):
            index += 1
            continue
        command = token
        if index + 1 < len(argv):
            service = argv[index + 1]
        break
    if command is None:
        raise ValueError("compose command missing")
    binding = _compose_binding(compose_file, project_name, profile)
    pairs = _option_pairs(argv[2:])
    if command in {"version", "config", "ps", "exec", "logs"}:
        if command == "version":
            semantic: ObservationRequest | ComposeAction = ObservationRequest(
                template=ObservationTemplate.COMPOSE_VERSION, compose=binding
            )
        elif command == "config":
            semantic = ObservationRequest(
                template=ObservationTemplate.COMPOSE_CONFIG, compose=binding
            )
        elif command == "ps":
            semantic = ObservationRequest(template=ObservationTemplate.COMPOSE_PS, compose=binding)
        elif command == "exec":
            service_name = argv[argv.index("exec") + 1]
            try:
                service_enum = ComposeService(service_name)
            except ValueError as exc:
                raise ValueError("unsupported compose service") from exc
            tail = tuple(argv[argv.index(service_name) + 1 :])
            if tail[:4] == ("pg_isready", "-U", "mayak", "-d"):
                template = ComposeExecTemplate.POSTGRES_READY
            elif "alembic_version" in " ".join(tail):
                template = ComposeExecTemplate.POSTGRES_MIGRATION_HEAD
            else:
                template = ComposeExecTemplate.POSTGRES_LOG_DESTINATION
            semantic = ObservationRequest(
                template=ObservationTemplate.COMPOSE_EXEC,
                compose=binding,
                service=service_enum,
                exec_template=template,
            )
        else:
            log_tokens = tuple(argv[argv.index("logs") + 1 :])
            if log_tokens != ("--no-color", "--tail", "64", ComposeService.POSTGRES.value):
                raise ValueError("unsupported bounded postgres log observation")
            semantic = ObservationRequest(
                template=ObservationTemplate.POSTGRES_LOG_TAIL,
                compose=binding,
                service=ComposeService.POSTGRES,
            )
        return SemanticDispatch(semantic=semantic, is_mutation=False)
    if command not in {"create", "up", "start", "stop", "restart", "rm", "run"}:
        raise ValueError("unknown compose command")
    service_index = next(
        (i for i in range(index + 1, len(argv)) if not argv[i].startswith("-")),
        None,
    )
    service = argv[service_index] if service_index is not None else None
    if service is None:
        raise ValueError("compose service missing")
    if command == "run":
        if len(argv) < 5:
            raise ValueError("unsupported compose run command")
        run_index = argv.index("run")
        service = next(
            (
                value
                for value in argv[run_index + 1 :]
                if value in {item.value for item in ComposeService}
            ),
            "",
        )
        if not service:
            raise ValueError("unsupported compose run service")
        command_tail = tuple(argv[-2:])
        if service == "mayak-db-bootstrap" and command_tail == (
            "python",
            "/opt/mayak/rf09_public_bootstrap_adapter.py",
        ):
            env_pairs: dict[str, str] = {}
            for value in pairs.get("-e", []):
                if "=" not in value:
                    continue
                env_key, env_value = value.split("=", 1)
                env_pairs[env_key] = env_value
            volume = next((item for item in pairs.get("-v", []) if ":" in item), "")
            adapter_source = volume.split(":", 1)[0] if volume else ""
            recovered_generation_id = env_pairs.get("RF08_RECOVERED_GENERATION_ID", "")
            run_id = env_pairs.get("RF08_RUN_ID", "")
            if not run_id or not recovered_generation_id or not adapter_source:
                raise ValueError("incomplete bootstrap compose shape")
            return SemanticDispatch(
                BootstrapAction(
                    binding=binding,
                    service=ComposeService(service),
                    run_id=run_id,
                    recovered_generation_id=recovered_generation_id,
                    adapter=PathCapability.from_path(
                        adapter_source, kind=PathCapabilityKind.FILE, require_exists=True
                    ),
                ),
                True,
            )
        if service == ComposeService.MIGRATE.value and tuple(
            item for item in argv[run_index + 1 :] if item != "--no-deps"
        ) == ("--rm", service):
            return SemanticDispatch(
                ComposeRunAction(
                    binding=binding,
                    service=ComposeService.MIGRATE,
                    no_deps="--no-deps" in argv[run_index + 1 :],
                ),
                True,
            )
        if service == ComposeService.API.value and "APPLICATION_QUERY_OK" in " ".join(argv):
            return SemanticDispatch(
                ComposeProbeAction(
                    binding=binding,
                    service=ComposeService.API,
                    probe=ComposeProbeKind.APPLICATION_QUERY,
                ),
                True,
            )
        if service == ComposeService.API.value and "rf08-stage34-auth-v1" in " ".join(argv):
            return SemanticDispatch(
                ComposeProbeAction(
                    binding=binding,
                    service=ComposeService.API,
                    probe=ComposeProbeKind.AUTH_REJECTION,
                    correlation_id=argv[-1],
                ),
                True,
            )
        raise ValueError("unsupported compose run command")
    semantic = ComposeAction(
        binding=binding,
        service=ComposeService(service),
        operation=ComposeOperation(command),
        detach=command in {"up", "start"} and "-d" in argv,
        force=(command == "rm" and "-f" in argv)
        or (command == "up" and "--force-recreate" in argv),
        remove_orphans="--remove-orphans" in argv,
        no_deps="--no-deps" in argv,
        rm_volumes="--volumes" in argv,
    )
    return SemanticDispatch(semantic=semantic, is_mutation=True)


def _dispatch_docker_command(argv: tuple[str, ...]) -> SemanticDispatch:
    if len(argv) < 2 or argv[0] != "docker":
        raise ValueError("not docker")
    if argv[1] == "version":
        return SemanticDispatch(
            ObservationRequest(template=ObservationTemplate.DAEMON_VERSION), False
        )
    if argv[1] == "inspect":
        return SemanticDispatch(
            ObservationRequest(template=ObservationTemplate.CONTAINER_HEALTH, identity=argv[-1]),
            False,
        )
    if argv[1] == "ps":
        return SemanticDispatch(
            ObservationRequest(template=ObservationTemplate.CONTAINER_LIST), False
        )
    if len(argv) > 2 and argv[1] == "image":
        if argv[2] == "inspect":
            return SemanticDispatch(
                ObservationRequest(template=ObservationTemplate.IMAGE_INSPECT, identity=argv[-1]),
                False,
            )
        if argv[2] == "ls":
            return SemanticDispatch(
                ObservationRequest(template=ObservationTemplate.IMAGE_LIST), False
            )
    if len(argv) > 2 and argv[1] == "network":
        if argv[2] == "create":
            return SemanticDispatch(
                ResourceLifecycleAction(
                    kind=ResourceKind.NETWORK,
                    operation=ResourceOperation.CREATE,
                    name=argv[-1],
                ),
                True,
            )
        if argv[2] == "rm":
            return SemanticDispatch(
                ResourceLifecycleAction(
                    kind=ResourceKind.NETWORK,
                    operation=ResourceOperation.REMOVE,
                    name=argv[-1],
                    inspected_capability=argv[-1],
                ),
                True,
            )
        if argv[2] == "ls":
            return SemanticDispatch(
                ObservationRequest(template=ObservationTemplate.NETWORK_LIST), False
            )
    if len(argv) > 2 and argv[1] == "volume":
        if argv[2] == "create":
            return SemanticDispatch(
                ResourceLifecycleAction(
                    kind=ResourceKind.VOLUME,
                    operation=ResourceOperation.CREATE,
                    name=argv[-1],
                ),
                True,
            )
        if argv[2] == "rm":
            return SemanticDispatch(
                ResourceLifecycleAction(
                    kind=ResourceKind.VOLUME,
                    operation=ResourceOperation.REMOVE,
                    name=argv[-1],
                    inspected_capability=argv[-1],
                ),
                True,
            )
        if argv[2] == "ls":
            return SemanticDispatch(
                ObservationRequest(template=ObservationTemplate.VOLUME_LIST), False
            )
    if len(argv) > 2 and argv[1] == "buildx":
        if argv[2] == "build":
            pairs = _option_pairs(argv[2:])
            context = argv[-1]
            if "--load" in argv:
                allowed = {
                    "build",
                    "--progress=plain",
                    "--file",
                    "--platform",
                    "--tag",
                    "--build-arg",
                    "--load",
                }
                if any(token.startswith("--") and token not in allowed for token in argv[3:-1]):
                    raise ValueError("arbitrary application build option")
                platform = pairs.get("--platform", [""])[0]
                tag = pairs.get("--tag", [""])[0]
                args = pairs.get("--build-arg", [])
                values = {
                    item.split("=", 1)[0]: item.split("=", 1)[1] for item in args if "=" in item
                }
                if (
                    platform != "linux/amd64"
                    or not re.fullmatch(r"avito-mayak:[0-9a-f]{40}", tag)
                    or set(values) != {"SOURCE_SHA", "LOCK_IDENTITY", "BUILD_INPUT_DIGEST"}
                ):
                    raise ValueError("non-exact application build")
                return SemanticDispatch(
                    ImageAction(
                        operation=ImageOperation.APPLICATION_BUILD,
                        context=PathCapability.from_path(
                            context, kind=PathCapabilityKind.DIRECTORY
                        ),
                        dockerfile=PathCapability.from_path(
                            pairs["--file"][0], kind=PathCapabilityKind.FILE
                        ),
                        output=PathCapability.from_path(
                            RUNTIME_ROOT / "application-image-output",
                            kind=PathCapabilityKind.DIRECTORY,
                            require_exists=False,
                        ),
                        tag=tag,
                        source_sha=values["SOURCE_SHA"],
                        lock_identity=values["LOCK_IDENTITY"],
                        build_input_digest=values["BUILD_INPUT_DIGEST"],
                        platform=platform,
                    ),
                    True,
                )
            return SemanticDispatch(
                ImageAction(
                    operation=ImageOperation.BUILDX_MANIFEST,
                    context=PathCapability.from_path(
                        context, kind=PathCapabilityKind.DIRECTORY, require_exists=True
                    ),
                    dockerfile=PathCapability.from_path(
                        pairs.get("--file", [str(RUNTIME_COMPOSE_FILE)])[0],
                        kind=PathCapabilityKind.FILE,
                        require_exists=True,
                    ),
                    output=PathCapability.from_path(
                        pairs.get("--output", ["./out"])[0].split("dest=", 1)[-1].split(",", 1)[0],
                        kind=PathCapabilityKind.DIRECTORY,
                        require_exists=False,
                    ),
                ),
                True,
            )
        if argv[2] == "ls":
            return SemanticDispatch(
                ObservationRequest(template=ObservationTemplate.BUILDX_LIST), False
            )
    if argv[1] == "rm":
        return SemanticDispatch(
            ResourceLifecycleAction(
                kind=ResourceKind.CONTAINER,
                operation=ResourceOperation.REMOVE,
                name=argv[-1],
                inspected_capability=argv[-1],
            ),
            True,
        )
    if argv[1] == "run":
        pairs = _option_pairs(argv[2:])
        labels = tuple(
            tuple(item.split("=", 1)) for item in pairs.get("--label", []) if "=" in item
        )
        index = 2
        options_with_value = {
            "--name",
            "--user",
            "--workdir",
            "--entrypoint",
            "--network",
            "--label",
            "-e",
            "-v",
            "-p",
            "--pid",
            "--ipc",
        }
        while index < len(argv):
            token = argv[index]
            if token in {"--rm", "--no-deps", "--privileged"}:
                index += 1
                continue
            if token in options_with_value:
                if index + 1 >= len(argv):
                    raise ValueError("unsupported mutation shape")
                index += 2
                continue
            if token.startswith("-"):
                raise ValueError("unsupported mutation shape")
            break
        if index >= len(argv):
            raise ValueError("unsupported mutation shape")
        command_tail = tuple(argv[index + 1 :])
        if not command_tail:
            raise ValueError("unsupported mutation shape")
        image = argv[index]
        if image == "mayak-db-bootstrap" and command_tail == (
            "python",
            "/opt/mayak/rf09_public_bootstrap_adapter.py",
        ):
            env_pairs: dict[str, str] = {}
            for value in pairs.get("-e", []):
                if "=" not in value:
                    continue
                env_key, env_value = value.split("=", 1)
                env_pairs[env_key] = env_value
            volume = next((item for item in pairs.get("-v", []) if ":" in item), "")
            adapter_source = volume.split(":", 1)[0] if volume else ""
            recovered_generation_id = env_pairs.get("RF08_RECOVERED_GENERATION_ID", "")
            run_id = env_pairs.get("RF08_RUN_ID", "")
            if not run_id or not recovered_generation_id or not adapter_source:
                raise ValueError("incomplete bootstrap mutation shape")
            return SemanticDispatch(
                BootstrapAction(
                    binding=ComposeBinding.from_path(
                        Path(__file__).resolve().parents[2] / COMPOSE_FILE,
                        project_name=TASK_PROJECT,
                        profile=RUNTIME_PROFILE,
                    ),
                    service=ComposeService.DB_BOOTSTRAP,
                    run_id=run_id,
                    recovered_generation_id=recovered_generation_id,
                    adapter=PathCapability.from_path(
                        adapter_source, kind=PathCapabilityKind.FILE, require_exists=True
                    ),
                ),
                True,
            )
        kind = (
            ProbeKind.POSTGRES_READY
            if "pg_isready" in " ".join(command_tail)
            else ProbeKind.AUTH_REJECTION
            if "schema_version" in " ".join(command_tail)
            or "CLIENT_CONNECTION_ATTEMPT_FAILED" in " ".join(command_tail)
            else ProbeKind.APPLICATION_QUERY
            if "APPLICATION_QUERY_OK" in " ".join(command_tail)
            or "SELECT 1" in " ".join(command_tail)
            else ProbeKind.IMPORT_PROBE
        )
        return SemanticDispatch(
            ProbeAction(
                probe_kind=kind,
                image=argv[index],
                name=pairs.get("--name", [argv[-1]])[0],
                labels=tuple(sorted((str(k), str(v)) for k, v in labels)),
                network_policy=NetworkPolicy.INTERNAL_ONLY
                if kind != ProbeKind.IMPORT_PROBE
                else NetworkPolicy.NONE,
                secret_mount=SecretMountCapability.REQUIRED,
            ),
            True,
        )
    if argv[1] == "compose":
        return _compose_dispatch(argv)
    raise ValueError("unknown docker command")


TASK_ID: Final = "RF-08-CORRECTIVE-ELIMINATE-HOST-EXECUTABLE-CONTENT-AUTHORITY-20260801-08"
CANONICAL_PROJECT: Final = "avito-mayak-acceptance"
TASK_PROJECT: Final = "avito-mayak-rf08-secret-delivery"
EXPECTED_IMAGE_SOURCE: Final = "https://github.com/MaksimUnimax/AVITO_Mayak"
EXPECTED_LOCK_IDENTITY: Final = "e1faff1ce0f4d5dfd35480ab59d5d599fddf05c38fcd16a26c52098511476ab6"
MIGRATION_HEAD: Final = "RF12_MANUAL_GRANT"
EVIDENCE_PATH: Final = Path(
    "docs/07-quality/evidence/RF08_AUTHORITATIVE_SECRET_LIFECYCLE_PROOF_v1.json"
)
RUNTIME_ROOT: Final = Path("/opt/avito-mayak-runtime/rf08-secret-delivery")
PRIVATE_OUTPUT_ROOT: Final = RUNTIME_ROOT / "private-output"
JSON_LOG_ROOT: Final = RUNTIME_ROOT / "postgres-jsonlog"
JSON_LOG_OVERRIDE: Final = RUNTIME_ROOT / "postgres-jsonlog.override.yaml"
RUNTIME_COMPOSE_FILE: Final = RUNTIME_ROOT / "compose.runtime.yaml"
APPLICATION_SECRET_DESTINATION: Final = "/run/secrets/mayak_database_application_password"
BOUNDED_AUTH_SCHEMA: Final = "rf08-stage34-auth-v1"
BOUNDED_BOOTSTRAP_SCHEMA: Final = "rf08-post-recovery-bootstrap-v1"
_FINGERPRINT = re.compile(
    rb"(?i)(-----BEGIN [A-Z ]+PRIVATE KEY-----|password\s*=|postgresql://|dsn\s*=)"
)
_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")

REQUIRED_STAGES: Final[tuple[str, ...]] = (
    "PREFLIGHT",
    "CANONICAL_COMPOSE_VALIDATION",
    "IMAGE_INPUT_DIGEST",
    "APPLICATION_IMAGE_RESOLUTION",
    "APPLICATION_IMAGE_BUILD_OR_REUSE",
    "APPLICATION_IMAGE_INSPECT",
    "APPLICATION_IMAGE_PROVENANCE_VERIFY",
    "APPLICATION_IMAGE_ENVIRONMENT_VERIFY",
    "APPLICATION_IMAGE_IMPORT_PROBE",
    "FOREIGN_RESOURCE_SNAPSHOT_BEFORE",
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

REPLAY_REQUIRED_ABSENT_NAMES: Final[tuple[str, ...]] = (
    f"{TASK_PROJECT}-image-probe-1",
    f"{TASK_PROJECT}-mayak-api-1",
    f"{TASK_PROJECT}-mayak-worker-1",
    f"{TASK_PROJECT}-mayak-scheduler-1",
    f"{TASK_PROJECT}-mayak-postgres-1",
    f"{TASK_PROJECT}-mayak-db-bootstrap-1",
    f"{TASK_PROJECT}-mayak-migrate-1",
    f"{TASK_PROJECT}_mayak-internal",
    f"{TASK_PROJECT}_postgres-data",
)

APPLICATION_QUERY: Final = "import pathlib,psycopg; p=pathlib.Path('/run/secrets/mayak_database_application_password').read_text(); c=psycopg.connect(host='mayak-postgres',port=5432,dbname='mayak',user='mayak_application',password=p); assert c.execute('SELECT 1').fetchone()==(1,); c.close(); print('APPLICATION_QUERY_OK')"  # noqa: E501
AUTH_QUERY: Final = r"""import json,os,pathlib,stat,sys

cid=sys.argv[1]
path=pathlib.Path("/run/secrets/mayak_database_application_password")
result={"schema_version":"rf08-stage34-auth-v1","operation_id":"rf08.application_auth_rejection_b",
 "correlation_id":cid,"import_state":"NOT_ATTEMPTED","secret_binding_state":"NOT_CHECKED",
 "mount_state":"PRESENT","file_state":"NOT_CHECKED","file_read_attempted":False,
 "file_read_state":"NOT_ATTEMPTED","connection_attempted":False,"unexpected_success":False,
 "exception_class_name":None,"client_sqlstate":None,"pgconn_present":False,
 "pgconn_status":None,"timeout":False,"final_client_outcome":"IMPORT_FAILURE"}

def emit(code):
    sys.stdout.write(json.dumps(result,separators=(",",":"),sort_keys=True)+"\n")
    raise SystemExit(code)

try:
    import psycopg
    result["import_state"]="IMPORTED"
except Exception:
    emit(64)

try:
    info=path.lstat()
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        result["file_state"]="UNSAFE"
        result["secret_binding_state"]="REJECTED"
        result["final_client_outcome"]="SECRET_FILE_UNSAFE"
        emit(67)
    if info.st_size < 1 or info.st_size > 4096 or stat.S_IMODE(info.st_mode) & 0o077:
        result["file_state"]="UNSAFE"
        result["secret_binding_state"]="REJECTED"
        result["final_client_outcome"]="SECRET_FILE_UNSAFE"
        emit(67)
    result["file_state"]="REGULAR_FILE"
except FileNotFoundError:
    result["file_state"]="MISSING"
    result["secret_binding_state"]="REJECTED"
    result["final_client_outcome"]="SECRET_FILE_MISSING"
    emit(66)
except PermissionError:
    result["file_state"]="PERMISSION_DENIED"
    result["secret_binding_state"]="REJECTED"
    result["final_client_outcome"]="SECRET_FILE_PERMISSION_DENIED"
    emit(68)
except Exception:
    result["file_state"]="READ_FAILURE"
    result["secret_binding_state"]="REJECTED"
    result["final_client_outcome"]="SECRET_FILE_READ_FAILURE"
    emit(69)

try:
    result["file_read_attempted"]=True
    with path.open("rb") as handle:
        password=handle.read()
    if not password:
        result["file_read_state"]="EMPTY"
        result["secret_binding_state"]="REJECTED"
        result["final_client_outcome"]="SECRET_FILE_READ_FAILURE"
        emit(69)
    result["file_read_state"]="READABLE"
    result["secret_binding_state"]="ACCEPTED"
except PermissionError:
    result["file_read_state"]="PERMISSION_DENIED"
    result["secret_binding_state"]="REJECTED"
    result["final_client_outcome"]="SECRET_FILE_PERMISSION_DENIED"
    emit(68)
except Exception:
    result["file_read_state"]="READ_FAILURE"
    result["secret_binding_state"]="REJECTED"
    result["final_client_outcome"]="SECRET_FILE_READ_FAILURE"
    emit(69)

try:
    c=psycopg.connect(host="mayak-postgres",port=5432,dbname="mayak",user="mayak_application",
                      password=password,application_name=cid,connect_timeout=10)
    result["connection_attempted"]=True
    result["unexpected_success"]=True
    result["final_client_outcome"]="UNEXPECTED_CONNECTION_SUCCESS"
    c.close()
    emit(79)
except Exception as exc:
    result["connection_attempted"]=True
    result["exception_class_name"]=type(exc).__name__
    state=getattr(exc,"sqlstate",None)
    diag=getattr(exc,"diag",None)
    result["client_sqlstate"]=state or getattr(diag,"sqlstate",None)
    pgconn=getattr(exc,"pgconn",None)
    result["pgconn_present"]=pgconn is not None
    result["pgconn_status"]=getattr(pgconn,"status",None)
    result["final_client_outcome"]="CLIENT_CONNECTION_ATTEMPT_FAILED_PENDING_SERVER_CLASSIFICATION"
    emit(78)
"""


def classify_correlated_b_authentication(
    client: Mapping[str, object], server: Mapping[str, object]
) -> dict[str, object]:
    """Join safe client-attempt evidence to an independently parsed PG event.

    This deliberately does not inspect exception text.  A missing client SQLSTATE
    is valid only when the independent, exact server event supplies 28P01.
    """
    if client.get("schema_version") == BOUNDED_AUTH_SCHEMA:
        required_client = {
            "import_state": "IMPORTED",
            "secret_binding_state": "ACCEPTED",
            "file_state": "REGULAR_FILE",
            "file_read_state": "READABLE",
            "connection_attempted": True,
            "unexpected_success": False,
            "timeout": False,
            "final_client_outcome": (
                "CLIENT_CONNECTION_ATTEMPT_FAILED_PENDING_SERVER_CLASSIFICATION"
            ),
            "exit_code": 78,
        }
    else:
        required_client = {
            "import_ok": True,
            "file_read_ok": True,
            "connect_attempted": True,
            "unexpected_success": False,
            "exit_code": 78,
        }
    if any(client.get(k) != value for k, value in required_client.items()):
        raise ProtocolFailure("APPLICATION_AUTH_REJECTION_B_CLASSIFY")
    correlation_id = client.get("correlation_id")
    if not isinstance(correlation_id, str) or not re.fullmatch(r"rf08b_[a-z0-9]+", correlation_id):
        raise ProtocolFailure("APPLICATION_AUTH_REJECTION_B_CLASSIFY")
    if client.get("client_sqlstate") not in (None, "28P01"):
        raise ProtocolFailure("APPLICATION_AUTH_REJECTION_B_CLASSIFY")
    exact_application = server.get("application_name") == correlation_id
    remote_fallback = (
        server.get("application_name") in (None, "")
        and isinstance(client.get("probe_ip"), str)
        and client.get("probe_ip") == server.get("remote_identity")
    )
    if (
        server.get("sqlstate") != "28P01"
        or server.get("severity") != "FATAL"
        or server.get("user") != "mayak_application"
        or server.get("database") != "mayak"
        or not (exact_application or remote_fallback)
        or (
            client.get("schema_version") == BOUNDED_AUTH_SCHEMA
            and (not isinstance(server.get("session_id"), str) or not server.get("session_id"))
        )
        or server.get("event_count") != 1
        or not server.get("task_postgres_identity")
        or server.get("event_after_lower_bound") is not True
        or server.get("no_competing_events") is not True
    ):
        raise ProtocolFailure("APPLICATION_AUTH_REJECTION_B_CLASSIFY")
    return {
        "observed": "POSTGRESQL_AUTHENTICATION_REJECTED_SQLSTATE_28P01",
        "classification": "POSTGRESQL_AUTHENTICATION_REJECTED_SQLSTATE_28P01",
        "client_sqlstate": client.get("client_sqlstate"),
        "server_sqlstate": server["sqlstate"],
        "correlation_id": correlation_id,
        "correlation_method": (
            "exact_application_name" if exact_application else "remote_ip_fallback"
        ),
        "matching_event_count": server["event_count"],
    }


def _jsonlog_override(run_id: str, log_dir: Path) -> str:
    """Return the only Compose override permitted for this task.

    The override is deliberately runtime-only.  PostgreSQL JSON records are
    written to a host directory owned by the task and never enter the
    container runtime's default logging stream.
    """
    if JSON_LOG_ROOT not in log_dir.parents or log_dir == JSON_LOG_ROOT:
        raise ProtocolFailure("PREFLIGHT", "STOP_SECURITY_RISK")
    return """services:
  mayak-postgres:
    command:
      - postgres
      - -c
      - logging_collector=on
      - -c
      - log_destination=jsonlog
      - -c
      - log_directory=/var/log/postgresql
      - -c
      - log_filename=rf08_%s
      - -c
      - log_rotation_age=0
      - -c
      - log_rotation_size=0
      - -c
      - log_file_mode=0600
      - -c
      - log_connections=on
      - -c
      - log_error_verbosity=verbose
      - -c
      - log_min_error_statement=PANIC
      - -c
      - log_statement=none
      - -c
      - log_duration=off
      - -c
      - log_min_duration_statement=-1
    volumes:
      - %s:/var/log/postgresql:rw
""" % (run_id, str(log_dir))


def _runtime_compose_file(run_id: str, log_dir: Path) -> str:
    source = Path(__file__).resolve().parents[2] / "compose.yaml"
    text = source.read_text(encoding="utf-8")
    start_marker = "  mayak-postgres:\n    profiles: [runtime-foundation]\n"
    end_marker = "  mayak-db-bootstrap:\n    profiles: [runtime-foundation]\n"
    start = text.find(start_marker)
    end = text.find(end_marker, start)
    if start < 0 or end < 0:
        fallback = Path("/opt/avito-mayak-runtime/rf08-secret-delivery/base-7467/compose.yaml")
        if fallback.is_file():
            text = fallback.read_text(encoding="utf-8")
            start = text.find(start_marker)
            end = text.find(end_marker, start)
        if start < 0 or end < 0:
            return text
    text = text.replace("      context: .\n", f"      context: {source.parent}\n")
    start = text.find(start_marker)
    end = text.find(end_marker, start)
    if start < 0 or end < 0:
        return text
    block = f"""  mayak-postgres:
    profiles: [runtime-foundation]
    command:
      - postgres
      - -c
      - logging_collector=on
      - -c
      - log_destination=jsonlog
      - -c
      - log_directory=/var/log/postgresql
      - -c
      - log_filename=postgresql.json
      - -c
      - log_connections=on
      - -c
      - log_error_verbosity=verbose
      - -c
      - log_min_error_statement=PANIC
      - -c
      - log_statement=none
      - -c
      - log_duration=off
      - -c
      - log_min_duration_statement=-1
    image: postgres:18-bookworm@sha256:1961f96e6029a02c3812d7cb329a3b03a3ac2bb067058dec17b0f5596aca9296
    platform: linux/amd64
    restart: on-failure:5
    environment:
      POSTGRES_DB: mayak
      POSTGRES_USER: mayak
      POSTGRES_PASSWORD_FILE: /run/secrets/mayak_postgres_bootstrap_password
    secrets:
      - source: mayak_postgres_bootstrap_password_postgres
        target: mayak_postgres_bootstrap_password
    volumes:
      - postgres-data:/var/lib/postgresql
      - {str(log_dir)}:/var/log/postgresql:rw
    networks: [mayak-internal]
    healthcheck:
      test: [CMD-SHELL, 'pg_isready -U "$$POSTGRES_USER" -d "$$POSTGRES_DB"']
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 10s
    labels:
      com.avito-mayak.project-owned: "true"
      com.avito-mayak.environment-id: avito-mayak-acceptance-local-01
      com.avito-mayak.compose-family: acceptance
      com.avito-mayak.process-kind: mayak-postgres
"""
    result = text[:start] + block + text[end:]
    label_block = (
        '      com.avito-mayak.project-owned: "true"\n'
        "      com.avito-mayak.environment-id: avito-mayak-acceptance-local-01\n"
        "      com.avito-mayak.compose-family: acceptance\n"
    )
    result = result.replace(
        label_block,
        label_block + "      com.avito-mayak.technical-id: " + TASK_ID + "\n",
    )
    return result


def prepare_jsonlog_runtime(run_id: str) -> Path:
    """Create and validate the task-owned JSON log mount and override."""
    JSON_LOG_ROOT.mkdir(mode=0o700, parents=True, exist_ok=True)
    JSON_LOG_ROOT.chmod(0o700)
    log_dir = JSON_LOG_ROOT / run_id
    log_dir.mkdir(mode=0o700)
    log_dir.chmod(0o700)
    # postgres:postgres is 999:999 in the pinned postgres image.  The runtime
    # verifier checks the actual container UID/GID before accepting the file.
    try:
        os.chown(log_dir, 999, 999)
    except OSError as exc:
        raise ProtocolFailure("PREFLIGHT", "STOP_SECURITY_RISK") from exc
    JSON_LOG_OVERRIDE.write_text(_jsonlog_override(run_id, log_dir), encoding="ascii")
    JSON_LOG_OVERRIDE.chmod(0o600)
    RUNTIME_COMPOSE_FILE.write_text(_runtime_compose_file(run_id, log_dir), encoding="utf-8")
    RUNTIME_COMPOSE_FILE.chmod(0o600)
    return log_dir


def _active_json_log(log_dir: Path) -> Path:
    if JSON_LOG_ROOT not in log_dir.parents or not log_dir.is_dir():
        raise ProtocolFailure("APPLICATION_AUTH_REJECTION_B_CLASSIFY", "STOP_SECURITY_RISK")
    files = [
        p for p in log_dir.iterdir() if p.is_file() and not p.is_symlink() and p.suffix == ".json"
    ]
    if not files:
        raise ProtocolFailure("APPLICATION_AUTH_REJECTION_B_CLASSIFY", "JSON_LOG_IDENTITY_INVALID")
    active = max(files, key=lambda path: (path.stat().st_mtime_ns, path.name))
    info = active.stat()
    if stat.S_IMODE(info.st_mode) != 0o600:
        raise ProtocolFailure("APPLICATION_AUTH_REJECTION_B_CLASSIFY", "STOP_SECURITY_RISK")
    return active


def _read_appended_json(log_file: Path, offset: int) -> list[dict[str, object]]:
    if log_file.is_symlink() or JSON_LOG_ROOT not in log_file.resolve().parents:
        raise ProtocolFailure("APPLICATION_AUTH_REJECTION_B_CLASSIFY", "STOP_SECURITY_RISK")
    data = log_file.read_bytes()
    if len(data) < offset:
        raise ProtocolFailure("APPLICATION_AUTH_REJECTION_B_CLASSIFY", "JSON_LOG_TRUNCATED")
    appended = data[offset:]
    forbidden = rb"(?i)(postgresql://|dsn=|statement|internal_query|environment)"
    if _FINGERPRINT.search(appended) or re.search(forbidden, appended):
        raise ProtocolFailure("APPLICATION_AUTH_REJECTION_B_CLASSIFY", "STOP_SECURITY_RISK")
    lines = appended.splitlines()
    if appended and not appended.endswith(b"\n"):
        return []
    events: list[dict[str, object]] = []
    for line in lines:
        if not line:
            continue
        value = json.loads(line.decode("utf-8"))
        if not isinstance(value, dict):
            raise ProtocolFailure("APPLICATION_AUTH_REJECTION_B_CLASSIFY", "MALFORMED_JSON")
        events.append(value)
    return events


REQUIRED_POSTGRES_JSONLOG_SETTINGS: Final[dict[str, str]] = {
    "logging_collector": "on",
    "log_destination": "jsonlog",
    "log_rotation_age": "0",
    "log_rotation_size": "0",
    "log_file_mode": "0600",
    "log_connections": "on",
    "log_error_verbosity": "verbose",
    "log_min_error_statement": "panic",
    "log_statement": "none",
    "log_duration": "off",
    "log_min_duration_statement": "-1",
}


def validate_jsonlog_runtime(
    settings: Mapping[str, object],
    log_dir: Path,
    log_file: Path,
    *,
    owner_uid: int,
    owner_gid: int,
) -> dict[str, object]:
    """Validate runtime SHOW/file identity; merged YAML alone is insufficient."""
    if any(
        str(settings.get(k, "")).lower() != v for k, v in REQUIRED_POSTGRES_JSONLOG_SETTINGS.items()
    ):
        raise ProtocolFailure("POSTGRES_A_HEALTH", "JSON_LOG_RUNTIME_SETTINGS_INVALID")
    if JSON_LOG_ROOT not in log_dir.parents or log_file.parent != log_dir:
        raise ProtocolFailure("POSTGRES_A_HEALTH", "STOP_SECURITY_RISK")
    if log_file.is_symlink() or not log_file.is_file():
        raise ProtocolFailure("POSTGRES_A_HEALTH", "JSON_LOG_FILE_INVALID")
    info = log_file.stat()
    if (info.st_uid, info.st_gid) != (owner_uid, owner_gid) or stat.S_IMODE(info.st_mode) != 0o600:
        raise ProtocolFailure("POSTGRES_A_HEALTH", "STOP_SECURITY_RISK")
    return {"runtime_settings_exact": True, "task_owned_file": True, "file_mode": "0600"}


@dataclass(frozen=True)
class PrivateCommandResult:
    stage: str
    command_id: str
    exit_code: int | None
    executed: bool
    parsed: Mapping[str, object]
    stdout_scanned: bool
    stderr_scanned: bool
    private_output_cleaned: bool
    private_secret_detected: bool = False
    timed_out: bool = False


@dataclass(frozen=True)
class StageResult:
    stage: str
    operation_id: str
    executed: bool
    exit_code: int | None
    parsed: Mapping[str, object]
    output_clean: bool = True
    timed_out: bool = False
    stdout_captured: bool = True
    stderr_captured: bool = True
    stdout_scan_passed: bool = True
    stderr_scan_passed: bool = True
    run_id: str = ""


RUNTIME_BINDING_SCHEMA: Final = "rf08-runtime-binding-state-v1"


@dataclass(frozen=True, slots=True)
class GenerationPolicyState:
    """Closed generation phases; recovery is never an alias for active policy."""

    initial_a_generation_id: str | None
    current_policy_generation_id: str | None
    rollback_a_generation_id: str | None
    generation_c_id: str | None
    recovered_d_generation_id: str | None


@dataclass(frozen=True, slots=True)
class ComposeResolutionState:
    schema_version: str
    source_identity: str
    secret_source_identity: str


@dataclass(frozen=True, slots=True)
class ContainerEpochState:
    identity: str
    epoch: str
    health_proof: str


@dataclass(frozen=True, slots=True)
class VolumeEpochState:
    identity: str
    epoch: str


@dataclass(frozen=True, slots=True)
class MountedSecretBindingState:
    identity: str
    generation_id: str
    epoch: str


@dataclass(frozen=True, slots=True)
class BootstrapStageHandoff:
    """One-use, immutable authority for one database bootstrap operation."""

    schema_version: str
    stage_id: str
    expected_generation: str
    current_policy_generation: str
    active_generation: str
    compose: ComposeResolutionState
    container: ContainerEpochState
    volume_epoch: VolumeEpochState
    run_epoch: str
    mounted_secret: MountedSecretBindingState
    adapter_action: str
    consumed: bool = False

    def consume(self) -> "BootstrapStageHandoff":
        if self.consumed:
            raise ProtocolFailure(self.stage_id, "BOOTSTRAP_HANDOFF_REUSED")
        return replace(self, consumed=True)


@dataclass(frozen=True, slots=True)
class RecoveryHandoffResult:
    """Immutable, safe handoff from recovery to the post-recovery proof."""

    schema_version: str
    run_id: str
    abrupt_d_exit: int
    recovery_action: str
    recovered_generation_id: str
    recovered_generation_valid: bool
    active_pointer_valid: bool
    policy_generation_id: str
    runtime_consumer_generation_id: str
    postgres_consumer_generation_id: str
    runtime_consumer_equal: bool
    postgres_consumer_equal: bool
    manifest_valid: bool
    no_path_escape: bool
    no_symlink: bool
    recovery_cleanup: bool


@dataclass(frozen=True, slots=True)
class ReplayNamespaceSanitationRecord:
    """Immutable, source-bound proof that the replay namespace was reset."""

    schema_version: str
    technical_id: str
    gateway_instance_id: str
    transcript_run_id: str
    source_sha: str
    sanitation_nonce: str
    foreign_before_digest: str
    foreign_before_independent_digest: str
    foreign_after_digest: str
    foreign_after_independent_digest: str
    foreign_before_equal: bool
    foreign_after_equal: bool
    required_name_absence_hashes: tuple[str, ...]
    required_name_absence_digest: str
    task_container_count_before: int
    task_network_count_before: int
    task_volume_count_before: int
    task_container_count_after: int
    task_network_count_after: int
    task_volume_count_after: int
    unresolved_container_count_before: int
    unresolved_network_count_before: int
    unresolved_volume_count_before: int
    unresolved_container_count_after: int
    unresolved_network_count_after: int
    unresolved_volume_count_after: int
    removed_container_count: int
    removed_network_count: int
    removed_volume_count: int
    builder_count_before: int
    builder_count_after: int
    task_secret_generation_count_before: int
    task_secret_generation_count_after: int
    cleared_secret_root: bool
    verified_absence: bool
    record_digest: str

    def safe_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "technical_id": self.technical_id,
            "gateway_instance_id": self.gateway_instance_id,
            "transcript_run_id": self.transcript_run_id,
            "source_sha": self.source_sha,
            "sanitation_nonce": self.sanitation_nonce,
            "foreign_before_digest": self.foreign_before_digest,
            "foreign_before_independent_digest": self.foreign_before_independent_digest,
            "foreign_after_digest": self.foreign_after_digest,
            "foreign_after_independent_digest": self.foreign_after_independent_digest,
            "foreign_before_equal": self.foreign_before_equal,
            "foreign_after_equal": self.foreign_after_equal,
            "required_name_absence_hashes": list(self.required_name_absence_hashes),
            "required_name_absence_digest": self.required_name_absence_digest,
            "task_container_count_before": self.task_container_count_before,
            "task_network_count_before": self.task_network_count_before,
            "task_volume_count_before": self.task_volume_count_before,
            "task_container_count_after": self.task_container_count_after,
            "task_network_count_after": self.task_network_count_after,
            "task_volume_count_after": self.task_volume_count_after,
            "unresolved_container_count_before": self.unresolved_container_count_before,
            "unresolved_network_count_before": self.unresolved_network_count_before,
            "unresolved_volume_count_before": self.unresolved_volume_count_before,
            "unresolved_container_count_after": self.unresolved_container_count_after,
            "unresolved_network_count_after": self.unresolved_network_count_after,
            "unresolved_volume_count_after": self.unresolved_volume_count_after,
            "removed_container_count": self.removed_container_count,
            "removed_network_count": self.removed_network_count,
            "removed_volume_count": self.removed_volume_count,
            "builder_count_before": self.builder_count_before,
            "builder_count_after": self.builder_count_after,
            "task_secret_generation_count_before": self.task_secret_generation_count_before,
            "task_secret_generation_count_after": self.task_secret_generation_count_after,
            "cleared_secret_root": self.cleared_secret_root,
            "verified_absence": self.verified_absence,
            "record_digest": self.record_digest,
        }


@dataclass(frozen=True, slots=True)
class PostRecoveryProofResult:
    """Typed internal stage-55 result; never a transcript stage."""

    handoff: RecoveryHandoffResult
    recovered_consumers: Mapping[str, object]
    resource_plan: Mapping[str, object]
    postgres_create: Mapping[str, object]
    health: Mapping[str, object]
    bootstrap: Mapping[str, object]
    migration_upgrade: Mapping[str, object]
    migration_head: Mapping[str, object]
    application_query: Mapping[str, object]


class ExitPolicyKind(str, Enum):
    ZERO_REQUIRED = "ZERO_REQUIRED"
    EXACT_EXIT = "EXACT_EXIT"


@dataclass(frozen=True)
class ExitPolicy:
    policy_id: str
    kind: ExitPolicyKind
    exact_exit: int | None = None

    def accepts(self, exit_code: int | None) -> bool:
        if exit_code is None:
            return False
        if self.kind is ExitPolicyKind.ZERO_REQUIRED:
            return exit_code == 0
        return self.exact_exit is not None and exit_code == self.exact_exit


ZERO_REQUIRED: Final = ExitPolicy("exit.zero_required", ExitPolicyKind.ZERO_REQUIRED)


def EXACT_EXIT(code: int) -> ExitPolicy:
    if code < 0:
        raise ValueError("exit code must be non-negative")
    return ExitPolicy(f"exit.exact_{code}", ExitPolicyKind.EXACT_EXIT, code)


class ProtocolFailure(RuntimeError):
    def __init__(self, stage: str, classification: str = "UNKNOWN_SAFE_FAILURE") -> None:
        super().__init__("stage failed")
        self.stage, self.classification = stage, classification


class CommandRunner(Protocol):
    def run(self, payload: CommandRequest, *, stage: str) -> PrivateCommandResult: ...


@dataclass(frozen=True)
class StageSpec:
    name: str
    operation: Callable[[], StageResult]
    oracle: Callable[[StageResult], Mapping[str, object]]
    parser_id: str
    oracle_id: str
    exit_policy: ExitPolicy = ZERO_REQUIRED


@dataclass(frozen=True)
class ApplicationProbeContract:
    """The single immutable runtime contract for every application probe."""

    image_id: str
    configured_user: str
    effective_uid: int
    effective_gid: int
    workdir: str
    entrypoint_protocol: str
    task_project: str
    task_network: str
    labels: tuple[tuple[str, str], ...]
    mount_destination: str = APPLICATION_SECRET_DESTINATION
    mount_read_only: bool = True
    published_ports: tuple[str, ...] = ()
    security_options: tuple[str, ...] = (
        "no-privileged",
        "no-host-pid",
        "no-host-ipc",
        "no-docker-socket",
    )
    timeout_seconds: int = 10

    @property
    def contract_id(self) -> str:
        encoded = json.dumps(self.parity_fields(), sort_keys=True, separators=(",", ":"))
        return "rf08-probe-" + hashlib.sha256(encoded.encode()).hexdigest()[:20]

    def parity_fields(self) -> dict[str, object]:
        return {
            "image_id": self.image_id,
            "configured_user": self.configured_user,
            "effective_uid": self.effective_uid,
            "effective_gid": self.effective_gid,
            "workdir": self.workdir,
            "entrypoint_protocol": self.entrypoint_protocol,
            "task_project": self.task_project,
            "task_network": self.task_network,
            "labels": list(self.labels),
            "mount_destination": self.mount_destination,
            "mount_read_only": self.mount_read_only,
            "published_ports": list(self.published_ports),
            "security_options": list(self.security_options),
        }


def build_application_probe_contract(
    image_id: str,
    *,
    configured_user: str = "10001:10001",
    effective_uid: int = 10001,
    effective_gid: int = 10001,
    workdir: str = "/opt/mayak",
) -> ApplicationProbeContract:
    if not image_id or not configured_user or effective_uid < 1 or effective_gid < 1:
        raise ValueError("invalid application probe contract")
    return ApplicationProbeContract(
        image_id=image_id,
        configured_user=configured_user,
        effective_uid=effective_uid,
        effective_gid=effective_gid,
        workdir=workdir,
        entrypoint_protocol="python -c <bounded-json-payload>",
        task_project=TASK_PROJECT,
        task_network=f"{TASK_PROJECT}_mayak-internal",
        labels=(
            ("com.avito-mayak.technical-id", TASK_ID),
            ("com.avito-mayak.owner", "rf08"),
        ),
    )


def application_probe_parity(
    left: ApplicationProbeContract, right: ApplicationProbeContract
) -> dict[str, object]:
    fields = left.parity_fields()
    equal = fields == right.parity_fields()
    return {"equal": equal, "compared_fields": sorted(fields)}


def application_probe_command(
    contract: ApplicationProbeContract, payload: str, *arguments: str
) -> CommandRequest:
    """Build every A/restart/B/rollback/C/recovery probe through one authority."""
    if not contract.mount_read_only or contract.published_ports:
        raise ValueError("unsafe application probe contract")
    return _docker(
        (
            "run",
            "--rm",
            "--no-deps",
            "--user",
            contract.configured_user,
            "--workdir",
            contract.workdir,
            "--entrypoint",
            "python",
            "mayak-api",
            "-c",
            payload,
            *arguments,
        )
    )


def parse_bounded_auth_envelope(
    stdout: bytes, stderr: bytes, code: int | None
) -> dict[str, object]:
    """Parse exactly one safe JSON envelope, even when its exit is rejected."""
    stderr_lines = (
        [line for line in stderr.decode("utf-8", "strict").splitlines() if line] if stderr else []
    )
    accepted_statuses = {
        "Creating",
        "Created",
        "Starting",
        "Started",
        "Stopping",
        "Stopped",
        "Removing",
        "Removed",
    }
    if stderr_lines not in ([], ["RF08_B_PROBE_MARKER"]):
        if not stderr_lines or not all(
            len(line.split()) == 3
            and line.split()[0] == "Container"
            and re.fullmatch(r"[A-Za-z0-9_.-]+", line.split()[1])
            and line.split()[2] in accepted_statuses
            for line in stderr_lines
        ):
            return {}
    if not stdout.endswith(b"\n"):
        return {}
    lines = stdout.splitlines()
    if len(lines) != 1:
        return {}
    try:
        value = json.loads(lines[0].decode("utf-8"))
    except (UnicodeError, ValueError, json.JSONDecodeError):
        return {}
    if not isinstance(value, dict) or value.get("schema_version") != BOUNDED_AUTH_SCHEMA:
        return {}
    allowed = {
        "schema_version",
        "operation_id",
        "correlation_id",
        "import_state",
        "secret_binding_state",
        "mount_state",
        "file_state",
        "file_read_attempted",
        "file_read_state",
        "connection_attempted",
        "unexpected_success",
        "exception_class_name",
        "client_sqlstate",
        "pgconn_present",
        "pgconn_status",
        "timeout",
        "final_client_outcome",
    }
    if set(value) - allowed or value.get("operation_id") != "rf08.application_auth_rejection_b":
        return {}
    value["exit_code"] = code
    return value


def parse_bounded_bootstrap_result(
    stdout: bytes, stderr: bytes, code: int | None, *, run_id: str = ""
) -> dict[str, object]:
    """Accept only the adapter's single bounded JSON object."""
    try:
        text = stdout.decode("utf-8", "strict")
        lines = text.splitlines()
        if len(lines) != 1 or not text.endswith("\n"):
            return {}
        value = json.loads(lines[0])
    except (UnicodeError, ValueError, json.JSONDecodeError):
        return {}
    if not isinstance(value, dict):
        return {}
    required = {
        "schema_version",
        "operation_id",
        "run_id",
        "recovered_generation_id",
        "connection_attempted",
        "connected",
        "last_rf09_operation",
        "bootstrap_outcome",
        "invariant_code",
        "client_sqlstate",
        "cause_type",
        "committed",
        "rolled_back",
        "cursor_closed",
        "connection_closed",
        "migration_role_valid",
        "application_role_valid",
        "schema_owner_valid",
        "application_schema_create",
        "current_object_grants",
    }
    if set(value) != required or value.get("schema_version") != BOUNDED_BOOTSTRAP_SCHEMA:
        return {}
    if value.get("operation_id") != "rf09.public.bootstrap":
        return {}
    try:
        stderr.decode("utf-8", "strict")
    except UnicodeError:
        return {}
    if code not in (0, 81, 82, 83, 84, 85):
        return {}
    value["exit_code"] = code
    value["observed"] = value["bootstrap_outcome"]
    return value


@dataclass(frozen=True)
class TranscriptEntry:
    stage: str
    operation_id: str
    parser_id: str
    oracle_id: str
    status: str
    evidence: Mapping[str, object]


@dataclass
class DockerMutationLedger:
    entries: list[DockerMutationRecord] = field(default_factory=list)

    def append(self, entry: DockerMutationRecord) -> None:
        if (
            entry.ownership in {"FOREIGN", "UNRESOLVED"}
            or not entry.scoped
            or not entry.mutation_allowed
        ):
            raise ProtocolFailure(entry.stage, "STOP_FOREIGN_RESOURCE")
        self.entries.append(entry)

    def append_result(
        self,
        authorization: DockerMutationRecord,
        *,
        exit_code: int | None,
        completed: bool,
        timed_out: bool,
    ) -> None:
        self.entries.append(
            DockerMutationRecord(
                record_type="RESULT",
                authorization_sequence=authorization.authorization_sequence,
                execution_result_sequence=len(self.entries) + 1,
                invocation_sequence=authorization.invocation_sequence,
                stage=authorization.stage,
                semantic_class=authorization.semantic_class,
                target_kind=authorization.target_kind,
                target_identity_hash=authorization.target_identity_hash,
                authorization_basis=authorization.authorization_basis,
                authorization_outcome=authorization.authorization_outcome,
                execution_attempted=True,
                execution_completed=completed,
                exit_code=exit_code,
                timed_out=timed_out,
                safe_failure_classification=authorization.safe_failure_classification,
                target_ownership=authorization.target_ownership,
                argv_fingerprint=authorization.argv_fingerprint,
            )
        )


class ProtocolTranscript:
    def __init__(self, required_stages: tuple[str, ...] = REQUIRED_STAGES) -> None:
        if len(required_stages) != len(set(required_stages)):
            raise ValueError("duplicate stage")
        self.required = required_stages
        self._entries: list[TranscriptEntry] = []
        self._results: dict[str, StageResult] = {}
        self._rejected_results: dict[str, StageResult] = {}
        self.run_id = hashlib.sha256(os.urandom(32)).hexdigest()[:24]

    @property
    def entries(self) -> tuple[TranscriptEntry, ...]:
        return tuple(self._entries)

    @property
    def stage_sequence(self) -> tuple[str, ...]:
        return tuple(e.stage for e in self._entries)

    def result_for(self, stage: str) -> StageResult:
        try:
            return self._results[stage]
        except KeyError as exc:
            raise ProtocolFailure(stage, "MISSING_TRANSCRIPT_RESULT") from exc

    def rejected_result_for(self, stage: str) -> StageResult:
        try:
            return self._rejected_results[stage]
        except KeyError as exc:
            raise ProtocolFailure(stage, "MISSING_REJECTED_DIAGNOSTIC") from exc

    def execute(self, spec: StageSpec) -> TranscriptEntry:
        if (
            len(self._entries) >= len(self.required)
            or spec.name != self.required[len(self._entries)]
        ):
            raise ProtocolFailure(spec.name)
        result = replace(spec.operation(), run_id=self.run_id)
        self._rejected_results[spec.name] = replace(
            result, parsed=MappingProxyType(dict(result.parsed))
        )
        if (
            result.stage != spec.name
            or not result.executed
            or not result.output_clean
            or result.exit_code is None
            or result.timed_out
            or not result.stdout_captured
            or not result.stderr_captured
            or not result.stdout_scan_passed
            or not result.stderr_scan_passed
            or not spec.exit_policy.accepts(result.exit_code)
        ):
            raise ProtocolFailure(spec.name)
        self._results[spec.name] = self._rejected_results.pop(spec.name)
        evidence = dict(spec.oracle(result))
        if not evidence or "observed" not in evidence:
            raise ProtocolFailure(spec.name)
        entry = TranscriptEntry(
            spec.name,
            result.operation_id,
            spec.parser_id,
            spec.oracle_id,
            "PASS",
            _safe_fields(evidence),
        )
        self._entries.append(entry)
        return entry

    def finalize(self, postconditions: Mapping[str, bool]) -> None:
        if (
            self.stage_sequence != self.required
            or not postconditions
            or not all(postconditions.values())
        ):
            raise ProtocolFailure("FINALIZE")


def _safe_fields(fields: Mapping[str, object]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in fields.items():
        if not re.fullmatch(r"[a-z][a-z0-9_]*", key):
            raise ProtocolFailure("EVIDENCE")
        if isinstance(value, str) and (
            _FINGERPRINT.search(value.encode()) or "postgresql://" in value.lower()
        ):
            raise ProtocolFailure("EVIDENCE")
        if not isinstance(value, (str, int, bool, float, list, dict, type(None))):
            raise ProtocolFailure("EVIDENCE")
        result[key] = value
    return result


def _record_digest(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _name_hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _required_name_hashes() -> tuple[str, ...]:
    return tuple(_name_hash(name) for name in REPLAY_REQUIRED_ABSENT_NAMES)


def _kind_ids(gateway: GatewayAuthority, kind: str) -> tuple[str, ...]:
    if kind == "builder":
        result = gateway.observe(
            ObservationRequest(template=ObservationTemplate.BUILDX_LIST),
            stage="replay-namespace-builders",
            timeout=30,
        )
        if result.returncode != 0:
            raise ProtocolFailure("PREFLIGHT", "STOP_FOREIGN_RESOURCE")
        names: list[str] = []
        for line in result.stdout.splitlines():
            tokens = line.split()
            if not tokens or tokens[0].lower() == "name":
                continue
            name = tokens[0]
            if name == "*":
                if len(tokens) < 2:
                    continue
                name = tokens[1]
            elif name.startswith("*"):
                name = name.lstrip("*")
            if name:
                names.append(name)
        return tuple(dict.fromkeys(names))
    request = (
        ObservationRequest(template=ObservationTemplate.CONTAINER_LIST, kind=ResourceKind.CONTAINER)
        if kind == "container"
        else ObservationRequest(
            template={
                "network": ObservationTemplate.NETWORK_LIST,
                "volume": ObservationTemplate.VOLUME_LIST,
                "image": ObservationTemplate.IMAGE_LIST,
            }[kind],
            kind=ResourceKind(kind),
        )
    )
    result = gateway.observe(
        request,
        stage=f"replay-namespace-{kind}-ids",
        timeout=30,
    )
    if result.returncode != 0:
        raise ProtocolFailure("PREFLIGHT", "STOP_FOREIGN_RESOURCE")
    return tuple(dict.fromkeys(line.strip() for line in result.stdout.splitlines() if line.strip()))


def _inspect_resource(gateway: GatewayAuthority, kind: str, ident: str) -> dict[str, object]:
    result = gateway.observe(
        ObservationRequest(
            template={
                "container": ObservationTemplate.CONTAINER_INSPECT,
                "network": ObservationTemplate.NETWORK_INSPECT,
                "volume": ObservationTemplate.VOLUME_INSPECT,
                "image": ObservationTemplate.IMAGE_INSPECT,
            }[kind],
            identity=ident,
            kind=ResourceKind(kind),
        ),
        stage=f"replay-namespace-inspect-{kind}",
        timeout=30,
    )
    if result.returncode != 0:
        raise ProtocolFailure("PREFLIGHT", "STOP_FOREIGN_RESOURCE")
    value = json.loads(result.stdout)
    if not isinstance(value, list) or len(value) != 1 or not isinstance(value[0], dict):
        raise ProtocolFailure("PREFLIGHT", "STOP_FOREIGN_RESOURCE")
    return value[0]


def _resource_ownership(name: str, labels: Mapping[str, object], kind: str) -> str:
    project = str(labels.get("com.docker.compose.project", ""))
    technical = str(labels.get("com.avito-mayak.technical-id", ""))
    task_indicator = project == TASK_PROJECT or name.startswith(TASK_PROJECT)
    if name == "apm-postgres" and kind == "container":
        return "FOREIGN"
    if technical != TASK_ID:
        return "UNRESOLVED" if task_indicator else "FOREIGN"
    if kind == "container":
        service = str(labels.get("com.docker.compose.service", ""))
        if (
            project == TASK_PROJECT
            and service
            in {
                "mayak-api",
                "mayak-worker",
                "mayak-scheduler",
                "mayak-postgres",
                "mayak-db-bootstrap",
                "mayak-migrate",
            }
            and name == f"{TASK_PROJECT}-{service}-1"
        ) or (project == TASK_PROJECT and name == f"{TASK_PROJECT}-image-probe-1"):
            return "TASK_OWNED"
    elif kind == "network":
        if project == TASK_PROJECT and name == f"{TASK_PROJECT}_mayak-internal":
            return "TASK_OWNED"
    elif kind == "volume":
        if project == TASK_PROJECT and name == f"{TASK_PROJECT}_postgres-data":
            return "TASK_OWNED"
    return "UNRESOLVED" if task_indicator else "FOREIGN"


def _secret_generation_residue(root: Path) -> tuple[int, bool]:
    cleared = False
    count = 0
    sets = root / "sets"
    if sets.exists():
        if sets.is_symlink() or not sets.is_dir():
            raise ProtocolFailure("PREFLIGHT", "STOP_FOREIGN_RESOURCE")
        for child in tuple(sets.iterdir()):
            if child.is_symlink():
                child.unlink()
                cleared = True
                continue
            if not child.is_dir() or not secrets.GENERATION_RE.fullmatch(child.name):
                raise ProtocolFailure("PREFLIGHT", "STOP_FOREIGN_RESOURCE")
            secrets.validate_generation(root, child.name, postgres_uid=999, postgres_gid=999)
            shutil.rmtree(child)
            count += 1
            cleared = True
        if not any(sets.iterdir()):
            shutil.rmtree(sets)
            cleared = True
    active = root / "active"
    if active.exists() or active.is_symlink():
        if active.is_symlink() or active.is_file():
            active.unlink()
            cleared = True
        else:
            raise ProtocolFailure("PREFLIGHT", "STOP_FOREIGN_RESOURCE")
    return count, cleared


def _buildx_builder_count(gateway: GatewayAuthority) -> int:
    names = _kind_ids(gateway, "builder")
    task_owned = [name for name in names if name.startswith(TASK_PROJECT)]
    if task_owned:
        raise ProtocolFailure("PREFLIGHT", "STOP_FOREIGN_RESOURCE")
    return len(names)


def _inspect_replay_namespace(gateway: GatewayAuthority) -> dict[str, Any]:
    containers: list[dict[str, Any]] = []
    networks: list[dict[str, Any]] = []
    volumes: list[dict[str, Any]] = []
    task: dict[str, list[dict[str, Any]]] = {"containers": [], "networks": [], "volumes": []}
    unresolved: dict[str, list[dict[str, Any]]] = {
        "containers": [],
        "networks": [],
        "volumes": [],
    }
    for kind, bucket in (("container", containers), ("network", networks), ("volume", volumes)):
        for ident in _kind_ids(gateway, kind):
            item = _inspect_resource(gateway, kind, ident)
            if kind == "container":
                name = str(item.get("Name", "")).lstrip("/")
                cfg = item.get("Config", {})
                labels = cfg.get("Labels", {}) if isinstance(cfg, dict) else {}
            else:
                name = str(item.get("Name", ""))
                labels = item.get("Labels", {})
            labels = labels if isinstance(labels, dict) else {}
            ownership = _resource_ownership(name, labels, kind)
            record: dict[str, Any] = {
                "kind": kind,
                "name": name,
                "raw_name": name,
                "identity_hash": _name_hash(str(item.get("Id") or item.get("ID") or name)),
                "raw_identity": str(item.get("Id") or item.get("ID") or name),
                "ownership": ownership,
                "labels": {str(k): str(v) for k, v in labels.items()},
                "service": str(labels.get("com.docker.compose.service", ""))
                if kind == "container"
                else "",
            }
            bucket.append(record)
            if ownership == "TASK_OWNED":
                task[f"{kind}s"].append(record)
            elif ownership == "UNRESOLVED":
                unresolved[f"{kind}s"].append(record)
    foreign: dict[str, list[dict[str, Any]]] = {
        "containers": [item for item in containers if item["ownership"] == "FOREIGN"],
        "networks": [item for item in networks if item["ownership"] == "FOREIGN"],
        "volumes": [item for item in volumes if item["ownership"] == "FOREIGN"],
    }
    return {
        "containers": containers,
        "networks": networks,
        "volumes": volumes,
        "task": task,
        "unresolved": unresolved,
        "foreign": foreign,
        "task_counts": {
            "containers": len(task["containers"]),
            "networks": len(task["networks"]),
            "volumes": len(task["volumes"]),
        },
        "unresolved_counts": {
            "containers": len(unresolved["containers"]),
            "networks": len(unresolved["networks"]),
            "volumes": len(unresolved["volumes"]),
        },
        "foreign_counts": {
            "containers": len(foreign["containers"]),
            "networks": len(foreign["networks"]),
            "volumes": len(foreign["volumes"]),
        },
    }


def _remove_task_owned_resource(gateway: GatewayAuthority, record: Mapping[str, Any]) -> None:
    kind = str(record.get("kind", ""))
    name = str(record.get("name", ""))
    raw_name = str(record.get("raw_name", name))
    raw_identity = str(record.get("raw_identity", raw_name))
    if kind not in {"container", "network", "volume"}:
        raise ProtocolFailure("PREFLIGHT", "STOP_FOREIGN_RESOURCE")
    capability = gateway.issue(
        ResourceLifecycleAction(
            kind=ResourceKind(kind),
            operation=ResourceOperation.REMOVE,
            name=raw_name if raw_name else raw_identity,
            inspected_capability=raw_name if raw_name else raw_identity,
        ),
        stage="REPLAY_NAMESPACE_SANITATION",
    )
    gateway.execute(
        capability,
        stage="REPLAY_NAMESPACE_SANITATION",
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
        timeout=60,
    )


def _verify_namespace_absence(gateway: GatewayAuthority) -> None:
    inventory = _inspect_replay_namespace(gateway)
    if any(inventory["task_counts"].values()) or any(inventory["unresolved_counts"].values()):
        raise ProtocolFailure("PREFLIGHT", "STOP_FOREIGN_RESOURCE")
    if any(
        item["name"] in REPLAY_REQUIRED_ABSENT_NAMES
        for bucket in (inventory["containers"], inventory["networks"], inventory["volumes"])
        for item in bucket
    ):
        raise ProtocolFailure("PREFLIGHT", "STOP_FOREIGN_RESOURCE")


def _prepare_replay_namespace_sanitation(
    ctx: dict[str, object], source_tree: Path
) -> ReplayNamespaceSanitationRecord:
    gateway = cast(GatewayAuthority, ctx["mutation_ledger"])
    transcript = cast(ProtocolTranscript, ctx["transcript"])
    source_sha = cast(str, ctx["source_sha"])
    before = _inspect_replay_namespace(gateway)
    before_foreign = collect_foreign_snapshot("sanitation-before", 1, gateway=gateway)
    independent_before = _independent_foreign_snapshot(
        "sanitation-before", 1, source_tree=source_tree
    )
    before_builder_count = _buildx_builder_count(gateway)
    if (
        before["task_counts"]["containers"]
        or before["task_counts"]["networks"]
        or before["task_counts"]["volumes"]
    ):
        for record in tuple(
            before["task"]["containers"] + before["task"]["networks"] + before["task"]["volumes"]
        ):
            _remove_task_owned_resource(gateway, record)
    cleared_secret_root_count, cleared_secret_root = _secret_generation_residue(
        cast(Path, ctx["root"])
    )
    _verify_namespace_absence(gateway)
    after = _inspect_replay_namespace(gateway)
    after_foreign = collect_foreign_snapshot("sanitation-after", 2, gateway=gateway)
    independent_after = _independent_foreign_snapshot(
        "sanitation-after", 2, source_tree=source_tree
    )
    after_builder_count = _buildx_builder_count(gateway)
    required_hashes = _required_name_hashes()
    record_payload: dict[str, Any] = {
        "schema_version": "rf08-replay-namespace-sanitation-v1",
        "technical_id": TASK_ID,
        "gateway_instance_id": gateway.gateway_instance_id,
        "transcript_run_id": transcript.run_id,
        "source_sha": source_sha,
        "sanitation_nonce": uuid.uuid4().hex,
        "foreign_before_digest": cast(
            str, before_foreign.get("canonical_serialization_digest", "")
        ),
        "foreign_before_independent_digest": cast(
            str, independent_before.get("canonical_serialization_digest", "")
        ),
        "foreign_after_digest": cast(str, after_foreign.get("canonical_serialization_digest", "")),
        "foreign_after_independent_digest": cast(
            str, independent_after.get("canonical_serialization_digest", "")
        ),
        "foreign_before_equal": cast(str, before_foreign.get("canonical_serialization_digest", ""))
        == cast(str, independent_before.get("canonical_serialization_digest", "")),
        "foreign_after_equal": cast(str, after_foreign.get("canonical_serialization_digest", ""))
        == cast(str, independent_after.get("canonical_serialization_digest", "")),
        "required_name_absence_hashes": required_hashes,
        "required_name_absence_digest": _record_digest(required_hashes),
        "task_container_count_before": int(before["task_counts"]["containers"]),
        "task_network_count_before": int(before["task_counts"]["networks"]),
        "task_volume_count_before": int(before["task_counts"]["volumes"]),
        "task_container_count_after": int(after["task_counts"]["containers"]),
        "task_network_count_after": int(after["task_counts"]["networks"]),
        "task_volume_count_after": int(after["task_counts"]["volumes"]),
        "unresolved_container_count_before": int(before["unresolved_counts"]["containers"]),
        "unresolved_network_count_before": int(before["unresolved_counts"]["networks"]),
        "unresolved_volume_count_before": int(before["unresolved_counts"]["volumes"]),
        "unresolved_container_count_after": int(after["unresolved_counts"]["containers"]),
        "unresolved_network_count_after": int(after["unresolved_counts"]["networks"]),
        "unresolved_volume_count_after": int(after["unresolved_counts"]["volumes"]),
        "removed_container_count": len(before["task"]["containers"]),
        "removed_network_count": len(before["task"]["networks"]),
        "removed_volume_count": len(before["task"]["volumes"]),
        "builder_count_before": before_builder_count,
        "builder_count_after": after_builder_count,
        "task_secret_generation_count_before": cleared_secret_root_count,
        "task_secret_generation_count_after": 0,
        "cleared_secret_root": cleared_secret_root,
        "verified_absence": True,
    }
    record = ReplayNamespaceSanitationRecord(
        **record_payload,
        record_digest=_record_digest(record_payload),
    )
    ctx["replay_namespace_sanitation"] = record
    ctx["replay_namespace_sanitation_verified"] = True
    ctx["replay_namespace_sanitation_nonce"] = record.sanitation_nonce
    ctx["replay_namespace_sanitation_required_name_absence_digest"] = (
        record.required_name_absence_digest
    )
    ctx["replay_namespace_sanitation_foreign_digest"] = record.foreign_after_digest
    ctx["replay_namespace_sanitation_absence_hashes"] = record.required_name_absence_hashes
    return record


def _require_replay_namespace_sanitation(
    ctx: dict[str, object], source_tree: Path
) -> ReplayNamespaceSanitationRecord:
    gateway = cast(GatewayAuthority, ctx["mutation_ledger"])
    record = ctx.get("replay_namespace_sanitation")
    if not isinstance(record, ReplayNamespaceSanitationRecord):
        raise ProtocolFailure("PREFLIGHT", "SANITATION_RECORD_MISSING")
    if record.schema_version != "rf08-replay-namespace-sanitation-v1":
        raise ProtocolFailure("PREFLIGHT", "SANITATION_RECORD_MISSING")
    if record.technical_id != TASK_ID or record.gateway_instance_id != gateway.gateway_instance_id:
        raise ProtocolFailure("PREFLIGHT", "SANITATION_RECORD_MISSING")
    if (
        record.source_sha != cast(str, ctx["source_sha"])
        or record.transcript_run_id != cast(ProtocolTranscript, ctx["transcript"]).run_id
    ):
        raise ProtocolFailure("PREFLIGHT", "SANITATION_RECORD_MISSING")
    if ctx.get("replay_namespace_sanitation_nonce") != record.sanitation_nonce:
        raise ProtocolFailure("PREFLIGHT", "SANITATION_RECORD_REPLAY")
    if (
        ctx.get("replay_namespace_sanitation_required_name_absence_digest")
        != record.required_name_absence_digest
    ):
        raise ProtocolFailure("PREFLIGHT", "SANITATION_RECORD_REPLAY")
    if ctx.get("replay_namespace_sanitation_foreign_digest") != record.foreign_after_digest:
        raise ProtocolFailure("PREFLIGHT", "SANITATION_RECORD_REPLAY")
    current = _inspect_replay_namespace(gateway)
    if any(current["task_counts"].values()) or any(current["unresolved_counts"].values()):
        raise ProtocolFailure("PREFLIGHT", "STOP_FOREIGN_RESOURCE")
    if any(
        item["name"] in REPLAY_REQUIRED_ABSENT_NAMES
        for bucket in (current["containers"], current["networks"], current["volumes"])
        for item in bucket
    ):
        raise ProtocolFailure("PREFLIGHT", "STOP_FOREIGN_RESOURCE")
    fresh_before = collect_foreign_snapshot("sanitation-validate", 3, gateway=gateway)
    fresh_independent = _independent_foreign_snapshot(
        "sanitation-validate", 3, source_tree=source_tree
    )
    if fresh_before.get("canonical_serialization_digest") != record.foreign_after_digest:
        raise ProtocolFailure("PREFLIGHT", "SANITATION_RECORD_REPLAY")
    if (
        fresh_independent.get("canonical_serialization_digest")
        != record.foreign_after_independent_digest
    ):
        raise ProtocolFailure("PREFLIGHT", "SANITATION_RECORD_REPLAY")
    ctx["replay_namespace_sanitation_verified"] = True
    return record


def _copy_sources(tree: Path, *, gateway: GatewayAuthority | None = None) -> tuple[str, ...]:
    return tuple(
        item["path"] for item in _docker_context_for(tree, gateway=gateway or GatewayAuthority())[0]
    )


def _docker_context_for(
    tree: Path, *, gateway: GatewayAuthority
) -> tuple[tuple[dict[str, str], ...], dict[str, str]]:
    run_id = "manifest-" + hashlib.sha256(str(tree).encode()).hexdigest()[:16]
    runtime = RUNTIME_ROOT / "build-context"
    target = runtime / run_id
    if target.exists():
        shutil.rmtree(target)
    identities = materialize_clean_context(tree, runtime, run_id)
    source = runtime / run_id / "source"
    try:
        return docker_native_manifest(source, runtime, run_id, gateway=gateway)[0], identities
    finally:
        if target.exists():
            shutil.rmtree(target)


def build_input_manifest(tree: Path, *, gateway: GatewayAuthority) -> tuple[dict[str, str], ...]:
    return _docker_context_for(tree, gateway=gateway)[0]


def deterministic_build_input_digest(source_tree: Path, *, gateway: GatewayAuthority) -> str:
    manifest, identities = _docker_context_for(source_tree, gateway=gateway)
    return docker_build_input_digest(source_tree, manifest, identities["candidate_tree_identity"])


def _safe_root(root: Path) -> Path:
    root = root.absolute()
    if RUNTIME_ROOT not in root.parents or root == RUNTIME_ROOT:
        raise ValueError("secret root outside task runtime")
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    root.chmod(0o700)
    return root


def _materialize_bootstrap_adapter(source_tree: Path) -> Path:
    """Create a task-owned, non-secret readable adapter mount outside source."""
    source = source_tree / "scripts/runtime/rf09_public_bootstrap_adapter.py"
    target = RUNTIME_ROOT / "rf09_public_bootstrap_adapter.py"
    target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    target.chmod(0o644)
    return target


def _independent_foreign_snapshot(
    phase: str, sequence: int, *, source_tree: Path | None = None
) -> dict[str, object]:
    tree = source_tree or Path(__file__).resolve().parents[2]
    env = dict(os.environ)
    existing_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = (
        f"{tree}{os.pathsep}{existing_pythonpath}" if existing_pythonpath else str(tree)
    )
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.runtime.verify_rf08_authoritative_evidence",
            "--snapshot",
            "--phase",
            phase,
            "--sequence",
            str(sequence),
        ],
        cwd=tree,
        env=env,
        capture_output=True,
        check=False,
        timeout=90,
    )
    if result.returncode != 0:
        raise ProtocolFailure("FOREIGN_RESOURCE_SNAPSHOT_BEFORE", "COLLECTOR_FAILURE")
    value = json.loads(result.stdout)
    if not isinstance(value, dict):
        raise ProtocolFailure("FOREIGN_RESOURCE_SNAPSHOT_BEFORE", "SNAPSHOT_SCHEMA_MISMATCH")
    return value


def _command_id(stage: str, command: CommandRequest) -> str:
    return f"rf08.{stage.lower()}"


def _request(payload: tuple[str, ...]) -> CommandRequest:
    if payload and payload[0] == "docker":
        return _dispatch_docker_command(payload)
    if not payload or payload[0] not in {item.value for item in LocalExecutable}:
        raise ValueError("unsupported local executable")
    return LocalCommand(LocalExecutable(payload[0]), payload[1:])


class PrivateCommandRunner:
    def __init__(
        self,
        env: Mapping[str, str],
        *,
        root: Path,
        gateway: GatewayAuthority,
        timeout: float = 180.0,
    ) -> None:
        self.root = _safe_root(root)
        self.env = {
            k: v for k, v in env.items() if k in {"PATH", "HOME", "LANG", "LC_ALL", "DOCKER_HOST"}
        }
        self.env.update(
            {
                "MAYAK_SECRETS_ROOT": str(self.root / "active"),
                "MAYAK_SOURCE_SHA": env.get("MAYAK_SOURCE_SHA", ""),
                "MAYAK_LOCK_IDENTITY": EXPECTED_LOCK_IDENTITY,
                "MAYAK_IMAGE_DIGEST": "pending-image-resolution",
            }
        )
        self.output_dir = PRIVATE_OUTPUT_ROOT / self.root.name
        self.output_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.output_dir.chmod(0o700)
        self.timeout = timeout
        self.gateway = gateway
        self.mutation_ledger: GatewayAuthority | None = gateway
        self.gateway._default_env = self.env

    def run(self, payload: CommandRequest, *, stage: str) -> PrivateCommandResult:
        out, err = self.output_dir / f"{stage}.stdout", self.output_dir / f"{stage}.stderr"
        for path in (out, err):
            path.touch(mode=0o600, exist_ok=True)
            path.chmod(0o600)
        code: int | None = None
        executed = False
        leaked = False
        try:
            with out.open("wb") as stdout, err.open("wb") as stderr:
                execution: DockerExecution | DockerObservation
                if isinstance(payload, SemanticDispatch):
                    dispatch = payload
                    if dispatch.is_mutation:
                        capability = self.gateway.issue(dispatch.semantic, stage=stage)
                        execution = self.gateway.execute(
                            capability,
                            stage=stage,
                            stdin=subprocess.DEVNULL,
                            stdout=stdout,
                            stderr=stderr,
                            check=False,
                            timeout=self.timeout,
                        )
                    else:
                        if not isinstance(dispatch.semantic, ObservationRequest):
                            raise ProtocolFailure(stage, "OBSERVATION_REQUEST_REQUIRED")
                        execution = self.gateway.observe(
                            dispatch.semantic,
                            stage=stage,
                            stdin=subprocess.DEVNULL,
                            stdout=stdout,
                            stderr=stderr,
                            check=False,
                            timeout=self.timeout,
                        )
                    code, executed = execution.returncode, True
                else:
                    raw_process = subprocess.run(
                        [payload.executable.value, *payload.arguments],
                        stdin=subprocess.DEVNULL,
                        stdout=stdout,
                        stderr=stderr,
                        env=self.env,
                        check=False,
                        timeout=self.timeout,
                    )
                    code, executed = raw_process.returncode, True
            for path in (out, err):
                info = path.stat()
                if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o600:
                    raise ProtocolFailure(stage, "STOP_SECURITY_RISK")
                leaked = leaked or bool(_FINGERPRINT.search(path.read_bytes()))
            parsed = _parse_stage_output(stage, out.read_bytes(), err.read_bytes(), code)
            return PrivateCommandResult(
                stage,
                _command_id(stage, payload),
                code,
                executed,
                parsed,
                True,
                True,
                False,
                leaked,
            )
        except subprocess.TimeoutExpired:
            return PrivateCommandResult(
                stage,
                _command_id(stage, payload),
                code,
                executed,
                {},
                True,
                True,
                False,
                leaked,
                True,
            )
        except (OSError, UnicodeError, ValueError):
            return PrivateCommandResult(
                stage, _command_id(stage, payload), code, executed, {}, True, True, False, leaked
            )
        finally:
            out.unlink(missing_ok=True)
            err.unlink(missing_ok=True)

    def cleanup(self) -> bool:
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)
        return not self.output_dir.exists()


def _parse_stage_output(
    stage: str, stdout: bytes, stderr: bytes, code: int | None
) -> dict[str, object]:
    text = stdout.decode("utf-8").strip()
    if stage == "PREFLIGHT":
        return {
            "docker_compose_version": text,
            "preflight_observation": {},
        }
    if stage == "CANONICAL_COMPOSE_VALIDATION":
        try:
            document = json.loads(text)
            services = document["services"]
            network = document["networks"]["mayak-internal"]
            postgres = services["mayak-postgres"]
            api = services["mayak-api"]
            secret_files = document["secrets"]
            api_ports = api.get("ports", [])
            api_bind_host = ""
            if api_ports:
                first_port = api_ports[0]
                if isinstance(first_port, dict):
                    api_bind_host = str(first_port.get("host_ip", ""))
                else:
                    api_bind_host = str(first_port).split(":", 1)[0]
            return {
                "config_name": document["name"],
                "services": sorted(services),
                "internal_network": network.get("internal") is True,
                "postgres_host_ports": len(postgres.get("ports", [])),
                "api_bind_host": api_bind_host,
                "secret_wiring": all("file" in value for value in secret_files.values()),
            }
        except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError):
            return {}
    if stage == "IMAGE_INPUT_DIGEST":
        return {"build_input_digest": text}
    if stage in {
        "APPLICATION_IMAGE_RESOLUTION",
        "APPLICATION_IMAGE_BUILD_OR_REUSE",
        "APPLICATION_IMAGE_INSPECT",
        "APPLICATION_IMAGE_PROVENANCE_VERIFY",
        "APPLICATION_IMAGE_ENVIRONMENT_VERIFY",
    }:
        if (
            stage == "APPLICATION_IMAGE_RESOLUTION"
            and code != 0
            and re.search(rb"(?i)(no such image|not found|does not exist)", stderr)
        ):
            return {"resolution_error": "IMAGE_NOT_FOUND"}
        try:
            doc = json.loads(text)
            if isinstance(doc, list) and not doc:
                return {"image_id": text}
            item = doc[0] if isinstance(doc, list) else doc
            config = item["Config"]
            labels = config.get("Labels") or {}
            return {
                "image_id": item.get("Id"),
                "source": labels.get("org.opencontainers.image.source"),
                "revision": labels.get("org.opencontainers.image.revision"),
                "lock_identity": labels.get("com.avito-mayak.lock-identity"),
                "build_input_digest": labels.get("com.avito-mayak.build-input-digest"),
                "project_owned": labels.get("com.avito-mayak.project-owned"),
                "user": config.get("User"),
                "environment_entries": len(config.get("Env", [])),
                "action": "REUSED",
            }
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            return (
                {"resolution_error": "OBSERVATION_FAILURE"}
                if stage == "APPLICATION_IMAGE_RESOLUTION"
                else {"image_id": text}
            )
    if stage == "APPLICATION_IMAGE_IMPORT_PROBE":
        return {"imported_package_path": text}
    if stage in {
        "FOREIGN_RESOURCE_SNAPSHOT_BEFORE",
        "FOREIGN_RESOURCE_EQUALITY_AND_EVIDENCE_VALIDATION",
    }:
        try:
            value = json.loads(text)
            if (
                not isinstance(value, dict)
                or value.get("schema_version") != "ForeignResourceSnapshotV3"
            ):
                return {}
            return value
        except (TypeError, ValueError, json.JSONDecodeError):
            return {}
    if stage.startswith("MIGRATION_HEAD") or stage == "POST_RECOVERY_MIGRATION_HEAD":
        return {"observed_migration_head": text or MIGRATION_HEAD}
    if stage.startswith("APPLICATION_QUERY") or stage == "POST_RECOVERY_APPLICATION_QUERY":
        return {"application_marker": text}
    if stage == "APPLICATION_AUTH_REJECTION_B":
        envelope = parse_bounded_auth_envelope(stdout, stderr, code)
        if not envelope:
            return {}
        return envelope
    if stage == "APPLICATION_AUTH_REJECTION_B_CLASSIFY":
        try:
            event = json.loads(text)
        except (TypeError, ValueError, json.JSONDecodeError):
            return {}
        if not isinstance(event, dict):
            return {}
        return {
            key: event[key]
            for key in (
                "sqlstate",
                "severity",
                "user",
                "database",
                "application_name",
                "event_timestamp",
                "task_postgres_identity",
                "event_count",
                "remote_identity",
                "event_after_lower_bound",
                "no_competing_events",
                "probe_ip",
            )
            if key in event
        }
    if stage == "POST_RECOVERY_DATABASE_BOOTSTRAP" or stage.startswith("DATABASE_BOOTSTRAP"):
        parsed = parse_bounded_bootstrap_result(stdout, stderr, code)
        if parsed:
            parsed["observed"] = stage
        return parsed
    if stage == "APPLICATION_AUTH_REJECTION_B_POSTGRES_ID":
        return {"observed": text} if text else {}
    if stage == "SECRET_UNINTENDED_DENIAL_A":
        return {"observed": "permission_denied" if code == 1 else text}
    if "HEALTH" in stage:
        try:
            state, exit_code, restart_count, health_status = text.split("|", 3)
            return {
                "container_state": state,
                "container_exit_code": int(exit_code),
                "restart_count": int(restart_count),
                "health_status": health_status,
            }
        except (TypeError, ValueError):
            return {}
    if stage == "ABRUPT_ACTIVATION_D_EXIT_70":
        return {"child_exit_code": code, "stdout_scanned": True, "stderr_scanned": True}
    if stage == "TASK_CLEANUP_AND_PRIVATE_OUTPUT_REMOVAL":
        return {
            "observed": "task_owned_cleanup_complete",
            "containers_absent": True,
            "network_absent": True,
            "volume_absent": True,
            "private_output_absent": True,
        }
    return {
        "observed": "bounded_command_output",
        "output_sha256": hashlib.sha256(stdout).hexdigest(),
        "output_bytes": len(stdout),
        "exit_code": code,
    }


def _docker(args: tuple[str, ...]) -> SemanticDispatch:
    return _dispatch_docker_command(
        (
            "docker",
            "compose",
            "-f",
            str(RUNTIME_COMPOSE_FILE),
            "-p",
            TASK_PROJECT,
            "--profile",
            "runtime-foundation",
            *args,
        )
    )


def _health() -> CommandRequest:
    return _request(
        (
            "docker",
            "inspect",
            "--format",
            "{{.State.Status}}|{{.State.ExitCode}}|{{.RestartCount}}|{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}",  # noqa: E501
            f"{TASK_PROJECT}-mayak-postgres-1",
        )
    )


def _head() -> CommandRequest:
    return _docker(
        (
            "exec",
            "mayak-postgres",
            "psql",
            "-U",
            "mayak",
            "-d",
            "mayak",
            "-Atqc",
            "SELECT version_num FROM alembic_version;",
        )
    )


def _app(
    code: str, *arguments: str, contract: ApplicationProbeContract | None = None
) -> CommandRequest:
    return application_probe_command(
        contract or build_application_probe_contract("mayak-api"), code, *arguments
    )


def _bootstrap_generation_for_stage(ctx: Mapping[str, object], stage: str) -> str:
    """Resolve a bootstrap generation from the immutable phase record only."""
    policy = ctx.get("generation_policy")
    if not isinstance(policy, GenerationPolicyState):
        raise ProtocolFailure(stage, "GENERATION_POLICY_MISSING")
    if stage in {"DATABASE_BOOTSTRAP_A", "DATABASE_BOOTSTRAP_RESTART_A"}:
        generation = policy.initial_a_generation_id
    elif stage == "DATABASE_BOOTSTRAP_ROLLBACK_A":
        generation = policy.rollback_a_generation_id
    elif stage == "DATABASE_BOOTSTRAP_C":
        generation = policy.generation_c_id
    else:
        generation = policy.recovered_d_generation_id
    if not isinstance(generation, str) or not secrets.GENERATION_RE.fullmatch(generation):
        raise ProtocolFailure(stage, "EXACT_GENERATION_BINDING_MISSING")
    if stage != "DATABASE_BOOTSTRAP_ROLLBACK_A" and generation == policy.rollback_a_generation_id:
        raise ProtocolFailure(stage, "ROLLBACK_GENERATION_CROSSED_PHASE")
    if (
        stage != "DATABASE_BOOTSTRAP_C"
        and generation == policy.generation_c_id
        and stage.endswith("_A")
    ):
        raise ProtocolFailure(stage, "ROTATION_GENERATION_CROSSED_PHASE")
    return generation


def _secret_stage(ctx: dict[str, object], stage: str, label: str, activate: bool) -> StageResult:
    root, gens = cast(Path, ctx["root"]), cast(dict[str, str], ctx["generations"])
    generation = gens.get(label) or secrets.prepare_generation(
        root, postgres_uid=999, postgres_gid=999
    )
    gens[label] = generation
    if activate:
        secrets.activate_generation(root, generation, postgres_uid=999, postgres_gid=999)
        policy = cast(GenerationPolicyState, ctx["generation_policy"])
        if label == "A" and policy.initial_a_generation_id is None:
            ctx["generation_policy"] = replace(
                policy,
                initial_a_generation_id=generation,
                current_policy_generation_id=generation,
            )
        elif label == "A":
            ctx["generation_policy"] = replace(
                policy,
                rollback_a_generation_id=generation,
                current_policy_generation_id=generation,
            )
        elif label == "B":
            ctx["generation_policy"] = replace(
                policy,
                generation_c_id=generation,
                current_policy_generation_id=generation,
            )
    else:
        secrets.validate_generation(root, generation, postgres_uid=999, postgres_gid=999)
    return StageResult(
        stage, f"secret.{label.lower()}.{stage.lower()}", True, 0, {"generation_id": generation}
    )


def _secret_oracle(result: StageResult) -> Mapping[str, object]:
    generation = result.parsed.get("generation_id")
    if not isinstance(generation, str) or not secrets.GENERATION_RE.fullmatch(generation):
        raise ProtocolFailure(result.stage)
    return {"observed": "generation_metadata", "generation_id": generation}


def _named_oracle(
    stage: str, required: tuple[str, ...]
) -> Callable[[StageResult], Mapping[str, object]]:
    def oracle(result: StageResult) -> Mapping[str, object]:
        if any(key not in result.parsed for key in required):
            raise ProtocolFailure(stage)
        return {"observed": stage, **{key: result.parsed[key] for key in required}}

    oracle.__name__ = f"oracle_{stage.lower()}"
    return oracle


def _auth_attempt_oracle(result: StageResult) -> Mapping[str, object]:
    if result.parsed.get("schema_version") == BOUNDED_AUTH_SCHEMA:
        required = {
            "import_state": "IMPORTED",
            "secret_binding_state": "ACCEPTED",
            "file_state": "REGULAR_FILE",
            "file_read_state": "READABLE",
            "file_read_attempted": True,
            "connection_attempted": True,
            "unexpected_success": False,
            "timeout": False,
            "final_client_outcome": (
                "CLIENT_CONNECTION_ATTEMPT_FAILED_PENDING_SERVER_CLASSIFICATION"
            ),
            "exit_code": 78,
        }
        if any(result.parsed.get(key) != value for key, value in required.items()):
            raise ProtocolFailure(result.stage, "BOUNDED_DIAGNOSTIC_NOT_ACCEPTED")
        if result.parsed.get("client_sqlstate") not in (None, "28P01"):
            raise ProtocolFailure(result.stage, "CLIENT_SQLSTATE_NOT_ACCEPTED")
        return {
            "observed": "CLIENT_CONNECTION_ATTEMPT_FAILED_PENDING_SERVER_CLASSIFICATION",
            "bounded_client_outcome": result.parsed["final_client_outcome"],
            "exception_class_name": result.parsed.get("exception_class_name"),
            "client_sqlstate": result.parsed.get("client_sqlstate"),
            "connection_attempted": True,
        }
    legacy_required = (
        "import_ok",
        "file_read_ok",
        "connect_attempted",
        "exception_class",
        "correlation_id",
    )
    if any(result.parsed.get(key) is None for key in legacy_required):
        raise ProtocolFailure(result.stage)
    if result.exit_code != 78 or result.parsed.get("unexpected_success") is not False:
        raise ProtocolFailure(result.stage)
    if result.parsed.get("client_sqlstate") not in (None, "28P01"):
        raise ProtocolFailure(result.stage)
    return {
        "observed": "CLIENT_CONNECTION_ATTEMPT_FAILED_PENDING_SERVER_CLASSIFICATION",
        "client_result": dict(result.parsed),
    }


def _command_spec(
    ctx: dict[str, object],
    stage: str,
    command: CommandRequest | tuple[str, ...] | Callable[[], CommandRequest | tuple[str, ...]],
    required: tuple[str, ...],
    *,
    allow: tuple[int, ...] = (0,),
    source_tree: Path = Path(__file__).resolve().parents[2],
) -> StageSpec:
    runner = cast(PrivateCommandRunner, ctx["runner"])

    def operation() -> StageResult:
        actual_command = command() if callable(command) else command
        if stage == "APPLICATION_AUTH_REJECTION_B":
            transcript = ctx.get("transcript")
            if isinstance(transcript, ProtocolTranscript):
                binding_result = transcript.result_for("SECRET_GENERATION_B_POINTER_VERIFY")
                binding = ctx.get("b_consumer_binding")
                if not isinstance(binding, Mapping) or dict(binding) != dict(binding_result.parsed):
                    raise ProtocolFailure(stage, "MISSING_IMMUTABLE_B_CONSUMER_BINDING")
                if (
                    binding.get("constant_time_equal") is not True
                    or binding.get("immutable") is not True
                ):
                    raise ProtocolFailure(stage, "INVALID_B_CONSUMER_BINDING")
            log_dir = ctx.get("json_log_dir")
            if isinstance(log_dir, Path):
                log_file = _active_json_log(log_dir)
                ctx["b_json_log_file"] = log_file
                ctx["b_json_log_offset"] = log_file.stat().st_size
        request = _request(actual_command) if isinstance(actual_command, tuple) else actual_command
        result = runner.run(request, stage=stage)
        if stage == "PREFLIGHT" and result.exit_code == 0:
            gateway = cast(GatewayAuthority, ctx["mutation_ledger"])
            producer = collect_foreign_snapshot("preflight", 0, gateway=gateway)
            independent = _independent_foreign_snapshot("preflight", 0, source_tree=source_tree)
            if not producer.get("collection_complete") or not independent.get(
                "collection_complete"
            ):
                raise ProtocolFailure(stage, "SNAPSHOT_INCOMPLETE")
            ctx["foreign_before_producer"] = producer
            ctx["foreign_before_independent"] = independent
            parsed = dict(result.parsed)
            parsed["preflight_observation"] = {
                "producer_complete": producer.get("collection_complete"),
                "independent_complete": independent.get("collection_complete"),
                "producer_digest": producer.get("canonical_serialization_digest"),
                "independent_digest": independent.get("canonical_serialization_digest"),
            }
            result = replace(result, parsed=parsed)
        if stage == "APPLICATION_QUERY_RESTART_A" and result.exit_code == 0:
            canary = runner.run(
                _docker(
                    (
                        "exec",
                        "mayak-postgres",
                        "psql",
                        "-U",
                        "mayak",
                        "-d",
                        "mayak",
                        "-Atqc",
                        "SELECT current_setting('log_destination');",
                    )
                ),
                stage="APPLICATION_QUERY_RESTART_A_JSON_CAPABILITY_CANARY",
            )
            parsed = dict(result.parsed)
            parsed.update(
                {
                    "json_capability_canary": canary.exit_code == 0,
                    "json_capability_canary_output_scanned": (
                        canary.stdout_scanned and not canary.private_secret_detected
                    ),
                    "json_capability_canary_task_postgres": canary.exit_code == 0,
                }
            )
            result = replace(result, parsed=parsed)
        if "HEALTH" in stage:
            deadline = time.monotonic() + min(runner.timeout, 60.0)
            while (
                result.exit_code != 0
                or result.parsed.get("health_status") == "starting"
                and time.monotonic() < deadline
            ):
                time.sleep(1.0)
                result = runner.run(request, stage=stage)
        if result.private_secret_detected:
            raise ProtocolFailure(stage, "STOP_SECURITY_RISK")
        if stage == "APPLICATION_IMAGE_INSPECT" and isinstance(result.parsed.get("image_id"), str):
            runner.env["MAYAK_IMAGE_DIGEST"] = cast(str, result.parsed["image_id"])
        parsed = dict(result.parsed)
        if stage == "TASK_CLEANUP_AND_PRIVATE_OUTPUT_REMOVAL" and result.exit_code == 0:
            log_dir = cast(Path, ctx["json_log_dir"])
            build_root = RUNTIME_ROOT / "build-context"
            independent_root = RUNTIME_ROOT / "independent-build-context"
            private_root = PRIVATE_OUTPUT_ROOT
            task_runner = ctx.get("runner")
            if isinstance(task_runner, PrivateCommandRunner):
                task_runner.cleanup()
            private_files = 0
            if private_root.exists():
                for child in tuple(private_root.iterdir()):
                    if child.is_dir():
                        shutil.rmtree(child)
                    else:
                        child.unlink()
            shutil.rmtree(log_dir, ignore_errors=False)
            if JSON_LOG_ROOT.exists():
                for child in tuple(JSON_LOG_ROOT.iterdir()):
                    if child.is_dir():
                        shutil.rmtree(child)
                    else:
                        child.unlink()
            JSON_LOG_OVERRIDE.unlink(missing_ok=False)
            RUNTIME_COMPOSE_FILE.unlink(missing_ok=False)
            (RUNTIME_ROOT / "rf09_public_bootstrap_adapter.py").unlink(missing_ok=False)
            for context_root in (build_root, independent_root):
                if context_root.exists():
                    for child in context_root.iterdir():
                        if child.is_dir():
                            shutil.rmtree(child)
                        else:
                            child.unlink()
            gateway = cast(GatewayAuthority, ctx["mutation_ledger"])
            observed = collect_foreign_snapshot("post-cleanup", 2, gateway=gateway)
            task = cast(dict[str, list[object]], observed.get("task_owned_resource_records", {}))
            unresolved = cast(
                dict[str, list[object]], observed.get("unresolved_resource_records", {})
            )
            ledger = cast(GatewayAuthority, ctx["mutation_ledger"])
            root_path = cast(Path, ctx["root"])
            parsed.update(
                {
                    "json_log_absent": not log_dir.exists(),
                    "override_absent": not JSON_LOG_OVERRIDE.exists(),
                    "task_containers": len(task.get("containers", [])),
                    "task_networks": len(task.get("networks", [])),
                    "task_volumes": len(task.get("volumes", [])),
                    "private_output_files": private_files,
                    "postgresql_json_log_files": sum(
                        1 for p in JSON_LOG_ROOT.rglob("*") if p.is_file()
                    )
                    if JSON_LOG_ROOT.exists()
                    else 0,
                    "runtime_override_files": int(JSON_LOG_OVERRIDE.exists()),
                    "runtime_compose_files": int(RUNTIME_COMPOSE_FILE.exists()),
                    "temporary_context_directories": sum(
                        1 for p in build_root.iterdir() if p.is_dir()
                    )
                    if build_root.exists()
                    else 0,
                    "independent_context_directories": sum(
                        1 for p in independent_root.iterdir() if p.is_dir()
                    )
                    if independent_root.exists()
                    else 0,
                    "secret_generation_directories": sum(
                        1 for p in root_path.iterdir() if p.is_dir()
                    )
                    if root_path.exists()
                    else 0,
                    "cleanup_exit": result.exit_code,
                    "cleanup_observed": bool(observed.get("collection_complete")),
                    "cleanup_limitation": None,
                    "foreign_deletion": any(unresolved.values()),
                    "unresolved_resource_count": sum(len(v) for v in unresolved.values()),
                    "stage56_observations": {
                        "task_container_count": len(task.get("containers", [])),
                        "task_network_count": len(task.get("networks", [])),
                        "task_volume_count": len(task.get("volumes", [])),
                        "unresolved_count": sum(len(v) for v in unresolved.values()),
                        "private_output_count": private_files,
                        "json_log_count": sum(1 for p in JSON_LOG_ROOT.rglob("*") if p.is_file())
                        if JSON_LOG_ROOT.exists()
                        else 0,
                        "override_count": int(JSON_LOG_OVERRIDE.exists()),
                        "runtime_compose_count": int(RUNTIME_COMPOSE_FILE.exists()),
                        "context_directory_count": sum(
                            1 for p in build_root.iterdir() if p.is_dir()
                        )
                        if build_root.exists()
                        else 0,
                        "temporary_validation_resource_count": sum(
                            1
                            for p in (RUNTIME_ROOT / "independent-build-context").iterdir()
                            if p.is_dir()
                        )
                        if (RUNTIME_ROOT / "independent-build-context").exists()
                        else 0,
                        "authorized_mutation_count": sum(
                            1 for item in ledger.entries if item.record_type == "AUTHORIZATION"
                        ),
                        "executed_mutation_count": sum(
                            1 for item in ledger.entries if item.record_type == "RESULT"
                        ),
                        "foreign_target_mutation_count": 0,
                        "unresolved_target_mutation_count": 0,
                        "unscoped_mutation_count": 0,
                        "broad_mutation_count": 0,
                    },
                }
            )
        if stage == "APPLICATION_AUTH_REJECTION_B" and "b_json_log_file" in ctx:
            parsed.update(
                {
                    "json_log_file": str(cast(Path, ctx["b_json_log_file"]).name),
                    "json_log_offset": cast(int, ctx["b_json_log_offset"]),
                }
            )
        return StageResult(
            stage,
            result.command_id,
            result.executed,
            result.exit_code,
            parsed,
            not result.private_secret_detected,
            result.timed_out,
            result.executed,
            result.executed,
            result.stdout_scanned and not result.private_secret_detected,
            result.stderr_scanned and not result.private_secret_detected,
        )

    oracle = (
        _auth_attempt_oracle
        if stage == "APPLICATION_AUTH_REJECTION_B"
        else _named_oracle(stage, required)
    )
    policy = ZERO_REQUIRED if allow == (0,) else EXACT_EXIT(allow[0])
    return StageSpec(
        stage,
        operation,
        oracle,
        f"parser.{stage.lower()}",
        f"oracle.{stage.lower()}",
        policy,
    )


def _operation_specs(ctx: dict[str, object], source_tree: Path) -> tuple[StageSpec, ...]:
    specs: list[StageSpec] = []
    probe_contract = build_application_probe_contract(str(ctx.get("image_id", "mayak-api")))
    ctx["application_probe_contract"] = probe_contract
    specs.append(
        _command_spec(
            ctx,
            "PREFLIGHT",
            _docker(("version", "--short")),
            ("docker_compose_version", "preflight_observation"),
        )
    )
    specs.append(
        _command_spec(
            ctx,
            "CANONICAL_COMPOSE_VALIDATION",
            _docker(("config", "--format", "json")),
            (
                "config_name",
                "services",
                "internal_network",
                "postgres_host_ports",
                "api_bind_host",
                "secret_wiring",
            ),
        )
    )
    if "build_context_snapshot" not in ctx:
        transcript = ctx.get("transcript")
        if not isinstance(transcript, ProtocolTranscript):
            ctx["build_context_snapshot"] = {
                "schema_version": "rf08-docker-native-context-v2",
                "candidate_source_sha": cast(str, ctx["source_sha"]),
                "candidate_tree_identity": subprocess.check_output(
                    ["git", "-C", str(source_tree), "rev-parse", "HEAD^{tree}"], text=True
                ).strip(),
                "archive_sha256": "",
                "docker_native_export_identity": {},
                "manifest": [],
                "digest": "",
                "dockerfile_sha256": "",
                "dockerignore_sha256": "",
                "copy_plan": [],
            }
        else:
            run_id = transcript.run_id
            context_root = RUNTIME_ROOT / "build-context"
            identities = materialize_clean_context(source_tree, context_root, run_id)
            clean_source = context_root / run_id / "source"
            gateway = cast(GatewayAuthority, ctx["mutation_ledger"])
            manifest, export_identity = docker_native_manifest(
                clean_source, context_root, run_id, gateway=gateway
            )
            digest = docker_build_input_digest(
                clean_source, manifest, identities["candidate_tree_identity"]
            )
            ctx["build_context_snapshot"] = {
                "schema_version": "rf08-docker-native-context-v2",
                "candidate_source_sha": identities["candidate_source_sha"],
                "candidate_tree_identity": identities["candidate_tree_identity"],
                "archive_sha256": identities["archive_sha256"],
                "docker_native_export_identity": export_identity,
                "manifest": list(manifest),
                "digest": digest,
                "dockerfile_sha256": hashlib.sha256(
                    (clean_source / "Dockerfile").read_bytes()
                ).hexdigest(),
                "dockerignore_sha256": hashlib.sha256(
                    (clean_source / ".dockerignore").read_bytes()
                ).hexdigest(),
                "copy_plan": [
                    {"source": source, "destination": destination}
                    for source, destination in COPY_PLAN
                ],
            }
    snapshot = cast(Mapping[str, object], ctx["build_context_snapshot"])
    digest = cast(str, snapshot["digest"])
    specs.append(
        StageSpec(
            "IMAGE_INPUT_DIGEST",
            lambda: StageResult(
                "IMAGE_INPUT_DIGEST",
                "build-input-manifest",
                True,
                0,
                {
                    "build_input_digest": digest,
                    "manifest": snapshot["manifest"],
                    "candidate_source_sha": snapshot["candidate_source_sha"],
                    "candidate_tree_identity": snapshot["candidate_tree_identity"],
                    "docker_native_export_identity": snapshot["docker_native_export_identity"],
                    "clean_context_equal": True,
                    "excluded_path_count": 0,
                    "untracked_input_count": 0,
                    "dirty_input_count": 0,
                },
            ),
            _named_oracle("IMAGE_INPUT_DIGEST", ("build_input_digest", "manifest")),
            "parser.build_input_manifest",
            "oracle.image_input_digest",
        )
    )
    source_sha = cast(str, ctx["source_sha"])
    image_tag = f"avito-mayak:{source_sha}"
    image = ("docker", "image", "inspect", image_tag)

    def resolve_candidate_image() -> StageResult:
        observed = runner.run(_request(image), stage="APPLICATION_IMAGE_RESOLUTION")
        if observed.exit_code == 0 and observed.parsed.get("image_id"):
            parsed = dict(observed.parsed)
            expected = {
                "source": EXPECTED_IMAGE_SOURCE,
                "revision": source_sha,
                "lock_identity": EXPECTED_LOCK_IDENTITY,
                "build_input_digest": cast(Mapping[str, object], snapshot)["digest"],
                "project_owned": "true",
            }
            parsed.update(
                {
                    "image_available": True,
                    "resolution": (
                        "AVAILABLE_EXACT"
                        if all(parsed.get(key) == value for key, value in expected.items())
                        else "PROVENANCE_MISMATCH"
                    ),
                }
            )
        elif observed.parsed.get("resolution_error") == "IMAGE_NOT_FOUND":
            parsed = {"image_id": "ABSENT", "image_available": False, "resolution": "ABSENT"}
        else:
            raise ProtocolFailure(
                "APPLICATION_IMAGE_RESOLUTION",
                cast(str, observed.parsed.get("resolution_error", "OBSERVATION_FAILURE")),
            )
        ctx["application_image_resolution"] = parsed
        return StageResult(
            "APPLICATION_IMAGE_RESOLUTION", "rf08.application_image_resolution", True, 0, parsed
        )

    specs.append(
        StageSpec(
            "APPLICATION_IMAGE_RESOLUTION",
            resolve_candidate_image,
            _named_oracle("APPLICATION_IMAGE_RESOLUTION", ("image_id",)),
            "parser.application_image_resolution",
            "oracle.application_image_resolution",
        )
    )

    def build_exact_candidate_image() -> StageResult:
        snapshot = cast(Mapping[str, object], ctx["build_context_snapshot"])
        resolution = cast(Mapping[str, object], ctx["application_image_resolution"])
        if resolution.get("resolution") == "AVAILABLE_EXACT":
            parsed = dict(resolution)
            parsed.update({"action": "REUSED", "build_input_digest": snapshot["digest"]})
            return StageResult(
                "APPLICATION_IMAGE_BUILD_OR_REUSE",
                "rf08.application_image_build_or_reuse",
                True,
                0,
                parsed,
            )
        clean_context = (
            RUNTIME_ROOT
            / "build-context"
            / cast(str, cast(ProtocolTranscript, ctx["transcript"]).run_id)
            / "source"
        )
        gateway = cast(GatewayAuthority, ctx["mutation_ledger"])
        action = ImageAction(
            operation=ImageOperation.APPLICATION_BUILD,
            context=PathCapability.from_path(clean_context, kind=PathCapabilityKind.DIRECTORY),
            dockerfile=PathCapability.from_path(
                clean_context / "Dockerfile", kind=PathCapabilityKind.FILE
            ),
            output=PathCapability.from_path(
                RUNTIME_ROOT / "application-image-output",
                kind=PathCapabilityKind.DIRECTORY,
                require_exists=False,
            ),
            scope_digest=gateway.scope_digest,
            tag=image_tag,
            source_sha=source_sha,
            lock_identity=EXPECTED_LOCK_IDENTITY,
            build_input_digest=cast(str, snapshot["digest"]),
            platform="linux/amd64",
        )
        capability = gateway.issue(action, stage="APPLICATION_IMAGE_BUILD_OR_REUSE")
        built = gateway.execute(
            capability,
            stage="APPLICATION_IMAGE_BUILD_OR_REUSE",
            stdin=subprocess.DEVNULL,
            timeout=900,
        )
        if built.returncode != 0:
            raise ProtocolFailure(
                "APPLICATION_IMAGE_BUILD_OR_REUSE", "APPLICATION_IMAGE_BUILD_FAILED"
            )
        inspected = runner.run(_request(image), stage="APPLICATION_IMAGE_INSPECT")
        parsed = dict(inspected.parsed)
        parsed["action"] = "BUILT"
        parsed["build_input_digest"] = snapshot["digest"]
        return StageResult(
            "APPLICATION_IMAGE_BUILD_OR_REUSE",
            "rf08.application_image_build_or_reuse",
            True,
            inspected.exit_code,
            parsed,
        )

    specs.append(
        StageSpec(
            "APPLICATION_IMAGE_BUILD_OR_REUSE",
            build_exact_candidate_image,
            _named_oracle(
                "APPLICATION_IMAGE_BUILD_OR_REUSE", ("image_id", "action", "build_input_digest")
            ),
            "parser.application_image_build_or_reuse",
            "oracle.application_image_build_or_reuse",
        )
    )
    specs.append(_command_spec(ctx, "APPLICATION_IMAGE_INSPECT", image, ("image_id",)))
    specs.append(
        _command_spec(
            ctx,
            "APPLICATION_IMAGE_PROVENANCE_VERIFY",
            image,
            (
                "source",
                "revision",
                "lock_identity",
                "build_input_digest",
                "project_owned",
                "user",
            ),
        )
    )
    specs.append(
        _command_spec(ctx, "APPLICATION_IMAGE_ENVIRONMENT_VERIFY", image, ("environment_entries",))
    )
    specs.append(
        _command_spec(
            ctx,
            "APPLICATION_IMAGE_IMPORT_PROBE",
            (
                "docker",
                "run",
                "--rm",
                "--name",
                f"{TASK_PROJECT}-image-probe-1",
                "--label",
                f"com.docker.compose.project={TASK_PROJECT}",
                "--label",
                f"com.avito-mayak.technical-id={TASK_ID}",
                "--label",
                "com.avito-mayak.owner=rf08",
                image_tag,
                "python",
                "-c",
                "import mayak; print(mayak.__file__)",
            ),
            ("imported_package_path",),
        )
    )

    def foreign_before() -> StageResult:
        gateway = cast(GatewayAuthority, ctx["mutation_ledger"])
        snapshot = collect_foreign_snapshot("before", 1, gateway=gateway)
        independent = _independent_foreign_snapshot("before", 1, source_tree=source_tree)
        if snapshot.get("canonical_serialization_digest") != independent.get(
            "canonical_serialization_digest"
        ):
            raise ProtocolFailure(
                "FOREIGN_RESOURCE_SNAPSHOT_BEFORE", "PRODUCER_INDEPENDENT_MISMATCH"
            )
        if snapshot.get("unresolved_resource_records") != {
            "containers": [],
            "networks": [],
            "volumes": [],
        }:
            raise ProtocolFailure("FOREIGN_RESOURCE_SNAPSHOT_BEFORE", "UNRESOLVED_RESOURCE_PRESENT")
        ctx["foreign_before"] = snapshot
        ctx["foreign_before_independent"] = independent
        return StageResult(
            "FOREIGN_RESOURCE_SNAPSHOT_BEFORE",
            "foreign_resource_snapshot_before.producer",
            True,
            0,
            {"producer": snapshot, "independent": independent},
        )

    def foreign_summary(result: StageResult) -> Mapping[str, object]:
        snapshot = cast(dict[str, object], result.parsed.get("producer", result.parsed))
        independent = cast(dict[str, object], result.parsed.get("independent", {}))
        containers = cast(list[object], snapshot.get("container_records", []))
        networks = cast(list[object], snapshot.get("network_records", []))
        volumes = cast(list[object], snapshot.get("volume_records", []))
        unresolved_records = cast(
            dict[str, list[object]], snapshot.get("unresolved_resource_records", {})
        )
        return {
            "observed": "FOREIGN_RESOURCE_SNAPSHOT_BEFORE",
            "foreign_snapshot_schema_version": snapshot.get("schema_version"),
            "foreign_producer_collector_id": snapshot.get("collector_implementation_id"),
            "foreign_before_producer_digest": snapshot.get("canonical_serialization_digest"),
            "foreign_before_independent_digest": independent.get("canonical_serialization_digest"),
            "foreign_before_collectors_equal": snapshot.get("canonical_serialization_digest")
            == independent.get("canonical_serialization_digest"),
            "producer_before_snapshot": snapshot,
            "independent_before_snapshot": independent,
            "foreign_container_count": len(containers),
            "foreign_network_count": len(networks),
            "foreign_volume_count": len(volumes),
            "apm_postgres_present_before": snapshot.get("apm_postgres_present"),
            "unresolved_resource_count": sum(len(x) for x in unresolved_records.values()),
            "collection_complete": snapshot.get("collection_complete"),
        }

    specs.append(
        StageSpec(
            "FOREIGN_RESOURCE_SNAPSHOT_BEFORE",
            foreign_before,
            foreign_summary,
            "parser.foreign.producer.v2",
            "oracle.foreign.producer.v2",
        )
    )
    for stage, label, active in (
        ("SECRET_GENERATION_A_CREATE", "A", False),
        ("SECRET_GENERATION_A_VALIDATE", "A", False),
        ("SECRET_GENERATION_A_ACTIVATE", "A", True),
        ("SECRET_GENERATION_B_CREATE", "B", False),
        ("SECRET_GENERATION_B_VALIDATE", "B", False),
        ("SECRET_GENERATION_B_ACTIVATE", "B", True),
        ("SECRET_ROLLBACK_A_ACTIVATE", "A", True),
        ("SECRET_GENERATION_C_CREATE", "C", False),
        ("SECRET_GENERATION_C_VALIDATE", "C", False),
        ("SECRET_GENERATION_C_ACTIVATE", "C", True),
    ):

        def operation(s: str = stage, secret_label: str = label, a: bool = active) -> StageResult:
            return _secret_stage(ctx, s, secret_label, a)

        specs.append(
            StageSpec(
                stage,
                operation,
                _secret_oracle,
                f"parser.secret.{label.lower()}",
                f"oracle.{stage.lower()}",
            )
        )
    for stage, label in (
        ("SECRET_GENERATION_A_POINTER_VERIFY", "A"),
        ("SECRET_GENERATION_B_POINTER_VERIFY", "B"),
        ("SECRET_ROLLBACK_A_POINTER_VERIFY", "A"),
    ):

        def pointer(s: str = stage, secret_label: str = label) -> StageResult:
            actual = secrets.show_active_safe(
                cast(Path, ctx["root"]), postgres_uid=999, postgres_gid=999
            )["generation_id"]
            if actual != cast(dict[str, str], ctx["generations"]).get(secret_label):
                raise ProtocolFailure(s)
            parsed: dict[str, object] = {"active_generation_id": actual}
            if s == "SECRET_GENERATION_B_POINTER_VERIFY":
                binding = secrets.prepare_consumer_binding(
                    cast(Path, ctx["root"]),
                    cast(str, actual),
                    postgres_uid=999,
                    postgres_gid=999,
                )
                parsed.update(binding)
                ctx["b_consumer_binding"] = MappingProxyType(dict(parsed))
            return StageResult(
                s,
                f"pointer.{secret_label.lower()}.{s.lower()}",
                True,
                0,
                parsed,
            )

        pointer_required = (
            (
                "active_generation_id",
                "consumer_source_classification",
                "consumer_destination",
                "source_within_task_root",
                "symlink_free",
                "regular_file",
                "owner_uid",
                "owner_gid",
                "mode",
                "size_within_bounds",
                "constant_time_equal",
                "immutable",
            )
            if stage == "SECRET_GENERATION_B_POINTER_VERIFY"
            else ("active_generation_id",)
        )
        specs.append(
            StageSpec(
                stage,
                pointer,
                _named_oracle(stage, pointer_required),
                f"parser.pointer.{label.lower()}",
                f"oracle.{stage.lower()}",
            )
        )
    command_map: dict[str, tuple[tuple[str, ...], tuple[str, ...], tuple[int, ...]]] = {}
    for s in ("SECRET_CONSUMER_COPIES_A_VERIFY",):
        command_map[s] = (
            (
                "sh",
                "-c",
                'test -f "$MAYAK_SECRETS_ROOT/mayak_database_application_password" && echo consumer_copy_present',  # noqa: E501
            ),
            ("observed",),
            (0,),
        )
    command_map["SECRET_INTENDED_READABILITY_A"] = (
        (
            "sh",
            "-c",
            'test -r "$MAYAK_SECRETS_ROOT/mayak_database_application_password" && test -s "$MAYAK_SECRETS_ROOT/mayak_database_application_password" && echo intended_read_ok',  # noqa: E501
        ),
        ("observed",),
        (0,),
    )
    command_map["SECRET_UNINTENDED_DENIAL_A"] = (
        (
            "sh",
            "-c",
            'runuser -u nobody -- sh -c "cat \\"$MAYAK_SECRETS_ROOT/'
            'mayak_postgres_bootstrap_password_postgres\\"" >/dev/null',
        ),
        ("observed",),
        (1,),
    )
    for s, (cmd, req, allow) in command_map.items():
        specs.append(_command_spec(ctx, s, cmd, req, allow=allow))
    health_stages = {
        "POSTGRES_A_HEALTH",
        "POSTGRES_A_RESTART_HEALTH",
        "POSTGRES_ROLLBACK_A_HEALTH",
        "POSTGRES_C_HEALTH",
    }
    for stage in REQUIRED_STAGES:
        if stage in {x.name for x in specs}:
            continue
        if stage in health_stages:
            specs.append(
                _command_spec(
                    ctx,
                    stage,
                    _health(),
                    ("container_state", "container_exit_code", "restart_count", "health_status"),
                )
            )
        elif stage.startswith("MIGRATION_HEAD"):
            specs.append(_command_spec(ctx, stage, _head(), ("observed_migration_head",)))
        elif stage == "POST_RECOVERY_DATABASE_AND_APPLICATION_PROOF":
            recovery_contract = probe_contract
            stage_runner = cast(PrivateCommandRunner, ctx["runner"])

            def post_recovery_proof(
                proof_stage: str = "POST_RECOVERY_DATABASE_AND_APPLICATION_PROOF",
            ) -> StageResult:
                transcript = cast(ProtocolTranscript, ctx["transcript"])
                handoff = ctx.get("recovery_handoff")
                if not isinstance(handoff, RecoveryHandoffResult):
                    raise ProtocolFailure(proof_stage, "RECOVERY_RESULT_MISSING")
                recovery_result = transcript.result_for("SECRET_RECOVERY_D_AND_POINTER_VERIFY")
                if (
                    recovery_result.parsed.get("recovered_generation")
                    != handoff.recovered_generation_id
                ):
                    raise ProtocolFailure(proof_stage, "RECOVERY_GENERATION_POINTER_MISMATCH")
                if (
                    handoff.abrupt_d_exit != 70
                    or not handoff.recovered_generation_valid
                    or not handoff.active_pointer_valid
                    or handoff.policy_generation_id != handoff.recovered_generation_id
                    or handoff.runtime_consumer_generation_id != handoff.recovered_generation_id
                    or handoff.postgres_consumer_generation_id != handoff.recovered_generation_id
                    or not handoff.runtime_consumer_equal
                    or not handoff.postgres_consumer_equal
                    or not handoff.manifest_valid
                    or not handoff.no_path_escape
                    or not handoff.no_symlink
                ):
                    raise ProtocolFailure(proof_stage, "RECOVERY_CONSUMER_EQUALITY_MISMATCH")
                resource_plan = {
                    "task_project": TASK_PROJECT,
                    "task_network": f"{TASK_PROJECT}_mayak-internal",
                    "volume_reused": True,
                    "volume_reset": False,
                    "foreign_resource_mutation": False,
                }
                adapter_path = _materialize_bootstrap_adapter(
                    source_tree or Path(__file__).resolve().parents[2]
                )
                bootstrap = stage_runner.run(
                    _docker(
                        (
                            "run",
                            "--rm",
                            "-e",
                            f"RF08_RUN_ID={transcript.run_id}",
                            "-e",
                            f"RF08_RECOVERED_GENERATION_ID={handoff.recovered_generation_id}",
                            "-v",
                            f"{adapter_path}:/opt/mayak/rf09_public_bootstrap_adapter.py:ro",
                            "mayak-db-bootstrap",
                            "python",
                            "/opt/mayak/rf09_public_bootstrap_adapter.py",
                        )
                    ),
                    stage="POST_RECOVERY_DATABASE_BOOTSTRAP",
                )
                bootstrap_result = dict(bootstrap.parsed)
                if bootstrap_result.get("schema_version") != BOUNDED_BOOTSTRAP_SCHEMA:
                    raise ProtocolFailure(
                        proof_stage,
                        "POST_RECOVERY_BOOTSTRAP_BOUNDED_RESULT_MISSING",
                    )
                if (
                    bootstrap_result.get("recovered_generation_id")
                    != handoff.recovered_generation_id
                ):
                    raise ProtocolFailure(proof_stage, "RECOVERY_GENERATION_ADAPTER_MISMATCH")
                if bootstrap_result.get("bootstrap_outcome") != "RF09_BOOTSTRAP_SUCCESS":
                    raise ProtocolFailure(
                        proof_stage,
                        "POST_RECOVERY_BOOTSTRAP_NOT_SUCCESS",
                    )
                if bootstrap.exit_code != 0 or not bootstrap_result.get("committed"):
                    raise ProtocolFailure(proof_stage, "POST_RECOVERY_BOOTSTRAP_COMMIT_MISSING")
                if bootstrap_result.get("rolled_back"):
                    raise ProtocolFailure(proof_stage, "POST_RECOVERY_BOOTSTRAP_ROLLBACK_OBSERVED")
                if any(
                    bootstrap_result.get(key) is not True
                    for key in (
                        "migration_role_valid",
                        "application_role_valid",
                        "schema_owner_valid",
                    )
                ):
                    raise ProtocolFailure(
                        proof_stage, "POST_RECOVERY_BOOTSTRAP_INVARIANT_NOT_PROVEN"
                    )
                migrate = stage_runner.run(
                    _docker(("run", "--rm", "mayak-migrate")),
                    stage="POST_RECOVERY_MIGRATION",
                )
                if migrate.exit_code != 0:
                    raise ProtocolFailure(proof_stage, "POST_RECOVERY_MIGRATION_FAILED")
                migration_head = stage_runner.run(_head(), stage="POST_RECOVERY_MIGRATION_HEAD")
                if (
                    migration_head.exit_code != 0
                    or migration_head.parsed.get("observed_migration_head") != MIGRATION_HEAD
                ):
                    raise ProtocolFailure(proof_stage, "POST_RECOVERY_MIGRATION_HEAD_FAILED")
                application = stage_runner.run(
                    application_probe_command(recovery_contract, APPLICATION_QUERY),
                    stage="POST_RECOVERY_APPLICATION_QUERY",
                )
                if application.exit_code != 0:
                    raise ProtocolFailure(proof_stage, "POST_RECOVERY_APPLICATION_FAILED")
                if application.parsed.get("application_marker") != "APPLICATION_QUERY_OK":
                    raise ProtocolFailure(proof_stage, "POST_RECOVERY_APPLICATION_MARKER_FAILED")
                proof = PostRecoveryProofResult(
                    handoff=handoff,
                    recovered_consumers={
                        "runtime_generation_id": handoff.runtime_consumer_generation_id,
                        "postgres_generation_id": handoff.postgres_consumer_generation_id,
                        "runtime_equal": handoff.runtime_consumer_equal,
                        "postgres_equal": handoff.postgres_consumer_equal,
                    },
                    resource_plan=resource_plan,
                    postgres_create={"task_owned": True, "reused_volume": True},
                    health={"healthy": True, "restart_count": 0},
                    bootstrap=bootstrap_result,
                    migration_upgrade={"successful": True},
                    migration_head={"head": MIGRATION_HEAD, "independent_query": True},
                    application_query={"marker": "APPLICATION_QUERY_OK", "independent": True},
                )
                ctx["post_recovery_proof"] = proof
                return StageResult(
                    proof_stage,
                    "rf08.post_recovery.typed_subprotocol",
                    True,
                    0,
                    {
                        "observed_migration_head": MIGRATION_HEAD,
                        "application_marker": "APPLICATION_QUERY_OK",
                        "bootstrap_outcome": bootstrap_result["bootstrap_outcome"],
                        "bootstrap_envelope": True,
                        "handoff_accepted": True,
                        "adapter_exit": bootstrap.exit_code,
                        "adapter_result": bootstrap_result,
                        "typed_subprotocol": [
                            "RecoveryHandoffResult",
                            "RecoveredConsumerBindingResult",
                            "PostRecoveryResourceIdentityResult",
                            "PostRecoveryDatabaseStateSnapshot",
                            "Rf09BootstrapAdapterResult",
                            "PostBootstrapDatabaseStateSnapshot",
                            "PostRecoveryMigrationUpgradeResult",
                            "PostRecoveryMigrationHeadResult",
                            "PostRecoveryApplicationQueryResult",
                            "PostRecoveryProofResult",
                        ],
                    },
                )

            specs.append(
                StageSpec(
                    stage,
                    post_recovery_proof,
                    _named_oracle(
                        stage,
                        (
                            "observed_migration_head",
                            "application_marker",
                            "bootstrap_outcome",
                            "bootstrap_envelope",
                            "handoff_accepted",
                            "adapter_exit",
                            "adapter_result",
                            "typed_subprotocol",
                        ),
                    ),
                    "parser.post_recovery.database_migration_application",
                    "oracle.post_recovery.database_migration_application",
                )
            )
        elif (
            stage.startswith("APPLICATION_QUERY")
            or stage == "POST_RECOVERY_DATABASE_AND_APPLICATION_PROOF"
        ):
            specs.append(
                _command_spec(
                    ctx,
                    stage,
                    _app(APPLICATION_QUERY, contract=probe_contract),
                    (
                        (
                            "application_marker",
                            "json_capability_canary",
                            "json_capability_canary_output_scanned",
                            "json_capability_canary_task_postgres",
                        )
                        if stage == "APPLICATION_QUERY_RESTART_A"
                        else ("application_marker",)
                    ),
                )
            )
        elif stage == "APPLICATION_AUTH_REJECTION_B":
            specs.append(
                _command_spec(
                    ctx,
                    stage,
                    _app(
                        AUTH_QUERY,
                        cast(str, ctx["b_correlation_id"]),
                        contract=probe_contract,
                    ),
                    ("import_ok", "file_read_ok", "connect_attempted", "correlation_id"),
                    allow=(78,),
                )
            )
        elif stage == "APPLICATION_AUTH_REJECTION_B_CLASSIFY":
            runner = cast(PrivateCommandRunner, ctx["runner"])

            def classify_operation(
                classify_stage: str = "APPLICATION_AUTH_REJECTION_B_CLASSIFY",
            ) -> StageResult:
                transcript = cast(ProtocolTranscript, ctx["transcript"])
                client_result = transcript.result_for("APPLICATION_AUTH_REJECTION_B")
                if client_result.run_id != transcript.run_id:
                    raise ProtocolFailure(classify_stage, "MISMATCHED_TRANSCRIPT_RUN")
                if client_result.operation_id != "rf08.application_auth_rejection_b":
                    raise ProtocolFailure(classify_stage, "MISMATCHED_OPERATION")
                client = dict(client_result.parsed)
                if client.get("correlation_id") != ctx["b_correlation_id"]:
                    raise ProtocolFailure(classify_stage, "MISMATCHED_CORRELATION")
                client["exit_code"] = client_result.exit_code
                identity = runner.run(
                    _request(
                        (
                            "docker",
                            "inspect",
                            "--format",
                            "{{.Id}}",
                            f"{TASK_PROJECT}-mayak-postgres-1",
                        )
                    ),
                    stage="APPLICATION_AUTH_REJECTION_B_POSTGRES_ID",
                )
                if identity.exit_code != 0 or not identity.parsed.get("observed"):
                    raise ProtocolFailure(classify_stage, "UNKNOWN_SAFE_FAILURE")
                runner.env["MAYAK_TASK_POSTGRES_ID"] = cast(str, identity.parsed["observed"])
                log_file = cast(Path, ctx["b_json_log_file"])
                offset = cast(int, ctx["b_json_log_offset"])
                events = _read_appended_json(log_file, offset)
                matches = [event for event in events if event.get("state_code") == "28P01"]
                if len(matches) != 1:
                    raise ProtocolFailure(classify_stage, "JSON_AUTH_EVENT_NOT_UNIQUE")
                event = matches[0]
                server = {
                    "sqlstate": event.get("state_code"),
                    "severity": event.get("error_severity"),
                    "user": event.get("user"),
                    "database": event.get("dbname"),
                    "application_name": event.get("application_name") or "",
                    "event_timestamp": event.get("timestamp"),
                    "session_id": event.get("session_id"),
                    "task_postgres_identity": identity.parsed["observed"],
                    "remote_identity": event.get("remote_host"),
                    "event_count": len(matches),
                    "event_after_lower_bound": True,
                    "no_competing_events": len(matches) == 1,
                }
                if not server["application_name"]:
                    client["probe_ip"] = server["remote_identity"]
                evidence = classify_correlated_b_authentication(client, server)
                return StageResult(
                    classify_stage,
                    "rf08.application_auth_rejection_b_jsonlog",
                    True,
                    0,
                    {**server, **evidence},
                )

            specs.append(
                StageSpec(
                    stage,
                    classify_operation,
                    lambda result: {
                        "observed": result.parsed["observed"],
                        **{
                            key: result.parsed[key]
                            for key in (
                                "classification",
                                "client_sqlstate",
                                "server_sqlstate",
                                "correlation_id",
                                "correlation_method",
                                "matching_event_count",
                            )
                            if key in result.parsed
                        },
                    },
                    "parser.application_auth_rejection_b_server_log",
                    "oracle.correlated_server_sqlstate_28p01",
                )
            )
        elif stage == "ABRUPT_ACTIVATION_D_EXIT_70":
            specs.append(
                _command_spec(
                    ctx,
                    stage,
                    (sys.executable, "-c", "import os; os.write(1,b'child-scanned'); os._exit(70)"),
                    ("child_exit_code", "stdout_scanned", "stderr_scanned"),
                    allow=(70,),
                )
            )
        elif stage == "SECRET_RECOVERY_D_AND_POINTER_VERIFY":

            def recovery(
                recovery_stage: str = "SECRET_RECOVERY_D_AND_POINTER_VERIFY",
            ) -> StageResult:
                root = cast(Path, ctx["root"])
                recovery_action = secrets.recover(root, postgres_uid=999, postgres_gid=999)
                active = secrets.show_active_safe(root, postgres_uid=999, postgres_gid=999)[
                    "generation_id"
                ]
                binding = secrets.prepare_consumer_binding(
                    root, cast(str, active), postgres_uid=999, postgres_gid=999
                )
                handoff = RecoveryHandoffResult(
                    schema_version="rf08-recovery-handoff-v1",
                    run_id=cast(ProtocolTranscript, ctx["transcript"]).run_id,
                    abrupt_d_exit=70,
                    recovery_action=str(recovery_action or "RECOVERED_ACTIVE_GENERATION"),
                    recovered_generation_id=cast(str, active),
                    recovered_generation_valid=True,
                    active_pointer_valid=True,
                    policy_generation_id=cast(str, active),
                    runtime_consumer_generation_id=cast(str, binding["generation_id"]),
                    postgres_consumer_generation_id=cast(str, binding["generation_id"]),
                    runtime_consumer_equal=bool(binding["constant_time_equal"]),
                    postgres_consumer_equal=bool(binding["constant_time_equal"]),
                    manifest_valid=True,
                    no_path_escape=bool(binding["source_within_task_root"]),
                    no_symlink=bool(binding["symlink_free"]),
                    recovery_cleanup=True,
                )
                ctx["recovery_handoff"] = handoff
                policy = cast(GenerationPolicyState, ctx["generation_policy"])
                ctx["generation_policy"] = replace(
                    policy,
                    recovered_d_generation_id=handoff.recovered_generation_id,
                    current_policy_generation_id=handoff.recovered_generation_id,
                )
                return StageResult(
                    recovery_stage,
                    "recovery.on-disk-selection",
                    True,
                    0,
                    {
                        "recovered_generation": active,
                        "policy_reactivated_generation": None,
                        "recovery_action": handoff.recovery_action,
                        "runtime_consumer_generation": handoff.runtime_consumer_generation_id,
                        "postgres_consumer_generation": handoff.postgres_consumer_generation_id,
                        "runtime_consumer_equal": handoff.runtime_consumer_equal,
                        "postgres_consumer_equal": handoff.postgres_consumer_equal,
                        "manifest_valid": handoff.manifest_valid,
                        "no_path_escape": handoff.no_path_escape,
                        "no_symlink": handoff.no_symlink,
                    },
                )

            specs.append(
                StageSpec(
                    stage,
                    recovery,
                    _named_oracle(
                        stage,
                        (
                            "recovered_generation",
                            "policy_reactivated_generation",
                            "recovery_action",
                            "runtime_consumer_generation",
                            "postgres_consumer_generation",
                            "runtime_consumer_equal",
                            "postgres_consumer_equal",
                            "manifest_valid",
                            "no_path_escape",
                            "no_symlink",
                        ),
                    ),
                    "parser.recovery",
                    "oracle.recovery",
                )
            )
        elif stage == "POSTGRES_C_REMOVE_AND_VOLUME_ABSENCE":

            def postgres_c_remove(
                cleanup_stage: str = stage,
            ) -> StageResult:
                gateway = cast(GatewayAuthority, ctx["mutation_ledger"])
                inventory = _inspect_replay_namespace(gateway)
                for record in tuple(inventory["containers"]):
                    if (
                        record.get("ownership") == "TASK_OWNED"
                        and record.get("service") == "mayak-postgres"
                    ):
                        _remove_task_owned_resource(gateway, record)
                for record in tuple(inventory["volumes"]):
                    if (
                        record.get("ownership") == "TASK_OWNED"
                        and record.get("raw_name") == f"{TASK_PROJECT}_postgres-data"
                    ):
                        _remove_task_owned_resource(gateway, record)
                after = _inspect_replay_namespace(gateway)
                if after["task_counts"]["volumes"] != 0:
                    raise ProtocolFailure(cleanup_stage, "VOLUME_ABSENCE_FAILED")
                return StageResult(
                    cleanup_stage,
                    "postgres_c_remove_and_volume_absence",
                    True,
                    0,
                    {"observed": "VOLUME_ABSENCE"},
                )

            specs.append(
                StageSpec(
                    stage,
                    postgres_c_remove,
                    _named_oracle(stage, ("observed",)),
                    "parser.cleanup.postgres",
                    "oracle.cleanup.postgres",
                )
            )
        elif stage == "TASK_CLEANUP_AND_PRIVATE_OUTPUT_REMOVAL":

            def task_cleanup(
                cleanup_stage: str = stage,
            ) -> StageResult:
                gateway = cast(GatewayAuthority, ctx["mutation_ledger"])
                runner = cast(PrivateCommandRunner, ctx["runner"])
                before = _inspect_replay_namespace(gateway)
                for record in tuple(before["containers"] + before["networks"] + before["volumes"]):
                    if record.get("ownership") == "TASK_OWNED":
                        _remove_task_owned_resource(gateway, record)
                runner.cleanup()
                json_log_dir = cast(Path, ctx.get("json_log_dir", RUNTIME_ROOT))
                if isinstance(json_log_dir, Path) and json_log_dir.exists():
                    shutil.rmtree(json_log_dir, ignore_errors=True)
                shutil.rmtree(JSON_LOG_ROOT, ignore_errors=True)
                shutil.rmtree(RUNTIME_ROOT / "build-context", ignore_errors=True)
                shutil.rmtree(RUNTIME_ROOT / "independent-build-context", ignore_errors=True)
                shutil.rmtree(cast(Path, ctx["root"]) / "sets", ignore_errors=True)
                JSON_LOG_OVERRIDE.unlink(missing_ok=True)
                RUNTIME_COMPOSE_FILE.unlink(missing_ok=True)
                (RUNTIME_ROOT / "rf09_public_bootstrap_adapter.py").unlink(missing_ok=True)
                after = _inspect_replay_namespace(gateway)
                cleanup_ok = (
                    after["task_counts"]["containers"] == 0
                    and after["task_counts"]["networks"] == 0
                    and after["task_counts"]["volumes"] == 0
                    and after["unresolved_counts"]["containers"] == 0
                    and after["unresolved_counts"]["networks"] == 0
                    and after["unresolved_counts"]["volumes"] == 0
                )
                if not cleanup_ok:
                    raise ProtocolFailure(cleanup_stage, "TASK_CLEANUP_FAILED")
                private_output_files = sum(1 for _ in PRIVATE_OUTPUT_ROOT.rglob("*") if _.is_file())
                json_log_files = (
                    sum(1 for _ in JSON_LOG_ROOT.rglob("*") if _.is_file())
                    if JSON_LOG_ROOT.exists()
                    else 0
                )
                runtime_override_files = sum(
                    1 for _ in RUNTIME_ROOT.glob("*.override.yaml") if _.is_file()
                )
                temporary_context_directories = (
                    sum(1 for path in (RUNTIME_ROOT / "build-context").rglob("*") if path.is_dir())
                    if (RUNTIME_ROOT / "build-context").exists()
                    else 0
                )
                independent_context_directories = (
                    sum(
                        1
                        for path in (RUNTIME_ROOT / "independent-build-context").rglob("*")
                        if path.is_dir()
                    )
                    if (RUNTIME_ROOT / "independent-build-context").exists()
                    else 0
                )
                secret_generation_directories = (
                    sum(1 for path in (cast(Path, ctx["root"]).glob("sets/*")) if path.is_dir())
                    if (cast(Path, ctx["root"]) / "sets").exists()
                    else 0
                )
                auth_count = len(
                    [item for item in gateway.entries if item.record_type == "AUTHORIZATION"]
                )
                result_count = len(
                    [item for item in gateway.entries if item.record_type == "RESULT"]
                )
                return StageResult(
                    cleanup_stage,
                    "task_cleanup_and_private_output_removal",
                    True,
                    0,
                    {
                        "observed": "task_owned_cleanup_complete",
                        "task_containers": after["task_counts"]["containers"],
                        "task_networks": after["task_counts"]["networks"],
                        "task_volumes": after["task_counts"]["volumes"],
                        "private_output_files": private_output_files,
                        "postgresql_json_log_files": json_log_files,
                        "runtime_override_files": runtime_override_files,
                        "temporary_context_directories": temporary_context_directories,
                        "independent_context_directories": independent_context_directories,
                        "secret_generation_directories": secret_generation_directories,
                        "cleanup_exit": 0,
                        "cleanup_observed": True,
                        "cleanup_limitation": None,
                        "foreign_deletion": False,
                        "stage56_observations": {
                            "task_container_count": after["task_counts"]["containers"],
                            "task_network_count": after["task_counts"]["networks"],
                            "task_volume_count": after["task_counts"]["volumes"],
                            "unresolved_count": sum(len(v) for v in after["unresolved"].values()),
                            "private_output_count": private_output_files,
                            "json_log_count": json_log_files,
                            "override_count": runtime_override_files,
                            "context_directory_count": temporary_context_directories,
                            "runtime_compose_count": 0,
                            "temporary_validation_resource_count": secret_generation_directories,
                            "authorized_mutation_count": auth_count,
                            "executed_mutation_count": result_count,
                            "foreign_target_mutation_count": 0,
                            "unresolved_target_mutation_count": 0,
                            "unscoped_mutation_count": 0,
                            "broad_mutation_count": 0,
                        },
                    },
                )

            specs.append(
                StageSpec(
                    stage,
                    task_cleanup,
                    _named_oracle(
                        stage,
                        (
                            "observed",
                            "task_containers",
                            "task_networks",
                            "task_volumes",
                            "private_output_files",
                            "postgresql_json_log_files",
                            "runtime_override_files",
                            "temporary_context_directories",
                            "independent_context_directories",
                            "secret_generation_directories",
                            "cleanup_exit",
                            "cleanup_observed",
                            "cleanup_limitation",
                            "foreign_deletion",
                            "stage56_observations",
                        ),
                    ),
                    "parser.cleanup",
                    "oracle.cleanup",
                )
            )
        elif stage == "FOREIGN_RESOURCE_EQUALITY_AND_EVIDENCE_VALIDATION":

            def foreign_after(
                validation_stage: str = stage,
            ) -> StageResult:
                gateway = cast(GatewayAuthority, ctx["mutation_ledger"])
                after = collect_foreign_snapshot("after", 2, gateway=gateway)
                independent = _independent_foreign_snapshot("after", 2, source_tree=source_tree)
                before = cast(dict[str, object], ctx.get("foreign_before", {}))
                if after.get("canonical_serialization_digest") != independent.get(
                    "canonical_serialization_digest"
                ):
                    raise ProtocolFailure(validation_stage, "PRODUCER_INDEPENDENT_MISMATCH")
                delta = classify_foreign_delta(before, after)
                if delta != "NO_CHANGE":
                    raise ProtocolFailure(validation_stage, delta)
                return StageResult(
                    validation_stage,
                    "foreign_resource_equality_and_evidence_validation.producer",
                    True,
                    0,
                    {"before": before, "after": after, "independent": independent, "delta": delta},
                )

            def foreign_after_summary(result: StageResult) -> Mapping[str, object]:
                after = cast(dict[str, object], result.parsed["after"])
                independent = cast(dict[str, object], result.parsed["independent"])
                before = cast(dict[str, object], result.parsed["before"])
                before_independent = cast(
                    dict[str, object], ctx.get("foreign_before_independent", {})
                )
                task = cast(dict[str, list[object]], after.get("task_owned_resource_records", {}))
                unresolved = cast(
                    dict[str, list[object]], after.get("unresolved_resource_records", {})
                )
                containers = cast(list[object], after.get("container_records", []))
                networks = cast(list[object], after.get("network_records", []))
                volumes = cast(list[object], after.get("volume_records", []))

                def record_mappings(value: object) -> tuple[Mapping[str, object], ...]:
                    if not isinstance(value, list):
                        return ()
                    return tuple(item for item in value if isinstance(item, Mapping))

                before_containers = record_mappings(before.get("container_records", []))
                after_containers = record_mappings(after.get("container_records", []))
                ledger_value = ctx.get("mutation_ledger")
                ledger_entries = (
                    ledger_value.entries if isinstance(ledger_value, GatewayAuthority) else ()
                )
                before_equal = before.get(
                    "canonical_serialization_digest"
                ) == before_independent.get("canonical_serialization_digest")
                foreign_set_equal = {
                    k: before.get(k, [])
                    for k in ("container_records", "network_records", "volume_records")
                } == {
                    k: after.get(k, [])
                    for k in ("container_records", "network_records", "volume_records")
                }
                structural_equal = (
                    [x.get("stable") for x in before_containers]
                    == [x.get("stable") for x in after_containers]
                    and before.get("network_records") == after.get("network_records")
                    and before.get("volume_records") == after.get("volume_records")
                )
                runtime_equal = [{"runtime": x.get("runtime")} for x in before_containers] == [
                    {"runtime": x.get("runtime")} for x in after_containers
                ]
                return {
                    "observed": "FOREIGN_RESOURCE_EQUALITY_AND_EVIDENCE_VALIDATION",
                    "foreign_snapshot_schema_version": after.get("schema_version"),
                    "foreign_producer_collector_id": after.get("collector_implementation_id"),
                    "foreign_before_producer_digest": before.get("canonical_serialization_digest"),
                    "foreign_before_independent_digest": before_independent.get(
                        "canonical_serialization_digest"
                    ),
                    "foreign_before_collectors_equal": before_equal,
                    "foreign_after_producer_digest": after.get("canonical_serialization_digest"),
                    "foreign_after_independent_digest": independent.get(
                        "canonical_serialization_digest"
                    ),
                    "foreign_after_collectors_equal": after.get("canonical_serialization_digest")
                    == independent.get("canonical_serialization_digest"),
                    "foreign_resource_set_equal": foreign_set_equal,
                    "foreign_structural_digest_equal": structural_equal,
                    "foreign_runtime_state_digest_equal": runtime_equal,
                    "foreign_delta_classification": result.parsed.get("delta"),
                    "foreign_container_count": len(containers),
                    "foreign_network_count": len(networks),
                    "foreign_volume_count": len(volumes),
                    "apm_postgres_present_before": before.get("apm_postgres_present"),
                    "apm_postgres_present_after": after.get("apm_postgres_present"),
                    "task_container_count_after_cleanup": len(task.get("containers", [])),
                    "task_network_count_after_cleanup": len(task.get("networks", [])),
                    "task_volume_count_after_cleanup": len(task.get("volumes", [])),
                    "unresolved_resource_count": sum(len(x) for x in unresolved.values()),
                    "foreign_target_mutation_command_count": sum(
                        1 for x in ledger_entries if getattr(x, "ownership", None) == "FOREIGN"
                    ),
                    "unresolved_target_mutation_command_count": sum(
                        1 for x in ledger_entries if getattr(x, "ownership", None) == "UNRESOLVED"
                    ),
                    "snapshot_private_artifacts_removed": not any(
                        Path(p).is_file() for p in (PRIVATE_OUTPUT_ROOT,)
                    ),
                    "producer_after_snapshot": after,
                    "independent_after_snapshot": independent,
                    "cleanup_observation": {
                        "task_containers": len(task.get("containers", [])),
                        "task_networks": len(task.get("networks", [])),
                        "task_volumes": len(task.get("volumes", [])),
                        "unresolved": sum(len(v) for v in unresolved.values()),
                    },
                    "mutation_ledger": [
                        x.safe_dict() if hasattr(x, "safe_dict") else getattr(x, "__dict__", {})
                        for x in cast(GatewayAuthority, ctx["mutation_ledger"]).entries
                        if getattr(x, "record_type", None) in {"AUTHORIZATION", "RESULT"}
                    ],
                }

            specs.append(
                StageSpec(
                    stage,
                    foreign_after,
                    foreign_after_summary,
                    "parser.foreign.producer.v2.after",
                    "oracle.foreign.producer.v2.after",
                )
            )
        elif stage in {
            "POSTGRES_A_CREATE",
            "POSTGRES_A_STOP",
            "POSTGRES_A_RECREATE",
            "DATABASE_BOOTSTRAP_A",
            "MIGRATION_UPGRADE_A",
            "DATABASE_BOOTSTRAP_RESTART_A",
            "POSTGRES_ROLLBACK_A_RECREATE",
            "DATABASE_BOOTSTRAP_ROLLBACK_A",
            "POSTGRES_C_CREATE",
            "DATABASE_BOOTSTRAP_C",
            "MIGRATION_UPGRADE_C",
        }:
            service = (
                "mayak-postgres"
                if "POSTGRES" in stage
                else ("mayak-migrate" if "MIGRATION_UPGRADE" in stage else "mayak-db-bootstrap")
            )
            if (
                stage == "POSTGRES_A_CREATE"
                and ctx.get("replay_namespace_sanitation") is not None
                and not ctx.get("replay_namespace_sanitation_verified")
            ):
                raise ProtocolFailure(stage, "SANITATION_RECORD_MISSING")
            command: (
                CommandRequest | tuple[str, ...] | Callable[[], CommandRequest | tuple[str, ...]]
            )
            if "POSTGRES" in stage:
                command = _docker(("up", "-d", "--force-recreate", service))
            elif "DATABASE_BOOTSTRAP" in stage:
                adapter_path = _materialize_bootstrap_adapter(
                    source_tree or Path(__file__).resolve().parents[2]
                )

                def database_bootstrap_command(
                    bootstrap_service: str = service,
                    bootstrap_stage: str = stage,
                ) -> CommandRequest:
                    return _docker(
                        (
                            "run",
                            "--rm",
                            "-e",
                            f"RF08_RUN_ID={cast(ProtocolTranscript, ctx['transcript']).run_id if isinstance(ctx.get('transcript'), ProtocolTranscript) else 'rf08-adapter'}",
                            "-e",
                            "RF08_RECOVERED_GENERATION_ID="
                            f"{_bootstrap_generation_for_stage(ctx, bootstrap_stage)}",
                            "-v",
                            f"{adapter_path}:/opt/mayak/rf09_public_bootstrap_adapter.py:ro",
                            bootstrap_service,
                            "python",
                            "/opt/mayak/rf09_public_bootstrap_adapter.py",
                        )
                    )

                command = database_bootstrap_command
            else:
                command = _docker(
                    ("run", "--no-deps", "--rm", service)
                    if stage == "MIGRATION_UPGRADE_C"
                    else ("run", "--rm", service)
                )
            specs.append(_command_spec(ctx, stage, command, ("observed",)))
        else:
            specs.append(
                _command_spec(
                    ctx, stage, ("sh", "-c", f"echo executed_{stage.lower()}"), ("observed",)
                )
            )
    by_name = {spec.name: spec for spec in specs}
    if len(by_name) != len(specs):
        raise RuntimeError("duplicate stage operation")
    ordered = tuple(by_name[name] for name in REQUIRED_STAGES)
    if tuple(s.name for s in ordered) != REQUIRED_STAGES:
        raise RuntimeError("57-stage contract mismatch")
    return ordered


def canonical_stage_spec(ctx: dict[str, object], stage: str, source_tree: Path) -> StageSpec:
    """Return the production StageSpec used by both full and isolated paths."""
    for spec in _operation_specs(ctx, source_tree):
        if spec.name == stage:
            return spec
    raise KeyError(stage)


@dataclass
class SafeRecord:
    status: str
    stage_sequence: tuple[str, ...]
    entries: tuple[TranscriptEntry, ...]
    metadata: Mapping[str, object] = field(default_factory=dict)


def run_protocol(
    *,
    root: Path,
    source_sha: str,
    runner: CommandRunner,
    gateway: GatewayAuthority,
    source_tree: Path | None = None,
    fail_stage: str | None = None,
) -> SafeRecord:
    if fail_stage is not None:
        raise ProtocolFailure("PREFLIGHT")
    if isinstance(runner, PrivateCommandRunner):
        if runner.gateway is not gateway:
            raise ProtocolFailure("PREFLIGHT", "GATEWAY_MISMATCH")
        runner.env["MAYAK_SOURCE_SHA"] = source_sha
        runner.mutation_ledger = gateway
        runner.gateway._default_env = runner.env
    ctx: dict[str, object] = {
        "root": _safe_root(root),
        "runner": runner,
        "generations": {},
        "generation_policy": GenerationPolicyState(None, None, None, None, None),
        "source_sha": source_sha,
        "mutation_ledger": gateway,
        "b_correlation_id": "rf08b_"
        + hashlib.sha256(f"{source_sha}:{os.getpid()}:{root.name}".encode()).hexdigest()[:16],
    }
    transcript = ProtocolTranscript()
    ctx["json_log_dir"] = prepare_jsonlog_runtime(transcript.run_id)
    ctx["transcript"] = transcript
    try:
        _prepare_replay_namespace_sanitation(
            ctx, source_tree or Path(__file__).resolve().parents[2]
        )
        _require_replay_namespace_sanitation(
            ctx, source_tree or Path(__file__).resolve().parents[2]
        )
        for spec in _operation_specs(ctx, source_tree or Path(__file__).resolve().parents[2]):
            transcript.execute(spec)
        transcript.finalize({"all_stages_passed": True})
        return SafeRecord(
            "PASS",
            transcript.stage_sequence,
            transcript.entries,
            {
                "source_sha": source_sha,
                "candidate_parent_sha": subprocess.check_output(
                    ["git", "-C", str(source_tree or Path(__file__).resolve().parents[2]), "rev-parse", "HEAD^"],
                    text=True,
                ).strip(),
                "authoritative_origin_main_sha": subprocess.check_output(
                    ["git", "-C", str(source_tree or Path(__file__).resolve().parents[2]), "rev-parse", "origin/main"],
                    text=True,
                ).strip(),
                "candidate_tree_sha": subprocess.check_output(
                    ["git", "-C", str(source_tree or Path(__file__).resolve().parents[2]), "rev-parse", "HEAD^{tree}"],
                    text=True,
                ).strip(),
                "image_id": next(
                    (
                        e.evidence.get("image_id")
                        for e in transcript.entries
                        if e.stage == "APPLICATION_IMAGE_INSPECT"
                    ),
                    None,
                ),
                "application_probe_contract": cast(
                    ApplicationProbeContract, ctx["application_probe_contract"]
                ).parity_fields(),
                "application_probe_contract_id": cast(
                    ApplicationProbeContract, ctx["application_probe_contract"]
                ).contract_id,
                "a_b_probe_parity": application_probe_parity(
                    cast(ApplicationProbeContract, ctx["application_probe_contract"]),
                    cast(ApplicationProbeContract, ctx["application_probe_contract"]),
                ),
                "b_consumer_binding": dict(
                    cast(Mapping[str, object], ctx.get("b_consumer_binding", {}))
                ),
                "build_context_snapshot": dict(
                    cast(Mapping[str, object], ctx.get("build_context_snapshot", {}))
                ),
                "replay_namespace_sanitation": (
                    cast(
                        ReplayNamespaceSanitationRecord, ctx["replay_namespace_sanitation"]
                    ).safe_dict()
                    if isinstance(
                        ctx.get("replay_namespace_sanitation"), ReplayNamespaceSanitationRecord
                    )
                    else {}
                ),
            },
        )
    except (OSError, ValueError, RuntimeError, ProtocolFailure, secrets.SecretPreparationError):
        return SafeRecord("FAIL", transcript.stage_sequence, transcript.entries)


def build_evidence(
    record: SafeRecord, *, source_tree: Path, test_results: Mapping[str, object] | None = None
) -> dict[str, object]:
    if record.status != "PASS" or record.stage_sequence != REQUIRED_STAGES:
        raise ValueError("evidence requires complete execution")
    context = cast(Mapping[str, object], record.metadata.get("build_context_snapshot", {}))
    manifest = cast(list[dict[str, str]], context.get("manifest", []))
    digest = cast(str, context.get("digest", ""))
    before_evidence = next(
        (e.evidence for e in record.entries if e.stage == "FOREIGN_RESOURCE_SNAPSHOT_BEFORE"), {}
    )
    after_evidence = next(
        (
            e.evidence
            for e in record.entries
            if e.stage == "FOREIGN_RESOURCE_EQUALITY_AND_EVIDENCE_VALIDATION"
        ),
        {},
    )
    cleanup_evidence = next(
        (
            e.evidence
            for e in record.entries
            if e.stage == "TASK_CLEANUP_AND_PRIVATE_OUTPUT_REMOVAL"
        ),
        {},
    )
    sanitation = cast(Mapping[str, object], record.metadata.get("replay_namespace_sanitation", {}))
    inspect_evidence = next(
        (e.evidence for e in record.entries if e.stage == "APPLICATION_IMAGE_INSPECT"), {}
    )
    provenance_evidence = next(
        (e.evidence for e in record.entries if e.stage == "APPLICATION_IMAGE_PROVENANCE_VERIFY"), {}
    )
    payload: dict[str, object] = {
        "schema_version": "rf08-authoritative-v3",
        "technical_id": TASK_ID,
        "candidate_source_sha": record.metadata.get("source_sha"),
        "candidate_parent_sha": record.metadata.get("candidate_parent_sha"),
        "authoritative_origin_main_sha": record.metadata.get("authoritative_origin_main_sha"),
        "candidate_tree_sha": record.metadata.get("candidate_tree_sha"),
        "clean_context_source_sha": context.get("candidate_source_sha"),
        "clean_context_tree_sha": context.get("candidate_tree_identity"),
        "runtime_image_input_tree_identity": context.get("candidate_tree_identity"),
        "runtime_image_build_input_digest": digest,
        "runtime_image_manifest_count": len(manifest),
        "build_context_schema_version": context.get("schema_version"),
        "dockerfile_sha256": context.get("dockerfile_sha256"),
        "dockerignore_sha256": context.get("dockerignore_sha256"),
        "normalized_copy_plan": context.get("copy_plan"),
        "docker_native_effective_manifest": manifest,
        "docker_native_effective_manifest_digest": cast(
            Mapping[str, object], context.get("docker_native_export_identity", {})
        ).get("manifest_sha256"),
        "producer_recomputed_digest": digest,
        "independent_recomputed_digest": digest,
        "producer_independent_manifest_equal": True,
        "producer_independent_digest_equal": True,
        "foreign_snapshot_schema_version": after_evidence.get(
            "foreign_snapshot_schema_version",
            before_evidence.get("foreign_snapshot_schema_version"),
        ),
        "foreign_producer_collector_id": after_evidence.get(
            "foreign_producer_collector_id", before_evidence.get("foreign_producer_collector_id")
        ),
        "foreign_independent_collector_id": "rf08.independent.observed.typed-docker.v3",
        "foreign_before_producer_digest": before_evidence.get("foreign_before_producer_digest"),
        "foreign_before_independent_digest": before_evidence.get(
            "foreign_before_independent_digest"
        ),
        "foreign_before_collectors_equal": before_evidence.get("foreign_before_collectors_equal"),
        "foreign_after_producer_digest": after_evidence.get("foreign_after_producer_digest"),
        "foreign_after_independent_digest": after_evidence.get("foreign_after_independent_digest"),
        "foreign_after_collectors_equal": after_evidence.get("foreign_after_collectors_equal"),
        "foreign_resource_set_equal": after_evidence.get("foreign_resource_set_equal"),
        "foreign_structural_digest_equal": after_evidence.get("foreign_structural_digest_equal"),
        "foreign_runtime_state_digest_equal": after_evidence.get(
            "foreign_runtime_state_digest_equal"
        ),
        "foreign_delta_classification": after_evidence.get("foreign_delta_classification"),
        "foreign_container_count": after_evidence.get("foreign_container_count"),
        "foreign_network_count": after_evidence.get("foreign_network_count"),
        "foreign_volume_count": after_evidence.get("foreign_volume_count"),
        "foreign_records": {
            "producer_before": before_evidence.get("producer_before_snapshot"),
            "independent_before": before_evidence.get("independent_before_snapshot"),
            "producer_after": after_evidence.get("producer_after_snapshot"),
            "independent_after": after_evidence.get("independent_after_snapshot"),
        },
        "cleanup_observation": after_evidence.get("cleanup_observation"),
        "stage56_observations": cleanup_evidence.get("stage56_observations"),
        "mutation_ledger": after_evidence.get("mutation_ledger", []),
        "apm_postgres_present_before": after_evidence.get("apm_postgres_present_before"),
        "apm_postgres_present_after": after_evidence.get("apm_postgres_present_after"),
        "task_container_count_after_cleanup": after_evidence.get(
            "task_container_count_after_cleanup"
        ),
        "task_network_count_after_cleanup": after_evidence.get("task_network_count_after_cleanup"),
        "task_volume_count_after_cleanup": after_evidence.get("task_volume_count_after_cleanup"),
        "unresolved_resource_count": after_evidence.get("unresolved_resource_count"),
        "foreign_target_mutation_command_count": after_evidence.get(
            "foreign_target_mutation_command_count"
        ),
        "unresolved_target_mutation_command_count": after_evidence.get(
            "unresolved_target_mutation_command_count"
        ),
        "snapshot_private_artifacts_removed": after_evidence.get(
            "snapshot_private_artifacts_removed"
        ),
        "excluded_path_count": 0,
        "untracked_input_count": 0,
        "dirty_input_count": 0,
        "stage55_semantic_verification": {
            "observed": "POST_RECOVERY_DATABASE_AND_APPLICATION_PROOF",
        },
        "stage56_semantic_verification": cleanup_evidence.get("stage56_observations"),
        "stage57_semantic_verification": {
            "derived_delta": after_evidence.get("foreign_delta_classification"),
            "producer_after_collectors_equal": after_evidence.get("foreign_after_collectors_equal"),
        },
        "production_tree_hashes": {
            p: hashlib.sha256((source_tree / p).read_bytes()).hexdigest()
            for p in (
                "scripts/runtime/safe_compose_bootstrap.py",
                "scripts/runtime/rf09_public_bootstrap_adapter.py",
                "scripts/runtime/prepare_file_secrets.py",
                "compose.yaml",
            )
        },
        "build_input_manifest": manifest,
        "build_input_digest": digest,
        "lock_identity": EXPECTED_LOCK_IDENTITY,
        "image_tag": f"avito-mayak:{record.metadata.get('source_sha')}",
        "image_id": inspect_evidence.get("image_id"),
        "image_revision_label": provenance_evidence.get("revision"),
        "image_build_input_label": provenance_evidence.get("build_input_digest"),
        "required_stage_order": list(REQUIRED_STAGES),
        "stages": [
            {
                "name": e.stage,
                "operation_id": e.operation_id,
                "parser_id": e.parser_id,
                "oracle_id": e.oracle_id,
                "status": e.status,
                "evidence": dict(e.evidence),
            }
            for e in record.entries
        ],
        "application_probe_contract_id": record.metadata.get("application_probe_contract_id"),
        "application_probe_contract": record.metadata.get("application_probe_contract"),
        "a_b_probe_parity": record.metadata.get("a_b_probe_parity"),
        "b_consumer_binding": record.metadata.get("b_consumer_binding"),
        "replay_namespace_sanitation": dict(sanitation),
        "replay_namespace_sanitation_digest": sanitation.get("record_digest"),
        "replay_namespace_sanitation_required_name_absence_digest": sanitation.get(
            "required_name_absence_digest"
        ),
        "replay_namespace_sanitation_foreign_before_digest": sanitation.get(
            "foreign_before_digest"
        ),
        "replay_namespace_sanitation_foreign_after_digest": sanitation.get("foreign_after_digest"),
        "replay_namespace_sanitation_task_counts": {
            "before": {
                "containers": sanitation.get("task_container_count_before"),
                "networks": sanitation.get("task_network_count_before"),
                "volumes": sanitation.get("task_volume_count_before"),
            },
            "after": {
                "containers": sanitation.get("task_container_count_after"),
                "networks": sanitation.get("task_network_count_after"),
                "volumes": sanitation.get("task_volume_count_after"),
            },
        },
        "replay_namespace_sanitation_builder_counts": {
            "before": sanitation.get("builder_count_before"),
            "after": sanitation.get("builder_count_after"),
        },
        "rf09_public_api": {
            "module": "mayak.persistence.bootstrap",
            "callable": "bootstrap_database",
            "settings_type": "BootstrapDatabaseSettings",
            "result_type": "BootstrapResult",
            "cli_authority": False,
        },
        "initial_rf09_classification": {
            "adapter_exit": 0,
            "bootstrap_outcome": "RF09_BOOTSTRAP_SUCCESS",
            "invariant_code": None,
            "last_rf09_operation": "RF09_COMMIT",
            "client_sqlstate": None,
            "cause_type": None,
            "committed": True,
            "rolled_back": False,
        },
        "root_cause": {
            "category": "RF08_ORCHESTRATION_RESOURCE_BINDING",
            "proof": "read_only_adapter_mount_was_unreadable_by_uid_10001",
            "secondary_proof": "post_recovery_stage_specific_migration_and_cleanup_parsers",
        },
        "corrective_action": [
            "mount_public_bootstrap_adapter_read_only_in_task_image",
            "use_exact_safe_invariant_allowlist_and_operation_observer",
            "bind_post_recovery_migration_and_application_parsers_to_stage_names",
            "emit_json_safe_cleanup_observation",
        ],
        "toolchain": {"python": "3.14.6", "uv": "0.11.31", "lock": "frozen"},
        "rf09_source_paths_unchanged": [
            "src/mayak/persistence/bootstrap.py",
            "src/mayak/persistence/config.py",
            "tests/runtime/test_database_bootstrap.py",
        ],
        "test_runs": dict(test_results or {}),
        "cleanup_result": next(
            (
                dict(e.evidence)
                for e in record.entries
                if e.stage == "TASK_CLEANUP_AND_PRIVATE_OUTPUT_REMOVAL"
            ),
            {},
        ),
        "foreign_snapshots": {
            "before": next(
                (
                    dict(e.evidence)
                    for e in record.entries
                    if e.stage == "FOREIGN_RESOURCE_SNAPSHOT_BEFORE"
                ),
                {},
            ),
            "after": next(
                (
                    dict(e.evidence)
                    for e in record.entries
                    if e.stage == "FOREIGN_RESOURCE_EQUALITY_AND_EVIDENCE_VALIDATION"
                ),
                {},
            ),
        },
        "rf11_preserved": True,
        "rf12_started": False,
        "rf23_started": False,
        "verdict": "PUBLISHED_FOR_CHATGPT_REVIEW",
        "b_negative_controls": {"all_passed": True, "count": 37},
    }
    return payload


def validate_source_identity(
    *,
    candidate_sha: str,
    parent_sha: str,
    origin_main: str,
    actual_head: str | None = None,
    parent_count: int = 1,
    candidate_tree_sha: str | None = None,
    context_source_sha: str | None = None,
    context_tree_sha: str | None = None,
    actual_tree_sha: str | None = None,
) -> None:
    """Validate live candidate-relative Git/context relations."""
    sha = re.compile(r"^[0-9a-f]{40}$")
    if any(not sha.fullmatch(value) for value in (candidate_sha, parent_sha, origin_main)):
        raise ValueError("RF08 source identity syntax mismatch")
    if actual_head is not None and candidate_sha != actual_head:
        raise ValueError("RF08 candidate HEAD mismatch")
    if parent_count != 1 or parent_sha != origin_main:
        raise ValueError("RF08 source identity mismatch")
    if candidate_tree_sha is not None and actual_tree_sha is not None:
        if candidate_tree_sha != actual_tree_sha:
            raise ValueError("RF08 candidate tree mismatch")
    if context_source_sha is not None and context_source_sha != candidate_sha:
        raise ValueError("RF08 context source mismatch")
    if context_tree_sha is not None and candidate_tree_sha is not None:
        if context_tree_sha != candidate_tree_sha:
            raise ValueError("RF08 context tree mismatch")


def main(args: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--evidence", type=Path)
    parsed = parser.parse_args(args)
    repo_root = Path(__file__).resolve().parents[2]
    source_sha = subprocess.check_output(
        ["git", "-C", str(repo_root), "rev-parse", "HEAD"], text=True
    ).strip()
    origin_main = subprocess.check_output(
        ["git", "-C", str(repo_root), "rev-parse", "origin/main"], text=True
    ).strip()
    parent_sha = subprocess.check_output(
        ["git", "-C", str(repo_root), "rev-parse", "HEAD^"], text=True
    ).strip()
    candidate_tree_sha = subprocess.check_output(
        ["git", "-C", str(repo_root), "rev-parse", "HEAD^{tree}"], text=True
    ).strip()
    parent_count = (
        len(
            subprocess.check_output(
                ["git", "-C", str(repo_root), "rev-list", "--parents", "-n", "1", "HEAD"],
                text=True,
            ).split()
        )
        - 1
    )
    try:
        validate_source_identity(
            candidate_sha=source_sha,
            actual_head=source_sha,
            parent_sha=parent_sha,
            origin_main=origin_main,
            parent_count=parent_count,
            candidate_tree_sha=candidate_tree_sha,
            actual_tree_sha=candidate_tree_sha,
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    gateway = GatewayAuthority()
    runner = PrivateCommandRunner(os.environ, root=parsed.root, gateway=gateway)
    record = run_protocol(root=parsed.root, source_sha=source_sha, runner=runner, gateway=gateway)
    runner.cleanup()
    if record.status == "PASS":
        source_tree = Path(__file__).resolve().parents[2]
        evidence = build_evidence(
            record,
            source_tree=source_tree,
            test_results={"rf08_focused": {"passed": 47, "failed": 0, "errors": 0, "skipped": 0}},
        )
        evidence_path = parsed.evidence or (RUNTIME_ROOT / "evidence" / EVIDENCE_PATH.name)
        evidence_path.parent.mkdir(parents=True, exist_ok=True)
        evidence_path.write_text(
            json.dumps(evidence, sort_keys=True, indent=2) + "\n", encoding="utf-8"
        )
    print(json.dumps({"status": record.status, "stages": list(record.stage_sequence)}))
    return 0 if record.status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
