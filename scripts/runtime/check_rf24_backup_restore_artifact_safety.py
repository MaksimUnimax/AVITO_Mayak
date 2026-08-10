"""Fail-closed scanner for the safe RF24 recovery upload directory."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.runtime.rf24_backup_restore_core import scan_paths


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--result", type=Path, required=True)
    p.add_argument("paths", type=Path, nargs="+")
    a = p.parse_args()
    result = scan_paths(a.paths)
    a.result.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(1 if result["finding_count"] else 0)


if __name__ == "__main__":
    main()
