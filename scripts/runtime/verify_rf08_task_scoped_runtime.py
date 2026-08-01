#!/usr/bin/env python3
"""Real Docker proof for the immutable RF-08 task-scoped Compose authority."""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import subprocess
from pathlib import Path
from typing import Any

from mayak.runtime.task_acceptance import TaskAcceptanceVerifierKind
from scripts.runtime.rf08_docker_authority import (
    RUNTIME_PROFILE,
    TECHNICAL_ID,
    ComposeAction,
    ComposeBinding,
    ComposeOperation,
    ComposeProjectTeardownAction,
    ComposeService,
    GatewayAuthority,
    ObservationRequest,
    ObservationTemplate,
    ResourceKind,
    TaskAcceptanceVerifierAction,
)

PROJECT = "avito-mayak-acceptance-rf30-inimage-20260801-08"
ROOT = Path(__file__).resolve().parents[2]
RUNTIME_ROOT = Path("/opt/avito-mayak-runtime/rf08-inimage-task-acceptance-20260801-08")
PROOF_IMAGE_DIGEST = "sha256:91070120fe709d63a469b4d16783693ac9afdf88120a4032073aa5eecd6e5eb5"
SECRET_ROOT = RUNTIME_ROOT / "secrets"
SECRET_NAMES = (
    "mayak_postgres_bootstrap_password_postgres",
    "mayak_postgres_bootstrap_password_runtime",
    "mayak_database_application_password",
    "mayak_database_migration_password",
    "mayak_session_signing_key",
)


def _observe(gateway: GatewayAuthority, template: ObservationTemplate, **kwargs: Any) -> str:
    result = gateway.observe(
        ObservationRequest(template=template, **kwargs), stage=f"runtime-{template.value}"
    )
    if result.returncode != 0:
        raise RuntimeError(f"observation failed: {template.value}")
    return result.stdout


def _inventory(gateway: GatewayAuthority) -> dict[str, tuple[str, ...]]:
    return {
        "containers": tuple(
            sorted(_observe(gateway, ObservationTemplate.CONTAINER_LIST).splitlines())
        ),
        "networks": tuple(sorted(_observe(gateway, ObservationTemplate.NETWORK_LIST).splitlines())),
        "volumes": tuple(sorted(_observe(gateway, ObservationTemplate.VOLUME_LIST).splitlines())),
    }


def _digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _write_synthetic_secrets() -> None:
    SECRET_ROOT.mkdir(parents=True, exist_ok=True)
    os.chmod(SECRET_ROOT, 0o700)
    for name in SECRET_NAMES:
        path = SECRET_ROOT / name
        path.write_bytes(secrets.token_bytes(32))
        os.chmod(path, 0o600)


