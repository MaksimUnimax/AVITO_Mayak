"""Observed, redacted Docker records used by both RF-08 verdicts."""

from __future__ import annotations

import hashlib
import json
import os
import socket
import stat
import struct
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

from scripts.runtime.rf08_docker_authority import GatewayAuthority, _ReadOnlyDockerQuery
from scripts.runtime.rf08_safe_foreign_schema import validate_safe_value

SCHEMA_VERSION: Final = "ForeignResourceSnapshotV3"
COLLECTOR_ID: Final = "rf08.producer.observed.typed-docker.v3"
TASK_PROJECT: Final = "avito-mayak-rf08-secret-delivery"
TASK_ID: Final = (
    "RF-08-CORRECTIVE-SEALED-PLAN-PROVENANCE-EXACT-BASE-AND-FAIL-CLOSED-INVENTORY-20260730-02"
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


class CollectionFailure(RuntimeError):
    pass


@dataclass(frozen=True)
class ForeignResourceDeltaV3:
    classification: str
    resource_set_equal: bool
    structural_equal: bool
    runtime_equal: bool


def _digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _identity_hash(prefix: str, value: bytes) -> str:
    return hashlib.sha256(prefix.encode() + b":" + value).hexdigest()


def _host_identity() -> str:
    value = Path("/etc/machine-id").read_bytes().strip()
    if not value or len(value) > 256:
        raise CollectionFailure("missing host identity")
    return _identity_hash("rf08-host-v2", value)


def _boot_identity() -> str:
    value = Path("/proc/sys/kernel/random/boot_id").read_bytes().strip()
    if not value or len(value) > 256:
        raise CollectionFailure("missing boot identity")
    return _identity_hash("rf08-boot-v1", value)


def _docker_endpoint() -> Path:
    raw = os.environ.get("DOCKER_HOST", "unix:///var/run/docker.sock")
    if not raw.startswith("unix://"):
        raise CollectionFailure("foreign docker endpoint")
    path = raw.removeprefix("unix://")
    if not path.startswith("/") or ".." in Path(path).parts:
        raise CollectionFailure("unsafe docker endpoint")
    endpoint = Path(os.path.abspath(path))
    try:
        metadata = endpoint.lstat()
    except OSError as exc:
        raise CollectionFailure("docker endpoint unavailable") from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISSOCK(metadata.st_mode):
        raise CollectionFailure("docker endpoint is not a safe unix socket")
    return endpoint


def _peer_start_time(pid: int) -> str:
    text = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8")
    close = text.rfind(")")
    if close < 0:
        raise CollectionFailure("malformed peer stat")
    fields = text[close + 2 :].split()
    if len(fields) <= 19 or not fields[19].isdigit():
        raise CollectionFailure("missing peer start time")
    return fields[19]


def _endpoint_identity(gateway: GatewayAuthority) -> tuple[str, str, dict[str, str]]:
    endpoint = _docker_endpoint()
    socket_stat = endpoint.stat()
    if not stat.S_ISSOCK(socket_stat.st_mode):
        raise CollectionFailure("docker endpoint is not a unix socket")
    peer: tuple[int, int, int] | None = None
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
        connection.connect(str(endpoint))
        try:
            raw_peer = connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12)
        except OSError:
            raw_peer = b""
        if raw_peer and len(raw_peer) != 12:
            raise CollectionFailure("malformed peer credentials")
        if raw_peer:
            try:
                peer = struct.unpack("3i", raw_peer)
            except struct.error as exc:
                raise CollectionFailure("malformed peer credentials") from exc
    if peer is not None and any(value < 0 for value in peer):
        raise CollectionFailure("invalid peer credentials")
    server = gateway.run(
        _ReadOnlyDockerQuery._from_argv(("docker", "version", "--format", "{{json .Server}}")),
        stage="foreign-endpoint-version",
        capture_output=True,
        check=False,
        timeout=30,
    )
    if server.returncode:
        raise CollectionFailure("docker server version failed")
    parsed = json.loads(server.stdout)
    if not isinstance(parsed, dict):
        raise CollectionFailure("docker server envelope malformed")
    safe_server = {
        key: str(parsed[key])
        for key in ("Version", "ApiVersion", "MinAPIVersion", "Os", "Arch", "KernelVersion")
        if parsed.get(key) is not None
    }
    if not safe_server.get("Version"):
        raise CollectionFailure("docker server version absent")
    payload = {
        "schema": (
            "LOCAL_UNIX_DOCKER_ENDPOINT_INSTANCE_V1"
            if peer
            else "LOCAL_UNIX_DOCKER_ENDPOINT_SOCKET_V1"
        ),
        "socket": {
            "path": str(endpoint),
            "st_dev": socket_stat.st_dev,
            "st_ino": socket_stat.st_ino,
            "mode": socket_stat.st_mode,
        },
        "boot": _boot_identity(),
        "server": safe_server,
    }
    if peer:
        pid, uid, gid = peer
        try:
            start_time = _peer_start_time(pid)
            executable = Path(f"/proc/{pid}/exe").stat()
        except OSError:
            start_time = ""
            executable = None
        if start_time and executable is not None:
            payload["peer"] = {
                "pid": pid,
                "uid": uid,
                "gid": gid,
                "start_time": start_time,
                "exe_dev": executable.st_dev,
                "exe_ino": executable.st_ino,
            }
        else:
            payload["schema"] = "LOCAL_UNIX_DOCKER_ENDPOINT_SOCKET_V1"
    return (str(payload["schema"]), _digest(payload), safe_server)


