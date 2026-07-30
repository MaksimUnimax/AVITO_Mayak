from __future__ import annotations

# mypy: ignore-errors

import ast
import json
import os
import shlex
import shutil
import socket
import subprocess
from pathlib import Path
from typing import Any

import pytest

from scripts.runtime import safe_compose_bootstrap as scb
from scripts.runtime.rf08_docker_authority import (
    MutationAuthority,
    ReadOnlyDockerQuery,
    gateway_token_active,
)
from scripts.runtime.rf08_foreign_snapshot import collect_snapshot
from scripts.runtime.verify_rf08_authoritative_evidence import (
    PRODUCER_COLLECTOR_ID,
    _docker_manifest,
    _independent_snapshot,
)

ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOTS = [ROOT / "scripts" / "runtime", ROOT / "src"]
ALLOWED_DOCKER_GATEWAY = ROOT / "scripts" / "runtime" / "rf08_docker_authority.py"


def _resolve(node: ast.AST, env: dict[str, Any]) -> Any:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        return env.get(node.id)
    if isinstance(node, ast.Tuple):
        items = [_resolve(item, env) for item in node.elts]
        return tuple(items) if all(item is not None for item in items) else None
    if isinstance(node, ast.List):
        items = [_resolve(item, env) for item in node.elts]
        return list(items) if all(item is not None for item in items) else None
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left, right = _resolve(node.left, env), _resolve(node.right, env)
        if isinstance(left, str) and isinstance(right, str):
            return left + right
        if isinstance(left, tuple) and isinstance(right, tuple):
            return left + right
        if isinstance(left, list) and isinstance(right, list):
            return left + right
    return None


def _command_tokens(value: Any) -> tuple[str, ...] | None:
    if isinstance(value, str):
        return tuple(shlex.split(value))
    if isinstance(value, (list, tuple)):
        tokens = tuple(str(item) for item in value)
        return tokens
    return None


def _is_docker_command(value: Any) -> bool:
    tokens = _command_tokens(value)
    if not tokens:
        return False
    return tokens[0] == "docker"


def test_repository_ast_guard_rejects_direct_docker_calls() -> None:
    findings: list[str] = []
    for root in SOURCE_ROOTS:
        for path in root.rglob("*.py"):
            if path == ALLOWED_DOCKER_GATEWAY:
                continue
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(path))
            env: dict[str, Any] = {}
            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.Assign)
                    and len(node.targets) == 1
                    and isinstance(node.targets[0], ast.Name)
                ):
                    resolved = _resolve(node.value, env)
                    if resolved is not None:
                        env[node.targets[0].id] = resolved
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                callee = node.func
                dotted = None
                if isinstance(callee, ast.Attribute) and isinstance(callee.value, ast.Name):
                    dotted = f"{callee.value.id}.{callee.attr}"
                if dotted not in {
                    "subprocess.run",
                    "subprocess.Popen",
                    "subprocess.call",
                    "subprocess.check_call",
                    "subprocess.check_output",
                    "os.system",
                    "os.popen",
                }:
                    continue
                if any(
                    keyword.arg == "shell"
                    and isinstance(keyword.value, ast.Constant)
                    and keyword.value.value is True
                    for keyword in node.keywords
                ):
                    findings.append(f"{path}:{node.lineno}: shell=True")
                    continue
                if dotted in {"os.system", "os.popen"}:
                    command = _resolve(node.args[0], env) if node.args else None
                    if _is_docker_command(command):
                        findings.append(f"{path}:{node.lineno}: docker via {dotted}")
                    continue
                if not node.args:
                    continue
                command = _resolve(node.args[0], env)
                if _is_docker_command(command):
                    findings.append(f"{path}:{node.lineno}: docker via {dotted}")
    assert not findings, "\n".join(findings)


def _fake_completed(
    argv: tuple[str, ...], stdout: str = "", *, text: bool = False
) -> subprocess.CompletedProcess[Any]:
    return subprocess.CompletedProcess(
        argv, 0, stdout=stdout if text else stdout.encode("utf-8"), stderr=b""
    )


