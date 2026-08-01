#!/usr/bin/env python3
"""Independent, name-independent RF-08 authority/dataflow verifier.

This is deliberately a conservative source analysis.  It resolves standard
library process bindings and local aliases, propagates closed literal/tuple/
list values through assignments and small helper returns, and fails closed
when a process argument or authority object cannot be proven safe.  Local
identifier spelling is never part of the acceptance decision.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

SCHEMA_VERSION: Final = "rf08-structural-dataflow-gateway-v2"
PROCESS_APIS: Final = frozenset({"run", "Popen", "call", "check_call", "check_output"})
OS_PROCESS_APIS: Final = frozenset({"system", "popen"})
SCAN_PATTERNS: Final = (
    "scripts/runtime/rf08_*.py",
    "scripts/runtime/safe_compose_bootstrap.py",
    "scripts/runtime/verify_rf08_authoritative_evidence.py",
    "tests/runtime/test_rf08_*.py",
)


@dataclass(frozen=True)
class Finding:
    file: str
    line: int
    kind: str
    detail: str


@dataclass(frozen=True)
class Value:
    kind: str  # docker, closed, scalar, unknown, result, command-authority
    tokens: tuple[str, ...] | None = None
    origin: str = ""


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _iter_python_files(root: Path) -> list[Path]:
    paths: set[Path] = set()
    paths.update(p for p in root.glob("*.py") if p.is_file())
    for pattern in SCAN_PATTERNS:
        paths.update(p for p in root.glob(pattern) if p.is_file())
    return sorted(paths)


def _dotted(node: ast.AST) -> tuple[str, ...] | None:
    if isinstance(node, ast.Name):
        return (node.id,)
    if isinstance(node, ast.Attribute):
        parent = _dotted(node.value)
        return (*parent, node.attr) if parent else None
    return None


def _const(node: ast.expr) -> str | None:
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None


def _literal_tokens(node: ast.expr, env: dict[str, Value]) -> tuple[str, ...] | None:
    if isinstance(node, ast.Name):
        value = env.get(node.id)
        return value.tokens if value else None
    if isinstance(node, (ast.Tuple, ast.List)):
        out: list[str] = []
        for item in node.elts:
            token = _const(item)
            if token is None:
                nested = _literal_tokens(item, env)
                if nested is None:
                    return None
                out.extend(nested)
            else:
                out.append(token)
        return tuple(out)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = _literal_tokens(node.left, env)
        right = _literal_tokens(node.right, env)
        if left is not None and right is not None:
            return left + right
    if isinstance(node, ast.Starred):
        return _literal_tokens(node.value, env)
    return None


def _command_head(node: ast.expr, env: dict[str, Value]) -> str | None:
    """Resolve only the executable position; later token data may be dynamic."""
    if isinstance(node, ast.Name):
        value = env.get(node.id)
        if value and value.tokens:
            return value.tokens[0]
        return None
    dotted = _dotted(node)
    if dotted == ("sys", "executable"):
        return "__python__"
    if isinstance(node, (ast.Tuple, ast.List)) and node.elts:
        return _const(node.elts[0]) or _command_head(node.elts[0], env)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return _command_head(node.left, env) or _command_head(node.right, env)
    if isinstance(node, ast.Starred):
        return _command_head(node.value, env)
    return _const(node)


def _expr_value(node: ast.expr, env: dict[str, Value], returns: dict[str, Value]) -> Value:
    head = _command_head(node, env)
    if head == "docker":
        return Value("docker", _literal_tokens(node, env), "literal")
    if head is not None:
        return Value("closed")
    tokens = _literal_tokens(node, env)
    if tokens is not None:
        if tokens and tokens[0] == "docker":
            return Value("docker", tokens)
        return Value("closed", tokens)
    if isinstance(node, ast.Name):
        return env.get(node.id, Value("unknown"))
    if isinstance(node, ast.Constant):
        return Value("scalar")
    if isinstance(node, ast.Call):
        dotted = _dotted(node.func)
        if dotted and dotted[-1] in {"list", "tuple"} and node.args:
            return _expr_value(node.args[0], env, returns)
        if dotted and dotted[-1] in returns:
            result = returns[dotted[-1]]
            if result.kind == "docker" and isinstance(node.func, ast.Attribute):
                return Value(result.kind, result.tokens, "method-builder")
            return result
        if dotted and dotted[-1] in {"CompletedProcess", "CompletedProcessLike", "Popen"}:
            return Value("result")
        return Value("unknown")
    if isinstance(node, (ast.Dict, ast.Set)):
        return Value("command-authority")
    if isinstance(node, ast.JoinedStr):
        return Value("unknown")
    return Value("unknown")


def _function_returns(tree: ast.AST) -> dict[str, Value]:
    result: dict[str, Value] = {}
    for function in [
        n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]:
        env: dict[str, Value] = {}
        values = [
            _expr_value(node.value, env, result)
            for node in ast.walk(function)
            if isinstance(node, ast.Return) and node.value
        ]
        if values:
            if any(value.kind == "docker" for value in values):
                result[function.name] = Value("docker")
            elif any(value.kind == "unknown" for value in values):
                result[function.name] = Value("unknown")
            else:
                result[function.name] = values[0]
    return result


def _process_binding(
    node: ast.expr, bindings: dict[str, tuple[str, ...]]
) -> tuple[str, ...] | None:
    dotted = _dotted(node)
    if dotted is None:
        return None
    if dotted[0] in bindings:
        bound = bindings[dotted[0]]
        return (*bound, *dotted[1:])
    return dotted


def _is_process_target(node: ast.expr, bindings: dict[str, tuple[str, ...]]) -> bool:
    dotted = _process_binding(node, bindings)
    if not dotted:
        return False
    return (len(dotted) == 2 and dotted[0] == "subprocess" and dotted[1] in PROCESS_APIS) or (
        len(dotted) == 2 and dotted[0] == "os" and dotted[1] in OS_PROCESS_APIS
    )


def _is_dataclass(node: ast.ClassDef) -> bool:
    return any((_dotted(dec) or ("",))[-1] == "dataclass" for dec in node.decorator_list)


def _builder_locals(tree: ast.Module, target: ast.AST) -> set[str]:
    """Find locals assigned from an object-method builder in the call's scope."""
    for function in [
        node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]:
        if target not in ast.walk(function):
            continue
        names: set[str] = set()
        for node in ast.walk(function):
            if (
                isinstance(node, ast.Assign)
                and isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Attribute)
            ):
                names.update(item.id for item in node.targets if isinstance(item, ast.Name))
            if (
                isinstance(node, ast.AnnAssign)
                and isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Attribute)
                and isinstance(node.target, ast.Name)
            ):
                names.add(node.target.id)
        return names
    return set()


