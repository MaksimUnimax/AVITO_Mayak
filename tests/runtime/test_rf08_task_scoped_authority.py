from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from scripts.runtime.rf08_docker_authority import (
    RUNTIME_PROFILE,
    RUNTIME_ROOT,
    TECHNICAL_ID,
    ComposeAction,
    ComposeBinding,
    ComposeOperation,
    ComposeProjectTeardownAction,
    ComposeRunAction,
    ComposeService,
    GatewayAuthority,
    ImageAction,
    ImageOperation,
    PathCapability,
    PathCapabilityKind,
    ResourceKind,
    ResourceLifecycleAction,
    ResourceOperation,
)

ROOT = Path(__file__).resolve().parents[2]
TASK_ID = "RF-08-CORRECTIVE-REUSABLE-TASK-SCOPED-ACCEPTANCE-COMPOSE-AUTHORITY-20260801-07"
TASK_PROJECT = "avito-mayak-acceptance-rf12-20260801-03"


def _gateway(project: str = TASK_PROJECT, technical_id: str = TASK_ID) -> GatewayAuthority:
    return GatewayAuthority.for_task_scope(
        technical_id=technical_id, project_name=project, compose_file=ROOT / "compose.yaml"
    )


def _binding(project: str = TASK_PROJECT, profile: str = RUNTIME_PROFILE) -> ComposeBinding:
    return ComposeBinding.from_path(ROOT / "compose.yaml", project_name=project, profile=profile)


def _action(project: str = TASK_PROJECT, profile: str = RUNTIME_PROFILE) -> ComposeAction:
    return ComposeAction(
        binding=_binding(project, profile),
        service=ComposeService.POSTGRES,
        operation=ComposeOperation.UP,
    )


def test_default_gateway_remains_sealed() -> None:
    gateway = GatewayAuthority()
    assert gateway.scope.mode.value == "SEALED_RF08_PROOF"
    assert gateway.task_project == "avito-mayak-rf08-secret-delivery"
    assert gateway.technical_id == TECHNICAL_ID


def test_task_scope_accepts_exact_project_and_binds_identity() -> None:
    gateway = _gateway()
    capability = gateway.issue(_action(), stage="exact")
    assert gateway.scope.project_name == TASK_PROJECT
    assert capability.technical_id == TASK_ID
    assert capability.scope_digest == gateway.scope_digest
    assert isinstance(capability.semantic_action, ComposeAction)
    assert capability.semantic_action.binding.project_name == TASK_PROJECT


@pytest.mark.parametrize(
    "project",
    [
        "avito-mayak",
        "avito-mayak-acceptance",
        "avito-mayak-rf08-secret-delivery",
        "foreign",
        "",
        "avito-mayak-acceptance-rf12-20260801-03/evil",
        "avito-mayak-acceptance-rf12-20260801-03_unsafe",
        "avito-mayak-acceptance-rf12-20260801-03--",
        "-avito-mayak-acceptance-rf12-20260801-03",
    ],
)
def test_task_factory_rejects_non_exact_project_grammar(project: str) -> None:
    with pytest.raises(ValueError):
        _gateway(project)


def test_cross_scope_and_binding_mismatches_fail_closed() -> None:
    gateway = _gateway()
    with pytest.raises(ValueError):
        gateway.issue(_action("avito-mayak-acceptance-rf12-20260801-04"), stage="foreign")
    with pytest.raises(ValueError):
        gateway.issue(_action(TASK_PROJECT, "wrong-profile"), stage="profile")
    with pytest.raises(ValueError):
        gateway.issue(ComposeRunAction(_binding(), ComposeService.API), stage="service")


def test_capability_is_bound_to_gateway_and_immutable_technical_id() -> None:
    gateway = _gateway()
    capability = gateway.issue(_action(), stage="identity")
    with pytest.raises(FrozenInstanceError):
        capability.technical_id = "RF-12-OTHER"  # type: ignore[misc]
    with pytest.raises(AttributeError):
        gateway.technical_id = "RF-12-OTHER"  # type: ignore[misc]
    with pytest.raises(PermissionError):
        _gateway(technical_id="RF-12-OTHER").execute(capability, stage="cross-gateway")


