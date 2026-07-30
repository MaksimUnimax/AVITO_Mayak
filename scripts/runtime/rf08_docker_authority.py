"""Single fail-closed boundary for RF-08 Docker mutations."""
# ruff: noqa: E501

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Callable, Iterable

TASK_PROJECT = "avito-mayak-rf08-secret-delivery"
TECHNICAL_ID = "RF-08-CORRECTIVE-NONROOT-FILE-SECRET-DELIVERY-20260729-01"
COMPOSE_FILES = ("compose.yaml",)
PROFILE = "runtime-foundation"


class DockerCommandClass(StrEnum):
    READ_ONLY = "READ_ONLY"
    MUTATION_TASK_PROJECT_CREATE = "MUTATION_TASK_PROJECT_CREATE"
    MUTATION_TASK_PROJECT_START = "MUTATION_TASK_PROJECT_START"
    MUTATION_TASK_PROJECT_STOP = "MUTATION_TASK_PROJECT_STOP"
    MUTATION_TASK_PROJECT_RECREATE = "MUTATION_TASK_PROJECT_RECREATE"
    MUTATION_TASK_PROJECT_RUN_ONESHOT = "MUTATION_TASK_PROJECT_RUN_ONESHOT"
    MUTATION_TASK_PROJECT_REMOVE = "MUTATION_TASK_PROJECT_REMOVE"
    MUTATION_TASK_PROJECT_DOWN = "MUTATION_TASK_PROJECT_DOWN"
    MUTATION_TASK_VOLUME_REMOVE = "MUTATION_TASK_VOLUME_REMOVE"
    MUTATION_IMAGE_BUILD_OR_LOAD = "MUTATION_IMAGE_BUILD_OR_LOAD"
    FORBIDDEN_UNSCOPED_MUTATION = "FORBIDDEN_UNSCOPED_MUTATION"
    FORBIDDEN_BROAD_MUTATION = "FORBIDDEN_BROAD_MUTATION"
    UNKNOWN_DOCKER_COMMAND = "UNKNOWN_DOCKER_COMMAND"


READ_ONLY = {"version", "info", "inspect", "ps", "images", "network", "volume", "compose"}
MUTATING = {"up", "start", "stop", "restart", "rm", "run", "create", "down", "build", "pull", "push"}


@dataclass(frozen=True)
class DockerMutationRecord:
    authorization_sequence: int
    execution_result_sequence: int | None
    stage: str
    operation_class: str
    docker_command_class: str
    task_project: str
    target_kind: str
    target_identity_hash: str
    planned_ownership: str
    authorization_result: str
    execution_attempted: bool = False
    execution_completed: bool = False
    exit_code: int | None = None
    timed_out: bool = False

    # Compatibility fields retained as read-only derived aliases for old evidence callers.
    @property
    def sequence(self) -> int:
        return self.authorization_sequence

    @property
    def ownership(self) -> str:
        return self.planned_ownership

    @property
    def mutation_allowed(self) -> bool:
        return self.authorization_result == "AUTHORIZED"

    @property
    def scoped(self) -> bool:
        return self.task_project == TASK_PROJECT

    @property
    def executed(self) -> bool:
        return self.execution_attempted

    def safe_dict(self) -> dict[str, object]:
        return asdict(self)


