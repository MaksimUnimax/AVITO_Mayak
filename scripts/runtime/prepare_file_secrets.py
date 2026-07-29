#!/usr/bin/env python3
"""Crash-safe, consumer-specific file secret generations.

The active directory is a managed relative symlink.  Secret files are regular
files in an immutable generation; activation changes one directory entry only.
"""

from __future__ import annotations

import argparse
import base64
import hmac
import json
import os
import re
import secrets
import stat
from pathlib import Path
from typing import Final, Iterable

RUNTIME_UID: Final = 10001
RUNTIME_GID: Final = 10001
DEFAULT_POSTGRES_UID: Final = 999
DEFAULT_POSTGRES_GID: Final = 999
MANIFEST_NAME: Final = "manifest.json"
MODE: Final = 0o400
ROOT_MODE: Final = 0o700
PROTOCOL_VERSION: Final = "rf08-generation-v1"
GENERATION_RE: Final = re.compile(r"g-[0-9a-f]{24}")
FAILPOINT_ENV: Final = "RF08_FAILPOINT"
FAILPOINT_EXIT_ENV: Final = "RF08_FAILPOINT_EXIT"

_FILES: Final = {
    "postgres_bootstrap": ("mayak_postgres_bootstrap_password_postgres", "postgres"),
    "runtime_bootstrap": ("mayak_postgres_bootstrap_password_runtime", "db-bootstrap"),
    "application_password": ("mayak_database_application_password", "api-worker-scheduler"),
    "migration_password": ("mayak_database_migration_password", "db-bootstrap-migrate"),
    "session_signing_key": ("mayak_session_signing_key", "api"),
}
_ALLOWED_ROOTS: tuple[Path, ...] = (
    Path("/opt/avito-mayak-runtime"),
    Path("/etc/avito-mayak/secrets"),
)
FAILPOINTS: Final[tuple[str, ...]] = (
    "after-root-creation",
    "after-sets-directory-creation",
    "after-each-secret-file-write",
    "after-manifest-write",
    "after-file-fsync",
    "after-generation-directory-fsync",
    "before-temporary-pointer-creation",
    "after-temporary-pointer-creation",
    "immediately-before-active-pointer-replace",
    "immediately-after-active-pointer-replace",
    "before-parent-directory-fsync",
    "after-parent-directory-fsync",
    "before-service-recreation",
    "after-failed-health-verification",
    "during-rollback-pointer-replacement",
    "during-retired-generation-cleanup",
)


class SecretPreparationError(Exception):
    """Constant, safe diagnostic exception."""


def _failpoint(stage: str) -> None:
    if os.environ.get(FAILPOINT_ENV) != stage:
        return
    if os.environ.get(FAILPOINT_EXIT_ENV) == "1":
        os._exit(70)
    raise SecretPreparationError("controlled failpoint")


def _safe_root(root: Path, *, create: bool = True) -> Path:
    root = root.absolute()
    if root.exists() and root.is_symlink():
        raise SecretPreparationError("target root must not be a symlink")
    if not any(root == allowed or allowed in root.parents for allowed in _ALLOWED_ROOTS):
        raise SecretPreparationError("target root is outside the project-owned secret boundary")
    if any(part.is_symlink() for part in (root, *root.parents) if part.exists()):
        raise SecretPreparationError("target root must not contain symlinks")
    if create:
        root.mkdir(mode=ROOT_MODE, parents=True, exist_ok=True)
        _failpoint("after-root-creation")
    if (
        not root.is_dir()
        or root.stat().st_uid != 0
        or stat.S_IMODE(root.stat().st_mode) != ROOT_MODE
    ):
        raise SecretPreparationError("target root ownership or mode is invalid")
    return root


def _safe_generation_id(value: str) -> str:
    if not GENERATION_RE.fullmatch(value):
        raise SecretPreparationError("generation identifier is invalid")
    return value


def _generation(root: Path, generation_id: str) -> Path:
    generation_id = _safe_generation_id(generation_id)
    sets = root / "sets"
    if sets.is_symlink() or not sets.is_dir():
        raise SecretPreparationError("sets directory is invalid")
    path = sets / generation_id
    if path.parent != sets or path.is_symlink():
        raise SecretPreparationError("generation path is invalid")
    return path


