import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest
import sqlalchemy as sa
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
            "filter_catalog_versions",
            "filter_definitions",
            "filter_options",
            "filter_dependencies",
            "filter_category_applicability",
            "filter_evidence_references",
            "filter_capability_profiles",
            "beacon_beacons",
            "beacon_configuration_revisions",
            "beacon_filter_overrides",
            "beacon_lifecycle_events",
            "egress_agents",
            "egress_routes",
            "egress_agent_heartbeats",
            "egress_route_leases",
            "scan_schedules",
            "scan_work_items",
            "scan_runs",
            "scan_listing_observations",
            "scan_beacon_listing_state",
            "scan_anchors",
            "parser_outcomes",
            "notification_endpoints",
            "notification_events",
            "notification_outbox",
            "notification_delivery_attempts",
            "notification_delivery_reconciliations",
            "telegram_inbound_updates",
            "telegram_identity_mappings",
            "telegram_delivery_mappings",
            "max_inbound_events",
            "max_identity_mappings",
            "max_delivery_mappings",
            "max_miniapp_nonces",
            "support_cases",
            "support_case_notes",
            "support_case_events",
        )
    }
    versions = sorted(path for path in (ROOT / "alembic" / "versions").iterdir() if path.is_file())
    assert [path.name for path in versions] == [
        "20260727_RF09_BOOTSTRAP_migration_boundary.py",
        "20260727_RF09_M01_platform_contracts.py",
        "20260727_RF09_M02_identity_and_access.py",
        "20260727_RF09_M03_entitlements_and_billing.py",
        "20260727_RF09_M13_filter_catalog_and_builder.py",
        "20260728_RF09_M04_beacon_management.py",
        "20260728_RF09_M05_avito_parser.py",
        "20260728_RF09_M06_scan_orchestration.py",
        "20260728_RF09_M07_egress_routing.py",
        "20260728_RF09_M08_notification_delivery.py",
        "20260728_RF09_M09_telegram_adapter.py",
        "20260728_RF09_M10_max_adapter.py",
        "20260728_RF09_M11_admin_support.py",
    ]
    scripts = ScriptDirectory.from_config(Config(str(ROOT / "alembic.ini")))
    revisions = list(scripts.walk_revisions())
    assert len(revisions) == 13
    assert scripts.get_heads() == ["RF09_M11"]
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
    m13 = scripts.get_revision("RF09_M13")
    assert (
        m13 and m13.down_revision == "RF09_M03" and not m13.branch_labels and not m13.dependencies
    )
    m04 = scripts.get_revision("RF09_M04")
    assert (
        m04 and m04.down_revision == "RF09_M13" and not m04.branch_labels and not m04.dependencies
    )
    m07 = scripts.get_revision("RF09_M07")
    assert (
        m07 and m07.down_revision == "RF09_M04" and not m07.branch_labels and not m07.dependencies
    )
    m06 = scripts.get_revision("RF09_M06")
    assert (
        m06 and m06.down_revision == "RF09_M07" and not m06.branch_labels and not m06.dependencies
    )
    m05 = scripts.get_revision("RF09_M05")
    assert (
        m05 and m05.down_revision == "RF09_M06" and not m05.branch_labels and not m05.dependencies
    )
    m08 = scripts.get_revision("RF09_M08")
    assert (
        m08 and m08.down_revision == "RF09_M05" and not m08.branch_labels and not m08.dependencies
    )
    m09 = scripts.get_revision("RF09_M09")
    assert (
        m09 and m09.down_revision == "RF09_M08" and not m09.branch_labels and not m09.dependencies
    )
    m10 = scripts.get_revision("RF09_M10")
    assert (
        m10 and m10.down_revision == "RF09_M09" and not m10.branch_labels and not m10.dependencies
    )
    m11 = scripts.get_revision("RF09_M11")
    assert (
        m11 and m11.down_revision == "RF09_M10" and not m11.branch_labels and not m11.dependencies
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


def test_rf09_m13_revision_contract_and_downgrade() -> None:
    import importlib.util

    path = ROOT / "alembic" / "versions" / "20260727_RF09_M13_filter_catalog_and_builder.py"
    text = path.read_text(encoding="utf-8")
    assert "RF-09-09-M13-FILTER-CATALOG-SCHEMA-BATCH-20260727" in text
    assert "Implementation owner: Module 14 / RF-09" in text
    assert "Domain owner: Module 13" in text
    assert "Domain tables created: 7" in text
    assert "Deferred FK count: 0" in text
    assert text.count("op.create_table") == 7
    assert text.count("op.create_index") == 9
    assert text.count("op.create_foreign_key") == 0
    assert text.count("sa.ForeignKeyConstraint") == 11
    assert "op.drop" not in text and "DROP" not in text.upper()
    spec = importlib.util.spec_from_file_location("rf09_m13", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.revision == "RF09_M13" and module.down_revision == "RF09_M03"
    with pytest.raises(RuntimeError, match="RF09_M13 is roll-forward only"):
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
        "show RF09_M13",
        "show RF09_M04",
        "show RF09_M07",
        "show RF09_M05",
        "show RF09_M08",
        "show RF09_M09",
    ):
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "-c", "alembic.ini", *command.split()],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        assert "mayak_database_migration_password" not in result.stdout + result.stderr


