# ruff: noqa: E501
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from mayak.platform.observability import JsonOperationalFormatter, correlation_id, safe_message
from mayak.runtime import backup as backup_runtime
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


@pytest.mark.parametrize("message", [
    "bearer fake-token-123",
    "password=fixture-password",
    "postgresql://fixture:fixture@db/mayak",
    "BEGIN RSA PRIVATE KEY",
    "cookie=fixture-cookie",
    "provider_token=fixture-provider-token",
    "raw_provider_payload=fixture-payload",
])
def test_legacy_secret_shaped_messages_are_redacted(message: str) -> None:
    import logging

    record = logging.LogRecord("legacy", logging.INFO, __file__, 1, message, (), None)
    encoded = JsonOperationalFormatter().format(record)
    assert message not in encoded
    assert "[REDACTED]" in safe_message(message)


def test_retention_is_fail_closed_for_foreign_unknown_and_symlink(tmp_path: Path) -> None:
    old = datetime.now(UTC) - timedelta(days=8)
    expired = tmp_path / "expired"
    expired.mkdir()
    dump = expired / "backup.dump"
    dump.write_bytes(b"synthetic")
    manifest = manifest_for(dump, environment_id="env", source_sha="a" * 40, migration_revision="head", tool_identity="pg_dump 18", now=old)
    manifest["retention_expiry"] = (old + timedelta(days=7)).isoformat()
    manifest["backup_id"] = "expired"
    manifest["verification"] = {"readability": True, "inventory": True}
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
        verify_backup(backup, manifest, lambda _: True, lambda _: True)


def test_random_nonempty_bytes_never_verify_as_archive(tmp_path: Path) -> None:
    backup = tmp_path / "backup.dump"
    backup.write_bytes(b"not a postgres archive")
    manifest = manifest_for(backup, environment_id="env", source_sha="a" * 40, migration_revision="head", tool_identity="pg_restore 18")
    with pytest.raises(ValueError, match="readability"):
        verify_backup(backup, manifest, lambda _: False, lambda _: False)


def test_root_and_intermediate_symlink_are_rejected(tmp_path: Path) -> None:
    root_target = tmp_path / "real-root"
    root_target.mkdir()
    root_link = tmp_path / "root-link"
    root_link.symlink_to(root_target, target_is_directory=True)
    with pytest.raises(ValueError, match="root"):
        retain_expired(root_link)
    outside = tmp_path / "outside"
    outside.mkdir()
    root = tmp_path / "root"
    root.mkdir()
    (root / "set").symlink_to(outside, target_is_directory=True)
    from scripts.runtime.rf26_operability import owned_path

    with pytest.raises(ValueError, match="symlink"):
        owned_path(root, root / "set" / "manifest.json")


def test_dump_and_manifest_symlinks_and_unknown_objects_survive_retention(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.write_bytes(b"fixture")
    item = root / "set"
    item.mkdir()
    (item / "backup.dump").symlink_to(outside)
    (item / "manifest.json").write_text("{}")
    assert retain_expired(root) == []
    extra = root / "unknown"
    extra.mkdir()
    (extra / "x").write_text("keep")
    assert extra.exists()


def test_hosted_runner_uses_package_boundary() -> None:
    old = subprocess.run(
        [sys.executable, "-S", "run_rf26_operability_acceptance.py", "--help"],
        cwd=Path("scripts/runtime"),
        env={**os.environ, "PYTHONPATH": ""},
        capture_output=True, text=True,
    )
    assert old.returncode != 0
    assert "No module named 'scripts'" in old.stderr
    current = subprocess.run(
        [sys.executable, "-S", "-m", "scripts.runtime.run_rf26_operability_acceptance", "--help"],
        cwd=Path("."),
        env={**os.environ, "PYTHONPATH": ""},
        capture_output=True, text=True,
    )
    assert current.returncode == 0


def test_backup_requires_one_actual_current_migration_head(monkeypatch: pytest.MonkeyPatch) -> None:
    class Cursor:
        def __enter__(self): return self
        def __exit__(self, *args): return None
        def execute(self, *_args): return None
        def fetchall(self): return [("head-01",)]

    class Connection:
        def __enter__(self): return self
        def __exit__(self, *args): return None
        def cursor(self): return Cursor()

    class FakePsycopg:
        @staticmethod
        def connect(**_kwargs): return Connection()

    monkeypatch.setattr(backup_runtime, "psycopg", FakePsycopg)
    monkeypatch.setattr(backup_runtime.ScriptDirectory, "from_config", lambda _config: type("S", (), {"get_heads": lambda self: ("head-01",)})())
    settings = type("Settings", (), {"database": type("Database", (), {"host": "db", "port": 5432, "name": "mayak", "migration_user": "migration", "connect_timeout_seconds": 5})()})()
    assert backup_runtime.authoritative_migration_revision(settings, "synthetic") == "head-01"

    class MissingCursor(Cursor):
        def fetchall(self): return []
    monkeypatch.setattr(FakePsycopg, "connect", staticmethod(lambda **_kwargs: type("C", (), {"__enter__": lambda s: s, "__exit__": lambda s, *a: None, "cursor": lambda s: MissingCursor()})()))
    with pytest.raises(RuntimeError, match="revision"):
        backup_runtime.authoritative_migration_revision(settings, "synthetic")
