# ruff: noqa: E501, I001
"""Semantic, fail-closed validator for the RF24 hosted acceptance workflow."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


BRANCH = "rf24-backup-restore-scenario-01"


def validate(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    required = (
        "postgres:18-bookworm", "github.sha", "uv sync --frozen --all-groups",
        "pg_dump", "pg_restore", "verify_rf24_backup_restore.py",
        "check_rf24_backup_restore_artifact_safety.py",
        "build_rf24_backup_restore_manifest.py", "upload-artifact", "RF25",
    )
    missing = [marker for marker in required if marker not in text]
    if missing:
        raise ValueError(f"workflow marker missing: {missing[0]}")
    if not re.search(r"branches:\s*\[\s*rf24-backup-restore-scenario-01\s*\]", text):
        raise ValueError("workflow must push only the RF24 task branch")
    if re.search(r"branches:\s*\[[^\]]*\bmain\b", text):
        raise ValueError("main trigger is forbidden")
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
    if not re.search(r"uv run python scripts/runtime/verify_rf24_backup_restore\.py\b", text):
        raise ValueError("independent verifier execution missing")
    if not re.search(r"uv run python scripts/runtime/check_rf24_backup_restore_artifact_safety\.py\b", text):
        raise ValueError("artifact scanner execution missing")
    if not re.search(r"uv run python scripts/runtime/build_rf24_backup_restore_manifest\.py\b", text):
        raise ValueError("manifest execution missing")
    if re.search(r"docker\s+exec\s+postgres\b", text):
        raise ValueError("ambiguous docker exec postgres binding")
    if re.search(r"postgresql-client|apt-get[^\n]*postgresql", text):
        raise ValueError("unapproved PostgreSQL client stack")
    if "psql " in text or " psql\n" in text:
        raise ValueError("bootstrap must use frozen Psycopg, not psql")
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
