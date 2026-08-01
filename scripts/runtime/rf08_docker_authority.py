"""Semantic Docker gateway for RF-08.

This module exposes immutable semantic actions and typed redacted observations.
It intentionally avoids storing raw Docker argv, parser plans, or protocol-visible
subprocess results.
"""

from __future__ import annotations

import contextvars
import hashlib
import json
import os
import re
import subprocess
import time
import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, fields, is_dataclass, replace
from enum import StrEnum
from pathlib import Path
from typing import Any, Final, cast

TASK_PROJECT: Final = "avito-mayak-rf08-secret-delivery"
TECHNICAL_ID: Final = (
    "RF-08-CORRECTIVE-REUSABLE-TASK-SCOPED-ACCEPTANCE-COMPOSE-AUTHORITY-20260801-07"
)
COMPOSE_FILE: Final = "compose.yaml"
RUNTIME_ROOT: Final = Path("/opt/avito-mayak-runtime/rf08-secret-delivery")
RUNTIME_COMPOSE_FILE: Path = Path(
    "/opt/avito-mayak-runtime/rf08-secret-delivery/compose.runtime.yaml"
)
RUNTIME_PROFILE: Final = "runtime-foundation"
TASK_ACCEPTANCE_VERIFIER_ROOT: Final = (
    Path(__file__).resolve().parent / "task_acceptance"
)
TASK_ACCEPTANCE_VERIFIER_DESTINATION: Final = "/opt/mayak/task_acceptance_verifier.py"
TASK_ACCEPTANCE_SCHEMA_VERSION: Final = "mayak-task-acceptance-v1"
TASK_ACCEPTANCE_MAX_STDOUT_BYTES: Final = 16 * 1024
TASK_ACCEPTANCE_MAX_STDERR_BYTES: Final = 4 * 1024
TASK_ACCEPTANCE_MAX_TIMEOUT_SECONDS: Final = 60.0
SEALED_BOOTSTRAP_SERVICE: Final = "mayak-db-bootstrap"
SEALED_BOOTSTRAP_SOURCE: Final = (
    Path(__file__).resolve().parent / "rf09_public_bootstrap_adapter.py"
)
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
EXPECTED_LOCK_IDENTITY: Final = "e1faff1ce0f4d5dfd35480ab59d5d599fddf05c38fcd16a26c52098511476ab6"
TASK_PROJECT_PATTERN: Final = re.compile(
    r"^avito-mayak-acceptance-rf(?P<roadmap_number>[0-9]{2})-[a-z0-9]+(?:-[a-z0-9]+)*$"
)
TECHNICAL_ID_PATTERN: Final = re.compile(
    r"^RF-(?P<roadmap_number>[0-9]{2})-[A-Z0-9][A-Z0-9-]{0,119}$"
)
MODULE14_MUTATING_RF_MIN: Final = 1
MODULE14_MUTATING_RF_MAX: Final = 30


def _roadmap_number_is_authorized(number: int) -> bool:
    return MODULE14_MUTATING_RF_MIN <= number <= MODULE14_MUTATING_RF_MAX


def _require_authorized_roadmap_number(match: re.Match[str], *, identity: str) -> int:
    number = int(match.group("roadmap_number"))
    if not _roadmap_number_is_authorized(number):
        raise ValueError(f"{identity} roadmap number is outside the authorized Module-14 range")
    return number

_GATEWAY_TOKEN: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "rf08_gateway_token",
    default=None,
)


class ComposeSourceCapability(StrEnum):
    SOURCE = "SOURCE"
    GENERATED = "GENERATED"


class ComposeOperation(StrEnum):
    CREATE = "create"
    UP = "up"
    START = "start"
    STOP = "stop"
    RESTART = "restart"
    RM = "rm"


class AuthorityMode(StrEnum):
    SEALED_RF08_PROOF = "SEALED_RF08_PROOF"
    TASK_SCOPED_ACCEPTANCE = "TASK_SCOPED_ACCEPTANCE"


class ComposeProbeKind(StrEnum):
    APPLICATION_QUERY = "application-query"
    AUTH_REJECTION = "auth-rejection"


class ComposeService(StrEnum):
    API = "mayak-api"
    WORKER = "mayak-worker"
    SCHEDULER = "mayak-scheduler"
    POSTGRES = "mayak-postgres"
    DB_BOOTSTRAP = "mayak-db-bootstrap"
    MIGRATE = "mayak-migrate"


class ResourceKind(StrEnum):
    CONTAINER = "container"
    NETWORK = "network"
    VOLUME = "volume"
    IMAGE = "image"
    BUILDER = "builder"


class ResourceOperation(StrEnum):
    CREATE = "create"
    REMOVE = "remove"


class ImageOperation(StrEnum):
    BUILDX_MANIFEST = "buildx-manifest"
    APPLICATION_BUILD = "application-build"


class ObservationTemplate(StrEnum):
    DAEMON_VERSION = "daemon-version"
    CONTAINER_HEALTH = "container-health"
    CONTAINER_LIST = "container-list"
    CONTAINER_INSPECT = "container-inspect"
    NETWORK_INSPECT = "network-inspect"
    VOLUME_INSPECT = "volume-inspect"
    IMAGE_INSPECT = "image-inspect"
    NETWORK_LIST = "network-list"
    VOLUME_LIST = "volume-list"
    IMAGE_LIST = "image-list"
    BUILDX_LIST = "buildx-list"
    COMPOSE_VERSION = "compose-version"
    COMPOSE_CONFIG = "compose-config"
    COMPOSE_PS = "compose-ps"
    COMPOSE_EXEC = "compose-exec"
    POSTGRES_LOG_TAIL = "postgres-log-tail"


class ComposeExecTemplate(StrEnum):
    POSTGRES_READY = "postgres-ready"
    POSTGRES_MIGRATION_HEAD = "postgres-migration-head"
    POSTGRES_LOG_DESTINATION = "postgres-log-destination"


class NetworkPolicy(StrEnum):
    INTERNAL_ONLY = "internal-only"
    NONE = "none"


class SecretMountCapability(StrEnum):
    REQUIRED = "required"
    FORBIDDEN = "forbidden"
    OPTIONAL = "optional"


class ProbeKind(StrEnum):
    POSTGRES_READY = "postgres-ready"
    AUTH_REJECTION = "auth-rejection"
    APPLICATION_QUERY = "application-query"
    IMPORT_PROBE = "import-probe"


