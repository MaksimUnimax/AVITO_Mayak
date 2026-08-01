from __future__ import annotations

from pathlib import Path

import pytest

from mayak.runtime.task_acceptance import TaskAcceptanceVerifierKind, verifier_kind_from_id
from scripts.runtime.rf08_verify_structural_gateway import SCHEMA_VERSION, verify_source

ROOT = Path(__file__).resolve().parents[2]


def test_unknown_verifier_and_dynamic_registry_fail_closed() -> None:
    with pytest.raises(ValueError):
        verifier_kind_from_id("caller.module")
    assert TaskAcceptanceVerifierKind.RF30_SELF_PROOF.value == "RF30_SELF_PROOF"


def test_registry_contains_no_dynamic_execution_primitives() -> None:
    source = (ROOT / "src/mayak/runtime/task_acceptance/__init__.py").read_text(encoding="utf-8")
    assert "importlib" not in source
    assert "eval(" not in source and "exec(" not in source
    assert "subprocess" not in source and "entry_points" not in source


def test_production_surface_has_exactly_one_transport() -> None:
    payload = verify_source(ROOT)
    assert payload["schema_version"] == SCHEMA_VERSION
    assert payload["finding_count"] == 0
    assert payload["docker_transport_count"] == 1
    assert payload["task_host_executable_route_count"] == 0
    assert payload["task_bind_mount_executable_route_count"] == 0
    assert payload["fixed_in_image_runner_route"] == 1


def test_structural_mutation_rejects_host_mount_and_dynamic_module(tmp_path: Path) -> None:
    authority = (ROOT / "scripts/runtime/rf08_docker_authority.py").read_text(encoding="utf-8")
    registry = ROOT / "src/mayak/runtime/task_acceptance"
    (tmp_path / "scripts/runtime").mkdir(parents=True)
    (tmp_path / "src/mayak/runtime/task_acceptance").mkdir(parents=True)
    (tmp_path / "scripts/runtime/rf08_docker_authority.py").write_text(
        authority.replace('"mayak.runtime.task_acceptance"', "caller.module"), encoding="utf-8"
    )
    (tmp_path / "src/mayak/runtime/task_acceptance/__init__.py").write_text(
        (registry / "__init__.py").read_text(encoding="utf-8"), encoding="utf-8"
    )
    assert verify_source(tmp_path)["finding_count"] > 0
