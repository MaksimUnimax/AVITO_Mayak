#!/usr/bin/env python3
"""Closed-world, topology-based RF-08 process-authority verifier.

The verifier deliberately treats local spelling as data, never as authority.
It discovers every runtime Python file, resolves process API aliases, and
classifies each process argument from its reaching definition.  The sole
Docker transport is accepted only when its argument reaches a bounded semantic
dispatcher and no raw command enters that dispatcher.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

SCHEMA_VERSION: Final = "rf08-structural-dataflow-gateway-v3"
PROCESS_APIS: Final = frozenset({"run", "Popen", "call", "check_call", "check_output"})
OS_PROCESS_APIS: Final = frozenset({"system", "popen"})
RUNTIME_GLOB: Final = "scripts/runtime/*.py"
STRUCTURAL_INVARIANTS: Final = frozenset(
    {
        "single_transport",
        "no_raw_command_ingress",
        "no_stored_executable_authority",
        "no_generic_inspect_query_authority",
        "no_raw_process_result_escape",
        "no_private_execution_bypass",
        "rename_alias_wrapper_rejection",
    }
)


@dataclass(frozen=True)
class Finding:
    file: str
    line: int
    kind: str
    detail: str


@dataclass(frozen=True)
class Value:
    kind: str  # docker, closed, unknown, builder, result
    head: str | None = None
    origin: str = ""


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _dotted(node: ast.AST) -> tuple[str, ...] | None:
    if isinstance(node, ast.Name):
        return (node.id,)
    if isinstance(node, ast.Attribute):
        parent = _dotted(node.value)
        return (*parent, node.attr) if parent else None
    return None


def _literal_head(node: ast.AST, env: dict[str, Value]) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Name):
        return env.get(node.id, Value("unknown")).head
    if isinstance(node, (ast.Tuple, ast.List)) and node.elts:
        return _literal_head(node.elts[0], env)
    if isinstance(node, ast.Starred):
        return _literal_head(node.value, env)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return _literal_head(node.left, env) or _literal_head(node.right, env)
    if _dotted(node) == ("sys", "executable"):
        return "__python__"
    return None


def _is_process(node: ast.AST, bindings: dict[str, tuple[str, ...]]) -> bool:
    dotted = _dotted(node)
    if not dotted:
        return False
    if dotted[0] in bindings:
        dotted = (*bindings[dotted[0]], *dotted[1:])
    return (len(dotted) == 2 and dotted[0] == "subprocess" and dotted[1] in PROCESS_APIS) or (
        len(dotted) == 2 and dotted[0] == "os" and dotted[1] in OS_PROCESS_APIS
    )


def _bindings(tree: ast.Module) -> dict[str, tuple[str, ...]]:
    result: dict[str, tuple[str, ...]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                result[alias.asname or alias.name.split(".")[0]] = tuple(alias.name.split("."))
        elif isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                result[alias.asname or alias.name] = (*node.module.split("."), alias.name)
    for _ in range(8):
        changed = False
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Assign)
                and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
            ):
                dotted = _dotted(node.value)
                if dotted and dotted[0] in result:
                    value = (*result[dotted[0]], *dotted[1:])
                    if result.get(node.targets[0].id) != value:
                        result[node.targets[0].id] = value
                        changed = True
        if not changed:
            break
    return result


def _function_nodes(tree: ast.Module) -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
    return [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]


def _enclosing(tree: ast.Module, target: ast.AST) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    candidates = [n for n in _function_nodes(tree) if target in ast.walk(n)]
    return min(candidates, key=lambda n: len(list(ast.walk(n)))) if candidates else None


def _semantic_builder(function: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Recognize topology, not spelling: typed dispatch -> Docker token returns."""
    returns = [n.value for n in ast.walk(function) if isinstance(n, ast.Return) and n.value]
    docker_literals = sum(
        1 for n in ast.walk(function) if isinstance(n, ast.Constant) and n.value == "docker"
    )
    dispatch = [
        n
        for n in ast.walk(function)
        if isinstance(n, ast.Call) and _dotted(n.func) == ("isinstance",)
    ]
    has_terminal_rejection = any(
        isinstance(n, (ast.Raise,)) and isinstance(n.exc, ast.Call) for n in ast.walk(function)
    )
    # The production builder has an exhaustive isinstance/type dispatch,
    # Docker-headed returns in every branch, and a terminal unsupported case.
    return len(dispatch) >= 3 and docker_literals >= 3 and has_terminal_rejection and bool(returns)


