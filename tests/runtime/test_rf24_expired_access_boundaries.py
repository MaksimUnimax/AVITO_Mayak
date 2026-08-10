from __future__ import annotations

from pathlib import Path

import pytest

from scripts.runtime.check_rf24_expired_access_artifact_safety import scan
from scripts.runtime.check_rf24_expired_access_ownership import violations
from scripts.runtime.check_rf24_expired_access_static_delta import delta
from scripts.runtime.check_rf24_expired_access_workflow import validate


def test_scanner_negative_cases_execute_one_to_one(tmp_path: Path) -> None:
    for case_id, payload in (
        ("authorization", "Authorization: Bearer secret"),
        ("password", "password=secret"),
        ("private-key", "-----BEGIN OPENSSH PRIVATE KEY-----"),
        ("provider-body", "raw_provider_payload"),
    ):
        path = tmp_path / case_id
        path.write_text(payload, encoding="utf-8")
        assert scan([path]) > 0, case_id


@pytest.mark.parametrize(
    ("source", "reason"),
    [
        ("from mayak.modules.beacon_management import runtime", "foreign import"),
        (
            "session.execute(text('UPDATE mayak.beacon_beacons SET state=\\'FROZEN\\''))",
            "foreign DML",
        ),
    ],
)
def test_ownership_negative_cases_execute_one_to_one(
    tmp_path: Path, source: str, reason: str
) -> None:
    path = tmp_path / "src/mayak/modules/scan_orchestration/bad.py"
    path.parent.mkdir(parents=True)
    path.write_text(source, encoding="utf-8")
    assert violations(tmp_path), reason


def test_workflow_valid_fixture_and_independent_mutations() -> None:
    workflow = Path(".github/workflows/ci-rf24-expired-access.yml").read_text(encoding="utf-8")
    assert validate(workflow) == []
    for needle in (
        "ref: ${{ github.sha }}",
        "alembic upgrade head",
        "verify_rf24_expired_access.py",
        "upload-artifact",
    ):
        assert validate(workflow.replace(needle, "")), needle


@pytest.mark.parametrize(
    ("case_id", "needle"),
    [
        ("container-default-sh", "shell: bash"),
        ("missing-head-assertion", 'test "$(git rev-parse HEAD)" = "$GITHUB_SHA"'),
        ("wildcard-safe-directory", 'git config --global --add safe.directory "$GITHUB_WORKSPACE"'),
        ("empty-migration-secret", "test -s /run/secrets/mayak_database_migration_password"),
        ("empty-application-secret", "test -s /run/secrets/mayak_database_application_password"),
        ("empty-session-secret", "test -s /run/secrets/mayak_session_signing_key"),
        ("missing-alembic", "uv run alembic upgrade head"),
        (
            "unpinned-postgres",
            "postgres:18-bookworm@sha256:1961f96e6029a02c3812d7cb329a3b03a3ac2bb067058dec17b0f5596aca9296",
        ),
        ("host-port", "services:\n      postgres:"),
        ("live-provider", 'MAYAK_AVITO_LIVE_ENABLED: "false"'),
        (
            "non-fail-closed-pytest",
            "set -euo pipefail\n          uv run pytest -q --disable-warnings 2>&1 | tee",
        ),
        ("fresh-db", "CREATE DATABASE"),
        ("post-suite-migration", "Create NEW post-suite database and migrate from zero"),
        ("final-p0-p8", "FINAL post-suite P0-P8 on NEW database"),
        ("verifier-pre-suite-evidence", "rm -f rf24-expired-access-evidence.json"),
        ("missing-scanner", "check_rf24_expired_access_artifact_safety.py"),
        ("missing-manifest", "build_rf24_expired_access_manifest.py"),
        ("missing-artifact-upload", "actions/upload-artifact@v4"),
        ("main-trigger", "branches: [rf24-expired-access-scenario-01]"),
    ],
)
def test_workflow_negative_cases_execute_actual_validator(case_id: str, needle: str) -> None:
    workflow = Path(".github/workflows/ci-rf24-expired-access.yml").read_text(encoding="utf-8")
    if case_id == "container-default-sh":
        mutated = workflow.replace("shell: bash", "shell: sh")
    elif case_id == "wildcard-safe-directory":
        mutated = workflow.replace(needle, "git config --global --add safe.directory '*'")
    elif case_id == "host-port":
        mutated = workflow.replace(needle, needle + "\n        ports: [5432:5432]")
    elif case_id == "main-trigger":
        mutated = workflow.replace(needle, "branches: [main]")
    else:
        mutated = workflow.replace(needle, "")
    assert validate(mutated), case_id


@pytest.mark.parametrize(
    ("base", "candidate", "changed", "accepted"),
    [
        (
            [{"path": "a.py", "code": "E1", "line": "1", "message": "old"}],
            [{"path": "a.py", "code": "E1", "line": "1", "message": "old"}],
            set(),
            True,
        ),
        ([{"path": "a.py", "code": "E1", "line": "1", "message": "old"}], [], set(), True),
        ([], [{"path": "a.py", "code": "E1", "line": "1", "message": "new"}], set(), False),
        ([], [{"path": "a.py", "code": "E1", "line": "1", "message": "new"}], {"a.py"}, False),
    ],
)
def test_static_delta_cases_execute(base, candidate, changed, accepted) -> None:
    assert delta(base, candidate, changed)["accepted"] is accepted
