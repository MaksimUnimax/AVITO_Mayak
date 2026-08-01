from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

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
    parse_task_acceptance_output,
)

ROOT = Path(__file__).resolve().parents[2]
COMPOSE = ROOT / "compose.yaml"
TECHNICAL_ID = "RF-08-CORRECTIVE-REUSABLE-TASK-SCOPED-ACCEPTANCE-COMPOSE-AUTHORITY-20260801-07"


def _gateway(project: str = "avito-mayak-acceptance-rf30-runner-20260801-07") -> GatewayAuthority:
    return GatewayAuthority.for_task_scope(
        technical_id=TECHNICAL_ID, project_name=project, compose_file=COMPOSE
    )


def _verifier() -> Path:
    return ROOT / "scripts/runtime/task_acceptance/rf30_self_proof.py"


def _action(gateway: GatewayAuthority) -> TaskAcceptanceVerifierAction:
    binding = ComposeBinding.from_path(
        COMPOSE, project_name=gateway.task_project, profile=RUNTIME_PROFILE
    )
    path = _verifier()
    return TaskAcceptanceVerifierAction(
        binding=binding,
        verifier_id="rf30_self_proof",
        verifier_path=PathCapability.from_path(path, kind=PathCapabilityKind.FILE),
        scope_digest=gateway.scope_digest,
    )


@pytest.mark.parametrize("service", tuple(ComposeService))
def test_task_bootstrap_is_always_rejected(service: ComposeService) -> None:
    gateway = _gateway()
    binding = ComposeBinding.from_path(
        COMPOSE, project_name=gateway.task_project, profile=RUNTIME_PROFILE
    )
    adapter = PathCapability.from_path(_verifier(), kind=PathCapabilityKind.FILE)
    with pytest.raises(PermissionError, match="sealed RF-08-only"):
        gateway.issue(
            BootstrapAction(binding, service, "run", "generation", adapter, gateway.scope_digest),
            stage="task-bootstrap-rejected",
        )


def test_sealed_bootstrap_requires_exact_adapter_and_service() -> None:
    gateway = GatewayAuthority()
    binding = ComposeBinding.from_path(
        COMPOSE, project_name="avito-mayak-rf08-secret-delivery", profile=RUNTIME_PROFILE
    )
    adapter = PathCapability.from_path(
        ROOT / "scripts/runtime/rf09_public_bootstrap_adapter.py", kind=PathCapabilityKind.FILE
    )
    gateway.issue(
        BootstrapAction(binding, ComposeService.DB_BOOTSTRAP, "run", "generation", adapter),
        stage="sealed-bootstrap-accepted",
    )
    with pytest.raises(ValueError):
        gateway.issue(
            BootstrapAction(binding, ComposeService.API, "run", "generation", adapter),
            stage="sealed-bootstrap-wrong-service",
        )
    alternate = PathCapability.from_path(_verifier(), kind=PathCapabilityKind.FILE)
    with pytest.raises(ValueError):
        gateway.issue(
            BootstrapAction(binding, ComposeService.DB_BOOTSTRAP, "run", "generation", alternate),
            stage="sealed-bootstrap-wrong-adapter",
        )


def test_task_verifier_shape_is_fixed_and_source_bound() -> None:
    gateway = _gateway()
    action = _action(gateway)
    capability = gateway.issue(action, stage="verifier-shape")
    tokens = gateway._build_docker_tokens(action)  # noqa: SLF001
    assert tokens[8:16] == (
        "run",
        "--rm",
        "--no-deps",
        "--user",
        "10001:10001",
        "--workdir",
        "/opt/mayak",
        "--entrypoint",
    )
    assert "mayak-api" in tokens
    assert tokens.count("-v") == 1
    assert "-e" not in tokens
    assert capability.semantic_action == action


