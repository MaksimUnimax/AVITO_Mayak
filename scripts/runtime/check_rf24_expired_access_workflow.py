"""Fail-closed executable contract validator for RF24 hosted acceptance."""

from __future__ import annotations

import argparse
import json
import re
import textwrap
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

ENVIRONMENT = {
    "MAYAK_RF10_POSTGRES_DSN": "postgresql+psycopg://mayak_application:application-only@postgres:5432/mayak",
    "MAYAK_RF11_POSTGRES_DSN": "postgresql+psycopg://mayak_migration:migration-only@postgres:5432/mayak",
    "RF10_POSTGRES_DSN": "postgresql+psycopg://mayak_application:application-only@postgres:5432/mayak",
    "RF11_POSTGRES_DSN": "postgresql+psycopg://mayak_migration:migration-only@postgres:5432/mayak",
    "RF15_MIGRATION_DSN": "postgresql+psycopg://mayak_migration:migration-only@postgres:5432/mayak",
    "RF24_DSN": "postgresql+psycopg://mayak_application:application-only@postgres:5432/mayak",
    "MAYAK_RF11_POSTGRES_PASSWORD_FILE": "/run/secrets/mayak_database_migration_password",
    "MAYAK_RF11_POSTGRES_USER": "mayak_migration",
    "MAYAK_RF11_POSTGRES_HOST": "postgres",
    "MAYAK_RF11_POSTGRES_PORT": '"5432"',
    "MAYAK_RF11_POSTGRES_DB": "mayak",
    "MAYAK_SECRETS_DIR": "/run/secrets",
    "DOCKER_HOST": "unix:///var/run/docker.sock",
}

DOCKER_CLI_SHA256 = "995b1d0b51e96d551a3b49c552c0170bc6ce9f8b9e0866b8c15bbc67d1cf93a3"
DOCKER_BUILDX_SHA256 = "dc8eaffbf29138123b4874d852522b12303c61246a5073fa0f025e4220317b1e"