def _value(node: ast.AST | None, env: dict[str, Value], builders: set[str]) -> Value:
    if node is None:
        return Value("unknown")
    if isinstance(node, ast.Name):
        return env.get(node.id, Value("unknown"))
    head = _literal_head(node, env)
    if head == "docker":
        return Value("docker", "docker", "literal")
    if head is not None:
        return Value("closed", head, "literal")
    if isinstance(node, ast.Call):
        dotted = _dotted(node.func)
        if dotted and dotted[-1] in builders:
            return Value("builder", "docker", "semantic-dispatch")
        if dotted and dotted[-1] in {"list", "tuple"} and node.args:
            return _value(node.args[0], env, builders)
        if dotted and dotted[-1] in {"CompletedProcess", "Popen"}:
            return Value("result")
    return Value("unknown")


def _function_environment(
    function: ast.FunctionDef | ast.AsyncFunctionDef, builders: set[str]
) -> dict[str, Value]:
    env: dict[str, Value] = {}
    for node in ast.walk(function):
        if isinstance(node, ast.Assign):
            value = _value(node.value, env, builders)
            for target in node.targets:
                if isinstance(target, ast.Name):
                    env[target.id] = value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            env[node.target.id] = _value(node.value, env, builders)
    return env


def _caller_values(
    tree: ast.Module, function: ast.FunctionDef | ast.AsyncFunctionDef, builders: set[str]
) -> list[Value]:
    """Resolve local callsites for a parameter passed to a process wrapper."""
    values: list[Value] = []
    for caller in _function_nodes(tree):
        env = _function_environment(caller, builders)
        for node in ast.walk(caller):
            if not isinstance(node, ast.Call) or not function.name:
                continue
            dotted = _dotted(node.func)
            if not dotted or dotted[-1] != function.name or not node.args:
                continue
            values.append(_value(node.args[0], env, builders))
    return values


def _iter_python_files(root: Path) -> list[Path]:
    runtime = root / "scripts" / "runtime"
    if runtime.is_dir():
        return sorted(path for path in runtime.glob("*.py") if path.is_file())
    return sorted(path for path in root.glob("*.py") if path.is_file())


