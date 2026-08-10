"""Fail-closed structural validator for the RF24 hosted acceptance workflow."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REQUIRED = (
    "runs-on: ubuntu-24.04",
    "python:3.14.6",
    "0.11.31",
    "postgres:18-bookworm@sha256:",
    "ref: ${{ github.sha }}",
    "fetch-depth: 0",
    "git rev-parse HEAD",
    "GITHUB_SHA",
    "rf24-expired-access-scenario-01",
    "alembic upgrade head",
    "mayak_migration",
    "mayak_application",
    "/run/secrets/",
    "MAYAK_AVITO_LIVE_ENABLED",
    "MAYAK_TELEGRAM_ENABLED",
    "MAYAK_MAX_ENABLED",
    "MAYAK_YOOKASSA_ENABLED",
    "check_rf24_expired_access_ownership.py",
    "check_rf24_expired_access_artifact_safety.py",
    "build_rf24_expired_access_manifest.py",
    "upload-artifact",
    "run_rf24_expired_access.py",
    "verify_rf24_expired_access.py",
    "pytest --collect-only",
    "lint-imports",
    "full-pytest",
    "fresh-post-suite",
    "delta",
)
FORBIDDEN = (
    "branches: [main",
    "ref: rf24-expired-access-scenario-01",
    "postgres:18-bookworm\n",
    "ruff check src tests scripts\n",
    "mypy src\n",
)


def validate(text: str, branch: str = "rf24-expired-access-scenario-01") -> list[str]:
    failures = [item for item in REQUIRED if item not in text]
    if branch not in text:
        failures.append("branch-trigger")
    failures.extend(item for item in FORBIDDEN if item in text)
    return sorted(set(failures))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("workflow", type=Path)
    parser.add_argument("--branch", default="rf24-expired-access-scenario-01")
    args = parser.parse_args(argv)
    failures = validate(args.workflow.read_text(encoding="utf-8"), args.branch)
    result = {
        "status": "PASS" if not failures else "FAIL",
        "finding_count": len(failures),
        "findings": failures,
    }
    print(json.dumps(result, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