def _hash_target(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def classify_docker_argv(argv: Iterable[str]) -> DockerCommandClass:
    args = tuple(argv)
    if not args or args[0] != "docker":
        return DockerCommandClass.UNKNOWN_DOCKER_COMMAND
    if len(args) < 2:
        return DockerCommandClass.UNKNOWN_DOCKER_COMMAND
    if args[1] == "system" and len(args) > 2 and args[2] == "prune":
        return DockerCommandClass.FORBIDDEN_BROAD_MUTATION
    if args[1] in {"rm", "network", "volume"}:
        if args[1] in {"network", "volume"} and len(args) > 2 and args[2] in {"rm", "prune"}:
            return (DockerCommandClass.MUTATION_TASK_VOLUME_REMOVE
                    if args[1] == "volume" and args[2] == "rm"
                    else DockerCommandClass.FORBIDDEN_BROAD_MUTATION)
        if args[1] == "rm":
            return DockerCommandClass.MUTATION_TASK_PROJECT_REMOVE
    if args[1] == "image" and len(args) > 2 and args[2] in {"build", "load"}:
        return DockerCommandClass.MUTATION_IMAGE_BUILD_OR_LOAD
    if args[1] == "image" and len(args) > 2 and args[2] == "inspect":
        return DockerCommandClass.READ_ONLY
    if args[1] == "run":
        return DockerCommandClass.MUTATION_TASK_PROJECT_RUN_ONESHOT
    if args[1] != "compose":
        return DockerCommandClass.READ_ONLY if args[1] in READ_ONLY else DockerCommandClass.UNKNOWN_DOCKER_COMMAND
    # Parse option/value pairs structurally; compose.yaml and project names are
    # operands, never commands.
    command = ""
    index = 2
    value_options = {"-f", "--file", "-p", "--project-name", "--profile", "-e", "--env", "-v", "--volume", "--user", "--entrypoint", "--format"}
    while index < len(args):
        item = args[index]
        if item in value_options:
            index += 2
            continue
        if item.startswith("-"):
            index += 1
            continue
        command = item
        break
    if command in {"config", "version", "ps", "ls", "exec"}:
        return DockerCommandClass.READ_ONLY
    return {
        "create": DockerCommandClass.MUTATION_TASK_PROJECT_CREATE,
        "up": DockerCommandClass.MUTATION_TASK_PROJECT_START,
        "start": DockerCommandClass.MUTATION_TASK_PROJECT_START,
        "stop": DockerCommandClass.MUTATION_TASK_PROJECT_STOP,
        "restart": DockerCommandClass.MUTATION_TASK_PROJECT_RECREATE,
        "run": DockerCommandClass.MUTATION_TASK_PROJECT_RUN_ONESHOT,
        "rm": DockerCommandClass.MUTATION_TASK_PROJECT_REMOVE,
        "down": DockerCommandClass.MUTATION_TASK_PROJECT_DOWN,
    }.get(command, DockerCommandClass.UNKNOWN_DOCKER_COMMAND)


class MutationAuthority:
    def __init__(self, *, task_project: str = TASK_PROJECT, technical_id: str = TECHNICAL_ID) -> None:
        self.task_project, self.technical_id = task_project, technical_id
        self.ledger: list[DockerMutationRecord] = []
        self._next = 1

    def authorize(self, argv: tuple[str, ...], *, stage: str, target_kind: str = "task_project", ownership: str = "TASK_OWNED") -> DockerMutationRecord:
        command_class = classify_docker_argv(argv)
        if command_class in {DockerCommandClass.READ_ONLY}:
            raise ValueError("read-only command is not a mutation")
        if command_class in {DockerCommandClass.UNKNOWN_DOCKER_COMMAND, DockerCommandClass.FORBIDDEN_BROAD_MUTATION, DockerCommandClass.FORBIDDEN_UNSCOPED_MUTATION}:
            raise PermissionError(command_class.value)
        if ownership != "TASK_OWNED":
            raise PermissionError("foreign or unresolved target")
        if argv[1] == "compose" and ("-p" not in argv or self.task_project not in argv):
            raise PermissionError("compose project not exact")
        if argv[1] != "compose" and not any(self.task_project in item for item in argv):
            raise PermissionError("direct task command not exact")
        if "--profile" in argv and PROFILE not in argv:
            raise PermissionError("compose profile not exact")
        record = DockerMutationRecord(self._next, None, stage, command_class.value, command_class.value,
                                      self.task_project, target_kind, _hash_target(" ".join(argv)), ownership,
                                      "AUTHORIZED")
        self._next += 1
        self.ledger.append(record)
        return record

    def execute(self, argv: tuple[str, ...], *, stage: str, runner: Callable[[tuple[str, ...]], tuple[int, bool, bool]], target_kind: str = "task_project", ownership: str = "TASK_OWNED") -> tuple[int, bool, bool]:
        authorization = self.authorize(argv, stage=stage, target_kind=target_kind, ownership=ownership)
        try:
            result = runner(argv)
        except TimeoutError:
            code, completed, timed_out = None, False, True
        else:
            code, completed, timed_out = result
        index = len(self.ledger) + 1
        self.ledger.append(DockerMutationRecord(authorization.authorization_sequence, index, stage,
            authorization.operation_class, authorization.docker_command_class, self.task_project,
            target_kind, authorization.target_identity_hash, ownership, "AUTHORIZED", True, completed, code, timed_out))
        return code or 0, completed, timed_out

    def validate_complete(self, executed_mutations: int) -> None:
        auth = [x for x in self.ledger if x.execution_result_sequence is None]
        results = [x for x in self.ledger if x.execution_result_sequence is not None]
        if executed_mutations and not self.ledger:
            raise ValueError("empty mutation ledger")
        if len(auth) != len(results) or any(r.authorization_sequence != a.authorization_sequence for a, r in zip(auth, results)):
            raise ValueError("mutation ledger incomplete or reordered")
        if len({r.execution_result_sequence for r in results}) != len(results):
            raise ValueError("duplicate mutation result")
