"""Read-only restore archive check used before any restore mutation."""

from __future__ import annotations

import argparse
from pathlib import Path

from mayak.runtime.backup import verify_archive


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    args = parser.parse_args()
    readable, inventory, version, _ = verify_archive(args.archive)
    if not readable or not inventory:
        raise SystemExit("archive verification failed")
    print(f"postgres_tool={version} readability=true inventory=true")


if __name__ == "__main__":
    main()
