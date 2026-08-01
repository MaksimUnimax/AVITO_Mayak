#!/usr/bin/env python3
"""Independent structural verifier for the RF-08 semantic gateway.

The verifier inspects source text and AST only. It does not import runtime
gateway implementation classes.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

SCHEMA_VERSION: Final = "rf08-structural-semantic-gateway-v1"
FORBIDDEN_PUBLIC_PARAMS: Final = {
    "argv",
    "command",
    "commands",
    "options",
    "extra_args",
    "env",
    "volume",
    "publish",
    "tokens",
    "parser",
    "plan",
}
FORBIDDEN_IMPORTS: Final = {
    "_ReadOnlyDockerQuery",
    "_parse_docker_command",
    "_parse_docker_option_pairs",
    "classify_docker_command_class",
    "DockerInvocationPlan",
    "MutationPlan",
    "ReadOnlyDockerQuery",
}
FORBIDDEN_CLASS_BASES: Final = {
    "DockerInvocationPlan",
    "ComposeOperationPlan",
    "ContainerProbeCreationPlan",
    "ContainerRemovalPlan",
    "ImageBuildPlan",
    "ImageLoadPlan",
    "BuildxManifestPlan",
    "BuilderScopePlan",
    "NetworkCreationPlan",
    "VolumeCreationPlan",
}
FORBIDDEN_FIELD_NAMES: Final = {
    "argv",
    "command",
    "command_tokens",
    "command_tuple",
    "tokens",
    "plan",
    "parser",
    "options",
    "extra_args",
    "env",
    "volume",
    "publish",
}
SCAN_PATTERNS: Final = (
    "scripts/runtime/rf08_*.py",
    "scripts/runtime/safe_compose_bootstrap.py",
    "scripts/runtime/verify_rf08_authoritative_evidence.py",
    "scripts/runtime/verify_rf08_sealed_plan_acceptance.py",
    "tests/runtime/test_rf08_*.py",
)


@dataclass(frozen=True)
class Finding:
    file: str
    line: int
    kind: str
    detail: str


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _iter_python_files(root: Path) -> list[Path]:
    paths: set[Path] = set()
    paths.update(p for p in root.glob("*.py") if p.is_file())
    for pattern in SCAN_PATTERNS:
        paths.update(p for p in root.glob(pattern) if p.is_file())
    return sorted(paths)


def _base_name(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _is_docker_subprocess(call: ast.Call) -> bool:
    func = call.func
    if not isinstance(func, ast.Attribute):
        return False
    if not isinstance(func.value, ast.Name) or func.value.id != "subprocess":
        return False
    if func.attr not in {"run", "Popen", "call"}:
        return False
    if not call.args:
        return False
    first = call.args[0]
    if isinstance(first, (ast.List, ast.Tuple)) and first.elts:
        head = first.elts[0]
        return isinstance(head, ast.Constant) and head.value == "docker"
    return False


def verify_source(root: Path) -> dict[str, Any]:
    root = root.resolve()
    files = _iter_python_files(root)
    findings: list[Finding] = []
    docker_transports = 0
    for path in files:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.ImportFrom)
                and node.module == "scripts.runtime.rf08_docker_authority"
            ):
                for alias in node.names:
                    if alias.name in FORBIDDEN_IMPORTS or alias.name.startswith("_"):
                        findings.append(
                            Finding(str(path), node.lineno, "forbidden-import", alias.name)
                        )
            if isinstance(node, ast.ClassDef):
                bases = {_base_name(base) for base in node.bases}
                if any(
                    base in FORBIDDEN_CLASS_BASES
                    or (base and ("Plan" in base or base.startswith("_") or "Base" in base))
                    for base in bases
                ):
                    findings.append(
                        Finding(
                            str(path),
                            node.lineno,
                            "raw-plan-inheritance",
                            ",".join(sorted(b for b in bases if b)),
                        )
                    )
                for stmt in node.body:
                    if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                        if stmt.target.id in FORBIDDEN_FIELD_NAMES:
                            findings.append(
                                Finding(
                                    str(path), stmt.lineno, "stored-command-field", stmt.target.id
                                )
                            )
                    if isinstance(stmt, ast.Assign):
                        for target in stmt.targets:
                            if isinstance(target, ast.Name) and target.id in FORBIDDEN_FIELD_NAMES:
                                findings.append(
                                    Finding(
                                        str(path), stmt.lineno, "stored-command-field", target.id
                                    )
                                )
            if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                for arg in (*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs):
                    if arg.arg in FORBIDDEN_PUBLIC_PARAMS:
                        findings.append(
                            Finding(
                                str(path),
                                node.lineno,
                                "public-command-parameter",
                                f"{node.name}:{arg.arg}",
                            )
                        )
            if isinstance(node, ast.Call):
                if _is_docker_subprocess(node):
                    docker_transports += 1
                    findings.append(
                        Finding(str(path), node.lineno, "docker-transport", "subprocess")
                    )
                if isinstance(node.func, ast.Attribute) and node.func.attr == "run":
                    for kw in node.keywords:
                        if (
                            kw.arg == "shell"
                            and isinstance(kw.value, ast.Constant)
                            and kw.value.value is True
                        ):
                            findings.append(
                                Finding(str(path), node.lineno, "shell-true", "subprocess.run")
                            )
                if isinstance(node.func, ast.Name) and node.func.id == "CompletedProcess":
                    findings.append(
                        Finding(str(path), node.lineno, "raw-completedprocess", "CompletedProcess")
                    )
            if isinstance(node, ast.Return) and isinstance(node.value, ast.Call):
                if isinstance(node.value.func, ast.Attribute):
                    attr = node.value.func.attr
                    if attr == "CompletedProcess":
                        findings.append(
                            Finding(str(path), node.lineno, "raw-completedprocess", attr)
                        )
    if docker_transports > 1:
        findings.append(Finding(str(root), 0, "multiple-docker-transports", str(docker_transports)))
    payload = {
        "schema_version": SCHEMA_VERSION,
        "root": str(root),
        "files_scanned": len(files),
        "finding_count": len(findings),
        "findings": [finding.__dict__ for finding in findings],
    }
    payload["digest"] = _sha(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return payload


def main(args: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parsed = parser.parse_args(args)
    payload = verify_source(parsed.root)
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return 1 if payload["finding_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
