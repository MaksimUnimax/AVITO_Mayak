"""Static fail-closed checks for the hosted RF24 backup/restore workflow."""

from __future__ import annotations

import argparse
from pathlib import Path

REQUIRED = (
    "postgres:18-bookworm",
    "github.sha",
    "uv sync --frozen",
    "pg_dump",
    "pg_restore",
    "upload-artifact",
    "RF25",
)


def validate(path: Path) -> None:
    text = path.read_text()
    for marker in REQUIRED:
        if marker not in text:
            raise ValueError(f"workflow marker missing: {marker}")
    if "*.dump" in text or "*.backup" in text:
        raise ValueError("raw backup glob in workflow")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("workflow", type=Path)
    a = p.parse_args()
    validate(a.workflow)