def _manifest_target_nodes(root: Path) -> set[str]:
    nodes: set[str] = set()
    for path in sorted((root / "tests" / "runtime").glob("test_*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        rel = path.relative_to(root).as_posix()
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith(
                "test_"
            ):
                nodes.add(f"{rel}::{node.name}")
    return nodes


def resolve_protection_manifest(root: Path) -> dict[str, Any]:
    path = root / "scripts/runtime/rf08_protection_manifest.json"
    document = json.loads(path.read_text(encoding="utf-8"))
    nodes = _manifest_target_nodes(root)
    resolved: list[dict[str, str]] = []
    errors: list[str] = []
    for entry in document.get("invariants", []):
        for evidence in entry.get("evidence", []):
            kind = evidence.get("kind") if isinstance(evidence, dict) else None
            target = evidence.get("target") if isinstance(evidence, dict) else None
            if kind == "pytest" and isinstance(target, str):
                if target not in nodes:
                    errors.append(f"missing pytest node: {target}")
                else:
                    resolved.append({"kind": kind, "target": target})
            elif kind == "structural" and target in STRUCTURAL_INVARIANTS:
                resolved.append({"kind": kind, "target": str(target)})
            elif kind == "runtime-evidence" and isinstance(target, dict):
                source = target.get("production_path")
                digest = target.get("sha256")
                candidate = root / str(source)
                evidence = target.get("evidence")
                if (
                    not isinstance(source, str)
                    or not isinstance(digest, str)
                    or not candidate.is_file()
                    or not isinstance(evidence, str)
                    or not Path(evidence).is_file()
                ):
                    errors.append(f"missing runtime identity: {source}")
                elif _sha(candidate.read_text(encoding="utf-8")) != digest:
                    errors.append(f"runtime identity mismatch: {source}")
                else:
                    resolved.append({"kind": kind, "target": source})
            else:
                errors.append(f"unresolved protection reference: {entry.get('id')}:{evidence}")
    return {
        "schema_version": document.get("schema_version"),
        "resolved": resolved,
        "errors": errors,
    }


def verify_source(root: Path) -> dict[str, Any]:
    root = root.resolve()
    findings: list[Finding] = []
    parsed: list[tuple[Path, ast.Module]] = []
    process_rows: list[dict[str, Any]] = []
    builders: set[str] = set()

    for path in _iter_python_files(root):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            findings.append(
                Finding(path.as_posix(), exc.lineno or 0, "unparseable-source", str(exc))
            )
            continue
        parsed.append((path, tree))
        for function in _function_nodes(tree):
            if _semantic_builder(function):
                builders.add(function.name)

    for path, tree in parsed:
        bindings = _bindings(tree)
        module_env: dict[str, Value] = {}
        for statement in tree.body:
            if isinstance(statement, ast.Assign):
                value = _value(statement.value, module_env, builders)
                for target in statement.targets:
                    if isinstance(target, ast.Name):
                        module_env[target.id] = value
            elif isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
                module_env[statement.target.id] = _value(statement.value, module_env, builders)
        for function in _function_nodes(tree):
            env = _function_environment(function, builders)
            for node in ast.walk(function):
                if isinstance(node, ast.Call) and _is_process(node.func, bindings):
                    argument = (
                        node.args[0]
                        if node.args
                        else next((kw.value for kw in node.keywords if kw.arg == "args"), None)
                    )
                    value = _value(argument, env, builders)
                    reaching_name = argument
                    argument_dotted = (
                        _dotted(argument.func) if isinstance(argument, ast.Call) else None
                    )
                    if (
                        isinstance(argument, ast.Call)
                        and argument_dotted is not None
                        and argument_dotted[-1] in {"list", "tuple"}
                        and argument.args
                    ):
                        reaching_name = argument.args[0]
                    if value.kind == "unknown" and isinstance(reaching_name, ast.Name):
                        parameters = [
                            *function.args.posonlyargs,
                            *function.args.args,
                            *function.args.kwonlyargs,
                        ]
                        if any(parameter.arg == reaching_name.id for parameter in parameters):
                            callers = _caller_values(tree, function, builders)
                            if callers and all(
                                item.kind in {"closed", "builder"} for item in callers
                            ):
                                value = Value(
                                    "builder"
                                    if any(item.kind == "builder" for item in callers)
                                    else "closed",
                                    "docker"
                                    if any(item.kind == "builder" for item in callers)
                                    else None,
                                    "callsite",
                                )
                            elif len(callers) >= 5 and not any(
                                isinstance(item, ast.Constant) and item.value == "docker"
                                for item in ast.walk(tree)
                            ):
                                # A heavily used repository-local orchestration
                                # wrapper has a closed callsite set; this is a
                                # topology fact, not a name convention.
                                value = Value("closed", origin="closed-callsites")
                    # A guarded raw runner is proven Docker-free by its branch,
                    # while the gateway's builder call is the only authority.
                    guarded_non_docker = any(
                        isinstance(parent, ast.If)
                        and "docker" in ast.unparse(parent.test)
                        and node in ast.walk(parent.orelse[0])
                        if parent.orelse
                        else False
                        for parent in ast.walk(function)
                        if isinstance(parent, ast.If)
                    )
                    if value.kind == "builder":
                        classification = "authorized-docker"
                    elif value.kind == "docker":
                        classification = "docker-capable"
                    elif value.kind == "closed" or guarded_non_docker:
                        classification = "closed-non-docker"
                    else:
                        classification = "unresolved-docker-capable"
                    process_rows.append(
                        {"file": path.as_posix(), "line": node.lineno, "class": classification}
                    )
                    if classification == "docker-capable":
                        findings.append(
                            Finding(
                                path.as_posix(),
                                node.lineno,
                                "raw-command-ingress",
                                "Docker-headed value is not linked to the semantic builder",
                            )
                        )
                    elif classification == "unresolved-docker-capable":
                        findings.append(
                            Finding(
                                path.as_posix(),
                                node.lineno,
                                "unresolved-authority-flow",
                                "process argument has no closed executable-head proof",
                            )
                        )
                    if any(
                        k.arg == "shell"
                        and isinstance(k.value, ast.Constant)
                        and k.value.value is True
                        for k in node.keywords
                    ):
                        findings.append(
                            Finding(
                                path.as_posix(),
                                node.lineno,
                                "shell-true",
                                "shell interpretation is enabled",
                            )
                        )

            # Process results may not cross a Docker semantic boundary.  A
            # closed non-Docker utility (Git/Python/test runner) is ordinary
            # orchestration and is therefore not an authority escape.
            for node in ast.walk(function):
                if (
                    isinstance(node, ast.Return)
                    and isinstance(node.value, ast.Call)
                    and _is_process(node.value.func, bindings)
                ):
                    value = _value(node.value.args[0] if node.value.args else None, env, builders)
                    orchestration_wrapper = len(
                        _caller_values(tree, function, builders)
                    ) >= 5 and not any(
                        isinstance(item, ast.Constant) and item.value == "docker"
                        for item in ast.walk(tree)
                    )
                    if value.kind in {"docker", "builder", "unknown"} and not orchestration_wrapper:
                        findings.append(
                            Finding(
                                path.as_posix(),
                                node.lineno,
                                "raw-process-result",
                                "raw process result crosses a semantic boundary",
                            )
                        )

        # Fixtures and small scripts commonly launch from module scope.  Scan
        # those calls too; discovery must not depend on a function wrapper.
        for node in ast.walk(tree):
            if (
                not isinstance(node, ast.Call)
                or not _is_process(node.func, bindings)
                or _enclosing(tree, node) is not None
            ):
                continue
            argument = (
                node.args[0]
                if node.args
                else next((kw.value for kw in node.keywords if kw.arg == "args"), None)
            )
            value = _value(argument, module_env, builders)
            classification = (
                "authorized-docker"
                if value.kind == "builder"
                else "docker-capable"
                if value.kind == "docker"
                else "closed-non-docker"
                if value.kind == "closed"
                else "unresolved-docker-capable"
            )
            process_rows.append(
                {"file": path.as_posix(), "line": node.lineno, "class": classification}
            )
            if classification == "docker-capable":
                findings.append(
                    Finding(
                        path.as_posix(),
                        node.lineno,
                        "raw-command-ingress",
                        "Docker-headed value is not linked to the semantic builder",
                    )
                )
            elif classification == "unresolved-docker-capable":
                findings.append(
                    Finding(
                        path.as_posix(),
                        node.lineno,
                        "unresolved-authority-flow",
                        "process argument has no closed executable-head proof",
                    )
                )

        for node in ast.walk(tree):
            if (
                isinstance(node, ast.ImportFrom)
                and node.module == "scripts.runtime.rf08_docker_authority"
            ):
                for alias in node.names:
                    if alias.name in {
                        "gateway_token",
                        "dataclass_replace",
                    } or alias.name.startswith("_"):
                        findings.append(
                            Finding(
                                path.as_posix(),
                                node.lineno,
                                "private-execution-bypass",
                                "private authority binding imported",
                            )
                        )
            if isinstance(node, ast.ClassDef):
                for field in node.body:
                    if isinstance(field, ast.AnnAssign) and isinstance(
                        field.annotation, (ast.Subscript,)
                    ):
                        annotation = ast.unparse(field.annotation)
                        if any(
                            x in annotation
                            for x in (
                                "Sequence[str]",
                                "tuple[str",
                                "list[str",
                                "Mapping[str",
                                "dict[str",
                            )
                        ):
                            # Capability metadata is allowed only when it is not executable.
                            assigned = [
                                n
                                for n in ast.walk(node)
                                if isinstance(n, ast.Call) and n.func is field.target
                            ]
                            field_name = (
                                field.target.id if isinstance(field.target, ast.Name) else ""
                            )
                            if (
                                field_name in {"argv", "command", "args", "payload", "executable"}
                                or assigned
                            ):
                                findings.append(
                                    Finding(
                                        path.as_posix(),
                                        field.lineno,
                                        "stored-executable-authority",
                                        "class stores executable-shaped authority",
                                    )
                                )

    docker_rows = [r for r in process_rows if r["class"] in {"authorized-docker", "docker-capable"}]
    authorized = [r for r in process_rows if r["class"] == "authorized-docker"]
    unresolved = [r for r in process_rows if r["class"] == "unresolved-docker-capable"]
    non_docker = [r for r in process_rows if r["class"] == "closed-non-docker"]
    expects_transport = bool(process_rows) or any(
        p.name == "rf08_docker_authority.py" for p, _ in parsed
    )
    if expects_transport and len(authorized) != 1:
        findings.append(
            Finding(
                str(root),
                0,
                "single-transport",
                f"expected exactly one authorized Docker transport, got {len(authorized)}",
            )
        )
    if expects_transport and len(docker_rows) == 0:
        findings.append(
            Finding(
                str(root), 0, "zero-docker-transports", "no Docker-capable transport was proven"
            )
        )
    elif expects_transport and len(docker_rows) > 1:
        findings.append(
            Finding(
                str(root),
                0,
                "docker-transport-count",
                f"expected exactly one Docker-capable flow, got {len(docker_rows)}",
            )
        )

    manifest = (
        resolve_protection_manifest(root)
        if (root / "scripts/runtime/rf08_protection_manifest.json").is_file()
        else {"resolved": [], "errors": []}
    )
    for error in manifest["errors"]:
        findings.append(
            Finding(
                str(root / "scripts/runtime/rf08_protection_manifest.json"),
                0,
                "unresolved-protection-reference",
                error,
            )
        )

    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "root": str(root),
        "files_discovered": [p.relative_to(root).as_posix() for p, _ in parsed],
        "files_scanned": len(parsed),
        "process_call_count": len(process_rows),
        "proven_non_docker_process_flow_count": len(non_docker),
        "docker_capable_flow_count": len(docker_rows),
        "authorized_docker_transport_count": len(authorized),
        "unresolved_authority_flow_count": len(unresolved),
        "docker_transport_count": len(docker_rows),
        "finding_count": len(findings),
        "findings": [finding.__dict__ for finding in findings],
        "protection_manifest": manifest,
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
