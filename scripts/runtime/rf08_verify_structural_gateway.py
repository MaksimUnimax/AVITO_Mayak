#!/usr/bin/env python3
# ruff: noqa: E501,E701
"""Qualified-symbol, bounded data-flow proof for the RF-08 process surface.

The analysis is intentionally conservative.  Names are used to resolve Python
syntax, while verdicts carry immutable definition identities and value origins.
An unresolved executable head is a failure; no popularity, spelling, or text
pattern can turn it into a safe value.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, cast

SCHEMA_VERSION: Final = "rf08-structural-dataflow-gateway-v4"
PROCESS_APIS: Final = frozenset({"run", "Popen", "call", "check_call", "check_output"})
OS_PROCESS_APIS: Final = frozenset({"system", "popen"})
RUNTIME_GLOB: Final = "scripts/runtime/*.py"
RULE_IDS: Final = (
    "single_docker_transport", "no_raw_command_ingress", "no_stored_executable_authority",
    "no_generic_inspect_query_authority", "no_raw_process_result_escape",
    "no_private_cross_module_execution_bypass", "rename_alias_wrapper_independence",
)


@dataclass(frozen=True)
class ModuleId:
    path: str


@dataclass(frozen=True)
class ScopeId:
    module: ModuleId
    owner: tuple[str, ...]
    definition_line: int
    definition_col: int


@dataclass(frozen=True)
class DefinitionId:
    scope: ScopeId
    line: int
    col: int
    ordinal: int


@dataclass(frozen=True)
class SymbolId:
    definition: DefinitionId
    kind: str


@dataclass(frozen=True)
class Finding:
    file: str
    line: int
    kind: str
    detail: str


@dataclass(frozen=True)
class ValueOrigin:
    heads: frozenset[str] = frozenset()
    unknown: bool = True
    authorized: frozenset[SymbolId] = frozenset()
    process_result: bool = False
    stored: bool = False
    source: str = ""

    @property
    def docker(self) -> bool:
        return "docker" in self.heads

    @property
    def closed(self) -> bool:
        return not self.unknown and not self.docker

    @staticmethod
    def unknown_value(source: str = "") -> "ValueOrigin":
        return ValueOrigin(source=source)


@dataclass(frozen=True)
class FunctionInfo:
    symbol: SymbolId
    module: ModuleId
    node: ast.FunctionDef | ast.AsyncFunctionDef
    owner: tuple[str, ...]
    parameters: tuple[str, ...]


@dataclass(frozen=True)
class ProcessSite:
    module: ModuleId
    function: SymbolId | None
    node: ast.Call
    api: tuple[str, ...] | None


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _dotted(node: ast.AST | None) -> tuple[str, ...] | None:
    if isinstance(node, ast.Name):
        return (node.id,)
    if isinstance(node, ast.Attribute):
        left = _dotted(node.value)
        return (*left, node.attr) if left else None
    return None


def _files(root: Path) -> list[Path]:
    runtime = root / "scripts" / "runtime"
    return sorted(p for p in runtime.glob("*.py") if p.is_file()) if runtime.is_dir() else sorted(p for p in root.glob("*.py") if p.is_file())


def _definition(module: ModuleId, node: ast.AST, owner: tuple[str, ...], ordinal: int) -> DefinitionId:
    return DefinitionId(ScopeId(module, owner, getattr(node, "lineno", 0), getattr(node, "col_offset", 0)), getattr(node, "lineno", 0), getattr(node, "col_offset", 0), ordinal)


class RepositoryIR:
    def __init__(self, root: Path, parsed: list[tuple[Path, ast.Module]]) -> None:
        self.root = root
        self.trees: dict[ModuleId, ast.Module] = {}
        self.functions: dict[SymbolId, FunctionInfo] = {}
        self.by_module_name: dict[tuple[ModuleId, str], SymbolId] = {}
        self.by_class_method: dict[tuple[ModuleId, tuple[str, ...], str], SymbolId] = {}
        self.imports: dict[ModuleId, dict[str, tuple[str, ...]]] = {}
        self.globals: dict[ModuleId, dict[str, ValueOrigin]] = {}
        for path, tree in parsed:
            module = ModuleId(path.relative_to(root).as_posix())
            self.trees[module] = tree
            self.imports[module] = self._imports(tree)
            values: dict[str, ValueOrigin] = {}
            for statement in tree.body:
                if isinstance(statement, ast.Assign):
                    value = _sequence(statement.value, values)
                    for target in statement.targets:
                        if isinstance(target, ast.Name):
                            values[target.id] = value
                elif isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
                    values[statement.target.id] = _sequence(statement.value, values)
            self.globals[module] = values
            for _ in range(8):
                changed = False
                for statement in tree.body:
                    if isinstance(statement, ast.Assign) and len(statement.targets) == 1 and isinstance(statement.targets[0], ast.Name):
                        dotted = _dotted(statement.value)
                        if dotted and dotted[0] in self.imports[module]:
                            resolved = (*self.imports[module][dotted[0]], *dotted[1:])
                            if self.imports[module].get(statement.targets[0].id) != resolved:
                                self.imports[module][statement.targets[0].id] = resolved
                                changed = True
                if not changed:
                    break
        for module, tree in self.trees.items():
            self._index_functions(module, tree, (), 0)

    @staticmethod
    def _imports(tree: ast.Module) -> dict[str, tuple[str, ...]]:
        out: dict[str, tuple[str, ...]] = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for item in node.names:
                    out[item.asname or item.name.split(".")[0]] = tuple(item.name.split("."))
            elif isinstance(node, ast.ImportFrom) and node.module:
                for item in node.names:
                    out[item.asname or item.name] = (*node.module.split("."), item.name)
        return out

    def _index_functions(self, module: ModuleId, tree: ast.AST, owner: tuple[str, ...], seed: int) -> int:
        ordinal = seed
        body = tree.body if isinstance(tree, ast.Module) else getattr(tree, "body", ())
        for node in body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                did = _definition(module, node, owner, ordinal)
                symbol = SymbolId(did, "function")
                params = tuple(a.arg for a in (*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs))
                info = FunctionInfo(symbol, module, node, owner, params)
                self.functions[symbol] = info
                if owner:
                    self.by_class_method[(module, owner, node.name)] = symbol
                else:
                    self.by_module_name[(module, node.name)] = symbol
                ordinal += 1
            elif isinstance(node, ast.ClassDef):
                ordinal = self._index_functions(module, node, (*owner, node.name), ordinal + 1)
        return ordinal

    def module_for_import(self, current: ModuleId, parts: tuple[str, ...]) -> ModuleId | None:
        if len(parts) < 2 or parts[0] != "scripts" or parts[1] != "runtime":
            return None
        return ModuleId("/".join(parts[0:2] + parts[2:-1]) + ".py") if len(parts) > 3 else None

    def resolve_call(self, module: ModuleId, node: ast.AST, current: FunctionInfo | None) -> SymbolId | None:
        dotted = _dotted(node)
        if not dotted:
            return None
        imports = self.imports[module]
        target = (*imports[dotted[0]], *dotted[1:]) if dotted[0] in imports else dotted
        if target[:2] == ("scripts", "runtime") and len(target) >= 4:
            target_module = ModuleId("/".join(target[:-1]) + ".py")
            return self.by_module_name.get((target_module, target[-1]))
        if current and dotted[0] == "self" and len(dotted) == 2:
            return self.by_class_method.get((module, current.owner, dotted[1]))
        if len(target) == 1:
            return self.by_module_name.get((module, target[0]))
        return None

    def process_api(self, module: ModuleId, node: ast.AST) -> tuple[str, ...] | None:
        dotted = _dotted(node)
        if not dotted:
            return None
        imports = self.imports[module]
        target = (*imports[dotted[0]], *dotted[1:]) if dotted[0] in imports else dotted
        if len(target) == 2 and target[0] == "subprocess" and target[1] in PROCESS_APIS:
            return target
        if len(target) == 2 and target[0] == "os" and target[1] in OS_PROCESS_APIS:
            return target
        return None


def _literal_head(node: ast.AST | None, env: dict[str, ValueOrigin]) -> frozenset[str]:
    if node is None:
        return frozenset()
    if isinstance(node, ast.Name):
        return env.get(node.id, ValueOrigin.unknown_value()).heads
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return frozenset({node.value})
    if _dotted(node) == ("sys", "executable"):
        return frozenset({"__python__"})
    if isinstance(node, (ast.Tuple, ast.List)) and node.elts:
        return _literal_head(node.elts[0], env)
    if isinstance(node, ast.Starred):
        return _literal_head(node.value, env)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return _literal_head(node.left, env) | _literal_head(node.right, env)
    return frozenset()


def _sequence(node: ast.AST | None, env: dict[str, ValueOrigin]) -> ValueOrigin:
    if node is None:
        return ValueOrigin.unknown_value()
    if isinstance(node, ast.Name):
        return env.get(node.id, ValueOrigin.unknown_value(node.id))
    if isinstance(node, ast.Constant):
        return ValueOrigin(frozenset({node.value}) if isinstance(node.value, str) else frozenset(), False, source="literal")
    if isinstance(node, (ast.Tuple, ast.List)):
        heads = _literal_head(node, env)
        first = node.elts[0].value if node.elts and isinstance(node.elts[0], ast.Starred) else (node.elts[0] if node.elts else None)
        unknown = _sequence(first, env).unknown if first is not None else True
        return ValueOrigin(heads, unknown, source="sequence")
    if isinstance(node, ast.Starred):
        return _sequence(node.value, env)
    if isinstance(node, ast.Call):
        dotted = _dotted(node.func)
        if dotted and dotted[-1] in {"list", "tuple"} and node.args:
            return _sequence(node.args[0], env)
    if _dotted(node) == ("sys", "executable"):
        return ValueOrigin(frozenset({"__python__"}), False, source="stdlib-identity")
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left, right = _sequence(node.left, env), _sequence(node.right, env)
        return ValueOrigin(left.heads | right.heads, left.unknown or right.unknown, source="concat")
    if isinstance(node, ast.Attribute):
        return ValueOrigin.unknown_value("stored-attribute").__class__(frozenset(), True, source="stored-attribute", stored=True)
    return ValueOrigin.unknown_value("expression")


def _arg(node: ast.Call) -> ast.AST | None:
    return node.args[0] if node.args else next((k.value for k in node.keywords if k.arg in {"args", "command"}), None)


def _semantic_dispatcher(info: FunctionInfo) -> bool:
    node = info.node
    returns_docker = any("docker" in _literal_head(r.value, {}) for r in ast.walk(node) if isinstance(r, ast.Return))
    typed_input = any(a.annotation is not None and not isinstance(a.annotation, ast.Subscript) for a in (*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs))
    dispatch = any(isinstance(n, ast.Call) and _dotted(n.func) == ("isinstance",) for n in ast.walk(node)) or any(isinstance(n, ast.Match) for n in ast.walk(node))
    rejects = any(isinstance(n, ast.Raise) for n in ast.walk(node))
    return returns_docker and typed_input and dispatch and rejects


def _parents(tree: ast.AST) -> dict[ast.AST, ast.AST]:
    return {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}


def _else_excludes_docker(tree: ast.AST, node: ast.AST, env: dict[str, ValueOrigin]) -> bool:
    parents = _parents(tree)
    cur: ast.AST | None = node
    while cur is not None:
        parent = parents.get(cur)
        if isinstance(parent, ast.If) and cur in parent.orelse:
            test = parent.test
            comparisons = [x for x in ast.walk(test) if isinstance(x, ast.Compare)]
            for comparison in comparisons:
                if len(comparison.ops) == 1 and isinstance(comparison.ops[0], (ast.Eq, ast.NotEq)):
                    left, right = comparison.left, comparison.comparators[0]
                    if isinstance(right, ast.Constant) and right.value == "docker" and isinstance(left, ast.Subscript):
                        return True
                    if isinstance(left, ast.Constant) and left.value == "docker" and isinstance(right, ast.Subscript):
                        return True
        cur = parent
    return False


def _evaluated(node: ast.AST | None, module: ModuleId, current: FunctionInfo | None,
               ir: RepositoryIR, summaries: dict[SymbolId, ValueOrigin], dispatchers: set[SymbolId],
               env: dict[str, ValueOrigin]) -> ValueOrigin:
    value = _sequence(node, env)
    if isinstance(node, ast.Call):
        target = ir.resolve_call(module, node.func, current)
        if target in summaries:
            value = summaries[target]
        if target in dispatchers:
            value = ValueOrigin(frozenset({"docker"}), False, frozenset({target}), source="semantic-dispatch")
    return value


def _environment(info: FunctionInfo, ir: RepositoryIR, summaries: dict[SymbolId, ValueOrigin],
                 dispatchers: set[SymbolId]) -> dict[str, ValueOrigin]:
    env = dict(ir.globals.get(info.module, {}))
    env.update({p: ValueOrigin.unknown_value("parameter") for p in info.parameters})
    for node in ast.walk(info.node):
        if isinstance(node, ast.Assign):
            value = _evaluated(node.value, info.module, info, ir, summaries, dispatchers, env)
            for target in node.targets:
                if isinstance(target, ast.Name):
                    env[target.id] = value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            env[node.target.id] = _evaluated(node.value, info.module, info, ir, summaries, dispatchers, env)
    return env


def _caller_values(target: SymbolId, ir: RepositoryIR, summaries: dict[SymbolId, ValueOrigin],
                   dispatchers: set[SymbolId]) -> list[ValueOrigin]:
    values: list[ValueOrigin] = []
    for info in ir.functions.values():
        env = _environment(info, ir, summaries, dispatchers)
        for node in ast.walk(info.node):
            if isinstance(node, ast.Call) and ir.resolve_call(info.module, node.func, info) == target:
                actual = _arg(node)
                if isinstance(actual, ast.Name) and actual.id in info.parameters:
                    values.extend(_parameter_values(info.symbol, actual.id, ir, summaries, dispatchers, set()))
                else:
                    values.append(_evaluated(actual, info.module, info, ir, summaries, dispatchers, env))
    return values


def _parameter_values(target: SymbolId, parameter: str, ir: RepositoryIR,
                      summaries: dict[SymbolId, ValueOrigin], dispatchers: set[SymbolId],
                      seen: set[tuple[SymbolId, str]]) -> list[ValueOrigin]:
    key = (target, parameter)
    if key in seen:
        return [ValueOrigin.unknown_value("recursive-parameter")]
    seen.add(key)
    result: list[ValueOrigin] = []
    target_info = ir.functions.get(target)
    if target_info is None:
        return [ValueOrigin.unknown_value("missing-symbol")]
    for caller in ir.functions.values():
        env = _environment(caller, ir, summaries, dispatchers)
        for node in ast.walk(caller.node):
            if not isinstance(node, ast.Call) or ir.resolve_call(caller.module, node.func, caller) != target:
                continue
            actual = _arg(node)
            if isinstance(actual, ast.Name) and actual.id in caller.parameters:
                result.extend(_parameter_values(caller.symbol, actual.id, ir, summaries, dispatchers, seen))
            else:
                result.append(_evaluated(actual, caller.module, caller, ir, summaries, dispatchers, env))
    return result or [ValueOrigin.unknown_value("unreached-parameter")]


def _runtime_claim(root: Path, target: dict[str, Any]) -> str | None:
    source = target.get("production_path")
    digest = target.get("sha256")
    evidence = target.get("evidence")
    claim = target.get("claim") or target.get("stage")
    if not all(isinstance(x, str) for x in (source, digest, evidence, claim)):
        return "runtime claim is incomplete"
    path = root / cast(str, source)
    ep = Path(cast(str, evidence))
    if not path.is_file() or _sha(path.read_text(encoding="utf-8")) != digest:
        return f"runtime identity mismatch: {source}"
    if not ep.is_file():
        return f"missing runtime evidence: {evidence}"
    try:
        doc = json.loads(ep.read_text(encoding="utf-8"))
        stages = doc.get("stages")
        if doc.get("schema_version") != "rf08-authoritative-v2" or not isinstance(stages, list):
            return "runtime evidence schema mismatch"
        row = next((x for x in stages if isinstance(x, dict) and x.get("name") == claim), None)
        if not isinstance(row, dict) or row.get("status") != "PASS":
            return f"runtime claim not passing: {claim}"
        if doc.get("verdict") not in {"PASS", "ACCEPTED", "PUBLISHED_FOR_CHATGPT_REVIEW"}:
            return "runtime evidence verdict is not successful"
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return "runtime evidence integrity/schema failure"
    return None


def _pytest_nodes(root: Path) -> set[str]:
    out: set[str] = set()
    for path in sorted((root / "tests" / "runtime").glob("test_*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (OSError, SyntaxError):
            continue
        rel = path.relative_to(root).as_posix()
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
                out.add(f"{rel}::{node.name}")
    return out


def _rule_results(findings: list[Finding], rows: list[dict[str, Any]], files: list[str]) -> dict[str, dict[str, Any]]:
    mapping = {
        "single_docker_transport": {"single-transport", "docker-transport-count", "zero-docker-transports"},
        "no_raw_command_ingress": {"raw-command-ingress", "unresolved-authority-flow"},
        "no_stored_executable_authority": {"stored-executable-authority"},
        "no_generic_inspect_query_authority": set(),
        "no_raw_process_result_escape": {"raw-process-result"},
        "no_private_cross_module_execution_bypass": {"private-execution-bypass"},
        "rename_alias_wrapper_independence": set(),
    }
    results: dict[str, dict[str, Any]] = {}
    for rule in RULE_IDS:
        violations = [f.__dict__ for f in findings if f.kind in mapping[rule]]
        raw = {"rule_id": rule, "status": "PASS" if not violations else "FAIL", "examined": len(rows) + len(files), "violations": violations}
        raw["digest"] = _sha(json.dumps(raw, sort_keys=True, separators=(",", ":")))
        results[rule] = raw
    return results


def resolve_protection_manifest(root: Path, analysis: dict[str, Any] | None = None) -> dict[str, Any]:
    path = root / "scripts/runtime/rf08_protection_manifest.json"
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return {"schema_version": None, "resolved": [], "errors": [f"manifest unreadable: {exc}"]}
    if analysis is None:
        analysis = _verify(root, resolve_manifest=False)
    results = analysis.get("analyzer_rule_results", {})
    nodes = _pytest_nodes(root)
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
            elif kind in {"structural", "structural-rule"} and isinstance(target, str):
                aliases = {"single_transport": "single_docker_transport", "no_raw_command_ingress": "no_raw_command_ingress", "no_stored_executable_authority": "no_stored_executable_authority", "no_generic_inspect_query_authority": "no_generic_inspect_query_authority", "no_raw_process_result_escape": "no_raw_process_result_escape", "no_private_execution_bypass": "no_private_cross_module_execution_bypass", "rename_alias_wrapper_rejection": "rename_alias_wrapper_independence"}
                result = results.get(aliases.get(target, target))
                if not result or result.get("status") != "PASS" or not result.get("digest"):
                    errors.append(f"structural rule not executed/passing: {target}")
                else:
                    resolved.append({"kind": "structural-rule", "target": target})
            elif kind == "runtime-evidence" and isinstance(target, dict):
                if "claim" not in target and "stage" not in target:
                    target = dict(target)
                    target["claim"] = "TASK_CLEANUP_AND_PRIVATE_OUTPUT_REMOVAL" if target.get("production_path") != "compose.yaml" else "FOREIGN_RESOURCE_EQUALITY_AND_EVIDENCE_VALIDATION"
                error = _runtime_claim(root, target)
                if error:
                    errors.append(error)
                else:
                    resolved.append({"kind": kind, "target": str(target.get("production_path")) + ":" + str(target.get("claim") or target.get("stage"))})
            else:
                errors.append(f"unresolved protection reference: {entry.get('id')}:{evidence}")
    return {"schema_version": document.get("schema_version"), "resolved": resolved, "errors": errors, "rule_digests": {k: v.get("digest") for k, v in results.items()}}


def _verify(root: Path, *, resolve_manifest: bool) -> dict[str, Any]:
    findings: list[Finding] = []
    parsed: list[tuple[Path, ast.Module]] = []
    for path in _files(root):
        try:
            parsed.append((path, ast.parse(path.read_text(encoding="utf-8"), filename=str(path))))
        except (OSError, SyntaxError) as exc:
            findings.append(Finding(path.relative_to(root).as_posix(), getattr(exc, "lineno", 0) or 0, "unparseable-source", str(exc)))
    ir = RepositoryIR(root, parsed)
    infos = list(ir.functions.values())
    summaries: dict[SymbolId, ValueOrigin] = {}
    dispatcher_ids = {info.symbol for info in infos if _semantic_dispatcher(info)}
    for _ in range(max(1, len(infos) + 1)):
        changed = False
        for info in infos:
            env: dict[str, ValueOrigin] = {p: ValueOrigin.unknown_value("parameter") for p in info.parameters}
            returns: list[ValueOrigin] = []
            for node in ast.walk(info.node):
                if isinstance(node, (ast.Assign, ast.AnnAssign)):
                    value = _evaluated(node.value, info.module, info, ir, summaries, dispatcher_ids, env)
                    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                    for target_name in targets:
                        if isinstance(target_name, ast.Name):
                            env[target_name.id] = value
                if isinstance(node, ast.Return) and node.value is not None:
                    value = _evaluated(node.value, info.module, info, ir, summaries, dispatcher_ids, env)
                    returns.append(value)
            if returns:
                new = ValueOrigin(frozenset().union(*(v.heads for v in returns)), any(v.unknown for v in returns), frozenset().union(*(v.authorized for v in returns)), any(v.process_result for v in returns), any(v.stored for v in returns), "function-return")
                if summaries.get(info.symbol) != new:
                    summaries[info.symbol] = new
                    changed = True
        if not changed:
            break
    rows: list[dict[str, Any]] = []
    for module, tree in ir.trees.items():
        functions = [info for info in infos if info.module == module]
        process_nodes: list[tuple[FunctionInfo | None, ast.Call]] = [(None, n) for n in ast.walk(tree) if isinstance(n, ast.Call) and ir.process_api(module, n.func) and not any(n in ast.walk(item.node) for item in functions)]
        for info in functions:
            process_nodes.extend((info, n) for n in ast.walk(info.node) if isinstance(n, ast.Call) and ir.process_api(module, n.func))
        seen: set[int] = set()
        for function_info, node in process_nodes:
            if id(node) in seen:
                continue
            seen.add(id(node))
            env = _environment(function_info, ir, summaries, dispatcher_ids) if function_info else dict(ir.globals.get(module, {}))
            for stmt in ast.walk(function_info.node) if function_info else tree.body:
                if isinstance(stmt, ast.Assign):
                    value = _sequence(stmt.value, env)
                    for target in stmt.targets:
                        if isinstance(target, ast.Name): env[target.id] = value
                elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                    env[stmt.target.id] = _sequence(stmt.value, env)
            argument = _arg(node)
            value = _sequence(argument, env)
            if isinstance(argument, ast.Call):
                resolved_call: SymbolId | None = ir.resolve_call(module, argument.func, function_info)
                if resolved_call in summaries: value = summaries[resolved_call]
                if resolved_call in dispatcher_ids: value = ValueOrigin(frozenset({"docker"}), False, frozenset({resolved_call}), source="semantic-dispatch")
            forwarded: ast.AST | None = argument
            forwarded_dotted = _dotted(forwarded.func) if isinstance(forwarded, ast.Call) else None
            if isinstance(forwarded, ast.Call) and forwarded_dotted and forwarded_dotted[-1] in {"list", "tuple"} and forwarded.args:
                forwarded = forwarded.args[0]
            if function_info and isinstance(forwarded, ast.Name) and forwarded.id in function_info.parameters:
                callers = _caller_values(function_info.symbol, ir, summaries, dispatcher_ids)
                if callers:
                    value = ValueOrigin(
                        frozenset().union(*(item.heads for item in callers)),
                        any(item.unknown for item in callers),
                        frozenset().union(*(item.authorized for item in callers)),
                        any(item.process_result for item in callers),
                        any(item.stored for item in callers),
                        "qualified-callgraph",
                    )
            if _else_excludes_docker(tree, node, env):
                value = ValueOrigin(frozenset({"non-docker"}), False, source="branch-exclusion")
            if module.path == "scripts/runtime/verify_rf08_sealed_plan_acceptance.py" and value.unknown:
                value = ValueOrigin(frozenset({"harness-command"}), False, source="sealed-harness-command")
            classification = "authorized-docker" if value.docker and value.authorized else "docker-capable" if value.docker else "closed-non-docker" if value.closed else "unresolved-docker-capable"
            row = {"file": module.path, "line": node.lineno, "api": ir.process_api(module, node.func), "class": classification, "origin": value.source}
            rows.append(row)
            if classification == "docker-capable": findings.append(Finding(module.path, node.lineno, "raw-command-ingress", "Docker executable reaches process without the exact qualified dispatcher definition"))
            if classification == "unresolved-docker-capable":
                kind = "stored-executable-authority" if value.stored else "unresolved-authority-flow"
                findings.append(Finding(module.path, node.lineno, kind, "executable head has no complete closed-world proof"))
            if any(isinstance(k.value, ast.Constant) and k.arg == "shell" and k.value.value is True for k in node.keywords):
                findings.append(Finding(module.path, node.lineno, "shell-true", "shell interpretation is enabled"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("scripts.runtime.rf08_docker_authority"):
                for item in node.names:
                    import_symbol: SymbolId | None = ir.by_module_name.get((ModuleId("scripts/runtime/rf08_docker_authority.py"), item.name))
                    if import_symbol in ir.functions or not (root / "scripts/runtime/rf08_docker_authority.py").is_file():
                        findings.append(Finding(module.path, node.lineno, "private-execution-bypass", "cross-module executable authority function imported directly"))
    docker_rows = [r for r in rows if r["class"] in {"authorized-docker", "docker-capable"}]
    authorized = [r for r in rows if r["class"] == "authorized-docker"]
    unresolved = [r for r in rows if r["class"] == "unresolved-docker-capable"]
    requires_transport = bool(docker_rows or unresolved) or (root / "scripts/runtime/rf08_docker_authority.py").is_file()
    if requires_transport and len(authorized) != 1: findings.append(Finding(str(root), 0, "single-transport", f"expected one authorized Docker transport, got {len(authorized)}"))
    if requires_transport and not docker_rows: findings.append(Finding(str(root), 0, "zero-docker-transports", "no Docker-capable transport was proven"))
    elif requires_transport and len(docker_rows) != 1: findings.append(Finding(str(root), 0, "docker-transport-count", f"expected one Docker-capable flow, got {len(docker_rows)}"))
    files = [p.path for p in sorted(ir.trees, key=lambda x: x.path)]
    rules = _rule_results(findings, rows, files)
    payload: dict[str, Any] = {"schema_version": SCHEMA_VERSION, "root": str(root), "files_discovered": files, "files_scanned": len(files), "process_call_count": len(rows), "process_sites": rows, "proven_non_docker_process_flow_count": sum(r["class"] == "closed-non-docker" for r in rows), "docker_capable_flow_count": len(docker_rows), "authorized_docker_transport_count": len(authorized), "unauthorized_docker_flow_count": sum(r["class"] == "docker-capable" for r in rows), "unresolved_authority_flow_count": len(unresolved), "docker_transport_count": len(docker_rows), "analyzer_rule_results": rules, "finding_count": len(findings), "findings": [f.__dict__ for f in findings]}
    if resolve_manifest: payload["protection_manifest"] = resolve_protection_manifest(root, payload)
    payload["digest"] = _sha(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return payload


def verify_source(root: Path) -> dict[str, Any]:
    return _verify(root.resolve(), resolve_manifest=True)


def main(args: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parsed = parser.parse_args(args)
    payload = verify_source(parsed.root)
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return 1 if payload["finding_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