def main() -> int:
    proof_source_sha = subprocess.check_output(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True
    ).strip()
    _write_synthetic_secrets()
    os.environ.update(
        {
            "MAYAK_SECRETS_ROOT": str(SECRET_ROOT),
            "MAYAK_SOURCE_SHA": proof_source_sha,
            "MAYAK_LOCK_IDENTITY": "rf08-task-scoped-candidate-lock",
            "MAYAK_IMAGE_DIGEST": PROOF_IMAGE_DIGEST,
        }
    )
    gateway = GatewayAuthority.for_task_scope(
        technical_id=TECHNICAL_ID, project_name=PROJECT, compose_file=ROOT / "compose.yaml"
    )
    binding = ComposeBinding.from_path(
        ROOT / "compose.yaml", project_name=PROJECT, profile=RUNTIME_PROFILE
    )
    before = _inventory(gateway)
    started = False
    try:
        up = gateway.issue(
            ComposeAction(binding, ComposeService.POSTGRES, ComposeOperation.UP, detach=True),
            stage="runtime-postgres-up",
        )
        execution = gateway.execute(up, stage="runtime-postgres-up-execute", timeout=120)
        if execution.returncode != 0:
            raise RuntimeError("postgres compose up failed")
        started = True
        ps = _observe(
            gateway,
            ObservationTemplate.COMPOSE_PS,
            compose=binding,
        )
        container_ids = tuple(item for item in ps.splitlines() if item)
        if len(container_ids) != 1:
            raise RuntimeError("task scope did not produce exactly one postgres container")
        container = gateway.observe(
            ObservationRequest(
                template=ObservationTemplate.CONTAINER_INSPECT,
                identity=container_ids[0],
                kind=ResourceKind.CONTAINER,
            ),
            stage="runtime-postgres-inspect",
        )
        if container.returncode != 0:
            raise RuntimeError("postgres inspect failed")
        inspected = container.payload[0]
        labels = inspected["Config"]["Labels"]
        if labels.get("com.docker.compose.project") != PROJECT:
            raise RuntimeError("Docker Compose project label mismatch")
        if inspected.get("HostConfig", {}).get("PortBindings"):
            raise RuntimeError("postgres has a host port")
        network = gateway.observe(
            ObservationRequest(
                template=ObservationTemplate.NETWORK_INSPECT,
                identity=f"{PROJECT}_mayak-internal",
                kind=ResourceKind.NETWORK,
            ),
            stage="runtime-network-inspect",
        )
        if network.returncode != 0 or not network.payload[0].get("Internal"):
            raise RuntimeError("task network is not internal")
        volume = gateway.observe(
            ObservationRequest(
                template=ObservationTemplate.VOLUME_INSPECT,
                identity=f"{PROJECT}_postgres-data",
                kind=ResourceKind.VOLUME,
            ),
            stage="runtime-volume-inspect",
        )
        if volume.returncode != 0:
            raise RuntimeError("task volume inspect failed")
        if volume.payload[0].get("Labels", {}).get("com.docker.compose.project") != PROJECT:
            raise RuntimeError("task volume ownership mismatch")
        health = gateway.observe(
            ObservationRequest(
                template=ObservationTemplate.CONTAINER_HEALTH,
                identity=container_ids[0],
                kind=ResourceKind.CONTAINER,
            ),
            stage="runtime-readiness",
        )
        if health.returncode != 0 or health.payload.get("health_status") not in {
            "healthy",
            "starting",
        }:
            raise RuntimeError("postgres readiness observation failed")
        verifier = gateway.issue(
            TaskAcceptanceVerifierAction(
                binding=binding,
                verifier_kind=TaskAcceptanceVerifierKind.RF30_SELF_PROOF,
                scope_digest=gateway.scope_digest,
            ),
            stage="runtime-task-acceptance-verifier",
        )
        verifier_execution = gateway.execute(
            verifier, stage="runtime-task-acceptance-verifier-execute", timeout=120
        )
        if verifier_execution.returncode != 0 or verifier_execution.payload is None:
            raise RuntimeError("task acceptance verifier failed")
        if verifier_execution.payload.status != "PASS":
            raise RuntimeError("task acceptance verifier did not pass")
        teardown = gateway.issue(
            ComposeProjectTeardownAction(binding),
            stage="runtime-teardown",
        )
        result = gateway.execute(teardown, stage="runtime-teardown-execute", timeout=120)
        if result.returncode != 0:
            raise RuntimeError("task teardown failed")
        started = False
        after = _inventory(gateway)
        if before != after:
            raise RuntimeError("foreign inventory changed")
        remaining = {
            key: tuple(item for item in value if PROJECT in item) for key, value in after.items()
        }
        if any(remaining.values()):
            raise RuntimeError("task resources remain")
        print(
            json.dumps(
                {
                    "project": PROJECT,
                    "scope_digest": gateway.scope_digest,
                    "foreign_inventory_digest": _digest(before),
                    "cleanup": "PASS",
                    "secrets": "synthetic-only",
                },
                sort_keys=True,
            )
        )
        return 0
    finally:
        if started:
            cleanup = gateway.issue(
                ComposeProjectTeardownAction(binding),
                stage="runtime-finally-teardown",
            )
            gateway.execute(cleanup, stage="runtime-finally-teardown-execute", timeout=120)
        for name in SECRET_NAMES:
            (SECRET_ROOT / name).unlink(missing_ok=True)
        try:
            SECRET_ROOT.rmdir()
            RUNTIME_ROOT.rmdir()
        except OSError:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
