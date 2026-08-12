"""RF27 least-privilege migration and readiness contract checks."""

from __future__ import annotations

import os
import subprocess
from collections.abc import Generator
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic.config import Config
from alembic.script import ScriptDirectory

ROOT = Path(__file__).parents[2]
NEW_HEAD = "RF27_PERSISTENCE_READINESS"
PREDECESSOR = "RF20_ADMIN_SUPPORT_RUNTIME"
APPLICATION = "mayak_application"
MIGRATION = "mayak_migration"
VERSION_TABLE = "mayak.alembic_version"


def test_rf27_revision_is_one_additive_linear_head() -> None:
    scripts = ScriptDirectory.from_config(Config(str(ROOT / "alembic.ini")))
    assert scripts.get_heads() == [NEW_HEAD]
    revision = scripts.get_revision(NEW_HEAD)
    assert revision is not None
    assert revision.down_revision == PREDECESSOR
    assert not revision.branch_labels
    assert not revision.dependencies

    path = ROOT / "alembic" / "versions" / "20260811_RF27_persistence_readiness.py"
    text = path.read_text(encoding="utf-8")
    upper = text.upper()
    assert "GRANT SELECT ON TABLE MAYAK.ALEMBIC_VERSION TO MAYAK_APPLICATION" in upper
    assert "REVOKE SELECT ON TABLE MAYAK.ALEMBIC_VERSION FROM MAYAK_APPLICATION" in upper
    for forbidden in (
        "INSERT",
        "UPDATE",
        "DELETE",
        "TRUNCATE",
        "REFERENCES",
        "TRIGGER",
        "CREATE",
        "ALTER",
        "DROP",
        "OWNER",
        "ALL",
    ):
        assert forbidden not in upper.split("DEF UPGRADE", 1)[1].split("DEF DOWNGRADE", 1)[0]


def test_historical_migrations_are_unchanged() -> None:
    base = "f7835d441c058886bf932bb239aa1aeaeb7ecb9b"
    historical = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", base, "alembic/versions"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    for path in historical:
        current = (ROOT / path).read_bytes()
        original = subprocess.run(
            ["git", "show", f"{base}:{path}"],
            check=True,
            capture_output=True,
        ).stdout
        assert current == original, path


def _database_urls() -> tuple[str, str] | None:
    application = os.environ.get("RF27_APPLICATION_DSN")
    migration = os.environ.get("RF27_MIGRATION_DSN")
    if not application or not migration:
        return None
    return application, migration


@pytest.fixture(scope="module")
def database_engines() -> Generator[tuple[sa.Engine, sa.Engine], None, None]:
    urls = _database_urls()
    if urls is None:
        pytest.skip("RF27_APPLICATION_DSN and RF27_MIGRATION_DSN are required")
    application = sa.create_engine(urls[0], pool_pre_ping=True)
    migration = sa.create_engine(urls[1], pool_pre_ping=True)
    try:
        yield application, migration
    finally:
        application.dispose()
        migration.dispose()


def test_application_role_has_select_only_and_migration_role_stays_authoritative(
    database_engines: tuple[sa.Engine, sa.Engine],
) -> None:
    application, migration = database_engines
    with application.connect() as connection:
        assert (
            connection.execute(sa.text(f"SELECT version_num FROM {VERSION_TABLE}")).scalar_one()
            == NEW_HEAD
        )
        privileges = connection.execute(
            sa.text(
                "SELECT privilege_type FROM information_schema.role_table_grants "
                "WHERE grantee=:role AND table_schema='mayak' "
                "AND table_name='alembic_version' ORDER BY privilege_type"
            ),
            {"role": APPLICATION},
        ).scalars().all()
        assert privileges == ["SELECT"]
        owner = connection.execute(
            sa.text(
                "SELECT pg_get_userbyid(c.relowner) FROM pg_class c "
                "JOIN pg_namespace n ON n.oid=c.relnamespace "
                "WHERE n.nspname='mayak' AND c.relname='alembic_version'"
            )
        ).scalar_one()
        assert owner == MIGRATION
        membership = connection.execute(
            sa.text(
                "SELECT 1 FROM pg_auth_members m JOIN pg_roles member "
                "ON member.oid=m.member WHERE member.rolname=:role"
            ),
            {"role": APPLICATION},
        ).first()
        assert membership is None

    for statement in (
        "INSERT INTO mayak.alembic_version(version_num) VALUES ('RF27_PERSISTENCE_READINESS')",
        "UPDATE mayak.alembic_version SET version_num='RF20_ADMIN_SUPPORT_RUNTIME'",
        "DELETE FROM mayak.alembic_version",
        "ALTER TABLE mayak.alembic_version ADD COLUMN rf27_forbidden integer",
        "DROP TABLE mayak.alembic_version",
    ):
        with application.begin() as connection:
            with pytest.raises(sa.exc.DBAPIError):
                connection.execute(sa.text(statement))

    with migration.connect() as connection:
        assert (
            connection.execute(sa.text(f"SELECT version_num FROM {VERSION_TABLE}")).scalar_one()
            == NEW_HEAD
        )


