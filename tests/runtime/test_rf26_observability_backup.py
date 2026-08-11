# ruff: noqa: E501
from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from mayak.platform.observability import JsonOperationalFormatter, correlation_id
from scripts.runtime.rf26_operability import manifest_for, retain_expired, verify_backup


def test_correlation_is_bounded_and_invalid_values_are_replaced() -> None:
    assert correlation_id("request-01") == "request-01"
    generated = correlation_id("not safe\n" + "x" * 200)
    assert generated.startswith("c-") and len(generated) <= 34


def test_json_formatter_is_ndjson_and_has_safe_identity() -> None:
    import logging

    record = logging.LogRecord("mayak.test", logging.INFO, __file__, 1, "safe", (), None)
    record.operation = "test"
    record.outcome = "success"
    record.reason_code = "TEST_OK"
    data = json.loads(JsonOperationalFormatter().format(record))
    assert data["operation"] == "test"
    assert "password" not in data


def test_retention_is_fail_closed_for_foreign_unknown_and_symlink(tmp_path: Path) -> None:
    old = datetime.now(UTC) - timedelta(days=8)
    expired = tmp_path / "expired"
    expired.mkdir()
    dump = expired / "backup.dump"
    dump.write_bytes(b"synthetic")
    manifest = manifest_for(dump, environment_id="env", source_sha="a" * 40, migration_revision="head", tool_identity="pg_dump 18", now=old)
    manifest["retention_expiry"] = (old + timedelta(days=7)).isoformat()
    (expired / "manifest.json").write_text(json.dumps(manifest))
    unknown = tmp_path / "unknown"
    unknown.mkdir()
    (unknown / "x").write_text("keep")
    assert retain_expired(tmp_path, now=datetime.now(UTC)) == ["expired"]
    assert unknown.exists()


def test_backup_verification_rejects_tampering(tmp_path: Path) -> None:
    backup = tmp_path / "backup.dump"
    backup.write_bytes(b"synthetic")
    manifest = manifest_for(backup, environment_id="env", source_sha="a" * 40, migration_revision="head", tool_identity="pg_dump 18")
    backup.write_bytes(b"tampered")
    with pytest.raises(ValueError, match="digest"):
        verify_backup(backup, manifest)