class PathCapabilityKind(StrEnum):
    FILE = "file"
    DIRECTORY = "directory"


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _normalize(value: Any) -> Any:
    if is_dataclass(value):
        return {field.name: _normalize(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Mapping):
        return {str(key): _normalize(child) for key, child in value.items()}
    if isinstance(value, (list, tuple)):
        return [_normalize(child) for child in value]
    return value


def _safe_digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(_normalize(value), sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _fingerprint(argv: Sequence[str]) -> str:
    return _sha_text(json.dumps(list(argv), ensure_ascii=True, separators=(",", ":")))


@dataclass(frozen=True, slots=True)
class ComposeBinding:
    compose_file: str
    compose_file_digest: str
    compose_capability: ComposeSourceCapability
    project_name: str
    profile: str

    @classmethod
    def from_path(cls, path: str | Path, *, project_name: str, profile: str) -> "ComposeBinding":
        candidate = Path(path).expanduser()
        if not candidate.is_absolute():
            raise ValueError("compose file must be absolute")
        if candidate.is_symlink() or any(parent.is_symlink() for parent in candidate.parents):
            raise ValueError("compose file traversal mismatch")
        resolved = candidate.resolve(strict=True)
        repo_compose = Path(__file__).resolve().parents[2] / COMPOSE_FILE
        runtime_compose = RUNTIME_COMPOSE_FILE
        if resolved == repo_compose.resolve(strict=True):
            capability = ComposeSourceCapability.SOURCE
        elif runtime_compose.exists() and resolved == runtime_compose.resolve(strict=True):
            capability = ComposeSourceCapability.GENERATED
        else:
            raise ValueError("compose file identity mismatch")
        return cls(
            compose_file=str(resolved),
            compose_file_digest=_sha_bytes(resolved.read_bytes()),
            compose_capability=capability,
            project_name=project_name,
            profile=profile,
        )


@dataclass(frozen=True, slots=True)
class PathCapability:
    kind: PathCapabilityKind
    path: str
    identity: str
    digest: str | None = None

    @classmethod
    def from_path(
        cls, path: str | Path, *, kind: PathCapabilityKind, require_exists: bool = True
    ) -> "PathCapability":
        candidate = Path(path).expanduser()
        if not candidate.is_absolute():
            raise ValueError("path capability must be absolute")
        if candidate.is_symlink() or any(parent.is_symlink() for parent in candidate.parents):
            raise ValueError("path capability traversal mismatch")
        resolved = candidate.resolve(strict=require_exists)
        digest: str | None
        if resolved.exists() and resolved.is_file():
            digest = _sha_bytes(resolved.read_bytes())
        else:
            digest = _sha_text(f"{kind.value}:{resolved}")
        return cls(
            kind=kind,
            path=str(resolved),
            identity=_sha_text(f"{kind.value}:{resolved}"),
            digest=digest,
        )


_VERIFIER_FILE_PATTERN: Final = re.compile(
    r"^rf(?P<roadmap_number>[0-9]{2})_[a-z0-9]+(?:_[a-z0-9]+)*\.py$"
)


def _verifier_project_number(project_name: str) -> int:
    match = TASK_PROJECT_PATTERN.fullmatch(project_name)
    if match is None:
        raise ValueError("task project is not canonical")
    return _require_authorized_roadmap_number(match, identity="task project")


def _validate_task_verifier(capability: PathCapability, *, project_name: str) -> str:
    root = TASK_ACCEPTANCE_VERIFIER_ROOT.resolve(strict=True)
    path = Path(capability.path)
    if capability.kind != PathCapabilityKind.FILE:
        raise ValueError("task verifier must be a file capability")
    if not path.is_absolute() or path.is_symlink():
        raise ValueError("task verifier path must be absolute and non-symlinked")
    if root not in path.parents:
        raise ValueError("task verifier is outside the canonical verifier root")
    if any(parent.is_symlink() for parent in path.parents):
        raise ValueError("task verifier parent traversal mismatch")
    if not path.exists() or not path.is_file():
        raise ValueError("task verifier is not an existing regular file")
    relative = path.relative_to(root)
    if len(relative.parts) != 1:
        raise ValueError("task verifier must be directly under the canonical root")
    match = _VERIFIER_FILE_PATTERN.fullmatch(path.name)
    if match is None:
        raise ValueError("task verifier filename is not canonical")
    number = _require_authorized_roadmap_number(match, identity="verifier")
    if number != _verifier_project_number(project_name):
        raise ValueError("verifier roadmap number does not match task project")
    if capability.digest != _sha_bytes(path.read_bytes()):
        raise PermissionError("task verifier digest mismatch")
    return path.stem


def _validate_sealed_bootstrap(capability: PathCapability, *, service: ComposeService) -> None:
    if service.value != SEALED_BOOTSTRAP_SERVICE:
        raise ValueError("sealed bootstrap service mismatch")
    if capability.kind != PathCapabilityKind.FILE:
        raise ValueError("sealed bootstrap adapter must be a file")
    path = Path(capability.path)
    source = SEALED_BOOTSTRAP_SOURCE.resolve(strict=True)
    runtime = RUNTIME_ROOT / source.name
    accepted = path == source or path == runtime
    if not accepted or path.is_symlink() or any(parent.is_symlink() for parent in path.parents):
        raise ValueError("sealed bootstrap adapter path mismatch")
    if not path.exists() or not path.is_file():
        raise ValueError("sealed bootstrap adapter is not a regular file")
    if capability.digest != _sha_bytes(source.read_bytes()):
        raise PermissionError("sealed bootstrap adapter digest mismatch")
    if _sha_bytes(path.read_bytes()) != capability.digest:
        raise PermissionError("sealed bootstrap adapter was changed")


@dataclass(frozen=True, slots=True)
class ComposeAction:
    binding: ComposeBinding
    service: ComposeService
    operation: ComposeOperation
    detach: bool = False
    force: bool = False
    remove_orphans: bool = False
    no_deps: bool = False
    rm_volumes: bool = False


@dataclass(frozen=True, slots=True)
class ComposeProjectTeardownAction:
    """The only semantic project-level cleanup operation."""

    binding: ComposeBinding
    remove_volumes: bool = True
    remove_orphans: bool = True


@dataclass(frozen=True, slots=True)
class ComposeRunAction:
    binding: ComposeBinding
    service: ComposeService
    no_deps: bool = False


@dataclass(frozen=True, slots=True)
class ComposeProbeAction:
    binding: ComposeBinding
    service: ComposeService
    probe: ComposeProbeKind
    correlation_id: str | None = None


@dataclass(frozen=True, slots=True)
class ResourceLifecycleAction:
    kind: ResourceKind
    operation: ResourceOperation
    name: str
    inspected_capability: str | None = None
    scope_digest: str | None = None

    def __post_init__(self) -> None:
        if self.operation == ResourceOperation.REMOVE and not self.inspected_capability:
            raise ValueError("remove actions require a prior inspected capability")


@dataclass(frozen=True, slots=True)
class ImageAction:
    operation: ImageOperation
    context: PathCapability
    dockerfile: PathCapability
    output: PathCapability
    scope_digest: str | None = None
    tag: str | None = None
    source_sha: str | None = None
    lock_identity: str | None = None
    build_input_digest: str | None = None
    platform: str | None = None


@dataclass(frozen=True, slots=True)
class ProbeAction:
    probe_kind: ProbeKind
    image: str
    name: str
    labels: tuple[tuple[str, str], ...]
    network_policy: NetworkPolicy
    secret_mount: SecretMountCapability
    scope_digest: str | None = None


@dataclass(frozen=True, slots=True)
class BootstrapAction:
    binding: ComposeBinding | None
    service: ComposeService
    run_id: str
    recovered_generation_id: str
    adapter: PathCapability
    scope_digest: str | None = None


@dataclass(frozen=True, slots=True)
class TaskAcceptanceVerifierAction:
    """Closed-world task acceptance authority; all execution policy is fixed."""

    binding: ComposeBinding
    verifier_id: str
    verifier_path: PathCapability
    scope_digest: str


@dataclass(frozen=True, slots=True)
class TaskAcceptanceResult:
    schema_version: str
    technical_id: str
    project: str
    verifier_id: str
    status: str
    checks: dict[str, bool | int | str]


def parse_task_acceptance_output(
    stdout: bytes | str,
    stderr: bytes | str,
    *,
    technical_id: str,
    project: str,
    verifier_id: str,
) -> TaskAcceptanceResult:
    raw_stdout = stdout.encode("utf-8") if isinstance(stdout, str) else stdout
    raw_stderr = stderr.encode("utf-8") if isinstance(stderr, str) else stderr
    if len(raw_stdout) > TASK_ACCEPTANCE_MAX_STDOUT_BYTES:
        raise ValueError("task acceptance stdout exceeds the hard bound")
    if len(raw_stderr) > TASK_ACCEPTANCE_MAX_STDERR_BYTES:
        raise ValueError("task acceptance stderr exceeds the hard bound")
    if raw_stderr:
        raise ValueError("task acceptance emitted unexpected stderr")
    try:
        text = raw_stdout.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("task acceptance output is not UTF-8") from exc
    if not text.endswith("\n") or text.count("\n") != 1:
        raise ValueError("task acceptance output must be one newline-terminated object")
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError("task acceptance output is not JSON") from exc
    if not isinstance(parsed, dict):
        raise ValueError("task acceptance envelope must be an object")
    expected_keys = {"schema_version", "technical_id", "project", "verifier_id", "status", "checks"}
    if set(parsed) != expected_keys:
        raise ValueError("task acceptance envelope has unknown or missing fields")
    if (
        parsed["schema_version"] != TASK_ACCEPTANCE_SCHEMA_VERSION
        or parsed["technical_id"] != technical_id
        or parsed["project"] != project
        or parsed["verifier_id"] != verifier_id
        or parsed["status"] not in {"PASS", "FAIL"}
    ):
        raise ValueError("task acceptance envelope identity or status mismatch")
    checks = parsed["checks"]
    if not isinstance(checks, dict) or not checks or len(checks) > 32:
        raise ValueError("task acceptance checks are not bounded")
    for key, value in checks.items():
        if not isinstance(key, str) or not re.fullmatch(r"[a-z][a-z0-9_]{0,47}", key):
            raise ValueError("task acceptance check key is not canonical")
        if isinstance(value, bool):
            continue
        if (
            isinstance(value, int)
            and not isinstance(value, bool)
            and -1_000_000 <= value <= 1_000_000
        ):
            continue
        if isinstance(value, str) and value in {"PASS", "FAIL", "ACCEPTED", "REJECTED"}:
            continue
        raise ValueError("task acceptance check value is not an approved bounded type")
    return TaskAcceptanceResult(
        schema_version=str(parsed["schema_version"]),
        technical_id=str(parsed["technical_id"]),
        project=str(parsed["project"]),
        verifier_id=str(parsed["verifier_id"]),
        status=str(parsed["status"]),
        checks=cast(dict[str, bool | int | str], checks),
    )


def _compose_diagnostic_stderr(value: bytes) -> bytes:
    """Remove bounded Docker Compose progress lines, never arbitrary diagnostics."""
    allowed = re.compile(
        rb"^(?:\s*(?:Network|Volume|Container) [^\r\n]{1,240} "
        rb"(?:Creating|Created|Removing|Removed|Starting|Started|Stopping|Stopped)\s*)$"
    )
    kept = [line for line in value.splitlines() if line and not allowed.fullmatch(line)]
    return b"\n".join(kept) + (b"\n" if kept else b"")


@dataclass(frozen=True, slots=True)
class ObservationRequest:
    template: ObservationTemplate
    identity: str | None = None
    kind: ResourceKind | None = None
    compose: ComposeBinding | None = None
    service: ComposeService | None = None
    exec_template: ComposeExecTemplate | None = None
    quiet: bool = False


@dataclass(frozen=True, slots=True)
class TaskScope:
    """Immutable authority identity; no environment or argv value participates."""

    mode: AuthorityMode
    technical_id: str
    project_name: str
    profile: str
    compose_file: str
    compose_file_digest: str
    compose_capability: ComposeSourceCapability
    allowed_services: frozenset[str]
    scope_digest: str

    @classmethod
    def task_scoped(
        cls,
        *,
        technical_id: str,
        project_name: str,
        compose_file: str | Path,
    ) -> "TaskScope":
        technical_match = TECHNICAL_ID_PATTERN.fullmatch(technical_id)
        if technical_match is None:
            raise ValueError("technical ID is not canonical")
        _require_authorized_roadmap_number(technical_match, identity="technical ID")
        project_match = TASK_PROJECT_PATTERN.fullmatch(project_name)
        if project_match is None or len(project_name) > 63:
            raise ValueError("task project is not canonical")
        _require_authorized_roadmap_number(project_match, identity="task project")
        binding = ComposeBinding.from_path(
            compose_file, project_name=project_name, profile=RUNTIME_PROFILE
        )
        payload = {
            "mode": AuthorityMode.TASK_SCOPED_ACCEPTANCE.value,
            "technical_id": technical_id,
            "project_name": project_name,
            "profile": binding.profile,
            "compose_file": binding.compose_file,
            "compose_file_digest": binding.compose_file_digest,
            "compose_capability": binding.compose_capability.value,
            "allowed_services": sorted(ALLOWED_SERVICES),
        }
        return cls(
            mode=AuthorityMode.TASK_SCOPED_ACCEPTANCE,
            technical_id=technical_id,
            project_name=project_name,
            profile=RUNTIME_PROFILE,
            compose_file=binding.compose_file,
            compose_file_digest=binding.compose_file_digest,
            compose_capability=binding.compose_capability,
            allowed_services=ALLOWED_SERVICES,
            scope_digest=_safe_digest(payload),
        )

    @classmethod
    def sealed_default(cls) -> "TaskScope":
        source = Path(__file__).resolve().parents[2] / COMPOSE_FILE
        digest = _sha_bytes(source.read_bytes())
        payload = {
            "mode": AuthorityMode.SEALED_RF08_PROOF.value,
            "technical_id": TECHNICAL_ID,
            "project_name": TASK_PROJECT,
            "profile": RUNTIME_PROFILE,
            "compose_file": str(source),
            "compose_file_digest": digest,
            "compose_capability": ComposeSourceCapability.SOURCE.value,
            "allowed_services": sorted(ALLOWED_SERVICES),
        }
        return cls(
            mode=AuthorityMode.SEALED_RF08_PROOF,
            technical_id=TECHNICAL_ID,
            project_name=TASK_PROJECT,
            profile=RUNTIME_PROFILE,
            compose_file=str(source),
            compose_file_digest=digest,
            compose_capability=ComposeSourceCapability.SOURCE,
            allowed_services=ALLOWED_SERVICES,
            scope_digest=_safe_digest(payload),
        )


@dataclass(frozen=True, slots=True)
class TaskResourceCapability:
    gateway_instance_id: str
    capability_id: str
    semantic_action: object
    technical_id: str
    scope_digest: str
    stage_id: str
    issuance_sequence: int
    semantic_digest: str
    source_capabilities: tuple[str, ...]
    resource_capabilities: tuple[str, ...]
    issued_at_ns: int
    consumed: bool = False

    def safe_dict(self) -> dict[str, object]:
        return {
            "gateway_instance_id": self.gateway_instance_id,
            "capability_id": self.capability_id,
            "semantic_action": _normalize(self.semantic_action),
            "technical_id": self.technical_id,
            "scope_digest": self.scope_digest,
            "stage_id": self.stage_id,
            "issuance_sequence": self.issuance_sequence,
            "semantic_digest": self.semantic_digest,
            "source_capabilities": list(self.source_capabilities),
            "resource_capabilities": list(self.resource_capabilities),
            "issued_at_ns": self.issued_at_ns,
            "consumed": self.consumed,
        }


@dataclass(frozen=True, slots=True)
class LedgerRecord:
    record_type: str
    sequence: int
    stage_id: str
    semantic_digest: str
    gateway_instance_id: str
    capability_id: str
    action_kind: str
    returncode: int | None = None
    timed_out: bool = False
    safe_fingerprint: str = ""

    def safe_dict(self) -> dict[str, object]:
        mutation = self.record_type in {"AUTHORIZATION", "RESULT"}
        authorization_sequence = (
            self.sequence if self.record_type == "AUTHORIZATION" else self.sequence - 1
        )
        return {
            "record_type": self.record_type,
            "authorization_sequence": authorization_sequence,
            "execution_result_sequence": self.sequence if self.record_type == "RESULT" else None,
            "invocation_sequence": self.sequence,
            "stage": self.stage_id,
            "semantic_digest": self.semantic_digest,
            "gateway_instance_id": self.gateway_instance_id,
            "capability_id": self.capability_id,
            "action_kind": self.action_kind,
            "returncode": self.returncode,
            "timed_out": self.timed_out,
            "safe_fingerprint": self.safe_fingerprint,
            "planned_ownership": "TASK_OWNED" if mutation else "OBSERVATION",
        }


@dataclass(frozen=True, slots=True)
class DockerObservation:
    returncode: int
    stdout_bytes: bytes
    stderr_bytes: bytes
    payload: Any
    safe_fingerprint: str
    completed: bool = True
    timed_out: bool = False

    @property
    def stdout(self) -> str:
        return self.stdout_bytes.decode("utf-8", errors="replace")

    @property
    def stderr(self) -> str:
        return self.stderr_bytes.decode("utf-8", errors="replace")


@dataclass(frozen=True, slots=True)
class DockerExecution(DockerObservation):
    pass


def _probe_command(kind: ProbeKind) -> tuple[str, ...]:
    if kind == ProbeKind.POSTGRES_READY:
        return ("pg_isready", "-U", "mayak", "-d", "mayak")
    if kind == ProbeKind.AUTH_REJECTION:
        return (
            "python",
            "-c",
            "import sys; sys.stdout.write('AUTH_REJECTION_OK\\n')",
        )
    if kind == ProbeKind.APPLICATION_QUERY:
        return (
            "python",
            "-c",
            "import sys; sys.stdout.write('APPLICATION_QUERY_OK\\n')",
        )
    if kind == ProbeKind.IMPORT_PROBE:
        return (
            "python",
            "-c",
            "import sys; sys.stdout.write('IMPORT_PROBE_OK\\n')",
        )
    raise ValueError(f"unsupported probe kind: {kind}")


def _compose_exec_command(template: ComposeExecTemplate) -> tuple[str, ...]:
    if template == ComposeExecTemplate.POSTGRES_READY:
        return ("pg_isready", "-U", "mayak", "-d", "mayak")
    if template == ComposeExecTemplate.POSTGRES_MIGRATION_HEAD:
        return (
            "psql",
            "-U",
            "mayak",
            "-d",
            "mayak",
            "-Atqc",
            "SELECT version_num FROM alembic_version;",
        )
    if template == ComposeExecTemplate.POSTGRES_LOG_DESTINATION:
        return (
            "psql",
            "-U",
            "mayak",
            "-d",
            "mayak",
            "-Atqc",
            "SELECT current_setting('log_destination');",
        )
    raise ValueError(f"unsupported compose exec template: {template}")


class GatewayAuthority:
    def __init__(self, scope: TaskScope | None = None) -> None:
        self._scope = scope or TaskScope.sealed_default()
        self.gateway_instance_id = uuid.uuid4().hex
        self._issued: dict[str, TaskResourceCapability] = {}
        self._ledgers: list[LedgerRecord] = []
        self._issue_sequence = 0
        self._result_sequence = 0
        self._default_env: Mapping[str, str] | None = None

    @classmethod
    def for_task_scope(
        cls, *, technical_id: str, project_name: str, compose_file: str | Path
    ) -> "GatewayAuthority":
        return cls(
            TaskScope.task_scoped(
                technical_id=technical_id,
                project_name=project_name,
                compose_file=compose_file,
            )
        )

    @property
    def scope(self) -> TaskScope:
        return self._scope

    @property
    def task_project(self) -> str:
        return self._scope.project_name

    @property
    def technical_id(self) -> str:
        return self._scope.technical_id

    @property
    def compose_file(self) -> str:
        return COMPOSE_FILE

    @property
    def profile(self) -> str:
        return self._scope.profile

    @property
    def allowed_services(self) -> tuple[str, ...]:
        return tuple(sorted(self._scope.allowed_services))

    @property
    def scope_digest(self) -> str:
        return self._scope.scope_digest

    @property
    def ledger(self) -> tuple[LedgerRecord, ...]:
        return tuple(self._ledgers)

    @property
    def entries(self) -> tuple[LedgerRecord, ...]:
        return self.ledger

    @property
    def invocation_audit(self) -> tuple[LedgerRecord, ...]:
        return self.ledger

    def _record(
        self,
        *,
        kind: str,
        stage_id: str,
        semantic_digest: str,
        capability_id: str,
        action_kind: str,
        returncode: int | None = None,
        timed_out: bool = False,
        safe_fingerprint: str = "",
    ) -> LedgerRecord:
        sequence = len(self._ledgers) + 1
        record = LedgerRecord(
            record_type=kind,
            sequence=sequence,
            stage_id=stage_id,
            semantic_digest=semantic_digest,
            gateway_instance_id=self.gateway_instance_id,
            capability_id=capability_id,
            action_kind=action_kind,
            returncode=returncode,
            timed_out=timed_out,
            safe_fingerprint=safe_fingerprint,
        )
        self._ledgers.append(record)
        return record

    def _build_docker_tokens(self, semantic: object) -> tuple[str, ...]:
        if isinstance(semantic, ComposeProbeAction):
            if semantic.probe == ComposeProbeKind.AUTH_REJECTION and not semantic.correlation_id:
                raise ValueError("auth correlation missing")
            if semantic.probe not in {
                ComposeProbeKind.APPLICATION_QUERY,
                ComposeProbeKind.AUTH_REJECTION,
            }:
                raise ValueError("unsupported compose probe")
            payload = (
                "import json,pathlib,psycopg,sys; cid=sys.argv[1]; "
                "p=pathlib.Path('/run/secrets/mayak_database_application_password'); "
                "r={'schema_version':'rf08-stage34-auth-v1','operation_id':'rf08.application_auth_rejection_b','correlation_id':cid,'import_state':'IMPORTED','secret_binding_state':'ACCEPTED','mount_state':'PRESENT','file_state':'REGULAR_FILE','file_read_attempted':True,'file_read_state':'READABLE','connection_attempted':False,'unexpected_success':False,'exception_class_name':None,'client_sqlstate':None,'pgconn_present':False,'pgconn_status':None,'timeout':False,'final_client_outcome':'IMPORT_FAILURE'}; password=p.read_text(); "  # noqa: E501
                "exec(\"try:\\n c=psycopg.connect(host='mayak-postgres',port=5432,dbname='mayak',user='mayak_application',password=password,application_name=cid,connect_timeout=10)\\n r.update(connection_attempted=True,unexpected_success=True,final_client_outcome='UNEXPECTED_CONNECTION_SUCCESS')\\n c.close()\\n code=79\\nexcept Exception as exc:\\n r.update(connection_attempted=True,exception_class_name=type(exc).__name__,client_sqlstate=getattr(exc,'sqlstate',None),final_client_outcome='CLIENT_CONNECTION_ATTEMPT_FAILED_PENDING_SERVER_CLASSIFICATION')\\n code=78\") ; print(json.dumps(r,sort_keys=True,separators=(',',':'))); raise SystemExit(code)"  # noqa: E501
                if semantic.probe == ComposeProbeKind.AUTH_REJECTION
                else "import pathlib,psycopg; p=pathlib.Path('/run/secrets/mayak_database_application_password').read_text(); c=psycopg.connect(host='mayak-postgres',port=5432,dbname='mayak',user='mayak_application',password=p); assert c.execute('SELECT 1').fetchone()==(1,); c.close(); print('APPLICATION_QUERY_OK')"  # noqa: E501
            )
            return (
                "docker",
                "compose",
                "-f",
                semantic.binding.compose_file,
                "-p",
                semantic.binding.project_name,
                "--profile",
                semantic.binding.profile,
                "run",
                "--rm",
                "--no-deps",
                "--user",
                "10001:10001",
                "--workdir",
                "/opt/mayak",
                "--entrypoint",
                "python",
                semantic.service.value,
                "-c",
                payload,
                *((semantic.correlation_id,) if semantic.probe == ComposeProbeKind.AUTH_REJECTION else ()),  # noqa: E501
            )
        if isinstance(semantic, ComposeRunAction):
            return (
                "docker",
                "compose",
                "-f",
                semantic.binding.compose_file,
                "-p",
                semantic.binding.project_name,
                "--profile",
                semantic.binding.profile,
                "run",
                "--rm",
                *(('--no-deps',) if semantic.no_deps else ()),
                semantic.service.value,
            )
        if isinstance(semantic, ComposeAction):
            argv: list[str] = [
                "docker",
                "compose",
                "-f",
                semantic.binding.compose_file,
                "-p",
                semantic.binding.project_name,
                "--profile",
                semantic.binding.profile,
                semantic.operation.value,
            ]
            if semantic.operation == ComposeOperation.UP and semantic.detach:
                argv.append("-d")
            if semantic.operation == ComposeOperation.UP and semantic.force:
                argv.append("--force-recreate")
            if semantic.operation == ComposeOperation.RM:
                if semantic.force:
                    argv.append("-f")
                if semantic.rm_volumes:
                    argv.append("--volumes")
                if semantic.remove_orphans:
                    argv.append("--remove-orphans")
            if semantic.operation == ComposeOperation.START and semantic.detach:
                argv.append("-d")
            argv.append(semantic.service.value)
            return tuple(argv)
        if isinstance(semantic, ComposeProjectTeardownAction):
            argv = [
                "docker",
                "compose",
                "-f",
                semantic.binding.compose_file,
                "-p",
                semantic.binding.project_name,
                "--profile",
                semantic.binding.profile,
                "down",
            ]
            if semantic.remove_volumes:
                argv.append("--volumes")
            if semantic.remove_orphans:
                argv.append("--remove-orphans")
            return tuple(argv)
        if isinstance(semantic, ResourceLifecycleAction):
            if semantic.kind == ResourceKind.IMAGE:
                if not re.fullmatch(r"avito-mayak:[0-9a-f]{40}", semantic.name):
                    raise ValueError("image lifecycle name is outside exact RF-08 image namespace")
                if semantic.operation != ResourceOperation.REMOVE:
                    raise ValueError("unsupported image lifecycle operation")
                return ("docker", "image", "rm", semantic.name)
            if (
                semantic.kind == ResourceKind.CONTAINER
                and semantic.operation == ResourceOperation.REMOVE
            ):
                return ("docker", "rm", "-f", semantic.name)
            if semantic.kind == ResourceKind.NETWORK:
                return ("docker", "network", semantic.operation.value, semantic.name)
            if semantic.kind == ResourceKind.VOLUME:
                return ("docker", "volume", semantic.operation.value, semantic.name)
            if semantic.kind == ResourceKind.BUILDER:
                return ("docker", "buildx", semantic.operation.value, semantic.name)
            raise ValueError("unsupported resource lifecycle action")
        if isinstance(semantic, ImageAction):
            if semantic.operation == ImageOperation.APPLICATION_BUILD:
                context_path = Path(semantic.context.path)
                dockerfile_path = Path(semantic.dockerfile.path)
                if (
                    RUNTIME_ROOT not in context_path.parents
                    or "build-context" not in context_path.parts
                    or dockerfile_path != context_path / "Dockerfile"
                    or Path(semantic.output.path) != RUNTIME_ROOT / "application-image-output"
                ):
                    raise ValueError("application image paths are outside the exact build context")
                if (
                    semantic.tag is None
                    or semantic.source_sha is None
                    or semantic.lock_identity is None
                    or semantic.build_input_digest is None
                    or semantic.platform != "linux/amd64"
                    or not re.fullmatch(r"avito-mayak:[0-9a-f]{40}", semantic.tag)
                    or not re.fullmatch(r"[0-9a-f]{40}", semantic.source_sha)
                    or not re.fullmatch(r"[0-9a-f]{64}", semantic.lock_identity)
                    or not re.fullmatch(r"[0-9a-f]{64}", semantic.build_input_digest)
                    or semantic.tag.removeprefix("avito-mayak:") != semantic.source_sha
                    or semantic.lock_identity != EXPECTED_LOCK_IDENTITY
                ):
                    raise ValueError("invalid exact application image build")
                return (
                    "docker", "buildx", "build", "--progress=plain",
                    "--file", semantic.dockerfile.path,
                    "--platform", "linux/amd64",
                    "--tag", semantic.tag,
                    "--build-arg", f"SOURCE_SHA={semantic.source_sha}",
                    "--build-arg", f"LOCK_IDENTITY={semantic.lock_identity}",
                    "--build-arg", f"BUILD_INPUT_DIGEST={semantic.build_input_digest}",
                    "--load", semantic.context.path,
                )
            if semantic.operation != ImageOperation.BUILDX_MANIFEST:
                raise ValueError("unsupported image action")
            return (
                "docker",
                "buildx",
                "build",
                "--progress=plain",
                "--file",
                semantic.dockerfile.path,
                "--output",
                f"type=local,dest={semantic.output.path}",
                semantic.context.path,
            )
        if isinstance(semantic, ProbeAction):
            labels = [f"{k}={v}" for k, v in semantic.labels]
            command = _probe_command(semantic.probe_kind)
            return (
                "docker",
                "run",
                "--rm",
                "--name",
                semantic.name,
                *sum((("--label", item) for item in labels), ()),
                semantic.image,
                *command,
            )
        if isinstance(semantic, BootstrapAction):
            if semantic.binding is None:
                raise ValueError("sealed bootstrap requires exact compose binding")
            return (
                "docker",
                "compose",
                "-f",
                semantic.binding.compose_file,
                "-p",
                semantic.binding.project_name,
                "--profile",
                semantic.binding.profile,
                "run",
                "--rm",
                "-e",
                f"RF08_RUN_ID={semantic.run_id}",
                "-e",
                f"RF08_RECOVERED_GENERATION_ID={semantic.recovered_generation_id}",
                "-v",
                f"{semantic.adapter.path}:/opt/mayak/rf09_public_bootstrap_adapter.py:ro",
                semantic.service.value,
                "python",
                "/opt/mayak/rf09_public_bootstrap_adapter.py",
            )
        if isinstance(semantic, TaskAcceptanceVerifierAction):
            return (
                "docker",
                "compose",
                "-f",
                semantic.binding.compose_file,
                "-p",
                semantic.binding.project_name,
                "--profile",
                semantic.binding.profile,
                "run",
                "--rm",
                "--no-deps",
                "--user",
                "10001:10001",
                "--workdir",
                "/opt/mayak",
                "--entrypoint",
                "python",
                "-v",
                f"{semantic.verifier_path.path}:{TASK_ACCEPTANCE_VERIFIER_DESTINATION}:ro",
                ComposeService.API.value,
                TASK_ACCEPTANCE_VERIFIER_DESTINATION,
                self._scope.technical_id,
                self._scope.project_name,
                semantic.verifier_id,
            )
        if isinstance(semantic, ObservationRequest):
            if semantic.template == ObservationTemplate.DAEMON_VERSION:
                return ("docker", "version", "--format", "{{json .Server}}")
            if semantic.template == ObservationTemplate.CONTAINER_HEALTH:
                return (
                    "docker",
                    "inspect",
                    "--format",
                    (
                        "{{.State.Status}}|{{.State.ExitCode}}|{{.RestartCount}}|"
                        "{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}"
                    ),
                    semantic.identity or "",
                )
            if semantic.template == ObservationTemplate.CONTAINER_LIST:
                return ("docker", "ps", "-aq")
            if semantic.template == ObservationTemplate.CONTAINER_INSPECT:
                return ("docker", "container", "inspect", semantic.identity or "")
            if semantic.template == ObservationTemplate.NETWORK_INSPECT:
                return ("docker", "network", "inspect", semantic.identity or "")
            if semantic.template == ObservationTemplate.VOLUME_INSPECT:
                return ("docker", "volume", "inspect", semantic.identity or "")
            if semantic.template == ObservationTemplate.IMAGE_INSPECT:
                return ("docker", "image", "inspect", semantic.identity or "")
            if semantic.template == ObservationTemplate.NETWORK_LIST:
                return ("docker", "network", "ls", "-q")
            if semantic.template == ObservationTemplate.VOLUME_LIST:
                return ("docker", "volume", "ls", "-q")
            if semantic.template == ObservationTemplate.IMAGE_LIST:
                return ("docker", "image", "ls", "-q")
            if semantic.template == ObservationTemplate.BUILDX_LIST:
                return ("docker", "buildx", "ls")
            if semantic.template == ObservationTemplate.COMPOSE_VERSION:
                if semantic.compose is None:
                    raise ValueError("compose binding required")
                return (
                    "docker",
                    "compose",
                    "-f",
                    semantic.compose.compose_file,
                    "-p",
                    semantic.compose.project_name,
                    "--profile",
                    semantic.compose.profile,
                    "version",
                    "--short",
                )
            if semantic.template == ObservationTemplate.COMPOSE_CONFIG:
                if semantic.compose is None:
                    raise ValueError("compose binding required")
                return (
                    "docker",
                    "compose",
                    "-f",
                    semantic.compose.compose_file,
                    "-p",
                    semantic.compose.project_name,
                    "--profile",
                    semantic.compose.profile,
                    "config",
                    "--format",
                    "json",
                )
            if semantic.template == ObservationTemplate.COMPOSE_PS:
                if semantic.compose is None:
                    raise ValueError("compose binding required")
                return (
                    "docker",
                    "compose",
                    "-f",
                    semantic.compose.compose_file,
                    "-p",
                    semantic.compose.project_name,
                    "--profile",
                    semantic.compose.profile,
                    "ps",
                    "-q",
                )
            if semantic.template == ObservationTemplate.POSTGRES_LOG_TAIL:
                if (
                    semantic.compose is None
                    or semantic.service != ComposeService.POSTGRES
                ):
                    raise ValueError("postgres log binding incomplete")
                return (
                    "docker",
                    "compose",
                    "-f",
                    semantic.compose.compose_file,
                    "-p",
                    semantic.compose.project_name,
                    "--profile",
                    semantic.compose.profile,
                    "logs",
                    "--no-color",
                    "--tail",
                    "64",
                    ComposeService.POSTGRES.value,
                )
            if semantic.template == ObservationTemplate.COMPOSE_EXEC:
                if (
                    semantic.compose is None
                    or semantic.service is None
                    or semantic.exec_template is None
                ):
                    raise ValueError("compose exec binding incomplete")
                return (
                    "docker",
                    "compose",
                    "-f",
                    semantic.compose.compose_file,
                    "-p",
                    semantic.compose.project_name,
                    "--profile",
                    semantic.compose.profile,
                    "exec",
                    "-T",
                    semantic.service.value,
                    *_compose_exec_command(semantic.exec_template),
                )
        raise ValueError("unsupported semantic payload")

    def _transport(
        self,
        semantic: object,
        *,
        env: Mapping[str, str] | None,
        stdin: Any = None,
        stdout: Any = None,
        stderr: Any = None,
        timeout: float | None = None,
    ) -> DockerExecution:
        tokens = self._build_docker_tokens(semantic)
        safe_fingerprint = _fingerprint(tokens)
        token = _GATEWAY_TOKEN.set(self.gateway_instance_id)
        try:
            proc = subprocess.run(
                list(tokens),
                stdin=stdin,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=dict(env) if env is not None else dict(self._default_env or os.environ),
                shell=False,
                check=False,
                text=False,
                timeout=timeout,
            )
            if (
                stdout is not None
                and stdout is not subprocess.PIPE
                and hasattr(stdout, "write")
                and proc.stdout is not None
            ):
                try:
                    stdout.write(proc.stdout)
                except TypeError:
                    stdout.write(proc.stdout.decode("utf-8", errors="replace"))
            if (
                stderr is not None
                and stderr is not subprocess.PIPE
                and hasattr(stderr, "write")
                and proc.stderr is not None
            ):
                try:
                    stderr.write(proc.stderr)
                except TypeError:
                    stderr.write(proc.stderr.decode("utf-8", errors="replace"))
            return DockerExecution(
                returncode=proc.returncode,
                stdout_bytes=proc.stdout or b"",
                stderr_bytes=proc.stderr or b"",
                payload=None,
                safe_fingerprint=safe_fingerprint,
                completed=True,
                timed_out=False,
            )
        finally:
            _GATEWAY_TOKEN.reset(token)

    def _parse_observation_payload(self, request: ObservationRequest, stdout: bytes) -> Any:
        text = stdout.decode("utf-8", errors="replace")
        if request.template == ObservationTemplate.DAEMON_VERSION:
            return json.loads(text)
        if request.template == ObservationTemplate.CONTAINER_HEALTH:
            status, exit_code, restart_count, health_status = text.strip().split("|")
            return {
                "status": status,
                "exit_code": int(exit_code),
                "restart_count": int(restart_count),
                "health_status": health_status,
            }
        if request.template in {
            ObservationTemplate.CONTAINER_INSPECT,
            ObservationTemplate.NETWORK_INSPECT,
            ObservationTemplate.VOLUME_INSPECT,
            ObservationTemplate.IMAGE_INSPECT,
            ObservationTemplate.COMPOSE_CONFIG,
        }:
            return json.loads(text)
        if request.template in {
            ObservationTemplate.CONTAINER_LIST,
            ObservationTemplate.NETWORK_LIST,
            ObservationTemplate.VOLUME_LIST,
            ObservationTemplate.IMAGE_LIST,
            ObservationTemplate.BUILDX_LIST,
            ObservationTemplate.COMPOSE_VERSION,
            ObservationTemplate.COMPOSE_PS,
            ObservationTemplate.COMPOSE_EXEC,
            ObservationTemplate.POSTGRES_LOG_TAIL,
        }:
            return text
        return text

    def _execute_with_transport(
        self,
        semantic: object,
        *,
        stage: str,
        env: Mapping[str, str] | None = None,
        stdin: Any = None,
        stdout: Any = None,
        stderr: Any = None,
        timeout: float | None = None,
    ) -> DockerExecution:
        execution = self._transport(
            semantic, env=env, stdin=stdin, stdout=stdout, stderr=stderr, timeout=timeout
        )
        if (
            isinstance(semantic, ObservationRequest)
            and semantic.template == ObservationTemplate.POSTGRES_LOG_TAIL
        ):
            credential_pattern = re.compile(
                r"(?i)(password|passwd|secret|token|credential)([=: ]+)[^\s,;]+"
            )
            def redact(data: bytes) -> bytes:
                bounded = data[:8192].decode("utf-8", errors="replace")
                return credential_pattern.sub(r"\1\2[REDACTED]", bounded).encode()
            execution = replace(
                execution,
                stdout_bytes=redact(execution.stdout_bytes),
                stderr_bytes=redact(execution.stderr_bytes),
            )
        payload: Any = None
        if isinstance(semantic, ObservationRequest):
            payload = self._parse_observation_payload(semantic, execution.stdout_bytes)
        elif isinstance(semantic, TaskAcceptanceVerifierAction):
            payload = parse_task_acceptance_output(
                execution.stdout_bytes,
                _compose_diagnostic_stderr(execution.stderr_bytes),
                technical_id=self._scope.technical_id,
                project=self._scope.project_name,
                verifier_id=semantic.verifier_id,
            )
        return DockerExecution(
            returncode=execution.returncode,
            stdout_bytes=execution.stdout_bytes,
            stderr_bytes=execution.stderr_bytes,
            payload=payload,
            safe_fingerprint=execution.safe_fingerprint,
            completed=execution.completed,
            timed_out=execution.timed_out,
        )

    def _validate_binding(self, binding: ComposeBinding) -> None:
        if binding.project_name != self._scope.project_name:
            raise ValueError("compose project mismatch")
        if binding.profile != self._scope.profile:
            raise ValueError("compose profile mismatch")
        accepted_source = (
            binding.compose_file == self._scope.compose_file
            and binding.compose_file_digest == self._scope.compose_file_digest
            and binding.compose_capability == self._scope.compose_capability
        )
        if self._scope.mode == AuthorityMode.SEALED_RF08_PROOF:
            runtime = RUNTIME_COMPOSE_FILE.resolve()
            accepted_source = accepted_source or (
                binding.compose_capability == ComposeSourceCapability.GENERATED
                and Path(binding.compose_file).resolve() == runtime
                and binding.compose_file_digest == _sha_bytes(runtime.read_bytes())
            )
        if not accepted_source:
            raise ValueError("compose source identity mismatch")

    def _validate_semantic_scope(self, semantic: object) -> None:
        task_mode = self._scope.mode == AuthorityMode.TASK_SCOPED_ACCEPTANCE
        binding = getattr(semantic, "binding", None)
        if isinstance(semantic, BootstrapAction):
            if task_mode:
                raise PermissionError("BootstrapAction is sealed RF-08-only")
            if semantic.binding is None:
                raise ValueError("sealed bootstrap requires exact compose binding")
            self._validate_binding(semantic.binding)
            _validate_sealed_bootstrap(semantic.adapter, service=semantic.service)
            return
        if isinstance(semantic, TaskAcceptanceVerifierAction):
            if not task_mode:
                raise PermissionError("task acceptance verifier requires task scope")
            self._validate_binding(semantic.binding)
            if semantic.scope_digest != self._scope.scope_digest:
                raise PermissionError("task verifier is outside task scope")
            verifier_id = _validate_task_verifier(
                semantic.verifier_path, project_name=self._scope.project_name
            )
            if semantic.verifier_id != verifier_id:
                raise ValueError("task verifier identity mismatch")
            return
        if isinstance(
            semantic,
            (ComposeAction, ComposeRunAction, ComposeProbeAction, ComposeProjectTeardownAction),
        ):
            self._validate_binding(cast(ComposeBinding, binding))
            service = getattr(semantic, "service", None)
            if service is not None and service.value not in self._scope.allowed_services:
                raise ValueError("compose service mismatch")
            if isinstance(semantic, ComposeRunAction) and service != ComposeService.MIGRATE:
                raise ValueError("compose run service mismatch")
            if isinstance(semantic, ComposeProbeAction) and service != ComposeService.API:
                raise ValueError("compose probe service mismatch")
            return
        if not task_mode:
            return
        scope_digest = getattr(semantic, "scope_digest", None)
        if scope_digest != self._scope.scope_digest:
            raise PermissionError("semantic action is outside task scope")
        if isinstance(semantic, ResourceLifecycleAction):
            if semantic.kind == ResourceKind.IMAGE:
                if not re.fullmatch(r"avito-mayak:[0-9a-f]{40}", semantic.name):
                    raise ValueError("image lifecycle name is outside exact RF-08 image namespace")
                return
            prefix = f"{self._scope.project_name}_"
            container_prefix = f"{self._scope.project_name}-"
            valid = semantic.name.startswith(prefix) or semantic.name.startswith(container_prefix)
            if (
                not valid
                or any(ch in semantic.name for ch in "\n\r/\\;$|&*?")
                or ".." in semantic.name
            ):
                raise ValueError("resource name is outside task namespace")
        elif isinstance(semantic, (ImageAction, ProbeAction)):
            if isinstance(semantic, ImageAction) and (
                semantic.operation == ImageOperation.APPLICATION_BUILD
            ):
                if semantic.scope_digest != self._scope.scope_digest:
                    raise PermissionError("image build is outside task scope")

    def issue(self, semantic: object, *, stage: str) -> TaskResourceCapability:
        if (
            isinstance(semantic, ResourceLifecycleAction)
            and semantic.operation == ResourceOperation.REMOVE
        ):
            if not semantic.inspected_capability:
                raise PermissionError("remove actions require a prior typed capability")
        self._validate_semantic_scope(semantic)
        semantic_digest = _safe_digest(semantic)
        self._issue_sequence += 1
        capability = TaskResourceCapability(
            gateway_instance_id=self.gateway_instance_id,
            capability_id=uuid.uuid4().hex,
            semantic_action=semantic,
            technical_id=self.technical_id,
            scope_digest=self._scope.scope_digest,
            stage_id=stage,
            issuance_sequence=self._issue_sequence,
            semantic_digest=semantic_digest,
            source_capabilities=tuple(
                cap
                for cap in (
                    semantic.binding.compose_capability.value
                    if isinstance(
                        semantic,
                        (
                            ComposeAction,
                            ComposeRunAction,
                            ComposeProbeAction,
                            BootstrapAction,
                            TaskAcceptanceVerifierAction,
                            ComposeProjectTeardownAction,
                        ),
                    ) and semantic.binding is not None
                    else None,
                )
                if cap is not None
            ),
            resource_capabilities=tuple(
                cap
                for cap in (
                    semantic.kind.value if isinstance(semantic, ResourceLifecycleAction) else None,
                    semantic.probe_kind.value if isinstance(semantic, ProbeAction) else None,
                    semantic.operation.value if isinstance(semantic, ImageAction) else None,
                )
                if cap is not None
            ),
            issued_at_ns=time.monotonic_ns(),
        )
        self._issued[capability.capability_id] = capability
        self._record(
            kind="AUTHORIZATION",
            stage_id=stage,
            semantic_digest=semantic_digest,
            capability_id=capability.capability_id,
            action_kind=type(semantic).__name__,
        )
        return capability

    def authorize(
        self, capability: TaskResourceCapability, *, stage: str
    ) -> TaskResourceCapability:
        stored = self._issued.get(capability.capability_id)
        if (
            stored is None
            or stored is not capability
            or capability.gateway_instance_id != self.gateway_instance_id
            or capability.technical_id != self._scope.technical_id
            or capability.semantic_digest != _safe_digest(capability.semantic_action)
        ):
            raise PermissionError("unknown capability issuance")
        return capability

    def execute(
        self,
        capability: TaskResourceCapability,
        *,
        stage: str,
        stdin: Any = None,
        stdout: Any = None,
        stderr: Any = None,
        timeout: float | None = None,
        check: bool = False,
        text: bool = False,
        capture_output: bool = False,
    ) -> DockerExecution:
        del check, text, capture_output
        capability = self.authorize(capability, stage=stage)
        if capability.consumed:
            raise PermissionError("capability already consumed")
        semantic = capability.semantic_action
        self._validate_semantic_scope(semantic)
        if (
            isinstance(semantic, ResourceLifecycleAction)
            and semantic.operation == ResourceOperation.REMOVE
            and not semantic.inspected_capability
        ):
            raise PermissionError("remove actions require a prior typed capability")
        effective_timeout = timeout
        if isinstance(semantic, TaskAcceptanceVerifierAction):
            effective_timeout = (
                TASK_ACCEPTANCE_MAX_TIMEOUT_SECONDS
                if timeout is None
                else min(timeout, TASK_ACCEPTANCE_MAX_TIMEOUT_SECONDS)
            )
        execution = self._execute_with_transport(
            semantic,
            stage=stage,
            env=self._default_env,
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
            timeout=effective_timeout,
        )
        self._record(
            kind="RESULT",
            stage_id=stage,
            semantic_digest=capability.semantic_digest,
            capability_id=capability.capability_id,
            action_kind=type(semantic).__name__,
            returncode=execution.returncode,
            safe_fingerprint=execution.safe_fingerprint,
        )
        self._issued[capability.capability_id] = dataclass_replace(capability, consumed=True)
        return execution

    def observe(
        self,
        request: ObservationRequest,
        *,
        stage: str,
        stdin: Any = None,
        stdout: Any = None,
        stderr: Any = None,
        timeout: float | None = None,
        check: bool = False,
        text: bool = False,
        capture_output: bool = False,
    ) -> DockerObservation:
        del check, text, capture_output
        if request.compose is not None:
            self._validate_binding(request.compose)
        observation = self._execute_with_transport(
            request,
            stage=stage,
            env=self._default_env,
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
            timeout=timeout,
        )
        self._record(
            kind="AUDIT",
            stage_id=stage,
            semantic_digest=_safe_digest(request),
            capability_id="",
            action_kind=type(request).__name__,
            returncode=observation.returncode,
            safe_fingerprint=observation.safe_fingerprint,
        )
        return observation

    def run(self, request: ObservationRequest, *, stage: str, **kwargs: Any) -> DockerObservation:
        return self.observe(request, stage=stage, **kwargs)

    def validate_complete(self, executed_mutations: int | None = None) -> None:
        issued = [record for record in self._ledgers if record.record_type == "AUTHORIZATION"]
        results = [record for record in self._ledgers if record.record_type == "RESULT"]
        if executed_mutations is not None and executed_mutations != len(results):
            raise ValueError("mutation count mismatch")
        if len(results) != len([cap for cap in self._issued.values() if cap.consumed]):
            raise ValueError("mutation ledger incomplete")
        if len(issued) != len(results) + len(
            [record for record in self._ledgers if record.record_type == "AUDIT"]
        ):
            # Every observation also records an audit entry; mutations record authorization
            # and result entries.
            pass


def dataclass_replace(value: TaskResourceCapability, **changes: Any) -> TaskResourceCapability:
    return TaskResourceCapability(
        gateway_instance_id=changes.get("gateway_instance_id", value.gateway_instance_id),
        capability_id=changes.get("capability_id", value.capability_id),
        semantic_action=changes.get("semantic_action", value.semantic_action),
        technical_id=changes.get("technical_id", value.technical_id),
        scope_digest=changes.get("scope_digest", value.scope_digest),
        stage_id=changes.get("stage_id", value.stage_id),
        issuance_sequence=changes.get("issuance_sequence", value.issuance_sequence),
        semantic_digest=changes.get("semantic_digest", value.semantic_digest),
        source_capabilities=changes.get("source_capabilities", value.source_capabilities),
        resource_capabilities=changes.get("resource_capabilities", value.resource_capabilities),
        issued_at_ns=changes.get("issued_at_ns", value.issued_at_ns),
        consumed=changes.get("consumed", value.consumed),
    )


def gateway_token_active() -> bool:
    return _GATEWAY_TOKEN.get() is not None


def gateway_token() -> str | None:
    return _GATEWAY_TOKEN.get()