def _fsync_directory(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _write_all(fd: int, data: bytes) -> None:
    view = memoryview(data)
    while view:
        view = view[os.write(fd, view) :]


def _write_regular(path: Path, value: bytes, uid: int, gid: int, mode: int) -> None:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), mode)
    try:
        os.fchmod(fd, mode)
        os.fchown(fd, uid, gid)
        _write_all(fd, value)
        _failpoint("after-each-secret-file-write")
        os.fsync(fd)
        _failpoint("after-file-fsync")
    finally:
        os.close(fd)


def _secret() -> bytes:
    return base64.urlsafe_b64encode(secrets.token_bytes(48))


def _manifest(generation_id: str, postgres_uid: int, postgres_gid: int) -> dict[str, object]:
    entries: list[dict[str, object]] = []
    for logical_name, (filename, consumer) in _FILES.items():
        uid, gid = (
            (postgres_uid, postgres_gid)
            if logical_name == "postgres_bootstrap"
            else (RUNTIME_UID, RUNTIME_GID)
        )
        entries.append(
            {
                "logical_name": logical_name,
                "filename": filename,
                "consumer": consumer,
                "uid": uid,
                "gid": gid,
                "mode": "0400",
            }
        )
    return {
        "schema_version": 1,
        "generation_id": generation_id,
        "expected_filenames": sorted([*(_FILES[name][0] for name in _FILES), MANIFEST_NAME]),
        "files": entries,
        "creation_protocol_version": PROTOCOL_VERSION,
    }


def _read_manifest(
    generation: Path, expected_id: str, postgres_uid: int, postgres_gid: int
) -> dict[str, object]:
    path = generation / MANIFEST_NAME
    if path.is_symlink() or not path.is_file():
        raise SecretPreparationError("manifest missing")
    try:
        value = json.loads(path.read_text(encoding="ascii"))
    except (OSError, UnicodeError, ValueError):
        raise SecretPreparationError("manifest invalid") from None
    expected = _manifest(expected_id, postgres_uid, postgres_gid)
    if value != expected:
        raise SecretPreparationError("manifest invalid")
    return value


def _validate_generation_path(generation: Path, postgres_uid: int, postgres_gid: int) -> None:
    if not generation.is_dir() or generation.is_symlink():
        raise SecretPreparationError("generation incomplete")
    generation_info = generation.stat()
    if generation_info.st_uid != 0 or stat.S_IMODE(generation_info.st_mode) != ROOT_MODE:
        raise SecretPreparationError("generation directory ownership or mode is invalid")
    generation_id = generation.name
    _safe_generation_id(generation_id)
    _read_manifest(generation, generation_id, postgres_uid, postgres_gid)
    expected_names = {filename for filename, _ in _FILES.values()} | {MANIFEST_NAME}
    names = {entry.name for entry in generation.iterdir()}
    if names != expected_names:
        raise SecretPreparationError("generation incomplete")
    for logical_name, (filename, _) in _FILES.items():
        path = generation / filename
        if path.is_symlink() or not path.is_file() or not stat.S_ISREG(path.stat().st_mode):
            raise SecretPreparationError("generation incomplete")
        info = path.stat()
        uid, gid = (
            (postgres_uid, postgres_gid)
            if logical_name == "postgres_bootstrap"
            else (RUNTIME_UID, RUNTIME_GID)
        )
        if (info.st_uid, info.st_gid) != (uid, gid):
            raise SecretPreparationError("owner mismatch")
        if stat.S_IMODE(info.st_mode) != MODE:
            raise SecretPreparationError("mode mismatch")
    manifest_info = (generation / MANIFEST_NAME).stat()
    if (manifest_info.st_uid, manifest_info.st_gid) != (0, 0) or stat.S_IMODE(
        manifest_info.st_mode
    ) != 0o600:
        raise SecretPreparationError("manifest invalid")
    first = (generation / _FILES["postgres_bootstrap"][0]).read_bytes()
    second = (generation / _FILES["runtime_bootstrap"][0]).read_bytes()
    if not hmac.compare_digest(first, second):
        raise SecretPreparationError("bootstrap copies do not match")


def validate_generation(
    root: Path, generation_id: str, *, postgres_uid: int, postgres_gid: int
) -> None:
    root = _safe_root(root)
    _validate_generation_path(_generation(root, generation_id), postgres_uid, postgres_gid)


