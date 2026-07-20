"""AST guards proving Admin & Support remains a semantic-only boundary."""

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[2]
PACKAGE = ROOT / "src/mayak/modules/admin_and_support"
FILES = sorted(PACKAGE.glob("*.py"))
EXPECTED_FILES = sorted(
    [
        "__init__.py",
        "access_actions.py",
        "anchor_actions.py",
        "beacon_actions.py",
        "case_records.py",
        "contracts.py",
        "notification_actions.py",
        "role_actions.py",
        "safe_reads.py",
        "tariff_actions.py",
    ]
)
CONTRACT_IMPORTS = {
    "__future__",
    "enum",
    "typing",
    "pydantic",
    "mayak.contracts",
    "mayak.contracts.metadata",
    "mayak.platform.boundaries",
    "mayak.modules.admin_and_support.contracts",
    "mayak.modules.admin_and_support.safe_reads",
}
PACKAGE_IMPORTS = (
    {"mayak.platform.boundaries"}
    | {
        "mayak.modules.admin_and_support." + name[:-3]
        for name in EXPECTED_FILES
        if name not in {"__init__.py", "contracts.py"}
    }
    | {"mayak.modules.admin_and_support.contracts"}
)
FORBIDDEN_PARTS = (
    "client",
    "gateway",
    "repository",
    "service",
    "worker",
    "handler",
    "router",
    "endpoint",
    "runtime",
    "session",
    "connection",
)
FORBIDDEN_CALLS = {
    "send",
    "publish",
    "dispatch",
    "retry",
    "persist",
    "save",
    "request",
    "post",
    "put",
    "delete",
}
SENSITIVE_PARTS = (
    "token",
    "raw_payload",
    "raw_provider_payload",
    "private_key",
    "secret",
    "bytes",
)


def _relative_name(node: ast.ImportFrom) -> str:
    if node.module is None:
        return "." * node.level
    return "." * node.level + node.module


def _normalized_import(node: ast.Import | ast.ImportFrom, package_init: bool) -> list[str]:
    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names]
    raw = _relative_name(node)
    if package_init and raw == ".contracts":
        return ["mayak.modules.admin_and_support.contracts"]
    if package_init and raw in {
        ".safe_reads",
        ".role_actions",
        ".tariff_actions",
        ".access_actions",
        ".anchor_actions",
        ".beacon_actions",
        ".case_records",
        ".notification_actions",
    }:
        return ["mayak.modules.admin_and_support" + raw]
    return [raw]


def violations(source: str, *, package_init: bool = False) -> list[str]:
    """Return stable violation labels without importing or executing source."""
    tree = ast.parse(source)
    allowed = PACKAGE_IMPORTS if package_init else CONTRACT_IMPORTS
    found: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for module in _normalized_import(node, package_init):
                if module not in allowed:
                    found.append(f"forbidden-import:{module}")
        if isinstance(node, ast.ClassDef):
            lowered = node.name.lower()
            if not node.name.startswith("Support") and any(
                part in lowered for part in FORBIDDEN_PARTS
            ):
                found.append(f"forbidden-class:{node.name}")
        if isinstance(node, ast.Call):
            name = (
                node.func.id
                if isinstance(node.func, ast.Name)
                else node.func.attr
                if isinstance(node.func, ast.Attribute)
                else ""
            )
            network_get = (
                name == "get"
                and isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id in {"requests", "httpx"}
            )
            if name in FORBIDDEN_CALLS or network_get:
                found.append(f"forbidden-call:{name}")
            if name in {"setattr", "__import__", "eval", "exec", "compile"}:
                found.append(f"forbidden-dynamic:{name}")
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Name) and any(
                    part in target.id.lower() for part in SENSITIVE_PARTS
                ):
                    value = node.value
                    safe = isinstance(value, ast.Constant) and value.value is False
                    annotation = (
                        ast.unparse(node.annotation)
                        if isinstance(node, ast.AnnAssign) and node.annotation
                        else ""
                    )
                    if not safe or "Literal[False]" not in annotation:
                        found.append(f"unsafe-sensitive-field:{target.id}")
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            annotations = [a.annotation for a in node.args.args if a.annotation]
            if node.returns:
                annotations.append(node.returns)
            if any(
                any(
                    word in ast.unparse(a)
                    for word in ("__import__", "eval", "exec", "compile", "getattr")
                )
                for a in annotations
            ):
                found.append("dynamic-annotation")
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)) and isinstance(node.value, ast.Call):
            found.append("top-level-runtime-instance")
    return list(dict.fromkeys(found))


