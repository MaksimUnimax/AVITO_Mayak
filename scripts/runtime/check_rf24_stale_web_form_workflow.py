"""Fail-closed executable contract validator for stale-Web hosted acceptance."""

# ruff: noqa: E501

from __future__ import annotations

import argparse
import re
from pathlib import Path

RULES: dict[str, tuple[str, ...]] = {
    "exact branch trigger": ("branches: [rf24-stale-web-form-scenario-01]",),
    "exact checkout": ("actions/checkout@v4", "ref: ${{ github.sha }}"),
    "Bash with pipefail": ("shell: bash", "set -euo pipefail"),
    "uv project interpreter": ("uv run python", "uv sync --frozen --all-groups"),
    "real PostgreSQL": ("postgres:18-bookworm", "--real-postgres"),
    "actual server-rendered Web GET": ("GET /cabinet", "build_web_router"),
    "expected row version extraction": ("expected_row_version", "server-rendered"),
    "concurrent owner mutation": ("concurrent", "BeaconManagementRuntime.patch"),
    "N to N+1": ("N+1", "version_after"),
    "actual stale HTTP POST": ("client.post", "stale_expected_row_version"),
    "required HTTP 409": ("status_code != 409", "stale_http_status"),
    "owner conflict provenance": ("ConflictError", "WebConflictError"),
    "zero stale effects": ("stale_revision_delta", "stale_work_delta", "stale_provider_call_delta"),
    "fresh reload": ("fresh_rendered", "rendered_version"),
    "fresh submission": ("fresh_response", "fresh_value_authoritative_after_fresh_submission"),
    "N+1 to N+2": ("final_version", "N+2"),
    "exact-one fresh revision": ("final_fresh_revision_delta", "== 1"),
    "Docker CLI pinned install": (
        "Install pinned Docker CLI and buildx before gates",
        "docker-29.2.1.tgz",
        "995b1d0b51e96d551a3b49c552c0170bc6ce9f8b9e0866b8c15bbc67d1cf93a3",
        "/usr/local/bin/docker",
    ),
    "buildx pinned install": (
        "buildx-v0.31.1.linux-amd64",
        "dc8eaffbf29138123b4874d852522b12303c61246a5073fa0f025e4220317b1e",
        "/usr/libexec/docker/cli-plugins/docker-buildx",
    ),
    "Docker socket and functional proof": (
        "DOCKER_HOST=unix:///var/run/docker.sock",
        "test -S /var/run/docker.sock",
        "docker version",
        "docker buildx version | grep -F 'v0.31.1'",
    ),
    "actual runtime settings preflight": (
        "Hosted substrate preflight",
        "uv run python - <<'PY'",
        "from mayak.runtime.settings import load_runtime_settings",
        "runtime-settings-preflight=PASS",
        "unset MAYAK_RF10_POSTGRES_DSN MAYAK_RF11_POSTGRES_DSN",
    ),
    "runtime identity contract": (
        "export MAYAK_ENVIRONMENT_ID=\"avito-mayak-rf24-stale-web-${GITHUB_RUN_ID}\"",
        "export MAYAK_LOCK_IDENTITY=\"$(sha256sum uv.lock",
        "export MAYAK_IMAGE_DIGEST=\"sha256:$(sha256sum Dockerfile",
        "MAYAK_PROCESS_KIND=mayak-worker",
        "MAYAK_SYNTHETIC_IDENTITY_ENABLED=true",
    ),
    "full repository pytest": ("uv run pytest -q --disable-warnings",),
    "fresh post-suite database": (
        "Create NEW post-suite database and migrate from zero",
        "CREATE DATABASE",
        "CREATE SCHEMA mayak",
        'export MAYAK_DATABASE_NAME="$db"',
        'export RF15_MIGRATION_DSN=',
        'export RF24_DSN=',
        "fresh-db-current-shell-binding=PASS",
        "uv run alembic upgrade head",
    ),
    "same-new-db exact head": (
        "exact-head-proof=PASS",
        "ScriptDirectory",
        'os.environ["RF15_MIGRATION_DSN"]',
        "select version_num from mayak.alembic_version",
    ),
    "final config and DB identity proof": (
        "FINAL post-suite S0-S8 on NEW database",
        "load_runtime_settings()",
        "final-runtime-config-proof=PASS",
        'os.environ["RF24_DSN"]',
        "unset MAYAK_RF10_POSTGRES_DSN MAYAK_RF11_POSTGRES_DSN",
    ),
    "scenario before acceptance artifacts": (
        "run_rf24_stale_web_form.py --real-postgres",
        "verify_rf24_stale_web_form.py",
        "check_rf24_stale_web_form_artifact_safety.py",
        "build_rf24_stale_web_form_manifest.py",
    ),
    "provider disablement": (
        'MAYAK_AVITO_LIVE_ENABLED: "false"',
        'MAYAK_TELEGRAM_ENABLED: "false"',
        'MAYAK_MAX_ENABLED: "false"',
        'MAYAK_YOOKASSA_ENABLED: "false"',
        'MAYAK_EGRESS_AGENT_ENABLED: "false"',
    ),
    "artifact upload": ("actions/upload-artifact@v4",),
}


