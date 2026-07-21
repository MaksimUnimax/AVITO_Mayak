"""Static Web Cabinet boundary and safety contract checks."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[2]
WEB = ROOT / "src/mayak/modules/web_cabinet"
EXPECTED_FILES = (
    "__init__.py",
    "admin_analytics.py",
    "auth_context.py",
    "beacon_commands.py",
    "channel_linking.py",
    "entitlement_projections.py",
    "notification_history.py",
    "read_models.py",
    "security_privacy.py",
    "status_display.py",
    "support_handoff.py",
)
FORBIDDEN_IMPORT_ROOTS = frozenset(
    {
        "requests",
        "httpx",
        "aiohttp",
        "urllib3",
        "fastapi",
        "django",
        "flask",
        "sqlalchemy",
        "alembic",
        "psycopg",
        "psycopg2",
        "redis",
        "celery",
        "aiogram",
        "telethon",
        "subprocess",
    }
)
FORBIDDEN_WORDS = frozenset(
    {
        "gateway",
        "repository",
        "service",
        "worker",
        "router",
        "endpoint",
        "runtime",
        "session_store",
        "database",
        "migration",
        "subprocess",
        "socket",
        "getenv",
        "client",
        "handler",
        "session_store",
        "environment",
        "filesystem",
    }
)
SENSITIVE_FIELDS = frozenset(
    {
        "password",
        "token",
        "cookie",
        "private_key",
        "raw_payload",
        "raw_provider_payload",
        "private_support",
        "stack_trace",
        "secret",
        "personal_data",
        "one_time_code",
        "session_material",
        "environment_secret",
        "raw_avito_payload",
        "internal_exception",
        "unnecessary_personal_data",
    }
)


def _tree(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def violations(source: str) -> list[str]:
    tree = ast.parse(source)
    found: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] in FORBIDDEN_IMPORT_ROOTS:
                    found.append(f"import:{alias.name}")
        elif (
            isinstance(node, ast.ImportFrom)
            and node.module
            and node.module.split(".")[0] in FORBIDDEN_IMPORT_ROOTS
        ):
            found.append(f"import:{node.module}")
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.name.lower() in FORBIDDEN_WORDS:
                found.append(f"implementation:{node.name}")
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id.lower() in SENSITIVE_FIELDS:
                annotation = ast.unparse(node.annotation)
                default = ast.unparse(node.value) if node.value is not None else None
                if annotation != "Literal[False]" or default != "False":
                    found.append(f"sensitive:{node.target.id}")
        elif (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in {"eval", "exec", "compile", "__import__"}
        ):
            found.append(f"call:{node.func.id}")
        elif (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in {"getenv", "run", "Popen", "call", "check_call", "connect"}
        ):
            found.append(f"call:{node.func.attr}")
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr in {"import_module", "getattr", "setattr", "__build_class__"}:
                found.append(f"reflection:{node.func.attr}")
        elif isinstance(node, ast.Attribute) and node.attr in {"git", "diff", "index", "status"}:
            found.append(f"worktree:{node.attr}")
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            if ".git" in node.value or "git status" in node.value or "git diff" in node.value:
                found.append("worktree:git")
    return found


def test_exact_production_file_inventory_and_ast_boundaries() -> None:
    actual = tuple(sorted(p.name for p in WEB.iterdir() if p.is_file() and p.name != "__pycache__"))
    assert actual == tuple(sorted(EXPECTED_FILES))
    for path in sorted(WEB.glob("*.py")):
        source = path.read_text(encoding="utf-8")
        assert not violations(source)
        tree = _tree(path)
        implementation_names = {
            node.name.lower()
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        }
        assert not implementation_names & FORBIDDEN_WORDS
        assert not any(isinstance(n, (ast.Global, ast.Nonlocal)) for n in ast.walk(tree))
        assert not any(
            isinstance(n, ast.Call)
            and isinstance(n.func, ast.Name)
            and n.func.id in {"eval", "exec"}
            for n in ast.walk(tree)
        )
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name.startswith("_"):
                continue
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                assert node.target.id not in SENSITIVE_FIELDS or "Literal[False]" in ast.unparse(
                    node.annotation
                )


def test_required_unsafe_and_safe_synthetic_snippets() -> None:
    unsafe = (
        "import requests\n",
        "from fastapi import FastAPI\n",
        "import subprocess\n",
        "x = eval('1')\n",
        "class Client: pass\n",
        "secret: str = 'x'\n",
        "import importlib\nimportlib.import_module('x')\n",
        "from pathlib import Path\nPath('.git').read_text()\n",
        "import subprocess\nsubprocess.run(['git', 'status'])\n",
    )
    safe = "from typing import Literal\nallowed: Literal[False] = False\n"
    assert all(violations(snippet) for snippet in unsafe)
    assert violations(safe) == []


@pytest.mark.parametrize(
    "snippet,label",
    (
        ("class Gateway: pass\n", "implementation:Gateway"),
        ("def repository(): pass\n", "implementation:repository"),
        ("password: str = 'x'\n", "sensitive:password"),
        ("token: Literal[False] = True\n", "sensitive:token"),
        ("x = compile('1', 'x', 'exec')\n", "call:compile"),
        ("importlib.import_module('x')\n", "reflection:import_module"),
        ("Path('.git/index')\n", "worktree:git"),
    ),
)
def test_detector_has_literal_negative_controls(snippet: str, label: str) -> None:
    assert label in violations(snippet)


def test_every_direct_semantic_model_has_literal_safety_config() -> None:
    for path in sorted(WEB.glob("*.py")):
        tree = _tree(path)
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name.startswith("_") is False:
                bases = {ast.unparse(base) for base in node.bases}
                if any("_Web" in base for base in bases):
                    configs = [
                        n
                        for n in node.body
                        if isinstance(n, ast.Assign)
                        and any(
                            isinstance(t, ast.Name) and t.id == "model_config" for t in n.targets
                        )
                    ]
                    assert not configs
                    parent_names = {
                        parent.name
                        for parent in tree.body
                        if isinstance(parent, ast.ClassDef) and parent.name in bases
                    }
                    assert parent_names
        assert (
            'ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)'
            in path.read_text(encoding="utf-8")
            or path.name == "__init__.py"
        )


def test_architecture_negative_controls_are_static_only() -> None:
    source = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    assert not any(
        isinstance(n, ast.Attribute) and n.attr in {"git", "diff", "index"} for n in ast.walk(tree)
    )
    assert not any(
        isinstance(n, ast.Call)
        and isinstance(n.func, ast.Name)
        and n.func.id in {"subprocess", "system"}
        for n in ast.walk(tree)
    )


@pytest.mark.parametrize("name", EXPECTED_FILES)
def test_inventory_member_is_present(name: str) -> None:
    assert (WEB / name).is_file()
