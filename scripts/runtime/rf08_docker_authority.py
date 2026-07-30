"""Stateful Docker gateway and exact argv classification for RF-08."""

from __future__ import annotations

import contextvars
import hashlib
import json
import subprocess
import uuid
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any, Final, TypeAlias

TASK_PROJECT: Final = "avito-mayak-rf08-secret-delivery"
TECHNICAL_ID: Final = "RF-08-CORRECTIVE-NONROOT-FILE-SECRET-DELIVERY-20260729-01"
COMPOSE_FILE: Final = "compose.yaml"
RUNTIME_PROFILE: Final = "runtime-foundation"
ALLOWED_SERVICES: Final = frozenset(
    {
        "mayak-api",
        "mayak-worker",
        "mayak-scheduler",
        "mayak-postgres",
        "mayak-db-bootstrap",
        "mayak-migrate",
    }
)
ALLOWED_OWNER: Final = "rf08"

_GATEWAY_TOKEN: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "rf08_docker_gateway_token",
    default=None,
)


class DockerCommandClass(StrEnum):
    READ_ONLY = "READ_ONLY"
    COMPOSE_CREATE = "COMPOSE_CREATE"
    COMPOSE_UP = "COMPOSE_UP"
    COMPOSE_START = "COMPOSE_START"
    COMPOSE_STOP = "COMPOSE_STOP"
    COMPOSE_RESTART = "COMPOSE_RESTART"
    COMPOSE_RUN = "COMPOSE_RUN"
    COMPOSE_RM = "COMPOSE_RM"
    COMPOSE_DOWN = "COMPOSE_DOWN"
    DIRECT_RUN = "DIRECT_RUN"
    DIRECT_CONTAINER_RM = "DIRECT_CONTAINER_RM"
    NETWORK_CREATE = "NETWORK_CREATE"
    NETWORK_RM = "NETWORK_RM"
    VOLUME_CREATE = "VOLUME_CREATE"
    VOLUME_RM = "VOLUME_RM"
    IMAGE_BUILD = "IMAGE_BUILD"
    IMAGE_LOAD = "IMAGE_LOAD"
    BUILDX_BUILD = "BUILDX_BUILD"
    TASK_SCOPED_BUILDER_CREATE = "TASK_SCOPED_BUILDER_CREATE"
    TASK_SCOPED_BUILDER_REMOVE = "TASK_SCOPED_BUILDER_REMOVE"
    FORBIDDEN_UNSCOPED_MUTATION = "FORBIDDEN_UNSCOPED_MUTATION"
    FORBIDDEN_BROAD_MUTATION = "FORBIDDEN_BROAD_MUTATION"
    UNKNOWN_DOCKER_COMMAND = "UNKNOWN_DOCKER_COMMAND"


@dataclass(frozen=True)
class TaskCreationPlan:
    expected_kind: str
    expected_name: str
    allowed_services: tuple[str, ...]
    project: str = TASK_PROJECT
    technical_id: str = TECHNICAL_ID
    compose_file: str = COMPOSE_FILE
    profile: str = RUNTIME_PROFILE
    owner_label: str = ALLOWED_OWNER


@dataclass(frozen=True)
class DockerInvocationPlan:
    argv: tuple[str, ...]
    command_class: DockerCommandClass
    target_kind: str
    target_identity_hash: str
    is_mutation: bool
    compose_file: str | None = None
    project_name: str | None = None
    profile: str | None = None
    command: str | None = None
    service: str | None = None
    exact_options: tuple[tuple[str, str | None], ...] = ()


@dataclass(frozen=True)
class ReadOnlyDockerQuery(DockerInvocationPlan):
    @classmethod
    def from_plan(cls, plan: DockerInvocationPlan) -> "ReadOnlyDockerQuery":
        if plan.is_mutation:
            raise ValueError("mutation plan is not a read-only query")
        return cls(
            argv=plan.argv,
            command_class=plan.command_class,
            target_kind=plan.target_kind,
            target_identity_hash=plan.target_identity_hash,
            is_mutation=plan.is_mutation,
            compose_file=plan.compose_file,
            project_name=plan.project_name,
            profile=plan.profile,
            command=plan.command,
            service=plan.service,
            exact_options=plan.exact_options,
        )

    @classmethod
    def from_argv(cls, argv: Sequence[str]) -> "ReadOnlyDockerQuery":
        plan = _direct_plan(tuple(argv))
        if plan.is_mutation:
            raise ValueError("mutation command is not read-only")
        return cls.from_plan(plan)


@dataclass(frozen=True)
class ComposeOperationPlan(DockerInvocationPlan):
    @classmethod
    def from_plan(cls, plan: DockerInvocationPlan) -> "ComposeOperationPlan":
        if plan.command_class not in {
            DockerCommandClass.COMPOSE_CREATE,
            DockerCommandClass.COMPOSE_UP,
            DockerCommandClass.COMPOSE_START,
            DockerCommandClass.COMPOSE_STOP,
            DockerCommandClass.COMPOSE_RESTART,
            DockerCommandClass.COMPOSE_RUN,
            DockerCommandClass.COMPOSE_RM,
            DockerCommandClass.COMPOSE_DOWN,
        }:
            raise ValueError("not a compose mutation plan")
        return cls(
            argv=plan.argv,
            command_class=plan.command_class,
            target_kind=plan.target_kind,
            target_identity_hash=plan.target_identity_hash,
            is_mutation=plan.is_mutation,
            compose_file=plan.compose_file,
            project_name=plan.project_name,
            profile=plan.profile,
            command=plan.command,
            service=plan.service,
            exact_options=plan.exact_options,
        )


@dataclass(frozen=True)
class ContainerProbeCreationPlan(DockerInvocationPlan):
    @classmethod
    def from_plan(cls, plan: DockerInvocationPlan) -> "ContainerProbeCreationPlan":
        if plan.command_class != DockerCommandClass.DIRECT_RUN:
            raise ValueError("not a direct run plan")
        return cls(
            argv=plan.argv,
            command_class=plan.command_class,
            target_kind=plan.target_kind,
            target_identity_hash=plan.target_identity_hash,
            is_mutation=plan.is_mutation,
            compose_file=plan.compose_file,
            project_name=plan.project_name,
            profile=plan.profile,
            command=plan.command,
            service=plan.service,
            exact_options=plan.exact_options,
        )


@dataclass(frozen=True)
class ContainerRemovalPlan(DockerInvocationPlan):
    @classmethod
    def from_plan(cls, plan: DockerInvocationPlan) -> "ContainerRemovalPlan":
        if plan.command_class != DockerCommandClass.DIRECT_CONTAINER_RM:
            raise ValueError("not a direct container removal plan")
        return cls(
            argv=plan.argv,
            command_class=plan.command_class,
            target_kind=plan.target_kind,
            target_identity_hash=plan.target_identity_hash,
            is_mutation=plan.is_mutation,
            compose_file=plan.compose_file,
            project_name=plan.project_name,
            profile=plan.profile,
            command=plan.command,
            service=plan.service,
            exact_options=plan.exact_options,
        )


@dataclass(frozen=True)
class ImageBuildPlan(DockerInvocationPlan):
    @classmethod
    def from_plan(cls, plan: DockerInvocationPlan) -> "ImageBuildPlan":
        if plan.command_class != DockerCommandClass.IMAGE_BUILD:
            raise ValueError("not an image build plan")
        return cls(
            argv=plan.argv,
            command_class=plan.command_class,
            target_kind=plan.target_kind,
            target_identity_hash=plan.target_identity_hash,
            is_mutation=plan.is_mutation,
            compose_file=plan.compose_file,
            project_name=plan.project_name,
            profile=plan.profile,
            command=plan.command,
            service=plan.service,
            exact_options=plan.exact_options,
        )


@dataclass(frozen=True)
class ImageLoadPlan(DockerInvocationPlan):
    @classmethod
    def from_plan(cls, plan: DockerInvocationPlan) -> "ImageLoadPlan":
        if plan.command_class != DockerCommandClass.IMAGE_LOAD:
            raise ValueError("not an image load plan")
        return cls(
            argv=plan.argv,
            command_class=plan.command_class,
            target_kind=plan.target_kind,
            target_identity_hash=plan.target_identity_hash,
            is_mutation=plan.is_mutation,
            compose_file=plan.compose_file,
            project_name=plan.project_name,
            profile=plan.profile,
            command=plan.command,
            service=plan.service,
            exact_options=plan.exact_options,
        )


@dataclass(frozen=True)
class BuildxManifestPlan(DockerInvocationPlan):
    @classmethod
    def from_plan(cls, plan: DockerInvocationPlan) -> "BuildxManifestPlan":
        if plan.command_class != DockerCommandClass.BUILDX_BUILD:
            raise ValueError("not a buildx manifest plan")
        return cls(
            argv=plan.argv,
            command_class=plan.command_class,
            target_kind=plan.target_kind,
            target_identity_hash=plan.target_identity_hash,
            is_mutation=plan.is_mutation,
            compose_file=plan.compose_file,
            project_name=plan.project_name,
            profile=plan.profile,
            command=plan.command,
            service=plan.service,
            exact_options=plan.exact_options,
        )


