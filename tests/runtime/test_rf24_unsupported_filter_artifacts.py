# ruff: noqa: E501
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_workflow_validator_positive_and_mutation(tmp_path: Path) -> None:
    workflow = ROOT / ".github/workflows/ci-rf24-unsupported-filter.yml"
    validator = ROOT / "scripts/runtime/check_rf24_unsupported_filter_workflow.py"
    good = subprocess.run(
        [sys.executable, str(validator), str(workflow)], capture_output=True, text=True
    )
    assert good.returncode == 0, good.stdout + good.stderr
    weakened = tmp_path / "weakened.yml"
    text = workflow.read_text(encoding="utf-8").replace("FIELD_UNSUPPORTED", "REMOVED_PROOF")
    weakened.write_text(text, encoding="utf-8")
    bad = subprocess.run(
        [sys.executable, str(validator), str(weakened)], capture_output=True, text=True
    )
    assert bad.returncode != 0


def test_manifest_is_json_bound(tmp_path: Path) -> None:
    artifact = tmp_path / "evidence.json"
    artifact.write_text(
        json.dumps({"technical_id": "RF24-UNSUPPORTED-FILTER-SCENARIO-01"}), encoding="utf-8"
    )
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/runtime/build_rf24_unsupported_filter_manifest.py"),
            str(tmp_path),
            "--source-sha",
            "a" * 40,
            "--run-id",
            "run",
            "--output",
            str(tmp_path / "manifest.json"),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["source_sha"] == "a" * 40
    assert manifest["files"][0]["basename"] == "evidence.json"
