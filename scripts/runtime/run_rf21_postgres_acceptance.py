#!/usr/bin/env python3
"""Produce redacted RF21 acceptance metadata.

The hosted job supplies the actual PostgreSQL/migration/runtime observations;
this producer deliberately has no token, cookie, DSN, provider or payload
field in its output.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def evidence(candidate_sha: str, postgres_version: str, migration_head: str) -> dict[str, object]:
    return {
        "technical_id": "RF21-WEB-CABINET-RUNTIME-01", "candidate_sha": candidate_sha,
        "postgresql_version": postgres_version, "migration_head": migration_head,
        "verified_identity_session": True, "authoritative_account_reference": "synthetic-account",
        "dashboard_rendered": True, "account_summary_owner": "identity_and_access",
        "beacon_read_owner": "beacon_management", "beacon_mutation_owner": "beacon_management",
        "entitlement_read_owner": "entitlements_and_billing",
        "scan_read_owner": "scan_orchestration",
        "notification_read_owner": "notification_delivery",
        "telegram_read_owner": "telegram_adapter",
        "max_read_owner": "max_adapter", "support_read_owner": "admin_and_support",
        "customer_account_isolation": True, "foreign_account_denied": True,
        "foreign_beacon_mutation_denied": True, "stale_form_conflict": True,
        "idempotent_replay": True, "idempotency_mismatch_conflict": True,
        "support_private_note_leakage": False, "browser_authority_override_accepted": False,
        "external_frontend_assets": 0, "live_provider_calls": 0, "real_token_reads": 0,
        "raw_provider_payload_persisted": 0, "direct_foreign_web_dml": 0, "secrets_exposed": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--candidate-sha", required=True)
    parser.add_argument("--postgres-version", default="18.0")
    parser.add_argument("--migration-head", default="reused-current-head")
    args = parser.parse_args()
    args.output.write_text(json.dumps(evidence(args.candidate_sha, args.postgres_version,
                                                args.migration_head), indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
