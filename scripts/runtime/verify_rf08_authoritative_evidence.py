# ruff: noqa: E501,E702
"""Independent RF-08 evidence verifier.

This module intentionally duplicates the small Docker/manifest oracle.  It
does not import the producer, its context helper, parser, constants, or
verdict functions.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import socket
import stat
import struct
import subprocess
import sys
import tarfile
from pathlib import Path, PurePosixPath
from typing import cast

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.runtime.rf08_docker_authority import (
    GatewayAuthority,
    ImageAction,
    ImageOperation,
    ObservationRequest,
    ObservationTemplate,
    PathCapability,
    PathCapabilityKind,
    ResourceKind,
)
from scripts.runtime.rf08_safe_foreign_schema import (
    validate_failure_snapshot,
    validate_safe_value,
    validate_snapshot,
)

TASK_ID = "RF-08-CORRECTIVE-REUSABLE-TASK-SCOPED-ACCEPTANCE-COMPOSE-AUTHORITY-20260801-07"
BASE = "a15b8288fb6640a786aab38ec9b940473b35c377"
TASK_EXPECTED_BASE = "a15b8288fb6640a786aab38ec9b940473b35c377"
PRODUCER_COLLECTOR_ID = "rf08.producer.observed.typed-docker.v3"
COPY_PLAN = (
    ("pyproject.toml", "pyproject.toml"),
    ("uv.lock", "uv.lock"),
    ("README.md", "README.md"),
    ("src", "src"),
    ("alembic.ini", "alembic.ini"),
    ("alembic", "alembic"),
)
STAGES = tuple(
    """PREFLIGHT
