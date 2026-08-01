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
import subprocess
import time
import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, fields, is_dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, Final

TASK_PROJECT: Final = "avito-mayak-rf08-secret-delivery"
TECHNICAL_ID: Final = (
    "RF-08-CORRECTIVE-SEALED-PLAN-PROVENANCE-EXACT-BASE-AND-FAIL-CLOSED-INVENTORY-20260730-02"
)
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
        runtime_compose = Path("/opt/avito-mayak-runtime/rf08-secret-delivery/compose.runtime.yaml")
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
class ComposeRunAction:
    binding: ComposeBinding
    service: ComposeService


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

    def __post_init__(self) -> None:
        if self.operation == ResourceOperation.REMOVE and not self.inspected_capability:
            raise ValueError("remove actions require a prior inspected capability")


@dataclass(frozen=True, slots=True)
class ImageAction:
    operation: ImageOperation
    context: PathCapability
    dockerfile: PathCapability
    output: PathCapability


@dataclass(frozen=True, slots=True)
class ProbeAction:
    probe_kind: ProbeKind
    image: str
    name: str
    labels: tuple[tuple[str, str], ...]
    network_policy: NetworkPolicy
    secret_mount: SecretMountCapability


@dataclass(frozen=True, slots=True)
class BootstrapAction:
    binding: ComposeBinding | None
    service: ComposeService
    run_id: str
    recovered_generation_id: str
    adapter: PathCapability


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
class TaskResourceCapability:
    gateway_instance_id: str
    capability_id: str
    semantic_action: object
    technical_id: str
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
    def __init__(self) -> None:
        self.task_project = TASK_PROJECT
        self.technical_id = TECHNICAL_ID
        self.compose_file = COMPOSE_FILE
        self.profile = RUNTIME_PROFILE
        self.allowed_services = tuple(sorted(ALLOWED_SERVICES))
        self.gateway_instance_id = uuid.uuid4().hex
        self._issued: dict[str, TaskResourceCapability] = {}
        self._ledgers: list[LedgerRecord] = []
        self._issue_sequence = 0
        self._result_sequence = 0
        self._default_env: Mapping[str, str] | None = None

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

    def _build_argv(self, semantic: object) -> tuple[str, ...]:
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
        if isinstance(semantic, ResourceLifecycleAction):
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
                return (
                    "docker",
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
                    semantic.service.value,
                    *_compose_exec_command(semantic.exec_template),
                )
        raise ValueError("unsupported semantic payload")

    def _transport(
        self,
        argv: Sequence[str],
        *,
        env: Mapping[str, str] | None,
        stdin: Any = None,
        stdout: Any = None,
        stderr: Any = None,
        timeout: float | None = None,
    ) -> tuple[int, bytes, bytes]:
        token = _GATEWAY_TOKEN.set(self.gateway_instance_id)
        try:
            proc = subprocess.run(
                list(argv),
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
            return proc.returncode, proc.stdout or b"", proc.stderr or b""
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
        argv = self._build_argv(semantic)
        fingerprint = _fingerprint(argv)
        code, stdout_bytes, stderr_bytes = self._transport(
            argv, env=env, stdin=stdin, stdout=stdout, stderr=stderr, timeout=timeout
        )
        payload: Any = None
        if isinstance(semantic, ObservationRequest):
            payload = self._parse_observation_payload(semantic, stdout_bytes)
        return DockerExecution(
            returncode=code,
            stdout_bytes=stdout_bytes,
            stderr_bytes=stderr_bytes,
            payload=payload,
            safe_fingerprint=fingerprint,
            completed=True,
            timed_out=False,
        )

    def issue(self, semantic: object, *, stage: str) -> TaskResourceCapability:
        if (
            isinstance(semantic, ResourceLifecycleAction)
            and semantic.operation == ResourceOperation.REMOVE
        ):
            if not semantic.inspected_capability:
                raise PermissionError("remove actions require a prior typed capability")
        if isinstance(semantic, ComposeAction):
            if semantic.service.value not in ALLOWED_SERVICES:
                raise ValueError("compose service mismatch")
            if semantic.binding.project_name != TASK_PROJECT:
                raise ValueError("compose project mismatch")
            if semantic.binding.profile != RUNTIME_PROFILE:
                raise ValueError("compose profile mismatch")
        if isinstance(semantic, ComposeRunAction):
            if semantic.service != ComposeService.MIGRATE:
                raise ValueError("compose run service mismatch")
            if semantic.binding.project_name != TASK_PROJECT:
                raise ValueError("compose project mismatch")
            if semantic.binding.profile != RUNTIME_PROFILE:
                raise ValueError("compose profile mismatch")
        if isinstance(semantic, ComposeProbeAction):
            if semantic.service != ComposeService.API:
                raise ValueError("compose probe service mismatch")
            if semantic.binding.project_name != TASK_PROJECT:
                raise ValueError("compose project mismatch")
            if semantic.binding.profile != RUNTIME_PROFILE:
                raise ValueError("compose profile mismatch")
        semantic_digest = _safe_digest(semantic)
        self._issue_sequence += 1
        capability = TaskResourceCapability(
            gateway_instance_id=self.gateway_instance_id,
            capability_id=uuid.uuid4().hex,
            semantic_action=semantic,
            technical_id=self.technical_id,
            stage_id=stage,
            issuance_sequence=self._issue_sequence,
            semantic_digest=semantic_digest,
            source_capabilities=tuple(
                cap
                for cap in (
                    semantic.binding.compose_capability.value
                    if isinstance(semantic, ComposeAction)
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
        if stored is None or stored is not capability:
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
        if (
            isinstance(semantic, ResourceLifecycleAction)
            and semantic.operation == ResourceOperation.REMOVE
            and not semantic.inspected_capability
        ):
            raise PermissionError("remove actions require a prior typed capability")
        execution = self._execute_with_transport(
            semantic,
            stage=stage,
            env=self._default_env,
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
            timeout=timeout,
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
