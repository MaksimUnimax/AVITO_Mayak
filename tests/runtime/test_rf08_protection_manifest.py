from __future__ import annotations

import json
from pathlib import Path

from scripts.runtime.rf08_verify_structural_gateway import resolve_protection_manifest


def test_rf08_protection_manifest_has_required_semantic_invariants() -> None:
    root = Path(__file__).resolve().parents[2]
    manifest = json.loads(
        (root / "scripts/runtime/rf08_protection_manifest.json").read_text(encoding="utf-8")
    )
    required = {
        "task_scoped_acceptance_executes_only_built_in_image_code",
        "single_docker_transport",
        "sealed_bootstrap_remains_distinct",
    }
    entries = {entry["id"] for entry in manifest["invariants"]}
    assert manifest["schema_version"] == "rf08-protection-scenarios-v4"
    assert entries == required
    result = resolve_protection_manifest(root)
    assert not result["errors"]
    assert len(result["resolved"]) >= len(required)


def test_rf08_protection_manifest_rejects_deleted_target(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "scripts/runtime/rf08_protection_manifest.json").read_text())
    target = root / "tests/runtime/test_rf08_adversarial_registry.py"
    shadow = tmp_path / "repo"
    (shadow / "scripts/runtime").mkdir(parents=True)
    (shadow / "tests/runtime").mkdir(parents=True)
    (shadow / "scripts/runtime/rf08_protection_manifest.json").write_text(json.dumps(manifest))
    (shadow / "tests/runtime/test_rf08_adversarial_registry.py").write_text(target.read_text())
    shadow_target = shadow / "tests/runtime/test_rf08_adversarial_registry.py"
    shadow_target.write_text(
        shadow_target.read_text().replace(
            "def test_renaming_does_not_change_verdict", "def test_deleted_target"
        )
    )
    assert resolve_protection_manifest(shadow)["errors"]
