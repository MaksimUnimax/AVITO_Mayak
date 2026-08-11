"""Fail-closed RF26 H19 prerequisite and child-environment boundary."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
from pathlib import Path
from urllib.parse import urlsplit

from scripts.runtime.rf26_h19_postgres import _validated_state, provision

TECHNICAL_ID = "RF26-OBSERVABILITY-BACKUP-RECOVERY-01"
BUILDX_VERSION = "v0.34.1"
BUILDX_SHA256 = "f1332ddb9010bd0b72628266c3a906d9a6979848033df4c8d9bd2cd113bae12b"
REQUIRED = (
    "MAYAK_RF10_POSTGRES_DSN",
    "MAYAK_RF11_POSTGRES_PASSWORD_FILE",
    "MAYAK_RF11_POSTGRES_USER",
    "MAYAK_RF11_POSTGRES_HOST",
    "MAYAK_RF11_POSTGRES_PORT",
    "MAYAK_RF11_POSTGRES_DB",
)
HANDOFF_PATHS = ("RF26_H19_STATE_DIR", "RF26_H19_JUNIT_PATH", "RF26_H19_DIAGNOSTIC_PATH")
REMOVED_ENV = (
    "MAYAK_SECRETS_DIR",
    "RF26_SOURCE_DB",
    "RF26_TARGET_DB",
    "RF26_CONFLICT_DB",
    "RF26_SOURCE_DSN",
    "RF26_TARGET_DSN",
    "RF26_CONFLICT_DSN",
    "RF24_PG_TOOL_PREFIX",
)
PHASES = (
    "H19P_POSTGRES_PROVISION",
    "H19P_STATE_VALIDATION",
    "H19P_ENVIRONMENT_EXPORT",
    "H19P_DOCKER_IDENTITY",
    "H19P_COMPOSE_IDENTITY",
    "H19P_READY_FOR_PYTEST",
)
DB_RE = re.compile(r"rf26_h19_(?:rf10|rf11)_[0-9]+")


class PreflightFailure(RuntimeError):
    def __init__(self, classification: str, reason: str) -> None:
        super().__init__(reason)
        self.classification = classification
        self.safe_reason = reason


def _failure(exc: BaseException) -> tuple[str, str]:
    if isinstance(exc, PreflightFailure):
        return exc.classification, exc.safe_reason
    if isinstance(exc, FileNotFoundError):
        return "H19_STATE_INVALID", "required task-owned state is absent"
    if isinstance(exc, PermissionError):
        return "H19_STATE_INVALID", "required task-owned state is inaccessible"
    if isinstance(exc, ValueError):
        return "H19_STATE_INVALID", "task-owned H19 state failed bounded validation"
    return "H19_STATE_INVALID", "task-owned H19 prerequisite failed bounded validation"


def _write_diagnostic(
    path: Path, *, failed_phase: str, classification: str, reason: str, completed: list[str]
) -> None:
    data = {
        "schema_version": 1,
        "technical_id": TECHNICAL_ID,
        "source_sha": os.getenv("GITHUB_SHA", "unknown"),
        "github_run_id": os.getenv("GITHUB_RUN_ID", "unknown"),
        "attempt": os.getenv("GITHUB_RUN_ATTEMPT", "unknown"),
        "failed_phase": failed_phase,
        "exception_class": "PreflightFailure",
        "classification": classification,
        "safe_reason": reason,
        "completed_phases": completed,
        "h19_pytest_execution_count": 0,
    }
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(data, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8"
        )
    except OSError:
        fallback = {
            "schema_version": 1,
            "technical_id": TECHNICAL_ID,
            "failed_phase": "diagnostic_generation",
            "safe_reason": "bounded fallback",
            "h19_pytest_execution_count": 0,
        }
        path.write_text(json.dumps(fallback, sort_keys=True) + "\n", encoding="utf-8")


def _read_state(state_dir: Path, run_id: str) -> dict[str, str]:
    databases = _validated_state(run_id=run_id, state_dir=state_dir)
    if databases is None:
        raise RuntimeError("H19 state is not provisioned")
    marker = state_dir / "h19.env"
    if stat.S_IMODE(marker.stat().st_mode) != 0o600:
        raise RuntimeError("H19 state marker mode is unsafe")
    password_file = state_dir / "rf11-password"
    if stat.S_IMODE(password_file.stat().st_mode) != 0o600:
        raise RuntimeError("H19 password file mode is unsafe")
    values: dict[str, str] = {}
    for line in marker.read_text(encoding="utf-8").splitlines():
        key, sep, value = line.partition("=")
        if (
            not sep
            or key in values
            or not re.fullmatch(r"[A-Z0-9_]+", key)
            or "\n" in value
            or "\r" in value
        ):
            raise ValueError("H19 state marker has unsafe syntax")
        values[key] = value
    if tuple(sorted(values)) != tuple(sorted((*REQUIRED, "RF26_H19_RF10_DB", "RF26_H19_RF11_DB"))):
        raise ValueError("H19 state marker schema mismatch")
    if values["RF26_H19_RF10_DB"] != databases[0] or values["RF26_H19_RF11_DB"] != databases[1]:
        raise ValueError("H19 database identity mismatch")
    if values["MAYAK_RF11_POSTGRES_DB"] != databases[1]:
        raise ValueError("H19 RF11 database identity mismatch")
    if values["MAYAK_RF11_POSTGRES_PASSWORD_FILE"] != str(password_file):
        raise ValueError("H19 password-file identity mismatch")
    parsed = urlsplit(values["MAYAK_RF10_POSTGRES_DSN"])
    if (
        parsed.scheme != "postgresql+psycopg"
        or parsed.username != "mayak_migration"
        or parsed.hostname != values["MAYAK_RF11_POSTGRES_HOST"]
        or parsed.port != int(values["MAYAK_RF11_POSTGRES_PORT"])
        or parsed.path.lstrip("/") != databases[0]
    ):
        raise ValueError("H19 RF10 DSN identity mismatch")
    return {key: values[key] for key in REQUIRED}


def _append_env(
    path: Path, values: dict[str, str], state_dir: Path, junit: Path, diagnostic: Path
) -> None:
    if not path:
        raise ValueError("GITHUB_ENV is unavailable")
    with path.open("a", encoding="utf-8") as stream:
        for key in (*REQUIRED, *HANDOFF_PATHS):
            value = (
                values[key]
                if key in values
                else {
                    "RF26_H19_STATE_DIR": state_dir,
                    "RF26_H19_JUNIT_PATH": junit,
                    "RF26_H19_DIAGNOSTIC_PATH": diagnostic,
                }[key]
            )
            stream.write(f"{key}={value}\n")


def _plugin_identity(path: Path, *, missing: str, regular: str, executable: str) -> None:
    if not path.exists():
        raise PreflightFailure(missing, "task-owned Docker plugin is absent")
    if path.is_symlink() or not path.is_file():
        raise PreflightFailure(regular, "task-owned Docker plugin is not a regular file")
    if not os.access(path, os.X_OK):
        raise PreflightFailure(executable, "task-owned Docker plugin is not executable")


def _docker_identity(docker_bin: Path, compose_plugin: Path, buildx_plugin: Path) -> None:
    if not docker_bin.exists():
        raise PreflightFailure("DOCKER_BIN_MISSING", "pinned Docker client is absent")
    if docker_bin.is_symlink() or not docker_bin.is_file():
        raise PreflightFailure(
            "DOCKER_BIN_NOT_REGULAR", "pinned Docker client is not a regular file"
        )
    if not os.access(docker_bin, os.X_OK):
        raise PreflightFailure(
            "DOCKER_BIN_NOT_EXECUTABLE", "pinned Docker client is not executable"
        )
    resolved = shutil.which("docker")
    if resolved is None or Path(resolved).resolve() != docker_bin.resolve():
        raise PreflightFailure(
            "DOCKER_PATH_RESOLUTION_MISMATCH", "PATH does not resolve the pinned Docker client"
        )
    result = subprocess.run(
        [str(docker_bin), "version", "--format", "{{.Client.Version}}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise PreflightFailure(
            "DOCKER_CLIENT_COMMAND_FAILED", "pinned Docker client command failed"
        )
    if result.stdout.strip() != "29.2.1":
        raise PreflightFailure(
            "DOCKER_CLIENT_VERSION_MISMATCH", "pinned Docker client version is not 29.2.1"
        )
    server = subprocess.run(
        [str(docker_bin), "info", "--format", "{{.ServerVersion}}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if server.returncode != 0:
        raise PreflightFailure(
            "DOCKER_SERVER_UNREACHABLE", "Docker server is not reachable through the task socket"
        )
    _plugin_identity(
        compose_plugin,
        missing="COMPOSE_PLUGIN_MISSING",
        regular="COMPOSE_PLUGIN_NOT_REGULAR",
        executable="COMPOSE_PLUGIN_NOT_EXECUTABLE",
    )
    _plugin_identity(
        buildx_plugin,
        missing="BUILDX_PLUGIN_MISSING",
        regular="BUILDX_PLUGIN_NOT_REGULAR",
        executable="BUILDX_PLUGIN_NOT_EXECUTABLE",
    )
    if hashlib.sha256(buildx_plugin.read_bytes()).hexdigest() != BUILDX_SHA256:
        raise PreflightFailure("BUILDX_VERSION_MISMATCH", "Buildx plugin checksum is not v0.34.1")
    config = buildx_plugin.parent.parent
    if buildx_plugin.resolve() != (config / "cli-plugins" / "docker-buildx").resolve():
        raise PreflightFailure(
            "BUILDX_PLUGIN_IDENTITY_MISMATCH", "Buildx plugin path is not task-owned"
        )
    env = {**os.environ, "DOCKER_CONFIG": str(config)}
    buildx = subprocess.run(
        [str(docker_bin), "buildx", "version"],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    if buildx.returncode != 0:
        raise PreflightFailure("BUILDX_COMMAND_FAILED", "pinned Buildx command failed")
    version = re.search(r"\bv(\d+\.\d+\.\d+)(?:[-+][^\s]+)?\b", buildx.stdout)
    if version is None or f"v{version.group(1)}" != BUILDX_VERSION:
        raise PreflightFailure("BUILDX_VERSION_MISMATCH", "Buildx semantic version is not v0.34.1")


def _compose_identity(docker_bin: Path) -> None:
    result = subprocess.run(
        [str(docker_bin), "compose", "version"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise PreflightFailure("COMPOSE_COMMAND_FAILED", "pinned Compose command failed")
    if result.stdout.strip() != "Docker Compose version v5.0.2":
        raise PreflightFailure("COMPOSE_VERSION_MISMATCH", "pinned Compose version is not v5.0.2")


def _build_child_env(
    values: dict[str, str], *, state_dir: Path, junit: Path, diagnostic: Path
) -> dict[str, str]:
    child = dict(os.environ)
    for key in REMOVED_ENV:
        child.pop(key, None)
    child.update(values)
    child.update(
        {
            "RF26_H19_STATE_DIR": str(state_dir),
            "RF26_H19_JUNIT_PATH": str(junit),
            "RF26_H19_DIAGNOSTIC_PATH": str(diagnostic),
        }
    )
    if any(
        child.get(name) != "false"
        for name in (
            "MAYAK_AVITO_LIVE_ENABLED",
            "MAYAK_TELEGRAM_ENABLED",
            "MAYAK_MAX_ENABLED",
            "MAYAK_YOOKASSA_ENABLED",
            "MAYAK_EGRESS_AGENT_ENABLED",
        )
    ):
        raise PreflightFailure(
            "PROVIDER_DISABLED_POLICY_MISMATCH", "provider live policy is not disabled"
        )
    if any(name not in child for name in (*REQUIRED, *HANDOFF_PATHS)):
        raise PreflightFailure(
            "H19_ENV_HANDOFF_INVALID", "required H19 child environment is incomplete"
        )
    if any(name in child for name in REMOVED_ENV):
        raise PreflightFailure(
            "H19_ENV_HANDOFF_INVALID", "forbidden H8-H18 environment remains in H19 child"
        )
    return child


def run(args: argparse.Namespace) -> int:
    completed: list[str] = []
    phase = PHASES[0]
    try:
        provision(run_id=args.run_id, repo_root=args.repo_root, state_dir=args.state_dir)
        completed.append(phase)
        print(phase)
        phase = PHASES[1]
        values = _read_state(args.state_dir, args.run_id)
        completed.append(phase)
        print(phase)
        phase = PHASES[3]
        _docker_identity(args.docker_bin, args.compose_plugin, args.buildx_plugin)
        completed.append(phase)
        print(phase)
        phase = PHASES[4]
        _compose_identity(args.docker_bin)
        phase = PHASES[2]
        child_env = _build_child_env(
            values, state_dir=args.state_dir, junit=args.junit, diagnostic=args.diagnostic
        )
        if not child_env:
            raise PreflightFailure("H19_ENV_HANDOFF_INVALID", "H19 child environment proof failed")
        completed.append(phase)
        print(phase)
        _append_env(
            args.github_env,
            {**values, **{key: child_env[key] for key in HANDOFF_PATHS}},
            args.state_dir,
            args.junit,
            args.diagnostic,
        )
        completed.append(phase)
        print(phase)
        phase = PHASES[5]
        completed.append(phase)
        print(phase)
        return 0
    except Exception as exc:
        classification, reason = _failure(exc)
        _write_diagnostic(
            args.diagnostic,
            failed_phase=phase,
            classification=classification,
            reason=reason,
            completed=completed,
        )
        print(
            "RF26 H19 preflight failed "
            f"phase={phase} classification={classification} reason={reason}"
        )
        return 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--state-dir", type=Path, required=True)
    parser.add_argument("--github-env", type=Path, required=True)
    parser.add_argument("--junit", type=Path, required=True)
    parser.add_argument("--diagnostic", type=Path, required=True)
    parser.add_argument("--docker-bin", type=Path, required=True)
    parser.add_argument("--compose-plugin", type=Path, required=True)
    parser.add_argument("--buildx-plugin", type=Path, required=True)
    return run(parser.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