def _daemon_identity(gateway: GatewayAuthority) -> str:
    return _endpoint_identity(gateway)[1]


def _labels(value: Any) -> dict[str, str]:
    return {str(k): str(v) for k, v in sorted(value.items())} if isinstance(value, dict) else {}


def _safe_labels(labels: dict[str, str]) -> list[list[str]]:
    return [
        [
            k
            if k
            in {
                "com.docker.compose.project",
                "com.docker.compose.service",
                "com.avito-mayak.technical-id",
            }
            else _digest(k),
            v
            if k
            in {
                "com.docker.compose.project",
                "com.docker.compose.service",
                "com.avito-mayak.technical-id",
            }
            and v in {TASK_PROJECT, TASK_ID, *ALLOWED_SERVICES}
            else _digest(v),
        ]
        for k, v in labels.items()
    ]


def _ownership(name: str, labels: dict[str, str], kind: str) -> str:
    project = labels.get("com.docker.compose.project")
    technical = labels.get("com.avito-mayak.technical-id")
    task_indicator = project == TASK_PROJECT or name.startswith(TASK_PROJECT)
    if name == "apm-postgres" and kind == "container":
        return "FOREIGN"
    if technical != TASK_ID:
        return "UNRESOLVED" if task_indicator else "FOREIGN"
    if kind == "container":
        service = labels.get("com.docker.compose.service")
        exact = (
            project == TASK_PROJECT
            and service in ALLOWED_SERVICES
            and name == f"{TASK_PROJECT}-{service}-1"
        )
        direct_exact = project == TASK_PROJECT and name.startswith(TASK_PROJECT)
        if exact or direct_exact:
            return "TASK_OWNED"
    elif kind == "network":
        exact = project == TASK_PROJECT and name == TASK_PROJECT + "_mayak-internal"
    elif kind == "volume":
        exact = project == TASK_PROJECT and name == TASK_PROJECT + "_postgres-data"
    else:
        exact = False
    if exact:
        return "TASK_OWNED"
    return "UNRESOLVED" if task_indicator else "FOREIGN"


