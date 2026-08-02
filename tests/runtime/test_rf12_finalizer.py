# ruff: noqa
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
    original = {"schema_version": "rf12-postgres-acceptance-v2", "technical_id": "RF12-test-execution-id", "candidate_source_sha": "a" * 40, "candidate_tree_identity": "tree", "evidence_phase": "RUNTIME_COMPLETE_PENDING_HOST_FINALIZATION", "gates": {**{name: True for name in _MODULE.RUNTIME_PRODUCER_GATES}, "docker_task_resource_cleanup": False, "post_cleanup_foreign_resource_equality": False}}
    runtime.write_text(json.dumps(original))
    before.write_text(json.dumps({"containers": [{"Name": "foreign"}], "networks": [], "volumes": []}))
    after.write_text(before.read_text())
    absence.write_text(json.dumps({"task_resources_absent": True, "container_absent": True, "network_absent": True, "volume_absent": True, "image_tag_absent": True, "image_id_not_retained": True, "remaining_task_resources": 0, "container_remaining_count": 0, "network_remaining_count": 0, "volume_remaining_count": 0, "image_tag_remaining_count": 0, "image_id_remaining_count": 0}))
    finalize(runtime, before, after, absence, output)
    evidence = json.loads(output.read_text())
    assert evidence["foreign_after_raw"] == evidence["foreign_before_raw"]
    assert evidence["post_cleanup_foreign_resource_equality"]["raw_after_observed"] is True
    assert evidence["gates"]["post_cleanup_foreign_resource_equality"] is True
    assert evidence["evidence_phase"] == "FINALIZED"
    for key in ("schema_version", "technical_id", "candidate_source_sha", "candidate_tree_identity"):
        assert evidence[key] == original[key]


def test_finalizer_rejects_failed_or_finalized_producer(tmp_path) -> None:
    import pytest
    runtime = tmp_path / "runtime.json"
    before = tmp_path / "before.json"; after = tmp_path / "after.json"; absence = tmp_path / "absence.json"; output = tmp_path / "output.json"
    gates = {**{name: True for name in _MODULE.RUNTIME_PRODUCER_GATES}, "docker_task_resource_cleanup": False, "post_cleanup_foreign_resource_equality": False}
    runtime.write_text(json.dumps({"evidence_phase": "RUNTIME_COMPLETE_PENDING_HOST_FINALIZATION", "gates": {**gates, "metadata_parity": False}}))
    before.write_text("{}"); after.write_text("{}"); absence.write_text("{}")
    with pytest.raises(SystemExit): _MODULE.finalize(runtime, before, after, absence, output)
    runtime.write_text(json.dumps({"evidence_phase": "FINALIZED", "gates": gates}))
    with pytest.raises(SystemExit): _MODULE.finalize(runtime, before, after, absence, output)
