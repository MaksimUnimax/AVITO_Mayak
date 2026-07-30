from __future__ import annotations

import subprocess
import hashlib
from dataclasses import replace
from pathlib import Path
from typing import Any, cast

import pytest

from scripts.runtime.rf08_docker_authority import (
    DockerCommandClass,
    MutationAuthority,
    ResolvedTaskResourceCapability,
    _compose_plan,
    _direct_plan,
    classify_docker_argv,
)

PROJECT = "avito-mayak-rf08-secret-delivery"
TECHNICAL_ID = "RF-08-CORRECTIVE-NONROOT-FILE-SECRET-DELIVERY-20260729-01"
REPO_ROOT = Path(__file__).resolve().parents[2]
REPO_COMPOSE = REPO_ROOT / "compose.yaml"
RUNTIME_COMPOSE = Path("/opt/avito-mayak-runtime/rf08-secret-delivery/compose.runtime.yaml")


def _completed(argv: tuple[str, ...], returncode: int = 0) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(argv, returncode, stdout="", stderr="")


def _compose_up_argv(compose_file: Path) -> tuple[str, ...]:
    return (
        "docker",
        "compose",
        "-f",
        str(compose_file),
        "-p",
        PROJECT,
        "--profile",
        "runtime-foundation",
        "up",
        "-d",
        "mayak-api",
    )


def test_authorization_is_recorded_before_subprocess_execution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    authority = MutationAuthority()
    seen: list[int] = []

    def fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        seen.append(len(authority.entries))
        argv = tuple(str(item) for item in args[0])
        assert kwargs.get("shell") is False
        return _completed(argv)

    monkeypatch.setattr("scripts.runtime.rf08_docker_authority.subprocess.run", fake_run)
    capability = authority.issue_from_argv(
        ("docker", "network", "create", f"{PROJECT}_mayak-internal"),
        stage="network-create",
    )
    authority.execute(capability, stage="network-create")
    assert seen == [0, 1, 1]
    assert [item.record_type for item in authority.entries] == ["AUTHORIZATION", "RESULT"]
    assert authority.entries[0].authorization_sequence == 1
    assert authority.entries[1].execution_result_sequence == 1
    authority.validate_complete(1)


