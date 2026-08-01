from __future__ import annotations

import json
from pathlib import Path


def test_rf08_protection_manifest_has_required_semantic_invariants() -> None:
    root = Path(__file__).resolve().parents[2]
    manifest = json.loads(
        (root / "scripts/runtime/rf08_protection_manifest.json").read_text(encoding="utf-8")
    )
    required = {
        "single_transport",
        "no_raw_command_ingress",
        "no_stored_executable_authority",
        "no_generic_inspect_query_authority",
        "no_raw_process_result_escape",
        "no_private_execution_bypass",
        "rename_alias_wrapper_rejection",
        "runtime_binding_generation_epoch",
        "cleanup",
        "foreign_equality",
    }
    entries = {entry["id"] for entry in manifest["invariants"]}
    assert manifest["schema_version"] == "rf08-protection-scenarios-v1"
    assert entries == required
    assert all(entry["evidence"] for entry in manifest["invariants"])
