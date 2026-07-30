#!/usr/bin/env python3
"""RF-08 sealed-plan acceptance harness.

This is a bounded live-mode wrapper around the producer, verifier, static
checks, and focused tests. It emits one redacted JSON result and exits nonzero
if any gate fails.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Final

REPO_ROOT: Final = Path(__file__).resolve().parents[2]
RUNTIME_ROOT: Final = Path("/opt/avito-mayak-runtime/rf08-secret-delivery")
VALIDATION_PYTHON: Final = RUNTIME_ROOT / "test-toolchain" / "venv" / "bin" / "python"
VALIDATION_UV: Final = RUNTIME_ROOT / "test-toolchain" / "venv" / "bin" / "uv"
VALIDATION_RUFF: Final = RUNTIME_ROOT / "test-toolchain" / "venv" / "bin" / "ruff"
VALIDATION_MYPY: Final = RUNTIME_ROOT / "test-toolchain" / "venv" / "bin" / "mypy"
VALIDATION_LINT_IMPORTS: Final = RUNTIME_ROOT / "test-toolchain" / "venv" / "bin" / "lint-imports"
VALIDATION_PYTEST: Final = RUNTIME_ROOT / "test-toolchain" / "venv" / "bin" / "pytest"
EVIDENCE_PATH: Final = (
    REPO_ROOT / "docs/07-quality/evidence/RF08_AUTHORITATIVE_SECRET_LIFECYCLE_PROOF_v1.json"
)
SOURCE_SHA: Final = "b43be0f0f007267126a8eac79248af7d79f344bb"


@dataclass(slots=True)
class GateResult:
    name: str
    ok: bool
    returncode: int
    command: list[str]


def _run(
    command: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def _gate(
    name: str,
    command: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
) -> tuple[GateResult, subprocess.CompletedProcess[str]]:
    proc = _run(command, cwd=cwd, env=env)
    return (
        GateResult(
            name=name,
            ok=proc.returncode == 0,
            returncode=proc.returncode,
            command=command,
        ),
        proc,
    )


def _bounded_output(
    proc: subprocess.CompletedProcess[str], *, limit: int = 4000
) -> dict[str, object]:
    return {
        "returncode": proc.returncode,
        "stdout": proc.stdout[:limit],
        "stderr": proc.stderr[:limit],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", default=True)
    parser.add_argument("--source-sha", default=SOURCE_SHA)
    parser.add_argument("--runtime-root", default=str(RUNTIME_ROOT))
    parser.add_argument("--evidence", default=str(EVIDENCE_PATH))
    args = parser.parse_args(argv)

    runtime_root = Path(args.runtime_root)
    evidence = Path(args.evidence)
    validation_python = VALIDATION_PYTHON

    gates: list[dict[str, object]] = []
    gate_results: list[GateResult] = []

    env = dict(os.environ)
    env["MAYAK_SOURCE_SHA"] = args.source_sha
    existing_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = (
        f"{REPO_ROOT}{os.pathsep}{existing_pythonpath}" if existing_pythonpath else str(REPO_ROOT)
    )

    python_gate, proc = _gate(
        "python-version",
        [str(validation_python), "-c", "import sys; print(sys.version.split()[0])"],
    )
    gates.append(
        {
            "name": python_gate.name,
            "ok": python_gate.ok,
            "returncode": python_gate.returncode,
            "command": python_gate.command,
            "output": _bounded_output(proc),
        }
    )
    gate_results.append(python_gate)

    uv_gate, proc = _gate("uv-version", [str(VALIDATION_UV), "--version"])
    gates.append(
        {
            "name": uv_gate.name,
            "ok": uv_gate.ok,
            "returncode": uv_gate.returncode,
            "command": uv_gate.command,
            "output": _bounded_output(proc),
        }
    )
    gate_results.append(uv_gate)

    producer_gate, proc = _gate(
        "producer-live",
        [
            str(validation_python),
            str(REPO_ROOT / "scripts/runtime/safe_compose_bootstrap.py"),
            "--root",
            str(runtime_root / "run-20260730-02"),
            "--source-sha",
            args.source_sha,
        ],
        cwd=REPO_ROOT,
        env=env,
    )
    gates.append(
        {
            "name": producer_gate.name,
            "ok": producer_gate.ok,
            "returncode": producer_gate.returncode,
            "command": producer_gate.command,
            "output": _bounded_output(proc),
        }
    )
    gate_results.append(producer_gate)

    verifier_gate, proc = _gate(
        "evidence-verifier",
        [
            str(validation_python),
            str(REPO_ROOT / "scripts/runtime/verify_rf08_authoritative_evidence.py"),
            str(evidence),
            str(REPO_ROOT),
        ],
        cwd=REPO_ROOT,
        env=env,
    )
    gates.append(
        {
            "name": verifier_gate.name,
            "ok": verifier_gate.ok,
            "returncode": verifier_gate.returncode,
            "command": verifier_gate.command,
            "output": _bounded_output(proc),
        }
    )
    gate_results.append(verifier_gate)

    ruff_gate, proc = _gate(
        "ruff",
        [
            str(VALIDATION_RUFF),
            "check",
            "scripts/runtime/rf08_docker_authority.py",
            "scripts/runtime/rf08_docker_context.py",
            "scripts/runtime/rf08_foreign_snapshot.py",
            "scripts/runtime/safe_compose_bootstrap.py",
            "scripts/runtime/verify_rf08_authoritative_evidence.py",
            "tests/runtime/test_rf08_adversarial_registry.py",
            "tests/runtime/test_rf08_docker_authority.py",
            "tests/runtime/test_rf08_safe_compose_bootstrap.py",
        ],
        cwd=REPO_ROOT,
        env=env,
    )
    gates.append(
        {
            "name": ruff_gate.name,
            "ok": ruff_gate.ok,
            "returncode": ruff_gate.returncode,
            "command": ruff_gate.command,
            "output": _bounded_output(proc),
        }
    )
    gate_results.append(ruff_gate)

    mypy_gate, proc = _gate(
        "mypy",
        [
            str(VALIDATION_MYPY),
            "--explicit-package-bases",
            "scripts/runtime/rf08_docker_authority.py",
            "scripts/runtime/rf08_docker_context.py",
            "scripts/runtime/rf08_foreign_snapshot.py",
            "scripts/runtime/safe_compose_bootstrap.py",
            "scripts/runtime/verify_rf08_authoritative_evidence.py",
        ],
        cwd=REPO_ROOT,
        env=env,
    )
    gates.append(
        {
            "name": mypy_gate.name,
            "ok": mypy_gate.ok,
            "returncode": mypy_gate.returncode,
            "command": mypy_gate.command,
            "output": _bounded_output(proc),
        }
    )
    gate_results.append(mypy_gate)

    import_linter_gate, proc = _gate(
        "import-linter",
        [str(VALIDATION_LINT_IMPORTS)],
        cwd=REPO_ROOT,
        env=env,
    )
    gates.append(
        {
            "name": import_linter_gate.name,
            "ok": import_linter_gate.ok,
            "returncode": import_linter_gate.returncode,
            "command": import_linter_gate.command,
            "output": _bounded_output(proc),
        }
    )
    gate_results.append(import_linter_gate)

    tests_gate, proc = _gate(
        "focused-tests",
        [
            str(VALIDATION_PYTEST),
            "tests/runtime/test_rf08_docker_authority.py",
            "tests/runtime/test_rf08_docker_guard.py",
            "tests/runtime/test_rf08_adversarial_registry.py",
            "tests/runtime/test_rf08_safe_compose_bootstrap.py",
        ],
        cwd=REPO_ROOT,
        env=env,
    )
    gates.append(
        {
            "name": tests_gate.name,
            "ok": tests_gate.ok,
            "returncode": tests_gate.returncode,
            "command": tests_gate.command,
            "output": _bounded_output(proc),
        }
    )
    gate_results.append(tests_gate)

    accepted = all(item.ok for item in gate_results)
    payload = {
        "accepted": accepted,
        "source_sha": args.source_sha,
        "evidence": str(evidence),
        "runtime_root": str(runtime_root),
        "gates": [
            {
                "name": gate["name"],
                "ok": gate["ok"],
                "returncode": gate["returncode"],
            }
            for gate in gates
        ],
    }
    print(json.dumps(payload, sort_keys=True))
    return 0 if accepted else 1


if __name__ == "__main__":
    raise SystemExit(main())
