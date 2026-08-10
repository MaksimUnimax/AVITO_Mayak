"""Build a deterministic, source/run-bound artifact manifest."""
# ruff: noqa: E501

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    files = []
    for path in sorted(
        p for p in args.root.iterdir() if p.is_file() and p.name != args.output.name
    ):
        files.append(
            {"basename": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        )
    args.output.write_text(
        json.dumps(
            {
                "technical_id": "RF24-UNSUPPORTED-FILTER-SCENARIO-01",
                "source_sha": args.source_sha,
                "hosted_run_id": args.run_id,
                "files": files,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    print(f"manifest=PASS files={len(files)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
