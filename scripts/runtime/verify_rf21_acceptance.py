#!/usr/bin/env python3
"""Fail-closed verifier for factual RF21 evidence."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

TECHNICAL_ID = "RF21-WEB-CABINET-RUNTIME-01"
REQUIRED_TRUE = (
    "production_composition_exercised", "identity_session_verified",
    "beacon_mutation_persisted_after_reopen", "idempotent_replay",
    "idempotency_mismatch_conflict", "strict_stale_command_conflict",
    "lww_patch_preserved_unrelated_state", "foreign_account_denied",
    "foreign_beacon_read_denied", "foreign_beacon_mutation_denied",
    "notification_account_scope",
)
REQUIRED_FALSE = ("browser_account_override_accepted", "browser_actor_override_accepted",
                  "browser_role_override_accepted")
REQUIRED_ZERO = ("external_frontend_assets", "live_provider_calls",
                 "real_provider_token_reads", "raw_provider_payload_persisted",
                 "direct_foreign_web_dml", "secrets_exposed")
OWNERS = {
    "account_summary_owner": "identity_and_access", "beacon_read_owner": "beacon_management",
    "beacon_mutation_owner": "beacon_management",
    "entitlement_read_owner": "entitlements_and_billing",
    "scan_read_owner": "scan_orchestration", "notification_read_owner": "notification_delivery",
    "telegram_read_owner": "telegram_adapter", "max_read_owner": "max_adapter",
    "support_read_owner": "admin_and_support",
}


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
    for key, owner in OWNERS.items():
        if data.get(key) != owner:
            raise SystemExit(f"invalid owner provenance: {key}")
    for key in REQUIRED_TRUE:
        if data.get(key) is not True:
            raise SystemExit(f"factual assertion failed: {key}")
    for key in REQUIRED_FALSE:
        if data.get(key) is not False:
            raise SystemExit(f"browser authority override accepted: {key}")
    for key in REQUIRED_ZERO:
        if data.get(key) != 0:
            raise SystemExit(f"unsafe observation: {key}")
    provenance = data.get("provenance")
    if not isinstance(provenance, dict) or not provenance.get("database_queries"):
        raise SystemExit("missing factual provenance")
    if data.get("dashboard_beacon_count", 0) < 1:
        raise SystemExit("dashboard Beacon observation required")
    if data.get("support_private_note_leakage") is not False:
        raise SystemExit("support private-note leakage")
    print("RF21 evidence verified")


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
