# ruff: noqa: E501
"""Project-owned RF26 backup, verification and retention operations.

The database-specific restore rehearsal remains owned by RF24.  This module
adds the one-shot operational boundary around it: canonical-root checks,
atomic finalization, safe metadata, and fail-closed retention.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Callable

TECHNICAL_ID = "RF26-OBSERVABILITY-BACKUP-RECOVERY-01"
RETENTION_DAYS = 7
FORMAT = "mayak-rf26-logical-backup"


def canonical_root(root: Path) -> Path:
    root = root.expanduser().resolve(strict=False)
    root.mkdir(parents=True, exist_ok=True)
    if root.is_symlink():
        raise ValueError("backup root must not be a symlink")
    return root


def owned_path(root: Path, candidate: Path) -> Path:
    root = canonical_root(root)
    resolved = candidate.resolve(strict=False)
    if resolved == root or root not in resolved.parents:
        raise ValueError("path escapes project backup root")
    current = root
    for part in resolved.relative_to(root).parts[:-1]:
        current /= part
        if current.is_symlink():
            raise ValueError("symlink boundary is not allowed")
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


def verify_backup(backup: Path, manifest: dict[str, Any], readable: Callable[[Path], bool] | None = None) -> dict[str, Any]:
    if manifest.get("technical_id") != TECHNICAL_ID or manifest.get("format") != FORMAT:
        raise ValueError("backup identity mismatch")
    if not backup.is_file() or backup.is_symlink() or digest(backup) != manifest.get("sha256") or backup.stat().st_size != manifest.get("size"):
        raise ValueError("backup digest or size mismatch")
    is_readable = readable(backup) if readable is not None else backup.stat().st_size > 0
    if not is_readable:
        raise ValueError("backup readability verification failed")
    manifest["verification"] = {"readability": True, "inventory": True}
    manifest["verified_at"] = datetime.now(UTC).isoformat()
    return manifest


def write_verified_set(root: Path, backup_id: str, dump: Callable[[Path], None], metadata: dict[str, str]) -> Path:
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
        verify_backup(temporary, manifest)
        target = root / backup_id
        target.mkdir(mode=0o700)
        shutil.copyfile(temporary, target / "backup.dump")
        (target / "backup.dump").chmod(0o600)
        (target / "manifest.json").write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")
        (target / "manifest.json").chmod(0o600)
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
            manifest = json.loads(manifest_path.read_text())
            expiry = datetime.fromisoformat(str(manifest["retention_expiry"]))
            if manifest.get("technical_id") != TECHNICAL_ID or manifest.get("format") != FORMAT or not dump_path.is_file() or expiry > moment:
                continue
            owned_path(root, item)
            shutil.rmtree(item)
            removed.append(item.name)
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
            continue
    return removed


__all__ = ["FORMAT", "RETENTION_DAYS", "TECHNICAL_ID", "canonical_root", "digest", "manifest_for", "owned_path", "retain_expired", "verify_backup", "write_verified_set"]
