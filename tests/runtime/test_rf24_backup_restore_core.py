# ruff: noqa: E501
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.runtime.rf24_backup_restore_core import build_manifest, scan_paths, verify_evidence

SHA = "a" * 40


def good() -> dict[str, object]:
    return {
        "schema_version": 2,
        "technical_id": "RF24-BACKUP-RESTORE-SCENARIO-01",
        "source_sha": SHA,
        "hosted_run_id": "123",
        "backup": {"sha256": "b" * 64, "size": 12, "verified": True, "format": "custom", "inventory_verified": True, "readability_verified": True, "pg_dump_version": "pg_dump (PostgreSQL) 18.0", "pg_restore_version": "pg_restore (PostgreSQL) 18.0", "postgres_server_version": "PostgreSQL 18.0"},
        "restore": {"result": "PASS"},
        "source_fingerprint_before": "x",
        "source_fingerprint_after": "x",
        "target_semantic_equivalence": True,
        "clean_target_prerequisite": True,
        "negative_controls": {
            x: {"executed": True, "preflight_result": "BLOCKED", "observed_reason": "synthetic observed rejection", "target_fingerprint_before": "target", "target_fingerprint_after": "target"}
            for x in (
                "tampered_digest",
                "corrupt_copy",
                "wrong_source_revision",
                "nonempty_newer_target",
                "duplicate_restore",
            )
        },
        "seed": {"runtime_boundary": "accepted-public-runtime", "state_classes": {"identity": {"count": 1, "projection_digest": "a"}}},
        "security": {
            "provider_live_calls": 0,
            "raw_provider_payload": False,
            "production_personal_data": False,
            "public_ingress": False,
            "postgres_host_published": False,
            "foreign_resource_impact": "none",
            "credentials_exposure": False,
            "raw_backup_uploaded": False,
            "raw_backup_cleanup": True,
            "direct_foreign_module_dml": False,
            "owner_bypass": False,
        },
    }


def test_verifier_accepts_complete_evidence() -> None:
    assert verify_evidence(good(), source_sha=SHA, run_id="123")["verdict"] == "PASS"


@pytest.mark.parametrize("field", ["target_semantic_equivalence", "clean_target_prerequisite"])
def test_verifier_rejects_missing_invariants(field: str) -> None:
    value = good()
    value[field] = False
    with pytest.raises(ValueError):
        verify_evidence(value, source_sha=SHA, run_id="123")


def test_scanner_rejects_raw_backup_and_secret(tmp_path: Path) -> None:
    dump = tmp_path / "copy.dump"
    dump.write_bytes(b"opaque")
    secret = tmp_path / "evidence.json"
    secret.write_text('{"dsn":"postgresql://u:p@db/x"}')
    result = scan_paths([dump, secret])
    assert result["finding_count"] == 2


def test_manifest_is_hash_bound_and_excludes_raw_backup(tmp_path: Path) -> None:
    safe = tmp_path / "evidence.json"
    safe.write_text(json.dumps(good(), sort_keys=True))
    scanner = scan_paths([safe])
    manifest = build_manifest([safe], source_sha=SHA, run_id="123", scanner=scanner)
    assert manifest["raw_backup_excluded"] is True
    assert manifest["files"][0]["sha256"]