def test_execution_result_references_prior_authorization(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    authority = MutationAuthority()

    def fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        argv = tuple(str(item) for item in args[0])
        assert kwargs.get("shell") is False
        return _completed(argv)

    monkeypatch.setattr("scripts.runtime.rf08_docker_authority.subprocess.run", fake_run)
    capability = authority.issue_from_argv(
        ("docker", "network", "create", f"{PROJECT}_mayak-internal"),
        stage="network-create",
    )
    authority.execute(capability, stage="network-create")
    auth, result = authority.entries
    assert auth.authorization_sequence == result.authorization_sequence == 1
    assert auth.invocation_sequence == result.invocation_sequence == 1
    assert result.execution_result_sequence == 1


def test_read_only_does_not_create_mutation_record() -> None:
    assert classify_docker_argv(("docker", "inspect", "abc")) == DockerCommandClass.READ_ONLY
    assert (
        classify_docker_argv(("docker", "version", "--format", "{{json .Server}}"))
        == DockerCommandClass.READ_ONLY
    )
    assert (
        classify_docker_argv(("docker", "system", "prune", "-f"))
        == DockerCommandClass.UNKNOWN_DOCKER_COMMAND
    )


def test_compose_binding_requires_exact_absolute_path_and_identity(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    authority = MutationAuthority()
    capability = authority.issue_from_argv(_compose_up_argv(REPO_COMPOSE), stage="compose")
    assert capability.compose_file == str(REPO_COMPOSE.resolve())
    assert capability.compose_file_digest == hashlib.sha256(REPO_COMPOSE.read_bytes()).hexdigest()

    if RUNTIME_COMPOSE.exists():
        runtime = authority.issue_from_argv(_compose_up_argv(RUNTIME_COMPOSE), stage="compose")
        assert runtime.compose_file == str(RUNTIME_COMPOSE.resolve())
        assert runtime.compose_generation_identity is not None

    with pytest.raises((ValueError, FileNotFoundError)):
        authority.issue_from_argv(
            _compose_up_argv(Path("/tmp/compose.yaml")),
            stage="compose",
        )
    with pytest.raises(ValueError):
        authority.issue_from_argv(
            _compose_up_argv(Path("compose.yaml")),
            stage="compose",
        )

    symlink = tmp_path / "compose.yaml"
    symlink.symlink_to(REPO_COMPOSE)
    with pytest.raises(ValueError):
        authority.issue_from_argv(_compose_up_argv(symlink), stage="compose")

    changed = tmp_path / "compose.yaml"
    changed.write_text("version: '3'\nservices: {}\n", encoding="utf-8")
    with pytest.raises(ValueError):
        authority.issue_from_argv(_compose_up_argv(changed), stage="compose")

    original_read_bytes = Path.read_bytes

    def fake_read_bytes(self: Path) -> bytes:
        if self == REPO_COMPOSE.resolve():
            return b"changed-compose"
        return original_read_bytes(self)

    tampered = authority.issue_from_argv(_compose_up_argv(REPO_COMPOSE), stage="compose")
    monkeypatch.setattr(Path, "read_bytes", fake_read_bytes, raising=False)
    with pytest.raises(PermissionError):
        authority.authorize(tampered, stage="compose")


def test_broad_unscoped_and_unknown_fail_closed() -> None:
    authority = MutationAuthority()
    with pytest.raises(ValueError):
        authority.issue_from_argv(("docker", "system", "prune", "-f"), stage="negative")
    with pytest.raises(ValueError):
        _compose_plan(
            (
                "docker",
                "compose",
                "-f",
                str(REPO_COMPOSE),
                "-p",
                PROJECT,
                "--profile",
                "runtime-foundation",
                "down",
            )
        )


def test_forged_and_reconstructed_capabilities_fail_before_subprocess(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    authority = MutationAuthority()
    seen: list[tuple[str, ...]] = []

    def fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        argv = tuple(str(item) for item in args[0])
        seen.append(argv)
        return _completed(argv)

    monkeypatch.setattr("scripts.runtime.rf08_docker_authority.subprocess.run", fake_run)
    capability = authority.issue_from_argv(
        ("docker", "network", "create", f"{PROJECT}_mayak-internal"),
        stage="capability",
    )
    seen.clear()
    copied = replace(capability)
    forged = replace(
        capability,
        gateway_instance_id=authority.gateway_instance_id,
        issuance_id="forged",
        seal="forged",
        command_class=DockerCommandClass.COMPOSE_DOWN.value,
        allowed_operations=("COMPOSE_DOWN",),
    )
    payload = capability.safe_dict()
    payload["allowed_operations"] = tuple(payload["allowed_operations"])
    manual = ResolvedTaskResourceCapability(seal="manual", **payload)

    with pytest.raises(PermissionError):
        authority.execute(copied, stage="copied")
    with pytest.raises(PermissionError):
        MutationAuthority().execute(copied, stage="cross-gateway")
    with pytest.raises(PermissionError):
        authority.authorize(forged, stage="forged")
    with pytest.raises(PermissionError):
        authority.execute(forged, stage="forged")
    with pytest.raises(PermissionError):
        authority.execute(manual, stage="manual")
    assert seen == []


def test_capability_is_single_use_and_ledger_tamper_is_detected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    authority = MutationAuthority()

    def fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        argv = tuple(str(item) for item in args[0])
        return _completed(argv)

    monkeypatch.setattr("scripts.runtime.rf08_docker_authority.subprocess.run", fake_run)
    capability = authority.issue_from_argv(
        ("docker", "network", "create", f"{PROJECT}_mayak-internal"),
        stage="audit",
    )
    authority.execute(capability, stage="audit")
    with pytest.raises(PermissionError):
        authority.execute(capability, stage="audit")
    with pytest.raises(AttributeError):
        authority.ledger.pop()  # type: ignore[attr-defined]
    cast(Any, authority._ledger).pop()
    with pytest.raises(ValueError):
        authority.validate_complete(1)
