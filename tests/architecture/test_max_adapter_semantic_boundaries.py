"""AST guards proving MAX production code remains a semantic boundary."""
import ast
from pathlib import Path

ROOT = Path(__file__).parents[2]
FILES = [ROOT / "src/mayak/modules/max_adapter/__init__.py",
         ROOT / "src/mayak/modules/max_adapter/contracts.py"]
FORBIDDEN = ("requests", "httpx", "aiohttp", "sqlalchemy", "alembic", "subprocess",
             "socket", "queue", "worker", "service", "runtime", "gateway", "endpoint")

def tree(path):
    return ast.parse(path.read_text(encoding="utf-8"))

def imports(t):
    for n in ast.walk(t):
        if isinstance(n, ast.Import):
            yield from (a.name for a in n.names)
        elif isinstance(n, ast.ImportFrom):
            yield n.module or ""

def test_production_file_set_is_exact():
    assert sorted(p.name for p in FILES[0].parent.iterdir()) == ["__init__.py", "contracts.py"]

def test_imports_are_limited_to_safe_dependencies():
    names = list(imports(tree(FILES[0]))) + list(imports(tree(FILES[1])))
    assert all(not any(x in n.lower() for x in FORBIDDEN) for n in names)
    assert all(n.startswith(("enum", "typing", "pydantic", "mayak.", "")) for n in names)

def test_no_forbidden_declarations():
    for path in FILES:
        for n in ast.walk(tree(path)):
            if isinstance(n, ast.ClassDef):
                assert not any(x in n.name.lower() for x in
                               ("handler", "client", "gateway", "repository", "service", "worker", "listener"))

def test_no_provider_or_runtime_calls():
    for path in FILES:
        for n in ast.walk(tree(path)):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute):
                assert n.func.attr not in {"get", "post", "put", "delete", "request", "send", "retry"}

def test_no_raw_sensitive_storage_fields():
    names = [n.target.id for p in FILES for n in ast.walk(tree(p))
             if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name)]
    forbidden = {"raw_provider_payload", "raw_web_app_data", "token", "private_key",
                 "phone", "contact_value", "message_content"}
    assert not any(name.lower() in forbidden for name in names)

def test_production_class_set_is_contract_only():
    classes = [n.name for n in tree(FILES[1]).body if isinstance(n, ast.ClassDef)]
    assert classes[0] == "_MaxContract" and len(classes) == 28

def test_negative_control_detects_unsafe_constructs():
    t = ast.parse("import requests\nclass Gateway: pass\nrequests.get('x')")
    assert "requests" in list(imports(t))
    assert "get" in [n.func.attr for n in ast.walk(t)
                     if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)]
    assert "Gateway" in [n.name for n in ast.walk(t) if isinstance(n, ast.ClassDef)]

def test_safe_semantic_snippet_passes_guard():
    t = ast.parse("from pydantic import BaseModel\nclass Safe(BaseModel): pass")
    assert list(imports(t)) == ["pydantic"]
    assert [n.name for n in ast.walk(t) if isinstance(n, ast.ClassDef)] == ["Safe"]

def test_production_does_not_import_pytest():
    assert all("pytest" not in n for p in FILES for n in imports(tree(p)))
