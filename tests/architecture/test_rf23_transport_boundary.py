import ast
from pathlib import Path

ROOT = Path(__file__).parents[2]
TRANSPORT = ROOT / "src/mayak/entrypoints/api"
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