def prepare_generation(
    root: Path, *, postgres_uid: int, postgres_gid: int, generation_id: str | None = None
) -> str:
    root = _safe_root(root)
    sets = root / "sets"
    if sets.is_symlink():
        raise SecretPreparationError("sets directory is invalid")
    sets.mkdir(mode=ROOT_MODE, exist_ok=True)
    if stat.S_IMODE(sets.stat().st_mode) != ROOT_MODE or sets.stat().st_uid != 0:
        raise SecretPreparationError("sets directory ownership or mode is invalid")
    _failpoint("after-sets-directory-creation")
    generation_id = generation_id or f"g-{secrets.token_hex(12)}"
    _safe_generation_id(generation_id)
    generation = _generation(root, generation_id)
    if generation.exists():
        raise SecretPreparationError("generation already exists")
    generation.mkdir(mode=ROOT_MODE)
    try:
        bootstrap = _secret()
        values = {
            "postgres_bootstrap": bootstrap,
            "runtime_bootstrap": bootstrap,
            "application_password": _secret(),
            "migration_password": _secret(),
            "session_signing_key": _secret(),
        }
        for logical_name, (filename, _) in _FILES.items():
            uid, gid = (
                (postgres_uid, postgres_gid)
                if logical_name == "postgres_bootstrap"
                else (RUNTIME_UID, RUNTIME_GID)
            )
            _write_regular(generation / filename, values[logical_name], uid, gid, MODE)
        manifest = json.dumps(
            _manifest(generation_id, postgres_uid, postgres_gid),
            sort_keys=True,
            separators=(",", ":"),
        ).encode("ascii")
        _write_regular(generation / MANIFEST_NAME, manifest, 0, 0, 0o600)
        _failpoint("after-manifest-write")
        _fsync_directory(generation)
        _fsync_directory(sets)
        _failpoint("after-generation-directory-fsync")
        _validate_generation_path(generation, postgres_uid, postgres_gid)
        return generation_id
    except SecretPreparationError:
        raise
    except (OSError, ValueError):
        raise SecretPreparationError("generation preparation failed") from None


def _active_id(root: Path) -> str:
    active = root / "active"
    if not active.is_symlink():
        raise SecretPreparationError("active pointer invalid")
    target = os.readlink(active)
    if target != f"sets/{Path(target).name}" or "/" in Path(target).name or "\\" in target:
        raise SecretPreparationError("active pointer invalid")
    generation_id = target.removeprefix("sets/")
    _safe_generation_id(generation_id)
    _generation(root, generation_id)
    return generation_id


def show_active_safe(root: Path, *, postgres_uid: int, postgres_gid: int) -> dict[str, object]:
    root = _safe_root(root)
    generation_id = _active_id(root)
    validate_generation(root, generation_id, postgres_uid=postgres_uid, postgres_gid=postgres_gid)
    return {"generation_id": generation_id, "target": f"sets/{generation_id}"}


def validate(root: Path, *, postgres_uid: int, postgres_gid: int) -> None:
    """Validate the managed active generation (compatibility convenience API)."""
    root = _safe_root(root)
    validate_generation(
        root, _active_id(root), postgres_uid=postgres_uid, postgres_gid=postgres_gid
    )


def activate_generation(
    root: Path, generation_id: str, *, postgres_uid: int, postgres_gid: int
) -> str | None:
    root = _safe_root(root)
    validate_generation(root, generation_id, postgres_uid=postgres_uid, postgres_gid=postgres_gid)
    previous: str | None = None
    try:
        previous = _active_id(root)
    except SecretPreparationError:
        if (root / "active").exists() or (root / "active").is_symlink():
            raise
    _failpoint("before-temporary-pointer-creation")
    temporary = root / f".active-{secrets.token_hex(8)}"
    os.symlink(f"sets/{generation_id}", temporary)
    try:
        _failpoint("after-temporary-pointer-creation")
        _failpoint("immediately-before-active-pointer-replace")
        os.replace(temporary, root / "active")
        _failpoint("immediately-after-active-pointer-replace")
        _failpoint("before-parent-directory-fsync")
        _fsync_directory(root)
        _failpoint("after-parent-directory-fsync")
    except SecretPreparationError:
        raise
    except (OSError, ValueError):
        raise SecretPreparationError("activation failed") from None
    finally:
        if temporary.is_symlink():
            temporary.unlink()
    return previous


def rollback_activation(
    root: Path, generation_id: str, *, postgres_uid: int, postgres_gid: int
) -> None:
    _failpoint("during-rollback-pointer-replacement")
    activate_generation(root, generation_id, postgres_uid=postgres_uid, postgres_gid=postgres_gid)


