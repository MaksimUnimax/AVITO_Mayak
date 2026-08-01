from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from scripts.runtime.rf08_docker_authority import (
    ComposeAction,
    ComposeBinding,
    ComposeOperation,
    ComposeService,
    GatewayAuthority,
    ObservationRequest,
    ObservationTemplate,
    PathCapability,
    PathCapabilityKind,
    ResourceKind,
    ResourceLifecycleAction,
    ResourceOperation,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
COMPOSE = REPO_ROOT / "compose.yaml"


def _completed(returncode: int = 0, stdout: bytes = b"", stderr: bytes = b"") -> SimpleNamespace:
    return SimpleNamespace(returncode=returncode, stdout=stdout, stderr=stderr)


def test_compose_binding_and_action_round_trip() -> None:
    binding = ComposeBinding.from_path(
        COMPOSE, project_name="avito-mayak-rf08-secret-delivery", profile="runtime-foundation"
    )
    assert binding.compose_file == str(COMPOSE.resolve())
    assert (
        binding.compose_file_digest
        == __import__("hashlib").sha256(COMPOSE.read_bytes()).hexdigest()
    )
    action = ComposeAction(
        binding=binding,
        service=ComposeService.POSTGRES,
        operation=ComposeOperation.UP,
        detach=True,
    )
    assert action.binding.project_name == "avito-mayak-rf08-secret-delivery"


def test_issue_execute_and_observe(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    gateway = GatewayAuthority()
    seen: list[tuple[str, ...]] = []

    def fake_run(*args: Any, **kwargs: Any) -> SimpleNamespace:
        argv = tuple(str(item) for item in args[0])
        seen.append(argv)
        if argv[:3] == ("docker", "version", "--format"):
            payload = {
                "Version": "26.0.0",
                "ApiVersion": "1.45",
                "MinAPIVersion": "1.24",
                "Os": "linux",
                "Arch": "amd64",
                "KernelVersion": "6.8.0",
            }
            return _completed(stdout=(json.dumps(payload) + "\n").encode())
        return _completed()

    monkeypatch.setattr("scripts.runtime.rf08_docker_authority.subprocess.run", fake_run)
    capability = gateway.issue(
        ResourceLifecycleAction(
            kind=ResourceKind.NETWORK,
            operation=ResourceOperation.CREATE,
            name="avito-mayak-rf08-secret-delivery_mayak-internal",
        ),
        stage="network-create",
    )
    execution = gateway.execute(capability, stage="network-create", timeout=1)
    assert execution.returncode == 0
    assert seen[0][:3] == ("docker", "network", "create")
    assert len(gateway.ledger) == 2

    observed = gateway.observe(
        ObservationRequest(template=ObservationTemplate.DAEMON_VERSION),
        stage="daemon-version",
        timeout=1,
    )
    assert observed.returncode == 0
    assert json.loads(observed.stdout)["Version"] == "26.0.0"


def test_compose_up_force_recreate_is_bounded(monkeypatch: pytest.MonkeyPatch) -> None:
    gateway = GatewayAuthority()
    seen: list[tuple[str, ...]] = []

    def fake_run(*args: Any, **kwargs: Any) -> SimpleNamespace:
        argv = tuple(str(item) for item in args[0])
        seen.append(argv)
        return _completed()

    monkeypatch.setattr("scripts.runtime.rf08_docker_authority.subprocess.run", fake_run)
    binding = ComposeBinding.from_path(
        COMPOSE, project_name="avito-mayak-rf08-secret-delivery", profile="runtime-foundation"
    )
    capability = gateway.issue(
        ComposeAction(
            binding=binding,
            service=ComposeService.POSTGRES,
            operation=ComposeOperation.UP,
            detach=True,
            force=True,
        ),
        stage="compose-up-force",
    )
    execution = gateway.execute(capability, stage="compose-up-force", timeout=1)
    assert execution.returncode == 0
    assert "--force-recreate" in seen[0]


def test_remove_requires_prior_capability() -> None:
    with pytest.raises(ValueError):
        ResourceLifecycleAction(
            kind=ResourceKind.NETWORK,
            operation=ResourceOperation.REMOVE,
            name="bad",
        )


def test_path_capability_requires_absolute(tmp_path: Path) -> None:
    file_path = tmp_path / "payload.txt"
    file_path.write_text("x", encoding="utf-8")
    cap = PathCapability.from_path(file_path, kind=PathCapabilityKind.FILE)
    assert cap.path == str(file_path.resolve())
    with pytest.raises(ValueError):
        PathCapability.from_path("relative.txt", kind=PathCapabilityKind.FILE)
