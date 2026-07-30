#!/usr/bin/env python3
"""Safe working-tree inventory for RF-08.

The inventory is path- and metadata-only. It does not read file contents.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Final

SCHEMA_VERSION: Final = "rf08-working-tree-inventory-v1"


@dataclass(frozen=True, slots=True)
class InventoryItem:
    path_hash: str
    kind: str
    size: int | None
    staged: bool
    modified: bool
    untracked: bool


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _root_identity(root: Path) -> str:
    return _sha(f"{SCHEMA_VERSION}:{root.resolve()}")


def _git_status(root: Path) -> list[tuple[str, str]]:
    proc = subprocess.run(
        ["git", "-C", str(root), "status", "--porcelain=v1", "--untracked-files=all"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    rows: list[tuple[str, str]] = []
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        status, path = line[:2], line[3:]
        rows.append((status, path))
    return rows


def _item(root: Path, status: str, rel: str) -> InventoryItem:
    path = root / rel
    try:
        st = path.lstat()
        if path.is_symlink():
            kind = "symlink"
            size: int | None = None
        elif path.is_dir():
            kind = "dir"
            size = None
        elif path.is_file():
            kind = "file"
            size = st.st_size
        else:
            kind = "other"
            size = None
    except FileNotFoundError:
        kind = "missing"
        size = None
    return InventoryItem(
        path_hash=_sha(rel),
        kind=kind,
        size=size,
        staged=status[0] not in {" ", "?", "!"},
        modified=status[1] not in {" ", "?", "!"},
        untracked=status == "??",
    )


def inventory(root: Path) -> dict[str, object]:
    root = root.resolve()
    rows = _git_status(root)
    items = sorted(
        (_item(root, status, rel) for status, rel in rows),
        key=lambda item: item.path_hash,
    )
    payload: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "root_safe_identity": _root_identity(root),
        "items": [
            {
                "path_hash": item.path_hash,
                "kind": item.kind,
                "size": item.size,
                "staged": item.staged,
                "modified": item.modified,
                "untracked": item.untracked,
            }
            for item in items
        ],
    }
    payload["digest"] = _sha(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args(argv)
    print(json.dumps(inventory(args.root), sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
