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
    pytest = re.search(r"Complete repository pytest once(?P<body>.*?)(?=\n\s*- name:|\Z)", text, re.S)
    if not pytest or "pytest" not in pytest.group("body"):
        raise ValueError("complete repository pytest step missing")
    if "pipefail" not in pytest.group("body") or "tee" not in pytest.group("body"):
        raise ValueError("complete pytest output must preserve exit status")
    if "ref: ${{ github.sha }}" not in text:
        raise ValueError("checkout is not bound to exact candidate SHA")
    if not re.search(r"mapfile -t candidates < <\(docker ps --filter ancestor=postgres:18-bookworm", text):
        raise ValueError("PostgreSQL service discovery is not explicit")
    if 'test "${#candidates[@]}" -eq 1' not in text or "Config.Image" not in text:
        raise ValueError("PostgreSQL service selection is ambiguous")
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
    scenario = text.index("Scenario-specific PG18 gate passed before broad suite")
    broad = text.index("Complete repository pytest once")
    if scenario > broad:
        raise ValueError("broad pytest precedes scenario-specific PG18 gate")
    role_block = text[text.index("def role"):text.index("with psycopg.connect", text.index("def role"))]
    if re.search(r"CREATE ROLE[^\n]*%s", role_block):
        raise ValueError("utility DDL uses bind placeholder")
    if "GRANT USAGE ON SCHEMA mayak TO mayak_application" not in text:
        raise ValueError("SOURCE application grant contract missing")
    if re.search(r"TARGET_DB.*alembic upgrade|target_db.*alembic upgrade", text, re.I):
        raise ValueError("TARGET is pre-migrated before clean proof")
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
    if '"seeded_state_classes"' in runner or 'RF24_SEED_PROOF' in runner:
        raise ValueError("seed proof must come from the runtime producer")
    if "SELECT version()" not in runner or '"postgres_server_version"' not in runner:
        raise ValueError("server version proof is missing or conflated")
    if re.search(r"CREATE DATABASE[^\n;]*;[^\n]*CREATE DATABASE", text):
        raise ValueError("databases must be created independently")
    if "--backup" not in text or "--source-dsn" not in text or "--target-dsn" not in text:
        raise ValueError("source/target DSN separation missing")
    upload = text.split("actions/upload-artifact", 1)[-1]
    if re.search(r"\*\.(dump|backup|tar|sql(?:\.gz)?)\b", upload, re.I):
        raise ValueError("raw backup upload glob")
    if "RF25" in text and re.search(r"(?:run:|uses:)[^\n]*RF25", text):
        raise ValueError("RF25 execution is forbidden")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("workflow", type=Path)
    args = parser.parse_args()
    validate(args.workflow)
