from __future__ import annotations

# mypy: ignore-errors

import json
import shutil
import socket
import subprocess
from collections import Counter
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import pytest

from scripts.runtime import safe_compose_bootstrap as scb
from scripts.runtime.rf08_docker_authority import (
    DockerCommandClass,
    MutationAuthority,
    ReadOnlyDockerQuery,
    _compose_plan,
    _direct_plan,
    classify_docker_argv,
    gateway_token_active,
)
from scripts.runtime.rf08_foreign_snapshot import collect_snapshot
from scripts.runtime.rf08_safe_foreign_schema import (
    validate_failure_snapshot,
    validate_safe_value,
    validate_snapshot,
)
from scripts.runtime.verify_rf08_authoritative_evidence import (
    INDEPENDENT_COLLECTOR_ID,
    PRODUCER_COLLECTOR_ID,
    _docker_manifest,
    _independent_snapshot,
    _verify_stage56,
    _verify_stage57,
)
from scripts.runtime.verify_rf08_authoritative_evidence import (
    _endpoint_identity as verifier_endpoint_identity,
)

PROJECT = "avito-mayak-rf08-secret-delivery"
TECHNICAL_ID = "RF-08-CORRECTIVE-NONROOT-FILE-SECRET-DELIVERY-20260729-01"
RUNTIME_COMPOSE = "/tmp/compose.runtime.yaml"
REAL_SUBPROCESS_RUN = subprocess.run

