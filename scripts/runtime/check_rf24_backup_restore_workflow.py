# ruff: noqa: E501, I001
"""Semantic, fail-closed validator for the RF24 hosted acceptance workflow."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


BRANCH = "rf24-backup-restore-scenario-01"

RF24_MODULES = (
    "run_rf24_vertical_spine",
    "run_rf24_backup_restore",
    "verify_rf24_backup_restore",
    "check_rf24_backup_restore_artifact_safety",
    "build_rf24_backup_restore_manifest",
    "check_rf24_backup_restore_workflow",
    "check_rf24_backup_restore_ownership",
)


def _step_body(text: str, name: str) -> str:
    pattern = rf"(?ms)^      - name: {re.escape(name)}\n(?P<body>.*?)(?=^      - (?:name:|uses:)|\Z)"
    match = re.search(pattern, text)
    if not match:
        raise ValueError(f"workflow step missing: {name}")
    return match.group("body")


def validate(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    required = (
        "postgres:18-bookworm", "github.sha", "uv sync --frozen --all-groups",
        "pg_dump", "pg_restore", "verify_rf24_backup_restore",
        "check_rf24_backup_restore_artifact_safety",
        "build_rf24_backup_restore_manifest", "upload-artifact", "RF25",
        "run_rf24_vertical_spine", "--seed-evidence",
    )
    missing = [marker for marker in required if marker not in text]
    if missing:
        raise ValueError(f"workflow marker missing: {missing[0]}")
    if not re.search(r"branches:\s*\[\s*rf24-backup-restore-scenario-01\s*\]", text):
        raise ValueError("workflow must push only the RF24 task branch")
    if re.search(r"branches:\s*\[[^\]]*\bmain\b", text):
        raise ValueError("main trigger is forbidden")
    for module in RF24_MODULES:
        invocation = rf"uv run python -m scripts\.runtime\.{module}\b"
        if not re.search(invocation, text):
            raise ValueError(f"module execution missing for {module}")
        if re.search(rf"uv run python scripts/runtime/{module}\.py\b", text):
            raise ValueError(f"direct-file execution forbidden for {module}")
    if not re.search(r"defaults:\s*\n\s+run:\s*\n\s+shell:\s*bash\b", text):
        raise ValueError("job-level Bash authority is missing")
    if "set -euo pipefail" in text and "shell: bash" not in text:
        raise ValueError("pipefail is not backed by Bash")
    if "ref: ${{ github.sha }}" not in text:
        raise ValueError("checkout is not bound to exact candidate SHA")
    if not re.search(r"mapfile -t candidates < <\(docker ps --filter ancestor=postgres:18-bookworm", text):
        raise ValueError("PostgreSQL service discovery is not explicit")
    if 'test "${#candidates[@]}" -eq 1' not in text or "Config.Image" not in text:
        raise ValueError("PostgreSQL service selection is ambiguous")
    tool_binding = re.search(r"RF24_PG_TOOL_PREFIX=docker exec (?P<options>[^%]+)%s", text)
    if not tool_binding or "-i" not in tool_binding.group("options").split():
        raise ValueError("archive-consuming PostgreSQL tool transport is not stdin-attached")
    for variable in (
        "MAYAK_AVITO_LIVE_ENABLED: \"false\"",
        "MAYAK_TELEGRAM_ENABLED: \"false\"",
        "MAYAK_MAX_ENABLED: \"false\"",
        "MAYAK_YOOKASSA_ENABLED: \"false\"",
        "MAYAK_EGRESS_AGENT_ENABLED: \"false\"",
    ):
        if variable not in text:
            raise ValueError(f"provider-disabled environment weakened: {variable}")
    if re.search(r"ports:\s*\n|--publish|--publish-all", text):
        raise ValueError("host-published port is forbidden")
    if not re.search(r"uv run python -m scripts\.runtime\.verify_rf24_backup_restore\b", text):
        raise ValueError("independent verifier execution missing")
    if not re.search(r"uv run python -m scripts\.runtime\.check_rf24_backup_restore_artifact_safety\b", text):
        raise ValueError("artifact scanner execution missing")
    if not re.search(r"uv run python -m scripts\.runtime\.build_rf24_backup_restore_manifest\b", text):
        raise ValueError("manifest execution missing")
    if "H26 executable substrate preflight" not in text or "H26 focused prerequisite gates" not in text:
        raise ValueError("H26 executable preflight is missing")
    preflight = _step_body(text, "H26 executable substrate preflight")
    cross_step = _step_body(text, "H26 cross-step Git trust probe")
    downstream = _step_body(text, "Independent verifier, scanner and manifest")
    persisted_names = (
        "GIT_CONFIG_COUNT",
        "GIT_CONFIG_KEY_0",
        "GIT_CONFIG_VALUE_0",
    )
    if "$GITHUB_ENV" not in preflight:
        raise ValueError("Git trust must be persisted through GITHUB_ENV")
    persistence_end = preflight.index('>> "$GITHUB_ENV"') + len('>> "$GITHUB_ENV"')
    persisted_lines = preflight[:persistence_end]
    required_persistence_lines = (
        "printf '%s\\n' 'GIT_CONFIG_COUNT=1'",
        "printf '%s\\n' 'GIT_CONFIG_KEY_0=safe.directory'",
        "printf 'GIT_CONFIG_VALUE_0=%s\\n' \"$workspace\"",
    )
    if any(line not in persisted_lines for line in required_persistence_lines[:2]):
        raise ValueError("all exact Git trust variables must be persisted")
    if required_persistence_lines[2] not in persisted_lines:
        raise ValueError("exact workspace Git trust value is not persisted")
    if re.search(r"GIT_CONFIG_[A-Z0-9_]+[^\n]*GITHUB_ENV", text):
        persisted_lines = [line for line in text.splitlines() if "GITHUB_ENV" in line and "GIT_CONFIG_" in line]
        if any(not any(name in line for name in persisted_names) for line in persisted_lines):
            raise ValueError("only the exact Git trust variables may be persisted")
    if "workspace=\"$(realpath \"$GITHUB_WORKSPACE\")\"" not in preflight:
        raise ValueError("Git trust workspace must be resolved with realpath")
    cross_pos = text.index("H26 cross-step Git trust probe")
    persistence_pos = text.index("$GITHUB_ENV", text.index("H26 executable substrate preflight"))
    if persistence_pos > cross_pos:
        raise ValueError("Git trust persistence must precede cross-step probe")
    if re.search(r"(?:export\s+|^\s*)GIT_CONFIG_(?:COUNT|KEY_0|VALUE_0)\s*=", cross_step, re.M):
        raise ValueError("cross-step Git probe must not repair trust locally")
    for expected in (
        'test "${GIT_CONFIG_COUNT:-}" = 1',
        'test "${GIT_CONFIG_KEY_0:-}" = safe.directory',
        'test "${GIT_CONFIG_VALUE_0:-}" = "$workspace"',
        'git rev-parse --show-toplevel',
        'git rev-parse HEAD:.github/workflows/ci-rf24-backup-restore.yml',
        'git merge-base --is-ancestor 90a00b12561cecbeac04e3b41c403bcee78f3d71 "$GITHUB_SHA"',
        "h26-cross-step-git-trust=PASS",
    ):
        if expected not in cross_step:
            raise ValueError(f"cross-step Git probe missing: {expected}")
    for expected in (
        'test "${GIT_CONFIG_COUNT:-}" = 1',
        'test "${GIT_CONFIG_KEY_0:-}" = safe.directory',
        'test "${GIT_CONFIG_VALUE_0:-}" = "$workspace"',
        'test "$(git rev-parse HEAD)" = "$GITHUB_SHA"',
    ):
        if expected not in downstream:
            raise ValueError(f"downstream verifier lacks inherited Git trust validation: {expected}")
    if re.search(r"unset\s+GIT_CONFIG_(?:COUNT|KEY_0|VALUE_0)", downstream):
        raise ValueError("downstream verifier must retain inherited Git trust")
    if "GIT_CONFIG_COUNT=1" not in preflight or "GIT_CONFIG_KEY_0=safe.directory" not in preflight:
        raise ValueError("H26 persisted Git trust is missing")
    if "GIT_CONFIG_GLOBAL=/dev/null" in text or "GIT_CONFIG_GLOBAL" in text:
        raise ValueError("H26 must not persist or require GIT_CONFIG_GLOBAL")
    if re.search(r"safe\.directory\s*[=:]\s*['\"]?\*|safe\.directory\s+['\"]\*['\"]", text):
        raise ValueError("wildcard Git trust is forbidden")
    if "git merge-base --is-ancestor" not in text or "git rev-parse HEAD:.github/workflows/ci-rf24-backup-restore.yml" not in text:
        raise ValueError("H26 child-process Git probes are missing")
    if "MAYAK_RF10_POSTGRES_DSN" not in text or "MAYAK_RF11_POSTGRES_PASSWORD_FILE" not in text:
        raise ValueError("H26 RF10/RF11 PostgreSQL contract is missing")
    if "chmod 600" not in text or "trap cleanup EXIT" not in text:
        raise ValueError("H26 password-file cleanup boundary is missing")
    if "docker buildx version" not in text or "docker buildx ls" not in text:
        raise ValueError("H26 Buildx capability preflight is missing")
    if "git config --global" in text:
        raise ValueError("global or wildcard Git trust is forbidden")
    if re.search(r"Server\.Version[^\n]{0,180}(?:=|==)\s*(?:['\"]|\$|Client\.Version)", text):
        raise ValueError("Docker server/client equality is forbidden")
    if "test \"$(docker version --format '{{.Server.Version}}')\" = '29.2.1'" in text:
        raise ValueError("Docker server/client equality is forbidden")
    if "/opt/avito-mayak-runtime" in text:
        raise ValueError("hosted H26 must not depend on server runtime path")
    if "--output \"type=local" not in text or "h26-buildx-local-export=PASS" not in text:
        raise ValueError("real Buildx local-export probe is missing")
    if "RF24_H26_PROBE_DB" not in text:
        raise ValueError("fresh H26 probe database is missing")
    if "${RF24_H26_PROBE_DB}" not in text:
        raise ValueError("H26 probe database DSN is not bound to the task-owned probe")
    if "migration.pgpass" in text or "PGPASSFILE=\"$password_file\"" in text:
        raise ValueError("RF11 raw password file must not be a pgpass file")
    if not re.search(r"printf '%s(?:\\n)?' 'migration-only'", text):
        raise ValueError("RF11 raw password file must contain only the raw password")
    if re.search(r"printf\s+'%s'\s+'[^']*:[^']*:[^']*:[^']*:[^']*'", text):
        raise ValueError("RF11 raw password file must not contain pgpass syntax")
    if "test \"$(wc -l < \"$password_file\")\" = 0" not in text:
        raise ValueError("RF11 raw password file shape is not checked")
    role_block = text[text.index("def role"):text.index("with psycopg.connect", text.index("def role"))]
    if re.search(r"CREATE ROLE[^\n]*%s", role_block):
        raise ValueError("utility DDL uses bind placeholder")
    if "GRANT USAGE ON SCHEMA mayak TO mayak_application" not in text:
        raise ValueError("SOURCE application grant contract missing")
    if re.search(r"TARGET_DB.*alembic upgrade|target_db.*alembic upgrade", text, re.I):
        raise ValueError("TARGET is pre-migrated before clean proof")
    if re.search(r"(?:target|TARGET)[^\n]{0,180}CREATE SCHEMA|CREATE SCHEMA[^\n]{0,180}(?:target|TARGET)", text, re.I):
        raise ValueError("TARGET application schema is created before restore")
    if "if database != target:" not in text:
        raise ValueError("target grants are not phase guarded")
    if re.search(r"docker\s+exec\s+postgres\b", text):
        raise ValueError("ambiguous docker exec postgres binding")
    if not re.search(r"services:\s*\n\s+mayak-postgres:\s*\n", text):
        raise ValueError("canonical PostgreSQL service identity is missing")
    if re.search(r"MAYAK_DATABASE_HOST:\s*postgres\b|@postgres:", text):
        raise ValueError("workflow configures noncanonical PostgreSQL host")
    if re.search(r"host=postgres\b", text):
        raise ValueError("workflow contains split-brain PostgreSQL host authority")
    if re.search(r"postgresql-client|apt-get[^\n]*postgresql", text):
        raise ValueError("unapproved PostgreSQL client stack")
    if "psql " in text or " psql\n" in text:
        raise ValueError("bootstrap must use frozen Psycopg, not psql")
    runner = Path(__file__).with_name("run_rf24_backup_restore.py").read_text(encoding="utf-8")
    if ('"preflight_result": "BLOCKED"' not in runner or '"executed": True' not in runner
            or "restore_preflight" not in runner or "require_clean_target" not in runner
            or "reestablish_application_authority" not in runner
            or '"runtime_read_proof"' not in runner):
        raise ValueError("negative controls lack execution-derived proof")
    if "database_tool_role_args" not in runner or "--username" not in runner:
        raise ValueError("backup/restore database role is implicit")
    if "validate_archive_transport(cmd)" not in runner or "archive.open(\"rb\")" not in runner:
        raise ValueError("archive stdin transport is not fail-closed and binary")
    if "inspect_clean_target" not in runner or "CLEAN_TARGET_PRE_RESTORE" not in runner:
        raise ValueError("clean-target catalog phase is missing")
    if '"beacon_revision_delta": 0' in runner or '"lifecycle_delta": 0' in runner:
        raise ValueError("replay deltas are fabricated constants")
    if '"seeded_state_classes"' in runner or 'RF24_SEED_PROOF' in runner:
        raise ValueError("seed proof must come from the runtime producer")
    if "SELECT version()" not in runner or '"postgres_server_version"' not in runner:
        raise ValueError("server version proof is missing or conflated")
    if re.search(r"CREATE DATABASE[^\n;]*;[^\n]*CREATE DATABASE", text):
        raise ValueError("databases must be created independently")
    if "--backup" not in text or "--source-dsn" not in text or "--target-dsn" not in text:
        raise ValueError("source/target DSN separation missing")
    upload = text.split("actions/upload-artifact", 1)[-1]
    if re.search(r"\.(?:dump|backup|tar|sql(?:\.gz)?)\b", upload, re.I):
        raise ValueError("raw backup upload glob")
    if "RF25" in text and re.search(r"(?:run:|uses:)[^\n]*RF25", text):
        raise ValueError("RF25 execution is forbidden")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("workflow", type=Path)
    args = parser.parse_args()
    validate(args.workflow)
