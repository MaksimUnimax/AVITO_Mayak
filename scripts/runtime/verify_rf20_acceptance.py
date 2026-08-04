"""Fail-closed verifier for RF20 semantic acceptance evidence."""

# ruff: noqa: E501

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        return 2
    try:
        data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return 2
    required = {
        "technical_id",
        "candidate_sha",
        "postgresql_version",
        "migration_head",
        "support_counts",
        "foreign_write_denied",
        "live_provider_calls",
        "real_token_reads",
        "raw_provider_payload_persisted",
        "host_postgres_published",
        "delegations",
        "port_calls",
        "foreign_target_denials",
        "ambiguous_replay_preserved",
        "adapter_signature_evidence",
        "audit_metadata",
        "note_body_in_event_details",
        "event_timestamps_aware",
        "correlation_count",
        "causation_count",
        "host_postgres_publication_proof",
    }
    if (
        not isinstance(data, dict)
        or not required <= data.keys()
        or data["technical_id"] != "RF20-ADMIN-SUPPORT-RUNTIME-01"
    ):
        return 2
    if (
        not str(data["postgresql_version"]).startswith("PostgreSQL 18")
        or data["migration_head"] != "RF20_ADMIN_SUPPORT_RUNTIME"
        or re.fullmatch(r"[0-9a-f]{40}", str(data["candidate_sha"])) is None
    ):
        return 2
    expected_sha = os.environ.get("GITHUB_SHA")
    if expected_sha and data["candidate_sha"] != expected_sha:
        return 2
    if (
        data["foreign_write_denied"] is not True
        or data["host_postgres_published"] is not False
        or not isinstance(data["host_postgres_publication_proof"], str)
        or not data["host_postgres_publication_proof"]
    ):
        return 2
    required_adapters = {
        "identity", "entitlements_tariff", "entitlements_access", "beacon", "scan", "notification"
    }
    if set(data["adapter_signature_evidence"]) != required_adapters:
        return 2
    if data["note_body_in_event_details"] is not False:
        return 2
    if data["event_timestamps_aware"] is not True:
        return 2
    if int(data["correlation_count"]) < 1 or int(data["causation_count"]) < 1:
        return 2
    if any(value is not True for value in data["audit_metadata"].values()):
        return 2
    if any(
        data[name] != 0
        for name in ("live_provider_calls", "real_token_reads", "raw_provider_payload_persisted")
    ):
        return 2
    if any(
        int(data["support_counts"].get(name, 0)) < 1
        for name in ("support_cases", "support_case_notes", "support_case_events")
    ):
        return 2
    if data.get("replay") is not True:
        return 2
    required_delegations = {"role", "tariff", "access", "beacon", "beacon_replay", "anchor", "foreign"}
    if not required_delegations <= data["delegations"].keys():
        return 2
    if data["ambiguous_replay_preserved"] is not True:
        return 2
    if any(int(data["port_calls"].get(name, 0)) < 1 for name in ("identity", "entitlements", "beacon", "scan")):
        return 2
    if int(data["foreign_target_denials"].get("beacon", 0)) < 1:
        return 2
    print("RF20 PostgreSQL evidence verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
