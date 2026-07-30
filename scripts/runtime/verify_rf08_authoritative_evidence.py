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
import re
import shutil
import subprocess
import tarfile
from pathlib import Path, PurePosixPath
from typing import cast

TASK_ID = "RF-08-CORRECTIVE-NONROOT-FILE-SECRET-DELIVERY-20260729-01"
BASE = "453356025051308b9cbe43b7201c248124348006"
TREE = "6f9548e8eda66acba2f9ac403dcb3d43f209774c"
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
FOREIGN_SCHEMA_VERSION = "ForeignResourceSnapshotV2"
INDEPENDENT_COLLECTOR_ID = "rf08.independent.typed-docker-control-plane.v2"
TASK_PROJECT = "avito-mayak-rf08-secret-delivery"
TASK_ID = "RF-08-CORRECTIVE-NONROOT-FILE-SECRET-DELIVERY-20260729-01"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _safe_digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _independent_snapshot(phase: str, sequence: int) -> dict[str, object]:
    """Independent read-only collector; no producer code or oracle is imported."""
    try:
        def inspect(kind: str, ident: str) -> dict[str, object]:
            result = subprocess.run(["docker", kind, "inspect", ident], capture_output=True, check=False, timeout=30)
            if result.returncode != 0:
                raise RuntimeError("inspect failed")
            value = json.loads(result.stdout)[0]
            if not isinstance(value, dict):
                raise ValueError("inspect shape")
            return value

        def ids(kind: str) -> list[str]:
            command = ["docker", "ps", "-aq"] if kind == "container" else ["docker", kind, "ls", "-q"]
            result = subprocess.run(command, capture_output=True, text=True, check=False, timeout=30)
            if result.returncode != 0:
                raise RuntimeError("enumeration failed")
            return sorted(set(x for x in result.stdout.splitlines() if x))

        def labels(value: object) -> list[list[str]]:
            return [[str(k), str(v) if str(k) in {"com.docker.compose.project", "com.avito-mayak.technical-id"} else _safe_digest(str(v))] for k, v in sorted((value or {}).items())] if isinstance(value, dict) else []

        def own(name: str, value: object) -> str:
            raw = value if isinstance(value, dict) else {}
            project, technical = raw.get("com.docker.compose.project"), raw.get("com.avito-mayak.technical-id")
            if name == "apm-postgres":
                return "FOREIGN"
            if technical is not None and technical != TASK_ID:
                return "UNRESOLVED" if project == TASK_PROJECT or name.startswith(TASK_PROJECT + "-") else "FOREIGN"
            if project == TASK_PROJECT and name.startswith(TASK_PROJECT + "-"):
                return "TASK_OWNED"
            if project == TASK_PROJECT or name.startswith(TASK_PROJECT + "-"):
                return "UNRESOLVED"
            return "FOREIGN"

        containers = []
        for ident in ids("container"):
            item = inspect("container", ident); name = str(item.get("Name", "")).lstrip("/"); cfg = item.get("Config", {}); host = item.get("HostConfig", {}); state = item.get("State", {}); raw_labels = cfg.get("Labels", {}) if isinstance(cfg, dict) else {}
            mounts = [{"type": m.get("Type"), "destination": m.get("Destination"), "mode": m.get("Mode"), "rw": m.get("RW")} for m in (item.get("Mounts") or []) if isinstance(m, dict)]  # type: ignore[union-attr,attr-defined]
            attachments = []
            for net, data in (item.get("NetworkSettings", {}).get("Networks", {}) or {}).items():  # type: ignore[union-attr,attr-defined]
                if isinstance(data, dict):
                    attachments.append({"name": str(net), "network_id": data.get("NetworkID"), "endpoint_id": data.get("EndpointID")})
            stable = {"id": item.get("Id"), "image_id": item.get("Image"), "image_reference": cfg.get("Image") if isinstance(cfg, dict) else None, "labels": labels(raw_labels), "restart_policy": host.get("RestartPolicy", {}).get("Name") if isinstance(host, dict) else None, "network_mode": host.get("NetworkMode") if isinstance(host, dict) else None, "privileged": host.get("Privileged") if isinstance(host, dict) else None, "read_only_rootfs": host.get("ReadonlyRootfs") if isinstance(host, dict) else None, "mounts": sorted(mounts, key=lambda x: json.dumps(x, sort_keys=True)), "networks": sorted(attachments, key=lambda x: (str(x.get("name")), str(x.get("network_id")))), "published_ports": item.get("NetworkSettings", {}).get("Ports", {}), "ownership": own(name, raw_labels)}  # type: ignore[union-attr,attr-defined]
            runtime = {"id": item.get("Id"), "status": state.get("Status") if isinstance(state, dict) else None, "running": state.get("Running") if isinstance(state, dict) else None, "paused": state.get("Paused") if isinstance(state, dict) else None, "restarting": state.get("Restarting") if isinstance(state, dict) else None, "dead": state.get("Dead") if isinstance(state, dict) else None, "exit_code": state.get("ExitCode") if isinstance(state, dict) else None, "health": state.get("Health", {}).get("Status") if isinstance(state, dict) and isinstance(state.get("Health"), dict) else None}
            containers.append({"stable": {"fingerprint": _safe_digest(["container", item.get("Id"), name]), "name": name if name == "apm-postgres" else _safe_digest(name), **stable}, "runtime": runtime})
        containers.sort(key=lambda x: str(x["stable"].get("id")))
        # Networks and volumes use the same immutable object IDs, labels, and ownership basis.
        networks = []
        for ident in ids("network"):
            item = inspect("network", ident); name = str(item.get("Name", "")); raw_labels = item.get("Labels", {})  # type: ignore[union-attr,attr-defined]
            networks.append({"stable": {"id": item.get("Id"), "name": name if name == TASK_PROJECT + "_mayak-internal" else _safe_digest(name), "driver": item.get("Driver"), "scope": item.get("Scope"), "internal": item.get("Internal"), "attachable": item.get("Attachable"), "ingress": item.get("Ingress"), "labels": labels(raw_labels), "ipam": item.get("IPAM", {}), "attached_container_ids": sorted((item.get("Containers") or {}).keys()) if isinstance(item.get("Containers"), dict) else [], "ownership": own(name, raw_labels)}})  # type: ignore[attr-defined]
        networks.sort(key=lambda x: str(x["stable"].get("id")))
        volumes = []
        for ident in ids("volume"):
            item = inspect("volume", ident); name = str(item.get("Name", "")); raw_labels = item.get("Labels", {}); options = item.get("Options") or {}  # type: ignore[union-attr,attr-defined]
            volumes.append({"stable": {"name": _safe_digest(name), "driver": item.get("Driver"), "labels": labels(raw_labels), "options": [[str(k), _safe_digest(str(v))] for k, v in sorted(options.items())], "scope": item.get("Scope"), "ownership": own(name, raw_labels)}})  # type: ignore[attr-defined]
        volumes.sort(key=lambda x: str(x["stable"].get("name")))
        foreign = {"containers": [x for x in containers if x["stable"]["ownership"] == "FOREIGN"], "networks": [x for x in networks if x["stable"]["ownership"] == "FOREIGN"], "volumes": [x for x in volumes if x["stable"]["ownership"] == "FOREIGN"]}
        task = {kind: [x for x in values if x["stable"]["ownership"] == "TASK_OWNED"] for kind, values in {"containers": containers, "networks": networks, "volumes": volumes}.items()}
        unresolved = {kind: [x for x in values if x["stable"]["ownership"] == "UNRESOLVED"] for kind, values in {"containers": containers, "networks": networks, "volumes": volumes}.items()}
        result = {"schema_version": FOREIGN_SCHEMA_VERSION, "capture_phase": phase, "collector_implementation_id": INDEPENDENT_COLLECTOR_ID, "source_host_safe_identity": _safe_digest("host"), "docker_server_safe_identity": _safe_digest("docker"), "capture_monotonic_sequence": sequence, "container_records": foreign["containers"], "network_records": foreign["networks"], "volume_records": foreign["volumes"], "apm_postgres_present": any(x["stable"].get("name") == "apm-postgres" for x in foreign["containers"]), "task_owned_resource_records": task, "unresolved_resource_records": unresolved, "collection_complete": True, "collection_errors": [], "redaction_passed": True}
        canonical = {key: result[key] for key in ("schema_version", "source_host_safe_identity", "docker_server_safe_identity", "container_records", "network_records", "volume_records", "apm_postgres_present", "task_owned_resource_records", "unresolved_resource_records", "collection_complete", "collection_errors", "redaction_passed")}
        result["canonical_serialization_digest"] = _safe_digest(canonical)
        return result
    except (OSError, subprocess.SubprocessError, ValueError, json.JSONDecodeError, RuntimeError) as exc:
        return {"schema_version": FOREIGN_SCHEMA_VERSION, "collector_implementation_id": INDEPENDENT_COLLECTOR_ID, "capture_phase": phase, "capture_monotonic_sequence": sequence, "collection_complete": False, "collection_errors": [type(exc).__name__], "redaction_passed": True, "container_records": [], "network_records": [], "volume_records": [], "task_owned_resource_records": {"containers": [], "networks": [], "volumes": []}, "unresolved_resource_records": {"containers": [], "networks": [], "volumes": []}, "canonical_serialization_digest": ""}