def _runtime_configuration_failures(text: str, positions: dict[str, int]) -> list[str]:
    failures: list[str] = []
    materialize_name = "Materialize and preflight runtime settings"
    materialize = _run_body(text, materialize_name)
    preflight_position = positions.get(materialize_name, -1)
    full_pytest_position = positions.get("Complete repository pytest", -1)
    final = _run_body(text, "FINAL post-suite P0-P8 on NEW database")
    if not materialize:
        return ["runtime-config-materialization-missing", "runtime-settings-preflight-missing"]
    required_materialization = (
        (
            'export MAYAK_ENVIRONMENT_ID="avito-mayak-rf24-expired-${GITHUB_RUN_ID}"',
            "environment-id-materialization-missing",
        ),
        ('MAYAK_SOURCE_SHA="$GITHUB_SHA"', "source-sha-materialization-missing"),
        (
            "MAYAK_LOCK_IDENTITY=\"$(sha256sum uv.lock | cut -d' ' -f1)\"",
            "lock-identity-not-uv-lock-derived",
        ),
        (
            "MAYAK_IMAGE_DIGEST=\"sha256:$(sha256sum Dockerfile | cut -d' ' -f1)\"",
            "image-identity-not-dockerfile-derived",
        ),
        ("MAYAK_PROCESS_KIND=mayak-worker", "process-kind-materialization-missing"),
        ("MAYAK_SYNTHETIC_IDENTITY_ENABLED=true", "synthetic-identity-not-enabled"),
    )
    for marker, finding in required_materialization:
        if marker not in materialize:
            failures.append(finding)
    if 'export MAYAK_ENVIRONMENT_ID="avito-mayak-rf24-expired-${GITHUB_RUN_ID}"' not in text:
        failures.append("environment-id-not-run-scoped")
    if preflight_position < 0:
        failures.append("runtime-settings-preflight-missing")
    elif full_pytest_position >= 0 and (
        preflight_position > full_pytest_position
        or text.find("      - name: " + materialize_name)
        > text.find("      - name: Complete repository pytest")
    ):
        failures.append("runtime-settings-preflight-after-full-pytest")
    if "uv run python - <<'PY'" not in materialize:
        failures.append("runtime-settings-preflight-not-uv-project-python")
    legacy_clear = (
        "unset MAYAK_RF10_POSTGRES_DSN MAYAK_RF11_POSTGRES_DSN "
        "MAYAK_RF11_POSTGRES_PASSWORD_FILE MAYAK_RF11_POSTGRES_USER "
        "MAYAK_RF11_POSTGRES_HOST MAYAK_RF11_POSTGRES_PORT MAYAK_RF11_POSTGRES_DB"
    )
    if legacy_clear not in materialize or legacy_clear not in final:
        failures.append("runtime-settings-legacy-env-not-cleared")
    if (
        "load_runtime_settings()" not in materialize
        and "compose_runtime_settings(" not in materialize
    ):
        failures.append("runtime-settings-preflight-not-actual-composition")
    for marker, finding in (
        (
            'settings.runtime.profile.value == "synthetic_acceptance"',
            "preflight-profile-proof-missing",
        ),
        (
            'settings.build.source_sha == os.environ["GITHUB_SHA"]',
            "preflight-source-sha-proof-missing",
        ),
        (
            'settings.build.environment_id == f"avito-mayak-rf24-expired-',
            "preflight-environment-proof-missing",
        ),
        ("settings.build.lock_identity == hashlib.sha256", "preflight-lock-proof-missing"),
        (
            'settings.build.image_digest == "sha256:" + hashlib.sha256',
            "preflight-image-proof-missing",
        ),
        (
            'settings.runtime.process_kind.value == "mayak-worker"',
            "preflight-process-kind-proof-missing",
        ),
        (
            "settings.session.synthetic_identity_enabled is True",
            "preflight-synthetic-proof-missing",
        ),
        ("settings.providers.egress_agent_enabled is False", "preflight-provider-proof-missing"),
    ):
        if marker not in materialize:
            failures.append(finding)
    if not final or "final-runtime-config-proof=PASS" not in final:
        failures.append("final-p0-config-identity-proof-missing")
    if final and "load_runtime_settings()" not in final:
        failures.append("final-p0-config-settings-proof-missing")
    if (
        'MAYAK_SYNTHETIC_IDENTITY_ENABLED: "false"' in text
        or "MAYAK_SYNTHETIC_IDENTITY_ENABLED=false" in materialize
    ):
        failures.append("final-p0-synthetic-identity-disabled")
    for marker, finding in (
        ('MAYAK_AVITO_LIVE_ENABLED: "false"', "live-avito-enabled"),
        ('MAYAK_TELEGRAM_ENABLED: "false"', "live-telegram-enabled"),
        ('MAYAK_MAX_ENABLED: "false"', "live-max-enabled"),
        ('MAYAK_YOOKASSA_ENABLED: "false"', "live-yookassa-enabled"),
        ('MAYAK_EGRESS_AGENT_ENABLED: "false"', "live-egress-agent-enabled"),
    ):
        if marker not in text:
            failures.append(finding)
    return failures


def _run_body(text: str, name: str) -> str:
    match = re.search(
        rf"^      - name: {re.escape(name)}\n"
        rf"(?:        .*\n|\n)*?"
        rf"        run: \|\n(?P<body>(?:          .*\n|\n)*)",
        text,
        re.M,
    )
    return textwrap.dedent(match.group("body")) if match else ""


def _heredocs(body: str) -> tuple[list[int], list[int]]:
    lines = body.splitlines()
    openings = [i for i, line in enumerate(lines) if line == "python - <<'PY'"]
    terminators = [i for i, line in enumerate(lines) if line == "PY"]
    return openings, terminators


PROJECT_DEPENDENCY_IMPORT = re.compile(
    r"^\s*(?:from\s+(?:mayak|alembic|sqlalchemy)(?:\.|\s)|import\s+"
    r"(?:mayak|alembic|sqlalchemy)(?:\.|\s|$))"
)


