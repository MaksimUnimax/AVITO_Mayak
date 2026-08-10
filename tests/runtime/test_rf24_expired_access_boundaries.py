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
    ("case_id", "needle"),
    [
        ("missing-rf10-dsn", "MAYAK_RF10_POSTGRES_DSN:"),
        ("missing-rf11-dsn", "MAYAK_RF11_POSTGRES_DSN:"),
        ("missing-rf11-password-file", "MAYAK_RF11_POSTGRES_PASSWORD_FILE:"),
        ("wrong-rf11-password-file", "/run/secrets/mayak_database_migration_password"),
        ("missing-rf11-host", "MAYAK_RF11_POSTGRES_HOST:"),
        ("missing-rf11-db", "MAYAK_RF11_POSTGRES_DB:"),
        ("missing-rf15-dsn", "RF15_MIGRATION_DSN:"),
        ("missing-secrets-dir", "MAYAK_SECRETS_DIR:"),
        ("missing-docker-host", "DOCKER_HOST:"),
        ("missing-docker-install", "Install hosted Docker CLI and buildx"),
        ("unpinned-docker-cli", "docker-29.2.1.tgz"),
        (
            "wrong-docker-cli-sha",
            "995b1d0b51e96d551a3b49c552c0170bc6ce9f8b9e0866b8c15bbc67d1cf93a3",
        ),
        ("missing-buildx-install", "buildx-v0.31.1.linux-amd64"),
        ("unpinned-buildx", "v0.31.1"),
        (
            "wrong-buildx-sha",
            "dc8eaffbf29138123b4874d852522b12303c61246a5073fa0f025e4220317b1e",
        ),
        ("missing-docker-version-proof", "docker version"),
        ("missing-buildx-version-proof", "docker buildx version"),
    ],
)
def test_workflow_environment_and_docker_negative_cases_execute_actual_validator(
    case_id: str, needle: str
) -> None:
    workflow = Path(".github/workflows/ci-rf24-expired-access.yml").read_text(encoding="utf-8")
    if case_id == "wrong-rf11-password-file":
        mutated = workflow.replace(needle, "/run/secrets/wrong")
    elif case_id in {"wrong-docker-cli-sha", "wrong-buildx-sha"}:
        mutated = workflow.replace(needle, "0" * 64)
    elif case_id == "missing-docker-version-proof":
        mutated = workflow.replace("docker version", "docker version-disabled")
    elif case_id == "missing-buildx-version-proof":
        mutated = workflow.replace("docker buildx version", "docker buildx version-disabled")
    else:
        mutated = workflow.replace(needle, "")
    assert validate(mutated), case_id


@pytest.mark.parametrize(
    ("case_id", "mutate"),
    [
        (
            "setup-python-inside-python-container",
            lambda w: w.replace(
                "actions/checkout@v4",
                "actions/setup-python@v5\n      - uses: actions/checkout@v4",
            ),
        ),
        (
            "container-python-path-not-enforced",
            lambda w: w.replace(
                'test "$python_path" = /usr/local/bin/python', "printf path-only"
            ),
        ),
        (
            "host-toolcache-python-accepted",
            lambda w: w.replace(
                'test "$python_path" = /usr/local/bin/python',
                "test \"$python_path\" = /__t/Python/3.14.6/x64",
            ),
        ),
        ("wrong-python-version", lambda w: w.replace('Python 3.14.6', 'Python 3.14.5')),
        (
            "docker-before-python-authority-proof",
            lambda w: w.replace(
                'test "$(command -v python)" = /usr/local/bin/python', "true"
            ),
        ),
        (
            "docker-cli-heredoc-unclosed",
            lambda w: w.replace("          PY\n          install -d", "          install -d", 1),
        ),
        (
            "buildx-heredoc-unclosed",
            lambda w: w.replace(
                '          PY\n          test "$(command -v docker)"',
                '          test "$(command -v docker)"',
                1,
            ),
        ),
        (
            "docker-proof-inside-unclosed-heredoc",
            lambda w: w.replace("          docker version\n", "          # docker version\n"),
        ),
        (
            "docker-cli-path-not-enforced",
            lambda w: w.replace(
                'test "$(command -v docker)" = /usr/local/bin/docker', "true"
            ),
        ),
        (
            "docker-install-after-full-pytest",
            lambda w: w.replace(
                "      - name: Install hosted Docker CLI and buildx",
                "      - name: Complete repository pytest\n"
                "        run: true\n"
                "      - name: Install hosted Docker CLI and buildx",
            ),
        ),
    ],
)
def test_workflow_new_root_cause_negative_cases(case_id: str, mutate) -> None:
    workflow = Path(".github/workflows/ci-rf24-expired-access.yml").read_text(encoding="utf-8")
    assert validate(mutate(workflow)), case_id