@dataclass(frozen=True)
class BuilderScopePlan(DockerInvocationPlan):
    @classmethod
    def from_plan(cls, plan: DockerInvocationPlan) -> "BuilderScopePlan":
        if plan.command_class not in {
            DockerCommandClass.TASK_SCOPED_BUILDER_CREATE,
            DockerCommandClass.TASK_SCOPED_BUILDER_REMOVE,
        }:
            raise ValueError("not a builder scope plan")
        return cls(
            argv=plan.argv,
            command_class=plan.command_class,
            target_kind=plan.target_kind,
            target_identity_hash=plan.target_identity_hash,
            is_mutation=plan.is_mutation,
            compose_file=plan.compose_file,
            project_name=plan.project_name,
            profile=plan.profile,
            command=plan.command,
            service=plan.service,
            exact_options=plan.exact_options,
        )


@dataclass(frozen=True)
class NetworkCreationPlan(DockerInvocationPlan):
    @classmethod
    def from_plan(cls, plan: DockerInvocationPlan) -> "NetworkCreationPlan":
        if plan.command_class not in {
            DockerCommandClass.NETWORK_CREATE,
            DockerCommandClass.NETWORK_RM,
        }:
            raise ValueError("not a network plan")
        return cls(
            argv=plan.argv,
            command_class=plan.command_class,
            target_kind=plan.target_kind,
            target_identity_hash=plan.target_identity_hash,
            is_mutation=plan.is_mutation,
            compose_file=plan.compose_file,
            project_name=plan.project_name,
            profile=plan.profile,
            command=plan.command,
            service=plan.service,
            exact_options=plan.exact_options,
        )


@dataclass(frozen=True)
class VolumeCreationPlan(DockerInvocationPlan):
    @classmethod
    def from_plan(cls, plan: DockerInvocationPlan) -> "VolumeCreationPlan":
        if plan.command_class not in {
            DockerCommandClass.VOLUME_CREATE,
            DockerCommandClass.VOLUME_RM,
        }:
            raise ValueError("not a volume plan")
        return cls(
            argv=plan.argv,
            command_class=plan.command_class,
            target_kind=plan.target_kind,
            target_identity_hash=plan.target_identity_hash,
            is_mutation=plan.is_mutation,
            compose_file=plan.compose_file,
            project_name=plan.project_name,
            profile=plan.profile,
            command=plan.command,
            service=plan.service,
            exact_options=plan.exact_options,
        )


@dataclass(frozen=True, slots=True)
class ResolvedTaskResourceCapability:
    gateway_instance_id: str
    issuance_id: str
    seal: str
    resource_kind: str
    immutable_identity_hash: str
    resource_name_hash: str
    project_identity: str
    technical_id: str
    owner_labels_digest: str
    service_identity: str | None
    driver: str | None
    scope: str | None
    topology_digest: str
    label_set_digest: str
    allowed_operations: tuple[str, ...]

    def safe_dict(self) -> dict[str, object]:
        return {
            "gateway_instance_id": self.gateway_instance_id,
            "issuance_id": self.issuance_id,
            "resource_kind": self.resource_kind,
            "immutable_identity_hash": self.immutable_identity_hash,
            "resource_name_hash": self.resource_name_hash,
            "project_identity": self.project_identity,
            "technical_id": self.technical_id,
            "owner_labels_digest": self.owner_labels_digest,
            "service_identity": self.service_identity,
            "driver": self.driver,
            "scope": self.scope,
            "topology_digest": self.topology_digest,
            "label_set_digest": self.label_set_digest,
            "allowed_operations": list(self.allowed_operations),
        }


MutationPlan: TypeAlias = (
    ComposeOperationPlan
    | ContainerProbeCreationPlan
    | ContainerRemovalPlan
    | ImageBuildPlan
    | ImageLoadPlan
    | BuildxManifestPlan
    | BuilderScopePlan
    | NetworkCreationPlan
    | VolumeCreationPlan
)


@dataclass(frozen=True)
class DockerInvocationAuditRecord:
    invocation_sequence: int
    stage: str
    command_class: str
    argv_fingerprint: str
    target_kind: str
    target_identity_hash: str
    is_mutation: bool
    gateway_instance_id: str


@dataclass(frozen=True)
class DockerMutationRecord:
    record_type: str
    authorization_sequence: int
    execution_result_sequence: int | None
    invocation_sequence: int
    stage: str
    command_class: str
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
        payload = asdict(self)
        payload["planned_ownership"] = self.planned_ownership
        payload["ownership"] = self.ownership
        payload["mutation_allowed"] = self.mutation_allowed
        payload["scoped"] = self.scoped
        payload["sequence"] = self.sequence
        payload["executed"] = self.executed
        return payload


@dataclass(frozen=True)
class DockerExecutionResult:
    returncode: int | None
    started: bool
    completed: bool
    timed_out: bool
    failure_classification: str | None = None


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _fingerprint(argv: Sequence[str]) -> str:
    return _sha256(json.dumps(list(argv), separators=(",", ":"), ensure_ascii=True))


def _split_option_pairs(argv: Sequence[str]) -> dict[str, list[str]]:
    pairs: dict[str, list[str]] = {}
    index = 0
    while index < len(argv):
        token = argv[index]
        if token.startswith("--") and "=" in token:
            option, value = token.split("=", 1)
            if option in {
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
            }:
                pairs.setdefault(option, []).append(value)
                index += 1
                continue
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
        }:
            if index + 1 >= len(argv):
                raise ValueError("missing option value")
            pairs.setdefault(token, []).append(argv[index + 1])
            index += 2
            continue
        if token.startswith("-"):
            pairs.setdefault(token, []).append("")
            index += 1
            continue
        index += 1
    return pairs


def _canonical_compose_identity(
    command: str, service: str | None, file: str, project: str, profile: str
) -> str:
    payload = {
        "command": command,
        "service": service,
        "file": file,
        "project": project,
        "profile": profile,
        "task_project": TASK_PROJECT,
        "technical_id": TECHNICAL_ID,
    }
    return _sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")))


