#!/usr/bin/env python3
"""Canonical non-mutating RF-08 sealed-plan acceptance harness."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from enum import StrEnum
from pathlib import Path
from typing import Any

from scripts.runtime.rf08_verify_structural_gateway import (
    SCHEMA_VERSION,
    resolve_protection_manifest,
    verify_source,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
def _digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


class _Tool(StrEnum):
    GIT = "git"
    PYTHON = sys.executable
    RUFF = "ruff"
    MYPY = "mypy"
    IMPORT_LINTER = "lint-imports"


def _run(tool: _Tool, args: tuple[str, ...]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [tool.value, *args],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def _gate(gate_id: str, tool: _Tool, args: tuple[str, ...]) -> dict[str, Any]:
    proc = _run(tool, args)
    return {
        "id": gate_id,
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "digest": _digest([proc.stdout, proc.stderr, proc.returncode]),
    }


def _manifest_gate() -> tuple[dict[str, Any], list[str]]:
    result = resolve_protection_manifest(REPO_ROOT)
    targets = [item["target"] for item in result["resolved"] if item["kind"] == "pytest"]
    gate = {
        "id": "protection-manifest-resolution",
        "ok": not result["errors"],
        "returncode": 0 if not result["errors"] else 1,
        "digest": _digest(result),
        "resolved_count": len(result["resolved"]),
        "errors": result["errors"],
    }
    return gate, sorted(set(targets))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-base", required=True)
    parser.add_argument("--static-only", action="store_true")
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    parsed = parser.parse_args(argv)
    root = parsed.root.resolve()
    gates: list[dict[str, Any]] = []
    head = _run(_Tool.GIT, ("-C", str(root), "rev-parse", "HEAD")).stdout.strip()
    parent = _run(_Tool.GIT, ("-C", str(root), "rev-parse", "HEAD^")).stdout.strip()
    origin = _run(_Tool.GIT, ("-C", str(root), "rev-parse", "origin/main")).stdout.strip()
    status = _run(_Tool.GIT, ("-C", str(root), "status", "--porcelain")).stdout
    provenance_ok = (
        bool(parsed.expected_base)
        and parent == parsed.expected_base
        and origin == parsed.expected_base
        and not status.strip()
    )
    gates.append(
        {
            "id": "git-provenance",
            "ok": provenance_ok,
            "returncode": 0 if provenance_ok else 2,
            "expected_base": parsed.expected_base,
            "head": head,
            "parent": parent,
            "origin_main": origin,
            "clean": not status.strip(),
        }
    )
    if not parsed.static_only:
        gates.append(
            {
                "id": "mode",
                "ok": False,
                "returncode": 2,
                "detail": "static-only mode is required for this proof tooling corrective",
            }
        )

    structural = verify_source(root)
    structural_ok = (
        structural.get("schema_version") == SCHEMA_VERSION
        and structural.get("finding_count") == 0
        and structural.get("docker_capable_flow_count") == 1
        and structural.get("authorized_docker_transport_count") == 1
        and structural.get("unauthorized_docker_flow_count") == 0
        and structural.get("unresolved_authority_flow_count") == 0
        and all(
            result.get("status") == "PASS" and bool(result.get("digest"))
            for result in structural.get("analyzer_rule_results", {}).values()
        )
    )
    gates.append(
        {
            "id": "structural-verifier",
            "ok": structural_ok,
            "returncode": 0 if structural_ok else 1,
            "digest": structural["digest"],
            "schema_version": structural.get("schema_version"),
            "derived_counts": {
                key: structural.get(key)
                for key in (
                    "process_call_count",
                    "proven_non_docker_process_flow_count",
                    "docker_capable_flow_count",
                    "authorized_docker_transport_count",
                    "unresolved_authority_flow_count",
                    "unauthorized_docker_flow_count",
                    "finding_count",
                )
            },
            "analyzer_rule_results": structural.get("analyzer_rule_results", {}),
        }
    )
    manifest_gate, targets = _manifest_gate()
    gates.append(manifest_gate)
    for target in targets:
        gates.append(_gate(f"manifest:{target}", _Tool.PYTHON, ("-m", "pytest", target)))
    gates.append(
        _gate(
            "compile",
            _Tool.PYTHON,
            ("-m", "compileall", "-q", "scripts/runtime", "tests/runtime"),
        )
    )
    changed = [
        "scripts/runtime/rf08_docker_authority.py",
        "scripts/runtime/rf08_docker_context.py",
        "scripts/runtime/rf08_foreign_snapshot.py",
        "scripts/runtime/rf08_verify_structural_gateway.py",
        "scripts/runtime/safe_compose_bootstrap.py",
        "scripts/runtime/verify_rf08_authoritative_evidence.py",
        "scripts/runtime/verify_rf08_sealed_plan_acceptance.py",
        "scripts/runtime/rf08_protection_manifest.json",
        "scripts/runtime/verify_rf08_task_scoped_runtime.py",
        "tests/runtime/test_rf08_adversarial_registry.py",
        "tests/runtime/test_rf08_protection_manifest.py",
        "tests/runtime/test_rf08_task_scoped_authority.py",
        "tests/runtime/test_rf08_safe_compose_bootstrap.py",
    ]
    changed_python = [path for path in changed if path.endswith(".py")]
    gates.append(_gate("ruff", _Tool.RUFF, ("check", *changed_python)))
    gates.append(
        _gate(
            "mypy",
            _Tool.MYPY,
            (
                "--ignore-missing-imports",
                "--explicit-package-bases",
                *changed_python,
            ),
        )
    )
    gates.append(_gate("import-linter", _Tool.IMPORT_LINTER, ()))
    accepted = all(bool(g.get("ok")) for g in gates)
    result = {
        "accepted": accepted,
        "mode": "static-only",
        "expected_base": parsed.expected_base,
        "head": head,
        "parent": parent,
        "origin_main": origin,
        "structural_verifier": {
            "identity": "scripts/runtime/rf08_verify_structural_gateway.py",
            "schema_version": structural.get("schema_version"),
            "digest": structural.get("digest"),
            "derived_counts": {
                key: structural.get(key)
                for key in (
                    "process_call_count",
                    "proven_non_docker_process_flow_count",
                    "docker_capable_flow_count",
                    "authorized_docker_transport_count",
                    "unresolved_authority_flow_count",
                    "finding_count",
                )
            },
        },
        "gates": gates,
        "final_marker": "PUBLISHED_FOR_CHATGPT_REVIEW" if accepted else "STATIC_ACCEPTANCE_FAILED",
    }
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if accepted else 1


if __name__ == "__main__":
    raise SystemExit(main())