def recover(root: Path, *, postgres_uid: int, postgres_gid: int) -> str | None:
    root = _safe_root(root)
    for candidate in root.glob(".active-*"):
        if candidate.is_symlink():
            candidate.unlink()
    try:
        active = _active_id(root)
        validate_generation(root, active, postgres_uid=postgres_uid, postgres_gid=postgres_gid)
        return active
    except SecretPreparationError:
        pass
    valid: list[tuple[int, str]] = []
    sets = root / "sets"
    if sets.is_dir() and not sets.is_symlink():
        for candidate in sets.iterdir():
            try:
                validate_generation(
                    root, candidate.name, postgres_uid=postgres_uid, postgres_gid=postgres_gid
                )
                valid.append((candidate.stat().st_mtime_ns, candidate.name))
            except (SecretPreparationError, OSError):
                if (
                    candidate.is_dir()
                    and not candidate.is_symlink()
                    and GENERATION_RE.fullmatch(candidate.name)
                ):
                    quarantine = sets / f".quarantine-{candidate.name}-{secrets.token_hex(4)}"
                    try:
                        os.replace(candidate, quarantine)
                    except OSError:
                        pass
                continue
        _fsync_directory(sets)
    if not valid:
        raise SecretPreparationError("recovery failed")
    return activate_generation(
        root, max(valid)[1], postgres_uid=postgres_uid, postgres_gid=postgres_gid
    )


def cleanup_retired(
    root: Path, *, keep: Iterable[str], postgres_uid: int, postgres_gid: int
) -> list[str]:
    root = _safe_root(root)
    active = _active_id(root)
    keep_set = set(keep) | {active}
    removed: list[str] = []
    for candidate in (root / "sets").iterdir():
        if candidate.name in keep_set:
            continue
        _failpoint("during-retired-generation-cleanup")
        if candidate.is_symlink() or not candidate.is_dir():
            continue
        try:
            _validate_generation_path(candidate, postgres_uid, postgres_gid)
        except SecretPreparationError:
            continue
        for child in candidate.iterdir():
            child.unlink()
        candidate.rmdir()
        removed.append(candidate.name)
    _fsync_directory(root / "sets")
    return removed


# Compatibility API retained for callers from the accepted RF-08 baseline.  It
# now means prepare and activate a complete generation; it never replaces files.
def prepare(root: Path, *, postgres_uid: int, postgres_gid: int, rotate: bool) -> None:
    root = _safe_root(root)
    if not rotate:
        try:
            _active_id(root)
        except SecretPreparationError:
            pass
        else:
            raise SecretPreparationError("active generation already exists")
    generation_id = prepare_generation(root, postgres_uid=postgres_uid, postgres_gid=postgres_gid)
    activate_generation(root, generation_id, postgres_uid=postgres_uid, postgres_gid=postgres_gid)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "operation",
        choices=(
            "prepare-generation",
            "validate-generation",
            "show-active-safe",
            "activate-generation",
            "rollback-activation",
            "recover",
            "cleanup-retired",
        ),
    )
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--generation-id")
    parser.add_argument("--keep", action="append", default=[])
    parser.add_argument("--postgres-uid", type=int, default=DEFAULT_POSTGRES_UID)
    parser.add_argument("--postgres-gid", type=int, default=DEFAULT_POSTGRES_GID)
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        args = _parser().parse_args(argv)
        common = {"postgres_uid": args.postgres_uid, "postgres_gid": args.postgres_gid}
        if args.operation == "prepare-generation":
            prepare_generation(args.root, **common)
        elif args.operation == "validate-generation":
            if not args.generation_id:
                raise SecretPreparationError("generation identifier required")
            validate_generation(args.root, args.generation_id, **common)
        elif args.operation == "show-active-safe":
            show_active_safe(args.root, **common)
        elif args.operation == "activate-generation":
            if not args.generation_id:
                raise SecretPreparationError("generation identifier required")
            activate_generation(args.root, args.generation_id, **common)
        elif args.operation == "rollback-activation":
            if not args.generation_id:
                raise SecretPreparationError("generation identifier required")
            rollback_activation(args.root, args.generation_id, **common)
        elif args.operation == "recover":
            recover(args.root, **common)
        else:
            cleanup_retired(args.root, keep=args.keep, **common)
        return 0
    except (SecretPreparationError, OSError, ValueError, TypeError):
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
