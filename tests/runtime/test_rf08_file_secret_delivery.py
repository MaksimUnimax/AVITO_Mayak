import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.runtime.prepare_file_secrets import (
    MANIFEST_NAME,
    MODE,
    ROOT_MODE,
    RUNTIME_GID,
    RUNTIME_UID,
    SecretPreparationError,
    prepare,
    validate,
)

ROOT = Path(__file__).parents[2]
UTILITY = ROOT / "scripts/runtime/prepare_file_secrets.py"
COMPOSE = ROOT / "compose.yaml"


def _root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    import scripts.runtime.prepare_file_secrets as module

    monkeypatch.setattr(module, "_ALLOWED_ROOTS", (tmp_path,))
    return tmp_path / "secrets"


def test_generation_has_exact_modes_owners_and_consistent_bootstrap(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _root(tmp_path, monkeypatch)
    prepare(root, postgres_uid=999, postgres_gid=999, rotate=False)
    assert stat.S_IMODE(root.stat().st_mode) == ROOT_MODE
    postgres = root / "mayak_postgres_bootstrap_password_postgres"
    runtime = root / "mayak_postgres_bootstrap_password_runtime"
    assert postgres.read_bytes() == runtime.read_bytes()
    assert stat.S_IMODE(postgres.stat().st_mode) == MODE
    assert (postgres.stat().st_uid, postgres.stat().st_gid) == (999, 999)
    for name in (
        "mayak_database_application_password",
        "mayak_database_migration_password",
        "mayak_session_signing_key",
    ):
        path = root / name
        assert stat.S_IMODE(path.stat().st_mode) == MODE
        assert (path.stat().st_uid, path.stat().st_gid) == (RUNTIME_UID, RUNTIME_GID)
    assert json.loads((root / MANIFEST_NAME).read_text())["files"]


def test_validation_detects_missing_owner_and_mode_and_preserves_unrelated(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _root(tmp_path, monkeypatch)
    prepare(root, postgres_uid=999, postgres_gid=999, rotate=False)
    unrelated = root / "unrelated"
    unrelated.write_text("not a secret")
    validate(root, postgres_uid=999, postgres_gid=999)
    (root / "mayak_database_migration_password").unlink()
    with pytest.raises(SecretPreparationError):
        validate(root, postgres_uid=999, postgres_gid=999)
    prepare(root, postgres_uid=999, postgres_gid=999, rotate=True)
    path = root / "mayak_database_application_password"
    os.chmod(path, 0o600)
    with pytest.raises(SecretPreparationError):
        validate(root, postgres_uid=999, postgres_gid=999)
    assert unrelated.read_text() == "not a secret"


def test_symlink_and_path_traversal_are_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _root(tmp_path, monkeypatch)
    root.mkdir(mode=ROOT_MODE)
    (root / "mayak_database_application_password").symlink_to(tmp_path / "outside")
    with pytest.raises(SecretPreparationError):
        prepare(root, postgres_uid=999, postgres_gid=999, rotate=False)
    with pytest.raises(SecretPreparationError):
        prepare(tmp_path / ".." / "outside", postgres_uid=999, postgres_gid=999, rotate=False)


def test_rotation_replaces_all_logical_copies_without_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _root(tmp_path, monkeypatch)
    prepare(root, postgres_uid=999, postgres_gid=999, rotate=False)
    before = {path.name: path.read_bytes() for path in root.iterdir() if path.name != MANIFEST_NAME}
    prepare(root, postgres_uid=999, postgres_gid=999, rotate=True)
    after = {path.name: path.read_bytes() for path in root.iterdir() if path.name != MANIFEST_NAME}
    assert before != after
    assert after["mayak_postgres_bootstrap_password_postgres"] == after[
        "mayak_postgres_bootstrap_password_runtime"
    ]


def test_partial_generation_rolls_back_without_incomplete_set(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import scripts.runtime.prepare_file_secrets as module

    root = _root(tmp_path, monkeypatch)
    original_replace = module.os.replace
    calls = 0

    def fail_after_first(source: Path, target: Path) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("synthetic failure")
        original_replace(source, target)

    monkeypatch.setattr(module.os, "replace", fail_after_first)
    with pytest.raises(SecretPreparationError):
        prepare(root, postgres_uid=999, postgres_gid=999, rotate=False)
    assert list(root.iterdir()) == []


def test_cli_never_exports_values_or_tracebacks(tmp_path: Path) -> None:
    root = tmp_path / "secrets"
    # The subprocess test uses the accepted task root boundary, not /tmp.
    task_root = Path("/opt/avito-mayak-runtime/rf08-secret-delivery/test-cli") / root.name
    task_root.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    try:
        result = subprocess.run(
            [sys.executable, str(UTILITY), "--root", str(task_root)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert result.stdout == ""
        assert result.stderr == ""
    finally:
        for path in task_root.iterdir() if task_root.exists() else ():
            path.unlink()
        if task_root.exists():
            task_root.rmdir()


def test_compose_uses_distinct_sources_and_canonical_targets() -> None:
    text = COMPOSE.read_text()
    assert "mayak_postgres_bootstrap_password_postgres" in text
    assert "mayak_postgres_bootstrap_password_runtime" in text
    assert "source: mayak_postgres_bootstrap_password_postgres" in text
    assert "source: mayak_postgres_bootstrap_password_runtime" in text
    assert text.count("target: mayak_postgres_bootstrap_password") == 2
    assert "password:" not in text
    assert "MAYAK_DATABASE_APPLICATION_PASSWORD" not in text
    postgres = text.split("\n  mayak-postgres:\n", 1)[1].split("\n  mayak-db-bootstrap:\n", 1)[0]
    assert "ports:" not in postgres
    assert "internal: true" in text
    assert 'user: "10001:10001"' in text
    assert "0440" not in text and "0444" not in text
