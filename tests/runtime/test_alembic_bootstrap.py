import subprocess
import sys
from pathlib import Path

import pytest
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
    assert set(metadata.tables) == {
        f"mayak.{name}"
        for name in (
            "platform_idempotency_records",
            "platform_audit_entries",
            "platform_event_outbox",
            "identity_accounts",
            "identity_provider_links",
            "identity_role_assignments",
            "identity_sessions",
            "identity_link_challenges",
            "entitlement_tariff_definitions",
            "entitlement_access_grants",
            "entitlement_usage_counters",
            "billing_payment_records",
            "billing_payment_operations",
            "billing_reconciliations",
        )
    }
    versions = sorted(path for path in (ROOT / "alembic" / "versions").iterdir() if path.is_file())
    assert [path.name for path in versions] == [
        "20260727_RF09_BOOTSTRAP_migration_boundary.py",
        "20260727_RF09_M01_platform_contracts.py",
        "20260727_RF09_M02_identity_and_access.py",
        "20260727_RF09_M03_entitlements_and_billing.py",
    ]
    scripts = ScriptDirectory.from_config(Config(str(ROOT / "alembic.ini")))
    revisions = list(scripts.walk_revisions())
    assert len(revisions) == 4
    assert scripts.get_heads() == ["RF09_M03"]
    assert sum(script.is_branch_point for script in revisions) == 0
    bootstrap = scripts.get_revision("RF09_BOOTSTRAP")
    m01 = scripts.get_revision("RF09_M01")
    assert (
        bootstrap
        and bootstrap.down_revision is None
        and not bootstrap.branch_labels
        and not bootstrap.dependencies
    )
    assert (
        m01
        and m01.down_revision == "RF09_BOOTSTRAP"
        and not m01.branch_labels
        and not m01.dependencies
    )
    m02 = scripts.get_revision("RF09_M02")
    assert (
        m02 and m02.down_revision == "RF09_M01" and not m02.branch_labels and not m02.dependencies
    )
    m03 = scripts.get_revision("RF09_M03")
    assert (
        m03 and m03.down_revision == "RF09_M02" and not m03.branch_labels and not m03.dependencies
    )


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


def test_rf09_m01_revision_contract_and_downgrade() -> None:
    import importlib.util

    path = ROOT / "alembic" / "versions" / "20260727_RF09_M01_platform_contracts.py"
    text = path.read_text(encoding="utf-8")
    assert "RF-09-06-M01-PLATFORM-CONTRACTS-SCHEMA-BATCH-20260727" in text
    assert "Domain owner: Module 01" in text
    assert "Domain tables created: 3" in text
    assert "Deferred FK count: 1" in text
    assert text.count("op.create_table") == 3
    assert text.count("op.create_index") == 7
    assert "ForeignKey" not in text and "identity_accounts" not in text
    assert "op.drop" not in text and "DROP" not in text.upper()
    spec = importlib.util.spec_from_file_location("rf09_m01", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.revision == "RF09_M01"
    assert module.down_revision == "RF09_BOOTSTRAP"
    try:
        module.downgrade()
    except RuntimeError as exc:
        assert str(exc) == "RF09_M01 is roll-forward only"
    else:
        raise AssertionError("downgrade unexpectedly succeeded")


def test_rf09_m02_revision_contract_and_downgrade() -> None:
    import importlib.util

    path = ROOT / "alembic" / "versions" / "20260727_RF09_M02_identity_and_access.py"
    text = path.read_text(encoding="utf-8")
    assert "RF-09-07-M02-IDENTITY-AND-ACCESS-SCHEMA-BATCH-20260727" in text
    assert "Implementation owner: Module 14 / RF-09" in text
    assert "Domain owner: Module 02" in text
    assert "Domain tables created: 5" in text
    assert "Deferred FK resolved: 1" in text
    assert text.count("op.create_table") == 5
    assert text.count("op.create_index") == 8
    assert text.count("op.create_foreign_key") == 1
    assert "op.drop" not in text and "DROP" not in text.upper()
    spec = importlib.util.spec_from_file_location("rf09_m02", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.revision == "RF09_M02" and module.down_revision == "RF09_M01"
    with pytest.raises(RuntimeError, match="RF09_M02 is roll-forward only"):
        module.downgrade()


def test_rf09_m03_revision_contract_and_downgrade() -> None:
    import importlib.util

    path = ROOT / "alembic" / "versions" / "20260727_RF09_M03_entitlements_and_billing.py"
    text = path.read_text(encoding="utf-8")
    assert "RF-09-08-M03-ENTITLEMENTS-AND-BILLING-SCHEMA-BATCH-20260727" in text
    assert "Implementation owner: Module 14 / RF-09" in text
    assert "Domain owner: Module 03" in text
    assert "Domain tables created: 6" in text
    assert "Deferred FK count: 0" in text
    assert text.count("op.create_table") == 6
    assert text.count("op.create_index") == 8
    assert text.count("op.create_foreign_key") == 0
    assert text.count("sa.ForeignKeyConstraint") == 7
    assert "op.drop" not in text and "DROP" not in text.upper()
    spec = importlib.util.spec_from_file_location("rf09_m03", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.revision == "RF09_M03" and module.down_revision == "RF09_M02"
    with pytest.raises(RuntimeError, match="RF09_M03 is roll-forward only"):
        module.downgrade()


def test_database_independent_alembic_commands() -> None:
    for command in (
        "heads",
        "history",
        "branches",
        "show RF09_BOOTSTRAP",
        "show RF09_M01",
        "show RF09_M02",
        "show RF09_M03",
    ):
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "-c", "alembic.ini", *command.split()],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        assert "mayak_database_migration_password" not in result.stdout + result.stderr


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
