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
    DockerCommandFailure,
    GatewayAuthority,
    ObservationRequest,
    ObservationTemplate,
    PathCapability,
    PathCapabilityKind,
    ResourceKind,
    ResourceLifecycleAction,
    ResourceOperation,
)
from scripts.runtime.safe_compose_bootstrap import _compose_dispatch

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


def test_check_true_raises_bounded_failure_after_recording_and_consuming(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gateway = GatewayAuthority()

    def fake_run(*args: Any, **kwargs: Any) -> SimpleNamespace:
        return _completed(returncode=17, stderr=b"SYNTHETIC_SECRET_STDERR")

    monkeypatch.setattr("scripts.runtime.rf08_docker_authority.subprocess.run", fake_run)
    capability = gateway.issue(
        ResourceLifecycleAction(
            kind=ResourceKind.NETWORK,
            operation=ResourceOperation.CREATE,
            name="avito-mayak-rf08-secret-delivery_mayak-internal",
        ),
        stage="bounded-failure",
    )
    with pytest.raises(DockerCommandFailure) as error:
        gateway.execute(capability, stage="bounded-failure", check=True)
    assert error.value.returncode == 17
    assert "SYNTHETIC_SECRET_STDERR" not in str(error.value)
    assert gateway.ledger[-1].record_type == "RESULT"
    assert gateway.ledger[-1].returncode == 17
    assert gateway._issued[capability.capability_id].consumed  # noqa: SLF001
    with pytest.raises(PermissionError):
        gateway.execute(capability, stage="bounded-failure-retry", check=True)


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


def test_postgres_log_tail_is_exact_and_bounded() -> None:
    binding = ComposeBinding.from_path(
        COMPOSE, project_name="avito-mayak-rf08-secret-delivery", profile="runtime-foundation"
    )
    gateway = GatewayAuthority()
    request = ObservationRequest(
        template=ObservationTemplate.POSTGRES_LOG_TAIL,
        compose=binding,
        service=ComposeService.POSTGRES,
    )
    assert gateway._build_docker_tokens(request)[-5:] == (
        "logs", "--no-color", "--tail", "64", "mayak-postgres"
    )  # noqa: SLF001
    dispatch = _compose_dispatch(
        ("docker", "compose", "-f", str(COMPOSE), "-p", binding.project_name,
         "--profile", binding.profile, "logs", "--no-color", "--tail", "64", "mayak-postgres")
    )
    assert dispatch.semantic.template == ObservationTemplate.POSTGRES_LOG_TAIL


@pytest.mark.parametrize(
    "tail",
    [
        ("--no-color", "--tail", "65", "mayak-postgres"),
        ("--no-color", "--tail", "64", "foreign-service"),
        ("--tail", "64", "mayak-postgres", "--timestamps"),
    ],
)
def test_postgres_log_tail_rejects_foreign_or_unbounded_shape(tail: tuple[str, ...]) -> None:
    with pytest.raises(ValueError):
        _compose_dispatch(
            ("docker", "compose", "-f", str(COMPOSE),
             "-p", "avito-mayak-rf08-secret-delivery", "--profile", "runtime-foundation",
             "logs", *tail)
        )


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