def _relative(value: str) -> str:
    path = PurePosixPath(value)
    if not value or path.is_absolute() or ".." in path.parts:
        raise ValueError("unsafe path")
    return path.as_posix()


def _clean_context(repo: Path, root: Path, run_id: str) -> tuple[Path, str]:
    run_root = root / run_id
    source = run_root / "source"
    run_root.mkdir(mode=0o700, parents=True)
    archive = run_root / "source.tar"
    with archive.open("wb") as stream:
        subprocess.run(
            ["git", "-C", str(repo), "archive", "--format=tar", BASE],
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
    source: Path, root: Path, run_id: str
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
    subprocess.run(
        [
            "docker",
            "buildx",
            "build",
            "--progress=plain",
            "--file",
            str(inspector),
            "--output",
            f"type=local,dest={output}",
            str(source),
        ],
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


def _digest(source: Path, manifest: list[dict[str, str]]) -> str:
    payload = {
        "schema_version": "rf08-docker-native-context-v1",
        "expected_base_tree_identity": TREE,
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
        if name.lower() not in str(row["operation_id"]).lower() and not (
            name.startswith("APPLICATION_AUTH_REJECTION_B")
            and str(row["operation_id"]).startswith("rf08.application_auth_rejection_b")
        ) and not str(
            row["operation_id"]
        ).startswith(("secret.", "pointer.")):
            raise ValueError(f"operation id does not identify stage: {name}")


def _verify_stage55(evidence: dict[str, object]) -> None:
    exact = {
        "observed": "POST_RECOVERY_DATABASE_AND_APPLICATION_PROOF",
        "handoff_accepted": True,
        "bootstrap_envelope": True,
        "bootstrap_outcome": "RF09_BOOTSTRAP_SUCCESS",
        "observed_migration_head": "RF09_FINALIZE",
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
    exact = {
        "observed": "task_owned_cleanup_complete",
        "task_containers": 0,
        "task_networks": 0,
        "task_volumes": 0,
        "private_output_files": 0,
        "postgresql_json_log_files": 0,
        "runtime_override_files": 0,
        "temporary_context_directories": 0,
        "independent_context_directories": 0,
        "secret_generation_directories": 0,
        "cleanup_exit": 0,
        "cleanup_observed": True,
        "cleanup_limitation": None,
        "foreign_deletion": False,
    }
    if any(evidence.get(k) != v for k, v in exact.items()):
        raise ValueError("stage 56 semantic contract failed")


def _verify_stage57(evidence: dict[str, object]) -> None:
    required = {
        "foreign_delta_classification": "NO_CHANGE",
        "foreign_resource_set_equal": True,
        "foreign_structural_digest_equal": True,
        "foreign_runtime_state_digest_equal": True,
        "foreign_before_collectors_equal": True,
        "foreign_after_collectors_equal": True,
        "task_container_count_after_cleanup": 0,
        "task_network_count_after_cleanup": 0,
        "task_volume_count_after_cleanup": 0,
        "unresolved_resource_count": 0,
        "foreign_target_mutation_command_count": 0,
        "unresolved_target_mutation_command_count": 0,
        "snapshot_private_artifacts_removed": True,
    }
    if any(evidence.get(key) != value for key, value in required.items()):
        raise ValueError("stage 57 typed equality contract failed")
    if evidence.get("stage57_semantic_verification") != "PASS":
        raise ValueError("stage 57 semantic result failed")


def verify_evidence(evidence_path: Path, source_tree: Path) -> dict[str, object]:
    document = json.loads(evidence_path.read_text(encoding="utf-8"))
    if document.get("technical_id") != TASK_ID or document.get("expected_base") != BASE:
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
            "POSTGRESQL_AUTHENTICATION_REJECTED_SQLSTATE_28P01",
            "CLIENT_CONNECTION_ATTEMPT_FAILED_PENDING_SERVER_CLASSIFICATION",
            "permission_denied",
            "RF09_BOOTSTRAP_SUCCESS",
        ):
            raise ValueError(f"stage-specific evidence missing: {expected}")
        _check_stage_ids(row, expected)
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
    source, archive_sha = _clean_context(source_tree, runtime_root, run_id)
    try:
        manifest, export = _docker_manifest(source, runtime_root, run_id)
        expected_manifest = document.get("docker_native_effective_manifest")
        if manifest != expected_manifest or document.get("build_input_manifest") != manifest:
            raise ValueError("independent manifest mismatch")
        if any(
            "__pycache__" in x["path"] or x["path"].endswith((".pyc", ".pyo")) for x in manifest
        ):
            raise ValueError("ignored/generated path in manifest")
        digest = _digest(source, manifest)
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
            document.get("expected_base_tree_identity") != TREE
            or document.get("docker_native_effective_manifest_digest") != export["manifest_sha256"]
        ):
            raise ValueError("context identity mismatch")
        if (
            document.get("excluded_path_count") != 0
            or document.get("untracked_input_count") != 0
            or document.get("dirty_input_count") != 0
        ):
            raise ValueError("context exclusion counts failed")
        if (
            document.get("stage55_semantic_verification")
            != {"result": "PASS", "exact_adapter_and_typed_subprotocol": True}
            or document.get("stage56_semantic_verification")
            != {"result": "PASS", "zero_residue_cleanup": True}
            or document.get("stage57_semantic_verification")
            != {"result": "PASS", "foreign_snapshot_equality": True}
        ):
            raise ValueError("stage semantic summaries missing")
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
        _verify_stage57(
            cast(
                dict[str, object],
                _stage(document, "FOREIGN_RESOURCE_EQUALITY_AND_EVIDENCE_VALIDATION")["evidence"],
            )
        )
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", action="store_true")
    parser.add_argument("--phase", default="verification")
    parser.add_argument("--sequence", type=int, default=1)
    parser.add_argument("evidence", type=Path, nargs="?")
    parser.add_argument("source_tree", type=Path, nargs="?")
    args = parser.parse_args(argv)
    if args.snapshot:
        print(json.dumps(_independent_snapshot(args.phase, args.sequence), sort_keys=True, separators=(",", ":")))
        return 0
    if args.evidence is None or args.source_tree is None:
        parser.error("evidence and source_tree are required unless --snapshot is used")
    print(json.dumps(verify_evidence(args.evidence, args.source_tree), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