def _fake_docker(
    argv: tuple[str, ...], *args: Any, **kwargs: Any
) -> subprocess.CompletedProcess[Any]:
    argv = tuple(argv)
    if not argv or argv[0] != "docker":
        return REAL_RUN(argv, *args, **kwargs)
    text = bool(kwargs.get("text", False))
    if argv[1] == "version" and "--format" in argv and "{{json .Server}}" in argv:
        payload = {
            "Version": "26.0.0",
            "ApiVersion": "1.45",
            "MinAPIVersion": "1.24",
            "Os": "linux",
            "Arch": "amd64",
            "KernelVersion": "6.8.0",
        }
        return _fake_completed(argv, json.dumps(payload) + "\n", text=text)
    if argv[:2] == ("docker", "inspect"):
        ident = argv[2]
        if ident == "apm-postgres":
            payload: dict[str, Any] | list[dict[str, Any]] = [
                {
                    "Id": "apm-postgres",
                    "Name": "/apm-postgres",
                    "Config": {
                        "Labels": {},
                        "Image": "postgres:18-bookworm",
                    },
                    "HostConfig": {
                        "NetworkMode": "bridge",
                        "Privileged": False,
                        "ReadonlyRootfs": True,
                        "RestartPolicy": {"Name": "always"},
                    },
                    "State": {
                        "Status": "running",
                        "Running": True,
                        "Paused": False,
                        "Restarting": False,
                        "Dead": False,
                        "ExitCode": 0,
                        "Health": {"Status": "healthy"},
                    },
                    "NetworkSettings": {
                        "Ports": {},
                        "Networks": {
                            "bridge": {
                                "NetworkID": "bridge-id",
                                "EndpointID": "bridge-endpoint",
                            }
                        },
                    },
                    "Mounts": [],
                }
            ]
        else:
            payload = [
                {
                    "Id": ident,
                    "Name": f"/{ident}",
                    "Config": {
                        "Labels": {},
                        "Image": "busybox:1.36",
                    },
                    "HostConfig": {
                        "NetworkMode": "bridge",
                        "Privileged": False,
                        "ReadonlyRootfs": True,
                        "RestartPolicy": {"Name": "always"},
                    },
                    "State": {
                        "Status": "running",
                        "Running": True,
                        "Paused": False,
                        "Restarting": False,
                        "Dead": False,
                        "ExitCode": 0,
                        "Health": {"Status": "healthy"},
                    },
                    "NetworkSettings": {
                        "Ports": {},
                        "Networks": {},
                    },
                    "Mounts": [],
                }
            ]
        return _fake_completed(argv, json.dumps(payload) + "\n", text=text)
    if argv[:2] == ("docker", "ps") and "-q" in argv:
        return _fake_completed(argv, "apm-postgres\n", text=text)
    if argv[:2] == ("docker", "network") and "ls" in argv and "-q" in argv:
        return _fake_completed(argv, "net-id-1\n", text=text)
    if argv[:2] == ("docker", "volume") and "ls" in argv and "-q" in argv:
        return _fake_completed(argv, "vol-id-1\n", text=text)
    if argv[:2] == ("docker", "buildx") and len(argv) > 2 and argv[2] == "build":
        output = None
        source = Path(argv[-1])
        for index, token in enumerate(argv):
            if token == "--output" and index + 1 < len(argv):
                value = argv[index + 1]
                if "dest=" in value:
                    output = Path(value.split("dest=", 1)[1].split(",", 1)[0])
                    break
        if output is not None:
            effective = output / "effective"
            effective.mkdir(mode=0o700, parents=True, exist_ok=True)
            for relative in ("pyproject.toml", "uv.lock", "README.md", "alembic.ini"):
                shutil.copy2(source / relative, effective / relative)
            if (source / "src").is_dir():
                shutil.copytree(source / "src", effective / "src", dirs_exist_ok=True)
            if (source / "alembic").is_dir():
                shutil.copytree(source / "alembic", effective / "alembic", dirs_exist_ok=True)
        return _fake_completed(argv, "", text=text)
    return _fake_completed(argv, "ok\n", text=text)


def _guarded_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[Any]:
    argv = args[0] if args else kwargs.get("args")
    if argv is None:
        return REAL_RUN(*args, **kwargs)
    if _is_docker_command(argv) and not gateway_token_active():
        raise RuntimeError("docker bypass blocked")
    if _is_docker_command(argv):
        return _fake_docker(tuple(argv), *args[1:], **kwargs)
    return REAL_RUN(*args, **kwargs)


