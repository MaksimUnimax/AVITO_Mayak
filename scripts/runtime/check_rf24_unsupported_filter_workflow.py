"""Semantic workflow contract and deterministic mutation validator."""
# ruff: noqa: E702

from __future__ import annotations

import argparse
from pathlib import Path

REQUIRED = (
    "rf24-unsupported-filter-scenario-01",
    "ubuntu-24.04",
    "python:3.14.6-bookworm",
    "postgres:18-bookworm",
    "set -euo pipefail",
    "uv sync --frozen --all-groups",
    "uv run pytest -q",
    "alembic upgrade head",
    "CREATE DATABASE mayak_rf24_unsupported_filter_",
    "run_rf24_unsupported_filter.py",
    "verify_rf24_unsupported_filter.py",
    "check_rf24_unsupported_filter_artifact_safety.py",
    "build_rf24_unsupported_filter_manifest.py",
    "SYNTHETIC_UNSUPPORTED_FIELD",
    "FIELD_UNSUPPORTED",
    "DRAFT_UNSUPPORTED",
    "SCALAR_FIELD",
    "MAYAK_AVITO_LIVE_ENABLED",
    "MAYAK_API_HOST_PORT",
    "upload-artifact@v4",
)


def validate(text: str) -> list[str]:
    return [token for token in REQUIRED if token not in text]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("workflow", type=Path)
    args = parser.parse_args()
    missing = validate(args.workflow.read_text(encoding="utf-8"))
    if missing:
        print("missing workflow protections: " + ", ".join(missing))
        return 1
    print("RF24 unsupported filter workflow=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