def test_task_verifier_digest_tamper_rejected_before_transport(tmp_path: Path) -> None:
    gateway = _gateway()
    source = _verifier()
    action = _action(gateway)
    capability = gateway.issue(action, stage="verifier-issued-before-tamper")
    altered = source.read_bytes() + b"\n"
    source.write_bytes(altered)
    try:
        with pytest.raises(PermissionError):
            gateway.execute(capability, stage="tampered-verifier")
    finally:
        source.write_bytes(altered[:-1])


def test_task_verifier_scope_and_project_number_are_bound() -> None:
    gateway = _gateway()
    action = _action(gateway)
    with pytest.raises(PermissionError):
        gateway.issue(
            TaskAcceptanceVerifierAction(
                action.binding, action.verifier_id, action.verifier_path, "0" * 64
            ),
            stage="wrong-scope",
        )
    other = _gateway("avito-mayak-acceptance-rf12-runner-20260801-07")
    with pytest.raises(ValueError):
        other.issue(
            TaskAcceptanceVerifierAction(
                ComposeBinding.from_path(
                    COMPOSE, project_name=other.task_project, profile=RUNTIME_PROFILE
                ),
                action.verifier_id,
                action.verifier_path,
                other.scope_digest,
            ),
            stage="wrong-project-verifier",
        )


def test_acceptance_envelope_is_bounded_and_exact() -> None:
    gateway = _gateway()
    result = parse_task_acceptance_output(
        json.dumps(
            {
                "schema_version": "mayak-task-acceptance-v1",
                "technical_id": TECHNICAL_ID,
                "project": gateway.task_project,
                "verifier_id": "rf30_self_proof",
                "status": "PASS",
                "checks": {"authority": True, "count": 1},
            },
            separators=(",", ":"),
        )
        + "\n",
        b"",
        technical_id=TECHNICAL_ID,
        project=gateway.task_project,
        verifier_id="rf30_self_proof",
    )
    assert result.status == "PASS"
    for invalid in (b"{}\n", b"{}\nextra\n", b"x" * 20000, b"not json\n"):
        with pytest.raises(ValueError):
            parse_task_acceptance_output(
                invalid,
                b"",
                technical_id=TECHNICAL_ID,
                project=gateway.task_project,
                verifier_id="rf30_self_proof",
            )
    with pytest.raises(ValueError):
        parse_task_acceptance_output(
            b"{}\n",
            b"unexpected",
            technical_id=TECHNICAL_ID,
            project=gateway.task_project,
            verifier_id="rf30_self_proof",
        )


def test_verifier_execution_clamps_timeout_and_parses_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gateway = _gateway()
    action = _action(gateway)
    envelope = {
        "schema_version": "mayak-task-acceptance-v1",
        "technical_id": TECHNICAL_ID,
        "project": gateway.task_project,
        "verifier_id": "rf30_self_proof",
        "status": "FAIL",
        "checks": {"authority": False},
    }
    seen: dict[str, object] = {}

    def fake_run(*args: object, **kwargs: object) -> SimpleNamespace:
        seen.update(kwargs)
        return SimpleNamespace(
            returncode=0,
            stdout=(json.dumps(envelope, separators=(",", ":")) + "\n").encode(),
            stderr=b"",
        )

    monkeypatch.setattr("scripts.runtime.rf08_docker_authority.subprocess.run", fake_run)
    execution = gateway.execute(
        gateway.issue(action, stage="verifier-output"),
        stage="verifier-output-execute",
        timeout=TASK_ACCEPTANCE_MAX_TIMEOUT_SECONDS * 10,
    )
    assert seen["timeout"] == TASK_ACCEPTANCE_MAX_TIMEOUT_SECONDS
    assert execution.payload.status == "FAIL"


def test_path_capability_rejects_symlink(tmp_path: Path) -> None:
    target = tmp_path / "target.py"
    target.write_text("pass\n", encoding="utf-8")
    link = tmp_path / "rf30_link.py"
    link.symlink_to(target)
    with pytest.raises(ValueError):
        PathCapability.from_path(link, kind=PathCapabilityKind.FILE)