def test_rf09_m04_revision_contract_and_downgrade() -> None:
    import importlib.util

    path = ROOT / "alembic" / "versions" / "20260728_RF09_M04_beacon_management.py"
    text = path.read_text(encoding="utf-8")
    assert "RF-09-10-M04-BEACON-MANAGEMENT-SCHEMA-BATCH-20260728" in text
    assert "Implementation owner: Module 14 / RF-09" in text
    assert "Domain owner: Module 04" in text
    assert "Domain tables created: 4" in text
    assert "Deferred FK count: 1" in text
    assert text.count("op.create_table") == 4
    assert text.count("op.create_index") == 4
    assert text.count("op.create_foreign_key") == 0
    assert text.count("sa.ForeignKeyConstraint") == 7
    assert "op.drop" not in text and "DROP" not in text.upper()
    spec = importlib.util.spec_from_file_location("rf09_m04", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.revision == "RF09_M04" and module.down_revision == "RF09_M13"
    with pytest.raises(RuntimeError, match="RF09_M04 is roll-forward only"):
        module.downgrade()


def test_rf09_m07_revision_contract_and_downgrade() -> None:
    import importlib.util

    path = ROOT / "alembic" / "versions" / "20260728_RF09_M07_egress_routing.py"
    text = path.read_text(encoding="utf-8")
    assert "RF-09-11-M07-EGRESS-ROUTING-SCHEMA-BATCH-20260728" in text
    assert "Implementation owner: Module 14/RF-09" in text
    assert "Domain owner: Module 07" in text
    assert "Domain tables created: 4" in text
    assert "Deferred FK count: 1" in text
    assert text.count("op.create_table") == 4
    assert text.count("op.create_index") == 5
    assert text.count("op.create_foreign_key") == 0
    assert text.count("sa.ForeignKeyConstraint") == 3
    assert "scan_work_items" not in text
    assert "op.drop" not in text and "DROP" not in text.upper()
    spec = importlib.util.spec_from_file_location("rf09_m07", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.revision == "RF09_M07" and module.down_revision == "RF09_M04"
    with pytest.raises(RuntimeError, match="RF09_M07 is roll-forward only"):
        module.downgrade()
    m05_path = ROOT / "alembic" / "versions" / "20260728_RF09_M05_avito_parser.py"
    m05_text = m05_path.read_text(encoding="utf-8")
    assert "RF-09-13-M05-AVITO-PARSER-SCHEMA-BATCH-20260728" in m05_text
    assert "Domain owner: Module 05" in m05_text
    assert "Implementation owner: Module 14/RF-09" in m05_text
    assert "reverse Scan FK remains deferred to RF09_FINALIZE" in m05_text
    assert m05_text.count("op.create_table") == 1
    assert m05_text.count("op.create_index") == 2
    assert m05_text.count("sa.ForeignKeyConstraint") == 3
    assert "op.execute" not in m05_text and "op.get_bind" not in m05_text
    assert "postgresql_nulls_not_distinct=True" in m05_text
    assert "scan_runs.parser_outcome_id" not in m05_text
    spec = importlib.util.spec_from_file_location("rf09_m05", m05_path)
    assert spec and spec.loader
    m05 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m05)
    assert m05.revision == "RF09_M05" and m05.down_revision == "RF09_M06"
    with pytest.raises(RuntimeError, match="RF09_M05 is roll-forward only"):
        m05.downgrade()


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
    path = ROOT / "alembic" / "versions" / "20260728_RF09_M08_notification_delivery.py"
    text = path.read_text(encoding="utf-8")
    assert "RF-09-14-M08-NOTIFICATION-DELIVERY-SCHEMA-BATCH-20260728" in text
    assert "Domain owner: Module 08 Notification Delivery" in text
    assert "Platform and Notification outboxes are distinct" in text
    assert "No new deferred foreign key" in text
    assert text.count("op.create_table") == 5
    assert text.count("op.create_index") == 7
    assert text.count("sa.ForeignKeyConstraint") == 8
    assert all(
        item not in text
        for item in ("op.execute", "op.bulk_insert", "op.get_bind", "op.create_foreign_key")
    )
    spec = importlib.util.spec_from_file_location("rf09_m08", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.revision == "RF09_M08" and module.down_revision == "RF09_M05"
    with pytest.raises(RuntimeError, match="RF09_M08 is roll-forward only"):
        module.downgrade()
    m09_path = ROOT / "alembic" / "versions" / "20260728_RF09_M09_telegram_adapter.py"
    m09_text = m09_path.read_text(encoding="utf-8")
    assert "RF-09-15-M09-TELEGRAM-ADAPTER-SCHEMA-BATCH-20260728" in m09_text
    assert "Domain owner: Module 09 Telegram Adapter" in m09_text
    assert "Implementation owner: Module 14/RF-09" in m09_text
    assert "Identity remains account/link authority" in m09_text
    assert "Notification remains generic delivery authority" in m09_text
    assert "Provider acceptance is not human read" in m09_text
    assert "No new deferred FK" in m09_text
    assert m09_text.count("op.create_table") == 3
    assert m09_text.count("op.create_index") == 4
    assert m09_text.count("sa.ForeignKeyConstraint") == 2
    assert all(
        item not in m09_text
        for item in ("op.execute", "op.bulk_insert", "op.get_bind", "op.create_foreign_key")
    )
    assert "telegram_message_ref IS NOT NULL" in m09_text
    spec = importlib.util.spec_from_file_location("rf09_m09", m09_path)
    assert spec and spec.loader
    m09 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m09)
    assert m09.revision == "RF09_M09" and m09.down_revision == "RF09_M08"
    with pytest.raises(RuntimeError, match="RF09_M09 is roll-forward only"):
        m09.downgrade()

    operations: list[tuple[str, tuple[object, ...], dict[str, object]]] = []

    class Spy:
        def create_table(self, *args: object, **kwargs: object) -> None:
            operations.append(("create_table", args, kwargs))

        def create_index(self, *args: object, **kwargs: object) -> None:
            operations.append(("create_index", args, kwargs))

    setattr(m09, "op", Spy())
    m09.upgrade()
    assert [item[0] for item in operations] == ["create_table"] * 3 + ["create_index"] * 4
    assert [str(item[1][0]) for item in operations[:3]] == [
        "telegram_inbound_updates",
        "telegram_identity_mappings",
        "telegram_delivery_mappings",
    ]
    assert [str(item[1][0]) for item in operations[3:]] == [
        "ix_telegram_inbound_updates_provider_update_id",
        "ix_telegram_inbound_updates_received_at",
        "ix_telegram_identity_mappings_provider_link_id",
        "ux_telegram_delivery_mappings_message_ref",
    ]
    assert (
        sum(
            len([item for item in args if isinstance(item, sa.ForeignKeyConstraint)])
            for _, args, _ in operations[:3]
        )
        == 2
    )

    # RF09_M10 contract and operation spy
    path = ROOT / "alembic" / "versions" / "20260728_RF09_M10_max_adapter.py"
    text = path.read_text(encoding="utf-8")
    assert "RF-09-16-M10-MAX-ADAPTER-SCHEMA-BATCH-20260728" in text
    assert "Domain owner: Module 10 MAX Adapter" in text
    assert "Implementation owner: Module 14/RF-09" in text
    assert "Production is webhook-first" in text and "polling is development/test-only" in text
    assert text.count("op.create_table") == 4 and text.count("op.create_index") == 5
    assert text.count("sa.ForeignKeyConstraint") == 3
    assert all(
        item not in text
        for item in (
            "op.execute",
            "op.bulk_insert",
            "op.get_bind",
            "op.create_foreign_key",
            "alembic.operations",
        )
    )
    spec = importlib.util.spec_from_file_location("rf09_m10", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.revision == "RF09_M10" and module.down_revision == "RF09_M09"
    with pytest.raises(RuntimeError, match="RF09_M10 is roll-forward only"):
        module.downgrade()
    operations_m10: list[tuple[str, tuple[object, ...], dict[str, object]]] = []

    class SpyM10:
        def create_table(self, *args: object, **kwargs: object) -> None:
            operations_m10.append(("create_table", args, kwargs))

        def create_index(self, *args: object, **kwargs: object) -> None:
            operations_m10.append(("create_index", args, kwargs))

    setattr(module, "op", SpyM10())
    module.upgrade()
    assert [item[0] for item in operations_m10] == ["create_table"] * 4 + ["create_index"] * 5
    assert [str(item[1][0]) for item in operations_m10[:4]] == [
        "max_inbound_events",
        "max_identity_mappings",
        "max_delivery_mappings",
        "max_miniapp_nonces",
    ]
    assert [str(item[1][0]) for item in operations_m10[4:]] == [
        "ix_max_inbound_events_provider_event_id",
        "ix_max_inbound_events_received_at",
        "ix_max_identity_mappings_provider_link_id",
        "ux_max_delivery_mappings_message_ref",
        "ix_max_miniapp_nonces_expires_at",
    ]
    assert (
        sum(
            len([item for item in args if isinstance(item, sa.ForeignKeyConstraint)])
            for _, args, _ in operations_m10[:4]
        )
        == 3
    )
    assert (
        sum(
            len([item for item in args if isinstance(item, sa.UniqueConstraint)])
            for _, args, _ in operations_m10[:4]
        )
        == 5
    )

    # RF09_M11 contract and operation spy
    path = ROOT / "alembic" / "versions" / "20260728_RF09_M11_admin_support.py"
    text = path.read_text(encoding="utf-8")
    assert "RF-09-17-M11-ADMIN-SUPPORT-SCHEMA-BATCH-20260728" in text
    assert "Domain owner: Module 11 Admin & Support" in text
    assert "Implementation owner: Module 14/RF-09" in text
    assert "Identity remains account/actor/authorization authority" in text
    assert "Foreign modules retain business-state authority" in text
    assert "internal notes are never customer-visible" in text
    assert "Foreign actions remain owning-module public commands" in text
    assert "No new deferred FK" in text
    assert text.count("op.create_table") == 3 and text.count("op.create_index") == 5
    assert text.count("sa.ForeignKeyConstraint") == 7
    assert all(
        item not in text
        for item in (
            "op.execute",
            "op.bulk_insert",
            "op.get_bind",
            "op.create_foreign_key",
            "alembic.operations",
            "getattr(op",
        )
    )
    spec = importlib.util.spec_from_file_location("rf09_m11", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.revision == "RF09_M11" and module.down_revision == "RF09_M10"
    with pytest.raises(RuntimeError, match="RF09_M11 is roll-forward only"):
        module.downgrade()
    operations_m11: list[tuple[str, tuple[object, ...], dict[str, object]]] = []

    class SpyM11:
        def create_table(self, *args: object, **kwargs: object) -> None:
            operations_m11.append(("create_table", args, kwargs))

        def create_index(self, *args: object, **kwargs: object) -> None:
            operations_m11.append(("create_index", args, kwargs))

    setattr(module, "op", SpyM11())
    module.upgrade()
    assert [item[0] for item in operations_m11] == ["create_table"] * 3 + ["create_index"] * 5
    assert [str(item[1][0]) for item in operations_m11] == [
        "support_cases",
        "support_case_notes",
        "support_case_events",
        "ix_support_cases_open_pending_updated_at",
        "ix_support_cases_account_updated_at",
        "ix_support_case_notes_case_created_at",
        "ix_support_case_events_case_created_at",
        "ix_support_case_events_actor_created_at",
    ]
    assert (
        sum(
            len([item for item in args if isinstance(item, sa.ForeignKeyConstraint)])
            for _, args, _ in operations_m11[:3]
        )
        == 7
    )
    assert (
        sum(
            len([item for item in args if isinstance(item, sa.UniqueConstraint)])
            for _, args, _ in operations_m11[:3]
        )
        == 0
    )
    assert (
        sum(
            kwargs.get("postgresql_where") is not None and not bool(kwargs.get("unique"))
            for _, _, kwargs in operations_m11[3:]
        )
        == 1
    )
