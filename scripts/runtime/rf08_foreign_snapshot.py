"""Producer-side typed Docker control-plane snapshots for RF-08.

This module never reads container files, mounts, volumes, environments, or logs.
Only Docker object metadata needed for safe ownership and equality is collected.
The verifier deliberately contains an independent implementation.
"""

# ruff: noqa: E501,E702

from __future__ import annotations

import hashlib
import json
import subprocess
from typing import Any, Final

SCHEMA_VERSION: Final = "ForeignResourceSnapshotV2"
COLLECTOR_ID: Final = "rf08.producer.typed-docker-control-plane.v2"
TASK_PROJECT: Final = "avito-mayak-rf08-secret-delivery"
TASK_ID: Final = "RF-08-CORRECTIVE-NONROOT-FILE-SECRET-DELIVERY-20260729-01"


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _run(args: list[str]) -> list[dict[str, Any]]:
    result = subprocess.run(["docker", *args], capture_output=True, check=False, timeout=30)
    if result.returncode != 0:
        raise RuntimeError("docker control-plane command failed")
    value = json.loads(result.stdout)
    if not isinstance(value, list):
        raise ValueError("docker control-plane result is not a list")
    return [item for item in value if isinstance(item, dict)]


def _labels(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    return {str(k): str(v) for k, v in sorted(value.items())}


def _ownership(name: str, labels: dict[str, str], kind: str) -> str:
    project = labels.get("com.docker.compose.project")
    technical = labels.get("com.avito-mayak.technical-id")
    prefix = f"{TASK_PROJECT}-"
    if technical is not None and technical != TASK_ID:
        return "UNRESOLVED" if project == TASK_PROJECT or name.startswith(prefix) else "FOREIGN"
    if project == TASK_PROJECT and name.startswith(prefix):
        return "TASK_OWNED"
    if project == TASK_PROJECT or name.startswith(prefix):
        return "UNRESOLVED"
    return "FOREIGN"


def _safe_labels(labels: dict[str, str]) -> list[list[str]]:
    return [[key, value if key in {"com.docker.compose.project", "com.avito-mayak.technical-id"} else _digest(value)] for key, value in labels.items()]


def _container(item: dict[str, Any]) -> dict[str, Any]:
    name = str(item.get("Name", "")).lstrip("/")
    labels = _labels(item.get("Config", {}).get("Labels"))
    mounts = []
    for mount in item.get("Mounts", []):
        if isinstance(mount, dict):
            mounts.append({"type": mount.get("Type"), "destination": mount.get("Destination"), "mode": mount.get("Mode"), "rw": mount.get("RW")})
    networks = item.get("NetworkSettings", {}).get("Networks", {})
    attachments = []
    if isinstance(networks, dict):
        for net, data in networks.items():
            data = data if isinstance(data, dict) else {}
            attachments.append({"name": str(net), "network_id": data.get("NetworkID"), "endpoint_id": data.get("EndpointID")})
    config = item.get("Config", {})
    host = item.get("HostConfig", {})
    state = item.get("State", {})
    ports = item.get("NetworkSettings", {}).get("Ports", {})
    stable = {
        "fingerprint": _digest(["container", item.get("Id"), name]),
        "name": name if name == "apm-postgres" else _digest(name),
        "id": item.get("Id"), "image_id": item.get("Image"), "image_reference": config.get("Image"),
        "labels": _safe_labels(labels), "restart_policy": host.get("RestartPolicy", {}).get("Name"),
        "network_mode": host.get("NetworkMode"), "privileged": host.get("Privileged"),
        "read_only_rootfs": host.get("ReadonlyRootfs"), "mounts": sorted(mounts, key=lambda x: json.dumps(x, sort_keys=True)),
        "networks": sorted(attachments, key=lambda x: (str(x.get("name")), str(x.get("network_id")))),
        "published_ports": ports,
        "ownership": "FOREIGN" if name == "apm-postgres" else _ownership(name, labels, "container"),
    }
    runtime = {"id": item.get("Id"), "status": state.get("Status"), "running": state.get("Running"), "paused": state.get("Paused"), "restarting": state.get("Restarting"), "dead": state.get("Dead"), "exit_code": state.get("ExitCode"), "health": state.get("Health", {}).get("Status") if isinstance(state.get("Health"), dict) else None}
    return {"stable": stable, "runtime": runtime}


def _network(item: dict[str, Any]) -> dict[str, Any]:
    labels = _labels(item.get("Labels")); name = str(item.get("Name", ""))
    containers = item.get("Containers", {})
    ids = sorted(str(k) for k in containers) if isinstance(containers, dict) else []
    stable = {"id": item.get("Id"), "name": name if name == f"{TASK_PROJECT}_mayak-internal" else _digest(name), "driver": item.get("Driver"), "scope": item.get("Scope"), "internal": item.get("Internal"), "attachable": item.get("Attachable"), "ingress": item.get("Ingress"), "labels": _safe_labels(labels), "ipam": item.get("IPAM", {}), "attached_container_ids": ids, "ownership": _ownership(name, labels, "network")}
    return {"stable": stable}


def _volume(item: dict[str, Any]) -> dict[str, Any]:
    labels = _labels(item.get("Labels")); name = str(item.get("Name", "")); options = item.get("Options") or {}
    stable = {"name": _digest(name), "driver": item.get("Driver"), "labels": _safe_labels(labels), "options": [[str(k), _digest(str(v))] for k, v in sorted(options.items())], "scope": item.get("Scope"), "ownership": _ownership(name, labels, "volume")}
    return {"stable": stable}


def collect_snapshot(phase: str, sequence: int) -> dict[str, Any]:
    try:
        container_ids = subprocess.run(["docker", "ps", "-aq"], capture_output=True, text=True, check=False, timeout=30)
        if container_ids.returncode != 0:
            raise RuntimeError("container enumeration failed")
        containers = []
        for ident in sorted(set(x for x in container_ids.stdout.splitlines() if x)):
            containers.extend(_run(["container", "inspect", ident]))
        networks = []
        for ident in sorted(set(x for x in subprocess.check_output(["docker", "network", "ls", "-q"], text=True, timeout=30).splitlines() if x)):
            networks.extend(_run(["network", "inspect", ident]))
        volumes = []
        for ident in sorted(set(x for x in subprocess.check_output(["docker", "volume", "ls", "-q"], text=True, timeout=30).splitlines() if x)):
            volumes.extend(_run(["volume", "inspect", ident]))
        records = {"containers": sorted((_container(x) for x in containers), key=lambda x: x["stable"]["id"]), "networks": sorted((_network(x) for x in networks), key=lambda x: x["stable"]["id"]), "volumes": sorted((_volume(x) for x in volumes), key=lambda x: x["stable"]["name"])}
        task = {kind: [x for x in records[kind] if x["stable"]["ownership"] == "TASK_OWNED"] for kind in records}
        unresolved = {kind: [x for x in records[kind] if x["stable"]["ownership"] == "UNRESOLVED"] for kind in records}
        foreign = {kind: [x for x in records[kind] if x["stable"]["ownership"] == "FOREIGN"] for kind in records}
        payload = {"schema_version": SCHEMA_VERSION, "capture_phase": phase, "collector_implementation_id": COLLECTOR_ID, "source_host_safe_identity": _digest("host"), "docker_server_safe_identity": _digest("docker"), "capture_monotonic_sequence": sequence, "container_records": foreign["containers"], "network_records": foreign["networks"], "volume_records": foreign["volumes"], "apm_postgres_present": any(x["stable"].get("name") == "apm-postgres" for x in foreign["containers"]), "task_owned_resource_records": task, "unresolved_resource_records": unresolved, "collection_complete": True, "collection_errors": [], "redaction_passed": True}
        canonical = {key: payload[key] for key in ("schema_version", "source_host_safe_identity", "docker_server_safe_identity", "container_records", "network_records", "volume_records", "apm_postgres_present", "task_owned_resource_records", "unresolved_resource_records", "collection_complete", "collection_errors", "redaction_passed")}
        payload["canonical_serialization_digest"] = _digest(canonical)
        return payload
    except (OSError, subprocess.SubprocessError, ValueError, json.JSONDecodeError, RuntimeError) as exc:
        return {"schema_version": SCHEMA_VERSION, "capture_phase": phase, "collector_implementation_id": COLLECTOR_ID, "collection_complete": False, "collection_errors": [type(exc).__name__], "redaction_passed": True, "container_records": [], "network_records": [], "volume_records": [], "task_owned_resource_records": {"containers": [], "networks": [], "volumes": []}, "unresolved_resource_records": {"containers": [], "networks": [], "volumes": []}, "canonical_serialization_digest": ""}


def classify_delta(before: dict[str, Any], after: dict[str, Any]) -> str:
    if not before.get("collection_complete") or not after.get("collection_complete"):
        return "SNAPSHOT_INCOMPLETE"
    if before.get("unresolved_resource_records") != {"containers": [], "networks": [], "volumes": []} or after.get("unresolved_resource_records") != {"containers": [], "networks": [], "volumes": []}:
        return "UNRESOLVED_RESOURCE_PRESENT"
    before_stable = {key: before.get(key) for key in ("network_records", "volume_records")}
    after_stable = {key: after.get(key) for key in ("network_records", "volume_records")}
    before_stable["container_records"] = [{"stable": item.get("stable")} for item in before.get("container_records", [])]
    after_stable["container_records"] = [{"stable": item.get("stable")} for item in after.get("container_records", [])]
    if before_stable != after_stable:
        return "FOREIGN_STRUCTURE_CHANGED"
    if [{"runtime": item.get("runtime")} for item in before.get("container_records", [])] != [{"runtime": item.get("runtime")} for item in after.get("container_records", [])]:
        return "FOREIGN_RUNTIME_STATE_CHANGED"
    return "NO_CHANGE"
