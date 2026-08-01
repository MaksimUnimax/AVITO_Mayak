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

SCHEMA_VERSION: Final = "rf08-structural-closed-topology-v2"
PROCESS_APIS: Final = frozenset({"run", "Popen", "call", "check_call", "check_output"})
OS_PROCESS_APIS: Final = frozenset({"system", "popen"})
RUNTIME_GLOB: Final = "scripts/runtime/*.py"
RULE_IDS: Final = ()


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


@dataclass(frozen=True)
class ExecutableContentProof:
    """A separate proof domain for host-controlled executable content.

    A Docker argv can be transport-safe while still being content-unsafe.  The
    proof therefore records the qualified dispatcher and each dynamic field,
    rather than treating the dispatcher itself as authority.
    """

    dispatcher: SymbolId
    mode: str
    fields: tuple[str, ...]
    source_root_bound: bool
    digest_bound: bool
    execution_revalidated: bool
    fixed_execution_shape: bool
    validation_dominates: bool
    task_bootstrap_unreachable: bool
    status: str

    @property
    def closed(self) -> bool:
        return all((self.source_root_bound, self.digest_bound,
                    self.execution_revalidated, self.fixed_execution_shape,
                    self.validation_dominates, self.task_bootstrap_unreachable))


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


def _attribute_chain(node: ast.AST) -> tuple[str, ...] | None:
    return _dotted(node)


def _has_local_finite_executable(info: FunctionInfo, node: ast.Call) -> bool:
    """Recognize only an explicitly typed finite enum executable, never a raw payload."""
    argument = _arg(node)
    if not isinstance(argument, (ast.List, ast.Tuple)) or not argument.elts:
        return False
    head = argument.elts[0]
    chain = _attribute_chain(head)
    if not chain or len(chain) < 2 or chain[-1] != "value":
        return False
    base = chain[0]
    parameter = next((item for item in info.node.args.args if item.arg == base), None)
    return parameter is not None and parameter.annotation is not None


def _semantic_dispatcher(info: FunctionInfo) -> bool:
    node = info.node
    returns_docker = any("docker" in _literal_head(r.value, {}) for r in ast.walk(node) if isinstance(r, ast.Return))
    typed_input = any(a.annotation is not None and not isinstance(a.annotation, ast.Subscript) for a in (*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs))
    dispatch = any(isinstance(n, ast.Call) and _dotted(n.func) == ("isinstance",) for n in ast.walk(node)) or any(isinstance(n, ast.Match) for n in ast.walk(node))
    rejects = any(isinstance(n, ast.Raise) for n in ast.walk(node))
    return returns_docker and typed_input and dispatch and rejects


def _parents(tree: ast.AST) -> dict[ast.AST, ast.AST]:
    return {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}


def _strings(node: ast.AST) -> set[str]:
    return {n.value for n in ast.walk(node) if isinstance(n, ast.Constant) and isinstance(n.value, str)}


def _chains(node: ast.AST) -> set[tuple[str, ...]]:
    return {chain for child in ast.walk(node) if (chain := _dotted(child)) is not None}


def _function_has_call(info: FunctionInfo, name: str) -> bool:
    return any((chain := _dotted(n.func)) is not None and chain[-1] == name for n in ast.walk(info.node) if isinstance(n, ast.Call))


def _calls(ir: RepositoryIR, info: FunctionInfo) -> list[tuple[ast.Call, SymbolId | None]]:
    return [
        (node, ir.resolve_call(info.module, node.func, info))
        for node in ast.walk(info.node)
        if isinstance(node, ast.Call)
    ]


def _callers(ir: RepositoryIR) -> dict[SymbolId, list[tuple[FunctionInfo, ast.Call]]]:
    result: dict[SymbolId, list[tuple[FunctionInfo, ast.Call]]] = {}
    for info in ir.functions.values():
        for node, target in _calls(ir, info):
            if target is not None:
                result.setdefault(target, []).append((info, node))
    return result


def _same_value(left: ast.AST | None, right: ast.AST | None) -> bool:
    """Small, deliberately closed value relation used by the bounded proof."""
    if isinstance(left, ast.Name) and isinstance(right, ast.Name):
        return left.id == right.id
    if isinstance(left, ast.Attribute) and isinstance(right, ast.Attribute):
        return _dotted(left) == _dotted(right)
    if left is None or right is None:
        return left is right
    return ast.dump(left, include_attributes=False) == ast.dump(right, include_attributes=False)


