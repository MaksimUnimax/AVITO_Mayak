# ruff: noqa: E501
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from scripts.runtime.rf24_backup_restore_core import (
    RF24_PROJECTION_SCHEMA,
    ProjectionSchemaError,
    build_manifest,
    inspect_clean_target,
    scan_paths,
    validate_projection_schema,
    verify_evidence,
)
from scripts.runtime.run_rf24_backup_restore import (
    ConnectionIdentity,
    compose_create_role,
    database_tool_role_args,
    direct_identity,
    run_binary_to_file,
    run_with_archive,
    tool,
    validate_archive_transport,
)

SHA = "a" * 40


def good() -> dict[str, object]:
    return {
        "schema_version": 2,
        "technical_id": "RF24-BACKUP-RESTORE-SCENARIO-01",
        "source_sha": SHA,
        "hosted_run_id": "123",
        "backup": {"sha256": "b" * 64, "size": 12, "verified": True, "format": "custom", "inventory_verified": True, "readability_verified": True, "pg_dump_version": "pg_dump (PostgreSQL) 18.0", "pg_restore_version": "pg_restore (PostgreSQL) 18.0", "postgres_server_version": "PostgreSQL 18.0"},
        "restore": {"result": "PASS"},
        "runtime_read_proof": True,
        "source_fingerprint_before": "x",
        "source_fingerprint_after": "x",
        "target_semantic_equivalence": True,
        "clean_target_prerequisite": True,
        "negative_controls": {
            x: {"executed": True, "shared_preflight_used": True, "preflight_result": "BLOCKED", "observed_reason": "synthetic observed rejection", "target_fingerprint_before": "target", "target_fingerprint_after": "target"}
            for x in (
                "tampered_digest",
                "corrupt_copy",
                "wrong_source_sha",
                "wrong_source_revision",
                "nonempty_newer_target",
                "duplicate_restore",
            )
        },
        "source_projection": {name: {"table": table, "count": 1, "digest": "a"} for name, (table, _) in RF24_PROJECTION_SCHEMA.items()},
        "target_projection": {name: {"table": table, "count": 1, "digest": "a"} for name, (table, _) in RF24_PROJECTION_SCHEMA.items()},
        "idempotency_replay": {"executed": True, "boundary": "POST /api/v1/beacons", "scope": "beacon_management", "key": "k", "fingerprint": "f", "result": {"class": "duplicate", "status": 200}, "before": {"fingerprint": "x", "counts": {}}, "after": {"fingerprint": "x", "counts": {}}, "beacon_revision_delta": 0, "lifecycle_delta": 0, "notification_delta": 0, "outbox_delta": 0, "provider_effect_delta": 0, "live_provider_calls": 0},
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


@pytest.mark.parametrize("field", ["before", "after", "boundary", "key", "fingerprint"])
def test_verifier_rejects_fabricated_minimal_replay(field: str) -> None:
    value = good()
    value["idempotency_replay"] = good()["idempotency_replay"]
    del value["idempotency_replay"][field]
    with pytest.raises(ValueError):
        verify_evidence(value, source_sha=SHA, run_id="123")


def test_verifier_recomputes_nonzero_effect_from_observed_counts() -> None:
    value = good()
    replay = value["idempotency_replay"]
    replay["before"] = {"fingerprint": "x", "counts": {"beacon_beacons": 1}}
    replay["after"] = {"fingerprint": "x", "counts": {"beacon_beacons": 2}}
    replay["original_beacon_id"] = "beacon-1"
    replay["replay_beacon_id"] = "beacon-1"
    replay["original_account_id"] = "account-1"
    replay["result"]["beacon_id"] = "beacon-1"
    with pytest.raises(ValueError, match="observation-derived"):
        verify_evidence(value, source_sha=SHA, run_id="123")


def test_scanner_rejects_raw_backup_and_secret(tmp_path: Path) -> None:
    dump = tmp_path / "copy.dump"
    dump.write_bytes(b"opaque")
    secret = tmp_path / "evidence.json"
    secret.write_text('{"dsn":"postgresql://u:p@db/x"}')
    result = scan_paths([dump, secret])
    assert result["finding_count"] == 2


@pytest.mark.parametrize("value", [
    "postgresql+psycopg://user:secret@host/db",
    "postgres://user:secret@host/db",
])
def test_scanner_rejects_all_credential_bearing_postgres_dialects(tmp_path: Path, value: str) -> None:
    path = tmp_path / "evidence.json"
    path.write_text(json.dumps({"dsn": value}))
    assert scan_paths([path])["finding_count"] == 1


def test_psycopg_boundary_rejects_sqlalchemy_dialect_without_exposing_value() -> None:
    with pytest.raises(ValueError, match="libpq") as error:
        direct_identity("postgresql+psycopg://user:secret@host/db")
    assert "secret" not in str(error.value)


def test_structured_connection_identity_is_not_a_string_rewrite() -> None:
    identity = direct_identity("postgresql://migration:secret@host:5432/source")
    assert isinstance(identity, ConnectionIdentity)
    assert identity.connect_kwargs()["user"] == "migration"


def test_manifest_is_hash_bound_and_excludes_raw_backup(tmp_path: Path) -> None:
    safe = tmp_path / "evidence.json"
    safe.write_text(json.dumps(good(), sort_keys=True))
    scanner = scan_paths([safe])
    manifest = build_manifest([safe], source_sha=SHA, run_id="123", scanner=scanner)
    assert manifest["raw_backup_excluded"] is True
    assert manifest["files"][0]["sha256"]


def test_role_ddl_uses_literal_password_and_identifier() -> None:
    statement = compose_create_role('safe"role', "pw' OR true --", createdb=True).as_string(None)
    assert '"safe""role"' in statement
    assert "'pw'' OR true --'" in statement
    assert "%s" not in statement
    assert "CREATEDB" in statement
    assert "password" not in statement.lower().split("--", 1)[-1]
    plain = compose_create_role("plain_role", "safe-password").as_string(None)
    assert "CREATEDB" not in plain
    assert "%s" not in plain


def test_archive_transport_rejects_detached_docker_exec() -> None:
    with pytest.raises(ValueError, match="attach stdin"):
        validate_archive_transport(["docker", "exec", "-u", "postgres", "container", "pg_restore", "--list"])


def test_archive_transport_accepts_interactive_docker_exec() -> None:
    validate_archive_transport(["docker", "exec", "-i", "-u", "postgres", "container", "pg_restore", "--list"])


def test_tool_prefix_keeps_explicit_database_role_and_no_secret_argv(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RF24_PG_TOOL_PREFIX", "docker exec -i -u postgres -e PGPASSFILE=/tmp/rf24.pgpass container")
    command = tool("pg_restore", *database_tool_role_args(), "target")
    assert "mayak_migration" in command
    assert "migration-only" not in command
    assert "-i" in command
    assert all("password" not in value.lower() for value in command)


def test_run_with_archive_opens_binary_input_and_preserves_stdout(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    archive = tmp_path / "archive.dump"
    archive.write_bytes(b"custom-format-bytes")
    observed: dict[str, object] = {}

    def fake_run(cmd: list[str], **kwargs: object) -> object:
        observed.update(kwargs)
        handle = kwargs["stdin"]
        assert getattr(handle, "mode") == "rb"
        assert handle.read() == b"custom-format-bytes"
        return subprocess.CompletedProcess(cmd, 0, stdout="TOC\n", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    assert run_with_archive(["docker", "exec", "-i", "container", "pg_restore", "--list"], archive) == "TOC\n"
    assert observed["text"] is True
    assert observed["shell"] if "shell" in observed else True


def test_run_with_archive_propagates_nonzero_without_serializing_stderr(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    archive = tmp_path / "archive.dump"
    archive.write_bytes(b"opaque")

    def fail_run(cmd: list[str], **kwargs: object) -> object:
        raise subprocess.CalledProcessError(1, cmd, stderr="secret-password")

    monkeypatch.setattr(subprocess, "run", fail_run)
    with pytest.raises(subprocess.CalledProcessError) as error:
        run_with_archive(["docker", "exec", "-i", "container", "pg_restore", "--list"], archive)
    assert error.value.returncode == 1
    assert "secret-password" not in str(error.value)


def test_run_binary_to_file_uses_binary_stdout_and_no_shell(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    destination = tmp_path / "archive.dump"
    observed: dict[str, object] = {}

    def fake_run(cmd: list[str], **kwargs: object) -> None:
        observed.update(kwargs)
        handle = kwargs["stdout"]
        handle.write(b"custom")

    monkeypatch.setattr(subprocess, "run", fake_run)
    run_binary_to_file(["docker", "exec", "-i", "container", "pg_dump"], destination)
    assert destination.read_bytes() == b"custom"
    assert "shell" not in observed


class _Cursor:
    def __init__(self, rows: list[tuple[str, str]]) -> None:
        self.rows = rows

    def __enter__(self) -> "_Cursor":
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def execute(self, *_: object) -> None:
        return None

    def fetchall(self) -> list[tuple[str, str]]:
        return self.rows


class _Connection:
    def __init__(self, rows: list[tuple[str, str]]) -> None:
        self.cursor_value = _Cursor(rows)

    def cursor(self) -> _Cursor:
        return self.cursor_value


def _schema_rows() -> list[tuple[str, str]]:
    return [(table, column) for table, columns in RF24_PROJECTION_SCHEMA.values() for column in columns]


def test_current_projection_schema_contract_passes_and_ignores_extra_columns() -> None:
    validate_projection_schema(_Connection([*_schema_rows(), ("unrelated", "column")]))


def test_projection_schema_contract_fails_closed_for_missing_table_without_secrets() -> None:
    rows = [row for row in _schema_rows() if row[0] != "beacon_lifecycle_events"]
    with pytest.raises(ProjectionSchemaError, match=r"table:beacon_lifecycle_events") as error:
        validate_projection_schema(_Connection(rows))
    assert "password" not in str(error.value).lower()
    assert "postgresql://" not in str(error.value)


def test_projection_schema_contract_fails_closed_for_missing_column() -> None:
    rows = [row for row in _schema_rows() if row != ("beacon_lifecycle_events", "causation_reference")]
    with pytest.raises(ProjectionSchemaError, match=r"beacon_lifecycle_events\.causation_reference"):
        validate_projection_schema(_Connection(rows))


class _CatalogCursor:
    def __init__(self) -> None:
        self._result: list[tuple[object, ...]] = []

    def __enter__(self) -> "_CatalogCursor":
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def execute(self, query: str, _: object) -> None:
        if "information_schema.schemata" in query:
            self._result = [(False,)]
        elif "pg_catalog.pg_class" in query:
            self._result = []

    def fetchone(self) -> tuple[object, ...]:
        return self._result[0]

    def fetchall(self) -> list[tuple[object, ...]]:
        return self._result


class _CatalogConnection:
    def cursor(self) -> _CatalogCursor:
        return _CatalogCursor()


def test_clean_target_inspection_is_catalog_only_and_strictly_empty() -> None:
    state = inspect_clean_target(_CatalogConnection())
    assert state.phase == "CLEAN_TARGET_PRE_RESTORE"
    assert state.is_clean
    assert state.project_relations == ()


def test_lifecycle_projection_uses_lifecycle_columns_and_revision_history_has_its_owner() -> None:
    source = Path(__file__).parents[2] / "scripts/runtime/run_rf24_vertical_spine.py"
    text = source.read_text(encoding="utf-8")
    assert "revision_no, to_state FROM mayak.beacon_lifecycle_events" not in text
    assert "beacon_configuration_revisions" in text
    lifecycle = RF24_PROJECTION_SCHEMA["beacon_history"]
    revisions = RF24_PROJECTION_SCHEMA["beacon_configuration_history"]
    assert "revision_no" not in lifecycle[1]
    assert "revision_no" in revisions[1]
