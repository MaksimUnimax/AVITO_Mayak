# ruff: noqa: E501, I001
from __future__ import annotations

import os
import json
import subprocess
from pathlib import Path

import pytest

from scripts.runtime import rf26_h19_preflight as preflight


def test_child_process_receives_required_h19_names_without_value_output(
    tmp_path: Path, monkeypatch
) -> None:
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    password_file = state_dir / "rf11-password"
    password_file.write_text("synthetic-only\n")
    password_file.chmod(0o600)
    marker = state_dir / "h19.env"
    marker.write_text(
        "\n".join(
            (
                "MAYAK_RF10_POSTGRES_DSN=postgresql+psycopg://mayak_migration:synthetic-only@db:5432/rf26_h19_rf10_123",
                f"MAYAK_RF11_POSTGRES_PASSWORD_FILE={password_file}",
                "MAYAK_RF11_POSTGRES_USER=mayak_migration",
                "MAYAK_RF11_POSTGRES_HOST=db",
                "MAYAK_RF11_POSTGRES_PORT=5432",
                "MAYAK_RF11_POSTGRES_DB=rf26_h19_rf11_123",
                "RF26_H19_RF10_DB=rf26_h19_rf10_123",
                "RF26_H19_RF11_DB=rf26_h19_rf11_123",
            )
        )
        + "\n"
    )
    marker.chmod(0o600)
    monkeypatch.setattr(
        preflight,
        "_validated_state",
        lambda **_: ("rf26_h19_rf10_123", "rf26_h19_rf11_123"),
    )
    values = preflight._read_state(state_dir, "123")
    env_file = tmp_path / "github-env"
    preflight._append_env(
        values=values,
        path=env_file,
        state_dir=state_dir,
        junit=tmp_path / "junit",
        diagnostic=tmp_path / "diag",
    )
    child_env = dict(os.environ)
    for line in env_file.read_text().splitlines():
        key, value = line.split("=", 1)
        child_env[key] = value
    result = subprocess.run(
        [
            "python",
            "-c",
            "import os; print(','.join(sorted(k for k in os.environ if k.startswith('MAYAK_RF'))))",
        ],
        env=child_env,
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == ",".join(sorted(preflight.REQUIRED))
    assert "synthetic-only" not in result.stdout


@pytest.mark.parametrize(
    ("name", "docker", "compose", "expected"),
    [
        ("missing", Path("/tmp/rf26-no-such-docker"), Path("/tmp/compose"), "DOCKER_BIN_MISSING"),
        ("not-regular", Path("/tmp"), Path("/tmp/compose"), "DOCKER_BIN_NOT_REGULAR"),
    ],
)
def test_docker_identity_has_bounded_classification(name, docker, compose, expected) -> None:
    del name
    with pytest.raises(preflight.PreflightFailure) as error:
        preflight._docker_identity(docker, compose, Path("/tmp/buildx"))
    assert error.value.classification == expected


def test_atomic_handoff_does_not_append_on_failed_preflight(tmp_path: Path, monkeypatch) -> None:
    env_file = tmp_path / "github-env"
    env_file.write_text("RF26_SOURCE_DB=stage-local\n")
    before = env_file.read_bytes()
    monkeypatch.setenv("MAYAK_AVITO_LIVE_ENABLED", "false")
    monkeypatch.setenv("MAYAK_TELEGRAM_ENABLED", "false")
    monkeypatch.setenv("MAYAK_MAX_ENABLED", "false")
    monkeypatch.setenv("MAYAK_YOOKASSA_ENABLED", "false")
    monkeypatch.setenv("MAYAK_EGRESS_AGENT_ENABLED", "false")
    with pytest.raises(preflight.PreflightFailure):
        preflight._docker_identity(
            Path("/tmp/rf26-no-such-docker"), Path("/tmp/compose"), Path("/tmp/buildx")
        )
    assert env_file.read_bytes() == before
    assert not any(key.encode() in env_file.read_bytes() for key in preflight.REQUIRED)


def test_failed_run_keeps_github_env_byte_identical(tmp_path: Path, monkeypatch) -> None:
    env_file = tmp_path / "github-env"
    env_file.write_bytes(b"RF26_SOURCE_DB=stage-local\n")
    before = env_file.read_bytes()
    monkeypatch.setattr(preflight, "provision", lambda **_: None)
    monkeypatch.setattr(
        preflight,
        "_read_state",
        lambda *_args, **_kwargs: {key: "synthetic" for key in preflight.REQUIRED},
    )
    monkeypatch.setattr(
        preflight,
        "_docker_identity",
        lambda *_args: (_ for _ in ()).throw(
            preflight.PreflightFailure(
                "DOCKER_SERVER_UNREACHABLE",
                "Docker server is not reachable through the task socket",
            )
        ),
    )
    args = type(
        "Args",
        (),
        {
            "run_id": "123",
            "repo_root": tmp_path,
            "state_dir": tmp_path / "state",
            "github_env": env_file,
            "junit": tmp_path / "junit",
            "diagnostic": tmp_path / "diag",
            "docker_bin": tmp_path / "docker",
            "compose_plugin": tmp_path / "compose",
            "buildx_plugin": tmp_path / "buildx",
        },
    )()
    assert preflight.run(args) == 1
    assert env_file.read_bytes() == before
    diagnostic = (tmp_path / "diag").read_text()
    assert '"classification":"DOCKER_SERVER_UNREACHABLE"' in diagnostic
    assert '"h19_pytest_execution_count":0' in diagnostic


@pytest.mark.parametrize(
    ("kind", "expected"),
    [("missing", "BUILDX_PLUGIN_MISSING"), ("regular", "BUILDX_PLUGIN_NOT_REGULAR")],
)
def test_buildx_identity_classifications(
    kind: str, expected: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    docker = tmp_path / "docker"
    docker.write_bytes(b"docker")
    docker.chmod(0o755)
    compose = tmp_path / "docker-compose"
    compose.write_bytes(b"compose")
    compose.chmod(0o755)
    buildx = tmp_path / "docker-buildx"
    if kind == "regular":
        buildx.mkdir()
    monkeypatch.setattr(preflight.shutil, "which", lambda _: str(docker))
    def fake_run(argv, **kwargs):
        if argv[1:3] == ["version", "--format"]:
            return type("Result", (), {"returncode": 0, "stdout": "29.2.1\n"})()
        if argv[1:3] == ["info", "--format"]:
            return type("Result", (), {"returncode": 0, "stdout": "29.2.1\n"})()
        return type("Result", (), {"returncode": 0, "stdout": "Buildx version v0.34.1\n"})()
    monkeypatch.setattr(preflight.subprocess, "run", fake_run)
    with pytest.raises(preflight.PreflightFailure) as error:
        preflight._docker_identity(docker, compose, buildx)
    assert error.value.classification == expected


def test_child_env_required_and_forbidden_names(monkeypatch, tmp_path: Path) -> None:
    for name in preflight.REMOVED_ENV:
        monkeypatch.setenv(name, "stage-local")
    for name in (
        "MAYAK_AVITO_LIVE_ENABLED",
        "MAYAK_TELEGRAM_ENABLED",
        "MAYAK_MAX_ENABLED",
        "MAYAK_YOOKASSA_ENABLED",
        "MAYAK_EGRESS_AGENT_ENABLED",
    ):
        monkeypatch.setenv(name, "false")
    values = {name: f"synthetic-{name}" for name in preflight.REQUIRED}
    child = preflight._build_child_env(
        values, state_dir=tmp_path, junit=tmp_path / "junit", diagnostic=tmp_path / "diag"
    )
    assert all(name in child for name in (*preflight.REQUIRED, *preflight.HANDOFF_PATHS))
    assert all(name not in child for name in preflight.REMOVED_ENV)


def _run_args(tmp_path: Path):
    env_file = tmp_path / "github-env"
    env_file.write_bytes(b"seed=keep\n")
    return type("Args", (), {"run_id": "123", "repo_root": tmp_path, "state_dir": tmp_path / "state", "github_env": env_file, "junit": tmp_path / "junit", "diagnostic": tmp_path / "diag", "docker_bin": tmp_path / "docker", "compose_plugin": tmp_path / "compose", "buildx_plugin": tmp_path / "buildx"})()


def test_preflight_emits_exactly_seven_ordered_receipts(monkeypatch, tmp_path: Path, capsys) -> None:
    args = _run_args(tmp_path)
    monkeypatch.setattr(preflight, "provision", lambda **_: None)
    monkeypatch.setattr(preflight, "_read_state", lambda *_a, **_k: {key: "synthetic" for key in preflight.REQUIRED})
    monkeypatch.setattr(preflight, "_docker_identity", lambda *_a: None)
    monkeypatch.setattr(preflight, "_compose_plugin_identity", lambda *_a: None)
    monkeypatch.setattr(preflight, "_compose_identity", lambda *_a: None)
    monkeypatch.setattr(preflight, "_buildx_identity", lambda *_a: None)
    monkeypatch.setattr(preflight, "_build_child_env", lambda *a, **k: {name: "synthetic" for name in (*preflight.REQUIRED, *preflight.HANDOFF_PATHS)})
    monkeypatch.setattr(preflight, "_append_env", lambda *a, **k: None)
    assert preflight.run(args) == 0
    receipts = [line for line in capsys.readouterr().out.splitlines() if line.startswith("H19P_")]
    assert receipts == list(preflight.H19_PREREQUISITE_PHASES)
    assert len(receipts) == len(set(receipts)) == 7


@pytest.mark.parametrize(
    ("hook", "classification", "phase", "completed"),
    [
        ("_docker_identity", "DOCKER_CLIENT_COMMAND_FAILED", "H19P_DOCKER_IDENTITY", 2),
        ("_compose_identity", "COMPOSE_COMMAND_FAILED", "H19P_COMPOSE_IDENTITY", 3),
        ("_buildx_identity", "BUILDX_PLUGIN_MISSING", "H19P_BUILDX_IDENTITY", 4),
        ("_build_child_env", "H19_ENV_HANDOFF_INVALID", "H19P_ENVIRONMENT_EXPORT", 5),
        ("_append_env", "H19_ENV_HANDOFF_INVALID", "H19P_ENVIRONMENT_EXPORT", 5),
    ],
)
def test_preflight_failure_attribution_is_exact_and_atomic(monkeypatch, tmp_path: Path, capsys, hook, classification, phase, completed) -> None:
    args = _run_args(tmp_path)
    before = args.github_env.read_bytes()
    monkeypatch.setattr(preflight, "provision", lambda **_: None)
    monkeypatch.setattr(preflight, "_read_state", lambda *_a, **_k: {key: "synthetic" for key in preflight.REQUIRED})
    for name in ("_docker_identity", "_compose_plugin_identity", "_compose_identity", "_buildx_identity"):
        monkeypatch.setattr(preflight, name, lambda *_a: None)
    monkeypatch.setattr(preflight, "_build_child_env", lambda *a, **k: {name: "synthetic" for name in (*preflight.REQUIRED, *preflight.HANDOFF_PATHS)})
    monkeypatch.setattr(preflight, "_append_env", lambda *a, **k: None)
    if hook == "_build_child_env":
        monkeypatch.setattr(preflight, hook, lambda *_a, **_k: (_ for _ in ()).throw(preflight.PreflightFailure(classification, "synthetic failure")))
    else:
        monkeypatch.setattr(preflight, hook, lambda *_a, **_k: (_ for _ in ()).throw(preflight.PreflightFailure(classification, "synthetic failure")))
    assert preflight.run(args) == 1
    diagnostic = json.loads((tmp_path / "diag").read_text())
    assert diagnostic["failed_phase"] == phase
    assert diagnostic["classification"] == classification
    assert len(diagnostic["completed_phases"]) == completed
    assert args.github_env.read_bytes() == before
