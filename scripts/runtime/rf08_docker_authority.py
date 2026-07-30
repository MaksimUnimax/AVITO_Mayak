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
from typing import Any, Final

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
        if token in {"-f", "--file"}:
            if index + 1 >= len(argv):
                raise ValueError("missing compose file")
            file_values.append(argv[index + 1])
            index += 2
            continue
        if token in {"-p", "--project-name"}:
            if index + 1 >= len(argv):
                raise ValueError("missing compose project")
            project_values.append(argv[index + 1])
            index += 2
            continue
        if token == "--profile":
            if index + 1 >= len(argv):
                raise ValueError("missing compose profile")
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
    if project_values[0] != TASK_PROJECT:
        raise ValueError("compose project mismatch")
    if Path(file_values[0]).name not in {COMPOSE_FILE, "compose.runtime.yaml"}:
        raise ValueError("compose file mismatch")
    if profile_values[0] != RUNTIME_PROFILE:
        raise ValueError("compose profile mismatch")
    if command == "version":
        if remainder != ("--short",):
            raise ValueError("compose version mismatch")
        return DockerInvocationPlan(
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
        return DockerInvocationPlan(
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
        return DockerInvocationPlan(
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
        return DockerInvocationPlan(
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
                if flags != {"--rm", "--no-deps"} and flags != {"--no-deps", "--rm"}:
                    raise ValueError("compose run flags mismatch")
                if "-d" in flags or "--detach" in flags:
                    raise ValueError("compose run flags mismatch")
                if positional[1:] == []:
                    raise ValueError("compose run command missing")
        return DockerInvocationPlan(
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
        return DockerInvocationPlan(
            argv,
            DockerCommandClass.READ_ONLY,
            "daemon",
            _sha256(" ".join(argv)),
            False,
            command=command,
        )
    if command == "inspect":
        return DockerInvocationPlan(
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
        return DockerInvocationPlan(
            argv,
            DockerCommandClass.READ_ONLY,
            "target",
            _sha256(" ".join(argv)),
            False,
            command=command,
        )
    if command == "image" and len(argv) > 2:
        if argv[2] == "inspect":
            return DockerInvocationPlan(
                argv,
                DockerCommandClass.READ_ONLY,
                "image",
                _sha256(" ".join(argv)),
                False,
                command="inspect",
            )
        if argv[2] == "build":
            return DockerInvocationPlan(
                argv,
                DockerCommandClass.IMAGE_BUILD,
                "image",
                _sha256(" ".join(argv)),
                True,
                command="build",
            )
        if argv[2] == "load":
            return DockerInvocationPlan(
                argv,
                DockerCommandClass.IMAGE_LOAD,
                "image",
                _sha256(" ".join(argv)),
                True,
                command="load",
            )
    if command == "buildx" and len(argv) > 2 and argv[2] == "build":
        return DockerInvocationPlan(
            argv,
            DockerCommandClass.BUILDX_BUILD,
            "image",
            _sha256(" ".join(argv)),
            True,
            command="build",
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
        return DockerInvocationPlan(
            argv,
            DockerCommandClass.DIRECT_RUN,
            "container",
            _sha256(" ".join(argv)),
            True,
            command=command,
        )
    if command == "rm":
        return DockerInvocationPlan(
            argv,
            DockerCommandClass.DIRECT_CONTAINER_RM,
            "container",
            _sha256(" ".join(argv)),
            True,
            command=command,
        )
    if command == "network" and len(argv) > 2:
        if argv[2] == "create":
            return DockerInvocationPlan(
                argv,
                DockerCommandClass.NETWORK_CREATE,
                "network",
                _sha256(" ".join(argv)),
                True,
                command="create",
            )
        if argv[2] == "rm":
            return DockerInvocationPlan(
                argv,
                DockerCommandClass.NETWORK_RM,
                "network",
                _sha256(" ".join(argv)),
                True,
                command="rm",
            )
        if argv[2] == "ls":
            return DockerInvocationPlan(
                argv,
                DockerCommandClass.READ_ONLY,
                "network",
                _sha256(" ".join(argv)),
                False,
                command="ls",
            )
    if command == "volume" and len(argv) > 2:
        if argv[2] == "create":
            return DockerInvocationPlan(
                argv,
                DockerCommandClass.VOLUME_CREATE,
                "volume",
                _sha256(" ".join(argv)),
                True,
                command="create",
            )
        if argv[2] == "rm":
            return DockerInvocationPlan(
                argv,
                DockerCommandClass.VOLUME_RM,
                "volume",
                _sha256(" ".join(argv)),
                True,
                command="rm",
            )
        if argv[2] == "ls":
            return DockerInvocationPlan(
                argv,
                DockerCommandClass.READ_ONLY,
                "volume",
                _sha256(" ".join(argv)),
                False,
                command="ls",
            )
    if command == "builder" and len(argv) > 2:
        if argv[2] == "create":
            return DockerInvocationPlan(
                argv,
                DockerCommandClass.TASK_SCOPED_BUILDER_CREATE,
                "builder",
                _sha256(" ".join(argv)),
                True,
                command="create",
            )
        if argv[2] == "rm":
            return DockerInvocationPlan(
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
        return DockerInvocationPlan(
            argv,
            DockerCommandClass.READ_ONLY,
            "daemon",
            _sha256(" ".join(argv)),
            False,
            command=command,
        )
    if command in {"network", "volume", "image"}:
        return DockerInvocationPlan(
            argv,
            DockerCommandClass.UNKNOWN_DOCKER_COMMAND,
            "unknown",
            _sha256(" ".join(argv)),
            False,
            command=command,
        )
    return DockerInvocationPlan(
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


def _target_ownership(plan: DockerInvocationPlan) -> str:
    if plan.argv and any(token == "apm-postgres" for token in plan.argv):
        return "FOREIGN"
    if plan.command == "run" and plan.command_class == DockerCommandClass.DIRECT_RUN:
        return "TASK_OWNED"
    if plan.command == "create" and plan.command_class in {
        DockerCommandClass.COMPOSE_CREATE,
        DockerCommandClass.COMPOSE_UP,
        DockerCommandClass.COMPOSE_START,
        DockerCommandClass.COMPOSE_STOP,
        DockerCommandClass.COMPOSE_RESTART,
        DockerCommandClass.COMPOSE_RUN,
        DockerCommandClass.COMPOSE_RM,
        DockerCommandClass.COMPOSE_DOWN,
    }:
        return "TASK_OWNED"
    if plan.command_class in {
        DockerCommandClass.NETWORK_CREATE,
        DockerCommandClass.NETWORK_RM,
        DockerCommandClass.VOLUME_CREATE,
        DockerCommandClass.VOLUME_RM,
        DockerCommandClass.IMAGE_BUILD,
        DockerCommandClass.IMAGE_LOAD,
        DockerCommandClass.BUILDX_BUILD,
    }:
        return "TASK_OWNED"
    if plan.command_class == DockerCommandClass.UNKNOWN_DOCKER_COMMAND:
        return "UNRESOLVED"
    return "TASK_OWNED" if plan.is_mutation else "FOREIGN"


@dataclass
class MutationAuthority:
    task_project: str = TASK_PROJECT
    technical_id: str = TECHNICAL_ID
    compose_file: str = COMPOSE_FILE
    profile: str = RUNTIME_PROFILE
    allowed_services: tuple[str, ...] = tuple(sorted(ALLOWED_SERVICES))
    gateway_instance_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    invocation_audit: list[DockerInvocationAuditRecord] = field(default_factory=list)
    ledger: list[DockerMutationRecord] = field(default_factory=list)
    _invocation_sequence: int = 0
    _authorization_sequence: int = 0
    _result_sequence: int = 0

    @property
    def entries(self) -> tuple[DockerMutationRecord, ...]:
        return tuple(self.ledger)

    def authorize(
        self, argv: tuple[str, ...], *, stage: str, target_kind: str | None = None
    ) -> DockerMutationRecord:
        plan = _direct_plan(argv)
        if not plan.is_mutation:
            raise ValueError("read-only command is not a mutation")
        if target_kind is not None:
            plan = DockerInvocationPlan(
                argv=plan.argv,
                command_class=plan.command_class,
                target_kind=target_kind,
                target_identity_hash=plan.target_identity_hash,
                is_mutation=plan.is_mutation,
                compose_file=plan.compose_file,
                project_name=plan.project_name,
                profile=plan.profile,
                command=plan.command,
                service=plan.service,
                exact_options=plan.exact_options,
            )
        ownership = _target_ownership(plan)
        if ownership != "TASK_OWNED":
            raise PermissionError("foreign or unresolved target")
        return DockerMutationRecord(
            record_type="AUTHORIZATION",
            authorization_sequence=0,
            execution_result_sequence=None,
            invocation_sequence=0,
            stage=stage,
            command_class=plan.command_class.value,
            target_kind=plan.target_kind,
            target_identity_hash=plan.target_identity_hash,
            authorization_basis="TASK_CREATION_PLAN",
            authorization_outcome="AUTHORIZED",
            target_ownership=ownership,
            argv_fingerprint=_fingerprint(argv),
        )

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
        self.invocation_audit.append(record)
        return record

    def _authorize(
        self, plan: DockerInvocationPlan, *, stage: str, audit: DockerInvocationAuditRecord
    ) -> DockerMutationRecord | None:
        if not plan.is_mutation:
            return None
        ownership = _target_ownership(plan)
        if ownership != "TASK_OWNED":
            raise PermissionError("foreign or unresolved target")
        self._authorization_sequence += 1
        record = DockerMutationRecord(
            record_type="AUTHORIZATION",
            authorization_sequence=self._authorization_sequence,
            execution_result_sequence=None,
            invocation_sequence=audit.invocation_sequence,
            stage=stage,
            command_class=plan.command_class.value,
            target_kind=plan.target_kind,
            target_identity_hash=plan.target_identity_hash,
            authorization_basis="TASK_CREATION_PLAN"
            if plan.command_class
            in {
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
            }
            else "READ_ONLY_INSPECT",
            authorization_outcome="AUTHORIZED",
            target_ownership=ownership,
            argv_fingerprint=audit.argv_fingerprint,
        )
        self.ledger.append(record)
        return record

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
        self.ledger.append(record)
        return record

    def append_result(
        self,
        authorization: DockerMutationRecord,
        *,
        exit_code: int | None,
        completed: bool,
        timed_out: bool,
    ) -> DockerMutationRecord:
        return self._record_result(
            authorization,
            exit_code=exit_code,
            completed=completed,
            timed_out=timed_out,
            failure_classification=None,
        )

    def execute(
        self,
        argv: tuple[str, ...],
        *,
        stage: str,
        runner: Any,
        target_kind: str | None = None,
    ) -> tuple[int, bool, bool]:
        plan = _direct_plan(argv)
        if target_kind is not None:
            plan = DockerInvocationPlan(
                argv=plan.argv,
                command_class=plan.command_class,
                target_kind=target_kind,
                target_identity_hash=plan.target_identity_hash,
                is_mutation=plan.is_mutation,
                compose_file=plan.compose_file,
                project_name=plan.project_name,
                profile=plan.profile,
                command=plan.command,
                service=plan.service,
                exact_options=plan.exact_options,
            )
        audit = self._record_audit(plan, stage=stage)
        authorization = self._authorize(plan, stage=stage, audit=audit)
        if authorization is None:
            result = runner(argv)
            code, completed, timed_out = result
            return code, completed, timed_out
        try:
            code, completed, timed_out = runner(argv)
        except TimeoutError:
            self._record_result(
                authorization,
                exit_code=None,
                completed=False,
                timed_out=True,
                failure_classification="TimeoutError",
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
        else:
            self._record_result(
                authorization,
                exit_code=code,
                completed=completed,
                timed_out=timed_out,
                failure_classification=None,
            )
            return code, completed, timed_out

    def run(
        self,
        argv: Sequence[str],
        *,
        stage: str,
        stdin: Any = None,
        stdout: Any = None,
        stderr: Any = None,
        env: Mapping[str, str] | None = None,
        cwd: str | Path | None = None,
        timeout: float | None = None,
        check: bool = False,
        text: bool = False,
        capture_output: bool = False,
    ) -> subprocess.CompletedProcess[Any]:
        plan = _direct_plan(tuple(argv))
        audit = self._record_audit(plan, stage=stage)
        if not plan.is_mutation:
            return self._run_subprocess(
                plan.argv,
                stdin=stdin,
                stdout=stdout,
                stderr=stderr,
                env=env,
                cwd=cwd,
                timeout=timeout,
                check=check,
                text=text,
                capture_output=capture_output,
            )
        authorization = self._authorize(plan, stage=stage, audit=audit)
        if authorization is None:
            raise PermissionError("mutation authorization missing")
        try:
            completed = self._run_subprocess(
                plan.argv,
                stdin=stdin,
                stdout=stdout,
                stderr=stderr,
                env=env,
                cwd=cwd,
                timeout=timeout,
                check=check,
                text=text,
                capture_output=capture_output,
            )
        except subprocess.CalledProcessError as exc:
            self._record_result(
                authorization,
                exit_code=exc.returncode,
                completed=True,
                timed_out=False,
                failure_classification=type(exc).__name__,
            )
            raise
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
        else:
            self._record_result(
                authorization,
                exit_code=completed.returncode,
                completed=True,
                timed_out=False,
                failure_classification=None,
            )
            return completed

    def _run_subprocess(
        self,
        argv: Sequence[str],
        *,
        stdin: Any = None,
        stdout: Any = None,
        stderr: Any = None,
        env: Mapping[str, str] | None = None,
        cwd: str | Path | None = None,
        timeout: float | None = None,
        check: bool = False,
        text: bool = False,
        capture_output: bool = False,
    ) -> subprocess.CompletedProcess[Any]:
        token = _GATEWAY_TOKEN.set(self.gateway_instance_id)
        try:
            return subprocess.run(
                list(argv),
                stdin=stdin,
                stdout=stdout,
                stderr=stderr,
                env=dict(env) if env is not None else None,
                cwd=str(cwd) if cwd is not None else None,
                timeout=timeout,
                check=check,
                text=text,
                capture_output=capture_output,
            )
        finally:
            _GATEWAY_TOKEN.reset(token)

    def validate_complete(self, executed_mutations: int | None = None) -> None:
        auth = [item for item in self.ledger if item.record_type == "AUTHORIZATION"]
        results = [item for item in self.ledger if item.record_type == "RESULT"]
        if not self.ledger and executed_mutations:
            raise ValueError("empty mutation ledger")
        if executed_mutations is not None and executed_mutations != len(auth):
            raise ValueError("mutation count mismatch")
        if self.ledger and not auth:
            raise ValueError("missing authorization records")
        if len(auth) != len(results):
            raise ValueError("mutation ledger incomplete")
        mutation_audit = [item for item in self.invocation_audit if item.is_mutation]
        if len(mutation_audit) != len(auth):
            raise ValueError("mutation audit mismatch")
        if any(
            auth_item.argv_fingerprint != audit_item.argv_fingerprint
            or result_item.argv_fingerprint != audit_item.argv_fingerprint
            for auth_item, result_item, audit_item in zip(auth, results, mutation_audit)
        ):
            raise ValueError("invocation hash mismatch")
        if len(self.invocation_audit) != len(
            [item for item in self.invocation_audit if item.is_mutation]
        ) + len([item for item in self.invocation_audit if not item.is_mutation]):
            raise ValueError("invocation audit corrupted")
        if sorted(item.authorization_sequence for item in auth) != list(range(1, len(auth) + 1)):
            raise ValueError("authorization sequence gap")
        if sorted(
            item.execution_result_sequence
            for item in results
            if item.execution_result_sequence is not None
        ) != list(range(1, len(results) + 1)):
            raise ValueError("result sequence gap")
        if any(
            self.ledger[index].record_type != "AUTHORIZATION"
            or self.ledger[index + 1].record_type != "RESULT"
            or self.ledger[index].authorization_sequence
            != self.ledger[index + 1].authorization_sequence
            or self.ledger[index].invocation_sequence != self.ledger[index + 1].invocation_sequence
            or self.ledger[index].stage != self.ledger[index + 1].stage
            or self.ledger[index].command_class != self.ledger[index + 1].command_class
            or self.ledger[index].target_kind != self.ledger[index + 1].target_kind
            or self.ledger[index].target_identity_hash
            != self.ledger[index + 1].target_identity_hash
            for index in range(0, len(self.ledger), 2)
        ):
            raise ValueError("invocation bijection mismatch")
        if any(item.authorization_outcome != "AUTHORIZED" for item in auth):
            raise ValueError("authorization rejected")
        if any(item.execution_attempted is not True for item in results):
            raise ValueError("result missing execution flag")
        if any(
            item.record_type == "RESULT"
            and item.authorization_sequence
            not in {auth_item.authorization_sequence for auth_item in auth}
            for item in results
        ):
            raise ValueError("result without authorization")


def gateway_token_active() -> bool:
    return _GATEWAY_TOKEN.get() is not None


def gateway_token() -> str | None:
    return _GATEWAY_TOKEN.get()
