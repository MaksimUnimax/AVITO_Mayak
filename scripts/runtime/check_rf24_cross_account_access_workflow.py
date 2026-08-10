"""Structural fail-closed validator for hosted RF24 cross-account acceptance."""
# ruff: noqa
from __future__ import annotations
import argparse
from pathlib import Path

RULES = {
 "branch trigger": ("branches: [rf24-cross-account-access-scenario-01]",),
 "exact container": ("python:3.14.6-bookworm",), "exact uv": ("UV_VERSION: 0.11.31", "uv sync --frozen"),
 "bash pipefail": ("set -euo pipefail",), "postgres": ("postgres:18-bookworm",),
 "docker bootstrap": ("docker-29.2.1.tgz", "995b1d0b51e96d551a3b49c552c0170bc6ce9f8b9e0866b8c15bbc67d1cf93a3", "buildx-v0.31.1.linux-amd64", "dc8eaffbf29138123b4874d852522b12303c61246a5073fa0f025e4220317b1e"),
 "docker proof": ("test -S /var/run/docker.sock", "docker version"), "settings proof": ("uv run python", "check_rf24_cross_account_runtime_settings.py", "runtime-settings-preflight=PASS"),
 "full pytest": ("uv run pytest -q --disable-warnings",), "fresh db": ("CREATE DATABASE", "fresh-db-current-shell-binding=PASS", "uv run alembic upgrade head"),
 "head proof": ("exact-head-proof=PASS", "select version_num from mayak.alembic_version"),
 "same db runner": ("FINAL post-suite C0-C10 on NEW database", "run_rf24_cross_account_access.py", "--real-postgres"),
 "safety gates": ("verify_rf24_cross_account_access.py", "check_rf24_cross_account_access_artifact_safety.py", "build_rf24_cross_account_access_manifest.py"),
 "artifact upload": ("actions/upload-artifact@v4", "rf24-cross-account-access"),
 "providers disabled": ("MAYAK_AVITO_LIVE_ENABLED: \"false\"", "MAYAK_TELEGRAM_ENABLED: \"false\"", "MAYAK_MAX_ENABLED: \"false\"", "MAYAK_YOOKASSA_ENABLED: \"false\"", "MAYAK_EGRESS_AGENT_ENABLED: \"false\""),
}

def validate(text: str) -> list[str]:
    errors = [name for name, needles in RULES.items() if not all(n in text for n in needles)]
    order = ["Install pinned Docker CLI and buildx before gates", "Initial database migration and complete repository pytest", "Create NEW post-suite database and migrate from zero", "FINAL post-suite C0-C10 on NEW database"]
    positions = [text.find(item) for item in order]
    if any(p < 0 for p in positions): errors.append("workflow steps missing")
    elif positions != sorted(positions): errors.append("hosted acceptance steps are out of order")
    return errors

def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("workflow", type=Path)
    errors = validate(parser.parse_args().workflow.read_text(encoding="utf-8"))
    if errors: print("\n".join(errors)); return 1
    print("workflow-validator=PASS"); return 0

if __name__ == "__main__": raise SystemExit(main())
