"""Complete static boundary controls for the semantic-only AS-11 package."""

import ast
import importlib
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[2]
PACKAGE = ROOT / "src/mayak/modules/admin_and_support"
EXPECTED_FILES = (
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
)
FORBIDDEN_CLASSES = {
    "Client",
    "Gateway",
    "Repository",
    "Service",
    "Worker",
    "Handler",
    "Router",
    "Endpoint",
    "Runtime",
    "Session",
    "Connection",
}
FORBIDDEN_ROOTS = {
    "requests",
    "httpx",
    "aiohttp",
    "urllib3",
    "sqlalchemy",
    "alembic",
    "psycopg",
    "psycopg2",
    "redis",
    "celery",
    "fastapi",
    "django",
    "flask",
    "aiogram",
    "telethon",
}
FORBIDDEN_CALLS = {
    "get",
    "post",
    "put",
    "patch",
    "delete",
    "request",
    "send",
    "publish",
    "dispatch",
    "connect",
    "execute",
    "retry",
}
SENSITIVE = {
    "secret",
    "token",
    "password",
    "private_key",
    "one_time_code",
    "raw_payload",
    "raw_provider_payload",
    "raw_note_text",
    "full_private_message",
    "personal_data",
    "recipient_identity",
}
SAFE_IMPORTS = {
    "__future__",
    "enum",
    "typing",
    "pydantic",
    "mayak.contracts",
    "mayak.contracts.metadata",
    "mayak.platform.boundaries",
}


def package_entry_inventory(path: Path = PACKAGE) -> tuple[tuple[str, str], ...]:
    """Inventory every entry; only an exact __pycache__ directory is ignored."""
    result = []
    for entry in path.iterdir():
        if entry.is_dir() and entry.name == "__pycache__":
            continue
        kind = (
            "symlink"
            if entry.is_symlink()
            else "directory"
            if entry.is_dir()
            else "python"
            if entry.is_file() and entry.suffix == ".py"
            else "file"
        )
        result.append((entry.name, kind))
    return tuple(sorted(result))


def _root(name: str) -> str:
    return name.split(".", 1)[0]


def violations(source: str, *, package_init: bool = False) -> list[str]:
    tree = ast.parse(source)
    found: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if _root(alias.name) not in SAFE_IMPORTS and _root(alias.name) not in {"mayak"}:
                    found.append(f"forbidden-import:{alias.name}")
                if _root(alias.name) in FORBIDDEN_ROOTS:
                    found.append(f"forbidden-root:{_root(alias.name)}")
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module and _root(module) in FORBIDDEN_ROOTS:
                found.append(f"forbidden-root:{_root(module)}")
            if (
                node.level == 0
                and module
                and _root(module) not in SAFE_IMPORTS
                and _root(module) != "mayak"
                and module != "importlib"
            ):
                found.append(f"forbidden-import:{module}")
        elif isinstance(node, ast.ClassDef):
            if node.name in FORBIDDEN_CLASSES or any(
                node.name.endswith(s) for s in FORBIDDEN_CLASSES
            ):
                if node.name != "SupportServiceLevel":
                    found.append(f"forbidden-class:{node.name}")
        elif isinstance(node, ast.Call):
            fn = node.func
            name = (
                fn.attr
                if isinstance(fn, ast.Attribute)
                else fn.id
                if isinstance(fn, ast.Name)
                else ""
            )
            if name in FORBIDDEN_CALLS and not (
                name == "get"
                and isinstance(fn, ast.Attribute)
                and isinstance(fn.value, ast.Name)
                and fn.value.id
                not in {"client", "requests", "httpx", "socket", "session", "worker"}
            ):
                found.append(f"forbidden-call:{name}")
            if name in {
                "getenv",
                "environ",
                "run",
                "Popen",
                "system",
                "socket",
                "open",
                "eval",
                "exec",
                "compile",
                "__import__",
                "import_module",
                "setattr",
            }:
                found.append(f"forbidden-dynamic:{name}")
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if (
                    isinstance(target, ast.Name)
                    and target.id != "minimal_personal_data"
                    and any(word in target.id.lower() for word in SENSITIVE)
                ):
                    ann = (
                        ast.unparse(node.annotation)
                        if isinstance(node, ast.AnnAssign) and node.annotation
                        else ""
                    )
                    safe = (
                        isinstance(node.value, ast.Constant)
                        and node.value.value is False
                        and "Literal[False]" in ann
                    )
                    if not safe:
                        found.append(f"unsafe-sensitive-field:{target.id}")
        elif isinstance(node, ast.FunctionDef):
            anns = [a.annotation for a in node.args.args if a.annotation] + (
                [node.returns] if node.returns else []
            )
            if any(
                any(
                    x in ast.unparse(a)
                    for x in ("eval", "exec", "compile", "getattr", "__import__")
                )
                for a in anns
            ):
                found.append("dynamic-annotation")
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)) and isinstance(node.value, ast.Call):
            found.append("top-level-runtime-instance")
    return list(dict.fromkeys(found))


