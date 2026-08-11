"""Fail-closed scanner for the safe RF24 recovery upload directory."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.runtime.rf24_backup_restore_core import scan_paths


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--result", type=Path, required=True)
    p.add_argument("--root", type=Path, help="Recursively scan one evidence tree")
    p.add_argument("paths", type=Path, nargs="*")
    a = p.parse_args()
    if a.root is not None:
        if a.paths:
            p.error("--root cannot be combined with positional paths")
        if not a.root.is_dir() or a.root.is_symlink():
            raise SystemExit("scan root is missing or unsafe")
        paths = sorted(
            path for path in a.root.rglob("*") if path.is_file() and not path.is_symlink()
        )
        if not paths:
            raise SystemExit("scan root is empty")
    else:
        if not a.paths:
            p.error("one or more paths are required")
        paths = a.paths
    result = scan_paths(paths)
    a.result.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(1 if result["finding_count"] else 0)


if __name__ == "__main__":
    main()
