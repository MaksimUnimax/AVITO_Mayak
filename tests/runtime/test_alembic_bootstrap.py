import subprocess
import sys
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

from mayak.persistence.metadata import metadata

ROOT = Path(__file__).parents[2]


def test_alembic_ini_is_safe_and_canonical() -> None:
    text = (ROOT / "alembic.ini").read_text(encoding="utf-8")
    assert "script_location = %(here)s/alembic" in text
    assert "version_locations = %(here)s/alembic/versions" in text
    assert "postgresql://" not in text and "password" not in text.lower()


def test_metadata_schema_and_script_directory_have_one_boundary() -> None:
    assert metadata.schema == "mayak"
    assert not metadata.tables
    versions = sorted(path for path in (ROOT / "alembic" / "versions").iterdir() if path.is_file())
    assert [path.name for path in versions] == ["20260727_RF09_BOOTSTRAP_migration_boundary.py"]
    scripts = ScriptDirectory.from_config(Config(str(ROOT / "alembic.ini")))
    revisions = list(scripts.walk_revisions())
    assert len(revisions) == 1
    assert revisions[0].revision == "RF09_BOOTSTRAP"
    assert revisions[0].down_revision is None
    assert not revisions[0].branch_labels
    assert not revisions[0].dependencies
    assert revisions[0].is_branch_point is False


def test_bootstrap_revision_is_a_nonempty_privilege_boundary() -> None:
    revision_path = ROOT / "alembic" / "versions" / "20260727_RF09_BOOTSTRAP_migration_boundary.py"
    text = revision_path.read_text(encoding="utf-8")
    upper = text.upper()
    technical_id = (
        "TECHNICAL ID: RF-09-05-ALEMBIC-BOOTSTRAP-REVISION-AND-MIGRATION-SERIALIZATION-20260727"
    )
    assert technical_id in upper
    assert "IMPLEMENTATION OWNER: MODULE 14 / RF-09" in upper
    assert "DOMAIN TABLES CREATED: 0" in upper
    assert "ROLL-FORWARD-ONLY" in upper
    assert "op.create_table" not in text
    assert "CREATE TABLE" not in upper
    assert "DROP" not in upper
    assert "CREATE EXTENSION" not in upper
    for statement in (
        "current_user",
        "pg_roles",
        "pg_namespace",
        "REVOKE ALL ON SCHEMA mayak FROM PUBLIC",
        "GRANT USAGE, CREATE ON SCHEMA mayak TO mayak_migration",
        "GRANT USAGE ON SCHEMA mayak TO mayak_application",
        "REVOKE CREATE ON SCHEMA mayak FROM mayak_application",
        "ALTER DEFAULT PRIVILEGES FOR ROLE mayak_migration IN SCHEMA mayak",
        "REVOKE ALL ON TABLE mayak.alembic_version FROM PUBLIC",
        "REVOKE ALL ON TABLE mayak.alembic_version FROM mayak_application",
    ):
        assert statement.upper() in upper
    assert "GRANT" not in upper.split("ALEMBIC_VERSION", 1)[1]


def test_bootstrap_downgrade_fails_before_mutation() -> None:
    import importlib.util

    path = ROOT / "alembic" / "versions" / "20260727_RF09_BOOTSTRAP_migration_boundary.py"
    spec = importlib.util.spec_from_file_location("rf09_bootstrap", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    try:
        module.downgrade()
    except RuntimeError as exc:
        assert str(exc) == "RF09_BOOTSTRAP is roll-forward only"
    else:
        raise AssertionError("downgrade unexpectedly succeeded")


def test_heads_and_history_need_no_database() -> None:
    for command in ("heads", "history"):
        argv = [sys.executable, "-m", "alembic", "-c", "alembic.ini", command]
        assert argv[0] == sys.executable
        assert all(Path(argument).name != "uv" for argument in argv)
        assert all(not Path(argument).is_absolute() for argument in argv[1:])
        result = subprocess.run(
            argv,
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        assert "mayak_database_migration_password" not in result.stdout + result.stderr