def test_downgrade_and_reupgrade_contract(database_engines: tuple[sa.Engine, sa.Engine]) -> None:
    _application, migration = database_engines
    pytest.skip("destructive downgrade/re-upgrade is run by the isolated RF27 acceptance harness")


def test_rf12_runtime_matrix_exercises_owned_postgres_behavior_when_task_db_is_present() -> None:
    """Run the accepted RF-12 command matrix through the real runtime boundary.

    The CI substrate deliberately supplies this DSN only for the full regression;
    local runs remain hermetic and skip rather than inventing a database.
    """
    dsn = os.environ.get("MAYAK_RF10_POSTGRES_DSN")
    if not dsn:
        pytest.skip("task-owned RF10 PostgreSQL DSN is required")
    from scripts.runtime import run_rf12_postgres_acceptance as rf12

    engine = sa.create_engine(dsn, pool_pre_ping=True)
    account_ids: list[str] = []
    try:
        with sa.orm.Session(engine) as session:
            matrix = rf12._call_matrix(session)
            account_ids.append(matrix["account_id"])
            assert len(matrix["rows"]) == 12
            assert {row["command_id"] for row in matrix["rows"][:-1]} == set(rf12.COMMAND_IDS)
            assert matrix["rows"][-1]["replay"]["state"] == "REPLAYED"
            assert matrix["rows"][-1]["mismatch"]["state"] == "MISMATCH"
        assert rf12._parity(engine)["observed"] is True
        assert rf12._constraints(engine)["result"] is True
    finally:
        if account_ids:
            rf12._cleanup(engine, account_ids)
        engine.dispose()


def test_rf12_runtime_concurrency_rollback_and_policy_families_are_observable() -> None:
    """Exercise each accepted RF-12 scenario family against the task database."""
    dsn = os.environ.get("MAYAK_RF10_POSTGRES_DSN")
    if not dsn:
        pytest.skip("task-owned RF10 PostgreSQL DSN is required")
    from scripts.runtime import run_rf12_postgres_acceptance as rf12

    engine = sa.create_engine(dsn, pool_pre_ping=True)
    accounts: list[str] = []
    try:
        scenarios = (
            rf12._real_concurrency(engine),
            rf12._real_tariff_concurrency(engine),
            rf12._real_tariff_concurrency(engine, mismatch=True),
            rf12._real_rollback(engine),
            rf12._real_payment_rollback(engine),
            rf12._real_payment_race(engine),
        )
        for scenario in scenarios:
            value = scenario.get("account_id")
            if value:
                accounts.append(str(value))
            accounts.extend(str(item) for item in scenario.get("account_ids", ()))
            assert scenario
        manual, manual_account = rf12._manual_entitlement_semantics(engine)
        payment, payment_account = rf12._payment_non_authority(engine)
        usage, usage_account = rf12._usage_policy_semantics(engine)
        accounts.extend((manual_account, payment_account, usage_account))
        assert manual["cases"]["active_exact_match"]["allowed"] is True
        assert payment["entitlement_effective"] is False
        assert rf12._usage_policy_gate(usage) is True
    finally:
        if accounts:
            rf12._cleanup(engine, accounts)
        engine.dispose()
