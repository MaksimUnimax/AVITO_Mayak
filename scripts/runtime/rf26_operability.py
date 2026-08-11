# ruff: noqa: E501
"""Project-owned RF26 backup, verification and retention operations.

The database-specific restore rehearsal remains owned by RF24.  This module
adds the one-shot operational boundary around it: canonical-root checks,
atomic finalization, safe metadata, and fail-closed retention.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Callable

TECHNICAL_ID = "RF26-OBSERVABILITY-BACKUP-RECOVERY-01"
RETENTION_DAYS = 7
FORMAT = "mayak-rf26-logical-backup"
_MANIFEST_KEYS = {"technical_id", "format", "backup_id", "environment_id", "source_sha", "migration_revision", "postgres_tool_identity", "created_at", "logical_format", "size", "sha256", "verification", "verified_at", "retention_expiry"}


def _absolute_without_resolution(path: Path) -> Path:
    return path.expanduser() if path.is_absolute() else Path.cwd() / path


def canonical_root(root: Path) -> Path:
    """Return the project root only after checking every existing component."""
    candidate = _absolute_without_resolution(root)
    current = Path(candidate.anchor)
    for part in candidate.parts[1:]:
        current /= part
        if current.exists() and current.is_symlink():
            raise ValueError("backup root path must not cross a symlink")
    resolved = candidate.resolve(strict=False)
    resolved.mkdir(parents=True, exist_ok=True)
    if resolved.is_symlink():
        raise ValueError("backup root must not be a symlink")
    return resolved


def owned_path(root: Path, candidate: Path) -> Path:
    root = canonical_root(root)
    raw = _absolute_without_resolution(candidate)
    if raw == root:
        raise ValueError("root itself is not an owned set")
    relative = raw.relative_to(root) if raw.is_relative_to(root) else None
    if relative is None:
        raise ValueError("path escapes project backup root")
    current = root
    for part in relative.parts:
        current /= part
        if current.exists() and current.is_symlink():
            raise ValueError("symlink boundary is not allowed")
    resolved = raw.resolve(strict=False)
    if resolved == root or root not in resolved.parents:
        raise ValueError("path escapes project backup root")
    return resolved


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def manifest_for(backup: Path, *, environment_id: str, source_sha: str, migration_revision: str, tool_identity: str, now: datetime | None = None) -> dict[str, Any]:
    if not backup.is_file() or backup.is_symlink():
        raise ValueError("backup artifact is not a regular file")
    created = now or datetime.now(UTC)
    return {"technical_id": TECHNICAL_ID, "format": FORMAT, "backup_id": backup.stem, "environment_id": environment_id, "source_sha": source_sha, "migration_revision": migration_revision, "postgres_tool_identity": tool_identity, "created_at": created.isoformat(), "logical_format": "custom", "size": backup.stat().st_size, "sha256": digest(backup), "verification": {"readability": False, "inventory": False}, "retention_expiry": (created + timedelta(days=RETENTION_DAYS)).isoformat()}


def verify_backup(
    backup: Path,
    manifest: dict[str, Any],
    readable: Callable[[Path], bool] | None = None,
    inventory: Callable[[Path], bool] | None = None,
) -> dict[str, Any]:
    if manifest.get("technical_id") != TECHNICAL_ID or manifest.get("format") != FORMAT:
        raise ValueError("backup identity mismatch")
    if not backup.is_file() or backup.is_symlink() or digest(backup) != manifest.get("sha256") or backup.stat().st_size != manifest.get("size"):
        raise ValueError("backup digest or size mismatch")
    if readable is None or inventory is None:
        raise ValueError("PostgreSQL archive verifier is required")
    is_readable = readable(backup)
    has_inventory = inventory(backup)
    if not is_readable or not has_inventory:
        raise ValueError("backup readability verification failed")
    manifest["verification"] = {"readability": True, "inventory": True, "verifier": "pg_restore"}
    manifest["verified_at"] = datetime.now(UTC).isoformat()
    return manifest


def write_verified_set(
    root: Path,
    backup_id: str,
    dump: Callable[[Path], None],
    metadata: dict[str, str],
    *,
    readable: Callable[[Path], bool],
    inventory: Callable[[Path], bool],
) -> Path:
    root = canonical_root(root)
    if not backup_id or "/" in backup_id or "\\" in backup_id or backup_id.startswith("."):
        raise ValueError("unsafe backup identity")
    final = owned_path(root, root / backup_id)
    if final.exists():
        raise FileExistsError("backup identity already exists")
    with tempfile.TemporaryDirectory(prefix=".rf26-", dir=root) as temp:
        temporary = Path(temp) / f"{backup_id}.dump"
        dump(temporary)
        temporary.chmod(0o600)
        manifest = manifest_for(temporary, environment_id=metadata["environment_id"], source_sha=metadata["source_sha"], migration_revision=metadata["migration_revision"], tool_identity=metadata["tool_identity"])
        verify_backup(temporary, manifest, readable, inventory)
        target = root / backup_id
        staging = Path(tempfile.mkdtemp(prefix=f".{backup_id}.", dir=root))
        try:
            staging.chmod(0o700)
            shutil.copyfile(temporary, staging / "backup.dump")
            (staging / "backup.dump").chmod(0o600)
            (staging / "manifest.json").write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8")
            (staging / "manifest.json").chmod(0o600)
            for child in (staging / "backup.dump", staging / "manifest.json"):
                with child.open("rb") as stream:
                    os.fsync(stream.fileno())
            os.replace(staging, target)
            os.chmod(target, 0o700)
        except Exception:
            shutil.rmtree(staging, ignore_errors=True)
            raise
    return target


def retain_expired(root: Path, *, now: datetime | None = None, active_ids: frozenset[str] = frozenset()) -> list[str]:
    root = canonical_root(root)
    moment = now or datetime.now(UTC)
    removed: list[str] = []
    for item in root.iterdir():
        if item.is_symlink() or not item.is_dir() or item.name in active_ids:
            continue
        manifest_path = item / "manifest.json"
        dump_path = item / "backup.dump"
        try:
            owned_path(root, item)
            if set(item.iterdir()) != {manifest_path, dump_path}:
                continue
            manifest = json.loads(manifest_path.read_text())
            expiry = datetime.fromisoformat(str(manifest["retention_expiry"]))
            created = datetime.fromisoformat(str(manifest["created_at"]))
            if (set(manifest) - _MANIFEST_KEYS or created.tzinfo is None or expiry.tzinfo is None or expiry != created + timedelta(days=RETENTION_DAYS) or manifest.get("technical_id") != TECHNICAL_ID or manifest.get("format") != FORMAT or manifest.get("backup_id") != item.name or manifest.get("logical_format") != "custom" or not isinstance(manifest.get("source_sha"), str) or len(manifest["source_sha"]) != 40 or any(char not in "0123456789abcdef" for char in manifest["source_sha"]) or not isinstance(manifest.get("postgres_tool_identity"), str) or not manifest["postgres_tool_identity"].startswith("pg_") or manifest.get("verification", {}).get("readability") is not True or manifest.get("verification", {}).get("inventory") is not True or not dump_path.is_file() or dump_path.is_symlink() or digest(dump_path) != manifest.get("sha256") or dump_path.stat().st_size != manifest.get("size") or expiry > moment):
                continue
            shutil.rmtree(item)
            removed.append(item.name)
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
            continue
    return removed


__all__ = ["FORMAT", "RETENTION_DAYS", "TECHNICAL_ID", "canonical_root", "digest", "manifest_for", "owned_path", "retain_expired", "verify_backup", "write_verified_set"]