def _compose_plan(argv: tuple[str, ...]) -> DockerInvocationPlan:
    if len(argv) < 3 or argv[0] != "docker" or argv[1] != "compose":
        raise ValueError("not a compose invocation")
    file_values: list[str] = []
    project_values: list[str] = []
    profile_values: list[str] = []
    index = 2
    while index < len(argv):
        token = argv[index]
        if token.startswith("--file="):
            file_values.append(token.split("=", 1)[1])
            index += 1
            continue
        if token.startswith("--project-name="):
            project_values.append(token.split("=", 1)[1])
            index += 1
            continue
        if token.startswith("--profile="):
            profile_values.append(token.split("=", 1)[1])
            index += 1
            continue
        if token in {"-f", "--file", "-p", "--project-name", "--profile"}:
            if index + 1 >= len(argv):
                raise ValueError("missing compose option value")
            if token in {"-f", "--file"}:
                file_values.append(argv[index + 1])
            elif token in {"-p", "--project-name"}:
                project_values.append(argv[index + 1])
            else:
                profile_values.append(argv[index + 1])
            index += 2
            continue
        if token.startswith("-"):
            raise ValueError("compose option mismatch")
        command = token
        remainder = argv[index + 1 :]
        break
    else:
        raise ValueError("compose command missing")
    if len(file_values) != 1 or len(project_values) != 1 or len(profile_values) != 1:
        raise ValueError("compose binding incomplete")
    compose_file = Path(file_values[0])
    if not compose_file.is_absolute():
        raise ValueError("compose file must be absolute")
    if project_values[0] != TASK_PROJECT:
        raise ValueError("compose project mismatch")
    if compose_file.name not in {COMPOSE_FILE, "compose.runtime.yaml"}:
        raise ValueError("compose file mismatch")
    if profile_values[0] != RUNTIME_PROFILE:
        raise ValueError("compose profile mismatch")
    if command == "version":
        if remainder != ("--short",):
            raise ValueError("compose version mismatch")
        return ReadOnlyDockerQuery(
            argv=argv,
            command_class=DockerCommandClass.READ_ONLY,
            target_kind="compose_project",
            target_identity_hash=_canonical_compose_identity(
                command, None, file_values[0], project_values[0], profile_values[0]
            ),
            is_mutation=False,
            compose_file=file_values[0],
            project_name=project_values[0],
            profile=profile_values[0],
            command=command,
            exact_options=(
                ("-f", file_values[0]),
                ("-p", project_values[0]),
                ("--profile", profile_values[0]),
            ),
        )
    if command == "config":
        if remainder != ("--format", "json"):
            raise ValueError("compose config mismatch")
        return ReadOnlyDockerQuery(
            argv=argv,
            command_class=DockerCommandClass.READ_ONLY,
            target_kind="compose_project",
            target_identity_hash=_canonical_compose_identity(
                command, None, file_values[0], project_values[0], profile_values[0]
            ),
            is_mutation=False,
            compose_file=file_values[0],
            project_name=project_values[0],
            profile=profile_values[0],
            command=command,
            exact_options=(
                ("-f", file_values[0]),
                ("-p", project_values[0]),
                ("--profile", profile_values[0]),
                ("--format", "json"),
            ),
        )
    if command == "ps":
        if remainder not in {(), ("-q",), ("--quiet",)}:
            raise ValueError("compose ps mismatch")
        return ReadOnlyDockerQuery(
            argv=argv,
            command_class=DockerCommandClass.READ_ONLY,
            target_kind="compose_project",
            target_identity_hash=_canonical_compose_identity(
                command, None, file_values[0], project_values[0], profile_values[0]
            ),
            is_mutation=False,
            compose_file=file_values[0],
            project_name=project_values[0],
            profile=profile_values[0],
            command=command,
            exact_options=(
                ("-f", file_values[0]),
                ("-p", project_values[0]),
                ("--profile", profile_values[0]),
            ),
        )
    if command == "exec":
        if len(remainder) < 3:
            raise ValueError("compose exec mismatch")
        service = remainder[0]
        if service not in ALLOWED_SERVICES:
            raise ValueError("compose exec service mismatch")
        payload = remainder[1:]
        safe_execs = {
            ("pg_isready", "-U", "mayak", "-d", "mayak"),
            (
                "psql",
                "-U",
                "mayak",
                "-d",
                "mayak",
                "-Atqc",
                "SELECT version_num FROM alembic_version;",
            ),
            (
                "psql",
                "-U",
                "mayak",
                "-d",
                "mayak",
                "-Atqc",
                "SELECT current_setting('log_destination');",
            ),
        }
        if tuple(payload) not in safe_execs:
            raise ValueError("compose exec payload mismatch")
        return ReadOnlyDockerQuery(
            argv=argv,
            command_class=DockerCommandClass.READ_ONLY,
            target_kind="container",
            target_identity_hash=_canonical_compose_identity(
                command, service, file_values[0], project_values[0], profile_values[0]
            ),
            is_mutation=False,
            compose_file=file_values[0],
            project_name=project_values[0],
            profile=profile_values[0],
            command=command,
            service=service,
            exact_options=(
                ("-f", file_values[0]),
                ("-p", project_values[0]),
                ("--profile", profile_values[0]),
            ),
        )
    if command in {"create", "up", "start", "stop", "restart", "run", "rm", "down"}:
        options_with_value = {
            "--name",
            "--entrypoint",
            "--user",
            "--workdir",
            "-e",
            "--env",
            "-v",
            "--volume",
            "--network",
        }
        flags = set()
        positional: list[str] = []
        index = 0
        while index < len(remainder):
            token = remainder[index]
            if command == "run" and positional:
                positional.append(token)
                index += 1
                continue
            if token in options_with_value:
                if index + 1 >= len(remainder):
                    raise ValueError("compose option missing value")
                index += 2
                continue
            if token in {
                "--rm",
                "--no-deps",
                "-d",
                "--detach",
                "-f",
                "--force",
                "--volumes",
                "--remove-orphans",
            }:
                flags.add(token)
                index += 1
                continue
            if token.startswith("-"):
                raise ValueError("compose command option mismatch")
            positional.append(token)
            index += 1
        if command == "down":
            if positional:
                raise ValueError("compose down operands mismatch")
            if flags != {"--volumes", "--remove-orphans"}:
                raise ValueError("compose down flags mismatch")
        else:
            if not positional:
                raise ValueError("compose service missing")
            if any(service not in ALLOWED_SERVICES for service in positional[:1]):
                raise ValueError("compose service mismatch")
            if command == "up" and not ({"-d", "--detach"} & flags):
                raise ValueError("compose up flags mismatch")
            if command == "rm" and not ({"-f", "--force"} & flags):
                raise ValueError("compose rm flags mismatch")
            if command == "run":
                if flags not in ({"--rm"}, {"--rm", "--no-deps"}):
                    raise ValueError("compose run flags mismatch")
                if "-d" in flags or "--detach" in flags:
                    raise ValueError("compose run flags mismatch")
        return ComposeOperationPlan(
            argv=argv,
            command_class={
                "create": DockerCommandClass.COMPOSE_CREATE,
                "up": DockerCommandClass.COMPOSE_UP,
                "start": DockerCommandClass.COMPOSE_START,
                "stop": DockerCommandClass.COMPOSE_STOP,
                "restart": DockerCommandClass.COMPOSE_RESTART,
                "run": DockerCommandClass.COMPOSE_RUN,
                "rm": DockerCommandClass.COMPOSE_RM,
                "down": DockerCommandClass.COMPOSE_DOWN,
            }[command],
            target_kind="compose_project",
            target_identity_hash=_canonical_compose_identity(
                command,
                positional[0] if positional else None,
                file_values[0],
                project_values[0],
                profile_values[0],
            ),
            is_mutation=True,
            compose_file=file_values[0],
            project_name=project_values[0],
            profile=profile_values[0],
            command=command,
            service=positional[0] if positional else None,
            exact_options=(
                ("-f", file_values[0]),
                ("-p", project_values[0]),
                ("--profile", profile_values[0]),
            ),
        )
    raise ValueError("unknown compose command")


def _direct_plan(argv: tuple[str, ...]) -> DockerInvocationPlan:
    if len(argv) < 2 or argv[0] != "docker":
        raise ValueError("not docker")
    command = argv[1]
    if command == "version":
        if argv[2:] not in {("--format", "{{json .Server}}"), ("--format", "{{json .Client}}")}:
            raise ValueError("version mismatch")
        return ReadOnlyDockerQuery(
            argv,
            DockerCommandClass.READ_ONLY,
            "daemon",
            _sha256(" ".join(argv)),
            False,
            command=command,
        )
    if command == "inspect":
        return ReadOnlyDockerQuery(
            argv,
            DockerCommandClass.READ_ONLY,
            "target",
            _sha256(" ".join(argv)),
            False,
            command=command,
        )
    if command == "ps":
        if argv[2:] not in {("-aq",), ("-q",), ("-a", "-q")} and "-aq" not in argv[2:]:
            raise ValueError("ps mismatch")
        return ReadOnlyDockerQuery(
            argv,
            DockerCommandClass.READ_ONLY,
            "target",
            _sha256(" ".join(argv)),
            False,
            command=command,
        )
    if command == "image" and len(argv) > 2:
        if argv[2] == "inspect":
            return ReadOnlyDockerQuery(
                argv,
                DockerCommandClass.READ_ONLY,
                "image",
                _sha256(" ".join(argv)),
                False,
                command="inspect",
            )
        if argv[2] == "build":
            return ImageBuildPlan(
                argv,
                DockerCommandClass.IMAGE_BUILD,
                "image",
                _sha256(" ".join(argv)),
                True,
                command="build",
            )
        if argv[2] == "load":
            return ImageLoadPlan(
                argv,
                DockerCommandClass.IMAGE_LOAD,
                "image",
                _sha256(" ".join(argv)),
                True,
                command="load",
            )
    if command == "buildx" and len(argv) > 2 and argv[2] == "build":
        return BuildxManifestPlan(
            argv,
            DockerCommandClass.BUILDX_BUILD,
            "image",
            _sha256(" ".join(argv)),
            True,
            command="build",
        )
    if command == "buildx" and len(argv) > 2 and argv[2] in {"create", "rm"}:
        return BuilderScopePlan(
            argv,
            DockerCommandClass.TASK_SCOPED_BUILDER_CREATE
            if argv[2] == "create"
            else DockerCommandClass.TASK_SCOPED_BUILDER_REMOVE,
            "builder",
            _sha256(" ".join(argv)),
            True,
            command=argv[2],
        )
    if command == "buildx" and len(argv) > 2 and argv[2] == "ls":
        return ReadOnlyDockerQuery(
            argv,
            DockerCommandClass.READ_ONLY,
            "builder",
            _sha256(" ".join(argv)),
            False,
            command="ls",
        )
    if command == "run":
        pairs = _split_option_pairs(argv[2:])
        if (
            "--privileged" in pairs
            or "--pid" in pairs
            or "--ipc" in pairs
            or "--device" in pairs
            or "--cap-add" in pairs
            or "--network" in pairs
            and any(v != "none" for v in pairs.get("--network", []))
            or "--publish" in pairs
            or "-p" in pairs
        ):
            raise ValueError("unsafe run flags")
        if "--name" not in pairs or "--label" not in pairs or "--rm" not in pairs:
            raise ValueError("run contract incomplete")
        labels = pairs.get("--label", [])
        label_map: dict[str, str] = {}
        for item in labels:
            if "=" not in item:
                raise ValueError("malformed label")
            key, value = item.split("=", 1)
            label_map[key] = value
        if label_map.get("com.docker.compose.project") != TASK_PROJECT:
            raise ValueError("run project mismatch")
        if label_map.get("com.avito-mayak.technical-id") != TECHNICAL_ID:
            raise ValueError("run technical id mismatch")
        if label_map.get("com.avito-mayak.owner") != ALLOWED_OWNER:
            raise ValueError("run owner mismatch")
        name = pairs.get("--name", [""])[0]
        if name != "apm-postgres" and not name.startswith(TASK_PROJECT):
            raise ValueError("run name mismatch")
        return ContainerProbeCreationPlan(
            argv,
            DockerCommandClass.DIRECT_RUN,
            "container",
            _sha256(" ".join(argv)),
            True,
            command=command,
        )
    if command == "rm":
        return ContainerRemovalPlan(
            argv,
            DockerCommandClass.DIRECT_CONTAINER_RM,
            "container",
            _sha256(" ".join(argv)),
            True,
            command=command,
        )
    if command == "network" and len(argv) > 2:
        if argv[2] == "create":
            return NetworkCreationPlan(
                argv,
                DockerCommandClass.NETWORK_CREATE,
                "network",
                _sha256(" ".join(argv)),
                True,
                command="create",
            )
        if argv[2] == "rm":
            return NetworkCreationPlan(
                argv,
                DockerCommandClass.NETWORK_RM,
                "network",
                _sha256(" ".join(argv)),
                True,
                command="rm",
            )
        if argv[2] == "ls":
            return ReadOnlyDockerQuery(
                argv,
                DockerCommandClass.READ_ONLY,
                "network",
                _sha256(" ".join(argv)),
                False,
                command="ls",
            )
    if command == "volume" and len(argv) > 2:
        if argv[2] == "create":
            return VolumeCreationPlan(
                argv,
                DockerCommandClass.VOLUME_CREATE,
                "volume",
                _sha256(" ".join(argv)),
                True,
                command="create",
            )
        if argv[2] == "rm":
            return VolumeCreationPlan(
                argv,
                DockerCommandClass.VOLUME_RM,
                "volume",
                _sha256(" ".join(argv)),
                True,
                command="rm",
            )
        if argv[2] == "ls":
            return ReadOnlyDockerQuery(
                argv,
                DockerCommandClass.READ_ONLY,
                "volume",
                _sha256(" ".join(argv)),
                False,
                command="ls",
            )
    if command == "builder" and len(argv) > 2:
        if argv[2] == "create":
            return BuilderScopePlan(
                argv,
                DockerCommandClass.TASK_SCOPED_BUILDER_CREATE,
                "builder",
                _sha256(" ".join(argv)),
                True,
                command="create",
            )
        if argv[2] == "rm":
            return BuilderScopePlan(
                argv,
                DockerCommandClass.TASK_SCOPED_BUILDER_REMOVE,
                "builder",
                _sha256(" ".join(argv)),
                True,
                command="rm",
            )
    if command == "compose":
        return _compose_plan(argv)
    if command in {"version", "info"}:
        return ReadOnlyDockerQuery(
            argv,
            DockerCommandClass.READ_ONLY,
            "daemon",
            _sha256(" ".join(argv)),
            False,
            command=command,
        )
    if command in {"network", "volume", "image"}:
        return ReadOnlyDockerQuery(
            argv,
            DockerCommandClass.UNKNOWN_DOCKER_COMMAND,
            "unknown",
            _sha256(" ".join(argv)),
            False,
            command=command,
        )
    return ReadOnlyDockerQuery(
        argv,
        DockerCommandClass.UNKNOWN_DOCKER_COMMAND,
        "unknown",
        _sha256(" ".join(argv)),
        False,
        command=command,
    )


