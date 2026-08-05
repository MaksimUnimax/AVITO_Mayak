from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_rf22_scanner_binds_exact_payload_digests(tmp_path: Path) -> None:
    artifact = tmp_path / "rf22.json"
    log = tmp_path / "rf22-full-pytest.log"
    manifest = tmp_path / "rf22-safety-manifest.json"
    artifact.write_text('{"technical_id":"RF22"}\n', encoding="utf-8")
    log.write_text("focused tests passed\n", encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/runtime/check_rf22_artifact_safety.py"),
            str(artifact),
            str(log),
            "--manifest",
            str(manifest),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    payloads = json.loads(manifest.read_text(encoding="utf-8"))["payloads"]
    assert [item["basename"] for item in payloads] == ["rf22.json", "rf22-full-pytest.log"]
    artifact.write_text('{"technical_id":"TAMPERED"}\n', encoding="utf-8")
    assert (
        next(item for item in payloads if item["basename"] == "rf22.json")["sha256"]
        != __import__("hashlib").sha256(artifact.read_bytes()).hexdigest()
    )


def test_rf22_verifier_rejects_legacy_boolean_artifact(tmp_path: Path) -> None:
    artifact = tmp_path / "rf22.json"
    manifest = tmp_path / "rf22-safety-manifest.json"
    artifact.write_text(json.dumps({"candidate_prepared": True}), encoding="utf-8")
    manifest.write_text("{}", encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/runtime/verify_rf22_acceptance.py"),
            str(artifact),
            "--candidate-sha",
            "0" * 40,
            "--manifest",
            str(manifest),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "legacy boolean" in result.stderr
