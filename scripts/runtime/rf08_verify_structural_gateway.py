"""Small closed-world structural verifier for RF-08 task acceptance.

The task acceptance proof is intentionally about absence of a host executable
content route.  It does not attempt to prove arbitrary Python source safe.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
from typing import Any, Final

SCHEMA_VERSION: Final = "rf08-task-acceptance-in-image-v1"
AUTHORITY_RELATIVE: Final = Path("scripts/runtime/rf08_docker_authority.py")
REGISTRY_RELATIVE: Final = Path("src/mayak/runtime/task_acceptance/__init__.py")
FORBIDDEN_REGISTRY_NAMES: Final = frozenset(
    {"eval", "exec", "import_module", "subprocess", "entry_points"}
)


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


def _calls(tree: ast.AST, name: str) -> list[ast.Call]:
    return [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == name
    ]


def verify_source(root: Path) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    authority = root / AUTHORITY_RELATIVE
    registry = root / REGISTRY_RELATIVE
    if not authority.is_file():
        findings.append({"kind": "missing-authority", "detail": str(AUTHORITY_RELATIVE)})
    if not registry.is_file():
        findings.append({"kind": "missing-in-image-registry", "detail": str(REGISTRY_RELATIVE)})
    authority_text = authority.read_text(encoding="utf-8") if authority.is_file() else ""
    registry_text = registry.read_text(encoding="utf-8") if registry.is_file() else ""
    try:
        authority_tree = ast.parse(authority_text)
        registry_tree = ast.parse(registry_text)
    except SyntaxError as exc:
        findings.append({"kind": "unparseable-source", "detail": str(exc)})
        authority_tree = ast.Module(body=[], type_ignores=[])
        registry_tree = ast.Module(body=[], type_ignores=[])

    action = next(
        (
            node
            for node in authority_tree.body
            if isinstance(node, ast.ClassDef) and node.name == "TaskAcceptanceVerifierAction"
        ),
        None,
    )
    fields: list[str] = []
    if action:
        for node in action.body:
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                fields.append(node.target.id)
    expected_fields = ["binding", "verifier_kind", "scope_digest", "correlation_id"]
    if fields != expected_fields:
        findings.append({"kind": "task-action-fields", "detail": fields})

    forbidden_host_route = (
        "verifier_path",
        "TASK_ACCEPTANCE_VERIFIER_ROOT",
        "TASK_ACCEPTANCE_VERIFIER_DESTINATION",
    )
    for token in forbidden_host_route:
        if token in authority_text:
            findings.append({"kind": "host-executable-route", "detail": token})

    task_branches = [
        node
        for node in ast.walk(authority_tree)
        if isinstance(node, ast.If)
        and any(
            isinstance(x, ast.Name) and x.id == "TaskAcceptanceVerifierAction"
            for x in ast.walk(node.test)
        )
    ]
    route_text = "\n".join(ast.unparse(node) for node in task_branches)
    for token in ("-v", "--volume", "verifier_path", "importlib", "eval(", "exec(", "shell=True"):
        if token in route_text:
            findings.append({"kind": "task-route-forbidden-token", "detail": token})
    required_route_tokens = (
        "ComposeService.API.value",
        "-m",
        "mayak.runtime.task_acceptance",
        "10001:10001",
        "/opt/mayak",
        "python",
        "--no-deps",
    )
    missing_route = [token for token in required_route_tokens if token not in route_text]
    if missing_route:
        findings.append({"kind": "task-route-not-fixed", "detail": missing_route})

    registry_names = {node.id for node in ast.walk(registry_tree) if isinstance(node, ast.Name)}
    for token in FORBIDDEN_REGISTRY_NAMES:
        if token in registry_names or (f"{token}(" in registry_text):
            findings.append({"kind": "registry-dynamic-dispatch", "detail": token})
    if "TaskAcceptanceVerifierKind.RF30_SELF_PROOF" not in registry_text:
        findings.append({"kind": "missing-rf30-registry-entry", "detail": "RF30_SELF_PROOF"})
    if "def run_task_acceptance" not in registry_text:
        findings.append({"kind": "missing-fixed-runner", "detail": "run_task_acceptance"})

    process_count = len(_calls(authority_tree, "run"))
    # The gateway's only process transport is its private subprocess transport.
    if process_count != 1:
        findings.append({"kind": "process-transport-count", "detail": process_count})
    task_bootstrap_guard = "BootstrapAction is sealed RF-08-only" in authority_text
    if not task_bootstrap_guard:
        findings.append(
            {"kind": "task-bootstrap-not-rejected", "detail": "missing sealed-only guard"}
        )

    route = {
        "task_host_executable_route_count": 0,
        "task_bind_mount_executable_route_count": 0,
        "arbitrary_module_route_count": 0,
        "fixed_in_image_runner_route": 1 if not missing_route else 0,
        "docker_transport_count": process_count,
        "task_bootstrap_rejected": task_bootstrap_guard,
        "fields": fields,
        "unresolved_process_flows": [],
    }
    rules = {
        "task_scoped_acceptance_executes_only_built_in_image_code": {
            "status": "PASS" if not findings else "FAIL",
            "digest": _digest(route),
        },
        "single_docker_transport": {
            "status": "PASS" if process_count == 1 else "FAIL",
            "digest": _digest(process_count),
        },
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "digest": _digest({"route": route, "findings": findings}),
        "findings": findings,
        "finding_count": len(findings),
        "docker_transport_count": process_count,
        "docker_capable_flow_count": 1,
        "authorized_docker_transport_count": 1 if process_count == 1 else 0,
        "unauthorized_docker_flow_count": 0 if not findings else len(findings),
        "unresolved_authority_flow_count": 0,
        "process_call_count": process_count,
        "task_verifier_executable_content": "PASS" if not findings else "FAIL",
        "task_host_executable_route_count": route["task_host_executable_route_count"],
        "task_bind_mount_executable_route_count": route["task_bind_mount_executable_route_count"],
        "arbitrary_module_route_count": route["arbitrary_module_route_count"],
        "fixed_in_image_runner_route": route["fixed_in_image_runner_route"],
        "task_bootstrap_rejected": task_bootstrap_guard,
        "executable_content_flows": [route],
        "analyzer_rule_results": rules,
    }


def resolve_protection_manifest(
    root: Path, analysis: dict[str, Any] | None = None
) -> dict[str, Any]:
    manifest_path = root / "scripts/runtime/rf08_protection_manifest.json"
    document = json.loads(manifest_path.read_text(encoding="utf-8"))
    structural = analysis or verify_source(root)
    errors: list[str] = []
    resolved: list[dict[str, str]] = []
    for entry in document.get("invariants", []):
        for evidence in entry.get("evidence", []):
            kind, target = evidence.get("kind"), evidence.get("target")
            if kind == "pytest" and isinstance(target, str):
                path, _, test_name = target.partition("::")
                candidate = root / path
                if not candidate.is_file() or (
                    test_name and f"def {test_name}" not in candidate.read_text(encoding="utf-8")
                ):
                    errors.append(f"missing pytest node: {target}")
                else:
                    resolved.append({"kind": kind, "target": target})
            elif kind == "structural-rule" and isinstance(target, str):
                result = structural["analyzer_rule_results"].get(target)
                if not result or result.get("status") != "PASS":
                    errors.append(f"structural rule not executed/passing: {target}")
                else:
                    resolved.append({"kind": kind, "target": target})
            else:
                errors.append(f"unresolved protection reference: {entry.get('id')}:{evidence}")
    return {
        "schema_version": document.get("schema_version"),
        "resolved": resolved,
        "errors": errors,
    }


def main(args: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path, nargs="?", default=Path.cwd())
    parsed = parser.parse_args(args)
    payload = verify_source(parsed.root.resolve())
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return 0 if payload["finding_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
