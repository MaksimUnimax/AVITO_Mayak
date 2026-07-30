"""Verdict-free safe records for RF-08 foreign-resource evidence."""
# ruff: noqa: E501

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from typing import Any

SHA256 = re.compile(r"^[0-9a-f]{64}$")
_SECRET = re.compile(r"(?i)(postgres(?:ql)?://|dsn\s*=|password\s*=|token\s*=|private.key|-----begin)")
_PATH = re.compile(r"(?:^|/)(?:proc|sys|run/secrets|var/run/docker|home|root|tmp)(?:/|$)")
_IP = re.compile(r"(?:\d{1,3}\.){3}\d{1,3}|[0-9a-f:]{3,}:+[0-9a-f:]+|/\d{1,2}")
OWNERSHIPS = frozenset({"TASK_OWNED", "FOREIGN", "UNRESOLVED"})


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def canonical_digest(payload: Mapping[str, Any], keys: Sequence[str]) -> str:
    return hashlib.sha256(
        json.dumps({key: payload.get(key) for key in keys}, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def validate_safe_value(value: Any, *, key: str = "", hash_field: bool = False) -> None:
    """Recursively reject secret-bearing and raw machine/topology values."""
    if isinstance(value, Mapping):
        for name, child in value.items():
            if not isinstance(name, str) or (
                name not in {"Version", "ApiVersion", "MinAPIVersion", "Os", "Arch", "KernelVersion"}
                and not re.fullmatch(r"[a-z][a-z0-9_]*", name)
            ):
                raise ValueError("unsafe evidence key")
            validate_safe_value(child, key=name)
        return
    if isinstance(value, (list, tuple)):
        for child in value:
            validate_safe_value(child, key=key)
        return
    if isinstance(value, bool) or value is None or isinstance(value, (int, float)):
        return
    if not isinstance(value, str):
        raise ValueError("unsupported evidence value")
    if hash_field or key.endswith(("_hash", "_digest", "_identity")):
        if not SHA256.fullmatch(value):
            raise ValueError("invalid hash field")
        return
    lowered = value.lower()
    if _SECRET.search(value) or _PATH.search(value) or _IP.search(value):
        raise ValueError("raw sensitive evidence")
    if len(value) > 256 and not SHA256.fullmatch(value):
        raise ValueError("opaque evidence value")
    if key in {"id", "object_id", "endpoint_id", "attached_container_id", "image_id"} and not SHA256.fullmatch(value):
        raise ValueError("raw object identifier")
    if lowered in {"/var/run/docker.sock", "localhost"}:
        raise ValueError("raw endpoint value")


def validate_snapshot(snapshot: Mapping[str, Any], *, collector_id: str) -> None:
    required = {
        "schema_version", "capture_phase", "collector_implementation_id", "capture_monotonic_sequence",
        "source_host_safe_identity", "host_boot_instance_safe_identity", "docker_server_safe_identity",
        "docker_endpoint_identity_schema", "docker_server_safe_metadata", "container_records",
        "network_records", "volume_records", "task_owned_resource_records", "unresolved_resource_records",
        "collection_complete", "collection_errors", "redaction_passed", "canonical_serialization_digest",
    }
    if set(snapshot) < required or snapshot.get("collector_implementation_id") != collector_id:
        raise ValueError("snapshot schema incomplete")
    if snapshot.get("schema_version") != "ForeignResourceSnapshotV3":
        raise ValueError("snapshot schema version")
    if snapshot.get("collection_complete") is not True or snapshot.get("collection_errors") != []:
        raise ValueError("snapshot collection incomplete")
    if snapshot.get("redaction_passed") is not True:
        raise ValueError("snapshot redaction failed")
    if snapshot.get("docker_endpoint_identity_schema") not in {
        "LOCAL_UNIX_DOCKER_ENDPOINT_INSTANCE_V1", "LOCAL_UNIX_DOCKER_ENDPOINT_SOCKET_V1"
    }:
        raise ValueError("endpoint schema")
    for key in ("source_host_safe_identity", "host_boot_instance_safe_identity", "docker_server_safe_identity"):
        if not SHA256.fullmatch(str(snapshot[key])):
            raise ValueError("identity hash")
    for key in ("container_records", "network_records", "volume_records"):
        records = snapshot[key]
        if not isinstance(records, list):
            raise ValueError("record list")
        identities: list[str] = []
        for record in records:
            if not isinstance(record, Mapping):
                raise ValueError("record shape")
            stable = record.get("stable")
            if not isinstance(stable, Mapping) or stable.get("ownership") not in OWNERSHIPS:
                raise ValueError("ownership proof")
            identity = str(stable.get("identity") or stable.get("fingerprint") or stable.get("id"))
            if identity in identities:
                raise ValueError("duplicate resource identity")
            identities.append(identity)
    validate_safe_value(snapshot)
