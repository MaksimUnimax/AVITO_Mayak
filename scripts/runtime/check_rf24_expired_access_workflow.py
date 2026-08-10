"""Fail-closed executable contract validator for RF24 hosted acceptance."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

REQUIRED = (
    "runs-on: ubuntu-24.04",
    "python:3.14.6-bookworm",
    "defaults:\n      run:\n        shell: bash",
    "actions/checkout@v4",
    "ref: ${{ github.sha }}",
    "fetch-depth: 0",
    'test "$(git rev-parse HEAD)" = "$GITHUB_SHA"',
    "command -v bash",
    "bash -c 'set -euo pipefail",
    "postgres:18-bookworm@sha256:1961f96e6029a02c3812d7cb329a3b03a3ac2bb067058dec17b0f5596aca9296",
    "/run/secrets/mayak_database_migration_password",
    "/run/secrets/mayak_database_application_password",
    "/run/secrets/mayak_session_signing_key",
    "test -s /run/secrets/",
    "mayak_migration",
    "mayak_application",
    "alembic downgrade base",
    "alembic upgrade head",
    "uv run pytest -q --disable-warnings 2>&1 | tee rf24-expired-access-full-pytest.log",
    "CREATE DATABASE",
    "FINAL post-suite P0-P8",
    "verify_rf24_expired_access.py",
    "check_rf24_expired_access_artifact_safety.py",
    "build_rf24_expired_access_manifest.py",
    "actions/upload-artifact@v4",
)


def _step_positions(text: str) -> dict[str, int]:
    names = re.findall(r"^      - name: (.+)$", text, re.M)
    return {name: i for i, name in enumerate(names)}


def validate(text: str, branch: str = "rf24-expired-access-scenario-01") -> list[str]:
    failures = [item for item in REQUIRED if item not in text]
    if f"branches: [{branch}]" not in text:
        failures.append("branch-trigger")
    if "branches: [main" in text or "ref: rf24-expired-access-scenario-01" in text:
        failures.append("movable-or-main-checkout")
    if "safe.directory=*" in text or "safe.directory '*'" in text or "safe.directory= *" in text:
        failures.append("safe-directory-wildcard")
    if "--publish" in text or "ports:" in text:
        failures.append("postgres-host-port")
    secret_paths = {
        "migration_password": "/run/secrets/mayak_database_migration_password",
        "application_password": "/run/secrets/mayak_database_application_password",
        "session_signing_key": "/run/secrets/mayak_session_signing_key",
    }
    for secret, path in secret_paths.items():
        if f"test -s {path}" not in text:
            failures.append(f"empty-{secret}")
    if "printf '%s\\n' migration-only" not in text or "migration-only@postgres" not in text:
        failures.append("role-secret-mismatch-migration")
    if "CREATE ROLE mayak_migration LOGIN PASSWORD 'migration-only'" not in text:
        failures.append("role-secret-mismatch-migration")
    if "ALTER ROLE mayak_migration CREATEDB" not in text:
        failures.append("fresh-database-owner-capability")
    if "CREATE ROLE mayak_application LOGIN PASSWORD 'application-only'" not in text:
        failures.append("role-secret-mismatch-application")
    positions = _step_positions(text)
    ordered = (
        "Sync dependencies",
        "Prepare non-empty acceptance secrets and PostgreSQL roles",
        "Initial migration zero to head",
        "Focused, one-to-one, ownership and workflow gates",
        "Static base-vs-candidate delta",
        "Complete repository pytest",
        "Create NEW post-suite database and migrate from zero",
        "FINAL post-suite P0-P8 on NEW database",
        "Verifier scanner manifest hash chain",
    )
    if any(name not in positions for name in ordered):
        failures.append("missing-semantic-step")
    else:
        for left, right in zip(ordered, ordered[1:]):
            if positions[left] >= positions[right]:
                failures.append(f"ordering:{left}>{right}")
    if "set -euo pipefail\n          uv run pytest -q --disable-warnings 2>&1 | tee" not in text:
        failures.append("pytest-pipeline-not-fail-closed")
    if "FINAL post-suite P0-P8" in text and text.index("FINAL post-suite P0-P8") < text.index(
        "Complete repository pytest"
    ):
        failures.append("final-before-full-pytest")
    if "rm -f rf24-expired-access-evidence.json" not in text:
        failures.append("pre-suite-evidence-reused")
    if "MAYAK_DATABASE_NAME=%s" not in text or "GITHUB_RUN_ID" not in text:
        failures.append("fresh-post-suite-db-binding")
    if 'MAYAK_AVITO_LIVE_ENABLED: "false"' not in text:
        failures.append("live-provider-enable")
    return sorted(set(failures))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("workflow", type=Path)
    parser.add_argument("--branch", default="rf24-expired-access-scenario-01")
    args = parser.parse_args(argv)
    failures = validate(args.workflow.read_text(encoding="utf-8"), args.branch)
    print(
        json.dumps(
            {
                "status": "PASS" if not failures else "FAIL",
                "finding_count": len(failures),
                "findings": failures,
            },
            sort_keys=True,
        )
    )
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