def _steps(text: str) -> dict[str, int]:
    return {name: index for index, name in enumerate(re.findall(r"^      - name: (.+)$", text, re.M))}


def _body(text: str, name: str) -> str:
    match = re.search(
        rf"^      - name: {re.escape(name)}\n(?:        .*\n|\n)*?        run: \|\n(?P<body>(?:          .*\n|\n)*)",
        text,
        re.M,
    )
    return match.group("body") if match else ""


def validate(text: str) -> list[str]:
    missing = [name for name, needles in RULES.items() if any(needle not in text for needle in needles)]
    steps = _steps(text)
    full = steps.get("Initial database migration and complete repository pytest", -1)
    docker = steps.get("Install pinned Docker CLI and buildx before gates", -1)
    substrate = steps.get("Hosted substrate preflight", -1)
    fresh = steps.get("Create NEW post-suite database and migrate from zero", -1)
    final = steps.get("FINAL post-suite S0-S8 on NEW database", -1)
    artifacts = steps.get("Verify scanner manifest hash chain", -1)
    if docker < 0 or (full >= 0 and docker > full):
        missing.append("Docker install must precede complete repository pytest")
    if substrate < 0 or (full >= 0 and substrate > full):
        missing.append("runtime-settings preflight must precede complete repository pytest")
    fresh_body = _body(text, "Create NEW post-suite database and migrate from zero")
    for marker, finding in (
        ('export MAYAK_DATABASE_NAME="$db"', "fresh database name must be current-shell exported"),
        ('export RF15_MIGRATION_DSN=', "fresh migration DSN must be current-shell exported"),
        ('export RF24_DSN=', "fresh RF24 DSN must be current-shell exported"),
        ("fresh-db-current-shell-binding=PASS", "fresh DB identity must be proven before migration"),
    ):
        if marker not in fresh_body:
            missing.append(finding)
    migration = fresh_body.find("uv run alembic upgrade head")
    proof = fresh_body.find("exact-head-proof=PASS")
    binding = fresh_body.find("fresh-db-current-shell-binding=PASS")
    if migration < 0 or binding < 0 or migration < binding:
        missing.append("fresh migration must follow current-shell DB binding proof")
    if proof < 0 or (migration >= 0 and proof < migration):
        missing.append("exact-head proof must follow fresh migration")
    if re.search(r"RF15_MIGRATION_DSN=.*(?:/mayak(?:\"|[' ]|$))", fresh_body):
        missing.append("fresh migration DSN must not target initial mayak database")
    if "create_engine(\"postgresql+psycopg://mayak_migration:migration-only@postgres:5432/mayak\")" in fresh_body:
        missing.append("exact-head proof must not target initial mayak database")
    if final < 0 or fresh < 0 or final < fresh:
        missing.append("final S0-S8 must follow fresh migration and exact-head proof")
    if artifacts >= 0 and final >= 0 and artifacts < final:
        missing.append("verifier/scanner/manifest must follow real S0-S8")
    scenario_pos = text.find("run_rf24_stale_web_form.py --real-postgres")
    for marker, finding in (
        ("verify_rf24_stale_web_form.py", "verifier must follow real S0-S8"),
        ("check_rf24_stale_web_form_artifact_safety.py", "scanner must follow real S0-S8"),
        ("build_rf24_stale_web_form_manifest.py", "manifest must follow real S0-S8"),
    ):
        if scenario_pos >= 0 and text.find(marker) < scenario_pos:
            missing.append(finding)
    if "if: always()" in text and "rf24-stale-web-form-full-pytest-diagnostic" in text:
        # The diagnostic upload is explicitly non-acceptance evidence; final upload is later.
        final_upload = text.rfind("name: rf24-stale-web-form")
        diagnostic_upload = text.find("name: rf24-stale-web-form-full-pytest-diagnostic")
        if final_upload < diagnostic_upload:
            missing.append("acceptance artifact upload must remain after verifier/scanner/manifest")
    return list(dict.fromkeys(missing))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("workflow", type=Path)
    args = parser.parse_args()
    missing = validate(args.workflow.read_text(encoding="utf-8"))
    if missing:
        print("missing workflow contracts: " + ", ".join(missing))
        return 1
    print("rf24-stale-web-form workflow=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
