"""AST guards proving MAX production code remains a semantic boundary."""
import ast
from pathlib import Path

ROOT = Path(__file__).parents[2]
FILES = [ROOT / "src/mayak/modules/max_adapter/__init__.py",
         ROOT / "src/mayak/modules/max_adapter/contracts.py"]
CONTRACT_IMPORTS = {"__future__", "enum", "typing", "pydantic", "mayak.contracts"}
PACKAGE_INIT_IMPORTS = {"mayak.platform.boundaries", "mayak.modules.max_adapter.contracts"}
FORBIDDEN_CLASS_PARTS = ("handler", "client", "gateway", "repository", "service",
                         "worker", "listener")
FORBIDDEN_CLASS_NAMES = {"provider", "client", "runtime"}
FORBIDDEN_CALLS = {"get", "post", "put", "delete", "request", "send", "retry"}
SENSITIVE_FIELDS = {"raw_provider_payload", "raw_web_app_data", "token", "private_key",
                    "phone", "contact_value", "message_content"}
PRODUCTION_CLASS_SET = {"_MaxContract", "MaxEligibilityState", "MaxUpdateIntakeState",
                        "MaxUpdateAdmissionState", "MaxUpdateSourceKind",
                        "MaxUpdateStructuralClass", "MaxUpdateDeduplicationState",
                        "MaxCommandSourceKind", "MaxCommandSurfaceKind",
                        "MaxCommandNormalizationState", "MaxContactValidationState",
                        "MaxMiniAppValidationState", "MaxOutboundRequestState",
                        "MaxProviderOutcomeState", "MaxRetryRecommendation",
                        "MaxReconciliationState", "MaxProviderIdentity",
                        "MaxAccountLinkReference", "MaxEligibilityEvidenceReference",
                        "MaxUpdateIntakeRecord", "MaxUpdateDeduplicationRecord",
                        "MaxCommandEnvelope", "MaxContactValidationResult",
                        "MaxMiniAppValidationResult", "MaxOutboundRequest",
                        "MaxProviderOutcome", "MaxReconciliationRecord", "MaxAdapterReadModel"}


def _module_name(node):
    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names]
    if node.module is None:
        return ["." * node.level]
    return ["." * node.level + node.module]


def violations(source: str, *, package_init: bool = False,
               production_file: Path | None = None) -> list[str]:
    """Return deterministic violations for production code and synthetic controls."""
    tree = ast.parse(source)
    allowed = PACKAGE_INIT_IMPORTS if package_init else CONTRACT_IMPORTS
    result = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for module in _module_name(node):
                normalized = ("mayak.modules.max_adapter.contracts"
                              if package_init and module == ".contracts" else module)
                if normalized not in allowed:
                    result.append(f"forbidden-import:{module}")
        if isinstance(node, ast.ClassDef):
            lowered = node.name.lower()
            if lowered in FORBIDDEN_CLASS_NAMES or any(
                part in lowered for part in FORBIDDEN_CLASS_PARTS
            ):
                result.append(f"forbidden-class:{node.name}")
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                if node.func.attr in FORBIDDEN_CALLS:
                    result.append(f"forbidden-call:{node.func.attr}")
                if node.func.attr == "setattr":
                    result.append("setattr-mutation")
            elif isinstance(node.func, ast.Name) and node.func.id == "setattr":
                result.append("setattr-mutation")
        if isinstance(node, (ast.AnnAssign, ast.Assign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            names = [target.id for target in targets if isinstance(target, ast.Name)]
            if any(name.lower() in SENSITIVE_FIELDS for name in names):
                result.extend(f"sensitive-field:{name}" for name in names
                              if name.lower() in SENSITIVE_FIELDS)

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            annotations = [arg.annotation for arg in node.args.args if arg.annotation]
            annotations += [node.returns] if node.returns else []
        elif isinstance(node, (ast.AnnAssign, ast.arg)):
            annotations = [node.annotation] if node.annotation else []
        else:
            continue
        for annotation in annotations:
            rendered = ast.unparse(annotation)
            if any(token in rendered for token in
                   ("__import__", "eval", "exec", "compile", "globals", "locals", "getattr")):
                result.append("dynamic-annotation-evasion")

    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)) and isinstance(node.value, ast.Call):
            callee = node.value.func.id if isinstance(node.value.func, ast.Name) else ""
            if any(part in callee.lower() for part in FORBIDDEN_CLASS_PARTS):
                result.append("top-level-runtime-instance")

    if production_file is not None:
        direct_entries = sorted(path.name for path in production_file.parent.iterdir()
                                if path.name != "__pycache__")
        if direct_entries != ["__init__.py", "contracts.py"]:
            result.append("production-file-set")
        if not package_init:
            classes = {node.name for node in tree.body if isinstance(node, ast.ClassDef)}
            if classes != PRODUCTION_CLASS_SET or len(classes) != 28:
                result.append("production-class-set")
    return list(dict.fromkeys(result))


