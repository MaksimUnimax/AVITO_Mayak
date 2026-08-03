#!/usr/bin/env python3
"""Independent fail-closed checker for RF18 primitive evidence."""

# ruff: noqa: E501, E701, I001

from __future__ import annotations

import json
import sys
from pathlib import Path


REQUIRED = {
    "technical_id", "candidate_sha", "m09_table_names", "m09_table_count", "inbound", "concurrency",
    "identity", "foreign_writes", "notification_lifecycle_mutations_by_adapter", "webhook",
    "long_polling", "fake_provider", "httpx_mocked", "readiness", "live_network_call_count",
    "real_secret_read_count", "raw_provider_payload_persisted_count", "secret_scan", "changed_paths",
}


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: verify_rf18_acceptance.py ARTIFACT", file=sys.stderr)
        return 2
    try:
        data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return 2
    if not isinstance(data, dict) or not REQUIRED.issubset(data) or data.get("technical_id") != "RF-18-TELEGRAM-ADAPTER-RUNTIME-20260803-01":
        return 2
    if data.get("m09_table_names") != ["telegram_inbound_updates", "telegram_identity_mappings", "telegram_delivery_mappings"] or data.get("m09_table_count") != 3:
        return 2
    zero_fields = ("foreign_writes", "notification_lifecycle_mutations_by_adapter", "live_network_call_count", "real_secret_read_count", "raw_provider_payload_persisted_count")
    if any(data.get(field) != 0 for field in zero_fields): return 2
    if data["fake_provider"].get("blind_retries") != 0 or data["httpx_mocked"].get("automatic_retries") != 0: return 2
    if data["readiness"].get("public_ingress_deployed") != 0: return 2
    inbound = data.get("inbound", {})
    if not all(inbound.get(field) is True for field in ("first_accept", "same_replay", "conflicting_replay", "rollback_rows_unchanged")): return 2
    if inbound.get("raw_payload_persisted") != 0: return 2
    for key in ("same_same", "same_different"):
        if inbound.get(key, {}).get("rows") != 1: return 2
    if not data.get("identity", {}).get("mapping") or not data.get("identity", {}).get("replay"): return 2
    if not data.get("delivery", {}).get("mapping") or not data.get("delivery", {}).get("replay") or not data.get("delivery", {}).get("conflict"): return 2
    if not data.get("inbound", {}).get("foreign_write_denied") or not data.get("inbound", {}).get("notification_write_denied"): return 2
    print("RF18 primitive evidence verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