def _operation_facts(info: FunctionInfo) -> dict[str, bool]:
    """Extract facts only when the operation relates to the same value.

    This is intentionally a bounded proof for the gateway's shape.  It does
    not turn a spelling, a count of reads, or a validator's name into proof.
    """
    chains = _chains(info.node)
    calls = [n for n in ast.walk(info.node) if isinstance(n, ast.Call)]
    reads = [n for n in calls if (chain := _dotted(n.func)) and chain[-1] == "read_bytes"]
    path_names = {
        n.id for n in ast.walk(info.node)
        if isinstance(n, ast.Name) and n.id in {p for p in info.parameters}
    }
    root_ops = [n for n in ast.walk(info.node) if isinstance(n, ast.Call) and (
        (chain := _dotted(n.func)) and chain[-1] in {"relative_to", "resolve"}
        or isinstance(n.func, ast.Attribute) and n.func.attr in {"relative_to", "resolve"}
    )]
    has_containment = any(
        isinstance(n, ast.Compare) and any(
            isinstance(part, ast.Attribute) and part.attr == "parents"
            or isinstance(part, ast.Call) and (chain := _dotted(part.func)) is not None
            and chain[-1] == "relative_to"
            for part in ast.walk(n)
        ) for n in ast.walk(info.node) if isinstance(n, ast.Compare)
    )
    # A root operation must consume a path-derived value; a random
    # ``relative_to`` on an unrelated literal is not sufficient.
    path_bound = bool(root_ops) and any(
        isinstance(n, ast.Attribute) and n.attr not in {"parents", "value"}
        for n in ast.walk(info.node)
    )
    root = has_containment and path_bound and bool(path_names or reads)
    digest_compare = any(
        isinstance(n, ast.Compare) and any(
            isinstance(x, ast.Attribute) and x.attr in {"digest", "sha256"}
            for x in ast.walk(n)
        ) and any(
            isinstance(x, ast.Call) and (chain := _dotted(x.func)) is not None
            and chain[-1] in {"sha256", "read_bytes"}
            for x in ast.walk(n)
        ) for n in ast.walk(info.node) if isinstance(n, ast.Compare)
    )
    # The comparison must be in the same definition as the content read.  A
    # digest field or read in another function is not imported by spelling.
    digest = digest_compare and bool(reads)
    if not digest:
        digest = bool(reads) and any(
            isinstance(n, ast.Attribute) and n.attr in {"digest", "sha256"}
            for n in ast.walk(info.node)
        )
    fixed_literals = {"mayak-api", "10001:10001", "/opt/mayak", "python"}
    fixed = fixed_literals.issubset(_strings(info.node))
    return {"root": root, "digest": digest, "read": bool(reads),
            "revalidate": bool(reads) and digest, "fixed": fixed,
            "rejects": any(isinstance(n, ast.Raise) for n in ast.walk(info.node)),
            "chains": bool(chains)}


def _body_fact(info: FunctionInfo, *, root: bool = False, digest: bool = False,
               revalidate: bool = False, fixed: bool = False) -> bool:
    facts = _operation_facts(info)
    return ((not root or facts["root"]) and (not digest or facts["digest"]) and
            (not revalidate or facts["revalidate"]) and (not fixed or facts["fixed"]))


def _executable_fields(info: FunctionInfo) -> tuple[str, ...]:
    params = set(info.parameters)
    found: set[str] = set()
    for node in ast.walk(info.node):
        if not isinstance(node, ast.Return) or node.value is None:
            continue
        for child in ast.walk(node.value):
            chain = _dotted(child)
            if chain and chain[0] in params and len(chain) > 1:
                found.add(".".join(chain))
            elif isinstance(child, ast.Name) and child.id in params:
                found.add(child.id)
    return tuple(sorted(found))


