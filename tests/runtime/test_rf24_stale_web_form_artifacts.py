from __future__ import annotations

import json

from scripts.runtime.build_rf24_stale_web_form_manifest import PAYLOADS
from scripts.runtime.build_rf24_stale_web_form_manifest import main as manifest_main
from scripts.runtime.check_rf24_stale_web_form_artifact_safety import scan


def test_artifact_scanner_allows_synthetic_facts_and_rejects_credentials(
    tmp_path, monkeypatch
) -> None:
    safe = tmp_path / "safe.json"
    safe.write_text(
        json.dumps({"credential_exposure": False, "value": "synthetic"}), encoding="utf-8"
    )
    assert scan([safe]) == []
    unsafe = tmp_path / "unsafe.txt"
    unsafe.write_text("Authorization: Bearer real-token", encoding="utf-8")
    assert scan([unsafe])


def test_manifest_fails_closed_on_missing_or_duplicate_payload(tmp_path, monkeypatch) -> None:
    for name in PAYLOADS:
        (tmp_path / name).write_text(name, encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["manifest", str(tmp_path), "a" * 40, "run-1"])
    assert manifest_main() == 0
    manifest = json.loads((tmp_path / "rf24-stale-web-form-manifest.json").read_text())
    assert manifest["payload_count"] == len(PAYLOADS)
    assert manifest["source_sha"] == "a" * 40
