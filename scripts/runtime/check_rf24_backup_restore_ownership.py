"""Static ownership guard for acceptance-only recovery code."""

from __future__ import annotations

import argparse
from pathlib import Path


def validate(paths: list[Path]) -> None:
    for path in paths:
        text = path.read_text()
        if any(
            marker in text
            for marker in ("INSERT INTO mayak.", "UPDATE mayak.", "DELETE FROM mayak.")
        ):
            raise ValueError(f"direct business-table DML: {path.name}")
        if "read_text().strip()" in text and "password" in text.lower():
            raise ValueError(f"secret read in acceptance evidence: {path.name}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("paths", type=Path, nargs="+")
    a = p.parse_args()
    validate(a.paths)