@pytest.mark.parametrize(
    ("case_id", "mutate", "finding"),
    [
        (
            "env-only-binding",
            lambda w: w.replace('export MAYAK_DATABASE_NAME="$db"\n', ""),
            "fresh-current-shell-mayak-database-export-missing",
        ),
        (
            "rf15-old-database",
            lambda w: w.replace(
                '${db}"\n          export RF24_DSN', 'mayak"\n          export RF24_DSN'
            ),
            "fresh-rf15-target-not-db-variable",
        ),
        (
            "rf24-old-database",
            lambda w: w.replace(
                'export RF24_DSN="postgresql+psycopg://mayak_application:application-only@postgres:5432/${db}"',
                'export RF24_DSN="postgresql+psycopg://mayak_application:application-only@postgres:5432/mayak"',
                1,
            ),
            "fresh-rf24-target-not-db-variable",
        ),
        (
            "export-after-upgrade",
            lambda w: w.replace(
                '          export RF24_DSN="postgresql+psycopg://mayak_application:application-only@postgres:5432/${db}"\n',
                '          uv run alembic upgrade head\n'
                '          export RF24_DSN="postgresql+psycopg://mayak_application:application-only@postgres:5432/${db}"\n',
                1,
            ),
            "fresh-current-shell-rf24-export-before-upgrade-missing",
        ),
        (
            "fresh-downgrade",
            lambda w: w.replace(
                "          uv run alembic upgrade head\n          uv run python - <<'PY'",
                "          uv run alembic downgrade base\n"
                "          uv run alembic upgrade head\n          uv run python - <<'PY",
                1,
            ),
            "fresh-step-downgrade-forbidden",
        ),
        (
            "missing-head-proof",
            lambda w: w.replace(
                'expected = ScriptDirectory.from_config(Config("alembic.ini")).get_heads()',
                "expected = []",
            ),
            "fresh-exact-head-proof-order-invalid",
        ),
        (
            "head-proof-before-upgrade",
            lambda w: w.replace(
                '          printf \'RF24_DSN=%s\\n\' "$RF24_DSN" >> "$GITHUB_ENV"\n'
                "          uv run alembic upgrade head\n",
                '          printf \'RF24_DSN=%s\\n\' "$RF24_DSN" >> "$GITHUB_ENV"\n',
                1,
            ).replace(
                "          assert observed == expected, \"fresh database is not exactly at "
                "migration head\"\n",
                "          assert observed == expected, \"fresh database is not exactly at "
                "migration head\"\n"
                "          uv run alembic upgrade head\n",
                1,
            ),
            "fresh-exact-head-proof-order-invalid",
        ),
        (
            "missing-current-shell-proof",
            lambda w: w.replace(
                '              target = urlsplit(os.environ[key]).path.lstrip("/")\n',
                "",
                1,
            ),
            "fresh-current-shell-target-proof-before-upgrade-missing",
        ),
        (
            "final-not-bound",
            lambda w: w.replace(
                '          assert urlsplit(os.environ["RF24_DSN"]).path.lstrip("/") == db\n',
                "",
            ),
            "final-p0-p8-fresh-db-proof-missing",
        ),
        (
            "missing-env-persistence",
            lambda w: w.replace(
                "          printf 'RF24_DSN=%s\\n' \"$RF24_DSN\" >> \"$GITHUB_ENV\"\n",
                "",
            ),
            "fresh-github-env-persistence-missing",
        ),
    ],
)
def test_fresh_database_mutations_have_specific_findings(
    case_id: str, mutate, finding: str
) -> None:
    workflow = Path(".github/workflows/ci-rf24-expired-access.yml").read_text(encoding="utf-8")
    findings = validate(mutate(workflow))
    assert finding in findings, (case_id, findings)


def test_exact_head_proof_plain_python_fails_closed() -> None:
    workflow = Path(".github/workflows/ci-rf24-expired-access.yml").read_text(encoding="utf-8")
    mutated = workflow.replace(
        "          uv run python - <<'PY'\n"
        "          import os\n"
        "          from alembic.config import Config",
        "          python - <<'PY'\n"
        "          import os\n"
        "          from alembic.config import Config",
        1,
    )
    assert validate(mutated) == ["fresh-exact-head-proof-not-uv-project-python"]


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