def test_production_file_set_is_exact():
    assert violations(
        FILES[0].read_text(encoding="utf-8"), package_init=True, production_file=FILES[0]
    ) == []
    assert violations(FILES[1].read_text(encoding="utf-8"), production_file=FILES[1]) == []


def test_production_file_set_ignores_only_pycache(tmp_path):
    package = tmp_path / "max_adapter"
    package.mkdir()
    (package / "__init__.py").write_text("", encoding="utf-8")
    contracts = package / "contracts.py"
    contracts.write_text("from __future__ import annotations\n", encoding="utf-8")
    (package / "__pycache__").mkdir()

    assert "production-file-set" not in violations(
        contracts.read_text(encoding="utf-8"), production_file=contracts
    )

    (package / "runtime").mkdir()
    assert "production-file-set" in violations(
        contracts.read_text(encoding="utf-8"), production_file=contracts
    )


def test_imports_are_limited_to_safe_dependencies():
    assert violations(FILES[0].read_text(encoding="utf-8"), package_init=True) == []
    assert violations(FILES[1].read_text(encoding="utf-8")) == []


def test_no_forbidden_declarations():
    assert all(node.name.lower() not in FORBIDDEN_CLASS_NAMES and
               not any(part in node.name.lower() for part in FORBIDDEN_CLASS_PARTS)
               for path in FILES for node in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
               if isinstance(node, ast.ClassDef))


def test_no_provider_or_runtime_calls():
    assert all(not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr in FORBIDDEN_CALLS)
               for path in FILES for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))))


def test_no_raw_sensitive_storage_fields():
    assert all(not (isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
                    and node.target.id.lower() in SENSITIVE_FIELDS)
               for path in FILES for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))))


def test_production_class_set_is_contract_only():
    tree = ast.parse(FILES[1].read_text(encoding="utf-8"))
    classes = {node.name for node in tree.body if isinstance(node, ast.ClassDef)}
    assert classes == PRODUCTION_CLASS_SET and len(classes) == 28


UNSAFE_SNIPPETS = [
    ("unknown standard-library import", "import json", False),
    ("unknown third-party import", "import requests", False),
    ("foreign mayak module import", "from mayak.unknown import X", False),
    ("forbidden relative import", "from .runtime import Client", True),
    ("runtime/provider class", "class Provider: pass", False),
    ("provider/network call", "import requests\nrequests.get('x')", False),
    ("sensitive field", "class Data:\n    token: str", False),
    ("dynamic annotation evasion", "class Data:\n    value: __import__('os')", False),
    ("top-level runtime instance", "client = Client()", False),
    ("mutation through setattr", "setattr(target, 'value', 1)", False),
]


def test_negative_controls_use_reusable_guard():
    for label, source, package_init in UNSAFE_SNIPPETS:
        assert violations(source, package_init=package_init), label


def test_safe_controls_use_reusable_guard():
    safe = ["from __future__ import annotations", "from enum import Enum",
            "from typing import Literal", "from pydantic import BaseModel, Field",
            "from mayak.contracts import ContractMetadata",
            "from mayak.platform.boundaries import MAX_ADAPTER_MODULE_ID",
            "from .contracts import MaxProviderIdentity"]
    for source in safe[:5]:
        assert violations(source) == []
    assert violations(safe[5], package_init=True) == []
    assert violations(safe[6], package_init=True) == []


def test_production_does_not_import_pytest():
    assert all("pytest" not in node for path in FILES
               for import_node in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
               if isinstance(import_node, (ast.Import, ast.ImportFrom))
               for node in _module_name(import_node))