def test_actual_production_entry_inventory_is_exact() -> None:
    assert package_entry_inventory() == tuple((name, "python") for name in EXPECTED_FILES)


def test_inventory_controls_use_same_function(tmp_path: Path) -> None:
    (tmp_path / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "__pycache__").mkdir()
    assert package_entry_inventory(tmp_path) == (("__init__.py", "python"),)
    (tmp_path / "unexpected.py").write_text("", encoding="utf-8")
    assert ("unexpected.py", "python") in package_entry_inventory(tmp_path)
    (tmp_path / "notes.txt").write_text("", encoding="utf-8")
    assert ("notes.txt", "file") in package_entry_inventory(tmp_path)
    (tmp_path / "nested").mkdir()
    assert ("nested", "directory") in package_entry_inventory(tmp_path)
    (tmp_path / "link").symlink_to(tmp_path / "__init__.py")
    assert ("link", "symlink") in package_entry_inventory(tmp_path)


def test_source_has_no_forbidden_boundary_or_side_effect() -> None:
    for path in PACKAGE.iterdir():
        if path.name != "__pycache__":
            assert not violations(
                path.read_text(encoding="utf-8"), package_init=path.name == "__init__.py"
            ), path


@pytest.mark.parametrize(
    "snippet",
    [
        "class SupportRepository: pass",
        "class SupportWorker: pass",
        "class AdminRuntime: pass",
        "class NotificationClient: pass",
        "import requests\nrequests.get('synthetic')",
        "import httpx\nclient.patch('synthetic')",
        "import socket\nsocket.connect('synthetic')",
        "worker.retry()",
        "session.execute()",
        "import os\nos.getenv('synthetic')",
        "import subprocess\nsubprocess.run([])",
        "import importlib\nimportlib.import_module('synthetic')",
        "eval('synthetic')",
        "exec('synthetic')",
        "compile('synthetic','','exec')",
        "setattr(x,'y',1)",
        "class Unsafe: password: str",
        "class Unsafe: one_time_code: str",
        "class Unsafe: raw_note_text: bytes",
        "class Unsafe: full_private_message: list",
        "class Unsafe: personal_data: dict",
        "class Unsafe: recipient_identity: object",
        "client = Client()",
        "service = Service()",
        "repository = Repository()",
        "worker = Worker()",
        "session = Session()",
        "connection = Connection()",
        "gateway = Gateway()",
        "handler = Handler()",
        "runtime = Runtime()",
    ],
)
def test_required_negative_controls_detected(snippet: str) -> None:
    assert violations(snippet), snippet


@pytest.mark.parametrize(
    "snippet",
    [
        "from __future__ import annotations",
        "from enum import Enum",
        "from typing import Literal",
        "from pydantic import BaseModel",
        "from mayak.contracts import ContractMetadata",
        "class SupportServiceLevel: pass",
        "mapping.get('synthetic')",
        "class Safe: secret: Literal[False] = False",
        "items = (('synthetic-a', 'synthetic-b'),)",
    ],
)
def test_required_safe_controls_accepted(snippet: str) -> None:
    assert violations(snippet) == []


def test_reload_side_effect_guards_verify_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    class Explodes:
        def __call__(self, *args: object, **kwargs: object) -> None:
            raise AssertionError("side effect")

    modules = (
        "mayak.modules.admin_and_support.contracts",
        "mayak.modules.admin_and_support.safe_reads",
        "mayak.modules.admin_and_support.role_actions",
        "mayak.modules.admin_and_support.tariff_actions",
        "mayak.modules.admin_and_support.access_actions",
        "mayak.modules.admin_and_support.anchor_actions",
        "mayak.modules.admin_and_support.beacon_actions",
        "mayak.modules.admin_and_support.case_records",
        "mayak.modules.admin_and_support.notification_actions",
        "mayak.modules.admin_and_support",
    )

    for module_name in modules:
        importlib.import_module(module_name)

    pydantic_loader = importlib.import_module("pydantic.plugin._loader")
    monkeypatch.setattr(pydantic_loader, "get_plugins", lambda: ())
    monkeypatch.setattr("os.getenv", Explodes())
    with pytest.raises(AssertionError, match="side effect"):
        os.getenv("synthetic")
    with pytest.raises(AssertionError, match="side effect"):
        os.getenv("PYDANTIC_DISABLE_PLUGINS")

    for module_name in modules:
        importlib.reload(importlib.import_module(module_name))

    before = set(sys.modules)
    importlib.reload(importlib.import_module("mayak.modules.admin_and_support"))
    assert set(sys.modules) >= before


def test_import_reload_has_no_external_roots() -> None:
    before = set(sys.modules)
    import mayak.modules.admin_and_support as package

    importlib.reload(package)
    added = {_root(name) for name in set(sys.modules) - before}
    assert not added & FORBIDDEN_ROOTS
