#!/usr/bin/env python3
"""Prepare consumer-specific, file-backed runtime secrets safely."""

from __future__ import annotations

import argparse
import base64
import json
import os
import secrets
import stat
from pathlib import Path
from typing import Final

RUNTIME_UID: Final = 10001
RUNTIME_GID: Final = 10001
DEFAULT_POSTGRES_UID: Final = 999
DEFAULT_POSTGRES_GID: Final = 999
MANIFEST_NAME: Final = "manifest.json"
MODE: Final = 0o400
ROOT_MODE: Final = 0o700

_FILES: Final = {
    "postgres_bootstrap": ("mayak_postgres_bootstrap_password_postgres", "postgres"),
    "runtime_bootstrap": ("mayak_postgres_bootstrap_password_runtime", "db-bootstrap"),
    "application_password": ("mayak_database_application_password", "api-worker-scheduler"),
    "migration_password": ("mayak_database_migration_password", "db-bootstrap-migrate"),
    "session_signing_key": ("mayak_session_signing_key", "api"),
}
_ALLOWED_ROOTS: Final = (Path("/opt/avito-mayak-runtime"), Path("/etc/avito-mayak/secrets"))


class SecretPreparationError(Exception):
    """Safe, constant diagnostic exception."""


def _safe_root(root: Path) -> Path:
    root = root.absolute()
    if any(part.is_symlink() for part in (root, *root.parents) if part.exists()):
        raise SecretPreparationError("target root must not contain symlinks")
    root = root.resolve(strict=False)
    if not any(root == allowed or allowed in root.parents for allowed in _ALLOWED_ROOTS):
        raise SecretPreparationError("target root is outside the project-owned secret boundary")
    if root.exists() and root.is_symlink():
        raise SecretPreparationError("target root must not be a symlink")
    root.mkdir(mode=ROOT_MODE, parents=True, exist_ok=True)
    root_stat = root.stat()
    if root_stat.st_uid != 0 or stat.S_IMODE(root_stat.st_mode) != ROOT_MODE:
        raise SecretPreparationError("target root ownership or mode is invalid")
    return root


def _safe_child(root: Path, name: str) -> Path:
    candidate = root / name
    if candidate.parent != root or candidate.name != name or candidate.is_symlink():
        raise SecretPreparationError("secret path rejected")
    return candidate


def _write_secret(path: Path, value: bytes, uid: int, gid: int) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags, MODE)
    try:
        os.fchmod(fd, MODE)
        os.fchown(fd, uid, gid)
        os.write(fd, value)
        os.fsync(fd)
    finally:
        os.close(fd)


def _secret() -> bytes:
    return base64.urlsafe_b64encode(secrets.token_bytes(48))


def _manifest(root: Path, postgres_uid: int, postgres_gid: int) -> dict[str, object]:
    entries = []
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
    return {"format": 1, "directory_mode": "0700", "files": entries}


def prepare(root: Path, *, postgres_uid: int, postgres_gid: int, rotate: bool) -> None:
    root = _safe_root(root)
    paths = [_safe_child(root, item[0]) for item in _FILES.values()]
    manifest_path = _safe_child(root, MANIFEST_NAME)
    if not rotate and any(path.exists() for path in [*paths, manifest_path]):
        raise SecretPreparationError("secret set already exists; use explicit rotation")

    generation = root / f".generation-{secrets.token_hex(12)}"
    generation.mkdir(mode=ROOT_MODE)
    previous: dict[Path, bytes | None] = {}
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
            _write_secret(generation / filename, values[logical_name], uid, gid)
        manifest = json.dumps(
            _manifest(root, postgres_uid, postgres_gid), sort_keys=True, separators=(",", ":")
        ).encode("ascii")
        _write_secret(generation / MANIFEST_NAME, manifest, 0, 0)
        os.chmod(generation / MANIFEST_NAME, 0o600)
        for path in [*paths, manifest_path]:
            if path.exists():
                previous[path] = path.read_bytes()
            os.replace(generation / path.name, path)
            os.chmod(path, 0o600 if path.name == MANIFEST_NAME else MODE)
        fd = os.open(root, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    except Exception as exc:
        for path in paths + [manifest_path]:
            try:
                path.unlink()
            except FileNotFoundError:
                pass
        for path, old in previous.items():
            if old is not None:
                fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, MODE)
                try:
                    os.write(fd, old)
                    os.fchmod(fd, 0o600 if path.name == MANIFEST_NAME else MODE)
                    os.fsync(fd)
                finally:
                    os.close(fd)
        if isinstance(exc, SecretPreparationError):
            raise
        raise SecretPreparationError("secret generation failed") from None
    finally:
        for child in generation.iterdir():
            child.unlink()
        generation.rmdir()


def validate(root: Path, *, postgres_uid: int, postgres_gid: int) -> None:
    root = _safe_root(root)
    expected = _manifest(root, postgres_uid, postgres_gid)["files"]
    if not isinstance(expected, list):
        raise SecretPreparationError("manifest invalid")
    for entry in expected:
        assert isinstance(entry, dict)
        path = _safe_child(root, str(entry["filename"]))
        if not path.is_file() or path.is_symlink():
            raise SecretPreparationError("secret file missing")
        info = path.stat()
        uid = int(entry["uid"])
        gid = int(entry["gid"])
        if info.st_uid != uid or info.st_gid != gid:
            raise SecretPreparationError("secret file ownership is invalid")
        if stat.S_IMODE(info.st_mode) != MODE:
            raise SecretPreparationError("secret file mode is invalid")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--postgres-uid", type=int, default=DEFAULT_POSTGRES_UID)
    parser.add_argument("--postgres-gid", type=int, default=DEFAULT_POSTGRES_GID)
    parser.add_argument("--rotate", action="store_true")
    parser.add_argument("--validate", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        args = _parser().parse_args(argv)
        if args.validate:
            validate(args.root, postgres_uid=args.postgres_uid, postgres_gid=args.postgres_gid)
        else:
            prepare(
                args.root,
                postgres_uid=args.postgres_uid,
                postgres_gid=args.postgres_gid,
                rotate=args.rotate,
            )
        return 0
    except (SecretPreparationError, OSError, ValueError):
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
