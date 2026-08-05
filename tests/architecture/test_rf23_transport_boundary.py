import ast
from pathlib import Path

ROOT = Path(__file__).parents[2]
TRANSPORT = ROOT / "src/mayak/entrypoints/api"
INTEGRATION = (
    ROOT / "src/mayak/runtime/rf21_composition.py",
    ROOT / "src/mayak/runtime/rf23_composition.py",
)
FORBIDDEN_MODULES = {
    "mayak.persistence.schema",
    "mayak.modules.identity_and_access.runtime",
    "mayak.modules.notification_delivery.runtime",
    "mayak.modules.scan_orchestration.read_models",
    "mayak.modules.telegram_adapter.runtime",
    "mayak.modules.max_adapter.runtime",
    "mayak.modules.beacon_management.runtime",
}


def _inventory(source: str) -> dict[str, int]:
    tree = ast.parse(source)
    modules: list[str] = []
    private = 0
    dml = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            modules.append(module)
            private += sum(alias.name.startswith("_") for alias in node.names)
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr in {"insert", "update", "delete", "execute", "scalar", "scalars"}:
                dml += 1
    return {
        "forbidden": sum(module in FORBIDDEN_MODULES for module in modules),
        "private": private,
        "read_model": sum(module.endswith(".read_models") for module in modules),
        "dml": dml,
    }


def _integration_inventory(source: str) -> dict[str, int]:
    tree = ast.parse(source)
    private_imports = private_refs = duck_typing = secret_reveals = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            private_imports += sum(alias.name.startswith("_") for alias in node.names)
        if isinstance(node, ast.Name) and node.id == "_RawSecret":
            private_refs += 1
        if isinstance(node, ast.Attribute) and node.attr == "_value_as_secret":
            private_refs += 1
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "hasattr"
        ):
            if any(
                isinstance(arg, ast.Constant) and arg.value == "_value_as_secret"
                for arg in node.args
            ):
                duck_typing += 1
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "reveal"
        ):
            secret_reveals += 1
    return {
        "private_imports": private_imports,
        "private_refs": private_refs,
        "duck_typing": duck_typing,
        "secret_reveals": secret_reveals,
    }


def test_rf23_transport_ast_inventory_is_clean() -> None:
    inventory = {key: 0 for key in ("forbidden", "private", "read_model", "dml")}
    for path in TRANSPORT.rglob("*.py"):
        current = _inventory(path.read_text(encoding="utf-8"))
        for key in inventory:
            inventory[key] += current[key]
    assert inventory == {"forbidden": 0, "private": 0, "read_model": 0, "dml": 0}


def test_rf23_transport_gate_rejects_adversarial_forbidden_import() -> None:
    assert _inventory("from mayak.modules.identity_and_access.runtime import _RawSecret") == {
        "forbidden": 1,
        "private": 1,
        "read_model": 0,
        "dml": 0,
    }
    assert (
        _inventory("from mayak.modules.scan_orchestration.read_models import recent_runs")[
            "read_model"
        ]
        == 1
    )
    assert _inventory("session.execute(text('select 1'))")["dml"] == 1


def test_rf23_integration_boundary_is_clean() -> None:
    inventory = {
        key: 0 for key in ("private_imports", "private_refs", "duck_typing", "secret_reveals")
    }
    for path in INTEGRATION:
        current = _integration_inventory(path.read_text(encoding="utf-8"))
        for key in inventory:
            inventory[key] += current[key]
    assert inventory == {key: 0 for key in inventory}


def test_rf23_integration_gate_rejects_each_private_pattern() -> None:
    assert _integration_inventory("from x import _RawSecret")["private_imports"] == 1
    assert _integration_inventory("x._value_as_secret()")["private_refs"] == 1
    assert _integration_inventory('hasattr(x, "_value_as_secret")')["duck_typing"] == 1
    assert _integration_inventory("issued.token.reveal()")["secret_reveals"] == 1