def _inspect(gateway: GatewayAuthority, kind: str, ident: str) -> dict[str, Any]:
    proc = gateway.run(
        _ReadOnlyDockerQuery._from_argv(("docker", kind, "inspect", ident)),
        stage=f"foreign-inspect-{kind}",
        capture_output=True,
        check=False,
        timeout=30,
    )
    if proc.returncode:
        raise CollectionFailure("inspect failed")
    value = json.loads(proc.stdout)
    if not isinstance(value, list) or len(value) != 1 or not isinstance(value[0], dict):
        raise CollectionFailure("inspect cardinality")
    item = value[0]
    actual = str(
        item.get("Id") or item.get("ID") or item.get("Name") or item.get("Name", "")
    ).lstrip("/")
    if actual and not (
        ident == actual
        or actual.startswith(ident)
        or ident == str(item.get("Name", "")).lstrip("/")
    ):
        raise CollectionFailure("inspect identity mismatch")
    return item


def _enumerate(gateway: GatewayAuthority, kind: str) -> list[str]:
    command = ("docker", "ps", "-aq") if kind == "container" else ("docker", kind, "ls", "-q")
    proc = gateway.run(
        _ReadOnlyDockerQuery._from_argv(command),
        stage=f"foreign-enumerate-{kind}",
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    if proc.returncode:
        raise CollectionFailure("enumeration failed")
    ids = [x.strip() for x in proc.stdout.splitlines() if x.strip()]
    seen: list[str] = []
    for ident in ids:
        if ident in seen:
            raise CollectionFailure("duplicate resource identity")
        seen.append(ident)
    return ids


def _container(item: dict[str, Any]) -> dict[str, Any]:
    name = str(item.get("Name", "")).lstrip("/")
    cfg = item.get("Config") or {}
    host = item.get("HostConfig") or {}
    state = item.get("State") or {}
    labels = _labels(cfg.get("Labels"))
    stable = {
        "fingerprint": _digest(["container", item.get("Id"), name]),
        "name": _digest(name),
        "is_apm_postgres": name == "apm-postgres",
        "id": _digest(str(item.get("Id"))),
        "image_id_hash": _digest(str(item.get("Image"))),
        "image_reference_hash": _digest(str(cfg.get("Image"))),
        "labels": _safe_labels(labels),
        "restart_policy": (host.get("RestartPolicy") or {}).get("Name"),
        "network_mode": (
            host.get("NetworkMode")
            if host.get("NetworkMode") in {"host", "none", "bridge", "default"}
            else _digest(str(host.get("NetworkMode")))
        ),
        "privileged": host.get("Privileged"),
        "read_only_rootfs": host.get("ReadonlyRootfs"),
        "mounts": sorted(
            (
                {
                    "type": m.get("Type"),
                    "destination_hash": _digest(str(m.get("Destination"))),
                    "mode": m.get("Mode"),
                    "rw": m.get("RW"),
                }
                for m in item.get("Mounts", [])
                if isinstance(m, dict)
            ),
            key=lambda x: json.dumps(x, sort_keys=True),
        ),
        "networks": [
            {
                "name_hash": _digest(str(name)),
                "network_id_hash": _digest(str(data.get("NetworkID"))),
                "endpoint_id_hash": _digest(str(data.get("EndpointID"))),
            }
            for name, data in sorted(
                ((item.get("NetworkSettings") or {}).get("Networks") or {}).items()
            )
            if isinstance(data, dict)
        ],
        "published_port_count": len(item.get("NetworkSettings", {}).get("Ports", {}) or {}),
        "ownership": _ownership(name, labels, "container"),
    }
    runtime = {
        "id": _digest(str(item.get("Id"))),
        "status": state.get("Status"),
        "running": state.get("Running"),
        "paused": state.get("Paused"),
        "restarting": state.get("Restarting"),
        "dead": state.get("Dead"),
        "exit_code": state.get("ExitCode"),
        "health": (state.get("Health") or {}).get("Status")
        if isinstance(state.get("Health"), dict)
        else None,
    }
    return {"stable": stable, "runtime": runtime}


def _network(item: dict[str, Any]) -> dict[str, Any]:
    name = str(item.get("Name", ""))
    labels = _labels(item.get("Labels"))
    stable = {
        "identity": _digest(str(item.get("Id"))),
        "name": name if name == TASK_PROJECT + "_mayak-internal" else _digest(name),
        "driver": item.get("Driver"),
        "scope": item.get("Scope"),
        "internal": item.get("Internal"),
        "attachable": item.get("Attachable"),
        "ingress": item.get("Ingress"),
        "labels": _safe_labels(labels),
        "ipam_hash": _digest(item.get("IPAM", {})),
        "attachment_count": len(item.get("Containers") or {}),
        "attachment_hashes": sorted(_digest(str(x)) for x in (item.get("Containers") or {})),
        "ownership": _ownership(name, labels, "network"),
    }
    return {"stable": stable}


def _volume(item: dict[str, Any]) -> dict[str, Any]:
    name = str(item.get("Name", ""))
    labels = _labels(item.get("Labels"))
    options = item.get("Options") or {}
    stable = {
        "identity": _digest(name),
        "name": _digest(name),
        "driver": item.get("Driver"),
        "labels": _safe_labels(labels),
        "options": [[_digest(str(k)), _digest(str(v))] for k, v in sorted(options.items())],
        "scope": item.get("Scope"),
        "ownership": _ownership(name, labels, "volume"),
    }
    return {"stable": stable}


def _canonical(payload: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "schema_version",
        "source_host_safe_identity",
        "docker_server_safe_identity",
        "host_boot_instance_safe_identity",
        "docker_endpoint_identity_schema",
        "docker_server_safe_metadata",
        "container_records",
        "network_records",
        "volume_records",
        "apm_postgres_present",
        "task_owned_resource_records",
        "unresolved_resource_records",
        "collection_complete",
        "collection_errors",
        "redaction_passed",
    )
    return {k: payload[k] for k in keys}


def collect_snapshot(phase: str, sequence: int, *, gateway: GatewayAuthority) -> dict[str, Any]:
    try:
        host, boot = _host_identity(), _boot_identity()
        endpoint_schema, daemon, server_metadata = _endpoint_identity(gateway)
        all_records = {
            kind: [
                ({"container": _container, "network": _network, "volume": _volume}[kind])(
                    _inspect(gateway, kind, ident)
                )
                for ident in _enumerate(gateway, kind)
            ]
            for kind in ("container", "network", "volume")
        }
        records = {
            "containers": sorted(all_records["container"], key=lambda x: x["stable"]["id"]),
            "networks": sorted(all_records["network"], key=lambda x: x["stable"]["identity"]),
            "volumes": sorted(all_records["volume"], key=lambda x: x["stable"]["identity"]),
        }
        task = {
            k: [x for x in v if x["stable"]["ownership"] == "TASK_OWNED"]
            for k, v in records.items()
        }
        unresolved = {
            k: [x for x in v if x["stable"]["ownership"] == "UNRESOLVED"]
            for k, v in records.items()
        }
        foreign = {
            k: [x for x in v if x["stable"]["ownership"] == "FOREIGN"] for k, v in records.items()
        }
        result = {
            "schema_version": SCHEMA_VERSION,
            "capture_phase": phase,
            "collector_implementation_id": COLLECTOR_ID,
            "source_host_safe_identity": host,
            "docker_server_safe_identity": daemon,
            "host_boot_instance_safe_identity": boot,
            "docker_endpoint_identity_schema": endpoint_schema,
            "docker_server_safe_metadata": server_metadata,
            "capture_monotonic_sequence": sequence,
            "container_records": foreign["containers"],
            "network_records": foreign["networks"],
            "volume_records": foreign["volumes"],
            "apm_postgres_present": any(
                x["stable"].get("is_apm_postgres") is True for x in foreign["containers"]
            ),
            "task_owned_resource_records": task,
            "unresolved_resource_records": unresolved,
            "collection_complete": True,
            "collection_errors": [],
            "redaction_passed": False,
        }
        validate_safe_value(result)
        result["redaction_passed"] = True
        result["canonical_serialization_digest"] = _digest(_canonical(result))
        return result
    except (
        OSError,
        subprocess.SubprocessError,
        ValueError,
        json.JSONDecodeError,
        CollectionFailure,
    ) as exc:
        return {
            "schema_version": SCHEMA_VERSION,
            "capture_phase": phase,
            "collector_implementation_id": COLLECTOR_ID,
            "capture_monotonic_sequence": sequence,
            "source_host_safe_identity": None,
            "docker_server_safe_identity": None,
            "host_boot_instance_safe_identity": None,
            "docker_endpoint_identity_schema": None,
            "docker_server_safe_metadata": {},
            "collection_complete": False,
            "collection_errors": [type(exc).__name__],
            "redaction_passed": False,
            "container_records": [],
            "network_records": [],
            "volume_records": [],
            "task_owned_resource_records": {"containers": [], "networks": [], "volumes": []},
            "unresolved_resource_records": {"containers": [], "networks": [], "volumes": []},
            "canonical_serialization_digest": "",
        }


def classify_delta(before: dict[str, Any], after: dict[str, Any]) -> str:
    if not before.get("collection_complete") or not after.get("collection_complete"):
        return "SNAPSHOT_INCOMPLETE"
    if before.get("source_host_safe_identity") != after.get("source_host_safe_identity"):
        return "HOST_IDENTITY_CHANGED"
    if before.get("docker_server_safe_identity") != after.get("docker_server_safe_identity"):
        return "DOCKER_DAEMON_IDENTITY_CHANGED"
    if any(
        before.get("unresolved_resource_records", {}).get(k)
        or after.get("unresolved_resource_records", {}).get(k)
        for k in ("containers", "networks", "volumes")
    ):
        return "UNRESOLVED_RESOURCE_PRESENT"
    for kind, added, removed, changed in (
        (
            "container_records",
            "FOREIGN_CONTAINER_ADDED",
            "FOREIGN_CONTAINER_REMOVED",
            "FOREIGN_CONTAINER_STRUCTURE_CHANGED",
        ),
        (
            "network_records",
            "FOREIGN_NETWORK_ADDED",
            "FOREIGN_NETWORK_REMOVED",
            "FOREIGN_NETWORK_STRUCTURE_CHANGED",
        ),
        (
            "volume_records",
            "FOREIGN_VOLUME_ADDED",
            "FOREIGN_VOLUME_REMOVED",
            "FOREIGN_VOLUME_STRUCTURE_CHANGED",
        ),
    ):
        left, right = before.get(kind, []), after.get(kind, [])

        def identity(x: dict[str, Any]) -> str:
            stable = x.get("stable", {})
            return str(stable.get("id") or stable.get("identity") or stable.get("name"))

        li = {identity(x): x for x in left}
        ri = {identity(x): x for x in right}
        if len(left) != len(li) or len(right) != len(ri):
            return "DUPLICATE_RESOURCE_IDENTITY"
        if sorted(li) != sorted(ri):
            return added if len(ri) > len(li) else removed
        if [li[k].get("stable") for k in sorted(li)] != [ri[k].get("stable") for k in sorted(ri)]:
            return (
                "FOREIGN_STRUCTURE_CHANGED"
                if not before.get("source_host_safe_identity")
                else changed
            )

    def ordered_runtime(value: dict[str, Any]) -> list[dict[str, Any]]:
        return [
            {"runtime": x.get("runtime")}
            for x in sorted(value.get("container_records", []), key=lambda y: identity(y))
        ]

    if ordered_runtime(before) != ordered_runtime(after):
        return (
            "FOREIGN_RUNTIME_STATE_CHANGED"
            if not before.get("source_host_safe_identity")
            else "FOREIGN_CONTAINER_RUNTIME_CHANGED"
        )
    return "NO_CHANGE"


ASSERTED_STAGE56_FIELDS_ABSENT = True
ASSERTED_STAGE57_FIELDS_ABSENT = True
LEGACY_RAW_FOREIGN_PARSER_ABSENT = True
SINGLE_FOREIGN_EVIDENCE_AUTHORITY_PRESENT = True
