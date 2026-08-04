#!/usr/bin/env python3
# ruff: noqa: E501
"""Fail-closed verifier for executable RF21 observations."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

TECHNICAL_ID = "RF21-WEB-CABINET-RUNTIME-01-CORRECTIVE-02"
OWNERS = ("identity", "account", "entitlements", "beacon", "scan", "notification", "telegram", "max", "support")


def verify(path: Path, *, expected_sha: str | None = None, root: Path = Path.cwd()) -> None:
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError, UnicodeDecodeError) as exc:
        raise SystemExit("malformed RF21 evidence") from exc
    if not isinstance(data, dict) or data.get("technical_id") != TECHNICAL_ID:
        raise SystemExit("wrong Technical ID")
    if expected_sha is not None and data.get("candidate_sha") != expected_sha:
        raise SystemExit("wrong candidate SHA")
    if not re.fullmatch(r"18(?:\.\d+)+(?:\s.*)?", str(data.get("postgresql_version", ""))):
        raise SystemExit("measured PostgreSQL 18.x proof required")
    heads = ScriptDirectory.from_config(Config(str(root / "alembic.ini"))).get_heads()
    if data.get("migration_head") not in heads:
        raise SystemExit("migration head is not the repository head")
    if data.get("production_scenario_uses_application_role") is not True:
        raise SystemExit("production scenario did not use application role")
    http = data.get("http")
    required_http = ("dashboard_get", "beacon_list_get", "beacon_detail_get", "patch_post", "foreign_get_denied",
                     "foreign_post_denied", "browser_overrides_denied", "replay", "mismatch", "strict_stale")
    if not isinstance(http, dict) or any(http.get(key) is not True for key in required_http):
        raise SystemExit("required Web HTTP observation missing or failed")
    if data.get("persisted") is not True or data.get("lww_preserved") is not True:
        raise SystemExit("mutation persistence/LWW observation failed")
    if int(data.get("dashboard_beacon_count", 0)) < 1:
        raise SystemExit("dashboard Beacon observation required")
    provenance = data.get("provenance")
    if not isinstance(provenance, dict) or not all(provenance.get(key) for key in ("database_queries", "http_requests", "owner_operations")):
        raise SystemExit("missing factual provenance")
    owners = data.get("owner_provenance")
    if not isinstance(owners, dict) or any(owners.get(key) not in {"database_query", "owner_operation", "http_request"} for key in OWNERS):
        raise SystemExit("missing owner-operation provenance")
    assets = data.get("external_asset_scan")
    transport = data.get("provider_transport")
    dml = data.get("direct_web_dml_scan")
    if not isinstance(assets, dict) or assets.get("count") != 0 or assets.get("provenance") != "rendered_html_scan":
        raise SystemExit("external asset scan failed")
    if not isinstance(transport, dict) or transport.get("count") != 0 or transport.get("provenance") != "instrumented_transport_disabled":
        raise SystemExit("provider transport observation failed")
    if not isinstance(dml, dict) or dml.get("found") is not False or dml.get("provenance") != "source_ast_scan":
        raise SystemExit("direct Web DML scan failed")
    security = data.get("security")
    if not isinstance(security, dict) or security.get("artifact_secret_scan", {}).get("result") != "PASS":
        raise SystemExit("artifact semantic safety failed")
    if data.get("support_private_note_leakage") is not False:
        raise SystemExit("support private-note leakage")
    lifecycle = data.get("lifecycle")
    if not isinstance(lifecycle, dict) or any(lifecycle.get(key) is not True for key in (
        "patch", "archive", "delete", "restore", "permanent_delete", "history_reloaded",
    )):
        raise SystemExit("complete Web lifecycle observation required")
    rollback = data.get("rollback")
    if not isinstance(rollback, dict) or any(rollback.get(key) is not True for key in (
        "request_rejected", "state_unchanged_after_reopen", "revision_unchanged_after_reopen",
    )):
        raise SystemExit("database-derived rollback proof required")
    notification = data.get("notification_isolation")
    if not isinstance(notification, dict) or any(notification.get(key) is not True for key in (
        "a_visible", "a_excludes_b", "b_visible", "b_excludes_a",
    )):
        raise SystemExit("two-account Notification isolation proof required")
    print("RF21 executable-provenance evidence verified")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence", type=Path)
    parser.add_argument("--expected-sha")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    verify(args.evidence, expected_sha=args.expected_sha, root=args.repo_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
