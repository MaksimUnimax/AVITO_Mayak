"""Fail-closed verifier for RF20 semantic acceptance evidence."""

from __future__ import annotations

import json
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
    }
    if (
        not isinstance(data, dict)
        or not required <= data.keys()
        or data["technical_id"] != "RF20-ADMIN-SUPPORT-RUNTIME-01"
    ):
        return 2
    if (
        not str(data["postgresql_version"]).startswith("PostgreSQL 18")
        or not data["migration_head"]
    ):
        return 2
    if data["foreign_write_denied"] is not True or data["host_postgres_published"] is not False:
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
    print("RF20 PostgreSQL evidence verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