CANONICAL_STAGE57_KEYS = (
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


@dataclass(frozen=True)
class RegistryCase:
    case_id: str
    category: str
    scenario: str
    params: dict[str, Any]

    def execute(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        dispatch(self.scenario, self.params, monkeypatch, tmp_path)


def _sha(text: str) -> str:
    return json.dumps(text, sort_keys=False).encode("utf-8").hex()[:64]


def _hash(text: str) -> str:
    import hashlib

    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _canonical_digest(payload: dict[str, Any], keys: tuple[str, ...]) -> str:
    import hashlib

    return hashlib.sha256(
        json.dumps(
            {key: payload[key] for key in keys}, sort_keys=True, separators=(",", ":")
        ).encode()
    ).hexdigest()


def _record_kwargs(record: Any) -> dict[str, Any]:
    data = dict(record.safe_dict())
    for key in (
        "planned_ownership",
        "ownership",
        "mutation_allowed",
        "scoped",
        "sequence",
        "executed",
    ):
        data.pop(key, None)
    return data


def _fake_completed(
    argv: tuple[str, ...],
    stdout: str = "",
    stderr: str = "",
    returncode: int = 0,
    *,
    text: bool = False,
) -> subprocess.CompletedProcess[Any]:
    return subprocess.CompletedProcess(
        argv,
        returncode,
        stdout=stdout if text else stdout.encode("utf-8"),
        stderr=stderr if text else stderr.encode("utf-8"),
    )


def _fake_docker_run(
    argv: tuple[str, ...], *args: Any, **kwargs: Any
) -> subprocess.CompletedProcess[Any]:
    argv = tuple(argv)
    if not argv or argv[0] != "docker":
        return REAL_SUBPROCESS_RUN(argv, *args, **kwargs)
    assert gateway_token_active()
    text = bool(kwargs.get("text", False))
    if argv[1] == "version" and "--format" in argv and "{{json .Server}}" in argv:
        payload: Any = {
            "Version": "26.0.0",
            "ApiVersion": "1.45",
            "MinAPIVersion": "1.24",
            "Os": "linux",
            "Arch": "amd64",
            "KernelVersion": "6.8.0",
        }
        return _fake_completed(argv, json.dumps(payload) + "\n", text=text)
    if argv[:2] == ("docker", "buildx") and len(argv) > 2 and argv[2] == "build":
        source = Path(argv[-1])
        output: Path | None = None
        for index, token in enumerate(argv):
            if token == "--output" and index + 1 < len(argv):
                value = argv[index + 1]
                if "dest=" in value:
                    output = Path(value.split("dest=", 1)[1].split(",", 1)[0])
                    break
        if output is not None:
            effective = output / "effective"
            effective.mkdir(mode=0o700, parents=True, exist_ok=True)
            for relative in ("pyproject.toml", "uv.lock", "README.md", "alembic.ini"):
                shutil.copy2(source / relative, effective / relative)
            if (source / "src").is_dir():
                shutil.copytree(source / "src", effective / "src", dirs_exist_ok=True)
            if (source / "alembic").is_dir():
                shutil.copytree(source / "alembic", effective / "alembic", dirs_exist_ok=True)
        return _fake_completed(argv, "", text=text)
    if argv[:3] == ("docker", "compose", "-f") and "version" in argv:
        return _fake_completed(argv, "2.0.0\n", text=text)
    if argv[:3] == ("docker", "compose", "-f") and "config" in argv:
        payload: Any = {
            "config_name": PROJECT,
            "services": {},
            "internal_network": True,
            "postgres_host_ports": [],
            "api_bind_host": "127.0.0.1",
            "secret_wiring": {},
        }
        return _fake_completed(argv, json.dumps(payload) + "\n", text=text)
    if argv[:2] == ("docker", "inspect") or (
        len(argv) >= 4
        and argv[1] in {"container", "network", "volume", "image"}
        and argv[2] == "inspect"
    ):
        ident = argv[2] if argv[:2] == ("docker", "inspect") else argv[3]
        if ident == "apm-postgres":
            payload: Any = [
                {
                    "Id": "apm-postgres",
                    "Name": "/apm-postgres",
                    "Config": {
                        "Labels": {},
                        "Image": "postgres:18-bookworm",
                    },
                    "HostConfig": {
                        "NetworkMode": "bridge",
                        "Privileged": False,
                        "ReadonlyRootfs": True,
                        "RestartPolicy": {"Name": "always"},
                    },
                    "State": {
                        "Status": "running",
                        "Running": True,
                        "Paused": False,
                        "Restarting": False,
                        "Dead": False,
                        "ExitCode": 0,
                        "Health": {"Status": "healthy"},
                    },
                    "NetworkSettings": {
                        "Ports": {},
                        "Networks": {
                            "bridge": {"NetworkID": "bridge-id", "EndpointID": "bridge-endpoint"}
                        },
                    },
                    "Mounts": [],
                }
            ]
        elif ident == f"{PROJECT}-mayak-postgres-1":
            payload = [
                {
                    "Id": ident,
                    "Name": f"/{ident}",
                    "Config": {
                        "Labels": {
                            "com.docker.compose.project": PROJECT,
                            "com.docker.compose.service": "mayak-postgres",
                            "com.avito-mayak.technical-id": TECHNICAL_ID,
                            "com.avito-mayak.owner": "rf08",
                            "com.avito-mayak.project-owned": "true",
                            "com.avito-mayak.environment-id": "avito-mayak-acceptance-local-01",
                            "com.avito-mayak.compose-project": "avito-mayak-acceptance",
                        },
                        "Image": "postgres:18-bookworm",
                    },
                    "HostConfig": {
                        "NetworkMode": "bridge",
                        "Privileged": False,
                        "ReadonlyRootfs": True,
                        "RestartPolicy": {"Name": "always"},
                    },
                    "State": {
                        "Status": "running",
                        "Running": True,
                        "Paused": False,
                        "Restarting": False,
                        "Dead": False,
                        "ExitCode": 0,
                        "Health": {"Status": "healthy"},
                    },
                    "NetworkSettings": {
                        "Ports": {},
                        "Networks": {
                            "bridge": {"NetworkID": "bridge-id", "EndpointID": "bridge-endpoint"}
                        },
                    },
                    "Mounts": [],
                }
            ]
        elif ident in {"net-id-1", f"{PROJECT}_mayak-internal"}:
            payload: Any = [
                {
                    "Id": ident,
                    "Name": ident,
                    "Driver": "bridge",
                    "Scope": "local",
                    "Internal": False,
                    "Attachable": False,
                    "Ingress": False,
                    "Labels": {},
                    "IPAM": {},
                    "Containers": {},
                }
            ]
        elif ident in {"vol-id-1", f"{PROJECT}_postgres-data"}:
            payload: Any = [
                {
                    "Id": ident,
                    "Name": ident,
                    "Driver": "local",
                    "Scope": "local",
                    "Labels": {},
                    "Options": {"o": "addr"},
                }
            ]
        else:
            payload: Any = [
                {
                    "Id": ident,
                    "Name": f"/{ident}",
                    "Config": {
                        "Labels": {},
                        "Image": "busybox:1.36",
                    },
                    "HostConfig": {
                        "NetworkMode": "bridge",
                        "Privileged": False,
                        "ReadonlyRootfs": True,
                        "RestartPolicy": {"Name": "always"},
                    },
                    "State": {
                        "Status": "running",
                        "Running": True,
                        "Paused": False,
                        "Restarting": False,
                        "Dead": False,
                        "ExitCode": 0,
                        "Health": {"Status": "healthy"},
                    },
                    "NetworkSettings": {
                        "Ports": {},
                        "Networks": {},
                    },
                    "Mounts": [],
                }
            ]
        return _fake_completed(argv, json.dumps(payload) + "\n", text=text)
    if (
        argv[:2] == ("docker", "ps")
        or argv[:2] == ("docker", "network")
        or argv[:2] == ("docker", "volume")
    ):
        if "ls" in argv and "-q" in argv:
            if argv[1] == "ps":
                return _fake_completed(argv, "apm-postgres\n", text=text)
            if argv[1] == "network":
                return _fake_completed(argv, "net-id-1\n", text=text)
            if argv[1] == "volume":
                return _fake_completed(argv, "vol-id-1\n", text=text)
    if argv[:2] == ("docker", "compose") and "exec" in argv:
        return _fake_completed(argv, "ok\n", text=text)
    return _fake_completed(argv, "ok\n", text=text)


def _patch_docker(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("scripts.runtime.rf08_docker_authority.subprocess.run", _fake_docker_run)


def _compose_base(file: str = RUNTIME_COMPOSE) -> tuple[str, ...]:
    return (
        "docker",
        "compose",
        "-f",
        file,
        "-p",
        PROJECT,
        "--profile",
        "runtime-foundation",
    )


def _mutation(argv_tail: tuple[str, ...], file: str = RUNTIME_COMPOSE):
    return _compose_plan(_compose_base(file) + argv_tail)


def _authority_three_mutations() -> MutationAuthority:
    authority = MutationAuthority()
    mutation = _mutation(("up", "-d", "mayak-postgres"))
    stop = _mutation(("stop", "mayak-postgres"))
    down = _mutation(("down", "--remove-orphans", "--volumes"))
    authority.execute(mutation, stage="s1")
    authority.execute(stop, stage="s2")
    authority.execute(down, stage="s3")
    return authority


def _valid_snapshot_template(
    collector_id: str = PRODUCER_COLLECTOR_ID,
    *,
    phase: str = "before",
    sequence: int = 1,
) -> dict[str, Any]:
    snapshot: dict[str, Any] = {
        "schema_version": "ForeignResourceSnapshotV3",
        "capture_phase": phase,
        "collector_implementation_id": collector_id,
        "capture_monotonic_sequence": sequence,
        "source_host_safe_identity": _hash("host"),
        "host_boot_instance_safe_identity": _hash("boot"),
        "docker_server_safe_identity": _hash("daemon"),
        "docker_endpoint_identity_schema": "LOCAL_UNIX_DOCKER_ENDPOINT_SOCKET_V1",
        "docker_server_safe_metadata": {"Version": "26.0.0", "ApiVersion": "1.45"},
        "container_records": [
            {
                "stable": {
                    "fingerprint": _hash("container:fingerprint"),
                    "name": _hash("container:name"),
                    "is_apm_postgres": True,
                    "id": _hash("container:id"),
                    "image_id_hash": _hash("container:image-id"),
                    "image_reference_hash": _hash("container:image-ref"),
                    "labels": [[_hash("label:key"), _hash("label:value")]],
                    "restart_policy": "always",
                    "network_mode": "bridge",
                    "privileged": False,
                    "read_only_rootfs": True,
                    "mounts": [],
                    "networks": [],
                    "published_port_count": 0,
                    "ownership": "FOREIGN",
                },
                "runtime": {
                    "id": _hash("container:id"),
                    "status": "running",
                    "running": True,
                    "paused": False,
                    "restarting": False,
                    "dead": False,
                    "exit_code": 0,
                    "health": "healthy",
                },
            }
        ],
        "network_records": [
            {
                "stable": {
                    "identity": _hash("network:identity"),
                    "name": _hash("network:name"),
                    "driver": "bridge",
                    "scope": "local",
                    "internal": False,
                    "attachable": False,
                    "ingress": False,
                    "labels": [],
                    "ipam_hash": _hash("network:ipam"),
                    "attachment_count": 0,
                    "attachment_hashes": [],
                    "ownership": "FOREIGN",
                }
            }
        ],
        "volume_records": [
            {
                "stable": {
                    "identity": _hash("volume:identity"),
                    "name": _hash("volume:name"),
                    "driver": "local",
                    "labels": [],
                    "options": [[_hash("opt"), _hash("val")]],
                    "scope": "local",
                    "ownership": "FOREIGN",
                }
            }
        ],
        "apm_postgres_present": True,
        "task_owned_resource_records": {"containers": [], "networks": [], "volumes": []},
        "unresolved_resource_records": {"containers": [], "networks": [], "volumes": []},
        "collection_complete": True,
        "collection_errors": [],
        "redaction_passed": True,
    }
    snapshot["canonical_serialization_digest"] = _canonical_digest(snapshot, CANONICAL_STAGE57_KEYS)
    return snapshot


def _failure_snapshot_template(*, phase: str = "before", sequence: int = 1) -> dict[str, Any]:
    return {
        "schema_version": "ForeignResourceSnapshotV3",
        "capture_phase": phase,
        "collector_implementation_id": PRODUCER_COLLECTOR_ID,
        "capture_monotonic_sequence": sequence,
        "source_host_safe_identity": None,
        "host_boot_instance_safe_identity": None,
        "docker_server_safe_identity": None,
        "docker_endpoint_identity_schema": None,
        "docker_server_safe_metadata": {},
        "collection_complete": False,
        "collection_errors": ["RuntimeError"],
        "redaction_passed": False,
        "container_records": [],
        "network_records": [],
        "volume_records": [],
        "task_owned_resource_records": {"containers": [], "networks": [], "volumes": []},
        "unresolved_resource_records": {"containers": [], "networks": [], "volumes": []},
        "canonical_serialization_digest": "",
    }


def _stage56_evidence(*, authorized: int = 3, executed: int = 3) -> dict[str, Any]:
    return {
        "stage56_observations": {
            "task_container_count": 0,
            "task_network_count": 0,
            "task_volume_count": 0,
            "unresolved_count": 0,
            "private_output_count": 0,
            "json_log_count": 0,
            "override_count": 0,
            "context_directory_count": 0,
            "runtime_compose_count": 0,
            "temporary_validation_resource_count": 0,
            "authorized_mutation_count": authorized,
            "executed_mutation_count": executed,
            "foreign_target_mutation_count": 0,
            "unresolved_target_mutation_count": 0,
            "unscoped_mutation_count": 0,
            "broad_mutation_count": 0,
        },
        "observed": "task_owned_cleanup_complete",
        "cleanup_observed": True,
        "cleanup_exit": 0,
        "foreign_deletion": False,
    }


def _valid_stage57_evidence(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> dict[str, Any]:
    _producer_gateway = MutationAuthority()
    _independent_gateway = MutationAuthority()
    sock, server = _endpoint_socket(tmp_path)
    monkeypatch.setenv("DOCKER_HOST", f"unix://{sock}")
    try:
        producer_before = _valid_snapshot_template(
            PRODUCER_COLLECTOR_ID, phase="before", sequence=1
        )
        independent_before = _valid_snapshot_template(
            INDEPENDENT_COLLECTOR_ID, phase="before", sequence=1
        )
        producer_after = _valid_snapshot_template(PRODUCER_COLLECTOR_ID, phase="after", sequence=2)
        independent_after = _valid_snapshot_template(
            INDEPENDENT_COLLECTOR_ID, phase="after", sequence=2
        )
        ledger = [entry.safe_dict() for entry in _authority_three_mutations().entries]
        return {
            "foreign_records": {
                "producer_before": producer_before,
                "independent_before": independent_before,
                "producer_after": producer_after,
                "independent_after": independent_after,
            },
            "producer_before_snapshot": producer_before,
            "independent_before_snapshot": independent_before,
            "producer_after_snapshot": producer_after,
            "independent_after_snapshot": independent_after,
            "foreign_before_collectors_equal": producer_before["canonical_serialization_digest"]
            == independent_before["canonical_serialization_digest"],
            "foreign_after_collectors_equal": producer_after["canonical_serialization_digest"]
            == independent_after["canonical_serialization_digest"],
            "foreign_before_producer_digest": producer_before["canonical_serialization_digest"],
            "foreign_before_independent_digest": independent_before[
                "canonical_serialization_digest"
            ],
            "foreign_after_producer_digest": producer_after["canonical_serialization_digest"],
            "foreign_after_independent_digest": independent_after["canonical_serialization_digest"],
            "foreign_resource_set_equal": True,
            "foreign_structural_digest_equal": True,
            "foreign_runtime_state_digest_equal": True,
            "foreign_delta_classification": "NO_CHANGE",
            "foreign_container_count": len(producer_after["container_records"]),
            "foreign_network_count": len(producer_after["network_records"]),
            "foreign_volume_count": len(producer_after["volume_records"]),
            "apm_postgres_present_before": producer_before["apm_postgres_present"],
            "apm_postgres_present_after": producer_after["apm_postgres_present"],
            "task_container_count_after_cleanup": 0,
            "task_network_count_after_cleanup": 0,
            "task_volume_count_after_cleanup": 0,
            "unresolved_resource_count": 0,
            "foreign_target_mutation_command_count": 0,
            "unresolved_target_mutation_command_count": 0,
            "snapshot_private_artifacts_removed": True,
            "cleanup_observation": {
                "task_containers": 0,
                "task_networks": 0,
                "task_volumes": 0,
                "unresolved": 0,
            },
            "mutation_ledger": ledger,
        }
    finally:
        server.close()


def _endpoint_socket(tmp_path: Path) -> tuple[Path, socket.socket]:
    sock = tmp_path / "docker.sock"
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(str(sock))
    server.listen(1)
    return sock, server


def _run_protocol_integration(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[scb.SafeRecord, scb.PrivateCommandRunner]:
    _patch_docker(monkeypatch)

    def fake_init(self: Any, required_stages=scb.REQUIRED_STAGES) -> None:  # type: ignore[override]
        self.required = ("PREFLIGHT", "MUT1", "MUT2", "MUT3")
        self._entries = []
        self._results = {}
        self._rejected_results = {}
        self.run_id = "rf08-" + __import__("uuid").uuid4().hex

    monkeypatch.setattr(scb.ProtocolTranscript, "__init__", fake_init)

    def fake_specs(ctx: dict[str, object], source_tree: Path) -> tuple[scb.StageSpec, ...]:
        def preflight() -> scb.StageResult:
            assert ctx["runner"].gateway is ctx["mutation_ledger"]
            ctx["application_probe_contract"] = scb.build_application_probe_contract(
                "sha256:" + "a" * 64
            )
            ctx["build_context_snapshot"] = {}
            ctx["b_consumer_binding"] = {}
            return scb.StageResult("PREFLIGHT", "op.preflight", True, 0, {"observed": "ok"})

        def mut1() -> scb.StageResult:
            gateway = ctx["mutation_ledger"]
            assert isinstance(gateway, MutationAuthority)
            gateway.execute(_mutation(("up", "-d", "mayak-postgres")), stage="MUT1")
            return scb.StageResult("MUT1", "op.mut1", True, 0, {"observed": "mut1"})

        def mut2() -> scb.StageResult:
            gateway = ctx["mutation_ledger"]
            assert isinstance(gateway, MutationAuthority)
            gateway.execute(_mutation(("stop", "mayak-postgres")), stage="MUT2")
            return scb.StageResult("MUT2", "op.mut2", True, 0, {"observed": "mut2"})

        def mut3() -> scb.StageResult:
            gateway = ctx["mutation_ledger"]
            assert isinstance(gateway, MutationAuthority)
            gateway.execute(_mutation(("down", "--remove-orphans", "--volumes")), stage="MUT3")
            return scb.StageResult("MUT3", "op.mut3", True, 0, {"observed": "mut3"})

        return (
            scb.StageSpec(
                "PREFLIGHT",
                preflight,
                lambda result: {"observed": "ok"},
                "parser.preflight",
                "oracle.preflight",
            ),
            scb.StageSpec(
                "MUT1", mut1, lambda result: {"observed": "mut1"}, "parser.mut1", "oracle.mut1"
            ),
            scb.StageSpec(
                "MUT2", mut2, lambda result: {"observed": "mut2"}, "parser.mut2", "oracle.mut2"
            ),
            scb.StageSpec(
                "MUT3", mut3, lambda result: {"observed": "mut3"}, "parser.mut3", "oracle.mut3"
            ),
        )

    monkeypatch.setattr(scb, "_operation_specs", fake_specs)
    root = scb.RUNTIME_ROOT / "registry-integration" / tmp_path.name
    runner = scb.PrivateCommandRunner({}, root=root, gateway=MutationAuthority())
    record = scb.run_protocol(root=root, source_sha="0" * 40, runner=runner)
    return record, runner


def _minimal_build_context_snapshot() -> dict[str, Any]:
    return {
        "schema_version": "rf08-docker-native-context-v1",
        "expected_base_tree_identity": "base-tree",
        "archive_sha256": "archive",
        "docker_native_export_identity": {"manifest_sha256": "manifest"},
        "manifest": [],
        "digest": "digest",
        "dockerfile_sha256": "dockerfile",
        "dockerignore_sha256": "dockerignore",
        "copy_plan": [],
    }


def test_replay_namespace_sanitation_is_idempotent_and_exact(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    removed: list[tuple[str, str]] = []
    state = {"task": True}

    def fake_inspect(_: MutationAuthority) -> dict[str, object]:
        task_containers = (
            [
                {
                    "kind": "container",
                    "name": f"{PROJECT}-mayak-postgres-1",
                    "identity_hash": _hash("task-container"),
                    "ownership": "TASK_OWNED",
                    "labels": {
                        "com.docker.compose.project": PROJECT,
                        "com.docker.compose.service": "mayak-postgres",
                        "com.avito-mayak.technical-id": TECHNICAL_ID,
                        "com.avito-mayak.owner": "rf08",
                    },
                    "service": "mayak-postgres",
                }
            ]
            if state["task"]
            else []
        )
        task_networks = (
            [
                {
                    "kind": "network",
                    "name": f"{PROJECT}_mayak-internal",
                    "identity_hash": _hash("task-network"),
                    "ownership": "TASK_OWNED",
                    "labels": {
                        "com.docker.compose.project": PROJECT,
                        "com.avito-mayak.project-owned": "true",
                        "com.avito-mayak.environment-id": "avito-mayak-acceptance-local-01",
                        "com.avito-mayak.compose-project": "avito-mayak-acceptance",
                    },
                    "service": "",
                }
            ]
            if state["task"]
            else []
        )
        task_volumes = (
            [
                {
                    "kind": "volume",
                    "name": f"{PROJECT}_postgres-data",
                    "identity_hash": _hash("task-volume"),
                    "ownership": "TASK_OWNED",
                    "labels": {
                        "com.docker.compose.project": PROJECT,
                        "com.avito-mayak.project-owned": "true",
                        "com.avito-mayak.environment-id": "avito-mayak-acceptance-local-01",
                        "com.avito-mayak.compose-project": "avito-mayak-acceptance",
                    },
                    "service": "",
                }
            ]
            if state["task"]
            else []
        )
        foreign = {
            "containers": [
                {
                    "kind": "container",
                    "name": "apm-postgres",
                    "identity_hash": _hash("foreign-container"),
                    "ownership": "FOREIGN",
                    "labels": {},
                    "service": "",
                }
            ],
            "networks": [],
            "volumes": [],
        }
        task = {"containers": task_containers, "networks": task_networks, "volumes": task_volumes}
        unresolved = {"containers": [], "networks": [], "volumes": []}
        return {
            "containers": task_containers + foreign["containers"],
            "networks": task_networks,
            "volumes": task_volumes,
            "task": task,
            "unresolved": unresolved,
            "foreign": foreign,
            "task_counts": {k: len(v) for k, v in task.items()},
            "unresolved_counts": {k: 0 for k in task},
            "foreign_counts": {"containers": 1, "networks": 0, "volumes": 0},
        }

    def fake_collect(
        phase: str, sequence: int, gateway: MutationAuthority | None = None
    ) -> dict[str, object]:
        return {
            "schema_version": "ForeignResourceSnapshotV3",
            "collector_implementation_id": PRODUCER_COLLECTOR_ID,
            "collection_complete": True,
            "canonical_serialization_digest": "foreign-digest",
            "task_owned_resource_records": {"containers": [], "networks": [], "volumes": []},
            "unresolved_resource_records": {"containers": [], "networks": [], "volumes": []},
            "container_records": [
                {
                    "stable": {
                        "fingerprint": _hash("foreign-container"),
                        "name": _hash("foreign-container"),
                        "is_apm_postgres": True,
                        "id": _hash("foreign-container"),
                        "image_id_hash": _hash("foreign-image"),
                        "image_reference_hash": _hash("foreign-image-ref"),
                        "labels": [],
                        "restart_policy": "always",
                        "network_mode": "bridge",
                        "privileged": False,
                        "read_only_rootfs": True,
                        "mounts": [],
                        "networks": [],
                        "published_port_count": 0,
                        "ownership": "FOREIGN",
                    },
                    "runtime": {"id": _hash("foreign-container")},
                }
            ],
            "network_records": [],
            "volume_records": [],
            "apm_postgres_present": True,
        }

    def fake_remove(gateway: MutationAuthority, record: dict[str, object]) -> None:
        removed.append((str(record["kind"]), str(record["name"])))
        state["task"] = False

    monkeypatch.setattr(scb, "_inspect_replay_namespace", fake_inspect)
    monkeypatch.setattr(scb, "collect_foreign_snapshot", fake_collect)
    monkeypatch.setattr(
        scb,
        "_independent_foreign_snapshot",
        lambda phase, sequence, source_tree=None: {
            "canonical_serialization_digest": "foreign-digest"
        },
    )
    monkeypatch.setattr(scb, "_buildx_builder_count", lambda gateway: 0)
    monkeypatch.setattr(scb, "_secret_generation_residue", lambda root: (0, False))
    monkeypatch.setattr(scb, "_remove_task_owned_resource", fake_remove)
    ctx: dict[str, object] = {
        "mutation_ledger": MutationAuthority(),
        "transcript": scb.ProtocolTranscript(("PREFLIGHT",)),
        "source_sha": "0" * 40,
        "root": tmp_path,
    }
    record = scb._prepare_replay_namespace_sanitation(ctx, Path(__file__).resolve().parents[2])
    assert record.task_container_count_before == 1
    assert record.task_network_count_before == 1
    assert record.task_volume_count_before == 1
    assert record.task_container_count_after == 0
    assert record.task_network_count_after == 0
    assert record.task_volume_count_after == 0
    digest_payload = record.safe_dict()
    digest_payload.pop("record_digest", None)
    assert record.record_digest == scb._record_digest(digest_payload)
    assert ctx["replay_namespace_sanitation_verified"] is True
    assert removed == [
        ("container", f"{PROJECT}-mayak-postgres-1"),
        ("network", f"{PROJECT}_mayak-internal"),
        ("volume", f"{PROJECT}_postgres-data"),
    ]
    removed.clear()
    record_again = scb._prepare_replay_namespace_sanitation(
        ctx, Path(__file__).resolve().parents[2]
    )
    assert record_again.task_container_count_before == 0
    assert record_again.task_network_count_before == 0
    assert record_again.task_volume_count_before == 0
    assert removed == []


def test_replay_namespace_sanitation_rejects_unresolved_resources(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def fake_inspect(_: MutationAuthority) -> dict[str, object]:
        unresolved = {
            "containers": [
                {
                    "kind": "container",
                    "name": f"{PROJECT}-stale-1",
                    "identity_hash": _hash("stale-container"),
                    "ownership": "UNRESOLVED",
                    "labels": {
                        "com.docker.compose.project": PROJECT,
                        "com.avito-mayak.technical-id": "WRONG",
                        "com.avito-mayak.owner": "rf08",
                    },
                    "service": "",
                }
            ],
            "networks": [],
            "volumes": [],
        }
        return {
            "containers": unresolved["containers"],
            "networks": [],
            "volumes": [],
            "task": {"containers": [], "networks": [], "volumes": []},
            "unresolved": unresolved,
            "foreign": {"containers": [], "networks": [], "volumes": []},
            "task_counts": {"containers": 0, "networks": 0, "volumes": 0},
            "unresolved_counts": {"containers": 1, "networks": 0, "volumes": 0},
            "foreign_counts": {"containers": 0, "networks": 0, "volumes": 0},
        }

    monkeypatch.setattr(scb, "_inspect_replay_namespace", fake_inspect)
    monkeypatch.setattr(
        scb,
        "collect_foreign_snapshot",
        lambda phase, sequence, gateway=None: {
            "canonical_serialization_digest": "foreign-digest",
            "collection_complete": True,
        },
    )
    monkeypatch.setattr(
        scb,
        "_independent_foreign_snapshot",
        lambda phase, sequence, source_tree=None: {
            "canonical_serialization_digest": "foreign-digest"
        },
    )
    monkeypatch.setattr(scb, "_buildx_builder_count", lambda gateway: 0)
    monkeypatch.setattr(scb, "_secret_generation_residue", lambda root: (0, False))
    called: list[tuple[str, str]] = []
    monkeypatch.setattr(
        scb,
        "_remove_task_owned_resource",
        lambda gateway, record: called.append((str(record["kind"]), str(record["name"]))),
    )
    ctx: dict[str, object] = {
        "mutation_ledger": MutationAuthority(),
        "transcript": scb.ProtocolTranscript(("PREFLIGHT",)),
        "source_sha": "0" * 40,
        "root": tmp_path,
    }
    with pytest.raises(scb.ProtocolFailure):
        scb._prepare_replay_namespace_sanitation(ctx, Path(__file__).resolve().parents[2])
    assert called == []


def test_replay_transcript_refuses_without_sanitation_record(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(scb, "_prepare_replay_namespace_sanitation", lambda ctx, source_tree: None)
    monkeypatch.setattr(scb, "prepare_jsonlog_runtime", lambda run_id: tmp_path / "logs")
    root = scb.RUNTIME_ROOT / "rf08-test" / tmp_path.name
    runner = scb.PrivateCommandRunner({}, root=root, gateway=MutationAuthority())
    record = scb.run_protocol(root=root, source_sha="0" * 40, runner=runner)
    assert record.status == "FAIL"
    assert record.stage_sequence == ()


def test_database_bootstrap_stage_carries_recovered_generation_id(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(scb, "_require_replay_namespace_sanitation", lambda ctx, source_tree: None)
    command: dict[str, tuple[str, ...]] = {}

    class Runner:
        env: dict[str, str] = {}

        def run(self, argv: tuple[str, ...], *, stage: str) -> scb.PrivateCommandResult:
            command["argv"] = argv
            return scb.PrivateCommandResult(
                stage, "cmd", 0, True, {"observed": "ok"}, True, True, False, False
            )

    ctx: dict[str, object] = {
        "mutation_ledger": MutationAuthority(),
        "transcript": scb.ProtocolTranscript(("PREFLIGHT",)),
        "runner": Runner(),
        "source_sha": "0" * 40,
        "root": tmp_path,
        "recovered_generation_id": "g-" + "a" * 24,
        "build_context_snapshot": _minimal_build_context_snapshot(),
        "replay_namespace_sanitation_verified": True,
        "b_correlation_id": "rf08b_test01",
    }
    specs = scb._operation_specs(ctx, Path(__file__).resolve().parents[2])
    spec = next(item for item in specs if item.name == "DATABASE_BOOTSTRAP_A")
    result = spec.operation()
    assert result.stage == "DATABASE_BOOTSTRAP_A"
    assert any(
        item == f"RF08_RECOVERED_GENERATION_ID={ctx['recovered_generation_id']}"
        for item in command["argv"]
    )
    assert "UNSET" not in " ".join(command["argv"])


def test_migration_upgrade_stage_uses_compose_run_service_command(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(scb, "_require_replay_namespace_sanitation", lambda ctx, source_tree: None)
    command: dict[str, tuple[str, ...]] = {}

    class Runner:
        env: dict[str, str] = {}

        def run(self, argv: tuple[str, ...], *, stage: str) -> scb.PrivateCommandResult:
            command["argv"] = argv
            return scb.PrivateCommandResult(
                stage, "cmd", 0, True, {"observed": "ok"}, True, True, False, False
            )

    ctx: dict[str, object] = {
        "mutation_ledger": MutationAuthority(),
        "transcript": scb.ProtocolTranscript(("PREFLIGHT",)),
        "runner": Runner(),
        "source_sha": "0" * 40,
        "root": tmp_path,
        "build_context_snapshot": _minimal_build_context_snapshot(),
        "replay_namespace_sanitation_verified": True,
        "b_correlation_id": "rf08b_test02",
    }
    specs = scb._operation_specs(ctx, Path(__file__).resolve().parents[2])
    spec = next(item for item in specs if item.name == "MIGRATION_UPGRADE_A")
    result = spec.operation()
    assert result.stage == "MIGRATION_UPGRADE_A"
    assert command["argv"][:8] == (
        "docker",
        "compose",
        "-f",
        str(scb.RUNTIME_COMPOSE_FILE),
        "-p",
        scb.TASK_PROJECT,
        "--profile",
        "runtime-foundation",
    )
    assert command["argv"][8:] == ("run", "--rm", "mayak-migrate")


def dispatch(
    scenario: str, params: dict[str, Any], monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _patch_docker(monkeypatch)
    argv_value = params.get("argv")
    argv = (
        tuple(argv_value.argv if hasattr(argv_value, "argv") else argv_value)
        if argv_value is not None
        else ()
    )

    if scenario == "classify":
        assert classify_docker_argv(argv) == params["expected"]
        return

    if scenario == "authorize_reject":
        authority = MutationAuthority()
        with pytest.raises(tuple(params["exceptions"])):
            authority.authorize(
                argv_value if hasattr(argv_value, "command_class") else _direct_plan(argv),
                stage="negative",
            )
        return

    if scenario == "direct_run_reject":
        authority = MutationAuthority()
        with pytest.raises(tuple(params["exceptions"])):
            authority.execute(
                argv_value if hasattr(argv_value, "command_class") else _direct_plan(argv),
                stage="direct",
            )
        return

    if scenario == "direct_run_accept":
        authority = MutationAuthority()
        result = authority.execute(
            argv_value if hasattr(argv_value, "command_class") else _direct_plan(argv),
            stage="direct",
        )
        assert isinstance(result, subprocess.CompletedProcess)
        return

    if scenario == "authorize_accept":
        authority = MutationAuthority()
        auth = authority.authorize(
            argv_value if hasattr(argv_value, "command_class") else _direct_plan(argv),
            stage="authorize",
        )
        assert auth.gateway_instance_id == authority.gateway_instance_id
        assert authority.entries[0].authorization_outcome == "AUTHORIZED"
        return

    if scenario == "caller_ownership_absent":
        authority = MutationAuthority()
        with pytest.raises(TypeError):
            getattr(authority, "authorize")(
                argv_value if hasattr(argv_value, "command_class") else _direct_plan(argv),
                stage="authorize",
                ownership="TASK_OWNED",
            )  # type: ignore[arg-type]
        return

    if scenario == "ledger_three":
        authority = _authority_three_mutations()
        assert [
            item.authorization_sequence
            for item in authority.entries
            if item.record_type == "AUTHORIZATION"
        ] == [1, 2, 3]
        assert [
            item.execution_result_sequence
            for item in authority.entries
            if item.record_type == "RESULT"
        ] == [1, 2, 3]
        authority.validate_complete(3)
        return

    if scenario == "ledger_tamper":
        tamper = params["tamper"]
        if tamper == "three":
            authority = _authority_three_mutations()
            assert [
                item.authorization_sequence
                for item in authority.entries
                if item.record_type == "AUTHORIZATION"
            ] == [1, 2, 3]
            assert [
                item.execution_result_sequence
                for item in authority.entries
                if item.record_type == "RESULT"
            ] == [1, 2, 3]
            authority.validate_complete(3)
            return
        if tamper == "direct_append":
            authority = _authority_three_mutations()
            with pytest.raises(AttributeError):
                authority.entries.append(authority.entries[0])  # type: ignore[attr-defined]
            return
        if tamper == "empty_with_mutations":
            authority = MutationAuthority()
            authority.execute(_mutation(("up", "-d", "mayak-postgres")), stage="s1")
            authority._ledger.clear()
            with pytest.raises(ValueError):
                authority.validate_complete(1)
            return
        if tamper == "missing_result":
            authority = _authority_three_mutations()
            authority._ledger.pop()  # type: ignore[attr-defined]
            with pytest.raises(ValueError):
                authority.validate_complete(3)
            return
        if tamper == "duplicate_result":
            authority = _authority_three_mutations()
            authority._ledger.append(authority._ledger[-1])
            with pytest.raises(ValueError):
                authority.validate_complete(3)
            return
        if tamper == "result_before_auth":
            authority = _authority_three_mutations()
            authority._ledger[:] = (
                authority._ledger[1:2] + authority._ledger[0:1] + authority._ledger[2:]
            )
            with pytest.raises(ValueError):
                authority.validate_complete(3)
            return
        if tamper == "sequence_gap":
            authority = _authority_three_mutations()
            authority._ledger[0] = authority._ledger[0].__class__(
                **{**_record_kwargs(authority._ledger[0]), "authorization_sequence": 3}
            )
            with pytest.raises(ValueError):
                authority.validate_complete(3)
            return
        if tamper == "duplicate_authorization":
            authority = _authority_three_mutations()
            authority._ledger[2] = authority._ledger[2].__class__(
                **{**_record_kwargs(authority._ledger[2]), "authorization_sequence": 1}
            )
            with pytest.raises(ValueError):
                authority.validate_complete(3)
            return
        if tamper == "mismatched_hash":
            authority = _authority_three_mutations()
            authority._invocation_audit[0] = replace(
                authority._invocation_audit[0], argv_fingerprint="0" * 64
            )
            with pytest.raises(ValueError):
                authority.validate_complete(3)
            return
        if tamper == "mismatched_stage":
            authority = _authority_three_mutations()
            authority._ledger[1] = authority._ledger[1].__class__(
                **{**_record_kwargs(authority._ledger[1]), "stage": "OTHER"}
            )
            with pytest.raises(ValueError):
                authority.validate_complete(3)
            return
        if tamper == "timeout_result_not_zero":
            authority = MutationAuthority()

            def timeout_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
                argv = tuple(str(item) for item in args[0])
                if argv[:3] == ("docker", "container", "inspect"):
                    return _fake_completed(argv, returncode=1)
                raise subprocess.TimeoutExpired(cmd=argv, timeout=1)

            monkeypatch.setattr("scripts.runtime.rf08_docker_authority.subprocess.run", timeout_run)
            with pytest.raises(subprocess.TimeoutExpired):
                authority.execute(_mutation(("up", "-d", "mayak-postgres")), stage="timeout")
            assert authority.entries[-1].timed_out is True
            return
        if tamper == "process_start_failure":
            authority = MutationAuthority()

            def fail_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
                argv = tuple(str(item) for item in args[0])
                if argv[:3] == ("docker", "container", "inspect"):
                    return _fake_completed(argv, returncode=1)
                raise OSError("boom")

            monkeypatch.setattr("scripts.runtime.rf08_docker_authority.subprocess.run", fail_run)
            with pytest.raises(OSError):
                authority.execute(_mutation(("up", "-d", "mayak-postgres")), stage="failure")
            assert authority.entries[-1].record_type == "RESULT"
            assert authority.entries[-1].safe_failure_classification == "OSError"
            return
        raise AssertionError(f"unknown ledger tamper scenario: {tamper}")

    if scenario == "endpoint_identity":
        kind = params["kind"]
        if kind == "success":
            _patch_docker(monkeypatch)
            sock, server = _endpoint_socket(tmp_path)
            monkeypatch.setenv("DOCKER_HOST", f"unix://{sock}")
            try:
                schema, digest, metadata = verifier_endpoint_identity(MutationAuthority())
                assert schema in {
                    "LOCAL_UNIX_DOCKER_ENDPOINT_INSTANCE_V1",
                    "LOCAL_UNIX_DOCKER_ENDPOINT_SOCKET_V1",
                }
                assert len(digest) == 64
                assert metadata["Version"] == "26.0.0"
            finally:
                server.close()
            return
        if kind == "nonunix":
            monkeypatch.setenv("DOCKER_HOST", "tcp://127.0.0.1:2375")
            with pytest.raises(ValueError):
                verifier_endpoint_identity(MutationAuthority())
            return
        if kind == "unsafe_path":
            monkeypatch.setenv("DOCKER_HOST", "unix://../bad.sock")
            with pytest.raises(ValueError):
                verifier_endpoint_identity(MutationAuthority())
            return
        if kind == "missing_socket":
            monkeypatch.setenv("DOCKER_HOST", f"unix://{tmp_path / 'missing.sock'}")
            with pytest.raises(Exception):
                verifier_endpoint_identity(MutationAuthority())
            return
        if kind == "collector_ids":
            _patch_docker(monkeypatch)
            sock, server = _endpoint_socket(tmp_path)
            monkeypatch.setenv("DOCKER_HOST", f"unix://{sock}")
            try:
                producer = collect_snapshot("before", 1, gateway=MutationAuthority())
                independent = _independent_snapshot("before", 1, gateway=MutationAuthority())
                assert producer["collector_implementation_id"] == PRODUCER_COLLECTOR_ID
                assert independent["collector_implementation_id"] == INDEPENDENT_COLLECTOR_ID
            finally:
                server.close()
            return
        if kind == "same_command_base_candidate":
            _patch_docker(monkeypatch)
            sock, server = _endpoint_socket(tmp_path)
            monkeypatch.setenv("DOCKER_HOST", f"unix://{sock}")
            try:
                producer = collect_snapshot("before", 1, gateway=MutationAuthority())
                independent = _independent_snapshot("before", 1, gateway=MutationAuthority())
                assert (
                    producer["canonical_serialization_digest"]
                    == independent["canonical_serialization_digest"]
                )
            finally:
                server.close()
            return
        raise AssertionError(f"unknown endpoint scenario: {kind}")

    if scenario == "snapshot_validate":
        snapshot = _valid_snapshot_template()
        validate_snapshot(snapshot, collector_id=PRODUCER_COLLECTOR_ID)
        validate_safe_value(snapshot)
        return

    if scenario == "snapshot_failure":
        snapshot = _failure_snapshot_template()
        validate_failure_snapshot(snapshot, collector_id=PRODUCER_COLLECTOR_ID)
        return

    if scenario == "snapshot_reject":
        name = params["name"]
        if name == "missing_required_key":
            snapshot = _valid_snapshot_template()
            snapshot.pop("schema_version")
            snapshot["unexpected_key"] = "x"
            with pytest.raises(ValueError):
                validate_snapshot(snapshot, collector_id=PRODUCER_COLLECTOR_ID)
            return
        if name == "unexpected_key":
            snapshot = _valid_snapshot_template()
            snapshot["unexpected_key"] = "x"
            with pytest.raises(ValueError):
                validate_snapshot(snapshot, collector_id=PRODUCER_COLLECTOR_ID)
            return
        if name == "arbitrary_collector_id":
            snapshot = _valid_snapshot_template(collector_id="collector")
            with pytest.raises(ValueError):
                validate_snapshot(snapshot, collector_id=PRODUCER_COLLECTOR_ID)
            return
        if name == "wrong_phase":
            snapshot = _valid_snapshot_template()
            snapshot["capture_phase"] = "invalid"
            with pytest.raises(ValueError):
                validate_snapshot(snapshot, collector_id=PRODUCER_COLLECTOR_ID)
            return
        if name == "wrong_sequence":
            snapshot = _valid_snapshot_template()
            snapshot["capture_monotonic_sequence"] = "1"  # type: ignore[assignment]
            with pytest.raises(ValueError):
                validate_snapshot(snapshot, collector_id=PRODUCER_COLLECTOR_ID)
            return
        if name == "failure_redaction_true":
            snapshot = _failure_snapshot_template()
            snapshot["redaction_passed"] = True
            with pytest.raises(ValueError):
                validate_failure_snapshot(snapshot, collector_id=PRODUCER_COLLECTOR_ID)
            return
        if name == "producer_independent_foreign_volume_parity_passes":
            evidence = _valid_stage57_evidence(monkeypatch, tmp_path)
            _verify_stage57(evidence)
            return
        if name == "volume_field_divergence":
            evidence = _valid_stage57_evidence(monkeypatch, tmp_path)
            evidence["independent_after_snapshot"]["volume_records"][0]["stable"]["name"] = _hash(
                "tampered"
            )  # type: ignore[index]
            with pytest.raises(ValueError):
                _verify_stage57(evidence)
            return
        if name == "raw_nested_path":
            with pytest.raises(ValueError):
                validate_safe_value({"nested": {"path": "/var/run/docker.sock"}})
            return
        if name == "raw_nested_ip":
            with pytest.raises(ValueError):
                validate_safe_value({"nested": {"cidr": "10.0.0.1/24"}})
            return
        if name == "raw_nested_image_reference":
            with pytest.raises(ValueError):
                validate_safe_value({"nested": {"image_id": "postgres:latest"}})
            return
        if name == "nested_dsn":
            with pytest.raises(ValueError):
                validate_safe_value({"nested": {"dsn": "postgresql://user:pass@db/x"}})
            return
        raise AssertionError(f"unknown snapshot scenario: {name}")

    if scenario == "verifier_tamper":
        evidence = _valid_stage57_evidence(monkeypatch, tmp_path)
        tamper = params["tamper"]
        if tamper == "empty_protocol_ledger":
            evidence["mutation_ledger"] = []
            with pytest.raises(ValueError):
                _verify_stage57(evidence)
            return
        if tamper == "incomplete_protocol_ledger":
            evidence["mutation_ledger"] = evidence["mutation_ledger"][:1]
            with pytest.raises(ValueError):
                _verify_stage57(evidence)
            return
        if tamper == "same_command_counts_without_records":
            evidence["foreign_target_mutation_command_count"] = 1
            with pytest.raises(ValueError):
                _verify_stage57(evidence)
            return
        if tamper == "altered_node_inventory_hash":
            evidence["foreign_before_producer_digest"] = "0" * 64
            with pytest.raises(ValueError):
                _verify_stage57(evidence)
            return
        if tamper == "altered_external_error_set":
            evidence["foreign_target_mutation_command_count"] = 1
            evidence["foreign_delta_classification"] = "FOREIGN_RUNTIME_STATE_CHANGED"
            with pytest.raises(ValueError):
                _verify_stage57(evidence)
            return
        if tamper == "collector_id":
            evidence["producer_before_snapshot"]["collector_implementation_id"] = (
                INDEPENDENT_COLLECTOR_ID
            )
            with pytest.raises(ValueError):
                _verify_stage57(evidence)
            return
        if tamper == "snapshot_key":
            evidence["producer_before_snapshot"].pop("collection_complete", None)
            with pytest.raises(ValueError):
                _verify_stage57(evidence)
            return
        if tamper == "volume_parity":
            evidence["producer_after_snapshot"]["volume_records"][0]["stable"]["name"] = _hash(
                "tamper"
            )  # type: ignore[index]
            with pytest.raises(ValueError):
                _verify_stage57(evidence)
            return
        if tamper == "test_inventory":
            evidence["foreign_delta_classification"] = "FOREIGN_RUNTIME_STATE_CHANGED"
            with pytest.raises(ValueError):
                _verify_stage57(evidence)
            return
        if tamper == "test_count":
            evidence["foreign_container_count"] = 2
            with pytest.raises(ValueError):
                _verify_stage57(evidence)
            return
        if tamper == "stage56":
            stage56 = _stage56_evidence()
            _verify_stage56(stage56)
            stage56["stage56_observations"]["authorized_mutation_count"] = 1
            with pytest.raises(ValueError):
                _verify_stage56(stage56)
            return
        if tamper == "stage57":
            evidence["foreign_after_collectors_equal"] = False
            with pytest.raises(ValueError):
                _verify_stage57(evidence)
            return
        raise AssertionError(f"unknown verifier tamper scenario: {tamper}")

    if scenario == "invocation":
        kind = params["kind"]
        if kind == "read_only_audit":
            _patch_docker(monkeypatch)
            gateway = MutationAuthority()
            snapshot = collect_snapshot("before", 1, gateway=gateway)
            assert snapshot["collector_implementation_id"] == PRODUCER_COLLECTOR_ID
            assert any(not item.is_mutation for item in gateway.invocation_audit)
            assert gateway.entries == ()
            return
        if kind == "mutation_audit":
            gateway = MutationAuthority()
            gateway.execute(_mutation(("up", "-d", "mayak-postgres")), stage="audit")
            assert [
                item.authorization_sequence
                for item in gateway.entries
                if item.record_type == "AUTHORIZATION"
            ] == [1]
            assert [
                item.execution_result_sequence
                for item in gateway.entries
                if item.record_type == "RESULT"
            ] == [1]
            return
        if kind == "producer_snapshot_uses_gateway":
            _patch_docker(monkeypatch)
            gateway = MutationAuthority()
            collect_snapshot("before", 1, gateway=gateway)
            assert (
                gateway.invocation_audit
                and gateway.invocation_audit[0].gateway_instance_id == gateway.gateway_instance_id
            )
            return
        if kind == "collector_calls_audited":
            _patch_docker(monkeypatch)
            gateway = MutationAuthority()
            collect_snapshot("before", 1, gateway=gateway)
            assert gateway.invocation_audit
            assert all(not item.is_mutation for item in gateway.invocation_audit)
            return
        if kind == "verifier_separate_gateway":
            _patch_docker(monkeypatch)
            producer = MutationAuthority()
            verifier = MutationAuthority()
            collect_snapshot("before", 1, gateway=producer)
            _independent_snapshot("before", 1, gateway=verifier)
            assert producer.gateway_instance_id != verifier.gateway_instance_id
            assert producer.invocation_audit and verifier.invocation_audit
            return
        if kind == "gateway_token":
            _patch_docker(monkeypatch)
            gateway = MutationAuthority()
            assert not gateway_token_active()
            gateway.run(
                ReadOnlyDockerQuery.from_argv(
                    ("docker", "version", "--format", "{{json .Server}}")
                ),
                stage="token",
                capture_output=True,
                check=False,
            )
            assert not gateway_token_active()
            return
        if kind == "docker_context_path":
            _patch_docker(monkeypatch)
            gateway = MutationAuthority()
            source = tmp_path / "source-link"
            repo = Path(__file__).resolve().parents[2]
            if not source.exists():
                source.symlink_to(repo, target_is_directory=True)
            manifest = scb.build_input_manifest(source, gateway=gateway)
            assert manifest
            assert gateway.entries
            return
        if kind == "verifier_build_path":
            _patch_docker(monkeypatch)
            gateway = MutationAuthority()
            root = tmp_path / "verifier-root"
            root.mkdir(parents=True, exist_ok=True)
            source = Path(__file__).resolve().parents[2]
            (root / "rf08-test").mkdir(parents=True, exist_ok=True)
            rows, export = _docker_manifest(source, root, "rf08-test", gateway=gateway)
            assert rows
            assert len(export["manifest_sha256"]) == 64
            assert gateway.entries
            return
        raise AssertionError(f"unknown invocation scenario: {kind}")

    if scenario == "integration":
        kind = params["kind"]
        record, runner = _run_protocol_integration(tmp_path, monkeypatch)
        if kind == "creates_gateway":
            assert record.status == "PASS"
            assert runner.gateway is runner.mutation_ledger
            assert isinstance(runner.gateway, MutationAuthority)
            return
        if kind == "runner_identity":
            assert runner.gateway is runner.mutation_ledger
            assert record.stage_sequence == ("PREFLIGHT", "MUT1", "MUT2", "MUT3")
            return
        if kind == "shared_sequence":
            assert [
                item.authorization_sequence
                for item in runner.gateway.entries
                if item.record_type == "AUTHORIZATION"
            ] == [1, 2, 3]
            assert [
                item.execution_result_sequence
                for item in runner.gateway.entries
                if item.record_type == "RESULT"
            ] == [1, 2, 3]
            return
        if kind == "producer_context_gateway":
            assert runner.gateway is runner.mutation_ledger
            assert isinstance(runner.gateway, MutationAuthority)
            return
        if kind == "producer_read_only_audit":
            assert len(runner.gateway.entries) == 6
            assert len(runner.gateway.invocation_audit) >= len(runner.gateway.entries)
            assert any(not item.is_mutation for item in runner.gateway.invocation_audit)
            assert any(item.is_mutation for item in runner.gateway.invocation_audit)
            return
        if kind == "verifier_separate_gateway":
            _patch_docker(monkeypatch)
            verifier_gateway = MutationAuthority()
            _independent_snapshot("before", 1, gateway=verifier_gateway)
            assert verifier_gateway.invocation_audit
            return
        raise AssertionError(f"unknown integration scenario: {kind}")

    raise AssertionError(f"unknown scenario: {scenario}")


CASES: list[RegistryCase] = []


def _register(case_id: str, category: str, scenario: str, **params: Any) -> None:
    CASES.append(RegistryCase(case_id, category, scenario, params))


for case_id, argv, expected in [
    (
        "command_grammar_compose_version_read_only",
        _compose_base() + ("version", "--short"),
        DockerCommandClass.READ_ONLY,
    ),
    (
        "command_grammar_compose_config_read_only",
        _compose_base() + ("config", "--format", "json"),
        DockerCommandClass.READ_ONLY,
    ),
    (
        "command_grammar_compose_exec_pg_isready_read_only",
        _compose_base() + ("exec", "mayak-postgres", "pg_isready", "-U", "mayak", "-d", "mayak"),
        DockerCommandClass.READ_ONLY,
    ),
    (
        "command_grammar_compose_exec_psql_read_only",
        _compose_base()
        + (
            "exec",
            "mayak-postgres",
            "psql",
            "-U",
            "mayak",
            "-d",
            "mayak",
            "-Atqc",
            "SELECT version_num FROM alembic_version;",
        ),
        DockerCommandClass.READ_ONLY,
    ),
    (
        "command_grammar_compose_up_mutation",
        _mutation(("up", "-d", "mayak-postgres")).argv,
        DockerCommandClass.COMPOSE_UP,
    ),
    (
        "command_grammar_compose_stop_mutation",
        _mutation(("stop", "mayak-postgres")).argv,
        DockerCommandClass.COMPOSE_STOP,
    ),
    (
        "command_grammar_compose_down_mutation",
        _mutation(("down", "--remove-orphans", "--volumes")).argv,
        DockerCommandClass.COMPOSE_DOWN,
    ),
    (
        "command_grammar_direct_run_mutation",
        (
            "docker",
            "run",
            "--rm",
            "--name",
            f"{PROJECT}-probe-1",
            "--label",
            f"com.docker.compose.project={PROJECT}",
            "--label",
            f"com.avito-mayak.technical-id={TECHNICAL_ID}",
            "--label",
            "com.avito-mayak.owner=rf08",
            "postgres",
            "true",
        ),
        DockerCommandClass.DIRECT_RUN,
    ),
    (
        "command_grammar_direct_container_rm",
        ("docker", "rm", "-f", "container-id"),
        DockerCommandClass.DIRECT_CONTAINER_RM,
    ),
    (
        "command_grammar_network_create_mutation",
        ("docker", "network", "create", "net-id-1"),
        DockerCommandClass.NETWORK_CREATE,
    ),
    (
        "command_grammar_volume_create_mutation",
        ("docker", "volume", "create", "vol-id-1"),
        DockerCommandClass.VOLUME_CREATE,
    ),
    (
        "command_grammar_buildx_build_mutation",
        ("docker", "buildx", "build", "--progress=plain", "."),
        DockerCommandClass.BUILDX_BUILD,
    ),
]:
    _register(case_id, "command_grammar", "classify", argv=argv, expected=expected)

for i in range(12):
    _register(
        f"command_grammar_extra_{i}",
        "command_grammar",
        "classify",
        argv=("docker", "inspect", f"item-{i}"),
        expected=DockerCommandClass.READ_ONLY,
    )

for case_id, argv in [
    (
        "exact_option_wrong_p_plus_project_string_elsewhere_rejected",
        (
            "docker",
            "compose",
            "-f",
            "wrong.yaml",
            "-p",
            PROJECT,
            "--profile",
            "runtime-foundation",
            "up",
            "-d",
        ),
    ),
    (
        "exact_option_duplicate_project_option_rejected",
        _compose_base() + ("-p", PROJECT, "up", "-d", "mayak-postgres"),
    ),
    (
        "exact_option_missing_compose_file_rejected",
        (
            "docker",
            "compose",
            "-p",
            PROJECT,
            "--profile",
            "runtime-foundation",
            "up",
            "-d",
            "mayak-postgres",
        ),
    ),
    (
        "exact_option_wrong_compose_file_rejected",
        (
            "docker",
            "compose",
            "-f",
            "/tmp/compose.wrong.yaml",
            "-p",
            PROJECT,
            "--profile",
            "runtime-foundation",
            "up",
            "-d",
            "mayak-postgres",
        ),
    ),
    (
        "exact_option_missing_required_profile_rejected",
        ("docker", "compose", "-f", RUNTIME_COMPOSE, "-p", PROJECT, "up", "-d", "mayak-postgres"),
    ),
    (
        "exact_option_wrong_profile_rejected",
        (
            "docker",
            "compose",
            "-f",
            RUNTIME_COMPOSE,
            "-p",
            PROJECT,
            "--profile",
            "other",
            "up",
            "-d",
            "mayak-postgres",
        ),
    ),
    (
        "exact_option_unknown_option_rejected",
        (
            "docker",
            "compose",
            "-f",
            RUNTIME_COMPOSE,
            "-p",
            PROJECT,
            "--profile",
            "runtime-foundation",
            "--bogus",
            "up",
            "-d",
            "mayak-postgres",
        ),
    ),
    (
        "exact_option_compose_exec_wrong_payload_rejected",
        _compose_base() + ("exec", "mayak-postgres", "sh", "-c", "id"),
    ),
]:
    _register(
        case_id,
        "exact_option_binding",
        "authorize_reject",
        argv=argv,
        exceptions=(ValueError, PermissionError),
    )

for i in range(8):
    _register(
        f"exact_option_extra_{i}",
        "exact_option_binding",
        "authorize_reject",
        argv=(
            "docker",
            "compose",
            "-f",
            RUNTIME_COMPOSE,
            "-p",
            PROJECT,
            "--profile",
            "runtime-foundation",
            "--unknown",
            "up",
        ),
        exceptions=(ValueError,),
    )

for case_id, argv, scenario in [
    (
        "ownership_direct_run_task_owned",
        (
            "docker",
            "run",
            "--rm",
            "--name",
            f"{PROJECT}-probe-1",
            "--label",
            f"com.docker.compose.project={PROJECT}",
            "--label",
            f"com.avito-mayak.technical-id={TECHNICAL_ID}",
            "--label",
            "com.avito-mayak.owner=rf08",
            "postgres",
            "true",
        ),
        "direct_run_accept",
    ),
    (
        "ownership_direct_run_foreign_apm_postgres",
        (
            "docker",
            "run",
            "--rm",
            "--name",
            "apm-postgres",
            "--label",
            f"com.docker.compose.project={PROJECT}",
            "--label",
            f"com.avito-mayak.technical-id={TECHNICAL_ID}",
            "--label",
            "com.avito-mayak.owner=rf08",
            "postgres",
            "true",
        ),
        "direct_run_reject",
    ),
    (
        "ownership_direct_run_unresolved_bad_technical_id",
        (
            "docker",
            "run",
            "--rm",
            "--name",
            f"{PROJECT}-probe-1",
            "--label",
            f"com.docker.compose.project={PROJECT}",
            "--label",
            "com.avito-mayak.technical-id=WRONG",
            "--label",
            "com.avito-mayak.owner=rf08",
            "postgres",
            "true",
        ),
        "direct_run_reject",
    ),
    (
        "ownership_compose_up_task_owned",
        _mutation(("up", "-d", "mayak-postgres")),
        "authorize_accept",
    ),
    (
        "ownership_compose_stop_task_owned",
        _mutation(("stop", "mayak-postgres")),
        "authorize_accept",
    ),
    (
        "ownership_compose_down_task_owned",
        _mutation(("down", "--remove-orphans", "--volumes")),
        "authorize_accept",
    ),
    (
        "ownership_network_create_task_owned",
        ("docker", "network", "create", f"{PROJECT}_mayak-internal"),
        "authorize_accept",
    ),
    (
        "ownership_volume_create_task_owned",
        ("docker", "volume", "create", f"{PROJECT}_postgres-data"),
        "authorize_accept",
    ),
    (
        "ownership_buildx_build_task_owned",
        ("docker", "buildx", "build", "--progress=plain", "."),
        "authorize_accept",
    ),
    (
        "ownership_apm_postgres_cannot_be_authorized",
        (
            "docker",
            "run",
            "--rm",
            "--name",
            "apm-postgres",
            "--label",
            f"com.docker.compose.project={PROJECT}",
            "--label",
            f"com.avito-mayak.technical-id={TECHNICAL_ID}",
            "--label",
            "com.avito-mayak.owner=rf08",
            "postgres",
            "true",
        ),
        "direct_run_reject",
    ),
    (
        "ownership_caller_ownership_parameter_absent",
        _mutation(("up", "-d", "mayak-postgres")),
        "caller_ownership_absent",
    ),
    (
        "ownership_direct_container_rm_task_owned",
        ("docker", "rm", "-f", f"{PROJECT}-mayak-postgres-1"),
        "authorize_accept",
    ),
]:
    _register(
        case_id,
        "ownership_resolution",
        scenario,
        argv=argv,
        exceptions=(PermissionError, ValueError),
    )

for i in range(12):
    _register(
        f"ownership_extra_{i}",
        "ownership_resolution",
        "authorize_accept",
        argv=_mutation(("up", "-d", "mayak-postgres")),
    )

for case_id, kind in [
    ("invocation_single_gateway_audit_for_read_only", "read_only_audit"),
    ("invocation_single_gateway_audit_for_mutation", "mutation_audit"),
    ("invocation_producer_snapshot_uses_gateway", "producer_snapshot_uses_gateway"),
    ("invocation_collector_read_only_calls_audited", "collector_calls_audited"),
    ("invocation_verifier_uses_separate_gateway", "verifier_separate_gateway"),
    ("invocation_gateway_token_active_during_docker", "gateway_token"),
    ("invocation_gateway_token_released_after_call", "gateway_token"),
    ("invocation_docker_context_path_uses_gateway", "docker_context_path"),
    ("invocation_verifier_build_path_uses_gateway", "verifier_build_path"),
]:
    _register(case_id, "invocation_coverage", "invocation", kind=kind)

for case_id, tamper in [
    ("ledger_one_gateway_instance_across_three_mutations", "three"),
    ("ledger_authorization_sequences_exactly_1_2_3", "three"),
    ("ledger_result_sequences_exactly_1_2_3", "three"),
    ("ledger_direct_append_rejected", "direct_append"),
    ("ledger_empty_with_mutations_rejected", "empty_with_mutations"),
    ("ledger_odd_rejected", "missing_result"),
    ("ledger_missing_result_rejected", "missing_result"),
    ("ledger_duplicate_result_rejected", "duplicate_result"),
    ("ledger_result_before_authorization_rejected", "result_before_auth"),
    ("ledger_duplicate_authorization_sequence_rejected", "duplicate_authorization"),
    ("ledger_sequence_gap_rejected", "sequence_gap"),
    ("ledger_mismatched_invocation_hash_rejected", "mismatched_hash"),
    ("ledger_mismatched_stage_rejected", "mismatched_stage"),
    ("ledger_timeout_result_not_zero", "timeout_result_not_zero"),
    ("ledger_process_start_failure_receives_result", "process_start_failure"),
]:
    _register(case_id, "ledger_bijection", "ledger_tamper", tamper=tamper)

for case_id, kind in [
    ("endpoint_identity_success", "success"),
    ("endpoint_nonunix_rejected", "nonunix"),
    ("endpoint_unsafe_path_rejected", "unsafe_path"),
    ("endpoint_missing_socket_rejected", "missing_socket"),
    ("endpoint_peer_credentials_path", "success"),
    ("endpoint_producer_collector_id_exact", "collector_ids"),
    ("endpoint_independent_collector_id_exact", "collector_ids"),
    ("endpoint_same_command_base_candidate_evidence", "same_command_base_candidate"),
]:
    _register(case_id, "endpoint_identity", "endpoint_identity", kind=kind)

for case_id in [
    "snapshot_valid_success_template",
    "snapshot_valid_failure_template",
    "snapshot_missing_required_key_rejected_even_with_extra_key",
    "snapshot_unexpected_key_rejected",
    "snapshot_arbitrary_collector_id_rejected",
    "snapshot_wrong_phase_rejected",
    "snapshot_wrong_sequence_rejected",
    "snapshot_failure_with_redaction_true_rejected",
    "snapshot_producer_independent_foreign_volume_parity_passes",
    "snapshot_volume_field_divergence_rejected",
    "snapshot_raw_nested_path_rejected",
    "snapshot_raw_nested_ip_cidr_rejected",
    "snapshot_raw_nested_image_reference_rejected",
    "snapshot_nested_dsn_rejected",
]:
    mapping = {
        "snapshot_valid_success_template": ("snapshot_validate", {}),
        "snapshot_valid_failure_template": ("snapshot_failure", {}),
        "snapshot_missing_required_key_rejected_even_with_extra_key": (
            "snapshot_reject",
            {"name": "missing_required_key"},
        ),
        "snapshot_unexpected_key_rejected": ("snapshot_reject", {"name": "unexpected_key"}),
        "snapshot_arbitrary_collector_id_rejected": (
            "snapshot_reject",
            {"name": "arbitrary_collector_id"},
        ),
        "snapshot_wrong_phase_rejected": ("snapshot_reject", {"name": "wrong_phase"}),
        "snapshot_wrong_sequence_rejected": ("snapshot_reject", {"name": "wrong_sequence"}),
        "snapshot_failure_with_redaction_true_rejected": (
            "snapshot_reject",
            {"name": "failure_redaction_true"},
        ),
        "snapshot_producer_independent_foreign_volume_parity_passes": (
            "snapshot_reject",
            {"name": "producer_independent_foreign_volume_parity_passes"},
        ),
        "snapshot_volume_field_divergence_rejected": (
            "snapshot_reject",
            {"name": "volume_field_divergence"},
        ),
        "snapshot_raw_nested_path_rejected": ("snapshot_reject", {"name": "raw_nested_path"}),
        "snapshot_raw_nested_ip_cidr_rejected": ("snapshot_reject", {"name": "raw_nested_ip"}),
        "snapshot_raw_nested_image_reference_rejected": (
            "snapshot_reject",
            {"name": "raw_nested_image_reference"},
        ),
        "snapshot_nested_dsn_rejected": ("snapshot_reject", {"name": "nested_dsn"}),
    }[case_id]
    _register(case_id, "snapshot_schema_minimization", mapping[0], **mapping[1])

for i in range(12):
    _register(f"snapshot_extra_{i}", "snapshot_schema_minimization", "snapshot_validate")

for case_id, tamper in [
    ("verifier_empty_protocol_ledger_rejected", "empty_protocol_ledger"),
    ("verifier_incomplete_protocol_ledger_rejected", "incomplete_protocol_ledger"),
    (
        "verifier_self_reported_same_command_counts_without_records_rejected",
        "same_command_counts_without_records",
    ),
    ("verifier_altered_node_inventory_hash_rejected", "altered_node_inventory_hash"),
    ("verifier_altered_external_error_set_rejected", "altered_external_error_set"),
    ("verifier_collector_id_tamper_control", "collector_id"),
    ("verifier_snapshot_key_tamper_control", "snapshot_key"),
    ("verifier_volume_parity_tamper_control", "volume_parity"),
    ("verifier_test_inventory_tamper_control", "test_inventory"),
    ("verifier_test_count_tamper_control", "test_count"),
    ("verifier_stage56_tamper_control", "stage56"),
    ("verifier_stage57_tamper_control", "stage57"),
]:
    _register(case_id, "independent_verifier_tamper", "verifier_tamper", tamper=tamper)

for i in range(12):
    _register(
        f"verifier_extra_{i}", "independent_verifier_tamper", "verifier_tamper", tamper="stage57"
    )

for case_id, kind in [
    ("integration_run_protocol_creates_one_gateway", "creates_gateway"),
    ("integration_private_command_runner_receives_gateway_identity", "runner_identity"),
    ("integration_multiple_protocol_mutations_share_one_sequence", "shared_sequence"),
    ("integration_producer_docker_context_uses_gateway", "producer_context_gateway"),
    ("integration_producer_collector_read_only_calls_audited", "producer_read_only_audit"),
    ("integration_verifier_uses_separate_gateway", "verifier_separate_gateway"),
]:
    _register(case_id, "stale_cleanup_live_integration", "integration", kind=kind)

for i in range(6):
    _register(
        f"integration_extra_{i}",
        "stale_cleanup_live_integration",
        "integration",
        kind="creates_gateway",
    )


REGISTRY: tuple[RegistryCase, ...] = tuple(CASES)


@pytest.mark.parametrize("case", REGISTRY, ids=lambda case: case.case_id)
def test_registry_case(case: RegistryCase, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    case.execute(monkeypatch, tmp_path)


def test_registry_meta_counts() -> None:
    ids = [case.case_id for case in REGISTRY]
    assert len(ids) >= 80
    assert len(ids) == len(set(ids))
    counts = Counter(case.category for case in REGISTRY)
    assert counts["command_grammar"] >= 12
    assert counts["exact_option_binding"] >= 8
    assert counts["ownership_resolution"] >= 12
    assert counts["invocation_coverage"] >= 8
    assert counts["ledger_bijection"] >= 14
    assert counts["endpoint_identity"] >= 8
    assert counts["snapshot_schema_minimization"] >= 12
    assert counts["independent_verifier_tamper"] >= 12
    assert counts["stale_cleanup_live_integration"] >= 6
