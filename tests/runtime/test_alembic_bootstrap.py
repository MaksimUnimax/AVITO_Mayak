import subprocess
from pathlib import Path

from mayak.persistence.metadata import metadata

ROOT = Path(__file__).parents[2]
UV = "/opt/avito-mayak-runtime/toolchain/uv/0.11.31/uv"


def test_alembic_ini_is_safe_and_canonical() -> None:
    text = (ROOT / "alembic.ini").read_text(encoding="utf-8")
    assert "script_location = %(here)s/alembic" in text
    assert "version_locations = %(here)s/alembic/versions" in text
    assert "postgresql://" not in text and "password" not in text.lower()


def test_metadata_and_script_directory_are_empty() -> None:
    assert metadata.schema == "mayak"
    assert not metadata.tables
    assert list((ROOT / "alembic" / "versions").iterdir()) == [
        ROOT / "alembic" / "versions" / ".gitkeep"
    ]


def test_heads_and_history_need_no_database() -> None:
    for command in ("heads", "history"):
        result = subprocess.run(
            [UV, "run", "--offline", "alembic", "-c", "alembic.ini", command],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        assert "mayak_database_migration_password" not in result.stdout + result.stderr