def classify_docker_argv(argv: Iterable[str]) -> DockerCommandClass:
    args = tuple(argv)
    if not args or args[0] != "docker":
        return DockerCommandClass.UNKNOWN_DOCKER_COMMAND
    try:
        return _direct_plan(args).command_class
    except ValueError:
        return DockerCommandClass.UNKNOWN_DOCKER_COMMAND


@dataclass(frozen=True, slots=True)
class _CapabilityIssuance:
    capability: ResolvedTaskResourceCapability
    authorization: DockerMutationRecord
    audit: DockerInvocationAuditRecord


@dataclass(frozen=True, slots=True)
class _ResolvedResourceDetails:
    ownership: str
    resource_kind: str
    resource_name: str | None
    immutable_identity_hash: str
    resource_name_hash: str
    project_identity: str
    technical_id: str
    owner_labels_digest: str
    service_identity: str | None
    driver: str | None
    scope: str | None
    topology_digest: str
    label_set_digest: str
    allowed_operations: tuple[str, ...]


@dataclass
class MutationAuthority:
    task_project: str = TASK_PROJECT
    technical_id: str = TECHNICAL_ID
    compose_file: str = COMPOSE_FILE
    profile: str = RUNTIME_PROFILE
    allowed_services: tuple[str, ...] = tuple(sorted(ALLOWED_SERVICES))
    gateway_instance_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    _invocation_audit: list[DockerInvocationAuditRecord] = field(default_factory=list, repr=False)
    _ledger: list[DockerMutationRecord] = field(default_factory=list, repr=False)
    _issued_capabilities: dict[str, _CapabilityIssuance] = field(default_factory=dict, repr=False)
    _invocation_sequence: int = 0
    _authorization_sequence: int = 0
    _result_sequence: int = 0
    _default_env: Mapping[str, str] | None = field(default=None, repr=False)

    @property
    def invocation_audit(self) -> tuple[DockerInvocationAuditRecord, ...]:
        return tuple(self._invocation_audit)

    @property
    def ledger(self) -> tuple[DockerMutationRecord, ...]:
        return tuple(self._ledger)

    @property
    def entries(self) -> tuple[DockerMutationRecord, ...]:
        return self.ledger

    def _resource_name(self, plan: DockerInvocationPlan) -> str | None:
        if plan.command_class in {
            DockerCommandClass.COMPOSE_CREATE,
            DockerCommandClass.COMPOSE_UP,
            DockerCommandClass.COMPOSE_START,
            DockerCommandClass.COMPOSE_STOP,
            DockerCommandClass.COMPOSE_RESTART,
            DockerCommandClass.COMPOSE_RUN,
            DockerCommandClass.COMPOSE_RM,
            DockerCommandClass.COMPOSE_DOWN,
        }:
            return f"{self.task_project}-{plan.service}-1" if plan.service else self.task_project
        if plan.command_class in {
            DockerCommandClass.DIRECT_RUN,
            DockerCommandClass.DIRECT_CONTAINER_RM,
            DockerCommandClass.NETWORK_CREATE,
            DockerCommandClass.NETWORK_RM,
            DockerCommandClass.VOLUME_CREATE,
            DockerCommandClass.VOLUME_RM,
        }:
            pairs = _split_option_pairs(plan.argv[2:])
            if "--name" in pairs and pairs["--name"]:
                return pairs["--name"][0]
            names = [token for token in plan.argv[2:] if not token.startswith("-")]
            return names[-1] if names else None
        if plan.command_class in {
            DockerCommandClass.IMAGE_BUILD,
            DockerCommandClass.IMAGE_LOAD,
            DockerCommandClass.BUILDX_BUILD,
            DockerCommandClass.TASK_SCOPED_BUILDER_CREATE,
            DockerCommandClass.TASK_SCOPED_BUILDER_REMOVE,
        }:
            return plan.argv[-1] if len(plan.argv) > 2 else None
        return None

    def _resolved_labels(
        self, plan: DockerInvocationPlan, *, service: str | None = None
    ) -> dict[str, str]:
        labels = {
            "com.docker.compose.project": self.task_project,
            "com.avito-mayak.technical-id": self.technical_id,
            "com.avito-mayak.owner": ALLOWED_OWNER,
        }
        service_name = service or plan.service
        if service_name:
            labels["com.docker.compose.service"] = service_name
        if plan.command_class in {
            DockerCommandClass.NETWORK_CREATE,
            DockerCommandClass.NETWORK_RM,
            DockerCommandClass.VOLUME_CREATE,
            DockerCommandClass.VOLUME_RM,
        }:
            labels["com.avito-mayak.project-owned"] = "true"
            labels["com.avito-mayak.environment-id"] = "avito-mayak-acceptance-local-01"
            labels["com.avito-mayak.compose-project"] = "avito-mayak-acceptance"
        return labels

    def _inspect_resource(self, kind: str, ident: str) -> dict[str, Any] | None:
        try:
            query = ReadOnlyDockerQuery.from_argv(("docker", kind, "inspect", ident))
        except ValueError:
            return None
        completed = self.run(query, stage=f"inspect-{kind}", capture_output=True)
        if completed.returncode != 0:
            return None
        try:
            value = json.loads(completed.stdout)
        except (TypeError, json.JSONDecodeError):
            return None
        if not isinstance(value, list) or len(value) != 1 or not isinstance(value[0], dict):
            return None
        return value[0]

    def _inspect_kind(self, kind: str, ident: str) -> dict[str, Any] | None:
        return self._inspect_resource(kind, ident)

    def _resource_digest(self, payload: Mapping[str, object]) -> str:
        return _sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")))

    def _current_resolution(self, plan: DockerInvocationPlan) -> _ResolvedResourceDetails:
        resource_name = self._resource_name(plan)
        if plan.command_class == DockerCommandClass.DIRECT_RUN:
            if resource_name == "apm-postgres":
                ownership = "FOREIGN"
                labels = self._resolved_labels(plan)
                identity_hash = plan.target_identity_hash
                topology = {
                    "argv": list(plan.argv),
                    "command_class": plan.command_class.value,
                    "name": resource_name,
                }
                return _ResolvedResourceDetails(
                    ownership=ownership,
                    resource_kind=plan.target_kind,
                    resource_name=resource_name,
                    immutable_identity_hash=identity_hash,
                    resource_name_hash=_sha256(resource_name),
                    project_identity=self.task_project,
                    technical_id=self.technical_id,
                    owner_labels_digest=_sha256(
                        json.dumps(labels, sort_keys=True, separators=(",", ":"))
                    ),
                    service_identity=plan.service,
                    driver=None,
                    scope=None,
                    topology_digest=self._resource_digest(topology),
                    label_set_digest=_sha256(
                        json.dumps(labels, sort_keys=True, separators=(",", ":"))
                    ),
                    allowed_operations=(plan.command_class.value,),
                )
            record = self._inspect_kind("container", resource_name) if resource_name else None
            labels = self._resolved_labels(plan)
            if record is not None:
                raw_labels = record.get("Config", {}).get("Labels", {})
                if not isinstance(raw_labels, dict):
                    raw_labels = {}
                service = str(raw_labels.get("com.docker.compose.service", ""))
                task_owned = (
                    isinstance(resource_name, str)
                    and raw_labels.get("com.docker.compose.project") == self.task_project
                    and raw_labels.get("com.avito-mayak.technical-id") == self.technical_id
                    and raw_labels.get("com.avito-mayak.project-owned") == "true"
                    and raw_labels.get("com.avito-mayak.environment-id")
                    == "avito-mayak-acceptance-local-01"
                    and raw_labels.get("com.avito-mayak.compose-project")
                    == "avito-mayak-acceptance"
                    and service in self.allowed_services
                    and isinstance(record.get("Id") or record.get("ID") or "", str)
                )
                if task_owned:
                    assert isinstance(resource_name, str)
                    identity_hash = _sha256(str(record.get("Id") or record.get("ID") or ""))
                    return _ResolvedResourceDetails(
                        ownership="TASK_OWNED",
                        resource_kind=plan.target_kind,
                        resource_name=resource_name,
                        immutable_identity_hash=identity_hash,
                        resource_name_hash=_sha256(resource_name),
                        project_identity=self.task_project,
                        technical_id=self.technical_id,
                        owner_labels_digest=_sha256(
                            json.dumps(raw_labels, sort_keys=True, separators=(",", ":"))
                        ),
                        service_identity=service,
                        driver=str(record.get("HostConfig", {}).get("NetworkMode"))
                        if isinstance(record.get("HostConfig"), dict)
                        else None,
                        scope=str(record.get("State", {}).get("Status"))
                        if isinstance(record.get("State"), dict)
                        else None,
                        topology_digest=self._resource_digest(
                            {
                                "id": identity_hash,
                                "name": resource_name,
                                "labels": raw_labels,
                            }
                        ),
                        label_set_digest=_sha256(
                            json.dumps(raw_labels, sort_keys=True, separators=(",", ":"))
                        ),
                        allowed_operations=(plan.command_class.value,),
                    )
            if resource_name and resource_name.startswith(self.task_project):
                ownership = "TASK_OWNED"
            else:
                ownership = "UNRESOLVED"
            return _ResolvedResourceDetails(
                ownership=ownership,
                resource_kind=plan.target_kind,
                resource_name=resource_name,
                immutable_identity_hash=plan.target_identity_hash,
                resource_name_hash=_sha256(resource_name or plan.target_identity_hash),
                project_identity=self.task_project,
                technical_id=self.technical_id,
                owner_labels_digest=_sha256(
                    json.dumps(labels, sort_keys=True, separators=(",", ":"))
                ),
                service_identity=plan.service,
                driver=None,
                scope=None,
                topology_digest=self._resource_digest(
                    {
                        "argv": list(plan.argv),
                        "command_class": plan.command_class.value,
                        "service": plan.service,
                    }
                ),
                label_set_digest=_sha256(json.dumps(labels, sort_keys=True, separators=(",", ":"))),
                allowed_operations=(plan.command_class.value,),
            )
        if plan.command_class == DockerCommandClass.DIRECT_CONTAINER_RM:
            if resource_name == "apm-postgres":
                ownership = "FOREIGN"
                labels = self._resolved_labels(plan)
                return _ResolvedResourceDetails(
                    ownership=ownership,
                    resource_kind=plan.target_kind,
                    resource_name=resource_name,
                    immutable_identity_hash=plan.target_identity_hash,
                    resource_name_hash=_sha256(resource_name),
                    project_identity=self.task_project,
                    technical_id=self.technical_id,
                    owner_labels_digest=_sha256(
                        json.dumps(labels, sort_keys=True, separators=(",", ":"))
                    ),
                    service_identity=None,
                    driver=None,
                    scope=None,
                    topology_digest=self._resource_digest(
                        {"argv": list(plan.argv), "command_class": plan.command_class.value}
                    ),
                    label_set_digest=_sha256(
                        json.dumps(labels, sort_keys=True, separators=(",", ":"))
                    ),
                    allowed_operations=(plan.command_class.value,),
                )
            record = self._inspect_kind("container", resource_name) if resource_name else None
            if record is None:
                ownership = (
                    "UNRESOLVED"
                    if isinstance(resource_name, str)
                    and resource_name.startswith(self.task_project)
                    else "FOREIGN"
                )
                return _ResolvedResourceDetails(
                    ownership=ownership,
                    resource_kind=plan.target_kind,
                    resource_name=resource_name,
                    immutable_identity_hash=plan.target_identity_hash,
                    resource_name_hash=_sha256(resource_name or plan.target_identity_hash),
                    project_identity=self.task_project,
                    technical_id=self.technical_id,
                    owner_labels_digest=_sha256(
                        json.dumps(
                            self._resolved_labels(plan), sort_keys=True, separators=(",", ":")
                        )
                    ),
                    service_identity=None,
                    driver=None,
                    scope=None,
                    topology_digest=self._resource_digest(
                        {"argv": list(plan.argv), "command_class": plan.command_class.value}
                    ),
                    label_set_digest=_sha256(
                        json.dumps(
                            self._resolved_labels(plan), sort_keys=True, separators=(",", ":")
                        )
                    ),
                    allowed_operations=(plan.command_class.value,),
                )
            raw_labels = record.get("Config", {}).get("Labels", {})
            if not isinstance(raw_labels, dict):
                raw_labels = {}
            service = str(raw_labels.get("com.docker.compose.service", ""))
            task_owned = (
                isinstance(resource_name, str)
                and raw_labels.get("com.docker.compose.project") == self.task_project
                and raw_labels.get("com.avito-mayak.technical-id") == self.technical_id
                and raw_labels.get("com.avito-mayak.project-owned") == "true"
                and raw_labels.get("com.avito-mayak.environment-id")
                == "avito-mayak-acceptance-local-01"
                and raw_labels.get("com.avito-mayak.compose-project")
                == "avito-mayak-acceptance"
                and service in self.allowed_services
                and isinstance(record.get("Id") or record.get("ID") or "", str)
            )
            ownership = "TASK_OWNED" if task_owned else "UNRESOLVED"
            identity = str(record.get("Id") or record.get("ID") or plan.target_identity_hash)
            return _ResolvedResourceDetails(
                ownership=ownership,
                resource_kind=plan.target_kind,
                resource_name=resource_name,
                immutable_identity_hash=_sha256(identity),
                resource_name_hash=_sha256(resource_name or identity),
                project_identity=self.task_project,
                technical_id=self.technical_id,
                owner_labels_digest=_sha256(
                    json.dumps(raw_labels, sort_keys=True, separators=(",", ":"))
                ),
                service_identity=service or None,
                driver=str(record.get("HostConfig", {}).get("NetworkMode"))
                if isinstance(record.get("HostConfig"), dict)
                else None,
                scope=str(record.get("State", {}).get("Status"))
                if isinstance(record.get("State"), dict)
                else None,
                topology_digest=self._resource_digest(
                    {"id": identity, "name": resource_name, "labels": raw_labels}
                ),
                label_set_digest=_sha256(
                    json.dumps(raw_labels, sort_keys=True, separators=(",", ":"))
                ),
                allowed_operations=(plan.command_class.value,),
            )
        if plan.command_class in {
            DockerCommandClass.COMPOSE_CREATE,
            DockerCommandClass.COMPOSE_UP,
            DockerCommandClass.COMPOSE_START,
            DockerCommandClass.COMPOSE_STOP,
            DockerCommandClass.COMPOSE_RESTART,
            DockerCommandClass.COMPOSE_RUN,
            DockerCommandClass.COMPOSE_RM,
            DockerCommandClass.COMPOSE_DOWN,
        }:
            labels = self._resolved_labels(plan, service=plan.service)
            record = self._inspect_kind("container", resource_name) if resource_name else None
            if plan.service == "apm-postgres":
                ownership = "FOREIGN"
            elif (
                plan.command_class == DockerCommandClass.COMPOSE_DOWN
                and resource_name == self.task_project
            ):
                ownership = "TASK_OWNED"
            elif record is not None:
                raw_labels = record.get("Config", {}).get("Labels", {})
                if not isinstance(raw_labels, dict):
                    raw_labels = {}
                exact = (
                    raw_labels.get("com.docker.compose.project") == self.task_project
                    and raw_labels.get("com.avito-mayak.technical-id") == self.technical_id
                    and raw_labels.get("com.avito-mayak.project-owned") == "true"
                    and raw_labels.get("com.avito-mayak.environment-id")
                    == "avito-mayak-acceptance-local-01"
                    and raw_labels.get("com.avito-mayak.compose-project")
                    == "avito-mayak-acceptance"
                    and raw_labels.get("com.docker.compose.service") == plan.service
                    and resource_name == f"{self.task_project}-{plan.service}-1"
                )
                ownership = "TASK_OWNED" if exact else "UNRESOLVED"
                labels = raw_labels
            elif plan.command_class in {
                DockerCommandClass.COMPOSE_CREATE,
                DockerCommandClass.COMPOSE_UP,
                DockerCommandClass.COMPOSE_START,
                DockerCommandClass.COMPOSE_STOP,
                DockerCommandClass.COMPOSE_RESTART,
                DockerCommandClass.COMPOSE_RUN,
                DockerCommandClass.COMPOSE_RM,
                DockerCommandClass.COMPOSE_DOWN,
            }:
                ownership = "TASK_OWNED"
            else:
                ownership = "UNRESOLVED"
            identity = (
                str(record.get("Id") or record.get("ID") or "")
                if record is not None
                else plan.target_identity_hash
            )
            return _ResolvedResourceDetails(
                ownership=ownership,
                resource_kind=plan.target_kind,
                resource_name=resource_name,
                immutable_identity_hash=_sha256(identity or plan.target_identity_hash),
                resource_name_hash=_sha256(resource_name or identity or plan.target_identity_hash),
                project_identity=self.task_project,
                technical_id=self.technical_id,
                owner_labels_digest=_sha256(
                    json.dumps(labels, sort_keys=True, separators=(",", ":"))
                ),
                service_identity=plan.service,
                driver=None,
                scope=plan.profile,
                topology_digest=self._resource_digest(
                    {
                        "argv": list(plan.argv),
                        "command": plan.command,
                        "service": plan.service,
                        "compose_file": plan.compose_file,
                    }
                ),
                label_set_digest=_sha256(json.dumps(labels, sort_keys=True, separators=(",", ":"))),
                allowed_operations=(plan.command_class.value,),
            )
        if plan.command_class in {
            DockerCommandClass.NETWORK_CREATE,
            DockerCommandClass.NETWORK_RM,
        }:
            labels = self._resolved_labels(plan)
            record = self._inspect_kind("network", resource_name) if resource_name else None
            if record is not None:
                raw_labels = record.get("Labels", {})
                if not isinstance(raw_labels, dict):
                    raw_labels = {}
                exact = (
                    raw_labels.get("com.docker.compose.project") == self.task_project
                    and raw_labels.get("com.avito-mayak.technical-id") == self.technical_id
                    and raw_labels.get("com.avito-mayak.project-owned") == "true"
                    and raw_labels.get("com.avito-mayak.environment-id")
                    == "avito-mayak-acceptance-local-01"
                    and raw_labels.get("com.avito-mayak.compose-project")
                    == "avito-mayak-acceptance"
                    and isinstance(record.get("Driver"), str)
                    and isinstance(record.get("Scope"), str)
                    and isinstance(record.get("Internal"), bool)
                    and isinstance(record.get("Attachable"), bool)
                    and isinstance(record.get("Ingress"), bool)
                    and resource_name == f"{self.task_project}_mayak-internal"
                )
                if exact:
                    identity = str(record.get("Id") or record.get("ID") or "")
                    return _ResolvedResourceDetails(
                        ownership="TASK_OWNED",
                        resource_kind=plan.target_kind,
                        resource_name=resource_name,
                        immutable_identity_hash=_sha256(identity or plan.target_identity_hash),
                        resource_name_hash=_sha256(resource_name or identity),
                        project_identity=self.task_project,
                        technical_id=self.technical_id,
                        owner_labels_digest=_sha256(
                            json.dumps(raw_labels, sort_keys=True, separators=(",", ":"))
                        ),
                        service_identity=None,
                        driver=str(record.get("Driver")),
                        scope=str(record.get("Scope")),
                        topology_digest=self._resource_digest(
                            {
                                "driver": record.get("Driver"),
                                "scope": record.get("Scope"),
                                "internal": record.get("Internal"),
                                "attachable": record.get("Attachable"),
                                "ingress": record.get("Ingress"),
                                "name": resource_name,
                        }
                    ),
                    label_set_digest=_sha256(
                        json.dumps(raw_labels, sort_keys=True, separators=(",", ":"))
                    ),
                    allowed_operations=(plan.command_class.value,),
                )
                labels = raw_labels
            if plan.command_class == DockerCommandClass.NETWORK_CREATE and resource_name == (
                f"{self.task_project}_mayak-internal"
            ):
                ownership = "TASK_OWNED"
            elif resource_name and resource_name.startswith(self.task_project):
                ownership = "UNRESOLVED"
            else:
                ownership = "FOREIGN"
            return _ResolvedResourceDetails(
                ownership=ownership,
                resource_kind=plan.target_kind,
                resource_name=resource_name,
                immutable_identity_hash=plan.target_identity_hash,
                resource_name_hash=_sha256(resource_name or plan.target_identity_hash),
                project_identity=self.task_project,
                technical_id=self.technical_id,
                owner_labels_digest=_sha256(
                    json.dumps(labels, sort_keys=True, separators=(",", ":"))
                ),
                service_identity=None,
                driver=None,
                scope=None,
                topology_digest=self._resource_digest(
                    {
                        "argv": list(plan.argv),
                        "command_class": plan.command_class.value,
                        "name": resource_name,
                    }
                ),
                label_set_digest=_sha256(json.dumps(labels, sort_keys=True, separators=(",", ":"))),
                allowed_operations=(plan.command_class.value,),
            )
        if plan.command_class in {
            DockerCommandClass.VOLUME_CREATE,
            DockerCommandClass.VOLUME_RM,
        }:
            labels = self._resolved_labels(plan)
            record = self._inspect_kind("volume", resource_name) if resource_name else None
            if record is not None:
                raw_labels = record.get("Labels", {})
                if not isinstance(raw_labels, dict):
                    raw_labels = {}
                exact = (
                    raw_labels.get("com.docker.compose.project") == self.task_project
                    and raw_labels.get("com.avito-mayak.technical-id") == self.technical_id
                    and raw_labels.get("com.avito-mayak.project-owned") == "true"
                    and raw_labels.get("com.avito-mayak.environment-id")
                    == "avito-mayak-acceptance-local-01"
                    and raw_labels.get("com.avito-mayak.compose-project")
                    == "avito-mayak-acceptance"
                    and isinstance(record.get("Driver"), str)
                    and isinstance(record.get("Scope"), str)
                )
                if exact:
                    identity = str(record.get("Id") or record.get("ID") or "")
                    return _ResolvedResourceDetails(
                        ownership="TASK_OWNED",
                        resource_kind=plan.target_kind,
                        resource_name=resource_name,
                        immutable_identity_hash=_sha256(identity or plan.target_identity_hash),
                        resource_name_hash=_sha256(resource_name or identity),
                        project_identity=self.task_project,
                        technical_id=self.technical_id,
                        owner_labels_digest=_sha256(
                            json.dumps(raw_labels, sort_keys=True, separators=(",", ":"))
                        ),
                        service_identity=None,
                        driver=str(record.get("Driver")),
                        scope=str(record.get("Scope")),
                        topology_digest=self._resource_digest(
                            {
                                "driver": record.get("Driver"),
                                "scope": record.get("Scope"),
                                "name": resource_name,
                            }
                        ),
                        label_set_digest=_sha256(
                            json.dumps(raw_labels, sort_keys=True, separators=(",", ":"))
                        ),
                        allowed_operations=(plan.command_class.value,),
                    )
                labels = raw_labels
            if plan.command_class == DockerCommandClass.VOLUME_CREATE and resource_name == (
                f"{self.task_project}_postgres-data"
            ):
                ownership = "TASK_OWNED"
            elif resource_name and resource_name.startswith(self.task_project):
                ownership = "UNRESOLVED"
            else:
                ownership = "FOREIGN"
            return _ResolvedResourceDetails(
                ownership=ownership,
                resource_kind=plan.target_kind,
                resource_name=resource_name,
                immutable_identity_hash=plan.target_identity_hash,
                resource_name_hash=_sha256(resource_name or plan.target_identity_hash),
                project_identity=self.task_project,
                technical_id=self.technical_id,
                owner_labels_digest=_sha256(
                    json.dumps(labels, sort_keys=True, separators=(",", ":"))
                ),
                service_identity=None,
                driver=None,
                scope=None,
                topology_digest=self._resource_digest(
                    {
                        "argv": list(plan.argv),
                        "command_class": plan.command_class.value,
                        "name": resource_name,
                    }
                ),
                label_set_digest=_sha256(json.dumps(labels, sort_keys=True, separators=(",", ":"))),
                allowed_operations=(plan.command_class.value,),
            )
        labels = self._resolved_labels(plan)
        ownership = "TASK_OWNED" if plan.is_mutation else "FOREIGN"
        if plan.command_class in {
            DockerCommandClass.IMAGE_BUILD,
            DockerCommandClass.IMAGE_LOAD,
            DockerCommandClass.BUILDX_BUILD,
            DockerCommandClass.TASK_SCOPED_BUILDER_CREATE,
            DockerCommandClass.TASK_SCOPED_BUILDER_REMOVE,
        }:
            identity = plan.target_identity_hash
            builder_topology: dict[str, object] = {
                "argv": list(plan.argv),
                "command_class": plan.command_class.value,
                "compose_file": plan.compose_file,
                "project_name": plan.project_name,
                "profile": plan.profile,
            }
            return _ResolvedResourceDetails(
                ownership=ownership,
                resource_kind=plan.target_kind,
                resource_name=resource_name,
                immutable_identity_hash=identity,
                resource_name_hash=_sha256(resource_name or identity),
                project_identity=self.task_project,
                technical_id=self.technical_id,
                owner_labels_digest=_sha256(
                    json.dumps(labels, sort_keys=True, separators=(",", ":"))
                ),
                service_identity=plan.service,
                driver=plan.command_class.value,
                scope=self.profile,
                topology_digest=self._resource_digest(builder_topology),
                label_set_digest=_sha256(json.dumps(labels, sort_keys=True, separators=(",", ":"))),
                allowed_operations=(plan.command_class.value,),
            )
        return _ResolvedResourceDetails(
            ownership=ownership,
            resource_kind=plan.target_kind,
            resource_name=resource_name,
            immutable_identity_hash=plan.target_identity_hash,
            resource_name_hash=_sha256(resource_name or plan.target_identity_hash),
            project_identity=self.task_project,
            technical_id=self.technical_id,
            owner_labels_digest=_sha256(json.dumps(labels, sort_keys=True, separators=(",", ":"))),
            service_identity=plan.service,
            driver=None,
            scope=None,
            topology_digest=self._resource_digest({"argv": list(plan.argv)}),
            label_set_digest=_sha256(json.dumps(labels, sort_keys=True, separators=(",", ":"))),
            allowed_operations=(plan.command_class.value,),
        )

    def _authorization_basis(self, plan: DockerInvocationPlan) -> str:
        if plan.command_class in {
            DockerCommandClass.COMPOSE_CREATE,
            DockerCommandClass.COMPOSE_UP,
            DockerCommandClass.COMPOSE_START,
            DockerCommandClass.COMPOSE_STOP,
            DockerCommandClass.COMPOSE_RESTART,
            DockerCommandClass.COMPOSE_RUN,
            DockerCommandClass.COMPOSE_RM,
            DockerCommandClass.COMPOSE_DOWN,
            DockerCommandClass.DIRECT_RUN,
            DockerCommandClass.DIRECT_CONTAINER_RM,
            DockerCommandClass.NETWORK_CREATE,
            DockerCommandClass.NETWORK_RM,
            DockerCommandClass.VOLUME_CREATE,
            DockerCommandClass.VOLUME_RM,
            DockerCommandClass.IMAGE_BUILD,
            DockerCommandClass.IMAGE_LOAD,
            DockerCommandClass.BUILDX_BUILD,
            DockerCommandClass.TASK_SCOPED_BUILDER_CREATE,
            DockerCommandClass.TASK_SCOPED_BUILDER_REMOVE,
        }:
            return "TASK_CREATION_PLAN"
        return "READ_ONLY_INSPECT"

    def _record_audit(
        self, plan: DockerInvocationPlan, *, stage: str
    ) -> DockerInvocationAuditRecord:
        self._invocation_sequence += 1
        record = DockerInvocationAuditRecord(
            invocation_sequence=self._invocation_sequence,
            stage=stage,
            command_class=plan.command_class.value,
            argv_fingerprint=_fingerprint(plan.argv),
            target_kind=plan.target_kind,
            target_identity_hash=plan.target_identity_hash,
            is_mutation=plan.is_mutation,
            gateway_instance_id=self.gateway_instance_id,
        )
        self._invocation_audit.append(record)
        return record

    def _issue_capability(
        self,
        plan: DockerInvocationPlan,
        *,
        details: _ResolvedResourceDetails,
        audit: DockerInvocationAuditRecord,
        authorization: DockerMutationRecord,
    ) -> ResolvedTaskResourceCapability:
        capability = ResolvedTaskResourceCapability(
            gateway_instance_id=self.gateway_instance_id,
            issuance_id=uuid.uuid4().hex,
            seal=uuid.uuid4().hex,
            resource_kind=details.resource_kind,
            immutable_identity_hash=details.immutable_identity_hash,
            resource_name_hash=details.resource_name_hash,
            project_identity=details.project_identity,
            technical_id=details.technical_id,
            owner_labels_digest=details.owner_labels_digest,
            service_identity=details.service_identity,
            driver=details.driver,
            scope=details.scope,
            topology_digest=details.topology_digest,
            label_set_digest=details.label_set_digest,
            allowed_operations=details.allowed_operations,
        )
        self._issued_capabilities[capability.issuance_id] = _CapabilityIssuance(
            capability=capability,
            authorization=authorization,
            audit=audit,
        )
        return capability

    def _validate_capability(
        self, capability: ResolvedTaskResourceCapability, plan: DockerInvocationPlan
    ) -> _CapabilityIssuance:
        if capability.gateway_instance_id != self.gateway_instance_id:
            raise PermissionError("foreign capability gateway")
        issuance = self._issued_capabilities.get(capability.issuance_id)
        if issuance is None or issuance.capability is not capability:
            raise PermissionError("unknown capability issuance")
        if capability.allowed_operations != (plan.command_class.value,):
            raise PermissionError("capability operation mismatch")
        details = self._current_resolution(plan)
        expected = {
            "resource_kind": details.resource_kind,
            "immutable_identity_hash": details.immutable_identity_hash,
            "resource_name_hash": details.resource_name_hash,
            "project_identity": details.project_identity,
            "technical_id": details.technical_id,
            "owner_labels_digest": details.owner_labels_digest,
            "service_identity": details.service_identity,
            "driver": details.driver,
            "scope": details.scope,
            "topology_digest": details.topology_digest,
            "label_set_digest": details.label_set_digest,
        }
        for key, value in expected.items():
            if getattr(capability, key) != value:
                raise PermissionError("stale or mismatched capability")
        if details.ownership != "TASK_OWNED":
            raise PermissionError("capability no longer authorized")
        return issuance

    def _record_authorization(
        self,
        *,
        plan: DockerInvocationPlan,
        stage: str,
        audit: DockerInvocationAuditRecord,
        details: _ResolvedResourceDetails,
        outcome: str,
    ) -> DockerMutationRecord:
        self._authorization_sequence += 1
        record = DockerMutationRecord(
            record_type="AUTHORIZATION",
            authorization_sequence=self._authorization_sequence,
            execution_result_sequence=None,
            invocation_sequence=audit.invocation_sequence,
            stage=stage,
            command_class=plan.command_class.value,
            target_kind=plan.target_kind,
            target_identity_hash=details.immutable_identity_hash,
            authorization_basis=self._authorization_basis(plan),
            authorization_outcome=outcome,
            execution_attempted=False,
            execution_completed=False,
            target_ownership=details.ownership,
            argv_fingerprint=audit.argv_fingerprint,
        )
        self._ledger.append(record)
        return record

    def _resolve_and_authorize(
        self, plan: DockerInvocationPlan, *, stage: str
    ) -> tuple[DockerInvocationAuditRecord, DockerMutationRecord, ResolvedTaskResourceCapability]:
        audit = self._record_audit(plan, stage=stage)
        details = self._current_resolution(plan)
        if details.ownership != "TASK_OWNED":
            authorization = self._record_authorization(
                plan=plan,
                stage=stage,
                audit=audit,
                details=details,
                outcome="REJECTED",
            )
            raise PermissionError("foreign or unresolved target")
        authorization = self._record_authorization(
            plan=plan,
            stage=stage,
            audit=audit,
            details=details,
            outcome="AUTHORIZED",
        )
        capability = self._issue_capability(
            plan,
            details=details,
            audit=audit,
            authorization=authorization,
        )
        return audit, authorization, capability

    def authorize(
        self, plan: DockerInvocationPlan, *, stage: str
    ) -> ResolvedTaskResourceCapability:
        if not plan.is_mutation:
            raise ValueError("read-only command is not a mutation")
        _, _, capability = self._resolve_and_authorize(plan, stage=stage)
        return capability

    def _record_result(
        self,
        authorization: DockerMutationRecord,
        *,
        exit_code: int | None,
        completed: bool,
        timed_out: bool,
        failure_classification: str | None,
    ) -> DockerMutationRecord:
        self._result_sequence += 1
        record = DockerMutationRecord(
            record_type="RESULT",
            authorization_sequence=authorization.authorization_sequence,
            execution_result_sequence=self._result_sequence,
            invocation_sequence=authorization.invocation_sequence,
            stage=authorization.stage,
            command_class=authorization.command_class,
            target_kind=authorization.target_kind,
            target_identity_hash=authorization.target_identity_hash,
            authorization_basis=authorization.authorization_basis,
            authorization_outcome=authorization.authorization_outcome,
            execution_attempted=True,
            execution_completed=completed,
            exit_code=exit_code,
            timed_out=timed_out,
            safe_failure_classification=failure_classification,
            target_ownership=authorization.target_ownership,
            argv_fingerprint=authorization.argv_fingerprint,
        )
        self._ledger.append(record)
        return record

    def execute(
        self,
        plan: DockerInvocationPlan,
        *,
        stage: str,
        capability: ResolvedTaskResourceCapability | None = None,
        stdin: Any = None,
        stdout: Any = None,
        stderr: Any = None,
        timeout: float | None = None,
        check: bool = False,
        text: bool = False,
        capture_output: bool = False,
    ) -> subprocess.CompletedProcess[Any]:
        if not plan.is_mutation:
            raise ValueError("read-only command is not a mutation")
        if capability is None:
            capability = self.authorize(plan, stage=stage)
        else:
            audit = self._record_audit(plan, stage=stage)
            details = self._current_resolution(plan)
            try:
                issuance = self._validate_capability(capability, plan)
            except PermissionError:
                self._record_authorization(
                    plan=plan,
                    stage=stage,
                    audit=audit,
                    details=details,
                    outcome="REJECTED",
                )
                raise
            authorization = issuance.authorization
            # The validation above proves the capability still matches the current resource.
            try:
                completed = self._run_subprocess(
                    plan.argv,
                    stdin=stdin,
                    stdout=stdout,
                    stderr=stderr,
                    timeout=timeout,
                    check=check,
                    text=text,
                    capture_output=capture_output,
                )
            except subprocess.TimeoutExpired:
                self._record_result(
                    authorization,
                    exit_code=None,
                    completed=False,
                    timed_out=True,
                    failure_classification="TimeoutExpired",
                )
                raise
            except OSError as exc:
                self._record_result(
                    authorization,
                    exit_code=None,
                    completed=False,
                    timed_out=False,
                    failure_classification=type(exc).__name__,
                )
                raise
            except subprocess.CalledProcessError as exc:
                self._record_result(
                    authorization,
                    exit_code=exc.returncode,
                    completed=True,
                    timed_out=False,
                    failure_classification=type(exc).__name__,
                )
                raise
            else:
                self._record_result(
                    authorization,
                    exit_code=completed.returncode,
                    completed=True,
                    timed_out=False,
                    failure_classification=None,
                )
                return completed
        issuance = self._issued_capabilities[capability.issuance_id]
        authorization = issuance.authorization
        try:
            completed = self._run_subprocess(
                plan.argv,
                stdin=stdin,
                stdout=stdout,
                stderr=stderr,
                timeout=timeout,
                check=check,
                text=text,
                capture_output=capture_output,
            )
        except subprocess.TimeoutExpired:
            self._record_result(
                authorization,
                exit_code=None,
                completed=False,
                timed_out=True,
                failure_classification="TimeoutExpired",
            )
            raise
        except OSError as exc:
            self._record_result(
                authorization,
                exit_code=None,
                completed=False,
                timed_out=False,
                failure_classification=type(exc).__name__,
            )
            raise
        except subprocess.CalledProcessError as exc:
            self._record_result(
                authorization,
                exit_code=exc.returncode,
                completed=True,
                timed_out=False,
                failure_classification=type(exc).__name__,
            )
            raise
        else:
            self._record_result(
                authorization,
                exit_code=completed.returncode,
                completed=True,
                timed_out=False,
                failure_classification=None,
            )
            return completed

    def run(
        self,
        query: ReadOnlyDockerQuery,
        *,
        stage: str,
        stdin: Any = None,
        stdout: Any = None,
        stderr: Any = None,
        timeout: float | None = None,
        check: bool = False,
        text: bool = False,
        capture_output: bool = False,
    ) -> subprocess.CompletedProcess[Any]:
        if not isinstance(query, ReadOnlyDockerQuery):
            raise TypeError("read-only Docker queries must use ReadOnlyDockerQuery")
        self._record_audit(query, stage=stage)
        if query.is_mutation:
            raise ValueError("query is not read-only")
        return self._run_subprocess(
            query.argv,
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
            timeout=timeout,
            check=check,
            text=text,
            capture_output=capture_output,
        )

    def _run_subprocess(
        self,
        argv: Sequence[str],
        *,
        env: Mapping[str, str] | None = None,
        stdin: Any = None,
        stdout: Any = None,
        stderr: Any = None,
        timeout: float | None = None,
        check: bool = False,
        text: bool = False,
        capture_output: bool = False,
    ) -> subprocess.CompletedProcess[Any]:
        token = _GATEWAY_TOKEN.set(self.gateway_instance_id)
        try:
            return subprocess.run(
                list(argv),
                env=dict(env) if env is not None else self._default_env,
                stdin=stdin,
                stdout=stdout,
                stderr=stderr,
                timeout=timeout,
                check=check,
                text=text,
                capture_output=capture_output,
                shell=False,
            )
        finally:
            _GATEWAY_TOKEN.reset(token)

    def validate_complete(self, executed_mutations: int | None = None) -> None:
        auth = [item for item in self._ledger if item.record_type == "AUTHORIZATION"]
        results = [item for item in self._ledger if item.record_type == "RESULT"]
        mutation_audit = [item for item in self._invocation_audit if item.is_mutation]
        if executed_mutations is not None and executed_mutations != len(
            [item for item in auth if item.authorization_outcome == "AUTHORIZED"]
        ):
            raise ValueError("mutation count mismatch")
        if len(auth) != len(mutation_audit):
            raise ValueError("mutation audit mismatch")
        if len([item for item in auth if item.authorization_outcome == "AUTHORIZED"]) != len(
            results
        ):
            raise ValueError("mutation ledger incomplete")
        if sorted(item.authorization_sequence for item in auth) != list(range(1, len(auth) + 1)):
            raise ValueError("authorization sequence gap")
        if sorted(
            item.execution_result_sequence
            for item in results
            if item.execution_result_sequence is not None
        ) != list(range(1, len(results) + 1)):
            raise ValueError("result sequence gap")
        if len(self._ledger) != len(auth) + len(results):
            raise ValueError("mutation ledger mismatch")
        if len(self._ledger) % 2 != 0:
            raise ValueError("mutation ledger incomplete")
        audit_by_invocation = {item.invocation_sequence: item for item in mutation_audit}
        seen_results: set[int] = set()
        for index in range(0, len(self._ledger), 2):
            auth_item = self._ledger[index]
            result_item = self._ledger[index + 1]
            if auth_item.record_type != "AUTHORIZATION" or result_item.record_type != "RESULT":
                raise ValueError("invocation bijection mismatch")
            audit_item = audit_by_invocation.get(auth_item.invocation_sequence)
            if audit_item is None:
                raise ValueError("missing mutation audit")
            if audit_item.argv_fingerprint != auth_item.argv_fingerprint:
                raise ValueError("invocation hash mismatch")
            if auth_item.authorization_outcome != "AUTHORIZED":
                raise ValueError("authorization rejected")
            if (
                result_item.authorization_sequence != auth_item.authorization_sequence
                or result_item.invocation_sequence != auth_item.invocation_sequence
                or result_item.stage != auth_item.stage
                or result_item.command_class != auth_item.command_class
                or result_item.target_kind != auth_item.target_kind
                or result_item.target_identity_hash != auth_item.target_identity_hash
            ):
                raise ValueError("invocation bijection mismatch")
            if result_item.execution_result_sequence in seen_results:
                raise ValueError("duplicate result sequence")
            seen_results.add(result_item.execution_result_sequence or 0)
        if len(results) != len(seen_results):
            raise ValueError("result sequence reuse")
        if any(item.execution_attempted is not True for item in results):
            raise ValueError("result missing execution flag")
        if any(
            item.record_type == "RESULT"
            and item.authorization_sequence
            not in {auth_item.authorization_sequence for auth_item in auth}
            for item in results
        ):
            raise ValueError("result without authorization")
        if len(self._invocation_audit) != len(auth) + len(
            [item for item in self._invocation_audit if not item.is_mutation]
        ):
            raise ValueError("invocation audit corrupted")


def gateway_token_active() -> bool:
    return _GATEWAY_TOKEN.get() is not None


def gateway_token() -> str | None:
    return _GATEWAY_TOKEN.get()
