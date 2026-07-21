import ast
from pathlib import Path

ROOT = Path(__file__).parents[2]


def test_telegram_contract_source_has_no_provider_runtime_or_persistence_imports() -> None:
    tree = ast.parse((ROOT / "src/mayak/modules/telegram_adapter/contracts.py").read_text())
    imports = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
    names = {alias.name.split(".")[0] for node in imports for alias in node.names}
    assert not names & {
        "requests",
        "httpx",
        "aiohttp",
        "subprocess",
        "os",
        "sqlalchemy",
        "psycopg",
        "alembic",
    }
    source = (ROOT / "src/mayak/modules/telegram_adapter/contracts.py").read_text()
    assert "Telegram API" not in source
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
    called_names = {node.func.id for node in calls if isinstance(node.func, ast.Name)}
    assert not called_names & {"eval", "exec", "popen"}
