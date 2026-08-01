from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from mayak.runtime.task_acceptance import TaskAcceptanceVerifierKind
from scripts.runtime.rf08_docker_authority import (
    RUNTIME_PROFILE,
    TASK_ACCEPTANCE_MAX_TIMEOUT_SECONDS,
    BootstrapAction,
    ComposeBinding,
    ComposeService,
    GatewayAuthority,
    PathCapability,
    PathCapabilityKind,
    TaskAcceptanceVerifierAction,
)

ROOT = Path(__file__).resolve().parents[2]
COMPOSE = ROOT / "compose.yaml"
TECHNICAL_ID = "RF-08-CORRECTIVE-ELIMINATE-HOST-EXECUTABLE-CONTENT-AUTHORITY-20260801-08"


def _gateway() -> GatewayAuthority:
    return GatewayAuthority.for_task_scope(
        technical_id=TECHNICAL_ID,
        project_name="avito-mayak-acceptance-rf30-inimage-20260801-08",
        compose_file=COMPOSE,
    )


def _action(gateway: GatewayAuthority) -> TaskAcceptanceVerifierAction:
    return TaskAcceptanceVerifierAction(
        binding=ComposeBinding.from_path(
            COMPOSE, project_name=gateway.task_project, profile=RUNTIME_PROFILE
        ),
        verifier_kind=TaskAcceptanceVerifierKind.RF30_SELF_PROOF,
        scope_digest=gateway.scope_digest,
    )


def test_fixed_in_image_route_has_no_host_content() -> None:
    gateway = _gateway()
    action = _action(gateway)
    gateway.issue(action, stage="fixed-route")
    tokens = gateway._build_docker_tokens(action)  # noqa: SLF001
    assert tokens[-5:] == (
        "-m",
        "mayak.runtime.task_acceptance",
        TECHNICAL_ID,
        gateway.task_project,
        "RF30_SELF_PROOF",
    )
    assert "-v" not in tokens and "--volume" not in tokens
    assert "python" in tokens
    assert "mayak-api" in tokens
    assert "10001:10001" in tokens
    assert "/opt/mayak" in tokens


def test_task_action_has_no_executable_content_fields() -> None:
    assert set(TaskAcceptanceVerifierAction.__dataclass_fields__) == {
        "binding",
        "verifier_kind",
        "scope_digest",
        "correlation_id",
    }
    with pytest.raises(TypeError):
        TaskAcceptanceVerifierAction(  # type: ignore[arg-type,call-arg]
            binding=None, verifier_id="x", verifier_path=Path("/tmp/x.py"), scope_digest="x"  # type: ignore[arg-type]
        )


def test_task_bootstrap_is_rejected_and_sealed_bootstrap_is_preserved() -> None:
    gateway = _gateway()
    binding = ComposeBinding.from_path(
        COMPOSE, project_name=gateway.task_project, profile=RUNTIME_PROFILE
    )
    adapter = PathCapability.from_path(
        ROOT / "scripts/runtime/rf09_public_bootstrap_adapter.py", kind=PathCapabilityKind.FILE
    )
    with pytest.raises(PermissionError, match="sealed RF-08-only"):
        gateway.issue(
            BootstrapAction(
                binding,
                ComposeService.DB_BOOTSTRAP,
                "run",
                "generation",
                adapter,
                gateway.scope_digest,
            ),
            stage="task-bootstrap",
        )
    sealed = GatewayAuthority()
    sealed_binding = ComposeBinding.from_path(
        COMPOSE, project_name="avito-mayak-rf08-secret-delivery", profile=RUNTIME_PROFILE
    )
    sealed.issue(
        BootstrapAction(sealed_binding, ComposeService.DB_BOOTSTRAP, "run", "generation", adapter),
        stage="sealed-bootstrap",
    )


def test_unknown_verifier_fails_closed() -> None:
    gateway = _gateway()
    action = _action(gateway)
    object.__setattr__(action, "verifier_kind", "caller.module")
    with pytest.raises((ValueError, TypeError)):
        gateway.issue(action, stage="unknown-verifier")


def test_result_contract_and_timeout_are_bounded(monkeypatch: pytest.MonkeyPatch) -> None:
    gateway = _gateway()
    action = _action(gateway)
    envelope = {
        "schema_version": "mayak-task-acceptance-v1",
        "technical_id": TECHNICAL_ID,
        "project": gateway.task_project,
        "verifier_id": "RF30_SELF_PROOF",
        "status": "PASS",
        "checks": {"authority": True},
    }
    seen: dict[str, object] = {}

    def fake_run(*args: object, **kwargs: object) -> SimpleNamespace:
        seen.update(kwargs)
        return SimpleNamespace(
            returncode=0, stdout=(json.dumps(envelope) + "\n").encode(), stderr=b""
        )

    monkeypatch.setattr("scripts.runtime.rf08_docker_authority.subprocess.run", fake_run)
    result = gateway.execute(gateway.issue(action, stage="issue"), stage="execute", timeout=999)
    assert result.payload is not None and result.payload.status == "PASS"
    assert seen["timeout"] == TASK_ACCEPTANCE_MAX_TIMEOUT_SECONDS
