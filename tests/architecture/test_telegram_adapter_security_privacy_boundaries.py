import ast
from pathlib import Path

ROOT = Path(__file__).parents[2]
ALLOWED = {
    "src/mayak/modules/telegram_adapter/contracts.py",
    "src/mayak/modules/telegram_adapter/__init__.py",
    "tests/unit/test_telegram_adapter_security_privacy_contracts.py",
    "tests/contract/test_telegram_adapter_security_privacy_exports.py",
    "tests/architecture/test_telegram_adapter_security_privacy_boundaries.py",
}


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


def test_task_diff_scope_is_exactly_five_paths() -> None:
    import subprocess

    changed = set(
        subprocess.check_output(["git", "diff", "--name-only"], cwd=ROOT, text=True).splitlines()
    )
    assert changed <= ALLOWED