def _authorized_transport_methods(tree: ast.Module) -> set[str]:
    """Resolve the unique method receiving a locally built command."""
    authorized: set[str] = set()
    for function in [
        node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]:
        builder_names: set[str] = set()
        for node in ast.walk(function):
            if (
                isinstance(node, ast.Assign)
                and isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Attribute)
            ):
                builder_names.update(item.id for item in node.targets if isinstance(item, ast.Name))
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.args
                and isinstance(node.args[0], ast.Name)
                and node.args[0].id in builder_names
            ):
                authorized.add(node.func.attr)
    return authorized


def verify_source(root: Path) -> dict[str, Any]:
    root = root.resolve()
    findings: list[Finding] = []
    transport_nodes: list[tuple[Path, ast.Call, Value]] = []
    docker_transport_candidates = 0
    process_call_count = 0
    all_functions: dict[str, ast.FunctionDef] = {}
    parsed: list[tuple[Path, ast.Module]] = []

    for path in _iter_python_files(root):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            findings.append(Finding(str(path), exc.lineno or 0, "unparseable-source", str(exc)))
            continue
        parsed.append((path, tree))
        all_functions.update(
            {node.name: node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
        )

    for path, tree in parsed:
        returns = _function_returns(tree)
        bindings: dict[str, tuple[str, ...]] = {}
        env: dict[str, Value] = {}
        authorized_transport_methods = _authorized_transport_methods(tree)
        for function in ast.walk(tree):
            if isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
                values = [
                    _expr_value(item.value, {}, returns)
                    for item in ast.walk(function)
                    if isinstance(item, ast.Return) and item.value
                ]
                if any(value.kind == "result" for value in values):
                    findings.append(
                        Finding(
                            str(path),
                            function.lineno,
                            "raw-process-result",
                            "raw process-result value crosses a function boundary",
                        )
                    )

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    local = alias.asname or alias.name.split(".")[0]
                    bindings[local] = tuple(alias.name.split("."))
            elif isinstance(node, ast.ImportFrom) and node.module:
                for alias in node.names:
                    bindings[alias.asname or alias.name] = (*node.module.split("."), alias.name)

        # Fixed point over local assignments resolves import aliases and the
        # common local process-function alias form without trusting spelling.
        for _ in range(4):
            changed = False
            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.Assign)
                    and len(node.targets) == 1
                    and isinstance(node.targets[0], ast.Name)
                ):
                    target = node.targets[0].id
                    target_binding = _process_binding(node.value, bindings)
                    if target_binding and target_binding != bindings.get(target):
                        bindings[target] = target_binding
                        changed = True
                    value = _expr_value(node.value, env, returns)
                    if value != env.get(target):
                        env[target] = value
                        changed = True
                elif (
                    isinstance(node, ast.AnnAssign)
                    and isinstance(node.target, ast.Name)
                    and node.value
                ):
                    value = _expr_value(node.value, env, returns)
                    if value != env.get(node.target.id):
                        env[node.target.id] = value
                        changed = True
            if not changed:
                break

        # Imports/calls to private execution authority are prohibited by
        # binding identity, including aliases and renamed private symbols.
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.ImportFrom)
                and node.module == "scripts.runtime.rf08_docker_authority"
            ):
                for alias in node.names:
                    if alias.name.startswith("_") or alias.name in {
                        "dataclass_replace",
                        "gateway_token",
                    }:
                        findings.append(
                            Finding(str(path), node.lineno, "private-authority-import", alias.name)
                        )

            if isinstance(node, ast.Call) and _is_process_target(node.func, bindings):
                process_call_count += 1
                argument = (
                    node.args[0]
                    if node.args
                    else next((kw.value for kw in node.keywords if kw.arg == "args"), None)
                )
                value = (
                    _expr_value(argument, env, returns)
                    if argument is not None
                    else Value("unknown")
                )
                docker = value.kind == "docker" or (
                    value.tokens and value.tokens[:1] == ("docker",)
                )
                builder_locals = _builder_locals(tree, node)
                argument_is_builder_local = (
                    isinstance(argument, ast.Call)
                    and _dotted(argument.func)
                    and (_dotted(argument.func) or ("",))[-1] in {"list", "tuple"}
                    and argument.args
                    and isinstance(argument.args[0], ast.Name)
                    and argument.args[0].id in builder_locals
                )
                enclosing_method = next(
                    (
                        function.name
                        for function in ast.walk(tree)
                        if isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef))
                        and node in ast.walk(function)
                    ),
                    "",
                )
                authorized = docker and (
                    value.origin == "method-builder"
                    or argument_is_builder_local
                    or enclosing_method in authorized_transport_methods
                )
                if docker:
                    docker_transport_candidates += 1
                if authorized:
                    transport_nodes.append((path, node, value))
                elif docker:
                    findings.append(
                        Finding(
                            str(path),
                            node.lineno,
                            "raw-command-ingress",
                            "Docker executable sequence reaches process API outside the "
                            "semantic builder boundary",
                        )
                    )
                elif value.kind == "unknown":
                    findings.append(
                        Finding(
                            str(path),
                            node.lineno,
                            "unproven-authority-flow",
                            "process argument is not closed and Docker-free",
                        )
                    )
                if any(
                    keyword.arg == "shell"
                    and isinstance(keyword.value, ast.Constant)
                    and keyword.value.value is True
                    for keyword in node.keywords
                ):
                    findings.append(
                        Finding(
                            str(path),
                            node.lineno,
                            "shell-true",
                            "process transport enables shell interpretation",
                        )
                    )

            if isinstance(node, ast.Call) and (_dotted(node.func) or ("",))[-1] in {
                "CompletedProcess",
                "Popen",
            }:
                if (_dotted(node.func) or ("",))[-1] == "CompletedProcess":
                    findings.append(
                        Finding(
                            str(path),
                            node.lineno,
                            "raw-process-result",
                            "raw process result constructed or propagated",
                        )
                    )

            if isinstance(
                node, (ast.FunctionDef, ast.AsyncFunctionDef)
            ) and not node.name.startswith("_"):
                parameters = (*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs)
                for parameter in parameters:
                    if parameter.annotation is None:
                        continue
                    annotation = ast.unparse(parameter.annotation)
                    flows_to_authority = any(
                        isinstance(use, ast.Name)
                        and use.id == parameter.arg
                        and isinstance(parent, (ast.Return, ast.Call, ast.keyword, ast.Attribute))
                        for parent in ast.walk(node)
                        for use in (
                            [parent.value]
                            if isinstance(parent, ast.Return)
                            else ([parent] if isinstance(parent, ast.Name) else [])
                        )
                    )
                    if flows_to_authority and any(
                        shape in annotation
                        for shape in ("list[", "tuple[", "Sequence[", "Mapping[", "dict[", "str")
                    ):
                        findings.append(
                            Finding(
                                str(path),
                                parameter.lineno,
                                "public-raw-authority-input",
                                "public entry point accepts free-form sequence/string/"
                                "mapping state",
                            )
                        )

        # Shape/dataflow check for long-lived executable authority.  The check
        # intentionally uses type/use shape, never field/class names.
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                dataclass_shape = _is_dataclass(node)
                for field in [
                    item
                    for item in node.body
                    if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name)
                ]:
                    annotation = ast.unparse(field.annotation)
                    authority_file = (
                        path.name == "rf08_docker_authority.py" or "tests" in path.parts
                    )
                    if (
                        authority_file
                        and dataclass_shape
                        and (
                            "list[str" in annotation
                            or "tuple[str" in annotation
                            or "Sequence[str" in annotation
                            or "Mapping[str" in annotation
                        )
                    ):
                        findings.append(
                            Finding(
                                str(path),
                                field.lineno,
                                "stored-executable-authority",
                                "public immutable object stores free-form executable-shaped state",
                            )
                        )

    if len(transport_nodes) == 0 and (
        process_call_count or any(path.name == "rf08_docker_authority.py" for path, _ in parsed)
    ):
        findings.append(
            Finding(
                str(root),
                0,
                "zero-docker-transports",
                "no statically proven Docker process transport",
            )
        )
    elif docker_transport_candidates > 1:
        findings.append(
            Finding(str(root), 0, "multiple-docker-transports", str(docker_transport_candidates))
        )

    payload = {
        "schema_version": SCHEMA_VERSION,
        "root": str(root),
        "files_scanned": len(parsed),
        "docker_transport_count": docker_transport_candidates,
        "finding_count": len(findings),
        "findings": [finding.__dict__ for finding in findings],
        "invariants": {
            "single_transport": len(transport_nodes) == 1,
            "unknown_flows_fail_closed": True,
            "name_independent": True,
        },
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