def test_exact_production_file_set() -> None:
    assert [p.name for p in FILES] == EXPECTED_FILES


def test_pycache_is_the_only_ignored_entry(tmp_path: Path) -> None:
    package = tmp_path / "admin_and_support"
    package.mkdir()
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "__pycache__").mkdir()
    assert sorted(p.name for p in package.iterdir() if p.name != "__pycache__") == ["__init__.py"]
    (package / "unexpected.py").write_text("", encoding="utf-8")
    assert "unexpected.py" in [p.name for p in package.iterdir() if p.name != "__pycache__"]


def test_import_isolation_and_no_runtime_constructs() -> None:
    for path in FILES:
        source = path.read_text(encoding="utf-8")
        assert not violations(source, package_init=path.name == "__init__.py"), path
        tree = ast.parse(source)
        assert not any(
            isinstance(n, (ast.Import, ast.ImportFrom)) and "pytest" in _normalized_import(n, False)
            for n in ast.walk(tree)
        )
        assert not any(
            isinstance(n, ast.Call)
            and isinstance(n.func, ast.Name)
            and n.func.id in {"eval", "exec", "compile", "__import__", "setattr"}
            for n in ast.walk(tree)
        )


def test_sensitive_fields_are_explicitly_safe() -> None:
    for path in FILES:
        assert not any(
            label.startswith("unsafe-sensitive-field")
            for label in violations(
                path.read_text(encoding="utf-8"), package_init=path.name == "__init__.py"
            )
        )


UNSAFE = [
    "from mayak.foreign import X",
    "import requests",
    "requests.get('synthetic')",
    "import sqlalchemy",
    "class Repository: pass",
    "class Worker: pass",
    "import os\nos.getenv('SYNTHETIC')",
    "import subprocess\nsubprocess.run([])",
    "setattr(target, 'value', 1)",
    "from importlib import import_module\nimport_module('x')",
    "class Data:\n    token: str",
    "class Data:\n    raw_payload: bytes",
    "client = Client()",
]


@pytest.mark.parametrize("snippet", UNSAFE)
def test_required_negative_controls_are_detected(snippet: str) -> None:
    assert violations(snippet), snippet


@pytest.mark.parametrize(
    "snippet",
    [
        "from __future__ import annotations",
        "from enum import Enum",
        "from typing import Literal",
        "from pydantic import BaseModel",
        "from mayak.contracts import ContractMetadata",
        "from mayak.contracts.metadata import ContractMetadata",
        "from mayak.platform.boundaries import ADMIN_AND_SUPPORT_MODULE_ID",
        "from .contracts import SupportCase",
        "class SupportServiceLevel: pass",
    ],
)
def test_safe_controls_are_accepted(snippet: str) -> None:
    assert violations(snippet, package_init=snippet.startswith("from .")) == []


def test_legitimate_support_names_are_not_false_positives() -> None:
    assert violations("class SupportCaseActionOutcome: pass") == []


def test_production_models_are_frozen_and_extra_forbid() -> None:
    for path in FILES:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and any(
                isinstance(b, ast.Name) and b.id == "BaseModel" for b in node.bases
            ):
                rendered = ast.unparse(node)
                assert "extra='forbid'" in rendered or 'extra="forbid"' in rendered
                assert "frozen=True" in rendered
