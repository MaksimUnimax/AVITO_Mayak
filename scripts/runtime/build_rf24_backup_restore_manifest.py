"""Build a hash-bound, raw-backup-free RF24 artifact manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.runtime.rf24_backup_restore_core import build_manifest


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--scanner", type=Path, required=True)
    p.add_argument("--source-sha", required=True)
    p.add_argument("--run-id", required=True)
    p.add_argument("paths", type=Path, nargs="+")
    a = p.parse_args()
    s = json.loads(a.scanner.read_text())
    m = build_manifest(a.paths, source_sha=a.source_sha, run_id=a.run_id, scanner=s)
    a.output.write_text(json.dumps(m, sort_keys=True, indent=2) + "\n")


if __name__ == "__main__":
    main()