REAL_RUN = subprocess.run
REAL_POPEN = subprocess.Popen
REAL_CALL = subprocess.call
REAL_CHECK_CALL = subprocess.check_call
REAL_CHECK_OUTPUT = subprocess.check_output
REAL_OS_SYSTEM = os.system
REAL_OS_POPEN = os.popen


def _guarded_popen(*args: Any, **kwargs: Any) -> Any:
    argv = args[0] if args else kwargs.get("args")
    if _is_docker_command(argv) and not gateway_token_active():
        raise RuntimeError("docker bypass blocked")
    return REAL_POPEN(*args, **kwargs)


def _guarded_call(*args: Any, **kwargs: Any) -> int:
    argv = args[0] if args else kwargs.get("args")
    if _is_docker_command(argv) and not gateway_token_active():
        raise RuntimeError("docker bypass blocked")
    return REAL_CALL(*args, **kwargs)


def _guarded_check_call(*args: Any, **kwargs: Any) -> int:
    argv = args[0] if args else kwargs.get("args")
    if _is_docker_command(argv) and not gateway_token_active():
        raise RuntimeError("docker bypass blocked")
    return REAL_CHECK_CALL(*args, **kwargs)


def _guarded_check_output(*args: Any, **kwargs: Any) -> bytes:
    argv = args[0] if args else kwargs.get("args")
    if _is_docker_command(argv) and not gateway_token_active():
        raise RuntimeError("docker bypass blocked")
    return REAL_CHECK_OUTPUT(*args, **kwargs)


def _guarded_system(command: str) -> int:
    if _is_docker_command(command) and not gateway_token_active():
        raise RuntimeError("docker bypass blocked")
    return REAL_OS_SYSTEM(command)


def _guarded_os_popen(command: str, *args: Any, **kwargs: Any) -> Any:
    if _is_docker_command(command) and not gateway_token_active():
        raise RuntimeError("docker bypass blocked")
    return REAL_OS_POPEN(command, *args, **kwargs)


def _endpoint_socket(tmp_path: Path) -> tuple[Path, Any]:
    sock = tmp_path / "docker.sock"
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(str(sock))
    server.listen(1)
    return sock, server


def test_dynamic_subprocess_guard_allows_gateway_and_rejects_bypass(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(subprocess, "run", _guarded_run)
    monkeypatch.setattr(subprocess, "Popen", _guarded_popen)
    monkeypatch.setattr(subprocess, "call", _guarded_call)
    monkeypatch.setattr(subprocess, "check_call", _guarded_check_call)
    monkeypatch.setattr(subprocess, "check_output", _guarded_check_output)
    monkeypatch.setattr(os, "system", _guarded_system)
    monkeypatch.setattr(os, "popen", _guarded_os_popen)

    sock, server = _endpoint_socket(tmp_path)
    monkeypatch.setenv("DOCKER_HOST", f"unix://{sock}")
    try:
        gateway = MutationAuthority()
        completed = gateway.run(
            ReadOnlyDockerQuery.from_argv(("docker", "version", "--format", "{{json .Server}}")),
            stage="guard",
            capture_output=True,
            check=False,
        )
        assert completed.returncode == 0
        with pytest.raises(RuntimeError):
            subprocess.run(["docker", "version", "--format", "{{json .Server}}"])

        producer = collect_snapshot("before", 1, gateway=MutationAuthority())
        assert producer["collector_implementation_id"] == PRODUCER_COLLECTOR_ID

        source = tmp_path / "source-link"
        repo = ROOT
        if not source.exists():
            source.symlink_to(repo, target_is_directory=True)
        manifest = scb.build_input_manifest(source, gateway=MutationAuthority())
        assert manifest

        verifier_gateway = MutationAuthority()
        independent = _independent_snapshot("before", 1, gateway=verifier_gateway)
        assert independent["collector_implementation_id"] != PRODUCER_COLLECTOR_ID

        root = tmp_path / "verifier-root"
        root.mkdir(parents=True, exist_ok=True)
        (root / "guard").mkdir(parents=True, exist_ok=True)
        rows, export = _docker_manifest(repo, root, "guard", gateway=MutationAuthority())
        assert rows
        assert len(export["manifest_sha256"]) == 64
    finally:
        server.close()
