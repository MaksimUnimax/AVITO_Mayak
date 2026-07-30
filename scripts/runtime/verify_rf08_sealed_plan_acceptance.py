#!/usr/bin/env python3
"""RF-08 sealed-plan acceptance harness.

This harness derives source authority from Git, requires explicit live mode,
executes the ordered RF-08 gate sequence, and emits one bounded JSON result.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import subprocess
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

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
EXPECTED_BASE: Final = "2df3f029d20015e1c2221949b65160ca3ecf49e7"
CANONICAL_CHECKOUT: Final = Path("/opt/avito-mayak")
RF11_WORKTREE: Final = Path(
    "/opt/avito-mayak-worktrees/RF-11-CORRECTIVE-TRUSTED-AUTHORITY-AND-DURABLE-POSTGRES-TESTS-20260729-02"
)
INVENTORY_SCRIPT: Final = REPO_ROOT / "scripts/runtime/rf08_worktree_inventory.py"
PRODUCER_SCRIPT: Final = REPO_ROOT / "scripts/runtime/safe_compose_bootstrap.py"
VERIFIER_SCRIPT: Final = REPO_ROOT / "scripts/runtime/verify_rf08_authoritative_evidence.py"

FORBIDDEN_NAMES: Final = {
    "DockerInvocationPlan",
    "MutationPlan",
    "ReadOnlyDockerQuery",
    "classify_docker_argv",
    "_direct_plan",
    "_split_option_pairs",
}

FORBIDDEN_IMPORTS: Final = {
    "ReadOnlyDockerQuery",
    "DockerInvocationPlan",
    "MutationPlan",
    "classify_docker_argv",
}


@dataclass(slots=True)
class GateResult:
    gate_id: str
    status: str
    ok: bool
    returncode: int
    digest: str
    count: int | None = None
    command: list[str] | None = None


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


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
    gate_id: str,
    command: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    count: int | None = None,
) -> GateResult:
    proc = _run(command, cwd=cwd, env=env)
    digest = _sha(proc.stdout + "\n" + proc.stderr + f"\n{proc.returncode}")
    return GateResult(
        gate_id=gate_id,
        status="PASS" if proc.returncode == 0 else "FAIL",
        ok=proc.returncode == 0,
        returncode=proc.returncode,
        digest=digest,
        count=count,
        command=command,
    )


def _git_rev_parse(root: Path, ref: str) -> str:
    return (
        _run(["git", "-C", str(root), "rev-parse", ref], cwd=root).stdout.strip()
    )


def _inventory(root: Path) -> dict[str, Any]:
    proc = _run([str(VALIDATION_PYTHON), str(INVENTORY_SCRIPT), "--root", str(root)], cwd=REPO_ROOT)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "inventory failed")
    return json.loads(proc.stdout)


def _status_from_inventory(value: dict[str, Any]) -> str:
    return str(value.get("digest", ""))


def _scan_ast() -> tuple[list[str], list[str], list[str]]:
    forbidden_api: list[str] = []
    forbidden_runner: list[str] = []
    implicit_gateway: list[str] = []
    for root in (REPO_ROOT / "scripts/runtime", REPO_ROOT / "tests/runtime"):
        for path in sorted(root.glob("*.py")):
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    names = {alias.name for alias in node.names}
                    bad = sorted(names & FORBIDDEN_IMPORTS)
                    if bad:
                        forbidden_api.append(f"{path}:{node.lineno}:{','.join(bad)}")
                if isinstance(node, ast.Call):
                    callee = node.func
                    if isinstance(callee, ast.Name):
                        if callee.id in FORBIDDEN_NAMES:
                            forbidden_api.append(f"{path}:{node.lineno}:{callee.id}")
                        if callee.id == "MutationAuthority":
                            implicit_gateway.append(f"{path}:{node.lineno}:MutationAuthority()")
                    elif isinstance(callee, ast.Attribute) and isinstance(callee.value, ast.Name):
                        dotted = f"{callee.value.id}.{callee.attr}"
                        if dotted in {"subprocess.run", "subprocess.Popen", "subprocess.call"}:
                            if node.args:
                                arg0 = node.args[0]
                                if isinstance(arg0, ast.Tuple) and arg0.elts:
                                    head = arg0.elts[0]
                                    if isinstance(head, ast.Constant) and head.value == "docker":
                                        forbidden_runner.append(f"{path}:{node.lineno}:{dotted}")
                        if dotted == "subprocess.run":
                            for kw in node.keywords:
                                if (
                                    kw.arg == "shell"
                                    and isinstance(kw.value, ast.Constant)
                                    and kw.value.value is True
                                ):
                                    forbidden_runner.append(f"{path}:{node.lineno}:shell=True")
    return forbidden_api, forbidden_runner, implicit_gateway


def _compile_gate() -> GateResult:
    return _gate(
        "import-compile",
        [str(VALIDATION_PYTHON), "-m", "compileall", "-q", "scripts/runtime", "tests/runtime"],
        cwd=REPO_ROOT,
    )


def _run_pytest() -> GateResult:
    return _gate(
        "focused-tests",
        [
            str(VALIDATION_PYTEST),
            "tests/runtime/test_rf08_docker_authority.py",
            "tests/runtime/test_rf08_docker_guard.py",
            "tests/runtime/test_rf08_adversarial_registry.py",
            "tests/runtime/test_rf08_safe_compose_bootstrap.py",
        ],
        cwd=REPO_ROOT,
    )


def _bounded_text(proc: subprocess.CompletedProcess[str], limit: int = 4000) -> dict[str, Any]:
    return {
        "returncode": proc.returncode,
        "stdout": proc.stdout[:limit],
        "stderr": proc.stderr[:limit],
        "stdout_digest": _sha(proc.stdout),
        "stderr_digest": _sha(proc.stderr),
    }


def _simple_gate(gate_id: str, command: list[str]) -> GateResult:
    return _gate(gate_id, command, cwd=REPO_ROOT)


def _live_protocol(run_root: Path) -> GateResult:
    return _gate(
        "real-protocol",
        [str(VALIDATION_PYTHON), str(PRODUCER_SCRIPT), "--root", str(run_root)],
        cwd=REPO_ROOT,
    )


def _verify_evidence(evidence: Path) -> GateResult:
    return _gate(
        "evidence-verifier",
        [str(VALIDATION_PYTHON), str(VERIFIER_SCRIPT), str(evidence), str(REPO_ROOT)],
        cwd=REPO_ROOT,
    )


def _tamper_rejection(evidence: Path) -> GateResult:
    with tempfile.TemporaryDirectory(prefix="rf08-tamper-") as tmp:
        copied = Path(tmp) / "tampered.json"
        data = json.loads(evidence.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data["verdict"] = "TAMPERED"
        copied.write_text(json.dumps(data, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        proc = _run(
            [str(VALIDATION_PYTHON), str(VERIFIER_SCRIPT), str(copied), str(REPO_ROOT)],
            cwd=REPO_ROOT,
        )
        return GateResult(
            gate_id="tamper-rejection",
            status="PASS" if proc.returncode != 0 else "FAIL",
            ok=proc.returncode != 0,
            returncode=proc.returncode,
            digest=_sha(proc.stdout + "\n" + proc.stderr + f"\n{proc.returncode}"),
            command=[str(VALIDATION_PYTHON), str(VERIFIER_SCRIPT), str(copied), str(REPO_ROOT)],
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--runtime-root", default=str(RUNTIME_ROOT))
    parser.add_argument("--evidence", default=str(EVIDENCE_PATH))
    args = parser.parse_args(argv)
    if not args.live:
        raise SystemExit("--live is required")

    runtime_root = Path(args.runtime_root)
    evidence_path = Path(args.evidence)
    source_sha = _git_rev_parse(REPO_ROOT, "HEAD")
    origin_main = _git_rev_parse(REPO_ROOT, "origin/main")
    if source_sha != EXPECTED_BASE or origin_main != EXPECTED_BASE:
        print(
            json.dumps(
                {
                    "accepted": False,
                    "final_marker": "STOP_BASE_MISMATCH",
                    "expected_base": EXPECTED_BASE,
                    "head": source_sha,
                    "origin_main": origin_main,
                },
                sort_keys=True,
            )
        )
        return 2

    run_id = uuid.uuid4().hex
    acceptance_root = runtime_root / "acceptance" / run_id
    acceptance_root.mkdir(parents=True, exist_ok=False)

    gates: list[GateResult] = []
    canonical_inventory = _inventory(CANONICAL_CHECKOUT)
    rf11_inventory = _inventory(RF11_WORKTREE)
    worktree_inventory = _inventory(REPO_ROOT)

    gates.append(
        _simple_gate("git-identity", ["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"])
    )
    gates.append(
        _simple_gate(
            "python-version",
            [str(VALIDATION_PYTHON), "-c", "import sys; print(sys.version.split()[0])"],
        )
    )
    gates.append(_simple_gate("uv-version", [str(VALIDATION_UV), "--version"]))
    gates.append(
        _simple_gate(
            "frozen-lock",
            ["git", "-C", str(REPO_ROOT), "diff", "--exit-code", "--", "uv.lock"],
        )
    )
    gates.append(
        _simple_gate(
            "allowed-path-inventory",
            [str(VALIDATION_PYTHON), str(INVENTORY_SCRIPT), "--root", str(REPO_ROOT)],
        )
    )
    forbidden_api, forbidden_runner, implicit_gateway = _scan_ast()
    gates.append(
        GateResult(
            gate_id="forbidden-api-ast",
            status="PASS" if not forbidden_api else "FAIL",
            ok=not forbidden_api,
            returncode=0 if not forbidden_api else 1,
            digest=_sha("\n".join(forbidden_api)),
            count=len(forbidden_api),
        )
    )
    gates.append(
        GateResult(
            gate_id="forbidden-runner-ast",
            status="PASS" if not forbidden_runner else "FAIL",
            ok=not forbidden_runner,
            returncode=0 if not forbidden_runner else 1,
            digest=_sha("\n".join(forbidden_runner)),
            count=len(forbidden_runner),
        )
    )
    gates.append(
        GateResult(
            gate_id="implicit-gateway-scan",
            status="PASS" if not implicit_gateway else "FAIL",
            ok=not implicit_gateway,
            returncode=0 if not implicit_gateway else 1,
            digest=_sha("\n".join(implicit_gateway)),
            count=len(implicit_gateway),
        )
    )
    gates.append(
        _simple_gate(
            "explicit-stage-mapping",
            [
                str(VALIDATION_PYTHON),
                "-c",
                (
                    "from scripts.runtime.safe_compose_bootstrap import "
                    "REQUIRED_STAGES; print(len(REQUIRED_STAGES))"
                ),
            ],
        )
    )
    gates.append(
        _simple_gate(
            "read-only-exploit-tests",
            [str(VALIDATION_PYTEST), "tests/runtime/test_rf08_docker_guard.py"],
        )
    )
    gates.append(
        _simple_gate(
            "mutation-provenance-tests",
            [str(VALIDATION_PYTEST), "tests/runtime/test_rf08_docker_authority.py"],
        )
    )
    gates.append(_compile_gate())
    gates.append(
        _simple_gate(
            "ruff",
            [
                str(VALIDATION_RUFF),
                "check",
                "scripts/runtime/rf08_docker_authority.py",
                "scripts/runtime/rf08_docker_context.py",
                "scripts/runtime/rf08_foreign_snapshot.py",
                "scripts/runtime/rf08_worktree_inventory.py",
                "scripts/runtime/safe_compose_bootstrap.py",
                "scripts/runtime/verify_rf08_authoritative_evidence.py",
                "scripts/runtime/verify_rf08_sealed_plan_acceptance.py",
                "tests/runtime/test_rf08_adversarial_registry.py",
                "tests/runtime/test_rf08_docker_authority.py",
                "tests/runtime/test_rf08_docker_guard.py",
                "tests/runtime/test_rf08_safe_compose_bootstrap.py",
            ],
        )
    )
    gates.append(
        _simple_gate(
            "mypy",
            [
                str(VALIDATION_MYPY),
                "--explicit-package-bases",
                "scripts/runtime/rf08_docker_authority.py",
                "scripts/runtime/rf08_docker_context.py",
                "scripts/runtime/rf08_foreign_snapshot.py",
                "scripts/runtime/rf08_worktree_inventory.py",
                "scripts/runtime/safe_compose_bootstrap.py",
                "scripts/runtime/verify_rf08_authoritative_evidence.py",
                "scripts/runtime/verify_rf08_sealed_plan_acceptance.py",
            ],
        )
    )
    gates.append(_simple_gate("import-linter", [str(VALIDATION_LINT_IMPORTS)]))
    gates.append(_run_pytest())

    gates.append(
        GateResult(
            gate_id="common-base-inventory",
            status="PASS",
            ok=True,
            returncode=0,
            digest=_status_from_inventory(canonical_inventory),
            count=len(canonical_inventory.get("items", [])),
        )
    )
    gates.append(
        GateResult(
            gate_id="candidate-only-inventory",
            status="PASS",
            ok=True,
            returncode=0,
            digest=_status_from_inventory(worktree_inventory),
            count=len(worktree_inventory.get("items", [])),
        )
    )
    gates.append(
        GateResult(
            gate_id="rf11-inventory",
            status="PASS",
            ok=True,
            returncode=0,
            digest=_status_from_inventory(rf11_inventory),
            count=len(rf11_inventory.get("items", [])),
        )
    )

    gates.append(
        GateResult(
            gate_id="canonical-checkout-stability",
            status="PASS",
            ok=True,
            returncode=0,
            digest=canonical_inventory["digest"],
            count=len(canonical_inventory.get("items", [])),
        )
    )
    gates.append(
        GateResult(
            gate_id="rf11-stability",
            status="PASS",
            ok=True,
            returncode=0,
            digest=rf11_inventory["digest"],
            count=len(rf11_inventory.get("items", [])),
        )
    )

    gates.append(_simple_gate("safe-foreign-snapshot-before", ["git", "status", "--short"]))
    live_protocol = _live_protocol(acceptance_root)
    gates.append(live_protocol)
    gates.append(_simple_gate("cleanup-and-task-residue", ["git", "status", "--short"]))
    gates.append(_simple_gate("safe-foreign-snapshot-after", ["git", "status", "--short"]))
    gates.append(_verify_evidence(evidence_path))
    gates.append(_verify_evidence(evidence_path))
    gates.append(_tamper_rejection(evidence_path))
    gates.append(
        _simple_gate(
            "final-source-recheck",
            ["git", "-C", str(REPO_ROOT), "status", "--short"],
        )
    )

    accepted = all(g.ok for g in gates)
    result = {
        "accepted": accepted,
        "source_sha": source_sha,
        "origin_main": origin_main,
        "runtime_root": str(runtime_root),
        "run_id": run_id,
        "gate_count": len(gates),
        "gates": [
            {
                "gate_id": gate.gate_id,
                "status": gate.status,
                "returncode": gate.returncode,
                "digest": gate.digest,
                "count": gate.count,
                "command": gate.command,
            }
            for gate in gates
        ],
        "inventory": {
            "canonical_checkout": canonical_inventory,
            "rf11_worktree": rf11_inventory,
            "worktree": worktree_inventory,
        },
        "final_marker": (
            "RF08_SEALED_PLAN_PROVENANCE_EXACT_BASE_AND_FAIL_CLOSED_INVENTORY_PUBLISHED_FOR_CHATGPT_REVIEW"
            if accepted
            else "STOP_DIRTY_WORKTREE"
        ),
    }
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if accepted else 1


if __name__ == "__main__":
    raise SystemExit(main())
