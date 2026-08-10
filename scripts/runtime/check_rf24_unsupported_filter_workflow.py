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
    "uv run pytest -q --disable-warnings",
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
    "check_rf24_cross_account_runtime_settings.py",
    "runtime-settings-preflight=PASS",
    "upload-artifact@v4",
)

GLOBAL_BROAD_SUITE = (
    "MAYAK_PROVIDER_MODE",
    "MAYAK_RUNTIME_PROFILE",
    "MAYAK_RF10_POSTGRES_DSN",
    "MAYAK_RF11_POSTGRES_DSN",
    "RF10_POSTGRES_DSN",
    "RF11_POSTGRES_DSN",
    "RF15_MIGRATION_DSN",
    "RF24_DSN",
)
UNRELATED_ACCEPTANCE = (
    "RF12_ACCEPTANCE_DSN",
    "RF17_MIGRATION_DSN",
    "RF17_APPLICATION_DSN",
    "RF18_MIGRATION_DSN",
    "RF18_DATABASE_URL",
    "RF19_MIGRATION_DSN",
    "RF19_DATABASE_URL",
    "RF20_MIGRATION_DSN",
    "RF20_DATABASE_URL",
    "RF21_MIGRATION_DSN",
    "RF21_DSN",
    "RF22_DSN",
    "RF22_DATABASE_URL",
    "RF22_MIGRATION_DSN",
)


def _section(text: str, start: str, end: str | None = None) -> str:
    begin = text.find(start)
    if begin < 0:
        return ""
    finish = text.find(end, begin + len(start)) if end else -1
    return text[begin:] if finish < 0 else text[begin:finish]


def validate(text: str) -> list[str]:
    errors = [f"missing:{token}" for token in REQUIRED if token not in text]
    h5 = text.find("H5 complete repository pytest")
    h6 = _section(text, "H6 create NEW post-suite database", "H7 exact head")
    h10 = _section(text, "H10 U0-U10 real PostgreSQL scenario", "H11 verifier")
    pre_h5 = text if h5 < 0 else text[:h5]

    if h5 < 0:
        errors.append("missing:H5 boundary")
    if "RF20_POSTGRES_OWNER_LABEL" in text:
        errors.append("fake RF20 owner label is forbidden")
    for name in UNRELATED_ACCEPTANCE:
        if name in pre_h5:
            errors.append(f"unrelated acceptance variable before H5:{name}")
    if any(name not in text for name in GLOBAL_BROAD_SUITE):
        errors.append("accepted common broad-suite bindings missing")
    if not h6:
        errors.append("missing:H6 fresh database section")
    else:
        if "CREATE DATABASE mayak_rf24_unsupported_filter_" not in h6:
            errors.append("H6 does not create DATABASE B")
        if "RF10_POSTGRES_DSN=\"$MAYAK_RF10_POSTGRES_DSN\"" not in h6:
            errors.append("H6 application/migration role binding is not explicit")
        if "RF11_POSTGRES_DSN=\"$MAYAK_RF11_POSTGRES_DSN\"" not in h6:
            errors.append("H6 migration role binding is not explicit")
        if "uv run alembic upgrade head" not in h6:
            errors.append("H6 does not migrate in the current shell")
        if '"$db"' not in h6:
            errors.append("DATABASE B bindings do not target the fresh database")
    if not h10 or 'export RF22_DSN="$MAYAK_RF10_POSTGRES_DSN"' not in h10:
        errors.append("unsupported-specific final scenario binding missing")
    if h10 and 'export RF22_DATABASE_URL="$MAYAK_RF10_POSTGRES_DSN"' not in h10:
        errors.append("RF22_DATABASE_URL is not bound to the DATABASE B application role")
    if h10 and 'export RF22_MIGRATION_DSN="$MAYAK_RF11_POSTGRES_DSN"' not in h10:
        errors.append("RF22_MIGRATION_DSN is not bound to the DATABASE B migration role")
    if "uv run pytest -q --disable-warnings" not in text:
        errors.append("complete repository pytest missing")
    if text.find("H10 U0-U10") < text.find("H5 complete repository pytest"):
        errors.append("H10 precedes successful H5")
    return errors


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
