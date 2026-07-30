# mypy: ignore-errors
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

import scripts.runtime.prepare_file_secrets as module
from scripts.runtime.prepare_file_secrets import (
    FAILPOINTS,
    MANIFEST_NAME,
    MODE,
    ROOT_MODE,
    SecretPreparationError,
    activate_generation,
    cleanup_retired,
    prepare_generation,
    recover,
    show_active_safe,
    validate_generation,
)


def root_for(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(module, "_ALLOWED_ROOTS", (tmp_path,))
    return tmp_path / "secrets"


def metadata(root: Path, generation: str) -> dict[str, tuple[bytes, int, int, int]]:
    directory = root / "sets" / generation
    return {
        p.name: (p.read_bytes(), p.stat().st_uid, p.stat().st_gid, stat.S_IMODE(p.stat().st_mode))
        for p in directory.iterdir()
        if p.is_file()
    }


def make_active(root: Path) -> str:
    generation = prepare_generation(root, postgres_uid=999, postgres_gid=999)
    activate_generation(root, generation, postgres_uid=999, postgres_gid=999)
    return generation


def test_initial_generation_layout_manifest_owners_modes_and_equality(tmp_path, monkeypatch):
    root = root_for(tmp_path, monkeypatch)
    generation = make_active(root)
    assert stat.S_IMODE(root.stat().st_mode) == ROOT_MODE
    assert stat.S_IMODE((root / "sets").stat().st_mode) == ROOT_MODE
    assert (root / "active").is_symlink()
    assert (root / "active").readlink() == Path(f"sets/{generation}")
    directory = root / "sets" / generation
    assert {p.name for p in directory.iterdir()} == {
        "mayak_postgres_bootstrap_password_postgres",
        "mayak_postgres_bootstrap_password_runtime",
        "mayak_database_application_password",
        "mayak_database_migration_password",
        "mayak_session_signing_key",
        MANIFEST_NAME,
    }
    assert (directory / "mayak_postgres_bootstrap_password_postgres").read_bytes() == (
        directory / "mayak_postgres_bootstrap_password_runtime"
    ).read_bytes()
    assert stat.S_IMODE((directory / MANIFEST_NAME).stat().st_mode) == 0o600
    for path in directory.iterdir():
        if path.name != MANIFEST_NAME:
            assert stat.S_IMODE(path.stat().st_mode) == MODE
    validate_generation(root, generation, postgres_uid=999, postgres_gid=999)


def test_manifest_unknown_file_copy_mode_owner_and_pointer_rejected(tmp_path, monkeypatch):
    root = root_for(tmp_path, monkeypatch)
    generation = make_active(root)
    directory = root / "sets" / generation
    (directory / "unexpected").write_text("x")
    with pytest.raises(SecretPreparationError):
        validate_generation(root, generation, postgres_uid=999, postgres_gid=999)
    (directory / "unexpected").unlink()
    os.chmod(directory / "mayak_database_application_password", 0o600)
    with pytest.raises(SecretPreparationError):
        validate_generation(root, generation, postgres_uid=999, postgres_gid=999)
    os.chmod(directory / "mayak_database_application_password", MODE)
    (directory / "mayak_postgres_bootstrap_password_runtime").write_bytes(b"different")
    with pytest.raises(SecretPreparationError):
        validate_generation(root, generation, postgres_uid=999, postgres_gid=999)
    (root / "active").unlink()
    (root / "active").symlink_to("../../outside")
    with pytest.raises(SecretPreparationError):
        show_active_safe(root, postgres_uid=999, postgres_gid=999)


def test_rotation_failure_preserves_existing_set_and_unrelated_file(tmp_path, monkeypatch):
    root = root_for(tmp_path, monkeypatch)
    first = make_active(root)
    unrelated = root / "unrelated"
    unrelated.write_text("preserve")
    before = metadata(root, first)
    monkeypatch.setenv(module.FAILPOINT_ENV, "after-each-secret-file-write")
    with pytest.raises(SecretPreparationError):
        prepare_generation(root, postgres_uid=999, postgres_gid=999)
    monkeypatch.delenv(module.FAILPOINT_ENV)
    assert show_active_safe(root, postgres_uid=999, postgres_gid=999)["generation_id"] == first
    assert metadata(root, first) == before
    assert unrelated.read_text() == "preserve"


@pytest.mark.parametrize(
    "failpoint",
    tuple(
        point
        for point in FAILPOINTS
        if point
        not in {
            "before-service-recreation",
            "after-failed-health-verification",
            "during-rollback-pointer-replacement",
            "during-retired-generation-cleanup",
        }
    ),
)
def test_failpoint_recovery_has_one_complete_active_generation(tmp_path, monkeypatch, failpoint):
    root = root_for(tmp_path, monkeypatch)
    first = make_active(root)
    before = metadata(root, first)
    monkeypatch.setenv(module.FAILPOINT_ENV, failpoint)
    try:
        if failpoint in {
            "before-temporary-pointer-creation",
            "after-temporary-pointer-creation",
            "immediately-before-active-pointer-replace",
            "immediately-after-active-pointer-replace",
            "before-parent-directory-fsync",
            "after-parent-directory-fsync",
        }:
            second = prepare_generation(root, postgres_uid=999, postgres_gid=999)
            with pytest.raises(SecretPreparationError):
                activate_generation(root, second, postgres_uid=999, postgres_gid=999)
        else:
            with pytest.raises(SecretPreparationError):
                prepare_generation(root, postgres_uid=999, postgres_gid=999)
    finally:
        monkeypatch.delenv(module.FAILPOINT_ENV)
    active = recover(root, postgres_uid=999, postgres_gid=999)
    assert active in {first, *[p.name for p in (root / "sets").iterdir()]}
    validate_generation(root, active, postgres_uid=999, postgres_gid=999)
    if active == first:
        assert metadata(root, first) == before


def test_abrupt_child_termination_and_recovery(tmp_path, monkeypatch):
    root = Path("/opt/avito-mayak-runtime/rf08-secret-delivery") / f"test-abrupt-{os.getpid()}"
    monkeypatch.setattr(module, "_ALLOWED_ROOTS", (Path("/opt/avito-mayak-runtime"),))
    first = make_active(root)
    env = os.environ | {
        "PYTHONPATH": str(Path.cwd()),
        module.FAILPOINT_ENV: "after-each-secret-file-write",
        module.FAILPOINT_EXIT_ENV: "1",
    }
    child_code = (
        "from pathlib import Path; import scripts.runtime.prepare_file_secrets as s; "
        "s._ALLOWED_ROOTS=(Path('/opt/avito-mayak-runtime'),); "
        f"s.prepare_generation(Path({str(root)!r}), postgres_uid=999, postgres_gid=999)"
    )
    child = subprocess.run(
        [
            sys.executable,
            "-c",
            child_code,
        ],
        env=env,
        capture_output=True,
        text=True,
    )
    assert child.returncode != 0 and child.stdout == child.stderr == ""
    assert recover(root, postgres_uid=999, postgres_gid=999) == first
    validate_generation(root, first, postgres_uid=999, postgres_gid=999)
    for path in sorted(root.rglob("*"), reverse=True):
        if path.is_file() or path.is_symlink():
            path.unlink()
        elif path.is_dir():
            path.rmdir()
    root.rmdir()


def test_rollback_and_cleanup_failpoints_preserve_active(tmp_path, monkeypatch):
    root = root_for(tmp_path, monkeypatch)
    first = make_active(root)
    second = prepare_generation(root, postgres_uid=999, postgres_gid=999)
    monkeypatch.setenv(module.FAILPOINT_ENV, "during-rollback-pointer-replacement")
    with pytest.raises(SecretPreparationError):
        module.rollback_activation(root, first, postgres_uid=999, postgres_gid=999)
    monkeypatch.setenv(module.FAILPOINT_ENV, "during-retired-generation-cleanup")
    with pytest.raises(SecretPreparationError):
        cleanup_retired(root, keep=(first,), postgres_uid=999, postgres_gid=999)
    monkeypatch.delenv(module.FAILPOINT_ENV)
    assert show_active_safe(root, postgres_uid=999, postgres_gid=999)["generation_id"] == first
    assert (root / "sets" / second).exists()


def test_cleanup_only_removes_valid_retired_generations(tmp_path, monkeypatch):
    root = root_for(tmp_path, monkeypatch)
    first = make_active(root)
    second = prepare_generation(root, postgres_uid=999, postgres_gid=999)
    activate_generation(root, second, postgres_uid=999, postgres_gid=999)
    assert first in cleanup_retired(root, keep=(), postgres_uid=999, postgres_gid=999)
    assert not (root / "sets" / first).exists()
    assert (root / "sets" / second).exists()
