"""Independent fail-closed verifier for RF-14 raw acceptance observations."""

# ruff: noqa: E501

from __future__ import annotations

import argparse
import json
from pathlib import Path

MARKER = "RF14_ACCEPTANCE_VERIFIED"
EXPECTED_HEAD = "RF13_BEACON_RUNTIME_HARDEN"
EXPECTED_COLUMNS = [
    "id",
    "beacon_id",
    "run_id",
    "route_id",
    "outcome_code",
    "listing_snapshot",
    "observed_at",
    "fingerprint",
    "created_at",
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("observations", type=Path)
    parser.add_argument("candidate_sha")
    args = parser.parse_args()
    data = json.loads(args.observations.read_text(encoding="utf-8"))
    identity = data["identity"]
    postgres = data["postgres"]
    persistence = data["persistence"]
    runtime = data["runtime"]
    checks = (
        identity["candidate_sha"] == args.candidate_sha,
        identity["parent_expected"] == "306ca35bedfee8bcb2894fd8e22234ebd48d0665",
        postgres["major"] == 18,
        postgres["alembic_head"] == EXPECTED_HEAD,
        postgres["parser_columns"] == EXPECTED_COLUMNS,
        persistence["usable_read"] is True,
        persistence["restricted_read"] is True,
        persistence["snapshot_bytes"] <= 32768,
        persistence["fingerprint_length"] == 64,
        persistence["replayed"] is True,
        persistence["rollback_before"] == persistence["rollback_after"],
        persistence["retry_replayed"] is False,
        persistence["committed_after_cleanup"] < persistence["committed_before_cleanup"],
        persistence["foreign_rows_left"] == 1,
        runtime["synthetic_status"] == "USABLE_RESPONSE",
        runtime["restricted_status"] == "RATE_OR_ACCESS_RESTRICTED",
        runtime["live_calls"] == 0,
    )
    if not all(checks):
        raise SystemExit("RF14 acceptance observation mismatch")
    print(MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
