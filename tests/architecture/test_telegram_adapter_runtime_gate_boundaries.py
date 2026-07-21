import ast
from pathlib import Path

# ruff: noqa: E501


def test_telegram_adapter_contains_only_semantic_gate_contracts_for_tg15() -> None:
    source = "\n".join(
        Path(path).read_text() for path in Path("src/mayak/modules/telegram_adapter").glob("*.py")
    )
    tree = ast.parse(source)
    forbidden_modules = {
        "sqlalchemy",
        "psycopg",
        "alembic",
        "telegram.ext",
        "requests",
        "httpx",
        "fastapi",
        "uvicorn",
        "subprocess",
    }
    imports = {
        node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module
    } | {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    assert not any(
        module == forbidden or module.startswith(f"{forbidden}.")
        for module in imports
        for forbidden in forbidden_modules
    )
    forbidden_calls = {"get_updates", "set_webhook", "create_engine", "os.getenv", "subprocess.run"}
    calls = {ast.unparse(node.func) for node in ast.walk(tree) if isinstance(node, ast.Call)}
    assert not calls & forbidden_calls
    assert not list(Path("src/mayak/modules/telegram_adapter").glob("*.env"))
    assert not list(Path("src/mayak/modules/telegram_adapter").glob("*.sql"))
