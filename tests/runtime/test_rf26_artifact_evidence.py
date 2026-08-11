# ruff: noqa: E501
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.runtime.rf26_artifact_evidence import (
    EXPECTED_FILES,
    build_observability_receipt,
    verify_exact_artifact,
    verify_observability,
    write_exact_artifact,
)

SHA = "a" * 40
RUN = "123"
ENV = "rf26-123"


def evidence() -> dict:
    return {"environment_id": ENV, "stages": [{"stage_id": "H8_REBUILD_FROM_ZERO", "observed_outputs": {"api_http_projection": {"version": {"source_sha": SHA, "environment_id": ENV, "migration_revision": "head-01"}, "diagnostics": {"readiness_state": "ready", "process_kind": "api", "runtime_profile": "synthetic_acceptance", "migration_revision": "head-01"}, "readiness": {"status": "ready", "migration_revision": "head-01"}}}}]}


def test_observability_receipt_uses_formatter_and_is_bound() -> None:
    value = build_observability_receipt(evidence=evidence(), source_sha=SHA, run_id=RUN, environment_id=ENV)
    path = Path("/tmp/rf26-observability-test.json")
    path.write_text(json.dumps(value), encoding="utf-8")
    try:
        verify_observability(path, source_sha=SHA, run_id=RUN, environment_id=ENV)
    finally:
        path.unlink(missing_ok=True)
    assert value["structured_log_schema"]["sample_event"]["correlation_id"] == f"rf26:{RUN}"


def _artifact(tmp_path: Path) -> Path:
    root = tmp_path / "evidence"
    root.mkdir()
    obs = build_observability_receipt(evidence=evidence(), source_sha=SHA, run_id=RUN, environment_id=ENV)
    values = {name: {"source_sha": SHA, "hosted_run_id": RUN} for name in EXPECTED_FILES if name not in {"observability.json", "artifact-safety.json", "artifact-manifest.json"}}
    values["observability.json"] = obs
    values["artifact-safety.json"] = {"finding_count": 0}
    for name, value in values.items():
        (root / name).write_text(json.dumps(value), encoding="utf-8")
    write_exact_artifact(root, source_sha=SHA, run_id=RUN, environment_id=ENV)
    return root


def test_exact_artifact_accepts_manifest_and_safety(tmp_path: Path) -> None:
    root = _artifact(tmp_path)
    verify_exact_artifact(root, source_sha=SHA, run_id=RUN, environment_id=ENV)
    assert sorted(path.name for path in root.iterdir()) == sorted(EXPECTED_FILES)


@pytest.mark.parametrize("mutation", ["missing", "extra", "digest", "symlink", "wrong_run"])
def test_exact_artifact_rejects_contract_mutations(tmp_path: Path, mutation: str) -> None:
    root = _artifact(tmp_path)
    if mutation == "missing":
        (root / "observability.json").unlink()
    elif mutation == "extra":
        (root / "extra.json").write_text("{}")
    elif mutation == "digest":
        (root / "acceptance.json").write_text("tampered")
    elif mutation == "symlink":
        target = tmp_path / "outside"
        target.write_text("x")
        (root / "verifier.json").unlink()
        (root / "verifier.json").symlink_to(target)
    else:
        value = json.loads((root / "acceptance.json").read_text())
        value["hosted_run_id"] = "999"
        (root / "acceptance.json").write_text(json.dumps(value))
    with pytest.raises(ValueError):
        verify_exact_artifact(root, source_sha=SHA, run_id=RUN, environment_id=ENV)
