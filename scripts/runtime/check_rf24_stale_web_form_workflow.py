"""Structural, fail-closed validator for hosted stale-Web acceptance."""

from __future__ import annotations

import argparse
from pathlib import Path

RULES = {
    "exact branch trigger": ("branches: [rf24-stale-web-form-scenario-01]",),
    "exact checkout": ("actions/checkout@v4", "ref: ${{ github.sha }}"),
    "Bash": ("shell: bash", "set -euo pipefail"),
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
    "verifier": ("verify_rf24_stale_web_form.py",),
    "artifact scanner": ("check_rf24_stale_web_form_artifact_safety.py",),
    "manifest/hash chain": ("build_rf24_stale_web_form_manifest.py", "sha256"),
    "artifact upload": ("actions/upload-artifact@v4",),
    "provider disablement": ("avito_live_enabled", "telegram_enabled", "max_enabled"),
    "full repository pytest": ("uv run pytest -q --disable-warnings",),
    "evidence after scenario": (
        "run_rf24_stale_web_form.py --real-postgres",
        "verify_rf24_stale_web_form.py",
    ),
}


def validate(text: str) -> list[str]:
    return [
        name for name, needles in RULES.items() if any(needle not in text for needle in needles)
    ]


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