CANONICAL_COMPOSE_VALIDATION
IMAGE_INPUT_DIGEST
APPLICATION_IMAGE_RESOLUTION
APPLICATION_IMAGE_BUILD_OR_REUSE
APPLICATION_IMAGE_INSPECT
APPLICATION_IMAGE_PROVENANCE_VERIFY
APPLICATION_IMAGE_ENVIRONMENT_VERIFY
APPLICATION_IMAGE_IMPORT_PROBE
FOREIGN_RESOURCE_SNAPSHOT_BEFORE
SECRET_GENERATION_A_CREATE
SECRET_GENERATION_A_VALIDATE
SECRET_GENERATION_A_ACTIVATE
SECRET_GENERATION_A_POINTER_VERIFY
SECRET_CONSUMER_COPIES_A_VERIFY
SECRET_INTENDED_READABILITY_A
SECRET_UNINTENDED_DENIAL_A
POSTGRES_A_CREATE
POSTGRES_A_HEALTH
DATABASE_BOOTSTRAP_A
MIGRATION_UPGRADE_A
MIGRATION_HEAD_A
APPLICATION_QUERY_A
POSTGRES_A_STOP
POSTGRES_A_RECREATE
POSTGRES_A_RESTART_HEALTH
DATABASE_BOOTSTRAP_RESTART_A
MIGRATION_HEAD_RESTART_A
APPLICATION_QUERY_RESTART_A
SECRET_GENERATION_B_CREATE
SECRET_GENERATION_B_VALIDATE
SECRET_GENERATION_B_ACTIVATE
SECRET_GENERATION_B_POINTER_VERIFY
APPLICATION_AUTH_REJECTION_B
APPLICATION_AUTH_REJECTION_B_CLASSIFY
SECRET_ROLLBACK_A_ACTIVATE
SECRET_ROLLBACK_A_POINTER_VERIFY
POSTGRES_ROLLBACK_A_RECREATE
POSTGRES_ROLLBACK_A_HEALTH
DATABASE_BOOTSTRAP_ROLLBACK_A
MIGRATION_HEAD_ROLLBACK_A
APPLICATION_QUERY_ROLLBACK_A
SECRET_GENERATION_C_CREATE
SECRET_GENERATION_C_VALIDATE
SECRET_GENERATION_C_ACTIVATE
POSTGRES_C_REMOVE_AND_VOLUME_ABSENCE
POSTGRES_C_CREATE
POSTGRES_C_HEALTH
DATABASE_BOOTSTRAP_C
MIGRATION_UPGRADE_C
MIGRATION_HEAD_C
APPLICATION_QUERY_C
ABRUPT_ACTIVATION_D_EXIT_70
SECRET_RECOVERY_D_AND_POINTER_VERIFY
POST_RECOVERY_DATABASE_AND_APPLICATION_PROOF
TASK_CLEANUP_AND_PRIVATE_OUTPUT_REMOVAL
FOREIGN_RESOURCE_EQUALITY_AND_EVIDENCE_VALIDATION""".splitlines()
)
SENSITIVE = re.compile(r"(?i)(-----BEGIN .*PRIVATE KEY-----|postgresql://|password\s*=|dsn\s*=)")
FOREIGN_SCHEMA_VERSION = "ForeignResourceSnapshotV3"
INDEPENDENT_COLLECTOR_ID = "rf08.independent.observed.typed-docker.v3"
TASK_PROJECT = "avito-mayak-rf08-secret-delivery"
TASK_ID = "RF-08-CORRECTIVE-REUSABLE-TASK-SCOPED-ACCEPTANCE-COMPOSE-AUTHORITY-20260801-07"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _safe_digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _identity_hash(prefix: str, value: bytes) -> str:
    return hashlib.sha256(prefix.encode() + b":" + value).hexdigest()


def _host_identity() -> str:
    value = Path("/etc/machine-id").read_bytes().strip()
    if not value or len(value) > 256:
        raise ValueError("host identity unavailable")
    return _identity_hash("rf08-host-v2", value)


def _boot_identity() -> str:
    value = Path("/proc/sys/kernel/random/boot_id").read_bytes().strip()
    if not value or len(value) > 256:
        raise ValueError("boot identity unavailable")
    return _identity_hash("rf08-boot-v1", value)


def _docker_endpoint() -> Path:
    raw = os.environ.get("DOCKER_HOST", "unix:///var/run/docker.sock")
    if not raw.startswith("unix://"):
        raise ValueError("foreign docker endpoint")
    path = raw.removeprefix("unix://")
    if not path.startswith("/") or ".." in Path(path).parts:
        raise ValueError("unsafe docker endpoint")
    endpoint = Path(os.path.abspath(path))
    metadata = endpoint.lstat()
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISSOCK(metadata.st_mode):
        raise ValueError("unsafe docker socket")
    return endpoint


def _endpoint_identity(gateway: GatewayAuthority) -> tuple[str, str, dict[str, str]]:
    endpoint = _docker_endpoint()
    socket_stat = endpoint.stat()
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
        connection.connect(str(endpoint))
        try:
            raw_peer = connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12)
        except OSError:
            raw_peer = b""
    if raw_peer and len(raw_peer) != 12:
        raise ValueError("malformed peer credentials")
    peer: tuple[int, int, int] | None = struct.unpack("3i", raw_peer) if raw_peer else None
    if peer is not None and min(peer) < 0:
        raise ValueError("invalid peer credentials")
    server = gateway.run(
        ObservationRequest(template=ObservationTemplate.DAEMON_VERSION),
        stage="verifier-endpoint-version",
        timeout=30,
    )
    if server.returncode:
        raise ValueError("docker server version failed")
    parsed = json.loads(server.stdout)
    if not isinstance(parsed, dict):
        raise ValueError("docker server envelope malformed")
    safe_server = {
        key: str(parsed[key])
        for key in ("Version", "ApiVersion", "MinAPIVersion", "Os", "Arch", "KernelVersion")
        if parsed.get(key) is not None
    }
    if not safe_server.get("Version"):
        raise ValueError("docker server version absent")
    payload = {
        "schema": "LOCAL_UNIX_DOCKER_ENDPOINT_INSTANCE_V1"
        if peer
        else "LOCAL_UNIX_DOCKER_ENDPOINT_SOCKET_V1",
        "socket": {
            "path": str(endpoint),
            "st_dev": socket_stat.st_dev,
            "st_ino": socket_stat.st_ino,
            "mode": socket_stat.st_mode,
        },
        "boot": _boot_identity(),
        "server": safe_server,
    }
    if peer is not None:
        pid, uid, gid = peer
        try:
            peer_stat = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8")
            close = peer_stat.rfind(")")
            fields = peer_stat[close + 2 :].split() if close >= 0 else []
            executable = Path(f"/proc/{pid}/exe").stat()
        except OSError:
            fields, executable = [], None
        if len(fields) > 19 and fields[19].isdigit() and executable is not None:
            payload["peer"] = {
                "pid": pid,
                "uid": uid,
                "gid": gid,
                "start_time": fields[19],
                "exe_dev": executable.st_dev,
                "exe_ino": executable.st_ino,
            }
        else:
            payload["schema"] = "LOCAL_UNIX_DOCKER_ENDPOINT_SOCKET_V1"
    return str(payload["schema"]), _safe_digest(payload), safe_server


def _independent_snapshot(
    phase: str, sequence: int, *, gateway: GatewayAuthority
) -> dict[str, object]:
    """Independent read-only collector; no producer code or oracle is imported."""
    try:

        def inspect(kind: str, ident: str) -> dict[str, object]:
            result = gateway.run(
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
                stage=f"verifier-inspect-{kind}",
                timeout=30,
            )
            if result.returncode != 0:
                raise RuntimeError("inspect failed")
            value = json.loads(result.stdout)[0]
            if not isinstance(value, dict):
                raise ValueError("inspect shape")
            actual = str(value.get("Id") or value.get("ID") or value.get("Name", "")).lstrip("/")
            name = str(value.get("Name", "")).lstrip("/")
            if actual and not (ident == actual or actual.startswith(ident) or ident == name):
                raise ValueError("inspect identity mismatch")
            return value

        def ids(kind: str) -> list[str]:
            result = gateway.run(
                ObservationRequest(
                    template={
                        "container": ObservationTemplate.CONTAINER_LIST,
                        "network": ObservationTemplate.NETWORK_LIST,
                        "volume": ObservationTemplate.VOLUME_LIST,
                        "image": ObservationTemplate.IMAGE_LIST,
                    }[kind],
                    kind=ResourceKind(kind),
                ),
                stage=f"verifier-enumerate-{kind}",
                timeout=30,
            )
            if result.returncode != 0:
                raise RuntimeError("enumeration failed")
            values = [x.strip() for x in result.stdout.splitlines() if x.strip()]
            if len(values) != len(list(dict.fromkeys(values))):
                raise ValueError("duplicate enumeration")
            return sorted(values)

        def labels(value: object) -> list[list[str]]:
            if not isinstance(value, dict):
                return []
            mapping = value
            return [
                [
                    str(k)
                    if str(k)
                    in {
                        "com.docker.compose.project",
                        "com.docker.compose.service",
                        "com.avito-mayak.technical-id",
                    }
                    else _safe_digest(str(k)),
                    str(v)
                    if str(k)
                    in {
                        "com.docker.compose.project",
                        "com.docker.compose.service",
                        "com.avito-mayak.technical-id",
                    }
                    and str(v)
                    in {
                        TASK_PROJECT,
                        TASK_ID,
                        "mayak-api",
                        "mayak-worker",
                        "mayak-scheduler",
                        "mayak-postgres",
                        "mayak-db-bootstrap",
                        "mayak-migrate",
                    }
                    else _safe_digest(str(v)),
                ]
                for k, v in sorted(mapping.items())
            ]

        def own(name: str, value: object, kind: str) -> str:
            raw = value if isinstance(value, dict) else {}
            project, technical = (
                raw.get("com.docker.compose.project"),
                raw.get("com.avito-mayak.technical-id"),
            )
            if name == "apm-postgres":
                return "FOREIGN"
            task_indicator = project == TASK_PROJECT or name.startswith(TASK_PROJECT)
            if technical != TASK_ID:
                return "UNRESOLVED" if task_indicator else "FOREIGN"
            if kind == "container":
                service = raw.get("com.docker.compose.service")
                exact = (
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
            if task_indicator:
                return "UNRESOLVED"
            return "FOREIGN"

        containers = []
        for ident in ids("container"):
            item = inspect("container", ident)
            name = str(item.get("Name", "")).lstrip("/")
            cfg = item.get("Config", {})
            host = item.get("HostConfig", {})
            state = item.get("State", {})
            raw_labels = cfg.get("Labels", {}) if isinstance(cfg, dict) else {}
            mounts_value = item.get("Mounts")
            mounts = (
                [
                    {
                        "type": m.get("Type"),
                        "destination_hash": _safe_digest(str(m.get("Destination"))),
                        "mode": m.get("Mode"),
                        "rw": m.get("RW"),
                    }
                    for m in mounts_value
                    if isinstance(m, dict)
                ]
                if isinstance(mounts_value, list)
                else []
            )
            attachments = []
            network_settings = item.get("NetworkSettings")
            networks_value = (
                network_settings.get("Networks") if isinstance(network_settings, dict) else None
            )
            for net, data in networks_value.items() if isinstance(networks_value, dict) else ():
                if isinstance(data, dict):
                    attachments.append(
                        {
                            "name_hash": _safe_digest(str(net)),
                            "network_id_hash": _safe_digest(str(data.get("NetworkID"))),
                            "endpoint_id_hash": _safe_digest(str(data.get("EndpointID"))),
                        }
                    )
            stable = {
                "id": _safe_digest(str(item.get("Id"))),
                "image_id_hash": _safe_digest(str(item.get("Image"))),
                "image_reference_hash": _safe_digest(
                    str(cfg.get("Image")) if isinstance(cfg, dict) else ""
                ),
                "labels": labels(raw_labels),
                "restart_policy": host.get("RestartPolicy", {}).get("Name")
                if isinstance(host, dict)
                else None,
                "network_mode": (
                    host.get("NetworkMode")
                    if isinstance(host, dict)
                    and host.get("NetworkMode") in {"host", "none", "bridge", "default"}
                    else _safe_digest(str(host.get("NetworkMode")))
                    if isinstance(host, dict)
                    else None
                ),
                "privileged": host.get("Privileged") if isinstance(host, dict) else None,
                "read_only_rootfs": host.get("ReadonlyRootfs") if isinstance(host, dict) else None,
                "mounts": sorted(mounts, key=lambda x: json.dumps(x, sort_keys=True)),
                "networks": sorted(
                    attachments, key=lambda x: (str(x.get("name")), str(x.get("network_id")))
                ),
                "published_port_count": len(
                    network_settings.get("Ports", {}) if isinstance(network_settings, dict) else {}
                ),
                "ownership": own(name, raw_labels, "container"),
            }
            runtime = {
                "id": _safe_digest(str(item.get("Id"))),
                "status": state.get("Status") if isinstance(state, dict) else None,
                "running": state.get("Running") if isinstance(state, dict) else None,
                "paused": state.get("Paused") if isinstance(state, dict) else None,
                "restarting": state.get("Restarting") if isinstance(state, dict) else None,
                "dead": state.get("Dead") if isinstance(state, dict) else None,
                "exit_code": state.get("ExitCode") if isinstance(state, dict) else None,
                "health": state.get("Health", {}).get("Status")
                if isinstance(state, dict) and isinstance(state.get("Health"), dict)
                else None,
            }
            containers.append(
                {
                    "stable": {
                        "fingerprint": _safe_digest(["container", item.get("Id"), name]),
                        "name": _safe_digest(name),
                        "is_apm_postgres": name == "apm-postgres",
                        **stable,
                    },
                    "runtime": runtime,
                }
            )
        containers.sort(key=lambda x: str(x["stable"].get("id")))
        # Networks and volumes use the same immutable object IDs, labels, and ownership basis.
        networks = []
        for ident in ids("network"):
            item = inspect("network", ident)
            name = str(item.get("Name", ""))
            raw_labels = item.get("Labels", {})
            attached_containers = item.get("Containers")
            networks.append(
                {
                    "stable": {
                        "identity": _safe_digest(str(item.get("Id"))),
                        "name": name
                        if name == TASK_PROJECT + "_mayak-internal"
                        else _safe_digest(name),
                        "driver": item.get("Driver"),
                        "scope": item.get("Scope"),
                        "internal": item.get("Internal"),
                        "attachable": item.get("Attachable"),
                        "ingress": item.get("Ingress"),
                        "labels": labels(raw_labels),
                        "ipam_hash": _safe_digest(item.get("IPAM", {})),
                        "attachment_count": len(attached_containers)
                        if isinstance(attached_containers, dict)
                        else 0,
                        "attachment_hashes": sorted(
                            _safe_digest(str(x)) for x in attached_containers
                        )
                        if isinstance(attached_containers, dict)
                        else [],
                        "ownership": own(name, raw_labels, "network"),
                    }
                }
            )
        networks.sort(key=lambda x: str(x["stable"].get("identity")))
        volumes = []
        for ident in ids("volume"):
            item = inspect("volume", ident)
            name = str(item.get("Name", ""))
            raw_labels = item.get("Labels", {})
            options_value = item.get("Options")
            options = options_value if isinstance(options_value, dict) else {}
            volumes.append(
                {
                    "stable": {
                        "identity": _safe_digest(name),
                        "name": _safe_digest(name),
                        "driver": item.get("Driver"),
                        "labels": labels(raw_labels),
                        "options": [
                            [_safe_digest(str(k)), _safe_digest(str(v))]
                            for k, v in sorted(options.items())
                        ],
                        "scope": item.get("Scope"),
                        "ownership": own(name, raw_labels, "volume"),
                    }
                }
            )
        volumes.sort(key=lambda x: str(x["stable"].get("name")))
        foreign = {
            "containers": [x for x in containers if x["stable"]["ownership"] == "FOREIGN"],
            "networks": [x for x in networks if x["stable"]["ownership"] == "FOREIGN"],
            "volumes": [x for x in volumes if x["stable"]["ownership"] == "FOREIGN"],
        }
        task = {
            kind: [x for x in values if x["stable"]["ownership"] == "TASK_OWNED"]
            for kind, values in {
                "containers": containers,
                "networks": networks,
                "volumes": volumes,
            }.items()
        }
        unresolved = {
            kind: [x for x in values if x["stable"]["ownership"] == "UNRESOLVED"]
            for kind, values in {
                "containers": containers,
                "networks": networks,
                "volumes": volumes,
            }.items()
        }
        host = _host_identity()
        boot = _boot_identity()
        endpoint_schema, endpoint, server_metadata = _endpoint_identity(gateway)
        result = {
            "schema_version": FOREIGN_SCHEMA_VERSION,
            "capture_phase": phase,
            "collector_implementation_id": INDEPENDENT_COLLECTOR_ID,
            "source_host_safe_identity": host,
            "host_boot_instance_safe_identity": boot,
            "docker_server_safe_identity": endpoint,
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
        canonical = {
            key: result[key]
            for key in (
                "schema_version",
                "source_host_safe_identity",
                "host_boot_instance_safe_identity",
                "docker_server_safe_identity",
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
        }
        result["canonical_serialization_digest"] = _safe_digest(canonical)
        return result
    except (
        OSError,
        subprocess.SubprocessError,
        ValueError,
        json.JSONDecodeError,
        RuntimeError,
    ) as exc:
        return {
            "schema_version": FOREIGN_SCHEMA_VERSION,
            "collector_implementation_id": INDEPENDENT_COLLECTOR_ID,
            "capture_phase": phase,
            "capture_monotonic_sequence": sequence,
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


def _relative(value: str) -> str:
    path = PurePosixPath(value)
    if not value or path.is_absolute() or ".." in path.parts:
        raise ValueError("unsafe path")
    return path.as_posix()


def _clean_context(
    repo: Path, root: Path, run_id: str, *, gateway: GatewayAuthority | None = None
) -> tuple[Path, str]:
    run_root = root / run_id
    source = run_root / "source"
    run_root.mkdir(mode=0o700, parents=True)
    archive = run_root / "source.tar"
    with archive.open("wb") as stream:
        subprocess.run(
            ["git", "-C", str(repo), "archive", "--format=tar", "HEAD"],
            stdout=stream,
            stderr=subprocess.DEVNULL,
            check=True,
        )
    archive_sha = _sha(archive)
    source.mkdir(mode=0o700)
    with tarfile.open(archive) as tar:
        for member in tar.getmembers():
            rel = _relative(member.name)
            target = source / rel
            if member.issym() or member.islnk() or member.isdev() or member.isfifo():
                raise ValueError("unsafe Git archive member")
            if member.isdir():
                target.mkdir(mode=0o700, parents=True, exist_ok=True)
            elif member.isfile():
                target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
                inp = tar.extractfile(member)
                if inp is None:
                    raise ValueError("archive member unavailable")
                with inp, target.open("wb") as out:
                    shutil.copyfileobj(inp, out)
            else:
                raise ValueError("unsupported Git archive member")
    archive.unlink()
    return source, archive_sha


def _docker_manifest(
    source: Path, root: Path, run_id: str, *, gateway: GatewayAuthority
) -> tuple[list[dict[str, str]], dict[str, str]]:
    run_root = root / run_id
    output = run_root / "output"
    inspector = run_root / "inspector.Dockerfile"
    inspector.write_text(
        "FROM scratch\n"
        "COPY pyproject.toml uv.lock README.md /effective/\n"
        "COPY src /effective/src\n"
        "COPY alembic.ini /effective/alembic.ini\n"
        "COPY alembic /effective/alembic\n",
        encoding="utf-8",
    )
    output.mkdir(mode=0o700)
    capability = gateway.issue(
        ImageAction(
            operation=ImageOperation.BUILDX_MANIFEST,
            context=PathCapability.from_path(
                source, kind=PathCapabilityKind.DIRECTORY, require_exists=True
            ),
            dockerfile=PathCapability.from_path(
                inspector, kind=PathCapabilityKind.FILE, require_exists=True
            ),
            output=PathCapability.from_path(
                output, kind=PathCapabilityKind.DIRECTORY, require_exists=False
            ),
        ),
        stage="verifier-buildx-build",
    )
    gateway.execute(
        capability,
        stage="verifier-buildx-build",
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
        timeout=180,
    )
    effective = output / "effective"
    if not effective.is_dir():
        raise ValueError("effective Docker output missing")
    paths = sorted(p for p in effective.rglob("*") if p.is_file())
    rows = [
        {"path": _relative(p.relative_to(effective).as_posix()), "sha256": _sha(p)} for p in paths
    ]
    rows.sort(key=lambda item: item["path"])
    if [x["path"] for x in rows] != sorted({x["path"] for x in rows}):
        raise ValueError("manifest is not sorted and unique")
    return rows, {
        "inspector_sha256": _sha(inspector),
        "manifest_sha256": hashlib.sha256(_canonical(rows)).hexdigest(),
    }


def _canonical(manifest: list[dict[str, str]]) -> bytes:
    return json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()


def _digest(source: Path, manifest: list[dict[str, str]], tree_identity: str) -> str:
    payload = {
        "schema_version": "rf08-docker-native-context-v1",
        "expected_base_tree_identity": tree_identity,
        "dockerfile_sha256": _sha(source / "Dockerfile"),
        "dockerignore_sha256": _sha(source / ".dockerignore"),
        "normalized_copy_plan": [{"source": a, "destination": b} for a, b in COPY_PLAN],
        "effective_file_manifest": manifest,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _stage(document: dict[str, object], name: str) -> dict[str, object]:
    stages = document["stages"]
    assert isinstance(stages, list)
    row = next((x for x in stages if isinstance(x, dict) and x.get("name") == name), None)
    if not isinstance(row, dict) or not isinstance(row.get("evidence"), dict):
        raise ValueError(f"stage evidence missing: {name}")
    return row


def _check_stage_ids(row: dict[str, object], name: str) -> None:
    for key in ("operation_id", "parser_id", "oracle_id"):
        value = row.get(key)
        if not isinstance(value, str) or not value or any(c.isspace() for c in value):
            raise ValueError(f"invalid {key}: {name}")
    if name not in {
        "IMAGE_INPUT_DIGEST",
        "SECRET_RECOVERY_D_AND_POINTER_VERIFY",
        "POST_RECOVERY_DATABASE_AND_APPLICATION_PROOF",
    }:
        evidence = row["evidence"]
        assert isinstance(evidence, dict)
        if (
            name.lower() not in str(row["operation_id"]).lower()
            and not (
                name.startswith("APPLICATION_AUTH_REJECTION_B")
                and str(row["operation_id"]).startswith("rf08.application_auth_rejection_b")
            )
            and not str(row["operation_id"]).startswith(("secret.", "pointer."))
        ):
            raise ValueError(f"operation id does not identify stage: {name}")


def _verify_stage55(evidence: dict[str, object]) -> None:
    exact = {
        "observed": "POST_RECOVERY_DATABASE_AND_APPLICATION_PROOF",
        "handoff_accepted": True,
        "bootstrap_envelope": True,
        "bootstrap_outcome": "RF09_BOOTSTRAP_SUCCESS",
        "observed_migration_head": "RF12_MANUAL_GRANT",
        "application_marker": "APPLICATION_QUERY_OK",
        "adapter_exit": 0,
    }
    if any(evidence.get(k) != v for k, v in exact.items()):
        raise ValueError("stage 55 semantic contract failed")
    expected_types = [
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
    ]
    if evidence.get("typed_subprotocol") != expected_types:
        raise ValueError("stage 55 typed subprotocol mismatch")
    adapter = evidence.get("adapter_result")
    if not isinstance(adapter, dict):
        raise ValueError("stage 55 adapter result missing")
    required = {
        "exit_code": 0,
        "bootstrap_outcome": "RF09_BOOTSTRAP_SUCCESS",
        "invariant_code": None,
        "last_rf09_operation": "RF09_COMMIT",
        "connection_attempted": True,
        "connected": True,
        "committed": True,
        "rolled_back": False,
        "migration_role_valid": True,
        "application_role_valid": True,
        "schema_owner_valid": True,
        "application_schema_create": False,
        "current_object_grants": False,
    }
    if any(adapter.get(k) != v for k, v in required.items()):
        raise ValueError("stage 55 adapter semantics mismatch")


def _verify_stage56(evidence: dict[str, object]) -> None:
    observations = evidence.get("stage56_observations")
    if not isinstance(observations, dict):
        raise ValueError("stage 56 observations missing")
    required = {
        "task_container_count",
        "task_network_count",
        "task_volume_count",
        "unresolved_count",
        "private_output_count",
        "json_log_count",
        "override_count",
        "context_directory_count",
        "runtime_compose_count",
        "temporary_validation_resource_count",
        "authorized_mutation_count",
        "executed_mutation_count",
        "foreign_target_mutation_count",
        "unresolved_target_mutation_count",
        "unscoped_mutation_count",
        "broad_mutation_count",
    }
    if set(observations) != required or any(
        not isinstance(observations[key], int) or observations[key] < 0 for key in required
    ):
        raise ValueError("stage 56 observation shape")
    if (
        evidence.get("observed") != "task_owned_cleanup_complete"
        or evidence.get("cleanup_observed") is not True
        or evidence.get("cleanup_exit") != 0
        or evidence.get("foreign_deletion") is not False
        or any(
            observations[key] != 0
            for key in (
                "task_container_count",
                "task_network_count",
                "task_volume_count",
                "unresolved_count",
                "private_output_count",
                "json_log_count",
                "override_count",
                "context_directory_count",
                "runtime_compose_count",
                "temporary_validation_resource_count",
                "foreign_target_mutation_count",
                "unresolved_target_mutation_count",
                "unscoped_mutation_count",
                "broad_mutation_count",
            )
        )
        or observations["authorized_mutation_count"] != observations["executed_mutation_count"]
    ):
        raise ValueError("stage 56 observed cleanup failed")


def _verify_stage57(evidence: dict[str, object]) -> None:
    records = evidence.get("foreign_records")
    if not isinstance(records, dict):
        records = {
            "producer_before": evidence.get("producer_before_snapshot"),
            "independent_before": evidence.get("independent_before_snapshot"),
            "producer_after": evidence.get("producer_after_snapshot"),
            "independent_after": evidence.get("independent_after_snapshot"),
        }
    if not isinstance(records, dict):
        raise ValueError("foreign records missing")
    required = ("producer_before", "independent_before", "producer_after", "independent_after")
    if any(not isinstance(records.get(k), dict) for k in required):
        raise ValueError("foreign record shape")
    before = cast(dict[str, object], records["producer_before"])
    before_i = cast(dict[str, object], records["independent_before"])
    after = cast(dict[str, object], records["producer_after"])
    after_i = cast(dict[str, object], records["independent_after"])
    for label, snapshot, collector_id in (
        ("producer_before", before, PRODUCER_COLLECTOR_ID),
        ("independent_before", before_i, INDEPENDENT_COLLECTOR_ID),
        ("producer_after", after, PRODUCER_COLLECTOR_ID),
        ("independent_after", after_i, INDEPENDENT_COLLECTOR_ID),
    ):
        if snapshot.get("collection_complete") is True:
            validate_snapshot(snapshot, collector_id=collector_id)
        else:
            validate_failure_snapshot(snapshot, collector_id=collector_id)
        validate_safe_value(snapshot)
        canonical_keys = (
            "schema_version",
            "source_host_safe_identity",
            "host_boot_instance_safe_identity",
            "docker_server_safe_identity",
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
        if snapshot.get("collection_complete") is True:
            expected_digest = _safe_digest({key: snapshot.get(key) for key in canonical_keys})
            if snapshot.get("canonical_serialization_digest") != expected_digest:
                raise ValueError("safe record recomputation failed")
    if before.get("collector_implementation_id") == before_i.get("collector_implementation_id"):
        raise ValueError("collector identity aliasing")
    if after.get("collector_implementation_id") == after_i.get("collector_implementation_id"):
        raise ValueError("collector identity aliasing")
    if before.get("canonical_serialization_digest") != before_i.get(
        "canonical_serialization_digest"
    ) or after.get("canonical_serialization_digest") != after_i.get(
        "canonical_serialization_digest"
    ):
        raise ValueError("collector parity failed")
    if (
        before.get("source_host_safe_identity") != after.get("source_host_safe_identity")
        or before.get("host_boot_instance_safe_identity")
        != after.get("host_boot_instance_safe_identity")
        or before.get("docker_server_safe_identity") != after.get("docker_server_safe_identity")
    ):
        raise ValueError("identity stability failed")
    if (
        before.get("container_records") != after.get("container_records")
        or before.get("network_records") != after.get("network_records")
        or before.get("volume_records") != after.get("volume_records")
    ):
        raise ValueError("foreign delta failed")
    ledger = evidence.get("mutation_ledger")
    if not isinstance(ledger, list):
        raise ValueError("mutation ledger failed")
    if not ledger:
        raise ValueError("mutation ledger failed")
    auth = [
        item
        for item in ledger
        if isinstance(item, dict) and item.get("execution_result_sequence") is None
    ]
    results = [
        item
        for item in ledger
        if isinstance(item, dict) and item.get("execution_result_sequence") is not None
    ]
    if len(auth) != len(results) or any(
        a.get("authorization_sequence") != r.get("authorization_sequence")
        for a, r in zip(auth, results)
    ):
        raise ValueError("mutation ledger parity failed")
    if any(
        item.get("planned_ownership") != "TASK_OWNED" for item in ledger if isinstance(item, dict)
    ):
        raise ValueError("foreign mutation target")

    def record_list(snapshot: dict[str, object], key: str) -> list[object]:
        value = snapshot.get(key)
        if not isinstance(value, list):
            raise ValueError("foreign record list missing")
        return value

    after_containers = record_list(after, "container_records")
    after_networks = record_list(after, "network_records")
    after_volumes = record_list(after, "volume_records")
    expected_summary = {
        "foreign_before_collectors_equal": True,
        "foreign_after_collectors_equal": True,
        "foreign_before_producer_digest": before.get("canonical_serialization_digest"),
        "foreign_before_independent_digest": before_i.get("canonical_serialization_digest"),
        "foreign_after_producer_digest": after.get("canonical_serialization_digest"),
        "foreign_after_independent_digest": after_i.get("canonical_serialization_digest"),
        "foreign_delta_classification": "NO_CHANGE",
        "foreign_container_count": len(after_containers),
        "foreign_network_count": len(after_networks),
        "foreign_volume_count": len(after_volumes),
        "foreign_target_mutation_command_count": 0,
    }
    if any(evidence.get(key) != value for key, value in expected_summary.items()):
        raise ValueError("foreign summary recomputation failed")


def _verify_sanitation_record(document: dict[str, object]) -> None:
    record = document.get("replay_namespace_sanitation")
    if not isinstance(record, dict):
        raise ValueError("sanitation record missing")
    required_hashes = record.get("required_name_absence_hashes")
    if not isinstance(required_hashes, list) or not required_hashes:
        raise ValueError("sanitation required-name proof missing")
    if record.get("required_name_absence_digest") != _safe_digest(required_hashes):
        raise ValueError("sanitation required-name digest mismatch")
    expected = _safe_digest({k: record.get(k) for k in record if k != "record_digest"})
    if record.get("record_digest") != expected:
        raise ValueError("sanitation record digest mismatch")
    if record.get("schema_version") != "rf08-replay-namespace-sanitation-v1":
        raise ValueError("sanitation schema mismatch")
    if record.get("technical_id") != TASK_ID:
        raise ValueError("sanitation technical id mismatch")
    if (
        record.get("foreign_before_equal") is not True
        or record.get("foreign_after_equal") is not True
    ):
        raise ValueError("sanitation foreign equality failed")
    if (
        record.get("task_container_count_after") != 0
        or record.get("task_network_count_after") != 0
        or record.get("task_volume_count_after") != 0
    ):
        raise ValueError("sanitation task namespace not empty")
    if (
        record.get("unresolved_container_count_after") != 0
        or record.get("unresolved_network_count_after") != 0
        or record.get("unresolved_volume_count_after") != 0
    ):
        raise ValueError("sanitation unresolved namespace not empty")
    if record.get("verified_absence") is not True:
        raise ValueError("sanitation absence not proven")


def verify_evidence(
    evidence_path: Path, source_tree: Path, *, verifier_gateway: GatewayAuthority
) -> dict[str, object]:
    document = json.loads(evidence_path.read_text(encoding="utf-8"))
    candidate_source_sha = subprocess.check_output(
        ["git", "-C", str(source_tree), "rev-parse", "HEAD"], text=True
    ).strip()
    if (
        document.get("technical_id") != TASK_ID
        or document.get("task_expected_base") != TASK_EXPECTED_BASE
        or document.get("runtime_image_input_base") != BASE
    ):
        raise ValueError("identity or base mismatch")
    if document.get("required_stage_order") != list(STAGES) or len(STAGES) != 57:
        raise ValueError("exact stage contract mismatch")
    stages = document.get("stages")
    if not isinstance(stages, list) or len(stages) != 57:
        raise ValueError("stage rows missing")
    for expected, row in zip(STAGES, stages):
        if not isinstance(row, dict) or row.get("name") != expected or row.get("status") != "PASS":
            raise ValueError(f"invalid row: {expected}")
        if not isinstance(row.get("evidence"), dict) or row["evidence"].get("observed") not in (
            expected,
            expected,
            "generation_metadata",
            "bounded_command_output",
            "task_owned_cleanup_complete",
            "VOLUME_ABSENCE",
            "POSTGRESQL_AUTHENTICATION_REJECTED_SQLSTATE_28P01",
            "CLIENT_CONNECTION_ATTEMPT_FAILED_PENDING_SERVER_CLASSIFICATION",
            "permission_denied",
            "RF09_BOOTSTRAP_SUCCESS",
        ):
            raise ValueError(f"stage-specific evidence missing: {expected}")
        _check_stage_ids(row, expected)
    _verify_sanitation_record(document)
    hashes = document.get("production_tree_hashes")
    if not isinstance(hashes, dict):
        raise ValueError("source hashes missing")
    for relative, expected in hashes.items():
        if (
            not isinstance(relative, str)
            or not isinstance(expected, str)
            or _sha(source_tree / relative) != expected
        ):
            raise ValueError(f"source hash mismatch: {relative}")
    runtime_root = Path("/opt/avito-mayak-runtime/rf08-secret-delivery/independent-build-context")
    run_id = "verify-" + hashlib.sha256(evidence_path.read_bytes()).hexdigest()[:16]
    source, archive_sha = _clean_context(
        source_tree, runtime_root, run_id, gateway=verifier_gateway
    )
    try:
        manifest, export = _docker_manifest(source, runtime_root, run_id, gateway=verifier_gateway)
        expected_manifest = document.get("docker_native_effective_manifest")
        if manifest != expected_manifest or document.get("build_input_manifest") != manifest:
            raise ValueError("independent manifest mismatch")
        if any(
            "__pycache__" in x["path"] or x["path"].endswith((".pyc", ".pyo")) for x in manifest
        ):
            raise ValueError("ignored/generated path in manifest")
        tree_identity = subprocess.check_output(
            ["git", "-C", str(source_tree), "rev-parse", "HEAD^{tree}"], text=True
        ).strip()
        digest = _digest(source, manifest, tree_identity)
        if any(
            document.get(k) != digest
            for k in (
                "build_input_digest",
                "producer_recomputed_digest",
                "independent_recomputed_digest",
            )
        ):
            raise ValueError("independent digest mismatch")
        image_stage = _stage(document, "IMAGE_INPUT_DIGEST")["evidence"]
        if (
            not isinstance(image_stage, dict)
            or image_stage.get("build_input_digest") != digest
            or image_stage.get("manifest") != manifest
        ):
            raise ValueError("IMAGE_INPUT_DIGEST evidence mismatch")
        if (
            document.get("producer_independent_manifest_equal") is not True
            or document.get("producer_independent_digest_equal") is not True
        ):
            raise ValueError("producer/independent equality missing")
        if (
            document.get("expected_base_tree_identity") != tree_identity
            or document.get("docker_native_effective_manifest_digest") != export["manifest_sha256"]
        ):
            raise ValueError("context identity mismatch")
        if (
            document.get("excluded_path_count") != 0
            or document.get("untracked_input_count") != 0
            or document.get("dirty_input_count") != 0
        ):
            raise ValueError("context exclusion counts failed")
        if not isinstance(document.get("stage55_semantic_verification"), dict):
            raise ValueError("stage 55 semantic observations missing")
        cleanup_stage = cast(
            dict[str, object],
            _stage(document, "TASK_CLEANUP_AND_PRIVATE_OUTPUT_REMOVAL")["evidence"],
        )
        if document.get("stage56_semantic_verification") != cleanup_stage.get(
            "stage56_observations"
        ):
            raise ValueError("stage 56 semantic observations mismatch")
        if document.get("stage57_semantic_verification") != {
            "derived_delta": "NO_CHANGE",
            "producer_after_collectors_equal": True,
        }:
            raise ValueError("stage 57 semantic observations mismatch")
        _verify_stage55(
            cast(
                dict[str, object],
                _stage(document, "POST_RECOVERY_DATABASE_AND_APPLICATION_PROOF")["evidence"],
            )
        )
        _verify_stage56(
            cast(
                dict[str, object],
                _stage(document, "TASK_CLEANUP_AND_PRIVATE_OUTPUT_REMOVAL")["evidence"],
            )
        )
        stage57 = dict(
            cast(
                dict[str, object],
                _stage(document, "FOREIGN_RESOURCE_EQUALITY_AND_EVIDENCE_VALIDATION")["evidence"],
            )
        )
        foreign_records = document.get("foreign_records")
        if isinstance(foreign_records, dict):
            stage57.setdefault("foreign_records", foreign_records)
            stage57.setdefault("producer_before_snapshot", foreign_records.get("producer_before"))
            stage57.setdefault(
                "independent_before_snapshot", foreign_records.get("independent_before")
            )
            stage57.setdefault("producer_after_snapshot", foreign_records.get("producer_after"))
            stage57.setdefault(
                "independent_after_snapshot", foreign_records.get("independent_after")
            )
        stage10 = cast(
            dict[str, object], _stage(document, "FOREIGN_RESOURCE_SNAPSHOT_BEFORE")["evidence"]
        )
        stage57.setdefault("producer_before_snapshot", stage10.get("producer_before_snapshot"))
        stage57.setdefault(
            "independent_before_snapshot", stage10.get("independent_before_snapshot")
        )
        _verify_stage57(stage57)
        if (
            not document.get("image_id")
            or document.get("verdict") != "PUBLISHED_FOR_CHATGPT_REVIEW"
        ):
            raise ValueError("image or verdict missing")
        encoded = json.dumps(document, sort_keys=True)
        if SENSITIVE.search(encoded):
            raise ValueError("prohibited sensitive material")
        return {
            "verified": True,
            "source_identity_mode": "affected-production-paths",
            "verification_source_sha": candidate_source_sha,
            "stage_count": 57,
            "manifest_files_checked": len(manifest),
            "archive_sha256": archive_sha,
            "manifest_digest": export["manifest_sha256"],
            "stage55": "PASS",
            "stage56": "PASS",
            "stage57": "PASS",
        }
    finally:
        shutil.rmtree(runtime_root / run_id, ignore_errors=True)


def main(args: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", action="store_true")
    parser.add_argument("--phase", default="verification")
    parser.add_argument("--sequence", type=int, default=1)
    parser.add_argument("evidence", type=Path, nargs="?")
    parser.add_argument("source_tree", type=Path, nargs="?")
    parsed = parser.parse_args(args)
    if parsed.snapshot:
        gateway = GatewayAuthority()
        print(
            json.dumps(
                _independent_snapshot(parsed.phase, parsed.sequence, gateway=gateway),
                sort_keys=True,
                separators=(",", ":"),
            )
        )
        return 0
    if parsed.evidence is None or parsed.source_tree is None:
        parser.error("evidence and source_tree are required unless --snapshot is used")
    verifier_gateway = GatewayAuthority()
    print(
        json.dumps(
            verify_evidence(parsed.evidence, parsed.source_tree, verifier_gateway=verifier_gateway),
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
