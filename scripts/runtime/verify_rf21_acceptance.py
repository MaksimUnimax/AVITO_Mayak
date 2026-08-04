#!/usr/bin/env python3
"""Fail-closed verifier for redacted RF21 acceptance evidence."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

REQUIRED_TRUE = (
    "verified_identity_session", "dashboard_rendered", "customer_account_isolation",
    "foreign_account_denied", "foreign_beacon_mutation_denied", "stale_form_conflict",
    "idempotent_replay", "idempotency_mismatch_conflict",
)
REQUIRED_ZERO = ("external_frontend_assets", "live_provider_calls", "real_token_reads",
                 "raw_provider_payload_persisted", "direct_foreign_web_dml", "secrets_exposed")
REQUIRED_OWNERS = ("account_summary_owner", "beacon_read_owner", "beacon_mutation_owner",
                   "entitlement_read_owner", "scan_read_owner", "notification_read_owner",
                   "telegram_read_owner", "max_read_owner", "support_read_owner")


def verify(path: Path, *, expected_sha: str | None = None) -> None:
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError, UnicodeDecodeError) as exc:
        raise SystemExit("malformed RF21 evidence") from exc
    if not isinstance(data, dict) or data.get("technical_id") != "RF21-WEB-CABINET-RUNTIME-01":
        raise SystemExit("wrong Technical ID")
    if expected_sha is not None and data.get("candidate_sha") != expected_sha:
        raise SystemExit("wrong candidate SHA")
    if not re.fullmatch(r"18(?:\.\d+)?", str(data.get("postgresql_version", ""))):
        raise SystemExit("PostgreSQL 18 proof required")
    for name in (*REQUIRED_TRUE, *REQUIRED_OWNERS):
        if name not in data or (name in REQUIRED_TRUE and data[name] is not True) or not data[name]:
            raise SystemExit(f"missing or invalid field: {name}")
    for name in REQUIRED_ZERO:
        if data.get(name) != 0:
            raise SystemExit(f"unsafe field: {name}")
    if not isinstance(data.get("migration_head"), str) or not data["migration_head"]:
        raise SystemExit("migration head required")
    print("RF21 evidence verified")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence", type=Path)
    parser.add_argument("--expected-sha")
    args = parser.parse_args()
    verify(args.evidence, expected_sha=args.expected_sha)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
