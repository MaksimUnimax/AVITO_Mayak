from __future__ import annotations

import subprocess
from dataclasses import replace
from pathlib import Path
from typing import Any, cast

import pytest

from scripts.runtime.rf08_docker_authority import (
    DockerCommandClass,
    MutationAuthority,
    _compose_plan,
    _direct_plan,
    classify_docker_argv,
)

PROJECT = "avito-mayak-rf08-secret-delivery"
TECHNICAL_ID = "RF-08-CORRECTIVE-NONROOT-FILE-SECRET-DELIVERY-20260729-01"


def _completed(argv: tuple[str, ...], returncode: int = 0) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(argv, returncode, stdout="", stderr="")


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
    plan = _direct_plan(
        (
            "docker",
            "network",
            "create",
            f"{PROJECT}_mayak-internal",
        )
    )
    authority.execute(plan, stage="network-create")
    assert seen == [0, 1]
    assert seen[-1] == 1
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
    plan = _direct_plan(("docker", "network", "create", f"{PROJECT}_mayak-internal"))
    authority.execute(plan, stage="network-create")
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


def test_compose_binding_requires_absolute_path() -> None:
    base = (
        "docker",
        "compose",
        "-f",
        str(Path("/tmp/compose.runtime.yaml")),
        "-p",
        PROJECT,
        "--profile",
        "runtime-foundation",
    )
    plan = _compose_plan(base + ("up", "-d", "mayak-api"))
    assert plan.is_mutation
    assert plan.compose_file == "/tmp/compose.runtime.yaml"
    migrate = _compose_plan(base + ("run", "--rm", "mayak-migrate"))
    assert migrate.command_class == DockerCommandClass.COMPOSE_RUN
    assert migrate.service == "mayak-migrate"
    probe = _compose_plan(
        base
        + (
            "run",
            "--rm",
            "--no-deps",
            "--user",
            "10001:10001",
            "--workdir",
            "/opt/mayak",
            "--entrypoint",
            "python",
            "mayak-api",
            "-c",
            "print(1)",
        )
    )
    assert probe.command_class == DockerCommandClass.COMPOSE_RUN
    assert probe.service == "mayak-api"
    with pytest.raises(ValueError):
        _compose_plan(
            (
                "docker",
                "compose",
                "-f",
                "compose.runtime.yaml",
                "-p",
                PROJECT,
                "--profile",
                "runtime-foundation",
                "up",
                "-d",
                "mayak-api",
            )
        )


def test_broad_unscoped_and_unknown_fail_closed() -> None:
    authority = MutationAuthority()
    with pytest.raises(ValueError):
        authority.authorize(_direct_plan(("docker", "system", "prune", "-f")), stage="negative")
    with pytest.raises(ValueError):
        _compose_plan(
            (
                "docker",
                "compose",
                "-f",
                "compose.runtime.yaml",
                "-p",
                PROJECT,
                "--profile",
                "runtime-foundation",
                "up",
                "-d",
                "mayak-api",
            )
        )


def test_foreign_and_unresolved_targets_fail_before_execution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    authority = MutationAuthority()

    def fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        argv = tuple(str(item) for item in args[0])
        assert kwargs.get("shell") is False
        if argv[:3] == ("docker", "container", "inspect"):
            return _completed(argv, returncode=1)
        raise AssertionError("subprocess must not be called")

    monkeypatch.setattr("scripts.runtime.rf08_docker_authority.subprocess.run", fake_run)
    foreign = _direct_plan(
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
        )
    )
    unresolved = _direct_plan(("docker", "rm", f"{PROJECT}-unresolved"))
    with pytest.raises(PermissionError):
        authority.execute(foreign, stage="cleanup")
    with pytest.raises(PermissionError):
        authority.execute(unresolved, stage="cleanup")
    assert [item.record_type for item in authority.entries] == [
        "AUTHORIZATION",
        "AUTHORIZATION",
    ]
    assert all(item.authorization_outcome == "REJECTED" for item in authority.entries)


def test_capability_is_gateway_bound_and_not_reconstructable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    authority = MutationAuthority()

    def fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        argv = tuple(str(item) for item in args[0])
        return _completed(argv)

    monkeypatch.setattr("scripts.runtime.rf08_docker_authority.subprocess.run", fake_run)
    plan = _direct_plan(("docker", "network", "create", f"{PROJECT}_mayak-internal"))
    capability = authority.authorize(plan, stage="capability")
    copied = replace(capability)
    with pytest.raises(PermissionError):
        MutationAuthority().execute(plan, stage="cross-gateway", capability=capability)
    with pytest.raises(PermissionError):
        authority.execute(plan, stage="copied", capability=copied)


def test_ledger_is_immutable_snapshot_and_validate_complete_detects_tamper(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    authority = MutationAuthority()

    def fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        argv = tuple(str(item) for item in args[0])
        return _completed(argv)

    monkeypatch.setattr("scripts.runtime.rf08_docker_authority.subprocess.run", fake_run)
    authority.execute(
        _direct_plan(("docker", "network", "create", f"{PROJECT}_mayak-internal")), stage="audit"
    )
    with pytest.raises(AttributeError):
        authority.ledger.pop()  # type: ignore[attr-defined]
    cast(Any, authority._ledger).pop()
    with pytest.raises(ValueError):
        authority.validate_complete(1)
