# ruff: noqa: E501
from copy import deepcopy

import pytest

from scripts.runtime.rf08_safe_foreign_schema import (
    canonical_digest,
    validate_safe_value,
    validate_snapshot,
)


def test_recursive_minimization_rejects_nested_sensitive_values() -> None:
    for value in (
        {"nested": {"dsn": "postgresql://user:pass@db/x"}},
        {"nested": [{"secret_marker": "password=bad"}]},
        {"nested": {"endpoint_id": "deadbeef"}},
    ):
        with pytest.raises(ValueError):
            validate_safe_value(value)


def test_valid_minimized_record_and_digest_pass() -> None:
    value = {
        "source_host_safe_identity": "a" * 64,
        "object_identity_hash": "b" * 64,
        "ownership": "FOREIGN",
        "mount_count": 0,
    }
    validate_safe_value(value)
    assert canonical_digest(value, tuple(value))


def test_incomplete_or_unresolved_snapshot_rejected() -> None:
    snapshot = {
        "schema_version": "ForeignResourceSnapshotV3",
        "collector_implementation_id": "collector",
        "collection_complete": False,
        "collection_errors": ["timeout"],
        "redaction_passed": True,
    }
    with pytest.raises(ValueError):
        validate_snapshot(snapshot, collector_id="collector")


def test_duplicate_identity_rejected() -> None:
    base = {
        "schema_version": "ForeignResourceSnapshotV3",
        "capture_phase": "before",
        "collector_implementation_id": "collector",
        "capture_monotonic_sequence": 1,
        "source_host_safe_identity": "a" * 64,
        "host_boot_instance_safe_identity": "b" * 64,
        "docker_server_safe_identity": "c" * 64,
        "docker_endpoint_identity_schema": "LOCAL_UNIX_DOCKER_ENDPOINT_SOCKET_V1",
        "docker_server_safe_metadata": {},
        "container_records": [],
        "network_records": [],
        "volume_records": [],
        "task_owned_resource_records": {"containers": [], "networks": [], "volumes": []},
        "unresolved_resource_records": {"containers": [], "networks": [], "volumes": []},
        "collection_complete": True,
        "collection_errors": [],
        "redaction_passed": True,
        "canonical_serialization_digest": "d" * 64,
    }
    record = {"stable": {"fingerprint": "x", "ownership": "FOREIGN"}}
    base["container_records"] = [record, deepcopy(record)]
    with pytest.raises(ValueError):
        validate_snapshot(base, collector_id="collector")
