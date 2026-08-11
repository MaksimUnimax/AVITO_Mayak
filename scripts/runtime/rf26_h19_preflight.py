"""Fail-closed RF26 H19 prerequisite and child-environment boundary."""
from __future__ import annotations

import argparse
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
REQUIRED = (
    "MAYAK_RF10_POSTGRES_DSN",
    "MAYAK_RF11_POSTGRES_PASSWORD_FILE",
    "MAYAK_RF11_POSTGRES_USER",
    "MAYAK_RF11_POSTGRES_HOST",
    "MAYAK_RF11_POSTGRES_PORT",
    "MAYAK_RF11_POSTGRES_DB",
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


def _safe_reason(exc: BaseException) -> str:
    reason = type(exc).__name__
    if isinstance(exc, FileNotFoundError):
        return "required task-owned file or executable is absent"
    if isinstance(exc, PermissionError):
        return "required task-owned path is not accessible"
    return (
        reason
        if reason in {"ValueError", "RuntimeError", "OSError", "CalledProcessError"}
        else "preflight failure"
    )


def _write_diagnostic(path: Path, *, failed_phase: str, reason: str, completed: list[str]) -> None:
    data = {
        "schema_version": 1,
        "technical_id": TECHNICAL_ID,
        "source_sha": os.getenv("GITHUB_SHA", "unknown"),
        "github_run_id": os.getenv("GITHUB_RUN_ID", "unknown"),
        "attempt": os.getenv("GITHUB_RUN_ATTEMPT", "unknown"),
        "failed_phase": failed_phase,
        "exception_class": reason,
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
        for key in REQUIRED:
            stream.write(f"{key}={values[key]}\n")
        stream.write(f"RF26_H19_STATE_DIR={state_dir}\nRF26_H19_JUNIT_PATH={junit}\nRF26_H19_DIAGNOSTIC_PATH={diagnostic}\n")


def _docker_identity(docker_bin: Path, compose_plugin: Path) -> None:
    if (
        not docker_bin.is_file()
        or not os.access(docker_bin, os.X_OK)
        or shutil.which("docker") != str(docker_bin)
    ):
        raise RuntimeError("Docker binary identity mismatch")
    result = subprocess.run(
        [str(docker_bin), "version", "--format", "{{.Client.Version}}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.stdout.strip() != "29.2.1":
        raise RuntimeError("Docker client version mismatch")
    if not compose_plugin.is_file() or not os.access(compose_plugin, os.X_OK):
        raise RuntimeError("Compose plugin is absent")


def _compose_identity(docker_bin: Path) -> None:
    result = subprocess.run(
        [str(docker_bin), "compose", "version"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0 or result.stdout.strip() != "Docker Compose version v5.0.2":
        raise RuntimeError("Compose version mismatch")


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
        phase = PHASES[2]
        _append_env(args.github_env, values, args.state_dir, args.junit, args.diagnostic)
        completed.append(phase)
        print(phase)
        phase = PHASES[3]
        _docker_identity(args.docker_bin, args.compose_plugin)
        completed.append(phase)
        print(phase)
        phase = PHASES[4]
        _compose_identity(args.docker_bin)
        provider_flags = (
            "MAYAK_AVITO_LIVE_ENABLED",
            "MAYAK_TELEGRAM_ENABLED",
            "MAYAK_MAX_ENABLED",
            "MAYAK_YOOKASSA_ENABLED",
            "MAYAK_EGRESS_AGENT_ENABLED",
        )
        if any(os.getenv(name) != "false" for name in provider_flags):
            raise RuntimeError("provider-disabled policy mismatch")
        completed.append(phase)
        print(phase)
        phase = PHASES[5]
        completed.append(phase)
        print(phase)
        return 0
    except Exception as exc:
        _write_diagnostic(
            args.diagnostic,
            failed_phase=phase,
            reason=_safe_reason(exc),
            completed=completed,
        )
        print(f"RF26 H19 preflight failed phase={phase} reason={_safe_reason(exc)}")
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
    return run(parser.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