def _python_provenance_failures(text: str) -> list[str]:
    """Reject dependency-bearing Python unless it is run by the uv project."""
    failures: list[str] = []
    lines = text.splitlines()
    step_name = "<workflow>"
    index = 0
    while index < len(lines):
        line = lines[index]
        step_match = re.match(r"^      - name: (.+)$", line)
        if step_match:
            step_name = step_match.group(1)
        stripped = line.strip()
        invocation = re.match(r"^(?P<command>(?:uv run )?python) - <<'PY'$", stripped)
        if invocation:
            command = invocation.group("command")
            body: list[str] = []
            end = index + 1
            while end < len(lines) and lines[end].strip() != "PY":
                body.append(lines[end])
                end += 1
            if any(PROJECT_DEPENDENCY_IMPORT.search(body_line) for body_line in body):
                if command != "uv run python":
                    failures.append(f"project-dependency-python-not-uv-managed:{step_name}")
            index = end
        elif re.search(r"(?<!uv run )\bpython\s+scripts/runtime/", stripped):
            failures.append(f"project-dependency-python-not-uv-managed:{step_name}")
        index += 1
    return failures


def _step_positions(text: str) -> dict[str, int]:
    names = re.findall(r"^      - name: (.+)$", text, re.M)
    return {name: i for i, name in enumerate(names)}


def _fresh_step_failures(text: str) -> list[str]:
    body = _run_body(text, "Create NEW post-suite database and migrate from zero")
    if not body:
        return ["fresh-step-missing"]
    failures: list[str] = []
    create = body.find("CREATE DATABASE")
    schema = body.find("CREATE SCHEMA mayak")
    binding = body.find('export MAYAK_DATABASE_NAME="$db"')
    migration_binding = body.find('export RF15_MIGRATION_DSN="')
    scenario_binding = body.find('export RF24_DSN="')
    proof = body.find('urlsplit(os.environ[key]).path.lstrip("/")')
    upgrade = body.find("uv run alembic upgrade head")
    head_proof = body.find("ScriptDirectory.from_config")
    head_import = body.find("from alembic.config import Config")
    grants = body.find("GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES")
    if not re.search(r'db="[^"]*\$\{GITHUB_RUN_ID\}', body):
        failures.append("fresh-db-name-not-run-id-derived")
    if create < 0:
        failures.append("fresh-db-create-missing")
    if schema < 0 or (create >= 0 and schema < create):
        failures.append("fresh-schema-not-created-after-database")
    if binding < 0 or 'test "$MAYAK_DATABASE_NAME" = "$db"' not in body:
        failures.append("fresh-current-shell-mayak-database-export-missing")
    if migration_binding < 0 or (upgrade >= 0 and migration_binding > upgrade):
        failures.append("fresh-current-shell-rf15-export-before-upgrade-missing")
    if scenario_binding < 0 or (upgrade >= 0 and scenario_binding > upgrade):
        failures.append("fresh-current-shell-rf24-export-before-upgrade-missing")
    if not re.search(r'export RF15_MIGRATION_DSN="[^"\n]*\$\{db\}', body):
        failures.append("fresh-rf15-target-not-db-variable")
    if not re.search(r'export RF24_DSN="[^"\n]*\$\{db\}', body):
        failures.append("fresh-rf24-target-not-db-variable")
    if proof < 0 or (upgrade >= 0 and proof > upgrade):
        failures.append("fresh-current-shell-target-proof-before-upgrade-missing")
    if any(
        marker not in body
        for marker in (
            "MAYAK_DATABASE_NAME=%s",
            "RF15_MIGRATION_DSN=%s",
            "RF24_DSN=%s",
        )
    ):
        failures.append("fresh-github-env-persistence-missing")
    if "alembic downgrade base" in body:
        failures.append("fresh-step-downgrade-forbidden")
    if upgrade < 0:
        failures.append("fresh-direct-upgrade-head-missing")
    if (
        head_proof < 0
        or "get_heads()" not in body
        or "SELECT version_num FROM mayak.alembic_version" not in body
        or "observed == expected" not in body
        or (upgrade >= 0 and head_proof < upgrade)
    ):
        failures.append("fresh-exact-head-proof-order-invalid")
    if head_import >= 0:
        lines = body.splitlines()
        import_line = next(
            (
                index
                for index, line in enumerate(lines)
                if "from alembic.config import Config" in line
            ),
            -1,
        )
        invocation = next(
            (
                line.strip()
                for line in reversed(lines[:import_line])
                if line.strip().endswith("python - <<'PY'")
            ),
            "",
        )
        if not invocation.startswith("uv run python - <<'PY'"):
            failures.append("fresh-exact-head-proof-not-uv-project-python")
    if grants < 0 or (head_proof >= 0 and grants < head_proof):
        failures.append("fresh-application-grants-before-head-proof")
    final = _run_body(text, "FINAL post-suite P0-P8 on NEW database")
    if not final or 'urlsplit(os.environ["RF24_DSN"]).path.lstrip("/") == db' not in final:
        failures.append("final-p0-p8-fresh-db-proof-missing")
    return failures


