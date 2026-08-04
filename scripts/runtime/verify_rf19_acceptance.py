"""Independent fail-closed checker for primitive RF19 evidence."""

# ruff: noqa: E501

from __future__ import annotations

import json
import sys
from pathlib import Path

REQUIRED = {
    "technical_id",
    "candidate_sha",
    "max_table_names",
    "live_network_call_count",
    "real_secret_read_count",
    "raw_provider_payload_persisted_count",
    "readiness",
    "fake_provider",
    "httpx_mocked",
    "postgresql_version",
    "migration_head",
    "foreign_write_denied",
    "foreign_sequence_write_denied",
    "inbound",
    "identity_mapping",
    "delivery_mapping",
    "nonce",
}


def main() -> int:
    if len(sys.argv) != 2:
        return 2
    try:
        data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return 2
    if (
        not isinstance(data, dict)
        or not REQUIRED.issubset(data)
        or data["technical_id"] != "RF19-MAX-ADAPTER-RUNTIME-01"
    ):
        return 2
    if data["max_table_names"] != [
        "max_delivery_mappings",
        "max_identity_mappings",
        "max_inbound_events",
        "max_miniapp_nonces",
    ]:
        return 2
    if any(
        data.get(key) != 0
        for key in (
            "live_network_call_count",
            "real_secret_read_count",
            "raw_provider_payload_persisted_count",
        )
    ):
        return 2
    if (
        data["fake_provider"].get("blind_retries") != 0
        or data["httpx_mocked"].get("automatic_retries") != 0
    ):
        return 2
    if data["readiness"].get("disabled") is not True:
        return 2
    if not str(data["postgresql_version"]).startswith("PostgreSQL 18"):
        return 2
    if (
        not data["migration_head"]
        or data["foreign_write_denied"] is not True
        or data["foreign_sequence_write_denied"] is not True
    ):
        return 2
    if data["inbound"].get("first") != "NORMALIZED_UPDATE_ACCEPTED":
        return 2
    if data["inbound"].get("replay") != "DUPLICATE_UPDATE":
        return 2
    if data["inbound"].get("conflict") != "AMBIGUOUS_REPLAY_CONFLICT":
        return 2
    if data["identity_mapping"].get("replay") is not True:
        return 2
    if data["delivery_mapping"].get("replay") is not True:
        return 2
    if data["nonce"].get("accepted") is not True or data["nonce"].get("replay") is not True:
        return 2
    print("RF19 primitive evidence verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
