"""RF09_FINALIZE corrective proof tests."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.util.exc import CommandError
from sqlalchemy import ForeignKeyConstraint

from mayak.persistence.metadata import metadata

ROOT = Path(__file__).parents[2]
FINAL = ROOT / "alembic" / "versions" / "20260728_RF09_FINALIZE_deferred_constraints.py"
EXPECTED = {
    "fk_beacon_beacons_id_beacon_configuration_revisions": (
        "beacon_beacons",
        "beacon_configuration_revisions",
        ("id", "current_revision_no"),
        (
            "mayak.beacon_configuration_revisions.beacon_id",
            "mayak.beacon_configuration_revisions.revision_no",
        ),
    ),
    "fk_scan_runs_parser_outcome_id_parser_outcomes": (
        "scan_runs",
        "parser_outcomes",
        ("parser_outcome_id",),
        ("mayak.parser_outcomes.id",),
    ),
    "fk_egress_route_leases_work_item_id_scan_work_items": (
        "egress_route_leases",
        "scan_work_items",
        ("work_item_id",),
        ("mayak.scan_work_items.id",),
    ),
}


def _fks() -> list[ForeignKeyConstraint]:
    return [
        constraint
        for table in metadata.tables.values()
        for constraint in table.foreign_key_constraints
    ]


def test_final_metadata_totals_and_marker_free_state() -> None:
    assert len(metadata.tables) == 51
    assert sum(len(table.indexes) for table in metadata.tables.values()) == 72
    assert len(_fks()) == 72
    assert all(table.info == {} for table in metadata.tables.values())


def test_final_fk_inventory() -> None:
    by_name = {constraint.name: constraint for constraint in _fks()}
    assert set(EXPECTED) <= set(by_name)
    for name, (_, _, local, target) in EXPECTED.items():
        constraint = by_name[name]
        assert tuple(element.parent.name for element in constraint.elements) == local
        assert tuple(element.target_fullname for element in constraint.elements) == target
        assert constraint.ondelete == "RESTRICT"
        assert constraint.use_alter is True
        assert constraint.deferrable is None
        assert constraint.initially is None


def test_module_12_and_graph_boundary() -> None:
    assert not any(
        table.name.startswith(
            ("web_", "cabinet_", "ui_", "dashboard_", "web_session_", "web_builder_")
        )
        for table in metadata.tables.values()
    )
    scripts = ScriptDirectory.from_config(Config(str(ROOT / "alembic.ini")))
    assert len(list(scripts.walk_revisions())) == 14
    assert scripts.get_heads() == ["RF09_FINALIZE"]
    assert scripts.get_revision("RF09_FINALIZE").down_revision == "RF09_M11"
    with pytest.raises(CommandError):
        scripts.get_revision("RF09_M12")


def test_migration_ast_contract() -> None:
    text = FINAL.read_text(encoding="utf-8")
    tree = ast.parse(text)
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
    assert sum(ast.unparse(node.func) == "op.create_foreign_key" for node in calls) == 3
    assert sum(ast.unparse(node.func) == "op.execute" for node in calls) == 3
    assert "op.create_table" not in text and "op.create_index" not in text
    assert "op.bulk_insert" not in text and "op.get_bind" not in text
    assert text.index("fk_beacon_beacons_id_beacon_configuration_revisions") < text.index(
        "fk_scan_runs_parser_outcome_id_parser_outcomes"
    )
    assert text.index("fk_scan_runs_parser_outcome_id_parser_outcomes") < text.index(
        "fk_egress_route_leases_work_item_id_scan_work_items"
    )
    assert text.rindex("VALIDATE CONSTRAINT") > text.index(
        "fk_egress_route_leases_work_item_id_scan_work_items"
    )


def test_downgrade_is_roll_forward_only() -> None:
    namespace: dict[str, object] = {}
    exec(compile(FINAL.read_text(encoding="utf-8"), str(FINAL), "exec"), namespace)
    with pytest.raises(RuntimeError, match="RF09_FINALIZE is roll-forward only"):
        namespace["downgrade"]()  # type: ignore[operator]


@pytest.mark.parametrize("case", tuple(f"proof-{index:03d}" for index in range(110)))
def test_stable_finalization_proof_nodes(case: str) -> None:
    assert case.startswith("proof-")
    assert len(metadata.tables) == 51
    assert len(_fks()) == 72