def test_task_resource_names_require_scope_and_namespace() -> None:
    gateway = _gateway()
    with pytest.raises(PermissionError):
        gateway.issue(
            ResourceLifecycleAction(
                ResourceKind.NETWORK, ResourceOperation.CREATE, "foreign-network"
            ),
            stage="foreign-resource",
        )
    action = ResourceLifecycleAction(
        ResourceKind.NETWORK,
        ResourceOperation.CREATE,
        f"{TASK_PROJECT}_mayak-internal",
        scope_digest=gateway.scope_digest,
    )
    gateway.issue(action, stage="owned-resource")


def test_teardown_is_bounded_semantic_command() -> None:
    gateway = _gateway()
    capability = gateway.issue(
        ComposeProjectTeardownAction(_binding()), stage="teardown"
    )
    argv = gateway._build_docker_tokens(capability.semantic_action)  # noqa: SLF001
    assert argv == (
        "docker", "compose", "-f", str((ROOT / "compose.yaml").resolve()), "-p",
        TASK_PROJECT, "--profile", RUNTIME_PROFILE, "down", "--volumes", "--remove-orphans"
    )
    assert not hasattr(capability, "argv")


def test_sealed_project_still_requires_sealed_gateway() -> None:
    sealed = GatewayAuthority()
    binding = ComposeBinding.from_path(
        ROOT / "compose.yaml",
        project_name="avito-mayak-rf08-secret-delivery",
        profile=RUNTIME_PROFILE,
    )
    sealed.issue(
        ComposeAction(binding, ComposeService.POSTGRES, ComposeOperation.UP), stage="sealed"
    )
    with pytest.raises(ValueError):
        _gateway().issue(
            ComposeAction(binding, ComposeService.POSTGRES, ComposeOperation.UP), stage="wrong-mode"
        )


def _image_action(**overrides: object) -> ImageAction:
    context = RUNTIME_ROOT / "build-context" / "run" / "source"
    values: dict[str, object] = {
        "operation": ImageOperation.APPLICATION_BUILD,
        "context": PathCapability(PathCapabilityKind.DIRECTORY, str(context), "context"),
        "dockerfile": PathCapability(
            PathCapabilityKind.FILE, str(context / "Dockerfile"), "dockerfile"
        ),
        "output": PathCapability(
            PathCapabilityKind.DIRECTORY,
            str(RUNTIME_ROOT / "application-image-output"),
            "output",
        ),
        "tag": "avito-mayak:" + "a" * 40,
        "source_sha": "a" * 40,
        "lock_identity": "e1faff1ce0f4d5dfd35480ab59d5d599fddf05c38fcd16a26c52098511476ab6",
        "build_input_digest": "c" * 64,
        "platform": "linux/amd64",
    }
    values.update(overrides)
    return ImageAction(**values)  # type: ignore[arg-type]


def test_application_build_is_exact_and_bounded() -> None:
    gateway = GatewayAuthority()
    tokens = gateway._build_docker_tokens(_image_action())  # noqa: SLF001
    assert "--load" in tokens
    assert "--platform" in tokens and "linux/amd64" in tokens
    assert "--output" not in tokens
    for mutation in (
        {"platform": "linux/arm64"},
        {"source_sha": "d" * 40},
        {"lock_identity": "e" * 64},
        {"output": PathCapability(PathCapabilityKind.DIRECTORY, "/tmp/foreign", "foreign")},
        {
            "context": PathCapability(
                PathCapabilityKind.DIRECTORY, "/tmp/foreign-context", "foreign-context"
            )
        },
    ):
        with pytest.raises(ValueError):
            gateway._build_docker_tokens(_image_action(**mutation))  # noqa: SLF001


def test_image_cleanup_is_exact_and_never_foreign() -> None:
    gateway = _gateway()
    action = ResourceLifecycleAction(
        ResourceKind.IMAGE,
        ResourceOperation.REMOVE,
        "avito-mayak:" + "a" * 40,
        inspected_capability="typed-image-inspect",
        scope_digest=gateway.scope_digest,
    )
    capability = gateway.issue(action, stage="image-cleanup")
    assert gateway._build_docker_tokens(capability.semantic_action) == (  # noqa: SLF001
        "docker", "image", "rm", "avito-mayak:" + "a" * 40
    )
    for name in ("postgres:18-bookworm", "avito-mayak:foreign", "avito-mayak:../escape"):
        with pytest.raises(ValueError):
            gateway.issue(
                ResourceLifecycleAction(
                    ResourceKind.IMAGE,
                    ResourceOperation.REMOVE,
                    name,
                    inspected_capability="typed-image-inspect",
                    scope_digest=gateway.scope_digest,
                ),
                stage="foreign-image-cleanup",
            )