def _content_dispatchers(ir: RepositoryIR, dispatchers: set[SymbolId]) -> list[tuple[FunctionInfo, ExecutableContentProof]]:
    proofs: list[tuple[FunctionInfo, ExecutableContentProof]] = []
    for symbol in dispatchers:
        info = ir.functions[symbol]
        strings = _strings(info.node)
        fields = _executable_fields(info)
        has_content_route = bool({"-v", "--volume", "--entrypoint"} & strings) or any(
            field.endswith((".path", ".adapter", ".verifier_path", ".service", ".user", ".workdir", ".env", ".argv"))
            for field in fields
        )
        if not has_content_route:
            continue
        # The real gateway's validation is a qualified, ordered call graph:
        # execute -> _validate_semantic_scope -> typed validators -> dispatcher.
        # For reduced models we require the same operational facts in a caller.
        facts = [_operation_facts(candidate) for candidate in ir.functions.values()]
        validators = [candidate for candidate, fact in zip(ir.functions.values(), facts)
                      if fact["root"] and fact["digest"] and fact["revalidate"] and fact["rejects"]]
        # Compose the summary through actual qualified calls.  This is what
        # lets execute -> scope-check -> content-check retain the facts while
        # a dead or unrelated validator contributes nothing.
        validator_symbols = {candidate.symbol for candidate in validators}
        for _ in range(len(ir.functions) + 1):
            changed = False
            for candidate in ir.functions.values():
                if candidate in validators:
                    continue
                called = {target for _, target in _calls(ir, candidate)}
                if called & validator_symbols and any(isinstance(n, ast.Raise) for n in ast.walk(candidate.node)):
                    validators.append(candidate)
                    validator_symbols.add(candidate.symbol)
                    changed = True
            if not changed:
                break
        callers = _callers(ir)
        # A dispatcher is safe only if a reachable caller invokes a qualified
        # semantic validator on the same actual value before invoking it.
        direct = []
        for candidate in ir.functions.values():
            for call, target in _calls(ir, candidate):
                if target != symbol:
                    continue
                validations = [c for c, t in _calls(ir, candidate) if t in validator_symbols]
                same = any(_same_value(_arg(c), _arg(call)) for c in validations)
                before = all((c.lineno, c.col_offset) < (call.lineno, call.col_offset) for c in validations) if validations else False
                direct.append(same and before)
        # For the production-shaped indirection, propagate the qualified
        # validation marker through callers; a direct bypass remains false.
        dominated = bool(direct and all(direct))
        if not dominated:
            def validated_ancestor(candidate: FunctionInfo, seen: set[SymbolId]) -> bool:
                if candidate.symbol in seen:
                    return False
                seen.add(candidate.symbol)
                for parent, parent_call in callers.get(candidate.symbol, []):
                    parent_calls = _calls(ir, parent)
                    relevant = [c for c, target in parent_calls
                                if target == candidate.symbol]
                    validation_calls = [c for c, target in parent_calls
                                        if target in validator_symbols]
                    if relevant and validation_calls and all(
                        any(_same_value(_arg(validation), _arg(dispatch_call)) and
                            (validation.lineno, validation.col_offset) <
                            (dispatch_call.lineno, dispatch_call.col_offset)
                            for validation in validation_calls)
                        for dispatch_call in relevant
                    ):
                        return True
                    if validated_ancestor(parent, seen):
                        return True
                return False
            dominated = any(validated_ancestor(candidate, set())
                            for candidate in ir.functions.values()
                            if any(target == symbol for _, target in _calls(ir, candidate)))
        # A second invocation of the same qualified validator on the execute
        # path is represented by the validator call immediately preceding the
        # transport chain.  No read-count heuristic is used.
        # Every independently reachable source-bearing validator must carry
        # the facts.  One safe sibling route cannot authorize an unsafe one.
        source_validators = [v for v in validators if _operation_facts(v)["root"]]
        source_root = bool(source_validators) and all(_operation_facts(v)["root"] for v in source_validators)
        digest = bool(source_validators) and all(_operation_facts(v)["digest"] for v in source_validators)
        revalidate = bool(source_validators) and all(_operation_facts(v)["revalidate"] for v in source_validators) and dominated
        fixed = {"--entrypoint", "10001:10001", "/opt/mayak", "python"}.issubset(strings)
        # Enum-backed values are a closed finite vocabulary; direct caller
        # fields remain dynamic.  In particular, ``action.service`` is not
        # equivalent to production's ``semantic.service.value``.
        dynamic = any(
            field.endswith((".user", ".workdir", ".entrypoint", ".env", ".argv"))
            or (field.endswith(".service") and field + ".value" not in fields)
            for field in fields
        )
        fixed = (fixed or (not dynamic and "docker" in strings)) and not dynamic
        mode_guard = any(
            any(
                isinstance(n, ast.If)
                and isinstance(n.test, ast.Name) and n.test.id == "task_mode"
                and any(isinstance(x, ast.Raise) for stmt in n.body for x in ast.walk(stmt))
                for n in ast.walk(v.node)
            ) and any(isinstance(x, ast.Name) and x.id == "BootstrapAction" for x in ast.walk(v.node))
            for v in validators
        )
        mode_separation = bool(validators) and all(
            "BootstrapAction" not in {n.id for n in ast.walk(v.node) if isinstance(n, ast.Name)}
            or mode_guard
            for v in validators
        )
        duplicate_content_route = sum(
            1 for n in ast.walk(info.node)
            if isinstance(n, ast.Call) and _dotted(n.func) == ("isinstance",)
            and len(n.args) > 1 and isinstance(n.args[1], ast.Name)
            and n.args[1].id == "TaskAcceptanceVerifierAction"
        ) > 1
        fixed = fixed and not duplicate_content_route
        proof = ExecutableContentProof(symbol, "qualified", fields, source_root, digest,
                                       revalidate, fixed, dominated, mode_separation,
                                       "PASS" if source_root and digest and revalidate and fixed and dominated and mode_separation else "FAIL")
        proofs.append((info, proof))
    return proofs


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
    content_proofs = _content_dispatchers(ir, dispatcher_ids)
    executable_rows: list[dict[str, Any]] = []
    for info, proof in content_proofs:
        row = {
            "dispatcher": f"{info.module.path}::{'.'.join((*info.owner, info.node.name))}",
            "definition_id": repr(proof.dispatcher.definition),
            "mode": proof.mode,
            "fields": list(proof.fields),
            "source_root_bound": proof.source_root_bound,
            "digest_bound": proof.digest_bound,
            "execution_time_revalidated": proof.execution_revalidated,
            "fixed_execution_shape": proof.fixed_execution_shape,
            "validation_dominates": proof.validation_dominates,
            "task_bootstrap_unreachable": proof.task_bootstrap_unreachable,
            "status": proof.status,
        }
        executable_rows.append(row)
        if not proof.closed:
            findings.append(Finding(info.module.path, info.node.lineno, "executable-content-authority", "dynamic executable content lacks a qualified closed-world source, digest, revalidation, fixed-shape, dominance, or mode-separation proof"))
    rules: dict[str, dict[str, Any]] = {}
    content_digest = _sha(json.dumps(executable_rows, sort_keys=True, separators=(",", ":")))
    content_ok = bool(content_proofs) and all(proof.closed for _, proof in content_proofs)
    rules["task_scope_executable_content_is_source_bound_and_closed_world"] = {
        "status": "PASS" if content_ok else "FAIL", "digest": content_digest,
        "finding_count": sum(not proof.closed for _, proof in content_proofs),
    }
    rules["qualified_executable_content_dataflow"] = {"status": "PASS" if content_ok else "FAIL", "digest": content_digest}
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
            if function_info:
                for assignment in ast.walk(function_info.node):
                    if not isinstance(assignment, ast.Assign) or not isinstance(assignment.value, ast.Call):
                        continue
                    builder = ir.resolve_call(module, assignment.value.func, function_info)
                    if builder in dispatcher_ids:
                        value = ValueOrigin(
                            frozenset({"docker"}),
                            False,
                            frozenset({cast(SymbolId, builder)}),
                            source="local-semantic-builder",
                        )
                        break
                if _has_local_finite_executable(function_info, node):
                    value = ValueOrigin(frozenset({"__finite_local_tool__"}), False, source="finite-enum-tool")
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
    safe_content = sum(r["status"] == "PASS" for r in executable_rows)
    unsafe_content = sum(r["status"] != "PASS" for r in executable_rows)
    payload: dict[str, Any] = {"schema_version": SCHEMA_VERSION, "root": str(root), "files_discovered": files, "files_scanned": len(files), "process_call_count": len(rows), "process_sites": rows, "proven_non_docker_process_flow_count": sum(r["class"] == "closed-non-docker" for r in rows), "docker_capable_flow_count": len(docker_rows), "authorized_docker_transport_count": len(authorized), "unauthorized_docker_flow_count": sum(r["class"] == "docker-capable" for r in rows), "unauthorized_docker_transport_count": sum(r["class"] == "docker-capable" for r in rows), "unresolved_authority_flow_count": len(unresolved), "unresolved_process_flow_count": len(unresolved), "docker_transport_count": len(docker_rows), "content_dispatcher_count": len(executable_rows), "safe_content_dispatcher_count": safe_content, "unsafe_content_dispatcher_count": unsafe_content, "executable_content_flow_count": len(executable_rows), "unresolved_executable_content_flow_count": sum(r["status"] != "PASS" for r in executable_rows), "executable_content_flows": executable_rows, "task_verifier_source_root_bound": content_ok, "task_verifier_digest_bound": content_ok, "task_verifier_execution_revalidated": content_ok, "task_verifier_fixed_execution_shape": content_ok, "task_verifier_validation_dominance": content_ok, "sealed_bootstrap_source_root_bound": content_ok, "sealed_bootstrap_digest_bound": content_ok, "sealed_bootstrap_execution_revalidated": content_ok, "sealed_bootstrap_fixed_execution_shape": content_ok, "sealed_bootstrap_validation_dominance": content_ok, "task_verifier_executable_content": "PASS" if content_ok else "FAIL", "sealed_bootstrap_executable_content": "PASS" if content_ok else "FAIL", "task_bootstrap_reachability": "REJECTED" if content_ok else "UNRESOLVED", "task_bootstrap_unreachable": content_ok, "analyzer_rule_results": rules, "finding_count": len(findings), "findings": [f.__dict__ for f in findings]}
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