def validate(text: str, branch: str = "rf24-expired-access-scenario-01") -> list[str]:
    failures = [item for item in REQUIRED if item not in text]
    failures.extend(_python_provenance_failures(text))
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
    failures.extend(_runtime_configuration_failures(text, positions))
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
    failures.extend(_fresh_step_failures(text))
    if 'MAYAK_AVITO_LIVE_ENABLED: "false"' not in text:
        failures.append("live-provider-enable")
    if "actions/setup-python@v5" in text:
        failures.append("setup-python-inside-python-container")
    python_proof = _run_body(text, "Prove container-native Python authority")
    uv_recheck = _run_body(text, "Re-check container-native Python after uv setup")
    docker_body = _run_body(text, "Install hosted Docker CLI and buildx")
    docker_step = text.find("Install hosted Docker CLI and buildx")
    for body, label in ((python_proof, "initial"), (uv_recheck, "after-uv")):
        if (
            "command -v python" not in body
            or 'test "$python_path" = /usr/local/bin/python' not in body
        ):
            failures.append(f"container-python-path-not-enforced:{label}")
        if "/__t/" not in body or "hostedtoolcache" not in body:
            failures.append(f"host-toolcache-python-not-rejected:{label}")
        if 'test "$(python --version 2>&1)" = "Python 3.14.6"' not in body:
            failures.append(f"wrong-or-missing-python-version:{label}")
    if not docker_body:
        failures.append("missing-docker-installation-body")
    else:
        openings, terminators = _heredocs(docker_body)
        if len(openings) != 2:
            failures.append("docker-heredoc-count")
        if len(terminators) != 2 or any(
            not any(end > start for end in terminators) for start in openings
        ):
            failures.append("docker-heredoc-terminator")
        if "docker version" not in docker_body or "docker buildx version" not in docker_body:
            failures.append("docker-proof-inside-unclosed-heredoc")
        if 'test "$(command -v python)" = /usr/local/bin/python' not in docker_body:
            failures.append("docker-before-python-authority-proof")
        if text.find("Re-check container-native Python after uv setup") > docker_step:
            failures.append("docker-before-python-authority-proof")
        if 'test "$(command -v docker)" = /usr/local/bin/docker' not in docker_body:
            failures.append("docker-cli-path-not-enforced")
        if "29.2.1" not in docker_body or DOCKER_CLI_SHA256 not in docker_body:
            failures.append("docker-cli-version-or-digest")
        if "v0.31.1" not in docker_body or DOCKER_BUILDX_SHA256 not in docker_body:
            failures.append("buildx-version-or-digest")
    full_pytest = text.find("Complete repository pytest")
    if docker_step < 0:
        failures.append("missing-docker-installation")
    elif full_pytest >= 0 and docker_step > full_pytest:
        failures.append("docker-install-after-full-pytest")
    for key, value in ENVIRONMENT.items():
        if f"{key}: {value}" not in text:
            failures.append(f"missing-environment:{key}")
    if "docker-29.2.1.tgz" not in text or DOCKER_CLI_SHA256 not in text:
        failures.append("docker-cli-unpinned-or-wrong-digest")
    if "buildx-v0.31.1.linux-amd64" not in text or DOCKER_BUILDX_SHA256 not in text:
        failures.append("buildx-unpinned-or-wrong-digest")
    if not re.search(r"(?m)^\s+docker version\s*$", text):
        failures.append("missing-docker-version-proof")
    if not re.search(r"(?m)^\s+docker buildx version\s+\|\s+grep -F 'v0\.31\.1'\s*$", text):
        failures.append("missing-buildx-version-proof")
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
