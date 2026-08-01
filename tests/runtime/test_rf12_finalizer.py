from __future__ import annotations

import importlib.util
import json
from pathlib import Path

# ruff: noqa: E501

_SPEC = importlib.util.spec_from_file_location("rf12_finalizer", Path("scripts/runtime/finalize_rf12_acceptance_evidence.py"))
assert _SPEC is not None and _SPEC.loader is not None
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
finalize = _MODULE.finalize


def test_finalizer_uses_raw_post_cleanup_snapshot(tmp_path) -> None:
    runtime = tmp_path / "runtime.json"
    before = tmp_path / "before.json"
    after = tmp_path / "after.json"
    absence = tmp_path / "absence.json"
    output = tmp_path / "output.json"
    runtime.write_text(json.dumps({"gates": {"docker_task_resource_cleanup": False, "post_cleanup_foreign_resource_equality": False}}))
    before.write_text(json.dumps({"containers": [{"Name": "foreign"}], "networks": [], "volumes": []}))
    after.write_text(before.read_text())
    absence.write_text(json.dumps({"task_resources_absent": True, "remaining_task_resources": 0}))
    finalize(runtime, before, after, absence, output)
    evidence = json.loads(output.read_text())
    assert evidence["foreign_after_raw"] == evidence["foreign_before_raw"]
    assert evidence["post_cleanup_foreign_resource_equality"]["raw_after_observed"] is True
    assert evidence["gates"]["post_cleanup_foreign_resource_equality"] is True
